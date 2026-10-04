"""ABleemStation stickers in real millimetres: the roof logo plate (61 x 17, fits the 62 x 18 recess), the front label strip
(43 x 4.6, POWER / RESET under the buttons), a side stripe (80 x 8) and the bottom rating plate (54 x 34), one per
board (Pi 3, Pi 4, Pi 5), each with a light box to write the serial number in by hand. Two colour sets: the ab2.0.0
one (dark, cyan / magenta) and the "Grey 94" special edition (light grey, dark text, four colour accents - colours
only, no third-party marks) in stickers/special/.
Writes stickers/*.svg, stickers/*.png (20 px/mm, also the viewer's decals), and the print sheet
stickers/ableemstation-stickers-A4.pdf (A4, 1:1, a cut line around each; 2 sets), and stickers/cricut-144dpi/
(one transparent PNG per sticker, 144 dpi, for a Cricut's Print Then Cut), all in ../files/stickers/.
Run:  python make_stickers.py"""
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "files", "stickers"))
WORK = os.path.join(HERE, "_stickers")
def find_chrome():
    """headless Chrome: $CHROME, else chrome / google-chrome on PATH, else the default Windows install"""
    for c in (os.environ.get("CHROME"), shutil.which("chrome"), shutil.which("google-chrome"),
              os.path.join(os.environ.get("ProgramFiles", ""), "Google", "Chrome", "Application", "chrome.exe")):
        if c and os.path.exists(c):
            return c
    raise SystemExit("Chrome not found - set CHROME to its path")


CHROME = find_chrome()
FONTS = os.path.join(HERE, "fonts")
RH = os.path.join(FONTS, "RedHatText-SemiBold.ttf")
os.makedirs(OUT, exist_ok=True)
os.makedirs(WORK, exist_ok=True)

# the colour sets: background gradient, accent, second accent, ink, muted ink, the S/N box, the side stripes, the tagline
PALETTES = {
    "": dict(G1="#2e3742", G2="#212831", CYAN="#36d9e0", MAG="#ff46aa", WHITE="#f0f8fa", STEEL="#96a4b2", BOX="#f0f8fa",
             STRIPES=("#36d9e0", "#ff46aa", "#96a4b2", "#36d9e0"), SUB="PERSONAL RETRO GAME SYSTEM"),
    "special": dict(G1="#dfddd8", G2="#c7c5bf", CYAN="#2f4f9e", MAG="#c8323c", WHITE="#2b2d31", STEEL="#6c6e73", BOX="#f8f7f3",
                    STRIPES=("#3aa776", "#d6453d", "#3f62b5", "#d27ab0"), SUB="SPECIAL EDITION · RETRO GAME SYSTEM"),
}
globals().update(PALETTES[""])
CSS = ('@font-face{font-family:OSB;src:url("file:///%s")}@font-face{font-family:OSM;src:url("file:///%s")}'
       '@font-face{font-family:RH;src:url("file:///%s")}') % (
    os.path.join(FONTS, "OpenSans-Bold.ttf").replace("\\", "/"), os.path.join(FONTS, "OpenSans-Medium.ttf").replace("\\", "/"),
    RH.replace("\\", "/"))
DEFS_T = ('<defs><linearGradient id="gr" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/>'
        '</linearGradient><linearGradient id="bar" x1="0" y1="0" x2="1" y2="0"><stop offset="0" stop-color="%s"/>'
        '<stop offset="1" stop-color="%s" stop-opacity="0"/></linearGradient></defs>')


def cut(w, h, c):
    return "M0 0H%s L%s %s V%s H%s L0 %s Z" % (w - c, w, c, h, c, h - c)


def svg(w, h, body):
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %s %s" width="%smm" height="%smm">%s%s</svg>'
            % (w, h, w, h, DEFS_T % (G1, G2, CYAN, CYAN), body))


def capsule(x, y, h, inner):
    w, c = h * 1.2, h * .3
    return ('<path d="M%s %s h%s l%s %s v%s h%s l%s %s z" fill="%s" stroke="%s" stroke-width="%s"/>%s'
            '<path d="M%s %s l%s %s h%s l%s %s z" fill="%s"/>') % (
        x, y, w - c, c, c, h - c, -(w - c), -c, -c, G2, MAG, h * .08, inner,
        x, y + h * 1.18, h * .08, -h * .08, w, -h * .08, h * .08, MAG)


def top():
    w, h = 61, 17
    play = '<path d="M%s %s l4.2 2.5 -4.2 2.5z" fill="%s"/>' % (6.6, 4.6, WHITE)
    return svg(w, h, (
        '<path d="%s" fill="url(#gr)"/><path d="%s" fill="none" stroke="%s" stroke-width=".35" transform="translate(.9 .9) scale(%s %s)"/>'
        % (cut(w, h, 3.2), cut(w, h, 3.2), CYAN, (w - 1.8) / w, (h - 1.8) / h))
        + capsule(3.6, 3.3, 7.6, play)
        + '<text x="16.5" y="9.6" font-family="OSB" font-size="6.6" fill="%s" textLength="40.5" lengthAdjust="spacingAndGlyphs">ABleem'
          '<tspan font-family="RH" fill="%s">Station</tspan></text>' % (WHITE, CYAN)
        + '<rect x="16.5" y="11.2" width="40" height=".55" fill="url(#bar)"/>'
        + '<text x="16.6" y="14.4" font-family="RH" font-size="2.0" fill="%s" textLength="39.6" lengthAdjust="spacing">%s</text>' % (STEEL, SUB))


def front():
    w, h = 43, 4.6
    lab = lambda x, t: ('<text x="%s" y="3.15" text-anchor="middle" font-family="RH" font-size="2.1" letter-spacing=".35" fill="%s">%s</text>'
                        % (x, WHITE, t))
    return svg(w, h, '<rect width="%s" height="%s" rx=".4" fill="%s"/>' % (w, h, G2)
               + '<rect x="0" y="0" width="%s" height=".35" fill="%s"/>' % (w, CYAN) + lab(13.5, "POWER") + lab(33.5, "RESET")
               + '<circle cx="22.5" cy="2.4" r=".45" fill="%s"/>' % MAG)


def side():
    w, h = 80, 8
    stripes = "".join('<path d="M%s 0 h%s l-6 %s h-%s z" fill="%s"/>' % (52 + i * 5.5, 3.2, h, 3.2, c)
                      for i, c in enumerate(STRIPES))
    return svg(w, h, '<path d="%s" fill="url(#gr)"/>' % cut(w, h, 2.2) + stripes
               + '<text x="4" y="5.4" font-family="OSB" font-size="3.6" fill="%s">ABleem<tspan font-family="RH" fill="%s">Station</tspan></text>'
               % (WHITE, CYAN))


# the rating plate per board: model, power, video (the board's own ports and its official supply)
BOARDS = {
    "": ("ABS-3 · Raspberry Pi 3 inside", "5 V DC  2.5 A  (micro-USB)", "HDMI · 720p / 1080p"),
    "-pi4": ("ABS-4 · Raspberry Pi 4 inside", "5 V DC  3 A  (USB-C)", "micro-HDMI · 720p / 1080p"),
    "-pi5": ("ABS-5 · Raspberry Pi 5 inside", "5 V DC  5 A  (USB-C, 27 W supply)", "micro-HDMI · 720p / 1080p"),
}
BW, BH = 54, 34


def bottom(model, power, video):
    w, h = BW, BH
    rows = [("MODEL", model), ("POWER", power), ("VIDEO", video), ("SOFTWARE", "AutoBleem")]
    t = "".join('<text x="4" y="%s" font-family="RH" font-size="2" fill="%s" letter-spacing=".3">%s</text>'
                '<text x="19" y="%s" font-family="OSM" font-size="2.2" fill="%s">%s</text>' % (13 + i * 3.6, STEEL, a, 13 + i * 3.6, WHITE, b)
                for i, (a, b) in enumerate(rows))
    # the serial number: a light box to write in with a permanent marker
    sn = ('<text x="4" y="29.2" font-family="RH" font-size="2" fill="%s" letter-spacing=".3">S/N</text>'
          '<rect x="12" y="26" width="38" height="4.4" rx=".6" fill="%s" stroke="%s" stroke-width=".25"/>') % (STEEL, BOX, CYAN)
    return svg(w, h, '<path d="%s" fill="url(#gr)"/>' % cut(w, h, 3)
               + '<text x="4" y="7.2" font-family="OSB" font-size="4.4" fill="%s">ABleem<tspan font-family="RH" fill="%s">Station</tspan></text>'
               % (WHITE, CYAN) + '<rect x="4" y="8.6" width="30" height=".45" fill="url(#bar)"/>' + t + sn
               + '<text x="12" y="32.6" font-family="RH" font-size="1.5" fill="%s">Power off before opening the case</text>' % STEEL)


def chrome(args, url):
    subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    "--virtual-time-budget=3000"] + args + [url], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


from PIL import Image  # noqa: E402


def build(OUT):
    """every sticker in the current colour set into OUT"""
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(WORK, exist_ok=True)
    ST = {"sticker-top": (top(), 61, 17), "sticker-front": (front(), 43, 4.6), "sticker-side": (side(), 80, 8)}
    for suffix, b in BOARDS.items():
        ST["sticker-bottom" + suffix] = (bottom(*b), BW, BH)
    PX = 20                     # px per mm for the PNGs
    for name, (s, w, h) in ST.items():
        open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8").write(s)
        page = os.path.join(WORK, name + ".html")
        big = s.replace('width="%smm" height="%smm"' % (w, h), 'width="%d" height="%d"' % (w * PX, h * PX))
        open(page, "w", encoding="utf-8").write('<!doctype html><style>%s*{margin:0}body{background:transparent}svg{display:block}</style>%s'
                                                % (CSS, big))
        chrome(["--force-device-scale-factor=1", "--window-size=%d,%d" % (round(w * PX), round(h * PX)),
                "--default-background-color=00000000", "--screenshot=" + os.path.join(OUT, name + ".png")],
               "file:///" + page.replace("\\", "/"))

    # Cricut (Print Then Cut, e.g. Joy Xtra + Design Space): one transparent PNG per sticker at 144 dpi with the dpi in the
    # file, scaled down from the 20 px/mm render (sharper than rendering small); one per sticker, Design Space repeats them
    CRICUT_DPI = 144
    cdir = os.path.join(OUT, "cricut-%ddpi" % CRICUT_DPI)
    os.makedirs(cdir, exist_ok=True)
    for name, (s, w, h) in ST.items():
        big = Image.open(os.path.join(OUT, name + ".png")).convert("RGBA")
        size = (round(w / 25.4 * CRICUT_DPI), round(h / 25.4 * CRICUT_DPI))
        big.resize(size, Image.LANCZOS).save(os.path.join(cdir, "ableemstation-%s.png" % name), dpi=(CRICUT_DPI, CRICUT_DPI))
        print("cricut: %s %dx%d px = %g x %g mm" % (name, size[0], size[1], w, h))

    # the A4 print sheet, 1:1: two sets, a hairline cut line 0.5 mm outside each sticker
    items, y = [], 18
    for _set in range(2):
        x = 15
        for name in ("sticker-top", "sticker-side", "sticker-bottom", "sticker-bottom-pi4", "sticker-bottom-pi5", "sticker-front"):
            s, w, h = ST[name]
            if x + w > 195:
                x, y = 15, y + 36
            items.append('<div style="position:absolute;left:%smm;top:%smm;width:%smm;height:%smm;outline:.1mm dashed #999;'
                         'outline-offset:.5mm">%s</div>' % (x, y, w, h, s))
            x += w + 8
        y += 40
    sheet = os.path.join(WORK, "sheet.html")
    open(sheet, "w", encoding="utf-8").write(
        '<!doctype html><style>%s@page{size:A4;margin:0}*{margin:0}body{width:210mm;height:297mm;position:relative;font:3mm sans-serif}'
        'svg{display:block}</style><div style="position:absolute;left:15mm;top:8mm;color:#555">ABleemStation stickers - print at 100%% '
        '(no "fit to page"), vinyl sticker sheet; cut on the dashed lines. Check: the top plate must measure 61 mm.</div>%s'
        % (CSS, "".join(items)))
    chrome(["--no-pdf-header-footer", "--print-to-pdf=" + os.path.join(OUT, "ableemstation-stickers-A4.pdf")], "file:///" + sheet.replace("\\", "/"))
    chrome(["--force-device-scale-factor=1", "--window-size=794,1123", "--screenshot=" + os.path.join(OUT, "ableemstation-stickers-A4-preview.png")],
           "file:///" + sheet.replace("\\", "/"))
    for f in os.listdir(WORK):
        os.remove(os.path.join(WORK, f))
    os.rmdir(WORK)
    print("written to", OUT)


for key, pal in PALETTES.items():
    globals().update(pal)
    build(os.path.join(OUT, key) if key else OUT)
