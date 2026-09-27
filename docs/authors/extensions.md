# Writing an extension

An **extension** is a plugin: a shared library (`.so`, or `.dll` on Windows) that the launcher loads
directly into its own process. It draws its screens with the launcher's own UI toolkit, in whatever theme
the user has chosen, and can keep doing work in the background while the launcher's carousel is showing.
The AutoBleem Store is the reference example - see the end of this page.

If what you are building is instead its own separate program (a game, an emulator port, a tool that runs
full-screen on its own), you want an [App](apps.md) instead - much simpler to build, since it never touches
the launcher's own code.

## The folder

`Extensions/<name>/` on the data root, laid out the same multi-platform way as an App
([README.md](README.md#platform-keys) has the platform keys):

```
Extensions/store/
    extension.ini
    icon.png                     the Extensions list's icon, 128x128, shared
    lang/                        translations, one <Language>.txt per language, shared
    bin/psc/store.so
    bin/rpi64/store.so
    bin/win/store.dll
    lib/<key>/                   optional: the extension's own third-party libraries
```

## `extension.ini`

```ini
[extension]
Name=AutoBleem Store
Description=Download apps and games
Author=Your name
Version=1.0.0
# resolved by the same rule as an App's Exec=; .so / .dll is added per platform
Plugin=bin/{key}/store
Icon=icon.png
# load the plugin and start polling it at start-up, rather than only when the user opens it
Background=true
# required | optional | none (the default): what the extension needs the network for
Network=required
# optional: named entry points a launcher menu item can open the extension at directly (see runEntry below)
Provides=network
```

- **`Plugin=`** resolves exactly like an App's `Exec=`: `Plugin.<key>=` first, else the plain pattern with
  `{key}` replaced, tried against each platform key in order; `.so`/`.dll` is appended automatically for the
  platform.
- **`Network=`** governs whether the extension can be opened without a network connection:
  - `required` - the launcher refuses to run it while there is no network; its row in the Extensions list is
    greyed out with an explanation, and selecting it does nothing but play the cancel sound. A
    `Background=true` extension that needs the network is still loaded at start-up (so it can resume once a
    connection appears); its own `poll()` is expected to wait for the network itself.
  - `optional` - it runs offline and does less, and says so itself.
  - `none`, or the key left out entirely - the network does not matter to it.
- **`Background=true`** loads the extension when the launcher starts (rather than the first time the user
  opens it) and calls its `poll()` once a frame from then on.
- **`Provides=`** is a list of names (separated by commas, semicolons or spaces) the extension answers to
  when a launcher menu item wants to open it directly at a particular page, rather than at its default
  screen - see `runEntry()` below.

The extension's binary is never trusted about its own compatibility: the ABI is read from the library
itself at load time, never from the ini (see "The ABI stamp" below), so a hand-edited ini cannot claim a
compatibility the binary does not actually have.

## The C++ surface

An extension is written against a small header, `gui/extension.h`, from the launcher's own SDK
(`autobleem-core`: `lib_ableem`, `ab_core`, `ab_classic`). It implements one class and ends one source file
with a macro:

```cpp
#include <ableem/engine/log.h>
class AppBase;

class ExtensionHost {                    // implemented by the launcher; what it offers your extension
public:
    virtual AppBase &app() = 0;                      // config, theme, language, audio; Gui::getInstance()
    virtual const std::string &name() const = 0;     // the folder's name, Extensions/<name>/
    virtual const std::string &folder() const = 0;   // Extensions/<name>/
    virtual const std::string &stateDir() const = 0; // System/Extensions/<name>/ - your own files go here
    virtual bool networkUp() = 0;                    // a default route (always true on Windows)

    virtual void requestRescan() = 0; // games were added or removed: run the launcher's scan
    virtual void reloadApps() = 0;    // the Apps set changed
    virtual void reloadConfig() = 0;  // config.ini changed (theme, language)
    virtual void notify(const std::string &title, const std::string &detail, uint64_t done, uint64_t total) = 0;
    virtual void clearNotification() = 0;

    virtual plog::IAppender *logAppender() = 0; // the launcher's log, tagged [<name>]
    virtual plog::Severity logSeverity() = 0;
};

class Extension {                        // implemented by you
public:
    virtual ~Extension() = default;
    virtual void run() = 0;              // Extensions list -> Cross: show your screens, return when done
    virtual void poll() {}               // once a frame, for Background=true - keep it cheap
    virtual void suspend() {}            // a game is about to start: free every Texture/Font, pause threads
    virtual void resume() {}             // the game ended, the display is back
    virtual void shutdown() {}           // the launcher is leaving: join threads, save what must survive
    virtual bool runEntry(const std::string &entry) { return false; } // see below
};

extern "C" const char *ab_extension_abi();
extern "C" Extension *ab_extension_create(ExtensionHost &host);
```

`AB_EXTENSION(MyExtensionClass)` is a macro (from `gui/extension.h`) that writes both `extern "C"` entry
points for you, so an extension's own code needs only to implement the `Extension` class:

```cpp
class Hello : public Extension {
public:
    explicit Hello(ExtensionHost &host) : host_(host) {}
    void run() override { /* stack your GuiScreens on Gui::getInstance() */ }
private:
    ExtensionHost &host_;
};

AB_EXTENSION(Hello)
```

### The life of a loaded extension

- **Loading.** A `Background=true` extension is loaded right after the launcher's splash, so its `poll()`
  runs from the first frame. Any other extension is loaded the first time the user opens it from the
  Extensions list. No extension is ever unloaded once loaded.
- **`run()`** is called when the user picks the extension from the Extensions list: show your screens (built
  on the launcher's `Gui`, like any of its own screens) and return once you are done, back to the list.
- **`poll()`** runs once a frame for a `Background=true` extension and must stay cheap - real work belongs
  on the extension's own threads (at a lowered priority), with results only handed over inside `poll()`.
- **Game launches.** Before the display, audio and controllers are handed to an emulator, every loaded
  extension's `suspend()` is called - drop every `Texture` and `Font` you are holding outside a screen (the
  launcher frees the renderer and window around a launch, exactly as it does for its own screens), and pause
  your own threads. `resume()` follows once the display is back.
- **`shutdown()`** runs before the launcher exits, on every exit path (power off, switching to RetroArch, an
  update) - join your threads and save whatever state must survive.
- **`runEntry(entry)`** lets a launcher menu item (for example "Network & Controllers" in the system menu)
  open your extension directly at a named page, rather than always landing on `run()`'s default screen.
  `entry` is one of the names your `extension.ini`'s `Provides=` lists; show that page and return `true`, or
  return `false` if you do not recognize the name (the caller then reports it as not handled). The launcher
  picks the first installed, runnable extension whose `Provides=` names a given entry - so at most one
  installed extension should claim a given entry on a given stick.

### Logging

Log with the ordinary `PLOG_INFO`/`PLOG_WARNING`/`PLOG_ERROR`/`PLOG_DEBUG` macros, exactly as the launcher's
own code does. The lines land in the launcher's own log file and on its console output, each one tagged
with your extension's folder name (`[store]`), so a single log tells the launcher and every loaded extension
apart. There is no separate log file for an extension, and no direct use of `stdout`/`stderr`. This is wired
up for you automatically by `AB_EXTENSION()` and the build helper below - you do not need to call any
logging setup yourself.

### The ABI stamp, and when it changes

A plugin calls the launcher's C++ classes directly, so both sides must be built exactly the same way:
same compiler family and major version, the same C++ standard library string ABI, and the same target. The
launcher checks all of this - packed into one string, `AB_SDK_STAMP` - before it calls anything else in a
loaded library; a mismatch leaves the extension greyed in the Extensions list ("Built for a different
AutoBleem - needs an update from its author") and it is never loaded.

Part of that stamp is an integer, **`AB_SDK_ABI`** (currently 4), bumped whenever the memory layout of a
class in the SDK surface changes, or the signature of a function an extension may call changes. Adding a
new class or a new free function does not require a bump. Practically, this means:

- An extension you build today is only guaranteed to load against a launcher built from the same
  `AB_SDK_ABI`. When the launcher bumps it, your existing binary is refused (cleanly - see above), not
  crashed, and you need to rebuild against the new SDK headers.
- Build against the same toolchain and container image the launcher's own release was built in, for the
  target you are building for - a plugin built with a different compiler or C library will not match the
  stamp even at the same `AB_SDK_ABI` number.

### Hidden visibility

The build helper below compiles your extension with hidden symbol visibility by default (as a Windows DLL
always has): nothing in your library is visible to the launcher, or to any other loaded extension, except
the two `extern "C"` entry points `AB_EXTENSION()` writes. This keeps two independently-built extensions
from silently sharing static state that happens to have the same symbol name.

## Building

Use the SDK's CMake helper, `ab_add_extension()`:

```cmake
ab_add_extension(store
    HOST autobleem-gui          # required on Windows only - the launcher's own executable target
    SOURCES src/main.cpp ...
    INI extension.ini
    ICON icon.png
    LANG lang)
```

It compiles your sources against the SDK's headers with none of the SDK's own code linked in - your
library's undefined symbols bind to the launcher's own copy of them when it is loaded (`dlopen` on Linux;
the launcher's own import library on Windows). Never link any of the SDK's static libraries directly: doing
so gives your extension its own second copy of the launcher's global state (its `Gui`, its `Env`, its
`Lang`), and the build will in fact fail with duplicate symbol definitions if you try.

`HOST` is only required on Windows, where a plugin needs the launcher's import library to resolve its
symbols at link time; on the Linux targets a plugin builds from the SDK's headers alone, and does not need
the launcher's executable present. The result is staged at `<build>/extensions/<name>/` in exactly the
folder layout the data root expects (`extension.ini`, the icon, `lang/`, and `bin/<key>/<name>.so` or
`.dll` for whichever platform this build targets).

## Repository naming

An extension's source repository is named `ext_<name>` (for example `ext_store`); the folder it installs to
keeps the bare name, `Extensions/store/`.

## Examples to read

- **`extensions/hello`** in the launcher's own repository is the SDK's minimal sample: one themed dialog and
  a background `poll()` that shows a notification bubble for a few seconds, with a log line at every step of
  its life. It is built on every target as part of the launcher's own CI, though never packaged for release
  - read it end to end before writing your own.
- **[`autobleem2/ext_store`](https://github.com/autobleem2/ext_store)** - the AutoBleem Store - is the first
  real-world extension: background downloads, its own multi-screen UI, and a `Provides=` entry point. Its
  own `README.md` and `CLAUDE.md` are worth reading for how a non-trivial extension is organized.
- **PSC-Bios**, the console's hardware-information extension, lives in the
  [`autobleem2/autobleem-console-tools`](https://github.com/autobleem2/autobleem-console-tools) repository
  (console-only) and is a smaller second example of a plugin built outside the launcher's own build tree,
  from the SDK's headers alone.
