# PLATFORM-11 - builds move from the build server to the laptop

Todo row: `docs/todo.md` line 169 (owner, 2026-09-27, start after the private panel is live).

## Handoff / stop point (2026-09-27, end of session)

Stopping for the night on window/weekly usage limits (Eleanor). Status:

- **Phase 1 (inventory)**: done, sections 1-4 below. Reported to Victor Lane (Lead Platform).
- **Phase 2, point 1** (route `autobleem-build/image.yml:image` through route.yml, laptop-or-server
  fallback instead of route.yml's usual laptop-or-hosted): the change is written and was verified by eye
  (full file re-read after editing), but is **blocked**: committing it in a fresh clone of autobleem-build
  at `E:/Programming/_work-r19/platform11-route/repo` (branch `feature/platform11-route-image`, off
  `develop` `dd59b73`) was refused by my own tool's permission classifier ("Modify Shared Resources"), and a
  follow-up plain `git status` in the same directory was refused too. Per the standing rule, this was not
  retried, not worked around, and not routed to another session to apply on my behalf - Victor is escalating
  it to Eleanor/the owner directly. **That clone directory is left untouched, uncommitted, waiting for the
  owner to apply it or explicitly unblock the tool for it.** The exact diff (the three new/changed jobs:
  `route`, `route_runner`, `image`'s `needs`/`runs-on`) is pasted in full in section 5a below so nothing is
  lost even if that directory becomes unreachable.
- **Phase 2, point 2** (autobleem-appliance `assemble.yml:image` split plan): done, doc-only as instructed -
  section 5b below is the plan; Victor's call was explicitly NOT to implement it yet (`--privileged`/
  rootless-debugfs and the host cache dir need proving on the laptop first).
- **Phase 2, point 3** (site-write jobs and the server's build caches stay put): no action needed - already
  true today, nothing proposed changes it.

**Next steps for whoever picks this back up:** (1) wait on the owner/Eleanor re: the image.yml blocker -
either they apply section 5a's diff directly, or they unblock the tool for that specific action and it gets
retried from a fresh clone; (2) once the laptop's `--privileged`/rootless-debugfs/disk are proven (see
section 5b's "proof steps"), the appliance split can be written; (3) nothing here is merged - both
PLATFORM-10 (`feature/platform10-nightly-retention`, merged) and PLATFORM-12
(`feature/platform12-tests-ci`, pushed `41203e3`, awaiting Victor's review) are separate, already reported.

## 1. Current runner state (`gh api orgs/autobleem2/actions/runners` - NOT refused, worked with my own gh auth)

4 runners, all online:
- `psc-build` (Linux, labels: self-hosted, Linux, X64, psc-build) - the build server, its runner process
  itself runs inside a container (route.yml's comment: cannot nest a `container:` job).
- `bleemmachine`, `bleemmachine-2`, `bleemmachine-3` - all labels `ab-main` only (`bleemmachine` also
  carries `pcusb-test`), registered with `--no-default-labels` so none carry `self-hosted`. Three runner
  processes on the same laptop = up to 3 routed jobs in parallel.

## 2. How route.yml picks a runner today (`autobleem-build/.github/workflows/route.yml`, already built)

A reusable `workflow_call` every caller's `build.yml` already uses via a `route` job + a `route_runner`
shim job (GitHub can't read a `uses:` job's outputs from a downstream `runs-on:` directly). Order:
1. `pull_request` event -> always `ubuntu-24.04`, decided before any token/API call (public org, PR never
   touches the self-hosted box or the laptop).
2. `force_fallback: true` input (test-only) -> `ubuntu-24.04`.
3. Mints an `autobleem-admin` GitHub App token (`AB_ADMIN_APP_ID` var + `AB_ADMIN_APP_KEY` secret); no
   token -> `ubuntu-24.04` with a `::notice::`.
4. `GET /orgs/autobleem2/actions/runners`; non-200 -> `ubuntu-24.04` with a `::notice::`.
5. Any runner online with label `ab-main` -> `runs_on=["ab-main"]`. Else -> `ubuntu-24.04`.

`psc-build` is deliberately NOT a route.yml fallback tier (its runner can't nest a `container:` job - found
live by proc_unzip run 36284746407). A caller that wants it pins `runs-on: [self-hosted, psc-build]` directly.

**Already routed through route.yml today** (so PLATFORM-11's mechanism is not new - it's mostly already
built and live):
- `autobleem` (launcher): `test.yml`'s `native` job, `publish-launcher.yml`'s `build` job
- `autobleem-console-tools`: `build`, `psc`, `linux` jobs
- `autobleem-pc-tools`: `build`, `test`, `package` jobs
- `pcsx-ab`, `pcsx-abnxt`: `build` job (Linux matrix; `windows` job is separate, `windows-latest`)
- `proc_unzip`: `build` job
- `ext_store`: `build` job

**Not yet routed, still `[self-hosted, psc-build]` hard-pinned** - the actual PLATFORM-11 work:
see the table below.

**Already on a plain hosted runner, no routing needed at all** (nothing to move):
- `autobleem-build/retroarch.yml`: `retroarch` and `cores` jobs (`ubuntu-24.04`, the `cores` job even frees
  disk space explicitly) - only `publish` is self-hosted.
- `autobleem-appliance/assemble.yml`: `plan`, `assemble`, `sign-win`, `release` (`ubuntu-24.04`) - only
  `image`, `publish-release`, `publish-nightly` are self-hosted.
- `retroarch-psc/build.yml`: every job (`image`, `retroarch`, `shards`, `cores`, `package`) is
  `ubuntu-latest` already - only `upstream.yml`'s `publish` job is self-hosted.
- every `app_*` port repo (crispydoom, jfsw, wolf4sdl, jfduke3d, opentyrian, amiberry, openbor, sdlpop,
  app_terminal), `autobleem-core`, `autobleem-themes`, `autobleem-manuals`'s own `build` job: all plain
  `ubuntu-24.04`, nothing self-hosted except (manuals only) its `publish` job.

## 3. Per-job table - what's left self-hosted, and what each needs

| repo/file:job | compiles or site work | needs |
|---|---|---|
| autobleem-build/image.yml:`image` | **compiles** - builds+pushes the `autobleem-build` cross-toolchain Docker image itself (armhf/i386 sysroots, SDL2 2.0.14 from source) | docker (build-image.sh), `packages: write` perm + `GITHUB_TOKEN` (push to ghcr.io, ambient - no org secret), heavy disk/time, no site access at all |
| autobleem-build/retroarch.yml:`publish` | site work - writes RetroArch/cores tarballs into the site tree | docker sibling container, `AB_REPO_DIR=/home/claude/autobleem-repo` (server's local site checkout), no secrets beyond that path existing |
| autobleem-appliance/assemble.yml:`image` | **mixed - compile + site-write in one job** - builds the flashable `.img.xz` (privileged loop-mount/mmdebstrap for pcusb, rootless debugfs for rpi; a persistent HOST cache dir `/home/claude/ab-image-cache`, not `actions/cache`), THEN (same job) publishes straight into `AB_REPO_DIR` via `repo_publish.sh --local` when it's a release/nightly | docker sibling container, `--privileged` for pcusb, the host cache dir, `AB_REPO_DIR`; gated by its own `AB_IMAGE_BUILD_ENABLED` var on top of `AB_CI_ENABLED` |
| autobleem-appliance/assemble.yml:`publish-release` | site work only | `AB_REPO_DIR`, docker sibling container |
| autobleem-appliance/assemble.yml:`publish-nightly` | site work only | `AB_REPO_DIR`, docker sibling container, writes `sources.json` (PLATFORM-10's full/partial marker) |
| pcsx-ab/build.yml:`publish` | site work only (emu/ tree) | `AB_REPO_DIR`, docker sibling container |
| pcsx-abnxt/build.yml:`publish`, `publish-nightly` | site work only | same as pcsx-ab |
| autobleem-manuals/build.yml:`publish` | site work only (PDFs), serialised (`concurrency: site-manuals-publish`) | `AB_REPO_DIR`, docker sibling container |
| retroarch-psc/upstream.yml:`publish` | site work only (psc/retroarch/) | `AB_REPO_DIR`, docker sibling container |
| ext_store/build.yml:`site` | site work only (Store catalog) | `AB_REPO_DIR`, docker sibling container |
| autobleem-repo/cleanup.yml, page.yml:`publish`, stack.yml:`deploy`, withdraw.yml:`withdraw` | site work only - these ARE the site/admin panel itself | direct filesystem access to the live site tree, the admin panel's own deploy; no docker even needed for some |

Common pattern across every remaining self-hosted job that isn't `autobleem-build:image` or
`autobleem-appliance:image`: a `docker run --rm -v "$PWD:$PWD" -v "$AB_REPO_DIR:$AB_REPO_DIR"` sibling
container (the runner is itself a container and can't nest `container:` jobs) running
`autobleem-repo/tools/repo_publish.sh --local`, because `--local` is a plain filesystem copy into
`/home/claude/autobleem-repo` - this only works because the job IS on the machine that IS the site.

## 4. Proposal

**Which jobs move (straightforward - already the same shape as what's routed today):**
- `autobleem-build/image.yml:image` - pure compile + registry push, no site access. Same treatment as
  `pcsx-ab`/`pcsx-abnxt`/`ext_store`'s `build` jobs: add `route`/`route_runner`, `runs-on:
  fromJSON(needs.route_runner.outputs.runs_on)`. Its `packages: write` permission and `GITHUB_TOKEN` push
  work identically from `ab-main` or `ubuntu-24.04`.

**Which needs a split first:**
- `autobleem-appliance/assemble.yml:image` - split into two jobs, mirroring how `retroarch.yml` already
  separates `retroarch`/`cores` (hosted/routed) from `publish` (self-hosted): an `image-build` job (routed,
  does the `make_rpi_image.sh`/`make_pc_image.sh` work, uploads `image-<platform>` as an artifact) and an
  `image-publish` job (`[self-hosted, psc-build]`, downloads the artifact, does only the
  `repo_publish.sh --local` step). Two open questions this raises that I have not decided for you:
  1. the host-persistent cache dir (`/home/claude/ab-image-cache`) lives on the server only - moving the
     build to the laptop means either a new cache dir there (fine, same `--base`/`--reuse-root` mechanism,
     just a second cache to seed) or losing the cache-hit speedup until it warms up again.
  2. `--privileged` (pcusb's loop-mount) and rootless debugfs (rpi) both need testing on the laptop's own
     runner/Docker setup before this is safe to route - I have not touched the laptop for this, per the
     read-only rule.

**What stays on the server (all of it - "the site's own jobs stay", per the todo row and per my read of
every one of these jobs above):**
- every `publish`/`publish-nightly`/`publish-release`/`site`/`deploy`/`withdraw`/`cleanup` job listed in
  section 3 - they all write directly into `/home/claude/autobleem-repo`, the live site tree, which only
  exists on that one machine. Routing these anywhere else would need `--local` to become a real remote
  publish (rsync/ssh) instead of a filesystem copy - a materially bigger change than PLATFORM-11 asks for,
  and the todo row is explicit that the site, admin panel and login all stay on the server.

**Fallback when the laptop is off:** already built into route.yml - step 5 above falls through to
`ubuntu-24.04` automatically, with a `::notice::` in the run's log (`"the laptop runner (ab-main) is not
online - falling back to ubuntu-24.04"`). Every already-routed job today gets this for free; adding
`autobleem-build:image` to route.yml gives it the same fallback with no new code. Nothing needs to *detect*
the laptop being off and change behaviour by hand - route.yml already re-checks on every run.

**The server's build caches:** nothing proposed deletes anything (per the rules). Two options, not decided
by me:
1. Leave them in place, unused, once `autobleem-build:image`'s builds move to the laptop - they just go
   stale (the image-build cache note says "cache RPi OS Lite download + PC mmdebstrap root.tar... don't
   refetch/rebuild", which was written for the server; the laptop would grow its own copy from scratch on
   its first run).
2. If disk pressure on the server matters again (PLATFORM-10's whole reason for existing), the owner could
   ask for the stale server-side `autobleem-build` image-build cache to be pruned by hand later, once the
   laptop route has been proven - but that is a separate, explicit ask, not part of this move.

## 5a. The blocked diff - autobleem-build/.github/workflows/image.yml (uncommitted, NOT pushed)

Written and verified by eye in `E:/Programming/_work-r19/platform11-route/repo` (branch
`feature/platform11-route-image` off `develop` `dd59b73`), blocked from commit as described above. Replaces
the `image:` job's `needs: lint` / `runs-on: [self-hosted, psc-build]` with two new jobs before it plus a
changed `needs`/`runs-on` on `image:` itself; everything else in the file (the `lint` job, the `image` job's
own steps, `dispatch-nightly-refresh`, the `on:` triggers) is unchanged:

```yaml
  # Which runner the image job below uses (PLATFORM-11): the laptop (ab-main) when it is online, else the
  # build server (psc-build) - NOT route.yml's usual ubuntu-24.04 hosted fallback. A cold build compiles
  # cross-toolchains for armhf/i386/MinGW and SDL2 2.0.14 from source in the same multi-stage image (about
  # an hour cold, see the job's own header comment); a GitHub-hosted runner's disk and job time are not
  # proven to hold that, so this job keeps the server as its fallback instead of guessing. route.yml itself
  # still decides "is the laptop online" the normal way (see autobleem-build's route.yml for the full
  # order); only the OTHER side of that decision is swapped here, from ubuntu-24.04 to psc-build. Nothing
  # below needs a server-local path or secret beyond what route.yml itself already brings (AB_ADMIN_APP_KEY,
  # to ask the API whether the laptop is online) - the image job's own steps only ever use GITHUB_TOKEN
  # (ghcr push) and gracefully fetch the cover databases from the live site when no local copy is there
  # (see docker/build-image.sh's fallback order), whichever runner this lands on.
  route:
    if: vars.AB_CI_ENABLED == 'true'
    needs: lint
    uses: autobleem2/autobleem-build/.github/workflows/route.yml@develop
    secrets: inherit

  # A job whose type is `uses: <reusable workflow>` (route, above) cannot have its outputs read by a
  # downstream job's `runs-on:` directly - this plain job re-exports route's output, substituting
  # psc-build for route's own ubuntu-24.04 fallback (see the comment above).
  route_runner:
    needs: route
    if: vars.AB_CI_ENABLED == 'true'
    runs-on: ubuntu-24.04
    timeout-minutes: 2
    outputs:
      runs_on: ${{ steps.pick.outputs.runs_on }}
    steps:
      - id: pick
        run: |
          set -euo pipefail
          runner="${{ needs.route.outputs.runner }}"
          if [[ "$runner" == hosted* ]]; then
            echo 'runs_on=["self-hosted","psc-build"]' >> "$GITHUB_OUTPUT"
            echo "::notice::image: laptop (ab-main) not available ($runner) - falling back to the build server (psc-build) instead of a GitHub-hosted runner, since a cold image build's disk/time is not proven to fit hosted limits"
          else
            echo "runs_on=${{ needs.route.outputs.runs_on }}" >> "$GITHUB_OUTPUT"
            echo "routed to $runner"
          fi

  image:
    # never on a pull request: that would run a fork's Dockerfile on the build server or the laptop
    if: vars.AB_CI_ENABLED == 'true' && github.event_name != 'pull_request'
    needs: [lint, route_runner]
    runs-on: ${{ fromJSON(needs.route_runner.outputs.runs_on) }}
    permissions:
      contents: read
      packages: write
    # ...(env/steps below unchanged: Build, Push, Summary)
```

Checked before writing this: the ghcr push already uses `secrets.GITHUB_TOKEN` (ambient, not a server
secret); `docker/build-image.sh`'s one server-local fallback path
(`/AutoBleem/BUILD/data_that_gets_copied/cover_databases`) simply won't match elsewhere and the script
already falls through to fetching the cover databases from the live site when no local copy is found;
nothing reads the server's docker layer cache explicitly - it's implicit to whichever daemon runs the
build, so the laptop grows its own the same way the server did.

## 5b. Phase 2, point 2 - autobleem-appliance assemble.yml:image split plan (doc only, no code - per Victor)

Victor's call: NOT now - it sits on the nightly path, and `--privileged`/rootless-debugfs plus the
host-persistent cache dir need proving on the laptop first. This is the plan for whenever that proof is
done; nothing below has been implemented.

### Why it has to split, not just route

Today's single `image` job (assemble.yml lines ~260-457) does three things in one `runs-on: [self-hosted,
psc-build]` job, matrixed over platform (rpi-armhf, rpi-arm64, pcusb):
1. builds the flashable `.img.xz` (`make_rpi_image.sh --rootless` or `make_pc_image.sh --mount
   --privileged`) into a **host-persistent cache dir** (`/home/claude/ab-image-cache/<platform>`, NOT
   `actions/cache` - the whole reason the memory note "cache RPi OS Lite download + PC mmdebstrap root.tar"
   exists);
2. uploads the image as a build artifact;
3. (release/nightly only) publishes it straight into `/home/claude/autobleem-repo` via `repo_publish.sh
   --local` - a plain filesystem copy that only works because this job runs on the machine that IS the site.

Step 3 has to stay on psc-build (same reasoning as every other publish job in section 3). Steps 1-2 are the
part that could route - same shape as `retroarch.yml` already splitting `retroarch`/`cores` (routable) from
`publish` (self-hosted).

### The two jobs

- **`image-build`** (routed: `route`/`route_runner` + `runs-on:
  fromJSON(needs.route_runner.outputs.runs_on)`, matrixed over `needs.plan.outputs.image_platforms` exactly
  as today): runs the existing `make_rpi_image.sh`/`make_pc_image.sh` step unchanged, uploads
  `image-<platform>` as an artifact exactly as today. Nothing about the docker-sibling-container mechanics
  needs to change - it already runs `docker run --rm --privileged? -v "$PWD:$PWD" -v
  "$AB_IMAGE_CACHE_DIR:$AB_IMAGE_CACHE_DIR" ... autobleem-build:<channel> bash run.sh`, which is exactly the
  pattern every already-routed build job uses.
- **`image-publish`** (`runs-on: [self-hosted, psc-build]`, unchanged pin - this is site work): `needs:
  [plan, image-build]`, downloads the `image-<platform>` artifact, runs only the existing "Publish the image
  to the site" step (the `merge_rpi_imager_json.py` + `repo_publish.sh --local` calls), unchanged from
  today's job body.

### The artifact hand-off

Identical to how `retroarch.yml` already does it: `image-build` uploads `image-<platform>` (the `.img.xz`
plus `rpi_imager_repo.json` for rpi) via `actions/upload-artifact@v7`, `image-publish` downloads it via
`actions/download-artifact@v8` with `path: dist` (or wherever `merge_rpi_imager_json.py`/`repo_publish.sh`
expect it) - no new mechanism, this repo already does this exact hand-off for `assemble` -> `image` today.

### The cache

`AB_IMAGE_CACHE_DIR=/home/claude/ab-image-cache` only exists on the server. Once `image-build` can land on
the laptop, one of:
1. **A second cache dir on the laptop** (e.g. `~/ab-image-cache` under whatever user `bleemmachine`'s runner
   process runs as), seeded cold on its first run (RPi OS Lite download + PC mmdebstrap root.tar, the exact
   thing the image-build-cache-base memory note says to avoid re-fetching) and then persistent the same way
   as the server's - this is the natural fix, but it means TWO caches to keep warm (server's goes stale if
   `image-build` never lands there again; harmless, just wasted disk until someone prunes it by hand later,
   same as section 4's proposal for the other cache).
2. Accept a cold (no `--base`/`--reuse-root` hit) build on the laptop until its own cache warms up - correct
   but slower for however many runs it takes; the job's own 30-day eviction (`find "$CACHE" ... -mtime +30
   -delete`) means a cache that's actually used stays warm on whichever host it's actually built on.
   Recommend (1): the point of routing this job at all is speed, and starting cold defeats it for weeks
   until it happens to run again on the same host consistently (route.yml's decision is close to "always
   the laptop when it's online", so in practice it would mostly land there and only occasionally fall back -
   still enough churn to want its own warm cache rather than relying on happenstance reuse).

### The proof steps (what "needs proving on the laptop first" means, concretely)

Before this split is safe to route for real, the laptop's own runner/Docker setup needs to show, once, by
hand or via a `workflow_dispatch` test run with `force_fallback` NOT forcing hosted (so it actually lands on
ab-main):
1. `--privileged` works there for pcusb's `make_pc_image.sh --mount` route (loop devices, `grub-install`) -
   the assemble.yml job comment already documents this needed `--privileged` on the *server's* sibling
   container; the laptop's own Docker daemon/host kernel needs the same loop-device and grub tooling
   available, unverified today.
2. The `--rootless` debugfs/mtools/xz route for rpi (no privilege needed, per the job's own comment - "only
   needs debugfs/mtools/xz, all in this image, regardless of uid") - lower risk, but still unverified on
   that specific host/image combination until it's actually run there once.
3. Disk: a cold rpi build needs the ~550 MB compressed base plus (with `--keep-raw`, which this job passes)
   the ~3.1 GB decompressed raw image, times however many platforms build concurrently in the matrix - the
   laptop's free disk for this should be checked before the first real run, the same way this doc flagged
   the disk question for `autobleem-build:image` in point 1.
4. Whatever host ends up running `image-build`, the publish step in `image-publish` still needs `needs:
   image-build` to actually see a successful artifact regardless of which runner built it - no special
   handling needed there, `actions/download-artifact` doesn't care which runner uploaded it.

None of this has been run or tested by me - this section is a plan, not a report of anything verified on
the laptop.

## 6. What I did NOT do
No workflow file touched, no runner registered, no `AB_CI_ENABLED`/visibility/secret changed. Only read via
`gh api repos/<r>/contents/...` (workflow file contents) and `gh api orgs/autobleem2/actions/runners`
(succeeded, not refused, using my own `gh auth` as screemerpl - Victor, if you expected this to need a
narrower token, flag it and I'll requery a specific scope).
