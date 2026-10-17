"""ABleemStation - a 3D-printable retro-console case for the Raspberry Pi 3B / 3B+ (build123d, all sizes in mm).

Parts (each prints without supports):
  shell   the top: walls + roof, printed upside down; port windows, hidden vents (45-degree slots in the roof over
          the SoC, side slots behind an inner baffle - no line of sight into the case), front POWER / RESET holes, the
          LED holder behind the lens, sticker recesses, 4 bosses for M3 heat-set inserts (Voron's M3 x 5 x 4: a 4.7 mm
          hole, 6 deep)
  base    the floor plate that sits inside the shell: Pi standoffs (M2.5 self-tap), the switch bracket for two
          6x6 mm tact switches, countersunk M3 holes, feet recesses, a finger-sized window to reach the microSD
  buttons the button tree: both POWER / RESET caps as one part, its ears melted onto two pins in the shell
  lens    the LED window, clear PETG: pushed into the front hole from inside, the LED hidden in the holder behind it
The shell comes in two versions: ableemstation-shell (a plain 5 mm LED in a tube behind the lens) and
ableemstation-shell-rgb (one WS2812B pixel cut from an LED strip, in a slot behind the lens - green while the Pi
runs, orange in standby like the PlayStation Classic, set by a small service on the Pi).
Layout: the back wall carries the Pi's long edge (power, HDMI, audio - the TV cables), the right wall the USB +
Ethernet, the front the buttons and the LED. Pi 3B mechanical data: board 85 x 56 x 1.4, holes 58 x 49 from (3.5, 3.5).
Run:  python make_case.py   (needs build123d: pip install build123d)
Writes STEP + STL + 3MF per part, the assembly STEP and the viewer's meshes to ../files/."""
import json
import math
import os

from build123d import (Align, Axis, Box, Compound, Cone, Cylinder, Kind, Location, Plane, Polygon, Pos, Rot, chamfer,
                       Mesher, export_step, export_stl, extrude, offset)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "files"))
os.makedirs(OUT, exist_ok=True)
MIN = (Align.MIN, Align.MIN, Align.MIN)

# ---- main sizes
W, D = 140.0, 105.0                 # outer: x = width, y = depth (back = 0 -> front)
WALL, ROOF, CUT = 2.4, 3.2, 16.0    # wall, roof (3.2: the vent slots' 45-degree run hides the inside), the cut corners (ab2.0.0)
BASE_T, FIT = 3.0, 0.3              # floor plate thickness, its gap to the walls
BRIDGE_STEP = 0.48                  # one bridge step over a screw-head recess: 3 layers at 0.16, 2 at 0.24
STAND = 3.0                         # Pi standoff height above the plate (clears the microSD socket under the board)
BX, BY = W - WALL - 2.0 - 85.0, WALL + 1.0      # the Pi board's corner: USB 2 mm past the board edge, HDMI 1 mm
BZ = BASE_T + STAND                 # board underside
BT = BZ + 1.4                       # board top
H = round(BT + 16.0 + 1.0 + ROOF, 1)  # height: just the Pi - the USB stack (16) + 1 mm + the roof
BTN_Z, BTN_X, LED_X = 16.5, (24.0, 44.0), 118.0
BAND = 11.0                         # the waist groove; below it the second colour (a filament change)
CAP_L, CAP_REST = 6.4, D - WALL - 1.5  # button cap length; its back end at rest (flange against the wall)
LENS_R, LENS_FL_R, LENS_FL = 3.0, 4.0, 1.0   # LED lens: shaft radius (through the wall), flange radius + thickness
LED_LEN = 8.6                       # a 5 mm LED from its rim to its tip
STRIP_W, STRIP_T = 10.6, 2.4        # the RGB pixel's slot: strip width + clearance, strip + LED + tape thickness
VENT_PITCH, VENT_W, VENT_N = 7.0, 2.4, 7   # roof vents: slot pitch, slot width (horizontal), number of slots
INSERT_R, INSERT_DEPTH = 2.35, 6.0          # the M3 heat-set insert's hole (Voron's standard M3 x 5 x 4 insert)
BOSSES = [(12.5, 14.5), (10.0, 84.0), (131.0, 66.0), (128.5, 90.5)]   # off the cut corners, checked in main()


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
def hull():
    """the shell's outer form, solid: the outline with the soft top edge"""
    s = prism(outline(), 0, H)
    return chamfer(s.edges().group_by(Axis.Z)[-1], 2.0)


def shell(led="led5", vents=None):
    """vents: the roof field (centre x, centre y, slot length, slot count); the default sits over the Pi 3's SoC"""
    s = hull()                                                               # soft top edge
    s -= prism(outline(WALL), -1, H - ROOF + 1)
    # port windows (0.8 mm around each port, bigger where a plug's body must pass)
    s -= box(W - WALL - 1, BY + 10.25 - 8.8, BT - 0.8, WALL + 2, 17.6, 15.1)              # Ethernet
    for yc in (29.0, 47.0):
        s -= box(W - WALL - 1, BY + yc - 7.4, BT - 0.8, WALL + 2, 14.8, 17.6)             # USB
    s -= box(BX + 10.6 - 6, -1, BT - 2.0, 12, WALL + 2, 7.5)                              # micro-USB plug
    s -= box(BX + 32 - 11, -1, BT - 2.5, 22, WALL + 2, 11.5)                              # HDMI plug
    s -= cyl_y(BX + 53.5, -1, BT + 3, 4.5, WALL + 2)                                      # audio plug
    # hidden roof vents over the SoC: slots straight through the 3.2 mm roof at 45 degrees, each running down towards
    # the front, so its inner end lies 3.2 mm in front of its outer end - more than the slot is wide: looking down,
    # or from in front of the console, you see the slot's sloping wall, never the inside. Printed roof-down, a 45
    # degree wall needs no bridge (the old labyrinth's channel was bridged, and the sagging bridge closed it).
    cx, cy, vl, vn = vents or (BX + 32, BY + 29, 52.0, VENT_N)
    run = ROOF + 2                                  # the slot's sideways run over its height (1 mm above and below)
    for i in range(vn):
        y = cy + (i - (vn - 1) / 2) * VENT_PITCH - ROOF / 2      # the outer opening, so the field stays centred
        slot = Polygon((y, H + 1), (y + VENT_W, H + 1), (y + VENT_W + run, H - ROOF - 1), (y + run, H - ROOF - 1), align=None)
        # (dir given: the polygon's winding alone would extrude it towards -x, away from the field)
        s -= extrude(Plane(origin=(cx - vl / 2, 0, 0), x_dir=(0, 1, 0), z_dir=(1, 0, 0)) * slot, amount=vl, dir=(1, 0, 0))
        # each slot must be open at both of the roof's faces, along its whole length - checked here, not on the printer
        for x in (cx - vl / 2 + 2, cx, cx + vl / 2 - 2):
            for dy, z in ((1, H - 0.3), (ROOF + 1, H - ROOF + 0.3)):
                assert (s & box(x - 0.5, y + dy + VENT_W / 2 - 0.3, z - 0.15, 1, 0.6, 0.3)).volume < 1e-3, \
                    "roof vent %d not open at (%g, %g)" % (i, x, z)
    # side vents opposite the USB (air in): slots through the wall with a baffle 1.8 mm behind them, hanging from the
    # roof and closed at both ends, open below - the air turns down under it; you see the baffle, not the inside
    for i in range(8):
        s -= box(-1, 34 + i * 6.0, BAND + 2.0, WALL + 2, 2.5, H - ROOF - BAND - 6.0)
    s += box(WALL + 1.8, 30, BAND - 2.0, 2.0, 58, H - ROOF - BAND + 2.5)                   # the baffle (2.0: it overlaps the boss at (10, 84), not just touches it)
    for y in (29.6, 86.6):
        s += box(WALL - 0.5, y, BAND - 2.0, 1.8 + 0.5 + 2.0, 1.8, H - ROOF - BAND + 2.5)  # its closed ends
    # sticker recesses (0.4 mm): the logo plate on the roof, the label strip on the front
    s -= box(12, 76, H - 0.4, 62, 18, 1)
    s -= box(14, D - 0.4, BTN_Z - 12.0, 44, 1, 5)
    ring = prism(outline(), BAND - 1.2, 1.2) - prism(outline(0.8), BAND - 1.3, 1.4)
    s -= ring                                                                             # the waist groove all round
    # front: two button holes and the LED window (the lens's shaft through the wall, its flange in a counterbore); the
    # shell is the same for both lights - the holder behind the window is a part of its own (led_holder)
    for x in BTN_X:
        s -= cyl_y(x, D - WALL - 1, BTN_Z, 4.6, WALL + 2)
    s -= lens_cuts()
    # bosses for M3 heat-set inserts, from the plate up to the roof
    for x, y in BOSSES:
        s += cyl_z(x, y, BASE_T, 4.2, H - ROOF - BASE_T + 0.5)
        s -= cyl_z(x, y, BASE_T - 1, INSERT_R, INSERT_DEPTH + 1)
    s += tree_pins()                                                                     # the button tree's pins
    return s + led_holder(led) if led else s


def lens_cuts():
    """the lens's flange counterbore and its shaft's hole through the front wall"""
    c = cyl_y(LED_X, D - WALL - LENS_FL - 0.2, BTN_Z, LENS_FL_R + 0.2, LENS_FL + 0.3)
    return c + cyl_y(LED_X, D - WALL - 1, BTN_Z, LENS_R + 0.1, WALL + 2)


# the LED holder: a part of its own, printed with the shell as one object - it reaches HOLDER_IN into the front wall,
# so the slicer merges the two (as the bottom merges its panels). Either light, the shell is the same
HOLDER_IN = 0.6


def led_holder(led):
    """led5: a tube for a 5 mm LED (its rim stops at the tube's back end, its tip 0.3 mm short of the lens), its upper
    half filled up to the roof (printed roof-down, it grows out of the roof); rgb: a block with a slot that one
    WS2812B strip segment slides into from below (wires out at the bottom), the LED 0.3 mm behind the lens's flange"""
    if led == "rgb":
        fl = D - WALL - LENS_FL - 0.2                                                     # the flange's back face
        h = box(LED_X - 8, D - WALL - 7, BTN_Z - 9, 16, 7 + HOLDER_IN, 19)
        h -= box(LED_X - STRIP_W / 2, fl - 0.3 - STRIP_T, BTN_Z - 10, STRIP_W, STRIP_T, 19)
        h -= cyl_y(LED_X, fl - 0.4, BTN_Z, 3.5, 0.6)                                       # the light's way through
    else:
        tube = LED_LEN + 0.3 + LENS_FL + 0.2
        h = cyl_y(LED_X, D - WALL - tube, BTN_Z, LENS_FL_R + 1.6, tube + HOLDER_IN)
        h += box(LED_X - LENS_FL_R - 1.6, D - WALL - tube, BTN_Z, 2 * (LENS_FL_R + 1.6), tube + HOLDER_IN,
                 H - ROOF - BTN_Z + 0.5)
        h -= cyl_y(LED_X, D - WALL - tube - 1, BTN_Z, 2.6, tube + 1)                      # the LED (5 mm)
    h &= prism(outline(WALL - HOLDER_IN), 0, H - ROOF + HOLDER_IN)                       # never through the cut corner
    return h - lens_cuts()


# ---- base
def base():
    b = prism(outline(WALL + FIT), 0, BASE_T)
    for hx, hy in ((3.5, 3.5), (61.5, 3.5), (3.5, 52.5), (61.5, 52.5)):
        b += cyl_z(BX + hx, BY + hy, BASE_T, 3.0, STAND)
        b -= cyl_z(BX + hx, BY + hy, 1.0, 1.15, STAND + 3)                           # M2.5 self-tap
        b -= Pos(BX + hx, BY + hy, BASE_T + STAND - 0.6) * Cone(1.15, 1.75, 0.61,
                                                                align=(Align.CENTER, Align.CENTER, Align.MIN))  # lead-in
    for x, y in BOSSES:                                                              # M3 clearance + head recess
        b -= cyl_z(x, y, -1, 1.7, BASE_T + 2)
        b -= Pos(x, y, -0.01) * Cylinder(3.2, 1.7, align=(Align.CENTER, Align.CENTER, Align.MIN))
        # the recess prints on the bed, so its ceiling would be a ring hanging in the air round the hole: two
        # sacrificial bridge steps instead - a slot as wide as the hole across the recess (its sides bridge from rim
        # to rim), then a square (its two new sides bridge across the slot) - and only then the round hole
        b -= box(x - 3.2, y - 1.7, 1.7 - 0.01, 6.4, 3.4, BRIDGE_STEP + 0.01)
        b -= box(x - 1.7, y - 1.7, 1.7 - 0.01, 3.4, 3.4, 2 * BRIDGE_STEP + 0.01)
    for fx, fy in ((22, 14), (W - 18, 14), (22, D - 14), (W - 30, D - 14)):          # feet recesses (Ø12 rubber)
        b -= cyl_z(fx, fy, -0.01, 6.2, 1.0)
    # reach the microSD from below: a finger's room (35 x 20), out from the board's edge - clear of the feet, the
    # standoffs and the rating plate's field
    b -= box(BX + 3 - 35, BY + 28 - 10, -1, 35, 20, BASE_T + 2)
    # switch bracket: 6x6 tact switches lie on their backs facing the buttons, in pockets 6.3 x 6.3 x 3.7; each leg
    # goes through its own hole in the bracket's back (SW_BACK thick), so the legs stick out behind it to be soldered
    yb = switch_floor() - SW_BACK                # the bracket's back face
    b += box(BTN_X[0] - 8, yb, BASE_T, BTN_X[1] - BTN_X[0] + 16, 6.6 - (3.0 - SW_BACK), BTN_Z + 4.5 - BASE_T)
    for x in BTN_X:
        b -= box(x - 3.15, yb + SW_BACK, BTN_Z - 3.15, 6.3, 3.7, 6.3)
        for lx, lz in SW_LEGS:
            b -= cyl_y(x + lx, yb - 1, BTN_Z + lz, SW_LEG_R, SW_BACK + 1.5)
    return b


# the 6x6 x 5 mm THT tact switch: four legs 6.5 mm apart across the plunger's sides and 4.5 mm along them, 3.5 mm long
SW_LEGS = [(sx * 3.25, sz * 2.25) for sx in (-1, 1) for sz in (-1, 1)]
SW_LEG_R, SW_BACK = 0.65, 1.8            # a leg's hole (legs 0.7 x 0.3; a small printed hole comes out tighter), the back


def switch_floor():
    """where a switch's back face sits: the cap's back at rest - gap - plunger - body"""
    return CAP_REST - 0.5 - 1.5 - 3.7


def switch_ghost(x):
    """one switch as it sits in the bracket: body, plunger, the four legs out of its back (for the fit check)"""
    y0 = switch_floor()
    s = box(x - 3, y0, BTN_Z - 3, 6, 3.5, 6) + cyl_y(x, y0 + 3.5, BTN_Z, 1.75, 1.5)
    for lx, lz in SW_LEGS:
        s += box(x + lx - 0.35, y0 - 3.5, BTN_Z + lz - 0.15, 0.7, 3.5, 0.3)
    return s


# ---- LED lens (clear PETG): a flange that sits in the counterbore + a shaft flush with the front face
def lens():
    c = cyl_y(0, 0, 0, LENS_FL_R, LENS_FL)
    c += cyl_y(0, LENS_FL, 0, LENS_R, WALL + 0.2)
    return c


# ---- button cap: the shaft through the wall + a flange inside that keeps it in
def button():
    c = cyl_y(0, 0, 0, 4.2, CAP_L)
    c += cyl_y(0, 0, 0, 5.6, 1.5)
    return c


# ---- the button tree (print 1): both caps as one part, like an old gamepad's - each cap hangs on a flexible strip
# from an ear, the two ears go on two pins in the shell and the pin ends are melted flat with a soldering iron. The
# strips bend when a cap is pressed (0.8 mm thick, 11-13 mm long: under 1 % strain, ~0.5 N on top of the switch);
# a thin link between the caps keeps it one part without pressing the other switch. It prints flat on its back face
TREE_T, TREE_W = 0.8, 3.0                     # strip thickness (it bends through it) and width
TREE_EARS = ((8.0, 7.0), (56.5, 7.0))         # the pins (x, z): low and outboard, so the strips are long enough
EAR_FLAT_X = 58.85                             # the right ear cut flat here: the universal case's front-panel groove
                                               # has its inner lip from x = 59.15 (the owner's test print, 2026-10-06)
EAR_R, PIN_R, PIN_HOLE_R, PIN_BOSS_R, PIN_MELT = 3.0, 1.0, 1.15, 2.2, 1.4


def tree_strip(p0, p1, w=TREE_W, t=TREE_T):
    """a flat strip of the tree from p0 to p1 (x, z), t thick from the tree's back face (assembled position)"""
    (x0, z0), (x1, z1) = p0, p1
    a = math.atan2(z1 - z0, x1 - x0)
    nx, nz = -math.sin(a) * w / 2, math.cos(a) * w / 2
    pts = [(x0 + nx, z0 + nz), (x1 + nx, z1 + nz), (x1 - nx, z1 - nz), (x0 - nx, z0 - nz)]
    pl = Plane(origin=(0, CAP_REST, 0), x_dir=(1, 0, 0), z_dir=(0, 1, 0))
    return extrude(pl * Polygon(*[(x, -z) for x, z in pts], align=None), amount=t, dir=(0, 1, 0))


def button_tree():
    """the tree where it sits in the case: the caps' flanges against the wall"""
    t = None
    for x in BTN_X:
        c = Pos(x, CAP_REST, BTN_Z) * button()
        t = c if t is None else t + c
    k = 5.6 * 0.7                                                       # where a strip meets its cap's flange
    (lx, lz), (rx, rz) = TREE_EARS
    t += tree_strip((lx, lz), (BTN_X[0] - k, BTN_Z - k))
    t += tree_strip((rx, rz), (BTN_X[1] + k, BTN_Z - k))
    t += tree_strip((BTN_X[0] + 5.1, BTN_Z), (BTN_X[1] - 5.1, BTN_Z), w=2.0, t=0.6)   # the thin link
    for x, z in TREE_EARS:
        e = cyl_y(x, CAP_REST, z, EAR_R, TREE_T)
        if x + EAR_R > EAR_FLAT_X:
            e &= box(x - EAR_R - 1, CAP_REST - 1, z - EAR_R - 1, EAR_FLAT_X - (x - EAR_R - 1), TREE_T + 2, 2 * EAR_R + 2)
        t += e
        t -= cyl_y(x, CAP_REST - 1, z, PIN_HOLE_R, TREE_T + 2)
    return t


def tree_pins():
    """the shell's two pins: a boss from the wall to the tree's front face, then the pin through the ear, PIN_MELT
    left over to melt into a head"""
    p = None
    for x, z in TREE_EARS:
        q = cyl_y(x, CAP_REST + TREE_T, z, PIN_BOSS_R, D - WALL - CAP_REST - TREE_T + 0.01)
        q += cyl_y(x, CAP_REST - PIN_MELT, z, PIN_R, D - WALL - CAP_REST + PIN_MELT + 0.01)
        p = q if p is None else p + q
    return p


LAYERS = {"0.16": (0.2, 0.16), "0.24": (0.24, 0.24)}   # the two Orca profiles: first layer, layer height


def first_layer_at(z, first, lh):
    """the height of the first layer that starts at or above z - where a filament change goes"""
    h = first
    while h < z - 1e-6:
        h += lh
    return round(h, 2)


def layer_number(z, first, lh):
    """the slicer's layer number (its layer slider counts from 1) of the layer printed at height z"""
    return int(round((z - first) / lh)) + 1


def on_bed(part):
    """move a part so it lies on z = 0"""
    bb = part.bounding_box()
    return Pos(-bb.min.X, -bb.min.Y, -bb.min.Z) * part


_TESS = {}                                  # id(solid) -> (solid, vertices, triangles): the same part in many files


def write_parts_3mf(path, label, parts):
    """ONE object of several named parts [(name, solid)], where they stand: a slicer keeps it one object and merges
    the parts where they overlap (a holder in its wall, a panel in its base) into one print. Pass the same solid
    objects to several calls and each is tessellated once"""
    import zipfile
    shift = Compound(children=[p for _, p in parts]).bounding_box().min
    objs, comps = [], []
    for i, (pname, p) in enumerate(parts, 1):
        if id(p) not in _TESS:                 # the solid itself is kept, so its id is never reused
            _TESS[id(p)] = (p,) + tuple(p.tessellate(0.02, 0.2))
        _, vs, ts = _TESS[id(p)]
        # tessellate() gives each face its own vertices: weld the shared ones, else the mesh is open along every edge
        key, idx, uniq = {}, [], []
        for q in vs:
            k = (round(q.X - shift.X, 4), round(q.Y - shift.Y, 4), round(q.Z - shift.Z, 4))
            if k not in key:
                key[k] = len(uniq)
                uniq.append(k)
            idx.append(key[k])
        tris = [(idx[a], idx[b], idx[c]) for a, b, c in ts]
        tris = [t for t in tris if len(set(t)) == 3]
        v = "".join('<vertex x="%.4f" y="%.4f" z="%.4f"/>' % k for k in uniq)
        t = "".join('<triangle v1="%d" v2="%d" v3="%d"/>' % tri for tri in tris)
        objs.append('<object id="%d" name="%s" type="model"><mesh><vertices>%s</vertices><triangles>%s</triangles></mesh></object>'
                    % (i, pname, v, t))
        comps.append('<component objectid="%d"/>' % i)
    n = len(parts) + 1
    model = ('<?xml version="1.0" encoding="UTF-8"?>\n<model unit="millimeter" xml:lang="en-US" '
             'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02"><resources>%s'
             '<object id="%d" name="%s" type="model"><components>%s</components></object></resources>'
             '<build><item objectid="%d"/></build></model>' % ("".join(objs), n, label, "".join(comps), n))
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0" encoding="UTF-8"?>\n<Types xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/'
                   'vnd.openxmlformats-package.relationships+xml"/><Default Extension="model" ContentType="application/'
                   'vnd.ms-package.3dmanufacturing-3dmodel+xml"/></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.'
                   'openxmlformats.org/package/2006/relationships"><Relationship Target="/3D/3dmodel.model" Id="rel0" '
                   'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/></Relationships>')
        z.writestr("3D/3dmodel.model", model)


def shell_print(body, led):
    """a shell as it prints: roof down, the same shell + the LED holder as two parts of one object"""
    return [("shell", Rot(180, 0, 0) * body), ("led-holder", Rot(180, 0, 0) * led_holder(led))]


def write_3mf(parts):
    """3MF per part, already turned the way it prints (shell: roof down, button tree: flat, shafts up), plus one file with
    every part to print (shell, base, the button tree, the lens - clear PETG), for each LED version - the slicer's auto-arrange spreads them over the plates"""
    printable = {
        "shell": on_bed(Rot(180, 0, 0) * parts["shell"]),
        "shell-rgb": on_bed(Rot(180, 0, 0) * parts["shell-rgb"]),
        "base": on_bed(parts["base"]),
        "buttons": on_bed(Rot(90, 0, 0) * parts["buttons"]),           # flat on its back face, the shafts up
        "lens": on_bed(Rot(90, 0, 0) * parts["lens"]),
    }
    body = shell(None)                                                     # one shell for both lights
    for name, p in printable.items():
        if name.startswith("shell"):                                       # + its LED holder, merged by the slicer
            write_parts_3mf(os.path.join(OUT, "ableemstation-%s.3mf" % name), "ableemstation-" + name,
                            shell_print(body, "rgb" if name.endswith("rgb") else "led5"))
            continue
        m = Mesher()
        m.add_shape(p, linear_deflection=0.02, angular_deflection=0.2)
        m.write(os.path.join(OUT, "ableemstation-%s.3mf" % name))
    for shell_name, suffix in (("shell", ""), ("shell-rgb", "-rgb")):
        m = Mesher()
        x = 0.0
        for p in (printable[shell_name], printable["base"], printable["buttons"], printable["lens"]):
            m.add_shape(Pos(x, 0, 0) * p, linear_deflection=0.02, angular_deflection=0.2)
            x += p.bounding_box().size.X + 10
        m.write(os.path.join(OUT, "ableemstation-all-parts%s.3mf" % suffix))


def main():
    parts = {"shell": shell(), "shell-rgb": shell("rgb"), "base": base(), "buttons": button_tree(), "lens": lens()}
    pi = pi_ghost()
    for name, p in parts.items():
        export_step(p, os.path.join(OUT, "ableemstation-%s.step" % name))
        export_stl(p, os.path.join(OUT, "ableemstation-%s.stl" % name))
    write_3mf(parts)
    # assembly: the button tree at rest (flanges against the wall, fronts 2.5 mm proud)
    caps = [parts["buttons"]]
    lens_in = Pos(LED_X, D - WALL - LENS_FL - 0.2, BTN_Z) * parts["lens"]
    asm = Compound(children=[parts["shell"], parts["base"], lens_in] + caps, label="ABleemStation")
    export_step(asm, os.path.join(OUT, "ableemstation-assembly.step"))
    viewer = os.path.join(OUT, "viewer")
    os.makedirs(viewer, exist_ok=True)
    for name, p in (("shell", parts["shell"]), ("shell-rgb", parts["shell-rgb"]), ("base", parts["base"]),
                    ("caps", Compound(children=caps)), ("pi", pi), ("lens", lens_in)):
        export_stl(p, os.path.join(viewer, name + ".stl"), tolerance=0.05, angular_tolerance=0.2)
    for f in os.listdir(viewer):
        if f.endswith(".glb"):
            os.remove(os.path.join(viewer, f))
    # fit check: the Pi must not touch the case except where its ports pass through the windows
    for name, p in (("shell", parts["shell"]), ("shell-rgb", parts["shell-rgb"]), ("base", parts["base"])):
        v = (p & pi).volume
        print("overlap pi x %s: %.2f mm3" % (name, v))
    # the LED holders: each reaches into the shell (one print, merged), the lens window stays clear
    body = shell(None)
    for led in ("led5", "rgb"):
        joint = (led_holder(led) & body).volume
        clear = (led_holder(led) & lens_cuts()).volume
        out = (led_holder(led) - prism(outline(), 0, H)).volume
        print("LED holder %s: overlaps the shell by %.1f mm3, in the lens window %.2f mm3, outside %.2f mm3" % (led, joint, clear, out))
        assert joint > 10 and clear < 0.01 and out < 0.001, "the %s holder is not one with the shell, blocks the lens or shows outside" % led
    # the button tree: on its pins without touching the shell elsewhere, clear of the base and the switches
    sws = switch_ghost(BTN_X[0]) + switch_ghost(BTN_X[1])
    for name, other in (("shell", parts["shell"]), ("shell-rgb", parts["shell-rgb"]), ("base", parts["base"]), ("switches", sws)):
        v = (parts["buttons"] & other).volume
        print("button tree x %s: %.2f mm3" % (name, v))
        assert v < 0.01, "the button tree hits the %s (%.2f mm3)" % (name, v)
    # the switches: body and legs clear of the bracket, each leg through the back to solder behind it
    for x in BTN_X:
        v = (switch_ghost(x) & parts["base"]).volume
        print("switch at x=%g x base: %.2f mm3" % (x, v))
        assert v < 0.01, "the switch at x=%g hits its bracket (%.2f mm3)" % (x, v)
    print("switch legs stick out %.1f mm behind the bracket" % (3.5 - SW_BACK))
    for name in ("shell", "shell-rgb"):
        print("overlap lens x %s: %.2f mm3" % (name, (lens_in & parts[name]).volume))
    # every screw must sit inside: the insert hole clear of the walls (0.8 mm of boss left), the countersink inside the
    # plate's edge (0.5 mm left) - a boss too close to a wall or a cut corner fails here, not on the printer
    inner, plate = prism(outline(WALL + 0.8), 0, H), prism(outline(WALL + FIT + 0.5), -1, BASE_T + 2)
    for x, y in BOSSES:
        out = (cyl_z(x, y, 0, INSERT_R, H - ROOF) - inner).volume + (cyl_z(x, y, 0, 3.2, BASE_T) - plate).volume
        print("screw at (%g, %g): %s" % (x, y, "ok" if out < 0.01 else "TOO CLOSE TO A WALL (%.2f mm3 outside)" % out))
        assert out < 0.01, "boss (%g, %g) too close to a wall" % (x, y)
    change = {name: first_layer_at(H - BAND, first, lh) for name, (first, lh) in LAYERS.items()}
    change_n = {name: layer_number(change[name], first, lh) for name, (first, lh) in LAYERS.items()}
    # the sizes the viewer needs (so it never carries its own copies)
    json.dump({"W": W, "D": D, "H": H, "BAND": BAND, "LED": [LED_X, D - 0.2, BTN_Z], "LED_R": LENS_R, "layer_change_mm": change, "layer_change_n": change_n,
               "top": {"c": [43, 85, H - 0.35], "w": 61, "h": 17}, "front": {"c": [36, D - 0.35, BTN_Z - 9.5], "w": 43, "h": 4.6},
               "filament_change_mm": round(H - BAND, 1)}, open(os.path.join(viewer, "params.json"), "w", newline="\n"), indent=1)
    print("height %.1f mm; filament change: %.2f mm (layer %d) with 0.16 mm layers, %.2f mm (layer %d) with 0.24 mm"
          % (H, change["0.16"], change_n["0.16"], change["0.24"], change_n["0.24"]))
    print("written to", OUT)


if __name__ == "__main__":
    main()
