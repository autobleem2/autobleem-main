# The launcher's Build section: history moved out of CLAUDE.md (task D19)

Moved verbatim from the launcher's `CLAUDE.md` "## Build" section during task D19's second pass
(2026-09-26): sccache adoption timings, the CI Docker-image build recipe and its verification story, the
PSC (console) build's first-run history, the 2019 root-cleanup, and the libchdr refresh story. CLAUDE.md
keeps the operational facts (scripts, flags, toolchain files, current architecture); this file keeps why
and how they came to be that way.

## sccache timings

- **sccache** (2026-09-20) sits in front of every compiler in the image: `ci/build.sh` (and pcsx-ab's)
  configure with `CMAKE_C/CXX_COMPILER_LAUNCHER=sccache`, `docker/run.sh` mounts the cache from the host
  (`~/.cache/autobleem-sccache`, `AB_SCCACHE_DIR`, 10 GB) so it outlives the container, the run ends with
  the stats; `AB_NO_SCCACHE=1` opts out. The console target: 263 s cold, **42 s** with the cache warm
  (95 % hits) - the remaining misses are what includes the generated `core/version.h`. The image's last
  layer holds the binary (a musl release), so a version bump rebuilds nothing else.

## CI docker image narrative

- **CI: one Docker image builds every target** (2026-09-19; autobleem-main's `docs/ci.md` is the operator's page,
  autobleem-main's `docs/archive/ci-plan.md` the plan until the workflows have run). `docker/Dockerfile` -> `autobleem-build`
  (Debian Bookworm, ~3.4 GB, built on the server with `docker/build-image.sh`): the native build with
  clang-format/clang-tidy **22** (apt.llvm.org, the major MSYS2 has), Debian's `crossbuild-essential-armhf`
  / `-arm64` with the multiarch `libsdl2*-dev` packages for the two Pis, `mingw-w64` (posix) with the
  official SDL2 mingw devel packages at `/opt/mingw-sdl2` for Windows, the three cover databases at
  `/opt/autobleem/db`, and **the console toolchain by AutoBleem-NG's recipe** under `/opt/psc`: a Debian
  Stretch armhf sysroot (`mmdebstrap --variant=extract` from archive.debian.org - glibc 2.24 / libstdc++
  6.0.22, the console's own), Stretch's **gcc-6** cross compiler (patchelf'ed RUNPATH to its own
  isl/mpc/mpfr/gmp, its libc linker scripts rewritten to bare names - no host `/usr/arm-linux-gnueabihf`
  hijack, that directory is the Pi cross libc's), and **SDL2 2.0.14 + image 2.6.3 + mixer 2.6.3 + ttf
  2.20.2 built from source** with the console's backend set (Wayland + dummy, GLES via EGL, ALSA, udev, no
  X11, no OSS - see "SDL2 on the console" below), wrapped as `armv8-sony-linux-gnueabihf-*` so `PSCtoolchainV8.cmake` works with
  `-DAB_PSC_TOOLCHAIN=/opt/psc`. The 2019 Sony toolchain (`/opt/toolchain`, `autobleem/PSC-CrossCompile-
  Toolchain`) is **no longer what releases are built with** (the owner's call: outdated). Each stage ends
  with `docker/ab-validate.sh` linking a C++14 + SDL test program and checking the result (the console:
  ARMv8, nothing above GLIBC_2.24 / GLIBCXX_3.4.22, no RPATH, a Wayland SDL2).
  `ci/build.sh native|psc|rpi|rpi64|win|all` (run as `docker/run.sh ci/build.sh <t>`) configures into the
  same `build_*/` dirs the `make_*.sh` scripts use, builds, validates and packages into `dist/<t>/`; for
  `psc`/`rpi`/`rpi64` it **builds pcsx-ab first** from the sibling checkout (`AB_PCSX_DIR` /
  `../pcsx-ab`; pcsx-ab has its own `ci/build.sh` and the same Debian-fallback toolchain files) and the
  package ships that emulator. New scripts: `tools/make_psc_package.sh` (the console zip - the release
  script `make_psc.sh` always assumed; it also **regenerates `libs.tar.gz`** from the image's SDL build,
  keeping iconv/ogg/vorbis) and `tools/make_win_package.sh` (launcher zip with the four SDL DLLs +
  `libwinpthread-1.dll`, and `UpdateRoms-<v>.zip`). **The workflows today** (2026-09-23, the compile-once
  model - autobleem-main's `docs/ci-org-migration-plan.md`): the image is built and pushed by
  **`autobleem2/autobleem-build`**'s own `image.yml`, from develop and master pushes (that repo is the
  Dockerfile's one source; this tree's `docker/` is a stale copy without llvm-mingw); here, **`test.yml`**
  is the test gate (`ci/build.sh native` on a hosted runner, every push and pull request) and
  **`publish-launcher.yml`** builds `launcher-<platform>-<v>.tar.gz` for psc/rpi/rpi64/pcusb/win on develop
  pushes and `v*` tags, and keeps the rolling `nightly` release current; **autobleem2/autobleem-appliance**
  assembles the packages and images from it and the other components' releases, and publishes them.
  The monolith's `ci.yml` (everything built here, the packages published from here) and `site-refresh.yml`
  (the site's RetroArch and cores - autobleem-build's `retroarch.yml` does that now) were deleted on
  2026-09-23. All gated by `AB_CI_ENABLED`. Verified 2026-09-19 on the server: all five targets green
  A hardware-run debugging tale from that pass (the pcsx-ab Wayland segfault, the missing ALSA build, a
  gcc-6 limitation and a `ctest -j` fixture race) is at autobleem-main `docs/history/launcher-console-runs.md`.

## PSC build history narrative

  `toolchains/psc/cmake/FindSDL2.cmake` defines the four imported SDL2 targets over the sysroot's `.so`s
  (2.0.4 predates `sdl2-config.cmake`). The console build is **dynamic** - the original toolchain file's
  `--static` was always overwritten by the root CMakeLists' `^arm` branch (`-march=armv8-a+simd -Os -s`), and
  `rc/autobleem.sh` unpacks `Autobleem/lib/libs.tar.gz` (SDL2, SDL2_mixer) to `/tmp/lib` at boot. First
  built this way 2026-09-17: GCC 8 warning-free, `Tag_CPU_arch: v8`, NEON, hard-float, and the binary needs
  at most `GLIBCXX_3.4.22` / `GLIBC_2.7`, which the console's stock libstdc++ 6.0.22 / glibc 2.24 provide
  (the toolchain's own libstdc++ is 6.0.25 - anything newer than 3.4.22 would fail to load on the console).
  **`make_psc.sh` checks that on the server before fetching the binary** (`tools/check_psc_binary.sh`:
  highest `GLIBC_`/`GLIBCXX_` version needed, and no RPATH/RUNPATH - the toolchain file sets
  `CMAKE_SKIP_RPATH`, since `FindSDL2.cmake` links the sysroot's `.so` files by absolute path), and passes
  the git facts up as `AB_GIT_*` environment variables because the tree goes up without `.git`. This
  Sony-toolchain build has never run on a console; the image's gcc-6 build has (2026-09-19).

## 2019 root-cleanup history

- **Linux/macOS (native)**: `make_sys.sh` - a plain host build into `build_sys/`. (The root's 2019 leftovers
  went on 2026-09-19: the armv7 `MacToolchain.cmake`/`PS1Ctoolchain.cmake`/`PSCtoolchainV7.cmake` and
  `make_mac.sh`/`make_all.sh` - the console build is `make_psc.sh` with `toolchains/psc/` - and
  `make_english.txt.sh` (`tools/lang_tools.py extract`), `.dep.inc`, a stray `coversP.db`, `default.lic`,
  root copies of `default.png`/`pcsx.cfg` (the real ones are in `src/resources`), and `win_drive.ps1`'s
  screenshots, now ignored as `/shot*.png`.)

## libchdr refresh history

- **`libchdr`** (`#include <libchdr/chd.h>`, link `chdr`) is vendored under `lib_ableem/third_party/libchdr/` -
  upstream libchdr at `8bba774` (2025-06-08), the snapshot AutoBleem-NG bundles, replacing the older libmamecd
  fork on 2026-09-18 because chdman's default **zstd** codec was missing there (a fresh CHD would not open).
  Used only by `lib_ableem/src/engine/cd_image_reader.h` (`ChdImageReader`), which now reads hunks with
  `chd_read` and takes track 0's length from `CDROM_TRACK_METADATA(2)` - upstream has no `cdrom_*` layer.
  Builds from source on every host (its own `CMakeLists.txt` there builds the libchdr sources - FLAC is the
  header-only dr_flac - plus vendored LZMA SDK 24.05, zlib 1.3.1 and zstd 1.5.6 under `deps/`, each trimmed
  to what its CMake build needs, all warnings-off like the other vendored code). `AB_ENABLE_CHD` defaults
  ON; OFF (which sets `ABLEEM_ENABLE_CHD=OFF` / `ABLEEM_NO_CHD`) compiles `ChdImageReader` out (`.chd`
  games then scan as "no serial"). `make_win.sh` passes `-DAB_ENABLE_CHD=ON` explicitly: a `build_win/`
  configured before the library was vendored had OFF cached, and that silently outlived the default
  becoming ON - `tests/core/test_cd_image.cpp` (over the zstd-compressed `tests/data/test.chd`, NG's
  fixture) is what noticed. **pcsx-ab** (`E:\Programming\pcsx-rearmed-develop`) got the same refresh the
  same day (its `8f26911`); the Pi payload binary was rebuilt from it then, the console one
  (`payload/Autobleem/bin/emu/`, via its `make_psc.sh`) on 2026-09-18 too - both play zstd CHDs.


## SDL2 on the console: the wl_shell ceiling, in full

builds without the image). **2.0.14 is the ceiling** (verified on a console the same day, and was 2.0.12 before):
the console's compositor is Sony's Weston 1.11, which offers `wl_shell` and no xdg shell, and 2.0.14 is the
last SDL with a `wl_shell` window - 2.0.16 removed it together with `zxdg_shell_v6`, and 2.0.20+ also need
libwayland >= 1.18 (the console has 1.12; 2.0.22's configure refuses it). The Wayland protocol code is
generated by a wayland-scanner 1.12 the image builds (a newer one emits `wl_proxy_marshal_flags()`, which
1.12 lacks). What a newer SDL would take, for later: a patch bringing `wl_shell` back as a fallback (what
retroarch-psc's `wl_shell_fallback.patch` did for RetroArch 1.22), with the 1.18/1.20 libwayland symbols made
optional - the route to 2.0.22 or 2.30 and `SDL_RenderGeometry` (2.0.18), which the carousel's turned covers
already use when the headers have it. SDL2's ABI is backward compatible, so a newer libSDL2 in the archive
never needs a rebuild of the programs.

**2026-09-29: superseded.** The patch described above as future work was built: the console's SDL2 is now our
own `autobleem2/autobleem_sdl` at 2.0.18 (the `wl_shell` fallback plus two GLES2 renderer fixes), replacing
plain upstream 2.0.14 in the build image. 2.0.18 is the new ceiling for the same reason 2.0.14 was (2.0.20+
needs libwayland >= 1.18, the console has 1.12). See `docs/decisions.md` and `autobleem_sdl`'s own README.
