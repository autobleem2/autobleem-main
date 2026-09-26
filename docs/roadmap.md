# Roadmap - to alpha2 (again) and on to 2.0.0 (2026-09-26)

Where the project stands and the order the open work goes in. Every item named here is a row of
**`docs/todo.md`** (its ID in brackets); ideas nobody has committed to are in **`docs/ideas.md`**. Written
from a read of every repository's documentation on 2026-09-26 - re-plan when a milestone closes. Kept by
Eleanor Voss - Program Manager (roadmap), `docs/decisions.md`.

**Renumbered 2026-09-26** (the owner): `v2.0.0-alpha2` and the stray `v2.0.0-alpha3` are withdrawn - what
the teams do now is still the road to the next pre-release, which is **alpha2** again. The old plan's
alpha3/4/5 are now alpha2/3/4; todo.md's milestone column follows.

## Where we are

| | |
|---|---|
| Last pre-release (the **testing** channel) | `v2.0.0-alpha1` once alpha2 is withdrawn (R1); `v2.0.0-alpha2` (2026-09-23) is still published until then |
| **Nightly** | `v2.0.0-alpha2-149-g4edd7b0-n4ac996` - becomes `v2.0.0-alpha1-...` when the alpha2 tag goes (R1 keeps the update check sane) |
| Stable (**release** channel) | none yet |
| Only in the nightly | extensions + the bundled Store, scanner processors + bundled Unzip, the quiet stick, multi-platform Apps and eight source-built App ports, abpad's Reset watch, PSC-Bios as an extension, LAN Share, LastResortRecovery, the community pad database |
| Proven on hardware | the console pass of 2026-09-19 (launch, sound, RetroArch, tools); the Pi 400 (quiet stick, Store, processors); the App ports' first console pass (2026-09-25/26); the pad-driver kernel on a console (2026-09-26) |
| **Not** proven on hardware | the quiet stick on a console, the emulators' `abfeatures` hand-over, the Store on a console, processors on a console, the PC stick on UEFI, Windows self-update |

## The milestones

| Milestone | Theme | Gate (what "done" means) | Who | Size |
|---|---|---|---|---|
| **alpha2** | Ship what is already built; make the release train work | `promote alpha` runs green end to end; the nightly's features in the testing channel; nothing false shipped on the stick | dev + owner decisions | ~2-3 days |
| **alpha3** | The console pass | every nightly feature proven on a console on both kernels (stock and AutoBleem); PSC-Bios native backend proven | dev + owner/testers | ~1 week |
| **alpha4** | The other platforms' pass | Pi (32/64), PC stick (BIOS + UEFI, real hardware), Windows (self-update, a real game), LAN Share - each proven | testers + dev fixes | ~1 week |
| **beta1** | Feature-complete, one of everything | pcsx-abnxt's compatibility pass done; the SDK package out; no duplicate trees; every repository documented; translations complete | dev + testers | ~2 weeks |
| **rc1 -> 2.0.0** | Release hygiene | signed Windows programs, masters clean, licensing closed, manuals in every language, CI hardened | owner + dev | ~1 week |
| **2.1+** | New features | from `docs/ideas.md` and the "later" rows of todo.md | - | - |

## The alpha releases

### alpha2 - "the release train works"

Everything in the nightly is ready for testers. What stands between it and a tagged pre-release is the
release process itself, plus a few things that should not ship to anyone.

| # | Must do before tagging | ID | Team | State |
|---|---|---|---|---|
| 1 | **Withdraw alpha2 and the stray alpha3** (tags, GitHub Releases, the site's testing channel), keep the nightly's update check sane, `release.py` skips an existing tag | R1 | infrastructure | decided 2026-09-26, to do |
| 2 | **Bring autobleem-build's master up to develop** (8 commits: SDL2 2.0.14 without OSS, no UPX on Windows, libdbus in the psc sysroot) and make it a release-train step | R2 | infrastructure | owner OK 2026-09-26, to do |
| 3 | **Give the Store and Unzip real releases** and add them to `release.py`'s stages | R3 | infrastructure | to do |
| 4 | **First real `promote.yml` run** (dry run first) | R4 | infrastructure + owner | after 1-3 |
| 5 | pc-tools' develop has the content of the 5 master-only commits | R5 | infrastructure | to do |
| 6 | The `AB_SDK_ABI` policy | S1 | - | **done**: only with a release; ABI 4 is alpha2's |
| 7 | `rc/app_env.sh`: abpadd with the launcher's SDL2 and our pad database | C1 | - | **done** (launcher `b6bb579`) |
| 8 | Stop shipping the 0.9.0 manuals | C2 | - | **done**; the current PDF in `Docs/` moved to D4 |
| 9 | Drop the launcher's obsolete `payload/Apps/` | C3 | - | **done** |
| 10 | Merge psc-kernel-payload's `feature/userland-refresh` | K2 | - | **done** (`1e8a16f`) |
| 11 | The flaky `test_update_service` | R16 | infrastructure | to do |

| # | Should do (docs and hygiene, no code risk) | ID | Team |
|---|---|---|---|
| 12 | Manuals: one repository, rebuild and publish the PDFs, the current PDF in the console package | D4 | to assign |
| 13 | autobleem-themes / autobleem-samples become the source (decided 2026-09-26) | D5, D6 | hardware |
| 14 | Launcher README rewrite | D2 | to assign |
| 15 | Archive the finished launcher plans (quiet stick, scanner processors) into the hub | D12 | to assign |
| 16 | Delete merged branches and workspaces (owner OK 2026-09-26) | D16 | hardware |

**Exit:** `v2.0.0-alpha2` on the testing channel, assembled from components all built in the updated
`:latest` image. Testers get the alpha3 checklist.

### alpha3 - "the console pass"

| # | Item | ID | Who |
|---|---|---|---|
| 1 | Merge the pad-driver kernel (psc-kernel `feature/pad-drivers` -> master, psc-kernel-payload `feature/pad-drivers` -> develop, its CLAUDE.md updated). The launcher's develop already depends on it (`2b48e11`, `aae8713`). | K1 | dev |
| 2 | Flash the fixed overlay on a console; run the pad-driver test list (DS4 v2 over BT, DS3 by cable, a SHANWAN clone, DualSense/Switch Pro/Xbox over BT) | K3 | tester |
| 3 | PSC-Bios native backend: push the local branch (4 commits exist only on the owner's PC), finish step 4 (async screens), then the console pass (step 5) | X1 | dev + tester |
| 4 | The quiet stick on a console, both kernels: resume from a kept slot (`AB_LOAD_STATE`), the exit dir with a real game, cards played in place, `stick_writes.sh` numbers, RetroArch's `--appendconfig` restore. Checklist §13. | H1 | dev (checklist), tester |
| 5 | The Store on the console (WiFi, a two-disc TSV game, a download resumed after standby); check that a resume re-requests the original URL (GitHub's signed redirects expire after about an hour) | H2, S7 | tester, dev |
| 6 | Scanner processors on the console (Unzip stopped by a game, finished by the next scan); the launcher's own ROM scan on the console | H3, H4 | tester |
| 7 | App ports: the rest of checklist §12 on a stick with the Reset watch (launcher >= `6e5b580`) | A1 | tester |
| 8 | Power Off on both kernels (§9); re-check the owner's four console notes (the cut emulator menu among them) | H5, H6, C5 | tester |
| 9 | Fixes found by 1-8 | - | dev |

**Exit:** `v2.0.0-alpha3`. The console is the first-class target again: every feature proven there.

### alpha4 - "the other platforms"

| # | Item | ID | Who |
|---|---|---|---|
| 1 | A Pi updating itself to the nightly (32- and 64-bit); the Imager's WiFi prompt with no presets; an armhf image boot | P5, P4 | tester |
| 2 | The Pi 400 pad dead 1-3 s after every game (hidapi re-enumeration) | P1 | dev |
| 3 | pcsx-abnxt's 32-bit Pi build: run it once | E5 | tester |
| 4 | The PC stick on 32- and 64-bit UEFI and real hardware with a pad; the Terminal App there | P2, A4 | tester |
| 5 | Windows: self-update end to end against the site; a real PS1 game through the whole chain; Chinese in pcsx-abnxt (a `fonts/` folder) | P3, E4 | tester, dev |
| 6 | LAN Share discs: multi-disc, CD audio, LibCrypt, each installed through the Store on a Pi and the console | P6 | tester |
| 7 | The Store and extensions on the Pi, the PC stick and the Windows product | H2 | tester |

**Exit:** `v2.0.0-alpha4`. Every platform has a green tester checklist.

### beta1 - "feature-complete"

| Item | ID |
|---|---|
| pcsx-abnxt phase 7, the compatibility pass (it has been the default emulator since 2026-09-21), then the phase-8 decision: pcsx-ab archived or kept | E1, E2 |
| The SDK: curated surface, export list, `autobleem-sdk-<target>` package; author docs for Apps, extensions and processors | S2, S3, S6 |
| One copy of everything: the launcher's `docker/`, `payload_linux/`, packaging `tools/`; one source for the shared build helpers and toolchain files (four `PSCtoolchainV8.cmake` variants today) | D7, D8, D9, A6 |
| Every repository documented: autobleem-core, console-tools, pc-tools, appliance and build have no top-level CLAUDE.md; the stale per-repo docs fixed; the launcher CLAUDE.md compacted | D10, D11, D1 |
| PSC-Bios in all 16 languages; ABFlashKit checks `abrootfs.md5` | X2, X3 |
| RetroBoot leftovers: the installer offers to remove them; a clear message when an old RetroArch tree cannot start | C4, C6 |
| The PS1 emulators tab on the site gets channels | R7 |
| App ports published to the Store by CI | A5 |

### rc1 -> 2.0.0

| Item | ID |
|---|---|
| Code signing through SignPath (wired and switched off) | R9 |
| Masters: reset to the last release, or let the release merge bring develop in | R6 |
| Licensing: Nihilore's terms (the track ships), the Axanar/cornelk note, the Sony-hash guard test | D13 |
| CI hardening: actions pinned to hashes, Dependabot, outside-collaborator approval, read-only default token | R8 |
| The manuals in every language the launcher offers; the USB-network root password and the front-port advice in the manual | D15 |

## Parallel tracks (not tied to a release)

| Track | Items |
|---|---|
| The owner's setup | Telegram for the admin panel (R10), OpenBOR's games (A2), the homebrew plan's four questions (S8), the Atari VCS probe (P7) |
| Kernel, longer term | the `next` variant (K4), backported USB WiFi (K5) |
| After 2.0 | processors next (S9), homebrew in the Store (S8), newer SDL2 on the console, our own RetroArch cores (E11), the themes pack - see `docs/ideas.md` |
