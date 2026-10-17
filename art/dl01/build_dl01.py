"""DL-01 The Wake: builds the scene-1 set and D-17's gameplay clips, exported for the
playable prototype in game/dl01/.

    python build_dl01.py --out ../../game/dl01/assets

Writes:
  set.glb  the static set plus the moving parts the game drives by name
           (shutter assembly, latch lever, counterweight, relay lamps, work bulb, cradle
           status lamp, sparks)
  d17.glb  D-17 rigged, with clips: Opening, Idle, Walk, CrouchWalk, CrouchIdle,
           JumpStart, JumpAir, Land, Mantle, Pull, Flinch

Coordinates: metres, Blender Z up. The playable plane is y = 0 and D-17 travels along +x.
glTF converts to Y up, so Blender (x, y, z) becomes (x, z, -y) in the game.
"""
import argparse
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'd17'))

import bpy  # noqa: E402  (must precede bmesh/mathutils)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import build_d17 as d17  # noqa: E402
from build_d17 import (add_box, add_cyl, add_sphere, add_torus, rounded_box, mesh_object,  # noqa: E402
                       worn_material, emission_material, simple_material, smoothstep, ease_back,
                       SIDES, CLAW_REST_OPEN, _key)

TEX = os.path.join(HERE, 'textures')
D17_START = Vector((1.0, 0.0, 0.0))
OPENING_FRAMES = 480                 # 20 s at 24 fps
DORMANT_YAW = -45.0                  # slumped three-quarters toward camera

# Shared with the game (game/dl01/main.js keeps the same numbers).
SHUTTER_PATH = [Vector((0.2, 1.60)), Vector((2.0, 0.62)), Vector((3.2, 0.60)), Vector((3.4, 0.02))]
LATCH_PIVOT = Vector((3.36, 0.12))   # (x, z); the lever stands up from here
LATCH_LEN = 0.21
LATCH_TILT = 8.0                     # degrees toward D-17 at rest
PULL_ROOT_X = 3.12
CRATE = (4.5, 5.1, 0.45)             # x0, x1, height
CROUCH = -0.17                       # body drop when crouched

# Opening beats (frames from the start of the scene).
BOOT, RISE, KNEE_CLICK = 216, (300, 352), 312
GRIT, SHIELD, CHECK, RELIEF, SHAKE = 350, 360, 384, 414, 436


def track(keys, f, ease=smoothstep):
    """Piecewise-eased value from [(frame, value), ...]."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f <= f1:
            return v0 + (v1 - v0) * ease((f - f0) / (f1 - f0))
    return keys[-1][1]


def spring(f, f0, amp, decay=7.0, freq=0.9):
    t = f - f0
    return amp * math.exp(-t / decay) * math.sin(t * freq) if t > 0 else 0.0


# --------------------------------------------------------------------------
# Materials (names are mapped to game shaders in main.js)
# --------------------------------------------------------------------------

def set_materials():
    m = {}
    m['concrete'] = worn_material('Concrete', base=(0.075, 0.074, 0.07), dirt=(0.035, 0.034, 0.03),
                                  chip=(0.12, 0.115, 0.105), rough=0.92, chip_rough=0.9, metallic=0.0)
    m['wall'] = worn_material('WallPanel', base=(0.09, 0.095, 0.09), dirt=(0.04, 0.04, 0.035),
                              chip=(0.14, 0.13, 0.11), rough=0.9, chip_rough=0.85, metallic=0.0)
    m['shutter'] = worn_material('ShutterSteel', base=(0.14, 0.16, 0.15), dirt=(0.09, 0.05, 0.025),
                                 chip=(0.16, 0.08, 0.035), rough=0.7, chip_rough=0.6, metallic=0.4)
    m['steel'] = worn_material('DepotSteel', base=(0.05, 0.052, 0.05), dirt=(0.05, 0.03, 0.018),
                               chip=(0.16, 0.15, 0.13), rough=0.6, chip_rough=0.4, metallic=0.6)
    m['depot_green'] = worn_material('DepotGreen', base=(0.06, 0.09, 0.07), dirt=(0.04, 0.035, 0.025),
                                     chip=(0.12, 0.11, 0.1), rough=0.65, chip_rough=0.5, metallic=0.2)
    m['red'] = worn_material('LeverRed', base=(0.45, 0.05, 0.03), dirt=(0.2, 0.04, 0.02),
                             chip=(0.08, 0.07, 0.06), rough=0.5, chip_rough=0.6, metallic=0.1)
    m['yellow'] = worn_material('SafetyYellow', base=(0.55, 0.42, 0.06), dirt=(0.2, 0.16, 0.05),
                                chip=(0.07, 0.068, 0.062), rough=0.8, chip_rough=0.9, metallic=0.0)
    m['wood'] = worn_material('CrateWood', base=(0.18, 0.12, 0.07), dirt=(0.08, 0.055, 0.035),
                              chip=(0.25, 0.19, 0.12), rough=0.85, chip_rough=0.8, metallic=0.0)
    m['paper'] = worn_material('ParcelBrown', base=(0.3, 0.22, 0.13), dirt=(0.15, 0.11, 0.07),
                               chip=(0.4, 0.33, 0.24), rough=0.9, chip_rough=0.85, metallic=0.0)
    m['copper'] = simple_material('Copper', (0.55, 0.3, 0.18), 0.35, metallic=1.0)
    m['rubber'] = simple_material('Rubber', (0.012, 0.012, 0.011), 0.7)
    m['tag'] = simple_material('ReflectTag', (0.8, 0.78, 0.7), 0.15, metallic=0.6)
    m['bulb'] = emission_material('WorkBulb', (1.0, 0.92, 0.8), 0.0)
    m['status'] = emission_material('CradleStatus', (0.35, 1.0, 0.45), 0.0)
    m['spark'] = emission_material('Spark', (0.7, 0.85, 1.0), 0.0)
    m['farglow'] = emission_material('FarGlow', (0.45, 0.55, 0.6), 0.012)
    m['relay'] = [emission_material(f'Relay{c}', (0.75, 1.0, 0.82), 0.0) for c in 'ABC']
    return m


def image_material(name, path):
    mat, nt, bsdf = d17._new_material(name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.6
    return mat


def make_pictogram(path):
    """Depot pictogram: a parcel with an outbound arrow and three dots for the relay lamps."""
    from PIL import Image, ImageDraw, ImageFilter
    w = h = 512
    img = Image.new('RGB', (w, h), (22, 34, 27))
    d = ImageDraw.Draw(img)
    fg = (196, 190, 160)
    d.rounded_rectangle((24, 24, w - 24, h - 24), radius=40, outline=fg, width=14)
    d.rectangle((120, 170, 330, 360), outline=fg, width=18)
    d.line((120, 230, 330, 230), fill=fg, width=14)
    d.line((225, 170, 225, 360), fill=fg, width=14)
    d.polygon([(350, 230), (430, 265), (350, 300)], fill=fg)
    d.rectangle((300, 252, 360, 278), fill=fg)
    for i in range(3):
        d.ellipse((150 + i * 80, 400, 190 + i * 80, 440), fill=fg)
    img = img.filter(ImageFilter.GaussianBlur(1.0))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def textured_plane(name, size, center, rot_x_deg, mat, coll):
    bm = bmesh.new()
    bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, calc_uvs=True)
    bmesh.ops.transform(bm, verts=bm.verts, matrix=Matrix.Translation(center)
                        @ Matrix.Rotation(math.radians(rot_x_deg), 4, 'X')
                        @ Matrix.Diagonal((size[0], size[1], 1, 1)))
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def obj(name, bm, mats, coll, sharp=35):
    return mesh_object(name, bm, mats, coll, sharp=sharp)


# --------------------------------------------------------------------------
# The set
# --------------------------------------------------------------------------

def build_shutter(m, coll):
    """A corrugated sorting shutter fallen across the alcove: a sloping roof over the cradle,
    sagging over a toppled conveyor, then down to the floor where its latch holds it."""
    pts = []
    for a, b in zip(SHUTTER_PATH, SHUTTER_PATH[1:]):
        n = max(2, int((b - a).length / 0.0125))
        pts += [a.lerp(b, i / n) for i in range(n)]
    pts.append(SHUTTER_PATH[-1])
    for _ in range(6):
        pts = [pts[0]] + [(pts[i - 1] + 2 * pts[i] + pts[i + 1]) / 4 for i in range(1, len(pts) - 1)] + [pts[-1]]
    dist = [0.0]
    for a, b in zip(pts, pts[1:]):
        dist.append(dist[-1] + (b - a).length)
    ys = [-0.55 + 1.5 * j / 6 for j in range(7)]
    rnd = random.Random(4)
    holes = [(rnd.uniform(0.4, 3.2), rnd.uniform(0.04, 0.12), rnd.choice([0, 4, 5])) for _ in range(6)]
    bm = bmesh.new()
    grid = []
    for i, (p, s) in enumerate(zip(pts, dist)):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        nrm = Vector((-t.y, t.x))
        off = 0.011 * math.sin(2 * math.pi * s / 0.075)
        row = []
        for y in ys:
            sag = 0.02 * math.sin(math.pi * (y + 0.55) / 1.5)
            q = p + nrm * (off - sag)
            row.append(bm.verts.new((q.x, y, q.y)))
        grid.append(row)
    for i in range(len(grid) - 1):
        for j in range(len(ys) - 1):
            if not any(abs(dist[i] - c) < w and j == k for c, w, k in holes):
                bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    ob = obj('Shutter', bm, [m['shutter']], coll, sharp=80)
    sol = ob.modifiers.new('thick', 'SOLIDIFY')
    sol.thickness = 0.004

    px, pz = LATCH_PIVOT
    bm = bmesh.new()
    add_box(bm, (3.4, 0.2, 0.035), (0.05, 1.5, 0.06))                    # bottom rail
    add_box(bm, (3.4, -0.02, 0.1), (0.07, 0.1, 0.16))                     # latch body
    add_cyl(bm, (px, -0.1, pz), (px, 0.06, pz), 0.014)                    # lever pivot
    obj('ShutterRail', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_box(bm, (3.44, -0.02, 0.012), (0.14, 0.14, 0.024))                # floor bracket stays put
    obj('LatchBracket', bm, [m['steel']], coll)

    # T-handled lever, modelled upright about its pivot so the game can rotate it.
    tilt = math.radians(LATCH_TILT)
    grip = Vector((px - LATCH_LEN * math.sin(tilt), 0, pz + LATCH_LEN * math.cos(tilt)))
    bm = bmesh.new()
    add_cyl(bm, (px, -0.02, pz), (grip.x, -0.02, grip.z), 0.011)
    add_cyl(bm, (grip.x, -0.14, grip.z), (grip.x, 0.1, grip.z), 0.013)
    obj('LatchLever', bm, [m['red']], coll)
    bm = bmesh.new()
    add_box(bm, (grip.x + 0.004, -0.165, grip.z), (0.004, 0.03, 0.02))
    obj('LatchTag', bm, [m['tag']], coll)

    bm = bmesh.new()
    top = Vector((3.5, -0.02, 2.3))
    add_cyl(bm, top + Vector((0, -0.03, 0)), top + Vector((0, 0.03, 0)), 0.085, seg=24)
    add_box(bm, top + Vector((0, 0, 0.1)), (0.06, 0.09, 0.2))
    add_box(bm, (3.0, 0.1, 2.38), (3.0, 0.12, 0.08))                     # gantry beam
    obj('Pulley', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_box(bm, (3.585, -0.02, 1.56), (0.13, 0.1, 0.22))
    obj('Counterweight', bm, [m['steel']], coll)
    bm = bmesh.new()
    for k in range(3):
        add_box(bm, (3.585, -0.071, 1.48 + k * 0.07), (0.131, 0.002, 0.03), rot=Matrix.Rotation(0.6, 4, 'Y'))
    obj('CounterweightStripes', bm, [m['yellow']], coll)


def build_set(m, coll):
    bm = bmesh.new()
    add_box(bm, (3.0, 3.0, -0.05), (16, 14, 0.1))
    obj('Floor', bm, [m['concrete']], coll)
    bm = bmesh.new()
    add_box(bm, (2.3, -0.38, 0.0015), (7.6, 0.07, 0.003))
    obj('SafetyLine', bm, [m['yellow']], coll)

    bm = bmesh.new()
    rnd = random.Random(1)
    for i in range(4):
        rounded_box((0.97, 0.12, 2.42), (-1.3 + i * 1.0, 1.06 + rnd.uniform(-0.01, 0.01), 1.21), p=6, cuts=8,
                    dents=((0.006, 3.0),), seed=i, bm=bm, mat=0)
    rounded_box((0.12, 2.4, 2.45), (-1.85, -0.1, 1.22), p=6, cuts=8, dents=((0.01, 2.0),), seed=9, bm=bm, mat=0)
    obj('AlcoveWalls', bm, [m['wall']], coll)
    bm = bmesh.new()
    rounded_box((4.3, 2.6, 0.18), (0.45, -0.1, 2.54), p=5, cuts=12, dents=((0.03, 1.5), (0.01, 6.0)),
                seed=3, bm=bm, mat=0)
    rounded_box((0.6, 1.2, 0.14), (2.75, 0.3, 2.3), p=3, cuts=8, dents=((0.03, 4.0),), seed=5, bm=bm,
                mat=0, rot=Matrix.Rotation(0.5, 4, 'Y'))
    obj('Ceiling', bm, [m['concrete']], coll)
    bm = bmesh.new()
    for i in range(7):
        x, y = 2.62 + rnd.uniform(-0.05, 0.05), -0.9 + i * 0.3
        add_cyl(bm, (x, y, 2.45), (x + rnd.uniform(0.05, 0.25), y + rnd.uniform(-0.1, 0.1),
                                   2.45 - rnd.uniform(0.2, 0.6)), 0.006, seg=6)
    for z in (2.04, 2.17):
        add_cyl(bm, (-1.8, 0.93, z), (2.35, 0.93, z), 0.045, seg=16)
    add_cyl(bm, (2.35, 0.93, 2.04), (2.55, 0.6, 1.7), 0.045, seg=16)
    for x in (-1.2, -0.2, 0.8, 1.8):
        add_box(bm, (x, 0.97, 2.1), (0.04, 0.06, 0.26))
    obj('PipesRebar', bm, [m['steel']], coll)

    # Left dead end: collapsed racking, parcels and rubble (kept off the walking lane).
    bm = bmesh.new()
    for i, x in enumerate((-1.55, -0.95, -0.45)):
        tilt = Matrix.Rotation([0.05, -0.12, 0.3][i], 4, 'Y')
        add_box(bm, (x, 0.55, 0.9), (0.05, 0.05, 1.8), rot=tilt)
        add_box(bm, (x, -0.35, 0.9), (0.05, 0.05, 1.8), rot=tilt)
    for z, rot in ((0.35, 0.0), (0.85, 0.08), (1.35, -0.2)):
        add_box(bm, (-1.0, 0.1, z), (1.2, 1.0, 0.03), rot=Matrix.Rotation(rot, 4, 'Y'))
    obj('Racking', bm, [m['steel']], coll)
    bm = bmesh.new()
    prnd = random.Random(7)
    for k in range(26):
        sz = (prnd.uniform(0.12, 0.32), prnd.uniform(0.12, 0.3), prnd.uniform(0.08, 0.22))
        x = prnd.uniform(-1.7, -0.45)
        z = sz[2] / 2 + (0.37 if k % 3 == 0 else 0.0)
        add_box(bm, (x, prnd.uniform(-0.4, 0.8), z), sz,
                rot=Matrix.Rotation(prnd.uniform(-0.5, 0.5), 4, 'Z') @ Matrix.Rotation(prnd.uniform(-0.15, 0.15), 4, 'X'))
    for x, y in ((0.35, 0.55), (1.55, 0.6), (2.6, 0.55), (4.2, 0.5), (4.3, -0.45), (5.4, 0.45)):
        sz = (prnd.uniform(0.1, 0.2), prnd.uniform(0.1, 0.2), prnd.uniform(0.07, 0.12))
        add_box(bm, (x, y, sz[2] / 2), sz, rot=Matrix.Rotation(prnd.uniform(-1, 1), 4, 'Z'))
    obj('Parcels', bm, [m['paper']], coll)
    bm = bmesh.new()
    for k in range(9):
        add_sphere(bm, (prnd.uniform(-1.6, -0.5), prnd.uniform(-0.5, 0.7), 0.02), prnd.uniform(0.04, 0.12),
                   seg=8, scale=(1.3, 1.0, 0.45), dents=(0.02, 15))
    obj('Rubble', bm, [m['concrete']], coll)

    # Toppled conveyor behind the lane holds the sag; a strut in front holds the near edge.
    bm = bmesh.new()
    for y in (0.3, 0.9):
        add_box(bm, (2.02, y, 0.3), (0.06, 0.06, 0.6))
        add_box(bm, (2.22, y, 0.3), (0.06, 0.06, 0.6))
    add_box(bm, (2.12, 0.6, 0.57), (0.3, 0.65, 0.05))
    for k in range(5):
        add_cyl(bm, (1.99, 0.32 + k * 0.14, 0.6), (2.25, 0.32 + k * 0.14, 0.6), 0.022, seg=12)
    add_box(bm, (2.1, -0.5, 0.3), (0.05, 0.05, 0.62), rot=Matrix.Rotation(0.12, 4, 'Y'))
    obj('Conveyor', bm, [m['steel']], coll)

    build_shutter(m, coll)

    pic = os.path.join(TEX, 'depot_pictogram.png')
    if not os.path.exists(pic):
        make_pictogram(pic)
    bm = bmesh.new()
    add_box(bm, (2.0, 0.95, 1.35), (0.26, 0.1, 0.34))
    add_cyl(bm, (2.0, 0.95, 1.52), (2.0, 0.95, 2.45), 0.022, seg=12)
    add_cyl(bm, (2.0, 0.93, 1.18), (2.0, 0.93, 0.03), 0.012, seg=10)
    for x in (1.93, 2.0, 2.07):
        add_torus(bm, (x, 0.893, 1.465), (0, 1, 0), 0.02, 0.0025, seg=16, rseg=4)
    obj('Relay', bm, [m['depot_green']], coll)
    textured_plane('RelayPictogram', (0.16, 0.16), (2.0, 0.899, 1.32), 90, image_material('Pictogram', pic), coll)
    for i, (x, mat) in enumerate(zip((1.93, 2.0, 2.07), m['relay'])):
        bm = bmesh.new()
        add_sphere(bm, (x, 0.9, 1.465), 0.016, seg=12, scale=(1, 0.6, 1))
        obj(f'RelayLamp{i}', bm, [mat], coll)
    d17.tube('RelayCable', [Vector((2.0, 0.93, 0.03)), Vector((1.4, 0.8, 0.015)), Vector((0.9, 0.7, 0.015))],
             0.012, 0, [m['rubber']], coll)

    bm = bmesh.new()
    add_cyl(bm, (1.7, 0.25, 2.45), (1.7, 0.25, 2.2), 0.004, seg=6)
    add_cyl(bm, (1.7, 0.25, 2.2), (1.7, 0.25, 2.12), 0.06, 0.08, seg=16)
    for k in range(6):
        a = k * math.pi / 3
        add_cyl(bm, (1.7 + 0.075 * math.cos(a), 0.25 + 0.075 * math.sin(a), 2.12),
                (1.7 + 0.05 * math.cos(a), 0.25 + 0.05 * math.sin(a), 2.03), 0.003, seg=4)
    obj('WorkLampFixture', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_sphere(bm, (1.7, 0.25, 2.08), 0.035, seg=12)
    obj('WorkLampBulb', bm, [m['bulb']], coll)

    x0, x1, h = CRATE
    cx = (x0 + x1) / 2
    bm = bmesh.new()
    for z in (0.06, 0.18, 0.3, 0.42):
        add_box(bm, (cx, 0.05, z * h / 0.45), (x1 - x0, 0.6, 0.1))
    obj('Crate', bm, [m['wood']], coll)
    bm = bmesh.new()
    for x in (x0, x1):
        for y in (-0.25, 0.35):
            add_box(bm, (x, y, h / 2), (0.03, 0.03, h + 0.01))
    add_box(bm, (x0 + 0.02, -0.252, h - 0.01), (0.05, 0.004, 0.06))
    add_cyl(bm, (x0, -0.262, h + 0.005), (x0, -0.262, h - 0.07), 0.008)
    obj('CrateIron', bm, [m['steel']], coll)

    bm = bmesh.new()
    for y, z in ((2.6, 0.7), (4.2, 1.0), (5.8, 0.8)):
        add_box(bm, (6.5, y, z), (9.0, 0.5, 0.1))
        for x in range(3, 11):
            add_box(bm, (x, y, z / 2), (0.06, 0.4, z))
    for x in (3.4, 4.2, 5.0, 5.8, 6.6, 7.4):
        add_box(bm, (x, 3.3, 0.4), (0.07, 0.07, 0.8))
        add_box(bm, (x - 0.08, 3.3, 0.55), (0.18, 0.04, 0.03))
    for x in (3.0, 4.6, 6.1, 8.0):
        add_cyl(bm, (x, 3.6, 4.0), (x, 3.6, 2.0 + random.Random(int(x * 10)).uniform(-0.6, 0.4)), 0.01, seg=6)
    obj('Hall', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_box(bm, (6.0, 8.0, 2.5), (14, 0.1, 6))
    obj('FarWall', bm, [m['farglow']], coll)
    bm = bmesh.new()
    add_cyl(bm, (0.3, -1.05, 0.06), (1.9, -0.95, 0.07), 0.06, seg=20)
    obj('ForegroundPipe', bm, [m['steel']], coll)


def build_cradle(m, coll):
    """Depot charging cradle behind the lane, its long contact arms reaching D-17's back
    in his dormant pose (evaluated from the Opening clip's first frame)."""
    dg = bpy.context.evaluated_depsgraph_get()
    bpy.context.scene.frame_set(1)
    dg.update()
    body = bpy.data.objects['BodyParts'].evaluated_get(dg)
    back = body.matrix_world @ Vector((0.0, 0.17, 0.43))
    upper = body.matrix_world @ Vector((-0.05, 0.19, 0.51))
    direction = back - D17_START
    direction.z = 0
    direction.normalize()
    post = back + direction * 0.4
    post.z = 0
    bm = bmesh.new()
    add_box(bm, post + Vector((0, 0, 0.42)), (0.075, 0.075, 0.84))
    add_box(bm, post + Vector((0, 0, 0.86)), (0.11, 0.11, 0.04))
    add_box(bm, post + Vector((0, 0, 0.02)), (0.22, 0.22, 0.04))
    tips = []
    for target in (back, upper):
        root = post + Vector((0, 0, target.z))
        tip = target + direction * 0.03
        add_cyl(bm, root, tip + direction * 0.02, 0.012, seg=10)
        tips.append(tip)
    obj('CradlePost', bm, [m['depot_green']], coll)
    bm = bmesh.new()
    for tip in tips:
        add_cyl(bm, tip + direction * 0.025, tip, 0.016, 0.012, seg=12)
    obj('CradleContacts', bm, [m['copper']], coll)
    bm = bmesh.new()
    add_sphere(bm, post + Vector((0, -0.04, 0.8)), 0.01, seg=8)
    obj('CradleStatus', bm, [m['status']], coll)
    bm = bmesh.new()
    rnd = random.Random(3)
    for tip in tips:
        a, b = tip + direction * 0.002, tip - direction * 0.03
        pts = [a.lerp(b, i / 5) + Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1))) * 0.008
               for i in range(6)]
        for p, q in zip(pts, pts[1:]):
            add_cyl(bm, p, q, 0.0012, seg=4)
    obj('Sparks', bm, [m['spark']], coll)


# --------------------------------------------------------------------------
# D-17 clips
# --------------------------------------------------------------------------

REST_WRIST = {s: Vector((s * 0.262, -0.01, 0.113)) for _, s in SIDES}
CARRY = {s: Vector((-s * 0.04, -0.09, 0.112)) for _, s in SIDES}
CROUCH_CARRY = {s: Vector((-s * 0.04, -0.09, 0.112 + 0.17)) for _, s in SIDES}
FOLDED = {s: Vector((-s * 0.162, -0.215, 0.327)) for _, s in SIDES}


class Clip:
    """Keys one action on the rig, then stashes it as an NLA track for export."""

    def __init__(self, arm, name, frames):
        self.arm, self.name, self.frames = arm, name, frames
        arm.animation_data_create()
        arm.animation_data.action = bpy.data.actions.new(name)
        self.pb = arm.pose.bones
        for p in self.pb:
            p.location = (0, 0, 0)
            if p.rotation_mode == 'AXIS_ANGLE':
                p.rotation_axis_angle = (0, 0, 1, 0)
            else:
                p.rotation_mode = 'XYZ'
                p.rotation_euler = (0, 0, 0)
        self.axes = {}
        for side, _ in SIDES:
            for f in ('finger_a', 'finger_b'):
                b = arm.data.bones[f'{f}.{side}']
                self.axes[f'{f}.{side}'] = (b.matrix_local.to_3x3().inverted() @ Vector((0, 1, 0))).normalized()

    def pose(self, frame, body=(0, 0, 0), body_rot=(0, 0, 0), head=(0, 0, 0), yaw=0.0,
             antenna=((0, 0), (0, 0), (0, 0)), feet=None, hands=None, hand_rot=None, claws=None):
        rad = math.radians
        pb = self.pb
        pb['root'].rotation_euler = (0, 0, rad(yaw))
        pb['body'].location = body
        pb['body'].rotation_euler = [rad(v) for v in body_rot]
        pb['head'].rotation_euler = [rad(v) for v in head]
        for i, (ax, az) in enumerate(antenna):
            pb[f'antenna_{i + 1}'].rotation_euler = (rad(ax), 0, rad(az))
        for side, s in SIDES:
            loc, rot = (feet or {}).get(side, ((0, 0, 0), (0, 0, 0)))
            ik = pb[f'ik_foot.{side}']
            ik.location = loc
            ik.rotation_euler = (rad(rot[0]), rad(rot[1]), rad(rot[2] - s * 6))
            h = pb[f'ik_hand.{side}']
            h.location = (hands or CARRY)[s] if hands is not None else CARRY[s]
            hr = (hand_rot or {}).get(side, (-24, s * 6, s * 10))
            h.rotation_euler = [rad(v) for v in hr]
            opening = rad((claws or {}).get(side, CLAW_REST_OPEN[side]))
            for fname, sign in (('finger_a', 1), ('finger_b', -1)):
                fp = pb[f'{fname}.{side}']
                fp.rotation_axis_angle = (sign * opening, *self.axes[f'{fname}.{side}'])
        for name in ('root', 'body', 'head', 'antenna_1', 'antenna_2', 'antenna_3'):
            _key(pb[name], 'location', 'rotation_euler', frame=frame)
        for side, _ in SIDES:
            _key(pb[f'ik_foot.{side}'], 'location', 'rotation_euler', frame=frame)
            _key(pb[f'ik_hand.{side}'], 'location', 'rotation_euler', frame=frame)
            for fname in ('finger_a', 'finger_b'):
                _key(pb[f'{fname}.{side}'], 'rotation_axis_angle', frame=frame)

    def done(self):
        ad = self.arm.animation_data
        track = ad.nla_tracks.new()
        track.name = self.name
        track.strips.new(self.name, 1, ad.action)
        ad.action = None


def clip_opening(arm):
    """The authored 20-second wake (beats in docs/scenes/DL-01_the_wake.md, section 4)."""
    c = Clip(arm, 'Opening', OPENING_FRAMES)
    servo = lambda x: ease_back(x, 0.9)   # noqa: E731
    for frame in range(1, OPENING_FRAMES + 1):
        f = frame - 1
        yaw = track([(0, DORMANT_YAW), (SHAKE + 4, DORMANT_YAW), (SHAKE + 34, 0)], f)
        z = track([(0, -0.13), (RISE[0], -0.13), (RISE[1], -0.008), (SHIELD, -0.008), (SHIELD + 6, -0.03),
                   (CHECK, -0.03), (CHECK + 12, -0.014), (RELIEF, -0.014), (RELIEF + 6, 0.004),
                   (RELIEF + 16, -0.006)], f)
        pitch = track([(0, 20), (RISE[0], 20), (RISE[1], 3), (SHIELD, 3), (SHIELD + 6, 9), (CHECK, 9),
                       (CHECK + 12, 6), (RELIEF, 6), (RELIEF + 10, 2)], f)
        roll = track([(0, 4), (KNEE_CLICK, 3.4), (KNEE_CLICK + 3, 0.5), (KNEE_CLICK + 9, 2.4),
                      (RISE[1], 0)], f, ease=servo)
        roll += 4.5 * math.exp(-max(0, f - SHAKE) / 8) * math.sin(max(0, f - SHAKE) * 1.4) if f > SHAKE else 0
        hp = track([(0, 25), (240, 25), (246, 16), (258, 16), (264, 8), (276, 8), (282, -2), (290, 0),
                    (SHIELD, 0), (SHIELD + 5, 14), (CHECK, 14), (CHECK + 10, 30), (RELIEF - 2, 30),
                    (RELIEF + 6, -5), (RELIEF + 14, 0)], f, ease=servo)
        hr = track([(0, 6), (240, 6), (246, 4), (258, 4), (264, 2), (276, 2), (282, 0),
                    (CHECK, 0), (CHECK + 10, 8), (RELIEF - 2, 8), (RELIEF + 8, 0)], f, ease=servo)
        hy = 13 * math.exp(-max(0, f - SHAKE) / 7) * math.sin(max(0, f - SHAKE) * 1.6) if f > SHAKE else 0

        droop = track([(0, 24), (RISE[0], 24), (RISE[1] + 6, 0)], f)
        twitch = 9 * math.sin((f - BOOT) * 1.7) * math.exp(-(f - BOOT) / 4) if BOOT < f < BOOT + 20 else 0
        fear = track([(SHIELD, 0), (SHIELD + 4, -20), (CHECK, -20), (CHECK + 10, 0)], f)
        perk = -spring(f, RELIEF, 18) - spring(f, SHAKE, 10, decay=6, freq=1.6)
        rise_lag = spring(f, RISE[1] - 10, 8, decay=8, freq=0.8)
        antenna = []
        for i in range(3):
            g = 1.0 + 0.35 * i
            antenna.append((droop * (0.6 + 0.2 * i) + twitch * g + fear / (i + 1) + perk * g + rise_lag * g,
                            spring(f, SHAKE, 8, decay=6, freq=1.6) * g))

        hands, hand_rot, claws = {}, {}, {}
        carry = track([(SHAKE - 4, 0), (SHAKE + 18, 1)], f)
        for side, s in SIDES:
            loc = FOLDED[s].copy()
            loc.z += track([(SHIELD, 0), (SHIELD + 5, -0.012), (CHECK, -0.012), (CHECK + 8, 0)], f)
            if side == 'L':
                loc = loc.lerp(Vector((-0.11, -0.16, 0.2)), track([(CHECK, 0), (CHECK + 8, 1)], f))
            else:
                tap = sum(max(0.0, math.sin(math.pi * (f - t0) / 6)) for t0 in (CHECK + 8, CHECK + 16)
                          if t0 <= f <= t0 + 6)
                loc.y += 0.012 * tap
                loc.x += 0.03 * track([(CHECK + 18, 0), (CHECK + 24, 1), (CHECK + 28, -0.6), (RELIEF, 0)], f)
            hands[s] = loc.lerp(CARRY[s], carry)
            hand_rot[side] = (-20 - 4 * carry, s * 6 * carry, s * 10 * carry)
            claws[side] = track([(0, 0), (CHECK + 6, 0), (CHECK + 10, 6), (RELIEF, 6),
                                 (SHAKE + 18, CLAW_REST_OPEN[side])], f)
        feet = {}
        for side, s in SIDES:
            t0 = SHAKE + (8 if side == 'L' else 18)
            lift = 0.022 * math.sin(math.pi * (f - t0) / 10) if t0 <= f <= t0 + 10 else 0.0
            feet[side] = ((0, 0, lift), (10 * lift / 0.022, 0, 0))
        c.pose(frame, body=(0, 0, z), body_rot=(pitch, roll, 0), head=(hp, hr, hy), yaw=yaw,
               antenna=antenna, feet=feet, hands=hands, hand_rot=hand_rot, claws=claws)
    c.done()


def gait(arm, name, frames, half, stance, lift, crouch=0.0, lean=3.0, head_pitch=2.0,
         antenna_back=0.0, carry=None):
    """Continuous in-place gait (the game moves the character). Feet travel +-half."""
    c = Clip(arm, name, frames)
    tau = 2 * math.pi
    carry = carry or CARRY
    for frame in range(1, frames + 2):          # closing frame repeats the first: seamless loop
        t = (frame - 1) / frames
        feet = {}
        for side, s in SIDES:
            u = (t - (0.0 if side == 'L' else 0.5)) % 1.0
            if u < stance:
                rel, z, sw = -half + 2 * half * u / stance, 0.0, None
            else:
                k = (u - stance) / (1 - stance)
                rel, z, sw = half - 2 * half * smoothstep(k), lift * math.sin(math.pi * k) ** 0.8, k
            dangle = 12 * math.sin(math.pi * sw) if sw is not None else 0.0
            feet[side] = ((0, rel, z), (dangle, 0, 0))
        sway = math.sin(tau * t)
        body = (-0.006 * sway, 0, crouch - 0.003 + 0.004 * math.cos(2 * tau * t - tau * stance / 2))
        body_rot = (lean + 0.8 * math.sin(2 * tau * t - 1.0), -2.0 * sway, 1.2 * math.sin(tau * t + 0.4))
        world_head = (head_pitch, 1.0 * math.sin(tau * t - 1.2), 0.0)
        head = tuple(w - b for w, b in zip(world_head, body_rot))
        antenna = [(antenna_back * (1.0 if i == 0 else 0.25) + 2.5 * math.sin(2 * tau * t - 1.2 - 0.5 * i), 0)
                   for i in range(3)]
        hands = {s: carry[s] + Vector((0, 0.012 * s * math.cos(tau * t), 0.005 * math.sin(2 * tau * t - 1.6)))
                 for _, s in SIDES}
        c.pose(frame, body=body, body_rot=body_rot, head=head, antenna=antenna, feet=feet, hands=hands)
    c.done()


def clip_crouch_idle(arm):
    c = Clip(arm, 'CrouchIdle', 48)
    tau = 2 * math.pi
    for frame in range(1, 50):
        t = (frame - 1) / 48
        c.pose(frame, body=(0, 0, CROUCH + 0.002 * math.sin(tau * t)), body_rot=(6, 0, 0),
               head=(-2 + 1.5 * math.sin(tau * t - 0.6), 0, 0),
               antenna=[(-65 if i == 0 else -12, 0) for i in range(3)], hands=CROUCH_CARRY)
    c.done()


def clip_jump(arm):
    c = Clip(arm, 'JumpStart', 6)
    for frame in range(1, 7):
        k = (frame - 1) / 5
        z = track([(0, 0), (0.6, -0.05), (1, 0.01)], k)
        c.pose(frame, body=(0, 0, z), body_rot=(6 * (1 - k), 0, 0), head=(-4 * k, 0, 0),
               antenna=[(10 * (1 - k), 0)] * 3)
    c.done()
    c = Clip(arm, 'JumpAir', 8)
    for frame in range(1, 10):
        t = (frame - 1) / 8
        feet = {side: ((0, 0.02 * s, 0.07), (18, 0, 0)) for side, s in SIDES}
        hands = {s: CARRY[s] + Vector((s * 0.02, 0.01, 0.06)) for _, s in SIDES}
        c.pose(frame, body=(0, 0, 0.01), body_rot=(4, 0, 0), head=(-6, 0, 0),
               antenna=[(-14 + 3 * math.sin(2 * math.pi * t - i), 0) for i in range(3)],
               feet=feet, hands=hands, claws={'L': 30, 'R': 18})
    c.done()
    c = Clip(arm, 'Land', 10)
    for frame in range(1, 11):
        f = frame - 1
        z = track([(0, 0), (2, -0.05), (10, 0)], f)
        c.pose(frame, body=(0, 0, z), body_rot=(track([(0, 4), (2, 8), (10, 2)], f), 0, 0),
               head=(track([(0, -6), (3, 6), (10, 0)], f), 0, 0),
               antenna=[(spring(f, 0, 14 * (1 + 0.3 * i), decay=4, freq=1.2), 0) for i in range(3)])
    c.done()


def mantle_path(t):
    """Root offset (forward, up) during the mantle; main.js uses the same curve."""
    up = CRATE[2] * smoothstep((t - 0.15) / 0.55)
    fwd = 0.38 * smoothstep((t - 0.25) / 0.75)
    return fwd, up


def clip_mantle(arm):
    frames = 22
    c = Clip(arm, 'Mantle', frames)
    d0 = 0.25                                   # starting distance from the crate face
    for frame in range(1, frames + 1):
        t = (frame - 1) / (frames - 1)
        fwd, up = mantle_path(t)
        edge_fwd, edge_up = d0 - fwd, CRATE[2] - up
        grab = smoothstep(t / 0.15) * (1 - smoothstep((t - 0.72) / 0.2))
        hands = {}
        for _, s in SIDES:
            target = Vector((s * 0.2, -edge_fwd, edge_up + 0.07))
            hands[s] = CARRY[s].lerp(target - REST_WRIST[s], grab)
        scrabble = math.sin(math.pi * min(1, max(0, (t - 0.15) / 0.55)))
        feet = {side: ((0, 0.035 * s * math.sin(t * 30), 0.05 * scrabble), (20 * scrabble, 0, 0))
                for side, s in SIDES}
        lean = 15 * math.sin(math.pi * min(1, max(0, (t - 0.2) / 0.6)))
        c.pose(frame, body=(0, 0, -0.02 * scrabble), body_rot=(4 + lean, 0, 0), head=(-8 * grab, 0, 0),
               antenna=[(-18 * scrabble + 6 * math.sin(t * 20 - i), 0) for i in range(3)],
               feet=feet, hands=hands, claws={'L': 4 + 20 * (1 - grab), 'R': 4 + 20 * (1 - grab)})
    c.done()


def lever_angle(f):
    """Lever pull in degrees from upright-ish, by frame of the Pull clip (main.js matches)."""
    return track([(0, 0), (12, 0), (20, 12), (24, 8), (30, 22), (33, 70), (40, 72)], f)


def lever_grip(f):
    a = math.radians(LATCH_TILT + lever_angle(f))
    px, pz = LATCH_PIVOT
    return Vector((px - LATCH_LEN * math.sin(a), pz + LATCH_LEN * math.cos(a)))


def clip_pull(arm):
    """Crouched under the shutter, both claws on the T-handle, two heaves; it gives on the second."""
    frames = 40
    c = Clip(arm, 'Pull', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        lean_back = track([(0, 0), (12, 0), (20, 0.03), (24, 0.015), (30, 0.05), (34, 0.08), (40, 0.07)], f)
        pitch = track([(0, 6), (12, 6), (20, -12), (24, -6), (30, -16), (34, -8), (40, -4)], f)
        g = lever_grip(min(f, 31))
        reach = smoothstep(f / 8) * (1 - smoothstep((f - 33) / 6))
        hands = {}
        for side, s in SIDES:
            lateral = -0.13 if side == 'R' else 0.09
            target = Vector((lateral, -(g.x - PULL_ROOT_X) + lean_back, g.y + 0.08 - CROUCH))
            hands[s] = CROUCH_CARRY[s].lerp(target - REST_WRIST[s], reach)
        grip = track([(0, 25), (8, 25), (12, 2), (31, 2), (34, 30), (40, 30)], f)
        strain = track([(12, 0), (20, 1), (24, 0.4), (30, 1), (34, 0)], f)
        c.pose(frame, body=(0, lean_back, CROUCH - 0.01 * strain), body_rot=(pitch, 0, 0),
               head=(track([(0, 4), (10, 10), (20, -6), (24, 0), (30, -8), (34, 2)], f),
                     3 * strain * math.sin(f * 2.1), 0),
               antenna=[(-65 + 6 * strain * math.sin(f * 1.7 + i) if i == 0 else -12, 0) for i in range(3)],
               hands=hands, hand_rot={'L': (-10, 0, 20), 'R': (-10, 0, -20)}, claws={'L': grip, 'R': grip})
    c.done()


def clip_flinch(arm):
    """The shutter rattles up: a startled jolt with claws over the head, then a slow peek."""
    frames = 40
    c = Clip(arm, 'Flinch', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        cover = track([(0, 0), (3, 1), (18, 1), (34, 0)], f, ease=lambda x: ease_back(x, 0.6))
        z = CROUCH + track([(0, 0), (3, -0.03), (18, -0.03), (40, 0.0)], f)
        hands = {s: CROUCH_CARRY[s].lerp(Vector((-s * 0.14, -0.06, 0.42)), cover) for _, s in SIDES}
        peek_tilt = track([(16, 0), (26, 10), (40, 6)], f)
        c.pose(frame, body=(0, 0.04 * cover, z), body_rot=(track([(0, 6), (3, -8), (18, -6), (40, 4)], f), 0, 0),
               head=(track([(0, 0), (3, 14), (18, 12), (30, -6), (40, -3)], f), peek_tilt, 0),
               antenna=[(-80 * cover - 40 * (1 - cover) + spring(f, 18, 10, decay=6) * (i + 1), 0) for i in range(3)],
               hands=hands, hand_rot={'L': (-60 * cover - 24 * (1 - cover), 0, 0), 'R': (-60 * cover - 24 * (1 - cover), 0, 0)},
               claws={'L': 4, 'R': 2})
    c.done()


def clip_idle(arm):
    arm.animation_data_create()
    arm.animation_data.action = bpy.data.actions.new('Idle')
    d17.animate_idle(arm, d17.IDLE_FRAMES)
    ad = arm.animation_data
    t = ad.nla_tracks.new()
    t.name = 'Idle'
    t.strips.new('Idle', 1, ad.action)
    ad.action = None


# --------------------------------------------------------------------------
# Export
# --------------------------------------------------------------------------

def export(path, objects):
    bpy.ops.object.select_all(action='DESELECT')
    for ob in objects:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.export_scene.gltf(
        filepath=path, export_format='GLB', use_selection=True, export_apply=True,
        export_yup=True, export_lights=False, export_cameras=False,
        export_animations=True, export_animation_mode='NLA_TRACKS', export_force_sampling=True,
        export_optimize_animation_size=True, export_def_bones=False, export_skins=True,
        export_materials='EXPORT')


def pack_for_web(out, names):
    """Artifact hosting serves .json but not .glb: wrap each GLB as base64 JSON for the page."""
    import base64
    import json
    for n in names:
        with open(os.path.join(out, n + '.glb'), 'rb') as fh:
            data = base64.b64encode(fh.read()).decode('ascii')
        with open(os.path.join(out, n + '.json'), 'w') as fh:
            json.dump({'format': 'glb-base64', 'data': data}, fh)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--blend', default=None)
    args = ap.parse_args()
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 24
    m = set_materials()
    set_coll = bpy.data.collections.new('DL01_Set')
    scene.collection.children.link(set_coll)
    build_set(m, set_coll)

    # Pose D-17 dormant at his start mark to fit the cradle, then return him to the origin:
    # the game places and turns him itself.
    arm = d17.build_robot('D17', tuple(D17_START), 90)
    clip_opening(arm)
    arm.animation_data.action = bpy.data.actions['Opening']
    build_cradle(m, set_coll)
    arm.animation_data.action = None
    arm.location = (0, 0, 0)
    arm.rotation_euler = (0, 0, 0)

    clip_idle(arm)
    gait(arm, 'Walk', 16, half=0.09, stance=0.6, lift=0.03, crouch=-0.012)
    gait(arm, 'CrouchWalk', 18, half=0.0675, stance=0.6, lift=0.022, crouch=CROUCH, lean=6,
         head_pitch=-2, antenna_back=-65, carry=CROUCH_CARRY)
    clip_crouch_idle(arm)
    clip_jump(arm)
    clip_mantle(arm)
    clip_pull(arm)
    clip_flinch(arm)

    for t in arm.animation_data.nla_tracks:
        t.mute = False
    scene.frame_start, scene.frame_end = 1, OPENING_FRAMES

    robot_objs = [o for o in bpy.data.collections['D17'].all_objects if o.type in ('MESH', 'ARMATURE', 'CURVE')]
    export(os.path.join(out, 'd17.glb'), robot_objs)
    set_objs = [o for o in set_coll.all_objects if o.type in ('MESH', 'CURVE')]
    export(os.path.join(out, 'set.glb'), set_objs)
    pack_for_web(out, ('d17', 'set'))
    if args.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend))
    print('exported', out)


if __name__ == '__main__':
    main()
