# The 2026-09 core/ab_ui/ab_evoui refactor

How the original monolithic `Gui` god object became `ab_core` / `ab_classic` / `ab_ui` / `ab_evoui`, phase by phase. Moved verbatim out of the launcher's CLAUDE.md on 2026-09-26 (task D19) to keep that file to what a developer needs today; this is the record of how it got there.

## Current work (2026-09)

Refactor for stability, then add features. Done on 2026-09-15 (one commit per step, see `git log`):

- Phase 0: Windows/MinGW dev build (`make_win.sh`), `AB_DEBUG_HOST` macro, keyboard-as-gamepad, `tools/win_drive.ps1`.
- Phase 1: no uncaught exceptions (playlist JSON, `stoi`, `popen`), `Util::runAndWait` for every fork/exec,
  SDL subsystem lifecycle (`TTF`/`Mix` init once, `SDL_Quit` via `atexit`), unit-buffered logs.
- Phase 2: `database.cpp` uses a local RAII `Stmt` wrapper (no leaked statements, NULL-safe columns, rollback).
- Phase 3: no raw owning `new`/`delete` left: stack objects for short-lived helpers and screens, `unique_ptr`
  for DBs, interceptors, `GuiLauncher` elements, pads, memory-card editors.
- Phase 4: `DirEntry::checkWritable` on every writer, `-Wall -Wextra` clean debug builds.
- lib_ableem: every SDL/SDL_image/SDL_mixer/SDL_ttf/SDL_FontCache call moved out of the app into a new static
  library, `lib_ableem/` (namespace `ableem`). The app links `ableem` and includes no SDL header anywhere;
  `grep -rl "SDL2/" src/code` returns nothing. See the "lib_ableem" section below.
- lib_ableem/engine: the SDL-free half of the app (filesystem, strings, ini/cfg files, the SQLite game
  database, cover dbs, disc image inspection, the scanner, RetroArch playlists, vendored sqlite/json/unecm)
  moved into a second target, `ableem_engine`, under `lib_ableem/include/ableem/engine/`. Every path the
  engine uses comes from `ableem::Environment` (set once in `main.cpp`); the engine has no idea what a Gui
  is (scan progress goes through `ScanProgressListener`). Verified byte-identical scan output before/after.

Done on 2026-09-16:

- The `Gui` god object is being split into a model (`App`) and a screen (`Gui`). `App` (`src/code/app.*`) was
  `main.cpp`'s loose free functions and globals; it owns the `Session` (`core/model/session.h`), the game
  library, the scanner, and now everything on the old `Gui` that was not graphics: `Config` (config.ini),
  `Theme` (the merged, resolved theme.json) and `AppAudio` (music + the five UI sounds).
  Screens reach them as `app.config()`, `app.theme()`, `app.audio()` through the `app` member of `GuiScreen`;
  the handful of non-screens (`Fonts`, the launcher's metadata panel) use `App::get()`.
  `Gui` is left with the window/renderer, `assets()`, `text()` and the background/logo/status drawing
  (phase C, 2026-09-16).

The next structural step (its plan was `docs/refactor-plan.md`, removed once every step was done - the git
history has it) was to split `src/code` into `ab_core` (model +
services, no SDL, unit tested with doctest), `ab_ui` and `ab_evoui`, moving the game queries, settings,
memcard/savestate and launch logic out of the screens that currently hold them. The list below is folded into
that plan's phases. Phase A is done apart from step 3 (the ARM build), which is deferred - no toolchain on
this host yet:

- **Step 1** - the `#define`-int selections are `enum class`es now: `GameSet` (+ `nextGameSet` for the Select
  wraparound) and `Ps1SelectState` in `session.h`, `LauncherScreenState` in `gui_launcher.h`, and the
  `LauncherMenuOption` in `gui_launcher.h`. `PsMenu::selOption` stays an `int` - it is a
  generic index into the icon row that `PsMenu` animates by `++`/`--` - and is compared through
  `selOptionIs()`. `EmuMode` and `MenuOption` were already enums.
- **Step 2** - `ab_core` exists (`src/code/core/`, links `ableem_engine` only).
  It held `main.h`, `environment.*`, `util.*`, `lang.*`, `DebugTimer.*`, `services/config.*` and
  `model/timing.h` at first; on 2026-09-16 the top level was cleared down to `main.h`. It is deliberately small: only files with no `Gui` and no `App::get()` could move without
  a content change.
- **Step 4** - the test harness (step 3, the ARM build, is deferred - no toolchain on this host). doctest
  2.4.11 vendored at `tests/third_party/doctest/doctest.h`, `tests/support/{env_fixture.h,temp_dir.*}`,
  ctest wiring behind `AB_BUILD_TESTS` (ON for hosts, forced OFF by the cross toolchain files), and the first
  suites: `tests/core/test_config.cpp` and `tests/core/test_env_fixture.cpp`. `make_win.sh` runs `ctest`
  after every build. `Theme` was to be tested here too, but it is not in `ab_core` yet.
- **Step 5** - `core/model/game_set.h` holds `GameSet`, `Ps1SelectState` and `GameSetSelection` (tested in
  `tests/core/test_game_set.cpp`). `Session::LauncherState` is gone: `Session::launcher` is a
  `GameSetSelection`, and `GuiLauncher`'s six `current*` mirror fields are one `selection` member that
  `loadAssets()` seeds and `GuiLauncher::rememberSelection()` writes back. Careful: the PS1 sub-set is
  deliberately **not** carried across while another set is showing - see the comment on
  `rememberSelection()`; it is a pre-existing quirk, flagged in the plan, not a fix waiting to happen.

Phase B has started. `GameQueryService` (`core/services/game_query.*`) owns every "which games does this
set show" question: `GuiLauncher::switchSet()` now calls `app.gameQuery().gamesFor(selection)` and does
carousel work only. RetroArch is reached through the `RetroArchGames` interface that `RetroArchService`
implements (and a test stub can). `PsGame` moved to `core/model/` to make that
possible - `setMemCard` is split into `PsGame::setMemCardInGameIni()` (Game.ini, in core) plus an explicit
`library().usbGames().updateMemcard()` at the two interceptor call sites, until step 8 reunites them.

`GameCatalogService` (`core/services/game_catalog.*`) is the write side: `recordGamePlayed()` (the history
is a 1..100 ranking, renumbered across USB *and* internal games on every launch, in one transaction),
`deleteUsbGame()` / `removeSaveStateFolder()` (a `!SaveStates` folder can be shared, so the caller confirms
before the second call) and `flushAllCovers()`. Favorite toggling is still in `GuiEditor` - it is one of six
identical `gameIni` blocks there and moves with the rest at step 9.

`MemcardService` (`core/services/memcard.*`) owns the `!MemCards` sets and which one a game plays with:
`activeCardName()`, `setCardForGame()` (Game.ini + regional.db together again), `swapInForLaunch()` /
`swapOutAfterLaunch()` - the halves both interceptors used to duplicate - and the create/list/rename/remove
the memory-card screens use. Nothing outside it constructs an `ableem::MemcardManager`.

`ResumePointService` (`core/services/resume_point.*`) owns the save-state slots in a game's `ssFolder` -
**`Games/!SaveStates/<game folder name>/`** (internal games: `/<id>/`), central since 1.x and keyed by the
folder's *name*, so a game moved into a sub-folder keeps its states and its own card (2026-09-21, see
autobleem-main's `docs/archive/legacy-1x-analysis.md`) - `slotIsActive`/`pictureForSlot`/`lastPicture`/`storePictureForSlot`/`removeSlot`/
`exitedCleanly`, plus `prepareForLaunch`/`saveAfterLaunch` that the PCSX interceptor used to hold. Its
header documents the file layout. Two naming quirks callers depend on: slot 0's picture has no number in
its name, and `lastPicture()` uses slot 0's picture name whichever slot it finds.

`GameSettingsService` (`core/services/game_settings.*`) is what the game editor edits: `open(game)` gives a
`GameSettings` (the game's Game.ini as an `IniFile` - filled in from the record for an internal game, which
has no file - plus the nine `pcsx.cfg` values), and one setter per editor option writes it back with the
encoding PCSX expects (0/1 flags decimal, levels hex, every `!SaveStates` copy via `ConfigFileEditor`).
The favorite/play-using-RA toggles live here (Game.ini for USB, internal.db for internal). `GuiEditor` is
now only the screen: callers set `gameData` and `show()`.
**A game's PCSX config has one source** (2026-09-24, `PcsxConfig`, `core/services/pcsx_config.*`): the
launcher's pcsx.cfg, or - once an emulator's menu saved "Save settings for this game" - the game's own
`!SaveStates/<folder>/.pcsx/pcsx.custom.cfg`, which both emulators load over pcsx.cfg and are the only
writers of. `PcsxConfig::value()` is what the launch and the editor read (the custom line first);
`GameSettings::custom` makes every setter a no-op and the editor greys its Video/Emulator rows behind an
"Unlock the settings" row (`GameSettingsService::unlock` deletes the file). A legacy `autobleem.cfg` /
`cfg/<label>-<id>.cfg` (the retired "Save AutoBleem config") becomes the custom file on open or launch
(`migrateLegacy`, the newest wins), and edits no longer touch `cfg/*.cfg`.

`LaunchService` (`core/services/launch.*`) is a game launch start to finish - what `App::launchGame` and
the three `EmuInterceptor`s (PCSX, RetroArch, Apps) did between them: `writeSelectionScript()`, then
`launch(game, mode, resumePoint)` picks the path from the game and the mode, swaps the memory cards in,
prepares the resume point, builds the argv for `rc/launch.sh` / `rc/launch_rb.sh` (or an App's own
`startup`), runs it through a `ProcessRunner`, and swaps the cards back out. `ProcessRunner`
(`core/services/process_runner.h`) is the one interface introduced purely for testability: `ForkProcessRunner`
is `System::runAndWait`, the dev host installs a `SplashProcessRunner` from `App` (which is where the old
`#ifdef AB_DEBUG_HOST` in each interceptor went), and the tests pass a recording fake. The launcher script
and RetroArch paths come from `Env` now (`getPathToRCDir()`, `getPathToRetroarchDir()`), not literals.
`session.h` moved to `core/model/` with it.

**`PsGame` is now a data record** - `ableem::GameRecord` plus the launcher-only fields and
`fromRecords()`, and nothing else. No filesystem, no `App`, no `Gui`.

**`ab_ui` and `ab_evoui` exist** (2026-09-16, after phase C step 14 broke the `menuSelection()` ->
`GuiLauncher` cycle). `App` is the model at the top of `ab_ui` - every screen's `app` member - and takes its
`ProcessRunner` from whoever constructs it; `AutoBleem : App` (`src/code/autobleem.*`, in the executable) adds
`run()`, the runner choice (fork on the console, splash on a dev host) and owns the outer loop.
`ClassicMenuScreen` is in the executable too, being the one screen that shows both the classic sub-screens and
the launcher. The linker now enforces: core knows no SDL, ab_ui knows no launcher, ab_evoui knows no `main`.

Nothing core-shaped is left outside `core/` (2026-09-17): `Theme` and `Clock` (was `UtilTime`) are core services
taking `Config&`; the `Scanner` singleton is gone - `AutoBleem` makes a `GameScanner` with a `SplashScanProgress`
listener (`gui/scan_progress.*`); `AppAudio` is `gui/app_audio.*` with `Config&`/`Theme&`; and `CardEdit` split into
`ableem::MemcardImage` (the engine, tested) plus a texture wrapper in `evoui/card_edit.*`. `src/code/engine/` no
longer exists.

**Phase C has started.** `TextRenderer` (`gui/text_renderer.*`, step 12) is the text half of the old `Gui`:
the `|@X|` token layout, `renderText*`/`renderSelectionBox`/`renderLabelBox`, the opscreen/text rects and
the `getR/G/B` colour parsing. Screens reach it as `gui->text()`. `ThemeAssets` (`gui/theme_assets.*`,
step 13) is the other half: the theme's font and font sets, the background/logo/jewel textures and the
button-marker textures, with `load()` reading them for whatever theme config.ini names; screens reach it as
`gui->assets()`. `Gui` keeps `loadAssets()` (assets + the theme's music) and the background/logo/status
drawing that combines assets and text. `ClassicMenuScreen` (`gui/screens/gui_classic_menu.*`, step 14) is the old
`Gui::menuSelection()` as a screen: `App::run()` shows it, it sets `session().menuOption` and closes, or shows
a sub-screen and restarts itself where the old code recursed. `gui.cpp` is 182 lines.

The three bugs the phase B extractions pinned were each fixed in their own commit on 2026-09-16: the
memcard fallback guard, `ConfigFileEditor`'s prefix matching (a key now has to be followed by whitespace or
`=`), and RetroArch launches not recording last_played (they do, for library games only).

**Phase B is complete.** `RetroArchService` (`core/services/retroarch.*`, step 11) is the old `RAIntegrator`
singleton as an `App`-owned service: reads `retroarch/info/*.info` and `retroarch/playlists/*.lpl` on first
use, resolves each entry's core (its own if installed, else `resources/platform/<platform>.cores.cfg`, else the first
`.info` listing the playlist's database), keeps Favorites/History after the platforms and refreshes them
after a RetroArch run (`reloadFavoritesAndHistory()`). `escapeName()` is the boxart file name rule.

Still to do, in order:

1. ~~Continue the refactor plan - phase B, the service extractions~~ - done (see above); the rule stays: a
   service extracted from a screen ships with its tests in the same commit and moves into `ab_core`.
2. ~~Centralize the hard-coded paths in `Env`~~ - done (2026-09-18). The engine side, the theme loaders, the
   launch scripts and RetroArch paths (`LaunchService`) and `backup_internal.sh` went first; the last one,
   `config.ini`'s `Cfg=` key (the selection script as an absolute console path, which the Pi installer had
   to rewrite per install), is gone: `LaunchService::selectionScriptFile()` is `<runtime>/autobleem_cfg.sh`
   (was `<rc>/` until the quiet-stick work of 2026-09-24), and
   `Config` drops a stale `cfg` key on load. `EnvironmentSetup` (core) and `main.cpp`'s `/autobleem` check are the only places left that
   spell a console path; `RetroArchService::mapPlaylistPath()`'s `/media` is the
   console playlist *format*, not this machine's layout.
3. ~~Split `GuiLauncher`~~ - done (phase D, 2026-09-16). **The refactor plan is complete.**
4. ~~Set up the Sony ARM toolchain~~ - done 2026-09-17: `make_psc.sh` builds on the remote server (see Build).
   `autobleem-gui` cross-compiles and links cleanly with the Sony GCC 8.2 toolchain. Superseded on
   2026-09-19 by the Docker image's Stretch/gcc-6 toolchain (see "CI" under Build), and **that build has run
   on a console**: the launcher came up on the owner's PSC (stock kernel, a FAT32 stick) with every cover in
   place, PS1 and RetroArch alike. **The full console pass happened on 2026-09-19** (a stick made in a
   Claude Desktop session, the owner at the console): after the two fixes noted under Build, sound (ALSA),
   a PS1 launch through the image's pcsx-ab and back, a Mega Drive game in RetroArch (RetroBoot 1.2) with
   the RetroArch set from playlists the offline ROM scan wrote on the PC (`UpdateRoms.exe` - the console
   itself never fetches), and both console tools (pscbios, abflashkit) from the system menu - all as
   expected. The console is no longer the untested target.
5. Features. Done on 2026-09-17: **themes are `theme.json`** (`docs/theme-format.md`). `ableem::ThemeSpec` is
   the typed theme (engine, JSON in/out, partial-over-default merge, per-file fallback), `ThemeConverter`
   (`core/services/theme_converter.*`) turns an old `theme.ini` + PSC-data-tree folder into the new layout in
   place - `Theme::load()` does it on first contact, `tools/theme_convert` ahead of time - and `payload/Themes`
   ships converted (aergb 334 -> 29 files). The stock SonyUI is no longer re-skinned (`rc/selection.sh`), and
   `src/resources/sony/` is just the two SST fonts. **The console tools are in the tree** (2026-09-18,
   `apps/`, see "Console tools"): pscbios and abflashkit build with the launcher, draw with its theme and
   run on Windows against fakes; `psctools/` (the 2020 sources) is deleted, the import commit has them. Screens read `app.theme().classic()/launcher()/sounds()`.
   A theme can also be dropped in as `<name>.zip`: `ThemeInstaller` (`core/services/theme_installer.*`)
   unpacks it to `<name>/` at `Theme::load()` / the Options theme list, over `ableem::ZipArchive` (vendored
   miniz, read-only, `lib_ableem/third_party/miniz/`).
6. Straight into EvolutionUI, with the scan in the background. Done on 2026-09-17 (plan at
   `C:\Users\Artur Jakubowicz\.claude\plans\lets-plan-some-feature-synchronous-feather.md` if that path is
   still around; otherwise this entry and the source map are the record). Four steps:
   - **Step 1** - `GamesFingerprint` (`lib_ableem/engine/games_fingerprint.*`): a snapshot of the games
     directory keyed by path + file size, deliberately **no mtime** - the PSC has no battery-backed clock,
     so a stored modification time cannot be trusted to stay put across a reboot (see
     `DirEntry::fileSize()`'s comment). `ScanProgressListener` gained `done`/`total` on `onScanProgress` and
     two new per-game callbacks, `onGameVerified`/`onGameFailedVerify`. `GameScanner::writeRegionalDatabase`
     split into `writeSubDirRows`/`writeAutobleemList`, both keyed by a caller-supplied id-by-path map - the
     class no longer assigns game ids itself. `GameDatabase` gained `loadGamePaths`/`findGameIdByPath`/
     `maxGameId`/`updateGame`/`replaceDiscs`/`clearSubDirTables` for that. **Watch the trailing separator**:
     the `PATH` column always carries one (`insertGame`'s `fullPath + sep`, a no-op if already there), a
     `UsbGame::fullPath` never does - every lookup by path needs it added back (or stripped, for the
     id-by-path maps `writeSubDirRows`/`writeAutobleemList` probe with bare `fullPath`). Missing this the
     first time round made every rescan treat known games as new (duplicate rows); `tests/core/
     test_scan_service.cpp`'s real-scan integration test is what caught it - the DB-level unit tests didn't,
     because their fixture never went through `+ sep` at all.
   - **Step 2** - `ScanService` (`core/services/scan_service.*`, `App::scans()`): one `std::thread` at the
     OS's lowest scheduling priority (`System::lowerCurrentThreadPriority()` - `SCHED_IDLE` on Linux,
     `THREAD_PRIORITY_IDLE` on Windows, so a scan never takes CPU from a running emulator) does every bit of
     filesystem work with its own `CoverDatabase` connection and queues `WorkerEvent`s; `poll()`, called
     from the main thread, applies every regional.db write and returns a `ScanUpdate`. `requestScan()`/
     `scanning()`/`setWatching()`; `checkForChanges()` is the watcher's debounce (two identical fingerprints
     in a row, `ScanWatchInterval` = 10s apart, `core/model/timing.h`), checked every `threadMain()` cycle
     when nothing was requested directly.
   - **Step 3** - `ClassicMenuScreen`/`gui/scan_progress.*` are deleted; `AutoBleem::run()` goes splash ->
     `GuiLauncher` directly and loops there (`Session::MenuOption` keeps only `IDLE`/`RETRO`/`START`, at
     their old numeric values - `rc/selection.sh` trimmed to match: RetroArch for `SEL_RETROARCH`, a reboot
     for anything else). No more `ui=classic`/EvolutionUI choice (`Config` drops a stale `ui` key
     on load). Circle in the launcher's `Games` state is a no-op now - there is nothing left to fall back
     to. `GuiLauncher::loop()` polls the scan once a frame; a new bottom-of-screen line
     (`scanStatusLine`) shows its progress or a "Scan complete" summary, and any roster change reruns the
     current set's query and re-selects the same game by id (`reloadGames()`) rather than splicing the
     carousel - simpler, and it is the one place duplicates-across-folders and sub-dir rows already get
     settled right. Per request: `GuiSplash` now holds at full brightness for `SplashHoldDuration` (2s) and
     fades back out before returning instead of cutting away; `GuiLauncher` fades in from black over
     `LauncherFadeInDuration` (300ms) every time it is shown.
   - **Step 4** - `GuiSystemMenu` (`evoui/screens/evoui_system_menu.*`): the L2+R2 overlay with everything the
     classic menu offered - Re-Scan, RetroArch/EmulationStation, Memory Cards, Game Manager (refuses itself
     while `scanning()` - it deletes folders the scanner may be reading), Hardware Information, Options,
     About, Power Off. A dumb picker (translucent panel, launcher fonts/colours); `GuiLauncher::
     loop_openSystemMenu()` reads its `SystemMenuAction` back and runs it. Originally bound to a bare R2,
     moved onto L2+R2 (2026-09-17, on request): every other button was already committed to something in at
     least one launcher state, and L2+R2 used to power off the console directly - reaching for a bare R2
     with L2 still down from an L2+Select folder/playlist switch risked shutting down by mistake. L2+R2 now
     opens this menu instead, Power Off is one of its items (behind its own confirm), and bare R2 does
     nothing.

CHD support no longer depends on an external install: a CHD library is vendored (libmamecd on
2026-09-17, replaced by upstream **libchdr with zstd** on 2026-09-18 - see the "libchdr" bullet under
Build). `AB_ENABLE_CHD` defaults ON on every host.
