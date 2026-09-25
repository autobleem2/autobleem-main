# Splitting the launcher repository

Archived plan (done 2026-09-23). The full text is in git history: `git log -- docs/archive/repo-split-analysis.md`.

## Why

By 2026-09-22 the launcher repository held the launcher, four other C++ programs, the build image, the site
tooling, the Pi/PC appliance installers and image builders, themes, manuals and sample games. The split
followed the one real coupling: a single `CMakeLists.txt` built every C++ program on the same
`lib_ableem` -> `ab_core` -> `ab_classic` chain, while the scripts, content and ops had no build coupling at
all and could simply be carved out (`git filter-repo`, history kept).

## §5. The shared foundation is a submodule

**`autobleem-core`** = `lib_ableem` + `ab_core` + `ab_classic` (+ its tests): the "AutoBleem SDK", joined
into each C++ repo as a git submodule the way pcsx-abnxt takes `libpicofe`. `lib_ableem` alone was not
enough - every tool links `ab_core`, the console tools `ab_classic` too. The one-time cost was separating
the `ab_classic` files from the launcher-only `ab_ui` ones in `src/code/gui/`. Accepted trade-off: a change
to shared code is a commit in core plus a pointer bump in each consumer.

## §6b. Compile once, assemble many

Every component builds once, on its own CI, and publishes per-target artifacts (a package per target +
metadata) to its GitHub Releases and the site; nothing is rebuilt to make a product. A separate **assembly**
step (autobleem-appliance) fetches only what a target needs and composes the stick/package/image - the
console gets the console tools, the kernel payload and our RetroArch; the Pi and PC stick get neither.
Images start from a cached base and compress last. `docs/versioning.md` builds on this: the assembly pulls
"version X" of each piece.

## The repositories that came out of it

| repo | what |
|---|---|
| `autobleem` | the launcher (`ab_ui`, `ab_evoui`, the executable), `payload/`, `src/resources`, abpad |
| `autobleem-core` | the SDK submodule; also `ab_installer` since 2026-09-23 |
| `autobleem-console-tools` | PSC-Bios (an extension), ABFlashKit |
| `autobleem-pc-tools` | UpdateRoms, AutoBleemInstaller, AutoBleemWinSetup, AutoBleemFlasher, LAN Share |
| `autobleem-build` | the Docker image, `ci/`, `toolchains/`, the `nightly-release` action, the self-hosted runner |
| `autobleem-appliance` | the assembly (`assemble.yml`), `payload_linux/`, the image builders |
| `autobleem-repo` | the download site's tooling, the admin panel |
| `autobleem-themes`, `autobleem-manuals`, `autobleem-samples` | content, each publishing its own artifact |
| `autobleem-main` | the project hub: docs, decisions, the release workflows |

## Lasting gotchas

- Toolchain ownership was to be settled once (vendored copy vs submodule of autobleem-build) and has not
  been: the launcher still carries its own `toolchains/` and `ci/build.sh`, newer than autobleem-build's.
- Clone with `--recurse-submodules`; the workflows check out `submodules: recursive`.
- Each repo has its own `CLAUDE.md`; the cross-repo map is this repository.

## Still open

- Settle toolchain ownership: bring autobleem-build's `toolchains/` and `ci/build.sh` up to the launcher's,
  then have the launcher use them (or declare the launcher's the source).
- The launcher's stale `docker/`: remove it once nothing in the launcher calls its `run.sh`.
- `payload_linux/` exists in both the launcher and autobleem-appliance and has drifted; keep one.
