"""ABleemStation universal: one case for the Raspberry Pi 2B, 3B, 3B+, 4B and 5, with the port walls as separate panels.
The shell, the base, the buttons and the lens are the Pi 3 case's (make_case.py); three wall openings take a panel each:
  back   (the board's long edge: power, HDMI, audio)   back-pi23 / back-pi4 / back-pi5 / back-blank
  right  (the short edge: USB + Ethernet)              right-pi23 / -pi4 / -pi5, each also "-front" (the USB block
                                                       furthest from the Ethernet closed - it feeds the front USB), blank
  front  (between the buttons and the LED)             front-usb (two USB-A sockets) / front-blank
A panel slides up into its opening from below: a tongue on its inner half runs in grooves in the jambs and the roof,
and a foot on its inside rests on the base plate, so the screwed-on base locks it. Panels print standing, bottom
edge down, so a filament change gives them the shell's two colours at the same line; every overhang inside is 45
degrees (no supports). Shells: passive (the Pi 3 case's
hidden roof vents) and active (a longer, denser vent field over the Raspberry Pi 5 Active Cooler), each for the plain
LED and the RGB pixel. Port positions: Raspberry Pi Ltd's mechanical drawings (3B+, 4B, 5).
Writes ../files/universal/ (STEP, STL, 3MF, viewer/). Run after make_case.py:  python make_universal.py"""
import json
import os

from build123d import Compound, Mesher, Plane, Polygon, Pos, Rot, export_step, export_stl, extrude

from make_case import (BASE_T, BT, BX, BY, BZ, D, FIT, H, ROOF, W, WALL, BAND, LED_X, BTN_Z, BTN_X, CAP_REST, LENS_FL,
                       LENS_R, LAYERS, base, box, button, cyl_y, first_layer_at, lens, on_bed, outline, prism, shell)

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "files", "universal"))
os.makedirs(os.path.join(OUT, "viewer"), exist_ok=True)

C = 0.15                     # panel clearance in its opening, each side
TG, TGC = 1.2, 0.15          # tongue thickness (the panel's inner half) and its clearance in the groove
TD = 1.2                     # how far a tongue reaches into its groove
RIB = 1.45                   # the inner lip that closes a groove inside a straight wall
ZT = H - ROOF                # the openings reach the roof's underside
ACTIVE_VENTS = (BX + 35, BY + 31, 64.0, 8)   # over the Active Cooler (63.5 x 42.5 x 13.7 mm)

# the openings: wall, from, to (along the wall), the foot's span, the inner ribs' bottom (clear of the board and
# the base's standoffs), which ends need a rib (a corner end has the other wall behind its groove instead)
OPENINGS = {
    "back": ("back", 48.5, 114.0, (58.0, 106.0), 8.0, (True, True)),
    "right": ("right", WALL, 60.5, (8.0, 55.0), 8.0, (False, True)),
    "front": ("front", 62.0, 106.0, (66.0, 102.0), BASE_T + 0.2, (True, True)),
}


def wbox(wall, u0, v0, z0, du, dv, dz):
    """a box in a wall's own frame: u along the wall, v from its outer face inwards, z up"""
    if wall == "back":
        return box(u0, v0, z0, du, dv, dz)
    if wall == "front":
        return box(u0, D - v0 - dv, z0, du, dv, dz)
    return box(W - v0 - dv, u0, z0, dv, du, dz)      # right


def wprofile(wall, u0, du, pts):
    """a profile drawn in a wall's (v, z) section, run along the wall from u0 for du"""
    if wall == "back":
        pl = Plane(origin=(u0, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0))
    elif wall == "front":
        pl = Plane(origin=(u0 + du, D, 0), x_dir=(0, -1, 0), z_dir=(-1, 0, 0))
    else:
        pl = Plane(origin=(W, u0, 0), x_dir=(-1, 0, 0), z_dir=(0, 1, 0))
    return extrude(pl * Polygon(*pts, align=None), amount=du)


FOOT = [(WALL - 0.3, BASE_T + 0.1), (WALL + 0.15, BASE_T + 0.1), (WALL + 1.75, BASE_T + 1.7), (WALL - 0.3, BASE_T + 1.7)]


def cut_opening(s, name):
    wall, a0, a1, _, rz, ribs = OPENINGS[name]
    v0, v1 = WALL - TG - TGC, WALL + TGC                       # the groove's span across the wall
    for end, on in zip((a0 - TD - 0.2 - RIB, a1), ribs):       # the inner lips first, so the grooves cut through them
        if on:
            s += wbox(wall, end, v1 - 0.01, rz, TD + 0.2 + RIB, RIB, ZT - rz + 0.01)
    s -= wbox(wall, a0, -1, -1, a1 - a0, WALL + 1.01, ZT + 1)                                # the opening
    s -= wbox(wall, a0 - TD - 0.2, v0, -1, a1 - a0 + 2 * (TD + 0.2), v1 - v0, ZT + 1 + TD + 0.2)  # the grooves
    return s


def panel(name, cuts=()):
    """the bare panel for an opening, minus the port windows (world-space solids)"""
    wall, a0, a1, (f0, f1), _, _ = OPENINGS[name]
    p = wbox(wall, a0 + C, 0, 0, a1 - a0 - 2 * C, WALL, ZT - C)                              # the outer plate
    p += wbox(wall, a0 - TD, WALL - TG, 0, a1 - a0 + 2 * TD, TG, ZT + TD)                    # the tongue
    p += wprofile(wall, f0, f1 - f0, FOOT)                     # the foot on the base, its underside at 45 degrees
    p -= prism(outline(), BAND - 1.2, 1.2) - prism(outline(0.8), BAND - 1.3, 1.4)          # the waist groove runs on
    for c in cuts:
        p -= c
    return p


# ---- the port windows, per board (world space; 0.8 mm round each port, bigger where a plug's body must pass)
def back_cuts(model):
    if model == "pi23":
        return [box(BX + 10.6 - 6, -1, BT - 2.0, 12, WALL + 2, 7.5),                     # micro-USB plug
                box(BX + 32 - 11, -1, BT - 2.5, 22, WALL + 2, 11.5),                     # HDMI plug
                cyl_y(BX + 53.5, -1, BT + 3, 4.5, WALL + 2)]                             # audio plug
    if model in ("pi4", "pi5"):
        c = [box(BX + 11.2 - 6.5, -1, BT + 1.6 - 4.0, 13, WALL + 2, 8.0),               # USB-C plug
             box(BX + 19.8, -1, BT + 1.5 - 4.0, 25.7, WALL + 2, 8.0)]                    # both micro-HDMI plugs
        if model == "pi4":
            c.append(cyl_y(BX + 54.0, -1, BT + 3, 4.5, WALL + 2))                        # audio plug (no jack on a Pi 5)
        return c
    return []


ETH_USB = {"pi23": (10.25, (29.0, 47.0)), "pi4": (45.75, (27.0, 9.0)), "pi5": (10.2, (29.1, 47.0))}


def right_cuts(model, front_usb=False):
    if model not in ETH_USB:
        return []
    eth, usb = ETH_USB[model]
    c = [box(W - WALL - 1, BY + eth - 8.8, BT - 0.8, WALL + 2, 17.6, 15.1)]               # Ethernet
    for yc in (usb[:1] if front_usb else usb):                                           # usb[1]: the block furthest from the Ethernet
        c.append(box(W - WALL - 1, BY + yc - 7.4, BT - 0.8, WALL + 2, 14.8, 17.6))
    if front_usb:                                                                        # the closed block still pokes 0.1 mm past the
        c.append(box(W - WALL - 0.01, BY + usb[1] - 7.4, BT - 0.8, 1.01, 14.8, 17.6))   # board edge: a 1 mm relief inside
    return c


# front USB: two USB-A sockets (a THT "USB-A female, 180 degrees" part, 14.5 x 7 mm shell) pushed in from behind into
# a block behind the panel; the plug passes a 13 x 5.6 window, the socket stops behind a 1 mm lip. The block's
# underside rises at 45 degrees from the foot, so the panel prints standing - which puts the sockets in its upper half
USB_X, USB_DEPTH = (74.0, 94.0), 12.0
USB_Z = BASE_T + 0.1 + (USB_DEPTH - WALL - 0.15) + 5.3          # the block's back edge, 5.3 under the socket's centre


def front_usb_panel():
    p = panel("front")
    p += wprofile("front", USB_X[0] - 9.0, USB_X[1] - USB_X[0] + 18.0,
                  [(WALL - 0.3, BASE_T + 0.1), (WALL + 0.15, BASE_T + 0.1), (USB_DEPTH, USB_Z - 5.3),
                   (USB_DEPTH, USB_Z + 5.3), (WALL - 0.3, USB_Z + 5.3)])
    for x in USB_X:
        p -= box(x - 7.4, D - USB_DEPTH - 0.5, USB_Z - 3.7, 14.8, USB_DEPTH - 0.5, 7.4)        # the socket's pocket
        p -= box(x - 6.5, D - 1.5, USB_Z - 2.8, 13.0, 2.5, 5.6)                                # the plug's window
    return p


# ---- the boards, as ghosts for the fit check and the viewer
def pi_ghost(model, cooler=False):
    p = box(BX, BY, BZ, 85, 56, 1.4)
    p += box(BX + 7, BY + 50, BT, 51, 5, 8.5)                                            # GPIO header
    eth, usb = ETH_USB[model]
    p += box(BX + 85 - 21 + (3.0 if model == "pi5" else 2.1), BY + eth - 8, BT, 21, 16, 13.5)   # Ethernet
    for yc in usb:
        p += box(BX + 85 - 17 + 2.1, BY + yc - 6.6, BT, 17, 13.2, 16)                    # USB pairs
    if model == "pi23":
        p += box(BX + 10.6 - 4, BY - 1.0, BT, 8, 6, 3)                                   # micro-USB
        p += box(BX + 32 - 7.5, BY - 1.0, BT, 15, 12, 6.5)                               # HDMI
        p += cyl_y(BX + 53.5, BY - 1.0, BT + 3, 3.0, 12)                                 # audio
        p += box(BX + 25, BY + 22, BT, 14, 14, 1.4)                                      # SoC
    else:
        p += box(BX + 11.2 - 4.5, BY - 1.0, BT, 9, 7.5, 3.2)                              # USB-C
        for x in ((26.0, 39.5) if model == "pi4" else (25.8, 39.2)):
            p += box(BX + x - 3.5, BY - 1.0, BT, 7, 7.5, 3.0)                            # micro-HDMI
        if model == "pi4":
            p += cyl_y(BX + 54.0, BY - 1.0, BT + 3, 3.0, 12)                             # audio
        p += box(BX + 22, BY + 15, BT, 16, 16, 2.4)                                      # SoC
    if cooler:
        p += box(BX + 3, BY + 4, BT, 63.5, 42.5, 13.7)                                   # Active Cooler (Pi 5)
    return p


def write_3mf(name, part):
    m = Mesher()
    m.add_shape(part, linear_deflection=0.02, angular_deflection=0.2)
    m.write(os.path.join(OUT, "ableemstation-%s.3mf" % name))


def standing(name, p):
    """a panel as it prints: standing on its bottom edge, its length along x"""
    return on_bed(Rot(0, 0, 90) * p if name.startswith("right") else p)


def main():
    shells = {}
    for kind, vents in (("", None), ("-active", ACTIVE_VENTS)):
        for led, suffix in (("led5", ""), ("rgb", "-rgb")):
            s = shell(led, vents)
            for name in OPENINGS:
                s = cut_opening(s, name)
            shells["uni-shell%s%s" % (kind, suffix)] = s
    panels = {}
    for m in ("pi23", "pi4", "pi5", "blank"):
        panels["back-" + m] = panel("back", back_cuts(m))
        panels["right-" + m] = panel("right", right_cuts(m))
        if m != "blank":
            panels["right-%s-front" % m] = panel("right", right_cuts(m, True))
    panels["front-usb"] = front_usb_panel()
    panels["front-blank"] = panel("front")

    for name, p in list(shells.items()) + [("panel-" + n, p) for n, p in panels.items()]:
        export_step(p, os.path.join(OUT, "ableemstation-%s.step" % name))
        export_stl(p, os.path.join(OUT, "ableemstation-%s.stl" % name))
    for name, s in shells.items():
        write_3mf(name, on_bed(Rot(180, 0, 0) * s))
    flats = {n: standing(n, p) for n, p in panels.items()}
    for n, p in flats.items():
        write_3mf("panel-" + n, p)
        bb = p.bounding_box().size
        print("panel %s prints %.1f x %.1f x %.1f mm (standing)" % (n, bb.X, bb.Y, bb.Z))
    m = Mesher()                                       # every panel on one plate, in rows
    x = y = row = 0.0
    for n, p in flats.items():
        bb = p.bounding_box().size
        if x and x + bb.X > 250:
            x, y, row = 0.0, y + row + 8, 0.0
        m.add_shape(Pos(x, y, 0) * p, linear_deflection=0.02, angular_deflection=0.2)
        x, row = x + bb.X + 8, max(row, bb.Y)
    m.write(os.path.join(OUT, "ableemstation-panels-all.3mf"))
    # the panels' filament change: printed bottom-up, the first layer at or above the shell's colour line
    # (the shell prints roof-down: its change at H - BAND from the roof is the line H - change from the bottom)
    pchange = {k: first_layer_at(H - first_layer_at(H - BAND, f, lh), f, lh) for k, (f, lh) in LAYERS.items()}
    print("panels: filament change at %.2f mm with 0.16 mm layers, %.2f mm with 0.24 mm" % (pchange["0.16"], pchange["0.24"]))

    # fit checks: no board touches a shell, a panel or the base; a panel fills its opening without touching the shell
    b = base()
    bad = 0
    for model in ("pi23", "pi4", "pi5"):
        for sname, s in shells.items():
            g = pi_ghost(model, cooler=(model == "pi5" and "active" in sname))
            v = (s & g).volume
            bad += v > 0.01
            print("overlap %s x %s: %.2f mm3" % (model, sname, v))
        g = pi_ghost(model)
        for n, p in panels.items():
            if model in n or n in ("back-blank", "front-blank", "front-usb"):   # right-blank: to drill for any board
                v = (p & g).volume
                bad += v > 0.01
                if v > 0.01:
                    print("overlap %s x panel-%s: %.2f mm3" % (model, n, v))
        print("overlap %s x base: %.2f mm3" % (model, (b & g).volume))
    for n, p in panels.items():
        v = (p & shells["uni-shell"]).volume + (p & shells["uni-shell-active-rgb"]).volume + (p & b).volume
        bad += v > 0.01
        print("panel %s x shell/base: %.2f mm3" % (n, v))
    assert not bad, "%d fit check(s) failed" % bad

    # the viewer: the passive shell, the base, caps, lens, each board's panel set and ghost, both front panels
    view = os.path.join(OUT, "viewer")
    caps = [Pos(x, CAP_REST, BTN_Z) * button() for x in BTN_X]
    lens_in = Pos(LED_X, D - WALL - LENS_FL - 0.2, BTN_Z) * lens()
    vparts = {"shell": shells["uni-shell"], "shell-active": shells["uni-shell-active"], "base": b,
              "caps": Compound(children=caps), "lens": lens_in,
              "front-usb": panels["front-usb"], "front-blank": panels["front-blank"]}
    for model in ("pi23", "pi4", "pi5"):
        vparts["set-" + model] = panels["back-" + model] + panels["right-" + model]
        vparts["set-%s-front" % model] = panels["back-" + model] + panels["right-%s-front" % model]
        vparts["pi-" + model] = pi_ghost(model, cooler=(model == "pi5"))
    for n, p in vparts.items():
        export_stl(p, os.path.join(view, n + ".stl"), tolerance=0.05, angular_tolerance=0.2)
    json.dump({"W": W, "D": D, "H": H, "BAND": BAND, "LED": [LED_X, D - 0.2, BTN_Z], "LED_R": LENS_R,
               "top": {"c": [43, 85, H - 0.35], "w": 61, "h": 17}, "front": {"c": [36, D - 0.35, BTN_Z - 9.5], "w": 43, "h": 4.6},
               "models": {"pi23": "Pi 2B / 3B / 3B+", "pi4": "Pi 4B", "pi5": "Pi 5"},
               "hint": "Raspberry Pi 2B / 3B / 3B+ / 4B / 5 - universal"},
              open(os.path.join(view, "params.json"), "w", newline="\n"), indent=1)
    print("written to", OUT)


if __name__ == "__main__":
    main()
