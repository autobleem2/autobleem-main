# The move to the `autobleem2` org, public, with GitHub-Actions CI

Archived plan (done 2026-09-23). The full text is in git history: `git log -- docs/archive/ci-org-migration-plan.md`.

## What was decided, and why

- **One new org, `autobleem2`, every build input in it, all public GPL-3.0-or-later.** Public repositories
  get unlimited hosted-runner minutes, so compiling moved off the 2-core build server onto parallel
  `ubuntu-24.04` runners; the server's self-hosted runner only does what must touch its disk (publishing
  to the site, the image build's cache, the appliance's image job). It absorbed the earlier "go public in
  `autobleem`" plan (deleted).
- **Transfer, not re-create**: GitHub's transfer keeps history, issues and permanent redirects, so old
  clones and URLs kept working through the cutover. Renames: `AutoBleem2` -> `autobleem` (the org carries
  the "2"), `pcsx-ab2` -> `pcsx-ab`; `pcsx-abnxt`, `libpicofe`, `retroarch-psc`, `psc-kernel-payload` kept
  their names.
- **`psc-kernel` is a real build input** (the plan first listed it as history): `psc-kernel-payload` builds
  the MT8167 4.4.22 vendor kernel from it, and the `boot.img` we publish owes GPL-2 source. It moved to
  `autobleem2/psc-kernel` (public, the gcc >= 10 fixes from the server's checkout pushed) and is a submodule
  of the payload. `psc-bluez` is not an input (upstream BlueZ is built) and stayed private under `screemerpl`.
- **develop is the default branch everywhere**; master (`main`) moves only with a release. Dev builds take
  nothing from master: `nightly-release@develop`, the image's `:develop` tag, retroarch-psc's upstream job
  on develop. Masters that carried unreleased CI commits were left as they were (the owner's call).
  pcsx-abnxt keeps upstream notaz in an `upstream` branch; the fork's own upstream workflows are disabled.
- **Pull requests always run on hosted runners** (a self-hosted runner must never run a fork's code), and
  every workflow is gated by the repository variable `AB_CI_ENABLED`.

## The two CI bugs the pcsx-ab pilot found (fix them in every new repo)

1. **Script modes**: shell scripts committed from Windows as `100644` - `ci/build.sh` failed with
   "Permission denied" on Linux. Commit them `100755` (`git update-index --chmod=+x`).
2. **sccache's GHA backend** calls the retired v1 artifact-cache API and fails every build ("services
   aren't available"). Use a local `SCCACHE_DIR` persisted by `actions/cache` keyed per target instead - a
   miss is a cold compile, never a failure.

## What was built

- Each component has its own gated workflow and publishes its packages to its GitHub Releases on a `v*`
  tag (hyphenated tags = pre-releases); actions pinned to their node24 majors. The emulators' Windows build
  runs natively on `windows-latest` with MSYS2 - the first CI Windows build the project had.
- **Channels**, one step each: autobleem-repo stopped carrying packages between pre-releases (a file whose
  name carries another version is not the release's); `Version::DESCRIBE` (`git describe --tags --exclude
  nightly`) is the site's folder name and what the update check compares; `UpdateService` takes
  `release | testing | nightly | off` (config.ini `updates`, default from the build's tag, old values
  migrated); the stick install/update logic moved into core (`ab_installer`: `InstallerJob`,
  `WindowsInstallJob`, `FlasherJob`); AutoBleemInstaller got a channel box; `AutoBleemFlasher` writes the PC
  stick image on Windows (admin rights - the one exception to per-user); the console updates itself when it
  has a default route (curl from psc-kernel-payload, `abupdate` from `rc/selection.sh`).
- **Development builds**: each component's develop CI keeps a rolling `nightly` pre-release
  (autobleem-build's `nightly-release` action); autobleem-appliance's `assemble.yml` assembles the nightly
  at 03:17 UTC from them and publishes `nightly/<version>/`, skipping a night when `sources.json` shows no
  component changed.
- The project-wide knowledge moved into this repository (autobleem-main) the same day.

## Still open

- The manuals' update and install sections for the channels (Options -> Updates, the console updating
  itself, AutoBleemInstaller's channel box, AutoBleemFlasher).
- The hardware/VM proofs went to testers (`docs/tester-checklist.md`): a Pi and the PC stick updating from
  an appliance-built package, a Windows self-update against the testing channel, a flasher-written stick.
- A nightly whose launcher did not change keeps the launcher's describe as its folder name, so an installed
  nightly sees no update when only an emulator changed (name the folder by date + hash, or compare
  `sources.json`).
- Masters carrying unreleased CI commits: reset them before the first `release`, or let its merge bring
  develop in.
- Optional hardening: SHA-pin `actions/*`, Dependabot for workflow actions.
