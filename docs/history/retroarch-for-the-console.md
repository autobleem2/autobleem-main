<!-- Moved from the launcher's CLAUDE.md (autobleem2/autobleem) on 2026-09-23 when the project's
     knowledge went to autobleem-main. Paths without a repository name are the launcher's. -->

# RetroArch for the console (`github.com/autobleem/retroarch-psc`, 2026-09-19/20)

The console runs RetroArch from **our own build**, not RetroBoot's any more - a separate private repo,
`autobleem/retroarch-psc` (`E:\Programming\retroarch-psc`), merged from AutoBleem-NG's `retroarch-psc` +
`libretro-cores-psc` (the NG org and its repos are **gone from GitHub**; the owner's zips in Downloads were
the source). One Dockerfile with NG's crosstool-ng toolchain stage (kept as `make retroarch-ctng`, the
cores' route), but **`make retroarch` builds with the `autobleem-build` image's `/opt/psc` toolchain**
(`retroarch/build.sh`: Stretch gcc-6 + the console's glibc 2.24 sysroot + our SDL2 2.0.12 - the compiler
pcsx-ab and the launcher use; Stretch's freetype and liblzma .debs unpacked into the sysroot for the
container's life; a **wayland-scanner 1.12** built from Stretch's tarball because the image's 1.21 emits
`wl_proxy_marshal_flags()`, which the console's libwayland 1.12 lacks). NG's four patches (wl_shell
fallback, PowerVR ribbon shader, pipeline limit, ALSA S16) plus **ours, `xz_core_loading.patch`**:
`dylib_load` unpacks a core whose file is an xz stream (KMFD's `km_*` cores, 147 of the owner's 178) with
liblzma into `/tmp/retroarch-cores/` and dlopens the copy - kept while the source's path/size/mtime match,
one core cached at a time (`HAVE_XZ_CORES=1`, `-l:liblzma.a`, the firmware has no liblzma). Result: v1.22.2
`autobleem-<build>`, 10.4 MB stripped / 3.4 MB UPX'd, GLIBC <= 2.22, libstdc++ static, 17 firmware
libraries; tag `v1.22.2-1`, `make package-retroarch` -> `retroarch-psc-<tag>.zip` + `manifest.json`
(`tools/make_manifest.py`, what the PC installer will read), `make publish` -> `psc/retroarch/` on the
download repository. **Ran on the console 2026-09-20**: XMB, the PSC pad autoconfig, Wayland/EGL/GLES 3.2
hw context, ALSA, the xz unpack - all in `retroarch/logs/retroarch.log`. GitHub Actions is written but
gated off (`CI_ENABLED`); the owner builds on the server only.

**Cores**: not built by us yet - `cores/cores.txt` is the RetroBoot roster (81) in build-priority order,
NG's full 170 kept as `cores-full.txt`; the estimate for building the 81 on the 2-core server is ~a day
(guessed from source sizes, not measured). **For now the console gets RetroBoot 1.2's cores as they are**:
`tools/check_cores.py` (pyelftools) reports a `cores/` folder - xz or ELF, ABI, GLIBC/GLIBCXX against the
firmware's 2.24/3.4.22, NEEDED against the firmware, libretro exports, GL; on the owner's stick 173 of 178
load in any RetroArch (5 cannot on a stock console: two need glibc 2.28/2.29, `km_emux_chip8` is an x86-64
build, `bsnes` needs libgomp, `km_imageviewer` is soft-float). `tools/pack_retroboot_cores.py` (`make
pack-retroboot-cores RETROBOOT_DIR=F:/retroarch`) packs the 171 + their info files + `cores-psc-<date>.json`
(sizes, sha256, glibc, GL, display names, and what was left out and why) -> `psc/cores/`. How RetroBoot
injects libraries, for the record: `LD_LIBRARY_PATH=retroboot/lib` (liblzma + a GLIBCXX 3.4.25 libstdc++)
for every RetroArch launch, `retroboot/assets/lib` -> `/tmp/rblib` for EmulationStation and the apps; none
of the cores needs either. Its `launch_rfa_rom.sh` relaunches RetroArch **five times** on a non-zero exit
(the blinking red LED, ~45 s) before returning to the launcher - our own launch scripts should give up
after one.

**What a RetroBoot-era `retroarch.cfg` gets wrong on 1.22.2** (all in the repo's `theme/retroarch-psc.cfg`,
the installer's cfg fragment): `xmb_theme = "8"` was RetroSystem in 1.9.0 and is Monochrome Inverted now
(RetroSystem is 7); `quit_on_close_content` (new since 1.10, default never) must be `2` or Close Content
stays in XMB instead of returning to the launcher as 1.9.0 did; `video_context_driver` must be `wayland`.
`menu_swap_ok_cancel_buttons = "true"` (Cross = OK in RetroArch's menus) is unchanged and works - a
core's own menu is the core's mapping (prboom: RetroPad A = Circle = enter), not RetroArch's. `theme/` in
the repo is the **ab2 XMB theme** for 1.22.2: `Autobleem2.png` (made by `make_wallpaper.py` from `payload/Themes/ab2/images/AB-EvoBack.jpg`
- logo bottom right, out of XMB's way, the bottom band a reflection of the texture), Selawik Light, the
RetroSystem icons (a 2020 RetroBoot stick lacks 19 that 1.22.2 asks for - `disc.png`, `movie.png`, `Sega -
Mega Drive - Genesis.png`, ... from libretro's retroarch-assets), `retroarch-theme.cfg` with the 1.22.2
keys. `video_context_driver` must be `"wayland"` (empty = KMS first, which Weston blocks). All of this is
on the owner's F: stick (the RetroBoot binary kept as `retroarch.retroboot-1.9.0`, the cfg as
`retroarch.cfg.retroboot`) with free test content in `roms/` (Peter Lemon's SNES/NES/GB/GBA homebrew,
mamedev's free arcade ROMs, Doom/Quake shareware, Cave Story); N64 needs a real game - the homebrew RSP
tests crash GLupeN64 (a core dump inside the core, not RetroArch). **Verified on the console 2026-09-20**:
Cave Story, Doom, Quake run and return.

**Coming back from RetroArch** (2026-09-20): the PSC's GPU frees the emulator's memory 3-4 s after the
process is gone; the launcher's window rebuilt sooner had its buffer uploads fail (`PVR: glBufferSubData:
No memory for object data` in `AB_err.txt`), Weston dropped the client (`wl_display@1: error 0: invalid
object 16`), SDL posted a Quit and `AutoBleem::run()` took it for the window's close button - out through
`selection.sh`'s reboot (what looked like the console going to sleep). Now `launchGame()` waits 2 s after a
RetroArch session (300 ms after pcsx) and `run()` treats a Quit on the console as a lost display: release,
1 s, rebuild, three times before giving up (after Quake it took two rebuilds; the log says
`The display went away (attempt n of 3)`).

**The splashes around RetroArch** (2026-09-20): `absplash` (`src/tools/absplash.cpp`, lib_ableem's ui
only, shipped packed next to the launcher with `src/resources/splash/{retroarch,autobleem}.jpg`) shows a
picture in the same full-screen window the launcher and RetroArch use - `absplash IMAGE --until-exists F |
--until-gone F | --seconds S [--timeout S]`. On the stick RetroBoot's `launch_rfa_rom.sh` (patched by hand,
copy at `E:/tmp/launch_rfa_rom.sh.ab2` - the model for our own launch script) runs it: the RetroArch
picture from launch until RetroArch's log says `Found display driver` (+1 s, `/tmp/.ra_up`), the AutoBleem
2 picture from RetroArch's exit until the launcher's window is back - `launchGame()` removes
`/tmp/.abload` after `display(true)`; `rc/launch_rb.sh` no longer does. **The reason nothing showed for a
day**: the stick's `retroboot/retroboot.cfg` had `show_splash=0` (RetroBoot's own setting; the backup
copy had 1) - the splash functions never ran. RetroBoot's rbimage/abimage (a 1280x720 toplevel window,
a 200x200 BMP at (540,260)) are replaced, not fixed. Verified on the console.

**The stick's layout, and our own launch scripts** (2026-09-20, the owner's cleanup of the F: stick - the
final structure the PC installer makes): `Themes/` (was `themes/`), and everything of RetroArch's under
**`RetroArch/`** - `bin/` is RetroArch's own tree (what was `retroarch/` at the root: the binary, cores,
info, assets, playlists, saves, `retroarch.cfg`, and RetroBoot's leftover `retroboot/` and `apps/`
folders, unused), `bios/` its system directory (was `retroarch/system`; `retroarch.cfg`'s
`system_directory`), `roms/` the other systems' games (was `roms/` at the root). `psc.ini`/`pc.ini` say
`retroarch_dir=RetroArch/bin`, `retroarch_roms_dir=RetroArch/roms`, `retroarch_bios_dir=RetroArch/bios`
(`Env::getPathToRetroarchBiosDir()`; the Pi's is `RetroArch/system`), `retroarch_core=cores/pcsx_rearmed_libretro.so`
(`km_pcsx_rearmed_neon` never existed on a RetroBoot 1.2 stick); the engine's defaults are the same, and
`UpdateRoms` tells a console stick by its `RetroArch/bin`. FAT/exFAT are case-insensitive, so an old stick
or card keeps working with `Themes`. **RetroBoot's scripts are not run any more**: `rc/launch_rb.sh <file>
<core>` starts RetroArch itself (`NEON`/`PEOPS` -> pcsx_rearmed/swanstation as RetroBoot mapped them; the
tree's directories and the console's PS1 BIOS into `RetroArch/bios` first; `XDG_CONFIG_HOME` is a `/tmp`
dir whose `retroarch` is a symlink to `RetroArch/bin`, so the cfg's "default" directories - favorites,
history - land there as RetroBoot's `XDG_CONFIG_HOME=/media` put them in `retroarch/`; the absplash
pictures; a non-zero exit keeps `logs/retroarch_crash.log` with dmesg and blinks the red LED four times,
**no relaunch**), `rc/retroarch.sh` runs it with nothing loaded and restarts AutoBleem, `rc/app_env.sh` is
what an App's `run.sh` sources (links `Autobleem/lib/apps/*` into `/tmp/applib` with the soname links -
the stick cannot hold symlinks - and exports `LD_LIBRARY_PATH`; RetroBoot's `init_libs.sh`), `boot.sh`
insmods `Autobleem/lib/modules/*.ko` (xpad), `launch_rb.sh` puts `Autobleem/lib/retroarch` on RetroArch's
path when present (our build needs nothing from it). `Autobleem/lib/{apps,retroarch,modules}` is the
site's **libs pack** unpacked (its groups are named so). **The Apps**: `payload/Apps` keeps only pscbios and
abflashkit; the eight third-party apps (amiberry, doom, eduke32, openbor, opentyrian, sdlpop,
shadowwarrior, wolf4sdl) are the site's **apps pack** (`tools/pack_psc_apps.py F:/Apps`), each
self-contained under `Apps/<name>/` - the RetroBoot-era ones had their binaries in `retroarch/apps/<name>`
and got them moved in, their scripts pointed at `/media/Apps/<name>`, `/media/System/Logs` and
`app_env.sh`. `Apps/retroboot` (RetroBoot's own menu as an app) is gone - the system menu's RetroArch item
is that. **`tools/install_autobleem.py --stage layout`** converts an older stick in place (renames, moves,
`retroarch.cfg` and every playlist's paths, `Applications.lpl` removed, the libraries copied out of
`retroboot/`, the apps made self-contained) and is idempotent; it ran on the owner's stick, then the new
launcher, `absplash`, the tools, the platform inis, the rc scripts and `UpdateRoms.exe` (which wrote
`/media/RetroArch/roms/...` playlists) went on. **Verified on the console 2026-09-20** (the owner: "looks like it works ok").
`payload/RetroArch/` is the folder's skeleton (README files) plus **`bios/biospack.txt`**, the console's
BIOS manifest: `tools/biospack.py --arch psc` takes the cores from `psc/cores/latest.json` (KMFD's
`km_<core>_xtreme...` names folded onto RetroBIOS's - `PSC_CORE_ALIASES`), adds the systems only those
cores cover (`PSC_SYSTEMS`: Saturn, Dreamcast, DS, PC-FX, Atari ST, CPC, PSP, DOSBox, NXEngine, xrick) and
keeps `dc/` - 719 files, 302 MB against the Pi's 647/188. `.gitignore`'s `bios/` rule has an exception for
that folder's two files.

**The PC installer exists** (2026-09-20, `apps/installer/`, its own CLAUDE.md): `AutoBleemInstaller.exe`,
a Win32 program like UpdateRoms with the Pi first-boot screen's look (the splash picture on top, the
questions as checkboxes, then two progress bars and the log), shipped as `AutoBleemInstaller-<v>.zip` with
the release's `autobleem-psc-<v>.tar.gz` next to it (`tools/make_installer_bundle.sh <tarball>`; `PACKAGE_KINDS`
"installer" on the site, INDEX_VERSION 21). It picks a removable drive (formats it FAT32/exFAT through
`format.com`, or `fat32format.exe` beside it for FAT32 over 32 GB), unpacks the tarball, fetches the ticked
cover databases (all three by default), RetroArch with cores/libs/apps/libretro bundles (off by default),
the BIOS files by `psc/bios` (needs RetroArch), the samples; run again it **updates** - the package's own
files replaced, everything of the user's kept, `config.ini` too - and an **AutoBleem 1.0 / NG stick is
brought to the new layout first** (the `layout` stage's steps in C++, `legacy_layout.*`; RetroBoot's
playlists dropped for the launcher's scan to rebuild). The engine got `TarArchive` (`.tar.gz` through
miniz, `tests/support/tar_builder.h` writes them for the tests), `PackCatalog`/`PscRetroArchCatalog` for
the `psc/*/latest.json` shapes and `DirEntry::createDirs`; `DirEntry::copyFile` had returned the opposite
of what it did (no caller until now). Verified on the PC over the real site into a folder (covers in 25 s;
RetroArch + all 719 BIOS files + samples, 1.7 GB); **not yet on a real stick or the console**.

**The installer ran on the owner's stick and the result booted** (2026-09-20). Since then it also puts
**UpdateRoms** on the stick (a phase after the unpacking: `releases/unstable.json` / `latest.json`, the
release whose `psc-fs` is this package, its `updateroms` zip into `<stick>/UpdateRoms/`; missing = a
line, not a failure) and **names the stick SONY** (`ensureVolumeLabel`, the status line says so). What is
left is in `TODO.md`.

**Three tester reports fixed** (2026-09-23; the installer's release source is `autobleem2/autobleem-pc-tools`,
`apps/installer` here is kept identical): the per-system `RetroArch/roms/<system>/` folders are made from the
package's `platform/roms_systems.cfg` whenever RetroArch is chosen or on the stick, on updates too, only the
missing ones (`InstallJobBase::createRomFolders`, shared with the Windows job, which already did it); an
AutoBleem 1.0 / RetroBoot stick's ES-style ROM folders (`nes`, `snes`, `megadrive`, ...) are renamed to the
RetroArch database names the scan reads (`LegacyLayout::convertRomFolders`, the port of
`install_autobleem.py`'s `ROMS_LAYOUT_MAP` - merge when both exist, case-only renames through a stop for FAT),
on every install so a stick an older installer converted is fixed too; and **UpdateRoms** comes from an
`UpdateRoms/` folder beside the installer first (the bundle carries it since alpha2 - same release, no
network), the site's otherwise, unpacked in scratch and swapped in only when complete - it used to be deleted
before the new one was unpacked. Every run writes `<stick>/System/Logs/installer.log`.

