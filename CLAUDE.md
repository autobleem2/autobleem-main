# AutoBleem 2 - the whole project

AutoBleem is a game launcher for the **PlayStation Classic**: it replaces Sony's menu, plays PS1 games from a
USB stick in its own emulators, and other systems' games in RetroArch. AutoBleem 2 also runs as an
appliance on a **Raspberry Pi** and a **PC USB stick**, and as a **Windows** program. This repository is the
project's shared knowledge - how the pieces fit, the rules they follow, the plans and their history. Each
repository's own CLAUDE.md covers its code; read that one too when you work in it.

**Start here:** `tools/workspace.sh` clones every repository into this checkout (repos.txt); a session
started anywhere in the tree then reads this file as well as the repository's own. `docs/decisions.md` is
the owner's standing rules - read it before changing anything that crosses a repository.

## The repositories (github.com/autobleem2)

| repository | what it is | builds / publishes |
|---|---|---|
| `autobleem` | the launcher (EvolutionUI, the carousel, the classic screens), `src/tools/` (absplash, abfatflag, abupdate), the console's rc scripts and `payload/` skeleton, `payload_linux/`, `apps/abpad` (the virtual gamepad) | `launcher-<platform>-<v>.tar.gz` per platform, a rolling `nightly` release |
| `autobleem-core` | the shared SDK: `lib_ableem` (engine + SDL ui), `ab_core` (the SDL-free services), `ab_classic` (the classic UI), `ab_installer` (InstallerJob, WindowsInstallJob, FlasherJob) | a submodule - no artifacts of its own |
| `autobleem-console-tools` | PSC-Bios (WiFi, timezone, pad wizard) and ABFlashKit (the kernel flasher, carrying psc-kernel-payload's release) | `console-tools-psc-<v>.tar.gz` |
| `autobleem-pc-tools` | AutoBleemInstaller (the console's stick, per channel), AutoBleemFlasher (the PC stick image), AutoBleemWinSetup (the Windows product's data tree), UpdateRoms | `pc-tools-win64-<v>.zip` |
| `pcsx-ab`, `pcsx-abnxt`, `libpicofe` | the two PS1 emulators (the classic one and the next one) and the next one's front-end library | `pcsx-ab-*-<platform>.tar.gz`, `pcsx-abnxt-*-<platform>.tar.gz` |
| `retroarch-psc` | RetroArch built for the console, following upstream releases | `psc/retroarch/` on the site |
| `psc-kernel`, `psc-kernel-payload` | the console's 4.4 kernel and the AutoBleem kernel payload (Buildroot: boot.img + the rootfs overlay - WiFi, BlueZ, curl) | a payload release ABFlashKit ships |
| `autobleem-appliance` | **assembles** every platform from the components' releases - never compiles: the console stick package + installer zip, the Pi and PC-stick packages and images, the Windows product | the release's and the nightly's packages and images, on the site |
| `autobleem-build` | the Docker build image every component compiles in; the scheduled RetroArch/cores refresh for the site | `ghcr.io/autobleem2/autobleem-build:latest` |
| `autobleem-repo` | the download site: the page generator (`tools/repo_index.py`), `repo_publish.sh`, Caddy | `https://autobleem.retromenele.pl/` |
| `autobleem-themes`, `autobleem-samples`, `autobleem-manuals` | the extra themes, the sample-games pack, the user manuals | their packs on the site |

How they depend on each other: **core** -> the **launcher** and the **tools** (submodule) -> their releases +
the **emulators'** -> the **appliance** assembles -> the **site** publishes. A change to shared code is a
core commit, then a submodule bump in each consumer.

## Branches, versions, channels

- **develop** is every repository's default and where work lands; **master** (retroarch-psc: `main`) moves
  only with a release. A development build needs nothing from master.
- A **release** is one tag across the components (`v2.0.0-alpha2`); the appliance assembles that tag's
  component releases. A **nightly** is each component's rolling `nightly` release (its develop CI keeps it
  current, through autobleem-build's `nightly-release` action), assembled by the appliance's scheduled run
  into `nightly/<launcher's git describe>/` on the site.
- **Channels** - `release` (newest stable), `testing` (the one pre-release), `nightly` - are what the
  launcher's update, AutoBleemInstaller, AutoBleemFlasher and the Raspberry Pi Imager lists offer
  (`docs/history/online-update.md` has the details).

## CI and publishing

GitHub Actions in each repository, gated by the repository variable `AB_CI_ENABLED`; compiling runs in the
`autobleem-build` image on hosted runners, anything that needs the build server's disk (publishing to the
site, building images) on the org's self-hosted runner. `docs/ci-org-migration-plan.md` is the plan of the
move to this setup (its progress log is the record), `docs/ci.md` the operator's page for by-hand builds.
The site's page is generated, never stored - autobleem-repo's CLAUDE.md has its rules.

## Where to find things

| | |
|---|---|
| `docs/decisions.md` | the owner's standing rules, with reasons |
| `docs/infrastructure.md` | what runs where (the addresses are in the git-ignored `infrastructure.local.md`) |
| `docs/tester-checklist.md` | the hardware proofs, for testers |
| `docs/ci-org-migration-plan.md`, `docs/repo-split-*.md` | the org migration and the repository split |
| `docs/pc-targets-plan.md`, `docs/rpi-image-and-update-plan.md` | the PC targets and the Pi image plans |
| `docs/versioning.md`, `docs/licensing-plan.md` | the version scheme; the GPL-3.0 analysis |
| `docs/kernel-flash-recovery.md`, `docs/pi-install-guide.md` | recovering a console; installing on a Pi |
| `docs/history/*.md` | how each platform and the big features came to be (moved from the launcher's CLAUDE.md, 2026-09-23) |
| `docs/archive/` | superseded plans, kept for what they record |

When a plan is done, its last word goes into `docs/history/` (or the repository's CLAUDE.md) and the plan
moves to `docs/archive/`.
