# What is left (2026-09-25)

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
- **Licensing leftovers** (`archive/licensing-plan.md`): Nihilore's terms for the music track (step 6); a note
  from Axanar and cornelk that their contributions are GPLv3 (step 7, optional).
- **Atari VCS 800**: the one on-hardware test that decides the port's shape (the launcher's
  `docs/atari-vcs-plan.md`) - for the tester with a unit.

## Testers

- **`docs/tester-checklist.md`** - the flasher, the installer's channel box, the console, the Pi, the PC
  stick and Windows updating themselves, the Imager lists, the download page.
- **A Pi updating itself to the refreshed nightly** (`docs/tester-checklist.md` section 4; appliance run
  36078337098, 2026-09-25): `v2.0.0-alpha2-149-g4edd7b0-n4ac996` is on the nightly channel - a Pi 400 on an
  older nightly, 32-bit and 64-bit, offered it, updated, games and settings kept. The same build is the
  nightly sections 10 and 11 were waiting for.
- **The PC stick beyond the BIOS VM**: 32- and 64-bit UEFI and real hardware, with a pad.
- **The AutoBleem Store on hardware** (the launcher's `docs/store-plan.md`, step 8 - a TODO, the owner
  2026-09-25): the console on the AutoBleem kernel's WiFi (an App from the catalog - the eight console Apps
  are there since 2026-09-25 - a two-disc game from a TSV source, a download resumed after a standby), the
  Pi 400, the PC stick, Windows.
- **Scanner processors on hardware** (the launcher's `docs/scanner-processors-plan.md`; the owner tests
  later, 2026-09-25): `docs/tester-checklist.md` section 11 - proc_unzip on the console and a Pi, stopped by a
  game and finished by the next scan, the new folders from the installers.
- **LAN Share's disc reading on hardware** (autobleem-pc-tools `docs/lan-share-plan.md`, step 7 - a TODO, the
  owner 2026-09-25; the first disc, RE3 PAL, read bit-perfect): a multi-disc game, a game with CD audio
  tracks, a LibCrypt game (PAL, needs a drive that gives the subchannel), each published to a Pi's abstored
  and installed through the Store on the Pi 400 and the console.

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
  - the third-party Apps ported from source, one `app_<name>` repository each (`decisions.md`, "Third-party
    App ports"), in this order: OpenTyrian, SDLPoP, Crispy Doom (shareware and Freedoom), Wolf4SDL, JFSW,
    EDuke32, OpenBOR, Amiberry. Each replaces the RetroBoot binary in the psc catalog.
- **The themes pack** (`screemerpl/autobleem-themes-pack`, archived): 51 community themes in the old
  format, with Sony's SST fonts and firmware images, franchise art and commercial music. A plan of its own,
  later (the owner, 2026-09-25).
- **Extensions** (the launcher's `docs/extensions-plan.md`). The plugin mechanism, the SDK side, the
  Extensions list and `hello` are in `develop` (2026-09-24), proven on Windows, Linux x86_64 and the Pi 400
  (the Store), built for every target; `hello` is built for dev hosts only. PSC-Bios is a bundled extension
  on the console. Left:
  - a console running the Store (the tester checklist);
  - the Windows *product* with a plugin (it links libstdc++ statically);
  - the curated SDK surface with its export list;
  - the ABI check in CI;
  - the SDK package, so an `ext_<name>` repository can build without the launcher's tree.
- **The AutoBleem Store** (the launcher's `docs/store-plan.md`, `autobleem2/ext_store`). Tested on the Pi 400
  (2026-09-24): the public catalog (the Terminal App, published from app_terminal's v1.0.0), a LAN source
  served by `abstored` (ext_store/server, any Linux; the Pi runs one from its crontab), covers from our covers
  databases, sources renamed/moved/switched http-https, the new keyboard. The site shows it at `/store/`; the
  manuals (English, Polish) have its section. Since 2026-09-25: its own CI (the Store for every target and
  abstored, a nightly, the site's Store page), the eight console Apps in the psc catalog (`pack_psc_apps.py
  --per-app`), and LAN Share (autobleem-pc-tools, done: the Windows app that publishes games and read discs to
  an abstored, and removes them; on the Store page). Left:
  - on hardware - see Testers above;
  - more Apps, one by one (each a porting session of its own - the `app_<name>` ports above);
  - the TSV format written up for source owners;
  - the other manual languages when they come.
- **Scanner processors - next** (the launcher's `docs/scanner-processors-next-plan.md`, the owner
  2026-09-25: later, after the hardware pass): `proc_unzip`'s first release (a `v*` tag; `.7z` and `.rar` went
  in as 1.1.0 on 2026-09-25), processors as a Store item kind, launch-time processors, signatures or a
  trusted list, and a `Heavy=` flag if the console's heavy jobs call for one.
- Optional hardening: pin the `actions/*` to commit hashes, Dependabot for the workflows.

## Later (ideas, not planned)

- The admin panel's second version: release notes drafted from the commits, the tester checklist's
  pass/fail per build.
- A Pi update without a network: a package dropped on the data partition, applied at the next boot
  (`archive/rpi-image-and-update-plan.md`, Part 1, entry point 2).
- Game Manager: "Move to folder..." - after the Game Manager's rework (`archive/legacy-1x-analysis.md`, item 6).
- The virtual gamepad through uinput (non-SDL and static apps), and `Apps/` on the Pi and the PC stick.
- The launcher's `docs/IDEAS.md`.
