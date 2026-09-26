# Decisions - the project's standing rules

The owner's calls that hold across the repositories, with the reason for each. A rule here beats a habit
anywhere else; when one changes, change it here in the same commit as the work that changes it (and date
it). Repository-specific rules live in that repository's CLAUDE.md.

## Branches, releases, CI

- **develop is every repository's default branch; master (retroarch-psc: main) moves only with a release**
  (2026-09-23). Scheduled workflows and checkouts without a ref take develop, so a development build needs
  nothing from master. Nothing is pushed to master for a nightly's sake. *Why:* master must always be what
  was released.
- **One unified version for a release**: every component is tagged `v2.0.0-alpha2`-style together (numbers
  not dot-separated: `-alpha3`, `-rc1`), and autobleem-appliance assembles a release from the components'
  releases of that tag. A nightly is named after the launcher's `git describe`
  (`v2.0.0-alpha2-17-g1760cc8`) - the name the launcher's update check compares with, so it must never be
  renamed by hand. `docs/versioning.md`.
- **alpha2 is withdrawn** (the owner, 2026-09-26): `v2.0.0-alpha2` and the stray `v2.0.0-alpha3` tags and
  releases are deleted; what the teams do now is still the road to the next pre-release, which is called
  **alpha2** again. alpha1 stays (todo R1).
- **`AB_SDK_ABI` moves only with a release** (the owner, 2026-09-26): within a development cycle the ABI may
  change once, and the release carries that one number. ABI 4 (`Extension::runEntry()`) is the next
  release's.
- **Every program shows the package's version** (2026-09-23), exactly as the package's `VERSION` writes it -
  never a component's own describe. `Env::productVersion()` / `$AB_VERSION`; RetroArch is the one exception.
- **The build image has two channels** (2026-09-23): develop builds compile in `autobleem-build:develop`,
  `v*` releases in `:latest` (master's). A nightly is develop all the way down, the compilers and SDL
  included; a toolchain change reaches releases only when autobleem-build's master moves.
- **No Windows exe is UPX-packed** (2026-09-23), and Authenticode signing through SignPath is wired into CI
  but **switched off** per repository (`AB_SIGNING_ENABLED` unset, 2026-09-24) until the owner sets it up. *Why:* Defender quarantined the packed, unsigned installer as
  Trojan:Win32/Wacatac.C!ml; the unpacked one scanned clean. `docs/code-signing.md`.
- **Three channels**: release (the newest stable tag), testing (the one pre-release), nightly (the newest
  development build). The launcher, the installers, the flasher and Raspberry Pi Imager all offer them.
- **Compile once, assemble many**: each component builds and releases its own artifacts; the appliance
  only assembles them, never compiles.
- **CI runs on GitHub Actions** in the `autobleem2` org, gated by the repository variable
  `AB_CI_ENABLED`; the self-hosted runner does what needs the build server's disk (publishing, images).
  Never set that variable, change a repository's visibility, or register runners unasked.
- **Never use the `gh` CLI on the build server.**

## Code

- **One copy of shared code**: `lib_ableem`, `ab_core`, `ab_classic` and `ab_installer` live in
  autobleem-core, a submodule of the launcher and the tool repositories. A change to it is a core commit
  first, then a submodule bump in each consumer.
- **A service extracted from a screen ships with its tests in the same commit.**
- **Every on-screen string is translated into all 16 languages in the same commit** that adds or changes
  it (`tools/lang_tools.py` in the launcher; never run `update` on the console tools' language files).
- **UI fixes** (the launcher's `feature/ui-fixes` way of working): one fix per commit, judged by eye on
  the Windows build; the owner decides the merge.
- **The download page's look is approved** (2026-09-23) and fixed: its rules are in autobleem-repo's
  CLAUDE.md. Fit new content into the existing pieces.
- **Never `python - <<EOF` from a shell tool**; write the script to a file and run it (backslashes get
  eaten, and an empty one hangs on a REPL).

## Platforms

- **Full screen on every real target** (launcher, pcsx-ab, RetroArch); only the dev build has a window.
- **The PlayStation Classic's own storage is never written** - not the root file system, not `/data`,
  nothing on the eMMC (ABFlashKit flashing the kernel on the user's request is the one exception).
  Everything lives on the stick and in `/tmp`.
- **The kernel stays at 4.4** (the owner, 2026-09-25): the GPU driver (PowerVR GE8300, DDK 1.9 blob) pins it;
  newer drivers are backported to 4.4 instead (psc-kernel `feature/pad-drivers`). `docs/console.md`.
- **The kernel payload's overlay only adds to the console, it never shadows a file of the stock root**
  (2026-09-24, after a busybox `/bin/sh` over Sony's stopped AutoBleem from starting); `overlay.py
  shape/check` enforces it.
- **Every way out of a game leaves it as it is at that moment** (2026-09-24): the emulator's menu, the menu
  button held 2 s, the console's Reset and Power buttons all save the live state; **every App can be left
  with Reset** and, on Linux, a Start+Select hold (2026-09-25). `docs/emulator-contract.md`.
- **The stick is written only when the user's state changes** (the quiet stick, 2026-09-24): logs, the
  selection hand-over and RetroArch's appended config live in RAM (`/tmp/autobleem` on the console).
- **The console's SDL2 is 2.0.14 at most**, Wayland video and ALSA audio only (Sony's Weston offers only
  `wl_shell`, which 2.0.16 removed; the console's libwayland is 1.12).
- **No BIOS file in any repository or on the download site** - only lists of hashes and upstream URLs.
- **RetroArch is optional everywhere**; without it nothing RetroArch-related runs.
- **The PC USB stick never says "Pi"** - every user-facing text on it reads as a PC product.
- **The Windows product is per user, no administrator rights** - the PC stick flasher is the one program
  that asks for them (writing a raw disk; agreed 2026-09-23).
- **The console installer has no offline fallback**: it always downloads the stick package from the
  chosen channel (2026-09-23).
- **The console updates itself only with a network** (the AutoBleem kernel's WiFi); a stock console never
  checks.
- **The console's update never relies on a tool in the kernel payload** (2026-09-23): it downloads with
  `abfetch`, the launcher's own HTTPS client shipped on the stick, so every AutoBleem kernel - the 1.x one
  included - updates the same way.
- **Apps and extensions are multi-platform folders** (2026-09-24, the launcher's
  `docs/app-format-plan.md`):
  - One `Apps/<name>/` (or `Extensions/<name>/`) holds a binary for every platform we build for, now or
    later, side by side in `bin/<key>/`, with its data shared.
  - The ini says which binary is for which platform key (`Exec.<key>=`, or `Exec=bin/{key}/...`; an
    extension's `Plugin=` resolves the same way).
  - The launcher resolves it by one rule (`AppManifest`, over the target's ordered key list), and `run.sh`
    and Windows start what it resolved.
  - A new target adds keys and never changes an existing App.
  - An App's ini says whether it runs with our virtual pad mapper (`VirtualPad=true|false`, absent =
    true); `app_env.sh` starts abpadd and the preload only for one that does.
- **Repository names** (2026-09-24): an extension's repository is `ext_<name>` (`autobleem2/ext_store`),
  an App's `app_<name>` (`app_opentyrian`), a scanner processor's `proc_<name>` (`autobleem2/proc_unzip`,
  2026-09-24). The folder it installs to keeps the bare name.
- **Third-party App ports** (the owner, 2026-09-25):
  - The four Tier-2 repositories under `screemerpl` (`amiberry-psc`, `openbor-psc`,
    `autobleem-gameports-pack`, `autobleem-themes-pack`) are **archived** there, not moved: reference only.
  - Each third-party App is ported from its upstream source into its own `app_<name>` repository in
    `autobleem2`, built like `app_terminal` for every target. The shape is **our patches over a pinned
    upstream submodule**, not a fork.
  - **A package carries its own libraries** in `lib/<key>/` (`Lib=lib/{key}`, which `app_env.sh` and the
    App's `run.sh` put first on the library path). Not bundled: the **SDL2 family** (SDL2, SDL2_image,
    _mixer, _ttf - shared, and known to be stable: the launcher's 2.0.14 in `/tmp/lib` on the console, the
    launcher's own DLLs on Windows - its folder is on an App's `PATH` - and the system's on the Pis and
    the PC stick), glibc, libstdc++/libgcc_s and the graphics driver stack. The RetroBoot libs pack is
    not used by the ports. Optional network libraries (SDL2_net) are built and bundled, not left out.
  - **Every target, Windows included**: psc, rpi, rpi64, pcusb and win packages for each port. On Windows
    an App of the old kind (`Startup=` only) is not offered - there is no `sh` to run it. **The one
    exception is Amiberry** (2026-09-25): its SDL2 line, Amiberry-Lite, is Linux-only, and the current
    Amiberry needs SDL3, which the console cannot run - Windows has WinUAE.
  - **Game data ships** with its App: shareware and freeware (DOOM1.WAD, Tyrian 2.1 - its 1995 licence
    file notwithstanding), and the data a port's upstream itself ships (SDLPoP's 1989 Prince of Persia).
    A file the build fetches is mirrored on our site (`mirror/<name>/`, autobleem-repo's
    `repo_publish.sh mirror`) and pinned by sha256. Doom is three Store items from one repository: Doom
    (shareware), Freedoom: Phase 1 and Freedoom: Phase 2 - crispy-doom only, no Heretic/Hexen/Strife.
  - **A way out of every App** (2026-09-25): the console's **Reset** button ends any App (`abpadd`
    watches it, for `VirtualPad=false` Apps too), and the **controller** does on the Linux targets (hold
    Start+Select). On **Windows** an App is left through its own menu, which its readme names.
  - A build not patched for the pad runs with `VirtualPad=true`; the port's own settings (a pad layout,
    full screen) ship as a patch to its default config file, or as the defaults its command line points
    at - never as a separate tool to run.
  - Amiberry and OpenBOR keep **our branding** (splash screens, logos), as the 2019 ports had it.
  - One repository at a time, the owner answering each port's detail questions first; then, with the
    owner's OK per port, the repository goes public in `autobleem2` with `AB_CI_ENABLED`, a
    `v<upstream>-<n>` tag makes the release, and the packages go to all five Store catalogs (replacing
    the RetroBoot App on psc).
  - The ports, their releases and what is particular to each: `docs/app-ports.md` (the "Done" list that
    stood here moved there on 2026-09-26). Amiberry and OpenBOR carry our branding; OpenBOR ships no
    games until the owner names free ones; Doom is three Store items (Doom shareware, Freedoom 1 and 2).
- **Extensions** (2026-09-24, the launcher's `docs/extensions-plan.md`) are our "mods":
  - An extension is a **plugin**: a `.so`/`.dll` loaded into the launcher, built on the AutoBleem SDK
    (autobleem-core: `ab_core`, `ab_classic`, `lib_ableem`). It uses the launcher's own copy of the SDK
    and draws with the user's theme and our UI components.
  - It may run in the background (`poll`/`suspend`/`resume`).
  - Load-time safety comes from a checked ABI stamp (`AB_SDK_ABI` + compiler + target) and a crash guard
    that disables an extension which brought the launcher down.
  - It lives in `Extensions/<name>/` with an `extension.ini`, and runs from **one central place**: the
    System menu's Extensions list.
  - It is **installed by hand** onto the stick and is **a separate download**: none is bundled with a
    release, **PSC-Bios and the Store excepted** (below). Nothing downloads or installs an extension - the
    Store never offers one.
  - It is built for every target.
  - Its `extension.ini` says whether it needs the network (`Network=required|optional|none`). The
    launcher **refuses to run one that requires it while the network is unreachable**: offline mode on the
    console, meaning no default route. The Store is `required`.
  - It **logs through the launcher's facility**: the same `PLOG_*` macros, into `System/Logs/autobleem.log`,
    each line tagged with the extension's name. There is no log file of its own.
  - Extensions in autobleem2 follow the 16-language rule; other people's fall back to English.
  - **PSC-Bios is an extension bundled with the console package; ABFlashKit stays an App** (the owner, later
    on 2026-09-24; until then both stayed Apps).
    - PSC-Bios is `Extensions/pscbios/`, a console-only plugin from autobleem-console-tools, run by the
      System menu's Hardware Information. The built-in screen shows wherever it cannot run.
    - Its `AB_SDK_ABI` must be the launcher's, which the console tools' CI enforces.
    - An update replaces it and removes the old `Apps/pscbios/`.
    - ABFlashKit flashes the kernel, so it runs with the launcher out of the way, as an App.
- **The Store** (2026-09-24, the launcher's `docs/store-plan.md`):
  - It is the **first extension, "AutoBleem Store"** (its own repository, `ext_store`), on **every target** (psc, rpi,
    rpi64, pcusb, win).
  - It only *pulls*: nothing listens on a port, and nothing is installed or uploaded to it from another
    device over the network.
  - Our Apps are store items, one zip per App per platform.
  - **User TSV sources are not limited**: any number, local or remote, any host, every item kind. They are
    how legal games from private sources get distributed. We ship no source but our own catalog.
  - A static notice sits on the Sources tab ("You are responsible for what your sources contain"). It is
    not a gate, and there is no dead-link checking.
  - **It ships with every platform's installer** (the owner, 2026-09-25 - it was a separate download,
    installed by hand): the appliance's assemble scripts put ext_store's package into every package (the
    stick's `Extensions/store/`, a Linux package's `extensions/` for `install.sh`, the Windows program
    folder's `Extensions/` for AutoBleemWinSetup), and every install and update replaces the shipped folder
    whole. The Store's own state (`System/Extensions/store/`, `disabled.txt`) and any extension the user
    unpacked by hand are never touched. A development build takes ext_store's nightly, a release its latest
    release (its nightly while there is none); the plugin's SDK stamp must match the launcher's.
- **Scanner processors** (2026-09-24, the launcher's `docs/scanner-processors-plan.md`): community console
  programs in `System/Processors/<name>/` that the scan runs over the games before it reads them.
  - The folder processors ("preprocessors") are the **first thing every scan does**, whoever asked for it
    (the user, the watcher, the start-up check); then each game folder and ROM file through its chain.
  - They run in **two sequences the user sorts** (PS1, ROMs - the System menu's Scanner processors, stored
    in `sequence.ini`); a new processor goes to the end.
  - A processor **may delete the original, but only after its output is complete**: written as `.part`,
    renamed, then the original deleted.
  - **Mods and patches run at scan time**, in place; the state file makes sure a game is not patched twice.
  - They **always run on the automatic scan**, heavy ones too - revisited if testing shows problems.
  - The built-in ECM decoding stays as it is (no `proc_unecm` for now).
  - `proc_unzip` is the first processor and the example; `tools/proc_check.py` checks one before publishing.
  - **Unzip ships with every package** (2026-09-25): a processor is bundled, unlike an extension. The
    appliance takes its nightly for a development build and its latest release for a release; an update
    replaces its program and keeps the user's order and on/off.
  - The installers make `System/Processors/` (and `Extensions/`), each with a README, written once.
- **No Project Eris code, ever** (2026-09-24): nothing from Project Eris or its mods (PSC Store included)
  is used in any repository. That covers sources, binaries, scripts, databases, samples, artwork and text.
  A feature inspired by theirs is a clean implementation from an analysis of what it does, written on our
  own code. *Why:* their code carries its own licence and authorship, and ours must stay GPLv3 and
  provably our own.
- **Themes and samples have their own source repositories** (the owner, 2026-09-26 - until then all five
  themes stayed in the launcher): `autobleem-themes` becomes the themes' source and `autobleem-samples` the
  sample pack's; the launcher's copies go once the build takes them from there (todo D5, D6).
  `ab2/ab.ogg` is the owner's own composition.
- **Images**: xz level 2 (`AB_XZ_LEVEL=2`) - speed over size; cache the base images between builds.

## Testing

- **UI is tested through the DebugDriver** (`tools/ab_drive.py` in the launcher), with the window hidden
  unless the owner wants to watch.
- **VMs are the owner's VirtualBox**, driven with VBoxManage - not QEMU.
- **Hardware proofs are delegated to testers**: `docs/tester-checklist.md`.
- **Never point a test write at a real disk of a development PC** (the flasher is proven by the unit
  suite and by testers).

## Working with Claude sessions

- **One Program Manager over the teams** (the owner - the CEO - 2026-09-26): **Eleanor Voss - Program
  Manager (roadmap)** writes no code. She keeps `docs/roadmap.md` and `docs/todo.md`, reports how far the
  next milestone or release is, plans user stories with the owner, and owns:
  - **the questions for the owner**: a team manager sends her any question that needs his decision; she
    queues them (`_team/ceo-questions.md` next to the checkouts), puts them to him together and relays the
    answers. A decision he gives directly in a team's session is cc'd to her in one line;
  - **todo intake**: teams send her new items instead of adding rows; she writes the row and decides which
    team does it (`Team:` in the row). The commit that finishes the work still deletes its row;
  - **the team sessions**: she decides whether a team has work, and may create a team (a new team manager's
    session, named per the naming rule) and close or clear one when it has no work or needs a fresh start
    (its state saved first - a REPORT.md, nothing uncommitted lost).
- **The 5-hour stop line is 90%** for every team (the owner, 2026-09-26): above it a team stops its agents,
  saves its state and waits for the window's reset.

- Several sessions work at once, sometimes in the same checkout: before pushing a shared branch look for
  commits that are not yours (`git log origin/<b>..<b>`), merge rather than rebase, never delete a branch
  another session committed to.
- Post a one-line progress note at each step of long multi-repository work, mapped to the plan; don't
  idle-wait on CI - pick up the next item meanwhile.
- **Clean up after yourself on the build server** (the owner, 2026-09-25, after `psc-build` reached 88%):
  when a build there is finished - its result fetched, or CI now builds it - delete what the build left
  behind: the `build_*/` and `dist/` folders, fetched data caches, logs you wrote to `~`, containers and
  images you pulled only for it (`alpine` for a root-owned delete, say). A synced tree that CI builds from
  now on goes entirely. Only your own: another session's files are theirs to delete - ask it (`ListAgents`,
  `SendMessage`) or the owner, never remove them yourself; the site (`~/autobleem-repo`), the runner and the
  shared build images are never "leftovers".
