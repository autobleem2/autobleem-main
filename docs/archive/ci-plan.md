# CI: one Docker image that builds every target

Archived plan (done 2026-09-19). The full text is in git history: `git log -- docs/archive/ci-plan.md`.
The pipeline around the image was replaced on 2026-09-23 (`ci-org-migration-plan.md`, `docs/ci.md`); the
image itself is `autobleem2/autobleem-build`.

## Why the console builds on Stretch with gcc-6

The console runs glibc 2.24 / libstdc++ 6.0.22 - Debian Stretch's. So the honest sysroot is a Stretch armhf
one (`mmdebstrap --variant=extract` from archive.debian.org) with Stretch's own gcc-6 cross compiler, the
newest whose libstdc++ the console can load. AutoBleem-NG's recipe; the owner dropped the 2019 Sony
crosstool-NG toolchain as outdated. Building the SDL2 family from source in the image makes `libs.tar.gz`
reproducible from pinned public sources. Not taken from NG: its hijack of the host's
`/usr/arm-linux-gnueabihf` (Debian's Pi cross libc lives there) - the gcc-6 binaries get a `patchelf`
RUNPATH and their libc linker scripts are rewritten to bare names instead.

## The image's toolchain stages

1. **psc** - the Stretch sysroot + gcc-6 under `/opt/psc`, a wayland-scanner 1.12, SDL2 (now 2.0.14) +
   image/mixer 2.6.3 + ttf 2.20.2 built with the console's backends (Wayland + dummy, GLES via EGL, ALSA,
   udev; no X11/OSS), wrapped as `armv8-sony-linux-gnueabihf-*` so `PSCtoolchainV8.cmake` works unchanged.
2. **rpi / rpi64** - Debian's `crossbuild-essential-armhf`/`-arm64` with the multiarch `libsdl2*-dev`
   packages (Bookworm, glibc 2.36: loads on Bookworm and Trixie); no SysGCC.
3. **mingw** - mingw-w64 *posix* threads with the official SDL2 mingw devel packages in `/opt/mingw-sdl2`.
4. **native** - the host build with clang-format/clang-tidy 22 from apt.llvm.org, major-pinned to MSYS2's
   so `format.sh --check` agrees on both.
5. **pcusb** (added 2026-09-20) - `crossbuild-essential-i386` + SDL2:i386; the suites run as i386.

The cover databases were a `db` stage (now fetched from the site's `db/`). The tree is never in the image:
it is bind-mounted and built as the calling uid.

## What `ab-validate` gates (end of each stage)

A C++14 + SDL test program must link and fit the target. For the console: ARMv8, nothing above GLIBC_2.24 /
GLIBCXX_3.4.22, no RPATH, an SDL2 that is 2.0.12/2.0.14 with Wayland and ALSA and without X11 or OSS (the
ALSA check came after a truncated `libasound.so` built an SDL2 with no sound). For the Pis and pcusb: the
right ELF class and architecture (pcusb's test is executed).

## Still open

- `wine64` in the image to run the doctest suites for the `win` target as well (Windows-only paths).
