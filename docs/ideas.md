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
| `-sonyhacks` - the configuration layer of Sony's per-title hacks - as a lever for the compatibility pass | S | med | Not a default; see todo EMU-1 |
| A native x86-64 Linux build of the emulators (the Atari VCS plan needs it) | M | low | |

## Console and kernel

| Idea | Size | Value | Notes |
|---|---|---|---|
| Done 2026-09-29: the console's SDL2 is our own `autobleem_sdl` 2.0.18 (`wl_shell` ported back as patch 0001, `SDL_RenderGeometry` and the rest of 2.0.16/2.0.18's renderer work included). Still open: SDL 2.0.20+/2.26+, which needs libwayland >= 1.18 symbols made optional (the console has 1.12) - current HIDAPI pad drivers and the CRC16 GUIDs would be the payoff | L | med | 2.0.18 is the new ceiling until this lands |
| A userland refresh: ship newer libraries than the stock root in the overlay, never the graphics stack | L | low-med | psc-kernel-payload `feature/userland-refresh`; a newer kernel is ruled out (the GPU blob pins 4.4 - the owner, 2026-09-25) |
| `abfetch` checks certificate dates when the AutoBleem kernel gives a real clock | S | low | No battery clock on a stock console, hence off today |
| Power Off: detect the OTG host up front instead of three refused suspends before `shutdown -h` | S | low | See `docs/console.md` |
| Build RetroArch's cores from `cores-full.txt` (170) after the 81 are proven | L | low | retroarch-psc; todo EMU-9 first |

## Apps, extensions, the Store, processors

| Idea | Size | Value | Notes |
|---|---|---|---|
| The virtual gamepad through uinput (non-SDL and static Apps, a virtual keyboard) | M | low-med | Needs uinput on the stock kernel (todo APPS-3) |
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
| A `pcusb64` target key (a 64-bit PC stick) | M | low-med | `archive/app-format-plan.md` |
| The Atari VCS 800 port | L | low-med | The launcher's `docs/atari-vcs-plan.md`; blocked on one hardware probe (todo PLATFORM-7) |
| The appliance fetches the emulators' binaries from their releases instead of keeping them in `payload_linux/Autobleem/bin/emu*` | M | low | Compile once, assemble many |
| ABleemStation universal: an M.2 SSD inside the case as extra games storage - a cradle on the base in the free strip beside the board (about 48 x 70-90 mm, 21 mm high: M.2 2230 / 2242 on a flat adapter; 2280 only just fits). Pi 5: NVMe over PCIe (a flat adapter on a longer FFC, beside the board, so the Active Cooler stays; Gen 2, can boot from it). Pi 4: a USB adapter - USB 2.0 wired under the board like the front USB, or USB 3.0 through a U-plug / a panel with a cable pass-through. Pi 2 / 3: USB 2.0 only, an M.2 SATA drive for the lower current | M | low-med | The owner, 2026-10-04: "some day"; a base variant + its fit check; how the launcher would use a second games location is open |
| ABleemStation universal: the port panels printed upside down (top edge on the bed), on one plate with the shell (roof-down), so one filament change colours everything. The panel's top (the tongue, 25.6 mm) is 2 mm below the shell's roof (27.6), so the change would land ~1 mm under the panel's waist groove: give the tongue a 2 mm cut-off extension with a thin neck (its trace stays in the roof's groove); the inner tabs need a 45-degree top and the ears move to the bed side. Without the extension: two-colour parts on two AFC lanes (~12 layers of extra lane changes) | M | low-med | The owner, 2026-10-04: "some day" |
| LAN Share: CHD output for a read disc; HTTPS or a password (only if ever reachable from outside); drive read offset and audio correction for redump-exact dumps | L | low | autobleem-pc-tools `docs/lan-share-plan.md` |

## Project tooling

| Idea | Size | Value | Notes |
|---|---|---|---|
| The admin panel's second version: release notes drafted from the commits, the tester checklist's pass/fail per build | M | med | autobleem-repo |
| Graft the 1.x history onto the repositories (`git replace --graft`) | S | low | `archive/legacy-1x-analysis.md` |
