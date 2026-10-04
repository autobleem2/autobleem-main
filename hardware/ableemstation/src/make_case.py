"""ABleemStation - a 3D-printable retro-console case for the Raspberry Pi 3B / 3B+ (build123d, all sizes in mm).

Parts (each prints without supports):
  shell   the top: walls + roof, printed upside down; port windows, round slotted vent over the SoC, front POWER /
          RESET holes + LED holder, sticker recesses, 4 bosses for M3 heat-set inserts (OD 4.0 hole, 6 deep)
  base    the floor plate that sits inside the shell: Pi standoffs (M2.5 self-tap), the switch bracket for two
          6x6 mm tact switches, countersunk M3 holes, feet recesses, a slot to reach the microSD
  button  POWER / RESET cap (print 2)
Layout: the back wall carries the Pi's long edge (power, HDMI, audio - the TV cables), the right wall the USB +
Ethernet, the front the buttons and the LED. Pi 3B mechanical data: board 85 x 56 x 1.4, holes 58 x 49 from (3.5, 3.5).
Run:  python make_case.py   (needs build123d: pip install build123d)
Writes STEP + STL + 3MF per part, the assembly STEP and the viewer's meshes to ../files/."""
import json
import os

from build123d import (Align, Axis, Box, Compound, Cylinder, Kind, Location, Polygon, Pos, Rot, chamfer,
                       Mesher, export_step, export_stl, extrude, offset)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "files"))
os.makedirs(OUT, exist_ok=True)
MIN = (Align.MIN, Align.MIN, Align.MIN)

# ---- main sizes
W, D = 140.0, 105.0                 # outer: x = width, y = depth (back = 0 -> front)
WALL, ROOF, CUT = 2.4, 2.4, 16.0    # wall, roof, the cut corners (back-left + front-right, the ab2.0.0 shape)
BASE_T, FIT = 3.0, 0.3              # floor plate thickness, its gap to the walls
STAND = 3.0                         # Pi standoff height above the plate (clears the microSD socket under the board)
BX, BY = W - WALL - 2.0 - 85.0, WALL + 1.0      # the Pi board's corner: USB 2 mm past the board edge, HDMI 1 mm
BZ = BASE_T + STAND                 # board underside
BT = BZ + 1.4                       # board top
H = round(BT + 16.0 + 1.0 + ROOF, 1)  # height: just the Pi - the USB stack (16) + 1 mm + the roof
BTN_Z, BTN_X, LED_X = 16.5, (24.0, 44.0), 118.0
BAND = 11.0                         # the waist groove; below it the second colour (a filament change)
CAP_L, CAP_REST = 6.4, D - WALL - 1.5  # button cap length; its back end at rest (flange against the wall)
BOSSES = [(12.0, 12.0), (10.0, 84.0), (131.0, 66.0), (130.0, 95.0)]


def outline(inset=0.0):
    pts = [(CUT, 0), (W, 0), (W, D - CUT), (W - CUT, D), (0, D), (0, CUT)]
    face = Polygon(*pts, align=None)
    return offset(face, -inset, kind=Kind.INTERSECTION) if inset else face


def prism(face, z0, h):
    return Pos(0, 0, z0) * extrude(face, amount=h)


def box(x, y, z, dx, dy, dz):
    return Pos(x, y, z) * Box(dx, dy, dz, align=MIN)


def cyl_y(x, y, z, r, length):      # a cylinder along +y starting at y
    return Pos(x, y, z) * (Rot(-90, 0, 0) * Cylinder(r, length, align=(Align.CENTER, Align.CENTER, Align.MIN)))


def cyl_z(x, y, z, r, h):
    return Pos(x, y, z) * Cylinder(r, h, align=(Align.CENTER, Align.CENTER, Align.MIN))


# ---- the Pi (a ghost for the fit check and the viewer; port sizes include the plugs' clearance where it matters)
def pi_ghost():
    p = box(BX, BY, BZ, 85, 56, 1.4)
    p += box(BX + 85 - 21 + 2.1, BY + 10.25 - 8, BT, 21, 16, 13.5)           # Ethernet
    for yc in (29.0, 47.0):
        p += box(BX + 85 - 17 + 2.1, BY + yc - 6.6, BT, 17, 13.2, 16)        # USB pairs
    p += box(BX + 10.6 - 4, BY - 1.0, BT, 8, 6, 3)                           # micro-USB
    p += box(BX + 32 - 7.5, BY - 1.0, BT, 15, 12, 6.5)                       # HDMI
    p += cyl_y(BX + 53.5, BY - 1.0, BT + 3, 3.0, 12)                         # audio
    p += box(BX + 7, BY + 50, BT, 51, 5, 8.5)                                # GPIO header
    p += box(BX + 25, BY + 22, BT, 14, 14, 1.4)                              # SoC
    return p


# ---- shell
def shell():
    s = prism(outline(), 0, H)
    s = chamfer(s.edges().group_by(Axis.Z)[-1], 2.0)                         # soft top edge
    s -= prism(outline(WALL), -1, H - ROOF + 1)
    # port windows (0.8 mm around each port, bigger where a plug's body must pass)
    s -= box(W - WALL - 1, BY + 10.25 - 8.8, BT - 0.8, WALL + 2, 17.6, 15.1)              # Ethernet
    for yc in (29.0, 47.0):
        s -= box(W - WALL - 1, BY + yc - 7.4, BT - 0.8, WALL + 2, 14.8, 17.6)             # USB
    s -= box(BX + 10.6 - 6, -1, BT - 2.0, 12, WALL + 2, 7.5)                              # micro-USB plug
    s -= box(BX + 32 - 11, -1, BT - 2.5, 22, WALL + 2, 11.5)                              # HDMI plug
    s -= cyl_y(BX + 53.5, -1, BT + 3, 4.5, WALL + 2)                                      # audio plug
    # cooling slots: a field through the roof over the SoC, and low slots in the side wall opposite the USB (air in)
    cx, cy = BX + 32, BY + 29
    for i in range(-4, 5):
        s -= box(cx - 26, cy + i * 5.0 - 1.25, H - ROOF - 1, 52, 2.5, ROOF + 2)
    for i in range(8):
        s -= box(-1, 34 + i * 6.0, BAND + 2.0, WALL + 2, 2.5, H - ROOF - BAND - 6.0)
    # sticker recesses (0.4 mm): the logo plate on the roof, the label strip on the front
    s -= box(12, 76, H - 0.4, 62, 18, 1)
    s -= box(14, D - 0.4, BTN_Z - 12.0, 44, 1, 5)
    ring = prism(outline(), BAND - 1.2, 1.2) - prism(outline(0.8), BAND - 1.3, 1.4)
    s -= ring                                                                             # the waist groove all round
    # front: two button holes, the LED hole + its holder tube
    for x in BTN_X:
        s -= cyl_y(x, D - WALL - 1, BTN_Z, 4.6, WALL + 2)
    s += cyl_y(LED_X, D - WALL - 6, BTN_Z, 4.2, 6)
    s -= cyl_y(LED_X, D - WALL - 7, BTN_Z, 2.6, WALL + 8)
    # bosses for M3 heat-set inserts, from the plate up to the roof
    for x, y in BOSSES:
        s += cyl_z(x, y, BASE_T, 4.2, H - ROOF - BASE_T + 0.5)
        s -= cyl_z(x, y, BASE_T - 1, 2.0, 7)
    return s


# ---- base
def base():
    b = prism(outline(WALL + FIT), 0, BASE_T)
    for hx, hy in ((3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)):
        b += cyl_z(BX + hx, BY + hy, BASE_T, 3.0, STAND)
        b -= cyl_z(BX + hx, BY + hy, 1.0, 1.15, STAND + 3)                           # M2.5 self-tap
    for x, y in BOSSES:                                                              # M3 clearance + countersink
        b -= cyl_z(x, y, -1, 1.7, BASE_T + 2)
        b -= Pos(x, y, -0.01) * Cylinder(3.2, 1.7, align=(Align.CENTER, Align.CENTER, Align.MIN))
    for fx, fy in ((22, 14), (W - 18, 14), (22, D - 14), (W - 30, D - 14)):          # feet recesses (Ø12 rubber)
        b -= cyl_z(fx, fy, -0.01, 6.2, 1.0)
    b -= box(BX - 9, BY + 28 - 8, -1, 12, 16, BASE_T + 2)                            # reach the microSD from below
    # switch bracket: 6x6 tact switches face the buttons; pockets 6.3 x 6.3 x 3.6 + a slot for the legs
    yb = CAP_REST - 0.5 - 1.5 - 3.7 - 3.0        # cap back at rest - gap - plunger - switch body - bracket back
    b += box(BTN_X[0] - 8, yb, BASE_T, BTN_X[1] - BTN_X[0] + 16, 6.6, BTN_Z + 4.5 - BASE_T)
    for x in BTN_X:
        b -= box(x - 3.15, yb + 3.0, BTN_Z - 3.15, 6.3, 3.7, 6.3)
        b -= box(x - 3.15, yb - 1, BTN_Z - 1.5, 6.3, 5, 3.0)
    return b


# ---- button cap (print 2): the shaft through the wall + a flange inside that keeps it in
def button():
    c = cyl_y(0, 0, 0, 4.2, CAP_L)
    c += cyl_y(0, 0, 0, 5.6, 1.5)
    return c


def on_bed(part):
    """move a part so it lies on z = 0"""
    bb = part.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * part


def write_3mf(parts):
    """3MF per part, already turned the way it prints (shell: roof down, button: flange down), plus one file with
    every part to print (shell, base, 2 buttons) - the slicer's auto-arrange spreads them over the plates"""
    printable = {
        "shell": on_bed(Rot(180, 0, 0) * parts["shell"]),
        "base": on_bed(parts["base"]),
        "button": on_bed(Rot(90, 0, 0) * parts["button"]),
    }
    for name, p in printable.items():
        m = Mesher()
        m.add_shape(p, linear_deflection=0.02, angular_deflection=0.2)
        m.write(os.path.join(OUT, "ableemstation-%s.3mf" % name))
    m = Mesher()
    x = 0.0
    for name, p in (("shell", printable["shell"]), ("base", printable["base"]), ("button", printable["button"]),
                    ("button", printable["button"])):
        m.add_shape(Pos(x, 0, 0) * p, linear_deflection=0.02, angular_deflection=0.2)
        x += p.bounding_box().size.X + 10
    m.write(os.path.join(OUT, "ableemstation-all-parts.3mf"))


def main():
    parts = {"shell": shell(), "base": base(), "button": button()}
    pi = pi_ghost()
    for name, p in parts.items():
        export_step(p, os.path.join(OUT, "ableemstation-%s.step" % name))
        export_stl(p, os.path.join(OUT, "ableemstation-%s.stl" % name))
    write_3mf(parts)
    # assembly: buttons at rest (flange against the wall, front 2.5 mm proud)
    caps = [Pos(x, CAP_REST, BTN_Z) * parts["button"] for x in BTN_X]
    asm = Compound(children=[parts["shell"], parts["base"]] + caps, label="ABleemStation")
    export_step(asm, os.path.join(OUT, "ableemstation-assembly.step"))
    viewer = os.path.join(OUT, "viewer")
    os.makedirs(viewer, exist_ok=True)
    for name, p in (("shell", parts["shell"]), ("base", parts["base"]), ("caps", Compound(children=caps)), ("pi", pi)):
        export_stl(p, os.path.join(viewer, name + ".stl"), tolerance=0.05, angular_tolerance=0.2)
    for f in os.listdir(viewer):
        if f.endswith(".glb"):
            os.remove(os.path.join(viewer, f))
    # fit check: the Pi must not touch the case except where its ports pass through the windows
    for name, p in (("shell", parts["shell"]), ("base", parts["base"])):
        v = (p & pi).volume
        print("overlap pi x %s: %.2f mm3" % (name, v))
    for c in caps:
        print("overlap cap x shell: %.2f mm3" % (c & parts["shell"]).volume)
    # the sizes the viewer needs (so it never carries its own copies)
    json.dump({"W": W, "D": D, "H": H, "BAND": BAND, "LED": [LED_X, D - 1.4, BTN_Z],
               "top": {"c": [43, 85, H - 0.35], "w": 61, "h": 17}, "front": {"c": [36, D - 0.35, BTN_Z - 9.5], "w": 43, "h": 4.6},
               "filament_change_mm": round(H - BAND, 1)}, open(os.path.join(viewer, "params.json"), "w", newline="\n"), indent=1)
    print("height %.1f mm, filament change at %.1f mm" % (H, H - BAND))
    print("written to", OUT)


if __name__ == "__main__":
    main()
