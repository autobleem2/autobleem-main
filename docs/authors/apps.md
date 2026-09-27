# Writing an App

An **App** is a third-party program - a game, an emulator, a tool - that shows up in the launcher's Apps
set and is started full-screen, the same way a PS1 game is. This page describes the folder format every
App follows, current across every platform AutoBleem runs on.

See [README.md](README.md) for the platform keys used throughout, and [extensions.md](extensions.md) if
what you are building needs to run *inside* the launcher instead (draw its own screens, react to the game
library) rather than as its own separate program.

## The folder

An App lives at `Apps/<name>/` on the data root (the USB stick, the Pi's or PC stick's data partition, or
the Windows product's data folder). A folder that targets several platforms holds one binary per platform
key, side by side, plus whatever the App needs on every platform:

```
Apps/opentyrian/
    app.ini
    run.sh                  optional - see "When you need a run.sh" below
    icon.png                shown in the Apps set, shared by every platform
    data/                   the App's own files (levels, music, ...), shared
    pad.ini                 optional virtual-gamepad profile, shared
    bin/psc/opentyrian
    bin/rpi64/opentyrian
    bin/linux-armhf/opentyrian
    bin/pcusb/opentyrian
    bin/win/opentyrian.exe
    lib/psc/...              optional: libraries only this platform's binary needs
    lib/rpi64/...
```

`bin/<key>/` and `lib/<key>/` are a convention `app.ini`'s `Exec=`/`Lib=` patterns build on - not a rule the
launcher enforces on their own. What matters is what the ini says.

## `app.ini`

```ini
[app]
Title=OpenTyrian
Author=Your name
Version=2.1.20221123
Image=icon.png
Readme=readme.txt

# the program, per platform key (paths relative to the folder)
Exec.psc=bin/psc/opentyrian
Exec.rpi64=bin/rpi64/opentyrian
Exec.linux-armhf=bin/linux-armhf/opentyrian
Exec.pcusb=bin/pcusb/opentyrian
Exec.win=bin/win/opentyrian.exe
# or, if every binary follows the bin/<key>/ convention, one line covers every key -
# {key} is replaced by whichever key matched:
Exec=bin/{key}/opentyrian

# optional, shared; Args.<key>= overrides it for one platform
Args=--fullscreen
# optional, added to the library search path (Lib.<key>= overrides)
Lib=lib/{key}
# optional environment variables, "NAME=value" pairs separated by ';' (Env.<key>= adds to or overrides them)
Env=SDL_AUDIODRIVER=alsa;TYRIAN_DATA=data
# whether the App should run behind AutoBleem's virtual gamepad (see below); absent = true
VirtualPad=true
# which group the Apps tab lists it under: Games, Emulators, Tools or Media (case-insensitive);
# anything else, or missing, files it under "Other"
Category=Games
```

Keys are case-insensitive (`Title`, `title` and `TITLE` are the same key); comments are `#` lines. Every
value is trimmed of surrounding whitespace.

### How the launcher picks a binary

For each platform key, in the order given in [README.md](README.md#platform-keys):

1. If the ini has `Exec.<key>=`, that is the candidate.
2. Otherwise, if it has a plain `Exec=` with `{key}` in it, the candidate is that pattern with `{key}`
   replaced by this key.
3. The first candidate that is an existing file is the program that runs. On Windows, a candidate that does
   not exist as given but does exist with `.exe` appended is used with `.exe` added - so one
   `Exec=bin/{key}/opentyrian` line can serve both a Linux binary and `opentyrian.exe` on Windows.

`Args=`, `Lib=` and `Env=` resolve the same way, for whichever key actually matched: the `.<key>` form is
tried first, then the plain form with `{key}` substituted. `Env=` is read first and then `Env.<key>=` adds
to or overrides individual variables on top of it.

**An App with no candidate for a given machine is simply not listed there** - it never appears in that
machine's Apps set, and a Store catalog would show it as "Not available for this system".

### `Startup=` - an App with a single, unported binary

Before an App had per-platform binaries, its `app.ini` named one script:

```ini
Startup=run.sh
```

This still works, and is how an App with only ever one target (traditionally the console) keeps running
unchanged. An ini with no `Exec=`/`Exec.<key>=` at all is started through its `Startup=` script wherever the
platform can run a shell script. It cannot run on Windows, which has no `sh` - an App meant to reach every
platform needs the `Exec=` form above.

### `VirtualPad=`

- `true` (the default, and what every App written before this key existed gets): the App is meant to be
  played through AutoBleem's virtual gamepad (see below).
- `false`: the App reads controllers its own way - it ships its own pad mapping, or has no use for one -
  and the launcher starts neither the virtual-pad daemon nor its library preload for it.

### `Category=`

Which group the launcher's Apps tab lists the App under: `Games`, `Emulators`, `Tools` or `Media`
(case-insensitive). Anything else, or no `Category=` at all, puts it under `Other`. The tab always shows
"All apps" first, then one row per category that has at least one App present.

## When you need a `run.sh`

On the Linux targets (the console, the Pis, the PC stick), the launcher runs your program one of two ways:

- **No `run.sh` in the folder**: the launcher runs a generic script of its own that sources
  `Autobleem/rc/app_env.sh` (below) and then simply executes your resolved binary with its resolved
  arguments. Most Apps need nothing more than this.
- **A `run.sh` in the folder**: the launcher runs that instead, with the same environment already set. Add
  one when you need to do something before your binary starts - write a config file, pick a data set, and
  so on. A minimal `run.sh` looks like:

  ```sh
  #!/bin/sh
  . "$(dirname "$0")/../../Autobleem/rc/app_env.sh"
  cd "$AB_APP_DIR" || exit 1
  exec "$AB_APP_EXEC" "$@"
  ```

**On Windows there is no shell**, so `run.sh` is never used there: the launcher starts your resolved
`Exec.win=` binary directly. An App that needs setup on Windows can name a `run.cmd` (or another
Windows-native step) as its `Exec.win=` target instead.

### What `app_env.sh` gives your program

Whether the launcher starts your binary directly or through `run.sh`, the following is set up for you
before it runs (on the Linux targets):

- **`AB_APP_DIR`**, **`AB_ROOT`**, **`AB_LOG_DIR`** - your folder, the data root, and where to log if you
  want to.
- **The library search path.** Your own `lib/<key>/` (from `Lib=`) always comes first. **SDL2 is never
  bundled inside an App** - AutoBleem's own SDL2 family is shared with every program that needs it: the
  launcher's own copy on the console (unpacked to `/tmp/lib` at boot) and on Windows (next to the launcher's
  executable), the system's own on the Pis and the PC stick. Bundle every *other* third-party library your
  binary needs under your own `lib/<key>/`.
  On the console specifically, an App built with the `psc` platform key is linked against that shared SDL2
  build - never vendor a different one.
- **A home directory on the data root.** `HOME` and the XDG directories (`XDG_DATA_HOME`,
  `XDG_CONFIG_HOME`, `XDG_STATE_HOME`) all point under `<data root>/Home/`, so a distribution that saves
  configuration or save files to "the user's home" writes them onto the same partition as everything else
  AutoBleem manages - not to the console's own storage, which is never written to. `XDG_CACHE_HOME` points
  into RAM instead, since a cache is not something worth keeping.
- **The virtual gamepad**, described next.

## The virtual gamepad

Many third-party programs read game controllers badly or not at all through the console's own driver stack.
AutoBleem's answer is a small daemon and a preloaded shim:

- **`abpadd`** reads every connected controller through the same controller database and code the launcher
  itself uses, and publishes the result in shared memory.
- **`libabpad.so`**, preloaded into your App's process (`LD_PRELOAD`), answers whatever controller API your
  program uses (SDL's, for instance) with a controller it understands - resolved exactly as the launcher
  would resolve it.

This happens automatically for any App with `VirtualPad=true` (the default) when both pieces are present on
the machine; an App with `VirtualPad=false` gets neither. Either way, on the console, `abpadd` also watches
for **the console's Reset button** and ends the App when it is pressed - see the exit rule below.

An App can ship its own `pad.ini` (a mapping profile) alongside `app.ini`; it is picked up automatically
when present.

## How the player leaves an App

**Every App must be leavable through the console's Reset button, and from the controller, without needing
a keyboard.** Concretely:

- On the console, holding Start+Select (through the virtual-gamepad shim) or pressing the Reset button
  (through `abpadd`'s watch, whether or not `VirtualPad=true`) ends the App and returns to the launcher.
- An App with `VirtualPad=false` still gets a Reset watch on the console (no controller shim, no SDL
  preload) - even a program that reads its own controllers must still exit on Reset.
- **Windows has no virtual-gamepad daemon and no Reset watch.** An App there is left through its own menu or
  keybinding - document how in the App's own readme, since there is nothing built in to fall back on.

If your program cannot be told to quit from outside (no menu, no signal it honors), it does not meet this
requirement and should not be published as an AutoBleem App until it can.

## Repository naming

An App's source repository is named `app_<name>` (for example `app_opentyrian`); the folder it installs to
on the data root keeps the bare name, `Apps/opentyrian/`.

## A minimal worked example

A single-platform App that only targets the console, using the old `Startup=` form:

```
Apps/mytool/
    app.ini
    run.sh
    icon.png
    bin/mytool
```

```ini
# app.ini
[app]
Title=My Tool
Author=Me
Version=1.0
Image=icon.png
Startup=run.sh
Category=Tools
```

```sh
#!/bin/sh
# run.sh
. "$(dirname "$0")/../../Autobleem/rc/app_env.sh"
cd "$AB_APP_DIR" || exit 1
exec ./bin/mytool "$@"
```

A multi-platform App using the newer `Exec=` form needs no `run.sh` at all if it has nothing to set up -
just the ini and a `bin/<key>/` binary per target platform, as shown under "The folder" above.
