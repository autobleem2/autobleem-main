# Volunteer test plans for AutoBleem v2.0.0-alpha1

**Testers: read the `.md` (on GitHub) or print the `.pdf`** - `psc`, `rpi`, `pcusb`, `win`. The `.yaml` files are
their source (the tester portal's format); `python3 tools/test_plan_docs.py testing/alpha1 --pdf` makes the `.md`
and `.pdf` from them again after a change - never edit those by hand.

One plan per platform, in the format of the tester portal plan (`docs/tester-portal-plan.md`): a list of
**sections** of about 10 minutes, each with a `needs` line (the start state), and steps `{id, do, expect}`.

| File | Platform | Sections | Minutes (all) |
|---|---|---|---|
| `psc.yaml` | PlayStation Classic (installer, stick, console) | 11 | 106 |
| `rpi.yaml` | Raspberry Pi 4 / 400, 32-bit and 64-bit image | 11 | 101 |
| `pcusb.yaml` | PC USB stick (flasher, boot, appliance) | 12 | 111 |
| `win.yaml` | Windows installer (AutoBleemSetup) | 10 | 91 |

Minutes are hands-on time. The Raspberry Pi and PC stick first boots (5-25 and about 8 minutes) run on their own
while you do something else.

## How sections are handed out

- A volunteer takes **one section**, not a whole plan. Read its `needs` line first: if you do not have that start
  state, take another section.
- Until the portal is running, sections are handed out by the maintainers (on the GitHub issues, see "How to
  report"): they give each volunteer the section of their platform that has the fewest passes so far.
- Target: **3 passes per section per platform per version**. Please do not take a section that already has three
  unless asked; a section you have started is yours for 48 hours, then it goes back.
- Sections are independent. Where one needs a state another produces (a game on the shelf, a Store download),
  the `needs` line says so.
- The steps follow the program's English names (menus, rows, buttons). Press the buttons of a pad; a USB keyboard
  stands in (arrow keys, Enter = Cross, Esc / Backspace = Circle, Tab = Triangle, Space = Square, F10 = system menu).
- Bring your own legally owned PS1 game. No game and no BIOS is shipped.

## How to answer a step

Each step has `status` and `comment`:

- `ok` - it did what `expect` says;
- `problem` - it did something else, or nothing: write what you saw, and whether it happens again, in `comment`;
- `na` - the step cannot be done on your setup (no RetroArch installed, no Bluetooth pad, ...).

A comment is also welcome on `ok` when a number is asked for (a time, a version, the text of the chip).

## How to report

Until the tester portal exists:

1. Copy the section you tested (its YAML block, or just the step ids with your status and comments) into a message.
2. Open a **GitHub issue** at https://github.com/autobleem2/autobleem-main/issues (title: the platform and the
   section id, e.g. `alpha1 rpi-install`) and paste it there, naming: the platform, the **version** (the chip under the pad battery plate, or L2 + R2 -> About), your device
   (Pi model and 32 / 64-bit, PC model and BIOS / UEFI, Windows version), and the section id.
3. For a `problem`: a photo of the screen helps. The logs are in `System/Logs/` on the stick / card / data folder
   (only written after a crash, unless Options -> Diagnostics -> Keep logs on the stick is ON; on a Pi or PC,
   Hardware Information -> Square saves them). Zip that folder and attach it only if you are happy to share it; it
   can contain Wi-Fi and game names.

Report only what you saw. A step that fails the same way twice is more useful than a guess about why.
