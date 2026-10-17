"""ABleemStation universal: one case for the Raspberry Pi 2B, 3B, 3B+, 4B and 5, with the port walls as separate panels.
The shell, the base, the buttons and the lens are the Pi 3 case's (make_case.py); three wall openings take a panel each:
  back   (the board's long edge: power, HDMI, audio)   back-pi23 / back-pi4 / back-pi5 / back-blank
  right  (the short edge: USB + Ethernet)              right-pi23 / -pi4 / -pi5, each also "-front" (the USB block
                                                       furthest from the Ethernet closed - it feeds the front USB), blank
  front  (between the buttons and the LED)             front-usb (two windows) / front-blank
The front and right panels print WITH the shell: one 3MF object per option (the shell body, the LED holder and the two
panels as parts), each panel filling its opening and grooves fully and reaching JOINT_IN into the shell around it, so
the slicer welds it all into one solid - the panel choice stays, the panel is no separate part any more. The back panel
prints with the base the same way (the bottom: base + back panel). The Pi, the switches and the two front USB sockets
on their pedestal are fitted on the bottom, and the shell slides down over it all; the back panel's tongue runs up
the back opening's grooves and ends in a groove in the roof. The Pi's right-edge ports reach into the right wall, so
each right panel has relief channels inside, from the shell's bottom edge up to the port windows.
The back panels also come on their own, printed standing (the same two colours at the same line). Shells: passive (the Pi 3 case's
hidden roof vents) and active (a longer, denser vent field over the Raspberry Pi 5 Active Cooler), each for the plain
LED and the RGB pixel. Port positions: Raspberry Pi Ltd's mechanical drawings (3B+, 4B, 5).
Writes ../files/universal/ (STEP, STL, 3MF, viewer/). Run after make_case.py:  python make_universal.py"""
import json
import os

from build123d import Compound, Mesher, Plane, Polygon, Pos, Rot, export_step, export_stl, extrude

from make_case import (BASE_T, BT, BX, BY, BZ, D, FIT, H, ROOF, W, WALL, BAND, LED_X, BTN_Z, BTN_X, CAP_REST, LENS_FL,
                       LENS_R, LAYERS, base, box, button_tree, cyl_y, cyl_z, first_layer_at, hull, layer_number, led_holder, lens, on_bed, outline, prism, shell,
                       shell_print, write_parts_3mf)

OUT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "files", "universal"))
os.makedirs(os.path.join(OUT, "viewer"), exist_ok=True)

C = 0.15                     # panel clearance in its opening, each side
TG, TGC = 1.2, 0.15          # tongue thickness (the panel's inner half) and its clearance in the groove
TD = 1.2                     # how far a tongue reaches into its groove
RIB = 1.45                   # the inner lip that closes a groove inside a straight wall
EASE = 0.15                  # the shell's opening and grooves this much wider on every side than C/TGC alone, so the
                             # top slides over the standing panels more easily (the owner's test print, 2026-10-06)
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


# the panel's tab: it stands in a rebate along the base's edge (seat at z = SEAT), its underside first rising from the
# panel, then flat - printed standing it hangs over the bed, so the -ears files carry props under it (tab_props)
SEAT = BASE_T - 1.0
TAB = [(WALL - 0.3, SEAT - 0.8), (WALL + 0.8, SEAT), (WALL + 2.5, SEAT), (WALL + 2.5, BASE_T + 1.7), (WALL - 0.3, BASE_T + 1.7)]


def cut_opening(s, name):
    wall, a0, a1, _, rz, ribs = OPENINGS[name]
    v0, v1 = WALL - TG - TGC - EASE, WALL + TGC + EASE         # the groove's span across the wall
    g = TD + 0.2 + EASE                                        # how far a groove runs past the opening's end
    for end, on in zip((a0 - g - RIB, a1), ribs):              # the inner lips first, so the grooves cut through them
        if on:
            s += wbox(wall, end, v1 - 0.01, rz, g + RIB, RIB, ZT - rz + 0.01)
    s -= wbox(wall, a0 - EASE, -1, -1, a1 - a0 + 2 * EASE, WALL + 1.01, ZT + 1)              # the opening
    s -= wbox(wall, a0 - g, v0, -1, a1 - a0 + 2 * g, v1 - v0, ZT + 1 + g)                    # the grooves
    return s


def panel(name, cuts=()):
    """the bare panel for an opening, minus the port windows (world-space solids)"""
    wall, a0, a1, (f0, f1), _, _ = OPENINGS[name]
    p = wbox(wall, a0 + C, 0, 0, a1 - a0 - 2 * C, WALL, ZT - C)                              # the outer plate
    p += wbox(wall, a0 - TD, WALL - TG, 0, a1 - a0 + 2 * TD, TG, ZT + TD)                    # the tongue
    p += wprofile(wall, f0, f1 - f0, TAB)                      # the tab that stands in the base's rebate
    p -= prism(outline(), BAND - 1.2, 1.2) - prism(outline(0.8), BAND - 1.3, 1.4)          # the waist groove runs on
    for c in cuts:
        p -= c
    return p


FUSED = ("front", "right")      # the openings whose panel prints with the shell
HULL = hull()


def fused_panel(name, cuts=()):
    """a panel that prints with the shell (a part of its 3MF object): no clearance, no tongue - it fills the opening and
    its grooves fully and reaches JOINT_IN into the wall's sides, the roof and the inner lips, so the slicer welds it
    to the shell along every edge; the outside is the plain wall again (the waist groove runs on)"""
    wall, a0, a1, _, rz, ribs = OPENINGS[name]
    v1 = WALL + TGC + EASE                                     # the groove's inner side
    g = TD + 0.2 + EASE                                        # how far a groove runs past the opening's end
    span = a1 - a0 + 2 * (g + JOINT_IN)
    p = wbox(wall, a0 - g - JOINT_IN, 0, 0, span, WALL, ZT + JOINT_IN)                        # the wall, opening + grooves
    p += wbox(wall, a0 - g - JOINT_IN, 0, ZT, span, v1 + JOINT_IN, g + JOINT_IN)              # the grooves' top, in the roof
    for u, on in zip((a0 - g, a1), ribs):                      # the gap between the wall and an inner lip
        if on:
            p += wbox(wall, u, WALL - 0.01, rz, g, v1 - WALL + JOINT_IN + 0.01, ZT - rz + 0.01)
    p &= HULL                                                  # nothing past the soft top edge
    p -= prism(outline(), BAND - 1.2, 1.2) - prism(outline(0.8), BAND - 1.3, 1.4)          # the waist groove
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
        return right_reliefs(model)
    eth, usb = ETH_USB[model]
    c = [box(W - WALL - 1, BY + eth - 8.8, BT - 0.8, WALL + 2, 17.6, 15.1)]               # Ethernet
    for yc in (usb[:1] if front_usb else usb):                                           # usb[1]: the block furthest from the Ethernet
        c.append(box(W - WALL - 1, BY + yc - 7.4, BT - 0.8, WALL + 2, 14.8, 17.6))
    if front_usb:                                                                        # the closed block still pokes 0.1 mm past the
        c.append(box(W - WALL - 0.01, BY + usb[1] - 7.4, BT - 0.8, 1.01, 14.8, 17.6))   # board edge: a 1 mm relief inside
    return c + right_reliefs(model)


# the ports on the board's right edge reach past it into the wall (USB and Ethernet 0.1 mm, the Pi 5's Ethernet 1.0 mm).
# The shell slides down over the board, so in the shell's frame each port comes up from its bottom edge: a channel
# inside the wall under each port window, RELIEF_FIT deeper than the port reaches, as wide as the window
RELIEF_FIT = 0.3


def right_ports(model):
    """(centre along the edge, window width, window height, how far the port reaches into the wall) per port"""
    eth, usb = ETH_USB[model]
    ports = [(eth, 17.6, 15.1, (3.0 if model == "pi5" else 2.1) - 2.0)]
    return ports + [(yc, 14.8, 17.6, 2.1 - 2.0) for yc in usb]


def right_reliefs(model):
    """the channels for a board's right-edge ports; a blank panel gets every board's, so any board fits under it"""
    models = ETH_USB if model not in ETH_USB else (model,)
    return [box(W - WALL - 0.01, BY + yc - w / 2, -1, reach + RELIEF_FIT + 0.01, w, BT - 0.8 + h + 1)
            for m in models for yc, w, h, reach in right_ports(m)]


def swept_ports(model):
    """the board's right-edge ports swept down to the shell's bottom edge: what they pass while the shell goes on"""
    eth, usb = ETH_USB[model]
    s = box(BX + 85 - 21 + (3.0 if model == "pi5" else 2.1), BY + eth - 8, -1, 21, 16, BT + 13.5 + 1)
    for yc in usb:
        s += box(BX + 85 - 17 + 2.1, BY + yc - 6.6, -1, 17, 13.2, BT + 16 + 1)
    return s


# front USB: two USB-A sockets (a THT "USB-A female, 180 degrees" part: a 13.1 x 5.7 x 14.1 mm shell, two mounting
# legs under it about 10 mm from its front) on a small board, screwed to a pedestal of the base,
# their fronts 0.3 mm behind the panel; the panel has only the plug windows, in a 1.4 mm recess (1 mm of panel left)
# so a plug still goes in its full depth
USB_X, USB_Z, USB_L = (74.0, 94.0), 17.0, 14.1
USB_W, USB_H = 13.1, 5.7
USB_FRONT = D - WALL - 0.3


# the sockets come on the common "USB-A female to DIP" breakout board: a 17 x 17 x 1.6 mm FR4 board, the socket on top
# with its shell sticking out past the board's front edge, two 3 mm mounting holes 12 mm apart whose centres are 11 mm
# behind that edge, the four DIP pins (VBUS, D-, D+, GND, 2.54 mm) 4 mm behind the holes. The board lies flat on a
# pedestal and two ~1.85 mm sheet-metal screws (straight into the plastic) hold it; a step in front of the board carries the shell's overhang and
# sets the board's front-back position
PCB, PCB_T = 17.0, 1.6
PCB_OVER = 5.4                      # how far the shell's front sticks out past the board (its legs ~10 mm behind the front,
                                    # 4.6 mm behind the board's edge) - measure one when they come and set it here
PCB_HOLE_Y, PCB_HOLE_X, PCB_DIP_Y = 11.0, 6.0, 15.2   # from the board's front edge / from its centre line
PCB_FIT = 0.3                       # the step's gap to the board's front edge
SOCKET_LIFT = 1.3                   # the socket's shell sits this much above the board's top (the owner's test print,
                                    # 2026-10-06: the pedestals 1.3 mm too high, the socket above the panel's window)
SCREW_R = 0.85                      # a ~1.85 mm sheet-metal screw's hole, through the pedestal and the plate (the test
                                    # print: 1.6 mm blind pilots too tight and too short)


def board_z():
    """the shell's underside and the board's underside (= the pedestal's top)"""
    z0 = USB_Z - USB_H / 2
    return z0, z0 - SOCKET_LIFT - PCB_T


def usb_sockets():
    """the sockets on their boards as ghosts for the fit check: shell, board, the solder tails and pins under it"""
    s = None
    for x in USB_X:
        z0, zb = board_z()                                                                  # shell / board underside
        y0 = USB_FRONT - PCB_OVER                                                           # the board's front edge
        b = box(x - USB_W / 2, USB_FRONT - USB_L, z0, USB_W, USB_L, USB_H)
        b += box(x - PCB / 2, y0 - PCB, zb, PCB, PCB, PCB_T)                                # the board
        b += box(x - 4.0, y0 - 8.3, zb - 1.5, 8.0, 2.0, 1.51)                              # the socket's pins + solder
        b += box(x - 4.4, y0 - PCB_DIP_Y - 1.0, zb - 1.5, 8.8, 2.0, 1.51)                  # the DIP row's solder
        for sx in (-1, 1):                                                                  # the legs' solder
            b += box(x + sx * PCB_HOLE_X - 1.0, y0 - 4.6 - 1.0, zb - 1.5, 2.0, 2.0, 1.51)
        s = b if s is None else s + b
    return s


def usb_cradle(x):
    """one board's pedestal: flat under the board, two screw holes, pockets for the solder tails (the socket's pins
    and legs, the DIP row - open to the back for the wires), and a step in front that carries the shell's overhang"""
    z0, zb = board_z()                         # the shell's underside, the board's underside = the pedestal's top
    y0 = USB_FRONT - PCB_OVER                  # the board's front edge
    y_back = y0 - PCB - 0.5
    y_front = USB_FRONT - 2.8                  # the step stops 2.8 mm short of the shell's front (the front panel's foot)
    hw = PCB / 2 + 0.5
    c = box(x - hw, y_back, BASE_T - 0.01, 2 * hw, y0 - y_back, zb - BASE_T + 0.01)                   # the pedestal
    c += box(x - USB_W / 2 + 0.5, y0 + PCB_FIT, BASE_T - 0.01, USB_W - 1.0, y_front - y0 - PCB_FIT,
             z0 - BASE_T + 0.01)                                                                        # the step
    for sx in (-1, 1):
        c -= cyl_z(x + sx * PCB_HOLE_X, y0 - PCB_HOLE_Y, -1, SCREW_R, zb + 2)                          # screw holes, through
        c -= box(x + sx * PCB_HOLE_X - 1.5, y0 - 4.6 - 1.5, zb - 2.5, 3.0, 3.0, 3)                     # the legs' tails
    c -= box(x - 4.8, y0 - 9.8, zb - 2.5, 9.6, 3.5, 3)                                                  # socket pins' tails
    c -= box(x - 5.2, y_back - 1, zb - 2.5, 10.4, (y0 - PCB_DIP_Y + 1.6) - (y_back - 1), 3)            # DIP row, open back
    return c


def front_usb_panel():
    p = fused_panel("front")
    for x in USB_X:
        p -= box(x - 6.5, D - WALL - 1, USB_Z - 2.8, 13.0, WALL + 2, 5.6)                      # the plug's window
        p -= box(x - 9.0, D - 1.4, USB_Z - 5.0, 18.0, 2.0, 10.0)                               # the plug's recess
    return p


# the one-piece bottom: the panel must become one with the base, so under each opening the base fills its rebate,
# the 45-degree pocket and the fit gap to the panel, and reaches JOINT_IN into the panel's plate - the slicer then
# merges the overlapping parts into one solid along the whole panel, not just on the tab's line
JOINT_IN = 0.6


def joint_fill(name):
    wall, a0, a1, _, _, _ = OPENINGS[name]
    v0, v1 = WALL - JOINT_IN, WALL - 0.5 + 2.5 + 0.65 + 0.05          # into the plate .. just past the rebate's inner face
    return wbox(wall, a0 + C, v0, 0, a1 - a0 - 2 * C, v1 - v0, BASE_T)


def bottom_base():
    """the base of the one-piece bottom: uni_base with the back panel's joint filled"""
    return uni_base() + joint_fill("back")


def uni_base():
    """the Pi 3 case's base + a rebate under the back panel's tab + the front USB sockets' pedestal (the front and
    right panels print with the shell, so the base has a plain edge there)"""
    b = base()
    for name, (wall, a0, a1, (f0, f1), _, _) in OPENINGS.items():
        if name in FUSED:
            continue
        b -= wbox(wall, f0 - 0.3, WALL - 0.5, SEAT, f1 - f0 + 0.6, 2.5 + 0.65, 3)                # the seat
        b -= wbox(wall, f0 - 0.3, WALL - 0.5, SEAT - 1.2, f1 - f0 + 0.6, 1.5, 3)                 # room for the 45-degree start
    for x in USB_X:
        b += usb_cradle(x)                                                                      # the boards' pedestals
    return b


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


def write_bottom(name, parts):
    """the base and its three panels as ONE object of four named parts, standing where they are assembled: a slicer
    keeps it one object and welds the parts where they touch (each panel's tab on its seat), so the base and the panels
    print as one piece - no ears, no props, nothing to assemble"""
    write_parts_3mf(os.path.join(OUT, "ableemstation-%s.3mf" % name), "ableemstation-" + name, parts)


# breakaway ears: a panel prints standing on a 2.4 mm edge, about 10 times as tall as it is thick, so each end gets an
# outrigger - a fin across the panel on a two-layer foot - that holds it upright and comes off by hand afterwards. The
# fin stands 0.4 mm off the tongue's end and hangs on two small bridges there: the tongue's end lives in the wall's
# groove, so what is left of a bridge never shows (trim it flush with a knife so the tongue slides in)
EAR_T, EAR_GAP, EAR_OUT, EAR_FOOT = 1.2, 0.4, 8.0, (6.5, 0.4)   # fin thickness, gap, reach each side, foot length + height
EAR_H = 0.6                                                     # fin height, of the panel's
EAR_RELIEF = 1.2      # the first layers squash wider (elephant foot): the fin keeps away from the tongue below this


def ears(name):
    """the two outriggers of an opening's panel, with their bridges (world space, like panel())"""
    wall, a0, a1, _, _, _ = OPENINGS[name]
    top = (ZT + TD) * EAR_H
    vc = WALL - TG / 2                                         # the tongue's middle, across the wall
    fin = [(-EAR_OUT, 0), (WALL + EAR_OUT, 0), (WALL + EAR_OUT, EAR_FOOT[1]), (vc + 0.6, top), (vc - 0.6, top),
           (-EAR_OUT, EAR_FOOT[1])]
    foot = [(-EAR_OUT, 0), (WALL + EAR_OUT, 0), (WALL + EAR_OUT, EAR_FOOT[1]), (-EAR_OUT, EAR_FOOT[1])]
    e = None
    for end, out in ((a0 - TD, -1), (a1 + TD, 1)):             # the tongue's two ends; out = away from the panel
        f0 = end + out * EAR_GAP if out > 0 else end - EAR_GAP - EAR_T
        part = wprofile(wall, f0, EAR_T, fin)
        part += wprofile(wall, f0 if out > 0 else f0 - EAR_FOOT[0] + EAR_T, EAR_FOOT[0], foot)
        # in line with the tongue the fin and its foot start only above EAR_RELIEF, so the squashed first layers
        # cannot weld them to the tongue's foot - the nearest material down there is the foot, a fin's thickness away
        part -= wbox(wall, f0 - 0.01, WALL - TG - 0.6, -1, EAR_T + 0.02, TG + 1.2, EAR_RELIEF + 1)
        for z in (3.0, top - 3.0):                             # two bridges, 1 x 0.8 mm, across the gap into the tongue
            u = end - EAR_GAP - 0.05 if out < 0 else end - 0.05
            part += wbox(wall, u, WALL - TG + 0.1, z, EAR_GAP + 0.1, TG - 0.2, 0.8)
        e = part if e is None else e + part
    return e


# breakaway props under the tab: standing, the tab's underside hangs 1.4-2 mm over the bed (its 45-degree start is too
# short to carry it), so a row of fins on a two-layer foot holds it up. They stop SUP_GAP under it - one layer of air,
# the way a slicer's support leaves it - and SUP_SIDE off the panel's inner face, so nothing welds; the row comes out
# in one piece
SUP_T, SUP_PITCH, SUP_GAP, SUP_SIDE, SUP_FOOT = 0.9, 4.0, 0.25, 0.5, 0.4   # fin, fin pitch, gap under the tab, side gap, foot


def tab_props(name):
    """the fins under an opening's panel tab, on their foot (world space, like panel())"""
    wall, _, _, (f0, f1), _, _ = OPENINGS[name]
    (v0, z0), (v1, z1), _, (v2, _), _ = TAB
    vs = WALL + SUP_SIDE                                        # the fins start clear of the panel's inner face
    zs = z0 + (vs - v0) * (z1 - z0) / (v1 - v0)                 # the tab's underside there, on its 45-degree start
    fin = [(vs, 0), (v2, 0), (v2, z1 - SUP_GAP), (v1, z1 - SUP_GAP), (vs, zs - SUP_GAP)]
    p = wprofile(wall, f0, f1 - f0, [(vs, 0), (v2, 0), (v2, SUP_FOOT), (vs, SUP_FOOT)])
    n = int((f1 - f0 - SUP_T) // SUP_PITCH) + 1
    first = f0 + (f1 - f0 - SUP_T - (n - 1) * SUP_PITCH) / 2
    for i in range(n):
        p += wprofile(wall, first + i * SUP_PITCH, SUP_T, fin)
    return p


def standing(name, p):
    """a panel as it prints: standing on its bottom edge, its length along x"""
    return on_bed(Rot(0, 0, 90) * p if name.startswith("right") else p)


def shell_options():
    """the shell's panel options: (file suffix, right panel, front panel); pi models: the front USB with the rear block
    that feeds it closed (usb) or open (usb-open), or a blank front; the blank right wall: either front"""
    o = []
    for m in ("pi23", "pi4", "pi5"):
        o += [("%s-usb" % m, "right-%s-front" % m, "front-usb"), ("%s-usb-open" % m, "right-" + m, "front-usb"),
              ("%s-blank" % m, "right-" + m, "front-blank")]
    return o + [("blank-usb", "right-blank", "front-usb"), ("blank-blank", "right-blank", "front-blank")]


def main():
    shells, bodies = {}, {}
    for kind, vents in (("", None), ("-active", ACTIVE_VENTS)):
        s = shell(None, vents)                         # one shell for both lights; the LED holder is a part of its own
        for name in OPENINGS:
            s = cut_opening(s, name)
        bodies[kind] = s
        for led, suffix in (("led5", ""), ("rgb", "-rgb")):
            shells["uni-shell%s%s" % (kind, suffix)] = s + led_holder(led)
    panels, fused = {}, {}                             # back: the slide-in panels; front + right: print with the shell
    for m in ("pi23", "pi4", "pi5", "blank"):
        panels["back-" + m] = panel("back", back_cuts(m))
        fused["right-" + m] = fused_panel("right", right_cuts(m))
        if m != "blank":
            fused["right-%s-front" % m] = fused_panel("right", right_cuts(m, True))
    fused["front-usb"] = front_usb_panel()
    fused["front-blank"] = fused_panel("front")

    # STEP / STL: the shell bodies (with their openings) and every panel on its own, where it stands in the case
    for name, p in list(shells.items()) + [("panel-" + n, p) for n, p in list(panels.items()) + list(fused.items())]:
        export_step(p, os.path.join(OUT, "ableemstation-%s.step" % name))
        export_stl(p, os.path.join(OUT, "ableemstation-%s.stl" % name))
    # printed: the shell per option = ONE object of four parts (shell, LED holder, front panel, right panel), roof down;
    # every solid turned once, so each is tessellated once for all the files it is in
    down = lambda p: Rot(180, 0, 0) * p                # noqa: E731
    fdown = {n: down(p) for n, p in fused.items()}
    for kind, body in bodies.items():
        bdown = down(body)
        for led, suffix in (("led5", ""), ("rgb", "-rgb")):
            hold = down(led_holder(led))
            for opt, right, front in shell_options():
                name = "uni-shell%s%s-%s" % (kind, suffix, opt)
                write_parts_3mf(os.path.join(OUT, "ableemstation-%s.3mf" % name), "ableemstation-" + name,
                                [("shell", bdown), ("led-holder", hold), ("panel-front", fdown[front]), ("panel-right", fdown[right])])
    print("shells: %d options each of 4 (passive / active x LED / RGB), shell + LED holder + front + right panel as one object"
          % len(shell_options()))
    # each fused panel welds into the shell all round its opening and shows nothing outside it
    for n, p in fused.items():
        joint = (p & bodies[""]).volume
        out = (p - HULL).volume
        print("panel %s: overlaps the shell by %.0f mm3, outside the shell's form %.3f mm3" % (n, joint, out))
        assert joint > 20 and out < 0.001, "panel %s is not one with the shell" % n

    # the back panels on their own, printed standing (a board swap or a reprint of the back wall)
    flats = {n: standing(n, p) for n, p in panels.items()}
    for n, p in flats.items():
        write_3mf("panel-" + n, p)
        bb = p.bounding_box().size
        print("panel %s prints %.1f x %.1f x %.1f mm (standing)" % (n, bb.X, bb.Y, bb.Z))
    m = Mesher()                                       # every back panel on one plate, in a row
    x = 0.0
    for n, p in flats.items():
        m.add_shape(Pos(x, 0, 0) * p, linear_deflection=0.02, angular_deflection=0.2)
        x += p.bounding_box().size.X + 8
    m.write(os.path.join(OUT, "ableemstation-panels-all.3mf"))
    # the same panels with their breakaway ears and tab props; the ears touch a panel only through the bridges, the
    # props not at all
    eared, m, x = {}, Mesher(), 0.0
    for n, p in panels.items():
        e, t = ears("back"), tab_props("back")
        bridges = (e & p).volume
        assert 0 < bridges < 3.0, "panel %s: the ears touch it with %.2f mm3, not just through the bridges" % (n, bridges)
        assert (t & p).volume < 1e-6, "panel %s: the tab props touch it" % n
        eared[n] = standing(n, p + e + t)
        write_3mf("panel-%s-ears" % n, eared[n])
        m.add_shape(Pos(x, 0, 0) * eared[n], linear_deflection=0.02, angular_deflection=0.2)
        x += eared[n].bounding_box().size.X + 4
    m.write(os.path.join(OUT, "ableemstation-panels-all-ears.3mf"))
    print("panels with ears + tab props: %s (bridges %.2f mm3 per panel)" % (", ".join(eared), bridges))
    # the panels' filament change: printed bottom-up, the first layer at or above the shell's colour line
    # (the shell prints roof-down: its change at H - BAND from the roof is the line H - change from the bottom)
    pchange = {k: first_layer_at(H - first_layer_at(H - BAND, f, lh), f, lh) for k, (f, lh) in LAYERS.items()}
    pchange_n = {k: layer_number(pchange[k], f, lh) for k, (f, lh) in LAYERS.items()}
    print("panels: filament change at %.2f mm (layer %d) with 0.16 mm layers, %.2f mm (layer %d) with 0.24 mm"
          % (pchange["0.16"], pchange_n["0.16"], pchange["0.24"], pchange_n["0.24"]))

    b = uni_base()
    export_step(b, os.path.join(OUT, "ableemstation-uni-base.step"))
    export_stl(b, os.path.join(OUT, "ableemstation-uni-base.stl"))
    write_3mf("uni-base", on_bed(b))
    # the bottom per back panel: the base (joint filled) + the back panel, one object to print in one go: the parts
    # overlap along the panel, so they print as one solid
    bb = bottom_base()
    for sname, s in shells.items():
        v = (bb & s).volume
        assert v < 0.01, "the bottom's joint fill hits %s: %.2f mm3" % (sname, v)
    for model in ("pi23", "pi4", "pi5"):
        assert (bb & pi_ghost(model)).volume < 0.01, "the bottom's joint fill hits the " + model
    for model in ("pi23", "pi4", "pi5", "blank"):
        p = panels["back-" + model]
        joint = (p & bb).volume
        assert joint > 20, "bottom %s: the back panel overlaps the base by %.1f mm3 only - not one piece" % (model, joint)
        write_bottom("uni-bottom-" + model, [("base", bb), ("panel-back", p)])
    print("bottoms: base + back panel as one object, 4 options; the panel overlaps the base by %.0f mm3" % (panels["back-pi4"] & bb).volume)
    usb = usb_sockets()
    # fit checks: no board touches a shell, a panel or the base; a back panel fills its opening without touching the
    # shell; the shell with its fused panels slides down over the board (its right-edge ports swept to the bottom edge)
    bad = 0
    for model in ("pi23", "pi4", "pi5"):
        for sname, s in shells.items():
            g = pi_ghost(model, cooler=(model == "pi5" and "active" in sname))
            v = (s & g).volume
            bad += v > 0.01
            print("overlap %s x %s: %.2f mm3" % (model, sname, v))
        g, sw = pi_ghost(model), swept_ports(model)
        for n, p in list(panels.items()) + list(fused.items()):
            if model in n or n.endswith("-blank") or n == "front-usb":   # the blank right wall: for any board
                v = (p & g).volume + (p & sw).volume
                bad += v > 0.01
                if v > 0.01:
                    print("overlap %s x panel-%s (in place or sliding on): %.2f mm3" % (model, n, v))
        v = max((s & sw).volume for s in shells.values())
        bad += v > 0.01
        print("overlap %s x base: %.2f mm3; its ports sliding into the shells: %.2f mm3" % (model, (b & g).volume, v))
    for n, p in panels.items():
        v = (p & shells["uni-shell"]).volume + (p & shells["uni-shell-active-rgb"]).volume + (p & b).volume
        bad += v > 0.01
        print("panel %s x shell/base: %.2f mm3" % (n, v))
    for n, p in fused.items():
        v = (p & b).volume
        bad += v > 0.01
        print("panel %s (with the shell) x base: %.2f mm3" % (n, v))
    v = (usb & b).volume + (usb & fused["front-usb"]).volume + (usb & shells["uni-shell-rgb"]).volume
    bad += v > 0.01
    print("front USB sockets x base/panel/shell: %.2f mm3" % v)
    tree = button_tree()                       # its ears clear of the front panel's groove lips (the test print)
    v = max((tree & shells[n]).volume for n in shells) + max((tree & fused[n]).volume for n in ("front-usb", "front-blank"))
    bad += v > 0.01
    print("button tree x shells/front panels: %.2f mm3" % v)
    # the boards: each lies on its pedestal, a screw pilot under each hole (air in it, plastic round it), and the step
    # carries the shell's overhang
    z0, zb = board_z()
    y0 = USB_FRONT - PCB_OVER
    hit = lambda px, py, pz: (box(px - 0.05, py - 0.05, pz - 0.05, 0.1, 0.1, 0.1) & b).volume > 1e-5   # noqa: E731
    for x in USB_X:
        ok = hit(x, y0 - 12.5, zb - 0.1) and hit(x, USB_FRONT - 3.5, z0 - 0.1)               # under the board, the step
        for sx in (-1, 1):
            hx, hy = x + sx * PCB_HOLE_X, y0 - PCB_HOLE_Y
            ok = ok and not hit(hx, hy, zb - 3) and hit(hx + SCREW_R + 0.4, hy, zb - 3)
        bad += not ok
        print("USB board at x=%g: %s" % (x, "seated, 2 screw pilots, shell carried" if ok else "NOT SEATED"))
    assert not bad, "%d fit check(s) failed" % bad

    # the viewer: the four shells (bodies), the base, caps, lens, each board's back panel and ghost; the front and
    # right panels ride with the shell
    view = os.path.join(OUT, "viewer")
    for f in os.listdir(view):                         # no mesh left over from an older set of parts
        if f.endswith(".stl"):
            os.remove(os.path.join(view, f))
    caps = [button_tree()]
    lens_in = Pos(LED_X, D - WALL - LENS_FL - 0.2, BTN_Z) * lens()
    vparts = {"shell": shells["uni-shell"], "shell-active": shells["uni-shell-active"], "shell-rgb": shells["uni-shell-rgb"],
              "shell-active-rgb": shells["uni-shell-active-rgb"], "base": b,
              "caps": Compound(children=caps), "lens": lens_in, "usb-sockets": usb}
    for n, p in fused.items():
        vparts[n] = p
    for model in ("pi23", "pi4", "pi5"):
        vparts["back-" + model] = panels["back-" + model]
        vparts["pi-" + model] = pi_ghost(model, cooler=(model == "pi5"))
    for n, p in vparts.items():
        export_stl(p, os.path.join(view, n + ".stl"), tolerance=0.05, angular_tolerance=0.2)
    json.dump({"W": W, "D": D, "H": H, "BAND": BAND, "LED": [LED_X, D - 0.2, BTN_Z], "LED_R": LENS_R,
               "top": {"c": [43, 85, H - 0.35], "w": 61, "h": 17}, "front": {"c": [36, D - 0.35, BTN_Z - 9.5], "w": 43, "h": 4.6},
               "models": {"pi23": "Pi 2B / 3B / 3B+", "pi4": "Pi 4B", "pi5": "Pi 5"},
               # the stickers without a recess: the side stripe on the dark band of the vent side (the side away from the
               # ports), the rating plate on the base's underside between the feet, the screws and the microSD window
               "side": {"c": [-0.05, 60, 5.2], "w": 80, "h": 8}, "bottom": {"c": [89, 57, -0.05], "w": 54, "h": 34},
               "bottoms": {"pi23": "sticker-bottom", "pi4": "sticker-bottom-pi4", "pi5": "sticker-bottom-pi5"},
               # the port labels on the back panel, above its windows (the panel's face: x 48.7..113.9, z up to the roof)
               "back": {"c": [81.25, -0.05, 20.6], "w": 62, "h": 5},
               "backs": {"pi23": "sticker-back-pi23", "pi4": "sticker-back-pi4", "pi5": "sticker-back-pi5"},
               # the filament changes, for the print notes in the viewer's download
               "layer_change_mm": {k: first_layer_at(H - BAND, f, lh) for k, (f, lh) in LAYERS.items()}, "panel_change_mm": pchange,
               "layer_change_n": {k: layer_number(first_layer_at(H - BAND, f, lh), f, lh) for k, (f, lh) in LAYERS.items()},
               "panel_change_n": pchange_n,
               "hint": "Raspberry Pi 2B / 3B / 3B+ / 4B / 5 - universal"},
              open(os.path.join(view, "params.json"), "w", newline="\n"), indent=1)
    print("written to", OUT)


if __name__ == "__main__":
    main()
