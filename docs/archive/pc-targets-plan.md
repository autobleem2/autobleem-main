# PC targets: the PC-USB stick and the Windows product

Archived plan (done 2026-09-20). The full text is in git history: `git log -- docs/archive/pc-targets-plan.md`.
What was built is in `docs/history/pc-usb-stick.md` and `docs/history/windows-product.md`.

## The two products

- **PC-USB**: a bootable stick image for 32-bit x86 PCs, Debian 12 Bookworm i386 (the last Debian with an
  i386 kernel; LTS to mid-2028), behaving like the Pi appliance - launcher on tty1 over kmsdrm, an exFAT data
  partition, the first-boot install UI, the same online update. Built from packages (mmdebstrap + GRUB for
  BIOS, UEFI-ia32 and UEFI-x64).
- **Windows**: an NSIS installer, per-user and without admin rights; RetroArch installed silently from the
  official setup exe; self-update by downloading the next `AutoBleemSetup-<v>.exe` and running it `/S`.

## The decisions still explaining the code

| question | decision |
|---|---|
| Build flavours | One CMake cache string **`AB_TARGET` = `psc \| rpi \| pcusb \| win \| dev`** -> one `AB_PLATFORM_<X>`; the sources test derived macros named for what they mean: `AB_DEBUG_HOST` (dev only), `AB_APPLIANCE` (rpi, pcusb), `AB_ROOT_RELATIVE_LAYOUT` (all but psc), `AB_HAS_INTERNAL_GAMES` (psc, dev). Never the CPU or OS - an i386 Linux build used to compile as the console. |
| Dev vs product on Windows | `make_win.sh` stays `dev` (window, keyboard-as-pad, splash runner); `--product` / `ci/build.sh win` is `AB_TARGET=win`. |
| Where things differ | Data in `resources/platform/<platform>.ini`, not `#ifdef`: `launch_mode=script\|direct`, `core_extension` (`.dll` on Windows), `retroarch_catalog`, `pcsx_dir`. |
| config.ini on Windows | `Environment::setStateDir()` - `<data>\System` on win, the working path elsewhere; the writers moved to it. |
| Launching on Windows | `LaunchPlan {exe, args, cwd}` built by `LaunchService` - script argv or direct exec, testable on any host; `WinProcessRunner` (CreateProcessW) minimises the launcher for the run. |
| No console flashes | `System::runShellCommand()` (cmd with `CREATE_NO_WINDOW`) is the default runner of OnlineAssets and UpdateService. |
| Fullscreen | Always, on every real target - launcher, emulators, RetroArch (the owner's rule); only `dev` keeps a 1280x720 window. |
| Windows setup helper | `AutoBleemWinSetup.exe` next to AutoBleemInstaller, sharing its core (now `WindowsInstallJob` in core's `ab_installer`). |
| Kernels on the stick | `linux-image-686-pae` and `-686`, GRUB picks with `cpuid -p`; `-march=i686 -mtune=generic`, no SSE2. |
| The image build | `make_pc_image.sh --mount` in a privileged container - the server's kernel refuses user namespaces there. |
| Payload | `payload_rpi` -> `payload_linux`, one `install.sh` with `PLATFORM=rpi\|pcusb`. |

## Lasting gotchas

- Secure Boot must be off (unsigned GRUB and i386 kernel). SmartScreen warns on the unsigned setup exe
  (code signing: `docs/code-signing.md`).
- OneDrive may redirect Documents; the installer shows the resolved data path and offers `%USERPROFILE%`.
- exFAT + tar as root: stage updates on the root fs with `--no-same-owner`.
- Nvidia: nouveau with `firmware-misc-nonfree`; no proprietary driver.

## Still open

- The PC stick on 32- and 64-bit UEFI and on real hardware, with a pad (only the BIOS VM has booted it).
- The Windows self-update round trip against the site (C3), with the testing channel.
