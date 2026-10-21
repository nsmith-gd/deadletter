"""Chapter 1 Attendance, DL-15 One Pupil Missing (game x 248.0 to 264.0). Design: docs/chapter1_part2_plan.md.

Class 6, the last class: a small classroom built for forty. Over the door he came in by (the duct from DL-14's hatch), a
raised sick bay balcony at 1.6 with a child's cot, a folding screen and a dripping basin; a pupil lift down from its
right end; the figures' rail along the floor from the lift to the end partition; three front-row places kept ready
(S1 R. ABEL, S2 T. ORME, S3 Mara's, with her crooked tree carved in the lid and her chair pulled out and turned); rows of
empty desks going back into the dark of an alcove behind; the attendance board with its three lamps and a bell; the
blackboard with the headcount crossed out and rewritten smaller under the Steward's portrait; the teacher's desk; and the
end partition with the class door and the rail's flap. Under the balcony, behind a half-pulled blanket, Mara's hiding
place: the nest, pencil trees all over the wall and the deck's underside, a cup held to a copper pipe, a biscuit tin with
the voice-card player on it, a torch, and a small warm lamp.

Called by build_attendance.py as build_set(dl01, m, coll), in final world coordinates.
Blender (x, y, z) is the game's (x, z, -y): +y is away from the camera, z is up. The lane is y -0.3..0.3, the floor z 0.

What the game moves (origin = pivot, world coordinates; REPORT at the bottom has the game's numbers):
    Att15FigA, Att15FigB   teaching figures on rail stands; origin on the rail top under the stand's centre; facing +x
    Att15Lift              the pupil lift, built UP (deck top 1.6); origin at the deck's top centre; includes its rail stub
    Att15LiftGate          its folding gate, built shut at the top; origin on the hinge post (back right corner, deck level)
    Att15LiftCW            the counterweight, built low (lift up); origin at its centre
    Att15LampPupil, Att15LampEscort, Att15Lamp1..3, Att15HideLamp   emissive lamps, own objects and materials
    Att15Door              the class door in the end partition, built shut; origin on its hinge (x 263.9)
    Att15Flap              the rail's flap in the end partition, built shut; origin on its top hinge
Static: Att15Set (the room), Att15Rows (the empty desks behind, merged), Att15Lights (the pendant bulbs, EMIT AttBulbGlow),
Att15Hide (the hiding place, with the card player), Att15Chair (Mara's chair: D-17 sits on it), Att15Bell.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
from build_d17 import add_box, add_cyl, add_sphere, add_torus, worn_material, simple_material, emission_material

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
COMMON = os.path.join(HERE, '..', 'common')
ATLAS_PATH = os.path.join(TEX, 'dl15_atlas.png')

# =====================================================================================================================
# Layout (Blender world; game x = x; the plan's numbers, which the game codes against)
# =====================================================================================================================
X0, X1 = 248.0, 264.0
LWALL = (248.0, 248.15)            # the left wall (DL-14's end wall is at 247.85: the gap stays dark)
BACK_Y = 1.4                       # the back wall's face
BACK_T = 0.2
CEIL = 3.6
FRONT_Y = -0.6                     # the cut toward the camera: walls and ceiling stop here
LANE = (-0.3, 0.3)
RAIL_Y = 0.55                      # the figures' rail: two rails either side of it
RAIL_G = 0.08                      # half the gauge (rails at y 0.47 and 0.63)
RAIL_H = 0.03                      # rail top above what it lies on
CHAN = (0.39, 0.71)                # the timber channel the rails lie in
HATCH = (248.55, 249.35, 1.6, 2.4)     # x0, x1, sill, head: the duct's end in the back wall
DUCT_Y = (1.4, 2.6)
BAL = (248.15, 251.4, -0.3, 1.4, 1.6)  # the sick bay balcony: x0, x1, y0, y1, top
BAL_UNDER = 1.5                        # clear height under it
BAL_STUB = (248.4, 251.4)              # its rail stub
FIGB_X, FIGA_X = 249.9, 259.2
COT = (249.6, 250.9, 0.9, 1.35)
LIFT = (251.4, 252.4, -0.3, 0.9, 1.6)  # x0, x1, y0, y1, deck top (built up)
LIFT_T = 0.06                          # the deck's thickness: the pit it sits in when down
POST_Y = 0.95
POSTS_X = (251.45, 252.35)
GATE_HINGE = (252.4, 0.9, 1.6)
SHEAVE = (251.57, 1.05, 3.3, 0.15)     # x, y, z, r (in the yz plane)
CW = (251.48, 251.66, 1.09, 1.31, 0.1, 0.85)
LAMP_PUPIL = (252.11, 0.85, 2.2)
LAMP_ESCORT = (252.25, 0.85, 2.2)
FLOOR_RAIL = (252.4, 264.0)
SEATS = (('S1', 253.2, 'R. ABEL'), ('S2', 254.6, 'T. ORME'), ('S3', 256.0, 'M. D.'))
DOCK_Y = (0.715, 0.79)                 # rev 0.3: the docks at S1 and S2 stand behind the rail's back edge (y)
SEAT_PLATE = (0.065, 0.006)            # Mara's chair: its round brass pressure plate, radius and thickness
PINBOARD = (257.56, 258.70, 1.06, 1.63)   # rev 0.3: the cork board under the attendance board: x0, x1, z0, z1
DRAWING = (257.83, 1.08)               # the drawing's sheet: its left edge x, bottom z (SHEET, STRIP give its size)
DESK_Y = (0.8, 1.2)
DESK_W = 0.3                           # half width
CHAIR = (255.92, 0.31, -4.0)           # Att15Chair: seat centre x, y; turn (degrees; it faces +x, its back to -x)
CHAIR_SEAT = 0.30
ALCOVE = (252.6, 257.25, 4.0)          # x0, x1 (inner faces), back wall face
ROWS_X = (252.95, 253.7, 254.45, 255.2, 255.95, 256.7)
ROWS_Y = (1.85, 2.5, 3.15, 3.75)
ATT = (257.4, 258.8, 1.7, 2.5)         # the attendance board: x0, x1, z0, z1
ATT_FACE = 1.37
ATT_LAMPS = (257.64, 258.1, 258.56)
ATT_LAMP_Z = 2.17
BELL = (258.1, BACK_Y, 2.74)
BB = (258.9, 261.6, 0.86, 2.04)        # the blackboard
PORTRAIT = (260.25, 2.68)              # its centre (x, z)
TDESK = (261.8, 262.6, 0.95, 1.38, 0.72)
PART = (263.75, 263.9)                 # the end partition
DOOR = (-0.3, 0.375, 2.0)              # y0, y1, height
DOOR_HINGE = (263.9, 0.38, 0.0)
FLAP = (263.8, 263.83, 0.41, 0.71, 0.035, 1.05)   # x0, x1, y0, y1, z0, z1
FLAP_HINGE = (263.815, 0.56, 1.05)
HIDE = (248.3, 251.2, 0.4, 1.4)        # the hiding place under the balcony
BLANKET_Y = 0.35
HIDE_ENTRY = 249.8
STOOL = (249.95, 0.92, 0.26)           # rev 0.3: the escort's stool (centre x, y; seat top), where the tin was
LOG_T = 0.03                           # the escort's log on it, closed
PLAYER_AT = (249.95, 0.94, STOOL[2] + LOG_T)   # the card player stands on the log (it was on the tin, at z 0.1)
HIDE_LAMP = (250.62, 1.12, 0.13)       # the hide lamp's glass
PIPE_Z = 0.44
PIPE_Y = BACK_Y - 0.055                # the copper pipe along the hide's back wall
PENDANTS = ((250.2, 0.45, 3.02), (254.6, 0.15, 2.95), (258.5, 0.15, 2.95), (262.3, 0.3, 2.95))
DEAD_PENDANT = (254.9, 2.8, 3.0)

# =====================================================================================================================
# Materials (the game's existing names wherever one fits; fallbacks for a lone build)
# =====================================================================================================================
KNOWN_WORN = {
    'PupilWood': dict(base=(.36, .27, .17), dirt=(.17, .12, .08), chip=(.46, .38, .27), rough=.7, chip_rough=.6, metallic=0,
                      grime_scale=12, chip_scale=40, chip_amount=.74, dust=(.3, .28, .24), dust_amount=.5),
    'CrateWood': dict(base=(.18, .12, .07), dirt=(.08, .055, .035), chip=(.25, .19, .12), rough=.85, chip_rough=.8, metallic=0,
                      grime_scale=6, chip_scale=30, chip_amount=.75, streaks=.6),
    'PigeonWood': dict(base=(.12, .085, .055), dirt=(.06, .045, .03), chip=(.2, .15, .1), rough=.85, chip_rough=.8, metallic=0,
                       grime_scale=6, chip_scale=30, chip_amount=.75, dust=(.1, .09, .08), dust_amount=.6),
    'WornIron': dict(base=(.045, .043, .04), dirt=(.06, .035, .02), chip=(.3, .29, .27), rough=.7, chip_rough=.35, metallic=.6,
                     grime_scale=9, chip_scale=40, chip_amount=.6, dust=(.09, .085, .075), dust_amount=.4),
    'HandledBrass': dict(base=(.2, .14, .06), dirt=(.08, .06, .03), chip=(.62, .46, .2), rough=.5, chip_rough=.2, metallic=.85,
                         grime_scale=8, chip_scale=26, chip_amount=.5, dust=(.12, .1, .07), dust_amount=.2),
    'LessonPlaster': dict(base=(0.27, 0.25, 0.2), dirt=(0.14, 0.12, 0.09), chip=(0.17, 0.15, 0.12), rough=0.9, chip_rough=0.85,
                          metallic=0.0, grime_scale=3.0, chip_scale=18.0, chip_amount=0.7, streaks=0.6),
    'LessonDado': dict(base=(0.13, 0.19, 0.15), dirt=(0.07, 0.09, 0.07), chip=(0.25, 0.23, 0.19), rough=0.75, chip_rough=0.9,
                       metallic=0.0, grime_scale=4.0, chip_scale=24.0, chip_amount=0.68, streaks=0.5),
}
KNOWN_PLAIN = {'Brass': ((.45, .32, .12), .45, .8), 'Copper': ((.55, .3, .18), .35, 1.0)}
NEW_EMIT = {     # name: (colour, strength), as index.html EMIT (0: off as built; the game switches it)
    'Att15LampPupil': ((0.72, 1.0, 0.78), 0.0),
    'Att15LampEscort': ((1.0, 0.66, 0.26), 0.0),
    'Att15Lamp1': ((1.0, 0.86, 0.62), 0.0),
    'Att15Lamp2': ((1.0, 0.86, 0.62), 0.0),
    'Att15Lamp3': ((1.0, 0.86, 0.62), 0.0),
    'Att15HideLamp': ((1.0, 0.7, 0.4), 5.0),
}
KNOWN_EMIT = {'AttBulbGlow': ((1.0, 0.82, 0.58), 4.0)}
ATLAS_MAT = 'Att15Atlas'


def mat(name):
    mt = bpy.data.materials.get(name)
    if mt is not None:
        return mt
    if name in KNOWN_WORN:
        return worn_material(name, **KNOWN_WORN[name])
    if name in KNOWN_PLAIN:
        c, r, mtl = KNOWN_PLAIN[name]
        return simple_material(name, c, r, metallic=mtl)
    if name in NEW_EMIT or name in KNOWN_EMIT:
        c, s = NEW_EMIT.get(name) or KNOWN_EMIT[name]
        return emission_material(name, c, s)
    if name == ATLAS_MAT:
        mt, nt, bsdf = d17._new_material(name)
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(ATLAS_PATH, check_existing=True)
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = 0.8
        return mt
    vp = _voice_props()
    if vp is not None:
        return vp.material(name)
    raise KeyError(name)


def _voice_props():
    import sys
    if not os.path.exists(os.path.join(COMMON, 'VOICE_PROPS_READY')):
        return None
    if COMMON not in sys.path:
        sys.path.insert(0, COMMON)
    import voice_props
    return voice_props


# =====================================================================================================================
# The atlas (PIL, at build time, into art/ch1/textures/dl15_atlas.png): every painted thing in the room, one draw call
# =====================================================================================================================
ATLAS = 1024
CELLS = {
    'board': (0, 0, 1024, 448),             # the blackboard, 2.7 x 1.18 m
    'att': (0, 448, 384, 668),              # the attendance board, 1.4 x 0.8 m
    'blanket': (0, 668, 72, 740),
    'portrait': (384, 448, 512, 608), 'stewplate': (384, 608, 512, 640), 'register': (384, 640, 512, 736),
    'liftsign': (0, 740, 512, 900),         # 0.86 x 0.28 m
    'name1': (0, 900, 128, 952), 'name2': (128, 900, 256, 952), 'name3': (256, 900, 384, 952),
    'lpupil': (384, 900, 512, 926), 'lescort': (384, 926, 512, 952),
    'dock1': (0, 952, 128, 988), 'dock2': (0, 988, 128, 1024), 'book': (128, 952, 224, 1024), 'clock': (224, 952, 296, 1024),
    'log': (896, 928, 1024, 1024),
    'pencil': (512, 448, 1024, 712),        # the hide's back wall, 2.9 x 1.46 m
    'under': (512, 712, 1024, 800),         # the deck's underside over the hide, 2.9 x 1.0 m
    'lid': (512, 800, 768, 928),            # Mara's desk lid, 0.56 x 0.28 m
    'dismiss': (768, 800, 1024, 864), 'sickbay': (768, 864, 1024, 928),
    'notice': (512, 928, 704, 1024), 'class6': (704, 928, 896, 992),
}
SWATCH = {'sw_dark': (8, 8, 8), 'sw_wood': (112, 84, 56), 'sw_wooddk': (64, 46, 30), 'sw_iron': (40, 39, 37),
          'sw_brass': (160, 124, 62), 'sw_enamel': (196, 194, 182), 'sw_ticking': (150, 146, 128), 'sw_screen': (170, 156, 120),
          'sw_cushion': (120, 58, 46), 'sw_tin': (58, 82, 110), 'sw_torch': (44, 70, 54), 'sw_pencil': (196, 156, 52),
          'sw_glass': (70, 74, 72), 'sw_chalk': (214, 210, 198), 'sw_felt': (60, 54, 50), 'sw_pages': (196, 188, 164),
          'sw_rubber': (20, 20, 20), 'sw_pale': (150, 144, 126)}
for _i, _k in enumerate(SWATCH):
    CELLS[_k] = (72 + 34 * (_i % 9), 668 + 36 * (_i // 9), 72 + 34 * (_i % 9) + 34, 668 + 36 * (_i // 9) + 36)


def cell_uv(name):
    x0, y0, x1, y1 = CELLS[name]
    return x0 / ATLAS, 1 - y1 / ATLAS, x1 / ATLAS, 1 - y0 / ATLAS


def cell_mid(name):
    u0, v0, u1, v1 = cell_uv(name)
    return (u0 + u1) / 2, (v0 + v1) / 2


def _font(size, kind='sans-bold'):
    from PIL import ImageFont
    paths = {'sans-bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
             'sans': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
             'serif': '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
             'carlito': '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf',
             'hand': '/usr/share/fonts/truetype/crosextra/Caladea-Italic.ttf',
             'handb': '/usr/share/fonts/truetype/crosextra/Caladea-BoldItalic.ttf'}
    try:
        return ImageFont.truetype(paths[kind], size)
    except OSError:
        return ImageFont.load_default()


def _noise(w, h, cells, seed):
    """Smooth value noise in [0, 1] (bicubic-upsampled lattice)."""
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for o in range(3):
        c = cells * (2 ** o)
        g = (rng.random((max(2, int(c * h / w)) + 1, c + 1)) * 255).astype('uint8')
        out += amp * np.asarray(Image.fromarray(g).resize((w, h), Image.BICUBIC)).astype(float) / 255.0
        tot += amp
        amp *= 0.5
    return out / tot


def _fade(img, seed, grey=(132, 130, 122), k=0.18, warm=(1.0, 0.96, 0.88), dust=0.14):
    import numpy as np
    from PIL import Image
    a = np.asarray(img.convert('RGB')).astype(float)
    a = a * (1 - k) + np.array(grey) * k
    a *= np.array(warm)
    n = _noise(a.shape[1], a.shape[0], 6, seed)
    a = a * (1 - dust * (n[..., None] - 0.5) * 2) + 18 * dust * (n[..., None] > 0.62)
    return Image.fromarray(np.clip(a, 0, 255).astype('uint8'), 'RGB')


def _crooked(stroke, ox, oy, s, sx=None):
    """Mara's tree (art/dl05/build_dl05.py _crooked_tree): a crooked trunk, four branches, a knot in the right one."""
    import build_dl05 as dl05
    dl05._crooked_tree(stroke, ox, oy, s, sx=sx)


def _chalk(size, draw, seed, rough=0.55, blur=0.7):
    """A chalk layer: draw(ImageDraw) onto a white-on-black mask; broken up by grain; returns an 'L' alpha."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    w, h = size
    m = Image.new('L', (w, h), 0)
    draw(ImageDraw.Draw(m))
    m = m.filter(ImageFilter.GaussianBlur(blur))
    rng = np.random.default_rng(seed)
    grain = rng.random((h, w))
    n = _noise(w, h, 24, seed + 1)
    a = np.asarray(m).astype(float) / 255.0
    a = a * np.clip(1.0 - rough * (grain * 0.7 + (1 - n) * 0.6) + 0.35, 0, 1)
    return Image.fromarray(np.clip(a * 255, 0, 255).astype('uint8'), 'L')


def _paint_board(img):
    """The blackboard (1 px = 2.64 mm): slate, old wipes, the date-line rubbed out, the tree half cleaned off, and the
    headcount ON ROLL: 31, 9, 4, each crossed out, then 3, smaller."""
    import numpy as np
    from PIL import Image
    x0, y0, x1, y1 = CELLS['board']
    w, h = x1 - x0, y1 - y0
    n = _noise(w, h, 5, 1501)
    base = np.ones((h, w, 3)) * np.array([30, 38, 34], float)
    base *= (0.85 + 0.3 * n)[..., None]
    # ghosts of wiping: broad arcs of chalk haze
    yy, xx = np.mgrid[0:h, 0:w]
    rnd = random.Random(1502)
    haze = np.zeros((h, w))
    for _ in range(9):
        cx, cy, r = rnd.uniform(0, w), rnd.uniform(-100, h + 100), rnd.uniform(160, 420)
        d = np.abs(np.hypot(xx - cx, (yy - cy) * 1.6) - r)
        haze += np.exp(-(d / rnd.uniform(18, 40)) ** 2) * rnd.uniform(0.05, 0.12)
    haze += 0.05 * _noise(w, h, 3, 1503)
    base = base + haze[..., None] * np.array([150, 156, 150])
    board = Image.fromarray(np.clip(base, 0, 255).astype('uint8'))

    chalk = np.array([214, 214, 204], float)

    def put(alpha, strength=1.0):
        nonlocal board
        a = np.asarray(board).astype(float)
        al = np.asarray(alpha).astype(float)[..., None] / 255.0 * strength
        board = Image.fromarray(np.clip(a * (1 - al) + chalk * al, 0, 255).astype('uint8'))

    # The date-line, top left, rubbed out (smeared, a word or two survive).
    def date(d):
        d.text((26, 14), 'Tuesday 14th   Autumn term', font=_font(40, 'handb'), fill=255)
        d.line((26, 64, 470, 64), fill=200, width=3)
    a = _chalk((w, h), date, 1504)
    an = np.asarray(a).astype(float)
    smear = np.array(Image.fromarray(an.astype('uint8')).resize((w // 8, h), Image.BILINEAR).resize((w, h), Image.BILINEAR)).astype(float)
    keep = 0.04 + 0.2 * np.clip((xx - 40) / 60.0, 0, 1) * np.clip((150 - xx) / 60.0, 0, 1)     # a word just survives
    put(Image.fromarray(np.clip(an * keep + smear * 0.16, 0, 255).astype('uint8')))

    # The tree diagram (the lesson's straight, tall tree), half cleaned off with a cloth.
    def tree(d):
        cx, base_, ht = 300, 420, 300
        d.line((cx, base_, cx, base_ - ht), fill=255, width=7)
        for zf, sp in ((0.4, 0.4), (0.6, 0.3), (0.78, 0.18)):
            yb = base_ - ht * zf
            for s in (-1, 1):
                d.line((cx, yb, cx + s * ht * sp, yb - ht * 0.16), fill=255, width=5)
        d.ellipse((cx - ht * 0.45, base_ - ht * 1.1, cx + ht * 0.45, base_ - ht * 0.52), outline=255, width=6)
        for s in (-1, 0, 1):
            d.line((cx, base_, cx + s * 40, base_ + 24), fill=255, width=5)
        d.text((cx + 150, base_ - ht * 0.95), 'LEAVES', font=_font(30, 'handb'), fill=255)
        d.line((cx + 146, base_ - ht * 0.9, cx + 100, base_ - ht * 0.84), fill=255, width=3)
        d.text((cx + 40, base_ - ht * 0.32), 'TRUNK', font=_font(30, 'handb'), fill=255)
        d.text((cx - 150, base_ - 20), 'ROOTS', font=_font(30, 'handb'), fill=255)
    a = np.asarray(_chalk((w, h), tree, 1505)).astype(float)
    wipe = np.clip(1.0 - 0.92 * np.exp(-((xx - 0.8 * yy) - 150) ** 2 / (2 * 55.0 ** 2)), 0, 1)       # a diagonal cloth swipe
    put(Image.fromarray(np.clip(a * wipe * 0.85, 0, 255).astype('uint8')))

    # ON ROLL: the headcount, falling. Big; each crossed out in turn; the last written smaller.
    def roll(d):
        cx = 820
        d.text((cx, 52), 'ON ROLL', font=_font(54, 'handb'), fill=255, anchor='mm')
        d.line((cx - 120, 86, cx + 120, 84), fill=255, width=4)
        for k, (t, y, sz) in enumerate((('31', 150, 100), ('9', 242, 96), ('4', 330, 92))):
            xo = cx - 46 + 30 * k
            d.text((xo, y), t, font=_font(sz, 'sans-bold'), fill=255, anchor='mm')
            bw = 74 if len(t) > 1 else 52
            d.line((xo - bw, y + 26, xo + bw, y - 20), fill=255, width=6)
        d.text((cx + 72, 404), '3', font=_font(60, 'sans-bold'), fill=255, anchor='mm')
    put(_chalk((w, h), roll, 1506, rough=0.35), 0.98)

    # Odd remnants: a sum, a tick column, a name half wiped, the duster's prints.
    def bits(d):
        d.text((560, 330), '3 + 0 = 3', font=_font(28, 'hand'), fill=255)
        for k in range(5):
            d.line((990, 140 + k * 30, 1000, 152 + k * 30, 1016, 128 + k * 30), fill=255, width=3)
        d.text((80, 360), 'Escorts:  Mr L. / Mrs O.', font=_font(26, 'hand'), fill=255)
    a = np.asarray(_chalk((w, h), bits, 1507)).astype(float) * 0.5
    put(Image.fromarray(a.astype('uint8')))
    img.paste(board, (x0, y0))


def _paint_att(img):
    """The attendance board (1 px = 3.65 mm): CLASS 6 · PRESENT on an enamel strip, three brass-ringed lamp sockets
    (the lamps are their own objects), the three names chalked under them, and nine more sockets plugged and painted over."""
    from PIL import Image, ImageDraw
    import numpy as np
    x0, y0, x1, y1 = CELLS['att']
    w, h = x1 - x0, y1 - y0
    t = Image.new('RGB', (w, h), (36, 58, 46))
    d = ImageDraw.Draw(t)
    d.rectangle((0, 0, w - 1, h - 1), outline=(70, 52, 30), width=8)
    d.rectangle((10, 10, w - 11, 52), fill=(208, 198, 168))
    d.text((w // 2, 32), 'CLASS 6  ·  PRESENT', font=_font(32, 'carlito'), fill=(34, 42, 36), anchor='mm')
    px = lambda x: (x - ATT[0]) / (ATT[1] - ATT[0]) * w
    pz = lambda z: (ATT[3] - z) / (ATT[3] - ATT[2]) * h
    for x in ATT_LAMPS:
        cx, cy = px(x), pz(ATT_LAMP_Z)
        d.ellipse((cx - 25, cy - 25, cx + 25, cy + 25), fill=(150, 116, 56))
        d.ellipse((cx - 19, cy - 19, cx + 19, cy + 19), fill=(18, 16, 14))
    for k in range(9):                                    # the board was built for more: sockets plugged, painted over
        cx, cy = 34 + k * 39.5, pz(1.79)
        d.ellipse((cx - 11, cy - 11, cx + 11, cy + 11), fill=(42, 64, 52), outline=(30, 48, 38), width=2)
    d.rectangle((14, pz(2.04), w - 15, pz(1.88)), fill=(22, 26, 24))      # the slate strip for the names
    sl = _chalk((w, h), lambda dd: [dd.text((px(x), pz(1.96)), nm, font=_font(29, 'handb'), fill=255, anchor='mm')
                                    for x, (_s, _x, nm) in zip(ATT_LAMPS, SEATS)], 1510, rough=0.3)
    ghost = _chalk((w, h), lambda dd: [dd.text((px(x) + 6, pz(1.94)), nm, font=_font(26, 'hand'), fill=255, anchor='mm')
                                       for x, nm in zip(ATT_LAMPS, ('J. KERR', 'P. LOWE', 'A. NYE'))], 1511, rough=0.6)
    a = np.asarray(t).astype(float)
    for al, s in ((ghost, 0.18), (sl, 1.0)):
        m = np.asarray(al).astype(float)[..., None] / 255.0 * s
        a = a * (1 - m) + np.array([220, 218, 206]) * m
    img.paste(_fade(Image.fromarray(np.clip(a, 0, 255).astype('uint8')), 1512, k=0.1, dust=0.16), (x0, y0))


def _paint_pencil(img, name, ground, seed, n_trees, dado_px=None, boards=False, n_big=5, low=False):
    """Mara's crooked trees in pencil (the hide's back wall, the deck's underside); `low`: drawn where a child sat."""
    import numpy as np
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = CELLS[name]
    w, h = x1 - x0, y1 - y0
    n = _noise(w, h, 6, seed)
    a = np.ones((h, w, 3)) * np.array(ground, float) * (0.84 + 0.3 * n)[..., None]
    if dado_px is not None:
        a[dado_px:] = np.array([66, 86, 74], float) * (0.84 + 0.3 * n[dado_px:])[..., None]
        a[dado_px - 3:dado_px + 3] = (70, 52, 34)
    if boards:
        for yy in range(0, h, 15):
            a[yy:yy + 1] *= 0.6
    base = Image.fromarray(np.clip(a, 0, 255).astype('uint8')).convert('RGBA')
    pen = Image.new('RGBA', (w, h), (40, 40, 48, 0))
    d = ImageDraw.Draw(pen)
    rnd = random.Random(seed + 7)

    def tree(ox, oy, s, al, wd):
        def stroke(pts, weight):
            q = [(x + rnd.uniform(-0.8, 0.8), y + rnd.uniform(-0.8, 0.8)) for x, y in pts]
            d.line(q, fill=(34, 34, 44, int(al)), width=max(1, int(wd * (0.6 + weight * 0.6))), joint='curve')
        _crooked(stroke, ox, oy, s, sx=s * rnd.uniform(0.7, 0.9))
    for k in range(n_trees):                                  # spread along the wall, a few big ones traced over and over
        big = k < n_big
        s = (rnd.uniform(0.42, 0.62) if big else rnd.uniform(0.2, 0.36)) * h
        ox = (k + rnd.uniform(0.2, 0.8)) / n_trees * w if not big else (0.1 + 0.2 * k + rnd.uniform(-0.04, 0.04)) * w
        oy = rnd.uniform(0.95 * s, h - 4)
        if low:
            s = rnd.uniform(0.2, 0.3) * h
            oy = h - rnd.uniform(4, 0.18 * h)
        for _p in range(3 if big else 1):
            tree(ox, oy, s, rnd.choice((150, 190, 225)), rnd.uniform(2.0, 3.0) if big else rnd.uniform(1.4, 2.0))
    base.alpha_composite(pen)
    img.paste(base.convert('RGB'), (x0, y0))


def _paint_lid(img):
    """Mara's desk lid: dark varnished pine, ink stains, and her crooked tree cut into it with a compass point."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    x0, y0, x1, y1 = CELLS['lid']
    w, h = x1 - x0, y1 - y0
    n = _noise(w, h, 4, 1520)
    grain = np.sin(np.arange(w)[None, :] * 0.0 + np.arange(h)[:, None] * 0.9 + 6 * n) * 0.06
    a = np.ones((h, w, 3)) * np.array([84, 58, 36], float) * (0.85 + 0.25 * n + grain)[..., None]
    t = Image.fromarray(np.clip(a, 0, 255).astype('uint8'))
    d = ImageDraw.Draw(t, 'RGBA')
    d.ellipse((190, 20, 230, 44), fill=(20, 22, 40, 120))                 # an ink stain
    d.line((6, 6, 60, 10), fill=(150, 116, 76, 160), width=2)              # old scratches
    d.line((170, 110, 240, 104), fill=(150, 116, 76, 120), width=2)
    rnd = random.Random(1521)
    cut = Image.new('L', (w, h), 0)
    dc = ImageDraw.Draw(cut)

    def stroke(pts, weight):
        dc.line(pts, fill=255, width=max(4, int(8 * (0.6 + weight * 0.5))), joint='curve')
    _crooked(stroke, w * 0.46, h * 0.97, h * 0.98, sx=h * 1.35)
    cut = cut.filter(ImageFilter.GaussianBlur(0.6))
    sh = Image.new('L', (w, h), 0)
    sh.paste(cut, (2, 2))
    a = np.asarray(t).astype(float)
    ms = np.asarray(sh).astype(float)[..., None] / 255.0
    mc = np.asarray(cut).astype(float)[..., None] / 255.0
    a = a * (1 - 0.6 * ms)                                                 # the cut's shadowed wall
    a = a * (1 - mc) + np.array([206, 168, 116]) * mc                      # the bright raw wood in the cut
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype('uint8')), (x0, y0))


# Rev 0.3: the shared outside drawing, its own texture (textures/dl15_drawing.png, material Att15Drawing): the sheet,
# the strip torn from a lesson sheet that extends it, and a cork tile for the pinboard.
DRAW_PATH = os.path.join(TEX, 'dl15_drawing.png')
DCELLS = {'dw_sheet': (0, 0, 512, 384), 'dw_strip': (0, 384, 342, 504), 'dw_cork': (352, 392, 512, 512)}
SHEET = (0.6, 0.45)                    # the drawing's sheet, w x h (m)
STRIP = (0.4, 0.14, 0.12, 0.02)        # the strip: w, h, its left edge's x on the sheet, how far it tucks under the sheet


def dcell_uv(name):
    x0, y0, x1, y1 = DCELLS[name]
    return x0 / 512, 1 - y1 / 512, x1 / 512, 1 - y0 / 512


def strip_edge(t):
    """The strip's torn top edge: its height (fraction of STRIP h) at t (0..1 along it)."""
    return 0.86 + 0.06 * math.sin(t * 23.0 + 1.0) + 0.04 * math.sin(t * 61.0) + 0.05 * (1 - t) * (t < 0.3)


def make_drawing(path):
    """Three children under a tree too big for the sheet (1 px = 1 mm while painting): wax crayon on buff sugar paper.
    The tree is Mara's, crooked, the knot in its branch; it goes off the top, and the crown goes on over a strip torn
    from a lesson sheet (printed ruled lines and a line of the lesson), tucked under the top edge and taped. Under
    the tree, holding hands, R.A., M (in her boots) and T.O.; a sun; grass."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    W, Hs = int(SHEET[0] * 1000), int(SHEET[1] * 1000)
    sw, sh, sx, tuck = (int(v * 1000) for v in STRIP)
    top = sh - tuck                                                  # the sheet's top edge on the canvas
    H = top + Hs
    rng = np.random.default_rng(1600)
    canvas = np.zeros((H, W, 3))
    # the papers: the lesson strip (white, ruled, printed), the sheet (buff sugar paper)
    n = _noise(W, H, 6, 1601)
    strip = Image.new('RGB', (sw, sh), (226, 224, 212))
    ds = ImageDraw.Draw(strip)
    for y in range(18, sh, 11):
        ds.line((0, y, sw, y), fill=(150, 170, 200), width=1)
    ds.line((22, 0, 22, sh), fill=(200, 120, 120), width=1)
    ds.text((30, 14), 'LESSON 6   Living things', font=_font(15, 'serif'), fill=(70, 70, 76), anchor='lb')
    ds.text((30, 36), '4.  The tree grows straight and tall toward the', font=_font(13, 'serif'), fill=(80, 80, 86), anchor='lb')
    ds.text((30, 58), '     light. Draw the tree in the box below.', font=_font(13, 'serif'), fill=(80, 80, 86), anchor='lb')
    ds.text((30, 102), '5.  Name the three parts of a tree:', font=_font(13, 'serif'), fill=(80, 80, 86), anchor='lb')
    canvas[:sh, sx:sx + sw] = np.asarray(strip).astype(float)
    paper = np.ones((Hs, W, 3)) * np.array([206, 190, 150], float)
    paper *= (0.9 + 0.16 * n[top:, :])[..., None]
    paper += (rng.random((Hs, W)) * 10 - 5)[..., None]
    canvas[top:] = paper
    img = Image.fromarray(np.clip(canvas, 0, 255).astype('uint8')).convert('RGBA')
    rnd = random.Random(1602)

    def crayon(paint, rgb, seed, grain=0.45, alpha=0.92):
        """A wax-crayon layer: paint(draw) onto a mask; the paper's tooth shows through."""
        m = Image.new('L', (W, H), 0)
        paint(ImageDraw.Draw(m))
        m = m.filter(ImageFilter.GaussianBlur(0.8))
        g = np.random.default_rng(seed).random((H, W))
        tooth = np.clip(1.0 - grain * (g ** 2) * 1.6, 0, 1)
        a = np.asarray(m).astype(float) / 255.0 * tooth * alpha
        lay = np.zeros((H, W, 4))
        lay[..., :3] = rgb
        lay[..., 3] = a * 255
        img.alpha_composite(Image.fromarray(np.clip(lay, 0, 255).astype('uint8'), 'RGBA'))

    def scribble(d, x0, y0, x1, y1, step=7, wd=7, slant=0.3):
        """Back-and-forth crayon filling a box."""
        y = y0
        while y < y1:
            d.line((x0 + rnd.uniform(-4, 4), y, x1 + rnd.uniform(-4, 4), y + slant * (x1 - x0) * 0.1 + rnd.uniform(-3, 3)), fill=255, width=wd)
            y += step
    ground = H - 70
    # sky: blue crayon across the sheet's top, scribbled, and on round behind the crown
    crayon(lambda d: scribble(d, 0, top + 4, W, top + 110, step=9, wd=8), (92, 136, 196), 1603, alpha=0.75)
    # the sun, top right, with rays
    def sun(d):
        cx, cy = W - 70, top + 70
        d.ellipse((cx - 38, cy - 38, cx + 38, cy + 38), fill=255)
        for k in range(12):
            a = 2 * math.pi * k / 12
            d.line((cx + 48 * math.cos(a), cy + 48 * math.sin(a), cx + 66 * math.cos(a), cy + 66 * math.sin(a)), fill=255, width=7)
    crayon(sun, (236, 190, 40), 1604)
    # grass, and a path of brown
    crayon(lambda d: scribble(d, 0, ground - 10, W, H, step=8, wd=9), (70, 140, 60), 1605)
    def blades(d):
        for x in range(0, W, 9):
            h_ = rnd.uniform(14, 34)
            d.line((x, ground, x + rnd.uniform(-6, 6), ground - h_), fill=255, width=4)
    crayon(blades, (52, 118, 46), 1606)
    # the tree: crooked, enormous, off the top of the sheet and on up the strip
    tx, tbase = 200, ground + 8
    def trunk(d):
        def stroke(pts, weight):
            d.line(pts, fill=255, width=int(14 + 26 * weight), joint='curve')
        import build_dl05 as dl05
        dl05._crooked_tree(stroke, tx, tbase, 640, sx=560)
    crayon(trunk, (104, 66, 36), 1607, grain=0.35)
    tips = [(tx + ux * 560, tbase + uy * 640) for ux, uy in ((-0.33, -0.66), (0.03, -0.9), (0.43, -0.78), (-0.15, -0.75),
                                                             (0.2, -0.7), (0.24, -0.3), (-0.05, -0.55))]
    def crown(d):
        for k in range(30):                                        # leafy loops round the branch ends
            bx, by = tips[k % len(tips)]
            cx, cy = bx + rnd.uniform(-50, 50), by + rnd.uniform(-45, 40)
            r = rnd.uniform(36, 66)
            pts = [(cx + r * math.cos(a) * rnd.uniform(0.85, 1.1), cy + r * 0.8 * math.sin(a) * rnd.uniform(0.85, 1.1))
                   for a in [j * 0.5 for j in range(14)]]
            d.line(pts, fill=255, width=7, joint='curve')
    crayon(crown, (54, 128, 58), 1608, alpha=0.88)
    crayon(lambda d: [d.ellipse((x - 9, y - 9, x + 9, y + 9), fill=255) for x, y in
                      [(bx + rnd.uniform(-40, 40), by + rnd.uniform(-30, 30)) for bx, by in tips for _ in range(2)]], (200, 56, 44), 1609)   # apples
    # the three, holding hands under it: R.A. (tall, blue jumper), M (smaller, red, in boots), T.O. (green, a cap)
    people = ((340, 160, (60, 90, 170), 'R.A.', 'hair'), (425, 128, (196, 60, 52), 'M', 'plaits'), (505, 150, (60, 140, 76), 'T.O.', 'cap'))
    feet = ground + 30
    for k, (cx, ht, col, name, head) in enumerate(people):
        hy = feet - ht
        def body(d, cx=cx, ht=ht, hy=hy):
            d.polygon([(cx - 22, hy + 30), (cx + 22, hy + 30), (cx + 28, hy + ht * 0.62), (cx - 28, hy + ht * 0.62)], fill=255)
        crayon(body, col, 1610 + k)
        def limbs(d, cx=cx, ht=ht, hy=hy):
            d.line((cx - 10, hy + ht * 0.62, cx - 14, feet - 4), fill=255, width=7)
            d.line((cx + 10, hy + ht * 0.62, cx + 14, feet - 4), fill=255, width=7)
            d.line((cx - 22, hy + 36, cx - 44, hy + ht * 0.5), fill=255, width=6)
            d.line((cx + 22, hy + 36, cx + 44, hy + ht * 0.5), fill=255, width=6)
            d.ellipse((cx - 17, hy - 4, cx + 17, hy + 30), outline=255, width=5)
        crayon(limbs, (40, 34, 30), 1620 + k, grain=0.3)
        if head == 'plaits':
            crayon(lambda d, cx=cx, hy=hy: [d.line((cx + s * 16, hy + 6, cx + s * 24, hy + 34), fill=255, width=7) for s in (-1, 1)],
                   (120, 74, 34), 1630)
            crayon(lambda d, cx=cx: [d.rounded_rectangle((cx + s * 14 - 12 + (6 if s > 0 else -6), feet - 18, cx + s * 14 + 12 + (10 if s > 0 else -10), feet + 2),
                                                         radius=4, fill=255) for s in (-1, 1)], (110, 70, 36), 1631)   # her boots
        elif head == 'cap':
            crayon(lambda d, cx=cx, hy=hy: d.chord((cx - 19, hy - 12, cx + 19, hy + 18), 180, 360, fill=255), (196, 150, 40), 1632)
        else:
            crayon(lambda d, cx=cx, hy=hy: d.arc((cx - 18, hy - 6, cx + 18, hy + 20), 180, 360, fill=255, width=8), (60, 40, 24), 1633)
        crayon(lambda d, cx=cx, hy=hy, name=name: d.text((cx, hy - 26), name, font=_font(28, 'handb'), fill=255, anchor='mm'), (40, 36, 60), 1640 + k, grain=0.25)
    crayon(lambda d: [d.line((people[k][0] + 44, feet - people[k][1] * 0.5, people[k + 1][0] - 44, feet - people[k + 1][1] * 0.5), fill=255, width=6)
                      for k in range(2)], (40, 34, 30), 1650)        # holding hands
    # the tape over the join (yellowed, see-through), on the sheet's face and over the strip
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    for x0_ in (sx + 18, sx + sw * 0.45, sx + sw - 70):
        dl.polygon([(x0_, top - 26), (x0_ + 56, top - 30), (x0_ + 58, top + 26), (x0_ + 2, top + 30)], fill=(236, 214, 140, 105))
    img.alpha_composite(lay)
    out = Image.new('RGB', (512, 512), (60, 58, 54))
    sheet = img.crop((0, top, W, H)).convert('RGB').resize((512, 384), Image.LANCZOS)
    out.paste(_fade(sheet, 1660, k=0.12, dust=0.12), (0, 0))
    st = img.crop((sx, 0, sx + sw, sh)).convert('RGB').resize((342, 120), Image.LANCZOS)
    out.paste(_fade(st, 1661, k=0.1, dust=0.1), (0, 384))
    # cork
    cn = _noise(160, 120, 10, 1662)
    ck = np.ones((120, 160, 3)) * np.array([150, 108, 66], float) * (0.75 + 0.4 * cn)[..., None]
    ck *= (0.85 + 0.3 * rng.random((120, 160)))[..., None]
    out.paste(Image.fromarray(np.clip(ck, 0, 255).astype('uint8')), (352, 392))
    out.save(path, optimize=True)


def make_atlas(path):
    from PIL import Image, ImageDraw, ImageFilter
    os.makedirs(TEX, exist_ok=True)
    img = Image.new('RGB', (ATLAS, ATLAS), (60, 58, 54))
    ink, cream, green = (30, 28, 24), (214, 204, 176), (40, 64, 50)
    _paint_board(img)
    _paint_att(img)
    # Rev 0.3: the refuge has moved to DL-14; here, a few of her trees, low on the wall where she sat, and over her head.
    _paint_pencil(img, 'pencil', (140, 132, 116), 1530, 6, dado_px=int((1.48 - 1.0) / 1.46 * 264), n_big=0, low=True)
    _paint_pencil(img, 'under', (150, 120, 84), 1531, 5, boards=True, n_big=2)
    _paint_lid(img)

    def enamel(name, lines, bg, fg, border=True, seed=0):
        x0, y0, x1, y1 = CELLS[name]
        w, h = x1 - x0, y1 - y0
        p = Image.new('RGB', (w, h), bg)
        dp = ImageDraw.Draw(p)
        if border:
            dp.rounded_rectangle((4, 4, w - 5, h - 5), radius=10, outline=fg, width=max(3, h // 24))
        for text, size, yf, kind in lines:
            dp.text((w // 2, int(h * yf)), text, font=_font(size, kind), fill=fg, anchor='mm')
        img.paste(_fade(p, 1540 + seed, k=0.12, dust=0.16), (x0, y0))
    enamel('liftsign', (('PUPIL LIFT', 66, 0.34, 'carlito'), ('NO PUPIL UNACCOMPANIED', 40, 0.74, 'carlito')), (208, 198, 168), green, seed=1)
    enamel('dismiss', (('DISMISSAL', 46, 0.53, 'carlito'),), green, cream, seed=2)
    enamel('sickbay', (('SICK BAY', 46, 0.53, 'carlito'),), (122, 38, 30), (226, 214, 190), seed=3)
    enamel('class6', (('CLASS 6', 40, 0.53, 'carlito'),), (40, 56, 78), cream, seed=4)
    enamel('lpupil', (('PUPIL', 20, 0.55, 'carlito'),), (26, 24, 20), (196, 232, 200), border=False, seed=5)
    enamel('lescort', (('ESCORT', 20, 0.55, 'carlito'),), (26, 24, 20), (236, 190, 110), border=False, seed=6)
    # The sick bay's protocol notice (the protective era): small print, the heading readable.
    x0, y0, x1, y1 = CELLS['notice']
    p = Image.new('RGB', (x1 - x0, y1 - y0), (206, 198, 172))
    dp = ImageDraw.Draw(p)
    dp.rectangle((3, 3, x1 - x0 - 4, y1 - y0 - 4), outline=(122, 38, 30), width=4)
    dp.text(((x1 - x0) // 2, 22), 'PROTECTED PUPILS', font=_font(24, 'carlito'), fill=(122, 38, 30), anchor='mm')
    for k, s in enumerate(('are not to be left alone', 'in the sick bay. An escort', 'stays until collected.')):
        dp.text(((x1 - x0) // 2, 46 + k * 16), s, font=_font(15, 'carlito'), fill=ink, anchor='mm')
    img.paste(_fade(p, 1547, k=0.14, dust=0.2), (x0, y0))
    # The name cards in the desks' brass holders: chalk on a black card.
    for k, (_s, _x, nm) in enumerate(SEATS):
        x0, y0, x1, y1 = CELLS['name%d' % (k + 1)]
        w, h = x1 - x0, y1 - y0
        import numpy as np
        al = np.asarray(_chalk((w, h), lambda dd: dd.text((w // 2, h // 2 + 1), nm, font=_font(34, 'handb'), fill=255, anchor='mm'),
                               1550 + k, rough=0.25)).astype(float)[..., None] / 255.0
        a = np.ones((h, w, 3)) * np.array([24, 26, 26], float) * (1 - al) + np.array([226, 224, 214]) * al
        img.paste(Image.fromarray(np.clip(a, 0, 255).astype('uint8')), (x0, y0))
    # The Steward, as DL-13 hangs him (cropped from its atlas when it is there), and his brass plate.
    x0, y0, x1, y1 = CELLS['portrait']
    src = os.path.join(TEX, 'dl13_atlas.png')
    if os.path.exists(src):
        s = Image.open(src).convert('RGB')
        img.paste(s.crop((768, 720, 896, 880)), (x0, y0))
        img.paste(s.crop((896, 720, 1024, 752)), CELLS['stewplate'][:2])
    else:
        ImageDraw.Draw(img).rectangle((x0, y0, x1 - 1, y1 - 1), fill=(150, 142, 120))
        ImageDraw.Draw(img).rectangle(CELLS['stewplate'][:2] + (CELLS['stewplate'][2] - 1, CELLS['stewplate'][3] - 1), fill=(120, 92, 44))
    # The register, open: columns of ticks thinning to three.
    x0, y0, x1, y1 = CELLS['register']
    rg = Image.new('RGB', (x1 - x0, y1 - y0), (204, 196, 172))
    dr = ImageDraw.Draw(rg)
    dr.line((64, 0, 64, 96), fill=(140, 130, 110), width=2)
    rnd = random.Random(1560)
    for yy in range(10, 96, 6):
        dr.line((4, yy, 124, yy), fill=(170, 176, 190), width=1)
    for row in range(14):
        yy = 12 + row * 6
        dr.line((6, yy - 2, 6 + rnd.randint(14, 30), yy - 2), fill=(60, 60, 90), width=1)
        for col in range(12):
            if rnd.random() < max(0.0, 0.95 - col * 0.085) or (row < 3 and col == 11):
                xx = 40 + col * 7 + (8 if col > 2 else 0)
                dr.line((xx, yy - 2, xx + 1, yy, xx + 4, yy - 5), fill=(50, 50, 80), width=1)
    img.paste(rg, (x0, y0))
    # The biscuit tin's lid, an exercise book, a stopped clock face.
    x0, y0, x1, y1 = CELLS['tin']
    tn = Image.new('RGB', (x1 - x0, y1 - y0), (58, 82, 110))
    dt = ImageDraw.Draw(tn)
    dt.ellipse((14, 8, 114, 64), fill=(196, 180, 140), outline=(150, 120, 60), width=4)
    dt.text((64, 30), 'ASSORTED', font=_font(15, 'carlito'), fill=(90, 40, 34), anchor='mm')
    for k in range(5):
        dt.ellipse((30 + k * 15, 42, 40 + k * 15, 52), fill=(160, 70, 60))
    img.paste(_fade(tn, 1561, k=0.25, dust=0.25), (x0, y0))
    x0, y0, x1, y1 = CELLS['book']
    bk = Image.new('RGB', (x1 - x0, y1 - y0), (100, 124, 96))
    db = ImageDraw.Draw(bk)
    db.rectangle((8, 8, 88, 34), fill=(214, 206, 182))
    db.text((48, 21), 'EXERCISE', font=_font(13, 'carlito'), fill=ink, anchor='mm')
    db.text((14, 54), 'M. D.  Class 6', font=_font(13, 'hand'), fill=(40, 40, 70), anchor='lm')
    img.paste(_fade(bk, 1562, k=0.2), (x0, y0))
    x0, y0, x1, y1 = CELLS['clock']
    ck = Image.new('RGB', (x1 - x0, y1 - y0), (40, 34, 26))
    dk = ImageDraw.Draw(ck)
    dk.ellipse((2, 2, 69, 69), fill=(214, 208, 190), outline=(24, 22, 18), width=3)
    for k in range(12):
        a = math.radians(k * 30)
        dk.line((36 + 27 * math.sin(a), 36 - 27 * math.cos(a), 36 + 32 * math.sin(a), 36 - 32 * math.cos(a)), fill=ink, width=2)
    for ang, ln, wd in ((math.radians(3 * 30 + 12), 17, 4), (math.radians(25 * 6), 27, 2)):
        dk.line((36, 36, 36 + ln * math.sin(ang), 36 - ln * math.cos(ang)), fill=ink, width=wd)
    img.paste(ck, (x0, y0))
    # The blanket: grey army wool, a faded red stripe near the hem.
    x0, y0, x1, y1 = CELLS['blanket']
    import numpy as np
    w, h = x1 - x0, y1 - y0
    n = _noise(w, h, 3, 1563)
    bl = np.ones((h, w, 3)) * np.array([92, 92, 98], float) * (0.82 + 0.36 * n)[..., None]
    bl[h - 14:h - 8] = np.array([120, 50, 44], float)
    img.paste(Image.fromarray(np.clip(bl, 0, 255).astype('uint8')), (x0, y0))
    for name, rgb in SWATCH.items():
        x0, y0, x1, y1 = CELLS[name]
        ImageDraw.Draw(img).rectangle((x0, y0, x1 - 1, y1 - 1), fill=rgb)
    img.filter(ImageFilter.GaussianBlur(0.35)).save(path, optimize=True)


# =====================================================================================================================
# Mesh building (as art/ch1/dl14.py's MB)
# =====================================================================================================================
class MB:
    """One object being built: faces tagged by material name. Faces flagged 'flat' keep the winding they were built
    with (decals and cloth, one-sided in the game); the rest have their normals recalculated outward."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.flat = self.bm.faces.layers.int.new('flat')
        self.names = []

    def __call__(self, name):                 # voice_props' target protocol: name -> slot index, and .bm
        return self.m(name)

    def m(self, name):
        if name not in self.names:
            self.names.append(name)
        return self.names.index(name)

    def mark(self):
        """The verts so far (a set: BMesh's pool doesn't keep creation order, so a count can't mark a place)."""
        return set(self.bm.verts)

    def since(self, n0):
        return [v for v in self.bm.verts if v not in n0]

    def xform(self, n0, M):
        for v in self.since(n0):
            v.co = M @ v.co

    def paint(self, verts, cell):
        uv = cell_mid(cell)
        faces = set()
        for v in verts:
            faces.update(v.link_faces)
        for f in faces:
            for lp in f.loops:
                lp[self.uv].uv = uv

    def box(self, mt, x0, x1, y0, y1, z0, z1, rot=None, cell=None):
        vs = add_box(self.bm, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), mat=self.m(mt), rot=rot)
        if cell:
            self.paint(vs, cell)
        return vs

    def sbox(self, cell, x0, x1, y0, y1, z0, z1, rot=None):
        """A box painted with one atlas swatch."""
        return self.box(ATLAS_MAT, x0, x1, y0, y1, z0, z1, rot=rot, cell=cell)

    def cbox(self, mt, c, size, rot=None, cell=None):
        vs = add_box(self.bm, c, size, mat=self.m(mt), rot=rot)
        if cell:
            self.paint(vs, cell)
        return vs

    def cyl(self, mt, a, b, r, r2=None, seg=10, cell=None):
        vs = add_cyl(self.bm, a, b, r, r2, mat=self.m(mt), seg=seg)
        if cell:
            self.paint(vs, cell)
        return vs

    def sphere(self, mt, c, r, seg=10, scale=(1, 1, 1), cell=None):
        vs = add_sphere(self.bm, c, r, mat=self.m(mt), seg=seg, scale=scale)
        if cell:
            self.paint(vs, cell)
        return vs

    def torus(self, mt, c, axis, R, r, seg=20, rseg=6, cell=None):
        vs = add_torus(self.bm, c, axis, R, r, mat=self.m(mt), seg=seg, rseg=rseg)
        if cell:
            self.paint(vs, cell)
        return vs

    def face(self, mt, corners, uvs=None, flat=True):
        f = self.bm.faces.new([self.bm.verts.new(c) for c in corners])
        f.material_index = self.m(mt)
        f[self.flat] = 1 if flat else 0
        if uvs:
            for lp, t in zip(f.loops, uvs):
                lp[self.uv].uv = t
        return f

    def decal(self, x0, x1, z0, z1, y, cell, mt=ATLAS_MAT, uvr=None):
        """A picture on a wall, facing the camera (-y)."""
        u0, v0, u1, v1 = uvr or cell_uv(cell)
        return self.face(mt, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    def tbox(self, x0, x1, y0, y1, z0, z1, cells, mt=ATLAS_MAT):
        """A box with an atlas cell per face: cells = {'-y','+y','-x','+x','+z','-z', 'all'}."""
        P = {
            '-y': [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)],
            '+y': [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)],
            '-x': [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)],
            '+x': [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
            '+z': [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)],
            '-z': [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)],
        }
        n0 = self.mark()
        for k, pts in P.items():
            c = cells.get(k, cells.get('all'))
            u0, v0, u1, v1 = cell_uv(c)
            if c.startswith('sw_'):
                u0 = u1 = (u0 + u1) / 2
                v0 = v1 = (v0 + v1) / 2
            self.face(mt, pts, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
        return n0

    def prism_yz(self, mt, pts, x0, x1, cell=None):
        """A polygon in (y, z), extruded from x0 to x1 (closed; normals recalculated)."""
        bm = self.bm
        f = [bm.verts.new((x0, y, z)) for y, z in pts]
        b = [bm.verts.new((x1, y, z)) for y, z in pts]
        fs = [bm.faces.new(f), bm.faces.new(list(reversed(b)))]
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            fs.append(bm.faces.new((f[j], f[i], b[i], b[j])))
        for fc in fs:
            fc.material_index = self.m(mt)
        if cell:
            self.paint(f + b, cell)
        return f + b

    def obj(self, name, coll, origin=(0.0, 0.0, 0.0), sharp=35):
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if not f[self.flat]])
        o = Vector(origin)
        if o.length:
            bmesh.ops.translate(bm, verts=bm.verts, vec=-o)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for n in self.names:
            me.materials.append(mat(n))
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        me.set_sharp_from_angle(angle=math.radians(sharp))
        ob = bpy.data.objects.new(name, me)
        ob.location = o
        coll.objects.link(ob)
        return ob


def Rz(a, about=(0, 0, 0)):
    p = Vector(about)
    return Matrix.Translation(p) @ Matrix.Rotation(a, 4, 'Z') @ Matrix.Translation(-p)


def Rx(a):
    return Matrix.Rotation(a, 4, 'X')


def wall(B, x0, x1, y0, y1, z0, z1, dado=1.0):
    """A plastered wall slab: dado paint below `dado`, plaster above."""
    if z0 < dado < z1:
        B.box('LessonDado', x0, x1, y0, y1, z0, dado)
        B.box('LessonPlaster', x0, x1, y0, y1, dado, z1)
    else:
        B.box('LessonDado' if z1 <= dado else 'LessonPlaster', x0, x1, y0, y1, z0, z1)


def trims(B, x0, x1, y, face=-1, rail=True):
    """Skirting and a dado rail along a wall face at y (the room on the -y side when face is -1)."""
    s = face
    B.box('PigeonWood', x0, x1, min(y, y + s * 0.02), max(y, y + s * 0.02), 0.0, 0.12)
    if rail:
        B.box('CrateWood', x0, x1, min(y, y + s * 0.03), max(y, y + s * 0.03), 0.98, 1.03)


# =====================================================================================================================
# The room's shell
# =====================================================================================================================
def build_shell(B):
    lx0, lx1, ly0, ly1, ltop = LIFT
    ax0, ax1, ay = ALCOVE
    # Floor: timber, top 0; the lift's pit (its deck's depth) at 251.4..252.4.
    B.box('CrateWood', X0, lx0, -1.6, BACK_Y + BACK_T, -0.2, 0.0)
    B.box('CrateWood', lx1, X1, -1.6, BACK_Y + BACK_T, -0.2, 0.0)
    B.box('CrateWood', lx0, lx1, -1.6, ly0, -0.2, 0.0)
    B.box('CrateWood', lx0, lx1, ly1, BACK_Y + BACK_T, -0.2, 0.0)
    B.box('CrateWood', lx0, lx1, ly0, ly1, -0.2, -LIFT_T)
    B.box('CrateWood', ax0 - 0.15, ax1 + 0.15, BACK_Y + BACK_T, ay + 0.15, -0.2, 0.0)
    for a, b, c, d in ((lx0, lx0 + 0.03, ly0, ly1), (lx1 - 0.03, lx1, ly0, ly1), (lx0, lx1, ly0, ly0 + 0.03), (lx0, lx1, ly1 - 0.03, ly1)):
        B.box('WornIron', a, b, c, d, -LIFT_T, 0.0)                         # the pit's iron kerb
    y = -1.5
    while y < ay:                                                            # board seams
        if y < BACK_Y:
            runs = [(LWALL[1], lx0), (lx1, PART[0])] if ly0 < y < ly1 else [(LWALL[1], PART[0])]
        else:
            runs = [(ax0, ax1)]
        for a, b in runs:
            B.box('PigeonWood', a, b, y - 0.004, y + 0.004, 0.0, 0.002)
        y += 0.16
    # The back wall, with the hatch: 248.0..252.6, then the alcove's mouth, then 257.25..263.9.
    hx0, hx1, hz0, hz1 = HATCH
    yb0, yb1 = BACK_Y, BACK_Y + BACK_T
    wall(B, X0, hx0, yb0, yb1, 0.0, CEIL)
    wall(B, hx1, ax0, yb0, yb1, 0.0, CEIL)
    wall(B, hx0, hx1, yb0, yb1, 0.0, hz0)
    wall(B, hx0, hx1, yb0, yb1, hz1, CEIL)
    wall(B, ax1, PART[1], yb0, yb1, 0.0, CEIL)
    B.box('LessonPlaster', ax0, ax1, yb0, yb1, 3.2, CEIL)                    # the alcove's lintel
    B.box('PigeonWood', ax0, ax1, yb0 - 0.03, yb0, 3.14, 3.2)
    # The alcove: its two returns and its back wall, into the dark.
    wall(B, ax0 - 0.15, ax0, yb1, ay + 0.15, 0.0, CEIL)
    wall(B, ax1, ax1 + 0.15, yb1, ay + 0.15, 0.0, CEIL)
    wall(B, ax0, ax1, ay, ay + 0.15, 0.0, CEIL)
    B.box('LessonPlaster', ax0 - 0.15, ax1 + 0.15, yb0, ay + 0.15, CEIL, CEIL + 0.15)
    trims(B, ax0, ax1, ay)
    # On the alcove's back wall: the pale patches where the pupils' work hung, two sheets left, curling; one fallen.
    rnd = random.Random(1580)
    for k in range(11):
        x = ax0 + 0.25 + k * 0.4 + rnd.uniform(-0.04, 0.04)
        z = 1.42 + rnd.uniform(-0.05, 0.05) + (0.32 if k % 2 else 0.0)
        cell = 'sw_pages' if k in (3, 8) else 'sw_pale'
        B.decal(x - 0.15, x + 0.15, z, z + 0.22, ay - 0.002, cell)
        if k in (3, 8):
            B.cyl(ATLAS_MAT, (x, ay, z + 0.2), (x, ay - 0.008, z + 0.2), 0.006, seg=6, cell='sw_brass')
    B.sbox('sw_pages', 255.1, 255.4, 3.65, 3.87, 0.0, 0.003)
    for x, s in ((ax0, 1), (ax1, -1)):
        B.box('PigeonWood', min(x, x + s * 0.02), max(x, x + s * 0.02), yb1, ay, 0.0, 0.12)
        B.box('CrateWood', min(x, x + s * 0.03), max(x, x + s * 0.03), yb0, ay, 0.98, 1.03)
    # The left wall (its face 248.15) and the ceiling, with a plaster cornice along the back.
    wall(B, LWALL[0], LWALL[1], FRONT_Y, yb0, 0.0, CEIL)
    B.box('LessonPlaster', X0, PART[1], FRONT_Y, yb1, CEIL, CEIL + 0.15)
    B.box('LessonPlaster', X0, ax0, yb0 - 0.1, yb0, CEIL - 0.08, CEIL)
    B.box('LessonPlaster', ax1, PART[0], yb0 - 0.1, yb0, CEIL - 0.08, CEIL)
    # Skirting and dado rail along the back wall (the hide's stretch is the hide's wall: it keeps them too).
    trims(B, LWALL[1], ax0, yb0)
    trims(B, ax1, PART[0], yb0)
    # The sick bay's own rail, at its child's height over the deck.
    B.box('PigeonWood', LWALL[1], BAL[1], yb0 - 0.03, yb0, 2.55, 2.6)
    # The duct behind the hatch: a dark box (Blender y 1.4..2.6), open to the left where it runs on toward DL-14.
    B.sbox('sw_dark', 247.85, hx1 + 0.1, yb1, DUCT_Y[1], hz0 - 0.1, hz0)
    B.sbox('sw_dark', 247.85, hx1 + 0.1, yb1, DUCT_Y[1], hz1, hz1 + 0.1)
    B.sbox('sw_dark', 247.85, hx1 + 0.1, DUCT_Y[1], DUCT_Y[1] + 0.1, hz0 - 0.1, hz1 + 0.1)
    B.sbox('sw_dark', hx1, hx1 + 0.1, yb1, DUCT_Y[1], hz0, hz1)
    # The hatch's iron frame and its door, hanging open inward against the duct's right side.
    for a, b, c, d in ((hx0 - 0.05, hx0, hz0 - 0.03, hz1 + 0.05), (hx1, hx1 + 0.05, hz0 - 0.03, hz1 + 0.05),
                       (hx0 - 0.05, hx1 + 0.05, hz1, hz1 + 0.05), (hx0 - 0.05, hx1 + 0.05, hz0 - 0.03, hz0 + 0.005)):
        B.box('WornIron', a, b, yb0 - 0.025, yb0, c, d)
    B.box('PigeonWood', hx1 - 0.035, hx1 - 0.005, yb1 + 0.02, yb1 + 0.8, hz0 + 0.02, hz1 - 0.02)
    B.box('WornIron', hx1 - 0.04, hx1 - 0.0, yb1 + 0.1, yb1 + 0.16, hz0 + 0.15, hz0 + 0.25)


def build_rails(B, x0, x1, z, stop_left=False, stop_right=False, channel=True):
    """The figures' rail: a timber channel and two low iron rails at y 0.47 / 0.63, rail top z + 0.03."""
    if channel:
        B.box('PigeonWood', x0, x1, CHAN[0], CHAN[1], z - 0.002, z + 0.003)
    for s in (-1, 1):
        y = RAIL_Y + s * RAIL_G
        B.box('WornIron', x0, x1, y - 0.012, y + 0.012, z, z + 0.008)
        B.box('WornIron', x0, x1, y - 0.005, y + 0.005, z + 0.008, z + 0.024)
        B.box('WornIron', x0, x1, y - 0.009, y + 0.009, z + 0.024, z + RAIL_H)
    for x, on in ((x0, stop_left), (x1, stop_right)):
        if on:
            s = 1 if x == x0 else -1
            B.box('WornIron', min(x, x + s * 0.08), max(x, x + s * 0.08), RAIL_Y - 0.11, RAIL_Y + 0.11, z, z + 0.12)
            B.box('CrateWood', min(x + s * 0.08, x + s * 0.1), max(x + s * 0.08, x + s * 0.1), RAIL_Y - 0.09, RAIL_Y + 0.09, z + 0.03, z + 0.1)


# =====================================================================================================================
# The sick bay balcony
# =====================================================================================================================
def build_balcony(B):
    x0, x1, y0, y1, top = BAL
    B.box('CrateWood', x0, x1, y0, y1, top - 0.04, top)                    # the deck
    y = y0 + 0.14
    while y < y1 - 0.05:
        B.box('PigeonWood', x0, x1, y - 0.004, y + 0.004, top, top + 0.002)
        y += 0.14
    for x in (248.2, 248.85, 249.5, 250.15, 250.8, 251.35):                 # iron joists under it
        B.box('WornIron', x - 0.025, x + 0.025, y0, y1, BAL_UNDER, top - 0.04)
    B.box('WornIron', x0, x1, y0, y0 + 0.06, BAL_UNDER, top)                 # the front beam, a channel
    B.box('WornIron', x0, x1, y0 - 0.01, y0, BAL_UNDER - 0.005, top - 0.01)
    B.box('WornIron', x0, x1, BLANKET_Y - 0.03, BLANKET_Y + 0.03, BAL_UNDER, top - 0.04)   # the cross beam over the blanket
    B.box('WornIron', x1 - 0.04, x1, y0, y1, BAL_UNDER, top)                 # the right end's edge angle
    B.box('WornIron', x0, x1, y1 - 0.04, y1, BAL_UNDER - 0.06, top - 0.04)  # the ledger on the wall
    for x in (248.27, 251.29):                                               # two slim columns, in front of the lane
        B.cyl('WornIron', (x, -0.36, 0.0), (x, -0.36, BAL_UNDER), 0.032, seg=10)
        B.box('WornIron', x - 0.07, x + 0.07, -0.43, -0.31, 0.0, 0.02)
        B.box('WornIron', x - 0.06, x + 0.06, -0.42, -0.24, BAL_UNDER - 0.03, BAL_UNDER)
        B.cyl('WornIron', (x, -0.36, BAL_UNDER - 0.3), (x + (0.25 if x < 250 else -0.25), -0.3, BAL_UNDER - 0.02), 0.012, seg=6)
    build_rails(B, BAL_STUB[0], BAL_STUB[1], top, stop_left=True)
    # The sick bay: a child's cot at the back, a folding screen, a basin that drips, the notices.
    cx0, cx1, cy0, cy1 = COT
    z = top
    for x in (cx0 + 0.02, cx1 - 0.02):
        for yy in (cy0 + 0.02, cy1 - 0.02):
            B.cyl(ATLAS_MAT, (x, yy, z), (x, yy, z + (0.78 if x < 250 else 0.66)), 0.016, seg=8, cell='sw_enamel')
        hb = 0.78 if x < 250 else 0.66
        B.cyl(ATLAS_MAT, (x, cy0 + 0.02, z + hb - 0.02), (x, cy1 - 0.02, z + hb - 0.02), 0.014, seg=8, cell='sw_enamel')
        B.cyl(ATLAS_MAT, (x, cy0 + 0.02, z + 0.3), (x, cy1 - 0.02, z + 0.3), 0.012, seg=8, cell='sw_enamel')
        for k in range(1, 6):
            yy = cy0 + 0.02 + (cy1 - cy0 - 0.04) * k / 6
            B.cyl(ATLAS_MAT, (x, yy, z + 0.3), (x, yy, z + hb - 0.02), 0.007, seg=6, cell='sw_enamel')
    for yy in (cy0 + 0.02, cy1 - 0.02):
        B.cyl(ATLAS_MAT, (cx0 + 0.02, yy, z + 0.3), (cx1 - 0.02, yy, z + 0.3), 0.012, seg=8, cell='sw_enamel')
    B.cyl(ATLAS_MAT, (cx0 + 0.02, cy0 + 0.02, z + 0.52), (cx1 - 0.02, cy0 + 0.02, z + 0.52), 0.011, seg=8, cell='sw_enamel')
    B.sbox('sw_ticking', cx0 + 0.04, cx1 - 0.04, cy0 + 0.04, cy1 - 0.04, z + 0.3, z + 0.38)
    B.cbox(ATLAS_MAT, (cx0 + 0.2, (cy0 + cy1) / 2, z + 0.41), (0.22, 0.3, 0.07), cell='sw_enamel')     # the pillow
    B.sbox('sw_felt', cx0 + 0.45, cx1 - 0.04, cy0 + 0.03, cy1 - 0.03, z + 0.38, z + 0.43)            # the blanket, folded back
    B.sbox('sw_felt', cx0 + 0.42, cx0 + 0.5, cy0 + 0.03, cy1 - 0.03, z + 0.38, z + 0.47)
    # The folding screen: three panels, zigzag, between the hatch and the cot.
    pts = [(249.40, 1.36), (249.56, 1.08), (249.42, 0.82), (249.56, 0.58)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        a = math.atan2(by - ay, bx - ax)
        n0 = B.mark()
        B.box('WornIron', 0.0, L, -0.012, 0.012, 0.0, 0.03)
        B.box('WornIron', 0.0, L, -0.012, 0.012, 1.02, 1.05)
        B.box('WornIron', 0.0, 0.025, -0.012, 0.012, 0.0, 1.05)
        B.box('WornIron', L - 0.025, L, -0.012, 0.012, 0.0, 1.05)
        B.sbox('sw_screen', 0.02, L - 0.02, -0.004, 0.004, 0.08, 1.0)
        B.xform(n0, Matrix.Translation((ax, ay, z)) @ Matrix.Rotation(a, 4, 'Z'))
    # The basin, on the back wall at child height, its tap dripping; its pipe goes down through the deck to the hide.
    bx = 251.15
    B.cyl(ATLAS_MAT, (bx, BACK_Y - 0.14, z + 0.5), (bx, BACK_Y - 0.14, z + 0.62), 0.07, 0.13, seg=16, cell='sw_enamel')
    B.box(ATLAS_MAT, bx - 0.13, bx + 0.13, BACK_Y - 0.03, BACK_Y, z + 0.5, z + 0.66, cell='sw_enamel')
    B.cyl('Brass', (bx, BACK_Y, z + 0.82), (bx, BACK_Y - 0.12, z + 0.82), 0.012, seg=8)
    B.cyl('Brass', (bx, BACK_Y - 0.12, z + 0.82), (bx, BACK_Y - 0.12, z + 0.76), 0.01, seg=8)
    B.cyl('Brass', (bx, BACK_Y - 0.12, z + 0.86), (bx, BACK_Y - 0.12, z + 0.82), 0.004, seg=6)
    B.sphere('Brass', (bx, BACK_Y - 0.12, z + 0.875), 0.016, seg=8, scale=(1.6, 1.6, 0.5))
    B.sphere(ATLAS_MAT, (bx, BACK_Y - 0.12, z + 0.715), 0.006, seg=6, scale=(1, 1, 1.5), cell='sw_glass')   # the drip
    B.cyl('Copper', (bx, PIPE_Y, z + 0.5), (bx, PIPE_Y, z - 0.04), 0.016, seg=8)                        # down through the deck
    B.cyl('Copper', (bx + 0.08, BACK_Y - 0.03, CEIL), (bx + 0.08, BACK_Y - 0.03, z + 0.82), 0.012, seg=8)  # the supply, from above
    B.cyl('Copper', (bx + 0.08, BACK_Y - 0.03, z + 0.82), (bx, BACK_Y - 0.03, z + 0.82), 0.012, seg=8)
    # Notices: SICK BAY over the cot; the protocol by the screen.
    B.box('PigeonWood', 249.88, 250.62, BACK_Y - 0.015, BACK_Y, 2.86, 3.05)
    B.decal(249.9, 250.6, 2.87, 3.04, BACK_Y - 0.016, 'sickbay')
    B.box('PigeonWood', 249.58, 250.02, BACK_Y - 0.012, BACK_Y, 2.62, 2.84)
    B.decal(249.6, 250.0, 2.63, 2.83, BACK_Y - 0.013, 'notice')
    # A hook with a towel by the basin; a chamber of a stool by the cot.
    B.sbox('sw_enamel', 250.93, 251.02, BACK_Y - 0.03, BACK_Y - 0.01, z + 0.42, z + 0.75)
    B.cyl(ATLAS_MAT, (251.0, BACK_Y, z + 0.75), (251.0, BACK_Y - 0.05, z + 0.77), 0.006, seg=6, cell='sw_brass')


# =====================================================================================================================
# The pupil lift
# =====================================================================================================================
def build_lift_static(B):
    """The guide posts, the counterweight's channel and the sheave above, the lamp box and the sign."""
    for x in POSTS_X:
        B.box('WornIron', x - 0.025, x + 0.025, POST_Y - 0.025, POST_Y + 0.025, 0.0, 3.45)
        B.box('WornIron', x - 0.05, x + 0.05, POST_Y - 0.05, POST_Y + 0.05, 0.0, 0.02)
        B.box('WornIron', x - 0.015, x + 0.015, POST_Y + 0.025, BACK_Y, 3.0, 3.06)   # stays to the wall
        B.box('WornIron', x - 0.015, x + 0.015, POST_Y + 0.025, BACK_Y, 0.8, 0.86)
    B.box('WornIron', POSTS_X[0] - 0.03, POSTS_X[1] + 0.03, POST_Y - 0.03, BACK_Y, 3.42, 3.5)    # the sheave's beam
    sx, sy, sz, sr = SHEAVE
    B.torus('WornIron', (sx, sy, sz), (1, 0, 0), sr - 0.01, 0.014, seg=24, rseg=6)
    B.cyl('WornIron', (sx - 0.012, sy, sz), (sx + 0.012, sy, sz), sr - 0.02, seg=18)
    B.cyl('WornIron', (sx - 0.06, sy, sz), (sx + 0.06, sy, sz), 0.02, seg=8)
    for x in (sx - 0.06, sx + 0.06):
        B.box('WornIron', x - 0.01, x + 0.01, sy - 0.03, sy + 0.03, sz, 3.42)
    # Over the ceiling, the cables' slack runs up into a dark trunk (the lift's cable when it is up, the weight's when down).
    B.sbox('sw_dark', sx - 0.15, sx + 0.15, POST_Y - 0.15, BACK_Y, CEIL, CEIL + 1.6)
    for x in (CW[0] - 0.02, CW[1] + 0.02):                                  # the counterweight's channel
        B.box('WornIron', x - 0.012, x + 0.012, BACK_Y - 0.1, BACK_Y, 0.0, 3.42)
    # The lamp box on the right post: PUPIL (green-white) and ESCORT (amber), labels under them; a buzzer.
    B.box('WornIron', 252.04, 252.32, 0.865, POST_Y - 0.025, 2.02, 2.3)
    for (x, y, z), lab in ((LAMP_PUPIL, 'lpupil'), (LAMP_ESCORT, 'lescort')):
        B.torus('Brass', (x, 0.863, z), (0, 1, 0), 0.038, 0.008, seg=16, rseg=4)
        B.decal(x - 0.065, x + 0.065, 2.04, 2.1, 0.8635, lab)
    B.cyl('WornIron', (252.18, 0.9, 2.3), (252.18, 0.9, 2.34), 0.025, seg=10)       # the buzzer
    B.cyl('WornIron', (252.30, POST_Y, 2.3), (252.30, POST_Y, 3.42), 0.008, seg=6)   # its conduit up the post
    # The sign across the posts, above a figure's head: PUPIL LIFT · NO PUPIL UNACCOMPANIED.
    B.box('PigeonWood', POSTS_X[0] - 0.02, POSTS_X[1] + 0.02, POST_Y - 0.04, POST_Y - 0.025, 2.62, 2.96)
    B.decal(POSTS_X[0], POSTS_X[1], 2.64, 2.94, POST_Y - 0.041, 'liftsign')


def build_lift(coll):
    """Att15Lift: an open platform lane-deep, built up (deck top 1.6): timber on an iron frame, its rail stub, the guide
    shoes on the posts, and its hoisting cable up over the sheave (long enough to stay over it as the lift goes down)."""
    B = MB()
    x0, x1, y0, y1, top = LIFT
    B.box('CrateWood', x0 + 0.005, x1 - 0.005, y0 + 0.005, y1 - 0.005, top - 0.03, top)
    for a, b, c, d in ((x0, x0 + 0.03, y0, y1), (x1 - 0.03, x1, y0, y1), (x0, x1, y0, y0 + 0.03), (x0, x1, y1 - 0.03, y1)):
        B.box('WornIron', a, b, c, d, top - LIFT_T, top - 0.025)
    for x in (x0 + 0.33, x1 - 0.33):
        B.box('WornIron', x - 0.02, x + 0.02, y0, y1, top - LIFT_T, top - 0.03)
    B.box('HandledBrass', x0, x1, y0, y0 + 0.03, top - 0.03, top + 0.002)               # brass nosings: a platform of its own
    B.box('HandledBrass', x0, x0 + 0.025, y0, y1, top - 0.03, top + 0.002)
    build_rails(B, x0, x1, top, channel=True)
    for x in POSTS_X:                                                        # guide shoes round the posts
        B.box('WornIron', x - 0.05, x + 0.05, y1 - 0.01, POST_Y - 0.028, top - LIFT_T, top - 0.005)
        for s in (-1, 1):
            B.box('WornIron', x + s * 0.034 - 0.006, x + s * 0.034 + 0.006, POST_Y - 0.03, POST_Y + 0.03, top - LIFT_T - 0.04, top - 0.005)
    sx, sy, sz, sr = SHEAVE
    B.box('WornIron', sx - 0.04, sx + 0.04, y1 - 0.01, sy - sr + 0.01, top - LIFT_T, top - 0.02)
    B.cyl('WornIron', (sx, sy - sr, top), (sx, sy - sr, top + 0.05), 0.012, seg=8)
    B.cyl('WornIron', (sx, sy - sr, top + 0.05), (sx, sy - sr, sz + top + 0.1), 0.007, seg=6)
    return B.obj('Att15Lift', coll, origin=((x0 + x1) / 2, (y0 + y1) / 2, top))


def build_gate(coll):
    """Att15LiftGate: an iron lattice gate on the lift's right edge, built shut at the top. Origin on its hinge post at
    the back (x 252.4, y 0.9, deck level). It swings open about z by -90 deg (Blender), its free end into the lift
    along the lift's back."""
    B = MB()
    hx, hy, hz = GATE_HINGE
    yf, H = -0.27, 0.85
    B.cyl('WornIron', (hx, hy, hz), (hx, hy, hz + H), 0.014, seg=8)
    B.box('WornIron', hx - 0.008, hx + 0.008, yf, hy, hz + H - 0.03, hz + H)
    B.box('WornIron', hx - 0.008, hx + 0.008, yf, hy, hz + 0.02, hz + 0.05)
    B.box('WornIron', hx - 0.01, hx + 0.01, yf - 0.02, yf + 0.01, hz + 0.02, hz + H)
    n = 9
    ys = [yf + (hy - 0.02 - yf) * k / n for k in range(n + 1)]
    for y in ys[1:-1]:
        B.box('WornIron', hx - 0.004, hx + 0.004, y - 0.004, y + 0.004, hz + 0.05, hz + H - 0.03)
    L = H - 0.08
    for ya, yb in zip(ys, ys[1:]):
        d = math.hypot(yb - ya, L)
        for s in (1, -1):
            a = math.atan2(L, (yb - ya)) * s
            B.cbox('WornIron', (hx, (ya + yb) / 2, hz + 0.05 + L / 2), (0.006, d, 0.008), rot=Rx(a))
    B.box('HandledBrass', hx - 0.03, hx + 0.03, yf - 0.03, yf - 0.01, hz + 0.5, hz + 0.6)        # the latch
    return B.obj('Att15LiftGate', coll, origin=(hx, hy, hz))


def build_cw(coll):
    """Att15LiftCW: cast-iron weight plates in a stirrup, built low (lift up); origin its centre; it rises 1.6 as the
    lift goes down. Its cable runs up over the sheave (long enough for the travel)."""
    B = MB()
    x0, x1, y0, y1, z0, z1 = CW
    k = 0
    z = z0
    while z < z1 - 0.06:
        B.box('WornIron', x0 + 0.005, x1 - 0.005, y0, y1, z + 0.004, z + 0.075)
        z += 0.08
        k += 1
    for x in (x0, x1 - 0.012):
        B.box('WornIron', x, x + 0.012, (y0 + y1) / 2 - 0.02, (y0 + y1) / 2 + 0.02, z0 - 0.02, z1 + 0.04)
    B.box('WornIron', x0, x1, (y0 + y1) / 2 - 0.02, (y0 + y1) / 2 + 0.02, z1 + 0.02, z1 + 0.05)
    sx, sy, sz, sr = SHEAVE
    B.cyl('WornIron', (sx, sy + sr, z1 + 0.05), (sx, sy + sr, sz), 0.007, seg=6)
    B.box('WornIron', sx - 0.02, sx + 0.02, (y0 + y1) / 2 - 0.02, sy + sr + 0.012, z1 + 0.04, z1 + 0.07)
    return B.obj('Att15LiftCW', coll, origin=((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))


def build_lamp(coll, name, c, r=0.03, squash=0.6):
    B = MB()
    B.sphere(name, c, r, seg=14, scale=(1, squash, 1))
    return B.obj(name, coll, origin=c)


# =====================================================================================================================
# The class: the front row, Mara's place, the rows behind, the boards, the teacher's desk, the partition
# =====================================================================================================================
def desk(B, xc, lid_cell=None, name_cell=None):
    """A child's desk behind the rail (y 0.8 to 1.2, top 0.55): a sloped lid toward the camera on a book box, a flat
    back strip with an inkwell, cast-iron standards; a brass name holder on its front."""
    w = DESK_W
    y0, y1 = DESK_Y
    for s in (-1, 1):
        x = xc + s * (w - 0.02)
        B.prism_yz('CrateWood', [(y0 + 0.01, 0.34), (y1 - 0.01, 0.34), (y1 - 0.01, 0.585), (1.07, 0.585), (y0 + 0.01, 0.478)],
                   x - 0.008, x + 0.008)
        B.box('WornIron', x - 0.012, x + 0.012, y0 + 0.02, y1 - 0.02, 0.0, 0.03)
        for yy in (y0 + 0.06, y1 - 0.06):
            B.box('WornIron', x - 0.01, x + 0.01, yy - 0.012, yy + 0.012, 0.03, 0.34)
        B.box('WornIron', x - 0.008, x + 0.008, y0 + 0.06, y1 - 0.06, 0.16, 0.185)
    B.box('CrateWood', xc - w + 0.02, xc + w - 0.02, y0 + 0.01, y0 + 0.025, 0.34, 0.47)     # front
    B.box('CrateWood', xc - w + 0.02, xc + w - 0.02, y1 - 0.025, y1 - 0.01, 0.34, 0.585)    # back
    B.box('CrateWood', xc - w + 0.02, xc + w - 0.02, y0 + 0.01, y1 - 0.01, 0.34, 0.355)     # bottom
    B.prism_yz('CrateWood', [(y0 - 0.005, 0.472), (1.07, 0.582), (1.07, 0.6), (y0 - 0.005, 0.49)], xc - w, xc + w)   # the lid
    B.box('CrateWood', xc - w, xc + w, 1.07, y1, 0.58, 0.6)
    B.box('PigeonWood', xc - w + 0.04, xc + w - 0.2, 1.085, 1.105, 0.6, 0.603)                 # the pen groove
    B.cyl('Brass', (xc + w - 0.1, 1.135, 0.6), (xc + w - 0.1, 1.135, 0.606), 0.02, seg=10)    # the inkwell's lid
    if lid_cell:
        a, b = (y0 - 0.005, 0.49), (1.07, 0.6)
        nz = 0.0015
        u0, v0, u1, v1 = cell_uv(lid_cell)
        B.face(ATLAS_MAT, [(xc - w + 0.02, a[0] + 0.01, a[1] + nz + 0.004), (xc + w - 0.02, a[0] + 0.01, a[1] + nz + 0.004),
                           (xc + w - 0.02, b[0] - 0.005, b[1] + nz - 0.002), (xc - w + 0.02, b[0] - 0.005, b[1] + nz - 0.002)],
               [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    if name_cell:
        B.box('HandledBrass', xc - 0.14, xc + 0.14, y0 - 0.002, y0 + 0.01, 0.37, 0.46)
        B.decal(xc - 0.13, xc + 0.13, 0.378, 0.452, y0 - 0.003, name_cell)
        B.box('HandledBrass', xc - 0.14, xc + 0.14, y0 - 0.008, y0 - 0.002, 0.37, 0.38)


def child_chair(B, M, seat_mt='CrateWood', leg_mt='PigeonWood', w=0.2, d=0.2, seat=0.30, cell=None):
    """A child's chair in its own frame (facing +x, its back at -x, the seat's top at `seat`), moved by M."""
    n0 = B.mark()
    S = (lambda c, *a: B.sbox(cell, *a)) if cell else (lambda c, *a: B.box(c, *a))
    S(seat_mt, -d / 2, d / 2, -w / 2, w / 2, seat - 0.022, seat)
    for sx in (-1, 1):
        for sy in (-1, 1):
            S(leg_mt, sx * (d / 2 - 0.02) - 0.011, sx * (d / 2 - 0.02) + 0.011, sy * (w / 2 - 0.02) - 0.011, sy * (w / 2 - 0.02) + 0.011,
              0.0, seat - 0.022)
        S(leg_mt, -d / 2 + 0.005, -d / 2 + 0.025, sx * (w / 2 - 0.02) - 0.011, sx * (w / 2 - 0.02) + 0.011, seat, seat + 0.27)
    S(seat_mt, -d / 2 + 0.003, -d / 2 + 0.027, -w / 2 + 0.01, w / 2 - 0.01, seat + 0.15, seat + 0.26)
    S(leg_mt, -d / 2 + 0.02, d / 2 - 0.02, -w / 2 + 0.015, -w / 2 + 0.03, 0.08, 0.1)
    S(leg_mt, -d / 2 + 0.02, d / 2 - 0.02, w / 2 - 0.03, w / 2 - 0.015, 0.08, 0.1)
    B.xform(n0, M)


def build_front_row(B):
    """S1, S2, S3: the desks behind the rail, their brass seat plates in the rail channel, the wire to the board."""
    for k, (_s, x, _nm) in enumerate(SEATS):
        desk(B, x, lid_cell='lid' if k == 2 else None, name_cell='name%d' % (k + 1))
        B.box('HandledBrass', x - 0.16, x + 0.16, RAIL_Y - 0.06, RAIL_Y + 0.06, 0.0, 0.006)
        B.box('HandledBrass', x - 0.17, x + 0.17, RAIL_Y - 0.065, RAIL_Y - 0.055, 0.0, 0.008)
        B.box('HandledBrass', x - 0.17, x + 0.17, RAIL_Y + 0.055, RAIL_Y + 0.065, 0.0, 0.008)
        for dx in (-0.12, 0.12):
            B.cyl('WornIron', (x + dx, RAIL_Y, 0.006), (x + dx, RAIL_Y, 0.009), 0.008, seg=6)
        B.cyl('WornIron', (x, CHAN[1] + 0.005, 0.006), (x, CHAN[1] + 0.03, 0.006), 0.006, seg=6)
    # The seats' wire: along the channel's back edge to the board, then up the wall to it.
    wx = ATT[0] + 0.06
    B.cyl('WornIron', (SEATS[0][1], CHAN[1] + 0.03, 0.008), (wx, CHAN[1] + 0.03, 0.008), 0.007, seg=6)
    B.cyl('WornIron', (wx, CHAN[1] + 0.03, 0.008), (wx, BACK_Y - 0.012, 0.008), 0.007, seg=6)
    B.cyl('WornIron', (wx, BACK_Y - 0.012, 0.008), (wx, BACK_Y - 0.012, ATT[2]), 0.007, seg=6)
    # Mara's things on her desk: an exercise book, a pencil.
    x = SEATS[2][1]
    B.tbox(x - 0.25, x - 0.08, 1.08, 1.19, 0.6, 0.606, {'+z': 'book', 'all': 'sw_pages'})
    B.cyl(ATLAS_MAT, (x + 0.02, 1.095, 0.606), (x + 0.12, 1.1, 0.606), 0.004, seg=6, cell='sw_pencil')


def build_chair(coll):
    """Att15Chair: Mara's chair, pulled out from her desk and turned to face +x, as if she got up in a hurry. Static;
    D-17 sits on it (seat top 0.30). Origin on the floor under the seat's centre."""
    B = MB()
    cx, cy, turn = CHAIR
    child_chair(B, Matrix.Translation((cx, cy, 0.0)) @ Matrix.Rotation(math.radians(turn), 4, 'Z'), seat=CHAIR_SEAT)
    return B.obj('Att15Chair', coll, origin=(cx, cy, 0.0))


def build_rows(coll):
    """Att15Rows: the rest of the class, four rows going back into the alcove's dark; low detail, one material, merged.
    Some chairs up on the desks, one desk pushed askew, a chair on its side."""
    B = MB()
    rnd = random.Random(1590)
    for j, yd in enumerate(ROWS_Y):
        for i, xd in enumerate(ROWS_X):
            if (i, j) in ((4, 3),):
                continue                                                     # a gap where a desk was taken away
            ang = rnd.uniform(-0.04, 0.04) + (0.22 if (i, j) == (1, 2) else 0.0)
            n0 = B.mark()
            B.sbox('sw_wooddk', -0.29, 0.29, -0.2, 0.2, 0.34, 0.36)
            B.prism_yz(ATLAS_MAT, [(-0.205, 0.47), (0.07, 0.58), (0.07, 0.6), (-0.205, 0.49)], -0.3, 0.3, cell='sw_wood')
            B.sbox('sw_wood', -0.3, 0.3, 0.07, 0.2, 0.58, 0.6)
            B.sbox('sw_wooddk', -0.28, 0.28, -0.19, -0.18, 0.36, 0.47)
            for s in (-1, 1):
                B.sbox('sw_wooddk', s * 0.28 - 0.008, s * 0.28 + 0.008, -0.19, 0.19, 0.34, 0.58)
                B.sbox('sw_iron', s * 0.27 - 0.01, s * 0.27 + 0.01, -0.18, 0.18, 0.0, 0.025)
                B.sbox('sw_iron', s * 0.27 - 0.008, s * 0.27 + 0.008, -0.012, 0.012, 0.025, 0.34)
            B.xform(n0, Matrix.Translation((xd, yd, 0.0)) @ Matrix.Rotation(ang, 4, 'Z'))
            up = rnd.random() < 0.4
            if (i, j) == (2, 1):
                M = Matrix.Translation((xd + 0.1, yd - 0.4, 0.11)) @ Matrix.Rotation(math.radians(90), 4, 'X') @ Matrix.Rotation(1.2, 4, 'Z')
            elif up:
                M = Matrix.Translation((xd, yd + 0.1, 0.6 + CHAIR_SEAT)) @ Matrix.Rotation(math.pi, 4, 'X') @ \
                    Matrix.Rotation(math.radians(90 + rnd.uniform(-8, 8)), 4, 'Z')
            else:
                M = Matrix.Translation((xd + rnd.uniform(-0.05, 0.05), yd - 0.34, 0.0)) @ Matrix.Rotation(math.radians(90 + rnd.uniform(-10, 10)), 4, 'Z')
            child_chair(B, M, cell='sw_wood')
    return B.obj('Att15Rows', coll)


def build_boards(B):
    """The attendance board (its lamps apart), the bell's box and wire, the blackboard and its ledge, the Steward, a
    stopped clock."""
    x0, x1, z0, z1 = ATT
    B.box('PigeonWood', x0 - 0.03, x1 + 0.03, ATT_FACE, BACK_Y, z0 - 0.03, z1 + 0.03)
    B.decal(x0, x1, z0, z1, ATT_FACE - 0.001, 'att')
    for x in ATT_LAMPS:
        B.torus('Brass', (x, ATT_FACE - 0.004, ATT_LAMP_Z), (0, 1, 0), 0.062, 0.009, seg=18, rseg=4)
    B.cyl('WornIron', (x0 + 0.06, BACK_Y - 0.012, z1 + 0.03), (x0 + 0.06, BACK_Y - 0.012, BELL[2] - 0.06), 0.007, seg=6)
    B.cyl('WornIron', (x0 + 0.06, BACK_Y - 0.012, BELL[2] - 0.06), (BELL[0] - 0.12, BACK_Y - 0.012, BELL[2] - 0.06), 0.007, seg=6)
    # The blackboard: a frame, the slate (atlas), its chalk ledge with chalk and a duster.
    bx0, bx1, bz0, bz1 = BB
    B.box('PigeonWood', bx0 - 0.05, bx1 + 0.05, BACK_Y - 0.03, BACK_Y, bz0 - 0.05, bz1 + 0.05)
    B.decal(bx0, bx1, bz0, bz1, BACK_Y - 0.031, 'board')
    B.box('PigeonWood', bx0 - 0.06, bx1 + 0.06, BACK_Y - 0.11, BACK_Y - 0.03, bz0 - 0.07, bz0 - 0.04)
    B.box('PigeonWood', bx0 - 0.06, bx1 + 0.06, BACK_Y - 0.11, BACK_Y - 0.1, bz0 - 0.04, bz0 - 0.02)
    for x in (259.6, 259.75, 260.9):
        B.cyl(ATLAS_MAT, (x, BACK_Y - 0.07, bz0 - 0.033), (x + 0.07, BACK_Y - 0.075, bz0 - 0.033), 0.006, seg=6, cell='sw_chalk')
    B.sbox('sw_felt', 261.2, 261.34, BACK_Y - 0.1, BACK_Y - 0.05, bz0 - 0.04, bz0 - 0.01)
    B.sbox('sw_wood', 261.2, 261.34, BACK_Y - 0.1, BACK_Y - 0.05, bz0 - 0.01, bz0 + 0.02)
    # The Steward over it, in DL-13's frame: heavy wood, a brass slip, a brass plate.
    px, pz = PORTRAIT
    B.box('PigeonWood', px - 0.31, px + 0.31, BACK_Y - 0.06, BACK_Y, pz - 0.38, pz + 0.38)
    B.box('Brass', px - 0.27, px + 0.27, BACK_Y - 0.07, BACK_Y - 0.06, pz - 0.34, pz + 0.34)
    B.decal(px - 0.25, px + 0.25, pz - 0.312, pz + 0.312, BACK_Y - 0.071, 'portrait')
    B.box('Brass', px - 0.12, px + 0.12, BACK_Y - 0.016, BACK_Y, pz - 0.47, pz - 0.41)
    B.decal(px - 0.11, px + 0.11, pz - 0.4675, pz - 0.4125, BACK_Y - 0.017, 'stewplate')
    # A clock, stopped, over the teacher's desk.
    cx, cz = 262.2, 2.55
    B.cyl('PigeonWood', (cx, BACK_Y, cz), (cx, BACK_Y - 0.05, cz), 0.16, seg=20)
    u0, v0, u1, v1 = cell_uv('clock')
    uc, vc, ur = (u0 + u1) / 2, (v0 + v1) / 2, (u1 - u0) / 2 * 0.98
    B.face(ATLAS_MAT, [(cx + 0.14 * math.cos(a), BACK_Y - 0.052, cz + 0.14 * math.sin(a)) for a in (2 * math.pi * k / 16 for k in range(16))],
           [(uc + ur * math.cos(a), vc + ur * math.sin(a)) for a in (2 * math.pi * k / 16 for k in range(16))])


def build_bell(coll):
    """Att15Bell: the dismissal bell over the attendance board: a brass gong on a wall plate, the striker beside it.
    Static (the game may shake it); origin on the wall at its mount."""
    B = MB()
    x, y, z = BELL
    B.box('WornIron', x - 0.12, x + 0.08, y - 0.015, y, z - 0.1, z + 0.1)
    B.cyl('WornIron', (x, y - 0.015, z), (x, y - 0.06, z), 0.012, seg=8)
    B.cyl('Brass', (x, y - 0.06, z), (x, y - 0.1, z), 0.1, 0.04, seg=24)
    B.cyl('Brass', (x, y - 0.1, z), (x, y - 0.11, z), 0.04, 0.012, seg=16)
    B.torus('Brass', (x, y - 0.06, z), (0, 1, 0), 0.098, 0.006, seg=24, rseg=4)
    B.box('WornIron', x - 0.11, x - 0.07, y - 0.08, y - 0.015, z - 0.08, z - 0.03)        # the coil box
    B.cyl('WornIron', (x - 0.09, y - 0.09, z - 0.05), (x - 0.03, y - 0.13, z - 0.02), 0.005, seg=6)   # the striker arm
    B.sphere('WornIron', (x - 0.03, y - 0.135, z - 0.02), 0.012, seg=8)
    return B.obj('Att15Bell', coll, origin=(x, y, z))


def build_teacher(B):
    """The teacher's desk against the back wall, its register open; her chair beside it, by the wall."""
    x0, x1, y0, y1, top = TDESK
    B.box('CrateWood', x0 - 0.02, x1 + 0.02, y0 - 0.03, y1, top - 0.035, top)
    B.box('PigeonWood', x0, x0 + 0.32, y0, y1 - 0.02, 0.04, top - 0.035)                 # the drawer pedestal
    for z in (0.22, 0.42, 0.6):
        B.box('PigeonWood', x0 + 0.02, x0 + 0.3, y0 - 0.008, y0, z - 0.07, z + 0.07)
        B.box('Brass', x0 + 0.14, x0 + 0.18, y0 - 0.02, y0 - 0.008, z - 0.008, z + 0.008)
    B.box('PigeonWood', x1 - 0.05, x1, y0, y1 - 0.02, 0.04, top - 0.035)
    B.box('PigeonWood', x0 + 0.32, x1 - 0.05, y1 - 0.04, y1 - 0.02, 0.25, top - 0.035)
    for x in (x0, x0 + 0.32, x1 - 0.05, x1):
        B.box('PigeonWood', x - 0.015, x + 0.015, y0, y1 - 0.02, 0.0, 0.04)
    B.tbox(x0 + 0.3, x0 + 0.62, y0 + 0.06, y0 + 0.3, top, top + 0.025, {'+z': 'register', 'all': 'sw_pages'})
    B.tbox(x0 + 0.05, x0 + 0.24, y1 - 0.2, y1 - 0.04, top, top + 0.05, {'all': 'sw_wooddk'})
    B.cyl('Brass', (x1 - 0.12, y1 - 0.12, top), (x1 - 0.12, y1 - 0.12, top + 0.06), 0.045, 0.02, seg=12)   # a handbell
    B.cyl('PigeonWood', (x1 - 0.12, y1 - 0.12, top + 0.06), (x1 - 0.12, y1 - 0.12, top + 0.14), 0.012, 0.016, seg=8)
    M = Matrix.Translation((262.92, 1.12, 0.0)) @ Matrix.Rotation(math.radians(-150), 4, 'Z') @ Matrix.Diagonal((1.25, 1.25, 1.5, 1))
    child_chair(B, M, seat=0.3)


def build_partition(B):
    """The end partition (x 263.75..263.9): the class door's opening in the lane, the rail's flap opening beside it, a
    jamb between, DISMISSAL on a flag sign over the door (facing the camera)."""
    p0, p1 = PART
    dy0, dy1, dh = DOOR
    fy0, fy1 = 0.4, 0.72
    wall(B, p0, p1, FRONT_Y, dy0, 0.0, CEIL)
    wall(B, p0, p1, dy0, dy1, dh, CEIL)
    wall(B, p0, p1, dy1, fy0, 0.0, CEIL)
    wall(B, p0, p1, fy0, fy1, 1.05, CEIL)
    wall(B, p0, p1, fy1, BACK_Y + BACK_T, 0.0, CEIL)
    # Architraves on the room side.
    for a, b, c, d in ((dy0 - 0.06, dy0, 0.0, dh + 0.06), (dy0 - 0.06, fy1 + 0.04, dh, dh + 0.06), (fy1, fy1 + 0.04, 0.0, dh)):
        B.box('PigeonWood', p0 - 0.02, p0, a, b, c, d)
    B.box('WornIron', p0 - 0.015, p0, fy0, fy1, 1.05, 1.09)                                # the flap's hinge bar
    for a, b in ((FRONT_Y, dy0 - 0.06), (fy1 + 0.04, BACK_Y)):
        B.box('PigeonWood', p0 - 0.02, p0, a, b, 0.0, 0.12)
        B.box('CrateWood', p0 - 0.03, p0, a, b, 0.98, 1.03)
    # DISMISSAL: a flag sign on an iron bracket out of the partition, over the door, both faces painted.
    sx0, sx1, sz0, sz1, sy = 263.08, 263.68, 2.14, 2.29, -0.04
    B.box('WornIron', sx0 - 0.01, p0, sy - 0.006, sy + 0.006, sz1 + 0.02, sz1 + 0.035)
    for x in (sx0 + 0.06, sx1 - 0.06):
        B.cyl('WornIron', (x, sy, sz1), (x, sy, sz1 + 0.03), 0.004, seg=6)
    B.box('PigeonWood', sx0 - 0.01, sx1 + 0.01, sy - 0.004, sy + 0.004, sz0 - 0.01, sz1 + 0.01)
    B.decal(sx0, sx1, sz0, sz1, sy - 0.005, 'dismiss')
    u0, v0, u1, v1 = cell_uv('dismiss')
    B.face(ATLAS_MAT, [(sx1, sy + 0.005, sz0), (sx0, sy + 0.005, sz0), (sx0, sy + 0.005, sz1), (sx1, sy + 0.005, sz1)],
           [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    # CLASS 6 on the back wall by the door, a fire bucket's hook gone; a timetable's pale patch.
    B.decal(262.95, 263.43, 1.86, 2.02, BACK_Y - 0.002, 'class6')


def build_door(coll):
    """Att15Door: the class door, panelled, shut in the partition's far layer. Origin on its hinge (x 263.9, y 0.38,
    floor); it swings +95 deg about z (Blender) toward +x, away into DL-16."""
    B = MB()
    hx, hy, _ = DOOR_HINGE
    dy0, dy1, dh = DOOR
    x0, x1 = hx - 0.042, hx - 0.002
    for a, b, c, d in ((dy0, dy0 + 0.1, 0.0, dh), (dy1 - 0.1, dy1, 0.0, dh), (dy0, dy1, 0.0, 0.16), (dy0, dy1, 0.92, 1.04),
                       (dy0, dy1, dh - 0.12, dh)):
        B.box('PigeonWood', x0, x1, a, b, c, d)
    B.box('PigeonWood', x0 + 0.01, x1 - 0.01, dy0 + 0.1, dy1 - 0.1, 0.16, dh - 0.12)
    for side in (-1, 1):
        x = x0 - 0.035 if side < 0 else x1 + 0.035
        B.cyl('Brass', (x0 if side < 0 else x1, dy0 + 0.08, 0.95), (x, dy0 + 0.08, 0.95), 0.008, seg=6)
        B.sphere('Brass', (x, dy0 + 0.08, 0.95), 0.026, seg=10)
    for z in (0.25, dh - 0.25):
        B.cyl('WornIron', (hx, hy, z - 0.06), (hx, hy, z + 0.06), 0.012, seg=8)
    return B.obj('Att15Door', coll, origin=DOOR_HINGE)


def build_flap(coll):
    """Att15Flap: the rail's flap beside the door, low on the rail: boards on iron straps, a leather skirt, hinged at
    its top edge. Built shut; origin on the hinge (x 263.815, y 0.56, z 1.05); it swings up toward +x by rotating
    about Blender y by a negative angle (-80 deg: open)."""
    B = MB()
    x0, x1, y0, y1, z0, z1 = FLAP
    B.box('PigeonWood', x0, x1, y0, y1, z0 + 0.06, z1 - 0.02)
    for z in (z0 + 0.2, z1 - 0.15):
        B.box('WornIron', x0 - 0.004, x1 + 0.004, y0, y1, z - 0.02, z + 0.02)
    B.sbox('sw_rubber', x0 + 0.005, x1 - 0.005, y0 + 0.01, y1 - 0.01, z0, z0 + 0.06)
    hx, hy, hz = FLAP_HINGE
    B.cyl('WornIron', (hx, y0 + 0.02, hz - 0.012), (hx, y1 - 0.02, hz - 0.012), 0.012, seg=8)
    return B.obj('Att15Flap', coll, origin=FLAP_HINGE)


def build_lighting(B, coll):
    """Enamel pendant shades on their cords (the bulbs are Att15Lights, EMIT AttBulbGlow); one dead over the alcove."""
    L = MB()
    for x, y, z in PENDANTS + (DEAD_PENDANT,):
        top = CEIL
        B.cyl('WornIron', (x, y, top), (x, y, z + 0.14), 0.005, seg=6)
        B.cyl('WornIron', (x, y, top), (x, y, top - 0.03), 0.05, seg=10)
        B.cyl('WornIron', (x, y, z + 0.14), (x, y, z + 0.08), 0.03, 0.045, seg=12)
        B.cyl(ATLAS_MAT, (x, y, z + 0.08), (x, y, z - 0.01), 0.045, 0.2, seg=20, cell='sw_enamel')
        if (x, y, z) == DEAD_PENDANT:
            B.sphere(ATLAS_MAT, (x, y, z + 0.02), 0.04, seg=10, cell='sw_glass')
        else:
            L.sphere('AttBulbGlow', (x, y, z + 0.02), 0.04, seg=10)
    return L.obj('Att15Lights', coll)


# =====================================================================================================================
# The hiding place under the balcony
# =====================================================================================================================
def cloth(B, x0, x1, z_top, z_bot, y, folds, amp, cell, hem=None, seed=0, nx=16, nz=6):
    """A hanging blanket: a grid with folds (amp along y), both faces (one-sided in the game). hem(t) lifts the bottom
    edge (t 0..1 along x)."""
    u0, v0, u1, v1 = cell_uv(cell)
    rnd = random.Random(seed)
    ph = rnd.uniform(0, 6)
    grid = []
    for j in range(nz + 1):
        row = []
        for i in range(nx + 1):
            t = i / nx
            zb = z_bot + (hem(t) if hem else 0.0)
            z = z_top - (z_top - zb) * j / nz
            x = x0 + (x1 - x0) * t
            a = amp * (0.4 + 0.6 * j / nz)
            yy = y + a * math.sin(t * folds * 2 * math.pi + ph) + 0.004 * math.sin(j * 1.7 + i)
            row.append(((x, yy, z), (u0 + (u1 - u0) * t, v1 - (v1 - v0) * j / nz)))
        grid.append(row)
    for j in range(nz):
        for i in range(nx):
            q = [grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1], grid[j][i]]
            B.face(ATLAS_MAT, [p[0] for p in q], [p[1] for p in q])
            B.face(ATLAS_MAT, [(p[0][0], p[0][1] + 0.006, p[0][2]) for p in reversed(q)], [p[1] for p in reversed(q)])


def build_hide(coll):
    """Att15Hide: Mara's hiding place under the balcony (floor level, x 248.3..251.2, y 0.4..1.4), behind a blanket
    on a cord at y 0.35, pulled half aside (the way in at x 249.8). The pencil trees on the wall and on the deck's
    underside; the nest; the cup held to the copper pipe; the biscuit tin with the card player on it; a torch;
    the lamp's brass body (its glass is Att15HideLamp)."""
    B = MB()
    hx0, hx1, hy0, hy1 = HIDE
    # The pencil trees: on the back wall (over its dado and plaster) and on the deck's underside, between the joists.
    B.decal(hx0, hx1, 0.02, 1.48, BACK_Y - 0.035, 'pencil')
    u0, v0, u1, v1 = cell_uv('under')
    zu = BAL[4] - 0.041
    B.face(ATLAS_MAT, [(hx0, hy0, zu), (hx0, hy1, zu), (hx1, hy1, zu), (hx1, hy0, zu)], [(u0, v0), (u0, v1), (u1, v1), (u1, v0)])
    # The right side: a boarded screen against the lift's well.
    B.box('PigeonWood', hx1 - 0.03, hx1, hy0, BACK_Y, 0.0, BAL_UNDER)
    for z in (0.3, 0.75, 1.2):
        B.box('PigeonWood', hx1 - 0.05, hx1 - 0.03, hy0 + 0.05, BACK_Y - 0.05, z - 0.04, z + 0.04)
    # The cord and the blanket(s): the left one hangs, its right edge bunched; the right one's corner hooked back.
    B.cyl('WornIron', (hx0, BLANKET_Y, 1.47), (hx1, BLANKET_Y, 1.47), 0.004, seg=6)
    cloth(B, hx0, 249.52, 1.47, 0.05, BLANKET_Y, 3.5, 0.03, 'blanket', seed=1)
    cloth(B, 249.38, 249.56, 1.47, 0.08, BLANKET_Y + 0.02, 2.0, 0.035, 'blanket', seed=2, nx=6)          # the bunch
    cloth(B, 250.12, hx1, 1.47, 0.06, BLANKET_Y, 3.0, 0.028, 'blanket', seed=3,
          hem=lambda t: 0.75 * max(0.0, 1 - t / 0.3) ** 1.6)
    B.cyl('WornIron', (250.14, BLANKET_Y, 0.82), (250.14, BLANKET_Y + 0.05, 0.82), 0.003, seg=4)        # the hook it's caught on
    # The nest: a blanket in a heap, a cushion, an exercise book; pencil stubs.
    rnd = random.Random(1570)
    nx, ny = 10, 6
    pts = {}
    for i in range(nx + 1):
        for j in range(ny + 1):
            x = 248.4 + 1.15 * i / nx
            y = 0.62 + 0.72 * j / ny
            e = math.sin(math.pi * i / nx) * math.sin(math.pi * j / ny)
            pts[i, j] = (x, y, 0.004 + e * (0.06 + 0.05 * rnd.random()) + 0.03 * e * math.sin(i * 1.3 + j))
    u0, v0, u1, v1 = cell_uv('blanket')
    for i in range(nx):
        for j in range(ny):
            q = [pts[i, j], pts[i + 1, j], pts[i + 1, j + 1], pts[i, j + 1]]
            B.face(ATLAS_MAT, q, [(u0 + (u1 - u0) * (i + a) / nx, v0 + (v1 - v0) * (j + b) / ny) for a, b in ((0, 0), (1, 0), (1, 1), (0, 1))])
    n0 = B.mark()
    d17.rounded_box((0.34, 0.24, 0.1), (248.68, 1.16, 0.12), p=3.0, cuts=3, bm=B.bm, mat=B.m(ATLAS_MAT))
    B.paint(B.since(n0), 'sw_cushion')
    n0 = B.mark()
    B.tbox(-0.09, 0.09, -0.12, 0.12, 0.0, 0.006, {'+z': 'book', 'all': 'sw_pages'})
    B.xform(n0, Matrix.Translation((249.25, 0.8, 0.075)) @ Matrix.Rotation(0.5, 4, 'Z') @ Matrix.Rotation(0.12, 4, 'X'))
    for k in range(6):
        x, y, a = 249.45 + rnd.uniform(-0.15, 0.25), 1.15 + rnd.uniform(-0.15, 0.15), rnd.uniform(0, math.pi)
        ln = rnd.uniform(0.03, 0.06)
        B.cyl(ATLAS_MAT, (x, y, 0.004), (x + ln * math.cos(a), y + ln * math.sin(a), 0.004), 0.004, seg=6, cell='sw_pencil')
    # The copper pipe along the back wall (from the basin above), and the cup held to it on a building block.
    py = PIPE_Y
    B.cyl('Copper', (LWALL[1], py, PIPE_Z), (251.15, py, PIPE_Z), 0.018, seg=10)
    B.cyl('Copper', (251.15, py, PIPE_Z), (251.15, py, BAL_UNDER), 0.018, seg=10)
    for x in (248.6, 249.6, 250.6):
        B.box('WornIron', x - 0.012, x + 0.012, py + 0.015, BACK_Y - 0.035, PIPE_Z - 0.03, PIPE_Z + 0.03)
    cx = 249.7
    B.sbox('sw_wood', cx - 0.06, cx + 0.06, py - 0.13, py - 0.01, 0.0, PIPE_Z - 0.045)
    B.cyl(ATLAS_MAT, (cx, py - 0.115, PIPE_Z), (cx, py - 0.019, PIPE_Z), 0.034, 0.04, seg=14, cell='sw_enamel')
    B.torus(ATLAS_MAT, (cx + 0.04, py - 0.07, PIPE_Z), (0, 1, 0), 0.022, 0.005, seg=10, rseg=4, cell='sw_enamel')
    # The biscuit tin (the card player stands on it), the torch, the lamp's body.
    tx, ty, th = TIN
    B.tbox(tx - 0.14, tx + 0.14, ty - 0.11, ty + 0.11, 0.0, th - 0.012, {'all': 'sw_tin'})
    B.tbox(tx - 0.145, tx + 0.145, ty - 0.115, ty + 0.115, th - 0.012, th, {'+z': 'tin', 'all': 'sw_tin'})
    n0 = B.mark()
    B.cyl(ATLAS_MAT, (0, 0, 0), (0.15, 0, 0), 0.02, seg=10, cell='sw_torch')
    B.cyl(ATLAS_MAT, (0.15, 0, 0), (0.19, 0, 0), 0.022, 0.03, seg=12, cell='sw_brass')
    B.cyl(ATLAS_MAT, (0.19, 0, 0), (0.192, 0, 0), 0.028, seg=12, cell='sw_glass')
    B.xform(n0, Matrix.Translation((250.35, 0.62, 0.02)) @ Matrix.Rotation(2.6, 4, 'Z'))
    lx, ly, lz = HIDE_LAMP
    B.cyl(ATLAS_MAT, (lx, ly, 0.0), (lx, ly, 0.05), 0.05, 0.04, seg=14, cell='sw_brass')
    B.cyl(ATLAS_MAT, (lx, ly, lz + 0.05), (lx, ly, lz + 0.075), 0.035, 0.015, seg=12, cell='sw_brass')
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        B.cyl(ATLAS_MAT, (lx + 0.045 * math.cos(a), ly + 0.045 * math.sin(a), 0.05), (lx + 0.04 * math.cos(a), ly + 0.04 * math.sin(a), lz + 0.055),
              0.004, seg=4, cell='sw_brass')
    B.torus(ATLAS_MAT, (lx, ly, lz + 0.09), (1, 0, 0), 0.02, 0.003, seg=10, rseg=4, cell='sw_brass')
    global PLAYER_INFO
    PLAYER_INFO = place_card_player(B)
    ob = B.obj('Att15Hide', coll)
    L = MB()
    L.sphere('Att15HideLamp', (lx, ly, lz), 0.034, seg=12, scale=(1, 1, 1.3))
    lamp = L.obj('Att15HideLamp', coll, origin=HIDE_LAMP)
    return ob, lamp


PLAYER_INFO = None


def place_card_player(B):
    """The voice-card player (art/common/voice_props.py) on the biscuit tin, its front to the camera, lid shut, horn
    turned toward the nest, a card (att_escort) standing in its slot."""
    vp = _voice_props()
    if vp is None:
        print('dl15: voice props not ready; no card player placed')
        return None
    info = vp.card_player(B, vp.xform(loc=PLAYER_AT, turn=0.0), lid='closed', horn=-35.0, card=True)
    print('dl15: card player', {k: tuple(round(c, 3) for c in v) if hasattr(v, '__len__') else round(v, 3)
                                for k, v in info.items() if k in ('card', 'top', 'mouth', 'height', 'crank_pivot')})
    return info


# =====================================================================================================================
# The teaching figures on rail stands
# =====================================================================================================================
def figure_mesh():
    """DL-12/13's jointed pupil model (art/ch1/dl13.py pupil()), its castor stand replaced by a rail bogie: two side
    frames, four flanged wheels on the rails (gauge 0.16), a bolster and the post up to the stand's platform. Faces +x;
    origin on the rail top under the stand's centre (the platform 0.1 above it, as on castors)."""
    import dl13
    B = MB()
    w, j, st = B.m('PupilWood'), B.m('CrateWood'), B.m('WornIron')
    tmp = bmesh.new()
    dl13.pupil(tmp, 0, 1, 2, 'stand', False)
    gone = [v for v in tmp.verts if v.co.z < 0.0995 or (abs(v.co.z - 0.1) < 1e-4 and v.co.xy.length < 0.05)]
    bmesh.ops.delete(tmp, geom=gone, context='VERTS')
    bmesh.ops.transform(tmp, matrix=Matrix.Rotation(math.radians(90), 4, 'Z'), verts=tmp.verts)
    me = bpy.data.meshes.new('_dl15_tmp')
    tmp.to_mesh(me)
    tmp.free()
    n0 = len(B.bm.faces)
    B.bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    remap = {0: w, 1: j, 2: st}
    B.bm.faces.ensure_lookup_table()
    for f in B.bm.faces[n0:]:
        f.material_index = remap.get(f.material_index, st)
    bm = B.bm
    for sy in (-1, 1):
        y = sy * RAIL_G
        add_box(bm, (0, y, 0.048), (0.34, 0.018, 0.024), mat=st)                     # the side frame
        for sx in (-1, 1):
            x = sx * 0.11
            add_cyl(bm, (x, y - 0.008, 0.03), (x, y + 0.008, 0.03), 0.03, mat=st, seg=12)
            yf = y - sy * 0.011
            add_cyl(bm, (x, yf - 0.003, 0.03), (x, yf + 0.003, 0.03), 0.038, mat=st, seg=12)   # the flange, inside the rail
            add_box(bm, (x, y + sy * 0.014, 0.04), (0.05, 0.008, 0.03), mat=st)     # the axle box
    for sx in (-1, 1):
        add_cyl(bm, (sx * 0.11, -RAIL_G, 0.03), (sx * 0.11, RAIL_G, 0.03), 0.008, mat=st, seg=6)
        add_box(bm, (sx * 0.175, 0, 0.05), (0.012, 0.2, 0.03), mat=st)              # the headstocks
        add_cyl(bm, (sx * 0.18, 0, 0.05), (sx * 0.2, 0, 0.05), 0.022, mat=st, seg=10)   # buffers: they meet, not pass
    add_box(bm, (0, 0, 0.066), (0.1, 0.18, 0.016), mat=st)                              # the bolster
    add_cyl(bm, (0, 0, 0.074), (0, 0, 0.1), 0.032, mat=st, seg=10)
    return B


def build_figures(coll):
    B = figure_mesh()
    bm = B.bm
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new('Att15FigureRail')
    bm.to_mesh(me)
    bm.free()
    for n in B.names:
        me.materials.append(mat(n))
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.set_sharp_from_angle(angle=math.radians(35))
    out = []
    for name, loc in (('Att15FigA', (FIGA_X, RAIL_Y, RAIL_H)), ('Att15FigB', (FIGB_X, RAIL_Y, BAL[4] + RAIL_H))):
        ob = bpy.data.objects.new(name, me)
        ob.location = loc
        coll.objects.link(ob)
        out.append(ob)
    return out


# =====================================================================================================================
def tris(ob):
    if ob.type != 'MESH':
        return 0
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def build_set(dl01, m, coll):
    make_atlas(ATLAS_PATH)
    B = MB()
    build_shell(B)
    build_balcony(B)
    build_lift_static(B)
    build_rails(B, FLOOR_RAIL[0], FLOOR_RAIL[1], 0.0)
    build_front_row(B)
    build_boards(B)
    build_teacher(B)
    build_partition(B)
    objs = []
    lights = build_lighting(B, coll)
    objs.append(B.obj('Att15Set', coll))
    objs.append(lights)
    objs.append(build_rows(coll))
    objs.append(build_chair(coll))
    objs.append(build_bell(coll))
    objs.extend(build_hide(coll))
    objs.append(build_lift(coll))
    objs.append(build_gate(coll))
    objs.append(build_cw(coll))
    objs.append(build_lamp(coll, 'Att15LampPupil', LAMP_PUPIL))
    objs.append(build_lamp(coll, 'Att15LampEscort', LAMP_ESCORT))
    for k, x in enumerate(ATT_LAMPS):
        objs.append(build_lamp(coll, 'Att15Lamp%d' % (k + 1), (x, ATT_FACE - 0.01, ATT_LAMP_Z), r=0.05, squash=0.55))
    objs.append(build_door(coll))
    objs.append(build_flap(coll))
    objs.extend(build_figures(coll))
    bpy.context.view_layer.update()
    total_t, total_p = 0, 0
    seen = set()
    for ob in objs:
        if ob.type != 'MESH':
            continue
        t = tris(ob)
        prim = len(ob.material_slots)
        total_t += t
        total_p += prim
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        print('dl15: %-16s tris %6d mats %d %-70s x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f  origin %s' % (
            ob.name, t, prim, [s.material.name for s in ob.material_slots],
            min(v.x for v in bb), max(v.x for v in bb), min(v.y for v in bb), max(v.y for v in bb), min(v.z for v in bb),
            max(v.z for v in bb), tuple(round(c, 3) for c in ob.location)))
        seen.update(s.material.name for s in ob.material_slots)
    print('dl15: total tris %d, draw calls (material slots) %d, materials %s' % (total_t, total_p, sorted(seen)))
    return objs


REPORT = """DL-15 One Pupil Missing (art/ch1/dl15.py). Game coords: (x, y, z) = Blender (x, z, -y).

MOVED (origin = pivot, world, built state):
- Att15FigA (259.2, 0.03, -0.55), Att15FigB (249.9, 1.63, -0.55): rail figures, origin on rail top under the stand, face
  +x. Same mesh (Att15FigureRail). Stand 0.40 long (buffers +-0.20), body +-0.13 deep, 0.95 tall above rail top.
  Seat stops (origin x): S1 253.2, S2 254.6, S3 256.0 (brass plates in the channel).
- Att15Lift: origin (251.9, 1.6, -0.3) = deck top centre, built UP; deck x 251.4-252.4, z -0.9..0.3; travel -1.6 in y
  (down: deck top 0, flush in its 0.06 pit). Includes its rail stub and its hoist cable.
- Att15LiftGate: origin (252.4, 1.6, -0.9) on the back hinge post; shut along x 252.4, z -0.9..0.27, 0.85 high. Move
  with the deck; open = rotate about game y by -90 deg (free end swings into the lift along its back, to x 251.2).
- Att15LiftCW: origin (251.57, 0.475, -1.2), built low; travel +1.6 in y as the lift goes down.
- Att15Door: hinge (263.9, 0, -0.38); leaf z -0.375..0.3 (y -0.3..0.375 Blender), 2.0 high, shut; open = rotate
  about game y by +95 deg. NOTE: hinge is at Blender y 0.38, not 0.55: the flap and the figures need y 0.40-0.72 clear.
- Att15Flap: hinge (263.815, 1.05, -0.56); 0.30 wide (Blender y 0.41-0.71), z0 0.035; open = rotate about game z by
  +80 deg (Blender ry -80): swings up toward +x.
- Emissive (own objects + materials): Att15LampPupil (252.11, 2.2, -0.85), Att15LampEscort (252.25, 2.2, -0.85) static
  on the right guide post 0.6 above the up-deck; Att15Lamp1/2/3 at x 257.64 / 258.1 / 258.56, y 2.17, z -1.36
  (R. ABEL, T. ORME, M. D.); Att15HideLamp (250.62, 0.13, -1.12), on as built.
- Static named: Att15Chair (origin 255.92, 0, -0.31; seat top 0.30; footprint x 255.81-256.03, z -0.42..-0.20),
  Att15Bell (258.1, 2.74, -1.4).

SURFACES (x0, x1, top):
- Floor 248.15-263.75, 0. Under the balcony (248.15-251.4) ceiling 1.5. Lift pit 251.4-252.4: -0.06 while lift is up.
- Balcony 248.15-251.4, 1.6 (lane-deep); rails 1.63. Lift deck 251.4-252.4, 1.6 up / 0 down.
- Rails everywhere +0.03 (no climb). Mara's chair seat 0.30 (Blender y 0.20-0.42: just behind the lane).
- Behind the lane, not walkable from it: front-row desks 0.49-0.60 sloped, teacher's desk 0.72, cot 1.98.
WALLS/LIMITS: left wall face x 248.15 (both levels); end partition face 263.75 (door 2.0 high when open); ceiling 3.6;
hatch in back wall x 248.55-249.35, sill 1.6, head 2.4, duct z -1.4..-2.6, open toward -x behind the wall. Gate blocks
the lift's right edge while shut. Two slim columns at x 248.27, 251.29, z +0.36 (in front of the lane, not blocking).

SECRET ROOM: floor x 248.3-251.2, z -0.4..-1.4, clear 1.5. Blanket at z -0.35; gap x 249.56-250.12. Path: from the lane
at x 249.8 straight in to z -0.6 (stop: the tin is at z -0.81..-1.03). Voice player (att_escort) on the biscuit tin:
base (249.95, 0.10, -0.92), card (249.95, 0.25, -0.875), horn mouth (249.91, 0.45, -0.81). Use it from x 249.95.

LIGHTS (index.html P/S format, game coords):
P(0xffd8b0, 1.8, 4.5, 250.2, 2.95, -0.45)   sick bay pendant
P(0xbcd0e8, 0.5, 2.0, 248.95, 2.0, -1.3)    the duct mouth
S(0xffe0b8, 5, 5, [252.0, 3.2, 1.2], [252.0, 2.1, -0.8], 0.45)   lift sign + PUPIL/ESCORT
S(0xffd8a8, 7, 6, [254.6, 3.0, 0.6], [254.6, 0.35, -0.9], 0.75, true)   S1/S2 and the rail
S(0xffe0b8, 5, 5, [256.0, 2.9, 0.9], [256.0, 0.45, -0.7], 0.4, true)   Mara's desk lid and chair
S(0xffe2c0, 4.5, 5, [258.1, 3.2, 1.0], [258.1, 2.1, -1.38], 0.4)   attendance board, bell
S(0xffe6c8, 8, 7, [260.3, 3.3, 1.4], [260.3, 1.4, -1.38], 0.6, true)   blackboard, figure A
P(0xffd8b0, 1.0, 3.5, 262.9, 2.6, 0.0)      door end
P(0xb8c8dc, 0.35, 4, 254.8, 2.6, -2.6)      alcove of desks, dim and cool
P(0xffb870, 1.8, 2.4, 250.62, 0.25, -0.95), P(0xffb873, 0.5, 1.4, 249.8, 0.15, -0.25)   hide lamp + floor slit

MATERIALS: reused WORN CrateWood, PigeonWood, WornIron, PupilWood, HandledBrass, LessonPlaster, LessonDado, DarkMetal;
PLAIN Brass, Copper; voice-prop HandWorn, ParcelPaper; EMIT AttBulbGlow (pendants). Image: Att15Atlas
(textures/dl15_atlas.png, passes through as a map). New EMIT entries:
Att15LampPupil: [.72, 1, .78, 0], Att15LampEscort: [1, .66, .26, 0], Att15Lamp1: [1, .86, .62, 0],
Att15Lamp2: [1, .86, .62, 0], Att15Lamp3: [1, .86, .62, 0], Att15HideLamp: [1, .7, .4, 5],
Suggested lamp() colours: Pupil 0xb8ffc8, Escort 0xffa848, Lamp1-3 0xffdca0.

TRIANGLES: 28.3k in 20 objects (Att15Set 7.4k, Rows 5.5k, Hide 5.0k, each figure 3.5k); ~50 material slots.
Cables above the ceiling sit in a black trunk (invisible on the game's background).
"""
