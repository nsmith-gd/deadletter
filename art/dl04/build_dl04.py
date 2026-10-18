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
FAR_RAIL = (55.6, 55.75)             # the safety rail across the far landing (top DECK + 0.8)
BELT = (57.7, 64.6)                  # the returns belt, flush with the floor
TURN_X = 58.2                        # where crates leave the belt for the hatch
TUNNEL = (64.6, 70.0)
HOP = (66.4, 68.2)                   # the chalk hopscotch
BALCONY = (70.0, 74.6)
# The refuge's cave: a city in a chasm under the mountain, its far end lost in haze. Ring C's lip along each
# wall, near to far (x, y): the chasm opens ahead of the balcony and bends away to the right.
CHASM_LEFT = ((68.5, 12.0), (57.0, 22.0), (50.0, 40.0), (54.0, 68.0), (64.0, 98.0), (70.0, 132.0), (73.0, 172.0),
              (78.0, 215.0), (84.0, 262.0), (90.0, 312.0))
CHASM_RIGHT = ((90.5, 10.0), (104.0, 20.0), (117.0, 38.0), (112.0, 68.0), (102.0, 98.0), (106.0, 128.0), (118.0, 160.0),
               (133.0, 200.0), (148.0, 252.0), (162.0, 312.0))
CHASM_FLOOR = -48.0                  # the depths, under the mist
# The terraces, bottom up: ring, height, and the offsets of its lip and back wall into the rock. Ring C,
# level with the balcony, is the poorest; ring B holds the works; ring A is better built.
TIERS = (('C', 0.0, 0.0, 8.0), ('B', 12.0, 3.5, 11.0), ('A', 24.0, 7.5, 14.0))
# The rock between them (height, offset): each face leans out over the terrace below, so the homes sit in
# niches; above ring A the wall is drawn up to meet the roof.
CHASM_FACES = ((-48.0, -9.0), (-36.0, -6.0), (-25.0, -3.5), (-15.0, -1.5), (-6.0, -0.4), 'C', (2.5, 8.3), (5.0, 8.0),
               (7.5, 6.6), (10.2, 4.8), 'B', (14.5, 11.3), (17.5, 11.0), (20.0, 9.6), (22.3, 8.4), 'A', (27.0, 14.3),
               (30.0, 14.0), (36.0, 13.0), (44.0, 12.0), (54.0, 10.5), (66.0, 8.0), (80.0, 4.0), (96.0, -1.0), (112.0, -7.0))
# The upper city's tiers down the chasm: front edge (y), top (z), depth.
MESAS = ((150.0, 12.0, 32.0), (184.0, 28.0, 36.0), (222.0, 46.0, 72.0))
# Viaducts across the chasm: how far down it (y), deck height, width, spans.
VIADUCTS = ((80.0, -2.0, 7.0, 4), (104.0, -16.0, 5.0, 3), (120.0, 20.0, 6.0, 4), (174.0, 36.0, 6.0, 6))
HOME_U = 48.0                        # the one lit home window: ring A on the right wall, this far along, facing the balcony


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
    m['masonry'] = simple_material('AtriumMasonry', (0.15, 0.135, 0.115), 0.85)
    m['windowglow'] = emission_material('AtriumWindowGlow', (1.0, 0.6, 0.28), 2.5)
    m['hazelights'] = emission_material('AtriumHazeLights', (0.62, 0.76, 0.95), 1.5)
    m['mist'] = emission_material('AtriumMist', (0.32, 0.4, 0.48), 0.1)


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
    # The buffer stops at the pan's far end, folded down flat on their hinges (none of it over 0.03 high),
    # so the trolley rolls off the pan and on across the latched platform.
    bm = bmesh.new()
    for y in (-0.3, 0.3):
        add_box(bm, (px1 + 0.04, y, DECK + 0.006), (0.06, 0.12, 0.012))                 # the hinge plate
        add_cyl(bm, (px1 + 0.06, y - 0.05, DECK + 0.016), (px1 + 0.06, y + 0.05, DECK + 0.016), 0.012, seg=8)
        add_cyl(bm, (px1 + 0.07, y, DECK + 0.022), (px1 + 0.17, y, DECK + 0.022), 0.02, seg=10)   # the stop, lying flat
    _obj('G4PanStops', bm, [m['steel']], coll)
    bm = bmesh.new()
    for y in (-0.3, 0.3):
        add_cyl(bm, (px1 + 0.17, y, DECK + 0.022), (px1 + 0.2, y, DECK + 0.022), 0.024, seg=10)
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
    # The safety rail across the lane just beyond the shaft: 0.8 high, too high to climb from the platform,
    # climbable from the trolley's top. Steel posts, a sheet infill to 0.62 (nothing to crawl under), a mid
    # rail, and a yellow cap he climbs onto.
    fx0, fx1 = FAR_RAIL
    bm = bmesh.new()
    fy0, fy1 = -0.72, 0.9
    for y in (fy0 + 0.03, 0.1, fy1 - 0.03):
        add_box(bm, ((fx0 + fx1) / 2, y, DECK + 0.38), (0.07, 0.06, 0.76))
        add_box(bm, ((fx0 + fx1) / 2, y, DECK + 0.006), (fx1 - fx0 + 0.04, 0.12, 0.012))       # base plates
    add_box(bm, ((fx0 + fx1) / 2, (fy0 + fy1) / 2, DECK + 0.33), (0.012, fy1 - fy0 - 0.06, 0.62))   # infill sheet
    add_box(bm, ((fx0 + fx1) / 2, (fy0 + fy1) / 2, DECK + 0.45), (0.05, fy1 - fy0, 0.04))      # mid rail
    add_box(bm, ((fx0 + fx1) / 2 - 0.008, -0.3, DECK + 0.22), (0.004, 0.32, 0.22), mat=2)       # a patch on the sheet
    add_box(bm, ((fx0 + fx1) / 2, (fy0 + fy1) / 2, DECK + 0.78), (fx1 - fx0, fy1 - fy0, 0.04), mat=1)   # the cap
    _obj('G4FarRail', bm, [m['steel'], m['yellow'], m['rust']], coll)
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
# The refuge's cave: a city in a chasm. Far detail: flat and plain, cheaper the further it is.
# --------------------------------------------------------------------------

def _cave_d(p, z, rough=True):
    """How far the rock bulges out (or bites in) at a point of a wall's line and a height: big slow lumps,
    and on the faces, a rougher grain. Lip and back of a terrace share it, so the terraces stay level."""
    q = Vector((p.x * 0.045, p.y * 0.045, z * 0.06))
    d = 3.0 * noise.noise(q) + 1.2 * noise.noise(q * 3.1 + Vector((7.1, 3.3, 1.9)))
    if rough:
        d += 1.3 * noise.noise(q * 9.0 + Vector((2.2, 9.1, 4.4)))
        d += 0.5 * abs(noise.noise(Vector((q.x * 2.0, q.y * 2.0, z * 0.9))))      # strata
    return d


def _ceil_z(x, y):
    """The cave's roof: low over the balcony, rising away down the chasm."""
    return 50.0 + 0.27 * y + 6.0 * noise.noise(Vector((x * 0.03, y * 0.03, 5.1)))


def _cave_rows():
    """A wall's rows bottom up: (height, offset into the rock, rough, terrace) where terrace marks a lip row."""
    rows = []
    tiers = {t[0]: t for t in TIERS}
    for r in CHASM_FACES:
        if isinstance(r, str):
            _, z, lip, back = tiers[r]
            rows += [(z, lip, False, r), (z, back, False, None)]
        else:
            rows.append((r[0], r[1], True, None))
    return rows


def _tier(ring):
    return next(t for t in TIERS if t[0] == ring)


def _wall(poly, side, seed):
    """A chasm wall along ring C's lip (near to far); side -1 has the rock on the left of that line."""
    pts = [Vector((x, y, 0.0)) for x, y in poly]
    for _ in range(2):                                 # rounded off
        out = [pts[0]]
        for a, b in zip(pts, pts[1:]):
            out += [a.lerp(b, 0.25), a.lerp(b, 0.75)]
        pts = out + [pts[-1]]
    L = [0.0]
    for a, b in zip(pts, pts[1:]):
        L.append(L[-1] + (b - a).length)
    return {'pts': pts, 'L': L, 'len': L[-1], 'side': side, 'seed': seed}


def _wpos(W, u):
    pts, L = W['pts'], W['L']
    u = max(0.0, min(W['len'], u))
    i = 0
    while i < len(L) - 2 and L[i + 1] < u:
        i += 1
    f = (u - L[i]) / max(1e-6, L[i + 1] - L[i])
    return pts[i].lerp(pts[i + 1], f)


def _wframe(W, u):
    """The wall's line at u, its direction there (away down the chasm) and its normal into the rock."""
    p = _wpos(W, u)
    d = (_wpos(W, u + 3.0) - _wpos(W, u - 3.0)).normalized()
    return p, d, Vector((d.y, -d.x, 0.0)) * W['side']


def _wat_y(W, y):
    """How far along the wall it reaches a given depth into the chasm."""
    u = 0.0
    while u < W['len'] and _wpos(W, u).y < y:
        u += 1.0
    return u


def _wdz(W, u, ring):
    """Each terrace was cut in level stretches, a step of a metre or two between them. Ring C stays level
    near the balcony, where it meets the lane."""
    v = noise.noise(Vector((u * 0.025, W['seed'] + {'C': 0.5, 'B': 3.7, 'A': 7.9}[ring], 0.3)))
    dz = 1.2 * round(v * 3.0)
    return dz * smoothstep((u - 30) / 25) if ring == 'C' else dz


def _wwarp(W, u, z):
    zs = [(tz, _wdz(W, u, r)) for r, tz, _, _ in TIERS]
    if z <= zs[0][0]:
        return zs[0][1] * smoothstep((z - CHASM_FLOOR) / (zs[0][0] - CHASM_FLOOR))
    for (za, da), (zb, db) in zip(zs, zs[1:]):
        if z <= zb:
            return da + (db - da) * (z - za) / (zb - za)
    return zs[-1][1] * (1 - smoothstep((z - zs[-1][0]) / 6.0))


def _wpt(W, u, z, off, rough=True):
    """A point of the wall: the rows above ring A are drawn up to meet the roof."""
    p, _, n = _wframe(W, u)
    zz = z + _wwarp(W, u, z)
    if z > 30.0:
        zz = 30.0 + (z - 30.0) * (_ceil_z(p.x, p.y) - 26.0) / (CHASM_FACES[-1][0] - 30.0)
    return p + n * (off + _cave_d(p, z, rough)) + Vector((0, 0, zz))


def _woff(W, u, z):
    """The wall face's offset at u and height z (between its rows): to stand things just off it."""
    p, _, _ = _wframe(W, u)
    rows = _cave_rows()
    for (za, oa, ra, _), (zb, ob, rb, _) in zip(rows, rows[1:]):
        if za <= z <= zb and zb > za:
            f = (z - za) / (zb - za)
            return (oa + _cave_d(p, za, ra)) * (1 - f) + (ob + _cave_d(p, zb, rb)) * f
    return rows[-1][1]


def _wface(W, u, z, gap):
    """A point standing gap out from the wall's face at u and height z (up to ring A's roofs)."""
    p, _, n = _wframe(W, u)
    return p + n * (_woff(W, u, z) - gap) + Vector((0, 0, z + _wwarp(W, u, z)))


def _wledge(W, u, ring):
    """A terrace at u: its lip, its back wall, the way along the wall (x of a box) and out to the void."""
    _, z, lip, back = _tier(ring)
    p, _, n = _wframe(W, u)
    dd = _cave_d(p, z, False)
    up = Vector((0, 0, z + _wdz(W, u, ring)))
    F = -n
    return p + n * (lip + dd) + up, p + n * (back + dd) + up, Vector((F.y, -F.x, 0.0)), F


def _litp(z):
    """How likely a lamp or window is still lit at a height: the abandoned depths almost dark, the light
    growing up the levels to the upper city, where people still live."""
    table = ((-50.0, 0.01), (-5.0, 0.02), (4.0, 0.05), (14.0, 0.16), (26.0, 0.32), (40.0, 0.5), (60.0, 0.65))
    for (za, pa), (zb, pb) in zip(table, table[1:]):
        if z <= zb:
            return pa + (pb - pa) * max(0.0, (z - za) / (zb - za))
    return table[-1][1]


def _blocked(u, spans):
    return any(abs(u - c) < h for c, h in spans)


def _rot(T, F):
    """Local x along T, local y along F (out toward the void), z up."""
    return Matrix(((T.x, F.x, 0, 0), (T.y, F.y, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)))


def _face(bm, c, T, F, w, h, mat=0, up=Vector((0, 0, 1))):
    """A flat quad centred at c, w along T and h along up, facing F."""
    hw, hh = T * (w / 2), up * (h / 2)
    f = bm.faces.new([bm.verts.new(c + a) for a in (-hw - hh, -hw + hh, hw + hh, hw - hh)])
    f.material_index = mat
    f.normal_update()
    if f.normal.dot(F) < 0:
        f.normal_flip()
    return f


def _arch(bm, c, T, F, w, h, seg=6):
    """An arched opening, c at the middle of its sill, facing F."""
    r = w / 2
    pts = [c - T * r, c + T * r]
    for k in range(seg + 1):
        a = math.pi * k / seg
        pts.append(c + T * (r * math.cos(a)) + Vector((0, 0, max(0.0, h - r) + r * math.sin(a))))
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


def _chasm_wall(bm, W):
    """A wall of the chasm, from the misty depths up to the roof, with its terraces cut (material 1)."""
    us, u = [], 0.0
    while u < W['len']:
        us.append(u)
        u += 2.5 + 0.02 * u
    us.append(W['len'])
    rows = _cave_rows()
    grid = [[bm.verts.new(_wpt(W, u, z, off, rough)) for u in us] for z, off, rough, _ in rows]
    _grid_faces(bm, grid, lambda r, c: 1 if rows[r][3] else 0, flip=W['side'] < 0)


def _roof(bm):
    """The roof over the chasm, barely seen: a rough sheet facing down."""
    xs = [25.0 + 6.0 * i for i in range(30)]
    ys = [-12.0 + 9.0 * j for j in range(43)]
    grid = [[bm.verts.new((x, y, _ceil_z(x, y))) for x in xs] for y in ys]
    _grid_faces(bm, grid)


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


def _stalactite(bm, x, y, r0, length, seed):
    """A spike of rock hanging from the roof."""
    z1 = _ceil_z(x, y) + 2.0
    rows = []
    for k in range(6):
        u = k / 5
        z = z1 - length * (1 - u)
        r = r0 * (0.06 + 0.94 * u ** 0.8)
        cx = x + 0.15 * length * noise.noise(Vector((seed, u * 2.0, 1.0)))
        ring = []
        for i in range(7):
            a = 2 * math.pi * i / 7
            j = 1 + 0.35 * noise.noise(Vector((math.cos(a) * 1.4 + seed, math.sin(a) * 1.4, u * 2)))
            ring.append(bm.verts.new(Vector((cx + r * j * math.cos(a), y + r * j * math.sin(a), z))))
        rows.append(ring)
    _grid_faces(bm, rows, cyclic=True, flip=True)
    bm.faces.new(rows[0][::-1])


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


def _house(b, c, T, F, w, d, floors, rnd, mat, lit=0.0):
    """A built home: plaster or sheet walls, a slab roof (now and then a tank or a flue on it), windows in
    a row on each floor, dark."""
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
                _face(b['glow'] if rnd.random() < lit else b['dark'], fc + T * u + Vector((0, 0, 3.0 * f + 1.6)), T, F, 0.95, 1.0)


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


def _hall(b, c, T, F, w, h, lit, rnd):
    """A workshop hall cut into the rock: a dressed-stone frame round an arched mouth, warm-lit inside
    behind its window bars when the works still run, dark and shuttered when not."""
    for s in (-1, 1):
        add_box(b['cut'], c + T * (s * (w / 2 + 0.3)) + Vector((0, 0, h / 2)), (0.6, 0.7, h), rot=_rot(T, F))
    add_box(b['cut'], c + Vector((0, 0, h + 0.35)), (w + 1.2, 0.7, 0.7), rot=_rot(T, F))
    if lit:
        _arch(b['glow'], c, T, F, w, h)
        fc = c + F * 0.12
        for i in range(1, 4):
            _face(b['dark'], fc + T * ((i / 4 - 0.5) * w) + Vector((0, 0, h * 0.45)), T, F, 0.14, h * 0.9)
        _face(b['dark'], fc + Vector((0, 0, h * 0.42)), T, F, w * 0.98, 0.14)
        if rnd.random() < 0.5:                       # something parked in the mouth, against the light
            add_box(b['rust'] if rnd.random() < 0.5 else b['sheet'], c + F * 0.9 + T * rnd.uniform(-w / 4, w / 4) + Vector((0, 0, 0.6)), (1.6, 1.2, 1.2), rot=_rot(T, F))
    else:
        _arch(b['dark'], c, T, F, w, h)
        _face(b['rust'] if rnd.random() < 0.5 else b['sheet'], c + F * 0.06 + Vector((0, 0, h * 0.35)), T, F, w * 0.95, h * 0.7)


def _gallery(b, lip, T, F, length, lamp, rnd, out=1.6):
    """A steel gallery cantilevered off a terrace's lip: deck, rail, a post, maybe a lamp."""
    c = lip + F * (out / 2 - 0.2)
    add_box(b['sheet'], c - Vector((0, 0, 0.08)), (length + 0.05, out + 0.4, 0.14), rot=_rot(T, F))
    add_box(b['sheet'], lip + F * (out - 0.2) + Vector((0, 0, 1.05)), (length + 0.05, 0.06, 0.06), rot=_rot(T, F))
    post = lip + F * (out - 0.2) - T * (length / 2)
    add_box(b['sheet'], post + Vector((0, 0, 0.55 + (0.7 if lamp else 0))), (0.07, 0.07, 1.1 + (1.4 if lamp else 0)), rot=_rot(T, F))
    if lamp:
        add_box(b['lamp'], post + F * 0.25 + Vector((0, 0, 2.45)), (0.3, 0.3, 0.3), rot=_rot(T, F))
    add_box(b['sheet'], c + F * (out / 2) - T * (length / 2) - Vector((0, 0, 0.8)), (0.1, 0.1, 1.9), rot=_rot(T, F) @ Matrix.Rotation(0.7, 4, 'X'))


def _ring_c(b, W, rnd, blocked):
    """Ring C, the poorest, level with the balcony: shipping boxes stacked in the niches, homes cut into
    the rock behind dark doors and shutters, barricades and tape; a few red lamps, fewer warm ones."""
    u = 3.0
    k = 0
    while u < 150.0:
        if _blocked(u, blocked):
            u += 1.5
            continue
        lip, back, T, F = _wledge(W, u, 'C')
        depth = (back - lip).length
        k += 1
        near = u < 80
        if k % 7 == 0:
            _barricade(b, (lip + back) / 2, T, F, depth + 0.6, rnd)
            add_box(b['red'], lip + F * 0.1 + Vector((0, 0, 2.8)), (0.3, 0.3, 0.3))
            u += 3.0
            continue
        r = rnd.random()
        if near and r < 0.5:
            w = 6.1 if rnd.random() < 0.6 else 2.45
            d = 2.45 if w > 3 else min(6.0, depth - 1.0)
            c = back + F * (d / 2 + 0.15) - Vector((0, 0, 0.2))
            _container(b, c, T, F, (w, d, 2.6), rnd)
            if rnd.random() < 0.55:
                _container(b, c + T * rnd.uniform(-0.6, 0.6) + Vector((0, 0, 2.62)) - F * 0.3, T, F, (min(w, 2.45 + 3.6 * rnd.random()), 2.45, 2.5), rnd)
            if rnd.random() < 0.4:
                rp = c + F * (d / 2 + 0.75) + Vector((0, 0, 2.35))
                add_box(b['rust'], rp, (w + 0.4, 1.6, 0.05), rot=_rot(T, F) @ Matrix.Rotation(-0.2, 4, 'X'))
            step = w + rnd.uniform(0.4, 2.0)
        elif near and r < 0.62:                       # a works still running, among the sealed homes
            w = rnd.uniform(4.5, 7.0)
            _hall(b, back + F * 0.3, T, F, w, rnd.uniform(3.6, 4.6), rnd.random() < _litp(back.z), rnd)
            step = w + rnd.uniform(1.0, 2.5)
        else:
            c = back + F * 0.25
            _arch(b['dark'], c, T, F, 2.2, 2.8, seg=4)
            _face(b['rust'] if rnd.random() < 0.5 else b['sheet'], c + F * 0.04 + T * 2.1 + Vector((0, 0, 1.6)), T, F, 1.2, 0.9)
            if rnd.random() < 0.3:
                add_box(b['sheet'], c + F * 1.4 + T * rnd.uniform(-1, 1) + Vector((0, 0, 0.45)), (1.0, 0.8, 0.9), rot=_rot(T, F))
            step = rnd.uniform(4.5, 7.0)
        if near:
            ml, _, mT, mF = _wledge(W, u + step / 2, 'C')
            add_box(b['sheet'], ml - mF * 0.2 + Vector((0, 0, 1.0)), (step, 0.05, 0.05), rot=_rot(mT, mF))
            add_box(b['sheet'], lip - F * 0.2 + Vector((0, 0, 0.5)), (0.06, 0.06, 1.0), rot=_rot(T, F))
        if rnd.random() < 0.08:                      # a failing lamp, mostly the red ones
            add_box(b['lamp'] if rnd.random() < 0.25 else b['red'], lip - F * 0.3 + Vector((0, 0, 2.4)), (0.28, 0.28, 0.3))
        u += step


def _ring_b(b, W, rnd, blocked):
    """Ring B: the works. Halls cut into the rock, most still lit, a gallery on their roofs now and then,
    crates, a steel gallery along the lip with work lamps; further off, just the lit mouths and lamps."""
    u = 4.0
    k = 0
    while u < 220.0:
        if _blocked(u, blocked):
            u += 1.5
            continue
        lip, back, T, F = _wledge(W, u, 'B')
        k += 1
        if u < 120:
            w, h = rnd.uniform(5.5, 9.0), rnd.uniform(4.2, 6.2)
            _hall(b, back + F * 0.3, T, F, w, h, rnd.random() < _litp(back.z), rnd)
            if rnd.random() < 0.4:                   # a gallery above the hall, and its own row of lit windows
                g = back + F * 1.0 + Vector((0, 0, h + 1.0))
                add_box(b['sheet'], g, (w + 1.5, 2.0, 0.14), rot=_rot(T, F))
                add_box(b['sheet'], g + F * 0.95 + Vector((0, 0, 1.0)), (w + 1.5, 0.05, 0.05), rot=_rot(T, F))
                for i in range(3):
                    _face(b['glow'] if rnd.random() < _litp(back.z + h + 2.4) else b['dark'], back + F * 0.32 + T * ((i - 1) * w / 3) + Vector((0, 0, h + 2.4)), T, F, 1.1, 1.2)
            if rnd.random() < 0.5:
                for i in range(rnd.randint(1, 3)):
                    s = rnd.uniform(0.8, 1.5)
                    add_box(b['rust' if rnd.random() < 0.5 else 'sheet'], lip - F * rnd.uniform(1.0, 2.5) + T * rnd.uniform(-w / 2, w / 2) + Vector((0, 0, s / 2)), (s, s, s), rot=_rot(T, F))
            step = w + rnd.uniform(1.2, 3.0)
            gl, _, gT, gF = _wledge(W, u + step / 2 - w / 2, 'B')
            _gallery(b, gl, gT, gF, step, rnd.random() < 2 * _litp(gl.z), rnd)
        else:
            if rnd.random() < 0.6:
                _arch(b['glow'] if rnd.random() < _litp(back.z) else b['dark'], back + F * 0.3, T, F, rnd.uniform(4, 7), rnd.uniform(3.5, 5.5), seg=4)
            if rnd.random() < 2 * _litp(lip.z):
                _face(b['lamp'], lip - F * 0.3 + Vector((0, 0, 2.2)), T, F, 0.45, 0.45)
            step = rnd.uniform(8.0, 13.0)
        u += step


def _ring_a(b, W, rnd, blocked, home=None):
    """Ring A: better built. Plaster homes in rows, their windows dark; lamps along the lip. With home,
    the one lit window, on the first house past that far along."""
    u = 6.0
    k = 0
    lit = None
    while u < 240.0:
        if _blocked(u, blocked):
            u += 1.5
            continue
        lip, back, T, F = _wledge(W, u, 'A')
        k += 1
        if u < 170:
            w, d = rnd.uniform(6.0, 8.5), rnd.uniform(4.5, 5.5)
            c = back + F * (d / 2 + 0.1) - Vector((0, 0, 0.1))
            _house(b, c, T, F, w, d, 2 if rnd.random() < 0.75 else 3, rnd, b['plaster'] if rnd.random() < 0.8 else b['sheet'], 0.5 * _litp(c.z))
            if home is not None and lit is None and u > home:
                lit = (c + F * (d / 2 + 0.05) + T * (w * 0.25) + Vector((0, 0, 4.6)), T, F)
            add_box(b['cut'], lip - F * 0.3 + Vector((0, 0, 0.5)), (w + 0.8, 0.25, 1.0), rot=_rot(T, F))
            if rnd.random() < 1.6 * _litp(lip.z):
                add_box(b['lamp'], lip - F * 0.1 + Vector((0, 0, 2.6)), (0.35, 0.35, 0.35), rot=_rot(T, F))
                add_box(b['sheet'], lip - F * 0.3 + Vector((0, 0, 1.3)), (0.08, 0.08, 2.6), rot=_rot(T, F))
            step = w + rnd.uniform(0.3, 1.5)
        else:
            for i in range(3):
                if rnd.random() < _litp(back.z + 6):
                    _face(b['glow'], back + F * 0.3 + T * (i * 2.4) + Vector((0, 0, rnd.choice((1.6, 4.6)))), T, F, 1.2, 1.4)
            if rnd.random() < 1.6 * _litp(lip.z):
                _face(b['lamp'], lip - F * 0.3 + Vector((0, 0, 2.4)), T, F, 0.6, 0.6)
            step = rnd.uniform(9.0, 13.0)
        u += step
    return lit


def _wall_lights(b, W, rnd):
    """The levels above ring A, up the walls toward the roof: lit windows and lamps, more of them the
    further down the chasm, where the city climbs."""
    u = 70.0
    while u < W['len'] - 5:
        z = rnd.uniform(32.0, 30.0 + 0.25 * (u + 40))
        p, _, n = _wframe(W, u)
        if z < _ceil_z(p.x, p.y) - 12:
            q = p + n * (_cave_d(p, 30.0, False) + 9.0) + Vector((0, 0, z))
            T = Vector((-n.y, n.x, 0.0))
            for i in range(rnd.randint(1, 4)):
                if rnd.random() < 0.4 + _litp(z):
                    _face(b['glow'] if rnd.random() < 0.6 + 0.3 * _litp(z) else b['haze'], q + T * (i * 2.2), T, -n, 1.2, 1.5)
        u += rnd.uniform(3.0, 7.0)


def _low_galleries(b, W, u0, u1, rnd):
    """Below ring C, down the cliff toward the mist: stacked steel galleries along the face, doorways cut
    behind them (some lit, the works below), lamps, and ladders between."""
    for z in (-7.0, -14.0, -21.0):
        u = u0 + rnd.uniform(0, 6)
        while u < u1:
            run = rnd.uniform(10.0, 22.0)
            pts = []
            v = u
            while v < min(u + run, u1):
                pts.append((v, _wface(W, v, z, 0.2)))
                v += 3.0
            for (va, a), (vb, c) in zip(pts, pts[1:]):
                d = c - a
                T = Vector((d.x, d.y, 0)).normalized()
                F = -_wframe(W, va)[2]
                if T.cross(F).z < 0:
                    T = -T
                add_box(b['sheet'], (a + c) / 2 + F * 0.9, (d.length + 0.05, 1.8, 0.12), rot=_rot(T, F))
                add_box(b['sheet'], (a + c) / 2 + F * 1.75 + Vector((0, 0, 1.0)), (d.length + 0.05, 0.05, 0.05), rot=_rot(T, F))
                if rnd.random() < 0.45:
                    _arch(b['glow'] if rnd.random() < _litp(z) else b['dark'], a + F * 0.05, T, F, 1.6, 2.4, seg=3)
                if rnd.random() < 0.04:                # a failing lamp
                    add_box(b['red'] if rnd.random() < 0.5 else b['lamp'], a + F * 1.7 + Vector((0, 0, 2.2)), (0.26, 0.26, 0.26), rot=_rot(T, F))
            if len(pts) > 2 and z > -21:
                q = pts[len(pts) // 2][1]
                F = -_wframe(W, pts[len(pts) // 2][0])[2]
                for s in (-0.3, 0.3):
                    T = Vector((F.y, -F.x, 0))
                    add_cyl(b['sheet'], q + F * 1.4 + T * s, q + F * 1.4 + T * s + Vector((0, 0, -7.0)), 0.04, seg=4)
            u += run + rnd.uniform(4.0, 12.0)


def _lift_tower(b, base, top_z, T, F, rnd):
    """A lattice lift tower rising out of the mist, its cage lit, its head wheel and cables."""
    zb = CHASM_FLOOR + 6.0
    for sx in (-1, 1):
        for sy in (-1, 1):
            q = base + T * (sx * 1.6) + F * (sy * 1.6)
            add_box(b['sheet'], Vector((q.x, q.y, (zb + top_z) / 2)), (0.3, 0.3, top_z - zb), rot=_rot(T, F))
    z = zb + 4.0
    while z < top_z:
        for s in (-1, 1):
            add_box(b['sheet'], base + F * (s * 1.6) + Vector((0, 0, z)), (3.4, 0.12, 0.12), rot=_rot(T, F))
            add_box(b['sheet'], base + T * (s * 1.6) + Vector((0, 0, z)), (0.12, 3.4, 0.12), rot=_rot(T, F))
        z += 4.0
    add_box(b['sheet'], base + Vector((0, 0, top_z + 0.4)), (4.0, 4.0, 0.4), rot=_rot(T, F))
    add_torus(b['sheet'], base + Vector((0, 0, top_z + 2.2)), T, 1.6, 0.12, seg=16, rseg=4)
    cz = top_z - 9.0
    add_box(b['rust'], base + Vector((0, 0, cz + 0.05)), (2.2, 2.2, 0.1), rot=_rot(T, F))
    add_box(b['red'], base + F * 2.1 + Vector((0, 0, top_z + 0.9)), (0.3, 0.3, 0.3), rot=_rot(T, F))
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_box(b['sheet'], base + T * (sx * 1.15) + F * (sy * 1.15) + Vector((0, 0, cz + 1.4)), (0.12, 0.12, 2.9), rot=_rot(T, F))
    add_box(b['sheet'], base + Vector((0, 0, cz + 2.95)), (2.5, 2.5, 0.2), rot=_rot(T, F))
    _wire(b['cable'], [base + Vector((0, 0, cz + 3.0)), base + Vector((0, 0, top_z + 2.2))], 0.04)


def _crane(b, base, T, F, rnd):
    """A jib crane on a cantilevered platform: mast, jib out over the chasm, a load on its hook."""
    add_box(b['sheet'], base + Vector((0, 0, 6.0)), (0.9, 0.9, 12.0), rot=_rot(T, F))
    add_box(b['rust'], base + F * 6.0 + Vector((0, 0, 11.6)), (0.7, 16.0, 0.9), rot=_rot(T, F))
    add_box(b['sheet'], base - F * 3.0 + Vector((0, 0, 11.3)), (1.8, 3.0, 1.4), rot=_rot(T, F))
    for s in (-1, 1):
        _wire(b['cable'], [base + Vector((0, 0, 14.5)), base + F * (6 + 7.5 * s) + Vector((0, 0, 12.0))], 0.03)
    hook = base + F * 11.5
    _wire(b['cable'], [hook + Vector((0, 0, 11.2)), hook + Vector((0, 0, 4.0))], 0.03)
    add_box(b['rust'], hook + Vector((0, 0, 3.0)), (2.2, 1.6, 1.6), rot=_rot(T, F))
    add_box(b['lamp'], base + F * 13.5 + Vector((0, 0, 11.0)), (0.35, 0.35, 0.35), rot=_rot(T, F))


def _platform(b, lip, T, F, w, out, rnd, crane=False):
    """A steel platform cantilevered out over the chasm on struts, crates and a lamp on it."""
    c = lip + F * (out / 2 - 0.5)
    add_box(b['sheet'], c - Vector((0, 0, 0.12)), (w, out + 1.0, 0.25), rot=_rot(T, F))
    for s in (-1, 1):
        a = lip + T * (s * (w / 2 - 0.4)) - Vector((0, 0, 4.5)) + F * 0.3
        e = lip + T * (s * (w / 2 - 0.4)) + F * (out - 0.6) - Vector((0, 0, 0.2))
        add_cyl(b['sheet'], a, e, 0.14, seg=4)
        add_box(b['sheet'], lip + T * (s * w / 2) + F * (out / 2 - 0.5) + Vector((0, 0, 1.05)), (0.05, out + 1.0, 0.05), rot=_rot(T, F))
    add_box(b['sheet'], lip + F * (out - 0.05) + Vector((0, 0, 1.05)), (w, 0.05, 0.05), rot=_rot(T, F))
    for i in range(rnd.randint(2, 4)):
        s = rnd.uniform(0.9, 1.6)
        add_box(b['rust' if rnd.random() < 0.5 else 'sheet'], c + T * rnd.uniform(-w / 3, w / 3) + F * rnd.uniform(-out / 4, out / 4) + Vector((0, 0, s / 2)), (s, s * 1.2, s), rot=_rot(T, F))
    if rnd.random() < 2.5 * _litp(lip.z):
        add_box(b['lamp'], lip + F * (out - 0.1) + T * (w / 2) + Vector((0, 0, 2.2)), (0.32, 0.32, 0.32), rot=_rot(T, F))
    if crane:
        _crane(b, c - T * (w / 3), T, F, rnd)


def _viaduct(b, WL, WR, y, z, width, spans, rnd):
    """A heavy arched viaduct across the chasm: piers down into the mist, an arch in each span, a
    parapet with lamps along it."""
    ul, ur = _wat_y(WL, y), _wat_y(WR, y)
    pl, _, nl = _wframe(WL, ul)
    pr, _, nr = _wframe(WR, ur)
    a = pl + nl * 5.0
    e = pr + nr * 5.0
    a.z = e.z = 0.0
    d = e - a
    L = d.length
    T = d.normalized()
    F = Vector((-T.y, T.x, 0.0))
    stone = b['masonry']
    pw = L / spans * 0.16
    piers = [a + T * (L * i / spans) for i in range(spans + 1)]
    top = z + 1.4
    zb = CHASM_FLOOR + 4.0
    for i, p in enumerate(piers):
        if 0 < i < spans:
            add_box(stone, p + Vector((0, 0, (zb + top) / 2)), (pw, width + 1.0, top - zb), rot=_rot(T, F))
    # Each span: the spandrel above its arch, extruded through the bridge's width.
    for p0, p1 in zip(piers, piers[1:]):
        u0, u1 = p0 + T * (pw / 2), p1 - T * (pw / 2)
        r = (u1 - u0).length / 2
        mid = (u0 + u1) / 2
        spring = z - 1.0 - r
        prof = [(u0, top), (u1, top), (u1, spring)]
        for k in range(1, 8):
            ang = math.pi * k / 8
            prof.append((mid + T * (r * math.cos(ang)), spring + r * math.sin(ang)))
        prof.append((u0, spring))
        sides = []
        for s in (-1, 1):
            sides.append([stone.verts.new(q + F * (s * width / 2) + Vector((0, 0, zz))) for q, zz in prof])
        stone.faces.new(sides[0][::-1])
        stone.faces.new(sides[1])
        n = len(prof)
        for i in range(n):
            j = (i + 1) % n
            stone.faces.new((sides[0][i], sides[0][j], sides[1][j], sides[1][i]))
    for s in (-1, 1):
        add_box(stone, a + T * (L / 2) + F * (s * (width / 2 - 0.2)) + Vector((0, 0, top + 0.5)), (L, 0.4, 1.0), rot=_rot(T, F))
        x = 4.0
        while x < L - 2:
            if rnd.random() < 1.5 * _litp(z):
                add_box(b['glow'], a + T * x + F * (s * (width / 2 - 0.2)) + Vector((0, 0, top + 2.6)), (0.5, 0.5, 0.5), rot=_rot(T, F))
                add_box(b['sheet'], a + T * x + F * (s * (width / 2 - 0.2)) + Vector((0, 0, top + 1.8)), (0.1, 0.1, 1.6), rot=_rot(T, F))
            x += 9.0 + rnd.uniform(-1, 2)


def _catwalk(b, WL, WR, y, z, rnd):
    """A steel catwalk across the chasm, hung from the roof."""
    pl, _, nl = _wframe(WL, _wat_y(WL, y))
    pr, _, nr = _wframe(WR, _wat_y(WR, y + 6))
    a, e = pl + nl * 3.0 + Vector((0, 0, z)), pr + nr * 3.0 + Vector((0, 0, z))
    d = e - a
    T = Vector((d.x, d.y, 0)).normalized()
    F = Vector((-T.y, T.x, 0.0))
    add_box(b['sheet'], (a + e) / 2, (d.length, 1.4, 0.12), rot=_rot(T, F))
    for s in (-1, 1):
        add_box(b['sheet'], (a + e) / 2 + F * (s * 0.68) + Vector((0, 0, 1.0)), (d.length, 0.05, 0.05), rot=_rot(T, F))
    add_box(b['rust'], (a + e) / 2 - Vector((0, 0, 0.8)), (d.length, 0.5, 1.4), rot=_rot(T, F))     # its girder
    x = 6.0
    while x < d.length - 3:
        p = a.lerp(e, x / d.length)
        if rnd.random() < 2 * _litp(z):
            add_box(b['glow'], p + F * 0.7 + Vector((0, 0, 1.4)), (0.35, 0.35, 0.35), rot=_rot(T, F))
        x += 10.0


def _falls(b, top, F, width, rnd):
    """A fall of water from the cliff into the misty depths: a pale ribbon, leaning out as it drops."""
    pts = []
    zs = [top.z - (top.z - CHASM_FLOOR - 20.0) * (k / 9) ** 1.3 for k in range(10)]
    T = Vector((F.y, -F.x, 0.0))
    for k, z in enumerate(zs):
        out = 0.6 * math.sqrt(max(0.0, top.z - z))
        w = width * (1 + 0.6 * k / 9)
        c = Vector((top.x, top.y, z)) + F * out
        pts.append((c - T * w / 2, c + T * w / 2))
    vs = [(b['mist'].verts.new(l), b['mist'].verts.new(r)) for l, r in pts]
    for (a0, a1), (c0, c1) in zip(vs, vs[1:]):
        f = b['mist'].faces.new((a0, a1, c1, c0))
        f.normal_update()
        if f.normal.dot(F) < 0:
            f.normal_flip()


def _mist(b, WL, WR):
    """Mist pooling in the depths: low sheets between the walls, higher toward the far end."""
    rows = []
    y = 4.0
    while y < 330.0:
        pl = _wpos(WL, _wat_y(WL, y)) if y < WL['pts'][-1].y else WL['pts'][-1]
        pr = _wpos(WR, _wat_y(WR, y)) if y < WR['pts'][-1].y else WR['pts'][-1]
        z = -24.0 + 10.0 * min(1.0, y / 250.0)
        rows.append([b['mist'].verts.new(Vector((pl.x - 4.0, y, z))), b['mist'].verts.new(Vector((pr.x + 4.0, y, z)))])
        y += 12.0
    for (a0, a1), (c0, c1) in zip(rows, rows[1:]):
        b['mist'].faces.new((a0, a1, c1, c0))


def _mesa(rock, b, WL, WR, y0, top, depth, tier, rnd, avoid=None):
    """A tier of the upper city: a rock step across the chasm, its face carved with lit arches, its top cut
    flat and built on, grander the higher it is."""
    ul, ur = _wat_y(WL, y0), _wat_y(WR, y0)
    xl, xr = _wpos(WL, ul).x + 16.0 - 4.0 * tier, _wpos(WR, ur).x + 8.0
    n = 12
    lip = [(xl + (xr - xl) * i / n, y0 + 4.0 * noise.noise(Vector((i * 0.7, top, 0.2)))) for i in range(n + 1)]
    back = [(x, y + depth) for x, y in lip]
    _cliff(rock, lip, ((CHASM_FLOOR, -4.0), (-20.0, -2.0), (top - 18.0, 0.0), (top - 6.0, 0.5), (top, 0.0)), -1,
           top_back=back, amp=0.5)
    F = Vector((0, -1.0, 0.0))
    T = Vector((-1.0, 0.0, 0.0))
    # Lit arches and lamps in its face.
    for i in range(int((xr - xl) / 7)):
        x = xl + 6 + i * 7 + rnd.uniform(-1, 1)
        for zz in (top - 7.0, top - 15.0):
            if zz > -18 and rnd.random() < 0.6:
                _arch(b['glow'] if rnd.random() < 0.15 + _litp(zz) else b['dark'], Vector((x, y0 - 3.6, zz)), T, F, 3.0, 4.0, seg=4)
    # The city on top: rows of lots back from the edge.
    yy = y0 + 6.0
    dpt = 8.0
    while yy < y0 + depth - 6:
        x = xl + 10.0
        while x < xr - 10.0:
            w = rnd.uniform(7.0, 13.0) + 2 * tier
            dpt = rnd.uniform(7.0, 11.0)
            h = rnd.uniform(6.0, 12.0) + 6.0 * tier + (yy - y0) * 0.1
            c = Vector((x + w / 2, yy + dpt / 2, top))
            r = rnd.random()
            if avoid and abs(c.x - avoid.x) < 38 and abs(c.y - avoid.y) < 24:
                x += w + 2.0
                continue
            if tier >= 1 and r < 0.12:
                _dome_house(b, c, min(w, dpt) / 2, h * 0.6, rnd)
            elif tier >= 1 and r < 0.26:
                _tower(b, c, rnd.uniform(2.2, 3.5), h * rnd.uniform(1.8, 2.6), rnd)
            elif r < 0.33:
                add_cyl(b['masonry'], c, c + Vector((0, 0, h * 2.4 + 8)), 0.9 + 0.2 * tier, seg=8)      # a chimney
                add_box(b['lamp'], c + Vector((0, 0, h * 2.4 + 8.4)), (0.7, 0.7, 0.4))
            else:
                _block(b, c, w, dpt, h, tier, rnd)
            x += w + rnd.uniform(1.0, 4.0)
        yy += dpt + rnd.uniform(2.0, 5.0)


def _block(b, c, w, d, h, tier, rnd):
    """An ordered city block: plaster below, masonry above; its front windows lit in rows."""
    add_box(b['plaster'] if tier < 2 else b['masonry'], c + Vector((0, 0, h / 2)), (w, d, h))
    add_box(b['cut'], c + Vector((0, 0, h + 0.3)), (w + 0.6, d + 0.6, 0.6))
    if tier >= 1 and rnd.random() < 0.4:            # a set-back storey
        add_box(b['masonry'], c + Vector((0, 0, h + 0.6 + h * 0.2)), (w * 0.6, d * 0.6, h * 0.4))
    fy = c.y - d / 2 - 0.05
    F, T = Vector((0, -1.0, 0)), Vector((-1.0, 0, 0))
    lit = 0.38 + 0.14 * tier
    nx, nz = max(1, int(w / 2.6)), max(1, int(h / 3.4))
    for i in range(nx):
        for j in range(nz):
            if rnd.random() < lit:
                _face(b['glow'], Vector((c.x - w / 2 + (i + 0.5) * w / nx, fy, c.z + (j + 0.6) * h / nz)), T, F, 1.1, 1.5)


def _tower(b, c, r, h, rnd):
    """A tower: a shaft of masonry, a lit band of windows near its top, a pointed or domed cap."""
    add_cyl(b['masonry'], c, c + Vector((0, 0, h)), r, seg=10)
    add_cyl(b['glow'], c + Vector((0, 0, h - 4.0)), c + Vector((0, 0, h - 2.5)), r + 0.05, seg=10)
    if rnd.random() < 0.5:
        add_cyl(b['sheet'], c + Vector((0, 0, h)), c + Vector((0, 0, h + r * 2.5)), r * 1.1, 0.05, seg=10)
    else:
        _dome(b['sheet'], c + Vector((0, 0, h)), r * 1.1, 10)
    for k in range(int(h / 6)):
        if rnd.random() < 0.7:
            _face(b['glow'], c + Vector((0, -r - 0.05, 3.0 + 6.0 * k)), Vector((-1, 0, 0)), Vector((0, -1, 0)), 0.9, 1.6)


def _dome(bm, c, r, seg=16, rings=5):
    """A hemisphere, its rim at c."""
    rows = []
    for k in range(rings):
        a = math.pi / 2 * k / rings
        rows.append([bm.verts.new(c + Vector((r * math.cos(a) * math.cos(t), r * math.cos(a) * math.sin(t), r * math.sin(a))))
                     for t in [2 * math.pi * i / seg for i in range(seg)]])
    apex = bm.verts.new(c + Vector((0, 0, r)))
    _grid_faces(bm, rows, cyclic=True, flip=True)
    for i in range(seg):
        bm.faces.new((rows[-1][i], rows[-1][(i + 1) % seg], apex))


def _dome_house(b, c, r, h, rnd):
    """A domed hall: a drum ringed with lit windows, a dome, a lantern."""
    add_cyl(b['masonry'], c, c + Vector((0, 0, h)), r, seg=16)
    add_cyl(b['glow'], c + Vector((0, 0, h * 0.55)), c + Vector((0, 0, h * 0.75)), r + 0.05, seg=16)
    _dome(b['sheet'], c + Vector((0, 0, h)), r, 16)
    add_cyl(b['glow'], c + Vector((0, 0, h + r)), c + Vector((0, 0, h + r + 1.5)), r * 0.15, seg=8)


def _civic(b, c, rnd):
    """The great domed hall at the top of the city: a podium, a colonnaded drum lit from within, the
    dome and its lantern, towers either side."""
    add_box(b['masonry'], c + Vector((0, 0, 4.0)), (56.0, 34.0, 8.0))
    add_box(b['cut'], c + Vector((0, 0, 8.3)), (58.0, 36.0, 0.6))
    for i in range(14):
        _face(b['glow'] if i % 3 else b['dark'], c + Vector((-26.0 + 4.0 * i, -17.05, 3.4)), Vector((-1, 0, 0)), Vector((0, -1, 0)), 2.0, 4.2)
    base = c + Vector((0, 0, 8.6))
    add_cyl(b['masonry'], base, base + Vector((0, 0, 15.0)), 16.0, seg=28)
    add_cyl(b['glow'], base + Vector((0, 0, 4.0)), base + Vector((0, 0, 11.0)), 16.05, seg=28)
    for i in range(24):
        t = 2 * math.pi * i / 24
        q = base + Vector((18.0 * math.cos(t), 18.0 * math.sin(t), 0))
        add_box(b['masonry'], q + Vector((0, 0, 6.5)), (1.0, 1.0, 13.0))
    add_cyl(b['cut'], base + Vector((0, 0, 13.0)), base + Vector((0, 0, 15.6)), 19.0, seg=28)
    _dome(b['sheet'], base + Vector((0, 0, 15.6)), 16.5, 24, 7)
    lan = base + Vector((0, 0, 32.1))
    add_cyl(b['glow'], lan, lan + Vector((0, 0, 4.0)), 2.6, seg=10)
    _dome(b['sheet'], lan + Vector((0, 0, 4.0)), 2.8, 10)
    for s in (-1, 1):
        _tower(b, c + Vector((s * 34.0, 4.0, 0)), 4.0, 52.0, rnd)


def _skyline(b, rnd):
    """The far end, lost in haze: flat silhouette cards of more city, and cool lights on them."""
    for y, x0, x1, base, hmax in ((330.0, 70.0, 180.0, 45.0, 85.0), (352.0, 55.0, 195.0, 60.0, 105.0)):
        pts = [Vector((x0, y, base - 30))]
        x = x0
        while x < x1:
            w = rnd.uniform(4.0, 12.0)
            h = base + rnd.uniform(0.2, 1.0) * (hmax - base)
            if rnd.random() < 0.2:                     # a dome
                for k in range(7):
                    a = math.pi * k / 6
                    pts.append(Vector((x + w / 2 - w / 2 * math.cos(a), y, h + w / 2 * math.sin(a))))
            else:
                pts += [Vector((x, y, h)), Vector((x + w, y, h))]
            x += w
            for i in range(int(w / 2.5)):
                if rnd.random() < 0.5:
                    _face(b['haze'], Vector((x - w + 1.2 + 2.5 * i, y - 0.2, rnd.uniform(base - 10, h - 2))), Vector((-1, 0, 0)), Vector((0, -1, 0)), 1.2, 1.4)
        pts.append(Vector((x1, y, base - 30)))
        f = b['card'].faces.new([b['card'].verts.new(p) for p in pts])
        f.normal_update()
        if f.normal.y > 0:
            f.normal_flip()
    # Behind it all, the haze the far end is lost in, faintly lit.
    vs = [b['mist'].verts.new(Vector(p)) for p in ((30.0, 372.0, -48.0), (220.0, 372.0, -48.0), (220.0, 372.0, 150.0), (30.0, 372.0, 150.0))]
    f = b['mist'].faces.new(vs)
    f.normal_update()
    if f.normal.y > 0:
        f.normal_flip()


def _fan(blades, frame, hub, axis, radius, n_blades):
    """A ventilation fan: its ring goes in frame (world), its blades in their own mesh around their local
    Z (the spin axis), to be placed at hub."""
    add_torus(frame, hub, axis, radius + 0.35, 0.32, seg=28, rseg=6)
    for k in range(n_blades):
        a = 2 * math.pi * k / n_blades
        rot = Matrix.Rotation(a, 4, 'Z') @ Matrix.Rotation(0.38, 4, 'X')
        add_box(blades, rot @ Vector((radius * 0.52, 0, 0)), (radius * 0.9, radius * 0.32, 0.08), rot=rot)
    add_cyl(blades, (0, 0, -0.5), (0, 0, 0.5), radius * 0.14, seg=12)


def build_atrium(m, coll):
    """The balcony and stair down to ring C, and the refuge's cave: a city in a chasm under the mountain,
    read in layers. Either side, dark cliffs with ring C's sealed homes at the balcony's level and ring B's
    works above, lit halls and galleries, pipes, a lift tower and a crane. Across the chasm, heavy arched
    viaducts at different heights and a steel catwalk, waterfalls into the misty depths, stalactites
    from a roof barely seen. Down the chasm and higher up, the upper city of domes, towers and chimneys,
    fading into haze: where the game climbs. The near side, toward the camera, is cut away."""
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
    keys = ('plaster', 'masonry', 'sheet', 'rust', 'dark', 'barricade', 'cut', 'cable', 'lamp', 'red', 'glow', 'haze', 'mist', 'card')
    b = {k: bmesh.new() for k in keys}
    WL = _wall(CHASM_LEFT, -1, 0.0)
    WR = _wall(CHASM_RIGHT, 1, 20.0)

    # The rock: both walls, the roof and its stalactites; the buttress the tunnel comes through (left of the
    # balcony), ring C's shelves either side of it, and the rock rising past the lane's end.
    rock = bmesh.new()
    _chasm_wall(rock, WL)
    _chasm_wall(rock, WR)
    _roof(rock)
    for i in range(46):
        y = 12.0 + (i / 45) ** 1.4 * 300.0
        x = rnd.uniform(_wpos(WL, _wat_y(WL, y)).x - 5, _wpos(WR, _wat_y(WR, y)).x + 5)
        _stalactite(rock, x, y, rnd.uniform(2.0, 5.0) * (1 + y / 200), rnd.uniform(8.0, 30.0) * (1 + y / 300), i * 1.7)
    _cliff(rock, ((69.6, 1.45), (69.6, 3.4), (69.1, 6.0), (68.2, 8.6), (66.9, 11.5), (64.9, 14.5)),
           ((-48.0, -6.0), (-25.0, -2.0), (-4.0, 0.8), (1.0, 1.0), (6.0, 0.8), (12.0, 1.0), (18.0, 1.4), (25.0, 2.2),
            (34.0, 3.5), (44.0, 5.5), (54.0, 9.0)), -1, amp=0.3)
    _cliff(rock, ((64.8, 1.7), (66.4, 1.6), (68.2, 1.6), (69.7, 1.6)),            # the rock the tunnel is cut through
           ((3.95, 0.1), (7.0, 0.4), (10.5, 0.9), (14.0, 2.0)), -1, amp=0.25)
    _cliff(rock, ((72.0, 2.7), (71.8, 5.5), (71.0, 8.4), (69.6, 11.3), (67.6, 14.3)),   # ring C, left of the balcony
           ((-48.0, -5.0), (-20.0, -2.0), (-8.0, -1.0), (-3.5, -0.2), (-0.03, 0.0)), -1, amp=0.12,
           top_back=((69.4, 2.5), (69.2, 5.2), (68.4, 8.0), (67.2, 10.8), (65.4, 13.8)))
    _cliff(rock, ((76.4, 2.05), (78.5, 2.1), (80.5, 2.3), (82.5, 2.9), (84.5, 3.9), (86.2, 5.5), (87.5, 7.6), (88.4, 10.2), (89.0, 13.0)),
           ((-48.0, -6.0), (-20.0, -2.5), (-9.5, -1.4), (-5.5, -0.4), (-1.8, 0.4), (-0.03, 0.0)), 1, amp=0.12,
           top_back=((76.4, 1.22), (78.5, 1.22), (80.5, 1.22), (82.5, 1.22), (84.5, 1.22), (86.2, 1.22), (88.5, 1.25), (91.0, 2.5), (92.5, 6.0)))
    _cliff(rock, ((100.5, 1.6), (96.5, 2.6), (93.0, 4.6), (90.4, 7.4), (88.6, 10.8), (87.4, 14.5)),   # rock rising past the lane's end
           ((-48.0, -5.0), (-1.0, 0.0), (3.6, 0.0), (8.0, -0.6), (14.0, 0.4), (20.0, 1.2), (27.0, 2.0), (36.0, 4.0), (50.0, 8.0)), 1, amp=0.3)

    # The upper city, down the chasm and up: three tiers, the great dome on the last.
    civic = Vector((108.0, 258.0, MESAS[-1][1]))
    for tier, (y0, top, depth) in enumerate(MESAS):
        _mesa(rock, b, WL, WR, y0, top, depth, tier, rnd, civic if tier == 2 else None)
    _civic(b, civic, rnd)
    _skyline(b, rnd)
    _cave_obj('AtriumRock', rock, [m['stone'], m['cut']], coll, smooth=True)

    # Life on the walls: ring C, ring B's works, ring A's homes, and the lights of the levels above.
    letters = {'C': (WL, 10.0), 'B': (WL, 125.0), 'A': (WL, 196.0)}
    lit = None
    for W in (WL, WR):
        blocked = {r: [(u, 4.0)] if L is W else [] for r, (L, u) in letters.items()}
        _ring_c(b, W, rnd, blocked['C'] + ([(18.0, 6.0)] if W is WL else [(26.0, 9.0)]))
        _ring_b(b, W, rnd, blocked['B'] + ([(44.0, 8.0)] if W is WL else [(30.0, 10.0)]))
        found = _ring_a(b, W, rnd, blocked['A'], home=HOME_U if W is WR else None)
        lit = lit or found
        _wall_lights(b, W, rnd)
        _low_galleries(b, W, 22.0, 120.0, rnd)
        # Pipes along ring B's back wall, near, and risers up out of the mist.
        pts = []
        for u in range(0, 96, 6):
            pts.append(_wface(W, float(u), 19.0, 1.1))
        _pipe(b['rust'] if W is WL else b['sheet'], pts, 0.6, seg=8)
        for u in (12.0, 38.0, 66.0, 90.0):
            p, _, n = _wframe(W, u)
            lo = min(_woff(W, u, z) for z in (-30.0, -18.0, -8.0, -3.0, 2.0, 8.0, 12.0))
            q = p + n * (lo - 1.2)
            _pipe(b['sheet'], [q + Vector((0, 0, CHASM_FLOOR + 8)), q + Vector((0, 0, 11.0)), q - n * 1.5 + Vector((0, 0, 12.5))], 0.45, seg=8)
    # A lift tower on the left, a crane on the right, platforms out over the chasm.
    lip, back, T, F = _wledge(WL, 18.0, 'C')
    tower = lip + F * 4.5
    _lift_tower(b, tower, 22.0, T, F, rnd)
    for ring in 'CB':                                 # landings across to it from ring C and ring B
        lp = _wledge(WL, 18.0, ring)[0]
        d = Vector((tower.x - lp.x, tower.y - lp.y, 0.0))
        span = d.length - 1.5
        dT = d.normalized()
        add_box(b['sheet'], lp + dT * (span / 2), (span + 0.3, 2.4, 0.15), rot=_rot(Vector((dT.y, -dT.x, 0)), dT))
    for W, u, ring, w, out, crane in ((WR, 30.0, 'B', 9.0, 7.0, True), (WR, 14.0, 'C', 6.0, 4.0, False),
                                      (WL, 44.0, 'B', 7.0, 5.0, False), (WR, 62.0, 'A', 6.0, 4.5, False)):
        lip, back, T, F = _wledge(W, u, ring)
        _platform(b, lip, T, F, w, out, rnd, crane)
    # Across the chasm: viaducts, a catwalk, cables.
    for y, z, width, spans in VIADUCTS:
        _viaduct(b, WL, WR, y, z, width, spans, rnd)
    _catwalk(b, WL, WR, 44.0, -5.0, rnd)
    _catwalk(b, WL, WR, 140.0, 10.0, rnd)
    for (ua, ra), (ub, rb), sag in (((25.0, 'B'), (35.0, 'B'), 5.0), ((55.0, 'C'), (48.0, 'B'), 4.0), ((80.0, 'A'), (95.0, 'A'), 7.0)):
        a = _wledge(WL, ua, ra)[0] + Vector((0, 0, 4.0))
        c = _wledge(WR, ub, rb)[0] + Vector((0, 0, 4.0))
        pts = _sag(a, c, sag, 18)
        _wire(b['cable'], pts, 0.05)
        for i in range(2, len(pts) - 2, 2):
            if rnd.random() < 2 * _litp(pts[i].z):
                add_box(b['glow'], pts[i] - Vector((0, 0, 0.3)), (0.32, 0.32, 0.36))
    # Water falling into the depths, and the mist they fall into.
    for W, u, z, w in ((WL, 96.0, 12.0, 3.0), (WR, 58.0, -2.0, 2.2), (WR, 150.0, 30.0, 5.0), (WL, 230.0, 40.0, 6.0)):
        _falls(b, _wface(W, u, z, 0.6), -_wframe(W, u)[2], w, rnd)
    _falls(b, Vector((104.0, MESAS[1][0] - 1.0, MESAS[1][1] - 2.0)), Vector((0, -1.0, 0)), 4.0, rnd)
    _mist(b, WL, WR)
    # Ring C beside the balcony: boxes on the shelf behind the lane, the left shelf sealed.
    for x0, y0, a, d, stack in ((87.0, 2.6, 1.571, 4.2, 2), (90.4, 2.6, 1.571, 2.45, 3), (89.6, 5.4, 1.87, 2.45, 1)):
        T = Vector((math.cos(a), math.sin(a), 0))
        F = Vector((-T.y, T.x, 0))
        for s in range(stack):
            dd = d if s < 2 else 2.45
            c = Vector((x0, y0, 2.62 * s)) + F * (dd / 2) + T * (0.3 * s * (1 if s % 2 else -1))
            _container(b, c, T, F, (2.45, dd, 2.6), rnd)
    add_box(b['red'], Vector((70.6, 10.4, 2.3)), (0.28, 0.28, 0.3))
    _barricade(b, Vector((69.0, 12.6, 0.0)), Vector((0.25, -0.97, 0)), Vector((0.97, 0.25, 0)), 3.2, rnd)

    # The fans: a big vent in the left cliff below ring B, and one in the roof over the chasm. Their blades
    # are their own meshes, spinning about their local Z (the game's local Y).
    frame, fans = b['sheet'], []
    n = _wframe(WL, 60.0)[2]
    hub = _wface(WL, 60.0, -10.0, 1.8)
    blades = bmesh.new()
    _fan(blades, frame, hub, -n, 3.6, 5)
    fans.append(('AtriumFanLow', blades, hub, -n))
    hub2 = Vector((84.0, 58.0, _ceil_z(84.0, 58.0) - 1.0))
    blades = bmesh.new()
    _fan(blades, frame, hub2, Vector((0, 0, 1)), 7.0, 4)
    for a in (0.3, 1.87):
        add_box(frame, hub2 + Vector((0, 0, 0.6)), (18.0, 0.6, 0.6), rot=_rz(a))
    fans.append(('AtriumFanHigh', blades, hub2, Vector((0, 0, 1))))
    for name, bmf, h, axis in fans:
        ob = _cave_obj(name, bmf, [m['sheet']], coll)
        ob.location = h
        ob.rotation_mode = 'QUATERNION'
        ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(axis)
    # A crack in the roof over the upper city: a glimpse of the real sky, far up.
    sky = bmesh.new()
    cx, cy = 98.0, 252.0
    pts = [Vector((cx + 9.0 * math.cos(t), cy + 2.5 * math.sin(t) + 1.5 * math.sin(3 * t), _ceil_z(cx, cy) - 1.0)) for t in [-2 * math.pi * i / 12 for i in range(12)]]
    sky.faces.new([sky.verts.new(p) for p in pts])
    _cave_obj('AtriumSkyGlimpse', sky, [m['skypanel']], coll)

    mats = {'plaster': m['plaster'], 'masonry': m['masonry'], 'sheet': m['sheet'], 'rust': m['rust'], 'dark': m['dark'],
            'barricade': m['barricade'], 'cut': m['cut'], 'cable': m['rubber'], 'lamp': m['ringlamp'], 'red': m['ringred'],
            'glow': m['windowglow'], 'haze': m['hazelights'], 'mist': m['mist'], 'card': m['stone']}
    names = {'plaster': 'AtriumHomes', 'masonry': 'AtriumMasonry', 'sheet': 'AtriumSheet', 'rust': 'AtriumRust',
             'dark': 'AtriumOpenings', 'barricade': 'AtriumBarricades', 'cut': 'AtriumCutStone', 'cable': 'AtriumCables',
             'lamp': 'AtriumLamps', 'red': 'AtriumRedLamps', 'glow': 'AtriumWindowGlow', 'haze': 'AtriumHazeLights',
             'mist': 'AtriumMist', 'card': 'AtriumSkyline'}
    for k in keys:
        if len(b[k].verts):                       # round things share their normals; boxes stay crisp
            _cave_obj(names[k], b[k], [mats[k]], coll, smooth=k in ('sheet', 'rust', 'cable', 'masonry'), sharp=150 if k == 'cable' else 50)
        else:
            b[k].free()
    if lit:
        bm = bmesh.new()
        add_box(bm, lit[0], (1.0, 0.06, 1.1), rot=_rot(lit[1], lit[2]))
        _cave_obj('AtriumLitWindow', bm, [m['homelight']], coll)
    # The ring letters, painted on the left wall's terraces: C by the balcony, B and A down the chasm.
    for ring, (W, u) in letters.items():
        mat = _image_material(f'RingLetter{ring}', os.path.join(TEX, f'ring_{ring}.png'), rough=0.9, alpha=True)
        _, back, T, F = _wledge(W, u, ring)
        size = 4.6 if ring == 'C' else 6.0
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
