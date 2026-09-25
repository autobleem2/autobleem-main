# App ports - how a third-party program becomes an AutoBleem App

The rules every `app_<name>` repository follows, written once. The owner's decisions behind them are in
`decisions.md` ("Third-party App ports"); the App format itself (`app.ini`, platform keys, `AppManifest`)
is in the launcher's CLAUDE.md, "Multi-platform Apps". `app_opentyrian` is the template to copy. Each port's
own CLAUDE.md keeps only what is particular to it.

## The ports (2026-09-26)

| Repository | App(s) | Release | Targets | Particular to it |
|---|---|---|---|---|
| `app_opentyrian` | OpenTyrian (Tyrian 2.1 freeware data) | v2.1.20260913-2 | psc rpi rpi64 pcusb win | the template; fills the screen at 4:3 |
| `app_sdlpop` | Prince of Persia (upstream ships the 1989 data) | v1.24-RC-1 | all five | no `VERSION` file, unlike the later ports |
| `app_crispydoom` | Doom (shareware), Freedoom: Phase 1 and 2 - three Store items | v7.1-2 | all five | `joystick_guid` must be set; patch 0002 exists only for the release image's SDL 2.0.12 (todo R2) |
| `app_wolf4sdl` | Wolfenstein 3D (shareware), Spear of Destiny demo | v20260504-2 | all five | raw buttons: `pad.ini` `virtual = psc` |
| `app_jfsw` | Shadow Warrior (shareware), software renderer | v20260105-2 | all five | upstream's own Win32 build on Windows; turning axis 0.1 on psc |
| `app_jfduke3d` | Duke Nukem 3D (shareware) | v20260105-2 | all five | kept as `app/eduke32` to replace the RetroBoot App in place |
| `app_openbor` | OpenBOR v7533, no games | v7533-3 | all five | our branding; `virtual = psc`; games wait for the owner (todo A2) |
| `app_amiberry` | Amiberry-Lite 5.9.3 (AROS, WHDLoad; no Kickstarts or games) | v5.9.3-1 | psc rpi rpi64 pcusb (**no win**) | C++17: gcc-12 against the console's Stretch sysroot with libstdc++ linked in - the route for any C++17 port |
| `app_terminal` | Terminal (bash on a pty) - our own App, not a port | v1.0.0 | psc rpi rpi64 pcusb | built on the SDK, `VirtualPad=false`; see its CLAUDE.md |

The owner's first console pass (2026-09-25/26) is behind the `-2`/`-3` releases; the rest of the hardware
pass is the tester checklist's §12 (todo A1).

## The shape of a port repository

- **Our patches over a pinned upstream submodule, never a fork.** `ci/build.sh` copies each submodule
  into `build_<key>/` and applies `patches/<name>/NNNN-*.patch`. To make a patch: edit inside the
  submodule, `git -C upstream/<name> diff > patches/<name>/NNNN-what.patch`, then check the submodule out
  clean again.
- **Submodules checked out LF** (`core.autocrlf false`, then re-checkout) - or the patches fail on a
  Windows checkout synced to the build server.
- **Build**: `ci/build.sh native|psc|rpi|rpi64|pcusb|win|all` inside `ghcr.io/autobleem2/autobleem-build`
  (`:develop` for develop, `:latest` for a `v*` tag). On the server by hand: rsync, the same `docker run
  ... ci/build.sh all`, then delete `build_*/` and `dist/` (decisions.md, clean up after builds).
- **Checks** before a package is made: `tools/check_psc_binary.sh` (glibc <= 2.24, GLIBCXX <= 3.4.22, no
  RPATH) and `tools/check_needed.sh` (every needed library is shipped or allowed; a per-port list of
  Windows system DLLs).

## Libraries

- **Shared, never bundled**: the SDL2 family (the launcher's 2.0.14 in `/tmp/lib` on the console, the
  launcher's own DLLs on Windows, the system's on the Pis and the PC stick), glibc, libstdc++/libgcc_s and
  the graphics stack. Nothing newer than the console's SDL is called unguarded.
- **Everything else is the App's own**: `lib/<key>/` and `Lib=lib/{key}` in `app.ini`, which `app_env.sh`
  and `run.sh` put first on the library path. Codecs (libpng, zlib, vorbis, vpx, flac, zstd) are built
  static per target into `build_<key>/deps` (kept while `deps/.stamp` matches). Optional network libraries
  (SDL2_net) are built and bundled, not left out. The RetroBoot libs pack is not used.

## Data, pads, state

- **Game data ships with the App** when it may: shareware, freeware, and what upstream itself ships. A
  file the build fetches comes from our mirror (`mirror/<name>/` on the site, autobleem-repo's
  `repo_publish.sh mirror`), pinned by sha256, cached in `build_data/`. Icons are drawn from the game's own
  title screen (`tools/make_icon(s).py`), never from art of unknown origin.
- **The pad**: `VirtualPad=true` (the virtual gamepad, `abpadd` + `libabpad.so`). The 2019/2020 PSC layout
  goes in as a patch to the port's defaults - configs are often binary or rewritten on exit, so never a
  separate setup tool. `pad.ini` `virtual = psc` for a port that reads raw buttons; the X360 default
  otherwise. Windows goes through XInput/GameController numbering under `_WIN32`.
- **State stays in the App folder**: it is the working directory (`rc/app_run.sh`,
  `LaunchService::planApp`), and each port's portable mode (`user_profiles_disabled`, `amiberry.portable`,
  `--configdir .`) keeps settings and saves there. A Store update must not overwrite them.
- **A way out of every App**: the console's **Reset** button (abpadd's Reset watch, also for
  `VirtualPad=false` Apps), a **Start+Select hold** on Linux, the port's own menu on **Windows** - which
  its readme names.

## Releases and the Store

- A `v<upstream>-<n>` tag makes a stable GitHub release (only a lower-case alpha/beta/rc/pre suffix makes
  a pre-release); `master` follows the released commit.
- Publishing to the Store is by hand today: `gh release download`, `tools/store_item.py`, `repo_publish.sh
  store` - into all five catalogs. The id and folder of the RetroBoot App it replaces are kept, so the Store
  replaces it in place on psc. Automating this is todo A5; the copies of the helper scripts in every
  repository are todo A6.
- One repository at a time, the owner answering each port's questions first; with the owner's OK the
  repository goes public in `autobleem2` with `AB_CI_ENABLED`.
