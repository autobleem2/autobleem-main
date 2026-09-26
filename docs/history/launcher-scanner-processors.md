# Scanner processors - the launcher's protocol and integration

Moved verbatim out of the launcher's CLAUDE.md on 2026-09-26 (task D19). See also this repo's own `docs/history/scanner-processors.md` for the cross-repo implementation record (proc_unzip, the GuiProcessors screen) - the two files cover the same feature from different angles and were written separately, so neither is a subset of the other.

## Scanner processors (2026-09-24, autobleem-main `docs/archive/scanner-processors-plan.md` and `docs/history/scanner-processors.md`)

**What a processor is.** A community console program in `System/Processors/<name>/` (`processor.ini`, a
binary per platform key in `bin/{key}/`, resolved by `AppManifest`), run by the scan over the games before it
reads them: it can turn a format the launcher does not read into one it does, or change a game's data (a
patch, a mod). The example and the first one is **`proc_unzip`** (its own repository, one C++ file over
miniz for `.zip` and a vendored libarchive + liblzma for `.7z` and `.rar` since 1.1.0). Its source repository is named `proc_<name>` (the owner's rule).

**The protocol.**
- `--version`, `--ismine --ps1 <folder>` / `--rom <file> --system <name>` (exit 0 = mine), and
  `--start --games|--roms <tree>` (a folder processor, a "preprocessor") or `--start --ps1|--rom ...` (an item
  processor).
- stdout, a line at a time: `#Starting - <title>`, `#<stage>`, `0`..`100`, `n/m`, `#WARN - ...`, and
  `#DONE` (exit 0) or `#ERROR - ...`. Success needs both `#DONE` and exit 0 (`ableem::ProcessorOutput`).
- The environment: `AB_PROCESSOR_PROTOCOL=1`, `AB_ROOT`, `AB_GAMES_DIR`, `AB_ROMS_DIR`, `AB_RDB_DIR`,
  `AB_TMP` (`/tmp/abproc/<name>`, off the stick - RAM on the console), `AB_PLATFORM(_KEYS)`, `AB_LANGUAGE`,
  `AB_VERSION`.
- The rules a processor keeps: `<name>.part` then a rename, the original deleted only after; idempotent;
  inside its target; a line at least every `Timeout=` seconds.

**Where it runs.** `ScanService::runScan()`, first thing whoever asked for the scan: the folder processors of
the **PS1** sequence over `Games/` and of the **ROMs** sequence over `roms/`; then, after the loose-file move
and the disc merge, every game folder and ROM file through its sequence's item chain (up to three rounds,
for what a step produced), and only then the hierarchy and the scan. The user orders and switches them in
`System/Processors/sequence.ini` - the System menu's **Scanner processors** screen (`GuiProcessors`) edits it.
`<state>/processors.state` (`ProcessorState`: version + a names-and-sizes digest) is why an unchanged target
is never offered twice; `System/Logs/processors.log` has every run.
`AutoBleem::run()` suspends the processors that modify files around a game or RetroArch
(`setProcessorsSuspended`): a running one is stopped (interrupted), and resuming requests a scan. The games
fingerprint also counts the processors' `Match` files, and `*.part` is never counted. The launcher's bubble
shows a processor's progress (`ScanUpdate::processor`), and a notification line its warnings and failures.

**Code**: core `ProcessorOutput` (engine), `System::runStreaming`, `ProcessorCatalog`, `ProcessorSequences`,
`ProcessorState`, `ProcessorRunner` (`ProcessorProcess` is the test seam; `tests/support/proc_helper.cpp` a
scriptable fake processor), `ScanService`; the launcher `evoui/screens/evoui_processors.*`. The built-in ECM
decoding is untouched (the owner's call). **`tools/proc_check.py <folder> --games DIR --roms DIR`** is what an
author runs before publishing: processor.ini, `--version`, the protocol per kind, leftovers, writes outside
the target, idempotence and a stop-and-restart, all on scratch copies of the samples.

**The installers make the folder** (2026-09-25), with a `README.txt` saying what goes there, written only when
it is missing: core's `ProcessorCatalog::ensureFolder()` from `InstallerJob` (the stick) and `WindowsInstallJob`,
`payload_linux/install.sh` (here and in autobleem-appliance's copy), `payload/System/Processors/README.txt`
for the console package, and `tools/make_usb.py`. The launcher itself never needs it: no folder, no processors.

**Unzip is bundled** (the owner, 2026-09-25: a processor ships with the packages, an extension does not):
autobleem-appliance's `stage_processor` (`tools/release_assets.sh`) fetches `proc_unzip`'s package - its
`nightly` for a development build, its latest `v*` release for a release (its nightly while it has none) - and
keeps only the package's `bin/<key>/`: the console stick gets `System/Processors/unzip/` (laid over the stick),
the Pi and PC-stick packages `processors/unzip/` (copied by `install.sh`), the Windows program folder
`Processors/unzip/` (copied into the data tree by core's `WindowsInstallJob`). An update replaces its files and
never touches `sequence.ini`. `proc_unzip` is part of the nightly's fingerprint.

