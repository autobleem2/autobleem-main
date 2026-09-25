# The online update

How the launcher checks for, downloads and applies an update on every platform. Paths without a repository
name are the launcher's.

## Channels and versions

- Three channels: `release` (`releases/latest.json`, the newest stable tag), `testing`
  (`releases/unstable.json`, the one pre-release, else release's), `nightly` (`nightly/latest.json`, else
  testing's, else release's). config.ini `updates` = `release | testing | nightly | off` (the old
  `stable`/`latest` still read). The default follows the build: a stable tag -> release, an
  `-alpha/-beta/-rc/-pre` tag -> testing, a build between tags -> nightly.
- **The installed version is `Env::productVersion()`**: the package's `VERSION` file (a nightly is named
  `<launcher describe>-n<fingerprint>`), the same string the site uses for the folder. Different means an
  update, so an applied update is never offered again. See `docs/versioning.md`.
- The installers take the same channels: AutoBleemInstaller (the stick package of the chosen channel, no
  offline fallback), AutoBleemFlasher (the PC stick image), Raspberry Pi Imager (one list per channel).

## The launcher side

- **`UpdateService`** (`core/services/update_service.*`, `App::updates()`): a worker thread fetches the
  catalogs through the platform's `download_command` and compares versions; RetroArch's installed version on
  a Pi/PC stick is the `/usr/local/share/autobleem/retroarch.version` stamp (no stamp = not checked).
  `checkDue()` is once per 24 h; `System/update.json` (`ableem::UpdateState`) remembers the last check, the
  postponement and skipped versions. `startDownload()` fetches into `System/Updates/` with
  **`update_download_command`** (no short timeout), checks `ableem::Sha256` against the catalog and writes
  `pending.json`. The JSON lives in the engine (`engine/update_catalog.*`). Tested in
  `tests/core/test_update_service.cpp` against a fake site.
- **Screens** (`evoui/screens/evoui_update.*`): `GuiUpdatePrompt` (*Update now / Remind me tomorrow / Skip
  this version*) raised by `GuiLauncher::pollUpdates()`, and `GuiUpdateProgress`; the L2+R2 menu's
  **Software Update** checks on the spot. After the download the launcher leaves with
  **`MENU_OPTION_UPDATE` (6)**. A dev host stops at "downloaded"; try it with `AB_UPDATE_PLATFORM=...`.
- Options -> "Updates" is shown on every platform.

## Applying it, per platform

- **Pi and PC stick**: `autobleem-session.sh` sees `AB_SELECTION=6` and runs `autobleem-update`
  (`payload_linux/system/autobleem-update.sh`): unpacks the package and runs its `install.sh --update`
  through the progress screen (the one chosen at first boot, `/etc/autobleem/installer-ui`), with
  `--retroarch-tarball` for a pre-downloaded RetroArch. Nothing repartitioned, the user's things kept.
  **The stage is `/var/tmp/autobleem-update` on the root, extracted with `--no-same-owner`**: tar as root
  restores uid/gid, which exFAT refuses.
- **Windows**: the downloaded `AutoBleemSetup-<v>.exe` started detached with `/S /RESTART` (see
  `windows-product.md`).
- **The console**: checked only with a network - `System::hasDefaultRoute()` (a non-loopback default route
  in `/proc/net/route`, asked at most every 30 s), so a stock console is never probed; the AutoBleem
  kernel's WiFi gives it one, its USB network to a PC does not. The site key is `psc-fs`.
  `rc/selection.sh` copies `abupdate`, `abfetch` and `cacert.pem` to tmpfs and runs `abupdate` under the
  AutoBleem picture: core's `InstallerJob` over the package (games, saves, settings, RetroArch, cover
  databases kept), then the new launcher starts. `InstallerJob` treats a stick as an update only when
  `Autobleem/bin/autobleem/autobleem-gui` exists.
- **`abfetch`** (`src/tools/abfetch`) is the console's HTTP client: HTTP/1.1 over vendored mbedTLS 3.6,
  TLS 1.2, `cacert.pem` next to it, redirects, connect and stall timeouts, a partial file removed. The
  update must not depend on the kernel payload (1.x's overlay has no curl). **Certificate validity dates are
  not checked** (no battery clock); chain, signatures and host name are, and the package's sha256 is checked
  against the catalog.
- **An installed launcher's first start after an update rescans** (the owner's rule): the installer removes
  `games.fingerprint`/`roms.fingerprint`.
- The record is `System/Logs/update.log` (with abupdate's exit status). **Read it first when an update
  "does nothing"** - a failed apply shows only a short dialog before the launcher restarts.

## Still open

- The console update has been proven on a PC-staged stick only; the run on a console is
  `docs/tester-checklist.md` section 3.
