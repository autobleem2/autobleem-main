# pcsx-abnxt - the next emulator (`github.com/autobleem2/pcsx-abnxt`)

What pcsx-abnxt is, how it ships next to pcsx-ab, and what the two share. The launcher<->emulator contract
itself (arguments, directories, files) is `docs/emulator-contract.md`.

## The two emulators

- **pcsx-ab** (`autobleem2/pcsx-ab`) is a 2017 upstream snapshot (r22 + 25 commits - what Sony's firmware
  took) with Sony's and our patches.
- **pcsx-abnxt** (`autobleem2/pcsx-abnxt`) is a fork of `notaz/pcsx_rearmed` at **r26** with our
  `autobleem2/libpicofe` fork as a submodule. It re-implements what Sony and we added (front buttons, the
  resume-point contract, disc change, the menu, filters, two pads, `SET_BY_PCSX`) on top of what upstream has
  now: aarch64 dynarec, lightrec, C-SIMD gpu_neon, lid emulation, SlowBoot, a per-serial hack database.
  Sony's 131-serial per-title hacks are **not** ported wholesale - ported on evidence. Its `docs/reference/`
  inventories the old delta; its CLAUDE.md holds the decisions.
- **Both ship, the user picks**: Options -> "PS1 Emulator" (`config.ini` `emulator` = `pcsx-abnxt` |
  `pcsx-ab`); **`pcsx-abnxt` is the default** and the fallback for any other value (since 2026-09-21). It is
  `launch.sh`'s 10th argument; the scripts run `Autobleem/bin/emu/pcsx-ab` or `Autobleem/bin/emunxt/pcsx-ab`
  (same binary name and `plugins/` layout; `emunxt-arm64/` for a 64-bit Pi) and fall back to `emu/` when the
  chosen folder has no binary. `ci/build.sh` builds it into `emunxt/` from `AB_PCSXNXT_DIR` / `../pcsx-abnxt`.

## What they share

- **Save states interoperate**: pcsx-abnxt reads and writes pcsx-ab's (Sony's) save-state layout
  (`libpcsxcore/state_sony.c`, its CLAUDE.md's "The save-state layout") - Sony had added fields upstream never
  had, shifting everything after the GPU. A game left in one continues in the other; an HLE-BIOS state is
  refused either way. pcsx-ab keeps the GPU busy bit in its own copy of GPUSTAT; it has to be handled on
  load, or a state saved in a busy moment hangs (Crash on its loading screen).
- **Every way out of a game leaves it as it is at that moment** (menu button held, Reset, Power): the autosave
  ring (Sony's ~10 s-old snapshot) is gone.
- **A game's config has one source**: both load `pcsx.cfg` then `.pcsx/pcsx.custom.cfg` over it. Their menus'
  one "Save settings for this game" writes only the custom file (foreign keys kept, Bios back to
  SET_BY_PCSX). While it exists the launcher's editor greys the PCSX rows behind "Unlock the settings",
  which deletes it (back to the launcher's values); a saved screen shape beats the global Widescreen option;
  an old `autobleem.cfg` / `cfg/<label>-<id>.cfg` becomes the custom file (`PcsxConfig::migrateLegacy`).
- nxt-only editor rows, shown only while `emulator` is `pcsx-abnxt`: **"Smoothing"** (`soft_filter` 0-4:
  None / Scale2x / Eagle2x / HQ2x / HQ3x) and **"Sony hacks"** (`sonyhacks` 0/1: the configuration part of
  Sony's per-title hacks for the disc's real serial - off unless a game asks).

## Language

- pcsx-abnxt's own screens speak every launcher language (not Sony's 13 PNG sets): `lang/<Name>.txt` in the
  launcher's `Key=Value` format, chosen by **`-language <Name>`** - `config.ini`'s `language`, `launch.sh`'s
  **11th argument**, passed to nxt alone (pcsx-ab would take an unknown option for a file to run).
- The scripts link the emulator's `lang/` and the launcher's `fonts/` into the run directory: the UI font is
  Selawik Light (`skin/ui.ttf`), and `Chinese_Simplified.txt` names `NotoSansSC-Regular.otf` (`|@font|`).
- Release tags: `r26-alphaN` sorts above the numbered `r26-N-g...` builds (`pcsx_version_key` on the site).

## Still open

- pcsx-abnxt's compatibility pass and release (its port plan's phases 7-8) are deferred to the owner's testing.
