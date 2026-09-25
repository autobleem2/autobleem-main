# The PC USB stick (`pcusb`)

The Pi appliance on a 32-bit x86 PC: what it shares with the Pi, how its image is built and how its first
boot differs. Paths without a repository name are the launcher's; the Pi side is `raspberry-pi.md`.

## What it is

- **Debian 12 Bookworm i386** (the owner's call: older CPUs must boot it) - the last Debian with a 32-bit
  x86 kernel (Trixie has none; Bookworm LTS runs to mid-2028). Everything of the Pi's: the launcher on tty1
  over kmsdrm, the exFAT data partition, the first-boot screen, `install.sh`, `autobleem-update`.
- **One package tree, `payload_linux/`**: `install.sh` has `PLATFORM=rpi|pcusb` (`detect_platform()`, a Pi by
  its device tree; `--platform` overrides) with the differences in `*_rpi` / `*_pcusb` functions: boot files
  (`/boot/efi` + `/etc/default/grub` + `update-grub` on a PC, the same quiet/splash words via
  `boot_cmdline_words()`), the disk (the root's), the arch (`i386` -> buildbot's `x86`), the site folder
  (`pc/`, `PLATFORM_DIR`), the BIOS manifest (`biospack-i386.txt`). `--shrink-root` and `--hdmi-mode` are
  Pi-only (a PC's KMS takes the native mode). A PC has an RTC: no NTP wait.
- **A PC user never reads "Pi"** (the owner's rule): messages use `$MACHINE`/`$MEDIUM`, and
  `system/autobleem-pc.txt` is the stick's options file. `autobleem-session.sh` picks the HDMI/DP output whose
  ELD reports a screen (`pc_hdmi_audio`).
- RetroArch on x86 is **desktop OpenGL only** (GLES and GL together leave the gl1 driver unlinkable). A failed
  RetroArch build means "go on without it, retry on a later run", and cores are only fetched for a RetroArch
  that is there. No 64-bit RetroArch is needed: on the amd64 kernel the userland stays i386.

## Build

- `AB_TARGET=pcusb`, `toolchains/pcusb/PcUsbToolchain.cmake`: Debian's `i686-linux-gnu` cross compiler,
  `-march=i686 -mtune=generic` (no SSE2, Debian's i386 baseline), `-D_FILE_OFFSET_BITS=64`. The unit tests
  build and run there (i386 is native on the amd64 server).
- `docker/run.sh ci/build.sh pcusb` -> `dist/pcusb/autobleem-pcusb-i386.tar.gz`
  (`tools/make_rpi_package.sh --arch i386`, emu from `Autobleem/bin/emu-i386/`). The site: `pc/retroarch/`
  (`ci/build_retroarch.sh i386` - triplet `i686-linux-gnu`, multiarch dir `i386-linux-gnu`), `pc/cores/i386/`,
  `pc/images/`. `pcusb.ini`'s `retroarch_catalog=pc/retroarch/latest.json`.

## The image, `tools/make_pc_image.sh`

- Debian publishes no i386 disk image, so it is built from packages: `mmdebstrap` (root mode under
  `docker/run.sh --privileged`; rootless is unproven on the server's kernel) with a customize hook that
  finishes the root from inside (staged files, the `autobleem` user in `sudo`, plymouth in every initramfs,
  the GRUB menu, no ssh host keys, no machine-id; grub2-common's kernel hook diverted, since `update-grub`
  cannot probe a device in a chroot).
- **No loop device anywhere**: the root is `mke2fs -d` on the *unpacked* tar (never the tar itself - an
  NLS-less mke2fs reads it in the C locale and refuses the first non-ASCII name). MBR: p1 the ESP (FAT32
  `ABBOOT`, `EFI/BOOT/BOOTIA32.EFI` + `BOOTX64.EFI` from `grub-mkimage` with an early config that finds the
  root by label, plus `autobleem.txt`), p2 the root (ext4 `AUTOBLEEM_ROOT`, 4 GB, grown to `root_gib` at
  first boot; data partition from the rest). `boot.img`/`core.img` are written into the MBR gap by hand.
- **Three kernels**, because GRUB's x86_64-efi loader refuses a 32-bit kernel: `linux-image-686`,
  `-686-pae` and `linux-image-amd64:amd64` as a foreign-architecture package; `tools/pc_image/10_autobleem`
  picks by `cpuid`. Secure Boot must be off.
- Bookworm's `sfdisk` is in the `fdisk` package (not util-linux) - the image carries it. An ssh drop-in runs
  `ssh-keygen -A` ahead of `sshd -t`; the first-boot script also makes host keys.
- `--reuse-root` keeps the ~8-minute mmdebstrap result while iterating. Output
  `autobleem-<v>-pcusb-i386.img.xz` (~600 MB, 4.25 GB raw). A fresh first boot takes ~8 minutes to the
  launcher (BIOS VM and 64-bit UEFI VM). Test in the owner's VirtualBox; to get a shell past the first-boot
  screen: Shift for GRUB, `e`, append `systemd.mask=autobleem-firstboot.service`.

## The setup screen

- `autobleem-install-ui.py --backend text` draws the progress and the three dialogs as text in newt's look
  (whiptail/raspi-config colours) with plain escape sequences - no curses, no terminfo (`AB_UI_ASCII=1` for a
  font without box drawing, `--render x.txt --size 100x30` to look on a PC).
- On `pcusb` the first dialog, in text, asks **graphical (default after 30 s) or text on every attempt** (a
  black graphical screen is exactly when the user reboots and wants the question back); a Pi is not asked.
  `installer=gfx|text` in `autobleem.txt` presets it. The answer goes to `/etc/autobleem/installer-ui`,
  which `autobleem-update.sh` reads too. Fallback chain gfx -> text -> plain prompts; every failure path
  ends in `bail` (the reason as a dialog, the console and tty1 back).

## Still open

- pcsx-ab / pcsx-abnxt have no i386 build: the package ships none and PS1 runs through RetroArch's
  pcsx_rearmed core (`launch.sh`'s fallback).
- Untested: 32-bit UEFI, real hardware, a pad (keyboard-as-pad is off on an appliance).
- mmdebstrap rootless (`--rootless`/`--userns`) is unproven on the build server.
