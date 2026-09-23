<!-- Moved from the launcher's CLAUDE.md (autobleem2/autobleem) on 2026-09-23 when the project's
     knowledge went to autobleem-main. Paths without a repository name are the launcher's. -->

# The online update

## Where it stands (2026-09-23)

The first version (below, 2026-09-20) was a Pi's alone, with two channels. What changed:

- **Three channels** everywhere: `release` (`releases/latest.json`, the newest stable tag), `testing`
  (`releases/unstable.json`, the one pre-release, else release's), `nightly` (`nightly/latest.json`, the
  newest development build, else testing's, else release's). config.ini `updates` = `release | testing |
  nightly | off`; the old `stable`/`latest` still read. The default follows the build: a stable tag ->
  release, a `-alpha/-beta/-rc/-pre` tag -> testing, a build between tags -> nightly.
- **The installed version is `Version::DESCRIBE`** - `git describe --tags --exclude nightly --match 'v*'` -
  exactly the site's folder name for a release (`v2.0.0-alpha2`) and a nightly (`v2.0.0-alpha2-17-g1760cc8`),
  so "different" means "an update" and an applied update is never offered again. The old
  `<VERSION>-<hash>` rule is gone.
- **Every platform with a way to apply it**: the Pi and the PC stick (`autobleem-update` -> `install.sh
  --update`), Windows (the downloaded `AutoBleemSetup-<v>.exe`, shown, `/RESTART`), and **the PlayStation
  Classic** (below). Options -> "Updates" is shown on all of them.
- **The console** (launcher `5b53dd6`): checked only with a network - `UpdateService::Config::networkUp` is
  `System::hasDefaultRoute()` (an up default route that is not the loopback in `/proc/net/route`), asked at
  most every 30 s, so a stock console (no network at all) is never probed or handed a download command; the
  AutoBleem kernel's WiFi (PSC-Bios sets it up) is what gives a console a route - its USB network to a PC
  does not. The key on the site is `psc-fs` (the stick package). The catalogs and the package come through
  `psc.ini`'s `update_download_command`, which is **`abfetch`** (`src/tools/abfetch`, `"%r/abfetch" ...`,
  `%r` = the launcher's folder): the launcher's own HTTP/1.1 client over a vendored mbedTLS 3.6 (TLS 1.2,
  the Mozilla CA bundle as `cacert.pem` next to it, redirects, a connect timeout and a stall timeout, a
  partial file removed). It replaced the kernel payload's curl the same day, on the owner's rule that the
  update must not depend on the payload: the AutoBleem 1.x kernel's overlay has no curl, and a payload
  release only reaches a console through ABFlashKit. A certificate's **validity dates are not checked** -
  the console has no battery-backed clock - while the chain, the signatures and the host name are, and the
  package is checked against the catalog's sha256 anyway. After "Update now" the launcher leaves with
  `MENU_OPTION_UPDATE`; `rc/selection.sh` copies `abupdate` (`src/tools/abupdate.cpp`), `abfetch` and
  `cacert.pem` to tmpfs and runs `abupdate` under the AutoBleem picture: autobleem-core's `InstallerJob`
  over the downloaded package - the PC installer's own update, the user's games, saves, settings, RetroArch
  and cover databases kept (UpdateRoms is fetched with the tmpfs `abfetch`) - then the new launcher starts.
  `System/Logs/update.log` is its record, with abupdate's exit status. **Proven on a PC** (2026-09-23, the
  Windows dev build on a `tools/make_usb.py` stick, `AB_UPDATE_PLATFORM=psc-fs` and the stick's `pc.ini` set
  as `psc.ini` is): the start-up check through `abfetch`, the prompt, the 62 MB nightly package downloaded
  and sha256-checked, `pending.json`, then `abupdate` - games, save states, memory cards and databases
  byte-identical, `config.ini`'s theme/language/channel kept, `System/Updates` removed. On a console:
  `docs/tester-checklist.md`, section 3. (Two things the PC run showed: `InstallerJob` calls a stick an
  update only when `Autobleem/bin/autobleem/autobleem-gui` exists - true on every console stick, not on a
  PC-staged one with only the `.exe` - and a nightly's UpdateRoms comes from the testing release.)
- **The installers take the same channels**: AutoBleemInstaller downloads the stick package of the channel
  picked in it (no package in its zip any more, no offline fallback), AutoBleemFlasher the PC stick image
  (`pc/images/{release,testing}.json`, `nightly/latest.json`'s `pc-i386`), Raspberry Pi Imager one list per
  channel (`rpi-imager/os_list{,-testing,-nightly}.json`).
- **Proofs** are the testers': `docs/tester-checklist.md`.

## The first version (2026-09-20, a Pi and the dev hosts)

*History: this section is how the update was first built. Its console paragraph no longer holds - since
launcher `5b53dd6` (2026-09-23) the update is compiled into the console build too; see "Where it stands"
above.*

The launcher keeps itself current from the download repository, the way the owner asked: **check at
start and once a day, say so, ask, and on a yes fetch everything and re-run the installer with the
first-boot screen**. At the time the console had no network and updated from a stick, so none of this was
compiled into the console build: the CMake option `AB_ONLINE_UPDATE` (on by default) was switched off in
the PSC branch of the root CMakeLists (it no longer is), and every hook in the launcher sits behind
`#ifdef AB_ONLINE_UPDATE`.

- **`UpdateService`** (`core/services/update_service.*`, `App::updates()`, configured by
  `App::applyUpdateSetting()` at start and after Options): a worker thread fetches
  `releases/unstable.json` (the "latest" channel - the one pre-release; falls back to `latest.json`
  when there is none) or `releases/latest.json` ("stable") plus `rpi/retroarch/latest.json` through the
  platform's `download_command`, and `compare()` calls a version that is not the installed one an update
  - the site keeps one pre-release, so different is newer; AutoBleem's installed version is
  `Version::VERSION-GIT_HASH` on the latest channel, the tag alone on stable; RetroArch's is the
  `/usr/local/share/autobleem/retroarch.version` stamp (no stamp = not checked). `checkDue()` is once
  per `CheckInterval` (24 h) with `System/update.json` remembering the last check, the postponement and
  the skipped versions (`ableem::UpdateState`). `startDownload()` fetches each tarball into
  `System/Updates/` with the platform's **`update_download_command`** (no short timeout - `rpi.ini`,
  `pc.ini`; `repo_url` next to it, both new `PlatformConfig` keys -> `Env::repoUrl()` /
  `updateDownloadCommand()`), checks it with the new engine **`ableem::Sha256`** against the catalog,
  and writes `pending.json` (`ableem::PendingUpdate`) for the Pi. Progress is the `.part` file's size.
  The JSON side lives in the engine (`engine/update_catalog.*`: `ReleaseCatalog`, `RetroArchCatalog`,
  `UpdateState`, `PendingUpdate`) - the app includes no JSON library. Tested in
  `tests/core/test_update_service.cpp` against a fake site.
- **Options -> "Updates"**: `stable` | `latest` | `off` (config.ini `updates`; the default follows the
  build - a `-pre` version takes `latest`). **Shown on a Pi only** for now (the owner's call).
- **The screens** (`evoui/screens/evoui_update.*`): `GuiUpdatePrompt` - "Update available", the
  versions and sizes, *Update now / Remind me tomorrow / Skip this version* (Circle = later);
  `GuiUpdateProgress` - the check, the download bar, the outcome. `GuiLauncher::pollUpdates()` (once a
  frame, next to the scan poll) raises the prompt when a check lands with something not skipped or
  postponed; the L2+R2 menu's **"Software Update"** item (`loop_softwareUpdate()`) checks on the spot.
  `offerUpdate()` runs the download and then, on a Pi, leaves the launcher with the new
  **`MENU_OPTION_UPDATE` (6)** in `autobleem_cfg.sh`; a dev host stops at a "downloaded into
  System/Updates" message (try it with `AB_UPDATE_PLATFORM=rpi` and `AB_UPDATE_RETROARCH_VERSION=...` in
  the environment - verified on the PC against the live site: prompt, 48 MB download, pending.json).
- **The Pi's apply step**: `autobleem-session.sh` sees `AB_SELECTION=6` and runs
  **`autobleem-update`** (`payload_linux/system/autobleem-update.sh`, installed to `/usr/local/bin` by
  `install.sh`'s `install_update_helper()` together with the first-boot screen, its splash and a copy
  of the installer under `/usr/local/share/autobleem/`): it unpacks the new package and runs its
  **`install.sh --update`** (`--yes`, RetroArch `prebuilt` only where the stamp says one is installed,
  nothing repartitioned, everything already there kept - config.ini, cores, BIOS, samples - and the
  initramfs not rebuilt when the splash files are unchanged) piped through the progress screen on
  tty1, with **`--retroarch-tarball`** pointing at the pre-downloaded build (a RetroArch-only update
  uses the installed release's installer copy). Success removes `System/Updates`; the session loop then
  starts the new launcher. Log: `System/Logs/update.log`. **The first real update (2026-09-20, the Pi
  400 on the `a84b8b4` image -> `6338ac9`)**: the check, the prompt and the 43 MB download all worked;
  the apply step died in one second at `tar` - the helper staged the package on the exFAT data
  partition, and tar run as root restores the archive's uid/gid, which exFAT refuses ("Cannot change
  ownership ... Operation not permitted", exit 2). The stage is `/var/tmp/autobleem-update` on the root
  filesystem now, with `--no-same-owner`. And **an installed launcher's first start after an update
  rescans** (the owner's rule): `install_payload()` removes `games.fingerprint`/`roms.fingerprint`. Nothing on the screen said why: the launcher had left, the
  helper's failure message is a 6 s dialog on tty1 and the session loop restarted the launcher - so
  read `update.log` first when an update "does nothing".

