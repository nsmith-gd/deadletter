"""DL-03 Return to Sender: the scanner, the return line and the dead-letter pit, D-17's clips for
the scene, and the lore signage. Called from art/dl01/build_dl01.py (chapter 1 is one level).

DL-03 continues straight on from DL-02's recharge hall:
  - a low corridor with the sorting scanner, which reads D-17's label and rejects room 114;
  - the sorting floor, where carriers rise from a dispatch hatch, stop at the dock and are hauled
    by a chain belt to the storage chute, tipping returned parcels into the pit;
  - the pit itself, Dead Letters: decades of undeliverable post under a wall of pigeonholes;
  - the upper gallery over the pit, reached only by riding a carrier up the service ramp once the
    belt is stopped and the points are thrown; at its far end, the residential access doorway, which
    art/dl04 builds and DL-04 continues through.

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
LANDING_X, RETURN_X = 39.7, 41.3     # where a carrier stops on the gallery, and its return lift
RETURN3 = (35.9,)                    # the return lift on the sorting floor, just short of the tip
GALLERY = (38.85, 47.4, 1.6)         # x0, x1, deck height
STOP_LEVER_X, POINTS_LEVER_X, LEVER_Y = 32.9, 34.25, 0.3
LEVER_PIVOT_Z, LEVER_LEN = 0.2, 0.42
RESIDENTIAL_X = 47.0
PIT = (36.4, 52.0, -6.0)             # x0, x1, floor height
HEAP = (40.8, 3.0, 0.1, 3.4)         # centre x, centre y, peak height, spread
CARRIER = dict(half=0.31, width=0.42, floor=0.14, rim=0.42)

# DL-06 The Heap (docs/chapter1_build_spec.md, section 5): the gallery end of the same space.
GATE_X, GATE_H, GATE_LIFT = 41.9, 1.6, 1.4       # the gallery gate: x, panel height, how far the game lifts it
GATE_Y = (-0.44, 0.82)                           # the panel's span across the gallery (deck y -0.5 to 0.9)
GATE_CHAIN_Y = 0.19                              # the gate's chain, at the panel's top centre
DRUM = (41.7, 5.0)                               # the stepped drum's axle (x, z), along y; GatePulley
DRUM_R = 0.2                                     # the gate's chain winds on this...
HUB_R = DRUM_R * 0.4 / GATE_LIFT                 # ...while the bucket's pays off this: 1.4 m of gate per 0.4 of bucket
BUCKET_X, BUCKET_Y = 39.0, 1.38                  # the bucket hangs behind the gallery, beside the ramp's top end
BUCKET_HOOK_Z, BUCKET_RIM_Z, BUCKET_DROP = 1.55, 1.2, 0.4
IDLER_R = 0.08                                   # the sheave over the bucket
HEAP_WEIGHT_XS = (31.6, 31.85)                   # two sorting weights by the dock, on the lane
SLIDE_X = (35.7, 38.9)                           # the return slide: its lip on the sorting floor, its head at the gallery
SLIDE_Y, SLIDE_W = -0.4, 0.48                    # centre line and inner width (front edge of the lane)
SLIDE_TOP_FLAT, SLIDE_RUNOUT, SLIDE_RUNOUT_Z = 38.65, 35.98, 0.06
SLIDE_LIP = (35.78, 0.08)                        # where the run-out ends, and the radius of the lip
HEAP_LETTER = (43.4, -0.47, 2.3)                 # snagged on the gallery's front rail
MAILSLOT6 = (44.2, 0.3, 2.15)                    # the slot's mouth: 0.3 behind the lane, 0.55 above the deck
CLOCK_X, DAYBOARD_X = 40.7, 45.3                 # moved along the gallery to make room for the gate and MailSlot6


def slide_surface(x):
    """Height of the slide's sliding surface at x (the curve the game moves D-17 along)."""
    gz = GALLERY[2]
    if x >= SLIDE_TOP_FLAT:
        return gz
    if x >= SLIDE_RUNOUT:
        t = (x - SLIDE_RUNOUT) / (SLIDE_TOP_FLAT - SLIDE_RUNOUT)
        return SLIDE_RUNOUT_Z + (gz - SLIDE_RUNOUT_Z) * smoothstep(t)
    return SLIDE_RUNOUT_Z


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
                 'Post for these rooms will be', 'held in the returns pit', 'until it is claimed.', '',
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
    d.text((80, 70), 'UNDELIVERABLE', font=_font(164), fill=cream)
    d.text((86, 296), 'HELD FOR CLAIM  .  DO NOT SORT', font=_font(46, 'sans'), fill=(170, 164, 140))
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
    rx0, rx1 = RETURN3[0] - 0.36, RETURN3[0] + 0.36                    # the return lift's hatch by the tip
    add_box(bm, ((hx1 + rx0) / 2, 4.0, -0.05), (rx0 - hx1, 16, 0.1))
    add_box(bm, ((rx1 + FLOOR_X1) / 2, 4.0, -0.05), (FLOOR_X1 - rx1, 16, 0.1))
    add_box(bm, ((rx0 + rx1) / 2, (-4.0 + RAIL_Y - 0.3) / 2, -0.05), (rx1 - rx0, RAIL_Y - 0.3 + 4.0, 0.1))
    add_box(bm, ((rx0 + rx1) / 2, (RAIL_Y + 0.3 + 12.0) / 2, -0.05), (rx1 - rx0, 12.0 - RAIL_Y - 0.3, 0.1))
    add_box(bm, ((30.0 + FLOOR_X1) / 2, -3.8, -1.4), (FLOOR_X1 - 30.0, 0.4, 2.8))     # the slab's thickness, seen from the pit
    add_box(bm, (FLOOR_X1 - 0.05, 3.0, -1.0), (0.1, 13.6, 2.0))
    add_box(bm, (HATCH_X, (-4.0 + RAIL_Y - 0.3) / 2, -0.05), (hx1 - hx0, RAIL_Y - 0.3 + 4.0, 0.1))
    add_box(bm, (HATCH_X, (RAIL_Y + 0.3 + 12.0) / 2, -0.05), (hx1 - hx0, 12.0 - RAIL_Y - 0.3, 0.1))
    add_box(bm, (FLOOR_X1 + 0.05, 3.0, -3.0), (0.1, 12, 6.0))           # the pit's near wall, under the floor edge
    _obj('SortingFloor', bm, [m['concrete']], coll)
    bm = bmesh.new()
    add_box(bm, (HATCH_X, RAIL_Y, -0.5), (hx1 - hx0, 0.6, 0.9))
    add_box(bm, ((rx0 + rx1) / 2, RAIL_Y, -0.5), (rx1 - rx0, 0.6, 0.9))
    _obj('HatchShaft', bm, [m['shaft']], coll)
    bm = bmesh.new()
    for c0, c1 in ((hx0, hx1), (rx0, rx1)):
        for y in (RAIL_Y - 0.31, RAIL_Y + 0.31):
            add_box(bm, ((c0 + c1) / 2, y, 0.004), (c1 - c0 + 0.08, 0.04, 0.008))
        for x in (c0 - 0.02, c1 + 0.02):
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
    # Lamps up the ramp, beside the rail: dark until the points are set to it, then they run upward.
    for k in range(6):
        u = (k + 0.5) / 6
        x = BLADE_END[0] + (RAMP_TOP[0] - BLADE_END[0]) * u
        z = BLADE_END[1] + (RAMP_TOP[1] - BLADE_END[1]) * u
        bm = bmesh.new()
        add_box(bm, (x, RAIL_Y + 0.27, z + 0.05), (0.07, 0.05, 0.04))
        _obj(f'RampLamp{k}', bm, [emission_material(f'RampLamp{k}', (0.55, 1.0, 0.65), 0.0)], coll)
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
    # The rail stops short of the lane's front edge, where the return slide comes down past it (DL-06).
    bm = bmesh.new()
    for y in (-0.08, 0.25):
        add_box(bm, (FLOOR_X1 - 0.08, y, 0.5), (0.05, 0.05, 1.0))
    for z in (0.5, 0.95):
        add_box(bm, (FLOOR_X1 - 0.08, 0.085, z), (0.05, 0.38, 0.04))
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
    # Both handles are red (things he can use are red); the stands tell them apart.
    for name, x, stand in (('StopLever', STOP_LEVER_X, m['depot_green']), ('PointsLever', POINTS_LEVER_X, m['yellow'])):
        mat = m['red']
        bm = bmesh.new()
        add_box(bm, (x, LEVER_Y, 0.1), (0.16, 0.2, 0.2))
        add_box(bm, (x + 0.09, LEVER_Y, 0.25), (0.02, 0.12, 0.5) if name == 'StopLever' else (0.02, 0.12, 0.3))
        _obj(name + 'Stand', bm, [stand], coll)
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
    add_box(bm, (x1, 5.45, (fz + 7) / 2), (0.2, 7.1, 7 - fz))           # behind DL-04's goods hall (y > 1.9)
    for x in (39.0, 43.5, 48.0):
        add_box(bm, (x, 8.7, (fz + 7) / 2), (0.4, 0.4, 7 - fz))
        if x < 47.0:
            add_box(bm, (x, 3.0, 6.6), (0.3, 12, 0.35))
        else:
            add_box(bm, (x, 5.45, 6.6), (0.3, 7.1, 0.35))
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
    r0, r1 = RETURN_X - 0.36, RETURN_X + 0.36
    add_box(bm, ((gx0 + r0) / 2, 0.2, gz - 0.03), (r0 - gx0, 1.4, 0.06))
    add_box(bm, ((r1 + gx1) / 2, 0.2, gz - 0.03), (gx1 - r1, 1.4, 0.06))
    add_box(bm, ((r0 + r1) / 2, (-0.5 + RAIL_Y - 0.3) / 2, gz - 0.03), (r1 - r0, RAIL_Y - 0.3 + 0.5, 0.06))
    add_box(bm, ((r0 + r1) / 2, (RAIL_Y + 0.3 + 0.9) / 2, gz - 0.03), (r1 - r0, 0.9 - RAIL_Y - 0.3, 0.06))
    _obj('GalleryDeck', bm, [m['steel']], coll)
    # DL-06: the front rail starts past the slide's head (open from gx0 to 39.15), the back rail past
    # the bucket (open from gx0 to 39.45, where carriers tip), and the end rail is only a short stub
    # behind the lane, clear of the slide's mouth and of the carriers coming off the ramp.
    bm = bmesh.new()
    fx0, bx0 = 39.15, 39.45
    x = gx0
    while x <= gx1 + 1e-6:
        add_box(bm, (max(x, fx0), -0.52, gz + 0.5), (0.04, 0.04, 1.0))
        add_box(bm, (max(x, bx0), 0.88, gz + 0.5), (0.04, 0.04, 1.0))
        add_cyl(bm, (x, 0.2, gz - 0.06), (x, 0.2, 6.6), 0.012, seg=6)
        x += 1.2
    for z in (gz + 0.5, gz + 0.98):
        add_box(bm, ((fx0 + gx1) / 2, -0.52, z), (gx1 - fx0, 0.04, 0.04))
    add_box(bm, ((bx0 + gx1) / 2, 0.88, gz + 0.98), (gx1 - bx0, 0.04, 0.04))
    add_box(bm, (gx0 - 0.02, 0.1, gz + 0.5), (0.04, 0.4, 0.04))         # clamped to the hanger rod at y 0.2
    _obj('GalleryRails', bm, [m['yellow']], coll)
    # Where returned carriers drop back to the dispatch level.
    bm = bmesh.new()
    for y in (RAIL_Y - 0.33, RAIL_Y + 0.33):
        add_box(bm, (RETURN_X, y, gz + 0.004), (0.8, 0.04, 0.008))
    for x in (RETURN_X - 0.38, RETURN_X + 0.38):
        add_box(bm, (x, RAIL_Y, gz + 0.004), (0.04, 0.7, 0.008))
    _obj('ReturnSlot', bm, [m['yellow']], coll)
    bm = bmesh.new()                                                      # the duct the empties go down
    for y in (RAIL_Y - 0.34, RAIL_Y + 0.34):
        add_box(bm, (RETURN_X, y, (gz - 0.06 + PIT[2]) / 2), (0.74, 0.03, gz - 0.06 - PIT[2]))
    for x in (RETURN_X - 0.37, RETURN_X + 0.37):
        add_box(bm, (x, RAIL_Y, (gz - 0.06 + PIT[2]) / 2), (0.03, 0.7, gz - 0.06 - PIT[2]))
    _obj('ReturnDuct', bm, [m['shutter']], coll)
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
    # (It stood at 41.9 until the gallery gate took that spot; it is lower now, under the lamp.)
    bm = bmesh.new()
    ch = 2.0
    add_cyl(bm, (CLOCK_X, 0.85, gz), (CLOCK_X, 0.85, gz + ch), 0.03, seg=8)
    add_cyl(bm, (CLOCK_X, 0.83, gz + ch), (CLOCK_X, 0.77, gz + ch), 0.2, seg=32)
    _obj('ClockPost', bm, [m['depot_green']], coll)
    clock = _image_material('ClockMat', os.path.join(TEX, 'clock_face.png'), rough=0.3)
    _plane('ClockFace', (0.36, 0.36), (CLOCK_X, 0.765, gz + ch), clock, coll)
    # The day board on its easel (moved right of MailSlot6).
    bm = bmesh.new()
    for dx in (-0.5, 0.5):
        add_box(bm, (DAYBOARD_X + dx, 0.8, gz + 0.75), (0.05, 0.05, 1.5), rot=Matrix.Rotation(0.12, 4, 'X'))
    add_box(bm, (DAYBOARD_X, 0.83, gz + 1.0), (1.02, 0.03, 0.72))
    _obj('DayBoardEasel', bm, [m['wood']], coll)
    board = _image_material('DayBoardMat', os.path.join(TEX, 'day_board.png'), rough=0.9)
    _plane('DayBoard', (0.96, 0.68), (DAYBOARD_X, 0.81, gz + 1.0), board, coll, rot=Matrix.Rotation(math.radians(90 - 7), 4, 'X'))
    # Residential access: the sign with tape across ring C, by the doorway (art/dl04 builds the wall).
    bm = bmesh.new()
    add_box(bm, (RESIDENTIAL_X + 0.1, 0.92, gz + 1.6), (0.9, 0.1, 3.2))
    _obj('ResidentialReturn', bm, [m['wall']], coll)
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


# --------------------------------------------------------------------------
# DL-06 The Heap: the gallery gate and its counterweight bucket, the sorting weights, the return
# slide, the letter on the rail and MailSlot6 (docs/chapter1_build_spec.md, section 5).
# --------------------------------------------------------------------------

def _basis(d, n):
    """4x4 rotation taking local X to d and local Z to n (n is made perpendicular to d)."""
    d = Vector(d).normalized()
    n = (Vector(n) - d * Vector(n).dot(d)).normalized()
    return Matrix((d, n.cross(d), n)).transposed().to_4x4()


def _chain(bm, a, b, R=0.026, r=0.0065, stretch=1.45, mat=0):
    """Interlocking oval links from a to b, alternately turned through 90 degrees."""
    a, b = Vector(a), Vector(b)
    d = (b - a).normalized()
    n1 = d.cross(Vector((0, 1, 0)) if abs(d.y) < 0.9 else Vector((1, 0, 0))).normalized()
    n2 = d.cross(n1).normalized()
    pitch = 2 * (R * stretch - r)                       # inside length of a link
    n = max(1, round((b - a).length / pitch))
    step = (b - a).length / n
    for k in range(n):
        verts = add_torus(bm, (0, 0, 0), (0, 0, 1), R, r, mat=mat, seg=6, rseg=3)
        bmesh.ops.transform(bm, verts=verts, matrix=Matrix.Translation(a + d * step * (k + 0.5))
                            @ _basis(d, n1 if k % 2 == 0 else n2) @ Matrix.Diagonal((stretch, 1, 1, 1)))
    return n


def _sweep(bm, stations, section, mat=0, cap=True):
    """Extrude a closed cross-section along stations [(origin, u, v)]; a vertex is origin + u*a + v*b."""
    rings = [[bm.verts.new(o + u * a + v * b) for a, b in section] for o, u, v in stations]
    k = len(section)
    for r0, r1 in zip(rings, rings[1:]):
        for j in range(k):
            bm.faces.new((r0[j], r0[(j + 1) % k], r1[(j + 1) % k], r1[j])).material_index = mat
    if cap:
        bm.faces.new(rings[0][::-1]).material_index = mat
        bm.faces.new(rings[-1]).material_index = mat
    return rings


def _hopper(bm, top_c, top, bot, depth, t, mat=0):
    """An open tapered box: top centre, top (x, y) and bottom (x, y) outer sizes, depth, wall thickness."""
    c = Vector(top_c)
    def ring(z, sx, sy):
        return [bm.verts.new(c + Vector((px * sx / 2, py * sy / 2, z))) for px, py in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    ot, ob = ring(0, *top), ring(-depth, *bot)
    k = (top[0] - bot[0]) / depth                        # the walls' slope, to inset the inside evenly
    it, ib = ring(0, top[0] - 2 * t, top[1] - 2 * t), ring(-depth + t, bot[0] - 2 * t + k * t, bot[1] - 2 * t + k * t)
    for j in range(4):
        n = (j + 1) % 4
        for f in ((ob[j], ob[n], ot[n], ot[j]), (it[j], it[n], ib[n], ib[j]), (ot[j], ot[n], it[n], it[j])):
            bm.faces.new(f).material_index = mat
    bm.faces.new(ob[::-1]).material_index = mat
    bm.faces.new(ib).material_index = mat


def heap_textures():
    from PIL import Image, ImageDraw, ImageFilter
    # The light shaft over the letter: soft-edged, fading upward, with a few dust streaks.
    w, h = 64, 256
    img = Image.new('RGBA', (w, h))
    px = img.load()
    rnd = random.Random(61)
    streaks = [(rnd.uniform(0.15, 0.85), rnd.uniform(0.03, 0.08), rnd.uniform(0.1, 0.3)) for _ in range(5)]
    for i in range(w):
        u = (i + 0.5) / w
        across = math.sin(math.pi * u) ** 1.6
        across *= 1 + sum(s * math.exp(-((u - c) / wd) ** 2) for c, wd, s in streaks)
        for j in range(h):
            v = 1 - (j + 0.5) / h                          # 0 at the bottom (the deck), 1 at the top
            along = smoothstep(v / 0.06) * (0.35 + 0.65 * (1 - v) ** 0.8)
            a = min(1.0, 0.42 * across * along)
            px[i, j] = (255, 238, 208, int(255 * a))
    img.save(os.path.join(TEX, 'heap_shaft.png'))
    # MailSlot6's plate: an envelope going into a slot, and a stamp. Wordless.
    img = Image.new('RGB', (128, 128), (200, 192, 168))
    d = ImageDraw.Draw(img)
    ink = (30, 34, 30)
    d.rectangle((4, 4, 123, 123), outline=ink, width=5)
    d.rectangle((26, 30, 102, 40), fill=ink)                     # the slot
    d.rectangle((40, 52, 88, 84), outline=ink, width=5)          # the envelope
    d.line((40, 52, 64, 70), fill=ink, width=4)
    d.line((88, 52, 64, 70), fill=ink, width=4)
    d.polygon([(64, 44), (54, 50), (74, 50)], fill=ink)          # up into the slot
    d.ellipse((44, 92, 84, 116), outline=(150, 40, 34), width=4)  # the stamp it gets
    img.filter(ImageFilter.GaussianBlur(0.6)).save(os.path.join(TEX, 'slot_picto.png'))


def _letter_material():
    """HeapLetter's paper: the Sorting Hall's shared letter atlas (art/sorting_hall/textures/letter_heap.png:
    the front on the left half, the back with the child's drawing on the right), or plain paper if it
    is missing."""
    p = os.path.join(HERE, '..', 'sorting_hall', 'textures', 'letter_heap.png')
    if os.path.exists(p):
        return _image_material('HeapLetterMat', p, rough=0.85)
    return simple_material('HeapLetterMat', (0.62, 0.58, 0.5), 0.85)


def build_heap(m, coll):
    gz = GALLERY[2]
    heap_textures()

    # The gallery gate: a shutter running in two channels, its chain up to the stepped drum.
    gy = (GATE_Y[0] + GATE_Y[1]) / 2
    span = GATE_Y[1] - GATE_Y[0]
    bm = bmesh.new()
    add_box(bm, (0, 0, GATE_H / 2), (0.03, span, GATE_H))
    for k in range(1, 16):
        add_box(bm, (0, 0, k * 0.1), (0.05, span - 0.02, 0.022))     # the shutter's ribs
    add_box(bm, (0, 0, GATE_H - 0.025), (0.06, span, 0.05))
    add_box(bm, (0, 0, 0.035), (0.07, span, 0.07), mat=1)            # a heavy bottom bar, safety yellow
    add_torus(bm, (0, GATE_CHAIN_Y - gy, GATE_H + 0.03), (1, 0, 0), 0.025, 0.007, seg=10, rseg=4)
    gate = _obj('GalleryGate', bm, [m['shutter'], m['yellow']], coll)
    gate.location = (GATE_X, gy, gz)
    # Its chain is its child, so it rises with it. The top end, where it meets the drum, runs on up
    # into the guide tube as the gate rises, so the chain never shows past the drum.
    bm = bmesh.new()
    top = DRUM[1] - 0.02
    n_gate = _chain(bm, (0, GATE_CHAIN_Y - gy, GATE_H + 0.05), (0, GATE_CHAIN_Y - gy, top - gz))
    ob = _obj('GateChain', bm, [m['steel']], coll, sharp=100)
    ob.parent = gate
    # The gate's frame: two channels, a header, hangers up to the roof, and the chain's guide tube.
    bm = bmesh.new()
    fh = 4.8
    for y, s in ((GATE_Y[0], -1), (GATE_Y[1], 1)):
        add_box(bm, (GATE_X, y + s * 0.02, (gz + fh) / 2), (0.1, 0.02, fh - gz))            # web
        for dx in (-0.042, 0.042):
            add_box(bm, (GATE_X + dx, y + s * 0.01 - s * 0.025, (gz + fh) / 2), (0.012, 0.07, fh - gz))
        add_box(bm, (GATE_X, y + s * 0.045, gz + 0.01), (0.2, 0.05, 0.02))                  # foot plate
        add_cyl(bm, (GATE_X, y + s * 0.02, fh), (GATE_X, y + s * 0.02, 6.6), 0.012, seg=6)
    add_box(bm, (GATE_X, gy, fh + 0.05), (0.12, span + 0.1, 0.1))
    add_box(bm, (GATE_X, GATE_CHAIN_Y, (DRUM[1] + 0.05 + 6.45) / 2), (0.07, 0.07, 6.45 - DRUM[1] - 0.05))
    add_box(bm, ((DRUM[0] + 0.1 + GATE_X) / 2, GATE_CHAIN_Y, 6.35), (GATE_X - DRUM[0] - 0.1, 0.05, 0.05))
    # The hoist: a beam along the gallery roof (between the hall's roof beams at 39.0 and 43.5), a
    # cross beam over the drum, the drum's two bearings on drop rods, and the sheave block's hanger.
    add_box(bm, ((39.0 + 43.5) / 2, BUCKET_Y, 6.375), (4.5, 0.1, 0.1))
    add_box(bm, (DRUM[0] + 0.05, (GATE_CHAIN_Y - 0.2 + BUCKET_Y + 0.2) / 2, 6.35), (0.1, BUCKET_Y - GATE_CHAIN_Y + 0.4, 0.12))
    for y in (GATE_CHAIN_Y - 0.11, BUCKET_Y + 0.1):
        add_box(bm, (DRUM[0], y, DRUM[1]), (0.12, 0.05, 0.1))
        add_box(bm, (DRUM[0], y, (DRUM[1] + 6.29) / 2), (0.04, 0.03, 6.29 - DRUM[1]))
    add_box(bm, (BUCKET_X + IDLER_R, BUCKET_Y, (5.45 + 6.34) / 2), (0.04, 0.04, 6.34 - 5.45))
    _obj('GalleryGateFrame', bm, [m['steel']], coll)

    # GatePulley: the stepped drum. The gate's chain winds on the big wheel (r 0.2, its right side
    # over the gate) while the bucket's chain pays off the small hub at the back (r 0.057), so the
    # gate rises 1.4 for the bucket's 0.4. Origin on the axle, which runs along y; the game turns it.
    bm = bmesh.new()
    wy = 0.0                                           # the big wheel, over the gate's chain
    add_torus(bm, (0, wy, 0), (0, 1, 0), DRUM_R - 0.022, 0.024, seg=24, rseg=6)
    add_cyl(bm, (0, wy - 0.035, 0), (0, wy + 0.035, 0), 0.05, seg=12)
    for k in range(4):
        add_box(bm, (0, wy, 0), (2 * DRUM_R - 0.04, 0.025, 0.035), rot=Matrix.Rotation(k * math.pi / 4, 4, 'Y'))
    add_cyl(bm, (0, -0.135, 0), (0, BUCKET_Y - GATE_CHAIN_Y + 0.125, 0), 0.022, seg=10)      # the shaft
    hy = BUCKET_Y - GATE_CHAIN_Y
    add_cyl(bm, (0, hy - 0.045, 0), (0, hy + 0.045, 0), HUB_R, seg=12)
    for dy in (-0.05, 0.05):
        add_cyl(bm, (0, hy + dy - 0.006, 0), (0, hy + dy + 0.006, 0), HUB_R + 0.03, seg=12)
    ob = _obj('GatePulley', bm, [m['shutter']], coll)
    ob.location = (DRUM[0], GATE_CHAIN_Y, DRUM[1])

    # The sheave over the bucket, in its block, and the run of chain along the roof to the hub.
    bm = bmesh.new()
    add_torus(bm, (0, 0, 0), (0, 1, 0), IDLER_R - 0.012, 0.014, seg=16, rseg=5)
    add_cyl(bm, (0, -0.02, 0), (0, 0.02, 0), 0.03, seg=10)
    ob = _obj('GateSheave', bm, [m['shutter']], coll)
    ob.location = (BUCKET_X + IDLER_R, BUCKET_Y, DRUM[1] + HUB_R - IDLER_R)
    idler_z = DRUM[1] + HUB_R - IDLER_R
    bm = bmesh.new()
    for dy in (-0.045, 0.045):                                     # cheeks, tall enough to hide the chain's spare end
        add_box(bm, (BUCKET_X + IDLER_R - 0.01, BUCKET_Y + dy, (idler_z - 0.11 + 5.47) / 2), (0.24, 0.01, 5.47 - idler_z + 0.11))
    add_box(bm, (BUCKET_X + IDLER_R - 0.01, BUCKET_Y, 5.47), (0.24, 0.1, 0.03))
    add_cyl(bm, (BUCKET_X + IDLER_R, BUCKET_Y - 0.06, idler_z), (BUCKET_X + IDLER_R, BUCKET_Y + 0.06, idler_z), 0.012, seg=8)
    _obj('GateSheaveBlock', bm, [m['steel']], coll)
    bm = bmesh.new()
    run_z = DRUM[1] + HUB_R
    _chain(bm, (BUCKET_X + IDLER_R, BUCKET_Y, run_z), (DRUM[0], BUCKET_Y, run_z))
    _obj('GateChainRun', bm, [m['steel']], coll, sharp=100)

    # GateBucket: a steel hopper on a bail, hanging behind the gallery beside the ramp's top end.
    # Origin at its chain hook; the game lowers it (and BucketChain with it) 0.4 as it fills.
    rim = BUCKET_RIM_Z - BUCKET_HOOK_Z
    top, bot, depth = (0.56, 0.52), (0.3, 0.28), 0.42
    bm = bmesh.new()
    _hopper(bm, (0, 0, rim), top, bot, depth, 0.02)
    for s in (-1, 1):                                              # the rim, safety yellow
        add_box(bm, (s * top[0] / 2, 0, rim + 0.012), (0.03, top[1] + 0.03, 0.03), mat=1)
        add_box(bm, (0, s * top[1] / 2, rim + 0.012), (top[0] + 0.03, 0.03, 0.03), mat=1)
    for z in (rim - 0.16, rim - 0.3):                              # stiffening bands
        f = (rim - z) / depth
        add_box(bm, (0, -(top[1] - (top[1] - bot[1]) * f) / 2 - 0.004, z), (top[0] - (top[0] - bot[0]) * f, 0.012, 0.03))
    bail = [(top[0] / 2 + 0.03, rim + 0.02), (top[0] / 2 + 0.03, rim + 0.12), (0.17, rim + 0.3), (0.0, -0.035)]
    for s in (-1, 1):
        add_cyl(bm, (s * (top[0] / 2 - 0.01), 0, rim + 0.02), (s * (top[0] / 2 + 0.05), 0, rim + 0.02), 0.022, seg=10)
        for (x0, z0), (x1, z1) in zip(bail, bail[1:]):
            add_cyl(bm, (s * x0, 0, z0), (s * x1, 0, z1), 0.011, seg=6)
    add_torus(bm, (0, 0, -0.005), (1, 0, 0), 0.028, 0.008, seg=10, rseg=4)
    add_box(bm, (0, 0, -0.04), (0.08, 0.03, 0.02))
    bucket = _obj('GateBucket', bm, [m['shutter'], m['yellow']], coll)
    bucket.location = (BUCKET_X, BUCKET_Y, BUCKET_HOOK_Z)
    # Its chain: hook to the sheave, plus the spare that stays in the block until the bucket drops.
    bm = bmesh.new()
    n_bucket = _chain(bm, (0, 0, 0.02), (0, 0, idler_z - BUCKET_HOOK_Z + BUCKET_DROP + 0.03))
    ob = _obj('BucketChain', bm, [m['steel']], coll, sharp=100)
    ob.parent = bucket                                             # it drops with the bucket
    # The tipping spout: from the deck's back edge down over the bucket's front half.
    bm = bmesh.new()
    a, b = Vector((0.9, gz)), Vector((1.2, gz - 0.27))
    ang = math.atan2(b.y - a.y, b.x - a.x)
    mid = (a + b) / 2
    ln = (b - a).length
    add_box(bm, (BUCKET_X, mid.x, mid.y - 0.008), (0.62, ln, 0.016), rot=Matrix.Rotation(ang, 4, 'X'))
    for s in (-1, 1):
        add_box(bm, (BUCKET_X + s * 0.31, mid.x, mid.y + 0.03), (0.012, ln, 0.08), rot=Matrix.Rotation(ang, 4, 'X'))
    add_box(bm, (BUCKET_X, 0.9, gz - 0.04), (0.66, 0.03, 0.06))
    _obj('BucketSpout', bm, [m['shutter']], coll)

    # Two sorting weights by the dock, the same casting as DL-03's (art/dl02 SortWeight), on the lane.
    for i, x in enumerate(HEAP_WEIGHT_XS):
        bm = bmesh.new()
        add_cyl(bm, (0, 0, 0.0), (0, 0, 0.02), 0.088, 0.09, seg=24)
        add_cyl(bm, (0, 0, 0.02), (0, 0, 0.12), 0.09, 0.075, seg=24)
        add_cyl(bm, (0, 0, 0.12), (0, 0, 0.15), 0.075, 0.035, seg=24)
        add_torus(bm, (0, 0, 0.165), (1, 0, 0), 0.042, 0.009, seg=20, rseg=6)
        weight = _obj(f'HeapWeight{i}', bm, [m['red']], coll)
        weight.location = (x, 0, 0)
        weight.rotation_euler = (0, 0, math.radians(8 - 21 * i))   # not quite lined up
        bm = bmesh.new()
        add_cyl(bm, (0, 0, 0.07), (0, 0, 0.09), 0.0905, 0.0885, seg=24)
        ob = _obj(f'HeapWeight{i}Band', bm, [m['paper']], coll)
        ob.parent = weight                                         # the game moves the weight; the band goes with it

    # ReturnSlide: a steel parcel slide along the lane's front edge, from the gallery's end down past
    # the ramp, the chute and the pit to the sorting floor, with a rounded lip at the bottom.
    pts = []                                                       # (x, z) on the sliding surface, head first
    for k in range(4):
        x = GALLERY[0] - (GALLERY[0] - SLIDE_TOP_FLAT) * k / 3
        pts.append(Vector((x, gz)))
    for k in range(1, 41):
        x = SLIDE_TOP_FLAT - (SLIDE_TOP_FLAT - SLIDE_RUNOUT) * k / 40
        pts.append(Vector((x, slide_surface(x))))
    for k in range(1, 4):
        pts.append(Vector((SLIDE_RUNOUT - (SLIDE_RUNOUT - SLIDE_LIP[0]) * k / 3, SLIDE_RUNOUT_Z)))
    lc = Vector((SLIDE_LIP[0], SLIDE_RUNOUT_Z - SLIDE_LIP[1]))
    for k in range(1, 8):
        th = math.radians(90 + 70 * k / 7)
        pts.append(lc + SLIDE_LIP[1] * Vector((math.cos(th), math.sin(th))))
    frames = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        nrm = Vector((t.y, -t.x))
        frames.append((Vector((p.x, 0, p.y)), Vector((0, 1, 0)), Vector((nrm.x, 0, nrm.y))))
    y0, y1, wt, bed = SLIDE_Y - SLIDE_W / 2, SLIDE_Y + SLIDE_W / 2, 0.025, 0.03
    # The walls are low at the head (so he can get in) and fade out round the lip.
    # Lower near the bottom too, where he walks past it on the sorting floor.
    wall = [(0.13 * smoothstep((GALLERY[0] - p.x) / 0.3) + 0.05) * (1 - 0.92 * smoothstep((SLIDE_LIP[0] - p.x) / 0.07))
            * (0.6 + 0.4 * smoothstep((p.x - SLIDE_RUNOUT) / 0.9)) for p in pts]
    bm = bmesh.new()
    rings = []
    for (o, u, v), h in zip(frames, wall):
        sec = [(y0 - wt, -bed), (y1 + wt, -bed), (y1 + wt, h), (y1, h), (y1, 0), (y0, 0), (y0, h), (y0 - wt, h)]
        rings.append([bm.verts.new(o + u * a + v * b) for a, b in sec])
    for r0, r1 in zip(rings, rings[1:]):
        for j in range(8):
            bm.faces.new((r0[j], r0[(j + 1) % 8], r1[(j + 1) % 8], r1[j]))
    bm.faces.new(rings[0][::-1])
    bm.faces.new(rings[-1])
    for yc in (y0 - wt / 2, y1 + wt / 2):                          # rolled edges along the walls' tops
        sec = [(0.016 * math.cos(2 * math.pi * j / 6), 0.016 * math.sin(2 * math.pi * j / 6)) for j in range(6)]
        _sweep(bm, [(o + u * yc + v * h, u, v) for (o, u, v), h in zip(frames, wall)], sec)
    # Legs: over the pit down into the dark (like the ramp's trestle), on the floor short feet.
    for x in (37.0, 37.75, 38.45):
        zt = slide_surface(x) - bed - 0.05
        for y in (y0 + 0.03, y1 - 0.03):
            add_box(bm, (x, y, (zt - 3.5) / 2), (0.05, 0.05, zt + 3.5))
        add_box(bm, (x, SLIDE_Y, zt + 0.02), (0.07, SLIDE_W + 0.04, 0.05))
        add_box(bm, (x, SLIDE_Y, zt - 0.6), (0.04, SLIDE_W - 0.04, 0.04))
    for x in (35.86, 36.12, 36.34):                                # feet under the run-out
        zt = slide_surface(x) - bed
        add_box(bm, (x, SLIDE_Y, zt / 2), (0.08, SLIDE_W, zt))
    _obj('ReturnSlide', bm, [m['shutter']], coll)

    # HeapLetter: caught by a twist of parcel twine on the gallery's front rail, in a shaft of light.
    # Origin at its centre; the front (address side) faces the camera.
    lx, ly, lz = HEAP_LETTER
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    add_box(bm, (0, 0, 0), (0.16, 0.004, 0.11))
    bm.normal_update()
    for f in bm.faces:
        n = f.normal
        for lp in f.loops:
            co = lp.vert.co
            u, v = co.x / 0.16 + 0.5, co.z / 0.11 + 0.5
            # Atlas: the front (facing -y, the camera) on the left half, the back on the right half.
            lp[uv].uv = (0.5 * u, v) if n.y < -0.5 else (0.5 + 0.5 * (1 - u), v) if n.y > 0.5 else (0.49, 0.5)
    letter = _obj('HeapLetter', bm, [_letter_material()], coll)
    letter.location = (lx, ly, lz)
    letter.rotation_euler = (math.radians(-8), math.radians(17), math.radians(-6))
    bm = bmesh.new()
    corner = Vector((lx - 0.05, ly + 0.004, lz + 0.065))
    twine = [Vector((lx - 0.08, -0.52, gz + 0.98)), Vector((lx - 0.095, -0.5, gz + 0.9)), corner + Vector((-0.012, 0, 0.02)),
             corner + Vector((0.01, 0.006, -0.006)), Vector((lx - 0.03, -0.505, gz + 0.86)), Vector((lx - 0.05, -0.52, gz + 0.98))]
    for p0, p1 in zip(twine, twine[1:]):
        add_cyl(bm, p0, p1, 0.0025, seg=5)
    add_cyl(bm, twine[0], twine[0] + Vector((0.01, -0.012, -0.12)), 0.0025, seg=5)   # a loose end
    _obj('HeapLetterTwine', bm, [m['paper']], coll)
    shaft = d17._new_material('HeapShaftMat')
    mat, nt, bsdf = shaft
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(os.path.join(TEX, 'heap_shaft.png'), check_existing=True)
    bsdf.inputs['Base Color'].default_value = (0, 0, 0, 1)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Emission Color'])
    nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Emission Strength'].default_value = 0.8
    if hasattr(mat, 'surface_render_method'):
        mat.surface_render_method = 'BLENDED'
    slope = 0.073                                                  # light from up and a little to the right
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    zb, zt = gz + 0.005, 6.4
    xb, xt = lx - slope * (lz - zb), lx + slope * (zt - lz)
    sy = ly + 0.05                                                 # just behind the letter
    vs = [bm.verts.new(p) for p in ((xb - 0.17, sy, zb), (xb + 0.17, sy, zb), (xt + 0.09, sy, zt), (xt - 0.09, sy, zt))]
    f = bm.faces.new(vs)
    for lp, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uvl].uv = c
    _obj('HeapLightShaft', bm, [mat], coll)

    # MailSlot6: a pillar box on the gallery's back edge beside the old sorting desk. Origin at the
    # slot's mouth, 0.3 behind the lane and 0.55 above the deck; SlotLamp6 sits on its cap.
    mx, my, mz = MAILSLOT6
    bm = bmesh.new()
    bz = mz - gz                                                   # 0.55: the deck is at local -0.55
    add_cyl(bm, (0, 0.12, -bz), (0, 0.12, -0.17), 0.055, seg=14)
    add_box(bm, (0, 0.12, -bz + 0.01), (0.2, 0.2, 0.02))
    add_box(bm, (0, 0.12, 0.02), (0.26, 0.24, 0.36))
    add_box(bm, (0, 0.12, 0.215), (0.29, 0.27, 0.03))
    add_cyl(bm, (-0.145, 0.12, 0.23), (0.145, 0.12, 0.23), 0.07, seg=16)
    add_box(bm, (0, -0.002, 0), (0.15, 0.006, 0.024), mat=2)                         # the slot itself, dark
    for (cx, cz, sx, sz) in ((0, 0.024, 0.2, 0.016), (0, -0.024, 0.2, 0.016), (-0.092, 0, 0.016, 0.064), (0.092, 0, 0.016, 0.064)):
        add_box(bm, (cx, -0.006, cz), (sx, 0.014, sz), mat=1)                         # its red rim
    add_box(bm, (0, -0.02, 0.04), (0.2, 0.04, 0.008), mat=1, rot=Matrix.Rotation(-0.35, 4, 'X'))   # the hood
    add_cyl(bm, (0, -0.004, 0.27), (0, 0.07, 0.27), 0.034, seg=12)                   # the lamp's bezel
    slot = _obj('MailSlot6', bm, [m['depot_green'], m['red'], m['shaft']], coll)
    slot.location = MAILSLOT6
    _plane('MailSlot6Plate', (0.1, 0.1), (mx, my - 0.002, mz - 0.1), _image_material('SlotPictoMat', os.path.join(TEX, 'slot_picto.png')), coll)
    bm = bmesh.new()
    add_sphere(bm, (0, 0, 0), 0.026, seg=12, scale=(1, 0.7, 1))
    ob = _obj('SlotLamp6', bm, [emission_material('SlotLamp6', (1.0, 0.62, 0.25), 0.0)], coll)
    ob.location = (mx, my - 0.012, mz + 0.27)
    return dict(gate_links=n_gate, bucket_links=n_bucket)


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
    build_heap(m, coll)
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
        right = dl01.window_reach(-1, CARRY[-1], reach, tap)     # elbow out, the claw turned in to the glass
        hands = {1: CARRY[1] + Vector((0, 0, 0.01 * reach)), -1: right}
        pitch = track([(0, 0), (8, 6), (48, 6), (60, -3), (84, -2)], f)
        head = (track([(0, 0), (8, 30), (46, 32), (58, -4), (64, 8), (70, -2), (84, 0)], f),
                track([(30, 0), (36, 8), (46, 4), (54, 0)], f), 0)
        antenna = [(track([(0, 0), (10, 12), (46, 10), (56, -10), (84, -6)], f) * (0.8 + 0.2 * i)
                    - spring(f, 56, 16 * (1 + 0.3 * i), decay=6), 0) for i in range(3)]
        c.pose(frame, body=(0, 0, track([(0, 0), (8, -0.01), (50, -0.01), (60, 0.006), (84, 0)], f)),
               body_rot=(pitch, 0, 0), head=head, antenna=antenna, hands=hands,
               hand_rot={'L': (-24, 6, 10), 'R': dl01.window_claw(-1, reach)}, elbows={'R': reach},
               claws={'L': CLAW_REST_OPEN['L'], 'R': track([(6, 1), (14, 6), (48, 6), (56, 1)], f)})
    c.done()


def lever_handle(angle_deg, dist=0.26):
    """The lever's grip relative to D-17 facing it: forward and height."""
    a = math.radians(angle_deg)
    return Vector((0, -(dist - LEVER_LEN * math.sin(a)), LEVER_PIVOT_Z + LEVER_LEN * math.cos(a)))


def lever_shaft(angle_deg, z=0.37, dist=0.26):
    """The point on the lever's shaft at height z, relative to D-17 facing it. The T-handle is at his
    eye level and, pushed away, beyond his reach, so he grips the shaft at shoulder height."""
    return Vector((0, -(dist - (z - LEVER_PIVOT_Z) * math.tan(math.radians(angle_deg))), z))


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
        shaft = lever_shaft(LEVER_AWAY + (LEVER_NEAR - LEVER_AWAY) * k)
        # Leaning in to reach it, then back as it comes; the wrists out to the shaft's sides (elbows
        # out) and the claws closing on it from both sides.
        body = (0, -0.03 * reach * (1 - k) + 0.03 * k, -0.02 * reach - 0.01 * strain)
        rot = (track([(0, 0), (8, 8), (12, 8)], f) - 10 * strain, 0, 0)
        targets = {s: shaft + Vector((s * 0.12, 0.03, 0.025)) for _, s in SIDES}
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
               hand_rot={side: (-24 - 36 * reach ** 2, s * (6 + 58 * reach ** 2), -s * (-10 + 56 * reach ** 2))
                         for side, s in SIDES},
               claws={'L': claw, 'R': claw}, elbows={'L': reach, 'R': reach})
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
               hand_rot={'L': (-50, 0, 20), 'R': (-50, 0, -20)}, claws={'L': 2, 'R': 2},
               elbows={'L': 1, 'R': 1})      # crouched, the claws come up past the pod: elbows out
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
        hands = {1: CARRY[1] + Vector((0, 0, -0.01 * droop / 42)),     # right: elbow out, claw turned in to the glass
                 -1: dl01.window_reach(-1, CARRY[-1] + Vector((0, 0, -0.01 * droop / 42)), reach)}
        step = track([(0, 0), (6, 0.03), (14, 0.025)], f)
        feet = {side: ((0, step * (1 if side == 'L' else 0.6), 0.012 * math.sin(math.pi * min(1, f / 8)) if side == 'L' else 0), (0, 0, 0))
                for side, s in SIDES}
        sag = track([(0, 0), (130, -0.008), (156, -0.025)], f)
        c.pose(frame, body=(0, step * 0.8, sag), body_rot=(track([(0, 0), (8, -4), (20, 0), (140, 2), (156, 6)], f), 0, 0),
               head=(pitch, tilt, yaw), feet=feet, hands=hands,
               antenna=[(droop * (0.8 + 0.15 * i) + spring(f, 6, -8), 0) for i in range(3)],
               hand_rot={'L': (-24, 6, 10), 'R': dl01.window_claw(-1, reach)}, elbows={'R': reach},
               claws={'L': CLAW_REST_OPEN['L'], 'R': track([(90, 1), (98, 5), (116, 5), (126, 1)], f)})
    c.done()


# --------------------------------------------------------------------------
# Quirks: small, specific reactions for particular moments
# --------------------------------------------------------------------------

def clip_attention(dl01, arm):
    """Under the scanner: he notices it, stands to attention as the bar sweeps him, follows it down
    with his eyes, and deflates at the refusal (frame 77, 3.2 s; the game's scan timing matches)."""
    track, spring, Clip, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY
    frames = 108
    c = Clip(arm, 'Attention', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        stand = track([(4, 0), (14, 1), (77, 1), (84, 0)], f)
        deflate = track([(77, 0), (86, 1)], f)
        follow = track([(12, -14), (53, 16), (60, 6), (70, 4)], f) if f < 77 else 4
        head = (track([(0, 0), (6, -18), (12, -14)], f) * (1 - stand) + follow * stand + 22 * deflate,
                track([(60, 0), (66, 6), (77, 0)], f), track([(30, 0), (36, -6), (44, 0)], f))
        antenna = [(-18 * stand + 32 * deflate * (0.8 + 0.15 * i) + spring(f, 8, -10) + spring(f, 77, 8, decay=5), 0) for i in range(3)]
        hands = {s: CARRY[s].lerp(CARRY[s] + Vector((s * 0.025, 0.02, -0.03)), stand).lerp(CARRY[s] + Vector((0, -0.01, -0.045)), deflate)
                 for _, s in SIDES}
        feet = {side: ((-s * 0.012 * stand, 0, 0), (0, 0, 0)) for side, s in SIDES}
        c.pose(frame, body=(0, 0, 0.008 * stand - 0.025 * deflate), body_rot=(-5 * stand + 7 * deflate, 0, 0),
               head=head, antenna=antenna, hands=hands, feet=feet,
               claws={'L': track([(4, CLAW_REST_OPEN['L']), (12, 2), (80, 2), (90, 14)], f),
                      'R': track([(4, CLAW_REST_OPEN['R']), (12, 2)], f)})
    c.done()


def clip_proud(dl01, arm):
    """It worked: two little bounces on his toes, chest out, antenna wiggling, a nod."""
    track, spring, Clip, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY
    frames = 40
    c = Clip(arm, 'Proud', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        bounce = sum(math.sin(math.pi * (f - t0) / 7) for t0 in (6, 15) if t0 <= f <= t0 + 7)
        tiptoe = 0.02 * max(0.0, bounce)
        feet = {side: ((0, 0, 0), (-10 * max(0.0, bounce), 0, 0)) for side, s in SIDES}
        hands = {s: CARRY[s] + Vector((s * 0.02 * max(0.0, bounce), 0, 0.03 * max(0.0, bounce))) for _, s in SIDES}
        c.pose(frame, body=(0, 0, tiptoe), body_rot=(track([(0, 0), (6, -6), (26, -5), (40, 0)], f), 0, 0),
               head=(track([(0, 0), (6, -10), (24, -8), (29, 8), (34, -2), (40, 0)], f), track([(4, 0), (10, 8), (24, 6), (32, 0)], f), 0),
               antenna=[(-10 + 9 * math.sin(f * 1.3 - i) * math.exp(-f / 22) + spring(f, 6, -10 * (1 + 0.3 * i)), 0) for i in range(3)],
               feet=feet, hands=hands, claws={'L': 22 + 10 * max(0.0, bounce), 'R': 4 + 18 * max(0.0, bounce)})
    c.done()


def clip_peek_down(dl01, arm):
    """At an edge: he leans out, one claw on the rail, and looks right down; a tiny recoil, a step back."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 72
    c = Clip(arm, 'PeekDown', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        lean = track([(0, 0), (16, 1), (46, 1), (52, 0.55), (64, 0.5), (72, 0)], f)
        recoil = track([(44, 0), (48, 1), (58, 0)], f)
        body, rot = (0, -0.03 * lean + 0.02 * recoil, -0.015 * lean), (16 * lean - 6 * recoil, 0, 0)
        rail = {1: Vector((0.27, -0.24, 0.5)), -1: Vector((-0.27, -0.24, 0.5))}   # out beside his head as he leans over
        import build_dl02
        held = build_dl02.reach(rail, body, rot, REST)
        hands = {1: CARRY[1].lerp(held[1], track([(4, 0), (14, 1), (60, 1), (70, 0)], f)), -1: CARRY[-1]}
        head = (track([(0, 0), (16, 34), (44, 40), (48, 18), (58, 26), (72, 4)], f), track([(20, 0), (30, 8), (44, 4)], f), 0)
        antenna = [(30 * lean + spring(f, 46, -16 * (1 + 0.3 * i), decay=4), 0) for i in range(3)]
        feet = {side: ((0, 0.03 * track([(52, 0), (64, 1)], f) if side == 'R' else 0, 0), (0, 0, 0)) for side, s in SIDES}
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands, feet=feet,
               hand_rot={'L': (-40, 0, 10), 'R': (-24, -6, -10)}, claws={'L': track([(8, 20), (14, 2), (60, 2), (68, 20)], f), 'R': CLAW_REST_OPEN['R']},
               elbows={'L': 1})
    c.done()


def clip_brush_off(dl01, arm):
    """Out of a tub full of old post: a shake from the shoulders down, both claws brushing his chest
    and sides, a last tap on the window, and a nod."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 60
    c = Clip(arm, 'BrushOff', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        shake = 7 * math.sin(f * 1.9) * math.exp(-f / 7) if f < 18 else 0
        brushL = math.sin(math.pi * min(1, max(0, (f - 16) / 10))) * (1 if f < 40 else 0)
        brushR = math.sin(math.pi * min(1, max(0, (f - 24) / 10))) * (1 if f < 40 else 0)
        # The claws lie on his chest with the elbows out (a reach straight in runs through the pod) and
        # brush across the window and out to the sides, just off the glass.
        brush = {1: brushL, -1: brushR}
        sweep = {1: math.sin(f * 0.9), -1: math.sin(f * 0.9 + 1)}
        chest = {s: dl01.WINDOW_WRIST[s] + 0.012 * dl01.WINDOW_OUT[s] + Vector((-s * 0.02 * sweep[s], 0, 0.02 * sweep[s]))
                 for _, s in SIDES}
        hands = {s: dl01.window_reach(s, CARRY[s], brush[s], target=chest[s], arc=0.06) for _, s in SIDES}
        knock = track([(38, 0), (42, 1), (48, 1), (54, 0)], f)
        tap = max(0, math.sin(math.pi * (f - 42) / 5)) * (1 if 42 <= f <= 47 else 0)
        hands[-1] = dl01.window_reach(-1, hands[-1], knock, 0.75 * tap)
        right = max(brushR, knock)
        c.pose(frame, body=(0, 0, -0.006 * abs(shake) / 7), body_rot=(track([(0, 0), (20, 8), (40, 6), (52, -3), (60, 0)], f), shake, 0),
               head=(track([(0, 0), (20, 22), (40, 20), (50, -6), (55, 4), (60, 0)], f), -shake * 1.4, 0),
               antenna=[(14 * math.sin(f * 2.1 - i) * math.exp(-f / 9) + spring(f, 50, -12), 0) for i in range(3)],
               hands=hands, hand_rot={'L': dl01.window_claw(1, brushL, (-60, 0, 30)), 'R': dl01.window_claw(-1, right, (-60, 0, -30))},
               elbows={'L': brushL, 'R': right}, claws={'L': 8, 'R': 4})
    c.done()


def clip_startle(dl01, arm):
    """A bang nearby: a jolt, claws up, antenna stiff, head pulled in; then he settles and looks."""
    track, spring, Clip, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY
    frames = 30
    c = Clip(arm, 'Startle', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        jolt = track([(0, 0), (2, 1), (8, 1), (22, 0)], f, ease=lambda x: ease_back(x, 0.6))
        hands = {s: CARRY[s] + Vector((s * 0.05 * jolt, 0.02 * jolt, 0.12 * jolt)) for _, s in SIDES}
        c.pose(frame, body=(0, 0.02 * jolt, 0.025 * math.sin(math.pi * min(1, f / 6)) - 0.015 * jolt),
               body_rot=(-8 * jolt, 0, 0), head=(14 * jolt, track([(8, 0), (14, -10), (24, -6), (30, 0)], f), 0),
               antenna=[(-40 * jolt + spring(f, 8, 12), 0) for i in range(3)], hands=hands,
               claws={'L': 30 * jolt + CLAW_REST_OPEN['L'] * (1 - jolt), 'R': 28 * jolt})
    c.done()


def add_clips(dl01, arm):
    clip_attention(dl01, arm)
    clip_proud(dl01, arm)
    clip_peek_down(dl01, arm)
    clip_brush_off(dl01, arm)
    clip_startle(dl01, arm)
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
