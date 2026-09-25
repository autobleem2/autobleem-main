# CI: how AutoBleem 2 is built today

Compile once, assemble many (`archive/repo-split-analysis.md` §6b): every component builds on its own CI in
one Docker image and publishes packages to its GitHub Releases; autobleem-appliance compiles nothing and
assembles the products from those; autobleem-main drives nightlies and promotions. History:
`history/ci-and-site.md`, `archive/ci-plan.md`, `archive/ci-org-migration-plan.md`.

## The rules every workflow follows

- **`AB_CI_ENABLED`** - a repository variable; until it is `true` every job is skipped. Never set it or
  change a repository's visibility unasked.
- **The image**: `ghcr.io/autobleem2/autobleem-build:develop` for develop pushes, PRs and nightlies,
  `:latest` for a `v*` tag (a nightly is develop all the way down, compilers included).
- **Runners**: compiling happens on hosted runners (`ubuntu-24.04`; `windows-latest` + MSYS2 for the
  emulators' Windows builds). The org's one **self-hosted runner** (on the build server, org-scoped,
  `autobleem-build/docker/runner/compose.yml`, labels `self-hosted,linux,x64`) only does what writes the
  server's disk or needs its Docker: site publishes, the image build, the appliance's disk images, the page,
  cleanup. Pull requests never reach it.
- **Nightlies**: each component's develop build refreshes its rolling GitHub `nightly` pre-release through
  autobleem-build's `.github/actions/nightly-release` (used `@develop`): the tag moved, the assets replaced.
  A `v*` tag makes a GitHub release (a hyphenated tag is a pre-release). `signpath-sign` is wired and off
  (`AB_SIGNING_ENABLED`, `docs/code-signing.md`).
- sccache runs from a local `SCCACHE_DIR` persisted with `actions/cache` (its GHA backend is broken).

## The workflows, repository by repository

| repository | workflow | triggers | what it does |
|---|---|---|---|
| `autobleem` (launcher) | `test.yml` | push/PR to develop, master; dispatch | `ci/build.sh native`: all suites, language validation, format, clang-tidy |
| | `publish-launcher.yml` | `v*` tags; develop pushes (not docs); dispatch | `launcher-<platform>-<v>.tar.gz` for psc/rpi/rpi64/pcusb/win -> release or nightly |
| `pcsx-ab`, `pcsx-abnxt` | `build.yml` | push develop/master, `v*`, PR, dispatch (runner, targets, publish) | four Linux targets + native Windows; `publish` to the site's `emu/` only on a tag or a dispatch with `publish` |
| `autobleem-core` | `build.yml` | push, `v*`, PR, dispatch | the SDK's suites |
| `autobleem-console-tools`, `autobleem-pc-tools` | `build.yml` | push, `v*`, PR, dispatch | the tools, tests, packages |
| `ext_store`, `proc_unzip`, `proc_template`, `app_*` | `build.yml` | push, `v*`, PR, dispatch | per-target packages, the nightly; ext_store also publishes the site's Store page (self-hosted) |
| `autobleem-manuals` | `build.yml` | push, `v*`, PR, dispatch (`publish`) | the PDFs; publish self-hosted |
| `autobleem-build` | `image.yml` | push/PR under `docker/**`; dispatch | builds the image on the self-hosted runner (layer cache), `:develop` from develop, `:latest` from master, plus `:<sha>` |
| | `retroarch.yml` | monthly (3rd, 04:17), daily 04:41, dispatch | RetroArch + cores for the Pis, the PC stick and Windows -> `rpi/`, `pc/`, `win/` on the site |
| `retroarch-psc` | `upstream.yml` | daily 04:41, dispatch | a new upstream RetroArch release built for the console, tagged, published to `psc/retroarch/` |
| | `build.yml` | push, `v*`, PR, dispatch | the full RetroArch + sharded cores build (gated by `CI_ENABLED` - see below) |
| `psc-kernel-payload` | `build.yml` | push, `v*`, PR, dispatch | boot.img + abrootfs, reusing the last release when nothing changed |
| `autobleem-appliance` | `assemble.yml` | `v*` tags; daily 03:17 UTC (nightly); dispatch (channel, version, platforms) | fetches the components' release or nightly assets, assembles every platform's package, publishes to the site; the `image` job (self-hosted, `AB_IMAGE_BUILD_ENABLED`) builds the Pi and PC stick images; a scheduled night with no changed component (`sources.json`) is skipped |
| `autobleem-repo` | `page.yml` | develop pushes touching the page generator; dispatch | regenerates the download page (self-hosted) |
| | `cleanup.yml` | daily 01:30, dispatch | the server's Docker and old nightlies pruned, before the assembly |
| | `withdraw.yml` | dispatch | removes (or restores) a testing or nightly build from the site |
| `autobleem-main` | `nightly.yml` | dispatch | `tools/release.py nightly`: rebuild the components whose develop moved, then assemble |
| | `promote.yml` | dispatch (kind, version, dry run) | `tools/release.py promote`: alpha/beta/rc/release tags across the components, the appliance last |

`nightly.yml` and `promote.yml` start workflows in other repositories, so they need the `autobleem-admin`
GitHub App (`AB_ADMIN_APP_ID`, `AB_ADMIN_APP_KEY`); the admin panel (`archive/admin-panel-plan.md`) is
their front end.

## By hand

Any target builds in the image on any Linux box with Docker, from a checkout with its submodules:

```bash
docker run --rm -u $(id -u):$(id -g) -v "$PWD:$PWD" -w "$PWD" \
    ghcr.io/autobleem2/autobleem-build:develop ci/build.sh psc     # native psc rpi rpi64 pcusb win
```

Output lands in `build_<target>/` and `dist/<target>/`. `AB_NO_PCSX=1`, `AB_NO_UPX=1`, `AB_NO_LINT=1`,
`AB_JOBS` are the knobs (the script's header). A tree without `.git` needs `AB_GIT_*` in the environment.
Changing a toolchain: a build-arg in autobleem-build's `docker/Dockerfile` on develop; `ab-validate` must
still pass (the console's SDL2 stays at 2.0.14, Wayland + ALSA only).

## Known issues

- `retroarch-psc`'s `build.yml` gates on `vars.CI_ENABLED`, not `AB_CI_ENABLED` like everything else
  (its `upstream.yml` uses `AB_CI_ENABLED`).
- The launcher's `toolchains/` and `ci/build.sh` are newer than autobleem-build's copies, which are meant to
  be the one source; the launcher's `docker/` is a stale copy of the image's.
