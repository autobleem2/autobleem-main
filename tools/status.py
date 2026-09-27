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
(the file is public), and commits status.json alone with `[skip ci]` and pushes develop - pulling with a merge
(never a rebase: the checkout is shared) and retrying when another session pushed first. --no-push writes
the file and stops. Standard library only.
"""
import argparse
import datetime
import json
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATUS = os.path.join(ROOT, "status.json")
TODO = os.path.join(ROOT, "docs", "todo.md")
STATES = ("working", "waiting", "asleep")
PRIVATE = re.compile(r"\b(10\.\d{1,3}|192\.168|172\.(1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b|_team[/\\]")


def load():
    try:
        with open(STATUS, encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"schema": 1, "teams": [], "needs_owner": []}


def closed_ids(todo_text):
    """The todo.md rows marked done: `| ID | ~~title~~ **done ...`."""
    return {m.group(1) for m in re.finditer(r"^\|\s*([A-Z]+\d+)\s*\|\s*~~", todo_text, re.M)}


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


def sync_closed(data):
    try:
        with open(TODO, encoding="utf-8") as f:
            return drop(data, closed_ids(f.read()))
    except FileNotFoundError:
        return 0


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
            queue[:] = [n for n in queue if n.get("id") != nid] + [{"id": nid, "kind": kind, "what": what}]
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


def git(*a, check=True):
    return subprocess.run(["git", "-C", ROOT] + list(a), check=check, capture_output=True, text=True)


def write_and_push(args, push):
    """Pull, re-apply on the fresh file, commit status.json alone, push; retry when someone pushed first."""
    for attempt in range(4):
        if push:
            git("pull", "--no-rebase", "-q", "origin", "develop")
        data = load()
        before = render(data)
        summary = apply(args, data)
        closed = sync_closed(data)
        if args.cmd == "sync" and not closed:
            print("status.py: nothing to sync")
            return
        if closed:
            summary += " (+%d closed in todo.md)" % closed
        data["schema"] = 1
        data["written_at"] = datetime.datetime.now().astimezone().replace(microsecond=0).isoformat()
        data["written_by"] = args.by or os.environ.get("AB_STATUS_BY") or data.get("written_by", "")
        text = render(data)
        check_public(text)
        if text == before:
            print("status.py: unchanged")
            return
        with open(STATUS, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        if not push:
            print("status.py: written (not pushed) - " + summary)
            return
        git("commit", "-q", "-m", "status: %s [skip ci]" % summary, "--", "status.json")
        if git("push", "-q", "origin", "develop", check=False).returncode == 0:
            print("status.py: pushed - " + summary)
            return
        # undo only our own unpushed status commit - the index is shared, so touch no other path
        git("reset", "-q", "--soft", "HEAD~1")
        git("checkout", "-q", "HEAD", "--", "status.json")
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
