<!-- Moved from the launcher's CLAUDE.md (autobleem2/autobleem) on 2026-09-23 when the project's
     knowledge went to autobleem-main. Paths without a repository name are the launcher's. -->

# The PC USB stick (2026-09-20, `pcusb`)

The Pi appliance on a **32-bit x86 PC** (the owner's call: older CPUs must boot it), first of the two PC
targets of `docs/archive/pc-targets-plan.md` (the other, the Windows product, comes after). **Debian 12 Bookworm
i386** - the last Debian with a 32-bit x86 kernel (Trixie has none; Bookworm LTS runs to mid-2028) - and
everything of the Pi's: the launcher on tty1 over kmsdrm, the exFAT data partition, the first-boot screen,
`install.sh`, the online update through `autobleem-update`. What is shared and what differs:

- **One package tree, `payload_linux/`** (was `payload_rpi/`, renamed 2026-09-20): one `install.sh` with
  `PLATFORM=rpi|pcusb` (`detect_platform()`: a Pi by its device tree, a PC by its architecture; `--platform`
  overrides) and the platform-specific parts in `*_rpi` / `*_pcusb` functions - the boot files (a Pi's
  firmware partition + `cmdline.txt`/`config.txt`; a PC's `/boot/efi` + `/etc/default/grub` and
  `update-grub`, the same quiet-boot/splash words through `boot_cmdline_words()`), the disk (the boot
  partition's, or the root's), the arch gate (`i386` -> buildbot's `x86`), the site's folder for RetroArch
  builds and cores (`rpi/` or `pc/`, `PLATFORM_DIR`), the BIOS manifest (`biospack-i386.txt`, 730 files -
  `tools/biospack.py --arch i386`), desktop OpenGL in a source-built RetroArch on x86. `--shrink-root` and
  `--hdmi-mode` stay Pi mechanisms (a PC's KMS driver takes the screen's native mode). **A PC user never reads
  "Pi"** (the owner's rule): `install.sh`'s messages say `$MACHINE`/`$MEDIUM` ("the Pi"/"the card",
  "the PC"/"the stick"), the first-boot dialogs likewise, and `system/autobleem-pc.txt` is the stick's
  edition of the options file. A PC has an RTC, so the first boot's NTP wait is the Pi's alone.
  `autobleem-session.sh` picks the HDMI/DP output whose ELD reports a screen on a PC (`pc_hdmi_audio`; the
  Pi's `vc4hdmi` cards as before). The first-boot script finds the staged package by name
  (`autobleem-pcusb-i386.tar.gz` -> the PC paths) and makes ssh host keys when an image shipped without them.
- **The build**: `AB_TARGET=pcusb` (`toolchains/pcusb/PcUsbToolchain.cmake`: Debian's `i686-linux-gnu`
  cross compiler from the Docker image's `pcusb` stage, `-march=i686 -mtune=generic` - no SSE2, Debian's own
  i386 baseline - `-D_FILE_OFFSET_BITS=64`; **the unit tests build and run there**, i386 being native on the
  amd64 server - the first run as an appliance build found three suites assuming internal games).
  `docker/run.sh ci/build.sh pcusb` -> `dist/pcusb/autobleem-pcusb-i386.tar.gz` (41 MB, top dir
  `autobleem-pcusb`; `tools/make_rpi_package.sh --arch i386`, emu from `Autobleem/bin/emu-i386/` once
  pcsx-ab has an i386 build - **it has none yet**, so the package ships no pcsx-ab and PS1 runs through
  RetroArch's pcsx_rearmed core, `launch.sh`'s fallback). Site: the `pcusb` release kind, `pc/retroarch/`
  (`ci/build_retroarch.sh i386` - the compiler triplet is `i686-linux-gnu`, the multiarch dir
  `i386-linux-gnu`), `pc/cores/i386/` (`ci/build_cores.sh i386`, buildbot's `linux/x86`), `pc/images/`
  (`repo_publish.sh pc-image|pc-retroarch|pc-cores`, `repo_index.py` indexes `pc/` as it does `rpi/`).
  `pcusb.ini`'s `retroarch_catalog=pc/retroarch/latest.json` is where the launcher's update looks for RetroArch.
- **The image, `tools/make_pc_image.sh`**: Debian publishes no i386 disk image, so it is built from packages -
  `mmdebstrap` (root mode under `docker/run.sh --privileged` on the server: its Ubuntu 18.04 kernel refuses
  `newuidmap` in a container, so `--rootless`/`--userns` is unproven there) with a customize hook that
  finishes the root from inside (our staged files, the `autobleem:autobleem` user in `sudo`, plymouth's
  theme in every initramfs, the GRUB menu, no ssh host keys, no machine-id; grub2-common's kernel hook
  diverted for the build since `update-grub` cannot probe a device in a chroot), `mke2fs -d` on the unpacked
  tar (never the tar itself: mke2fs built `--disable-nls` reads it in the C locale and refuses the first
  non-ASCII name), an MBR with p1 the ESP (FAT32 `ABBOOT`: `EFI/BOOT/BOOTIA32.EFI` + `BOOTX64.EFI` from
  `grub-mkimage` with an early config that finds the root by label, and `autobleem.txt`) and p2 the root
  (ext4 `AUTOBLEEM_ROOT`, 4 GB, grown to `root_gib` on the first boot; the data partition is made of the
  rest), `boot.img`/`core.img` written into the MBR gap by hand (`grub-bios-setup` is not in the `-bin`
  packages). No loop device anywhere. **Three kernels** because GRUB's x86_64-efi loader refuses a 32-bit
  kernel: `linux-image-686`, `-686-pae` and **`linux-image-amd64:amd64` as a foreign-architecture package**
  (Bookworm's i386 archive has no amd64 kernel; Debian's release notes describe this route) - the userland
  is i386 whichever runs; `tools/pc_image/10_autobleem` (in place of `10_linux`) picks by `cpuid -l`/`-p`.
  Secure Boot must be off. `--reuse-root` keeps the 8-minute mmdebstrap result while iterating. Output
  `autobleem-<v>-pcusb-i386.img.xz` (593 MB, 4.25 GB raw); the Docker `all` stage carries the tools
  (`grub-*-bin`, `fdisk`, `dosfstools`, `uidmap`, e2fsprogs 1.47.2 from source).
- **First boot in VirtualBox** (2026-09-20, a 32-bit VM with PAE, BIOS; `E:/tmp/pcimg`, VM `ab-pcusb-bios`,
  the VDI grown to 16 GB so the data partition has room): GRUB picked the PAE kernel, plymouth, the
  first-boot screen with the RetroArch question - then it sat on "Preparing the system partition":
  **Bookworm's util-linux no longer carries `sfdisk`** (the `fdisk` package does), and the failure was only
  in the log because the dialog had left the screen in graphics mode - both fixed (the image has `fdisk`, a
  failed grow shows a dialog). `ssh.service` failed five times over on the boot screen for want of host keys
  (a drop-in runs `ssh-keygen -A` ahead of `sshd -t`). To get a shell when the first-boot screen owns the
  keyboard: hold Shift for GRUB, `e`, append `systemd.mask=autobleem-firstboot.service` to the `linux` line,
  Ctrl+X, log in as `autobleem`/`autobleem`; VBoxManage's `keyboardputscancode`/`keyboardputstring` drive it.
  QEMU was tried first and removed again - the owner's VirtualBox is the VM for this. **The second image
  went end to end** the same day: the root grown, the exFAT data partition made, RetroArch (that run took
  the slow road - `pc/retroarch/` was not published yet, the source build died on the mixed GL flags since
  fixed, and Debian's `retroarch` package came in with its Qt desktop - ~400 MB the appliance never uses,
  so on `pcusb` a failed build now means "go on without RetroArch, retry on a later run", and the cores
  are only fetched for a RetroArch that is there), the cores and bundles, 730 BIOS files, the payload, the
  three initramfs (redundant on the image - the theme-unchanged check now applies to every run, two
  minutes saved), a reboot, and **the ab2 launcher on the screen**. The site has `pc/retroarch/`
  (v1.22.2, 6 MB: desktop OpenGL only - GLES and GL together leave RetroArch's gl1 driver unlinkable) and
  `pc/cores/i386/` (212 cores, 779 MB; `unzip`'s "done with warnings" over the cheats bundle used to kill
  `build_cores.sh`), so a fresh first boot takes the fast road - **~8 minutes to the launcher, seen on a
  BIOS VM and on a 64-bit UEFI VM** (the amd64 kernel with the i386 userland: no 64-bit RetroArch exists or
  is needed). The `7ad9b85` image is on the site (`pc/images/`, the `pcusb` package in the pre-release,
  `pc-install.html`). Untested: 32-bit UEFI, real hardware, a pad (keyboard-as-pad is off on an appliance,
  so the VM shows the carousel and no more). Found on the way: **every Pi and PC-stick install had been
  losing its sample games** - the pack has had no `Games/` since Tetrade left and `tar` was told to extract
  it by name (fixed: the members come from the pack).
- **The setup screen is the user's choice on a PC** (2026-09-22, the owner's ask after a stick whose first
  boot retried the graphical screen boot after boot): `autobleem-install-ui.py --backend text` draws every
  screen it has - the progress (heading, the phase bar, the step bar, the output box) and the three dialogs
  - as text on the console in newt's look (whiptail / raspi-config: blue root, grey windows with a shadow,
  red for the selected row and the focused `< OK >` / `< Cancel >` button, a blue field), with nothing but
  the console's escape sequences (no curses, no terminfo; `AB_UI_ASCII=1` for a font without box-drawing
  glyphs, `--render x.txt --size 100x30` for a look on the PC). The dialog text is re-flowed to the window.
  `autobleem-firstboot.sh`'s `choose_ui_mode()`: on `pcusb` the first dialog - drawn with the text screen -
  asks graphical (recommended, taken after 30 s) or text, **on every attempt** (a graphical screen that stays
  black is exactly when the user reboots and wants the question back); a Pi is not asked (gfx as before);
  `installer=gfx|text` in `autobleem.txt` presets either. The answer goes to **`/etc/autobleem/installer-ui`**,
  which `autobleem-update.sh` reads, so the launcher's online updates draw with the same screen. The
  fallback chain is gfx -> text -> plain `read` prompts (`downgrade_ui`, a gfx failure remembered as text);
  `log`/`warn` print to the console only in plain mode (a screen owns it otherwise) and every failure path
  ends in `bail` - the reason as a dialog, the bare console back, tty1 back. Tested on the build server
  through a pty (keys in, the escape stream out); the screenshots the owner saw are that stream rendered.

