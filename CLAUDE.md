# AutoBleem 2 - the whole project

AutoBleem is a game launcher for the **PlayStation Classic**: it replaces Sony's menu, plays PS1 games from a
USB stick in its own emulators, and other systems' games in RetroArch. AutoBleem 2 also runs as an
appliance on a **Raspberry Pi** and a **PC USB stick**, and as a **Windows** program. This repository is the
project's **main source of knowledge** - how the pieces fit, the rules they follow, what is left and in
which order, and the history. Each repository's own CLAUDE.md covers its code; read that one too when you
work in it.

**Start here:** `tools/workspace.sh` clones every repository into this checkout (`repos.txt`); a session
started anywhere in the tree then reads this file as well as the repository's own. `docs/decisions.md` is
the owner's standing rules - read it before changing anything that crosses a repository. **`docs/roadmap.md`
is what to work on next.**

## The repositories (github.com/autobleem2)

| repository | what it is | builds / publishes |
|---|---|---|
| `autobleem` | the launcher (EvolutionUI, the carousel, the classic screens), `src/tools/` (absplash, abfatflag, abupdate, abfetch), the console's rc scripts and `payload/` skeleton, `apps/abpad` (the virtual gamepad) | `launcher-<platform>-<v>.tar.gz` per platform, a rolling `nightly` release |
| `autobleem-core` | the shared SDK: `lib_ableem` (engine + SDL ui), `ab_core` (the SDL-free services), `ab_classic` (the classic UI), `ab_installer` (InstallerJob, WindowsInstallJob, FlasherJob) | a submodule of the launcher and the tools - no artifacts, no tags yet |
| `autobleem-console-tools` | PSC-Bios (WiFi, Bluetooth pads, timezone, pad wizard - an extension, `Extensions/pscbios/`) and ABFlashKit (the kernel flasher, an App carrying psc-kernel-payload's release) | `console-tools-psc-<v>.tar.gz` |
| `autobleem-pc-tools` | AutoBleemInstaller (the console's stick, per channel), AutoBleemFlasher (the PC stick image), AutoBleemWinSetup (the Windows product's data tree), UpdateRoms, LAN Share (publishes games and read discs to an abstored), LastResortRecovery (fastboot recovery) | `pc-tools-win64-<v>.zip` |
| `ext_store` | the AutoBleem Store, the first extension, bundled with every platform's package; `server/` is `abstored`, a LAN catalog server | a rolling `nightly` (no `v*` release yet) |
| `proc_unzip`, `proc_template` | the first scanner processor (zip, 7z, rar - bundled with every package) and the skeleton to copy | `unzip-<v>.zip`, a rolling `nightly` (no `v*` release yet) |
| `app_*` | the Apps: `app_terminal` (ours) and eight source ports - OpenTyrian, SDLPoP, Crispy Doom, Wolf4SDL, JFSW, JFDuke3D, OpenBOR, Amiberry (`docs/app-ports.md`) | `v<upstream>-<n>` releases, published to the Store catalogs |
| `pcsx-ab`, `pcsx-abnxt`, `libpicofe` | the two PS1 emulators (the classic one and the next one - the default) and the next one's front-end library (`docs/emulator-contract.md`) | `pcsx-ab-*-<platform>.tar.gz`, `pcsx-abnxt-*-<platform>.tar.gz` |
| `retroarch-psc` | RetroArch built for the console, following upstream releases | `psc/retroarch/` on the site |
| `psc-kernel`, `psc-kernel-payload` | the console's 4.4 kernel and the AutoBleem kernel payload (Buildroot: boot.img + the rootfs overlay - WiFi, BlueZ, curl, the pad drivers) | a payload release ABFlashKit ships |
| `autobleem-appliance` | **assembles** every platform from the components' releases - never compiles: the console stick package + installer zip, the Pi and PC-stick packages and images, the Windows product | the release's and the nightly's packages and images, on the site |
| `autobleem-build` | the Docker build image every component compiles in; the scheduled RetroArch/cores refresh for the site | `ghcr.io/autobleem2/autobleem-build:develop` (develop builds) and `:latest` (releases, from its master) |
| `autobleem-repo` | the download site: the page generator (`tools/repo_index.py`), `repo_publish.sh`, Caddy, the admin panel | `https://autobleem.retromenele.pl/` |
| `autobleem-themes`, `autobleem-samples`, `autobleem-manuals` | the extra themes, the sample-games pack, the user manuals - the first two hold stale copies of what the launcher owns, and the manuals exist twice (todo D4-D6) | their packs on the site |

How they depend on each other: **core** -> the **launcher** and the **tools** (submodule) -> their releases +
the **emulators'** + the **Store**, **Unzip** -> the **appliance** assembles -> the **site** publishes. A
change to shared code is a core commit, then a submodule bump in each consumer.

## Branches, versions, channels

- **develop** is every repository's default and where work lands; **master** (retroarch-psc: `main`) moves
  only with a release (psc-kernel is the exception today - todo K6).
- A **release** is one tag across the components (`v2.0.0-alpha3`), made by `tools/release.py promote`
  (`.github/workflows/promote.yml`); the appliance assembles that tag's component releases. A **nightly** is
  each component's rolling `nightly` release, assembled every night into `nightly/<launcher describe>-n<fp>/`
  on the site. Every program shows the **package's** version. All in `docs/versioning.md`.
- **Channels** - `release` (newest stable; none yet), `testing` (the one pre-release, `v2.0.0-alpha2`),
  `nightly` - are what the launcher's update, AutoBleemInstaller, AutoBleemFlasher and the Raspberry Pi
  Imager lists offer.

## CI and publishing

GitHub Actions in each repository, gated by the repository variable `AB_CI_ENABLED`; compiling runs in the
`autobleem-build` image on hosted runners, anything that needs the build server's disk (publishing to the
site, building images) on the org's self-hosted runner. `docs/ci.md` lists every workflow;
`docs/history/ci-and-site.md` is how it came to be. The build server's disk is kept clear by autobleem-repo's
nightly `cleanup.yml`; the admin panel (`/admin/` on the site) shows and starts builds. The site's page is
generated, never stored - autobleem-repo's CLAUDE.md has its rules.

## Where to find things

| | |
|---|---|
| **`docs/roadmap.md`** | **where we are, the milestones and the alpha releases, in tables** |
| **`docs/todo.md`** | **what is left** - every open item of every repository, one table row each with an ID; no repository keeps its own list |
| `docs/ideas.md` | ideas nobody has committed to |
| `docs/decisions.md` | the owner's standing rules, with reasons |
| `docs/console.md` | the PlayStation Classic as a platform: hardware, the stick layout, the boot chain, standby, the dirty flag, debugging |
| `docs/emulator-contract.md` | what the launcher hands the PS1 emulators and gets back (`rc/launch.sh`, `abfeatures`, the ways out) |
| `docs/app-ports.md` | how a third-party program becomes an App - the rules every `app_*` repository follows, and the ports |
| `docs/versioning.md`, `docs/ci.md`, `docs/code-signing.md` | the version scheme; every workflow; Authenticode through SignPath (parked) |
| `docs/infrastructure.md` | what runs where (the addresses are in the git-ignored `infrastructure.local.md`) |
| `docs/tester-checklist.md` | the hardware proofs, for testers |
| `docs/kernel-flash-recovery.md`, `docs/pi-install-guide.md` | recovering a console; installing on a Pi |
| `docs/store-homebrew-plan.md` | an open plan: homebrew PS1 games in the Store |
| `docs/history/*.md` | how each platform and the big features came to be |
| `docs/archive/` | finished plans, reduced to what they decided (the full texts are in git history) |

Open plans that belong to one repository stay there: the launcher's `docs/` (`extensions-plan.md`,
`store-plan.md`, `app-format-plan.md`, `virtual-gamepad-plan.md`, `scanner-processors-next-plan.md`,
`atari-vcs-plan.md`, plus the references `theme-format.md`, `menu-options.md`, `translation.md`),
autobleem-pc-tools' `docs/lan-share-plan.md`, autobleem-console-tools' native-backend plan. When a plan is
done, its last word goes into `docs/history/` (or the repository's CLAUDE.md), what is still open into
`docs/todo.md`, and the plan moves to `docs/archive/`, reduced.

## Keeping this repository the source of truth

- A fact that more than one repository needs lives here, once; the repositories link to it.
- An open item goes into `docs/todo.md` in the commit that finds it, and leaves in the commit that closes it.
- When a milestone closes, update `docs/roadmap.md` ("Where we are" and the next milestone's tables).
- The last full read of every repository's documentation was 2026-09-26; its stale-statement lists are
  todo D1, D2, D10 and D11.
