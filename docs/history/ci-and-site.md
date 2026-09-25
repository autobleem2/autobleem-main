# The org, the CI and the site's admin panel (2026-09-22/23)

The last word of the org/CI plans: `docs/archive/ci-org-migration-plan.md` and `admin-panel-plan.md` (reduced
summaries; the full texts - and the superseded `ci-public-migration-plan.md` - are in git history).

## What exists

- **Every repository is public in `github.com/autobleem2`**, default branch **develop**; `psc-bluez` went back
  to `screemerpl` (private - not a build input). The repositories and how they depend on each other are in
  this repository's `CLAUDE.md`.
- **Compile once, assemble many.** Each component builds on hosted runners in
  `ghcr.io/autobleem2/autobleem-build` (`:develop` for develop builds, `:latest` for releases) and keeps a
  rolling `nightly` release (autobleem-build's `nightly-release` action); a `v*` tag makes its release.
  `autobleem-appliance` never compiles: it assembles the console stick package, the Pi and PC-stick packages
  and images and the Windows product from those releases and publishes them. Everything is gated by the
  repository variable `AB_CI_ENABLED`.
- **The build server** runs only what needs its disk or privileges, on the org's self-hosted runner: the
  site publish, the image builds, the withdraw/page jobs - and, since 2026-09-23, a nightly cleanup
  (autobleem-repo's `cleanup.yml`, 01:30 UTC: old `autobleem-build:<sha>` tags, dangling images, stale build
  cache). The disk ran full that day and stopped the runner mid-nightly; the site now keeps **one** nightly
  (`NIGHTLY_KEEP`, the one before kept only while the newest has no images yet).
- **Channels**: release / testing / nightly, offered by the launcher's update, AutoBleemInstaller,
  AutoBleemFlasher and the Raspberry Pi Imager lists (`history/online-update.md`). The console updates itself
  when it has a network (`abupdate` from `rc/selection.sh`).
- **The admin panel**, `https://autobleem.retromenele.pl/admin/` (autobleem-repo `admin/`): GitHub login
  through the `autobleem-admin` GitHub App and oauth2-proxy, org members look, `release-managers` act. Builds
  with a time-left estimate, the channels, the builders' health (runner, disk - red under 10 GB, image), the
  buttons (nightly all or per platform, promote alpha/beta/rc/release through `autobleem-main`'s
  `promote.yml` / `tools/release.py`, cancel / re-run, withdraw, republish the page), the audit log, browser
  and Telegram notifications, and the same as a JSON API with a GitHub token as the bearer.

## The tools that left the launcher's tree

- PSC-Bios (WiFi, timezone, pad mapping wizard - an extension now) and ABFlashKit (the kernel flasher, an App)
  live in `autobleem2/autobleem-console-tools`; UpdateRoms, AutoBleemInstaller and AutoBleemWinSetup in
  `autobleem2/autobleem-pc-tools` - each with its own CLAUDE.md, CI and release, assembled by autobleem-appliance.
- The console tools' pattern stays: an SDL-free `<tool>_core` (tested) under the program, drawing with the
  launcher's theme through `AppBase`, `EnvironmentSetup::forTool()`, and console-only work behind an interface
  with a fake (`ConsoleBackend` -> `AbnetBackend` / `FakeBackend`) so a tool runs on Windows for a visual test.
- UpdateRoms is a plain Win32 window, no SDL and no theme (the owner's call), linked `-static` into one exe.

What is still open from these plans is in `docs/todo.md`.
