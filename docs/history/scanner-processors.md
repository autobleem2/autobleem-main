# Scanner processors

How the scan was extended to run user-ordered processors over the games before reading them. A processor can unpack formats the launcher doesn't read (zips, `.7z`, `.rvz`) or modify games (patches, mods).

## Implementation (2026-09-24)

**Repositories**: autobleem-core, launcher, proc_unzip. Branches `feature/processors` merged into develop on 2026-09-24.

**Core abstractions** (`ableem_engine`, tested):
- `ProcessorOutput` — parses and validates the processor's stdout (protocol).
- `ProcessorCatalog` — lists installed processors from `System/Processors/`.
- `ProcessorSequences` — PS1 and ROMs sequences from `System/Processors/sequence.ini`, with on/off state.
- `ProcessorState` — what ran on what (version + names-and-sizes digest per target).
- `ProcessorRunner` — runs a processor; `ProcessorProcess` is the real implementation, `ProcessorRecorder` is the test fake.

**Launcher integration**:
- `ScanService` runs folder processors first (over the whole tree), then for each game/ROM runs the item-processor chain in sequence order.
- `GuiProcessors` (System menu, L2+R2) — edit the sequences: L1/R1 switch between PS1/ROMs, Up/Down select a processor, Square to grab+move, Cross to toggle on/off, Triangle to re-run on everything.
- `NotificationBubble` shows progress (title, stage, bar, counter); a failure is a notification line with the error.

**The manifest** — `processor.ini` in each processor's folder:
- Name, Description, Author, Version, Icon
- `Kinds=games-folder|ps1|roms-folder|rom` (which sequences it belongs to)
- `Match=<file pattern>` (candidate if its files match)
- `Systems=<list>` (for ROM processors, which systems)
- `Order=<number>` (author's suggestion for new processors, user's order is what matters)
- `Timeout=<seconds>` (heartbeat expectation)

**Platform resolution** — same as Apps: one binary per platform key (`psc`, `rpi`, `rpi64`, `pcusb`, `win`, `linux-*`, `dev`), resolved by `AppManifest`. First existing key wins.

**Protocol** (stdout line by line, exit 0 = success):
- `#Starting - <title>` — processor name and version
- `#<stage>` — current step
- Progress: `0..100` (percentage) or `n/m` (counter)
- `#WARN - <message>`, `#ERROR - <message>`
- `#DONE` (success); exit non-zero = failure
- Stderr goes to `System/Logs/processors.log` prefixed `! `

**Environment** (`LaunchPlan::env`):
- `AB_PROCESSOR_PROTOCOL=1`, `AB_ROOT`, `AB_GAMES_DIR`, `AB_ROMS_DIR`, `AB_RDB_DIR`
- `AB_TMP=/tmp/abproc/<name>` (RAM on console)
- `AB_PLATFORM(_KEYS)`, `AB_LANGUAGE`, `AB_VERSION`

**Output rules**:
- Writes as `<file>.part`, renamed when complete, original deleted only after.
- Idempotent — same input twice gives the same output.
- All writes inside the target.
- One line output at least every `Timeout=` seconds.

**State file** (`<state>/processors.state`):
- Version + per-target (path + CRC) digest
- Reason an unchanged target is never processed twice
- Processor change or target change forgets its state

**Logging** — `System/Logs/processors.log`:
- Header per run: timestamp, processor name/version, full argv, start time
- Every stdout/stderr line
- Exit code and duration

**The first processor** — `proc_unzip` (separate repo `autobleem2/proc_unzip`):
- Reads `.zip`, unpacks to folder
- Detects multi-disc game folders and reorganizes them
- `.7z` and `.rar` support (libarchive + liblzma)
- Bundled with packages (every platform); users may add their own

**Tools**:
- `tools/proc_check.py <folder>` — validation for processor authors (manifest, protocol, leaves, idempotence, stop-restart on scratch copy)

## Verified

- Windows dev build: end-to-end unzip before scan, bubble progress, sorting screen.
- Linux in CI image.

## Still open

- Console and Pi 400 hardware run.
- Next plan: `.7z`, the Store, launch-time processors, signatures.
