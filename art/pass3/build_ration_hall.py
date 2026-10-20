"""Chapter 1, pass 3 (docs/chapter1_pass3_plan.md): DL-05 The Ration Hall. Built in FINAL world x, after
insert_scenes() has opened the gap between the Racks' service passage (ends x 47.9) and the scanner corridor of
the return line (starts x 59.9).

The depot workers' canteen and ration counter, the bottom of the refuge, where the labour grades queued and where
families slept when ring C flooded, and where they starved when the rations ran out (pass 4, the famine). Left to right:

    x 47.9 to 48.1   the hall's end wall, with a doorway the size of the Racks' passage (y -0.9 to 0.67, 2.4 high)
    x 48.1 to 53.2   the canteen, its floor rows of the dead under sheets, ration tags on their toes (two on the cots):
                     the shrine on the first column (49.65), the painted sky on the back wall, the grade notice and the
                     tally marks on the second column; one shrouded body on the lane's back edge, a rope on its ankles
    x 53.2 to 56.6   the ration counter behind the lane, hacked through at 55.92 to 56.27; NO RATIONS / GRADE 4 painted
                     on the wall over it; the WEIGH-IN post at its left end (53.68: the dial, its needle and the SERVED
                     flag); the crayon drawing on the counter's front; the drum (53.45); the weighbridge plate let into
                     the floor in front of the hatch (53.85 to 55.75)
    x 56.6 to 56.84  the kitchen wall, with the serving hatch (y -0.6 to 0.77, 1.30 high) and its steel shutter
    x 56.84 to 59.9  the kitchen, stripped, low (2.4), running into the scanner corridor's section at 59.9

The puzzle (pass 4, docs/chapter1_pass4_plan.md section 4): the hatch opens only while the plate reads a person. D-17
alone reads UNDER; the drum slams the needle to OVER; one of the dead, dragged onto the plate, reads PERSON, and the
hatch winds up and stays (SERVED). The winch is gone. The shutter's lip still carries the drum dent from pass 3.

Driven by the game (game/undelivered/index.html):
    RationShutter      origin on its bottom edge (the lip's underside) at (SHUTTER_X, 0, 0); moves in z (game y)
    RationDrum         the pushable drum; origin at its base centre (DRUM_START_X, DRUM_Y, 0); moves in x
    RationScalePlate   the weighbridge plate; origin at its top centre (PLATE_C); dips PLATE_DIP in z (game y)
    RationScaleNeedle  the dial's needle; origin at the dial's centre (DIAL_C), modelled pointing at zero; turns about
                       y (game z): see NEEDLE_SWEEP (clockwise as the camera sees it, so game z rotation = -sweep)
    RationServedFlag   the SERVED flag on the dial; origin on its hinge (FLAG_HINGE), modelled up (hidden); drops by
                       turning FLAG_THROW about x (game x)
    RationBody         the shrouded body to drag; origin at its centre on the floor (BODY_START_X, BODY_Y, 0), lying
                       along x, its feet to +x with the drag toggle at BODY_LOOP (x offset, height); moves in x
    RationLamp         the counter's strip tube (emissive; flickers)
    RationCandles      the shrine's candle flames (emissive)

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
DRUM_START_X = 53.45                 # left of the plate, in front of the counter's left end
DRUM_STOP_X = SHUTTER_X - SHUTTER_T / 2 - DRUM_R - 0.02      # 56.22: where pass 3's drums were jammed under the lip (the dent)
DENT = 0.01                          # the lip's dent, where drums' chimes have bitten
SHUTTER_REST = DRUM_H - DENT

# The weigh-in (pass 4): a goods weighbridge let into the floor in front of the hatch.
PLATE = (53.85, 55.75)               # x0, x1 of the plate
PLATE_Y = (-0.30, 0.64)              # y0, y1 (game z +0.30 to -0.64): the lane and the drag line behind it
PLATE_TOP = 0.004                    # flush (4 mm proud, as the bay plate)
PLATE_DIP = 0.01                     # how far it sinks under a load
PLATE_C = ((PLATE[0] + PLATE[1]) / 2, (PLATE_Y[0] + PLATE_Y[1]) / 2, PLATE_TOP)   # (54.80, 0.17, 0.004): its origin
PIT = (PLATE[0] - 0.02, PLATE[1] + 0.02, PLATE_Y[0] - 0.02, PLATE_Y[1] + 0.02, -0.05)  # x0, x1, y0, y1, floor
DRUM_PLATE_X = PLATE_C[0]            # 54.80: the drum squarely on the plate
DRUM_PARK_X = 56.02                  # pushed on past the plate, into the corner by the hatch (rim 1.5 cm short of the lip)
POST = (53.68, 0.645)                # the WEIGH-IN post: x, y (behind the drag line, in front of the counter)
DIAL_C = (53.68, 0.494, 1.25)        # the dial's centre (its face toward -y): the needle's pivot
DIAL_R = 0.236
NEEDLE_LEN = 0.205
# Needle sweeps, degrees clockwise from zero (as the camera sees it). The dial's bands: UNDER 0 to 110, PERSON 110 to
# 170, OVER 170 to 240 (the stop). Blender: rotation_euler.y = +sweep; the game (glTF): rotation.z = -sweep.
NEEDLE_SWEEP = {'D-17': 28.0, 'PERSON': 140.0, 'OVER': 236.0}
FLAG_HINGE = (53.68, 0.50, 1.64)     # the SERVED flag's hinge, over the dial
FLAG_THROW = -90.0                   # degrees about x (game x): up and hidden -> hanging in front, SERVED to the camera
BODY_Y = 0.35                        # the drag line (as the courier's in DL-04, game z -0.35)
BODY_START_X = 52.3
BODY_PLATE_X = PLATE_C[0]            # 54.80: fully on the plate from 54.675 to 54.925
HACK = (55.92, 56.27)                # where the counter has been hacked through

LAMP = (54.75, 0.25, 2.05)           # the strip tube's centre over the counter
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
    # Pass 4. The remains: one painted palette for every figure and shroud (DL-02's sorters too), one draw call each.
    'RemainsMat': lambda: _image_material('RemainsMat', tex.texture('remains_atlas.png'), 0.9),
    'WeighInMat': lambda: _image_material('WeighInMat', tex.texture('weighin.png'), 0.45),
    'NoRationsMat': lambda: _image_material('NoRationsMat', tex.texture('no_rations.png'), 0.95, alpha=True),
    # Made by other scenes' builders; the same names and values here when this one runs first or alone.
    'GaugeNeedle': lambda: simple_material('GaugeNeedle', (0.02, 0.018, 0.016), 0.4, metallic=0.3),
    'PlateSteel': lambda: worn_material('PlateSteel', base=(0.11, 0.115, 0.11), dirt=(0.06, 0.04, 0.025),
                                        chip=(0.2, 0.19, 0.17), rough=0.55, chip_rough=0.4, metallic=0.7),
    'SafetyYellow': lambda: worn_material('SafetyYellow', base=(0.55, 0.42, 0.06), dirt=(0.2, 0.16, 0.05),
                                          chip=(0.07, 0.068, 0.062), rough=0.8, chip_rough=0.9, metallic=0.0),
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
    # Pass 4: cut round the weighbridge's pit, so the plate can sink into it.
    bm = P['Concrete']
    px0, px1, py0, py1, pz = PIT
    box(bm, FLOOR_X[0], px0, -4.0, 3.8, -0.1, 0.0)
    box(bm, px1, FLOOR_X[1], -4.0, 3.8, -0.1, 0.0)
    box(bm, px0, px1, -4.0, py0, -0.1, 0.0)
    box(bm, px0, px1, py1, 3.8, -0.1, 0.0)
    box(bm, px0, px1, py0, py1, -0.1, pz)
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
    h0, h1 = HACK
    # Body and front panels (DepotGreen) with shadow gaps, a scuffed steel kick plate; all cut where the counter has
    # been hacked through (pass 4: someone took an axe to it, to get at the servery behind).
    for a, b in ((c0, h0), (h1, c1)):
        box(w, a, b, fy + 0.03, by, 0, COUNTER_TOP - 0.03)
        rbox(P['DepotSteel'], a, b, fy - 0.012, fy + 0.03, 0, 0.13, p=6, cuts=3)
        # The top: wood, its front edge rounded and worn where elbows leaned.
        rbox(P['CrateWood'], a - (0.03 if a == c0 else 0.0), b, fy - 0.05, by + 0.02, COUNTER_TOP - 0.035, COUNTER_TOP + 0.01,
             p=5, cuts=6, dents=((0.002, 9.0),), seed=3 + a)
    n = 6
    pw = (c1 - c0) / n
    for i in range(n):
        x0, x1 = c0 + i * pw + 0.012, c0 + (i + 1) * pw - 0.012
        for a, b in ((x0, min(x1, h0)), (max(x0, h1), x1)):
            if b - a > 0.05:
                rbox(P['DepotGreen'], a, b, fy, fy + 0.035, 0.14, COUNTER_TOP - 0.05, p=10, cuts=3,
                     dents=((0.0015, 6.0),), seed=i + a)
    build_hack(P)
    # The grille: bars up to the fascia, two serving slots cut through it at counter height.
    st = P['DepotSteel']
    slots = ((54.35, 54.75), (55.55, 55.95))
    x = c0 + 0.06
    while x < SHUTTER_X - 0.2:
        z0 = COUNTER_TOP + 0.01
        if any(a < x < b for a, b in slots):
            z0 = 1.24
        if h0 - 0.02 < x < h1 + 0.02:                          # over the hack: the bars cut and bent back
            cyl(st, (x, GRILLE_Y, FASCIA_Z[0]), (x, GRILLE_Y, 1.5), 0.008, seg=6)
            cyl(st, (x, GRILLE_Y, 1.5), (x + 0.05, GRILLE_Y + 0.22, 1.3), 0.008, seg=6)
        else:
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


def build_hack(P):
    """The counter hacked through between HACK[0] and HACK[1]: splintered ends to the top and the panels, the axe
    left in the cut, splinters and a broken panel on the floor. Through the gap: the empty servery."""
    rnd = random.Random(5041)
    h0, h1 = HACK
    fy, by = COUNTER_Y
    wood, green, st = P['CrateWood'], P['DepotGreen'], P['DepotSteel']
    for x, sgn in ((h0, 1), (h1, -1)):
        for k in range(7):                                     # splinters off the top's cut ends, into the gap
            y = rnd.uniform(fy - 0.04, by)
            z = COUNTER_TOP - rnd.uniform(0.0, 0.03)
            L = rnd.uniform(0.03, 0.12)
            add_wedge = d17.add_wedge
            add_wedge(wood, (x - sgn * 0.01, y, z), (x + sgn * L, y + rnd.uniform(-0.03, 0.03), z - rnd.uniform(0, 0.05)),
                      0.03, 0.004, 0.02, 0.003, (0, 1, 0), mat=0)
        for k in range(5):                                     # the panels' torn ends
            z = rnd.uniform(0.18, 0.85)
            L = rnd.uniform(0.03, 0.09)
            d17.add_wedge(green, (x - sgn * 0.01, fy + 0.017, z), (x + sgn * L, fy + 0.01 + rnd.uniform(-0.02, 0.01), z + rnd.uniform(-0.06, 0.06)),
                          0.08, 0.006, 0.03, 0.004, (0, 0, 1), mat=0)
    # The axe, its head bitten into the left cut's top edge, the haft up and back over the counter.
    hx, hy, hz = h0 + 0.015, fy + 0.18, COUNTER_TOP - 0.01
    d17.add_box(st, (hx, hy, hz), (0.05, 0.014, 0.1), mat=0, rot=Matrix.Rotation(-0.5, 4, 'Y'))
    d17.add_box(P['HandWorn'], (hx + 0.03, hy, hz - 0.035), (0.012, 0.015, 0.08), mat=0, rot=Matrix.Rotation(-0.5, 4, 'Y'))
    cyl(wood, (hx - 0.02, hy, hz + 0.03), (hx - 0.3, hy + 0.05, hz + 0.26), 0.016, seg=8)
    # On the floor at its foot and inside: a panel prised off, splinters, chips.
    rbox(green, h0 - 0.05, h1 + 0.02, fy - 0.07, fy - 0.035, 0.0, 0.012, p=8, cuts=2,
         rot=Matrix.Rotation(0.12, 4, 'Z'))
    for k in range(14):
        x = rnd.uniform(h0 - 0.15, h1 + 0.1)
        y = rnd.uniform(fy - 0.06, fy + 0.5)
        d17.add_box(wood, (x, y, 0.004), (rnd.uniform(0.03, 0.14), rnd.uniform(0.008, 0.02), 0.008), mat=0,
                    rot=Matrix.Rotation(rnd.uniform(0, math.pi), 4, 'Z'))


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


def build_drum_marks(P, coll):
    """Where drums have stood and been shoved: the bump rail along the counter's foot, scraped bright, and the rust
    ring in the corner by the hatch, where the drum ends up if it is pushed on past the plate."""
    st, pawl = P['DepotSteel'], P['HandWorn']
    ry = COUNTER_Y[0] - 0.035
    rbox(st, COUNTER[0] + 0.05, PART[0] - 0.03, ry - 0.012, ry + 0.012, 0.09, 0.2, p=6, cuts=3)
    box(pawl, COUNTER[0] + 0.3, PART[0] - 0.1, ry - 0.0135, ry - 0.011, 0.12, 0.17)
    for x in (COUNTER[0] + 0.15, 55.4, 56.4):
        box(st, x - 0.015, x + 0.015, ry, COUNTER_Y[0], 0.1, 0.19)
    floor_decal('RationDrumRing', 'DrumRingMat', DRUM_PARK_X, DRUM_Y, 0.5, coll)


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


def build_canteen(P, coll):
    """The cots, the stove, a washing line; the sky on the back wall; the notice and the tallies on the second
    column; litter on the floor. The dead are build_famine's."""
    rnd = random.Random(5006)
    # Pass 4: the tables and benches are gone (burned, or broken up for the stove); the floor is the dead's. The two
    # cots against the back wall stay, each with one of them on it (build_famine), their blankets taken for sheets.
    cot(P, 49.25, 3.15, True, blanket=False, seed=0.3)
    cot(P, 52.0, 3.22, True, blanket=False, seed=0.7)
    # The camp stove and its kettle on the floor between the cots, a bucket, tin cups.
    st = P['BareMetal']
    kx, ky = 50.62, 3.3
    cyl(P['CastIron'], (kx, ky, 0.0), (kx, ky, 0.06), 0.09, seg=16)
    lathe(st, [(0.0, 0.06), (0.085, 0.06), (0.09, 0.10), (0.08, 0.16), (0.05, 0.19), (0.02, 0.2), (0.0, 0.2)], 16,
          center=(kx, ky, 0.0))
    cyl(st, (kx + 0.08, ky, 0.12), (kx + 0.15, ky, 0.16), 0.008, seg=6)
    add_torus(st, (kx, ky, 0.23), (1, 0, 0), 0.05, 0.005, mat=0, seg=12, rseg=4)
    lathe(st, [(0.0, 0.0), (0.12, 0.0), (0.15, 0.26), (0.142, 0.26), (0.112, 0.008), (0.0, 0.008)], 18,
          center=(50.85, 3.0, 0.0))
    for x, y in ((50.4, 3.05), (50.75, 3.45)):
        cyl(st, (x, y, 0.0), (x, y, 0.08), 0.035, seg=12)
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
    """Mara's crayon drawing, taped to the counter's front by the WEIGH-IN post, in the lamp's light."""
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
# Pass 4: the remains (shared with art/pass4/build_story_depot.py), the famine, the weigh-in
# --------------------------------------------------------------------------

class Painted:
    """One mesh in one atlas material: each part takes its paint from a cell of the atlas (a UV rectangle).
    Closed parts get outward normals in isolation; open surfaces (sheets, cards) are wound by their builders."""
    def __init__(self, rect_of=tex.atlas_uv):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.rect_of = rect_of

    def add(self, cell, build, size=0.3, closed=True):
        """build(bm) adds geometry with the d17 primitives (mat=0); its faces are box-projected into `cell`, one
        texel patch `size` metres across."""
        tmp = bmesh.new()
        tmp.loops.layers.uv.new('UVMap')
        build(tmp)
        if closed and tmp.faces:
            bmesh.ops.recalc_face_normals(tmp, faces=tmp.faces[:])
        self._project(tmp, self.rect_of(cell), size)
        self._merge(tmp)

    def _project(self, tmp, rect, size):
        u0, v0, u1, v1 = rect
        mu, mv = (u1 - u0) * 0.06, (v1 - v0) * 0.06
        uvl = tmp.loops.layers.uv['UVMap']
        for f in tmp.faces:
            f.normal_update()
            n = f.normal
            ax = max(range(3), key=lambda k: abs(n[k]))
            i, j = [(1, 2), (0, 2), (0, 1)][ax]
            c = f.calc_center_median()
            off = (math.sin(c.x * 12.9 + c.y * 78.2 + c.z * 37.7) * 0.5 + 0.5) * 0.4
            for lp in f.loops:
                p = lp.vert.co
                a = min(0.98, max(0.02, 0.3 + off + (p[i] - c[i]) / size))
                b = min(0.98, max(0.02, 0.3 + off * 0.7 + (p[j] - c[j]) / size))
                lp[uvl].uv = (u0 + mu + (u1 - u0 - 2 * mu) * a, v0 + mv + (v1 - v0 - 2 * mv) * b)

    def _merge(self, tmp):
        me = bpy.data.meshes.new('_painted')
        tmp.to_mesh(me)
        tmp.free()
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    def quads(self, cell, quads, uvs=None):
        """Explicit quads (already wound to face out), UVs over the whole cell (or the given per-corner uvs)."""
        u0, v0, u1, v1 = self.rect_of(cell)
        tmp = bmesh.new()
        uvl = tmp.loops.layers.uv.new('UVMap')
        for q in quads:
            f = tmp.faces.new([tmp.verts.new(p) for p in q])
            for lp, (a, b) in zip(f.loops, uvs or ((0, 0), (1, 0), (1, 1), (0, 1))):
                lp[uvl].uv = (u0 + (u1 - u0) * a, v0 + (v1 - v0) * b)
        self._merge(tmp)

    def grid(self, cell, pts, nx, ny):
        """A sheet: pts[i][j] (i along u, j along v), wound so its face is +u x +v; UVs over the cell."""
        u0, v0, u1, v1 = self.rect_of(cell)
        tmp = bmesh.new()
        uvl = tmp.loops.layers.uv.new('UVMap')
        vs = [[tmp.verts.new(pts[i][j]) for j in range(ny + 1)] for i in range(nx + 1)]
        for i in range(nx):
            for j in range(ny):
                f = tmp.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
                for lp, (a, b) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
                    lp[uvl].uv = (u0 + (u1 - u0) * (0.02 + 0.96 * a / nx), v0 + (v1 - v0) * (0.02 + 0.96 * b / ny))
        self._merge(tmp)

    def transform(self, M):
        bmesh.ops.transform(self.bm, matrix=M, verts=self.bm.verts)

    def obj(self, name, matname, coll, sharp=40):
        """Write it out as is (no normal recalculation: the open parts are wound already)."""
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        me.materials.append(mat(matname))
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        me.set_sharp_from_angle(angle=math.radians(sharp))
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        return ob

    def mesh(self, name, matname, sharp=40):
        """The same, as mesh data only (for linked duplicates)."""
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        me.materials.append(mat(matname))
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        me.set_sharp_from_angle(angle=math.radians(sharp))
        return me


# --------------------------------------------------------------------------
# Pass 5 (docs/chapter1_pass5_plan.md): the dead are 76 years dead. Bones, and cloth rotted onto them, for the shrouds
# here and DL-02's sorters (art/pass4/build_story_depot.py). Low-key and stylised: dry dark-ivory bone, dark hollows
# for the eyes, nothing that reads as gore.
# --------------------------------------------------------------------------

def _perp(t):
    a = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
    return (a - t * a.dot(t)).normalized()


def sweep(bm, pts, radii, seg=6, caps=True, side=None, flat=1.0):
    """A tube along pts (rings carried along the path), per-point radii, capped with fans. flat < 1 squashes the
    section along `side` (kept perpendicular to the path)."""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    ts = [(pts[min(n - 1, i + 1)] - pts[max(0, i - 1)]).normalized() for i in range(n)]
    nrm = _perp(ts[0]) if side is None else (Vector(side) - ts[0] * Vector(side).dot(ts[0])).normalized()
    rings = []
    for i, (p, t) in enumerate(zip(pts, ts)):
        nrm = (nrm - t * nrm.dot(t)).normalized()
        bi = t.cross(nrm)
        r = radii[i] if hasattr(radii, '__len__') else radii
        rings.append([bm.verts.new(p + nrm * (r * flat * math.cos(2 * math.pi * k / seg)) + bi * (r * math.sin(2 * math.pi * k / seg)))
                      for k in range(seg)])
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    if caps:
        for ring, p in ((rings[0], pts[0]), (rings[-1], pts[-1])):
            c = bm.verts.new(p)
            for k in range(seg):
                bm.faces.new((c, ring[(k + 1) % seg], ring[k]))
    return rings


def ellipsoid(bm, c, M, radii, seg=8):
    """An ellipsoid at c, its axes the columns of the 3x3 M, with the given radii along them."""
    res = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(4, seg // 2), radius=1.0)
    T = Matrix.Translation(Vector(c)) @ M.to_4x4() @ Matrix.Diagonal((*radii, 1.0))
    bmesh.ops.transform(bm, matrix=T, verts=res['verts'])
    return res['verts']


def frame3(x, y_hint):
    """Columns (x, y, z): x along `x`, y as near `y_hint` as can be."""
    x = Vector(x).normalized()
    y = Vector(y_hint) - x * Vector(y_hint).dot(x)
    y = y.normalized() if y.length > 1e-6 else _perp(x)
    return Matrix((x, y, x.cross(y))).transposed()


def long_bone(bm, a, b, r, knob=1.55, seg=6):
    """A long bone: a shaft with its two ends swollen into joints."""
    a, b = Vector(a), Vector(b)
    ts = (0.0, 0.06, 0.2, 0.8, 0.94, 1.0)
    rs = (r * knob * 0.7, r * knob, r, r * 0.95, r * knob, r * knob * 0.7)
    return sweep(bm, [a.lerp(b, t) for t in ts], rs, seg=seg)


def skull(P, H, face, crown, s=1.0, jaw=0.22, cell='bone'):
    """A skull at H: the dome, the face, the eye sockets and the nose as dark hollows, the jaw dropped a little.
    `face` points out of the face, `crown` toward the top of the head."""
    F = frame3(face, crown)
    f, u = F.col[0], F.col[1]
    l = u.cross(f)
    M = Matrix((f, l, u)).transposed()                       # x: out of the face, y: its left, z: the crown

    def at(x, y, z):
        return Vector(H) + (f * x + l * y + u * z) * s
    R = lambda r: tuple(v * s for v in r)                     # noqa: E731
    P.add(cell, lambda bm: ellipsoid(bm, at(-0.015, 0, 0.025), M, R((0.092, 0.07, 0.075)), seg=12), size=0.12)
    P.add(cell, lambda bm: ellipsoid(bm, at(0.058, 0, -0.035), M, R((0.035, 0.048, 0.04)), seg=8), size=0.12)
    for sd in (1, -1):
        P.add(cell, lambda bm, sd=sd: ellipsoid(bm, at(0.052, sd * 0.05, -0.012), M, R((0.022, 0.018, 0.014)), seg=6), size=0.12)
        P.add('dark', lambda bm, sd=sd: ellipsoid(bm, at(0.071, sd * 0.027, 0.0), M, R((0.012, 0.019, 0.017)), seg=8))
    P.add('dark', lambda bm: ellipsoid(bm, at(0.088, 0, -0.03), M, R((0.008, 0.01, 0.014)), seg=6))
    P.add('dark', lambda bm: ellipsoid(bm, at(0.08, 0, -0.064), M, R((0.012, 0.03, 0.008)), seg=6))
    # The jaw: a U from under one ear round the chin to the other, hinged open by `jaw` radians.
    piv = Vector((-0.005, 0, -0.03))
    Rj = Matrix.Rotation(jaw, 3, 'Y')
    pts = [(-0.005, 0.05, -0.03), (0.0, 0.048, -0.075), (0.05, 0.036, -0.088), (0.085, 0.0, -0.086),
           (0.05, -0.036, -0.088), (0.0, -0.048, -0.075), (-0.005, -0.05, -0.03)]
    pts = [at(*(piv + Rj @ (Vector(p) - piv))) for p in pts]
    P.add(cell, lambda bm: sweep(bm, pts, [0.008 * s, 0.011 * s, 0.01 * s, 0.012 * s, 0.01 * s, 0.011 * s, 0.008 * s], seg=5), size=0.12)


def hand(P, W, hd, hn, s=1.0, curl=0.6, spread=1.0, cell='bone'):
    """A hand's bones from the wrist W: the carpals, five metacarpals with their fingers curled by `curl` (radians a
    joint) toward the palm. hd: toward the fingers; hn: out of the back of the hand."""
    M = frame3(hd, hn)                                       # x: fingers, y: back of the hand, z: across
    d, n, sd = M.col[0], M.col[1], M.col[2]
    W = Vector(W)
    P.add(cell, lambda bm: ellipsoid(bm, W + d * 0.022 * s, M, (0.022 * s, 0.011 * s, 0.026 * s), seg=6), size=0.1)
    for k in range(5):
        if k == 0:                                           # the thumb, off the side
            base = W + (d * 0.02 + sd * 0.022) * s
            dirn = (d * 0.7 + sd * 0.7 - n * 0.2).normalized()
            lens = (0.04, 0.03, 0.022)
        else:
            base = W + (d * 0.038 + sd * (0.0125 * (k - 2.5) + 0.006)) * s
            dirn = (d + sd * 0.12 * (k - 2.5) * spread).normalized()
            lens = (0.062, 0.035, 0.022, 0.017) if k in (2, 3) else (0.056, 0.03, 0.02, 0.015)
        pts = [base]
        dv = dirn
        for j, L in enumerate(lens):
            if j:
                dv = (Matrix.Rotation(curl, 3, sd) @ dv).normalized()
            pts.append(pts[-1] + dv * L * s)
        rs = [0.0055 * s] + [max(0.0035, 0.0062 - 0.0008 * j) * s for j in range(len(lens))]
        P.add(cell, lambda bm, pts=pts, rs=rs: sweep(bm, pts, rs, seg=4), size=0.1)


def foot(P, A, fd, up, s=1.0, curl=0.25, cell='bone'):
    """A foot's bones from the ankle A: the heel and the ankle bone, five metatarsals and their toes. fd: toward the
    toes; up: out of the top of the foot."""
    M = frame3(fd, up)                                       # x: toes, y: top of the foot, z: across
    d, n, sd = M.col[0], M.col[1], M.col[2]
    A = Vector(A)
    P.add(cell, lambda bm: ellipsoid(bm, A - (d * 0.03 + n * 0.028) * s, M, (0.04 * s, 0.026 * s, 0.022 * s), seg=8), size=0.1)
    P.add(cell, lambda bm: ellipsoid(bm, A + (d * 0.015 - n * 0.005) * s, M, (0.03 * s, 0.02 * s, 0.024 * s), seg=6), size=0.1)
    tips = []
    for k in range(5):
        base = A + (d * 0.05 + sd * (0.011 * (k - 2) - 0.004) - n * 0.008 * abs(k - 2)) * s
        dirn = (d + sd * 0.1 * (k - 2)).normalized()
        lens = (0.075 - 0.006 * k, 0.03 - 0.003 * k, 0.018)
        pts = [base]
        dv = dirn
        for j, L in enumerate(lens):
            if j:
                dv = (Matrix.Rotation(curl, 3, sd) @ dv).normalized()
            pts.append(pts[-1] + dv * L * s)
        r0 = (0.009 if k == 0 else 0.0065) * s
        P.add(cell, lambda bm, pts=pts, r0=r0: sweep(bm, pts, [r0, r0 * 0.85, r0 * 0.8, r0 * 0.65], seg=4), size=0.1)
        tips.append(pts[-1])
    return tips


def ribcage(P, top, bottom, lat, fwd, s=1.0, n=8, cell='bone', sternum=True):
    """The thoracic spine from `top` to `bottom` (the back of the chest) and its ribs: each pair arcs out and round to
    the front, the lower ones short (floating), the upper ones joined to a sternum."""
    top, bottom = Vector(top), Vector(bottom)
    down = (bottom - top).normalized()
    lat = (Vector(lat) - down * Vector(lat).dot(down)).normalized()
    fwd = Vector(fwd)
    fwd = (fwd - down * fwd.dot(down) - lat * fwd.dot(lat)).normalized()
    L = (bottom - top).length
    ends = []
    for i in range(n):
        u = (i + 0.5) / n
        S = top + (bottom - top) * (0.04 + 0.9 * u)
        a = (0.07 + 0.065 * math.sin(math.pi * (0.25 + 0.7 * u))) * s        # half width
        b = (0.15 + 0.05 * math.sin(math.pi * (0.2 + 0.6 * u))) * s          # depth to the front
        drop = (0.04 + 0.03 * u) * s * L / 0.3
        tmax = math.pi * (0.9 if i < n - 2 else 0.6)
        for side in (1, -1):
            pts = []
            for k in range(7):
                t = tmax * k / 6
                pts.append(S + lat * side * a * math.sin(t) + fwd * b * (1 - math.cos(t)) / 2 + down * drop * (1 - math.cos(t)) / 2)
            P.add(cell, lambda bm, pts=pts: sweep(bm, pts, [0.0085 * s] * 6 + [0.0065 * s], seg=4), size=0.15)
        if i == 0:
            ends.append(S + fwd * b + down * drop * 0.95)
        if i == n - 3:
            ends.append(S + fwd * b * 0.95 + down * drop)
    if sternum and len(ends) == 2:
        P.add(cell, lambda bm: sweep(bm, [ends[0], ends[0].lerp(ends[1], 0.5), ends[1]], [0.016 * s, 0.013 * s, 0.009 * s],
                                     seg=5, side=fwd, flat=0.45), size=0.15)
    return ends[0] if ends else top


def spine(P, pts, s=1.0, step=0.026, cell='bone'):
    """The spine as a column of vertebrae along pts: a tube swelling at each one."""
    pts = [Vector(p) for p in pts]
    path = []
    for a, b in zip(pts, pts[1:]):
        k = max(1, int((b - a).length / (step / 2)))
        path += [a.lerp(b, i / k) for i in range(k)]
    path.append(pts[-1])
    rs = [(0.019 if i % 2 else 0.013) * s for i in range(len(path))]
    P.add(cell, lambda bm: sweep(bm, path, rs, seg=6), size=0.15)


def pelvis(P, c, up, lat, fwd, s=1.0, cell='bone'):
    """The pelvis: two flared wings, the sacrum between them behind, the ring of the pubis in front."""
    c = Vector(c)
    M = frame3(fwd, lat)                                     # x: forward, y: left, z: up
    f, l, u = M.col[0], M.col[1], M.col[2]
    for sd in (1, -1):
        Mw = frame3(f * 0.6 + l * sd * 0.8, u)               # the wing's broad face turned forward and out
        P.add(cell, lambda bm, sd=sd, Mw=Mw: ellipsoid(bm, c + (l * sd * 0.085 + u * 0.04 - f * 0.01) * s, Mw,
                                                       (0.018 * s, 0.065 * s, 0.06 * s), seg=8), size=0.15)
    P.add(cell, lambda bm: ellipsoid(bm, c + (-f * 0.04 + u * 0.02) * s, M, (0.022 * s, 0.045 * s, 0.055 * s), seg=6), size=0.15)
    P.add(cell, lambda bm: add_torus(bm, c + (f * 0.035 - u * 0.02) * s, (u * 0.55 + f * 0.45).normalized(), 0.058 * s,
                                     0.013 * s, mat=0, seg=12, rseg=4), size=0.15)


def cloth(P, cell, pts, thick=0.0015):
    """A sheet of cloth both sides out (the game draws one side of a face): pts[i][j], i along u, j along v."""
    nx, ny = len(pts) - 1, len(pts[0]) - 1
    nrm = [[None] * (ny + 1) for _ in range(nx + 1)]
    for i in range(nx + 1):
        for j in range(ny + 1):
            du = pts[min(nx, i + 1)][j] - pts[max(0, i - 1)][j]
            dv = pts[i][min(ny, j + 1)] - pts[i][max(0, j - 1)]
            c = du.cross(dv)
            nrm[i][j] = c.normalized() if c.length > 1e-9 else Vector((0, 0, 1))
    P.grid(cell, [[pts[i][j] + nrm[i][j] * thick for j in range(ny + 1)] for i in range(nx + 1)], nx, ny)
    P.grid(cell, [[pts[i][j] - nrm[i][j] * thick for i in range(nx + 1)] for j in range(ny + 1)], ny, nx)


def rag_tube(P, cell, a, b, r, sag=0.0, seed=0.0, ragged=0.3, flat=1.0, seg=8, rows=3, side=None):
    """A sleeve or trouser leg rotted onto the bone from a to b: its underside hanging by `sag`, squashed by `flat`,
    its far end torn ragged (up to `ragged` of its length)."""
    a, b = Vector(a), Vector(b)
    t = (b - a).normalized()
    n0 = _perp(t) if side is None else (Vector(side) - t * Vector(side).dot(t)).normalized()
    b0 = t.cross(n0)
    L = (b - a).length
    rnd = random.Random(int(seed * 1000) + 17)
    tear = [ragged * L * rnd.random() for _ in range(seg)]
    pts = []
    for k in range(seg + 1):
        ang = 2 * math.pi * k / seg
        rad = n0 * math.cos(ang) * flat + b0 * math.sin(ang)
        col = []
        for i in range(rows + 1):
            v = i / rows
            p = a + t * (L - tear[k % seg]) * v + rad * r
            p.z -= sag * max(0.0, -rad.z) * math.sin(math.pi * min(1.0, v * 1.2 + 0.1))
            col.append(p)
        pts.append(col)
    cloth(P, cell, pts)


def rag_strip(P, cell, top, down, across, length, width, seed=0.0, rows=4):
    """A torn strip of cloth hanging from `top` along `down`, `width` wide along `across`, waving a little."""
    top, down, across = Vector(top), Vector(down).normalized(), Vector(across).normalized()
    out = down.cross(across)
    rnd = random.Random(int(seed * 1000) + 31)
    ph = rnd.uniform(0, 6.28)
    pts = []
    for i in range(2):
        col = []
        for j in range(rows + 1):
            v = j / rows
            w = width * (1 - 0.55 * v) * (i - 0.5)
            col.append(top + down * length * v + across * w + out * 0.012 * math.sin(ph + v * 5.0) * v)
        pts.append(col)
    cloth(P, cell, pts)


def _axes(xdir, ydir):
    """A 4x4 rotation whose local x runs along xdir and local y as near ydir as can be."""
    x = Vector(xdir).normalized()
    y = Vector(ydir) - x * Vector(ydir).dot(x)
    y = y.normalized() if y.length > 1e-6 else Vector((0, 0, 1)).cross(x).normalized()
    return Matrix((x, y, x.cross(y))).transposed().to_4x4()


def _cap_height(x, y, cap):
    """Top of a capsule (a, b, half-width, half-height) lying on the floor, at plan point (x, y); 0 outside."""
    (ax, ay, az), (bx, by, bz), rl, rv = cap
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 < 1e-9 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
    d = math.hypot(x - (ax + dx * t), y - (ay + dy * t))
    if d >= rl:
        return 0.0
    return az + (bz - az) * t + rv * math.sqrt(1.0 - (d / rl) ** 2)


# The dead under their sheets (pass 5: 76 years dead). Each shape: the skeleton's capsules under the sheet (a, b,
# plan half-width, height), the ribs' ridges (x0, x1, half-width, pitch, depth), where the sheet is sampled finely along
# x, the sheet's extent and rows across, how closely it has settled (the slope it tents at), and the bones left out of
# it: the feet (ankle, toward the toes, out of the top of the foot), a forearm and hand from under its edge.
_ARM_IN = [((-0.50, 0.20, 0.0), (-0.24, 0.21, 0.0), 0.024, 0.03), ((-0.25, 0.21, 0.0), (-0.23, 0.21, 0.0), 0.03, 0.04),
           ((-0.24, 0.21, 0.0), (0.0, 0.20, 0.0), 0.024, 0.026), ((0.0, 0.20, 0.0), (0.1, 0.19, 0.0), 0.04, 0.02)]
_ARM_OUT = [((-0.50, 0.20, 0.0), (-0.26, 0.25, 0.0), 0.024, 0.03), ((-0.27, 0.25, 0.0), (-0.25, 0.25, 0.0), 0.03, 0.04),
            ((-0.26, 0.25, 0.0), (-0.07, 0.35, 0.0), 0.024, 0.026)]


def _mirror(caps):
    return [((a[0], -a[1], a[2]), (b[0], -b[1], b[2]), rl, rv) for a, b, rl, rv in caps]


_ADULT = [((-0.72, 0.0, 0.0), (-0.66, 0.0, 0.0), 0.08, 0.15),                         # the skull, face up
          ((-0.60, 0.0, 0.0), (-0.54, 0.0, 0.0), 0.03, 0.035),                         # the jaw and the neck
          ((-0.53, 0.0, 0.0), (-0.45, 0.0, 0.0), 0.125, 0.11),                         # the rib cage
          ((-0.45, 0.0, 0.0), (-0.32, 0.0, 0.0), 0.15, 0.125),
          ((-0.31, 0.0, 0.0), (-0.12, 0.0, 0.0), 0.024, 0.035),                        # the spine: the sheet sags to it
          ((-0.10, 0.11, 0.0), (-0.02, 0.12, 0.0), 0.05, 0.085), ((-0.10, -0.11, 0.0), (-0.02, -0.12, 0.0), 0.05, 0.085),
          ((-0.10, 0.0, 0.0), (0.0, 0.0, 0.0), 0.04, 0.05), ((0.02, 0.0, 0.0), (0.05, 0.0, 0.0), 0.045, 0.06),  # pelvis
          ((0.03, 0.10, 0.0), (0.38, 0.09, 0.0), 0.024, 0.032), ((0.03, -0.10, 0.0), (0.38, -0.09, 0.0), 0.024, 0.032),
          ((0.38, 0.09, 0.0), (0.42, 0.09, 0.0), 0.035, 0.05), ((0.38, -0.09, 0.0), (0.42, -0.09, 0.0), 0.035, 0.05),
          ((0.42, 0.09, 0.0), (0.66, 0.09, 0.0), 0.024, 0.032), ((0.42, -0.09, 0.0), (0.66, -0.09, 0.0), 0.024, 0.032)]
_FEET = [((0.645, 0.095, 0.045), (0.25, 0.5, 0.83), (0.95, 0.2, -0.25)),
         ((0.645, -0.095, 0.045), (0.25, -0.5, 0.83), (0.95, -0.2, -0.25))]
_BOUND = [((0.645, 0.05, 0.05), (0.12, 0.16, 0.98), (0.99, 0.0, -0.12)),               # tied together, toes up
          ((0.645, -0.05, 0.05), (0.12, -0.16, 0.98), (0.99, 0.0, -0.12))]
SHROUDS = {
    'adult': dict(caps=_ADULT + _ARM_IN + _mirror(_ARM_IN), ribs=(-0.535, -0.31, 0.15, 0.042, 0.11),
                  fine=(-0.76, -0.27), sheet=(-0.84, 0.58, -0.29, 0.29, 14), settle=3.2,
                  feet=_FEET, shins=0.09, hand=None, length=1.65),
    'curled': dict(caps=[((-0.50, 0.06, 0.0), (-0.47, 0.06, 0.0), 0.085, 0.14),             # on its side, knees drawn up
                         ((-0.42, 0.04, 0.0), (-0.36, 0.03, 0.0), 0.03, 0.05),
                         ((-0.34, 0.03, 0.0), (-0.08, 0.05, 0.0), 0.10, 0.2),
                         ((-0.06, 0.08, 0.0), (0.04, 0.08, 0.0), 0.03, 0.06),
                         ((0.04, 0.04, 0.0), (0.12, 0.0, 0.0), 0.09, 0.17),
                         ((0.10, 0.0, 0.08), (0.30, -0.26, 0.08), 0.035, 0.05),
                         ((0.30, -0.26, 0.06), (0.32, -0.28, 0.06), 0.045, 0.06),
                         ((0.30, -0.26, 0.05), (0.46, -0.06, 0.04), 0.03, 0.04),
                         ((-0.30, -0.10, 0.12), (-0.10, -0.22, 0.08), 0.03, 0.04),
                         ((-0.10, -0.22, 0.05), (0.06, -0.20, 0.04), 0.03, 0.03)],
                   ribs=(-0.34, -0.08, 0.10, 0.045, 0.1), fine=(-0.6, -0.05), sheet=(-0.64, 0.5, -0.44, 0.30, 18),
                   settle=3.0, feet=[((0.49, -0.04, 0.05), (0.8, -0.55, 0.15), (0.1, 0.25, 1.0)),
                                     ((0.50, 0.0, 0.11), (0.8, -0.5, 0.3), (-0.1, 0.4, 0.9))],
                   shins=None, hand=None, length=1.2),
}
SHROUDS['adult_hand'] = dict(SHROUDS['adult'], caps=_ADULT + _ARM_OUT + _mirror(_ARM_IN), hand=1)
SHROUDS['adult_hand_r'] = dict(SHROUDS['adult'], caps=_ADULT + _ARM_IN + _mirror(_ARM_OUT), hand=-1)
SHROUDS['bound'] = dict(SHROUDS['adult'], feet=_BOUND, shins=0.05)
SHROUDS['child'] = dict(SHROUDS['adult'], length=1.02, scale=(0.62, 0.72, 0.72))


def _sheet_height(spec):
    caps = spec['caps']
    rx0, rx1, rw, pitch, depth = spec['ribs']

    def H(x, y):
        h = max(_cap_height(x, y, c) for c in caps)
        if rx0 < x < rx1 and abs(y) < rw and h > 0.02:          # the ribs: ridges the sheet has settled between
            h *= 1.0 - depth * (0.5 + 0.5 * math.cos(2 * math.pi * (x - rx0) / pitch))
        return h
    return H


def shroud(kind, seed=0.0, rope=False):
    """A skeleton under a sheet, 76 years on the floor, as a Painted mesh in the remains atlas, its origin at the
    centre of its footprint on the floor, lying along x with its feet to +x. The sheet has settled onto the bones: a
    dome over the skull, ridges over the ribs, sunk to the spine below them, the pelvis's wings, the long bones. The
    feet are bone, out from under the hem, with a ration tag tied to a toe; on some a forearm and hand from under the
    sheet's edge. With rope: a rope round the ankles to a wooden toggle across the toes (D-17's grip), at BODY_LOOP.
    Returns (painted, toggle position or None)."""
    spec = SHROUDS[kind]
    x0, x1, y0, y1, ny = spec['sheet']
    f0, f1 = spec['fine']
    xs, x = [], x0
    while x < x1 - 1e-6:                                     # fine over the skull and the ribs, coarser elsewhere
        xs.append(x)
        x += 0.012 if f0 <= x <= f1 else 0.034
    xs.append(x1)
    nx = len(xs) - 1
    ys = [y0 + (y1 - y0) * j / ny for j in range(ny + 1)]
    Hf = _sheet_height(spec)
    H = [[Hf(x, y) for y in ys] for x in xs]
    # Drape: a cone dilation (the sheet tents from the bones it rests on), then a light blur, then creases.
    k = spec['settle']
    rad = 0.08
    S = [[0.0] * (ny + 1) for _ in range(nx + 1)]
    for i in range(nx + 1):
        for j in range(ny + 1):
            best = H[i][j]
            for p in range(nx + 1):
                ddx = abs(xs[p] - xs[i])
                if ddx > rad:
                    continue
                for q in range(max(0, j - 4), min(ny, j + 4) + 1):
                    h = H[p][q]
                    if h > best:
                        v = h - k * math.hypot(ddx, ys[q] - ys[j])
                        if v > best:
                            best = v
            S[i][j] = best
    T = [row[:] for row in S]
    for i in range(1, nx):
        for j in range(1, ny):
            T[i][j] = (S[i][j] * 6 + S[i - 1][j] + S[i + 1][j] + S[i][j - 1] + S[i][j + 1]) / 10
    S = T
    pts = []
    for i, x in enumerate(xs):
        row = []
        for j, y in enumerate(ys):
            z = S[i][j]
            edge = i == 0 or j == 0 or j == ny
            if z > 0.004 and not edge:
                z += 0.006 + 0.004 * noise.noise(Vector((x * 7.0, y * 9.0, seed * 3.1))) * min(1.0, z * 12)
            if edge or z < 0.004:
                z = 0.003 + 0.002 * abs(noise.noise(Vector((x * 11.0, y * 11.0, seed))))
            # the hem, rotted ragged along the sides
            yy = y + (0.012 * noise.noise(Vector((x * 9.0, seed, 1.7))) if j in (0, ny) else 0.0)
            row.append(Vector((x, yy, z)))
        pts.append(row)
    # The foot end hangs over the shins: a short ragged drop below its edge.
    drop = [Vector((p.x + 0.012 + 0.008 * noise.noise(Vector((p.y * 13.0, seed, 0.4))), p.y, max(0.003, p.z - 0.035)))
            for p in pts[-1]]
    pts.append(drop)
    P = Painted()
    P.grid('sheet', pts, nx + 1, ny)
    # Out from under the hem: the shin bones' ends, the feet, bone.
    tips = []
    for (A, fd, up) in spec['feet']:
        A = Vector(A)
        if spec['shins'] is not None:
            sy = math.copysign(spec['shins'], A.y)
            P.add('bone', lambda bm, A=A, sy=sy: long_bone(bm, (x1 - 0.1, sy, 0.03), A + Vector((-0.012, 0, -0.012)), 0.012, knob=1.4, seg=6))
        tips.append(foot(P, A, Vector(fd), Vector(up), s=1.0))
    # A forearm and hand from under the sheet's edge, palm down on the floor, the fingers loose.
    if spec['hand']:
        sd = spec['hand']
        E, W = Vector((-0.17, 0.29 * sd, 0.022)), Vector((-0.07, 0.355 * sd, 0.016))
        for o in (-0.008, 0.008):
            P.add('bone', lambda bm, o=o: long_bone(bm, E + Vector((o, 0, 0)), W + Vector((o, 0, 0)), 0.0075, knob=1.3, seg=5))
        hand(P, W, Vector((0.35, sd * 1.0, -0.12)), Vector((0, 0, 1)), s=1.0, curl=0.28, spread=1.4)
    # The ration tag: tied round the big toe of one foot, hanging from it on its string.
    big = tips[-1][0]
    side = -1.0 if big.y <= 0 else 1.0
    hang = big + Vector((0.035, side * 0.02, -0.05))
    P.add('rope', lambda bm: add_cyl(bm, big, hang, 0.0025, mat=0, seg=4))
    P.add('rope', lambda bm: add_torus(bm, big - Vector((0, 0, 0.012)), (0, 0, 1), 0.011, 0.0025, mat=0, seg=8, rseg=3))
    tw, tl = 0.05, 0.085                                     # the tag, hanging at 45 degrees to the body, two-sided
    nrm = Vector((0.707, side * 0.707, 0.0))
    up = Vector((0, 0, 1))
    for n_ in (nrm, -nrm):
        r = up.cross(n_)
        c = hang - Vector((0, 0, tl / 2 + 0.002)) + n_ * 0.0008
        P.quads('tag', [[c - r * tw / 2 - up * tl / 2, c + r * tw / 2 - up * tl / 2,
                         c + r * tw / 2 + up * tl / 2, c - r * tw / 2 + up * tl / 2]])
    if 'scale' in spec:
        P.transform(Matrix.Diagonal((*spec['scale'], 1.0)))
    # Centre it on its length and stretch it to the spec's length.
    xs_all = [v.co.x for v in P.bm.verts]
    lo, hi = min(xs_all), max(xs_all)
    sx = spec['length'] / (hi - lo)
    M = Matrix.Diagonal((sx, 1, 1, 1)) @ Matrix.Translation((-(lo + hi) / 2, 0, 0))
    P.transform(M)
    grip = None
    if rope:
        # Rope bound round both ankles above the heels, knotted on top, two strands on to a wooden toggle lying
        # across the toes at BODY_LOOP_AT (the game's grip: keep it there).
        ax_ = (M @ Vector(spec['feet'][0][0])).x - 0.035
        P.add('rope', lambda bm: _band(bm, ax_, 0.075, 0.045, 0.045))
        kc = Vector((ax_, 0.0, 0.098))
        P.add('rope', lambda bm: add_sphere(bm, kc, 0.02, mat=0, seg=8))
        grip = Vector((BODY_LOOP_AT[0], 0.0, BODY_LOOP_AT[1]))
        for s_ in (-1, 1):
            P.add('rope', lambda bm, s_=s_: add_cyl(bm, kc, grip + Vector((0, s_ * 0.075, 0)), 0.008, mat=0, seg=5))
            P.add('rope', lambda bm, s_=s_: add_torus(bm, grip + Vector((0, s_ * 0.075, 0)), (0, 1, 0), 0.022, 0.007, mat=0, seg=10, rseg=4))
        P.add('wood', lambda bm: add_cyl(bm, grip - Vector((0, 0.13, 0)), grip + Vector((0, 0.13, 0)), 0.016, mat=0, seg=10))
    return P, grip


def _band(bm, x, ry, rz, zc):
    """A rope bound round both ankles: an oval loop about x."""
    vs = add_torus(bm, (x, 0, zc), (1, 0, 0), 0.1, 0.01, mat=0, seg=18, rseg=5)
    bmesh.ops.scale(bm, vec=(1.0, ry / 0.1, rz / 0.1), space=Matrix.Translation((-x, 0, -zc)), verts=vs)
    return vs


BODY_LOOP_AT = (0.674, 0.277)        # RationBody's toggle (x offset from its origin, height): the game's grip

# Where the dead lie (x, y, z, turn in degrees, shape): feet to +x before the turn.
FAMINE = [
    ('RationDead01', 48.47, 1.985, 0.0, -90, 'adult'),      # a row, feet to the camera: two by the end wall,
    ('RationDead02', 49.09, 1.985, 0.002, -90, 'adult_hand'),
    ('RationDead03', 50.20, 1.985, 0.0, -90, 'adult'),      # four between the columns, under the vent
    ('RationDead04', 50.80, 1.985, 0.002, -90, 'adult_hand_r'),
    ('RationDead05', 51.40, 1.985, 0.0, -90, 'adult_hand'),
    ('RationDead06', 52.00, 1.985, 0.002, -90, 'adult'),
    ('RationDead07', 48.75, 0.86, 0.004, 0, 'child'),       # in front of the row, by the door: small
    ('RationDead08', 49.25, 3.15, 0.37, 0, 'adult'),        # on the cots
    ('RationDead09', 52.0, 3.22, 0.37, 180, 'curled'),
]


def build_famine(coll):
    """The dead under sheets in rows across the canteen floor and on the cots: linked duplicates of a few shapes,
    each one mesh in the remains atlas (sheet, bones, tag). And the one D-17 drags, RationBody: one mesh, its sheet
    finely divided along x (its length) so the game can ripple it as it is dragged."""
    meshes = {}
    for kind, seed in (('adult', 1.0), ('adult_hand', 1.6), ('adult_hand_r', 2.4), ('curled', 2.0), ('child', 3.0)):
        P, _ = shroud(kind, seed)
        meshes[kind] = P.mesh('RationShroud_' + kind, 'RemainsMat')
    out = []
    for name, x, y, z, turn, kind in FAMINE:
        ob = bpy.data.objects.new(name, meshes[kind])
        coll.objects.link(ob)
        ob.location = (x, y, z)
        ob.rotation_euler = (0, 0, math.radians(turn))
        out.append(ob)
    P, grip = shroud('bound', 4.0, rope=True)
    body = P.obj('RationBody', 'RemainsMat', coll)
    body.location = (BODY_START_X, BODY_Y, 0.0)
    BODY_LOOP[:] = [round(grip.x, 3), round(grip.z, 3)]
    return out, body


BODY_LOOP = []                       # filled by build_famine: the toggle's (x offset from the origin, height)


def _face_quad(c, w, h, y):
    """Corners of a quad facing -y (the camera), wound to face it."""
    cx, cz = c
    return [Vector((cx - w / 2, y, cz - h / 2)), Vector((cx + w / 2, y, cz - h / 2)),
            Vector((cx + w / 2, y, cz + h / 2)), Vector((cx - w / 2, y, cz + h / 2))]


def build_weighin(P, coll):
    """The WEIGH-IN: a goods weighbridge let into the floor in front of the hatch (RationScalePlate), its dial on a
    post at the counter's left end (face, RationScaleNeedle, RationServedFlag), the sign on the post."""
    # The pit's curb: angle iron round it, flush with the floor.
    px0, px1, py0, py1, pz = PIT
    st = P['DepotSteel']
    for (a, b, c, d) in ((px0 - 0.04, px1 + 0.04, py0 - 0.04, py0), (px0 - 0.04, px1 + 0.04, py1, py1 + 0.04),
                         (px0 - 0.04, px0, py0, py1), (px1, px1 + 0.04, py0, py1)):
        box(st, a, b, c, d, pz, 0.0015)
    box(P['Shaft'], px0, px1, py0, py1, pz, pz + 0.002)
    # The plate: chequer-ridged steel, a yellow band along its front and ends. Origin at its top centre.
    cx, cy, top = PLATE_C
    hx, hy = (PLATE[1] - PLATE[0]) / 2, (PLATE_Y[1] - PLATE_Y[0]) / 2
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.017), (2 * hx, 2 * hy, 0.034), mat=0)
    k = 0
    x = -hx + 0.06
    while x < hx - 0.05:
        add_box(bm, (x, 0, 0.0015), (0.012, 2 * hy - 0.06, 0.003), mat=0)
        x += 0.1
        k += 1
    add_box(bm, (0, -hy + 0.04, 0.0006), (2 * hx - 0.02, 0.06, 0.0012), mat=1)
    for s in (-1, 1):
        add_box(bm, (s * (hx - 0.04), 0, 0.0006), (0.06, 2 * hy - 0.02, 0.0012), mat=1)
    for sx in (-1, 1):                                   # lifting eyes in the corners
        for sy in (-1, 1):
            cyl(bm, (sx * (hx - 0.1), sy * (hy - 0.1), 0.0), (sx * (hx - 0.1), sy * (hy - 0.1), 0.004), 0.025, seg=10)
    plate = obj('RationScalePlate', bm, ['PlateSteel', 'SafetyYellow'], coll, sharp=30)
    plate.location = PLATE_C

    # The post, its foot bolted to the floor, the counter's corner behind it; the dial's case on it, the flag's bracket.
    x, y = POST
    g = P['DepotGreen']
    rbox(g, x - 0.03, x + 0.03, y - 0.03, y + 0.03, 0.0, 1.62, p=10, cuts=3)
    rbox(st, x - 0.1, x + 0.1, y - 0.035, y + 0.035, 0.0, 0.014, p=5, cuts=2)
    for dx in (-0.075, 0.075):
        cyl(st, (x + dx, y, 0.014), (x + dx, y, 0.026), 0.009, seg=6)
    dcx, dcy, dcz = DIAL_C
    cyl(g, (dcx, dcy + 0.016, dcz), (dcx, y - 0.03, dcz), 0.25, seg=36)
    add_torus(st, (dcx, dcy + 0.009, dcz), (0, 1, 0), 0.246, 0.012, mat=0, seg=36, rseg=6)
    rbox(g, x - 0.24, x + 0.24, 0.606, 0.614, 0.735, 0.955, p=6, cuts=2)                      # the sign's backing
    fx, fy, fz = FLAG_HINGE
    for dx in (-0.19, 0.19):                                                                    # the flag's bracket
        top_z = dcz + math.sqrt(max(0.0, 0.25 ** 2 - dx ** 2)) - 0.01
        cyl(st, (fx + dx, fy + 0.004, top_z), (fx + dx, fy + 0.004, fz + 0.012), 0.007, seg=6)
    cyl(st, (fx - 0.2, fy, fz), (fx + 0.2, fy, fz), 0.005, seg=6)
    # The face and the sign: one atlas.
    Pw = Painted(tex.weigh_uv)
    n = 40
    rimg = 244.0
    ring = []
    for i in range(n):
        a = 2 * math.pi * i / n
        ring.append((math.cos(a), math.sin(a)))
    fy_face = dcy + 0.013
    tris = []
    uvs = []
    for i in range(n):
        (c0, s0), (c1, s1) = ring[i], ring[(i + 1) % n]
        tris.append([Vector((dcx, fy_face, dcz)), Vector((dcx + DIAL_R * c0, fy_face, dcz + DIAL_R * s0)),
                     Vector((dcx + DIAL_R * c1, fy_face, dcz + DIAL_R * s1))])
        uvs.append([(256 / 512, 0.5), ((256 + rimg * c0) / 512, (256 + rimg * s0) / 512),
                    ((256 + rimg * c1) / 512, (256 + rimg * s1) / 512)])
    tmp = bmesh.new()
    uvl = tmp.loops.layers.uv.new('UVMap')
    u0, v0, u1, v1 = tex.weigh_uv('dial')
    for t, uv in zip(tris, uvs):
        f = tmp.faces.new([tmp.verts.new(p) for p in t])
        for lp, (a, b) in zip(f.loops, uv):
            lp[uvl].uv = (u0 + (u1 - u0) * a, v0 + (v1 - v0) * b)
    bmesh.ops.remove_doubles(tmp, verts=tmp.verts[:], dist=1e-6)
    Pw._merge(tmp)
    Pw.quads('sign', [_face_quad((x, 0.845), 0.4, 0.2, 0.604)])
    Pw.obj('RationWeighIn', 'WeighInMat', coll)

    # The needle: a flat blade with a short tail and a hub, pivoting at the dial's centre, pointing at zero.
    a = math.radians(-120.0)
    d = Vector((math.sin(a), 0, math.cos(a)))
    bm = bmesh.new()
    d17.add_wedge(bm, -d * 0.05, d * NEEDLE_LEN, 0.022, 0.004, 0.005, 0.004, (0, 0, 1) if abs(d.z) < 0.9 else (1, 0, 0), mat=0)
    cyl(bm, (0, -0.012, 0), (0, 0.008, 0), 0.024, seg=16)
    cyl(bm, (0, -0.016, 0), (0, -0.012, 0), 0.012, seg=12)
    needle = obj('RationScaleNeedle', bm, ['GaugeNeedle'], coll, sharp=30)
    needle.location = (dcx, dcy, dcz)

    # The SERVED flag: built hanging (its face to the camera), then turned up into its hidden rest about the hinge.
    Pf = Painted(tex.weigh_uv)
    w, h, t = 0.34, 0.11, 0.008
    q = _face_quad((0.0, -0.006 - h / 2), w, h, -t / 2)
    Pf.quads('served', [q])
    back = [Vector((p.x, t / 2, p.z)) for p in q][::-1]
    Pf.quads('flagback', [back])
    for (i0, i1) in ((0, 1), (1, 2), (2, 3), (3, 0)):                    # the edges
        a0, a1 = q[i0], q[i1]
        e = [a0, Vector((a0.x, t / 2, a0.z)), Vector((a1.x, t / 2, a1.z)), a1]
        Pf.quads('flagback', [e])
    Pf.add('flagback', lambda bm: add_cyl(bm, (-0.12, 0, 0), (0.12, 0, 0), 0.009, mat=0, seg=8))
    Pf.transform(Matrix.Rotation(math.radians(-FLAG_THROW), 4, 'X'))
    flag = Pf.obj('RationServedFlag', 'WeighInMat', coll, sharp=30)
    flag.location = FLAG_HINGE
    return plate, needle, flag


def build_paint(coll):
    """NO RATIONS / GRADE 4, slapped in whitewash on the wall over the counter."""
    decal('RationNoRations', 'NoRationsMat', 53.65, 56.15, 2.9, 3.84, BACK_Y - 0.02, coll)


# --------------------------------------------------------------------------

def build_set(dl01, m, coll):
    tex.make_textures()
    P = Parts()
    build_shell(P)
    build_counter(P, coll)
    build_shutter(coll)
    build_drum(coll)
    build_drum_marks(P, coll)
    build_lamp(P, coll)
    build_canteen(P, coll)
    build_shrine(P, coll)
    build_drawing(P, coll)
    build_kitchen(P)
    build_weighin(P, coll)
    build_famine(coll)
    build_paint(coll)
    P.emit(coll)


def add_clips(dl01, arm):
    """No new clips: the drum is pushed (PushWalk), the body dragged as DL-04's courier is (its toggle is lower:
    BODY_LOOP)."""
    pass
