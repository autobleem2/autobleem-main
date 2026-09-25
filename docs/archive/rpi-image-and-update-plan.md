# Pi: the Imager image (done) and an update without a network (parked)

Archived plan (done 2026-09-19 - Part 2, the prebuilt image; Part 1 is parked). The full text is in git
history: `git log -- docs/archive/rpi-image-and-update-plan.md`. What was built for the image is in
`docs/history/raspberry-pi.md` ("Flashable image for Raspberry Pi Imager").

## Part 1 - updating a Pi without a network (parked)

The Pi updates itself online (`UpdateService` -> `autobleem-update` -> `install.sh --update`,
`docs/history/online-update.md`), and `install.sh --update` already is the fast re-run this part first
asked for: nothing repartitioned, RetroArch/cores/BIOS/config kept. What is left is the offline entry point,
for a user with no network and no ssh: **a package dropped on the exFAT data partition from a PC, applied at
the next boot**.

**The idea**

- A folder on the data partition, `Autobleem/update/` (kept by a placeholder file). The user copies
  `autobleem-rpi*.tar.gz` (or a PC-stick package) into it and reboots.
- `autobleem-session.sh` gets `apply_pending_update()`, once per boot, before the launcher loop (not once per
  launcher restart after RetroArch). No tarball -> return at once (the common case).
- Exactly one `*.tar.gz` there: progress straight to `/dev/tty1` ("Applying AutoBleem update: <name>..."),
  since the service's journal is invisible before the launcher owns the screen.
- Check the architecture (the tarball's name vs `dpkg --print-architecture`); a mismatch is logged, the file
  renamed `.rejected`, and the boot goes on.
- Apply it the way the online update does - stage on the **root** filesystem (`/var/tmp`, `tar
  --no-same-owner`: exFAT refuses the archive's uid/gid) and run its `install.sh --update` - rather than
  the separate sha256 diff-copy helper the original plan proposed; one apply path for both.
- On success rename the tarball `applied-<version>.tar.gz.done` (a visible history), remove the stage.
- **Any failure** (bad tar, disk full) logs to tty1 and `System/Logs/update.log`, cleans up, and **starts
  the launcher anyway** on the old files - an update must never be why the appliance fails to boot.
- The same would serve the PC stick; `payload_linux/README.md` gets an "Updating" section.

**Verify when picked up**: a tarball dropped over a Windows share of the exFAT partition shows its progress
on tty1 before the launcher and ends as `applied-*.done`; a corrupt one is logged and the Pi still boots.

## Part 2 - the prebuilt image: lasting gotchas

- A first boot without network is the normal case: the first-boot service owns tty8 and asks for WiFi
  (country first - it unblocks rfkill).
- The stock first boot grows the root over the whole card; the image removes `resize` from `cmdline.txt`
  and `install.sh --grow-root N --grow-only` grows it to a bounded size before anything is unpacked.
- A local image needs a `*.rpi-imager-manifest` for Imager's customisation screen
  (`rpi_imager_local_manifest.py`).

## Still open

- Part 1: the offline update from a package dropped on the data partition (above).
- Part 2, not recorded as verified on hardware: the interactive WiFi prompt end to end, and a first boot
  with Imager presets (hostname/user/WiFi) through the local manifest.
