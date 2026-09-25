# Tester checklist - the release channels, the installers and the updaters

What needs a person with real hardware (or a VM) before the channel work of 2026-09-23 counts as proven.
Every item has what you need, what to do, what you should see, and where the logs are. Report each item as
**pass / fail / blocked**, with the build's version (Options -> About, or the `VERSION` file), the logs
listed for it, and a photo of the screen when something looks wrong.

The three channels, everywhere below:

| channel | what it is | where the site lists it |
|---|---|---|
| **Release** | the newest stable `v*` release - **none exists yet**, so this channel has nothing to offer today; "nothing to install" is the right answer | `releases/latest.json` |
| **Testing** | the one pre-release (today `v2.0.0-alpha2`) | `releases/unstable.json` |
| **Nightly** | the newest development build of `develop` (`v2.0.0-alpha2-N-g<hash>`) | `nightly/latest.json` |

Status column: **ready** = can be tested now; **blocked** = waits for the item named.

---

## 1. PC USB stick flasher (Windows) - ready once `AutoBleemFlasher-<v>.zip` is on the site

**You need:** a Windows 10/11 PC, a USB stick of 8 GB or more whose contents you can lose, an internet
connection; for the boot test a PC (or VirtualBox) that can boot from USB with Secure Boot off.
**Get it:** the download page -> PC -> PC USB stick -> "Flasher for Windows". Unzip, run `AutoBleemFlasher.exe`.

| # | Do | Expect |
|---|---|---|
| 1.1 | Start it | Windows asks for administrator rights (UAC). The window shows the AutoBleem picture, a Channel box and a USB stick box. Within a few seconds the text under them names the channel's version and the download size. |
| 1.2 | Pick **Release** | "The release channel has no stick image" (no stable release yet) - Write is greyed out. |
| 1.3 | Plug a stick in, without pressing Refresh | It appears in the USB stick box by itself, described as model - size (USB, disk N) - drive letter. |
| 1.4 | Have a USB **hard drive** plugged in too, if you have one | It is **not** listed. Tick "Show USB hard drives too": it appears, marked "USB hard drive". Untick it again. |
| 1.5 | Pick **Nightly**, the stick, press Write | Two questions: the first names the stick and says everything is erased (Cancel is the default); the second is a last "erase ... now?" (No is the default). Answering No stops everything, and the stick is untouched. |
| 1.6 | Write again, answer yes twice | Step 1 of 3 downloads (~650 MB, with a bar), Step 2 of 3 writes (the bar in GB), Step 3 of 3 reads back. It ends with "Done - the stick is ready". |
| 1.7 | Run it again, same channel, another stick (or the same one) | Step 1 finishes at once - "is already there" (the image is kept in `%TEMP%\AutoBleemFlasher`). |
| 1.8 | Pick **An image file on this PC...**, choose an `.img.xz` you downloaded from the site, write | Same as 1.6 without the download. With the site's `.sha256` file next to it, the log says "matches its .sha256". |
| 1.9 | Start a write and press Stop half way through | It stops. The message says the stick is not usable until it is written again. Writing it again works. |
| 1.10 | Open a file from the stick in Explorer (or leave an Explorer window on it), then Write | Either it works (Windows let go of the stick), or it fails with "the stick is in use - close every window and program...". It never writes half a stick silently. |
| 1.11 | Boot a PC (BIOS, and UEFI if you can) from a stick written in 1.6 | GRUB, the AutoBleem boot picture, the first-boot setup screen, then the launcher - as for a stick written with `dd`. |

**Logs:** the flasher's window log (copy it with a screenshot); for 1.11 the stick's
`/var/log/autobleem-firstboot-install.log`.

---

## 2. PlayStation Classic installer - the channel box (Windows) - ready

**You need:** a Windows PC, a USB stick for the console, internet. **Get it:** download page ->
PlayStation Classic -> "Installer for Windows" (`AutoBleemInstaller-<v>.zip`: the program and its README only -
the stick's files are downloaded).

| # | Do | Expect |
|---|---|---|
| 2.1 | Start it | Channel defaults to the installer's own kind (a nightly installer -> Nightly). After a few seconds the status says what the channel would install ("A fresh install of AutoBleem v..."). |
| 2.2 | Switch between the three channels | The version in the status changes; Release says it has nothing to install. |
| 2.3 | Fresh stick, **Testing**, Install | The package is downloaded and checked, then unpacked; the stick is named SONY; UpdateRoms is on it (`UpdateRoms/UpdateRoms.exe`); the console boots it. |
| 2.4 | Run it again over that stick with **Nightly** | The status says "AutoBleem v2.0.0-alpha2 is on this stick: it will be updated to ...". After Update, your games, saves and `config.ini` settings are still there and the console boots the new version (About screen). |
| 2.5 | Unplug the network cable / WiFi, start it | The status says the channel has nothing to install and mentions the internet connection. Install stays greyed out. |

**Logs:** `<stick>/System/Logs/installer.log`.

---

## 3. PlayStation Classic updating itself - ready from the first nightly with `abfetch`

The console downloads with `abfetch`, the launcher's own downloader on the stick - nothing from the kernel
payload - so the current AutoBleem kernel and the old 1.x one are tested the same way.

**You need:** a console with an **AutoBleem kernel** (ABFlashKit's, or the 1.x one) and WiFi set up in
PSC-Bios, plus a stick that **already has `abfetch`** (`Autobleem/bin/autobleem/abfetch` - a nightly from after
2026-09-23's `abfetch` change, put on with AutoBleemInstaller) and is one version behind the channel you test
(for example yesterday's nightly, with the Nightly channel chosen). A stick from before that change cannot
update itself (it looks for a curl the kernel does not have) - update it once with AutoBleemInstaller.

| # | Do | Expect |
|---|---|---|
| 3.0 | PSC-Bios (L2+R2 -> Hardware Information on the console) -> WiFi: connect | PSC-Bios shows an IP address. |
| 3.1 | Options -> Updates | The row is there, with release / testing / nightly / off. |
| 3.2 | Choose **nightly**, go back to the carousel, wait up to a minute | An "Update available" dialog shows both versions. |
| 3.3 | "Remind me tomorrow" | The dialog goes away and does not come back when you restart the launcher. |
| 3.4 | L2+R2 -> Software Update | The check runs on screen and offers the update again. |
| 3.5 | "Update now" | A download bar is shown. The launcher then closes, the AutoBleem picture stays on screen while the stick is updated (up to a few minutes), and the launcher comes back. |
| 3.6 | Check the result | About shows the new version. Games, save states, memory cards, the theme and other settings are unchanged. |
| 3.7 | Turn WiFi off (or use a console with the stock kernel), then L2+R2 -> Software Update | "Not connected". No dialog appears at start and nothing slows down. |
| 3.8 | Pull the stick during 3.5's download (only on a stick you can re-install) | The launcher reports the failure. The next boot starts the old launcher. |
| 3.9 | After 3.5, open `System/Logs/update.log` on a PC | It ends with `abupdate exit status 0` and "the stick is AutoBleem <new version> now"; `System/Updates/` is gone. |
| 3.10 | If you have one: repeat 3.0-3.6 on a console with the **AutoBleem 1.x kernel** | The same results. |

**Logs:** `System/Logs/update.log` (the update step), `System/Logs/installer.log`, `System/Logs/autobleem.log`
(the check and the download - the `abfetch` command lines and their exit codes are in it).

---

## 4. Raspberry Pi updating itself - ready

**You need:** a Pi with an AutoBleem image that is one version behind the channel you choose, a network
connection, and a keyboard or pad. Test both 32-bit and 64-bit if you can.

| # | Do | Expect |
|---|---|---|
| 4.1 | Options -> Updates -> nightly (or testing) | Within a minute: "Update available" with the AutoBleem version (and RetroArch if it is newer). |
| 4.2 | Update now | The download bar is shown. The launcher then leaves, the setup screen runs the update on tty1, and the launcher comes back with the new version. |
| 4.3 | Check | Games, settings, cores, BIOS files and samples are kept. The first start rescans the games once. |

**Logs:** `System/Logs/update.log` on the data partition, `System/Logs/autobleem.log`.

## 5. PC USB stick updating itself - ready

The same as 4, on a PC stick (or the VirtualBox VM) that is one version behind. When it was installed, the
setup asked for the graphical or text screen; the update must draw with the same one.

## 6. Windows program updating itself - ready once a newer `AutoBleemSetup` is published on the chosen channel

**You need:** AutoBleem installed with `AutoBleemSetup-<older>.exe` from the site.

| # | Do | Expect |
|---|---|---|
| 6.1 | Options -> Updates -> testing (or nightly) | "Update available" shows the site's version. |
| 6.2 | Update now | The download runs. The launcher closes, the setup wizard shows its progress, and the new launcher starts by itself. |
| 6.3 | Check | Data folder, games, settings, RetroArch and cores are all kept. Add/Remove Programs shows the new version. |

**Logs:** `<data folder>\System\Logs\autobleem.log`, and `System/update.json` (the check's state).

---

## 7. Raspberry Pi Imager - one list per channel - ready

**You need:** Raspberry Pi Imager 1.9 or newer and an SD card.

| # | Do | Expect |
|---|---|---|
| 7.1 | Download page -> Raspberry Pi: the box lists the Imager repository addresses | Only Testing and Nightly are listed (no stable release yet). Each has a Copy button. |
| 7.2 | Imager -> App Options -> Content Repository -> Use custom URL, paste the Testing one | AutoBleem appears with the 32-bit and 64-bit images of `v2.0.0-alpha2`. |
| 7.3 | The same with the Nightly one | The nightly build's images, newer version number. |
| 7.4 | Flash one of them with Imager's customisation (user, WiFi) and boot it | The first-boot setup screen, then the launcher (as described in the Pi manual on the site). |

## 8. The download page - ready

| # | Check | Expect |
|---|---|---|
| 8.1 | PC tab -> PC USB stick | "Flasher for Windows" is listed with the images, per channel, once published. The "Step by step" page's *Writing the stick* section starts with the flasher. |
| 8.2 | Every download link on every tab | Each one downloads, and its size matches the table. |
| 8.3 | Phone-width browser | No sideways scrolling. The tabs and tables stay readable. |

## 9. PlayStation Classic Power Off - ready from launcher `f3e88ff`

**You need:** a console with the AutoBleem stick. Test the setups you have: the stick in front port 2
(stock or AutoBleem kernel), and, on the AutoBleem kernel, the stick on a hub in the micro-USB (power) port.

| # | Do | Expect |
|---|---|---|
| 9.1 | Stick in a front port: L2+R2 -> Power Off -> confirm | After a few seconds only the red LED is on (standby). The stick may be pulled now. |
| 9.2 | Press POWER | Green LED, the AutoBleem picture, and the launcher is back within about 15 s (no full boot). |
| 9.3 | Stick on a hub in the power port (AutoBleem kernel): L2+R2 -> Power Off -> confirm | After about 10 s the console switches off (red LED). The launcher does not come back by itself. |
| 9.4 | Press POWER | A normal full boot into AutoBleem. The stick is not reported as needing repair in Windows afterwards. |

**Logs:** `System/Logs/standby.log`. A power-port setup ends each Power Off with "powering off instead" and
the kernel's reason (`usb1 failed to suspend`).

## 10. Extensions and the AutoBleem Store - ready (nightly `v2.0.0-alpha2-149-g4edd7b0-n4ac996`, 2026-09-25)

**You need:** that nightly on a console (AutoBleem kernel, WiFi set up in PSC-Bios), a Pi or the PC stick. The
Store is bundled with every package since 2026-09-25 (`Extensions/store/` is already there); `hello` is a
development sample the developers hand you as an `Extensions/hello/` folder - it never ships. With the Store
bundled, 10.1 shows the Store in the list rather than "No extensions installed".

| # | Do | Expect |
|---|---|---|
| 10.1 | Without any extension: L2+R2 -> Extensions | "No extensions installed" and a line saying where they go. |
| 10.2 | Copy `Extensions/hello/` onto the stick and start the launcher | For a few seconds a "Hello - A background extension is running" bubble at the top right. |
| 10.3 | L2+R2 -> Extensions -> Hello -> Cross | A "Hello" dialog in the launcher's look. Confirm, and back in the carousel a "Confirmed in the extension" bubble for a few seconds. |
| 10.4 | Start a game with `hello` installed, play a minute, come back | The game runs as usual; back in the launcher nothing is missing (theme, sound, pads). |
| 10.5 | Copy `Extensions/store/`; turn WiFi off; L2+R2 -> Extensions | The Store's row is greyed: "Needs a network connection". Cross does nothing. |
| 10.6 | WiFi on: open the Store | The tabs Apps / Games / Downloads / Sources; the Sources tab lists "AutoBleem" with its item count. |
| 10.7 | Install an App; leave the Store while it downloads | The download goes on in a bubble in the carousel. When it is done, the App is in the Apps set and starts. |
| 10.8 | Start a large download, then start a game; come back | The download stopped for the game and continues where it was. |
| 10.9 | Power Off in the middle of a download; power on | The download continues after the start. |
| 10.10 | Put a `.tsv` source (from the Store's README) into `System/Extensions/store/sources/` | Its items appear under Games after Square (Refresh) or reopening the Store. |

**Logs:** `System/Logs/autobleem.log`; every extension line is tagged `[hello]` or `[store]`. The Store's own
files are in `System/Extensions/store/`.

---

## 11. Scanner processors - ready (nightly `v2.0.0-alpha2-149-g4edd7b0-n4ac996`, 2026-09-25)

**You need:** that nightly on a console, a Pi or the PC stick - Unzip comes with it
(`System/Processors/unzip/`). A zipped PS1 game (a `.cue` + `.bin` in a `.zip`) and a zipped ROM (one Mega
Drive or SNES ROM in a `.zip`).

| # | Do | Expect |
|---|---|---|
| 11.1 | Install fresh (or update) | `System/Processors/` (with `unzip/` in it) and `Extensions/` exist, each with a `README.txt`. |
| 11.2 | L2+R2 -> Scanner processors | Unzip on both tabs, switched on; only this machine's binary in `unzip/bin/`. |
| 11.3 | Drop the zipped game into `Games/` | Within a minute a scan starts on its own; the bubble shows "Unzip V1.x" with a bar; the game is on the shelf afterwards, in its own folder; the `.zip` is gone. |
| 11.4 | Drop the zipped ROM into its `RetroArch/roms/<system>/` folder | The ROM is unpacked next to where the zip was, the zip is gone, and the game is in its playlist. |
| 11.5 | Re-Scan Games with nothing new | No processor bubble; nothing on the stick changes. |
| 11.6 | Drop a large zipped game (several hundred MB), start a game while Unzip is working, play a minute, come back | Unzip stopped for the game; the next scan finishes it; no `*.part` file is left in the game's folder. |
| 11.7 | Power Off while Unzip is working; power on | The next scan finishes the game; no `*.part` left. |
| 11.8 | L2+R2 -> Scanner processors: Cross on Unzip, Circle; drop another zipped game | "Switched off": the zip stays zipped. Switch it on again and the next scan unpacks it. |
| 11.9 | The console only: how long 11.6's game takes, and is the launcher smooth meanwhile | Note the time and anything that stutters - this decides whether heavy processors need a "run on request" switch. |
| 11.10 | Switch Unzip off, then update AutoBleem (a newer nightly) | Unzip is still there and still switched off. |
| 11.11 | A nightly with Unzip V1.1.0 or later: drop a PS1 game packed as `.7z`, and one as `.rar` (a RAR set of volumes - `Game.part1.rar`, `Game.part2.rar`, ... - if you have one) into `Games/` | Both unpacked like the zip in 11.3, each in its own folder; the archives (every volume of a set) are gone. |
| 11.12 | The console only: a large solid `.7z` game (several hundred MB) | It unpacks without the launcher running out of memory; note the time next to 11.9's. |

**Logs:** `processors.log` in the logs folder (every run, with its output); `autobleem.log` for the scan.

---

## 12. The ported Apps (OpenTyrian, SDLPoP, Doom and Freedoom, Wolfenstein and Spear, Shadow Warrior, Duke Nukem 3D, OpenBOR, Amiberry) and the way out - ready from the next nightly (launcher `6e5b580`)

**You need:** a nightly with launcher `bf3bfa7` or later, and the package for your machine from
`github.com/autobleem2/app_opentyrian` -> Releases -> `nightly` (`opentyrian-<psc|rpi|rpi64|pcusb|win>-<v>.zip`) -
or from the Store (v2.1.20260913-1, all five catalogs). A pad; on Windows an Xbox-style (XInput) pad.

| # | Do | Expect |
|---|---|---|
| 12.1 | Unpack the zip over the stick's (or Windows' data folder's) root - it makes `Apps/opentyrian/` | Tyrian (OpenTyrian) in the Apps set, with its picture. On a stick that had the old RetroBoot OpenTyrian, the new one replaces it. |
| 12.2 | Start it | Full screen; the intro plays, then the title menu. No window, no black screen. |
| 12.3 | Play: D-pad/stick, Cross/Triangle, Square/Circle, L1/L2, R1/R2, Start, Select | Move; fire; rear weapon mode; left and right sidekicks; pause; menu - as in the App's readme. |
| 12.4 | Hold Start + Select (console, Pi, PC stick) | The game closes after about 1.5 s and the launcher comes back. |
| 12.5 | Save a game, leave, start it again, load it | The save is there (console/Pi/PC stick: `Home/.config/opentyrian/` on the stick; Windows: `%APPDATA%\OpenTyrian`). |
| 12.6 | The console only: sound, and does it run smoothly | Music and effects; note any slowdown. |
| 12.7 | Windows: the launcher's L2+R2 menu is fine afterwards; a `Startup=run.sh` App copied from a stick | That old-style App is **not** listed on Windows (it could not start there). |

**Prince of Persia (SDLPoP)** - the same way, from the Store (v1.24-RC-1, all five catalogs) or
`github.com/autobleem2/app_sdlpop` -> Releases:

| # | Do | Expect |
|---|---|---|
| 12.8 | Install it (the Store, or unpack over the root - `Apps/sdlpop/`) and start it | Full screen, 4:3 in the middle, no info screen; the intro, then the game. The old RetroBoot SDLPoP is replaced. |
| 12.9 | Play: D-pad/stick, Triangle, Cross, Square, Start, Select | Move; jump/climb; duck; step/grab/sword; Start and Select both open the pause menu. |
| 12.10 | Pause menu -> save; leave (hold Start + Select); start again; load | The save is there - in `Apps/sdlpop/` (`PRINCE.SAV`, `QUICKSAVE.SAV`). |
| 12.11 | Change a setting in the pause menu, update the App from the Store (when a newer one is there) | The setting and the saves survive the update (`SDLPoP.cfg` stays). |

**Doom (Shareware), Freedoom: Phase 1, Freedoom: Phase 2 (Crispy Doom)** - three Store items (v7.1-1, all five
catalogs) or `github.com/autobleem2/app_crispydoom` -> Releases:

| # | Do | Expect |
|---|---|---|
| 12.12 | Install all three and start each | Full screen, the game's title screen and demo; three icons from each game's title picture. The old RetroBoot Doom is replaced. |
| 12.13 | Play on the console's own pad: D-pad, Cross, Circle, Square, L1/R1, L2/R2, Start, Select | Move and turn; fire; use (doors); run; strafe; previous/next weapon; menu; automap. |
| 12.14 | The same on a dual-stick pad (a Pi, the PC stick, Windows): the left stick, the right stick | Left stick moves and turns, right stick strafes; on Windows the D-pad moves too. |
| 12.15 | Save a game, leave, start again, load | The save is in the App's `savegames/`. |

**Wolfenstein 3D (Shareware), Spear of Destiny (Demo) (Wolf4SDL)** - two Store items (v20260504-1, all five
catalogs) or `github.com/autobleem2/app_wolf4sdl` -> Releases:

| # | Do | Expect |
|---|---|---|
| 12.19 | Install both and start each | Full screen, the picture 4:3 and the full height of the screen (black bars at the sides), nothing cut off or stretched. The old RetroBoot Wolf4SDL is replaced. |
| 12.20 | Play on the console's own pad: D-pad, Cross, Circle, Square, Triangle, Select, L1/R1, L2, R2, Start | Move and turn; fire; run; open; next/previous weapon; strafe; pause; menu. The same on any other pad (the virtual pad shows it as the console's). |
| 12.21 | Windows, an Xbox-style pad: the D-pad, the buttons | The D-pad moves; Start opens the menu (the triggers do nothing there). |

**Shadow Warrior (Shareware) (JFSW)** - one Store item (v20260105-1, all five catalogs) or
`github.com/autobleem2/app_jfsw` -> Releases:

| # | Do | Expect |
|---|---|---|
| 12.22 | Install it and start it (on Windows too) | Straight into the game, full screen, 4:3 - no setup window, not even for a moment. The old RetroBoot Shadow Warrior is replaced. |
| 12.23 | Play on the console's own pad: D-pad, Square, Cross, Circle, Triangle, L1, R1, L2/R2, Select, Start | Move and turn; fire; crouch; open; jump; next item; next weapon; strafe; use item; menu (Start twice: the map). |
| 12.24 | The console: sound and music; does it run smoothly | Effects and music; note any slowdown (the software renderer at 640x480). |

**Duke Nukem 3D (Shareware) (JFDuke3D)** - one Store item (v20260105-1, all five catalogs; it replaces the old
EDuke32 App) or `github.com/autobleem2/app_jfduke3d` -> Releases:

| # | Do | Expect |
|---|---|---|
| 12.25 | Install it and start it (on Windows too) | Straight into the game, full screen, 4:3, no setup window. |
| 12.26 | Play on the console's own pad: D-pad, Cross, Circle, Triangle, Square (once, twice), L1 (once, twice), R1, L2/R2, Select, Start | Move and turn; fire; crouch; jump; open / kick; next item / use it; next weapon; strafe; map; menu. |
| 12.27 | Save, leave, start again, load | The save is in the App folder (`Apps/eduke32/`). |

**OpenBOR** - one Store item (v7533-1, all five catalogs; it replaces the old RetroBoot OpenBOR) or
`github.com/autobleem2/app_openbor` -> Releases. It comes without games: copy one or two `.pak` files you have
into `Apps/openbor/Paks` first.

| # | Do | Expect |
|---|---|---|
| 12.28 | Start it with the Paks folder empty (on Windows too) | Full screen: the OpenBOR logo with the AutoBleem mark, then the blue AutoBleem menu saying "No Mods In Paks Folder!". |
| 12.29 | Add a pak, start it again, pick it with the D-pad, Start | The game starts; music plays; a game with an intro video plays it (WebM). |
| 12.30 | Play on the console's own pad: D-pad, Cross, Circle, Square, Triangle, L1, R1, Start, Select, L2 | Move; attack 1-4; jump; special; start/pause; a screenshot in `ScreenShots/`; the menu. The same on any other pad; on Windows an Xbox-style pad the same way (L2 is the left trigger). |
| 12.31 | Change a setting, leave, start again | The setting kept (`Apps/openbor/Saves/`). |

**Amiberry** (the Amiga) - one Store item (v5.9.3-1, psc, rpi, rpi64, pcusb - there is no Windows one; it
replaces the old RetroBoot Amiberry) or `github.com/autobleem2/app_amiberry` -> Releases. Bring an `.adf` you
have; a real Kickstart (`kick13.rom`, `kick31.rom` into `Apps/amiberry/roms`) if you have one.

| # | Do | Expect |
|---|---|---|
| 12.32 | Start it | Full screen, Amiberry's menu (Quickstart); the About page shows the Amiberry logo with the AutoBleem logo and a credits line for the port. |
| 12.33 | With the pad only: choose A500, put an `.adf` from `floppies/` in DF0, start | The Amiga boots the disk (with AROS, or your Kickstart). Note the console's speed. |
| 12.34 | Play: D-pad, Cross, Circle, Square, Triangle, Start, Select | Joystick; fire; Return; Space; left mouse button; the joystick ports swapped; Select opens the menu. |
| 12.35 | A WHDLoad game (`.lha` in `lha/`, a real Kickstart in `roms/`): start it from the menu | It starts with no disk swapping. |
| 12.36 | Save a state, leave (Select -> Quit), start again, load it | The state is in `Apps/amiberry/savestates/`. |

**The way out, every App above** (launcher `6e5b580` or later):

| # | Do | Expect |
|---|---|---|
| 12.16 | The console: in each App, press **Reset** once | The App closes within about 1.5 s and the launcher comes back (`abpadd.log`: "Reset was pressed"). |
| 12.17 | The console: start the Terminal App, press Reset | It closes too (`abpadd --exit-only`). |
| 12.18 | Windows: leave each App through its menu, as its readme says | Back in the launcher. |

**Logs:** `autobleem.log`; on Linux `abpadd.log` (the virtual pad) in the logs folder.

## 13. The quiet stick - ready (nightly `v2.0.0-alpha2-149-g4edd7b0-n4ac996` or later)

Since 2026-09-24 AutoBleem writes to the stick only when your own state changes (a save, a memory card, a
resume slot you keep, a setting you change, a game added or removed); logs and hand-over files live in RAM.
It was measured on a Pi 400 and has **never run on a console**. Test it on the stock kernel and, if you
have it, the AutoBleem kernel.

**You need:** a console with the nightly, a PS1 game you can save in, a PC to look at the stick.

| # | Do | Expect |
|---|---|---|
| 13.1 | Boot to the carousel, wait a minute, Power Off (L2+R2), put the stick in the PC | Nothing under `Games/`, `System/Databases/` or `Themes/` has a new modified time. `System/Logs/` has no `autobleem.log`, `AB_out.txt` or `launch.log` (they are in RAM now). |
| 13.2 | Start a game in pcsx-abnxt (the default), save in-game to the memory card, leave through the emulator's menu -> Exit, **keep** the resume slot | The launcher shows the slot's picture. On the PC: the card in `Games/!SaveStates/<game>/` (or `Games/!MemCards/<set>/`) and the kept slot's state and picture have the new time. |
| 13.3 | Start the same game and pick that resume slot | The game continues exactly where you left it (this is the `AB_LOAD_STATE` path - never exercised anywhere). |
| 13.4 | Start the game again, leave through Exit, and this time do **not** keep the slot | Nothing under `Games/!SaveStates/<game>/sstates/` changed. |
| 13.5 | Repeat 13.2-13.3 with Options -> PS1 Emulator = pcsx-ab | The same results. |
| 13.6 | Start a RetroArch game, change a core option in RetroArch's menu, quit | Your change is kept next time. `RetroArch/bin/retroarch.cfg` still has AutoBleem's own settings (it was not overwritten with the launcher's temporary ones). |
| 13.7 | Options -> Diagnostics -> Keep logs on the stick; play a game; Power Off | `System/Logs/` now has `autobleem.log`, `launch.log`, `pcsx.log`. Turn it off again afterwards. |
| 13.8 | (For developers) `tools/stick_writes.sh start` before and `stop` after a boot + a game | The list of written files matches 13.1-13.4. |

**Logs:** with 13.7 on: `System/Logs/autobleem.log`, `launch.log`, `pcsx.log`; a crash leaves
`System/Logs/crash-<n>/`.

---

### Reporting

Send per item: pass/fail/blocked, the version, the logs named for it, and screenshots or photos of anything
unexpected. A failure is most useful with the steps that led to it and whether it happens again.
