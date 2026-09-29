# Infrastructure - what runs where

The machines and services the project uses. Addresses, account names and machine-specific paths are
**not** in this public repository: they are in `infrastructure.local.md` next to this checkout's root
(git-ignored), which the owner keeps; ask for a copy. Below, `<build-server>`, `<test-pi>` and the like are
the names that file fills in.

| what | where | used for |
|---|---|---|
| **Download site** | `https://autobleem.retromenele.pl/` (a plain-HTTP mirror on `<build-server>:9090`) | every package, image, catalog and manual; a Caddy container on the build server serves `~/autobleem-repo` there (autobleem-repo's `docker/repo/`) |
| **Build server** | `<build-server>` (ssh alias `psc-build`), Linux x86_64, Docker | the self-hosted GitHub runner - publishing (`publish-release`, `publish-nightly`) and the site's files, by-hand builds with `docker/run.sh`; **not** the appliance's image builds any more (moved to `bleemmachine-image`, 2026-09-29 - see below) |
| **Build image** | `ghcr.io/autobleem2/autobleem-build:develop` (develop's) and `:latest` (master's) | every component compiles in it (autobleem-build) - develop builds in `:develop`, `v*` releases in `:latest` |
| **PC test machine** | `bleemmachine` (`docs/pc-test-machine.md`), a laptop, Linux x86_64, Docker | three org CI runners (`ab-main` label - most Linux compiles route here, `docs/ci.md`) and, since 2026-09-29, a 4th self-hosted runner (`bleemmachine-image` label, user `gha-runner`) that builds the appliance's RPi and PC-stick images (moved off psc-build - disk space); also hosts the `pcusb-test` VM for PC-USB device testing |
| **GitHub** | `github.com/autobleem2` | the repositories, Actions, releases (every component's `nightly` pre-release is its rolling development build) |
| **Test Raspberry Pi** | `<test-pi>` on the owner's LAN (a Pi 400) | trying Pi images and updates on hardware |
| **VMs** | the owner's VirtualBox | trying the PC USB stick image |
| **Consoles** | the owner's PlayStation Classic(s) | console tests (see `docs/tester-checklist.md`) |

Each test device's hardware, OS and traps (Pi 400, PlayStation Classic, the pcusb-test VM): `docs/test-devices.md`.

`infrastructure.local.md` holds, for each: the address, the account, how to reach it (keys, not passwords -
passwords are never written down), and the local paths a developer machine uses (toolchain folders, the
MSYS2 install, where the repositories are checked out).
