# The PlayStation Classic - what every repository needs to know

The console as a platform: the hardware, the stick layout, how our code gets control, and how it goes to
standby. Gathered 2026-09-26 from the launcher's CLAUDE.md, psc-kernel-payload, retroarch-psc and
pcsx-abnxt; each of those keeps the code-level detail, this page keeps the facts they share.

## The hardware and its software

| | |
|---|---|
| SoC | MediaTek MT8167, 4x Cortex-A35 run in **aarch32** (armhf); build for `-march=armv8-a -mfpu=neon-vfpv4` - the kernel's HWCAP lacks the armv8 FP bit, so `neon-fp-armv8` code is refused at run time |
| GPU | PowerVR **GE8300** (GX6250 in older docs is the MT8173's - wrong), DDK 1.9 blob; it pins the kernel at **4.4** (the owner, 2026-09-25: no kernel bump) |
| Display | Sony's Weston **1.11**, `wl_shell` only (no xdg shell), libwayland **1.12**; no X |
| Audio | ALSA; no OSS |
| C runtime | glibc **2.24**, libstdc++ 6.0.22 - a console binary may need at most `GLIBC_2.24` / `GLIBCXX_3.4.22` and no RPATH (`check_psc_binary.sh`) |
| SDL | our SDL2 **2.0.14** at most (the last with a `wl_shell` window), Wayland + ALSA only, in `Autobleem/lib/libs.tar.gz` -> `/tmp/lib`. Everything on the console - the launcher, both emulators, the tools, the Apps - uses that one set. A newer SDL is an idea (`docs/ideas.md`) |
| Toolchain | the autobleem-build image's `/opt/psc`: a Debian Stretch sysroot and Stretch's gcc-6 (C++14). A C++17 App (Amiberry) uses gcc-12 against the same sysroot with libstdc++ linked in |
| Init | **systemd** - `halt`/`reboot`/`shutdown` are `systemctl`; the board has no real halt (a `shutdown -h` reboots) |
| Storage | the eMMC is **never written** (decisions.md) - the stick and `/tmp` only; ABFlashKit flashing the kernel on the user's request is the one exception |
| Clock | no battery; a stored mtime cannot be trusted across a reboot (fingerprints use sizes, never mtimes); the AutoBleem kernel gives a real clock (`/autobleem` exists) |

**Kernels.** *Stock*: Sony's. *AutoBleem kernel*: psc-kernel (4.4.22 vendor fork) + psc-kernel-payload's
overlay, flashed by ABFlashKit - `boot.img` (a FIT: LZ4 kernel + dtb, `dd` to BOOTIMG1, unsigned),
`abrootfs.tgz` unpacked to `/data/autobleem/rootfs` (the one sanctioned eMMC write), `recovery-{on,off}.img`
(MISC flags). It adds WiFi, BlueZ, curl, a USB network gadget (RNDIS; root password `autobleem`, a
per-console dropbear host key), exFAT, and - on `feature/pad-drivers` - the 6.1 pad drivers backported.
The overlay's rule: **it only adds to the console, it never shadows a file of the stock root**
(`overlay.py shape/check` against `reference/console-rootfs.txt`; a busybox `/bin/sh` shadowing Sony's
broke AutoBleem's start on 2026-09-24). Recovery: `docs/kernel-flash-recovery.md` and pc-tools'
LastResortRecovery.

**USB ports.** Sticks and pads belong on the **front** ports. The rear micro-USB (power) port is an OTG
*host* on the AutoBleem kernel (a device on the stock one): hot-plugging there drops the USB stack (`-71`
errors, cause unproven), and a device on it makes the kernel refuse suspend-to-RAM (see Power Off).
**Every resume resets the USB bus** - hub, pads and stick re-enumerate within ~2 s.

**Buttons.** RESET = the input key `KEY_PLAYPAUSE` (SDL: `SDL_SCANCODE_AUDIOPLAY`) - it leaves every game
and App (the owner's rule; see `docs/emulator-contract.md` and `docs/app-ports.md`). OPEN = `KEY_EJECT`
(RetroArch's menu). POWER = the power-off handler (below).

## The stick (`/media`)

A stock console reads **FAT32 only**; exFAT needs the AutoBleem kernel. The partition label must start
with `SONY`.

```
Autobleem/bin/autobleem/   the launcher + absplash, abfatflag + resources (run.sh, lang/, platform/, splash/)
Autobleem/bin/emu/         pcsx-ab + plugins            Autobleem/bin/emunxt/  pcsx-abnxt (the default)
Autobleem/bin/abpad/       the virtual gamepad          Autobleem/bin/db/      covers*.db
Autobleem/rc/*.sh          boot, launch and standby glue (the launcher's payload/Autobleem/rc)
Autobleem/lib/libs.tar.gz  the SDL2 family -> /tmp/lib;  lib/apps, lib/retroarch, lib/modules: the site's libs pack
Games/                     one folder per game (sub-folders allowed); Games/!SaveStates/<folder name>/ (every
                           game's states and its own card, keyed by the folder's *name*); Games/!MemCards/ (shared cards)
System/Databases/          regional.db (USB games), internal.db (copy of the stock DB + columns)
System/Logs/               crash-<n>/ (last 3), saved-<n>/, standby.log, update.log, installer.log;
                           everything else only with the `keep` marker (the quiet stick)
System/Extensions/  System/Processors/  System/lightguns.txt  System/Bios|Preferences|Region|UI/ (backups)
Themes/<name>/theme.json   Apps/<name>/ (app.ini, bin/<key>/)   Extensions/<name>/ (extension.ini)
RetroArch/bin/             RetroArch's tree (binary, cores/, info/, database/rdb/, thumbnails/, playlists/)
RetroArch/bios/            the cores' BIOS files        RetroArch/roms/<system>/  the other systems' games
/tmp/autobleem/            the runtime dir (RAM): logs/, autobleem_cfg.sh, ra-append.cfg, exit/, extensions.active
/gaadata/<id>/             the 20 built-in games (read-only console storage)
```

**The quiet stick** (2026-09-24): the stick is written only when the user's state changes - a save, a
card, a kept resume slot, a changed setting, a game added or removed. Logs, the selection hand-over and
RetroArch's appended config live in the runtime dir. Anything that runs per boot, per scan or per launch
writes through `writeFileIfChanged` or to the runtime dir (core's `test_quiet_stick.cpp` guards it).

## How our code gets control

1. `usbwatch.service` (`usb_watch`) polls `blkid` every 2 s for a `SONY*`-labelled `sd[ab]1`, mounts it
   rw on `/media` (~6 s after power-on), finds `/media/028c18a9-ec4b-4632-b2cf-d4e20f252e8f/` (one of
   Sony's update ids), "verifies" `LUPDATA.BIN` into `/tmp/diag/.../start` and runs it: the red LED
   blinks for 5.6 s, then `cd /media/Autobleem; source ./start.sh`. **The whole chain is sourced by a
   shell whose script is on tmpfs.**
2. `powermanage.service` puts the console into its boot standby (`echo mem`) during that blink - the
   stick is mounted rw through it; nothing of ours runs before it.
3. `start.sh` -> `rc/boot.sh`: bind-mounts `rc/20-joystick.rules` over `/etc/udev/rules.d` (two pads
   through one hub), `killsony.sh`, `backup.sh`, `checkstick.sh` (the dirty flag, below), loads a stick
   module only when the kernel has none of its own, then loops `autobleem.sh` -> `selection.sh`.
4. `autobleem.sh` unpacks `libs.tar.gz` to `/tmp/lib`, runs `bin/autobleem/run.sh` -> `autobleem-gui /media`.
5. The launcher starts games in-process (`rc/launch.sh` for PCSX, `rc/launch_rb.sh` for RetroArch, an
   App's `rc/app_run.sh`) and comes back to its loop. It leaves only by writing `<runtime>/autobleem_cfg.sh`
   (`AB_SELECTION=`): **4** RetroArch/EmulationStation, **6** the online update (`abupdate` from tmpfs,
   downloaded with `abfetch`, our own HTTPS client), **7** Power Off. `selection.sh` (a copy on tmpfs)
   acts on it and loops back; anything else - a crash, no file - persists the logs and reboots.

## Power Off - Sony's standby with the stick unmounted

The launcher's Power Off (the system menu and the power button) sets selection 7 and unwinds cleanly;
`selection.sh`'s `standby()` then: `rm System/.session`, `umount /media` (five tries; busy -> the holders
into `System/Logs/standby.log` and a reboot), clears the dirty flag if it is ours, **green LED off, red
on**, `echo mem`. After the power button: green on, 3 s for the bus, up to 30 s of `blkid` for the `SONY`
partition, mount it as usb_watch does, `touch System/.session`, back to the launcher under the splash. No
stick after 30 s -> reboot. **The red LED alone is AutoBleem's standby.**

On the AutoBleem kernel the RNDIS gadget is switched off and back on around it (the overlay's `rndis
restart`, in the background - it never returns). If the kernel refuses the suspend (a device on the OTG
port: `musb_bus_suspend: trying to suspend as a_host while active`), it is retried twice, logged, and the
third time `shutdown -h now` powers the console down instead - POWER is then a cold boot. **Never read
`/sys/power/wakeup_count`** in these scripts: it blocks while a wakeup is in progress.

## The FAT dirty flag

Linux's fat driver sets the boot sector's dirty bit on an rw mount and clears it on umount - but **never
clears a flag it found set at mount time**, so a stick pulled once during the boot standby would stay dirty
for ever (and Windows would offer to "scan and fix" it every time). `abfatflag` (the launcher's
`src/tools/`, over core's `FatDirtyFlag`: FAT12/16/32 and exFAT's `VolumeFlags`) fixes that:
`rc/checkstick.sh` at boot, when `System/.session` is absent (the last session ended through the standby),
remounts ro, clears the flag if still set (then it is ours), and marks it dirty again after the rw remount
so "mounted rw = dirty" stays true on disk. A session that ended any other way - the stick pulled while the
launcher ran, a crash - keeps the marker, and Windows gets to repair real damage.

## Debugging on the console

- The console on WiFi (the AutoBleem kernel) takes `ssh root@<ip>`; the RT5370 dongle only after boot.
- `System/Logs/keep` (Options -> Diagnostics) keeps every log on the stick; Hardware Information's Square
  copies the RAM logs there once.
- `AB_SHOT=<file%d.bmp>` (the launcher) / `PLAT_SDL2_SHOT` (pcsx-abnxt) save frames; `AB_DEBUG_PORT` takes
  a DebugDriver connection (`tools/ab_drive.py`, `tools/emu_drive.py`) - over `ssh -L` on a console.
- pcsx-abnxt's CLAUDE.md has the core-dump recipe.
