<!-- Moved from the launcher's CLAUDE.md (autobleem2/autobleem) on 2026-09-23 when the project's
     knowledge went to autobleem-main. Paths without a repository name are the launcher's. -->

# Raspberry Pi port (2026-09-17)

A second, *non-PSC* target: AutoBleem as an appliance on **32-bit Raspberry Pi OS Lite** (Bookworm or
Trixie), games on an exFAT partition of the SD card that behaves like the console's USB stick. **Running on
hardware since 2026-09-18**: a Pi 400 (BCM2711, same as a Pi 4) with 32-bit Trixie at <test-pi> - the
installer shrank its root to 16 GB, built RetroArch 1.22.2 from source, downloaded 109 cores; the launcher
boots into the carousel with sound over HDMI and starts games in pcsx-ab. What that first session fixed, in
order (each its own commit): the `init=` shrink that could never work (now an initramfs `local-premount`
script), a `YES` swallowed by apt, `cp -a` failing on exFAT, an empty unit file after a power cut (atomic
writes now), ALSA defaulting to the DualShock's USB audio (`autobleem-session` writes `/etc/asound.conf` for
the connected HDMI), the splash gone before the TV synced (`SplashSettleDuration`), **no game launching on
any platform** since the classic menu's removal (`startingGame` -> `MENU_OPTION_START` lives in
`AutoBleem::run()` now), the launcher's window being the DRM master (`Gui::releaseDisplay()` around a
launch - see "Conventions"), and pcsx-ab's `fclose(NULL)` in its console-only cpu-temperature watcher.
Things to know when working on the Pi over ssh: `plink -pw` from `C:\Program Files\PuTTY` (the harness
will not install ssh keys), `sudo -S` with the password on stdin, the journal is not persistent, and the
launcher's logs are `System/Logs/AB_out.txt`/`AB_err.txt` on the partition. PS1 games run in **pcsx-ab** as on the console: the Pi build from `E:\Programming\pcsx-rearmed-develop`
(`AUTOBLEEM_DIR=../autobleem-develop ./make_rpi.sh` copies its `build_rpi/dist/` into
`payload_linux/Autobleem/bin/emu/`, which is checked in like the console's `payload/Autobleem/bin/emu/`), and the
Pi `rc/launch.sh` builds `/tmp/runpcsx` exactly as the console's does (`.pcsx` -> the `!SaveStates` folder,
`bios` -> `System/Bios`, `plugins` -> `emu/plugins`, `-region 4`, `-load 1` on resume). The BIOS is the user's:
`System/Bios/romw.bin` + `romJP.bin` (pcsx.cfg's `Bios = SET_BY_PCSX` picks one by serial; HLE without them).
RetroArch's `pcsx_rearmed` core is only the fallback if the package shipped without pcsx-ab.

**RetroArch on the Pi** lives in `RetroArch/` on the data partition, in RetroArch's own standard tree (`cores`,
`info`, `system` = the cores' BIOS files, `roms` = the user's other-system games, `saves`, `states`,
`playlists`, `config`, `assets`, `autoconfig`, `database`, ...) with a generated `retroarch.cfg` whose every
directory key points in there; the Pi's `rc/launch_rb.sh`/`retroarch.sh` run `retroarch --config` on it, and
`Env::getPathToRetroarchDir()` is that folder on a Pi - **from `resources/platform/rpi.ini`** (`PlatformConfig`,
see the source map), which also names the Pi's PS1 core and where the `retroarch` binary may be; the
console's `psc.ini` keeps `retroarch/` and RetroBoot's core and binary. `roms/` gets a folder per system
named as RetroArch's playlists are, so *Import Content -> Scan Directory* on it lands in the set.
`install.sh` builds the **latest tagged RetroArch from GitHub on the Pi** (KMS/EGL/GLES, udev,
ALSA; no X/Wayland/Qt/ffmpeg) because libretro's buildbot has every armhf *core* but no armhf *frontend*;
`--retroarch apt` uses the distribution's package (1.19 on Trixie), `--retroarch none` leaves it alone. Then it
downloads all ~130 cores from `buildbot.libretro.com/nightly/linux/armhf/latest/.index-extended` and the
`info`/`assets`/`autoconfig`/`database-rdb`/`database-cursors`/`cheats`/`overlays`/`shaders_glsl` bundles from
`assets/frontend/` into that tree (`--no-downloads` skips). Cores are `dlopen`ed off the exFAT partition, which
works because the fstab entry has no `noexec`. Trixie renamed packages for its 64-bit `time_t` transition
(`libpng16-16t64`, `libegl-dev`/`libgles-dev`); `pkg_first_available` in `install.sh` tries each name.

- **Toolchain**: `toolchains/rpi/RPitoolchain.cmake` over the Windows-hosted "SysGCC for Raspberry Pi"
  (`C:\sysGCC\raspberry`, gcc 14.2.0, `arm-linux-gnueabihf`, sysroot rsynced from a real Pi). `./make_rpi.sh`
  configures and builds into `build_rpi/`. Target is `armv7-a + neon-vfpv4`, so Pi 2/3/4/Zero 2 - **not**
  armv6 (Pi 1/Zero). Invoke it the way `make_win.sh` is invoked, from the MSYS2 UCRT64 shell, but keep
  `C:\sysGCC\raspberry\bin` *off* PATH: its `rm`/`mkdir`/`make` shadow the MSYS2 ones and break the script.
  The compilers are named by absolute path in the toolchain file, so they do not need to be on PATH.
- **SDL2 discovery**: that sysroot has the SDL2/image/mixer/ttf runtime `.so`s but no `-dev` package - no
  headers, no unversioned symlinks, no cmake config. `toolchains/rpi/cmake/FindSDL2.cmake` defines all four
  imported targets itself (lib_ableem does one `find_package(SDL2)` and then links four bare names), with
  headers from `toolchains/rpi/sdl2-devkit/include` (copied from the MSYS2 SDL2 package - the public headers
  are arch-independent, and 2.32.10 vs the Pi's 2.32.4 is ABI-safe) and `IMPORTED_LOCATION` pointed straight
  at the versioned `.so`, which is what makes the missing symlinks irrelevant.
- **`AB_PLATFORM_RPI`** (`core/services/environment.h`), from `-DAB_TARGET=rpi` (the toolchain file forces
  it; see "The platform model" under Build). A Pi is a *real* target, not an `AB_DEBUG_HOST`: it forks
  emulators and halts for real. What `AB_APPLIANCE` (rpi or pcusb) changes: `GameQueryService::
  showInternalGames()` is hard `false` and the "Show Internal Games" row is gone from the Options menu (no
  `/gaadata`; `AB_HAS_INTERNAL_GAMES` is psc/dev only); `backup_internal.sh` is the console's alone.
  `AB_ROOT_RELATIVE_LAYOUT` (everything but the console) is what selects `EnvironmentSetup`'s "everything
  under the root given on the command line" branch, which the Pi shares with the 1-arg debug mode.
  `internal.db` is still *opened* on a Pi (it comes up empty) because `GameCatalogService`/
  `GameSettingsService` unconditionally expect the handle.
- Root `CMakeLists.txt`'s console branch is PSC-specific (it overwrites `CMAKE_CXX_FLAGS` with
  `-march=armv8-a+simd` and adds `/opt/toolchain/armv8-sony-...` to the include path), so the appliances
  (`rpi`, `pcusb`) take their own branch there, flags from the toolchain file. Without that the Pi build was
  getting armv8 code, which would SIGILL on a Pi 2.
- **Package**: `payload_linux/` is a sibling of `payload/`, not inside it, and is laid out as the package the
  Pi unpacks: `install.sh` + `README.md` at the top, `system/` for the host-side files (systemd unit, the
  `autobleem-session.sh` loop that replaces `rc/selection.sh`, the two shrink-root initramfs pieces, the plymouth theme), and the data-partition
  tree exactly as it lands on the exFAT partition - `Autobleem/rc/` (the Pi `launch.sh`/`launch_rb.sh`/
  `retroarch.sh`), `Autobleem/bin/emu/`, `Games/`, `Apps/` (empty dirs kept by `placeholder` files).
  `tools/make_rpi_package.sh` copies that tree, fills in `Autobleem/bin/autobleem` (`build_rpi/autobleem-gui`
  + `src/resources`, minus `internal.db`), `Autobleem/bin/db` (`db/covers*.db`) and `themes/`
  (`payload/Themes`), strips the placeholders, and tars it to `build_rpi/autobleem-rpi.tar.gz`. `install.sh`
  then finds or creates the exFAT partition, copies `Autobleem/ themes/ Games/ Apps/` onto it as they are, and
  puts the launcher on tty1 via systemd with `getty@tty1` disabled. Documented as `sudo bash install.sh`
  because a package built on Windows loses the executable bit.
- The installer's data partition is meant to be on the SD card next to the root (the owner's preference);
  with a root already expanded over the card that is `--shrink-root <GiB>`: an offline shrink at the next
  boot done **from the initramfs** - `system/shrink-root-hook.sh` packs e2fsck/resize2fs/parted/sfdisk/
  mkfs.exfat in, `system/shrink-root-premount.sh` is an initramfs-tools `local-premount` script that shrinks
  the root while it is still unmounted, restoring `cmdline.txt` first; `disarm_shrink()` removes both on the
  next run. The first attempt used `init=` the way Pi OS's own first-boot resize does, and that cannot work
  for a shrink: by the time `init=` runs the root is mounted, and `resize2fs` will not shrink a mounted
  filesystem (Pi OS only ever *grows*, which works online). A USB stick with an exFAT partition labelled
  `AUTOBLEEM` also works (`--disk /dev/sda`), but is not the intended setup.
- **Boot screen** (2026-09-18): the installer sets the KMS mode for the whole boot on the kernel command line
  (`video=HDMI-A-1:1280x720@60 video=HDMI-A-2:...`, `--hdmi-mode`; `config.txt`'s `hdmi_mode` is ignored by
  the KMS driver) - the launcher asks SDL for 1280x720 anyway, so plymouth and the launcher share one mode and
  the handover is not a modeset. The AutoBleem logo is a plymouth `script` theme, `payload_linux/system/plymouth/`
  (`splash.png` 1280x720 on black), installed to `/usr/share/plymouth/themes/autobleem` and packed into **every** installed kernel's initramfs
  (`update-initramfs -u -k all` since 2026-09-18 - the 32-bit image carries one per board, v6/v7/v7l/v8,
  and a card set up on the Pi 400 showed the stock theme when moved to a Pi 3; the shrink hook stays on the
  running kernel, `-k $(uname -r)`, it is for this board's next boot - never bare `-u`). `cmdline.txt` gets `splash plymouth.ignore-serial-consoles`,
  `config.txt` gets `disable_splash=1` in its own `[all]` section. The handover: `autobleem.service`
  `Conflicts=plymouth-quit.service` (the display-manager pattern, so systemd does not take the splash down
  when the system is up) and `autobleem-session` runs `plymouth quit --retain-splash` first thing, before
  even checking for the binary - plymouth holds the DRM master, SDL needs it. `--no-boot-splash` skips
  plymouth, `--no-quiet-boot` implies it. Verified on the Pi 400 the same day: plymouthd comes up from the
  initramfs (PID ~181, `vc4.ko` is in there - plymouth's initramfs hook pulls the DRM modules in even with
  `MODULES=dep`), `plymouth-quit.service` stays inactive, `plymouth-quit-wait` finishes in the same second
  as the session's "boot splash taken down", the CRTC is 1280x720, kernel to launcher ~8 s.
- **BIOS pack** (2026-09-18, per-architecture manifest 2026-09-19): `install.sh`'s `download_bios_pack()`
  fetches `system/biospack.txt` (armhf) or `system/biospack-arm64.txt` (arm64, picked by `$ARCH`) into
  `RetroArch/system/` - one line per file, `<sha256> <size> <url> <path>`, wget + `sha256sum` per file, a
  `.part` renamed once the hash checks out, files already right are skipped (so a re-run only repairs) - and
  `install_ps1_bios()` copies SCPH-5501/5500 to `System/Bios/romw.bin`/`romJP.bin` for pcsx-ab unless the
  user's own are there. `--no-bios` skips both; `--no-downloads` does not. Both manifests are written by
  **`tools/biospack.py --arch armhf|arm64`** from [RetroBIOS](https://github.com/Abdess/retrobios)
  (`install/retroarch.json`, pinned to one commit in `RETROBIOS_REF`) filtered to the cores that
  architecture actually has, minus `mame`, an allow-list of `Vendor/System` folders (everything
  `RA_ROM_SYSTEMS` has a folder for - consoles, handhelds and the Amiga/C64/MSX/Spectrum/PC-98/X68000
  computers - plus arcade, Neo Geo CD, ScummVM, Doom/Wolfenstein engine data) and path excludes (arcade
  `samples/`, MAME's `history/mameinfo/cheat.dat`, stella's `.wav`, x86 `.dll/.so/.dylib`, `dc/`,
  `kronos/`). **Where the core list comes from differs by architecture**: armhf reads RetroBIOS's own
  `install/targets/retroarch.json` (`"linux-armhf"` - 109 cores); arm64 has no matching entry there (only
  `android-arm64-v8a`/`osx-arm64`/`ios-arm64`, none of them this target), so it reads the real listing at
  `buildbot.libretro.com/nightly/linux/aarch64/latest/.index-extended` instead - the same URL
  `download_retroarch_content()` itself downloads cores from - via `biospack.py`'s `buildbot_cores()`. 222
  cores there vs 109 for armhf, so the arm64 pack is bigger: 694 files/230 MB vs 647 files/188 MB (both
  numbers as of the pinned commit; `--list` reprints them live) against 5.8 GB for RetroBIOS's whole
  RetroArch pack. **`buildbot.libretro.com`'s directory is `linux/aarch64`, not `linux/arm64`** - Debian's
  `dpkg --print-architecture` says `arm64`, the buildbot's own path segment does not match it; `install.sh`
  maps one to the other (`RA_ARCH=aarch64` when `$ARCH` is `arm64`) for both the cores download and the BIOS
  pack. `RA_ROM_SYSTEMS` names are RetroArch's rdb names (`database/rdb/*.rdb`) so a scan of `roms/` lands
  in the right playlist; `disksys.rom` (FDS) lives in RetroBIOS's `Arcade/FBNeo` folder, and DOS has a
  folder but no files (its only "BIOS" entries are x86 MIDI libraries).
  `--list` shows what is in and out, `--check DIR` verifies a `system/` folder. **No BIOS file is in this
  repository** - only their hashes and URLs.
- **Other systems run** (2026-09-18): ROMs in `RetroArch/roms/<system>/`, scanned by RetroArch's own Import
  Content (guide: `payload_linux/README.md`, "Games for the other systems"), launched from the RetroArch set
  in-process like pcsx. What that took: `RetroArchService::mapPlaylistPath()` (no double `/media` prefix on a
  Pi), only installed cores in the database->core table, the `showOptions()` null deref on a fresh screen
  with a foreign game (the launcher used to die on the way back and be restarted with the splash),
  `platform/<platform>.cores.cfg` (Genesis Plus GX over picodrive, whose Cyclone core segfaults on the Pi -
  unexplained), and blueMSX's `Machines/*/config.ini` in the BIOS pack (`EXTRA_SOURCES` in
  `tools/biospack.py`). `make_rpi.sh --debug` + the PC's cross gdb is how a Pi core dump gets read (gdb on
  the Pi hangs in `snd_pcm_open` on the mapped ALSA device).
- **The ROM scan, step 1 of `docs/retroarch-scanner-plan.md`** (2026-09-18): `ScanService`'s cycle goes on
  from `Games/` to the RetroArch ROM folders **when RetroArch is detected** - `ScanService::romScanEnabled()`,
  the binary the platform ini names exists and `retroarch_roms_dir` (a new key: `roms` on the console and
  PC, `RetroArch/roms` on the Pi -> `Env::getPathToRetroarchRomsDir()`) is a directory; RetroArch is optional
  on every platform and without it none of this runs. `ableem::RetroArchScanner` (engine, see lib_ableem)
  writes `<playlists>/<system>.lpl` per `roms/<system>/` folder from the file names alone, merged over what
  is there; the worker reports `WorkerEvent::Kind::PlaylistsWritten`, `poll()` has `RetroArchService::
  reloadPlaylists()` re-read them and the launcher refreshes its playlist names and the RetroArch set
  (`ScanUpdate::playlistsWritten`). `roms.fingerprint` (`GamesFingerprint::takeAllFiles`) is watched next
  to `games.fingerprint`; `ScanService::fingerprintsMatchDisk()` is the startup check for both.
  `resources/platform/roms_folders.cfg` names the folders that are not named as their database is
  (`Arcade` and `SNK - Neo Geo` -> `FBNeo - Arcade Games`). Verified on the PC's fake tree (`tools/make_usb.py`
  fakes a RetroArch install: stub binary, one `.info`, zipped ROMs) and **on the Pi 400** over its 848
  ROMs - RetroArch's own playlists survive byte for byte, a copy/delete lands in the carousel 17 s later;
  **not yet on a console.** **Step 2** (2026-09-19): with `<retroarch>/database/rdb/<system>.rdb` there,
  the worker names every ROM the database knows before the merge (`RetroArchScanner::identify` - a zip
  member by the CRC the archive records, a loose file by hashing it up to 64 MB, an arcade set by
  `rom_name`; a miss keeps the file's name, nothing is dropped) and an identified name replaces an
  unidentified one an earlier scan wrote. `RetroArchService::ensureMetadata()` then reads the same rdb
  once per playlist for publisher/year/players, which the meta panel shows for a RetroArch game the
  database knows. On the Pi: 679 of 848 named in ~2 s. **Step 3** (2026-09-19): `OnlineAssets`
  (`core/services/online_assets.*`) fetches, through the platform ini's `download_command` (`curl -sfL
  -m 20 ...` on the PC and the Pi, nothing on the console), the databases bundle when `database/rdb/`
  is empty and the box art of every ROM without one - only with config.ini `online=true` (Options: "Fetch
  box art online"), after one probe per cycle, and only when there is something to fetch; a server miss
  is remembered in `Named_Boxarts/.autobleem-missing.txt`. Pi: 36 covers fetched, 31 not on the server.
  **PS1 games get the same since 2026-09-19** (`ScanService::fetchMissingPs1BoxArt`, after
  `scanGamesDirectory`): a game with no PNG next to it and nothing in the thumbnails tree is asked for by
  its rdb record name (libretro-thumbnails' file name), else its title, and its Game.ini gets the cached
  path at once; `OnlineAssets::fetchMissingBoxArt` takes `(database, label)` requests now, with an
  on-fetched callback, and `ps1Requests()` is the selection (both tested). `config.ini`'s `online`
  defaults to **true**; the gate is the platform's `download_command` (Pi, PC - never the console). With
  that, `install.sh --thumbnails` defaults to `none` - the ~9300-file mirror (now four streams with a
  percentage) is `--thumbnails boxarts`, for covers offline. The owner first said no to this and then
  yes, for network-guaranteed platforms only.
  **Step 5** (2026-09-19): `apps/updateroms/` - `UpdateRoms.exe`, run from the stick in a PC, does the
  same scan with the PC's network and the target's paths (`usb_root` in the platform inis); see its
  CLAUDE.md. **The plan is complete**; what is left is listed at the end of the plan doc. On a console
  (2026-09-19): the RetroArch set from playlists `UpdateRoms.exe` wrote on the PC works as expected; the
  console's own scan stays offline by design (no `download_command` in `psc.ini`).
- Two gotchas the port turned up. `System::getAvailableSpace()` called a `floatToString()` that **has never
  existed anywhere in the code base** - the whole `#ifndef AB_DEBUG_HOST` branch had simply never been
  compiled, because no ARM build had ever run. Fixed with a file-local helper. And `config.ini`'s `Cfg=` key
  was an absolute console path that the installer had to rewrite per install - gone since 2026-09-18, the
  selection script is `Env::getPathToRCDir() + autobleem_cfg.sh` on every platform.

**Flashable image for Raspberry Pi Imager** (2026-09-19, plan at `docs/rpi-image-and-update-plan.md`). A
second way to get AutoBleem onto a Pi, alongside the tarball + `install.sh` flow: `tools/make_rpi_image.sh`
takes an official Raspberry Pi OS Lite image (downloaded automatically per architecture from Raspberry Pi
Foundation's stable "latest" redirect, sha256-verified against its published checksum, or a local `--base`),
loop-mounts it and injects an AutoBleem package plus `payload_linux/system/autobleem-firstboot.{service,sh}`
onto its root filesystem under `/opt/autobleem-image/` - **injection only**, deliberately: no chroot, no
qemu, no package pre-install, nothing from the base image is ever executed at build time (`systemctl
enable`'s effect is one hand-crafted symlink instead), so the same mechanism works for either architecture
from either architecture's build host. Two edits on the boot partition: `cmdline.txt` loses the word
**`resize`** - on Trixie that is what the initramfs (`local-premount/resize_early`, and `set_partuuid`)
keys on to grow the root over the whole card, which would leave `install.sh` no room for the data
partition - and **`autobleem.txt`** (from `payload_linux/system/`) is added: AutoBleem's first-boot options
as `key=value`, editable from any PC (`root_gib` default 8, `hdmi_mode`, `retroarch`, `thumbnails`, `bios`,
`downloads`; CRLF/BOM tolerated), and **ssh is enabled** (the owner's rule, 2026-09-20: once installed the launcher owns
tty1 and the keyboard, so there is no console to enable it from - the `multi-user.target.wants/ssh.service`
symlink in the root plus the official empty `ssh` file on the boot partition; the host keys are made by Pi OS's
own `regenerate_ssh_host_keys.service`). cloud-init's `user-data`/`network-config`/`meta-data` are left exactly as
shipped, so Raspberry Pi Imager's OS customisation (this base image is cloud-init 25.2 + rpi-cloud-init-mods:
`init_format: cloudinit-rpi`) lands on top as on a stock image. **`install.sh --grow-root GIB`** is the
counterpart to `--shrink-root`: `sfdisk --no-reread --force -N` + `partx -u` + `resize2fs` grow the still
image-sized root online (proven on a mounted loop-device filesystem on the Pi), capped so 2 GiB stay for the
data partition, run before apt (a fresh Lite root has ~400 MB free) and skipped when a data partition exists.
The output is `autobleem-<version>-rpi-<arch>.img.xz`: `make_rpi_package.sh` writes a `VERSION` file into the
tarball from the build's generated `version.h` (the tag, plus short hash and `-dirty` unless clean and exactly
at the tag), `make_rpi_image.sh` reads it from the tarball (`--version` overrides) and also puts it in the
Imager JSON description. (Found on the way: `generate_version.cmake`'s `git diff-index` stamped clean trees
dirty until an `update-index --refresh` was added before it - stale stat info, worse with MSYS2's git and
Git for Windows sharing one checkout.) **RetroArch is a question on the first boot** (owner's rule, see the
memory note: optional everywhere): unless `autobleem.txt` says `retroarch=`, the script asks, a minute's
silence means yes; `n` means `--retroarch none --no-downloads`, and `install.sh` makes that a lean PS1-only
install - `download_thumbnails` is its own step (box art is the launcher's, not RetroArch's) and the BIOS
pack shrinks to `scph5501.bin`/`scph5500.bin`.
**The first boot has a screen** (2026-09-20, the owner's ask): `payload_linux/system/autobleem-install-ui.py`
draws on `/dev/fb0` (RGB565 or XRGB, from sysfs) with nothing but python3's stdlib - it decodes the plymouth
`splash.png` itself (a small PNG reader), renders text from the console's Terminus PSF fonts
(`/usr/share/consolefonts`, PSF1/2 with their unicode tables) and puts tty8 in `KD_GRAPHICS`. The logo,
"Setting up AutoBleem", bar 1 = the phase (from `@@phase N/9 text` lines `install.sh`'s `phase()` prints
with `AB_UI_MARKERS=1`), bar 2 = the last percentage seen in the output (the download loops, wget) or a
pulse, and a box with the last 8 lines (a `\r` progress line rewrites the box's last line). The first-boot
script pipes `install.sh` through `tee` (the log) and the screen. **The questions are on the same screen**
(the owner's ask, the same day): `menu` / `input` / `message` modes draw a panel under the logo and read
keys raw from tty8 (termios; arrows, Enter, Esc = exit 3, a one-character item key as a hotkey, a countdown
to `--default`); the script's `ui_menu`/`ui_input`/`ui_message` wrappers call them and fall back to the old
text prompts without a framebuffer or when the program fails (any exit but 0/3 sets `UI_OK=0`). The console
stays in graphics mode from the first dialog to the reboot; `text_mode()` before a failure message. The
WiFi flow (country, scan list, hidden SSID, password, Ethernet - **no skip**, the owner's rule: the install
needs the network, the menu comes back until it is there) and the RetroArch question are all dialogs now. ~40 ms a frame on a PC; `--render out.ppm --fonts DIR` draws one frame on a PC for a look.
Every dialog is its own process, and decoding + scaling the splash PNG in pure Python cost ~1 s on the PC
and several seconds on the Pi - the owner pressed Enter again into a panel that had not changed - so
the prepared logo rows are cached in `splash.png.cache` next to the PNG (keyed on its size/mtime and the
framebuffer geometry; 22 ms warm) and a taken answer redraws the panel with a "Please wait..." footer
before the program exits (`accept()`); stale key presses are flushed when the next dialog opens.
The image build injects the script and the splash into `/opt/autobleem-image/`. Verified on the Pi 400:
the real installer through the progress screen, and the three dialog kinds with the Pi's keyboard.
`autobleem-firstboot.service` (`WantedBy=multi-user.target`, `ConditionPathExists=!/opt/autobleem-image/.done`,
`After=multi-user.target cloud-final.service userconfig.service`, `StandardInput/Output=tty` on
**`/dev/tty8`**, its own VT, switched to with `chvt 8` and back with `chvt 1`) **owns the screen and keyboard
for the first boot**, the way `autobleem.service` does later: the whole install is watched, not a silent
journal-only job. It deliberately does *not* `Conflicts=getty@tty1.service`: a `Wants=`-pulled unit whose
`Conflicts=` target is in the same boot transaction gets its job silently dropped (that first version never
ran at all - nothing in the journal, `ConditionResult=no` never evaluated). The script
waits up to 40 s for network; **with none it asks** - `rfkill unblock` + the WiFi country (default from
`cmdline.txt`'s `cfg80211.ieee80211_regdom=`, else the locale; Raspberry Pi OS keeps WiFi soft-blocked
until one is set, `raspi-config nonint do_wifi_country`), an `nmcli` scan listed by signal, pick / hidden
SSID / "I plugged in Ethernet" (skip removed 2026-09-20), password, `nmcli device wifi connect`, then a real fetch check -
then waits for NTP (`timedatectl ... NTPSynchronized`), then runs `install.sh --yes` + the `autobleem.txt`
options, output on tty8 and tee'd to `/var/log/autobleem-firstboot-install.log`. Failure or a skipped
network question switches back to tty1 (the login prompt) and retries on the next boot (a counter caps it at 20, then it
disables itself and leaves a note); success deletes the staged package, disables the unit and reboots once
more (boot splash and HDMI mode take effect on the boot after `install.sh` sets them). WiFi presets are not
an AutoBleem key on purpose - Imager's screen and the boot partition's own `network-config` already are
that. `tools/rpi_imager_repo.json` is the checked-in template for Imager's metadata; `make_rpi_image.sh`
writes a filled-in copy (real `extract_size`/`extract_sha256`/`image_download_size`/`image_download_sha256`/
`release_date`) to its output directory per architecture built, `url`/`icon`/`devices` left as placeholders
(no publishing pipeline yet). **`tools/rpi_imager_local_manifest.py`** turns that into what Imager's own
`doc/local_json/create_local_json.py` produces for local files - a `*.rpi-imager-manifest` with `file://`
URLs (double-click it, or App Options -> Content Repository -> Use custom file, or `--repo`) - which is what
makes Imager offer the customisation screen (user/WiFi/SSH) for a locally built image. `payload_linux/README.md`'s
"Flashing with Raspberry Pi Imager" section has the walkthrough.

**The download repository** (2026-09-19; its plan, `docs/repo-server-plan.md`, was removed on 2026-09-20 when
every step was done - the git log has it): **`https://autobleem.retromenele.pl/`**,
the build server's `~/autobleem-repo` served by a Caddy container (`docker/repo/`) on 443 (a
Let's Encrypt certificate Caddy obtained by TLS-ALPN-01 once the owner's `A` record existed - the host's
nginx keeps port 80, and no root was needed; Caddy renews it) and on 9090 as plain HTTP
(`http://<build-server>:9090/`, the same tree). Read-only to the world; publishing is `tools/repo_publish.sh
<release|image|retroarch|db|assets|index> ...` - rsync over `ssh psc-build` (or `--local` on the server),
`.sha256` sidecars, then `tools/repo_index.py` rerun on the server from `<repo>/.tools/` (uploaded with every
publish, but only when its `INDEX_VERSION` is at least the published one's - a `--local` run from the
server's stale rsync tree once regenerated the page without the manual link). The tree:
`releases/<tag>/` (the five packages, `SHA256SUMS`, `release.json`) with `releases/latest.json` (newest
stable) and `unstable.json` (the one pre-release), `rpi-imager/images/<v>/` and Raspberry Pi Imager's
"Add repository" URLs, **one per channel** since 2026-09-23 (the owner's ask): `rpi-imager/os_list.json`
(a stable release only - absent until the first one), `os_list-testing.json` (the pre-release set) and
`os_list-nightly.json` (the newest `nightly/<v>/` build's Pi images) - each a `rpi_imager_repo.json` with
the placeholders filled in; the page's Pi tab lists those that exist, each with a Copy button, `rpi/retroarch/<tag>/` + `latest.json`, **`psc/retroarch/<tag>/` + `latest.json`** (2026-09-20: the
console's RetroArch from `github.com/autobleem/retroarch-psc` - its `make publish` runs `repo_publish.sh
psc-retroarch <tag> retroarch-psc-<tag>.zip manifest.json`; the tag is `v<RetroArch version>-<build>`,
`psc_version_key` orders it, the newest kept as for the Pi builds), **`psc/cores/cores-psc-<date>.tar.gz`**
+ `.json` + `latest.json` (the console's cores, `repo_publish.sh psc-cores`, newest date kept - see
"RetroArch for the console" below), **`psc/libs/`** and **`psc/apps/`** (the same shape: `libs-psc-<date>.tar.gz`,
the libraries and the xpad module for `Autobleem/lib/`, from retroarch-psc's `tools/pack_retroboot_libs.py`;
`apps-psc-<date>.tar.gz`, the eight third-party Apps as `Apps/<name>/`, from `tools/pack_psc_apps.py` over a
stick's Apps folder - `repo_publish.sh psc-libs|psc-apps`), **`emu/pcsx-abnxt/<version>/`** and **`emu/pcsx-ab/<version>/`** + `latest.json` each (2026-09-20: the two emulators' packages, one per platform, from each repo's `tools/make_packages.sh` - pcsx-abnxt's version is `git describe` (`r26-24-g0f4727f1`), pcsx-ab's `<date>-<hash>` (`20260920-fc8c992`, no tags there); `repo_publish.sh pcsx|pcsx-ab <version> dist/packages/*`; the newest version kept; `EMULATORS` in `repo_index.py` renders one panel each under "Every platform"), **`psc/bios/biospack.txt`** + `latest.json` (the console's BIOS *list* only - `repo_publish.sh psc-bios payload/RetroArch/bios/biospack.txt`; the installer fetches the files from RetroBIOS, the owner's rule: no BIOS file on the site), `db/` (the three cover databases), **`samples/`** (the sample-games pack, below), `assets/`. **Retention** (the owner's rules): a pre-release *replaces* the previous one (packages and image
sets alike - `repo_index.py` deletes the older ones), only the newest RetroArch build is kept, stable
releases stay. **Since INDEX_VERSION 22 a package kind the new pre-release does not bring is carried
over** from the one it replaces (a publish of the console's packages alone no longer drops the Pi's, and
the other way round - two sessions publishing into the pre-release did exactly that on 2026-09-20). Since
INDEX_VERSION 35 a carried-over package goes when its kind is published for real afterwards (the newer file
of the two wins; before that the folder kept both and the page showed the older, alphabetically first one -
the Windows set of 2026-09-21).

**The web pages are generated, not stored**: `tools/repo_index.py` holds `PAGE_CSS` and renders
`index.html` (the landing page, **by platform since 2026-09-20** - PlayStation Classic, Raspberry Pi, PC,
then "Every platform"; each platform is an *Install* panel (what a user installs from: the console's USB
package, the Pi **images**, the Windows launcher + UpdateRoms - the latest stable release and, under it,
the one pre-release marked as a development build) and a dashed *Build inputs* panel (what the
installers, the image build and the CI fetch: the RetroArch builds, the cores tarballs, the Pi tarball
with `install.sh`; the cover databases are the inputs every platform shares) - the owner's reading of the
tree, an image or a package is the artefact, everything else feeds one)
and `rpi-install.html` (the Pi manual: `RPI_MODELS` - which image for which Pi, 32-bit recommended because
pcsx-ab's dynarec is ARM32-only, 64-bit for the bigger core set; requirements; Imager steps; what the first
boot does; where games go - files dropped straight into `Games/` are sorted into folders by the scan;
options and updates). Styled after the **ab2 theme** at the owner's request: its `abback2.jpg` (the
AutoBleem 2 logo is painted into it; `ab.png` is blank) as the hero, the navy/cyan palette, Selawik Light -
staged as `assets/` from `payload/Themes/ab2` by `tools/repo_assets.py` (`tools/repo_icon.png` is the
emblem cut out for the favicon and Imager's icon, checked in because MSYS2's python has no Pillow). To
change the pages: edit the render functions, bump `INDEX_VERSION`, `tools/repo_publish.sh index`.
**The page generator is merged on every publish, never copied** (2026-09-20, after two sessions had
overwritten each other's page twice): `tools/repo_index_merge.py` three-way merges this checkout's
`tools/repo_index.py` with the copy the repository runs (`<repo>/.tools/repo_index.py`) over the older of
the two develop versions they started from - mine from `git merge-base HEAD origin/develop`, the
repository's stored next to its copy as `.tools/repo_index.base.py` + `.rev` - with `git merge-file`;
`repo_publish.sh` uploads the result and the newer base. Distinct lines combine (a panel one session added
survives the other's publish); the same lines changed on both sides are a conflict and **nothing is
published** - the file with the markers is left in a temp dir, resolve it, commit to develop, publish
again. `INDEX_VERSION` is informational now (the larger of the two, +1 when the merge changed the
repository's). The server keeps `.tools/repo_index.prev.py` and falls back to it when the merged copy
fails to run. A tree without git (the server's rsync trees) merges over the repository's stored base,
right as long as that tree is at least as new as it. Two lines conflict easily - `render_index`'s
signature and `main()`'s summary `print` - so a new panel is best committed to develop before the next
session publishes. (The PC USB stick's `pc/` panels landed on develop with the merge of 2026-09-20.) Two
things the first publishes through it showed: the server's python is 3.6, so the tool uses no
`capture_output`; and a **stored base older than a region both sides had added** conflicts on every
publish that touches that region, whichever side is right - the base only moves on a successful publish
**from a git checkout** (the server's rsync tree has none), and now moves even when the two copies are
already identical. So: land the page change on develop, publish from the PC checkout.
`AB_REPO_URL` is the base URL everything generated starts with.

It holds the cover databases, the images and **RetroArch v1.22.2 for armhf and arm64** - `ci/build_retroarch.sh`
cross-builds it in the Docker image (a `retroarch` stage after `psc` with the foreign-arch dev packages;
same configure as the installer's source build, no FLAC - its soname differs between Bookworm and Trixie;
`retroarch.version`/`retroarch.depends` under `usr/local/share/autobleem`), and **`install.sh --retroarch
prebuilt` is the default** (`--repo`, `autobleem.txt` `repo=`; falls back to the source build when the
repository is unreachable). Verified on the Pi 400 the same day: installed in a couple of minutes, plays a
NES game. **Since 2026-09-20 the images are built on the server too**, rootless: `docker/run.sh
tools/make_rpi_image.sh --arch armhf --package dist/rpi/autobleem-rpi.tar.gz --work build_rpi_image --out
build_rpi_image/out` after `ci/build.sh rpi rpi64` - `--rootless` (the default without root) does the
five writes into the ext4 root with `debugfs -w` on `<img>?offset=N` and the two boot files with `mcopy`
on `<img>@@N`, offsets read from the MBR; `--mount` is the old loop-mount way for a machine with root.
7 minutes per image at the default xz level 4 (12 at level 6 for ~2% less size), then
`tools/repo_publish.sh --local image ...` on the same machine - no Pi in the loop. The Pi 400 only *tests*
an image, on the owner's request, never as part of CI (there is no Pi in the cloud). The Pi package leaves
the cover databases out (`make_rpi_package.sh --with-covers` puts them back; `install.sh` fetches them
from the site's `db/`), and the installer takes the cores as one tarball (`rpi/cores/`, `ci/build_cores.sh`
- a download of buildbot's cores and bundles, no compiling) before falling back to buildbot's per-core
download. The `c3a684c` pre-release (the two Pi tarballs) and its image set are on the site. **CI feeds the
site for every platform** (2026-09-21, widened from the Pi-only scope of the day before on the owner's
request): `ci.yml`'s `site` job publishes on every push to develop - the five launcher packages and the
console's stick installer bundle (`ci/build.sh win` ships `AutoBleemInstaller.exe`, `make_installer_bundle.sh
--exe` zips it with the psc tarball) as the pre-release `v2.0.0-pre0-<sha>`, both emulators' packages under
`emu/`, then the three images (the Pi pair rootless, the PC stick's `--mount` in a privileged container) -
and on a `v*` tag the same under the tag's name, on the self-hosted runner (`~/autobleem-repo`
mounted into the job container as `REPO_DIR`); `docs/ci.md` has the job's shape. `site-refresh.yml`
(monthly, or `workflow_dispatch`) rebuilds RetroArch and re-downloads the cores tarballs. All of it is written
and unrun: nothing in Actions runs until `AB_CI_ENABLED` is set and the runner is registered (the owner's
PAT, `docs/ci-plan.md`) - until then the by-hand sequence in `docs/ci.md` is how a pre-release is refreshed
(done 2026-09-21 for all five platforms: `v2.0.0-pre0-a09927c`).
The console zip is not on the site and its cover databases still come from the Docker image's baked copy
(the console has no network, so the zip must carry them) - deliberately left as is.

**Sample games** (2026-09-20, the owner's ask: an install should not start with an empty shelf): `install.sh`'s
`install_sample_games()` (phase 8, after the payload; `--no-samples`, `autobleem.txt` `samples=no`) fetches
`samples/latest.json` from the site and unpacks the newest `samples-<date>.tar.gz` onto the data partition -
`Games/` and `SAMPLES.md` always, the `RetroArch/` part (roms + thumbnails) only with RetroArch installed -
once (`System/samples.txt` remembers it, so a re-run never puts back a sample the user deleted). The pack is
**`tools/build_samples.py`** over **`tools/samples/samples.json`**: each game's files from its upstream release
URL, sha256-checked (a zip member taken out), laid out as they land on the partition; only the stdlib, so it
runs in the Docker image; `tools/repo_publish.sh samples <tar.gz> <json>` publishes it (`repo_index.py`
keeps the newest date, `latest.json` carries the games list, the landing page's "Sample games" panel shows
them with licence links). **Licence first**: every entry names its licence and URL, and only games we may
*redistribute* went in - a free download is not enough. Today: Tetrade (PS1, MIT), Nova the Squirrel (NES,
GPL-3.0), Asteroids + Castle Platformer (SNES, MIT, undisbeliever), Alex vs Bus - The Race (Mega Drive,
GPL-3.0 + CC BY-SA assets, the `pre3` release) - and that is the set: the owner closed the list on
2026-09-20, no further sample games are planned. The PS1 game gets a **locked `Game.ini`** (`Automation=0`, the launcher's own lock: the scanner then
skips its create/update branch, so the title/publisher/year/players and the PNG next to the game stay - no
serial, no rdb, no covers db involved; verified on the PC: regional.db row `Tetrade / Logan Campbell / 2025 /
2`, ini untouched). The ROMs are named as the launcher's ROM scan labels a ROM no rdb knows (the file's stem)
with a box art of the same name under `RetroArch/thumbnails/<db>/Named_Boxarts/`. The covers are drawn by
`tools/samples/make_covers.py` (Pillow, so run on the PC and checked in as `tools/samples/covers/`): the
game's own title screenshot (`tools/samples/shots/`, from its repository) cropped to the box shape the
carousel draws for the system (square PS1, tall NES/MD, wide SNES), a navy band with the title in Selawik.
**Tetrade crashed pcsx-ab in the BIOS shell** (2026-09-20, the owner on the Pi: its custom boot logo - the
fork had upstream's "skip BIOS logos" jump commented out, so the shell always ran). Hence **the boot logo is
a per-game option**: pcsx-ab's `Config.SlowBoot` (pcsx-ab2 `377da70`; 1 = run the shell, the default on
every existing card; 0 = return into the kernel past it, as upstream always does), pcsx.cfg `SlowBoot`,
the game editor's "Boot logo" row (`GameSettingsService::setBootLogo`, `PcsxSettings::bootLogo`; no line =
shown), `LaunchService` passing it to RetroArch as `pcsx_rearmed_show_bios_bootlogo`, and the sample
pack shipping a `pcsx.cfg` next to the PS1 game (`skip_boot_logo` in the manifest -> `SlowBoot = 0`; the
Pi's `launch.sh` copies the game folder's cfg over the `!SaveStates` one at every launch, so it is what
pcsx-ab reads). With that, **`ConfigFileEditor::replaceProperty` appends a key the file does not have** -
it used to replace lines only, so a pcsx.cfg copied from an older default could never take a newer
option (the test that pinned that is flipped). The pack on the site was rebuilt in place (same date).
**Skipping the shell was not enough** (the same day, traced on the Pi 400 with a per-second pc/EPC print and
an I/O-write trace): the game booted and sat in PSn00bSDK's `DrawSync` forever, because **the 2013-era
core decoded the I/O registers by the literal `0x1f80....` addresses the PsyQ libraries use** - PSn00bSDK
reaches them through KSEG1 (`0xbf80....`), and every such write fell through `psxHwWrite16/32`'s switch to
plain memory: no GPU DMA ever started, no I_MASK write took effect. pcsx-ab2 `1feb7e2` masks the address
(`switch (add & 0x1fffffff)`, as upstream does); with it Tetrade boots with the interpreter and the
dynarec, through the shell and without it. Two more pcsx-ab changes from the same hunt: the real-BIOS
fast boot now **loads the executable itself** (`aeac3f9`, upstream's "manual booting" - SYSTEM.CNF, the
exe, pc/gp/sp - instead of the 2013 `pc = ra` jump, which relied on the kernel booting the CD), and
LoadCdrom logs it. The pack keeps `SlowBoot = 0` for Tetrade: its image has no licence data, so the shell
shows a garbled logo before the game. **Any PSn00bSDK homebrew was broken on pcsx-ab until this fix.**
**That fix was not the whole story**: with it the game boots, sets 320x240, runs its DMAs and IRQ acks
through the init, and then goes quiet after the ordering-table clear - never draws, the screen stays
black (RetroArch's current pcsx_rearmed plays it). The owner stopped the emulator work there
(2026-09-20): **Tetrade is out of the sample pack, and the pack has no PS1 game** - the four ROMs stay;
`build_samples.py` keeps its PSX layout code (locked Game.ini, pcsx.cfg with `SlowBoot = 0`) for the day a
PS1 homebrew with a redistributable licence, a disc image and a working boot on pcsx-ab turns up. The
KSEG1 and fast-boot changes stay in pcsx-ab (they are right regardless).

**Where the packages come from now**: the build server's Docker image (`docs/ci.md` - `ssh psc-build`,
`cd ~/autobleem`, `docker/run.sh ci/build.sh rpi rpi64`, `dist/<target>/`), which builds pcsx-ab from the same
run and bakes in the **real cover databases** (the PC checkout's `db/` holds 16 KB stubs, so a package made
on the PC ships no covers) - both Pi packages in ~2 min incremental. `~/autobleem` there is an rsync tree
(from the MSYS2 shell, *including* `payload*/`; pass `AB_GIT_*` for the version); its clock ran ~5 min behind
the PC, which made rsync'd files "future" and ninja loop ("manifest 'build.ninja' still dirty") - `touch` the
`-newermt now` files. The images themselves are built on the Pi 400 (loop mounts need root; the server has no
sudo), packages streamed server -> PC -> Pi, `--work/--out` on the data partition (the 8 GB root is too
small - the script checks free space first since it ran out once).

**What has run for real** (2026-09-19, Pi 400 as the build host over ssh, then as the target): the image
build itself for both architectures (download, verify, mount, inject, recompress; the *output* re-mounted
and its contents checked; a second run fills the other architecture's JSON entry alongside); two build-script
bugs found only against real hardware (`--dry-run` demanding `/sbin`-only tools; the wget redirect parsing
matching neither of wget 1.25.0's two `Location` line formats, so the download was named after the alias
URL and the `.sha256` check failed). **The first real boot of the first image** (arm64, "Use custom", no
presets) is what shaped the first-boot script above: the wizard asked for a keyboard layout, WiFi stayed
rfkill-blocked with no country set, `autobleem-firstboot` ran `install.sh --yes` silently in the background
with no network and died at `apt-get install` (`Temporary failure resolving 'deb.debian.org'`), leaving a
login prompt and no clue on screen - hence the script's own VT, the WiFi prompt, the NTP wait; and the root had
been grown over the whole card - hence the `resize` removal and `--grow-root`. `--grow-root`'s partition
mechanics were proven on a mounted loop-device filesystem on the Pi. **The second flash** (arm64, via the
local manifest with Imager's presets) went end to end: cloud-init applied the presets, the firstboot script
took the screen on tty8, asked the RetroArch question, grew the root 2400 -> 8192 MiB, made the 110 GB exFAT
data partition, built RetroArch, fetched cores + BIOS, rebooted into the launcher. Both `933bd2f` images
(armhf and arm64, from the server's Docker packages) were then built on the Pi, re-mounted and checked, and
sit in `build_rpi_image/` on the PC with a two-entry `os_list_local.rpi-imager-manifest`. **The first armhf flash** (2026-09-19, no presets) answered the WiFi question - the prompt works - and then
died unpacking the package: the 306 MB tarball is staged on the still image-sized root and unpacks to 327 MB
(290 MB of cover databases), *before* `--grow-root` had run; arm64 had just enough free to get away with it.
`autobleem-firstboot.sh` now extracts `install.sh` alone, runs it with `--grow-root N --grow-only` (preflight +
grow, then stop - a no-op on a retry), checks the free space against `gzip -l`'s unpacked size, and only
then unpacks the rest, behind an `.extracted` marker (a half-unpacked tree from a failed attempt is removed,
not run). **Verified the same evening on that card**: the root grown by hand to 8 GiB over ssh, the fixed
script and a re-packed tarball dropped into `/opt/autobleem-image/`, and the retry went end to end -
`--grow-only` a no-op, the package unpacked, RetroArch built (~25 min), cores, BIOS, splash, reboot into
the launcher on the 109 GB data partition. So the armhf image's first boot is proven apart from the
`--grow-only` growing a root for real (it has only ever found one already grown) - that is what the next
image build from `develop` checks. A 32-bit Trixie root also makes a 2 GB `/var/swap` (dphys-swapfile)
on its first boot with room; `root_gib=8` covers it.

### Raspberry Pi 64-bit (2026-09-18)

A second Pi architecture, alongside the 32-bit port above, not a separate app target: `AB_PLATFORM_RPI` and
`AB_TARGET_RPI` do not branch on word size, so every application-level behaviour (no internal games,
root-relative layout, install-tree paths) is identical on both. Only the toolchain, three build-system
files, and the checked-in pcsx-ab binary differ. **Builds cleanly, unrun on hardware** - `make_rpi64.sh`,
`pcsx-rearmed-develop`'s `make_rpi64.sh` and `make_rpi_package.sh --arch arm64` all verified end to end
2026-09-18/19 (real aarch64 ELF binaries, a working `autobleem-rpi-arm64.tar.gz`); the owner has no 64-bit
Pi OS card imaged yet, so nothing has booted on real hardware. Targets 64-bit **Trixie**, same as the 32-bit
port targets 32-bit Trixie (and Bookworm).

- **Toolchain**: `toolchains/rpi64/RPi64toolchain.cmake`, over "SysGCC for Raspberry Pi (64-bit)" -
  gnutoolchains.com/raspberry64 (Sysprogs OÜ, the same vendor family as the 32-bit `C:\sysGCC\raspberry`;
  sysprogs.com's own site says it has no 64-bit Pi toolchain, but gnutoolchains.com's free prebuilt one
  does - GCC 14.2.0, built against `2025-12-04-raspios-trixie`, same GCC version as the 32-bit toolchain).
  Installed 2026-09-18 to **`E:\sysGCC\raspberry64`** (the owner's call - not `C:`, unlike the 32-bit one),
  via `raspberry64-gcc14.2.0.exe /S /D=E:\sysGCC\raspberry64` (its NSIS installer takes silent-install
  flags). Same compiler/sysroot layout as the 32-bit toolchain assumed:
  `aarch64-linux-gnu-{gcc,g++,strip}.exe` in `bin/`, sysroot at `<root>/aarch64-linux-gnu/sysroot` with
  SDL2/SDL2_image/SDL2_mixer/SDL2_ttf/libpng16 runtime `.so`s under `usr/lib/aarch64-linux-gnu`.
  `./make_rpi64.sh` configures and builds into `build_rpi64/` (`--debug` -> `build_rpi64_dbg/`; incremental, `--clean` wipes), mirroring
  `make_rpi.sh` exactly. Target is plain `armv8-a` - every 64-bit-capable Pi (3/4/5/400/Zero 2 W) is that
  core, so there is no armv7-style board split to make.
- **SDL2 discovery**: `toolchains/rpi64/cmake/FindSDL2.cmake` is the same borrowed-headers-plus-imported-.so
  trick as the 32-bit module, and *reuses* `toolchains/rpi/sdl2-devkit/include` by relative path rather than
  keeping a second copy - the public SDL2 headers are pure C and arch-independent. Only the library
  directory differs: the sysroot's `usr/lib/aarch64-linux-gnu` instead of `usr/lib/arm-linux-gnueabihf`.
- Root `CMakeLists.txt`'s `ABLEEM_EMBEDDED_TARGET` switch matched `CMAKE_SYSTEM_PROCESSOR MATCHES "^arm"`,
  which `aarch64` does not match - fixed to also check `STREQUAL "aarch64"` so cursor-grab/keyboard-as-pad
  are disabled on a 64-bit Pi the same as everywhere else embedded. No other CMakeLists.txt change was
  needed: the PSC's `^arm`-and-`NOT AB_TARGET_RPI` branch and the Pi's own `elseif (AB_TARGET_RPI)` branch
  both already keyed off `AB_TARGET_RPI` rather than the processor string.
- **pcsx-ab has no aarch64 dynarec** in this fork (verified: no repo-authored aarch64 anywhere in
  `pcsx-rearmed-develop`, and Ari64's dynarec/NEON GPU-GTE assembly is 32-bit-ARM-only) - PS1 games on a
  64-bit Pi run through its C interpreter, like the PC build, not the NEON dynarec the 32-bit Pi gets. Still
  correct, just slower per clock. `pcsx-rearmed-develop`'s `CMakeLists.txt:35-39` sets `_pcsxab_is_arm` from
  `CMAKE_SYSTEM_PROCESSOR MATCHES "^(arm|ARM)"`, which is deliberately **not** extended to aarch64 for this
  reason - folding aarch64 into that branch would try to build 32-bit ARM assembly with the 64-bit compiler.
  Its own `toolchains/rpi64/RPi64toolchain.cmake` and `make_rpi64.sh` (mirroring the 32-bit ones there) build
  it as a plain aarch64 Linux target instead, `PCSXAB_GLES`/dynarec left off. Built 2026-09-19: a real
  aarch64 `pcsx-ab` + the three plugins, committed into `emu-arm64/` below.
- **Package**: one `payload_linux/` tree still serves both architectures - `install.sh` reads
  `dpkg --print-architecture` (`armhf` or `arm64`) into `$ARCH`, and separately into `$RA_ARCH` (`armhf` or
  **`aarch64`**, not `arm64` - buildbot.libretro.com's own directory name for 64-bit ARM does not match
  Debian's; caught and fixed 2026-09-19 before it shipped, `nightly/linux/arm64/` 404s) for the
  `buildbot.libretro.com/nightly/linux/$RA_ARCH/latest` cores URL. Only the emulator binaries are
  architecture-specific, so pcsx-ab (with its `plugins/`) is checked in twice: `payload_linux/Autobleem/bin/emu/` (armhf) and
  `payload_linux/Autobleem/bin/emu-arm64/` (arm64, built and committed 2026-09-19).
  `tools/make_rpi_package.sh --arch armhf|arm64` (armhf is the default, unchanged output name)
  picks the matching `build_rpi`/`build_rpi64` source directory and, for `arm64`, moves `emu-arm64/`'s
  contents over `emu/` while staging so the on-device path stays `Autobleem/bin/emu/pcsx-ab` either way; the
  tarball is named `autobleem-rpi.tar.gz` (armhf) or `autobleem-rpi-arm64.tar.gz` (arm64) so the two never
  collide on the Pi's home directory during `--push`. Both verified 2026-09-19 - `autobleem-gui` packs with
  UPX as `linux/arm64` (1.2 MB), the 32-bit package rebuilt clean alongside it (no regression).
- **BIOS pack** (2026-09-19): `tools/biospack.py --arch arm64` builds `payload_linux/system/biospack-arm64.txt`
  (694 files, 230 MB) from the real `buildbot.libretro.com/nightly/linux/aarch64` core listing, since
  RetroBIOS's own per-target file has no 64-bit Linux entry to read instead - see "BIOS pack" under the
  32-bit section above for the full mechanism, now shared by both architectures. Spot-verified: downloaded
  and hashed 4 random entries against the manifest, all matched.
- **A pre-existing repo bug this work turned up** (fixed on `develop`, 2026-09-18, unrelated to word size):
  `.gitignore`'s bare `build/` line matched at any depth, silently excluding
  `lib_ableem/third_party/libchdr/deps/zstd-1.5.6/build/` - zstd's own vendored `CMakeLists.txt`, not a
  build output directory - from every commit. A truly fresh clone's CMake configure failed outright on
  *every* platform (`add_subdirectory given source ... which is not an existing directory`); it only ever
  worked in the long-lived `autobleem-develop` checkout because those files were on disk from before the
  line was added, untracked. Anchored to `/build/` and the nine missing files recovered from that checkout.
- **First boot on hardware 2026-09-20**: the `c3a684c` arm64 image (built rootless on the server) on
  the Pi 400 - the first boot went end to end (`--grow-only` grew the image-sized root, the cores tarball,
  the cover databases, the prebuilt arm64 RetroArch, the boot splash from the single 64-bit kernel) and
  the launcher came up **black, with no sound**: SDL's "opengl" renderer could not dlopen `libGL.so.1`
  (`libgl1` was never a dependency of anything - on the 32-bit card it had come in with RetroArch's
  source-build packages, and the prebuilt RetroArch ends that) and silently gave a context with no
  shaders and no render targets. `install.sh` installs `libgl1 libgl1-mesa-dri libegl1 libgles2 libgbm1`
  since; `ableem::Renderer` logs an error when a renderer has no render-target support. On the 64-bit
  kernel `/dev/dri/card0` is v3d and `card1` the vc4 display - SDL picks card1 by itself. The same boot
  came up in the **default theme**: the kernel log said "exFAT-fs: Volume was not properly unmounted" -
  the first boot's `reboot` had left the data partition dirty and `config.ini` (copied last, small) came
  back as an empty file, which the launcher read as "no settings". Three fixes: the first-boot script
  unmounts the exFAT partitions before rebooting (a `sync` alone was not enough), `IniFile::save` writes
  atomically (`.tmp` + `DirEntry::replaceFile`) and `IniFile::load` warns about an empty file, and `Config`
  defaults `theme` to `ab2` in code (tested). Audio was fine all along (the owner's mistake).

