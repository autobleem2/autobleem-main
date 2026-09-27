# Known bugs

Everything known to be broken, whether or not a fix is approved yet. The approved work is
[`todo.md`](todo.md). This file lists defects. An entry here is **not** approval to fix it: only the owner adds todo
rows, and the `Fix` column links the row once one exists.

Whoever finds a bug records it here the same day: take the next free `BUG-N` and fill every column. One bug, one
entry. Search this file first, and mark a repeat `duplicate of BUG-N` rather than deleting it.

**Severity**:
- `blocker`: stops a release or makes a platform unusable;
- `major`: a feature does not work;
- `minor`: a cosmetic or workaround-able defect.

**State**:
- `open`: recorded, not yet reproduced.
- `confirmed`: reproduced, with the cause known or not.
- `fixing`: a todo row exists and someone is on it.
- `fixed-untested`: the fix is merged and waits for the device check.
- `closed`: verified on the device, or by the test that failed. QA (or that test) closes a bug; a developer never
  closes their own fix.
- `wontfix`, `duplicate`: only with the owner's word.

**Found** says where and when. **Fix** is the todo row, or `-` if none is approved.

| BUG | Title | Platform | Severity | State | Found | Fix |
|---|---|---|---|---|---|---|
| BUG-1 | A game starts by itself after leaving Options: presses made during "Applying settings..." stay queued and Cross starts the selected game | psc | major | fixed-untested | console session 318, block B3, 2026-09-27 | [CONSOLE-11](todo.md) |
| BUG-2 | PSC-Bios pad-mapping wizard: analog mapping does not work - moving a stick does nothing or maps something at random | psc | major | confirmed | console session 318, step A5.2, 2026-09-27 | [TOOLS-9](todo.md) |
| BUG-3 | PSC-Bios pad-mapping wizard: an input the pad does not have cannot be skipped and never times out, so the wizard cannot finish on such a pad | psc | major | confirmed | console session 318, block A5, 2026-09-27 | [TOOLS-9](todo.md) |
| BUG-4 | PSC-Bios pad-mapping wizard: holding Circle 2 s exits only from the pad being mapped, not from another pad | psc | minor | confirmed | console session 318, step A5.3, 2026-09-27 | [TOOLS-9](todo.md) |
| BUG-5 | PSC-Bios pad-mapping wizard: "Gamepad configuration changed" is a separate screen - it should be a popup on the same window | psc | minor | confirmed | console session 318, block A5, 2026-09-27 | [TOOLS-9](todo.md) |
| BUG-6 | The mouse pointer shows after a Bluetooth pad pairs or reconnects - the console's libinput (1.4) does not know `LIBINPUT_IGNORE_DEVICE`, so the no-pointer rule has no effect | psc | major | confirmed | console, 2026-09-26; cause found in console session 318, 2026-09-27 | [KERNEL-6](todo.md) |
| BUG-7 | Cancelling a Bluetooth pairing with Circle does not stop it - the pad finishes pairing a moment later | psc | minor | fixed-untested | console, 2026-09-26 | [KERNEL-7](todo.md) |
| BUG-8 | pcsx-abnxt: the low-battery icon of a wireless pad is not shown (a nearly empty DualSense over Bluetooth); on Select+Start it only flashes - drawn before the scaling and the scanlines, which cover it | psc | major | fixed-untested | console session 318, block B3, 2026-09-27 | [EMU-15](todo.md) |
| BUG-9 | pcsx-abnxt: in-game notices (`hud_msg`, FPS/CPU/SPU) are drawn into the frame before the scanlines, so the scanlines cover them | psc, rpi, pcusb, win | minor | fixing | console session 318, block B3, 2026-09-27 | [EMU-15](todo.md) |
| BUG-10 | PSC-Bios cannot pair pads on a Pi when Bluetooth is soft-blocked by rfkill: the adapter stays `off-blocked` and nothing scans or pairs | rpi | major | confirmed | Pi 400, 2026-09-27 | [TOOLS-10](todo.md) |
| BUG-11 | pcsx-ab: no "This PS1 emulator does not support swapping pads yet" notice when the swap is on and the emulator lacks `padorder` | psc | minor | wontfix | console session 318, step B3.5, 2026-09-27 (pcsx-ab is no longer developed) | - |
| BUG-12 | pcsx-ab: the Windows dev build crashes a moment after loading any state | win | major | wontfix | Windows dev build (pcsx-ab is no longer developed) | [EMU-8](todo.md) |
| BUG-13 | Pi 400: the pad is dead for 1-3 s after every game and at boot - a multi-mode pad re-enumerates when SDL's hidapi driver probes it | rpi | minor | confirmed | Pi 400 | - |
| BUG-14 | N64 in RetroArch: the homebrew RSP tests crash GLupeN64 inside the core; never tested with a real game | rpi, pcusb, win | minor | open | RetroArch core tests | [EMU-12](todo.md) |
| BUG-15 | Every extension-catalog scan line is written twice to `autobleem.log` | all | minor | wontfix | console session 318, 2026-09-27 (declined for now by the owner) | - |
