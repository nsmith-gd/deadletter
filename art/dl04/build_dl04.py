"""DL-04 The Handbrake: Goods Lift 2 and its safety pawl, the returns belt, the residential access
tunnel and the refuge's central atrium, D-17's clips for the scene, and its lore signage. Called from
art/dl01/build_dl01.py (chapter 1 is one level).

DL-04 continues straight on from DL-03's gallery, at the gallery's height (1.6 m):
  - through the residential doorway into the goods hall, where Lift 2's platform sits at the bottom of
    its shaft; a load pan in the floor drives the head drum, and the goods trolley, still loaded with
    ballast, is heavy enough to bring the platform level with the landings;
  - the safety pawl that holds it there, patched by hand for fifty years, and Lift 1 beside it, failed;
  - the returns belt beyond the far landing, bringing crates of post down from the rings;
  - the residential access tunnel, with children's chalk on its floor and walls;
  - a balcony high in the refuge's atrium: three rings of homes around a void.

Coordinates as before: metres, Blender Z up, the lane at y = 0, travel along +x.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
import build_dl03 as dl03
from build_d17 import (add_box, add_cyl, add_sphere, add_torus, rounded_box, emission_material,
                       worn_material, simple_material, smoothstep, ease_back, SIDES, CLAW_REST_OPEN)

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')

# Shared with the game (game/undelivered/index.html keeps the same numbers).
DECK = 1.6                           # DL-04 runs at the DL-03 gallery's height
DOOR4_X = 47.5                       # the residential doorway in the gallery's end wall
HALL4_X0 = 48.6                      # the goods hall
T4_X, T4_HALF, T4_DECK, T4_TOP = 49.5, 0.36, 0.2, 0.44   # goods trolley: start, half-length, deck, ballast top
T4_HANDLE = 0.44                     # the push bar, as on the DL-02 trolley (the push clips are shared)
PAN = (50.5, 51.9)                   # the load pan in the floor
PAWL_X, LEVER_Y, LEVER_PIVOT_Z, LEVER_LEN = 52.45, 0.3, 0.2, 0.42
SHAFT = (52.8, 55.3)                 # Lift 2's shaft across the lane
RISE = 2.7                           # the platform's travel, bottom to landing
DRUM = (54.05, 0.7, DECK + 3.6, 0.45)        # head drum: x, y, z, radius (axle along y)
PULLEY = (51.2, 0.42, DECK + 3.6, 0.2)       # the pan chain's pulley, in line with the drum's hub
YOKE = (53.6, 54.5, 1.45)            # the platform's chain anchors: x, x, height above its deck
BELT = (57.7, 64.6)                  # the returns belt, flush with the floor
TURN_X = 58.2                        # where crates leave the belt for the hatch
TUNNEL = (64.6, 70.0)
HOP = (66.4, 68.2)                   # the chalk hopscotch
BALCONY = (70.0, 74.6)
ATRIUM = (77.3, 41.5, 40.0)          # centre x, y and radius of the refuge's atrium (the core stands off to the right)
RINGS = (('A', 8.0), ('B', -5.0), ('C', -18.0))   # walkway levels
ATRIUM_FLOOR, ATRIUM_TOP = -26.0, 26.0
ARC = (math.radians(-39), math.radians(219))      # the near side, toward the camera, is left open


def _obj(name, bm, mats, coll, sharp=35):
    return d17.mesh_object(name, bm, mats, coll, sharp=sharp)


_plane = dl03._plane
_font = dl03._font
_age = dl03._age


def _image_material(name, path, rough=0.7, alpha=False):
    mat, nt, bsdf = d17._new_material(name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    if alpha:
        nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
        for attr, value in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
            if hasattr(mat, attr):
                try:
                    setattr(mat, attr, value)
                except (TypeError, ValueError):
                    pass
    return mat


def _rz(a):
    return Matrix.Rotation(a, 4, 'Z')


# --------------------------------------------------------------------------
# Lore, painted, stamped and chalked
# --------------------------------------------------------------------------

def make_textures():
    from PIL import Image, ImageDraw, ImageFilter
    os.makedirs(TEX, exist_ok=True)
    ink, cream, yellow = (26, 24, 20), (222, 212, 184), (196, 168, 60)

    # Lift 2's sign: how the lift works, and the one rule, mostly in pictures.
    img = Image.new('RGB', (900, 640), yellow)
    d = ImageDraw.Draw(img)
    d.rectangle((14, 14, 886, 626), outline=ink, width=12)
    d.text((44, 34), 'GOODS LIFT 2', font=_font(70), fill=ink)
    # A trolley on the pan, an arrow, the platform raised level with the landing.
    d.rectangle((50, 300, 330, 318), fill=ink)                          # the pan
    for k in range(5):
        d.line((70 + k * 56, 330, 96 + k * 56, 352), fill=ink, width=8)
    d.rectangle((110, 228, 270, 262), fill=ink)                         # trolley deck and ballast
    d.rectangle((126, 190, 254, 226), fill=ink)
    d.line((96, 262, 80, 196), fill=ink, width=10)
    for x in (130, 250):
        d.ellipse((x - 16, 262, x + 16, 294), fill=ink)
    d.polygon([(360, 250), (430, 250), (430, 222), (482, 266), (430, 310), (430, 282), (360, 282)], fill=ink)
    d.rectangle((520, 160, 536, 330), fill=ink)                         # landing, gap, landing
    d.rectangle((520, 160, 600, 176), fill=ink)
    d.rectangle((790, 160, 806, 330), fill=ink)
    d.rectangle((730, 160, 806, 176), fill=ink)
    d.rectangle((604, 160, 726, 178), fill=(150, 36, 30))               # the platform, up
    d.polygon([(665, 196), (690, 236), (640, 236)], fill=ink)
    d.line((665, 236, 665, 300), fill=ink, width=10)
    # The rule.
    d.rectangle((44, 420, 856, 600), outline=ink, width=8)
    d.line((90, 580, 130, 450), fill=(150, 36, 30), width=14)           # a lever, pulled
    d.ellipse((116, 432, 148, 464), fill=(150, 36, 30))
    d.rectangle((70, 570, 170, 590), fill=ink)
    d.text((200, 452), 'SET PAWL', font=_font(60), fill=ink)
    d.text((200, 522), 'BEFORE BOARDING', font=_font(52), fill=ink)
    _age(img, 41, 0.6).save(os.path.join(TEX, 'lift2_sign.png'))

    # Lift 1's enamel plate.
    img = Image.new('RGB', (640, 240), cream)
    d = ImageDraw.Draw(img)
    d.rectangle((10, 10, 630, 230), outline=ink, width=10)
    d.text((34, 26), 'LIFT 1', font=_font(64), fill=ink)
    d.text((34, 112), 'OUT OF SERVICE  R.Y. 97', font=_font(36, 'mono-bold'), fill=(150, 36, 30))
    d.text((34, 166), 'USE LIFT 2', font=_font(34, 'mono'), fill=ink)
    _age(img, 42, 0.8).save(os.path.join(TEX, 'lift1_plate.png'))

    # Brass repair tags wired to the pawl: a refuge year and initials, stamped by hand.
    for k, (yr, who) in enumerate((('58', 'J.O.'), ('71', 'T.M.'), ('84', 'J.O.'), ('96', 'A.K.'), ('103', 'M.'), ('107', 'M.'))):
        img = Image.new('RGB', (200, 128), (150, 112, 52))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((4, 4, 196, 124), radius=18, outline=(92, 66, 28), width=6)
        d.ellipse((14, 52, 34, 72), fill=(40, 32, 20))
        d.text((44, 14), 'R.Y.' + yr, font=_font(40, 'mono-bold'), fill=(58, 40, 18))
        d.text((44, 66), who, font=_font(40, 'mono-bold'), fill=(58, 40, 18))
        rnd = random.Random(60 + k)
        for _ in range(30):
            x, y = rnd.uniform(0, 200), rnd.uniform(0, 128)
            d.point((x, y), fill=(90, 70, 40))
        img.filter(ImageFilter.GaussianBlur(0.6)).save(os.path.join(TEX, f'repair_tag{k}.png'))

    # The lift's dial: platform at the bottom (left) to level with the landing (right).
    s = 256
    img = Image.new('RGB', (s, s), (206, 198, 172))
    d = ImageDraw.Draw(img)
    d.rectangle((4, 4, s - 4, s - 4), outline=ink, width=8)
    c = s / 2

    def at(k, r):
        a = math.radians(-100 + 200 * k)
        return c + r * math.sin(a), c + 18 - r * math.cos(a)
    for k in range(40):
        x, y = at(0.96 + 0.04 * k / 39, 92)
        d.ellipse((x - 8, y - 8, x + 8, y + 8), fill=(60, 140, 70))
    for k in range(11):
        x0, y0 = at(k / 10, 100)
        x1, y1 = at(k / 10, 84 if k % 5 == 0 else 92)
        d.line((x0, y0, x1, y1), fill=ink, width=6 if k % 5 == 0 else 3)
    d.rectangle((22, 200, 66, 210), fill=ink)                     # platform low
    d.rectangle((190, 160, 234, 170), fill=ink)                   # platform at the landing
    d.line((190, 150, 234, 150), fill=ink, width=4)
    d.ellipse((c - 12, c + 6, c + 12, c + 30), fill=ink)
    img.filter(ImageFilter.GaussianBlur(0.6)).save(os.path.join(TEX, 'lift_dial.png'))

    # The belt warning: a figure hopping a crate on a moving belt.
    img = Image.new('RGB', (520, 640), yellow)
    d = ImageDraw.Draw(img)
    d.rectangle((12, 12, 508, 628), outline=ink, width=12)
    d.polygon([(260, 40), (470, 380), (50, 380)], outline=ink, width=14)
    d.rectangle((110, 312, 410, 330), fill=ink)                         # the belt
    for x in (140, 380):
        d.ellipse((x - 14, 316, x + 14, 344), fill=ink)
    d.rectangle((280, 262, 340, 310), fill=ink)                         # a crate
    d.ellipse((196, 160, 226, 190), fill=ink)                           # a figure, mid-hop
    d.line((211, 190, 220, 240), fill=ink, width=12)
    d.line((220, 240, 196, 266), fill=ink, width=10)
    d.line((220, 240, 250, 258), fill=ink, width=10)
    d.line((214, 204, 188, 222), fill=ink, width=8)
    d.line((214, 204, 244, 196), fill=ink, width=8)
    for k in range(3):
        d.polygon([(370 - k * 40, 356), (346 - k * 40, 366), (370 - k * 40, 376)], fill=ink)
    d.text((40, 410), 'RETURNS LINE', font=_font(58), fill=ink)
    d.text((40, 488), 'Line starts by itself.', font=_font(30, 'sans'), fill=ink)
    d.text((40, 532), 'Mind the crates.', font=_font(30, 'sans'), fill=ink)
    _age(img, 43, 0.6).save(os.path.join(TEX, 'belt_warning.png'))

    # Over the belt: where the crates are going.
    img = Image.new('RGB', (1400, 240), (34, 58, 44))
    d = ImageDraw.Draw(img)
    d.rectangle((10, 10, 1390, 230), outline=cream, width=10)
    d.polygon([(40, 120), (130, 50), (130, 90), (220, 90), (220, 150), (130, 150), (130, 190)], fill=cream)
    d.text((260, 44), 'RETURNS FROM THE RINGS', font=_font(64), fill=cream)
    d.text((262, 138), 'to Dead Letters  .  Do not ride the line', font=_font(40, 'sans'), fill=(190, 182, 150))
    _age(img, 44, 0.7).save(os.path.join(TEX, 'returns_sign.png'))

    # The tunnel's ring board, with tape across C.
    img = Image.new('RGB', (900, 300), cream)
    d = ImageDraw.Draw(img)
    d.rectangle((10, 10, 890, 290), outline=ink, width=10)
    d.text((40, 30), 'RESIDENTIAL RINGS', font=_font(56), fill=ink)
    for i, (ring, arrow) in enumerate((('A', 'up'), ('B', 'right'), ('C', 'down'))):
        x = 60 + i * 280
        d.rectangle((x, 120, x + 200, 270), outline=ink, width=8)
        d.text((x + 18, 132), ring, font=_font(110), fill=ink)
        ax, ay = x + 150, 196
        if arrow == 'up':
            d.polygon([(ax, ay - 50), (ax + 30, ay), (ax - 30, ay)], fill=ink)
            d.rectangle((ax - 10, ay, ax + 10, ay + 46), fill=ink)
        elif arrow == 'right':
            d.polygon([(ax + 40, ay), (ax, ay - 30), (ax, ay + 30)], fill=ink)
            d.rectangle((ax - 40, ay - 10, ax, ay + 10), fill=ink)
        else:
            d.polygon([(ax, ay + 50), (ax + 30, ay), (ax - 30, ay)], fill=ink)
            d.rectangle((ax - 10, ay - 46, ax + 10, ay), fill=ink)
    d.polygon([(600, 290), (636, 262), (880, 110), (846, 92)], fill=(150, 36, 30))
    d.polygon([(600, 110), (632, 92), (880, 262), (846, 290)], fill=(150, 36, 30))
    _age(img, 45, 0.5).save(os.path.join(TEX, 'rings_board.png'))

    # Glazed tunnel tiles, grimed, with a green band at a child's shoulder height.
    img = Image.new('RGB', (1024, 512), (176, 172, 150))
    d = ImageDraw.Draw(img)
    rnd = random.Random(46)
    for row in range(16):
        for col in range(16):
            x, y = col * 64 + (32 if row % 2 else 0), row * 32
            v = rnd.randint(-14, 10)
            d.rectangle((x + 2, y + 2, x + 62, y + 30), fill=(170 + v, 166 + v, 144 + v))
    d.rectangle((0, 300, 1024, 340), fill=(52, 92, 70))
    _age(img, 47, 1.4).save(os.path.join(TEX, 'tunnel_tiles.png'))

    # Chalk on the tunnel floor: hopscotch, one to eight, and HOME.
    w, h = 1080, 360
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    chalk = (236, 232, 220, 225)
    rnd = random.Random(48)

    def wobbly_rect(x0, y0, x1, y1, col):
        pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            for _ in range(2):
                d.line((ax + rnd.uniform(-3, 3), ay + rnd.uniform(-3, 3), bx + rnd.uniform(-3, 3), by + rnd.uniform(-3, 3)),
                       fill=col, width=7)
    cells = [(1, 'm'), (2, 'm'), (3, 'm'), (4, 't'), (5, 'b'), (6, 'm'), (7, 't'), (8, 'b')]
    x = 20
    i = 0
    while i < len(cells):
        n, pos = cells[i]
        if pos == 'm':
            wobbly_rect(x, 90, x + 120, 270, chalk)
            d.text((x + 36, 140), str(n), font=_font(80), fill=chalk)
            x += 120
            i += 1
        else:
            for (nn, pp) in cells[i:i + 2]:
                y0 = 20 if pp == 't' else 180
                wobbly_rect(x, y0, x + 120, y0 + 160, chalk)
                d.text((x + 36, y0 + 34), str(nn), font=_font(80), fill=chalk)
            x += 120
            i += 2
    d.arc((x - 40, 60, x + 160, 300), 270, 90, fill=chalk, width=8)
    d.text((x + 6, 150), 'HOME', font=_font(36), fill=(240, 180, 190, 225))
    d.ellipse((150, 300, 178, 324), fill=(240, 180, 190, 200))            # a stone, and a dropped stub
    d.line((620, 320, 660, 330), fill=(170, 210, 240, 230), width=12)
    img.filter(ImageFilter.GaussianBlur(1.1)).save(os.path.join(TEX, 'chalk_floor.png'))

    # Chalk on the tunnel wall, at a child's height: a big sun, houses, a family, a dog.
    w, h = 1600, 400
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    sun = (250, 214, 90, 230)
    d.ellipse((90, 40, 250, 200), outline=sun, width=10)
    for k in range(12):
        a = k * math.pi / 6
        d.line((170 + 100 * math.cos(a), 120 + 100 * math.sin(a), 170 + 150 * math.cos(a), 120 + 150 * math.sin(a)), fill=sun, width=9)
    d.arc((135, 100, 205, 160), 20, 160, fill=sun, width=7)
    d.ellipse((140, 90, 152, 102), fill=sun)
    d.ellipse((188, 90, 200, 102), fill=sun)
    white, pink, blue = (236, 232, 220, 220), (240, 170, 186, 220), (160, 206, 240, 220)
    for k, col in enumerate((white, blue, pink)):
        x0 = 420 + k * 230
        d.rectangle((x0, 220, x0 + 160, 360), outline=col, width=8)
        d.polygon([(x0 - 14, 224), (x0 + 80, 150), (x0 + 174, 224)], outline=col, width=8)
        d.rectangle((x0 + 60, 290, x0 + 100, 360), outline=col, width=7)
        d.rectangle((x0 + 18, 244, x0 + 50, 274), outline=col, width=6)
    for k, (x0, tall) in enumerate(((1170, 170), (1260, 110))):           # a grown-up and a child, holding hands
        top = 370 - tall
        d.ellipse((x0 - 18, top - 36, x0 + 18, top), outline=white, width=7)
        d.line((x0, top, x0, top + tall * 0.55), fill=white, width=7)
        d.line((x0, top + tall * 0.55, x0 - 22, 370), fill=white, width=7)
        d.line((x0, top + tall * 0.55, x0 + 22, 370), fill=white, width=7)
        d.line((x0 - 34, top + 30, x0 + 34, top + 30), fill=white, width=7)
    d.line((1204, 230, 1226, 282), fill=white, width=7)
    d.rectangle((1380, 300, 1470, 340), outline=blue, width=7)            # a dog
    d.ellipse((1460, 270, 1500, 310), outline=blue, width=7)
    for x0 in (1390, 1455):
        d.line((x0, 340, x0, 370), fill=blue, width=7)
    d.line((1380, 306, 1350, 280), fill=blue, width=7)
    img.filter(ImageFilter.GaussianBlur(1.0)).save(os.path.join(TEX, 'chalk_wall.png'))

    # Ring letters, painted metres high on the atrium wall; ring C taped and marked closed.
    for ring in 'ABC':
        img = Image.new('RGBA', (512, 512), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        d.text((96, -20), ring, font=_font(470), fill=(214, 204, 176, 235))
        if ring == 'C':
            d.polygon([(10, 470), (60, 500), (500, 60), (450, 30)], fill=(170, 40, 34, 240))
            d.polygon([(10, 60), (60, 30), (500, 470), (450, 500)], fill=(170, 40, 34, 240))
        img.filter(ImageFilter.GaussianBlur(1.2)).save(os.path.join(TEX, f'ring_{ring}.png'))


# --------------------------------------------------------------------------
# The set
# --------------------------------------------------------------------------

def dl04_materials(m):
    m['hallbulb'] = emission_material('HallBulb4', (1.0, 0.88, 0.7), 0.0)
    m['atlanding'] = emission_material('AtLanding', (1.0, 0.62, 0.18), 0.0)
    m['pawllamp'] = emission_material('PawlLamp', (1.0, 0.2, 0.1), 0.0)
    m['beacon'] = emission_material('BeaconLamp', (1.0, 0.55, 0.12), 0.0)
    m['tunnelbulb'] = emission_material('TunnelBulb', (0.95, 0.9, 0.78), 0.0)
    m['ringlamp'] = emission_material('RingLamp', (1.0, 0.78, 0.5), 0.0)
    m['ringred'] = emission_material('RingLampRed', (1.0, 0.18, 0.1), 0.0)
    m['homelight'] = emission_material('HomeLight', (1.0, 0.72, 0.4), 0.0)
    m['skypanel'] = emission_material('SkyPanel', (0.7, 0.8, 0.9), 0.0)
    m['tote'] = worn_material('ToteGreen', base=(0.08, 0.11, 0.09), dirt=(0.05, 0.05, 0.04),
                              chip=(0.16, 0.18, 0.15), rough=0.7, chip_rough=0.6, metallic=0.0)
    m['belt'] = d17._new_material('BeltRubber')[0]
    m['plaster'] = simple_material('AtriumPlaster', (0.3, 0.28, 0.22), 0.9)
    m['dark'] = simple_material('AtriumDark', (0.006, 0.006, 0.006), 0.8)
    m['stone'] = simple_material('AtriumStone', (0.05, 0.05, 0.048), 0.95)
    m['barricade'] = simple_material('Barricade', (0.4, 0.06, 0.04), 0.7)
    m['brass'] = simple_material('Brass', (0.45, 0.32, 0.12), 0.45, metallic=0.8)


def build_goods_hall(m, coll):
    """The goods hall behind the residential door: walls, landings, beams, lamps, and Lift 1 behind."""
    x1 = TUNNEL[0]
    bm = bmesh.new()
    # The landings: one solid floor slab, cut by Lift 2's shaft (the belt sits in it further on).
    add_box(bm, ((47.3 + SHAFT[0]) / 2, 0.1, DECK - 1.45), (SHAFT[0] - 47.3, 3.4, 2.9))
    add_box(bm, ((SHAFT[1] + BELT[0]) / 2, 0.1, DECK - 1.45), (BELT[0] - SHAFT[1], 3.4, 2.9))
    add_box(bm, ((BELT[0] + x1) / 2, 0.1, DECK - 1.46), (x1 - BELT[0], 3.4, 2.88))
    _obj('G4Floor', bm, [m['concrete']], coll)
    bm = bmesh.new()
    # Back wall, with the opening onto Lift 1, and the hall's end over the belt.
    add_box(bm, ((DOOR4_X + 49.2) / 2, 1.85, DECK + 2.8), (49.2 - DOOR4_X, 0.12, 5.6))
    add_box(bm, ((51.6 + x1) / 2, 1.85, DECK + 2.8), (x1 - 51.6, 0.12, 5.6))
    add_box(bm, (50.4, 1.85, DECK + 4.1), (2.4, 0.12, 3.0))
    add_box(bm, ((DOOR4_X + x1) / 2, 0.2, DECK + 5.7), (x1 - DOOR4_X, 3.6, 0.2))
    add_box(bm, ((BELT[0] + x1) / 2, 0.3, DECK + 3.5), (x1 - BELT[0], 3.2, 0.25))   # lower ceiling over the belt
    _obj('G4Walls', bm, [m['wall']], coll)
    bm = bmesh.new()
    for x in (49.0, 52.66, 55.44, 57.7, 61.2):
        add_box(bm, (x, 0.2, DECK + 5.45), (0.22, 3.4, 0.3))
        add_box(bm, (x, 1.72, DECK + 2.7), (0.22, 0.2, 5.4))
    _obj('G4Beams', bm, [m['steel']], coll)
    # The residential door's vestibule: a low ceiling, yellow jambs.
    bm = bmesh.new()
    add_box(bm, ((DOOR4_X + HALL4_X0) / 2, 0.2, DECK + 1.55), (HALL4_X0 - DOOR4_X, 1.6, 0.12))
    _obj('G4Vestibule', bm, [m['concrete']], coll)
    # Hall lamps: over the pan and over the far landing.
    bm, bulbs = bmesh.new(), bmesh.new()
    for x in (51.0, 56.5):
        add_cyl(bm, (x, -0.1, DECK + 5.6), (x, -0.1, DECK + 3.0), 0.005, seg=6)
        add_cyl(bm, (x, -0.1, DECK + 3.0), (x, -0.1, DECK + 2.86), 0.07, 0.15, seg=16)
        add_sphere(bulbs, (x, -0.1, DECK + 2.88), 0.04, seg=12)
    _obj('G4Lamps', bm, [m['steel']], coll)
    _obj('G4LampBulbs', bulbs, [m['hallbulb']], coll)
    # Parcels and a sack left by the door; a broom against the wall.
    rnd = random.Random(404)
    bm = bmesh.new()
    for x, y, sz in ((48.0, 0.62, (0.26, 0.2, 0.16)), (48.2, 0.66, (0.2, 0.18, 0.12)), (48.1, 0.64, (0.18, 0.16, 0.1))):
        add_box(bm, (x, y, DECK + sz[2] / 2 + (0.16 if x == 48.1 else 0)), sz, rot=_rz(rnd.uniform(-0.4, 0.4)))
    _obj('G4Parcels', bm, [m['paper']], coll)
    bm = bmesh.new()
    add_cyl(bm, (56.95, 1.66, DECK + 0.02), (57.12, 1.7, DECK + 1.2), 0.012, seg=6)
    add_box(bm, (56.95, 1.66, DECK + 0.06), (0.24, 0.05, 0.1), rot=Matrix.Rotation(0.14, 4, 'Y'))
    _obj('G4Broom', bm, [m['wood']], coll)

    # Lift 1, behind the back wall: a lattice gate jammed half open, the shaft, its platform wrecked at
    # the bottom, its chains hanging.
    bm = bmesh.new()
    for x in (49.25, 51.55):
        add_box(bm, (x, 1.9, DECK + 1.3), (0.1, 0.1, 2.6))
    add_box(bm, (50.4, 1.9, DECK + 2.62), (2.4, 0.12, 0.12))
    _obj('G4Lift1Frame', bm, [m['yellow']], coll)
    bm = bmesh.new()
    for k in range(9):                                   # the gate's lattice, bunched to one side
        x = 49.32 + k * 0.09
        add_box(bm, (x, 1.86, DECK + 1.15), (0.012, 0.015, 2.2))
        if k < 8:
            for z in (0.4, 1.1, 1.8):
                add_box(bm, (x + 0.045, 1.86, DECK + z), (0.12, 0.012, 0.012), rot=Matrix.Rotation(0.7 * (1 if k % 2 else -1), 4, 'Y'))
    add_box(bm, (50.4, 1.86, DECK + 0.02), (2.3, 0.04, 0.04))
    _obj('G4Lift1Gate', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_box(bm, (50.4, 4.35, DECK - 1.0), (2.6, 0.1, 9.0))
    for x in (49.1, 51.7):
        add_box(bm, (x, 3.1, DECK - 1.0), (0.1, 2.5, 9.0))
    add_box(bm, (50.4, 3.1, DECK - 3.0), (2.6, 2.5, 0.1))
    _obj('G4Lift1Shaft', bm, [m['wall']], coll)
    bm = bmesh.new()                                     # the fallen platform, tipped on its side
    tilt = Matrix.Rotation(math.radians(24), 4, 'Y') @ Matrix.Rotation(math.radians(-8), 4, 'X')
    add_box(bm, (50.4, 3.0, DECK - 0.75), (2.2, 1.7, 0.1), rot=tilt)
    for dx in (-0.9, 0.9):
        add_box(bm, (50.4 + dx * 0.92, 3.6, DECK - 0.55 - dx * 0.38), (0.06, 0.06, 0.9), rot=tilt)
    add_box(bm, (50.9, 3.0, DECK - 0.95), (0.45, 0.4, 0.3), rot=tilt @ _rz(0.4))
    _obj('G4Lift1Wreck', bm, [m['shutter']], coll)
    bm = bmesh.new()
    for x, low in ((49.6, DECK - 0.3), (51.2, DECK + 0.9)):
        add_cyl(bm, (x, 3.1, DECK + 4.4), (x + 0.05, 3.1, low), 0.012, seg=6)
    _obj('G4Lift1Chains', bm, [m['steel']], coll)
    plate = _image_material('Lift1PlateMat', os.path.join(TEX, 'lift1_plate.png'))
    _plane('G4Lift1Plate', (0.64, 0.24), (50.4, 1.78, DECK + 2.9), plate, coll)


def build_trolley(m, coll):
    """The goods trolley: a heavy flatbed with a push bar at its left end, loaded with ballast pigs
    strapped under a frame. Origin on the floor at its centre."""
    h, dk, top, hh = T4_HALF, T4_DECK, T4_TOP, T4_HANDLE
    bm = bmesh.new()
    add_box(bm, (0, 0, dk - 0.025), (2 * h, 0.42, 0.05))
    for x in (-h + 0.012, h - 0.012):
        add_box(bm, (x, 0, dk + 0.02), (0.024, 0.42, 0.04))
    for y in (-0.16, 0.16):
        add_cyl(bm, (-h + 0.01, y, dk), (-h - 0.02, y, hh), 0.012, seg=8)
    add_cyl(bm, (-h - 0.02, -0.18, hh), (-h - 0.02, 0.18, hh), 0.015, seg=10)
    for x in (-h + 0.07, h - 0.07):                       # wheel forks
        for y in (-0.15, 0.15):
            add_box(bm, (x, y, 0.11), (0.035, 0.035, 0.08))
    for x in (-0.3, 0.3):                                 # the cage over the load
        for y in (-0.19, 0.19):
            add_box(bm, (x, y, (dk + top) / 2 + 0.01), (0.025, 0.025, top - dk + 0.02))
    _obj('GoodsTrolley', bm, [m['depot_green']], coll).location = (T4_X, 0, DECK)
    bm = bmesh.new()
    add_cyl(bm, (-h - 0.02, -0.13, hh), (-h - 0.02, 0.13, hh), 0.018, seg=10)
    _obj('GoodsTrolleyGrip', bm, [m['rubber']], coll).location = (T4_X, 0, DECK)
    bm = bmesh.new()
    rnd = random.Random(414)
    for layer in range(3):
        for k in range(5):
            z = dk + 0.035 + layer * 0.07
            add_box(bm, (rnd.uniform(-0.03, 0.03), -0.15 + k * 0.075, z), (0.52, 0.065, 0.065),
                    rot=_rz(rnd.uniform(-0.04, 0.04)))
    _obj('GoodsBallast', bm, [m['iron']], coll).location = (T4_X, 0, DECK)
    bm = bmesh.new()
    for x in (-0.16, 0.16):
        add_box(bm, (x, 0, top + 0.005), (0.04, 0.42, 0.012))
        for y in (-0.205, 0.205):
            add_box(bm, (x, y, (dk + top) / 2), (0.04, 0.012, top - dk))
    _obj('GoodsStraps', bm, [m['yellow']], coll).location = (T4_X, 0, DECK)
    for i, (x, y) in enumerate(((-h + 0.07, -0.15), (-h + 0.07, 0.15), (h - 0.07, -0.15), (h - 0.07, 0.15))):
        bm = bmesh.new()
        add_cyl(bm, (0, -0.014, 0), (0, 0.014, 0), 0.055, seg=16)
        add_box(bm, (0.03, 0, 0), (0.022, 0.03, 0.012))
        _obj(f'GoodsWheel{i}', bm, [m['rubber']], coll).location = (T4_X + x, y, DECK + 0.055)


def build_lift(m, coll):
    """Lift 2: the load pan, the head frame with its drum and pulley, the shaft and the platform, the
    pawl with its lever, its hand-made reinforcement and repair tags, the dial and the lamps."""
    px0, px1 = PAN
    sx0, sx1 = SHAFT
    # The load pan: a treaded steel plate with an origin at its top centre, so the game can press it.
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.016), (px1 - px0 - 0.03, 0.7, 0.032))
    for k in range(18):
        add_box(bm, (-(px1 - px0) / 2 + 0.06 + k * 0.074, 0, 0.001), (0.012, 0.64, 0.002),
                rot=_rz(0.5 if k % 2 else -0.5))
    _obj('GoodsPan', bm, [m['plate']], coll).location = ((px0 + px1) / 2, 0, DECK + 0.004)
    bm = bmesh.new()
    for x in (px0 - 0.012, px1 + 0.012):
        add_box(bm, (x, 0, DECK + 0.002), (0.05, 0.78, 0.004))
    for y in (-0.38, 0.38):
        add_box(bm, ((px0 + px1) / 2, y, DECK + 0.002), (px1 - px0 + 0.07, 0.05, 0.004))
    _obj('G4PanBorder', bm, [m['yellow']], coll)
    bm = bmesh.new()                                      # buffer stops at the pan's far end
    for y in (-0.3, 0.3):
        add_cyl(bm, (px1 + 0.06, y, DECK), (px1 + 0.06, y, DECK + 0.1), 0.04, seg=12)
    _obj('G4PanStops', bm, [m['red']], coll)
    bm = bmesh.new()
    for y in (-0.3, 0.3):
        add_cyl(bm, (px1 + 0.06, y, DECK + 0.1), (px1 + 0.06, y, DECK + 0.13), 0.042, seg=12)
    _obj('G4PanStopCaps', bm, [m['rubber']], coll)

    # The head frame over the shaft, the drum and the pan pulley.
    bx = DRUM[0]
    bm = bmesh.new()
    for x in (sx0 - 0.14, sx1 + 0.14):
        add_box(bm, (x, 0.95, DECK + 2.1), (0.16, 0.16, 4.2))
    add_box(bm, ((sx0 + sx1) / 2, 0.95, DECK + 4.25), (sx1 - sx0 + 0.5, 0.18, 0.2))
    add_box(bm, ((PULLEY[0] - 0.3 + sx0) / 2, 0.95, DECK + 4.15), (sx0 - PULLEY[0] + 0.4, 0.14, 0.14))
    add_box(bm, (bx, 0.95, DECK + 3.9), (0.12, 0.08, 0.7))
    add_box(bm, (PULLEY[0], 0.95, DECK + 3.88), (0.08, 0.06, 0.6))
    add_box(bm, (PULLEY[0], 0.68, DECK + 3.6), (0.05, 0.55, 0.05))
    _obj('G4HeadFrame', bm, [m['yellow']], coll)
    bm = bmesh.new()
    r = DRUM[3]
    add_cyl(bm, (0, -0.16, 0), (0, 0.16, 0), r, seg=40)
    for y in (-0.17, 0.17):
        add_cyl(bm, (0, y - 0.01, 0), (0, y + 0.01, 0), r + 0.05, seg=40)
    add_cyl(bm, (0, -0.36, 0), (0, 0.26, 0), 0.05, seg=12)
    for k in range(6):                                     # spokes on the face, so it reads turning
        a = k * math.pi / 3
        add_box(bm, (math.cos(a) * r * 0.5, -0.19, math.sin(a) * r * 0.5), (r * 0.9, 0.025, 0.05), rot=Matrix.Rotation(-a, 4, 'Y'))
    add_cyl(bm, (0, -0.34, 0), (0, -0.22, 0), 0.2, seg=24)  # the hub the pan chain wraps, toward the camera
    _obj('HeadDrum', bm, [m['iron']], coll).location = DRUM[:3]
    bm = bmesh.new()
    add_cyl(bm, (0, -0.04, 0), (0, 0.04, 0), PULLEY[3], seg=24)
    for k in range(4):
        a = k * math.pi / 2
        add_box(bm, (math.cos(a) * 0.1, -0.05, math.sin(a) * 0.1), (0.16, 0.012, 0.03), rot=Matrix.Rotation(-a, 4, 'Y'))
    _obj('PanPulley', bm, [m['iron']], coll).location = PULLEY[:3]

    # The shaft: walls below the landings, its back wall, a little debris at the bottom.
    floor_z = DECK - RISE - 0.12
    bm = bmesh.new()
    add_box(bm, ((sx0 + sx1) / 2, 1.0, (floor_z + DECK + 4.2) / 2), (sx1 - sx0, 0.1, DECK + 4.2 - floor_z))
    add_box(bm, ((sx0 + sx1) / 2, 0.1, floor_z - 0.05), (sx1 - sx0, 2.0, 0.1))
    _obj('G4Shaft', bm, [m['wall']], coll)
    bm = bmesh.new()
    for x in (sx0, sx1):
        add_box(bm, (x + (-0.02 if x == sx0 else 0.02), 0.1, (floor_z + DECK) / 2), (0.04, 2.0, DECK - floor_z))
    _obj('G4ShaftFaces', bm, [m['concrete']], coll)
    bm = bmesh.new()
    rnd = random.Random(420)
    for k in range(7):
        add_box(bm, (sx0 + 0.3 + rnd.uniform(0, 1.8), rnd.uniform(-0.6, 0.7), floor_z + 0.04), (0.18, 0.13, 0.08),
                rot=_rz(rnd.uniform(0, 3)))
    _obj('G4ShaftDebris', bm, [m['paper']], coll)
    # The rack on the near wall: teeth the pawl rides over.
    bm = bmesh.new()
    add_box(bm, (sx0 + 0.03, 0.5, (floor_z + DECK) / 2), (0.04, 0.08, DECK - floor_z - 0.1))
    z = floor_z + 0.1
    while z < DECK - 0.12:
        add_box(bm, (sx0 + 0.06, 0.5, z), (0.03, 0.08, 0.025), rot=Matrix.Rotation(0.5, 4, 'Y'))
        z += 0.08
    _obj('G4Rack', bm, [m['steel']], coll)

    # The platform: deck, underframe, the back rail, the yoke the chains hang from, and the bracket the
    # pawl's dog drops into. Origin at its deck top centre, at the landing; the game lowers it.
    cx = (sx0 + sx1) / 2
    bm = bmesh.new()
    add_box(bm, (0, 0, -0.04), (sx1 - sx0 - 0.04, 1.5, 0.08))
    for k in range(int((sx1 - sx0) / 0.1)):
        add_box(bm, (-(sx1 - sx0) / 2 + 0.06 + k * 0.1, 0, 0.001), (0.014, 1.4, 0.002))
    _obj('GoodsPlatform', bm, [m['plate']], coll).location = (cx, 0, DECK)
    bm = bmesh.new()
    for y in (-0.6, 0.0, 0.6):
        add_box(bm, (0, y, -0.14), (sx1 - sx0 - 0.08, 0.08, 0.12))
    for x in (YOKE[0] - cx, YOKE[1] - cx):
        add_box(bm, (x, 0.72, YOKE[2] / 2), (0.07, 0.07, YOKE[2]))
    add_box(bm, ((YOKE[0] + YOKE[1]) / 2 - cx, 0.72, YOKE[2]), (YOKE[1] - YOKE[0] + 0.1, 0.08, 0.08))
    add_box(bm, (sx0 + 0.12 - cx, 0.5, 0.1), (0.05, 0.05, 0.2))           # the dog's bracket on its post
    add_box(bm, (sx0 + 0.12 - cx, 0.5, 0.2), (0.14, 0.12, 0.03))
    _obj('GoodsPlatformFrame', bm, [m['steel']], coll).location = (cx, 0, DECK)
    bm = bmesh.new()
    for x in (sx0 + 0.06 - cx, (YOKE[0] + YOKE[1]) / 2 - cx, sx1 - 0.06 - cx):
        add_box(bm, (x, 0.74, 0.5), (0.04, 0.04, 1.0))
    for z in (0.5, 0.98):
        add_box(bm, (0, 0.74, z), (sx1 - sx0 - 0.1, 0.04, 0.04))
    _obj('GoodsPlatformRail', bm, [m['yellow']], coll).location = (cx, 0, DECK)

    # The pawl: a steel dog hinged at the shaft's edge (origin at its pin, lying along +x when set; the
    # game swings it up out of the way), in a housing patched by hand for fifty years.
    pin = (sx0 - 0.08, 0.5, DECK + 0.24)
    bm = bmesh.new()
    add_cyl(bm, (0, -0.05, 0), (0, 0.05, 0), 0.022, seg=12)
    add_box(bm, (0.12, 0, 0), (0.22, 0.06, 0.035))
    add_box(bm, (0.22, 0, -0.03), (0.035, 0.06, 0.06))
    _obj('Pawl', bm, [m['iron']], coll).location = pin
    bm = bmesh.new()
    add_box(bm, (pin[0] - 0.08, 0.5, DECK + 0.14), (0.22, 0.2, 0.28))
    add_box(bm, (pin[0] - 0.08, 0.5, DECK + 0.02), (0.28, 0.26, 0.04))
    add_box(bm, (pin[0] - 0.01, 0.5, pin[2]), (0.08, 0.14, 0.06))
    _obj('G4PawlHousing', bm, [m['iron']], coll)
    bm = bmesh.new()                                      # welded plates, a strap clamp, extra bolts
    add_box(bm, (pin[0] - 0.1, 0.395, DECK + 0.16), (0.2, 0.012, 0.15), rot=Matrix.Rotation(0.06, 4, 'Y'))
    add_box(bm, (pin[0] - 0.15, 0.393, DECK + 0.22), (0.08, 0.01, 0.06))
    for k, (dx, dz) in enumerate(((-0.17, 0.22), (-0.17, 0.1), (-0.02, 0.1), (-0.02, 0.22), (-0.1, 0.06), (-0.13, 0.26))):
        add_cyl(bm, (pin[0] + dx, 0.4, DECK + dz), (pin[0] + dx, 0.38, DECK + dz), 0.009, seg=6)
    add_box(bm, (pin[0] - 0.08, 0.5, DECK + 0.05), (0.25, 0.25, 0.025))
    add_box(bm, (pin[0] - 0.08, 0.5, DECK + 0.25), (0.25, 0.25, 0.022))
    _obj('G4PawlPatches', bm, [m['steel']], coll)
    bm = bmesh.new()
    pts = d17.helix((0, 0, 0), 0.016, 0.16, 7, n=70)        # a spare spring, wired on beside the original
    for a, b in zip(pts, pts[1:]):
        add_cyl(bm, (pin[0] - 0.24 + a.x, 0.42 + a.y, DECK + 0.26 + a.z), (pin[0] - 0.24 + b.x, 0.42 + b.y, DECK + 0.26 + b.z), 0.0035, seg=4)
    for z in (DECK + 0.22, DECK + 0.12):
        add_torus(bm, (pin[0] - 0.24, 0.42, z), (0, 0, 1), 0.026, 0.002, seg=12, rseg=3)
    _obj('G4PawlSpring', bm, [m['copper']], coll)
    # Six repair tags wired to the housing's front, left to right in order of their years.
    for k in range(6):
        mat = _image_material(f'RepairTag{k}', os.path.join(TEX, f'repair_tag{k}.png'), rough=0.4)
        x = pin[0] - 0.36 + k * 0.064
        z = DECK + 0.06 - (k % 2) * 0.025
        _plane(f'G4RepairTag{k}', (0.058, 0.037), (x, 0.385, z), mat, coll,
               rot=_rz(random.Random(k).uniform(-0.18, 0.18)) @ Matrix.Rotation(math.radians(90), 4, 'X'))
        bm = bmesh.new()
        add_cyl(bm, (x - 0.02, 0.39, z + 0.018), (x - 0.02, 0.39, DECK + 0.12), 0.0015, seg=4)
        _obj(f'G4TagWire{k}', bm, [m['copper']], coll)
    # The lever on its stand, and the rod to the pawl.
    bm = bmesh.new()
    add_box(bm, (PAWL_X, LEVER_Y, DECK + 0.1), (0.16, 0.2, 0.2))
    add_box(bm, (PAWL_X + 0.09, LEVER_Y, DECK + 0.3), (0.02, 0.12, 0.6))
    add_box(bm, (PAWL_X + 0.09, LEVER_Y, DECK + 0.62), (0.08, 0.1, 0.07))
    _obj('PawlLeverStand', bm, [m['depot_green']], coll)
    bm = bmesh.new()
    add_cyl(bm, (0, 0, 0), (0, 0, LEVER_LEN), 0.014, seg=8)
    add_cyl(bm, (-0.07, 0, LEVER_LEN), (0.07, 0, LEVER_LEN), 0.02, seg=10)
    _obj('PawlLever', bm, [m['red']], coll).location = (PAWL_X, LEVER_Y, DECK + LEVER_PIVOT_Z)
    bm = bmesh.new()
    add_cyl(bm, (PAWL_X + 0.1, 0.36, DECK + 0.5), (pin[0] - 0.12, 0.42, DECK + 0.3), 0.01, seg=6)
    _obj('G4PawlRod', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_sphere(bm, (PAWL_X + 0.09, LEVER_Y - 0.055, DECK + 0.64), 0.022, seg=10)
    _obj('PawlLamp', bm, [m['pawllamp']], coll)
    bm = bmesh.new()
    add_sphere(bm, (PAWL_X + 0.09, LEVER_Y - 0.055, DECK + 0.56), 0.02, seg=10)
    _obj('AtLandingLamp', bm, [m['atlanding']], coll)

    # The dial on the head frame's near post, facing the camera.
    gx, gz = sx0 - 0.14, DECK + 1.45
    bm = bmesh.new()
    add_box(bm, (gx, 0.84, gz), (0.24, 0.06, 0.24))
    _obj('G4DialBox', bm, [m['steel']], coll)
    _plane('G4DialFace', (0.2, 0.2), (gx, 0.808, gz), _image_material('LiftDialMat', os.path.join(TEX, 'lift_dial.png')), coll)
    bm = bmesh.new()
    add_box(bm, (0, 0, 0.035), (0.007, 0.004, 0.075))
    add_cyl(bm, (0, -0.003, 0), (0, 0.003, 0), 0.009, seg=10)
    _obj('LiftNeedle', bm, [m['red']], coll).location = (gx, 0.802, gz - 0.02)

    # The sign over the pan.
    sign = _image_material('Lift2SignMat', os.path.join(TEX, 'lift2_sign.png'))
    _plane('G4Lift2Sign', (0.9, 0.64), (51.2, 1.78, DECK + 2.45), sign, coll)


def build_belt(m, coll):
    """The far landing and the returns belt: frame, rollers, the belt surface (the game scrolls it), the
    chute from the rings, the hatch the crates leave by, the beacon and the signs; the crate templates."""
    bx0, bx1 = BELT
    _plane('ReturnsBelt', (bx1 - bx0, 1.0), ((bx0 + bx1) / 2, 0, DECK + 0.004), m['belt'], coll,
           rot=Matrix.Identity(4), uv_repeat=((bx1 - bx0) * 2, 1))
    bm = bmesh.new()
    for y in (-0.53, 0.53):
        add_box(bm, ((bx0 + bx1) / 2, y, DECK + 0.01), (bx1 - bx0 + 0.1, 0.05, 0.06))
    for x in (bx0, bx1):
        add_cyl(bm, (x, -0.5, DECK - 0.06), (x, 0.5, DECK - 0.06), 0.065, seg=16)
    _obj('G4BeltFrame', bm, [m['steel']], coll)
    bm = bmesh.new()
    x = bx0 + 0.3
    while x < bx1 - 0.2:
        add_cyl(bm, (x, -0.56, DECK - 0.03), (x, -0.5, DECK - 0.03), 0.028, seg=10)   # roller ends, seen in the frame's slot
        x += 0.42
    _obj('G4BeltRollers', bm, [m['iron']], coll)
    # The chute from the rings, down onto the belt's far end, and the hatch above it.
    bm = bmesh.new()
    a, b = Vector((64.3, 1.75, DECK + 1.35)), Vector((64.25, 0.35, DECK + 0.2))
    n = 8
    for k in range(n):
        p = a.lerp(b, (k + 0.5) / n)
        add_box(bm, (p.x, p.y, p.z), (0.56, (a - b).length / n + 0.02, 0.03), rot=Matrix.Rotation(math.atan2(a.z - b.z, a.y - b.y), 4, 'X'))
        for dx in (-0.29, 0.29):
            add_box(bm, (p.x + dx, p.y, p.z + 0.08), (0.03, (a - b).length / n + 0.02, 0.18), rot=Matrix.Rotation(math.atan2(a.z - b.z, a.y - b.y), 4, 'X'))
    _obj('G4Chute', bm, [m['shutter']], coll)
    bm = bmesh.new()
    add_box(bm, (64.3, 1.82, DECK + 1.6), (0.8, 0.08, 0.06))
    add_box(bm, (64.3, 1.82, DECK + 1.0), (0.8, 0.08, 0.06))
    _obj('G4ChuteHatch', bm, [m['yellow']], coll)
    # Where crates leave the belt: a hatch in the back wall with rubber flaps.
    bm = bmesh.new()
    for x in (bx0 + 0.05, TURN_X + 0.45):
        add_box(bm, (x, 1.78, DECK + 0.3), (0.06, 0.1, 0.6))
    add_box(bm, ((bx0 + TURN_X + 0.5) / 2, 1.78, DECK + 0.62), (TURN_X + 0.5 - bx0, 0.1, 0.06))
    _obj('G4TurnHatch', bm, [m['yellow']], coll)
    bm = bmesh.new()
    for k in range(7):
        add_box(bm, (bx0 + 0.12 + k * 0.1, 1.76, DECK + 0.3), (0.085, 0.008, 0.56))
    _obj('G4TurnFlaps', bm, [m['rubber']], coll)
    bm = bmesh.new()
    for x in range(int((TURN_X + 0.4 - bx0) / 0.09)):
        add_cyl(bm, (bx0 + 0.05 + x * 0.09, 0.62, DECK + 0.02), (bx0 + 0.05 + x * 0.09, 1.7, DECK + 0.02), 0.02, seg=8)
    _obj('G4TurnRollers', bm, [m['steel']], coll)
    # The beacon on its post, and the signs.
    bm = bmesh.new()
    add_cyl(bm, (57.35, 0.9, DECK), (57.35, 0.9, DECK + 2.0), 0.03, seg=8)
    add_cyl(bm, (57.35, 0.9, DECK + 2.0), (57.35, 0.9, DECK + 2.04), 0.08, seg=16)
    _obj('G4BeaconPost', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_sphere(bm, (57.35, 0.9, DECK + 2.1), 0.07, seg=14, scale=(1, 1, 0.9))
    _obj('BeaconLamp', bm, [m['beacon']], coll)
    _plane('G4BeltWarning', (0.42, 0.52), (57.0, 1.78, DECK + 1.25), _image_material('BeltWarningMat', os.path.join(TEX, 'belt_warning.png')), coll)
    _plane('G4ReturnsSign', (2.1, 0.36), (61.2, 1.78, DECK + 2.4), _image_material('ReturnsSignMat', os.path.join(TEX, 'returns_sign.png')), coll)

    # Crate templates, parked out of sight: a low tote, a deeper one, and two stacked. Origin at the base.
    sizes = [(0.36, 0.4, 0.18), (0.42, 0.4, 0.24), (0.4, 0.4, 0.42)]
    for i, (lx, ly, lz) in enumerate(sizes):
        bm = bmesh.new()
        layers = [(0, lz)] if i < 2 else [(0, lz / 2), (lz / 2, lz / 2)]
        for z0, hz in layers:
            add_box(bm, (0, 0, z0 + 0.01), (lx, ly, 0.02), mat=0)
            for y in (-ly / 2, ly / 2):
                add_box(bm, (0, y, z0 + hz / 2), (lx, 0.016, hz), mat=0)
            for x in (-lx / 2, lx / 2):
                add_box(bm, (x, 0, z0 + hz / 2), (0.016, ly, hz), mat=0)
            add_box(bm, (0, -ly / 2 - 0.004, z0 + hz * 0.72), (lx * 0.3, 0.004, hz * 0.18), mat=2)
        rnd = random.Random(430 + i)
        top = layers[-1][0]
        for k in range(3):
            add_box(bm, (rnd.uniform(-0.08, 0.08), rnd.uniform(-0.1, 0.1), top + lz * (0.45 if i < 2 else 0.22) + k * 0.02),
                    (0.2, 0.012, 0.13), mat=1, rot=Matrix.Rotation(rnd.uniform(-0.4, 0.4), 4, 'Y') @ _rz(rnd.uniform(-0.3, 0.3)))
        ob = _obj(f'ReturnCrate{i}', bm, [m['tote'], m['letters'], m['rubber']], coll)
        ob.location = (60.0 + i, -8.0, -6.0)


def build_tunnel(m, coll):
    """The residential access tunnel: a portal, arched ribs, a tiled back wall, lamps, the ring board,
    and children's chalk on the floor and the wall."""
    t0, t1 = TUNNEL
    bm = bmesh.new()
    add_box(bm, ((t0 + t1) / 2, 1.42, DECK + 1.2), (t1 - t0, 0.1, 2.4))
    _obj('G4TunnelBack', bm, [m['wall']], coll)
    _plane('G4TunnelTiles', (t1 - t0, 1.9), ((t0 + t1) / 2, 1.36, DECK + 0.95),
           _image_material('TunnelTilesMat', os.path.join(TEX, 'tunnel_tiles.png'), rough=0.35), coll, uv_repeat=((t1 - t0) / 2.0, 1))
    # The arch: ribs from the back wall up and over to the front, cut away toward the camera.
    bm = bmesh.new()
    x = t0 + 0.05
    while x <= t1 + 1e-6:
        prev = None
        for k in range(9):
            a = math.pi * 0.5 * k / 8
            p = Vector((x, 1.36 - 2.2 * (1 - math.cos(a)), DECK + 1.45 + 0.85 * math.sin(a)))
            if prev is not None:
                add_cyl(bm, prev, p, 0.05, seg=6)
            prev = p
        add_box(bm, (x, 1.33, DECK + 0.72), (0.1, 0.08, 1.44))
        x += 1.35
    add_box(bm, ((t0 + t1) / 2, -0.2, DECK + 2.32), (t1 - t0, 1.4, 0.08))
    _obj('G4TunnelRibs', bm, [m['steel']], coll)
    bm = bmesh.new()                                      # the portal, chevroned (its near post is cut away)
    add_box(bm, (t0, 1.3, DECK + 1.25), (0.25, 0.22, 2.5))
    add_box(bm, (t0, 0.2, DECK + 2.48), (0.25, 2.4, 0.22))
    _obj('G4Portal', bm, [m['yellow']], coll)
    bm, bulbs = bmesh.new(), bmesh.new()
    for x in (66.0, 68.9):
        add_box(bm, (x, 1.3, DECK + 1.95), (0.22, 0.1, 0.14))
        add_sphere(bulbs, (x, 1.24, DECK + 1.95), 0.045, seg=12, scale=(1.4, 0.6, 1))
    _obj('G4TunnelLamps', bm, [m['steel']], coll)
    _obj('G4TunnelBulbs', bulbs, [m['tunnelbulb']], coll)
    _plane('G4RingsBoard', (0.9, 0.3), (65.3, 1.33, DECK + 1.65), _image_material('RingsBoardMat', os.path.join(TEX, 'rings_board.png')), coll)
    chalk = _image_material('ChalkFloorMat', os.path.join(TEX, 'chalk_floor.png'), rough=0.9, alpha=True)
    _plane('ChalkFloor', (HOP[1] - HOP[0], 0.6), ((HOP[0] + HOP[1]) / 2, 0.02, DECK + 0.004), chalk, coll, rot=Matrix.Identity(4))
    chalk = _image_material('ChalkWallMat', os.path.join(TEX, 'chalk_wall.png'), rough=0.9, alpha=True)
    _plane('ChalkWall', (3.6, 0.9), (67.5, 1.34, DECK + 0.48), chalk, coll)


def _annulus(bm, cx, cy, r0, r1, z0, z1, a0, a1, seg, mat=0):
    """A ring segment between radii r0 and r1, heights z0 and z1, angles a0 to a1 (closed with caps)."""
    rings = []
    for k in range(seg + 1):
        a = a0 + (a1 - a0) * k / seg
        c, s = math.cos(a), math.sin(a)
        rings.append([bm.verts.new((cx + r * c, cy + r * s, z)) for r, z in ((r0, z0), (r1, z0), (r1, z1), (r0, z1))])
    for k in range(seg):
        a, b = rings[k], rings[k + 1]
        for i in range(4):
            bm.faces.new((a[i], b[i], b[(i + 1) % 4], a[(i + 1) % 4])).material_index = mat
    bm.faces.new(rings[0][::-1]).material_index = mat
    bm.faces.new(rings[-1]).material_index = mat


def _quad(bm, center, size, rot, mat=0):
    """One face, facing the rotated -y (the atrium's modules face the void this way): far detail is flat."""
    w, h = size[0] / 2, size[1] / 2
    m = Matrix.Translation(center) @ rot
    vs = [bm.verts.new(m @ Vector(p)) for p in ((-w, 0, -h), (w, 0, -h), (w, 0, h), (-w, 0, h))]
    bm.faces.new(vs).material_index = mat


def build_atrium(m, coll):
    """The balcony and stair, and the refuge's atrium: three rings of homes on two floors each around a
    void, their walkways and railings, bridges to the central core, the dead sky array overhead, ring C
    barricaded. Everything faces the void; the near side, toward the camera, is left open."""
    b0, b1 = BALCONY
    bm = bmesh.new()
    add_box(bm, ((b0 + b1) / 2, 0.7, DECK - 0.15), (b1 - b0, 3.4, 0.3))
    add_box(bm, ((b0 + b1) / 2, 0.7, DECK - 1.0), (b1 - b0 - 0.4, 2.6, 1.4))
    for k in range(9):                                    # the stair down toward ring B
        add_box(bm, (b1 + 0.15 + k * 0.24, 0.3, DECK - 0.1 - k * 0.2), (0.26, 1.1, 0.2))
    _obj('G4Balcony', bm, [m['concrete']], coll)
    bm = bmesh.new()
    x = b0
    while x <= b1 + 1e-6:
        add_box(bm, (x, 2.36, DECK + 0.5), (0.04, 0.04, 1.0))
        x += 0.5
    for z in (DECK + 0.5, DECK + 0.98):
        add_box(bm, ((b0 + b1) / 2, 2.36, z), (b1 - b0, 0.04, 0.04))
    add_box(bm, (b0, 1.85, DECK + 0.98), (0.04, 1.0, 0.04))
    for k in range(10):
        add_box(bm, (b1 + 0.15 + k * 0.24, 0.86, DECK + 0.85 - k * 0.2), (0.04, 0.04, 1.0))
    _obj('G4BalconyRail', bm, [m['yellow']], coll)
    bm = bmesh.new()                                      # the tunnel's end pillar
    add_box(bm, (b0 - 0.1, 1.45, DECK + 1.6), (0.3, 0.3, 3.2))
    _obj('G4BalconyWalls', bm, [m['wall']], coll)

    cx, cy, R = ATRIUM
    a0, a1 = ARC
    rnd = random.Random(470)
    # The atrium wall, floor and roof.
    bm = bmesh.new()
    _annulus(bm, cx, cy, R + 0.2, R + 1.0, ATRIUM_FLOOR, ATRIUM_TOP, a0, a1, 72)
    _obj('AtriumWall', bm, [m['stone']], coll)
    bm = bmesh.new()
    _annulus(bm, cx, cy, 0.0, R + 1.0, ATRIUM_FLOOR - 0.5, ATRIUM_FLOOR, 0, 2 * math.pi, 48)
    _annulus(bm, cx, cy, 0.0, R + 1.0, ATRIUM_TOP, ATRIUM_TOP + 0.6, 0, 2 * math.pi, 48)
    _obj('AtriumFloorRoof', bm, [m['stone']], coll)
    # The sky array under the roof: panels that once made a day; a few still faintly lit.
    panels, dead = bmesh.new(), bmesh.new()
    for i in range(-9, 10):
        for j in range(-9, 10):
            px, py = cx + i * 3.6, cy + j * 3.6
            if math.hypot(px - cx, py - cy) > R - 8:
                continue
            if rnd.random() < 0.3:                       # the rest are dead, dark against the dark roof
                add_box(panels, (px, py, ATRIUM_TOP - 0.15), (3.0, 3.0, 0.08))
    _obj('AtriumSkyPanels', panels, [m['skypanel']], coll)
    dead.free()

    facade, openings, trim, planters, lamps, red = (bmesh.new() for _ in range(6))
    step = 4.2 / R
    lit = None
    zr = 0.0
    for ring, zr in RINGS:
        # Walkway slab, fascia band, railing, and the homes on two floors at the wall.
        _annulus(trim, cx, cy, R - 5.0, R + 0.2, zr - 0.5, zr, a0, a1, 64)
        _annulus(trim, cx, cy, R - 5.05, R - 4.95, zr + 0.95, zr + 1.0, a0, a1, 64)
        n_posts = int((a1 - a0) / math.radians(5))
        for k in range(n_posts + 1):
            a = a0 + (a1 - a0) * k / n_posts
            p = (cx + (R - 5.0) * math.cos(a), cy + (R - 5.0) * math.sin(a))
            add_box(trim, (p[0], p[1], zr + 0.5), (0.06, 0.06, 1.0))
            if k % 3 == 0:
                bulb = (p[0] + 0.15 * math.cos(a), p[1] + 0.15 * math.sin(a), zr + 1.1)
                if ring != 'C':
                    add_box(lamps, bulb, (0.16, 0.16, 0.16))
                elif k % 12 == 0:
                    add_box(red, bulb, (0.16, 0.16, 0.16))
        a = a0 + step / 2
        idx = 0
        while a < a1 - step / 2:
            rot = _rz(a + math.pi / 2)
            out = Vector((math.cos(a), math.sin(a), 0))
            inward = -out

            def at(u, depth, z):
                t = Vector((-math.sin(a), math.cos(a), 0))
                return Vector((cx, cy, 0)) + out * R + t * u + inward * depth + Vector((0, 0, z))
            _quad(facade, at(0, 0.2, zr + 2.8), (4.0, 5.6), rot)
            add_box(trim, at(-2.0, 0.17, zr + 2.8), (0.24, 0.34, 5.6), rot=rot)
            add_box(trim, at(0, 0.24, zr + 2.78), (4.0, 0.12, 0.1), rot=rot)
            door = rnd.choice((-1.1, 1.1))
            _quad(openings, at(door, 0.21, zr + 1.0), (0.9, 2.0), rot)
            _quad(openings, at(-door * 0.75, 0.21, zr + 1.45), (1.2, 1.0), rot)
            for wx in (-0.95, 0.95):
                if rnd.random() < 0.25:
                    continue                                 # shutters closed: plaster shows
                _quad(openings, at(wx, 0.21, zr + 4.15), (0.95, 0.95), rot)
                if rnd.random() < 0.4:
                    add_box(planters, at(wx, 0.3, zr + 3.72), (0.9, 0.14, 0.14), rot=rot)
            # One window lit, high on ring A, across the void.
            if ring == 'A' and lit is None and a > math.radians(70):
                lit = (at(0.95, 0.24, zr + 2.8 + 1.35), rot)
            idx += 1
            a += step
        # Bridges from the walkway to the core.
        for ab in (math.radians(20), math.radians(90), math.radians(160)):
            c, s = math.cos(ab), math.sin(ab)
            mid = (R - 5.0 + 5.0) / 2
            rot = _rz(ab)
            add_box(trim, (cx + c * mid, cy + s * mid, zr - 0.25), (R - 10.0, 2.0, 0.4), rot=rot)
            for side in (-1, 1):
                p = Vector((cx + c * mid, cy + s * mid, zr + 0.5)) + Vector((-s, c, 0)) * side
                add_box(trim, p, (R - 10.0, 0.05, 0.05), rot=rot)
            if ring == 'C':
                p = Vector((cx + c * (R - 6.0), cy + s * (R - 6.0), zr + 0.6))
                for k in range(3):
                    add_box(red, p + Vector((0, 0, -0.3 + k * 0.35)), (0.12, 2.1, 0.14), rot=rot @ Matrix.Rotation(0.25 * (1 if k % 2 else -1), 4, 'X'))
    _obj('AtriumFacades', facade, [m['plaster']], coll)
    _obj('AtriumOpenings', openings, [m['dark']], coll)
    _obj('AtriumTrim', trim, [m['stone']], coll)
    _obj('AtriumPlanters', planters, [m['wood']], coll)
    _obj('AtriumLamps', lamps, [m['ringlamp']], coll)
    _obj('AtriumRedLamps', red, [m['ringred']], coll)
    if lit:
        bm = bmesh.new()
        add_box(bm, lit[0], (0.9, 0.04, 0.9), rot=lit[1])
        _obj('AtriumLitWindow', bm, [m['homelight']], coll)
    # The core: a column through the middle, with its lift shafts and a band at each ring.
    bm = bmesh.new()
    add_cyl(bm, (cx, cy, ATRIUM_FLOOR), (cx, cy, ATRIUM_TOP), 5.0, seg=40)
    for _, zr in RINGS:
        add_cyl(bm, (cx, cy, zr - 0.6), (cx, cy, zr + 0.1), 5.4, seg=40)
    _obj('AtriumCore', bm, [m['stone']], coll)
    bm = bmesh.new()
    for ab in (math.radians(-110), math.radians(-90), math.radians(-70)):
        c, s = math.cos(ab), math.sin(ab)
        add_box(bm, (cx + c * 5.02, cy + s * 5.02, 0), (1.3, 0.1, ATRIUM_TOP - ATRIUM_FLOOR - 1), rot=_rz(ab + math.pi / 2))
    _obj('AtriumCoreShafts', bm, [m['dark']], coll)
    # Ring letters, painted on the wall over each ring, across the void and to either side.
    for ring, zr in RINGS:
        mat = _image_material(f'RingLetter{ring}', os.path.join(TEX, f'ring_{ring}.png'), rough=0.9, alpha=True)
        for k, ab in enumerate((math.radians(60), math.radians(120))):
            p = (cx + (R - 0.05) * math.cos(ab), cy + (R - 0.05) * math.sin(ab), zr + 7.4)
            p = (cx + (R + 0.15) * math.cos(ab), cy + (R + 0.15) * math.sin(ab), zr + 7.4)
            _plane(f'AtriumRing{ring}{k}', (4.2, 4.2), p, mat, coll, rot=_rz(ab - math.pi / 2) @ Matrix.Rotation(math.radians(90), 4, 'X'))


def residential_doorway(m, coll):
    """DL-03's end wall gets its doorway: the lane runs on through it into DL-04."""
    gz = DECK
    bm = bmesh.new()
    for y0, y1 in ((-0.55, -0.42), (0.45, 0.95)):
        add_box(bm, (DOOR4_X, (y0 + y1) / 2, gz + 1.6), (0.3, y1 - y0, 3.2))
    add_box(bm, (DOOR4_X, 0.2, gz + 2.35), (0.3, 1.5, 1.7))
    _obj('ResidentialWall', bm, [m['wall']], coll)
    bm = bmesh.new()
    for y in (-0.44, 0.44):
        add_box(bm, (DOOR4_X - 0.16, y, gz + 0.75), (0.06, 0.06, 1.5))
    add_box(bm, (DOOR4_X - 0.16, 0.0, gz + 1.5), (0.06, 0.94, 0.08))
    _obj('ResidentialDoorFrame', bm, [m['yellow']], coll)


def build_set(dl01, m, coll):
    make_textures()
    dl04_materials(m)
    residential_doorway(m, coll)
    build_goods_hall(m, coll)
    build_trolley(m, coll)
    build_lift(m, coll)
    build_belt(m, coll)
    build_tunnel(m, coll)
    build_atrium(m, coll)


# --------------------------------------------------------------------------
# D-17 clips
# --------------------------------------------------------------------------

def _reach(targets, body, body_rot, rest):
    import build_dl02
    return build_dl02.reach(targets, body, body_rot, rest)


def clip_teeter(dl01, arm):
    """The unlatched platform drops under him: knees buckle, claws fly up and wheel, he leans back and
    hops back to the landing (the game moves him: take-off at frame 12, landing at 22), then steadies."""
    track, spring, Clip, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY
    frames = 38
    c = Clip(arm, 'Teeter', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        buckle = track([(0, 0), (3, 1), (8, 0.6), (12, 0.3), (22, 0.8), (28, 0)], f)
        up = track([(0, 0), (4, 1), (20, 1), (30, 0.2), (38, 0)], f)
        wheel = math.sin(f * 1.4) * track([(4, 0), (6, 1), (14, 1), (20, 0)], f)
        hands = {s: CARRY[s] + Vector((s * 0.09 * up, 0.02 * up + 0.04 * wheel * s, 0.17 * up + 0.05 * wheel))
                 for _, s in SIDES}
        tuck = track([(12, 0), (15, 0.06), (19, 0.06), (22, 0)], f)
        feet = {side: ((0, 0.01 * s, tuck), (-20 * tuck / 0.06, 0, 0)) for side, s in SIDES}
        roll = 4 * math.sin(f * 1.1) * track([(22, 0), (24, 1), (34, 0)], f)
        c.pose(frame, body=(0, 0.02 * up, -0.05 * buckle),
               body_rot=(track([(0, 0), (3, 10), (8, -10), (12, -12), (20, -4), (24, 6), (32, 0)], f), roll, 0),
               head=(track([(0, 0), (3, 30), (10, 26), (14, 6), (24, 14), (30, 24), (38, 10)], f),
                     track([(24, 0), (30, 8), (38, 4)], f), 0),
               antenna=[(spring(f, 0, -28 * (1 + 0.3 * i), decay=5, freq=1.3) + spring(f, 22, 14, decay=4), 0) for i in range(3)],
               hands=hands, hand_rot={'L': (-40 - 30 * up, 0, 20), 'R': (-40 - 30 * up, 0, -20)},
               claws={'L': 34 * up + CLAW_REST_OPEN['L'] * (1 - up), 'R': 30 * up}, feet=feet)
    c.done()


def clip_pat(dl01, arm):
    """Goodbye to the goods trolley: he reaches to the ballast, pats it twice, rests the claw a moment,
    and gives a small nod."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 48
    c = Clip(arm, 'Pat', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        reach = track([(2, 0), (12, 1), (36, 1), (44, 0)], f)
        tap = sum(math.sin(math.pi * (f - t0) / 5) for t0 in (14, 21) if t0 <= f <= t0 + 5)
        body, rot = (0, -0.015 * reach, -0.01 * reach), (track([(0, 0), (12, 8), (36, 8), (44, 0)], f), 0, 0)
        target = Vector((-0.04, -0.27, T4_TOP + 0.075 + 0.025 * tap))
        right = _reach({1: Vector((0, 0, 0)), -1: target}, body, rot, REST)[-1]
        hands = {1: CARRY[1], -1: CARRY[-1].lerp(right, reach)}
        head = (track([(0, 0), (10, 18), (30, 16), (36, 8), (40, 20), (44, 4), (48, 0)], f),
                track([(8, 0), (14, 10), (30, 8), (38, 0)], f), 0)
        antenna = [(track([(0, 0), (12, 6), (30, 8), (40, -8), (48, -2)], f) + spring(f, 40, -8 * (1 + 0.3 * i), decay=4), 0)
                   for i in range(3)]
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands,
               hand_rot={'L': (-24, 6, 10), 'R': (-24 - 40 * reach, 0, -10)},
               claws={'L': CLAW_REST_OPEN['L'], 'R': track([(2, 1), (10, 12), (34, 12), (42, 1)], f)})
    c.done()


HOPS = ((18, 26), (28, 36), (38, 48))     # take-off and landing frames; the game moves him 0.32 m per hop


def clip_hopscotch(dl01, arm):
    """Chalk squares on the floor: he stops and looks down at them, then hops them, one foot, one foot,
    both feet; a little bounce and a pleased wiggle of the antenna."""
    track, spring, Clip, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY
    frames = 70
    c = Clip(arm, 'Hopscotch', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        air = [math.sin(math.pi * min(1, max(0, (f - a) / (b - a)))) for a, b in HOPS]
        crouch = sum(track([(a - 4, 0), (a, 1), (a + 2, 0)], f) + track([(b - 1, 0), (b + 1, 1), (b + 4, 0)], f) for a, b in HOPS)
        one_foot = track([(14, 0), (17, 1), (36, 1), (39, 0)], f)
        feet = {'L': ((0.01 * track([(38, 0), (46, 1)], f), 0, 0.03 * air[0] + 0.03 * air[1] + 0.035 * air[2]), (12 * air[2], 0, 0)),
                'R': ((-0.01 * track([(38, 0), (46, 1)], f), 0.02 * one_foot, 0.07 * one_foot + 0.035 * air[2]), (30 * one_foot, 0, 0))}
        cheer = track([(50, 0), (55, 1), (62, 1), (68, 0)], f)
        hands = {s: CARRY[s] + Vector((s * 0.03 * max(air), 0, 0.04 * max(air))) for _, s in SIDES}
        hands[-1] = hands[-1] + Vector((-0.02 * cheer, 0, 0.1 * cheer))
        wiggle = 10 * math.sin(f * 1.3) * track([(48, 0), (52, 1), (64, 1), (70, 0)], f)
        c.pose(frame, body=(0, 0, -0.03 * crouch + 0.012 * math.sin(math.pi * min(1, max(0, (f - 50) / 6)))),
               body_rot=(track([(0, 0), (8, 6), (16, 4), (48, 2), (54, -4), (70, 0)], f), 3 * one_foot, 0),
               head=(track([(0, 0), (8, 30), (16, 26), (48, 20), (54, -6), (70, 0)], f), track([(4, 0), (10, 10), (16, 0)], f), 0),
               antenna=[(track([(0, 0), (8, -10), (48, -6), (70, -2)], f) + wiggle * (1 + 0.3 * i) - spring(f, 48, 8), 0) for i in range(3)],
               feet=feet, hands=hands, hand_rot={'L': (-24, 6, 10), 'R': (-24 - 50 * cheer, 0, -10)},
               claws={'L': CLAW_REST_OPEN['L'], 'R': 1 + 20 * cheer})
    c.done()


def clip_look_back(dl01, arm):
    """At the tunnel mouth, turned back toward the depot (the game turns him): a long look, the antenna
    settling, a claw to the parcel window; then a small nod, and the antenna comes up."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 84
    c = Clip(arm, 'LookBack', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        reach = track([(30, 0), (40, 1), (58, 1), (66, 0)], f)
        window = Vector((-0.05, -0.24, 0.41))
        hands = {1: CARRY[1], -1: CARRY[-1].lerp(window - REST[-1], reach)}
        head = (track([(0, 0), (12, -8), (30, -6), (40, 18), (56, 16), (64, 0), (68, 14), (74, -4), (84, 0)], f),
                track([(6, 0), (16, 8), (30, 6), (40, 0)], f),
                track([(6, 0), (18, 12), (28, -10), (36, 0)], f))
        antenna = [(track([(0, 0), (20, 10), (50, 18), (64, 16), (72, -10), (84, -6)], f) * (0.8 + 0.15 * i)
                    - spring(f, 70, 10 * (1 + 0.3 * i), decay=5), 0) for i in range(3)]
        c.pose(frame, body=(0, 0, track([(0, 0), (40, -0.01), (64, -0.01), (72, 0.004), (84, 0)], f)),
               body_rot=(track([(0, 0), (40, 6), (60, 6), (70, -2), (84, 0)], f), 0, 0), head=head, antenna=antenna,
               hands=hands, hand_rot={'L': (-24, 6, 10), 'R': (-24 - 70 * reach, 0, -20 * reach)},
               claws={'L': CLAW_REST_OPEN['L'], 'R': track([(30, 1), (38, 5), (58, 5), (66, 1)], f)})
    c.done()


def clip_awe(dl01, arm):
    """At the balcony rail, facing out over the atrium (the game turns him): a step to the rail; the
    head lifts to the dead sky and travels slowly along the rings, left to right; the antenna stands up.
    Then down, to the dark of ring C; both claws come to his chest; a small step back, a long stillness,
    and a nod."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 160
    c = Clip(arm, 'Awe', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        fwd = track([(0, 0), (14, 0.04), (112, 0.04), (126, 0.0)], f)
        lift = [0.03 * math.sin(math.pi * min(1, max(0, (f - t0) / 8))) for t0 in (0, 6)]
        feet = {'L': ((0, -fwd, lift[0]), (0, 0, 0)), 'R': ((0, -fwd * 0.9, lift[1]), (0, 0, 0))}
        pitch = track([(0, 0), (14, -16), (40, -30), (70, -22), (90, 24), (120, 26), (136, 2), (146, 12), (160, 0)], f)
        yaw = track([(14, 0), (42, 34), (72, -34), (90, 0)], f)
        tilt = track([(40, 0), (50, 6), (66, -6), (90, 0), (120, 4), (136, 0)], f)
        hold = track([(88, 0), (100, 1), (128, 1), (140, 0)], f)
        window = Vector((-0.05, -0.24, 0.41))
        hands = {1: CARRY[1].lerp(Vector((0.05, -0.23, 0.36)) - REST[1], hold), -1: CARRY[-1].lerp(window - REST[-1], hold)}
        antenna = [(track([(0, 0), (20, -18), (88, -22), (110, 4), (136, 0), (160, -6)], f) * (0.8 + 0.15 * i)
                    + spring(f, 136, -8), 0) for i in range(3)]
        c.pose(frame, body=(0, -fwd * 0.6, track([(0, 0), (20, 0.008), (70, 0.008), (100, -0.012), (130, -0.012), (150, 0)], f)),
               body_rot=(track([(0, 0), (14, -3), (40, -8), (70, -6), (92, 6), (120, 6), (138, 0)], f), 0, 0),
               head=(pitch, tilt, yaw), feet=feet, hands=hands,
               hand_rot={'L': (-24 - 40 * hold, 6, 10), 'R': (-24 - 70 * hold, 0, -20 * hold)},
               claws={'L': CLAW_REST_OPEN['L'] * (1 - hold) + 4 * hold, 'R': track([(88, 1), (98, 5), (128, 5), (140, 1)], f)})
    c.done()


def add_clips(dl01, arm):
    clip_teeter(dl01, arm)
    clip_pat(dl01, arm)
    clip_hopscotch(dl01, arm)
    clip_look_back(dl01, arm)
    clip_awe(dl01, arm)
