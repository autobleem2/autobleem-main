# Debugging and "done" - how every session works

The owner's rule (2026-09-27): every team debugs this way and reports "done" this way. Adapted from the
`systematic-debugging` and `verification-before-completion` skills of obra/superpowers (MIT), rewritten for this
project; the plugin itself is not used.

## The two laws

1. **No fix before the root cause.** A change made to see whether it helps is a guess, not a fix.
2. **No "done", "green", "fixed" or "passes" without fresh evidence** - the command run in this turn, its output
   read, its exit code checked. An agent's "success" report is a claim to check, not evidence.

## Debugging: four phases, in order

**1. Root cause.**
- Read the whole error: every line of the log, the exit code, the path, the line number. The answer is often
  written there ("Container feature is not supported when runner is already running inside container").
- Reproduce it on purpose, with exact steps. Not reproducible yet -> gather more evidence; do not guess.
- Ask what changed: `git log`/`git diff` since it last worked, a new image, toolchain, submodule bump, config.
- Across component boundaries, instrument before fixing: log what goes in and what comes out at each boundary
  and run once to see WHERE it breaks. Ours: workflow -> container -> `ci/build.sh` -> CMake -> compiler;
  launcher -> `rc/launch.sh` -> emulator; stick -> console boot chain -> launcher; host -> VM.
- Trace a bad value backwards to where it is born, and fix it there, not where it surfaced.

**2. Pattern.**
- Find the nearest thing that works (the other emulator, the Pi build, the previous nightly, the repo whose CI
  is green) and list every difference, however small. Do not decide in advance that one "cannot matter".
- Read a reference completely before copying its pattern.

**3. Hypothesis.**
- Write one hypothesis: "X is the cause because Y" - in the report or the status file.
- Test it with the smallest change, one variable at a time. Wrong -> a new hypothesis, not a second change on
  top of the first.
- "I don't understand X yet" is a valid report. Pretending is not.

**4. Fix.**
- A failing test first - a doctest case, a script, a `tools/ab_drive.py` run, a `proc_check.py` sample - then
  the fix, then the same test passing. The test stays in the tree when it can.
- One fix, the root cause only. No "while I'm here" edits in the same commit.
- **Three failed fixes = stop.** The design is in question, not the next patch: report it (to the owner if it needs his
  decision) before a fourth attempt.

**When it really is the environment** (a flaky network, a device, timing): say what was ruled out and how,
then add handling (a retry, a timeout, a clear message) and logging for next time. Most "no root cause" cases
are an investigation stopped too early.

## On the devices

- **Get the logs first**: the `keep` marker in `System/Logs` (or Options -> Diagnostics), `rc/launch.sh`'s
  `launch.log`/`pcsx.log`, `standby.log`, `AB_SHOT` frames, `autobleem-gui --sysinfo`.
- **Check the instrument before the code**: busybox `ps` cuts lines at ~78 columns (read `/proc/<pid>/cmdline`);
  `pgrep -f` inside `ssh`/`bash -c` matches itself. K9 was a "bug" made by the first of these.
- A test that needs hands on a device goes to the tester checklist (`docs/tester-checklist.md`); everything the
  DebugDriver, the laptop VM (`docs/pc-test-machine.md`) or ssh can reach is tested directly.

## Before saying "done"

For every claim, name the command that proves it, run it now, read the output, then say it with the evidence:

| Claim | Evidence | Not evidence |
|---|---|---|
| Builds | the build command, exit 0 | "the linter passed" |
| Tests pass | the ctest line: N/N passed | a run from before the last edit |
| CI green | the run's conclusion **success**, not *cancelled* or *skipped*, on the right runner | "the job started" |
| Fixed | the original symptom re-run, gone | "the code changed" |
| Merged / pushed | `git log origin/<branch>` shows the sha | a local commit |
| Written / documented | `git status` clean, the file on the remote | a file in the working tree |
| Agent finished | its diff read by the reviewer | its report |

Words that mean the evidence is missing: "should", "probably", "seems", "looks fine". Replace them with the
evidence, or with "not verified yet".

Waiting in scripts and tests: wait for the condition (a file, a marker, a socket, a status line), not a fixed
`sleep` - and when a fixed wait is truly needed, say why in a comment.
