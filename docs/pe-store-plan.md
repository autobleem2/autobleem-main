# PE Apps in the Store (APPS-8) - plan

Status: **in progress** (the owner, 2026-10-05: "robimy APPS-8 w trybie nocnym"). Milestone alpha1.2.
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

## Status (2026-10-05)

Steps 1 to 5 are done and merged. The core has `ModInstaller` and the item's `source_url` (`AB_SDK_ABI` 9). The
Store has the PE Apps tab, with the licence and the source link in the details. The launcher has `abdialog` for the
mods' questions and text screens (the text screen's title is the App's name), and "Apps end whole": the runner stays
the App's parent and stops everything the App started, on Reset, Start+Select and the App's own end. The `pe`
processor (1.1.0) moves a converted `.mod` to `Mods/done/` (the owner, 2026-10-05: "Przenieś do Mods/done/");
`Mods/done/` is never scanned, a package dropped again replaces the old one, and one that fails stays in `Mods/`.
The Store counts a PE item as installed while its `.mod` is in `Mods/` or `Mods/done/` or its marker
`Apps/.pe_state/<file>.ini` is there; removing it deletes both and the Apps made from it, and an update retires the
old version's package in either place. The site has the PE Apps catalog kind, `source/<id>/` (kept at least 3 years)
and `deps/` (Boost 1.74 for Commander Genius). Step 6, the PSC test: two rounds with the owner - OpenLara and
tyrquake fully work; Commander Genius and OpenJazz start and end cleanly but their pad mapping is wrong (Triangle as
the primary button, the menu on R2). Round 4 (2026-10-05) passed 10/10 after a planned fix: one pad model for every
PE App (the kernel pad `psc-kernel`), both ports bound in the console pad's numbers, a deadzone on the x360 outputs,
the touchpad and motion nodes kept off the desktop seat. `pe_ports` v1.0.0 is in the online Store.

## Decisions (the owner, 2026-10-05)

1. The plan is approved; it runs from the night of 2026-10-05.
2. Wave 1: openlara, Commander-Genius (Keen 1), openjazz (JJ1), tyrquake. blastem moves to wave 2.
3. The Quake shareware `pak0.pak` ships in the tyrquake package, with id's licence texts unmodified (the owner takes the risk).
4. PPSSPP only as `app_ppsspp` in the native PSP plan.
5. Repository `autobleem2/pe_ports` (public, default develop, CI on).
6. tyrquake built from source has no pad code (the 2020 binary's pad code has no published source): our own SDL pad
   patch, tested on the PSC.
7. openjazz is pinned to the 2020 SDL2 fork (gitlab.com/modmyclassic/ports/openjazz-sdl2); a port of modern upstream
   later if wanted.
8. The GPL written offer names the GitHub organisation as the contact.
9. Commander Genius's Boost 1.74 headers are mirrored on our site (not fetched from archives.boost.io).
