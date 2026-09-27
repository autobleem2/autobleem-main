# Writing a scanner processor

A **scanner processor** is a small console program the launcher's scan runs over the games before it reads
them. It can turn a file format the launcher does not understand into one it does (unpacking an archive,
for instance), or otherwise transform a game's files on disk (applying a patch, converting a format). The
launcher's own bundled example is `proc_unzip`, which unpacks `.zip`, `.7z` and `.rar` archives dropped into
the games tree.

If what you are building is instead a program the player runs directly, you likely want an [App](apps.md)
instead - a processor's whole job is to run automatically during a scan, never something the player opens
by hand.

## The folder

`System/Processors/<name>/` on the data root, laid out the same multi-platform way as an App
([README.md](README.md#platform-keys) has the platform keys):

```
System/Processors/unzip/
    processor.ini
    bin/psc/unzip
    bin/rpi64/unzip
    bin/pcusb/unzip
    bin/win/unzip.exe
```

## `processor.ini`

```ini
[processor]
Name=Unzip
Description=Unpacks zip, 7z and rar archives dropped into the games tree
Author=Your name
Version=1.1.0
# resolved the same way as an App's Exec=
Exec=bin/{key}/unzip
# what it can be given: games-folder, roms-folder (the whole tree, once per scan, before anything else -
# a "preprocessor"), ps1, rom (one game folder or one ROM file at a time)
Kinds=games-folder
# optional: file name patterns it is interested in (* and ?, case-insensitive); empty = every file
Match=*.zip;*.7z;*.rar
# optional: RetroArch system folder names it applies to (rom/roms-folder kinds only); empty = every system
Systems=
# where a freshly installed processor lands in its sequence, relative to others (lower = earlier)
Order=100
# seconds of silence before the launcher kills it as stuck; 0 = never
Timeout=600
# false: it only reads, so it is never interrupted for a game launch or RetroArch
Modifies=true
```

## The protocol

A processor is a plain command-line program the launcher's scan runs and talks to over its standard
input/output:

```
proc --version
proc --ismine --ps1 <game folder>            (or --rom <file> --system <name>, for a Kinds=rom processor)
proc --start --games <tree>                  (or --roms <tree>, for Kinds=roms-folder)
proc --start --ps1 <game folder>             (or --rom <file> --system <name>)
```

- **`--version`** exits 0 and prints one line: `#<Name> V<version> - <description>`.
- **`--ismine`** is only asked of an item processor (`Kinds=ps1` or `Kinds=rom`): exit 0 means "this file or
  folder is mine to work on", exit 1 means "not mine". A folder/roms processor is never asked this - it
  always runs over the whole tree.
- **`--start`** does the actual work. While it runs it prints, one line at a time, flushed as it goes:
  - `#Starting - <title>` first,
  - `#<stage>` whenever a new stage begins,
  - a bare `0`..`100` for a percentage, or `n/m` for a counter,
  - `#WARN - <text>` for anything worth telling the user about without failing,
  - and, at the end, either `#DONE` with exit code 0 (success), or `#ERROR - <text>` with a non-zero exit
    code (failure). **Both** the `#DONE` line and exit code 0 are required for success - one without the
    other is treated as a failure.

### The rules a processor must follow

- **Write atomically.** Write to `<name>.part` (or similar) and rename it into place only once it is
  complete; never delete the original file until the replacement is fully written.
- **Be idempotent.** Running the processor a second time on its own output must do nothing (and should say
  so quickly, not redo the work).
- **Stay inside your target.** Never touch anything outside the folder or file you were given.
- **Keep talking.** Print at least one protocol line at least every `Timeout=` seconds, or the launcher will
  assume you are stuck and kill you.
- **Survive being interrupted.** If stopped partway through (a game launch, for instance) and started again
  on the same target, you must finish correctly and leave no leftover `.part` files behind.

### The environment

Every processor run gets these environment variables:

| variable | meaning |
|---|---|
| `AB_PROCESSOR_PROTOCOL` | `1` - lets a program tell it is being run under this protocol |
| `AB_ROOT` | the data root |
| `AB_GAMES_DIR` | the PS1 games tree |
| `AB_ROMS_DIR` | the other systems' ROMs tree |
| `AB_RDB_DIR` | where RetroArch's own database files live |
| `AB_TMP` | a scratch directory of your own (`/tmp/abproc/<name>` on the console - RAM, not the stick) |
| `AB_PLATFORM`, `AB_PLATFORM_KEYS` | this machine's platform key, and the whole ordered list |
| `AB_LANGUAGE` | the user's chosen language |
| `AB_VERSION` | the AutoBleem version running it |

## Where it runs, and how the user controls it

The scan runs the folder processors of a sequence first (over the whole PS1 games tree, or the whole ROMs
tree), then, after files are sorted into game folders, each game folder or ROM file through its sequence's
item processors - up to three rounds, in case one processor's output is something another one wants to look
at again. `System/Processors/sequence.ini` records the order and which processors are switched on; the
launcher's own "Scanner processors" screen is where a player edits that. A processor is skipped on a target
it has already processed and that has not changed since (tracked by a small state file), so a processor
never repeats needless work on every scan. Anything a processor changes is also picked up by the scan's own
change detection, the same as any other change to the games tree.

## Checking your processor before you publish it

The launcher ships a checker, **`tools/proc_check.py`**, meant to be run against sample data before you
publish anything:

```
python tools/proc_check.py <processor folder> --games <sample Games tree> --roms <sample roms tree>
```

It runs your processor against **scratch copies** of the sample trees (nothing you point it at is ever
touched) and reports every rule above that it can see broken: `processor.ini` sanity (the fields parse, the
binary actually resolves for this machine), `--version`'s output, the protocol for every `Kinds=` your ini
declares that the sample trees can exercise, leftover `.part` files, writes outside your target, whether a
second run on your own output still has anything to do (idempotence), and whether a run interrupted midway
through can be safely restarted (atomicity). It exits 0 only when nothing failed (warnings are still shown,
but do not fail the check).

## Repository naming

A processor's source repository is named `proc_<name>` (for example `proc_unzip`, `proc_template`); the
folder it installs to keeps the bare name, `System/Processors/unzip/`.

## Starting from a template

**[`autobleem2/proc_template`](https://github.com/autobleem2/proc_template)** is a skeleton repository
meant to be copied to start a new processor: the protocol is already wired up in its `src/main.cpp`, along
with two utility headers (`src/fsutil.h` for the atomic-write/heartbeat/environment-variable helpers most
processors need, `src/strutil.h` for the rest), and the CMake build, cross toolchains, CI and a self-test
already work out of the box. Its own `README.md` walks through renaming it into your own processor step by
step. Follow it there instead of copying steps here, since the exact files and lines to change may move as
the template is updated.

**[`autobleem2/proc_unzip`](https://github.com/autobleem2/proc_unzip)**, the launcher's own bundled example
(shipped in every release package), is the other reference worth reading - the same protocol written as one
self-contained file instead of split into utility headers, if you would rather see it that way. It is a
`Kinds=games-folder` processor, so it is also the simpler of the two kinds to start from if your idea is
about the games tree as a whole rather than one file at a time.
