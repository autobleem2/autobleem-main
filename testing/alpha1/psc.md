# AutoBleem v2.0.0-alpha1 - test plan: PlayStation Classic

**How it works:** take **one section** (about 10 minutes), do its steps in order and tick what you saw:
**OK** (it did what *Expect* says), **Problem** (it did something else - write what you saw) or **N/A** (your
setup cannot do this step). Then report the section as a GitHub issue (below each section). A step that fails
the same way twice is worth more than a guess about why.

Report here: https://github.com/autobleem2/autobleem-main/issues - one issue per section.

## Before you start

- Get: AutoBleemInstaller-<version>.zip from the PlayStation Classic panel of the download page (autobleem.retromenele.pl). It holds only the installer and its README; AutoBleem is downloaded while it installs.
- You need: a PlayStation Classic, a Windows PC with internet, a USB 2.0 stick of 8 GB or more (its contents will be erased), a pad.
- For the Store and Network & Controllers sections: the AutoBleem kernel (ABFlashKit) and a USB Wi-Fi dongle set up in PSC-Bios. A stock console has no network.
- A PS1 game you legally own (a disc image of your own game). No game and no BIOS is shipped; the console uses its own BIOS.
- Do not touch the console's internal flash. Nothing in these tests needs it.
- Tick: Format the stick FAT32 (a fresh stick only), Cover databases; leave Sample games OFF for the welcome-card section; RetroArch ON only for the RetroArch section.

## Sections

| Section | What | Minutes |
|---|---|---|
| [psc-install](#psc-install) | Install with the Windows installer and first boot | 10 |
| [psc-firstrun](#psc-firstrun) | First run: the welcome card and adding a game | 8 |
| [psc-launcher](#psc-launcher) | The launcher: shelf, set picker, Quick menu, system menu | 10 |
| [psc-options](#psc-options) | Options and switching the language | 10 |
| [psc-game](#psc-game) | Games: start, the in-game menu, Reset and Exit | 10 |
| [psc-resume](#psc-resume) | Resume points and memory cards | 10 |
| [psc-manage](#psc-manage) | The game editor, Game Manager and Hardware Information | 8 |
| [psc-store](#psc-store) | The Store: browse, download (speed and time), network drop and resume | 10 |
| [psc-network](#psc-network) | Network & Controllers (PSC-Bios): Wi-Fi, Bluetooth, pad mapping | 10 |
| [psc-retroarch](#psc-retroarch) | RetroArch and Apps | 10 |
| [psc-power](#psc-power) | Power off, standby, LED and Reset | 10 |

## psc-install

**Install with the Windows installer and first boot** - about 10 minutes

**You need:** A Windows PC, a USB stick, a PlayStation Classic.

| # | Do | Expect | Result |
|---|---|---|---|
| 1 | Unzip AutoBleemInstaller-<version>.zip and run AutoBleemInstaller.exe with the stick plugged in. | A window with the Channel box and the drive box. Within a few seconds the line under them names the version the channel would install and what is on the stick now. | ☐ OK ☐ Problem ☐ N/A |
| 2 | Pick the channel named in the announcement (Testing or Nightly), pick the stick, tick Format the stick (FAT32) and Cover databases, leave Sample games and RetroArch off. | Choices are accepted. The Release channel says it has nothing to install while no stable release exists. | ☐ OK ☐ Problem ☐ N/A |
| 3 | Press Install and wait. | Progress bars and the log show every step (download, check, unpack). It ends with the stick named SONY and UpdateRoms\UpdateRoms.exe on it. Write the time it took. | ☐ OK ☐ Problem ☐ N/A |
| 4 | Eject the stick safely, plug it into the console's SECOND USB port (the right one) and switch the console on. | The light blinks for a few seconds and the console goes to standby with nothing shown (this is how AutoBleem is picked up). | ☐ OK ☐ Problem ☐ N/A |
| 5 | Press POWER once. | The AutoBleem picture, then the launcher. | ☐ OK ☐ Problem ☐ N/A |

**Report:** a GitHub issue titled `alpha1 psc psc-install` with your device, the version (L2 + R2 -> About) and one line per step, e.g. `1 OK`, `2 Problem: the screen stayed black`, `3 N/A`.

## psc-firstrun

**First run: the welcome card and adding a game** - about 8 minutes

**You need:** A fresh AutoBleem install with an EMPTY Games folder (no sample games) and one legally owned PS1 game.

| # | Do | Expect | Result |
|---|---|---|---|
| 1 | Start the launcher on an install whose Games folder is empty. | Instead of an empty shelf a welcome card: 'Hi, and welcome to AutoBleem!' - drop games into Games and press Re-scan games - and it names the place for your platform: on your stick. | ☐ OK ☐ Problem ☐ N/A |
| 2 | Put one legally owned PS1 game (a .cue + .bin, or a .chd) into its own folder under Games/ - on your stick. On the console switch off with Power off first and pull the stick only while the light is red; put the card / stick back afterwards. | The files copy; the game's folder name is the game's name. | ☐ OK ☐ Problem ☐ N/A |
| 3 | Quick menu (Up) -> Re-scan games. | A scan runs with a progress bubble at the top right; the game appears on the shelf as it is found and the welcome card goes away. Details show publisher, year, players when the databases know the game. | ☐ OK ☐ Problem ☐ N/A |
| 4 | Watch the game's cover. | A cover appears (from the cover databases, or fetched online on a Pi / PC / Windows). Note if a game gets no cover. | ☐ OK ☐ Problem ☐ N/A |

**Report:** a GitHub issue titled `alpha1 psc psc-firstrun` with your device, the version (L2 + R2 -> About) and one line per step, e.g. `1 OK`, `2 Problem: the screen stayed black`, `3 N/A`.

## psc-launcher

**The launcher: shelf, set picker, Quick menu, system menu** - about 10 minutes

**You need:** AutoBleem installed with at least one game on the shelf.

| # | Do | Expect | Result |
|---|---|---|---|
| 1 | Start the launcher and look at the shelf (with at least one game on it). | The covers of the current set, the selected one in the middle with a soft reflection under it, its details beside it as a compact grid (a fact the game does not have is left out) and a Play button. The look is the ab2.0.0 theme. | ☐ OK ☐ Problem ☐ N/A |
| 2 | Look at the top-left corner, under the pad battery plate (if no pad shows a battery, just the corner). | A small chip with the channel (ALPHA, or RC / TESTING / NIGHTLY for other builds) and the short version beside it. Write the exact text in the comment. | ☐ OK ☐ Problem ☐ N/A |
| 3 | Look at the hint bar at the bottom. | Two lines of four slots. Line 1 is what the buttons do for the selected game (play, the icon row, the Quick menu). Line 2 is Select, Start, Triangle and L2 + R2, dimmed when one does nothing. | ☐ OK ☐ Problem ☐ N/A |
| 4 | Press Select, then (still in the picker) move Up / Down and press L1 / R1 to see the tabs. | The PlayStation tab lists All games and Internal games (the console's built-in twenty), then USB games, then Favorite games and Game history. Each row shows a count. The footer names the keys (L1 / R1 tabs, L2 / R2 page, Cross picks, Circle Back). L1 / R1 switch the PlayStation / RetroArch / Apps tabs (RetroArch only if it is installed). | ☐ OK ☐ Problem ☐ N/A |
| 5 | In the picker choose USB games with Cross. | Back on the shelf with the whole library. A bubble at the top right says Showing: USB games for a few seconds. | ☐ OK ☐ Problem ☐ N/A |
| 6 | Press Up on the shelf (the Quick menu). | The Quick menu opens with: Re-scan games, Store, Network & Controllers, Restart launcher and System menu..., each with a one-line description. Up / Down wrap around; Circle closes it. | ☐ OK ☐ Problem ☐ N/A |
| 7 | Press L2 + R2 (the system menu). | The menu opens, grouped: at the top Re-scan games and Extensions; Library (Game Manager, Memory Cards, Scanner processors); System (Options, Network & Controllers where the platform has it, Hardware Information, Software Update on a Pi/PC/Windows, About); Leave (RetroArch only if installed, Power off). Names in sentence case, each row with a description. | ☐ OK ☐ Problem ☐ N/A |
| 8 | Press Circle, then Triangle (the button guide). | One page lists every button of every screen. With a USB keyboard connected a Keyboard column shows the keys too. | ☐ OK ☐ Problem ☐ N/A |

**Report:** a GitHub issue titled `alpha1 psc psc-launcher` with your device, the version (L2 + R2 -> About) and one line per step, e.g. `1 OK`, `2 Problem: the screen stayed black`, `3 N/A`.

## psc-options

**Options and switching the language** - about 10 minutes

**You need:** AutoBleem installed and started.

| # | Do | Expect | Result |
|---|---|---|---|
| 1 | L2 + R2 -> Options. Scroll through the whole list. | Rows are grouped under headings: Interface, Fonts, Sound, Emulation, Library, Updates, Diagnostics. On/off values read ON / OFF. Rows for RetroArch appear only if RetroArch is installed. | ☐ OK ☐ Problem ☐ N/A |
| 2 | Options -> Interface -> Language: choose Polski (or any language you read), then Circle out to the shelf and open L2 + R2. | The menus are translated at once, with no restart. Open the system menu, the Quick menu and Options once and check nothing stays in English or is cut off. Switch back to English afterwards. | ☐ OK ☐ Problem ☐ N/A |
| 3 | Options -> Interface -> Display: pick another resolution (look at the list first). The console offers 720p and 1080p. | Where the row exists (it is not shown in a development window) the new mode is applied and the question 'Keep this display mode?' appears with a countdown. Do not confirm: the old mode comes back by itself. Repeat and confirm: the new mode stays. | ☐ OK ☐ Problem ☐ N/A |
| 4 | Options -> Interface -> Notification timeout: set 0, then switch the set with Select (any other group). | The value reads Off at 0 and the 'Showing: ...' bubble no longer appears. Set it back to a few seconds and the bubble returns. | ☐ OK ☐ Problem ☐ N/A |
| 5 | Options -> Interface -> Animations OFF, move through two or three screens, then ON again. Also try Cover shine ON / OFF. | With animations off every screen change is instant; on, they slide. Cover shine ON shows a shine crossing the selected cover when the shelf comes to rest. | ☐ OK ☐ Problem ☐ N/A |
| 6 | Options -> Interface -> Emulator screen scaling: look at the choices (1x1, 2x (integer), 4:3, 4:3 (integer), Full screen) and pick 4:3. | Every value is accepted and shown. (The picture in a game is checked in the games section.) | ☐ OK ☐ Problem ☐ N/A |
| 7 | Options -> Emulation -> PS1 emulator, and Options -> Updates. | PS1 emulator offers pcsx-abnxt (the default) and pcsx-ab. Updates offers release, testing, nightly and off (not shown on a development host); the default follows the installed version. Leave both as you found them. | ☐ OK ☐ Problem ☐ N/A |

**Report:** a GitHub issue titled `alpha1 psc psc-options` with your device, the version (L2 + R2 -> About) and one line per step, e.g. `1 OK`, `2 Problem: the screen stayed black`, `3 N/A`.

## psc-game

**Games: start, the in-game menu, Reset and Exit** - about 10 minutes

**You need:** AutoBleem on the shelf with one legally owned PS1 game (a .cue + .bin or a .chd in its own folder under Games/). No BIOS is shipped (the console uses its own).

| # | Do | Expect | Result |
|---|---|---|---|
| 1 | Select a PS1 game and press Cross. | The game starts full screen in pcsx-abnxt (the default emulator) with sound and picture, with no black screen. | ☐ OK ☐ Problem ☐ N/A |
| 2 | In the game: Press Select + Start on the pad (or the pad's Home button if it has one). | The game stops behind the emulator's menu, drawn in the launcher's look, over the game's last picture. It has three tabs Game / Picture / Controllers (L1 / R1 switch them). Close it with the same button and the game goes on. | ☐ OK ☐ Problem ☐ N/A |
| 3 | Open the menu, go to Game -> Saves -> Quick save, play a little, then Quick load. | The game returns to the saved moment. Game -> Saves -> Load autosave also works (the game as it was up to 30 seconds ago). | ☐ OK ☐ Problem ☐ N/A |
| 4 | Open the menu, Picture tab: change Scanlines or Filter, and look at the Scaling row. | The picture changes at once. Each row has a help line on the right; a row that does not apply is greyed with the reason in its help line. The Scaling choice from Options -> Emulator screen scaling is respected. | ☐ OK ☐ Problem ☐ N/A |
| 5 | Menu -> Game tab -> CD disc -> Reset game. | The menu closes, the emulator shows 'Please wait...' for a moment, and the game starts again from its beginning. | ☐ OK ☐ Problem ☐ N/A |
| 6 | Menu -> Game tab -> Exit. | The menu closes, 'Please wait...' is shown while the resume point is written, then the launcher comes back with your game selected. | ☐ OK ☐ Problem ☐ N/A |
| 7 | Start the game again; hold the menu button for 2 seconds. | The game is left exactly as with Reset: 'Please wait...', then the launcher. | ☐ OK ☐ Problem ☐ N/A |
| 8 | Open the in-game menu again, then press the console's RESET button on the front. | The menu closes, the emulator shows 'Please wait...' while the resume point is written, and the launcher comes back. | ☐ OK ☐ Problem ☐ N/A |
| 9 | Menu -> Controllers tab, then Game tab -> PCSX menu, then back. | Controller 1 and 2 offer standard (digital), analog (DualShock), a gun or none; the PCSX menu opens PCSX-ReARMed's own pages (options, cheats, About) and returns to the menu. | ☐ OK ☐ Problem ☐ N/A |

**Report:** a GitHub issue titled `alpha1 psc psc-game` with your device, the version (L2 + R2 -> About) and one line per step, e.g. `1 OK`, `2 Problem: the screen stayed black`, `3 N/A`.

## psc-resume

**Resume points and memory cards** - about 10 minutes

**You need:** AutoBleem with a PS1 game you can save in.

| # | Do | Expect | Result |
|---|---|---|---|
| 1 | On the shelf pick a game that has never been played and press Down. | The icon row opens under the game: Settings, Game, Memory Card, Resume. The Resume icon is greyed out because there is no resume point. | ☐ OK ☐ Problem ☐ N/A |
| 2 | Start the game, save in the game to its memory card, then press the console's RESET button. | 'Please wait...' appears while the resume point is written, then the launcher. The game's Resume icon now shows a small picture. | ☐ OK ☐ Problem ☐ N/A |
| 3 | Down -> Resume. | Four framed cards, each with a picture of the moment, its slot number and date. The newest has a NEWEST chip; an unused slot says 'No resume point'. | ☐ OK ☐ Problem ☐ N/A |
| 4 | Cross on the NEWEST card. | The game continues exactly where you left it, with the saved game on its memory card intact. | ☐ OK ☐ Problem ☐ N/A |
| 5 | Leave again, then Down -> Resume -> Triangle on a card. | The card is deleted; its slot says 'No resume point'. Circle back. | ☐ OK ☐ Problem ☐ N/A |
| 6 | Down -> Memory Card (the game's memory card editor). | The game's card and a second card side by side, with every save's icon and title. Square copies a save, Triangle deletes one, Select defragments, Start swaps the right-hand card for another set. Try the copy on a throw-away save only. | ☐ OK ☐ Problem ☐ N/A |
| 7 | L2 + R2 -> Memory Cards -> Square: create a set named Test with the on-screen keyboard; then rename it (Cross) and delete it (Triangle). | The on-screen keyboard (letters, symbols, accents; Shift, Space, Backspace, Confirm) types the name; the set appears, is renamed and is deleted after the confirmation. | ☐ OK ☐ Problem ☐ N/A |

**Report:** a GitHub issue titled `alpha1 psc psc-resume` with your device, the version (L2 + R2 -> About) and one line per step, e.g. `1 OK`, `2 Problem: the screen stayed black`, `3 N/A`.

## psc-manage

**The game editor, Game Manager and Hardware Information** - about 8 minutes

**You need:** AutoBleem with a game on the shelf.

| # | Do | Expect | Result |
|---|---|---|---|
| 1 | On the shelf pick a game, press Down, then Cross on Game (the game editor). | The details on the right (title, publisher, year, players, folder, memory card) and the settings on the left in four groups: Game, Display, Rendering, Emulator. Display has Resolution, Remove seams, Dithering, Smoothing, Filter, Scanlines, Scanline brightness. | ☐ OK ☐ Problem ☐ N/A |
| 2 | Change one Display value (for example Scanlines), press Circle, and start the game. | The setting is kept and used in the game. Triangle renames the game, Square changes its memory card; Circle saves and leaves. | ☐ OK ☐ Problem ☐ N/A |
| 3 | Open the game's in-game menu -> Game -> Save settings for this game, leave, and open the game editor again. | Display, Rendering and Emulator rows are greyed under the heading 'Saved in the emulator'. 'Unlock the settings' (confirm) makes them editable again. | ☐ OK ☐ Problem ☐ N/A |
| 4 | L2 + R2 -> Game Manager. | The games as a list of titles only; the selected game's folder is in its details, its cover beside it; free space at top right. Do NOT delete a game you want to keep (Square deletes). | ☐ OK ☐ Problem ☐ N/A |
| 5 | L2 + R2 -> Hardware Information. | One page: system, CPU, storage with free space, network addresses, display and audio, the connected pads (the first two as Player 1 and Player 2). The page refreshes every second. It does not open PSC-Bios. | ☐ OK ☐ Problem ☐ N/A |
| 6 | L2 + R2 -> Extensions. | The list of installed extensions (the AutoBleem Store, PSC-Bios). Cross runs one, Triangle turns it off / on. | ☐ OK ☐ Problem ☐ N/A |

**Report:** a GitHub issue titled `alpha1 psc psc-manage` with your device, the version (L2 + R2 -> About) and one line per step, e.g. `1 OK`, `2 Problem: the screen stayed black`, `3 N/A`.

## psc-store

**The Store: browse, download (speed and time), network drop and resume** - about 10 minutes

**You need:** A console with the AutoBleem kernel and Wi-Fi set up in PSC-Bios (the stock console has no network and no Store), a few hundred MB free on the stick.

| # | Do | Expect | Result |
|---|---|---|---|
| 1 | Quick menu (Up) -> Store. | The Store opens with four tabs: Apps, Games, Downloads, Sources (L1 / R1 move between them). Sources lists AutoBleem's own catalog. | ☐ OK ☐ Problem ☐ N/A |
| 2 | Apps tab, then Games tab: browse. | Each item shows a picture, version, size and a source favicon. Installed items carry an 'Installed' badge. L2 / R2 jump by letter, Square refreshes, Start searches the titles, Select shows one source at a time. The footer shows the keys of the selected row. | ☐ OK ☐ Problem ☐ N/A |
| 3 | Pick an item of at least a few tens of MB that is not installed yet and press Cross, then open the Downloads tab. | The item is queued and downloads; the progress bar moves steadily. | ☐ OK ☐ Problem ☐ N/A |
| 4 | Leave the Store with Circle (back to the shelf) while it downloads. | A bubble at the top right shows the running download with its speed and time left, in the form `1.4 MB/s · 0:42`. It goes on downloading in the background. | ☐ OK ☐ Problem ☐ N/A |
| 5 | Pull the USB Wi-Fi dongle (or switch the router's Wi-Fi off) for about 30 seconds. | The item says 'Waiting for the network'. The launcher does not crash or hang. | ☐ OK ☐ Problem ☐ N/A |
| 6 | Plug the dongle in again (or switch Wi-Fi back on). Look at the progress. | The download carries on from where it stopped (the progress does not go back to 0) and finishes. Write the percentage before and after in the comment. | ☐ OK ☐ Problem ☐ N/A |
| 7 | When it is done: open the item in the Store, then the Apps set (Select) or Re-scan games for a game. | The item shows 'Installed'; an App is in the Apps set and starts after its read-me (Circle goes back); a game appears on the shelf after the scan with the Store's picture as its cover. | ☐ OK ☐ Problem ☐ N/A |
| 8 | Start another download and press Cross on it while it runs; then Triangle on an item the Store installed. | Cross cancels the queued or running download. Triangle removes the item the Store installed (after its question). | ☐ OK ☐ Problem ☐ N/A |

**Report:** a GitHub issue titled `alpha1 psc psc-store` with your device, the version (L2 + R2 -> About) and one line per step, e.g. `1 OK`, `2 Problem: the screen stayed black`, `3 N/A`.

## psc-network

**Network & Controllers (PSC-Bios): Wi-Fi, Bluetooth, pad mapping** - about 10 minutes

**You need:** AutoBleem installed with the AutoBleem kernel (Wi-Fi and Bluetooth need it); a pad; a USB keyboard helps. A Bluetooth pad is optional.

| # | Do | Expect | Result |
|---|---|---|---|
| 1 | Quick menu (Up) -> Network & Controllers. | PSC-Bios opens, titled Network & Controllers: time and time zone, the Wi-Fi / Ethernet / Bluetooth adapters with their addresses, and every connected controller with whether it has a button mapping. | ☐ OK ☐ Problem ☐ N/A |
| 2 | Select (Wi-Fi Network). | The network name can be typed (on-screen keyboard) or picked from a scan; password, 'Apply / Restart Network'; the time zone is set here. Once connected the IP address is shown. Circle goes back without changing anything if you are already online. | ☐ OK ☐ Problem ☐ N/A |
| 3 | Square (Bluetooth Controllers). | A scan for Bluetooth gamepads starts; paired pads can be paired or removed. With no Bluetooth pad, just check it scans and returns. | ☐ OK ☐ Problem ☐ N/A |
| 4 | Press R1 (Controller Mapping), try RESET, then leave with Circle held 2 seconds (or POWER). | Controller Mapping (R1): the wizard shows the pad raw (axes, buttons, hat) and a DualShock picture that lights up. It is driven by the console's front buttons: RESET switches to the next pad, OPEN starts the mapping, POWER cancels / leaves. Holding Circle on the pad for 2 seconds also leaves (a bar fills, the hint says 'Hold 2 s: Exit'). Do not save a mapping unless asked. | ☐ OK ☐ Problem ☐ N/A |
| 5 | Triangle (About), then Circle back to the launcher. | About opens and closes; Circle returns to the launcher with the shelf intact. | ☐ OK ☐ Problem ☐ N/A |
| 6 | L2 + R2 -> Extensions -> PSC-Bios -> Triangle (turn it off), then Circle and open the Quick menu. | Network & Controllers is greyed with the note 'enable it in Extensions'; Cross on it opens the Extensions list at PSC-Bios. Triangle again turns it back on and the item works. Leave it ON at the end. | ☐ OK ☐ Problem ☐ N/A |

**Report:** a GitHub issue titled `alpha1 psc psc-network` with your device, the version (L2 + R2 -> About) and one line per step, e.g. `1 OK`, `2 Problem: the screen stayed black`, `3 N/A`.

## psc-retroarch

**RetroArch and Apps** - about 10 minutes

**You need:** AutoBleem with RetroArch installed (the tick in the installer / the answer yes on first boot), a legally owned ROM, and an App from the Store.

| # | Do | Expect | Result |
|---|---|---|---|
| 1 | Press Select and look at the tabs (L1 / R1). | A RetroArch tab (one group per system with games, plus RetroArch's Favorites and History) and an Apps tab (All apps, then Games, Emulators, Tools, Media, Other). Without RetroArch installed there is no RetroArch tab - write that in the comment. | ☐ OK ☐ Problem ☐ N/A |
| 2 | Put one legally owned ROM into RetroArch/roms/<system folder>/ (for example 'Sega - Mega Drive - Genesis'), run UpdateRoms.exe from the stick on a PC, then Re-scan games and start it with Cross. | The game shows on the RetroArch tab, starts in its core with picture and sound, and 'Close Content' / 'Quit RetroArch' in RetroArch's menu comes back to the launcher. | ☐ OK ☐ Problem ☐ N/A |
| 3 | On a PS1 game press Square. | The game starts in RetroArch's PS1 core instead of the PS1 emulator; leaving returns to the launcher. | ☐ OK ☐ Problem ☐ N/A |
| 4 | L2 + R2 -> RetroArch (in the Leave group). | RetroArch's own menu opens with nothing loaded; Quit RetroArch returns to the launcher. | ☐ OK ☐ Problem ☐ N/A |
| 5 | Apps set: pick an App (one from the Store, for example) and press Cross. | Its read-me shows first (Circle goes back); Cross starts it full screen with no window or black screen. | ☐ OK ☐ Problem ☐ N/A |
| 6 | In the App: Hold Start + Select for about 1.5 seconds. | The App closes and the launcher comes back (on the console the front RESET button also closes it within about 1.5 seconds). | ☐ OK ☐ Problem ☐ N/A |
| 7 | On an install made WITHOUT RetroArch (if you have one): look at the Select picker and the L2 + R2 menu. | No RetroArch tab, no RetroArch row, no RetroArch options. Mark N/A if RetroArch is installed. | ☐ OK ☐ Problem ☐ N/A |

**Report:** a GitHub issue titled `alpha1 psc psc-retroarch` with your device, the version (L2 + R2 -> About) and one line per step, e.g. `1 OK`, `2 Problem: the screen stayed black`, `3 N/A`.

## psc-power

**Power off, standby, LED and Reset** - about 10 minutes

**You need:** A console with the AutoBleem stick and a PS1 game; the console's power cable within reach.

| # | Do | Expect | Result |
|---|---|---|---|
| 1 | L2 + R2 -> Power off -> confirm. | After a few seconds only the red LED is on (AutoBleem's standby). Write the time it took in the comment. | ☐ OK ☐ Problem ☐ N/A |
| 2 | While the light is red, pull the stick, look at it in a PC (optional), put it back, then press the console's POWER button. | Windows does not ask to check or repair the stick. After POWER the LED goes green together with the console waking (it does not stay red), the AutoBleem picture shows and the launcher is back within about 15 seconds. | ☐ OK ☐ Problem ☐ N/A |
| 3 | On the shelf press the console's POWER button. | The same standby as with the menu: red LED, stick disconnected; POWER brings the launcher back. | ☐ OK ☐ Problem ☐ N/A |
| 4 | Quick menu (Up) -> Restart launcher. | The launcher closes and starts again (the picture, then the shelf), settings unchanged. | ☐ OK ☐ Problem ☐ N/A |
| 5 | Pull the console's power cable, plug it in and press POWER. | The boot standby again: the light blinks a few seconds and the console goes to standby with nothing shown; one press of POWER brings the launcher. | ☐ OK ☐ Problem ☐ N/A |
| 6 | Play a game, then press the front RESET button. | 'Please wait...' then the launcher; the game has a resume point. | ☐ OK ☐ Problem ☐ N/A |

**Report:** a GitHub issue titled `alpha1 psc psc-power` with your device, the version (L2 + R2 -> About) and one line per step, e.g. `1 OK`, `2 Problem: the screen stayed black`, `3 N/A`.
