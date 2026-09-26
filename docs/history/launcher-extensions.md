# Extensions (`docs/extensions-plan.md`)

Moved verbatim out of the launcher's CLAUDE.md on 2026-09-26 (task D19). The ABI-bump rule from this section stays in CLAUDE.md too.

## Extensions (2026-09-24, `docs/extensions-plan.md`)

**What an extension is.** A plugin, `Extensions/<name>/` with an `extension.ini`:
- `Name`, `Description`, `Author`, `Version`, `Icon`;
- `Plugin=bin/{key}/<name>`, resolved by `AppManifest`, with `.so`/`.dll` added;
- `Provides=` (2026-09-26) - a semicolon-separated list of entry points (e.g. `network`) the extension provides
  for the launcher's system menu (Network & Controllers opens the first installed extension that provides
  `network` at that entry through `Extension::runEntry(entry)`);
- `Background=true` to be polled every frame;
- `Network=required|optional|none` - `required` is refused offline.

It is run from the System menu's **Extensions** item (`GuiExtensions`); its source repository is named
`ext_<name>`. **The Store ships with every platform's installer** (the owner, 2026-09-25 - it used to be a
separate download): the appliance's assemble scripts put `ext_store`'s package in (the stick's
`Extensions/`, `extensions/` in a Linux package for `install.sh`, the Windows program folder's `Extensions/`
for `WindowsInstallJob`), and every install and update replaces a shipped extension's folder whole
(`InstallerJob` removes exactly the package's `Extensions/<name>/`), leaving an extension's state in
`System/Extensions/` and any extension the user unpacked by hand alone. PSC-Bios ships with the console's.

**How it binds to the launcher.**
- It links against the launcher's own copy of the SDK. `autobleem-gui` is built with `ENABLE_EXPORTS`
  (`--export-all-symbols` on MinGW). On Windows a plugin imports from **`autobleem-gui.exe` by name**, so
  never rename the executable; `tools/ab_drive.py` runs `drive/autobleem-gui.exe` for that reason.
- A plugin never links the SDK's static libraries: `ab_add_extension()`
  (`autobleem-core/cmake/ab_extension.cmake`) gives it the headers and, on Windows, the import library.
- It logs through plog instance 1 (`PLOG_DEFAULT_INSTANCE_ID=1`), chained by `AB_EXTENSION` into the
  launcher's log with an `[<name>]` tag. Chaining instance 0 recursed on Linux.
- A plugin is built with **hidden visibility** (`ab_add_extension`); only the two `AB_EXTENSION` entry points
  are exported. With default visibility the Linux loader merges what two plugins both define (a static in
  an inline or template function is a GNU "unique" symbol): the plugins shared one plog instance-1 logger,
  and every line was logged once per extension, under each one's tag. `nm -D --defined-only` on a plugin
  should list `ab_extension_abi`/`ab_extension_create` and no `u` symbols.
- **ABI**: `AB_SDK_STAMP` in `gui/extension.h`, a macro on purpose. Bump `AB_SDK_ABI` (currently 4, since 2026-09-26)
  whenever the layout of a class, or the signature of a function, an extension may use changes. **AB_SDK_ABI 4**
  (2026-09-26): `Extension::runEntry(entry)` - extensions can be opened at a named entry point, e.g. `"network"`
  for the Network & Controllers hub; `extension.ini`'s `Provides=` lists them; `ExtensionCatalog::findProvider(entry)`
  finds the first installed extension that provides it.

**Where the code is.**
- Core: `ExtensionCatalog` and `PluginLoader`.
- ab_classic: `gui/extension.h`, `ExtensionRuntime` (the crash guard: `System/Extensions/.active`, and
  `disabled.txt`) and `ExtensionHostBase`.
- The launcher: `App` (its `LauncherExtensionHost`, `takeExtensionRequests()`),
  `AutoBleem::run`/`runOutside` (start, crash guard, suspend/resume, shutdown) and `GuiLauncher`
  (the poll and its `extensionBubble`).
- `extensions/hello/` is the sample and smoke test, staged in `build_win/extensions/` and put on the dev
  stick by `make_usb.py`. It is built on a dev host only (`AB_BUILD_SAMPLE_EXTENSION`, off for every device
  target): it never goes into a package or onto a device (the owner's call, 2026-09-24).

