# AutoBleem in Rust - an idea and a first plan (2026-10-11)

Status: **idea** (`docs/ideas.md`), not approved and not costed. It answers three of the owner's questions:
which language and libraries AutoBleem would use if it were written again, where a move to Rust would start,
and which parts of the logic could move. The line counts are from autobleem-core at the end of September 2026.

## What decides the choice: the PlayStation Classic

The Pi and a PC run anything; the console sets the limits (`docs/console.md`):

- 32-bit ARM (armhf), a PowerVR GE8300 whose driver reports OpenGL ES 3.2 / GLSL ES 3.20 (read from the
  driver's strings, confirmed at run time by step 0 below) and pins the kernel at 4.4;
- Sony's Weston 1.11 with `wl_shell` only and libwayland 1.12, no X; our own SDL 2.0.18 (`autobleem_sdl`) is the
  ceiling there;
- 1 GB of RAM shared with the running emulator; glibc 2.24;
- a start in a fraction of a second, pad-only input, 17 languages including Chinese;
- the emulators (pcsx-ab, pcsx-abnxt) are C and stay C.

## The proposed stack

| Layer | Pick | Why |
|---|---|---|
| Language | **Rust** | C++ speed without the class of crashes paid for today (leaks, use-after-free, races in the scanner threads); good cross-compiling (`cargo zigbuild` targets the console's glibc 2.24) |
| Window, input, audio | **SDL2** (the `sdl2` crate over `autobleem_sdl`) | the one library proven on the console's Weston and on every platform shipped; pads, hotplug, audio |
| Drawing | an own small GLES 3.0 renderer on **`glow`** (a GLES2 fallback only if the runtime check disappoints) | tiles, textures, transitions, CRT shaders; small, predictable, profilable on the console |
| UI | an own retained-mode UI driven by the theme's data | a pad launcher is a carousel, lists and panels; general UI frameworks are mouse-first and heavy |
| Text | **cosmic-text** (shaping and font fallback) | Chinese, Czech, Polish, Turkish on one path, no hand patches |
| Images | `image`, decoded on a worker thread | covers load in the background, the carousel never stutters |
| Game database | **SQLite** (`rusqlite`) | as today |
| Themes, config | **serde + JSON** | a theme is pure data, easy to validate and to generate from the design tools |
| Translations | **Fluent** (`fluent-rs`) | plurals and grammatical cases (Polish, Czech); readable files for translators |
| Emulators | stay C, a separate process as today | proven, not rewritten |
| UI tests | a headless renderer and the same DebugDriver protocol | the same scripts drive the old and the new launcher |

Ruled out:

- **Qt / QML** - heavy on the console, the licence, a slow start;
- **Flutter / Electron** - no sensible start on the console's GPU in 1 GB next to an emulator;
- **Godot** - has GLES2, but tens of MB, a slow start, and nothing for a `wl_shell`-only compositor;
- **wgpu** - possible (its GL backend needs GLES 3.0), but heavier, and a layer that hides what reaches the
  console's driver;
- **Lua for logic** - only if themes ever need their own scripts; data is enough today.

The pragmatic alternative: **C++20 with the same set** (SDL2, GLES 3, HarfBuzz + FreeType, SQLite, nlohmann/json),
sanitizers in CI and a split into modules. Less risk in the move, but it does not remove the memory bugs.

## FFI in one paragraph

FFI (a foreign function interface) lets code in one language call functions written in another, inside one
program. Rust exports a function with the C calling convention (`#[no_mangle] pub extern "C" fn ...`), builds a
`.a`/`.so`, and the C++ launcher calls it like any C function; the `cxx` crate generates a safe bridge between
Rust and C++. Rust cannot check memory safety across that border, so the border stays small: a few functions
with simple data.

## How to move: piece by piece, never a big rewrite

The C++ launcher keeps working the whole time; Rust parts go into it one by one until a new one replaces it.

**Step 0 - proof that Rust runs on the console** (small, cheap, the only step that can end the idea): first
`glGetString(GL_VERSION)` from a real GLES 3 context on the console; then a Rust program with SDL2 + GLES 3 on
`glow` on the console's Weston through `autobleem_sdl` - one textured tile, Chinese text, pad
input - cross-built for armhf against glibc 2.24, the same program on the Pi and a PC; the start time, the RAM
and 60 fps measured. If it fails, the idea stops here and AutoBleem stays C++.

**Step 0 passed (2026-10-12)**: a probe in Rust (glow, GLES 3.0, cosmic-text; SDL2 loaded at run time; the armhf
build cross-compiled with `cargo zigbuild` for glibc 2.24), 30 s each:

| Device | GL at run time | SDL | Resolution | fps (avg) | first frame |
|---|---|---|---|---|---|
| PlayStation Classic | OpenGL ES 3.2, PowerVR GE8300 | `autobleem_sdl` 2.0.18, Wayland | 1280x720 | 59.0 | 366 ms |
| Raspberry Pi 400 | OpenGL ES 3.1, V3D 4.2 (Mesa) | system 2.32.4, KMSDRM | 1920x1080 | 59.6 | 497 ms |
| PC | OpenGL ES 3.2 | 2.0.18 | 1280x720 | 61 | ~1.05 s |

The Pi 400 has GLES 3.1, so the renderer keeps to GLES 3.0 features. Text from cosmic-text looked clearly better
than today's. Step 1 needs its own plan and approval.

**Step 1 - logic without UI, inside today's launcher through FFI** (the waves below). Each module ships in the
old launcher at once, with its unit tests.

**Step 2 - a new UI shell in Rust** on top of those modules: the GLES 3 renderer, cosmic-text, the carousel from
the theme format, and the **same DebugDriver protocol**, so today's scripts drive both launchers and their
screens are compared pixel by pixel. Behind a switch, on the PC test machine first.

**Step 3 - the switch**: when every screen matches and the tests pass on the PC test machine, the Pi and the
console, the new launcher becomes the default; the C++ one goes after one release of overlap.

## Which logic moves (autobleem-core `src/code/core/services`, ~10k lines in 37 files)

**Wave 1 - parsing and data, ~2.5k lines (the start)**: pure functions whose input is users' files.

| Module (lines) | What | Why Rust |
|---|---|---|
| `disc_reader` (330) | reads disc images, the serial | binary user data - the classic place for memory bugs |
| `scan_service` (933) | scans the games folder | users' files; parallel without races |
| `game_query`, `game_catalog` (455) | game queries, the catalog | SQLite and types, easy to test |
| `memcard` (109), `resume_point` (263) | memory cards, resume points | binary formats, easy to cover |
| `config`, `platform_config`, `pcsx_config` (403) | config files | serde instead of hand parsing |
| `theme`, `theme_converter` (397) | themes | serde and validation, shared with the design tools |
| `app_manifest`, `extension_catalog`, `processor_catalog` (832) | the manifests of Apps, extensions and processors | outside JSON, pure validation |

**Wave 2 - network, downloads, installs, ~1.4k lines**: `downloader`, `online_assets`, `update_service` (HTTP,
checksums, resume), `content_installer`, `theme_installer` (unpacking archives - Rust makes "zip slip", files
escaping their folder, easy to block).

**Wave 3 - system and processes, ~4.4k lines (last, together with the new UI)**: `launch`, `system`,
`system_info`, `environment`, `retroarch`, `processor_runner`, `processor_sequences`, `processor_state` - bound to
the platforms (console, Pi, PC, Windows), hard to test without the devices, they start the emulators.

**Stays to the end or as it is**: thin OS glue - `pad_battery`, `lightgun`, `output_mode`, `windows_host`.

**The first candidate: `disc_reader`** - small, a clear input (a disc image) and output (serial, region, title),
easy to test on real images, the most exposed to bad data; a good first piece to practise FFI and the
multi-platform build on.

## Open before a real plan

- A review of the module split and the dependencies between the modules.
- `lib_ableem` (in autobleem-core) not looked at yet.
- The UI layers (`src/code/evoui` ~9.3k lines, `src/code/gui` ~2.7k, the core's `gui` ~6.6k, the installer ~2.8k)
  belong to step 2 and are not sized in detail.
- The cost of each step.
