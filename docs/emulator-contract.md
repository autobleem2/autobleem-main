# The launcher and the PS1 emulators - the contract

What AutoBleem hands pcsx-ab and pcsx-abnxt, and what it expects back. Both emulators keep this contract;
a change to it is a change in the launcher (`LaunchService`, `rc/launch.sh`), in core
(`ResumePointService`, `MemcardService`, `PcsxConfig`) and in both emulators, together. Gathered
2026-09-26 from pcsx-ab's and pcsx-abnxt's CLAUDE.md (their "What the launcher hands over" sections now
point here) and the launcher's `rc/launch.sh`.

## The two emulators

| | pcsx-ab (`Autobleem/bin/emu/`) | pcsx-abnxt (`Autobleem/bin/emunxt/`) |
|---|---|---|
| Base | the 2017 PCSX-ReARMed snapshot Sony shipped, plus Sony's and our patches | upstream r26 + our re-implementation of what matters (`frontend/ab/`), libpicofe |
| Status | ships; the fallback | **the default** since 2026-09-21 (Options -> "PS1 Emulator"); compatibility pass pending (todo E1), then the owner decides whether pcsx-ab is archived (E2) |
| Binary | `pcsx-ab` | also named `pcsx-ab` - the launch scripts do not care which folder it came from |

They share `.pcsx`, the `pcsx.cfg` keys, Sony's save-state layout (a state crosses from one to the other,
except an HLE-BIOS state) and a game's own `pcsx.custom.cfg`.

## The run directory

`rc/launch.sh` (arguments: 1 ssFolder, 2 cdfile, 3 lang, 4 region, 5 gameFolder, 6 resume slot, 7 aspect,
8 filter, 9 pad, 10 the emulator - `pcsx-ab` or `pcsx-abnxt`, 11 the UI language) builds `/tmp/runpcsx/`:

| Entry | Is |
|---|---|
| `.pcsx` | a link to the game's `Games/!SaveStates/<folder name>/` (internal games: `/<id>/`) - `pcsx.cfg`, `sstates/`, `screenshots/`, `memcards/`, `filename.txt`, `lastcdimg.txt` |
| `bios` | a link to `System/Bios` (the user's BIOS files; none ship with us) |
| `plugins`, `skin`, `lang` | links into the emulator's folder |
| `fonts` | the launcher's fonts folder, for a language whose glyphs nxt's own font lacks (Chinese) |

The game's `pcsx.cfg` is copied into `.pcsx` only when it differs. The binary is copied to `/tmp/pcsx` and
run from there with:

```
-filter <f> -ratio <aspect> -lang <n> -region 4 -enter 1 [-load <slot>] [-language <Name>] -cdfile <image>
```

`-filter` is nxt's numbering (0 Off, 1 Linear, 2 Sharp); the script flips it for pcsx-ab (0 bilinear,
1 nearest, no Sharp). `-language` goes to nxt only. Exit status 0 is every normal way out; anything else
came from a crash handler and `ab_persist_logs` keeps the logs.

## A game's configuration - one source

The launcher's `pcsx.cfg`, or - once the emulator's menu saved "Save settings for this game" - the game's
own `.pcsx/pcsx.custom.cfg`, which both emulators load over `pcsx.cfg` and are its only writers.
`PcsxConfig::value()` in core reads the custom line first; the game editor greys its Video/Emulator rows
until "Unlock the settings" deletes the file. `Bios = SET_BY_PCSX` -> `romw.bin` (US/EU), `romJP.bin`
(JP), HLE without the file; `card2.mcd` is `none`.

## What comes back

On exit the emulator writes, in the `.pcsx` layout: `sstates/<name>.000` (the live state at the moment of
leaving), `screenshots/<name>.png` (its picture, taken from a frame without the HUD), `lastcdimg.txt` (the
disc in the drive), and **last** `filename.txt` - the launcher's sign that the game ended cleanly and its
resume point is good. A memory-card write in the last 2 s is waited for ("SAVING..."), so the state and the
card agree.

## `abfeatures` - the quiet-stick hand-over

An `abfeatures` file next to the binary lists what the emulator takes; the launcher sets only those
variables (an older launcher sets none, an older emulator ignores them):

| Variable | Feature | Effect |
|---|---|---|
| `AB_EXIT_DIR` | `exitdir` | the exit files above go to `<runtime>/exit` (RAM); the launcher copies them to the stick only when the player keeps a slot |
| `AB_MEMCARD_DIR` | `memcarddir` | the game's card set (`Games/!MemCards/<set>`) is played in place instead of being swapped in and out |
| `AB_LOAD_STATE` | `loadstate` | the kept slot is loaded where it is (like `-loadf`; `-load` is then ignored) instead of being copied to slot 0 |

**Not yet run on a console in either emulator** (todo H1).

## Every way out leaves the game as it is

The owner's rule (2026-09-24): the menu's Exit, the window's close, **the menu button held 2 s** (on every
platform; Select+Start is Home on a pad without a Guide button), the console's **RESET** button
(`KEY_PLAYPAUSE`: pcsx-ab `SACTION_RESET_EVENT`, nxt `SACTION_AB_RESET`), POWER and overheating all end the
emulator's loop, and the live state is saved after it, between two CPU slices. OPEN (`KEY_EJECT`) changes
the disc (refused for the first 22 s). The same rule holds for Apps (`docs/app-ports.md`).

## Multi-disc

The scan writes an `.m3u` for a multi-disc game; RetroArch gets the `.m3u`, pcsx-abnxt reads an `.m3u`, a
multi-disc PBP or the folder's images of one kind; pcsx-ab gets the first disc's `.cue` and its disc picker
lists the folder.
