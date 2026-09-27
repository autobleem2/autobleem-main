#!/usr/bin/env python3
"""bridge.py - the PC side of the laptop bridge: give tasks to AI workers that run on the test laptop.

The workers are headless Claude Code sessions run by `tools/agents/agentd.py` as the `abagents` user there
(decisions.md, "The company is leads plus one shared pool"). This script only talks ssh (key auth) to that
user and calls agentd's subcommands; nothing listens on the network on either side.

The host is never written in this repository: set AB_AGENTS_HOST (e.g. abagents@<laptop>) or put it on the
first line of ~/.autobleem-agents-host.

    python tools/bridge.py install                          copy agentd + its systemd unit, (re)start it
    python tools/bridge.py spawn intern --model haiku --display "..." --brief b.md [--settings s.json]
    python tools/bridge.py settings intern s.json           replace a worker's permissions
    python tools/bridge.py ask intern "task" --from "Marcus Hale" [--wait [SECONDS]]
    python tools/bridge.py wait ID [--timeout S] | result ID | cancel ID
    python tools/bridge.py status | log intern [-n N] | enable intern | disable intern

`ask --wait` prints the worker's answer (the `result` field) and exits 0 when it succeeded, 1 when it did not;
`--json` prints the whole result record instead.
"""
import argparse
import json
import os
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REMOTE_BIN = os.environ.get("AB_AGENTS_BIN", "~/agents/bin")  # another place only for testing
UNIT = """[Unit]
Description=AutoBleem AI workers (agentd)

[Service]
ExecStart=/usr/bin/python3 %h/agents/bin/agentd.py serve
Environment=PATH=%h/.local/bin:/usr/local/bin:/usr/bin:/bin
Restart=always
RestartSec=5

[Install]
WantedBy=default.target
"""


def host():
    h = os.environ.get("AB_AGENTS_HOST", "").strip()
    if not h:
        try:
            with open(os.path.expanduser("~/.autobleem-agents-host"), encoding="utf-8") as f:
                h = f.readline().strip()
        except OSError:
            pass
    if not h:
        sys.exit("set AB_AGENTS_HOST=abagents@<laptop> or write it into ~/.autobleem-agents-host")
    return h


def remote_env():
    """AGENTS_HOME / AGENTS_CLAUDE passed through - only for testing agentd somewhere else."""
    return " ".join("%s=%s" % (k, shlex.quote(os.environ[k])) for k in ("AGENTS_HOME", "AGENTS_CLAUDE")
                    if os.environ.get(k))


def ssh(remote_cmd, stdin_text=None, check=True):
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", host(), remote_cmd]
    p = subprocess.run(cmd, input=(stdin_text or "").encode("utf-8"), stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE)
    out, err = p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
    if check and p.returncode != 0:
        sys.stderr.write(err)
        sys.exit(p.returncode)
    return out, err, p.returncode


def agentd(args, stdin_text=None, check=True):
    env = remote_env()
    return ssh("%s python3 %s/agentd.py %s" % (env, REMOTE_BIN, " ".join(shlex.quote(a) for a in args)),
               stdin_text, check)


def install(_):
    src = open(os.path.join(HERE, "agents", "agentd.py"), encoding="utf-8").read()
    ssh("mkdir -p %s ~/.config/systemd/user && cat > %s/agentd.py && chmod 755 %s/agentd.py"
        % (REMOTE_BIN, REMOTE_BIN, REMOTE_BIN), src)
    ssh("cat > ~/.config/systemd/user/agentd.service", UNIT)
    out, _, _ = ssh("systemctl --user daemon-reload && systemctl --user enable --now agentd.service >/dev/null 2>&1;"
                    " systemctl --user restart agentd.service && systemctl --user is-active agentd.service")
    print("agentd: " + out.strip())


def print_result(text, as_json):
    try:
        r = json.loads(text)
    except ValueError:
        print(text)
        return 1
    if r.get("waiting"):
        print("still %s: %s" % (r.get("state"), r.get("id")))
        return 2
    if as_json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        head = "[%s %s, %ss, $%s]" % (r.get("display") or r.get("agent"), "ok" if r.get("ok") else "FAILED",
                                      r.get("seconds"), r.get("cost_usd"))
        print(head)
        print(r.get("result") or "")
        if not r.get("ok") and r.get("stderr"):
            print(r["stderr"], file=sys.stderr)
    return 0 if r.get("ok") else 1


def main():
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("install")
    s = sub.add_parser("spawn")
    s.add_argument("name")
    s.add_argument("--model", default="haiku")
    s.add_argument("--display", default="")
    s.add_argument("--brief", help="a Markdown file: the worker's CLAUDE.md")
    s.add_argument("--settings", help="a JSON file: the worker's Claude Code settings (permissions)")
    s.add_argument("--timeout-min", default="30")
    s = sub.add_parser("settings")
    s.add_argument("name")
    s.add_argument("file")
    s = sub.add_parser("ask")
    s.add_argument("name")
    s.add_argument("task")
    s.add_argument("--from", dest="sender", required=True)
    s.add_argument("--timeout-min")
    s.add_argument("--wait", nargs="?", const="1800", help="wait for the answer (seconds, default 1800)")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("wait")
    s.add_argument("id")
    s.add_argument("--timeout", default="1800")
    s.add_argument("--json", action="store_true")
    s = sub.add_parser("result")
    s.add_argument("id")
    s.add_argument("--json", action="store_true")
    sub.add_parser("status")
    for c in ("cancel",):
        sub.add_parser(c).add_argument("id")
    for c in ("enable", "disable"):
        sub.add_parser(c).add_argument("name")
    s = sub.add_parser("log")
    s.add_argument("name")
    s.add_argument("-n", default="20")
    a = p.parse_args()

    if a.cmd == "install":
        install(a)
    elif a.cmd == "spawn":
        brief = open(a.brief, encoding="utf-8").read() if a.brief else ""
        out, _, _ = agentd(["spawn", a.name, "--model", a.model, "--display", a.display,
                            "--timeout-min", a.timeout_min], brief)
        print(out.strip())
        if a.settings:
            agentd(["settings", a.name], open(a.settings, encoding="utf-8").read())
            print("settings: " + a.settings)
    elif a.cmd == "settings":
        print(agentd(["settings", a.name], open(a.file, encoding="utf-8").read())[0].strip())
    elif a.cmd == "ask":
        args = ["ask", a.name, "--from", a.sender]
        if a.timeout_min:
            args += ["--timeout-min", a.timeout_min]
        tid = agentd(args, a.task)[0].strip()
        if not a.wait:
            print(tid)
            return
        sys.exit(print_result(agentd(["wait", tid, "--timeout", a.wait])[0], a.json))
    elif a.cmd == "wait":
        sys.exit(print_result(agentd(["wait", a.id, "--timeout", a.timeout])[0], a.json))
    elif a.cmd == "result":
        sys.exit(print_result(agentd(["result", a.id])[0], a.json))
    elif a.cmd == "log":
        print(agentd(["log", a.name, "-n", a.n])[0].rstrip())
    elif a.cmd in ("status", "cancel", "enable", "disable"):
        print(agentd([a.cmd] + ([a.id] if a.cmd == "cancel" else [a.name] if a.cmd != "status" else []))[0].rstrip())


if __name__ == "__main__":
    main()
