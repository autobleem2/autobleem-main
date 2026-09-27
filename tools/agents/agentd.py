#!/usr/bin/env python3
"""agentd - AI workers on a Linux machine, run as headless Claude Code sessions (the laptop bridge).

Runs as the `abagents` user on the test laptop (decisions.md, "The company is leads plus one shared pool").
Every worker is a folder `$AGENTS_HOME/<name>/`:

    agent.json      {"name", "display", "model", "timeout_min", "max_turns"}
    work/           the worker's working directory; its CLAUDE.md is the worker's brief
    settings.json   the worker's Claude Code permissions (passed with --settings)
    inbox/          tasks waiting, <id>.json
    running/        the task being worked on + <id>.pid (the claude process, recorded - stopped only by it)
    outbox/         results, <id>.json
    done/           finished task files
    session_id      the Claude session the next task resumes, so the worker remembers earlier tasks
    disabled        present = the worker takes no new tasks
    agent.log       one line per task

One task at a time per worker, workers in parallel. Nothing listens on the network: the PC reaches this
script over ssh (`tools/bridge.py` in autobleem-main), which only calls the subcommands below.

    agentd.py serve                              the daemon (systemd user unit agentd.service)
    agentd.py spawn NAME --model M --display D   create a worker (brief on stdin -> work/CLAUDE.md)
    agentd.py settings NAME                      replace a worker's settings.json from stdin
    agentd.py ask NAME --from WHO [--timeout-min N]   queue a task (prompt on stdin), print its id
    agentd.py wait ID [--timeout S]              block until the result is there, print it (JSON)
    agentd.py result ID                          print a result if there is one
    agentd.py status                             the workers, their queues and what runs
    agentd.py cancel ID                          stop a running task by its recorded pid
    agentd.py enable|disable NAME                let a worker take tasks, or not
    agentd.py log NAME [-n N]                    the last lines of a worker's log
"""
import argparse
import json
import os
import secrets
import signal
import subprocess
import sys
import threading
import time

HOME = os.environ.get("AGENTS_HOME", os.path.expanduser("~/agents"))
CLAUDE = os.environ.get("AGENTS_CLAUDE", os.path.expanduser("~/.local/bin/claude"))
POLL_S = float(os.environ.get("AGENTS_POLL_S", "2"))
SUBDIRS = ("work", "inbox", "running", "outbox", "done")


def now():
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def agent_dir(name):
    if not name or not all(c.isalnum() or c in "-_" for c in name):
        sys.exit("bad worker name: %r" % name)
    return os.path.join(HOME, name)


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def log(adir, line):
    with open(os.path.join(adir, "agent.log"), "a", encoding="utf-8") as f:
        f.write("%s %s\n" % (now(), line))


def agents():
    if not os.path.isdir(HOME):
        return []
    return sorted(n for n in os.listdir(HOME) if os.path.isfile(os.path.join(HOME, n, "agent.json")))


def find_task(task_id):
    """(worker dir, state) of a task id: the state is the subfolder it sits in."""
    for n in agents():
        adir = os.path.join(HOME, n)
        for state in ("outbox", "running", "inbox"):
            if os.path.exists(os.path.join(adir, state, task_id + ".json")):
                return adir, state
    return None, None


# ------------------------------------------------------------------ the daemon

def run_task(adir, task_path):
    cfg = read_json(os.path.join(adir, "agent.json"), {})
    task = read_json(task_path, {})
    tid = task.get("id") or os.path.basename(task_path)[:-5]
    running = os.path.join(adir, "running", tid + ".json")
    os.replace(task_path, running)
    pid_file = os.path.join(adir, "running", tid + ".pid")
    prompt = "Task %s from %s:\n\n%s" % (tid, task.get("from", "?"), task.get("prompt", ""))
    sid_file = os.path.join(adir, "session_id")
    sid = open(sid_file).read().strip() if os.path.exists(sid_file) else ""
    timeout = 60 * float(task.get("timeout_min") or cfg.get("timeout_min") or 30)
    started = time.time()

    def attempt(resume):
        cmd = [CLAUDE, "-p", prompt, "--output-format", "json", "--model", cfg.get("model", "haiku"),
               "--max-turns", str(cfg.get("max_turns", 60))]
        settings = os.path.join(adir, "settings.json")
        if os.path.exists(settings):
            cmd += ["--settings", settings]
        if resume:
            cmd += ["--resume", resume]
        proc = subprocess.Popen(cmd, cwd=os.path.join(adir, "work"), stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, stdin=subprocess.DEVNULL, start_new_session=True)
        with open(pid_file, "w") as f:
            f.write(str(proc.pid))
        try:
            out, err = proc.communicate(timeout=timeout)
            return proc.returncode, out.decode("utf-8", "replace"), err.decode("utf-8", "replace"), False
        except subprocess.TimeoutExpired:
            os.killpg(proc.pid, signal.SIGTERM)  # the group this task started, by its recorded pid
            try:
                out, err = proc.communicate(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(proc.pid, signal.SIGKILL)
                out, err = proc.communicate()
            return proc.returncode, out.decode("utf-8", "replace"), err.decode("utf-8", "replace"), True

    code, out, err, timed_out = attempt(sid)
    parsed = None
    try:
        parsed = json.loads(out) if out.strip() else None
    except ValueError:
        parsed = None
    if sid and not timed_out and (parsed is None or parsed.get("is_error")) and "No conversation found" in (out + err):
        code, out, err, timed_out = attempt("")  # the old session is gone: start a fresh one
        try:
            parsed = json.loads(out) if out.strip() else None
        except ValueError:
            parsed = None

    ok = bool(parsed) and not parsed.get("is_error") and code == 0 and not timed_out
    if parsed and parsed.get("session_id"):
        with open(sid_file, "w") as f:
            f.write(parsed["session_id"])
    result = {
        "id": tid, "agent": cfg.get("name"), "display": cfg.get("display"), "from": task.get("from"),
        "row": task.get("row"), "ok": ok, "timed_out": timed_out, "exit": code,
        "result": (parsed or {}).get("result") if parsed else out[-4000:],
        "stderr": err[-2000:] if not ok else "",
        "cost_usd": (parsed or {}).get("total_cost_usd"), "turns": (parsed or {}).get("num_turns"),
        "session_id": (parsed or {}).get("session_id"),
        "queued": task.get("created"), "started": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(started)),
        "finished": now(), "seconds": round(time.time() - started, 1),
    }
    write_json(os.path.join(adir, "outbox", tid + ".json"), result)
    os.replace(running, os.path.join(adir, "done", tid + ".json"))
    if os.path.exists(pid_file):
        os.remove(pid_file)
    log(adir, "%s from=%s ok=%s seconds=%s cost=%s" % (tid, task.get("from"), ok, result["seconds"],
                                                        result["cost_usd"]))


def serve():
    busy = {}
    # a task left in running/ by a crash or a reboot goes back to the inbox
    for n in agents():
        adir = os.path.join(HOME, n)
        for f in os.listdir(os.path.join(adir, "running")):
            p = os.path.join(adir, "running", f)
            if f.endswith(".json"):
                os.replace(p, os.path.join(adir, "inbox", f))
            elif f.endswith(".pid"):
                os.remove(p)
    while True:
        for n in agents():
            adir = os.path.join(HOME, n)
            t = busy.get(n)
            if (t and t.is_alive()) or os.path.exists(os.path.join(adir, "disabled")):
                continue
            inbox = os.path.join(adir, "inbox")
            tasks = sorted(f for f in os.listdir(inbox) if f.endswith(".json"))
            if tasks:
                t = threading.Thread(target=run_task, args=(adir, os.path.join(inbox, tasks[0])), daemon=True)
                busy[n] = t
                t.start()
        time.sleep(POLL_S)


# ------------------------------------------------------------------ the commands the bridge calls

def cmd_spawn(a):
    adir = agent_dir(a.name)
    for d in SUBDIRS:
        os.makedirs(os.path.join(adir, d), exist_ok=True)
    write_json(os.path.join(adir, "agent.json"), {"name": a.name, "display": a.display, "model": a.model,
                                                  "timeout_min": a.timeout_min, "max_turns": a.max_turns})
    brief = sys.stdin.read()
    if brief.strip():
        with open(os.path.join(adir, "work", "CLAUDE.md"), "w", encoding="utf-8") as f:
            f.write(brief)
    log(adir, "spawned model=%s display=%r" % (a.model, a.display))
    print(adir)


def cmd_settings(a):
    adir = agent_dir(a.name)
    data = json.loads(sys.stdin.read())
    write_json(os.path.join(adir, "settings.json"), data)
    log(adir, "settings replaced")
    print("ok")


def cmd_ask(a):
    adir = agent_dir(a.name)
    if not os.path.isfile(os.path.join(adir, "agent.json")):
        sys.exit("no worker %s" % a.name)
    prompt = sys.stdin.read()
    if not prompt.strip():
        sys.exit("empty task")
    tid = time.strftime("%Y%m%d-%H%M%S-") + secrets.token_hex(2)
    write_json(os.path.join(adir, "inbox", tid + ".json"),
               {"id": tid, "from": a.sender, "prompt": prompt, "created": now(), "timeout_min": a.timeout_min,
                "row": a.row,
                "what": a.what or next((ln.strip() for ln in prompt.splitlines() if ln.strip()), "")[:90]})
    print(tid)


def cmd_wait(a):
    deadline = time.time() + a.timeout
    while True:
        adir, state = find_task(a.id)
        if adir is None:
            sys.exit("no task %s" % a.id)
        if state == "outbox":
            print(open(os.path.join(adir, "outbox", a.id + ".json"), encoding="utf-8").read())
            return
        if time.time() > deadline:
            print(json.dumps({"id": a.id, "state": state, "waiting": True}))
            return
        time.sleep(POLL_S)


def cmd_result(a):
    a.timeout = 0
    cmd_wait(a)


def cmd_status(a):
    out = []
    for n in agents():
        adir = os.path.join(HOME, n)
        cfg = read_json(os.path.join(adir, "agent.json"), {})
        running = [f[:-5] for f in os.listdir(os.path.join(adir, "running")) if f.endswith(".json")]
        out.append({"name": n, "display": cfg.get("display"), "model": cfg.get("model"),
                    "enabled": not os.path.exists(os.path.join(adir, "disabled")),
                    "queued": sorted(f[:-5] for f in os.listdir(os.path.join(adir, "inbox")) if f.endswith(".json")),
                    "running": running,
                    "results": len(os.listdir(os.path.join(adir, "outbox"))),
                    "tasks": [dict(state=state, **{k: t.get(k) for k in ("id", "from", "row", "what", "created")})
                              for state in ("running", "inbox")
                              for t in (read_json(os.path.join(adir, state, f), {})
                                        for f in sorted(os.listdir(os.path.join(adir, state))) if f.endswith(".json"))]})
    print(json.dumps(out, ensure_ascii=False, indent=1))


def cmd_cancel(a):
    adir, state = find_task(a.id)
    if state != "running":
        sys.exit("task %s is not running (%s)" % (a.id, state))
    pid = int(open(os.path.join(adir, "running", a.id + ".pid")).read().strip())
    os.killpg(pid, signal.SIGTERM)  # the recorded pid of this task's own process group
    log(adir, "%s cancelled (pid %d)" % (a.id, pid))
    print("sent SIGTERM to %d" % pid)


def cmd_enable(a, on):
    adir = agent_dir(a.name)
    marker = os.path.join(adir, "disabled")
    if on and os.path.exists(marker):
        os.remove(marker)
    elif not on:
        open(marker, "w").close()
    log(adir, "enabled" if on else "disabled")
    print("ok")


def cmd_log(a):
    path = os.path.join(agent_dir(a.name), "agent.log")
    lines = open(path, encoding="utf-8").read().splitlines() if os.path.exists(path) else []
    print("\n".join(lines[-a.n:]))


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("serve")
    s = sub.add_parser("spawn")
    s.add_argument("name")
    s.add_argument("--model", default="haiku")
    s.add_argument("--display", default="")
    s.add_argument("--timeout-min", type=float, default=30)
    s.add_argument("--max-turns", type=int, default=60)
    s = sub.add_parser("settings")
    s.add_argument("name")
    s = sub.add_parser("ask")
    s.add_argument("name")
    s.add_argument("--from", dest="sender", required=True)
    s.add_argument("--timeout-min", type=float, default=None)
    s.add_argument("--row", default="", help="the todo row (or a short label) the task belongs to, for the panel")
    s.add_argument("--what", default="", help="one line for the panel; default: the task's first line")
    for c in ("wait", "result"):
        s = sub.add_parser(c)
        s.add_argument("id")
        if c == "wait":
            s.add_argument("--timeout", type=float, default=1800)
    sub.add_parser("status")
    s = sub.add_parser("cancel")
    s.add_argument("id")
    for c in ("enable", "disable"):
        sub.add_parser(c).add_argument("name")
    s = sub.add_parser("log")
    s.add_argument("name")
    s.add_argument("-n", type=int, default=20)
    a = p.parse_args()
    if a.cmd == "serve":
        serve()
    elif a.cmd in ("enable", "disable"):
        cmd_enable(a, a.cmd == "enable")
    else:
        globals()["cmd_" + a.cmd](a)


if __name__ == "__main__":
    main()
