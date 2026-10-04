"""ABleemStation wiring diagram: the POWER and RESET buttons and the front LED on a Raspberry Pi 3B / 3B+, plus the parts
to buy. Writes ../files/wiring.svg and ../files/wiring.png (headless Chrome, the fonts from fonts/).
POWER: GPIO3 (pin 5) + GND (pin 9) - shuts down with dtoverlay=gpio-shutdown and wakes the Pi from halt.
LED:   GPIO14/TXD (pin 8) -> resistor -> LED -> GND (pin 6) - lit while the Pi runs, with enable_uart=1.
RESET: the two RUN pads on the board (a 2-pin header soldered in). Run:  python make_wiring.py"""
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "files"))
FONTS = os.path.join(HERE, "fonts")


def find_chrome():
    """headless Chrome: $CHROME, else chrome / google-chrome on PATH, else the default Windows install"""
    for c in (os.environ.get("CHROME"), shutil.which("chrome"), shutil.which("google-chrome"),
              os.path.join(os.environ.get("ProgramFiles", ""), "Google", "Chrome", "Application", "chrome.exe")):
        if c and os.path.exists(c):
            return c
    raise SystemExit("Chrome not found - set CHROME to its path")


BG, PANEL, LINE, INK, DIM = "#161b21", "#1f262e", "#33404c", "#eef3f6", "#93a3b3"
CYAN, MAG, YEL, GND = "#36d9e0", "#ff46aa", "#f2c94c", "#8a96a3"
W, H = 1500, 1060
NAMES = {1: "3V3", 2: "5V", 3: "GPIO2 SDA", 4: "5V", 5: "GPIO3 SCL", 6: "GND", 7: "GPIO4", 8: "GPIO14 TXD", 9: "GND",
         10: "GPIO15 RXD", 11: "GPIO17", 12: "GPIO18", 13: "GPIO27", 14: "GND", 15: "GPIO22", 16: "GPIO23", 17: "3V3",
         18: "GPIO24", 19: "GPIO10", 20: "GND"}
USED = {5: YEL, 9: GND, 8: CYAN, 6: GND}
X_ODD, X_EVEN, Y0, DY = 690, 750, 200, 42


def pin_xy(n):
    return (X_ODD if n % 2 else X_EVEN), Y0 + ((n - 1) // 2) * DY


def text(x, y, t, size=15, fill=INK, anchor="start", weight=500, family="RH"):
    return ('<text x="%s" y="%s" font-family="%s, sans-serif" font-size="%s" font-weight="%s" fill="%s" text-anchor="%s">%s</text>'
            % (x, y, family, size, weight, fill, anchor, t))


def wire(points, color, w=4):
    return '<polyline points="%s" fill="none" stroke="%s" stroke-width="%s" stroke-linejoin="round" stroke-linecap="round"/>' % (
        " ".join("%s,%s" % p for p in points), color, w)


def switch(x, y, label, color):
    """a push button between (x, y) and (x + 80, y): two contacts and a plunger bar above them"""
    return ('<circle cx="%s" cy="%s" r="5" fill="%s"/><circle cx="%s" cy="%s" r="5" fill="%s"/>'
            '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="4" stroke-linecap="round"/>'
            '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="4" stroke-linecap="round"/>'
            '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="3"/>') % (
        x, y, INK, x + 80, y, INK, x - 4, y - 18, x + 84, y - 18, color, x + 40, y - 18, x + 40, y - 34, color,
        x + 28, y - 34, x + 52, y - 34, color) + text(x + 40, y + 30, label, 16, INK, "middle", 600)


def resistor(x, y, label):
    pts = [(x, y)] + [(x + 10 + i * 10, y + (-10 if i % 2 == 0 else 10)) for i in range(6)] + [(x + 70, y), (x + 80, y)]
    return wire(pts, INK, 3) + text(x + 40, y - 20, label, 15, INK, "middle", 600)


def led(x, y):
    """anode at x, cathode at x + 60 (triangle pointing to the bar), two light arrows"""
    return ('<path d="M%s %s L%s %s L%s %s Z" fill="%s" stroke="%s" stroke-width="2"/>' % (
        x + 8, y - 18, x + 8, y + 18, x + 38, y, CYAN, CYAN)) + (
        '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="4"/>'
        '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="3"/>'
        '<path d="M%s %s l12 -12 M%s %s l12 -12" stroke="%s" stroke-width="2.5" fill="none"/>'
        '<path d="M%s %s l-1 6 l6 -1 z M%s %s l-1 6 l6 -1 z" fill="%s"/>') % (
        x + 40, y - 20, x + 40, y + 20, CYAN, x, y, x + 8, y, INK, x + 26, y - 22, x + 36, y - 26, CYAN,
        x + 38, y - 34, x + 48, y - 38, CYAN) + '<line x1="%s" y1="%s" x2="%s" y2="%s" stroke="%s" stroke-width="3"/>' % (
        x + 40, y, x + 60, y, INK) + text(x + 30, y + 44, "LED  + (long leg) &#8594; &#8722; (flat side)", 14, DIM, "middle")


def build():
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (W, H, W, H),
         '<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG),
         text(60, 70, "ABleem<tspan fill=\"%s\">Station</tspan> &#183; wiring" % CYAN, 34, INK, weight=600, family="OSB"),
         text(60, 104, "Raspberry Pi 3B / 3B+ &#183; pin 1 = the square pad, at the microSD end of the header; odd pins are the row nearer the middle of the board", 16, DIM)]
    # the header (pins 1-20 are all this needs)
    s.append('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="%s" stroke="%s"/>' % (X_ODD - 26, Y0 - 30, X_EVEN - X_ODD + 52, 10 * DY + 18, PANEL, LINE))
    s.append(text((X_ODD + X_EVEN) / 2, Y0 - 42, "GPIO header (pins 1-20)", 14, DIM, "middle"))
    for n in range(1, 21):
        x, y = pin_xy(n)
        col = USED.get(n)
        shape = ('<rect x="%s" y="%s" width="18" height="18" fill="%s" stroke="%s" stroke-width="2"/>' % (x - 9, y - 9, col or "#4a5561", INK)
                 if n == 1 else '<circle cx="%s" cy="%s" r="9" fill="%s" stroke="%s" stroke-width="2"/>' % (x, y, col or "#4a5561", INK if col else LINE))
        s.append(shape)
        s.append(text(x, y + 4, str(n), 10, BG if col else DIM, "middle", 700))
        lab = "%s" % NAMES[n]
        if n % 2:
            s.append(text(X_ODD - 24, y - 12, lab, 13, INK if col else DIM, "end", 600 if col else 400))
        else:
            s.append(text(X_EVEN + 24, y - 12, lab, 13, INK if col else DIM, "start", 600 if col else 400))
    # POWER: pin 5 -> button -> pin 9 (both on the odd column, to the left)
    x5, y5 = pin_xy(5)
    x9, y9 = pin_xy(9)
    s.append(wire([(x5, y5), (420, y5), (420, 420), (390, 420)], YEL))
    s.append(switch(310, 420, "POWER", YEL))
    s.append(wire([(310, 420), (280, 420), (280, 470), (560, 470), (560, y9), (x9, y9)], GND))
    s.append(text(150, 300, "POWER", 22, YEL, weight=600))
    s.append(text(150, 326, "GPIO3 (pin 5) + GND (pin 9)", 15, INK))
    s.append(text(150, 350, "press = safe shutdown", 15, DIM))
    s.append(text(150, 372, "press again = start from halt", 15, DIM))
    # LED: pin 8 -> resistor -> LED -> pin 6 (both on the even column, to the right)
    x8, y8 = pin_xy(8)
    x6, y6 = pin_xy(6)
    s.append(wire([(x8, y8), (930, y8)], CYAN))
    s.append(resistor(930, y8, "330 &#937;"))
    s.append(wire([(1010, y8), (1040, y8)], CYAN))
    s.append(led(1040, y8))
    s.append(wire([(1100, y8), (1140, y8), (1140, y6 - 60), (880, y6 - 60), (880, y6), (x6, y6)], GND))
    s.append(text(1190, 250, "LED", 22, CYAN, weight=600))
    s.append(text(1190, 276, "GPIO14 TXD (pin 8) &#8594; 330 &#937;", 15, INK))
    s.append(text(1190, 298, "&#8594; LED &#8594; GND (pin 6)", 15, INK))
    s.append(text(1190, 322, "lit while the Pi runs", 15, DIM))
    s.append(text(1190, 344, "blue / white / cyan LED: 100 &#937;", 15, DIM))
    # the lower panels start below the header
    P0 = Y0 + 10 * DY + 20
    # RESET: the RUN pads
    s.append('<rect x="150" y="%d" width="520" height="160" rx="8" fill="%s" stroke="%s"/>' % (P0, PANEL, LINE))
    s.append(text(176, P0 + 36, "RESET", 22, MAG, weight=600))
    s.append(text(176, P0 + 62, "the two pads marked RUN on the Pi board", 15, INK))
    s.append(text(176, P0 + 84, "(solder in a 2-pin 2.54 mm header)", 15, DIM))
    s.append(text(176, P0 + 130, "press = restart", 15, DIM))
    for px in (560, 600):
        s.append('<rect x="%d" y="%d" width="20" height="20" fill="none" stroke="%s" stroke-width="2"/>'
                 '<circle cx="%d" cy="%d" r="5" fill="%s"/>' % (px - 10, P0 + 40, INK, px, P0 + 50, INK))
    s.append(text(580, P0 + 30, "RUN", 13, DIM, "middle", 600))
    s.append(wire([(560, P0 + 50), (560, P0 + 120), (500, P0 + 120)], MAG))
    s.append(switch(420, P0 + 120, "", MAG))
    s.append(wire([(420, P0 + 120), (400, P0 + 120), (400, P0 + 145), (630, P0 + 145), (630, P0 + 80), (600, P0 + 80), (600, P0 + 50)], MAG))
    # config.txt
    s.append('<rect x="760" y="%d" width="590" height="160" rx="8" fill="%s" stroke="%s"/>' % (P0, PANEL, LINE))
    s.append(text(786, P0 + 36, "/boot/config.txt (add these two lines)", 17, INK, weight=600))
    s.append(text(786, P0 + 74, "dtoverlay=gpio-shutdown", 18, CYAN, family="monospace"))
    s.append(text(786, P0 + 104, "enable_uart=1", 18, CYAN, family="monospace"))
    s.append(text(786, P0 + 136, "then reboot once; the POWER button and the LED work from then on", 14, DIM))
    # what to buy
    B0 = P0 + 190
    s.append('<rect x="150" y="%d" width="1200" height="210" rx="8" fill="%s" stroke="%s"/>' % (B0, PANEL, LINE))
    s.append(text(176, B0 + 36, "What to buy", 20, INK, weight=600))
    rows = [("2 x", "tactile push button 6 x 6 mm, 5 mm tall, 4 pins through-hole (THT)", "POWER, RESET - the bracket pockets are 6.3 x 6.3 mm"),
            ("1 x", "LED 5 mm, diffused (any colour; green / red / yellow / orange are brightest on 3.3 V)", "the front holder takes 5 mm"),
            ("1 x", "resistor 330 &#937; 1/4 W (or 100 &#937; for a blue / white / cyan LED)", "in series with the LED"),
            ("1 x", "2-pin male header 2.54 mm", "soldered into the RUN pads"),
            ("6 x", "jumper wire female-female (Dupont), 20 cm + heat-shrink tube", "onto the GPIO pins and the switches' legs")]
    for i, (q, a, b) in enumerate(rows):
        y = B0 + 72 + i * 28
        s.append(text(176, y, q, 15, CYAN, weight=600))
        s.append(text(220, y, a, 15, INK))
        s.append(text(1330, y, b, 13, DIM, "end"))
    s.append("</svg>")
    return "".join(s)


def main():
    svg = build()
    open(os.path.join(OUT, "wiring.svg"), "w", encoding="utf-8", newline="\n").write(svg)
    css = ('@font-face{font-family:RH;src:url("%s")}@font-face{font-family:OSB;src:url("%s")}*{margin:0}svg{display:block}' % (
        "file:///" + os.path.join(FONTS, "RedHatText-Medium.ttf").replace("\\", "/"),
        "file:///" + os.path.join(FONTS, "OpenSans-Bold.ttf").replace("\\", "/")))
    page = os.path.join(OUT, "_wiring.html")
    open(page, "w", encoding="utf-8", newline="\n").write("<!doctype html><style>%s</style>%s" % (css, svg))
    subprocess.run([find_chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    "--force-device-scale-factor=1", "--window-size=%d,%d" % (W, H), "--virtual-time-budget=3000",
                    "--screenshot=" + os.path.join(OUT, "wiring.png"), "file:///" + page.replace("\\", "/")],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(page)
    print("written:", os.path.join(OUT, "wiring.png"))


if __name__ == "__main__":
    main()
