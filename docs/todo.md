# What is left (2026-09-26)

Every open item of every repository, in one list. It merges this file's earlier list, the launcher's
`TODO.md`, the open steps of every plan, and the "not yet run" lines scattered through the repositories'
CLAUDE.md files. Each row has an ID, which `docs/roadmap.md` plans by milestone. Ideas nobody has
committed to are in `docs/ideas.md`.

**How to keep it:** when an item is done, delete its row in the same commit as the work (the commit
message names the ID). New work that needs more than a row gets its own plan in `docs/`. A repository keeps
no TODO list of its own.

Size: **S** = a sitting, **M** = a day or two, **L** = several days or subsystems. Who: **dev** = a
development session, **owner** = the owner's decision or setup, **tester** = hardware in a tester's hands.
Milestone: **a2 a3 a4 b1 rc** = alpha2, alpha3, alpha4, beta1, rc/2.0.0 (renumbered 2026-09-26: the old alpha2 and the stray alpha3 are withdrawn, so the next pre-release is alpha2 again); **later** = after 2.0.

## R - Release and process

| ID | What | Where | Size | Who | Ms |
|---|---|---|---|---|---|
| R1 | **Replace `v2.0.0-alpha2` (and the stray `v2.0.0-alpha3`) with the new alpha2** (the owner, 2026-09-26: what we do now is still the road to alpha2; alpha1 stays). **Not withdrawn ahead of time** - the old alpha2 stays on the testing channel until the new one exists (the site cannot yet go back to alpha1 and the psc channel could not point at a nightly - `_team/r-items/R1-safety.md`). Steps: ~~the payload's rolling `nightly` release, console-tools' develop builds taking it with no 2020 fallback~~ (done 2026-09-26: payload 101d5bd, console-tools 7dcb29b); give `repo_publish.sh` a `withdraw` mode; `release.py` checks every repository for an existing tag before tagging anything; then in one `promote` run the old alpha2/alpha3 tags and releases go and the new alpha2 is tagged. The update checks compare for equality only, so the nightly's `git describe` dropping to `alpha1-N` is safe on devices (checked). Team: infrastructure. | all component repos, site, release.py | M | dev | a2 |
| R2 | Make moving autobleem-build's master (`:latest`, what `v*` tags compile in) a step of `promote` (it is not in `STAGES`), so master never falls behind develop again. The catch-up merge itself is done (master `df961cf`, 2026-09-26, owner OK). Team: infrastructure. | release.py | S | dev | a2 |
| R3 | ext_store and proc_unzip have only `nightly` and are not in `release.py`'s stages; the appliance falls back to their nightlies for a release. Tag them (proc_unzip v1.1.0), add them to the train. Team: infrastructure. | release.py, release_assets.sh | S | dev | a2 |
| R4 | First real `promote.yml` run (alpha1/2 predate it; autobleem-core has no tags at all): check `AB_ADMIN_APP_ID`/`AB_ADMIN_APP_KEY` on autobleem-main and `AB_CI_ENABLED` on every stage repo; dry run first. Team: infrastructure. | autobleem-main | S | owner+dev | a2 |
| R5 | autobleem-pc-tools' `origin/master` has 5 commits not on develop (installer ROM folders, "UpdateRoms never lost", CI packaging). Confirm develop has their content. Team: infrastructure. | pc-tools | S | dev | a2 |
| R6 | Masters before the first `release`: some carry CI commits that never went through a release. Reset them to the last release, or let the release merge bring develop in. | all | S | owner | rc |
| R7 | The download page's PS1 emulators tab has no channels: pcsx-ab/abnxt publish only for `v*` tags, and `index_pcsx()` keeps one version. Publish develop pushes (`emu/<name>/nightly/<v>/`), keep the newest per channel, draw the channel pills. | pcsx-ab, pcsx-abnxt, autobleem-repo | M | dev | b1 |
| R8 | CI hardening: pin `actions/*` to hashes, Dependabot for workflows, "require approval for outside collaborators", read-only default token - per repo. | all | S | dev+owner | rc |
| R9 | Code signing through SignPath (`docs/code-signing.md`): apply, publish the policy (privacy statement vs the update check), five projects, `SIGNPATH_ORGANIZATION_ID` + `SIGNPATH_API_TOKEN`, then `AB_SIGNING_ENABLED=true`. Parked by the owner. | pc-tools, launcher | M | owner | rc |
| R11 | Versioning leftovers: the `upstream` field in `manifest.json` (§3); collapse `repo_index.py`'s four version keys into one semver sort (§6). | several, autobleem-repo | S-M | dev | later |
| R13 | A nightly's UpdateRoms comes from the testing release (observed in the online-update work, never said fixed) - check. | appliance | S | dev | a2 |
| R14 | The doctest suites under wine for the `win` target. | autobleem-build | M | dev | later |
| R17 | A push of the autobleem-build image to develop rebuilds no component, so a toolchain change reaches the nightly only with the next unrelated commit (found by the build-times batch). Team: infrastructure. | autobleem-build, appliance | S-M | dev | b1 |

## C - Console (launcher side)

| ID | What | Where | Size | Who | Ms |
|---|---|---|---|---|---|
| C4 | RetroBoot leftovers on a migrated stick: `RetroArch/bin/retroboot/` (~600 MB, EmulationStation) and `RetroArch/bin/apps/`. The installer offers to remove them (check what the system menu's "RetroArch/EmulationStation" then starts). | core installer | M | dev | b1 |
| C5 | The owner's console note: "the emulator starts into a partially cut menu" - reproduce on the current nightly. (The other three notes - Power Off on a custom kernel, the `roms/<system>` folders, UpdateRoms lost on reinstall - were fixed on 2026-09-23; re-check them in H6.) | pcsx-abnxt/pcsx-ab | S | tester | a3 |
| C6 | A stock console with a RetroBoot 1.1 tree and a later KMFD build wants GLIBC_2.28, so RetroArch never starts: an installer check or a clear message. | installer, manual | S | dev | b1 |
| C8 | **Pad battery in the launcher** (the owner, 2026-09-26, after K3): a small battery indicator per wireless pad (today only PSC-Bios's pairing screen shows it), plus a notification when a pad runs low. The level comes from the kernel's `power_supply` / BlueZ `Battery1` - a core service, shared with E15. Team: software/ui (the data source with hardware). | core, launcher | M | dev | b1 |
| C9 | **Which pad is which PS1 port** (the owner, 2026-09-26): nothing shows which connected pad is player 1 / player 2 in the emulator - today the connection order decides. Show the assignment (Hardware Information / PSC-Bios pads list, and ideally a "P1/P2" hint in the launcher), later let the user swap it. Team: software/ui. | launcher, console-tools, emulators | M | dev | b1 |
| C10 | **SSH keys from the stick**: `rc/boot.sh` installs `System/ssh/authorized_keys` for the AutoBleem kernel's dropbear when the file exists (copy /home/root to /tmp, add the key 700/600, bind-mount - nothing on the eMMC), so a key survives a launcher reinstall. Today it is a hand-made block on the owner's stick (the owner, 2026-09-26: permanent SSH access for the team). Team: hardware. | launcher rc | S | dev | a2 |

## H - Hardware proofs (the tester checklist)

| ID | What | Where | Size | Who | Ms |
|---|---|---|---|---|---|
| H1 | **The quiet stick on a console, both kernels** - never run there (the Pi 400 was measured): resume from a kept slot (`AB_LOAD_STATE`, never exercised anywhere), `AB_EXIT_DIR` with a real game in both emulators, `AB_MEMCARD_DIR`, `tools/stick_writes.sh` numbers, RetroArch 1.22's `--appendconfig` + `restoreAppended()` - checklist §13 (written 2026-09-26). | launcher, both emulators, checklist | M | dev+tester | a3 |
| H2 | **The Store on hardware**: the console on the AutoBleem kernel's WiFi (an App from the catalog, a two-disc TSV game, a download resumed after standby), the Pi 400, the PC stick, the Windows product; extensions (`hello`, the crash guard, the display hand-over) on each. | checklist §10 | M | tester | a3/a4 |
| H3 | Scanner processors on the console and a Pi (checklist §11): Unzip stopped by a game and finished by the next scan, the installers' new folders. | checklist §11 | M | tester | a3 |
| H4 | The launcher's own ROM scan on a console (only UpdateRoms' playlists have run there). | launcher | S | tester | a3 |
| H5 | Power Off on both kernels (checklist §9). | checklist §9 | S | tester | a3 |
| H6 | Re-check the owner's console notes 1-3 (see C5). | - | S | tester | a3 |
| H7 | **The DebugDriver over the LAN on a device** (feature/debug-driver-lan, 2026-09-26 - tested on the PC only): the Pi 400 (a systemd drop-in with `AB_DEBUG_PORT`, `AB_DEBUG_BIND=<its IP>`, `AB_DEBUG_TOKEN`, then `ab_drive.py run "..." --host 192.168.68.144 --port ... --token ...`, `grab` a screenshot) and the PSC (the same exports in the stick's `run.sh`); remove the test settings afterwards. Only when the owner says the machine is free. | Pi 400, PSC | S | owner+tester | a3 |
| H8 | **Keyboard control on real hardware** (software/ui's owner-bugs batch, 2026-09-26): a USB keyboard on the PSC (Esc = Circle now, not power off; the console's power button unchanged), the Pi 400 and the PC stick - the PC-style map, sysfs keyboard detection (the Button Guide's Keyboard column appears only then), hot-plug. Team: hardware runs it, software/ui fixes. | launcher, core (`Input`, `KeyboardPresence`) | S-M | tester | a3 |
| H9 | **PSC-Bios Network & Controllers on the Pi 400 and the PC stick, as root** (the nmcli/bluetoothctl backend, `NmBackend`): Wi-Fi scan/connect (never the Pi's own ssh Wi-Fi), time zone via timedatectl, BT scan/pair/remove, rfkill unblock. Team: hardware, software/ui fixes. | console-tools | M | tester+owner | a3 |
| H10 | **The PSC-Bios pad-mapping wizard with a real pad** on the console and a Pi: holding Circle 2 s exits (bar + hint), a short press still maps, Esc exits. Team: hardware, software/ui fixes. | console-tools | S | tester | a3 |
| H11 | **The Network & Controllers hub and the "greyed provider" item on the console**: a PSC-Bios disabled by the crash guard shows greyed with its reason, and Cross opens Extensions at it. Team: hardware, software/ui fixes. | launcher | S | tester | a3 |
| H12 | **Large files with `-D_FILE_OFFSET_BITS=64`** (psc/rpi builds): a Store download over 2 GB on the console and on a 32-bit Pi. Team: hardware, software/ui fixes. | launcher, console-tools | S | tester | a3 |
| H13 | **The Store's source icons over a real network on the console** (abfetch): a root page with `<link rel=icon>`, the retry after a failed fetch (Refresh), a corrupt cached icon healed. Team: hardware, software/ui fixes. | ext_store | S | tester | a3 |
| H14 | **The L1/R1 scroll sound at the d-pad's volume**, judged by ear on the console. | launcher | S | owner | a3 |

## K - Kernel and kernel payload

| ID | What | Where | Size | Who | Ms |
|---|---|---|---|---|---|
| K3 | The rest of the pad-driver test list on a console (the pad-driver payload is flashed and runs; tested 2026-09-26: modules load, DS4 v2 over BT, DS3 by cable through abbtagent, a SHANWAN clone, pairings kept over reboots and flashes): DualSense, Switch Pro and Xbox over BT, every pad in the launcher. And PSC-Bios native backend step 5 leftovers (`apps/pscbios/docs/native-backend-plan.md`): a wrong password, a cancelled pairing, bluetoothd stopped or hung, a WiFi dongle not named wlan0. | psc-kernel-payload, console-tools | M | tester | a3 |
| K4 | The `next` variant: `build.sh -V next all`, validate `psc_next_defconfig` on Buildroot 2024.02, sixaxis on the newer BlueZ (forward the DanTheMans patch to `patches-next/` if it regresses). | psc-kernel-payload | M | dev | later |
| K5 | Modern USB WiFi: backports first, then out-of-tree (rtl8812au, 8821cu, 88x2bu, mt76), each a psc-kernel commit. | psc-kernel | L | dev | later |
| K7 | The rear/micro-USB (OTG) port on the AutoBleem kernel: hot-plugging there drops the USB stack (`-71`), cause unproven. Interim advice - plug in only with the console off, the stick on a front port - into the manual. (After a *standby* its host session is not restarted either - fixed in the launcher's `selection.sh`, AutoBleem2 `f18583b`, through `mt_usb/swmode`; a kernel fix in MediaTek's musb resume would be the proper one.) | payload, manual | S/M | dev | b1 |
| K8 | `ntpget` in the overlay is a prebuilt binary whose source was never found. | psc-kernel-payload | S | dev | later |
| K10 | **Bug: the mouse cursor is back after a Bluetooth pad reconnects** (the owner, K3.1 step 7, 2026-09-26: DualSense + DS4 re-paired, power-cycled, PS pressed - the pads work, but a mouse pointer shows on screen). Likely the pad's touchpad/motion input nodes appearing on reconnect and escaping payload db4fc89's no-pointer rule (a udev rule applied at pairing, not on a later hot-plug?). Reproduce, fix in the payload (and the launcher's `SDL_ShowCursor` if it is the launcher's). Team: hardware. **Fix merged 2026-09-26 (psc-kernel-payload d85093c: rule 81->99, LIBINPUT_IGNORE_DEVICE, TAG-="seat", motion-sensors node too); left: the owner's console run, part B of `E:Programming_work-kernelTESTS-K10.md`.** | psc-kernel-payload, launcher | S | dev | a2 |
| K11 | **Bug: cancelling a Bluetooth pairing does not cancel it** (the owner, K3.5, 2026-09-26): Circle during "Pairing ..." puts the row back to "new" and nothing hangs, but the DS4 finished pairing a moment later anyway. PSC-Bios's native backend must really stop it (BlueZ `Device1.CancelPairing`, then remove the half-paired device), or show the pad as paired if it could not. Team: hardware. | console-tools (PSC-Bios native backend) | S | dev | a2 |

## E - Emulators and RetroArch

| ID | What | Where | Size | Who | Ms |
|---|---|---|---|---|---|
| E1 | **pcsx-abnxt phase 7, the compatibility pass** - the 20 built-in games and the `title.h` titles on the console, a subset on the Pi: boot, first minutes, a save, FMV, CDDA, a real disc swap (Parasite Eve, RE2, FF7). It decides which of Sony's 131 per-title hacks are needed. abnxt has been the default since 2026-09-21. | pcsx-abnxt | L | tester+dev | b1 |
| E2 | pcsx-abnxt phase 8: the only emulator in `emu/`, pcsx-ab archived - the owner decides after E1. | pcsx-abnxt, appliance | M | owner | b1 |
| E3 | pcsx-abnxt: a "which disc" picker in the launcher's resume menu, and the `.m3u` hand-over. | pcsx-abnxt, launcher | M | dev | later |
| E4 | Windows direct mode: Chinese in pcsx-abnxt needs a `fonts/` folder next to the emulator. | launcher/win | S | dev | a4 |
| E5 | pcsx-abnxt's 32-bit Pi build has never run. | pcsx-abnxt | S | tester | a4 |
| E6 | A save state loaded in the first seconds of an HLE boot spins in the HLE BIOS (a PC without a BIOS cannot test resume). | pcsx-abnxt | M | dev | later |
| E7 | Upstream PR candidates (`path_is_absolute`, `PCSX_MEMCARD_COUNT`, soft filter, the 4:3 layer rule, player-2 analogs, `pl_scanlines_by_plat`, the `MENU_SHOW_VOUTMODE` NULL fix). | pcsx-abnxt | M | dev | later |
| E8 | pcsx-ab: the Windows dev build crashes a moment after loading any state; ~30 implicit prototypes kept at warning level; CDDA in CHDs untested by ear. | pcsx-ab | M | dev | later |
| E9 | Our own RetroArch cores: the console runs RetroBoot 1.2's `km_*` pack; build `cores.txt` (81; about a day on the server), test on hardware, then consider `cores-full.txt`. | retroarch-psc | L | dev | later |
| E10 | The RetroArch theme (`retroarch-psc.cfg`, wallpaper, fonts, RetroSystem icons): "the installer will apply it" - not done. | retroarch-psc, installer | S-M | dev | later |
| E11 | pcsx-ab cannot run Tetrade (PSn00bSDK): after the KSEG1 fix it boots, then goes quiet after the ordering-table clear. Until a redistributable PS1 homebrew boots on the shipped emulator, the sample pack has no PS1 game. Try it on pcsx-abnxt first. | pcsx-ab(nxt), samples | M | dev | b1 |
| E12 | N64 in RetroArch has never been tested with a real game (the homebrew RSP tests crash GLupeN64 inside the core). | retroarch-psc | S | tester | later |
| E13 | picodrive's Cyclone core segfaults on the Pi 400 (worked around in `rpi.cores.cfg` with Genesis Plus GX) - unexplained. | launcher platform ini | M | dev | later |
| E14 | No i386 build of either PS1 emulator: the PC stick plays PS1 through RetroArch's pcsx_rearmed core until pcsx-abnxt gets one. | pcsx-abnxt | M | dev | later |
| E15 | **Pad battery overlay in the emulators** (the owner, 2026-09-26): a tiny battery icon in a corner while a game runs (pcsx-abnxt, pcsx-ab, RetroArch if feasible - its own overlay/notification), shown only for a wireless pad and when low or on a button hold; reads the same level as C8. Team: software/ui. | pcsx-abnxt, pcsx-ab, retroarch-psc | M | dev | b1 |

## X - Console tools and PC tools

| ID | What | Where | Size | Who | Ms |
|---|---|---|---|---|---|
| X1 | **PSC-Bios native backend** (wpa_ctrl WiFi, BlueZ over D-Bus, replacing the `abnet`/`bt` scripts that failed on the console for a whole night). Steps 1-3 are 4 commits **only on the owner's PC** (`E:/Programming/autobleem-console-tools`, `feature/native-backend`, never pushed), and step 4 (async screens) is ~1,800 lines uncommitted. Push, finish step 4, then the console pass (step 5: DS4, DS3 cable, WiFi from nothing, a wrong password; the `netdev` group, the D-Bus policy, `/etc/timezone`, `settime`). | console-tools | L | dev+tester | a3 |
| X2 | PSC-Bios translations: 5 languages from 2020 are half empty, 11 missing - the 16-language rule. | console-tools | M | dev | b1 |
| X3 | ABFlashKit never checks `abrootfs.md5` (only `boot.md5`); its `payload/` holds a checked-in binary and an old readme. | console-tools | S | dev | b1 |
| X4 | LastResortRecovery has never run against a console, and its driver install (self-signed catalogue) was never exercised - both need the owner's OK. Point `docs/kernel-flash-recovery.md` at it. | pc-tools | M | owner+tester | b1 |
| X5 | UpdateRoms passes no ROM scan-state file (the digest is portable) - rescans are slower than they need be. | pc-tools | S | dev | later |
| X7 | **The owner's console stick as an installable image** (the owner asked, 2026-09-26): the next time the stick is in the PC, back it up whole (every file, to `E:\tmp\`), then turn that tree into an image/package the PC installer (AutoBleemInstaller - the "USB PC installer") can install onto a stick - a known-good, tested state (nightly 157 + develop's rc/PSC-Bios/payload of 2026-09-26, the Apps and games on it) to restore or reproduce. Check first what format the installer takes (its package/zip layout, `InstallerJob`) and leave out what must not be copied: `System/ssh/` (a TEMP SSH key), per-console state (`System/Bios`, `Preferences`, `Region`, `UI` are the console's own backups), logs, `FOUND.*`, `$RECYCLE.BIN`, `System Volume Information`. Say where the owner's games/BIOS files would end up before building anything shareable - the image is for the owner's own use. | pc-tools, owner's stick | M | dev | a3 |
| X8 | **PSC-Bios: the wrong-WiFi-password message is too long to read** (the owner, K3.4, 2026-09-26): "Could not connect to <network>: wrong password (...)" runs past the row. Shorten it (the reason alone, e.g. "Wrong password") or wrap it; check every language file. Team: software/ui. | console-tools | S | dev | a2 |

## S - SDK, extensions, the Store, processors

| ID | What | Where | Size | Who | Ms |
|---|---|---|---|---|---|
| S2 | The curated SDK surface (`include/autobleem/sdk/` - does not exist yet) and its export list (version script / `.def`); surface classes moved to pimpl as they are touched. | autobleem-core | M | dev | b1 |
| S3 | The SDK package `autobleem-sdk-<target>-<v>.tar.gz`, so an `ext_<name>` builds without the launcher's tree; the abidiff check against the last release in CI (the console tools and ext_store already compare `AB_SDK_ABI`). | core, build | M | dev | b1 |
| S4 | The Windows product with a plugin: the MinGW toolchain now links extensions with static libstdc++ and CI checks it - verify once and close. | launcher | S | dev | a2 |
| S5 | A generic `ab_classic` detail pane (the Store's pane and `GameDetailPane` rebuilt on it). | core | M | dev | later |
| S6 | Author documentation: App format (folder, keys, ini, when `run.sh`), extensions (surface, lifecycle, ABI, building), processors (`proc_template` or a page), the Store's TSV (ext_store's README has it - link it publicly). | hub, core, proc_template | M | dev | b1 |
| S7 | A resumed Store download must re-request the *original* URL: GitHub's signed redirects expire after about an hour (`abfetch --continue`, `queue.txt`). | ext_store, abfetch | S | dev | a3 |
| S8 | Homebrew PS1 games in the Store (`docs/store-homebrew-plan.md`, researched): four questions for the owner in its section 5. | ext_store, repo | M | owner then dev | later |
| S9 | Scanner processors, next (the launcher's `docs/scanner-processors-next-plan.md`): processors as a Store item kind, launch-time processors (`--prepare`/`--cleanup`), signatures or a trusted list, `Heavy=`. | core, ext_store | L | dev | later |
| S10 | Remove the memcard `backup/` + `restoreAll` recovery path "in a later release" (the quiet stick made it unnecessary). | core | S | dev | later |

## A - Apps and the virtual gamepad

| ID | What | Where | Size | Who | Ms |
|---|---|---|---|---|---|
| A1 | The App ports' console pass, the rest of checklist §12 (the owner's first pass gave six `-2`/`-3` releases), on a stick whose launcher has the Reset watch (>= `6e5b580`). 2026-09-26: OpenBOR `7533-4` starts and plays, Amiberry `5.9.3-2` takes one menu step per D-pad press (its `pad.ini`, `movement = as-is`) - both had failed on nightly 157, whose `app_env.sh` predated `bf3bfa7` and gave the Apps the firmware's SDL 2.0.4; any nightly >= `169-ge22d771` has the fix. | checklist §12 | M | tester | a3 |
| A2 | OpenBOR's games: the owner names one or two free paks for the next `v7533-n`. | app_openbor | S | owner | any |
| A3 | abpad: keyboard mode (written, never exercised with a keyboard-only App); a launcher page showing which pads the daemon sees; does a stock kernel have uinput. | launcher | M | dev | later |
| A4 | The Terminal App on the PC stick (untested); on Windows the first character after a resize can be lost (ConPTY). | app_terminal | S | tester, dev | a4 |
| A5 | Publish App ports to the Store from CI (today: `gh release download` + `store_item.py` + `repo_publish.sh store` by hand in 8 repos; ext_store's `site` job is the model). | app_*, repo | M | dev | b1 |
| A6 | One source for the shared build helpers: `check_psc_binary.sh` (two variants), `check_needed.sh` (three), `store_item.py` (eight copies), the toolchain files (four `PSCtoolchainV8.cmake` variants). | autobleem-build | M | dev | b1 |

## P - The other platforms

| ID | What | Where | Size | Who | Ms |
|---|---|---|---|---|---|
| P1 | Pi 400: the pad is dead 1-3 s after every game and at boot - the multi-mode pad re-enumerates under SDL's hidapi probe. `SDL_HINT_JOYSTICK_HIDAPI=0` swapped Triangle/Square (reverted); fix with a pad-database line for the evdev GUID, or by not closing the pad around a game. | launcher | M | dev | a4 |
| P2 | The PC stick beyond the BIOS VM: 32- and 64-bit UEFI, real hardware, a pad; AutoBleemFlasher writing a stick the owner boots. | checklist | M | tester | a4 |
| P3 | Windows: the self-update never ran end to end against the site; a real PS1 game never went through the whole chain (a fake disc only). | checklist §6 | S | tester | a4 |
| P4 | Pi image: the interactive WiFi prompt on a flash without presets; an armhf image boot. | appliance | S | tester | a4 |
| P5 | A Pi updating itself to the refreshed nightly, 32- and 64-bit, games and settings kept (checklist §4). | checklist §4 | S | tester | a3 |
| P6 | LAN Share discs: a multi-disc game, CD audio tracks, a LibCrypt game (needs a drive that gives the subchannel), each published to a Pi's abstored and installed through the Store on the Pi 400 and the console. | pc-tools | M | tester | a4 |
| P7 | Atari VCS 800: the one probe that decides the port's shape (the launcher's `docs/atari-vcs-plan.md`). | - | S | tester | later |

## D - Documentation and repository hygiene

| ID | What | Where | Size | Who | Ms |
|---|---|---|---|---|---|
| D1 | Compact the launcher's CLAUDE.md (1451 lines, ~45 stale statements) to ~500: its project-wide parts are now `docs/console.md`, `docs/emulator-contract.md`, `docs/app-ports.md`; the dated "Current work" narrative goes to `docs/history/`; the lib_ableem/core sections go to autobleem-core's new CLAUDE.md. | launcher, core | M | dev | a2/b1 |
| D2 | Rewrite the launcher README (says "private", "never run on a console", a wrong stick layout, the tools "in this tree"). Also pcsx-abnxt's README (upstream's text, no AutoBleem intro) and retroarch-psc's ("private", crosstool-ng as the build). | launcher, pcsx-abnxt, retroarch-psc | S | dev | a2 |
| D4 | **The manuals exist twice and each copy has what the other lacks**: the launcher's (609 lines: Store/Extensions, Scanner processors, "On the PC" with LAN Share, new screenshots) and autobleem-manuals' (505: the channel texts, the flasher, the Updates row, abnxt as default). Merge into autobleem-manuals, normalise it to LF, delete the launcher's copy and tools, rebuild and publish the PDFs. Then (the rest of C2, 2026-09-26) have the console package carry the current manual PDF in `Docs/` - today `payload/Docs/README.txt` only points at the site's manual. | launcher, manuals | M | dev | a2 |
| D5 | **autobleem-themes becomes the themes' source** (the owner, 2026-09-26): ~~bring it up to the launcher's five themes~~ (step 1 done 2026-09-26: autobleem-themes develop f6bd6e6, packaged, nightly + v* release), then the launcher/appliance take the themes from it (a release or pinned commit, like the other components) and the launcher's `payload/Themes` copy goes. `themes/default` stays wherever `Theme::load()` needs it at build and test time. Team: hardware. | themes, launcher, appliance | M | dev | a2 |
| D7 | Remove the launcher's `docker/` (a stale copy; its `docker/repo/` is a stale copy of autobleem-repo's) - but first sync the launcher's **newer** `toolchains/` and `ci/build.sh` into autobleem-build (MinGW static runtime for extensions, `PKG_CONFIG_LIBDIR`, the abpad and extension-DLL checks); autobleem-build still validates `apps/pscbios`/`apps/abflashkit`. | launcher, build | M | dev | b1 |
| D8 | `payload_linux/` exists twice and has drifted again (the appliance's `install.sh` has journald-in-RAM). Keep the appliance's; the launcher keeps only `Autobleem/rc/` for its tests. | launcher, appliance | S | dev | b1 |
| D9 | Launcher `tools/` vs the appliance's: 5 scripts identical, 5 diverged (`make_psc_package.sh`, `make_rpi_image.sh`, `make_rpi_package.sh`, `make_win_package.sh`, `pack_psc_apps.py`) - packaging belongs to the appliance; also the site tools (`repo_publish.sh`, `repo_index*.py`, `rpi_imager_*`) still in the launcher. | launcher, appliance | S | dev | b1 |
| D10 | Repositories without a top-level CLAUDE.md: **autobleem-core** (the SDK - its knowledge is in the launcher's), autobleem-console-tools (its app docs point to a root CLAUDE.md that does not exist), autobleem-pc-tools, autobleem-appliance (only a Pi user README), autobleem-build (only `docker/README.md`); and no README at all in manuals, themes, samples. | several | M | dev | b1 |
| D11 | Stale per-repository docs (lists in the 2026-09-26 audit): pcsx-ab's status table (2026-09-17); pcsx-abnxt's "SDL 2.0.12", `github.com/autobleem/*` names and the GLIBC 2.12 typo; psc-kernel-payload's internal contradictions (Buildroot 2020.02 vs 2022.02, glibc 2.28 vs 2.34, who builds the kernel, "nothing has booted", `bt-pairing.md`); retroarch-psc's `/media/retroarch` paths; the app_* versions and "not yet run on a console"; ext_store's "installed by hand" and "menu item 6"; the appliance README's channels, logs and old flows; docker READMEs' paths; pc-tools' CLAUDE.md paths; the launcher's `menu-options.md` (Select picker, new Options rows) and its plans' status headers (extensions, store, app-format, virtual-gamepad). | many | M | dev | b1 |
| D12 | Archive the remaining launcher plans into the hub: store, app-format, virtual-gamepad once their last row (H2/S6, S6, A3) closes. | launcher, hub | S | dev | a2 |
| D13 | Licensing: Nihilore's terms for the evolution theme's `Absolute Terror.ogg` (it still ships), a note from Axanar and cornelk that their contributions are GPLv3 (optional), the Sony-hash guard test (fail on a known Sony file under `payload/` or `src/resources/`). | launcher | S | owner+dev | rc |
| D14 | Legacy: retire the old GitLab on the build server (compose down, nginx conf, `/srv/gitlab` - six years of unpatched CVEs); the ab2 game editor's 18 rows in a 560-high `menuPanel` (check nothing is cut off); the optional 1.x history graft. | server, launcher | S | owner/dev | later |
| D15 | The manuals in every language the launcher offers; add the USB-network root password (`autobleem`), the front-port advice (K7) and the channel/update sections. | manuals | M | dev | rc |
| D16 | Delete merged leftovers (the owner's OK, 2026-09-26; check each is merged and no session still works in it first): the `pcsx-abnxt-launch` worktree, `_work-extensions`, remote branches `proof/plugin` (launcher), `feature/lan-share` + `feature/last-resort-recovery` (pc-tools), `feature/pscbios-extension` (console-tools), `feature/overlay-never-shadow` (payload). Team: hardware. | several | S | dev | a2 |
