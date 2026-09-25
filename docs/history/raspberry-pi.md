# Raspberry Pi port (`rpi`, 32-bit and 64-bit)

What the Raspberry Pi appliance is, how it is built, installed and imaged. Paths without a repository name
are the launcher's (`autobleem2/autobleem`); the PC stick shares most of this (`pc-usb-stick.md`).

## The appliance

- AutoBleem as an appliance on **Raspberry Pi OS Lite** (Bookworm or Trixie), armhf or arm64. The launcher
  owns tty1 through systemd (`autobleem.service`, `getty@tty1` disabled); `autobleem-session.sh` is its loop
  and replaces the console's `rc/selection.sh`.
- `AB_TARGET=rpi` -> `AB_PLATFORM_RPI`, one of the `AB_APPLIANCE` targets: a real target (forks emulators,
  halts for real), no internal games (`AB_HAS_INTERNAL_GAMES` is psc/dev only, the Options row is gone),
  root-relative layout (`EnvironmentSetup`'s "everything under the root" branch, shared with the 1-arg debug
  mode). `internal.db` is still opened (empty) because `GameCatalogService`/`GameSettingsService` expect it.
- 32-bit and 64-bit are the same app target; only the toolchain, `FindSDL2.cmake` and the pcsx-ab binary
  differ. The 64-bit Pi **booted on hardware on 2026-09-20** (Pi 400, the arm64 image, end to end).
- **The data partition** is an exFAT partition on the SD card next to the root, laid out like the
  console's stick (`Games/`, `System/`, `Themes/`, `Apps/`, `Autobleem/`, `RetroArch/`). Cores are
  `dlopen`ed from it, so its fstab entry has no `noexec`. A USB stick with an exFAT partition labelled
  `AUTOBLEEM` also works (`--disk /dev/sda`) but is not the intended setup.
- PS1 games run in **pcsx-ab / pcsx-abnxt** as on the console: the Pi `rc/launch.sh` builds `/tmp/runpcsx`
  exactly as the console's does. The BIOS is the user's (`System/Bios/romw.bin` + `romJP.bin`, HLE without).
  RetroArch's `pcsx_rearmed` core is the fallback only. **pcsx-ab has no aarch64 dynarec** (Ari64's dynarec
  and the NEON GPU are ARM32-only), so a 64-bit Pi runs PS1 through the interpreter - hence 32-bit is the
  recommended image.
- **RetroArch** lives in `RetroArch/` on the data partition in its standard tree (`cores`, `info`, `system`
  = the cores' BIOS, `roms`, `saves`, `states`, `playlists`, ...) with a generated `retroarch.cfg` pointing
  every directory in there. Paths come from `resources/platform/rpi.ini` (`PlatformConfig`), never from
  `#ifdef`s. `rpi.cores.cfg` prefers Genesis Plus GX (picodrive's Cyclone core segfaults on the Pi 400,
  unexplained), plain Snes9x and blueMSX.
- The launcher's ROM scan, metadata from the rdb and online box art run on the Pi (`download_command` is
  curl there; config.ini `online` defaults to true, the platform's `download_command` is the gate).

## Build

- `make_rpi.sh` / `make_rpi64.sh` (incremental, `--clean`, `--debug`), toolchains
  `toolchains/rpi/RPitoolchain.cmake` / `toolchains/rpi64/RPi64toolchain.cmake` over `toolchains/rpi/common.cmake`:
  SysGCC on the Windows PC when present, Debian's multiarch cross compiler otherwise (the Docker image,
  `ci/build.sh rpi rpi64`, which also builds pcsx-ab and bakes in the real cover databases).
- armhf is `armv7-a + neon-vfpv4` (Pi 2/3/4/Zero 2, **not** armv6); arm64 is plain `armv8-a`. The root
  CMakeLists' console branch is PSC-specific, so the appliances take their own branch - without it a Pi
  build got armv8 code that SIGILLs on a Pi 2. `ABLEEM_EMBEDDED_TARGET` also matches `aarch64`.
- The SysGCC sysroots have SDL2 runtime `.so`s but no `-dev`: `toolchains/rpi*/cmake/FindSDL2.cmake` defines
  the four imported targets with headers from `toolchains/rpi/sdl2-devkit/include` and `IMPORTED_LOCATION`
  at the versioned `.so`. Keep SysGCC's `bin` off PATH (its `rm`/`mkdir`/`make` shadow MSYS2's).
- pcsx-ab for arm64 is built as a plain aarch64 target (no dynarec, no GLES); its `_pcsxab_is_arm` check
  must **not** be extended to aarch64.
- A Pi core dump is read with `make_rpi.sh --debug` + the PC's cross gdb (gdb on the Pi hangs in
  `snd_pcm_open` on the mapped ALSA device).

## The package and `install.sh`

- `payload_linux/` (a sibling of `payload/`) is the package as the Pi unpacks it: `install.sh` + `README.md`,
  `system/` (units, session loop, shrink-root initramfs pieces, plymouth theme, first-boot files) and the
  data-partition tree. `tools/make_rpi_package.sh --arch armhf|arm64` fills in the launcher, resources and
  themes and writes a `VERSION` file; for arm64 it moves `emu-arm64/` over `emu/` so the device path is
  always `Autobleem/bin/emu/pcsx-ab`. Cover databases are left out (`--with-covers` puts them back;
  `install.sh` fetches them from the site's `db/`). Run as `sudo bash install.sh` (a package built on
  Windows loses the executable bit).
- `$ARCH` is `dpkg --print-architecture`; `$RA_ARCH` maps `arm64` to **`aarch64`**, buildbot's directory
  name (`nightly/linux/arm64/` 404s). Trixie renamed packages for 64-bit `time_t`; `pkg_first_available`
  tries each name.
- Options: `--retroarch prebuilt` (default: the site's build of the latest tagged RetroArch, KMS/EGL/GLES,
  udev, ALSA; falls back to a source build when the site is unreachable) | `source` | `apt` | `none`;
  `--repo`; `--no-downloads`; `--thumbnails none|boxarts` (default none - covers are fetched online by the
  launcher); `--no-bios`; `--no-samples`; `--hdmi-mode`; `--no-boot-splash` / `--no-quiet-boot`;
  `--shrink-root GIB`; `--grow-root GIB` (`--grow-only` stops after it); `--update` (the online update);
  `--disk`. Cores come as one tarball from the site (`rpi/cores/`), else buildbot per core.
- **Graphics libraries are explicit dependencies**: `libgl1 libgl1-mesa-dri libegl1 libgles2 libgbm1`.
  Without `libGL.so.1` SDL's opengl renderer silently gives a context with no render targets - a black
  launcher (`ableem::Renderer` now logs that). On the 64-bit kernel `card0` is v3d and `card1` the vc4
  display; SDL picks card1 itself.
- ALSA would default to a USB pad's audio: `autobleem-session` writes `/etc/asound.conf` for the connected HDMI.
- **Boot screen**: the KMS mode is set on the kernel command line (`video=HDMI-A-1:...`; `config.txt`'s
  `hdmi_mode` is ignored by KMS), so plymouth and the launcher share one mode. The logo is a plymouth
  `script` theme packed into **every** kernel's initramfs (`update-initramfs -u -k all` - the 32-bit image
  carries one kernel per board); the shrink hook stays on the running kernel only, never bare `-u`.
  `autobleem.service` `Conflicts=plymouth-quit.service` and the session runs `plymouth quit --retain-splash`
  first (plymouth holds the DRM master). Kernel to launcher is ~8 s.
- **Root shrink** (`--shrink-root`) is done offline from the initramfs (`local-premount` script,
  `disarm_shrink()` removes it after): `resize2fs` cannot shrink a mounted root, so Pi OS's `init=` route
  (which only ever grows) cannot work. **Root grow** (`--grow-root`) is online: `sfdisk --no-reread --force
  -N` + `partx -u` + `resize2fs`, capped to leave 2 GiB for data, run before apt, skipped when a data
  partition exists.
- **BIOS pack**: `system/biospack.txt` (armhf) / `biospack-arm64.txt`, one line per file (`<sha256> <size>
  <url> <path>`), fetched into `RetroArch/system/` with a `.part` + hash check (a re-run only repairs), plus
  SCPH-5501/5500 copied to `System/Bios/` unless the user's own are there. Written by `tools/biospack.py
  --arch ...` from RetroBIOS (pinned commit) filtered to the cores the architecture has (armhf: RetroBIOS's
  own target list; arm64: buildbot's `linux/aarch64` listing), an allow-list of system folders and path
  excludes. **No BIOS file is ever in a repository or on the site** - hashes and URLs only.
- **Sample games**: `install_sample_games()` unpacks the site's `samples/latest.json` pack once
  (`System/samples.txt` remembers, so a deleted sample never comes back); `Games/` always, the RetroArch
  part only with RetroArch. The pack is `tools/build_samples.py` over `tools/samples/samples.json`. Rules:
  every entry names its licence, only games we may **redistribute**, the list is closed (the owner,
  2026-09-20): Nova the Squirrel (NES), Asteroids + Castle Platformer (SNES), Alex vs Bus (MD). There is no
  PS1 sample; `build_samples.py` keeps the PS1 layout code (a locked `Game.ini` with `Automation=0`, a
  `pcsx.cfg` with `SlowBoot = 0`). ROMs are named as the ROM scan labels an unknown ROM, with a matching
  box art (`tools/samples/make_covers.py`).
- **Tetrade / KSEG1**: the 2013-era pcsx-ab core decoded I/O registers by their `0x1f80....` addresses only;
  PSn00bSDK homebrew uses KSEG1 (`0xbf80....`), so its writes fell through to memory. pcsx-ab now masks the
  address (`add & 0x1fffffff`) and its real-BIOS fast boot loads the executable itself; the boot logo is a
  per-game option (`SlowBoot`, the editor's "Boot logo" row).
- `ConfigFileEditor::replaceProperty` appends a key the file lacks, so an old pcsx.cfg can take a new option.

## The flashable image and the first boot

- `tools/make_rpi_image.sh` takes the official Pi OS Lite image (downloaded and sha256-checked, or `--base`)
  and **only injects**: the package and `autobleem-firstboot.{service,sh}` under `/opt/autobleem-image/`,
  `systemctl enable` as a hand-made symlink, nothing from the base image executed - so either architecture
  builds on either host. `--rootless` (default without root) writes with `debugfs -w` / `mcopy` at offsets
  read from the MBR; `--mount` loop-mounts. Output `autobleem-<v>-rpi-<arch>.img.xz`, ~7 min at xz level 4.
- Boot-partition edits: `cmdline.txt` loses **`resize`** (otherwise the initramfs grows the root over the
  whole card and leaves no room for data), `autobleem.txt` is added (`key=value` first-boot options:
  `root_gib` default 8, `hdmi_mode`, `retroarch`, `thumbnails`, `bios`, `downloads`, `samples`, `repo`;
  CRLF/BOM tolerated), and **ssh is enabled** (the owner's rule - the launcher owns tty1 afterwards).
  cloud-init files are left as shipped, so Imager's OS customisation applies as on a stock image.
- Imager metadata: `tools/rpi_imager_repo.json` is the template; `tools/rpi_imager_local_manifest.py` makes
  a `*.rpi-imager-manifest` with `file://` URLs, which is what makes Imager offer customisation for a local
  image. The site publishes one list per channel (`rpi-imager/os_list{,-testing,-nightly}.json`).
- **`autobleem-firstboot.service`** owns **tty8** for the whole install (`chvt 8`, back with `chvt 1`).
  It must **not** `Conflicts=getty@tty1.service`: a `Wants=`-pulled unit conflicting with a unit in the same
  boot transaction is silently dropped. The script: waits for network, else asks (rfkill unblock, WiFi
  country - Pi OS keeps WiFi blocked until one is set - an `nmcli` scan, hidden SSID, Ethernet; **no skip**,
  the install needs the network), waits for NTP (Pi only - no RTC), asks the RetroArch question (a minute's
  silence = yes; no = a lean PS1-only install), extracts `install.sh` alone and runs `--grow-root N
  --grow-only` **before** unpacking the rest (the package does not fit on the image-sized root), checks
  free space against `gzip -l`, unpacks behind an `.extracted` marker, then `install.sh --yes`. Failure
  goes back to tty1 and retries next boot (capped at 20). Success removes the stage, disables the unit,
  **unmounts the exFAT partitions** and reboots (a `sync` alone left the partition dirty and `config.ini`
  empty; `IniFile::save` is atomic now and `Config` defaults `theme` to `ab2`).
- **The install screen**, `system/autobleem-install-ui.py`: stdlib python on `/dev/fb0` (RGB565/XRGB), its
  own PNG decoder for the splash (cached as `splash.png.cache`, keyed on size/mtime and fb geometry - the
  pure-Python decode took seconds on a Pi), Terminus PSF fonts, tty8 in `KD_GRAPHICS`. Two bars (the phase
  from `install.sh`'s `@@phase N/9` markers with `AB_UI_MARKERS=1`, the last percentage) and the last 8
  lines. `menu`/`input`/`message` modes are the dialogs (raw keys from tty8, a countdown to `--default`,
  "Please wait..." redraw on accept, stale keys flushed); the script falls back to text prompts when the
  program fails. `--render out.ppm` draws a frame on a PC.
- A 32-bit Trixie root makes a 2 GB `/var/swap` on first boot; `root_gib=8` covers it.

## The download repository

The site, its layout, retention, the page generator and the CI that feeds it are autobleem-repo's: see its
`CLAUDE.md` and `history/ci-and-site.md`.

## Still open

- pcsx-ab still cannot run Tetrade (PSn00bSDK): after the KSEG1 fix it boots, then goes quiet after the
  ordering-table clear and never draws; the sample pack has no PS1 game until a redistributable PS1 homebrew
  boots on the shipped emulator.
- The launcher's own ROM scan (step 1 of the RetroArch scanner plan) has not been run on a console (the
  console's RetroArch set from `UpdateRoms.exe` playlists has).
- Picodrive's Cyclone core segfaults on the Pi 400 - unexplained (worked around by `rpi.cores.cfg`).
