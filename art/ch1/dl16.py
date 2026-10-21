"""Chapter 1 Attendance, DL-16 After the Bell (game x 264.0 to 280.0). Design: docs/chapter1_part2_plan.md (DL-16).

The dismissal corridor. The back wall (face y 1.4) carries a big faded playground mural (a straight tree, swings, a
smiling sun, a line of children holding hands, a slide, a picket fence with its gate open) and a newer painted arrow,
PLAYGROUND ->, that points at the far end of the corridor. The figures' rail (two low rails at y 0.55, top 0.03, in a
timber floor channel) comes in from DL-15's flap at 263.9 and runs along the wall: past the crossing lever at 266.0,
over the light well (267.9 to 269.9) on a bascule bridge, and into the bottom bay of a tall storage rack of folded
teaching figures, dozens of them, hung on hooks like coats. Two hooks in the bay hang empty (R. ABEL, T. ORME). The
rack's counterweight stands across the lane after it; behind that, the doorway on into DL-17.

Called by build_attendance.py as build_set(dl01, m, coll), in final world coordinates.
Blender (x, y, z) is the game's (x, z, -y): +y is away from the camera, z is up. The lane is y = 0, the floor z = 0.

What the game moves (origin = pivot, world coordinates; REPORT at the bottom has the numbers):
    Att16Lever    the crossing lever; origin on its floor pivot; built upright; pulled = handle toward +x
    Att16Bridge   the bascule leaf over the well; origin on its far hinge (269.9, 0.3, 0); built DOWN (spanning)
    Att16Latch    the hook on the far post; origin on its pivot; built UP; the game swings it down onto the deck
    Att16CW       the rack's counterweight; origin at its bottom centre (278.5, 0, 0); built resting on the floor
Static: Att16Set (the corridor, the well, the lever's frame, the fence, the bench), Att16Rack (the rack, its hooks,
labels and dust sheet), Att16RackFig.NN (linked duplicates of one folded figure mesh), Att16BayFig.0/1 (two figures on
stands already hung in the bay), Att16Lamps (EMIT AttGlobeLamp), Att16PitGlow (EMIT, the boiler's peep-hole in the
well), Att16Speaker (an empty at the tannoy's horn mouth, the emitter for att_bell).
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
COMMON = os.path.join(HERE, '..', 'common')
I4 = Matrix.Identity(4)

# =====================================================================================================================
# Layout (Blender world; game x = x)
# =====================================================================================================================
X0, X1 = 263.9, 280.0          # DL-15's partition ends at 263.9; DL-17 starts at 280
END_X = 279.6                  # the end partition (279.6 .. 280.0) with the doorway on
WALL_Y, WALL_Y2 = 1.4, 1.6     # the back wall's face and back
CEIL = 3.0
FLOOR_FRONT, CEIL_FRONT = -1.6, -1.0
DADO = 1.0
RAIL_Y, RAIL_HALF, RAIL_TOP = 0.55, 0.08, 0.03   # as DL-15: rails at y 0.47 / 0.63, top 0.03
CHAN = (0.39, 0.71)            # the timber channel strip the rails lie in (DL-15's)
RAIL_X0 = 264.0                # DL-15's floor rail ends here; ours continues from it
LEVER = (266.0, 0.35, 0.0)     # the crossing lever's pivot
LEVER_LEN = 0.6                # the handle's height
PIT = (267.9, 269.9)           # the light well
PIT_FLOOR = -1.6
FENCE_Y = 1.0                  # the well's fence (the back wall of the well below it)
BRIDGE_Y = (-0.3, 0.9)
HINGE = (269.9, 0.3, 0.0)      # Att16Bridge's origin
TAIL = (269.9, 270.65, -0.4, 1.0, -0.8)    # the tail chamber under the floor plate: x0, x1, y0, y1, floor
LATCH = (270.06, 0.8, 0.12)    # Att16Latch's pivot
LATCH_LEN = 0.52
POST = (269.98, 270.14, 0.86, 0.98)        # the far post (x0, x1, y0, y1)
RACK = (273.6, 277.6)
RACK_Y = (0.6, 1.4)
RACK_TOP = 2.92
BAY = (274.6, 276.6)
BAY_HEAD = (1.6, 1.7)
TIERS = (0.58, 1.14, 1.70, 2.26, 2.82)     # the hook bars' heights (tier 1 at the bottom .. tier 5 at the top)
ROWS = (0.80, 1.08)                        # front row, back row
BAY_BAR_Z = 1.56
BAY_HOOKS = (274.95, 275.45, 275.95, 276.35)   # 274.95 (R. ABEL) and 275.45 (T. ORME) hang empty
HOOK_CATCH_Z = 1.295
FIG_HANG_Z = 0.34              # a figure's origin (DL-15's: on the rail top under its bogie) when it hangs from a bay hook
CW = (277.8, 279.2, -0.25, 0.25, 1.5)
CW_LIFT = 2.0
SHEAVE = (277.675, 0.12, 2.75, 0.1)        # x, y, z, r: the counterweight chain's sheave under the ceiling
CW_HOLE = (277.72, 279.28, -0.34, 0.34)    # the ceiling's slot the counterweight rises into
DOOR = (END_X, X1, -0.35, 0.45, 2.1)       # x0, x1, y0, y1, head
TANNOY = (265.4, WALL_Y - 0.002, 2.5)
LAMPS = (265.0, 270.05, 275.05)
DEAD_LAMP = 267.6
GLOBE_Z = 2.62
BENCH = (270.9, 272.5, 1.0, 1.36, 0.32)

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
    'Concrete': dict(base=[.075, .074, .07], dirt=[.035, .034, .03], chip=[.12, .115, .105], rough=.92, chipRough=.9, metal=0, grime=1.3, chipScale=9, chipAmt=.7, dust=[.11, .105, .095], dustAmt=.5, streak=.5),
    'SafetyYellow': dict(base=[.55, .42, .06], dirt=[.2, .16, .05], chip=[.07, .068, .062], rough=.8, chipRough=.9, metal=0, grime=4, chipScale=10, chipAmt=.55, dustAmt=.6),
    'LeverRed': dict(base=[.45, .05, .03], dirt=[.2, .04, .02], chip=[.08, .07, .06], rough=.5, chipRough=.6, metal=.1, grime=20, chipScale=60, chipAmt=.7),
    'DustyCream': dict(base=[.5, .46, .35], dirt=[.3, .26, .18], chip=[.03, .027, .022], rough=.85, chipRough=.55, metal=0, grime=4, chipScale=24, chipAmt=.64, dust=[.56, .54, .48], dustAmt=.95, streak=.4),
    'DarkMetal': dict(base=[.017, .016, .014], dirt=[.03, .024, .016], chip=[.075, .068, .055], rough=.72, chipRough=.45, metal=.25, grime=5, chipScale=34, chipAmt=.78, dust=[.075, .072, .062], dustAmt=.7),
}
GAME_PLAIN = {'Brass': ((.45, .32, .12), .45, .8), 'Copper': ((.55, .3, .18), .35, 1.0)}
GAME_EMIT = {'AttGlobeLamp': ((1.0, 0.86, 0.62), 3.0)}
NEW_EMIT = {'Att16PitGlow': ((1.0, 0.42, 0.14), 2.2)}      # new: the boiler's peep-hole down the well
MURAL_PNG = 'dl16_mural.png'                                # new: Att16Mural (image material, passes through)


def _worn_kw(g):
    return dict(base=tuple(g['base']), dirt=tuple(g['dirt']), chip=tuple(g['chip']), rough=g['rough'],
                chip_rough=g['chipRough'], metallic=g['metal'], dust=tuple(g.get('dust', (0.10, 0.095, 0.08))),
                grime_scale=g['grime'], chip_scale=g['chipScale'], chip_amount=g['chipAmt'],
                streaks=g.get('streak', 0.5), dust_amount=g.get('dustAmt', 0.6))


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
    if name == 'Att16Mural':
        mt, nt, bsdf = d17._new_material(name)
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(os.path.join(TEX, MURAL_PNG), check_existing=True)
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = 0.85
        return mt
    vp = _voice_props()
    if vp is not None:
        return vp.material(name)
    raise KeyError(name)


def _voice_props():
    if not os.path.exists(os.path.join(COMMON, 'VOICE_PROPS_READY')):
        return None
    if COMMON not in sys.path:
        sys.path.insert(0, COMMON)
    import voice_props
    return voice_props


# =====================================================================================================================
# The texture: the mural (top 784 rows) and an atlas of plates, labels and swatches (4096 x 1024, dl16_mural.png)
# =====================================================================================================================
TW, TH = 4096, 1024
MURAL_X0, MURAL_X1 = X0, 273.6
PPM = TW / (MURAL_X1 - MURAL_X0)           # 422 px per metre
MURAL_H = 784
MURAL_Z0 = 1.04
MURAL_Z1 = MURAL_Z0 + MURAL_H / PPM        # 2.897
LABELS = ('models', 'class1', 'class2', 'class3', 'class4', 'class5', 'class6')
CELLS = {name: (448 * k, 784, 448 * (k + 1), 880) for k, name in enumerate(LABELS)}
CELLS.update({
    'workshop': (3136, 784, 3584, 880),
    'tagA': (3584, 784, 3752, 880), 'tagB': (3752, 784, 3920, 880), 'tag0': (3920, 784, 4088, 880),
    'hold': (0, 880, 576, 1024), 'keepclear': (576, 880, 1152, 1024), 'cwsign': (1152, 880, 1728, 1024),
    'sheet': (1728, 880, 2496, 1024),
})
SWATCH = {'sw_wood': (104, 74, 46), 'sw_iron': (38, 37, 35), 'sw_brass': (170, 132, 64), 'sw_dark': (6, 6, 6),
          'sw_cream': (196, 186, 160), 'sw_chalk': (214, 210, 198), 'sw_glass': (70, 74, 72), 'sw_red': (120, 40, 30),
          'sw_rust': (90, 52, 30), 'sw_bag': (40, 52, 84), 'sw_canvas': (178, 172, 156), 'sw_string': (184, 172, 140),
          'sw_rubber': (30, 28, 26), 'sw_lag': (150, 142, 120)}
for _k, _n in enumerate(SWATCH):
    _c, _r = _k % 25, _k // 25
    CELLS[_n] = (2496 + 64 * _c, 880 + 64 * _r, 2560 + 64 * _c, 944 + 64 * _r)


def cell_uv(name):
    x0, y0, x1, y1 = CELLS[name]
    return x0 / TW, 1 - y1 / TH, x1 / TW, 1 - y0 / TH


def cell_mid(name):
    u0, v0, u1, v1 = cell_uv(name)
    return (u0 + u1) / 2, (v0 + v1) / 2


def mural_uv(x, z):
    return (x - MURAL_X0) / (MURAL_X1 - MURAL_X0), 1 - (MURAL_Z1 - z) * PPM / TH


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


def _lerp(a, b, t):
    t = max(0.0, min(1.0, t))
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


def _fade(img, seed, grey=(140, 136, 124), k=0.3, warm=(1.0, 0.95, 0.84), dust=0.12):
    """Sun-faded, varnish-yellowed, dusty: the school's colours dimmed toward grey."""
    import numpy as np
    from PIL import Image
    a = np.asarray(img.convert('RGB')).astype(float)
    a = a * (1 - k) + np.array(grey) * k
    a *= np.array(warm)
    n = _noise(a.shape[1], a.shape[0], 8, seed)
    a = a * (1 - dust * (n[..., None] - 0.5) * 2) + 16 * dust * (n[..., None] > 0.63)
    return Image.fromarray(np.clip(a, 0, 255).astype('uint8'), 'RGB')


def mx(x):
    return (x - MURAL_X0) * PPM


def mz(z):
    return (MURAL_Z1 - z) * PPM


def _child(d, x, feet, h, body, hair, rnd, arms=None, skirt=True, face=True):
    """A naive painted child, `h` metres tall, feet at `feet` (z); returns its hands' pixel positions."""
    s = h / 0.5
    cx = mx(x)
    fy = mz(feet)
    hr = 0.062 * s * PPM
    head_c = (cx, mz(feet + h) + hr)
    leg = 0.17 * s * PPM
    hip_y = fy - leg
    sh_y = hip_y - 0.16 * s * PPM
    skin = (226, 188, 150)
    for dx in (-0.035, 0.035):                                          # legs and shoes
        lx = cx + dx * s * PPM
        d.line((lx, hip_y, lx, fy - 6), fill=skin if skirt else body, width=int(0.028 * s * PPM))
        d.ellipse((lx - 0.03 * s * PPM, fy - 12, lx + 0.03 * s * PPM + 4, fy + 2), fill=(52, 40, 34))
    w0, w1 = 0.06 * s * PPM, (0.13 if skirt else 0.075) * s * PPM
    d.polygon([(cx - w0, sh_y), (cx + w0, sh_y), (cx + w1, hip_y + (6 if skirt else 0)), (cx - w1, hip_y + (6 if skirt else 0))], fill=body)
    hands = [(cx - 0.17 * s * PPM, sh_y + 0.12 * s * PPM), (cx + 0.17 * s * PPM, sh_y + 0.12 * s * PPM)]
    if arms == 'up':
        hands = [(cx - 0.12 * s * PPM, sh_y - 0.14 * s * PPM), (cx + 0.12 * s * PPM, sh_y - 0.14 * s * PPM)]
    for hx, hy in hands:
        d.line((cx + (6 if hx > cx else -6), sh_y + 6, hx, hy), fill=body, width=int(0.024 * s * PPM))
        d.ellipse((hx - 6, hy - 6, hx + 6, hy + 6), fill=skin)
    d.ellipse((head_c[0] - hr, head_c[1] - hr, head_c[0] + hr, head_c[1] + hr), fill=skin)
    d.chord((head_c[0] - hr - 2, head_c[1] - hr - 3, head_c[0] + hr + 2, head_c[1] + hr * 0.7), 180, 360, fill=hair)
    if rnd.random() < 0.5:                                             # bunches or a fringe
        d.ellipse((head_c[0] - hr - 10, head_c[1] - 6, head_c[0] - hr + 6, head_c[1] + 12), fill=hair)
        d.ellipse((head_c[0] + hr - 6, head_c[1] - 6, head_c[0] + hr + 10, head_c[1] + 12), fill=hair)
    if face:
        for ex in (-0.35, 0.35):
            d.ellipse((head_c[0] + ex * hr - 3, head_c[1] - 3, head_c[0] + ex * hr + 3, head_c[1] + 3), fill=(40, 34, 30))
        d.arc((head_c[0] - hr * 0.45, head_c[1] - hr * 0.2, head_c[0] + hr * 0.45, head_c[1] + hr * 0.55), 20, 160, fill=(150, 60, 50), width=3)
    return hands


def paint_mural(rnd):
    """The playground, painted by the school long ago at child height, then the newer arrow over its sky."""
    import numpy as np
    from PIL import Image, ImageDraw
    W, H = TW, MURAL_H
    hz = mz(1.62)                                                      # the horizon
    a = np.zeros((H, W, 3))
    t = np.clip(np.arange(H) / hz, 0, 1)[:, None]
    sky = np.array([104, 150, 186]) * (1 - t ** 1.3) + np.array([188, 204, 200]) * t ** 1.3
    a[:] = sky[:, None, :]
    g = np.clip((np.arange(H) - hz) / (H - hz), 0, 1)[:, None]
    grass = np.array([120, 158, 82]) * (1 - g) + np.array([78, 118, 58]) * g
    a[int(hz):] = grass[int(hz):, None, :]
    img = Image.fromarray(np.clip(a, 0, 255).astype('uint8'))
    d = ImageDraw.Draw(img)
    for _ in range(4200):                                              # brush strokes in the sky
        y = rnd.uniform(0, hz - 4)
        x = rnd.uniform(-60, W)
        c = _lerp((104, 150, 186), (188, 204, 200), (y / hz) ** 1.3)
        j = rnd.randint(-10, 10)
        d.line((x, y, x + rnd.uniform(40, 120), y + rnd.uniform(-5, 5)), fill=(c[0] + j, c[1] + j, c[2] + j), width=rnd.randint(5, 11))
    hills = [(0, hz + 4)]                                              # far hills
    for k in range(29):
        hills.append((k * W / 28, hz - 18 - 22 * math.sin(k * 0.9 + 1.3) ** 2))
    hills.append((W, hz + 4))
    d.polygon(hills, fill=(118, 148, 140))
    for _ in range(3800):                                              # grass tufts
        x, y = rnd.uniform(0, W), rnd.uniform(hz + 6, H)
        c = _lerp((120, 158, 82), (78, 118, 58), (y - hz) / (H - hz))
        j = rnd.randint(-14, 10)
        d.line((x, y, x + rnd.uniform(-5, 5), y - rnd.uniform(8, 18)), fill=(c[0] + j, c[1] + j, c[2] + j), width=3)
    # the path across the grass to the gate, sandy
    pts_top = [(mx(x), mz(1.2 + 0.03 * math.sin(x * 2.1))) for x in np.linspace(MURAL_X0, MURAL_X1, 30)]
    pts_bot = [(mx(x), mz(1.07)) for x in np.linspace(MURAL_X1, MURAL_X0, 30)]
    d.polygon(pts_top + pts_bot, fill=(196, 176, 128))
    for _ in range(500):
        x = rnd.uniform(0, W)
        y = rnd.uniform(mz(1.18), mz(1.08))
        d.ellipse((x - 3, y - 2, x + 3, y + 2), fill=(170, 150, 108))
    for _ in range(140):                                               # flowers
        x, y = rnd.uniform(0, W), rnd.uniform(hz + 20, mz(1.24))
        r = rnd.uniform(4, 8)
        col = rnd.choice(((232, 220, 170), (226, 196, 84), (214, 120, 120), (236, 236, 236)))
        for k in range(5):
            aa = k * 1.2566
            d.ellipse((x + r * math.cos(aa) - r * 0.6, y + r * math.sin(aa) - r * 0.6, x + r * math.cos(aa) + r * 0.6, y + r * math.sin(aa) + r * 0.6), fill=col)
        d.ellipse((x - 3, y - 3, x + 3, y + 3), fill=(220, 170, 50))
    # clouds: flat-bottomed, white
    for cx, cz, s in ((265.5, 2.6, 1.2), (268.7, 2.66, 1.0), (272.2, 2.75, 0.8), (270.2, 2.0, 0.6)):
        px, py = mx(cx), mz(cz)
        for k in range(6):
            r = s * rnd.uniform(32, 52)
            ox = px + s * (k - 2.5) * 30 + rnd.uniform(-8, 8)
            oy = py - rnd.uniform(0, 30) * s
            d.ellipse((ox - r, oy - r, ox + r, min(oy + r, py + 14)), fill=(226, 230, 226))
    # the sun, with a face
    sx, sy, r = mx(266.95), mz(2.42), 0.17 * PPM
    for k in range(16):
        aa = 2 * math.pi * k / 16 + 0.1
        d.line((sx + (r + 14) * math.cos(aa), sy + (r + 14) * math.sin(aa), sx + (r + 58) * math.cos(aa), sy + (r + 58) * math.sin(aa)),
               fill=(230, 178, 64), width=13)
    d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=(240, 202, 86))
    d.ellipse((sx - r * 0.6, sy - r * 0.62, sx + r * 0.1, sy - r * 0.08), fill=(246, 220, 128))
    for ex in (-0.32, 0.32):
        d.ellipse((sx + ex * r - 7, sy - r * 0.18 - 9, sx + ex * r + 7, sy - r * 0.18 + 9), fill=(70, 50, 30))
    d.arc((sx - r * 0.5, sy - r * 0.25, sx + r * 0.5, sy + r * 0.55), 25, 155, fill=(150, 70, 40), width=7)
    for ex in (-0.55, 0.55):
        d.ellipse((sx + ex * r - 14, sy + r * 0.12 - 9, sx + ex * r + 14, sy + r * 0.12 + 9), fill=(236, 160, 100))
    # birds
    for bx, bz in ((268.1, 2.42), (268.35, 2.5), (270.9, 2.38), (264.9, 2.72)):
        px, py = mx(bx), mz(bz)
        d.arc((px - 22, py - 8, px, py + 12), 200, 340, fill=(60, 64, 70), width=4)
        d.arc((px, py - 8, px + 22, py + 12), 200, 340, fill=(60, 64, 70), width=4)
    # the school's tree: straight and tall (as in DL-14's windows)
    tx = mx(264.45)
    d.rectangle((tx - 16, mz(2.05), tx + 16, mz(1.28)), fill=(106, 78, 50))
    d.ellipse((tx - 0.3 * PPM, mz(2.55), tx + 0.3 * PPM, mz(1.88)), fill=(74, 122, 64), outline=(54, 92, 48), width=6)
    for _ in range(26):
        ox, oy = rnd.uniform(-0.2, 0.2) * PPM, rnd.uniform(-0.22, 0.18) * PPM
        rr = rnd.uniform(14, 30)
        d.ellipse((tx + ox - rr, mz(2.22) + oy - rr, tx + ox + rr, mz(2.22) + oy + rr), fill=rnd.choice(((92, 140, 74), (64, 110, 56))))
    d.ellipse((tx - 50, mz(1.3) - 8, tx + 50, mz(1.3) + 10), fill=(66, 100, 50))
    # the swings: a red A-frame, one child swinging, one seat empty and still moving
    red = (178, 64, 50)
    top = mz(2.15)
    for ax in (265.62, 267.42):
        for dx in (-0.14, 0.14):
            d.line((mx(ax + dx), mz(1.2), mx(ax), top), fill=red, width=15)
    d.line((mx(265.62), top, mx(267.42), top), fill=red, width=18)
    for ax in (265.62, 267.42):
        d.ellipse((mx(ax) - 12, top - 12, mx(ax) + 12, top + 12), fill=(130, 46, 36))
    rope = (90, 76, 58)
    s1x, s1z = 266.12, 1.52
    for dx in (-0.1, 0.1):
        d.line((mx(s1x + dx), top + 8, mx(s1x + dx), mz(s1z)), fill=rope, width=4)
    d.rectangle((mx(s1x - 0.13), mz(s1z) - 4, mx(s1x + 0.13), mz(s1z) + 8), fill=(120, 84, 52))
    _child(d, s1x, s1z - 0.18, 0.42, (70, 104, 170), (60, 42, 30), rnd, arms='up')
    piv = (mx(266.92), top + 8)                                        # the empty one, swung toward the well
    ang = math.radians(28)
    L = (mz(1.6) - top)
    for dx in (-0.1, 0.1):
        px, py = piv[0] + dx * PPM, piv[1]
        d.line((px, py, px + L * math.sin(ang), py + L * math.cos(ang)), fill=rope, width=4)
    sxx, syy = piv[0] + L * math.sin(ang), piv[1] + L * math.cos(ang)
    d.polygon([(sxx - 0.12 * PPM, syy - 6), (sxx + 0.14 * PPM, syy - 18), (sxx + 0.15 * PPM, syy - 4), (sxx - 0.11 * PPM, syy + 8)], fill=(120, 84, 52))
    # children holding hands, in a line across the well's wall: the last one smaller, a little apart
    cols = ((190, 74, 62), (72, 104, 172), (214, 178, 70), (82, 140, 84), (212, 124, 62), (150, 112, 172))
    hairs = ((60, 42, 30), (180, 140, 70), (40, 30, 24), (120, 70, 40), (60, 42, 30), (30, 26, 22))
    xs = [268.05 + k * 0.36 for k in range(5)] + [269.95]
    prev = None
    for k, x in enumerate(xs):
        h = 0.5 if k < 5 else 0.38
        hands = _child(d, x, 1.13, h, cols[k], hairs[k], rnd, skirt=(k % 2 == 0))
        if prev is not None:
            d.line((prev[0], prev[1], hands[0][0], hands[0][1]), fill=(226, 188, 150), width=9)
        prev = hands[1]
    # the slide: a ladder up, a yellow chute down toward the gate, a child at the top
    blue = (70, 98, 150)
    for lx in (270.32, 270.5):
        d.line((mx(lx), mz(1.16), mx(lx + 0.05), mz(1.86)), fill=blue, width=12)
    for k in range(6):
        zz = 1.26 + k * 0.11
        f = (zz - 1.16) / 0.7
        d.line((mx(270.32 + 0.05 * f), mz(zz), mx(270.5 + 0.05 * f), mz(zz)), fill=blue, width=8)
    d.rectangle((mx(270.3), mz(1.9), mx(270.7), mz(1.84)), fill=blue)
    chute = [(270.66, 1.88), (270.95, 1.7), (271.25, 1.47), (271.55, 1.28), (271.85, 1.2)]
    d.line([(mx(x), mz(z)) for x, z in chute], fill=(222, 190, 72), width=40, joint='curve')
    d.line([(mx(x), mz(z) + 22) for x, z in chute], fill=(160, 130, 50), width=8, joint='curve')
    d.line((mx(271.12), mz(1.55), mx(271.12), mz(1.18)), fill=blue, width=10)
    d.line((mx(271.5), mz(1.32), mx(271.5), mz(1.16)), fill=blue, width=10)
    _child(d, 270.5, 1.9, 0.36, (214, 120, 140), (50, 36, 26), rnd, arms='up')
    # the fence and the open gate
    white = (226, 222, 206)
    fz0, fz1 = 1.12, 1.46
    x = 271.95
    while x < MURAL_X1 - 0.02:
        if not (272.58 < x < 273.06):
            px = mx(x)
            d.polygon([(px - 12, mz(fz0)), (px + 12, mz(fz0)), (px + 12, mz(fz1)), (px, mz(fz1 + 0.06)), (px - 12, mz(fz1))], fill=white, outline=(150, 146, 130))
        x += 0.1
    for zz in (1.2, 1.38):
        d.line((mx(271.9), mz(zz), mx(272.55), mz(zz)), fill=white, width=10)
        d.line((mx(273.1), mz(zz), mx(MURAL_X1), mz(zz)), fill=white, width=10)
    for gx in (272.55, 273.08):
        d.rectangle((mx(gx) - 16, mz(1.6), mx(gx) + 16, mz(1.1)), fill=(214, 208, 190), outline=(150, 146, 130), width=3)
        d.ellipse((mx(gx) - 20, mz(1.6) - 22, mx(gx) + 20, mz(1.6) + 14), fill=(214, 208, 190))
    g0, g1 = mx(273.08), mx(273.38)                                     # the gate leaf, swung open toward us
    d.polygon([(g0, mz(1.16)), (g1, mz(1.08)), (g1, mz(1.5)), (g0, mz(1.48))], outline=white, width=9)
    for k in range(1, 4):
        gx = g0 + (g1 - g0) * k / 4
        d.line((gx, mz(1.16) + (mz(1.08) - mz(1.16)) * k / 4, gx, mz(1.48) + (mz(1.5) - mz(1.48)) * k / 4), fill=white, width=7)
    # a painted frame line round the whole
    d.rectangle((2, 2, W - 3, H - 3), outline=(46, 70, 54), width=10)
    img = _fade(img, 1601, k=0.34, dust=0.16)
    d = ImageDraw.Draw(img, 'RGBA')

    # Later: the arrow, painted over the sky in fresher signwriter's paint.
    ax0, ax1, ah = 269.45, 272.86, 273.5
    z0, z1 = 2.32, 2.62
    cream, ink = (228, 214, 170, 255), (138, 44, 34, 255)
    shaft = [(mx(ax0), mz(z1)), (mx(ax1), mz(z1)), (mx(ax1), mz(2.78)), (mx(ah), mz(2.47)), (mx(ax1), mz(2.16)),
             (mx(ax1), mz(z0)), (mx(ax0), mz(z0))]
    d.polygon(shaft, fill=cream)
    d.line(shaft + [shaft[0]], fill=ink, width=10, joint='curve')
    d.text((mx((ax0 + ax1) / 2), mz(2.47)), 'PLAYGROUND', font=_font(118, 'sans-bold'), fill=ink, anchor='mm')
    # Age and children: peeled paint, scuffs at hand and shoe height, a damp stain over the well, a crack.
    for _ in range(26):                                                # flakes of paint gone, showing the plaster
        cx, cy = rnd.uniform(30, W - 30), rnd.uniform(20, H - 20)
        if mx(ax0) - 40 < cx < mx(ah) + 40 and mz(2.8) < cy < mz(2.05):
            continue
        r = rnd.uniform(6, 22)
        pts = [(cx + r * rnd.uniform(0.6, 1.8) * math.cos(t_), cy + r * rnd.uniform(0.3, 0.7) * math.sin(t_)) for t_ in
               [k * 2 * math.pi / 11 for k in range(11)]]
        d.polygon(pts, fill=(184, 176, 154, 200))
        d.line(pts[:6], fill=(120, 110, 90, 90), width=2)
    for _ in range(320):
        x, y = rnd.uniform(0, W), rnd.uniform(mz(1.42), H - 4)
        d.line((x, y, x + rnd.uniform(20, 90), y + rnd.uniform(-6, 6)), fill=(70, 58, 44, rnd.randint(18, 50)), width=rnd.randint(2, 6))
    for _ in range(60):                                                # hand prints of grime by the swings and the gate
        x, y = rnd.uniform(0, W), rnd.uniform(mz(1.75), mz(1.25))
        d.ellipse((x - 9, y - 11, x + 9, y + 11), fill=(60, 50, 40, rnd.randint(16, 34)))
    sx0, sx1 = mx(268.2), mx(269.7)                                    # the damp over the light well
    for _ in range(60):
        x = rnd.uniform(sx0, sx1)
        ln = rnd.uniform(0.2, 1.1) * PPM
        d.line((x, 0, x + rnd.uniform(-6, 6), ln), fill=(92, 80, 52, rnd.randint(14, 34)), width=rnd.randint(6, 20))
    d.ellipse((sx0 - 60, -120, sx1 + 60, 0.45 * PPM), fill=(96, 84, 56, 40))
    pts, x, y = [], mx(270.95), 0
    while y < mz(2.0):
        pts.append((x, y))
        x += rnd.uniform(-10, 10)
        y += rnd.uniform(8, 20)
    d.line(pts, fill=(52, 46, 38, 200), width=3)
    # Mara's mark: a little crooked tree in pencil on the grass by the open gate.
    sys.path.insert(0, os.path.join(HERE, '..', 'dl05'))
    try:
        import build_dl05 as dl05

        def stroke(pts_, weight):
            for _ in range(2):
                q = [(px + rnd.uniform(-1.2, 1.2), py + rnd.uniform(-1.2, 1.2)) for px, py in pts_]
                d.line(q, fill=(40, 40, 48, 190), width=max(2, int(3 * (0.6 + weight * 0.6))), joint='curve')
        dl05._crooked_tree(stroke, mx(273.22), mz(1.14), 0.2 * PPM)
    except ImportError:
        pass
    return _fade(img, 1602, k=0.06, grey=(150, 146, 134), warm=(1.0, 0.98, 0.94), dust=0.1)


def make_texture(path):
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(1600)
    img = Image.new('RGB', (TW, TH), (60, 58, 54))
    img.paste(paint_mural(rnd), (0, 0))
    ink, cream = (30, 28, 24), (214, 204, 176)

    def put(name, tile, k=0.12, dust=0.15):
        x0, y0 = CELLS[name][:2]
        img.paste(_fade(tile, sum(map(ord, name)), k=k, dust=dust), (x0, y0))

    for name in LABELS:                                                # the rack's tier cards, in brass holders
        x0, y0, x1, y1 = CELLS[name]
        t = Image.new('RGB', (x1 - x0, y1 - y0), (206, 196, 164))
        d = ImageDraw.Draw(t)
        d.rectangle((0, 0, x1 - x0 - 1, y1 - y0 - 1), outline=(150, 116, 56), width=9)
        d.rectangle((9, 9, x1 - x0 - 10, y1 - y0 - 10), outline=(120, 96, 50), width=2)
        text = 'MODELS' if name == 'models' else 'CLASS ' + name[-1]
        d.text(((x1 - x0) // 2, (y1 - y0) // 2 + 2), text, font=_font(66, 'carlito'), fill=ink, anchor='mm')
        put(name, t, k=0.16, dust=0.3)
    x0, y0, x1, y1 = CELLS['workshop']
    t = Image.new('RGB', (x1 - x0, y1 - y0), (40, 64, 50))
    d = ImageDraw.Draw(t)
    d.rounded_rectangle((5, 5, x1 - x0 - 6, y1 - y0 - 6), radius=14, outline=cream, width=5)
    d.text(((x1 - x0) // 2, (y1 - y0) // 2 + 2), 'WORKSHOP', font=_font(62, 'carlito'), fill=cream, anchor='mm')
    put('workshop', t)
    for name, who in (('tagA', 'R. ABEL'), ('tagB', 'T. ORME'), ('tag0', None)):
        x0, y0, x1, y1 = CELLS[name]
        t = Image.new('RGB', (x1 - x0, y1 - y0), (200, 186, 150))
        d = ImageDraw.Draw(t)
        d.ellipse((10, 40, 26, 56), fill=(60, 56, 50))
        if who:
            d.text((96, 50), who, font=_font(34, 'hand'), fill=(40, 40, 64), anchor='mm')
        else:
            d.line([(40 + k * 9, 50 + 6 * math.sin(k)) for k in range(12)], fill=(120, 116, 110), width=3)
        put(name, t, k=0.1)
    x0, y0, x1, y1 = CELLS['hold']                                      # the lever's brass plate
    t = Image.new('RGB', (x1 - x0, y1 - y0), (168, 128, 60))
    d = ImageDraw.Draw(t)
    for yy in range(y1 - y0):
        d.line((0, yy, x1 - x0, yy), fill=_lerp((186, 146, 72), (140, 104, 46), yy / (y1 - y0)))
    d.rectangle((4, 4, x1 - x0 - 5, y1 - y0 - 5), outline=(96, 70, 30), width=4)
    d.text(((x1 - x0) // 2, 52), 'HOLD', font=_font(54, 'sans-bold'), fill=(44, 30, 14), anchor='mm')
    d.text(((x1 - x0) // 2, 104), 'UNTIL CLEAR', font=_font(48, 'sans-bold'), fill=(44, 30, 14), anchor='mm')
    for sx_, sy_ in ((20, 20), (x1 - x0 - 20, 20), (20, y1 - y0 - 20), (x1 - x0 - 20, y1 - y0 - 20)):
        d.ellipse((sx_ - 7, sy_ - 7, sx_ + 7, sy_ + 7), fill=(90, 66, 30))
        d.line((sx_ - 5, sy_, sx_ + 5, sy_), fill=(200, 160, 90), width=2)
    put('hold', t, k=0.05, dust=0.1)
    x0, y0, x1, y1 = CELLS['keepclear']                                 # the well's enamel sign
    t = Image.new('RGB', (x1 - x0, y1 - y0), (214, 210, 196))
    d = ImageDraw.Draw(t)
    d.rectangle((6, 6, x1 - x0 - 7, y1 - y0 - 7), outline=(160, 40, 32), width=10)
    d.text(((x1 - x0) // 2, 50), 'LIGHT WELL', font=_font(54, 'sans-bold'), fill=(160, 40, 32), anchor='mm')
    d.text(((x1 - x0) // 2, 104), 'KEEP CLEAR', font=_font(44, 'sans-bold'), fill=(30, 30, 30), anchor='mm')
    for _ in range(14):
        cx, cy, r = rnd.uniform(0, x1 - x0), rnd.uniform(0, y1 - y0), rnd.uniform(3, 9)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(40, 36, 32))
    put('keepclear', t)
    x0, y0, x1, y1 = CELLS['cwsign']                                    # stencilled on the counterweight
    t = Image.new('RGB', (x1 - x0, y1 - y0), (176, 140, 30))
    d = ImageDraw.Draw(t)
    for k in range(-4, 40):
        xx = k * 36
        d.polygon([(xx, 0), (xx + 18, 0), (xx - 2, 30), (xx - 20, 30)], fill=(24, 22, 20))
        d.polygon([(xx, y1 - y0 - 30), (xx + 18, y1 - y0 - 30), (xx - 2, y1 - y0), (xx - 20, y1 - y0)], fill=(24, 22, 20))
    d.rectangle((0, 30, x1 - x0, y1 - y0 - 30), fill=(30, 28, 26))
    d.text(((x1 - x0) // 2, (y1 - y0) // 2), 'COUNTERWEIGHT · STAND CLEAR', font=_font(40, 'carlito'), fill=(196, 160, 46), anchor='mm')
    put('cwsign', t, k=0.2, dust=0.35)
    x0, y0, x1, y1 = CELLS['sheet']                                     # the dust sheet: old cotton, stained
    import numpy as np
    w, h = x1 - x0, y1 - y0
    n = _noise(w, h, 6, 1610)
    folds = 0.5 + 0.5 * np.sin(np.arange(w)[None, :] / w * math.pi * 9 + 3 * n)
    a = np.ones((h, w, 3)) * np.array([186, 180, 162]) * (0.78 + 0.22 * folds)[..., None] * (0.9 + 0.2 * n)[..., None]
    t = Image.fromarray(np.clip(a, 0, 255).astype('uint8'))
    d = ImageDraw.Draw(t)
    for _ in range(7):
        cx, cy, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(10, 34)
        d.ellipse((cx - r, cy - r * 0.7, cx + r, cy + r * 0.7), outline=(140, 120, 84), width=3)
    put('sheet', t, k=0.05, dust=0.3)
    d = ImageDraw.Draw(img)
    for name, rgb in SWATCH.items():
        x0, y0, x1, y1 = CELLS[name]
        d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=rgb)
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    q = img.quantize(255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    q.save(path, optimize=True)


# =====================================================================================================================
# Mesh building
# =====================================================================================================================
class MB:
    """One object being built: faces tagged by material name. Faces flagged 'flat' keep the winding they were built
    with (decals, one-sided in the game); the rest have their normals recalculated outward."""

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
        self.bm.verts.ensure_lookup_table()
        return len(self.bm.verts)

    def since(self, n0):
        self.bm.verts.ensure_lookup_table()
        return self.bm.verts[n0:]

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

    def ico(self, mt, c, r, sub=1, scale=(1, 1, 1), rot=None):
        res = bmesh.ops.create_icosphere(self.bm, subdivisions=sub, radius=1.0)
        M = Matrix.Translation(Vector(c)) @ (rot or I4) @ Matrix.Diagonal((r * scale[0], r * scale[1], r * scale[2], 1.0))
        bmesh.ops.transform(self.bm, matrix=M, verts=res['verts'])
        d17._tag(res['verts'], self.m(mt))
        return res['verts']

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
        """A picture on a wall, facing the camera (-y)."""
        u0, v0, u1, v1 = uvr or cell_uv(cell)
        return self.face(mt, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    def prism_xz(self, mt, pts, y0, y1):
        """A polygon in (x, z), extruded from y0 to y1."""
        bm = self.bm
        f = [bm.verts.new((x, y0, z)) for x, z in pts]
        b = [bm.verts.new((x, y1, z)) for x, z in pts]
        fs = [bm.faces.new(f), bm.faces.new(list(reversed(b)))]
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            fs.append(bm.faces.new((f[j], f[i], b[i], b[j])))
        for fc in fs:
            fc.material_index = self.m(mt)
        return f + b

    def chain(self, mt, a, b, pitch=0.05, R=0.016, r=0.0045, sag=0.0):
        """A taut (or slightly sagging) chain of links from a to b; alternate links turned 90 degrees."""
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
            f = (i + 0.5) / n
            p = a.lerp(b, f) - Vector((0, 0, sag * 4 * f * (1 - f)))
            ax = side if i % 2 else up
            vs = add_torus(self.bm, (0, 0, 0), (0, 0, 1), R, r, mat=self.m(mt), seg=8, rseg=3)
            # stretch each ring along the chain (an oval link)
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


def place(me, name, loc, coll, rot=(0.0, 0.0, 0.0)):
    ob = bpy.data.objects.new(name, me)
    ob.location = Vector(loc)
    ob.rotation_euler = rot
    coll.objects.link(ob)
    return ob


def rails(B, x0, x1, base=0.0):
    """The figures' track, DL-15's profile: two low iron rails (foot, web, head; top base + 0.03)."""
    for yc in (RAIL_Y - RAIL_HALF, RAIL_Y + RAIL_HALF):
        B.box('WornIron', x0, x1, yc - 0.012, yc + 0.012, base, base + 0.008)
        B.box('WornIron', x0, x1, yc - 0.005, yc + 0.005, base + 0.008, base + 0.024)
        B.box('WornIron', x0, x1, yc - 0.009, yc + 0.009, base + 0.024, base + RAIL_TOP)


def channel(B, x0, x1, rail_to=None):
    """The timber channel strip on the floor (DL-15's), and the rails on it."""
    B.box('PigeonWood', x0, x1, CHAN[0], CHAN[1], -0.002, 0.003)
    rails(B, x0, rail_to or x1)


# =====================================================================================================================
# The corridor
# =====================================================================================================================
def build_shell(B):
    # The back wall: dado below, plaster above (the mural is a decal on it); skirting, dado rail, cornice.
    B.box('WinDado', X0, END_X, WALL_Y, WALL_Y2, 0.0, DADO)
    B.box('WinPlaster', X0, END_X, WALL_Y, WALL_Y2, DADO, CEIL)
    B.box('PigeonWood', X0, END_X, WALL_Y - 0.02, WALL_Y, 0.0, 0.12)
    B.box('PigeonWood', X0, END_X, WALL_Y - 0.035, WALL_Y, DADO - 0.02, MURAL_Z0)
    B.box('WinPlaster', X0, END_X, WALL_Y - 0.08, WALL_Y, CEIL - 0.08, CEIL)
    B.box('WinPlaster', X0, END_X, WALL_Y - 0.03, WALL_Y, CEIL - 0.12, CEIL - 0.08)
    # The ceiling, with the slot the counterweight rises into, and its dark shaft above.
    hx0, hx1, hy0, hy1 = CW_HOLE
    B.box('WinPlaster', X0, hx0, CEIL_FRONT, WALL_Y2, CEIL, CEIL + 0.15)
    B.box('WinPlaster', hx1, END_X, CEIL_FRONT, WALL_Y2, CEIL, CEIL + 0.15)
    B.box('WinPlaster', hx0, hx1, CEIL_FRONT, hy0, CEIL, CEIL + 0.15)
    B.box('WinPlaster', hx0, hx1, hy1, WALL_Y2, CEIL, CEIL + 0.15)
    for a, b, c, d in ((hx0 - 0.1, hx0, hy0 - 0.1, hy1 + 0.1), (hx1, hx1 + 0.1, hy0 - 0.1, hy1 + 0.1),
                       (hx0, hx1, hy0 - 0.1, hy0), (hx0, hx1, hy1, hy1 + 0.1)):
        B.box('Att16Mural', a, b, c, d, CEIL + 0.15, 4.85, cell='sw_dark')          # black: lost in the dark above
    B.box('Att16Mural', hx0 - 0.1, hx1 + 0.1, hy0 - 0.1, hy1 + 0.1, 4.85, 4.95, cell='sw_dark')
    # The floor: lino with the rail's channel, cut by the well; the floor plate over the bridge's tail.
    px0, px1 = PIT
    tx0, tx1, ty0, ty1, tz = TAIL
    B.box('WinLino', X0, px0, FLOOR_FRONT, WALL_Y2, -0.2, 0.0)
    B.box('WinLino', tx1, END_X, FLOOR_FRONT, WALL_Y2, -0.2, 0.0)
    channel(B, RAIL_X0, px0 - 0.005)
    channel(B, tx1, BAY[1] - 0.04, rail_to=BAY[1] - 0.12)
    B.box('PigeonWood', END_X, X1, DOOR[2] - 0.02, DOOR[3] + 0.02, -0.2, 0.004)          # the doorway's threshold
    # beside the well's far edge: lino in front of and behind the tail chamber, the iron plate over it
    B.box('WinLino', px1, tx1, FLOOR_FRONT, ty0, -0.2, 0.0)
    B.box('WinLino', px1, tx1, ty1, WALL_Y2, -0.2, 0.0)
    B.box('WornIron', px1, tx1, ty0, ty1, -0.04, 0.0)
    for x in (px1 + 0.2, px1 + 0.45):                                                    # plate seams and bolts
        B.box('CastIron', x - 0.004, x + 0.004, ty0, ty1, -0.0405, 0.0005)
    for x in (px1 + 0.05, tx1 - 0.05):
        for y in (ty0 + 0.05, 0.1, 0.8, ty1 - 0.05):
            B.cyl('CastIron', (x, y, 0.0), (x, y, 0.006), 0.012, seg=6)
    B.box('PigeonWood', px1 + 0.005, tx1, CHAN[0], CHAN[1], 0.0, 0.003)
    rails(B, px1 + 0.005, tx1)
    # The well: thin concrete walls, its floor, the back wall under the service ledge, the tail chamber.
    B.box('Concrete', px0 - 0.15, px0, FLOOR_FRONT, FENCE_Y + 0.15, -1.75, -0.2)
    B.box('Concrete', px1, px1 + 0.15, FLOOR_FRONT, ty0, -1.75, -0.2)
    B.box('Concrete', px1, px1 + 0.15, ty0, FENCE_Y + 0.15, -1.75, tz - 0.15)
    B.box('Concrete', px0 - 0.15, px1 + 0.15, FLOOR_FRONT, FENCE_Y + 0.15, -1.8, PIT_FLOOR)
    B.box('Concrete', px0, px1, FENCE_Y, FENCE_Y + 0.15, PIT_FLOOR, -0.2)
    B.box('Concrete', px0, px1, FENCE_Y, WALL_Y2, -0.2, 0.0)                              # the service ledge
    B.box('Concrete', px1, tx1 + 0.15, ty0 - 0.15, ty1 + 0.15, tz - 0.15, tz)             # the chamber's floor
    B.box('Concrete', tx1, tx1 + 0.15, ty0, ty1, tz, -0.2)                                # and its end
    B.box('Concrete', px1 + 0.15, tx1, ty0 - 0.15, ty0, tz, -0.04)
    B.box('Concrete', px1 + 0.15, tx1, ty1, ty1 + 0.15, tz, -0.04)
    # The well's lips, painted yellow; the ledge's nosing.
    B.box('SafetyYellow', px0 - 0.05, px0, FLOOR_FRONT, FENCE_Y, -0.06, 0.002)
    B.box('SafetyYellow', px1, px1 + 0.05, FLOOR_FRONT, ty0, -0.06, 0.002)
    B.box('SafetyYellow', px1, px1 + 0.05, ty1, FENCE_Y + 0.02, -0.06, 0.002)
    B.box('WornIron', px0, px1, FENCE_Y - 0.01, FENCE_Y + 0.03, -0.08, 0.002)
    # The end partition with the doorway on (dark beyond until DL-17 lights).
    x0, x1, y0, y1, hd = DOOR
    B.box('WinPlaster', x0, x1, y1, WALL_Y2, 0.0, CEIL + 0.15)
    B.box('WinPlaster', x0, x1, y0, y1, hd, CEIL + 0.15)
    B.box('WinDado', x0 - 0.01, x0, y1, WALL_Y, 0.0, DADO)
    for a, b, c, d in ((y1, y1 + 0.07, 0.0, hd + 0.07), (y0, y1 + 0.07, hd, hd + 0.07)):    # the architrave
        B.box('PigeonWood', x0 - 0.025, x0, a, b, c, d)
    B.box('PigeonWood', x0 - 0.02, x1, y0 - 0.025, y0, hd - 0.02, CEIL)                    # the lintel's face
    B.box('PigeonWood', x0 - 0.02, x0 + 0.06, y1, y1 + 0.03, 0.0, hd)                     # the back jamb's lining
    # the hanging sign in front of it
    sx0, sx1, sz0, sz1 = 279.12, 279.68, 2.24, 2.36
    B.box('WornIron', sx0, sx1, y0 - 0.032, y0 - 0.018, sz0, sz1, cell=None)
    B.decal('Att16Mural', sx0 + 0.005, sx1 - 0.005, sz0 + 0.005, sz1 - 0.005, y0 - 0.033, cell='workshop')
    for x in (sx0 + 0.06, sx1 - 0.06):
        B.cyl('WornIron', (x, y0 - 0.025, sz1), (x, y0 - 0.025, CEIL), 0.004, seg=4)


def build_mural(B):
    """The mural: one decal over the plaster, from DL-15's partition to the rack (x 263.9 to 273.6)."""
    y = WALL_Y - 0.002
    xs = [MURAL_X0 + (MURAL_X1 - MURAL_X0) * k / 8 for k in range(9)]
    for a, b in zip(xs, xs[1:]):
        B.face('Att16Mural', [(a, y, MURAL_Z0), (b, y, MURAL_Z0), (b, y, MURAL_Z1), (a, y, MURAL_Z1)],
               [mural_uv(a, MURAL_Z0), mural_uv(b, MURAL_Z0), mural_uv(b, MURAL_Z1), mural_uv(a, MURAL_Z1)])


def build_lever_frame(B):
    """The lever's static parts: a cast base plate on the floor, the notched quadrant behind the lever, a short iron
    standard to its left with the brass plate HOLD UNTIL CLEAR, and the rodding cover to the well."""
    x, y, _z = LEVER
    B.box('CastIron', x - 0.17, x + 0.2, y - 0.045, y + 0.045, 0.0, 0.025)
    for bx in (x - 0.14, x + 0.17):
        B.cyl('CastIron', (bx, y - 0.03, 0.025), (bx, y - 0.03, 0.035), 0.011, seg=6)
    for dy in (-0.032, 0.032):                                                           # the pivot's cheeks
        B.box('CastIron', x - 0.05, x + 0.05, y + dy - 0.008, y + dy + 0.008, 0.0, 0.07)
    # the quadrant: an arc of radius 0.42 round the pivot, from 8 degrees back to 42 degrees forward (toward +x)
    R, n = 0.42, 10
    a0, a1 = math.radians(-8), math.radians(42)
    yq = y + 0.035
    for k in range(n):
        aa, bb = a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n
        pa = (x + R * math.sin(aa), yq, R * math.cos(aa))
        pb = (x + R * math.sin(bb), yq, R * math.cos(bb))
        B.cyl('CastIron', pa, pb, 0.014, seg=4)
        if k % 3 == 1:
            B.box('CastIron', pa[0] - 0.006, pa[0] + 0.006, yq - 0.01, yq + 0.01, pa[2] + 0.012, pa[2] + 0.03)
    B.cyl('CastIron', (x + R * math.sin(a1), yq, R * math.cos(a1)), (x + 0.18, yq, 0.025), 0.012, seg=4)
    B.cyl('CastIron', (x + R * math.sin(a0), yq, R * math.cos(a0)), (x - 0.08, yq, 0.025), 0.012, seg=4)
    # the standard and its plate
    sx = x - 0.3
    B.cyl('CastIron', (sx, y, 0.0), (sx, y, 0.52), 0.016, seg=8)
    B.cyl('CastIron', (sx, y, 0.0), (sx, y, 0.03), 0.045, seg=10)
    B.box('CastIron', sx - 0.17, sx + 0.17, y - 0.03, y - 0.016, 0.39, 0.495)
    B.decal('Att16Mural', sx - 0.16, sx + 0.16, 0.4, 0.485, y - 0.0305, cell='hold')
    # the rodding cover, flush, from the lever to the well
    B.box('WornIron', x + 0.2, PIT[0] - 0.05, y - 0.04, y + 0.04, -0.02, 0.002)


def build_well(B):
    """Down the well: lagged boiler pipes, a valve, a squat boiler front with a glowing peep-hole (Att16PitGlow, its
    own object), rungs in the left wall. Over it, the fence on the service ledge with its sign."""
    px0, px1 = PIT
    # pipes along the back wall, through both side walls
    # (all below the leaf's tail and truss as they swing: the tail reaches z -0.72 at x 269.6..269.9)
    B.cyl('DustyCream', (px0 - 0.1, 0.86, -0.9), (px1 + 0.1, 0.86, -0.9), 0.1, seg=12)
    for x in (px0 + 0.3, px0 + 0.95, px1 - 0.35):
        B.cyl('WornIron', (x - 0.02, 0.86, -0.9), (x + 0.02, 0.86, -0.9), 0.108, seg=12)
    B.cyl('WornIron', (px0 - 0.1, 0.66, -0.87), (px1 + 0.1, 0.66, -0.87), 0.06, seg=10)
    for x in (px0 + 0.6, px1 - 0.6):
        B.cyl('WornIron', (x - 0.025, 0.66, -0.87), (x + 0.025, 0.66, -0.87), 0.085, seg=10)
    B.cyl('Copper', (px0 - 0.1, 0.95, -0.78), (px1 + 0.1, 0.95, -0.78), 0.022, seg=8)
    # a riser up from the boiler, a valve on it
    vx = 269.45
    B.cyl('WornIron', (vx, 0.62, PIT_FLOOR), (vx, 0.62, -1.02), 0.05, seg=10)
    B.cyl('WornIron', (vx, 0.62, -1.02), (vx, 0.86, -0.9), 0.05, seg=10)
    B.cyl('WornIron', (vx, 0.62, -1.25), (vx, 0.5, -1.25), 0.018, seg=6)
    B.torus('LeverRed', (vx, 0.49, -1.25), (0, 1, 0), 0.09, 0.012, seg=14, rseg=4)
    for k in range(4):
        aa = k * math.pi / 2 + 0.4
        B.cyl('LeverRed', (vx, 0.49, -1.25), (vx + 0.09 * math.cos(aa), 0.49, -1.25 + 0.09 * math.sin(aa)), 0.007, seg=4)
    # the boiler's front, low at the back of the well
    bx0, bx1 = 268.05, 268.95
    B.box('CastIron', bx0, bx1, 0.55, FENCE_Y, PIT_FLOOR, -1.0)
    B.box('CastIron', bx0 - 0.03, bx1 + 0.03, 0.52, FENCE_Y, -1.04, -0.98)
    B.cyl('CastIron', ((bx0 + bx1) / 2, 0.55, -1.25), ((bx0 + bx1) / 2, 0.5, -1.25), 0.11, seg=14)
    for k in range(5):                                                                   # the ash door's slots
        x = bx0 + 0.18 + k * 0.13
        B.box('Att16Mural', x - 0.04, x + 0.04, 0.545, 0.55, -1.52, -1.5, cell='sw_dark')
    # rungs in the left wall of the well
    for k in range(5):
        z = -1.35 + k * 0.28
        B.cyl('WornIron', (px0, 0.76, z), (px0 + 0.12, 0.76, z), 0.011, seg=5)
        B.cyl('WornIron', (px0, 0.96, z), (px0 + 0.12, 0.96, z), 0.011, seg=5)
        B.cyl('WornIron', (px0 + 0.12, 0.76, z), (px0 + 0.12, 0.96, z), 0.011, seg=5)
    # the fence: iron railings with spear tops, on the ledge's front edge
    fy = FENCE_Y + 0.02
    for x in (px0 + 0.05, (px0 + px1) / 2, px1 - 0.05):
        B.box('WornIron', x - 0.022, x + 0.022, fy - 0.022, fy + 0.022, 0.0, 1.0)
        B.sphere('WornIron', (x, fy, 1.02), 0.03, seg=8)
    for z in (0.1, 0.92):
        B.box('WornIron', px0 + 0.05, px1 - 0.05, fy - 0.01, fy + 0.01, z, z + 0.03)
    x = px0 + 0.16
    while x < px1 - 0.1:
        B.cyl('WornIron', (x, fy, 0.1), (x, fy, 0.98), 0.008, seg=5)
        B.cyl('WornIron', (x, fy, 0.98), (x, fy, 1.05), 0.016, 0.0, seg=5)
        x += 0.11
    sx = (px0 + px1) / 2 + 0.45
    B.box('WornIron', sx - 0.25, sx + 0.25, fy - 0.03, fy - 0.012, 0.5, 0.64)
    B.decal('Att16Mural', sx - 0.24, sx + 0.24, 0.51, 0.63, fy - 0.031, cell='keepclear')


def build_far_post(B):
    """The fixed ironwork at the far side of the well: the hinge's two bearings either side of the leaf (outside
    the lane), and the back post that carries the latch's pivot and a stop for the raised leaf."""
    hx, hy, hz = HINGE
    for y0, y1 in ((BRIDGE_Y[0] - 0.12, BRIDGE_Y[0] - 0.02), (BRIDGE_Y[1] + 0.02, BRIDGE_Y[1] + 0.075)):
        B.box('CastIron', hx - 0.06, hx + 0.12, y0, y1, -0.22, -0.045)
        B.cyl('CastIron', (hx, y0, hz), (hx, y1, hz), 0.05, seg=12)
    x0, x1, y0, y1 = POST
    B.box('CastIron', x0, x1, y0, y1, 0.0, 1.05)
    B.box('CastIron', x0 - 0.02, x1 + 0.02, y0 - 0.02, y1 + 0.02, 0.0, 0.05)
    B.box('CastIron', x0 - 0.015, x1 + 0.015, y0 - 0.015, y1 + 0.015, 1.05, 1.09)
    lx, ly, lz = LATCH
    B.box('CastIron', lx - 0.04, lx + 0.04, ly + 0.012, y0, lz - 0.04, lz + 0.04)        # the latch's pivot boss
    B.box('CastIron', HINGE[0] + 0.035, x0, BRIDGE_Y[1] - 0.06, y0, 1.0, 1.1)           # the raised leaf's stop
    B.box('SafetyYellow', x0, x1, y0 - 0.002, y1, 0.85, 0.95)


def build_corridor_props(B):
    """Child-height things along the way: a low bench, a peg rail with one PE bag left on it, the tannoy."""
    x0, x1, y0, y1, top = BENCH
    B.box('CrateWood', x0, x1, y0, y1, top - 0.035, top)
    for x in (x0 + 0.08, x1 - 0.08):
        B.box('PigeonWood', x - 0.025, x + 0.025, y0 + 0.03, y1 - 0.03, 0.0, top - 0.035)
    B.box('PigeonWood', x0 + 0.08, x1 - 0.08, y1 - 0.06, y1 - 0.03, 0.08, 0.12)
    # a single plimsoll under it
    B.box('Att16Mural', x0 + 0.5, x0 + 0.72, y0 + 0.1, y0 + 0.18, 0.0, 0.03, cell='sw_rubber')
    B.box('Att16Mural', x0 + 0.52, x0 + 0.7, y0 + 0.11, y0 + 0.17, 0.03, 0.07, cell='sw_canvas')
    # the peg rail above it (below the mural), at a child's reach
    B.box('PigeonWood', x0, x1, WALL_Y - 0.03, WALL_Y, 0.78, 0.9)
    for k in range(6):
        x = x0 + 0.14 + k * 0.265
        B.cyl('WornIron', (x, WALL_Y - 0.03, 0.85), (x, WALL_Y - 0.1, 0.87), 0.008, seg=5)
        B.sphere('WornIron', (x, WALL_Y - 0.1, 0.87), 0.012, seg=6)
    bx = x0 + 0.14 + 3 * 0.265                                                            # the PE bag, still on its peg
    B.cyl('Att16Mural', (bx - 0.004, WALL_Y - 0.09, 0.86), (bx - 0.07, WALL_Y - 0.06, 0.66), 0.004, seg=4, cell='sw_string')
    B.cyl('Att16Mural', (bx + 0.004, WALL_Y - 0.09, 0.86), (bx + 0.07, WALL_Y - 0.06, 0.66), 0.004, seg=4, cell='sw_string')
    vs = B.sphere('Att16Mural', (bx, WALL_Y - 0.07, 0.56), 1.0, seg=8, scale=(0.11, 0.03, 0.12), cell='sw_bag')
    # the tannoy, high on the wall: the bell's speaker
    vp = _voice_props()
    if vp is None:
        print('dl16: voice props not ready; no tannoy')
        return Vector((TANNOY[0], TANNOY[1] - 0.4, TANNOY[2] - 0.15))
    info = vp.tannoy(B, vp.xform(TANNOY, 0.0), tilt=18.0, aim=-35.0, conduit=0.42, conduit_dir=90.0)
    return Vector(info['mouth'])


def build_lamps(B, coll):
    """Globe pendants on short rods (the lit globes are their own object, EMIT AttGlobeLamp); a dead one over the well."""
    for x in LAMPS + (DEAD_LAMP,):
        y = 0.1 if x == LAMPS[2] else 0.0
        B.cyl('WornIron', (x, y, CEIL), (x, y, GLOBE_Z + 0.13), 0.01, seg=6)
        B.cyl('WornIron', (x, y, CEIL), (x, y, CEIL - 0.03), 0.05, seg=10)
        B.cyl('WornIron', (x, y, GLOBE_Z + 0.15), (x, y, GLOBE_Z + 0.11), 0.045, 0.06, seg=10)
    B.sphere('Att16Mural', (DEAD_LAMP, 0.0, GLOBE_Z), 0.12, seg=12, cell='sw_glass')
    L = MB()
    for x in LAMPS:
        L.sphere('AttGlobeLamp', (x, 0.1 if x == LAMPS[2] else 0.0, GLOBE_Z), 0.12, seg=14)
    return L.obj('Att16Lamps', coll)


# =====================================================================================================================
# What the game moves
# =====================================================================================================================
def build_lever(coll):
    """Att16Lever: a signal-box style lever, red, its grip worn bright; origin on the floor pivot. Built upright; the
    game pulls it toward +x (Blender rotation about +y of +35 deg; game rotation.z of -35 deg)."""
    B = MB()
    x, y, z = LEVER
    B.cyl('CastIron', (x, y - 0.026, 0.0), (x, y + 0.026, 0.0), 0.034, seg=12)            # the pivot's boss
    pts = [(x - 0.022, -0.02), (x + 0.022, -0.02), (x + 0.015, LEVER_LEN - 0.07), (x - 0.015, LEVER_LEN - 0.07)]
    B.prism_xz('LeverRed', pts, y - 0.014, y + 0.014)
    B.box('CastIron', x - 0.03, x + 0.03, y - 0.02, y + 0.02, 0.36, 0.44)                 # the catch block on the quadrant
    B.cyl('CastIron', (x + 0.02, y - 0.016, 0.42), (x + 0.02, y - 0.016, LEVER_LEN - 0.04), 0.005, seg=4)   # catch rod
    B.cyl('LeverRed', (x, y, LEVER_LEN - 0.08), (x, y, LEVER_LEN + 0.04), 0.017, seg=10)
    B.cyl('HandledBrass', (x, y, LEVER_LEN - 0.06), (x, y, LEVER_LEN + 0.03), 0.019, seg=10)
    B.sphere('HandledBrass', (x, y, LEVER_LEN + 0.045), 0.024, seg=10)
    B.box('HandledBrass', x + 0.012, x + 0.05, y - 0.012, y + 0.012, LEVER_LEN - 0.07, LEVER_LEN - 0.045)    # the catch handle
    return B.obj('Att16Lever', coll, origin=LEVER)


def build_bridge(coll):
    """Att16Bridge: an iron bascule leaf with a timber deck (top at z 0), lane-deep (y -0.3 .. 0.9), carrying the
    rail. Built DOWN, spanning the well; origin on its hinge at the far end (269.9, 0.3, 0). Under it a queen-post
    truss with taut chain ties; behind the hinge, under the floor plate, its tail with the cast counterweight. The
    game raises it by rotating about +y (Blender) by +90 deg: the free end rises over to stand at x 269.65..269.9."""
    B = MB()
    px0, px1 = PIT
    hx, hy, hz = HINGE
    y0, y1 = BRIDGE_Y
    xa, xb = px0 + 0.03, px1 - 0.01
    # deck planks across the leaf, with gaps
    n = 16
    w = (xb - xa) / n
    for k in range(n):
        B.box('CrateWood', xa + k * w + 0.004, xa + (k + 1) * w - 0.004, y0, y1, -0.05, 0.0)
    B.box('WornIron', xa - 0.01, xa + 0.02, y0, y1, -0.08, 0.002)                       # the free end's nosing
    # the two side girders, fish-bellied, running on past the hinge into the tail
    tail = TAIL[1] - 0.1
    prof = [(xa, -0.05), (tail, -0.05), (tail, -0.3), (hx, -0.3), (268.4, -0.17), (xa, -0.12)]
    for gy in (y0 + 0.02, y1 - 0.02):
        B.prism_xz('CastIron', prof, gy - 0.03, gy + 0.03)
        B.prism_xz('CastIron', [(xa + 0.02, -0.05), (tail, -0.05), (tail, -0.07), (xa + 0.02, -0.07)], gy - 0.06, gy + 0.06)
        for x in (268.3, 268.9, 269.5, hx + 0.2, hx + 0.45):                              # rivet heads along the web
            B.cyl('CastIron', (x, gy - 0.03, -0.1), (x, gy - 0.036, -0.1), 0.009, seg=5)
    for x in (268.3, 268.9, 269.5):                                                      # cross-girders
        B.box('CastIron', x - 0.03, x + 0.03, y0 + 0.05, y1 - 0.05, -0.15, -0.05)
    # the trunnion through the leaf (its stubs run into the fixed bearings either side)
    for a, b in ((y0 - 0.1, y0 + 0.03), (y1 - 0.03, y1 + 0.07)):
        B.cyl('CastIron', (hx, a, hz), (hx, b, hz), 0.035, seg=12)
    # the tail's counterweight: a cast box between the girders, pig weights stacked in it
    B.box('CastIron', hx + 0.22, tail, y0 + 0.05, y1 - 0.05, -0.32, -0.07)
    for k in range(4):
        yy = y0 + 0.15 + k * 0.27
        B.box('WornIron', hx + 0.27, tail - 0.05, yy - 0.1, yy + 0.1, -0.07, -0.06)
    # the queen-post truss under the leaf: two struts and taut chain ties, each side
    s1, s2, sz = 268.55, 269.3, -0.58
    for gy in (y0 + 0.02, y1 - 0.02):
        for sx in (s1, s2):
            B.cyl('CastIron', (sx, gy, -0.1), (sx, gy, sz), 0.016, seg=6)
            B.sphere('CastIron', (sx, gy, sz), 0.026, seg=8)
        B.chain('WornIron', (xa + 0.06, gy, -0.12), (s1, gy, sz))
        B.chain('WornIron', (s1, gy, sz), (s2, gy, sz))
        B.chain('WornIron', (s2, gy, sz), (hx - 0.05, gy, -0.29))
    # the rail on the deck, and the eye the latch drops into
    B.box('PigeonWood', xa + 0.02, xb, CHAN[0], CHAN[1], 0.0, 0.003)
    rails(B, xa + 0.02, xb)
    lx = LATCH[0] - LATCH_LEN - 0.01
    B.box('CastIron', lx - 0.05, lx + 0.05, LATCH[1] - 0.03, LATCH[1] + 0.03, 0.0, 0.006)
    B.torus('CastIron', (lx, LATCH[1], 0.03), (0, 1, 0), 0.026, 0.008, seg=10, rseg=4)
    return B.obj('Att16Bridge', coll, origin=HINGE)


def build_latch(coll):
    """Att16Latch: a hooked iron arm on the far post. Built UP (pointing up from its pivot, the hook's jaw turned
    toward the bridge, -x); origin on its pivot. The game drops it onto the deck: Blender rotation about +y of -90 deg
    (game rotation.z +90 deg) lays it along -x, its jaw down into the eye on the deck at (269.53, 0.8)."""
    B = MB()
    x, y, z = LATCH
    L = LATCH_LEN
    B.cyl('CastIron', (x, y + 0.012, z), (x, y - 0.03, z), 0.028, seg=10)
    B.box('WornIron', x - 0.016, x + 0.016, y - 0.012, y + 0.012, z, z + L)
    B.box('WornIron', x - 0.11, x + 0.016, y - 0.012, y + 0.012, z + L - 0.03, z + L)   # the jaw, toward -x
    B.box('WornIron', x - 0.11, x - 0.08, y - 0.012, y + 0.012, z + L - 0.09, z + L - 0.02)
    B.box('SafetyYellow', x - 0.017, x + 0.017, y - 0.013, y + 0.013, z + 0.18, z + 0.3)
    B.sphere('WornIron', (x, y, z + 0.4), 0.02, seg=6)
    return B.obj('Att16Latch', coll, origin=LATCH)


def build_cw(coll):
    """Att16CW: the rack's counterweight, a cast-iron box 1.4 x 0.5 x 1.5 across the lane, resting on the floor;
    origin at its bottom centre. Its chain rises from a bracket on its back left corner to the sheave under the
    ceiling (the chain moves with it; it slides up out of sight through the ceiling's slot). The game lifts it 2.0."""
    B = MB()
    x0, x1, y0, y1, h = CW
    B.box('CastIron', x0, x1, y0, y1, 0.0, h)
    B.box('CastIron', x0 - 0.0, x1 + 0.0, y0 - 0.025, y1 + 0.025, h - 0.08, h)            # the rim top and bottom
    B.box('CastIron', x0, x1, y0 - 0.025, y1 + 0.025, 0.0, 0.08)
    for x in (x0 + 0.04, (x0 + x1) / 2, x1 - 0.04):                                       # cast ribs on both faces
        B.box('CastIron', x - 0.03, x + 0.03, y0 - 0.02, y0, 0.08, h - 0.08)
        B.box('CastIron', x - 0.03, x + 0.03, y1, y1 + 0.02, 0.08, h - 0.08)
    for x in (x0, x1):                                                                    # the guide shoes
        sx = x - 0.03 if x == x0 else x + 0.0
        for z in (0.1, h - 0.18):
            B.box('WornIron', sx, sx + 0.03, y0 - 0.05, y1 + 0.05, z, z + 0.08)
    B.decal('Att16Mural', x0 + 0.1, x1 - 0.1, 0.95, 1.25, y0 - 0.0215, cell='cwsign')
    B.box('Att16Mural', x0 + 0.08, x1 - 0.08, y0 - 0.022, y0 - 0.02, 0.18, 0.24, cell='sw_rust')
    # bolts along the top rim
    for k in range(8):
        x = x0 + 0.1 + k * (x1 - x0 - 0.2) / 7
        B.cyl('WornIron', (x, y0 - 0.025, h - 0.04), (x, y0 - 0.035, h - 0.04), 0.012, seg=6)
    # the lifting eye on top, and the chain's bracket on the back left corner
    cx = (x0 + x1) / 2
    B.box('CastIron', cx - 0.1, cx + 0.1, -0.06, 0.06, h, h + 0.04)
    B.torus('WornIron', (cx, 0.0, h + 0.09), (0, 1, 0), 0.05, 0.014, seg=12, rseg=4)
    sx, sy, sz, sr = SHEAVE
    cxr = sx + sr                                                                           # the chain's line: the sheave's right tangent
    B.box('WornIron', cxr - 0.012, x0, sy - 0.03, sy + 0.03, h - 0.2, h - 0.08)             # the lug on its left face
    B.torus('WornIron', (cxr, sy, h - 0.06), (1, 0, 0), 0.02, 0.006, seg=8, rseg=3)
    B.chain('WornIron', (cxr, sy, h - 0.04), (cxr, sy, sz))
    return B.obj('Att16CW', coll, origin=((x0 + x1) / 2, 0.0, 0.0))


def build_cw_frame(B):
    """The counterweight's guide frame: four iron angles at its corners, floor to ceiling, outside the lane's walking
    line (y +-0.3), and a head frame at the ceiling; the sheave on a hanger and the chain over it to the rack."""
    x0, x1, y0, y1, h = CW
    for gx0, gx1 in ((x0 - 0.06, x0), (x1, x1 + 0.06)):
        for gy0, gy1 in ((y0 - 0.075, y0 - 0.015), (y1 + 0.015, y1 + 0.075)):
            B.box('WornIron', gx0, gx1, gy0, gy1, 0.0, CEIL)
            B.box('WornIron', gx0 - 0.02, gx1 + 0.02, gy0 - 0.02, gy1 + 0.02, 0.0, 0.015)
    for gy0, gy1 in ((y0 - 0.075, y0 - 0.015), (y1 + 0.015, y1 + 0.075)):
        B.box('WornIron', x0 - 0.06, x1 + 0.06, gy0, gy1, CEIL - 0.08, CEIL)
    B.box('SafetyYellow', x0 - 0.06, x0, y0 - 0.076, y0 - 0.015, 1.9, 2.1)
    B.box('SafetyYellow', x1, x1 + 0.06, y0 - 0.076, y0 - 0.015, 1.9, 2.1)
    # the sheave, hung from the ceiling between the rack and the counterweight
    sx, sy, sz, sr = SHEAVE
    B.torus('WornIron', (sx, sy, sz), (0, 1, 0), sr - 0.015, 0.016, seg=22, rseg=4)
    B.cyl('WornIron', (sx, sy - 0.012, sz), (sx, sy + 0.012, sz), sr - 0.025, seg=18)
    B.cyl('WornIron', (sx, sy - 0.05, sz), (sx, sy + 0.05, sz), 0.022, seg=8)
    for dy in (-0.05, 0.05):
        B.box('WornIron', sx - 0.02, sx + 0.02, sy + dy - 0.008, sy + dy + 0.008, sz, CEIL)
    B.box('WornIron', sx - 0.12, sx + 0.12, sy - 0.08, sy + 0.08, CEIL - 0.02, CEIL)
    # the chain over the top of the sheave and down its left side to the rack's lifting bar
    pts = [(sx + sr * math.cos(math.radians(a)), sz + sr * math.sin(math.radians(a))) for a in range(0, 181, 30)]
    for (ax, az), (bx, bz) in zip(pts, pts[1:]):
        B.chain('WornIron', (ax, sy, az), (bx, sy, bz), pitch=0.045)
    B.chain('WornIron', (sx - sr, sy, sz), (sx - sr, sy, 2.36))
    B.torus('WornIron', (sx - sr, sy, 2.33), (0, 1, 0), 0.025, 0.008, seg=8, rseg=3)
    B.box('WornIron', sx - sr - 0.03, RACK[1] - 0.01, sy - 0.02, RACK_Y[0] + 0.03, 2.28, 2.31)


# =====================================================================================================================
# The rack and its figures
# =====================================================================================================================
def folded_figure_mesh():
    """A teaching figure folded for storage: DL-12's lay figure (the same parts and sizes, low detail), hung by a ring
    between its shoulder blades like a coat on a peg: head bowed, arms hanging to its knees, knees drawn up, shins
    folded back. Origin on the ring (the hook's catch point); it faces +x."""
    B = MB()
    w, j = 'PupilWood', 'CrateWood'
    V = Vector
    Rx = lambda a: Matrix.Rotation(math.radians(a), 4, 'X')
    bm = B.bm
    d17.rounded_box((0.186, 0.11, 0.165), (0, 0.0, -0.08), p=3.0, cuts=1, bm=bm, mat=B.m(w), rot=Rx(10))
    B.ico(j, (0, 0.0, -0.178), 1.0, scale=(0.05, 0.04, 0.03))
    d17.rounded_box((0.158, 0.098, 0.085), (0, 0.004, -0.235), p=3.0, cuts=1, bm=bm, mat=B.m(w))
    B.cyl(j, (0, -0.02, 0.0), (0, -0.06, 0.04), 0.021, seg=5)                            # the neck, bowed
    B.ico(w, (0, -0.1, 0.05), 1.0, sub=2, scale=(0.062, 0.068, 0.085), rot=Rx(-48))      # the head, bowed
    B.torus('WornIron', (0, 0.06, 0.0), (1, 0, 0), 0.016, 0.004, seg=6, rseg=3)           # the ring
    B.box('WornIron', -0.02, 0.02, 0.05, 0.058, -0.04, -0.005)
    for sx in (-1, 1):
        sh = V((sx * 0.112, 0.0, -0.012))
        el = V((sx * 0.124, -0.06, -0.135))
        wr = V((sx * 0.1, -0.165, -0.18))
        B.ico(j, sh, 0.029)
        B.ico(j, el, 0.02)
        B.cyl(w, sh, el, 0.021, 0.018, seg=5)
        B.cyl(w, el, wr, 0.017, 0.014, seg=5)
        hd = (wr - el).normalized()
        hc = wr + hd * 0.035
        B.box(w, hc.x - 0.011, hc.x + 0.011, hc.y - 0.03, hc.y + 0.03, hc.z - 0.022, hc.z + 0.022)
        hip, knee, ank = V((sx * 0.055, -0.005, -0.27)), V((sx * 0.06, -0.18, -0.18)), V((sx * 0.062, -0.13, -0.44))
        B.ico(j, hip, 0.031)
        B.ico(j, knee, 0.026)
        B.cyl(w, hip, knee, 0.036, 0.03, seg=5)
        B.cyl(w, knee, ank, 0.026, 0.021, seg=5)
        B.box(w, ank.x - 0.024, ank.x + 0.024, ank.y - 0.085, ank.y + 0.015, ank.z - 0.034, ank.z)
    B.xform(0, Matrix.Rotation(math.radians(90), 4, 'Z') @ Matrix.Translation((0, -0.06, 0)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new('Att16FoldedFigure')
    bm.to_mesh(me)
    bm.free()
    for n in B.names:
        me.materials.append(mat(n))
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.set_sharp_from_angle(angle=math.radians(35))
    return me


def stand_figure_mesh():
    """The figure as DL-15 builds it (DL-13's pupil(), its castors replaced by a rail bogie on DL-15's gauge), so the
    two already hung in the bay match the two that arrive. Faces +x; origin on the rail top under the bogie's centre."""
    import dl13
    B = MB()
    w, j, st = B.m('PupilWood'), B.m('CrateWood'), B.m('WornIron')
    tmp = bmesh.new()
    dl13.pupil(tmp, 0, 1, 2, 'stand', True)
    gone = [v for v in tmp.verts if v.co.z < 0.0995 or (abs(v.co.z - 0.1) < 1e-4 and v.co.xy.length < 0.05)]
    bmesh.ops.delete(tmp, geom=gone, context='VERTS')
    bmesh.ops.transform(tmp, matrix=Matrix.Rotation(math.radians(90), 4, 'Z'), verts=tmp.verts)
    me = bpy.data.meshes.new('_dl16_tmp')
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
        y = sy * RAIL_HALF
        add_box(bm, (0, y, 0.048), (0.34, 0.018, 0.024), mat=st)
        for sx in (-1, 1):
            x = sx * 0.11
            add_cyl(bm, (x, y - 0.008, 0.03), (x, y + 0.008, 0.03), 0.03, mat=st, seg=10)
            yf = y - sy * 0.011
            add_cyl(bm, (x, yf - 0.003, 0.03), (x, yf + 0.003, 0.03), 0.038, mat=st, seg=10)
    for sx in (-1, 1):
        add_cyl(bm, (sx * 0.11, -RAIL_HALF, 0.03), (sx * 0.11, RAIL_HALF, 0.03), 0.008, mat=st, seg=6)
        add_box(bm, (sx * 0.175, 0, 0.05), (0.012, 0.2, 0.03), mat=st)
        add_cyl(bm, (sx * 0.18, 0, 0.05), (sx * 0.2, 0, 0.05), 0.022, mat=st, seg=8)
    add_box(bm, (0, 0, 0.066), (0.1, 0.18, 0.016), mat=st)
    add_cyl(bm, (0, 0, 0.074), (0, 0, 0.1), 0.032, mat=st, seg=10)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new('Att16StandFigure')
    bm.to_mesh(me)
    bm.free()
    for n in B.names:
        me.materials.append(mat(n))
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.set_sharp_from_angle(angle=math.radians(35))
    return me


RING_DROP = 0.065            # a tier's hooks catch their rings this far below the bar
LABEL_W, LABEL_H = 0.64, 0.137


def rack_slots():
    """Every hook position on the tiers: (section, tier index, row index, x of the hook, y, bar z). Each sub-bay
    between uprights takes three figures a row (a folded figure reaches 0.29 forward of its ring, toward +x)."""
    up = 0.035
    subs = (('L', RACK[0] + 2 * up, BAY[0] - up), ('M', BAY[0] + up, (BAY[0] + BAY[1]) / 2 - up),
            ('M', (BAY[0] + BAY[1]) / 2 + up, BAY[1] - up), ('R', BAY[1] + up, RACK[1] - 2 * up))
    out = []
    rnd = random.Random(1631)
    for name, sx0, sx1 in subs:
        n = int((sx1 - sx0 - 0.29) / 0.3) + 1
        pad = (sx1 - sx0 - 0.29 - 0.3 * (n - 1)) / 2
        for ti, z in enumerate(TIERS):
            for ri, y in enumerate(ROWS):
                if name == 'M' and ti < 3:
                    continue                      # the bay: open below its header
                if name == 'L' and ti < 2 and ri == 0:
                    continue                      # the rail runs in front of the left section's low tiers
                for k in range(n):
                    out.append((name, ti, ri, sx0 + pad + 0.3 * k + rnd.uniform(-0.012, 0.012), y, z))
    return out


LABEL_AT = {('M', 4): 'models', ('L', 3): 'class1', ('M', 3): 'class2', ('R', 3): 'class3',
            ('L', 2): 'class4', ('R', 2): 'class5'}


def build_rack(coll, folded, standing):
    """Att16Rack: a tall timber rack against the back wall, cantilevered off five uprights so its low front is open
    where the rail runs; hook bars on every tier; tier cards; the bay (274.6 .. 276.6) with its header CLASS 6 and four
    hooks over the rail; the rail's buffer; a dust sheet half pulled over the top tier's right end."""
    B = MB()
    rnd = random.Random(1630)
    x0, x1 = RACK
    fy0, wy = RACK_Y[0], WALL_Y - 0.02
    ups = (x0 + 0.035, BAY[0], (BAY[0] + BAY[1]) / 2, BAY[1], x1 - 0.035)
    for x in ups:                                                                       # uprights at the wall
        B.box('PigeonWood', x - 0.035, x + 0.035, wy - 0.1, wy, 0.0, RACK_TOP)
    fronts = {x0 + 0.035: 1.62, BAY[0]: 1.62, BAY[1]: 0.0, x1 - 0.035: 0.0}
    for x, zb in fronts.items():                                                        # front posts (low ones only clear of the rail)
        B.box('PigeonWood', x - 0.03, x + 0.03, fy0, fy0 + 0.06, zb, RACK_TOP)
    B.box('PigeonWood', x0, x1, fy0, fy0 + 0.06, RACK_TOP - 0.07, RACK_TOP)
    # arms at each tier, out from each upright to the front (or short, where the rail passes)
    for x in ups:
        for ti, z in enumerate(TIERS):
            front = fy0
            if x in (x0 + 0.035, BAY[0]) and ti < 2:
                front = 0.93
            if x == (BAY[0] + BAY[1]) / 2 and ti < 3:
                continue
            B.box('PigeonWood', x - 0.025, x + 0.025, front, wy - 0.1, z + 0.012, z + 0.07)
            if front < 0.9:
                B.prism_xz('PigeonWood', [(x - 0.02, z + 0.012), (x + 0.02, z + 0.012), (x + 0.02, z - 0.16), (x - 0.02, z - 0.16)], wy - 0.32, wy - 0.1)
    # front rails at each tier where the front is closed (tier cards hang on them)
    for ti, z in enumerate(TIERS):
        for sx0, sx1, ok in ((x0, BAY[0], ti >= 2), (BAY[0], BAY[1], ti >= 3), (BAY[1], x1, True)):
            if ok and ti < 4:
                B.box('PigeonWood', sx0, sx1, fy0, fy0 + 0.04, z + 0.035, z + 0.07)
    # the bay's header, its card, the hook bar and four drop hooks over the rail; the rail's buffer at the back
    hz0, hz1 = BAY_HEAD
    B.box('PigeonWood', BAY[0] - 0.03, BAY[1] + 0.03, fy0, fy0 + 0.08, hz0, hz1)
    cx = (BAY[0] + BAY[1]) / 2
    B.box('HandledBrass', cx - LABEL_W / 2 - 0.012, cx + LABEL_W / 2 + 0.012, fy0 - 0.012, fy0, hz0 - 0.005, hz0 + LABEL_H + 0.005)
    B.decal('Att16Mural', cx - LABEL_W / 2, cx + LABEL_W / 2, hz0, hz0 + LABEL_H, fy0 - 0.013, cell='class6')
    for x in (BAY[0] + 0.1, cx, BAY[1] - 0.1):
        B.box('WornIron', x - 0.012, x + 0.012, RAIL_Y - 0.01, fy0 + 0.04, BAY_BAR_Z - 0.01, hz0 + 0.02)
    B.cyl('WornIron', (BAY[0] + 0.05, RAIL_Y, BAY_BAR_Z), (BAY[1] - 0.05, RAIL_Y, BAY_BAR_Z), 0.014, seg=8)
    for k, hx in enumerate(BAY_HOOKS):
        B.cyl('WornIron', (hx - 0.022, RAIL_Y, BAY_BAR_Z), (hx - 0.022, RAIL_Y, HOOK_CATCH_Z + 0.025), 0.007, seg=5)
        jpts = [(hx - 0.022 * math.cos(math.radians(a)), HOOK_CATCH_Z + 0.025 - 0.022 * math.sin(math.radians(a))) for a in range(0, 181, 30)]
        jpts.append((hx + 0.022, HOOK_CATCH_Z + 0.05))
        for (ax, az), (bx, bz) in zip(jpts, jpts[1:]):
            B.cyl('WornIron', (ax, RAIL_Y, az), (bx, RAIL_Y, bz), 0.006, seg=5)
        tag = ('tagA', 'tagB', 'tag0', 'tag0')[k]                                        # a card tag on each drop
        tz = BAY_BAR_Z - 0.1
        B.cyl('Att16Mural', (hx - 0.022, RAIL_Y - 0.008, tz + 0.03), (hx - 0.03, RAIL_Y - 0.01, tz + 0.005), 0.002, seg=3, cell='sw_string')
        B.face('Att16Mural', [(hx - 0.075, RAIL_Y - 0.012, tz - 0.04), (hx + 0.005, RAIL_Y - 0.012, tz - 0.04),
                         (hx + 0.005, RAIL_Y - 0.012, tz + 0.005), (hx - 0.075, RAIL_Y - 0.012, tz + 0.005)],
               [(cell_uv(tag)[0], cell_uv(tag)[1]), (cell_uv(tag)[2], cell_uv(tag)[1]), (cell_uv(tag)[2], cell_uv(tag)[3]),
                (cell_uv(tag)[0], cell_uv(tag)[3])])
    B.box('CastIron', BAY[1] - 0.12, BAY[1] - 0.04, RAIL_Y - 0.11, RAIL_Y + 0.11, 0.003, 0.12)   # the buffer stop
    B.box('CrateWood', BAY[1] - 0.14, BAY[1] - 0.12, RAIL_Y - 0.09, RAIL_Y + 0.09, 0.03, 0.11)
    # every hook on the tiers, and a folded figure on most of them
    slots = rack_slots()
    figs = []
    label_x = {}
    for (sec, ti), cell in LABEL_AT.items():
        sx0, sx1 = {'L': (x0, BAY[0]), 'M': (BAY[0], BAY[1]), 'R': (BAY[1], x1)}[sec]
        label_x[(sec, ti)] = (sx0 + sx1) / 2
    bars = {}
    for sec, ti, ri, hx, y, z in slots:
        bars.setdefault((sec, ti, ri, y, z), []).append(hx)
    for (sec, ti, ri, y, z), xs in bars.items():
        sx0, sx1 = {'L': (x0, BAY[0]), 'M': (BAY[0], BAY[1]), 'R': (BAY[1], x1)}[sec]
        B.cyl('WornIron', (sx0 + 0.03, y, z), (sx1 - 0.03, y, z), 0.011, seg=6)
        for hx in xs:
            B.cyl('WornIron', (hx, y, z), (hx, y, z - RING_DROP + 0.012), 0.005, seg=4)
            B.cyl('WornIron', (hx, y, z - RING_DROP + 0.012), (hx + 0.022, y, z - RING_DROP - 0.004), 0.005, seg=4)
            if rnd.random() < 0.07:
                continue                                                                   # a hook here and there empty
            figs.append((hx, y, z - RING_DROP))
    for (sec, ti), cell in LABEL_AT.items():                                               # the tier cards
        lx = label_x[(sec, ti)]
        z = TIERS[ti] + 0.07 if ti < 4 else RACK_TOP - 0.1
        y = fy0 - 0.001
        B.box('HandledBrass', lx - LABEL_W / 2 - 0.012, lx + LABEL_W / 2 + 0.012, y - 0.012, y, z - 0.005, z + LABEL_H + 0.005)
        B.decal('Att16Mural', lx - LABEL_W / 2, lx + LABEL_W / 2, z, z + LABEL_H, y - 0.013, cell=cell)
    # the dust sheet, half pulled over the top tier's right end: over the top, down the front in folds
    build_sheet(B, rnd)
    ob = B.obj('Att16Rack', coll)
    out = [ob]
    for k, (hx, y, z) in enumerate(figs):
        o = place(folded, 'Att16RackFig.%02d' % k, (hx, y, z), coll,
                  rot=(rnd.uniform(-0.03, 0.03), rnd.uniform(-0.05, 0.05), rnd.uniform(-0.2, 0.2)))
        out.append(o)
    for k, hx in enumerate(BAY_HOOKS[2:]):                                                 # the two already hung in the bay
        out.append(place(standing, 'Att16BayFig.%d' % k, (hx, RAIL_Y, FIG_HANG_Z), coll, rot=(0.0, 0.0, rnd.uniform(-0.12, 0.12))))
    return out, len(figs)


def build_sheet(B, rnd):
    """A grid draped from the back of the rack's top, over its front edge, down the front in folds to a ragged hem."""
    xa, xb = 276.05, RACK[1] + 0.03
    nx, nt = 18, 10
    top = RACK_TOP + 0.015
    path = [(WALL_Y - 0.08, top), (0.95, top - 0.01), (RACK_Y[0] - 0.02, top + 0.005)]
    u0, v0, u1, v1 = cell_uv('sheet')
    grid = []
    for i in range(nx + 1):
        f = i / nx
        x = xa + (xb - xa) * f
        hem = 2.22 + 0.16 * math.sin(f * 5.1 + 0.7) + 0.08 * rnd.random() + 0.12 * (1 - f) ** 2 * 2
        drop = top - hem
        col = []
        pts = path + [(RACK_Y[0] - 0.03 - 0.02 * math.sin(f * 17 + 1.3), top - drop * k / 4) for k in range(1, 5)]
        for k, (y, z) in enumerate(pts):
            fold = 0.025 * math.sin(f * 23.0 + k * 0.6) if k >= 3 else 0.0
            sag = -0.03 * math.sin(f * math.pi * 6) ** 2 if k in (1,) else 0.0
            col.append(((x, y + fold, z + sag), (u0 + (u1 - u0) * f, v1 - (v1 - v0) * k / (len(pts) - 1))))
        grid.append(col)
    for i in range(nx):
        for k in range(len(grid[0]) - 1):
            q = [grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k], grid[i][k]]
            B.face('Att16Mural', [p[0] for p in q], [p[1] for p in q], flat=False)


# =====================================================================================================================
def tris(ob):
    if ob.type != 'MESH':
        return 0
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def build_set(dl01, m, coll):
    os.makedirs(TEX, exist_ok=True)
    make_texture(os.path.join(TEX, MURAL_PNG))
    B = MB()
    build_shell(B)
    build_mural(B)
    build_lever_frame(B)
    build_well(B)
    build_far_post(B)
    build_cw_frame(B)
    mouth = build_corridor_props(B)
    objs = [build_lamps(B, coll)]
    objs.insert(0, B.obj('Att16Set', coll))
    G = MB()
    G.sphere('Att16PitGlow', (268.5, 0.5, -1.25), 1.0, seg=12, scale=(0.07, 0.02, 0.07))
    G.box('Att16PitGlow', 268.1, 268.9, 0.548, 0.552, -1.5, -1.47)
    objs.append(G.obj('Att16PitGlow', coll, origin=(268.5, 0.5, -1.25)))
    objs.append(build_lever(coll))
    objs.append(build_bridge(coll))
    objs.append(build_latch(coll))
    cw = build_cw(coll)
    objs.append(cw)
    folded, standing = folded_figure_mesh(), stand_figure_mesh()
    rack_objs, nfig = build_rack(coll, folded, standing)
    objs.extend(rack_objs)
    e = bpy.data.objects.new('Att16Speaker', None)
    e.empty_display_type = 'SPHERE'
    e.empty_display_size = 0.1
    e.location = mouth
    coll.objects.link(e)
    bpy.context.view_layer.update()
    total, unique, seen = 0, 0, set()
    for ob in objs:
        if ob.type != 'MESH':
            continue
        t = tris(ob)
        total += t
        if ob.data.name not in seen:
            seen.add(ob.data.name)
            unique += t
            bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
            print('dl16: %-18s tris %6d mats %-70s x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (
                ob.name, t, [s.material.name for s in ob.material_slots],
                min(v.x for v in bb), max(v.x for v in bb), min(v.y for v in bb), max(v.y for v in bb), min(v.z for v in bb), max(v.z for v in bb)))
    print('dl16: folded figures %d; tris drawn %d, unique mesh tris %d; tannoy mouth %s' % (nfig, total, unique, tuple(round(c, 3) for c in mouth)))


REPORT = """DL-16 After the Bell (x 263.9..280.0). Blender (x, y, z) = game (x, z, -y). Rail top 0.03; rails at Blender y 0.47 / 0.63
(DL-15's gauge and profile, its PigeonWood channel strip y 0.39..0.71); ours runs 264.0..267.895, on the bridge 267.95..269.89,
269.905..276.48 (buffer stop 276.48..276.56).

MOVED OBJECTS (origin = pivot, world; built state = rotation 0)
- Att16Lever: pivot Blender (266.0, 0.35, 0) = game (266.0, 0, -0.35). Built upright; grip 0.52..0.64. Pulled (handle toward +x):
  Blender rotation_euler.y = +35 deg = game rotation.z = -35 deg.
- Att16Bridge: hinge Blender (269.9, 0.3, 0) = game (269.9, 0, -0.3). Built DOWN: deck top 0 over x 267.92..269.9, y -0.3..0.9.
  Raised = Blender rotation_euler.y +90 deg = game rotation.z -90 deg. Raised it stands at x 269.6..269.93 (deck face 269.9, rails to
  269.93, truss struts to 269.35 at 1.1..1.4), up to 2.0; its tail swings down into the well (to z -0.72 at x 269.6..269.9).
- Att16Latch: pivot Blender (270.06, 0.8, 0.12) = game (270.06, 0.12, -0.8). Built UP (arm to 0.64, jaw toward -x). Dropped =
  Blender rotation_euler.y -90 deg = game rotation.z +90 deg: lies along -x, jaw into the deck's eye at (269.53, 0.8, 0.03).
- Att16CW: origin bottom centre Blender (278.5, 0, 0) = game (278.5, 0, 0). Box x 277.8..279.2 (guide shoes 277.77..279.23), Blender
  y -0.25..0.25, top 1.5. Lift +2.0 (bottom 2.0, top 3.5, into the ceiling slot x 277.72..279.28; its chain goes with it).
Static: Att16Set, Att16Rack, Att16RackFig.00..73 (linked, mesh Att16FoldedFigure), Att16BayFig.0/1 (mesh Att16StandFigure = DL-15's
figure with its bogie), Att16Lamps (EMIT AttGlobeLamp), Att16PitGlow (EMIT), Att16Speaker (empty, att_bell emitter).

SURFACES (x0, x1, top) for D-17: floor 263.9..267.9 @ 0; bridge 267.92..269.9 @ 0 (only when down); 269.9..279.6 @ 0 (iron plate
269.9..270.65 flush); doorway 279.6..280.0 @ 0.004 (head 2.1). Counterweight 277.77..279.23 @ 1.5 blocks until lifted (too high
to climb). Raised bridge: a wall 269.6..269.93, 0..2.0. Ceiling 3.0. Bench 270.9..272.5 top 0.32 and lever frame are behind the lane.
THE WELL: x 267.9..269.9, floor -1.6, sheer walls at 267.9 and 269.9 (full depth), back wall y 1.0, open to the camera; yellow lips
at both edges. No climb-out (rungs on its left wall are behind the lane, decorative): treat a fall as a reset, or block the edge.

RACK: x 273.6..277.6, Blender y 0.6..1.4, top 2.92; tiers bars at 0.58/1.14/1.70/2.26/2.82; cards MODELS, CLASS 1..5, CLASS 6 on
the bay header (1.6..1.7). Bay 274.6..276.6 open below 1.6. Four drop hooks over the rail, catch (wire bottom) z 1.298, y 0.55:
  EMPTY 275.45 (tag T. ORME: the first to arrive) and 274.95 (tag R. ABEL: the second); 275.95, 276.35 hold figures.
  Arriving figure: lift its origin from (x, 0.55, 0.03) to (x, 0.55, 0.34) Blender = game (x, 0.34, -0.55) (+0.31): head top meets
  the hook. 74 folded figures on the tiers.

TANNOY: mount Blender (265.4, 1.398, 2.5); horn mouth Blender (265.22, 0.971, 2.348) = game (265.22, 2.348, -0.971) (Att16Speaker).

LIGHTS (game coords, index.html P/S helpers):
  P(0xffdcaa, 1.6, 5, 265.0, 2.45, 0), P(0xffdcaa, 1.6, 5, 270.05, 2.45, 0)            // the two lit globes
  S(0xffe0b8, 4, 4, [266.0, 2.4, 1.4], [266.0, 0.4, -0.35], 0.5)                        // the lever and its plate
  S(0xffd8a8, 7, 6, [275.3, 2.9, 1.6], [275.6, 1.2, -1.0], 0.7, true)                   // the rack (shadowed), globe at 275.05
  S(0xffd8a8, 4, 5, [278.5, 2.7, 1.6], [278.5, 0.8, 0], 0.6)                            // the counterweight
  P(0xff7a30, 1.2, 2.5, 268.5, -1.1, -0.3)                                               // down the well, the boiler's glow
  P(0xe8dcc8, 0.6, 6, 269.0, 2.4, 2.0)                                                   // a soft wash on the mural
  DL-17's doorway stays dark until its own lights come up.

MATERIALS: new EMIT  Att16PitGlow: [1, .42, .14, 2.2],
  new image material Att16Mural (art/ch1/textures/dl16_mural.png, 4096x1024, 0.44 MB; mural + plates + swatches; passes through).
  Reused (all in index.html): WORN WinPlaster WinDado WinLino PigeonWood CrateWood WornIron CastIron HandledBrass PupilWood Concrete
  SafetyYellow LeverRed DustyCream DarkMetal DepotSteel TannoyEnamel; PLAIN Copper Cable; EMIT AttGlobeLamp.

TRIANGLES: 68.4k drawn (unique meshes 22.7k; folded figure 596 x 74, bay figure 2.15k x 2, set 8.1k, bridge 5.1k, rack 4.0k).

PREVIEWS: /tmp/claude-0/-home-user-deadletter/228ec196-fd3f-53d1-bee6-a1339d260a7f/scratchpad/dl16out/left.png (bridge raised), /tmp/claude-0/-home-user-deadletter/228ec196-fd3f-53d1-bee6-a1339d260a7f/scratchpad/dl16out/left_down.png (lever held, bridge down), /tmp/claude-0/-home-user-deadletter/228ec196-fd3f-53d1-bee6-a1339d260a7f/scratchpad/dl16out/right.png, /tmp/claude-0/-home-user-deadletter/228ec196-fd3f-53d1-bee6-a1339d260a7f/scratchpad/dl16out/right_solved.png (counterweight lifted), /tmp/claude-0/-home-user-deadletter/228ec196-fd3f-53d1-bee6-a1339d260a7f/scratchpad/dl16out/rack.png, /tmp/claude-0/-home-user-deadletter/228ec196-fd3f-53d1-bee6-a1339d260a7f/scratchpad/dl16out/bridge.png, /tmp/claude-0/-home-user-deadletter/228ec196-fd3f-53d1-bee6-a1339d260a7f/scratchpad/dl16out/well.png
"""
