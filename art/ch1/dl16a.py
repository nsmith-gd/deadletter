"""Chapter 1 Attendance, DL-16a Her Way Round (game x 310.0 to 324.0). Design: docs/chapter1_expansion_proposal.md
(DL-16a); build sheet: docs/chapter1_expansion_build.md (DL-16a, Conventions).

The kitchen corridor behind the dismissal corridor: a two-storey school servery. On the left, in through DL-16's end
doorway, the kitchen: a dresser whose shelf runs out over the floor as a high pass shelf (a string-tied bundle of books
on it), the servery's hot cupboard under a band of crazed cream tiles, two catering tins on the floor, then the
dumbwaiter: an open iron shaft to the ceiling with a small tray car in it (open to the front), its counterweight hanging
behind at the top, and over the car's opening a brass load gauge (one amber window, the line, a red OVER; dressing now:
the director's playtest and docs/research/puzzle_design_2d.md section 5 cut the ballast puzzle, so this is her way
round, a ride). On the shaft's front-left post at child height, the call push: a round brass bell push under a small
bell pictogram, which calls the car down; the same push and pictogram inside the car send it up. Then the barred gate, PUPILS NOT PERMITTED BEYOND THIS POINT, with the lower corridor going on behind it under
an upper passage (floor 2.4) that runs from the top of the shaft over the gate to a stair down to the workshop's door.
At child height, in chalk: a crooked tree on the dresser, another on the hot cupboard, a third, an arrow to the car.
At the top, on the hatch frame where the car lets out onto the passage, a fourth tree and a small handprint.

Called by build_attendance.py as build_set(dl01, m, coll), in FINAL world coordinates (no SHIFT).
Blender (x, y, z) is the game's (x, z, -y): +y is away from the camera, z is up. The lane is y = 0, the floor z = 0.

What the game moves (origin = pivot, world coordinates; REPORT at the bottom has the numbers):
    Att16aCar      the dumbwaiter car; origin the middle of its floor's top (313.0, 0.1, 0.05); built at the bottom;
                   moves in z (+2.4 to floor top 2.45). Its lamp (EMIT Att16aCarLamp), bell push, brass plate, rope
                   and crosshead are in its mesh; the empty Att16aBellPush is its child.
    Att16aCW       its counterweight; origin bottom centre (313.0, 0.655, 3.0); built at the top; moves -2.4.
    Att16aTin1/2   catering tins; origin bottom centre (311.2, 0, 0) / (311.45, 0, 0); dressing now (no ballast).
    Att16aLoad1, Att16aLoadOver   the gauge's two lamps (own objects, own EMIT materials, built off); dressing now.
    Att16aBellPush (empty) at the bell push's face, parented to Att16aCar.
    Att16aCallPush the outside call push (brass rose and ivory button); origin the button's face (312.375, -0.46, 0.55).
Static: Att16aSet (the room; the call push's block and pictogram plate; the present-day service cable, NewCable /
NewSteel, and its relay box), Att16aBooks (set
dressing on the shelf), Att16aChalk (image material Chalk16a with alpha), Att16aLamps (EMIT AttBulbGlow),
Att16aRelayLamp (EMIT, the relay box's green pilot lamp, its own object).
"""
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
from build_d17 import add_box, add_cyl, add_sphere, add_torus, worn_material, simple_material, emission_material

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
I4 = Matrix.Identity(4)

# =====================================================================================================================
# Layout (Blender world; game x = x). Gameplay numbers from the build sheet are marked (*).
# =====================================================================================================================
X0, X1 = 310.0, 324.0                       # (*) DL-16's partition face .. DL-17's left wall face
WALL_Y, WALL_Y2 = 1.2, 1.35                 # (*) the back wall's face, and its back
FLOOR_FRONT, CEIL_FRONT = -1.6, -1.0        # as DL-16 and DL-17
CEIL = 3.9                                  # (*) the ceiling (a two-storey servery)
CEIL_T = 0.15
DADO = 1.0
L_DOOR = (-0.35, 0.45, 2.1)                 # DL-16's end doorway (y0, y1, head); its partition is 3.15 high
L_PART_TOP = 3.15
R_DOOR = (-0.45, 0.55, 2.1)                 # DL-17's doorway (dl17 DOORWAY); its left wall 324.0 .. 324.15, 3.0 high
R_WALL_TOP = 3.15                           # (DL-17's ceiling slab 3.0 .. 3.15 sits on it)

SHELF = (310.2, 310.9, 0.1, 0.6, 1.25)      # (*) the high pass shelf: x0, x1, y0, y1, top
SHELF_T = 0.035
DRESSER = (310.15, 310.95, 0.62, 2.45)      # the dresser it runs out from: x0, x1, front posts' y, top
BOOKS = (310.55, 0.35, 1.25)                # (*) Att16aBooks' origin
TINS = ((311.2, 0.0), (311.45, 0.0))        # (*) on the floor, y 0
TIN_R, TIN_H = 0.075, 0.17
COUNTER = (310.95, 312.42, 0.70, 0.9)       # the hot cupboard: x0, x1, door face y, top

CAR_IN = (312.6, 313.4)                     # (*) the car's inside
CAR_Y = (-0.4, 0.6)                         # (*) its depth
CAR_FLOOR = 0.05                            # (*) its floor's top at the bottom
CAR_TRAVEL = 2.4                            # (*) to 2.45 at the top
CAR_WALL = 0.03                             # its sides and back: outer x 312.57 .. 313.43
CAR_ROOF = 1.21                             # the roof's underside (clear inside 1.16 over the floor: D-17 is 1.12)
CAR_ORIGIN = (313.0, 0.1, 0.05)
BELL = (313.25, 0.6)                        # (*) the bell push: x, z (at the bottom), on the car's back wall
CALL_PUSH = (312.375, -0.46, 0.55)          # (*) Att16aCallPush: the outside call push's face, on the front-left post
CALL_N = (-0.6, -0.8, 0.0)                  # the way its face looks: to the camera, turned toward the lane's left
SHAFT = (312.5, 313.5, -0.45, 0.7)          # (*) the shaft's clear inside: x0, x1, y0, y1; posts outside it
POST = 0.08
HEAD_Z = 3.74                               # the shaft's head frame under the ceiling
HDR = (1.3, 1.5)                            # the lower landing's header across the shaft's front (the gauge on it)
GAUGE = (312.72, 313.28, 1.33, 1.47)        # the brass plate: x0, x1, z0, z1 (centre z 1.4)
LOAD_X = (312.88,)                          # Att16aLoad1 (one amber window: he and one tin)
OVER_X = 313.12                             # Att16aLoadOver (the line between them at 313.0)
LAMP_Z = 1.39
CW = (312.72, 313.28, 0.62, 0.69, 0.7)      # x0, x1, y0, y1, height
CW_ORIGIN = (313.0, 0.655, 3.0)             # bottom centre, at the top of the shaft
ROPE_LEN = 2.85                             # ropes run on up into the ceiling (a black trunk hides their ends)

GATE_X, GATE_Y, GATE_TOP = 314.0, (-0.45, 0.9), 2.3      # (*)
PASS = (313.5, 321.2, -0.3, 1.2, 2.4)       # (*) the upper passage: x0, x1, y0, y1, floor
DECK_T, JOIST = 0.04, 0.06                  # boards 2.36 .. 2.4 on iron joists 2.30 .. 2.36
HATCH = (313.5, 313.74, -0.45, -0.33, 3.62)  # the hatch frame's front jamb: x0, x1, y0, y1, head's underside
STAIR = (321.2, 323.6, -0.45, 0.6)          # (*)
TREADS, GOING, RISE = 12, 0.2, 0.2          # (*) tread i (1..12) at x 321.2 + 0.2 (i - 1) .. + 0.2 i, top 2.4 - 0.2 i
CHALK_TREES = (310.7, 311.6, 312.3)         # (*) at 0.4 .. 0.6
TREE4 = (313.6, 2.6, 2.9)                   # (*) the fourth tree and the handprint
PENDANT = (311.5, 0.3, 2.75)                # the kitchen's pendant bulb
PASS_LAMP = (317.4, 0.45, 3.5)              # the lamp over the upper passage
STAIR_LAMP = (322.75, WALL_Y - 0.08, 1.95)  # a bulkhead by the stair's foot, toward DL-17's door
CABLE_Z, CABLE_Y, CABLE_R = 3.70, WALL_Y - 0.03, 0.011   # the new service cable, just under the ceiling's beams
RELAY = (314.02, 314.26, 3.40, 3.62)        # its relay box on the passage's back wall: x0, x1, z0, z1
RELAY_LAMP = (314.2, 3.455)                 # the green pilot lamp on its front: x, z

# =====================================================================================================================
# Materials (names are the game's: index.html's WORN / PLAIN / EMIT tables)
# =====================================================================================================================
GAME_WORN = {   # copied from index.html's WORN table: fallbacks for a lone build (a full build already has them)
    'WinPlaster': dict(base=[.29, .27, .21], dirt=[.15, .13, .095], chip=[.2, .185, .15], rough=.9, chipRough=.85, metal=0, grime=3, chipScale=18, chipAmt=.7, dust=[.24, .22, .18], dustAmt=.5, streak=.6),
    'WinDado': dict(base=[.12, .16, .135], dirt=[.065, .075, .06], chip=[.30, .27, .21], rough=.55, chipRough=.85, metal=0, grime=4, chipScale=22, chipAmt=.68, dust=[.16, .17, .15], dustAmt=.4, streak=.5),
    'WinLino': dict(base=[.115, .085, .05], dirt=[.06, .045, .03], chip=[.075, .07, .062], rough=.7, chipRough=.9, metal=0, grime=3, chipScale=14, chipAmt=.66, dust=[.13, .12, .1], dustAmt=.6, streak=.3),
    'PigeonWood': dict(base=[.12, .085, .055], dirt=[.06, .045, .03], chip=[.2, .15, .1], rough=.85, chipRough=.8, metal=0, grime=6, chipScale=30, chipAmt=.75, dust=[.1, .09, .08], dustAmt=.6),
    'CrateWood': dict(base=[.18, .12, .07], dirt=[.08, .055, .035], chip=[.25, .19, .12], rough=.85, chipRough=.8, metal=0, grime=6, chipScale=30, chipAmt=.75, streak=.6),
    'WornIron': dict(base=[.045, .043, .04], dirt=[.06, .035, .02], chip=[.3, .29, .27], rough=.7, chipRough=.35, metal=.6, grime=9, chipScale=40, chipAmt=.6, dust=[.09, .085, .075], dustAmt=.4),
    'CastIron': dict(base=[.035, .034, .032], dirt=[.05, .03, .018], chip=[.13, .12, .1], rough=.75, chipRough=.45, metal=.5, grime=9, chipScale=50, chipAmt=.72, dust=[.08, .075, .065], dustAmt=.5),
    'HandledBrass': dict(base=[.2, .14, .06], dirt=[.08, .06, .03], chip=[.62, .46, .2], rough=.5, chipRough=.2, metal=.85, grime=8, chipScale=26, chipAmt=.5, dust=[.12, .1, .07], dustAmt=.2),
    'PupilWood': dict(base=[.36, .27, .17], dirt=[.17, .12, .08], chip=[.46, .38, .27], rough=.7, chipRough=.6, metal=0, grime=12, chipScale=40, chipAmt=.74, dust=[.3, .28, .24], dustAmt=.5),
    'SafetyYellow': dict(base=[.55, .42, .06], dirt=[.2, .16, .05], chip=[.07, .068, .062], rough=.8, chipRough=.9, metal=0, grime=4, chipScale=10, chipAmt=.55, dustAmt=.6),
    'DustyCream': dict(base=[.5, .46, .35], dirt=[.3, .26, .18], chip=[.03, .027, .022], rough=.85, chipRough=.55, metal=0, grime=4, chipScale=24, chipAmt=.64, dust=[.56, .54, .48], dustAmt=.95, streak=.4),
    'DarkMetal': dict(base=[.017, .016, .014], dirt=[.03, .024, .016], chip=[.075, .068, .055], rough=.72, chipRough=.45, metal=.25, grime=5, chipScale=34, chipAmt=.78, dust=[.075, .072, .062], dustAmt=.7),
}
GAME_PLAIN = {'Copper': ((.55, .3, .18), .35, 1.0),
              'NewCable': ((.016, .016, .018), .28, 0.0), 'NewSteel': ((.26, .27, .28), .4, .8)}   # pass 6's new line
GAME_EMIT = {'AttBulbGlow': ((1.0, 0.82, 0.58), 4.0)}
NEW_EMIT = {   # new: (colour, strength) as index.html EMIT; the gauge's lamps are built off (the game switches them)
    'Att16aCarLamp': ((1.0, 0.8, 0.52), 4.0),
    'Att16aLoad1': ((1.0, 0.62, 0.16), 0.0),
    'Att16aLoadOver': ((1.0, 0.12, 0.06), 0.0),
    'Att16aRelayLamp': ((0.35, 1.0, 0.45), 3.0),
}
ATLAS_PNG, CHALK_PNG = 'dl16a_atlas.png', 'dl16a_chalk.png'   # new image materials Att16aAtlas, Chalk16a (alpha)


def _worn_kw(g):
    return dict(base=tuple(g['base']), dirt=tuple(g['dirt']), chip=tuple(g['chip']), rough=g['rough'],
                chip_rough=g['chipRough'], metallic=g['metal'], dust=tuple(g.get('dust', (0.10, 0.095, 0.08))),
                grime_scale=g['grime'], chip_scale=g['chipScale'], chip_amount=g['chipAmt'],
                streaks=g.get('streak', 0.5), dust_amount=g.get('dustAmt', 0.6))


def _image_material(name, png, rough, alpha=False):
    mt, nt, bsdf = d17._new_material(name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(os.path.join(TEX, png), check_existing=True)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    if alpha:
        nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
        for attr, value in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
            if hasattr(mt, attr):
                try:
                    setattr(mt, attr, value)
                except (TypeError, ValueError):
                    pass
    return mt


def mat(name):
    mt = bpy.data.materials.get(name)
    if mt is not None:
        return mt
    if name in GAME_WORN:
        return worn_material(name, **_worn_kw(GAME_WORN[name]))
    if name in GAME_PLAIN:
        c, r, mtl = GAME_PLAIN[name]
        return simple_material(name, c, r, metallic=mtl)
    if name in GAME_EMIT:
        return emission_material(name, *GAME_EMIT[name])
    if name in NEW_EMIT:
        return emission_material(name, *NEW_EMIT[name])
    if name == 'Att16aAtlas':
        return _image_material(name, ATLAS_PNG, 0.8)
    if name == 'Chalk16a':
        return _image_material(name, CHALK_PNG, 0.95, alpha=True)
    raise KeyError(name)


# =====================================================================================================================
# Textures: an atlas of tiles, plates, signs and swatches (2048 x 1024), and the chalk (RGBA, 1024 x 512)
# =====================================================================================================================
TW, TH = 2048, 1024
CELLS = {
    'tiles': (0, 0, 1024, 640),          # the servery's splashback, 1.47 x 0.92 m
    'pupils': (1024, 0, 2048, 296),      # PUPILS NOT PERMITTED BEYOND THIS POINT, 0.76 x 0.22
    'menu': (1280, 296, 1792, 664),      # the dinners board, 0.70 x 0.50
    'staff': (1792, 296, 2048, 392),     # STAFF ONLY
    'gauge': (0, 640, 768, 832),         # TRAYS ONLY - LOAD TO THE LINE, 0.56 x 0.14
    'max3': (768, 640, 1280, 736),       # the car's plate (NO PASSENGERS), 0.32 x 0.06
    'tinlabel': (0, 832, 512, 960),      # the tins' paper label, wrapped
    'ring': (512, 832, 640, 896),        # RING (no longer used: the car's push has the bell pictogram too)
    'bellpict': (1408, 896, 1536, 992),  # the call push's plate: a bell, no words, 0.064 x 0.048
    'cwsign': (640, 832, 1024, 960),     # the counterweight's hazard plate
    'stair': (1024, 296, 1280, 392),     # STAFF STAIR, a small enamel
    'workshop': (1024, 392, 1280, 488),  # WORKSHOP, with an arrow down
}
SWATCH = {'sw_dark': (4, 4, 4), 'sw_chalk': (214, 210, 198), 'sw_glass': (60, 64, 62), 'sw_string': (184, 172, 140),
          'sw_black': (16, 14, 13), 'sw_ivory': (214, 200, 168), 'sw_paper': (196, 186, 160), 'sw_tin': (86, 92, 60),
          'sw_bk1': (112, 38, 32), 'sw_bk2': (38, 60, 96), 'sw_bk3': (54, 84, 54), 'sw_bk4': (140, 110, 60),
          'sw_bk5': (86, 50, 70), 'sw_steel': (120, 122, 120), 'sw_plate': (206, 202, 186), 'sw_enamel': (196, 190, 170),
          'sw_slate': (36, 40, 38), 'sw_red': (130, 36, 28), 'sw_rubber': (28, 26, 24), 'sw_green': (52, 82, 64)}
for _k, _n in enumerate(SWATCH):
    _c, _r = _k % 16, _k // 16
    CELLS[_n] = (1024 + 64 * _c, 832 + 64 * _r, 1088 + 64 * _c, 896 + 64 * _r)

CW_, CH_ = 1024, 512
CHALK = {'tree1': (0, 0, 256, 256), 'tree2': (256, 0, 512, 256), 'tree3': (512, 0, 768, 256), 'tree4': (768, 0, 1024, 256),
         'arrow': (0, 256, 512, 416), 'hand': (512, 256, 640, 384)}


def cell_uv(name):
    x0, y0, x1, y1 = CELLS[name]
    return x0 / TW, 1 - y1 / TH, x1 / TW, 1 - y0 / TH


def cell_mid(name):
    u0, v0, u1, v1 = cell_uv(name)
    return (u0 + u1) / 2, (v0 + v1) / 2


def chalk_uv(name):
    x0, y0, x1, y1 = CHALK[name]
    return x0 / CW_, 1 - y1 / CH_, x1 / CW_, 1 - y0 / CH_


def _font(size, kind='sans-bold'):
    from PIL import ImageFont
    paths = {'sans-bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
             'sans': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
             'carlito': '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf',
             'hand': '/usr/share/fonts/truetype/crosextra/Caladea-Italic.ttf'}
    try:
        return ImageFont.truetype(paths[kind], size)
    except OSError:
        return ImageFont.load_default()


def _fit(d, text, kind, size, width):
    """The largest font up to `size` whose text fits `width` pixels."""
    while size > 8:
        f = _font(size, kind)
        if d.textlength(text, font=f) <= width:
            return f
        size -= 2
    return _font(size, kind)


def _lerp(a, b, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def _noise(w, h, cells, seed):
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


def _fade(img, seed, grey=(140, 136, 124), k=0.12, warm=(1.0, 0.96, 0.88), dust=0.14):
    """Aged: dimmed toward grey, warmed, dusty (as DL-16's plates)."""
    import numpy as np
    from PIL import Image
    a = np.asarray(img.convert('RGB')).astype(float)
    a = a * (1 - k) + np.array(grey) * k
    a *= np.array(warm)
    n = _noise(a.shape[1], a.shape[0], 8, seed)
    a = a * (1 - dust * (n[..., None] - 0.5) * 2) + 16 * dust * (n[..., None] > 0.63)
    return Image.fromarray(np.clip(a, 0, 255).astype('uint8'), 'RGB')


def _screws(d, w, h, inset, r, col=(80, 64, 40), rust=None):
    for sx, sy in ((inset, inset), (w - inset, inset), (inset, h - inset), (w - inset, h - inset)):
        if rust:
            d.ellipse((sx - r * 2.2, sy - r * 1.6, sx + r * 2.2, sy + r * 3.4), fill=rust)
        d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=col)
        d.line((sx - r * 0.7, sy, sx + r * 0.7, sy), fill=(30, 26, 20), width=max(1, r // 3))


def _brass(w, h, rnd):
    """A worn brass plate: a vertical sheen, hand-polished brighter in the middle, darker at the edges."""
    import numpy as np
    from PIL import Image
    y = np.linspace(0, 1, h)[:, None]
    x = np.linspace(0, 1, w)[None, :]
    sheen = 0.82 + 0.18 * np.cos((y - 0.35) * 3.0) * np.cos((x - 0.5) * 1.6)
    n = _noise(w, h, 10, rnd.randint(0, 9999))
    base = np.array([176, 134, 62])[None, None, :] * (sheen * (0.88 + 0.24 * n))[..., None]
    return Image.fromarray(np.clip(base, 0, 255).astype('uint8'), 'RGB')


def make_atlas(path):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(16100)
    img = Image.new('RGB', (TW, TH), (60, 58, 54))
    ink = (34, 26, 16)

    def put(name, tile, k=0.12, dust=0.15):
        x0, y0 = CELLS[name][:2]
        img.paste(_fade(tile, sum(map(ord, name)), k=k, dust=dust), (x0, y0))

    # --- the splashback: 6-inch cream glazed tiles, a green border course on top, crazed, chipped, one missing ------
    x0, y0, x1, y1 = CELLS['tiles']
    w, h = x1 - x0, y1 - y0
    ppm = w / 1.47
    ts = 0.152 * ppm
    t = Image.new('RGB', (w, h), (70, 66, 58))                                   # the grout
    d = ImageDraw.Draw(t)
    rows = int(h / ts) + 1
    for r in range(rows):
        for c in range(int(w / ts) + 1):
            tx, ty = c * ts, h - (r + 1) * ts
            top = r == rows - 1 or ty < ts * 0.5
            col = (44, 76, 58) if top else _lerp((214, 206, 178), (196, 186, 156), rnd.random())
            if r == 0:
                col = _lerp(col, (120, 108, 82), 0.35)                            # grimed over the counter
            if (r, c) == (2, 7):
                d.rectangle((tx + 3, ty + 3, tx + ts - 3, ty + ts - 3), fill=(92, 84, 70))   # one missing: plaster
                for _ in range(30):
                    px, py = tx + rnd.uniform(6, ts - 6), ty + rnd.uniform(6, ts - 6)
                    d.point((px, py), fill=(70, 62, 50))
                continue
            d.rectangle((tx + 3, ty + 3, tx + ts - 3, ty + ts - 3), fill=col)
            d.line((tx + 6, ty + 7, tx + ts - 9, ty + 7), fill=_lerp(col, (255, 255, 240), 0.35), width=3)  # glaze edge
            for _ in range(rnd.randint(1, 4)):                                   # crazing
                px, py = tx + rnd.uniform(5, ts - 5), ty + rnd.uniform(5, ts - 5)
                pts = [(px, py)]
                for _ in range(rnd.randint(2, 5)):
                    px += rnd.uniform(-18, 18)
                    py += rnd.uniform(-18, 18)
                    pts.append((min(max(px, tx + 4), tx + ts - 4), min(max(py, ty + 4), ty + ts - 4)))
                d.line(pts, fill=_lerp(col, (90, 80, 60), 0.45), width=1)
            if rnd.random() < 0.12:                                              # a chipped corner
                cx_, cy_ = rnd.choice(((tx + 4, ty + 4), (tx + ts - 4, ty + 4), (tx + 4, ty + ts - 4), (tx + ts - 4, ty + ts - 4)))
                d.ellipse((cx_ - 9, cy_ - 7, cx_ + 9, cy_ + 7), fill=(104, 94, 76))
    cr = [(w * 0.62, h), (w * 0.64, h * 0.8), (w * 0.61, h * 0.62), (w * 0.66, h * 0.44)]  # a long crack
    d.line(cr, fill=(60, 52, 40), width=2)
    a = np.asarray(t).astype(float)                                              # grease and steam, darker low down
    yy = np.linspace(0, 1, h)[:, None, None]
    n = _noise(w, h, 6, 1611)[..., None]
    a = a * (0.72 + 0.28 * (1 - yy) ** 0.6) * (0.9 + 0.2 * n)
    put('tiles', Image.fromarray(np.clip(a, 0, 255).astype('uint8')), k=0.08, dust=0.12)

    # --- the gate's enamel sign -------------------------------------------------------------------------------------
    x0, y0, x1, y1 = CELLS['pupils']
    w, h = x1 - x0, y1 - y0
    t = Image.new('RGB', (w, h), (222, 216, 196))
    d = ImageDraw.Draw(t)
    red = (164, 36, 28)
    d.rectangle((8, 8, w - 9, h - 9), outline=red, width=16)
    d.rectangle((30, 30, w - 31, h - 31), outline=(40, 34, 30), width=3)
    d.text((w // 2, 108), 'PUPILS NOT PERMITTED', font=_fit(d, 'PUPILS NOT PERMITTED', 'sans-bold', 92, w - 110), fill=red, anchor='mm')
    d.text((w // 2, 206), 'BEYOND THIS POINT', font=_fit(d, 'BEYOND THIS POINT', 'sans-bold', 74, w - 220), fill=(30, 28, 26), anchor='mm')
    for _ in range(14):                                                          # chips, round the edge (knocked by trolleys)
        if rnd.random() < 0.5:
            cx_, cy_ = rnd.uniform(0, w), rnd.choice((rnd.uniform(2, 22), rnd.uniform(h - 22, h - 2)))
        else:
            cx_, cy_ = rnd.choice((rnd.uniform(2, 22), rnd.uniform(w - 22, w - 2))), rnd.uniform(0, h)
        r = rnd.uniform(3, 10)
        d.ellipse((cx_ - r, cy_ - r * 0.8, cx_ + r, cy_ + r * 0.8), fill=(36, 32, 28))
    for _ in range(3):                                                           # rust run from the screws
        sx_ = rnd.choice((20, w - 20))
        d.line((sx_, 28, sx_ + rnd.uniform(-3, 3), 28 + rnd.uniform(20, 50)), fill=(130, 84, 48), width=4)
    _screws(d, w, h, 20, 7, col=(70, 66, 60), rust=(140, 90, 50))
    put('pupils', t, k=0.1, dust=0.18)

    # --- the gauge's plate: engraved brass, one window, the line, OVER --------------------------------------------
    x0, y0, x1, y1 = CELLS['gauge']
    w, h = x1 - x0, y1 - y0
    t = _brass(w, h, rnd)
    d = ImageDraw.Draw(t)
    d.rectangle((3, 3, w - 4, h - 4), outline=(84, 60, 26), width=5)
    d.text((w // 2, 30), 'TRAYS ONLY - LOAD TO THE LINE', font=_fit(d, 'TRAYS ONLY - LOAD TO THE LINE', 'sans-bold', 40, w - 70), fill=ink, anchor='mm')
    px = lambda x: (x - GAUGE[0]) / (GAUGE[1] - GAUGE[0]) * w
    pz = lambda z: (GAUGE[3] - z) / (GAUGE[3] - GAUGE[2]) * h
    ly = pz(LAMP_Z)
    for k, x in enumerate(LOAD_X + (OVER_X,)):
        cx_ = px(x)
        d.ellipse((cx_ - 31, ly - 31, cx_ + 31, ly + 31), outline=(70, 50, 22), width=4)
        d.ellipse((cx_ - 25, ly - 25, cx_ + 25, ly + 25), fill=(24, 18, 12))
        over = k == len(LOAD_X)
        d.text((cx_, ly + 54), 'OVER' if over else 'LOAD', font=_font(28, 'sans-bold'), fill=(150, 30, 22) if over else ink, anchor='mm')
    lx = (px(LOAD_X[-1]) + px(OVER_X)) / 2                                       # the line, red, engraved deep
    d.rectangle((lx - 5, 50, lx + 5, h - 12), fill=(150, 30, 22))
    d.polygon([(lx - 16, 50), (lx + 16, 50), (lx, 64)], fill=(150, 30, 22))
    d.rectangle((px(OVER_X) - 52, ly - 40, px(OVER_X) + 52, ly + 70), outline=(150, 30, 22), width=3)
    _screws(d, w, h, 13, 6, col=(96, 72, 32))
    put('gauge', t, k=0.04, dust=0.08)

    # --- NO PASSENGERS (the car's plate), RING ----------------------------------------------------------------------------------------
    for name, text, size in (('max3', 'NO PASSENGERS', 54), ('ring', 'RING', 34)):
        x0, y0, x1, y1 = CELLS[name]
        w, h = x1 - x0, y1 - y0
        t = _brass(w, h, rnd)
        d = ImageDraw.Draw(t)
        d.rectangle((2, 2, w - 3, h - 3), outline=(84, 60, 26), width=4)
        d.text((w // 2, h // 2 + 1), text, font=_fit(d, text, 'sans-bold', size, w - (50 if name == 'max3' else 16)), fill=ink, anchor='mm')
        if name == 'max3':
            _screws(d, w, h, 12, 5, col=(96, 72, 32))
        put(name, t, k=0.04, dust=0.08)

    # --- the call push's plate: brass, a bell engraved and filled black, no words --------------------------------------
    x0, y0, x1, y1 = CELLS['bellpict']
    w, h = x1 - x0, y1 - y0
    t = _brass(w, h, rnd)
    d = ImageDraw.Draw(t)
    d.rectangle((2, 2, w - 3, h - 3), outline=(84, 60, 26), width=4)
    cx_, top_, bot_ = w // 2, 16, 70
    bell = [(cx_ - 6, top_ + 4), (cx_ + 6, top_ + 4)]
    for k in range(9):                                   # the bell's flank, flaring to its lip
        f = k / 8
        bell.append((cx_ + 9 + 18 * f ** 2.2, top_ + 6 + (bot_ - top_ - 6) * f))
    bell += [(cx_ + 30, bot_ + 2), (cx_ - 30, bot_ + 2)]
    for k in range(8, -1, -1):
        f = k / 8
        bell.append((cx_ - 9 - 18 * f ** 2.2, top_ + 6 + (bot_ - top_ - 6) * f))
    d.polygon(bell, fill=ink)
    d.ellipse((cx_ - 5, top_ - 4, cx_ + 5, top_ + 6), outline=ink, width=3)               # its crown loop
    d.ellipse((cx_ - 6, bot_ + 2, cx_ + 6, bot_ + 13), fill=ink)                         # the clapper
    for s_ in (-1, 1):                                                                   # it rings: two arcs each side
        for r_ in (40, 50):
            box = (cx_ - r_, top_ + 30 - r_ * 0.8, cx_ + r_, top_ + 30 + r_ * 0.8)
            d.arc(box, 160 if s_ < 0 else -20, 200 if s_ < 0 else 20, fill=ink, width=3)
    put('bellpict', t, k=0.04, dust=0.08)

    # --- the dinners board: slate, DINNERS signwritten, the chalk wiped to a haze --------------------------------------
    x0, y0, x1, y1 = CELLS['menu']
    w, h = x1 - x0, y1 - y0
    n = _noise(w, h, 7, 1620)
    a = np.ones((h, w, 3)) * np.array([38, 44, 41]) * (0.85 + 0.3 * n)[..., None]
    t = Image.fromarray(np.clip(a, 0, 255).astype('uint8'))
    d = ImageDraw.Draw(t, 'RGBA')
    d.text((w // 2, 44), 'DINNERS', font=_font(58, 'carlito'), fill=(218, 206, 170, 255), anchor='mm')
    d.line((60, 80, w - 60, 80), fill=(218, 206, 170, 200), width=3)
    for _ in range(18):                                                          # the wiped haze
        cx_, cy_ = rnd.uniform(30, w - 30), rnd.uniform(110, h - 30)
        d.ellipse((cx_ - 90, cy_ - 22, cx_ + 90, cy_ + 22), fill=(200, 200, 190, 14))
    for k, line in enumerate(('Mince, potatoes', 'Cabbage', 'Jam roly-poly', 'Custard')):
        d.text((48, 130 + k * 56), line, font=_font(40, 'hand'), fill=(210, 208, 196, 70 if k < 3 else 40))
    d.text((w - 60, h - 40), 'Thurs', font=_font(30, 'hand'), fill=(210, 208, 196, 120), anchor='rm')
    put('menu', t, k=0.04, dust=0.2)

    # --- STAFF ONLY, STAFF STAIR, WORKSHOP: small enamels -------------------------------------------------------------
    for name, text, bg, fg in (('staff', 'STAFF ONLY', (36, 52, 84), (222, 214, 190)),
                               ('stair', 'STAFF STAIR', (36, 52, 84), (222, 214, 190)),
                               ('workshop', 'WORKSHOP', (40, 64, 50), (214, 204, 176))):
        x0, y0, x1, y1 = CELLS[name]
        w, h = x1 - x0, y1 - y0
        t = Image.new('RGB', (w, h), bg)
        d = ImageDraw.Draw(t)
        d.rounded_rectangle((5, 5, w - 6, h - 6), radius=12, outline=fg, width=4)
        tw = w - 40 if name != 'workshop' else w - 80
        d.text((w // 2 - (14 if name == 'workshop' else 0), h // 2 + 1), text, font=_fit(d, text, 'carlito', 52, tw), fill=fg, anchor='mm')
        if name == 'workshop':                                                   # an arrow, down and on
            ax = w - 34
            d.line((ax, 24, ax, h - 28), fill=fg, width=7)
            d.polygon([(ax - 14, h - 34), (ax + 14, h - 34), (ax, h - 14)], fill=fg)
        for _ in range(6):
            cx_, cy_, r = rnd.uniform(0, w), rnd.choice((rnd.uniform(0, 12), rnd.uniform(h - 12, h))), rnd.uniform(2, 6)
            d.ellipse((cx_ - r, cy_ - r, cx_ + r, cy_ + r), fill=(30, 28, 26))
        put(name, t, k=0.1, dust=0.2)

    # --- the tins' label: SCHOOL MEALS SERVICE, RATIONS, a portion's worth -------------------------------------------
    x0, y0, x1, y1 = CELLS['tinlabel']
    w, h = x1 - x0, y1 - y0
    t = Image.new('RGB', (w, h), (196, 178, 130))
    d = ImageDraw.Draw(t)
    d.rectangle((0, 0, w, 16), fill=(120, 40, 32))
    d.rectangle((0, h - 16, w, h), fill=(120, 40, 32))
    d.text((w // 2, 40), 'SCHOOL MEALS SERVICE', font=_font(22, 'sans-bold'), fill=(60, 44, 30), anchor='mm')
    d.text((w // 2, 76), 'RATIONS', font=_font(40, 'sans-bold'), fill=(120, 40, 32), anchor='mm')
    d.text((w // 2, 104), 'CATERING PACK  ·  NET 3 KG', font=_font(16, 'sans'), fill=(60, 44, 30), anchor='mm')
    put('tinlabel', t, k=0.15, dust=0.3)

    # --- the counterweight's hazard plate ------------------------------------------------------------------------------
    x0, y0, x1, y1 = CELLS['cwsign']
    w, h = x1 - x0, y1 - y0
    t = Image.new('RGB', (w, h), (176, 140, 30))
    d = ImageDraw.Draw(t)
    for k in range(-4, 16):
        xx = k * 36
        d.polygon([(xx, 0), (xx + 18, 0), (xx - 2, 26), (xx - 20, 26)], fill=(24, 22, 20))
        d.polygon([(xx, h - 26), (xx + 18, h - 26), (xx - 2, h), (xx - 20, h)], fill=(24, 22, 20))
    d.rectangle((0, 26, w, h - 26), fill=(30, 28, 26))
    d.text((w // 2, h // 2), 'COUNTERWEIGHT', font=_fit(d, 'COUNTERWEIGHT', 'carlito', 52, w - 30), fill=(196, 160, 46), anchor='mm')
    put('cwsign', t, k=0.2, dust=0.35)

    d = ImageDraw.Draw(img)
    for name, rgb in SWATCH.items():
        x0, y0, x1, y1 = CELLS[name]
        d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=rgb)
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    q = img.quantize(255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q.save(path, optimize=True)


def make_chalk(path):
    """Her chalk, at child height: three crooked trees (her tree, as in DL-05 and DL-16's mural), an arrow; the fourth
    tree, smaller, and a small handprint pressed in chalk dust. White chalk with a dry, broken grain."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(16200)
    img = Image.new('RGBA', (CW_, CH_), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    col = (236, 234, 224, 255)

    def stroke(pts_, weight):
        for _ in range(2):
            q = [(px + rnd.uniform(-1.6, 1.6), py + rnd.uniform(-1.6, 1.6)) for px, py in pts_]
            d.line(q, fill=col, width=max(3, int(round(7 * (0.55 + weight * 0.55)))), joint='curve')

    sys.path.insert(0, os.path.join(HERE, '..', 'dl05'))
    try:
        import build_dl05 as dl05
        tree = dl05._crooked_tree
    except ImportError:                                                          # a lone build: a plain crooked tree
        def tree(stroke_, ox, oy, s, sx=None):
            stroke_([(ox, oy), (ox - 0.03 * s, oy - 0.4 * s), (ox + 0.04 * s, oy - 0.7 * s), (ox - 0.05 * s, oy - 0.93 * s)], 1.0)
            stroke_([(ox, oy - 0.45 * s), (ox - 0.3 * s, oy - 0.66 * s)], 0.7)
            stroke_([(ox, oy - 0.55 * s), (ox + 0.4 * s, oy - 0.75 * s)], 0.7)
    # three trees, each a little more hurried and leaning toward the car (+x); the fourth smaller, more careful
    for name, s, sx, lean in (('tree1', 208, 200, 0.0), ('tree2', 200, 214, 0.06), ('tree3', 196, 226, 0.12), ('tree4', 180, 176, 0.0)):
        x0, y0, x1, y1 = CHALK[name]
        ox, oy = x0 + 124, y1 - 18
        if lean:
            base = stroke

            def stroke(pts_, weight, base=base, ox=ox, oy=oy, lean=lean):
                base([(px + (oy - py) * lean, py) for px, py in pts_], weight)
        tree(stroke, ox, oy, s, sx)
        if lean:
            stroke = base
    # the arrow: drawn fast, a long wobbly shaft rising a little, the head redrawn
    x0, y0, x1, y1 = CHALK['arrow']
    pts = [(x0 + 24 + k * 22, y0 + 104 - 18 * math.sin(k / 19 * math.pi * 0.5) + rnd.uniform(-2, 2)) for k in range(20)]
    stroke(pts, 1.0)
    hx, hy = pts[-1]
    for _ in range(2):
        stroke([(hx - 52, hy - 40 + rnd.uniform(-4, 4)), (hx + 4, hy), (hx - 50, hy + 34 + rnd.uniform(-4, 4))], 1.0)
    # the handprint: a child's left hand, pressed flat in chalk dust (palm and five fingers), patchy
    x0, y0, x1, y1 = CHALK['hand']
    hd = Image.new('L', (x1 - x0, y1 - y0), 0)
    dh = ImageDraw.Draw(hd)
    dh.ellipse((34, 58, 96, 118), fill=210)
    for fx, fy, ang, ln in ((26, 70, -55, 32), (40, 46, -14, 40), (60, 40, 0, 46), (79, 44, 12, 42), (94, 56, 26, 32)):
        a_ = math.radians(ang)
        tx, ty = fx + ln * math.sin(a_), fy - ln * math.cos(a_)
        dh.line((fx, fy + 10, tx, ty), fill=210, width=13)
        dh.ellipse((tx - 6.5, ty - 6.5, tx + 6.5, ty + 6.5), fill=210)
    hd = hd.filter(ImageFilter.GaussianBlur(1.6))
    grain = (_noise(x1 - x0, y1 - y0, 14, 1630) * 255).astype('uint8')
    ha = (np.asarray(hd).astype(float) / 255.0) * np.clip((grain.astype(float) - 70) / 120, 0.15, 1.0)
    layer = np.zeros((y1 - y0, x1 - x0, 4), dtype='uint8')
    layer[..., :3] = (236, 234, 224)
    layer[..., 3] = np.clip(ha * 235, 0, 255).astype('uint8')
    img.alpha_composite(Image.fromarray(layer, 'RGBA'), (x0, y0))
    # chalk's grain: a dry, broken stroke
    a = np.asarray(img).astype(float)
    n1 = np.asarray(Image.fromarray((np.random.default_rng(1631).random((CH_, CW_)) * 255).astype('uint8')).filter(ImageFilter.GaussianBlur(0.7))).astype(float) / 255
    n2 = _noise(CW_, CH_, 40, 1632)
    a[..., 3] *= np.clip(0.35 + 1.1 * n1 * (0.6 + 0.6 * n2), 0, 1)
    out = Image.fromarray(np.clip(a, 0, 255).astype('uint8'), 'RGBA').filter(ImageFilter.GaussianBlur(0.6))
    o = np.array(out)
    o[..., 3] = np.where(o[..., 3] < 6, 0, o[..., 3])
    o[..., :3] = (236, 234, 224)                                                  # colour everywhere: clean edges when filtered
    Image.fromarray(o, 'RGBA').save(path, optimize=True)


# =====================================================================================================================
# Mesh building (as DL-16's MB)
# =====================================================================================================================
class MB:
    """One object being built: faces tagged by material name. Faces flagged 'flat' keep the winding they were built
    with (decals, one-sided in the game); the rest have their normals recalculated outward."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.flat = self.bm.faces.layers.int.new('flat')
        self.names = []

    def m(self, name):
        if name not in self.names:
            self.names.append(name)
        return self.names.index(name)

    def mark(self):
        self.bm.verts.ensure_lookup_table()
        return len(self.bm.verts)

    def since(self, n0):
        self.bm.verts.ensure_lookup_table()
        return self.bm.verts[n0:]

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

    def sbox(self, cell, x0, x1, y0, y1, z0, z1):
        return self.box('Att16aAtlas', x0, x1, y0, y1, z0, z1, cell=cell)

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

    def decal(self, mt, x0, x1, z0, z1, y, cell=None, uvr=None):
        """A picture facing the camera (-y)."""
        u0, v0, u1, v1 = uvr or cell_uv(cell)
        return self.face(mt, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    def prism_xz(self, mt, pts, y0, y1, cell=None):
        """A convex polygon in (x, z), extruded from y0 to y1."""
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

    def label_band(self, c, r, z0, z1, cell, seg=20, face_dir=-math.pi / 2):
        """A paper label round a cylinder about z (centre c = (x, y)), the cell's middle facing face_dir."""
        u0, v0, u1, v1 = cell_uv(cell)
        bm = self.bm
        ring0, ring1 = [], []
        for i in range(seg + 1):
            a = face_dir - math.pi + 2 * math.pi * i / seg
            p = (c[0] + r * math.cos(a), c[1] + r * math.sin(a))
            ring0.append(bm.verts.new((p[0], p[1], z0)))
            ring1.append(bm.verts.new((p[0], p[1], z1)))
        for i in range(seg):
            f = bm.faces.new((ring0[i], ring0[i + 1], ring1[i + 1], ring1[i]))
            f.material_index = self.m('Att16aAtlas')
            f[self.flat] = 1
            for lp, (uu, vv) in zip(f.loops, ((i, 0), (i + 1, 0), (i + 1, 1), (i, 1))):
                lp[self.uv].uv = (u0 + (u1 - u0) * uu / seg, v0 + (v1 - v0) * vv)
        # wound so its normals point outward: (i, i+1) runs counter-clockwise seen from above (left to right, seen from -y)

    def chain(self, mt, a, b, pitch=0.045, R=0.014, r=0.004):
        a, b = Vector(a), Vector(b)
        L = (b - a).length
        n = max(2, int(round(L / pitch)))
        t = (b - a).normalized()
        side = t.cross(Vector((0, 1, 0)))
        if side.length < 1e-3:
            side = t.cross(Vector((1, 0, 0)))
        side.normalize()
        up = t.cross(side).normalized()
        for i in range(n):
            p = a.lerp(b, (i + 0.5) / n)
            ax = side if i % 2 else up
            vs = add_torus(self.bm, (0, 0, 0), (0, 0, 1), R, r, mat=self.m(mt), seg=8, rseg=3)
            rot = Matrix((t, ax.cross(t), ax)).transposed().to_4x4()
            M = Matrix.Translation(p) @ rot @ Matrix.Diagonal((1.45, 1.0, 1.0, 1.0))
            for v in vs:
                v.co = M @ v.co

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


# =====================================================================================================================
# The room
# =====================================================================================================================
def stair_line(x):
    """The stair's pitch line through its nosings: 2.4 at 321.2, 0 at 323.6."""
    return PASS[4] - (x - STAIR[0]) * RISE / GOING


def tread(i):
    """Tread i (1..12): x0, x1, top."""
    a = STAIR[0] + (i - 1) * GOING
    return a, a + GOING, PASS[4] - RISE * i


def build_shell(B):
    sx0, sx1, sy0, sy1 = SHAFT
    # The back wall: plaster, floor to above the ceiling; dado, skirting and rails as overlays on it.
    B.box('WinPlaster', X0, X1, WALL_Y, WALL_Y2, 0.0, CEIL + CEIL_T)
    B.box('WinDado', X0, X1, WALL_Y - 0.01, WALL_Y, 0.0, DADO)
    B.box('PigeonWood', X0, X1, WALL_Y - 0.03, WALL_Y, DADO - 0.02, DADO + 0.03)
    B.box('PigeonWood', X0, X1, WALL_Y - 0.025, WALL_Y, 0.0, 0.12)
    # the passage's own dado, and its band following the stair's pitch down to the lower one
    ux0 = HATCH[1]
    B.box('WinDado', ux0, STAIR[0], WALL_Y - 0.012, WALL_Y, PASS[4], PASS[4] + 0.85)
    B.box('PigeonWood', ux0, STAIR[0], WALL_Y - 0.032, WALL_Y, PASS[4] + 0.83, PASS[4] + 0.88)
    B.box('PigeonWood', ux0, STAIR[0], WALL_Y - 0.026, WALL_Y, PASS[4], PASS[4] + 0.1)
    xa = STAIR[0] + (PASS[4] - DADO) * GOING / RISE                                   # where the pitch meets the dado
    xb = STAIR[0] + (PASS[4] + 0.85 - DADO) * GOING / RISE
    B.prism_xz('WinDado', [(STAIR[0], PASS[4]), (xa, DADO), (xb, DADO), (STAIR[0], PASS[4] + 0.85)], WALL_Y - 0.012, WALL_Y)
    xr = STAIR[0] + (PASS[4] + 0.83 - (DADO - 0.02)) * GOING / RISE                    # its rail, down to the lower rail
    B.prism_xz('PigeonWood', [(STAIR[0], PASS[4] + 0.83), (xr, DADO - 0.02), (xr, DADO + 0.03), (STAIR[0], PASS[4] + 0.88)],
               WALL_Y - 0.032, WALL_Y)
    # The floor: lino, the shaft's footprint an iron plate; the thresholds at both doorways.
    px0, px1, py0, py1 = sx0 - POST, sx1 + POST, sy0 - POST, sy1 + POST
    B.box('WinLino', X0, px0, FLOOR_FRONT, WALL_Y2, -0.2, 0.0)
    B.box('WinLino', px1, X1, FLOOR_FRONT, WALL_Y2, -0.2, 0.0)
    B.box('WinLino', px0, px1, FLOOR_FRONT, py0, -0.2, 0.0)
    B.box('WinLino', px0, px1, py1, WALL_Y2, -0.2, 0.0)
    B.box('WornIron', px0, px1, py0, py1, -0.2, 0.0)
    for x in (sx0 + 0.33, sx0 + 0.66):                                                # the plate's seams and bolts
        B.box('CastIron', x - 0.004, x + 0.004, py0, py1, -0.0005, 0.0005)
    for x in (px0 + 0.05, px1 - 0.05):
        for y in (py0 + 0.05, py1 - 0.05):
            B.cyl('CastIron', (x, y, 0.0), (x, y, 0.005), 0.012, seg=6)
    B.box('PigeonWood', X0, X0 + 0.04, L_DOOR[0] - 0.02, L_DOOR[1] + 0.02, -0.2, 0.004)    # meets DL-16's (0.004)
    B.box('WornIron', X1 - 0.04, X1, R_DOOR[0], R_DOOR[1], -0.2, 0.012)                 # meets DL-17's iron strip
    # The ceiling: one slab, beams across it (clear of the shaft's head), the walls above the neighbours' tops.
    B.box('WinPlaster', X0, X1, CEIL_FRONT, WALL_Y2, CEIL, CEIL + CEIL_T)
    for x in (311.2, 315.4, 317.8, 320.2, 322.6):
        B.box('PigeonWood', x - 0.07, x + 0.07, CEIL_FRONT, WALL_Y, CEIL - 0.16, CEIL)
    B.box('PigeonWood', X0, X1, WALL_Y - 0.1, WALL_Y, CEIL - 0.12, CEIL)                # the wall plate
    B.box('WinPlaster', X0, X0 + 0.15, CEIL_FRONT, WALL_Y2, L_PART_TOP, CEIL)            # over DL-16's partition
    B.box('WinPlaster', X1, X1 + 0.15, CEIL_FRONT, WALL_Y2, R_WALL_TOP, CEIL + CEIL_T)   # over DL-17's wall
    # The doorways' architraves on this side (each neighbour has its own on its side).
    y0, y1, hd = L_DOOR
    B.box('PigeonWood', X0, X0 + 0.025, y1, y1 + 0.07, 0.0, hd + 0.07)
    B.box('PigeonWood', X0, X0 + 0.025, y0, y1 + 0.07, hd, hd + 0.07)
    y0, y1, hd = R_DOOR
    for a, b, c, d in ((y1, y1 + 0.07, 0.0, hd + 0.07), (y0 - 0.07, y0, 0.0, hd + 0.07), (y0 - 0.07, y1 + 0.07, hd, hd + 0.07)):
        B.box('PigeonWood', X1 - 0.025, X1, a, b, c, d)
    # The black trunk above the ceiling the ropes run up into (lost in the dark, as DL-16's slot).
    tx0, tx1, ty0, ty1 = 312.8, 313.2, 0.38, 0.8
    z0, z1 = CEIL + CEIL_T, CEIL + 2.75
    for a, b, c, d in ((tx0 - 0.02, tx0, ty0, ty1), (tx1, tx1 + 0.02, ty0, ty1), (tx0, tx1, ty0 - 0.02, ty0), (tx0, tx1, ty1, ty1 + 0.02)):
        B.sbox('sw_dark', a, b, c, d, z0, z1)
    B.sbox('sw_dark', tx0 - 0.02, tx1 + 0.02, ty0 - 0.02, ty1 + 0.02, z1, z1 + 0.02)


def build_kitchen(B, rnd):
    """The dresser with its pass shelf, the hot cupboard and splashback, the dinners board."""
    x0, x1, y0, y1, top = SHELF
    dx0, dx1, fy, dtop = DRESSER
    wy = WALL_Y
    # The dresser: four uprights, a cupboard below (door face y 0.66), plate shelves above, a cornice.
    for ux in (dx0 + 0.03, dx1 - 0.03):
        B.box('PigeonWood', ux - 0.03, ux + 0.03, fy, fy + 0.06, 0.0, dtop)
        B.box('PigeonWood', ux - 0.03, ux + 0.03, wy - 0.06, wy, 0.0, dtop)
        B.box('PigeonWood', ux - 0.025, ux + 0.025, fy + 0.06, wy - 0.06, dtop - 0.08, dtop - 0.02)
    B.box('PigeonWood', dx0, dx1, fy - 0.01, wy, dtop, dtop + 0.05)
    B.box('PigeonWood', dx0 - 0.02, dx1 + 0.02, fy - 0.03, wy, dtop + 0.05, dtop + 0.09)
    B.box('PigeonWood', dx0 + 0.06, dx1 - 0.06, wy - 0.025, wy, 0.88, dtop)               # its back boards
    for k in range(1, 6):
        xx = dx0 + 0.06 + k * (dx1 - dx0 - 0.12) / 6
        B.box('Att16aAtlas', xx - 0.002, xx + 0.002, wy - 0.026, wy - 0.025, 0.88, dtop, cell='sw_dark')
    cx0, cx1 = dx0 + 0.06, dx1 - 0.06
    B.box('PigeonWood', cx0, cx1, fy + 0.02, wy - 0.02, 0.0, 0.85)                        # the cupboard
    B.box('WinDado', cx0 + 0.01, (cx0 + cx1) / 2 - 0.004, fy - 0.0, fy + 0.02, 0.06, 0.82)  # its doors, painted green
    B.box('WinDado', (cx0 + cx1) / 2 + 0.004, cx1 - 0.01, fy - 0.0, fy + 0.02, 0.06, 0.82)
    for xx in ((cx0 + cx1) / 2 - 0.04, (cx0 + cx1) / 2 + 0.04):
        B.cyl('HandledBrass', (xx, fy, 0.66), (xx, fy - 0.02, 0.66), 0.012, seg=8)
    B.box('PigeonWood', dx0, dx1, fy - 0.02, wy, 0.85, 0.88)                              # the worktop
    # The shelf at 1.25: the dresser's own (behind) and the pass shelf running out from it over the floor to y 0.1.
    B.box('PigeonWood', dx0, dx1, y1, wy, top - SHELF_T, top)
    B.box('CrateWood', x0, x1, y0, y1, top - SHELF_T, top)
    B.box('CrateWood', x0, x1, y0 - 0.01, y0 + 0.012, top - 0.07, top + 0.012)           # a lip on its front edge
    for xx in (x0 + 0.02, x1 - 0.02):
        B.box('CastIron', xx - 0.012, xx + 0.012, y0 + 0.03, fy + 0.05, top - SHELF_T - 0.035, top - SHELF_T)   # the iron bearers
        B.cyl('WornIron', (xx, y0 + 0.03, top - 0.01), (xx, fy + 0.03, dtop - 0.1), 0.008, seg=6)              # tie rods up and back
        B.cyl('WornIron', (xx, y0 + 0.03, top - SHELF_T - 0.035), (xx, y0 + 0.03, top + 0.02), 0.014, seg=8)   # the rods' eyes
        B.box('CastIron', xx - 0.02, xx + 0.02, fy + 0.01, fy + 0.07, dtop - 0.14, dtop - 0.06)
    # plates on the dresser's racks (on edge), bowls, a jug
    for z in (1.7, 2.12):
        B.box('PigeonWood', dx0 + 0.06, dx1 - 0.06, fy + 0.25, wy, z - 0.03, z)
        B.box('PigeonWood', dx0 + 0.06, dx1 - 0.06, fy + 0.25, fy + 0.28, z, z + 0.06)
        n = 6
        for k in range(n):
            px = dx0 + 0.13 + k * (dx1 - dx0 - 0.26) / (n - 1)
            B.cyl('Att16aAtlas', (px - 0.006, fy + 0.36 + 0.03 * (k % 2), z + 0.12), (px + 0.006, fy + 0.36 + 0.03 * (k % 2), z + 0.12),
                  0.11, seg=14, cell='sw_plate')
    for k in range(3):                                                                    # bowls stacked on the worktop shelf
        B.cyl('Att16aAtlas', (dx0 + 0.2, 0.95, 1.25 + k * 0.04), (dx0 + 0.2, 0.95, 1.29 + k * 0.04), 0.07 + 0.005 * k, 0.09 + 0.005 * k, seg=14, cell='sw_plate')
    B.cyl('Att16aAtlas', (dx1 - 0.2, 0.95, 1.25), (dx1 - 0.2, 0.95, 1.42), 0.07, 0.06, seg=12, cell='sw_enamel')
    B.cyl('Att16aAtlas', (dx1 - 0.2, 0.95, 1.42), (dx1 - 0.2, 0.95, 1.46), 0.06, 0.068, seg=12, cell='sw_enamel')
    # The hot cupboard: dark steel, two doors, a worktop; on it a tea urn, a stack of trays, plates.
    hx0, hx1, hy, htop = COUNTER
    B.box('DarkMetal', hx0, hx1, hy + 0.02, wy, 0.08, htop - 0.04)
    B.box('CastIron', hx0 + 0.03, hx1 - 0.03, hy + 0.06, wy, 0.0, 0.08)                   # the plinth, set back
    mid = (hx0 + hx1) / 2
    for a, b in ((hx0 + 0.02, mid - 0.006), (mid + 0.006, hx1 - 0.02)):
        B.box('DarkMetal', a, b, hy, hy + 0.02, 0.1, htop - 0.08)
        B.box('HandledBrass', (a + b) / 2 - 0.08, (a + b) / 2 + 0.08, hy - 0.025, hy - 0.012, 0.78, 0.795)
        for xx in ((a + b) / 2 - 0.07, (a + b) / 2 + 0.07):
            B.box('HandledBrass', xx - 0.006, xx + 0.006, hy - 0.025, hy, 0.775, 0.8)
        for zz in (0.18, 0.7):                                                            # its vents
            B.sbox('sw_black', (a + b) / 2 - 0.12, (a + b) / 2 + 0.12, hy - 0.001, hy, zz, zz + 0.015)
    B.box('WornIron', hx0 - 0.01, hx1, hy - 0.03, wy, htop - 0.04, htop)                  # the worktop, steel
    B.box('WornIron', hx0 - 0.01, hx1, wy - 0.02, wy, htop, htop + 0.08)                  # its upstand
    ux, uy = 311.2, 0.98                                                                   # the tea urn
    B.cyl('DustyCream', (ux, uy, htop), (ux, uy, htop + 0.42), 0.15, seg=18)
    B.cyl('DustyCream', (ux, uy, htop + 0.42), (ux, uy, htop + 0.47), 0.15, 0.1, seg=18)
    B.cyl('HandledBrass', (ux, uy, htop + 0.47), (ux, uy, htop + 0.52), 0.02, seg=8)
    B.cyl('HandledBrass', (ux, uy - 0.14, htop + 0.12), (ux, uy - 0.2, htop + 0.12), 0.015, seg=8)
    B.cyl('HandledBrass', (ux, uy - 0.2, htop + 0.12), (ux, uy - 0.2, htop + 0.08), 0.013, seg=8)
    B.box('HandledBrass', ux - 0.035, ux + 0.035, uy - 0.215, uy - 0.185, htop + 0.14, htop + 0.16)
    for side in (-1, 1):
        B.torus('WornIron', (ux + side * 0.155, uy, htop + 0.33), (1, 0, 0), 0.035, 0.007, seg=10, rseg=4)
    for k in range(9):                                                                     # a stack of trays
        z = htop + 0.012 * k
        B.box('Att16aAtlas', 311.62 + 0.004 * (k % 3), 312.02 + 0.004 * (k % 3), 0.82, 1.14, z, z + 0.01, cell='sw_steel')
    for k in range(7):                                                                     # plates
        B.cyl('Att16aAtlas', (312.22, 0.98, htop + 0.014 * k), (312.22, 0.98, htop + 0.014 * (k + 1) - 0.002), 0.11, 0.12, seg=16, cell='sw_plate')
    # The splashback (crazed tiles), a plate shelf over it; the dinners board above.
    B.decal('Att16aAtlas', hx0, hx1, htop + 0.08, htop + 0.08 + 0.92, wy - 0.003, cell='tiles')
    B.box('PigeonWood', hx0, hx1, wy - 0.16, wy, 1.92, 1.95)
    for xx in (hx0 + 0.1, hx1 - 0.1):
        B.prism_xz('CastIron', [(xx - 0.01, 1.92), (xx + 0.01, 1.92), (xx + 0.01, 1.78)], wy - 0.15, wy - 0.13)
    for k in range(5):
        px = hx0 + 0.2 + k * 0.26
        B.cyl('Att16aAtlas', (px, 1.11, 1.95), (px, 1.11, 2.08 + 0.02 * (k % 2)), 0.04, 0.045, seg=10, cell='sw_enamel')
    mx0, mx1, mz0, mz1 = 311.1, 311.8, 2.2, 2.7
    B.box('PigeonWood', mx0 - 0.04, mx1 + 0.04, wy - 0.03, wy, mz0 - 0.04, mz1 + 0.04)
    B.decal('Att16aAtlas', mx0, mx1, mz0, mz1, wy - 0.031, cell='menu')
    B.box('PigeonWood', mx0, mx1, wy - 0.06, wy - 0.03, mz0 - 0.05, mz0 - 0.02)           # its chalk ledge
    # A kitchen clock high on the wall, stopped.
    cx, cz = 312.0, 3.05
    B.cyl('PigeonWood', (cx, wy, cz), (cx, wy - 0.05, cz), 0.17, seg=24)
    B.cyl('Att16aAtlas', (cx, wy - 0.05, cz), (cx, wy - 0.052, cz), 0.145, seg=24, cell='sw_ivory')
    for k in range(12):
        a = k * math.pi / 6
        B.box('Att16aAtlas', cx + 0.125 * math.sin(a) - 0.005, cx + 0.125 * math.sin(a) + 0.005, wy - 0.054, wy - 0.052,
              cz + 0.125 * math.cos(a) - 0.012, cz + 0.125 * math.cos(a) + 0.012, cell='sw_black')
    for ang, ln in ((math.radians(100), 0.07), (math.radians(-28), 0.11)):              # ten past three... it stopped
        tip = (cx + ln * math.sin(ang), cz + ln * math.cos(ang))
        B.prism_xz('Att16aAtlas', [(cx - 0.006 * math.cos(ang), cz + 0.006 * math.sin(ang)), (tip[0], tip[1]),
                                   (cx + 0.006 * math.cos(ang), cz - 0.006 * math.sin(ang))], wy - 0.058, wy - 0.055, cell='sw_black')
    # The kitchen's pendant: an enamel shade on a cord (the bulb is in Att16aLamps).
    x, y, z = PENDANT
    B.cyl('Att16aAtlas', (x, y, CEIL), (x, y, z + 0.1), 0.004, seg=5, cell='sw_black')
    B.cyl('WornIron', (x, y, CEIL), (x, y, CEIL - 0.03), 0.04, seg=10)
    B.cyl('WornIron', (x, y, z + 0.1), (x, y, z + 0.06), 0.02, seg=8)
    B.cyl('DustyCream', (x, y, z + 0.09), (x, y, z - 0.03), 0.04, 0.2, seg=18)
    B.cyl('Att16aAtlas', (x, y, z + 0.07), (x, y, z - 0.025), 0.035, 0.19, seg=18, cell='sw_enamel')


def build_shaft(B):
    """The dumbwaiter's shaft: iron corner posts, the lower landing's header with the gauge, the upper sill, the head
    frame, the car's guide rails at its back corners, the counterweight's guides and buffers, boarding at the back;
    the hatch frame where the car lets out onto the upper passage; the shaft's plates."""
    sx0, sx1, sy0, sy1 = SHAFT
    p = POST
    fy0, fy1 = sy0 - p, sy0                    # the front posts' y
    by0, by1 = sy1, sy1 + p                    # the back posts'
    top = CEIL + 0.02                          # into the ceiling slab
    B.box('WornIron', sx0 - p, sx0, fy0, fy1, 0.0, top)                                   # front left, full height
    B.box('WornIron', sx1, sx1 + p, fy0, fy1, 0.0, PASS[4] - 0.05)                        # front right, into the sill
    for x0, x1 in ((sx0 - p, sx0), (sx1, sx1 + p)):
        B.box('WornIron', x0, x1, by0, by1, 0.0, top)                                     # the back posts
        B.box('CastIron', x0 - 0.02, x1 + 0.02, fy0 - 0.02, fy1 + 0.02, 0.0, 0.02)
        B.box('CastIron', x0 - 0.02, x1 + 0.02, by0 - 0.02, by1 + 0.02, 0.0, 0.02)
    # the lower landing's header (the gauge is on it), the upper sill, the head frame: proud of the posts
    hy0, hy1, ex = fy0 - 0.012, fy1 - 0.004, 0.01
    B.box('WornIron', sx0 - p - ex, sx1 + p + ex, hy0, hy1, HDR[0], HDR[1])
    B.box('SafetyYellow', sx0 - p - ex, sx1 + p + ex, hy0 - 0.002, hy0 + 0.01, HDR[0], HDR[0] + 0.025)
    B.box('WornIron', sx0 - p - ex, sx1 + p + ex, hy0, hy1, PASS[4] - 0.1, PASS[4])
    B.box('SafetyYellow', sx0 - p - ex, sx1 + p + ex, hy0 - 0.002, hy0 + 0.01, PASS[4] - 0.1, PASS[4] - 0.075)
    B.box('CastIron', sx0 - p - ex, sx1 + p + ex, hy0, hy1, HEAD_Z, top)
    B.box('CastIron', sx0 - p - ex, sx1 + p + ex, by0 + 0.004, by1 + 0.012, HEAD_Z, top)
    for x0, x1 in ((sx0 - p + 0.005, sx0 - 0.005), (sx1 + 0.005, sx1 + p - 0.005)):
        B.box('CastIron', x0, x1, hy1, by0 + 0.004, HEAD_Z, top)
    B.box('CastIron', sx0 + 0.01, sx1 - 0.01, 0.36, 0.76, HEAD_Z + 0.06, top)              # the head's cross beam, ropes through
    for x in (sx0 - p / 2, sx1 + p / 2):                                                   # rivets on the posts' fronts
        for z in (0.1, 0.7, 1.9, 2.9, 3.4):
            if z > PASS[4] and x > sx1:
                continue
            B.cyl('CastIron', (x, fy0, z), (x, fy0 - 0.008, z), 0.01, seg=6)
    # the car's guide rails (T-section) at its back corners; the counterweight's guides and buffers behind
    for x0, x1 in ((sx0, sx0 + 0.04), (sx1 - 0.04, sx1)):
        B.box('WornIron', x0, x1, 0.47, 0.53, 0.0, HEAD_Z)
        for z in (0.6, 1.6, 2.6, 3.4):                                                     # its brackets to the boarding
            B.box('CastIron', x0 + 0.004, x1 - 0.004, 0.53, sy1 + 0.02, z, z + 0.05)
    cx0, cx1, cy0, cy1, _h = CW
    for gx0, gx1 in ((cx0 - 0.05, cx0 - 0.01), (cx1 + 0.01, cx1 + 0.05)):
        B.box('WornIron', gx0, gx1, cy0, sy1 + 0.02, 0.0, HEAD_Z)
        B.box('WornIron', (gx0 + gx1) / 2 - 0.006, (gx0 + gx1) / 2 + 0.006, cy0 - 0.02, cy0, 0.0, HEAD_Z)
    for bx in (312.85, 313.15):                                                            # the counterweight's spring buffers
        B.cyl('CastIron', (bx, CW_ORIGIN[1], 0.0), (bx, CW_ORIGIN[1], 0.04), 0.035, seg=10)
        for k in range(6):
            B.torus('WornIron', (bx, CW_ORIGIN[1], 0.06 + k * 0.035), (0, 0, 1), 0.022, 0.005, seg=10, rseg=3)
        B.cyl('CastIron', (bx, CW_ORIGIN[1], 0.25), (bx, CW_ORIGIN[1], 0.27), 0.03, seg=10)
    # the shaft's back: vertical boards, a seam line between each
    B.box('CrateWood', sx0, sx1, sy1 + 0.02, sy1 + 0.045, 0.0, HEAD_Z)
    k = 0
    x = sx0 + 0.125
    while x < sx1 - 0.05:
        B.sbox('sw_dark', x - 0.003, x + 0.003, sy1 + 0.019, sy1 + 0.02, 0.0, HEAD_Z)
        x += 0.125
        k += 1
    # The hatch frame at the top: a timber jamb at the front, a lintel across, a partition behind the shaft; brass
    # number plate on the lintel. The fourth tree is on the jamb (Att16aChalk).
    hx0, hx1, hy0, hy1, hz = HATCH
    B.box('PigeonWood', hx0, hx1, hy0, hy1, PASS[4], hz)
    B.box('WornIron', hx0, hx1, hy0, PASS[2], PASS[4] - 0.1, PASS[4])                      # its foot, on the shaft's sill
    B.box('PigeonWood', hx0, hx1, hy0, by1, hz, HEAD_Z + 0.03)
    B.box('PigeonWood', hx0, hx1, hy0, PASS[3], HEAD_Z + 0.03, CEIL + 0.02)
    B.box('WinPlaster', hx0 + 0.02, hx1, by1, PASS[3], PASS[4], HEAD_Z + 0.03)
    B.box('PigeonWood', hx0 - 0.015, hx1 + 0.015, hy0 - 0.015, hy0, hz - 0.03, hz)        # the lintel's moulding


def build_gauge(B, coll):
    """The load gauge's plate on the lower landing's header (z 1.4): brass, engraved TRAYS ONLY - LOAD TO THE LINE;
    one amber window (LOAD), the line, a red OVER window. The two lenses are their own objects (Att16aLoad1,
    Att16aLoadOver), in brass bezels; behind each window a dark socket in the plate."""
    gx0, gx1, gz0, gz1 = GAUGE
    fy = SHAFT[2] - POST - 0.012                                                           # the header's front face
    B.box('HandledBrass', gx0 - 0.008, gx1 + 0.008, fy - 0.014, fy, gz0 - 0.008, gz1 + 0.008)
    B.decal('Att16aAtlas', gx0, gx1, gz0, gz1, fy - 0.0145, cell='gauge')
    out = []
    for name, x in (('Att16aLoad1', LOAD_X[0]), ('Att16aLoadOver', OVER_X)):
        B.torus('HandledBrass', (x, fy - 0.016, LAMP_Z), (0, 1, 0), 0.024, 0.005, seg=16, rseg=4)
        L = MB()
        c = (x, fy - 0.017, LAMP_Z)
        L.sphere(name, c, 0.02, seg=14, scale=(1, 0.45, 1))
        out.append(L.obj(name, coll, origin=c))
    return out


def build_gate(B):
    """The gate at 314.0, under the passage: an iron frame, round bars, floor to 2.3, across y -0.45 .. 0.9 (a fixed
    post to the wall behind); padlocked; the enamel sign on its front, facing the corridor."""
    x = GATE_X
    y0, y1 = GATE_Y
    t = 0.03
    B.box('WornIron', x - t, x + t, y0, y0 + 0.05, 0.0, GATE_TOP)                          # the stiles
    B.box('WornIron', x - t, x + t, y1 - 0.05, y1, 0.0, GATE_TOP)
    for z0, z1 in ((0.04, 0.09), (1.08, 1.13), (GATE_TOP - 0.06, GATE_TOP)):
        B.box('WornIron', x - 0.02, x + 0.02, y0 + 0.05, y1 - 0.05, z0, z1)
    y = y0 + 0.11
    while y < y1 - 0.06:
        B.cyl('WornIron', (x, y, 0.09), (x, y, GATE_TOP - 0.06), 0.011, seg=6)
        y += 0.105
    B.box('WornIron', x - 0.035, x + 0.035, y1, WALL_Y, 0.0, GATE_TOP)                      # the fixed post to the wall
    for z in (0.3, 1.9):                                                                   # hinges on the back stile
        B.cyl('CastIron', (x, y1 + 0.01, z - 0.06), (x, y1 + 0.01, z + 0.06), 0.022, seg=8)
    B.cyl('CastIron', (x - 0.05, y0 - 0.03, 0.0), (x - 0.05, y0 - 0.03, 0.12), 0.012, seg=6)  # a drop bolt into the floor
    # the padlock and its chain round the front stile and the passage's corner post
    lx, lz = x - 0.05, 1.0
    B.chain('WornIron', (x - 0.04, y0 - 0.01, 1.06), (x - 0.04, y0 - 0.01, 1.18))
    B.box('HandledBrass', lx - 0.03, lx + 0.03, y0 - 0.04, y0 - 0.02, lz - 0.04, lz + 0.03)
    B.torus('WornIron', (lx, y0 - 0.03, lz + 0.045), (0, 1, 0), 0.02, 0.005, seg=10, rseg=3)
    B.sbox('sw_black', lx - 0.004, lx + 0.004, y0 - 0.041, y0 - 0.04, lz - 0.02, lz)
    # the sign, on two straps wired to the bars, facing the camera
    sx0, sx1, sz0, sz1 = 313.62, 314.38, 1.5, 1.72
    sy = y0 - 0.04
    B.box('WornIron', sx0 - 0.01, sx1 + 0.01, sy - 0.012, sy, sz0 - 0.01, sz1 + 0.01)
    B.decal('Att16aAtlas', sx0, sx1, sz0, sz1, sy - 0.0125, cell='pupils')
    for zz in (sz0 + 0.04, sz1 - 0.06):                                                    # its straps to the front stile
        B.box('WornIron', x - 0.035, x + 0.035, sy, y0 + 0.01, zz, zz + 0.025)


def build_passage(B):
    """The upper passage over the gate: timber boards on iron joists, a channel along its front with a railing, a
    cast-iron column at mid-span, bearers on the back wall; at its right end, the stair down."""
    x0, x1, y0, y1, fl = PASS
    B.box('CrateWood', x0, x1, y0, y1, fl - DECK_T, fl)
    yy = y0 + 0.14                                                                         # board joints along x
    while yy < y1 - 0.05:
        B.sbox('sw_dark', x0, x1, yy - 0.002, yy + 0.002, fl, fl + 0.0005)
        yy += 0.14
    B.box('WornIron', x0, x1, y0 - 0.005, y0 + 0.03, fl - DECK_T - JOIST, fl + 0.01)        # the front channel
    B.box('WornIron', x0, x1, y0 + 0.03, y0 + 0.08, fl - DECK_T - JOIST - 0.008, fl - DECK_T - JOIST + 0.004)
    B.box('WornIron', x0 + 0.24, x1, y1 - 0.06, y1, fl - DECK_T - JOIST - 0.04, fl - DECK_T)  # bearer on the wall
    xs = [GATE_X] + [x0 + 1.0 + 0.95 * k for k in range(1, 9) if x0 + 1.0 + 0.95 * k < x1 - 0.1]
    for xx in xs:                                                                          # the joists across
        B.box('WornIron', xx - 0.03, xx + 0.03, y0 + 0.03, y1 - 0.06, fl - DECK_T - JOIST, fl - DECK_T)
        B.box('WornIron', xx - 0.04, xx + 0.04, y0 + 0.03, y1 - 0.06, fl - DECK_T - JOIST - 0.004, fl - DECK_T - JOIST + 0.01)
    # the column at mid-span, just inside the front edge
    cx, cy = 317.6, y0 + 0.04
    B.cyl('CastIron', (cx, cy, 0.0), (cx, cy, 0.06), 0.08, 0.07, seg=12)
    B.cyl('CastIron', (cx, cy, 0.06), (cx, cy, fl - DECK_T - JOIST - 0.08), 0.045, 0.04, seg=12)
    B.cyl('CastIron', (cx, cy, fl - DECK_T - JOIST - 0.08), (cx, cy, fl - DECK_T - JOIST), 0.05, 0.08, seg=12)
    # the railing: posts, a top rail at 0.9, a middle rail, a kicking plate on the channel
    rails_x = [x0 + 0.27 + k * 1.1 for k in range(8) if x0 + 0.27 + k * 1.1 < x1 - 0.1] + [x1 - 0.02]
    ry = y0 + 0.012
    for xx in rails_x:
        B.box('WornIron', xx - 0.012, xx + 0.012, ry - 0.012, ry + 0.012, fl, fl + 0.9)
        B.box('WornIron', xx - 0.03, xx + 0.03, ry - 0.025, ry + 0.025, fl, fl + 0.015)
    B.cyl('WornIron', (x0 + 0.24, ry, fl + 0.9), (x1 - 0.02, ry, fl + 0.9), 0.017, seg=10)
    B.cyl('WornIron', (x0 + 0.24, ry, fl + 0.45), (x1 - 0.02, ry, fl + 0.45), 0.009, seg=6)
    B.cyl('WornIron', (x0 + 0.24, ry, fl + 0.9), (x0 + 0.24, ry, fl + 0.45), 0.012, seg=6)   # its end to the hatch jamb
    # things along the back of the passage: a tray rack on castors, a crate of jugs
    rx0, rx1 = 319.4, 320.15
    for xx in (rx0, rx1):
        for yy in (0.8, 1.12):
            B.box('WornIron', xx - 0.012, xx + 0.012, yy - 0.012, yy + 0.012, fl + 0.06, fl + 1.22)
            B.cyl('CastIron', (xx, yy - 0.025, fl + 0.03), (xx, yy + 0.025, fl + 0.03), 0.03, seg=8)
    for k in range(13):
        z = fl + 0.18 + k * 0.078
        B.box('WornIron', rx0, rx1, 0.79, 0.81, z, z + 0.008)
        B.box('WornIron', rx0, rx1, 1.11, 1.13, z, z + 0.008)
        if k % 3 != 1:
            B.box('Att16aAtlas', rx0 + 0.02, rx1 - 0.02, 0.8, 1.12, z + 0.008, z + 0.016, cell='sw_steel')
    B.box('CrateWood', 316.1, 316.6, 0.82, 1.18, fl, fl + 0.3)
    for k in range(4):
        B.cyl('Att16aAtlas', (316.18 + k * 0.11, 1.0, fl + 0.3), (316.18 + k * 0.11, 1.0, fl + 0.44), 0.045, 0.05, seg=10, cell='sw_enamel')
    # The lamp over the passage: a short-dropped enamel shade (its bulb in Att16aLamps).
    x, y, z = PASS_LAMP
    B.cyl('WornIron', (x, y, CEIL), (x, y, z + 0.12), 0.008, seg=6)
    B.cyl('WornIron', (x, y, CEIL), (x, y, CEIL - 0.03), 0.045, seg=10)
    B.cyl('DustyCream', (x, y, z + 0.1), (x, y, z - 0.02), 0.04, 0.17, seg=16)
    B.cyl('Att16aAtlas', (x, y, z + 0.08), (x, y, z - 0.015), 0.035, 0.16, seg=16, cell='sw_enamel')


def build_stair(B):
    """The stair down: 12 treads of 0.2 x 0.2 from the passage (2.4) at 321.2 to the floor at 323.6, the last at the
    floor's own level. Two painted cut strings (their tops under each tread, so the steps read in profile), worn
    timber treads with iron nosings on their step-off edge, a railing on the open front."""
    y0, y1 = STAIR[2], STAIR[3]
    soff = lambda x: max(0.0, stair_line(x) - 0.32)
    for i in range(1, TREADS + 1):
        a, b, top = tread(i)
        if top > 0.0:
            B.box('PupilWood', a, b, y0 + 0.03, y1 - 0.03, top - 0.04, top)
            B.box('WornIron', b - 0.035, b + 0.003, y0 + 0.026, y1 - 0.026, top - 0.042, top + 0.0015)
        for sy0, sy1 in ((y0, y0 + 0.03), (y1 - 0.03, y1)):
            zt = top - 0.04 if top > 0.0 else 0.0
            if zt - soff(b) > 0.005:
                B.prism_xz('WinDado', [(a, zt), (b, zt), (b, soff(b)), (a, soff(a))], sy0, sy1)
    # the strings' top end against the passage's channel
    B.prism_xz('WinDado', [(STAIR[0] - 0.12, PASS[4] - DECK_T - JOIST), (STAIR[0], PASS[4] - DECK_T - JOIST),
                           (STAIR[0], soff(STAIR[0])), (STAIR[0] - 0.12, soff(STAIR[0]) + 0.0)], y0, y0 + 0.03)
    # the railing on the open front: balusters on the string, a rail 0.9 over the nosings, a newel at each end
    ry = y0 + 0.015
    for i in range(1, TREADS):
        a, b, top = tread(i)
        if i % 2 == 1:
            B.cyl('WornIron', ((a + b) / 2, ry, top - 0.04), ((a + b) / 2, ry, stair_line((a + b) / 2) + 0.9), 0.009, seg=6)
    B.cyl('WornIron', (STAIR[0] - 0.02, ry, PASS[4] + 0.9), (STAIR[1] - 0.15, ry, stair_line(STAIR[1] - 0.15) + 0.9), 0.017, seg=10)
    nx = STAIR[1] - 0.15
    B.box('WornIron', nx - 0.025, nx + 0.025, ry - 0.025, ry + 0.025, 0.0, stair_line(nx) + 0.9)
    B.sphere('WornIron', (nx, ry, stair_line(nx) + 0.93), 0.03, seg=8)
    # STAFF STAIR enamel on the wall at its head, WORKSHOP with its arrow at its foot
    B.box('WornIron', 320.62, 321.02, WALL_Y - 0.012, WALL_Y, 3.0, 3.15)
    B.decal('Att16aAtlas', 320.63, 321.01, 3.005, 3.145, WALL_Y - 0.0125, cell='stair')
    B.box('WornIron', 323.0, 323.6, WALL_Y - 0.012, WALL_Y, 1.62, 1.845)
    B.decal('Att16aAtlas', 323.01, 323.59, 1.625, 1.84, WALL_Y - 0.0125, cell='workshop')
    # the bulkhead by its foot (the glass is in Att16aLamps)
    x, y, z = STAIR_LAMP
    B.box('WornIron', x - 0.09, x + 0.09, WALL_Y - 0.02, WALL_Y, z - 0.08, z + 0.08)
    B.cyl('WornIron', (x, WALL_Y - 0.02, z), (x, y + 0.02, z), 0.07, seg=14)
    for k in range(3):
        zz = z - 0.04 + k * 0.04
        B.cyl('WornIron', (x - 0.07, y - 0.012, zz), (x + 0.07, y - 0.012, zz), 0.004, seg=4)
    B.cyl('Att16aAtlas', (x, WALL_Y - 0.004, z + 0.08), (x, WALL_Y - 0.004, CEIL), 0.012, seg=6, cell='sw_black')


def build_lower_corridor(B, rnd):
    """Behind the gate, under the passage: pipes on the back wall, STAFF ONLY, a tray trolley, crates, a mop bucket
    under the stair. All behind the lane."""
    wy = WALL_Y
    for z, r, mt in ((2.08, 0.045, 'WornIron'), (1.98, 0.022, 'Copper')):
        B.cyl(mt, (SHAFT[1] + POST, wy - 0.07, z), (X1, wy - 0.07, z), r, seg=10)
    for x in (314.6, 316.6, 318.6, 320.6, 322.6):
        B.box('WornIron', x - 0.02, x + 0.02, wy - 0.12, wy, 1.94, 2.12)
    B.box('WornIron', 314.75, 315.17, wy - 0.012, wy, 1.42, 1.58)
    B.decal('Att16aAtlas', 314.76, 315.16, 1.425, 1.575, wy - 0.0125, cell='staff')
    # the tray trolley, parked
    tx0, tx1, ty0, ty1 = 316.3, 317.15, 0.72, 1.12
    for z in (0.18, 0.5, 0.82):
        B.box('WornIron', tx0, tx1, ty0, ty1, z, z + 0.02)
        B.box('Att16aAtlas', tx0 + 0.03, tx1 - 0.03, ty0 + 0.03, ty1 - 0.03, z + 0.02, z + 0.03, cell='sw_steel')
    for xx in (tx0 + 0.015, tx1 - 0.015):
        for yy in (ty0 + 0.015, ty1 - 0.015):
            B.box('WornIron', xx - 0.012, xx + 0.012, yy - 0.012, yy + 0.012, 0.08, 0.92)
            B.cyl('Att16aAtlas', (xx, yy - 0.02, 0.05), (xx, yy + 0.02, 0.05), 0.045, seg=10, cell='sw_rubber')
    B.cyl('WornIron', (tx1, ty0 + 0.05, 0.95), (tx1, ty1 - 0.05, 0.95), 0.012, seg=6)
    for k in range(3):
        B.cyl('Att16aAtlas', (tx0 + 0.2 + k * 0.2, 0.92, 0.53), (tx0 + 0.2 + k * 0.2, 0.92, 0.6), 0.07, 0.08, seg=12, cell='sw_enamel')
    # crates, stacked
    for k, (cx, cz) in enumerate(((319.0, 0.0), (319.48, 0.0), (319.22, 0.3))):
        B.box('CrateWood', cx - 0.22, cx + 0.22, 0.82, 1.18, cz, cz + 0.29)
        B.box('PigeonWood', cx - 0.225, cx + 0.225, 0.815, 0.83, cz + 0.12, cz + 0.17)
    # a mop bucket and mop under the stair
    bx = 322.35
    B.cyl('Att16aAtlas', (bx, 0.95, 0.0), (bx, 0.95, 0.26), 0.13, 0.15, seg=14, cell='sw_steel')
    B.torus('WornIron', (bx, 0.95, 0.26), (0, 0, 1), 0.15, 0.008, seg=16, rseg=3)
    B.cyl('PupilWood', (bx + 0.05, 0.95, 0.1), (bx + 0.42, 1.12, 1.25), 0.014, seg=6)


def _wire(B, pts, r, mt, seg=6):
    """A run of cable through the points: straight lengths, a ball at each bend."""
    pts = [Vector(p) for p in pts]
    for a, b in zip(pts, pts[1:]):
        B.cyl(mt, a, b, r, seg=seg)
    for p in pts[1:-1]:
        B.sphere(mt, p, r, seg=seg)


def cable_path():
    """The new service cable: in through the wall over DL-16's partition, along the kitchen's back wall just under the
    ceiling's beams (z 3.70), behind the shaft's head, down into the relay box by the hatch and out again, along the
    upper passage over the gate, down the stair's wall parallel to its pitch (1.3 over the nosings), level at 2.4 to the
    corner, and along DL-17's wall toward its doorway, where it goes in over the door. (x, y, z, wall normal)"""
    z, y = CABLE_Z, CABLE_Y
    r0, r1, rz0, rz1 = RELAY
    a, b = r0 + 0.05, r1 - 0.05
    xe = X1 - 0.03
    return [(X0 + 0.15, y, z), (a, y, z), (a, y, rz1 + 0.02), (b, y, rz1 + 0.02), (b, y, z), (STAIR[0], y, z),
            (STAIR[0] + 1.3, y, z - 1.3), (xe, y, z - 1.3), (xe, R_DOOR[1] + 0.08, z - 1.3)]


def build_cable(B):
    """A present-day service line through the school (the prologue's new cable, pass 6): glossy black, galvanised
    clips about every metre, two taped joints; a small new relay box near the top of the dumbwaiter's shaft (its green
    pilot lamp is Att16aRelayLamp); glands where it goes into the walls."""
    pts = [Vector(p) for p in cable_path()]
    _wire(B, pts, CABLE_R, 'NewCable')
    acc, nxt = 0.0, 0.45
    for a, b in zip(pts, pts[1:]):
        seg = (b - a).length
        n = Vector((-1, 0, 0)) if abs(a.x - b.x) < 1e-6 and abs(a.y - b.y) > 1e-6 else Vector((0, -1, 0))   # out of its wall
        d = (b - a).normalized()
        side = d.cross(n).normalized()
        while acc + seg >= nxt:
            p = a.lerp(b, (nxt - acc) / seg)
            if not (RELAY[0] - 0.08 < p.x < RELAY[1] + 0.08):
                for sg in (-1, 1):
                    c = p + side * sg * 0.022 - n * 0.004
                    add_box(B.bm, c, (0.012, 0.012, 0.012), mat=B.m('NewSteel'))
                B.cyl('NewSteel', p - side * 0.026 + n * 0.004, p + side * 0.026 + n * 0.004, 0.0065, seg=4)
            nxt += 1.05
        acc += seg
    for k, f in ((0, 0.62), (4, 0.55)):                                                # taped joints: two black bands
        a, b = pts[k], pts[k + 1]
        p = a.lerp(b, f)
        d = (b - a).normalized()
        for o in (-0.04, 0.04):
            B.cyl('NewCable', p + d * (o - 0.025), p + d * (o + 0.025), CABLE_R + 0.005, seg=6)
    for p, ax in ((pts[0], Vector((-1, 0, 0))), (pts[-1], Vector((1, 0, 0)))):        # glands into the walls
        B.cyl('NewSteel', p, p + ax * 0.03, 0.02, seg=8)
    # the relay box: galvanised, a lid on four screws, two glands on top, a printed label, the pilot lamp's bezel
    x0, x1, z0, z1 = RELAY
    yb = WALL_Y
    B.box('NewSteel', x0, x1, yb - 0.09, yb, z0, z1)
    B.box('NewSteel', x0 + 0.008, x1 - 0.008, yb - 0.096, yb - 0.09, z0 + 0.008, z1 - 0.008)
    for xx in (x0 + 0.022, x1 - 0.022):
        for zz in (z0 + 0.022, z1 - 0.022):
            B.cyl('NewSteel', (xx, yb - 0.096, zz), (xx, yb - 0.1, zz), 0.006, seg=6)
    for xx in (x0 + 0.05, x1 - 0.05):
        B.cyl('NewSteel', (xx, CABLE_Y, z1), (xx, CABLE_Y, z1 + 0.022), 0.017, seg=8)
    B.box('Att16aAtlas', x0 + 0.04, x0 + 0.14, yb - 0.097, yb - 0.096, z0 + 0.12, z0 + 0.16, cell='sw_paper')
    lx, lz = RELAY_LAMP
    B.torus('NewSteel', (lx, yb - 0.098, lz), (0, 1, 0), 0.012, 0.003, seg=12, rseg=3)


def build_relay_lamp(coll):
    """Att16aRelayLamp: the relay box's tiny green pilot lamp (EMIT, lit as built), its own object; origin its centre."""
    L = MB()
    c = (RELAY_LAMP[0], WALL_Y - 0.099, RELAY_LAMP[1])
    L.sphere('Att16aRelayLamp', c, 0.008, seg=10, scale=(1, 0.5, 1))
    return L.obj('Att16aRelayLamp', coll, origin=c)


def build_chalk(coll):
    """Att16aChalk: her chalk on the dresser's door, the hot cupboard's doors (an arrow over the third), and on the
    hatch frame at the top. Image material Chalk16a (alpha)."""
    B = MB()
    dfy = DRESSER[2]                                   # the dresser's door face
    hfy = COUNTER[2]                                   # the hot cupboard's door face
    for k, (x, y) in enumerate(((CHALK_TREES[0], dfy), (CHALK_TREES[1], hfy), (CHALK_TREES[2], hfy))):
        B.decal('Chalk16a', x - 0.1, x + 0.1, 0.4, 0.6, y - 0.0015, uvr=chalk_uv('tree%d' % (k + 1)))
    B.decal('Chalk16a', 312.03, 312.41, 0.61, 0.73, hfy - 0.0015, uvr=chalk_uv('arrow'))
    x, z0, z1 = TREE4
    fy = HATCH[2]
    B.decal('Chalk16a', x - 0.08, x + 0.08, z0, z0 + 0.16, fy - 0.0015, uvr=chalk_uv('tree4'))
    B.decal('Chalk16a', x - 0.045, x + 0.035, z1 - 0.085, z1, fy - 0.0015, uvr=chalk_uv('hand'))
    return B.obj('Att16aChalk', coll)


# =====================================================================================================================
# What the game moves
# =====================================================================================================================
def build_car(coll):
    """Att16aCar: a small tray car, open to the front (and at its sides in front of y 0.25, so D-17 walks in along the
    lane): a timber floor in an iron edge (top 0.05), an iron frame, a lined back wall with rubbing strips, short side
    returns at the back, an iron roof; the brass plate NO PASSENGERS on its front fascia, a caged lamp (EMIT
    Att16aCarLamp) under the roof at the back left, the bell push on its back wall at z 0.6, a crosshead with the
    rope's shackle, the rope running up into the ceiling, guide shoes on the back corners. Origin: the middle of the
    floor's top (313.0, 0.1, 0.05). Built at the bottom."""
    B = MB()
    ix0, ix1 = CAR_IN
    ox0, ox1 = ix0 - CAR_WALL, ix1 + CAR_WALL
    y0, y1 = CAR_Y
    f, rf = CAR_FLOOR, CAR_ROOF
    # floor: boards along x in an iron edge
    B.box('WornIron', ix0, ix1, y0 + 0.025, y1, 0.004, f - 0.012)
    n = 7
    for k in range(n):
        ya = y0 + 0.01 + k * (y1 - y0 - 0.02) / n
        yb = y0 + 0.01 + (k + 1) * (y1 - y0 - 0.02) / n - 0.004
        B.box('PupilWood', ix0, ix1, ya, yb, f - 0.014, f)
    B.box('WornIron', ix0, ix1, y0, y0 + 0.025, 0.0, f + 0.004)                            # the front sill angle
    for x0, x1 in ((ox0, ix0), (ix1, ox1)):
        B.box('WornIron', x0, x1, y0, y1, 0.0, f + 0.004)
    # the back wall (lined), rubbing strips, side returns, corner posts
    B.box('WornIron', ox0, ox1, y1 - 0.012, y1, f, rf)
    B.box('CrateWood', ix0, ix1, y1 - 0.03, y1 - 0.012, f, rf)
    for k in range(1, 6):
        xx = ix0 + k * (ix1 - ix0) / 6
        B.sbox('sw_dark', xx - 0.002, xx + 0.002, y1 - 0.0305, y1 - 0.03, f, rf)
    for z in (0.32, 0.86):
        B.box('PigeonWood', ix0, ix1, y1 - 0.05, y1 - 0.03, z, z + 0.05)
    for x0, x1 in ((ox0, ix0), (ix1, ox1)):
        B.box('CrateWood', x0, x1, 0.25, y1 - 0.012, f + 0.004, rf)
        B.box('WornIron', x0, x1, y0, y0 + 0.03, f + 0.004, rf)                            # the front posts
        B.box('WornIron', x0 - 0.004, x1 + 0.004, 0.22, 0.26, f, rf)                       # the returns' edge angles
    # roof, front fascia with the plate, the crosshead and the rope
    B.box('WornIron', ox0, ox1, y0, y1, rf, rf + 0.035)
    B.box('WornIron', ox0 - 0.004, ox1 + 0.004, y0 - 0.004, y0 + 0.015, rf - 0.03, rf + 0.039)
    px0, px1 = 312.84, 313.16
    B.box('HandledBrass', px0 - 0.006, px1 + 0.006, y0 - 0.009, y0 - 0.004, rf - 0.024, rf + 0.03)
    B.decal('Att16aAtlas', px0, px1, rf - 0.02, rf + 0.026, y0 - 0.0095, cell='max3')
    ch = rf + 0.035
    B.box('CastIron', ix0 + 0.02, ix1 - 0.02, 0.45, 0.55, ch, ch + 0.055)
    for xx in (ix0 + 0.06, ix1 - 0.06):
        B.prism_xz('CastIron', [(xx - 0.05, ch), (xx + 0.05, ch), (xx, ch + 0.05)], 0.46, 0.54)
    B.box('CastIron', 312.97, 313.03, 0.48, 0.52, ch + 0.055, ch + 0.09)
    B.torus('WornIron', (313.0, 0.5, ch + 0.11), (1, 0, 0), 0.022, 0.006, seg=10, rseg=4)
    B.cyl('DarkMetal', (313.0, 0.5, ch + 0.13), (313.0, 0.5, ch + 0.13 + ROPE_LEN), 0.009, seg=6)
    # guide shoes on the back corners, on the shaft's rails
    for x0, x1 in ((ox0 - 0.03, ox0), (ox1, ox1 + 0.03)):
        for z in (0.06, rf - 0.12):
            B.box('CastIron', x0, x1, 0.45, 0.55, z, z + 0.1)
    # the lamp: a small caged fitting under the roof, at the back left
    lx, ly, lz = 312.72, 0.42, rf - 0.035
    B.cyl('WornIron', (lx, ly, rf), (lx, ly, rf - 0.012), 0.035, seg=10)
    L = (lx, ly, lz)
    B.sphere('Att16aCarLamp', L, 0.022, seg=10, scale=(1, 1, 1.15))
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        B.cyl('WornIron', (lx + 0.032 * math.cos(a), ly + 0.032 * math.sin(a), rf - 0.012),
              (lx + 0.03 * math.cos(a), ly + 0.03 * math.sin(a), lz - 0.03), 0.0025, seg=3)
    B.torus('WornIron', (lx, ly, lz - 0.02), (0, 0, 1), 0.03, 0.003, seg=10, rseg=3)
    # the bell push: a brass rose, a black button, RING over it
    bx, bz = BELL
    by = y1 - 0.03
    B.cyl('HandledBrass', (bx, by, bz), (bx, by - 0.01, bz), 0.035, seg=14)
    B.cyl('Att16aAtlas', (bx, by - 0.01, bz), (bx, by - 0.02, bz), 0.016, seg=10, cell='sw_black')
    B.box('HandledBrass', bx - 0.036, bx + 0.036, by - 0.004, by, bz + 0.048, bz + 0.104)
    B.decal('Att16aAtlas', bx - 0.032, bx + 0.032, bz + 0.052, bz + 0.1, by - 0.0045, cell='bellpict')   # as the call push's
    B.cyl('Att16aAtlas', (bx, by - 0.002, bz + 0.035), (bx, by - 0.002, rf), 0.004, seg=4, cell='sw_black')   # its flex
    car = B.obj('Att16aCar', coll, origin=CAR_ORIGIN)
    e = bpy.data.objects.new('Att16aBellPush', None)
    e.empty_display_type = 'SPHERE'
    e.empty_display_size = 0.03
    coll.objects.link(e)
    e.parent = car
    e.location = Vector((bx, by - 0.02, bz)) - Vector(CAR_ORIGIN)                            # car-local
    return car, e


def build_call_mount(B):
    """The call push's mount on the shaft's left frame: an oak block on an iron backplate on the front-left post's
    left face (flush with its front, so the post never hides it), its face turned to the camera and the lane's left;
    the bell pictogram plate over the push; its flex in a thin conduit up the post into the landing's header."""
    sx0 = SHAFT[0]
    p = POST
    fy0, fy1 = SHAFT[2] - p, SHAFT[2]                   # the front post's y
    n = Vector(CALL_N).normalized()
    t = Vector((-n.y, n.x, 0.0))                        # along the face, to the right as seen from in front
    F = Vector(CALL_PUSH) - n * 0.014                   # the block's face
    R = Matrix((t, -n, Vector((0, 0, 1)))).transposed().to_4x4()
    add_box(B.bm, F - n * 0.025, (0.09, 0.05, 0.25), mat=B.m('PigeonWood'), rot=R)
    B.box('WornIron', sx0 - p - 0.012, sx0 - p, fy0, fy1, 0.41, 0.69)                       # its backplate on the post
    for z in (0.43, 0.67):
        B.cyl('WornIron', (sx0 - p - 0.012, (fy0 + fy1) / 2, z), (sx0 - p - 0.018, (fy0 + fy1) / 2, z), 0.006, seg=6)
    # (the push itself, its brass rose and button, is Att16aCallPush) the bell pictogram plate over it, on the block
    pc = F + Vector((0, 0, 0.078))
    add_box(B.bm, pc + n * 0.002, (0.078, 0.004, 0.06), mat=B.m('HandledBrass'), rot=R)
    u0, v0, u1, v1 = cell_uv('bellpict')
    B.face('Att16aAtlas', [pc + n * 0.0045 + t * sx * 0.036 + Vector((0, 0, sz * 0.027)) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))],
           [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
    # the flex, in a thin conduit from the block's top up the post's left face into the header
    top = F - n * 0.03 + Vector((0, 0, 0.125))
    cx = sx0 - p - 0.009
    cy = (fy0 + fy1) / 2 + 0.02
    B.cyl('WornIron', top, Vector((cx, cy, top.z + 0.04)), 0.007, seg=6)
    B.cyl('WornIron', Vector((cx, cy, top.z + 0.04)), Vector((cx, cy, HDR[0])), 0.007, seg=6)
    for z in (0.9, 1.15):
        B.box('WornIron', cx - 0.004, cx + 0.009, cy - 0.012, cy + 0.012, z - 0.006, z + 0.006)   # its saddles


def build_call_push(coll):
    """Att16aCallPush: the outside call push, a round brass bell push (a brass rose, an ivory button), its own object;
    origin at the button's face. Its block and the bell pictogram plate over it are in Att16aSet."""
    B = MB()
    n = Vector(CALL_N).normalized()
    F = Vector(CALL_PUSH) - n * 0.014                   # the block's face, where the rose sits
    B.cyl('HandledBrass', F - n * 0.001, F + n * 0.008, 0.032, seg=18)                     # a round brass rose
    B.cyl('HandledBrass', F + n * 0.008, F + n * 0.010, 0.022, 0.018, seg=18)
    B.cyl('Att16aAtlas', F + n * 0.006, F + n * 0.014, 0.0135, 0.0125, seg=14, cell='sw_ivory')   # its button
    return B.obj('Att16aCallPush', coll, origin=CALL_PUSH)


def build_cw(coll):
    """Att16aCW: a slim counterweight behind the car (y 0.62 .. 0.69): a cast frame of two stiles and two bars with
    filler weights stacked in it, a hazard plate on its bottom bar, its rope up from a shackle into the ceiling.
    Origin bottom centre (313.0, 0.655, 3.0); built at the top of the shaft. Moves opposite the car (-2.4)."""
    B = MB()
    x0, x1, y0, y1, h = CW
    z0 = CW_ORIGIN[2]
    z1 = z0 + h
    for a, b in ((x0, x0 + 0.04), (x1 - 0.04, x1)):
        B.box('CastIron', a, b, y0, y1, z0, z1)
    B.box('CastIron', x0, x1, y0, y1, z0, z0 + 0.08)
    B.box('CastIron', x0, x1, y0, y1, z1 - 0.06, z1)
    n = 9
    for k in range(n):
        za = z0 + 0.08 + k * (h - 0.14) / n
        B.box('WornIron', x0 + 0.045, x1 - 0.045, y0 + 0.008, y1 - 0.008, za + 0.003, za + (h - 0.14) / n - 0.003)
    B.decal('Att16aAtlas', x0 + 0.05, x1 - 0.05, z0 + 0.008, z0 + 0.072, y0 - 0.0005, cell='cwsign')
    for a, b in ((x0 - 0.02, x0), (x1, x1 + 0.02)):                                          # guide shoes
        for z in (z0 + 0.02, z1 - 0.1):
            B.box('CastIron', a, b, y0 + 0.01, y1 - 0.01, z, z + 0.08)
    cx, cy = CW_ORIGIN[0], CW_ORIGIN[1]
    B.box('CastIron', cx - 0.03, cx + 0.03, cy - 0.02, cy + 0.02, z1, z1 + 0.025)
    B.torus('WornIron', (cx, cy, z1 + 0.04), (1, 0, 0), 0.016, 0.005, seg=10, rseg=4)
    B.cyl('DarkMetal', (cx, cy, z1 + 0.055), (cx, cy, z1 + 0.055 + ROPE_LEN), 0.009, seg=6)
    return B.obj('Att16aCW', coll, origin=CW_ORIGIN)


def build_tin(coll, name, x, y, rnd):
    """A catering tin, olive, with rolled rims and a paper label (SCHOOL MEALS SERVICE, RATIONS) facing the camera;
    a little dented. Origin bottom centre."""
    B = MB()
    r, h = TIN_R, TIN_H
    B.cyl('Att16aAtlas', (x, y, 0.004), (x, y, h - 0.004), r, seg=20, cell='sw_tin')
    for z in (0.004, h - 0.004):
        B.torus('WornIron', (x, y, z), (0, 0, 1), r - 0.001, 0.004, seg=20, rseg=4)
    for z in (0.045, h - 0.045):                                                             # beads
        B.torus('Att16aAtlas', (x, y, z), (0, 0, 1), r, 0.002, seg=20, rseg=3, cell='sw_tin')
    B.cyl('WornIron', (x, y, h - 0.006), (x, y, h - 0.002), r - 0.006, seg=20)
    B.label_band((x, y), r + 0.0015, 0.055, h - 0.055, 'tinlabel', seg=20, face_dir=-math.pi / 2 + rnd.uniform(-0.4, 0.4))
    return B.obj(name, coll, origin=(x, y, 0.0))


def build_books(coll):
    """Att16aBooks: four school books, stacked a little skew, tied with string both ways with a bow on top. Origin
    bottom centre (310.55, 0.35, 1.25)."""
    B = MB()
    cx, cy, z = BOOKS
    rnd = random.Random(16300)
    sizes = ((0.25, 0.18, 0.034, 'sw_bk2'), (0.24, 0.175, 0.03, 'sw_bk1'), (0.23, 0.17, 0.028, 'sw_bk3'), (0.22, 0.16, 0.026, 'sw_bk5'))
    zz = z
    for k, (w, d, t, cell) in enumerate(sizes):
        ox, oy = rnd.uniform(-0.008, 0.008), rnd.uniform(-0.006, 0.006)
        a = rnd.uniform(-0.05, 0.05)
        rot = Matrix.Rotation(a, 4, 'Z')
        n0 = B.mark()
        B.box('Att16aAtlas', -w / 2, w / 2, -d / 2, d / 2, 0.0, 0.004, cell=cell)          # boards
        B.box('Att16aAtlas', -w / 2, w / 2, -d / 2, d / 2, t - 0.004, t, cell=cell)
        B.box('Att16aAtlas', -w / 2, -w / 2 + 0.006, -d / 2, d / 2, 0.0, t, cell=cell)      # the spine (toward -x)
        B.box('Att16aAtlas', -w / 2 + 0.006, w / 2 - 0.004, -d / 2 + 0.004, d / 2 - 0.004, 0.004, t - 0.004, cell='sw_paper')
        for v in B.since(n0):
            v.co = Matrix.Translation((cx + ox, cy + oy, zz)) @ rot @ v.co
        zz += t
    top = zz
    # the string: once round along x, once along y, a knot and a bow on top
    s = 0.0025
    W, D = 0.252, 0.182
    for y in (cy - 0.0,):
        B.box('Att16aAtlas', cx - W / 2, cx + W / 2, y - s, y + s, top, top + 2 * s, cell='sw_string')
        for x in (cx - W / 2, cx + W / 2):
            B.box('Att16aAtlas', x - s, x + s, y - s, y + s, z, top + 2 * s, cell='sw_string')
    for x in (cx + 0.02,):
        B.box('Att16aAtlas', x - s, x + s, cy - D / 2, cy + D / 2, top + 2 * s, top + 4 * s, cell='sw_string')
        for y in (cy - D / 2, cy + D / 2):
            B.box('Att16aAtlas', x - s, x + s, y - s, y + s, z, top + 4 * s, cell='sw_string')
    kx, ky, kz = cx + 0.02, cy, top + 4 * s
    B.sphere('Att16aAtlas', (kx, ky, kz + 0.004), 0.007, seg=6, cell='sw_string')
    for sgn in (-1, 1):
        B.torus('Att16aAtlas', (kx + sgn * 0.016, ky, kz + 0.006), (0.3 * sgn, 0, 1), 0.013, 0.0022, seg=10, rseg=3, cell='sw_string')
        B.cyl('Att16aAtlas', (kx, ky, kz + 0.004), (kx + sgn * 0.012, ky - 0.03, kz + 0.001), 0.0022, seg=3, cell='sw_string')
    return B.obj('Att16aBooks', coll, origin=BOOKS)


def build_lamps(coll):
    """Att16aLamps: the static lit bulbs (EMIT AttBulbGlow): the kitchen pendant's, the passage lamp's, the
    bulkhead's glass by the stair's foot."""
    L = MB()
    x, y, z = PENDANT
    L.sphere('AttBulbGlow', (x, y, z - 0.01), 0.045, seg=12)
    x, y, z = PASS_LAMP
    L.sphere('AttBulbGlow', (x, y, z), 0.04, seg=12)
    x, y, z = STAIR_LAMP
    L.sphere('AttBulbGlow', (x, y + 0.01, z), 0.06, seg=12, scale=(1, 0.45, 1))
    return L.obj('Att16aLamps', coll)


# =====================================================================================================================
def tris(ob):
    if ob.type != 'MESH':
        return 0
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def build_set(dl01, m, coll):
    os.makedirs(TEX, exist_ok=True)
    make_atlas(os.path.join(TEX, ATLAS_PNG))
    make_chalk(os.path.join(TEX, CHALK_PNG))
    rnd = random.Random(1616)
    B = MB()
    build_shell(B)
    build_kitchen(B, rnd)
    build_shaft(B)
    lamps = build_gauge(B, coll)
    build_gate(B)
    build_passage(B)
    build_stair(B)
    build_lower_corridor(B, rnd)
    build_cable(B)
    build_call_mount(B)
    objs = [B.obj('Att16aSet', coll), build_chalk(coll), build_lamps(coll), build_call_push(coll)]
    car, bell = build_car(coll)
    objs += [car, build_cw(coll), build_relay_lamp(coll)]
    for k, (x, y) in enumerate(TINS):
        objs.append(build_tin(coll, 'Att16aTin%d' % (k + 1), x, y, rnd))
    objs.append(build_books(coll))
    objs += lamps
    bpy.context.view_layer.update()
    total = 0
    for ob in objs:
        t = tris(ob)
        total += t
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        print('dl16a: %-16s tris %6d mats %-60s x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f origin %s' % (
            ob.name, t, [s.material.name for s in ob.material_slots],
            min(v.x for v in bb), max(v.x for v in bb), min(v.y for v in bb), max(v.y for v in bb), min(v.z for v in bb),
            max(v.z for v in bb), tuple(round(c, 3) for c in ob.location)))
    print('dl16a: tris %d; bell push (world) %s' % (total, tuple(round(c, 3) for c in bell.matrix_world.translation)))


REPORT = """DL-16a Her Way Round (art/ch1/dl16a.py), game x 310.0 .. 324.0, built in FINAL coordinates (no SHIFT).
Blender (x, y, z) = game (x, z, -y). Numbers below are Blender unless marked "game".

MOVED (origin = pivot, world; built pose = rotation 0, as listed):
- Att16aCar: origin (313.0, 0.1, 0.05) = the middle of its floor's top = game (313.0, 0.05, -0.1). Built at the BOTTOM.
  Inside x 312.6 .. 313.4 (side/back skins 0.03: outer 312.57 .. 313.43; guide shoes to 312.54 / 313.46), depth y -0.4 .. 0.6,
  floor top 0.05, roof underside 1.21 (clear 1.16 over the floor; D-17 to 1.12), roof top 1.245, crosshead to 1.30.
  Open at the front; its sides are open in front of y 0.25 (short returns 0.25 .. 0.6 only), so he walks in along the lane
  from either side (a 4 mm iron edge at the floor's sides, top 0.054). Top: +2.4 in z (floor top 2.45, roof 3.645).
  Carries in its mesh: the lamp (EMIT Att16aCarLamp, bulb at (312.72, 0.42, 1.175)), the brass plate NO PASSENGERS on its
  front fascia (z 1.18 .. 1.249), the bell push (brass rose on the back wall's lining, face y 0.55, at x 313.25 z 0.6) with
  the bell pictogram over it (was RING), and its rope (up into the ceiling; see ROPES).
- Att16aBellPush: EMPTY, child of Att16aCar, local (0.25, 0.45, 0.55); world at build (313.25, 0.55, 0.6) = game
  (313.25, 0.6, -0.55). Moves with the car (use getWorldPosition).
- Att16aCW: origin bottom centre (313.0, 0.655, 3.0) = game (313.0, 3.0, -0.655). Built at the TOP of the shaft, behind the car:
  x 312.72 .. 313.28 (shoes to 312.70 / 313.30), y 0.62 .. 0.69, z 3.0 .. 3.7. Moves opposite the car: -2.4 (bottom 0.6, top
  1.3, clear of its spring buffers at 0.27 and of the car, which passes in front of it).
- Att16aCallPush (NEW, redesign after the director's playtest: no ballast puzzle): the outside call push, a round brass
  bell push (brass rose r 0.032, ivory button r 0.0135) on an oak block on the shaft's front-left post's left face, at
  child height, its face turned to the camera and toward the lane's left (normal Blender (-0.6, -0.8, 0)). Origin = the
  button's face, Blender (312.375, -0.46, 0.55) = game (312.375, 0.55, 0.46); its own object (HandledBrass, Att16aAtlas).
  Over it on the block (in Att16aSet), a brass plate 0.072 x 0.054 with a bell pictogram (atlas cell bellpict), no words;
  a conduit from the block up the post into the landing's header. Reachable from the lane just left of the car (the
  car's inside starts at 312.6). The car's own push (Att16aBellPush) now has the same bell pictogram plate over it
  (was RING), so one sign means "call / send" both sides.
  DEVIATION: asked for about (312.42, -0.2, 0.55). At y -0.2 the push sat behind the front-left post (y -0.53..-0.45),
  which hid it whenever the camera was right of 312.4; and its block covered half of her third chalk tree (312.3). It
  is on the post's own left face instead, flush with its front (y -0.47..-0.43), x 312.35..312.41.
- Att16aTin1 (311.2, 0, 0), Att16aTin2 (311.45, 0, 0) = game (311.2 / 311.45, 0, 0): catering tins, r 0.075 (rims 0.078),
  0.17 high, origin bottom centre. Same mesh shape, separate meshes. Dressing now (the ballast puzzle is cut).
- Att16aBooks: set dressing now (not carried), still its own object at (310.55, 0.35, 1.25) on the shelf; four books tied
  with string, x 310.42 .. 310.69, y 0.26 .. 0.45, 0.14 high (bow to 1.39).
- Att16aLoad1 (amber, LOAD) and Att16aLoadOver (red, OVER): the gauge's two lamps, own objects, own EMIT materials of the
  same names (built OFF, strength 0), origins at the lenses' centres: x 312.88 / 313.12, y -0.559, z 1.39
  = game (x, 1.39, 0.559); the red line engraved between them at x 313.0. Load2/Load3 are dropped (no objects).
  Suggested lamp() colours: Load1 0xffa030, Over 0xff2a18. Dressing now: no load rule (leave both off, or let Load1
  glow while the car carries him).
- Att16aRelayLamp: the relay box's green pilot lamp (EMIT Att16aRelayLamp, lit as built), own object, origin (314.2, 1.101, 3.455)
  = game (314.2, 3.455, -1.101). Static unless the game switches it (suggested lamp() colour 0x60ff78).

SURFACES / COLLISION (as the build sheet; all built to these numbers):
- Floor 0 from 310.0 to 324.0 (lino; the shaft's footprint 312.42 .. 313.58 an iron plate flush at 0). Thresholds: 310.0 .. 310.04
  at 0.004 (meets DL-16's), 323.96 .. 324.0 at 0.012 (meets DL-17's iron strip). Ceiling 3.9 (beams to 3.74 at 311.2, 315.4,
  317.8, 320.2, 322.6, all clear of the passage's walking height; the shaft's head frame 3.74 .. 3.9).
- High shelf: x 310.2 .. 310.9, y 0.1 .. 0.6, top 1.25 (a 12 mm lip along its front edge at y 0.09 .. 0.112). Nothing under
  it in the lane (iron bearers at x 310.22 / 310.88, tie rods up and back to the dresser at y 0.65). Dressing only now.
- Car floor 0.05 at the bottom / 2.45 at the top. Shaft clear inside 312.5 .. 313.5, y -0.45 .. 0.7; its posts outside that
  (front y -0.53 .. -0.45, back 0.7 .. 0.78, x 312.42 .. 312.5 and 313.5 .. 313.58). Lower landing's header across the shaft's
  front at z 1.3 .. 1.5 (y -0.542 .. -0.454, in front of the lane), the gauge's plate on it (centre z 1.4). Upper sill 2.3 .. 2.4.
  The front-right post stops at the passage (2.35); above it the hatch frame's jamb (x 313.5 .. 313.74, y -0.45 .. -0.33,
  2.4 .. 3.62) and lintel (3.62): the car's top landing opens to the right onto the passage under a 3.62 head.
- Gate: x 313.97 .. 314.03, floor to 2.3, y -0.45 .. 0.9, then a fixed post to the wall (0.9 .. 1.2). A wall for D-17.
  Its sign PUPILS NOT PERMITTED BEYOND THIS POINT at x 313.62 .. 314.38, z 1.5 .. 1.72, y -0.5 (in front of the lane).
- Upper passage: x 313.5 .. 321.2, floor 2.4, y -0.3 .. 1.2 (boards 2.36 .. 2.4 on joists to 2.30; the joist at 314.0 is the
  gate's head). Railing along y -0.29: posts, top rail 3.3, middle rail 2.85 (in front of the lane). A cast column at
  (317.6, -0.26) under its front edge. Clear height on the passage 1.5 (to the ceiling) / 1.34 under the beams.
- Stair: tread i (1..12) at x 321.2 + 0.2 (i - 1) .. 321.2 + 0.2 i, top 2.4 - 0.2 i (2.2, 2.0, .. 0.2, 0.0); y -0.45 .. 0.6.
  Tread 12 (323.4 .. 323.6) is the floor itself (top 0), so 11 timber treads are built. Strings under the treads (front
  y -0.45 .. -0.42, back 0.57 .. 0.6), soffit 0.32 below the nosing line. Railing on its open front (y -0.435).
- Lower corridor beyond the gate: 314.0 .. 324.0 at 0, under the passage (head 2.30, joists), then by the stair's foot to
  DL-17's doorway (y -0.45 .. 0.55, head 2.1). Everything in it is behind the lane (y > 0.7) except the column (y -0.26).

STORY: chalk (Att16aChalk, image material Chalk16a, alpha): trees at 0.4 .. 0.6 centred x 310.7 (on the dresser's cupboard
door, face y 0.62), 311.6 and 312.3 (on the hot cupboard's doors, face y 0.70), an arrow over the third (x 312.03 .. 312.41,
z 0.61 .. 0.73) pointing at the car; on the hatch jamb's front (face y -0.45): the fourth tree x 313.52 .. 313.68,
z 2.6 .. 2.76, and a small handprint x 313.555 .. 313.635, z 2.815 .. 2.9.
Signs: the gate's enamel; the gauge TRAYS ONLY - LOAD TO THE LINE (one window LOAD, a red line, OVER; dressing); the
bell pictogram over both pushes (outside the car and inside it); NO PASSENGERS on the
car (was MAX 3 PORTIONS: no longer true of the puzzle); STAFF ONLY (lower corridor), STAFF STAIR (passage), WORKSHOP with an arrow (stair foot); a DINNERS board in the kitchen.

ROPES: no rope objects to scale. Each rope is part of its mover's mesh and runs 2.85 up from its shackle, through the head frame
and the ceiling into a black trunk above it (x 312.78 .. 313.22, y 0.36 .. 0.82, z 4.05 .. 6.82, swatch black like DL-16's
slot), so whichever way they move, the ropes always reach up out of sight.

LIGHTS (index.html P/S, game coords):
  P(0xffdcaa, 1.6, 5, 311.5, 2.6, -0.3)                                       // the kitchen pendant (bulb in Att16aLamps)
  S(0xffe0b8, 5, 5, [313.0, 3.2, 2.4], [313.0, 0.9, -0.2], 0.5)               // the car and the gauge
  S(0xffd8a8, 4, 5, [310.8, 2.8, 2.2], [310.8, 1.0, -0.4], 0.6)               // the shelf, the books, the first tree
  S(0xffe0b8, 3.5, 5, [315.0, 3.0, 2.6], [314.1, 1.4, 0.45], 0.5)             // the gate and its sign
  S(0xffe0b8, 3, 4, [314.4, 3.8, 1.8], [313.62, 2.75, 0.45], 0.4)             // the hatch: the fourth tree and the hand
  P(0xffdcaa, 1.2, 4, 317.4, 3.35, -0.45)                                     // over the upper passage
  P(0xffd0a0, 0.8, 3.5, 322.75, 1.9, -1.0)                                    // the bulkhead by the stair's foot
  P(0xffc890, 0.5, 1.8, 312.72, 1.15, -0.42)                                  // in the car (move it with the car)

MATERIALS: new EMIT Att16aCarLamp: [1, .8, .52, 4], Att16aLoad1: [1, .62, .16, 0], Att16aLoadOver: [1, .12, .06, 0],
  Att16aRelayLamp: [.35, 1, .45, 3]. Reused PLAIN NewCable, NewSteel (pass 6's new line, same values). New image materials (pass through as maps):
  Att16aAtlas (textures/dl16a_atlas.png, 2048 x 1024: tiles, signs, plates, swatches) and Chalk16a (textures/dl16a_chalk.png,
  1024 x 512 RGBA, alpha BLEND; its name starts with Chalk, so materialFor() keeps its alpha as a decal).
  Reused WORN: WinPlaster WinDado WinLino PigeonWood CrateWood WornIron CastIron HandledBrass PupilWood SafetyYellow
  DustyCream DarkMetal; PLAIN Copper; EMIT AttBulbGlow (Att16aLamps).

SERVICE CABLE (in Att16aSet; NewCable r 0.011, NewSteel clips every 1.05 m, two taped joints): in through the wall over DL-16's
partition at (310.15, 1.17, 3.70), along the back wall at z 3.70 (under the beams' 3.74), down into the relay box (x 314.02 ..
314.26, y 1.11 .. 1.2, z 3.40 .. 3.62, by the hatch at the top of the shaft) and out, along the passage over the gate to 321.2,
down the stair's wall parallel to the pitch (1.3 over the nosings) to (322.5, 2.4), level to the corner, then along DL-17's
wall face (x 323.97) to y 0.63, into the wall over its doorway (a gland). All behind the lane.

DEVIATIONS: the call push's position (see Att16aCallPush). Otherwise none from the build sheet's numbers. Interpretations: the bell push is at z 0.6 world with the car at the bottom
(0.55 above the car floor); the stair's 12th tread is the floor (tops 2.2 .. 0.0); the gauge's plate sits 12 mm proud of the
header (lenses at y -0.559); the passage railing's posts stand on its front channel at y -0.29.
"""
