# AutoBleem versioning standard

One version scheme for every component of the suite, so a release is trivial to track and the
compile-once/assemble-many pipeline (`docs/repo-split-analysis.md` §6b) can pull "version X" of each piece.
Decided 2026-09-22 (owner): **unified semver + build metadata**, and the version must be **visible in every
component's UI**.

## 1. The version string

Every repo — launcher, `pcsx-ab`, `pcsx-abnxt`, `retroarch-psc`, the console/PC tools, themes, samples —
uses the **same grammar**, driven by its git tag:

| Kind | Tag / version | Example |
|---|---|---|
| **Stable release** | `vX.Y.Z` | `v2.0.0` |
| **Pre-release** | `vX.Y.Z-alpha.N` / `-beta.N` / `-rc.N` | `v2.0.0-rc.1` |
| **Nightly (develop)** | `vX.Y.Z-dev.<shortsha>` | `v2.1.0-dev.a09927c` |
| **Upstream lineage** (forks) | append semver build metadata `+…` | `v2.0.0+r26.g0f4727f1`, `v2.0.0+ra1.22.2` |

- **Unified**: for a coordinated release, every component is tagged the **same** `vX.Y.Z`. "AutoBleem 2.0.0"
  means every component at `v2.0.0`. The assembly pulls that one version of each piece.
- **Pre-release suffixes are dot-numbered** (`-alpha.1`, not `-alpha1`) so they sort by semver.
- **Ordering** is plain semver: `2.0.0-alpha.1 < 2.0.0-beta.1 < 2.0.0-rc.1 < 2.0.0`; a `-dev.<sha>` build of
  the next version sorts below its release. `repo_index.py` uses **one** semver sort — the per-scheme
  `pcsx_version_key` / `psc_version_key` hacks go away.
- **Upstream base never lost**: a fork's own tag is the AutoBleem version; its upstream base (notaz r26,
  RetroArch 1.22.2) rides in the `+build` metadata and in `manifest.json` (see §3).
- **Unified applies to *releases*, not to development.** A coordinated `vX.Y.Z` tag is what makes every
  component match. Develop/nightly builds carry their own `-dev.<sha>` per component (which naturally
  differ), and a developer may build any **mix** — a "dirty" assembly of whatever is checked out or newest —
  on request. The assembly enforces one version only for a tagged release; for a dev/dirty build it composes
  whatever component versions it is given (latest dev of each, or a locally built component), stamps the
  result `-dev` and records each component's actual version in the manifest. Nothing forces the whole suite
  to rev together during day-to-day work.

## 2. How each repo derives it

A single shared helper (lives in `autobleem-build`, copied into each repo's build, à la the launcher's
`cmake/generate_version.cmake`) turns the tag into the version fields at build time:

- `git describe --tags --always --dirty` → the tag when on one, else `<next>-dev.<sha>`.
- Emits a generated `version.h` (C/C++) or a `VERSION`/`manifest.json` (scripts) with the fields in §3.
- `BUILD_TIMESTAMP` is kept stable while tag/hash/branch/dirty are unchanged (the launcher already does this
  — avoids needless rebuilds).
- Nightlies get `<next>` from a repo constant (the launcher's `AB_VERSION_FALLBACK`, renamed consistently);
  a tagged build takes the tag verbatim.

## 3. The recorded fields (version.h / manifest.json)

Every component records, and its packaged `manifest.json` carries:

- `version` — the semver string (`v2.0.0` / `v2.0.0-rc.1` / `v2.0.0-dev.<sha>`).
- `commit`, `branch`, `dirty`, `build_date`.
- `upstream` — for forks, the upstream base (`r26 / g0f4727f1`, `RetroArch 1.22.2`); empty otherwise.
- `full` — a human string combining the above (what the UI shows), e.g.
  `v2.0.0 (master@a09927c)` or `v2.0.0-dev.a09927c+r26`.

## 4. It must be visible — every component shows **the package's** version

**The owner's rule (2026-09-23): every program except RetroArch shows the version of the package it came
in, written exactly as the package's `VERSION` file writes it** — `v2.0.0-alpha2-17-g1760cc8` for a
nightly, `v2.0.0-alpha2` at a tag. Not a component's own `git describe`: on one stick the launcher,
pcsx-ab and pcsx-abnxt used to show three different `v2.0.0-alpha2-…` strings (each repo describes
itself against the shared release tags with its own commit count and hash), and the splash showed a
fourth, the bare tag.

How it works (all in `autobleem-core`, `core/services/environment.*`):

- **`Env::productVersion()`** — `$AB_VERSION` when a parent set it; else the first line of a `VERSION`
  file: the data root's (the stick's own, written by the assembly and the installer), the one next to the
  running program (`Env::executableDir()`), or the one a folder up (`<stick>/UpdateRoms/UpdateRoms.exe`
  reads the stick's); else this build's `Version::DESCRIBE`.
- **`Env::exportProductVersion()`** — the launcher's `main()` puts it into `AB_VERSION` before anything
  starts, so every program it runs (the emulators, the console tools, the Apps) inherits the same string.
- **The assembly** (`autobleem-appliance`) writes the release's `VERSION` next to every PC program: into
  `AutoBleemInstaller/`, `UpdateRoms/` and `AutoBleemFlasher/` before zipping them, and into the Windows
  program folder (the NSIS script installs it, and the Windows launcher reads it from there).

| Component | Where the version shows |
|---|---|
| **Launcher** | Splash, About, Hardware Information (`Env::productVersion()`); the log's first line is `AutoBleem <package version> (launcher <branch>@<hash>, built …)`. |
| **Console tools** (pscbios, abflashkit) | The shared classic screens (About, Hardware Information) — `Env::productVersion()`, through `AB_VERSION` from the launcher. |
| **PC tools** (installer, setup helper, UpdateRoms, flasher) | The window title and the log's first line (`Env::productVersion()`, the build's own `FULL_VERSION` in brackets in the log). |
| **Emulators** (pcsx-ab, pcsx-abnxt) | `AutoBleem <AB_VERSION>`: pcsx-abnxt's AutoBleem menu footer (`ab_menu.c`) and both emulators' credits frame (`menu.c`); their log line puts it before their own `REV`. Without `AB_VERSION` (started by hand) they show their own `REV` as before. |
| **RetroArch (console build)** | The one exception: RetroArch's own version; our build stamp goes in `retroarch.version` and the log. |

Rule for new UI: the version is `Env::productVersion()` (or `$AB_VERSION` in a program that does not link
core), drawn in a consistent, unobtrusive spot (a footer or an About/System line), and written in the
**first line of the component's log**, where the component's own build identity may follow in brackets.

## 5. Assembly & the site

- A release's manifest (`releases/<vX.Y.Z>/release.json`) lists each component artifact **at the same
  version** — the assembly reads it to fetch and compose.
- `latest.json` / `unstable.json` carry the one semver; "latest stable" and "the pre-release" are a semver
  comparison, not per-scheme rules.
- The launcher's online update compares its installed `version` to the channel's — unchanged, just uniform.

## 6. Migration (applies as each repo is touched)

1. Add/point the shared `generate_version` helper; emit the §3 fields.
2. Normalise existing tags: the emulators' `v2.0.0-alpha1` → `v2.0.0-alpha.1`; retroarch's `v1.22.2-1` →
   `v2.0.0+ra1.22.2` on its next AutoBleem-coordinated tag (its own `retroarch.version` keeps `1.22.2`).
3. Add the UI version line wherever §4 says it is missing.
4. Collapse `repo_index.py` to one semver sort once every publisher emits the standard string.
