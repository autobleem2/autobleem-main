# Ideas (2026-09-26)

What someone has thought worth doing and nobody has committed to - gathered from the launcher's
`docs/IDEAS.md`, the plans' "later" sections, the old todo's "Later" list and every repository's notes.
When an idea is taken up it becomes a row in `docs/todo.md` (and a plan if it needs one); when it is
dropped, delete it here with a word in the commit message why.

Value is a guess: **high** = users would notice at once, **med** = nice, **low** = for completeness.
Size as in todo.md.

## Launcher and UI

| Idea | Size | Value | Notes |
|---|---|---|---|
| A visual system carousel for RetroArch (per-system logos, Recalbox-style) | M + art | med | The Select set picker (2026-09-21) is a tabbed text list; the launcher's `docs/IDEAS.md` has the design |
| Game Manager: "Move to folder..." | S | med | After the Game Manager rework (`archive/legacy-1x-analysis.md`) |
| Real artwork for the big-box frame (`evoimg/bigbox.png`, generated today) | S | low | Any time; `tools/make_bigbox_frame.py` draws the placeholder |
| The themes pack: the 51 community themes of `screemerpl/autobleem-themes-pack` (archived) converted - without Sony's fonts and firmware images, franchise art or commercial music | L | med | A plan of its own (the owner, 2026-09-25); a Store `theme` kind would be its home |
| "Add your WAD" in the launcher or the Store, so Doom plays a full `DOOM.WAD` without editing `app.ini` | S | low | app_crispydoom |

## PS1 emulation

| Idea | Size | Value | Notes |
|---|---|---|---|
| A real CRT/scanline shader in the emulator (GLES/GL, ported RetroArch GLSL) | M-L | med | The research in the launcher's `docs/IDEAS.md` targets pcsx-ab - re-scope it to pcsx-abnxt |
| A scaler thread for HQ2x/HQ3x (30 fps on the console today) | M | low | pcsx-abnxt, "if it ever matters" |
| DuckStation as an alternative PS1 core on strong machines, driven like RetroArch | M-XL | low-med | CC-BY-NC-ND licence gate; resume pictures, memory cards and light guns unknown |
| pcsx-abnxt as an upstream `psclassic` platform (a PR to notaz) | M | low | The shape is in pcsx-abnxt's CLAUDE.md |
| `-sonyhacks` - the configuration layer of Sony's per-title hacks - as a lever for the compatibility pass | S | med | Not a default; see todo E1 |
| A native x86-64 Linux build of the emulators (the Atari VCS plan needs it) | M | low | |

## Console and kernel

| Idea | Size | Value | Notes |
|---|---|---|---|
| A newer SDL2 on the console (2.26+): port `wl_shell` back as a fallback (as retroarch-psc's `wl_shell_fallback.patch` did for RetroArch 1.22) and make libwayland >= 1.18 symbols optional | L | med | Brings `SDL_RenderGeometry`, current HIDAPI pad drivers and the CRC16 GUIDs; 2.0.14 is the ceiling today (the console's Weston 1.11 offers only `wl_shell`, libwayland is 1.12) |
| A userland refresh: ship newer libraries than the stock root in the overlay, never the graphics stack | L | low-med | psc-kernel-payload `feature/userland-refresh`; a newer kernel is ruled out (the GPU blob pins 4.4 - the owner, 2026-09-25) |
| `abfetch` checks certificate dates when the AutoBleem kernel gives a real clock | S | low | No battery clock on a stock console, hence off today |
| Power Off: detect the OTG host up front instead of three refused suspends before `shutdown -h` | S | low | See `docs/console.md` |
| Build RetroArch's cores from `cores-full.txt` (170) after the 81 are proven | L | low | retroarch-psc; todo E9 first |

## Apps, extensions, the Store, processors

| Idea | Size | Value | Notes |
|---|---|---|---|
| The virtual gamepad through uinput (non-SDL and static Apps, a virtual keyboard) | M | low-med | Needs uinput on the stock kernel (todo A3) |
| Store item kinds: `rom:<system>` (into `RetroArch/roms/<system>/`) and `theme` (through `ThemeInstaller`) | M | med | store-plan |
| Store search with the keyboard | S | med | |
| Extension-provided System menu items, more launcher hooks | M | low | Explicitly not planned for now |
| A reporting-only processor (bad dumps, a missing BIOS) | S | med | Possible today with `Modifies=false`; nobody has written one |
| proc_unzip: split 7z (`.7z.001`), password archives, Deflate/BZip2 inside 7z; RAR5 blocks over more than two volumes (a libarchive limit) | M | low | |
| `proc_unecm` in place of the built-in ECM decoding | S-M | low | Decided against for now (the owner) |
| `Data.<key>=` - per-platform data in `app.ini` | S | low | Until an App needs it |
| Terminal: CJK double-width cells, reflow of long lines on resize | M | low | app_terminal |

## Platforms and distribution

| Idea | Size | Value | Notes |
|---|---|---|---|
| A Pi update without a network: a package dropped on the data partition, applied at the next boot | M | med | `archive/rpi-image-and-update-plan.md`, Part 1 |
| A `pcusb64` target key (a 64-bit PC stick) | M | low-med | app-format-plan |
| The Atari VCS 800 port | L | low-med | The launcher's `docs/atari-vcs-plan.md`; blocked on one hardware probe (todo P7) |
| The appliance fetches the emulators' binaries from their releases instead of keeping them in `payload_linux/Autobleem/bin/emu*` | M | low | Compile once, assemble many |
| LAN Share: CHD output for a read disc; HTTPS or a password (only if ever reachable from outside); drive read offset and audio correction for redump-exact dumps | L | low | autobleem-pc-tools `docs/lan-share-plan.md` |

## Project tooling

| Idea | Size | Value | Notes |
|---|---|---|---|
| The admin panel's second version: release notes drafted from the commits, the tester checklist's pass/fail per build | M | med | autobleem-repo |
| Graft the 1.x history onto the repositories (`git replace --graft`) | S | low | `archive/legacy-1x-analysis.md` |
