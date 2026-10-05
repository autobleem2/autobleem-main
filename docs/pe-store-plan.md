# PE Apps in the Store (APPS-8) - plan

Status: **plan only, not started** (the owner, 2026-10-05: "na razie plan do dokumentacji"). Milestone alpha1.2.
Follows APPS-7 (PE Apps step 1, done 2026-10-05): a `.mod` in the stick's `Mods/` becomes an App through `proc_pe`,
and the launcher's `rc/pe_run.sh` runs it with the pad the mod expects.

## Goal

A Store section **"PE Apps"** (PL "Aplikacje PE"; the name of the 2020 environment never appears in the UI) that
installs open-source PE mod programs for the PlayStation Classic. Every item is **built by our CI from public
source**, never a repack of a third-party binary.

## Why rebuild, not host the 2020 packages (licence audit, 2026-10-05)

The 25 projects of https://gitlab.com/groups/modmyclassic/ports were audited:

- the committed binaries cannot be proven to match any source commit, and the original build image is private,
  so the GPL "corresponding source" cannot be shown for them;
- the packages' own wrapper files (`launch.sh`, `launcher.cfg`, icons, pack Makefiles) carry no licence, so we
  generate our own (they are a few lines each);
- the pad-select pictures carry third-party logos (Quake, Doom, Quake 3, Windows): left out, our dialogs replace
  them;
- the remap libraries of the 2020 environment (`sdl_remap_arm.so`, `drastic_sdl_remap.so`) have no licence and
  are never shipped: our abpad does their job.

### Verdict per port

| Port | Licence | Verdict | Notes |
|---|---|---|---|
| openlara | BSD-2 | rebuild | the user brings the TR1 data |
| Commander-Genius | GPL-2 | rebuild (or repack + source mirror) | Keen 1 shareware (with VENDOR.DOC) may ship; Keen 4 partial and save games removed |
| openjazz-sdl2 | GPL-2+ | rebuild | Jazz Jackrabbit shareware with LICENSE.DOC, unmodified |
| tyrquake | GPL-2 | rebuild | Quake shareware `pak0.pak`: open question (id's terms cover the complete shareware package only) |
| blastem | GPL-3+ | rebuild | the user brings ROMs |
| lzdoom | GPL-3 | rebuild | sound libs from source (LGPL notices); the user brings an IWAD or Freedoom; no "brutal" variant |
| dosbox, dosbox-gl | GPL-2 | rebuild | gl4es from our libs pack; win311 not hosted (Windows art, the user's Windows) |
| corsixth | MIT | rebuild | the Theme Hospital demo files removed; the user brings the game |
| ioquake3 | GPL-2 | rebuild | the user brings Quake 3 data |
| openjk | GPL-2 | rebuild (later) | the user brings JK2 data |
| cannonball | own non-commercial licence | rebuild (later, low priority) | the user brings the arcade ROMs |
| ppsspp | GPL-2+ | **not here**: built once as `app_ppsspp` in the native PSP plan | the 2020 mod's homebrew games are not shipped |
| drastic | closed | **user brings it** (the owner: the author cannot be reached) | |
| zdoom | non-commercial source licences | not hosted | superseded by lzdoom |
| xash3d | GPL-3 + proprietary SDK parts, no source in the port | not hosted | |
| rawgl | no licence | not hosted | |
| psc_devilutionx | grey (decompiled code, commercial data) | not hosted | |
| sdlpop, wolf4sdl, eduke32, openbor, autobleem-apps | - | not hosted | we ship our own `app_*` ports |
| retroarch, emulationstation_packer, fbff | - | not hosted | empty or not for the PSC |

## GPL obligations (for every hosted item)

- The exact source is mirrored on our own site next to the item: a `git archive` of the pinned commit plus
  submodules, our patches and our build scripts (with the build image digest). It is kept at least 3 years after the
  item's last release.
- Each package carries `SOURCE.txt` (licence, source URL, commit, sha256, the 3-year offer), the licence text, the
  upstream copyright lines and a note of our changes.
- The source archive is never in the item's `files[]` (it must not land on the stick).
- MIT/BSD/zlib parts are listed in the package's third-party notices.

## Steps

| # | Step | Repo |
|---|---|---|
| 1 | A new repository `pe_ports`: one folder per port with the pinned upstream (submodule), the 2020 port's patches, and a generator for our `launch.sh` / `launcher.cfg` / icon. CI builds each port in the `autobleem-build` PSC image (gcc-6 Stretch sysroot; gcc-12 for C++17 ports), checks it with `check_psc_binary.sh`, packs a `.mod` and a source archive, and publishes them as a release. | pe_ports (new) |
| 2 | Wave 1: openlara, Commander-Genius (Keen 1), openjazz (JJ1), blastem, tyrquake. Wave 2: lzdoom, dosbox, corsixth, ioquake3. | pe_ports |
| 3 | Store: a new item kind with its own tab "PE Apps"; installing drops the `.mod` into `Mods/` and starts a scan, so `proc_pe` makes the App as for a user's own mod; licence and source fields shown; all languages. | ext_store, launcher |
| 4 | Site: a "PE Apps" section of the Store page and the source mirror under `source/<id>/`. | autobleem-repo |
| 5 | Dialogs: the two tools a mod calls (a text screen; a Cross/Circle/Square/Triangle choice) as AutoBleem-styled SDL programs instead of fixed answers. | launcher |
| 6 | Console test: install from the Store, start, pad, Reset. | - |

Rough cost: 8-10% of a week. Risks: the 2020 patches may not apply to newer upstream (pin the 2020 commit
instead); heavy builds (lzdoom's sound libraries) need the static-deps pattern of the `app_*` ports.

## Open decisions (for the owner, when the plan starts)

1. Approve the plan as a whole.
2. Wave 1 list.
3. Quake shareware `pak0.pak` in the tyrquake package, or the user brings it.
4. PPSSPP only as `app_ppsspp` in the native PSP plan (recommended), or also as a PE package.
