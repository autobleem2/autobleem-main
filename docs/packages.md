# Packages - one game-data format for every engine (APPS-12) - specification

Status: **specification, step 1 of APPS-12** (the owner, 2026-10-06: "mamy jeden pack z danymi gry dla wszystkich
engine ... ogolna opcja", "user musi tez miec jakis sposob wgrac jego dane oryginalnej gry jako paczki"). Milestone
alpha1.2. Written before any code: the launcher, autobleem-core, proc_pe, pe_ports, the `app_*` repositories, ext_store
and autobleem-repo implement exactly this; a change to it is a change to this file first.

**Applies to:** the launcher and autobleem-core (scan, picker, launch, Store catalog), proc_pe, pe_ports, app_crispydoom,
app_jfduke3d, app_jfsw (and the other app_* that need game data), ext_store, autobleem-repo (catalog, site), the manuals.
**Does NOT apply to:** shipping or downloading commercial game data (we only ever ship free data: Freedoom, shareware,
OpenArena); PS1 games; RetroArch content (ROMs, cores); Themes; the engine's own settings and saves.

Where this sits in the other docs: the App format is autobleem-main `docs/archive/app-format-plan.md` (`app.ini`,
`AppManifest`); the PE route is `docs/pe-store-plan.md`; the Store is the launcher's `docs/store-plan.md`; the quiet
stick is the launcher's `docs/developer-guide.md`, "The quiet stick". This file adds to them, it does not replace them.

## 1. The idea in one page

- A **package** is a folder under `Packages/` on the stick that holds the data of one or more **games** (Freedoom =
  Phase 1 + Phase 2; Quake's `id1`; a DOS game). A game has a **content kind** (`doom-iwad`, `quake-id1`, ...).
- An **engine** (an App) says in its `app.ini` which kinds it can run: `Uses=doom-iwad`.
- **The launcher joins them.** When the player starts an engine that has `Uses=`, the launcher lists the games of
  matching kind (from `Packages/` and from the engine's own data folder) and starts the engine with the chosen game's
  files in environment variables (`AB_PKG_FILE` ...) and `{package}` placeholders in `Args=`.
- **Our own packages** (Store, PE mods) carry a descriptor, `package.ini`. **The player's own files** (his original
  Doom, Quake, Theme Hospital ...) are recognised from a table, `rc/packages.ini`, by file names - nothing is written
  into his folders.
- A package is **never launched**. The "Packages" row of the Apps tab only shows what is there.
- A new game = a row in the table (data). A new engine = `Uses=` (data). Code changes only for a new kind's display
  name (section 3.3) or a new engine's own start script.

```
Packages/                         the stick (user-writable, ours and his)
  freedoom/                       from the Store (zip)   package.ini   freedoom1.wad  freedoom2.wad  licences/
  quake-shareware/                from the Store (zip)   package.ini   id1/pak0.pak
  Doom/DOOM.WAD  DOOM2.WAD        the player's own copy  (no descriptor; recognised from rc/packages.ini)
  DOS/Prince/PRINCE.EXE ...       the player's own copy  (recognised, or his own package.ini)
Apps/crispydoom/app.ini           Uses=doom-iwad   -> picker -> AB_PKG_FILE=.../Packages/Doom/DOOM2.WAD
```

## 2. The package on the stick

### 2.1 Location and scan

- The folder is `Packages/` in the stick's data root (`Env::getPathToPackagesDir()`: the USB root + `Packages`, like
  `Apps` and `Mods`). It is created by the installers and the image build (with a `README.txt` that says how to add
  games - the text of section 4.7), and by `PackageInstaller` at the first Store install. **The scan never creates it**
  (quiet stick).
- A **package root** is the folder that holds `package.ini` (a descriptor package), or - for files the player dropped -
  the folder where a table row matched (section 4). The scan visits `Packages/` and the folders below it **up to 4
  levels down**, skips names starting with `.` and `$` and `System Volume Information`, never descends into a
  descriptor package, and stops after 2000 folders in one scan (it logs that it stopped).
- Everything the scan finds lives in **RAM only** (section 4.5). Nothing is written to the stick by the scan.

### 2.2 `package.ini`

Plain ini, UTF-8 (LF or CRLF, a BOM is ignored), read with `IniFile`: keys are case-insensitive, values trimmed, **a
`#` starts a comment anywhere on a line** (so a title cannot contain `#`), the `[package]` header is conventional and
ignored, and **keys are flat** (IniFile has no sections) - games are numbered `Game1.`, `Game2.` ... Do not use the key
`Publisher` (IniFile rewrites it); the key is `Author`.

| Key | Required | Meaning |
|---|---|---|
| `Title` | yes | The package's name (max 80 characters), e.g. `Freedoom`. |
| `Kind` | yes, unless every game names its own `Kind` | The default content kind of its games: one kind, or several separated by `;` when a package holds games of different kinds (section 3). |
| `Id` | no | The package's id, `[a-z0-9]` and single `-`, max 40 characters (the same grammar as a kind). Default: the folder name lower-cased with every other character turned into `-`. Unique on the stick: when two folders claim one id the first by folder name wins and the other is listed as a duplicate. |
| `Version` | no | Free text, shown in the info view; the installers compare versions with the existing `compareVersions` rule. |
| `Licence` | no | SPDX id or a short text (`BSD-3-Clause`, `Shareware (id Software)`). Shown in the info view. |
| `Author` | no | Who made the data (`The Freedoom project`). |
| `Description` | no | One line, max 200 characters. |
| `Image` | no | A PNG in the package (relative path), the carousel's cover for the Packages row. Absent = the launcher's generic package icon. |
| `Readme` | no | A text file in the package (relative path), shown by the info view. |
| `Source` | no | `store`, `mod` or `user`; the installer **stamps it** (`PackageInstaller` writes `store`, proc_pe writes `mod`); a hand-made descriptor says `user` or nothing. Shown as "Store" / "Mod" / "Your files". |
| `StoreId` | no | The catalog id (`pkg/freedoom`), stamped by `PackageInstaller`; how the Store knows it installed the folder. |
| `PeSource` | no | The `.mod` file name, stamped by proc_pe when it makes a package from an old/third-party `.mod` (2.3). |
| `Replaces` | no | App folders this package supersedes (`pe-freedoomdata`), `;` separated: `PackageInstaller` parks each one that exists in `Apps/.replaced/` after the package is in place (section 11). |
| `Game<N>.Title` | yes (N from 1) | The game's display name (`Freedoom: Phase 1`). |
| `Game<N>.File` | yes | The game's **main file**, relative to the package root, `/` separators, no `..`, not absolute: what `AB_PKG_FILE` becomes (a `.wad`, `id1/pak0.pak`, `PRINCE.EXE`). The name is resolved case-insensitively against the real folder; the real spelling is what the engine gets. |
| `Game<N>.Id` | no | The game's id, same grammar as `Id`; default `game<N>`. It is also the `{package_game}` value; **keep it stable across versions** (saves are filed under it). |
| `Game<N>.Kind` | no | This game's content kind; default the package's `Kind` (the first one when it lists several). |
| `Game<N>.Variant` | no | Free text shown after the title in the picker's second line (`Phase 1`, `v1.9`). |
| `Game<N>.Dosbox.<name>` | no | `dos-game` only: a per-game DOSBox setting - `Cycles`, `Memsize`, `Sound` (the DOSBox engine defines the names it reads; anything else is ignored). Passed as `AB_PKG_SET_<NAME>` (section 5.2). |
| `Game<N>.Mapper` | no | `dos-game` only: a DOSBox mapper file in the package (relative path) for this game's keys; passed as `AB_PKG_MAPPER`. Absent = the engine's default. |
| `Game<N>.Start<M>.File`, `Game<N>.Start<M>.Title` | no | Programs that start the game (M from 1): for a `dos-game`, the game itself and its SETUP (section 10). The first one is the default. Relative like `File`. |

Rules the reader enforces (a violation drops the game or the package and logs one line - never a crash, never a write):

- games are read from `Game1` upward and stop at the first N without a `Title`;
- a game whose `File` does not exist, or whose kind does not fit the kind grammar (section 3.2), is dropped; a package
  with no game left is not a package (the folder is then "unknown data");
- keys that are not listed are ignored (room for later versions); a file larger than 64 KB is refused.

Example, Freedoom as pe_ports builds it (`Packages/freedoom/package.ini`, after the Store stamped it):

```
[package]
Title=Freedoom
Kind=doom-iwad
Version=0.13.0-1
Licence=BSD-3-Clause
Author=The Freedoom project
Description=Free game data for Doom engines: Phase 1 (the Ultimate Doom replacement) and Phase 2 (the Doom II replacement).
Image=freedoomdata.png
Source=store
StoreId=pkg/freedoom
Replaces=pe-freedoomdata
Game1.Id=freedoom1
Game1.Title=Freedoom: Phase 1
Game1.File=freedoom1.wad
Game2.Id=freedoom2
Game2.Title=Freedoom: Phase 2
Game2.File=freedoom2.wad
```

Example, a DOS game a player writes himself (`Packages/DOS/Prince/package.ini`):

```
[package]
Title=Prince of Persia
Kind=dos-game
Game1.Title=Prince of Persia
Game1.File=PRINCE.EXE
Game1.Start1.File=PRINCE.EXE
Game1.Start1.Title=Play
Game1.Start2.File=SETUP.EXE
Game1.Start2.Title=Setup
```

Example, a package of several kinds:

```
[package]
Title=My id Software games
Kind=doom-iwad;quake-id1
Game1.Title=Doom II
Game1.File=Doom/DOOM2.WAD
Game2.Title=Quake
Game2.Kind=quake-id1
Game2.File=Quake/id1/pak0.pak
```

(For Quake, `AB_PKG_DIR` is the package root; a game whose files live in a sub-folder is better as its own package so
that the root is the folder the engine expects - the table does this by itself, section 4.)

### 2.3 How pe_ports builds one (and the old `.mod` route)

Today a data port (`kind=data` in pe_ports' `port.ini`) becomes a `.mod` that proc_pe turns into an App with an empty
script (`pe-freedoomdata`, `pe-openarenadata`). From APPS-12 **a data port builds a package zip and a Store item of
kind `package`** - one data format for every package, no `.mod` for data:

1. **`port.ini`**: a data port (`kind=data`) gets a `[package]` section (the keys of 2.2, no `Game<N>` numbering in the
   source - the generator writes it):
   ```
   [package]
   content_kind=doom-iwad
   games=freedoom1|Freedoom: Phase 1|freedoom1.wad;freedoom2|Freedoom: Phase 2|freedoom2.wad
   replaces=pe-freedoomdata
   ```
   (each game is `id|title|file`; the licence, author, version, description, image come from `[port]`). A `dos-game`
   port may add `start=`, `mapper=` and `dosbox.<name>=` lines (2.2).
2. **`tools/mkmod.py`** (a `--package` output for a data port, the `.mod` output stays for engine ports): validates the
   section (the kind grammar, every `file` present in the staged data), writes `package.ini` (no stamps) and packs the
   data, `package.ini`, the icon as `Image`, `licences/` and `SOURCE.txt` into **`<id>-<version>.zip`** (one folder or
   the root, 2.4). The licence/source-offer files of today's `.mod` stay in the zip. `ci/build.sh`'s "no binary" check
   for `kind=data` stays; a data port without `[package]` fails the build.
3. **The Store item** the build writes (`tools/store_item.py` of the repo, or mkmod's catalog line): `kind: "package"`,
   `category: "packages"`, `provides`, the zip as its one file with size and sha256, `requires` empty (section 8). The
   engines' items point at it with `requires` (`lzdoom` -> `pkg/freedoom`, `ioquake3` -> `pkg/openarena`).
4. **Engine ports** keep making `.mod` Apps; `port.ini` `[port]` gets `uses=` (a `;` list) and optionally `package_dir=`
   (a relative folder), which `mkmod.py` writes as `launcher_uses="doom-iwad;heretic-iwad"` and
   `launcher_package_dir="WAD"` in `launcher.cfg`; proc_pe copies them to `app.ini` as `Uses=` and `PackageDir=`. A
   value that does not fit the grammar is dropped with a `#WARN`. The engine's `launch.sh` reads the choice from
   `AB_PKG_*` (section 5) - the environment reaches it through `rc/pe_run.sh` unchanged.
5. **The old data Apps migrate** when the package is installed (section 11): `Replaces=pe-freedoomdata` parks the old App.

**Is proc_pe's `.mod` -> package route still needed? Not for our data - recommended: build it anyway, small, for
old and third-party `.mod`s.** Nothing of ours uses it after step 2. A third-party or older `.mod` that holds only data
(`launcher_package="1"` in `launcher.cfg` plus a `package.ini` in the launcher folder) is made into `Packages/pe-<launcher_filename>/`
with the same checks as an App (size limits, path checks, links become copies, atomic rename), `Source=mod` and
`PeSource=<the .mod>` stamped, replace/refuse/skip rules as for Apps, removal and `present` through `ModInstaller`
(also covering `Packages/`). It is a few dozen lines on code that exists; dropping it would leave a `.mod` of data in
`Mods/` making an App with nothing to run. If the lead prefers less code, the alternative is proc_pe refusing such a mod
with a `#WARN` ("data mods are packages: use the Store's zip") - the spec works either way, nothing else depends on it.

### 2.4 How the Store installs one

One route for our data, one result (a folder in `Packages/` with a `package.ini`). Data built by pe_ports (Freedoom,
OpenArena ...) is a `package` item like any other (2.3); only old/third-party `.mod`s still reach `Packages/` through
proc_pe.

- **A `package` item** (catalog `kind: "package"`, section 8) has one file: a `.zip`, `.tar.gz` or `.7z` that holds
  `package.ini` at its root or inside its one folder. `PackageInstaller::install(archive, packagesDir, stagingDir)`
  works like `AppInstaller`: unpack to staging on the same filesystem, find the descriptor, **validate it with the
  reader of 2.2** (a `Title`, a kind, every game's file present), then rename into `Packages/<folder>/` where
  `<folder>` is the id made safe for FAT (`GameInstaller::folderNameFor`) and, when that folder exists with a
  different `StoreId`, " (2)" appended. It stamps `Source=store` and `StoreId=<the catalog id>` into the laid
  descriptor. A newer version replaces the folder whole (it is ours: staged first, then the old one removed, so a
  failure leaves the old one); an equal or older version is a no-op. Any failure leaves `Packages/` untouched.
  `PackageInstaller::remove(folder)` removes **only** a folder whose descriptor says `Source=store` or `Source=mod`
  - never a player's folder, never one without a descriptor.
- After the install the Store asks the launcher for a scan of `Packages/` only (`requestRescan(ScanPackages)`, section 9).

## 3. Content kinds

### 3.1 What a kind is

A kind names **what an engine needs in order to run a game**, not who made the files. `doom-iwad` is one kind because
both Crispy Doom and LZDoom run Doom, Doom II, Final Doom and Freedoom; Heretic is a different kind because only LZDoom
runs it. Split a kind only when two engines differ in what they can run.

### 3.2 Grammar and the rule for a new kind

`[a-z0-9]+(-[a-z0-9]+)*`, at most 32 characters, always lower case (a value in an ini is lower-cased and trimmed before
comparing). The name is `<family>-<shape>`: the game or engine family first (`doom`, `quake`, `q3`, `duke3d`, `sw`,
`dos`, `theme-hospital`), then what the data is (`iwad`, `id1`, `grp`, `game`). An unknown kind is **kept and shown** by
its id - an engine or a table from a newer release still works with an older launcher.

To add a kind: (1) a row (or rows) in `rc/packages.ini` for the player's files, (2) the display name in core's
`packageKindName()` (translated at the call site with `_()`, 16 languages) - without it the id is shown, (3) the engines'
`Uses=` and the manual's table of games (section 4.7). Nothing else.

### 3.3 The initial vocabulary

| Kind | Holds | Identifying files (relative to the package root) | `AB_PKG_FILE` | Run by (first users) | Display name (`_()`) |
|---|---|---|---|---|---|
| `doom-iwad` | A Doom-engine IWAD: Doom, Doom II, Final Doom, Freedoom, Chex Quest, HacX | `DOOM.WAD`, `DOOM1.WAD`, `DOOM2.WAD`, `TNT.WAD`, `PLUTONIA.WAD`, `FREEDOOM1.WAD`, `FREEDOOM2.WAD`, `FREEDM.WAD`, `CHEX.WAD`, `HACX.WAD` (each with the header `IWAD`) | the `.wad` | Crispy Doom, LZDoom | "Doom data" |
| `heretic-iwad` | Heretic | `HERETIC.WAD` | the `.wad` | LZDoom | "Heretic data" |
| `hexen-iwad` | Hexen | `HEXEN.WAD` | the `.wad` | LZDoom | "Hexen data" |
| `strife-iwad` | Strife | `STRIFE1.WAD` | the `.wad` | LZDoom | "Strife data" |
| `quake-id1` | Quake's `id1` folder | `id1/pak0.pak` (the full game also has `id1/pak1.pak`) | `<root>/id1/pak0.pak` | TyrQuake | "Quake data" |
| `q3-openarena` | OpenArena's base game | `baseoa/pak0.pk3` | that file | ioquake3 (OpenArena) | "OpenArena data" |
| `q3-baseq3` | Quake III Arena's base game | `baseq3/pak0.pk3` | that file | ioquake3 | "Quake III Arena data" |
| `theme-hospital` | The original Theme Hospital folder (disc, GOG, demo) | `DATA/VBLK-0.DAT` and `QDATA/FONT00V.DAT` | `<root>/DATA/VBLK-0.DAT` | CorsixTH | "Theme Hospital data" |
| `dos-game` | One MS-DOS game | a descriptor (`package.ini` with `Start` programs) or a table row naming its executable | the game's main program | DOSBox (APPS-10) | "DOS game" |
| `duke3d-grp` | Duke Nukem 3D's group file | `DUKE3D.GRP` | the `.grp` | JFDuke3D | "Duke Nukem 3D data" |
| `sw-grp` | Shadow Warrior's group file | `SW.GRP` | the `.grp` | JFSW | "Shadow Warrior data" |

`AB_PKG_DIR` is the package root in every row - the folder an engine would be pointed at (`-basedir`,
`fs_basepath`, `-j`). The file names are matched case-insensitively. **Verification status:** the identifying files above were taken from the engines and published lists. **Only Quake's
(`id1/pak0.pak` + `id1/pak1.pak`, the full game) is to be verified at the device round** - the owner has that copy. **Every
other row is marked `# verify against a real copy` in the shipped table** and the implementer must not treat it as
confirmed; the Freedoom rows are verifiable from our own build.

### 3.4 Not kinds (for alpha1.2)

- **PWADs / Doom mods** are not a kind: they are add-ons to an IWAD (the engine needs an IWAD *and* the mod), and the
  picker chooses one thing. They stay in the engine's own `MODS/` folder (LZDoom). (the owner, 2026-10-06).
- Wolf3D, Commander Keen, OpenJazz and the other shareware ports keep their data inside their App. Moving one to a
  package later is the one-line procedure of 3.2.

## 4. The player's own files

### 4.1 What the player does

He copies the game's own folder or files into `Packages/` on the stick - anywhere up to 4 levels deep, in any
sub-folder name (`Packages/Doom/DOOM2.WAD`, `Packages/Quake/id1/pak0.pak`, `Packages/Theme Hospital/DATA/...`,
`Packages/DOS/Prince/PRINCE.EXE`). The next scan (a launcher start, or the Store/Options rescan) recognises it. He does
nothing else, and nothing is written into his folders.

### 4.2 The tables

The launcher reads two tables, in this order, rows keeping their order inside a file:

1. `Packages/packages.ini` - **optional, the player's own** (only ever read; the player makes it), so a game we do not
   know can be added by one row;
2. `rc/packages.ini` - the shipped table (replaced by every update, like the other `rc/` files; it lives in the launcher
   repository's `payload/rc` and `payload_linux/rc`, and the two copies must be identical, as `rc/ab_log.sh`'s are).

The first row that matches a file wins (so his rows beat ours). A malformed row is skipped and logged; the rest still loads.

### 4.3 Syntax

Line-based, UTF-8, LF or CRLF, parsed by a small dedicated reader (`PackageTable` - **not** `IniFile`, which keeps one
section and could not hold many rows). A line that **starts** with `#` or `;` is a comment (a `#` inside a value is
ordinary text). `[row-id]` begins a row; `key=value` lines follow, keys case-insensitive, values trimmed. A shipped
file starts with `# autobleem-packages 1`.

| Key | Required | Meaning |
|---|---|---|
| `[row-id]` | yes | The row's id, the grammar of a kind; it is **the game's id** (`{package_game}`; saves are filed under it), so it never changes once shipped. |
| `kind` | yes | The content kind. |
| `title` | yes | The game's display name (a game name is not translated). |
| `match` | yes | The files that must all exist, relative to the root, `/` separated, `;` between them (`id1/pak0.pak;id1/pak1.pak`). The **root** is the folder in which they are found. |
| `main` | no | The main file (`AB_PKG_FILE`); default the first `match`. |
| `size` | no | The exact size in bytes of the first `match` file (tells shareware from retail when the names are equal). |
| `magic` | no | Four ASCII characters the main file starts with (`IWAD`); the scan reads 4 bytes, only when the names and size already matched. |
| `variant` | no | Free text for the picker's second line (`v1.9`). |
| `licence` | no | Shown in the info view (`Shareware`, `Free`). |
| `start` | no | For `dos-game`: `FILE|Title;FILE|Title` - the programs that start it (like `Start<M>` of a descriptor). |
| `set.<name>` | no | For `dos-game`: a DOSBox setting (`set.cycles=3000`), like `Dosbox.<name>` of a descriptor. |
| `mapper` | no | For `dos-game`: a mapper file, relative to the root. |

Initial shipped table (the implementer completes it; ordering matters - a specific row before a generic one):

```
# autobleem-packages 1
# rows marked 'verify' were not checked against a real copy; only [quake] is checked at the device round
# verify against a real copy
[doom1-shareware]
kind=doom-iwad
title=Doom (Shareware)
match=DOOM1.WAD
magic=IWAD
licence=Shareware

# verify against a real copy
[doom]
kind=doom-iwad
title=Doom
match=DOOM.WAD
magic=IWAD

# verify against a real copy
[doom2]
kind=doom-iwad
title=Doom II: Hell on Earth
match=DOOM2.WAD
magic=IWAD

# Final Doom: [tnt] is TNT.WAD, [plutonia] is PLUTONIA.WAD - the same shape as [doom2]
# verify against a real copy
[tnt]
kind=doom-iwad
title=Final Doom: TNT - Evilution
match=TNT.WAD
magic=IWAD

# [freedoom2], [freedm] (FREEDM.WAD), [chex] (CHEX.WAD) and [hacx] (HACX.WAD) have the same shape
# verify against a real copy
[freedoom1]
kind=doom-iwad
title=Freedoom: Phase 1
match=FREEDOOM1.WAD
magic=IWAD
licence=BSD-3-Clause

# [hexen] (HEXEN.WAD) and [strife] (STRIFE1.WAD) likewise, each with its own kind
# verify against a real copy
[heretic]
kind=heretic-iwad
title=Heretic
match=HERETIC.WAD
magic=IWAD

[quake]
kind=quake-id1
title=Quake
match=id1/pak0.pak;id1/pak1.pak

# verify against a real copy
[quake-shareware]
kind=quake-id1
title=Quake (Shareware)
match=id1/pak0.pak
size=18689235
licence=Shareware

# verify against a real copy
[quake-id1]
kind=quake-id1
title=Quake (id1 data)
match=id1/pak0.pak

# verify against a real copy
[openarena]
kind=q3-openarena
title=OpenArena
match=baseoa/pak0.pk3
licence=GPL-2.0

# verify against a real copy
[quake3]
kind=q3-baseq3
title=Quake III Arena
match=baseq3/pak0.pk3

# verify against a real copy
[theme-hospital]
kind=theme-hospital
title=Theme Hospital
match=DATA/VBLK-0.DAT;QDATA/FONT00V.DAT

# verify against a real copy
[duke3d-shareware]
kind=duke3d-grp
title=Duke Nukem 3D (Shareware)
match=DUKE3D.GRP
size=11035779
licence=Shareware

# verify against a real copy
[duke3d]
kind=duke3d-grp
title=Duke Nukem 3D
match=DUKE3D.GRP

# verify against a real copy
[sw]
kind=sw-grp
title=Shadow Warrior
match=SW.GRP
```

(The sizes above are the commonly published sizes of the Quake 1.06 shareware `pak0.pak` and the Duke Nukem 3D 1.3d
shareware group file; they are unverified. Variant rows
for other versions - registered/atomic Duke, Shadow Warrior's shareware - are added the same way when someone has the
file to measure. An unknown version still matches the generic row, so it is never refused for being unlisted.)

### 4.4 Matching rules

- **Case-insensitive on FAT** (and on every other stick): the scan lists each folder and compares lower-cased names;
  a `match` path is resolved segment by segment (`Id1/PAK0.PAK` finds `id1/pak0.pak`). `AB_PKG_FILE`/`AB_PKG_DIR` are
  built from the **real on-disk spelling**, so they also work on a case-sensitive stick.
- **One game per (root, main file):** the first matching row (the player's table first) wins. Different main files in
  one folder are different games: a folder with `DOOM.WAD` and `DOOM2.WAD` gives two games in one package. The same
  game in two places gives two entries (the picker shows the second line, section 6, so they can be told apart).
- **Variants** are rows in order: the specific one first (`quake` needs `pak1.pak`, `quake-shareware` is told by `size`),
  the generic last. `size` and `magic` are checked only after the names matched; a file that matches by name but fails
  `size`/`magic` does not match that row (it may match a later one).
- **The implicit package** of a recognised folder: id `u/<the root's path under Packages/, lower case, / separators>`
  (the root `Packages/` itself = `u/`), title = the folder's name (the root's real name; `Packages` itself = "Packages"),
  `Source=user`, no image, games = its hits.
- **Unknown data:** a folder directly under `Packages/` in which nothing matched, neither itself nor anywhere below it
  within the depth limit, and which has no `package.ini`, is listed as **unknown data** (title = its name). A folder that only *groups* recognised folders (`Packages/DOS/` over `Prince/`) is not unknown. Loose files that match nothing are ignored. The info view of unknown data says what to do (4.7); it is
  never offered to an engine.
- Nothing is hashed: a scan costs directory listings, `stat`, and 4 bytes of a main file when a row has `magic`.

### 4.5 Where the launcher keeps what it recognised

**In RAM, in `PackageService`, rebuilt by every scan - never on the stick.** No database row, no fingerprint file, no
index file: the quiet-stick rule (nothing written per boot or scan; nothing into the player's folders) is met by not
writing at all. Rebuild triggers: the launcher's start, a `ScanPackages` request (Store install/remove, Options rescan,
the existing change watcher - which compares a signature of the top-level listing of `Packages/` held in RAM), and the
return from an engine (cheap, and a player may have copied files over the network meanwhile). The runtime directory is
not used either.

The one thing that is persistent is the **last choice per engine** (section 6.2), in that engine's own App folder.

### 4.6 Versions of the same game

A table row may carry a `variant` and rows may differ by `size`; two folders with two versions of one game are two
entries. There is no "newest wins": the player chooses, and the last choice is remembered.

### 4.7 The instructions the player gets

One text, in three places: the manual (a page "Your own games", every language of the manual), the project's site (the
same page), and the launcher - the "No game data" message (6.4), the info view of unknown data, and `Packages/README.txt`
that the installers lay. The text says: where `Packages/` is; one example path per game family (generated from the
table's rows so it cannot drift); that file names may be in any letter case; that the player's own
files are only read, never changed; that the game's own folder can be dropped in whole; how to add an unlisted game
(`Packages/packages.ini`, one row, or a `package.ini` for a DOS game); that we never supply commercial game data.
The page's table lists every kind of 3.3 with its name and the files (it is built from `rc/packages.ini`).

## 5. The engine side

### 5.1 `app.ini`

```
Uses=doom-iwad; heretic-iwad; hexen-iwad; strife-iwad
PackageDir=WAD
```

- `Uses=` (a `;` list of kinds, case-insensitive, blanks trimmed; empty or absent = the engine takes no package and
  starts as it always did). `AppManifest` gains `uses` (a vector).
- `PackageDir=` (a `;` list of folders relative to the App's folder) - **the engine's own data folder counts as a
  source** (lzdoom's `WAD/`, TyrQuake's `.tyrquake/`, CorsixTH's `data/`): it is scanned with the same tables, up to 4
  levels down, as an implicit package (`Source=user`, id `e/<folder>`, listed in the picker marked "in this App"), but it
  is **not** in `Packages/` and does not appear in the Packages row. `AppManifest` gains `packageDirs`.
- Both are read on every platform key; they need no `Exec.<key>` variants.

For the PE route they come from `port.ini` (`uses=`, `package_dir=`) through `launcher.cfg` and proc_pe (2.3).

### 5.2 What the engine receives

After the pick (section 6) the launcher sets, in `LaunchService::appEnvironment` next to the `AB_APP_*` variables:

| Variable | Value |
|---|---|
| `AB_PKG_DIR` | The absolute path of the package root (the folder holding the game's files), no trailing slash. |
| `AB_PKG_FILE` | The absolute path of the game's main file. |
| `AB_PKG_KIND` | The game's kind id (an engine that runs several - `q3-openarena`/`q3-baseq3` - chooses its mode by it). |
| `AB_PKG_TITLE` | The game's display name, UTF-8. |
| `AB_PKG_ID` | `<package id>/<game id>` - the key of the choice and of the engine's per-game saves. |
| `AB_PKG_GAME` | The game's id alone (`freedoom2`, `doom2`). |
| `AB_PKG_STARTS` | Only when the game has `Start` programs: `FILE|Title;FILE|Title` - the first is the default. |
| `AB_PKG_SET_<NAME>` | One per `Game<N>.Dosbox.<name>` (or table `set.<name>=`) of the chosen game, name upper-cased: `AB_PKG_SET_CYCLES`, `AB_PKG_SET_MEMSIZE`, `AB_PKG_SET_SOUND`. |
| `AB_PKG_MAPPER` | Absolute path of the game's mapper file (`Game<N>.Mapper` / table `mapper=`), when it has one. |

Paths use the stick's real mount point (`/media/Autobleem/Packages/...` on the console), so a script started from
`/var/volatile/launchtmp` reads them as they are. An App started with no choice (no `Uses=`) gets none of these
variables - an engine that sets `Uses=` never sees them empty, because it is not started without a choice (5.4).

**The contract: an engine treats `AB_PKG_DIR` as read-only.** It keeps settings, saves, logs and caches in its own App
folder (or `$HOME`). This is what keeps the player's folders untouched and what lets a package sit on a read-only
medium. (An engine that writes next to its data - some DOS games do - writes to a layer of its own; section 10.)

### 5.3 Placeholders in `Args=` and `Env=`

For native Apps (and any App whose command line the launcher builds): in the resolved `Args=` and in the values of
`Env=`, these are replaced just before the start:

`{package}` = `AB_PKG_FILE`, `{package_dir}` = `AB_PKG_DIR`, `{package_kind}`, `{package_title}`, `{package_id}`,
`{package_game}`.

- Replacement happens **per argument after the line is split** (`AppManifest::splitArgs`), so a path with blanks
  (`Packages/Theme Hospital/...`) stays **one** argument on the direct (Windows) route; on the script route
  (`AB_APP_ARGS`) a value that has blanks is wrapped in double quotes, which is the quoting `splitArgs` and
  `rc/app_env.sh` already honour. (The implementer verifies the script route with a path that has a blank and fixes
  `app_env.sh` in the same commit if it does not keep the quotes.)
- An unknown `{name}` is left as it is. An App with no choice is not touched (no `{package}` replaced by "").
- Placeholders work in `Args`/`Env` only - not in `Exec`, `Lib`.
- PE ports do not use placeholders: their `launch.sh` reads `$AB_PKG_FILE` and friends.

Example, Crispy Doom as one App (replaces three):

```
Exec=bin/{key}/crispy-doom
Uses=doom-iwad
Args=-iwad "{package}" -config default.cfg -extraconfig crispy-doom.cfg -savedir savegames/{package_game}
```

Example, a PE port's `launch.sh` fragment (LZDoom): `LZ_IWAD=$AB_PKG_FILE` replaces the search of the WAD folder and
the path to the neighbouring Freedoom App; TyrQuake gets `-basedir "$AB_PKG_DIR"`; ioquake3 `+set fs_basepath
"$AB_PKG_DIR"` and `com_basegame` from `case $AB_PKG_KIND in q3-openarena) baseoa ;; q3-baseq3) baseq3 ;; esac`;
CorsixTH writes `$AB_PKG_DIR` into its `config.txt` (`theme_hospital_install`) each start. (The exact switches of the
JFDuke3D / JFSW start, `-j` and `-g`, are the implementer's to verify against the engines.)

### 5.4 0, 1 or more matches

The launcher builds the **entries**: every game of every package (Packages/ and the App's `PackageDir`) whose kind is in
the engine's `Uses=` (case-insensitive). Then:

| Entries | What happens |
|---|---|
| 0 | The "No game data" message (6.4); the engine is not started; Cross or Circle returns to the carousel. |
| 1 | The engine starts at once with that entry. No screen. (The choice is still remembered.) |
| 2 or more | The picker (section 6). |

The check runs on every start (the index is in RAM; the entries' files are checked to still exist right before the
start - a vanished file shows the message instead of a crashing engine).

## 6. The picker

A launcher screen (the launcher's own list screen, not the PE choice dialog, which only has four answers), `GuiPackagePicker`.

### 6.1 Behaviour

- **Title**: the App's title; the screen's heading "Choose game data".
- **Rows**: one per entry. First line: the game's title (+ variant). Second line (smaller font): the package's title
  (`Source` label - "Store" / "Mod" / "Your files" / "In this App") and the kind's display name. Two entries with the
  same game title are told apart by that second line.
- **Order**: by the position of the entry's kind in the engine's `Uses=` list, then by game title (case-insensitive,
  natural number order), then by package title. Stable between runs.
- **Cursor** starts on the last choice for this App (6.2), else on the first row. Up/Down move, L1/R1 page, the list
  scrolls and the usual hold-repeat applies (the set picker's list widget).
- **Cross** = pick: the choice is stored (6.2) and the engine starts. **Circle** = back to the carousel; nothing is
  started, nothing is stored, no confirmation.
- The hint bar: Cross "Start", Circle "Back" (existing strings).
- Input follows the busy rule (a scan in progress does not eat the first press); a theme's own list colours and fonts
  apply; it is drawn in the same layer system as the set picker so the 5 themes need no per-theme code.

### 6.2 The last choice - where and how, quietly

`<App folder>/ab_settings.ini`, key `LastPackage=<AB_PKG_ID>` - the existing per-App file of `AppSettings` (the Store and
`AppInstaller` already keep it across updates). Written **only when the pick differs from what is stored**, through
`writeFileIfChanged`; an App the player starts with one entry never gets the line unless the entry changed. Not in the
runtime directory (it must survive a reboot) and not in the player's folders. `AppSettings` gains
`lastPackage(appFolder)` / `setLastPackage(appFolder, id)`; the file goes when nothing is left in it (as today).

### 6.3 16:9 and 4:3

The list uses the available height in whole rows; the second line is a truncated single line with an ellipsis (never
wraps); the heading is one line. At 4:3 the same rows with the narrower width - the second line truncates earlier (title
first, kind last: the kind is dropped before the package title). The row height never changes between the two aspects;
only the number of visible rows and the text width do. Acceptance: shots in both aspects in all five themes, with 2
entries, 8 entries (scrolling) and an entry with a very long title (ab_drive walk, section 12).

### 6.4 The strings (every `_()` key; the implementer adds them to all 16 language files in the same commit)

Launcher (core/launcher):

- `Choose game data`
- `No game data found`
- `%1 needs game data it can run: %2.` (`%1` the App's title, `%2` the kinds' display names, comma separated)
- `Put the game's files into the Packages folder on the stick (for example Packages/Doom/DOOM2.WAD), or get a package from the Store. Your own files are only read, never changed.` - this reuses the manual's text (4.7), so keep them identical.
- `In this App` (the source label of an engine's own folder), `Store`, `Mod`, `Your files`
- `Packages` (the row's name, `appCategoryName(AppCategory::Packages)`)
- info view labels: `Contents`, `Kind`, `Version`, `Licence`, `Source`, `Runs with`, `Location`, `Nothing installed runs this`
- `Unknown data`, `Not recognised. If this is a game, see the manual: Your own games.`
- `Shareware`, `Free` (the table's `licence` values when they are these words - table values are shown as they are, these two are translated)
- the kinds' display names of 3.3 (`Doom data`, `Heretic data`, `Hexen data`, `Strife data`, `Quake data`, `OpenArena data`,
  `Quake III Arena data`, `Theme Hospital data`, `DOS game`, `Duke Nukem 3D data`, `Shadow Warrior data`)

Store (ext_store's own language files): `Packages` (the type), `Needs: %1`, `Also installs: %1`, `Needs game data: %1`,
`Installed with %1`, `Needs: %1 (not in the Store)`.

Existing keys are reused where the text is the same (`Start`, `Back`, `Version`, `Licence`).

## 7. The "Packages" row and the info view

- `AppCategory` gains **`Packages` at the end** (value 7; the order is stored in the carousel session file, so nothing is
  renumbered); `AppCategoryLast = Packages`; `appCategoryName(Packages)` = "Packages". `parseAppCategory` never returns
  it (an App's `Category=Packages` is `Other`): Packages are not Apps.
- `GameQueryService::appCategories()` lists the Packages row **only when the index holds at least one package** (like the
  PE row), unknown data included, after the other rows; its count is the number of packages. `apps(All)` and the
  `Counts::apps` total do **not** include packages; `apps(Packages)` returns one `PsGame` per package: `app = true`,
  `package = true`, `package_id`, `base` = the package's folder (a recognised root for a user's folder), `title`,
  `image_path` (`Image=` or the generic icon), `readme_path`.
- The carousel shows them like the other App rows. **Cross opens the info view; nothing is launched**, no resume, no
  game menu, no pad settings. The launch path asserts `!game.package` (a test, section 12). The Start/Triangle
  game menu is not opened for a package.
- **The info view** (`GuiPackageInfo`, the style of the existing App readme/details view): title, version, source
  ("Store", "Mod", "Your files"), licence, the **games** (title + variant + kind name, one per line), `Description`,
  the readme text when there is one, the **location** (the folder relative to the stick's root), and **Runs with:** the
  titles of the installed Apps whose `Uses=` includes any of the package's kinds (from the Apps manifests, computed when
  the view opens), or "Nothing installed runs this" with the Store hint. Circle closes it. Unknown data shows its name,
  "Unknown data" and the "Not recognised" text, and an empty "Runs with".
- Removal of a package is not offered by the launcher (the player's files are his; the Store removes what it installed).

## 8. The Store

### 8.1 Catalog

`StoreItem.kind` gains the documented value **`package`** (a `.zip`/`.tar.gz`/`.7z` with a `package.ini`, 2.4). The new
and changed catalog fields, JSON (`store/<platform>/catalog.json`) and TSV (columns of the same names):

| Field | Meaning |
|---|---|
| `category` | Already added by the Store item types work (branch `feature/store-types`): the item's type, lower case. A package item says **`packages`**; the launcher's `AppCategory` names stay `games`, `emulators`, `tools`, `media`, `other`, `pe`, `packages`. An installed App takes the catalog's category only when its `app.ini` names none - an App is never put in `packages`. |
| `provides` | **New.** The content kinds a package item holds (`["doom-iwad"]`). Lower-cased, trimmed, unknown kept. For display ("Content") and for the engine's "needs game data" hint. |
| `uses` | **New.** The content kinds an engine item runs - the same list as its `app.ini` `Uses=`. For display and the hint. |
| `requires` | Already read into `dependsOn` and ignored; now honoured (8.2). The ids of other items (`pkg/freedoom`, `pkg/openarena`). |

```json
{"id": "pkg/quake-shareware", "kind": "package", "title": "Quake (Shareware)", "version": "1.06",
 "category": "packages", "provides": ["quake-id1"], "licence": "Shareware (id Software)",
 "files": [{"url": "https://.../quake-shareware-1.06.zip", "size": 9461876, "sha256": "..."}]}
{"id": "pe/tyrquake", "kind": "pe", "title": "TyrQuake", "category": "games", "uses": ["quake-id1"],
 "requires": ["pkg/quake-shareware"], "files": [{"url": "https://.../tyrquake.mod"}]}
```

### 8.2 "Needs" and install-together

- The engine's detail shows **"Needs: <title> (<size>)"** for each `requires` id found in the loaded sources (installed
  ones with a tick), **"Needs: <id> (not in the Store)"** for one that is not, and, when it has `uses` and nothing in
  `requires`, "Needs game data: <kind names>".
- **Install** of an item whose `requires` are not installed adds the missing items to the work queue **before it**
  (dependencies of dependencies first, each once; a cycle is refused at load with a log line). The confirmation dialog
  lists them ("Also installs: Freedoom (58 MB)") with the total size and the free-space check on the sum. A dependency
  that fails stops the item behind it (it stays queued as "waiting for X", no half state); the user can still install
  the engine alone from the dialog's second answer.
- Remove has no reference counting: removing a package an engine uses leaves the engine's picker with fewer entries (or
  the "No game data" message). The Store says nothing more.
- The Store's installed list (`installed.tsv`) records package items like any other; `PackageInstaller` also stamps
  `StoreId` so an installed folder is found without it.
- The site (autobleem-repo) lists the same "Needs" on each item page, from the same catalog fields.

### 8.3 What changes in which repository

ext_store: `supported()` takes `package`; the installer step calls `PackageInstaller`; `Update::packagesChanged` ->
`requestRescan(ScanPackages)`; the detail view's "Type"/"Content"/"Needs" lines; queue order for `requires`; the strings
of 6.4. autobleem-repo: the catalog generator emits `kind`, `category`, `provides`, `uses`, `requires` for each item
(the app_* repos' `tools/store_item.py` write them); the item page shows them.

## 9. Core: exactly what changes (folded into ABI 10)

`AB_SDK_ABI` stays **10** - the same unreleased bump the Store item types already joined (`extension.h`'s note gets a
second line). Console-tools and pc-tools are re-pointed once, after both pieces are in. The layout- or signature-visible
changes:

| Where | Change | Extension-visible |
|---|---|---|
| `lib_ableem/.../store_catalog.h` `StoreItem` | `+ category` (already there), **`+ std::vector<std::string> provides`, `+ std::vector<std::string> uses`**; parsers for the JSON keys `provides`/`uses` and TSV columns of the same names (lower-case, trimmed); `kind` comment lists `package` | yes (the Store reads it) |
| `src/code/core/model/ps_game.h` `PsGame` | **`+ bool package = false; + std::string package_id;`** (appended last) | yes |
| `src/code/core/model/game_set.h` | `AppCategory::Packages = 7`, `AppCategoryLast`, `appCategoryName`; nothing renumbered | indirectly (stored order) |
| `src/code/core/model/scan_scope.h` | **`ScanPackages = 16`**, included in `ScanAll`; `ScanScope` stays `unsigned`; `ScanService::checkForChanges`/`runScan` handle it (RAM signature, no fingerprint row) | yes (`requestRescan(ScanScope)`) |
| `src/code/core/services/app_manifest.*` `AppManifest` | `+ std::vector<std::string> uses; + std::vector<std::string> packageDirs;` read in `resolve` from `Uses=`/`PackageDir=` | no |
| NEW `services/package_table.*` | `PackageTable` (parser of 4.3), `PackageRow` | no |
| NEW `services/package_service.*` | `PackageService`: the scan of 2.1/4.4, the RAM index, `PackageInfo`/`PackageGame`/`PackageEntry` structs, `entriesFor(const AppManifest&)`, the kind display names, the descriptor reader of 2.2 | no |
| `services/launch.*` | `LaunchService::planApp(const PsGame &, const PackageEntry * = nullptr)` and `appEnvironment(const AppManifest &, const PackageEntry * = nullptr)`: the `AB_PKG_*` variables and the placeholders of 5.3; an assertion that a `package` game is never launched | no |
| `services/app_settings.*` | `lastPackage`, `setLastPackage` (6.2) | no |
| `services/content_installer.*` | NEW `PackageInstaller` (2.4); `ModInstaller::remove/present` also cover `Packages/` (2.3) | no |
| `services/environment.*` | `getPathToPackagesDir()`, `getPathToPackagesTable()` (the `rc/` file) | no |
| `services/game_query.*` | `appCategories()` adds the Packages row, `apps(Packages)`; `apps(All)`/`Counts::apps` exclude it | no |

Quiet stick: `tests/core/test_quiet_stick.cpp` gains a stick with a populated `Packages/`; two scans and a launch of a
picked entry leave the tree snapshot unchanged (the only allowed write is `ab_settings.ini`, and only on a changed choice).

## 10. DOSBox (APPS-10) as a consumer

The owner's decision (2026-10-06): **DOS games are reached only through DOSBox.** DOSBox is an App with `Uses=dos-game`; there
is no MS-DOS row in the games list and no "runtime-only" concept.

- A DOS game is a package of kind `dos-game`: a `package.ini` (ours, from the Store) or the player's own descriptor / a
  row of his `Packages/packages.ini`. The descriptor carries, per game: `Game<N>.File` (the main program), the **start
  programs** (`Game<N>.Start<M>.*` / `start=`: the game, `SETUP.EXE`), the **per-game DOSBox settings**
  (`Game<N>.Dosbox.Cycles`, `.Memsize`, `.Sound`) and an **optional per-game mapper file** (`Game<N>.Mapper`) - 2.2.
- The flow: the player starts DOSBox -> the launcher's picker lists the `dos-game` packages (the same screen as every
  engine) -> after the pick the engine gets `AB_PKG_DIR` (to mount as `C:`), `AB_PKG_FILE`, `AB_PKG_STARTS`,
  `AB_PKG_SET_*` and `AB_PKG_MAPPER` -> **with two or more starts the DOSBox start script shows its program choice
  (Game / Setup)** and runs the chosen one; with one start it runs it. DOSBox with no `dos-game` package shows the
  launcher's "No game data found" message with how to add games.
- **The one exception to "`AB_PKG_DIR` is read-only" (5.2): a `dos-game` package is mounted read-write.** DOS games
  write their saves and settings (SETUP's config) next to themselves, and our engine is DOSBox 0.74 (the 2020 SDL2
  line - it has no overlay mount; DOSBox-staging needs a newer compiler than the image's gcc-6). So DOSBox mounts the
  package folder as `C:` read-write; the game's writes land in its own folder, which is what the player expects from a
  DOS game. Nothing else writes there (the launcher still never does). An overlay is a later idea, if the engine moves.
- **This spec does not depend on APPS-3** (the pad's keyboard mode, moved to alpha2): the picker and the program choice
  are launcher/engine screens on the normal pad, and a game's keys come from its optional mapper file. Until APPS-3,
  games that need keys are limited by what the mapper file can bind.
- The Store's "MS-DOS games" = catalog items `kind: "package"`, `provides: ["dos-game"]`; the DOSBox item's
  `uses: ["dos-game"]` gives the "Needs game data" hint. A new DOSBox icon is designed separately.

## 11. Migration of the old data Apps (nothing lost, nothing deleted)

| Today | After |
|---|---|
| `Apps/pe-freedoomdata`, `Apps/pe-openarenadata` (PE data Apps; no saves, only data files) | The Store's new `pkg/freedoom` / `pkg/openarena` zip package installs `Packages/freedoom` (2.3, 2.4); its `Replaces=pe-freedoomdata` makes `PackageInstaller` **park the old App** in `Apps/.replaced/` once the package is in place (a failed install leaves the App; an App that is not ours - no `PeSource=` - is left alone). The old `.mod` in `Mods/done/` is inert (never reprocessed). The old catalog ids `pe/freedoomdata`, `pe/openarenadata` leave the catalog; the Store lists them as "installed, not in the catalog" until removed (Remove deletes the parked/old data as today). |
| lzdoom's `LZ_FREEDOOM=../pe-freedoomdata` and ioquake3's `OA_DATA` | Replaced by `AB_PKG_*` in the same pe_ports release as the packages (`requires=` points at the data package, so the Store installs both). The engine's own data (`WAD/`, saved games, `lzdoom.ini`) is not moved. |
| Crispy Doom's three Apps `Apps/doom`, `Apps/freedoom1`, `Apps/freedoom2` (each with its own `savegames/`, `default.cfg`, `crispy-doom.cfg`) | One App `Apps/crispydoom`, `Uses=doom-iwad`; the data is two Store packages (`pkg/doom-shareware`, shared Freedoom `pkg/freedoom`) that the App `requires`. **Saves are filed per game**: `-savedir savegames/{package_game}`, where the game id is the row id / `Game<N>.Id` (`doom1-shareware`, `freedoom1`, `freedoom2`). |

**The Crispy Doom saves migration** is declared by the new App's `app.ini` and done once by `AppInstaller` when the new
App is installed (Store or by hand): 

```
Replaces=doom; freedoom1; freedoom2
Migrate=doom:savegames>savegames/doom1-shareware; freedoom1:savegames>savegames/freedoom1; freedoom2:savegames>savegames/freedoom2; doom:default.cfg>default.cfg
```

- `Migrate` entries are `<old App folder>:<path in it>><path in the new App>`; a path is a file or a folder. **Copy, never
  move**; a destination that already exists is not overwritten; an entry whose source is missing is skipped. The
  operation is idempotent (a second install copies nothing new).
- `Replaces=` names the old Apps (the same key serves a package's `package.ini`, 2.2). After the copies **succeed**, each old App folder is **moved** (renamed, the same
  filesystem) to `Apps/.replaced/<name>/` - hidden from the Apps scan (dot-folders are skipped), restorable by the
  player by moving it back, never deleted. If any copy failed, nothing is moved and the old Apps stay beside the new one.
- The old Store ids (`app/doom`, `app/freedoom1`, `app/freedoom2`) leave the catalog in the same release; the Store's
  installed list keeps their rows as "installed, not in the catalog" until the player removes them.
- The same mechanism (`Replaces=`/`Migrate=`) is available to any later App that merges others. It is a core feature
  (tested in `test_content_installer`), not a Crispy Doom special case.
- Nothing in the launcher moves or deletes anything at start-up: migration happens only inside an installer, at the
  player's or the Store's request.

Duke3D and Shadow Warrior: the shareware group file moves out of the App into packages (`pkg/duke3d-shareware`,
`pkg/sw-shareware`) that the Apps `require`; the Apps get `Uses=duke3d-grp` / `Uses=sw-grp`. Their saves and settings stay in the
App folder, which does not change, so nothing is migrated.

## 12. Tests (the unit tests each repository needs, shipped with the change)

Native tests run on the laptop through `ci/build.sh native`; tests of file layouts build a temporary tree and never touch
a real stick. The scan tests use a faithful in-memory listing where the real filesystem would behave differently (case).

**autobleem-core**
- `test_package_table`: comments, `[row-id]` grammar, missing `kind`/`title`/`match` skipped with a log, `;` lists,
  keys in any case, CRLF and BOM, `#` inside a value kept, the player's table before the shipped one, 500 rows load.
- `test_package_scan` (temporary trees): `Doom/DOOM.WAD` + `DOOM2.WAD` = one package, two games; upper, lower and mixed
  case names (`Id1/Pak0.Pak`, `doom.wad`); real spelling reaches `AB_PKG_FILE`; Quake full (`pak1.pak` present) vs
  shareware (by `size`) vs generic, in that order; `magic=IWAD` mismatch does not match; nested `Packages/DOS/Prince`
  and the depth limit (4 matches, 5 does not); the 2000-folder cap; a descriptor package is not descended and wins over
  a table row inside it; loose files at `Packages/`; hidden/`$`/`System Volume Information` skipped; a grouping folder is
  not unknown, an empty or non-matching one is; the same game twice = two entries; ids stable across scans; a missing
  `Packages/` = an empty index and **no directory created**.
- `test_package_ini`: every key of 2.2 (`Replaces`, `Dosbox.*`, `Mapper` included), `Game<N>` gaps stop the list, a missing file drops the game, an escaping path
  (`..`, absolute, a drive letter) drops it, a bad kind/id is rejected, a 64 KB+ file is refused, `Start` lists, `Kind`
  list vs per-game kind.
- `test_package_match`: an App's `Uses=` against kinds (case, blanks, several kinds, empty = no picker), the entries'
  order, an engine `PackageDir` source, an unknown kind kept.
- `test_launch` additions: `AB_PKG_SET_*` and `AB_PKG_MAPPER` from a dos-game choice; `AB_PKG_*` present only with a choice; every placeholder; an unknown `{x}` untouched; a path
  with a blank is **one** argument on the direct route and quoted on the script route; `Env=` placeholders; a `package`
  game refuses to launch.
- `test_app_manifest`: `Uses` and `PackageDir` parse, with blanks and case.
- `test_app_settings`: `LastPackage` round trip; a second identical write leaves the file's size and mtime alone; the
  file goes when empty; `AppInstaller` keeps it across an update.
- `test_game_query` / `test_game_set`: the Packages row only with packages, last in the list, outside the `apps` total,
  `apps(Packages)` entries flagged; the carousel session round-trips category 7 and an old session file still loads.
- `test_store_catalog`: `provides`, `uses`, `requires`, `category` in JSON and TSV; `kind: package` kept; an item without them unchanged.
- `test_content_installer`: `PackageInstaller` install / replace-newer / no-op-same / refuse-broken (nothing left in
  `Packages/`) / FAT-safe and duplicate folder names / stamps `Source` and `StoreId` / `remove` only stamped folders, never
  a player's; `Replaces=` in a package parks the old App only after the install succeeded; `ModInstaller::remove` and `present` with a package made from a mod; `Replaces`/`Migrate` copy, no
  overwrite, idempotent, nothing moved after a failed copy, old App parked in `Apps/.replaced`.
- `test_scan_scope`/`test_scan_service`: `ScanPackages` is in `ScanAll`; the watcher asks for it when the top-level
  listing signature changes and for nothing when it does not.
- `test_quiet_stick`: a populated `Packages/` leaves the tree snapshot identical across two scans and a start.
- `test_sdk_abi`: still 10 (the existing check).

**launcher**: `GuiPackagePicker` with the faithful Input stub (`tmp/ab-gui-testfix/stubs.cpp` extended, not a thinner
copy): 0 entries = message and no start, 1 = start without a screen, 3 = picker; cursor on the last choice; Circle = no
launch and nothing stored; Cross stores once (a second identical pick writes nothing); the layout test for 16:9 and 4:3
(row rectangles inside the screen, the second line truncated not wrapped); the Packages row appears/disappears; Cross on
a package opens the info view and never calls the launch path; the info view's "Runs with" list; `lang_tools validate`
over every new key in all 16 languages; the shots walk (two entries, eight, a long title, "No game data", the Packages row
and an info view; 16:9 and 4:3; five themes) on a VM sandbox through `ab_drive.py`.

**proc_pe** (only if the old-`.mod` route is kept, 2.3): a `.mod` with `launcher_package="1"` makes `Packages/pe-<name>/` with `package.ini` stamped (`Source=mod`,
`PeSource`, `Version`, `Image`) and **no App and no `launch.sh`**; a missing or invalid `package.ini` = `#WARN`, nothing
added; a game file that does not exist = refused; path traversal and over-size limits as for Apps; replace / older
refused / same skipped / foreign folder left alone; the old `Apps/pe-<id>` with our `PeSource` is removed only after the
package is in place; an engine launcher folder's `launcher_uses`/`launcher_package_dir` become `Uses=`/`PackageDir=`
and an invalid value is dropped with a warning; every existing test unchanged.

**pe_ports**: `mkmod.py` tests: a `[package]` section validates (kind grammar, every game file in the staged data) and builds
`<id>-<version>.zip` with `package.ini` (accepted by core's reader and `PackageInstaller`) plus a `package` Store item with
`provides`, size and sha256; `replaces`, `start`, `mapper` and `dosbox.*` reach `package.ini`; an engine's `uses=`/`package_dir=` land in `launcher.cfg`; a data port without a
`[package]` section fails the build; the engines' start scripts (`psc-pad.sh` of lzdoom, ioquake3, CorsixTH, tyrquake) run
under `sh -n` and, with `AB_PKG_FILE`/`AB_PKG_DIR`/`AB_PKG_KIND` set in a temporary folder, produce the expected `-iwad`,
`fs_basepath`, `com_basegame`, `theme_hospital_install`.

**app_crispydoom / app_jfduke3d / app_jfsw**: `tools/store_item.py` emits `uses`/`requires`/`category`; the `app.ini`
check (kinds in `Uses=` are in the vocabulary; `{package}` only where `Uses=` is set; `Replaces`/`Migrate` syntax); a
sample install over the old three Apps on a temporary tree copies the saves per game and parks the old Apps.

**ext_store**: `supported()` takes `package`; the queue puts a missing `requires` before its item and none for an
installed one; the "Also installs" total and the free-space check on the sum; a failed dependency stops the item behind it;
a cycle is refused; install and remove of a package item; `Update::packagesChanged` asks for `ScanPackages`; the detail
lines; the strings in 16 languages (the existing language test).

**autobleem-repo**: the catalog generator output for `package`, `pe` data and engine items; the schema check accepts
`provides`/`uses`; the item page shows "Needs".

**autobleem-manuals**: the page "Your own games" in every language of the manual; the generated table matches `rc/packages.ini`
(a test that fails when a kind or row has no line in the page).

## 13. Order of work and who touches what

1. **This spec** (APPS-12 step 1) -> reviewed, then fixed.
2. **autobleem-core + launcher** (section 9, 5-7, 12): the table and scan, the picker, the row, the launch env, `PackageInstaller`.
   In parallel **ext_store + catalog** (section 8) on the same ABI 10 note.
3. **proc_pe + pe_ports**, then **app_crispydoom, app_jfduke3d, app_jfsw** (the engines read the choice; migration).
4. The manuals page and the site.
5. console-tools / pc-tools re-pointed once; VM walk; one device round.

Docs to update with the implementation: the launcher's `CLAUDE.md` and `docs/store-plan.md` (catalog fields, install
route), `docs/developer-guide.md` (a short "Packages" section and the quiet-stick line), the Store's `CLAUDE.md`,
`docs/pe-store-plan.md` (data ports), the pe_ports `README.md` ("port.ini": `[package]`, `uses`, `package_dir`), proc_pe's
`CLAUDE.md`, each `app_*` `CLAUDE.md`.

## 14. Decisions (the owner, 2026-10-06) and what is left

Answered, and written into this spec:

1. Doom mods (PWADs) **stay in the engine's `MODS/` folder** for alpha1.2 (3.4). A `doom-pwad` kind is a later row.
2. pe_ports data (Freedoom, OpenArena) is **republished as zip `package` items**; one data format for every package
   (2.3). The old data Apps migrate (11). proc_pe's `.mod` data route is kept only for old/third-party mods (2.3).
3. DOSBox is an App with `Uses=dos-game`; **DOS games are reached only through DOSBox** (10).
4. The three old Crispy Doom Apps are **parked in `Apps/.replaced/`** after the saves are copied (11).
5. The Packages row shows **only when at least one package exists** (7).
6. The player's own read-only `Packages/packages.ini`: **yes** (4.2).
7. For the device round the owner has only the full Quake (`id1/pak0.pak` + `pak1.pak`); every other identifying-file row
   is marked "verify against a real copy" (3.3, 4.3) and Quake's is verified at the round.

Decided by the lead: proc_pe keeps the small old-`.mod` data route (2.3) for old and third-party data mods.
