# Homebrew in the Store - plan (2026-09-25, not started)

The owner, 2026-09-25: offer free PlayStation homebrew in the AutoBleem Store from a TSV hosted on our site.
The binaries stay on their original pages; we host only the list and the covers. The covers must go along
with the download, so the launcher shows the right art. Admins edit the list (add, change, remove) in the
admin panel. **Research only - nothing here is implemented yet.**

It touches three repositories:
- **autobleem-repo**: the TSV, the covers, a publish workflow, the admin panel's new tab;
- **ext_store**: our homebrew list as a built-in source;
- **autobleem-core**: the cover and a Game.ini installed with the game.

## 1. What exists today (checked 2026-09-25)

**The Store already reads the right format.** `StoreSourceTsv` (core, `lib_ableem/src/engine/store_catalog.cpp`)
takes a header-named TSV: `kind`, `title`, `url` are required. `size`, `sha256`, `disc`, `serial`, `image`,
`description`, `author`, `licence` and `version` are read. Unknown columns are ignored, so new ones can be
added without breaking an older Store.

**Downloads from other hosts work.**
- `store_download_command` is `curl -sfL -C -` on the PC targets and `abfetch --continue` on the console.
  Both follow redirects (`abfetch`'s `fetch.cpp`, up to `maxRedirects`).
- Both hosts we use redirect (archive.org to a `dnNNNN.*.archive.org` node, GitHub to
  `release-assets.githubusercontent.com`) and answer a `Range` request with `206`, so a download resumes.
- **GitHub's redirect is signed and expires after about an hour.** A resume after a standby must request the
  original URL again, never the one it was redirected to. Check that `abfetch --continue` and `queue.txt`
  keep the original.

**The installer takes what these hosts serve.** `ContentInstaller` (core, `content_installer.cpp`):
- unpacks `.zip`, `.7z` and `.tar.gz`, and takes a bare disc file as it is;
- finds disc files at any depth: `chd pbp cue bin img iso ecm sbi m3u` (plus `pkg`, listed as not
  installable);
- writes a `.cue` for a bare `.bin`;
- installs into `System/Store/staging/<id>/`, then renames to `Games/<title>/`;
- **fails with "no PlayStation disc image" when there is none.** That is why a bare Net Yaroze `.exe` cannot
  be offered.

**The installer does nothing with covers yet.** `StorePictures` shows the TSV's `image` in the Store only when
our covers databases do not know the game. Homebrew is never in them, so `image` is what shows there. After
the install, the launcher knows nothing of that picture.

**How the launcher finds a game's cover** (core, `usb_game.cpp` / `game_scanner.cpp`):
- The carousel takes `<first disc name>.png` next to the game **before anything else**. That is the file the
  scan writes from the covers database.
- A PNG byte-identical to `default.png` is removed by the scan. A real cover is never touched.
- `Game.ini` with `automation=0` is a *locked* game. The scan keeps its `title`, `publisher`, `year`,
  `players` and `serial` (`game_database.cpp`: `locked = automation != 1`).

**The admin panel** (autobleem-repo `admin/`) already has most of what an editor needs:
- FastAPI, behind oauth2-proxy (GitHub login), at `/admin/`;
- org members read, the `release-managers` team acts;
- every action goes to `audit.jsonl`, and a browser's POST needs `X-AB-Request: 1`;
- it mounts the site's tree **read-only**, and acts by starting workflows through the `autobleem-admin`
  GitHub App, which has **Contents: read and write** on every repository.

**The site publishes through `repo_publish.sh <kind>`.** `store/<platform>/` is our catalog: `index_store()`
builds `catalog.json` from `<id>.item.json` descriptors and needs every file *on our disk*, so an external
URL does not fit the catalog as it is.

## 2. Which games (the seed list)

Of 95 games collected on 2026-09-25 (the "PS1 Homebrew Shelf" artifact), **34 can be installed straight from
their original host**. Every download was opened to check that a disc image is inside. Sizes add up to about
2.4 GB.

The other 61 cannot be offered this way:

| Reason | Games | What would unblock them |
|---|---|---|
| itch.io only | 34 (Sonic XA, Yume Nikki, the FNAF trilogy, the Bonnie Studios games, Celeste Classic, Loonies 8192, Wolfenstein 3D / Rick Dangerous PSX, ...) | itch.io has no fixed download link: each download is a short-lived signed URL made after a JavaScript step (and scraping it would be against its terms). Ask each author for a GitHub/archive.org release, or for permission to mirror (`repo_publish.sh mirror`). |
| An `.exe` with data files, no disc | 18 (most single Net Yaroze games: Blitter Boy, Time Slip, Super Bub Contest, ...) | Many of them are on the Net Yaroze Collection disc, which is in the list. Building a disc image for each ourselves would be mirroring. |
| A page, source code or a source repository only | 9 (Terra Incognita, Doki Doki Literature Club, Tiny Backrooms, Super Mario 64, Deathball, ...) | A release from the author. |

Things the seed list needs to handle:
- **Another World (rawpsx)**: use the release's `rawpsx_demo.iso`. The `rawpsx-r3.zip` next to it is the
  engine alone, with an empty `data/`.
- **Tetrade**: the `.bin` and the `.cue` are separate release files, so two lines with the same title.
- **Net Yaroze 2014**: the zip holds three ISOs (NTSC, PAL, PAL & NTSC). As it stands, they would install as
  one three-disc game. Needs `members` (section 3.1).
- **Dragon's Lair Trilogy**: three different games in one zip. Needs `members`, so three items from one URL.
- **PSone Miner**: the download is the author's source repository with the ISO inside. It works, it is just
  bigger than it needs to be.
- **Snake 3D** is not in the list: its archive.org zip is the source code and assets.
- Covers: three have none (Nortis, QuakePSX, Tetrade). The archive.org ones are screenshots or title
  screens. Real box art hardly exists for homebrew.


## 3. Design

### 3.1 The TSV and the covers on the site

**The source of truth lives in git**, not on the site:
- `store-homebrew/homebrew.tsv` in autobleem-repo, one line per file;
- `store-homebrew/covers/<id>.png`, the covers as we serve them;
- `store-homebrew/covers/src/<id>.<ext>`, the image as an editor supplied it.

Git gives history, review and revert, and it is what the panel writes to (3.4).

**Published to** `https://<site>/store/homebrew/`:
- `homebrew.tsv`: the same file, with `size`, `sha256` and `image` filled in by the workflow;
- `covers/<id>.png`.

The same TSV serves every platform: a PS1 game installs the same way on the console, a Pi, the PC stick and
Windows.

**Columns**: the existing ones, plus a few new ones an older Store ignores.

| column | new? | meaning |
|---|---|---|
| `id` | new | stable key, `ps1-<slug>`; names the cover file and survives a title change |
| `kind` | | `ps1` |
| `title` | | as the Store and the carousel show it |
| `url` | | the file on its original host (archive.org, GitHub) |
| `disc` | | the file's disc number; lines with the same `kind` + `title` are one item |
| `members` | new | optional glob(s), `;`-separated: which files of the archive are this item's (Net Yaroze 2014, Dragon's Lair Trilogy) |
| `size`, `sha256` | | written by the workflow after it has fetched the file once |
| `image` | | our cover URL, written by the workflow (`covers/<id>.png`) |
| `author` | | also written into Game.ini as `publisher` |
| `year`, `players`, `genre` | new | Game.ini's `year` and `players`; `genre` for the Store's details |
| `page` | new | the game's own page (credit, and where the Store's details send a user) |
| `description`, `licence`, `version` | | as today |
| `serial` | | only when the disc has a real serial of its own; left empty otherwise |

**Covers**:
- Normalised by the workflow, never by hand: PNG, square, 512x512, the art fitted inside on black (jewel-case
  proportions, like the covers databases' art).
- Kept in git, so the site never depends on a third-party image host.
- Editors supply the art. The seed covers are the ones the artifact used (the cover column in section 6).

### 3.2 Publishing and checking (autobleem-repo workflow `store-homebrew.yml`)

**Triggers**: a push to develop that touches `store-homebrew/`, a manual run, and a nightly link check.

**Steps**, on the self-hosted runner, in the build image:
1. **Validate** each line: the required columns, a unique `id`, and a URL on an allowed host (a list:
   archive.org, github.com, gitlab.com, sourceforge.net - itch.io refused with a message).
2. **Fetch every new or changed URL once.** Record `size` and `sha256`, and list the archive: a disc image
   must be inside, matching `members` when given.
   - The result is cached in `store-homebrew/.verified.json` (URL -> size, sha256, member list, date), so
     an unchanged line is not fetched again.
   - The first run is about 2.4 GB. After that only changes are fetched.
3. **Normalise the covers** (Pillow).
4. **Publish** with `repo_publish.sh --local homebrew FILES` (a new kind, `DEST=store/homebrew`). The page
   generator merges it as usual.

**A failed line** is left out of the published TSV and reported in the job summary; the rest still publishes.
Telegram says so once the panel's notifier is set up.

**The nightly link check** is a `Range: bytes=0-0` request per URL. It compares the total size with the
recorded one:
- a URL that fails, or whose size changed, is marked in `.verified.json`;
- the panel shows it red (3.4);
- the line stays published, and the Store's sha256 check refuses a changed file.

The Store page on the site (`render_store`) can get a **Homebrew** tab from the same TSV, using the approved
pieces only (the `download-page-style` rules): a small table of What | Author | Year | Size | Page.

### 3.3 The Store and the installer (ext_store + autobleem-core)

**Where the list comes from.** `decisions.md`'s Store entry says "We ship no source but our own catalog". Two
ways to fit that:
- **(a) Recommended**: the homebrew TSV counts as part of *our* catalog. The Store reads `store_homebrew_url`
  (derived from `repo_url`, like `catalogUrl`, and overridable with `AB_STORE_HOMEBREW` for testing) as a
  built-in source.
  - The user cannot remove it, but can hide it with Select, as with any source.
  - `decisions.md` gets a line saying so.
- **(b)** `index_store()` learns external files, and the TSV is folded into every platform's `catalog.json`
  as `ps1` items. That means no Store change, but the catalog format gains remote files, and the TSV is then
  an internal file rather than what the Store reads.

**Installing the cover and the facts with the game** (`ContentInstaller`, in staging, before the rename):
- **The cover**: the item's `image` is fetched into staging as `<first disc name>.png`, the name the carousel
  takes first.
  - Only when the archive did not bring one of that name.
  - Only for items from our own sources, or any source (to decide - it is cheap either way).
  - A failed cover fetch does not fail the install.
- **Game.ini**: written with `title`, `publisher` = `author`, `year`, `players`, and `automation=0`, so the
  scan keeps them.
  - This matters because homebrew serials are often dummies or copies of a commercial game's. Last Survivor
    carries `SLUS_034.34`. Without the lock the scan would name it after whatever that serial is in the
    rdb, and pull that game's cover from the covers database.
  - `serial` is written only when the TSV gives one.
- **Picking files**: `members` limits which files of an archive are taken. It is a general feature, useful to
  any source.
- **Remembering it**: `installed.tsv` already records the item. Nothing more is needed for a later update
  (a new `sha256` = an update).

**Tests** (`tests/core/test_content_installer.cpp`, ext_store's `test_store_service.cpp`):
- a cover and a Game.ini are installed with the game, and the scan keeps them (a scan over the installed
  folder in the same test);
- `members` picks the right files;
- a resume re-requests the original URL.

### 3.4 The admin panel's Store tab (autobleem-repo `admin/`)

**Who**: org members see the tab. A new team, **`store-editors`**, edits: a content job, not a release job
(`AB_STORE_TEAM`, default `store-editors`; `release-managers` may edit too).

**The page**, a new tab in `app/static/index.html`, in the panel's existing look. A table of the entries:
- the cover (thumbnail), title, author, year, host, size;
- the last check (green, or red with the reason from `.verified.json`);
- the published or not-yet-published state.

**Actions**:
- **Add / Edit**: a form with the columns of 3.1.
  - Cover: upload a file, or give an image URL that the panel fetches.
  - **Check link**: the server asks the URL for `Range: bytes=0-0` and shows the status, final host and size
    before saving. The full check (the disc image inside) is the workflow's.
- **Remove**: with a confirmation step built into the page (the panel's pattern; no `confirm()`).

**The API**, all under `/admin/api/store/homebrew`:

| request | does |
|---|---|
| `GET` | the entries plus `.verified.json` |
| `POST` | add |
| `PUT /<id>` | change |
| `DELETE /<id>` | remove |
| `POST /check` | the link probe |
| `POST /publish` | run `store-homebrew.yml` now |

Every write goes to the audit log. Scripts use it with a bearer token, as the other endpoints do.

**How a write lands**: one commit to autobleem-repo's develop through the GitHub App's Contents / Git Data
API.
- The commit carries the TSV and the cover source together (one tree, one commit), with the message
  `store-homebrew: add <title> (<login> via admin panel)`.
- It is guarded by the file's blob sha: someone else's edit in between gives a `409`, and the page reloads
  and says so.
- The push triggers the workflow, so the panel never writes to the site's tree. It stays mounted read-only,
  as the panel's design has it.

**Tests**: `admin/tests/test_admin.py` over the fake GitHub - add, edit, remove, conflict, the team check,
the audit entry, and refusing an itch.io URL.

## 4. Steps (when it is started)

1. **autobleem-repo**:
   - `store-homebrew/homebrew.tsv` seeded with section 6's 34 games, and their covers;
   - `tools/store_homebrew.py` (validate, fetch-and-verify with the cache, covers) with its tests;
   - the `homebrew` publish kind;
   - `store-homebrew.yml`.

   Publish once and look at the TSV.
2. **autobleem-core**: `members`, the cover and the Game.ini in `ContentInstaller`, with tests. Bump the
   submodule in the launcher and ext_store.
3. **ext_store**: the built-in homebrew source (option (a)), and the details pane showing `page` and `year`.
   Try it on the Windows dev build against a local copy of the TSV (`AB_STORE_HOMEBREW`), then the Pi 400.
4. **autobleem-repo admin**: the API and the tab. The owner makes the `store-editors` team.
5. **The site's Store page**: the Homebrew tab.
6. `decisions.md` (the homebrew source), `tester-checklist.md` (install a homebrew game on each target, and
   check the carousel shows the cover and the title), and the manuals' Store section.

## 5. Open questions for the owner

- **Characters and games that belong to someone else.** The seed list includes some:
  - PSXFunkin (Friday Night Funkin' is open source, with its art under its authors' terms);
  - Nu, Pogodi! (the Soviet cartoon's characters);
  - Another World's demo data;
  - the Net Yaroze compilations (other people's games, gathered by a third party);
  - **Dragon's Lair Trilogy**, the one most likely to be a problem: the FMV of commercial laserdisc games,
    still sold today.

  We only link to them, but they would be listed on our site. Keep, drop, or drop Dragon's Lair only?
- **Option (a) or (b)** in 3.3.
- **The `store-editors` team**, or `release-managers` only?
- **itch.io authors**: write to them and ask for a GitHub/archive.org release or mirroring permission? The
  top candidates are Sonic XA, Yume Nikki PS1, the FNAF trilogy, Celeste Classic and Loonies 8192.

## 6. The seed list

What the workflow starts from. "Cover source" is where the first cover comes from, to be normalised and kept
in git. Years and authors are from the games' pages and the archive.org records.

| # | Title | Author | Year | Genre | Download (original host) | Size | Cover source |
|---|---|---|---|---|---|---|---|
| 1 | [240p Test Suite](https://archive.org/details/240p-test-suite-ps-1) | Filip Aláč | 2020 | Tool | <https://archive.org/download/240p-test-suite-ps-1/240pTestSuitePS1.zip> | 455 KB | <https://archive.org/download/240p-test-suite-ps-1/Unbenannt.PNG> |
| 2 | [Abyssal Infants](https://kakoeimon.itch.io/abyssal-infants) | kakoeimon | 2021 | Shoot 'em up | <https://archive.org/download/abyssal_infants_psx/abyssal_infants_psx.zip> | 29.4 MB | <https://img.itch.zone/aW1nLzYzNTMxMDMucG5n/original/LsvUIH.png> |
| 3 | [Airport](https://github.com/XaviDCR92/Airport) | XaviDCR92 | 2021 | Strategy / ATC | <https://archive.org/download/airport-v-0.1/Airport%20v0.1.zip> | 463 KB | <https://archive.org/download/airport-v-0.1/Unbenannt.PNG> |
| 4 | [Another World (rawpsx)](https://github.com/fgsfdsfgs/rawpsx) | fgsfdsfgs | 2021 | Cinematic platformer | <https://github.com/fgsfdsfgs/rawpsx/releases/download/r3/rawpsx_demo.iso> | 3.0 MB | <https://archive.org/download/rawpsx_demo/00cover_itemimage.jpg> |
| 5 | [Bow and Arrow PSX](https://abelliqueux.itch.io/bow-and-arrow-psx) | Schnappy (ABelliqueux) | 2021 | Action | <https://archive.org/download/bow_and_arrow_iso/bow_and_arrow_iso.zip> | 1.3 MB | <https://img.itch.zone/aW1nLzcyNDkxMjEucG5n/original/JZqnPU.png> |
| 6 | [Buzzy Bee](https://ndr008.itch.io/buzzy-bee) | NDR008 & co. | 2021 | Arcade | <https://archive.org/download/buzzy-bee-v-1.1-image/BuzzyBee_v1.1_image.zip> | 32.9 MB | <https://img.itch.zone/aW1nLzcwNjI4NjEucG5n/original/iDNShe.png> |
| 7 | [Cave Story (DoukutsuPSX)](https://github.com/fgsfdsfgs/doukutsupsx) | fgsfdsfgs | 2021 | Metroidvania | <https://github.com/fgsfdsfgs/doukutsupsx/releases/download/v0.7/doukutsu_r7_eu.iso> | 31.1 MB | <https://archive.org/download/doukutsu_test5_2/cave.PNG> |
| 8 | [Dragon's Lair Trilogy](https://archive.org/details/PSX_Homebrew_Dragons_Lair_Trilogy) | (unknown) | 2024 | FMV | <https://archive.org/download/PSX_Homebrew_Dragons_Lair_Trilogy/PSX%20Dragons%20Lair%20Trilogy.zip> | 1217.3 MB | <https://archive.org/download/PSX_Homebrew_Dragons_Lair_Trilogy/00cover_itemimage.JPG> |
| 9 | [Escape from the North](https://reachcoding.eu/escape-from-the-north) | Christoph Hofwartner (reachC) | 2018 | Puzzle | <https://archive.org/download/eftn10/eftn10.zip> | 12.6 MB | <https://archive.org/download/eftn10/Unbenant.PNG> |
| 10 | [Fromage](https://chenthread.asie.pl/fromage/) | asie, GreaseMonkey & co. (ChenThread) | 2021 | Sandbox | <https://archive.org/download/fromage-0.93e/fromage-0.93e.zip> | 15.3 MB | <https://archive.org/download/fromage-0.93e/BOOTEXE_2022-03-29_09-14-13.png> |
| 11 | [He-Run-PSX](https://archive.org/details/He-Run-PSX) | emymin | 2021 | Arcade | <https://archive.org/download/He-Run-PSX/HERUN.zip> | 103 KB | <https://archive.org/download/He-Run-PSX/Unbenannt.PNG> |
| 12 | [Hover Racing](https://archive.org/details/hover_202203) | Tomokazu Sato | 1997 | Racing | <https://archive.org/download/hover_202203/HOVER.zip> | 1.9 MB | <https://archive.org/download/hover_202203/Unbenannt.PNG> |
| 13 | [Insta Death](https://archive.org/details/ps-1-game-insta-death) | Noel Rojas Oliveras | 2023 | Platformer | <https://archive.org/download/ps-1-game-insta-death/PS1_Game_INSTA-DEATH.zip> | 26.2 MB | <https://archive.org/download/ps-1-game-insta-death/instantdeath.jpg> |
| 14 | [Last Survivor](https://archive.org/details/last-survivor.-21.03.16) | Alex Trevisan | 2016 | Action | <https://archive.org/download/last-survivor.-21.03.16/LastSurvivor.21.03.16.zip> | 98 KB | <https://archive.org/download/last-survivor.-21.03.16/00cover_itemimage.jpg> |
| 15 | [Magic Castle](https://archive.org/details/magic-castle-2021-07-may) | Kaiga | 1998 / 2021 | Action roguelite | <https://archive.org/download/magic-castle-2021-07-may/Magic_Castle_2021_07_May.zip> | 262.4 MB | <https://archive.org/download/magic-castle-2021-07-may/00cover_itemimage.jpg> |
| 16 | [Marilyn: In the Magic World](https://archive.org/details/marilyn_v012a) | Meido-Tek (Lameguy64) | 2014 | Action platformer | <https://archive.org/download/marilyn_v012a/marilyn_v012a.zip> | 23.9 MB | <https://archive.org/download/marilyn_v012a/Unbenannt.PNG> |
| 17 | [Net Yaroze 2014 / 2019](https://archive.org/details/ny2014) | qobol | 2014 / 2019 | Compilation | <https://archive.org/download/ny2014/ny2014.zip> | 406.4 MB | <https://archive.org/download/ny2014/Unbenannt.PNG> |
| 18 | [Net Yaroze Collection (83 games)](https://archive.org/details/psx-net-yaroze-collection-83-games) | various, compiled by M. Di Somma | 2007 | Compilation | <https://archive.org/download/psx-net-yaroze-collection-83-games/PSX%20-%20Net%20Yaroze%20Collection%20%2883%20Games%29.zip> | 39.3 MB | <https://archive.org/download/psx-net-yaroze-collection-83-games/HASH-C24CF5EAEB5CAD4B_2021-12-05_18-49-36.png> |
| 19 | [Nolibgs PSX demo disc](https://abelliqueux.itch.io/nolibgs-demo-disc) | Schnappy | 2021 | Tech demos | <https://archive.org/download/nolibgs_demo/nolibgs_demo.zip> | 1.4 MB | <https://img.itch.zone/aW1nLzc0NDYwMzYuZ2lm/original/1mEkcf.gif> |
| 20 | [Nortis](https://github.com/jbreckmckye/nortis) | Jimmy Breck-McKye | 2024 | Puzzle | <https://github.com/jbreckmckye/nortis/releases/download/build/release.zip> | 31 KB | (none - needs one) |
| 21 | [Nu, Pogodi!](https://archive.org/details/nu-pogodi-11) | brill | 2021 | Arcade | <https://archive.org/download/nu-pogodi-11/NuPogodi_11.zip> | 4.3 MB | <https://archive.org/download/nu-pogodi-11/NUPOGODIEXE_2022-03-24_17-38-42.png> |
| 22 | [Pinballoid](https://github.com/XaviDCR92/Pinballoid) | XaviDCR92 | 2015 | Puzzle | <https://archive.org/download/pinballoid-b19-oct-2015/pinballoid-b19-oct-2015.zip> | 424 KB | <https://archive.org/download/pinballoid-b19-oct-2015/PINBALLOEXE_2022-04-04_19-41-18.png> |
| 23 | [PSone Miner](https://archive.org/details/psone-miner) | ttwthomas | 2022 | Arcade | <https://archive.org/download/psone-miner/psone-miner-main.zip> | 34 KB | <https://archive.org/download/psone-miner/Unbenannt.PNG> |
| 24 | [PSXFunkin](https://github.com/cuckydev/PSXFunkin/releases) | CuckyDev | 2021 | Rhythm | <https://github.com/cuckydev/PSXFunkin/releases/download/t0.12/PSXFunkin.t0.12.7z> | 252.6 MB | <https://archive.org/download/psxfunkin.t-0.12/Unbenannt.PNG> |
| 25 | [Psychon](https://archive.org/details/psychon_collection) | Ben James | ? | Shooter | <https://archive.org/download/psychon_collection/PSYCHON.zip> | 3.1 MB | <https://archive.org/download/psychon_collection/00cover_itemimage.JPG> |
| 26 | [QuakePSX](https://github.com/fgsfdsfgs/quakepsx/releases) | fgsfdsfgs | 2021 | FPS | <https://github.com/fgsfdsfgs/quakepsx/releases/download/latest-shareware/quakepsx-sw-9e1bbc4.zip> | 11.4 MB | (none - needs one) |
| 27 | [Robot Ron](https://archive.org/details/robot-ron) | Matt Verran | 2001 | Arcade | <https://archive.org/download/robot-ron/psone_iso.zip> | 1.0 MB | <https://archive.org/download/robot-ron/Unbenannt.PNG> |
| 28 | [Roll Boss Rush](https://archive.org/details/rbr_111) | Isufje | 2015 | Action / boss rush | <https://archive.org/download/rbr_111/rbr_111.zip> | 82.1 MB | <https://archive.org/download/rbr_111/Unbenannt.PNG> |
| 29 | [Siikasaurus](https://zhamul.itch.io/siikasaurus) | Zhamul | 2016 | Action | <https://archive.org/download/Siikasaurus/Siikasaurus.zip> | 566 KB | <https://img.itch.zone/aW1hZ2UvNzg5MjYvMzY5MzMzLnBuZw==/original/B4j2jE.png> |
| 30 | [SQRXZ 4](https://archive.org/details/sqrxz4-v.latest-psx) | RetroGuru | 2021 | Platformer | <https://archive.org/download/sqrxz4-v.latest-psx/sqrxz4-v.latest-psx.zip> | 6.9 MB | <https://archive.org/download/sqrxz4-v.latest-psx/sqr.PNG> |
| 31 | [Tetrade](https://github.com/Logan-Campbell/Tetrade) | Logan Campbell | 2024 | Puzzle | <https://github.com/Logan-Campbell/Tetrade/releases/download/v1.0/TETRADE_PSX.bin><br><https://github.com/Logan-Campbell/Tetrade/releases/download/v1.0/TETRADE_PSX.cue> | 3.0 MB | (none - needs one) |
| 32 | [The 11th Power](http://sebastianmihai.com/11th-power.html) | Sebastian Mihai | 2014 | Puzzle (2048) | <https://archive.org/download/the11thpower/the11thpower.zip> | 32 KB | <https://archive.org/download/the11thpower/Unbenannt.PNG> |
| 33 | [Where's Derpy](https://archive.org/details/wheres-derpy-ps1-port-by-gameblabla-v11) | gameblabla | 2013 | Puzzle | <https://archive.org/download/wheres-derpy-ps1-port-by-gameblabla-v11/wheres-derpy-ps1-port-by-gameblabla-v11.zip> | 3.0 MB | <https://archive.org/download/wheres-derpy-ps1-port-by-gameblabla-v11/Unbenannt.PNG> |
| 34 | [Yarmico / Yarmico 2](https://archive.org/details/yarmico) | gwald | 2022-2023 | Platformer | <https://archive.org/download/yarmico/yarmico-SCEI-PlayStation.zip> | 11.2 MB | <https://archive.org/download/yarmico/yamico-screens.png> |
