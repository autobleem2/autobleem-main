# The PC test machine (`bleemmachine`, RELEASE-10)

A laptop dedicated to PC-USB (`AB_TARGET=pcusb`) device testing and a second org CI runner. Its address is
in `infrastructure.local.md` (not committed); this file is the how-to.

## Layout

- **The laptop's internal disk is never touched.** Debian 13 x64 lives on an external USB disk; GRUB points at
  the removable path, no NVRAM change. This is the host.
- The host runs, natively: the GitHub Actions runner (`docker/runner`, see "CI runner" below), Docker, and
  KVM/libvirt.
- A libvirt/KVM VM, **`pcusb-test`** (2 vCPU / 2 GiB, **autostart on** - it comes up with the laptop, `qemu:///system` - a fresh `virsh` needs `-c
  qemu:///system`, the unprivileged per-user session driver is the default otherwise and cannot make a
  bridge), boots the **real PC-USB pendrive** by whole-USB-device passthrough - not an imported disk image,
  so the same first-boot/update/BIOS paths a real machine takes are exercised. `screemer` is in the `libvirt`
  group: attaching/starting the VM needs no sudo.
- A real-hardware pass boots the laptop itself from that same pendrive when a test needs actual PC BIOS/UEFI
  (never at the same time as the VM - one or the other has the stick).

### The pendrive passthrough

Identify the drive read-only first - never guess:
```bash
lsblk -o NAME,SIZE,TRAN,MODEL,SERIAL,LABEL
ls -la /dev/disk/by-id/          # stable path, never /dev/sdX
```
Then its USB vendor:product id (for a *whole-device* hostdev passthrough - the VM gets the drive, not a
partition):
```bash
udevadm info --attribute-walk --name=/dev/sdX | grep -E 'idVendor|idProduct'
lsusb -d <vendor>:<product>      # confirm it is the only device with that id on the box
```
Attach it (persists across VM restarts; the VM must be off to attach for the first time cleanly):
```xml
<hostdev mode='subsystem' type='usb' managed='yes'>
  <source>
    <vendor id='0x<vendor>'/>
    <product id='0x<product>'/>
  </source>
</hostdev>
```
```bash
virsh -c qemu:///system attach-device pcusb-test hostdev.xml --config --persistent
virsh -c qemu:///system start pcusb-test
```
The VM's `<os><boot dev='hd'/></os>` (SeaBIOS, no other disk defined) boots the USB stick's GRUB directly -
no boot-order fiddling needed.

## Getting a screenshot or a screen recording back

**Never a VNC port on the LAN and never a window on the owner's PC.** `virsh domdisplay` reports the VM's
VNC socket bound to `127.0.0.1` on the laptop; read frames locally with:
```bash
virsh -c qemu:///system screenshot pcusb-test /tmp/shot.ppm   # PNG despite the extension
```
copy it back over the same ssh connection (`scp screemer@<laptop>:/tmp/shot.ppm ...`). This needs no tunnel,
no extra port, and nothing is ever exposed beyond the ssh session already in use.

**Driving the UI is `tools/ab_drive.py` (the DebugDriver), always** - not padsim (the owner, 2026-09-27:
padsim navigation is not stable yet). It is set up permanently for every dev:
- **Guest**: `/etc/systemd/system/autobleem.service.d/debug-driver.conf` (root fs) sets
  `AB_DEBUG_PORT=6900`; the launcher listens on the guest's own `127.0.0.1:6900` (loopback only).
- **Laptop**: a `screemer` user service, `~/.config/systemd/user/pcusb-test-debugdriver.service` (linger on,
  so it runs from boot with nobody logged in), holds an ssh forward from the laptop's **`127.0.0.1:6900`**
  to the guest's - never the LAN. The guest's address is pinned (`192.168.122.119`, a DHCP reservation for
  its MAC in libvirt's `default` network), so the forward does not break on a new lease.
- **From your PC**, one hop:
```bash
ssh -L 16900:127.0.0.1:6900 screemer@<laptop>
python tools/ab_drive.py run "menu software; wait 4000; grab upd.png" --port 16900
```
Use a local port other than 6900 on a dev PC - a local dev launcher may already hold the default one.
`grab` brings the frame back over the socket; nothing is written on the stick. `systemctl --user status
pcusb-test-debugdriver` on the laptop if it does not answer (the launcher restarts with the service; the
forward reconnects every 5 s).

## Installing a nightly

Two ways, depending on what is being tested:

**A - in place, through the launcher's own updater** (what a real user does; use this when the launcher on
the stick already runs and the test is about the update path itself, or about whatever changed since the
stick's current build):
1. `config.ini`'s `updates=nightly` (Options -> Updates also offers this on-screen).
2. L2+R2 -> **Software Update** checks on the spot and offers the download - or wait for the automatic
   24-hourly check. `docs/tester-checklist.md` section 3 is the exact walk-through (3.4, 3.7).
3. The apply step is `autobleem-update.sh` -> `install.sh --update`: nothing is repartitioned, the user's
   games/saves/settings are kept, and the first start after re-scans (fingerprints are dropped on purpose).
4. Read `System/Logs/update.log` first if it looks like it "did nothing" - a failed apply is a short dialog
   before the restart, easy to miss on a screenshot taken a beat late.

**B - reimage the pendrive from a fresh build** (what a first-boot, an install-time bug, or a from-scratch
regression test needs - and the only option before any launcher has ever run on the stick):
1. Fetch `pc/images/latest.json` from the site (`autobleem.retromenele.pl`) for the current channel's
   `autobleem-<v>-pcusb-i386.img.xz`, or a specific nightly's manifest entry.
2. `sha256sum` it against the manifest before doing anything else with it.
3. `unxz` it, then write it to the pendrive's **by-id path** (never `/dev/sdX`) with `dd` - this is the one
   genuinely irreversible step in the whole loop, and needs the owner's own direct go for the exact command
   every time (the auto-mode safety classifier also refuses an agent-run `dd` on its own; the owner runs it,
   or explicitly allows that class of command first).
4. Boot (VM passthrough or real hardware) into the fresh first-boot setup wizard.

## The virtual gamepad (padsim, RELEASE-14)

**Not for driving the UI** (the owner, 2026-09-27) - use the DebugDriver above. padsim stays installed for
the day a test needs a real evdev pad in the guest (an emulator or an App's input), once it is made stable.

The VM's pendrive is a real appliance stick - it has no way to take pad input except a real controller
plugged into the laptop and passed through, which doesn't script. **padsim** is a test-only virtual X360
gamepad, reachable and drivable from the host, so `ab_drive.py`-style scripting works on a real running
launcher instead of just the DebugDriver's own build.

- **Guest side**: `padsim` (a small C daemon, source at `/usr/local/src/padsim/padsim.c` in the guest,
  binary at `/usr/local/bin/padsim`) opens a uinput device shaped exactly like a wired Xbox 360 pad
  (vendor `0x045e`, product `0x028e`, the standard button/axis layout) - the same thing SDL2, RetroArch,
  both PCSX forks and Apps all already resolve natively, so nothing new needs teaching. It's started by
  `padsim.service`, a systemd unit on the **guest's root filesystem** (`/etc/systemd/system/padsim.service`
  - never the data/exFAT partition, so it can't be mistaken for anything shipped on a real stick), reading
  `/dev/virtio-ports/org.autobleem.padsim`.
- **Host side**: the guest's virtio-serial port is backed by a plain unix socket on the laptop (no network,
  no TCP port) - the channel device in the VM's domain XML:
  ```xml
  <channel type='unix'>
    <source mode='bind' path='/tmp/pcusb-test-padsim.sock'/>
    <target type='virtio' name='org.autobleem.padsim'/>
  </channel>
  ```
  (needs a `<controller type='virtio-serial' index='0'/>` alongside it; the socket's `source path` is
  pinned to `/tmp` deliberately - libvirt's own default location under `/run/libvirt/qemu/channel/...` is
  `0750 libvirt-qemu:libvirt-qemu`, unreachable by `screemer` without also being in that group).
- **Driving it**: `python tools/padsim_client.py --socket /tmp/pcusb-test-padsim.sock press a` (or
  `run "dpad down; wait 200; press a"`) from bleemmachine itself. One line in, one `ok`/`err <msg>` line
  back - the same shape as `ab_drive.py`'s own DebugDriver protocol, with padsim's own small vocabulary
  (`press`/`release`/`hold`/`stick`/`trigger`/`dpad`) documented in the script's own docstring.
- **Proven end to end** (2026-09-27, debugging.md's bar): a `press a` sent from the host socket, the raw
  evdev bytes read back in the guest (`EV_KEY BTN_SOUTH` press + `SYN`, then release + `SYN` - exact byte
  match, not just "a device exists"), and the running launcher's Options screen visibly moving its
  selection three rows for three `dpad down` commands sent the same way, caught in a `virsh screenshot`
  before/after pair.

### What's different from a clean pcusb-test-vm image

Everything below is test-machine convenience, never anything a real stick or a real user sees. Reimaging
the VM's pendrive from a fresh build (Method B above) wipes all of it - use that path whenever a test needs
to rule out these additions as the cause of something:
- sshd host keys + the `autobleem` user's `authorized_keys` (one dedicated key, `pcusb-test-vm_ed25519` on
  bleemmachine) - persistent SSH into the guest, owner-approved for this VM specifically.
- `autobleem ALL=(ALL) NOPASSWD:ALL` in `/etc/sudoers.d/taskforce-vm-sandbox`.
- `gcc`, `make`, `evtest` (apt-installed, pulled in the i386 dev toolchain as dependencies).
- `/etc/modules-load.d/padsim.conf` (loads `uinput` at boot) and `/etc/udev/rules.d/99-padsim-uinput.rules`
  (`/dev/uinput` group `input`, mode 0660).
- `/usr/local/bin/padsim` + `/usr/local/src/padsim/padsim.c` + `/etc/systemd/system/padsim.service`
  (enabled, root-fs only).
- `/etc/systemd/system/autobleem.service.d/debug-driver.conf` (`AB_DEBUG_PORT=6900`, the DebugDriver).
- On the host (bleemmachine): `screemer` added to the `libvirt-qemu` group (owner's direct OK), and the
  VM's domain XML has the extra `<controller type='virtio-serial'>` + `<channel>` device; the
  `pcusb-test-debugdriver` user service with linger enabled; the DHCP reservation pinning the guest's IP.

None of this touches the exFAT data partition (`Games/`, `System/`, the launcher's own tree) - a reimage of
just the pendrive, or a fresh VM disk, clears it all in one step.

## The two monitors: shell and status panel (RELEASE-13)

The laptop boots straight into **sway** (a Wayland compositor): `screemer` logs in on tty1 by itself
(`/etc/systemd/system/getty@tty1.service.d/autologin.conf`) and `~/.profile` starts sway there through
`~/.local/share/abpanel/start-sway.sh` - on tty1 only, never over ssh. If sway exits, tty1 stays at a plain shell (`~/.cache/sway.log`); logging out starts
it again. Packages: `sway foot virt-viewer grim chafa` (the owner's sudo, `--no-install-recommends`).

- **Workspace 1** (the working monitor, `$work` = `eDP-1`, the laptop's screen): a full-screen foot with tmux
  session `main` - `tmux attach -t main` over ssh joins the same shell. 14 pt (`~/.config/foot/foot.ini`).
- **Workspace 2** (the standby monitor, `$panel` = `DVI-I-1`, the monitor on the dock): 12 pt, four quadrants, laid out by `tools/abpanel/layout.sh`
  (the owner's layout, 2026-09-27; merged into launcher develop as 83dd31f):
  - top-left, `abpanel overview`: the logo, host, runners and VM, then the htop-like load view (a bar per
    core, memory, swap, load average, disk, the top processes by CPU and by memory side by side);
  - top-right: the VM's **live** view (`virt-viewer --attach`: through libvirt, no port of its own; the VM's
    VNC listens on 127.0.0.1 only);
  - bottom-left, `abpanel teams`: autobleem-main's `status.json` on develop (every 60 s, no token) - usage,
    the teams, Needs the owner;
  - bottom-right, `abpanel empty`: reserved, blank until its use is decided.
- Without the dock both workspaces are on the laptop's screen: **Super+1** the shell, **Super+2** the panel. Super+Return a new terminal, Super+Shift+E leaves sway.
- The code is the launcher repo's `tools/abpanel/` (abpanel.py, layout.sh, start-sway.sh, sway.config,
  foot.ini); `install.sh` puts it in place for the current user (`~/.local/share/abpanel`,
  `~/.config/sway/config`, `~/.config/foot/foot.ini`, the `~/.profile` block),
  `install.sh --uninstall` takes it away. After an update: `git pull` in `~/src/autobleem`, run `install.sh`,
  then log the tty1 session out (`loginctl terminate-session <tty1's session>`) to restart sway.
- One-frame checks over ssh: `abpanel overview --once`, `teams --once` (also `status`, `load`).
- Screenshots (for the owner's look checks): `grim` with `SWAYSOCK=/run/user/1000/sway-ipc.1000.$(pgrep -x sway).sock`
  and `WAYLAND_DISPLAY=wayland-1`; `grim -o DVI-I-1 panel.png`. With the dock, `grim -o eDP-1` fails
  ("failed to copy output") - the laptop's screen is on the secondary GPU; judge it by eye.

**The second monitor is on the ThinkPad Hybrid USB-C dock, which is DisplayLink** (`lsusb` 17e9:6015): its
video goes over USB, so the Intel GPU never sees it (`DP-*`/`HDMI-*` stay "disconnected"). It needs the
DisplayLink driver from **Synaptics' own APT repository** (`synaptics-repository-keyring.deb` from
synaptics.com, adding `/etc/apt/sources.list.d/synaptics.list`, key scoped with `signed-by`), package
`displaylink-driver` (the proprietary DisplayLinkManager daemon) with Synaptics' `evdi` DKMS module. Secure
Boot is off, so the module needs no signing. **DKMS rebuilds evdi on every kernel update** - that needs
`linux-headers-<new kernel>` installed with it (`linux-headers-amd64` pulls them); if the second monitor is
gone after an update, check `/usr/sbin/dkms status` first (installed 2026-09-27, displaylink-driver 6.4.0-22,
evdi 1.15.1).

**sway with the evdi card** (tried 2026-09-27, `start-sway.sh`): only one setup runs both monitors - the evdi
card **first** in `WLR_DRM_DEVICES` (by-path names, `platform-evdi.0-card` then the Intel `pci-0000:00:02.0-card`),
`WLR_RENDERER_ALLOW_SOFTWARE=1` (the primary renderer is then software), `WLR_DRM_NO_MODIFIERS=1`, and
`sway --unsupported-gpu` (sway refuses DisplayLink's proprietary daemon otherwise). The Intel card first
crashes sway the moment it drives the evdi output; `WLR_RENDERER=pixman` cannot add the second card. The
driver makes four evdi cards; only the first is given to sway (the empty ones fail the DRM backend).

## Building every target on the laptop (RELEASE-12)

Every toolchain is in the build image, so the laptop needs nothing but Docker (`screemer` is in the `docker`
group - no sudo). Both images are pulled: `ghcr.io/autobleem2/autobleem-build:develop` (nightly/develop
builds) and `:latest` (release builds) - `docker pull` either to refresh it. Checkouts in `~/src`: the launcher
(`autobleem`, with submodules) and, next to it, `pcsx-ab` and `pcsx-abnxt` - `ci/build.sh` builds both
emulators first for psc/rpi/rpi64/pcusb (`AB_NO_PCSX=1` ships the checked-in binaries instead).

One command per target, from `~/src/autobleem` (`git pull --recurse-submodules` first):
```bash
AB_BUILD_IMAGE=ghcr.io/autobleem2/autobleem-build:develop docker/run.sh ci/build.sh <psc|rpi|rpi64|pcusb|win>
```
Measured 2026-09-27 (8 threads, sccache cold, the runners idle): psc 237 s, rpi 578 s, rpi64 324 s, pcusb
326 s, win 618 s - all exit 0. The package lands in `dist/<target>/` (psc: `.zip` + `.tar.gz`; rpi/rpi64/pcusb:
the installer tarball; win: `AutoBleemSetup-*.exe` + the product zip). Getting it back to a PC:
```bash
scp screemer@<laptop>:src/autobleem/dist/<target>/* .
```
**A local build no longer dirties the tree** (DOCS-15, 2026-09-27): for the appliance and console targets
`ci/build.sh` used to write the freshly built emulators straight over the checked-in ones in
`payload*/Autobleem/bin/emu*` (tracked files) before the launcher's version header was generated, so git saw
a modified tree and the version stamped `-dirty`. It now stages them into `build_<t>/emu-stage/` instead and
packages from there - `payload/` and `payload_linux/` stay exactly as checked out, `git status --porcelain`
is empty after a build, and the version is clean. If an older build (from before DOCS-15) left the tree dirty,
`git checkout -- payload payload_linux` still restores it.

## CI runner

Three org-scoped self-hosted runners, deliberately **not** sharing the build server's exposure:
- **bleemmachine** carries `ab-main,pcusb-test`; **bleemmachine-2** and **bleemmachine-3** (2026-09-27,
  scale-out) carry `ab-main` only, so a job that drives the VM (`pcusb-test`) can only land on the first one and
  never runs twice at once. Three is the ceiling: 4 cores / 8 threads with the VM holding 2 vCPUs (RAM is not
  the limit). Each has its own directory (`~gha-runner/actions-runner[-N]`) and service
  (`actions.runner.autobleem2.bleemmachine[-N].service`).
- Labels (`--no-default-labels`) - a dedicated label, not the generic
  `self-hosted,linux,x64` the build server's runner carries, so a workflow only reaches this machine when a
  job is explicitly retargeted at it. Runner group `pcusb-test` (id 3, every autobleem2 repo).
- Runs as its own user (`gha-runner`), a systemd service
  (`actions.runner.autobleem2.bleemmachine.service`), survives reboot.
- **Pull requests never reach it** - the same rule as the build server's runner (`docs/ci.md`): no workflow
  uses `pull_request_target`, and every self-hosted job excludes `pull_request` in its trigger or its `if:`.
- Confirmed 2026-09-27: a job assigned here falls back to the build server's runner correctly when this
  one is stopped (the routing works); a job needing the build server's own container-based runner setup
  still needs that machine specifically, which is a routing/workflow question, not a laptop problem.
