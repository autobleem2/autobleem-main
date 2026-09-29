# Test devices - hardware, OS and traps

One section per device we test on. Addresses and accounts are in `infrastructure.local.md` (not committed);
`<test-pi>` and the like are the names that file fills in. The laptop and its VM are described in
`docs/pc-test-machine.md`; the console's platform in `docs/console.md`.

## Test Raspberry Pi (`<test-pi>`, a Pi 400)

- **Kernel 64-bit, userland 32-bit.** `uname -m` says aarch64 (`6.18.50+rpt-rpi-v8`), but
  `dpkg --print-architecture` says `armhf`. Build and install the `rpi` target, never `rpi64`. An arm64 binary
  on this userland exits at once with status 127 and no output.
- **SD card:** root `/dev/mmcblk0p2` (ext4); data `/dev/mmcblk0p3` (**exFAT**) mounted at `/media/autobleem`
  (rw, noatime, fmask/dmask 0000). The data partition has no Unix permissions: `chmod` fails with "Operation
  not permitted", and every file is already executable.
- **Service:** the launcher runs as `autobleem.service`: `ExecStart=/usr/local/bin/autobleem-session
  /media/autobleem`, `WorkingDirectory=/media/autobleem/Autobleem/bin/autobleem`,
  `RequiresMountsFor=/media/autobleem`, `RuntimeDirectory=autobleem` (logs and hand-over files in
  `/run/autobleem`), plus a drop-in `nosplash.conf`.
- **Paths:** launcher `/media/autobleem/Autobleem/bin/autobleem/autobleem-gui`; extensions
  `/media/autobleem/Extensions/<name>/` (`store`, `pscbios`; binaries in `bin/rpi/`); logs on the data
  partition in `/media/autobleem/System/Logs/` (`autobleem.log`, `AB_out.txt`, `AB_err.txt`,
  `crash-<n>/reason.txt`, `crash.count`).
- **Privileges:** the normal user has no passwordless sudo, so `systemctl restart autobleem` needs root.
  Replacing the launcher binary on the data partition works as the normal user.
- **Updates:** the launcher's own update check runs here (curl, `nightly/latest.json`). Installation:
  `docs/pi-install-guide.md`.

## PlayStation Classic

- **Storage:** the stick is mounted at `/media`. The console's own storage (eMMC, `/data`) is never written -
  only `/media` and `/tmp`.
- **Busybox userland:** `ps` truncates command lines - read `/proc/<pid>/cmdline`; `sort -h` is not supported.
- **`/tmp` is tmpfs**, emptied by every reboot: anything placed there (e.g. a DebugDriver env file) is gone
  afterwards.
- **Restarting the launcher:** write `AB_SELECTION=8` to `/tmp/autobleem/autobleem_cfg.sh`, then kill the
  `./autobleem-gui /media` process; the loop in `boot.sh` starts it again.
- **Logs:** `/media/System/Logs/` (same file names as on the Pi); runtime dir `/tmp/autobleem`.
- **Replacing the launcher:** the binary on the stick can be busy ("Text file busy") while it runs - move the
  old one aside, then copy the new one.
- The platform itself (hardware, stick layout, boot chain): `docs/console.md`.

## pcusb-test VM

- A Debian guest on the PC test machine (`docs/pc-test-machine.md`). The physical PC-USB test stick is passed
  through to it; its AutoBleem install is at `/media/autobleem` (launcher
  `/media/autobleem/Autobleem/bin/autobleem/autobleem-gui`).
- Reached only through `tools/vm/abvm.py` from a dev PC: take a lease first; `guest "<cmd>"` runs a shell
  command, `drive` opens the DebugDriver on the guest's port 6900.
- Sandboxes (headless launchers, each with its own root folder on the test machine and its own lease) run next
  to it. When every sandbox lease is taken, the stick's own install is the fallback target.
- No network restrictions noted. The stick currently has no extra Store sources configured.
