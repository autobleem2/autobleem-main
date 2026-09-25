# The Windows product (`win`)

AutoBleem as a Windows program from an NSIS installer: where its files live, how it launches the
emulators, and how it installs and updates itself. Paths without a repository name are the launcher's.

## The model

- **Per user, no administrator rights** (the owner's call): the program in
  `%LOCALAPPDATA%\Programs\AutoBleem`, the data tree (games, settings, themes, RetroArch) in a folder the user
  picks, `Documents\AutoBleem` by default. **Full screen always** (the launcher, the emulators, RetroArch).
- `AB_TARGET=win` is a real target, not a dev host: `make_win.sh --product` on the PC, `ci/build.sh win` in
  the image (mingw, `make_win_package.sh --product`, `makensis` -> `AutoBleemSetup-<v>.exe`).

## Where things are

- `Environment::setStateDir()`: what a program writes about itself (`config.ini`, fingerprints, reports,
  probe files) goes to `<data>/System` on Windows (the program folder is not the user's to write); the
  working path elsewhere.
- `EnvironmentSetup::fromWindowsInstall(HostFacts)`: the data root is the registry's `DataRoot`, else
  `dataroot.txt` next to the exe (a portable copy), else `<Documents>\AutoBleem`. `WindowsHost`
  (`core/services/windows_host.*`) reads the facts; the decision is tested on every host with hand-filled facts.
- The shipped `<program>/Themes` is copied into the data tree at first and **again whenever the program's
  copy changes** (a `.shipped` stamp with a digest of names, sizes and MD5s). A user's edit of a shipped
  theme lasts until a release changes that theme - copy it under a new name.
- `win.ini`: `RetroArch/bin` with `.dll` cores, `launch_mode=direct`, `pcsx_dir=emu`, `pcsxnxt_dir=emunxt`,
  no RetroArch catalog (libretro's own build, not ours to update).

## Launches

- A launch is a `LaunchPlan` (exe, args, cwd) from `LaunchService::planPcsx/planRetroArch/planApp`, run by the
  `ProcessRunner`; `launch_mode=direct` runs the programs themselves instead of `rc/launch.sh`.
- Options -> "PS1 Emulator" picks `emu/` (pcsx-ab) or `emunxt/` (pcsx-abnxt); a missing binary falls back to
  the other, both missing to RetroArch's PS1 core (launch.sh's order).
  - **pcsx-abnxt** starts from its folder with `-dotdir <save states> -biosdir <System/Bios> -fullscreen`.
  - **pcsx-ab** knows only launch.sh's run directory: `System/runpcsx` is laid out with directory links
    (`System::makeDirectoryLink` - a junction, `mklink /J`, no privilege, NTFS only) and cleared after
    (`removeDirectoryLink` removes the link, never its target). Where no junction can be made (FAT), it falls
    back to RetroArch's core.
  - RetroArch: the first `retroarch_binary` that exists, `--config <cfg> -L <core> --fullscreen <file>`.
- `System::runAndWait` is `CreateProcessW` (CRT quoting rules, `CREATE_NO_WINDOW`); `WinProcessRunner` keeps
  the display and minimises the window for the run. `System::runShellCommand` builds `cmd /c "<line>"` by
  hand with `CREATE_NO_WINDOW` (no console flashes); `System::diskSpace` is `GetDiskFreeSpaceExW`.
- Full screen is `SDL_WINDOW_FULLSCREEN_DESKTOP` (no mode change); the 1280x720 canvas is drawn as big as
  fits, centred. `AB_WINDOWED=1` asks for a window. The exe is GUI-subsystem (`-mwindows`; attaches to a
  console it was started from, so `--sysinfo` prints), with an icon and a version block (`src/win/`).

## Install and update

- The program folder (`make_win_package.sh --product`): the exe, resources, every DLL `ldd` finds,
  `AutoBleemWinSetup.exe`, `Themes/`, `emu/` and `emunxt/` (a local build or the site's win64 packages).
- **`AutoBleemWinSetup.exe`** (autobleem-pc-tools) fills the data tree from the site: cover databases,
  RetroArch (the site's repack of libretro's Windows build, else the official `RetroArch.7z` through
  `ableem::SevenZipArchive` - the official setup exe wants admin rights), cores, BIOS
  (`tools/biospack.py --arch win64`), samples. `--run` goes straight to progress; started from the Start
  Menu it asks the questions again (to add RetroArch later).
- **`installer/windows/autobleem.nsi`**: program folder, data folder (OneDrive warned about), components,
  then the helper with `--run`. Choices go to `HKCU\Software\AutoBleem`, so a silent `/S` run (an update)
  repeats them; the uninstaller leaves the data folder. **Start it from PowerShell or Explorer** - the MSYS2
  shell rewrites `/S` into a path.
- **Self-update**: the launcher holds the mutex `Global\AutoBleemLauncher` (one instance), looks for the
  site's `win-setup` package, and after the download starts the installer detached with `/S /RESTART` and
  leaves; the installer waits for the mutex, replaces the program folder, re-runs the helper
  `--quiet --update` and starts the new launcher.

## Still open

- The Windows self-update has never been exercised end to end against the site.
- A real PS1 game has never been run through the whole Windows chain (the fake disc boots to "Booting up...").
- Chinese in pcsx-abnxt on Windows needs a `fonts/` folder next to the emulator - not wired yet.
- pcsx-ab has no Windows build with `-dotdir` (it runs from the junction run dir), and its Windows dev build
  crashes after loading any save state.
- The unit tests do not run under wine in the image.
