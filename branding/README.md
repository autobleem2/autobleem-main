# AutoBleem branding

The one place for the look of AutoBleem: colours, type, logo, backgrounds and ready-made art. Use these files
instead of redrawing; if something is missing, add only the missing piece in the same style.

## Colours

| Role | Hex | Use |
|---|---|---|
| Graphite top | `#2e3742` | panels, tiles, buttons (gradient start) |
| Graphite bottom | `#212831` | the same gradient, end |
| Page dark | `#171b22` | flat dark backgrounds, avatars |
| Cyan | `#36d9e0` | lines, rims, headings, the logo bar |
| Magenta | `#ff46aa` | **only the focused / selected item** and the logo's "2" rim |
| Ink | `#f4f6f8` | text on dark |
| Dim | `#9aa4b2` | secondary text, "AUTO" in the logo |

Rule: cyan lines on graphite; magenta is kept for focus, so it stays rare and means something.

## Shape

The "v02b" look: every tile, panel and button has **two cut corners, top right and bottom left** (the shape of a
memory card). No lines, stripes or brushed metal; no all-cyan glow everywhere.

## Type

**Red Hat Text** (OFL, no reserved name): Medium 500 for text, SemiBold 600 for titles. Files and licence in
`fonts/`. The launcher's classic screens use Open Sans.

## Logo (C3)

"AUTO" in steel grey, "BLEEM" in white bold, and a **"2" in a cut-corner capsule with a magenta rim**; below it a
cyan bar fading to the right, ending in a short magenta bar under the capsule.

| File | What |
|---|---|
| `logo/logo-c3.png`, `@2x` | the logo, transparent background, for dark backgrounds |
| `logo/logo-c3-cyan.png` | the same with a cyan capsule rim (single-accent places) |
| `logo/logo.png`, `@2x`, `emblem*.png`, `icon.png` | the web-site copies |
| `avatar/ab2-logo-square-1000.png` | the full logo centred on a square dark canvas |
| `avatar/ab2-avatar-*.png` | "AB2" short mark (A steel, B white, the "2" capsule) for round avatars |

Use the logo on dark only; keep clear space of at least the capsule's height around it. Do not recolour the
capsule rim to anything but magenta (or the cyan variant), and do not use Sony marks anywhere.

## Backgrounds

- `background/mosaic-p5-1280x720.png`: the "p5 mozaika" background (cut-corner tiles, cyan glow top right, magenta
  glow bottom left) used by the ab2.0.0 theme.
- `background/background.jpg`, `og.png`: the web site's background and social image.

## Splash and boot

- `splash/launcher-splash.jpg`: launcher splash (logo + tagline "RETRO GAME LAUNCHER", right-aligned under the
  magenta end).
- `splash/retroarch-splash.jpg`: RetroArch loading splash (RetroArch is GPL; its icon may be used).
- `splash/plymouth-1080.png`: Linux appliance boot picture.

## Donation art

`donate/`: Ko-fi banner and avatar, GitHub Sponsors header, "Support AutoBleem" buttons (normal and hover, 1x and
@2x) and the README badge. Public wording: "development tools and infrastructure" only.

## Where it comes from

The generators and the full set of mockups are in the private design repository; this folder holds the finished,
approved pieces only. Change a piece there, then copy the result here.
