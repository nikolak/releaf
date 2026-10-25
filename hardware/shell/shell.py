"""Releaf controller shell, built with CadQuery 2.x.

    python shell.py            # writes releaf-shell-front.step and releaf-shell-back.step here

Two printed parts:
  back  - the half against the wall. Carries the linker latch and holds the
          PCB. Its back face sits flush with the panel's back.
  front - the cover you see. Presses the PCB onto the latch and covers
          everything above the panel's front face.
Held together without screws by two large latches, one on each 60 degree
end wall. Each is a tall plate hanging from the front with a hook near its
tip; the hook catches the top edge of an opening in the back that runs through
to the back face, so a broken hook falls out the back. Both catch faces are
45 degrees, so they print without support, and the hook sits slightly into the
edge so the latch keeps pulling the front down onto the back. A firm pull
separates the halves.

The logo leaf (from logo.svg in the repository root) is indented
LOGO_INDENT into the front face. The floor of the indent is the logo's own
bodies, so it can be printed in other colours, or in the front's colour for a
plain engraving.

Output is STEP only, in print orientation: releaf-shell-back.step (the back
half plus its loose support block) and releaf-shell-front.step (the front
half plus the logo as separate bodies), next to this script.

Coordinates:
  X  across the shell. X = JOINT is the panel edge; the shell's panel-side
     face sits SHAVE inside it, so it can't hold the linker off.
  Y  along the panel edge.
  Z  toward the wall. Z = BACK is the back face; the front is at negative Z.
"""

import math
import pathlib
import xml.etree.ElementTree as ET

import cadquery as cq

HERE = pathlib.Path(__file__).parent
REPO = HERE.parent.parent

# --- latch -----------------------------------------------------------------
JOINT = -6.0              # panel edge
SHAVE = 0.5               # panel-side face sits this far inside it
FACE = JOINT + SHAVE
BACK = 5.5                # back face, flush with the panel back
LATCH_Y = (-20.24, 8.0)   # Y slab the latch occupies (bridge + coves)
RECESS_Y = (-15.24, 3.0)  # linker plate recess, open through both side walls
RECESS_FRONT = 3.0
J1_XY = (5.19, -6.32)     # centre of the latch hole = centre of the PCB pads

# --- PCB (releaf.kicad_pcb) -------------------------------------------------
PCB_T = 1.6
PCB_BACK = 0.3                    # pads rest on the latch bridge
PCB_FRONT = PCB_BACK - PCB_T
PLATE_FRONT = BACK - 1.0          # 1 mm back plate: about 4 mm under the PCB for solder joints and pin ends
BOARD = (80.0, 20.0)
J1_KICAD = (40.0, 10.0)
NOTCHES = [(1, 10), (50, 1), (32, 19), (79, 4.5)]   # centres of the R1.5 edge notches
CLEAR = 0.3                       # PCB to shell, each side
CLEAR_JOINT = 0.1                 # ...except on the panel side, where the wall is thin
CLAMP = 0.05                      # front ribs press this far into the PCB

# Component heights above the PCB front. The SuperMini and the regulator
# are assumed to sit on standard 2.54 mm headers (2.5 mm plastic spacer).
MINI_STANDOFF = 2.5
MINI_PCB = 1.0
USB_H = 3.2
REG_STANDOFF = 2.5
REG_H = 2.8
CAP_D = 8.0
CAP_LIFT = 0.3

# --- shell ------------------------------------------------------------------
LENGTH = 115.0            # panel-side edge = the Shapes hexagon edge
WIDTH = 23.5
END_ANGLE = 60.0          # ends follow the neighbouring panel edges
WALL = 1.6
TOP_CLEAR = 0.5           # tallest part (C1) to the inside of the top
R_ACUTE = 1.0             # plan corner radii
R_OBTUSE = 2.5
SEAM = -0.5               # front/back split = the panel's front face (6 mm panel)
REVEAL = 0.4              # chamfer on each side of the seam
BACK_CHAMFER = 0.6

# Top-edge chamfers: (inset on top, drop down the side). The front prints
# front-down, so keep inset <= drop (45 degree overhang at most).
BEVEL_OUTER = (5.0, 5.0)
BEVEL_JOINT = (2.5, 2.5)
BEVEL_END = (1.5, 1.5)

# Latches: one on each end wall. A tall plate hangs from the front; the hook
# near its tip catches the top edge of an opening that runs through to the
# back face, so a broken hook just falls out the back.
LATCH_X = JOINT + WIDTH / 2   # X where the latch's centre meets the end wall
LATCH_W = 16.0            # along the end wall
LATCH_T = 1.5             # bends toward the inside
LATCH_ROOT = -10.2        # Z, buried in the front's top
LATCH_TIP = BACK - 0.5    # stops 0.5 short of the back face
HOOK = 1.0                # how far the hook sticks out of the plate (45 degree faces)
PRELOAD = 0.1             # hook overlaps the catch edge this much: no play, front held down
LATCH_FLEX = HOOK + 0.2   # free room behind the plate to bend into
LATCH_SIDE = 0.15         # slot clearance along the wall

# Logo indented into the front face; the letters' tops point toward the panel
LOGO_H = 9.0              # height of the leaf, across the shell
LOGO_INDENT = 0.4         # the logo sits this far below the front face
LOGO_THICK = 0.4          # logo bodies behind that, the floor of the indent, for a second colour
LOGO_Y = 39.2             # centre of the leaf, from the shell centre along Y
LEAF_INSET = 0.12         # mm off each leaf facet, so the gaps between them print


def board_xyz(bx, by, h=0.0):
    """KiCad board coordinates (mm, y down) plus height above the PCB front."""
    return (J1_XY[0] - J1_KICAD[1] + by, J1_XY[1] + J1_KICAD[0] - bx, PCB_FRONT - h)


def box(x0, x1, y0, y1, z0, z1):
    x0, x1 = sorted((x0, x1))
    y0, y1 = sorted((y0, y1))
    z0, z1 = sorted((z0, z1))
    return cq.Workplane().box(x1 - x0, y1 - y0, z1 - z0, centered=False).translate((x0, y0, z0))


def cyl_z(x, y, z0, z1, r):
    z0, z1 = sorted((z0, z1))
    return cq.Workplane().circle(r).extrude(z1 - z0).translate((x, y, z0))


def xz_prism(pts, y, length):
    """Polygon in the XZ plane, extruded along Y over y - length/2 .. y + length/2."""
    return cq.Workplane("XZ", origin=(0, y + length / 2, 0)).polyline(pts).close().extrude(length)


# Derived layout ------------------------------------------------------------
Y_MID = J1_XY[1]
X_OUT = JOINT + WIDTH
RUN = WIDTH / math.tan(math.radians(END_ANGLE))
_ENDS = [(JOINT, Y_MID - LENGTH / 2), (X_OUT, Y_MID - LENGTH / 2 + RUN),
         (X_OUT, Y_MID + LENGTH / 2 - RUN), (JOINT, Y_MID + LENGTH / 2)]
# the end walls keep their 60 degree lines; the panel-side corners slide in along them
_k = SHAVE / WIDTH
OUTLINE = [
    (FACE, _ENDS[0][1] + (_ENDS[1][1] - _ENDS[0][1]) * _k),
    _ENDS[1],
    _ENDS[2],
    (FACE, _ENDS[3][1] + (_ENDS[2][1] - _ENDS[3][1]) * _k),
]
# wall per edge of OUTLINE: end, outer, end, panel side (thinner by SHAVE)
WALLS = [WALL, WALL, WALL, WALL - SHAVE]

bx0, by0, _ = board_xyz(0, 0)
bx1, by1, _ = board_xyz(*BOARD)
PCB_X = (min(bx0, bx1), max(bx0, bx1))
PCB_Y = (min(by0, by1), max(by0, by1))
POCKET_X = (PCB_X[0] - CLEAR_JOINT, PCB_X[1] + CLEAR)
POCKET_Y = (PCB_Y[0] - CLEAR, PCB_Y[1] + CLEAR)

TALLEST = CAP_LIFT + CAP_D
TOP = PCB_FRONT - TALLEST - TOP_CLEAR - WALL      # outer front face



def latches():
    """(x, y, angle) per latch: the middle of its barb face, and the direction
    the barb points (degrees from +X, outward through the end wall)."""
    res = []
    normals = edge_normals(OUTLINE)
    for nx, ny, (x0, y0) in (normals[0], normals[2]):  # the two end walls
        ex, ey = -ny, nx
        t = (LATCH_X - x0) / ex
        inset = WALL + 0.2
        res.append((x0 + ex * t - nx * inset, y0 + ey * t - ny * inset, math.degrees(math.atan2(ny, nx))))
    return res


def offset_polygon(pts, ds):
    """Offset each edge of a convex counter-clockwise polygon inward by ds[i]."""
    n = len(pts)
    lines = []
    for i in range(n):
        d = ds[i]
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        ex, ey = x1 - x0, y1 - y0
        le = math.hypot(ex, ey)
        nx, ny = ey / le, -ex / le          # outward for CCW
        lines.append(((x0 - nx * d, y0 - ny * d), (ex, ey)))
    out = []
    for i in range(n):
        (p, e), (q, f) = lines[i - 1], lines[i]
        det = e[0] * -f[1] - e[1] * -f[0]
        t = ((q[0] - p[0]) * -f[1] - (q[1] - p[1]) * -f[0]) / det
        out.append((p[0] + e[0] * t, p[1] + e[1] * t))
    return out


def edge_normals(pts):
    """Outward plan normal and a point on each edge of a CCW polygon."""
    res = []
    for i in range(len(pts)):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % len(pts)]
        le = math.hypot(x1 - x0, y1 - y0)
        res.append(((y1 - y0) / le, -(x1 - x0) / le, (x0, y0)))
    return res


def prism(pts, z0, z1, r_acute, r_obtuse):
    sk = cq.Sketch().polygon(pts + [pts[0]])
    sk = sk.vertices("<X").fillet(r_acute).reset().vertices(">X").fillet(r_obtuse).reset()
    z0, z1 = sorted((z0, z1))
    return cq.Workplane().placeSketch(sk).extrude(z1 - z0).translate((0, 0, z0))


def bevel_cutters(insets):
    """Half-spaces that chamfer the top edges, each moved inward by insets[i]."""
    # edge order of OUTLINE (CCW): end (-Y), outer, end (+Y), joint
    sizes = [BEVEL_END, BEVEL_OUTER, BEVEL_END, BEVEL_JOINT]
    cutters = []
    for (nx, ny, p0), (w, h), inset in zip(edge_normals(OUTLINE), sizes, insets):
        # plane through (p0 - w*n, TOP) and (p0, TOP + h), containing the edge
        L = math.hypot(h, w)
        N = cq.Vector(h * nx / L, h * ny / L, -w / L)
        q = cq.Vector(p0[0] - w * nx, p0[1] - w * ny, TOP) - N * inset
        e = cq.Vector(-ny, nx, 0)
        plane = cq.Plane(origin=q, xDir=e, normal=N)
        cutters.append(cq.Workplane(plane).rect(400, 400).extrude(100))
    return cutters


def latch_slab():
    """The linker latch: a bridge under the PCB pads with the plug pocket in it,
    and the recess the linker plate sits in. Measured from the tested print."""
    x0, x1 = JOINT, X_OUT + 3
    body = box(x0, x1, *LATCH_Y, 2.3, BACK)                         # plate
    body = body.union(box(x0, x1, -16.24, 4.0, PCB_BACK, 2.3))      # bridge under the pads
    for yc, ya, yb in ((-18.24, -18.24, -16.24), (6.0, 4.0, 6.0)):  # R2 coves up to the plate
        cove = cq.Workplane("YZ", origin=(x0 - 1, 0, 0)).center(yc, PCB_BACK).circle(2.0).extrude(x1 - x0 + 2)
        body = body.union(box(x0, x1, ya, yb, PCB_BACK, 2.3).cut(cove))
    body = body.cut(box(x0 - 1, x1 + 1, *RECESS_Y, RECESS_FRONT, BACK + 1))
    # pocket: a trapezoid in plan (11.63 wide at the panel end, 10.37 at the far end),
    # R2 corners, straight walls up to 2.0, then a 45 degree lead-in to the recess floor
    hy = -6.325

    def half(x):
        return 5.815 - 0.63 / 7.98 * (x - 1.2)

    pts = [(-0.81, hy - half(-0.81)), (11.19, hy - half(11.19)), (11.19, hy + half(11.19)), (-0.81, hy + half(-0.81))]
    face = cq.Sketch().polygon(pts + [pts[0]]).vertices().fillet(2.0).reset()._faces.Faces()[0]
    wide = face.outerWire().offset2D(1.0, "arc")[0]
    walls = cq.Solid.extrudeLinear(face, cq.Vector(0, 0, 2.11)).translate(cq.Vector(0, 0, -0.1))
    lead = cq.Solid.makeLoft([face.outerWire().moved(cq.Location(cq.Vector(0, 0, 2.0))),
                              wide.moved(cq.Location(cq.Vector(0, 0, 3.0)))])
    top = cq.Solid.extrudeLinear(cq.Face.makeFromWires(wide), cq.Vector(0, 0, 1.0)).translate(cq.Vector(0, 0, 2.99))
    return body.cut(cq.Workplane().add(walls)).cut(cq.Workplane().add(lead)).cut(cq.Workplane().add(top))


def place(shape, x, y, angle):
    return shape.rotate((0, 0, 0), (0, 0, 1), angle).translate((x, y, 0))


HOOK_PEAK = LATCH_TIP - HOOK   # Z of the hook's outermost point


def latch_local():
    """Latch plate with its outer face on x = 0 (outward = +x), centred on y = 0.
    The hook near the tip has a 45 degree lead-in toward the tip and a 45 degree
    catch face above it, so it prints without support."""
    plate = box(-LATCH_T, 0, -LATCH_W / 2, LATCH_W / 2, LATCH_ROOT, LATCH_TIP)
    hook = [(-0.01, LATCH_TIP), (HOOK, HOOK_PEAK), (-0.01, HOOK_PEAK - HOOK - 0.01)]
    return plate.union(xz_prism(hook, 0, LATCH_W))


def latch_seat_local():
    """What the back loses for one latch: the slot the plate bends in and the
    opening the hook sits in, both open through the back face. The opening's
    top is a 45 degree face matching the hook's catch, PRELOAD into it."""
    side = LATCH_W / 2 + LATCH_SIDE
    cut = box(0.1, -(LATCH_T + LATCH_FLEX), -side, side, SEAM - 1, BACK + 1)
    x1 = HOOK + 0.1
    z0 = HOOK_PEAK - HOOK + PRELOAD          # catch edge, where it meets the plate face
    opening = [(0.05, z0 + 0.05), (x1, z0 + x1), (x1, BACK + 1), (0.05, BACK + 1)]
    return cut.union(xz_prism(opening, 0, 2 * side))


# --- back ---------------------------------------------------------------------
def make_back():
    outer = (prism(OUTLINE, SEAM, BACK, R_ACUTE, R_OBTUSE)
             .faces(">Z").edges().chamfer(BACK_CHAMFER)
             .faces("<Z").edges().chamfer(REVEAL))

    back = outer.cut(box(*POCKET_X, *POCKET_Y, SEAM - 1, PLATE_FRONT))

    # swap in the latch: clear the slab from the PCB plane back, then add it
    back = back.cut(box(JOINT - 1, X_OUT + 1, *LATCH_Y, PCB_BACK, BACK + 1))
    back = back.union(latch_slab().intersect(outer))
    # restore the side walls inside the slab
    back = back.union(outer.cut(box(*POCKET_X, *POCKET_Y, SEAM - 1, BACK + 1)))

    # ledges under the PCB edges (solder joints stay clear of these strips)
    ledge = 1.0
    for x0, x1 in ((POCKET_X[0], PCB_X[0] + ledge - CLEAR), (PCB_X[1] - ledge + CLEAR, POCKET_X[1])):
        back = back.union(box(x0, x1, *POCKET_Y, PCB_BACK, PLATE_FRONT))
    for y0, y1 in ((POCKET_Y[0], PCB_Y[0] + ledge - CLEAR), (PCB_Y[1] - ledge + CLEAR, POCKET_Y[1])):
        back = back.union(box(*POCKET_X, y0, y1, PCB_BACK, PLATE_FRONT))

    # locating pins in the four board notches (stop 0.3 short of the PCB front)
    for nx, ny in NOTCHES:
        x, y, _ = board_xyz(nx, ny)
        pin = cyl_z(x, y, PCB_FRONT + 0.3, PLATE_FRONT, 1.3)
        # above the seam, keep it inside the PCB pocket, clear of the front's walls
        pin = pin.cut(box(-100, 100, -200, 200, SEAM - 2, SEAM)).union(
            pin.intersect(box(*POCKET_X, *POCKET_Y, SEAM - 2, SEAM + 0.01)))
        back = back.union(pin)

    # seats for the front's latches
    for x, y, angle in latches():
        back = back.cut(place(latch_seat_local(), x, y, angle))
    # the linker plate recess, last, so nothing above reaches into it; open through both side walls
    return back.cut(box(JOINT - 1, X_OUT + 1, *RECESS_Y, RECESS_FRONT, BACK + 1))


def logo_pieces():
    """[(class, polygons, holes)] from logo.svg: each path's first subpath is the
    outline, any further ones are holes. y points down, as in SVG."""
    root = ET.parse(REPO / "logo.svg").getroot()
    out = []
    for el in root.iter("{http://www.w3.org/2000/svg}path"):
        rings = []
        for sub in el.get("d").split("M")[1:]:
            pts = sub.replace("Z", "").replace("L", " ").split()
            rings.append([tuple(float(v) for v in p.split(",")) for p in pts])
        out.append((el.get("class"), None, rings[:1], rings[1:]))
    return out


def make_logo(z0, z1):
    """The leaf from logo.svg as one solid, from z0 to z1 behind the front face."""
    pieces = [p for p in logo_pieces() if p[0] == "leaf"]
    xs = [x for _, _, polys, _ in pieces for p in polys for x, _ in p]
    ys = [y for _, _, polys, _ in pieces for p in polys for _, y in p]
    height = max(ys) - min(ys)
    px, py = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    cx = (FACE + BEVEL_JOINT[0] + X_OUT - BEVEL_OUTER[0]) / 2      # middle of the flat top
    cy = Y_MID + LOGO_Y

    def to_xy(x, y):
        # logo y points down; seen from the front, the leaf's left side is at +Y
        # and its top points toward the panel (-X)
        u, v = (x - px) / height, (py - y) / height
        return (cx - v * LOGO_H, cy - u * LOGO_H)

    leaf = None
    for _, _, polys, _ in pieces:
        for poly in polys:
            w = cq.Workplane("XY", origin=(0, 0, TOP + z0)).polyline([to_xy(*p) for p in poly]).close()
            facet = w.offset2D(-LEAF_INSET).extrude(z1 - z0)
            leaf = facet if leaf is None else leaf.union(facet)
    return leaf


# --- front --------------------------------------------------------------------
def make_front():
    outer = prism(OUTLINE, TOP, SEAM, R_ACUTE, R_OBTUSE).faces(">Z").edges().chamfer(REVEAL)
    for c in bevel_cutters([0, 0, 0, 0]):
        outer = outer.cut(c)

    inner_pts = offset_polygon(OUTLINE, WALLS)
    cavity = prism(inner_pts, TOP + WALL, SEAM + 5, 0.5, max(R_OBTUSE - WALL, 0.5))
    for c in bevel_cutters(WALLS):
        cavity = cavity.cut(c)

    front = outer.cut(cavity).cut(box(*POCKET_X, *POCKET_Y, PCB_FRONT, SEAM + 1))
    inner_top = TOP + WALL
    clamp_z = PCB_FRONT + CLAMP

    # rib along the PCB's panel-side edge, pressing it onto the latch bridge
    # (with a 45 degree underside back to the wall, since the front prints front-down)
    x_wall, x_tip = FACE + WALLS[3], PCB_X[0] + 0.7
    reach = x_tip - x_wall
    pts = [(x_wall - 0.2, clamp_z), (x_tip, clamp_z), (x_tip, clamp_z - 0.5),
           (x_wall, clamp_z - 0.5 - reach), (x_wall - 0.2, clamp_z - 0.5 - reach)]
    front = front.union(xz_prism(pts, (PCB_Y[0] + PCB_Y[1]) / 2, PCB_Y[1] - PCB_Y[0]))
    # ...and a fin down from the top along the outer edge
    front = front.union(box(PCB_X[1] - 0.7, PCB_X[1] + 0.1, *PCB_Y, inner_top - 0.1, clamp_z))

    # press frame over the pads, against the panel's spring contacts
    px0, py0, _ = board_xyz(37.0, 5.4)
    px1, py1, _ = board_xyz(43.0, 14.6)
    frame = box(px0, px1, py0, py1, inner_top - 0.1, clamp_z)
    frame = frame.cut(box(px0 + 1.2, px1 - 1.2, py0 - 1.2, py1 + 1.2, inner_top - 1, clamp_z + 1))
    front = front.union(frame)

    keep = outer
    for x, y, angle in latches():
        front = front.union(place(latch_local(), x, y, angle))
        keep = keep.union(place(box(-LATCH_T, HOOK, -LATCH_W / 2, LATCH_W / 2, SEAM - 1, LATCH_TIP),
                                x, y, angle))

    # the indent, and room behind it for the logo bodies
    front = front.cut(make_logo(-0.5, LOGO_INDENT + LOGO_THICK))
    # the latches reach below the seam; keep everything else inside the outline
    return front.intersect(keep)


# --- reference board ----------------------------------------------------------
def make_board():
    """PCB and component envelopes, for fit checks and renders only."""
    x0, x1 = PCB_X
    y0, y1 = PCB_Y
    pcb = box(x0, x1, y0, y1, PCB_FRONT, PCB_BACK)
    for nx, ny in NOTCHES:
        x, y, _ = board_xyz(nx, ny)
        pcb = pcb.cut(cyl_z(x, y, -5, 5, 1.5))
    for sx in (33.25, 43.75):
        a = board_xyz(sx, 5.5)
        b = board_xyz(sx + 3, 14.5)
        pcb = pcb.cut(box(a[0], b[0], a[1], b[1], -5, 5))

    parts = {}

    def comp(name, bxa, bya, bxb, byb, h0, h1):
        a = board_xyz(bxa, bya, h0)
        b = board_xyz(bxb, byb, h1)
        parts[name] = box(a[0], b[0], a[1], b[1], a[2], b[2])

    m0, m1 = MINI_STANDOFF, MINI_STANDOFF + MINI_PCB
    comp("mini_pcb", 0.8, 1.0, 23.32, 19.0, m0, m1)
    comp("mini_parts", 4.0, 2.0, 22.5, 18.0, m1, m1 + 1.6)
    comp("usb_c", -0.3, 9.9 - 4.5, 7.0, 9.9 + 4.5, m1, m1 + USB_H)
    for by in (2.26, 17.5):
        comp(f"header_{by}", 1.9, by - 1.27, 22.3, by + 1.27, 0, MINI_STANDOFF)
        comp(f"pins_{by}", 2.9, by - 0.4, 21.3, by + 0.4, 0, 6.0)
    comp("reg", 53.0, 3.37, 60.62, 14.77, REG_STANDOFF, REG_STANDOFF + REG_H)
    comp("reg_header", 53.0, 12.2, 59.6, 14.8, 0, REG_STANDOFF)
    comp("reg_pins", 53.9, 13.1, 59.0, 13.9, 0, 6.0)
    comp("switch", 62.0, 2.75, 72.0, 5.25, 0, 5.0)
    comp("knob", 64.0, 3.0, 70.0, 5.0, 5.0, 6.5)
    comp("r1", 27.25, 6.6, 29.75, 12.9, 0, 2.5)
    comp("cap_leads", 62.5, 10.7, 66.5, 15.3, 0, 1.0)
    ax, ay, az = board_xyz(66.5, 13.0, CAP_LIFT + CAP_D / 2)
    parts["c1"] = (cq.Workplane("XZ", origin=(0, ay, 0)).center(ax, az)
                   .circle(CAP_D / 2).extrude(11.5))
    return pcb, parts


# Loose support block for the linker recess (its own body in the back STEP): fills the recess and
# stops one layer short of its ceiling, so the whole ceiling, latch hole edge
# included, prints on a flat surface. It sticks out of the panel-side face as a
# tab on both long sides: push or pull it out after printing.
SUPPORT_GAP = 0.2         # block top to ceiling = one layer
SUPPORT_CLEAR = 0.4       # block to recess walls
SUPPORT_TAB = 10.0        # how far it sticks out of the panel-side face, to grab it by


def make_support():
    c = SUPPORT_CLEAR
    return box(FACE - SUPPORT_TAB, X_OUT + SUPPORT_TAB, RECESS_Y[0] + c, RECESS_Y[1] - c, RECESS_FRONT + SUPPORT_GAP, BACK)


def on_back(shape):
    """Print orientation for the back half: back face down on z = 0."""
    return shape.rotate((0, 0, 0), (0, 1, 0), 180).translate((0, 0, BACK))


def on_front(shape):
    """Print orientation for the front half: front face down on z = 0."""
    return shape.translate((0, 0, -TOP))


def export_step(path, parts):
    """One STEP file, one named body per part."""
    assy = cq.Assembly()
    for name, shape, rgb in parts:
        assy.add(shape, name=name, color=cq.Color(*rgb))
    assy.export(str(path))


if __name__ == "__main__":
    back = make_back()
    front = make_front()
    leaf = make_logo(LOGO_INDENT, LOGO_INDENT + LOGO_THICK)
    white, green, grey = (0.95, 0.95, 0.93), (0.2, 0.6, 0.25), (0.15, 0.15, 0.15)
    out = HERE
    export_step(out / "releaf-shell-back.step",
                [("back", on_back(back), white), ("support - remove after printing", on_back(make_support()), grey)])
    export_step(out / "releaf-shell-front.step",
                [("front", on_front(front), white), ("logo", on_front(leaf), green)])
    print("thickness %.2f mm, back %.1f cm3, front %.1f cm3"
          % (BACK - TOP, back.val().Volume() / 1000, front.val().Volume() / 1000))
