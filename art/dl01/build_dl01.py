"""Chapter 1 (DL-01 The Wake and DL-02 The Weight of the Job): builds the continuous set and
D-17's gameplay clips, exported for the playable prototype in game/undelivered/. The DL-02 half
lives in art/dl02/build_dl02.py and is called from here.

    python build_dl01.py --out ../../game/undelivered/assets

Writes:
  set.glb       the static set plus the moving parts the game drives by name (shutter assembly,
                latch lever, counterweight, relay lamps, crank wheel, exit door; DL-02's weight,
                trolley, floor plate, gate and gauge needle, rack row lights)
  d17.glb       D-17 rigged, with clips: Opening, Idle, Walk, Run, CrouchWalk, CrouchIdle, JumpStart,
                JumpAir, Land, Mantle, Pull, Flinch, Tug, Crank, Lift, SetDown, SetDownHigh,
                CarryIdle, CarryWalk, Grab, PushIdle, PushWalk, Nudge
  couriers.glb  three baked poses of a dormant courier and the rack slots to instance them at

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
sys.path.insert(0, os.path.join(HERE, '..', 'dl02'))
sys.path.insert(0, os.path.join(HERE, '..', 'dl03'))

import bpy  # noqa: E402  (must precede bmesh/mathutils)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

import build_d17 as d17  # noqa: E402
import build_dl02 as dl02  # noqa: E402
import build_dl03 as dl03  # noqa: E402
from build_d17 import (add_box, add_cyl, add_sphere, add_torus, rounded_box, mesh_object,  # noqa: E402
                       worn_material, emission_material, simple_material, smoothstep, ease_back,
                       SIDES, CLAW_REST_OPEN, _key)

TEX = os.path.join(HERE, 'textures')
D17_START = Vector((1.0, 0.0, 0.0))
OPENING_FRAMES = 480                 # 20 s at 24 fps
DORMANT_YAW = -45.0                  # slumped three-quarters toward camera

# Shared with the game (game/undelivered/index.html keeps the same numbers).
SHUTTER_PATH = [Vector((0.2, 1.60)), Vector((2.0, 0.62)), Vector((3.2, 0.60)), Vector((3.4, 0.02))]
LATCH_PIVOT = Vector((3.36, 0.12))   # (x, z); the lever stands up from here
LATCH_LEN = 0.21
LATCH_TILT = 8.0                     # degrees toward D-17 at rest
PULL_ROOT_X = 3.12
CRATE = (5.6, 6.2, 0.45)             # x0, x1, height (mantle)
STEP = (4.1, 4.9, 0.22)              # fallen conveyor: x0, x1, height (first jump)
PIT = (6.6, 7.1, -0.35)              # drain trench: x0, x1, floor height
HALL_X = 7.3                         # the sorting hall opens up from here
CRANK = (9.62, 0.2, 0.45)            # wheel centre (x, y, z); D-17 faces into the wall to turn it
DOOR = (10.0, 10.8, 1.05)            # exit door in the bulkhead: x0, x1, height
BULKHEAD_Y = 0.62
CORD = (0.42, -0.04, 0.70, 2.05)     # pull-cord lamp: x, y, bead z, shade z
MANTLE_KEYS = [(0, 0.0, 0.0), (6, 0.0, 0.0), (10, 0.03, 0.12), (14, 0.03, 0.18), (20, 0.05, 0.45),
               (24, 0.05, 0.38), (32, 0.10, 0.78), (38, 0.20, 0.95), (44, 0.33, 1.0), (56, 0.38, 1.0)]
MANTLE_FRAMES = 56                   # (frame, forward m, fraction of the ledge height); main.js matches
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
    m['cordbulb'] = emission_material('CordBulb', (1.0, 0.85, 0.6), 0.0)
    m['doorglow'] = emission_material('DoorGlow', (0.6, 0.85, 0.72), 0.0)
    m['water'] = simple_material('Water', (0.01, 0.012, 0.012), 0.05, metallic=0.2)
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


def make_route_map(path):
    """Faded depot route map: tunnels climbing from the depot to the homes, the school, the works
    and the ward, with a 'you are here' dot. Symbols only, no words."""
    from PIL import Image, ImageDraw, ImageFilter
    import random as _r
    rnd = _r.Random(5)
    w, h = 1024, 680
    img = Image.new('RGB', (w, h), (58, 70, 62))
    d = ImageDraw.Draw(img)
    for _ in range(90):
        x, y, r = rnd.randint(0, w), rnd.randint(0, h), rnd.randint(10, 90)
        c = rnd.randint(40, 70)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(c, c + 10, c + 2))
    img = img.filter(ImageFilter.GaussianBlur(14))
    d = ImageDraw.Draw(img)
    ink, faded, red = (214, 206, 176), (150, 150, 128), (178, 64, 52)
    d.rectangle((16, 16, w - 16, h - 16), outline=ink, width=6)
    stations = {'depot': (170, 560), 'homes': (360, 420), 'school': (560, 470), 'works': (700, 300),
                'ward': (840, 170), 'up': (900, 60)}
    for a, b in (('depot', 'homes'), ('homes', 'school'), ('homes', 'works'), ('school', 'works'),
                 ('works', 'ward'), ('ward', 'up')):
        d.line((*stations[a], *stations[b]), fill=faded, width=14)
        d.line((*stations[a], *stations[b]), fill=ink, width=5)
    for name, (x, y) in stations.items():
        d.ellipse((x - 30, y - 30, x + 30, y + 30), fill=(58, 70, 62), outline=ink, width=6)
    x, y = stations['depot']            # parcel glyph
    d.rectangle((x - 16, y - 12, x + 16, y + 14), outline=ink, width=4); d.line((x - 16, y, x + 16, y), fill=ink, width=3)
    x, y = stations['homes']            # house
    d.polygon([(x - 18, y), (x, y - 18), (x + 18, y)], outline=ink, width=4); d.rectangle((x - 13, y, x + 13, y + 16), outline=ink, width=4)
    x, y = stations['school']           # bell
    d.pieslice((x - 16, y - 18, x + 16, y + 14), 180, 360, outline=ink, width=4); d.line((x - 18, y, x + 18, y), fill=ink, width=4)
    d.ellipse((x - 4, y + 4, x + 4, y + 12), fill=ink)
    x, y = stations['works']            # wrench
    d.line((x - 14, y + 14, x + 8, y - 8), fill=ink, width=6); d.ellipse((x + 2, y - 18, x + 20, y), outline=ink, width=4)
    x, y = stations['ward']             # cross
    d.rectangle((x - 5, y - 17, x + 5, y + 17), fill=ink); d.rectangle((x - 17, y - 5, x + 17, y + 5), fill=ink)
    x, y = stations['up']               # arrow up
    d.polygon([(x - 16, y + 8), (x, y - 14), (x + 16, y + 8)], fill=ink); d.rectangle((x - 5, y + 6, x + 5, y + 20), fill=ink)
    x, y = stations['depot']            # you are here
    d.ellipse((x + 34, y - 46, x + 58, y - 22), fill=red)
    for k in range(5):                  # tally marks of past deliveries in the corner
        d.line((60 + k * 18, 600, 66 + k * 18, 640), fill=faded, width=5)
    d.line((52, 630, 150, 606), fill=faded, width=5)
    img = img.filter(ImageFilter.GaussianBlur(1.4))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def build_extension(m, coll):
    """The second half of DL-01: cord lamp and route map, a fallen conveyor to hop onto, the
    drain trench, the sorting hall, and the bulkhead with its crank wheel and exit door."""
    rnd = random.Random(21)
    # Pull-cord lamp over the cradle bay, and the route map it reveals.
    cx, cy, bead, shade = CORD
    bm = bmesh.new()
    add_cyl(bm, (cx, cy, 2.45), (cx, cy, shade + 0.12), 0.004, seg=6)
    add_cyl(bm, (cx, cy, shade + 0.12), (cx, cy, shade), 0.035, 0.11, seg=20)
    obj('CordLampShade', bm, [m['depot_green']], coll)
    bm = bmesh.new()
    add_sphere(bm, (cx, cy, shade - 0.02), 0.03, seg=12)
    obj('CordBulb', bm, [m['cordbulb']], coll)
    rmap = os.path.join(TEX, 'route_map.png')
    if not os.path.exists(rmap):
        make_route_map(rmap)
    textured_plane('RouteMap', (1.0, 0.66), (-0.05, 0.995, 1.25), 90, image_material('RouteMapMat', rmap), coll)
    bm = bmesh.new()
    add_box(bm, (-0.05, 1.0, 1.25), (1.06, 0.01, 0.72))
    obj('RouteMapFrame', bm, [m['steel']], coll)

    # Fallen conveyor: the first thing to jump onto.
    x0, x1, h = STEP
    bm = bmesh.new()
    for y in (-0.22, 0.32):
        add_box(bm, ((x0 + x1) / 2, y, h - 0.03), (x1 - x0, 0.05, 0.06))
    for x in (x0 + 0.05, x1 - 0.05):
        for y in (-0.22, 0.32):
            add_box(bm, (x, y, (h - 0.06) / 2), (0.05, 0.05, h - 0.06))
    add_box(bm, (x0 - 0.1, 0.05, 0.03), (0.24, 0.7, 0.06), rot=Matrix.Rotation(0.25, 4, 'Y'))
    obj('StepFrame', bm, [m['steel']], coll)
    bm = bmesh.new()
    k = 0
    x = x0 + 0.04
    while x < x1 - 0.02:
        add_cyl(bm, (x, -0.2, h - 0.012), (x, 0.3, h - 0.012), 0.016, seg=10)
        x += 0.055
        k += 1
    obj('StepRollers', bm, [m['steel']], coll)

    # Drain trench: broken grate bars hanging in, standing water at the bottom.
    px0, px1, pz = PIT
    bm = bmesh.new()
    for i in range(7):
        y = -0.5 + i * 0.18
        a = Vector((px0 + 0.02, y, -0.01))
        add_cyl(bm, a, a + Vector((rnd.uniform(0.08, 0.2), rnd.uniform(-0.05, 0.05), -rnd.uniform(0.1, 0.3))), 0.008, seg=6)
    for i in range(5):
        y = -0.4 + i * 0.25
        add_cyl(bm, (px1 - 0.02, y, -0.01), (px1 - rnd.uniform(0.05, 0.15), y + 0.03, -rnd.uniform(0.05, 0.2)), 0.008, seg=6)
    obj('TrenchGrate', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_box(bm, ((px0 + px1) / 2, 4.0, pz + 0.025), (px1 - px0 - 0.05, 16, 0.002))
    obj('TrenchWater', bm, [m['water']], coll)

    # The sorting hall: gantry, columns, a huge sorting carousel, chutes, hanging hooks.
    bm = bmesh.new()
    for x in range(6, 17, 2):
        add_box(bm, (x, 4.2, 3.5), (0.3, 0.3, 7))
        add_box(bm, (x + 0.6, 8.0, 3.5), (0.4, 0.4, 7))
    add_box(bm, (11.0, 2.4, 3.2), (12, 0.6, 0.12))
    for x in range(6, 17):
        add_box(bm, (x, 2.15, 3.45), (0.03, 0.03, 0.5))
    add_box(bm, (11.0, 2.15, 3.68), (12, 0.04, 0.04))
    add_torus(bm, (10.5, 7.0, 3.6), (0, 1, 0), 2.6, 0.12, seg=64, rseg=8)
    add_torus(bm, (10.5, 7.0, 3.6), (0, 1, 0), 2.2, 0.06, seg=64, rseg=6)
    for i in range(16):
        a = 2 * math.pi * i / 16
        p = Vector((10.5 + 2.6 * math.cos(a), 7.0, 3.6 + 2.6 * math.sin(a)))
        add_box(bm, p - Vector((0, 0, 0.25)), (0.4, 0.5, 0.06))
        add_cyl(bm, p, p - Vector((0, 0, 0.25)), 0.01, seg=4)
    for x0c, x1c, y in ((7.5, 9.5, 5.5), (12.0, 14.5, 6.0), (13.5, 11.8, 3.6)):
        add_cyl(bm, (x0c, y, 6.5), (x1c, y, 1.6), 0.35, seg=20)
    obj('HallMachinery', bm, [m['steel']], coll)
    for i, (x, length) in enumerate(((7.7, 1.5), (8.5, 1.9), (9.3, 1.3))):
        bm = bmesh.new()
        top = Vector((x, 1.7, 3.2))
        add_cyl(bm, top, top - Vector((0, 0, length)), 0.006, seg=6)
        add_torus(bm, top - Vector((0, 0, length + 0.03)), (1, 0, 0), 0.03, 0.006, seg=12, rseg=4)
        obj(f'Hook{i}', bm, [m['steel']], coll)
        bm = bmesh.new()
        add_box(bm, top - Vector((0, 0, length + 0.16)), (0.26, 0.2, 0.2),
                rot=Matrix.Rotation(rnd.uniform(-0.3, 0.3), 4, 'Z'))
        obj(f'HookParcel{i}', bm, [m['paper']], coll)

    # A live cable hanging from the gantry that sparks now and then.
    bm = bmesh.new()
    pts = [Vector((7.95, 0.75, 3.2)), Vector((7.9, 0.72, 2.2)), Vector((8.0, 0.7, 1.35))]
    for a, b in zip(pts, pts[1:]):
        add_cyl(bm, a, b, 0.012, seg=8)
    obj('LiveCable', bm, [m['rubber']], coll)
    bm = bmesh.new()
    for i in range(5):
        a = Vector((8.0, 0.7, 1.35))
        add_cyl(bm, a, a + Vector((rnd.uniform(-0.06, 0.06), rnd.uniform(-0.06, 0.06), -rnd.uniform(0.02, 0.08))), 0.0015, seg=4)
    obj('CableSpark', bm, [m['spark']], coll)
    bm = bmesh.new()
    add_box(bm, (8.7, 0.45, 0.005), (0.5, 0.4, 0.01))
    for k in range(6):
        add_box(bm, (8.48 + k * 0.088, 0.45, 0.012), (0.02, 0.38, 0.012))
    obj('Vent', bm, [m['steel']], coll)

    # Bulkhead with the exit door and its crank wheel.
    dx0, dx1, dh = DOOR
    by = BULKHEAD_Y
    bm = bmesh.new()
    panels = [(9.1, dx0, 0.0, 2.6), (dx1, 12.45, 0.0, 2.6), (dx0, dx1, dh, 2.6)]   # runs on to hide the passage
    for i, (a0, a1, z0, z1) in enumerate(panels):      # seamed wall panels like the alcove's
        n = max(1, round((a1 - a0) / 0.95))
        for k in range(n):
            w = (a1 - a0) / n
            rounded_box((w - 0.03, 0.3, z1 - z0 - 0.02), (a0 + w * (k + 0.5), by + 0.15, (z0 + z1) / 2), p=12, cuts=8,
                        dents=((0.008, 3.0),), seed=31 + i * 5 + k, bm=bm, mat=0)
    for k in range(2):                                   # end wall closing the lane, kept out of the foreground
        rounded_box((0.4, 0.97, 2.6), (11.9, -1.0 + k * 1.0, 1.3), p=24, cuts=8, dents=((0.004, 3.0),), seed=50 + k, bm=bm, mat=0)
    obj('Bulkhead', bm, [m['wall']], coll)
    bm = bmesh.new()
    add_box(bm, (dx0 - 0.04, by - 0.02, dh / 2), (0.08, 0.08, dh + 0.08))
    add_box(bm, (dx1 + 0.04, by - 0.02, dh / 2), (0.08, 0.08, dh + 0.08))
    add_box(bm, ((dx0 + dx1) / 2, by - 0.02, dh + 0.06), (dx1 - dx0 + 0.16, 0.1, 0.12))
    obj('DoorFrame', bm, [m['yellow']], coll)
    door = []
    n = int(dh / 0.075)
    bm = bmesh.new()
    for k in range(n):
        add_box(bm, ((dx0 + dx1) / 2, by + 0.03, 0.04 + k * 0.075), (dx1 - dx0 - 0.02, 0.025, 0.07))
    obj('ExitDoor', bm, [m['shutter']], coll)
    bm = bmesh.new()
    add_box(bm, ((dx0 + dx1) / 2, by + 0.9, dh / 2 + 0.2), (dx1 - dx0 + 0.6, 0.05, dh + 0.6))
    obj('DoorGlow', bm, [m['doorglow']], coll)
    bm = bmesh.new()
    add_box(bm, ((dx0 + dx1) / 2, by + 0.5, -0.04), (dx1 - dx0, 0.9, 0.08))
    add_box(bm, (dx0 + 0.25, by + 0.75, 0.01), (0.5, 0.5, 0.02))                  # a floor plate beyond
    obj('DoorPassage', bm, [m['concrete']], coll)
    wx, wy, wz = CRANK
    bm = bmesh.new()
    add_box(bm, (wx, wy + 0.16, wz / 2 + 0.05), (0.09, 0.09, wz + 0.1))
    add_cyl(bm, (wx, wy + 0.12, wz), (wx, wy, wz), 0.02, seg=10)
    obj('CrankPost', bm, [m['depot_green']], coll)
    bm = bmesh.new()
    add_torus(bm, (wx, wy, wz), (0, 1, 0), 0.15, 0.012, seg=32, rseg=8)
    for i in range(4):
        a = math.pi * i / 2 + math.pi / 4
        add_cyl(bm, (wx, wy, wz), (wx + 0.15 * math.cos(a), wy, wz + 0.15 * math.sin(a)), 0.007, seg=6)
    add_cyl(bm, (wx, wy - 0.01, wz), (wx, wy + 0.01, wz), 0.03, seg=12)
    obj('CrankWheel', bm, [m['red']], coll)


def build_set(m, coll):
    bm = bmesh.new()
    px0, px1, pz = PIT
    add_box(bm, ((px0 - 5.0) / 2, 4.0, -0.05), (px0 + 5.0, 16, 0.1))
    add_box(bm, ((px1 + 30.0) / 2, 4.0, -0.05), (30.0 - px1, 16, 0.1))
    add_box(bm, ((px0 + px1) / 2, 4.0, pz - 0.05), (px1 - px0, 16, 0.1))
    for x in (px0, px1):  # trench walls
        add_box(bm, (x, 4.0, pz / 2), (0.04, 16, -pz))
    obj('Floor', bm, [m['concrete']], coll)
    bm = bmesh.new()
    add_box(bm, ((-1.5 + px0) / 2, -0.38, 0.0015), (px0 + 1.5, 0.07, 0.003))
    add_box(bm, ((px1 + 11.5) / 2, -0.38, 0.0015), (11.5 - px1, 0.07, 0.003))
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
    for x, y in ((0.35, 0.55), (1.55, 0.6), (2.6, 0.55), (3.7, 0.5), (5.2, -0.45), (6.4, 0.5)):
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
    build_extension(m, coll)

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
    add_box(bm, (7.0, 12.5, 4.0), (20, 0.1, 9))
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
         antenna_back=0.0, carry=None, arm_swing=0.012, bob=0.004, roll=2.0, claws=None):
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
        body = (-0.006 * sway, 0, crouch - 0.003 + bob * math.cos(2 * tau * t - tau * stance / 2))
        body_rot = (lean + 0.8 * math.sin(2 * tau * t - 1.0), -roll * sway, 1.2 * math.sin(tau * t + 0.4))
        world_head = (head_pitch, 1.0 * math.sin(tau * t - 1.2), 0.0)
        head = tuple(w - b for w, b in zip(world_head, body_rot))
        antenna = [(antenna_back * (1.0 if i == 0 else 0.25) + 2.5 * math.sin(2 * tau * t - 1.2 - 0.5 * i), 0)
                   for i in range(3)]
        hands = {s: carry[s] + Vector((0, arm_swing * s * math.cos(tau * t), 0.005 * math.sin(2 * tau * t - 1.6)))
                 for _, s in SIDES}
        c.pose(frame, body=body, body_rot=body_rot, head=head, antenna=antenna, feet=feet, hands=hands, claws=claws)
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


def mantle_at(f):
    """Root offset (forward m, fraction of ledge height) at frame f; main.js uses the same keys."""
    for (f0, w0, u0), (f1, w1, u1) in zip(MANTLE_KEYS, MANTLE_KEYS[1:]):
        if f <= f1:
            k = smoothstep((f - f0) / (f1 - f0)) if f1 > f0 else 1.0
            return w0 + (w1 - w0) * k, u0 + (u1 - u0) * k
    return MANTLE_KEYS[-1][1], MANTLE_KEYS[-1][2]


def clip_mantle(arm):
    """A climb with effort and character: look up, hop and grab, heave, slip back, heave again,
    the old left knee over the edge, tip onto the top, stand, and a glance back down."""
    c = Clip(arm, 'Mantle', MANTLE_FRAMES)
    h = CRATE[2]
    d0 = 0.17                                   # collision stops him this far from the face
    for frame in range(1, MANTLE_FRAMES + 1):
        f = frame - 1
        fwd, frac = mantle_at(f)
        up = frac * h
        ef, eu = d0 - fwd, h - up               # crate edge relative to the root
        grab = track([(6, 0), (10, 1), (40, 1), (46, 0)], f)
        hands = {}
        for side, s in SIDES:
            grip = Vector((s * 0.16, -ef + 0.02, eu + 0.06))
            push = Vector((s * 0.16, -ef + 0.05, eu + 0.1))
            target = grip.lerp(push, track([(36, 0), (44, 1)], f))
            hands[s] = CARRY[s].lerp(target - REST_WRIST[s], grab)
        feet = {}
        for side, s in SIDES:
            if f < 10:
                loc = (0, 0, 0)
            elif (side == 'L' and f < 30) or (side == 'R' and f < 38):
                # Scrabbling against the crate face, feet alternating.
                phase = math.sin((f - 10) * 0.9 + (0 if side == 'L' else math.pi))
                zw = 0.12 + 0.09 * phase + 0.1 * smoothstep((f - 20) / 12)
                loc = (0, -(ef - 0.05), zw - up)
            elif f < 46:
                t0 = 30 if side == 'L' else 38
                k = smoothstep((f - t0) / 6)
                zw = (0.12 + 0.1) * (1 - k) + (h + 0.03) * k
                loc = (0, -((ef - 0.05) * (1 - k) + (ef + 0.08) * k), zw - up)
            else:
                loc = (0, 0, 0)
            rot = (25 * math.sin(math.pi * min(1, max(0, (f - 10) / 30))), 0, 0)
            feet[side] = (loc, rot)
        pitch = track([(0, 0), (6, -6), (10, 4), (20, 12), (24, 8), (32, 18), (38, 30), (44, 6), (50, 2), (56, 0)], f)
        struggle = math.sin(math.pi * min(1, max(0, (f - 12) / 22)))
        roll = 6 * struggle * math.sin(f * 0.9) + spring(f, 44, 5, decay=4, freq=1.4)
        head = (track([(0, 0), (6, -28), (10, -20), (14, -10), (24, -14), (32, -6), (38, 10), (44, 0)], f),
                3 * struggle * math.sin(f * 1.3),
                track([(46, 0), (50, 60), (54, 60), (56, 35)], f))
        body_z = track([(0, 0), (5, -0.04), (9, 0.01), (14, 0), (40, 0), (44, -0.03), (50, 0)], f)
        antenna = [(-12 * struggle + 8 * math.sin(f * 0.8 - i) * struggle + spring(f, 44, 14 * (1 + 0.3 * i), decay=5, freq=1.3)
                    + track([(0, 0), (6, -10), (10, 0)], f), 0) for i in range(3)]
        opening = track([(0, 20), (9, 25), (10, 0), (40, 0), (44, 25), (52, 20)], f)
        c.pose(frame, body=(0, 0, body_z), body_rot=(pitch, roll, 0), head=head, antenna=antenna,
               feet=feet, hands=hands, claws={'L': opening, 'R': opening})
    c.done()


def clip_tug(arm):
    """Reach up for the lamp's pull-cord on tiptoe, grip, tug it down, let go, look up at the light."""
    frames = 44
    c = Clip(arm, 'Tug', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        reach = track([(4, 0), (12, 1), (24, 1), (30, 0)], f)
        pull = track([(14, 0), (19, 1), (23, 1), (26, 0)], f)
        tiptoe = track([(6, 0), (12, 0.035), (15, 0.035), (19, -0.03), (26, 0)], f)
        hands = {}
        for side, s in SIDES:
            if side == 'R':
                target = Vector((-0.08, -0.15, 0.6 - 0.11 * pull))
                hands[s] = CARRY[s].lerp(target - REST_WRIST[s], reach)
            else:
                hands[s] = CARRY[s] + Vector((0, 0.02, 0.03 * reach))
        hand_rot = {'R': (-24 + 194 * reach, 0, 0), 'L': (-24, 6, 10)}
        look = track([(0, 0), (6, -26), (24, -18), (30, -32), (40, -30), (44, -20)], f)
        tilt = track([(26, 0), (34, 9), (44, 6)], f)
        yaw = track([(30, 0), (38, 28), (44, 20)], f)
        feet = {side: ((0, 0, 0), (-8 * tiptoe / 0.035 if tiptoe > 0 else 0, 0, 0)) for side, _ in SIDES}
        antenna = [(track([(0, 0), (8, -8), (24, -6), (28, 0)], f) - spring(f, 26, 14 * (1 + 0.3 * i), decay=6), 0)
                   for i in range(3)]
        c.pose(frame, body=(0, 0, tiptoe), body_rot=(track([(0, 2), (12, -6), (19, 4), (26, 2)], f), 0, 0),
               head=(look, tilt, yaw), antenna=antenna, feet=feet, hands=hands, hand_rot=hand_rot,
               claws={'R': track([(10, 25), (14, 0), (23, 0), (25, 28), (34, CLAW_REST_OPEN['R'])], f),
                      'L': CLAW_REST_OPEN['L']})
    c.done()


def clip_crank(arm):
    """One stroke of the crank wheel (loops): grip the rim, haul it a sixth of a turn,
    let go, reach back, grip again. D-17 faces the wheel, his back to the camera."""
    frames = 24
    c = Clip(arm, 'Crank', frames)
    r, cz, cy = 0.15, CRANK[2], -0.2
    for frame in range(1, frames + 2):
        f = (frame - 1) % frames
        turn = track([(0, 0), (12, 1)], f) if f <= 12 else track([(12, 1), (22, 0)], f)
        lift_off = math.sin(math.pi * (f - 12) / 10) if 12 <= f <= 22 else 0.0
        hands = {}
        for side, s in SIDES:
            a0 = math.radians(40 if side == 'L' else 220)
            a = a0 - math.radians(60) * turn
            target = Vector((r * math.cos(a), cy + 0.04 * lift_off, cz + r * math.sin(a)))
            hands[s] = target - REST_WRIST[s]
        effort = math.sin(math.pi * min(f, 12) / 12) if f <= 12 else 0.0
        c.pose(frame, body=(0, -0.02 * effort, -0.012 - 0.012 * effort),
               body_rot=(8 + 5 * effort, 2.5 * effort, 0),
               head=(track([(0, -6), (8, -12), (14, -4), (24, -6)], f), 2 * effort, 0),
               antenna=[(6 * effort + 3 * math.sin(f * 0.6 - i), 0) for i in range(3)],
               hands=hands, hand_rot={'L': (-30, 0, 30), 'R': (-30, 0, -30)},
               claws={'L': 0 if f < 12 or f > 21 else 26, 'R': 0 if f < 12 or f > 21 else 26})
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
    slots = dl02.build_set(sys.modules[__name__], m, set_coll)
    dl03.build_set(sys.modules[__name__], m, set_coll)

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
    gait(arm, 'Walk', 11, half=0.105, stance=0.58, lift=0.035, crouch=-0.02, bob=0.006, arm_swing=0.016)
    gait(arm, 'Run', 10, half=0.12, stance=0.38, lift=0.065, crouch=-0.035, lean=10, head_pitch=0,
         antenna_back=-14, carry={s: CARRY[s] + Vector((-s * 0.02, 0.02, 0.07)) for _, s in SIDES},
         arm_swing=0.035, bob=0.012, roll=3.0)
    gait(arm, 'CrouchWalk', 13, half=0.08, stance=0.6, lift=0.022, crouch=CROUCH, lean=6,
         head_pitch=-2, antenna_back=-65, carry=CROUCH_CARRY)
    clip_crouch_idle(arm)
    clip_jump(arm)
    clip_mantle(arm)
    clip_pull(arm)
    clip_flinch(arm)
    clip_tug(arm)
    clip_crank(arm)
    dl02.add_clips(sys.modules[__name__], arm)
    dl03.add_clips(sys.modules[__name__], arm)

    for t in arm.animation_data.nla_tracks:
        t.mute = False
    scene.frame_start, scene.frame_end = 1, OPENING_FRAMES

    robot_objs = [o for o in bpy.data.collections['D17'].all_objects if o.type in ('MESH', 'ARMATURE', 'CURVE')]
    export(os.path.join(out, 'd17.glb'), robot_objs)
    set_objs = [o for o in set_coll.all_objects if o.type in ('MESH', 'CURVE')]
    export(os.path.join(out, 'set.glb'), set_objs)
    courier_coll = bpy.data.collections.new('Couriers')
    scene.collection.children.link(courier_coll)
    dl02.build_couriers(sys.modules[__name__], slots, courier_coll)
    export(os.path.join(out, 'couriers.glb'), list(courier_coll.all_objects))
    pack_for_web(out, ('d17', 'set', 'couriers'))
    if args.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend))
    print('exported', out)


if __name__ == '__main__':
    main()
