# RetroArch for the console (`github.com/autobleem2/retroarch-psc`)

How the PlayStation Classic gets its RetroArch, cores, libraries and stick layout, and the PC installer that
puts them there. Paths without a repository name are the launcher's.

## The build

- The console runs **our own RetroArch**, not RetroBoot's: the public repository `autobleem2/retroarch-psc`,
  merged from AutoBleem-NG's `retroarch-psc` + `libretro-cores-psc` (the NG org is gone from GitHub).
- `make retroarch` builds with the `autobleem-build` image's `/opt/psc` toolchain (Stretch gcc-6, the
  console's glibc 2.24 sysroot, our **SDL2 2.0.14**) - the compiler pcsx-ab and the launcher use. NG's
  crosstool-ng stage is kept as `make retroarch-ctng`. Stretch's freetype and liblzma are unpacked into the
  sysroot for the build, and a **wayland-scanner 1.12** is built because a newer one emits
  `wl_proxy_marshal_flags()`, which the console's libwayland 1.12 lacks.
- CPU flags are `-march=armv8-a -mtune=cortex-a35 -mfpu=neon-vfpv4 -mfloat-abi=hard`: **`neon-vfpv4`, not
  `neon-fp-armv8`**, because the PSC kernel's HWCAP advertises only VFPv3/VFPv4 although the silicon is
  ARMv8 - ARMv8 FPU instructions trap at run time.
- Patches: NG's four (wl_shell fallback, PowerVR ribbon shader, pipeline limit, ALSA S16) plus two of ours:
  - **`xz_core_loading.patch`**: `dylib_load` unpacks a core stored as an xz stream (KMFD's `km_*` cores)
    into `/tmp/retroarch-cores/` with a static liblzma and dlopens the copy, kept while path/size/mtime
    match, one core cached at a time (`HAVE_XZ_CORES=1`; the firmware has no liblzma).
  - **`psc_front_buttons.patch`**: the console's front buttons as RetroArch keys - POWER (`KEY_SLEEP`) is
    `"power"`, OPEN (`KEY_EJECTCD`) `"media"`, RESET was `"play"` already. The cfg binds RESET to
    `input_exit_emulator` (the launcher takes over) and OPEN to `input_menu_toggle`.
- Result: v1.22.2, GLIBC <= 2.22, libstdc++ static. `make package-retroarch` -> `retroarch-psc-<tag>.zip` +
  `manifest.json` (tag `v<RetroArch version>-<build>`), `make publish` -> the site's `psc/retroarch/`.

## Cores and libraries

- Cores are **not built by us yet**: the console gets RetroBoot 1.2's cores as they are. `cores/cores.txt`
  is the RetroBoot roster (81) in build-priority order, NG's 170 kept as `cores-full.txt`.
- `tools/check_cores.py` (pyelftools) checks a `cores/` folder: xz or ELF, ABI, GLIBC/GLIBCXX against the
  firmware's 2.24 / 3.4.22, NEEDED against the firmware, libretro exports, GL. Of 178 RetroBoot cores 5
  cannot load on a stock console (two need glibc 2.28/2.29, `km_emux_chip8` is x86-64, `bsnes` needs
  libgomp, `km_imageviewer` is soft-float). `tools/pack_retroboot_cores.py` packs the rest with their info
  files and a json of sizes/sha256/glibc/GL/what was left out and why -> the site's `psc/cores/`.
- The site's **libs pack** (`tools/pack_retroboot_libs.py`) unpacks into `Autobleem/lib/{apps,retroarch,modules}`
  (the Apps' libraries, RetroArch's, `xpad.ko`); our RetroArch needs nothing from it. The **apps pack**
  (`tools/pack_psc_apps.py`) holds the third-party Apps, each self-contained under `Apps/<name>/`.
- The console's BIOS manifest is `payload/RetroArch/bios/biospack.txt` (`tools/biospack.py --arch psc`:
  cores from `psc/cores/latest.json`, KMFD names folded onto RetroBIOS's via `PSC_CORE_ALIASES`, the extra
  systems only those cores cover in `PSC_SYSTEMS`).

## `retroarch.cfg` on 1.22.2

The installer's cfg fragment is the repo's `theme/retroarch-psc.cfg`. What a RetroBoot-era cfg gets wrong:

- `video_driver = "gl"`, `video_context_driver = "wayland"` (empty = KMS first, which Weston blocks),
  `input_driver = "udev"`.
- `quit_on_close_content = "2"`, or Close Content stays in XMB instead of returning to the launcher.
- `xmb_theme` 8 is Monochrome Inverted now; RetroSystem is 7.
- `menu_swap_ok_cancel_buttons = "true"` (Cross = OK) still works; a core's own menu uses the core's mapping.
- `theme/` is the **ab2 XMB theme** (wallpaper from `make_wallpaper.py`, Selawik Light, the RetroSystem icons
  plus the 19 that 1.22.2 asks for and a 2020 stick lacks).

## Running it

- `rc/launch_rb.sh <file> <core>` starts RetroArch itself - RetroBoot's scripts are not run any more:
  `NEON`/`PEOPS` map to pcsx_rearmed/swanstation, the console's PS1 BIOS is copied into `RetroArch/bios`,
  `XDG_CONFIG_HOME` is a `/tmp` dir whose `retroarch` links to `RetroArch/bin` (so favorites/history land
  there), and a non-zero exit keeps `logs/retroarch_crash.log` with dmesg and blinks the red LED - **no
  relaunch** (RetroBoot relaunched five times, ~45 s). `rc/retroarch.sh` runs it with no content.
- **Coming back**: the PSC's GPU frees the emulator's memory 3-4 s after the process exits; a launcher window
  rebuilt sooner fails its buffer uploads, Weston drops it and SDL posts a Quit. So `launchGame()` waits
  2 s after RetroArch (300 ms after pcsx), and `run()` treats a Quit on the console as a lost display:
  release, 1 s, rebuild, up to three times (`The display went away (attempt n of 3)`).
- **Splashes**: `absplash IMAGE --until-exists F | --until-gone F | --seconds S [--timeout S]` shows the
  RetroArch picture until RetroArch's log says `Found display driver` (`/tmp/.ra_up`) and the AutoBleem
  picture from its exit until the launcher's window is back (`launchGame()` removes `/tmp/.abload` after
  `display(true)`).

## The stick layout

- `Themes/`, and everything of RetroArch's under **`RetroArch/`**: `bin/` is RetroArch's own tree (binary,
  cores, info, assets, playlists, saves, `retroarch.cfg`), `bios/` its system directory, `roms/<system>/` the
  other systems' games, named as RetroArch's databases are. `psc.ini`/`pc.ini`: `retroarch_dir=RetroArch/bin`,
  `retroarch_roms_dir=RetroArch/roms`, `retroarch_bios_dir=RetroArch/bios` (the Pi's is `RetroArch/system`),
  `retroarch_core=cores/pcsx_rearmed_libretro.so`. UpdateRoms tells a console stick by its `RetroArch/bin`.
- FAT/exFAT are case-insensitive, so an old stick keeps working with `themes/`. The stick cannot hold
  symlinks: `rc/app_env.sh` links `Autobleem/lib/apps/*` into `/tmp/applib` with the soname links.

## The PC installer

`AutoBleemInstaller.exe` (`autobleem2/autobleem-pc-tools`, whose CLAUDE.md has the details) makes this layout:
it formats the drive if asked, unpacks the stick package, fetches what was ticked, names the stick **SONY**,
and on a second run **updates** it, keeping the user's files. It converts an AutoBleem 1.0 / NG / RetroBoot
stick first (`LegacyLayout`, which also renames the ES-style ROM folders to the database names).

## Still open

- Build the console's cores ourselves (`cores/cores.txt`, 81 cores; estimated ~a day on the 2-core server,
  not measured) instead of shipping RetroBoot 1.2's.
- N64 has not been tested with a real game (the homebrew RSP tests crash GLupeN64 inside the core).
- Anything else left for the console's RetroArch is in `docs/todo.md`.
