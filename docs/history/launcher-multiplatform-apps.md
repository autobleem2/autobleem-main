# Multi-platform Apps (`docs/archive/app-format-plan.md`)

Moved verbatim out of the launcher's CLAUDE.md on 2026-09-26 (task D19). The two standing rules from this section (SDL2 shared never bundled, the `app_<name>`/`ext_<name>` naming rule) stay in CLAUDE.md too.

## Multi-platform Apps (2026-09-24, `docs/archive/app-format-plan.md`)

**One App folder, a binary per platform.**
- `Apps/<name>/` keeps its shared files once (icon, data, `pad.ini`) and one binary per platform key in
  `bin/<key>/`.
- `app.ini` says which binary is which: `Exec.<key>=`, or one `Exec=bin/{key}/<name>` pattern.

**Platform keys.**
- `Env::appPlatformKeys()` is the ordered list this build accepts:
  - the target's own key first: `psc`, `rpi`, `rpi64`, `pcusb`, `win`, `dev`;
  - then its generic `linux-<arch>` / `windows-x86_64` key;
  - then the platform ini's `app_platform_keys=`.
- The console takes `psc` only, because nothing built against a current distribution loads there.

**Resolving an App: one rule, `AppManifest` (`core/services/app_manifest.*`).**
- The first key whose binary exists wins. `Args`/`Lib` resolve for that key. `Env=` is one
  `NAME=value;...` line with `Env.<key>=` on top: `IniFile` lower-cases keys, so there is no key per
  variable.
- `GameQueryService::apps()` leaves out an App with nothing to run here.
- `LaunchService::planApp` starts the App:
  - through `rc/app_run.sh`, or its own `Startup=` script, with `AB_APP_DIR/EXEC/ARGS/LIB/KEY`,
    `AB_PLATFORM(_KEYS)`, `AB_ROOT` and the ini's `Env` in the environment (`LaunchPlan::env`,
    `System::runAndWait`'s `env`);
  - directly on Windows (the resolved exe, `Args` split; `PATH` = `Lib`, then the launcher's own folder,
    then the inherited one).
- An ini with only `Startup=` is an App of the old kind and is started exactly as before - except on
  Windows, which has no `sh`: `AppManifest` refuses it there, so it is neither listed nor run
  (2026-09-25).
- **SDL2 is shared, never bundled** (autobleem-main `docs/decisions.md`, "Third-party App ports"): an App
  uses the launcher's SDL2 family - `/tmp/lib` on the console (`app_env.sh` puts it ahead of the libs
  pack for an `AB_APP_KEY=psc` App), the launcher's folder on Windows (`SDL2.dll`, `SDL2_image/mixer/ttf`)
  - or the system's on the Pis and the PC stick. Every other library an App needs is in its own
  `lib/<key>/` (`Lib=lib/{key}`).
- `VirtualPad=true|false` (absent = true) says whether the App runs with the virtual pad mapper.
  `AB_APP_VIRTUAL_PAD` carries it, and `app_env.sh` skips abpadd and the preload when it is off.
- An App's source repository is named `app_<name>`, an extension's `ext_<name>` (the owner's rule).
- **`Category=`** (2026-09-26): `Games`/`Emulators`/`Tools`/`Media`, case-insensitive
  (`core/model/game_set.h`'s `AppCategory`, parsed by `GameQueryService::apps()`/`appCategories()`);
  missing or anything else is `Other`. The set picker's Apps tab (`evoui_set_picker.cpp`) lists "All apps"
  first, then one row per category with at least one App present, each with its count;
  `GuiLauncher::showSetName()` shows "Showing: Apps: Tools (3 apps)" for a category row - Apps are counted
  as apps, never games. The app_* repos and the Store catalog will carry their own category later; this is
  the app.ini side only.

**The scripts.**
- `rc/app_env.sh` is one file for every Linux target: the console's libs pack only where
  `Autobleem/lib/apps` exists, `AB_APP_LIB` first on the library path, home on the stick, the virtual
  gamepad.
- A `run.sh` started by hand resolves the ini itself through `rc/app_resolve.sh`, the rule in `sh`+`awk`.
  It reads the keys from `System/platform_keys`, which the launcher writes at start-up.
- `tests/rc/test_app_resolve.cpp` holds the shell copy to `AppManifest`'s answers. It also keeps the
  three scripts identical in `payload/` and `payload_linux/`. **autobleem-appliance's `payload_linux/`
  carries the same three files**: change all three copies together.

