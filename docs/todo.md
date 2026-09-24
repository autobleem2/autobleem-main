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
  five SignPath projects, then the org variable `SIGNPATH_ORGANIZATION_ID` and secret `SIGNPATH_API_TOKEN`,
  and last each repository's switch `AB_SIGNING_ENABLED=true`. Parked (the owner, 2026-09-24): the CI is
  wired and switched off, and ships unsigned until then.
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
- **The download page's PS1 emulators tab has no channels** (the owner asked, 2026-09-24 - "later"): it shows
  one build per emulator (today v2.0.0-alpha2), never a nightly. Two causes: pcsx-ab's and pcsx-abnxt's
  `build.yml` `publish` job runs only for a `v*` tag or a manual run with `publish` (a develop push reaches
  only the repository's GitHub `nightly` pre-release), and autobleem-repo's `index_pcsx()` keeps the newest
  version in `emu/<name>/` and deletes the rest. Fix: publish develop pushes too (e.g.
  `emu/<name>/nightly/<version>/`), keep the newest per channel (release / testing / nightly) with a catalog
  each next to `latest.json`, and draw the panel with the channel pills the other tabs use.
- **Multi-platform Apps** (the launcher's `docs/app-format-plan.md`). The format, `AppManifest`, the launcher
  and the three rc scripts are in `develop` (2026-09-24). Left:
  - the Windows product's `Apps/` folder;
  - the eight console Apps converted to `bin/psc/` (the owner's `F:/Apps`; `pack_psc_apps.py --per-app`
    packs them for the Store as they are);
  - OpenTyrian built for every target (the tier-2 App repositories, `app_<name>`).
- **Extensions** (the launcher's `docs/extensions-plan.md`). The plugin mechanism, the SDK side, the
  Extensions list and `hello` are in `develop` (2026-09-24), proven on Windows and Linux x86_64 and built
  for every target. Left:
  - a console and a Pi running `hello` and the Store (the tester checklist);
  - the Windows *product* with a plugin (it links libstdc++ statically);
  - the curated SDK surface with its export list;
  - the ABI check in CI;
  - the SDK package, so an `ext_<name>` repository can build without the launcher's tree.
- **The AutoBleem Store** (the launcher's `docs/store-plan.md`). It works on the Windows dev build (an App
  and a game installed from a local test site). It is kept in a local repository until
  **`autobleem2/ext_store` is created (the owner's step)**. The site's side (`store/<platform>/catalog.json`,
  `repo_publish.sh store`) is on autobleem-repo's `feature/extensions`. Left:
  - the first items published;
  - Apps for the other targets;
  - hardware;
  - the manuals.
- Optional hardening: pin the `actions/*` to commit hashes, Dependabot for the workflows.

## Later (ideas, not planned)

- The admin panel's second version: release notes drafted from the commits, the tester checklist's
  pass/fail per build.
- A Pi update without a network: a package dropped on the data partition, applied at the next boot
  (`archive/rpi-image-and-update-plan.md`, Part 1, entry point 2).
- Game Manager: "Move to folder..." - after the Game Manager's rework (`archive/legacy-1x-analysis.md`, item 6).
- The virtual gamepad through uinput (non-SDL and static apps), and `Apps/` on the Pi and the PC stick.
- The launcher's `docs/IDEAS.md`.
