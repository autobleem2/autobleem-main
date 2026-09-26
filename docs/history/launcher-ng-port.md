# The AutoBleem-NG port, UPX and Chinese (Simplified)

Moved verbatim out of the launcher's CLAUDE.md on 2026-09-26 (task D19).

**AutoBleem-NG port** (2026-09-18, plan in `~/.claude/plans/there-is-a-project-tingly-pixel.md`): the public
fork `github.com/AutoBleem-NG/autobleem` is 122 commits past the snapshot this repo started from (its
`924a02cb`, 2021-03-14, is byte-identical to our `src/code`). Done so far, one commit each: the Phase 0 bug
fixes (`play_us_ra` typo, locked games keeping their serial, CHD exported as `.chd.cue`, the `.m3u`
generator, the year on the meta panel, the per-size bold font cache `Fonts::boldAtSize`, translation
wrappers + sorted languages, music not restarting on theme browse, Favorites fallback, rc guards, the
stock-SonyUI/`.lic`/RetroBoot-patch cleanup), the libchdr refresh, and Phase 1 - `RdbReader`,
`MetadataLookup`, `ThumbnailLookup` (see lib_ableem/engine below), verified on the Pi 400 with the
libretro box arts mirrored by `payload_linux/install.sh --thumbnails`; Phase 2, the multi-disc folder merge
(`DiscSuffix`, `mergeMultiDiscFolders`); pcsx-ab's libchdr refresh (its own repo); `core/version.h` + the
`make_psc.sh` link gates; Phase 3, lightgun games (`LightgunService`, `GameSet::Lightgun`, the editors);
plog (`<ableem/engine/log.h>`); the Key=Value language files + `tools/lang_tools.py`; fitted/wrapped/elided
text in `TextRenderer` with the Game Manager's preview pane and the launcher's `launcher.snapPanel`; and
`docs/menu-options.md` + `docs/translation.md`. **The port is complete** apart from what was left out on
purpose: the fork's Docker/CI pipeline, gtest (doctest does the job) and the RetroBoot-1.2.1 Apps payload.
**UPX** is in (2026-09-18): `make_psc.sh` packs the fetched console binary and `tools/make_rpi_package.sh` the
Pi one (`upx --best --lzma`, 3.1 MB -> 1 MB, MSYS2's `mingw-w64-ucrt-x86_64-upx`; `AB_NO_UPX=1` skips, and a
debug build is never packed - gdb cannot read a packed binary). The packed Pi binary was run on the Pi 400.
Its Options paging and "Font" rows came over on 2026-09-18 (`GuiOptions::render` spreads the rows over the
panel and pages by what fits at the font's height; `themefont`/`font` in config.ini, `Fonts::userFontPath`
picks the classic font from `retroarch/fonts`, `resources/fonts` or the theme folder). Its clang-format/clang-tidy setup came over afterwards (see "Code style" under
Build).

**Chinese (Simplified)** (2026-09-18): `resources/lang/Chinese_Simplified.txt` (the fork's file, completed for
our keys) plus a CJK font the fork never shipped - `resources/fonts/NotoSansSC-Regular.otf` (8 MB, Noto CJK
SC subset, SIL OFL; `OFL.txt` next to it). `Fonts::cjkFontFor(language)` names it for a language whose name
contains "Chinese" (and it exists), and `ThemeAssets::load()` then uses it as *every* font - the theme's
classic font and the launcher's medium/bold pair - because no theme font has the glyphs. A language change
in Options calls `gui->loadAssets(false)` so the swap happens live, both ways. Themes are untouched.
