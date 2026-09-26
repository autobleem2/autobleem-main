# The console's power off - and how the exploit chain really runs

Moved verbatim out of the launcher's CLAUDE.md on 2026-09-26 (task D19); this is the full forensic account of how the boot/standby/power-off chain was found to work. The load-bearing facts and rules this section pinned stay in CLAUDE.md's own condensed "The console's power off" section.

### The console's power off (2026-09-22) - and how the exploit chain really runs

What the boot really is, from `tools/psc_mount_debug.sh`'s dumps (the two rounds are in the git log of this
entry): the console is **systemd** (`halt`/`reboot`/`shutdown` are `systemctl`); `powermanage.service`
(`/usr/bin/start_pman`) does its housekeeping and then **`echo mem > /sys/power/state` - the "1st
suspend"**, the standby every boot goes through before the power button; `usbwatch.service`
(`/usr/bin/usb_watch`) polls `blkid` every 2 s for a `SONY*`-labelled `sd[ab]1`, mounts it rw on `/media`,
finds `/media/028c18a9-.../` (one of Sony's eight update ids), gpg-"verifies" `LUPDATA.BIN` into
`/tmp/diag/028c.../start` and runs it - `red_led 14 0.2` (the 5.6 s blink) then `cd /media/Autobleem; source
./start.sh` - so **our whole chain is sourced into a shell whose script lives on tmpfs**; the only thing of
Sony's that ever holds the stick is that shell's cwd, which our `cd` moved there. The mount lands at ~6 s,
the suspend during the blink: the stick is mounted rw all through the boot standby (its dirty flag set),
and nothing of ours runs before it - that part is untouchable. Sony's own "power off" is `power_manage`
(`/data/power/*` = `/dev/shm/power`, `touch prepare_suspend`, `echo mem`), a suspend as well; the board has
no real halt, `shutdown -h now` (systemd, which unmounts `/media` cleanly first) reboots. **The USB bus is
reset by every resume** - hub, pad and stick re-enumerate within 2 s (the stick keeps its name, usually) -
and `power_manage` does not notice a suspend it did not start (`resume_count`/`usbreset_count` stay put).

So the launcher's **Power Off is Sony's power off with the stick unmounted** (verified on the console the
same day with `tools/psc_sleep_test.sh` before it was built): `App::requestPowerOff()` (the system menu's
item and the power button - `AutoBleem`'s constructor re-wires `Platform::setPowerOffHandler` on
`AB_PLATFORM_PSC`; every other build keeps `System::powerOff()`) sets `MENU_OPTION_POWEROFF` (7) and
`Input::requestQuit()` - poll() returns Quit on every call from then on, every screen's loop closes on
Quit, so the stack of screens unwinds and `AutoBleem::run()` leaves cleanly (databases closed, the scan
joined), "POWERING OFF... PLEASE WAIT" on the screen. `rc/boot.sh` is a loop now (`cd $RC; ./autobleem.sh;
cd /tmp; sh /tmp/selection.sh`), the udev rules file bind-mounted from `/tmp`, so nothing of ours is on the
stick while `selection.sh` (a copy on tmpfs) runs its `standby()`: `rm System/.session`, `umount /media`
(five tries; busy -> the holders into `System/Logs/standby.log` and a reboot), `abfatflag clean` when the
flag is ours (below), **green off, red on**, `echo mem`, and after the power button: green on, 3 s for
the bus, up to 30 s of `blkid` for the `SONY` partition, `mount` as usb_watch mounts it, `touch
System/.session`, exit 0 -> the launcher again - under the AutoBleem picture (`absplash` and
`splash/autobleem.jpg` copied to `/tmp` by boot.sh, shown from the resume until the launcher's
`display(false)` unlinks `/tmp/.abload`, as after RetroArch; the ten seconds were black and looked like a
console that did not start). No stick after 30 s -> reboot. The red LED alone is
"AutoBleem's standby" (the manual says so: the sign it works as intended). RetroArch (`AB_SELECTION=4`)
comes back through the same loop - `retroarch.sh` no longer re-runs `start.sh` nested.
**On the AutoBleem kernel** (2026-09-23, a tester's report: Power Off just restarted AutoBleem - then, with
the first fix, hung on a black screen with the green LED). The overlay's `/etc/autobleem/rndis` brings up a
USB network gadget (RNDIS) on the power port at every boot; `standby()` turns it off
(`/sys/class/android_usb/android0/enable`) and back on through the overlay's own `rndis restart` - **in the
background**, because its `start()` ends in `tcpsvd` (the FTP server), which stays in the foreground and
never returns. The gadget was not what refused the suspend, though: the kernel's own log (retests with the
tester, 2026-09-23) said `musb_bus_suspend: trying to suspend as a_host while active` / `Device usb1 failed
to suspend async: error -16` - the tester's stick sat on a hub in the **micro-USB (power) port**, which the
AutoBleem kernel runs as an OTG host (the stock kernel has no host mode there), and that host refuses
suspend-to-RAM while it serves a device. `shutdown -h now` (what 1.x did) only runs the drivers' shutdown
hooks, so nothing can refuse it. So: the write's result is checked, a refusal retried twice (logged to
`System/Logs/standby.log` with the wakelocks and the kernel's reason lines), and after the third
`poweroff_instead()` mounts the stick again (it never went away), appends the log, sets the red LED and
runs `shutdown -h now` - POWER is then a cold boot, not a quick wake. Confirmed by the tester the same
day, from the OTG hub and from a front port. **Never read `/sys/power/wakeup_count` in these scripts**: it
blocks while a wakeup event is in progress, which hung a diagnostic build on the red LED.
**The rear port after a wake** (2026-09-26, the owner's console on the pad-driver payload, WiFi and Bluetooth
dongles on a powered hub at the rear): MediaTek's musb driver does not restart its OTG host session after a
resume - the front bus came back in 2 s, the rear hub never did, so WiFi and Bluetooth were gone after every
wake. `standby()` notes whether the rear bus (found by its controller, `musb-hdrc.0.auto`) had a device before
the suspend; after the wake, if it is still missing 5 s in, it writes `idle` then `host` to
`/sys/devices/platform/mt_usb/swmode` (the glue's `musb_id_pin_sw_work`: VBUS, session, PHY) and the hub
re-enumerates within 2 s - before the stick's mount loop, so a stick on that hub comes back too. The stock
kernel, an empty rear port or a device that came back: nothing, no wait. Unbinding/rebinding the driver is
**not** a way: its probe cannot run twice (IRQ never freed, `probe ... failed with error -16`) and the port stays
dead until a reboot. Also: this kernel does not add the time spent suspended to the wall clock (a standby is
seconds in the logs), and after the wake the overlay's `rndis restart` restarts dropbear with a new host key.

**The dirty flag** (`ableem::FatDirtyFlag`, `lib_ableem/engine/fat_dirty_flag.*`, tested; the CLI
`abfatflag DEVICE [clean|dirty]` in `src/tools/`, shipped next to `absplash`): the boot sector byte at
0x41 (FAT32) / 0x25 (FAT12/16) bit 0 - what Linux's fat driver sets on an rw mount and clears on umount,
what Windows' "scan and fix" keys on - plus FAT[1]'s ClnShutBit on a clear, and exFAT's `VolumeFlags`
bit 1 (excluded from the boot checksum). **The kernel never clears a flag it found set at mount time**
(`fat_set_state`'s `sbi->dirty` gate; it says "Volume was not properly unmounted" and leaves it), so a
stick pulled once during the boot standby would stay dirty for ever. `rc/checkstick.sh` (boot.sh, before
the launcher, nothing open for writing yet): copies the tool to `/tmp`, and when `System/.session` is
absent - the previous session ended through the standby - does `remount,ro` (the kernel clears a flag
it owns right there), `abfatflag clean` if it is still dirty (then it is ours: `/tmp/ab_stick_owned`, and
`abfatflag dirty` after the `remount,rw` to keep "mounted rw = dirty" true on disk), and `touch
System/.session`. A session that ended any other way - the stick pulled while the launcher ran, a crash
- leaves the marker, the flag stays, and Windows gets to repair real damage. `standby()` clears an owned
flag after its umount and forgets the ownership after the fresh mount (the kernel owns it again).
Nothing in any of this writes to the console's own storage (the owner's rule: `/data` included).


## Fragment kept verbatim from CLAUDE.md pass 1 (task D19 pass 2 cleanup)

These two sentence-fragment lead-ins were left dangling in the launcher's `CLAUDE.md` by task D19's first
pass (their antecedents were in the text that pass 1 already moved here); moved here verbatim rather than
left attached to unrelated rule sentences:

day, from the OTG hub and from a front port.

kernel, an empty rear port or a device that came back: nothing, no wait.
