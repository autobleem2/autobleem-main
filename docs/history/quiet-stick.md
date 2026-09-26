# The quiet stick

How the launcher was refactored so the stick is written only when the user's state changes. Logs and intermediate files go to RAM.

## Implementation (2026-09-24)

**Five repositories touched:** launcher, autobleem-core, pcsx-abnxt, pcsx-ab, autobleem-appliance. Branches `feature/quiet-stick` merged into develop on 2026-09-24.

**The runtime directory** — every log and every hand-over file in a platform-specific tmpfs:
- Console: `AB_RUNTIME_DIR=/tmp/autobleem` (tmpfs at every boot)
- Pi/PC stick: `/run/autobleem` (systemd `RuntimeDirectory`)
- Windows/dev: `<root>/System/Runtime`

The launcher exports `AB_RUNTIME_DIR` into all children (scripts, emulators, Apps).

**Logs**: autobleem.log (256 KB x 2 in RAM) when `keeplogs` is off (default) or the marker `System/Logs/keep` is missing. When either is present, logs go to `System/Logs` on the stick. `AB_out.txt`/`AB_err.txt` hold warnings/errors + children's output. A crash copies `<runtime>/logs/` to `System/Logs/crash-<n>/` (last 3 kept); the launcher shows a notification once (`System/Logs/crash-<n>/.new` marker).

**Write-if-changed**: `DirEntry::writeFileIfChanged` in the engine. Every game's `Game.ini` and every scan file (`Game.ini`, `.m3u`, playlists, fingerprints) written only when the content differs. The history ranking updates only rows that move. `ConfigFileEditor` batches writes through `replaceProperties` (one read + one write per batch).

**Refused games** — instead of `gamesThatFailedVerifyCheck.txt`: regional.db `FAILED_GAMES` table (PATH, FOLDER, REASON), replaced in the scan's transaction only when the list differs. The Game Manager lists them under the games with the reason in the pane; Square offers "Delete folder".

**Intermediate files off the stick**:
- Exit state: emulator's exit state (`.000`, PNG, `filename.txt`) to `$AB_RUNTIME_DIR/exit/`, copied into a kept resume slot only. Both emulators (pcsx-abnxt, pcsx-ab) get `-exitdir` option.
- Memory cards: given by path to the emulator (`-mcd1 <path>`), no copies. The set's card written in place by the game.
- RetroArch: per-game settings and core options to `$AB_RUNTIME_DIR/ra-append.cfg` (applies only for this launch, read-only on the stick). `--appendconfig` applied by the launch script.

## Measured on Pi 400 (nightly v2.0.0-alpha2-117-g497b9bc)

After restart to the new session script (from that point forward, `/run/autobleem` is the runtime):

| Scenario | Data partition writes |
|---|---|
| 5 min idle at carousel | **0 KiB, 0 files** |
| Rescan with no change | 11 KiB (fingerprint, test file, one old session's tee) |
| First start of new build | `config.ini` + one `Game.ini` |
| Boot to carousel | **4 KiB (8 sectors)** — FAT mount's own volume flag only |
| PS1 game + kept resume slot + RetroArch game | 2201 KiB, 9 files (slot, card, history, RetroArch config). Exit state was in RAM. |

Without `abfeatures` file in emulator binary (the issue): 2666 KiB (temporary state copied into slot).

## Still open

- Resuming from a kept slot (`AB_LOAD_STATE` not exercised yet).
- Same measurements on a console.
- Verify on RetroArch 1.22 that `--appendconfig` + restore work without baking per-game keys into the global config.
- Verify the exit dir on a console with a real game.
- Console: slot resume test, both kernels (stock + AutoBleem).
