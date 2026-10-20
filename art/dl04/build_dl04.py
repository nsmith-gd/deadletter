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
    atrium_sign_sheet()


def atrium_sign_sheet():
    """The city's painted signs, one sheet of 4 x 2 cells: an UP arrow, ring A and ring B roundels, the lift,
    the stair, an UP arrow in ink (for lamp boxes), the post's envelope, and WORKS B4 in ink."""
    from PIL import Image, ImageDraw, ImageFilter
    S = 256
    img = Image.new('RGBA', (4 * S, 2 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    paint, ink = (214, 204, 176, 235), (24, 20, 16, 245)

    def arrow(ox, oy, col):
        d.polygon([(ox + 128, oy + 22), (ox + 222, oy + 120), (ox + 160, oy + 120), (ox + 160, oy + 234), (ox + 96, oy + 234),
                   (ox + 96, oy + 120), (ox + 34, oy + 120)], fill=col)

    def roundel(ox, oy, letter):
        d.ellipse((ox + 14, oy + 14, ox + 242, oy + 242), outline=paint, width=18)
        d.text((ox + 128, oy + 132), letter, font=_font(150), fill=paint, anchor='mm')
        d.polygon([(ox + 128, oy + 2), (ox + 152, oy + 30), (ox + 104, oy + 30)], fill=paint)

    arrow(0, 0, paint)
    roundel(S, 0, 'A')
    roundel(2 * S, 0, 'B')
    ox = 3 * S                                          # the lift: a cage, up and down
    d.rectangle((ox + 40, 18, ox + 216, 238), outline=paint, width=16)
    d.polygon([(ox + 128, 42), (ox + 178, 110), (ox + 78, 110)], fill=paint)
    d.polygon([(ox + 128, 214), (ox + 178, 146), (ox + 78, 146)], fill=paint)
    oy = S                                              # the stair, climbing
    pts = [(14, oy + 236)]
    for k in range(5):
        pts += [(14 + 46 * k, oy + 196 - 40 * k), (60 + 46 * k, oy + 196 - 40 * k)]
    d.line(pts, fill=paint, width=22, joint='curve')
    d.polygon([(200, oy + 16), (244, oy + 16), (244, oy + 60)], fill=paint)
    arrow(S, S, ink)
    ox = 2 * S                                          # the post: an envelope
    d.rectangle((ox + 22, oy + 58, ox + 234, oy + 198), outline=paint, width=16)
    d.line([(ox + 30, oy + 66), (ox + 128, oy + 140), (ox + 226, oy + 66)], fill=paint, width=16)
    ox = 3 * S
    d.text((ox + 128, oy + 84), 'WORKS', font=_font(58), fill=ink, anchor='mm')
    d.text((ox + 128, oy + 176), 'B 4', font=_font(96), fill=ink, anchor='mm')
    img.filter(ImageFilter.GaussianBlur(0.8)).save(os.path.join(TEX, 'atrium_signs.png'))


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
    m['windowglow'] = emission_material('AtriumWindowGlow', (1.0, 0.55, 0.24), 1.4)     # pass 5: the few left, dim and warm
    m['hazelights'] = emission_material('AtriumHazeLights', (0.6, 0.72, 0.9), 0.6)
    m['mist'] = emission_material('AtriumMist', (0.32, 0.4, 0.48), 0.1)
    m['atcloth'] = simple_material('AtriumCloth', (0.2, 0.13, 0.065), 0.9)        # awnings, washing, tarps
    m['atwood'] = simple_material('AtriumWood', (0.085, 0.06, 0.04), 0.88)        # shutters, doors, crates
    # Pass 5: the city gone dark, overgrown (docs/chapter1_pass5_plan.md, section 3).
    m['vine'] = simple_material('AtriumVine', (0.03, 0.038, 0.02), 0.9)            # vines and roots, hanging
    m['moss'] = simple_material('AtriumMoss', (0.06, 0.075, 0.035), 0.95)          # moss and lichen on the ledges
    m['wet'] = simple_material('AtriumWet', (0.014, 0.016, 0.015), 0.35)           # water stains down the rock


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
    _plane('G4ReturnsSign', (2.1, 0.36), (62.6, 1.78, DECK + 2.4), _image_material('ReturnsSignMat', os.path.join(TEX, 'returns_sign.png')), coll)

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
    """A shipping-box home: w along T, d along F, h up, its front toward F: a door, maybe a window, dark.
    Nearer, its corner posts and rails, a framed door, the odd lamp still on, a mail-slot sign, and what
    is kept on its roof."""
    w, d, h = size
    mat = b['rust'] if rnd.random() < 0.55 else b['sheet']
    rot = _rot(T, F)
    _abox(mat, c + Vector((0, 0, h / 2)), size, rot=rot)
    lod, dr = _lod(c), _drnd(c, 3)
    if lod >= 1:
        for s in (-1, 1):
            _abox(mat, c + T * (s * (w / 2 - 0.05)) + F * (d / 2 - 0.05) + UP * (h / 2), (0.16, 0.16, h + 0.04), rot=rot)
        _abox(mat, c + F * (d / 2 - 0.05) + UP * (h - 0.07), (w + 0.04, 0.16, 0.14), rot=rot)
        _abox(mat, c + F * (d / 2 - 0.05) + UP * 0.07, (w + 0.04, 0.16, 0.14), rot=rot)
        if dr.random() < 0.45:                       # on the roof: a tarp over something, or crates
            if dr.random() < 0.5:
                _abox(b['cloth'], c + UP * (h + 0.35) + T * dr.uniform(-w / 4, w / 4), (min(w * 0.6, 2.6), d * 0.7, 0.7), rot=rot)
            else:
                for i in range(dr.randint(1, 3)):
                    s = dr.uniform(0.5, 0.9)
                    _abox(b['wood'], c + UP * (h + s / 2) + T * dr.uniform(-w / 3, w / 3) + F * dr.uniform(-d / 4, d / 4), (s, s, s), rot=rot @ _rz(dr.uniform(-0.3, 0.3)))
    if not front:
        return
    fc = c + F * (d / 2 + 0.02)
    u = rnd.uniform(-0.3, 0.3) * w
    _face(b['dark'], fc + T * u + Vector((0, 0, 0.95)), T, F, 0.85, 1.9)
    if lod >= 1:                                     # its frame
        q = fc + T * u + F * 0.03
        for s in (-1, 1):
            _abox(b['sheet'], q + T * (s * 0.47) + UP * 0.97, (0.09, 0.06, 1.94), rot=rot)
        _abox(b['sheet'], q + UP * 1.95, (1.03, 0.06, 0.09), rot=rot)
        if lod >= 2 and dr.random() < 0.5:          # the door leaf, ajar
            hinge = q + T * 0.42
            leaf = _rot(T, F) @ Matrix.Rotation(dr.uniform(0.25, 0.9), 4, 'Z')
            _abox(b['wood'] if dr.random() < 0.5 else b['sheet'], hinge + (leaf @ Vector((-0.4, 0.03, 0.0))) + UP * 0.95, (0.8, 0.04, 1.86), rot=leaf)
        if dr.random() < 0.12:                       # a lamp left on over the door
            _wall_lamp(b, fc + T * u + UP * 2.2, F, True)
        elif lod >= 2 and dr.random() < 0.3:          # the mail slot's sign
            _sign(b['signs'], fc + T * (u + (0.75 if u < 0 else -0.75)) + UP * 1.35 + F * 0.01, T, F, (0.42, 0.42), 6)
    if w > 3 and rnd.random() < 0.6:
        side = -1 if u > 0 else 1
        q = fc + T * (side * w * 0.28) + Vector((0, 0, 1.45))
        _face(b['dark'], q, T, F, 1.1, 0.7)
        if lod >= 1:
            _abox(b['cut'], q + F * 0.05 - UP * 0.4, (1.3, 0.14, 0.08), rot=rot)
            for i in (-1, 0, 1):
                _quad(b['sheet'], [q + F * 0.03 + T * (i * 0.3 - 0.02) - UP * 0.35, q + F * 0.03 + T * (i * 0.3 + 0.02) - UP * 0.35,
                                   q + F * 0.03 + T * (i * 0.3 + 0.02) + UP * 0.35, q + F * 0.03 + T * (i * 0.3 - 0.02) + UP * 0.35], F)


def _house(b, c, T, F, w, d, floors, rnd, mat, lit=0.0, home=False):
    """A built home: plaster or sheet walls, a slab roof (now and then a tank or a flue on it), windows in
    a row on each floor, dark. Near and middling, the windows are cut in with stone sills and lintels,
    shuttered or lit with something against the light, balconies off the upper floors, an awning and a
    lamp over the door, chimneys and attics on the roof; far, flat quads. With home, the one lit window's
    opening (its light is AtriumLitWindow), on the first floor a quarter along."""
    h = 3.0 * floors + 0.3
    rot = _rot(T, F)
    lod, dr = _lod(c + F * (d / 2)), _drnd(c, 1)
    roof_mat = b['cut'] if rnd.random() < 0.6 else b['rust']
    r = rnd.random()
    tank = flue = None
    if r < 0.3:
        tank = (c + T * rnd.uniform(-w / 3, w / 3) - F * (d / 4) + Vector((0, 0, h + 0.2)), b['rust'] if r < 0.15 else b['sheet'])
    elif r < 0.5:
        flue = c + T * rnd.uniform(-w / 3, w / 3) - F * (d / 3) + Vector((0, 0, h))
    n = max(1, int(w / 1.9))
    door = rnd.randrange(n)
    ops = []
    for f in range(floors):
        for i in range(n):
            u = (i - (n - 1) / 2) * (w / n)
            if f == 0 and i == door:
                ops.append((f, u, 'door'))
            elif rnd.random() < 0.85:
                ops.append((f, u, 'glow' if rnd.random() < lit else 'dark'))
    # The roof: its slab, and what stands on it.
    _abox(roof_mat, c + Vector((0, 0, h + 0.1)) + F * 0.2, (w + 0.3, d + 0.5, 0.2), rot=rot)
    if tank:
        _tank(b, tank[0], 0.6, 1.3, dr, lod, mat=tank[1])
    elif flue:
        add_cyl(b['sheet'], flue, flue + Vector((0, 0, 2.2)), 0.12, seg=6)
        _abox(b['sheet'], flue + UP * 2.25, (0.36, 0.36, 0.08), rot=rot)
    if lod >= 1:
        top = c + UP * (h + 0.2)
        k = dr.random()
        if k < 0.35 and floors == 2:                 # an attic under a pitched roof
            aw = w * dr.uniform(0.45, 0.7)
            ac = top - F * (d * 0.12) + T * dr.uniform(-(w - aw) / 2, (w - aw) / 2)
            _cbox(mat, ac, T, F, aw, d * 0.55, 1.2, 0.0)
            _gable(b['rust'] if dr.random() < 0.6 else b['sheet'], mat, ac + UP * 1.2, T, F, aw, d * 0.55, 1.3, over=0.25)
            if lod >= 2:
                q = ac + F * (d * 0.275 + 0.01) + UP * 0.25
                _quad(b['glow'] if dr.random() < lit else b['dark'], [q - T * 0.35, q + T * 0.35, q + T * 0.35 + UP * 0.7, q - T * 0.35 + UP * 0.7], F)
        elif k < 0.6:                                 # a shed on the roof
            sw = dr.uniform(1.6, 2.6)
            sc = top - F * (d * 0.25) + T * dr.uniform(-w / 3, w / 3)
            _abox(b['sheet'] if dr.random() < 0.5 else b['rust'], sc + UP * 1.0, (sw, 1.8, 2.0), rot=rot)
            _abox(b['rust'], sc + UP * 2.05 + F * 0.1, (sw + 0.3, 2.2, 0.08), rot=rot @ Matrix.Rotation(0.12, 4, 'X'))
        for i in range(dr.randint(0, 2)):
            _chimney(b, top - F * (d * 0.3) + T * dr.uniform(-w / 2.4, w / 2.4), T, F, dr.uniform(1.0, 2.0), dr)
        if lod >= 2 and dr.random() < 0.3:            # an aerial
            q = top + T * dr.uniform(-w / 3, w / 3) - F * (d * 0.2)
            _wire(b['cable'], [q, q + UP * 3.2], 0.03)
            _abox(b['sheet'], q + UP * 2.8, (1.2, 0.04, 0.04), rot=rot)
            _abox(b['sheet'], q + UP * 2.3, (0.8, 0.04, 0.04), rot=rot)
    fc = c + F * (d / 2 + 0.02)
    if lod == 0:                                       # far: a plain block, its windows flat
        _abox(mat, c + Vector((0, 0, h / 2)), (w, d, h), rot=rot)
        for f, u, kind in ops:
            if kind == 'door':
                _face(b['dark'], fc + T * u + Vector((0, 0, 1.0)), T, F, 0.9, 2.0)
            else:
                _face(b['glow'] if kind == 'glow' else b['dark'], fc + T * u + Vector((0, 0, 3.0 * f + 1.6)), T, F, 0.95, 1.0)
        return
    # Near and middling: a chamfered block, its front cut with the openings.
    ch = 0.22
    _cbox(mat, c, T, F, w, d, h, ch, front=False)
    fc = c + F * (d / 2)
    holes, dress, balconies = [], [], []
    for f, u, kind in ops:
        if home and f == 1 and abs(u - w * 0.25) < 1.25:
            continue
        if kind == 'door':
            holes.append((u, 0.1, 0.9, 2.0, b['dark']))
            dress.append((u, 0.1, 0.9, 2.0, 'door'))
            continue
        if f >= 1 and dr.random() < 0.3:              # a french window onto a balcony
            z = 3.0 * f + 0.25
            k = 'glow' if kind == 'glow' else 'dark'
            holes.append((u, z, 0.95, 2.0, b[k]))
            dress.append((u, z, 0.95, 2.0, k))
            balconies.append((u, z, min(1.9, w / n - 0.25)))
            continue
        k = kind if kind == 'glow' else dr.choice(('shut', 'open', 'dark', 'shut', 'open', 'dark', 'dark'))
        holes.append((u, 3.0 * f + 1.1, 0.95, 1.0, b['glow'] if k == 'glow' else b['dark']))
        dress.append((u, 3.0 * f + 1.1, 0.95, 1.0, k))
    if home:
        holes.append((w * 0.25, 4.05, 0.95, 1.05, b['dark']))
        dress.append((w * 0.25, 4.05, 0.95, 1.05, 'dark'))
    _facade(b, mat, fc, T, F, w - 2 * ch, h, holes)
    for u, z, ww, wh, kind in dress:
        _dress_opening(b, fc + T * u + UP * z, T, F, ww, wh, kind, lod, dr)
        if kind == 'door':
            if dr.random() < 0.5:
                _awning(b, fc + T * u, T, F, 1.5, dr)
            if dr.random() < 1.6 * _litp(c.z):
                _wall_lamp(b, fc + T * (u + 0.75) + UP * 2.3, F, True)
            elif lod >= 2 and dr.random() < 0.3:
                _sign(b['signs'], fc + T * (u - 0.8) + UP * 1.5 + F * 0.01, T, F, (0.45, 0.45), 1)
    for u, z, bw in balconies:
        _balcony(b, fc + T * u + UP * z, T, F, bw, lod, dr)
    for f in range(1, floors):                         # string courses between the floors
        _abox(b['cut'], fc + UP * (3.0 * f + 0.02) + F * 0.04, (w - 2 * ch + 0.02, 0.1, 0.14), rot=rot)
    _abox(b['cut'], fc + UP * (h - 0.12) + F * 0.06, (w + 0.1, 0.14, 0.24), rot=rot)     # the cornice


def _barricade(b, c, T, F, span, rnd):
    """A seal across a terrace: overlapping sheets on posts from lip to back wall, taped across."""
    k = max(2, int(span / 1.1))
    for i in range(k):
        u = (i + 0.5) / k - 0.5
        _abox(b['rust'] if rnd.random() < 0.6 else b['sheet'], c + F * (u * span) + T * (0.05 * (i % 2)) + Vector((0, 0, 1.3 + rnd.uniform(-0.1, 0.15))),
              (0.04, span / k + 0.15, 2.6), rot=_rot(T, F) @ Matrix.Rotation(rnd.uniform(-0.04, 0.04), 4, 'X'))
    for s in (-1, 1):
        _abox(b['barricade'], c - T * 0.08 + Vector((0, 0, 1.4 + 0.3 * s)), (0.03, span * 0.95, 0.16),
              rot=_rot(T, F) @ Matrix.Rotation(s * 0.18, 4, 'X'))
    if _lod(c) >= 1:                                   # its posts
        for u in (-0.5, 0.0, 0.5):
            _abox(b['sheet'], c + F * (u * span * 0.95) - T * 0.1 + UP * 1.4, (0.1, 0.1, 2.8), rot=_rot(T, F))


def _hall(b, c, T, F, w, h, lit, rnd):
    """A workshop hall cut into the rock: a dressed-stone frame round an arched mouth, warm-lit inside
    behind its window bars when the works still run, dark and shuttered when not. Nearer, the arch's
    voussoirs and keystone, a lamp hung in the mouth and the machines against the light, a sign over
    it, a pipe up the rock."""
    rot = _rot(T, F)
    for s in (-1, 1):
        _abox(b['cut'], c + T * (s * (w / 2 + 0.3)) + Vector((0, 0, h / 2)), (0.6, 0.7, h), rot=rot)
    _abox(b['cut'], c + Vector((0, 0, h + 0.35)), (w + 1.2, 0.7, 0.7), rot=rot)
    lod, dr = _lod(c), _drnd(c, 2)
    r = w / 2
    if lod >= 1:                                      # the voussoirs: a ring of dressed stone, its keystone
        spring = max(0.0, h - r)
        q = c + F * 0.12
        prev = None
        for k in range(9):
            a = math.pi * k / 8
            d = T * math.cos(a) + UP * math.sin(a)
            cur = (q + UP * spring + d * r, q + UP * spring + d * (r + 0.45))
            if prev:
                _quad(b['cut'], [prev[0], cur[0], cur[1], prev[1]], F)
            prev = cur
        _abox(b['cut'], c + UP * (h + 0.12) + F * 0.2, (0.5, 0.3, 0.6), rot=rot)
    if lit:
        _arch(b['glow'], c, T, F, w, h)
        fc = c + F * 0.12
        if lod >= 2:                                   # machines against the light: a flywheel, a column
            m = c + F * 0.06 + T * dr.uniform(-w / 4, w / 4)
            rr = dr.uniform(0.6, 1.0)
            _quad(b['dark'], [m + UP * (rr + 0.1) + (T * math.cos(a) + UP * math.sin(a)) * rr for a in [2 * math.pi * k / 10 for k in range(10)]], F, cull=False)
            _quad(b['dark'], [m - T * 0.15, m + T * 0.15, m + T * 0.15 + UP * (rr + 0.1), m - T * 0.15 + UP * (rr + 0.1)], F, cull=False)
        for i in range(1, 4):
            _face(b['dark'], fc + T * ((i / 4 - 0.5) * w) + Vector((0, 0, h * 0.45)), T, F, 0.14, h * 0.9)
        _face(b['dark'], fc + Vector((0, 0, h * 0.42)), T, F, w * 0.98, 0.14)
        if rnd.random() < 0.5:                       # something parked in the mouth, against the light
            _abox(b['rust'] if rnd.random() < 0.5 else b['sheet'], c + F * 0.9 + T * rnd.uniform(-w / 4, w / 4) + Vector((0, 0, 0.6)), (1.6, 1.2, 1.2), rot=rot)
        if lod >= 1:
            _hang_lamp(b, c + F * 0.7 + UP * (h + 0.0), 0.9)
    else:
        _arch(b['dark'], c, T, F, w, h)
        _face(b['rust'] if rnd.random() < 0.5 else b['sheet'], c + F * 0.06 + Vector((0, 0, h * 0.35)), T, F, w * 0.95, h * 0.7)
        if lod >= 2:                                   # the shutter's ribs
            for i in range(1, 6):
                q = c + F * 0.08 + T * ((i / 6 - 0.5) * w * 0.95)
                _quad(b['dark'], [q - T * 0.03, q + T * 0.03, q + T * 0.03 + UP * (h * 0.7), q - T * 0.03 + UP * (h * 0.7)], F)
    if lod >= 1 and dr.random() < 0.55:               # its sign over the lintel
        _signboard(b, c + UP * (h + 1.25) + F * 0.42, T, F, (1.5, 0.75), dr.choice((7, 5)) if lit else dr.choice((2, 0, 4)), lit=lit and dr.random() < 0.6)
    if lod >= 1 and dr.random() < 0.4:                # a pipe out of the works, up the rock
        q = c + T * (r + 0.9) + F * 0.25
        _pipe(b['rust'], [q + UP * 0.3, q + UP * (h + 2.6), q + UP * (h + 3.2) - F * 0.6], 0.14, seg=6)


def _gallery(b, lip, T, F, length, lamp, rnd, out=1.6):
    """A steel gallery cantilevered off a terrace's lip: deck, rail, a post, maybe a lamp. Near, its
    balusters and the deck's edge."""
    rot = _rot(T, F)
    c = lip + F * (out / 2 - 0.2)
    cr = _drnd(lip, 29)
    if cr.random() < 0.3:                               # pass 5: torn off its brackets, hanging down the face
        R = rot @ Matrix.Rotation(-cr.uniform(1.0, 1.35), 4, 'X')
        _abox(b['sheet'], lip + R.to_3x3() @ Vector((0.0, out / 2, -0.08)), (length + 0.05, out + 0.4, 0.14), rot=R)
        _abox(b['sheet'], lip + R.to_3x3() @ Vector((0.0, out + 0.1, 0.5)), (length * 0.7, 0.05, 0.05), rot=R)
        return
    _abox(b['sheet'], c - Vector((0, 0, 0.08)), (length + 0.05, out + 0.4, 0.14), rot=rot)
    _abox(b['sheet'], lip + F * (out - 0.2) + Vector((0, 0, 1.05)), (length + 0.05, 0.06, 0.06), rot=rot)
    post = lip + F * (out - 0.2) - T * (length / 2)
    _abox(b['sheet'], post + Vector((0, 0, 0.55 + (0.7 if lamp else 0))), (0.07, 0.07, 1.1 + (1.4 if lamp else 0)), rot=rot)
    if lamp:
        _abox(b['sheet'], post + F * 0.12 + Vector((0, 0, 2.5)), (0.05, 0.3, 0.05), rot=rot)
        _abox(b['sheet'], post + F * 0.25 + Vector((0, 0, 2.62)), (0.3, 0.3, 0.06), rot=rot)
        _octa(b['lamp'], post + F * 0.25 + Vector((0, 0, 2.45)), 0.12)
    _abox(b['sheet'], c + F * (out / 2) - T * (length / 2) - Vector((0, 0, 0.8)), (0.1, 0.1, 1.9), rot=rot @ Matrix.Rotation(0.7, 4, 'X'))
    lod = _lod(c)
    if lod >= 1:
        e = lip + F * (out - 0.2)
        _abox(b['sheet'], e + UP * 0.5, (length + 0.05, 0.04, 0.04), rot=rot)
        if lod >= 2:
            k = max(2, int(length / 0.45))
            for i in range(k):
                q = e - T * (length / 2) + T * (length * (i + 0.5) / k)
                _quad(b['sheet'], [q - T * 0.015, q + T * 0.015, q + T * 0.015 + UP * 1.05, q - T * 0.015 + UP * 1.05], F)


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
            _abox(b['red'], lip + F * 0.1 + Vector((0, 0, 2.8)), (0.3, 0.3, 0.3))
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
                _abox(b['rust'], rp, (w + 0.4, 1.6, 0.05), rot=_rot(T, F) @ Matrix.Rotation(-0.2, 4, 'X'))
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
                _abox(b['sheet'], c + F * 1.4 + T * rnd.uniform(-1, 1) + Vector((0, 0, 0.45)), (1.0, 0.8, 0.9), rot=_rot(T, F))
            step = rnd.uniform(4.5, 7.0)
        if near:
            ml, _, mT, mF = _wledge(W, u + step / 2, 'C')
            _abox(b['sheet'], ml - mF * 0.2 + Vector((0, 0, 1.0)), (step, 0.05, 0.05), rot=_rot(mT, mF))
            _abox(b['sheet'], lip - F * 0.2 + Vector((0, 0, 0.5)), (0.06, 0.06, 1.0), rot=_rot(T, F))
        if near and _lod(back) >= 2:                  # a cable along the back wall, its bulbs mostly dead
            dr = _drnd(back, 5)
            if dr.random() < 0.5:
                a, e = back + F * 0.4 + UP * 3.3, _wledge(W, u + step, 'C')[1] + F * 0.4 + UP * 3.3
                _festoon(b, a, e, 0.35, 2, lambda: dr.random() < 0.15)
        if rnd.random() < 0.08:                      # a failing lamp, mostly the red ones
            _abox(b['lamp'] if rnd.random() < 0.25 else b['red'], lip - F * 0.3 + Vector((0, 0, 2.4)), (0.28, 0.28, 0.3))
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
                _abox(b['sheet'], g, (w + 1.5, 2.0, 0.14), rot=_rot(T, F))
                _abox(b['sheet'], g + F * 0.95 + Vector((0, 0, 1.0)), (w + 1.5, 0.05, 0.05), rot=_rot(T, F))
                for i in range(3):
                    _face(b['glow'] if rnd.random() < _litp(back.z + h + 2.4) else b['dark'], back + F * 0.32 + T * ((i - 1) * w / 3) + Vector((0, 0, h + 2.4)), T, F, 1.1, 1.2)
            if rnd.random() < 0.5:
                for i in range(rnd.randint(1, 3)):
                    s = rnd.uniform(0.8, 1.5)
                    _abox(b['rust' if rnd.random() < 0.5 else 'sheet'], lip - F * rnd.uniform(1.0, 2.5) + T * rnd.uniform(-w / 2, w / 2) + Vector((0, 0, s / 2)), (s, s, s), rot=_rot(T, F))
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
    last_lamp = None
    while u < 240.0:
        if _blocked(u, blocked):
            u += 1.5
            continue
        lip, back, T, F = _wledge(W, u, 'A')
        k += 1
        if u < 170:
            w, d = rnd.uniform(6.0, 8.5), rnd.uniform(4.5, 5.5)
            c = back + F * (d / 2 + 0.1) - Vector((0, 0, 0.1))
            is_home = home is not None and lit is None and u > home
            _house(b, c, T, F, w, d, 2 if rnd.random() < 0.75 else 3, rnd, b['plaster'] if rnd.random() < 0.8 else b['sheet'], 0.5 * _litp(c.z),
                   home=is_home)
            if is_home:                                # its light sits in the window's recess
                lit = (c + F * (d / 2 - 0.17) + T * (w * 0.25) + Vector((0, 0, 4.6)), T, F)
            _abox(b['cut'], lip - F * 0.3 + Vector((0, 0, 0.5)), (w + 0.8, 0.25, 1.0), rot=_rot(T, F))
            if _lod(lip) >= 1:
                _abox(b['cut'], lip - F * 0.3 + Vector((0, 0, 1.04)), (w + 0.85, 0.36, 0.08), rot=_rot(T, F))
            if rnd.random() < 1.6 * _litp(lip.z):
                head = lip - F * 0.3 + F * 0.55 + Vector((0, 0, 2.55))
                _street_lamp(b, lip - F * 0.3, T, F, 2.8, True)
                if last_lamp is not None and (head - last_lamp).length < 16.0 and _lod(lip) >= 1:
                    dr = _drnd(head, 7)
                    _festoon(b, last_lamp + Vector((0, 0, 0.3)), head + Vector((0, 0, 0.3)), 0.5, 3, lambda: dr.random() < 0.7)
                last_lamp = head
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
            k = rnd.randint(1, 4)
            for i in range(k):
                if rnd.random() < 0.4 + _litp(z):
                    _face(b['glow'] if rnd.random() < 0.6 + 0.3 * _litp(z) else b['haze'], q + T * (i * 2.2), T, -n, 1.2, 1.5)
                else:
                    _face(b['dark'], q + T * (i * 2.2), T, -n, 1.2, 1.5)
            _cliff_home(b, q, T, -n, k)
        u += rnd.uniform(3.0, 7.0)


def _cliff_home(b, q, T, F, k):
    """The front of a home dug into the rock round a row of k windows (the first at q): its wall standing
    out of the cliff, a cornice, a ledge to walk along with a rail, a door, sills and a lamp nearer."""
    lod, dr = _lod(q), _drnd(q, 19)
    cq = q + T * ((k - 1) * 1.1)
    w = (k - 1) * 2.2 + 2.6 + dr.uniform(0.0, 1.6)
    cq = cq + T * dr.uniform(-0.3, 0.3)
    mat = b['masonry'] if q.z > 50.0 or dr.random() < 0.25 else b['plaster']
    h = 3.5 if dr.random() < 0.6 else 6.3
    _cbox(mat, cq - F * 3.53 - UP * 1.6, T, F, w, 7.0, h, 0.2 if lod else 0.0, bottom=True)
    rot = _rot(T, F)
    _abox(b['cut'], cq + F * 0.12 + UP * (h - 1.52), (w + 0.4, 0.5, 0.26), rot=rot)
    if h > 4.0:                                          # an upper floor: a shuttered row, a lamp-lit one now and then
        for i in range(k):
            lit = dr.random() < 0.25 + _litp(q.z)
            _face(b['glow'] if lit else (b['wood'] if lod and dr.random() < 0.5 else b['dark']), q + T * (i * 2.2) + UP * 2.8, T, F, 1.0, 1.2)
        _abox(b['cut'], cq + F * 0.06 + UP * 1.75, (w + 0.1, 0.22, 0.14), rot=rot)
    r = dr.random()
    if r < 0.3 and lod >= 1:                             # a pitched roof, or a tank, on top
        _gable(b['rust'], mat, cq - F * 2.0 + UP * (h - 1.6), T, F, w, 3.6, 1.2, over=0.2)
    elif r < 0.5:
        _tank(b, cq - F * 1.6 + T * dr.uniform(-w / 4, w / 4) + UP * (h - 1.6), 0.6, 1.1, dr, lod)
    _abox(b['cut'], cq + F * 0.55 - UP * 1.7, (w + 2.0, 1.3, 0.22), rot=rot)
    if lod >= 1:
        _abox(b['sheet'], cq + F * 1.15 - UP * 0.65, (w + 2.0, 0.05, 0.05), rot=rot)
        for sx in (-1, 1):
            _abox(b['cut'], cq + T * (sx * (w / 2)) + F * 0.4 - UP * 2.2, (0.3, 1.0, 0.8), rot=rot @ Matrix.Rotation(0.6, 4, 'X'))
        for i in range(k):
            _abox(b['cut'], q + T * (i * 2.2) + F * 0.08 - UP * 0.8, (1.4, 0.18, 0.1), rot=rot)
    side = 1 if dr.random() < 0.5 else -1
    dq = cq + T * (side * (w / 2 - 0.7)) + F * 0.02 - UP * 0.6
    _face(b['dark'], dq, T, F, 0.9, 1.9)
    if dr.random() < 0.3 + _litp(q.z):
        _wall_lamp(b, dq + UP * 1.35 + T * (-side * 0.7), F, True)


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
                _abox(b['sheet'], (a + c) / 2 + F * 0.9, (d.length + 0.05, 1.8, 0.12), rot=_rot(T, F))
                _abox(b['sheet'], (a + c) / 2 + F * 1.75 + Vector((0, 0, 1.0)), (d.length + 0.05, 0.05, 0.05), rot=_rot(T, F))
                if rnd.random() < 0.45:
                    _arch(b['glow'] if rnd.random() < _litp(z) else b['dark'], a + F * 0.05, T, F, 1.6, 2.4, seg=3)
                if rnd.random() < 0.04:                # a failing lamp
                    _abox(b['red'] if rnd.random() < 0.5 else b['lamp'], a + F * 1.7 + Vector((0, 0, 2.2)), (0.26, 0.26, 0.26), rot=_rot(T, F))
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
            _abox(b['sheet'], Vector((q.x, q.y, (zb + top_z) / 2)), (0.3, 0.3, top_z - zb), rot=_rot(T, F))
    z = zb
    while z + 4.0 < top_z + 0.1:                      # x-bracing, on the faces the camera sees
        for fs, fa in ((F, T), (-F, T), (T, F), (-T, F)):
            mid = base + fs * 1.6 + Vector((0, 0, z + 2.0))
            if not _seen(mid, fs):
                continue
            for s in (-1, 1):
                p0 = base + fs * 1.6 + fa * (s * 1.6) + Vector((0, 0, z))
                p1 = base + fs * 1.6 + fa * (-s * 1.6) + Vector((0, 0, z + 4.0))
                _wire(b['sheet'], [p0, p1], 0.05)
        z += 4.0
    z = zb + 4.0
    while z < top_z:
        for s in (-1, 1):
            _abox(b['sheet'], base + F * (s * 1.6) + Vector((0, 0, z)), (3.4, 0.12, 0.12), rot=_rot(T, F))
            _abox(b['sheet'], base + T * (s * 1.6) + Vector((0, 0, z)), (0.12, 3.4, 0.12), rot=_rot(T, F))
        z += 4.0
    _abox(b['sheet'], base + Vector((0, 0, top_z + 0.4)), (4.0, 4.0, 0.4), rot=_rot(T, F))
    add_torus(b['sheet'], base + Vector((0, 0, top_z + 2.2)), T, 1.6, 0.12, seg=16, rseg=4)
    cz = top_z - 9.0
    _abox(b['rust'], base + Vector((0, 0, cz + 0.05)), (2.2, 2.2, 0.1), rot=_rot(T, F))
    _abox(b['red'], base + F * 2.1 + Vector((0, 0, top_z + 0.9)), (0.3, 0.3, 0.3), rot=_rot(T, F))
    for sx in (-1, 1):
        for sy in (-1, 1):
            _abox(b['sheet'], base + T * (sx * 1.15) + F * (sy * 1.15) + Vector((0, 0, cz + 1.4)), (0.12, 0.12, 2.9), rot=_rot(T, F))
    _abox(b['sheet'], base + Vector((0, 0, cz + 2.95)), (2.5, 2.5, 0.2), rot=_rot(T, F))
    _wire(b['cable'], [base + Vector((0, 0, cz + 3.0)), base + Vector((0, 0, top_z + 2.2))], 0.04)
    _octa(b['lamp'], base + Vector((0, 0, cz + 2.6)), 0.12)
    for s in (-1, 1):                                  # the cage's mesh sides
        _quad(b['sheet'], [base + T * (s * 1.15) + F * -1.15 + Vector((0, 0, cz + 0.1)), base + T * (s * 1.15) + F * 1.15 + Vector((0, 0, cz + 0.1)),
                           base + T * (s * 1.15) + F * 1.15 + Vector((0, 0, cz + 1.1)), base + T * (s * 1.15) + F * -1.15 + Vector((0, 0, cz + 1.1))], T * s)
    _signboard(b, base + F * 1.75 + Vector((0, 0, top_z - 2.0)), T, F, (1.0, 1.0), 3, lit=True)


def _crane(b, base, T, F, rnd):
    """A jib crane on a cantilevered platform: mast, jib out over the chasm, a load on its hook."""
    _abox(b['sheet'], base + Vector((0, 0, 6.0)), (0.9, 0.9, 12.0), rot=_rot(T, F))
    _abox(b['rust'], base + F * 6.0 + Vector((0, 0, 11.6)), (0.7, 16.0, 0.9), rot=_rot(T, F))
    _abox(b['sheet'], base - F * 3.0 + Vector((0, 0, 11.3)), (1.8, 3.0, 1.4), rot=_rot(T, F))
    for s in (-1, 1):
        _wire(b['cable'], [base + Vector((0, 0, 14.5)), base + F * (6 + 7.5 * s) + Vector((0, 0, 12.0))], 0.03)
    hook = base + F * 11.5
    _wire(b['cable'], [hook + Vector((0, 0, 11.2)), hook + Vector((0, 0, 4.0))], 0.03)
    _abox(b['rust'], hook + Vector((0, 0, 3.0)), (2.2, 1.6, 1.6), rot=_rot(T, F))
    _abox(b['lamp'], base + F * 13.5 + Vector((0, 0, 11.0)), (0.35, 0.35, 0.35), rot=_rot(T, F))
    if _lod(base) >= 1:
        for k in range(15):                            # the jib's lattice, zig-zag under it
            p0 = base + F * (-2.0 + k) + Vector((0, 0, 11.15))
            p1 = base + F * (-1.5 + k) + Vector((0, 0, 10.2))
            _wire(b['sheet'], [p0, p1, p0 + F * 1.0], 0.04)
        _abox(b['sheet'], base + F * 5.5 + Vector((0, 0, 10.2)), (0.12, 15.0, 0.12), rot=_rot(T, F))
        cab = base + F * 0.9 + Vector((0, 0, 10.0))
        _abox(b['sheet'], cab, (1.4, 1.2, 1.4), rot=_rot(T, F))
        _quad(b['glow'], [cab + F * 0.61 + T * -0.5 + Vector((0, 0, -0.1)), cab + F * 0.61 + T * 0.5 + Vector((0, 0, -0.1)),
                          cab + F * 0.61 + T * 0.5 + Vector((0, 0, 0.5)), cab + F * 0.61 + T * -0.5 + Vector((0, 0, 0.5))], F)


def _platform(b, lip, T, F, w, out, rnd, crane=False):
    """A steel platform cantilevered out over the chasm on struts, crates and a lamp on it."""
    c = lip + F * (out / 2 - 0.5)
    _abox(b['sheet'], c - Vector((0, 0, 0.12)), (w, out + 1.0, 0.25), rot=_rot(T, F))
    for s in (-1, 1):
        a = lip + T * (s * (w / 2 - 0.4)) - Vector((0, 0, 4.5)) + F * 0.3
        e = lip + T * (s * (w / 2 - 0.4)) + F * (out - 0.6) - Vector((0, 0, 0.2))
        add_cyl(b['sheet'], a, e, 0.14, seg=4)
        _abox(b['sheet'], lip + T * (s * w / 2) + F * (out / 2 - 0.5) + Vector((0, 0, 1.05)), (0.05, out + 1.0, 0.05), rot=_rot(T, F))
    _abox(b['sheet'], lip + F * (out - 0.05) + Vector((0, 0, 1.05)), (w, 0.05, 0.05), rot=_rot(T, F))
    for i in range(rnd.randint(2, 4)):
        s = rnd.uniform(0.9, 1.6)
        _abox(b['rust' if rnd.random() < 0.5 else 'sheet'], c + T * rnd.uniform(-w / 3, w / 3) + F * rnd.uniform(-out / 4, out / 4) + Vector((0, 0, s / 2)), (s, s * 1.2, s), rot=_rot(T, F))
    if rnd.random() < 2.5 * _litp(lip.z):
        _abox(b['lamp'], lip + F * (out - 0.1) + T * (w / 2) + Vector((0, 0, 2.2)), (0.32, 0.32, 0.32), rot=_rot(T, F))
    if crane:
        _crane(b, c - T * (w / 3), T, F, rnd)
    if _lod(c) >= 2:
        for i in range(int(w / 0.5)):
            q = lip + F * (out - 0.05) + T * (-w / 2 + 0.25 + 0.5 * i)
            _quad(b['sheet'], [q - T * 0.015, q + T * 0.015, q + T * 0.015 + UP * 1.05, q - T * 0.015 + UP * 1.05], F)


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
    rot = _rot(T, F)
    lod = _lod(a + T * (L / 2) + Vector((0, 0, z)))
    for i, p in enumerate(piers):
        if 0 < i < spans:
            q = Vector((p.x, p.y, zb))
            _cbox(stone, q, T, F, pw, width + 1.0, top - zb, 0.18 * pw, top=False)
            for s in (-1, 1):                          # cutwaters, up to the imposts
                f0 = q + F * (s * (width / 2 + 0.5))
                tip = f0 + F * (s * pw * 0.45)
                hgt = z - 1.0 - (L / spans * 0.84) / 2 - zb
                cap = pw * 0.45
                for side in (-1, 1):
                    e = f0 + T * (side * pw / 2)
                    _quad(stone, [e, tip, tip + UP * hgt, e + UP * (hgt + cap)], (F * s * (pw / 2) + T * side * cap).normalized())
                _quad(stone, [f0 + T * (-pw / 2) + UP * (hgt + cap), f0 + T * (pw / 2) + UP * (hgt + cap), tip + UP * hgt], (F * s + UP).normalized())
                if lod >= 1:                           # the impost: a cap where the arches spring
                    _abox(b['cut'], q + F * (s * (width / 2 + 0.2)) + UP * (hgt + 0.1), (pw + 0.5, 0.6, 0.35), rot=rot)
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
        if lod >= 1:                                   # the voussoirs, proud of each face, and the keystone
            for s in (-1, 1):
                fo = F * (s * (width / 2 + 0.12))
                prev = None
                for k in range(9):
                    ang = math.pi * k / 8
                    d = T * math.cos(ang) + UP * math.sin(ang)
                    fo2 = fo + F * (s * 0.18)
                    cur = (mid + fo2 + UP * spring + d * r, mid + fo2 + UP * spring + d * (r + 1.0))
                    if prev:
                        _quad(b['cut'], [prev[0], cur[0], cur[1], prev[1]], F * s)
                        _quad(b['cut'], [prev[0] - F * (s * 0.32), cur[0] - F * (s * 0.32), cur[0], prev[0]], -d)
                        _quad(b['cut'], [prev[1], cur[1], cur[1] - F * (s * 0.32), prev[1] - F * (s * 0.32)], d)
                    prev = cur
                _abox(b['cut'], mid + fo + UP * (spring + r + 0.5), (0.8, 0.3, 1.1), rot=rot)
    for s in (-1, 1):
        _abox(stone, a + T * (L / 2) + F * (s * (width / 2 - 0.2)) + Vector((0, 0, top + 0.5)), (L, 0.4, 1.0), rot=_rot(T, F))
        if lod >= 1:                                   # the parapet's coping, the string course under it
            _abox(b['cut'], a + T * (L / 2) + F * (s * (width / 2 - 0.2)) + Vector((0, 0, top + 1.06)), (L, 0.62, 0.14), rot=rot)
            _abox(b['cut'], a + T * (L / 2) + F * (s * (width / 2 + 0.1)) + Vector((0, 0, top - 0.25)), (L, 0.5, 0.4), rot=rot)
        x = 4.0
        while x < L - 2:
            if rnd.random() < 1.5 * _litp(z):
                q = a + T * x + F * (s * (width / 2 - 0.2)) + Vector((0, 0, top + 1.0))
                _abox(b['sheet'], q + Vector((0, 0, 1.0)), (0.1, 0.1, 2.0), rot=rot)
                _abox(b['sheet'], q + Vector((0, 0, 1.98)) + F * (s * 0.3), (0.06, 0.6, 0.06), rot=rot)
                _abox(b['glow'], q + Vector((0, 0, 1.75)) + F * (s * 0.55), (0.36, 0.36, 0.42), rot=rot)
                _abox(b['sheet'], q + Vector((0, 0, 2.0)) + F * (s * 0.55), (0.48, 0.48, 0.08), rot=rot)
            x += 9.0 + rnd.uniform(-1, 2)
    if z > 10.0 and lod >= 1:                          # high up, homes built out over the parapet on corbels
        dr = _drnd(a, 11)
        for k in range(spans):
            for s in (-1, 1):
                if dr.random() < 0.55:
                    continue
                hw = dr.uniform(3.0, 5.0)
                hc = a + T * (L * (k + dr.uniform(0.3, 0.7)) / spans) + F * (s * (width / 2 - 0.6)) + Vector((0, 0, top + 1.0))
                hF = F * s
                hT = Vector((hF.y, -hF.x, 0.0))
                hd, hh = 2.6, dr.choice((2.8, 3.2, 5.8))
                hb = hc + hF * (hd / 2 - 0.3)
                _cbox(b['plaster'] if dr.random() < 0.7 else b['sheet'], hb, hT, hF, hw, hd, hh, 0.12)
                _abox(b['rust'], hb + UP * (hh + 0.1), (hw + 0.4, hd + 0.4, 0.16), rot=_rot(hT, hF))
                for c2 in (-1, 1):
                    _abox(b['cut'], hb + hF * (hd / 2 - 0.3) + hT * (c2 * (hw / 2 - 0.3)) - UP * 0.55, (0.3, 0.9, 1.0), rot=_rot(hT, hF) @ Matrix.Rotation(0.5, 4, 'X'))
                fw = hb + hF * (hd / 2 + 0.01)
                for j in range(int(hh / 2.8)):
                    for i in range(max(1, int(hw / 1.6))):
                        uu = (i - (int(hw / 1.6) - 1) / 2) * 1.6
                        lit = dr.random() < 0.5
                        _quad(b['glow'] if lit else b['dark'], [fw + hT * (uu - 0.4) + UP * (2.8 * j + 1.0), fw + hT * (uu + 0.4) + UP * (2.8 * j + 1.0),
                                                                 fw + hT * (uu + 0.4) + UP * (2.8 * j + 2.0), fw + hT * (uu - 0.4) + UP * (2.8 * j + 2.0)], hF)
                        _abox(b['cut'], fw + hT * uu + UP * (2.8 * j + 0.96), (1.0, 0.16, 0.08), rot=_rot(hT, hF))
                if dr.random() < 0.5:
                    _chimney(b, hb - hF * 0.5 + hT * dr.uniform(-hw / 3, hw / 3) + UP * (hh + 0.18), hT, hF, 1.4, dr)


def _catwalk(b, WL, WR, y, z, rnd):
    """A steel catwalk across the chasm, hung from the roof."""
    pl, _, nl = _wframe(WL, _wat_y(WL, y))
    pr, _, nr = _wframe(WR, _wat_y(WR, y + 6))
    a, e = pl + nl * 3.0 + Vector((0, 0, z)), pr + nr * 3.0 + Vector((0, 0, z))
    d = e - a
    T = Vector((d.x, d.y, 0)).normalized()
    F = Vector((-T.y, T.x, 0.0))
    _abox(b['sheet'], (a + e) / 2, (d.length, 1.4, 0.12), rot=_rot(T, F))
    for s in (-1, 1):
        _abox(b['sheet'], (a + e) / 2 + F * (s * 0.68) + Vector((0, 0, 1.0)), (d.length, 0.05, 0.05), rot=_rot(T, F))
    _abox(b['rust'], (a + e) / 2 - Vector((0, 0, 0.8)), (d.length, 0.5, 1.4), rot=_rot(T, F))     # its girder
    x = 6.0
    while x < d.length - 3:
        p = a.lerp(e, x / d.length)
        if rnd.random() < 2 * _litp(z):
            _abox(b['glow'], p + F * 0.7 + Vector((0, 0, 1.4)), (0.35, 0.35, 0.35), rot=_rot(T, F))
        x += 10.0
    lod = _lod((a + e) / 2)
    x = 5.0
    while x < d.length - 2:                            # work lamps hung under its girder
        p = a.lerp(e, x / d.length)
        if lod >= 1:
            dr = _drnd(p)
            _hang_lamp(b, p - Vector((0, 0, 1.5)), 0.5, warm=dr.random() < 0.4, lit=dr.random() < 0.6)
        x += 14.0
    if lod >= 1:
        for s in (-1, 1):
            _abox(b['sheet'], (a + e) / 2 + F * (s * 0.68) + Vector((0, 0, 0.5)), (d.length, 0.04, 0.04), rot=_rot(T, F))
        if lod >= 2:
            k = int(d.length / 1.2)
            for i in range(k):
                q = a.lerp(e, (i + 0.5) / k) - F * 0.68
                _quad(b['sheet'], [q - T * 0.02, q + T * 0.02, q + T * 0.02 + Vector((0, 0, 1.0)), q - T * 0.02 + Vector((0, 0, 1.0))], -F)


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
    dr = _drnd(Vector((xl, y0, top)), 17)
    for zz in (top - 7.0, top - 15.0):
        if zz <= -18:
            continue
        g = Vector(((xl + xr) / 2, y0 - 4.3, zz - 0.15))
        _abox(b['cut'], g, (xr - xl - 6.0, 1.6, 0.3))
        _abox(b['sheet'], g + Vector((0, -0.75, 1.1)), (xr - xl - 6.0, 0.06, 0.06))
        x = xl + 5.0
        while x < xr - 5.0:                              # its lamps, and homes cut in the face between the arches
            if dr.random() < 0.55 + _litp(zz):
                _octa(b['lamp'], Vector((x, y0 - 4.9, zz + 2.3)), 0.2)
            if dr.random() < 0.35:
                q = Vector((x + 3.5, y0 - 3.65, zz))
                _quad(b['plaster'], [q + Vector((-1.8, 0, 0)), q + Vector((1.8, 0, 0)), q + Vector((1.8, 0, 3.2)), q + Vector((-1.8, 0, 3.2))], F)
                for k in (-0.8, 0.8):
                    w0 = q + Vector((k, -0.03, 1.4))
                    _quad(b['glow'] if dr.random() < 0.35 + _litp(zz) else b['dark'],
                          [w0 + Vector((-0.4, 0, 0)), w0 + Vector((0.4, 0, 0)), w0 + Vector((0.4, 0, 1.1)), w0 + Vector((-0.4, 0, 1.1))], F)
            x += dr.uniform(4.0, 7.0)
    if tier < 2:                                         # a switchback stair up the face, flights of 4 m
        sx = dr.uniform(xl + 14.0, xr - 22.0)
        z = max(-18.0, top - 15.0) - 4.0
        k = 0
        while z < top - 0.5:
            rise = min(4.0, top - z)
            x0, x1 = (sx, sx + 9.0) if k % 2 == 0 else (sx + 9.0, sx)
            a, e = Vector((x0, y0 - 5.4, z)), Vector((x1, y0 - 5.4, z + rise))
            dd = e - a
            rot = Vector((1, 0, 0)).rotation_difference(dd.normalized()).to_matrix().to_4x4()
            _abox(b['sheet'], (a + e) / 2, (dd.length, 1.3, 0.22), rot=rot)
            _abox(b['sheet'], (a + e) / 2 + Vector((0, -0.62, 1.0)), (dd.length, 0.05, 0.05), rot=rot)
            _abox(b['sheet'], Vector((x1, y0 - 5.4, z + rise - 0.1)), (1.6, 1.4, 0.2))
            z += rise
            k += 1
    # The top's edge: a balustrade, lamp standards along it.
    pts = [Vector((x, y, 0)) for x, y in lip]
    edge = []
    for i, q in enumerate(pts):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        nrm = Vector((-d.y, d.x, 0.0))
        edge.append(q + nrm * (0.5 * _cave_d(q, top, False) + 0.6) + Vector((0, 0, top)))
    for i, (q0, q1) in enumerate(zip(edge, edge[1:])):
        d = q1 - q0
        dT = Vector((d.x, d.y, 0)).normalized()
        rot = _rot(dT, Vector((-dT.y, dT.x, 0)))
        _abox(b['cut'], (q0 + q1) / 2 + Vector((0, 0, 0.5)), (d.length + 0.3, 0.35, 1.0), rot=rot)
        if dr.random() < 0.5 + _litp(top):
            m = (q0 + q1) / 2 + Vector((0, 0, 1.0))
            _abox(b['sheet'], m + Vector((0, 0, 1.5)), (0.12, 0.12, 3.0))
            _octa(b['lamp'], m + Vector((0, 0, 3.2)), 0.22)
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
                _abox(b['lamp'], c + Vector((0, 0, h * 2.4 + 8.4)), (0.7, 0.7, 0.4))
            else:
                _block(b, c, w, dpt, h, tier, rnd)
            x += w + rnd.uniform(1.0, 4.0)
        yy += dpt + rnd.uniform(2.0, 5.0)


def _block(b, c, w, d, h, tier, rnd):
    """An ordered city block: plaster below, masonry above; its front windows lit in rows. Pilasters at its
    corners, a string course or a balcony band at each floor, its dark windows as well as its lit ones, and
    on its roof tanks, chimneys, a mansard or an aerial with a lamp."""
    F, T = Vector((0, -1.0, 0)), Vector((-1.0, 0, 0))
    mat = b['plaster'] if tier < 2 else b['masonry']
    _abox(mat, c + Vector((0, 0, h / 2)), (w, d, h))
    _abox(b['cut'], c + Vector((0, 0, h + 0.3)), (w + 0.6, d + 0.6, 0.6))
    setback = tier >= 1 and rnd.random() < 0.4
    if setback:                                        # a set-back storey
        _abox(b['masonry'], c + Vector((0, 0, h + 0.6 + h * 0.2)), (w * 0.6, d * 0.6, h * 0.4))
    fy = c.y - d / 2 - 0.05
    lit = 0.38 + 0.14 * tier
    nx, nz = max(1, int(w / 2.6)), max(1, int(h / 3.4))
    for i in range(nx):
        for j in range(nz):
            q = Vector((c.x - w / 2 + (i + 0.5) * w / nx, fy, c.z + (j + 0.6) * h / nz))
            _face(b['glow'] if rnd.random() < lit else b['dark'], q, T, F, 1.1, 1.5)
    dr = _drnd(c, 13)
    for j in range(1, nz):
        z = c.z + j * h / nz - 0.05
        if dr.random() < 0.3:
            _abox(b['cut'], Vector((c.x, fy - 0.5, z)), (w - 0.8, 1.1, 0.22))
            _abox(b['sheet'], Vector((c.x, fy - 1.0, z + 1.0)), (w - 0.8, 0.05, 0.05))
        else:
            _abox(b['cut'], Vector((c.x, fy - 0.1, z)), (w + 0.2, 0.3, 0.25))
    for s in (-1, 1):
        _abox(b['cut'], Vector((c.x + s * (w / 2 - 0.3), fy - 0.15, c.z + h / 2)), (0.6, 0.4, h))
    rt = c + Vector((0, 0, h + 0.6))
    k = dr.random()
    if k < 0.3 and not setback:
        _gable(b['sheet'], mat, rt, T, F, w * 0.92, d * 0.92, min(w, d) * 0.3, over=0.2)
    elif k < 0.65:
        for i in range(dr.randint(1, 2)):
            _tank(b, rt + Vector((dr.uniform(-w / 3, w / 3), dr.uniform(0, d / 3), 0)), dr.uniform(0.9, 1.4), dr.uniform(1.4, 2.4), dr, 0)
    for i in range(dr.randint(1, 3)):
        _chimney(b, rt + Vector((dr.uniform(-w / 2.5, w / 2.5), d / 4, 0)), T, F, dr.uniform(2.0, 4.5), dr)
    if dr.random() < 0.35:                             # an aerial, its lamp at the top
        q = rt + Vector((dr.uniform(-w / 3, w / 3), d / 6, 0))
        hh = dr.uniform(4.0, 8.0)
        _wire(b['cable'], [q, q + Vector((0, 0, hh))], 0.08)
        _octa(b['lamp'], q + Vector((0, 0, hh + 0.2)), 0.22)


TOWERS = []                          # (c, r, h) of every tower built: pass 5 topples one


def _tower(b, c, r, h, rnd):
    """A tower: a shaft of masonry, a lit band of windows near its top, a pointed or domed cap."""
    TOWERS.append((c.copy(), r, h))
    add_cyl(b['masonry'], c, c + Vector((0, 0, h)), r, seg=10)
    add_cyl(b['glow'], c + Vector((0, 0, h - 4.0)), c + Vector((0, 0, h - 2.5)), r + 0.05, seg=10)
    if rnd.random() < 0.5:
        add_cyl(b['sheet'], c + Vector((0, 0, h)), c + Vector((0, 0, h + r * 2.5)), r * 1.1, 0.05, seg=10)
    else:
        _dome(b['sheet'], c + Vector((0, 0, h)), r * 1.1, 10)
    for k in range(int(h / 6)):
        if rnd.random() < 0.7:
            _face(b['glow'], c + Vector((0, -r - 0.05, 3.0 + 6.0 * k)), Vector((-1, 0, 0)), Vector((0, -1, 0)), 0.9, 1.6)
    add_cyl(b['cut'], c + Vector((0, 0, h - 4.6)), c + Vector((0, 0, h - 4.25)), r + 0.7, seg=10)     # its gallery
    add_cyl(b['cut'], c + Vector((0, 0, h - 0.4)), c + Vector((0, 0, h)), r + 0.25, seg=10)           # and cornice
    for k in range(1, int(h / 10)):
        add_cyl(b['cut'], c + Vector((0, 0, 10.0 * k)), c + Vector((0, 0, 10.0 * k + 0.35)), r + 0.12, seg=10)
    tip = c + Vector((0, 0, h + r * 2.6))
    _wire(b['cable'], [tip - Vector((0, 0, 0.5)), tip + Vector((0, 0, 2.6))], 0.06)
    _octa(b['lamp'], tip + Vector((0, 0, 2.8)), 0.24)


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

def _ribs(bm, c, r, n, rings=5, t=0.12, a0=0.0):
    """Ribs over a dome (rim at c): stone or lead seams that catch the light."""
    for i in range(n):
        th = a0 + 2 * math.pi * i / n
        pts = [c + Vector(((r + t) * math.cos(a) * math.cos(th), (r + t) * math.cos(a) * math.sin(th), (r + t) * math.sin(a)))
               for a in [math.pi / 2 * k / rings for k in range(rings)]]
        _wire(bm, pts, t)


def _dome_house(b, c, r, h, rnd):
    """A domed hall: a drum ringed with lit windows, a dome, a lantern."""
    add_cyl(b['masonry'], c, c + Vector((0, 0, h)), r, seg=16)
    add_cyl(b['glow'], c + Vector((0, 0, h * 0.55)), c + Vector((0, 0, h * 0.75)), r + 0.05, seg=16)
    _dome(b['sheet'], c + Vector((0, 0, h)), r, 16)
    add_cyl(b['glow'], c + Vector((0, 0, h + r)), c + Vector((0, 0, h + r + 1.5)), r * 0.15, seg=8)
    add_cyl(b['cut'], c + Vector((0, 0, h - 0.5)), c + Vector((0, 0, h + 0.1)), r + 0.35, seg=16)
    _ribs(b['cut'], c + Vector((0, 0, h)), r, 8)
    _dome(b['sheet'], c + Vector((0, 0, h + r + 1.5)), r * 0.2, 8, 3)


def _civic(b, c, rnd):
    """The great domed hall at the top of the city: a podium, a colonnaded drum lit from within, the
    dome and its lantern, towers either side."""
    _abox(b['masonry'], c + Vector((0, 0, 4.0)), (56.0, 34.0, 8.0))
    _abox(b['cut'], c + Vector((0, 0, 8.3)), (58.0, 36.0, 0.6))
    for i in range(14):
        _face(b['glow'] if i % 3 else b['dark'], c + Vector((-26.0 + 4.0 * i, -17.05, 3.4)), Vector((-1, 0, 0)), Vector((0, -1, 0)), 2.0, 4.2)
    base = c + Vector((0, 0, 8.6))
    add_cyl(b['masonry'], base, base + Vector((0, 0, 15.0)), 16.0, seg=28)
    add_cyl(b['glow'], base + Vector((0, 0, 4.0)), base + Vector((0, 0, 11.0)), 16.05, seg=28)
    for i in range(24):
        t = 2 * math.pi * i / 24
        q = base + Vector((18.0 * math.cos(t), 18.0 * math.sin(t), 0))
        _abox(b['masonry'], q + Vector((0, 0, 6.5)), (1.0, 1.0, 13.0))
    add_cyl(b['cut'], base + Vector((0, 0, 13.0)), base + Vector((0, 0, 15.6)), 19.0, seg=28)
    _dome(b['sheet'], base + Vector((0, 0, 15.6)), 16.5, 24, 7)
    _ribs(b['cut'], base + Vector((0, 0, 15.6)), 16.5, 24, rings=7, t=0.3)
    for i in range(12):                                # lamps round the lantern's gallery
        t = 2 * math.pi * i / 12
        _octa(b['lamp'], base + Vector((4.0 * math.cos(t), 4.0 * math.sin(t), 32.6)), 0.3)
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


# --------------------------------------------------------------------------
# The city's dressing: small modules repeated along the walls (windows, balconies, awnings, roofs, lamps,
# stairs, signs), all merged by material in build_atrium. Detail falls off with distance from the vista,
# and faces no camera can ever face are not built at all.
# --------------------------------------------------------------------------

# Where the city is seen from: the tunnel mouth, the balcony and the vista shot's crane up and back, and ring
# C's ledge as far as the atrium shows (the game's camera x from 62 to 84 here, up to 13 m out, up to 12 m up).
VIEW_BOX = ((62.0, 84.0), (-13.0, -0.5), (-0.5, 12.0))
VIEW_EYE = Vector((74.5, -8.5, 9.5))           # the vista's wide end: detail is graded by distance from it
_VIEW = [Vector((x, y, z)) for x in VIEW_BOX[0] for y in VIEW_BOX[1] for z in VIEW_BOX[2]]
UP = Vector((0, 0, 1))


def _seen(c, n):
    """Can a face at c, its front toward n, ever face a camera that sees the city? The atrium's materials
    are double-sided in the game, so only faces hidden behind their own solid are left out."""
    return any(n.dot(p - c) > 0.0 for p in _VIEW)


def _lod(p):
    """2 near (everything), 1 middle (recesses, slabs, lamps), 0 far (flat, silhouette and lights only)."""
    d = (Vector(p) - VIEW_EYE).length
    return 2 if d < 75.0 else 1 if d < 150.0 else 0


def _drnd(p, salt=0):
    """A random stream for the dressing, seeded by place, so the city's layout (drawn from the scene's own
    stream) never moves when the dressing changes."""
    return random.Random(int(p.x * 7919.0) * 31 + int(p.y * 104729.0) * 17 + int(p.z * 1299.0) + salt)


def _quad(bm, pts, n=None, cull=True):
    """A face through pts on its own verts (its edges stay crisp in smoothed meshes), wound toward n;
    left out when no camera could face it."""
    if n is not None and cull and not _seen(sum(pts, Vector()) / len(pts), n):
        return None
    f = bm.faces.new([bm.verts.new(p) for p in pts])
    if n is not None:
        f.normal_update()
        if f.normal.dot(n) < 0:
            f.normal_flip()
    return f


def _abox(bm, center, size, rot=None):
    """add_box for the city: only the faces some camera can see (most backs and undersides go)."""
    R = rot or Matrix.Identity(4)
    M = Matrix.Translation(Vector(center)) @ R
    R3 = R.to_3x3()
    h = (size[0] / 2, size[1] / 2, size[2] / 2)
    for a, i, j in ((0, 1, 2), (1, 2, 0), (2, 0, 1)):
        for s in (-1, 1):
            n = Vector((0.0, 0.0, 0.0))
            n[a] = s
            pts = []
            for si, sj in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                v = Vector((0.0, 0.0, 0.0))
                v[a], v[i], v[j] = s * h[a], si * h[i], sj * h[j]
                pts.append(M @ v)
            _quad(bm, pts, (R3 @ n).normalized())


def _cbox(bm, c, T, F, w, d, h, ch, top=True, front=True, bottom=False):
    """A block with its four upright edges chamfered, c at the middle of its foot: the corners catch the
    light. front=False leaves the face toward F open for a _facade."""
    hw, hd = w / 2, d / 2
    ch = max(0.0, min(ch, hw * 0.4, hd * 0.4))
    loc = ((-hw + ch, -hd), (hw - ch, -hd), (hw, -hd + ch), (hw, hd - ch), (hw - ch, hd), (-hw + ch, hd), (-hw, hd - ch), (-hw, -hd + ch))
    P = [c + T * a + F * b for a, b in loc]
    up = UP * h
    for i in range(8):
        a, e = P[i], P[(i + 1) % 8]
        if (e - a).length < 1e-4 or (i == 4 and not front):
            continue
        _quad(bm, [a, e, e + up, a + up], (e - a).cross(UP).normalized())
    if top:
        _quad(bm, [p + up for p in P], UP)
    if bottom:
        _quad(bm, P[::-1], -UP)


def _octa(bm, c, r):
    """A bulb: a small octahedron, bright enough to bloom."""
    ring = [bm.verts.new(c + Vector(d) * r) for d in ((1, 0, 0), (0, 1, 0), (-1, 0, 0), (0, -1, 0))]
    top, bot = bm.verts.new(c + UP * (r * 1.3)), bm.verts.new(c - UP * (r * 1.3))
    for i in range(4):
        a, e = ring[i], ring[(i + 1) % 4]
        bm.faces.new((a, e, top))
        bm.faces.new((e, a, bot))


def _hang_lamp(b, top, drop, warm=True, shade=0.22, lit=True):
    """A lamp hung on a drop wire: a six-sided shade open below (left whole, seen from under) and its bulb."""
    p = top - UP * drop
    _wire(b['cable'], [top, p + UP * 0.2], 0.012)
    if shade:
        rt, rb = shade * 0.3, shade
        ring = [(Vector((math.cos(a), math.sin(a), 0))) for a in [math.pi * k / 3 for k in range(6)]]
        for k in range(6):
            a, e = ring[k], ring[(k + 1) % 6]
            _quad(b['sheet'], [p + UP * 0.2 + a * rt, p + UP * 0.2 + e * rt, p + e * rb, p + a * rb], (a + e).normalized(), cull=False)
    if lit:
        _octa(b['glow'] if warm else b['haze'], p - UP * 0.05, 0.09)


def _gable(roof, wall, c, T, F, w, d, rise, over=0.3):
    """A pitched roof over a w by d plan (ridge along T), c at the middle of its eaves; gable ends in wall."""
    hw, hd = w / 2 + over, d / 2 + over
    ridge = [c + T * (-hw) + UP * rise, c + T * hw + UP * rise]
    for s in (-1, 1):
        eave = [c + T * (-hw) + F * (s * hd), c + T * hw + F * (s * hd)]
        n = (F * s * rise + UP * hd).normalized()
        _quad(roof, [eave[0], eave[1], ridge[1], ridge[0]], n)
    for s in (-1, 1):
        _quad(wall, [c + T * (s * w / 2) + F * (-d / 2), c + T * (s * w / 2) + F * (d / 2), c + T * (s * w / 2) + UP * rise], T * s)


def _tank(b, p, r, h, dr, lod, mat=None):
    """A water tank on legs, with a conical lid."""
    mat = mat or (b['rust'] if dr.random() < 0.5 else b['sheet'])
    leg = 0.8 if lod else 0.0
    add_cyl(mat, p + UP * leg, p + UP * (leg + h), r, seg=8 if lod else 6)
    add_cyl(mat, p + UP * (leg + h), p + UP * (leg + h + r * 0.45), r * 1.05, 0.06, seg=8 if lod else 6)
    if lod:
        for sx in (-1, 1):
            for sy in (-1, 1):
                _abox(b['sheet'], p + Vector((sx * r * 0.6, sy * r * 0.6, leg / 2)), (0.08, 0.08, leg))


def _chimney(b, p, T, F, h, dr):
    """A chimney stack: chamfered brick, a cap, now and then a cowl."""
    _cbox(b['masonry'], p, T, F, 0.6, 0.6, h, 0.08)
    _abox(b['cut'], p + UP * (h + 0.06), (0.78, 0.78, 0.12), rot=_rot(T, F))
    if dr.random() < 0.4:
        add_cyl(b['sheet'], p + UP * (h + 0.12), p + UP * (h + 0.6), 0.12, seg=6)
        _abox(b['sheet'], p + UP * (h + 0.66), (0.42, 0.42, 0.06), rot=_rot(T, F))


def _silhouette(dk, base, T, F, ww, wh, kind):
    """Something seen against a lit room: a plant, a standard lamp, a drawn curtain, a hung coat."""
    def P(u, z):
        return base + T * u + UP * z
    if kind == 'plant':
        u = ww * 0.22
        _quad(dk, [P(u - 0.13, 0), P(u + 0.13, 0), P(u + 0.16, 0.24), P(u - 0.16, 0.24)], F, cull=False)
        for a, l in ((-0.6, 0.45), (0.0, 0.6), (0.55, 0.42), (-0.2, 0.5), (0.3, 0.55)):
            tip = P(u + l * math.sin(a), 0.24 + l * math.cos(a))
            _quad(dk, [P(u - 0.03, 0.22), P(u + 0.03, 0.22), tip], F, cull=False)
    elif kind == 'lamp':
        u = -ww * 0.25
        _quad(dk, [P(u - 0.015, 0), P(u + 0.015, 0), P(u + 0.015, wh * 0.62), P(u - 0.015, wh * 0.62)], F, cull=False)
        _quad(dk, [P(u - 0.16, wh * 0.6), P(u + 0.16, wh * 0.6), P(u + 0.08, wh * 0.82), P(u - 0.08, wh * 0.82)], F, cull=False)
    elif kind == 'curtain':
        _quad(dk, [P(ww / 2, 0), P(ww * 0.12, 0), P(ww * 0.22, wh), P(ww / 2, wh)], F, cull=False)
    else:                                   # a coat on a peg
        u = ww * 0.3
        _quad(dk, [P(u - 0.14, wh * 0.25), P(u + 0.14, wh * 0.25), P(u + 0.09, wh * 0.78), P(u - 0.09, wh * 0.78)], F, cull=False)


def _facade(b, wall, c, T, F, w, h, holes, depth=0.22):
    """A wall face cut with openings, c at the middle of its foot, facing F. holes: (u, z, width, height,
    fill) with fill a bucket for the back of the opening; the reveals are in the wall's material, so each
    opening reads as a real recess. Spans between openings are merged into strips."""
    if not holes or not _seen(c + UP * (h / 2), F):
        _quad(wall, [c - T * (w / 2), c + T * (w / 2), c + T * (w / 2) + UP * h, c - T * (w / 2) + UP * h], F)
        return
    zs = sorted({0.0, h} | {z for _, z, _, _, _ in holes} | {z + hh for _, z, _, hh, _ in holes})
    for za, zb in zip(zs, zs[1:]):
        zm = (za + zb) / 2
        cuts = sorted((u - ww / 2, u + ww / 2) for u, z, ww, hh, _ in holes if z < zm < z + hh)
        x = -w / 2
        for a, e in cuts + [(w / 2, w / 2)]:
            if a - x > 1e-4:
                _quad(wall, [c + T * x + UP * za, c + T * a + UP * za, c + T * a + UP * zb, c + T * x + UP * zb], F)
            x = max(x, e)
    back = -F * depth
    for u, z, ww, hh, fill in holes:
        o = c + T * u + UP * z
        l, r, t = o - T * (ww / 2), o + T * (ww / 2), UP * hh
        _quad(wall, [l, l + t, l + t + back, l + back], T)
        _quad(wall, [r, r + back, r + t + back, r + t], -T)
        _quad(wall, [l, l + back, r + back, r], UP)
        _quad(wall, [l + t, r + t, r + t + back, l + t + back], -UP)
        _quad(fill, [l + back, r + back, r + t + back, l + t + back], F)


def _dress_opening(b, c, T, F, ww, wh, kind, lod, dr, depth=0.22):
    """What a window or door cut by _facade gets: c at the middle of its sill in the wall's face. Stone sill
    and lintel; a lit room shows its glazing bars and something against the light; shutters closed in the
    opening or folded back beside it."""
    rot = _rot(T, F)
    if lod >= 1:
        if kind != 'door':
            _abox(b['cut'], c + F * 0.07 - UP * 0.04, (ww + 0.22, 0.18, 0.08), rot=rot)
        _abox(b['cut'], c + UP * (wh + 0.09) + F * 0.03, (ww + 0.3, 0.08, 0.18), rot=rot)
    back = c - F * (depth - 0.03)
    if kind == 'glow':
        if lod >= 1:
            _quad(b['dark'], [back + T * -0.025, back + T * 0.025, back + T * 0.025 + UP * wh, back + T * -0.025 + UP * wh], F)
            _quad(b['dark'], [back - T * (ww / 2) + UP * (wh * 0.62), back + T * (ww / 2) + UP * (wh * 0.62),
                              back + T * (ww / 2) + UP * (wh * 0.62 + 0.05), back - T * (ww / 2) + UP * (wh * 0.62 + 0.05)], F)
        if lod >= 2 and dr.random() < 0.7:
            _silhouette(b['dark'], c - F * (depth - 0.09), T, F, ww, wh, dr.choice(('plant', 'lamp', 'curtain', 'coat', 'plant')))
    elif kind == 'shut':
        p = c - F * 0.06
        _quad(b['wood'], [p - T * (ww / 2), p + T * (ww / 2), p + T * (ww / 2) + UP * wh, p - T * (ww / 2) + UP * wh], F)
        if lod >= 2:
            p = p + F * 0.01
            _quad(b['dark'], [p - T * 0.02, p + T * 0.02, p + T * 0.02 + UP * wh, p - T * 0.02 + UP * wh], F)
    elif kind == 'open' and lod >= 1:
        for s in (-1, 1):
            q = c + F * 0.04 + T * (s * (ww * 0.75 + 0.03))
            _quad(b['wood'], [q - T * (ww / 4), q + T * (ww / 4), q + T * (ww / 4) + UP * wh, q - T * (ww / 4) + UP * wh], F)


def _balcony(b, c, T, F, bw, lod, dr, out=0.95):
    """A balcony off a floor, c at the middle of its threshold in the wall's face: a slab on corbels, rails
    and balusters or a sheet parapet; washing on a line, a pot or two."""
    rot = _rot(T, F)
    cr = _drnd(c, 23)                                   # pass 5: a third of them have fallen, or hang by a corner
    if cr.random() < 0.34:
        if lod >= 2:                                    # the corbels' stubs stay
            for s in (-1, 1):
                _abox(b['cut'], c + F * 0.12 + T * (s * (bw / 2 - 0.18)) - UP * 0.32, (0.12, 0.22, 0.3), rot=rot)
        if cr.random() < 0.6:                           # hanging from one corner, its rail dangling
            s = 1 if cr.random() < 0.5 else -1
            R = rot @ Matrix.Rotation(-s * cr.uniform(0.9, 1.25), 4, 'Y')
            pivot = c + T * (s * bw / 2) - UP * 0.07
            _abox(b['cut'], pivot + R.to_3x3() @ Vector((-s * bw / 2, out / 2, 0.0)), (bw, out, 0.14), rot=R)
            if lod >= 1:
                tip = pivot + R.to_3x3() @ Vector((-s * bw, out - 0.05, 0.0))
                _abox(b['sheet'], tip + Vector((0, 0, -0.45)), (0.05, 0.05, 0.9), rot=rot @ Matrix.Rotation(0.3 * s, 4, 'Y'))
        return
    _abox(b['cut'], c + F * (out / 2) - UP * 0.07, (bw, out, 0.14), rot=rot)
    if lod < 1:
        return
    edge = c + F * (out - 0.05)
    if lod >= 2:
        for s in (-1, 1):
            _abox(b['cut'], c + F * 0.22 + T * (s * (bw / 2 - 0.18)) - UP * 0.32, (0.12, 0.42, 0.36), rot=rot)
    if lod >= 2 and dr.random() < 0.6:
        _abox(b['sheet'], edge + UP * 0.98, (bw, 0.05, 0.05), rot=rot)
        _abox(b['sheet'], edge + UP * 0.12, (bw, 0.04, 0.04), rot=rot)
        k = max(3, int(bw / 0.22))
        for i in range(k + 1):
            q = edge + T * (-bw / 2 + bw * i / k)
            _quad(b['sheet'], [q - T * 0.015, q + T * 0.015, q + T * 0.015 + UP * 0.98, q - T * 0.015 + UP * 0.98], F)
        for s in (-1, 1):
            q = c + T * (s * bw / 2)
            _quad(b['sheet'], [q + UP * 0.95, q + F * out + UP * 0.95, q + F * out + UP * 1.0, q + UP * 1.0], T * s)
    else:
        mat = b['sheet'] if dr.random() < 0.5 else b['rust']
        _quad(mat, [edge - T * (bw / 2), edge + T * (bw / 2), edge + T * (bw / 2) + UP * 0.9, edge - T * (bw / 2) + UP * 0.9], F)
        _abox(b['cut'], edge + UP * 0.93, (bw + 0.06, 0.12, 0.07), rot=rot)
    if lod >= 2 and dr.random() < 0.35:                 # washing on a line across the front
        a, e = edge - T * (bw / 2 - 0.05) + UP * 1.6, edge + T * (bw / 2 - 0.05) + UP * 1.6
        _wire(b['cable'], [a, (a + e) / 2 - UP * 0.08, e], 0.008)
        x = -bw / 2 + 0.2
        while x < bw / 2 - 0.3:
            cw, chh = dr.uniform(0.25, 0.5), dr.uniform(0.3, 0.6)
            q = edge + T * (x + cw / 2) + UP * 1.55 + F * 0.02
            mat = b['cloth'] if dr.random() < 0.5 else b['plaster']
            _quad(mat, [q - T * (cw / 2), q + T * (cw / 2), q + T * (cw / 2) - UP * chh, q - T * (cw / 2) - UP * chh], F, cull=False)
            x += cw + dr.uniform(0.08, 0.3)
    elif lod >= 2 and dr.random() < 0.5:                # a pot plant
        q = c + F * (out * 0.7) + T * dr.uniform(-bw / 3, bw / 3)
        _abox(b['rust'], q + UP * 0.15, (0.3, 0.3, 0.3), rot=rot)
        for a in (-0.5, 0.1, 0.6):
            _quad(b['dark'], [q + UP * 0.28 - T * 0.04, q + UP * 0.28 + T * 0.04, q + UP * (0.28 + 0.5 * math.cos(a)) + T * (0.5 * math.sin(a))], F, cull=False)


def _awning(b, c, T, F, aw, dr, z=2.35):
    """A canvas or tin awning over a door, c at the middle of the door's foot in the wall's face."""
    rot = _rot(T, F) @ Matrix.Rotation(-0.38, 4, 'X')
    mat = b['cloth'] if dr.random() < 0.6 else b['rust']
    _abox(mat, c + F * 0.52 + UP * (z - 0.2), (aw, 1.12, 0.04), rot=rot)
    if mat is b['cloth']:                               # its valance
        q = c + F * 1.04 + UP * (z - 0.4)
        _quad(mat, [q - T * (aw / 2), q + T * (aw / 2), q + T * (aw / 2) - UP * 0.18, q - T * (aw / 2) - UP * 0.18], F)
    for s in (-1, 1):
        q = c + T * (s * (aw / 2 - 0.08))
        _wire(b['cable'], [q + UP * (z + 0.25), q + F * 0.95 + UP * (z - 0.38)], 0.012)


def _wall_lamp(b, p, F, lit):
    """A bracket lamp on a wall, p on the wall's face."""
    T = Vector((F.y, -F.x, 0))
    _abox(b['sheet'], p + F * 0.2, (0.05, 0.4, 0.05), rot=_rot(T, F))
    if lit:
        _octa(b['lamp'], p + F * 0.38 - UP * 0.12, 0.09)
    _abox(b['sheet'], p + F * 0.38 - UP * 0.02, (0.22, 0.22, 0.06), rot=_rot(T, F))


def _street_lamp(b, base, T, F, h, lit, warm=True):
    """A lamp standard: post, an arm out over the void, a lantern; a bulb in it when lit."""
    rot = _rot(T, F)
    _abox(b['sheet'], base + UP * (h / 2), (0.09, 0.09, h), rot=rot)
    _abox(b['sheet'], base + UP * (h - 0.05) + F * 0.3, (0.05, 0.6, 0.05), rot=rot)
    q = base + F * 0.55 + UP * (h - 0.25)
    _abox(b['sheet'], q + UP * 0.2, (0.3, 0.3, 0.06), rot=rot)
    if lit:
        _octa(b['lamp'] if warm else b['haze'], q, 0.11)


def _festoon(b, a, e, sag, n, rnd_lit, warm=True):
    """A string of bulbs slung between two points; rnd_lit() says whether each still lights."""
    pts = _sag(a, e, sag, max(4, n * 2))
    _wire(b['cable'], pts, 0.012)
    for i in range(1, len(pts) - 1, 2):
        if rnd_lit():
            _octa(b['glow'] if warm else b['haze'], pts[i] - UP * 0.12, 0.07)


def _sign(bs, c, T, F, size, cell, cols=4, rows=2):
    """A painted pictogram (a cell of the sign sheet) on a quad facing F, c at its middle."""
    uv = bs.loops.layers.uv.active
    R, hh = -T * (size[0] / 2), UP * (size[1] / 2)      # -T is to the right, seen from the F side
    f = bs.faces.new([bs.verts.new(p) for p in (c - R - hh, c + R - hh, c + R + hh, c - R + hh)])
    col, row = cell % cols, cell // cols
    u0, v0 = col / cols, 1.0 - (row + 1) / rows
    for lp, (du, dv) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uv].uv = (u0 + (du * 0.98 + 0.01) / cols, v0 + (dv * 0.98 + 0.01) / rows)
    f.normal_update()
    if f.normal.dot(F) < 0:
        f.normal_flip()                                  # the UVs stay with their corners


def _signboard(b, c, T, F, size, cell, lit=False):
    """A board on the wall with a pictogram on it: painted on plate, or a lamp box with the sign dark on it."""
    w, h = size
    if lit:
        _abox(b['sheet'], c - F * 0.08, (w + 0.12, 0.12, h + 0.12), rot=_rot(T, F))
        _quad(b['glow'], [c - T * (w / 2) - UP * (h / 2) - F * 0.015, c + T * (w / 2) - UP * (h / 2) - F * 0.015,
                          c + T * (w / 2) + UP * (h / 2) - F * 0.015, c - T * (w / 2) + UP * (h / 2) - F * 0.015], F)
    else:
        _abox(b['sheet'], c - F * 0.04, (w + 0.1, 0.05, h + 0.1), rot=_rot(T, F))
    _sign(b['signs'], c + F * 0.01, T, F, (w, h), cell)


def _stair_run(b, a, e, F, width=1.1, rise=0.36):
    """A steel stair from a up to e (feet of its first and last steps), its open side toward F: treads and
    risers, a stringer each side, a handrail on posts."""
    d = e - a
    run = Vector((d.x, d.y, 0.0))
    L = run.length
    T = run.normalized()
    S = Vector((-T.y, T.x, 0.0))
    if S.dot(F) < 0:
        S = -S
    n = max(2, int(abs(d.z) / rise))
    tr, ri = L / n, d.z / n
    for s in (-1, 1):                                   # stringers
        side = S * (s * width / 2)
        _quad(b['sheet'], [a + side - UP * 0.25, e + side - UP * 0.25, e + side + UP * 0.05, a + side + UP * 0.05], S * s)
    for k in range(n):
        p = a + T * (tr * k) + UP * (ri * k)
        l, r = p - S * (width / 2), p + S * (width / 2)
        _quad(b['sheet'], [l, r, r + UP * ri, l + UP * ri], -T)
        _quad(b['sheet'], [l + UP * ri, r + UP * ri, r + UP * ri + T * tr, l + UP * ri + T * tr], UP)
    rail = [a + S * (width / 2) + UP * 1.0, e + S * (width / 2) + UP * 1.0]
    _wire(b['sheet'], rail, 0.03)
    for k in range(0, n + 1, max(1, n // 4)):
        p = a + T * (tr * k) + UP * (ri * k) + S * (width / 2)
        _abox(b['sheet'], p + UP * 0.5, (0.05, 0.05, 1.0))


def _tier_stair(b, W, u, lo, hi, run=17.0):
    """A steel stair up the rock from one terrace to the next, along the wall: its foot signed with the
    ring it climbs to, an arrow painted big on the rock above."""
    la, _, Ta, Fa = _wledge(W, u, lo)
    le, _, Te, Fe = _wledge(W, u + run, hi)
    a, e = la - Fa * 1.4, le - Fe * 0.4
    _stair_run(b, a, e, Fa)
    d = Vector((e.x - a.x, e.y - a.y, 0)).normalized()
    _abox(b['sheet'], e + d * 0.8 - UP * 0.06, (1.6, 1.4, 0.12), rot=_rot(d, Vector((-d.y, d.x, 0))))
    post = a - d * 1.0
    _abox(b['sheet'], post + UP * 1.2, (0.08, 0.08, 2.4))
    _signboard(b, post + UP * 2.0 + Fa * 0.06, Ta, Fa, (0.7, 0.7), 1 if hi == 'A' else 2)
    _signboard(b, post + UP * 1.2 + Fa * 0.06, Ta, Fa, (0.55, 0.55), 4)
    _sign(b['signs'], _wface(W, u + 4.0, _tier(lo)[1] + 7.5, 0.35), Ta, Fa, (2.6, 2.6), 0)


def _haze_curtain(b, WL, WR, y, z0, z1):
    """A layer of haze across the chasm at a depth: a sheet from wall to wall (its ends buried in the rock),
    its top along the edge of the tier behind it so the line it draws is the tier's own."""
    pl = _wpos(WL, _wat_y(WL, y)) if y < WL['pts'][-1].y else WL['pts'][-1]
    pr = _wpos(WR, _wat_y(WR, y)) if y < WR['pts'][-1].y else WR['pts'][-1]
    vs = [Vector((pl.x - 12.0, y, z0)), Vector((pr.x + 12.0, y, z0)), Vector((pr.x + 12.0, y, z1)), Vector((pl.x - 12.0, y, z1))]
    f = b['mist'].faces.new([b['mist'].verts.new(v) for v in vs])
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
    keys = ('plaster', 'masonry', 'sheet', 'rust', 'dark', 'barricade', 'cut', 'cable', 'lamp', 'red', 'glow', 'haze', 'mist', 'card',
            'cloth', 'wood', 'signs')
    b = {k: bmesh.new() for k in keys}
    b['signs'].loops.layers.uv.new('UVMap')
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

    # The dressing that ties the levels together (its own random stream: the layout above never moves).
    xr = random.Random(4711)
    for W, u, lo, hi in ((WL, 50.0, 'C', 'B'), (WL, 92.0, 'B', 'A'), (WR, 62.0, 'C', 'B'), (WR, 96.0, 'B', 'A')):
        _tier_stair(b, W, u, lo, hi)
    # Cables strung across the chasm, lamps hung from them (most still burning), a string of bulbs over the
    # works, and a pipe bridge slung under its cable.
    for ua, ub, z, sag, n in ((20.0, 25.0, 5.5, 3.0, 3), (66.0, 74.0, 30.0, 6.0, 4), (130.0, 128.0, 34.0, 6.0, 4)):
        a, e = _wface(WL, ua, z, 0.3), _wface(WR, ub, z, 0.3)
        pts = _sag(a, e, sag, 20)
        _wire(b['cable'], pts, 0.04)
        for k in range(n):
            q = pts[int((k + 0.5) / n * 19) + 1]
            _hang_lamp(b, q, xr.uniform(0.6, 1.6), warm=xr.random() < 0.8, lit=xr.random() < 0.35 + 2.0 * _litp(q.z))
    a, e = _wface(WL, 36.0, 17.5, 0.3), _wface(WR, 44.0, 17.5, 0.3)
    _festoon(b, a, e, 3.0, 8, lambda: xr.random() < 0.6)
    a, e = _wface(WL, _wat_y(WL, 98.0), 4.0, 0.5), _wface(WR, _wat_y(WR, 102.0), 4.0, 0.5)
    top_a, top_e = a + UP * 7.0, e + UP * 7.0
    hang = _sag(top_a, top_e, 4.0, 16)
    _wire(b['cable'], hang, 0.05)
    for off, rr, mat in ((0.0, 0.32, 'rust'), (0.75, 0.22, 'sheet')):
        side = Vector((-(e - a).y, (e - a).x, 0)).normalized() * off
        line = _sag(a + side, e + side, 1.2, 16)
        _pipe(b[mat], line, rr, seg=8)
        for k in range(2, 15, 3):
            add_cyl(b[mat], line[k] - (line[k + 1] - line[k]).normalized() * 0.08, line[k] + (line[k + 1] - line[k]).normalized() * 0.08, rr + 0.08, seg=8)
    for k in range(2, 15, 2):
        _wire(b['cable'], [hang[k], _sag(a, e, 1.2, 16)[k] + UP * 0.42], 0.02)
    # Haze at depth: behind the near viaduct (its top hidden behind the parapet) and before the upper city's
    # first and last tiers (their tops along the tiers' own edges).
    _haze_curtain(b, WL, WR, VIADUCTS[0][0] + 6.0, CHASM_FLOOR, VIADUCTS[0][1] + 0.2)
    for y0, top, _ in (MESAS[0], MESAS[2]):
        _haze_curtain(b, WL, WR, y0 - 6.0, CHASM_FLOOR, top - 1.0)

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
            'glow': m['windowglow'], 'haze': m['hazelights'], 'mist': m['mist'], 'card': m['stone'],
            'cloth': m['atcloth'], 'wood': m['atwood'],
            'signs': _image_material('RingLetterSigns', os.path.join(TEX, 'atrium_signs.png'), rough=0.85, alpha=True)}
    names = {'plaster': 'AtriumHomes', 'masonry': 'AtriumMasonry', 'sheet': 'AtriumSheet', 'rust': 'AtriumRust',
             'dark': 'AtriumOpenings', 'barricade': 'AtriumBarricades', 'cut': 'AtriumCutStone', 'cable': 'AtriumCables',
             'lamp': 'AtriumLamps', 'red': 'AtriumRedLamps', 'glow': 'AtriumWindowGlow', 'haze': 'AtriumHazeLights',
             'mist': 'AtriumMist', 'card': 'AtriumSkyline', 'cloth': 'AtriumCloth', 'wood': 'AtriumWood', 'signs': 'AtriumSigns'}
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
    __import__('hopscotch_clip').clip_hopscotch_long(dl01, arm)   # DL-08's long version (hopscotch_clip.py)
    clip_look_back(dl01, arm)
    clip_awe(dl01, arm)
