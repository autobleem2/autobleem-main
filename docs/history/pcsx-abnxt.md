<!-- Moved from the launcher's CLAUDE.md (autobleem2/autobleem) on 2026-09-23 when the project's
     knowledge went to autobleem-main. Paths without a repository name are the launcher's. -->

# pcsx-abnxt - the next emulator (`github.com/autobleem/pcsx-abnxt`, started 2026-09-20)

pcsx-ab (`autobleem/pcsx-ab2`, `E:\Programming\pcsx-rearmed-develop`) is a 2017 upstream snapshot (master
`bebe989b`, r22 + 25 commits - what Sony's firmware took) with Sony's and our patches; it stays the shipped
emulator until pcsx-abnxt's phase 8. **pcsx-abnxt** (`E:\Programming\pcsx-abnxt`) is a public GitHub fork of
`notaz/pcsx_rearmed` at **r26** with our own `autobleem/libpicofe` fork as the submodule, re-implementing
what Sony and we added (the front buttons, the resume-point contract, the autosave ring, disc change, the
menu, filters, two pads, `SET_BY_PCSX`) on top of what upstream has now - aarch64 dynarec, lightrec, C-SIMD
gpu_neon, lid emulation, SlowBoot, a per-serial hack database. Sony's 131-serial per-title hacks are **not**
ported (tested instead, ported on evidence). **Its port plan is complete** (2026-09-20 night, the owner's call -
the plan file is deleted, `git show` has it; the compatibility pass and the release, phases 7-8, are deferred
to the owner's testing) and `docs/reference/` is the inventory of the old delta with two patches; its CLAUDE.md the decisions. **Nothing on this side changes**:
the launch scripts, `pcsx.cfg`, `ResumePointService`'s files and `LaunchService` are the contract the new
emulator keeps, and the binary keeps the name `pcsx-ab` in the payloads.

**Both ship, the user picks** (2026-09-20, the owner's ask): Options -> **"PS1 Emulator"** (`config.ini`
`emulator` = `pcsx-abnxt` | `pcsx-ab`, **`pcsx-abnxt` the default** on every build and the fallback for any other value since 2026-09-21 (the owner's call; it was `pcsx-ab`) - `Config`),
which `LaunchService::launchPcsx` passes as the **10th argument** of `launch.sh`; the console's and the Pi's
scripts run `Autobleem/bin/emu/pcsx-ab` or **`Autobleem/bin/emunxt/pcsx-ab`** (the same binary name and
`plugins/` layout, `emunxt-arm64/` for the 64-bit Pi as `emu-arm64/`) and fall back to `emu/` when the
chosen folder has no binary. Both read the same `.pcsx` (pcsx.cfg, memory cards); a resume point one wrote
does not load in the other (save-state versions differ) - the game starts fresh. `ci/build.sh` builds
pcsx-abnxt into `emunxt/` from `AB_PCSXNXT_DIR` / `../pcsx-abnxt` next to pcsx-ab; `make_rpi_package.sh`,
`install.sh`, the PC installer's update list and `install_autobleem.py` know the folder. The checked-in
`emunxt/` binaries are `r26-24-g0f4727f1` (console, Pi armhf, Pi arm64); on a PC a game launch is a splash
either way, so the row is only carried through there. **A game editor row that exists for nxt alone**
(2026-09-21): "Smoothing" - pcsx-abnxt's software scaler on the PSX frame (None / Scale2x / Eagle2x / HQ2x /
HQ3x, the emulator's own menu row of the same name; `pcsx.cfg` `soft_filter` 0-4, hex like the levels;
`GameSettingsService::setSmoothing`, `PcsxSettings::smoothing`, `SmoothingNames`) - rendered and reachable
(`GuiEditor::lastOption()`) only while `config.ini`'s `emulator` is `pcsx-abnxt`, because the classic
pcsx-ab ignores the key; the language files carry `Smoothing:` (English and Polish translated). The same
for **"Sony hacks"** (a checkbox after it, `pcsx.cfg` `sonyhacks` 0/1, `setSonyHacks`, `PcsxSettings::sonyHacks`,
`Sony hacks:` in the language files): pcsx-abnxt applies the configuration part of Sony's per-title hacks
(SPU interpolation, SPU thread, interlace, region) for the disc's real serial over the cfg - a lever for a
game that misbehaves, off unless a game asks. pcsx-abnxt `r26-alpha1` (2026-09-21) is the first alpha on the
download repository, and `tools/repo_index.py`'s `pcsx_version_key` knows such tags sort above the numbered
`r26-N-g...` builds before them (it pruned the alpha on its first publish).

**The emulator speaks the launcher's language** (2026-09-20, the owner's rule: every language the launcher
has, Chinese included - not Sony's 13 PNG sets): pcsx-abnxt's own screens (its disc picker and the two
messages around it) are drawn from its own `lang/<Name>.txt` files, one per launcher language in the same
`Key=Value` format, chosen by **`-language <Name>`** - `config.ini`'s `language` value, the **11th argument**
of `launch.sh`, which both scripts pass on to nxt alone (the classic pcsx-ab would take an unknown option
for a file to run); direct mode adds it to the nxt command line. The scripts also link the emulator's
`lang/` and the launcher's `Autobleem/bin/autobleem/fonts/` (as `fonts/`) into the run directory: the
emulator's font is Selawik Light in its `skin/ui.ttf`, and `Chinese_Simplified.txt` names
`NotoSansSC-Regular.otf` (`|@font|`), which it finds through that link. The emulator packages carry
`skin/` and `lang/` since pcsx-abnxt `82d77a16`; `ci/build.sh` copies the whole dist into `emunxt/`. On
Windows (direct mode) Chinese needs a `fonts/` folder next to the emulator - not wired yet.

