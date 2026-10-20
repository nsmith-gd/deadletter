"""Chapter 1, pass 3 (docs/chapter1_pass3_plan.md): DL-05 The Ration Hall. Built in FINAL world x, after
insert_scenes() has opened the gap between the Racks' service passage (ends x 47.9) and the scanner corridor of
the return line (starts x 59.9).

The depot workers' canteen and ration counter, the bottom of the refuge, where the labour grades queued and where
families slept when ring C flooded. Left to right:

    x 47.9 to 48.1   the hall's end wall, with a doorway the size of the Racks' passage (y -0.9 to 0.67, 2.4 high)
    x 48.1 to 53.2   the canteen: the shrine on the first column (49.65), the queue barriers folded into a maze
                     behind the lane (50.1 to 52.6), canteen tables with cots between them and bedrolls everywhere,
                     the painted sky on the back wall, the grade notice and the tally marks on the second column
    x 53.2 to 56.6   the ration counter behind the lane, its grille, fascia and chalked ration board; the winch at
                     its left end (53.55), the crayon drawing taped beside it, the ration drum on its guide (54.6)
    x 56.6 to 56.84  the kitchen wall, with the serving hatch (y -0.6 to 0.77, 1.30 high) and its steel shutter
    x 56.84 to 59.9  the kitchen, stripped, low (2.4), running into the scanner corridor's section at 59.9

The puzzle: the shutter drops the moment the winch's wheel is let go. Push the drum along its guide until it
stops against the shutter (its rim under the shutter's lip), wind, let go: the lip slams onto the drum's rim and
holds at 0.64, and he crouches under. The lip carries a drum-shaped arc dent (and the floor a rust ring): it has
been done before.

Driven by the game (game/undelivered/index.html):
    RationShutter  origin on its bottom edge (the lip's underside) at (SHUTTER_X, 0, 0); moves in z (game y)
    RationWinch    the handwheel; origin at its axle (WINCH); turns about y (game z), 60 degrees a Crank stroke
    RationDrum     the pushable drum; origin at its base centre (DRUM_START_X, DRUM_Y, 0); moves in x
    RationLamp     the counter's strip tube (emissive; flickers)
    RationCandles  the shrine's candle flames (emissive)

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y.
"""
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector, noise

import build_d17 as d17
from build_d17 import add_box, add_cyl, add_sphere, add_torus, rounded_box, worn_material, emission_material, simple_material

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import textures_ration_hall as tex  # noqa: E402

# --------------------------------------------------------------------------
# Layout (shared with the game: keep game/undelivered/index.html in step)
# --------------------------------------------------------------------------
X0, X1 = 47.9, 59.9                  # the hall's span: from the Racks' passage to the scanner corridor
ENTRY = (47.9, 48.1)                 # the hall's end wall, with the passage-sized doorway
DOOR_Y1, DOOR_H = 0.67, 2.4          # the doorway: y -0.9 to 0.67, 2.4 high (the Racks' passage section)
FRONT_Y = -0.9                       # walls are cut here, toward the camera
BACK_Y, CEIL = 3.6, 4.4              # the canteen's back wall and ceiling
COLUMNS = ((49.65, 1.35), (52.85, 1.35))
COL_W = 0.36
FLOOR_X = (51.0, 63.0)               # RationFloor: RacksFloor stops at 51 and SortingFloor starts at 63

COUNTER = (53.2, 56.6)               # the ration counter, behind the lane
COUNTER_Y = (0.68, 1.28)             # its front face and back
COUNTER_TOP = 0.95
GRILLE_Y = 0.98
FASCIA_Z = (2.2, 2.6)
SERVERY_Y = 2.0                      # the servery's back wall, behind the counter

PART = (56.6, 56.84)                 # the kitchen wall
HATCH_Y = (-0.6, 0.77)               # the serving hatch through it
HATCH_TOP = 1.30
KITCHEN_BACK, KITCHEN_CEIL = 1.8, 2.4
CORRIDOR_BACK = 0.67                 # art/dl03's scanner corridor section, which starts at x 59.9

SHUTTER_X = 56.48                    # the shutter's plane, on the hall face of the kitchen wall
SHUTTER_T = 0.03                     # its slats
SHUTTER_Y = (-0.55, 0.72)            # its span across the hatch
SHUTTER_H = 1.36                     # bottom edge to top
SHUTTER_LIP = 0.16                   # the bottom bar's lip, reaching toward the hall
SHUTTER_OPEN = 1.2                   # fully wound (its bottom edge)
HOUSING = (56.40, 56.60, 1.30, 2.62)  # x0, x1, z0, z1 of the box it winds up into

DRUM_Y = 0.38                        # behind the lane (game z -0.38)
DRUM_R = 0.225                       # its half-width: the chimes and rolling hoops
DRUM_H = 0.65                        # the top chime
DRUM_START_X = 54.6
DRUM_STOP_X = SHUTTER_X - SHUTTER_T / 2 - DRUM_R - 0.02      # 56.22: against the shutter, rim under its lip
DENT = 0.01                          # the lip's dent, where drums' chimes have bitten
SHUTTER_REST = DRUM_H - DENT         # 0.64: on the drum
GUIDE_X0 = 54.25                     # the drum's floor guide runs from here to the stop

WINCH = Vector((53.55, 0.2, 0.45))   # the handwheel's axle centre; as DL-01's crank (the Crank clip fits)
WHEEL_R = 0.15
PULLEY_Z = 2.78                      # the cable's run from the winch to the shutter housing
CABLE_Y = 0.43

LAMP = (54.75, 0.25, 2.05)           # the strip tube's centre over the counter, between the winch and the hatch
LAMP_LEN = 2.0
SHRINE_X = COLUMNS[0][0]
CANDLE_FLAMES = []                   # filled by build_shrine: (x, y, z) of each lit flame


# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------

def _image_material(name, path, rough=0.75, alpha=False):
    mat, nt, bsdf = d17._new_material(name)
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    if alpha:
        nt.links.new(t.outputs['Alpha'], bsdf.inputs['Alpha'])
        for attr, value in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
            if hasattr(mat, attr):
                try:
                    setattr(mat, attr, value)
                except (TypeError, ValueError):
                    pass
    return mat


NEW = {
    # The drum: olive paint over steel, worn to bright metal at its chimes and hoops (the game's WORN table).
    'DrumOlive': lambda: worn_material('DrumOlive', base=(0.07, 0.08, 0.05), dirt=(0.045, 0.038, 0.024),
                                       chip=(0.26, 0.25, 0.22), rough=0.62, chip_rough=0.35, metallic=0.35,
                                       grime_scale=6, chip_scale=30, chip_amount=0.68, streaks=0.5,
                                       dust=(0.1, 0.095, 0.08), dust_amount=0.5),
    # Bare steel polished by hands: pale and only a little metallic, so it reads bright under the scene's light
    # (a metallic finish goes dark without an environment to reflect).
    'HandWorn': lambda: worn_material('HandWorn', base=(0.46, 0.44, 0.39), dirt=(0.2, 0.18, 0.15),
                                      chip=(0.62, 0.6, 0.55), rough=0.35, chip_rough=0.3, metallic=0.3,
                                      grime_scale=22, chip_scale=60, chip_amount=0.72, edge_wear=False, streaks=0.2,
                                      dust_amount=0.0),
    'CotCanvas': lambda: worn_material('CotCanvas', base=(0.16, 0.15, 0.1), dirt=(0.08, 0.07, 0.045),
                                       chip=(0.2, 0.19, 0.15), rough=0.95, chip_rough=0.95, metallic=0.0,
                                       grime_scale=6, chip_scale=30, chip_amount=0.78, streaks=0.3),
    'CanteenGreen': lambda: worn_material('CanteenGreen', base=(0.1, 0.13, 0.1), dirt=(0.05, 0.055, 0.045),
                                          chip=(0.16, 0.15, 0.13), rough=0.85, chip_rough=0.9, metallic=0.0,
                                          grime_scale=2, chip_scale=14, chip_amount=0.7, streaks=0.8),
    'CandleWax': lambda: simple_material('CandleWax', (0.55, 0.5, 0.4), 0.6),
    'RationLamp': lambda: emission_material('RationLamp', (0.86, 0.95, 0.84), 3.0),
    'RationCandle': lambda: emission_material('RationCandle', (1.0, 0.62, 0.25), 4.0),
    'RationBoardMat': lambda: _image_material('RationBoardMat', tex.texture('ration_board.png'), 0.9),
    'GradeNoticeMat': lambda: _image_material('GradeNoticeMat', tex.texture('grade_notice.png'), 0.85),
    'SkyMuralMat': lambda: _image_material('SkyMuralMat', tex.texture('sky_mural.png'), 0.9),
    'CrayonDrawingMat': lambda: _image_material('CrayonDrawingMat', tex.texture('crayon_drawing.png'), 0.85),
    'ShrineNamesMat': lambda: _image_material('ShrineNamesMat', tex.texture('shrine_names.png'), 0.85, alpha=True),
    'ChalkTally': lambda: _image_material('ChalkTally', tex.texture('chalk_tally.png'), 0.95, alpha=True),
    'DrumStencil': lambda: _image_material('DrumStencil', tex.texture('drum_stencil.png'), 0.7, alpha=True),
    'RationSignMat': lambda: _image_material('RationSignMat', tex.texture('ration_sign.png'), 0.8),
    'DrumRingMat': lambda: _image_material('DrumRingMat', tex.texture('drum_ring.png'), 0.95, alpha=True),
}


def mat(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = NEW[name]() if name in NEW else simple_material(name, (0.1, 0.1, 0.1), 0.8)
    return m


class Parts:
    """Static geometry, gathered by material and merged into one object per material at the end."""
    def __init__(self):
        self.bms = {}

    def __getitem__(self, key):
        if key not in self.bms:
            self.bms[key] = bmesh.new()
        return self.bms[key]

    def emit(self, coll):
        out = []
        for key, bm in self.bms.items():
            if len(bm.verts):
                out.append(d17.mesh_object('RationSet' + key, bm, [mat(key)], coll, sharp=35))
        return out


def obj(name, bm, mats, coll, sharp=35):
    return d17.mesh_object(name, bm, [mat(n) for n in mats], coll, sharp=sharp)


def flat_obj(name, bm, mats, coll):
    """A mesh kept exactly as wound (decals: one-sided in the game, so their normals must face out)."""
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for n in mats:
        me.materials.append(mat(n))
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def quad(bm, uv, corners, mi=0, uvs=((0, 0), (1, 0), (1, 1), (0, 1))):
    f = bm.faces.new([bm.verts.new(c) for c in corners])
    f.material_index = mi
    for lp, t in zip(f.loops, uvs):
        lp[uv].uv = t
    return f


def decal(name, matname, x0, x1, z0, z1, y, coll, tilt=0.0):
    """A picture on a wall facing the camera (-y): x0..x1, z0..z1, at y; optional tilt about y (radians)."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    r = Matrix.Rotation(tilt, 3, 'Y')
    pts = [Vector((cx, y, cz)) + r @ Vector(p) for p in ((x0 - cx, 0, z0 - cz), (x1 - cx, 0, z0 - cz),
                                                         (x1 - cx, 0, z1 - cz), (x0 - cx, 0, z1 - cz))]
    quad(bm, uv, pts)
    return flat_obj(name, bm, [matname], coll)


def floor_decal(name, matname, cx, cy, size, coll, z=0.002):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    h = size / 2
    quad(bm, uv, [(cx - h, cy - h, z), (cx + h, cy - h, z), (cx + h, cy + h, z), (cx - h, cy + h, z)])
    return flat_obj(name, bm, [matname], coll)


def box(bm, x0, x1, y0, y1, z0, z1, rot=None):
    return add_box(bm, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), mat=0, rot=rot)


def rbox(bm, x0, x1, y0, y1, z0, z1, p=8.0, cuts=4, dents=(), seed=0.0, rot=None):
    """A box with softened edges (a superellipsoid): the bevel the set's quality bar asks for."""
    return rounded_box((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2),
                       p=p, cuts=cuts, dents=dents, seed=seed, bm=bm, mat=0, rot=rot)


def cyl(bm, a, b, r, r2=None, seg=12):
    return add_cyl(bm, a, b, r, r2, mat=0, seg=seg)


def polyline(bm, pts, r, seg=6):
    for a, b in zip(pts, pts[1:]):
        add_cyl(bm, a, b, r, mat=0, seg=seg)


def lathe(bm, profile, seg, center=(0, 0, 0), mat_of=None, a0=0.0, a1=2 * math.pi, uv=None):
    """Revolve [(r, z), ...] about z. mat_of(r, z, angle) -> material index per face."""
    c = Vector(center)
    closed = abs(a1 - a0 - 2 * math.pi) < 1e-6
    n = seg if closed else seg + 1
    rings = []
    for r, z in profile:
        ring = []
        for i in range(n):
            a = a0 + (a1 - a0) * i / seg
            ring.append(bm.verts.new(c + Vector((r * math.cos(a), r * math.sin(a), z))))
        rings.append(ring)
    faces = []
    for j in range(len(profile) - 1):
        for i in range(seg):
            i2 = (i + 1) % n if closed else i + 1
            vs = (rings[j][i], rings[j][i2], rings[j + 1][i2], rings[j + 1][i])
            if len(set(vs)) < 4:
                continue
            try:
                f = bm.faces.new(vs)
            except ValueError:
                continue
            if mat_of:
                rm = (profile[j][0] + profile[j + 1][0]) / 2
                zm = (profile[j][1] + profile[j + 1][1]) / 2
                am = a0 + (a1 - a0) * (i + 0.5) / seg
                f.material_index = mat_of(rm, zm, am)
            faces.append(f)
    return rings, faces


def face_out(ob, outward, mats):
    """mesh_object recalculates normals, which can turn an open strip (a decal) inward: flip those faces of the
    given material slots whose normal disagrees with outward(centre). They are one-sided in the game."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bad = [f for f in bm.faces if f.material_index in mats and f.normal.dot(outward(f.calc_center_median())) < 0]
    if bad:
        bmesh.ops.reverse_faces(bm, faces=bad)
        bm.to_mesh(ob.data)
    bm.free()


def catenary(a, b, sag, n=10):
    a, b = Vector(a), Vector(b)
    return [a.lerp(b, t) - Vector((0, 0, sag * 4 * t * (1 - t))) for t in (i / n for i in range(n + 1))]


# --------------------------------------------------------------------------
# The room
# --------------------------------------------------------------------------

def build_shell(P):
    """Floor, walls, ceiling, columns, the kitchen wall with its hatch, the kitchen, and the joins at both ends."""
    # Floor: RacksFloor covers the hall to x 51; this runs on under the kitchen and the scanner corridor to 63,
    # where art/dl03's sorting floor begins (nothing else covers 51 to 63 since the gap was opened).
    bm = P['Concrete']
    box(bm, FLOOR_X[0], FLOOR_X[1], -4.0, 3.8, -0.1, 0.0)
    # The canteen's end wall, with the doorway from the Racks' passage, and a cut cap toward the camera.
    w = P['WallPanel']
    ex0, ex1 = ENTRY
    box(w, ex0, ex1, DOOR_Y1, BACK_Y + 0.2, 0, CEIL)
    box(w, ex0, ex1, FRONT_Y, DOOR_Y1, DOOR_H, CEIL)
    # The back wall, the ceiling slab and its beams.
    box(w, ex0, PART[0], BACK_Y, BACK_Y + 0.2, 0, CEIL)
    box(w, ex0, PART[1], FRONT_Y, BACK_Y + 0.2, CEIL, CEIL + 0.2)
    for x in (50.3, 52.85, 55.2):
        rbox(w, x - 0.15, x + 0.15, FRONT_Y, BACK_Y, CEIL - 0.42, CEIL + 0.01, p=10)
    rbox(w, ex1, PART[0], COLUMNS[0][1] - 0.14, COLUMNS[0][1] + 0.14, CEIL - 0.36, CEIL + 0.01, p=10)
    # Columns, chamfered, with a painted dado band and a plinth.
    g = P['CanteenGreen']
    for x, y in COLUMNS:
        rbox(w, x - COL_W / 2, x + COL_W / 2, y - COL_W / 2, y + COL_W / 2, 0, CEIL, p=12, cuts=3)
        rbox(g, x - COL_W / 2 - 0.012, x + COL_W / 2 + 0.012, y - COL_W / 2 - 0.012, y + COL_W / 2 + 0.012, 0.06, 1.22, p=14, cuts=3)
        rbox(P['Concrete'], x - COL_W / 2 - 0.03, x + COL_W / 2 + 0.03, y - COL_W / 2 - 0.03, y + COL_W / 2 + 0.03, 0, 0.07, p=6, cuts=2)
    # The canteen dado: green to 1.2 on the back wall and the end wall, with a rail on top.
    box(g, ex1, PART[0], BACK_Y - 0.02, BACK_Y, 0, 1.2)
    box(g, ex1, ex1 + 0.02, DOOR_Y1, BACK_Y, 0, 1.2)
    st = P['DepotSteel']
    rbox(st, ex1, PART[0], BACK_Y - 0.045, BACK_Y, 1.19, 1.24, p=4, cuts=2)
    # Pipes along the back wall high up, and a conduit down the end wall.
    for z, r in ((3.86, 0.06), (4.08, 0.04)):
        cyl(st, (ex1, BACK_Y - 0.14, z), (PART[0], BACK_Y - 0.14, z), r, seg=12)
        for x in (49.0, 51.2, 53.4, 55.6):
            box(st, x - 0.02, x + 0.02, BACK_Y - 0.2, BACK_Y, z - r - 0.02, z + r + 0.02)
    cyl(st, (ex1 + 0.06, 2.6, 0.2), (ex1 + 0.06, 2.6, CEIL), 0.025, seg=8)

    # The kitchen wall, with the serving hatch through it.
    k0, k1 = PART
    box(w, k0, k1, FRONT_Y, HATCH_Y[0], 0, CEIL)
    box(w, k0, k1, HATCH_Y[0], HATCH_Y[1], HATCH_TOP, CEIL)
    box(w, k0, k1, HATCH_Y[1], BACK_Y + 0.2, 0, CEIL)
    # The hatch's steel frame on the hall face, and the shutter's guide channels.
    for y in HATCH_Y:
        rbox(st, k0 - 0.04, k0 + 0.01, y - 0.04, y + 0.04, 0, HATCH_TOP + 0.04, p=6, cuts=2)
    rbox(st, k0 - 0.04, k0 + 0.01, HATCH_Y[0] - 0.04, HATCH_Y[1] + 0.04, HATCH_TOP - 0.02, HATCH_TOP + 0.06, p=6, cuts=2)
    sy0, sy1 = SHUTTER_Y
    for ya, yb in ((sy0 - 0.06, sy0 + 0.01), (sy1 - 0.01, sy1 + 0.06)):
        for xa, xb in ((SHUTTER_X - 0.035, SHUTTER_X - 0.022), (SHUTTER_X + 0.022, SHUTTER_X + 0.035)):
            box(st, xa, xb, ya, yb, 0, HOUSING[2] + 0.02)
        y_out = ya if ya < sy0 else yb - 0.013
        box(st, SHUTTER_X - 0.035, SHUTTER_X + 0.035, y_out, y_out + 0.013, 0, HOUSING[2] + 0.02)
        for z in (0.2, 0.75, 1.2):                                     # brackets back to the wall
            box(st, SHUTTER_X + 0.035, k0, (ya + yb) / 2 - 0.02, (ya + yb) / 2 + 0.02, z - 0.03, z + 0.03)
    # The housing the shutter winds up into: sheet steel, with stiffening ribs and rivets.
    hx0, hx1, hz0, hz1 = HOUSING
    sh = P['ShutterSteel']
    rbox(sh, hx0, hx1, sy0 - 0.11, sy1 + 0.11, hz0, hz1, p=10, cuts=4, dents=((0.003, 4.0),), seed=7)
    for z in (hz0 + 0.06, hz1 - 0.06):
        rbox(st, hx0 - 0.012, hx0 + 0.02, sy0 - 0.12, sy1 + 0.12, z - 0.025, z + 0.025, p=4, cuts=2)
    for y in (sy0 - 0.02, 0.085, sy1 + 0.02):
        rbox(st, hx0 - 0.012, hx0 + 0.02, y - 0.025, y + 0.025, hz0, hz1, p=4, cuts=2)
    for y in (sy0 + 0.2, sy1 - 0.2):
        for z in (hz0 + 0.06, hz1 - 0.06):
            add_sphere(P['DepotSteel'], (hx0 - 0.014, y, z), 0.008, mat=0, seg=6)

    # The kitchen: low, tiled, its ceiling and back wall running into the corridor's section at 59.9.
    box(w, k1, X1, -1.4, KITCHEN_BACK + 0.1, KITCHEN_CEIL, KITCHEN_CEIL + 0.1)
    box(w, k1, X1, KITCHEN_BACK, KITCHEN_BACK + 0.1, 0, CEIL)
    box(w, X1 - 0.1, X1, CORRIDOR_BACK, KITCHEN_BACK + 0.1, 0, CEIL)       # closes the step to the corridor
    en = P['BayEnamel']
    box(en, k1, X1 - 0.1, KITCHEN_BACK - 0.015, KITCHEN_BACK, 0.12, 1.55)  # tiles
    gr = P['SectionCap']
    for k in range(1, 10):                                                 # their courses
        box(gr, k1, X1 - 0.1, KITCHEN_BACK - 0.018, KITCHEN_BACK - 0.014, 0.12 + k * 0.15 - 0.004, 0.12 + k * 0.15 + 0.004)
    x = k1 + 0.15
    while x < X1 - 0.12:
        box(gr, x - 0.004, x + 0.004, KITCHEN_BACK - 0.018, KITCHEN_BACK - 0.014, 0.12, 1.55)
        x += 0.15
    box(P['DepotSteel'], k1, X1 - 0.1, KITCHEN_BACK - 0.03, KITCHEN_BACK, 0, 0.12)   # skirting
    # A floor drain in the kitchen.
    cyl(P['CastIron'], (57.7, 0.9, 0.0), (57.7, 0.9, 0.004), 0.12, seg=16)
    for k in range(-3, 4):
        box(P['DepotSteel'], 57.7 + k * 0.03 - 0.006, 57.7 + k * 0.03 + 0.006, 0.9 - 0.1, 0.9 + 0.1, 0.0, 0.006)


def build_counter(P, coll):
    """The ration counter: panelled front, a worn wooden top, the grille, the fascia, the servery behind."""
    c0, c1 = COUNTER
    fy, by = COUNTER_Y
    w = P['WallPanel']
    # Body and front panels (DepotGreen) with shadow gaps, a scuffed steel kick plate.
    box(w, c0, c1, fy + 0.03, by, 0, COUNTER_TOP - 0.03)
    n = 6
    pw = (c1 - c0) / n
    for i in range(n):
        x0 = c0 + i * pw + 0.012
        rbox(P['DepotGreen'], x0, x0 + pw - 0.024, fy, fy + 0.035, 0.14, COUNTER_TOP - 0.05, p=10, cuts=3,
             dents=((0.0015, 6.0),), seed=i)
    rbox(P['DepotSteel'], c0, c1, fy - 0.012, fy + 0.03, 0, 0.13, p=6, cuts=3)
    # The top: wood, its front edge rounded and worn where elbows leaned.
    rbox(P['CrateWood'], c0 - 0.03, c1, fy - 0.05, by + 0.02, COUNTER_TOP - 0.035, COUNTER_TOP + 0.01, p=5, cuts=6,
         dents=((0.002, 9.0),), seed=3)
    # The grille: bars up to the fascia, two serving slots cut through it at counter height.
    st = P['DepotSteel']
    slots = ((54.35, 54.75), (55.55, 55.95))
    x = c0 + 0.06
    while x < SHUTTER_X - 0.2:
        z0 = COUNTER_TOP + 0.01
        if any(a < x < b for a, b in slots):
            z0 = 1.24
        cyl(st, (x, GRILLE_Y, z0), (x, GRILLE_Y, FASCIA_Z[0]), 0.008, seg=6)
        x += 0.1
    for z in (1.24, 1.66, FASCIA_Z[0] - 0.02):
        rbox(st, c0 + 0.02, SHUTTER_X - 0.18, GRILLE_Y - 0.015, GRILLE_Y + 0.015, z - 0.015, z + 0.015, p=4, cuts=2)
    for a, b in slots:                                        # the slot's little sill, worn
        rbox(P['HandWorn'], a, b, GRILLE_Y - 0.12, GRILLE_Y + 0.05, COUNTER_TOP + 0.01, COUNTER_TOP + 0.02, p=4, cuts=2)
    # The fascia and its sign; the servery's walls behind.
    rbox(P['DepotGreen'], c0 - 0.05, HOUSING[0] - 0.02, 0.82, 0.99, FASCIA_Z[0], FASCIA_Z[1], p=10, cuts=4)
    decal('RationSign', 'RationSignMat', c0 + 0.2, c0 + 2.8, FASCIA_Z[0] + 0.06, FASCIA_Z[0] + 0.385, 0.816, coll)
    box(w, c0, PART[0], SERVERY_Y, SERVERY_Y + 0.1, 0, FASCIA_Z[1])
    box(w, c0 - 0.06, c0 + 0.04, fy, SERVERY_Y + 0.1, 0, FASCIA_Z[1])
    # The servery's shelves, bare: a stack of empty trays, two tins, a ledger, an upturned bowl.
    pw_ = P['PigeonWood']
    for z in (1.1, 1.5, 1.9):
        rbox(pw_, c0 + 0.15, PART[0] - 0.1, SERVERY_Y - 0.28, SERVERY_Y, z - 0.015, z + 0.015, p=5, cuts=2)
        for x in (c0 + 0.4, 55.0, 56.3):
            box(P['CastIron'], x - 0.01, x + 0.01, SERVERY_Y - 0.24, SERVERY_Y, z - 0.12, z - 0.015)
    for k in range(5):
        rbox(P['BareMetal'], 53.6, 54.1, SERVERY_Y - 0.26, SERVERY_Y - 0.04, 1.115 + k * 0.022, 1.13 + k * 0.022, p=4, cuts=2)
    for x in (55.4, 55.52):
        cyl(P['BareMetal'], (x, SERVERY_Y - 0.15, 1.515), (x, SERVERY_Y - 0.15, 1.62), 0.045, seg=14)
    rbox(P['ParcelBrown'], 54.6, 54.95, SERVERY_Y - 0.25, SERVERY_Y - 0.03, 1.915, 1.96, p=5, cuts=2)

    # On the counter: the ration scale, a stack of tin bowls by the first slot, a ledger, a stamp.
    s = P['BareMetal']
    x, y = 55.15, 0.82
    rbox(P['DepotGreen'], x - 0.12, x + 0.12, y - 0.1, y + 0.1, COUNTER_TOP, COUNTER_TOP + 0.08, p=6, cuts=3)
    cyl(s, (x, y, COUNTER_TOP + 0.08), (x, y, COUNTER_TOP + 0.16), 0.012, seg=8)
    cyl(s, (x, y, COUNTER_TOP + 0.16), (x, y, COUNTER_TOP + 0.175), 0.13, 0.15, seg=24)
    for k in range(4):
        cyl(s, (54.55, 0.8, COUNTER_TOP + k * 0.022), (54.55, 0.8, COUNTER_TOP + 0.02 + k * 0.022), 0.07, 0.085, seg=18)
    rbox(P['ParcelBrown'], 55.85, 56.2, 0.72, 0.92, COUNTER_TOP, COUNTER_TOP + 0.035, p=5, cuts=2,
         rot=Matrix.Rotation(0.18, 4, 'Z'))
    cyl(P['PigeonWood'], (53.9, 0.8, COUNTER_TOP), (53.9, 0.8, COUNTER_TOP + 0.07), 0.022, seg=10)
    rbox(P['Rubber'], 53.87, 53.93, 0.77, 0.83, COUNTER_TOP, COUNTER_TOP + 0.015, p=4, cuts=2)

    # The ration board, hung on the grille, in a wooden frame.
    bx0, bx1, bz0, bz1 = 53.85, 55.15, 1.27, 1.97
    decal('RationBoard', 'RationBoardMat', bx0, bx1, bz0, bz1, GRILLE_Y - 0.05, coll)
    fw = P['CrateWood']
    for (x0, x1, z0, z1) in ((bx0 - 0.04, bx1 + 0.04, bz0 - 0.04, bz0), (bx0 - 0.04, bx1 + 0.04, bz1, bz1 + 0.04),
                             (bx0 - 0.04, bx0, bz0, bz1), (bx1, bx1 + 0.04, bz0, bz1)):
        rbox(fw, x0, x1, GRILLE_Y - 0.06, GRILLE_Y - 0.03, z0, z1, p=6, cuts=2)
    rbox(fw, bx0, bx1, GRILLE_Y - 0.12, GRILLE_Y - 0.04, bz0 - 0.04, bz0 - 0.02, p=4, cuts=2)  # chalk ledge
    for x in (bx0 + 0.1, bx1 - 0.1):
        polyline(P['Cable'], [(x, GRILLE_Y - 0.045, bz1 + 0.04), (x + (0.18 if x < 54.5 else -0.18), GRILLE_Y - 0.01, FASCIA_Z[0] - 0.02)], 0.003, 4)
    for k in range(3):                                       # chalk stubs on the ledge
        cyl(P['LetterPaper'], (bx0 + 0.3 + k * 0.08, GRILLE_Y - 0.09, bz0 - 0.012), (bx0 + 0.33 + k * 0.08, GRILLE_Y - 0.085, bz0 - 0.012), 0.006, seg=6)


def build_winch(P, coll):
    """The winch at the counter's left end: two cast frames, a pinion on the handwheel's axle driving a big gear
    on the cable spool above. Its ratchet's pawl has snapped (the bright break, the piece on the base plate):
    that is why the shutter drops the moment the wheel is let go. The cable climbs to a pulley over the counter,
    runs along under the ceiling to the shutter housing, and drops in."""
    wx, wy, wz = WINCH
    ir, st, pawl = P['CastIron'], P['DepotSteel'], P['HandWorn']
    # Base plate, bolted to the floor and the counter's kick plate.
    rbox(ir, wx - 0.25, wx + 0.25, wy + 0.06, COUNTER_Y[0] - 0.01, 0, 0.035, p=6, cuts=3)
    for x in (wx - 0.21, wx + 0.21):
        for y in (wy + 0.1, COUNTER_Y[0] - 0.05):
            cyl(st, (x, y, 0.03), (x, y, 0.05), 0.014, seg=6)
    # Frames: plates in the x-z plane with rounded tops, a rib down each edge.
    frame_y = (wy + 0.1, COUNTER_Y[0] - 0.05)
    z2 = wz + 0.05 + 0.165
    for fy in frame_y:
        for sx in (-1, 1):                               # an A of two legs, splayed, a tie across
            cyl(ir, (wx + sx * 0.2, fy, 0.03), (wx + sx * 0.06, fy, z2 + 0.06), 0.022, 0.018, seg=10)
            rbox(ir, wx + sx * 0.2 - 0.04, wx + sx * 0.2 + 0.04, fy - 0.03, fy + 0.03, 0.03, 0.06, p=5, cuts=2)
        cyl(ir, (wx - 0.15, fy, 0.24), (wx + 0.15, fy, 0.24), 0.014, seg=8)
        rbox(ir, wx - 0.09, wx + 0.09, fy - 0.018, fy + 0.018, wz - 0.06, z2 + 0.09, p=3.0, cuts=5, seed=fy)
    # Axle 1 (the handwheel's, which the game turns) with its pinion; axle 2 above with the gear and spool.
    cyl(st, (wx, wy + 0.05, wz), (wx, frame_y[1] + 0.04, wz), 0.02, seg=12)
    cyl(st, (wx, frame_y[0] - 0.03, z2), (wx, frame_y[1] + 0.04, z2), 0.024, seg=12)
    for fy in frame_y:
        for z in (wz, z2):
            cyl(ir, (wx, fy - 0.03, z), (wx, fy + 0.03, z), 0.045, seg=14)          # bearing bosses
    gy = frame_y[1] - 0.06

    def gear(cx, cz, r, teeth, y0, y1, bm):
        cyl(bm, (cx, y0, cz), (cx, y1, cz), r, seg=max(16, teeth))
        for k in range(teeth):
            a = 2 * math.pi * k / teeth
            add_box(bm, (cx + (r + 0.008) * math.cos(a), (y0 + y1) / 2, cz + (r + 0.008) * math.sin(a)),
                    (0.018, y1 - y0, 0.016 * r / 0.05 if r < 0.08 else 0.022), mat=0,
                    rot=Matrix.Rotation(-a, 4, 'Y'))
    gear(wx, wz, 0.045, 10, gy - 0.02, gy + 0.02, st)
    gear(wx, z2, 0.155, 36, gy - 0.016, gy + 0.016, ir)
    for k in range(5):                                          # the big gear's spokes, cut out
        a = 2 * math.pi * k / 5 + 0.3
        cyl(st, (wx, gy - 0.02, z2), (wx + 0.12 * math.cos(a), gy - 0.02, z2 + 0.12 * math.sin(a)), 0.012, seg=6)
    # The spool, the cable wound on it.
    sy0, sy1 = CABLE_Y - 0.06, CABLE_Y + 0.06
    for y in (sy0, sy1):
        cyl(ir, (wx, y - 0.008, z2), (wx, y + 0.008, z2), 0.1, seg=20)
    cyl(st, (wx, sy0, z2), (wx, sy1, z2), 0.055, seg=16)
    for k in range(7):
        add_torus(P['Cable'], (wx, sy0 + 0.012 + k * 0.016, z2), (0, 1, 0), 0.066, 0.008, mat=0, seg=18, rseg=5)
    # The ratchet wheel on the handwheel's axle, outside the front frame, and its snapped pawl.
    ry = frame_y[0] - 0.035
    gear(wx, wz, 0.06, 14, ry - 0.012, ry + 0.012, st)
    px, pz = wx + 0.13, wz + 0.1
    cyl(st, (px, ry - 0.025, pz), (px, ry + 0.02, pz), 0.012, seg=8)                # pawl pivot
    add_box(ir, (px - 0.02, ry, pz - 0.012), (0.05, 0.016, 0.022), mat=0, rot=Matrix.Rotation(0.5, 4, 'Y'))
    add_box(pawl, (px - 0.044, ry, pz - 0.026), (0.008, 0.017, 0.023), mat=0, rot=Matrix.Rotation(0.5, 4, 'Y'))   # the break
    add_box(ir, (wx + 0.16, wy + 0.2, 0.045), (0.06, 0.018, 0.02), mat=0, rot=Matrix.Rotation(0.9, 4, 'Z'))        # the piece
    # A spring that used to hold it, hanging loose.
    pts = [Vector((px + 0.01, ry, pz + 0.015)) + Vector((0.006 * math.cos(t * 1.4), 0.006 * math.sin(t * 1.4), -0.004 * t)) for t in range(14)]
    polyline(st, pts, 0.002, 4)

    # The cable: from the spool's right side straight up to a pulley over the counter, along under the ceiling
    # to a pulley over the housing, and down into it.
    cx_up = wx + 0.066
    p1 = Vector((cx_up + 0.06, CABLE_Y, PULLEY_Z))
    p2 = Vector((SHUTTER_X + 0.06 - 0.12, CABLE_Y, PULLEY_Z))
    cab = P['Cable']
    polyline(cab, [(cx_up, CABLE_Y, z2), (cx_up, CABLE_Y, PULLEY_Z)], 0.006, 6)
    polyline(cab, [(p1.x, CABLE_Y, PULLEY_Z + 0.06), (p2.x, CABLE_Y, PULLEY_Z + 0.06)], 0.006, 6)
    polyline(cab, [(p2.x + 0.06, CABLE_Y, PULLEY_Z), (p2.x + 0.06, CABLE_Y, HOUSING[3] - 0.02)], 0.006, 6)
    for p in (p1, p2):
        cyl(ir, p + Vector((0, -0.02, 0)), p + Vector((0, 0.02, 0)), 0.065, seg=20)
        add_torus(st, p, (0, 1, 0), 0.062, 0.008, mat=0, seg=20, rseg=5)
        # Straps up to the ceiling beam's line.
        for dy in (-0.035, 0.035):
            box(st, p.x - 0.012, p.x + 0.012, CABLE_Y + dy - 0.004, CABLE_Y + dy + 0.004, PULLEY_Z, CEIL)
    for x in (54.6, 55.6):                                      # cable eyes on hangers along the run
        cyl(st, (x, CABLE_Y, PULLEY_Z + 0.06), (x, CABLE_Y, CEIL), 0.006, seg=6)
        add_torus(st, (x, CABLE_Y, PULLEY_Z + 0.06), (1, 0, 0), 0.016, 0.004, mat=0, seg=10, rseg=4)

    # The handwheel itself: the game turns it about its axle. Hub and spokes cast iron; the rim and the
    # spinner knob polished bright by hands.
    bm = bmesh.new()
    cyl(bm, (0, -0.035, 0), (0, 0.1, 0), 0.035, seg=16)
    cyl(bm, (0, -0.045, 0), (0, -0.035, 0), 0.026, seg=16)
    for k in range(6):
        a = 2 * math.pi * k / 6 + math.radians(30)
        cyl(bm, (0.03 * math.cos(a), 0, 0.03 * math.sin(a)), ((WHEEL_R - 0.01) * math.cos(a), 0, (WHEEL_R - 0.01) * math.sin(a)), 0.009, seg=6)
    add_torus(bm, (0, 0, 0), (0, 1, 0), WHEEL_R, 0.016, mat=1, seg=36, rseg=8)
    ka = math.radians(90)
    kp = Vector((WHEEL_R * math.cos(ka), 0, WHEEL_R * math.sin(ka)))
    add_cyl(bm, kp, kp + Vector((0, -0.075, 0)), 0.014, 0.017, mat=1, seg=12)
    add_sphere(bm, kp + Vector((0, -0.078, 0)), 0.019, mat=1, seg=12)
    wheel = obj('RationWinch', bm, ['CastIron', 'HandWorn'], coll)
    wheel.location = WINCH
    return wheel


def build_shutter(coll):
    """The steel shutter: curved slats, a heavy bottom bar with its lip toward the hall. The lip has a drum-shaped
    arc dent, scraped bright, where drums' chimes have been slammed into it. Origin on the bottom edge."""
    bm = bmesh.new()
    sy0, sy1 = SHUTTER_Y
    pitch = 0.075
    bar_h = 0.09
    ny = 6
    ys = [sy0 + (sy1 - sy0) * j / ny for j in range(ny + 1)]
    zs = []
    z = bar_h
    while z < SHUTTER_H - 1e-6:
        for k in range(4):
            zs.append(z + pitch * k / 4)
        z += pitch
    zs.append(SHUTTER_H)

    def xc(zv, yv):
        t = ((zv - bar_h) / pitch) % 1.0
        bulge = -0.009 * math.sin(math.pi * t)
        wav = 0.004 * noise.noise(Vector((yv * 2.0, zv * 1.5, 0.3)))
        return bulge + wav
    th = SHUTTER_T / 2 - 0.009
    for side in (-1, 1):
        grid = [[bm.verts.new((xc(zv, yv) + side * th, yv, zv)) for yv in ys] for zv in zs]
        for i in range(len(zs) - 1):
            for j in range(ny):
                q = (grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j])
                bm.faces.new(q if side < 0 else q[::-1])
        if side < 0:
            front = grid
        else:
            back = grid
    for i in range(len(zs) - 1):                       # the slats' end edges
        for g0, g1, j in ((front, back, 0), (front, back, ny)):
            bm.faces.new((g0[i][j], g0[i + 1][j], g1[i + 1][j], g1[i][j]))
    for j in range(ny):                                 # the top edge
        bm.faces.new((front[-1][j], front[-1][j + 1], back[-1][j + 1], back[-1][j]))
    # End locks on alternate slats (they ride in the guides).
    k = 0
    for zz in zs[::4]:
        if k % 2 == 0:
            for y in (sy0 + 0.01, sy1 - 0.01):
                add_box(bm, (0, y, zz + pitch / 2), (0.036, 0.02, pitch * 0.7), mat=0)
        k += 1
    # The bottom bar: a web the slats sit in, the lip reaching toward the hall, its dent and the scrapes.
    cxd, cyd = DRUM_STOP_X - SHUTTER_X, DRUM_Y                  # the drum's centre, in the shutter's frame
    rc = DRUM_R - 0.006                                          # the chime's crest

    def dent(x, y):
        d = math.hypot(x - cxd, y - cyd)
        return DENT * math.exp(-((d - rc) / 0.016) ** 2) if x < -0.005 else 0.0
    add_box(bm, (0, (sy0 + sy1) / 2, bar_h / 2 + 0.01), (0.036, sy1 - sy0, bar_h - 0.02), mat=1)
    lx0, lx1 = -SHUTTER_LIP - 0.018, 0.018
    nx, nly = 8, 48
    xs = [lx0 + (lx1 - lx0) * i / nx for i in range(nx + 1)]
    ys2 = [sy0 + (sy1 - sy0) * j / nly for j in range(nly + 1)]
    lip_t = 0.02
    bot = [[bm.verts.new((x, y, dent(x, y))) for y in ys2] for x in xs]
    top = [[bm.verts.new((x, y, lip_t + 2.5 * dent(x, y) - (0.004 if x < lx0 + 0.02 else 0))) for y in ys2] for x in xs]

    def mi(x, y):
        d = math.hypot(x - cxd, y - cyd)
        return 2 if (x < -0.005 and abs(d - rc) < 0.035) else 1
    for i in range(nx):
        for j in range(nly):
            xm, ym = (xs[i] + xs[i + 1]) / 2, (ys2[j] + ys2[j + 1]) / 2
            f = bm.faces.new((bot[i][j], bot[i + 1][j], bot[i + 1][j + 1], bot[i][j + 1])[::-1])
            f.material_index = mi(xm, ym)
            f = bm.faces.new((top[i][j], top[i + 1][j], top[i + 1][j + 1], top[i][j + 1]))
            f.material_index = mi(xm, ym)
    for i in range(nx):
        for j in (0, nly):
            f = bm.faces.new((bot[i][j], bot[i + 1][j], top[i + 1][j], top[i][j]))
            f.material_index = 1
    for j in range(nly):
        for i in (0, nx):
            f = bm.faces.new((bot[i][j], bot[i][j + 1], top[i][j + 1], top[i][j]))
            f.material_index = 1
    ob = obj('RationShutter', bm, ['ShutterSteel', 'DepotSteel', 'HandWorn'], coll, sharp=60)
    ob.location = (SHUTTER_X, 0, 0)
    return ob


def build_drum(coll):
    """The ration drum: olive paint over steel, two rolling hoops and the chimes worn bright, a bright patch where
    hands push it (its hall side, toward the lane), dents, the stencil toward the camera. Origin at its base."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    R = DRUM_R
    body = R - 0.011
    prof = [(0.0, 0.004), (0.19, 0.004), (R - 0.016, 0.0), (R - 0.004, 0.004), (R, 0.014), (R - 0.002, 0.026),
            (body + 0.003, 0.034), (body, 0.042)]
    for zc in (0.2, 0.45):
        prof += [(body, zc - 0.03), (body + 0.003, zc - 0.02), (R - 0.002, zc - 0.011), (R, zc), (R - 0.002, zc + 0.011),
                 (body + 0.003, zc + 0.02), (body, zc + 0.03)]
    prof += [(body, DRUM_H - 0.04), (body + 0.003, DRUM_H - 0.032), (R - 0.002, DRUM_H - 0.022), (R, DRUM_H - 0.01),
             (R - 0.005, DRUM_H), (R - 0.014, DRUM_H - 0.002), (R - 0.02, DRUM_H - 0.018), (R - 0.03, DRUM_H - 0.022),
             (0.0, DRUM_H - 0.024)]
    rnd = random.Random(5004)
    patch = [rnd.uniform(-0.02, 0.02) for _ in range(64)]

    def mat_of(r, z, a):
        deg = math.degrees(a) % 360
        if r > R - 0.0045:
            return 1                                     # crowns of the hoops and chimes: bright
        if r >= body - 1e-4 and 0.24 < z < 0.41:
            k = int(deg / 360 * 64) % 64
            if 165 + patch[k] * 400 < deg < 245 + patch[k] * 400 and 0.26 + patch[(k + 7) % 64] < z < 0.4:
                return 1                                 # where hands push: on the hall side, toward the lane
        return 0
    rings, faces = lathe(bm, prof, 40, mat_of=mat_of)
    bm.normal_update()
    # Dents: noise along the body, and one big knock near the top on the far side.
    knock = Vector((math.cos(math.radians(40)) * body, math.sin(math.radians(40)) * body, 0.55))
    for ring, (r, z) in zip(rings, prof):
        if abs(r - body) > 1e-4 or z < 0.05 or z > DRUM_H - 0.05:
            continue
        for v in ring:
            n = Vector((v.co.x, v.co.y, 0)).normalized()
            amt = 0.003 * noise.noise(v.co * 9.0 + Vector((3.1, 1.7, 0.2)))
            dk = (v.co - knock).length
            amt -= 0.012 * math.exp(-(dk / 0.06) ** 2)
            v.co += n * amt
    # Bungs on the lid.
    for dx in (-0.1, 0.09):
        add_cyl(bm, (dx, 0.02, DRUM_H - 0.025), (dx, 0.02, DRUM_H - 0.012), 0.026, mat=3, seg=12)
        add_cyl(bm, (dx, 0.02, DRUM_H - 0.012), (dx, 0.02, DRUM_H - 0.006), 0.012, mat=3, seg=6)
    # The stencil, on a strip just proud of the body, facing the camera (-y): 250 to 300 degrees.
    a0, a1, z0, z1, n = math.radians(246), math.radians(298), 0.255, 0.395, 10
    for i in range(n):
        aa, ab = a0 + (a1 - a0) * i / n, a0 + (a1 - a0) * (i + 1) / n
        rr = body + 0.0016
        c = [(rr * math.cos(aa), rr * math.sin(aa), z0), (rr * math.cos(ab), rr * math.sin(ab), z0),
             (rr * math.cos(ab), rr * math.sin(ab), z1), (rr * math.cos(aa), rr * math.sin(aa), z1)]
        f = bm.faces.new([bm.verts.new(p) for p in c])
        f.material_index = 2
        for lp, t in zip(f.loops, ((i / n, 0), ((i + 1) / n, 0), ((i + 1) / n, 1), (i / n, 1))):
            lp[uv].uv = t
    ob = obj('RationDrum', bm, ['DrumOlive', 'HandWorn', 'DrumStencil', 'DepotSteel'], coll, sharp=50)
    face_out(ob, lambda p: Vector((p.x, p.y, 0)), {2})
    ob.location = (DRUM_START_X, DRUM_Y, 0)
    return ob


def build_guide(P, coll):
    """The drum's guide: a steel channel let into the floor under its centre line, a bump rail along the
    counter's foot behind it, the stop, the rust ring where drums have stood, and scrapes along the way."""
    st, pawl = P['DepotSteel'], P['HandWorn']
    gx1 = DRUM_STOP_X + 0.06
    for dy in (-0.045, 0.045):
        box(st, GUIDE_X0, gx1, DRUM_Y + dy - 0.022, DRUM_Y + dy + 0.022, 0.0, 0.004)
    box(P['Shaft'], GUIDE_X0, gx1, DRUM_Y - 0.023, DRUM_Y + 0.023, 0.0, 0.0015)
    for x in (GUIDE_X0 + 0.02, (GUIDE_X0 + gx1) / 2, gx1 - 0.02):
        for dy in (-0.05, 0.05):
            cyl(st, (x, DRUM_Y + dy, 0.004), (x, DRUM_Y + dy, 0.008), 0.008, seg=6)
    box(st, gx1 - 0.03, gx1, DRUM_Y - 0.02, DRUM_Y + 0.02, 0.0, 0.03)          # the stop lug, under the drum
    # The bump rail: angle iron on the counter's foot, scraped bright along its edge.
    ry = COUNTER_Y[0] - 0.035
    rbox(st, GUIDE_X0 - 0.05, PART[0] - 0.03, ry - 0.012, ry + 0.012, 0.09, 0.2, p=6, cuts=3)
    box(pawl, GUIDE_X0 + 0.2, PART[0] - 0.1, ry - 0.0135, ry - 0.011, 0.12, 0.17)
    for x in (GUIDE_X0 + 0.1, 55.4, 56.4):
        box(st, x - 0.015, x + 0.015, ry, COUNTER_Y[0], 0.1, 0.19)
    floor_decal('RationDrumRing', 'DrumRingMat', DRUM_STOP_X, DRUM_Y, 0.56, coll)


def build_lamp(P, coll):
    """The one practical: a strip tube in a green reflector, on chains from the ceiling, over the counter."""
    x, y, z = LAMP
    h = LAMP_LEN / 2
    g = P['DepotGreen']
    for s in (-1, 1):                                    # the reflector: two sloped leaves and a spine
        rbox(g, x - h - 0.04, x + h + 0.04, y + s * 0.07 - 0.04, y + s * 0.07 + 0.04, z + 0.04, z + 0.05, p=4, cuts=2,
             rot=None)
    rbox(g, x - h - 0.04, x + h + 0.04, y - 0.1, y + 0.1, z + 0.05, z + 0.08, p=5, cuts=3)
    for s in (-1, 1):
        rbox(g, x - h - 0.04, x + h + 0.04, y + s * 0.1 - 0.008, y + s * 0.1 + 0.008, z + 0.0, z + 0.07, p=4, cuts=2)
        rbox(P['DepotSteel'], x + s * h - 0.03, x + s * h + 0.01 * s, y - 0.025, y + 0.025, z - 0.015, z + 0.05, p=4, cuts=2)
    # Chains to the ceiling: links as little rings.
    for cx in (x - h + 0.2, x + h - 0.2):
        zz = z + 0.08
        for k in range(8):                               # a short chain, then a rod up into the dark
            add_torus(P['DepotSteel'], (cx, y, zz + 0.025), (1, 0, 0) if k % 2 else (0, 1, 0), 0.016, 0.004, mat=0, seg=8, rseg=4)
            zz += 0.04
        cyl(P['DepotSteel'], (cx, y, zz), (cx, y, CEIL - 0.42), 0.006, seg=6)
    # A conduit from the fitting along to the fascia.
    polyline(P['Cable'], catenary((x + h, y, z + 0.06), (HOUSING[0] - 0.06, 0.82, FASCIA_Z[1]), 0.15, 8), 0.007, 6)
    bm = bmesh.new()
    cyl(bm, (x - h + 0.02, y, z + 0.02), (x + h - 0.02, y, z + 0.02), 0.016, seg=12)
    lamp = obj('RationLamp', bm, ['RationLamp'], coll)
    return lamp


def build_maze(P):
    """The queue barriers, folded back and forth into a maze in front of the counter: three rows behind the lane,
    joined at alternate ends; one section pulled out and leaning, one fallen flat. A bedroll in the queue."""
    st = P['DepotSteel']

    def barrier(p0, p1, h=1.0, lean=0.0, flat=False):
        p0, p1 = Vector(p0), Vector(p1)
        d = (p1 - p0)
        L = d.length
        u = d.normalized()
        side = Vector((-u.y, u.x, 0))
        up = Vector((0, 0, 1))
        if flat:
            up, side = side, -up
        elif lean:
            up = (up * math.cos(lean) + side * math.sin(lean)).normalized()
        b = p0 + up * 0.08
        t = p0 + up * h
        polyline(st, [b, b + d], 0.016, 8)
        polyline(st, [t, t + d], 0.018, 8)
        for e in (p0, p1):
            polyline(st, [e + up * 0.02, e + up * (h + 0.02)], 0.018, 8)
            if not flat:
                foot = e + up * 0.01
                add_box(st, foot, (0.04, 0.5, 0.02), mat=0, rot=Matrix.Rotation(math.atan2(u.y, u.x), 4, 'Z'))
        n = int(L / 0.11)
        for k in range(1, n):
            q = p0 + d * (k / n)
            cyl(st, q + up * 0.08, q + up * h, 0.007, seg=5)
    rows = (0.62, 1.12, 1.62)
    barrier((50.45, rows[0], 0), (51.5, rows[0], 0))
    barrier((51.5, rows[0], 0), (52.55, rows[0] - 0.02, 0))
    barrier((50.15, rows[1], 0), (51.2, rows[1], 0))
    barrier((51.35, rows[1] + 0.05, 0), (52.35, rows[1] + 0.12, 0), lean=0.28)     # pulled out, leaning
    barrier((50.45, rows[2], 0), (51.5, rows[2], 0))
    barrier((51.6, 1.98, 0.0), (52.6, 2.02, 0.0), flat=True)                      # fallen flat
    barrier((52.6, rows[0], 0), (52.6, rows[1], 0), h=1.0)
    barrier((50.12, rows[1], 0), (50.12, rows[2], 0), h=1.0)


def bedroll(P, c, length, along_x=True, r=0.09, key='ToyFabric', strap='Rubber', seed=0.0):
    c = Vector(c)
    d = Vector((length / 2, 0, 0)) if along_x else Vector((0, length / 2, 0))
    rot = None if along_x else Matrix.Rotation(math.pi / 2, 4, 'Z')
    rounded_box((length, 2 * r * 1.15, 2 * r * 0.85), c + Vector((0, 0, r * 0.85)), p=2.6, cuts=6,
                dents=((0.008, 6.0), (0.003, 18.0)), seed=seed, bm=P[key], mat=0, rot=rot)
    for s in (-0.3, 0.3):
        q = c + d * s * 2 + Vector((0, 0, r * 0.85))
        add_torus(P[strap], q, d.normalized(), r * 1.02, 0.008, mat=0, seg=14, rseg=4)


def cot(P, cx, cy, along_x=True, length=1.85, width=0.68, h=0.4, blanket=True, seed=0.0, small=False):
    """A folding camp cot: two side rails, canvas sagging between, X legs; a blanket and a pillow."""
    rnd = random.Random(int(seed * 100) + 9)
    st = P['DepotSteel']
    L, W = length / 2, width / 2

    def T(x, y, z):
        return Vector((cx + x, cy + y, z)) if along_x else Vector((cx + y, cy + x, z))
    for s in (-1, 1):
        cyl(st, T(-L, s * W, h), T(L, s * W, h), 0.016, seg=8)
    for x in (-L + 0.08, 0.0, L - 0.08):
        cyl(st, T(x - 0.18, -W, 0.01), T(x + 0.18, -W, h - 0.01), 0.011, seg=6)
        cyl(st, T(x + 0.18, -W, 0.01), T(x - 0.18, -W, h - 0.01), 0.011, seg=6)
        cyl(st, T(x - 0.18, W, 0.01), T(x + 0.18, W, h - 0.01), 0.011, seg=6)
        cyl(st, T(x + 0.18, W, 0.01), T(x - 0.18, W, h - 0.01), 0.011, seg=6)
        cyl(st, T(x, -W, h * 0.5), T(x, W, h * 0.5), 0.008, seg=6)
    for x in (-L, L):
        cyl(st, T(x, -W, h), T(x, W, h), 0.014, seg=8)
    # Canvas: a sagging sheet with thickness.
    cv = P['CotCanvas']
    nx, ny = 12, 5
    grid = {}
    for side, dz in ((0, 0.0), (1, -0.006)):
        for i in range(nx + 1):
            for j in range(ny + 1):
                x = -L + 2 * L * i / nx
                y = -W + 2 * W * j / ny
                sag = 0.05 * math.sin(math.pi * j / ny) * (0.6 + 0.4 * math.sin(math.pi * i / nx))
                grid[side, i, j] = cv.verts.new(T(x, y, h + 0.012 - sag + dz))
    for i in range(nx):
        for j in range(ny):
            cv.faces.new((grid[0, i, j], grid[0, i + 1, j], grid[0, i + 1, j + 1], grid[0, i, j + 1]))
            cv.faces.new((grid[1, i, j], grid[1, i, j + 1], grid[1, i + 1, j + 1], grid[1, i + 1, j]))
    rim = [(i, 0) for i in range(nx)] + [(nx, j) for j in range(ny)] + [(i, ny) for i in range(nx, 0, -1)] + \
          [(0, j) for j in range(ny, 0, -1)]
    for (i0, j0), (i1, j1) in zip(rim, rim[1:] + rim[:1]):       # close the sheet's edges: a solid the normals agree on
        cv.faces.new((grid[0, i0, j0], grid[1, i0, j0], grid[1, i1, j1], grid[0, i1, j1]))
    if blanket:
        rounded_box((length * (0.62 if not small else 0.7), width * 1.05, 0.06),
                    T(0.12 * length, 0.0, h - 0.0), p=2.4, cuts=8, dents=((0.014, 5.0), (0.004, 16.0)), seed=seed,
                    bm=P['ToyFabric' if rnd.random() < 0.6 else 'CotCanvas'], mat=0,
                    rot=None if along_x else Matrix.Rotation(math.pi / 2, 4, 'Z'))
        rounded_box((0.34 if not small else 0.24, 0.22 if not small else 0.16, 0.08), T(-L + 0.24, 0.0, h + 0.02), p=2.5, cuts=6,
                    dents=((0.006, 8.0),), seed=seed + 1, bm=P['LetterPaper'], mat=0,
                    rot=None if along_x else Matrix.Rotation(math.pi / 2, 4, 'Z'))


def table(P, cx, cy, length=1.7, depth=0.7, h=0.74):
    st = P['DepotSteel']
    rbox(P['CrateWood'], cx - length / 2, cx + length / 2, cy - depth / 2, cy + depth / 2, h - 0.04, h, p=6, cuts=4,
         dents=((0.0015, 8.0),), seed=cx)
    for x in (cx - length / 2 + 0.15, cx + length / 2 - 0.15):
        for s in (-1, 1):
            cyl(st, (x, cy + s * (depth / 2 - 0.06), h - 0.04), (x, cy + s * (depth / 2 - 0.16), 0.0), 0.018, seg=8)
        cyl(st, (x, cy - depth / 2 + 0.11, 0.25), (x, cy + depth / 2 - 0.11, 0.25), 0.012, seg=6)
    cyl(st, (cx - length / 2 + 0.15, cy, 0.25), (cx + length / 2 - 0.15, cy, 0.25), 0.012, seg=6)


def bench(P, cx, cy, length=1.5, h=0.44, upturned_on=None, tipped=False):
    st = P['DepotSteel']
    w = 0.26
    if upturned_on is not None:                           # upside down on a table, legs in the air
        top = upturned_on
        rbox(P['CrateWood'], cx - length / 2, cx + length / 2, cy - w / 2, cy + w / 2, top, top + 0.04, p=6, cuts=3)
        for x in (cx - length / 2 + 0.12, cx + length / 2 - 0.12):
            for s in (-1, 1):
                cyl(st, (x, cy + s * 0.08, top + 0.04), (x, cy + s * 0.1, top + 0.04 + h - 0.04), 0.015, seg=6)
        return
    if tipped:                                            # on its side
        rbox(P['CrateWood'], cx - length / 2, cx + length / 2, cy - 0.02, cy + 0.02, 0.0, w, p=6, cuts=3)
        for x in (cx - length / 2 + 0.12, cx + length / 2 - 0.12):
            for s in (-1, 1):
                cyl(st, (x, cy + 0.02, w / 2 + s * 0.08), (x, cy + h - 0.02, w / 2 + s * 0.1), 0.015, seg=6)
        return
    rbox(P['CrateWood'], cx - length / 2, cx + length / 2, cy - w / 2, cy + w / 2, h - 0.04, h, p=6, cuts=3)
    for x in (cx - length / 2 + 0.12, cx + length / 2 - 0.12):
        for s in (-1, 1):
            cyl(st, (x, cy + s * 0.08, h - 0.04), (x, cy + s * 0.1, 0.0), 0.015, seg=6)


def build_canteen(P, coll):
    """Tables with cots between them, bedrolls on the floor, on a table and in the queue; a washing line; the
    sky on the back wall; the notice and the tallies on the second column; a few dark things in the foreground."""
    rnd = random.Random(5006)
    # Tables and benches.
    table(P, 49.2, 2.4)
    table(P, 52.0, 2.4)
    bench(P, 49.2, 1.92)
    bench(P, 52.0, 2.4, upturned_on=0.74)
    bench(P, 52.1, 2.95, tipped=True)
    bedroll(P, (49.1, 2.42, 0.74), 1.4, True, r=0.1, key='ToyFabric', seed=1.0)          # someone slept on the table
    # Cots: against the back wall, and a small one between the tables.
    cot(P, 49.25, 3.15, True, seed=0.3)
    cot(P, 52.0, 3.22, True, seed=0.7)
    cot(P, 50.62, 2.62, False, length=1.3, width=0.55, h=0.32, seed=1.3, small=True)
    # Bedrolls on the floor: by the door, in the queue between the barriers, under the second table.
    bedroll(P, (48.45, 1.25, 0.0), 1.2, False, r=0.085, key='CotCanvas', seed=2.0)
    bedroll(P, (48.75, 1.25, 0.0), 1.15, False, r=0.08, key='ToyFabric', seed=2.4)
    bedroll(P, (51.2, 0.87, 0.0), 1.1, True, r=0.08, key='ToyFabric', seed=3.0)
    rounded_box((0.8, 0.5, 0.05), Vector((52.0, 2.4, 0.03)), p=2.4, cuts=8, dents=((0.01, 6.0),), seed=4.0,
                bm=P['CotCanvas'], mat=0)
    # A kettle on a camp stove on the first table; a bucket; tin cups.
    st = P['BareMetal']
    cyl(P['CastIron'], (48.75, 2.3, 0.74), (48.75, 2.3, 0.8), 0.09, seg=16)
    lathe(st, [(0.0, 0.8), (0.085, 0.8), (0.09, 0.84), (0.08, 0.9), (0.05, 0.93), (0.02, 0.94), (0.0, 0.94)], 16,
          center=(48.75, 2.3, 0.0))
    cyl(st, (48.83, 2.3, 0.86), (48.9, 2.3, 0.9), 0.008, seg=6)
    add_torus(st, (48.75, 2.3, 0.97), (1, 0, 0), 0.05, 0.005, mat=0, seg=12, rseg=4)
    lathe(st, [(0.0, 0.0), (0.12, 0.0), (0.15, 0.26), (0.142, 0.26), (0.112, 0.008), (0.0, 0.008)], 18,
          center=(50.85, 1.45, 0.0))
    for x, y in ((49.6, 2.5), (52.4, 2.25), (51.9, 2.6)):
        cyl(st, (x, y, 0.74), (x, y, 0.82), 0.035, seg=12)
    # The washing line, from the shrine's column to the end wall: a small shirt, socks, a towel.
    a, b = Vector((COLUMNS[0][0] - COL_W / 2, 1.42, 1.9)), Vector((ENTRY[1], 1.7, 1.98))
    line = catenary(a, b, 0.09, 10)
    polyline(P['Cable'], line, 0.003, 4)

    def cloth(t, w, h, key, seed, shirt=False):
        k = min(int(t * 10), 9)
        p = line[k].lerp(line[k + 1], t * 10 - k)
        rot = Matrix.Rotation(math.atan2(b.y - a.y, b.x - a.x), 4, 'Z')
        rounded_box((w, 0.014, h), p - Vector((0, 0, h / 2 - 0.01)), p=9, cuts=6, dents=((0.006, 9.0),), seed=seed,
                    bm=P[key], mat=0, rot=rot)
        if shirt:                                        # sleeves
            rounded_box((w * 1.7, 0.016, h * 0.28), p - Vector((0, 0, h * 0.16)), p=9, cuts=5, dents=((0.004, 9.0),),
                        seed=seed + 0.5, bm=P[key], mat=0, rot=rot)
    cloth(0.25, 0.22, 0.3, 'BedroomDado', 1.0, shirt=True)
    cloth(0.48, 0.08, 0.16, 'CotCanvas', 2.0)
    cloth(0.56, 0.08, 0.15, 'CotCanvas', 2.5)
    cloth(0.75, 0.3, 0.4, 'ToyFabric', 3.0)
    # The painted sky on the back wall, above the cots.
    decal('RationMural', 'SkyMuralMat', 48.45, 53.05, 1.3, 3.6, BACK_Y - 0.025, coll)
    # A vent in the ceiling over the cots (some light still falls through it).
    vx, vy = 50.8, 2.7
    rbox(P['DepotSteel'], vx - 0.4, vx + 0.4, vy - 0.4, vy + 0.4, CEIL - 0.06, CEIL - 0.01, p=5, cuts=3)
    for k in range(-3, 4):
        box(P['SectionCap'], vx + k * 0.1 - 0.02, vx + k * 0.1 + 0.02, vy - 0.36, vy + 0.36, CEIL - 0.062, CEIL - 0.058)
    # The grade notice and the tally marks, on the second column.
    cx, cy = COLUMNS[1]
    face = cy - COL_W / 2 - 0.016
    decal('RationGradeNotice', 'GradeNoticeMat', cx - 0.15, cx + 0.15, 1.02, 1.45, face, coll, tilt=0.03)
    decal('RationTally', 'ChalkTally', cx - 0.16, cx + 0.16, 0.24, 0.72, face - 0.001, coll)
    for x, z in ((cx - 0.13, 1.42), (cx + 0.13, 1.43)):
        cyl(P['Brass'], (x, face - 0.004, z), (x, face + 0.004, z), 0.006, seg=6)
    # The foreground: low, dark, out of the lane.
    # Litter: paper scraps, a ration card, wrappers, on the floor among the cots and along the queue.
    lit = P['LetterPaper']
    for _ in range(26):
        x, y = rnd.uniform(48.3, 53.0), rnd.uniform(0.45, 3.4)
        if abs(y - 0.0) < 0.4:
            continue
        add_box(lit, (x, y, 0.001), (rnd.uniform(0.05, 0.14), rnd.uniform(0.04, 0.1), 0.002), mat=0,
                rot=Matrix.Rotation(rnd.uniform(0, math.pi), 4, 'Z'))


def build_shrine(P, coll):
    """On the first column, beside the lane: names and photographs pinned up, a shelf of candle stubs, more on the
    floor, wax run down everything, a tin of paper flowers, a folded paper bird. Four candles still burn."""
    cx, cy = COLUMNS[0]
    face = cy - COL_W / 2
    rnd = random.Random(5007)
    decal('RationShrineNames', 'ShrineNamesMat', cx - 0.17, cx + 0.17, 0.62, 1.16, face - 0.012, coll)
    # The shelf on two brackets.
    rbox(P['CrateWood'], cx - 0.24, cx + 0.24, face - 0.14, face, 0.5, 0.53, p=6, cuts=3)
    for x in (cx - 0.18, cx + 0.18):
        add_box(P['DepotSteel'], (x, face - 0.05, 0.47), (0.015, 0.1, 0.06), mat=0)
    wax = P['CandleWax']
    flames = []
    spots = [(cx - 0.18, face - 0.07, 0.53), (cx - 0.08, face - 0.05, 0.53), (cx + 0.02, face - 0.09, 0.53),
             (cx + 0.12, face - 0.06, 0.53), (cx + 0.2, face - 0.08, 0.53)]
    spots += [(cx - 0.22, face - 0.22, 0.0), (cx - 0.1, face - 0.3, 0.0), (cx + 0.02, face - 0.2, 0.0),
              (cx + 0.14, face - 0.28, 0.0), (cx + 0.24, face - 0.18, 0.0), (cx - 0.02, face - 0.38, 0.0),
              (cx + 0.3, face - 0.34, 0.0)]
    lit = {1, 3, 7, 9, 11}
    for k, (x, y, z) in enumerate(spots):
        r = rnd.uniform(0.012, 0.022)
        hgt = rnd.uniform(0.015, 0.09)
        cyl(wax, (x, y, z), (x, y, z + hgt), r, r * 0.92, seg=10)
        cyl(wax, (x, y, z), (x, y, z + 0.004), r * 2.2, r * 1.6, seg=12)          # the pool of melted wax
        cyl(P['Rubber'], (x, y, z + hgt), (x, y, z + hgt + 0.012), 0.0018, seg=4)  # the wick
        if k in lit:
            flames.append((x, y, z + hgt + 0.012))
    for x in (cx - 0.08, cx + 0.12):                         # wax run over the shelf's edge
        cyl(wax, (x, face - 0.14, 0.53), (x + 0.004, face - 0.142, 0.47), 0.006, 0.003, seg=6)
    # The tin of paper flowers, and the folded paper bird.
    t = Vector((cx + 0.32, face - 0.12, 0.0))
    cyl(P['BareMetal'], t, t + Vector((0, 0, 0.11)), 0.04, seg=14)
    for k in range(5):
        a = 2 * math.pi * k / 5
        tip = t + Vector((0.05 * math.cos(a), 0.04 * math.sin(a), 0.2 + 0.03 * math.sin(k * 2.0)))
        cyl(P['DepotGreen'], t + Vector((0, 0, 0.1)), tip, 0.003, seg=4)
        add_sphere(P[('LetterPaper', 'ToyPatch', 'ChildPaint')[k % 3]], tip, 0.024, mat=0, seg=8, scale=(1, 1, 0.6))
    bp = Vector((cx - 0.02, face - 0.08, 0.53))
    bird = P['LetterPaper']
    for s in (-1, 1):
        f = [bird.verts.new(bp + Vector(p)) for p in ((-0.05, 0, 0.0), (0.05, 0, 0.0), (0.0, s * 0.045, 0.045))]
        bird.faces.new(f)
    f = [bird.verts.new(bp + Vector(p)) for p in ((0.04, 0, 0.0), (0.075, 0, 0.05), (0.06, 0, 0.0))]
    bird.faces.new(f)
    # The flames: small teardrops, one object the game can flicker.
    bm = bmesh.new()
    for x, y, z in flames:
        add_sphere(bm, (x, y, z + 0.012), 0.007, mat=0, seg=8, scale=(1, 1, 2.2))
    CANDLE_FLAMES[:] = flames
    return obj('RationCandles', bm, ['RationCandle'], coll)


def build_drawing(P, coll):
    """Mara's crayon drawing, taped to the counter's front beside the winch, in the lamp's light."""
    x0, x1, z0, z1 = 53.86, 54.2, 0.47, 0.725
    decal('RationDrawing', 'CrayonDrawingMat', x0, x1, z0, z1, COUNTER_Y[0] - 0.003, coll, tilt=-0.04)


def build_kitchen(P):
    """Stripped: a steel prep table, two great empty pots, bare shelves, a ladle on its rail, empty crates, a
    slumped sack, a dead bulb."""
    st, bare = P['DepotSteel'], P['BareMetal']
    k1 = PART[1]
    tx0, tx1, ty0, ty1, th = k1 + 0.25, 58.9, KITCHEN_BACK - 0.62, KITCHEN_BACK - 0.03, 0.88
    rbox(bare, tx0, tx1, ty0, ty1, th - 0.035, th, p=6, cuts=4)
    for x in (tx0 + 0.05, tx1 - 0.05):
        for y in (ty0 + 0.05, ty1 - 0.05):
            cyl(st, (x, y, 0), (x, y, th - 0.03), 0.02, seg=8)
    rbox(st, tx0 + 0.04, tx1 - 0.04, ty0 + 0.04, ty1 - 0.04, 0.2, 0.22, p=5, cuts=2)
    for x, r, h in ((57.55, 0.19, 0.32), (58.3, 0.16, 0.26)):
        lathe(bare, [(0.0, th), (r - 0.02, th), (r, th + 0.02), (r, th + h), (r + 0.012, th + h + 0.01), (r - 0.008, th + h + 0.008),
                     (r - 0.012, th + 0.03), (0.0, th + 0.03)], 22, center=(x, (ty0 + ty1) / 2, 0.0))
        for s in (-1, 1):
            add_torus(st, (x + s * (r + 0.025), (ty0 + ty1) / 2, th + h - 0.05), (0, 1, 0), 0.03, 0.007, mat=0, seg=10, rseg=4)
    for z in (1.4, 1.8):
        rbox(st, k1 + 0.2, 59.4, KITCHEN_BACK - 0.3, KITCHEN_BACK, z - 0.015, z + 0.015, p=5, cuts=2)
        for x in (k1 + 0.4, 58.2, 59.2):
            box(st, x - 0.01, x + 0.01, KITCHEN_BACK - 0.26, KITCHEN_BACK, z - 0.14, z - 0.015)
    cyl(bare, (58.6, KITCHEN_BACK - 0.15, 1.415), (58.6, KITCHEN_BACK - 0.15, 1.52), 0.04, seg=12)
    cyl(st, (k1 + 0.3, KITCHEN_BACK - 0.05, 1.6), (58.0, KITCHEN_BACK - 0.05, 1.6), 0.008, seg=6)
    lp = Vector((57.3, KITCHEN_BACK - 0.06, 1.6))
    cyl(bare, lp, lp - Vector((0, 0.01, 0.34)), 0.006, seg=6)
    lathe(bare, [(0.0, -0.04), (0.04, -0.02), (0.045, 0.0), (0.0, 0.0)], 12, center=lp - Vector((0, 0.01, 0.36)))
    # Empty crates stacked by the way out; a sack slumped against them.
    rnd = random.Random(5008)
    for k, (x, y, z) in enumerate(((59.25, 1.35, 0.0), (59.3, 1.35, 0.36), (58.75, 1.45, 0.0))):
        rbox(P['CrateWood'], x - 0.24, x + 0.24, y - 0.2, y + 0.2, z, z + 0.34, p=7, cuts=3,
             dents=((0.004, 7.0),), seed=k, rot=Matrix.Rotation(rnd.uniform(-0.08, 0.08), 4, 'Z'))
    rounded_box((0.36, 0.26, 0.42), Vector((58.95, 1.0, 0.18)), p=2.2, cuts=8, dents=((0.02, 5.0), (0.006, 14.0)), seed=8,
                bm=P['ParcelBrown'], mat=0)
    # A dead bulb on its flex.
    cyl(P['Cable'], (58.0, 0.5, KITCHEN_CEIL), (58.0, 0.5, 2.02), 0.004, seg=4)
    cyl(st, (58.0, 0.5, 2.03), (58.0, 0.5, 1.98), 0.018, seg=10)
    add_sphere(P['DeadBulb'], (58.0, 0.5, 1.95), 0.035, mat=0, seg=12)


# --------------------------------------------------------------------------

def build_set(dl01, m, coll):
    tex.make_textures()
    P = Parts()
    build_shell(P)
    build_counter(P, coll)
    build_winch(P, coll)
    build_shutter(coll)
    build_drum(coll)
    build_guide(P, coll)
    build_lamp(P, coll)
    build_maze(P)
    build_canteen(P, coll)
    build_shrine(P, coll)
    build_drawing(P, coll)
    build_kitchen(P)
    P.emit(coll)


def add_clips(dl01, arm):
    """The winch's wheel sits where DL-01's crank wheel does relative to D-17 (0.2 in front of him, axle at 0.45,
    radius 0.15) and turns 60 degrees a stroke: the existing Crank clip fits, so no new clip."""
    pass
