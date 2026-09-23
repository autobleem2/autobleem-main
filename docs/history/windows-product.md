<!-- Moved from the launcher's CLAUDE.md (autobleem2/autobleem) on 2026-09-23 when the project's
     knowledge went to autobleem-main. Paths without a repository name are the launcher's. -->

# The Windows product (2026-09-20, `win`)

The second PC target of `docs/pc-targets-plan.md` (phases B and C): AutoBleem as a Windows program from an
NSIS installer - **per user, no administrator rights** (the owner's call), the program in
`%LOCALAPPDATA%\Programs\AutoBleem`, the data tree (games, settings, themes, RetroArch) in a folder of the
user's choosing, `Documents\AutoBleem` by default. **Full screen always** (the owner's rule for every real
target): the launcher, pcsx-ab, RetroArch. `AB_TARGET=win` is a real target, not a dev host: `make_win.sh
--product` -> `build_win_product/` on the PC, `ci/build.sh win` in the image (the mingw toolchain with
`AB_TARGET=win` into `build_mingw_product/`, `make_win_package.sh --product`, `makensis` ->
`dist/win/AutoBleemSetup-<v>.exe`; nsis and p7zip joined the image's `all` stage). What it took, in order:

- **B1 - where things are.** `Environment::setStateDir()/getPathToStateDir()`: what a program writes about
  itself - `config.ini`, the scan's fingerprints and report files, the online probe files - goes there;
  the default is the working path (the console, the Pi and the PC stick unchanged), the Windows product sets
  `<data>/System` (the program folder is not the user's to write). `EnvironmentSetup::fromWindowsInstall(
  HostFacts)`: the data root is the registry's `DataRoot` (what the installer wrote), else `dataroot.txt`
  next to the exe (a portable copy), else `<Documents>\AutoBleem`; the tree is made and the shipped
  `<program>/Themes` copied in - once at first, and since 2026-09-22 again whenever the program's copy
  differs from what the data tree's copy was made from (a `.shipped` stamp with a digest of every
  file's name, size and MD5; a copy without the stamp is refreshed once): the owner's installed launcher
  kept reading the first install's ab2 and never saw the resume-slot glow. A user's edit of a shipped
  theme lasts until a release changes that theme (the manual says to copy it under a new name);
  `fromArguments()` with no argument is that on `AB_PLATFORM_WIN`.
  `WindowsHost` (`core/services/windows_host.*`) reads the facts (`GetModuleFileNameW`, `RegGetValueW`,
  `SHGetKnownFolderPath`); the decision is tested on every host with hand-filled facts. `win.ini`:
  `RetroArch/bin` with `.dll` cores, `launch_mode=direct`, `pcsx_dir=emu`, `pcsxnxt_dir=emunxt`, no
  RetroArch catalog (libretro's own build there, not ours to update).
- **B2 - the launches.** A launch is a `LaunchPlan` (exe, args, cwd) built by `LaunchService::planPcsx/
  planRetroArch/planApp` and run by the `ProcessRunner` - script mode (`rc/launch.sh` with its ten
  arguments) unchanged, `launch_mode=direct` runs the programs themselves. **Both PS1 emulators, chosen as
  on the console and the Pi** (the owner's ask): Options -> "PS1 Emulator" picks `emu/` (pcsx-ab) or
  `emunxt/` (pcsx-abnxt); a chosen folder with no binary falls back to the other, both missing to RetroArch's
  PS1 core - launch.sh's order. They start differently: **pcsx-abnxt** from its folder with `-dotdir <save
  states> -biosdir <System/Bios> -fullscreen` (the options its branch `feature/launch-dirs` adds -
  `E:\Programming\pcsx-abnxt-launch`, a worktree, pushed and not yet merged: the other session had
  uncommitted work on that repo's `develop`); the **old pcsx-ab**, which knows only launch.sh's run
  directory, from `System/runpcsx` laid out with directory links (`System::makeDirectoryLink` - a junction
  through `mklink /J` on Windows, no privilege needed, NTFS only; a symlink elsewhere, the target made
  absolute) and cleared after (`removeDirectoryLink` - the link, never its target); a FAT stick where no
  junction can be made falls back to RetroArch's core. RetroArch: the first `retroarch_binary` that exists,
  `--config <its cfg> -L <core> --fullscreen <file>`. `System::runAndWait` is real on Windows
  (`CreateProcessW`, the command line quoted by the CRT's rules, `CREATE_NO_WINDOW`), `WinProcessRunner`
  keeps the display and has the window minimised for the run and raised after (`Platform::minimizeWindow/
  restoreWindow`). Verified on the PC: the product started pcsx-abnxt full screen with `-dotdir` (its
  profile made under the game's save-state folder), the launcher back when the emulator went.
- **B3.** `System::runShellCommand` (cmd with `CREATE_NO_WINDOW`; `OnlineAssets`/`UpdateService`'s default
  runner - no console flashes over the launcher; cmd parses its own line, `/c "<line>"`, so it is built by
  hand) and `System::diskSpace` (statvfs / `GetDiskFreeSpaceExW` - the free space measured on every
  platform, the `df` pipeline is gone). `tests/core/test_system.cpp`.
- **B4.** `GuiBase/Platform` take a fullscreen flag (`SDL_WINDOW_FULLSCREEN_DESKTOP`, no mode change); the
  `Renderer` draws the 1280x720 canvas as big as fits, centred - black bars on a desktop of another shape,
  through the window target's viewport. `Gui::fullscreen()` is true on everything but the dev build
  (`AB_WINDOWED=1` asks a product build for a window). The exe is GUI-subsystem (`-mwindows`; started from
  a console it attaches to it, so `--sysinfo` prints) with the icon (`tools/make_icon.py` - a PNG-in-ICO from
  `tools/repo_icon.png`, stdlib only - `src/win/autobleem.ico`) and a version block (`src/win/autobleem.rc.in`).
  `make_win_package.sh --product` stages the program folder as `autobleem-win-product-<v>.zip`: the exe,
  its resources, the DLLs (on MSYS2 every DLL `ldd` finds, so the folder runs on a PC without it),
  `AutoBleemWinSetup.exe`, `Themes/`, `emu/` and `emunxt/` from a local build (`AB_PCSX_WIN_DIST` /
  `AB_PCSXNXT_WIN_DIST`) or the site's win64 package of each (`emu/<name>/latest.json`),
  `dataroot.txt.example`. Two things the first run showed: the no-cover-db warning was drawn before the
  theme was loaded (a black screen - now after `display()`), and the `AutoBleem.lpl` export failed without
  a RetroArch playlists dir (skipped now).
- **C1 - the setup helper.** `AutoBleemWinSetup.exe` (`apps/installer`, its CLAUDE.md): the data tree from
  the download repository - the cover databases, RetroArch (the site's repack of libretro's own Windows
  build, else the official `RetroArch.7z` unpacked by the new **`ableem::SevenZipArchive`** over the LZMA
  SDK's 7z reader vendored as `lib_ableem/third_party/lzma-7z` - the official setup exe wants administrator
  rights, checked), the cores (the site's `win/cores` pack, else one zip per core from buildbot), the BIOS
  files (`win/bios`, `tools/biospack.py --arch win64`), the samples. The site side: `ci/build_retroarch.sh
  win64` (the 7z repacked as a tarball), `ci/build_cores.sh win64`, `repo_publish.sh win-retroarch|
  win-cores|win-bios`, `repo_index.py`'s `index_win`.
- **C2 - the installer.** `installer/windows/autobleem.nsi`: welcome, the program folder, the data folder
  (its own page; a OneDrive folder warned about), the components (covers, RetroArch, BIOS, samples),
  then `AutoBleemWinSetup --run` with them (`--run`: straight to its progress page - started without it,
  from the Start Menu's "AutoBleem Setup", the helper asks the questions again to add RetroArch later; the
  owner saw the questions twice before that flag). The choices go to `HKCU\Software\AutoBleem` so a silent
  `/S` run (an update) repeats them; Start Menu and Desktop shortcuts, the Add/Remove entry, an uninstaller
  that leaves the data folder. `.onInit` waits for a running launcher (the mutex below). Run on the PC:
  the wizard by the owner, then `/S` as an update (22 s, covers kept, the fingerprints removed). **Start
  it from PowerShell or Explorer** - the MSYS2 shell rewrites `/S` into a path and the wizard shows.
- **C3 - the launcher's own update.** On `AB_PLATFORM_WIN` the launcher holds the mutex
  `Global\AutoBleemLauncher` (one instance; the installer's cue), looks for the site's `win-setup`
  package (no RetroArch check), and after the download starts the installer detached
  (`System::startDetached`) with `/S /RESTART` and leaves; the installer waits for the mutex, replaces the
  program folder, re-runs the helper `--quiet --update` and starts the new launcher. Not yet exercised end
  to end against the site (no `win-setup` published before the first `ci/build.sh win`).

The site shows the PC platform as two pills, *PC USB stick* and *Windows* (`repo_index.py`'s `tabbed()`
second level: `<h3 class="subtab">` headings inside a section; `#pc-windows` opens it). Not done: pcsx-ab's
Windows build with `-dotdir` (the old emulator runs from the junction run dir instead), a real game
through the whole chain (the fake disc boots to "Booting up..."), and the tests under wine in the image.

