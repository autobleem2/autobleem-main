# A quiet stick

Archived plan (done 2026-09-24). The full text is in git history: `git log -- docs/archive/quiet-stick-plan.md`.

The stick is written only when the user's state changes — a save, a card, a kept resume slot, a setting the player changed, a game added or removed. Everything else is in RAM or not written at all. Logs, intermediate files and rewrites of unchanged data go to RAM or nowhere.

## The decisions (the owner, 2026-09-24)

1. **The log switch: both** — config.ini `keeplogs` with its Options row, and the `System/Logs/keep` marker file.
2. **RetroArch's save on exit: switchable** — config.ini `rapersist`, Options row "Persist RetroArch config", applied through an append file.
3. **Crash folders: last 3 kept** — `System/Logs/crash-<n>/`, and a notification on the next start.
4. **Refused games: shown in the Game Manager**, no file.

## What was built (2026-09-24)

**Merged** into develop in all five repos (launcher, autobleem-core, pcsx-abnxt, pcsx-ab, autobleem-appliance) on 2026-09-24, published as nightly v2.0.0-alpha2-117-g497b9bc.

Implementation phases:
- **Logs to RAM**: `AB_RUNTIME_DIR` = `/tmp/autobleem` (console), `/run/autobleem` (Linux), `<root>/System/Runtime` (Windows/dev); the launcher exports it into all children. File appender writes `<runtime>/logs/autobleem.log` (256 KB x 2 in RAM). The keep-logs marker and config.ini `keeplogs` switch between RAM and the stick.
- **Write only what changed**: `DirEntry::writeFileIfChanged` helper in the engine; `IniFile::save`, `ConfigFileEditor` go through it. Scan no longer rewrites every game's `Game.ini`, `.m3u`, playlists or database when nothing changed. History ranking updates only the rows that move.
- **Intermediate files off the stick**: emulator exit state to `$AB_RUNTIME_DIR/exit/`, copied into a kept resume slot only; memory cards swapped in place by path, not copied; RetroArch via `--appendconfig` to a RAM file, core options in a copy in RAM.
- **Refused games**: regional.db `FAILED_GAMES` table, shown in the Game Manager; the scan writes the list only when it differs from what is there.

## Measured on the Pi 400

Scenarios with the nightly (after restart to the new session script, `/run/autobleem`):

| Scenario | Written to data partition |
|---|---|
| 5 min idle at carousel | **0 KiB, 0 files** |
| rescan with no game changed | 11 KiB: fingerprint + test file + old session's tee (both `.online-probe` and covers dbs opened read-write **fixed** the same night) |
| first start of new build | `config.ini` once + one `Game.ini` (one-off update) |
| boot to carousel | **4 KiB (8 sectors), no file** — mount's own volume flag |
| PS1 game + kept slot + RetroArch game | 2201 KiB, 9 files (with `abfeatures` in place): slot kept, card, regional.db (last played / history), RetroArch config + restore. Exit state went to RAM. |

## Still open

- Resuming from a kept slot (`AB_LOAD_STATE`, not exercised yet).
- The same measurements on a console.
- Verify on RetroArch 1.22 that `--appendconfig` + restore work as expected.
- Verify the exit dir on a console with a real game.
