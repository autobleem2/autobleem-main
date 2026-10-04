"""ABleemStation wiring diagrams, one per front-LED version, with the parts to buy:
  ../files/wiring.svg / .png       a plain 5 mm LED   (printed shell)
  ../files/wiring-rgb.svg / .png   one WS2812B pixel  (printed shell-rgb)
POWER: GPIO3 (pin 5) + GND (pin 9) - dtoverlay=gpio-shutdown: shuts down, and wakes the Pi from halt.
RESET: GPIO23 (pin 16) + GND (pin 20) - dtoverlay=gpio-key with keycode 164 (KEY_PLAYPAUSE), the key the
       console's Reset button sends: AutoBleem's emulators leave the game, an App is closed.
LED:   GPIO14/TXD (pin 8) -> 330 ohm -> LED -> GND (pin 6), lit while the Pi runs (enable_uart=1).
RGB:   5V (pin 2), GND (pin 6), data from GPIO10/SPI MOSI (pin 19) through 330 ohm; a service on the Pi sets green
       at boot and orange at shutdown (the pixel keeps its colour while it has 5 V, so the standby stays orange).
Run:  python make_wiring.py   (headless Chrome renders the PNGs; the fonts come from fonts/)"""
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
CYAN, MAG, YEL, GND, RED, GRN = "#36d9e0", "#ff46aa", "#f2c94c", "#8a96a3", "#ff6b5e", "#3cff6e"
W, H = 1500, 1100
NAMES = {1: "3V3", 2: "5V", 3: "GPIO2 SDA", 4: "5V", 5: "GPIO3 SCL", 6: "GND", 7: "GPIO4", 8: "GPIO14 TXD", 9: "GND",
         10: "GPIO15 RXD", 11: "GPIO17", 12: "GPIO18", 13: "GPIO27", 14: "GND", 15: "GPIO22", 16: "GPIO23", 17: "3V3",
         18: "GPIO24", 19: "GPIO10 MOSI", 20: "GND"}
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
    """horizontal, from (x, y) to (x + 80, y)"""
    pts = [(x, y)] + [(x + 10 + i * 10, y + (-10 if i % 2 == 0 else 10)) for i in range(6)] + [(x + 70, y), (x + 80, y)]
    return wire(pts, INK, 3) + text(x + 40, y - 20, label, 15, INK, "middle", 600)


def resistor_v(x, y, label):
    """vertical, from (x, y) down to (x, y + 80), the label on its left"""
    pts = [(x, y)] + [(x + (-10 if i % 2 == 0 else 10), y + 10 + i * 10) for i in range(6)] + [(x, y + 70), (x, y + 80)]
    return wire(pts, INK, 3) + text(x - 20, y + 46, label, 15, INK, "end", 600)


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


def pixel(x, y):
    """a WS2812B strip pixel, 120 x 110: the 5V and GND pads on the left (y + 55, y + 85), DIN on the right (y + 85)"""
    s = ['<rect x="%s" y="%s" width="120" height="110" rx="6" fill="%s" stroke="%s" stroke-width="2"/>' % (x, y, PANEL, INK),
         '<rect x="%s" y="%s" width="40" height="34" rx="4" fill="#f4f4f0"/>' % (x + 40, y + 10),
         '<circle cx="%s" cy="%s" r="9" fill="none" stroke="#c9c9c4" stroke-width="3"/>' % (x + 60, y + 27)]
    for px, py in ((x, y + 55), (x, y + 85), (x + 120, y + 85)):
        s.append('<circle cx="%s" cy="%s" r="5" fill="%s"/>' % (px, py, INK))
    s.append(text(x + 10, y + 60, "5V", 12, INK, weight=600))
    s.append(text(x + 10, y + 90, "GND", 12, INK, weight=600))
    s.append(text(x + 110, y + 90, "DIN", 12, INK, "end", 600))
    s.append(text(x + 60, y + 132, "WS2812B pixel (cut from a 5 V strip; DIN = the arrow's start)", 14, DIM, "middle"))
    return "".join(s)


def build(rgb):
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">' % (W, H, W, H),
         '<rect width="%d" height="%d" fill="%s"/>' % (W, H, BG),
         text(60, 70, "ABleem<tspan fill=\"%s\">Station</tspan> &#183; wiring &#183; %s" % (CYAN, "RGB pixel" if rgb else "LED"),
              34, INK, weight=600, family="OSB"),
         text(60, 104, "Raspberry Pi 3B / 3B+ &#183; pin 1 = the square pad, at the microSD end of the header; odd pins are the row nearer the middle of the board", 16, DIM)]
    used = {5: YEL, 9: GND, 16: MAG, 20: GND, 6: GND}
    used.update({2: RED, 19: GRN} if rgb else {8: CYAN})
    # the header (pins 1-20 are all this needs)
    s.append('<rect x="%d" y="%d" width="%d" height="%d" rx="6" fill="%s" stroke="%s"/>' % (
        X_ODD - 26, Y0 - 30, X_EVEN - X_ODD + 52, 10 * DY + 18, PANEL, LINE))
    s.append(text((X_ODD + X_EVEN) / 2, Y0 - 42, "GPIO header (pins 1-20)", 14, DIM, "middle"))
    for n in range(1, 21):
        x, y = pin_xy(n)
        col = used.get(n)
        s.append('<rect x="%s" y="%s" width="18" height="18" fill="%s" stroke="%s" stroke-width="2"/>' % (x - 9, y - 9, col or "#4a5561", INK)
                 if n == 1 else '<circle cx="%s" cy="%s" r="9" fill="%s" stroke="%s" stroke-width="2"/>' % (x, y, col or "#4a5561", INK if col else LINE))
        s.append(text(x, y + 4, str(n), 10, BG if col else DIM, "middle", 700))
        if n % 2:
            s.append(text(X_ODD - 24, y - 12, NAMES[n], 13, INK if col else DIM, "end", 600 if col else 400))
        else:
            s.append(text(X_EVEN + 24, y - 12, NAMES[n], 13, INK if col else DIM, "start", 600 if col else 400))
    # POWER: pin 5 -> button -> pin 9 (both on the odd column, to the left)
    x5, y5 = pin_xy(5)
    x9, y9 = pin_xy(9)
    s.append(wire([(x5, y5), (420, y5), (420, 420), (390, 420)], YEL))
    s.append(switch(310, 420, "POWER", YEL))
    s.append(wire([(310, 420), (280, 420), (280, 470), (560, 470), (560, y9), (x9, y9)], GND))
    s.append(text(120, 300, "POWER", 22, YEL, weight=600))
    s.append(text(120, 326, "GPIO3 (pin 5) + GND (pin 9)", 15, INK))
    s.append(text(120, 350, "press = safe shutdown", 15, DIM))
    s.append(text(120, 372, "press again = start from halt", 15, DIM))
    # RESET: pin 16 -> button -> pin 20 (both on the even column, to the right)
    x16, y16 = pin_xy(16)
    x20, y20 = pin_xy(20)
    s.append(wire([(x16, y16), (880, y16)], MAG))
    s.append(switch(880, y16, "RESET", MAG))
    s.append(wire([(960, y16), (1000, y16), (1000, y20), (x20, y20)], GND))
    s.append(text(1040, y16 - 14, "RESET", 22, MAG, weight=600))
    s.append(text(1040, y16 + 12, "GPIO23 (pin 16) + GND (pin 20)", 15, INK))
    s.append(text(1040, y16 + 36, "the console's Reset: in a game = back to", 15, DIM))
    s.append(text(1040, y16 + 58, "the menu, in an App = close it", 15, DIM))
    if rgb:
        # the pixel: 5V from pin 2, GND to pin 6, data from pin 19 through 330 ohm, round the bottom of the header
        x2, y2 = pin_xy(2)
        x6, y6 = pin_xy(6)
        x19, y19 = pin_xy(19)
        px, py = 1060, 170
        s.append(wire([(x2, y2), (1010, y2), (1010, py + 55), (px, py + 55)], RED))
        s.append(wire([(x6, y6), (980, y6), (980, py + 85), (px, py + 85)], GND))
        s.append(wire([(x19, y19), (610, y19), (610, 640), (1440, 640), (1440, 450)], GRN))
        s.append(resistor_v(1440, 370, "330 &#937;"))
        s.append(wire([(1440, 370), (1440, py + 85), (px + 120, py + 85)], GRN))
        s.append(pixel(px, py))
        s.append(text(1060, 350, "RGB pixel", 22, GRN, weight=600))
        s.append(text(1060, 376, "5V (pin 2) + GND (pin 6)", 15, INK))
        s.append(text(1060, 398, "DIN &#8592; 330 &#937; &#8592; GPIO10 (pin 19)", 15, INK))
        s.append(text(1060, 422, "green = on, orange = standby", 15, DIM))
    else:
        # the LED: pin 8 -> resistor -> LED -> pin 6 (both on the even column, to the right)
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
    # config.txt
    P0 = 680
    conf = [("dtoverlay=gpio-shutdown", "POWER"),
            ("dtoverlay=gpio-key,gpio=23,active_low=1,gpio_pull=up,keycode=164", "RESET (164 = the console's Reset key)"),
            ("dtparam=spi=on", "the pixel's data line (SPI)") if rgb else ("enable_uart=1", "the LED: TXD is high while the Pi runs")]
    ph = 176 if rgb else 150
    s.append('<rect x="120" y="%d" width="1260" height="%d" rx="8" fill="%s" stroke="%s"/>' % (P0, ph, PANEL, LINE))
    s.append(text(146, P0 + 36, "/boot/config.txt (add these lines, then reboot once)", 17, INK, weight=600))
    for i, (ln, why) in enumerate(conf):
        s.append(text(146, P0 + 72 + i * 28, ln, 17, CYAN, family="monospace"))
        s.append(text(1354, P0 + 72 + i * 28, why, 14, DIM, "end"))
    if rgb:
        s.append(text(146, P0 + 160, "+ a small service on the Pi sets the colour: green at boot, orange at shutdown (the pixel keeps it through the standby)", 14, DIM))
    # what to buy
    B0 = P0 + ph + 20
    s.append('<rect x="120" y="%d" width="1260" height="190" rx="8" fill="%s" stroke="%s"/>' % (B0, PANEL, LINE))
    s.append(text(146, B0 + 36, "What to buy", 20, INK, weight=600))
    rows = [("2 x", "tactile push button 6 x 6 mm, 5 mm tall, 4 pins through-hole (THT)", "POWER, RESET - the bracket pockets are 6.3 x 6.3 mm")]
    if rgb:
        rows += [("1 x", "WS2812B LED strip, 5 V, 60 LEDs/m, 10 mm wide (one pixel is cut off it)", "slides into the slot behind the lens"),
                 ("1 x", "resistor 330 &#937; 1/4 W", "in the data line, close to the pixel"),
                 ("7 x", "jumper wire female-female (Dupont), 20 cm + heat-shrink tube", "three soldered to the pixel's pads")]
    else:
        rows += [("1 x", "LED 5 mm, diffused (green / red / yellow / orange are brightest on 3.3 V)", "sits in the tube behind the lens"),
                 ("1 x", "resistor 330 &#937; 1/4 W (or 100 &#937; for a blue / white / cyan LED)", "in series with the LED"),
                 ("6 x", "jumper wire female-female (Dupont), 20 cm + heat-shrink tube", "onto the GPIO pins and the switches' legs")]
    for i, (q, a, b) in enumerate(rows):
        y = B0 + 72 + i * 30
        s.append(text(146, y, q, 15, CYAN, weight=600))
        s.append(text(190, y, a, 15, INK))
        s.append(text(1354, y, b, 13, DIM, "end"))
    s.append("</svg>")
    return "".join(s)


def render(name, svg):
    open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8", newline="\n").write(svg)
    css = ('@font-face{font-family:RH;src:url("%s")}@font-face{font-family:OSB;src:url("%s")}*{margin:0}svg{display:block}' % (
        "file:///" + os.path.join(FONTS, "RedHatText-Medium.ttf").replace("\\", "/"),
        "file:///" + os.path.join(FONTS, "OpenSans-Bold.ttf").replace("\\", "/")))
    page = os.path.join(OUT, "_" + name + ".html")
    open(page, "w", encoding="utf-8", newline="\n").write("<!doctype html><style>%s</style>%s" % (css, svg))
    subprocess.run([find_chrome(), "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
                    "--force-device-scale-factor=1", "--window-size=%d,%d" % (W, H), "--virtual-time-budget=3000",
                    "--screenshot=" + os.path.join(OUT, name + ".png"), "file:///" + page.replace("\\", "/")],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    os.remove(page)
    print("written:", os.path.join(OUT, name + ".png"))


def main():
    render("wiring", build(False))
    render("wiring-rgb", build(True))


if __name__ == "__main__":
    main()
