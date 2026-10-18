"""DL-02 The Sorting Hall: the set and D-17's clips for this scene (docs/chapter1_build_spec.md, sections 2 and 3).

Built in world coordinates, between the stretches that build_dl01.OFF2..OFF4 move: the hall runs from DL-01's
bulkhead (x 11.9) to the weight room's left wall (x 25.0), on DL-01's floor. D-17 comes out of the service
passage (art/dl02, Passage, which stays where it is) through a doorway in the hall's back wall at x 13.2.

  - the tube station: brass tubes from the ceiling into a delivery cup, with the first undelivered letter in it;
  - MailSlot2, a post pillar with a red rimmed slot and a stamp lamp;
  - the tea corner in an alcove: a table, mugs, a kettle, the "courier of the year" board; the ring C notice;
  - the box (CarryBox) to carry and climb on;
  - the sorting table, backed by a pigeonhole wall whose right end has fallen across the lane (the collapse);
  - the gantry over the collapse, to the lit doorway into the weight room (cut in art/dl02).

Also here, shared by the three letters (DL-02, DL-06, DL-09): the envelope mesh (letter_mesh), the letter
textures (textures/letter_*.png, painted by textures_sorting_hall.py) and the clips PickUpLetter and PostLetter.

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Euler, Matrix, Quaternion, Vector

import build_d17 as d17
from build_d17 import (add_box, add_cyl, add_sphere, add_torus, rounded_box, emission_material,
                       worn_material, simple_material, smoothstep, SIDES, CLAW_REST_OPEN)
import textures_sorting_hall as paint

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')

# Shared with the game (game/undelivered/index.html keeps the same numbers).
HALL = (11.9, 25.0)                   # world x
LEFT_X = 12.0                         # the hall's left wall (its face)
BACK_Y = 1.0                          # the back wall's face, beyond the passage
PASS_Y = 0.62                         # the face of the wall over the passage (the bulkhead's line)
CEIL = 4.5
EMERGE = (12.85, 13.55, 1.05)         # the doorway out of the passage: x0, x1, height (= art/dl02 DOOR2)
TUBE = (14.6, 0.85, 0.9)              # the delivery cup: x, y, rim height
SLOT = (16.0, 0.45, 0.55)             # MailSlot2: pillar centre x, y; the slot's centre height
SLOT_FACE_Y = 0.295                   # the slot plate's face (D-17 stands at y 0 to post)
ALCOVE = (15.35, 17.3, 1.7, 2.3)      # the tea corner: x0, x1, back face y, lintel
BOX_X = 17.4
BOX = (0.40, 0.34, 0.20)              # CarryBox: x, y, z (see build_box)
BOX_HANDLE = (-0.06, 0.22)            # its handle: x from the box's centre (toward D-17 coming from the left), top height
TABLE = (18.6, 22.6, 0.75)            # SortTable: x0, x1, top
TABLE_Y = (-0.45, 0.65)
COLLAPSE = (22.6, 23.5, 2.2)          # x0, x1, height at the back
GANTRY = (22.4, 25.0, 1.35)           # SortGantry: x0, x1, deck top
GANTRY_Y = (-0.35, 0.2)

# The envelope (section 2).
LETTER = (0.16, 0.11, 0.003)          # long side, short side, thickness
LETTER_TEX = {k: os.path.join(TEX, f'letter_{k}.png') for k in ('tube', 'heap', 'c110')}


def _obj(name, bm, mats, coll, sharp=35):
    return d17.mesh_object(name, bm, mats, coll, sharp=sharp)


def _image_material(name, path, rough=0.75):
    mat, nt, bsdf = d17._new_material(name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    return mat


def _plane(name, size, center, mat, coll, rot=None):
    """A textured quad, facing -y (the camera) unless rotated."""
    bm = bmesh.new()
    bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, calc_uvs=True)
    m = Matrix.Translation(center) @ (rot or Matrix.Rotation(math.radians(90), 4, 'X')) @ Matrix.Diagonal((size[0], size[1], 1, 1))
    bmesh.ops.transform(bm, verts=bm.verts, matrix=m)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def _rx(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'X')


def _rz(deg):
    return Matrix.Rotation(math.radians(deg), 4, 'Z')


# --------------------------------------------------------------------------
# The letters' shared pieces
# --------------------------------------------------------------------------

def letter_material(key):
    """The image material for letter 'tube', 'heap' or 'c110' (LetterTube, LetterHeap, LetterC110)."""
    paint.make_textures()
    name = {'tube': 'LetterTube', 'heap': 'LetterHeap', 'c110': 'LetterC110'}[key]
    return bpy.data.materials.get(name) or _image_material(name, LETTER_TEX[key], rough=0.85)


def letter_mesh(name, mat, coll, loc=(0, 0, 0), rot=(0, 0, 0)):
    """An envelope, 0.16 x 0.11 and 3 mm thick, origin at its centre. In its own coordinates it lies flat:
    the long side along x, the front (address) facing +z, the flap's edge toward +y. The texture is an atlas,
    the front on its left half and the back on its right half; the edges take the back's paper."""
    w, h, t = LETTER
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    v = {}
    for sx in (-1, 1):
        for sy in (-1, 1):
            for sz in (-1, 1):
                v[sx, sy, sz] = bm.verts.new((sx * w / 2, sy * h / 2, sz * t / 2))

    def face(keys, uvs):
        f = bm.faces.new([v[k] for k in keys])
        for lp, co in zip(f.loops, uvs):
            lp[uv].uv = co
    # Front (+z): the left half of the atlas, read from above with +y up the page.
    face([(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], [(0, 0), (0.5, 0), (0.5, 1), (0, 1)])
    # Back (-z): the right half, read from below (mirrored in x so it is the right way round).
    face([(-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)], [(1, 1), (0.5, 1), (0.5, 0), (1, 0)])
    edge = [(0.52, 0.04), (0.53, 0.04), (0.53, 0.05), (0.52, 0.05)]
    face([(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)], edge)
    face([(1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1)], edge)
    face([(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)], edge)
    face([(-1, 1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1)], edge)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    ob.location = loc
    ob.rotation_euler = [math.radians(a) for a in rot]
    coll.objects.link(ob)
    return ob


# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------

def hall_materials(m):
    # Shared palette entries other scenes define; made here with the same names and values when this scene
    # is built on its own.
    if 'brass' not in m:
        m['brass'] = bpy.data.materials.get('Brass') or simple_material('Brass', (0.45, 0.32, 0.12), 0.45, metallic=0.8)
    if 'pigeon' not in m:
        m['pigeon'] = bpy.data.materials.get('PigeonWood') or worn_material(
            'PigeonWood', base=(0.12, 0.085, 0.055), dirt=(0.06, 0.045, 0.03), chip=(0.2, 0.15, 0.1),
            rough=0.85, chip_rough=0.8, metallic=0.0)
    if 'letters' not in m:
        m['letters'] = bpy.data.materials.get('LetterPaper') or worn_material(
            'LetterPaper', base=(0.55, 0.52, 0.45), dirt=(0.3, 0.27, 0.2), chip=(0.62, 0.6, 0.55),
            rough=0.9, chip_rough=0.9, metallic=0.0)
    if 'deadbulb' not in m:
        m['deadbulb'] = bpy.data.materials.get('DeadBulb') or simple_material('DeadBulb', (0.16, 0.16, 0.15), 0.25)
    # New here.
    m['sortlamp'] = emission_material('SortLampBulb', (1.0, 0.84, 0.6), 0.0)
    m['tubelamp'] = emission_material('TubeLamp', (1.0, 0.7, 0.35), 0.0)
    m['slotlamp2'] = emission_material('SlotLamp2', (1.0, 0.78, 0.45), 0.0)
    m['enamel'] = simple_material('TeaEnamel', (0.58, 0.55, 0.47), 0.35)


# --------------------------------------------------------------------------
# The set
# --------------------------------------------------------------------------

def _panels(bm, x0, x1, z0, z1, y, seed, depth=0.3):
    """Seamed wall panels like the bulkhead's, face at y."""
    n = max(1, round((x1 - x0) / 0.95))
    w = (x1 - x0) / n
    for k in range(n):
        rounded_box((w - 0.03, depth, z1 - z0 - 0.02), (x0 + w * (k + 0.5), y + depth / 2, (z0 + z1) / 2), p=12, cuts=3,
                    dents=((0.006, 3.0),), seed=seed + k, bm=bm, mat=0)


def build_shell(m, coll):
    """Walls, ceiling and beams. The weight room's wall at x 25 is art/dl02's (WeighRoomLeftWall)."""
    ex0, ex1, eh = EMERGE
    bm = bmesh.new()
    add_box(bm, (LEFT_X - 0.09, -0.3, (CEIL + 0.15) / 2), (0.18, 2.6, CEIL + 0.15))           # left wall, behind DL-01's end wall
    # Over the passage: panels like the bulkhead's to 2.6 (the bulkhead's own run to 12.45), then plain wall.
    for i, (a0, a1, z0, z1) in enumerate(((12.45, ex0, 0.0, 2.6), (ex1, 13.95, 0.0, 2.6), (ex0, ex1, eh, 2.6))):
        _panels(bm, a0, a1, z0, z1, PASS_Y, 140 + 5 * i)
    add_box(bm, (13.05, PASS_Y + 0.15, (2.6 + CEIL + 0.15) / 2), (2.1, 0.3, CEIL + 0.15 - 2.6))
    add_box(bm, (14.05, 0.95, (CEIL + 0.15) / 2), (0.22, 0.7, CEIL + 0.15))                     # pilaster where the wall steps back
    # Beyond the passage: the back wall, with the tea-corner alcove.
    a0, a1, ay, lintel = ALCOVE
    for x0, x1 in ((14.16, a0), (a1, HALL[1])):
        add_box(bm, ((x0 + x1) / 2, BACK_Y + 0.13, (CEIL + 0.15) / 2), (x1 - x0, 0.26, CEIL + 0.15))
    add_box(bm, ((a0 + a1) / 2, BACK_Y + 0.13, (lintel + CEIL + 0.15) / 2), (a1 - a0, 0.26, CEIL + 0.15 - lintel))
    add_box(bm, ((a0 + a1) / 2, ay + 0.08, lintel / 2), (a1 - a0 + 0.1, 0.16, lintel))          # alcove back
    for x in (a0 - 0.02, a1 + 0.02):
        add_box(bm, (x, (BACK_Y + ay) / 2 + 0.05, lintel / 2), (0.04, ay - BACK_Y + 0.1, lintel))
    add_box(bm, ((a0 + a1) / 2, (BACK_Y + ay) / 2 + 0.05, lintel + 0.03), (a1 - a0, ay - BACK_Y + 0.1, 0.06))
    _obj('SortHallWalls', bm, [m['wall']], coll)

    # A dado of panels along the back wall, and the scar where the pigeonhole wall tore away.
    bm = bmesh.new()
    for x0, x1 in ((14.16, a0), (a1, 18.4)):
        add_box(bm, ((x0 + x1) / 2, BACK_Y - 0.01, 0.55), (x1 - x0, 0.03, 1.1))
    add_box(bm, ((14.16 + HALL[1]) / 2, BACK_Y - 0.02, 1.12), (HALL[1] - 14.16, 0.05, 0.05))
    obj = _obj('SortHallDado', bm, [m['depot_green']], coll)
    bm = bmesh.new()
    rnd = random.Random(144)
    for k in range(9):                                 # bolts and torn brackets where the unit hung
        z = 0.9 + k * 0.17
        add_box(bm, (22.55 + rnd.uniform(-0.04, 0.04), BACK_Y - 0.02, z), (0.05, 0.04, 0.02))
        add_box(bm, (23.6 + rnd.uniform(-0.04, 0.04), BACK_Y - 0.02, z + 0.05), (0.04, 0.06, 0.03),
                rot=Matrix.Rotation(rnd.uniform(-0.6, 0.6), 4, 'Y'))
    _obj('CollapseScar', bm, [m['rust'] if 'rust' in m else m['steel']], coll)

    # Ceiling and its beams.
    bm = bmesh.new()
    add_box(bm, ((HALL[0] + HALL[1]) / 2, -0.45, CEIL + 0.08), (HALL[1] - HALL[0] + 0.1, 3.5, 0.16))
    _obj('SortHallCeiling', bm, [m['concrete']], coll)
    bm = bmesh.new()
    for x in (13.5, 16.5, 19.5, 22.5):
        add_box(bm, (x, -0.45, CEIL - 0.14), (0.16, 3.5, 0.28))
    for y in (-1.4, 0.55):
        add_box(bm, ((HALL[0] + HALL[1]) / 2, y, CEIL - 0.06), (HALL[1] - HALL[0], 0.12, 0.12))
    _obj('SortHallBeams', bm, [m['steel']], coll)
    return obj


def build_tube_station(m, coll):
    """The pneumatic tube terminal: brass tubes down from the ceiling into a cabinet on the back wall, the
    delivery tube's mouth over the cup, the cup with the first letter in it, a rack of tube carriers."""
    tx, ty, tz = TUBE
    bm = bmesh.new()
    add_box(bm, (tx, 0.9, 1.4), (0.7, 0.2, 0.7), mat=0)                           # the cabinet
    add_box(bm, (tx, 0.79, 1.4), (0.62, 0.02, 0.62), mat=0)
    add_box(bm, (tx, 0.86, 1.76), (0.76, 0.3, 0.04), mat=1)                        # brass cap
    add_box(bm, (tx - 0.18, 0.775, 1.55), (0.14, 0.012, 0.14), mat=1)            # the arrivals dial
    for k in range(3):                                                            # dispatch flaps
        add_box(bm, (tx - 0.2 + k * 0.2, 0.775, 1.22), (0.12, 0.015, 0.08), mat=1)
    add_box(bm, (tx, 0.95, 0.88), (0.08, 0.1, 0.16), mat=0)                       # the cup's bracket
    _obj('TubeTerminal', bm, [m['depot_green'], m['brass']], coll)

    # Brass runs: three down into the cabinet, the delivery tube on through it to a mouth above the cup,
    # and the manifold along the top of the back wall that feeds them.
    bm = bmesh.new()
    r = 0.032
    for x in (tx - 0.22, tx, tx + 0.22):
        add_cyl(bm, (x, 0.88, CEIL - 0.3), (x, 0.88, 1.78), r, seg=12)
        add_cyl(bm, (x, 0.88, CEIL - 0.3), (x, 0.88, CEIL - 0.42), r + 0.008, seg=12)
    for z, y in ((CEIL - 0.3, 0.88), (CEIL - 0.55, 0.9)):
        add_cyl(bm, (12.3, y, z), (24.8, y, z), r, seg=12)
        for x in range(13, 25, 2):
            add_cyl(bm, (x, y, z), (x + 0.08, y, z), r + 0.01, seg=12)                # collars
    add_cyl(bm, (tx + 0.22, 0.88, CEIL - 0.55), (tx + 0.22, 0.88, CEIL - 0.3), r, seg=12)
    for x in (12.6, 17.6, 21.0, 24.3):                                             # drops into the wall
        add_cyl(bm, (x, 0.9, CEIL - 0.55), (x, 0.9, 2.9 + (x % 1.3)), r, seg=12)
        add_cyl(bm, (x, 0.9, 2.9 + (x % 1.3)), (x, 1.02, 2.9 + (x % 1.3)), r, seg=12)
    add_cyl(bm, (tx, 0.86, 1.0), (tx, 0.83, 1.07), 0.03, 0.045, seg=16)            # the delivery mouth over the cup
    add_cyl(bm, (tx, 0.86, 1.07), (tx, 0.86, 1.06), 0.046, seg=16)
    _obj('TubeRuns', bm, [m['brass']], coll)

    # The cup (static): an open brass basket at 0.9, its rim lipped forward.
    bm = bmesh.new()
    cx0, cx1, cy0, cy1, cz0 = tx - 0.12, tx + 0.12, ty - 0.1, ty + 0.1, tz - 0.1
    add_box(bm, (tx, ty, cz0), (0.24, 0.2, 0.012))
    add_box(bm, (tx, cy1, (cz0 + tz) / 2), (0.24, 0.012, tz - cz0))
    add_box(bm, (tx, cy0 + 0.01, (cz0 + tz) / 2 - 0.02), (0.24, 0.012, tz - cz0 - 0.04), rot=_rx(-12))
    for x in (cx0, cx1):
        add_box(bm, (x, ty, (cz0 + tz) / 2), (0.012, 0.2, tz - cz0))
    add_cyl(bm, (cx0, cy0 - 0.005, tz - 0.02), (cx1, cy0 - 0.005, tz - 0.02), 0.009, seg=8)
    _obj('TubeCup', bm, [m['brass']], coll)

    # The first letter, standing in the cup and leaning back against it. Origin at its centre.
    letter_mesh('TubeLetter', letter_material('tube'), coll, loc=(tx + 0.01, ty + 0.01, tz - 0.035), rot=(68, 0, 6))

    # Its lamp: lit by the game when the tube coughs.
    bm = bmesh.new()
    add_sphere(bm, (tx + 0.2, 0.772, 1.6), 0.018, seg=12, scale=(1, 0.6, 1))
    _obj('TubeLamp', bm, [m['tubelamp']], coll)

    # A rack of tube carriers (the brass capsules the letters rode in), and one dropped.
    bm = bmesh.new()
    add_box(bm, (14.12, 0.9, 0.62), (0.14, 0.2, 0.02), mat=0)
    add_box(bm, (14.12, 0.99, 0.72), (0.14, 0.02, 0.22), mat=0)
    for k in range(3):
        add_cyl(bm, (14.07 + k * 0.05, 0.86, 0.63), (14.07 + k * 0.05, 0.86, 0.83), 0.022, seg=12, mat=1)
    add_cyl(bm, (14.2, 0.55, 0.022), (14.38, 0.62, 0.022), 0.022, seg=12, mat=1)
    _obj('TubeCarriers', bm, [m['steel'], m['brass']], coll)


def build_mail_slot(m, coll):
    """MailSlot2: a post pillar on the lane's back edge. Its slot (red rimmed, at 0.55) faces the lane;
    a stamp lamp on its cap. Origin at the pillar's base centre."""
    sx, sy, sz = SLOT
    face = SLOT_FACE_Y
    bm = bmesh.new()
    add_cyl(bm, (0, 0, 0), (0, 0, 0.05), 0.175, seg=24, mat=0)
    add_cyl(bm, (0, 0, 0.05), (0, 0, 0.8), 0.15, seg=24, mat=0)
    add_cyl(bm, (0, 0, 0.8), (0, 0, 0.83), 0.165, seg=24, mat=0)
    add_sphere(bm, (0, 0, 0.83), 0.15, seg=24, scale=(1, 1, 0.42), mat=0)
    add_box(bm, (0, face - sy + 0.025, sz), (0.3, 0.05, 0.13), mat=1)              # the slot plate
    add_box(bm, (0, face - sy + 0.012, sz + 0.075), (0.32, 0.03, 0.02), mat=1)     # its hood
    add_box(bm, (0, face - sy + 0.02, 0.32), (0.16, 0.03, 0.1), mat=2)              # the collection plate
    add_box(bm, (0, face - sy + 0.008, sz), (0.22, 0.03, 0.03), mat=3)              # the slot: dark inside
    # The red rim round the slot.
    for dz in (-0.024, 0.024):
        add_box(bm, (0, face - sy - 0.002, sz + dz), (0.25, 0.012, 0.016), mat=4)
    for dx in (-0.118, 0.118):
        add_box(bm, (dx, face - sy - 0.002, sz), (0.016, 0.012, 0.064), mat=4)
    ob = _obj('MailSlot2', bm, [m['depot_green'], m['steel'], m['brass'], m['rubber'], m['red']], coll)
    ob.location = (sx, sy, 0)
    bm = bmesh.new()                                                                # the stamp lamp's cage
    for k in range(4):
        a = k * math.pi / 2
        add_cyl(bm, (0.035 * math.cos(a), 0.035 * math.sin(a), 0.89), (0.02 * math.cos(a), 0.02 * math.sin(a), 0.95), 0.004, seg=4)
    add_cyl(bm, (0, 0, 0.885), (0, 0, 0.895), 0.045, seg=16)
    ob = _obj('SlotLamp2Cage', bm, [m['brass']], coll)
    ob.location = (sx, sy, 0)
    bm = bmesh.new()
    add_sphere(bm, (0, 0, 0), 0.028, seg=14)
    ob = _obj('SlotLamp2', bm, [m['slotlamp2']], coll)
    ob.location = (sx, sy, 0.92)


def build_tea_corner(m, coll):
    """The alcove: a little table with mugs and a kettle, mugs on hooks with number tags, a stool, the
    courier-of-the-year board. No lamp: a dead bulb on its flex."""
    a0, a1, ay, lintel = ALCOVE
    bm = bmesh.new()
    add_box(bm, (15.78, 1.4, 0.7), (0.6, 0.42, 0.04))
    for x in (15.52, 16.04):
        for y in (1.23, 1.57):
            add_box(bm, (x, y, 0.34), (0.035, 0.035, 0.68))
    add_box(bm, (15.78, 1.4, 0.18), (0.55, 0.38, 0.02))
    add_cyl(bm, (16.55, 1.25, 0.0), (16.55, 1.25, 0.42), 0.13, 0.12, seg=16)          # an upturned crate for a stool
    _obj('TeaTable', bm, [m['wood']], coll)
    bm = bmesh.new()
    rnd = random.Random(150)
    for i, (x, y) in enumerate(((15.6, 1.32), (15.72, 1.48), (15.93, 1.36))):
        add_cyl(bm, (x, y, 0.72), (x, y, 0.81), 0.035, seg=14)
        add_torus(bm, (x + 0.04, y, 0.765), (0, 1, 0), 0.022, 0.006, seg=10, rseg=4)
    add_cyl(bm, (15.5, 1.5, 0.72), (15.5, 1.5, 0.735), 0.06, seg=14)                    # a saucer
    for k in range(5):                                                                 # mugs on hooks, one hook empty
        x = a0 + 0.2 + k * 0.17
        if k != 3:
            add_cyl(bm, (x, ay - 0.06, 1.13), (x, ay - 0.06, 1.22), 0.035, seg=14)
    _obj('TeaMugs', bm, [m['enamel']], coll)
    bm = bmesh.new()
    add_sphere(bm, (15.86, 1.5, 0.81), 0.075, seg=16, scale=(1, 1, 0.9))                # the kettle
    add_cyl(bm, (15.86, 1.5, 0.87), (15.86, 1.5, 0.9), 0.03, seg=12)
    add_cyl(bm, (15.8, 1.5, 0.8), (15.74, 1.5, 0.86), 0.012, 0.008, seg=8)
    add_torus(bm, (15.86, 1.5, 0.9), (1, 0, 0), 0.05, 0.007, seg=14, rseg=4)
    add_box(bm, ((a0 + a1) / 2 - 0.25, ay - 0.02, 1.25), (0.95, 0.03, 0.03))             # the hook rail
    for k in range(5):
        x = a0 + 0.2 + k * 0.17
        add_cyl(bm, (x, ay - 0.03, 1.25), (x, ay - 0.08, 1.23), 0.004, seg=4)
    add_cyl(bm, (16.45, 1.3, lintel), (16.45, 1.3, 1.9), 0.004, seg=6)                   # the dead bulb's flex
    _obj('TeaKettle', bm, [m['steel']], coll)
    bm = bmesh.new()
    for k in range(5):                                                                 # number tags over the hooks
        add_box(bm, (a0 + 0.2 + k * 0.17, ay - 0.012, 1.31), (0.06, 0.006, 0.03))
    _obj('TeaTags', bm, [m['tag']], coll)
    bm = bmesh.new()
    add_sphere(bm, (16.45, 1.3, 1.87), 0.03, seg=12)
    _obj('TeaBulb', bm, [m['deadbulb']], coll)

    # The courier-of-the-year board, on the alcove's back wall.
    bx, bz, bw, bh = 16.62, 1.5, 0.8, 0.51
    bm = bmesh.new()
    add_box(bm, (bx, ay - 0.01, bz), (bw + 0.06, 0.03, bh + 0.06))
    _obj('CourierBoardFrame', bm, [m['wood']], coll)
    _plane('CourierBoard', (bw, bh), (bx, ay - 0.027, bz), _image_material('CourierBoardMat', os.path.join(TEX, 'courier_board.png')), coll)

    # The ring C notice, pinned by the tube terminal.
    _plane('RingCNotice', (0.25, 0.35), (15.1, BACK_Y - 0.006, 1.25),
           _image_material('RingCNoticeMat', os.path.join(TEX, 'ringc_notice.png')), coll)
    bm = bmesh.new()
    for x in (15.0, 15.2):
        add_sphere(bm, (x, BACK_Y - 0.01, 1.41), 0.008, seg=8)
    _obj('RingCNoticePins', bm, [m['brass']], coll)


def build_box(m, coll):
    """CarryBox: a parcel box 0.40 (x) x 0.34 (y) x 0.20 (z), origin at its base centre, with a red strap
    round it and a red handle on top (its grip at 0.22, as the clips' bail; offset 6 cm toward -x, so a box
    carried rightward hangs clear of his legs)."""
    bx, by, bz = BOX
    hx, hz = BOX_HANDLE
    bm = bmesh.new()
    rounded_box((bx, by, bz), (0, 0, bz / 2), p=10, cuts=3, dents=((0.004, 6.0),), seed=7, bm=bm, mat=0)
    add_box(bm, (0.08, -by / 2 - 0.001, 0.12), (0.12, 0.003, 0.07), mat=1)            # a label
    ob = _obj('CarryBox', bm, [m['paper'], m['tag']], coll)
    ob.location = (BOX_X, 0, 0)
    bm = bmesh.new()
    w = 0.035
    add_box(bm, (hx, 0, bz + 0.002), (w, by + 0.006, 0.004))                           # the strap, all the way round
    add_box(bm, (hx, 0, -0.001), (w, by + 0.006, 0.003))
    for y in (-by / 2 - 0.002, by / 2 + 0.002):
        add_box(bm, (hx, y, bz / 2), (w, 0.004, bz + 0.006))
    for y in (-0.1, 0.1):                                                              # the handle on top
        add_box(bm, (hx, y, bz + 0.012), (0.02, 0.02, 0.022))
    add_cyl(bm, (hx, -0.12, hz - 0.008), (hx, 0.12, hz - 0.008), 0.009, seg=10)
    ob = _obj('CarryBoxStrap', bm, [m['red']], coll)
    ob.location = (BOX_X, 0, 0)
    ob.parent = bpy.data.objects['CarryBox']
    ob.matrix_parent_inverse = Matrix.Translation((-BOX_X, 0, 0))


def build_table(m, coll):
    """SortTable: a long sorting table, solid to the floor (drawers in front), top at 0.75. Trays, parcels and
    the pigeonhole wall behind it only on the back half, so the strip along the front of the top is clear."""
    x0, x1, top = TABLE
    y0, y1 = TABLE_Y
    cx, w = (x0 + x1) / 2, x1 - x0
    bm = bmesh.new()
    add_box(bm, (cx, (y0 + y1) / 2, top - 0.025), (w + 0.04, y1 - y0 + 0.04, 0.05), mat=0)    # the top
    add_box(bm, (cx, (y0 + y1) / 2, 0.34), (w - 0.04, y1 - y0 - 0.06, 0.68), mat=0)            # the carcass
    add_box(bm, (cx, (y0 + y1) / 2, 0.04), (w, y1 - y0 - 0.02, 0.08), mat=2)                   # plinth
    n = 8
    for k in range(n):                                                                         # two rows of drawers
        x = x0 + 0.02 + (w - 0.04) * (k + 0.5) / n
        for z, hgt in ((0.53, 0.2), (0.25, 0.3)):
            add_box(bm, (x, y0 + 0.02, z), ((w - 0.04) / n - 0.025, 0.02, hgt), mat=0)
            add_box(bm, (x, y0 + 0.004, z + hgt / 2 - 0.05), (0.09, 0.012, 0.018), mat=1)       # pulls
            add_box(bm, (x, y0 + 0.006, z + hgt / 2 - 0.025), (0.035, 0.008, 0.012), mat=3)     # card holders
    add_box(bm, (cx, y0 + 0.005, top - 0.06), (w + 0.04, 0.012, 0.012), mat=1)                # brass edging
    _obj('SortTable', bm, [m['wood'], m['brass'], m['steel'], m['tag']], coll)

    rnd = random.Random(186)
    trays, parcels, letters = bmesh.new(), bmesh.new(), bmesh.new()
    for k in range(7):                                                                         # sorting trays
        x = x0 + 0.35 + k * 0.55 + rnd.uniform(-0.05, 0.05)
        if k == 4:
            continue
        tw, td = 0.42, 0.28
        y = 0.43
        rot = Matrix.Rotation(rnd.uniform(-0.08, 0.08), 4, 'Z')
        add_box(trays, (x, y, top + 0.006), (tw, td, 0.012), rot=rot)
        for dy in (-td / 2, td / 2):
            add_box(trays, (x, y + dy, top + 0.035), (tw, 0.012, 0.06), rot=rot)
        for dx in (-tw / 2, tw / 2):
            add_box(trays, (x + dx, y, top + 0.035), (0.012, td, 0.06), rot=rot)
        for j in range(rnd.randint(4, 9)):                                                    # letters standing in it
            add_box(letters, (x - tw / 2 + 0.04 + j * 0.04, y + rnd.uniform(-0.02, 0.02), top + 0.06),
                    (0.004, 0.2, 0.1), rot=Matrix.Rotation(rnd.uniform(-0.25, 0.25), 4, 'Y'))
    for x, sz in ((20.55, (0.24, 0.2, 0.16)), (20.75, (0.16, 0.14, 0.1)), (22.2, (0.2, 0.26, 0.14)), (19.0, (0.14, 0.12, 0.08))):
        add_box(parcels, (x, 0.42 + rnd.uniform(-0.04, 0.04), top + sz[2] / 2), sz, rot=Matrix.Rotation(rnd.uniform(-0.4, 0.4), 4, 'Z'))
    add_box(parcels, (20.7, 0.4, top + 0.16 + 0.05), (0.12, 0.1, 0.1), rot=Matrix.Rotation(0.5, 4, 'Z'))
    _obj('SortTrays', trays, [m['pigeon']], coll)
    _obj('SortParcels', parcels, [m['paper']], coll)
    _obj('SortLetters', letters, [m['letters']], coll)

    # The pigeonhole wall behind the table (its right end is the collapse).
    px0, px1, pz0, pz1, py = 18.45, 22.5, top, 2.6, 0.7
    bm = bmesh.new()
    add_box(bm, ((px0 + px1) / 2, py + 0.28, (pz0 + pz1) / 2), (px1 - px0, 0.04, pz1 - pz0))            # back board
    cols, rows = 20, 11
    for k in range(cols + 1):
        x = px0 + (px1 - px0) * k / cols
        hgt = pz1 - pz0 if k < cols else 0.9                                                         # the broken end
        add_box(bm, (x, py + 0.14, pz0 + hgt / 2), (0.02, 0.3, hgt))
    for j in range(rows + 1):
        z = pz0 + (pz1 - pz0) * j / rows
        xe = px1 if z < pz0 + 0.95 else px1 - (px1 - px0) / cols * (1 + (j % 3))
        add_box(bm, ((px0 + xe) / 2, py + 0.14, z), (xe - px0, 0.3, 0.02))
    add_box(bm, ((px0 + px1) / 2 - 0.1, py + 0.12, pz1 + 0.05), (px1 - px0 - 0.2, 0.36, 0.1))           # cornice
    add_box(bm, (px1 - 0.25, py + 0.14, pz0 + 1.15), (0.5, 0.3, 0.02), rot=Matrix.Rotation(0.35, 4, 'Y'))   # a hanging shelf
    _obj('PigeonholeWall', bm, [m['pigeon']], coll)
    bm = bmesh.new()
    for k in range(70):                                                                             # post left in the holes
        c = rnd.randrange(cols - 1)
        j = rnd.randrange(rows)
        x = px0 + (px1 - px0) * (c + 0.5) / cols
        z = pz0 + (pz1 - pz0) * j / rows + 0.01
        if rnd.random() < 0.5:
            add_box(bm, (x + rnd.uniform(-0.04, 0.04), py + 0.16, z + 0.04), (0.12, 0.2, 0.004 * rnd.randint(1, 6)))
        else:
            add_box(bm, (x, py + 0.16, z + 0.05), (0.004 * rnd.randint(1, 5), 0.2, 0.1),
                    rot=Matrix.Rotation(rnd.uniform(-0.3, 0.3), 4, 'Y'))
    _obj('PigeonholeLetters', bm, [m['letters']], coll)

    # The work lamp over the table: warm, on a long flex from the ceiling.
    lx, ly, lz = 20.6, -0.25, 2.62
    bm = bmesh.new()
    add_cyl(bm, (lx, ly, CEIL), (lx, ly, lz + 0.14), 0.005, seg=6, mat=1)
    add_cyl(bm, (lx, ly, lz + 0.14), (lx, ly, lz + 0.05), 0.03, 0.04, seg=16, mat=0)
    add_cyl(bm, (lx, ly, lz + 0.05), (lx, ly, lz - 0.02), 0.04, 0.17, seg=24, mat=0)
    _obj('SortLampFixture', bm, [m['depot_green'], m['rubber']], coll)
    bm = bmesh.new()
    add_sphere(bm, (lx, ly, lz), 0.04, seg=14)
    _obj('SortLampBulb', bm, [m['sortlamp']], coll)


def _slab_frame():
    """The fallen pigeonhole unit: (origin on its top face, axis up the slope, normal out of the face)."""
    a = math.radians(46.0)
    up = Vector((0, math.cos(a), math.sin(a)))
    nrm = Vector((0, -math.sin(a), math.cos(a)))
    top_y, top_z = 0.2, 1.30                          # its top face passes just under the gantry's deck here
    k = 1.0 / math.tan(a) if a else 0
    z_at = lambda y: top_z + (y - top_y) * math.tan(a)     # noqa: E731
    return up, nrm, z_at, a


def build_collapse(m, coll):
    """A pigeonhole wall, fallen across the lane: one tall unit lying against the back wall at a slant, its
    foot on the floor in front of the lane and its head 2.2 up the back wall, the gantry resting on it.
    Parcels, letters, boards and broken cubbies are heaped under and round it, so nothing passes below."""
    x0, x1, _ = COLLAPSE
    cx, w = (x0 + x1) / 2, x1 - x0
    up, nrm, z_at, a = _slab_frame()
    rot = Matrix.Rotation(a, 4, 'X')
    y_lo = 0.2 - 1.30 / math.tan(a)                   # where its face meets the floor
    y_hi = 1.06
    length = (y_hi - y_lo) / math.cos(a)
    base = Vector((cx, y_lo, 0.0))
    t = 0.34

    def at(s, d, x=cx):                               # s up the slope, d down from the face
        p = base + up * s - nrm * d
        return Vector((x, p.y, p.z))
    bm = bmesh.new()
    add_box(bm, at(length / 2, t - 0.02), (w, length, 0.04), rot=rot)                      # its back
    for x in (x0 + 0.01, x1 - 0.01):                                                      # its sides
        add_box(bm, at(length / 2, t / 2, x), (0.03, length, t), rot=rot)
    for k in range(1, 6):                                                                 # cubby dividers
        add_box(bm, at(length / 2, t / 2, x0 + w * k / 6), (0.016, length - 0.1, t - 0.04), rot=rot)
    n = 18
    for k in range(n + 1):
        s = 0.05 + (length - 0.1) * k / n
        if k in (5, 6, 11):
            continue                                                                      # broken shelves
        add_box(bm, at(s, t / 2), (w - 0.04, 0.016, t - 0.04), rot=rot)
    add_box(bm, at(length - 0.02, t / 2), (w + 0.04, 0.06, t + 0.04), rot=rot)          # its cornice, against the wall
    add_box(bm, at(0.03, t / 2), (w + 0.02, 0.06, t), rot=rot)                          # its foot
    _obj('Collapse', bm, [m['pigeon']], coll)

    rnd = random.Random(226)
    heap, post, boards = bmesh.new(), bmesh.new(), bmesh.new()
    for k in range(34):                                                                   # parcels and cubbies under it
        y = rnd.uniform(y_lo + 0.15, 0.95)
        zt = max(0.1, z_at(y) - 0.3 - 0.05)
        sz = (rnd.uniform(0.18, 0.36), rnd.uniform(0.16, 0.32), rnd.uniform(0.1, 0.24))
        z = rnd.uniform(sz[2] / 2, max(sz[2] / 2, zt - sz[2] / 2))
        add_box(heap, (rnd.uniform(x0 - 0.05, x1 + 0.05), y, z), sz,
                rot=Matrix.Rotation(rnd.uniform(-0.6, 0.6), 4, 'Z') @ Matrix.Rotation(rnd.uniform(-0.3, 0.3), 4, 'X'))
    for k in range(12):                                                                   # spilled in front, off the lane
        sz = (rnd.uniform(0.16, 0.3), rnd.uniform(0.14, 0.26), rnd.uniform(0.08, 0.18))
        add_box(heap, (rnd.uniform(x0 - 0.1, x1 + 0.15), rnd.uniform(y_lo - 0.35, y_lo + 0.25), sz[2] / 2), sz,
                rot=Matrix.Rotation(rnd.uniform(-1, 1), 4, 'Z'))
    for k in range(60):                                                                   # letters, everywhere in it
        y = rnd.uniform(y_lo - 0.4, 0.9)
        zmax = max(0.02, z_at(y) - 0.36) if y > y_lo else 0.02
        add_box(post, (rnd.uniform(x0 - 0.2, x1 + 0.2), y, rnd.uniform(0.004, min(zmax, 0.6))), (0.16, 0.11, 0.003),
                rot=Matrix.Rotation(rnd.uniform(-3, 3), 4, 'Z') @ Matrix.Rotation(rnd.uniform(-0.5, 0.5), 4, 'X'))
    for k in range(7):                                                                    # broken boards
        p = Vector((rnd.uniform(x0 - 0.2, x1 + 0.2), rnd.uniform(y_lo - 0.2, 0.6), rnd.uniform(0.05, 0.4)))
        add_box(boards, p, (rnd.uniform(0.3, 0.7), 0.02, 0.14),
                rot=Matrix.Rotation(rnd.uniform(-1.2, 1.2), 4, 'Z') @ Matrix.Rotation(rnd.uniform(-0.8, 0.8), 4, 'Y'))
    _obj('CollapseHeap', heap, [m['paper']], coll)
    _obj('CollapseLetters', post, [m['letters']], coll)
    _obj('CollapseBoards', boards, [m['pigeon']], coll)

    # Water seeping out from under the wreck: the first sign of the flood.
    bm = bmesh.new()
    add_cyl(bm, (23.75, -0.15, 0.0), (23.75, -0.15, 0.003), 0.45, seg=24)
    add_cyl(bm, (24.25, 0.15, 0.0), (24.25, 0.15, 0.003), 0.3, seg=20)
    ob = _obj('CollapsePuddle', bm, [m['water']], coll)
    ob.scale = (1.0, 0.55, 1.0)
    ob.location = (0, 0, 0)
    d17_apply_scale(ob, (23.9, 0.0))


def d17_apply_scale(ob, pivot):
    """Bake an object's scale into its mesh about a world (x, y) pivot."""
    sx, sy, sz = ob.scale
    px, py = pivot
    me = ob.data
    for v in me.vertices:
        v.co.x = px + (v.co.x - px) * sx
        v.co.y = py + (v.co.y - py) * sy
        v.co.z *= sz
    ob.scale = (1, 1, 1)


def build_gantry(m, coll):
    """SortGantry: a steel walkway at 1.35 from the table's end to the weight room's doorway, resting on the
    fallen pigeonhole wall and bolted to the far wall. Its left end is torn off where it once ran on over the
    table. A handrail along its front; along its back too, past the wreck."""
    gx0, gx1, deck = GANTRY
    gy0, gy1 = GANTRY_Y
    _, _, z_at, _ = _slab_frame()
    cx, w = (gx0 + gx1) / 2, gx1 - gx0
    bm = bmesh.new()
    add_box(bm, (cx, (gy0 + gy1) / 2, deck - 0.015), (w, gy1 - gy0, 0.03), mat=0)          # the deck plate
    for k in range(10):                                                                     # treads
        y = gy0 + 0.03 + k * (gy1 - gy0 - 0.06) / 9
        add_box(bm, (cx, y, deck - 0.002), (w, 0.012, 0.006), mat=0)
    for y in (gy0 - 0.01, gy1 + 0.01):                                                      # stringers
        add_box(bm, (cx, y, deck - 0.1), (w, 0.03, 0.14), mat=0)
    for x in (22.5, 23.05, 23.6, 24.15, 24.7):                                              # bearers
        add_box(bm, (x, (gy0 + gy1) / 2, deck - 0.1), (0.05, gy1 - gy0, 0.1), mat=0)
    add_box(bm, (cx, gy0 - 0.03, deck + 0.04), (w, 0.012, 0.08), mat=1)                    # yellow toe board, front
    for x in (gx0 + 0.08, 23.0, 23.65, 24.3, gx1 - 0.08):                                  # front handrail
        add_box(bm, (x, gy0 - 0.02, deck + 0.45), (0.035, 0.035, 0.9), mat=0)
    add_cyl(bm, (gx0 + 0.06, gy0 - 0.02, deck + 0.9), (gx1 - 0.02, gy0 - 0.02, deck + 0.9), 0.02, seg=10, mat=0)
    add_cyl(bm, (gx0 + 0.08, gy0 - 0.02, deck + 0.46), (gx1 - 0.02, gy0 - 0.02, deck + 0.46), 0.013, seg=8, mat=0)
    for x in (23.65, 24.3, gx1 - 0.08):                                                    # back handrail, past the wreck
        add_box(bm, (x, gy1 + 0.02, deck + 0.45), (0.035, 0.035, 0.9), mat=0)
    add_cyl(bm, (23.55, gy1 + 0.02, deck + 0.9), (gx1 - 0.02, gy1 + 0.02, deck + 0.9), 0.02, seg=10, mat=0)
    # Where it rests on the wreck: jammed legs from the slab's face up to the front stringer.
    for x in (22.75, 23.35):
        zb = z_at(gy0 - 0.01) - 0.02
        add_box(bm, (x, gy0 - 0.01, (zb + deck - 0.17) / 2), (0.05, 0.05, deck - 0.17 - zb), mat=0)
    # At the far wall: brackets under the deck and two hangers from the ceiling.
    for y in (gy0, gy1):
        add_box(bm, (gx1 - 0.04, y, deck - 0.35), (0.08, 0.05, 0.5), mat=0)
        add_box(bm, (gx1 - 0.22, y, deck - 0.3), (0.42, 0.04, 0.04), mat=0, rot=Matrix.Rotation(-0.75, 4, 'Y'))
        add_cyl(bm, (24.2, y, CEIL - 0.28), (24.2, y, deck - 0.05), 0.01, seg=6, mat=0)
    # The torn left end: the back stringer bent down and back, a rail end twisted up.
    add_box(bm, (gx0 - 0.1, gy1 + 0.08, deck - 0.2), (0.28, 0.03, 0.12), mat=0,
            rot=Matrix.Rotation(-0.5, 4, 'Z') @ Matrix.Rotation(0.6, 4, 'Y'))
    add_cyl(bm, (gx0 + 0.06, gy0 - 0.02, deck + 0.9), (gx0 - 0.05, gy0 - 0.12, deck + 1.05), 0.02, seg=10, mat=0)
    _obj('SortGantry', bm, [m['steel'], m['yellow']], coll)


def build_set(dl01, m, coll):
    paint.make_textures()
    hall_materials(m)
    build_shell(m, coll)
    build_tube_station(m, coll)
    build_mail_slot(m, coll)
    build_tea_corner(m, coll)
    build_box(m, coll)
    build_table(m, coll)
    build_collapse(m, coll)
    build_gantry(m, coll)
    # The letter in D-17's claw (the game attaches it to his right wrist and shows it during PickUpLetter and
    # PostLetter; it takes the material of whichever letter he holds). Parked out of sight under the floor.
    letter_mesh('HeldLetter', letter_material('tube'), coll, loc=(TUBE[0], 0.0, -0.5))


# --------------------------------------------------------------------------
# D-17's clips: PickUpLetter and PostLetter
#
# The clips are authored from the letter: each key says where the envelope is (its centre and how it lies, in
# rig space: D-17 faces -y, his right is -x), and the right claw is put where it has to be to hold it there.
# The letter rides in the claw at a fixed offset from the right wrist bone (HELD_OFFSET), pinched by its long
# edge between the claw's tips, tilted CLAW_TILT off the claw's line so the claw can take it off the floor.
# --------------------------------------------------------------------------

CLAW_TIP = 0.105                      # wrist to the closed claw's tips (ik_hand.R head, rest axes)
PINCH = 0.015                         # how much of the letter is between the tips
CLAW_TILT = 20.0                      # degrees between the claw's line and the letter

# Mesh axes (letter_mesh: x long side, y toward the pinched edge, z front) to the wrist bone's axes:
# the long side across the claw (bone y), the pinched edge toward the wrist (bone z), the front facing bone x
# (the axis the claw's two fingers close along), then tilted about bone y.
_PERM = Matrix(((0, 0, 1), (1, 0, 0), (0, 1, 0)))


def held_offset():
    """(rotation 3x3, position) of the held letter in the right wrist bone's rest frame (Blender bone axes,
    which match the armature's: x his left, y back, z up, with the claw hanging along -z)."""
    rot = Matrix.Rotation(math.radians(-CLAW_TILT), 3, 'Y') @ _PERM
    pos = Vector((0, 0, -CLAW_TIP)) + rot @ Vector((0, -(LETTER[1] / 2 - PINCH), 0))
    return rot, pos


def _letter_rot(u, n):
    """Mesh-to-rig rotation for a letter whose long side runs along u and whose front faces n."""
    n = Vector(n).normalized()
    u = (Vector(u) - n * Vector(u).dot(n)).normalized()
    return Matrix((u, n.cross(u), n)).transposed()


def _hand_for(c, L):
    """Right wrist position and rotation (rig space) that hold the letter at centre c with rotation L."""
    ra, pa = held_offset()
    h = L @ ra.transposed()
    return Vector(c) - h @ pa, h


class _Right:
    """Turns rig-space right-wrist targets into Clip.pose hand offsets and hand_rot for a body pose."""
    REST_ROT = (-24.0, -6.0, -10.0)

    def __init__(self, dl01):
        import build_dl02
        self.dl01, self.delta = dl01, build_dl02.body_delta
        self.prev = None

    def rest(self, body, body_rot, carry=None):
        """The right wrist's rig-space position and rotation in the rest (carry) pose."""
        B = self.delta(body, body_rot)
        w = B @ (self.dl01.REST_WRIST[-1] + (carry if carry is not None else self.dl01.CARRY[-1]))
        h = B.to_3x3() @ Euler([math.radians(a) for a in self.REST_ROT], 'XYZ').to_matrix()
        return w, h

    def pose(self, w, h, body, body_rot):
        B = self.delta(body, body_rot)
        loc = B.inverted() @ w - self.dl01.REST_WRIST[-1]
        e = (B.to_3x3().transposed() @ h).to_euler('XYZ', self.prev) if self.prev else (B.to_3x3().transposed() @ h).to_euler('XYZ')
        self.prev = e
        return loc, tuple(math.degrees(a) for a in e)


def _mix(a, b, k):
    """Blend two (wrist, rotation) holds."""
    qa, qb = a[1].to_quaternion(), b[1].to_quaternion()
    return a[0].lerp(b[0], k), qa.slerp(qb, k).to_matrix()


def _bez(p0, p1, p2, t):
    t = max(0.0, min(1.0, t))
    return p0 * (1 - t) ** 2 + p1 * (2 * (1 - t) * t) + p2 * t * t


# Where the letter is at the clips' key frames (rig space). The game swaps the floor letter for HeldLetter at
# PICK_GRAB and hides it, stowed in his chest, at PICK_STOW; PostLetter shows it at POST_SHOW and the slot
# takes it at POST_IN.
PICK_FRAMES, PICK_GRAB, PICK_STOW = 30, 12, 26
POST_FRAMES, POST_SHOW, POST_IN = 40, 4, 22
PICK_AT = Vector((-0.12, -0.25, LETTER[2] / 2))       # the letter on the floor: centre (flat, front up, long side across)
POST_X = -0.15                                         # his right-hand offset from the slot's centre (rig x)
SLOT_AHEAD = 0.30                                      # the slot plate's face, ahead of his root
SLOT_Z = 0.55


def _pick_letter_poses():
    floor = _letter_rot((1, 0, 0), (0, 0, 1))
    look_c = Vector((-0.12, -0.31, 0.47))
    look_n = (Vector((0.0, -0.17, 0.63)) - look_c)                  # front toward his eyes
    look = _letter_rot((0, 0, -1), look_n)
    chest_c = Vector((-0.035, -0.229, 0.385))
    chest = _letter_rot((0, 0, 1), (0, -1, 0))
    return floor, (look_c, look), (chest_c, chest)


def _post_letter_poses():
    tilt = math.radians(10.0)                                       # the far edge a little up as it goes in
    fwd = Vector((0, -math.cos(tilt), math.sin(tilt)))
    n = Vector((0, 0, -1))
    n = (n - fwd * n.dot(fwd)).normalized()
    slot = _letter_rot((-1, 0, 0), n)
    return slot, fwd


def clip_pick_up_letter(dl01, arm):
    """He bends, takes the letter off the floor 0.25 ahead with his right claw (pinching its near edge),
    straightens up and holds it in front of his face to look at it, head on one side, then presses it to his
    chest window, where it is stowed, and lowers the claw."""
    track, spring, Clip = dl01.track, dl01.spring, dl01.Clip
    c = Clip(arm, 'PickUpLetter', PICK_FRAMES)
    R = _Right(dl01)
    floor, (look_c, look), (chest_c, chest) = _pick_letter_poses()
    for frame in range(1, PICK_FRAMES + 1):
        f = frame - 1
        squat = track([(0, 0), (8, 1), (13, 1), (19, 0)], f)
        body = (0, -0.045 * squat + 0.01 * track([(20, 0), (24, 1), (28, 0)], f), -0.1 * squat)
        rot = (14 * squat + track([(17, 0), (20, -3), (26, -3), (30, 0)], f), 0, -6 * squat)
        rest = R.rest(body, rot)
        grab = _hand_for(PICK_AT, floor)
        pre = _hand_for(PICK_AT + Vector((-0.02, 0.05, 0.05)), floor)
        if f <= 8:
            k = smoothstep(f / 8)
            hold = _mix(rest, pre, k)
            hold = (_bez(rest[0], rest[0].lerp(pre[0], 0.5) + Vector((-0.06, 0, 0.04)), pre[0], k), hold[1])
        elif f <= PICK_GRAB - 1:
            hold = _mix(pre, grab, smoothstep((f - 8) / (PICK_GRAB - 1 - 8)))
        elif f <= PICK_GRAB:
            hold = grab
        elif f <= 18:
            k = smoothstep((f - PICK_GRAB) / (18 - PICK_GRAB))
            up = _hand_for(look_c, look)
            via = (grab[0] + up[0]) / 2 + Vector((-0.08, 0.0, 0.0))
            hold = (_bez(grab[0], via, up[0], k), _mix(grab, up, k)[1])
        elif f <= 21:
            hold = _hand_for(look_c + Vector((0, 0, 0.006 * math.sin(math.pi * (f - 18) / 3))), look)
        elif f <= 24:
            k = smoothstep((f - 21) / 3)
            a, b = _hand_for(look_c, look), _hand_for(chest_c, chest)
            via = (a[0] + b[0]) / 2 + Vector((-0.04, -0.05, 0.0))
            hold = (_bez(a[0], via, b[0], k), _mix(a, b, k)[1])
        elif f <= PICK_STOW:
            hold = _hand_for(chest_c + Vector((0, 0.004 * (f - 24), 0)), chest)
        else:
            hold = _mix(_hand_for(chest_c, chest), rest, smoothstep((f - PICK_STOW) / (PICK_FRAMES - 1 - PICK_STOW)))
        loc, hr = R.pose(hold[0], hold[1], body, rot)
        hands = {1: dl01.CARRY[1] + Vector((0, 0.01 * squat, 0.0)), -1: loc}
        claw_r = track([(0, CLAW_REST_OPEN['R']), (6, 26), (PICK_GRAB - 1, 22), (PICK_GRAB, 3), (PICK_STOW - 1, 3),
                        (PICK_STOW + 1, 14), (PICK_FRAMES - 1, CLAW_REST_OPEN['R'])], f)
        head = (track([(0, 0), (6, 26), (13, 30), (17, 10), (21, 10), (24, 22), (27, 18), (30, 0)], f),
                track([(15, 0), (18, 16), (21, 16), (23, 0)], f),
                track([(13, 0), (17, -24), (21, -24), (23, 0)], f))
        antenna = [(track([(0, 0), (6, 8), (13, 6), (17, -16), (21, -18), (25, 6), (30, 0)], f) * (0.8 + 0.15 * i)
                    + spring(f, PICK_GRAB, 5) + spring(f, 25, -6), 0) for i in range(3)]
        feet = {'R': ((0, 0, 0), (0, 0, 0)), 'L': ((0, 0.02 * squat, 0), (0, 0, 0))}
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, feet=feet, hands=hands,
               hand_rot={'L': (-24, 6, 10), 'R': hr}, claws={'L': CLAW_REST_OPEN['L'], 'R': claw_r},
               elbows={'R': min(1.0, 1.6 * track([(0, 0), (6, 1), (PICK_STOW + 1, 1), (PICK_FRAMES - 1, 0)], f))})
    c.done()


def clip_post_letter(dl01, arm):
    """Facing the slot, 0.3 ahead at 0.55: he takes the letter from his chest, raises it to the slot, leans in
    and pushes it in, lets go; a moment's pause, then a pleased little bob."""
    track, spring, Clip = dl01.track, dl01.spring, dl01.Clip
    c = Clip(arm, 'PostLetter', POST_FRAMES)
    R = _Right(dl01)
    _, _, (chest_c, chest) = _pick_letter_poses()
    slot, fwd = _post_letter_poses()
    half = LETTER[1] / 2
    # The letter's centre: at the mouth with its far edge just in, then pushed in until its near edge is at the
    # plate (the claw's tips then at the plate's face).
    mouth = Vector((POST_X, -SLOT_AHEAD + half - 0.025, SLOT_Z))
    inside = mouth + fwd * 0.07
    ready = mouth - fwd * 0.015 + Vector((-0.02, 0, -0.01))
    for frame in range(1, POST_FRAMES + 1):
        f = frame - 1
        reach = track([(4, 0), (12, 1), (22, 1), (27, 0.6)], f)
        bob = track([(28, 0), (31, -0.022), (34, 0.004), (37, -0.004), (40, 0)], f)
        body = (0, 0.03 * reach - 0.012 * track([(13, 0), (20, 1), (24, 0)], f),
                0.008 * reach + bob)
        rot = (-9 * reach + 5 * track([(13, 0), (20, 1), (24, 0)], f) + track([(28, 0), (31, 5), (35, -2), (40, 0)], f), 0, 0)
        rest = R.rest(body, rot)
        at_chest = _hand_for(chest_c, chest)
        if f <= POST_SHOW:
            k = smoothstep(f / POST_SHOW)
            via = (rest[0] + at_chest[0]) / 2 + Vector((-0.05, -0.06, 0.0))      # round the window's corner
            hold = (_bez(rest[0], via, at_chest[0], k), _mix(rest, at_chest, k)[1])
        elif f <= 13:
            k = smoothstep((f - POST_SHOW) / (13 - POST_SHOW))
            b = _hand_for(ready, slot)
            via = (at_chest[0] + b[0]) / 2 + Vector((-0.08, -0.02, 0.0))
            hold = (_bez(at_chest[0], via, b[0], k), _mix(at_chest, b, k)[1])
        elif f <= 15:
            hold = _hand_for(ready.lerp(mouth, smoothstep((f - 13) / 2)), slot)
        elif f <= POST_IN - 1:
            hold = _hand_for(mouth.lerp(inside, smoothstep((f - 15) / (POST_IN - 1 - 15))), slot)
        elif f <= 26:
            out = inside - fwd * 0.05 * smoothstep((f - (POST_IN - 1)) / 5)
            hold = _hand_for(out, slot)
        else:
            a = _hand_for(inside - fwd * 0.05, slot)
            k = smoothstep((f - 26) / (POST_FRAMES - 1 - 26))
            via = (a[0] + rest[0]) / 2 + Vector((-0.07, 0.0, 0.0))
            hold = (_bez(a[0], via, rest[0], k), _mix(a, rest, k)[1])
        loc, hr = R.pose(hold[0], hold[1], body, rot)
        hands = {1: dl01.CARRY[1] + Vector((0, 0.015 * reach, 0.01 * reach)), -1: loc}
        claw_r = track([(0, CLAW_REST_OPEN['R']), (POST_SHOW, 3), (POST_IN - 1, 3), (POST_IN + 1, 22),
                        (30, 18), (POST_FRAMES - 1, CLAW_REST_OPEN['R'])], f)
        head = (track([(0, 0), (4, 18), (8, 4), (13, -2), (22, -2), (26, 4), (31, -10), (35, 6), (40, 0)], f),
                track([(22, 0), (25, 10), (29, 10), (32, 0)], f), 0)
        antenna = [(track([(0, 0), (6, -6), (20, -6), (24, -14), (28, -12), (40, 0)], f) * (0.8 + 0.15 * i)
                    + spring(f, POST_IN, -7) + spring(f, 31, 12 * (1 + 0.3 * i), decay=5, freq=1.3), 0) for i in range(3)]
        tiptoe = track([(14, 0), (19, 1), (24, 0)], f)
        feet = {side: ((0, 0, 0), (-7 * tiptoe, 0, 0)) for side, _ in SIDES}
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, feet=feet, hands=hands,
               hand_rot={'L': (-24, 6, 10), 'R': hr}, claws={'L': CLAW_REST_OPEN['L'], 'R': claw_r},
               elbows={'R': track([(0, 0), (3, 1), (34, 1), (POST_FRAMES - 1, 0)], f)})
    c.done()


def add_clips(dl01, arm):
    clip_pick_up_letter(dl01, arm)
    clip_post_letter(dl01, arm)
