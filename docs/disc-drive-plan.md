# A PS1 disc or an audio CD in a USB drive - the plan (2026-10-12)

Status: **plan, waiting for the owner's approval**. The emulator part is done and on develop; this plan is the
launcher, the core and the platforms around it.

## What the owner asked for

The launcher knows whether a CD drive is connected, also when it is plugged in or out while the launcher runs.
When a disc goes in, the launcher reads it in the background while a disc-shaped icon blinks. From the serial
it finds the cover and the metadata in the database. When that is ready the carousel fades out and the disc's
cover fades in where the selected game always sits, with the disc's metadata and a disc icon on the cover. The
memory cards, the game's config and the resume points belong to the serial. A disc plays only in our emulator
(pcsx-abnxt), never in RetroArch.

## The owner's decisions (2026-10-12)

| Question | Decision |
|---|---|
| The same game is also an image on the stick (the same serial) | The disc uses that game's folder: its memory cards, config and resume points. With no such game, the disc gets its own folder by serial |
| The way back from the disc to the carousel | Taking the disc out, or a button (Circle); after the button the disc stays in the drive and the icon waits on it |
| Multi-disc games | One memory card and one set of saves for the whole set, by the first disc's serial (from the database); changing a disc in a game = opening the tray |
| Platforms | The Raspberry Pi first, then the PlayStation Classic, the PC USB stick last; **Windows does not get this** |
| Audio CDs (the owner's addition: the real PS1 played them too) | An audio CD shows a jewel case with a note and "Audio CD" in place of the cover, with no game config, memory card or resume points; Cross opens a CD player designed in the spirit of the PS1 BIOS's, with a music visualisation - piece 8 |
| The mockups (DISC-1, 2026-10-12 03:1x, files in the Graphic Designer's `!autobleem/out/disc-drive/`) | An empty drive shows a dim disc icon; the drive chip ("Reading the disc...", "Disc: <title>", "This is not a PlayStation disc") is always centred at the top of the screen, never beside the notifications; after Circle, **R1 = "Disc"** brings the disc view back, shown in the carousel footer only while a disc is ready (R1 keeps its meaning elsewhere: in the player it is "next track"); the player's visualisation is **spectrum bars only** (no waveform); **no disc badge on the cover** ("it is on the screen, so it is a CD" - the meta row's "DISC" source tag and the lit chip mark it); the player's buttons as mockup 04: Cross play track, Square stop, L1/R1 previous/next, L2/R2 seek, Triangle repeat, Select shuffle, Start pause, Circle back. **Approved 03:21** ("super - zatwierdzam") |
| Playing a disc that matches a library game | Counts as that game's play ("recently played", the play record), like its image |
| LibCrypt from a drive (2026-10-12 04:56-05:04, after the Pi tests) | With a network the launcher downloads the game's `.sbi` and the emulator reads no Q from the drive; offline the emulator's own reading of the drive's marks stays as the failover. The `.sbi` files come from **our site, a pack of redump's LibCrypt `.sbi` by serial**; when a serial has several versions (Spyro: Year of the Dragon PAL: "Original" and "Rev 1 Platinum", different marks) the launcher fetches all and the emulator reads the 32 LibCrypt places once and takes the version that matches, else the drive's marks - piece 10 |

## What exists already

- **The emulator** (pcsx-abnxt develop `73966e41`): `-cdfile cdrom://driveN.cue` plays the disc in the Nth SCSI
  device (`/dev/sgN` on Linux), sectors read raw with READ CD, the drive at 4x. The subchannel is read too, so
  LibCrypt discs play without an `.sbi` on drives that give raw P-W (tried: an LG GP20N slim, Spyro: Year of the
  Dragon PAL). Its CLAUDE.md, "A real disc in a drive", has the details.
- **The core** (autobleem-core): `DiscReader` with the `CdDrive` interface (TOC, a 2352-byte sector with its
  Q) and Q de-interleaving, written to rip a disc to an image; `SerialScanner` (images only);
  `MetadataLookup::findBySerial` (title, publisher, year, players, the cover's PNG). There is no Linux `CdDrive`:
  the only real one is LAN Share's `WinCdDrive` (autobleem-pc-tools, Windows).
- **The launcher**: no drive detection at all; the only hotplug it knows is the pads'.
- **The hardware** (the probe on the Pi 400, 2026-10-12): a bus-powered slim drive over-currents the Pi's
  port, so it needs a powered hub. The Genesys hub tried autosuspends when empty and then misses a drive
  plugged in later; `power/control=on` on the hub keeps it awake. The kernel's own 2048-byte reads of a PS1
  disc fail (it is Mode 2), so nothing can mount it: the launcher reads raw, like the emulator.

## The pieces

### 1. Core: a Linux drive (`LinuxCdDrive : CdDrive`)

In lib_ableem's engine (no SDL): SG_IO on `/dev/sgN` - READ TOC, READ CD 2352 bytes with raw P-W (the same
probing as the emulator: sub-only or sector + sub, the Q's shift), TEST UNIT READY for "is there a disc",
START STOP UNIT for the tray if a screen ever wants it. Unit tests with the existing `FakeDrive`.

### 2. Core: what the disc is (`DiscIdentity`)

From raw sectors, nothing mounted: the volume descriptor (sector 16), the root directory, `SYSTEM.CNF`'s
`BOOT = cdrom:\SCES_028.35;1` -> `SCES-02835` (`SerialScanner::normalizeSerial`); the volume label when there is
no `SYSTEM.CNF` line. Mode 2 Form 1 user data starts at byte 24 of a raw sector. The result: a PS1 disc (serial,
region, title, cover) / not a PS1 disc (an audio CD, a PC disc) / unreadable. Then `MetadataLookup::findBySerial`;
for a multi-disc game, the first disc's serial from the database's disc set.

### 3. Core: watching the drive (`DriveWatcher`)

A worker thread that polls about once a second (no udev on the console): `/sys/class/scsi_generic/sg*/device/type`
= 5 is a CD/DVD drive, its sg number is what the emulator gets (`drive<N>`), so a stick plugged in before the
drive cannot move it. States: no drive / empty / reading / ready (the identity) / not a PS1 disc / error;
the UI asks for the state, the thread never touches SDL. When it finds a drive behind a USB hub it sets that
hub's `power/control` to `on` (runtime only, nothing written to the stick - the quiet stick rule). It stops
while a game runs (the emulator owns the drive) and starts again after.

### 4. Core: the disc as a game (`DiscGame`)

A `PsGame` made for the disc: when the library has a game with the same serial (or any disc of its set), its
`ssFolder`, memory cards, config and resume points; otherwise `!SaveStates/disc-<serial>/`, made on the first
launch. The launch: pcsx-abnxt only (not pcsx-ab, not RetroArch), `-cdfile cdrom://drive<N>.cue`, the region from
the serial, the resume-point menu as for any game. A resume point is offered only for the same serial.

### 5. The launcher (EvolutionUI)

- **The icon**: a chip centred at the top of the screen (the notifications' height and top, never beside
  them): none with no drive; a dim disc icon with an empty drive; blinking, with "Reading the disc...", while
  reading; lit, "Disc: <title>", when the disc is ready but the carousel is shown (after Circle); dim, "This is
  not a PlayStation disc", for another disc.
- **Ready**: the carousel fades out, the disc's cover fades in at the selected game's place, with its
  metadata and "DISC" as the meta row's source tag (no badge on the cover). Cross plays it; Circle goes back to the carousel; taking the disc
  out goes back too; on the carousel, R1 ("Disc", in the footer only while a disc is ready) brings the disc
  view back. Not a PS1 disc: the chip's message, the carousel stays.
- **Themes**: two new assets, the drive icon (`disc_drive`) and the Audio CD jewel case (`audio_cd_case`), at
  1x and @2x, for ab2.0.0 and the default theme (the Graphic Designer draws them); a theme without them gets
  the defaults.
- **Strings** ("Reading the disc...", "This is not a PlayStation disc", the help lines) in all 16 language
  files in the same commit.

### 6. The emulator, small additions

- The tray opened during a game = the emulated lid open (upstream reads `rcdrom_isMediaInserted`; to be checked
  on the device).
- "Change disc" in the in-game menu, for a drive: "Open the tray and put in the next disc" (all languages).

### 7. The platforms, in order

1. **Raspberry Pi**: the kernel has `sr_mod`, `sg`, `cdrom`; checked who the launcher runs as and whether it
   may open `/dev/sg*` and write the hub's `power/control`.
2. **PlayStation Classic**: its stock 4.4.22 kernel has no `sr_mod`/`sg`/`cdrom` - they go into
   psc-kernel-payload as modules, loaded by the rc at boot; the emulator's psc build gets a device check; the hub
   autosuspend checked on the console too.
3. **PC USB stick**: last; the guest's permissions on `/dev/sg*`.
4. **Windows**: not planned (the owner).

### 8. Audio CDs: the CD player

- **Telling it apart**: a disc whose TOC has only audio tracks is an audio CD; a PS1 game with audio tracks
  (mixed mode) stays a game. The identity gets a fourth result: audio CD (the track list and lengths, the
  CD-Text titles when the drive gives them - READ TOC format 5).
- **The disc view**: a jewel case with a note and "Audio CD" (art from the Graphic Designer, a theme asset with
  a default), the number of tracks and the total time in place of the game's metadata; no config, memory card
  or resume-point entries.
- **The player** (a new screen, Cross on the audio CD): the track grid, play/pause, stop, previous/next, seek
  inside a track, repeat (track/disc) and shuffle, the elapsed and total time; the look in the spirit of the
  PS1 BIOS's CD player, our own design (no Sony art), from a mockup first. The theme's music stops while it
  plays; Circle leaves it; taking the disc out stops it and goes back to the carousel.
- **The sound**: digital, not the drive's headphone socket (a USB drive has no line to the console): a reader
  thread pulls the tracks raw with READ CD (2352 bytes = 1/75 s of 44.1 kHz 16-bit stereo) into a ring
  buffer, SDL audio plays it - through lib_ableem's `Audio`, a new streaming source. Reading ahead a few seconds
  covers the drive's spin-ups.
- **The visualisation**: from the same PCM - segmented spectrum bars with peak caps (a small FFT, 30 times a
  second; the owner chose bars only), drawn with the renderer; cheap enough for the console's CPU, to be
  measured there.
- **Strings** ("Audio CD", "Track", the player's help lines) in all languages.

### 10. LibCrypt: the `.sbi` from our site (the owner, 2026-10-12)

What the Pi showed (Spyro: Year of the Dragon PAL, LG GP20N): the drive gives LibCrypt's marks byte for byte as
redump's `.sbi`, but also ~4% of the sectors' Qs with a bad CRC, the same on every read (scratches - the
subchannel has no error correction), two of them on LibCrypt's places. pcsx-abnxt (develop `c4536582` and on) now
reads the drive's marks once per disc - a pair n, n+5 with both Qs bad - and no subchannel during play; that is
the offline failover. (The game still loops a cutscene with redump's own `.sbi` too, so that loop is not LibCrypt -
a separate emulation issue, on the owner's list.)

- **The site**: `sbi/index.json` (`{"SCES-02835": ["SCES-02835.1.sbi", "SCES-02835.2.sbi"], ...}`) and the files in
  `sbi/`, built once from redump's LibCrypt list by a script in autobleem-repo and refreshed by hand.
- **The launcher**: for a PS1 disc whose serial is in the index, before `launchDisc`, every version is fetched (when
  missing) into the game's save folder as `<ID>.sbi` (one version) or `<ID>.1.sbi`, `<ID>.2.sbi`... (`<ID>` = the
  serial without the dash, as the emulator's CdromId); no network = nothing fetched.
- **The emulator**: `<ID>.sbi` = used as is, no Q read; `<ID>.N.sbi` = the 32 places read once and the matching
  version taken; none matches or no file = the drive's marks.

### 9. Testing

- Core unit tests with `FakeDrive`: the identity from a recorded set of sectors, every watcher state.
- The UI flow on the pcusb-test VM through the DebugDriver needs a drive in the guest: a VirtualBox virtual
  drive with an image, or a dev-only fake drive backed by a cue/bin (`AB_FAKE_DRIVE`) - the first step of the
  work decides which.
- The device checks on the Pi, then the console, with the owner and a real disc (one LibCrypt, one multi-disc).

## Phases and cost (rough, % of a week)

| Phase | What | Cost |
|---|---|---|
| 1 | Core: `LinuxCdDrive`, `DiscIdentity`, `DriveWatcher`, `DiscGame`, their tests | ~3% |
| 2 | Launcher: the icon, the fades, the disc view, the launch, theme assets, strings; the emulator's two additions | ~4% |
| 3 | Audio CDs: the identity's fourth result, the jewel case, the player screen (from a mockup), the streaming source, the visualisation, strings | ~5% |
| 4 | The Pi with the owner (a game disc and an audio CD) | ~1% |
| 5 | The console: the kernel modules, the rc, the device check, the visualisation's cost measured | ~3% |
| 6 | The PC USB stick | ~1-2% |

## Open

- A track's INDEX 00 pregap (the PM's call, reversible): selecting a track starts at its INDEX 01; playing on
  from the track before plays straight through, as a CD player does.
- CD-Text titles come from few discs; looking the tracks up online (MusicBrainz) would be a new thing.
- The multi-disc set: no database maps a serial to its set, so `DiscGameService` takes it from RetroArch's
  rdb ("Game (Region) (Disc 2)" -> the "(Disc 1)" record's serial); without an rdb a disc keeps its own serial.
- On the Pi, the launcher's user and its access to `/dev/sg*` and the hub's `power/control`.

## Not in this plan (new things, for the owner's list)

- Copying a disc to the stick as an image (with its `.sbi`): `DiscReader` already does the reading.
