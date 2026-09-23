<!-- Moved from the launcher's CLAUDE.md (autobleem2/autobleem) on 2026-09-23 when the project's
     knowledge went to autobleem-main. Paths without a repository name are the launcher's. -->

# Console tools (`apps/`, 2026-09-18) - and one PC tool - moved out on 2026-09-23 (see above)

`apps/installer/` (2026-09-20) and `apps/updateroms/` (2026-09-19) are the odd ones out: **PC** programs. The
installer is described under "RetroArch for the console" and in its own CLAUDE.md. UpdateRoms is a program, `UpdateRoms.exe`, built on the dev
hosts only (root `CMakeLists.txt` skips it for `arm`/`aarch64`), that scans a console stick or a Pi card
sitting in a card reader - `UpdateRomsJob` (core, tested) over the same `RetroArchScanner`/`CoreInfoTable`/
`OnlineAssets` the launcher's scan uses, writing the target's paths. **A plain Win32 window, no SDL, no
AutoBleem theme** (the owner's call), linked `-static`: one 540 KB exe with no MinGW DLLs.
`tools/make_updateroms_bundle.sh` makes the folder for a stick (a Release build in `build_updateroms/`),
`make_usb.py` stages it into `usb/UpdateRoms/`. Its own CLAUDE.md has the rest.

The two standalone tools the console runs from `Apps/` - **PSC-Bios** (`apps/pscbios/`: WiFi, timezone,
the gamepad mapping wizard) and **ABFlashKit** (`apps/abflashkit/`: the kernel flasher) - were 2020 forks
of the old AutoBleem GUI with their own copies of everything (`psctools/` in git history). They are targets
in this tree now, built on `ab_classic`: each has a `<tool>_core` static library (SDL-free, links `ab_core`,
tested from `tests/apps/`) and the program on top, its own `CLAUDE.md`, `resources/` (what ships next to
its binary in `payload/Apps/<tool>/`) and `resources/lang/` (Key=Value, validated by `make_win.sh`; the
tool loads the main GUI's language file first, then its own on top - `Lang::loadMore`). They draw with the
main GUI's theme through `AppBase` and read its `config.ini` - `EnvironmentSetup::forTool()` sets the
working path to the launcher's resources dir and pins `Env::getAppDir()` to the tool's own folder. The
console-only work is behind an interface with a fake for the dev host (`ConsoleBackend` -> `AbnetBackend` /
`FakeBackend`), the `ProcessRunner` pattern, so `usb/Apps/<tool>/<tool>.exe <usb root>` runs on Windows for
a visual test (`tools/make_usb.py` stages it, `tools/win_drive.ps1 -Tool <tool>` drives it). `make_psc.sh`
builds them next to the launcher, gates them with `check_psc_binary.sh`, packs them and copies each binary
plus its `resources/` into `payload/Apps/<tool>/`; a Pi does not build them. `tools/format.sh`,
`tools/lint.sh` and `.clang-tidy` cover `apps/`.

