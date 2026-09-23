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
- **Every program shows the package's version** (2026-09-23), exactly as the package's `VERSION` writes it -
  never a component's own describe. `Env::productVersion()` / `$AB_VERSION`; RetroArch is the one exception.
- **The build image has two channels** (2026-09-23): develop builds compile in `autobleem-build:develop`,
  `v*` releases in `:latest` (master's). A nightly is develop all the way down, the compilers and SDL
  included; a toolchain change reaches releases only when autobleem-build's master moves.
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
- **Themes**: all five stay in the launcher repository; `ab2/ab.ogg` is the owner's own composition.
- **Images**: xz level 2 (`AB_XZ_LEVEL=2`) - speed over size; cache the base images between builds.

## Testing

- **UI is tested through the DebugDriver** (`tools/ab_drive.py` in the launcher), with the window hidden
  unless the owner wants to watch.
- **VMs are the owner's VirtualBox**, driven with VBoxManage - not QEMU.
- **Hardware proofs are delegated to testers**: `docs/tester-checklist.md`.
- **Never point a test write at a real disk of a development PC** (the flasher is proven by the unit
  suite and by testers).

## Working with Claude sessions

- Several sessions work at once, sometimes in the same checkout: before pushing a shared branch look for
  commits that are not yours (`git log origin/<b>..<b>`), merge rather than rebase, never delete a branch
  another session committed to.
- Post a one-line progress note at each step of long multi-repository work, mapped to the plan; don't
  idle-wait on CI - pick up the next item meanwhile.
