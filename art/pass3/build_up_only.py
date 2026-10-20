"""Chapter 1, pass 3 (docs/chapter1_pass3_plan.md, section 4): DL-10 Up Only, the ring C relocation lift lobby.
Built in FINAL world x, after insert_scenes() has opened the gaps (called from art/dl01/build_dl01.py).

The place the lower-grade families left from. It runs on from the DL-09 balcony (the city vista) at the deck's
height (1.6), and comes down to ring C's ledge (0), where art/dl05 takes over:
  - the porch (116.6 .. 118.8): the balcony's deck carried on to the lobby's entrance, where the balcony stair
    used to go down (that stair is gone from G4Balcony; it is the collapsed stair below, beside the lift);
  - the lobby (118.8 .. 126.85): the heap of left luggage (the last suitcase, tagged C-114, slid off onto the
    lane: Suitcase114), the painted queue line to the lift with what was dropped along it (a suitcase burst open,
    a child's shoe, a doll, an empty birdcage), the bench, the departures board, the failing pendant lamp;
  - the lift, behind the lane: a lattice gate (LiftDoorL/R) in the front wall under the sign RELOCATION - GRADES
    1-2 ONLY with EVERYONE painted across the grades, and the car behind it (LiftCar), its floor a weighing plate
    (LiftFloorPlate) with a load gauge (LiftLoadNeedle); the call panel left of the gate, one worn brass UP
    (LiftPanel, LiftUpButton, LiftUpLamp);
  - the crank on the pier (ServiceCrank) that winds the service door (ServiceDoor) up out of the lane, by a chain;
  - the counterweight's open shaft on the lane (126.85 .. 127.75), the counterweight (Counterweight) standing at
    the deck with its footplate and side rails, roped to the car over two sheaves on the head frame above
    (LiftSheave, LiftSheaveIdler, LiftRopeCar, LiftRopeCW), the service UP on the shaft's far wall
    (ServicePanel, ServiceUpButton, ServiceUpLamp), cold light falling down the shaft from far above;
  - ring C's level at the shaft's foot: the bottom landing (127.75 .. ring C's ledge, 130.8), and against its back
    wall the stair that came down from the lobby's level, collapsed: its head, a torn stub, the fallen flight
    on its rubble.

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y. Game (x, y, z) = (x, z, -y).
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
from build_d17 import (add_box, add_cyl, add_sphere, add_torus, rounded_box, emission_material, worn_material,
                       simple_material, SIDES, CLAW_REST_OPEN)

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
ATLAS = os.path.join(TEX, 'uponly_atlas.png')

# --------------------------------------------------------------------------
# Layout, shared with the game (game x = these; game y = z; game z = -y)
# --------------------------------------------------------------------------
DECK = 1.6                            # the balcony's deck, the porch, the lobby
BALCONY_END = 116.6                   # DL-09's balcony deck ends here (dl04 BALCONY[1] + OFF4 + WIDTH1)
PORCH = (116.6, 118.8)                # the deck carried on where the balcony stair went down
LOBBY_X0 = 118.8                      # the lobby's entrance (posts behind the lane, a lintel over it)
CEIL = 4.9                            # the waiting area's ceiling
BACK_Y = 1.2                          # the waiting area's back wall face
WALL_Y = 0.34                         # the lift's front wall face (the gate, the panel, the crank's pier)
WALL_T = 0.12
LIFT_WALL = (123.55, 126.85)          # the front wall: the lift, then the pier with the crank
HEAP = (119.05, 120.95)               # the left luggage, against the back wall
SUITCASE = (121.3, 0.0)               # Suitcase114's origin (base centre) x, y; it sits on the deck, on the lane
SUITCASE_SIZE = (0.32, 0.12, 0.2)     # length (x), thickness (y), height (z) of its body
SUITCASE_GRIP = 0.225                 # the top of its handle (the depot box's grip is at 0.22)
LAMP = (121.35, 0.2, 4.1)             # the failing pendant (LobbyBulb), over the suitcase: its pool is where to look
CRANK_LAMP = (126.48, 0.2, DECK + 1.45)   # a caged work lamp on the pier over the crank (CrankLamp), its pool on the wheel
QUEUE = (119.3, 124.4)                # the painted queue line along the lane, to the gate
QUEUE_Y = (-0.48, 0.3)                # its two edge lines
# The lift: the car behind the lane, its landing gate in the front wall.
GATE = (124.4, 125.5, 1.8)            # the doorway: x0, x1, height (its sign must sit under the side camera's frame top, ~4.0)
GATE_Y = 0.4825                       # the gate's leaves run just behind the wall (0.47 .. 0.495)
LEAF_W = 0.57                         # each leaf; open, each sits behind the wall beside the doorway
LEAF_SLIDE = 0.56                     # LiftDoorL closes +0.56 x, LiftDoorR -0.56 x (modelled open)
CAR = (124.2, 125.7)                  # the car's outside, x
CAR_Y = (0.52, 1.74)                  # ... and y
CAR_C = (124.95, 1.13)                # LiftCar's origin: the centre of its floor (z = DECK at the start)
CAR_IN = (124.27, 125.63)             # inside the car, between its walls (x); inside y 0.58 .. 1.68
PLATE = (124.32, 125.58, 0.58, 1.66)  # LiftFloorPlate (x0, x1, y0, y1), flush with the car floor; dips 0.01
CAR_H = 2.1                           # inside height
CAR_HITCH = 2.3                       # the ropes' hitch, above the car's floor
CAR_RAILS = (124.12, 125.78)          # the car's guide rails (x), at CAR_C's y
PANEL_X = 124.07                      # LiftUpButton's x
BUTTON_AHEAD = 0.30                   # both UP buttons' faces stand 0.30 ahead of him (the lobby's at y 0.30)
BUTTON_DZ = 0.56                      # the UP buttons' height above the floor he stands on
BUTTON_RIGHT = 0.12                   # the buttons sit this far to his right (the PressButtonHigh clip's reach)
UP_STAND_X = PANEL_X - BUTTON_RIGHT   # facing the wall (+y), his right is +x
CRANK = (126.45, 0.2, DECK + 0.45)    # ServiceCrank's wheel centre, as DL-01's crank (the Crank clip's reach)
CRANK_R = 0.15
SDOOR = (126.8, (-0.55, 0.335), 1.85)  # ServiceDoor: x (centre of a 0.06 leaf), y span, height
SDOOR_RISE = 1.45                     # wound fully up, its foot clears the deck by 1.45
CASING_Z = 3.42                       # the casing the door winds up into
# The counterweight's shaft, on the lane.
CW_SHAFT = (126.85, 127.75)
CW_X = 127.3                          # Counterweight origin x (its footplate's top centre, on the lane)
CW_TOP, CW_BOTTOM = DECK, 0.0         # the footplate's top: at the start, and at ring C's level
CW_TRAVEL = CW_TOP - CW_BOTTOM        # 1:1 with the car: the car rises as far as the counterweight falls
FOOT = (-0.4, 0.4, -0.42, 0.78)       # the footplate, counterweight-local x0, x1, y0, y1 (its top is the origin)
CW_RAIL_Y, CW_RAIL_Z, CW_RAIL_X = 0.34, 0.11, (-0.3, 0.3)   # the side rails he grips (as the cage's), local
CW_RAILS = (126.93, 127.67)           # the counterweight's guide rails (x), at the rope plane
CW_HITCH = 0.55                       # its rope hitch, above the footplate's top
SERVICE_ANG = math.radians(25)        # the service panel turns its face this far from -x toward the camera
SERVICE_FACE = 0.09                   # its button's face stands this far out of the panel's back (local -x)
RIGHT_WALL = (127.75, 128.0)          # the shaft's far wall at the deck's level ...
LANDING_Z1 = 1.25                     # ... over the bottom landing's opening (0 .. 1.25)
PIT_Z = -1.75                         # the counterweight's pit floor
# The ropes and the head frame: one plane, two sheaves, axles along y.
ROPE_Y = 1.0
SHEAVE_Z, SHEAVE_R = 5.95, 0.3
SHEAVE_A = CAR_C[0] + SHEAVE_R        # LiftSheave, over the car: its left side drops to the car's hitch
SHEAVE_B = CW_X - SHEAVE_R            # LiftSheaveIdler, over the counterweight: its right side drops to it
SHAFT_BACK = 1.9                      # the shafts' back wall face
# Ring C's level: the bottom landing and the collapsed stair.
STAIR_HEAD = (128.0, 128.75)          # the stair's head landing, at the deck's level, behind the lane
STAIR_FOOT = 130.6                    # where its flight came down to ring C
STAIR_Y = (0.5, 1.6)


def service_frame():
    """The service panel's frame: on the shaft's far wall, turned toward him and the camera, placed so that its button's
    face is BUTTON_RIGHT to the right (-y) of the lane and BUTTON_DZ above the footplate at the top."""
    d = Vector((-math.cos(SERVICE_ANG), -math.sin(SERVICE_ANG), 0)) * SERVICE_FACE
    return Matrix.Translation((RIGHT_WALL[0], -BUTTON_RIGHT - d.y, DECK + BUTTON_DZ)) @ _rz(SERVICE_ANG)


def service_button_face():
    return service_frame() @ Vector((-SERVICE_FACE, 0, 0))


def ride_x():
    """Where he stands on the footplate to ride and to press the service UP (its face 0.30 ahead of him)."""
    return service_button_face().x - BUTTON_AHEAD


def ledge_x0(dl01):
    """Ring C's ledge (art/dl05), in final x: where ring C's lane takes over."""
    return dl01.dl05.LEDGE[0] + dl01.OFF4 + dl01.WIDTH1 + dl01.WIDTH2


I4 = Matrix.Identity(4)


def _rx(a):
    return Matrix.Rotation(a, 4, 'X')


def _ry(a):
    return Matrix.Rotation(a, 4, 'Y')


def _rz(a):
    return Matrix.Rotation(a, 4, 'Z')


# --------------------------------------------------------------------------
# Building kit
# --------------------------------------------------------------------------

def cbox(bm, center, size, b=0.012, mat=0, rot=None):
    """A box with its edges chamfered b wide: it catches the light along every edge (as art/dl05's)."""
    h = (size[0] / 2, size[1] / 2, size[2] / 2)
    b = max(0.0005, min(b, h[0] * 0.45, h[1] * 0.45, h[2] * 0.45))
    M = Matrix.Translation(center) @ (rot or I4)
    P = {}
    for s in [(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]:
        for a in range(3):
            co = [s[i] * (h[i] - b) for i in range(3)]
            co[a] = s[a] * h[a]
            P[(s, a)] = bm.verts.new(M @ Vector(co))
    cyc = ((-1, -1), (-1, 1), (1, 1), (1, -1))
    faces = []
    for a in range(3):
        b1, b2 = [i for i in range(3) if i != a]

        def S(sa, s1, s2):
            s = [0, 0, 0]
            s[a], s[b1], s[b2] = sa, s1, s2
            return tuple(s)
        for sa in (-1, 1):
            faces.append([P[(S(sa, s1, s2), a)] for s1, s2 in cyc])
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                faces.append([P[(S(-1, s1, s2), b1)], P[(S(1, s1, s2), b1)], P[(S(1, s1, s2), b2)], P[(S(-1, s1, s2), b2)]])
    for s in [(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]:
        faces.append([P[(s, 0)], P[(s, 1)], P[(s, 2)]])
    for f in faces:
        bm.faces.new(f).material_index = mat


def bx(bm, xr, yr, zr, mat=0, b=0.0, rot=None):
    """A box from (min, max) ranges; chamfered when b > 0."""
    c = ((xr[0] + xr[1]) / 2, (yr[0] + yr[1]) / 2, (zr[0] + zr[1]) / 2)
    s = (xr[1] - xr[0], yr[1] - yr[0], zr[1] - zr[0])
    if b:
        cbox(bm, c, s, b, mat, rot)
    else:
        add_box(bm, c, s, mat=mat, rot=rot)


def _wall_pieces(a0, a1, z0, z1, holes):
    cuts = sorted({a0, a1, *[h[0] for h in holes], *[h[1] for h in holes]})
    cuts = [c for c in cuts if a0 <= c <= a1]
    for ca, cb in zip(cuts, cuts[1:]):
        if cb - ca < 1e-4:
            continue
        zs = z0
        for ha0, ha1, hz0, hz1 in sorted((h for h in holes if h[0] <= ca + 1e-6 and h[1] >= cb - 1e-6), key=lambda h: h[2]):
            if hz0 > zs + 1e-4:
                yield (ca, cb, zs, min(hz0, z1))
            zs = max(zs, hz1)
        if z1 > zs + 1e-4:
            yield (ca, cb, zs, z1)


def wall_x(bm, x0, x1, y0, y1, z0, z1, holes=(), mat=0, b=0.0):
    """A wall along x (thickness y0..y1) with rectangular holes (hx0, hx1, hz0, hz1)."""
    for xa, xb, za, zb in _wall_pieces(x0, x1, z0, z1, holes):
        bx(bm, (xa, xb), (y0, y1), (za, zb), mat, b)


class Batch:
    """Static geometry merged into one object: one draw call per material, however many parts."""
    def __init__(self, U):
        self.U, self.bm, self.mats = U, bmesh.new(), []
        self.uv = self.bm.loops.layers.uv.new('UVMap')

    def __call__(self, key):
        mat = self.U[key] if isinstance(key, str) else key
        for i, x in enumerate(self.mats):
            if x == mat:
                return i
        self.mats.append(mat)
        return len(self.mats) - 1

    def done(self, name, coll, origin=None, sharp=35):
        if not len(self.bm.verts):
            self.bm.free()
            return None
        if origin is not None:
            bmesh.ops.translate(self.bm, vec=-Vector(origin), verts=self.bm.verts)
        ob = d17.mesh_object(name, self.bm, self.mats, coll, sharp=sharp)
        if origin is not None:
            ob.location = origin
        return ob


def quad(B, corners, rect, mat):
    """A textured quad on the atlas: corners counter-clockwise from bottom left (seen from its front), rect in atlas
    pixels (x0, y0, x1, y1) with y down, as PIL draws it."""
    vs = [B.bm.verts.new(Vector(c)) for c in corners]
    f = B.bm.faces.new(vs)
    f.material_index = mat
    x0, y0, x1, y1 = rect
    uvs = ((x0, y1), (x1, y1), (x1, y0), (x0, y0))
    for lp, (u, v) in zip(f.loops, uvs):
        lp[B.uv].uv = (u / 1024.0, 1.0 - v / 1024.0)
    return f


def sign(B, center, w, h, rect, mat, face=(0, -1, 0), tilt=0.0):
    """A sign facing `face` (horizontal), w x h, centred; tilt leans its top back (radians)."""
    n = Vector(face).normalized()
    right = Vector((-n.y, n.x, 0))
    up = Vector((0, 0, 1))
    if tilt:
        up = (up * math.cos(tilt) - n * math.sin(tilt))
    c = Vector(center)
    hw, hh = right * (w / 2), up * (h / 2)
    return quad(B, (c - hw - hh, c + hw - hh, c + hw + hh, c - hw + hh), rect, mat)


def chain(bm, p0, p1, pitch=0.06, w=0.022, mat=0):
    """A chain of flat links from p0 to p1, turned alternately."""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    n = max(1, int(d.length / pitch))
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    for k in range(n):
        c = p0 + d * ((k + 0.5) / n)
        r = rot @ (_rz(math.pi / 2) if k % 2 else I4)
        add_box(bm, c, (w, w * 0.3, pitch + 0.018), mat=mat, rot=r)


def rope_arc(bm, c, r, a0, a1, rr, ys, mat, n=12):
    """Ropes lying in a sheave's groove, from angle a0 to a1 (radians, in the x-z plane), at each y in ys."""
    for y in ys:
        pts = [Vector((c[0] + r * math.cos(a0 + (a1 - a0) * k / n), y, c[2] + r * math.sin(a0 + (a1 - a0) * k / n)))
               for k in range(n + 1)]
        for a, b in zip(pts, pts[1:]):
            add_cyl(bm, a, b, rr, seg=6, mat=mat)


def _clip(poly, inside, cross):
    out = []
    for i, p in enumerate(poly):
        q = poly[i - 1]
        if inside(p):
            if not inside(q):
                out.append(cross(q, p))
            out.append(p)
        elif inside(q):
            out.append(cross(q, p))
    return out


def stripes(bm, x, normal, ya, yb, za, zb, width=0.1, slope=1.0, mat=0):
    """Danger stripes on a face at x (facing +x or -x, normal = +1/-1): diagonal bands `width` wide every 2 * width,
    clipped to the rectangle ya..yb, za..zb."""
    for k in range(-int((zb - za) / width) - 4, int((yb - ya) / width) + 4, 2):
        u0 = ya + k * width
        poly = [(u0, za), (u0 + width, za), (u0 + width + slope * (zb - za), zb), (u0 + slope * (zb - za), zb)]
        for axis, lim, keep in ((0, ya, 1), (0, yb, -1), (1, za, 1), (1, zb, -1)):
            if not poly:
                break
            inside = (lambda p, a=axis, l=lim, kp=keep: (p[a] - l) * kp >= -1e-9)

            def cross(q, p, a=axis, l=lim):
                t = (l - q[a]) / (p[a] - q[a])
                return (q[0] + (p[0] - q[0]) * t, q[1] + (p[1] - q[1]) * t)
            poly = _clip(poly, inside, cross)
        if len(poly) >= 3:
            vs = [bm.verts.new((x, u, v)) for u, v in poly]
            f = bm.faces.new(vs if normal > 0 else vs[::-1])
            f.material_index = mat


def remove_faces(name, pred):
    """Delete the faces of an existing object whose world-space centre passes pred; returns how many."""
    ob = bpy.data.objects.get(name)
    if ob is None or ob.type != 'MESH':
        return 0
    mw = ob.matrix_world
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    dead = [f for f in bm.faces if pred(mw @ f.calc_center_median())]
    if dead:
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        bm.to_mesh(ob.data)
        ob.data.update()
    bm.free()
    return len(dead)


# --------------------------------------------------------------------------
# Textures: one atlas for every sign, plate and tag in the scene
# --------------------------------------------------------------------------
# Atlas rects (pixels, y down) and what they are.
R_SIGN = (0, 0, 1024, 256)            # RELOCATION - GRADES 1-2 ONLY, EVERYONE painted across (2.0 x 0.5 m)
R_ENTRY = (0, 256, 512, 384)          # RELOCATION LIFT, ring C (1.6 x 0.4)
R_STAIR = (512, 256, 1024, 384)       # the stair sign: STAIRS, a stair going down to C (1.0 x 0.25)
R_PANEL = (0, 384, 256, 640)          # the call panel's plate: a passenger aboard -> up; empty -> no
R_SERVICE = (256, 384, 512, 640)      # the service plate: car and counterweight over the sheave
R_BOARD = (512, 384, 1024, 768)       # the departures board, chalk
R_TAG = (0, 640, 128, 896)            # the luggage tag, C-114
R_RINGC = (128, 640, 384, 896)        # ring C's roundel, at the bottom landing
R_CAR = (640, 896, 896, 1024)         # the car's notice: persons and load, by grade
R_HAZARD = (640, 768, 896, 896)       # the stair's hazard board: a broken stair
R_POSTER = (896, 768, 1024, 1024)     # the relocation poster: a tower in the light, UP
R_GAUGE = (384, 768, 640, 1024)       # the car's load gauge face
R_TAGS = (128, 896, 384, 1024)        # plain luggage tags (other families)
R_LABEL = (0, 896, 128, 1024)         # the paper label pasted on Suitcase114's face: C-114


def make_textures():
    from PIL import Image, ImageDraw
    import build_dl03 as dl03
    font, age = dl03._font, dl03._age
    os.makedirs(TEX, exist_ok=True)
    img = Image.new('RGB', (1024, 1024), (30, 30, 28))
    d = ImageDraw.Draw(img, 'RGBA')
    ink, cream, green = (26, 24, 20), (214, 204, 176), (28, 52, 40)
    rnd = random.Random(1010)

    def text_c(box, s, f, fill):
        x0, y0, x1, y1 = box
        l, t, r, b = d.textbbox((0, 0), s, font=f)
        d.text(((x0 + x1 - (r - l)) / 2 - l, (y0 + y1 - (b - t)) / 2 - t), s, font=f, fill=fill)

    def arrow(cx, cy, s, fill, up=True):
        k = -1 if up else 1
        d.polygon([(cx, cy + k * s), (cx - s * 0.8, cy), (cx - s * 0.32, cy), (cx - s * 0.32, cy - k * s * 0.9),
                   (cx + s * 0.32, cy - k * s * 0.9), (cx + s * 0.32, cy), (cx + s * 0.8, cy)], fill=fill)

    # The relocation sign: enamel, cream on green, a brass-screwed border; EVERYONE brushed across the grades.
    d.rectangle(R_SIGN, fill=green)
    d.rectangle((10, 10, 1014, 246), outline=cream, width=8)
    for x, y in ((26, 26), (998, 26), (26, 230), (998, 230)):
        d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=(120, 96, 40), outline=ink, width=2)
    text_c((40, 22, 984, 118), 'RELOCATION', font(92), cream)
    d.line((60, 126, 964, 126), fill=cream, width=5)
    f2 = font(78)
    parts = ('GRADES 1–2', '  ONLY')
    widths = [d.textbbox((0, 0), t, font=f2)[2] - d.textbbox((0, 0), t, font=f2)[0] for t in parts]
    x = 512 - sum(widths) / 2
    spans = []
    for t, w in zip(parts, widths):
        l, tp, r, b = d.textbbox((0, 0), t, font=f2)
        d.text((x - l, 186 - (b - tp) / 2 - tp), t, font=f2, fill=cream)
        spans.append((x, x + w))
        x += w
    arrow(spans[0][0] - 70, 182, 30, cream)
    arrow(spans[1][1] + 60, 182, 30, cream)
    # The later hand: a pale wash brushed over the grades (they ghost through), EVERYONE lettered on it in dark
    # paint, and one stroke through ONLY. Runs and drips.
    paint, dark = (214, 208, 186), (30, 28, 24)
    gx0, gx1 = spans[0][0] - 18, spans[0][1] + 30
    wash = Image.new('RGBA', (1024, 256), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wash)
    for k in range(9):
        y = 146 + k * 9 + rnd.uniform(-2, 2)
        wd.line((gx0 + rnd.uniform(-6, 10), y, gx1 + rnd.uniform(-10, 6), y + rnd.uniform(-3, 3)), fill=(*paint, rnd.randint(170, 215)), width=14)
    for k in range(10):
        x = rnd.uniform(gx0 + 10, gx1 - 10)
        wd.line((x, 222, x + rnd.uniform(-1, 1), 222 + rnd.uniform(6, 26)), fill=(*paint, 200), width=rnd.randint(3, 6))
    img.paste(wash, (0, 0), wash)
    layer = Image.new('RGBA', (1024, 256), (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    f3 = font(66)
    l, tp, r, b = ld.textbbox((0, 0), 'EVERYONE', font=f3)
    ld.text(((gx0 + gx1) / 2 - (r - l) / 2 - l, 184 - (b - tp) / 2 - tp), 'EVERYONE', font=f3, fill=(*dark, 255))
    layer = layer.rotate(-2.5, resample=Image.BICUBIC, center=((gx0 + gx1) / 2, 184))
    ld = ImageDraw.Draw(layer)
    for k in range(7):
        x = rnd.uniform(gx0 + 30, gx1 - 30)
        y0 = rnd.uniform(205, 214)
        ld.line((x, y0, x + rnd.uniform(-1, 1), y0 + rnd.uniform(8, 20)), fill=(*dark, 220), width=rnd.randint(2, 4))
    ox0, ox1 = spans[1][0] + 30, spans[1][1] + 6
    ld.line((ox0, 196, ox1, 176), fill=(*dark, 235), width=9)
    img.paste(layer, (0, 0), layer)

    # The entrance sign: RELOCATION LIFT, the car pictogram going up, ring C's roundel.
    d.rectangle(R_ENTRY, fill=(36, 40, 36))
    d.rectangle((6, 262, 506, 378), outline=cream, width=5)
    text_c((120, 268, 420, 320), 'RELOCATION', font(40), cream)
    text_c((120, 322, 420, 372), 'LIFT', font(40), cream)
    d.rectangle((28, 278, 92, 366), outline=cream, width=5)
    arrow(60, 314, 22, cream)
    d.ellipse((430, 280, 494, 344), outline=cream, width=5)
    text_c((430, 280, 494, 344), 'C', font(40), cream)
    text_c((424, 346, 500, 376), 'RING', font(18), cream)

    # The stair sign: STAIRS, a stair going down to ring C's roundel.
    d.rectangle(R_STAIR, fill=(196, 168, 60))
    d.rectangle((518, 262, 1018, 378), outline=ink, width=6)
    text_c((540, 280, 790, 360), 'STAIRS', font(58), ink)
    for k in range(5):
        d.rectangle((806 + k * 26, 288 + k * 16, 806 + k * 26 + 28, 296 + k * 16), fill=ink)
    arrow(950, 320, 30, ink, up=False)
    d.ellipse((960, 270, 1006, 316), outline=ink, width=4)
    text_c((960, 270, 1006, 316), 'C', font(30), ink)

    # The call panel's plate, wordless: a figure in the car -> the arrow up; the car empty -> crossed out.
    d.rectangle(R_PANEL, fill=(206, 196, 168))
    d.rectangle((6, 390, 250, 634), outline=ink, width=6)
    for oy, full in ((404, True), (522, False)):
        d.rectangle((26, oy, 106, oy + 100), outline=ink, width=6)
        if full:
            d.ellipse((54, oy + 22, 78, oy + 46), fill=ink)
            d.rectangle((52, oy + 48, 80, oy + 82), fill=ink)
            d.rectangle((84, oy + 64, 100, oy + 92), fill=ink)                 # a case at its feet
            arrow(178, oy + 52, 34, ink)
        else:
            d.line((132, oy + 16, 224, oy + 92), fill=ink, width=12)
            d.line((224, oy + 16, 132, oy + 92), fill=ink, width=12)
        d.rectangle((22, oy + 96, 110, oy + 104), fill=ink)                      # the floor plate

    # The service plate: the car and the counterweight over the sheave, the car up, the weight down.
    d.rectangle(R_SERVICE, fill=(196, 168, 60))
    d.rectangle((262, 390, 506, 634), outline=ink, width=6)
    d.ellipse((330, 410, 438, 518), outline=ink, width=8)
    d.ellipse((376, 456, 392, 472), fill=ink)
    d.line((336, 464, 336, 540), fill=ink, width=5)
    d.line((432, 464, 432, 566), fill=ink, width=5)
    d.rectangle((292, 540, 382, 610), outline=ink, width=6)                    # the car
    d.rectangle((414, 566, 450, 616), fill=ink)                                # the counterweight, someone on it
    d.ellipse((424, 534, 440, 550), fill=ink)
    d.rectangle((426, 550, 438, 566), fill=ink)
    arrow(306, 474, 18, ink)
    arrow(476, 590, 18, ink, up=False)

    # The departures board: chalk on black, family numbers and their dates, ticked; C-114 at the bottom.
    d.rectangle(R_BOARD, fill=(22, 26, 24))
    d.rectangle((516, 388, 1020, 764), outline=(90, 66, 40), width=10)
    chalk = (204, 204, 192)
    text_c((530, 398, 1006, 440), 'DEPARTURES  RING C', font(32), chalk)
    d.line((540, 444, 996, 444), fill=chalk, width=3)
    rows = ('C-101', 'C-102', 'C-104', 'C-105', 'C-106', 'C-108', 'C-110', 'C-112', 'C-114')
    for k, num in enumerate(rows):
        y = 452 + k * 33
        col = 540 if k < 5 else 780
        yy = y if k < 5 else 452 + (k - 5) * 33
        d.text((col, yy), num, font=font(24, 'sans'), fill=chalk)
        date = '19.5' if num == 'C-114' else f'{(k * 7) % 28 + 1:02d}.{3 + k // 4}'
        d.text((col + 98, yy + 2), date, font=font(20, 'sans'), fill=(170, 170, 160))
        d.line((col + 176, yy + 14, col + 186, yy + 24), fill=chalk, width=4)
        d.line((col + 186, yy + 24, col + 206, yy + 2), fill=chalk, width=4)
    for k in range(4):                                                         # tallies, smudges
        x = 560 + k * 46
        for j in range(4):
            d.line((x + j * 8, 640, x + j * 8, 680), fill=chalk, width=3)
        d.line((x - 4, 672, x + 30, 646), fill=chalk, width=3)
    d.text((800, 640), 'LAST CAR', font=font(26, 'sans'), fill=chalk)
    d.text((800, 680), 'UP 19.00', font=font(26, 'sans'), fill=chalk)
    for k in range(30):
        x, y = rnd.uniform(520, 1010), rnd.uniform(400, 760)
        d.ellipse((x - 18, y - 6, x + 18, y + 6), fill=(200, 200, 190, rnd.randint(6, 16)))

    # The luggage tag: manila card, a reinforced eyelet, C-114 in a parent's hand.
    d.rectangle(R_TAG, fill=(198, 170, 116))
    d.polygon([(0, 640), (40, 640), (0, 680)], fill=(30, 30, 28))
    d.polygon([(128, 640), (88, 640), (128, 680)], fill=(30, 30, 28))
    d.ellipse((46, 656, 82, 692), fill=(150, 122, 72))
    d.ellipse((56, 666, 72, 682), fill=(30, 30, 28))
    layer = Image.new('RGBA', (256, 128), (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((22, 24), 'C-114', font=font(56, 'serif'), fill=(36, 34, 60, 255))
    layer = layer.rotate(90, expand=True).rotate(4, resample=Image.BICUBIC)
    img.paste(layer.crop((0, 0, 128, 256)), (0, 700 - 60), layer.crop((0, 0, 128, 256)))
    d.line((16, 860, 112, 852), fill=(36, 34, 60), width=3)

    # Ring C's roundel at the bottom landing.
    d.rectangle(R_RINGC, fill=(40, 46, 42))
    d.ellipse((150, 662, 362, 874), outline=cream, width=12)
    text_c((150, 662, 362, 874), 'C', font(150), cream)

    # The car's notice: 8 persons, 600 kg; by the grade card; in service.
    d.rectangle(R_CAR, fill=(206, 196, 168))
    d.rectangle((644, 900, 892, 1020), outline=ink, width=4)
    text_c((648, 906, 888, 946), '8 PERSONS', font(30), ink)
    text_c((648, 946, 888, 980), '600 kg', font(26), ink)
    text_c((648, 982, 888, 1016), 'GRADES 1–2', font(22, 'sans'), ink)

    # The stair's hazard board: chevrons, a broken stair.
    d.rectangle(R_HAZARD, fill=(196, 168, 60))
    for k in range(-2, 12):
        x = 640 + k * 26
        d.polygon([(x, 896), (x + 13, 896), (x + 13 + 26, 768), (x + 26, 768)], fill=ink)
    d.rectangle((700, 784, 836, 880), fill=(196, 168, 60))
    for k in range(3):
        d.rectangle((708 + k * 18, 800 + k * 14, 728 + k * 18, 806 + k * 14), fill=ink)
    for k in range(2):
        d.rectangle((790 + k * 18, 846 + k * 14, 810 + k * 18, 852 + k * 14), fill=ink)
    d.line((762, 836, 778, 818), fill=ink, width=6)

    # The relocation poster: a tower in sunlight over the haze, an arrow up, the grades.
    d.rectangle(R_POSTER, fill=(64, 92, 112))
    for k in range(9):
        d.rectangle((896, 768 + k * 14, 1024, 782 + k * 14), fill=(min(255, 200 + k * 6), min(255, 160 + k * 10), 90 + k * 8))
    d.rectangle((944, 820, 976, 960), fill=(40, 50, 58))
    d.polygon([(944, 820), (960, 790), (976, 820)], fill=(40, 50, 58))
    for k in range(5):
        d.rectangle((952, 830 + k * 24, 968, 840 + k * 24), fill=(240, 200, 120))
    d.rectangle((896, 960, 1024, 1024), fill=(30, 40, 46))
    arrow(924, 990, 20, cream)
    d.text((946, 974), 'UP', font=font(30), fill=cream)

    # The load gauge's face: cream, EMPTY in black at the left, a band to LOADED, the needle drawn by the game.
    gx, gy = 512, 896
    d.rectangle(R_GAUGE, fill=(30, 30, 28))
    d.ellipse((gx - 120, gy - 120, gx + 120, gy + 120), fill=(214, 206, 180), outline=(120, 96, 40), width=8)
    for k in range(11):
        a = math.radians(225 - k * 27)
        r0, r1 = (78, 106) if k % 5 == 0 else (90, 106)
        d.line((gx + r0 * math.cos(a), gy - r0 * math.sin(a), gx + r1 * math.cos(a), gy - r1 * math.sin(a)), fill=ink, width=5)
    d.arc((gx - 70, gy - 70, gx + 70, gy + 70), start=-45 - 54, end=-45, fill=ink, width=10)
    d.text((gx - 92, gy + 50), '0', font=font(26), fill=ink)
    d.text((gx + 50, gy + 50), '600', font=font(22), fill=ink)

    # Plain tags, other families'.
    for k in range(2):
        x0 = 128 + k * 128
        d.rectangle((x0, 896, x0 + 128, 1024), fill=(188, 162, 112) if k else (204, 196, 170))
        d.ellipse((x0 + 54, 908, x0 + 74, 928), fill=(30, 30, 28))
        d.text((x0 + 20, 950), ('C-108', 'C-102')[k], font=font(28, 'serif'), fill=(40, 38, 60))

    # The label on the case itself: cream paper, a ruled border, C over 114 in ink, big enough to read in the shot.
    d.rectangle(R_LABEL, fill=(214, 202, 168))
    d.rectangle((6, 902, 122, 1018), outline=(60, 50, 40), width=4)
    text_c((8, 904, 120, 958), 'C', font(52, 'serif'), (36, 34, 60))
    text_c((8, 956, 120, 1014), '114', font(46, 'serif'), (36, 34, 60))

    img = age(img, 1011, 0.45)
    img.save(ATLAS)


# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------

def _shared(name, make):
    return bpy.data.materials.get(name) or make()


def up_materials(m):
    """The scene's materials: the chapter's shared ones by name (made here only when built on its own), and its own."""
    U = {}
    for k in ('concrete', 'wall', 'steel', 'depot_green', 'yellow', 'wood', 'paper', 'rubber', 'copper', 'shutter'):
        U[k] = m[k]
    U['iron'] = _shared('CastIron', lambda: worn_material('CastIron', base=(0.035, 0.034, 0.032), dirt=(0.05, 0.03, 0.018),
                                                          chip=(0.13, 0.12, 0.1), rough=0.75, chip_rough=0.45, metallic=0.5))
    U['plate'] = _shared('PlateSteel', lambda: worn_material('PlateSteel', base=(0.11, 0.115, 0.11), dirt=(0.06, 0.04, 0.025),
                                                             chip=(0.2, 0.19, 0.17), rough=0.55, chip_rough=0.4, metallic=0.7))
    U['bright'] = _shared('PawlSteel', lambda: worn_material('PawlSteel', base=(0.3, 0.29, 0.27), dirt=(0.08, 0.06, 0.04),
                                                             chip=(0.55, 0.53, 0.5), rough=0.4, chip_rough=0.3, metallic=0.85))
    U['brass'] = _shared('Brass', lambda: simple_material('Brass', (0.45, 0.32, 0.12), 0.45, metallic=0.8))
    U['rock'] = _shared('CaveRock', lambda: worn_material('CaveRock', base=(0.05, 0.048, 0.045), dirt=(0.028, 0.026, 0.024),
                                                          chip=(0.085, 0.08, 0.072), rough=0.95, chip_rough=0.9, metallic=0.0))
    U['toy'] = _shared('ToyFabric', lambda: worn_material('ToyFabric', base=(0.36, 0.33, 0.3), dirt=(0.18, 0.15, 0.12),
                                                          chip=(0.42, 0.4, 0.36), rough=0.95, chip_rough=0.95, metallic=0.0))
    U['toypatch'] = _shared('ToyPatch', lambda: worn_material('ToyPatch', base=(0.42, 0.3, 0.08), dirt=(0.2, 0.14, 0.05),
                                                              chip=(0.3, 0.32, 0.4), rough=0.95, chip_rough=0.95, metallic=0.0))
    U['childpaint'] = _shared('ChildPaint', lambda: worn_material('ChildPaint', base=(0.12, 0.24, 0.42), dirt=(0.06, 0.09, 0.12),
                                                                  chip=(0.2, 0.14, 0.08), rough=0.6, chip_rough=0.8, metallic=0.0))
    U['cream'] = _shared('DustyCream', lambda: worn_material('DustyCream', base=(0.5, 0.46, 0.35), dirt=(0.3, 0.26, 0.18),
                                                             chip=(0.03, 0.027, 0.022), rough=0.85, chip_rough=0.55, metallic=0.0))
    U['cloth'] = _shared('AtriumCloth', lambda: simple_material('AtriumCloth', (0.2, 0.13, 0.065), 0.9))
    U['dark'] = _shared('SectionCap', lambda: simple_material('SectionCap', (0.012, 0.011, 0.01), 0.95))
    U['cable'] = _shared('Cable', lambda: simple_material('Cable', (0.014, 0.013, 0.012), 0.55))
    U['deadbulb'] = _shared('DeadBulb', lambda: simple_material('DeadBulb', (0.16, 0.16, 0.15), 0.25))
    U['glass'] = _shared('DirtyGlass', lambda: simple_material('DirtyGlass', (0.03, 0.035, 0.035), 0.25, metallic=0.2))
    U['rust'] = _shared('AtriumRust', lambda: simple_material('AtriumRust', (0.11, 0.048, 0.025), 0.85))
    U['masonry'] = _shared('AtriumMasonry', lambda: simple_material('AtriumMasonry', (0.15, 0.135, 0.115), 0.85))
    # This scene's own (game/undelivered/index.html needs entries for these; see the report).
    U['leather'] = worn_material('LuggageLeather', base=(0.15, 0.08, 0.045), dirt=(0.06, 0.035, 0.02), chip=(0.27, 0.18, 0.11),
                                 rough=0.62, chip_rough=0.8, metallic=0.0, grime_scale=12.0, chip_scale=40.0, chip_amount=0.74)
    U['canvas'] = worn_material('LuggageCanvas', base=(0.13, 0.135, 0.105), dirt=(0.07, 0.065, 0.05), chip=(0.21, 0.2, 0.16),
                                rough=0.9, chip_rough=0.9, metallic=0.0, grime_scale=10.0, chip_scale=30.0, chip_amount=0.72)
    U['paint'] = worn_material('FloorPaint', base=(0.42, 0.39, 0.3), dirt=(0.2, 0.18, 0.13), chip=(0.075, 0.074, 0.07),
                               rough=0.85, chip_rough=0.92, metallic=0.0, grime_scale=3.0, chip_scale=14.0, chip_amount=0.58)
    U['polished'] = simple_material('BrassPolished', (0.8, 0.62, 0.32), 0.22, metallic=1.0)
    U['uplamp'] = emission_material('LiftUpLampGlow', (1.0, 0.58, 0.18), 0.0)
    U['svclamp'] = emission_material('ServiceUpLampGlow', (1.0, 0.58, 0.18), 0.0)
    U['lobbybulb'] = emission_material('LobbyBulb', (1.0, 0.84, 0.6), 0.0)
    U['carlamp'] = emission_material('CarLamp', (1.0, 0.9, 0.75), 0.0)
    U['cranklamp'] = emission_material('CrankLamp', (1.0, 0.86, 0.64), 0.0)
    U['sky'] = emission_material('ShaftSky', (0.62, 0.74, 0.9), 0.6)
    mat, nt, bsdf = d17._new_material('UpOnlyAtlasMat')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(ATLAS, check_existing=True)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.6
    U['atlas'] = mat
    return U


# --------------------------------------------------------------------------
# What was there: the balcony stair, the atrium's homes where the lobby stands
# --------------------------------------------------------------------------

DWELLINGS = ('AtriumRust', 'AtriumSheet', 'AtriumWood', 'AtriumOpenings', 'AtriumCloth', 'AtriumSigns', 'AtriumWindowGlow',
             'AtriumLamps', 'AtriumHomes', 'AtriumMasonry', 'AtriumCables', 'AtriumRedLamps', 'AtriumBarricades', 'AtriumPlaster')


def clear_site():
    """The balcony stair (in G4Balcony and its rail) is taken out: the porch carries the deck on, and the stair is
    rebuilt collapsed beside the lift. The atrium's container homes stacked where the lobby and the bottom landing
    now stand are taken out too (faces centred in the site's box)."""
    bpy.context.view_layer.update()                    # insert_scenes() moved things: refresh matrix_world first
    out = {}
    out['G4Balcony'] = remove_faces('G4Balcony', lambda c: c.x > BALCONY_END + 0.01)
    out['G4BalconyRail'] = remove_faces('G4BalconyRail', lambda c: c.x > BALCONY_END + 0.05 and c.y < 1.2)
    for name in DWELLINGS:
        n = remove_faces(name, lambda c: 116.5 < c.x < 131.4 and -3.0 < c.y < 4.2 and -1.0 < c.z < 9.5)
        if n:
            out[name] = n
    print('up_only: removed faces', out)


# --------------------------------------------------------------------------
# The porch, the lobby's shell, the foundation
# --------------------------------------------------------------------------

def build_shell(U, coll, dl01):
    B = Batch(U)
    con, wall, grn, stl, yel, mas, rock = B('concrete'), B('wall'), B('depot_green'), B('steel'), B('yellow'), B('masonry'), B('rock')
    x0, x1 = PORCH[0], CW_SHAFT[0]
    # Floors: the porch (the balcony's width), the lobby (back to its back wall; in front of the lift only to the wall).
    bx(B.bm, (PORCH[0], PORCH[1]), (-1.0, 2.4), (DECK - 0.3, DECK), con, 0.02)
    bx(B.bm, (PORCH[1], LIFT_WALL[0]), (-1.0, BACK_Y + 0.2), (DECK - 0.3, DECK), con, 0.02)
    bx(B.bm, (LIFT_WALL[0], x1), (-1.0, WALL_Y + WALL_T), (DECK - 0.3, DECK), con, 0.02)
    for x in [x0 + 0.6 * k for k in range(1, int((x1 - x0) / 0.6) + 1)]:             # paving joints
        if x < x1 - 0.05:
            y1 = 2.4 if x < PORCH[1] else (BACK_Y if x < LIFT_WALL[0] else WALL_Y)
            bx(B.bm, (x - 0.006, x + 0.006), (-1.0, y1), (DECK - 0.004, DECK + 0.001), B('dark'))
    bx(B.bm, (x0, x1), (-1.03, -0.99), (DECK - 0.33, DECK + 0.005), stl, 0.008)          # a steel nosing on the deck's edge
    # The porch: steel beams under it into the rock, the balcony's rail carried on behind it.
    for y in (-0.7, 0.9, 2.1):
        bx(B.bm, (PORCH[0], PORCH[1] + 0.4), (y - 0.08, y + 0.08), (DECK - 0.62, DECK - 0.3), stl, 0.01)
    for x in (PORCH[0] + 0.5, PORCH[1] - 0.3):
        add_cyl(B.bm, (x, 0.9, DECK - 0.6), (x + 0.9, 0.9, -0.8), 0.06, seg=8, mat=stl)
    x = 117.0
    while x < PORCH[1] - 0.1:
        bx(B.bm, (x - 0.02, x + 0.02), (2.34, 2.38), (DECK, DECK + 1.0), yel)
        x += 0.5
    for z in (DECK + 0.5, DECK + 0.98):
        bx(B.bm, (PORCH[0], PORCH[1] - 0.1), (2.34, 2.38), (z - 0.02, z + 0.02), yel)
    # The foundation under the lobby: a concrete face from the deck down into the rock, pilasters, a drain, a vent.
    bx(B.bm, (PORCH[1], LIFT_WALL[0]), (-0.95, BACK_Y + 0.6), (-2.6, DECK - 0.3), con)
    bx(B.bm, (LIFT_WALL[0], x1), (-0.95, WALL_Y + WALL_T), (-2.6, DECK - 0.3), con)
    bx(B.bm, (LIFT_WALL[0], x1), (WALL_Y + WALL_T, SHAFT_BACK), (-2.6, 0.3), con)          # the car's pit floor
    for dx in (-0.4, 0.4):                                                         # the car's buffers
        add_cyl(B.bm, (CAR_C[0] + dx, CAR_C[1], 0.3), (CAR_C[0] + dx, CAR_C[1], 0.62), 0.07, seg=12, mat=stl)
        add_cyl(B.bm, (CAR_C[0] + dx, CAR_C[1], 0.62), (CAR_C[0] + dx, CAR_C[1], 0.68), 0.085, seg=12, mat=B('rubber'))
    for x in (PORCH[1] + 0.2, 121.2, 123.6, 126.0):
        bx(B.bm, (x - 0.22, x + 0.22), (-1.02, -0.9), (-1.2, DECK - 0.3), con, 0.03)
    for z in (0.15, 0.75):
        bx(B.bm, (PORCH[1] + 0.4, x1 - 0.1), (-0.97, -0.95), (z - 0.01, z + 0.01), B('dark'))
    add_cyl(B.bm, (122.4, -1.0, DECK - 0.35), (122.4, -1.0, -0.5), 0.05, seg=10, mat=stl)
    for z in (1.1, 0.4):
        add_cyl(B.bm, (122.4, -1.06, z), (122.4, -0.95, z), 0.065, seg=10, mat=stl)
    for z, r in ((1.08, 0.045), (0.94, 0.035)):                                      # pipes along under the deck
        add_cyl(B.bm, (PORCH[1], -1.05, z), (x1 - 0.05, -1.05, z), r, seg=10, mat=stl)
    for x in (PORCH[1] + 0.6, 121.0, 123.0, 125.0, 126.5):
        bx(B.bm, (x - 0.03, x + 0.03), (-1.1, -0.95), (0.88, 1.15), stl, 0.006)
    bx(B.bm, (PORCH[1] + 0.2, x1 - 0.05), (-1.1, -0.96), (0.62, 0.66), stl, 0.006)                # a cable tray
    add_cyl(B.bm, (PORCH[1] + 0.2, -1.04, 0.69), (x1 - 0.05, -1.04, 0.69), 0.02, seg=6, mat=B('rubber'))
    bx(B.bm, (124.6, 125.1), (-0.99, -0.94), (0.15, 0.45), B('dark'))
    for k in range(5):
        bx(B.bm, (124.62 + k * 0.1, 124.64 + k * 0.1), (-1.0, -0.97), (0.15, 0.45), stl)
    # The waiting area: its back wall, a green dado and a dark skirting, pilasters; the ceiling slab; the entrance.
    bx(B.bm, (LOBBY_X0, LIFT_WALL[0]), (BACK_Y, BACK_Y + 0.25), (DECK, CEIL), wall)
    bx(B.bm, (LOBBY_X0, LIFT_WALL[0]), (BACK_Y - 0.012, BACK_Y), (DECK + 0.12, DECK + 1.15), grn)
    bx(B.bm, (LOBBY_X0, LIFT_WALL[0]), (BACK_Y - 0.02, BACK_Y), (DECK, DECK + 0.12), stl)
    bx(B.bm, (LOBBY_X0, LIFT_WALL[0]), (BACK_Y - 0.03, BACK_Y), (DECK + 1.15, DECK + 1.19), stl, 0.006)
    for x in (LOBBY_X0 + 0.3, 121.2):
        bx(B.bm, (x - 0.16, x + 0.16), (BACK_Y - 0.1, BACK_Y), (DECK, CEIL), wall, 0.02)
        bx(B.bm, (x - 0.18, x + 0.18), (BACK_Y - 0.12, BACK_Y), (CEIL - 0.25, CEIL), wall, 0.02)
    bx(B.bm, (LOBBY_X0 - 0.15, LIFT_WALL[0] + 0.1), (-1.0, BACK_Y + 0.25), (CEIL, CEIL + 0.32), con, 0.02)
    bx(B.bm, (LOBBY_X0 - 0.15, LIFT_WALL[0] + 0.1), (-1.06, -0.98), (CEIL - 0.08, CEIL + 0.04), stl, 0.01)
    bx(B.bm, (LOBBY_X0 - 0.15, LIFT_WALL[0]), (BACK_Y - 0.08, BACK_Y), (CEIL - 0.14, CEIL), wall, 0.01)   # cornice
    # The entrance: a wall behind the lane, a lintel across it (deep enough to read as a doorway from the porch).
    bx(B.bm, (LOBBY_X0 - 0.15, LOBBY_X0 + 0.15), (0.55, 2.4), (DECK, CEIL + 0.32), wall, 0.02)
    bx(B.bm, (LOBBY_X0 - 0.15, LOBBY_X0 + 0.15), (-1.0, 0.55), (DECK + 2.05, CEIL), wall, 0.02)
    bx(B.bm, (LOBBY_X0 - 0.2, LOBBY_X0 - 0.15), (-1.0, 0.6), (DECK + 2.0, DECK + 2.08), stl, 0.008)
    bx(B.bm, (LOBBY_X0 - 0.2, LOBBY_X0 - 0.15), (0.55, 0.62), (DECK, DECK + 2.05), stl, 0.008)
    # The porch's lamp bracket and the entrance sign's rods (the sign is on the atlas).
    bx(B.bm, (117.2, LOBBY_X0 - 0.15), (0.84, 0.92), (DECK + 2.46, DECK + 2.52), stl, 0.008)
    for x in (117.35, 118.45):
        add_cyl(B.bm, (x, 0.89, DECK + 2.46), (x, 0.89, DECK + 2.28), 0.006, seg=6, mat=stl)
    # Above the ceiling, the lobby's masonry back; the shafts' back wall, high, with ties.
    bx(B.bm, (LOBBY_X0 - 0.15, LIFT_WALL[0]), (BACK_Y, BACK_Y + 0.35), (CEIL + 0.32, 8.0), mas)
    bx(B.bm, (LIFT_WALL[0] - 0.05, RIGHT_WALL[1] + 0.3), (SHAFT_BACK, SHAFT_BACK + 0.3), (PIT_Z, 9.0), con)
    for z in (2.6, 4.4, 6.2):
        bx(B.bm, (LIFT_WALL[0], RIGHT_WALL[0]), (SHAFT_BACK - 0.06, SHAFT_BACK), (z - 0.06, z + 0.06), stl, 0.008)
    # The car's shaft walls (left; the pier between the shafts), up to the head frame.
    bx(B.bm, (LIFT_WALL[0], LIFT_WALL[0] + 0.15), (WALL_Y, SHAFT_BACK), (DECK - 1.6, 4.6), wall)
    bx(B.bm, (126.1, CW_SHAFT[0]), (WALL_Y, SHAFT_BACK), (DECK - 0.3, 4.6), wall)
    # The counterweight's shaft: its far wall over the bottom landing; the pit; the slot on up into the rock.
    bx(B.bm, RIGHT_WALL, (-0.62, SHAFT_BACK), (LANDING_Z1, 4.6), wall)
    bx(B.bm, (RIGHT_WALL[0] - 0.02, RIGHT_WALL[1] + 0.02), (-0.66, -0.6), (LANDING_Z1 - 0.02, 4.62), stl, 0.008)
    for k in range(6):                                                             # chevrons on its foot
        x = RIGHT_WALL[0] + 0.02 + k * 0.05
        bx(B.bm, (x, x + 0.025), (-0.62, SHAFT_BACK), (LANDING_Z1, LANDING_Z1 + 0.12), yel)
    bx(B.bm, (CW_SHAFT[0], CW_SHAFT[1]), (-0.95, SHAFT_BACK), (PIT_Z - 0.3, PIT_Z), con)
    bx(B.bm, (CW_SHAFT[1], CW_SHAFT[1] + 0.25), (-0.95, SHAFT_BACK), (PIT_Z - 0.3, -0.3), con)
    for x in (CW_SHAFT[0] - 0.15, RIGHT_WALL[1] - 0.1):
        bx(B.bm, (x, x + 0.25), (-0.4, SHAFT_BACK), (6.8, 13.0), rock)
    bx(B.bm, (CW_SHAFT[0] - 0.15, RIGHT_WALL[1] + 0.15), (SHAFT_BACK - 0.2, SHAFT_BACK + 0.3), (9.0, 13.0), rock)
    # The rock over the head frame, either side of the slot (seen only in a wide framing).
    bx(B.bm, (LIFT_WALL[0] - 0.05, CW_SHAFT[0] - 0.15), (0.6, SHAFT_BACK), (7.2, 9.5), rock)
    B.done('UOShell', coll)

    # The ring C side: the bottom landing's floor and the rock under it, its back wall, its roundel.
    lx = ledge_x0(dl01)
    B = Batch(U)
    con, rock, yel, stl = B('concrete'), B('rock'), B('yellow'), B('steel')
    bx(B.bm, (CW_SHAFT[1], lx + 0.02), (-0.7, 1.95), (-0.3, 0.0), con, 0.015)
    for x in [CW_SHAFT[1] + 0.6 * k for k in range(1, 6)]:
        if x < lx - 0.1:
            bx(B.bm, (x - 0.006, x + 0.006), (-0.7, 1.95), (-0.004, 0.001), B('dark'))
    bx(B.bm, (CW_SHAFT[1], CW_SHAFT[1] + 0.1), (-0.7, 1.0), (-0.02, 0.006), yel)          # the sill, painted
    rounded_box((lx - CW_SHAFT[1] + 0.6, 3.0, 2.6), ((CW_SHAFT[1] + lx) / 2 + 0.1, 0.4, -1.65), p=3.0, cuts=4,
                dents=((0.1, 2.2), (0.03, 7.0)), seed=4.0, mat=rock, bm=B.bm)
    bx(B.bm, (RIGHT_WALL[0], lx + 0.3), (1.95, 2.3), (-0.3, 5.2), B('masonry'))           # the back: old masonry
    for k in range(4):
        z = 0.6 + k * 1.2
        bx(B.bm, (RIGHT_WALL[0], lx + 0.3), (1.93, 1.95), (z - 0.01, z + 0.01), B('dark'))
    rnd = random.Random(1012)
    for k in range(8):                                                              # rock bulging through it, high
        s = rnd.uniform(0.5, 1.1)
        rounded_box((s * 1.4, s, s * 1.2), (rnd.uniform(129.0, lx + 0.4), 1.9 + s * 0.3, rnd.uniform(2.6, 5.2)), p=2.5,
                    cuts=3, dents=((s * 0.12, 2.4),), seed=k * 3.1, mat=rock, bm=B.bm)
    sign(B, (128.3, 1.925, 0.95), 0.38, 0.38, R_RINGC, B('atlas'))
    # The bottom landing's gate, rusted open and folded against the shaft's far wall.
    for k in range(7):
        y = 0.55 + k * 0.05
        bx(B.bm, (RIGHT_WALL[0] + 0.02, RIGHT_WALL[0] + 0.04), (y - 0.008, y + 0.008), (0.03, LANDING_Z1 - 0.05), stl)
    for z in (0.05, LANDING_Z1 - 0.08):
        bx(B.bm, (RIGHT_WALL[0] + 0.01, RIGHT_WALL[0] + 0.05), (0.52, 0.9), (z, z + 0.025), stl)
    B.done('UOLanding', coll)


# --------------------------------------------------------------------------
# The waiting area: the luggage, the queue, what was dropped, the bench, the boards, the lamp
# --------------------------------------------------------------------------

def suitcase(bm, c, size, rot, mat_body, mat_trim, mat_handle, latches=True, straps=False, mat_strap=None):
    """A suitcase standing on its long edge: length along local x, thickness y, height z; c is its base centre."""
    L, T, H = size
    M = Matrix.Translation(c) @ rot
    tmp = bmesh.new()
    rounded_box((L, T, H), (0, 0, H / 2), p=6, cuts=2, dents=((0.004, 5.0),), seed=c[0], mat=mat_body, bm=tmp)
    bx(tmp, (-L / 2 + 0.01, L / 2 - 0.01), (-T / 2 - 0.004, T / 2 + 0.004), (H * 0.52, H * 0.56), mat_trim)   # the lid's seam
    for sx in (-1, 1):
        for sz in (0, 1):
            cbox(tmp, (sx * (L / 2 - 0.018), 0, 0.018 + sz * (H - 0.036)), (0.04, T + 0.012, 0.04), 0.006, mat_trim)  # corners
    if latches:
        for sx in (-1, 1):
            bx(tmp, (sx * L * 0.3 - 0.016, sx * L * 0.3 + 0.016), (-T / 2 - 0.008, -T / 2), (H * 0.48, H * 0.6), mat_trim)
    if straps and mat_strap is not None:
        for sx in (-1, 1):
            bx(tmp, (sx * L * 0.22 - 0.014, sx * L * 0.22 + 0.014), (-T / 2 - 0.005, T / 2 + 0.005), (-0.002, H + 0.004), mat_strap)
    for sx in (-1, 1):                                                         # the handle's lugs and grip
        bx(tmp, (sx * 0.05 - 0.008, sx * 0.05 + 0.008), (-0.012, 0.012), (H - 0.002, H + 0.014), mat_trim)
    add_cyl(tmp, (-0.05, 0, H + 0.019), (0.05, 0, H + 0.019), 0.0085, seg=8, mat=mat_handle)
    for sx in (-1, 1):
        add_cyl(tmp, (sx * 0.05, 0, H + 0.012), (sx * 0.044, 0, H + 0.019), 0.0085, seg=8, mat=mat_handle)
    bmesh.ops.transform(tmp, matrix=M, verts=tmp.verts)
    me = bpy.data.meshes.new('_t')
    tmp.to_mesh(me)
    tmp.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def build_luggage(U, coll):
    """The heap of left luggage against the back wall, and the queue line with what was dropped along it."""
    B = Batch(U)
    lea, can, brs, stl, wood, pap, cloth = B('leather'), B('canvas'), B('brass'), B('steel'), B('wood'), B('paper'), B('cloth')
    rnd = random.Random(1013)
    z = DECK
    # The heap: a trunk at the bottom, cases stacked and leaning, duffels, a hatbox, a bedroll, tags.
    bx(B.bm, (119.1, 119.95), (0.62, 1.16), (z, z + 0.46), wood, 0.012)
    for x in (119.18, 119.87):
        bx(B.bm, (x - 0.03, x + 0.03), (0.6, 1.18), (z - 0.002, z + 0.462), stl, 0.006)
    for zz in (z + 0.1, z + 0.36):
        bx(B.bm, (119.08, 119.97), (0.6, 1.18), (zz - 0.02, zz + 0.02), stl, 0.006)
    bx(B.bm, (119.45, 119.6), (0.58, 0.62), (z + 0.3, z + 0.4), brs, 0.004)
    cases = (                                                                    # base centre, size, yaw, tilt (about x), body
        ((120.25, 0.85, z), (0.62, 0.2, 0.42), 0.05, 1.5708, lea),           # lying flat
        ((120.27, 0.86, z + 0.205), (0.56, 0.18, 0.38), -0.08, 1.5708, can),
        ((119.55, 0.86, z + 0.46), (0.6, 0.19, 0.4), 0.12, 1.5708, lea),
        ((119.5, 0.95, z + 0.65), (0.46, 0.16, 0.34), -0.2, 1.5708, can),
        ((120.62, 0.7, z), (0.5, 0.16, 0.36), 0.25, 0.0, can),               # standing
        ((120.15, 0.82, z + 0.39), (0.42, 0.15, 0.3), 0.6, 0.0, lea),
        ((119.85, 0.98, z + 0.81), (0.36, 0.14, 0.28), -0.4, 0.35, lea),
        ((120.8, 0.98, z), (0.34, 0.14, 0.4), -0.1, 0.0, lea),
    )
    for c, size, yaw, tilt, body in cases:
        suitcase(B.bm, c, size, _rz(yaw) @ _rx(tilt), body, stl, lea, straps=rnd.random() < 0.5, mat_strap=lea)
    for c, r, l in (((120.55, 0.95, z + 0.58), 0.13, 0.55), ((119.25, 0.9, z + 0.99), 0.12, 0.5)):      # duffels
        rounded_box((l, r * 2, r * 1.8), c, p=2.2, cuts=3, dents=((0.012, 6.0),), seed=c[0], mat=can, bm=B.bm, rot=_rz(0.3))
        add_torus(B.bm, (c[0], c[1], c[2] + r * 0.9), (0, 1, 0), 0.07, 0.008, mat=lea, seg=12, rseg=4)
    add_cyl(B.bm, (120.05, 0.95, z + 0.97), (120.05, 0.95, z + 1.17), 0.15, seg=18, mat=pap)              # a hatbox
    add_cyl(B.bm, (120.05, 0.95, z + 1.17), (120.05, 0.95, z + 1.19), 0.155, seg=18, mat=pap)
    rounded_box((0.7, 0.24, 0.24), (119.4, 0.75, z + 0.58), p=2.0, cuts=3, dents=((0.01, 5.0),), seed=3, mat=cloth, bm=B.bm,
                rot=_rz(-0.15))                                                  # a bedroll, tied
    for dx in (-0.22, 0.22):
        add_torus(B.bm, (119.4 + dx, 0.75 + dx * 0.15, z + 0.58), (1, -0.15, 0), 0.122, 0.006, mat=stl, seg=14, rseg=4)
    for k, (x, y, zz) in enumerate(((119.62, 0.64, z + 0.6), (120.42, 0.6, z + 0.3), (120.66, 0.61, z + 0.24))):    # tags
        rect = (R_TAGS[0] + (k % 2) * 128, R_TAGS[1], R_TAGS[0] + (k % 2) * 128 + 128, R_TAGS[3])
        sign(B, (x, y, zz), 0.05, 0.05, rect, B('atlas'), face=(math.sin(0.2 * k), -1, 0), tilt=0.2)

    # The queue line: two worn painted edges along the lane, footprints between them, an arrow turning in to the gate.
    pnt = B('paint')
    for y in QUEUE_Y:
        bx(B.bm, (QUEUE[0], QUEUE[1]), (y - 0.03, y + 0.03), (z, z + 0.002), pnt)
    bx(B.bm, (QUEUE[0] - 0.03, QUEUE[0] + 0.03), (QUEUE_Y[0], QUEUE_Y[1]), (z, z + 0.002), pnt)
    bx(B.bm, (QUEUE[1] - 0.03, QUEUE[1] + 0.03), (QUEUE_Y[0], QUEUE_Y[1] - 0.18), (z, z + 0.002), pnt)
    for k in range(9):                                                           # pairs of feet, waiting
        x = QUEUE[0] + 0.35 + k * 0.5
        for dy, dx in ((-0.12, 0.0), (0.04, 0.04)):
            for part, (ox, r) in enumerate(((0.0, 0.045), (-0.085, 0.035))):
                add_cyl(B.bm, (x + dx + ox, -0.1 + dy, z), (x + dx + ox, -0.1 + dy, z + 0.0015), r, seg=10, mat=pnt)
    bx(B.bm, (124.6, 125.3), (-0.08, -0.02), (z, z + 0.002), pnt)                 # the turn in, under the sign
    for k in range(3):
        bx(B.bm, (124.92, 124.98), (-0.02 + k * 0.1, 0.06 + k * 0.1), (z, z + 0.002), pnt)
    tri = [B.bm.verts.new((124.95 + dx, dy, z + 0.0021)) for dx, dy in ((-0.1, 0.3), (0.1, 0.3), (0.0, 0.42))]
    B.bm.faces.new(tri).material_index = pnt
    B.done('UOLuggage', coll)

    # Dropped along the line: a case burst open, a child's shoe, a doll, an empty birdcage.
    B = Batch(U)
    can, lea, stl, cloth = B('canvas'), B('leather'), B('steel'), B('cloth')
    c = Vector((121.95, 0.58, z))
    rounded_box((0.44, 0.3, 0.07), c + Vector((0, 0, 0.035)), p=6, cuts=2, seed=2, mat=can, bm=B.bm, rot=_rz(0.25))
    lid = _rz(0.25) @ Matrix.Translation((0, 0.15, 0.07)) @ _rx(math.radians(-110)) @ Matrix.Translation((0, 0.15, 0.035))
    rounded_box((0.44, 0.3, 0.07), c, p=6, cuts=2, seed=3, mat=can, bm=B.bm, rot=lid)
    for k in range(4):                                                          # clothes spilling
        rounded_box((rnd.uniform(0.18, 0.3), rnd.uniform(0.12, 0.22), 0.03),
                    c + Vector((rnd.uniform(-0.25, 0.2), rnd.uniform(-0.32, -0.08), 0.015 + 0.01 * k)), p=2.0, cuts=2,
                    dents=((0.008, 9.0),), seed=k, mat=cloth if k % 2 else B('cream'), bm=B.bm, rot=_rz(rnd.uniform(0, 3)))
    # The shoe: a child's T-bar, blue, on its side on the front line.
    shoe = Matrix.Translation((122.42, -0.36, z)) @ _rz(0.7) @ _rx(math.radians(80))
    sb = bmesh.new()
    rounded_box((0.15, 0.06, 0.016), (0, 0, 0.008), p=3, cuts=2, seed=1, mat=0, bm=sb)                  # sole
    rounded_box((0.14, 0.055, 0.05), (0.0, 0, 0.035), p=3, cuts=3, seed=2, mat=1, bm=sb,
                shape=lambda q: q.__setitem__(2, q[2] * (0.6 if q[0] < -0.2 else 1.0)))
    bx(sb, (0.0, 0.016), (-0.032, 0.032), (0.056, 0.064), 0)                                           # the strap
    add_sphere(sb, (0.008, -0.034, 0.06), 0.006, seg=6, mat=2)
    bmesh.ops.transform(sb, matrix=shoe, verts=sb.verts)
    for f in sb.faces:
        f.material_index = (lea, B('childpaint'), B('brass'))[f.material_index]
    me = bpy.data.meshes.new('_t')
    sb.to_mesh(me)
    sb.free()
    B.bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    # The doll: a rag doll on its back, arms out, a patched dress.
    dc = Vector((122.88, 0.44, z))
    M = Matrix.Translation(dc) @ _rz(-0.5)
    toy, patch = B('toy'), B('toypatch')
    for p, r, sc, mat in (((0.13, 0, 0.045), 0.05, (1, 1, 0.9), toy), ((0.0, 0, 0.04), 0.06, (1.4, 1.0, 0.6), patch),
                          ((-0.11, 0, 0.032), 0.05, (1.2, 1.3, 0.55), patch)):
        add_sphere(B.bm, M @ Vector(p), r, seg=10, scale=sc, mat=mat)
    for a, b in (((0.03, -0.05, 0.035), (0.08, -0.15, 0.025)), ((0.03, 0.05, 0.035), (0.0, 0.15, 0.025)),
                 ((-0.15, -0.03, 0.025), (-0.27, -0.06, 0.02)), ((-0.15, 0.03, 0.025), (-0.26, 0.08, 0.02))):
        add_cyl(B.bm, M @ Vector(a), M @ Vector(b), 0.016, seg=6, mat=toy)
    for dy in (-0.018, 0.018):
        add_sphere(B.bm, M @ Vector((0.15, dy, 0.085)), 0.006, seg=6, mat=B('dark'))
    for k in range(6):                                                          # yarn hair
        a = -0.9 + k * 0.36
        add_cyl(B.bm, M @ Vector((0.16, 0.04 * math.sin(a), 0.07)), M @ Vector((0.22, 0.07 * math.sin(a), 0.03)), 0.008,
                seg=4, mat=B('wood'))
    # The birdcage: a domed wire cage on a round base, its door open and empty, a ring to hang it by.
    cc = Vector((123.25, 0.72, z))
    brs = B('brass')
    add_cyl(B.bm, cc, cc + Vector((0, 0, 0.03)), 0.13, seg=20, mat=brs)
    add_torus(B.bm, cc + Vector((0, 0, 0.034)), (0, 0, 1), 0.125, 0.006, mat=brs, seg=20, rseg=4)
    add_torus(B.bm, cc + Vector((0, 0, 0.2)), (0, 0, 1), 0.12, 0.004, mat=brs, seg=20, rseg=4)
    n = 16
    for k in range(n):
        a = 2 * math.pi * k / n
        if k in (0, 1):                                                         # the door's gap
            continue
        pts = []
        for j in range(7):
            t = j / 6
            r = 0.12 * (1 if t < 0.6 else math.cos((t - 0.6) / 0.4 * math.pi / 2))
            zz = 0.034 + 0.3 * t if t < 0.6 else 0.214 + 0.12 * math.sin((t - 0.6) / 0.4 * math.pi / 2)
            pts.append(cc + Vector((r * math.cos(a), r * math.sin(a), zz)))
        for p0, p1 in zip(pts, pts[1:]):
            add_cyl(B.bm, p0, p1, 0.0025, seg=4, mat=brs)
    add_torus(B.bm, cc + Vector((0, 0, 0.36)), (1, 0, 0), 0.03, 0.005, mat=brs, seg=12, rseg=4)
    door = Matrix.Translation(cc + Vector((0.12 * math.cos(0.4), 0.12 * math.sin(0.4) - 0.06, 0.04))) @ _rz(-1.2)
    for k in range(4):
        add_cyl(B.bm, door @ Vector((0.02 * k, 0, 0)), door @ Vector((0.02 * k, 0, 0.13)), 0.0025, seg=4, mat=brs)
    add_cyl(B.bm, door @ Vector((0, 0, 0.13)), door @ Vector((0.06, 0, 0.13)), 0.003, seg=4, mat=brs)
    add_cyl(B.bm, cc + Vector((0.04, 0.02, 0.04)), cc + Vector((-0.06, -0.03, 0.04)), 0.004, seg=4, mat=B('wood'))   # a perch, fallen
    B.done('UODropped', coll)


def build_waiting(U, coll):
    """The bench, the departures board and the poster on the back wall, the pendant lamp over the queue."""
    B = Batch(U)
    wood, iron, stl, atl = B('wood'), B('iron'), B('steel'), B('atlas')
    z = DECK
    # The bench: slats on cast iron ends.
    for x in (121.85, 123.35):
        bx(B.bm, (x - 0.03, x + 0.03), (0.78, 1.14), (z, z + 0.44), iron, 0.008)
        bx(B.bm, (x - 0.03, x + 0.03), (1.08, 1.14), (z + 0.44, z + 0.86), iron, 0.008)
        add_cyl(B.bm, (x, 0.8, z + 0.02), (x, 1.1, z + 0.4), 0.012, seg=6, mat=iron)
    for k in range(4):
        y = 0.8 + k * 0.085
        bx(B.bm, (121.75, 123.45), (y, y + 0.07), (z + 0.42, z + 0.45), wood, 0.008)
    for k in range(2):
        bx(B.bm, (121.75, 123.45), (1.1, 1.13), (z + 0.56 + k * 0.16, z + 0.66 + k * 0.16), wood, 0.008)
    # The boards: departures (chalk) over the bench, the relocation poster over the heap.
    bx(B.bm, (121.9, 123.3), (BACK_Y - 0.03, BACK_Y), (z + 1.2, z + 2.25), B('wood'), 0.01)
    sign(B, (122.6, BACK_Y - 0.032, z + 1.725), 1.36, 1.02, R_BOARD, atl)
    bx(B.bm, (122.35, 122.55), (BACK_Y - 0.06, BACK_Y - 0.03), (z + 1.18, z + 1.22), wood, 0.004)     # the chalk ledge
    add_cyl(B.bm, (122.39, BACK_Y - 0.05, z + 1.23), (122.45, BACK_Y - 0.05, z + 1.23), 0.006, seg=6, mat=B('cream'))
    sign(B, (119.95, BACK_Y - 0.005, z + 1.95), 0.42, 0.84, R_POSTER, atl, tilt=-0.01)
    # The pendant lamp: an enamel shade on a long flex from the ceiling, its bulb failing (LobbyBulb).
    lx, ly = LAMP[0], LAMP[1]
    add_cyl(B.bm, (lx, ly, CEIL), (lx, ly, 4.24), 0.005, seg=6, mat=B('cable'))
    add_cyl(B.bm, (lx, ly, CEIL - 0.03), (lx, ly, CEIL), 0.04, seg=12, mat=stl)
    add_cyl(B.bm, (lx, ly, 4.24), (lx, ly, 4.16), 0.03, 0.03, seg=12, mat=stl)
    add_cyl(B.bm, (lx, ly, 4.17), (lx, ly, 4.07), 0.03, 0.17, seg=20, mat=B('depot_green'))
    add_cyl(B.bm, (lx, ly, 4.069), (lx, ly, 4.07), 0.17, 0.17, seg=20, mat=B('depot_green'))
    B.done('UOWaiting', coll)
    bm = bmesh.new()
    add_sphere(bm, LAMP, 0.04, seg=12, scale=(1, 1, 1.2))
    d17.mesh_object('LobbyBulb', bm, [U['lobbybulb']], coll)

    # The entrance sign, over the porch (on the atlas).
    B = Batch(U)
    sign(B, (117.9, 0.879, DECK + 2.12), 1.2, 0.3, R_ENTRY, B('atlas'))
    bx(B.bm, (117.28, 118.52), (0.881, 0.9), (DECK + 1.95, DECK + 2.29), B('steel'), 0.006)
    B.done('UOEntrySign', coll)


# --------------------------------------------------------------------------
# The lift: its front wall and gate, the panel, the car, the head frame
# --------------------------------------------------------------------------

def lattice_leaf(B, w, h, frame, bars, grip):
    """One leaf of a lattice gate in its own space: origin at its foot's centre, the leaf in the x-z plane."""
    hw = w / 2
    for sx in (-1, 1):
        bx(B.bm, (sx * hw - 0.016, sx * hw + 0.016), (-0.012, 0.012), (0.0, h), frame, 0.004)
    for zz in ((0.0, 0.05), (h - 0.05, h), (h * 0.48, h * 0.52)):
        bx(B.bm, (-hw, hw), (-0.012, 0.012), zz, frame, 0.004)
    a = hw - 0.016
    bay = 2 * a
    z0 = 0.05
    while z0 < h - 0.07:
        z1 = min(z0 + bay, h - 0.05)
        k = (z1 - z0) / bay
        for s in (-1, 1):
            p = Vector((s * a, 0, z0))
            q = Vector((s * a - s * 2 * a * k, 0, z1))
            d = q - p
            add_box(B.bm, (p + q) / 2, (0.016, 0.008, d.length), mat=bars,
                    rot=Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4())
        if k > 0.99:
            add_cyl(B.bm, (0, -0.01, (z0 + z1) / 2), (0, 0.01, (z0 + z1) / 2), 0.008, seg=6, mat=frame)
        z0 = z1
    return grip


def build_lift_front(U, coll):
    """The front wall over the lane (green below, panelled above), the architrave, the sign, the indicator, the gate."""
    B = Batch(U)
    wall, grn, stl, brs, yel = B('wall'), B('depot_green'), B('steel'), B('brass'), B('yellow')
    g0, g1, gh = GATE
    y0, y1 = WALL_Y, WALL_Y + WALL_T
    top = 4.6
    wall_x(B.bm, LIFT_WALL[0], LIFT_WALL[1], y0 + 0.012, y1, DECK, top, holes=((g0, g1, DECK, DECK + gh),), mat=wall)
    wall_x(B.bm, LIFT_WALL[0], LIFT_WALL[1], y0, y0 + 0.012, DECK + 0.12, DECK + 1.15, holes=((g0 - 0.12, g1 + 0.12, DECK, DECK + gh),), mat=grn)
    wall_x(B.bm, LIFT_WALL[0], LIFT_WALL[1], y0 - 0.006, y0 + 0.012, DECK, DECK + 0.12, holes=((g0 - 0.12, g1 + 0.12, DECK, DECK + gh),), mat=stl)
    wall_x(B.bm, LIFT_WALL[0], LIFT_WALL[1], y0 - 0.02, y0 + 0.01, DECK + 1.15, DECK + 1.19, holes=((g0 - 0.12, g1 + 0.12, DECK, DECK + gh),), mat=stl, b=0.005)
    for x in (LIFT_WALL[0] + 0.08, 126.1, LIFT_WALL[1] - 0.08):                # pilasters
        bx(B.bm, (x - 0.08, x + 0.08), (y0 - 0.06, y0 + 0.02), (DECK, top), wall, 0.015)
        bx(B.bm, (x - 0.1, x + 0.1), (y0 - 0.08, y0 + 0.02), (DECK, DECK + 0.14), stl, 0.01)
        bx(B.bm, (x - 0.1, x + 0.1), (y0 - 0.08, y0 + 0.02), (top - 0.16, top), wall, 0.015)
    # The architrave: steel with a brass bead, a brass threshold, worn bright down the middle.
    for x in (g0 - 0.07, g1 + 0.07):
        bx(B.bm, (x - 0.06, x + 0.06), (y0 - 0.035, y0 + 0.01), (DECK, DECK + gh + 0.07), stl, 0.01)
        bx(B.bm, (x - 0.008, x + 0.008), (y0 - 0.04, y0 - 0.03), (DECK + 0.02, DECK + gh + 0.05), brs)
    bx(B.bm, (g0 - 0.13, g1 + 0.13), (y0 - 0.035, y0 + 0.01), (DECK + gh, DECK + gh + 0.12), stl, 0.01)
    bx(B.bm, (g0, g1), (y0 - 0.03, CAR_Y[0] - 0.005), (DECK - 0.01, DECK + 0.004), brs)
    bx(B.bm, (g0 + 0.2, g1 - 0.2), (y0 - 0.025, CAR_Y[0] - 0.01), (DECK + 0.004, DECK + 0.005), B('polished'))
    # The gate's track over the doorway, behind the wall; the pockets either side.
    bx(B.bm, (LIFT_WALL[0] + 0.15, 126.1), (GATE_Y - 0.03, GATE_Y + 0.03), (DECK + gh + 0.02, DECK + gh + 0.1), stl)
    bx(B.bm, (LIFT_WALL[0] + 0.15, 126.1), (GATE_Y - 0.02, GATE_Y + 0.02), (DECK - 0.02, DECK + 0.004), stl)
    # The floor indicator over the doorway: a brass half-dial, the rings in order; the needle at C.
    ic = Vector(((g0 + g1) / 2, y0 - 0.04, DECK + gh + 0.82))
    bx(B.bm, (ic.x - 0.28, ic.x + 0.28), (y0 - 0.03, y0), (ic.z - 0.15, ic.z + 0.02), stl, 0.008)
    n = 14
    rim = [ic + Vector((0.25 * math.cos(math.pi * k / n), -0.01, 0.25 * math.sin(math.pi * k / n))) for k in range(n + 1)]
    for a, b in zip(rim, rim[1:]):
        add_cyl(B.bm, a, b, 0.012, seg=6, mat=brs)
    fan = [B.bm.verts.new(ic + Vector((0, -0.002, 0)))] + [B.bm.verts.new(p + Vector((0, 0.008, 0))) for p in rim]
    for a, b in zip(fan[1:], fan[2:]):
        B.bm.faces.new((fan[0], b, a)).material_index = B('cream')
    for k in range(5):                                                         # C, B, A, 2, 1
        a = math.pi * (0.9 - 0.2 * k)
        p = ic + Vector((0.2 * math.cos(a), -0.012, 0.2 * math.sin(a)))
        add_cyl(B.bm, p, p + Vector((0, -0.004, 0)), 0.018, seg=8, mat=B('dark'))
    add_cyl(B.bm, ic + Vector((0, -0.006, 0)), ic + Vector((0.17 * math.cos(math.pi * 0.9), -0.006, 0.17 * math.sin(math.pi * 0.9))),
            0.006, seg=4, mat=B('dark'))
    add_cyl(B.bm, ic + Vector((0, 0, 0)), ic + Vector((0, -0.015, 0)), 0.02, seg=10, mat=brs)
    # The sign: RELOCATION - GRADES 1-2 ONLY, EVERYONE painted across, on brass stand-offs.
    sc = Vector(((g0 + g1) / 2, y0 - 0.05, DECK + gh + 0.37))
    bx(B.bm, (sc.x - 0.84, sc.x + 0.84), (y0 - 0.045, y0 - 0.02), (sc.z - 0.22, sc.z + 0.22), stl, 0.008)
    sign(B, sc + Vector((0, -0.002, 0)), 1.6, 0.4, R_SIGN, B('atlas'))
    for dx in (-0.78, 0.78):
        for dz in (-0.17, 0.17):
            add_cyl(B.bm, sc + Vector((dx, 0.03, dz)), sc + Vector((dx, -0.006, dz)), 0.012, seg=8, mat=brs)
    # The head of the wall, and the open steel frame above it: columns, beams and braces, so the ropes and sheaves read.
    bx(B.bm, (LIFT_WALL[0], RIGHT_WALL[1]), (y0 - 0.04, y1), (top, top + 0.16), stl, 0.012)
    for x in (LIFT_WALL[0] + 0.08, 126.1, RIGHT_WALL[1] - 0.08):
        bx(B.bm, (x - 0.07, x + 0.07), (y0, y0 + 0.14), (top, 6.8), stl, 0.01)
        bx(B.bm, (x - 0.07, x + 0.07), (SHAFT_BACK - 0.14, SHAFT_BACK), (top, 6.8), stl, 0.01)
    bx(B.bm, (LIFT_WALL[0], RIGHT_WALL[1]), (y0, y0 + 0.14), (6.66, 6.8), stl, 0.01)
    for (xa, xb) in ((LIFT_WALL[0] + 0.15, 126.03), (126.17, RIGHT_WALL[1] - 0.15)):
        for s in (-1, 1):
            a = Vector((xa if s > 0 else xb, y0 + 0.07, top + 0.16))
            b = Vector((xb if s > 0 else xa, y0 + 0.07, 6.66))
            d = b - a
            add_box(B.bm, (a + b) / 2, (0.05, 0.04, d.length), mat=stl,
                    rot=Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4())
    for x in (LIFT_WALL[0] + 0.3, 125.0, 126.6, 127.4):                       # rivet heads on the head beam
        for zz in (top + 0.04, top + 0.12):
            add_sphere(B.bm, (x, y0 - 0.045, zz), 0.012, seg=6, mat=stl)
    # The head beams the sheaves stand on (either side of the rope plane), and the bearing pedestals.
    for y in (ROPE_Y - 0.2, ROPE_Y + 0.2):
        bx(B.bm, (LIFT_WALL[0], RIGHT_WALL[1]), (y - 0.07, y + 0.07), (SHEAVE_Z - 0.48, SHEAVE_Z - 0.3), stl, 0.01)
        for sx in (SHEAVE_A, SHEAVE_B):
            bx(B.bm, (sx - 0.1, sx + 0.1), (y - 0.06, y + 0.06), (SHEAVE_Z - 0.3, SHEAVE_Z - 0.06), B('iron'), 0.012)
            add_cyl(B.bm, (sx, y - 0.07, SHEAVE_Z), (sx, y + 0.07, SHEAVE_Z), 0.07, seg=14, mat=B('iron'))
    for sx in (SHEAVE_A, SHEAVE_B):                                            # the axles through
        add_cyl(B.bm, (sx, ROPE_Y - 0.28, SHEAVE_Z), (sx, ROPE_Y + 0.28, SHEAVE_Z), 0.035, seg=10, mat=B('bright'))
    # The ropes over the sheaves and across between them (static: they lie in the grooves).
    rys = (ROPE_Y - 0.025, ROPE_Y, ROPE_Y + 0.025)
    rope_arc(B.bm, (SHEAVE_A, 0, SHEAVE_Z), SHEAVE_R, math.pi, math.pi / 2, 0.011, rys, B('cable'), n=8)
    rope_arc(B.bm, (SHEAVE_B, 0, SHEAVE_Z), SHEAVE_R, math.pi / 2, 0.0, 0.011, rys, B('cable'), n=8)
    for y in rys:
        add_cyl(B.bm, (SHEAVE_A, y, SHEAVE_Z + SHEAVE_R), (SHEAVE_B, y, SHEAVE_Z + SHEAVE_R), 0.011, seg=6, mat=B('cable'))
    # The car's guide rails, and the counterweight's, down their shafts.
    for x in CAR_RAILS:
        bx(B.bm, (x - 0.012, x + 0.012), (CAR_C[1] - 0.045, CAR_C[1] + 0.045), (0.3, 6.6), stl)
        bx(B.bm, (x - 0.035, x + 0.035), (CAR_C[1] + 0.035, CAR_C[1] + 0.05), (0.3, 6.6), stl)
    for x in CW_RAILS:
        bx(B.bm, (x - 0.01, x + 0.01), (ROPE_Y - 0.04, ROPE_Y + 0.04), (PIT_Z, 6.6), stl)
        bx(B.bm, (x - 0.03, x + 0.03), (ROPE_Y + 0.04, ROPE_Y + 0.055), (PIT_Z, 6.6), stl)
        for zz in (-1.0, 0.8, 2.6, 4.4, 6.2):
            bx(B.bm, (x - 0.02, x + 0.02), (ROPE_Y + 0.055, SHAFT_BACK), (zz - 0.03, zz + 0.03), stl)
    # The counterweight's buffers in its pit.
    for dx in (-0.16, 0.16):
        cx = CW_X + dx
        add_cyl(B.bm, (cx, ROPE_Y, PIT_Z), (cx, ROPE_Y, PIT_Z + 0.04), 0.08, seg=12, mat=yel)
        pts = d17.helix(Vector((cx, ROPE_Y, PIT_Z + 0.2)), 0.05, 0.16, 4, n=25)
        for a, b in zip(pts, pts[1:]):
            add_cyl(B.bm, a, b, 0.009, seg=4, mat=stl)
        add_cyl(B.bm, (cx, ROPE_Y, PIT_Z + 0.2), (cx, ROPE_Y, PIT_Z + 0.24), 0.065, seg=12, mat=B('rubber'))
    # The far glow: the shaft's top, far above, where the cold light comes from.
    B.done('UOLiftFront', coll)
    bm = bmesh.new()
    add_box(bm, ((CW_SHAFT[0] + RIGHT_WALL[1]) / 2, 0.75, 12.9), (1.0, 2.2, 0.02))
    d17.mesh_object('UOShaftSky', bm, [U['sky']], coll)

    # The gate: two lattice leaves, modelled open (each behind the wall beside the doorway).
    for name, xc, grip_side in (('LiftDoorL', g0 - LEAF_W / 2 + 0.005, 1), ('LiftDoorR', g1 + LEAF_W / 2 - 0.005, -1)):
        B = Batch(U)
        lattice_leaf(B, LEAF_W, gh - 0.02, B('steel'), B('steel'), None)
        gx = grip_side * (LEAF_W / 2 - 0.03)                                   # the leading edge's grip, worn bright
        bx(B.bm, (gx - 0.012, gx + 0.012), (-0.03, -0.012), (0.85, 1.25), B('bright'), 0.004)
        for zz in (0.85, 1.25):
            bx(B.bm, (gx - 0.01, gx + 0.01), (-0.03, -0.012), (zz - 0.01, zz + 0.01), B('bright'))
        for sy in (-1, 1):                                                     # hangers on the track
            add_cyl(B.bm, (sy * 0.18, -0.02, gh + 0.05), (sy * 0.18, 0.02, gh + 0.05), 0.025, seg=10, mat=B('steel'))
            bx(B.bm, (sy * 0.18 - 0.01, sy * 0.18 + 0.01), (-0.006, 0.006), (gh - 0.04, gh + 0.05), B('steel'))
        B.done(name, coll, origin=(xc, GATE_Y, DECK))


def build_panel(U, coll):
    """The call panel left of the gate: a green enamel plate on a cast box, the wordless instruction, one big worn
    brass UP (LiftUpButton, pushed in along +y), its amber lamp (LiftUpLamp)."""
    bz = DECK + BUTTON_DZ
    B = Batch(U)
    box_y = (0.322, WALL_Y)
    bx(B.bm, (PANEL_X - 0.09, PANEL_X + 0.09), box_y, (bz - 0.16, bz + 0.2), B('iron'), 0.012)
    bx(B.bm, (PANEL_X - 0.075, PANEL_X + 0.075), (0.318, 0.323), (bz - 0.145, bz + 0.185), B('depot_green'), 0.003)
    add_cyl(B.bm, (PANEL_X, 0.32, bz), (PANEL_X, 0.31, bz), 0.05, seg=20, mat=B('brass'))          # the bezel
    add_cyl(B.bm, (PANEL_X, 0.32, bz + 0.13), (PANEL_X, 0.305, bz + 0.13), 0.026, seg=14, mat=B('brass'))
    for dx, dz in ((-0.06, -0.13), (0.06, -0.13), (-0.06, 0.17), (0.06, 0.17)):
        add_sphere(B.bm, (PANEL_X + dx, 0.316, bz + dz), 0.007, seg=6, mat=B('brass'))
    sign(B, (PANEL_X, WALL_Y - 0.004, bz + 0.42), 0.26, 0.26, R_PANEL, B('atlas'))
    bx(B.bm, (PANEL_X - 0.14, PANEL_X + 0.14), (WALL_Y - 0.003, WALL_Y), (bz + 0.28, bz + 0.56), B('brass'))
    add_cyl(B.bm, (PANEL_X - 0.09, 0.32, bz + 0.1), (PANEL_X - 0.15, 0.32, bz + 0.1), 0.012, seg=6, mat=B('steel'))   # conduit
    add_cyl(B.bm, (PANEL_X - 0.15, 0.32, bz + 0.1), (PANEL_X - 0.15, 0.32, 4.6), 0.012, seg=6, mat=B('steel'))
    B.done('LiftPanel', coll)
    # LiftUpButton: the push, a broad brass mushroom worn bright on its face; an arrow cast in it. Origin at its face.
    B = Batch(U)
    add_cyl(B.bm, (0, 0.02, 0), (0, 0.004, 0), 0.036, seg=20, mat=B('brass'))
    add_cyl(B.bm, (0, 0.004, 0), (0, 0.0, 0), 0.034, 0.03, seg=20, mat=B('polished'))
    tri = [B.bm.verts.new((dx, -0.0004, dz)) for dx, dz in ((-0.016, -0.008), (0.016, -0.008), (0.0, 0.016))]
    B.bm.faces.new(tri).material_index = B('brass')
    B.done('LiftUpButton', coll, origin=None)
    ob = bpy.data.objects['LiftUpButton']
    ob.location = (PANEL_X, BUTTON_AHEAD, bz)
    bm = bmesh.new()
    add_sphere(bm, (0, 0, 0), 0.02, seg=12, scale=(1, 0.6, 1))
    ob = d17.mesh_object('LiftUpLamp', bm, [U['uplamp']], coll)
    ob.location = (PANEL_X, 0.305, bz + 0.13)


def build_car(U, coll):
    """LiftCar: origin at its floor's centre. Panelled walls (green below, cream above), a brass handrail, the lamp,
    the load gauge and the notice on its back wall, the sling and crosshead with the ropes' hitch, guide shoes;
    the weighing linkage under its floor. Children: LiftFloorPlate (the weighing plate), LiftLoadNeedle."""
    B = Batch(U)
    hw = (CAR[1] - CAR[0]) / 2
    yf, yb = CAR_Y[0] - CAR_C[1], CAR_Y[1] - CAR_C[1]          # front and back, car-local
    px0, px1 = PLATE[0] - CAR_C[0], PLATE[1] - CAR_C[0]
    py0, py1 = PLATE[2] - CAR_C[1], PLATE[3] - CAR_C[1]
    stl, grn, crm, brs, iron = B('steel'), B('depot_green'), B('cream'), B('brass'), B('iron')
    # The platform, round the plate's well (the well's floor a little below, so the dip reads at its edge).
    bx(B.bm, (-hw, hw), (yf, yb), (-0.16, -0.06), stl, 0.01)
    for xr, yr in (((-hw, hw), (yf, py0 - 0.006)), ((-hw, hw), (py1 + 0.006, yb)), ((-hw, px0 - 0.006), (py0 - 0.006, py1 + 0.006)),
                   ((px1 + 0.006, hw), (py0 - 0.006, py1 + 0.006))):
        bx(B.bm, xr, yr, (-0.06, 0.0), stl, 0.004)
    bx(B.bm, (px0 - 0.006, px1 + 0.006), (py0 - 0.006, py1 + 0.006), (-0.07, -0.06), B('dark'))
    for xr, yr in (((px0 - 0.012, px1 + 0.012), (py0 - 0.012, py0 - 0.006)), ((px0 - 0.012, px1 + 0.012), (py1 + 0.006, py1 + 0.012)),
                   ((px0 - 0.012, px0 - 0.006), (py0 - 0.006, py1 + 0.006)), ((px1 + 0.006, px1 + 0.012), (py0 - 0.006, py1 + 0.006))):
        bx(B.bm, xr, yr, (-0.003, 0.001), B('yellow'))                         # the plate's edge, painted
    bx(B.bm, (-0.6, 0.6), (yf, yf + 0.04), (-0.01, 0.004), brs)                # the car's sill
    # The walls: back and sides, inside faces panelled.
    for xr in ((hw - 0.06, hw), (-hw, -hw + 0.06)):
        bx(B.bm, xr, (yf, yb), (0.0, CAR_H), stl, 0.008)
    bx(B.bm, (-hw, hw), (yb - 0.06, yb), (0.0, CAR_H), stl, 0.008)
    inner = hw - 0.062
    for k, (xa, xb) in enumerate(((-inner, -0.24), (-0.22, 0.22), (0.24, inner))):          # back wall panels
        bx(B.bm, (xa + 0.02, xb - 0.02), (yb - 0.075, yb - 0.06), (0.16, 0.95), grn, 0.006)
        bx(B.bm, (xa + 0.02, xb - 0.02), (yb - 0.072, yb - 0.06), (1.02, CAR_H - 0.1), crm, 0.006)
    for s in (-1, 1):                                                          # side wall panels
        x = s * inner
        for ya, yb2 in ((yf + 0.08, -0.02), (0.02, yb - 0.1)):
            bx(B.bm, (x - 0.012, x + 0.012), (ya, yb2), (0.16, 0.95), grn, 0.006)
            bx(B.bm, (x - 0.01, x + 0.01), (ya, yb2), (1.02, CAR_H - 0.1), crm, 0.006)
    bx(B.bm, (-inner, inner), (yb - 0.08, yb - 0.06), (0.0, 0.14), stl, 0.004)           # kick plates
    for s in (-1, 1):
        bx(B.bm, (s * inner - 0.02, s * inner + 0.02), (yf + 0.05, yb - 0.06), (0.0, 0.14), stl, 0.004)
    # The front returns either side of the opening, and the car's headpiece.
    for s in (-1, 1):
        bx(B.bm, (s * 0.6, s * hw) if s > 0 else (-hw, -0.6), (yf, yf + 0.06), (0.0, CAR_H), stl, 0.008)
    bx(B.bm, (-hw, hw), (yf, yf + 0.06), (CAR_H - 0.12, CAR_H), stl, 0.008)
    # The handrail (brass) round the back and sides.
    rz = 0.9
    add_cyl(B.bm, (-inner + 0.05, yb - 0.11, rz), (inner - 0.05, yb - 0.11, rz), 0.016, seg=10, mat=brs)
    for s in (-1, 1):
        add_cyl(B.bm, (s * (inner - 0.05), yb - 0.11, rz), (s * (inner - 0.05), yf + 0.12, rz), 0.016, seg=10, mat=brs)
        for y in (yb - 0.11, yf + 0.12):
            add_cyl(B.bm, (s * (inner - 0.05), y, rz), (s * (inner - 0.005), y, rz), 0.01, seg=6, mat=brs)
    add_cyl(B.bm, (-0.2, yb - 0.11, rz), (-0.2, yb - 0.065, rz), 0.01, seg=6, mat=brs)
    add_cyl(B.bm, (0.2, yb - 0.11, rz), (0.2, yb - 0.065, rz), 0.01, seg=6, mat=brs)
    # The ceiling, and its lamp (CarLamp) under a wire guard.
    bx(B.bm, (-hw, hw), (yf, yb), (CAR_H, CAR_H + 0.06), stl, 0.008)
    bx(B.bm, (-inner, inner), (yf + 0.06, yb - 0.06), (CAR_H - 0.03, CAR_H), crm)
    lamp = Vector((0.0, 0.05, CAR_H - 0.03))
    add_cyl(B.bm, lamp, lamp - Vector((0, 0, 0.02)), 0.09, seg=16, mat=stl)
    add_sphere(B.bm, lamp - Vector((0, 0, 0.03)), 0.065, seg=14, scale=(1, 1, 0.45), mat=B('carlamp'))
    for k in range(4):
        a = k * math.pi / 2
        add_cyl(B.bm, lamp + Vector((0.08 * math.cos(a), 0.08 * math.sin(a), -0.01)), lamp + Vector((0.04 * math.cos(a), 0.04 * math.sin(a), -0.075)),
                0.003, seg=4, mat=stl)
    # The load gauge (its needle is LiftLoadNeedle) and the notice, on the back wall.
    gc = Vector((0.36, yb - 0.075, 1.3))
    add_cyl(B.bm, gc + Vector((0, 0.01, 0)), gc - Vector((0, 0.01, 0)), 0.165, seg=28, mat=brs)
    quad(B, [gc + Vector((-0.145, -0.0105, -0.145)), gc + Vector((0.145, -0.0105, -0.145)), gc + Vector((0.145, -0.0105, 0.145)),
             gc + Vector((-0.145, -0.0105, 0.145))], (392, 776, 632, 1016), B('atlas'))
    sign(B, (-0.38, yb - 0.074, 1.5), 0.3, 0.15, R_CAR, B('atlas'))
    # The sling: stiles up the sides outside the walls, the crosshead over the roof, the hitch; guide shoes.
    for s in (-1, 1):
        x = s * (hw + 0.02)
        bx(B.bm, (x - 0.02, x + 0.02), (-0.06, 0.06), (-0.22, CAR_H + 0.12), stl, 0.008)
        for z in (-0.18, CAR_H + 0.04):
            bx(B.bm, (0.79, 0.85) if s > 0 else (-0.85, -0.79), (-0.05, 0.05), (z - 0.05, z + 0.05), iron, 0.006)
    hy = ROPE_Y - CAR_C[1]
    bx(B.bm, (-hw - 0.04, hw + 0.04), (hy - 0.065, hy + 0.065), (CAR_H + 0.06, CAR_H + 0.18), stl, 0.012)
    bx(B.bm, (-hw - 0.04, hw + 0.04), (-0.05, 0.05), (-0.26, -0.16), stl, 0.01)
    for dy in (-0.025, 0.0, 0.025):                                            # the ropes' hitch: rods, springs, nuts
        add_cyl(B.bm, (0, hy + dy, CAR_H + 0.18), (0, hy + dy, CAR_HITCH + 0.01), 0.008, seg=6, mat=B('bright'))
        add_cyl(B.bm, (0, hy + dy, CAR_HITCH - 0.03), (0, hy + dy, CAR_HITCH + 0.01), 0.016, seg=8, mat=iron)
    # Under the floor: the weighing linkage (a lever from the plate's bearers to a spring box), seen as the car rises.
    for x in (px0 + 0.2, px1 - 0.2):
        bx(B.bm, (x - 0.03, x + 0.03), (py0 + 0.1, py1 - 0.1), (-0.22, -0.16), iron, 0.006)
    add_cyl(B.bm, (px0 + 0.2, 0.0, -0.24), (px1 - 0.05, 0.0, -0.3), 0.018, seg=8, mat=iron)
    add_cyl(B.bm, (px1 - 0.05, 0.0, -0.36), (px1 - 0.05, 0.0, -0.18), 0.05, seg=12, mat=iron)
    B.done('LiftCar', coll, origin=(CAR_C[0], CAR_C[1], DECK))
    car = bpy.data.objects['LiftCar']

    # LiftFloorPlate: the weighing plate, chequered, flush with the floor; origin at its top centre. It dips 0.01.
    B = Batch(U)
    pw, pd = px1 - px0, py1 - py0
    bx(B.bm, (-pw / 2, pw / 2), (-pd / 2, pd / 2), (-0.03, 0.0), B('plate'), 0.005)
    for i in range(int(pw / 0.08)):
        for j in range(int(pd / 0.08)):
            x = -pw / 2 + 0.04 + i * 0.08
            y = -pd / 2 + 0.04 + j * 0.08
            a = 0.6 if (i + j) % 2 else -0.6
            add_box(B.bm, (x, y, 0.0015), (0.035, 0.008, 0.003), mat=B('plate'), rot=_rz(a))
    for x, y in ((-pw / 2 + 0.05, -pd / 2 + 0.05), (pw / 2 - 0.05, -pd / 2 + 0.05), (-pw / 2 + 0.05, pd / 2 - 0.05), (pw / 2 - 0.05, pd / 2 - 0.05)):
        add_cyl(B.bm, (x, y, 0.0), (x, y, 0.003), 0.012, seg=8, mat=B('bright'))
    ob = B.done('LiftFloorPlate', coll)
    ob.parent = car
    ob.location = ((px0 + px1) / 2, (py0 + py1) / 2, 0.0)              # car-local; world: PLATE's centre at the floor

    # LiftLoadNeedle: pivot at the gauge's centre, modelled pointing at 0 (down and left); the game turns it about +y.
    bm = bmesh.new()
    a = math.radians(225)
    tip = Vector((0.12 * math.cos(a), 0, 0.12 * math.sin(a)))
    add_cyl(bm, (0, 0, 0), tip, 0.006, 0.002, seg=4)
    add_cyl(bm, (0, 0.002, 0), (0, -0.008, 0), 0.016, seg=10)
    ob = d17.mesh_object('LiftLoadNeedle', bm, [U['iron']], coll)
    ob.parent = car
    ob.location = (gc.x, gc.y - 0.014, gc.z)                                  # car-local

    # The ropes, each from its sheave's tangent down to its hitch; origins at the top (the game scales them in z).
    for name, x, z1 in (('LiftRopeCar', CAR_C[0], DECK + CAR_HITCH), ('LiftRopeCW', CW_X, CW_TOP + CW_HITCH)):
        bm = bmesh.new()
        for dy in (-0.025, 0.0, 0.025):
            add_cyl(bm, (0, dy, 0), (0, dy, z1 - SHEAVE_Z), 0.011, seg=6)
        ob = d17.mesh_object(name, bm, [U['cable']], coll)
        ob.location = (x, ROPE_Y, SHEAVE_Z)

    # The sheaves: spoked iron wheels with three grooves, axles along y.
    for name, sx in (('LiftSheave', SHEAVE_A), ('LiftSheaveIdler', SHEAVE_B)):
        B = Batch(U)
        iron = B('iron')
        add_cyl(B.bm, (0, -0.05, 0), (0, 0.05, 0), SHEAVE_R - 0.012, seg=32, mat=iron)
        for dy in (-0.05, -0.0125, 0.0125, 0.05):
            add_cyl(B.bm, (0, dy - 0.006, 0), (0, dy + 0.006, 0), SHEAVE_R + 0.02, seg=32, mat=iron)
        add_cyl(B.bm, (0, -0.07, 0), (0, 0.07, 0), 0.07, seg=14, mat=iron)
        for k in range(6):
            a = k * math.pi / 3
            add_box(B.bm, (math.cos(a) * SHEAVE_R * 0.5, -0.055, math.sin(a) * SHEAVE_R * 0.5), (SHEAVE_R * 0.75, 0.03, 0.05),
                    mat=iron, rot=_ry(-a))
        bx(B.bm, (SHEAVE_R * 0.55, SHEAVE_R * 0.75), (-0.075, -0.065), (-0.025, 0.025), B('yellow'))     # a paint mark, so it reads turning
        B.done(name, coll, origin=(sx, ROPE_Y, SHEAVE_Z))


# --------------------------------------------------------------------------
# The crank, the service door, the counterweight and the service UP
# --------------------------------------------------------------------------

def build_service(U, coll):
    wx, wy, wz = CRANK
    B = Batch(U)
    iron, stl, grn = B('iron'), B('steel'), B('depot_green')
    # The winch box behind the wheel, on the pier; the chain up from its drum to the sprockets over the door.
    bx(B.bm, (wx - 0.12, wx + 0.12), (0.27, WALL_Y), (wz - 0.15, wz + 0.15), grn, 0.015)
    add_cyl(B.bm, (wx, 0.27, wz), (wx, 0.24, wz), 0.05, seg=14, mat=iron)
    add_cyl(B.bm, (wx + 0.1, 0.29, wz + 0.04), (wx + 0.1, 0.25, wz + 0.04), 0.045, seg=14, mat=iron)        # the drum
    chx = wx + 0.145
    for z in (wz + 0.2, 3.0, 3.9):                                             # chain guides
        bx(B.bm, (chx - 0.03, chx + 0.03), (0.27, WALL_Y), (z - 0.02, z + 0.02), stl, 0.004)
    sp1 = Vector((chx - 0.0, 0.29, 4.45))
    sp2 = Vector((SDOOR[0], 0.29, 4.45))
    for c in (sp1, sp2):
        add_cyl(B.bm, c + Vector((0, -0.015, 0)), c + Vector((0, 0.015, 0)), 0.06, seg=14, mat=iron)
        add_cyl(B.bm, c + Vector((0, 0.015, 0)), c + Vector((0, WALL_Y - c.y + 0.02, 0)), 0.015, seg=8, mat=stl)
    chain(B.bm, sp1 + Vector((0, 0, 0.06)), sp2 + Vector((0, 0, 0.06)), mat=stl)
    # The service plate, wordless, over the crank.
    sign(B, (wx, WALL_Y - 0.004, wz + 0.62), 0.24, 0.24, R_SERVICE, B('atlas'))
    # The door's casing over the lane, and its guide in the pier.
    bx(B.bm, (SDOOR[0] - 0.08, SDOOR[0] + 0.08), (SDOOR[1][0] - 0.06, WALL_Y + 0.08), (CASING_Z, 5.0), B('shutter'), 0.012)
    for z in (CASING_Z + 0.08, 4.9):
        bx(B.bm, (SDOOR[0] - 0.09, SDOOR[0] + 0.09), (SDOOR[1][0] - 0.07, WALL_Y + 0.08), (z - 0.03, z + 0.03), stl, 0.006)
    for k in range(6):
        add_sphere(B.bm, (SDOOR[0] - 0.081, SDOOR[1][0] + 0.12 + k * 0.15, CASING_Z + 0.08), 0.01, seg=6, mat=stl)
    bx(B.bm, (SDOOR[0] - 0.05, SDOOR[0] + 0.05), (WALL_Y - 0.01, WALL_Y + 0.06), (DECK, CASING_Z), stl, 0.006)
    bx(B.bm, (SDOOR[0] - 0.06, SDOOR[0] + 0.06), (SDOOR[1][0] - 0.03, SDOOR[1][0] + 0.03), (CASING_Z - 0.1, CASING_Z), stl, 0.006)
    B.done('UOServiceWinch', coll)

    # ServiceCrank: the wheel (rim worn bright, spokes in old green), origin at its centre; turns about +y.
    B = Batch(U)
    add_torus(B.bm, (0, 0, 0), (0, 1, 0), CRANK_R, 0.013, mat=B('bright'), seg=32, rseg=8)
    for k in range(4):
        a = math.pi * k / 2 + math.pi / 4
        add_cyl(B.bm, (0, 0, 0), (CRANK_R * math.cos(a), 0, CRANK_R * math.sin(a)), 0.008, seg=6, mat=B('depot_green'))
    add_cyl(B.bm, (0, -0.015, 0), (0, 0.04, 0), 0.032, seg=14, mat=B('depot_green'))
    add_cyl(B.bm, (0, -0.022, 0), (0, -0.015, 0), 0.02, seg=10, mat=B('bright'))
    knob = Vector((CRANK_R * math.cos(math.radians(30)), 0, CRANK_R * math.sin(math.radians(30))))
    add_cyl(B.bm, knob, knob + Vector((0, -0.07, 0)), 0.014, seg=10, mat=B('bright'))
    B.done('ServiceCrank', coll, origin=CRANK)

    # ServiceChain: the run from the drum up to the first sprocket; the game slides it along z (pitch 0.06) as he winds.
    bm = bmesh.new()
    chain(bm, (chx, 0.29, wz + 0.04), (chx, 0.29, 4.45), mat=0)
    ob = d17.mesh_object('ServiceChain', bm, [U['steel']], coll)

    # ServiceDoor: a steel leaf across the lane, painted in danger stripes (it guards a machine that crushes), ribbed,
    # a rubber foot, the service plate on both faces; origin at its foot's centre. It winds straight up SDOOR_RISE.
    B = Batch(U)
    ya, yb = SDOOR[1]
    h = SDOOR[2]
    yc = (ya + yb) / 2
    t = 0.04
    yel, blk = B('yellow'), B('rubber')
    bx(B.bm, (-t, t), (ya - yc, yb - yc), (0.0, h), yel, 0.008)
    for s_ in (-1, 1):
        stripes(B.bm, s_ * (t + 0.0015), s_, ya - yc + 0.01, yb - yc - 0.01, 0.03, h - 0.03, width=0.11, slope=0.8, mat=blk)
    for k in range(int(h / 0.22)):                                              # its front edge, banded, facing the camera
        z = 0.03 + k * 0.22
        bx(B.bm, (-t + 0.004, t - 0.004), (ya - yc - 0.003, ya - yc), (z, z + 0.11), blk)
    for z in (0.5, 1.0, 1.5):
        for s_ in (-1, 1):
            bx(B.bm, (s_ * t - 0.01, s_ * t + 0.01), (ya - yc + 0.03, yb - yc - 0.03), (z - 0.02, z + 0.02), B('steel'), 0.004)
    bx(B.bm, (-t - 0.003, t + 0.003), (ya - yc, yb - yc), (0.0, 0.025), blk)
    for s_ in (-1, 1):
        sign(B, (s_ * (t + 0.006), -0.05, 1.22), 0.22, 0.22, R_SERVICE, B('atlas'), face=(s_, 0, 0))
    add_torus(B.bm, (0, ya - yc + 0.1, h + 0.04), (1, 0, 0), 0.03, 0.008, mat=B('steel'), seg=12, rseg=4)     # its lifting eye
    chain(B.bm, (0, ya - yc + 0.1, h + 0.07), (0, ya - yc + 0.1, h + 0.25), mat=B('steel'))
    B.done('ServiceDoor', coll, origin=(SDOOR[0], yc, DECK))
    # The casing's front, toward the camera, banded too; a caged work lamp over the crank (CrankLamp).
    B = Batch(U)
    bx(B.bm, (SDOOR[0] - 0.08, SDOOR[0] + 0.08), (SDOOR[1][0] - 0.065, SDOOR[1][0] - 0.06), (CASING_Z, 5.0), B('yellow'))
    for k in range(7):
        z = CASING_Z + 0.04 + k * 0.22
        bx(B.bm, (SDOOR[0] - 0.08, SDOOR[0] + 0.08), (SDOOR[1][0] - 0.068, SDOOR[1][0] - 0.065), (z, z + 0.11), B('rubber'))
    lp = Vector(CRANK_LAMP)
    bx(B.bm, (lp.x - 0.05, lp.x + 0.05), (lp.y + 0.05, WALL_Y), (lp.z + 0.02, lp.z + 0.1), B('steel'), 0.006)
    add_cyl(B.bm, lp + Vector((0, 0.05, 0.06)), lp + Vector((0, -0.02, 0.06)), 0.045, seg=12, mat=B('steel'))
    for k in range(6):
        a = k * math.pi / 3
        add_cyl(B.bm, lp + Vector((0.05 * math.cos(a), -0.02, 0.06 + 0.05 * math.sin(a))), lp + Vector((0.02 * math.cos(a), -0.09, 0.06 + 0.02 * math.sin(a))),
                0.003, seg=4, mat=B('steel'))
    add_cyl(B.bm, lp + Vector((0, 0.05, 0.1)), (lp.x, WALL_Y - 0.01, 4.6), 0.008, seg=5, mat=B('cable'))
    B.done('UOServiceFront', coll)
    bm = bmesh.new()
    add_sphere(bm, lp + Vector((0, -0.04, 0.06)), 0.032, seg=12, scale=(1, 1.2, 1))
    d17.mesh_object('CrankLamp', bm, [U['cranklamp']], coll)

    # The counterweight: footplate on a frame cantilevered from a cast-iron block; its side rails; origin at the
    # footplate's top centre on the lane. It falls CW_TRAVEL to ring C's level as the car rises.
    B = Batch(U)
    iron, stl, plate, yel, bright = B('iron'), B('steel'), B('plate'), B('yellow'), B('bright')
    fx0, fx1, fy0, fy1 = FOOT
    by0, by1 = ROPE_Y - 0.16, ROPE_Y + 0.16                       # the block, world y
    bx(B.bm, (fx0, fx1), (fy0, fy1), (-0.035, 0.0), plate, 0.006)
    for i in range(int((fx1 - fx0) / 0.08)):
        for j in range(int((fy1 - fy0) / 0.08)):
            add_box(B.bm, (fx0 + 0.04 + i * 0.08, fy0 + 0.04 + j * 0.08, 0.0015), (0.035, 0.008, 0.003), mat=plate,
                    rot=_rz(0.6 if (i + j) % 2 else -0.6))
    bx(B.bm, (fx0, fx1), (fy0 - 0.012, fy0 + 0.02), (-0.05, 0.004), yel, 0.004)
    for k in range(8):
        x = fx0 + 0.04 + k * 0.1
        bx(B.bm, (x, x + 0.045), (fy0 - 0.014, fy0 - 0.011), (-0.048, 0.002), B('rubber'))
    for sx in (-1, 1):                                                          # the frame under it, back to the block
        x = sx * 0.3
        bx(B.bm, (x - 0.035, x + 0.035), (fy0, by1), (-0.16, -0.035), stl, 0.006)
        a, b = Vector((x, fy0 + 0.12, -0.16)), Vector((x, by0, -0.95))
        d = b - a
        add_box(B.bm, (a + b) / 2, (0.05, 0.03, d.length), mat=stl, rot=Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4())
    bx(B.bm, (fx0, fx1), (fy0 + 0.02, fy0 + 0.08), (-0.14, -0.035), stl, 0.006)
    # The side rails he grips riding (as the cage's): worn bright, on short posts, either side of the lane.
    for y in (-CW_RAIL_Y, CW_RAIL_Y):
        add_cyl(B.bm, (CW_RAIL_X[0], y, CW_RAIL_Z), (CW_RAIL_X[1], y, CW_RAIL_Z), 0.016, seg=10, mat=bright)
        for x in (CW_RAIL_X[0] + 0.02, 0.0, CW_RAIL_X[1] - 0.02):
            add_cyl(B.bm, (x, y, 0.0), (x, y, CW_RAIL_Z), 0.012, seg=6, mat=stl)
    # The block's frame: channel uprights, crossheads, guide shoes; cast slabs stacked in it; the hitch.
    top, bot = CW_HITCH - 0.05, -1.5
    for sx in (-1, 1):
        x = sx * 0.3
        bx(B.bm, (x - 0.04, x + 0.04), (by0, by1), (bot, top), stl, 0.008)
        for z in (bot + 0.1, top - 0.1):
            bx(B.bm, (sx * 0.34, sx * 0.4) if sx > 0 else (-0.4, -0.34), (ROPE_Y - 0.05, ROPE_Y + 0.05), (z - 0.05, z + 0.05), iron, 0.006)
    for z in ((top - 0.08, top), (bot, bot + 0.08)):
        bx(B.bm, (-0.34, 0.34), (by0, by1), z, stl, 0.008)
    n = 9
    for k in range(n):
        z0 = bot + 0.1 + k * 0.155
        cbox(B.bm, (0, ROPE_Y, z0 + 0.07), (0.52, 0.3, 0.14), 0.012, iron)
    for k in range(3):
        add_cyl(B.bm, (-0.18 + k * 0.18, by0 - 0.004, bot + 0.6), (-0.18 + k * 0.18, by0 - 0.012, bot + 0.6), 0.018, seg=8, mat=bright)
    for dy in (-0.025, 0.0, 0.025):
        add_cyl(B.bm, (0, ROPE_Y + dy, top), (0, ROPE_Y + dy, CW_HITCH + 0.01), 0.008, seg=6, mat=bright)
        add_cyl(B.bm, (0, ROPE_Y + dy, CW_HITCH - 0.035), (0, ROPE_Y + dy, CW_HITCH + 0.01), 0.016, seg=8, mat=iron)
    # A yellow band round its foot (the world's own warning: a machine that crushes).
    for k in range(6):
        x = -0.26 + k * 0.1
        bx(B.bm, (x, x + 0.05), (by0 - 0.004, by0), (bot + 0.0, bot + 0.08), yel)
    B.done('LiftCounterweight', coll, origin=None).location = (CW_X, 0.0, CW_TOP)
    # The service UP on the shaft's far wall: a cast box angled toward him and the camera, its push and lamp.
    M = service_frame()
    B = Batch(U)
    bm = bmesh.new()
    cbox(bm, (-0.03, 0, 0.04), (0.06, 0.16, 0.3), 0.01, B('iron'))
    bx(bm, (-0.0615, -0.059), (-0.065, 0.065), (-0.09, 0.17), B('depot_green'))
    add_cyl(bm, (-0.06, 0, 0), (-0.07, 0, 0), 0.05, seg=20, mat=B('brass'))
    add_cyl(bm, (-0.06, 0, 0.13), (-0.075, 0, 0.13), 0.026, seg=14, mat=B('brass'))
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    me = bpy.data.meshes.new('_t')
    bm.to_mesh(me)
    bm.free()
    B.bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    sign(B, M @ Vector((-0.004, 0.0, 0.42)), 0.2, 0.2, R_SERVICE, B('atlas'), face=tuple((M.to_3x3() @ Vector((-1, 0, 0)))))
    top = M @ Vector((-0.02, 0.0, 0.19))
    add_cyl(B.bm, top, (top.x, top.y, 4.6), 0.012, seg=6, mat=B('steel'))
    B.done('ServicePanel', coll)
    B = Batch(U)
    add_cyl(B.bm, (0, 0, 0), (-0.016, 0, 0), 0.036, seg=20, mat=B('brass'))
    add_cyl(B.bm, (-0.016, 0, 0), (-0.02, 0, 0), 0.034, 0.03, seg=20, mat=B('polished'))
    B.done('ServiceUpButton', coll)
    ob = bpy.data.objects['ServiceUpButton']
    ob.location = M @ Vector((-0.07, 0, 0))
    ob.rotation_euler = (0, 0, SERVICE_ANG)
    bm = bmesh.new()
    add_sphere(bm, (0, 0, 0), 0.02, seg=12, scale=(0.6, 1, 1))
    ob = d17.mesh_object('ServiceUpLamp', bm, [U['svclamp']], coll)
    ob.location = M @ Vector((-0.075, 0, 0.13))
    ob.rotation_euler = (0, 0, SERVICE_ANG)


# --------------------------------------------------------------------------
# The carry item: Suitcase114
# --------------------------------------------------------------------------

def build_suitcase114(U, coll):
    """Suitcase114: a small brown case standing on its long edge, broadside to the camera, origin at its base
    centre; a handle on top (grip 0.225, along x), the C-114 tag on a string from the handle (Suitcase114Tag,
    its origin at the knot, so the game can swing it)."""
    L, T, H = SUITCASE_SIZE
    B = Batch(U)
    suitcase(B.bm, (0, 0, 0), (L, T, H), I4, B('leather'), B('brass'), B('leather'), straps=True, mat_strap=B('canvas'))
    for sx in (-1, 1):                                                          # scuffed brass feet
        add_cyl(B.bm, (sx * 0.1, 0, 0.0), (sx * 0.1, 0, 0.006), 0.012, seg=8, mat=B('brass'))
    sign(B, (-0.075, -T / 2 - 0.006, H * 0.33), 0.085, 0.085, R_LABEL, B('atlas'), face=(0, -1, 0))   # its label, on the face
    ob = B.done('Suitcase114', coll)
    ob.location = (SUITCASE[0], SUITCASE[1], DECK)
    B = Batch(U)
    knot = Vector((0.03, -0.004, H + 0.026))                                   # tied round the handle's grip
    add_cyl(B.bm, (0, 0, 0), (0.0, -0.066, -0.04), 0.0016, seg=4, mat=B('cable'))
    sign(B, (0.0, -0.068, -0.095), 0.05, 0.1, R_TAG, B('atlas'), face=(0.1, -1, 0))
    tag = B.done('Suitcase114Tag', coll)
    tag.location = knot
    tag.parent = ob


# --------------------------------------------------------------------------
# The collapsed stair
# --------------------------------------------------------------------------

def stair_flight(bm, n, width, steel, tread, nosing, rise=0.2, going=0.24):
    """A steel flight in its own frame: its top nosing at the origin, going down along +x; n treads, stringers either
    side (width across y)."""
    for k in range(n):
        x = k * going
        z = -k * rise
        cbox(bm, (x + going / 2, 0, z - 0.02), (going + 0.02, width - 0.08, 0.04), 0.008, tread)
        bx(bm, (x + going - 0.02, x + going + 0.01), (-width / 2 + 0.05, width / 2 - 0.05), (z - 0.045, z), nosing)
    L = n * going
    for s in (-1, 1):
        y = s * (width / 2 - 0.02)
        a0, b0 = Vector((0, y, 0.06)), Vector((L, y, -n * rise + 0.06))
        d0 = b0 - a0
        add_box(bm, (a0 + b0) / 2 + Vector((0, 0, -0.1)), (d0.length, 0.02, 0.22), mat=steel,
                rot=_ry(math.atan2(-d0.z, d0.x)))


def _merge_into(B, bm, M):
    bmesh.ops.transform(bm, matrix=M, verts=bm.verts)
    me = bpy.data.meshes.new('_t')
    bm.to_mesh(me)
    bm.free()
    B.bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def build_stair(U, coll):
    """The stair down to ring C beside the lift, collapsed: its head at the deck's level behind the lane (taped off,
    the hazard board), its top flight torn off and hanging, the rest fallen on a heap of rubble against the
    back wall. Nothing of it is on the lane."""
    B = Batch(U)
    con, stl, yel = B('concrete'), B('steel'), B('yellow')
    h1 = STAIR_HEAD[1]
    y0, y1 = STAIR_Y
    w = y1 - y0
    yc = (y0 + y1) / 2
    # The head landing on brackets from the back wall, its front rail bent, tape across, the signs.
    bx(B.bm, (RIGHT_WALL[1], h1), (y0, SHAFT_BACK), (DECK - 0.22, DECK), con, 0.02)
    bx(B.bm, (h1 - 0.03, h1 + 0.01), (y0, y1), (DECK - 0.24, DECK + 0.004), stl, 0.006)
    for x in (RIGHT_WALL[1] + 0.15, h1 - 0.15):
        a, b = Vector((x, SHAFT_BACK, DECK - 0.9)), Vector((x, y0 + 0.2, DECK - 0.22))
        d = b - a
        add_box(B.bm, (a + b) / 2, (0.06, 0.04, d.length), mat=stl, rot=Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4())
        bx(B.bm, (x - 0.04, x + 0.04), (y0 + 0.1, SHAFT_BACK), (DECK - 0.3, DECK - 0.22), stl, 0.006)
    for x in (RIGHT_WALL[1] + 0.05, h1 - 0.05):
        add_cyl(B.bm, (x, y0 + 0.03, DECK), (x, y0 + 0.03, DECK + 0.95), 0.02, seg=8, mat=yel)
    add_cyl(B.bm, (RIGHT_WALL[1] + 0.05, y0 + 0.03, DECK + 0.95), (h1 - 0.05, y0 + 0.03, DECK + 0.95), 0.02, seg=8, mat=yel)
    add_cyl(B.bm, (h1 - 0.05, y0 + 0.03, DECK + 0.95), (h1 + 0.35, y0 - 0.05, DECK + 0.55), 0.02, seg=8, mat=yel)  # bent out over the drop
    add_cyl(B.bm, (h1 + 0.35, y0 - 0.05, DECK + 0.55), (h1 + 0.5, y0 - 0.02, DECK + 0.1), 0.02, seg=8, mat=yel)
    for z in (DECK + 0.55, DECK + 0.8):                                         # tape across the head, sagging
        pts = [Vector((h1 - 0.02, y0 + 0.05, z)), Vector((h1 - 0.02, yc, z - 0.07)), Vector((h1 - 0.02, y1 - 0.05, z - 0.01))]
        for a, b in zip(pts, pts[1:]):
            d = b - a
            add_box(B.bm, (a + b) / 2, (0.003, d.length, 0.05), mat=yel,
                    rot=_rx(math.atan2(d.z, d.y)))
    sign(B, (RIGHT_WALL[1] + 0.35, y0 - 0.002, DECK + 0.32), 0.42, 0.21, R_HAZARD, B('atlas'))
    bx(B.bm, (RIGHT_WALL[1] + 0.13, RIGHT_WALL[1] + 0.57), (y0 + 0.0, y0 + 0.02), (DECK + 0.2, DECK + 0.44), B('wood'), 0.004)
    sign(B, (128.45, SHAFT_BACK - 0.005, DECK + 1.15), 0.8, 0.2, R_STAIR, B('atlas'))
    # The top flight: torn from the landing's edge, three treads hanging steeply, its stringers bent and ragged.
    tb = bmesh.new()
    stair_flight(tb, 3, w, stl, B('plate'), yel)
    for k in range(4):                                                          # torn stringer ends
        add_box(tb, (0.72 + 0.02 * k, (-1 if k % 2 else 1) * (w / 2 - 0.02), -0.6 - 0.05 * k), (0.06, 0.02, 0.12), mat=stl,
                rot=_ry(0.6 * k))
    _merge_into(B, tb, Matrix.Translation((h1 + 0.01, yc, DECK - 0.02)) @ _ry(math.radians(38)) @ _rx(math.radians(6)))
    # The fallen flight: five treads lying askew on the rubble, its foot near where the stair came down.
    fb = bmesh.new()
    stair_flight(fb, 5, w, stl, B('plate'), yel)
    _merge_into(B, fb, Matrix.Translation((129.25, yc + 0.22, 0.62)) @ _rz(math.radians(-6)) @ _ry(math.radians(-14))
                @ _rx(math.radians(-18)))
    B.done('UOStairSteel', coll)

    # The rubble: the stair's concrete, broken; lumps of the back wall's anchor; loose treads; dust spilling toward the
    # lane but not on it.
    B = Batch(U)
    con, rock, stl = B('concrete'), B('rock'), B('steel')
    rnd = random.Random(1015)
    for k in range(18):
        s = rnd.uniform(0.12, 0.4)
        x = rnd.uniform(128.55, STAIR_FOOT + 0.1)
        y = rnd.uniform(0.75, 1.8)
        zc = s * 0.3 + max(0.0, 0.35 - abs(x - 129.5) * 0.25) * (1.0 if y > 1.0 else 0.6)
        rounded_box((s * 1.3, s, s * 0.8), (x, y, zc), p=2.2, cuts=2, dents=((s * 0.12, 3.0),), seed=k * 1.7,
                    mat=con if k % 3 else rock, bm=B.bm, rot=_rz(rnd.uniform(0, 3)) @ _rx(rnd.uniform(-0.4, 0.4)))
    for k in range(14):
        s = rnd.uniform(0.04, 0.1)
        add_sphere(B.bm, (rnd.uniform(128.3, STAIR_FOOT + 0.2), rnd.uniform(0.42, 1.5), s * 0.3), s, seg=6,
                   scale=(1.3, 1, 0.55), dents=(s * 0.25, 9), mat=con)
    for k in range(4):                                                          # rebar out of the broken edge
        a = Vector((h1 + 0.02, y0 + 0.15 + k * 0.25, DECK - 0.12))
        add_cyl(B.bm, a, a + Vector((0.18 + 0.05 * k, 0.02, -0.12 - 0.04 * k)), 0.006, seg=4, mat=B('rust'))
    for x, y, a in ((130.05, 0.95, 0.35), (128.75, 1.45, -0.6)):                 # loose treads
        cbox(B.bm, (x, y, 0.03), (0.26, 0.9, 0.04), 0.008, stl, rot=_rz(a) @ _rx(0.2))
    rounded_box((2.2, 1.3, 0.25), (129.6, 1.25, 0.03), p=2.0, cuts=3, dents=((0.03, 4.0),), seed=5.0, mat=con, bm=B.bm)   # dust heap
    # The scar on the back wall where the flight was anchored.
    for k in range(5):
        x = h1 + 0.3 + k * 0.38
        z = DECK - 0.2 - k * 0.32
        bx(B.bm, (x - 0.1, x + 0.1), (SHAFT_BACK - 0.03, SHAFT_BACK - 0.005), (z - 0.08, z + 0.06), B('dark'))
        add_cyl(B.bm, (x, SHAFT_BACK - 0.01, z), (x + 0.03, SHAFT_BACK - 0.14, z - 0.06), 0.008, seg=4, mat=stl)
    B.done('UOStairRubble', coll)


# --------------------------------------------------------------------------
# Entry points
# --------------------------------------------------------------------------

def build_set(dl01, m, coll):
    make_textures()
    U = up_materials(m)
    clear_site()
    build_shell(U, coll, dl01)
    build_luggage(U, coll)
    build_waiting(U, coll)
    build_lift_front(U, coll)
    build_panel(U, coll)
    build_car(U, coll)
    build_service(U, coll)
    build_suitcase114(U, coll)
    build_stair(U, coll)


# --------------------------------------------------------------------------
# D-17 clips
# --------------------------------------------------------------------------

PRESS_AT = 16                         # the frame the push goes in
PRESS_WRIST = Vector((-0.133, -0.159, 0.559))     # the right wrist on the button (body space): the push 0.30 ahead, 0.12 right, 0.56 up
PRESS_AIM = Vector((0.15, -0.95, 0.2))
PRESS_VIA = Vector((-0.26, -0.16, 0.34))


def clip_press_button_high(dl01, arm):
    """Facing a wall button 0.30 ahead, 0.12 to his right and 0.56 up (the game turns him to it): he looks up at it,
    raises his right claw out past the pod, pushes (the button goes in at frame 16), holds, and lets it go."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 36
    c = Clip(arm, 'PressButtonHigh', frames)
    carry_w = REST[-1] + CARRY[-1]

    def via(p0, p1, p2, t):
        t = max(0.0, min(1.0, t))
        return p0 * (1 - t) ** 2 + p1 * (2 * (1 - t) * t) + p2 * t * t

    def aim(d):
        d = Vector(d).normalized()
        a = -math.acos(max(-1.0, min(1.0, -d.z)))
        sa = math.sin(a)
        return (math.degrees(a), 0.0, math.degrees(math.atan2(-d.x / sa, d.y / sa)))

    rest_r = (-24.0, -6.0, -10.0)
    for frame in range(1, frames + 1):
        f = frame - 1
        up = track([(1, 0), (11, 1), (24, 1), (34, 0)], f)
        push = track([(PRESS_AT - 3, 0), (PRESS_AT, 1), (PRESS_AT + 5, 1), (PRESS_AT + 8, 0)], f)
        wrist = via(carry_w, PRESS_VIA, PRESS_WRIST + Vector((0, 0.03 * (1 - up), 0)), up) + Vector((0, -0.012 * push, 0))
        hands = {1: CARRY[1], -1: wrist - REST[-1]}
        body = (0, -0.008 * up - 0.004 * push, 0.012 * up)
        rot = (track([(0, 0), (10, 4), (24, 4), (34, 0)], f) + 1.5 * push, track([(6, 0), (12, -2), (26, -2), (34, 0)], f), 0)
        hr = aim(PRESS_AIM)
        head = (track([(0, 0), (8, -16), (26, -14), (34, 0)], f), track([(4, 0), (10, -8), (26, -6), (34, 0)], f),
                track([(0, 0), (8, 4), (26, 3), (34, 0)], f))
        antenna = [(track([(0, 0), (10, -10), (PRESS_AT, -10), (PRESS_AT + 2, -20), (26, -12), (35, 0)], f) * (0.8 + 0.15 * i)
                    + spring(f, PRESS_AT, -5), 0) for i in range(3)]
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands,
               hand_rot={'L': (-24.0, 6.0, 10.0), 'R': tuple(a + (b - a) * up for a, b in zip(rest_r, hr))},
               claws={'L': CLAW_REST_OPEN['L'], 'R': track([(2, 1), (8, 2), (28, 2), (34, 1)], f)}, elbows={'R': 0.6 * up})
    c.done()


RIDE_FRAMES = 96


def clip_ride_counterweight(dl01, arm):
    """Riding the counterweight down (the game turns him to face +x on its footplate, between its side rails):
    he crouches and takes a rail in each claw (frames 0 to 12), braced; as it goes down he looks up and back over
    his left shoulder at the car going up with the suitcase (16 to 58), holds there, then turns to look down at
    ring C coming (64 to 90). A low hum runs through him. Play once; hold the last frame."""
    import build_dl02
    track, Clip, REST = dl01.track, dl01.Clip, dl01.REST_WRIST
    c = Clip(arm, 'RideCounterweight', RIDE_FRAMES)
    grip = {s: Vector((s * (CW_RAIL_Y - 0.015), -0.04, CW_RAIL_Z + 0.063)) for _, s in SIDES}
    tau = 2 * math.pi
    for frame in range(1, RIDE_FRAMES + 1):
        f = frame - 1
        k = track([(0, 0), (12, 1)], f)
        hum = 0.0015 * math.sin(f * 2.3) + 0.001 * math.sin(f * 3.7)
        body = (0.0, 0.004 * math.sin(tau * f / 48), -0.13 * k + hum)
        rot = (6.0 * k + 0.6 * math.sin(tau * f / 48), 0.8 * math.sin(tau * f / 32), 0)
        held = build_dl02.reach(grip, body, rot, REST)
        hands = {s: dl01.CARRY[s].lerp(held[s], k) for _, s in SIDES}
        up = track([(16, 0), (30, 1), (56, 1), (66, 0)], f)
        down = track([(64, 0), (78, 1), (RIDE_FRAMES - 1, 1)], f)
        head = (-rot[0] - 38 * up + 26 * down, 26 * up * 0.4, 38 * up)
        head = (head[0], head[1] + 2 * math.sin(f * 0.21), head[2])
        antenna = [(-30 * k + 14 * up - 10 * down + 3 * math.sin(tau * f / 24 - i), 0) for i in range(3)]
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands,
               hand_rot={'L': (-70 * k - 24 * (1 - k), 0, 10), 'R': (-70 * k - 24 * (1 - k), 0, -10)},
               claws={'L': 20 - 16 * k, 'R': 1 + 3 * k}, elbows={'L': k, 'R': k})
    c.done()


def add_clips(dl01, arm):
    clip_press_button_high(dl01, arm)
    clip_ride_counterweight(dl01, arm)
