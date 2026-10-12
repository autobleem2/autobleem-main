# A PS1 disc in a USB drive - the plan (2026-10-12)

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

- **The icon**: none with no drive; a still disc icon with an empty drive (optional - see Open); blinking
  while reading; lit when the disc is ready but the carousel is shown (after Circle).
- **Ready**: the carousel fades out, the disc's cover fades in at the selected game's place, with its
  metadata, and the disc badge on the cover. Cross plays it; Circle goes back to the carousel; taking the disc
  out goes back too. Not a PS1 disc: a short message, the carousel stays.
- **Themes**: two new assets, the disc icon and the badge on the cover, with defaults in the default theme
  (the Graphic Designer draws them); a theme without them gets the defaults.
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

### 8. Testing

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
| 3 | The Pi with the owner | ~1% |
| 4 | The console: the kernel modules, the rc, the device check | ~3% |
| 5 | The PC USB stick | ~1-2% |

## Open

- Where the drive icon sits on the carousel screen, and whether an empty drive shows it at all: a mockup from
  the Graphic Designer first.
- Where the multi-disc set comes from for a disc that is not in the library (the covers db or the rdb).
- On the Pi, the launcher's user and its access to `/dev/sg*` and the hub's `power/control`.

## Not in this plan (new things, for the owner's list)

- Copying a disc to the stick as an image (with its `.sbi`): `DiscReader` already does the reading.
- A built-in `.sbi` pack by serial, so LibCrypt discs play on drives that cannot give raw P-W.
- Playing audio CDs.
