"""DL-02 The Weight of the Job: the set, D-17's carry and push clips, and the dormant couriers.

Called from art/dl01/build_dl01.py, which builds chapter 1 as one continuous level. DL-02 continues
straight on from the DL-01 bulkhead. D-17 walks through its door and along a service passage behind
the wall, then steps out of a second doorway into the weighing room. Beyond the gate is the
recharge hall.

Coordinates as in DL-01: metres, Blender Z up, the playable plane at y = 0, travel along +x.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

import build_d17 as d17
from build_d17 import (add_box, add_cyl, add_sphere, add_torus, rounded_box, emission_material,
                       worn_material, smoothstep, ease_back, SIDES, CLAW_REST_OPEN)

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')

# Shared with the game (game/undelivered/index.html keeps the same numbers).
ROOM_X0 = 12.1                       # the hall's end wall; DL-02 starts on its far side
WALL_X1 = 12.45                      # the bulkhead panel runs on to here, hiding the passage
DOOR2 = (12.85, 13.55, 1.05)         # the doorway D-17 steps back out of: x0, x1, height
PASSAGE_Y = 1.25                     # his line along the service passage
WEIGHT_X = 12.62                     # the sorting weight, by the stand
TROLLEY_X = 14.55                    # trolley centre; deck half-length, deck top, handle height
TROLLEY_HALF, TROLLEY_DECK, TROLLEY_HANDLE = 0.28, 0.16, 0.44
PLATE = (15.8, 16.55)                # floor plate x0, x1
GATE_X, GATE_W, GATE_H = 17.6, 1.1, 1.25
HALL2_X1 = 26.9                      # recharge hall right wall; the lane leaves through it
ROWS_Y = (1.65, 2.95, 4.25, 5.55, 6.85)
NEAR_ROW_Y = 0.9                     # the row right behind the lane
NUDGE_SLOT = 2                       # near-row slot of the courier D-17 can try to wake
LEFT_WALL = (12.0, 12.32)             # the weighing room's left wall (the Sorting Hall's right): x0, x1
GANTRY_DOOR = (-0.42, 0.42, 1.35, 2.4)  # the gantry doorway: y0, y1 (cut open to the front of the wall), sill, head (the deck is at 1.35)
GRIP = (0.29, 0.21)                  # the weight's bail: forward of D-17 when lifting, height on the weight
WRIST_ABOVE_GRIP = 0.07


def _obj(name, bm, mats, coll, sharp=35):
    return d17.mesh_object(name, bm, mats, coll, sharp=sharp)


def _textured_plane(name, size, center, mat, coll, rot=None):
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


def _image_material(name, path):
    mat, nt, bsdf = d17._new_material(name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.6
    return mat


# --------------------------------------------------------------------------
# Painted signs
# --------------------------------------------------------------------------

def make_gate_sign(path):
    """The rule, without words: a load on the plate lifts the gate."""
    from PIL import Image, ImageDraw, ImageFilter
    w, h = 768, 512
    img = Image.new('RGB', (w, h), (196, 168, 60))
    d = ImageDraw.Draw(img)
    ink = (24, 22, 18)
    d.rectangle((14, 14, w - 14, h - 14), outline=ink, width=12)
    # The plate with a weight on it.
    d.rectangle((70, 380, 330, 404), fill=ink)
    d.ellipse((150, 250, 250, 378), fill=ink)
    d.arc((172, 206, 228, 270), 180, 360, fill=ink, width=14)
    for k in range(3):
        d.line((110 + k * 90, 418, 140 + k * 90, 448), fill=ink, width=10)
    # The arrow, then the gate raised over a gap.
    d.polygon([(360, 300), (440, 300), (440, 270), (500, 320), (440, 370), (440, 340), (360, 340)], fill=ink)
    d.rectangle((540, 120, 556, 404), fill=ink)
    d.rectangle((680, 120, 696, 404), fill=ink)
    for k in range(6):
        d.rectangle((560 + k * 22, 120, 570 + k * 22, 250), fill=ink)
    d.rectangle((556, 240, 680, 254), fill=ink)
    d.polygon([(618, 150), (648, 190), (588, 190)], fill=(196, 168, 60))
    d.text((40, 40), 'GATE 4', fill=ink)
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def make_gauge_face(path):
    """Load gauge on the gate post: needle from 0 (left) to full (right), the green band is enough."""
    from PIL import Image, ImageDraw, ImageFilter
    s = 256
    img = Image.new('RGB', (s, s), (206, 198, 172))
    d = ImageDraw.Draw(img)
    ink = (28, 26, 22)
    c = s / 2
    d.rectangle((4, 4, s - 4, s - 4), outline=ink, width=8)

    def at(load, r):
        a = math.radians(-100 + 200 * load)        # clockwise from straight up
        return c + r * math.sin(a), c + 12 - r * math.cos(a)
    for k in range(60):
        load = 0.68 + 0.32 * k / 59
        x, y = at(load, 92)
        d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(60, 140, 70))
    for k in range(11):
        x0, y0 = at(k / 10, 100)
        x1, y1 = at(k / 10, 84 if k % 5 == 0 else 92)
        d.line((x0, y0, x1, y1), fill=ink, width=6 if k % 5 == 0 else 3)
    d.ellipse((c - 12, c, c + 12, c + 24), fill=ink)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


# --------------------------------------------------------------------------
# The set
# --------------------------------------------------------------------------

def dl02_materials(m):
    m['iron'] = worn_material('CastIron', base=(0.035, 0.034, 0.032), dirt=(0.05, 0.03, 0.018),
                              chip=(0.13, 0.12, 0.1), rough=0.75, chip_rough=0.45, metallic=0.5)
    m['plate'] = worn_material('PlateSteel', base=(0.11, 0.115, 0.11), dirt=(0.06, 0.04, 0.025),
                               chip=(0.2, 0.19, 0.17), rough=0.55, chip_rough=0.4, metallic=0.7)
    m['platebulb'] = emission_material('PlateBulb', (1.0, 0.9, 0.75), 0.0)
    m['rowlight'] = [emission_material(f'RowLight{i}', (0.8, 0.92, 0.95), 0.0) for i in range(len(ROWS_Y) + 1)]
    m['passage'] = emission_material('PassageGlow', (0.6, 0.85, 0.72), 0.0)
    m['gantrylamp'] = emission_material('GantryLamp', (1.0, 0.76, 0.46), 0.0)


def build_passage(m, coll):
    """The service passage behind the bulkhead: back wall, roof, end caps, and the second doorway."""
    x0, x1, dh = DOOR2
    by = 0.62
    bm = bmesh.new()
    add_box(bm, (11.7, 1.67, 0.72), (4.3, 0.1, 1.44))                     # back wall
    add_box(bm, (11.7, 1.3, 1.49), (4.3, 0.84, 0.1))                      # roof
    for x in (9.53, 13.87):
        add_box(bm, (x, 1.3, 0.72), (0.1, 0.84, 1.44))
    obj = _obj('Passage', bm, [m['wall']], coll)
    # The wall D-17 steps out through is now the Sorting Hall's back wall (art/sorting_hall); its doorway
    # keeps this frame and glow. The weighing room's own back wall moves with the room (build_weigh_room).
    bm = bmesh.new()
    add_box(bm, (x0 - 0.04, by - 0.02, dh / 2), (0.08, 0.08, dh + 0.08))
    add_box(bm, (x1 + 0.04, by - 0.02, dh / 2), (0.08, 0.08, dh + 0.08))
    add_box(bm, ((x0 + x1) / 2, by - 0.02, dh + 0.06), (x1 - x0 + 0.16, 0.1, 0.12))
    _obj('Door2Frame', bm, [m['yellow']], coll)
    bm = bmesh.new()
    add_box(bm, ((x0 + x1) / 2, 1.6, 0.7), (x1 - x0 + 0.6, 0.04, 1.4))
    _obj('PassageGlow', bm, [m['passage']], coll)
    return obj


def build_room_walls(m, coll):
    """The weighing room's back wall (seamed like the bulkhead's, as it was when it held DL-01's doorway) and
    its left wall, shared with the Sorting Hall, with the gantry doorway D-17 comes in by: x 12.0 to 12.32,
    1.35 to 2.4 high, and a warm lamp over it on the hall's side (GantryLamp, the hall's brightest point)."""
    lx0, lx1 = LEFT_WALL
    _, gy1, sill, head = GANTRY_DOOR
    by = 0.62
    bm = bmesh.new()
    a0, a1 = lx1, GATE_X - 0.05
    n = max(1, round((a1 - a0) / 0.95))
    for k in range(n):
        w = (a1 - a0) / n
        rounded_box((w - 0.03, 0.3, 2.58), (a0 + w * (k + 0.5), by + 0.15, 1.3), p=12, cuts=8,
                    dents=((0.008, 3.0),), seed=71 + k, bm=bm, mat=0)
    _obj('WeighRoomWall', bm, [m['wall']], coll)
    # The left wall runs from in front of the lane (cut away there, like the gate's partition, so the side view
    # sees through the doorway) to behind the Sorting Hall's back wall, and up to its ceiling.
    y_front, y_back, top = -0.6, 1.25, 4.65
    cx, t = (lx0 + lx1) / 2, lx1 - lx0
    bm = bmesh.new()
    add_box(bm, (cx, (y_front + y_back) / 2, sill / 2), (t, y_back - y_front, sill))
    add_box(bm, (cx, (y_front + y_back) / 2, (head + top) / 2), (t, y_back - y_front, top - head))
    add_box(bm, (cx, (gy1 + y_back) / 2, (sill + head) / 2), (t, y_back - gy1, head - sill))     # the back jamb
    _obj('WeighRoomLeftWall', bm, [m['wall']], coll)
    bm = bmesh.new()                                    # a steel frame round the opening, both faces
    for x in (lx0 - 0.015, lx1 + 0.015):
        add_box(bm, (x, gy1 + 0.03, (sill + head) / 2), (0.03, 0.06, head - sill))
        add_box(bm, (x, (y_front + gy1) / 2 + 0.03, head + 0.03), (0.03, gy1 - y_front + 0.06, 0.06))
    add_box(bm, (cx, (y_front + y_back) / 2, head + 0.03), (t + 0.06, y_back - y_front, 0.06))    # the lintel
    add_box(bm, (cx, (y_front + gy1) / 2, sill - 0.01), (t + 0.06, gy1 - y_front, 0.02))          # the sill plate
    add_box(bm, (cx, y_front - 0.015, (head + top) / 2), (t + 0.04, 0.03, top - head))             # edge trims on the cut
    add_box(bm, (cx, y_front - 0.015, sill / 2), (t + 0.04, 0.03, sill))
    _obj('GantryDoorFrame', bm, [m['steel']], coll)
    bm = bmesh.new()                                    # hazard stripes along the sill's cut edge and its hall side
    for k in range(9):
        add_box(bm, (lx0 - 0.032, y_front + 0.06 + k * (gy1 - y_front - 0.12) / 8, sill - 0.05), (0.004, 0.05, 0.07),
                rot=Matrix.Rotation(0.6, 4, 'X'))
    _obj('GantryDoorStripes', bm, [m['yellow']], coll)
    # The lamp over the doorway, on the hall's side of the wall: a caged bulkhead light.
    lz = head + 0.3
    bm = bmesh.new()
    add_box(bm, (lx0 - 0.03, 0.0, lz), (0.06, 0.2, 0.16))
    add_cyl(bm, (lx0 - 0.06, 0.0, lz), (lx0 - 0.11, 0.0, lz), 0.065, 0.06, seg=16)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        add_cyl(bm, (lx0 - 0.06, 0.06 * math.cos(a), lz + 0.06 * math.sin(a)), (lx0 - 0.16, 0.035 * math.cos(a), lz + 0.035 * math.sin(a)), 0.005, seg=4)
    add_cyl(bm, (lx0 - 0.03, 0.12, lz + 0.05), (lx0 - 0.03, 0.9, lz + 0.05), 0.01, seg=6)        # its conduit, back along the wall
    _obj('GantryLampFixture', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_sphere(bm, (lx0 - 0.13, 0.0, lz), 0.045, seg=14, scale=(0.8, 1, 1))
    _obj('GantryLamp', bm, [m['gantrylamp']], coll)


def build_weigh_room(m, coll):
    """The weighing room: the sorting weight by its stand, the trolley, the plate, the gate."""
    rnd = random.Random(202)
    # Ceiling, low over the room.
    bm = bmesh.new()
    rounded_box((GATE_X + 0.15 - LEFT_WALL[0], 2.6, 0.16), ((LEFT_WALL[0] + GATE_X + 0.15) / 2, -0.35, 2.68), p=5, cuts=12,
                dents=((0.02, 1.5), (0.008, 6.0)), seed=12, bm=bm, mat=0)
    _obj('WeighRoomCeiling', bm, [m['concrete']], coll)
    build_room_walls(m, coll)

    # The sorting weight: a cast-iron bell weight with a bail handle, origin at its base.
    bm = bmesh.new()
    add_cyl(bm, (0, 0, 0.0), (0, 0, 0.02), 0.088, 0.09, seg=24)
    add_cyl(bm, (0, 0, 0.02), (0, 0, 0.12), 0.09, 0.075, seg=24)
    add_cyl(bm, (0, 0, 0.12), (0, 0, 0.15), 0.075, 0.035, seg=24)
    add_torus(bm, (0, 0, 0.165), (1, 0, 0), 0.042, 0.009, seg=20, rseg=6)
    ob = _obj('SortWeight', bm, [m['red']], coll)              # red: something he can pick up
    ob.location = (WEIGHT_X, 0, 0)
    bm = bmesh.new()
    add_cyl(bm, (0, 0, 0.07), (0, 0, 0.09), 0.0905, 0.0885, seg=24)
    ob = _obj('SortWeightBand', bm, [m['paper']], coll)
    ob.location = (WEIGHT_X, 0, 0)
    # Its stand, with three smaller weights still on it.
    bm = bmesh.new()
    for x in (12.3, 12.62):
        for y in (0.3, 0.52):
            add_box(bm, (x, y, 0.22), (0.03, 0.03, 0.44))
    for z in (0.2, 0.42):
        add_box(bm, (12.46, 0.41, z), (0.38, 0.26, 0.02))
    _obj('WeightStand', bm, [m['steel']], coll)
    bm = bmesh.new()
    for x, z, r in ((12.38, 0.43, 0.05), (12.52, 0.43, 0.04), (12.45, 0.21, 0.06)):
        add_cyl(bm, (x, 0.41, z), (x, 0.41, z + r * 1.4), r, r * 0.8, seg=16)
        add_torus(bm, (x, 0.41, z + r * 1.6), (1, 0, 0), r * 0.45, 0.005, seg=12, rseg=4)
    _obj('SmallWeights', bm, [m['iron']], coll)

    # The trolley: a flatbed with a push bar at its left end; origin on the floor at its centre.
    h, d, hh = TROLLEY_HALF, TROLLEY_DECK, TROLLEY_HANDLE
    bm = bmesh.new()
    add_box(bm, (0, 0, d - 0.02), (2 * h, 0.38, 0.04))
    for x in (-h + 0.01, h - 0.01):
        add_box(bm, (x, 0, d + 0.015), (0.02, 0.38, 0.03))
    for y in (-0.15, 0.15):
        add_cyl(bm, (-h + 0.01, y, d), (-h - 0.02, y, hh), 0.011, seg=8)
    add_cyl(bm, (-h - 0.02, -0.17, hh), (-h - 0.02, 0.17, hh), 0.014, seg=10)
    for x in (-h + 0.06, h - 0.06):
        for y in (-0.14, 0.14):
            add_box(bm, (x, y, 0.09), (0.03, 0.03, 0.06))
    ob = _obj('Trolley', bm, [m['depot_green']], coll)
    ob.location = (TROLLEY_X, 0, 0)
    bm = bmesh.new()
    add_cyl(bm, (-h - 0.02, -0.12, hh), (-h - 0.02, 0.12, hh), 0.017, seg=10)
    ob = _obj('TrolleyGrip', bm, [m['red']], coll)
    ob.location = (TROLLEY_X, 0, 0)
    for i, (x, y) in enumerate(((-h + 0.06, -0.14), (-h + 0.06, 0.14), (h - 0.06, -0.14), (h - 0.06, 0.14))):
        bm = bmesh.new()
        add_cyl(bm, (0, -0.012, 0), (0, 0.012, 0), 0.04, seg=16)
        add_box(bm, (0.025, 0, 0), (0.02, 0.026, 0.01))
        ob = _obj(f'TrolleyWheel{i}', bm, [m['rubber']], coll)
        ob.location = (TROLLEY_X + x, y, 0.04)

    # Floor plate in a hazard border; origin at its top centre so the game can press it down.
    px0, px1 = PLATE
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.015), (px1 - px0 - 0.03, 0.66, 0.03))
    for k in range(10):
        add_box(bm, (-(px1 - px0) / 2 + 0.06 + k * 0.07, 0, 0.001), (0.012, 0.6, 0.002),
                rot=Matrix.Rotation(0.5 if k % 2 else -0.5, 4, 'Z'))
    ob = _obj('FloorPlate', bm, [m['plate']], coll)
    ob.location = ((px0 + px1) / 2, 0, 0.004)
    bm = bmesh.new()
    for x in (px0 - 0.01, px1 + 0.01):
        add_box(bm, (x, 0, 0.002), (0.05, 0.74, 0.004))
    for y in (-0.36, 0.36):
        add_box(bm, ((px0 + px1) / 2, y, 0.002), (px1 - px0 + 0.07, 0.05, 0.004))
    _obj('PlateBorder', bm, [m['yellow']], coll)
    # The linkage: a floor channel from the plate to the gate, then a rod up the post.
    bm = bmesh.new()
    add_box(bm, ((px1 + GATE_X) / 2, 0.47, 0.006), (GATE_X - px1, 0.08, 0.012))
    add_cyl(bm, (GATE_X - 0.06, 0.6, 0.02), (GATE_X - 0.06, 0.6, 1.45), 0.008, seg=6)
    add_cyl(bm, (GATE_X - 0.06, 0.66, 1.5), (GATE_X - 0.06, 0.54, 1.5), 0.06, seg=20)
    _obj('PlateLinkage', bm, [m['steel']], coll)

    # Gate: a portcullis of bars across the lane, origin at the floor so the game can lift it.
    bm = bmesh.new()
    n = 11
    for k in range(n):
        y = -GATE_W / 2 + 0.05 + k * (GATE_W - 0.1) / (n - 1)
        add_box(bm, (0, y, GATE_H / 2), (0.022, 0.022, GATE_H))
    for z in (0.05, GATE_H * 0.55, GATE_H - 0.03):
        add_box(bm, (0, 0, z), (0.035, GATE_W - 0.04, 0.035))
    ob = _obj('Gate', bm, [m['shutter']], coll)
    ob.location = (GATE_X, 0, 0)
    # The partition the gate runs in: posts, header, and the wall above.
    bm = bmesh.new()
    for y in (-GATE_W / 2 - 0.04, GATE_W / 2 + 0.04):
        add_box(bm, (GATE_X, y, 0.75), (0.1, 0.07, 1.5))
    add_box(bm, (GATE_X, 0.0, GATE_H + 0.1), (0.12, GATE_W + 0.16, 0.12))
    _obj('GateFrame', bm, [m['yellow']], coll)
    bm = bmesh.new()
    add_box(bm, (GATE_X, 0.15, 3.0), (0.14, 1.55, 3.4))
    add_box(bm, (GATE_X, 0.75, 0.75), (0.14, 0.34, 1.5))
    _obj('GatePartition', bm, [m['wall']], coll)
    # Load gauge on the near post, facing the camera.
    gauge = os.path.join(TEX, 'gate_gauge.png')
    if not os.path.exists(gauge):
        make_gauge_face(gauge)
    gy = -GATE_W / 2 - 0.08
    bm = bmesh.new()
    add_box(bm, (GATE_X, gy + 0.02, 1.02), (0.2, 0.04, 0.2))
    _obj('GaugeBox', bm, [m['steel']], coll)
    _textured_plane('GaugeFace', (0.17, 0.17), (GATE_X, gy - 0.001, 1.02), _image_material('GaugeFaceMat', gauge), coll)
    bm = bmesh.new()
    add_box(bm, (0, 0, 0.03), (0.006, 0.004, 0.065))
    add_cyl(bm, (0, -0.003, 0), (0, 0.003, 0), 0.008, seg=10)
    ob = _obj('GateNeedle', bm, [m['red']], coll)
    ob.location = (GATE_X, gy - 0.006, 1.012)

    # The sign over the plate, and a caged lamp.
    sign = os.path.join(TEX, 'gate_sign.png')
    if not os.path.exists(sign):
        make_gate_sign(sign)
    _textured_plane('GateSign', (0.48, 0.32), (16.25, 0.605, 1.45), _image_material('GateSignMat', sign), coll)
    bm = bmesh.new()
    add_box(bm, (16.25, 0.612, 1.45), (0.52, 0.01, 0.36))
    _obj('GateSignBack', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_cyl(bm, (16.3, -0.05, 2.6), (16.3, -0.05, 2.25), 0.004, seg=6)
    add_cyl(bm, (16.3, -0.05, 2.25), (16.3, -0.05, 2.15), 0.05, 0.09, seg=16)
    for k in range(6):
        a = k * math.pi / 3
        add_cyl(bm, (16.3 + 0.08 * math.cos(a), -0.05 + 0.08 * math.sin(a), 2.15),
                (16.3 + 0.05 * math.cos(a), -0.05 + 0.05 * math.sin(a), 2.06), 0.003, seg=4)
    _obj('PlateLampFixture', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_sphere(bm, (16.3, -0.05, 2.12), 0.03, seg=12)
    _obj('PlateLampBulb', bm, [m['platebulb']], coll)

    # A big platform scale against the wall, and parcels left where they were weighed.
    bm = bmesh.new()
    add_box(bm, (14.05, 0.4, 0.04), (0.56, 0.36, 0.08))
    add_box(bm, (14.05, 0.52, 0.55), (0.06, 0.06, 1.0))
    add_box(bm, (14.05, 0.5, 1.1), (0.26, 0.1, 0.26))
    _obj('PlatformScale', bm, [m['depot_green']], coll)
    _textured_plane('ScaleFace', (0.2, 0.2), (14.05, 0.449, 1.1), bpy.data.materials['GaugeFaceMat'], coll)
    bm = bmesh.new()
    for x, y, sz in ((13.95, 0.38, (0.22, 0.18, 0.14)), (14.15, 0.42, (0.16, 0.14, 0.1)), (15.0, 0.48, (0.2, 0.2, 0.12)),
                     (15.2, 0.45, (0.14, 0.16, 0.09)), (17.1, 0.45, (0.18, 0.2, 0.14))):
        z = sz[2] / 2 + (0.08 if x < 14.3 else 0)
        add_box(bm, (x, y, z), sz, rot=Matrix.Rotation(rnd.uniform(-0.4, 0.4), 4, 'Z'))
    _obj('WeighParcels', bm, [m['paper']], coll)


def build_recharge_hall(m, coll):
    """Rows of recharge racks, one cradle after another, under strip lights that have been off for years."""
    rnd = random.Random(17)
    bm = bmesh.new()
    add_box(bm, (22.3, 9.2, 3.2), (9.6, 0.2, 6.4))                        # back wall
    add_box(bm, (HALL2_X1, 4.9, 3.2), (0.2, 8.6, 6.4))                     # right wall behind the lane
    add_box(bm, (HALL2_X1, -0.2, 3.9), (0.2, 1.65, 5.0))                   # header over the lane exit
    add_box(bm, (GATE_X, 5.06, 3.2), (0.2, 8.3, 6.4))                      # left wall, behind the weighing room
    add_box(bm, ((ROOM_X0 + GATE_X) / 2, 1.0, 4.5), (GATE_X - ROOM_X0 + 0.2, 0.16, 3.8))   # above the weighing room
    for x in (19.4, 22.3, 25.2):
        for y in (0.98 + 0.25, 4.9, 8.6):
            add_box(bm, (x, y, 3.2), (0.32, 0.32, 6.4))
    for y in (1.2, 4.9, 8.6):
        add_box(bm, (22.3, y, 5.6), (9.6, 0.25, 0.35))
    _obj('RechargeHall', bm, [m['wall']], coll)
    bm = bmesh.new()
    add_box(bm, (21.6, -1.7, 2.5), (0.36, 0.36, 5.0))                       # foreground column
    _obj('ForegroundColumn', bm, [m['steel']], coll)

    # Cradle rows: plinth, posts with their contact arms, a strip light over each row.
    racks, contacts, plinths, fixtures, tags = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    slots = []
    rows = [(NEAR_ROW_Y, 18.4, 26.3, 0.79)] + [(y, 18.2, 26.4, 0.82) for y in ROWS_Y]
    for r, (y, xa, xb, step) in enumerate(rows):
        add_box(plinths, ((xa + xb) / 2, y + 0.1, 0.03), (xb - xa + 0.5, 0.62, 0.06))
        x = xa
        k = 0
        while x <= xb + 1e-6:
            post = Vector((x, y + 0.36, 0))
            add_box(racks, post + Vector((0, 0, 0.45)), (0.07, 0.07, 0.84))
            add_box(racks, post + Vector((0, 0, 0.88)), (0.1, 0.1, 0.04))
            for z in (0.43, 0.51):
                add_cyl(racks, post + Vector((0, 0, z)), Vector((x, y + 0.2, z + 0.06)), 0.01, seg=8)
                add_cyl(contacts, Vector((x, y + 0.2, z + 0.06)), Vector((x, y + 0.17, z + 0.06)), 0.014, 0.011, seg=10)
            add_box(tags, post + Vector((0, -0.036, 0.72)), (0.05, 0.004, 0.03))
            slots.append((r, k, x, y))
            x += step
            k += 1
        if r > 0:
            add_box(fixtures, ((xa + xb) / 2, y, 2.62), (xb - xa + 0.4, 0.12, 0.06))
            for xx in (xa + 1.0, (xa + xb) / 2, xb - 1.0):
                add_cyl(fixtures, (xx, y, 2.65), (xx, y, 5.4), 0.005, seg=4)
    _obj('RackPlinths', plinths, [m['concrete']], coll)
    _obj('RackPosts', racks, [m['depot_green']], coll)
    _obj('RackContacts', contacts, [m['copper']], coll)
    _obj('RackTags', tags, [m['tag']], coll)
    _obj('RowFixtures', fixtures, [m['steel']], coll)
    for r, (y, xa, xb, step) in enumerate(rows):
        bm = bmesh.new()
        if r == 0:
            add_box(bm, ((xa + xb) / 2, y + 0.45, 1.6), (xb - xa + 0.2, 0.03, 0.03))
        else:
            add_box(bm, ((xa + xb) / 2, y, 2.585), (xb - xa + 0.3, 0.05, 0.02))
        _obj(f'RowTube{r}', bm, [m['rowlight'][r]], coll)

    return slots


# --------------------------------------------------------------------------
# D-17 clips
# --------------------------------------------------------------------------

def body_delta(body, body_rot):
    """Armature-space transform of the body bone for a pose (its head rests at z 0.4)."""
    head = Vector((0, 0, 0.4))
    r = Euler([math.radians(v) for v in body_rot], 'XYZ').to_matrix().to_4x4()
    return Matrix.Translation(head + Vector(body)) @ r @ Matrix.Translation(-head)


def reach(targets, body, body_rot, rest):
    """IK-hand offsets that put each wrist on an armature-space target, given the body pose.
    The hand targets are children of the body bone, so its lean and drop carry them."""
    inv = body_delta(body, body_rot).inverted()
    return {s: inv @ targets[s] - rest[s] for _, s in SIDES}


def blend(a, b, k):
    return {s: a[s].lerp(b[s], k) for _, s in SIDES}


def grip_targets(fwd, z, lateral=0.12):
    """Both claws on the bail: wrists just above it and out to its sides (his arms are too short to
    bring them together in front of the pod), the claws angled in onto it (HOLD_HAND)."""
    return {s: Vector((s * lateral, -fwd, z + WRIST_ABOVE_GRIP)) for _, s in SIDES}


HOLD_FWD, HOLD_Z = 0.23, 0.3        # the bail while carried, clear of the pod: forward of the root, height (weight base = this - 0.21)
HOLD_HAND = {'L': (-10, 54, 0), 'R': (-10, -54, 0)}   # hand_rot: claws angled in from the wrists onto the bail
HOLD_ELBOWS = {'L': 1, 'R': 1}      # elbows out (Clip.pose), so the forearms pass outside the pod
HOLD_BODY, HOLD_ROT = (0, 0.01, -0.035), (-4, 0, 0)


def clip_lift(dl01, arm):
    """Squat, both claws on the bail, a careful check of the grip, two tries, then up to the chest."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 40
    c = Clip(arm, 'Lift', frames)
    low = grip_targets(GRIP[0], GRIP[1])
    for frame in range(1, frames + 1):
        f = frame - 1
        z = track([(0, 0), (8, -0.07), (14, -0.075), (18, -0.085), (22, -0.07), (26, -0.08), (34, -0.035), (40, -0.035)], f)
        pitch = track([(0, 0), (8, 12), (22, 12), (26, 10), (34, -4), (40, -4)], f)
        strain = track([(14, 0), (18, 1), (22, 0.3), (26, 1), (32, 0.6), (36, 0)], f)
        roll = 3 * strain * math.sin(f * 1.9)
        # Squatting, he shifts forward over his feet: the bail on the floor is otherwise out of reach.
        lean_in = track([(0, 0), (8, 1), (26, 1), (34, 0)], f)
        body, rot = (0, 0.01 * smoothstep((f - 26) / 8) - 0.045 * lean_in, z), (pitch, roll, 0)
        lift = track([(0, 0), (22, 0), (23, 0.03), (24, 0.0), (26, 0.0), (34, 1)], f)
        up = grip_targets(HOLD_FWD, HOLD_Z)
        targets = {s: low[s].lerp(up[s], lift) + Vector((0, 0, 0.012 * strain * math.sin(f * 2.3))) for _, s in SIDES}
        hands = reach(targets, body, rot, REST)
        hands = blend(CARRY, hands, track([(0, 0), (9, 1)], f))
        claw = track([(0, 20), (9, 28), (12, 2), (40, 2)], f)
        head = (track([(0, 0), (8, 24), (12, 30), (16, 18), (22, 26), (30, 10), (40, 6)], f),
                track([(10, 0), (13, 10), (16, 0)], f), 0)
        antenna = [(track([(0, 0), (8, 10), (26, 6), (34, -8), (40, -4)], f) + 6 * strain * math.sin(f * 1.5 - i)
                    - spring(f, 34, 10 * (1 + 0.3 * i), decay=5), 0) for i in range(3)]
        feet = {side: ((s * 0.015 * smoothstep(f / 8), 0, 0), (0, 0, 0)) for side, s in SIDES}
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, feet=feet, hands=hands,
               hand_rot=HOLD_HAND, claws={'L': claw, 'R': claw}, elbows=HOLD_ELBOWS)
    c.done()


def clip_set_down(dl01, arm, name, base):
    """Lower the weight onto the floor (base 0) or the trolley deck, let go, and give it one pat."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 36
    c = Clip(arm, name, frames)
    down = grip_targets(GRIP[0], base + GRIP[1])
    up = grip_targets(HOLD_FWD, HOLD_Z)
    deep = 1 - min(1, base / 0.16)
    for frame in range(1, frames + 1):
        f = frame - 1
        z = track([(0, -0.035), (12, -0.035 - 0.04 * deep), (18, -0.04 - 0.03 * deep), (30, -0.01), (36, 0)], f)
        pitch = track([(0, -4), (12, 10), (18, 12), (30, 4), (36, 0)], f) * (0.25 + 0.75 * deep)   # bowing less to the deck
        lean_in = track([(0, 0), (12, 1), (24, 1), (32, 0)], f)   # forward over his feet to reach down
        body, rot = (0, 0.01 * (1 - smoothstep(f / 10)) - 0.045 * lean_in, z), (pitch, 0, 0)
        lower = track([(0, 0), (12, 1)], f)
        targets = {s: up[s].lerp(down[s], lower) for _, s in SIDES}
        # After letting go: the right claw comes up and pats the top once, from out to the side.
        pat = {s: targets[s] for _, s in SIDES}
        top = Vector((-0.13, -GRIP[0] + 0.03, base + 0.26))
        pat[-1] = top + Vector((0, 0, track([(19, 0.04), (22, 0.0), (24, 0.03)], f)))
        patting = track([(15, 0), (19, 1), (25, 1), (28, 0)], f)
        hands = reach(blend(targets, pat, patting), body, rot, REST)
        hands = blend(hands, CARRY, track([(26, 0), (36, 1)], f))
        claw = track([(0, 2), (14, 2), (16, 28), (36, CLAW_REST_OPEN['L'])], f)
        head = (track([(0, 6), (12, 26), (24, 24), (30, 8), (36, 0)], f) * (0.4 + 0.6 * deep),   # the deck is nearer his eyes
                track([(22, 0), (27, 9), (36, 0)], f), 0)
        antenna = [(track([(0, -4), (12, 8), (16, 0)], f) - spring(f, 16, 8 * (1 + 0.3 * i), decay=5), 0) for i in range(3)]
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands,
               hand_rot=HOLD_HAND,
               claws={'L': claw, 'R': track([(0, 2), (14, 2), (16, 28), (19, 10), (36, CLAW_REST_OPEN['R'])], f)},
               elbows={side: 1 - track([(30, 0), (36, 1)], f) for side, _ in SIDES})
    c.done()


def clip_carry_idle(dl01, arm):
    track, Clip, REST = dl01.track, dl01.Clip, dl01.REST_WRIST
    frames = 48
    c = Clip(arm, 'CarryIdle', frames)
    tau = 2 * math.pi
    for frame in range(1, frames + 2):
        t = (frame - 1) / frames
        body = (0, 0.01, -0.035 + 0.004 * math.sin(tau * t))
        rot = (-4 + 0.8 * math.sin(tau * t - 0.5), 1.0 * math.sin(tau * t), 0)
        targets = {s: v + Vector((0, 0, 0.006 * math.sin(tau * t - 0.8))) for s, v in grip_targets(HOLD_FWD, HOLD_Z).items()}
        hands = reach(targets, body, rot, REST)
        c.pose(frame, body=body, body_rot=rot, head=(6 + 2 * math.sin(tau * t), 0, 0),
               antenna=[(-4 + 3 * math.sin(tau * t - i), 0) for i in range(3)], hands=hands,
               hand_rot=HOLD_HAND, claws={'L': 2, 'R': 2}, elbows=HOLD_ELBOWS)
    c.done()


def carry_gait(dl01, arm):
    """Short, wide, careful steps under a load, leaning back against it."""
    Clip, REST = dl01.Clip, dl01.REST_WRIST
    frames, half, stance, lift = 14, 0.055, 0.64, 0.02
    c = Clip(arm, 'CarryWalk', frames)
    tau = 2 * math.pi
    for frame in range(1, frames + 2):
        t = (frame - 1) / frames
        feet = {}
        for side, s in SIDES:
            u = (t - (0.0 if side == 'L' else 0.5)) % 1.0
            if u < stance:
                rel, zf = -half + 2 * half * u / stance, 0.0
            else:
                k = (u - stance) / (1 - stance)
                rel, zf = half - 2 * half * smoothstep(k), lift * math.sin(math.pi * k) ** 0.8
            feet[side] = ((s * 0.012, rel, zf), (0, 0, 0))
        sway = math.sin(tau * t)
        body = (-0.01 * sway, 0.01, -0.04 + 0.006 * math.cos(2 * tau * t))
        rot = (-4 + 1.2 * math.sin(2 * tau * t - 1.0), -4.0 * sway, 1.5 * math.sin(tau * t + 0.4))
        targets = {s: v + Vector((0.006 * sway, 0, 0.008 * math.sin(2 * tau * t - 1.4)))
                   for s, v in grip_targets(HOLD_FWD, HOLD_Z).items()}
        hands = reach(targets, body, rot, REST)
        head = (6 - rot[0], 1.2 * math.sin(tau * t - 1.2) - rot[1], 0)
        c.pose(frame, body=body, body_rot=rot, head=head, feet=feet,
               antenna=[(-6 + 3 * math.sin(2 * tau * t - 1.2 - 0.5 * i), 0) for i in range(3)],
               hands=hands, hand_rot=HOLD_HAND, claws={'L': 2, 'R': 2}, elbows=HOLD_ELBOWS)
    c.done()


def push_targets(fwd=0.32):
    """Wrists just behind and above the push bar, claws forward over it (PUSH_HAND). The bar is out of
    his reach from where he stands, so the push clips lean his body in over his feet (PUSH_LEAN)."""
    return {s: Vector((s * 0.12, -fwd + 0.06, TROLLEY_HANDLE + 0.03)) for _, s in SIDES}


PUSH_LEAN = 0.06                    # m the body leans in toward the bar, over his feet
PUSH_HAND = {'L': (-60, 0, 10), 'R': (-60, 0, -10)}


def clip_push(dl01, arm):
    """Both claws on the trolley's push bar. PushIdle holds it; PushWalk leans in and walks.
    The game plays PushWalk backwards to pull."""
    track, Clip, REST = dl01.track, dl01.Clip, dl01.REST_WRIST
    tau = 2 * math.pi
    c = Clip(arm, 'PushIdle', 48)
    for frame in range(1, 50):
        t = (frame - 1) / 48
        body, rot = (0, -PUSH_LEAN, -0.02 + 0.003 * math.sin(tau * t)), (3 + 0.6 * math.sin(tau * t), 0, 0)
        hands = reach(push_targets(), body, rot, REST)
        c.pose(frame, body=body, body_rot=rot, head=(-6 + 1.5 * math.sin(tau * t - 0.6) - rot[0] * 0.5, 0, 0),
               antenna=[(-6 + 2 * math.sin(tau * t - i), 0) for i in range(3)], hands=hands,
               hand_rot=PUSH_HAND, claws={'L': 2, 'R': 2}, elbows={'L': 1, 'R': 1})
    c.done()
    frames, half, stance, lift = 12, 0.07, 0.62, 0.026
    c = Clip(arm, 'PushWalk', frames)
    for frame in range(1, frames + 2):
        t = (frame - 1) / frames
        feet = {}
        for side, s in SIDES:
            u = (t - (0.0 if side == 'L' else 0.5)) % 1.0
            if u < stance:
                rel, zf, sw = -half + 2 * half * u / stance, 0.0, None
            else:
                k = (u - stance) / (1 - stance)
                rel, zf, sw = half - 2 * half * smoothstep(k), lift * math.sin(math.pi * k) ** 0.8, k
            feet[side] = ((0, rel, zf), (10 * math.sin(math.pi * sw) if sw is not None else 0, 0, 0))
        sway = math.sin(tau * t)
        body = (-0.006 * sway, -PUSH_LEAN - 0.015, -0.03 + 0.004 * math.cos(2 * tau * t))
        rot = (2 + 1.0 * math.sin(2 * tau * t - 1.0), -2.0 * sway, 1.0 * math.sin(tau * t + 0.4))
        hands = reach(push_targets(), body, rot, REST)
        c.pose(frame, body=body, body_rot=rot, head=(-8 - rot[0] * 0.5, -rot[1], 0), feet=feet,
               antenna=[(-10 + 2.5 * math.sin(2 * tau * t - 1.2 - 0.5 * i), 0) for i in range(3)],
               hands=hands, hand_rot=PUSH_HAND, claws={'L': 2, 'R': 2}, elbows={'L': 1, 'R': 1})
    c.done()


def clip_grab(dl01, arm):
    """Step up to the push bar and take hold of it (the game turns him to face the trolley first)."""
    track, Clip, REST, CARRY = dl01.track, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 14
    c = Clip(arm, 'Grab', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        k = smoothstep(f / 10)
        body, rot = (0, -PUSH_LEAN * k, -0.02 * k), (3 * k, 0, 0)
        held = reach(push_targets(), body, rot, REST)
        hands = {s: dl01.reach_around(CARRY[s], held[s], k) for _, s in SIDES}   # forward first, then up to the bar
        c.pose(frame, body=body, body_rot=rot, head=(track([(0, 0), (5, 14), (13, -4)], f), 0, 0),
               antenna=[(-6 * k, 0)] * 3, hands=hands,
               hand_rot={'L': (-24 - 36 * k, 0, 10), 'R': (-24 - 36 * k, 0, -10)},
               claws={'L': track([(0, 20), (6, 30), (10, 2)], f), 'R': track([(0, 1), (6, 30), (10, 2)], f)},
               elbows={'L': min(1.0, 2 * k), 'R': min(1.0, 2 * k)})
    c.done()


def clip_nudge(dl01, arm):
    """He reaches out to the courier slumped in its cradle and taps its shoulder. Twice. Waits.
    Nothing. The claw lingers, comes back, and his head goes down."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 84
    c = Clip(arm, 'Nudge', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        reachk = track([(4, 0), (16, 1), (50, 1), (62, 0)], f)
        tap = sum(math.sin(math.pi * (f - t0) / 5) for t0 in (18, 26) if t0 <= f <= t0 + 5)
        body = (0, -0.03 * reachk, 0.0)
        rot = (track([(0, 0), (16, 3), (50, 3), (62, 2), (84, 4)], f), 0, 0)
        # The courier's shoulder is past his reach: the claw points out to it and its tip does the
        # tapping, the wrist out to the right and the elbow out (a reach for it with the wrist ran
        # the arm through the pod).
        tip = Vector((-0.05, -0.33 - 0.02 * tap, 0.47))
        right = reach({1: Vector((0, 0, 0)), -1: tip + Vector((-0.07, 0.09, 0))}, body, rot, REST)[-1]
        hands = {1: CARRY[1] + Vector((0, 0, 0.01 * reachk)), -1: dl01.reach_around(CARRY[-1], right, reachk)}
        wait = track([(30, 0), (36, 1), (50, 1), (60, 0)], f)
        head = (track([(0, 0), (12, -6), (30, -4), (50, -2), (64, 16), (84, 22)], f),
                track([(28, 0), (36, 12), (50, 10), (60, 0)], f), track([(40, 0), (46, -8), (54, 0)], f))
        antenna = [(track([(0, 0), (30, 0), (36, -18), (50, -14), (64, 10), (84, 26)], f) * (0.7 + 0.2 * i)
                    + spring(f, 18, 4) + spring(f, 26, 4), 0) for i in range(3)]
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands,
               hand_rot={'L': (-24, 6, 10), 'R': (-24 - 66 * reachk, 0, -10 + 43 * reachk)}, elbows={'R': min(1.0, 2 * reachk)},
               claws={'L': CLAW_REST_OPEN['L'], 'R': track([(4, 1), (14, 10), (50, 10), (60, 1)], f)})
    c.done()


def add_clips(dl01, arm):
    clip_lift(dl01, arm)
    clip_set_down(dl01, arm, 'SetDown', 0.0)
    clip_set_down(dl01, arm, 'SetDownHigh', TROLLEY_DECK)
    clip_carry_idle(dl01, arm)
    carry_gait(dl01, arm)
    clip_grab(dl01, arm)
    clip_push(dl01, arm)
    clip_nudge(dl01, arm)


# --------------------------------------------------------------------------
# The dormant couriers
# --------------------------------------------------------------------------

COURIER_POSES = {
    # Slumped forward in the cradle, the same rest D-17 woke from.
    'A': dict(body=(0, 0, -0.13), body_rot=(20, 4, 0), head=(25, 6, 0), droop=24, arms=(0.0, 0.0)),
    # Fallen to one side, one arm hanging.
    'B': dict(body=(0.01, 0, -0.15), body_rot=(12, -13, 5), head=(34, -12, 8), droop=40, arms=(-0.07, 0.02)),
    # Folded right over, head on its chest.
    'C': dict(body=(0, -0.01, -0.16), body_rot=(28, 2, -3), head=(42, 2, 0), droop=55, arms=(-0.04, -0.05)),
}


def build_couriers(dl01, slots, out_coll):
    """Pose a spare D-17 three ways and bake each pose to one static mesh. Empties mark the slots
    (CourierSlot.<pose>.<n>); the game instances the meshes there. No parcels: their compartments are empty."""
    rnd = random.Random(9)
    arm = d17.build_robot('Courier', (0, 0, 0), 0)
    coll = bpy.data.collections['Courier']
    meshes = {}
    folded = {s: Vector((-s * 0.162, -0.215, 0.327)) for _, s in SIDES}
    for key, p in COURIER_POSES.items():
        c = dl01.Clip(arm, f'Courier{key}', 1)
        hands = {s: folded[s].lerp(dl01.CARRY[s], 0.5) + Vector((0, 0, p['arms'][0 if s > 0 else 1])) for _, s in SIDES}
        c.pose(1, body=p['body'], body_rot=p['body_rot'], head=p['head'],
               antenna=[(p['droop'] * (0.6 + 0.2 * i), 0) for i in range(3)], hands=hands, claws={'L': 4, 'R': 0})
        arm.animation_data.action = bpy.data.actions[f'Courier{key}']
        bpy.context.scene.frame_set(1)
        dg = bpy.context.evaluated_depsgraph_get()
        dg.update()
        bm = bmesh.new()
        mats = []
        for ob in coll.all_objects:
            if ob.type not in ('MESH', 'CURVE') or ob.name.startswith('ParcelLabel'):
                continue
            ev = ob.evaluated_get(dg)
            me = ev.to_mesh()
            names = [s.material.name if s.material else '' for s in ob.material_slots] or ['']
            if all(n == 'ParcelPaper' for n in names):
                ev.to_mesh_clear()
                continue
            me.transform(ev.matrix_world)
            remap = []
            for n in names:
                mat = bpy.data.materials.get(n)
                if mat not in mats:
                    mats.append(mat)
                remap.append(mats.index(mat))
            off = len(bm.faces)
            bm.from_mesh(me)
            bm.faces.ensure_lookup_table()
            for f in bm.faces[off:]:
                f.material_index = remap[min(f.material_index, len(remap) - 1)]
            ev.to_mesh_clear()
        me = bpy.data.meshes.new(f'Courier{key}')
        bm.to_mesh(me)
        bm.free()
        me.validate(clean_customdata=False)
        for mat in mats:
            me.materials.append(mat)
        ob = bpy.data.objects.new(f'Courier{key}', me)
        out_coll.objects.link(ob)
        dec = ob.modifiers.new('lod', 'DECIMATE')
        dec.ratio = 0.09
        meshes[key] = ob
        arm.animation_data.action = None
    # Keep the slots: most filled, a few empty, the odd one fallen.
    n = 0
    for r, k, x, y in slots:
        if r == 0 and k == NUDGE_SLOT:
            key = 'A'
        else:
            roll = rnd.random()
            if roll < 0.1:
                continue
            key = 'A' if roll < 0.55 else 'B' if roll < 0.8 else 'C'
        e = bpy.data.objects.new(f'CourierSlot.{key}.{n}', None)
        e.location = (x + rnd.uniform(-0.02, 0.02), y + rnd.uniform(-0.02, 0.02), 0.06)
        e.rotation_euler = (0, 0, math.radians(rnd.uniform(-8, 8) if not (r == 0 and k == NUDGE_SLOT) else 0))
        if r == 0 and k == NUDGE_SLOT:
            e.name = f'CourierSlot.{key}.nudge'
        out_coll.objects.link(e)
        n += 1
    # The spare robot is no longer needed.
    for ob in list(coll.all_objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.collections.remove(coll)
    return meshes


def build_set(dl01, m, coll):
    dl02_materials(m)
    build_passage(m, coll)          # the passage from DL-01 stays where it is; the rooms move by OFF2
    before = set(bpy.data.objects)
    build_weigh_room(m, coll)
    slots = build_recharge_hall(m, coll)
    dl01.shift_new(before, lambda o: dl01.OFF2)
    return [(r, k, x + dl01.OFF2, y) for r, k, x, y in slots]
