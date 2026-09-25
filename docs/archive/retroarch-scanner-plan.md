# Scanning RetroArch's ROMs from AutoBleem

Archived plan (done 2026-09-19). The full text is in git history: `git log -- docs/archive/retroarch-scanner-plan.md`.

Copy a ROM into `roms/<system>/` and the carousel updates - the same background scan that watches `Games/`
for PS1 games writes RetroArch's playlists. **RetroArch is optional everywhere**: nothing here runs unless
`Env::retroArchInstalled()` and the ROM folders exist. It works offline from the file names alone;
identification and box art switch on when their inputs exist, and "where things are / how to fetch" stays
data in `resources/platform/<platform>.ini`.

## The five steps and their key choices

1. **The offline scan** (`ableem::RetroArchScanner`, run by `ScanService`'s worker after the PS1 pass). One
   entry per game: a `.cue` hides its bins, an `.m3u` its discs, a `.ccd` its image. A `.zip` for a core
   that does not read archives itself (`zip` among its extensions; `block_extract` honoured in addition -
   no current `.info` sets it) is opened: one ROM = `zip#rom` named after the zip, **with the CRC from the
   central directory** (the same CRC RetroArch's scanner records), several = one entry each, none =
   skipped; an arcade core gets the zip whole; a `.7z` goes in whole. Label = the file's stem.
   `.info` parsing became `ableem::CoreInfoTable`; folder aliases (`roms_folders.cfg`: `Arcade/` ->
   the FBNeo playlist) let two folders share a playlist.
   **Merge rules**: keep every entry outside our ROM folder, keep an entry whose file is still there
   exactly (RetroArch's own label and CRC win), drop the vanished, add the new, sort by label; write
   `.tmp` + rename and only when something changed; never touch `AutoBleem.lpl`, Favorites or History;
   keep the playlist header (`RetroArchPlaylistHeader`) so RetroArch 1.22's version-1.5 files survive.
2. **Identification by `.rdb`**: a zip member or a loose file by CRC (`Crc32::ofFile`, capped at 64 MB so a
   CD image is never read), an **arcade set by `rom_name`** - not the archive's CRC, which a repacked set
   would miss. A hit sets the label to the record's name, and an identified entry replaces one for the
   same ROM whose label differs; a miss keeps the stem. CD systems are simply the size cap. Publisher, year
   and players for the meta panel come from the same rdb (`RetroArchService::ensureMetadata`).
3. **Box art**: offline through `ThumbnailLookup`; online through the platform's `download_command`
   (`OnlineAssets`, curl with its own timeout, `.part` + rename) when config.ini `online=true`, a command
   exists and one probe per cycle succeeds, only for games with no cover. Server misses are remembered in
   `Named_Boxarts/.autobleem-missing.txt`. The 40 MB `database-rdb.zip` is fetched when there is no `.rdb`.
4. **What the user sees**: the scan's progress and "Scan complete" with the ROM count. The Game Manager
   was left out on purpose (it manages PS1 folders).
5. **`UpdateRoms.exe`** - the console's online path, run from the stick on a PC: steps 1-3 with the PC's
   network, writing **the target's paths** (`RetroArchScanner::Options::targetRomsDir`, `/media/...` from
   `usb_root` in `psc.ini`/`rpi.ini`, never the PC's drive letter; a kept entry naming this machine's ROM
   folder is mapped too). The stick's kind is told by RetroBoot's folder vs the Pi installer's
   `retroarch.cfg` (`--target` overrides). A plain Win32 window, one ~540 KB file.

Since 2026-09-21 a rescan is cheap: a per-folder digest (`roms.scanstate`, no mtimes) skips unchanged
folders, and a loose ROM gets its CRC from its existing playlist entry.

## Lasting gotchas

- Never fight RetroArch over a playlist it also rewrites; write + rename; no scan while a launch runs.
- A ROM folder no `.info` or `cores.cfg` knows is skipped.
- `neogeo.zip` next to the arcade sets is listed as "Neo Geo" - it is an FBNeo record; the BIOS belongs in
  `system/`.
- Never read a CD image into memory on the 32-bit targets.

## Still open

- The launcher's own ROM scan (steps 1-3 over `/media/roms`) has never run on a console: the console has
  only read playlists `UpdateRoms.exe` wrote on the PC.
