# Scanner processors

Archived plan (done 2026-09-24). The full text is in the launcher's git history (autobleem2/autobleem): `git log -- docs/scanner-processors-plan.md`.

A processor is a console program the scan runs over the games before it reads them: it can turn a format the launcher does not read into one it does (a zipped `.bin/.cue`, `.7z`, `.rvz`, a future disc format), or change a game's data (a translation patch, a texture or audio mod, a region fix). Separate process, not a plugin; can be written in anything and crash without taking the launcher down.

## The decisions (the owner, 2026-09-24)

1. **Processors** in `System/Processors/<name>/`.
2. **Folder processor** (preprocessor) runs over the whole tree before anything is read; **item processor** runs on one game/ROM.
3. **A processor may delete the original**, but only once its output is complete: output is `.part`, renamed into place, then the original is deleted.
4. **Mods and patches run at scan time**, in place. The state file (`<state>/processors.state`) ensures a game is not patched twice.
5. **Repositories are named `proc_<name>`**.
6. **Folder processors are the first thing a scan does**, whatever started it (Re-Scan Games, the watcher, the start-up check).
7. **The user puts processors in order**: `System/Processors/sequence.ini` holds two sequences (PS1 and ROMs), one row per processor with on/off and the user's chosen order.
8. **`proc_unzip` is bundled** (the first processor and code example). A processor ships with packages; the launcher never needs an empty folder.
9. **The built-in ECM decoding stays** as it is.

## What was built (2026-09-24)

**Merged** into develop in autobleem-core and the launcher on 2026-09-24, verified on Windows and in CI. `proc_unzip` is public (`autobleem2/proc_unzip`, CI on, in every nightly).

Implementation:
- **Two kinds**: folder processors (run over `Games/` or `roms/` first), then item processors (run on each game/ROM in sequence order). The state file records what ran on what, so a unchanged target is never offered twice.
- **Manifest format**: `processor.ini` (Name, Description, Author, Version, Icon, `Kinds=games-folder|ps1|roms-folder|rom`, `Match=<file pattern>`, `Systems=<list>`, `Order=<number>`, `Timeout=<seconds>`).
- **Platform resolution**: one binary per platform key in `bin/{key}/`, resolved by `AppManifest` (same as Apps): first existing key wins.
- **Protocol** (stdout line by line, exit 0 on success): `#Starting - <title>`, `#<stage>`, progress `0..100`, counter `n/m`, warnings/errors `#WARN`/`#ERROR`, `#DONE` = success.
- **Environment**: `AB_PROCESSOR_PROTOCOL=1`, `AB_ROOT`, `AB_GAMES_DIR`, `AB_ROMS_DIR`, `AB_RDB_DIR`, `AB_TMP` (`/tmp/abproc/<name>`, RAM on console), `AB_PLATFORM(_KEYS)`, `AB_LANGUAGE`, `AB_VERSION`.
- **Sequences**: PS1 and ROMs sequences in `System/Processors/sequence.ini`, editable by the user in the System menu (L2+R2 -> Scanner processors). L1/R1 switch sequences; Up/Down pick a processor; Square to move, Cross to toggle on/off, Triangle to re-run on everything.
- **Logging**: `System/Logs/processors.log` has every run with a header, stderr prefixed `! `, exit code and duration.
- **The launcher's bubble** shows progress (`title - stage`, bar, `n/m` counter); a failure is a notification line.

## Measurement and verification

Built end-to-end on Windows (unzip before scan, bubble, sorting), Linux in CI image. `tools/proc_check.py <folder>` is what an author runs before publishing: validates the manifest, tests `--version`, the protocol per kind, checks for leftovers and writes outside the target, idempotence, and a stop-and-restart.

## Still open

- Not yet run on a console or a Pi.
- The next plan (`docs/scanner-processors-next-plan.md` in the launcher) is `.7z`, the Store, launch-time processors and signatures.
