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
from mathutils import Matrix, Vector, noise

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
# The refuge's cave: a cavern dug into the mountain, the city terraced up its walls. Its footprint (ring C's
# lip) is egg-shaped: narrow at the near end, where the balcony looks in, and wide across the far side.
CAVE = (78.0, 47.0, 34.0, 12.0, 40.0)   # centre x, y; half-width (mean, and its swell toward the far side); half-depth
CAVE_ARC = (math.radians(-65), math.radians(245))   # the near side, toward the camera, is cut away
CAVE_FLOOR = -11.0                   # the industrial floor, well below the balcony
# The terraces, bottom up: ring, height, and the offsets of its lip and back wall out from the footprint.
# Ring C, level with the balcony, is the poorest; 'U' is the first of the upper levels, only lights.
TIERS = (('C', 0.0, 0.0, 7.0), ('B', 10.0, 2.0, 8.5), ('A', 22.0, 4.0, 11.0), ('U', 32.0, 7.0, 10.5))
# The rock between them (height, offset): each face leans out over the terrace below, so the homes sit in
# niches under the next ledge.
CAVE_FACES = ((-13.5, 2.0), (-9.0, 0.8), (-4.5, -0.4), 'C', (2.5, 7.3), (5.0, 7.0), (6.8, 5.8), (8.6, 3.8),
              'B', (12.5, 8.8), (15.5, 8.5), (17.8, 7.2), (20.2, 5.6), 'A', (24.5, 11.3), (27.5, 11.0),
              (30.0, 9.8), (31.2, 8.0), 'U', (35.0, 10.7), (38.0, 9.5))
# The chimney up toward the surface: its mouth (where the vault closes) and its top (x, y, half-axes, z).
CHIMNEY = ((80.0, 64.0, 15.0, 12.5, 50.0), (84.0, 84.0, 9.0, 8.0, 120.0))
FAN_T = 96.0                         # the floor fan in the far wall (degrees round the footprint)
LIT_T = math.radians(84)             # the one lit window, on ring A, far across


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

    # The plate by the shaft's edge: the lever, the pawl, the platform held.
    img = Image.new('RGB', (630, 420), cream)
    d = ImageDraw.Draw(img)
    d.rectangle((10, 10, 620, 410), outline=ink, width=10)
    d.line((70, 330, 140, 150), fill=(150, 36, 30), width=18)              # the lever, pulled toward you
    d.ellipse((122, 128, 160, 166), fill=(150, 36, 30))
    d.rectangle((40, 330, 170, 350), fill=ink)
    d.arc((60, 140, 220, 300), 200, 290, fill=ink, width=8)
    d.polygon([(66, 186), (82, 150), (100, 192)], fill=ink)
    d.rectangle((300, 250, 590, 272), fill=ink)                             # the platform, and the dog over it
    d.line((360, 200, 430, 245), fill=(150, 36, 30), width=16)
    d.ellipse((346, 188, 372, 214), fill=ink)
    d.text((230, 40), 'SET PAWL', font=_font(64), fill=ink)
    d.text((232, 300), 'before boarding', font=_font(40, 'sans'), fill=ink)
    _age(img, 49, 0.7).save(os.path.join(TEX, 'pawl_plate.png'))

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
    m['plaster'] = simple_material('AtriumPlaster', (0.2, 0.185, 0.15), 0.9)
    m['dark'] = simple_material('AtriumDark', (0.006, 0.006, 0.006), 0.8)
    m['stone'] = simple_material('AtriumStone', (0.058, 0.052, 0.045), 0.95)
    m['barricade'] = simple_material('Barricade', (0.4, 0.06, 0.04), 0.7)
    m['brass'] = simple_material('Brass', (0.45, 0.32, 0.12), 0.45, metallic=0.8)
    m['cut'] = simple_material('AtriumCut', (0.085, 0.078, 0.066), 0.95)
    m['sheet'] = simple_material('AtriumSheet', (0.075, 0.082, 0.08), 0.6, metallic=0.4)
    m['rust'] = simple_material('AtriumRust', (0.11, 0.048, 0.025), 0.85)
    m['wet'] = simple_material('AtriumWet', (0.008, 0.009, 0.009), 0.18)
    m['upperlights'] = emission_material('AtriumUpperLights', (1.0, 0.66, 0.34), 2.0)
    m['upperglow'] = emission_material('AtriumUpperGlow', (1.0, 0.58, 0.28), 1.5)


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

    _plane('G4PawlPlate', (0.42, 0.28), (PAWL_X + 0.05, 1.78, DECK + 1.25), _image_material('PawlPlateMat', os.path.join(TEX, 'pawl_plate.png')), coll)

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
    bm = bmesh.new()                                      # rubber flaps, hinged at the top; the game swings them
    hinge = ((bx0 + TURN_X + 0.5) / 2, 1.76, DECK + 0.58)
    for k in range(7):
        add_box(bm, (bx0 + 0.12 + k * 0.1 - hinge[0], 0, -0.28), (0.085, 0.008, 0.56))
    _obj('TurnFlaps', bm, [m['rubber']], coll).location = hinge
    bm, bulb = bmesh.new(), bmesh.new()                   # a lamp over the hatch, so the crates are seen to go in
    add_box(bm, ((bx0 + TURN_X + 0.5) / 2, 1.72, DECK + 0.95), (0.3, 0.12, 0.08))
    add_sphere(bulb, ((bx0 + TURN_X + 0.5) / 2, 1.66, DECK + 0.88), 0.035, seg=10)
    _obj('G4HatchLamp', bm, [m['steel']], coll)
    _obj('G4HatchBulb', bulb, [m['hallbulb']], coll)
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
    add_box(bm, ((t0 + t1) / 2, 0.1, DECK - 1.45), (t1 - t0, 3.4, 2.9))     # the floor (it was missing)
    _obj('G4TunnelFloor', bm, [m['concrete']], coll)
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


# --------------------------------------------------------------------------
# The refuge's cave: rock, terraces, homes and industry. Far detail: flat and plain.
# --------------------------------------------------------------------------

def _cave_lip(t):
    """Ring C's lip at angle t, before the rock's lumps: an egg, with bays and bulges."""
    cx, cy, a0, swell, b = CAVE
    a = a0 + swell * math.sin(t) + 8.0 * math.cos(t) * (1 + math.sin(t)) / 2     # wider to the right, away from the near end
    k = 1 + 0.09 * math.sin(3 * t + 0.7) + 0.06 * math.sin(5 * t + 2.1)
    return Vector((cx + a * k * math.cos(t), cy + b * k * math.sin(t), 0.0))


def _cave_frame(t):
    """Ring C's lip at angle t, the wall's direction there (t increasing) and its normal out into the rock."""
    p = _cave_lip(t)
    d = (_cave_lip(t + 1e-4) - _cave_lip(t - 1e-4)).normalized()
    return p, d, Vector((d.y, -d.x, 0.0))


def _cave_d(p, z, rough=True):
    """How far the rock bulges out (or bites in) at a point of the footprint and a height: big slow lumps,
    and on the faces, a rougher grain. Lip and back of a terrace share it, so the terraces stay level."""
    q = Vector((p.x * 0.045, p.y * 0.045, z * 0.06))
    d = 3.0 * noise.noise(q) + 1.2 * noise.noise(q * 3.1 + Vector((7.1, 3.3, 1.9)))
    if rough:
        d += 1.3 * noise.noise(q * 9.0 + Vector((2.2, 9.1, 4.4)))
        d += 0.5 * abs(noise.noise(Vector((q.x * 2.0, q.y * 2.0, z * 0.9))))      # strata
    return d


def _tier_dz(t, ring):
    """Each terrace was cut in level stretches, a step of a metre or two between them. Ring C stays level
    near the balcony, where it meets the lane."""
    seed = {'C': 0.5, 'B': 3.7, 'A': 7.9, 'U': 11.3}[ring]
    v = noise.noise(Vector((math.cos(t) * 1.7, math.sin(t) * 1.7, seed)))
    dz = 1.2 * round(v * 3.0)
    if ring == 'C':
        a = abs((math.degrees(t) + 90 + 180) % 360 - 180)
        dz *= smoothstep((a - 35) / 30)
    return dz


def _warp(t, z):
    """The terraces' steps, carried by the rock between them."""
    zs = [(tz, _tier_dz(t, r)) for r, tz, _, _ in TIERS]
    if z <= zs[0][0]:
        return zs[0][1] * smoothstep((z - CAVE_FLOOR) / (zs[0][0] - CAVE_FLOOR))
    for (za, da), (zb, db) in zip(zs, zs[1:]):
        if z <= zb:
            return da + (db - da) * (z - za) / (zb - za)
    top = CAVE_FACES[-1][0]
    return zs[-1][1] * (1 - smoothstep((z - zs[-1][0]) / (top - zs[-1][0])))


def _cave_pt(t, z, off, rough=True):
    p, _, n = _cave_frame(t)
    return p + n * (off + _cave_d(p, z, rough)) + Vector((0, 0, z + _warp(t, z)))


def _cave_rows():
    """The wall's rows bottom up: (height, offset, rough, terrace) where terrace marks a lip row."""
    rows = []
    tiers = {t[0]: t for t in TIERS}
    for r in CAVE_FACES:
        if isinstance(r, str):
            _, z, lip, back = tiers[r]
            rows += [(z, lip, False, r), (z, back, False, None)]
        else:
            rows.append((r[0], r[1], True, None))
    return rows


def _tier(ring):
    return next(t for t in TIERS if t[0] == ring)


def _ledge(t, ring):
    """A terrace at angle t: its lip, its back wall, the wall's direction and the way out to the void."""
    _, z, lip, back = _tier(ring)
    p, d, n = _cave_frame(t)
    dd = _cave_d(p, z, False)
    up = Vector((0, 0, z + _tier_dz(t, ring)))
    return p + n * (lip + dd) + up, p + n * (back + dd) + up, d, -n


def _wall_off(t, z):
    """The wall's offset at angle t and height z (between its rows): to stand things just off it."""
    p, _, _ = _cave_frame(t)
    rows = _cave_rows()
    for (za, oa, ra, _), (zb, ob, rb, _) in zip(rows, rows[1:]):
        if za <= z <= zb and zb > za:
            f = (z - za) / (zb - za)
            return (oa + _cave_d(p, za, ra)) * (1 - f) + (ob + _cave_d(p, zb, rb)) * f
    return rows[-1][1] + _cave_d(p, rows[-1][0], rows[-1][2])


def _blocked(t, spans):
    return any(abs(t - c) < h for c, h in spans)


def _rot(T, F):
    """Local x along T, local y along F (out toward the void), z up."""
    return Matrix(((T.x, F.x, 0, 0), (T.y, F.y, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))


def _face(bm, c, T, F, w, h, mat=0, up=Vector((0, 0, 1))):
    """A flat quad centred at c, w along T and h along up, facing F."""
    hw, hh = T * (w / 2), up * (h / 2)
    vs = [bm.verts.new(c + a) for a in (-hw - hh, -hw + hh, hw + hh, hw - hh)]
    f = bm.faces.new(vs)
    f.material_index = mat
    f.normal_update()
    if f.normal.dot(F) < 0:
        f.normal_flip()
    return f


def _arch(bm, c, T, F, w, h, seg=6):
    """A dark tunnel mouth: an arched opening, c at the middle of its sill, facing F."""
    r = w / 2
    pts = [c - T * r, c + T * r]
    for k in range(seg + 1):
        a = math.pi * k / seg
        pts.append(c + T * (r * math.cos(a)) + Vector((0, 0, h - r + r * math.sin(a))))
    f = bm.faces.new([bm.verts.new(p) for p in pts])
    f.normal_update()
    if f.normal.dot(F) < 0:
        f.normal_flip()


def _wire(bm, pts, r, mat=0):
    """A thin three-sided tube through pts: cables, far off."""
    rings = []
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        u = d.cross(Vector((0, 0, 1)))
        u = u.normalized() if u.length > 1e-3 else Vector((1, 0, 0))
        v = d.cross(u)
        rings.append([bm.verts.new(p + (u * math.cos(a) + v * math.sin(a)) * r) for a in (0.0, 2.094, 4.189)])
    for a, b in zip(rings, rings[1:]):
        for k in range(3):
            bm.faces.new((a[k], a[(k + 1) % 3], b[(k + 1) % 3], b[k])).material_index = mat


def _pipe(bm, pts, r, seg=8):
    """A pipe along a polyline: one tube, its joints shared."""
    rings = []
    for i, p in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        u = d.cross(Vector((0, 0, 1)))
        u = u.normalized() if u.length > 1e-3 else Vector((1, 0, 0))
        v = d.cross(u)
        rings.append([bm.verts.new(p + (u * math.cos(a) + v * math.sin(a)) * r) for a in [2 * math.pi * k / seg for k in range(seg)]])
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k]))
    bm.faces.new(rings[0])
    bm.faces.new(rings[-1][::-1])


def _sag(a, b, sag, n=14):
    return [a.lerp(b, i / n) - Vector((0, 0, 4 * sag * (i / n) * (1 - i / n))) for i in range(n + 1)]


def _cave_obj(name, bm, mats, coll, smooth=False, sharp=50):
    """Like _obj, but keeps the winding as built (far quads face the camera) and shades flat unless asked."""
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for mat in mats:
        me.materials.append(mat)
    me.polygons.foreach_set('use_smooth', [smooth] * len(me.polygons))
    if smooth:
        me.set_sharp_from_angle(angle=math.radians(sharp))
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def _grid_faces(bm, grid, mat_of=lambda r, c: 0, cyclic=False, flip=False):
    cols = len(grid[0])
    for r in range(len(grid) - 1):
        for c in range(cols if cyclic else cols - 1):
            c1 = (c + 1) % cols
            vs = (grid[r][c], grid[r + 1][c], grid[r + 1][c1], grid[r][c1])
            if flip:
                vs = vs[::-1]
            try:
                bm.faces.new(vs).material_index = mat_of(r, c)
            except ValueError:
                pass


def _cave_shell(bm):
    """The cavern: the terraced wall around the open near side, the vault closing over it, and the
    chimney the city climbs toward the surface. Terrace tops are tool-cut (material 1), the rest raw rock."""
    t0, t1 = CAVE_ARC
    nw = 150
    ts = [t0 + (t1 - t0) * i / nw for i in range(nw + 1)]
    rows = _cave_rows()
    grid = [[bm.verts.new(_cave_pt(t, z, off, rough)) for t in ts] for z, off, rough, _ in rows]
    _grid_faces(bm, grid, lambda r, c: 1 if rows[r][3] else 0)
    # The vault: the wall's top row on round the near side, then up and in to the chimney's mouth.
    gap = 2 * math.pi - (t1 - t0)
    ng = max(4, int(nw * gap / (t1 - t0)))
    tg = [t1 + gap * i / ng for i in range(1, ng)]
    ztop, offtop = rows[-1][0], rows[-1][1]
    top = grid[-1] + [bm.verts.new(_cave_pt(t, ztop, offtop)) for t in tg]
    allt = ts + tg
    mx, my, ma, mb, mz = CHIMNEY[0]
    vault = [top]
    base = [v.co.copy() for v in top]
    for k in range(1, 6):
        ph = k / 5 * math.pi / 2
        f = 1 - math.cos(ph)
        z = ztop + (mz - ztop) * math.sin(ph)
        row = []
        for t, b in zip(allt, base):
            mpt = Vector((mx + ma * math.cos(t), my + mb * math.sin(t), mz))
            p = b.lerp(mpt, f)
            p.z = z + 2.5 * math.sin(math.pi * f) * noise.noise(Vector((p.x, p.y, 3.0)) * 0.08)
            row.append(bm.verts.new(p))
        vault.append(row)
    # The chimney: up and back, narrowing, toward the upper levels and the surface.
    hz = CHIMNEY[1][4]
    for k in range(1, 9):
        z = mz + (hz - mz) * k / 8
        cx, cy, a, b = _chimney_at(z)
        row = []
        for t in allt:
            c, s = math.cos(t), math.sin(t)
            j = _chimney_j(cx + a * c, cy + b * s, z)
            row.append(bm.verts.new(Vector((cx + a * c * j, cy + b * s * j, z))))
        vault.append(row)
    _grid_faces(bm, vault, cyclic=True)


def _chimney_at(z):
    """The chimney's centre and half-axes at a height."""
    (mx, my, ma, mb, mz), (hx, hy, ha, hb, hz) = CHIMNEY
    f = (z - mz) / (hz - mz)
    return mx + (hx - mx) * f, my + (hy - my) * f, ma + (ha - ma) * f, mb + (hb - mb) * f


def _chimney_j(x, y, z):
    return 1.0 + 0.16 * noise.noise(Vector((x, y, z)) * 0.12)


def _cliff(bm, lip, rows, side, top_back=None, mat_top=1, amp=0.6):
    """A rock face along a polyline (lip, in plan), rows (height, offset into the rock) bottom up; side +1
    puts the rock on the polyline's right. With top_back, a tool-cut top from the lip back to those points."""
    pts = [Vector((x, y, 0)) for x, y in lip]
    ns = []
    for i in range(len(pts)):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        ns.append(Vector((d.y, -d.x, 0)) * side)
    grid = []
    for z, off in rows:
        rough = abs(z - rows[-1][0]) > 1e-3 or top_back is None
        grid.append([bm.verts.new(p + n * (off + amp * _cave_d(p, z, rough)) + Vector((0, 0, z))) for p, n in zip(pts, ns)])
    _grid_faces(bm, grid, flip=side < 0)
    if top_back:
        zt = rows[-1][0]
        back = [bm.verts.new(Vector((x, y, zt))) for x, y in top_back]
        _grid_faces(bm, [grid[-1], back], lambda r, c: mat_top, flip=side < 0)


def _lump(bm, c, size, seed):
    """A mass of rock: a spur standing out of the wall, or a fall of it."""
    res = bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1.0)
    off = Vector((seed * 3.1, seed * 1.7, seed * 2.3))
    for v in res['verts']:
        n = v.co.normalized()
        k = 1 + 0.32 * noise.noise(n * 1.6 + off) + 0.12 * noise.noise(n * 4.0 + off)
        v.co = c + Vector((n.x * size[0], n.y * size[1], n.z * size[2])) * k


def _pillar(bm, x, y, r0, seed, z0=CAVE_FLOOR - 1.5, z1=46.5, taper=None, lean=(0.0, 0.0)):
    """A natural column of rock, floor to vault, waisted in the middle and leaning; with taper (radius
    fraction at z0), a stalactite hanging from the vault instead."""
    rows = []
    n = 13
    for k in range(n):
        z = z0 + (z1 - z0) * k / (n - 1)
        u = k / (n - 1)
        if taper is None:
            f = (z - 14.0) / 30.0
            r = r0 * (0.7 + 1.1 * f * f)
        else:
            r = r0 * (taper + (1 - taper) * u ** 0.7)
        cx = x + lean[0] * u + 1.6 * noise.noise(Vector((seed, z * 0.06, 1.0)))
        cy = y + lean[1] * u + 1.6 * noise.noise(Vector((seed, z * 0.06, 7.0)))
        ring = []
        for i in range(11):
            a = 2 * math.pi * i / 11
            p = Vector((math.cos(a), math.sin(a), 0))
            j = 1 + 0.4 * noise.noise(Vector((p.x * 1.4 + seed, p.y * 1.4, z * 0.09))) + 0.15 * noise.noise(Vector((p.x * 4 + seed, p.y * 4, z * 0.3)))
            ring.append(bm.verts.new(Vector((cx, cy, z)) + p * r * j))
        rows.append(ring)
    _grid_faces(bm, rows, cyclic=True, flip=True)
    if taper is not None:
        bm.faces.new(rows[0])


def _floor_z(x, y):
    q = Vector((x * 0.05, y * 0.05, 0.3))
    return CAVE_FLOOR + 0.7 * noise.noise(q) + 0.25 * noise.noise(q * 4 + Vector((1.7, 0.2, 0.0)))


def _cave_floor(bm):
    xs = [20.0 + 2.5 * i for i in range(48)]
    ys = [-4.0 + 2.5 * j for j in range(44)]
    grid = [[bm.verts.new((x, y, _floor_z(x, y))) for x in xs] for y in ys]
    cx, cy, a0, sw, b = CAVE

    def inside(r, c):
        x, y = xs[c] + 1.25, ys[r] + 1.25
        return ((x - cx) / (a0 + sw + 9)) ** 2 + ((y - cy) / (b + 9)) ** 2 < 1.0 or y < 16
    for r in range(len(ys) - 1):
        for c in range(len(xs) - 1):
            if inside(r, c):
                bm.faces.new((grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c]))
    for v in [v for v in bm.verts if not v.link_faces]:
        bm.verts.remove(v)


def _container(b, c, T, F, size, rnd, front=True):
    """A shipping-box home: w along T, d along F, h up, its front toward F: a door, maybe a window, dark."""
    w, d, h = size
    add_box(b['rust'] if rnd.random() < 0.55 else b['sheet'], c + Vector((0, 0, h / 2)), size, rot=_rot(T, F))
    if not front:
        return
    fc = c + F * (d / 2 + 0.02)
    u = rnd.uniform(-0.3, 0.3) * w
    _face(b['dark'], fc + T * u + Vector((0, 0, 0.95)), T, F, 0.85, 1.9)
    if w > 3 and rnd.random() < 0.6:
        side = -1 if u > 0 else 1
        _face(b['dark'], fc + T * (side * w * 0.28) + Vector((0, 0, 1.45)), T, F, 1.1, 0.7)


def _house(b, c, T, F, w, d, floors, rnd, mat):
    """A built home: plaster or sheet walls, a slab roof (now and then a tank or a flue on it), windows in
    a row on each floor."""
    h = 3.0 * floors + 0.3
    add_box(mat, c + Vector((0, 0, h / 2)), (w, d, h), rot=_rot(T, F))
    add_box(b['cut'] if rnd.random() < 0.6 else b['rust'], c + Vector((0, 0, h + 0.1)) + F * 0.2, (w + 0.3, d + 0.5, 0.2), rot=_rot(T, F))
    r = rnd.random()
    if r < 0.3:
        q = c + T * rnd.uniform(-w / 3, w / 3) - F * (d / 4) + Vector((0, 0, h + 0.2))
        add_cyl(b['rust'] if r < 0.15 else b['sheet'], q, q + Vector((0, 0, 1.3)), 0.6, seg=8)
    elif r < 0.5:
        q = c + T * rnd.uniform(-w / 3, w / 3) - F * (d / 3) + Vector((0, 0, h))
        add_cyl(b['sheet'], q, q + Vector((0, 0, 2.2)), 0.12, seg=6)
    fc = c + F * (d / 2 + 0.02)
    n = max(1, int(w / 1.9))
    door = rnd.randrange(n)
    for f in range(floors):
        for i in range(n):
            u = (i - (n - 1) / 2) * (w / n)
            if f == 0 and i == door:
                _face(b['dark'], fc + T * u + Vector((0, 0, 1.0)), T, F, 0.9, 2.0)
            elif rnd.random() < 0.85:
                _face(b['dark'], fc + T * u + Vector((0, 0, 3.0 * f + 1.6)), T, F, 0.95, 1.0)


def _barricade(b, c, T, F, span, rnd):
    """A seal across a terrace: overlapping sheets on posts from lip to back wall, taped across."""
    k = max(2, int(span / 1.1))
    for i in range(k):
        u = (i + 0.5) / k - 0.5
        add_box(b['rust'] if rnd.random() < 0.6 else b['sheet'], c + F * (u * span) + T * (0.05 * (i % 2)) + Vector((0, 0, 1.3 + rnd.uniform(-0.1, 0.15))),
                (0.04, span / k + 0.15, 2.6), rot=_rot(T, F) @ Matrix.Rotation(rnd.uniform(-0.04, 0.04), 4, 'X'))
    for s in (-1, 1):
        add_box(b['barricade'], c - T * 0.08 + Vector((0, 0, 1.4 + 0.3 * s)), (0.03, span * 0.95, 0.16),
                rot=_rot(T, F) @ Matrix.Rotation(s * 0.18, 4, 'X'))


def _ring_c(b, rnd, blocked):
    """Ring C, the lowest and poorest: shipping boxes stacked two high in the niches under ring B, lean-to
    sheet, scaffold, sealed with barricades and tape; a few red lamps."""
    t0, t1 = CAVE_ARC
    t = t0 + 0.12
    k = 0
    while t < t1 - 0.12:
        if _blocked(t, blocked):
            t += 0.03
            continue
        lip, back, T, F = _ledge(t, 'C')
        depth = (back - lip).length
        k += 1
        if k % 8 == 0:
            # A barricade across the terrace, lip to back wall, taped, with a red lamp.
            _barricade(b, (lip + back) / 2, T, F, depth + 0.6, rnd)
            add_box(b['red'], lip + F * 0.1 + Vector((0, 0, 2.8)), (0.3, 0.3, 0.3))
            t += 2.5 / 40
            continue
        endon = rnd.random() < 0.35
        w, d = (2.45, 6.0) if endon else (6.1, 2.45)
        d = min(d, depth - 0.6)
        c = back + F * (d / 2 + 0.15) - Vector((0, 0, 0.2))
        _container(b, c, T, F, (w, d, 2.6), rnd)
        clear = _tier('B')[1] + _tier_dz(t, 'B') - lip.z
        if rnd.random() < 0.6 and clear > 8.0:
            w2 = 2.45 if rnd.random() < 0.5 else min(w, 6.1)
            _container(b, c + T * rnd.uniform(-0.6, 0.6) + Vector((0, 0, 2.62)) - F * 0.3, T, F, (w2, 2.45, 2.5), rnd)
            if rnd.random() < 0.5:                   # the stair up: a plank
                sp = c + F * (d / 2 + 0.7) + T * (w / 2 - 0.6) + Vector((0, 0, 1.3))
                add_box(b['sheet'], sp, (2.9, 0.7, 0.08), rot=_rot(T, F) @ Matrix.Rotation(-0.75, 4, 'Y'))
        if rnd.random() < 0.5:                       # a lean-to of corrugated sheet off the front
            rp = c + F * (d / 2 + 0.75) + Vector((0, 0, 2.35))
            add_box(b['rust' if rnd.random() < 0.5 else 'sheet'], rp, (w + 0.4, 1.6, 0.05), rot=_rot(T, F) @ Matrix.Rotation(-0.2, 4, 'X'))
            for s in (-1, 1):
                add_box(b['sheet'], c + F * (d / 2 + 1.45) + T * (s * w / 2) + Vector((0, 0, 1.05)), (0.08, 0.08, 2.1), rot=_rot(T, F))
        elif rnd.random() < 0.35:                    # a scaffold of poles and a deck
            for s in (-1, 1):
                add_box(b['sheet'], c + F * (d / 2 + 0.5) + T * (s * w * 0.45) + Vector((0, 0, 2.6)), (0.08, 0.08, 5.2), rot=_rot(T, F))
            add_box(b['sheet'], c + F * (d / 2 + 0.5) + Vector((0, 0, 2.62)), (w, 0.6, 0.06), rot=_rot(T, F))
        t += (w + rnd.uniform(0.3, 2.6)) / 40


def _ring_b(b, rnd, blocked):
    """Ring B: block homes of plaster and sheet, one or two floors, a few boxes between; a parapet of
    cut stone at the lip and a lamp now and then."""
    t0, t1 = CAVE_ARC
    t = t0 + 0.14
    k = 0
    while t < t1 - 0.14:
        if _blocked(t, blocked):
            t += 0.03
            continue
        lip, back, T, F = _ledge(t, 'B')
        k += 1
        r = rnd.random()
        if r < 0.3:
            w, d = 6.1, 2.45
            _container(b, back + F * (d / 2 + 0.2), T, F, (w, d, 2.6), rnd)
            if rnd.random() < 0.4:
                _container(b, back + F * (d / 2 + 0.1) + Vector((0, 0, 2.62)), T, F, (2.45, 2.45, 2.5), rnd)
        else:
            w = rnd.uniform(3.6, 6.5)
            d = rnd.uniform(3.2, 4.4)
            _house(b, back + F * (d / 2 + 0.1) + Vector((0, 0, -0.1)), T, F, w, d, 2 if rnd.random() < 0.6 else 1, rnd,
                   b['plaster'] if r < 0.62 else (b['sheet'] if r < 0.85 else b['rust']))
        lp = lip - F * 0.3
        add_box(b['cut'], lp + Vector((0, 0, 0.45)), (w + 1.2, 0.25, 0.9), rot=_rot(T, F))
        if k % 4 == 0 and rnd.random() < 0.7:
            add_box(b['sheet'], lp + Vector((0, 0, 1.4)), (0.08, 0.08, 2.8), rot=_rot(T, F))
            add_box(b['lamp'] if rnd.random() < 0.55 else b['sheet'], lp + F * 0.3 + Vector((0, 0, 2.75)), (0.3, 0.3, 0.3), rot=_rot(T, F))
        t += (w + rnd.uniform(0.2, 1.6)) / 45


def _ring_a(b, rnd, blocked):
    """Ring A: the best built down here. Rows of two-floor plaster homes with slab roofs and windows in
    rows, a parapet; nearly every window dark, one lit, far across."""
    t0, t1 = CAVE_ARC
    t = t0 + 0.16
    k = 0
    lit = None
    while t < t1 - 0.16:
        if _blocked(t, blocked):
            t += 0.03
            continue
        lip, back, T, F = _ledge(t, 'A')
        k += 1
        w = rnd.uniform(6.0, 8.0)
        d = rnd.uniform(4.5, 5.5)
        floors = 2 if rnd.random() < 0.75 else 1
        c = back + F * (d / 2 + 0.1) + Vector((0, 0, -0.1))
        _house(b, c, T, F, w, d, floors, rnd, b['plaster'] if rnd.random() < 0.8 else b['sheet'])
        if floors == 2 and rnd.random() < 0.3:      # a room built on top, set back
            _house(b, c - F * 1.2 + T * rnd.uniform(-1, 1) + Vector((0, 0, 6.5)), T, F, w * 0.55, d * 0.5, 1, rnd, b['sheet'])
        if lit is None and t > LIT_T:
            lit = (c + F * (d / 2 + 0.04) + T * (w * 0.25) + Vector((0, 0, 4.6)), T, F)
        lp = lip - F * 0.3
        add_box(b['cut'], lp + Vector((0, 0, 0.5)), (w + 0.6, 0.25, 1.0), rot=_rot(T, F))
        if k % 3 == 1 and rnd.random() < 0.75:
            add_box(b['sheet'], lp + Vector((0, 0, 1.6)), (0.08, 0.08, 3.2), rot=_rot(T, F))
            add_box(b['lamp'] if rnd.random() < 0.6 else b['sheet'], lp + F * 0.3 + Vector((0, 0, 3.1)), (0.32, 0.32, 0.32), rot=_rot(T, F))
        t += (w + rnd.uniform(0.3, 1.2) + (6.0 if rnd.random() < 0.15 else 0.0)) / 50
    return lit


def _upper_lights(b, rnd):
    """The levels above: no more than lights, lamps left burning along their terraces. The upper terrace
    across the far side (its windows dark), then rows of lamps up the chimney, more of them lit the higher
    they are."""
    t = math.radians(12)
    while t < math.radians(168):
        lip, bk, T, F = _ledge(t, 'U')
        if rnd.random() < 0.5:
            _face(b['dark'], bk + F * 0.3 + Vector((0, 0, rnd.choice((1.2, 2.8)))), T, F, 1.2, 0.9)
        if rnd.random() < 0.18:
            _face(b['upper'], lip - F * 0.2 + Vector((0, 0, 1.6)), T, F, 0.55, 0.55)
        t += rnd.uniform(0.02, 0.06)
    for z in (54.0, 57.5, 61.0, 65.0, 69.5, 74.5, 80.0, 86.0, 96.0, 106.0):
        cx, cy, a, bb = _chimney_at(z)
        f = min(1.0, (z - 50.0) / 40.0)
        n = int(26 + 20 * f)
        for i in range(n):
            t = 2 * math.pi * (i + rnd.random() * 0.6) / n
            if rnd.random() < (0.15 if math.sin(t) > 0.2 else 0.45):
                continue
            c, s = math.cos(t), math.sin(t)
            j = _chimney_j(cx + a * c, cy + bb * s, z)
            p = Vector((cx + (a * j - 0.8) * c, cy + (bb * j - 0.8) * s, z + rnd.uniform(-0.6, 0.6)))
            F = Vector((-c * bb, -s * a, 0)).normalized()
            T = Vector((-F.y, F.x, 0))
            if rnd.random() < 0.3 + 0.45 * f:
                _face(b['upper'], p, T, F, 0.8 + 0.4 * f, 0.8 + 0.4 * f)
            else:
                _face(b['dark'], p, T, F, 1.3, 1.0)


def _risers(b, rnd):
    """Pipe runs up the walls from the floor, bracketed to the terraces, some to the vault and some
    turning along under a terrace's lip; and the big duct from the floor fan."""
    rows = _cave_rows()
    for deg, rr, count, top, run in ((-44, 0.55, 2, 'B', 22), (-8, 0.9, 1, None, 0), (24, 0.6, 3, 'A', -26),
                                      (62, 1.1, 1, None, 0), (128, 0.6, 2, 'B', 30), (160, 0.8, 1, None, 0),
                                      (198, 0.55, 3, 'A', -20), (232, 0.7, 1, 'C', -14)):
        t = math.radians(deg)
        p, T, n = _cave_frame(t)
        zt = _tier(top)[1] + _tier_dz(t, top) - 1.0 if top else 40.0
        lo = min(_cave_d(p, z, rough) + off for z, off, rough, _ in rows if -11.5 < z < zt + 1)
        for j in range(count):
            sh = (j - (count - 1) / 2) * (2 * rr + 0.35)
            base = p + n * (lo - rr - 0.5) + T * sh
            pts = [base + Vector((0, 0, CAVE_FLOOR - 1)), base + Vector((0, 0, zt - j * 0.1))]
            if top:
                # Along under the terrace's lip, following it round.
                _, z, lip, _ = _tier(top)
                steps = max(2, int(abs(run) / 3))
                for s in range(1, steps + 1):
                    ts = t + (run / 40.0) * s / steps
                    q, _, nq = _cave_frame(ts)
                    pts.append(q + nq * (lip + _cave_d(q, z, False) - rr - 0.6 - j * (2 * rr + 0.3)) + Vector((0, 0, zt - j * 0.1)))
            _pipe(b['rust'] if (deg + j) % 3 == 0 else b['sheet'], pts, rr, seg=8)
            for ring, z, lip, back in TIERS[:3]:
                if z + _tier_dz(t, ring) > zt:
                    break
                q = p + n * (lip + _cave_d(p, z, False)) + T * sh + Vector((0, 0, z + _tier_dz(t, ring) - 0.6))
                add_cyl(b['sheet'], Vector((base.x, base.y, q.z)), q, 0.08, seg=4)
    # The big duct from the floor fan up the far wall, past every terrace.
    t = math.radians(FAN_T)
    p, T, n = _cave_frame(t)
    lo = min(off + _cave_d(p, z, rough) for z, off, rough, _ in rows if -1.0 < z < 34)
    c = p + n * (lo - 1.7)
    add_box(b['sheet'], c + Vector((0, 0, 16.0)), (2.6, 2.6, 33.0), rot=_rot(T, -n))
    add_box(b['sheet'], c + Vector((0, 0, 32.5)) + T * 4.0, (8.0, 2.6, 2.6), rot=_rot(T, -n))


def _fan(blades, frame, hub, axis, radius, n_blades):
    """A ventilation fan: its ring goes in frame (world), its blades in their own mesh around their local
    Z (the spin axis), to be placed at hub."""
    add_torus(frame, hub, axis, radius + 0.35, 0.32, seg=28, rseg=6)
    for k in range(n_blades):
        a = 2 * math.pi * k / n_blades
        rot = Matrix.Rotation(a, 4, 'Z') @ Matrix.Rotation(0.38, 4, 'X')
        add_box(blades, rot @ Vector((radius * 0.52, 0, 0)), (radius * 0.9, radius * 0.32, 0.08), rot=rot)
    add_cyl(blades, (0, 0, -0.5), (0, 0, 0.5), radius * 0.14, seg=12)


def _floor_works(b, rnd):
    """The cave floor: tanks, a pump house, pipes, a trunk main, floor shacks, scrap, and puddles."""
    def fz(x, y):
        return _floor_z(x, y) - 0.3
    for x, y, r, h in ((70.5, 17.0, 3.2, 7.5), (78.5, 21.5, 2.6, 6.0), (63.5, 25.0, 3.8, 9.0), (59.0, 36.0, 3.0, 6.5), (98.0, 33.0, 3.4, 8.0)):
        z = fz(x, y)
        mat = b['rust'] if rnd.random() < 0.5 else b['sheet']
        add_cyl(mat, (x, y, z), (x, y, z + h), r, seg=18)
        add_cyl(mat, (x, y, z + h), (x, y, z + h + r * 0.35), r, 0.4, seg=18)
        for k in range(2):
            add_cyl(b['sheet'], (x, y, z + h * (0.3 + 0.4 * k)), (x, y, z + h * (0.3 + 0.4 * k) + 0.25), r + 0.06, seg=18)
        add_box(b['sheet'], (x - r - 0.25, y, z + h / 2 + 1), (0.12, 0.5, h + 2))
    for x, y in ((86.5, 24.0), (88.0, 31.0)):
        z = fz(x, y)
        add_cyl(b['rust'], (x - 4.5, y, z + 2.4), (x + 4.5, y, z + 2.4), 1.7, seg=14)
        for s in (-3, 3):
            add_box(b['cut'], (x + s, y, z + 0.4), (0.6, 2.8, 1.2))
    # The pump house, its pumps outside, and the pipes between.
    x, y = 81.5, 13.0
    z = fz(x, y)
    add_box(b['sheet'], (x, y, z + 1.8), (6.5, 3.8, 3.6))
    add_box(b['rust'], (x, y, z + 3.75), (7.2, 4.4, 0.08), rot=Matrix.Rotation(0.06, 4, 'X'))
    _face(b['dark'], Vector((x - 1.5, y + 1.92, z + 1.1)), Vector((1, 0, 0)), Vector((0, 1, 0)), 1.1, 2.2)
    for k in range(3):
        px = x - 2.2 + 2.2 * k
        add_cyl(b['sheet'], (px, y + 2.6, z + 0.7), (px, y + 4.0, z + 0.7), 0.6, seg=12)
        add_box(b['cut'], (px, y + 3.3, z + 0.2), (1.2, 1.8, 0.4))
    pz = fz(75, 20) + 0.7
    for a, c in (((70.5, 17.0), (80.0, 15.6)), ((78.5, 21.5), (82.0, 16.6)), ((63.5, 25.0), (70.5, 17.0)), ((86.5, 24.0), (83.0, 16.6))):
        add_cyl(b['rust'], (a[0], a[1], pz), (c[0], c[1], pz), 0.35, seg=8)
    # A trunk main along the floor to the far wall on stands, and up the cliff to ring C's shelf.
    pts = [Vector((84.0, 4.6, 0.6)), Vector((84.0, 6.5, fz(84, 6.5) + 1.6))]
    for k in range(11):
        y0 = 10.0 + 7.0 * k
        pts.append(Vector((84.0 - 0.15 * k * k, y0, fz(84, y0) + 1.6)))
        add_box(b['cut'], (84.0 - 0.15 * k * k, y0, fz(84, y0) + 0.4), (1.8, 0.4, 0.8))
    _pipe(b['sheet'], pts, 0.8, seg=10)
    # Shacks on the floor between the machines: people live even down here.
    for x, y, a in ((66.0, 12.0, 0.4), (60.0, 18.0, 0.9), (74.0, 30.0, -0.3), (92.0, 18.0, 1.3), (95.0, 41.0, 0.2), (55.0, 28.0, 1.6), (68.0, 36.0, 0.1)):
        T = Vector((math.cos(a), math.sin(a), 0))
        F = Vector((-T.y, T.x, 0))
        _container(b, Vector((x, y, fz(x, y) + 0.3)), T, F, (6.1, 2.45, 2.6), rnd)
        if rnd.random() < 0.5:
            add_box(b['rust'], Vector((x, y, fz(x, y) + 2.85)) + F * 1.6, (6.6, 1.8, 0.05), rot=_rot(T, F) @ Matrix.Rotation(-0.15, 4, 'X'))
    for _ in range(26):
        x, y = rnd.uniform(52, 104), rnd.uniform(8, 80)
        s = (rnd.uniform(0.6, 2.5), rnd.uniform(0.6, 2.0), rnd.uniform(0.3, 1.2))
        add_box(b['rust' if rnd.random() < 0.6 else 'sheet'], (x, y, fz(x, y) + s[2] / 2), s, rot=_rz(rnd.uniform(0, 3)) @ Matrix.Rotation(rnd.uniform(-0.2, 0.2), 4, 'X'))
    for x, y, r in ((74.0, 11.0, 2.2), (68.0, 23.0, 1.6), (88.5, 13.0, 2.6), (77.0, 34.0, 3.0), (62.0, 31.0, 1.8), (93.0, 27.0, 1.5), (82.0, 45.0, 3.5), (70.0, 52.0, 2.4)):
        z = max(_floor_z(x + r * math.cos(a), y + r * math.sin(a)) for a in (0, 1.57, 3.14, 4.71)) + 0.03
        vs = [b['wet'].verts.new((x + r * math.cos(a) * (1 + 0.3 * math.sin(3 * a)), y + r * 0.7 * math.sin(a), z)) for a in [2 * math.pi * i / 10 for i in range(10)]]
        b['wet'].faces.new(vs)


def _trestle(b, p, T, F, zb):
    """A lattice tower from the floor up to p: four legs and braces."""
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = p + T * (sx * 1.2) + F * (sy * 1.2)
            add_box(b['sheet'], Vector((q.x, q.y, (zb + p.z) / 2)), (0.25, 0.25, p.z - zb), rot=_rot(T, F))
    z = zb + 3
    while z < p.z - 1:
        for s in (-1, 1):
            add_box(b['sheet'], p + F * (s * 1.2) + Vector((0, 0, z - p.z)), (2.6, 0.1, 0.1), rot=_rot(T, F))
            add_box(b['sheet'], p + T * (s * 1.2) + Vector((0, 0, z - p.z)), (0.1, 2.6, 0.1), rot=_rot(T, F))
        z += 3.5


def _crossings(b, rnd):
    """Catwalks across the void (ring C's, pipes slung under it, on trestles from the floor; ring B's pipe
    bridge further back), plank bridges sagging between terraces, ladders and stairs."""
    for ta, tb, ring, pipes, legs in ((214, 14, 'C', 2, (0.3, 0.64)), (134, 52, 'B', 1, (0.5,))):
        la, _, _, _ = _ledge(math.radians(ta), ring)
        lb, _, _, _ = _ledge(math.radians(tb), ring)
        la.z = lb.z = min(la.z, lb.z) - 0.15
        d = lb - la
        L = d.length
        T = d.normalized()
        F = Vector((-T.y, T.x, 0))
        mid = (la + lb) / 2
        add_box(b['sheet'], mid, (L + 2, 1.5, 0.12), rot=_rot(T, F))
        for s in (-1, 1):
            add_box(b['sheet'], mid + F * (s * 0.72) + Vector((0, 0, 1.0)), (L + 2, 0.05, 0.05), rot=_rot(T, F))
        x = 0.0
        while x < L:
            for s in (-1, 1):
                add_box(b['sheet'], la + T * x + F * (s * 0.72) + Vector((0, 0, 0.5)), (0.05, 0.05, 1.0), rot=_rot(T, F))
            x += 4.0
        for j in range(pipes):
            off = F * (0.45 * (2 * j - 1) if pipes > 1 else 0) + Vector((0, 0, -0.9))
            add_cyl(b['rust' if j else 'sheet'], la + off, lb + off, 0.45, seg=10)
        for f in legs:
            p = la.lerp(lb, f)
            _trestle(b, p, T, F, _floor_z(p.x, p.y) - 0.3)
    # Plank bridges, sagging, between terraces across a corner of the void.
    for (ta, ra), (tb, rb), sag in (((35, 'A'), (100, 'U'), 2.2), ((205, 'B'), (150, 'A'), 1.6)):
        a, _, _, _ = _ledge(math.radians(ta), ra)
        c, _, _, _ = _ledge(math.radians(tb), rb)
        pts = _sag(a + Vector((0, 0, 0.1)), c + Vector((0, 0, 0.1)), sag, 16)
        side = Vector((-(c - a).y, (c - a).x, 0)).normalized()
        for p, q in zip(pts, pts[1:]):
            d = q - p
            T = Vector((d.x, d.y, 0)).normalized()
            pitch = math.atan2(d.z, Vector((d.x, d.y)).length)
            add_box(b['rust'], (p + q) / 2, (d.length, 1.0, 0.08), rot=_rot(T, Vector((-T.y, T.x, 0))) @ Matrix.Rotation(-pitch, 4, 'Y'))
        for s in (-1, 1):
            _wire(b['cable'], [p + Vector((0, 0, 1.0)) + side * (0.5 * s) for p in pts], 0.035)
    # Ladders: ring C up to ring B's lip, ring B up to ring A's.
    for deg, lo, hi in ((-30, 'C', 'B'), (35, 'C', 'B'), (100, 'C', 'B'), (150, 'C', 'B'), (210, 'C', 'B'),
                        (10, 'B', 'A'), (75, 'B', 'A'), (128, 'B', 'A'), (190, 'B', 'A')):
        t = math.radians(deg)
        _, zh, liph, _ = _tier(hi)
        _, zl, _, _ = _tier(lo)
        p, T, n = _cave_frame(t)
        top = p + n * (liph + _cave_d(p, zh, False) - 0.35) + Vector((0, 0, zh + _tier_dz(t, hi) + 0.9))
        bot = p + n * (liph + _cave_d(p, zl, False) - 0.2) + Vector((0, 0, zl + _tier_dz(t, lo)))
        for s in (-1, 1):
            add_cyl(b['sheet'], bot + T * (s * 0.28), top + T * (s * 0.28), 0.04, seg=4)
        k = int((top - bot).length / 0.9)
        for i in range(1, k):
            _face(b['sheet'], bot.lerp(top, i / k), T, -n, 0.56, 0.06)
    # Stairs: two flights from ring B to ring A, sloped plates with a rail.
    for deg in (48, 168):
        t = math.radians(deg)
        _, zb, _, _ = _tier('B')
        _, za, lipa, _ = _tier('A')
        zb += _tier_dz(t, 'B')
        za += _tier_dz(t, 'A')
        p, T, n = _cave_frame(t)
        base = p + n * (lipa + _cave_d(p, za, False) - 1.0)
        half = (za - zb) / 2
        for z0, s in ((zb, 1), (zb + half, -1)):
            c = base + T * (s * half / 2) + Vector((0, 0, z0 + half / 2))
            R = _rot(T, -n) @ Matrix.Rotation(-math.atan2(half, half) * s, 4, 'Y')
            add_box(b['sheet'], c, (half * 1.414, 1.1, 0.18), rot=R)
            add_box(b['sheet'], c - n * 0.55 + Vector((0, 0, 0.9)), (half * 1.414, 0.05, 0.05), rot=R)
        add_box(b['sheet'], base + T * half + Vector((0, 0, zb + half - 0.1)), (1.6, 1.4, 0.15), rot=_rot(T, -n))


def _cables(b, rnd):
    """Cables strung across the void and along the terraces, with a bulb here and there: warm, a few red
    on ring C, many dead."""
    spans = ((205, 'C', -25, 'C', 3.0), (170, 'C', 30, 'C', 5.0), (230, 'B', 120, 'C', 4.0), (-40, 'B', 70, 'B', 6.0),
             (140, 'B', 40, 'A', 6.0), (195, 'A', 15, 'A', 8.0), (100, 'A', 55, 'U', 3.0), (240, 'C', 160, 'B', 3.0))
    for ta, ra, tb, rb, sag in spans:
        a, _, _, _ = _ledge(math.radians(ta), ra)
        c, _, _, _ = _ledge(math.radians(tb), rb)
        pts = _sag(a + Vector((0, 0, 3.2)), c + Vector((0, 0, 3.2)), sag, 18)
        _wire(b['cable'], pts, 0.05)
        for i in range(2, len(pts) - 2, 2):
            r = rnd.random()
            key = 'red' if (ra == 'C' and r < 0.2) else ('lamp' if r < 0.38 else ('cable' if r < 0.7 else None))
            if key:
                add_box(b[key], pts[i] - Vector((0, 0, 0.25)), (0.28, 0.28, 0.32))
    # Along ring C's back wall: festoons from niche to niche, mostly dead.
    t0, t1 = CAVE_ARC
    t = t0 + 0.1
    while t < t1 - 0.2:
        t2 = t + rnd.uniform(0.1, 0.2)
        _, a, _, F = _ledge(t, 'C')
        _, c, _, F2 = _ledge(t2, 'C')
        pts = _sag(a + F * 1.5 + Vector((0, 0, 3.0)), c + F2 * 1.5 + Vector((0, 0, 3.0)), 0.6, 4)
        _wire(b['cable'], pts, 0.03)
        r = rnd.random()
        if r < 0.12:
            add_box(b['red'], pts[2] - Vector((0, 0, 0.2)), (0.22, 0.22, 0.26))
        elif r < 0.2:
            add_box(b['lamp'], pts[2] - Vector((0, 0, 0.2)), (0.22, 0.22, 0.26))
        t = t2


def _stains(b, rnd):
    """Water stains down the rock below the terraces' lips and in streaks down the wall."""
    t0, t1 = CAVE_ARC
    for _ in range(70):
        t = rnd.uniform(t0 + 0.05, t1 - 0.05)
        ring, z, lip, back = rnd.choice(TIERS[:3] + (('F', 37.0, 9.5, 9.5),))
        p, T, n = _cave_frame(t)
        w = rnd.uniform(0.5, 2.2)
        length = rnd.uniform(3.0, 9.0)
        col = []
        for k in range(5):
            zz = z - length * k / 4
            c = p + n * (_wall_off(t, zz) - 0.6) + Vector((0, 0, zz + _warp(t, zz)))
            ww = w * (1 - 0.15 * k)
            col.append((c - T * ww / 2, c + T * ww / 2))
        vs = [(b['wet'].verts.new(l), b['wet'].verts.new(r)) for l, r in col]
        for (a0, a1), (c0, c1) in zip(vs, vs[1:]):
            b['wet'].faces.new((a0, a1, c1, c0))


def _carved(b, rnd):
    """Homes cut straight into the rock: rows of doors and windows in the cliff below ring C, over the
    works on the floor, with plank walkways and ladders down; more in the pillar; laundry strung out."""
    for z0, t_a, t_b, step in ((-8.6, -30, 215, 0.045), (-4.4, -10, 195, 0.05)):
        t = math.radians(t_a)
        run = []
        while t < math.radians(t_b):
            if rnd.random() < 0.3:
                if len(run) > 2:
                    _walkway(b, run, rnd)
                run = []
                t += step * rnd.uniform(1, 3)
                continue
            z = z0 + _warp(t, z0)
            p, T, n = _cave_frame(t)
            c = p + n * (_wall_off(t, z0 + 1.0) - 0.12) + Vector((0, 0, z))
            if rnd.random() < 0.55:
                _face(b['dark'], c + Vector((0, 0, 1.0)), T, -n, 0.9, 1.9)
            else:
                _face(b['dark'], c + Vector((0, 0, 1.4)), T, -n, 0.9, 0.8)
                if rnd.random() < 0.5:
                    _face(b['rust'], c + Vector((0, 0, 1.4)) - n * 0.03, T, -n, 0.95, 0.85)
            run.append((t, c))
            t += step * rnd.uniform(0.7, 1.4)
        if len(run) > 2:
            _walkway(b, run, rnd)
    # In the pillar: a few doors and a ladder.
    for k in range(9):
        a = rnd.uniform(-2.6, -0.6)
        z = rnd.uniform(-8.0, 6.0)
        c = Vector((96.0 + 4.0 * (z + 12.5) / 58 + 3.4 * math.cos(a), 63.0 + 6.0 * (z + 12.5) / 58 + 3.4 * math.sin(a), z))
        F = Vector((math.cos(a), math.sin(a), 0))
        _face(b['dark'], c, Vector((-F.y, F.x, 0)), F, 0.9, 1.6)


def _walkway(b, run, rnd):
    """Planks along the cliff under a row of cut homes, on brackets, and a ladder down to the floor."""
    for (ta, ca), (tb, cb) in zip(run, run[1:]):
        if (cb - ca).length > 6:
            continue
        _, _, na = _cave_frame(ta)
        d = cb - ca
        T = Vector((d.x, d.y, 0)).normalized()
        F = Vector((-T.y, T.x, 0))
        add_box(b['rust'] if rnd.random() < 0.5 else b['sheet'], (ca + cb) / 2 - na * 0.6 - Vector((0, 0, 0.05)), (d.length + 0.1, 1.1, 0.08), rot=_rot(T, F))
    t, c = run[len(run) // 2]
    _, T, n = _cave_frame(t)
    top, bot = c - n * 1.0, c - n * 1.6
    bot.z = _floor_z(bot.x, bot.y)
    for s in (-1, 1):
        add_cyl(b['sheet'], bot + T * (s * 0.28), top + T * (s * 0.28) + Vector((0, 0, 0.9)), 0.04, seg=4)
    if rnd.random() < 0.6:                            # washing on a line
        t2, c2 = run[min(len(run) - 1, len(run) // 2 + 2)]
        _, _, n2 = _cave_frame(t2)
        a, e = c - n * 0.9 + Vector((0, 0, 2.3)), c2 - n2 * 0.9 + Vector((0, 0, 2.3))
        pts = _sag(a, e, 0.3, 6)
        _wire(b['cable'], pts, 0.02)
        for p in pts[1:-1]:
            if rnd.random() < 0.7:
                d = (e - a).normalized()
                _face(b['plaster'] if rnd.random() < 0.6 else b['rust'], p - Vector((0, 0, 0.35)), d, Vector((-d.y, d.x, 0)), 0.5, 0.6)


def build_atrium(m, coll):
    """The balcony and stair down to ring C, and the refuge's cave: a cavern dug into the mountain with the
    city terraced up its walls. Ring C, level with the balcony, is the poorest: stacked shipping boxes,
    sealed and dark. Ring B and ring A above are better built; the levels above them are only lights, up a
    chimney toward the surface, with a faint warm glow at its top. Pipes, a duct and fans, tanks and pumps
    on the floor below, catwalks, ladders and cables strung across with a few bulbs. The near side, toward
    the camera, is cut away."""
    b0, b1 = BALCONY
    bm = bmesh.new()
    add_box(bm, ((b0 + b1) / 2, 0.7, DECK - 0.15), (b1 - b0, 3.4, 0.3))
    add_box(bm, ((b0 + b1) / 2, 0.7, DECK - 1.0), (b1 - b0 - 0.4, 2.6, 1.4))
    for k in range(9):                                    # the stair down to ring C's ledge
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

    rnd = random.Random(470)
    keys = ('plaster', 'sheet', 'rust', 'dark', 'barricade', 'cut', 'wet', 'cable', 'lamp', 'red', 'upper')
    b = {k: bmesh.new() for k in keys}
    # Where the terraces are interrupted: spurs of uncut rock, tunnel mouths, the painted letters.
    spurs = {'C': ((20, 7.0), (148, 8.0), (205, 6.0)), 'B': ((-22, 7.0), (112, 6.5), (178, 8.5)),
             'A': ((44, 8.0), (138, 7.5), (214, 7.0))}
    tunnels = {'C': ((-32, 3.6, 3.2), (62, 4.2, 3.6), (128, 3.6, 3.2), (226, 3.2, 3.0)),
               'B': ((18, 3.4, 3.0), (92, 4.6, 3.8), (192, 3.4, 3.0)),
               'A': ((66, 3.6, 3.2), (162, 3.6, 3.2))}
    letters = {'C': 104.0, 'B': 80.0, 'A': 112.0}
    blocked = {r: [(math.radians(a), s / 40 * 0.9) for a, s in spurs[r]] + [(math.radians(a), (w + 2.5) / 80) for a, w, _ in tunnels[r]]
               + [(math.radians(letters[r]), 0.11)] for r in 'CBA'}

    # The rock: the cavern, its floor, spurs and pillars; the buttress the tunnel comes through (left of the
    # balcony), the shelves of ring C either side of it, and the rock rising past the lane's end.
    rock = bmesh.new()
    _cave_shell(rock)
    _cave_floor(rock)
    for r in 'CBA':
        for i, (a, s) in enumerate(spurs[r]):
            lip, back, T, F = _ledge(math.radians(a), r)
            _lump(rock, back + (lip - back) * 0.45 + Vector((0, 0, s * 0.35)), (s * 0.8, s * 0.55, s * 0.75), i * 3.3 + ord(r))
    _pillar(rock, 96.0, 63.0, 4.2, 5.0, lean=(4.0, 6.0))
    _pillar(rock, 59.0, 58.0, 6.5, 2.0, z0=17.0, z1=47.0, taper=0.08, lean=(-3.0, 2.0))
    _lump(rock, Vector((92.0, 70.0, CAVE_FLOOR + 1.0)), (7.0, 5.0, 3.5), 9.0)          # falls of rock, never cleared
    _lump(rock, Vector((52.0, 48.0, CAVE_FLOOR + 0.5)), (6.0, 6.0, 3.0), 11.0)
    _cliff(rock, ((69.6, 1.45), (69.6, 3.4), (69.1, 6.0), (68.2, 8.6), (66.9, 11.5), (64.9, 14.5)),
           ((-13.5, -1.5), (-9.0, -0.4), (-4.0, 0.8), (1.0, 1.0), (6.0, 0.8), (12.0, 1.0), (18.0, 1.4), (25.0, 2.2),
            (31.0, 3.5), (36.0, 5.5), (41.0, 9.0)), -1, amp=0.3)
    _cliff(rock, ((64.6, 1.6), (66.4, 1.6), (68.2, 1.6), (69.7, 1.6)),            # the rock the tunnel is cut through
           ((3.95, 0.1), (7.0, 0.4), (10.5, 0.9), (14.0, 2.0)), -1, amp=0.25)
    _cliff(rock, ((72.0, 2.7), (71.8, 5.5), (71.0, 8.4), (69.6, 11.3), (67.6, 14.3)),   # ring C, left of the balcony
           ((-13.5, -2.0), (-8.0, -1.0), (-3.5, -0.2), (-0.03, 0.0)), -1, amp=0.12,
           top_back=((69.4, 2.5), (69.2, 5.2), (68.4, 8.0), (67.2, 10.8), (65.4, 13.8)))
    _cliff(rock, ((76.4, 2.05), (78.5, 2.1), (80.5, 2.3), (82.5, 2.9), (84.5, 3.9), (86.2, 5.5), (87.5, 7.6), (88.4, 10.2), (89.0, 13.0)),
           ((-13.5, -2.5), (-9.5, -1.4), (-5.5, -0.4), (-1.8, 0.4), (-0.03, 0.0)), 1, amp=0.12,
           top_back=((76.4, 1.22), (78.5, 1.22), (80.5, 1.22), (82.5, 1.22), (84.5, 1.22), (86.2, 1.22), (88.5, 1.25), (91.0, 2.5), (92.5, 6.0)))
    _cliff(rock, ((100.5, 1.6), (96.5, 2.6), (93.0, 4.6), (90.4, 7.4), (88.6, 10.8), (87.4, 14.5)),   # rock rising past the lane's end
           ((-13.5, -2.0), (-1.0, 0.0), (3.6, 0.0), (8.0, -0.6), (14.0, 0.4), (20.0, 1.2), (27.0, 2.0), (34.0, 4.0), (41.0, 8.0)), 1, amp=0.3)
    _cave_obj('AtriumRock', rock, [m['stone'], m['cut']], coll, smooth=True)

    # Tunnel mouths cut into the terraces' back walls, and the big one at the floor where the rails go in.
    for r in 'CBA':
        for a, w, h in tunnels[r]:
            _, back, T, F = _ledge(math.radians(a), r)
            _arch(b['dark'], back + F * 0.25, T, F, w, h)
            add_box(b['sheet'], back + F * 0.3 + Vector((0, 0, h + 0.25)), (w + 0.6, 0.3, 0.3), rot=_rot(T, F))
            if rnd.random() < 0.6:
                add_box(b['lamp'] if r != 'C' else b['red'], back + F * 0.5 + Vector((0, 0, h + 0.55)), (0.3, 0.3, 0.3), rot=_rot(T, F))
    t = math.radians(140)
    p, T, n = _cave_frame(t)
    c = p + n * (_wall_off(t, -9.0) - 1.2) + Vector((0, 0, CAVE_FLOOR - 0.3))
    _arch(b['dark'], c, T, -n, 8.0, 7.0, seg=8)
    for s in (-1, 1):
        add_box(b['sheet'], c + T * (s * 4.3) + Vector((0, 0, 3.5)), (0.5, 0.6, 7.0), rot=_rot(T, -n))
        _pipe(b['rust'], [c + T * (s * 0.8) - n * 0.5 + Vector((0, 0, 0.35)), c + T * (s * 0.8) - n * 22 + Vector((0, 0, 0.35))], 0.09, seg=4)

    _ring_c(b, rnd, blocked['C'])
    _ring_b(b, rnd, blocked['B'])
    lit = _ring_a(b, rnd, blocked['A'])
    _upper_lights(b, rnd)
    _risers(b, rnd)
    _floor_works(b, rnd)
    _crossings(b, rnd)
    _cables(b, rnd)
    _stains(b, rnd)
    _carved(b, rnd)
    # Ring C either side of the balcony: boxes on the shelves against the drop.
    for x0, y0, a, d, stack in ((87.0, 2.6, 1.571, 4.2, 2), (90.4, 2.6, 1.571, 2.45, 3), (89.6, 5.4, 1.87, 2.45, 1)):
        T = Vector((math.cos(a), math.sin(a), 0))
        F = Vector((-T.y, T.x, 0))
        for s in range(stack):
            dd = d if s < 2 else 2.45
            c = Vector((x0, y0, 2.62 * s)) + F * (dd / 2) + T * (0.3 * s * (1 if s % 2 else -1))
            _container(b, c, T, F, (2.45, dd, 2.6), rnd)
    add_box(b['red'], Vector((70.6, 10.4, 2.3)), (0.28, 0.28, 0.3))
    _barricade(b, Vector((69.0, 12.6, 0.0)), Vector((0.25, -0.97, 0)), Vector((0.97, 0.25, 0)), 3.2, rnd)

    # The fans: one at the floor in the far wall feeding the duct, one across the chimney's mouth. Their
    # blades are their own meshes, spinning about their local Z (the game's local Y).
    frame, fans = b['sheet'], []
    t = math.radians(FAN_T)
    p, _, n = _cave_frame(t)
    hub = p + n * (_wall_off(t, -5.5) - 1.4) + Vector((0, 0, -5.5 + _warp(t, -5.5)))
    blades = bmesh.new()
    _fan(blades, frame, hub, -n, 4.6, 5)
    for s in (-1, 1):
        add_box(frame, hub + Vector((0, 0, s * 5.2)), (11.0, 0.6, 0.6), rot=_rot(Vector((-n.y, n.x, 0)), -n))
    fans.append(('AtriumFanLow', blades, hub, -n))
    mx, my, ma, mb, mz = CHIMNEY[0]
    hub2 = Vector((mx, my, mz - 1.5))
    blades = bmesh.new()
    _fan(blades, frame, hub2, Vector((0, 0, 1)), 11.0, 4)
    for a in (0.3, 1.87):
        add_box(frame, hub2 + Vector((0, 0, 0.9)), (2 * ma + 6, 0.7, 0.7), rot=_rz(a))
    fans.append(('AtriumFanHigh', blades, hub2, Vector((0, 0, 1))))
    for name, bmf, h, axis in fans:
        ob = _cave_obj(name, bmf, [m['sheet']], coll)
        ob.location = h
        ob.rotation_mode = 'QUATERNION'
        ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(axis)
    # The glow of the upper levels at the chimney's top, and above it, a glimpse of the real sky.
    cx, cy, a, bb = _chimney_at(112.0)
    glow, sky = bmesh.new(), bmesh.new()
    ring_o = [glow.verts.new((cx + a * 1.1 * math.cos(t), cy + bb * 1.1 * math.sin(t), 112.0)) for t in [2 * math.pi * i / 24 for i in range(24)]]
    ring_i = [glow.verts.new((cx + a * 0.3 * math.cos(t), cy + bb * 0.3 * math.sin(t), 113.5)) for t in [2 * math.pi * i / 24 for i in range(24)]]
    for i in range(24):
        j = (i + 1) % 24
        glow.faces.new((ring_o[i], ring_i[i], ring_i[j], ring_o[j]))
    sky.faces.new([sky.verts.new((cx + a * 0.32 * math.cos(t), cy + bb * 0.32 * math.sin(t), 118.0)) for t in [-2 * math.pi * i / 16 for i in range(16)]])
    _cave_obj('AtriumUpperGlow', glow, [m['upperglow']], coll)
    _cave_obj('AtriumSkyGlimpse', sky, [m['skypanel']], coll)

    mats = {'plaster': m['plaster'], 'sheet': m['sheet'], 'rust': m['rust'], 'dark': m['dark'], 'barricade': m['barricade'],
            'cut': m['cut'], 'wet': m['wet'], 'cable': m['rubber'], 'lamp': m['ringlamp'], 'red': m['ringred'], 'upper': m['upperlights']}
    names = {'plaster': 'AtriumHomes', 'sheet': 'AtriumSheet', 'rust': 'AtriumRust', 'dark': 'AtriumOpenings',
             'barricade': 'AtriumBarricades', 'cut': 'AtriumCutStone', 'wet': 'AtriumWet', 'cable': 'AtriumCables',
             'lamp': 'AtriumLamps', 'red': 'AtriumRedLamps', 'upper': 'AtriumUpperLights'}
    for k in keys:
        if len(b[k].verts):                       # round things share their normals; boxes stay crisp
            _cave_obj(names[k], b[k], [mats[k]], coll, smooth=k in ('sheet', 'rust', 'cable'), sharp=150 if k == 'cable' else 50)
        else:
            b[k].free()
    if lit:
        bm = bmesh.new()
        add_box(bm, lit[0], (1.0, 0.06, 1.1), rot=_rot(lit[1], lit[2]))
        _cave_obj('AtriumLitWindow', bm, [m['homelight']], coll)
    # The ring letters, painted on the back wall of each terrace between the homes: one each.
    for ring, a in letters.items():
        mat = _image_material(f'RingLetter{ring}', os.path.join(TEX, f'ring_{ring}.png'), rough=0.9, alpha=True)
        _, back, T, F = _ledge(math.radians(a), ring)
        size = 4.6 if ring == 'C' else 5.0
        p = back + F * 0.35 + Vector((0, 0, size / 2 + 0.3))
        ang = math.atan2(F.y, F.x) + math.pi / 2
        _plane(f'AtriumRing{ring}', (size, size), p, mat, coll,
               rot=_rz(ang) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Rotation(rnd.uniform(-0.06, 0.06), 4, 'Z'))


def residential_doorway(m, coll):
    """DL-03's end wall gets its doorway: the lane runs on through it into DL-04."""
    gz = DECK
    bm = bmesh.new()
    # Only the back of the wall and the lintel: a post toward the camera would read as a wall he walks through.
    add_box(bm, (DOOR4_X, 0.7, gz + 1.6), (0.3, 0.5, 3.2))
    add_box(bm, (DOOR4_X, 0.2, gz + 2.35), (0.3, 1.5, 1.7))
    _obj('ResidentialWall', bm, [m['wall']], coll)
    bm = bmesh.new()
    add_box(bm, (DOOR4_X - 0.16, 0.44, gz + 0.75), (0.06, 0.06, 1.5))
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
        hands = {s: CARRY[s] + Vector((s * 0.1 * up, -0.04 * up + 0.04 * wheel * s, 0.17 * up + 0.05 * wheel))  # up and out in front, clear of the shoulders
                 for _, s in SIDES}
        tuck = track([(12, 0), (15, 0.06), (19, 0.06), (22, 0)], f)
        feet = {side: ((0, 0.01 * s, tuck), (-20 * tuck / 0.06, 0, 0)) for side, s in SIDES}
        roll = 4 * math.sin(f * 1.1) * track([(22, 0), (24, 1), (34, 0)], f)
        c.pose(frame, body=(0, 0.02 * up, -0.05 * buckle),
               body_rot=(track([(0, 0), (3, 10), (8, -10), (12, -12), (20, -4), (24, 6), (32, 0)], f), roll, 0),
               head=(track([(0, 0), (3, 30), (10, 26), (14, 6), (24, 14), (30, 24), (38, 10)], f),
                     track([(24, 0), (30, 8), (38, 4)], f), 0),
               antenna=[(spring(f, 0, -28 * (1 + 0.3 * i), decay=5, freq=1.3) + spring(f, 22, 14, decay=4), 0) for i in range(3)],
               hands=hands, hand_rot={'L': (-40 - 30 * up, 0, 20), 'R': (-40 - 30 * up, 0, -20)}, elbows={'L': up, 'R': up},
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
        body, rot = (0, 0, -0.01 * reach), (track([(0, 0), (12, 4), (36, 4), (44, 0)], f), 0, 0)
        # The ballast is past his reach: the wrist stays out to the right, elbow out, and the claw points
        # in to it so its tip does the patting (a reach for it with the wrist ran the arm through the pod).
        target = Vector((-0.13, -0.235, T4_TOP + 0.03 + 0.025 * tap))
        right = _reach({1: Vector((0, 0, 0)), -1: target}, body, rot, REST)[-1]
        hands = {1: CARRY[1], -1: dl01.reach_around(CARRY[-1], right, reach)}
        head = (track([(0, 0), (10, 18), (30, 16), (36, 8), (40, 20), (44, 4), (48, 0)], f),
                track([(8, 0), (14, 10), (30, 8), (38, 0)], f), 0)
        antenna = [(track([(0, 0), (12, 6), (30, 8), (40, -8), (48, -2)], f) + spring(f, 40, -8 * (1 + 0.3 * i), decay=4), 0)
                   for i in range(3)]
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands,
               hand_rot={'L': (-24, 6, 10), 'R': (-24 - 53 * reach, 0, -10 + 42 * reach)}, elbows={'R': min(1.0, 2 * reach)},
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
        hands = {1: CARRY[1], -1: dl01.window_reach(-1, CARRY[-1], reach)}     # elbow out, claw turned in to the glass
        head = (track([(0, 0), (12, -8), (30, -6), (40, 18), (56, 16), (64, 0), (68, 14), (74, -4), (84, 0)], f),
                track([(6, 0), (16, 8), (30, 6), (40, 0)], f),
                track([(6, 0), (18, 12), (28, -10), (36, 0)], f))
        antenna = [(track([(0, 0), (20, 10), (50, 18), (64, 16), (72, -10), (84, -6)], f) * (0.8 + 0.15 * i)
                    - spring(f, 70, 10 * (1 + 0.3 * i), decay=5), 0) for i in range(3)]
        c.pose(frame, body=(0, 0, track([(0, 0), (40, -0.01), (64, -0.01), (72, 0.004), (84, 0)], f)),
               body_rot=(track([(0, 0), (40, 6), (60, 6), (70, -2), (84, 0)], f), 0, 0), head=head, antenna=antenna,
               hands=hands, hand_rot={'L': (-24, 6, 10), 'R': dl01.window_claw(-1, reach)}, elbows={'R': reach},
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
        # Both claws on the window, elbows out; the left one a little lower.
        hands = {1: dl01.window_reach(1, CARRY[1], hold, target=dl01.WINDOW_WRIST[1] - Vector((0, 0, 0.015))),
                 -1: dl01.window_reach(-1, CARRY[-1], hold)}
        antenna = [(track([(0, 0), (20, -18), (88, -22), (110, 4), (136, 0), (160, -6)], f) * (0.8 + 0.15 * i)
                    + spring(f, 136, -8), 0) for i in range(3)]
        c.pose(frame, body=(0, -fwd * 0.6, track([(0, 0), (20, 0.008), (70, 0.008), (100, -0.012), (130, -0.012), (150, 0)], f)),
               body_rot=(track([(0, 0), (14, -3), (40, -8), (70, -6), (92, 6), (120, 6), (138, 0)], f), 0, 0),
               head=(pitch, tilt, yaw), feet=feet, hands=hands,
               hand_rot={'L': dl01.window_claw(1, hold, (-24, 6, 10)), 'R': dl01.window_claw(-1, hold)},
               elbows={'L': hold, 'R': hold}, claws={'L': CLAW_REST_OPEN['L'] * (1 - hold) + 4 * hold, 'R': track([(88, 1), (98, 5), (128, 5), (140, 1)], f)})
    c.done()


def add_clips(dl01, arm):
    clip_teeter(dl01, arm)
    clip_pat(dl01, arm)
    clip_hopscotch(dl01, arm)
    clip_look_back(dl01, arm)
    clip_awe(dl01, arm)
