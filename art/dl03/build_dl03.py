"""DL-03 Return to Sender: the scanner, the return line and the dead-letter pit, D-17's clips for
the scene, and the lore signage. Called from art/dl01/build_dl01.py (chapter 1 is one level).

DL-03 continues straight on from DL-02's recharge hall:
  - a low corridor with the sorting scanner, which reads D-17's label and rejects room 114;
  - the sorting floor, where carriers rise from a dispatch hatch, stop at the dock and are hauled
    by a chain belt to the storage chute, tipping returned parcels into the pit;
  - the pit itself, Dead Letters: decades of undeliverable post under a wall of pigeonholes;
  - the upper gallery over the pit, reached only by riding a carrier up the service ramp once the
    belt is stopped and the points are thrown; at its far end, the residential access (DL-04).

Coordinates as before: metres, Blender Z up, the lane at y = 0, travel along +x.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
from build_d17 import (add_box, add_cyl, add_sphere, add_torus, rounded_box, emission_material,
                       worn_material, simple_material, smoothstep, ease_back, SIDES, CLAW_REST_OPEN)

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')

# Shared with the game (game/undelivered/index.html keeps the same numbers).
CORRIDOR_X0 = 26.9
SCANNER_X = 28.9
FLOOR_X1 = 36.4                      # the sorting floor ends at the pit edge
RAIL_Y = 0.55                        # the return line runs just behind the lane
HATCH_X, DOCK_X, JUNCTION_X, TIP_X = 30.5, 31.0, 34.6, 36.5
BLADE_END = (35.25, 0.32)            # the points blade, raised (x, z)
RAMP_TOP = (38.5, 1.6)
LANDING_X, RETURN_X = 39.7, 41.3     # where a carrier stops on the gallery, and where it drops away
GALLERY = (38.85, 47.4, 1.6)         # x0, x1, deck height
STOP_LEVER_X, POINTS_LEVER_X, LEVER_Y = 32.9, 34.25, 0.3
LEVER_PIVOT_Z, LEVER_LEN = 0.2, 0.42
RESIDENTIAL_X = 47.0
PIT = (36.4, 52.0, -6.0)             # x0, x1, floor height
HEAP = (40.8, 3.0, 0.1, 3.4)         # centre x, centre y, peak height, spread
CARRIER = dict(half=0.31, width=0.42, floor=0.14, rim=0.42)


def _obj(name, bm, mats, coll, sharp=35):
    return d17.mesh_object(name, bm, mats, coll, sharp=sharp)


def _plane(name, size, center, mat, coll, rot=None, uv_repeat=(1, 1)):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5, calc_uvs=True)
    for f in bm.faces:
        for lp in f.loops:
            lp[uv].uv = (lp[uv].uv.x * uv_repeat[0], lp[uv].uv.y * uv_repeat[1])
    m = Matrix.Translation(center) @ (rot or Matrix.Rotation(math.radians(90), 4, 'X')) @ Matrix.Diagonal((size[0], size[1], 1, 1))
    bmesh.ops.transform(bm, verts=bm.verts, matrix=m)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def _image_material(name, path, rough=0.7):
    mat, nt, bsdf = d17._new_material(name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    return mat


# --------------------------------------------------------------------------
# Lore, painted and typed: everything here is read from the walls, never from a log.
# --------------------------------------------------------------------------

def _font(size, kind='sans-bold'):
    from PIL import ImageFont
    paths = {'sans-bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
             'sans': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
             'mono': '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
             'mono-bold': '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
             'serif': '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'}
    try:
        return ImageFont.truetype(paths[kind], size)
    except OSError:
        return ImageFont.load_default()


def _age(img, seed, amount=0.5):
    """Stains, foxing and a little blur, so nothing looks freshly printed."""
    from PIL import ImageDraw, ImageFilter
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img, 'RGBA')
    w, h = img.size
    for _ in range(int(40 * amount)):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(4, w * 0.08)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(70, 50, 25, rnd.randint(6, 22)))
    for _ in range(int(14 * amount)):
        x = rnd.uniform(0, w)
        d.line((x, 0, x + rnd.uniform(-20, 20), h), fill=(40, 30, 20, rnd.randint(6, 16)), width=rnd.randint(2, 8))
    return img.filter(ImageFilter.GaussianBlur(0.7))


def make_textures():
    from PIL import Image, ImageDraw
    os.makedirs(TEX, exist_ok=True)
    ink, cream, green = (28, 26, 22), (222, 212, 184), (34, 58, 44)

    # The notice by the scanner: why room 114 cannot be delivered.
    img = Image.new('RGB', (640, 860), (214, 204, 176))
    d = ImageDraw.Draw(img)
    d.rectangle((18, 18, 622, 842), outline=ink, width=6)
    d.text((48, 50), 'REFUGE POSTAL SERVICE', font=_font(34), fill=ink)
    d.line((48, 100, 592, 100), fill=ink, width=4)
    d.text((48, 130), 'NOTICE', font=_font(64), fill=(120, 30, 26))
    y = 236
    for line in ('RING C IS SEALED.', '', 'Rooms C-100 to C-160', 'are no longer in service.', '',
                 'Post for these rooms will be', 'held at DEAD LETTERS until', 'it is claimed.', '',
                 'Couriers: do not attempt', 'delivery past the seal.'):
        d.text((48, y), line, font=_font(30, 'mono-bold' if line.isupper() else 'mono'), fill=ink)
        y += 46
    d.text((48, 770), 'Depot office  -  Refuge Year 43', font=_font(26, 'mono'), fill=ink)
    _age(img, 1).save(os.path.join(TEX, 'notice_ring_c.png'))

    # The day board: deliveries per day, chalked up year after year, then left.
    img = Image.new('RGB', (900, 640), (30, 36, 32))
    d = ImageDraw.Draw(img)
    rnd = random.Random(5)
    chalk = (206, 210, 196)
    d.rectangle((10, 10, 890, 630), outline=(120, 96, 64), width=18)
    d.text((60, 44), 'DELIVERED PER DAY', font=_font(46), fill=chalk)
    d.text((60, 104), 'refuge year', font=_font(26, 'sans'), fill=(160, 166, 150))
    for _ in range(260):                                        # chalk dust and old rubbings
        x, y = rnd.uniform(20, 880), rnd.uniform(20, 620)
        d.line((x, y, x + rnd.uniform(-60, 60), y + rnd.uniform(-8, 8)), fill=(48, 55, 50), width=rnd.randint(4, 14))
    rows = [('30', '1 240'), ('42', '540'), ('55', '210'), ('68', '96'), ('80', '41'), ('95', '12'),
            ('104', '5'), ('109', '2'), ('110', '')]
    for i, (yr, n) in enumerate(rows):
        x, y = 60 + (i // 5) * 420, 160 + (i % 5) * 88
        jit = lambda: rnd.uniform(-3, 3)  # noqa: E731
        d.text((x + jit(), y + jit()), yr, font=_font(44, 'mono-bold'), fill=chalk)
        d.text((x + 140 + jit(), y + jit()), n, font=_font(44, 'mono'), fill=chalk)
        d.line((x, y + 64, x + 360, y + 64 + jit()), fill=(90, 100, 90), width=2)
    _age(img, 2, 0.3).save(os.path.join(TEX, 'day_board.png'))

    # A service poster from better years.
    img = Image.new('RGB', (600, 860), green)
    d = ImageDraw.Draw(img)
    d.rectangle((24, 24, 576, 836), outline=cream, width=10)
    d.rectangle((150, 150, 450, 420), outline=cream, width=22)
    d.line((150, 240, 450, 240), fill=cream, width=18)
    d.line((300, 150, 300, 420), fill=cream, width=18)
    d.polygon([(470, 240), (560, 285), (470, 330)], fill=cream)
    for i in range(3):
        d.ellipse((200 + i * 80, 470, 240 + i * 80, 510), fill=cream)
    d.text((60, 580), 'REFUGE', font=_font(70), fill=cream)
    d.text((60, 660), 'POSTAL SERVICE', font=_font(48), fill=cream)
    d.text((60, 740), 'Every parcel finds its door.', font=_font(30, 'serif'), fill=(200, 190, 150))
    _age(img, 3, 0.9).save(os.path.join(TEX, 'poster_service.png'))

    # The enamel sign over the pit.
    img = Image.new('RGB', (1600, 400), (24, 26, 24))
    d = ImageDraw.Draw(img)
    d.rectangle((14, 14, 1586, 386), outline=cream, width=12)
    d.text((80, 64), 'DEAD LETTERS', font=_font(172), fill=cream)
    d.text((86, 296), 'UNDELIVERABLE  .  HELD FOR CLAIM  .  DO NOT SORT', font=_font(46, 'sans'), fill=(170, 164, 140))
    _age(img, 4, 0.6).save(os.path.join(TEX, 'dead_letters_sign.png'))

    # The residential access sign, with tape across ring C.
    img = Image.new('RGB', (900, 360), (196, 168, 60))
    d = ImageDraw.Draw(img)
    d.rectangle((12, 12, 888, 348), outline=ink, width=12)
    d.text((44, 46), 'RESIDENTIAL ACCESS', font=_font(64), fill=ink)
    for i, ring in enumerate('ABC'):
        x = 80 + i * 250
        d.rectangle((x, 170, x + 190, 320), outline=ink, width=10)
        d.text((x + 60, 180), ring, font=_font(110), fill=ink)
    d.polygon([(560, 330), (600, 300), (820, 160), (790, 140)], fill=(150, 36, 30))
    d.polygon([(560, 160), (590, 140), (820, 300), (790, 330)], fill=(150, 36, 30))
    _age(img, 6, 0.5).save(os.path.join(TEX, 'residential_sign.png'))

    # The return stamp on the parcels nearest the chute.
    img = Image.new('RGB', (512, 320), (190, 156, 108))
    d = ImageDraw.Draw(img)
    stamp = (150, 40, 34)
    d.rectangle((26, 30, 486, 290), outline=stamp, width=10)
    d.text((54, 60), 'RETURN TO', font=_font(64), fill=stamp)
    d.text((54, 132), 'SENDER', font=_font(64), fill=stamp)
    d.text((54, 220), 'ADDRESS NOT IN SERVICE', font=_font(28), fill=stamp)
    _age(img, 7, 0.8).save(os.path.join(TEX, 'return_stamp.png'))

    # The depot clock, stopped.
    img = Image.new('RGB', (400, 400), (24, 24, 22))
    d = ImageDraw.Draw(img)
    d.ellipse((20, 20, 380, 380), fill=(206, 198, 172), outline=(60, 56, 50), width=14)
    for k in range(12):
        a = k * math.pi / 6
        d.line((200 + 150 * math.sin(a), 200 - 150 * math.cos(a), 200 + 172 * math.sin(a), 200 - 172 * math.cos(a)),
               fill=ink, width=10 if k % 3 == 0 else 5)
    for a, length, w in ((math.radians(4 * 30 + 23), 95, 14), (math.radians(12 * 6), 150, 8)):
        d.line((200, 200, 200 + length * math.sin(a), 200 - length * math.cos(a)), fill=ink, width=w)
    d.ellipse((188, 188, 212, 212), fill=ink)
    _age(img, 8, 0.4).save(os.path.join(TEX, 'clock_face.png'))


# --------------------------------------------------------------------------
# The set
# --------------------------------------------------------------------------

def dl03_materials(m):
    m['scanlamp'] = [emission_material(f'ScanLamp{i}', (1.0, 0.25, 0.12), 0.0) for i in range(3)]
    m['scanbar'] = emission_material('ScanBar', (1.0, 0.2, 0.1), 0.0)
    m['guide'] = emission_material('GuideArrow', (1.0, 0.3, 0.12), 0.0)
    m['docklamp'] = emission_material('DockLamp', (1.0, 0.7, 0.3), 0.0)
    m['interlock'] = emission_material('Interlock', (1.0, 0.2, 0.1), 0.0)
    m['pitbulb'] = emission_material('PitBulb', (1.0, 0.86, 0.66), 0.0)
    m['gallerybulb'] = emission_material('GalleryBulb', (0.9, 0.95, 1.0), 0.0)
    m['carrierlamp'] = emission_material('CarrierLamp', (1.0, 0.6, 0.2), 0.0)
    m['letters'] = worn_material('LetterPaper', base=(0.55, 0.52, 0.45), dirt=(0.3, 0.27, 0.2),
                                 chip=(0.62, 0.6, 0.55), rough=0.9, chip_rough=0.9, metallic=0.0)
    m['pigeon'] = worn_material('PigeonWood', base=(0.12, 0.085, 0.055), dirt=(0.06, 0.045, 0.03),
                                chip=(0.2, 0.15, 0.1), rough=0.85, chip_rough=0.8, metallic=0.0)
    m['chain'] = d17._new_material('ChainBelt')[0]
    m['shaft'] = simple_material('Shaft', (0.005, 0.005, 0.005), 0.9)


def build_corridor(m, coll):
    """The low corridor out of the recharge hall, and the scanner across it."""
    bm = bmesh.new()
    add_box(bm, ((CORRIDOR_X0 + 30.0) / 2, 0.67, 1.2), (30.0 - CORRIDOR_X0, 0.1, 2.4))
    add_box(bm, ((CORRIDOR_X0 + 30.0) / 2, -0.35, 2.45), (30.0 - CORRIDOR_X0, 2.1, 0.1))
    _obj('ScanCorridor', bm, [m['wall']], coll)
    # Scanner arch: posts, the housing with its three lamps, the bar that sweeps down.
    x = SCANNER_X
    bm = bmesh.new()
    for dx in (-0.32, 0.32):                     # a gateway: two frames, so it reads from the side
        for y in (-0.62, 0.62):
            add_box(bm, (x + dx, y, 0.78), (0.1, 0.1, 1.56))
            add_box(bm, (x + dx, y, 0.02), (0.2, 0.2, 0.04))
    add_box(bm, (x, 0.0, 1.68), (0.86, 1.46, 0.24))
    add_box(bm, (x, -0.62, 1.5), (0.74, 0.06, 0.06))
    _obj('ScannerArch', bm, [m['depot_green']], coll)
    bm = bmesh.new()
    for dx in (-0.32, 0.32):
        for y in (-0.56, 0.56):
            add_box(bm, (x + dx, y, 0.8), (0.03, 0.02, 1.4))
    _obj('ScannerRails', bm, [m['steel']], coll)
    for i in range(3):
        bm = bmesh.new()
        add_sphere(bm, (x - 0.08 + 0.08 * i, -0.735, 1.68), 0.022, seg=12, scale=(1, 0.6, 1))
        _obj(f'ScanLamp{i}', bm, [m['scanlamp'][i]], coll)
    bm = bmesh.new()
    add_box(bm, (0, 0, 0), (0.6, 1.1, 0.012))
    ob = _obj('ScanBar', bm, [m['scanbar']], coll)
    ob.location = (x, 0, 1.5)
    # The screen beside it (the game draws the display), and the notice under it.
    bm = bmesh.new()
    add_box(bm, (29.65, 0.6, 1.36), (0.6, 0.08, 0.44))
    _obj('ScannerScreenFrame', bm, [m['steel']], coll)
    notice = _image_material('NoticeMat', os.path.join(TEX, 'notice_ring_c.png'))
    _plane('NoticeRingC', (0.3, 0.4), (27.9, 0.61, 1.15), notice, coll)
    # Guide arrows on the floor, which light toward the chute when a parcel is returned.
    bm = bmesh.new()
    xx = 29.5
    while xx < 36.0:
        for s in (1, -1):
            add_box(bm, (xx, 0.0 + s * 0.06, 0.003), (0.16, 0.035, 0.004), rot=Matrix.Rotation(-s * 0.7, 4, 'Z'))
        xx += 0.55
    _obj('GuideArrows', bm, [m['guide']], coll)


def build_return_line(m, coll):
    """Sorting floor: dispatch hatch, dock, rails with their chain belt, the points, the chute, the ramp."""
    rnd = random.Random(33)
    hx0, hx1 = HATCH_X - 0.36, HATCH_X + 0.36
    # Floor with a hole for the hatch, a shaft below it, and the pit edge.
    bm = bmesh.new()
    add_box(bm, ((30.0 + hx0) / 2, 4.0, -0.05), (hx0 - 30.0, 16, 0.1))
    add_box(bm, ((hx1 + FLOOR_X1) / 2, 4.0, -0.05), (FLOOR_X1 - hx1, 16, 0.1))
    add_box(bm, (HATCH_X, (-4.0 + RAIL_Y - 0.3) / 2, -0.05), (hx1 - hx0, RAIL_Y - 0.3 + 4.0, 0.1))
    add_box(bm, (HATCH_X, (RAIL_Y + 0.3 + 12.0) / 2, -0.05), (hx1 - hx0, 12.0 - RAIL_Y - 0.3, 0.1))
    add_box(bm, (FLOOR_X1 + 0.05, 3.0, -3.0), (0.1, 12, 6.0))           # the pit's near wall, under the floor edge
    _obj('SortingFloor', bm, [m['concrete']], coll)
    bm = bmesh.new()
    add_box(bm, (HATCH_X, RAIL_Y, -0.5), (hx1 - hx0, 0.6, 0.9))
    _obj('HatchShaft', bm, [m['shaft']], coll)
    bm = bmesh.new()
    for y in (RAIL_Y - 0.31, RAIL_Y + 0.31):
        add_box(bm, (HATCH_X, y, 0.004), (hx1 - hx0 + 0.08, 0.04, 0.008))
    for x in (hx0 - 0.02, hx1 + 0.02):
        add_box(bm, (x, RAIL_Y, 0.004), (0.04, 0.66, 0.008))
    _obj('HatchFrame', bm, [m['yellow']], coll)
    # Back wall of the sorting floor, tall, with the poster; a beam and lamps above.
    bm = bmesh.new()
    add_box(bm, ((30.0 + FLOOR_X1) / 2, 1.62, 2.5), (FLOOR_X1 - 30.0, 0.12, 5.0))
    add_box(bm, ((30.0 + FLOOR_X1) / 2, -0.3, 3.4), (FLOOR_X1 - 30.0, 0.2, 0.3))
    _obj('SortingWall', bm, [m['wall']], coll)
    _plane('ServicePoster', (0.6, 0.86), (33.6, 1.555, 1.7), _image_material('PosterMat', os.path.join(TEX, 'poster_service.png')), coll)
    # Rails: from the hatch to the tip, and the branch up the ramp to the gallery.
    rails, sleepers = bmesh.new(), bmesh.new()
    def rail_run(a, b):
        a, b = Vector(a), Vector(b)
        for dy in (-0.12, 0.12):
            add_cyl(rails, (a.x, RAIL_Y + dy, a.y + 0.03), (b.x, RAIL_Y + dy, b.y + 0.03), 0.012, seg=6)
        n = max(1, int((b - a).length / 0.28))
        for k in range(n + 1):
            p = a.lerp(b, k / n)
            add_box(sleepers, (p.x, RAIL_Y, p.y + 0.008), (0.06, 0.34, 0.016))
    rail_run((HATCH_X, 0), (TIP_X, 0))
    rail_run(BLADE_END, RAMP_TOP)
    rail_run(RAMP_TOP, (RETURN_X + 0.3, RAMP_TOP[1]))
    _obj('Rails', rails, [m['steel']], coll)
    _obj('Sleepers', sleepers, [m['wood']], coll)
    # The chain belt along the rail bed (the game scrolls its texture while it runs).
    def belt(name, a, b):
        a, b = Vector(a), Vector(b)
        length = (b - a).length
        ob = _plane(name, (length, 0.07), ((a.x + b.x) / 2, RAIL_Y, (a.y + b.y) / 2 + 0.018), m['chain'], coll,
                    rot=Matrix.Rotation(-math.atan2(b.y - a.y, b.x - a.x), 4, 'Y'), uv_repeat=(length * 6, 1))
        return ob
    belt('ChainBelt0', (HATCH_X + 0.4, 0), (TIP_X - 0.1, 0))
    belt('ChainBelt1', BLADE_END, RAMP_TOP)
    belt('ChainBelt2', RAMP_TOP, (RETURN_X, RAMP_TOP[1]))
    # The points: a hinged blade that lies flat (to the chute) or lifts to meet the ramp.
    bm = bmesh.new()
    length = math.hypot(BLADE_END[0] - JUNCTION_X, BLADE_END[1])
    for dy in (-0.12, 0.12):
        add_box(bm, (length / 2, dy, 0.03), (length, 0.03, 0.03))
    add_box(bm, (length / 2, 0, 0.012), (length, 0.26, 0.012))
    ob = _obj('PointsBlade', bm, [m['steel']], coll)
    ob.location = (JUNCTION_X, RAIL_Y, 0)
    bm = bmesh.new()
    add_cyl(bm, (JUNCTION_X, RAIL_Y - 0.2, 0.03), (JUNCTION_X, RAIL_Y + 0.2, 0.03), 0.03, seg=12)
    add_box(bm, (TIP_X + 0.04, RAIL_Y, 0.08), (0.06, 0.38, 0.12))
    _obj('PointsHeel', bm, [m['red']], coll)
    # The ramp's trestle over the pit edge, and the gallery that it reaches.
    bm = bmesh.new()
    for k in range(6):
        u = k / 5
        x = BLADE_END[0] + (RAMP_TOP[0] - BLADE_END[0]) * u
        z = BLADE_END[1] + (RAMP_TOP[1] - BLADE_END[1]) * u
        base = 0.0 if x < FLOOR_X1 else -3.5
        for dy in (-0.2, 0.2):
            add_box(bm, (x, RAIL_Y + dy, (z + base) / 2), (0.06, 0.06, z - base))
        add_box(bm, (x, RAIL_Y, z - 0.02), (0.08, 0.5, 0.05))
    _obj('RampTrestle', bm, [m['steel']], coll)
    # The storage chute: a long steel trough from the tip down into the heap.
    bm = bmesh.new()
    a, b = Vector((TIP_X + 0.1, -0.05)), Vector((39.3, -2.4))
    ang = math.atan2(b.y - a.y, b.x - a.x)
    rot = Matrix.Rotation(-ang, 4, 'Y')
    mid = (a + b) / 2
    length = (b - a).length
    add_box(bm, (mid.x, RAIL_Y, mid.y), (length, 0.9, 0.03), rot=rot)
    for dy in (-0.45, 0.45):
        add_box(bm, (mid.x, RAIL_Y + dy, mid.y + 0.12), (length, 0.03, 0.26), rot=rot)
    _obj('Chute', bm, [m['shutter']], coll)
    # Guard rail at the pit edge, and the dock: a lamp, a stop line, the route board's frame.
    bm = bmesh.new()
    for y in (-0.55, 0.25):
        add_box(bm, (FLOOR_X1 - 0.08, y, 0.5), (0.05, 0.05, 1.0))
    for z in (0.5, 0.95):
        add_box(bm, (FLOOR_X1 - 0.08, -0.15, z), (0.05, 0.85, 0.04))
    add_box(bm, (DOCK_X, RAIL_Y - 0.3, 0.004), (0.06, 0.12, 0.008))
    _obj('GuardRail', bm, [m['yellow']], coll)
    bm = bmesh.new()
    add_box(bm, (DOCK_X, 1.54, 1.32), (0.82, 0.05, 0.5))
    add_cyl(bm, (DOCK_X + 0.5, 1.5, 1.1), (DOCK_X + 0.5, 1.5, 0.0), 0.02, seg=8)
    _obj('RouteBoardFrame', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_sphere(bm, (DOCK_X + 0.5, 1.46, 1.16), 0.035, seg=12)
    _obj('DockLamp', bm, [m['docklamp']], coll)
    # The two levers: the belt stop (red) and the points (yellow), each pivoting on its stand.
    for name, x, mat in (('StopLever', STOP_LEVER_X, m['red']), ('PointsLever', POINTS_LEVER_X, m['yellow'])):
        bm = bmesh.new()
        add_box(bm, (x, LEVER_Y, 0.1), (0.16, 0.2, 0.2))
        add_box(bm, (x + 0.09, LEVER_Y, 0.25), (0.02, 0.12, 0.5) if name == 'StopLever' else (0.02, 0.12, 0.3))
        _obj(name + 'Stand', bm, [m['depot_green']], coll)
        bm = bmesh.new()
        add_cyl(bm, (0, 0, 0), (0, 0, LEVER_LEN), 0.014, seg=8)
        add_cyl(bm, (-0.07, 0, LEVER_LEN), (0.07, 0, LEVER_LEN), 0.02, seg=10)
        ob = _obj(name, bm, [mat], coll)
        ob.location = (x, LEVER_Y, LEVER_PIVOT_Z)
    bm = bmesh.new()
    add_box(bm, (POINTS_LEVER_X + 0.09, LEVER_Y, 0.55), (0.06, 0.06, 0.08))
    _obj('InterlockBox', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_sphere(bm, (POINTS_LEVER_X + 0.09, LEVER_Y - 0.035, 0.56), 0.02, seg=10)
    _obj('InterlockLamp', bm, [m['interlock']], coll)
    # Overhead lamps on the sorting floor.
    bm, bulbs = bmesh.new(), bmesh.new()
    for x in (31.6, 34.6):
        add_cyl(bm, (x, 0.2, 3.25), (x, 0.2, 2.45), 0.005, seg=6)
        add_cyl(bm, (x, 0.2, 2.45), (x, 0.2, 2.33), 0.05, 0.11, seg=16)
        add_sphere(bulbs, (x, 0.2, 2.35), 0.035, seg=12)
    _obj('FloorLamps', bm, [m['steel']], coll)
    _obj('FloorLampBulbs', bulbs, [m['pitbulb']], coll)


def build_pit(m, coll):
    """Dead Letters: the pit under the chute. Pigeonholes up the far wall, the sign, the lamps."""
    rnd = random.Random(44)
    x0, x1, fz = PIT
    bm = bmesh.new()
    add_box(bm, ((x0 + x1) / 2, 3.0, fz - 0.05), (x1 - x0, 12, 0.1))
    add_box(bm, ((x0 + x1) / 2, 9.1, (fz + 7) / 2), (x1 - x0, 0.2, 7 - fz))
    add_box(bm, (x1, 3.0, (fz + 7) / 2), (0.2, 12, 7 - fz))
    for x in (39.0, 43.5, 48.0):
        add_box(bm, (x, 8.7, (fz + 7) / 2), (0.4, 0.4, 7 - fz))
        add_box(bm, (x, 3.0, 6.6), (0.3, 12, 0.35))
    _obj('PitHall', bm, [m['wall']], coll)
    # The pigeonhole wall: hundreds of cubbies, most of them still holding something.
    bm, letters = bmesh.new(), bmesh.new()
    gx0, gx1, gz0, gz1, cell = 37.5, 51.5, fz + 0.4, 4.6, 0.42
    cols, rows = int((gx1 - gx0) / cell), int((gz1 - gz0) / cell)
    for c in range(cols + 1):
        add_box(bm, (gx0 + c * cell, 8.85, (gz0 + gz1) / 2), (0.03, 0.4, gz1 - gz0))
    for r in range(rows + 1):
        add_box(bm, ((gx0 + gx1) / 2, 8.85, gz0 + r * cell), (gx1 - gx0, 0.4, 0.03))
    for c in range(cols):
        for r in range(rows):
            if rnd.random() < 0.72:
                x, z = gx0 + (c + 0.5) * cell, gz0 + r * cell + 0.02
                for k in range(rnd.randint(1, 3)):
                    add_box(letters, (x + rnd.uniform(-0.08, 0.08), 8.72 + k * 0.03, z + 0.06 + rnd.uniform(0, 0.08)),
                            (0.22, 0.01, 0.14), rot=Matrix.Rotation(rnd.uniform(-0.3, 0.3), 4, 'Y'))
    _obj('Pigeonholes', bm, [m['pigeon']], coll)
    _obj('PigeonLetters', letters, [m['letters']], coll)
    # Returned parcels with their stamps showing: on the heap below the chute, and a stack left by
    # the guard rail, where D-17 stands to look.
    stamp = _image_material('ReturnMat', os.path.join(TEX, 'return_stamp.png'))
    def heap_h(x, y):
        hx, hy, sx, sy, peak = 41.5, HEAP[1], 4.2, 3.0, -0.4
        return fz + (peak - fz) * math.exp(-(((x - hx) / sx) ** 2 + ((y - hy) / sy) ** 2))
    boxes = bmesh.new()
    spots = [(35.55, 0.28, 0.0, 0.34, 0.22, 0.2), (35.92, 0.3, 0.0, 0.28, 0.24, 0.18), (35.7, 0.3, 0.2, 0.26, 0.2, 0.16)]
    for x, y in ((39.4, 1.4), (39.9, 1.0), (40.4, 1.6), (39.1, 2.0), (40.9, 1.2)):
        sz = (rnd.uniform(0.26, 0.4), rnd.uniform(0.2, 0.3), rnd.uniform(0.16, 0.24))
        spots.append((x, y, heap_h(x, y) + sz[2] / 2 - 0.04, *sz))
    for k, (x, y, z, sx, sy, sz) in enumerate(spots):
        zc = z + sz / 2 if z >= 0 else z
        add_box(boxes, (x, y, zc), (sx, sy, sz))
        _plane(f'ReturnStamp{k}', (sx * 0.8, sz * 0.75), (x, y - sy / 2 - 0.003, zc), stamp, coll)
    _obj('ReturnedParcels', boxes, [m['paper']], coll)

    # The enamel sign, hung on chains over the heap.
    sign = _image_material('DeadLettersMat', os.path.join(TEX, 'dead_letters_sign.png'), rough=0.4)
    _plane('DeadLettersSign', (3.2, 0.8), (43.6, 5.0, 3.4), sign, coll)
    bm = bmesh.new()
    add_box(bm, (43.6, 5.02, 3.4), (3.3, 0.03, 0.88))
    for x in (42.2, 45.0):
        add_cyl(bm, (x, 5.0, 3.85), (x, 5.0, 6.6), 0.008, seg=6)
    _obj('DeadLettersSignBack', bm, [m['steel']], coll)
    # Hanging lamps over the heap.
    bm, bulbs = bmesh.new(), bmesh.new()
    for x, y, z in ((39.6, 2.2, 2.6), (43.8, 3.6, 2.9), (48.0, 2.6, 2.4)):
        add_cyl(bm, (x, y, 6.6), (x, y, z + 0.12), 0.006, seg=6)
        add_cyl(bm, (x, y, z + 0.12), (x, y, z), 0.06, 0.16, seg=16)
        add_sphere(bulbs, (x, y, z + 0.02), 0.045, seg=12)
    _obj('PitLamps', bm, [m['steel']], coll)
    _obj('PitLampBulbs', bulbs, [m['pitbulb']], coll)


def build_gallery(m, coll):
    """The upper gallery over the pit: the carriers' landing, the old sorting desk, the clock, the
    day board, and the residential access at the far end."""
    gx0, gx1, gz = GALLERY
    bm = bmesh.new()
    add_box(bm, ((gx0 + gx1) / 2, 0.2, gz - 0.03), (gx1 - gx0, 1.4, 0.06))
    _obj('GalleryDeck', bm, [m['steel']], coll)
    bm = bmesh.new()
    x = gx0
    while x <= gx1 + 1e-6:
        add_box(bm, (x, -0.52, gz + 0.5), (0.04, 0.04, 1.0))
        add_box(bm, (x, 0.88, gz + 0.5), (0.04, 0.04, 1.0))
        add_cyl(bm, (x, 0.2, gz - 0.06), (x, 0.2, 6.6), 0.012, seg=6)
        x += 1.2
    for z in (gz + 0.5, gz + 0.98):
        add_box(bm, ((gx0 + gx1) / 2, -0.52, z), (gx1 - gx0, 0.04, 0.04))
    add_box(bm, ((gx0 + gx1) / 2, 0.88, gz + 0.98), (gx1 - gx0, 0.04, 0.04))
    add_box(bm, (gx0 - 0.02, 0.0, gz + 0.5), (0.04, 1.0, 0.04))
    _obj('GalleryRails', bm, [m['yellow']], coll)
    # Where returned carriers drop back to the dispatch level.
    bm = bmesh.new()
    add_box(bm, (RETURN_X + 0.15, RAIL_Y, gz - 0.02), (0.75, 0.5, 0.05))
    _obj('ReturnSlot', bm, [m['shaft']], coll)
    # The old sorting desk, left as it was: stamps, an ink pad, a stack of letters, a mug.
    bm, paper, inky = bmesh.new(), bmesh.new(), bmesh.new()
    add_box(bm, (42.6, 0.72, gz + 0.42), (0.9, 0.36, 0.04))
    for dx in (-0.4, 0.4):
        for dy in (-0.14, 0.14):
            add_box(bm, (42.6 + dx, 0.72 + dy, gz + 0.2), (0.04, 0.04, 0.4))
    for k, dx in enumerate((-0.25, -0.15)):
        add_cyl(bm, (42.6 + dx, 0.66, gz + 0.44), (42.6 + dx, 0.66, gz + 0.52), 0.018, seg=10)
        add_sphere(bm, (42.6 + dx, 0.66, gz + 0.54), 0.02, seg=8)
    add_cyl(bm, (42.95, 0.64, gz + 0.44), (42.95, 0.64, gz + 0.53), 0.035, 0.032, seg=14)
    add_torus(bm, (42.99, 0.64, gz + 0.49), (0, 1, 0), 0.02, 0.005, seg=10, rseg=4)
    for k in range(9):
        add_box(paper, (42.55 + random.Random(k).uniform(-0.02, 0.02), 0.74, gz + 0.445 + k * 0.006),
                (0.22, 0.15, 0.005), rot=Matrix.Rotation(random.Random(k + 9).uniform(-0.15, 0.15), 4, 'Z'))
    add_box(inky, (42.3, 0.75, gz + 0.45), (0.12, 0.08, 0.012))
    _obj('SortingDesk', bm, [m['steel']], coll)
    _obj('DeskLetters', paper, [m['letters']], coll)
    _obj('InkPad', inky, [m['rubber']], coll)
    # The clock on its post, stopped.
    bm = bmesh.new()
    add_cyl(bm, (41.9, 0.85, gz), (41.9, 0.85, gz + 2.2), 0.03, seg=8)
    add_cyl(bm, (41.9, 0.83, gz + 2.2), (41.9, 0.77, gz + 2.2), 0.2, seg=32)
    _obj('ClockPost', bm, [m['depot_green']], coll)
    clock = _image_material('ClockMat', os.path.join(TEX, 'clock_face.png'), rough=0.3)
    _plane('ClockFace', (0.36, 0.36), (41.9, 0.765, gz + 2.2), clock, coll)
    # The day board on its easel.
    bm = bmesh.new()
    for dx in (-0.5, 0.5):
        add_box(bm, (44.6 + dx, 0.8, gz + 0.75), (0.05, 0.05, 1.5), rot=Matrix.Rotation(0.12, 4, 'X'))
    add_box(bm, (44.6, 0.83, gz + 1.0), (1.02, 0.03, 0.72))
    _obj('DayBoardEasel', bm, [m['wood']], coll)
    board = _image_material('DayBoardMat', os.path.join(TEX, 'day_board.png'), rough=0.9)
    _plane('DayBoard', (0.96, 0.68), (44.6, 0.81, gz + 1.0), board, coll, rot=Matrix.Rotation(math.radians(90 - 7), 4, 'X'))
    # Residential access: a doorway, the sign with tape across ring C.
    bm = bmesh.new()
    add_box(bm, (RESIDENTIAL_X + 0.5, 0.2, gz + 1.6), (0.3, 1.5, 3.2))
    add_box(bm, (RESIDENTIAL_X + 0.1, 0.92, gz + 1.6), (0.9, 0.1, 3.2))
    add_box(bm, (RESIDENTIAL_X + 0.1, 0.2, gz + 2.8), (0.9, 1.5, 0.8))
    _obj('ResidentialWall', bm, [m['wall']], coll)
    rsign = _image_material('ResidentialMat', os.path.join(TEX, 'residential_sign.png'))
    _plane('ResidentialSign', (0.8, 0.32), (RESIDENTIAL_X - 0.2, 0.86, gz + 1.65), rsign, coll)
    bm = bmesh.new()
    add_sphere(bm, (44.0, 0.2, gz + 2.3), 0.035, seg=12)
    add_sphere(bm, (40.5, 0.2, gz + 2.3), 0.035, seg=12)
    _obj('GalleryBulbs', bm, [m['gallerybulb']], coll)
    bm = bmesh.new()
    for x in (44.0, 40.5):
        add_cyl(bm, (x, 0.2, 6.6), (x, 0.2, gz + 2.4), 0.005, seg=6)
        add_cyl(bm, (x, 0.2, gz + 2.42), (x, 0.2, gz + 2.32), 0.05, 0.1, seg=14)
    _obj('GalleryLamps', bm, [m['steel']], coll)


def build_carrier(m, coll):
    """A sorting carrier: an open steel tub on a flanged chassis, a tow hook for the chain, a lamp.
    Origin on the rail at the carrier's centre; the game clones it."""
    h, w, fl, rim = CARRIER['half'], CARRIER['width'], CARRIER['floor'], CARRIER['rim']
    bm = bmesh.new()
    add_box(bm, (0, 0, fl - 0.01), (2 * h, w, 0.02))
    for y in (-w / 2, w / 2):
        add_box(bm, (0, y, (fl + rim) / 2), (2 * h, 0.02, rim - fl))
    for x in (-h, h):
        add_box(bm, (x, 0, (fl + rim) / 2), (0.02, w, rim - fl))
    for x in (-h, h):
        add_box(bm, (x, 0, rim), (0.04, w + 0.03, 0.03))
    for y in (-w / 2, w / 2):
        add_box(bm, (0, y, rim), (2 * h + 0.03, 0.04, 0.03))
    _obj('CarrierTub', bm, [m['shutter']], coll)
    bm = bmesh.new()
    add_box(bm, (0, 0, 0.09), (2 * h - 0.06, 0.2, 0.05))
    for x in (-h + 0.08, h - 0.08):
        for y in (-0.12, 0.12):
            add_cyl(bm, (x, y - 0.015, 0.06), (x, y + 0.015, 0.06), 0.05, seg=14)
            add_cyl(bm, (x, y + (0.02 if y > 0 else -0.02), 0.06), (x, y + (0.026 if y > 0 else -0.026), 0.06), 0.06, seg=14)
    add_box(bm, (h + 0.05, 0, 0.05), (0.08, 0.04, 0.03))
    add_box(bm, (-h - 0.05, 0, 0.05), (0.08, 0.04, 0.03))
    _obj('CarrierChassis', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_sphere(bm, (h - 0.05, -w / 2 - 0.015, rim - 0.06), 0.018, seg=10)
    _obj('CarrierLamp', bm, [m['carrierlamp']], coll)
    bm = bmesh.new()
    add_box(bm, (-0.06, -w / 2 - 0.012, (fl + rim) / 2), (0.2, 0.004, 0.12))
    _obj('CarrierPlate', bm, [m['tag']], coll)
    for n in ('CarrierTub', 'CarrierChassis', 'CarrierLamp', 'CarrierPlate'):
        bpy.data.objects[n].location = (TIP_X + 6.0, -6.0, 0.0)        # parked out of sight; the game clones it


def build_set(dl01, m, coll):
    make_textures()
    dl03_materials(m)
    build_corridor(m, coll)
    build_return_line(m, coll)
    build_pit(m, coll)
    build_gallery(m, coll)
    build_carrier(m, coll)


# --------------------------------------------------------------------------
# D-17 clips
# --------------------------------------------------------------------------

def clip_check_label(dl01, arm):
    """After the rejection: he looks down at his own chest, taps the window twice, reads the label,
    then lifts his head, antenna up, and gives a small nod. The job is still his."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 84
    c = Clip(arm, 'CheckLabel', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        reach = track([(6, 0), (16, 1), (46, 1), (56, 0)], f)
        tap = sum(math.sin(math.pi * (f - t0) / 5) for t0 in (18, 25) if t0 <= f <= t0 + 5)
        window = Vector((-0.06, -0.24 - 0.02 * tap, 0.41))
        right = CARRY[-1].lerp(window - REST[-1], reach)
        hands = {1: CARRY[1] + Vector((0, 0, 0.01 * reach)), -1: right}
        pitch = track([(0, 0), (8, 6), (48, 6), (60, -3), (84, -2)], f)
        head = (track([(0, 0), (8, 30), (46, 32), (58, -4), (64, 8), (70, -2), (84, 0)], f),
                track([(30, 0), (36, 8), (46, 4), (54, 0)], f), 0)
        antenna = [(track([(0, 0), (10, 12), (46, 10), (56, -10), (84, -6)], f) * (0.8 + 0.2 * i)
                    - spring(f, 56, 16 * (1 + 0.3 * i), decay=6), 0) for i in range(3)]
        c.pose(frame, body=(0, 0, track([(0, 0), (8, -0.01), (50, -0.01), (60, 0.006), (84, 0)], f)),
               body_rot=(pitch, 0, 0), head=head, antenna=antenna, hands=hands,
               hand_rot={'L': (-24, 6, 10), 'R': (-24 - 70 * reach, 0, -20 * reach)},
               claws={'L': CLAW_REST_OPEN['L'], 'R': track([(6, 1), (14, 6), (48, 6), (56, 1)], f)})
    c.done()


def lever_handle(angle_deg, dist=0.26):
    """The lever's grip relative to D-17 facing it: forward and height."""
    a = math.radians(angle_deg)
    return Vector((0, -(dist - LEVER_LEN * math.sin(a)), LEVER_PIVOT_Z + LEVER_LEN * math.cos(a)))


LEVER_AWAY, LEVER_NEAR = -18.0, 6.0          # degrees from upright; the game matches


def clip_lever(dl01, arm, name, stuck=False):
    """Facing a floor lever: reach, grip, haul it toward himself (or try to, twice, and fail), let go."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 46 if stuck else 34
    c = Clip(arm, name, frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        if stuck:
            k = 0.06 * (math.sin(math.pi * min(1, max(0, (f - 10) / 7))) + math.sin(math.pi * min(1, max(0, (f - 19) / 7))))
            reach = track([(0, 0), (8, 1), (28, 1), (34, 0)], f)
            strain = track([(10, 0), (13, 1), (17, 0), (19, 0), (22, 1.3), (26, 0)], f)
        else:
            k = track([(0, 0), (10, 0), (22, 1)], f)
            reach = track([(0, 0), (8, 1), (24, 1), (30, 0)], f)
            strain = track([(10, 0), (14, 1), (22, 0.3)], f)
        grip = lever_handle(LEVER_AWAY + (LEVER_NEAR - LEVER_AWAY) * k)
        body = (0, 0.03 * strain + 0.02 * k, -0.02 * reach - 0.01 * strain)
        rot = (track([(0, 0), (8, 8), (12, 8)], f) - 10 * strain, 0, 0)
        targets = {s: grip + Vector((s * 0.05, 0, 0.04)) for _, s in SIDES}
        inv = dl02_reach(targets, body, rot, REST)
        hands = {s: CARRY[s].lerp(inv[s], reach) for _, s in SIDES}
        if stuck:
            head = (track([(0, 0), (8, -10), (28, -8), (34, -18), (46, -16)], f), track([(28, 0), (36, 28), (46, 24)], f),
                    track([(28, 0), (36, 30), (46, 26)], f))
        else:
            head = (track([(0, 0), (8, -10), (22, -2), (30, 0)], f), 0, 0)
        antenna = [(-6 * strain + spring(f, 22 if not stuck else 28, 8 * (1 + 0.3 * i), decay=5), 0) for i in range(3)]
        claw = track([(0, 20), (7, 28), (9, 1), (24 if not stuck else 28, 1), (30 if not stuck else 34, 20)], f)
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands,
               hand_rot={'L': (-60, 0, 20), 'R': (-60, 0, -20)}, claws={'L': claw, 'R': claw})
    c.done()


def dl02_reach(targets, body, body_rot, rest):
    import build_dl02
    return build_dl02.reach(targets, body, body_rot, rest)


def clip_hop(dl01, arm):
    """A small two-footed hop over a rim (into or out of a carrier). The game moves him along the arc."""
    track, spring, Clip, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY
    frames = 24
    c = Clip(arm, 'Hop', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        z = track([(0, 0), (5, -0.06), (8, 0.02), (16, 0.02), (19, -0.06), (24, -0.01)], f)
        tuck = track([(7, 0), (10, 0.06), (15, 0.06), (18, 0)], f)
        feet = {side: ((0, 0.01 * s, tuck), (25 * tuck / 0.06, 0, 0)) for side, s in SIDES}
        hands = {s: CARRY[s] + Vector((s * 0.03 * (tuck / 0.06), 0, 0.05 * (tuck / 0.06))) for _, s in SIDES}
        c.pose(frame, body=(0, 0, z), body_rot=(track([(0, 2), (5, 10), (9, -4), (17, 2), (20, 8), (24, 2)], f), 0, 0),
               head=(track([(0, 0), (5, 8), (9, -8), (18, 4), (24, 0)], f), 0, 0), feet=feet, hands=hands,
               antenna=[(spring(f, 8, -10 * (1 + 0.3 * i), decay=4) + spring(f, 19, 12 * (1 + 0.3 * i), decay=4), 0) for i in range(3)],
               claws={'L': 26, 'R': 18})
    c.done()


def clip_ride(dl01, arm):
    """Crouched in a carrier, claws on the front rim, looking ahead; swaying with the rails (loops)."""
    Clip, REST = dl01.Clip, dl01.REST_WRIST
    frames = 48
    c = Clip(arm, 'Ride', frames)
    tau = 2 * math.pi
    rim = CARRIER['rim'] - CARRIER['floor']
    for frame in range(1, frames + 2):
        t = (frame - 1) / frames
        body = (0, 0, -0.1 + 0.004 * math.sin(2 * tau * t))
        rot = (4 + 1.2 * math.sin(tau * t), 1.5 * math.sin(tau * t + 0.7), 0)
        targets = {s: Vector((s * 0.16, -0.26, rim + 0.05)) for _, s in SIDES}
        hands = dl02_reach(targets, body, rot, REST)
        c.pose(frame, body=body, body_rot=rot, head=(-4 + 2 * math.sin(tau * t - 0.5) - rot[0], 3 * math.sin(tau * t), 0),
               antenna=[(-8 + 4 * math.sin(2 * tau * t - i), 0) for i in range(3)], hands=hands,
               hand_rot={'L': (-50, 0, 20), 'R': (-50, 0, -20)}, claws={'L': 2, 'R': 2})
    c.done()


def clip_refuse(dl01, arm):
    """Not that carrier: he looks up at the route board, shakes his head twice, steps back."""
    track, spring, Clip, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY
    frames = 40
    c = Clip(arm, 'Refuse', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        shake = 14 * math.sin((f - 14) * 0.75) * (1 if 14 <= f <= 30 else 0) * (1 - max(0, f - 24) / 8)
        head = (track([(0, 0), (8, -18), (14, -10), (30, -6), (40, 4)], f), 0,
                track([(0, 0), (8, 22), (14, 0)], f) + shake)
        antenna = [(track([(0, 0), (12, -6), (30, 14), (40, 12)], f) + spring(f, 14, 6), 0) for i in range(3)]
        c.pose(frame, body=(0, track([(28, 0), (36, 0.03)], f), track([(28, 0), (32, -0.012), (40, 0)], f)),
               body_rot=(track([(0, 0), (28, -2), (34, 4), (40, 2)], f), 0, 0), head=head, antenna=antenna,
               hands={s: CARRY[s] + Vector((0, 0.02 * track([(28, 0), (34, 1)], f), 0)) for _, s in SIDES})
    c.done()


def clip_realise(dl01, arm):
    """DL-02, as he walks in among the racks: he stops. His head turns to the couriers, then lifts and
    travels along the rows. The antenna sinks. He looks down at his own chest and touches the window,
    looks back at them for a long moment, and his head goes down."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 156
    c = Clip(arm, 'Realise', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        yaw = track([(0, 0), (14, 0), (40, 52), (56, 58), (76, 34), (88, 0), (118, 0), (128, 46), (144, 40), (156, 22)], f)
        pitch = track([(0, 0), (14, 2), (40, -2), (56, -12), (76, -10), (88, 28), (112, 30), (128, 4), (144, 8), (156, 20)], f)
        tilt = track([(40, 0), (56, 6), (76, -4), (88, 0), (128, 0), (144, 10), (156, 6)], f)
        droop = track([(0, 0), (20, 0), (80, 26), (110, 30), (130, 24), (156, 42)], f)
        reach = track([(90, 0), (100, 1), (116, 1), (126, 0)], f)
        window = Vector((-0.05, -0.24, 0.42))
        hands = {1: CARRY[1] + Vector((0, 0, -0.01 * droop / 42)),
                 -1: (CARRY[-1] + Vector((0, 0, -0.01 * droop / 42))).lerp(window - REST[-1], reach)}
        step = track([(0, 0), (6, 0.03), (14, 0.025)], f)
        feet = {side: ((0, step * (1 if side == 'L' else 0.6), 0.012 * math.sin(math.pi * min(1, f / 8)) if side == 'L' else 0), (0, 0, 0))
                for side, s in SIDES}
        sag = track([(0, 0), (130, -0.008), (156, -0.025)], f)
        c.pose(frame, body=(0, step * 0.8, sag), body_rot=(track([(0, 0), (8, -4), (20, 0), (140, 2), (156, 6)], f), 0, 0),
               head=(pitch, tilt, yaw), feet=feet, hands=hands,
               antenna=[(droop * (0.8 + 0.15 * i) + spring(f, 6, -8), 0) for i in range(3)],
               hand_rot={'L': (-24, 6, 10), 'R': (-24 - 70 * reach, 0, -20 * reach)},
               claws={'L': CLAW_REST_OPEN['L'], 'R': track([(90, 1), (98, 5), (116, 5), (126, 1)], f)})
    c.done()


def add_clips(dl01, arm):
    clip_check_label(dl01, arm)
    clip_lever(dl01, arm, 'LeverPull')
    clip_lever(dl01, arm, 'LeverStuck', stuck=True)
    clip_hop(dl01, arm)
    clip_ride(dl01, arm)
    clip_refuse(dl01, arm)
    clip_realise(dl01, arm)
    # A slow, heavy walk for the moments that need to be taken slowly.
    dl01.gait(arm, 'SadWalk', 16, half=0.08, stance=0.62, lift=0.02, crouch=-0.03, lean=1.0, head_pitch=14,
              antenna_back=22, arm_swing=0.006, bob=0.003, roll=1.5)
