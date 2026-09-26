# Console hardware-run debugging tales

Moved verbatim out of the launcher's CLAUDE.md on 2026-09-26 (task D19).

## The 2026-09-19 CI image console pass

  (37/37 tests, format, tidy), packages inspected. **Run on a console
  2026-09-19**: the psc package's launcher, `libs.tar.gz` and pcsx-ab went onto the owner's stick (the
  previous set kept in `E:\tmp\stick-prev`), and the launcher started with all covers - the first hardware
  run of any console build of this repo. Two bugs the console then showed, both fixed the same day: pcsx-ab
  segfaulted at its first frame (its Wayland branch never set `SDL_SysWMinfo::version`, so SDL 2.0.6+'s
  "Version must be 2.0.6 or newer" check failed on uninitialised stack - a coin the gcc-8 build won and the
  gcc-6 build lost; pcsx-ab2 `70c5dcb`), and no sound anywhere (the Dockerfile's linker-script rewrite had
  truncated the sysroot's `libasound.so`, so SDL2 was built without ALSA; `ab-validate psc` now checks the
  audio backends). `rc/launch.sh` writes `System/Logs/launch.log` + `pcsx.log` since then - that is how
  both were read. A stock-firmware console also needs RetroBoot 1.2's `retroarch` (the vendored bundle);
  a RetroBoot 1.1 tree with a later KMFD build wants GLIBC_2.28 and never starts (see `retroarch/logs/`).
  What the image's compilers turned up: the console's gcc-6 cannot combine an inherited constructor with a
  member initialised from another member (`GuiLauncher` now spells its constructor out - keep it that way
  for every screen), and the test fixture's scratch dirs now carry the pid (`ctest -j` runs suites in
  parallel; same label + counter in two processes deleted each other's trees). Editing the root
  CMakeLists' console branch: a GCC < 8 gets `-march=armv8-a -mfpu=neon-vfpv4` (it used to get armv7ve,
  no NEON - a branch that had never been compiled).


## The older, now-redundant "keyboard = gamepad" paragraph (task D19 pass 2)

Moved verbatim out of the launcher's `CLAUDE.md` "### Smoke test layout (Windows)" section during task
D19's second pass (2026-09-26): a pre-2026-09-26 paragraph duplicating what the newer "**The keyboard**
(2026-09-26, the owner's PC-style layout)" paragraph already covers (its own "On a dev host the old letter
map stays alongside" sentence). Kept here only because it was still verbatim-present pre-D19; the newer
paragraph is authoritative.

**Keyboard = gamepad on debug hosts** (`ableem::Input::setKeyboardAsPad`, on by default off the console):
`X O S T` = cross/circle/square/triangle, `I J K L` = d-pad, `Space` = Start, `B` = Select, `Q E 1 2` = L1 R1 L2 R2,
`Esc` = power off (exits). `tools/win_drive.ps1 -Usb <usb> -Sequence "x;5;space;8"` starts the exe, posts those keys
to its window, screenshots after each, and collects the logs — use it to smoke test without a controller.


## Runtime-layout narrative moved in task D19 pass 2

### SonyUI/RetroBoot-hook removal history

in-process and never reach it. `boot.sh` loops `autobleem.sh` -> `selection.sh` since 2026-09-22, so both
come back to the launcher without a reboot; `selection.sh` reboots for anything else (a crash, a missing
`autobleem_cfg.sh` - the file is deleted once read), which brings AutoBleem back up. The stock
SonyUI exit - `starter` mounted over `/usr/sony/bin/pcsx`, USB games linked into `/gaadata` with a `.lic`
each (`link.sh`/`overmount.sh`/`startsony.sh`) - is gone with it (2026-09-18, as in AutoBleem-NG), and so is
`.lic` handling in the scanner. RetroBoot's own update hook went the same day: `autobleem.sh` no longer
runs `retroboot/bin/init.sh` at boot, and the `/tmp/.rbpatching` guards, `rb_patch_background.sh` and
`rb_monitor.sh` are deleted - an RB_Patch dropped on the stick is not applied by AutoBleem any more.

### systemd-tmpfiles aging discovery

**`/tmp` is kept out of systemd's aging** (2026-09-26): the console boots with its clock at 2018-09-01, and on
the AutoBleem kernel WiFi's timesyncd jumps it to today - after which `systemd-tmpfiles-clean.timer` (15 min
after boot, then daily; `/usr/lib/tmpfiles.d/tmp.conf` ages `/tmp` at 10 days) deleted everything boot had put
there as eight years old: `/tmp/lib`'s soname links (the Apps then loaded the firmware's SDL 2.0.4 from
`/usr/lib`), the libs archive, the bind-mounted udev rules file. `boot.sh` writes `x /tmp/*` to
`/run/tmpfiles.d/autobleem.conf` (tmpfs - nothing on the console's own storage), checked on its systemd 229;
psc-kernel-payload `3f67f19`+ also ships a `tmp.conf` without an age. Anything of ours in `/tmp` relies on it.

