"""Chapter 1 Attendance, DL-14 The Window (game x 232.0 to 248.0). Design: docs/chapter1_attendance_plan.md.

A corridor whose back wall is a row of tall classroom windows, each glazed over a painted panel of blue sky, a field,
a sun and one straight, tall tree (PIL-painted, naive, faded). Each window has a roller blind in a pelmet and a hinged
window-cleaner's ledge folded up under it. Blinds A and B hang on one endless chain that runs from the crank at 242.4
up over the ceiling pulleys to both rollers, and down the wall to A's chain wheel low at 235.0 (the lead moved it there
from 236.6, between the pole and the desk). Behind B's painted panel, in its lower right pane, the corner peels back
to show concrete, and on it Mara's crooked tree in pencil, drawn over and over. Under the stair, the stock cupboard: the last teacher's corner.

Rev 0.3 (docs/chapter1_rev03_plan.md): behind the hatch, at the duct's mouth, the refuge the last three children shared
(AttRefuge, seen through the hatch from ledge B and the landing): three places along its back wall under their
scratched initials (R.A., T.O., M), a biscuit tin open with crumbs, a tin cup held to the water pipe, a lantern
(AttRefugeLamp); the duct goes on from its right side behind the painted windows. By the crank, an enamel drive plate
(one chain, two blinds, A down = B up; the clutch slips if a blind is held), A and B roundels on the two pelmets, and a
clutch (AttClutch) behind A's chain wheel that the game spins while the chain slips.

Called by build_attendance.py as build_set(dl01, m, coll), in final world coordinates.
Blender (x, y, z) is the game's (x, z, -y): +y is away from the camera, z is up. The lane is y = 0, the floor z = 0.

What the game moves (origin = pivot, world coordinates; see REPORT at the bottom for the game's numbers):
    AttBlindA, AttBlindB   roller blinds, built DOWN; origin on the top roller's axis; the game scales z (game y) to roll
    AttLedgeA, AttLedgeB   window-cleaner's ledges, built OUT (lane-deep, y -0.3..0.9); origin on the wall hinge
    AttPanelPeel           the corner of B's painted panel, built flat (closed); origin on its diagonal hinge
    AttCrank               the handwheel at 242.4; origin on its axle
    AttWheelA              A's chain wheel at 235.0 (between the pole and the desk), low on the wall; origin on its axle
    AttPole                the window pole (carried); origin at its middle grip; built along local z, leaned by rotation
    AttChain               the endless chain, static (its UV v runs along the loop for a texture scroll)
    AttClutch              the clutch's pressure plate behind A's wheel; origin on the axle; spins about local y (game z)
Static: AttWinSet (the corridor), AttGlobeLamps (EMIT AttGlobeLamp), AttCupboard (the secret room),
AttCupboardLamp (EMIT AttCupboardLamp), AttRefuge (the children's refuge), AttRefugeLamp (EMIT DenLanternGlow), and the
card player from art/common/voice_props.py.
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

# =====================================================================================================================
# Layout (Blender world; game x = x)
# =====================================================================================================================
X0, X1 = 232.0, 248.0
END_X = 247.85                 # the end wall's face
WALL_Y = 0.9                   # the back wall's face (the corridor side)
WALL_Y1 = 1.2                  # the front layer's back face; the painted panels' layer and the cupboard start here
WALL_Y2 = 1.3                  # the back of the wall behind the windows
PANEL_Y = 1.17                 # the painted panels' face, in the window recess
CEIL = 3.95
LAND_H = 2.05                  # the gallery level, in from DL-13
STAIR = (233.0, 234.4)
N_TREAD = 5
TREAD_RUN = (STAIR[1] - STAIR[0]) / N_TREAD                               # 0.28
TREADS = [(STAIR[0] + i * TREAD_RUN, STAIR[0] + (i + 1) * TREAD_RUN, LAND_H * (1 - (i + 1) / (N_TREAD + 1)))
          for i in range(N_TREAD)]                                          # (x0, x1, top): 1.708 .. 0.342
SILL, HEAD = 0.5, 3.0          # window openings
WINDOWS = [                     # name, x0, x1, painted variant
    ('W0', 235.05, 236.15, 1),
    ('A', 236.45, 237.55, 0),
    ('B', 237.85, 238.95, 0),
    ('W3', 240.50, 241.60, 1),
    ('W4', 243.30, 244.40, 0),
    ('W5', 244.70, 245.80, 1),
]
TRANSOMS = (1.30, 2.15)
HATCH = (239.2, 240.25, 2.15, 3.05)          # the way on: x0, x1, sill, head (rev 0.3: was 239.25..240.15, head 3.0)
HATCH_LAND = (239.2, 240.2, 2.15)            # its iron landing, lane-deep
DEN = (238.98, 240.47, WALL_Y2, 2.6)         # behind the hatch: the children's refuge, x0, x1, y0, y1 (floor = the sill)
DEN_TOP = 3.08                               # its ceiling
DUCT = (WALL_Y2, 1.95, 0.62)                 # the duct on from its right side, behind the painted windows: y0, y1, height
PLACES = (239.56, 239.87, 240.18)            # the three places along its back wall: R.A., T.O., M (by the pipe)
REF_PIPE = (240.385, 2.5)                    # the water pipe down its back right corner (x, y)
REF_LAMP = (239.42, 1.74)                    # the lantern on the floor (x, y); its glass is AttRefugeLamp
CLUTCH = (235.0, 0.712, 0.32, 0.12)          # AttClutch, behind A's wheel: x, y (its face), z (the axle), r
DRIVE_PLATE = (242.64, 243.20, 0.44, 0.92)   # the enamel drive plate by the crank: x0, x1, z0, z1
END_DOOR = (246.4, 247.3, 2.1)
CUP_DOOR = (233.2, 233.8, 1.05)              # the stock cupboard's door, under the stair
ROOM = (232.4, 235.0, WALL_Y1, 3.4, 2.3)     # x0, x1, y0, y1, ceiling
DESK = (235.4, 236.2, 0.62)
LEDGE_A = (236.4, 237.6, 1.1)
LEDGE_B = (237.8, 239.0, 1.6)
LEDGE_Y = (-0.3, WALL_Y)
ROLLER_Y, ROLLER_Z, ROLLER_R = 0.76, 3.15, 0.035
BLIND_FACE_Y = ROLLER_Y - ROLLER_R
BLIND_A = (236.48, 237.56, 1.22)             # fabric x0, x1, hem bottom when down
BLIND_B = (237.82, 238.93, 1.72)
CHAIN_Y = 0.68
WHEEL_A = (235.0, CHAIN_Y, 0.32, 0.15)       # x, y, z, r (moved from 236.6 by the lead: between the pole and the desk)
CRANK = (242.4, 0.32, 0.5, 0.19)             # handwheel: x, y, z, r
S0 = (242.4, 0.95, 0.10)                     # the crank's chain sprocket (x, z, r) above the gearbox
POLE_BASE, POLE_TOP, POLE_Y = (234.8, 0.0), (234.0, 2.05), -0.3   # leaning on the stair's front newel
JAM = (235.0, 0.62, 0.41)                    # the jammed pole's axis: through both lugs, along x
LUG_DX = 0.2                                 # the lugs stand this far either side of the wheel
PEEL = ((238.44, 0.55), (238.90, 0.55), (238.90, 1.26))   # H1, corner C, H2 of B's lower-right pane (x, z)
LAMPS = (234.6, 240.75)                      # globe pendants (lit); a dead one at 245.2

# =====================================================================================================================
# Materials
# =====================================================================================================================
NEW_WORN = {     # the game's WORN table format is in REPORT
    'WinPlaster': dict(base=(.29, .27, .21), dirt=(.15, .13, .095), chip=(.2, .185, .15), rough=.9, chip_rough=.85,
                       metallic=0, grime_scale=3, chip_scale=18, chip_amount=.7, streaks=.6, dust=(.24, .22, .18), dust_amount=.5),
    'WinDado': dict(base=(.12, .16, .135), dirt=(.065, .075, .06), chip=(.30, .27, .21), rough=.55, chip_rough=.85,
                    metallic=0, grime_scale=4, chip_scale=22, chip_amount=.68, streaks=.5, dust=(.16, .17, .15), dust_amount=.4),
    'WinLino': dict(base=(.115, .085, .05), dirt=(.06, .045, .03), chip=(.075, .07, .062), rough=.7, chip_rough=.9,
                    metallic=0, grime_scale=3, chip_scale=14, chip_amount=.66, streaks=.3, dust=(.13, .12, .1), dust_amount=.6),
}
REUSE_WORN = {   # names already in index.html's WORN table (fallbacks for a lone build)
    'PigeonWood': dict(base=(.12, .085, .055), dirt=(.06, .045, .03), chip=(.2, .15, .1), rough=.85, chip_rough=.8, metallic=0,
                       grime_scale=6, chip_scale=30, chip_amount=.75, dust=(.1, .09, .08), dust_amount=.6),
    'CrateWood': dict(base=(.18, .12, .07), dirt=(.08, .055, .035), chip=(.25, .19, .12), rough=.85, chip_rough=.8, metallic=0,
                      grime_scale=6, chip_scale=30, chip_amount=.75, streaks=.6),
    'WornIron': dict(base=(.045, .043, .04), dirt=(.06, .035, .02), chip=(.3, .29, .27), rough=.7, chip_rough=.35, metallic=.6,
                     grime_scale=9, chip_scale=40, chip_amount=.6, dust=(.09, .085, .075), dust_amount=.4),
    'HandledBrass': dict(base=(.2, .14, .06), dirt=(.08, .06, .03), chip=(.62, .46, .2), rough=.5, chip_rough=.2, metallic=.85,
                         grime_scale=8, chip_scale=26, chip_amount=.5, dust=(.12, .1, .07), dust_amount=.2),
}
NEW_EMIT = {'AttGlobeLamp': ((1.0, 0.86, 0.62), 3.0), 'AttCupboardLamp': ((1.0, 0.72, 0.42), 6.0),
            'DenLanternGlow': ((1.0, 0.55, 0.22), 2.5)}     # (already in index.html's EMIT: DL-09's den lantern)
REUSE_PLAIN = {'Copper': ((.55, .3, .18), .35, 1.0)}
IMAGES = {'WinPanel': ('dl14_panels.png', 0.45), 'WinAtlas': ('dl14_atlas.png', 0.85), 'WinChain': ('dl14_chain.png', 0.4),
          'WinDrive': ('dl14_drive.png', 0.6)}


def mat(name):
    mt = bpy.data.materials.get(name)
    if mt is not None:
        return mt
    if name in NEW_WORN:
        return worn_material(name, **NEW_WORN[name])
    if name in REUSE_WORN:
        return worn_material(name, **REUSE_WORN[name])
    if name in NEW_EMIT:
        c, s = NEW_EMIT[name]
        return emission_material(name, c, s)
    if name in REUSE_PLAIN:
        c, r, mtl = REUSE_PLAIN[name]
        return simple_material(name, c, r, metallic=mtl)
    if name in IMAGES:
        fn, rough = IMAGES[name]
        mt, nt, bsdf = d17._new_material(name)
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(os.path.join(TEX, fn), check_existing=True)
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = rough
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
# Textures (PIL, at build time, into art/ch1/textures/dl14_*.png)
# =====================================================================================================================
ATLAS = 1024
CELLS = {
    'pencil': (0, 0, 512, 768), 'blindA': (512, 0, 768, 512), 'blind2': (768, 0, 1024, 512), 'notice': (512, 512, 1024, 768),
    'stock': (0, 768, 256, 832), 'class5': (0, 832, 256, 896), 'blindsplate': (0, 896, 256, 960),
    'sw_wood': (0, 960, 64, 1024), 'sw_brass': (64, 960, 128, 1024), 'sw_iron': (128, 960, 192, 1024), 'sw_string': (192, 960, 256, 1024),
    'book0': (256, 768, 384, 896), 'book1': (384, 768, 512, 896), 'book2': (256, 896, 384, 1024), 'book3': (384, 896, 512, 1024),
    'card': (512, 768, 640, 848), 'card2': (640, 768, 768, 848), 'boxlabel': (512, 848, 768, 928),
    'chalkbox': (512, 928, 640, 1008), 'register': (640, 928, 768, 1008), 'clock': (768, 768, 896, 896), 'openbook': (896, 768, 1024, 896),
    'sw_cardboard': (768, 896, 832, 960), 'sw_pages': (832, 896, 896, 960), 'sw_wool': (896, 896, 960, 960), 'sw_dark': (960, 896, 1024, 960),
    'sw_glass': (768, 960, 832, 1024), 'sw_green': (832, 960, 896, 1024), 'sw_chalk': (896, 960, 960, 1024), 'sw_ink': (960, 960, 1024, 1024),
}
SWATCH = {'sw_wood': (104, 74, 46), 'sw_brass': (170, 132, 64), 'sw_iron': (38, 37, 35), 'sw_string': (184, 172, 140),
          'sw_cardboard': (122, 96, 64), 'sw_pages': (196, 188, 164), 'sw_wool': (78, 70, 64), 'sw_dark': (8, 8, 8),
          'sw_glass': (70, 74, 72), 'sw_green': (44, 66, 54), 'sw_chalk': (214, 210, 198), 'sw_ink': (18, 20, 30)}
PANEL_W = 448                  # each painted variant is 448 x 1024 in dl14_panels.png; 896..1024 is the hardboard back


def cell_uv(name):
    x0, y0, x1, y1 = CELLS2[name] if name.startswith('r_') else CELLS[name]
    return x0 / ATLAS, 1 - y1 / ATLAS, x1 / ATLAS, 1 - y0 / ATLAS


def cell_mid(name):
    u0, v0, u1, v1 = cell_uv(name)
    return (u0 + u1) / 2, (v0 + v1) / 2


def panel_uv(variant, u, v):
    return (variant * PANEL_W + u * PANEL_W) / 1024.0, v


def _font(size, kind='sans-bold'):
    from PIL import ImageFont
    paths = {'sans-bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
             'sans': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
             'serif': '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
             'carlito': '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf',
             'hand': '/usr/share/fonts/truetype/crosextra/Caladea-Italic.ttf'}
    try:
        return ImageFont.truetype(paths[kind], size)
    except OSError:
        return ImageFont.load_default()


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


def _paint_panel(img, x0, seed, flip):
    """The painted window: a naive sky, a sun, a field, and one tree, straight and tall, toward the sun."""
    from PIL import Image, ImageDraw
    rnd = random.Random(seed)
    w, h = PANEL_W, 1024
    layer = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(layer)
    hy = int(h * 0.79)                                   # the horizon (z 1.02)
    sky0, sky1 = (78, 120, 166), (170, 192, 204)
    for y in range(hy):
        d.line((0, y, w, y), fill=_lerp(sky0, sky1, (y / hy) ** 1.4))
    for _ in range(1400):                                # brush strokes
        y = rnd.uniform(0, hy)
        x = rnd.uniform(-40, w)
        c = _lerp(sky0, sky1, (y / hy) ** 1.4)
        j = rnd.randint(-9, 9)
        d.line((x, y, x + rnd.uniform(30, 90), y + rnd.uniform(-4, 4)), fill=(c[0] + j, c[1] + j, c[2] + j), width=rnd.randint(4, 9))
    for cx, cy, s in ((0.3, 0.33, 1.0), (0.78, 0.47, 0.8), (0.2, 0.6, 0.7)):   # clouds: flat-bottomed, white
        cx, cy = (1 - cx if flip else cx) * w, cy * h
        for k in range(6):
            r = s * rnd.uniform(26, 44)
            ox = cx + s * (k - 2.5) * 22 + rnd.uniform(-6, 6)
            oy = cy - rnd.uniform(0, 26) * s
            d.ellipse((ox - r, oy - r, ox + r, min(oy + r, cy + 10)), fill=(222, 226, 222))
        d.line((cx - s * 80, cy + 10, cx + s * 80, cy + 10), fill=(196, 204, 206), width=5)
    sx, sy, r = (0.3 if flip else 0.7) * w, h * 0.15, 50          # the sun (z 2.62)
    for k in range(14):
        a = 2 * math.pi * k / 14 + 0.1
        d.line((sx + (r + 12) * math.cos(a), sy + (r + 12) * math.sin(a), sx + (r + 44) * math.cos(a), sy + (r + 44) * math.sin(a)),
               fill=(226, 186, 76), width=8)
    d.ellipse((sx - r, sy - r, sx + r, sy + r), fill=(238, 204, 92))
    d.ellipse((sx - r * 0.55, sy - r * 0.6, sx + r * 0.15, sy - r * 0.05), fill=(246, 222, 130))
    hills = [(0, hy)]
    for k in range(9):
        hills.append((k * w / 8, hy - 22 - 16 * math.sin(k * 1.7 + seed) ** 2))
    hills.append((w, hy))
    d.polygon(hills, fill=(112, 142, 132))
    f0, f1 = (118, 154, 80), (76, 114, 56)                        # the field
    for y in range(hy, h):
        d.line((0, y, w, y), fill=_lerp(f0, f1, (y - hy) / (h - hy)))
    vx = w * (0.62 if flip else 0.38)
    for k in range(-6, 13):                                       # furrows
        bx = vx + (k - 3) * 70
        d.line((vx + (k - 3) * 6, hy + 2, bx, h), fill=(92, 128, 64), width=5)
    for _ in range(70):                                           # flowers
        x, y = rnd.uniform(0, w), rnd.uniform(hy + 30, h - 8)
        rr = 2 + 4 * (y - hy) / (h - hy)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=rnd.choice(((230, 222, 176), (226, 200, 90), (206, 206, 214))))
    tx = (0.74 if flip else 0.26) * w                             # the tree: straight, tall, toward the sun
    d.rectangle((tx - 7, hy - 150, tx + 7, hy + 40), fill=(104, 76, 48))
    d.ellipse((tx - 60, hy - 262, tx + 60, hy - 128), fill=(78, 126, 66), outline=(56, 96, 50), width=5)
    d.ellipse((tx - 34, hy - 244, tx + 4, hy - 206), fill=(98, 146, 78))
    d.ellipse((tx - 30, hy + 30, tx + 30, hy + 50), fill=(64, 98, 48))
    img.paste(layer, (x0, 0))


def make_panels(path):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    img = Image.new('RGB', (1024, 1024), (110, 86, 58))
    _paint_panel(img, 0, 1401, False)
    _paint_panel(img, PANEL_W, 1402, True)
    # the hardboard back (the peeled corner's underside)
    hb = np.asarray(Image.new('RGB', (128, 1024), (112, 86, 58))).astype(float)
    hb *= (0.85 + 0.3 * _noise(128, 1024, 3, 1403))[..., None]
    img.paste(Image.fromarray(np.clip(hb, 0, 255).astype('uint8')), (896, 0))
    img = _fade(img, 1404)
    d = ImageDraw.Draw(img, 'RGBA')
    rnd = random.Random(1405)
    for _ in range(110):                                         # craquelure in the old paint
        x, y = rnd.uniform(0, 896), rnd.uniform(0, 1024)
        pts = [(x, y)]
        for _k in range(rnd.randint(3, 7)):
            x += rnd.uniform(-18, 18)
            y += rnd.uniform(-18, 18)
            pts.append((x, y))
        d.line(pts, fill=(40, 34, 26, rnd.randint(30, 70)), width=1)
    for k in range(2):                                           # a water stain creeping up from each sill
        x0 = k * PANEL_W
        for _ in range(12):
            cx, r = x0 + rnd.uniform(0, PANEL_W), rnd.uniform(40, 110)
            d.ellipse((cx - r, 1024 - r * 0.6, cx + r, 1024 + r * 0.6), fill=(96, 78, 46, 22))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    img.save(path, optimize=True)


def _graphite_tree(d, ox, oy, s, rnd, alpha=210, width=3.2, passes=2):
    import build_dl05 as dl05

    def stroke(pts, weight):
        for _ in range(passes):
            q = [(x + rnd.uniform(-1.6, 1.6), y + rnd.uniform(-1.6, 1.6)) for x, y in pts]
            d.line(q, fill=(34, 34, 42, int(alpha * rnd.uniform(0.85, 1.0))), width=max(3, int(width * (0.7 + weight * 0.7))), joint='curve')
    dl05._crooked_tree(stroke, ox, oy, s, sx=s * rnd.uniform(0.7, 0.85))


def _visible(px, py):
    """Inside the peeled triangle of the pencil cell (right of the hinge line H1-H2)."""
    h1 = ((PEEL[0][0] - 238.42) * 1024, (1.28 - PEEL[0][1]) * 1024)
    h2 = ((PEEL[2][0] - 238.42) * 1024, (1.28 - PEEL[2][1]) * 1024)
    return (h2[0] - h1[0]) * (py - h1[1]) - (h2[1] - h1[1]) * (px - h1[0]) > 0 and 4 < px < 506 and 4 < py < 764


def make_pencil(img, rnd):
    """Concrete behind B's panel, and Mara's crooked tree with the knot in its branch, drawn over and over (1 px = 1 mm)."""
    import numpy as np
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = CELLS['pencil']
    w, h = x1 - x0, y1 - y0
    n = _noise(w, h, 5, 1410)
    a = np.ones((h, w, 3)) * np.array([112, 110, 104]) * (0.82 + 0.36 * n)[..., None]
    for yy in range(0, h, 150):                                  # formwork board marks
        a[yy:yy + 3] *= 0.86
    rng = np.random.default_rng(1411)
    pores = rng.random((h, w)) > 0.996
    a[pores] *= 0.55
    conc = Image.fromarray(np.clip(a, 0, 255).astype('uint8')).convert('RGBA')
    pen = Image.new('RGBA', (w, h), (44, 44, 52, 0))
    d = ImageDraw.Draw(pen)
    placed = 0
    tries = 0
    big = [(390, 742, 380, 3, 245), (285, 744, 250, 2, 220), (462, 470, 190, 2, 225)]   # the most-traced ones by the corner
    for ox, oy, s, passes, al in big:
        _graphite_tree(d, ox, oy, s, rnd, alpha=al, width=5.5, passes=passes + 1)
        placed += 1
    while placed < 18 and tries < 4000:                          # and again, and again, smaller, all over the corner
        tries += 1
        s = rnd.uniform(90, 200)
        ox, oy = rnd.uniform(40, 480), rnd.uniform(140, 760)
        pts = [(ox, oy), (ox - 0.05 * s, oy - 0.93 * s), (ox - 0.36 * s, oy - 0.66 * s), (ox + 0.45 * s, oy - 0.8 * s),
               (ox - 0.13 * s, oy), (ox + 0.14 * s, oy)]
        if not all(_visible(px, py) for px, py in pts):
            continue
        _graphite_tree(d, ox, oy, s, rnd, alpha=rnd.choice((150, 200, 235)), width=rnd.uniform(3.2, 4.6), passes=rnd.choice((1, 2, 2, 3)))
        placed += 1
    conc.alpha_composite(pen)
    img.paste(conc.convert('RGB'), (x0, y0))


def make_atlas(path):
    from PIL import Image, ImageDraw, ImageFilter
    import numpy as np
    rnd = random.Random(1420)
    img = Image.new('RGB', (ATLAS, ATLAS), (60, 58, 54))
    make_pencil(img, rnd)
    ink, cream, green = (30, 28, 24), (214, 204, 176), (40, 64, 50)

    # Blinds: faded dark-green holland, sun-bleached in streaks; the static ones stained and mended.
    for name, seed, stained in (('blindA', 1421, False), ('blind2', 1422, True)):
        x0, y0, x1, y1 = CELLS[name]
        w, h = x1 - x0, y1 - y0
        n = _noise(w, h, 4, seed)
        base = np.array([66, 82, 70], float)
        a = np.ones((h, w, 3)) * base
        weave = (np.sin(np.arange(h)[:, None] * 1.9) * 0.04 + np.sin(np.arange(w)[None, :] * 2.3) * 0.04)
        streak = np.clip(np.sin(np.arange(w)[None, :] / w * math.pi * 3 + seed) * 0.5 + 0.5, 0, 1) ** 4
        a *= (0.88 + 0.22 * n + weave)[..., None]
        a = a * (1 - 0.35 * streak[..., None]) + np.array([150, 150, 128]) * 0.35 * streak[..., None]
        a[:, w // 2 - 1:w // 2 + 1] *= 0.8                       # the seam
        a[h - 26:h] *= 0.78                                      # the hem pocket
        if stained:
            for _ in range(5):
                cx, cy, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(20, 60)
                yy, xx = np.ogrid[:h, :w]
                m = ((xx - cx) ** 2 + (yy - cy) ** 2 < r * r)
                a[m] = a[m] * 0.8 + np.array([90, 76, 50]) * 0.2
        tile = Image.fromarray(np.clip(a, 0, 255).astype('uint8'))
        dd = ImageDraw.Draw(tile)
        if stained:
            dd.line((30, 300, 60, 330, 44, 360), fill=(28, 30, 26), width=3)       # a mended tear
            for k in range(8):
                dd.line((36 + k * 3, 318 + k * 4, 52 + k * 3, 312 + k * 4), fill=(170, 160, 130), width=1)
        img.paste(tile, (x0, y0))

    # The window drill notice.
    x0, y0, x1, y1 = CELLS['notice']
    t = Image.new('RGB', (x1 - x0, y1 - y0), (206, 196, 166))
    d = ImageDraw.Draw(t)
    d.rectangle((0, 0, 511, 62), fill=green)
    d.text((256, 33), 'WINDOW DRILL', font=_font(40, 'carlito'), fill=cream, anchor='mm')
    lines = ('At the bell:', '1   Blinds down', '2   Ledges out', '3   Stand clear of the chain', '4   Eyes to the front')
    for k, s in enumerate(lines):
        d.text((26, 84 + k * 30), s, font=_font(24, 'carlito'), fill=ink, anchor='lm')
    mx, my, k = 440, 186, 0.62                                   # the school's mark: a sun over an open book
    d.pieslice((mx - 44 * k, my - 74 * k, mx + 44 * k, my + 14 * k), 180, 360, fill=(196, 150, 50))
    for a_ in range(200, 341, 28):
        r = math.radians(a_)
        d.line((mx + 54 * k * math.cos(r), my - 30 * k + 54 * k * math.sin(r), mx + 76 * k * math.cos(r), my - 30 * k + 76 * k * math.sin(r)),
               fill=(196, 150, 50), width=4)
    d.polygon([(mx - 70 * k, my - 8 * k), (mx, my + 8 * k), (mx + 70 * k, my - 8 * k), (mx + 70 * k, my + 52 * k), (mx, my + 70 * k),
               (mx - 70 * k, my + 52 * k)], fill=green)
    d.text((440, 240), 'LOWER SCHOOL', font=_font(15, 'carlito'), fill=ink, anchor='mm')
    d.rectangle((2, 2, 509, 253), outline=(120, 110, 86), width=3)
    img.paste(_fade(t, 1423, k=0.15, dust=0.2), (x0, y0))

    def plate(name, text, size, bg=green, fg=cream):
        x0, y0, x1, y1 = CELLS[name]
        p = Image.new('RGB', (x1 - x0, y1 - y0), bg)
        dp = ImageDraw.Draw(p)
        dp.rounded_rectangle((3, 3, x1 - x0 - 4, y1 - y0 - 4), radius=10, outline=fg, width=4)
        dp.text(((x1 - x0) // 2, (y1 - y0) // 2 + 1), text, font=_font(size, 'carlito'), fill=fg, anchor='mm')
        for xx in (12, x1 - x0 - 12):
            dp.ellipse((xx - 4, (y1 - y0) // 2 - 4, xx + 4, (y1 - y0) // 2 + 4), fill=(110, 106, 96))
        img.paste(_fade(p, sum(map(ord, name)), k=0.12, dust=0.15), (x0, y0))
    plate('stock', 'STOCK', 40)
    plate('class5', 'CLASS 5', 40)
    plate('blindsplate', 'BLINDS   A         B', 34, bg=(150, 116, 56), fg=(40, 30, 16))
    bx0, by0 = CELLS['blindsplate'][:2]
    dpl = ImageDraw.Draw(img)
    for cx_, up in ((172, False), (196, True)):                  # A goes down as B goes up
        cy_ = by0 + 33
        tri_ = [(bx0 + cx_ - 9, cy_ + 9), (bx0 + cx_ + 9, cy_ + 9), (bx0 + cx_, cy_ - 9)] if up else \
               [(bx0 + cx_ - 9, cy_ - 9), (bx0 + cx_ + 9, cy_ - 9), (bx0 + cx_, cy_ + 9)]
        dpl.polygon(tri_, fill=(40, 30, 16))

    for name, rgb in SWATCH.items():
        x0, y0, x1, y1 = CELLS[name]
        ImageDraw.Draw(img).rectangle((x0, y0, x1 - 1, y1 - 1), fill=rgb)

    # Exercise books: four covers.
    for k, (bg, who) in enumerate((((96, 118, 140), None), ((170, 150, 110), None), ((100, 124, 96), 'M. D.'), ((130, 112, 132), None))):
        x0, y0, x1, y1 = CELLS['book%d' % k]
        b = Image.new('RGB', (128, 128), bg)
        db = ImageDraw.Draw(b)
        db.rectangle((10, 12, 117, 44), fill=(214, 206, 182))
        db.text((64, 28), 'EXERCISE', font=_font(16, 'carlito'), fill=ink, anchor='mm')
        db.line((16, 70, 112, 70), fill=(40, 36, 30), width=1)
        db.line((16, 92, 112, 92), fill=(40, 36, 30), width=1)
        db.text((16, 66), 'Name', font=_font(11, 'carlito'), fill=ink, anchor='ls')
        db.text((16, 88), 'Class 4', font=_font(11, 'carlito'), fill=ink, anchor='ls')
        if who:
            db.text((56, 67), who, font=_font(16, 'hand'), fill=(40, 40, 70), anchor='ls')
        img.paste(_fade(b, 1430 + k, k=0.2), (x0, y0))

    # Voice cards, addressed and never sent.
    for name, to in (('card', 'To the family of'), ('card2', 'To the family of')):
        x0, y0, x1, y1 = CELLS[name]
        c = Image.new('RGB', (128, 80), (212, 200, 170))
        dc = ImageDraw.Draw(c)
        dc.rectangle((96, 6, 120, 30), outline=(110, 96, 70), width=2)
        dc.text((8, 22), to, font=_font(12, 'hand'), fill=(40, 40, 70), anchor='ls')
        for kk in range(3):
            yy = 38 + kk * 12
            pts = [(10 + i * 6, yy + 2 * math.sin(i * 1.3 + kk + len(name))) for i in range(int(14 + 4 * rnd.random()))]
            dc.line(pts, fill=(50, 50, 80), width=1)
        dc.text((8, 74), 'class four', font=_font(11, 'hand'), fill=(40, 40, 70), anchor='ls')
        img.paste(_fade(c, 1440 + len(name), k=0.12), (x0, y0))

    x0, y0, x1, y1 = CELLS['boxlabel']
    lb = Image.new('RGB', (256, 80), (200, 186, 150))
    dl = ImageDraw.Draw(lb)
    dl.rectangle((3, 3, 252, 76), outline=(70, 60, 44), width=2)
    dl.text((128, 26), 'CLASS 4', font=_font(26, 'carlito'), fill=ink, anchor='mm')
    dl.text((128, 56), 'EXERCISE BOOKS · 40', font=_font(18, 'carlito'), fill=ink, anchor='mm')
    img.paste(_fade(lb, 1450, k=0.15), (x0, y0))
    x0, y0, x1, y1 = CELLS['chalkbox']
    cb = Image.new('RGB', (128, 80), (60, 92, 120))
    dcb = ImageDraw.Draw(cb)
    dcb.text((64, 30), 'CHALK', font=_font(24, 'carlito'), fill=(226, 222, 206), anchor='mm')
    dcb.text((64, 58), 'WHITE · 144', font=_font(14, 'carlito'), fill=(226, 222, 206), anchor='mm')
    img.paste(_fade(cb, 1451, k=0.2), (x0, y0))
    x0, y0, x1, y1 = CELLS['register']
    rg = Image.new('RGB', (128, 80), (36, 58, 44))
    drg = ImageDraw.Draw(rg)
    drg.rectangle((14, 16, 113, 64), outline=(176, 150, 80), width=2)
    drg.text((64, 32), 'REGISTER', font=_font(16, 'carlito'), fill=(186, 160, 90), anchor='mm')
    drg.text((64, 52), 'CLASS 4', font=_font(13, 'carlito'), fill=(186, 160, 90), anchor='mm')
    img.paste(_fade(rg, 1452, k=0.15), (x0, y0))

    x0, y0, x1, y1 = CELLS['clock']                               # stopped at ten past nine
    ck = Image.new('RGB', (128, 128), (40, 34, 26))
    dk = ImageDraw.Draw(ck)
    dk.ellipse((4, 4, 123, 123), fill=(214, 208, 190), outline=(24, 22, 18), width=4)
    for k in range(12):
        a = math.radians(k * 30)
        dk.line((64 + 50 * math.sin(a), 64 - 50 * math.cos(a), 64 + 57 * math.sin(a), 64 - 57 * math.cos(a)), fill=ink, width=4)
    for ang, ln, wd in ((math.radians(9 * 30 + 5), 30, 6), (math.radians(10 * 6), 46, 4)):
        dk.line((64, 64, 64 + ln * math.sin(ang), 64 - ln * math.cos(ang)), fill=ink, width=wd)
    img.paste(_fade(ck, 1453, k=0.15), (x0, y0))

    x0, y0, x1, y1 = CELLS['openbook']
    ob = Image.new('RGB', (128, 128), (200, 194, 172))
    do = ImageDraw.Draw(ob)
    do.line((64, 0, 64, 128), fill=(140, 130, 110), width=2)
    for yy in range(14, 128, 10):
        do.line((4, yy, 60, yy), fill=(150, 160, 180), width=1)
        do.line((68, yy, 124, yy), fill=(150, 160, 180), width=1)
    for yy in range(14, 110, 10):
        pts = [(8 + i * 5, yy - 3 + rnd.uniform(-1, 1)) for i in range(rnd.randint(5, 10))]
        do.line(pts, fill=(60, 60, 90), width=1)
    img.paste(ob, (x0, y0))

    img.filter(ImageFilter.GaussianBlur(0.4)).save(path, optimize=True)


def make_chain(path):
    """Two links per tile (0.1 m): one face-on, one edge-on; bright worn steel on dark. v runs along the chain."""
    from PIL import Image, ImageDraw, ImageFilter
    img = Image.new('RGB', (64, 256), (14, 13, 12))
    d = ImageDraw.Draw(img)
    d.ellipse((6, -6, 57, 134), fill=(150, 146, 136))
    d.ellipse((12, 2, 51, 126), fill=(96, 94, 88))
    d.ellipse((21, 20, 42, 108), fill=(14, 13, 12))
    d.ellipse((9, 4, 22, 90), fill=(196, 192, 180))
    d.rounded_rectangle((25, 118, 39, 266), radius=6, fill=(118, 114, 106))
    d.line((30, 124, 30, 258), fill=(186, 182, 170), width=3)
    d.rounded_rectangle((25, -10, 39, 10), radius=6, fill=(118, 114, 106))
    img.filter(ImageFilter.GaussianBlur(0.5)).save(path, optimize=True)


# Rev 0.3 (docs/chapter1_rev03_plan.md): the drive plate by the crank, the clutch's face, the A / B roundels, and the
# children's refuge behind the hatch, in a second atlas (textures/dl14_drive.png, material WinDrive). Its cells are
# named r_*; cell_uv() takes either atlas's names.
CELLS2 = {
    'r_drive': (0, 0, 640, 544),            # the drive plate, 0.56 x 0.48 m
    'r_clutch': (640, 0, 896, 256),         # the clutch plate's face (a disc)
    'r_tinlid': (896, 0, 1024, 96),         # the biscuit tin's lid, 0.21 x 0.16
    'r_lblA': (896, 96, 960, 160), 'r_lblB': (960, 96, 1024, 160),
    'r_cushA': (640, 256, 768, 384), 'r_cushO': (768, 256, 896, 384), 'r_blanket': (896, 256, 1024, 384),
    'r_tinside': (640, 384, 896, 416),
    'r_wall': (0, 544, 768, 1024),          # the refuge's back wall, x 238.98..240.47, z 2.15..3.08
}
SWATCH2 = {'r_sw_tin': (46, 70, 106), 'r_sw_crumb': (182, 146, 88), 'r_sw_enamel': (222, 218, 204), 'r_sw_blue': (34, 52, 104),
           'r_sw_wood': (136, 100, 62), 'r_sw_iron': (40, 39, 37), 'r_sw_brass': (176, 136, 66), 'r_sw_string': (190, 178, 146),
           'r_sw_dark': (10, 9, 8), 'r_sw_red': (132, 48, 40), 'r_sw_cream': (222, 212, 184), 'r_sw_paper': (204, 196, 172),
           'r_sw_tinin': (120, 112, 96), 'r_sw_green': (52, 84, 60)}
for _i, _k in enumerate(SWATCH2):
    CELLS2[_k] = (768 + 32 * (_i % 8), 544 + 32 * (_i // 8), 768 + 32 * (_i % 8) + 32, 544 + 32 * (_i // 8) + 32)
WALL2 = (238.98, 240.47, 2.15)              # the refuge wall cell's x0, x1, z0 (its top: z0 + (x1 - x0) * 480 / 768)


def _letters(d, xy, text, size, fill, kind='carlito', anchor='mm', stroke=0, stroke_fill=None):
    d.text(xy, text, font=_font(size, kind), fill=fill, anchor=anchor, stroke_width=stroke, stroke_fill=stroke_fill)


def _arrow_v(d, x, ya, yb, w, fill):
    """A bold arrow along y from ya (its tail) to yb (its head)."""
    s = 1 if yb > ya else -1
    head = w * 1.25
    d.rectangle((x - w * 0.32, min(ya, yb - s * head), x + w * 0.32, max(ya, yb - s * head)), fill=fill)
    d.polygon([(x - w, yb - s * head), (x + w, yb - s * head), (x, yb)], fill=fill)


def _chain_dots(d, pts, fill, step=13, r=(6, 3.5)):
    """A roller chain along a polyline: links as little ovals, alternate ones turned."""
    acc = 0.0
    k = 0
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        L = math.hypot(bx - ax, by - ay)
        while acc <= L:
            t = acc / L
            x, y = ax + (bx - ax) * t, ay + (by - ay) * t
            horiz = abs(bx - ax) > abs(by - ay)
            rx, ry = (r if horiz else (r[1], r[0])) if k % 2 == 0 else (r[1] + 1, r[1] + 1)
            d.ellipse((x - rx, y - ry, x + rx, y + ry), fill=fill)
            acc += step
            k += 1
        acc -= L


def make_drive_plate(img):
    """The enamel drive plate (1 px ~ 0.9 mm): one chain round two blinds, A down = B up; and the clutch, which slips
    if a blind is held so the other moves alone. Pictures first, a few big words."""
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = CELLS2['r_drive']
    w, h = x1 - x0, y1 - y0
    cream, green, ink, cloth = (220, 212, 186), (34, 62, 50), (26, 26, 24), (70, 104, 84)
    amber = (196, 128, 36)
    p = Image.new('RGB', (w, h), cream)
    d = ImageDraw.Draw(p)
    d.rounded_rectangle((4, 4, w - 5, h - 5), radius=26, outline=green, width=10)
    d.rounded_rectangle((18, 18, w - 19, 84), radius=12, fill=green)
    _letters(d, (w // 2, 52), 'BLIND DRIVE', 50, cream)
    # Left: the two blinds on one endless chain, driven by the crank.
    rA, rB, ry = 104, 276, 128                                    # roller centres (x), roller y
    for cx, label, down in ((rA, 'A', True), (rB, 'B', False)):
        d.rounded_rectangle((cx - 66, ry - 11, cx + 66, ry + 11), radius=10, fill=(96, 70, 44), outline=ink, width=3)
        bot = 336 if down else 214
        d.rectangle((cx - 58, ry + 11, cx + 58, bot), fill=cloth, outline=ink, width=3)
        d.rectangle((cx - 62, bot, cx + 62, bot + 12), fill=(96, 70, 44), outline=ink, width=2)
        if down:
            _arrow_v(d, cx, ry + 40, 318, 30, cream)
        else:
            _arrow_v(d, cx, 318, 236, 30, ink)
        d.ellipse((cx - 34, 372 - 34, cx + 34, 372 + 34), fill=ink)
        _letters(d, (cx, 374), label, 54, cream)
    # The chain: up from the crank, over both rollers' sprockets, and back down to it.
    sA, sB, cw = (rA + 66, ry), (rB + 66, ry), (190, 470)
    loop = [(cw[0] - 30, cw[1]), (28, cw[1] - 20), (28, ry - 26), (sA[0], ry - 26), (sA[0], ry + 20), (sB[0] - 132, ry + 20),
            (sB[0] - 132, ry - 26), (sB[0], ry - 26), (sB[0] + 22, ry), (sB[0] + 22, cw[1] - 20), (cw[0] + 30, cw[1])]
    _chain_dots(d, loop, (60, 58, 54))
    for sx, sy in (sA, sB):
        d.ellipse((sx - 15, sy - 15, sx + 15, sy + 15), fill=(120, 116, 106), outline=ink, width=3)
    d.ellipse((cw[0] - 32, cw[1] - 32, cw[0] + 32, cw[1] + 32), fill=cream, outline=ink, width=7)   # the crank's handwheel
    for a in range(3):
        aa = math.radians(90 + 120 * a)
        d.line((cw[0], cw[1], cw[0] + 30 * math.cos(aa), cw[1] + 30 * math.sin(aa)), fill=ink, width=5)
    d.ellipse((cw[0] - 8, cw[1] - 8, cw[0] + 8, cw[1] + 8), fill=ink)
    d.ellipse((cw[0] - 23 - 9, cw[1] - 23 - 9, cw[0] - 23 + 9, cw[1] - 23 + 9), fill=amber, outline=ink, width=2)
    d.arc((cw[0] - 50, cw[1] - 50, cw[0] + 50, cw[1] + 50), 200, 320, fill=amber, width=6)        # turn it
    d.polygon([(cw[0] + 36, cw[1] - 46), (cw[0] + 50, cw[1] - 26), (cw[0] + 26, cw[1] - 28)], fill=amber)
    # A down = B up.
    _letters(d, (492, 506), 'A DOWN = B UP', 34, green)
    # Right: the clutch. A held blind (the pole through its wheel), the clutch slipping, the other blind moving alone.
    d.rounded_rectangle((372, 100, 612, 470), radius=14, outline=green, width=4)
    _letters(d, (492, 126), 'CLUTCH', 34, green)
    cx, cy = 430, 214                                              # a held wheel: pins, and the pole through them
    d.ellipse((cx - 38, cy - 38, cx + 38, cy + 38), outline=ink, width=6)
    for a in range(6):
        aa = math.radians(a * 60 + 15)
        d.ellipse((cx + 24 * math.cos(aa) - 5, cy + 24 * math.sin(aa) - 5, cx + 24 * math.cos(aa) + 5, cy + 24 * math.sin(aa) + 5), fill=ink)
    d.line((cx - 30, cy + 70, cx + 18, cy - 70), fill=(150, 104, 56), width=11)                      # the pole
    d.line((cx - 30, cy + 70, cx + 18, cy - 70), fill=ink, width=2)
    _letters(d, (cx, cy + 92), 'HELD', 26, ink)
    ex, ey = 540, 214                                              # the clutch: two plates and a spring, slipping
    for dx in (-22, 22):
        d.rounded_rectangle((ex + dx - 8, ey - 44, ex + dx + 8, ey + 44), radius=4, fill=(120, 116, 106), outline=ink, width=3)
    d.line((ex - 14, ey, ex + 14, ey), fill=ink, width=5)
    for k in range(4):
        d.line((ex - 12 + 6 * k, ey - 10, ex - 9 + 6 * k, ey + 10), fill=ink, width=3)
    for s in (-1, 1):                                              # slip: one plate turns, the other stays
        d.arc((ex - 58, ey - 58, ex + 58, ey + 58), 200 if s < 0 else 20, 300 if s < 0 else 120, fill=amber, width=7)
    d.polygon([(ex + 24, ey - 66), (ex + 4, ey - 50), (ex + 30, ey - 46)], fill=amber)
    d.polygon([(ex - 24, ey + 66), (ex - 4, ey + 50), (ex - 30, ey + 46)], fill=amber)
    _letters(d, (ex, ey + 92), 'SLIPS', 26, amber)
    d.line((470, 214, 494, 214), fill=ink, width=4)
    d.polygon([(494, 206), (494, 222), (506, 214)], fill=ink)
    for k, s in enumerate(('If a blind is held,', 'the clutch slips:', 'the other blind', 'moves alone.')):
        _letters(d, (492, 350 + k * 28), s, 25, ink)
    for sx, sy in ((26, 26), (w - 27, 26), (26, h - 27), (w - 27, h - 27)):                       # its four screws
        d.ellipse((sx - 7, sy - 7, sx + 7, sy + 7), fill=(150, 146, 136), outline=(70, 66, 60), width=2)
        d.line((sx - 5, sy, sx + 5, sy), fill=(70, 66, 60), width=2)
    img.paste(_fade(p, 1470, k=0.1, dust=0.12), (x0, y0))
    dd = ImageDraw.Draw(img, 'RGBA')                               # chips in the enamel at the edges
    rnd = random.Random(1471)
    for _ in range(6):
        ex_, ey_ = (rnd.choice((rnd.uniform(6, 30), rnd.uniform(w - 30, w - 6))), rnd.uniform(6, h - 6)) if rnd.random() < 0.5 else \
                   (rnd.uniform(6, w - 6), rnd.choice((rnd.uniform(6, 22), rnd.uniform(h - 22, h - 6))))
        r = rnd.uniform(2, 5)
        dd.ellipse((x0 + ex_ - r, y0 + ey_ - r * 0.7, x0 + ex_ + r, y0 + ey_ + r * 0.7), fill=(52, 56, 60, 220))


def make_refuge_wall(img):
    """The refuge's back wall (1 px ~ 1.94 mm): bare concrete, and what three children left on it. Over each place its
    initials, scratched: R.A. (an aeroplane), T.O. (a boat), M (her crooked tree); between them, a window drawn in
    chalk with a sun in it; tally marks; a smudge where heads leant."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    x0, y0, x1, y1 = CELLS2['r_wall']
    w, h = x1 - x0, y1 - y0
    s = w / (WALL2[1] - WALL2[0])                                  # px per metre
    top = WALL2[2] + h / s
    px = lambda x: (x - WALL2[0]) * s
    pz = lambda z: (top - z) * s
    n = _noise(w, h, 5, 1480)
    a = np.ones((h, w, 3)) * np.array([118, 114, 106]) * (0.8 + 0.36 * n)[..., None]
    for yy in range(int(pz(2.95)), h, int(0.3 * s)):              # formwork board marks
        a[yy:yy + 2] *= 0.84
    rng = np.random.default_rng(1481)
    a[rng.random((h, w)) > 0.995] *= 0.55
    yy, xx = np.mgrid[0:h, 0:w]
    for xc in (239.56, 239.87, 240.18):                           # where heads and shoulders leant: darker, polished
        g = np.exp(-(((xx - px(xc)) / (0.11 * s)) ** 2 + ((yy - pz(2.5)) / (0.13 * s)) ** 2))
        a *= (1 - 0.22 * g)[..., None]
    wall = Image.fromarray(np.clip(a, 0, 255).astype('uint8')).convert('RGBA')
    lay = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    rnd = random.Random(1482)
    scratch, shade = (196, 192, 182, 235), (40, 38, 34, 170)

    def scr(pts, wd=3):                                            # a scratch: a pale groove with a dark lip under it
        q = [(x + rnd.uniform(-0.7, 0.7), y + rnd.uniform(-0.7, 0.7)) for x, y in pts]
        d.line([(x + 1.2, y + 1.6) for x, y in q], fill=shade, width=wd)
        d.line(q, fill=scratch, width=wd)

    def scr_text(cx, cy, text, size):
        m = Image.new('L', (w, h), 0)
        ImageDraw.Draw(m).text((cx, cy), text, font=_font(size, 'sans-bold'), fill=255, anchor='mm')
        m = m.filter(ImageFilter.FIND_EDGES).filter(ImageFilter.MaxFilter(3))
        sh = Image.new('RGBA', (w, h), shade[:3] + (0,))
        sh.putalpha(m.point(lambda v: int(v * 0.7)))
        lay.alpha_composite(sh, (2, 2))
        sc = Image.new('RGBA', (w, h), scratch[:3] + (0,))
        sc.putalpha(m.point(lambda v: int(v * 0.92)))
        lay.alpha_composite(sc)
    # The initials, each over its own place.
    scr_text(px(239.56), pz(2.66), 'R.A.', 46)
    scr_text(px(239.87), pz(2.66), 'T.O.', 46)
    scr_text(px(240.18), pz(2.66), 'M', 56)
    # R.A.'s aeroplane
    ax, ay = px(239.56), pz(2.83)
    scr([(ax - 40, ay), (ax + 40, ay - 6)], 4)
    scr([(ax - 8, ay - 3), (ax - 22, ay - 30), (ax - 4, ay - 30), (ax + 12, ay - 4)], 3)
    scr([(ax - 6, ay + 1), (ax - 18, ay + 22), (ax - 2, ay + 22), (ax + 12, ay - 1)], 3)
    scr([(ax - 40, ay), (ax - 46, ay - 16), (ax - 34, ay - 2)], 3)
    # T.O.'s boat
    bx, by = px(239.87), pz(2.81)
    scr([(bx - 38, by), (bx + 38, by), (bx + 26, by + 16), (bx - 26, by + 16), (bx - 38, by)], 3)
    scr([(bx, by), (bx, by - 50)], 3)
    scr([(bx + 2, by - 48), (bx + 30, by - 8), (bx + 2, by - 8)], 3)
    for k in range(3):
        scr([(bx - 40 + 26 * k, by + 26), (bx - 28 + 26 * k, by + 22), (bx - 16 + 26 * k, by + 26)], 2)
    # M's crooked tree, pencil, gone over and over
    pen = ImageDraw.Draw(lay)

    def stroke(pts, weight):
        for _ in range(2):
            q = [(x + rnd.uniform(-1, 1), y + rnd.uniform(-1, 1)) for x, y in pts]
            pen.line(q, fill=(34, 34, 42, 230), width=max(2, int(4 * (0.6 + weight * 0.6))), joint='curve')
    import build_dl05 as dl05
    dl05._crooked_tree(stroke, px(240.18), pz(2.74), 0.2 * s, sx=0.17 * s)
    # A window drawn in chalk above the middle place, the sun in its top pane: an outside, from inside.
    wx0, wx1, wz0, wz1 = px(239.62), px(240.12), pz(3.03), pz(2.86)
    ch = (226, 224, 214, 215)
    for k in range(2):
        o = k * 1.5
        d.rectangle((wx0 + o, wz0 + o, wx1 - o, wz1 - o), outline=ch, width=3)
    d.line(((wx0 + wx1) / 2, wz0, (wx0 + wx1) / 2, wz1), fill=ch, width=3)
    d.line((wx0, (wz0 + wz1) / 2, wx1, (wz0 + wz1) / 2), fill=ch, width=3)
    sx_, sy_ = wx0 + 0.72 * (wx1 - wx0), wz0 + 0.28 * (wz1 - wz0)
    d.ellipse((sx_ - 10, sy_ - 10, sx_ + 10, sy_ + 10), outline=(226, 196, 110, 230), width=4)
    for k in range(8):
        aa = 2 * math.pi * k / 8
        d.line((sx_ + 14 * math.cos(aa), sy_ + 14 * math.sin(aa), sx_ + 21 * math.cos(aa), sy_ + 21 * math.sin(aa)), fill=(226, 196, 110, 220), width=3)
    # Tally marks by the pipe (days, or visits), in pencil.
    tx, tz = px(240.3), pz(2.98)
    for g in range(3):
        for k in range(5 if g < 2 else 3):
            if k == 4:
                pen.line((tx + g * 34 - 4, tz + 18 + g * 0, tx + g * 34 + 26, tz + 2), fill=(40, 40, 48, 210), width=2)
            else:
                pen.line((tx + g * 34 + k * 6, tz, tx + g * 34 + k * 6 + 1, tz + 22), fill=(40, 40, 48, 210), width=2)
    wall.alpha_composite(lay)
    img.paste(wall.convert('RGB').filter(ImageFilter.GaussianBlur(0.5)), (x0, y0))


def make_drive(path):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    img = Image.new('RGB', (1024, 1024), (60, 58, 54))
    make_drive_plate(img)
    make_refuge_wall(img)
    # The clutch plate's face: dark iron, three bold cream bars and an amber wedge, so its turning reads.
    x0, y0, x1, y1 = CELLS2['r_clutch']
    c = Image.new('RGB', (x1 - x0, y1 - y0), (40, 39, 37))
    d = ImageDraw.Draw(c)
    cx = cy = 128
    d.ellipse((2, 2, 253, 253), fill=(150, 116, 56))
    d.ellipse((14, 14, 241, 241), fill=(44, 42, 40))
    for k in range(3):
        aa = math.radians(90 + 120 * k)
        pts = [(cx + r * math.cos(aa + da), cy - r * math.sin(aa + da)) for r, da in ((34, -0.32), (112, -0.13), (112, 0.13), (34, 0.32))]
        d.polygon(pts, fill=(226, 220, 200))
    d.pieslice((18, 18, 237, 237), -95, -55, fill=(214, 140, 40))
    d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=(70, 68, 64))
    d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=(24, 23, 22))
    for k in range(6):
        aa = math.radians(k * 60)
        d.ellipse((cx + 22 * math.cos(aa) - 4, cy + 22 * math.sin(aa) - 4, cx + 22 * math.cos(aa) + 4, cy + 22 * math.sin(aa) + 4), fill=(24, 23, 22))
    img.paste(_fade(c, 1490, k=0.06, dust=0.1), (x0, y0))
    # The A and B roundels: enamel, green on cream.
    for name, t in (('r_lblA', 'A'), ('r_lblB', 'B')):
        x0, y0, x1, y1 = CELLS2[name]
        r = Image.new('RGB', (64, 64), (34, 62, 50))
        dr = ImageDraw.Draw(r)
        dr.ellipse((1, 1, 62, 62), fill=(220, 212, 186), outline=(34, 62, 50), width=5)
        dr.text((32, 34), t, font=_font(40, 'carlito'), fill=(34, 62, 50), anchor='mm')
        img.paste(r, (x0, y0))
    # The biscuit tin: its lid (a painted oval, ASSORTED, biscuits round it) and its side band.
    x0, y0, x1, y1 = CELLS2['r_tinlid']
    t = Image.new('RGB', (128, 96), (46, 70, 106))
    dt = ImageDraw.Draw(t)
    dt.rectangle((3, 3, 124, 92), outline=(184, 150, 70), width=4)
    dt.ellipse((16, 14, 112, 82), fill=(212, 196, 150), outline=(184, 150, 70), width=4)
    dt.text((64, 40), 'ASSORTED', font=_font(15, 'carlito'), fill=(120, 40, 34), anchor='mm')
    dt.text((64, 58), 'BISCUITS', font=_font(12, 'carlito'), fill=(60, 50, 40), anchor='mm')
    for k in range(4):
        dt.ellipse((6 + k * 30, 76, 18 + k * 30, 88), fill=(176, 130, 70))
    img.paste(_fade(t, 1491, k=0.2, dust=0.2), (x0, y0))
    x0, y0, x1, y1 = CELLS2['r_tinside']
    ts = Image.new('RGB', (256, 32), (46, 70, 106))
    dts = ImageDraw.Draw(ts)
    dts.rectangle((0, 10, 255, 21), fill=(184, 150, 70))
    for k in range(10):
        dts.ellipse((6 + k * 25, 12, 16 + k * 25, 20), fill=(120, 40, 34))
    img.paste(_fade(ts, 1492, k=0.2, dust=0.2), (x0, y0))
    # Their three places: a faded red cushion (R.A.), a ticking cushion (T.O.), a folded army blanket (M).
    rng = np.random.default_rng(1493)
    for name, kind in (('r_cushA', 'red'), ('r_cushO', 'ticking'), ('r_blanket', 'blanket')):
        x0, y0, x1, y1 = CELLS2[name]
        n = _noise(128, 128, 3, int(rng.integers(1, 9999)))
        if kind == 'red':
            a = np.ones((128, 128, 3)) * np.array([132, 52, 42], float)
            yy, xx = np.mgrid[0:128, 0:128]
            a[((xx // 16 + yy // 16) % 2) == 0] *= 0.86                      # a faded check
        elif kind == 'ticking':
            a = np.ones((128, 128, 3)) * np.array([196, 190, 170], float)
            for k in range(0, 128, 14):
                a[:, k:k + 5] = np.array([60, 74, 112], float)
        else:
            a = np.ones((128, 128, 3)) * np.array([94, 94, 98], float)
            a[20:28] = np.array([124, 50, 44], float)
            for k in range(44, 128, 28):
                a[k:k + 3] *= 0.7                                             # the folds
        a *= (0.82 + 0.3 * n)[..., None]
        img.paste(Image.fromarray(np.clip(a, 0, 255).astype('uint8')), (x0, y0))
    for name, rgb in SWATCH2.items():
        x0, y0, x1, y1 = CELLS2[name]
        ImageDraw.Draw(img).rectangle((x0, y0, x1 - 1, y1 - 1), fill=rgb)
    img.filter(ImageFilter.GaussianBlur(0.4)).save(path, optimize=True)


def make_textures():
    os.makedirs(TEX, exist_ok=True)
    make_panels(os.path.join(TEX, 'dl14_panels.png'))
    make_atlas(os.path.join(TEX, 'dl14_atlas.png'))
    make_chain(os.path.join(TEX, 'dl14_chain.png'))
    make_drive(os.path.join(TEX, 'dl14_drive.png'))


# =====================================================================================================================
# Mesh building
# =====================================================================================================================
class MB:
    """One object being built: faces tagged by material name. Faces flagged 'flat' keep the winding they were built
    with (decals, which are one-sided in the game); the rest have their normals recalculated outward."""

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
        """Every loop of the faces round these verts samples one atlas swatch."""
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

    def decal(self, mt, x0, x1, z0, z1, y, cell=None, uvr=None):
        """A picture on a wall, facing the camera (-y)."""
        u0, v0, u1, v1 = uvr or cell_uv(cell)
        return self.face(mt, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

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
            if 'sw_' in c:
                u0 = u1 = (u0 + u1) / 2
                v0 = v1 = (v0 + v1) / 2
            self.face(mt, pts, [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
        return n0

    def prism_xz(self, mt, pts, y0, y1):
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
        return f + b

    def prism_yz(self, mt, pts, x0, x1):
        bm = self.bm
        f = [bm.verts.new((x0, y, z)) for y, z in pts]
        b = [bm.verts.new((x1, y, z)) for y, z in pts]
        fs = [bm.faces.new(f), bm.faces.new(list(reversed(b)))]
        for i in range(len(pts)):
            j = (i + 1) % len(pts)
            fs.append(bm.faces.new((f[j], f[i], b[i], b[j])))
        for fc in fs:
            fc.material_index = self.m(mt)
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


def Ry(a, about=(0, 0, 0)):
    p = Vector(about)
    return Matrix.Translation(p) @ Matrix.Rotation(a, 4, 'Y') @ Matrix.Translation(-p)


# =====================================================================================================================
# The corridor's shell
# =====================================================================================================================
def holed_wall(B, x0, x1, y0, y1, z0, z1, holes, split=1.0, lower='WinDado', upper='WinPlaster'):
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


def wall_runs(holes, z0, z1, xa=233.0, xb=END_X):
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


def build_shell(B):
    holes = [(CUP_DOOR[0], CUP_DOOR[1], 0.0, CUP_DOOR[2])] + [(x0, x1, SILL, HEAD) for _, x0, x1, _v in WINDOWS] + \
            [(HATCH[0], HATCH[1], HATCH[2], HATCH[3]), (END_DOOR[0], END_DOOR[1], 0.0, END_DOOR[2])]
    holed_wall(B, X0, END_X, WALL_Y, WALL_Y1, 0.0, CEIL, holes)
    # The back layer behind the windows (the cupboard is behind the wall from 232.25 to 235.15).
    holed_wall(B, X0, 232.25, WALL_Y1, WALL_Y2, 0.0, CEIL, [], upper='WinPlaster', lower='WinPlaster')
    holed_wall(B, 235.15, END_X, WALL_Y1, WALL_Y2, 0.0, CEIL, [(HATCH[0], HATCH[1], HATCH[2], HATCH[3])],
               upper='WinPlaster', lower='WinPlaster')
    # Floor, ceiling and cornice; the end wall; the joint with DL-13 at 232.
    B.box('WinLino', X0, X1, -1.6, WALL_Y1, -0.2, 0.0)
    B.box('WinLino', 235.15, X1, WALL_Y1, WALL_Y2, -0.2, 0.0)
    B.box('WinPlaster', X0, X1, -1.0, WALL_Y2, CEIL, CEIL + 0.15)
    B.box('WinPlaster', X0, END_X, WALL_Y - 0.08, WALL_Y, CEIL - 0.1, CEIL)
    B.box('WinPlaster', X0, END_X, WALL_Y - 0.03, WALL_Y, CEIL - 0.16, CEIL - 0.1)
    B.box('WinDado', END_X, X1, -1.0, WALL_Y2, 0.0, 1.0)
    B.box('WinPlaster', END_X, X1, -1.0, WALL_Y2, 1.0, CEIL)
    B.box('PigeonWood', END_X - 0.02, END_X, -1.0, WALL_Y, 0.0, 0.12)
    B.box('WinPlaster', X0, X0 + 0.2, -1.0, WALL_Y, 3.55, CEIL)                  # bulkhead over the way in
    B.box('WinPlaster', X0, X0 + 0.12, WALL_Y - 0.12, WALL_Y, LAND_H, 3.55)       # and its pilaster
    # Skirting and dado rail, along the wall between openings.
    for a, b in wall_runs(holes, 0.0, 0.12):
        B.box('PigeonWood', a, b, WALL_Y - 0.02, WALL_Y, 0.0, 0.12)
    for a, b in wall_runs(holes, 0.98, 1.03):
        B.box('PigeonWood', a, b, WALL_Y - 0.03, WALL_Y, 0.98, 1.03)
    # The landing at gallery level (232..233), on a plastered mass.
    B.box('WinDado', X0, STAIR[0], -0.45, WALL_Y, 0.0, 1.0)
    B.box('WinPlaster', X0, STAIR[0], -0.45, WALL_Y, 1.0, LAND_H - 0.05)
    B.box('PigeonWood', X0, STAIR[0] + 0.03, -0.47, WALL_Y, LAND_H - 0.05, LAND_H)
    B.box('PigeonWood', STAIR[0] - 0.02, STAIR[0] + 0.03, -0.47, WALL_Y, LAND_H - 0.12, LAND_H - 0.05)
    return holes


def build_stair(B):
    """Open-riser treads on two stringers, steep as a ship's stair; the handrail on the wall side. Collision: each
    tread is solid from x0 to x1 at its top (TREADS)."""
    for x0, x1, h in TREADS:
        B.box('CrateWood', x0 - 0.005, x1 + 0.025, -0.40, 0.40, h - 0.045, h)
        B.box('CrateWood', x1 - 0.005, x1 + 0.03, -0.40, 0.40, h - 0.07, h - 0.045)       # the nosing's lip
    k = (TREADS[0][2] - TREADS[-1][2]) / (TREADS[-1][0] - TREADS[0][0])
    T = lambda x: TREADS[0][2] + 0.07 - k * (x - STAIR[0])
    xt = STAIR[0] + T(STAIR[0]) / k
    xb = STAIR[0] + (T(STAIR[0]) - 0.3) / k
    poly = [(STAIR[0], T(STAIR[0])), (STAIR[0], T(STAIR[0]) - 0.3), (xb, 0.0), (xt, 0.0)]
    for y0, y1 in ((-0.44, -0.40), (0.40, 0.44)):
        B.prism_xz('PigeonWood', poly, y0, y1)
    # Newel at the foot, rail and spindles on the wall side (behind the lane: they hide nothing).
    B.box('PigeonWood', 234.32, 234.40, 0.34, 0.42, 0.0, 1.2)
    B.box('PigeonWood', 234.32, 234.40, -0.42, -0.335, 0.0, 1.2)            # the front newel: the pole leans on it
    B.box('PigeonWood', 234.30, 234.42, -0.44, -0.32, 1.2, 1.26)
    B.box('PigeonWood', 234.30, 234.42, 0.32, 0.44, 1.2, 1.26)
    rail = lambda x: 1.26 + (234.36 - x) * (1.6 / 1.36)
    B.cyl('PigeonWood', (234.36, 0.38, 1.25), (233.0, 0.38, rail(233.0)), 0.024, seg=8)
    B.box('PigeonWood', 232.96, 233.04, 0.34, 0.42, LAND_H, rail(233.0) + 0.04)
    for x in (233.3, 233.6, 233.9, 234.15):
        B.cyl('PigeonWood', (x, 0.42, T(x)), (x, 0.42, rail(x)), 0.012, seg=6)


def build_windows(B):
    """Each window: the painted panel in the recess, its frame and bars, its sill board, a pelmet over its roller.
    The static ones have their ledges folded up; W4's blind is stuck half down."""
    for name, x0, x1, var in WINDOWS:
        xc = (x0 + x1) / 2
        uvp = lambda x, z: panel_uv(var, (x - x0) / (x1 - x0), (z - SILL) / (HEAD - SILL))
        if name == 'B':                                           # B's panel, less the peeled corner (AttPanelPeel)
            (hx, hz), (cx, cz), (gx, gz) = PEEL
            for poly in ([(x0, SILL), (x1, SILL), (x1, cz), (x0, cz)],
                         [(cx, cz), (x1, cz), (x1, HEAD), (cx, HEAD)],
                         [(x0, cz), (hx, hz), (gx, gz), (cx, HEAD), (x0, HEAD)]):
                B.face('WinPanel', [(x, PANEL_Y, z) for x, z in poly], [uvp(x, z) for x, z in poly])
            # behind the corner: concrete, and Mara's trees in pencil
            B.decal('WinAtlas', 238.42, 238.92, 0.53, 1.28, WALL_Y1 - 0.001, cell='pencil')
        else:
            B.face('WinPanel', [(x0, PANEL_Y, SILL), (x1, PANEL_Y, SILL), (x1, PANEL_Y, HEAD), (x0, PANEL_Y, HEAD)],
                   [uvp(x0, SILL), uvp(x1, SILL), uvp(x1, HEAD), uvp(x0, HEAD)])
        fy0, fy1 = PANEL_Y - 0.065, PANEL_Y - 0.004
        B.box('PigeonWood', x0, x0 + 0.05, fy0, fy1, SILL, HEAD)
        B.box('PigeonWood', x1 - 0.05, x1, fy0, fy1, SILL, HEAD)
        B.box('PigeonWood', x0, x1, fy0, fy1, HEAD - 0.05, HEAD)
        B.box('PigeonWood', x0, x1, fy0, fy1, SILL, SILL + 0.05)
        B.box('PigeonWood', xc - 0.02, xc + 0.02, fy0 + 0.01, fy1, SILL, HEAD)
        for tz in TRANSOMS:
            B.box('PigeonWood', x0, x1, fy0 + 0.01, fy1, tz - 0.02, tz + 0.02)
        B.box('PigeonWood', x0 - 0.04, x1 + 0.04, WALL_Y - 0.06, PANEL_Y, SILL - 0.04, SILL)
        # Pelmet over the roller (each leaves the chain's runs clear).
        px0, px1 = {'A': (236.40, 237.58), 'B': (237.82, 238.93), 'W0': (235.2, 236.2)}.get(name, (x0 - 0.05, x1 + 0.05))
        B.box('PigeonWood', px0, px1, 0.66, WALL_Y, 3.06, 3.28)
        B.box('PigeonWood', px0 - 0.01, px1 + 0.01, 0.65, 0.67, 3.24, 3.29)
        # Hinge leaves on the wall for the ledge (the knuckle goes with the ledge).
        hz = {'A': LEDGE_A[2], 'B': LEDGE_B[2]}.get(name, 1.1)
        for hx in (x0 + 0.2, xc, x1 - 0.2):
            B.box('WornIron', hx - 0.035, hx + 0.035, WALL_Y - 0.006, WALL_Y, hz - 0.14, hz - 0.02)
        if name in ('A', 'B'):
            continue
        # Static: the ledge folded up flat against the wall; the blind rolled up (W4's stuck half down).
        B.box('CrateWood', x0 - 0.02, x1 + 0.02, WALL_Y - 0.06, WALL_Y - 0.01, hz, hz + 1.2)
        B.box('CrateWood', x0 - 0.02, x1 + 0.02, WALL_Y - 0.09, WALL_Y - 0.06, hz + 1.16, hz + 1.2)
        if name == 'W4':
            fz = 2.2
            u0, v0, u1, v1 = cell_uv('blind2')
            B.face('WinAtlas', [(x0 + 0.04, BLIND_FACE_Y, fz), (x1 - 0.04, BLIND_FACE_Y, fz), (x1 - 0.04, BLIND_FACE_Y, 3.1),
                                (x0 + 0.04, BLIND_FACE_Y, 3.1)], [(u0, v0 + 0.35 * (v1 - v0)), (u1, v0 + 0.35 * (v1 - v0)), (u1, v1), (u0, v1)])
            B.box('PigeonWood', x0 + 0.03, x1 - 0.03, BLIND_FACE_Y - 0.015, BLIND_FACE_Y + 0.01, fz - 0.03, fz + 0.02)
        if name == 'W5':                                          # a torn strip hangs from W5's roller
            u0, v0, u1, v1 = cell_uv('blind2')
            B.face('WinAtlas', [(x1 - 0.32, BLIND_FACE_Y, 2.55), (x1 - 0.12, BLIND_FACE_Y, 2.7), (x1 - 0.1, BLIND_FACE_Y, 3.1),
                                (x1 - 0.34, BLIND_FACE_Y, 3.1)], [(u0, v0 + 0.7 * (v1 - v0)), (u0 + 0.25 * (u1 - u0), v0 + 0.78 * (v1 - v0)),
                                                                  (u0 + 0.27 * (u1 - u0), v1), (u0, v1)])


def build_hatch(B):
    """The way on: a high hatch at 239.25..240.15, sill 2.15, its door open inward on the dark; an iron landing lane-deep
    in front of it, one mantle up from ledge B."""
    x0, x1, z0, z1 = HATCH
    for a, b, c, d in ((x0 - 0.05, x0, z0 - 0.05, z1 + 0.05), (x1, x1 + 0.05, z0 - 0.05, z1 + 0.05),
                       (x0 - 0.05, x1 + 0.05, z1, z1 + 0.05)):
        B.box('WornIron', a, b, WALL_Y - 0.025, WALL_Y, c, d)
    # Behind it (rev 0.3), the room the children kept: concrete, floored with boards, its back wall marked (WinDrive's
    # r_wall); the duct goes on from its right side, low, behind the painted windows toward DL-15.
    dx0, dx1, dy0, dy1 = DEN
    B.box('CrateWood', dx0 - 0.1, dx1 + 0.1, dy0, dy1 + 0.1, z0 - 0.1, z0)
    for k in range(1, 9):                                                               # its boards' seams
        y = dy0 + (dy1 - dy0) * k / 9
        B.box('PigeonWood', dx0, dx1, y - 0.004, y + 0.004, z0, z0 + 0.002)
    B.box('WinPlaster', dx0 - 0.1, dx0, dy0, dy1 + 0.1, z0, DEN_TOP)
    B.box('WinPlaster', dx1, dx1 + 0.1, DUCT[1], dy1 + 0.1, z0, DEN_TOP)
    B.box('WinPlaster', dx1, dx1 + 0.1, dy0, DUCT[1], z0 + DUCT[2], DEN_TOP)
    B.box('WinPlaster', dx0 - 0.1, dx1 + 0.1, dy0, dy1 + 0.1, DEN_TOP, DEN_TOP + 0.1)
    B.box('WinPlaster', dx0 - 0.1, dx1 + 0.1, dy1, dy1 + 0.1, z0, DEN_TOP)
    B.decal('WinDrive', WALL2[0], WALL2[1], WALL2[2], WALL2[2] + (WALL2[1] - WALL2[0]) * 480 / 768, dy1 - 0.001, cell='r_wall')
    B.box('WinAtlas', dx1 + 0.1, dx1 + 0.6, dy0 - 0.05, DUCT[1] + 0.05, z0 - 0.05, z0 + DUCT[2] + 0.05, cell='sw_dark')
    B.box('WornIron', dx1 - 0.01, dx1 + 0.1, dy0, DUCT[1], z0 + DUCT[2] - 0.03, z0 + DUCT[2])                # its lintel
    B.box('PigeonWood', x0 + 0.005, x0 + 0.035, WALL_Y2 + 0.02, WALL_Y2 + 0.86, z0 + 0.02, z1 - 0.02)   # the door, open in
    lx0, lx1, lh = HATCH_LAND
    B.box('WornIron', lx0, lx1, LEDGE_Y[0], WALL_Y, lh - 0.035, lh)
    B.box('WornIron', lx0, lx1, LEDGE_Y[0], LEDGE_Y[0] + 0.025, lh - 0.09, lh)
    for x in (lx0 + 0.05, (lx0 + lx1) / 2, lx1 - 0.05):
        B.box('WornIron', x - 0.012, x + 0.012, LEDGE_Y[0], WALL_Y, lh - 0.07, lh - 0.035)
    for x in (lx0 + 0.04, lx1 - 0.04):
        B.cyl('WornIron', (x, WALL_Y - 0.01, lh - 0.55), (x, LEDGE_Y[0] + 0.08, lh - 0.06), 0.016, seg=6)
        B.box('WornIron', x - 0.03, x + 0.03, WALL_Y - 0.01, WALL_Y, lh - 0.62, lh - 0.48)


def build_end(B):
    """The dark end: a radiator under each of the last windows, a stack of small chairs, a closed classroom door."""
    for name, x0, x1, _v in WINDOWS[3:]:
        a, b = x0 + 0.1, x1 - 0.1
        n = 9
        for k in range(n):
            x = a + (b - a) * (k + 0.5) / n
            B.box('WornIron', x - 0.03, x + 0.03, 0.73, 0.86, 0.13, 0.48)
        B.box('WornIron', a, b, 0.76, 0.83, 0.44, 0.47)
        B.box('WornIron', a, b, 0.76, 0.83, 0.14, 0.17)
        for x in (a + 0.03, b - 0.03):
            B.box('WornIron', x - 0.02, x + 0.02, 0.74, 0.85, 0.0, 0.13)
        B.cyl('WornIron', (b, 0.84, 0.16), (b + 0.12, 0.84, 0.16), 0.018, seg=8)
        B.cyl('WornIron', (b + 0.12, 0.84, 0.16), (b + 0.12, 0.84, 0.0), 0.018, seg=8)
    # Small chairs, stacked by the door: everything here at child height.
    for k in range(3):
        z = k * 0.06
        x, y = 246.08, 0.6
        B.box('CrateWood', x - 0.15, x + 0.15, y - 0.14, y + 0.14, 0.27 + z, 0.295 + z)
        for dx in (-0.13, 0.13):
            for dy in (-0.12, 0.12):
                B.box('PigeonWood', x + dx - 0.012, x + dx + 0.012, y + dy - 0.012, y + dy + 0.012, z, 0.27 + z)
            B.box('PigeonWood', x + dx - 0.012, x + dx + 0.012, y + 0.11, y + 0.135, 0.295 + z, 0.55 + z)
        B.box('CrateWood', x - 0.14, x + 0.14, y + 0.11, y + 0.135, 0.44 + z, 0.53 + z)
    # The door (closed), its architrave, a vision panel onto nothing, a knob, and the class's plate.
    x0, x1, h = END_DOOR
    B.box('PigeonWood', x0, x1, 1.0, 1.05, 0.0, h)
    for a, b, c, d in ((x0 + 0.1, x1 - 0.1, 0.15, 0.85), (x0 + 0.1, x1 - 0.1, 0.95, 1.25)):
        B.box('PigeonWood', a, b, 0.985, 1.0, c, d)
    B.box('WinAtlas', x0 + 0.2, x1 - 0.2, 0.99, 1.0, 1.35, 1.85, cell='sw_glass')
    for a, b, c, d in ((x0 - 0.07, x0, 0.0, h + 0.07), (x1, x1 + 0.07, 0.0, h + 0.07), (x0 - 0.07, x1 + 0.07, h, h + 0.07)):
        B.box('PigeonWood', a, b, WALL_Y - 0.025, WALL_Y, c, d)
    B.sphere('WinAtlas', (x1 - 0.1, 0.96, 0.92), 0.03, seg=8, cell='sw_brass')
    B.cyl('WinAtlas', (x1 - 0.1, 1.0, 0.92), (x1 - 0.1, 0.96, 0.92), 0.012, seg=6, cell='sw_brass')
    B.decal('WinAtlas', (x0 + x1) / 2 - 0.15, (x0 + x1) / 2 + 0.15, h + 0.12, h + 0.195, WALL_Y - 0.002, cell='class5')


def build_props(B):
    """The teacher's desk, the clock, the drill notice, the crank's gearbox and the chain's pulleys, the wheel's bracket."""
    # The desk across the lane (solid; top 0.62).
    dx0, dx1, top = DESK
    B.box('CrateWood', dx0 - 0.02, dx1 + 0.02, -0.37, 0.47, top - 0.035, top)
    B.box('PigeonWood', dx0, dx0 + 0.3, -0.33, 0.43, 0.04, top - 0.035)
    B.box('PigeonWood', dx1 - 0.06, dx1, -0.33, 0.43, 0.04, top - 0.035)
    B.box('PigeonWood', dx0 + 0.3, dx1 - 0.06, -0.33, -0.30, 0.2, top - 0.035)
    for a, b in ((dx0 + 0.04, dx0 + 0.26), (dx0 + 0.34, dx1 - 0.1)):
        B.box('PigeonWood', a, b, -0.345, -0.33, 0.24, top - 0.08)
    for x in (dx0, dx0 + 0.3, dx1 - 0.06, dx1):
        B.box('PigeonWood', x - 0.015, x + 0.015, -0.34, 0.44, 0.0, 0.04)
    # On it, at the back edge: the bell, the register, an inkwell.
    B.cyl('WinAtlas', (dx1 - 0.12, 0.36, top), (dx1 - 0.12, 0.36, top + 0.06), 0.045, 0.022, seg=12, cell='sw_brass')
    B.cyl('WinAtlas', (dx1 - 0.12, 0.36, top + 0.06), (dx1 - 0.12, 0.36, top + 0.13), 0.012, 0.016, seg=8, cell='sw_wood')
    B.tbox('WinAtlas', dx0 + 0.08, dx0 + 0.33, 0.24, 0.44, top, top + 0.035,
           {'+z': 'register', 'all': 'sw_green'})
    B.cyl('WinAtlas', (dx0 + 0.45, 0.38, top), (dx0 + 0.45, 0.38, top + 0.05), 0.025, seg=8, cell='sw_ink')
    # The clock over the cupboard door: stopped.
    B.cyl('PigeonWood', (233.5, WALL_Y, 3.25), (233.5, WALL_Y - 0.05, 3.25), 0.17, seg=20)
    B.face('WinAtlas', [(233.5 + 0.15 * math.cos(a), WALL_Y - 0.052, 3.25 + 0.15 * math.sin(a)) for a in
                        (2 * math.pi * k / 16 for k in range(16))],
           [(cell_mid('clock')[0] + 0.0605 * math.cos(a), cell_mid('clock')[1] + 0.0605 * math.sin(a)) for a in
            (2 * math.pi * k / 16 for k in range(16))])
    # The window drill, framed on the crank's pier.
    B.box('PigeonWood', 242.70, 243.20, WALL_Y - 0.02, WALL_Y, 1.18, 1.45)
    B.decal('WinAtlas', 242.72, 243.18, 1.2, 1.43, WALL_Y - 0.021, cell='notice')
    # The crank's gearbox, its chain sprocket above, and its plate.
    B.box('WornIron', 242.22, 242.58, 0.74, WALL_Y, 0.28, 1.1)
    B.box('WornIron', 242.18, 242.62, 0.84, WALL_Y, 0.24, 0.3)
    B.cyl('WornIron', (242.4, 0.74, 0.5), (242.4, 0.70, 0.5), 0.06, seg=14)
    # Rev 0.3: the drive plate (it replaces the little BLINDS A B plate): one chain, two blinds, A down = B up; the
    # clutch slips if a blind is held. Enamel on a steel backing, four screws.
    px0, px1, pz0, pz1 = DRIVE_PLATE
    B.box('WornIron', px0 - 0.012, px1 + 0.012, WALL_Y - 0.008, WALL_Y, pz0 - 0.012, pz1 + 0.012)
    B.decal('WinDrive', px0, px1, pz0, pz1, WALL_Y - 0.009, cell='r_drive')
    # A and B, on the two blinds' pelmets and on A's chain wheel's wall plate, so the plate's letters have places.
    for name, xc, zc, r in (('r_lblA', 236.99, 3.17, 0.055), ('r_lblB', 238.375, 3.17, 0.055), ('r_lblA', 235.19, 0.17, 0.035)):
        y = 0.6585 if zc > 3 else WALL_Y - 0.016
        u0, v0, u1, v1 = cell_uv(name)
        ring = [2 * math.pi * k / 16 for k in range(16)]
        B.face('WinDrive', [(xc + r * math.cos(a), y, zc + r * math.sin(a)) for a in ring],
               [((u0 + u1) / 2 + (u1 - u0) / 2 * math.cos(a), (v0 + v1) / 2 + (v1 - v0) / 2 * math.sin(a)) for a in ring])
    # The clutch's static half behind A's wheel (AttClutch is the plate that turns): a friction ring, its spring.
    cx, cy, cz, cr = CLUTCH
    B.cyl('WinAtlas', (cx, cy + 0.02, cz), (cx, cy + 0.03, cz), cr - 0.012, seg=24, cell='sw_brass')
    B.cyl('WornIron', (cx, cy + 0.03, cz), (cx, cy + 0.05, cz), cr - 0.02, seg=24)
    for k in range(7):
        B.torus('WornIron', (cx, cy + 0.06 + k * 0.016, cz), (0, 1, 0), 0.034, 0.006, seg=12, rseg=4)
    B.cyl('WornIron', (cx, WALL_Y - 0.016, cz), (cx, cy + 0.16, cz), 0.05, seg=14)
    sx, sz, sr = S0
    pulley(B, sx, sz, sr, axle_to=0.74)
    # Ceiling pulleys and the rollers' sprockets (static), each on an axle from the wall.
    for x, z, r in PULLEYS:
        pulley(B, x, z, r)
    for gx0, gx1 in ((237.6, 237.72), (238.90, 239.0)):            # the rollers' right-angle drives
        B.box('WornIron', gx0, gx1, 0.70, 0.82, ROLLER_Z - 0.07, ROLLER_Z + 0.07)
    for x0, x1 in ((236.45, 237.62), (237.82, 238.93)):            # the rollers themselves, in their pelmets
        B.cyl('WinAtlas', (x0, ROLLER_Y, ROLLER_Z), (x1, ROLLER_Y, ROLLER_Z), ROLLER_R, seg=10, cell='sw_wood')
    # A's chain wheel's bracket: a wall plate, the axle, and two lugs with slots the pole slides through (along x).
    wx, wy, wz, wr = WHEEL_A
    B.box('WornIron', wx - 0.25, wx + 0.25, WALL_Y - 0.015, WALL_Y, wz - 0.2, wz + 0.13)
    B.cyl('WornIron', (wx, WALL_Y, wz), (wx, wy - 0.04, wz), 0.018, seg=10)
    jx, jy, jz = JAM
    for lx in (jx - LUG_DX, jx + LUG_DX):
        B.box('WornIron', lx - 0.012, lx + 0.012, jy + 0.035, WALL_Y, jz - 0.04, jz + 0.04)         # the arm
        B.box('WornIron', lx - 0.0125, lx + 0.0125, jy - 0.05, jy + 0.035, jz + 0.03, jz + 0.045)  # the eye: top
        B.box('WornIron', lx - 0.0125, lx + 0.0125, jy - 0.05, jy + 0.035, jz - 0.045, jz - 0.03)  # bottom
        B.box('WornIron', lx - 0.0125, lx + 0.0125, jy - 0.05, jy - 0.035, jz - 0.045, jz + 0.045)  # front
    # The globe that has gone out, at the dark end.
    B.cyl('WornIron', (245.2, 0.0, CEIL), (245.2, 0.0, 3.4), 0.01, seg=6)
    B.cyl('WornIron', (245.2, 0.0, CEIL), (245.2, 0.0, CEIL - 0.03), 0.05, seg=10)
    B.sphere('WinAtlas', (245.2, 0.0, 3.27), 0.12, seg=12, cell='sw_glass')
    for x in LAMPS:
        B.cyl('WornIron', (x, 0.0, CEIL), (x, 0.0, 3.4), 0.01, seg=6)
        B.cyl('WornIron', (x, 0.0, CEIL), (x, 0.0, CEIL - 0.03), 0.05, seg=10)
        B.cyl('WornIron', (x, 0.0, 3.4), (x, 0.0, 3.36), 0.045, 0.06, seg=10)


def pulley(B, x, z, r, axle_to=WALL_Y):
    """A chain wheel in the wall plane (axis along y) on an axle from the wall."""
    y = CHAIN_Y
    B.cyl('WornIron', (x, y - 0.0125, z), (x, y + 0.0125, z), r - 0.012, seg=16)
    B.torus('WornIron', (x, y, z), (0, 1, 0), r - 0.008, 0.01, seg=18, rseg=4)
    B.cyl('WornIron', (x, y - 0.03, z), (x, axle_to, z), 0.014, seg=8)
    if axle_to == WALL_Y:
        B.cyl('WornIron', (x, WALL_Y - 0.012, z), (x, WALL_Y, z), 0.04, seg=10)


# The chain's wheels (x, z, r): crank sprocket S0 (in build_props), ceiling pulleys, the rollers' sprockets.
P1, P1b = (242.40, 3.62, 0.10), (242.20, 3.42, 0.10)
Q1, Q2 = (239.25, 3.42, 0.10), (238.85, 3.42, 0.10)
R1, R2 = (235.25, 3.42, 0.10), (234.95, 3.62, 0.10)           # over A's wheel at 235.0
R3, R4 = (237.50, 3.42, 0.10), (237.90, 3.42, 0.10)           # either side of A's roller sprocket
SA, SB = (237.70, ROLLER_Z, 0.10), (239.05, ROLLER_Z, 0.10)
PULLEYS = [P1, P1b, Q1, Q2, R1, R2, R3, R4, SA, SB]


def chain_path():
    """The endless loop (x, z), in order: up from the crank's right side, over P1 and left along the upper run, down
    the wall round A's wheel low at 235.0 and up again, right along the lower run, down round A's roller sprocket
    (between A and B), on round B's sprocket, right to P1', and down round the crank's sprocket."""
    pts = []

    def arc(c, a0, a1, n=8):
        cx, cz, r = c
        for i in range(n + 1):
            a = math.radians(a0 + (a1 - a0) * i / n)
            pts.append((cx + r * math.cos(a), cz + r * math.sin(a)))
    s0 = (S0[0], S0[1], S0[2])
    w = (WHEEL_A[0], WHEEL_A[2], WHEEL_A[3])
    arc(P1, 0, 90)
    arc(R2, 90, 180)
    arc(w, 180, 360, 12)
    arc(R1, 180, 90)
    arc(R3, 90, 0)
    arc(SA, 180, 360, 10)
    arc(R4, 180, 90)
    arc(Q2, 90, 0)
    arc(SB, 180, 360, 10)
    arc(Q1, 180, 90)
    arc(P1b, 90, 0)
    arc(s0, 180, 360, 10)
    out = []
    for p in pts:                                               # drop repeats where arcs meet
        if not out or (Vector(p) - Vector(out[-1])).length > 1e-4:
            out.append(p)
    if (Vector(out[0]) - Vector(out[-1])).length < 1e-4:
        out.pop()
    return out


def build_chain(coll):
    """AttChain: a flat strip 0.028 wide and 0.012 deep along the loop at y CHAIN_Y, links textured on its faces.
    UV v runs along the loop (one tile = two links, about 0.1 m)."""
    pts = [Vector((x, z)) for x, z in chain_path()]
    n = len(pts)
    seg = [(pts[(i + 1) % n] - pts[i]).length for i in range(n)]
    L = sum(seg)
    tile = L / round(L / 0.1)
    hw, y0, y1 = 0.014, CHAIN_Y - 0.006, CHAIN_Y + 0.006
    B = MB()
    mi = B.m('WinChain')
    bm = B.bm
    rings = []
    for i in range(n):
        t = (pts[(i + 1) % n] - pts[i - 1]).normalized()
        nn = Vector((-t.y, t.x))
        a, b = pts[i] - nn * hw, pts[i] + nn * hw
        rings.append([bm.verts.new((a.x, y0, a.y)), bm.verts.new((b.x, y0, b.y)), bm.verts.new((b.x, y1, b.y)),
                      bm.verts.new((a.x, y1, a.y))])
    s = 0.0
    for i in range(n):
        j = (i + 1) % n
        v0, v1 = s / tile, (s + seg[i]) / tile
        s += seg[i]
        for k in range(4):
            kk = (k + 1) % 4
            f = bm.faces.new((rings[i][k], rings[i][kk], rings[j][kk], rings[j][k]))
            f.material_index = mi
            ua, ub = ((0.0, 1.0), (0.95, 1.0), (1.0, 0.0), (0.0, 0.05))[k]
            for lp, uv in zip(f.loops, ((ua, v0), (ub, v0), (ub, v1), (ua, v1))):
                lp[B.uv].uv = uv
    ob = B.obj('AttChain', coll, origin=(239.4, CHAIN_Y, 2.0))
    return ob, L


# =====================================================================================================================
# What the game moves
# =====================================================================================================================
def build_blind(coll, name, x0, x1, bottom, cell='blindA'):
    """A roller blind hanging DOWN from its roller: the fabric, a weighted hem slat and a pull ring. Origin on the
    roller's axis at the fabric's centre; the game scales z (game y) toward 0 to roll it up into the pelmet."""
    B = MB()
    xc = (x0 + x1) / 2
    y = BLIND_FACE_Y
    u0, v0, u1, v1 = cell_uv(cell)
    nx, nz = 6, 8
    top = ROLLER_Z
    grid = []
    for j in range(nz + 1):
        row = []
        for i in range(nx + 1):
            z = top - (top - bottom - 0.03) * j / nz
            x = x0 + (x1 - x0) * i / nx
            wob = 0.006 * math.sin(i * 2.1 + j * 0.7) * (j / nz)
            row.append((x, y + wob, z, u0 + (u1 - u0) * i / nx, v1 - (v1 - v0) * j / nz))
        grid.append(row)
    for j in range(nz):
        for i in range(nx):
            q = [grid[j + 1][i], grid[j + 1][i + 1], grid[j][i + 1], grid[j][i]]
            B.face('WinAtlas', [p[:3] for p in q], [p[3:] for p in q])
    B.box('WinAtlas', x0 - 0.01, x1 + 0.01, y - 0.018, y + 0.012, bottom, bottom + 0.05, cell='sw_wood')
    B.cyl('WinAtlas', (xc, y - 0.02, bottom + 0.02), (xc, y - 0.02, bottom - 0.03), 0.003, seg=4, cell='sw_string')
    B.torus('WinAtlas', (xc, y - 0.02, bottom - 0.05), (0, 1, 0), 0.018, 0.004, seg=12, rseg=4, cell='sw_brass')
    return B.obj(name, coll, origin=(xc, ROLLER_Y, ROLLER_Z))


def build_ledge(coll, name, x0, x1, h, notch=None):
    """A window-cleaner's ledge, built OUT: a board lane-deep (y -0.3 .. 0.9) with its top at h, a lip, two dark wooden
    knee brackets under it and the hinge's knuckle at the wall. Origin on the hinge line (y WALL_Y, z h). It folds UP flat
    against the wall by rotating -90 degrees about x. `notch` (x0, x1) leaves the chain's path clear by the wall."""
    B = MB()
    y0, y1 = LEDGE_Y
    if notch:
        B.box('CrateWood', notch[1], x1, y0, y1 - 0.01, h - 0.045, h)
        B.box('CrateWood', x0, notch[1], y0, notch[0], h - 0.045, h)
    else:
        B.box('CrateWood', x0, x1, y0, y1 - 0.01, h - 0.045, h)
    B.box('CrateWood', x0, x1, y0, y0 + 0.04, h - 0.09, h - 0.045)                     # the front lip
    for x in (x0 + 0.06, x1 - 0.06):
        B.box('CrateWood', x - 0.02, x + 0.02, y0 + 0.04, (notch[0] if notch and x < notch[1] else y1) - 0.02, h - 0.075, h - 0.045)
    kx0 = notch[1] if notch else x0
    B.cyl('CrateWood', (kx0 + 0.02, y1 - 0.012, h - 0.02), (x1 - 0.02, y1 - 0.012, h - 0.02), 0.014, seg=8)
    for hx in (kx0 + 0.2, (kx0 + x1) / 2, x1 - 0.2):
        B.box('CrateWood', hx - 0.03, hx + 0.03, y1 - 0.25, y1 - 0.012, h, h + 0.004)
    for bx in ((x0 + 0.55, x1 - 0.12) if notch else (x0 + 0.18, x1 - 0.18)):
        B.prism_yz('CrateWood', [(y1 - 0.015, h - 0.045), (y1 - 0.015, h - 0.24), (y1 - 0.05, h - 0.24),
                                (0.25, h - 0.06), (0.25, h - 0.045)], bx - 0.008, bx + 0.008)
    return B.obj(name, coll, origin=((x0 + x1) / 2, WALL_Y, h))


def build_peel(coll):
    """AttPanelPeel: the lower-right corner of B's painted panel, a triangle hinged along its diagonal H1-H2, built flat
    (closed, in the panel's plane). Front: the painting; back: hardboard. Origin: the hinge's midpoint."""
    (hx, hz), (cx, cz), (gx, gz) = PEEL
    x0, x1 = 237.85, 238.95
    uvp = lambda x, z: panel_uv(0, (x - x0) / (x1 - x0), (z - SILL) / (HEAD - SILL))
    hb = lambda x, z: ((896 + 128 * (x - hx) / (cx - hx)) / 1024.0, (z - SILL) / (HEAD - SILL))
    B = MB()
    y0, y1 = PANEL_Y, PANEL_Y + 0.006
    tri = [(hx, hz), (cx, cz), (gx, gz)]
    B.face('WinPanel', [(x, y0, z) for x, z in tri], [uvp(x, z) for x, z in tri])
    B.face('WinPanel', [(x, y1, z) for x, z in reversed(tri)], [hb(x, z) for x, z in reversed(tri)])
    for (ax, az), (bx, bz) in zip(tri, tri[1:] + tri[:1]):
        B.face('WinPanel', [(ax, y1, az), (bx, y1, bz), (bx, y0, bz), (ax, y0, az)], [hb(ax, az), hb(bx, bz), hb(bx, bz), hb(ax, az)])
    mid = ((hx + gx) / 2, PANEL_Y, (hz + gz) / 2)
    return B.obj('AttPanelPeel', coll, origin=mid)


def build_crank(coll):
    """AttCrank: the handwheel, its spokes, hub and axle, and a grip worn bright. Origin on the axle at the wheel's
    centre; it turns about the game's z (Blender -y)."""
    B = MB()
    x, y, z, r = CRANK
    B.torus('WornIron', (x, y, z), (0, 1, 0), r, 0.017, seg=28, rseg=6)
    for k in range(4):
        a = math.radians(45 + 90 * k)
        B.cyl('WornIron', (x, y, z), (x + r * math.cos(a), y, z + r * math.sin(a)), 0.011, seg=6)
    B.cyl('WornIron', (x, y - 0.035, z), (x, y + 0.04, z), 0.035, seg=12)
    B.cyl('WornIron', (x, y, z), (x, 0.70, z), 0.018, seg=8)
    gx, gz = x + r * math.cos(math.radians(135)), z + r * math.sin(math.radians(135))
    B.cyl('HandledBrass', (gx, y, gz), (gx, y - 0.11, gz), 0.019, seg=10)
    B.sphere('HandledBrass', (gx, y - 0.115, gz), 0.024, seg=10)
    return B.obj('AttCrank', coll, origin=(x, y, z))


def build_wheel(coll):
    """AttWheelA: A's chain wheel, low on the wall: rim, teeth, five spokes, a hub, and six jam pins standing toward the
    camera that a pole through the bracket's lugs catches. Origin on its axle; it turns about the game's z."""
    B = MB()
    x, y, z, r = WHEEL_A
    B.torus('WornIron', (x, y, z), (0, 1, 0), r - 0.012, 0.012, seg=24, rseg=6)
    for k in range(18):
        a = 2 * math.pi * k / 18
        B.box('WornIron', -0.009, 0.009, -0.01, 0.01, -0.012, 0.012,
              rot=None)
        vs = B.since(B.mark() - 8)
        M = Matrix.Translation((x + r * math.cos(a), y, z + r * math.sin(a))) @ Matrix.Rotation(-a, 4, 'Y')
        for v in vs:
            v.co = M @ v.co
    for k in range(5):
        a = 2 * math.pi * k / 5 + 0.3
        B.cyl('WornIron', (x, y, z), (x + (r - 0.015) * math.cos(a), y, z + (r - 0.015) * math.sin(a)), 0.01, seg=6)
    B.cyl('WornIron', (x, y - 0.03, z), (x, y + 0.02, z), 0.032, seg=12)
    for k in range(6):
        a = 2 * math.pi * k / 6 + 0.2
        px, pz = x + 0.09 * math.cos(a), z + 0.09 * math.sin(a)
        B.cyl('WornIron', (px, y - 0.005, pz), (px, y - 0.06, pz), 0.008, seg=6)
    return B.obj('AttWheelA', coll, origin=(x, y, z))


def build_clutch(coll):
    """AttClutch (rev 0.3): the slipping clutch on A's drive, its pressure plate just behind A's chain wheel, seen through
    the wheel's spokes: a disc 0.24 across, its face painted with three bold cream bars and an amber wedge so its turning
    reads, a brass friction rim, the hub nut. Origin on the axle (235.0, 0.722, 0.32): it spins about Blender y, the
    game's z (toward the camera), as AttWheelA does. The game turns it with the wheel, and alone while the wheel is held
    and the chain slips past."""
    B = MB()
    x, y, z, r = CLUTCH
    B.cyl('WornIron', (x, y + 0.002, z), (x, y + 0.02, z), r, seg=32)
    u0, v0, u1, v1 = cell_uv('r_clutch')
    ring = [2 * math.pi * k / 32 for k in range(32)]
    B.face('WinDrive', [(x + r * math.cos(a), y, z + r * math.sin(a)) for a in ring],
           [((u0 + u1) / 2 + (u1 - u0) / 2 * math.cos(a), (v0 + v1) / 2 + (v1 - v0) / 2 * math.sin(a)) for a in ring])
    B.torus('HandledBrass', (x, y + 0.011, z), (0, 1, 0), r, 0.008, seg=32, rseg=6)
    B.cyl('WornIron', (x, y - 0.012, z), (x, y, z), 0.026, seg=6)                 # the hub nut, hexagonal
    return B.obj('AttClutch', coll, origin=(x, y + 0.01, z))


def _project(B, verts, cell, c, size, front_y=None):
    """UVs for the faces round these verts from an atlas cell, projected: from above for faces that face up, from
    the front (-y) for the rest; c the centre, size (x, y, z) the extent mapped onto the cell."""
    u0, v0, u1, v1 = cell_uv(cell)
    faces = set()
    for v in verts:
        faces.update(v.link_faces)
    for f in faces:
        f.normal_update()
        up = abs(f.normal.z) > 0.6
        for lp in f.loops:
            p = lp.vert.co
            s = 0.5 + (p.x - c[0]) / size[0]
            t = 0.5 + ((p.y - c[1]) / size[1] if up else (p.z - c[2]) / size[2])
            s, t = min(max(s, 0.0), 1.0), min(max(t, 0.0), 1.0)
            lp[B.uv].uv = (u0 + (u1 - u0) * s, v0 + (v1 - v0) * t)


def build_refuge(coll):
    """AttRefuge (rev 0.3; static): the place the last three children shared, behind the hatch, at the duct's mouth,
    seen through the hatch by anyone who climbs to it, lit by a lantern on the floor (its glass AttRefugeLamp,
    EMIT DenLanternGlow). Along the back wall, three places under their marks: R.A.'s faded red cushion, T.O.'s ticking
    cushion, M's folded army blanket by the pipe. In front, the biscuit tin, open, its lid leant on it, crumbs. On M's
    side, a tin cup held to the water pipe with string, mouth to the pipe: for listening."""
    B = MB()
    z0 = HATCH[2]
    rnd = random.Random(1495)
    py = 2.4
    for k, (x, cell, size, tilt) in enumerate(((PLACES[0], 'r_cushA', (0.26, 0.25, 0.075), 0.05), (PLACES[1], 'r_cushO', (0.25, 0.24, 0.07), -0.04),
                                               (PLACES[2], 'r_blanket', (0.27, 0.25, 0.065), 0.02))):
        # a fruit crate stood on end for a seat: four corner posts, slats with gaps, the dark inside
        ch, cw, cd = 0.2 - 0.012 * k, 0.27, 0.24
        M = Matrix.Translation((x, py, z0)) @ Matrix.Rotation(tilt * 0.6, 4, 'Z')
        n0 = set(B.bm.verts)
        B.box('WinDrive', -cw / 2 + 0.012, cw / 2 - 0.012, -cd / 2 + 0.012, cd / 2 - 0.012, 0.0, ch - 0.004, cell='r_sw_dark')
        for sx_ in (-1, 1):
            for sy_ in (-1, 1):
                B.box('WinDrive', sx_ * cw / 2 - 0.012, sx_ * cw / 2 + 0.012, sy_ * cd / 2 - 0.012, sy_ * cd / 2 + 0.012, 0.0, ch, cell='r_sw_wood')
        for za, zb in ((0.012, 0.075), (0.1, 0.165), (ch - 0.03, ch)):
            if zb > ch:
                continue
            B.box('WinDrive', -cw / 2, cw / 2, -cd / 2 - 0.006, -cd / 2 + 0.006, za, min(zb, ch), cell='r_sw_wood')
            for sx_ in (-1, 1):
                B.box('WinDrive', sx_ * cw / 2 - 0.006, sx_ * cw / 2 + 0.006, -cd / 2, cd / 2, za, min(zb, ch), cell='r_sw_wood')
        for v in [v for v in B.bm.verts if v not in n0]:
            v.co = M @ v.co
        # and on it the cushion (or the folded blanket), sat on
        n0 = set(B.bm.verts)
        d17.rounded_box(size, (0.0, 0.0, size[2] / 2), p=3.0 if cell != 'r_blanket' else 6.0, cuts=3, bm=B.bm, mat=B.m('WinDrive'))
        vs = [v for v in B.bm.verts if v not in n0]
        for v in vs:                                                                # dished in the middle
            r2 = (v.co.x / (size[0] / 2)) ** 2 + (v.co.y / (size[1] / 2)) ** 2
            if v.co.z > size[2] * 0.6:
                v.co.z -= 0.022 * max(0.0, 1 - r2) * (1.0 if cell != 'r_blanket' else 0.4)
        for v in vs:
            v.co = M @ Matrix.Translation((0.0, 0.0, ch)) @ Matrix.Rotation(tilt, 4, 'Z') @ v.co
        _project(B, vs, cell, (x, py, z0 + ch + size[2] / 2), (size[0] + 0.03, size[1] + 0.03, size[2] + 0.01))
        if cell == 'r_blanket':                                                     # its folded edge, rolled over the front
            B.cyl('WinDrive', (x - 0.13, py - 0.125, z0 + ch + 0.03), (x + 0.13, py - 0.12, z0 + ch + 0.03), 0.032, seg=10, cell='r_sw_iron')
            B.box('WinDrive', x - 0.13, x + 0.13, py - 0.135, py - 0.115, z0 + ch - 0.09, z0 + ch + 0.03, cell='r_sw_iron')
    # The biscuit tin, open, in front of the middle place; its lid leant against it facing out; crumbs.
    tx, ty = PLACES[1] + 0.02, 1.98
    tw, td, th = 0.21, 0.155, 0.075
    n0 = set(B.bm.verts)
    B.box('WinDrive', tx - tw / 2, tx + tw / 2, ty - td / 2, ty + td / 2, z0, z0 + 0.006, cell='r_sw_tinin')
    for a, b, c, d in ((tx - tw / 2, tx + tw / 2, ty - td / 2, ty - td / 2 + 0.004), (tx - tw / 2, tx + tw / 2, ty + td / 2 - 0.004, ty + td / 2),
                       (tx - tw / 2, tx - tw / 2 + 0.004, ty - td / 2, ty + td / 2), (tx + tw / 2 - 0.004, tx + tw / 2, ty - td / 2, ty + td / 2)):
        vs = B.box('WinDrive', a, b, c, d, z0, z0 + th)
        _project(B, vs, 'r_tinside', (tx, ty, z0 + th / 2), (tw + 0.002, td + 0.002, th + 0.002))
    for k in range(5):                                                              # what is left inside: crumbs
        cx, cy = tx + rnd.uniform(-0.08, 0.08), ty + rnd.uniform(-0.05, 0.05)
        B.box('WinDrive', cx - 0.006, cx + 0.006, cy - 0.005, cy + 0.005, z0 + 0.006, z0 + 0.012, cell='r_sw_crumb')
    for k in range(9):
        cx, cy = tx + rnd.uniform(-0.25, 0.25), ty + rnd.uniform(-0.2, 0.15)
        if abs(cx - tx) < tw / 2 + 0.01 and abs(cy - ty) < td / 2 + 0.01:
            continue
        B.box('WinDrive', cx - 0.005, cx + 0.005, cy - 0.004, cy + 0.004, z0, z0 + 0.006, cell='r_sw_crumb')
    B.box('WinDrive', tx + 0.14, tx + 0.18, ty - 0.11, ty - 0.085, z0, z0 + 0.008, cell='r_sw_crumb')     # half a biscuit
    n0 = set(B.bm.verts)
    lw, ld = tw + 0.008, td + 0.008
    vs = B.box('WinDrive', -lw / 2, lw / 2, -0.006, 0.006, 0.0, ld)
    vs = [v for v in B.bm.verts if v not in n0]
    for v in vs:
        v.co = Matrix.Translation((tx + 0.01, ty - td / 2 - 0.045, z0)) @ Matrix.Rotation(math.radians(-17), 4, 'X') @ v.co
    u0, v0, u1, v1 = cell_uv('r_tinlid')
    faces = set()
    for v in vs:
        faces.update(v.link_faces)
    for f in faces:
        for lp in f.loops:
            lp[B.uv].uv = (u0 + (u1 - u0) * (0.5 + (lp.vert.co.x - tx - 0.01) / lw), v0 + (v1 - v0) * min(1.0, max(0.0, (lp.vert.co.z - z0) / (ld * 0.956))))
    # The water pipe down the back right corner, and the tin cup held to it with string, its mouth to the pipe.
    px, py_ = REF_PIPE
    B.cyl('Copper', (px, py_, z0), (px, py_, DEN_TOP), 0.019, seg=10)
    for z in (z0 + 0.2, DEN_TOP - 0.12):
        B.box('WornIron', px - 0.012, px + 0.012, py_, DEN[3], z - 0.02, z + 0.02)
    cz = z0 + 0.6
    B.cyl('WinDrive', (px - 0.115, py_, cz), (px - 0.018, py_, cz), 0.03, 0.036, seg=14, cell='r_sw_enamel')
    B.torus('WinDrive', (px - 0.019, py_, cz), (1, 0, 0), 0.036, 0.003, seg=14, rseg=4, cell='r_sw_blue')
    B.torus('WinDrive', (px - 0.07, py_, cz + 0.045), (0, 1, 0), 0.02, 0.005, seg=10, rseg=4, cell='r_sw_enamel')
    for k, z in enumerate((cz - 0.012, cz + 0.014)):                               # the string, round the pipe and the cup
        B.torus('WinDrive', (px, py_, z), (0, 0, 1), 0.021, 0.0025, seg=10, rseg=3, cell='r_sw_string')
        B.cyl('WinDrive', (px - 0.015, py_ - 0.02, z), (px - 0.09, py_ - 0.032, z - 0.005 + 0.01 * k), 0.0025, seg=4, cell='r_sw_string')
        B.cyl('WinDrive', (px - 0.015, py_ + 0.02, z), (px - 0.09, py_ + 0.032, z - 0.005 + 0.01 * k), 0.0025, seg=4, cell='r_sw_string')
    B.cyl('WinDrive', (px - 0.09, py_ - 0.033, cz - 0.003), (px - 0.09, py_ + 0.033, cz - 0.003), 0.0025, seg=4, cell='r_sw_string')
    # The lantern on the floor: a base, its cage, its cap and handle (the glass is AttRefugeLamp).
    lx, ly = REF_LAMP
    B.cyl('WinDrive', (lx, ly, z0), (lx, ly, z0 + 0.03), 0.055, 0.05, seg=14, cell='r_sw_iron')
    B.cyl('WinDrive', (lx, ly, z0 + 0.155), (lx, ly, z0 + 0.18), 0.045, 0.02, seg=12, cell='r_sw_iron')
    for k in range(4):
        a = math.pi / 4 + k * math.pi / 2
        B.cyl('WinDrive', (lx + 0.047 * math.cos(a), ly + 0.047 * math.sin(a), z0 + 0.03),
              (lx + 0.042 * math.cos(a), ly + 0.042 * math.sin(a), z0 + 0.158), 0.004, seg=4, cell='r_sw_iron')
    B.torus('WinDrive', (lx, ly, z0 + 0.2), (0, 1, 0), 0.035, 0.003, seg=12, rseg=4, cell='r_sw_iron')
    # A pencil and a crayon dropped on R.A.'s cushion's edge; a sheet of drawing paper under the tin's corner.
    B.cyl('WinDrive', (PLACES[0] - 0.06, 2.2, z0 + 0.004), (PLACES[0] + 0.05, 2.16, z0 + 0.004), 0.004, seg=6, cell='r_sw_brass')
    B.cyl('WinDrive', (PLACES[0] + 0.12, 2.1, z0 + 0.005), (PLACES[0] + 0.17, 2.14, z0 + 0.005), 0.005, seg=6, cell='r_sw_green')
    n0 = set(B.bm.verts)
    B.box('WinDrive', -0.1, 0.1, -0.075, 0.075, 0.0, 0.002, cell='r_sw_paper')
    for v in [v for v in B.bm.verts if v not in n0]:
        v.co = Matrix.Translation((tx - 0.17, ty + 0.05, z0)) @ Matrix.Rotation(0.35, 4, 'Z') @ v.co
    ob = B.obj('AttRefuge', coll)
    L = MB()
    L.cyl('DenLanternGlow', (lx, ly, z0 + 0.035), (lx, ly, z0 + 0.15), 0.036, 0.03, seg=14)
    lamp = L.obj('AttRefugeLamp', coll, origin=(lx, ly, z0 + 0.09))
    return ob, lamp


def build_pole(coll):
    """AttPole: the window pole, 2.2 m: a wooden shaft, a brass hook at the top, a ferrule at the foot, and a grip band
    worn bright at the middle. Built along local z (hook at +z), origin at the middle grip; leaned against the newel by
    its rotation about y."""
    B = MB()
    L = 1.1
    B.cyl('CrateWood', (0, 0, -L + 0.04), (0, 0, L - 0.06), 0.017, seg=10)
    B.cyl('HandledBrass', (0, 0, -L), (0, 0, -L + 0.05), 0.019, 0.018, seg=10)
    B.cyl('HandledBrass', (0, 0, -0.07), (0, 0, 0.07), 0.0195, seg=10)
    B.cyl('HandledBrass', (0, 0, L - 0.08), (0, 0, L - 0.03), 0.02, 0.016, seg=10)
    hook = [(0, 0, L - 0.04), (0, 0, L - 0.005)] + \
           [(0.03 + 0.03 * math.cos(math.radians(a)), 0, L - 0.005 + 0.03 * math.sin(math.radians(a))) for a in (180, 135, 90, 45, 0, -40)]
    for a, b in zip(hook, hook[1:]):
        B.cyl('HandledBrass', a, b, 0.0075, seg=6)
    B.cyl('HandledBrass', (0, 0, L - 0.01), (0, 0, L + 0.0), 0.009, 0.002, seg=6)
    ob = B.obj('AttPole', coll)
    bx, bz = POLE_BASE
    tx, tz = POLE_TOP
    ob.location = ((bx + tx) / 2, POLE_Y, (bz + tz) / 2)
    ob.rotation_euler = (0.0, math.atan2(tx - bx, tz - bz), 0.0)
    return ob


# =====================================================================================================================
# The stock cupboard: the last teacher's corner
# =====================================================================================================================
def build_cupboard(coll):
    B = MB()
    x0, x1, y0, y1, ch = ROOM
    B.box('WinPlaster', x0 - 0.15, x0, y0, y1 + 0.15, 0.0, ch + 0.15)
    B.box('WinPlaster', x1, x1 + 0.15, y0, y1 + 0.15, 0.0, ch + 0.15)
    B.box('WinPlaster', x0 - 0.15, x1 + 0.15, y1, y1 + 0.15, 0.0, ch + 0.15)
    B.box('WinPlaster', x0 - 0.15, x1 + 0.15, y0, y1 + 0.15, ch, ch + 0.15)
    B.box('WinPlaster', x0 - 0.15, x1 + 0.15, y0, y1 + 0.15, -0.2, -0.02)
    B.box('PigeonWood', x0, x1, y0, y1, -0.02, 0.0)
    # The door (ledged and braced), standing open into the room on its left hinge; its architrave on the corridor side.
    dx0, dx1, dh = CUP_DOOR
    n0 = B.mark()
    B.box('PigeonWood', 0.0, 0.58, -0.03, 0.0, 0.0, dh - 0.02)
    for z in (0.12, 0.5, 0.88):
        B.box('PigeonWood', 0.04, 0.54, 0.0, 0.022, z - 0.04, z + 0.04)
    B.sphere('WinAtlas', (0.5, -0.05, 0.55), 0.022, seg=8, cell='sw_brass')
    B.xform(n0, Matrix.Translation((dx0 + 0.01, y0, 0.0)) @ Matrix.Rotation(math.radians(85), 4, 'Z'))
    for a, b, c, d in ((dx0 - 0.06, dx0, 0.0, dh + 0.06), (dx1, dx1 + 0.06, 0.0, dh + 0.06), (dx0 - 0.06, dx1 + 0.06, dh, dh + 0.06)):
        B.box('PigeonWood', a, b, WALL_Y - 0.02, WALL_Y, c, d)
    B.decal('WinAtlas', 233.33, 233.67, dh + 0.09, dh + 0.175, WALL_Y - 0.002, cell='stock')
    # Shelving on the back wall, full of what a school uses up.
    rnd = random.Random(1460)
    sy0, sy1 = y1 - 0.34, y1 - 0.02
    for x in (x0 + 0.05, 233.7, x1 - 0.05):
        B.box('PigeonWood', x - 0.015, x + 0.015, sy0, sy1, 0.0, 2.0)
    levels = (0.06, 0.5, 0.95, 1.4, 1.85)
    for z in levels:
        B.box('PigeonWood', x0 + 0.03, x1 - 0.03, sy0, sy1, z - 0.025, z)
    for z in levels:
        for bay0, bay1 in ((x0 + 0.07, 233.68), (233.72, x1 - 0.07)):
            x = bay0 + 0.01
            while x < bay1 - 0.1:
                kind = rnd.random()
                if kind < 0.42:                                        # a box of exercise books, labelled
                    w = rnd.uniform(0.26, 0.34)
                    if x + w > bay1:
                        break
                    hgt = rnd.uniform(0.22, 0.3) if z < 1.8 else 0.2
                    B.box('WinAtlas', x, x + w, sy0 + 0.03, sy1 - 0.02, z, z + hgt, cell='sw_cardboard')
                    B.decal('WinAtlas', x + 0.04, x + w - 0.04, z + hgt * 0.45, z + hgt * 0.45 + (w - 0.08) * 80 / 256, sy0 + 0.029, cell='boxlabel')
                    x += w + rnd.uniform(0.01, 0.04)
                elif kind < 0.72:                                      # a stack of exercise books
                    w = 0.17
                    if x + w > bay1:
                        break
                    hgt = rnd.uniform(0.06, 0.18)
                    B.tbox('WinAtlas', x, x + w, sy0 + 0.06, sy0 + 0.27, z, z + hgt,
                           {'+z': 'book%d' % rnd.randrange(4), 'all': 'sw_pages'})
                    x += w + 0.02
                elif kind < 0.86:                                      # chalk
                    w = 0.13
                    if x + w > bay1:
                        break
                    B.tbox('WinAtlas', x, x + w, sy0 + 0.05, sy0 + 0.13, z, z + 0.08, {'-y': 'chalkbox', 'all': 'sw_cardboard'})
                    x += w + 0.03
                else:                                                  # ink, or a gap
                    if z < 1.8 and rnd.random() < 0.6:
                        for k in range(rnd.randint(1, 3)):
                            B.cyl('WinAtlas', (x + 0.03 + k * 0.06, sy0 + 0.1, z), (x + 0.03 + k * 0.06, sy0 + 0.1, z + 0.09), 0.025, seg=8, cell='sw_ink')
                    x += 0.2
    for k in range(3):                                                 # rolled maps on top
        B.cyl('WinAtlas', (x0 + 0.2 + k * 0.05, sy0 + 0.1 + k * 0.05, 1.88), (x0 + 1.1 + k * 0.05, sy0 + 0.1 + k * 0.05, 1.88 + 0.02 * k),
              0.03, seg=8, cell='sw_pages')
    # Boxes on the floor by the door, one open on its exercise books.
    for bx0, by0, bz0, w, d, hgt in ((234.32, 1.55, 0.0, 0.6, 0.42, 0.36), (234.36, 2.05, 0.0, 0.56, 0.4, 0.34),
                                     (234.38, 2.08, 0.34, 0.52, 0.36, 0.3), (234.36, 2.55, 0.0, 0.58, 0.44, 0.38)):
        B.box('WinAtlas', bx0, bx0 + w, by0, by0 + d, bz0, bz0 + hgt, cell='sw_cardboard')
        B.decal('WinAtlas', bx0 + 0.08, bx0 + w - 0.08, bz0 + hgt * 0.4, bz0 + hgt * 0.4 + (w - 0.16) * 80 / 256, by0 - 0.001, cell='boxlabel')
    # (the open one: its flaps up, books inside)
    B.box('WinAtlas', 234.32, 234.92, 1.55, 1.56, 0.36, 0.52, cell='sw_cardboard')
    B.tbox('WinAtlas', 234.40, 234.84, 1.62, 1.92, 0.3, 0.355, {'+z': 'book2', 'all': 'sw_pages'})
    # The teacher's corner: a small table by the left wall, a chair, a lamp, chalk, the tied stack of cards.
    tx0, tx1, ty0, ty1, th = x0 + 0.02, x0 + 0.62, 2.3, 3.0, 0.71
    B.box('PigeonWood', tx0, tx1, ty0, ty1, th - 0.03, th)
    for lx in (tx0 + 0.03, tx1 - 0.03):
        for ly in (ty0 + 0.03, ty1 - 0.03):
            B.box('PigeonWood', lx - 0.02, lx + 0.02, ly - 0.02, ly + 0.02, 0.0, th - 0.03)
    B.box('PigeonWood', tx0 + 0.03, tx1 - 0.03, ty0 + 0.02, ty0 + 0.04, th - 0.12, th - 0.03)
    cx, cy = 233.2, 2.1                                                # the chair, pushed back from the table as she got up
    n0 = B.mark()
    B.box('PigeonWood', -0.21, 0.21, -0.2, 0.2, 0.43, 0.46)
    for dx in (-0.18, 0.18):
        for dy in (-0.17, 0.17):
            B.box('PigeonWood', dx - 0.018, dx + 0.018, dy - 0.018, dy + 0.018, 0.0, 0.43)
    for dy in (-0.17, 0.17):
        B.box('PigeonWood', 0.17, 0.2, dy - 0.018, dy + 0.018, 0.46, 0.92)
    B.box('PigeonWood', 0.17, 0.2, -0.17, 0.17, 0.72, 0.9)
    # her cardigan over the chair's back
    B.box('WinAtlas', 0.13, 0.25, -0.19, 0.19, 0.6, 0.94, cell='sw_wool')
    B.box('WinAtlas', 0.1, 0.13, -0.12, 0.08, 0.5, 0.82, cell='sw_wool')
    B.xform(n0, Matrix.Translation((cx, cy, 0.0)) @ Matrix.Rotation(math.radians(-38), 4, 'Z'))
    # the lamp (its bulb is AttCupboardLamp)
    lx, ly = tx0 + 0.12, ty1 - 0.12
    B.cyl('WinAtlas', (lx, ly, th), (lx, ly, th + 0.025), 0.065, seg=14, cell='sw_brass')
    B.cyl('WinAtlas', (lx, ly, th + 0.025), (lx, ly, th + 0.34), 0.008, seg=6, cell='sw_brass')
    B.cyl('WinAtlas', (lx, ly, th + 0.34), (LAMP_BULB[0], LAMP_BULB[1], th + 0.37), 0.008, seg=6, cell='sw_brass')
    B.cyl('WinAtlas', (LAMP_BULB[0], LAMP_BULB[1], th + 0.37), (LAMP_BULB[0], LAMP_BULB[1], th + 0.25), 0.03, 0.1, seg=16, cell='sw_green')
    # chalk in a tin, a register, an exercise book open, the stack of cards tied with string
    B.tbox('WinAtlas', tx1 - 0.2, tx1 - 0.07, ty0 + 0.08, ty0 + 0.16, th, th + 0.03, {'+z': 'chalkbox', 'all': 'sw_iron'})
    for k in range(3):
        B.cyl('WinAtlas', (tx1 - 0.19 + k * 0.03, ty0 + 0.12, th + 0.032), (tx1 - 0.13 + k * 0.03, ty0 + 0.13, th + 0.032), 0.006, seg=6, cell='sw_chalk')
    B.tbox('WinAtlas', tx1 - 0.24, tx1 - 0.04, ty0 + 0.24, ty0 + 0.4, th, th + 0.006, {'+z': 'openbook', 'all': 'sw_pages'})
    sx0, sy0_ = tx1 - 0.24, ty1 - 0.2
    B.tbox('WinAtlas', sx0, sx0 + 0.14, sy0_, sy0_ + 0.14, th, th + 0.075, {'+z': 'card', 'all': 'sw_cardboard'})
    for (a, b, c, d) in ((sx0 + 0.065, sx0 + 0.075, sy0_ - 0.002, sy0_ + 0.142), (sx0 - 0.002, sx0 + 0.142, sy0_ + 0.065, sy0_ + 0.075)):
        B.box('WinAtlas', a, b, c, d, th + 0.074, th + 0.078, cell='sw_string')
    B.torus('WinAtlas', (sx0 + 0.058, sy0_ + 0.07, th + 0.08), (0, 0, 1), 0.012, 0.003, seg=10, rseg=4, cell='sw_string')
    B.torus('WinAtlas', (sx0 + 0.084, sy0_ + 0.07, th + 0.08), (0, 0, 1), 0.012, 0.003, seg=10, rseg=4, cell='sw_string')
    # more of them, unsent, in a shoebox on the shelf's lowest level by the table
    B.box('WinAtlas', x0 + 0.1, x0 + 0.42, y1 - 0.32, y1 - 0.1, 0.06, 0.2, cell='sw_cardboard')
    for k in range(14):
        B.tbox('WinAtlas', x0 + 0.12 + k * 0.02, x0 + 0.13 + k * 0.02, y1 - 0.3, y1 - 0.14, 0.06, 0.22 + 0.01 * math.sin(k),
               {'-x': 'card2', 'all': 'sw_pages'})
    global PLAYER_INFO
    PLAYER_INFO = place_card_player(B)
    ob = B.obj('AttCupboard', coll)
    L = MB()
    L.sphere('AttCupboardLamp', (LAMP_BULB[0], LAMP_BULB[1], 0.71 + 0.27), 0.03, seg=10)
    lamp = L.obj('AttCupboardLamp', coll)
    return ob, lamp


LAMP_BULB = (232.62, 2.78)              # the cupboard lamp's bulb (x, y); its height is 0.98
CARD_PLAYER = (232.66, 2.52, 0.71)     # on the teacher's table, facing her chair (+x)
PLAYER_INFO = None


def place_card_player(B):
    """The voice-card player (art/common/voice_props.py), merged into the cupboard: on the teacher's table, its front
    to her chair (+x), its lid shut, a card (att_teacher) standing in its slot."""
    vp = _voice_props()
    if vp is None:
        print('dl14: voice props not ready; no card player placed')
        return None
    info = vp.card_player(B, vp.xform(loc=CARD_PLAYER, turn=90.0), lid='closed', horn=-30.0, card=True)
    print('dl14: card player', {k: v for k, v in info.items() if k in ('card', 'top', 'mouth', 'height', 'crank_pivot')})
    return info


def build_globes(coll):
    B = MB()
    for x in LAMPS:
        B.sphere('AttGlobeLamp', (x, 0.0, 3.27), 0.12, seg=14)
    return B.obj('AttGlobeLamps', coll)


# =====================================================================================================================
def tris(ob):
    if ob.type != 'MESH':
        return 0
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def build_set(dl01, m, coll):
    make_textures()
    B = MB()
    build_shell(B)
    build_stair(B)
    build_windows(B)
    build_hatch(B)
    build_end(B)
    build_props(B)
    objs = [B.obj('AttWinSet', coll)]
    objs.append(build_globes(coll))
    objs.append(build_chain(coll)[0])
    objs.append(build_blind(coll, 'AttBlindA', BLIND_A[0], BLIND_A[1], BLIND_A[2]))
    objs.append(build_blind(coll, 'AttBlindB', BLIND_B[0], BLIND_B[1], BLIND_B[2]))
    objs.append(build_ledge(coll, 'AttLedgeA', LEDGE_A[0], LEDGE_A[1], LEDGE_A[2]))
    objs.append(build_ledge(coll, 'AttLedgeB', LEDGE_B[0], LEDGE_B[1], LEDGE_B[2]))
    objs.append(build_peel(coll))
    objs.append(build_crank(coll))
    objs.append(build_wheel(coll))
    objs.append(build_clutch(coll))
    objs.append(build_pole(coll))
    objs.extend(build_refuge(coll))
    objs.extend(build_cupboard(coll))
    bpy.context.view_layer.update()
    total_t, total_p = 0, 0
    for ob in objs:
        if ob.type != 'MESH':
            continue
        t = tris(ob)
        prim = len([s for s in ob.material_slots])
        total_t += t
        total_p += prim
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        print('dl14: %-18s tris %6d mats %d %-60s x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (
            ob.name, t, prim, [s.material.name for s in ob.material_slots],
            min(v.x for v in bb), max(v.x for v in bb), min(v.y for v in bb), max(v.y for v in bb), min(v.z for v in bb), max(v.z for v in bb)))
    print('dl14: total tris %d, draw calls (material slots) %d' % (total_t, total_p))


REPORT = """DL-14 The Window, rev 0.3 additions (art/ch1/dl14.py). Game coords: (x, y, z) = Blender (x, z, -y).

MOVED (new):
- AttClutch: the slipping clutch's pressure plate, behind A's chain wheel (seen through its spokes): a disc r 0.12,
  face toward the camera with three cream bars and an amber wedge. Origin (235.0, 0.32, -0.722), on the same axis as
  AttWheelA. Spin axis: game z (Blender y; its local z in three.js after the glTF y-up conversion), i.e.
  AttClutch.rotateZ(angle), as AttWheelA. Turn it with the wheel while A is free (rotateZ(B.a * 6) like the wheel), and
  spin it on its own (about -dt * 6 per second, the chain's way) while the wheel is jammed and the chain runs.

STATIC (new):
- AttRefuge: the children's refuge behind the hatch, floor = the sill (2.15), x 238.98-240.47, z -1.3..-2.6, ceiling
  3.08. Three places along the back wall (z -2.22..-2.52): R.A. x 239.56, T.O. x 239.87, M x 240.18; biscuit tin
  (239.89, 2.15, -1.98); tin cup on the pipe (240.30, 2.65, -2.5); pipe x 240.385, z -2.5. Seen through the hatch
  from ledge B and from the landing (the game's camera is above the sill there).
- AttRefugeLamp: the lantern's glass, (239.42, 2.24, -1.74), material DenLanternGlow (already in EMIT: [1, .55, .22, 2.5]).
  Suggested light: P(0xffb070, 1.4, 2.2, 239.6, 2.5, -1.9)   the refuge, through the hatch.
- The drive plate (in AttWinSet): x 242.64-243.20, y 0.44-0.92, z -0.891 (on the wall right of the crank's gearbox;
  it replaces the small BLINDS A B plate). A / B roundels on the two blinds' pelmets (x 236.99 / 238.375, y 3.17) and an
  A on A's wheel's wall plate.

CHANGED:
- The hatch's opening is wider and a little taller: x 239.2-240.25 (was 239.25-240.15), head 3.05 (was 3.0). The sill
  (2.15), the landing (239.2-240.2) and ATT.hatch are unchanged. The duct now runs on from the refuge's right side,
  z -1.3..-1.95, 0.62 high (the game's duct z -1.3 is inside it). The hatch door hangs open against the refuge's left.

MATERIALS: new image WinDrive (textures/dl14_drive.png, passes through as a map); Copper (PLAIN, existing);
DenLanternGlow (EMIT, existing).
"""
