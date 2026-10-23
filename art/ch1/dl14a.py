"""Chapter 1 Attendance, DL-14a Lights Out (game x 248.0 to 263.0). Spec: docs/chapter1_expansion_build.md (DL-14a);
design: docs/chapter1_expansion_proposal.md.

The school dormitory at rest hour. He comes out of the duct (from DL-14's hatch) through a vent in the linen cupboard
onto bunk 1's top deck. Along the lane: bunk 1 (two iron bunks pushed together), locker 1, the wall of rest-hour
things (the decoy gown pegs, the REST HOUR rules, the red brake lever, the night-light's dial, the painted tin sun),
locker 2, the three friends' bunks pushed together (R. ABEL, T. ORME, M. DALE on their ends; a torch and three biscuits
under them), locker 3, the crank on its iron standard with its drive plate, the nurse's chair with her weighted wool cape,
the eye (a lux meter) and its four lamps, and the door in the end wall (LIGHTS OUT) with the figures' rail stub beside
it. Over bunks 2, W1's blackout blind hangs out on brackets (y 1.0) in front of the frosted window to the light well;
at the right, W2's blind in front of the reeded glass to the night corridor. One cord drives both. Through three
arches in the back wall, the second ward: rows of made-up beds in the dark, the night at its far windows.

Called by build_attendance.py as build_set(dl01, m, coll), in final world coordinates (no shift).
Blender (x, y, z) is the game's (x, z, -y): +y is away from the camera, z is up. The lane is y = 0, the floor z = 0.

What the game moves (origin = pivot, world coordinates; REPORT at the bottom has the game's numbers):
    Att14aPawl        the REST HOUR brake lever; pivot (252.3, 1.36, 0.6); built off (handle up); +40 deg about x brakes
    Att14aDialHand    the night-light dial's hand; origin on the dial's centre; built pointing up; turns clockwise
    Att14aSunLamp     the tin sun's glass (own emissive); origin the sun's centre
    Att14aCrank       the handwheel at 258.7; origin on its axle at the wheel's centre
    Att14aBlindW1     W1's blind fabric, built DOWN (to 1.97); origin the middle of its roller axis; scale z to roll
    Att14aHemW1       W1's hem bar and its peg; origin the peg's hook point (256.2, 1.0, 1.93); moves with the blind
    Att14aBlindW2     W2's blind, built DOWN (hem bar included, to 1.95); origin the middle of its roller axis
    Att14aGown        the nurse's weighted wool cape on its hanger; origin the hanger's hook point; on the chair's hook
    Att14aDoor        the door, built shut; origin on its hinge (262.92, 0.45, 0)
    Att14aEyeSun, Att14aEyeW1, Att14aEyeW2 (small amber), Att14aEyeDark (big green): the eye's lamps, own emissives
Static: Att14aSet (the room), Att14aWard (the back ward's shell) and Att14aWardBed01..16 (linked duplicates of one
bed), Att14aGlobe (EMIT AttGlobeLamp), Att14aWellGlow / Att14aCorridorGlow / Att14aWardNight (EMIT glass), and the
empty Att14aSpeaker at the tannoy's horn.
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
ATLAS_PATH = os.path.join(TEX, 'dl14a_atlas.png')
SIGNS_PATH = os.path.join(TEX, 'dl14a_signs.png')
ATLAS_MAT = 'Att14aAtlas'          # bedding, gowns, lockers, small things, swatches
SIGNS_MAT = 'Att14aSigns'          # every printed thing: the rules, the drive plate, the eye's board, the dial, cards

# =====================================================================================================================
# Layout (Blender world; game x = x). The spec's numbers, which the game codes against.
# =====================================================================================================================
X0, X1 = 248.0, 263.0
LWALL = (248.0, 248.15)            # the left wall (DL-14's end wall at 247.85 stays; the gap stays dark)
RWALL = (262.85, 263.0)            # the end wall with the door
BACK_Y, BACK_T = 1.4, 0.2          # the back wall's face and thickness
BACK_Y2 = BACK_Y + BACK_T
CEIL = 3.5
FRONT_Y = -0.6                     # the cut toward the camera: walls and ceiling stop here
FLOOR_Y0 = -1.6
DADO = 1.0
DECK = 1.15                        # every bunk's top deck
LOWER = 0.5                        # every bunk's lower bed (decor)

VENT = (248.55, 249.35, 1.15, 1.8)                 # the duct's vent in the linen cupboard's face: x0, x1, sill, head
CUPBOARD = (248.15, 249.65, 2.62)                  # the built-in linen cupboard: x0, x1, its top
BUNK1 = (248.3, 250.3, -0.35, 1.4)                 # x0, x1, y0, y1 (two iron bunks pushed together, split at 249.3)
LOCKERS = ((250.3, 250.8), (254.3, 254.8), (257.6, 258.1))
LOCKER_Y, LOCKER_TOP = (-0.3, 0.5), 0.55
PAWL = (252.3, 1.36, 0.6)                          # the REST HOUR brake's pivot
PAWL_LEN = 0.45
DIAL = (253.0, 1.35)                               # the night-light dial's centre (x, z)
DIAL_R = 0.26                                      # its painted face
DIAL_FACE_Y = 1.368
HAND_Y = 1.356                                     # Att14aDialHand's origin (y): just in front of the face
SUN = (253.9, 2.55)                                # the tin sun's centre (x, z)
SUN_GLASS_R = 0.15
SUN_Y = 1.355                                      # Att14aSunLamp's origin (y)
PEG_X = (251.02, 251.26, 251.5, 251.74, 251.98)    # the decoy gown pegs; the free one at 251.5
PEG_FREE = 251.5
PEG_REST = (1.345, 0.80)                           # a peg's hook point: y, z (where a hanger's hook sits)
PEGBOARD = (250.9, 252.06, 0.74, 0.88, 1.383)      # x0, x1, z0, z1, face y
RULES = (250.95, 252.2, 1.25, 2.2)                 # the REST HOUR rules sign: x0, x1, z0, z1
BUNKS2 = (254.8, 257.6, -0.35, 1.3)                # the three friends' bunks, pushed together
NAMES = ('R. ABEL', 'T. ORME', 'M. DALE')
W1 = (255.4, 257.0, 1.6, 3.1)                      # window to the light well: x0, x1, sill, head
W1_BLACK = 2.05                                    # its lower panes are blacked out up to here (the blind covers the rest)
W2 = (259.3, 260.9, 1.9, 3.1)                      # borrowed light from the night corridor
ROLLER_Z, ROLLER_R = 3.25, 0.035
W1_BLIND = (255.3, 257.1)                          # fabric x
W1_ROLLER_Y = 1.075                                # W1's roller axis: out on brackets, the fabric at y 1.04
W1_FABRIC_Y = W1_ROLLER_Y - ROLLER_R
W1_FABRIC_BOTTOM = 1.97
HEM_W1 = (256.2, 1.0, 1.93)                        # the peg's hook point on W1's hem bar (Att14aHemW1's origin)
HEM_BAR = (1.02, 1.06, 1.95, 2.0)                  # W1's hem bar: y0, y1, z0, z1 (the fabric ends inside it at 1.97)
W2_BLIND = (259.2, 261.0)
W2_ROLLER_Y = 1.3
W2_FABRIC_Y = W2_ROLLER_Y - ROLLER_R
W2_HEM = 1.95                                      # W2's blind's bottom, hem bar included
CRANK = (258.7, 0.32, 0.5, 0.19)                   # the handwheel: x, y, z, r
STANDARD = (258.7, 0.66)                           # the crank's iron standard (a column to the ceiling): x, y
GEARBOX = (258.52, 258.88, 0.5, 0.8, 0.26, 1.08)
CRANK_PULLEY = (258.7, 1.2, 0.07)                  # on the gearbox's top: x, z, r (axis along y at STANDARD y)
DRIVE_PLATE = (259.0, 259.56, 0.42, 0.91, 0.6145)  # x0, x1, z0, z1, face y
W1_DRUM = (257.12, 257.2, 0.065)                   # the cord's drum on W1's roller: x0, x1, r
W2_DRUM = (259.08, 259.16, 0.065)
CHAIR = (260.6, 0.4, 0.42)                         # the nurse's chair: seat centre x, y; seat top. It faces -x.
CHAIR_SEAT = 0.4                                   # seat size (square)
GOWN_HOOK = (261.0, 0.4, 0.95)                     # the hook on the chair's back (a brass arm): the gown's hook point
EYE = (261.9, 2.25)
EYEBOARD = (261.35, 262.45, 1.2, 2.65, 1.384)      # the eye's board: x0, x1, z0, z1, face y
EYE_LAMPS = {'Att14aEyeSun': (261.6, 1.86, 0.034), 'Att14aEyeW1': (261.9, 1.86, 0.034), 'Att14aEyeW2': (262.2, 1.86, 0.034),
             'Att14aEyeDark': (261.9, 1.53, 0.07)}  # x, z, r; glass centres at y 1.37
EYE_LAMP_Y = 1.37
DOOR = (-0.45, 0.45, 1.75)                         # the doorway: y0, y1, head
DOOR_HINGE = (262.92, 0.45, 0.0)
RAIL = (261.6, 263.0)                              # the figures' rail stub
RAIL_Y, RAIL_G, RAIL_H = 0.55, 0.08, 0.03          # rails at y 0.47 / 0.63, rail top 0.03
CHAN = (0.39, 0.71)
RAIL_HATCH = (0.45, 0.76, 1.08)                    # the low opening beside the door for the rail: y0, y1, head
ARCHES = ((249.75, 250.85), (254.4, 255.2), (257.25, 258.55))
ARCH_CROWN = 2.85
WARD = (248.15, 259.0, 6.4)                        # the back ward: x0, x1, far wall's face (y)
WARD_BED_X = tuple(248.9 + 1.25 * k for k in range(8))
WARD_ROWS = (2.15, 4.55)                           # each row's foot ends (y); beds 1.7 long, heads to +y
WARD_WINDOWS = ((249.6, 250.5), (253.3, 254.2), (257.0, 257.9))
TANNOY = (252.75, BACK_Y - 0.002, 2.98)
GLOBE = (251.3, 0.05, 3.1)                         # the one dim ceiling globe (lit)
DEAD_GLOBES = ((256.2, 0.05, 3.1), (260.3, 0.05, 3.1))

# The night-light's cycle (the dial's bands), seconds of a 10 s cycle.
CYCLE = 10.0
BANDS = (('BRIGHT', 0.0, 3.0), ('DIMMING', 3.0, 4.5), ('DARK', 4.5, 8.0), ('BRIGHTENING', 8.0, 10.0))

# =====================================================================================================================
# Materials (the game's existing names wherever one fits; fallbacks for a lone build)
# =====================================================================================================================
KNOWN_WORN = {
    'WinPlaster': dict(base=(.29, .27, .21), dirt=(.15, .13, .095), chip=(.2, .185, .15), rough=.9, chip_rough=.85,
                       metallic=0, grime_scale=3, chip_scale=18, chip_amount=.7, streaks=.6, dust=(.24, .22, .18), dust_amount=.5),
    'WinDado': dict(base=(.12, .16, .135), dirt=(.065, .075, .06), chip=(.30, .27, .21), rough=.55, chip_rough=.85,
                    metallic=0, grime_scale=4, chip_scale=22, chip_amount=.68, streaks=.5, dust=(.16, .17, .15), dust_amount=.4),
    'WinLino': dict(base=(.115, .085, .05), dirt=(.06, .045, .03), chip=(.075, .07, .062), rough=.7, chip_rough=.9,
                    metallic=0, grime_scale=3, chip_scale=14, chip_amount=.66, streaks=.3, dust=(.13, .12, .1), dust_amount=.6),
    'PigeonWood': dict(base=(.12, .085, .055), dirt=(.06, .045, .03), chip=(.2, .15, .1), rough=.85, chip_rough=.8, metallic=0,
                       grime_scale=6, chip_scale=30, chip_amount=.75, dust=(.1, .09, .08), dust_amount=.6),
    'CrateWood': dict(base=(.18, .12, .07), dirt=(.08, .055, .035), chip=(.25, .19, .12), rough=.85, chip_rough=.8, metallic=0,
                      grime_scale=6, chip_scale=30, chip_amount=.75, streaks=.6),
    'WornIron': dict(base=(.045, .043, .04), dirt=(.06, .035, .02), chip=(.3, .29, .27), rough=.7, chip_rough=.35, metallic=.6,
                     grime_scale=9, chip_scale=40, chip_amount=.6, dust=(.09, .085, .075), dust_amount=.4),
    'CastIron': dict(base=(.035, .034, .032), dirt=(.05, .03, .018), chip=(.13, .12, .1), rough=.75, chip_rough=.45,
                     metallic=.5, dust=(.08, .075, .065), grime_scale=9, chip_scale=50, chip_amount=.72, dust_amount=.5),
    'HandledBrass': dict(base=(.2, .14, .06), dirt=(.08, .06, .03), chip=(.62, .46, .2), rough=.5, chip_rough=.2, metallic=.85,
                         grime_scale=8, chip_scale=26, chip_amount=.5, dust=(.12, .1, .07), dust_amount=.2),
    'LeverRed': dict(base=(0.45, 0.05, 0.03), dirt=(0.2, 0.04, 0.02), chip=(.3, .29, .27), rough=.6, chip_rough=.35,
                     metallic=.2, grime_scale=8, chip_scale=30, chip_amount=.6),
}
KNOWN_PLAIN = {'Brass': ((.45, .32, .12), .45, .8), 'GaugeNeedle': ((.02, .018, .016), .4, .3),
               'EyeDark': ((.003, .003, .003), .3, 0.0)}
SWITCHED_EMIT = {   # the lamps the game switches: own objects, own materials (as built: sun bright, both blinds down)
    'Att14aSunLamp': ((1.0, 0.8, 0.42), 4.0),
    'Att14aEyeSun': ((1.0, 0.6, 0.18), 3.0),
    'Att14aEyeW1': ((1.0, 0.6, 0.18), 0.0),
    'Att14aEyeW2': ((1.0, 0.6, 0.18), 0.0),
    'Att14aEyeDark': ((0.36, 1.0, 0.46), 0.0),
}
STATIC_EMIT = {     # new static glows (EMIT entries in REPORT); AttGlobeLamp is already in the game's table
    'Att14aWellGlow': ((0.72, 0.84, 1.0), 2.2),
    'Att14aCorridorGlow': ((1.0, 0.72, 0.4), 1.8),
    'Att14aWardNight': ((0.4, 0.48, 0.66), 0.22),
    'AttGlobeLamp': ((1.0, 0.86, 0.62), 3.0),
}


def mat(name):
    mt = bpy.data.materials.get(name)
    if mt is not None:
        return mt
    if name in KNOWN_WORN:
        return worn_material(name, **KNOWN_WORN[name])
    if name in KNOWN_PLAIN:
        c, r, mtl = KNOWN_PLAIN[name]
        return simple_material(name, c, r, metallic=mtl)
    if name in SWITCHED_EMIT or name in STATIC_EMIT:
        c, s = SWITCHED_EMIT.get(name) or STATIC_EMIT[name]
        return emission_material(name, c, s)
    if name in (ATLAS_MAT, SIGNS_MAT):
        mt, nt, bsdf = d17._new_material(name)
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(ATLAS_PATH if name == ATLAS_MAT else SIGNS_PATH, check_existing=True)
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = 0.8 if name == ATLAS_MAT else 0.55
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
# Textures (PIL, at build time): textures/dl14a_atlas.png (cloth and small things) and dl14a_signs.png (print)
# =====================================================================================================================
ATLAS = 1024
CELLS = {
    'blanket': (0, 0, 256, 256), 'blanket2': (256, 0, 512, 256),
    'sheet': (512, 0, 640, 128), 'pillow': (640, 0, 768, 128), 'ticking': (768, 0, 1024, 128),
    'gown': (512, 128, 768, 384),
    'gown1': (768, 128, 896, 256), 'gown2': (896, 128, 1024, 256), 'gown3': (768, 256, 896, 384), 'gown4': (896, 256, 1024, 384),
    'locker': (0, 256, 116, 384), 'grille': (128, 256, 256, 384), 'torch': (256, 256, 384, 288),
}
SWATCH = {'sw_wood': (104, 74, 46), 'sw_brass': (170, 132, 64), 'sw_iron': (38, 37, 35), 'sw_dark': (8, 8, 8),
          'sw_glass': (70, 74, 72), 'sw_cream': (214, 204, 176), 'sw_green': (44, 66, 54), 'sw_red': (132, 48, 40),
          'sw_string': (184, 172, 140), 'sw_white': (206, 202, 190), 'sw_tin': (120, 124, 124), 'sw_sun': (226, 178, 66),
          'sw_ray': (206, 124, 40), 'sw_black': (16, 16, 18), 'sw_chalk': (214, 210, 198), 'sw_lockerpaint': (86, 106, 88),
          'sw_blanket': (84, 82, 80), 'sw_biscuit': (186, 138, 78), 'sw_torch': (40, 66, 104), 'sw_lens': (226, 220, 176),
          'sw_spring': (58, 58, 56), 'sw_paper': (204, 196, 172), 'sw_cup': (196, 196, 190), 'sw_ink': (24, 24, 36),
          'sw_gowncord': (176, 150, 96), 'sw_ward': (70, 70, 72), 'sw_wardsheet': (150, 148, 140), 'sw_rubber': (20, 20, 19),
          'sw_lining': (128, 30, 30), 'sw_lead': (96, 98, 100)}
for _i, _k in enumerate(SWATCH):
    CELLS[_k] = (32 * (_i % 32), 960 - 32 * (_i // 32), 32 * (_i % 32) + 32, 992 - 32 * (_i // 32))

SIGNS = 1024
SCELLS = {
    'rules': (0, 0, 640, 486),              # 1.25 x 0.95 m
    'drive': (640, 0, 1024, 336),           # 0.56 x 0.49 m
    'eyeboard': (0, 486, 400, 1013),        # 1.10 x 1.45 m
    'dial': (640, 336, 896, 592),           # the night-light dial's face (a disc)
    'w1': (896, 336, 960, 400), 'w2': (960, 336, 1024, 400),
    'card0': (400, 486, 592, 546), 'card1': (400, 546, 592, 606), 'card2': (400, 606, 592, 666), 'cardx': (400, 666, 592, 726),
    'lightsout': (592, 592, 944, 696),      # 0.44 x 0.13 m
    'brake': (592, 696, 864, 776),          # 0.34 x 0.10 m
    'nightlight': (592, 776, 842, 826),     # 0.30 x 0.06 m
    'linen': (592, 826, 842, 884),          # 0.30 x 0.07 m
    'tree': (400, 726, 592, 950),           # Mara's pencil tree on the plaster, 0.24 x 0.28 m
    'ward': (592, 884, 842, 934),           # WARD 2, over the right arch, 0.40 x 0.08 m
}


def cell_uv(name):
    if name in SCELLS:
        x0, y0, x1, y1 = SCELLS[name]
        S = SIGNS
    else:
        x0, y0, x1, y1 = CELLS[name]
        S = ATLAS
    return x0 / S, 1 - y1 / S, x1 / S, 1 - y0 / S


def cell_mid(name):
    u0, v0, u1, v1 = cell_uv(name)
    return (u0 + u1) / 2, (v0 + v1) / 2


def _font(size, kind='carlito'):
    from PIL import ImageFont
    paths = {'sans-bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
             'sans': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
             'serif': '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
             'carlito': '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf',
             'carlito-r': '/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf',
             'hand': '/usr/share/fonts/truetype/crosextra/Caladea-Italic.ttf'}
    try:
        return ImageFont.truetype(paths[kind], size)
    except OSError:
        return ImageFont.load_default()


def _text(d, xy, text, size, fill, kind='carlito', anchor='mm', max_w=None):
    """Text, shrunk until it fits max_w pixels."""
    while max_w and size > 8:
        f = _font(size, kind)
        x0, _, x1, _ = d.textbbox((0, 0), text, font=f)
        if x1 - x0 <= max_w:
            break
        size -= 1
    d.text(xy, text, font=_font(size, kind), fill=fill, anchor=anchor)


def _lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


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


def _fade(img, seed, grey=(132, 130, 122), k=0.3, warm=(1.0, 0.96, 0.86), dust=0.12):
    """Sun-faded, varnish-yellowed, dusty: the school's colours dimmed toward grey."""
    import numpy as np
    from PIL import Image
    a = np.asarray(img.convert('RGB')).astype(float)
    a = a * (1 - k) + np.array(grey) * k
    a *= np.array(warm)
    n = _noise(a.shape[1], a.shape[0], 6, seed)
    a = a * (1 - dust * (n[..., None] - 0.5) * 2) + 18 * dust * (n[..., None] > 0.62)
    return Image.fromarray(np.clip(a, 0, 255).astype('uint8'), 'RGB')


def _chips(img, box, seed, n=6, col=(52, 56, 60, 220)):
    """Chips in an enamel plate's edges (box: the plate's pixel rectangle in img)."""
    from PIL import ImageDraw
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img, 'RGBA')
    rnd = random.Random(seed)
    for _ in range(n):
        if rnd.random() < 0.5:
            ex, ey = rnd.choice((rnd.uniform(x0 + 3, x0 + 16), rnd.uniform(x1 - 16, x1 - 3))), rnd.uniform(y0 + 3, y1 - 3)
        else:
            ex, ey = rnd.uniform(x0 + 3, x1 - 3), rnd.choice((rnd.uniform(y0 + 3, y0 + 12), rnd.uniform(y1 - 12, y1 - 3)))
        r = rnd.uniform(1.5, 4)
        d.ellipse((ex - r, ey - r * 0.7, ex + r, ey + r * 0.7), fill=col)


def _weave(w, h, base, seed, stripes=(), check=None, nap=0.18):
    """Woollen cloth: a base colour, a weave, a nap of noise; stripes = [(y0, y1, rgb)] across; check = (period, rgb2)."""
    import numpy as np
    from PIL import Image
    n = _noise(w, h, 4, seed)
    a = np.ones((h, w, 3)) * np.array(base, float)
    if check:
        per, c2 = check
        yy, xx = np.mgrid[0:h, 0:w]
        band_x = ((xx // (per // 2)) % 2 == 0)
        band_y = ((yy // (per // 2)) % 2 == 0)
        a[band_x] = a[band_x] * 0.6 + np.array(c2, float) * 0.4
        a[band_y] = a[band_y] * 0.6 + np.array(c2, float) * 0.4
        thin = ((xx % per) < 2) | ((yy % per) < 2)
        a[thin] = a[thin] * 0.5 + np.array((200, 180, 120), float) * 0.5
    for y0, y1, rgb in stripes:
        a[y0:y1] = np.array(rgb, float)
    weave = np.sin(np.arange(h)[:, None] * 2.1) * 0.035 + np.sin(np.arange(w)[None, :] * 2.4) * 0.035
    a *= (1 - nap + 2 * nap * n + weave)[..., None]
    return Image.fromarray(np.clip(a, 0, 255).astype('uint8'))


def make_atlas(path):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    img = Image.new('RGB', (ATLAS, ATLAS), (60, 58, 54))
    rnd = random.Random(14100)

    def put(name, tile):
        x0, y0, x1, y1 = CELLS[name]
        img.paste(tile.resize((x1 - x0, y1 - y0)), (x0, y0))
    # Blankets: grey institutional wool with two red stripes near the foot; a fawn one with a blue stripe (bunk 1).
    put('blanket', _weave(256, 256, (86, 84, 82), 14101, stripes=((208, 216, (122, 40, 36)), (224, 232, (122, 40, 36)))))
    put('blanket2', _weave(256, 256, (150, 136, 110), 14102, stripes=((212, 222, (52, 66, 102)),)))
    put('sheet', _weave(128, 128, (196, 192, 180), 14103, nap=0.08))
    pil = _weave(128, 128, (202, 198, 186), 14104, nap=0.06)
    dp = ImageDraw.Draw(pil)
    dp.rectangle((0, 0, 127, 10), fill=(176, 172, 160))                    # its seam and a darned patch
    dp.ellipse((70, 60, 96, 80), outline=(160, 156, 146), width=2)
    put('pillow', pil)
    tk = np.ones((128, 256, 3)) * np.array((200, 196, 182), float)
    for k in range(0, 256, 16):
        tk[:, k:k + 5] = np.array((70, 84, 120), float)
    tk *= (0.85 + 0.25 * _noise(256, 128, 3, 14105))[..., None]
    put('ticking', Image.fromarray(np.clip(tk, 0, 255).astype('uint8')))
    # The nurse's cape: heavy navy wool; at the bottom its hem band, stitched into pockets, lumpy with the lead weights.
    cape = _weave(256, 256, (38, 44, 70), 14106, nap=0.14)
    dc = ImageDraw.Draw(cape)
    dc.rectangle((0, 222, 255, 255), fill=(26, 30, 50))
    dc.line((0, 222, 255, 222), fill=(70, 76, 104), width=2)
    for k in range(0, 256, 28):
        dc.line((k, 224, k, 255), fill=(64, 70, 96), width=1)
        dc.ellipse((k + 6, 230, k + 22, 248), fill=(44, 50, 74))
    put('gown', cape)
    put('gown1', _weave(128, 128, (40, 50, 86), 14107, nap=0.15))
    put('gown2', _weave(128, 128, (58, 82, 60), 14108, check=(32, (90, 70, 40)), nap=0.15))
    put('gown3', _weave(128, 128, (118, 92, 64), 14109, check=(26, (80, 54, 36)), nap=0.15))
    put('gown4', _weave(128, 128, (92, 112, 140), 14110, nap=0.15))
    # A locker's door: painted green-grey, a panel, a brass card holder with its card, the knob.
    x0, y0, x1, y1 = CELLS['locker']
    lk = Image.new('RGB', (x1 - x0, y1 - y0), (86, 106, 88))
    dl = ImageDraw.Draw(lk)
    w, h = lk.size
    dl.rectangle((0, 0, w - 1, 10), fill=(70, 88, 72))
    dl.rectangle((8, 18, w - 9, h - 10), outline=(64, 80, 66), width=3)
    dl.rectangle((w // 2 - 22, 26, w // 2 + 22, 42), fill=(150, 116, 56))
    dl.rectangle((w // 2 - 19, 29, w // 2 + 19, 39), fill=(204, 196, 172))
    dl.line((w // 2 - 14, 34, w // 2 + 10, 34), fill=(60, 60, 80), width=1)
    dl.ellipse((w - 26, h // 2 - 5, w - 16, h // 2 + 5), fill=(150, 116, 56))
    put('locker', _fade(lk, 14111, k=0.12, dust=0.2))
    # The vent's grille (louvres), the torch's painted tin band.
    gr = Image.new('RGB', (128, 128), (64, 66, 64))
    dg = ImageDraw.Draw(gr)
    for k in range(10, 120, 12):
        dg.rectangle((8, k, 119, k + 6), fill=(110, 112, 108))
        dg.line((8, k + 7, 119, k + 7), fill=(20, 20, 20), width=2)
    dg.rectangle((0, 0, 127, 127), outline=(40, 40, 40), width=6)
    put('grille', _fade(gr, 14112, k=0.1, dust=0.25))
    tc = Image.new('RGB', (128, 32), (40, 66, 104))
    dt = ImageDraw.Draw(tc)
    dt.rectangle((0, 12, 127, 20), fill=(186, 150, 70))
    put('torch', tc)
    for name, rgb in SWATCH.items():
        x0, y0, x1, y1 = CELLS[name]
        ImageDraw.Draw(img).rectangle((x0, y0, x1 - 1, y1 - 1), fill=rgb)
    img.filter(ImageFilter.GaussianBlur(0.4)).save(path, optimize=True)


def _school_mark(d, mx, my, k, gold=(196, 150, 50), green=(40, 64, 50)):
    """The school's mark: a sun over an open book."""
    d.pieslice((mx - 44 * k, my - 74 * k, mx + 44 * k, my + 14 * k), 180, 360, fill=gold)
    for a_ in range(200, 341, 28):
        r = math.radians(a_)
        d.line((mx + 54 * k * math.cos(r), my - 30 * k + 54 * k * math.sin(r), mx + 76 * k * math.cos(r),
                my - 30 * k + 76 * k * math.sin(r)), fill=gold, width=max(2, int(5 * k)))
    d.polygon([(mx - 70 * k, my - 8 * k), (mx, my + 8 * k), (mx + 70 * k, my - 8 * k), (mx + 70 * k, my + 52 * k),
               (mx, my + 70 * k), (mx - 70 * k, my + 52 * k)], fill=green)


def _moon(d, cx, cy, r, fill, bg):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=fill)
    d.ellipse((cx - r * 0.45, cy - r * 1.1, cx + r * 1.55, cy + r * 0.9), fill=bg)


def _cord(d, pts, fill, w=3):
    d.line(pts, fill=fill, width=w, joint='curve')


def make_rules(img):
    """REST HOUR: the rules, enamel on steel, cream on green, a sleeping moon (1 px ~ 1.95 mm)."""
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = SCELLS['rules']
    w, h = x1 - x0, y1 - y0
    cream, green, ink = (222, 212, 184), (34, 62, 50), (26, 26, 24)
    p = Image.new('RGB', (w, h), cream)
    d = ImageDraw.Draw(p)
    d.rounded_rectangle((5, 5, w - 6, h - 6), radius=28, outline=green, width=12)
    d.rounded_rectangle((22, 22, w - 23, 118), radius=14, fill=green)
    _text(d, (w // 2, 72), 'REST HOUR', 82, cream)
    _moon(d, 88, 70, 30, (226, 200, 120), green)
    for k, (sx, sy) in enumerate(((524, 46), (556, 84), (590, 52))):
        _text(d, (sx, sy), 'z' if k < 2 else 'Z', 22 + 6 * k, (226, 200, 120), kind='serif')
    rules = ('1.  Lights out.', '2.  No talking.', '3.  Stay in your own bed.', '4.  Pupils are never unaccompanied.')
    for k, s in enumerate(rules):
        _text(d, (52, 168 + k * 66), s, 46, ink, anchor='lm', max_w=w - 104)
    d.line((52, 420, w - 160, 420), fill=green, width=3)
    _text(d, (52, 448), 'LOWER SCHOOL  ·  BY ORDER', 24, green, anchor='lm')
    _school_mark(d, w - 92, 436, 0.5)
    for sx, sy in ((30, 30), (w - 31, 30), (30, h - 31), (w - 31, h - 31)):
        d.ellipse((sx - 7, sy - 7, sx + 7, sy + 7), fill=(150, 146, 136), outline=(70, 66, 60), width=2)
    img.paste(_fade(p, 14120, k=0.14, dust=0.16), (x0, y0))
    _chips(img, (x0, y0, x1, y1), 14121, n=9)


def make_drive(img):
    """The drive plate by the crank: ONE CORD - TWO BLINDS, and a picture of just that: two blinds, W1 and W2, on their
    rollers, one cord round both drums and down to the crank. Nothing about which way they go or what the clutch does
    (the design review: that was the solution). 1 px ~ 1.46 mm."""
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = SCELLS['drive']
    w, h = x1 - x0, y1 - y0
    cream, green, ink, cloth, amber = (220, 212, 186), (34, 62, 50), (26, 26, 24), (46, 50, 60), (196, 128, 36)
    p = Image.new('RGB', (w, h), cream)
    d = ImageDraw.Draw(p)
    d.rounded_rectangle((3, 3, w - 4, h - 4), radius=18, outline=green, width=7)
    d.rounded_rectangle((13, 13, w - 14, 74), radius=9, fill=green)
    _text(d, (w // 2, 44), 'ONE CORD - TWO BLINDS', 40, cream, max_w=w - 40)
    # Two blinds, both half down, on their rollers; their drums side by side in the middle; the cord round both.
    ry = 104
    for cx, label in ((82, 'W1'), (w - 82, 'W2')):
        d.rounded_rectangle((cx - 62, ry - 10, cx + 62, ry + 10), radius=8, fill=(96, 70, 44), outline=ink, width=2)
        bot = 196
        d.rectangle((cx - 54, ry + 10, cx + 54, bot), fill=cloth, outline=ink, width=2)
        d.rectangle((cx - 58, bot, cx + 58, bot + 9), fill=(96, 70, 44), outline=ink, width=2)
        d.ellipse((cx - 22, 150 - 22, cx + 22, 150 + 22), fill=cream)
        _text(d, (cx, 151), label, 24, ink)
    cw = (w // 2, 262)                                                     # the crank's handwheel
    da, db = w // 2 - 32, w // 2 + 32                                      # the two drums
    for sx in (da, db):
        d.ellipse((sx - 11, ry - 11, sx + 11, ry + 11), fill=(120, 116, 106), outline=ink, width=2)
    cord = (60, 58, 54)
    _cord(d, [(da, ry - 11), (cw[0] - 16, ry - 11), (cw[0] - 16, cw[1])], cord, w=4)
    _cord(d, [(db, ry - 11), (cw[0] + 16, ry - 11), (cw[0] + 16, cw[1])], cord, w=4)
    _cord(d, [(da, ry + 11), (db, ry + 11)], cord, w=3)
    d.ellipse((cw[0] - 28, cw[1] - 28, cw[0] + 28, cw[1] + 28), fill=cream, outline=ink, width=6)
    for a in range(3):
        aa = math.radians(90 + 120 * a)
        d.line((cw[0], cw[1], cw[0] + 25 * math.cos(aa), cw[1] + 25 * math.sin(aa)), fill=ink, width=5)
    d.ellipse((cw[0] - 7, cw[1] - 7, cw[0] + 7, cw[1] + 7), fill=ink)
    d.arc((cw[0] - 42, cw[1] - 42, cw[0] + 42, cw[1] + 42), 200, 320, fill=amber, width=6)
    d.polygon([(cw[0] + 30, cw[1] - 40), (cw[0] + 42, cw[1] - 22), (cw[0] + 21, cw[1] - 24)], fill=amber)
    for sx, sy in ((18, 18), (w - 19, 18), (18, h - 19), (w - 19, h - 19)):
        d.ellipse((sx - 5, sy - 5, sx + 5, sy + 5), fill=(150, 146, 136), outline=(70, 66, 60), width=2)
    img.paste(_fade(p, 14130, k=0.1, dust=0.12), (x0, y0))
    _chips(img, (x0, y0, x1, y1), 14131, n=6)


def eyeboard_px(x, z):
    """World (x, z) on the eye's board -> pixel in its cell."""
    bx0, bx1, bz0, bz1, _ = EYEBOARD
    x0, y0, x1, y1 = SCELLS['eyeboard']
    s = (x1 - x0) / (bx1 - bx0)
    return (x - bx0) * s, (bz1 - z) * s


def make_eyeboard(img):
    """The eye's board (1 px ~ 2.75 mm): LIGHT METER, the eye's painted lashes, the three amber lamps' labels, DARK
    (REST HOUR) by the big green lamp, and the plate's sentence."""
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = SCELLS['eyeboard']
    w, h = x1 - x0, y1 - y0
    cream, green, ink, gold = (222, 212, 184), (34, 62, 50), (26, 26, 24), (186, 150, 70)
    p = Image.new('RGB', (w, h), green)
    d = ImageDraw.Draw(p)
    d.rounded_rectangle((4, 4, w - 5, h - 5), radius=20, outline=gold, width=6)
    _text(d, (w // 2, 30), 'LIGHT METER', 26, cream)
    ex, ez = eyeboard_px(EYE[0], EYE[1])
    for k in range(9):                                                     # painted lashes over the eye
        a = math.radians(200 + k * 17.5)
        d.line((ex + 92 * math.cos(a), ez + 56 * math.sin(a), ex + 118 * math.cos(a), ez + 80 * math.sin(a)), fill=cream, width=5)
    for name, label in (('Att14aEyeSun', ('NIGHT-', 'LIGHT')), ('Att14aEyeW1', ('WELL', 'WINDOW')),
                        ('Att14aEyeW2', ('CORRIDOR', 'WINDOW'))):
        lx, lz, r = EYE_LAMPS[name]
        px, pz = eyeboard_px(lx, lz)
        d.ellipse((px - 22, pz - 22, px + 22, pz + 22), fill=(20, 22, 20))
        for k, s in enumerate(label):
            _text(d, (px, pz + 36 + k * 19), s, 18, cream, max_w=100)
    gx, gz = eyeboard_px(EYE_LAMPS['Att14aEyeDark'][0], EYE_LAMPS['Att14aEyeDark'][1])
    d.ellipse((gx - 36, gz - 36, gx + 36, gz + 36), fill=(20, 22, 20))
    _moon(d, gx - 92, gz, 22, (226, 200, 120), green)
    _text(d, (gx + 98, gz - 12), 'DARK', 34, cream)
    _text(d, (gx + 98, gz + 16), '(REST HOUR)', 17, cream, max_w=110)
    d.rounded_rectangle((14, h - 92, w - 15, h - 14), radius=10, fill=cream)
    _text(d, (w // 2, h - 68), 'REST HOUR BEGINS WHEN', 27, ink, max_w=w - 50)
    _text(d, (w // 2, h - 38), 'THE ROOM IS DARK', 27, ink, max_w=w - 50)
    for sx, sy in ((20, 20), (w - 21, 20), (20, h - 108), (w - 21, h - 108)):
        d.ellipse((sx - 6, sy - 6, sx + 6, sy + 6), fill=(150, 146, 136), outline=(70, 66, 60), width=2)
    img.paste(_fade(p, 14140, k=0.12, dust=0.14), (x0, y0))
    _chips(img, (x0, y0, x1, y1), 14141, n=8, col=(170, 166, 150, 200))


def make_dial(img):
    """The night-light dial's face: its bands round the circle, clockwise from the top (BRIGHT warm yellow, DIMMING a
    gradient, DARK black with a small painted moon, BRIGHTENING a gradient), a tick at the top, numerals 0..9."""
    import numpy as np
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = SCELLS['dial']
    n = x1 - x0
    c = n / 2
    yy, xx = np.mgrid[0:n, 0:n].astype(float)
    dx, dy = xx + 0.5 - c, yy + 0.5 - c
    r = np.hypot(dx, dy) / c
    t = (np.degrees(np.arctan2(dx, -dy)) % 360) / 360 * CYCLE         # clockwise from the top, in seconds
    yel, blk = np.array((232, 190, 74), float), np.array((14, 14, 18), float)
    f = np.zeros_like(t)                                              # 1 = bright, 0 = dark
    f[t < 3.0] = 1.0
    m = (t >= 3.0) & (t < 4.5)
    f[m] = 1 - (t[m] - 3.0) / 1.5
    m = (t >= 8.0)
    f[m] = (t[m] - 8.0) / 2.0
    a = blk[None, None] * (1 - f[..., None]) + yel[None, None] * f[..., None]
    a[r > 0.985] = (40, 34, 26)
    a[(r > 0.9) & (r <= 0.985)] = (222, 212, 184)                     # the cream ring with the numerals
    a[r < 0.13] = (40, 34, 26)
    face = Image.fromarray(np.clip(a, 0, 255).astype('uint8'))
    d = ImageDraw.Draw(face)
    ink = (26, 26, 24)
    for k in range(10):                                               # seconds round the rim
        ang = math.radians(k / CYCLE * 360)
        d.line((c + 0.9 * c * math.sin(ang), c - 0.9 * c * math.cos(ang), c + 0.82 * c * math.sin(ang), c - 0.82 * c * math.cos(ang)),
               fill=(222, 212, 184) if 4.5 <= k < 8 else ink, width=3)
    for b, bt0, bt1 in BANDS:                                         # the band boundaries on the cream ring
        ang = math.radians(bt0 / CYCLE * 360)
        d.line((c + 0.9 * c * math.sin(ang), c - 0.9 * c * math.cos(ang), c + 0.985 * c * math.sin(ang), c - 0.985 * c * math.cos(ang)),
               fill=ink, width=3)
    sa = math.radians(1.5 / CYCLE * 360)                              # a painted sun in BRIGHT
    sx, sy = c + 0.55 * c * math.sin(sa), c - 0.55 * c * math.cos(sa)
    for k in range(8):
        aa = 2 * math.pi * k / 8
        d.line((sx + 15 * math.cos(aa), sy + 15 * math.sin(aa), sx + 23 * math.cos(aa), sy + 23 * math.sin(aa)), fill=(196, 110, 30), width=3)
    d.ellipse((sx - 11, sy - 11, sx + 11, sy + 11), fill=(240, 214, 120), outline=(196, 110, 30), width=2)
    ma = math.radians(6.25 / CYCLE * 360)                             # the small painted moon in DARK
    mx, my = c + 0.55 * c * math.sin(ma), c - 0.55 * c * math.cos(ma)
    _moon(d, mx, my, 15, (226, 214, 160), (14, 14, 18))
    for k, (sx_, sy_) in enumerate(((mx - 30, my - 22), (mx + 26, my + 18), (mx + 8, my - 34))):
        d.ellipse((sx_ - 2, sy_ - 2, sx_ + 2, sy_ + 2), fill=(214, 204, 160))
    d.polygon([(c - 9, 3), (c + 9, 3), (c, 20)], fill=(150, 30, 26))   # the painted top mark under the brass one
    img.paste(face, (x0, y0))


def make_small(img):
    """Name cards, LIGHTS OUT, the brake's plate, NIGHT-LIGHT, LINEN, W1 / W2, WARD 2, Mara's tree."""
    from PIL import Image, ImageDraw
    cream, green, ink, gold, red = (222, 212, 184), (34, 62, 50), (26, 26, 24), (176, 136, 66), (132, 34, 28)
    for k, name in enumerate(NAMES + ('',)):
        key = 'card%d' % k if k < 3 else 'cardx'
        x0, y0, x1, y1 = SCELLS[key]
        cd = Image.new('RGB', (x1 - x0, y1 - y0), (214, 204, 176))
        dc = ImageDraw.Draw(cd)
        dc.rectangle((2, 2, x1 - x0 - 3, y1 - y0 - 3), outline=(150, 140, 110), width=2)
        if name:
            _text(dc, ((x1 - x0) // 2, (y1 - y0) // 2 + 2), name, 34, (30, 32, 52), kind='serif', max_w=x1 - x0 - 22)
        img.paste(_fade(cd, 14150 + k, k=0.12, dust=0.15), (x0, y0))

    def plate(key, text, size, bg, fg, kind='carlito', radius=10, screws=True):
        x0, y0, x1, y1 = SCELLS[key]
        w, h = x1 - x0, y1 - y0
        p = Image.new('RGB', (w, h), bg)
        dp = ImageDraw.Draw(p)
        dp.rounded_rectangle((3, 3, w - 4, h - 4), radius=radius, outline=fg, width=4)
        _text(dp, (w // 2, h // 2 + 1), text, size, fg, kind=kind, max_w=w - (60 if screws else 20))
        if screws:
            for xx in (14, w - 14):
                dp.ellipse((xx - 4, h // 2 - 4, xx + 4, h // 2 + 4), fill=(110, 106, 96))
        img.paste(_fade(p, sum(map(ord, key)), k=0.12, dust=0.15), (x0, y0))
        _chips(img, (x0, y0, x1, y1), sum(map(ord, key)) + 1, n=3)
    plate('lightsout', 'LIGHTS OUT', 64, green, cream, radius=14)
    plate('nightlight', 'NIGHT-LIGHT', 32, gold, (40, 30, 16), radius=6)
    plate('linen', 'LINEN', 36, green, cream)
    plate('ward', 'WARD 2', 38, green, cream)
    x0, y0, x1, y1 = SCELLS['brake']                                   # the brake's plate: BRAKE, and which way is on
    w, h = x1 - x0, y1 - y0
    p = Image.new('RGB', (w, h), red)
    dp = ImageDraw.Draw(p)
    dp.rounded_rectangle((3, 3, w - 4, h - 4), radius=8, outline=cream, width=4)
    _text(dp, (92, 28), 'REST HOUR', 20, cream)
    _text(dp, (92, 56), 'BRAKE', 36, cream)
    _text(dp, (214, 22), 'OFF ↑', 20, cream)
    _text(dp, (214, 56), 'ON ↙', 20, cream, kind='sans-bold')
    img.paste(_fade(p, 14160, k=0.12, dust=0.15), (x0, y0))
    for key, t in (('w1', 'W1'), ('w2', 'W2')):
        x0, y0, x1, y1 = SCELLS[key]
        r = Image.new('RGB', (64, 64), green)
        dr = ImageDraw.Draw(r)
        dr.ellipse((1, 1, 62, 62), fill=cream, outline=green, width=5)
        _text(dr, (32, 34), t, 28, green)
        img.paste(r, (x0, y0))
    # Mara's crooked tree, in pencil on the plaster at the head of her bunk, gone over and over; M.D. under it.
    import build_dl05 as dl05
    x0, y0, x1, y1 = SCELLS['tree']
    w, h = x1 - x0, y1 - y0
    import numpy as np
    a = np.ones((h, w, 3)) * np.array((150, 140, 112), float) * (0.9 + 0.16 * _noise(w, h, 4, 14170))[..., None]
    pl = Image.fromarray(np.clip(a, 0, 255).astype('uint8')).convert('RGBA')
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dl = ImageDraw.Draw(lay)
    rnd = random.Random(14171)

    def stroke(pts, weight):
        for _ in range(3):
            q = [(x + rnd.uniform(-1.2, 1.2), y + rnd.uniform(-1.2, 1.2)) for x, y in pts]
            dl.line(q, fill=(40, 40, 50, int(200 * rnd.uniform(0.8, 1.0))), width=max(2, int(4 * (0.6 + weight * 0.6))), joint='curve')
    dl05._crooked_tree(stroke, w * 0.48, h * 0.82, h * 0.7, sx=h * 0.56)
    _text(dl, (w * 0.5, h * 0.92), 'M.D.', 20, (44, 44, 56, 210), kind='hand')
    pl.alpha_composite(lay)
    img.paste(pl.convert('RGB'), (x0, y0))


def make_signs(path):
    from PIL import Image, ImageFilter
    img = Image.new('RGB', (SIGNS, SIGNS), (60, 58, 54))
    make_rules(img)
    make_drive(img)
    make_eyeboard(img)
    make_dial(img)
    make_small(img)
    img.filter(ImageFilter.GaussianBlur(0.35)).save(path, optimize=True)


def make_textures():
    os.makedirs(TEX, exist_ok=True)
    make_atlas(ATLAS_PATH)
    make_signs(SIGNS_PATH)


# =====================================================================================================================
# Mesh building (as dl14's MB: faces tagged by material name; decals keep their winding)
# =====================================================================================================================
class MB:
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
        """The verts so far (a set: primitives may remove verts, so indices are not a safe mark)."""
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

    def decal(self, mt, x0, x1, z0, z1, y, cell):
        """A picture on a wall, facing the camera (-y)."""
        u0, v0, u1, v1 = cell_uv(cell)
        return self.face(mt, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    def decal_back(self, mt, x0, x1, z0, z1, y, cell):
        """The same picture facing +y (read from behind, so mirrored in x to read right)."""
        u0, v0, u1, v1 = cell_uv(cell)
        return self.face(mt, [(x1, y, z0), (x0, y, z0), (x0, y, z1), (x1, y, z1)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    def disc(self, mt, c, r, cell, seg=32, y=None):
        """A round picture facing -y, mapped onto the inscribed circle of its cell."""
        u0, v0, u1, v1 = cell_uv(cell)
        ring = [2 * math.pi * k / seg for k in range(seg)]
        cx, cy, cz = c
        return self.face(mt, [(cx + r * math.cos(a), cy, cz + r * math.sin(a)) for a in ring],
                         [((u0 + u1) / 2 + (u1 - u0) / 2 * math.cos(a), (v0 + v1) / 2 + (v1 - v0) / 2 * math.sin(a)) for a in ring])

    def tbox(self, mt, x0, x1, y0, y1, z0, z1, cells):
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

    def prism_xz(self, mt, pts, y0, y1, cell=None):
        """A polygon in (x, z), extruded from y0 to y1 (closed; normals recalculated)."""
        bm = self.bm
        f = [bm.verts.new((x, y0, z)) for x, z in pts]
        b = [bm.verts.new((x, y1, z)) for x, z in pts]
        fs = [bm.faces.new(f), bm.faces.new(list(reversed(b)))]
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            fs.append(bm.faces.new((f[j], f[i], b[i], b[j])))
        for fc in fs:
            fc.material_index = self.m(mt)
        if cell:
            self.paint(f + b, cell)
        return f + b

    def merge(self, src, mt, uv=None, M=None):
        """Append a temporary bmesh's geometry (closed, any material) as material mt; uv(co) -> (u, v) per loop."""
        idx = self.m(mt)
        if isinstance(uv, str):
            c = cell_mid(uv)
            uv = (lambda co, c=c: c)
        vmap = {}
        for v in src.verts:
            vmap[v] = self.bm.verts.new(M @ v.co if M is not None else v.co.copy())
        for f in src.faces:
            try:
                nf = self.bm.faces.new([vmap[v] for v in f.verts])
            except ValueError:
                continue
            nf.material_index = idx
            if uv:
                for lp in nf.loops:
                    lp[self.uv].uv = uv(lp.vert.co)
        src.free()

    def mesh(self, name, origin=(0.0, 0.0, 0.0), sharp=35):
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
        return me

    def obj(self, name, coll, origin=(0.0, 0.0, 0.0), sharp=35):
        me = self.mesh(name, origin, sharp)
        ob = bpy.data.objects.new(name, me)
        ob.location = Vector(origin)
        coll.objects.link(ob)
        return ob


def proj_xz(cell, c, sx, sz):
    """UVs projected from the front: (x, z) round c over a sx by sz window onto the cell."""
    u0, v0, u1, v1 = cell_uv(cell)

    def f(co):
        s = min(max(0.5 + (co.x - c[0]) / sx, 0.0), 1.0)
        t = min(max(0.5 + (co.z - c[2]) / sz, 0.0), 1.0)
        return (u0 + (u1 - u0) * s, v0 + (v1 - v0) * t)
    return f


def proj_xy(cell, c, sx, sy):
    """UVs projected from above."""
    u0, v0, u1, v1 = cell_uv(cell)

    def f(co):
        s = min(max(0.5 + (co.x - c[0]) / sx, 0.0), 1.0)
        t = min(max(0.5 + (co.y - c[1]) / sy, 0.0), 1.0)
        return (u0 + (u1 - u0) * s, v0 + (v1 - v0) * t)
    return f


def sweep_bm(pts, r, seg=6):
    """A tube along pts (dl12's sweep, into a temporary bmesh)."""
    import dl12
    tmp = bmesh.new()
    dl12.sweep(tmp, [Vector(p) for p in pts], r, 0, seg=seg)
    return tmp


def pillow(B, c, size, cell='pillow'):
    tmp = d17.rounded_box(size, (0, 0, 0), p=2.6, cuts=4, mat=0)
    for v in tmp.verts:                                     # dented where a head was
        r2 = (v.co.x / (size[0] / 2)) ** 2 + (v.co.y / (size[1] / 2)) ** 2
        if v.co.z > 0:
            v.co.z -= 0.12 * size[2] * max(0.0, 1 - r2)
    B.merge(tmp, ATLAS_MAT, proj_xy(cell, c, size[0], size[1]), M=Matrix.Translation(c))


# =====================================================================================================================
# The room's shell
# =====================================================================================================================
def holed_wall(B, x0, x1, y0, y1, z0, z1, holes, split=DADO, lower='WinDado', upper='WinPlaster'):
    """A wall slab with rectangular holes (hx0, hx1, hz0, hz1), as boxes over the grid the holes make; the cells below
    `split` take the dado's paint."""
    xs = sorted({x0, x1} | {h[0] for h in holes if x0 < h[0] < x1} | {h[1] for h in holes if x0 < h[1] < x1})
    zs = sorted({z0, z1, split} | {h[2] for h in holes if z0 < h[2] < z1} | {h[3] for h in holes if z0 < h[3] < z1})
    zs = [z for z in zs if z0 <= z <= z1]
    for za, zb in zip(zs, zs[1:]):
        run = None
        for xa, xb in zip(xs, xs[1:]):
            cx, cz = (xa + xb) / 2, (za + zb) / 2
            solid = not any(h[0] < cx < h[1] and h[2] < cz < h[3] for h in holes)
            if solid:
                run = (run[0], xb) if run else (xa, xb)
            if (not solid or xb == xs[-1]) and run:
                B.box(lower if cz < split else upper, run[0], run[1], y0, y1, za, zb)
                run = None


def wall_runs(holes, z0, z1, xa, xb):
    """The x runs along the wall not crossed by any hole between heights z0 and z1."""
    cuts = sorted((h[0], h[1]) for h in holes if h[2] < z1 and h[3] > z0)
    runs, x = [], xa
    for a, b in cuts:
        if a > x:
            runs.append((x, min(a, xb)))
        x = max(x, b)
    if x < xb:
        runs.append((x, xb))
    return [(a, b) for a, b in runs if b - a > 0.02]


def arch_geom(a0, a1):
    r = (a1 - a0) / 2
    return (a0 + a1) / 2, ARCH_CROWN - r, r


def back_holes():
    return [(CUPBOARD[0], CUPBOARD[1], 0.0, CUPBOARD[2])] + [(a0, a1, 0.0, ARCH_CROWN) for a0, a1 in ARCHES] + \
           [(W1[0], W1[1], W1[2], W1[3]), (W2[0], W2[1], W2[2], W2[3])]


def build_shell(B):
    holes = back_holes()
    holed_wall(B, LWALL[1], RWALL[0], BACK_Y, BACK_Y2, 0.0, CEIL, holes)
    # The arches' heads: the spandrels over each round head, a plaster archivolt round it, a keystone; pilaster strips.
    for a0, a1 in ARCHES:
        xc, zs, r = arch_geom(a0, a1)
        n = 10
        left = [(a0, ARCH_CROWN), (a0, zs)] + [(xc + r * math.cos(math.radians(180 - 90 * k / n)), zs + r * math.sin(math.radians(180 - 90 * k / n)))
                                                for k in range(1, n + 1)]
        right = [(a1, ARCH_CROWN), (xc, ARCH_CROWN)] + [(xc + r * math.cos(math.radians(90 - 90 * k / n)), zs + r * math.sin(math.radians(90 - 90 * k / n)))
                                                         for k in range(1, n + 1)]
        B.prism_xz('WinPlaster', left, BACK_Y, BACK_Y2)
        B.prism_xz('WinPlaster', right, BACK_Y, BACK_Y2)
        m = 2 * n
        band = [(xc + (r + 0.075) * math.cos(math.pi * k / m), zs + (r + 0.075) * math.sin(math.pi * k / m)) for k in range(m + 1)] + \
               [(xc + r * math.cos(math.pi * k / m), zs + r * math.sin(math.pi * k / m)) for k in range(m, -1, -1)]
        B.prism_xz('WinPlaster', band, BACK_Y - 0.018, BACK_Y)
        B.box('WinPlaster', xc - 0.06, xc + 0.06, BACK_Y - 0.03, BACK_Y, ARCH_CROWN - 0.02, ARCH_CROWN + 0.1)
        for x0_, x1_ in ((a0 - 0.075, a0), (a1, a1 + 0.075)):
            B.box('WinPlaster', x0_, x1_, BACK_Y - 0.018, BACK_Y, DADO + 0.03, zs)
            B.box('WinDado', x0_, x1_, BACK_Y - 0.022, BACK_Y, 0.0, DADO + 0.03)
            B.box('WinPlaster', x0_ - 0.01, x1_ + 0.01, BACK_Y - 0.03, BACK_Y, zs - 0.06, zs)          # the impost
        # the floor runs on through the arch
        B.box('WinLino', a0, a1, BACK_Y, BACK_Y2, -0.2, 0.0)
    # The WARD 2 plate over the right arch.
    xc, zs, r = arch_geom(*ARCHES[2])
    B.decal(SIGNS_MAT, xc - 0.2, xc + 0.2, ARCH_CROWN + 0.13, ARCH_CROWN + 0.21, BACK_Y - 0.032, 'ward')
    # Left wall; end wall with the doorway and the rail's low hatch beside it; floor; ceiling and cornice.
    for (za, zb, mt) in ((0.0, DADO, 'WinDado'), (DADO, CEIL, 'WinPlaster')):
        B.box(mt, LWALL[0], LWALL[1], FRONT_Y, BACK_Y2, za, zb)
    dy0, dy1, dh = DOOR
    hy0, hy1, hh = RAIL_HATCH
    for ya, yb, za, zb in ((FRONT_Y, dy0, 0.0, CEIL), (dy0, dy1, dh, CEIL), (hy0, hy1, hh, CEIL), (hy1, BACK_Y2, 0.0, CEIL)):
        if za < DADO < zb:
            B.box('WinDado', RWALL[0], RWALL[1], ya, yb, za, DADO)
            B.box('WinPlaster', RWALL[0], RWALL[1], ya, yb, DADO, zb)
        else:
            B.box('WinDado' if zb <= DADO else 'WinPlaster', RWALL[0], RWALL[1], ya, yb, za, zb)
    B.box('WinLino', X0, X1, FLOOR_Y0, BACK_Y, -0.2, 0.0)
    B.box('WinLino', X0, X1, BACK_Y, BACK_Y2, -0.2, -0.001)
    B.box('WinPlaster', X0, X1, FRONT_Y - 0.4, BACK_Y2, CEIL, CEIL + 0.15)
    B.box('WinPlaster', LWALL[1], RWALL[0], BACK_Y - 0.08, BACK_Y, CEIL - 0.1, CEIL)
    B.box('WinPlaster', LWALL[1], RWALL[0], BACK_Y - 0.03, BACK_Y, CEIL - 0.16, CEIL - 0.1)
    # Skirting and dado rail along the back wall between openings; the same on the end wall's room face.
    xa, xb = LWALL[1], RWALL[0]
    for a, b in wall_runs(holes, 0.0, 0.12, xa, xb):
        B.box('PigeonWood', a, b, BACK_Y - 0.02, BACK_Y, 0.0, 0.12)
    for a, b in wall_runs(holes, DADO - 0.02, DADO + 0.03, xa, xb):
        B.box('PigeonWood', a, b, BACK_Y - 0.03, BACK_Y, DADO - 0.02, DADO + 0.03)
    B.box('PigeonWood', RWALL[0] - 0.02, RWALL[0], hy1, BACK_Y, 0.0, 0.12)
    B.box('PigeonWood', RWALL[0] - 0.02, RWALL[0], FRONT_Y, dy0, 0.0, 0.12)
    B.box('PigeonWood', LWALL[1], LWALL[1] + 0.02, FRONT_Y, BACK_Y, 0.0, 0.12)
    B.box('PigeonWood', LWALL[1], LWALL[1] + 0.03, FRONT_Y, BACK_Y, DADO - 0.02, DADO + 0.03)
    # A picture rail high on the back wall.
    for a, b in wall_runs(holes, 3.0, 3.03, xa, xb):
        B.box('PigeonWood', a, b, BACK_Y - 0.02, BACK_Y, 3.0, 3.03)
    return holes


def build_door_frame(B):
    """The doorway's architrave on the room side, the hinge jamb over the rail's hatch, the hatch's iron frame, the
    LIGHTS OUT sign on its bracket over the doorway (a flag sign, read from the camera), the threshold."""
    dy0, dy1, dh = DOOR
    hy0, hy1, hh = RAIL_HATCH
    fx0, fx1 = RWALL[0] - 0.025, RWALL[0]
    B.box('PigeonWood', fx0, fx1, dy0 - 0.075, dy0, 0.0, dh + 0.075)
    B.box('PigeonWood', fx0, fx1, dy0 - 0.075, hy1 + 0.05, dh, dh + 0.075)
    B.box('PigeonWood', fx0, fx1, dy1, dy1 + 0.04, hh, dh)                       # the hinge jamb, over the hatch
    for a, b, c, d in ((hy0 - 0.005, hy0 + 0.02, 0.0, hh), (hy1 - 0.02, hy1 + 0.005, 0.0, hh), (hy0, hy1, hh - 0.02, hh)):
        B.box('WornIron', RWALL[0] - 0.012, RWALL[1], a, b, c, d)
    B.box('PigeonWood', RWALL[0], RWALL[1], dy0, dy1, 0.0, 0.012)                # the threshold
    B.box('WornIron', DOOR_HINGE[0] - 0.035, DOOR_HINGE[0] + 0.035, dy1 - 0.005, dy1 + 0.02, hh + 0.05, dh - 0.05)  # the hinge leaf
    # LIGHTS OUT: an enamel flag sign on an iron bracket from the end wall, over the doorway, both faces printed.
    sx0, sx1, sz0, sz1 = RWALL[0] - 0.47, RWALL[0] - 0.03, 1.86, 1.99
    B.box('WornIron', sx0 - 0.005, RWALL[0], -0.01, 0.01, sz1 + 0.02, sz1 + 0.035)
    for x in (sx0 + 0.04, sx1 - 0.04):
        B.cyl('WornIron', (x, 0.0, sz1 + 0.02), (x, 0.0, sz1), 0.004, seg=4)
    B.box('WornIron', RWALL[0] - 0.01, RWALL[0], -0.03, 0.03, sz1 - 0.02, sz1 + 0.06)
    B.box('CastIron', sx0 - 0.006, sx1 + 0.006, -0.004, 0.004, sz0 - 0.006, sz1 + 0.006)
    B.decal(SIGNS_MAT, sx0, sx1, sz0, sz1, -0.0045, 'lightsout')
    B.decal_back(SIGNS_MAT, sx0, sx1, sz0, sz1, 0.0045, 'lightsout')


def build_rail(B):
    """The figures' rail as a short stub by the door (DL-15's): a timber channel and two low iron rails at y 0.47 / 0.63,
    rail top 0.03, a buffer stop at its left end; it runs on under the end wall's hatch toward DL-14b."""
    x0, x1 = RAIL
    B.box('PigeonWood', x0, x1, CHAN[0], CHAN[1], -0.002, 0.003)
    for s in (-1, 1):
        y = RAIL_Y + s * RAIL_G
        B.box('WornIron', x0, x1, y - 0.012, y + 0.012, 0.0, 0.008)
        B.box('WornIron', x0, x1, y - 0.005, y + 0.005, 0.008, 0.024)
        B.box('WornIron', x0, x1, y - 0.009, y + 0.009, 0.024, RAIL_H)
    B.box('WornIron', x0, x0 + 0.08, RAIL_Y - 0.11, RAIL_Y + 0.11, 0.0, 0.12)
    B.box('CrateWood', x0 + 0.08, x0 + 0.1, RAIL_Y - 0.09, RAIL_Y + 0.09, 0.03, 0.1)
    for y in (RAIL_Y - 0.06, RAIL_Y + 0.06):
        B.cyl('WornIron', (x0 + 0.1, y, 0.065), (x0 + 0.14, y, 0.065), 0.018, seg=10)


# =====================================================================================================================
# The linen cupboard and the duct's vent; the bunks; the lockers
# =====================================================================================================================
def build_cupboard(B):
    """The built-in linen cupboard, its face at y 1.4 (the wall's face): panelled doors, the vent (the duct's mouth,
    open) at sill 1.15 over bunk 1's deck, the dark duct behind it rising to the left, a cornice, LINEN."""
    x0, x1, top = CUPBOARD
    vx0, vx1, vz0, vz1 = VENT
    fy0, fy1 = BACK_Y - 0.02, BACK_Y + 0.02
    # The face, round the vent: below it, either side, above it.
    for a, b, c, d in ((x0, x1, 0.0, vz0 - 0.04), (x0, vx0 - 0.04, vz0 - 0.04, vz1 + 0.06), (vx1 + 0.04, x1, vz0 - 0.04, vz1 + 0.06),
                       (x0, x1, vz1 + 0.06, top)):
        B.box('PigeonWood', a, b, fy0 + 0.01, fy1, c, d)
    for a, b, c, d in ((x0 + 0.06, (x0 + x1) / 2 - 0.02, 0.14, vz0 - 0.12), ((x0 + x1) / 2 + 0.02, x1 - 0.06, 0.14, vz0 - 0.12),
                       (x0 + 0.06, (x0 + x1) / 2 - 0.02, vz1 + 0.16, top - 0.12), ((x0 + x1) / 2 + 0.02, x1 - 0.06, vz1 + 0.16, top - 0.12)):
        B.box('CrateWood', a, b, fy0 - 0.005, fy0 + 0.01, c, d)                    # the doors' panels
    for x in ((x0 + x1) / 2 - 0.07, (x0 + x1) / 2 + 0.07):
        for z in ((0.14 + vz0 - 0.12) / 2, (vz1 + 0.16 + top - 0.12) / 2):
            B.sphere(ATLAS_MAT, (x, fy0 - 0.02, z), 0.018, seg=8, cell='sw_brass')
    B.box('PigeonWood', x0 - 0.02, x1 + 0.02, BACK_Y - 0.07, BACK_Y, top, top + 0.08)                       # cornice
    B.decal(SIGNS_MAT, (x0 + x1) / 2 - 0.15, (x0 + x1) / 2 + 0.15, top - 0.105, top - 0.035, fy0 - 0.007, 'linen')
    # The vent's frame (tin, rolled edge) and the duct behind: floor at the sill, cheeks, a roof rising to the left.
    for a, b, c, d in ((vx0 - 0.04, vx0, vz0, vz1), (vx1, vx1 + 0.04, vz0, vz1), (vx0 - 0.04, vx1 + 0.04, vz1, vz1 + 0.04),
                       (vx0 - 0.04, vx1 + 0.04, vz0 - 0.04, vz0)):
        B.box('WornIron', a, b, fy0 - 0.012, fy1, c, d)
    dy1 = 2.05
    B.box(ATLAS_MAT, vx0 - 0.02, vx1 + 0.02, fy1, dy1, vz0 - 0.02, vz0, cell='sw_iron')
    B.box(ATLAS_MAT, vx0 - 0.04, vx0, fy1, dy1, vz0, vz1 + 0.6, cell='sw_dark')
    B.box(ATLAS_MAT, vx1, vx1 + 0.04, fy1, dy1, vz0, vz1, cell='sw_dark')
    B.box(ATLAS_MAT, vx0 - 0.04, vx1 + 0.04, dy1, dy1 + 0.04, vz0, vz1 + 0.6, cell='sw_dark')
    B.prism_xz(ATLAS_MAT, [(vx0, vz1 + 0.6), (vx1 + 0.04, vz1), (vx1 + 0.04, vz1 + 0.04), (vx0, vz1 + 0.64)], fy1, dy1, cell='sw_dark')
    B.box(ATLAS_MAT, vx0 - 0.3, vx0 - 0.04, fy1, dy1, vz1 + 0.6, vz1 + 0.64, cell='sw_dark')
    for k in range(1, 4):                                                        # the duct's seams catch a little light
        y = fy1 + (dy1 - fy1) * k / 4
        B.box('WornIron', vx0, vx1, y - 0.004, y + 0.004, vz0, vz0 + 0.004)
    # The grille he pushed out: lying askew on the deck by the vent, louvres up.
    n0 = B.mark()
    B.tbox(ATLAS_MAT, -0.38, 0.38, -0.3, 0.3, 0.0, 0.012, {'+z': 'grille', 'all': 'sw_iron'})
    B.xform(n0, Matrix.Translation((248.98, 0.95, DECK + 0.002)) @ Matrix.Rotation(math.radians(-14), 4, 'Z') @ Matrix.Rotation(math.radians(4), 4, 'Y'))


def bunk(B, x0, x1, y0, y1, blanket='blanket', card=None, head_high=True, top_pillow=True, low_pillow=True, ladder=False,
         low_turned=False):
    """One iron bunk, end-on to the camera (its foot at y0): square-tube posts, angle-iron spring frames, a barred foot
    and head, the lower bed (mattress, blanket, sheet turned down, pillow) with its top at LOWER, the top deck's
    blanket at DECK. card: a name card in a brass holder on the foot's middle rail. head_high=False: the head stops at
    the deck (bunk 1's left bed, in front of the vent)."""
    pr = 0.0175
    foot_top, head_top = 1.31, (1.43 if head_high else DECK - 0.01)
    posts = ((x0 + pr, y0 + pr, foot_top), (x1 - pr, y0 + pr, foot_top), (x0 + pr, y1 - pr, head_top), (x1 - pr, y1 - pr, head_top))
    for px, py, top in posts:
        B.box('WornIron', px - pr, px + pr, py - pr, py + pr, 0.0, top)
        B.cyl('WornIron', (px, py, top), (px, py, top + 0.014), 0.021, seg=8)
        B.cyl('WornIron', (px, py, 0.0), (px, py, 0.012), 0.024, seg=8)
    for za, zb in ((0.31, 0.35), (0.96, 1.0)):
        for xa, xb in ((x0, x0 + 0.035), (x1 - 0.035, x1)):
            B.box('WornIron', xa, xb, y0 + 0.035, y1 - 0.035, za, zb)
        for ya, yb in ((y0, y0 + 0.035), (y1 - 0.035, y1)):
            B.box('WornIron', x0 + 0.035, x1 - 0.035, ya, yb, za, zb)
        B.box(ATLAS_MAT, x0 + 0.035, x1 - 0.035, y0 + 0.035, y1 - 0.035, zb - 0.012, zb - 0.006, cell='sw_spring')
    # Foot: top rail, three bars over the deck, a middle rail (the card's) and two bars under it.
    xc = (x0 + x1) / 2
    B.box('WornIron', x0 + 0.035, x1 - 0.035, y0 + 0.005, y0 + 0.03, foot_top - 0.03, foot_top)
    for x in (xc - 0.22, xc, xc + 0.22):
        B.cyl('WornIron', (x, y0 + 0.0175, 1.0), (x, y0 + 0.0175, foot_top - 0.03), 0.007, seg=6)
    B.box('WornIron', x0 + 0.035, x1 - 0.035, y0 + 0.005, y0 + 0.03, 0.70, 0.725)
    for x in (xc - 0.3, xc + 0.3):
        B.cyl('WornIron', (x, y0 + 0.0175, 0.35), (x, y0 + 0.0175, 0.70), 0.007, seg=6)
    # Head: a rail at 0.8 with bars, and (head_high) the top bed's rail at 1.4 with bars.
    B.box('WornIron', x0 + 0.035, x1 - 0.035, y1 - 0.03, y1 - 0.005, 0.78, 0.805)
    for x in (xc - 0.3, xc - 0.1, xc + 0.1, xc + 0.3):
        B.cyl('WornIron', (x, y1 - 0.0175, 0.35), (x, y1 - 0.0175, 0.78), 0.007, seg=6)
    if head_high:
        B.box('WornIron', x0 + 0.035, x1 - 0.035, y1 - 0.03, y1 - 0.005, head_top - 0.03, head_top)
        for x in (xc - 0.3, xc - 0.1, xc + 0.1, xc + 0.3):
            B.cyl('WornIron', (x, y1 - 0.0175, 1.0), (x, y1 - 0.0175, head_top - 0.03), 0.007, seg=6)
    # The beds: mattress (ticking), the blanket over it tucked down the sides, the sheet turned down, the pillow.
    for zb, top, pil in ((0.35, LOWER, low_pillow), (1.0, DECK, top_pillow)):
        B.tbox(ATLAS_MAT, x0 + 0.04, x1 - 0.04, y0 + 0.045, y1 - 0.045, zb - 0.006, top - 0.035, {'all': 'ticking'})
        by1 = y1 - 0.33
        if low_turned and zb < 0.5:                                              # her blanket turned back, the sheet
            B.tbox(ATLAS_MAT, x0 + 0.04, x1 - 0.04, y0 + 0.05, y1 - 0.05, top - 0.035, top - 0.03, {'all': 'sheet'})
            B.tbox(ATLAS_MAT, x0 + 0.03, x1 - 0.03, y0 + 0.035, y0 + 0.7, top - 0.07, top, {'+z': blanket, '-y': blanket, 'all': 'sw_blanket'})
            B.tbox(ATLAS_MAT, x0 + 0.035, x1 - 0.035, y0 + 0.7, y0 + 0.78, top - 0.03, top + 0.03, {'all': blanket})
        else:
            B.tbox(ATLAS_MAT, x0 + 0.03, x1 - 0.03, y0 + 0.035, by1, top - 0.07, top, {'+z': blanket, '-y': blanket, 'all': 'sw_blanket'})
            B.tbox(ATLAS_MAT, x0 + 0.04, x1 - 0.04, by1, by1 + 0.07, top - 0.03, top + 0.008, {'all': 'sheet'})
        for xa, xb in ((x0 + 0.026, x0 + 0.04), (x1 - 0.04, x1 - 0.026)):
            B.box(ATLAS_MAT, xa, xb, y0 + 0.035, by1 + 0.07, top - 0.13, top - 0.01, cell='sw_blanket')
        if pil:
            pillow(B, (xc, y1 - 0.19, top + 0.04), (x1 - x0 - 0.2, 0.26, 0.1))
    if card:
        B.box(ATLAS_MAT, xc - 0.09, xc + 0.09, y0 - 0.008, y0 + 0.005, 0.66, 0.74, cell='sw_brass')
        B.decal(SIGNS_MAT, xc - 0.08, xc + 0.08, 0.675, 0.725, y0 - 0.009, card)
    if ladder:                                                                   # hooked over the foot's top rail
        lx0, lx1, ly = x1 - 0.32, x1 - 0.06, y0 - 0.04
        for x in (lx0, lx1):
            B.box('WornIron', x - 0.012, x + 0.012, ly - 0.012, ly + 0.012, 0.0, foot_top + 0.02)
            B.box('WornIron', x - 0.012, x + 0.012, ly, y0 + 0.03, foot_top + 0.005, foot_top + 0.025)
        for k in range(1, 5):
            z = foot_top * k / 5
            B.cyl('WornIron', (lx0, ly, z), (lx1, ly, z), 0.009, seg=6)


def build_bunks(B):
    x0, x1, y0, y1 = BUNK1
    xm = (x0 + x1) / 2
    bunk(B, x0, xm, y0, y1, blanket='blanket2', card='cardx', head_high=False, top_pillow=False)
    bunk(B, xm, x1, y0, y1, blanket='blanket2', card='cardx')
    x0, x1, y0, y1 = BUNKS2
    w = (x1 - x0) / 3
    for k in range(3):
        bunk(B, x0 + k * w, x0 + (k + 1) * w, y0, y1, card='card%d' % k, ladder=(k == 2), low_turned=(k == 2))
    # Under the friends' bunks: a torch and three biscuits (they talked after lights out), crumbs.
    tx, ty = 256.02, 0.16
    B.cyl(ATLAS_MAT, (tx, ty, 0.022), (tx + 0.13, ty + 0.03, 0.022), 0.021, seg=10, cell='sw_torch')
    B.cyl(ATLAS_MAT, (tx + 0.13, ty + 0.03, 0.022), (tx + 0.17, ty + 0.04, 0.024), 0.024, 0.029, seg=10, cell='sw_iron')
    B.cyl(ATLAS_MAT, (tx + 0.17, ty + 0.04, 0.024), (tx + 0.173, ty + 0.04, 0.024), 0.026, seg=10, cell='sw_lens')
    B.box(ATLAS_MAT, tx + 0.05, tx + 0.07, ty + 0.002, ty + 0.025, 0.04, 0.047, cell='sw_brass')
    rnd = random.Random(14180)
    for (bx, by, r, bite) in ((255.86, -0.04, 0.032, False), (255.93, 0.27, 0.032, False), (256.32, 0.02, 0.03, True)):
        B.cyl(ATLAS_MAT, (bx, by, 0.0), (bx, by, 0.009), r, seg=14, cell='sw_biscuit')
        if bite:                                                                 # a bite out of the last one
            B.cyl(ATLAS_MAT, (bx + r * 0.8, by + r * 0.4, 0.0), (bx + r * 0.8, by + r * 0.4, 0.0095), 0.016, seg=8, cell='sw_wood')
    for _ in range(10):
        cx, cy = 256.0 + rnd.uniform(-0.22, 0.4), 0.1 + rnd.uniform(-0.22, 0.22)
        B.box(ATLAS_MAT, cx - 0.004, cx + 0.004, cy - 0.003, cy + 0.003, 0.0, 0.004, cell='sw_biscuit')
    # Mara's tree in pencil on the plaster at the head of her bunk, by W1's jamb.
    B.decal(SIGNS_MAT, 257.06, 257.3, 1.2, 1.48, BACK_Y - 0.0015, 'tree')


def build_lockers(B):
    y0, y1 = LOCKER_Y
    for k, (x0, x1) in enumerate(LOCKERS):
        B.tbox(ATLAS_MAT, x0 + 0.01, x1 - 0.01, y0 + 0.01, y1 - 0.02, 0.06, LOCKER_TOP - 0.025,
               {'-y': 'locker', 'all': 'sw_lockerpaint'})
        B.box('PigeonWood', x0 + 0.025, x1 - 0.025, y0 + 0.03, y1 - 0.04, 0.0, 0.06)
        B.box('CrateWood', x0, x1, y0, y1, LOCKER_TOP - 0.025, LOCKER_TOP)
        B.sphere(ATLAS_MAT, (x1 - 0.06, y0 + 0.002, 0.3), 0.014, seg=8, cell='sw_brass')
    # On locker 2, a tin cup; on locker 3, a folded towel. Low: he walks over them (they are decor).
    x = LOCKERS[1][0] + 0.12
    B.cyl(ATLAS_MAT, (x, 0.3, LOCKER_TOP), (x, 0.3, LOCKER_TOP + 0.07), 0.032, 0.036, seg=12, cell='sw_cup')
    B.torus(ATLAS_MAT, (x + 0.04, 0.3, LOCKER_TOP + 0.04), (0, 1, 0), 0.018, 0.004, seg=10, rseg=4, cell='sw_cup')
    x = LOCKERS[2][0] + 0.25
    B.box(ATLAS_MAT, x - 0.17, x + 0.17, 0.12, 0.42, LOCKER_TOP, LOCKER_TOP + 0.035, cell='sw_white')


# =====================================================================================================================
# The rest-hour wall: pegs, rules, brake, dial, sun; the windows and blinds; the crank; the eye; the chair
# =====================================================================================================================
def build_pegs(B):
    """The decoy pegs: a peg rail at child height with five turned pegs, small gowns hung by their loops on four; ONE
    free peg at 251.5. Each peg's hook point (where a loop or a hanger's hook sits) is at (x, 1.345, 0.80)."""
    x0, x1, z0, z1, fy = PEGBOARD
    B.box('PigeonWood', x0, x1, fy, BACK_Y, z0, z1)
    B.box('PigeonWood', x0, x1, fy - 0.012, fy, z1 - 0.02, z1)
    ry, rz = PEG_REST
    for k, x in enumerate(PEG_X):
        a = Vector((x, fy, rz - 0.019))
        b = Vector((x, 1.305, rz - 0.004))
        B.cyl('PigeonWood', a, b, 0.013, 0.011, seg=8)
        B.sphere('PigeonWood', (x, 1.3, rz - 0.002), 0.017, seg=8)
        B.box(ATLAS_MAT, x - 0.04, x + 0.04, fy - 0.003, fy, 0.835, 0.862, cell='sw_paper')     # a name tag over each
        if x != PEG_FREE:
            B.box(ATLAS_MAT, x - 0.028, x + 0.022, fy - 0.0035, fy - 0.003, 0.846, 0.85, cell='sw_ink')
    gowns = [g for g in zip(PEG_X, ('gown1', 'gown2', None, 'gown3', 'gown4')) if g[1]]
    import dl12
    for k, (x, cell) in enumerate(gowns):
        tmp = bmesh.new()
        dl12.coat_body(tmp, s=0.74, hanger=False, hood=False, wide=0.86, length=1.12 + 0.05 * (k % 2))
        c = (x, ry, rz - 0.24)
        B.merge(tmp, ATLAS_MAT, proj_xz(cell, c, 0.3, 0.5), M=Matrix.Translation((x, ry, rz)) @ Matrix.Rotation(math.radians((-3, 2, -1, 4)[k]), 4, 'Y'))


def build_rules(B):
    x0, x1, z0, z1 = RULES
    B.box('PigeonWood', x0 - 0.025, x1 + 0.025, BACK_Y - 0.02, BACK_Y, z0 - 0.025, z1 + 0.025)
    B.box('CastIron', x0 - 0.004, x1 + 0.004, BACK_Y - 0.026, BACK_Y - 0.02, z0 - 0.004, z1 + 0.004)
    B.decal(SIGNS_MAT, x0, x1, z0, z1, BACK_Y - 0.027, 'rules')


def build_brake_static(B):
    """The brake's fixed parts: a cast-iron wall plate, the pin's cheeks and a brass pin, a toothed quadrant over the
    lever's travel (toward the camera), the rod up to the shoe on the dial's rim, and its plate (REST HOUR BRAKE)."""
    px, py, pz = PAWL
    B.box('CastIron', px - 0.12, px + 0.12, BACK_Y - 0.015, BACK_Y, pz - 0.2, pz + 0.17)
    for s in (-1, 1):
        B.box('CastIron', px + s * 0.052 - 0.01, px + s * 0.052 + 0.01, py - 0.035, BACK_Y - 0.015, pz - 0.05, pz + 0.05)
    B.cyl('Brass', (px - 0.07, py, pz), (px + 0.07, py, pz), 0.012, seg=10)
    for k in range(10):                                                      # the quadrant's teeth: 0 .. 45 deg forward
        a = math.radians(-2 + k * 5.0)
        for r, size in ((0.22, (0.012, 0.03, 0.03)), (0.25, (0.012, 0.018, 0.022))):
            c = Vector((px + 0.072, py - r * math.sin(a), pz + r * math.cos(a)))
            add_box(B.bm, c, size, mat=B.m('Brass'), rot=Matrix.Rotation(-a, 4, 'X'))
    B.cyl('CastIron', (px + 0.072, py, pz), (px + 0.072, py - 0.2 * math.sin(math.radians(42)), pz + 0.2 * math.cos(math.radians(42))), 0.008, seg=6)
    B.cyl('CastIron', (px + 0.072, BACK_Y - 0.015, pz + 0.2), (px + 0.072, py, pz + 0.2), 0.008, seg=6)
    # The crank arm on the pin's right end and the rod to the brake shoe at the dial's rim (lower left).
    dx, dz = DIAL
    a = math.radians(225)
    shoe = Vector((dx + (DIAL_R + 0.045) * math.sin(a), BACK_Y - 0.035, dz + (DIAL_R + 0.045) * math.cos(a)))
    arm = Vector((px + 0.1, BACK_Y - 0.035, pz - 0.07))
    B.cyl('CastIron', (px + 0.07, py, pz), (arm.x, py, arm.z), 0.01, seg=6)
    B.cyl('CastIron', (arm.x, py, arm.z), arm, 0.008, seg=6)
    B.cyl('Brass', arm, shoe, 0.007, seg=6)
    for z in (0.95,):
        t = (z - arm.z) / (shoe.z - arm.z)
        p = arm + (shoe - arm) * t
        B.box('CastIron', p.x - 0.015, p.x + 0.015, p.y, BACK_Y, z - 0.012, z + 0.012)
    add_box(B.bm, shoe, (0.07, 0.04, 0.04), mat=B.m('CastIron'), rot=Matrix.Rotation(a, 4, 'Y'))
    # Its plate, over the lever.
    bx0, bx1, bz0, bz1 = px - 0.17, px + 0.17, 1.1, 1.2
    B.box('CastIron', bx0 - 0.006, bx1 + 0.006, BACK_Y - 0.008, BACK_Y, bz0 - 0.006, bz1 + 0.006)
    B.decal(SIGNS_MAT, bx0, bx1, bz0, bz1, BACK_Y - 0.009, 'brake')


def build_dial_static(B):
    """The night-light dial: a wooden backing, a brass bezel, the painted face (its bands), a brass alignment mark at
    the top, the spindle's boss; its plate (NIGHT-LIGHT) under it; the conduit up to the sun."""
    dx, dz = DIAL
    B.cyl('PigeonWood', (dx, BACK_Y, dz), (dx, BACK_Y - 0.025, dz), DIAL_R + 0.06, seg=40)
    B.torus('Brass', (dx, BACK_Y - 0.03, dz), (0, 1, 0), DIAL_R + 0.012, 0.014, seg=40, rseg=6)
    B.disc(SIGNS_MAT, (dx, DIAL_FACE_Y, dz), DIAL_R, 'dial', seg=40)
    B.prism_xz('Brass', [(dx - 0.035, dz + DIAL_R + 0.05), (dx + 0.035, dz + DIAL_R + 0.05), (dx, dz + DIAL_R - 0.02)],
               DIAL_FACE_Y - 0.012, DIAL_FACE_Y - 0.004)
    B.cyl('Brass', (dx, BACK_Y - 0.025, dz + DIAL_R + 0.05), (dx, DIAL_FACE_Y - 0.012, dz + DIAL_R + 0.05), 0.012, seg=8)
    B.cyl('CastIron', (dx, DIAL_FACE_Y, dz), (dx, HAND_Y + 0.004, dz), 0.012, seg=8)
    B.box('Brass', dx - 0.155, dx + 0.155, BACK_Y - 0.006, BACK_Y, 0.975, 1.045)
    B.decal(SIGNS_MAT, dx - 0.15, dx + 0.15, 0.98, 1.04, BACK_Y - 0.007, 'nightlight')
    # The conduit: from the dial's back up to the sun, saddled to the wall.
    sx, sz = SUN
    cx = dx + 0.24
    pts = [(cx, BACK_Y - 0.012, dz + 0.1), (cx, BACK_Y - 0.012, sz), (sx - 0.2, BACK_Y - 0.012, sz)]
    B.cyl('WornIron', pts[0], pts[1], 0.01, seg=6)
    B.cyl('WornIron', pts[1], pts[2], 0.01, seg=6)
    B.sphere('WornIron', pts[1], 0.012, seg=6)
    for z in (1.9, 2.3):
        B.box('WornIron', cx - 0.018, cx + 0.018, BACK_Y - 0.026, BACK_Y, z - 0.008, z + 0.008)


def build_sun_static(B):
    """The night-light: a painted tin sun on stand-offs from the wall. A disc behind the glass, twelve rays (long and
    short, yellow and orange), a brass rim round the glass, and a sleeping face in dark tin strips over the glass (the
    glass is Att14aSunLamp: the face shows dark on it when it glows)."""
    sx, sz = SUN
    yb = SUN_Y + 0.008
    B.cyl(ATLAS_MAT, (sx, yb, sz), (sx, yb + 0.014, sz), 0.2, seg=32, cell='sw_sun')
    for k in range(12):
        a = 2 * math.pi * k / 12 + math.pi / 12
        long_ = k % 2 == 0
        r0, r1, hw = 0.19, (0.36 if long_ else 0.29), (0.11 if long_ else 0.13)
        pts = [(sx + r0 * math.cos(a - hw), sz + r0 * math.sin(a - hw)), (sx + r1 * math.cos(a), sz + r1 * math.sin(a)),
               (sx + r0 * math.cos(a + hw), sz + r0 * math.sin(a + hw))]
        B.prism_xz(ATLAS_MAT, pts, yb + 0.002, yb + 0.01, cell='sw_sun' if long_ else 'sw_ray')
    B.torus('Brass', (sx, SUN_Y - 0.004, sz), (0, 1, 0), SUN_GLASS_R + 0.008, 0.009, seg=32, rseg=6)
    for k in range(3):                                                         # stand-offs to the wall
        a = math.radians(90 + 120 * k)
        p = (sx + 0.12 * math.cos(a), sz + 0.12 * math.sin(a))
        B.cyl('WornIron', (p[0], yb + 0.014, p[1]), (p[0], BACK_Y, p[1]), 0.008, seg=6)
    # The sleeping face on the glass: two closed eyes (arcs, smiling), a small smile.

    def on_glass(x, z):
        rr = ((x - sx) ** 2 + (z - sz) ** 2) / SUN_GLASS_R ** 2
        return SUN_Y - 0.055 * math.sqrt(max(0.0, 1 - rr)) - 0.004
    for ex in (-0.052, 0.052):
        pts = [(sx + ex + 0.03 * math.cos(math.radians(a)), sz + 0.03 + 0.022 * math.sin(math.radians(a))) for a in range(200, 341, 20)]
        B.merge(sweep_bm([(x, on_glass(x, z), z) for x, z in pts], 0.0055), ATLAS_MAT, 'sw_iron')
    pts = [(sx + 0.055 * math.cos(math.radians(a)), sz - 0.025 + 0.04 * math.sin(math.radians(a))) for a in range(215, 326, 15)]
    B.merge(sweep_bm([(x, on_glass(x, z), z) for x, z in pts], 0.0055), ATLAS_MAT, 'sw_iron')


def build_windows(B):
    """W1 (to the light well): frosted wired glass glowing cold (Att14aWellGlow), its lower panes painted out to 1.95;
    W2 (borrowed light from the night corridor): reeded glass glowing warm (Att14aCorridorGlow). Frames, bars, sills.
    Returns the glow objects' builders' quads."""
    glows = {}
    for name, (x0, x1, sill, head), glow, black in (('W1', W1, 'Att14aWellGlow', W1_BLACK), ('W2', W2, 'Att14aCorridorGlow', None)):
        gy = BACK_Y + 0.1
        G = glows.setdefault(glow, MB())
        z0 = black if black else sill + 0.1
        G.face(glow, [(x0, gy, z0), (x1, gy, z0), (x1, gy, head), (x0, gy, head)])
        if black:
            B.box(ATLAS_MAT, x0, x1, gy, gy + 0.004, sill, black, cell='sw_black')
        fy0, fy1 = gy - 0.06, gy - 0.004
        xc = (x0 + x1) / 2
        B.box('PigeonWood', x0, x0 + 0.05, fy0, fy1, sill, head)
        B.box('PigeonWood', x1 - 0.05, x1, fy0, fy1, sill, head)
        B.box('PigeonWood', x0, x1, fy0, fy1, head - 0.05, head)
        B.box('PigeonWood', x0, x1, fy0, fy1, sill, sill + (0.05 if black else 0.1))
        B.box('PigeonWood', xc - 0.02, xc + 0.02, fy0 + 0.01, fy1, sill, head)
        for tz in ((black or sill), (sill + head) / 2 + 0.25):
            if sill < tz < head:
                B.box('PigeonWood', x0, x1, fy0 + 0.01, fy1, tz - 0.02, tz + 0.02)
        for k in (1, 3):                                                     # the glazing bars
            x = x0 + (x1 - x0) * k / 4
            B.box('PigeonWood', x - 0.012, x + 0.012, fy0 + 0.02, fy1, sill, head)
        B.box('PigeonWood', x0 - 0.05, x1 + 0.05, BACK_Y - 0.07, gy - 0.06, sill - 0.04, sill)   # the sill board
        B.box('WinPlaster', x0 - 0.06, x0, BACK_Y - 0.015, BACK_Y, sill - 0.04, head + 0.06)     # the plaster reveal's lip
        B.box('WinPlaster', x1, x1 + 0.06, BACK_Y - 0.015, BACK_Y, sill - 0.04, head + 0.06)
        B.box('WinPlaster', x0 - 0.06, x1 + 0.06, BACK_Y - 0.015, BACK_Y, head, head + 0.06)
        if name == 'W1':                                                    # the wire in the glass, scratched paint
            for k in range(1, 12):
                z = black + (head - black) * k / 12
                B.box(ATLAS_MAT, x0, x1, gy - 0.002, gy - 0.0015, z - 0.002, z + 0.002, cell='sw_tin')
    return glows


def build_rollers(B):
    """The rollers (static: the blinds roll up into them), W1's long brackets out to y 1.0 with struts, W2's short ones
    and a pelmet, the cord drums, the W1 / W2 roundels; and the cord: up the crank's standard from the pulley on its
    gearbox, over two pulleys under the ceiling, to W1's drum and to W2's, and back across between the drums."""
    for (x0, x1), ry, (dx0, dx1, dr) in ((W1_BLIND, W1_ROLLER_Y, W1_DRUM), (W2_BLIND, W2_ROLLER_Y, W2_DRUM)):
        B.cyl(ATLAS_MAT, (x0 - 0.02, ry, ROLLER_Z), (x1 + 0.02, ry, ROLLER_Z), ROLLER_R, seg=12, cell='sw_wood')
        B.cyl('WornIron', (dx0, ry, ROLLER_Z), (dx1, ry, ROLLER_Z), dr, seg=16)
        B.torus('WornIron', ((dx0 + dx1) / 2, ry, ROLLER_Z), (1, 0, 0), dr, 0.008, seg=16, rseg=4)
        bx = (x0 - 0.05, max(x1, dx1) + 0.05) if dx0 > x1 else (min(x0, dx0) - 0.05, x1 + 0.05)
        for x in bx:
            B.box('WornIron', x - 0.015, x + 0.015, ry - 0.05, BACK_Y, ROLLER_Z - 0.04, ROLLER_Z + 0.04)
            B.cyl('WornIron', (x, ry, ROLLER_Z), (x + (0.02 if x > (x0 + x1) / 2 else -0.02), ry, ROLLER_Z), 0.02, seg=8)
            if ry < 1.2:                                                    # W1's arms reach out 0.4: a strut under each
                B.cyl('WornIron', (x, BACK_Y, ROLLER_Z - 0.3), (x, ry + 0.05, ROLLER_Z - 0.035), 0.012, seg=6)
                B.box('WornIron', x - 0.03, x + 0.03, BACK_Y - 0.01, BACK_Y, ROLLER_Z - 0.36, ROLLER_Z + 0.06)
    B.box('PigeonWood', W2_BLIND[0] - 0.12, W2_BLIND[1] + 0.08, 1.2, BACK_Y, ROLLER_Z + 0.06, ROLLER_Z + 0.09)    # W2's pelmet
    B.box('PigeonWood', W2_BLIND[0] - 0.12, W2_BLIND[1] + 0.08, 1.2, 1.22, ROLLER_Z - 0.06, ROLLER_Z + 0.09)
    for key, x, y in (('w1', (W1[0] + W1[1]) / 2, BACK_Y - 0.003), ('w2', (W2[0] + W2[1]) / 2, 1.199)):
        u0, v0, u1, v1 = cell_uv(key)
        r, zc = 0.05, (3.38 if key == 'w1' else ROLLER_Z + 0.015)
        B.cyl('Brass', (x, y + 0.001, zc), (x, y + 0.006, zc), r + 0.008, seg=20)
        B.disc(SIGNS_MAT, (x, y, zc), r, key, seg=20)
    # The cord.
    sx, sy = STANDARD
    px, pz, pr = CRANK_PULLEY
    top = CEIL - 0.13
    left, right = (px - pr, sy, pz), (px + pr, sy, pz)
    w1top = (W1_DRUM[1] - 0.02, W1_ROLLER_Y, ROLLER_Z + W1_DRUM[2])
    w1bot = (W1_DRUM[1] - 0.02, W1_ROLLER_Y, ROLLER_Z - W1_DRUM[2])
    w2top = (W2_DRUM[0] + 0.02, W2_ROLLER_Y, ROLLER_Z + W2_DRUM[2])
    w2bot = (W2_DRUM[0] + 0.02, W2_ROLLER_Y, ROLLER_Z - W2_DRUM[2])
    runs = [(left, (px - pr, sy, top)), ((px - pr, sy, top), w1top), (right, (px + pr, sy, top)), ((px + pr, sy, top), w2top),
            (w1bot, w2bot)]
    for a, b in runs:
        B.cyl(ATLAS_MAT, a, b, 0.0055, seg=6, cell='sw_string')
    for x in (px - pr - 0.04, px + pr + 0.04):                              # the pulleys under the ceiling
        B.cyl('WornIron', (x, sy - 0.012, top), (x, sy + 0.012, top), 0.04, seg=14)
    B.box('WornIron', px - pr - 0.09, px + pr + 0.09, sy - 0.03, sy + 0.03, top + 0.03, CEIL)


def build_crank_static(B):
    """The crank's iron standard (a column to the ceiling), its gearbox, the cord's pulley on top, the clutch on its
    side; the drive plate on two arms beside it."""
    sx, sy = STANDARD
    B.box('CastIron', sx - 0.04, sx + 0.04, sy - 0.04, sy + 0.04, 0.0, CEIL)
    B.box('CastIron', sx - 0.1, sx + 0.1, sy - 0.1, sy + 0.1, 0.0, 0.05)
    B.box('CastIron', sx - 0.07, sx + 0.07, sy - 0.07, sy + 0.07, CEIL - 0.06, CEIL)
    gx0, gx1, gy0, gy1, gz0, gz1 = GEARBOX
    B.box('WornIron', gx0, gx1, gy0, gy1, gz0, gz1)
    B.box('WornIron', gx0 - 0.03, gx1 + 0.03, gy0 - 0.02, gy1 + 0.02, gz0 - 0.03, gz0)
    B.box('WornIron', gx0 - 0.015, gx1 + 0.015, gy0 - 0.01, gy1 + 0.01, gz1, gz1 + 0.025)
    for x in (gx0 + 0.03, gx1 - 0.03):
        for z in (gz0 + 0.04, gz1 - 0.04):
            B.sphere('Brass', (x, gy0 - 0.003, z), 0.009, seg=6)
    x, y, z, r = CRANK
    B.cyl('WornIron', (x, gy0, z), (x, gy0 - 0.03, z), 0.05, seg=14)
    px, pz, pr = CRANK_PULLEY
    B.cyl('WornIron', (px, sy - 0.012, pz), (px, sy + 0.012, pz), pr - 0.01, seg=18)
    B.torus('WornIron', (px, sy, pz), (0, 1, 0), pr - 0.006, 0.009, seg=18, rseg=4)
    B.box('WornIron', px - 0.02, px + 0.02, sy - 0.03, sy + 0.03, gz1 + 0.02, pz)
    # The clutch on the gearbox's right side: two plates, a brass friction ring, the spring.
    cz = 0.86
    B.cyl('WornIron', (gx1, sy - 0.04, cz), (gx1 + 0.02, sy - 0.04, cz), 0.085, seg=20)
    B.cyl('Brass', (gx1 + 0.02, sy - 0.04, cz), (gx1 + 0.03, sy - 0.04, cz), 0.08, seg=20)
    B.cyl('WornIron', (gx1 + 0.03, sy - 0.04, cz), (gx1 + 0.05, sy - 0.04, cz), 0.085, seg=20)
    for k in range(4):
        B.torus('WornIron', (gx1 + 0.06 + k * 0.012, sy - 0.04, cz), (1, 0, 0), 0.03, 0.005, seg=10, rseg=4)
    # The drive plate on two arms from the standard, beside the crank.
    x0, x1, z0, z1, fy = DRIVE_PLATE
    B.box('CastIron', x0 - 0.012, x1 + 0.012, fy + 0.001, fy + 0.012, z0 - 0.012, z1 + 0.012)
    for zz in (z0 + 0.08, z1 - 0.08):
        B.box('CastIron', sx + 0.04, x0 + 0.04, fy + 0.012, fy + 0.03, zz - 0.015, zz + 0.015)
    B.decal(SIGNS_MAT, x0, x1, z0, z1, fy, 'drive')


def build_eye_static(B):
    """The eye (a lux meter) over the door end: its board (LIGHT METER, the lamps' labels, DARK (REST HOUR), REST HOUR
    BEGINS WHEN THE ROOM IS DARK), an almond brass rim, the dark lens with a brass iris, the lamps' bezels."""
    x0, x1, z0, z1, fy = EYEBOARD
    B.box('CastIron', x0 - 0.01, x1 + 0.01, fy + 0.001, BACK_Y, z0 - 0.01, z1 + 0.01)
    B.decal(SIGNS_MAT, x0, x1, z0, z1, fy, 'eyeboard')
    ex, ez = EYE
    rim = [(ex + 0.2 * math.cos(t), ez + (0.12 if t <= math.pi else 0.09) * math.sin(t)) for t in
           [2 * math.pi * k / 32 for k in range(33)]]
    B.prism_xz('CastIron', [p for p in rim[:-1]], fy - 0.012, fy)
    B.merge(sweep_bm([(x, fy - 0.014, z) for x, z in rim], 0.012, seg=8), 'Brass')
    B.sphere('EyeDark', (ex, fy - 0.012, ez), 0.085, seg=20, scale=(1, 0.45, 1))
    B.torus('HandledBrass', (ex, fy - 0.046, ez), (0, 1, 0), 0.05, 0.007, seg=24, rseg=5)
    B.torus('HandledBrass', (ex, fy - 0.024, ez), (0, 1, 0), 0.086, 0.006, seg=24, rseg=5)
    for name, (lx, lz, r) in EYE_LAMPS.items():
        B.torus('Brass', (lx, EYE_LAMP_Y + 0.004, lz), (0, 1, 0), r + 0.006, 0.006 if r < 0.05 else 0.009, seg=20, rseg=5)
        B.cyl('CastIron', (lx, fy, lz), (lx, EYE_LAMP_Y + 0.004, lz), r + 0.004, seg=16)
    # A cable from the eye's board down to the door's frame (the door's latch is on it).
    B.cyl('WornIron', (x1 - 0.06, BACK_Y - 0.01, z0), (x1 - 0.06, BACK_Y - 0.01, 1.9), 0.009, seg=6)
    B.cyl('WornIron', (x1 - 0.06, BACK_Y - 0.01, 1.9), (RWALL[0] - 0.01, BACK_Y - 0.01, 1.9), 0.009, seg=6)
    B.cyl('WornIron', (RWALL[0] - 0.01, BACK_Y - 0.01, 1.9), (RWALL[0] - 0.01, RAIL_HATCH[1] + 0.06, 1.9), 0.009, seg=6)


def build_chair(B):
    """The nurse's chair facing the beds (-x): a plain wooden chair, seat top 0.42, its back on the +x side; a brass
    hook on an arm from the back's top rail (the gown hangs on it clear of the back, toward the room)."""
    cx, cy, top = CHAIR
    h = CHAIR_SEAT / 2
    B.box('PigeonWood', cx - h, cx + h, cy - h, cy + h, top - 0.035, top)
    B.box('PigeonWood', cx - h + 0.02, cx + h - 0.02, cy - h + 0.02, cy + h - 0.02, top - 0.09, top - 0.035)
    for dx in (-h + 0.025, h - 0.025):
        for dy in (-h + 0.025, h - 0.025):
            B.box('PigeonWood', cx + dx - 0.02, cx + dx + 0.02, cy + dy - 0.02, cy + dy + 0.02, 0.0, top - 0.035)
    for dy in (-h + 0.025, h - 0.025):
        B.box('PigeonWood', cx + h - 0.045, cx + h - 0.005, cy + dy - 0.02, cy + dy + 0.02, top, 0.98)
        B.box('PigeonWood', cx - h + 0.025, cx + h - 0.025, cy + dy - 0.012, cy + dy + 0.012, 0.14, 0.17)
    for za, zb in ((0.62, 0.7), (0.88, 0.98)):
        B.box('PigeonWood', cx + h - 0.04, cx + h - 0.01, cy - h + 0.03, cy + h - 0.03, za, zb)
    for k in range(3):
        y = cy + (k - 1) * 0.1
        B.box('PigeonWood', cx + h - 0.035, cx + h - 0.015, y - 0.015, y + 0.015, 0.7, 0.88)
    # The hook: a brass arm out of the back's top rail (+x), its tip turned up.
    hx, hy, hz = GOWN_HOOK
    r = 0.008
    B.box('Brass', cx + h - 0.01, cx + h + 0.005, hy - 0.025, hy + 0.025, hz - 0.035, hz + 0.02)
    B.cyl('Brass', (cx + h, hy, hz - r), (hx + 0.015, hy, hz - r), r, seg=8)
    B.cyl('Brass', (hx + 0.015, hy, hz - r), (hx + 0.03, hy, hz + 0.03), r, seg=8)
    B.sphere('Brass', (hx + 0.03, hy, hz + 0.03), 0.012, seg=8)
    # A clipboard on the seat (the night's register), a pencil.
    n0 = B.mark()
    B.box(ATLAS_MAT, -0.11, 0.11, -0.15, 0.15, 0.0, 0.008, cell='sw_wood')
    B.box(ATLAS_MAT, -0.1, 0.1, -0.14, 0.13, 0.008, 0.012, cell='sw_paper')
    B.box(ATLAS_MAT, -0.04, 0.04, 0.11, 0.15, 0.008, 0.02, cell='sw_tin')
    B.cyl(ATLAS_MAT, (-0.06, -0.05, 0.016), (0.08, -0.08, 0.016), 0.004, seg=6, cell='sw_sun')
    B.xform(n0, Matrix.Translation((cx - 0.02, cy - 0.02, top)) @ Matrix.Rotation(math.radians(80), 4, 'Z'))


def build_lighting(B, coll):
    """The ceiling globes on their rods: one dim and lit (EMIT AttGlobeLamp), two gone out."""
    L = MB()
    for x, y, z in (GLOBE,) + DEAD_GLOBES:
        B.cyl('WornIron', (x, y, CEIL), (x, y, z + 0.17), 0.01, seg=6)
        B.cyl('WornIron', (x, y, CEIL), (x, y, CEIL - 0.03), 0.05, seg=10)
        B.cyl('WornIron', (x, y, z + 0.17), (x, y, z + 0.13), 0.045, 0.06, seg=10)
        if (x, y, z) == GLOBE:
            L.sphere('AttGlobeLamp', (x, y, z), 0.12, seg=14)
        else:
            B.sphere(ATLAS_MAT, (x, y, z), 0.12, seg=12, cell='sw_glass')
    return L.obj('Att14aGlobe', coll, origin=GLOBE)


def build_speaker(B, coll):
    """The tannoy high on the rest-hour wall (art/common/voice_props.py), turned to the beds; Att14aSpeaker at its
    horn's mouth, the emitter for the rest-hour announcement."""
    mouth = Vector((TANNOY[0] - 0.1, TANNOY[1] - 0.4, TANNOY[2] - 0.1))
    vp = _voice_props()
    if vp is not None:
        info = vp.tannoy(B, vp.xform(TANNOY, 0.0), tilt=16.0, aim=-30.0, conduit=0.36, conduit_dir=90.0)
        mouth = Vector(info['mouth'])
    e = bpy.data.objects.new('Att14aSpeaker', None)
    e.empty_display_type = 'SPHERE'
    e.empty_display_size = 0.1
    e.location = mouth
    coll.objects.link(e)
    return e


# =====================================================================================================================
# The back ward (atmosphere): its shell, its far windows, sixteen made-up beds (linked duplicates of one mesh)
# =====================================================================================================================
def build_ward(coll):
    W = MB()
    x0, x1, fy = WARD
    W.box('WinLino', x0, x1, BACK_Y2, fy, -0.2, -0.001)
    W.box('WinPlaster', x0 - 0.15, x1 + 0.15, BACK_Y2, fy + 0.2, CEIL, CEIL + 0.15)
    for (za, zb, mt) in ((0.0, DADO, 'WinDado'), (DADO, CEIL, 'WinPlaster')):
        W.box(mt, x0 - 0.15, x0, BACK_Y2, fy + 0.2, za, zb)
        W.box(mt, x1, x1 + 0.15, BACK_Y2, fy + 0.2, za, zb)
    holes = [(a, b, 1.2, 3.0) for a, b in WARD_WINDOWS]
    holed_wall(W, x0, x1, fy, fy + 0.2, 0.0, CEIL, holes)
    G = MB()
    for a, b in WARD_WINDOWS:
        G.face('Att14aWardNight', [(a, fy + 0.12, 1.2), (b, fy + 0.12, 1.2), (b, fy + 0.12, 3.0), (a, fy + 0.12, 3.0)])
        for x in (a + (b - a) / 3, a + 2 * (b - a) / 3):
            W.box('PigeonWood', x - 0.015, x + 0.015, fy + 0.06, fy + 0.11, 1.2, 3.0)
        for z in (1.8, 2.4):
            W.box('PigeonWood', a, b, fy + 0.06, fy + 0.11, z - 0.015, z + 0.015)
        W.box('PigeonWood', a - 0.04, b + 0.04, fy - 0.06, fy + 0.02, 1.16, 1.2)
    # The ward's back face of the dormitory wall, and its skirting.
    W.box('PigeonWood', x0, x1, fy - 0.02, fy, 0.0, 0.12)
    shell = W.obj('Att14aWard', coll)
    night = G.obj('Att14aWardNight', coll)
    me = ward_bed_mesh()
    beds = []
    k = 0
    for fy0 in WARD_ROWS:
        for x in WARD_BED_X:
            k += 1
            ob = bpy.data.objects.new('Att14aWardBed%02d' % k, me)
            ob.location = (x, fy0, 0.0)
            coll.objects.link(ob)
            beds.append(ob)
    return [shell, night] + beds


def ward_bed_mesh():
    """A made-up iron bed, its foot toward the camera at local y 0, its head at y 1.7, a locker by its head (+x). One
    material (the atlas) so each copy is one draw call."""
    B = MB()
    hw, L = 0.4, 1.7
    I = 'sw_ward'
    for px, py, top in ((-hw + 0.02, 0.02, 0.78), (hw - 0.02, 0.02, 0.78), (-hw + 0.02, L - 0.02, 1.05), (hw - 0.02, L - 0.02, 1.05)):
        B.cyl(ATLAS_MAT, (px, py, 0.0), (px, py, top), 0.016, seg=6, cell=I)
        B.sphere(ATLAS_MAT, (px, py, top + 0.012), 0.022, seg=6, cell=I)
    for y, zs in ((0.02, (0.36, 0.76)), (L - 0.02, (0.36, 0.84, 1.03))):
        for z in zs:
            B.cyl(ATLAS_MAT, (-hw + 0.02, y, z), (hw - 0.02, y, z), 0.011, seg=6, cell=I)
    for x in (-0.2, 0.0, 0.2):
        B.cyl(ATLAS_MAT, (x, 0.02, 0.36), (x, 0.02, 0.76), 0.006, seg=4, cell=I)
    for x in (-0.27, -0.09, 0.09, 0.27):
        B.cyl(ATLAS_MAT, (x, L - 0.02, 0.36), (x, L - 0.02, 1.03), 0.006, seg=4, cell=I)
    for x in (-hw + 0.02, hw - 0.02):
        B.box(ATLAS_MAT, x - 0.012, x + 0.012, 0.04, L - 0.04, 0.33, 0.36, cell=I)
    B.tbox(ATLAS_MAT, -hw + 0.025, hw - 0.025, 0.05, L - 0.4, 0.36, 0.52, {'+z': 'blanket', '-y': 'blanket', 'all': 'sw_blanket'})
    B.tbox(ATLAS_MAT, -hw + 0.035, hw - 0.035, L - 0.4, L - 0.05, 0.36, 0.5, {'all': 'sw_wardsheet'})
    B.tbox(ATLAS_MAT, -hw + 0.03, hw - 0.03, L - 0.44, L - 0.37, 0.5, 0.53, {'all': 'sw_wardsheet'})
    pillow(B, (0.0, L - 0.2, 0.545), (0.58, 0.28, 0.1))
    B.tbox(ATLAS_MAT, hw + 0.06, hw + 0.4, L - 0.36, L - 0.02, 0.0, 0.62, {'-y': 'locker', 'all': 'sw_lockerpaint'})
    B.box(ATLAS_MAT, hw + 0.05, hw + 0.41, L - 0.37, L - 0.01, 0.62, 0.645, cell='sw_wood')
    return B.mesh('Att14aWardBed')


# =====================================================================================================================
# What the game moves
# =====================================================================================================================
def build_pawl(coll):
    """Att14aPawl: the REST HOUR brake's red lever, its pivot on the wall. Built off: handle straight up. +40 deg about
    x (Blender and game alike) throws it on: the handle leans toward the camera."""
    B = MB()
    px, py, pz = PAWL
    B.cyl('LeverRed', (px, py, pz), (px, py, pz + PAWL_LEN), 0.018, 0.015, seg=10)
    B.cyl('LeverRed', (px - 0.07, py, pz + PAWL_LEN), (px + 0.07, py, pz + PAWL_LEN), 0.024, seg=12)
    B.cyl('HandledBrass', (px - 0.05, py, pz + PAWL_LEN), (px + 0.05, py, pz + PAWL_LEN), 0.0255, seg=12)
    B.cyl('LeverRed', (px - 0.035, py, pz), (px + 0.035, py, pz), 0.04, seg=14)
    B.box('LeverRed', px - 0.025, px + 0.025, py - 0.02, py + 0.02, pz - 0.1, pz - 0.02)
    B.box('LeverRed', px - 0.018, px + 0.018, py - 0.06, py - 0.02, pz + 0.12, pz + 0.16)        # the latch's thumb catch
    B.cyl('LeverRed', (px + 0.035, py, pz + 0.21), (px + 0.075, py, pz + 0.21), 0.009, seg=6)   # the dog's pin (on the teeth)
    return B.obj('Att14aPawl', coll, origin=PAWL)


def build_dial_hand(coll):
    """Att14aDialHand: a brass hand with a dark edge, a counterweight tail and a hub; origin on the dial's centre (just
    in front of the face); built pointing up. Clockwise as the camera sees it = Blender rotation about +y."""
    B = MB()
    dx, dz = DIAL
    R = DIAL_R - 0.03
    pts = [(-0.014, -0.012), (-0.005, R), (0.0, R + 0.012), (0.005, R), (0.014, -0.012), (0.0, -0.08)]
    B.prism_xz('GaugeNeedle', [(dx + x * 1.35, dz + z * 1.03) for x, z in pts], HAND_Y + 0.0005, HAND_Y + 0.0035)
    B.prism_xz('Brass', [(dx + x, dz + z) for x, z in pts], HAND_Y - 0.003, HAND_Y + 0.0005)
    B.cyl('Brass', (dx, HAND_Y + 0.004, dz), (dx, HAND_Y - 0.008, dz), 0.022, seg=14)
    B.cyl('GaugeNeedle', (dx, HAND_Y - 0.008, dz), (dx, HAND_Y - 0.011, dz), 0.008, seg=8)
    return B.obj('Att14aDialHand', coll, origin=(dx, HAND_Y, dz))


def build_sun_lamp(coll):
    """Att14aSunLamp: the tin sun's glass, a low dome (own emissive)."""
    B = MB()
    sx, sz = SUN
    B.sphere('Att14aSunLamp', (sx, SUN_Y, sz), SUN_GLASS_R, seg=24, scale=(1, 0.37, 1))
    return B.obj('Att14aSunLamp', coll, origin=(sx, SUN_Y, sz))


def build_crank(coll):
    """Att14aCrank: the handwheel, as DL-14's AttCrank: rim, four spokes, hub, the axle back to the gearbox, a grip worn
    bright. Origin on the axle at the wheel's centre; it spins about Blender y (the game's z)."""
    B = MB()
    x, y, z, r = CRANK
    B.torus('WornIron', (x, y, z), (0, 1, 0), r, 0.017, seg=28, rseg=6)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        B.cyl('WornIron', (x, y, z), (x + r * math.cos(a), y, z + r * math.sin(a)), 0.011, seg=6)
    B.cyl('WornIron', (x, y - 0.035, z), (x, y + 0.04, z), 0.035, seg=12)
    B.cyl('WornIron', (x, y, z), (x, GEARBOX[2] - 0.03, z), 0.018, seg=8)
    gx, gz = x + r * math.cos(math.radians(135)), z + r * math.sin(math.radians(135))
    B.cyl('HandledBrass', (gx, y, gz), (gx, y - 0.11, gz), 0.019, seg=10)
    B.sphere('HandledBrass', (gx, y - 0.115, gz), 0.024, seg=10)
    return B.obj('Att14aCrank', coll, origin=(x, y, z))


def blind_fabric(B, x0, x1, y, top, bottom, cell, nx=6, nz=8):
    u0, v0, u1, v1 = cell_uv(cell)
    grid = []
    for j in range(nz + 1):
        row = []
        for i in range(nx + 1):
            z = top - (top - bottom) * j / nz
            x = x0 + (x1 - x0) * i / nx
            wob = 0.006 * math.sin(i * 2.1 + j * 0.7) * (j / nz)
            row.append((x, y + wob, z, u0 + (u1 - u0) * i / nx, v1 - (v1 - v0) * j / nz))
        grid.append(row)
    for j in range(nz):
        for i in range(nx):
            q = [grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1], grid[j][i]]
            B.face(ATLAS_MAT, [p[:3] for p in q], [p[3:] for p in q])
            B.face(ATLAS_MAT, [p[:3] for p in reversed(q)], [p[3:] for p in reversed(q)])     # its back (seen from above)


def build_blinds(coll):
    """Att14aBlindW1 (fabric only, DOWN to 1.97), Att14aHemW1 (its hem bar and the peg), Att14aBlindW2 (DOWN, hem bar
    and pull ring included, to 1.95). Blackout cloth: the 'blanket' weave dyed black is too busy; a dark swatch reads."""
    x0, x1 = W1_BLIND
    B = MB()
    blind_fabric(B, x0, x1, W1_FABRIC_Y, ROLLER_Z, W1_FABRIC_BOTTOM, 'sw_black')
    w1 = B.obj('Att14aBlindW1', coll, origin=((x0 + x1) / 2, W1_ROLLER_Y, ROLLER_Z))
    H = MB()
    hx, hy, hz = HEM_W1
    hy0, hy1, hz0, hz1 = HEM_BAR
    H.box(ATLAS_MAT, x0 - 0.01, x1 + 0.01, hy0, hy1, hz0, hz1, cell='sw_wood')
    for x in (x0 + 0.02, x1 - 0.02):
        H.box(ATLAS_MAT, x - 0.012, x + 0.012, hy0 - 0.004, hy1 + 0.004, hz0 - 0.004, hz1 + 0.004, cell='sw_brass')
    H.box('Brass', hx - 0.035, hx + 0.035, hy0 - 0.006, hy0, 1.895, 1.995)                  # the peg's plate
    r = 0.012
    H.cyl('Brass', (hx, hy0 - 0.006, hz - r), (hx, 0.95, hz - r), r, seg=10)                 # the peg: its top at 1.93
    H.sphere('Brass', (hx, 0.946, hz - r + 0.006), 0.02, seg=10)
    for z in (1.915, 1.975):
        H.sphere('HandledBrass', (hx, hy0 - 0.007, z), 0.006, seg=6)
    hem = H.obj('Att14aHemW1', coll, origin=HEM_W1)
    x0, x1 = W2_BLIND
    B = MB()
    blind_fabric(B, x0, x1, W2_FABRIC_Y, ROLLER_Z, W2_HEM + 0.03, 'sw_black')
    B.box(ATLAS_MAT, x0 - 0.01, x1 + 0.01, W2_FABRIC_Y - 0.018, W2_FABRIC_Y + 0.012, W2_HEM, W2_HEM + 0.045, cell='sw_wood')
    xc = (x0 + x1) / 2
    B.torus(ATLAS_MAT, (xc, W2_FABRIC_Y - 0.022, W2_HEM + 0.022), (0, 1, 0), 0.016, 0.004, seg=12, rseg=4, cell='sw_brass')
    w2 = B.obj('Att14aBlindW2', coll, origin=(xc, W2_ROLLER_Y, ROLLER_Z))
    return [w1, hem, w2]


CAPE = ((-0.095, 0.15, 0.07), (-0.2, 0.17, 0.09), (-0.4, 0.19, 0.1), (-0.6, 0.2, 0.105), (-0.665, 0.2, 0.105))
CAPE_BACK = 0.03          # the cape's back sits only this far behind its hook (so it hangs in front of a blind)


def cape_ring(z, w, df, k, n=24, fold=0.0):
    """A ring of the cape at height z (local to its hook): half-width w, front depth df, back depth CAPE_BACK, with
    folds (fold: their amplitude)."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        ry = df if math.sin(t) < 0 else CAPE_BACK
        r = 1 + fold * math.sin(7 * t + 0.6 * k)
        pts.append(Vector((w * math.cos(t) * r, ry * math.sin(t) * r, z)))
    return pts


def build_gown(coll):
    """Att14aGown (the design review: a heavy wool nurse's cape, so it plainly can hold a blind down): navy wool with a
    red lining showing at its front edges, a collar with a brass clasp and chain, and a weighted hem: a stitched hem
    band with lead weights sewn in along the front and a chain run round the hem. On a wooden hanger with a wire hook;
    origin at the inside top of the hook (the hook point), hanging along -z (0.665 long), its front to -y, its back
    only 3 cm behind the hook. Built on the chair's hook."""
    import dl12
    B = MB()
    hx, hy, hz = GOWN_HOOK
    M = Matrix.Translation(GOWN_HOOK)
    # The body: rings from the shoulders to the hem, folds growing toward the hem; closed at both ends.
    tmp = bmesh.new()
    rings = []
    for k, (z, w, df) in enumerate(CAPE):
        rings.append([tmp.verts.new(p) for p in cape_ring(z, w, df, k, fold=0.07 * k / (len(CAPE) - 1))])
    n = len(rings[0])
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            tmp.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i]))
    tmp.faces.new(rings[0])
    tmp.faces.new(rings[-1][::-1])
    zc = (CAPE[0][0] + CAPE[-1][0]) / 2
    B.merge(tmp, ATLAS_MAT, proj_xz('gown', (hx, hy, hz + zc), 0.42, CAPE[0][0] - CAPE[-1][0]), M=M)
    # The collar (a stand-up band round the hanger's neck), the clasp: two brass discs and a short chain.
    tmp = d17.rounded_box((0.13, 0.09, 0.05), (0.0, -0.012, -0.075), p=3.0, cuts=2, mat=0)
    B.merge(tmp, ATLAS_MAT, proj_xz('gown', (hx, hy, hz - 0.075), 0.42, 0.6), M=M)
    for dx in (-0.025, 0.025):
        B.cyl('Brass', (hx + dx, hy - 0.056, hz - 0.085), (hx + dx, hy - 0.066, hz - 0.085), 0.013, seg=10)
    for k in range(3):
        B.torus('Brass', (hx - 0.012 + 0.012 * k, hy - 0.067, hz - 0.085), (0, 1, 0) if k % 2 else (0, 0, 1), 0.007, 0.0018, seg=8, rseg=3)
    # The red lining, turned back along the two front edges, from the collar to the hem.
    for side in (-1, 1):
        pts = []
        for z, w, df in CAPE:
            pts.append((hx + side * 0.012, hy - df - 0.002, hz + z))
        for (ax, ay, az), (bx, by, bz) in zip(pts, pts[1:]):
            B.box(ATLAS_MAT, min(ax, bx) - 0.006, max(ax, bx) + 0.006, min(ay, by) - 0.004, max(ay, by) + 0.002, bz, az, cell='sw_lining')
    B.box(ATLAS_MAT, hx - 0.003, hx + 0.003, hy - 0.112, hy - 0.06, hz + CAPE[-1][0], hz + CAPE[1][0], cell='sw_dark')   # the opening
    # The weighted hem: lead weights sewn in along the front (each a lump showing through the band), and a chain
    # stitched round the hem's edge.
    zh = hz + CAPE[-1][0]
    w, df = CAPE[-1][1], CAPE[-1][2]
    for i in range(9):
        t = math.pi + math.pi * (i + 0.5) / 9
        x, y = w * math.cos(t), df * math.sin(t)
        nrm = Vector((math.cos(t) / w, math.sin(t) / df, 0)).normalized()
        c = Vector((hx + x, hy + y, zh + 0.035)) + nrm * 0.004
        B.cyl(ATLAS_MAT, c - nrm * 0.006, c + nrm * 0.008, 0.019, seg=10, cell='sw_lead')
    m = 40
    for i in range(m):
        t = 2 * math.pi * i / m
        x, y = (w + 0.006) * math.cos(t), ((df if math.sin(t) < 0 else CAPE_BACK) + 0.006) * math.sin(t)
        tang = Vector((-w * math.sin(t), (df if math.sin(t) < 0 else CAPE_BACK) * math.cos(t), 0)).normalized()
        axis = tang.cross(Vector((0, 0, 1))) if i % 2 else Vector((0, 0, 1))
        B.torus('WornIron', (hx + x, hy + y, zh + 0.008), axis, 0.011, 0.0028, seg=8, rseg=3)
    # The hanger: a broad wooden bar and its wire hook.
    tmp = bmesh.new()
    dl12.hanger_bar(tmp, s=1.0)
    B.merge(tmp, ATLAS_MAT, 'sw_wood', M=M)
    tmp = bmesh.new()
    dl12.hanger_hook(tmp)
    B.merge(tmp, ATLAS_MAT, 'sw_brass', M=M)
    return B.obj('Att14aGown', coll, origin=GOWN_HOOK)


def build_door(coll):
    """Att14aDoor: the door to the corridor, panelled, a small vision panel, knobs both sides; shut in the end wall.
    Origin on its hinge (262.92, 0.45, 0); it opens +90 deg about z (Blender) into the corridor (+x)."""
    B = MB()
    hx, hy, _ = DOOR_HINGE
    dy0, dy1, dh = DOOR
    x0, x1 = hx - 0.02, hx + 0.02
    ly0, ly1, lh = dy0 + 0.008, dy1 - 0.008, dh - 0.008
    for a, b, c, d in ((ly0, ly0 + 0.1, 0.008, lh), (ly1 - 0.1, ly1, 0.008, lh), (ly0, ly1, 0.008, 0.18), (ly0, ly1, 0.86, 0.98),
                       (ly0, ly1, lh - 0.12, lh)):
        B.box('PigeonWood', x0, x1, a, b, c, d)
    B.box('PigeonWood', x0 + 0.008, x1 - 0.008, ly0 + 0.1, ly1 - 0.1, 0.18, 0.86)
    B.box('PigeonWood', x0 + 0.008, x1 - 0.008, ly0 + 0.1, ly1 - 0.1, 0.98, 1.2)
    B.box('PigeonWood', x0 + 0.008, x1 - 0.008, ly0 + 0.1, ly1 - 0.1, 1.5, lh - 0.12)
    B.box(ATLAS_MAT, x0 + 0.012, x1 - 0.012, ly0 + 0.1, ly1 - 0.1, 1.2, 1.5, cell='sw_glass')
    for side in (-1, 1):
        x = x0 - 0.035 if side < 0 else x1 + 0.035
        B.cyl('Brass', (x0 if side < 0 else x1, ly0 + 0.08, 0.92), (x, ly0 + 0.08, 0.92), 0.008, seg=6)
        B.sphere('Brass', (x, ly0 + 0.08, 0.92), 0.026, seg=10)
    for z in (1.25, 1.62):
        B.cyl('WornIron', (hx, hy, z - 0.05), (hx, hy, z + 0.05), 0.011, seg=8)
    return B.obj('Att14aDoor', coll, origin=DOOR_HINGE)


def build_eye_lamps(coll):
    out = []
    for name, (lx, lz, r) in EYE_LAMPS.items():
        B = MB()
        B.sphere(name, (lx, EYE_LAMP_Y, lz), r, seg=16, scale=(1, 0.55, 1))
        out.append(B.obj(name, coll, origin=(lx, EYE_LAMP_Y, lz)))
    return out


# =====================================================================================================================
def tris(ob):
    if ob.type != 'MESH':
        return 0
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def build_set(dl01, m, coll):
    make_textures()
    B = MB()
    build_shell(B)
    build_door_frame(B)
    build_rail(B)
    build_cupboard(B)
    build_bunks(B)
    build_lockers(B)
    build_pegs(B)
    build_rules(B)
    build_brake_static(B)
    build_dial_static(B)
    build_sun_static(B)
    glows = build_windows(B)
    build_rollers(B)
    build_crank_static(B)
    build_eye_static(B)
    build_chair(B)
    objs = [build_lighting(B, coll)]
    speaker = build_speaker(B, coll)
    objs.insert(0, B.obj('Att14aSet', coll))
    for name, G in glows.items():
        objs.append(G.obj(name, coll))
    objs.extend(build_ward(coll))
    objs.append(build_pawl(coll))
    objs.append(build_dial_hand(coll))
    objs.append(build_sun_lamp(coll))
    objs.append(build_crank(coll))
    objs.extend(build_blinds(coll))
    objs.append(build_gown(coll))
    objs.append(build_door(coll))
    objs.extend(build_eye_lamps(coll))
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
        seen.update(s.material.name for s in ob.material_slots)
        if ob.name.startswith('Att14aWardBed') and ob.name != 'Att14aWardBed01':
            continue
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        print('dl14a: %-18s tris %6d mats %d x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f  origin %s' % (
            ob.name, t, prim, min(v.x for v in bb), max(v.x for v in bb), min(v.y for v in bb), max(v.y for v in bb),
            min(v.z for v in bb), max(v.z for v in bb), tuple(round(c, 3) for c in ob.location)))
    print('dl14a: speaker at', tuple(round(c, 3) for c in speaker.location))
    print('dl14a: total tris %d (ward beds %d each, %d copies), draw calls (material slots) %d, materials %s' % (
        total_t, tris(bpy.data.objects['Att14aWardBed01']), len(WARD_BED_X) * len(WARD_ROWS), total_p, sorted(seen)))
    return objs


REPORT = """DL-14a Lights Out (art/ch1/dl14a.py), x 248.0-263.0, final coordinates (no shift).
Game coords: (x, y, z) = Blender (x, z, -y). Blender numbers are given as B(x, y, z).

MOVED (origin = pivot; built pose):
- Att14aPawl: pivot B(252.3, 1.36, 0.6) = game (252.3, 0.6, -1.36), on the back wall's cast-iron plate. Built OFF,
  the handle straight up (grip bar at height 1.05). Braked: rotateX(+40 deg) after restoring the rest quaternion,
  exactly as AttPawl (the handle leans toward the camera, over the brass toothed quadrant).
- Att14aDialHand: B(253.0, 1.356, 1.35) = game (253.0, 1.35, -1.356), the dial's centre, just in front of the face
  (face r 0.26 at B y 1.368; bezel r 0.27). Built pointing up at the fixed brass mark. Clockwise one turn per cycle:
  rotateZ(-2*PI*t/10) as AttDialHand. Face bands clockwise from the top: BRIGHT 0-3 s (0-108 deg) warm yellow,
  DIMMING 3-4.5 (108-162) gradient, DARK 4.5-8 (162-288) black with a small moon, BRIGHTENING 8-10 (288-360) gradient.
- Att14aSunLamp: B(253.9, 1.355, 2.55) = game (253.9, 2.55, -1.355); a low glass dome r 0.15 in the tin sun (rays to
  r 0.36). Its own material Att14aSunLamp, EMIT [1, .8, .42, 4] (built bright). A sleeping face in dark tin strips
  lies on the glass (in Att14aSet): it shows as a silhouette when the glass glows.
- Att14aCrank: B(258.7, 0.32, 0.5) = game (258.7, 0.5, -0.32), handwheel r 0.19 (as AttCrank); spins about game z
  (rotateZ) while the blinds move. Its gearbox (B x 258.52-258.88, y 0.5-0.8, z 0.26-1.08) and clutch sit on an
  iron standard at B(258.7, 0.66) running to the ceiling; the cord's pulley on top at height 1.2.
- Att14aBlindW1: origin = the middle of its roller axis B(256.2, 1.075, 3.25) = game (256.2, 3.25, -1.075). Fabric
  x 255.3-257.1 at B y 1.04, built DOWN from 3.25 to 1.97 (1.28 tall; the hem bar is NOT in it). Scale game y
  (Blender z) from 1 (down) to 0.04 (rolled up: fabric bottom 3.199).
- Att14aHemW1: origin = the peg's hook point B(256.2, 1.0, 1.93) = game (256.2, 1.93, -1.0) exactly: the top of the
  brass peg at that point (the peg runs from the hem bar out to B y 0.95, a knob at its end). It carries the hem bar
  (x 255.29-257.11, B y 1.02-1.06, height 1.95-2.0; the fabric ends inside it at 1.97) and the peg. Lowest metal 1.90.
  Move it with the blind: hem.y = 1.93 + (1 - s) * 1.28 (s = W1's scale); rolled up (s 0.04) = 3.159.
- Att14aBlindW2: origin = the middle of its roller axis B(260.1, 1.3, 3.25) = game (260.1, 3.25, -1.3). Fabric
  x 259.2-261.0 at B y 1.265, built DOWN to 1.95 with the hem bar (1.95-1.995) and a small brass pull ring on the
  bar's face included (nothing below 1.95). Scale game y. No peg.
- Att14aGown: now a heavy wool NURSE'S CAPE with a weighted hem (design review): navy wool, red lining at the
  front edges, a brass collar clasp, a stitched hem band with nine lead weights sewn in along the front and a chain
  round the hem's edge. Origin = the hanger's hook point (inside top of the wire hook, as AttCoat), built hanging on
  the chair's hook at B(261.0, 0.4, 0.95) = game (261.0, 0.95, -0.4); hangs along -z 0.665 to its hem (height 0.285;
  chain to 0.27), x 260.79-261.21, front toward the camera, rotation 0; its back is only 3 cm behind the hook, its
  front 0.11 in front. To hang it, put its origin on a hook point: W1's peg = Att14aHemW1's origin (its hem then at
  1.265, above bunks 2's deck 1.15; its back at B y 1.03, in front of the blind's fabric at 1.04); a wall peg =
  (x, 0.80, -1.345) game (the game's wallPeg z -1.38 is 3.5 cm behind the pegs' hook point).
  DEVIATION: the spec gives the hook at x 260.6 (the chair's x). The chair's seat is centred at 260.6 as specified;
  a hook on its back (x 260.8) would hang the gown into the chair's back or side-on to the camera, so the hook is on
  a brass arm out of the back's top rail and the gown hangs at x 261.0, facing the room. Use 261.0 for the pick-up.
- Att14aDoor: hinge B(262.92, 0.45, 0) = game (262.92, 0, -0.45). Leaf x 262.90-262.94, B y -0.442..0.442,
  height 0.008-1.742, knobs both sides, shut. Open: rotate about game y by +90 deg (Blender z +90): the free end
  swings into the corridor (+x). CHECK: index.html now does rotateY(-PI/2), which swings it into the room (-x); open, the leaf lies at B y 0.41-0.45 (game z -0.41..-0.45), x 262.92-263.80.
  NOTE for DL-14b: that is right beside the figures' rail (rails at 0.47 / 0.63; a figure's body reaches to 0.42),
  so either the figure's envelope or the door's open angle needs a centimetre or two there.
- Eye lamps (own objects, own materials, as built): Att14aEyeSun B(261.6, 1.37, 1.86), Att14aEyeW1 B(261.9, 1.37,
  1.86), Att14aEyeW2 B(262.2, 1.37, 1.86): small amber domes r 0.034, labelled NIGHT-LIGHT / WELL WINDOW / CORRIDOR
  WINDOW on the board under them; Att14aEyeDark B(261.9, 1.37, 1.53): the big green dome r 0.07, DARK (REST HOUR)
  beside it. Game: (x, height, -1.37). Built: EyeSun lit (sun bright), W1/W2/Dark off (both blinds down).
  EMIT: Att14aEyeSun/W1/W2 [1, .6, .18, 3 lit / 0 off], Att14aEyeDark [.36, 1, .46, 0 off; ~4 lit],
  Att14aSunLamp [1, .8, .42, 4 bright; 0 dark].
- Att14aSpeaker (empty): the tannoy's horn mouth, printed at build (about B(252.59, 0.95, 2.84) = game
  (252.59, 2.84, -0.95)); the tannoy hangs high on the rest-hour wall at x 252.75, turned to the beds.

SURFACES (as the spec; the mesh is built to these):
- Floor 0 from 248.15 to 262.85. Left wall face x 248.15; end wall 262.85-263.0; ceiling 3.5; back wall face B y 1.4.
- Bunk 1: x 248.3-250.3, top deck 1.15, B y -0.35..1.4 (two iron bunks pushed together, split at 249.3). Lower beds
  at 0.5 (decor). Over the deck, only the foot end's iron rail (B y -0.35, to 1.31) and the right bed's head (B y 1.4,
  to 1.43); the left bed's head stops at the deck so the vent is clear. The vent's grille lies on the deck (2 cm).
- The vent: x 248.55-249.35, sill 1.15, head 1.8, in the linen cupboard's face (B y 1.4; cupboard x 248.15-249.65,
  top 2.62); the dark duct behind it rises to the left.
- Lockers 1/2/3: x 250.3-250.8, 254.3-254.8, 257.6-258.1; top 0.55; B y -0.3..0.5. (A tin cup on 2, a towel on 3:
  decor, 7 cm and 3.5 cm.)
- Bunks 2: x 254.8-257.6, top deck 1.15, B y -0.35..1.3: three beds 0.933 wide (R. ABEL, T. ORME, M. DALE, left to
  right; the cards on the foot's middle rail at height 0.7). A ladder hooked on M. DALE's foot (x 257.28-257.54, B y
  -0.39; decor). Under them, the torch and three biscuits at x 255.86-256.35.
- Chair: seat centre x 260.6, B y 0.4, seat 0.4 x 0.4 (x 260.4-260.8), top 0.42; its back at x 260.755-260.795, to 0.98.
- Rail stub x 261.6-263.0, rails B y 0.47 / 0.63, top 0.03, channel 0.39-0.71; buffer stop at 261.6 (x 261.6-261.7,
  0.12 high). It runs on through a low opening in the end wall beside the door: B y 0.45-0.76, height 1.08 (iron
  framed). The door's hinge jamb stands above it (1.08-1.75).
- Wall things (all on the back wall, B y ~1.36-1.4): decoy pegs at x 251.02, 251.26, 251.5 (free), 251.74, 251.98,
  hook points (x, 0.80, game z -1.345), small gowns on all but 251.5; REST HOUR rules x 250.95-252.2, 1.25-2.2;
  the brake's plate x 252.13-252.47, 1.1-1.2; dial centre (253.0, 1.35); NIGHT-LIGHT plate under it; sun (253.9,
  2.55); eye centre (261.9, 2.25) on its board x 261.35-262.45, 1.2-2.65.
- Windows: W1 x 255.4-257.0, sill 1.6, head 3.1 (frosted wired glass, EMIT Att14aWellGlow, cold; its lower panes
  painted black up to 2.05, so the down blind (hem 1.93) covers all the light); W2 x 259.3-260.9, sill 1.9, head 3.1
  (reeded glass from 2.0, EMIT Att14aCorridorGlow, warm; a deep bottom rail 1.9-2.0 under the blind's hem). The glass is at B y 1.5. W1's roller on long iron brackets with
  struts (x 255.25, 257.25); the cord drum at x 257.12-257.2; W2's drum at 259.08-259.16, a pelmet over W2.
- The cord (static, in Att14aSet): up the crank's standard from its pulley (1.2) to two pulleys under the ceiling
  (3.37), across to W1's drum and W2's drum, and a return run between the drums.
- Arches to the back ward: x 249.75-250.85, 254.4-255.2, 257.25-258.55, crowns 2.85 (round heads). WARD 2 over the
  right one. The ward: x 248.15-259.0, B y 1.6-6.4: 16 made-up beds in two rows (feet at B y 2.15 and 4.55, x 248.9
  to 257.65 every 1.25), each with its locker; three tall night windows in its far wall (EMIT Att14aWardNight, dim).

STATIC OBJECTS: Att14aSet (the room; materials WinPlaster, WinDado, WinLino, PigeonWood, CrateWood, WornIron,
CastIron, HandledBrass, Brass, LeverRed, EyeDark, GaugeNeedle, the tannoy's TannoyEnamel/DepotSteel/DarkMetal/Cable,
and two images), Att14aGlobe (EMIT AttGlobeLamp, at B(251.3, 0.05, 3.1); two dead globes at 256.2 and 260.3 in the
set), Att14aWellGlow, Att14aCorridorGlow, Att14aWardNight (EMIT), Att14aWard (the ward's shell), Att14aWardBed01..16
(linked duplicates of one mesh 'Att14aWardBed', 780 tris, one material).

MATERIALS: images Att14aAtlas (textures/dl14a_atlas.png: bedding, gowns, lockers, swatches) and Att14aSigns
(textures/dl14a_signs.png: REST HOUR, the drive plate, the eye's board, the dial, the name cards, LIGHTS OUT, the
brake, NIGHT-LIGHT, LINEN, W1/W2, WARD 2, Mara's pencil tree), both pass through as maps. PLAIN EyeDark, Brass,
GaugeNeedle (existing). New EMIT entries: Att14aSunLamp: [1, .8, .42, 4], Att14aEyeSun: [1, .6, .18, 3],
Att14aEyeW1: [1, .6, .18, 0], Att14aEyeW2: [1, .6, .18, 0], Att14aEyeDark: [.36, 1, .46, 0],
Att14aWellGlow: [.72, .84, 1, 2.2], Att14aCorridorGlow: [1, .72, .4, 1.8], Att14aWardNight: [.4, .48, .66, .22].

SIGNS (textures): REST HOUR ("1. Lights out. 2. No talking. 3. Stay in your own bed. 4. Pupils are never
unaccompanied."); the drive plate by the crank (x 259.0-259.56, 0.42-0.91): only "ONE CORD - TWO BLINDS" (design review),
with a picture of two blinds W1 and W2 on one cord round to the crank; nothing about which way they move or the clutch; the eye's board ("LIGHT METER", the lamps' labels,
"DARK (REST HOUR)", "REST HOUR BEGINS WHEN THE ROOM IS DARK"); LIGHTS OUT on a flag sign over the doorway (both
faces, x 262.38-262.82, 1.86-1.99, at B y 0); REST HOUR BRAKE (OFF up / ON forward) over the lever.

LIGHTS (suggested, index.html P/S format, game coords):
P(0xffd8a8, 1.2, 4.0, 251.3, 2.95, -0.05)    the dim globe
P(0xffc070, 1.6, 3.5, 253.9, 2.5, -0.9)      the sun's glow (scale with the cycle; 0 when DARK)
S(0xc0d4ff, 3.5, 5, [256.2, 2.6, -1.3], [256.2, 0.9, 0.4], 0.7)   W1's cold light (when its blind is up)
S(0xffc890, 3.0, 5, [260.1, 2.6, -1.3], [260.1, 0.6, 0.4], 0.7)   W2's warm light (when its blind is up)
P(0x8094c0, 0.4, 5, 253.5, 2.8, -4.2)        the back ward, dim and cool
P(0xffd8b0, 0.6, 3.0, 261.8, 2.8, -0.3)      the eye and the door

TRIANGLES: ~40k in 37 objects (Att14aSet ~22k; ward beds 16 x 780, linked); about 60 material slots.
"""
