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
  On the build server the image is **local**: `image.yml` builds it there, in the Docker daemon the self-hosted
  runner shares (the runner is the `autobleem-runner` container - `myoung34/github-runner` on the host's
  `docker.sock`), so the jobs there use the local `:develop`/`:latest` and never pull. Its ghcr login is the job's
  own `GITHUB_TOKEN`, which expires with the job - a later `docker pull` on the server answers "denied", and that is
  not a fault. The promote moves autobleem-build's master first, so `:latest` is rebuilt before any `v*` tag
  compiles; autobleem-repo's `cleanup.yml` keeps `:develop` and `:latest` (2026-10-03).
- **Runners**: the Linux compile jobs go through **`autobleem-build`'s `route.yml`** (a reusable workflow,
  2026-09-27): the laptop runners (`bleemmachine`, `bleemmachine-2`, `bleemmachine-3` - three instances on the one
  laptop, because one runner runs one job at a time and serialized the matrix legs; label `ab-main`, runner
  group `pcusb-test` - no `self-hosted` label, so `runs-on` is `["ab-main"]` alone) when any is online,
  else hosted `ubuntu-24.04`. Measured 2026-09-27: console-tools 5m31s on three runners (9m22s on one,
  about 3m hosted).
  A pull request always goes hosted, decided before any token is minted; `force_fallback` (a dispatch input)
  forces hosted for a test. The caller needs a `route` job (`secrets: inherit` - the `autobleem-admin` App
  reads the org's runner list; the repository must be in the App variables' selection, which the
  owner keeps), a plain `route_runner` job re-exporting `runs_on` (a reusable workflow's outputs cannot feed
  `runs-on` directly), then `runs-on: fromJSON(...)` on the build job. **The build server is not a fallback**:
  its runner itself runs in a container, and a runner in a container cannot start a `container:` job
  (proc_unzip run 36284746407). Moved (2026-09-27, each proven by a green develop build on the laptop): proc_unzip, ext_store,
  console-tools, pc-tools, the launcher (`test.yml` native + `publish-launcher.yml`'s build matrix),
  pcsx-ab, pcsx-abnxt. Still hosted: `windows-latest` + MSYS2 for the emulators' Windows builds. The build server's **self-hosted runner**
  (org-scoped, `autobleem-build/docker/runner/compose.yml`, labels `self-hosted,linux,x64,psc-build`) only
  does what writes the server's disk or needs its Docker: site publishes, the appliance's disk images
  (through 2026-09-28 - see below), the page, cleanup. Pull requests never reach either self-hosted runner.
  **2026-09-29: the appliance's `image` job (RPi and PC-stick image building, `assemble.yml`) moved off
  psc-build to its own 4th runner on `bleemmachine` (label `bleemmachine-image`, user `gha-runner`, same org
  - `docs/infrastructure.md`'s "PC test machine" row) - psc-build's disk was down to 13G free with the
  image job's 6.8G base-image cache on it, and bleemmachine had 152G free to spare; while there, pcusb also
  dropped `--mount`/`--privileged` for `mmdebstrap --mode=unshare` (rootless, bleemmachine's kernel supports
  unprivileged user namespaces, which psc-build's container-runner could not). Because the `image` job no
  longer runs on the box that holds `AB_REPO_DIR`, its site-publish step moved too: it now uploads the
  finished `.img.xz` as a normal `actions/upload-artifact` and `publish-release`/`publish-nightly` (still
  self-hosted on psc-build, unchanged otherwise) download it and write it to the site, the same
  artifact-passing plumbing the workflow already used for every other payload - no new ssh/rsync path.
  Full reasoning and the disk/permission inventory behind the move:
  `company/status/notes/image-build-move-plan.md` (PLATFORM-11; autobleem-appliance PR #1,
  `f27683257d51c9f81f84314cb20f2ba00c52476c`). **The runner audit (2026-09-27, image job since moved)**:
  every self-hosted psc-build job but one is a site write (`AB_REPO_DIR=/home/claude/autobleem-repo` bind-mounted:
  appliance publish-release/publish-nightly, build retroarch.yml publish, manuals, pc-tools site, samples,
  ext_store site, pcsx-ab/abnxt publish, retroarch-psc publish, autobleem-repo page/stack/cleanup/withdraw);
  the remaining one needs the server's own state (autobleem-build `image.yml` - the daemon's layer cache;
  note this is autobleem-build's Docker-image build, unrelated to the appliance's now-relocated `image`
  job). All of them are pinned to the build server by its own
  label, `runs-on: [self-hosted, psc-build]` (2026-09-27, all 10 repos) - never use the general
  `self-hosted,linux,x64` labels for a new job. **psc-build's runner itself runs in a container**, so it
  cannot run a job with `container:` ("Container feature is not supported when runner is already running
  inside container") - no compile job can go there. What can run on either: pcsx-ab/abnxt's compile job with
  `runner=self-hosted` (bare `self-hosted` today). **Pull requests never reach a self-hosted runner** - no
  workflow uses `pull_request_target`, and each self-hosted job either sits in a workflow with no
  `pull_request` trigger or excludes it in its `if:` (develop/tag refs, `event_name != 'pull_request'`,
  dispatch inputs); keep it so for any job moved to either runner.
- **Nightlies**: each component's develop build refreshes its rolling GitHub `nightly` pre-release through
  autobleem-build's `.github/actions/nightly-release` (used `@develop`): the tag moved, the assets replaced,
  then (2026-09-26) a `component-nightly` repository_dispatch starts autobleem-appliance's assembly - the
  nightly follows a push within ~30 min instead of waiting for the schedule. The seven feeding components
  (launcher, pcsx-ab, pcsx-abnxt, console-tools, pc-tools, ext_store, proc_unzip) mint the `autobleem-admin`
  App's token for it; a repository without `AB_ADMIN_APP_ID` publishes its nightly and leaves the assembly
  to the schedule. Only a build of every target publishes a nightly (a partial manual run does not).
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
| `autobleem-build` | `image.yml` | push/PR under `docker/**`; dispatch | builds the image on the self-hosted runner (layer cache), `:develop` from develop, `:latest` from master, plus `:<sha>`; a real develop push also dispatches `autobleem-main`'s `nightly.yml` with `rebuild_all` (R17, below) |
| | `retroarch.yml` | monthly (3rd, 04:17), daily 04:41, dispatch | RetroArch + cores for the Pis, the PC stick and Windows -> `rpi/`, `pc/`, `win/` on the site |
| `retroarch-psc` | `upstream.yml` | daily 04:41, dispatch | a new upstream RetroArch release built for the console, tagged, published to `psc/retroarch/` |
| | `build.yml` | push, `v*`, PR, dispatch | the full RetroArch + sharded cores build (gated by `CI_ENABLED` - see below) |
| `psc-kernel-payload` | `build.yml` | push, `v*`, PR, dispatch | boot.img + abrootfs, reusing the last release when nothing changed |
| `autobleem-appliance` | `assemble.yml` | `v*` tags; a component's nightly (repository_dispatch `component-nightly`); daily 03:17 UTC as the safety net; dispatch (channel, version, platforms, images, skip_unchanged) | fetches the components' release or nightly assets, assembles every platform's package, publishes to the site; the `image` job (self-hosted, `[bleemmachine-image]` since 2026-09-29 - moved off psc-build, see above; `AB_IMAGE_BUILD_ENABLED`) builds the Pi and PC stick images and uploads them as a build artifact (it no longer writes the site directly - `publish-release`/`publish-nightly` download that artifact and publish it), skipped with `images: false` (packages only); an automatic run waits `AB_NIGHTLY_SETTLE_SECONDS` (180) for sibling builds and is skipped when the site's nightly has the same components, platforms and images (`sources.json`); the concurrency group never cancels - one run and one pending, so a burst gives at most two assemblies |
| `autobleem-repo` | `page.yml` | develop pushes touching the page generator; dispatch | regenerates the download page (self-hosted) |
| | `cleanup.yml` | daily 01:30, dispatch | the server's Docker and old nightlies pruned, before the assembly |
| | `withdraw.yml` | dispatch | removes (or restores) a testing or nightly build from the site |
| `autobleem-main` | `nightly.yml` | dispatch | `tools/release.py nightly`: rebuild the components whose develop moved (not by documentation only), then assemble unless the chain already did (`--all`: always) |
| `autobleem-main` | `preview.yml` | dispatch (the admin panel's Preview panel) | `tools/release.py preview --branch B`: every component that has the branch builds it into its rolling `preview` release (the `channel=preview` input of its build), then the appliance assembles `preview/<version>/` with every other component's nightly (PLATFORM-20) |
| | `promote.yml` | dispatch (kind, version, dry run) | `tools/release.py promote`: alpha/beta/rc/release tags across the components, the appliance last; run again after a failure it finishes the same tag (`resume_tag`: the launcher tagged, the appliance not built) and reruns a reused tag's failed build |

`nightly.yml` and `promote.yml` start workflows in other repositories, so they need the `autobleem-admin`
GitHub App (`AB_ADMIN_APP_ID`, `AB_ADMIN_APP_KEY`); the admin panel (`archive/admin-panel-plan.md`) is
their front end. The components' `nightly` jobs use the same App, with the same two names in each of the
seven repositories, for the dispatch to the appliance (the App needs Contents: write on autobleem-appliance).

**A develop image push reaches the nightly on its own (R17, 2026-09-27).** Until then a toolchain change in
`autobleem-build`'s `docker/Dockerfile` only reached the nightly with the next unrelated commit in one of the
seven components - nothing reacted to `:develop` being republished, and the manual "nightly refresh"
(`tools/release.py nightly` / the admin panel button) by default rebuilds only what a component's own
develop moved past its `nightly` tag, which an image-only change never does either. `image.yml`'s
`dispatch-nightly-refresh` job now mints the same App's token (`AB_ADMIN_APP_ID`/`AB_ADMIN_APP_KEY` reach
`autobleem-build` since 2026-09-27; proven by image run 36284543904 -> nightly 36284615325) and starts `autobleem-main`'s `nightly.yml` with `rebuild_all: true` - the existing,
already-tested path that rebuilds every `NIGHTLY_REPOS` component regardless of their own source (none of
them pin the image by digest, so the rebuild alone picks up the new toolchain) and reassembles the
appliance's nightly. Only for a real `:develop` push (never master, a pull request, or a validate-only
`workflow_dispatch` with `push: false`); should the App ever stop reaching `autobleem-build` it is a quiet
`::notice`, and the fallback stays what it always was - run `nightly.yml` by hand with `rebuild_all` (the
admin panel's "Refresh nightly", once it exposes that option, or `gh workflow run nightly.yml -f
rebuild_all=true --repo autobleem2/autobleem-main`).

## By hand

Any target builds in the image on any Linux box with Docker, from a checkout with its submodules:

```bash
docker run --rm -u $(id -u):$(id -g) -v "$PWD:$PWD" -w "$PWD" \
    ghcr.io/autobleem2/autobleem-build:develop ci/build.sh psc     # native psc rpi rpi64 pcusb win
```

Output lands in `build_<target>/` and `dist/<target>/`. `AB_NO_PCSX=1`, `AB_NO_UPX=1`, `AB_NO_LINT=1`,
`AB_JOBS` are the knobs (the script's header). A tree without `.git` needs `AB_GIT_*` in the environment.
Changing a toolchain: a build-arg in autobleem-build's `docker/Dockerfile` on develop; `ab-validate` must
still pass (the console's SDL2 stays at `autobleem_sdl` 2.0.18, Wayland + ALSA only).

## Known issues

- `retroarch-psc`'s `build.yml` gates on `vars.CI_ENABLED`, not `AB_CI_ENABLED` like everything else
  (its `upstream.yml` uses `AB_CI_ENABLED`).
- The launcher's `toolchains/` and `ci/build.sh` are newer than autobleem-build's copies, which are meant to
  be the one source; the launcher's `docker/` is a stale copy of the image's.
