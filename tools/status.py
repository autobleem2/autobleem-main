#!/usr/bin/env python3
"""status.py - keeps status.json (the teams' current work and what waits on the owner, schema 1 -
docs/admin-roadmap-plan.md) current without anyone hand-editing it. The admin Roadmap tab and the PC test
machine's panel read it from develop every minute, so whoever changes a team's state runs one command:

  status.py team "Victor Lane" [--state working|waiting|asleep] [--item ID "what"]... [--note "..."]
      set one team's state/note; any --item replaces that team's item list (--clear-items empties it);
      --label "infrastructure" names the team when it is new
  status.py done ID...           drop ID from every team's items and from the owner's queue
  status.py needs add ID KIND "what"   |   status.py needs rm ID...
                                 the owner's queue (KIND: decision, device test, action, look, ...)
  status.py usage FIVE WEEKLY [--cap N] [--five-resets ISO] [--weekly-resets ISO]
  status.py sync                 only the automatic part (below), committed if anything changed
  status.py show                 print the file

Every write also drops the items whose todo.md row is closed (`| ID | ~~...~~`), stamps written_at (local
time with its offset) and written_by (--by, else $AB_STATUS_BY), refuses LAN addresses and `_team` paths
(the file is public), and pushes a commit of status.json alone (`[skip ci]`) straight onto origin's develop:
it reads develop's latest status.json and todo.md, builds the commit with a private index, and retries when
another session pushed first - the caller's working tree, the shared index and whatever is checked out
(a branch, a detached merge-hub worktree) are never touched. --no-push edits the file on disk instead and
stops. Standard library only.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS = os.path.join(ROOT, "status.json")
TODO = os.path.join(ROOT, "docs", "todo.md")
STATES = ("working", "waiting", "asleep")
PRIVATE = re.compile(r"\b(10\.\d{1,3}|192\.168|172\.(1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b|_team[/\\]")


def load_empty():
    return {"schema": 1, "teams": [], "needs_owner": []}


def load():
    try:
        with open(STATUS, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return load_empty()


def read_todo():
    try:
        with open(TODO, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def closed_ids(todo_text):
    """The todo.md rows marked done: `| ID | ~~title~~ **done ...`."""
    return {m.group(1) for m in re.finditer(r"^\|\s*([A-Z]+-?\d+)\s*\|\s*~~", todo_text, re.M)}


def item_ids(item_id):
    """"H12/H13" counts as closed only when every part is."""
    return [p.strip() for p in item_id.split("/") if p.strip()]


def drop(data, ids):
    """Remove items and owner-queue entries whose ids are all in `ids`; returns how many went."""
    gone = 0
    for t in data.get("teams", []):
        keep = [i for i in t.get("items", []) if not all(p in ids for p in item_ids(i.get("id", "")))]
        gone += len(t.get("items", [])) - len(keep)
        t["items"] = keep
    keep = [n for n in data.get("needs_owner", []) if not all(p in ids for p in item_ids(n.get("id", "")))]
    gone += len(data.get("needs_owner", [])) - len(keep)
    data["needs_owner"] = keep
    return gone


def find_team(data, name):
    for t in data.setdefault("teams", []):
        if t.get("name") == name:
            return t
    return None


def apply(args, data):
    """Apply one command to `data`; returns a short summary for the commit message."""
    if args.cmd == "team":
        t = find_team(data, args.name)
        if t is None:
            t = {"name": args.name, "team": args.label or "", "state": args.state or "working",
                 "items": [], "note": ""}
            data["teams"].append(t)
        if args.label:
            t["team"] = args.label
        if args.state:
            t["state"] = args.state
        if args.item or args.clear_items:
            t["items"] = [{"id": i, "what": w} for i, w in (args.item or [])]
        if args.note is not None:
            t["note"] = args.note
        return "%s %s%s" % (args.name, t["state"], (" - " + ", ".join(i["id"] for i in t["items"])) if t["items"] else "")
    if args.cmd == "done":
        drop(data, set(args.ids))
        return "done " + " ".join(args.ids)
    if args.cmd == "needs":
        queue = data.setdefault("needs_owner", [])
        if args.action == "add":
            if len(args.rest) != 3:
                sys.exit("needs add ID KIND \"what\"")
            nid, kind, what = args.rest
            entry = {"id": nid, "kind": kind, "what": what}
            if getattr(args, "howto", None):
                if not re.match(r"^howto/[a-z0-9][a-z0-9-]{0,63}\.html$", args.howto):
                    sys.exit("status.py: --howto is howto/<name>.html (lower case, digits, dashes)")
                entry["howto"] = args.howto
            queue[:] = [n for n in queue if n.get("id") != nid] + [entry]
            return "owner's queue + " + nid
        queue[:] = [n for n in queue if n.get("id") not in args.rest]
        return "owner's queue - " + " ".join(args.rest)
    if args.cmd == "usage":
        u = data.setdefault("usage", {})
        u["five_hour_percent"], u["weekly_percent"] = args.five, args.weekly
        if args.cap is not None:
            u["weekly_cap_today_percent"] = args.cap
        if args.five_resets:
            u["five_hour_resets_at"] = args.five_resets
        if args.weekly_resets:
            u["weekly_resets_at"] = args.weekly_resets
        return "usage %d%%/%d%%" % (args.five, args.weekly)
    return "sync"


def check_public(text):
    m = PRIVATE.search(text)
    if m:
        sys.exit("status.py: refusing - status.json is public and would contain %r" % m.group(0))


def render(data):
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def git(*a, check=True, stdin=None, env=None):
    """Run git in ROOT; stdout comes back as UTF-8 text (bytes in and out, so Windows never adds a CR)."""
    r = subprocess.run(["git", "-C", ROOT] + list(a), check=False, capture_output=True, input=stdin, env=env)
    if check and r.returncode:
        sys.exit("status.py: git %s failed: %s" % (a[0], r.stderr.decode("utf-8", "replace").strip()))
    return r.returncode, r.stdout.decode("utf-8")


def show(rev, path):
    code, out = git("show", "%s:%s" % (rev, path), check=False)
    return out if code == 0 else None


def commit_on(base, text, message):
    """A commit on top of `base` that changes status.json alone - built with a private index, so neither the
    caller's working tree nor the shared index nor whatever branch (or detached HEAD) is checked out is
    touched."""
    _, blob = git("hash-object", "-w", "--stdin", stdin=text.encode("utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ, GIT_INDEX_FILE=os.path.join(tmp, "index"))
        git("read-tree", base, env=env)
        git("update-index", "--add", "--cacheinfo", "100644,%s,status.json" % blob.strip(), env=env)
        _, tree = git("write-tree", env=env)
    _, commit = git("commit-tree", tree.strip(), "-p", base, "-m", message)
    return commit.strip()


def write_and_push(args, push):
    """Apply the command to develop's latest status.json and push a commit of it straight to develop; retry
    when another session pushed first. --no-push works on the files on disk instead."""
    for attempt in range(5):
        if push:
            git("fetch", "-q", "origin", "develop")
            _, base = git("rev-parse", "FETCH_HEAD")
            base = base.strip()
            raw, todo = show(base, "status.json"), show(base, "docs/todo.md") or ""
            data = json.loads(raw) if raw else load_empty()
        else:
            data = load()
            todo = read_todo()
        before = render(data)
        summary = apply(args, data)
        closed = drop(data, closed_ids(todo))
        if args.cmd == "sync" and not closed:
            print("status.py: nothing to sync")
            return
        if closed:
            summary += " (+%d closed in todo.md)" % closed
        if render(data) == before:
            print("status.py: unchanged")
            return
        data["schema"] = 1
        data["written_at"] = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
        data["written_by"] = args.by or os.environ.get("AB_STATUS_BY") or data.get("written_by", "")
        text = render(data)
        check_public(text)
        if not push:
            with open(STATUS, "w", encoding="utf-8", newline="\n") as f:
                f.write(text)
            print("status.py: written (not pushed) - " + summary)
            return
        commit = commit_on(base, text, "status: %s [skip ci]" % summary)
        code, _ = git("push", "-q", "origin", commit + ":refs/heads/develop", check=False)
        if code == 0:
            print("status.py: pushed %s - %s (your checkout catches up on its next pull)" % (commit[:7], summary))
            return
    sys.exit("status.py: push kept failing - try again")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("--by", help="written_by (else $AB_STATUS_BY)")
    p.add_argument("--no-push", action="store_true", help="write status.json, do not commit or push")
    sub = p.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("team")
    t.add_argument("name")
    t.add_argument("--label")
    t.add_argument("--state", choices=STATES)
    t.add_argument("--item", nargs=2, action="append", metavar=("ID", "WHAT"))
    t.add_argument("--clear-items", action="store_true")
    t.add_argument("--note")
    d = sub.add_parser("done")
    d.add_argument("ids", nargs="+")
    n = sub.add_parser("needs")
    n.add_argument("action", choices=("add", "rm"))
    n.add_argument("rest", nargs="+")
    n.add_argument("--howto", help="howto/<name>.html - the page the admin panel opens beside the entry")
    u = sub.add_parser("usage")
    u.add_argument("five", type=int)
    u.add_argument("weekly", type=int)
    u.add_argument("--cap", type=int)
    u.add_argument("--five-resets")
    u.add_argument("--weekly-resets")
    sub.add_parser("sync")
    sub.add_parser("show")
    args = p.parse_args(argv)
    if args.cmd == "show":
        sys.stdout.write(render(load()))
        return
    write_and_push(args, push=not args.no_push)


if __name__ == "__main__":
    main()
