# Console hardware-run debugging tales

Moved verbatim out of the launcher's CLAUDE.md on 2026-09-26 (task D19).

## The 2026-09-19 CI image console pass

  (37/37 tests, format, tidy), packages inspected. **Run on a console
  2026-09-19**: the psc package's launcher, `libs.tar.gz` and pcsx-ab went onto the owner's stick (the
  previous set kept in `E:\tmp\stick-prev`), and the launcher started with all covers - the first hardware
  run of any console build of this repo. Two bugs the console then showed, both fixed the same day: pcsx-ab
  segfaulted at its first frame (its Wayland branch never set `SDL_SysWMinfo::version`, so SDL 2.0.6+'s
  "Version must be 2.0.6 or newer" check failed on uninitialised stack - a coin the gcc-8 build won and the
  gcc-6 build lost; pcsx-ab2 `70c5dcb`), and no sound anywhere (the Dockerfile's linker-script rewrite had
  truncated the sysroot's `libasound.so`, so SDL2 was built without ALSA; `ab-validate psc` now checks the
  audio backends). `rc/launch.sh` writes `System/Logs/launch.log` + `pcsx.log` since then - that is how
  both were read. A stock-firmware console also needs RetroBoot 1.2's `retroarch` (the vendored bundle);
  a RetroBoot 1.1 tree with a later KMFD build wants GLIBC_2.28 and never starts (see `retroarch/logs/`).
  What the image's compilers turned up: the console's gcc-6 cannot combine an inherited constructor with a
  member initialised from another member (`GuiLauncher` now spells its constructor out - keep it that way
  for every screen), and the test fixture's scratch dirs now carry the pid (`ctest -j` runs suites in
  parallel; same label + counter in two processes deleted each other's trees). Editing the root
  CMakeLists' console branch: a GCC < 8 gets `-march=armv8-a -mfpu=neon-vfpv4` (it used to get armv7ve,
  no NEON - a branch that had never been compiled).
