# The laptop bridge - AI workers on the test laptop

The company is three leads plus one shared worker pool, dispatched by the Program Manager (see
`docs/decisions.md`). The pool's workers run on the test laptop as headless Claude Code sessions:

- **`agentd.py`** runs there as the Linux user `abagents` (no sudo, in the `docker` group, linger on) as the
  systemd user unit `agentd.service`. Each worker is a folder `~/agents/<name>/` with its brief
  (`work/CLAUDE.md`), permissions (`settings.json`), inbox/outbox and the Claude session it resumes. Tasks run
  one at a time per worker; workers run in parallel. The script's docstring describes the layout.
- **`../bridge.py`** is the PC side. It only talks ssh (key auth) to `abagents@<laptop>`, never over any
  other port. The host is never committed: set `AB_AGENTS_HOST` or write it into `~/.autobleem-agents-host`.
- **`workers/<name>/`** holds each worker's brief and settings as they are deployed.

## One-time setup (the owner)

Create the `abagents` user and log Claude in there: `howto/intern-setup.html`.

## Deploy and use (the PM, or any lead)

```
python tools/bridge.py install
python tools/bridge.py spawn intern --model haiku --display "Nina Park - Intern (Haiku)" \
    --brief tools/agents/workers/intern/CLAUDE.md --settings tools/agents/workers/intern/settings.json
python tools/bridge.py ask intern "check that ... and report" --from "Marcus Hale" --wait
python tools/bridge.py status
python tools/bridge.py log intern
```

`ask --wait` blocks until the answer arrives (default 30 minutes) and exits 0 on success. Without `--wait`
it prints the task id; `wait <id>` or `result <id>` fetch the answer later. `cancel <id>` stops a running
task by the pid agentd recorded for it. `disable <name>` stops a worker from taking new tasks.

Git Bash on Windows rewrites `/tmp/...` in environment variables. When testing against another directory
with `AB_AGENTS_BIN`, `AGENTS_HOME` or `AGENTS_CLAUDE`, set
`MSYS2_ENV_CONV_EXCL='AB_AGENTS_BIN;AGENTS_HOME;AGENTS_CLAUDE'`.

## Tested

2026-09-27 on the laptop, with a fake `claude` in a throwaway directory:
- spawn with its brief and settings;
- two tasks, the second resuming the first one's session;
- cancel by recorded pid;
- the per-task timeout;
- a lost session starting a fresh one.

The first real worker, the Intern, comes after the owner's setup.
