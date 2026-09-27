# The PC test machine (`bleemmachine`, R21)

A laptop dedicated to PC-USB (`AB_TARGET=pcusb`) device testing and a second org CI runner. Its address is
in `infrastructure.local.md` (not committed); this file is the how-to.

## Layout

- **The laptop's internal disk is never touched.** Debian 13 x64 lives on an external USB disk; GRUB points at
  the removable path, no NVRAM change. This is the host.
- The host runs, natively: the GitHub Actions runner (`docker/runner`, see "CI runner" below), Docker, and
  KVM/libvirt.
- A libvirt/KVM VM, **`pcusb-test`** (2 vCPU / 2 GiB, `qemu:///system` - a fresh `virsh` needs `-c
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

For interactive driving instead of a one-off screenshot, use **`tools/ab_drive.py`** (the DebugDriver) the
same as any other device (`docs/console.md`, `docs/history/raspberry-pi.md`'s H7 item): set `AB_DEBUG_PORT`
(and, to reach it from outside the VM, `AB_DEBUG_BIND=0.0.0.0` inside the guest only - the VM's own NAT
network, `192.168.122.0/24`, is not the laptop's LAN) via a systemd drop-in on the guest, then reach it
through the laptop:
```bash
ssh -L 6900:192.168.122.<vm-ip>:<port> screemer@<laptop>   # one hop: the VM is on the laptop's own libvirt
                                                            # NAT network (`virsh net-dhcp-leases default`
                                                            # gives its current IP), reachable from the
                                                            # laptop directly - no second ssh needed
python tools/ab_drive.py run "menu 6; wait_screen GuiOptions; shot a.png" --host 127.0.0.1 --port 6900
```
Remove the drop-in afterwards - the same rule as every other device.

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

## CI runner

A second org-scoped self-hosted runner, deliberately **not** sharing the build server's exposure:
- Labels `ab-main,pcusb-test` (`--no-default-labels`) - a dedicated label, not the generic
  `self-hosted,linux,x64` the build server's runner carries, so a workflow only reaches this machine when a
  job is explicitly retargeted at it. Runner group `pcusb-test` (id 3, every autobleem2 repo).
- Runs as its own user (`gha-runner`), a systemd service
  (`actions.runner.autobleem2.bleemmachine.service`), survives reboot.
- **Pull requests never reach it** - the same rule as the build server's runner (`docs/ci.md`): no workflow
  uses `pull_request_target`, and every self-hosted job excludes `pull_request` in its trigger or its `if:`.
- Confirmed 2026-09-27: a job assigned here falls back to the build server's runner correctly when this
  one is stopped (the routing works); a job needing the build server's own container-based runner setup
  still needs that machine specifically, which is a routing/workflow question, not a laptop problem.
