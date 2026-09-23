# What is left (2026-09-23)

Everything still open from the finished plans (`docs/archive/`) and the open ones, in one list. Strike an
item when it is done and delete it at the next cleanup; a new piece of work that needs more than a line gets
its own plan in `docs/` (see `CLAUDE.md`, "Where to find things").

## The owner's decisions and setup

- **Masters before the first `release`**: some masters carry CI commits that never went through a release
  (`decisions.md`). Reset them to their last release, or let the first release's merge bring develop's
  history in as it is.
- **Code signing through SignPath** (`docs/code-signing.md`): apply to SignPath Foundation, publish the code
  signing policy (check the privacy statement against the update check and the online downloads), set up the
  five SignPath projects, then the org variable `SIGNPATH_ORGANIZATION_ID` and secret `SIGNPATH_API_TOKEN`.
  The CI is wired and ships unsigned until then.
- **Telegram for the admin panel**: a bot and a chat id into the server's `admin/.env`
  (`AB_TELEGRAM_TOKEN`, `AB_TELEGRAM_CHAT`), then restart the panel (autobleem-repo `admin/README.md`, step 3).
- **Tier-2 repositories** - `amiberry-psc`, `openbor-psc`, `autobleem-themes-pack`, `autobleem-gameports-pack`
  under `screemerpl`: move them into `autobleem2`, or leave them as the Apps pack's personal sources.
- **Licensing leftovers** (`archive/licensing-plan.md`): Nihilore's terms for the music track (step 6); a note
  from Axanar and cornelk that their contributions are GPLv3 (step 7, optional).
- **Atari VCS 800**: the one on-hardware test that decides the port's shape (the launcher's
  `docs/atari-vcs-plan.md`) - for the tester with a unit.

## Testers

- **`docs/tester-checklist.md`** - the flasher, the installer's channel box, the console, the Pi, the PC
  stick and Windows updating themselves, the Imager lists, the download page.
- **The PC stick beyond the BIOS VM**: 32- and 64-bit UEFI and real hardware, with a pad.

## Engineering

- **The virtual gamepad on a console** (the launcher's `docs/virtual-gamepad-plan.md`, step 9): compile
  `abpad` with the console toolchain and run an App through it on a console. Then step 8, a launcher page
  showing which pads the daemon sees; keyboard mode (step 5) is written and never exercised.
- **The manuals**: the update and install sections for the channels - Options -> Updates, the console
  updating itself, AutoBleemInstaller's channel box, AutoBleemFlasher (autobleem-manuals, all languages).
- **The launcher's stale `docker/`**: autobleem-build is the image's one source. Remove the copy once nothing
  in the launcher (`ci/build.sh`, `test.yml`, the docs) calls its `run.sh`.
- **`payload_linux/` exists twice** - the launcher's (edited) and autobleem-appliance's (what the packages
  are assembled from). They had drifted: the appliance's lacked the virtual gamepad's `rc/app_env.sh` and
  `pad.default.ini` until 2026-09-23. Keep one - the appliance's, the launcher's removed - or have the
  launcher's tarball carry it.
- Optional hardening: pin the `actions/*` to commit hashes, Dependabot for the workflows.

## Later (ideas, not planned)

- The admin panel's second version: release notes drafted from the commits, the tester checklist's
  pass/fail per build.
- A Pi update without a network: a package dropped on the data partition, applied at the next boot
  (`archive/rpi-image-and-update-plan.md`, Part 1, entry point 2).
- Game Manager: "Move to folder..." - after the Game Manager's rework (`archive/legacy-1x-analysis.md`, item 6).
- The virtual gamepad through uinput (non-SDL and static apps), and `Apps/` on the Pi and the PC stick.
- The launcher's `docs/IDEAS.md`.
