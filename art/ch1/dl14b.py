"""Chapter 1 Attendance, DL-14b Unaccompanied (game x 263.0 to 278.0). Design: docs/chapter1_expansion_proposal.md
(DL-14b); build sheet: docs/chapter1_expansion_build.md ("DL-14b Unaccompanied").

The night corridor between the dormitory and the sick bay. NO PUPIL UNACCOMPANIED. An old escort trolley still runs its
round on the figures' floor rail: a slow cream-enamelled cabinet on a bogie, a lamp on its front with a drooping visor,
a bell on top, a padded push-paddle low on its front, ESCORT 3 on its sides. Whatever pupil-sized thing it finds in its
lamp's beam it takes back to the dormitory. Along the back wall: a cloakroom niche (niche A) by the dormitory door, the
trolley's painted dock, the bay where a shabby teaching figure (a card round its neck: PUPIL) stands on a short spur,
and at the far end an open iron stair up to the landing at the sick bay's door (in DL-15's left wall). Chalk marks on
the lino where children were told to stand; a lost slipper by the niche.

Called by build_attendance.py as build_set(dl01, m, coll), in FINAL world coordinates (no shift).
Blender (x, y, z) is the game's (x, z, -y): +y is away from the camera, z is up. The lane is y = 0, the floor z = 0.

What the game moves (origin = pivot, world coordinates; REPORT at the bottom has the game's numbers):
    Att14bTrolley  the escort trolley; origin on the rail top under the middle of its base (266.0, 0.55, 0.03); built
                   facing +x (lamp and paddle on its +x end); the bell is part of it
    Att14bCone     the lamp's beam; origin at the lamp's mouth (266.35, 0.55, 1.0); pointing +x
    Att14bFig      the teaching figure (DL-15's rail figure); origin on the rail top under its bogie (269.9, 0.85, 0.03);
                   standing in the bay on the spur, facing +x
Static: Att14bSet (the corridor, niche A, the bay and its spur, the dock, the stair and landing, signs, dressing, the
present-day service cable and its relay box), Att14bLamps (EMIT AttGlobeLamp: two dim globes, one over the stair),
Att14bRelayLamp (EMIT, the relay box's green pilot lamp, lit).
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
ATLAS_PATH = os.path.join(TEX, 'dl14b_atlas.png')

# =====================================================================================================================
# Layout (Blender world; game x = x; the build sheet's numbers, which the game codes against)
# =====================================================================================================================
X0, X1 = 263.0, 278.0          # the dormitory's end wall (dl14a) ends at 263.0; DL-15's left wall (dl15) starts at 278.0
WALL_Y, WALL_Y2 = 1.0, 1.2     # the back wall's face and back (0.2 thick)
CEIL = 3.0
FLOOR_FRONT, CEIL_FRONT = -1.6, -1.0
DADO = 1.0
RAIL_Y, RAIL_G, RAIL_H = 0.55, 0.08, 0.03       # as DL-15: rails at y 0.47 / 0.63, rail top 0.03
CHAN = (0.39, 0.71)            # the timber channel the rails lie in
RAIL = (263.0, 275.3)          # the figures' rail (the trolley runs on it); a buffer stop at its right end
NICHE = (263.6, 264.5, 1.8)    # niche A (cloakroom recess): x0, x1, head
BAY = (269.4, 270.4, 1.9)      # the figure's bay: x0, x1, head
RECESS_Y = (0.25, 1.0)         # the recesses' gameplay depth (the hood over each reaches forward to 0.25)
RECESS_BACK = 1.5              # the recesses' back wall face, cut back through the wall for depth (visual only)
CHEEK_Y = 0.76                 # the recesses' side cheeks stand from the wall forward to here (behind the channel)
DOCK = (264.6, 265.4)          # the trolley's painted dock on the floor
DOCK_STOP = 265.0              # the trolley's left patrol end (its origin x there): a brass contact in the channel
FIG = (269.9, 0.85, RAIL_H)    # Att14bFig's origin: on the spur's rail top under its bogie
SPUR = (269.6, 270.2, 0.55, 0.85)     # the spur (a traverser plate in the bay's floor): x0, x1, from y, to y
TROLLEY = (266.0, RAIL_Y, RAIL_H)     # Att14bTrolley's origin
LAMP_DX, LAMP_Z = 0.35, 1.0           # the lamp's mouth, from the trolley's origin: +x, and its height above the floor
MOUTH = (TROLLEY[0] + LAMP_DX, RAIL_Y, LAMP_Z)   # Att14bCone's origin
CONE_LEN, CONE_R, CONE_END_Z = 2.6, 0.6, 0.55   # the beam: length along +x, base radius, base centre height
CONE_R0, CONE_SEG = 0.064, 16                   # its radius at the mouth (the lamp glass), sides
N_TREAD, RUN = 9, 0.255
STAIR = (275.3, 277.6)
RISE = 1.6 / N_TREAD           # 0.1778
TREADS = [(STAIR[0] + i * RUN, (STAIR[0] + (i + 1) * RUN) if i < N_TREAD - 1 else STAIR[1], (i + 1) * RISE)
          for i in range(N_TREAD)]        # (x0, x1, top): the 9th (277.34..277.6) is at 1.6, flush with the landing
STAIR_Y = (-0.45, 0.6)
LAND = (277.6, 278.0, 1.6)
SERVICE_Y, SERVICE_Z = WALL_Y - 0.013, 2.7   # the new service cable along the back wall, under the cornice
RELAY = (270.88, 271.12, 0.89, 2.58, 2.8)     # its relay box: x0, x1, front y, z0, z1
RELAY_LAMP = (271.0, 2.635, 0.014)            # Att14bRelayLamp on the box's front: x, z, radius
LAMPS = (267.35, 276.9)        # the two lit globes (one over the stair); a dead one at 272.3
DEAD_LAMP = 272.3
GLOBE_Z = 2.62
SIGN_BIG = (265.95, 268.75, 1.88, 2.43)       # NO PUPIL UNACCOMPANIED: x0, x1, z0, z1
SIGN_RAIL = (271.0, 272.3, 1.15, 1.45)        # ESCORTS KEEP TO THE RAIL
SIGN_SICK = (275.55, 276.45, 2.05, 2.39)      # SICK BAY, arrow up the stair
DOCK_PLATE = (264.7, 265.3, 1.13, 1.31)       # ESCORT 3 DOCK, over the dock
CHALK_FEET = (266.9, 268.55, 271.15, 272.75, 274.25)
SLIPPER = (263.93, 0.1, 28.0)                 # x, y, turn (degrees)

# =====================================================================================================================
# Materials (the game's names wherever one fits: index.html's WORN / PLAIN / EMIT tables; fallbacks for a lone build)
# =====================================================================================================================
GAME_WORN = {
    'WinPlaster': dict(base=[.29, .27, .21], dirt=[.15, .13, .095], chip=[.2, .185, .15], rough=.9, chipRough=.85, metal=0, grime=3, chipScale=18, chipAmt=.7, dust=[.24, .22, .18], dustAmt=.5, streak=.6),
    'WinDado': dict(base=[.12, .16, .135], dirt=[.065, .075, .06], chip=[.30, .27, .21], rough=.55, chipRough=.85, metal=0, grime=4, chipScale=22, chipAmt=.68, dust=[.16, .17, .15], dustAmt=.4, streak=.5),
    'WinLino': dict(base=[.115, .085, .05], dirt=[.06, .045, .03], chip=[.075, .07, .062], rough=.7, chipRough=.9, metal=0, grime=3, chipScale=14, chipAmt=.66, dust=[.13, .12, .1], dustAmt=.6, streak=.3),
    'PigeonWood': dict(base=[.12, .085, .055], dirt=[.06, .045, .03], chip=[.2, .15, .1], rough=.85, chipRough=.8, metal=0, grime=6, chipScale=30, chipAmt=.75, dust=[.1, .09, .08], dustAmt=.6),
    'CrateWood': dict(base=[.18, .12, .07], dirt=[.08, .055, .035], chip=[.25, .19, .12], rough=.85, chipRough=.8, metal=0, grime=6, chipScale=30, chipAmt=.75, streak=.6),
    'WornIron': dict(base=[.045, .043, .04], dirt=[.06, .035, .02], chip=[.3, .29, .27], rough=.7, chipRough=.35, metal=.6, grime=9, chipScale=40, chipAmt=.6, dust=[.09, .085, .075], dustAmt=.4),
    'CastIron': dict(base=[.035, .034, .032], dirt=[.05, .03, .018], chip=[.13, .12, .1], rough=.75, chipRough=.45, metal=.5, grime=9, chipScale=50, chipAmt=.72, dust=[.08, .075, .065], dustAmt=.5),
    'HandledBrass': dict(base=[.2, .14, .06], dirt=[.08, .06, .03], chip=[.62, .46, .2], rough=.5, chipRough=.2, metal=.85, grime=8, chipScale=26, chipAmt=.5, dust=[.12, .1, .07], dustAmt=.2),
    'PupilWood': dict(base=[.36, .27, .17], dirt=[.17, .12, .08], chip=[.46, .38, .27], rough=.7, chipRough=.6, metal=0, grime=12, chipScale=40, chipAmt=.74, dust=[.3, .28, .24], dustAmt=.5),
    'CreamPaint': dict(base=[.66, .58, .40], dirt=[.36, .30, .19], chip=[.028, .025, .02], rough=.78, chipRough=.5, metal=0, grime=3, chipScale=20, chipAmt=.63, dust=[.62, .57, .45], dustAmt=.3, streak=.55),
    'SorterCushion': dict(base=[.16, .045, .035], dirt=[.07, .03, .022], chip=[.24, .17, .12], rough=.62, chipRough=.85, metal=0, grime=8, chipScale=30, chipAmt=.72, dust=[.12, .1, .09], dustAmt=.4),
}
GAME_PLAIN = {'Brass': ((.45, .32, .12), .45, .8), 'Rubber': ((.012, .012, .011), .7, 0.0),
              'NewCable': ((0.016, 0.016, 0.018), 0.28, 0.0),      # the present-day service cable (pass 6's 'new cable')
              'NewSteel': ((0.26, 0.27, 0.28), 0.4, 0.8)}          # galvanised: its clips, the relay box
GAME_EMIT = {'AttGlobeLamp': ((1.0, 0.86, 0.62), 3.0)}
NEW_EMIT = {'Att14bTrolleyLamp': ((1.0, 0.8, 0.5), 4.0),     # the trolley's lamp glass (part of Att14bTrolley)
            'Att14bBeam': ((1.0, 0.85, 0.6), 1.0),           # Att14bCone (the game gives it its own additive material)
            'Att14bRelayLamp': ((0.45, 1.0, 0.5), 5.0)}      # the new relay box's pilot lamp, lit
ATLAS_MAT = 'Att14bAtlas'


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
    if not os.path.exists(os.path.join(COMMON, 'VOICE_PROPS_READY')):
        return None
    if COMMON not in sys.path:
        sys.path.insert(0, COMMON)
    import voice_props
    return voice_props


# =====================================================================================================================
# The atlas (PIL, at build time, into art/ch1/textures/dl14b_atlas.png): the signs, plates, cards and swatches
# =====================================================================================================================
ATLAS = 1024
CELLS = {
    'unacc': (0, 0, 1024, 200),          # NO PUPIL UNACCOMPANIED, 2.8 x 0.55 m
    'rail': (0, 200, 512, 320),          # ESCORTS KEEP TO THE RAIL, 1.3 x 0.3 m
    'sickbay': (512, 200, 832, 320),     # SICK BAY with the arrow, 0.9 x 0.34 m
    'escort3': (832, 200, 1024, 264),    # the trolley's number plate, 0.3 x 0.1 m
    'dockplate': (832, 264, 1024, 320),  # ESCORT 3 DOCK, 0.6 x 0.18 m
    'dockfloor': (0, 320, 512, 480),     # the dock's floor paint in front of the channel, 0.8 x 0.25 m
    'dockback': (512, 320, 768, 400),    # its hatching behind the channel, 0.8 x 0.25 m
    'pupil': (768, 320, 896, 400),       # the figure's card, 0.14 x 0.09 m
    'chart': (896, 320, 1024, 704),      # the height chart in the bay, 0.3 x 0.9 m
    'model': (0, 480, 512, 528),         # the bay's fascia, 1.0 x 0.09 m
    'cloaks': (512, 480, 768, 528),      # niche A's fascia plate, 0.45 x 0.08 m
}
SWATCH = {'sw_dark': (8, 8, 8), 'sw_iron': (40, 39, 37), 'sw_brass': (160, 124, 62), 'sw_chalk': (218, 214, 202),
          'sw_glass': (70, 74, 72), 'sw_felt': (104, 34, 40), 'sw_fleece': (196, 184, 160), 'sw_rubber': (22, 20, 20),
          'sw_coat': (34, 44, 70), 'sw_scarf': (150, 52, 40), 'sw_tape': (196, 170, 136), 'sw_string': (150, 136, 106),
          'sw_card': (190, 172, 132), 'sw_paint': (176, 146, 64), 'sw_wood': (104, 74, 46), 'sw_enamel': (200, 192, 168)}
for _i, _k in enumerate(SWATCH):
    CELLS[_k] = (32 * (_i % 16), 560 + 32 * (_i // 16), 32 * (_i % 16) + 32, 592 + 32 * (_i // 16))


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
             'mono': '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
             'carlito': '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf',
             'carlito-r': '/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf',
             'hand': '/usr/share/fonts/truetype/crosextra/Caladea-Italic.ttf',
             'handb': '/usr/share/fonts/truetype/crosextra/Caladea-BoldItalic.ttf'}
    try:
        return ImageFont.truetype(paths[kind], size)
    except OSError:
        return ImageFont.load_default()


def _fit(d, text, size, kind, maxw):
    """The font at `size`, smaller if the text would be wider than maxw px."""
    while size > 8:
        f = _font(size, kind)
        if d.textlength(text, font=f) <= maxw:
            return f
        size -= 2
    return _font(size, kind)


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


def _chips(img, seed, n, rmax, colour=(30, 28, 26)):
    """Enamel chipped to the iron: a few dark flakes, mostly near the edges."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    w, h = img.size
    for _ in range(n):
        if rnd.random() < 0.7:
            x = rnd.choice((rnd.uniform(0, 0.06), rnd.uniform(0.94, 1))) * w
            y = rnd.uniform(0, 1) * h
        else:
            x, y = rnd.uniform(0, 1) * w, rnd.choice((rnd.uniform(0, 0.1), rnd.uniform(0.9, 1))) * h
        r = rnd.uniform(1.5, rmax)
        pts = [(x + r * math.cos(a) * rnd.uniform(0.5, 1.2), y + r * math.sin(a) * rnd.uniform(0.5, 1.2))
               for a in [k * math.pi / 3 for k in range(6)]]
        d.polygon(pts, fill=colour)


def make_atlas(path):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    os.makedirs(TEX, exist_ok=True)
    img = Image.new('RGB', (ATLAS, ATLAS), (60, 58, 54))
    cream, green, ink, red = (210, 200, 170), (36, 62, 48), (30, 28, 24), (124, 40, 32)

    def plate(name, bg, fg, lines, seed, border=True, chips=8, radius=12):
        x0, y0, x1, y1 = CELLS[name]
        w, h = x1 - x0, y1 - y0
        p = Image.new('RGB', (w, h), bg)
        d = ImageDraw.Draw(p)
        if border:
            d.rounded_rectangle((4, 4, w - 5, h - 5), radius=radius, outline=fg, width=max(3, h // 22))
        for text, size, xf, yf, kind, col in lines:
            d.text((int(w * xf), int(h * yf)), text, font=_fit(d, text, size, kind, w * 0.9), fill=col or fg, anchor='mm')
        _chips(p, seed, chips, max(3, h // 16))
        img.paste(_fade(p, 1400 + seed, k=0.12, dust=0.16), (x0, y0))
        return p

    # The big enamel: NO PUPIL UNACCOMPANIED (cream, green letters, a red rule; screw holes; chipped).
    x0, y0, x1, y1 = CELLS['unacc']
    w, h = x1 - x0, y1 - y0
    p = Image.new('RGB', (w, h), cream)
    d = ImageDraw.Draw(p)
    d.rounded_rectangle((5, 5, w - 6, h - 6), radius=16, outline=green, width=8)
    d.rounded_rectangle((16, 16, w - 17, h - 17), radius=10, outline=green, width=2)
    d.text((w // 2, int(h * 0.44)), 'NO PUPIL UNACCOMPANIED', font=_fit(d, 'NO PUPIL UNACCOMPANIED', 104, 'carlito', w - 90), fill=green, anchor='mm')
    d.line((150, int(h * 0.74), w - 150, int(h * 0.74)), fill=red, width=5)
    d.text((w // 2, int(h * 0.85)), 'BY ORDER', font=_font(24, 'carlito'), fill=green, anchor='mm')
    for sx in (30, w - 31):
        for sy in (30, h - 31):
            d.ellipse((sx - 6, sy - 6, sx + 6, sy + 6), fill=(80, 76, 70))
    _chips(p, 1401, 26, 9)
    img.paste(_fade(p, 1402, k=0.1, dust=0.18), (x0, y0))
    # ESCORTS KEEP TO THE RAIL, and the rule under it.
    plate('rail', green, cream, (('ESCORTS KEEP TO THE RAIL', 52, 0.5, 0.36, 'carlito', None),
                                ('Pupils found in the corridor are returned to the dormitory.', 22, 0.5, 0.74, 'carlito-r', None)),
          3, chips=10)
    # SICK BAY, with an arrow up the stair (up and to the right).
    x0, y0, x1, y1 = CELLS['sickbay']
    w, h = x1 - x0, y1 - y0
    p = Image.new('RGB', (w, h), red)
    d = ImageDraw.Draw(p)
    d.rounded_rectangle((4, 4, w - 5, h - 5), radius=10, outline=(226, 214, 190), width=5)
    d.text((int(w * 0.38), h // 2), 'SICK BAY', font=_fit(d, 'SICK BAY', 64, 'carlito', w * 0.6), fill=(226, 214, 190), anchor='mm')
    ax, ay, L = int(w * 0.79), int(h * 0.62), 54
    tip = (ax + L * 0.7, ay - L * 0.7)
    d.line((ax - L * 0.55, ay + L * 0.25, tip[0] - 6, tip[1] + 6), fill=(226, 214, 190), width=13)
    d.polygon([tip, (tip[0] - 38, tip[1] + 4), (tip[0] - 4, tip[1] + 38)], fill=(226, 214, 190))
    _chips(p, 1404, 8, 6)
    img.paste(_fade(p, 1405, k=0.12, dust=0.14), (x0, y0))
    # The trolley's number plate and the dock's plate.
    plate('escort3', cream, (30, 40, 70), (('ESCORT  3', 40, 0.5, 0.54, 'carlito', None),), 6, chips=4, radius=8)
    plate('dockplate', green, cream, (('ESCORT 3', 26, 0.5, 0.36, 'carlito', None), ('DOCK', 18, 0.5, 0.74, 'carlito', None)),
          7, chips=4, radius=8)
    # The dock's floor paint: worn yellow, a stencilled ESCORT 3, scuffed where the trolley turns.
    for name, seed in (('dockfloor', 1410), ('dockback', 1411)):
        x0, y0, x1, y1 = CELLS[name]
        w, h = x1 - x0, y1 - y0
        n = _noise(w, h, 5, seed)
        a = np.ones((h, w, 3)) * np.array([170, 140, 62], float) * (0.75 + 0.35 * n)[..., None]
        t = Image.fromarray(np.clip(a, 0, 255).astype('uint8'))
        d = ImageDraw.Draw(t)
        if name == 'dockfloor':
            d.rectangle((0, 0, w - 1, h - 1), outline=(40, 34, 22), width=6)
            d.text((w // 2, h // 2 + 4), 'ESCORT  3', font=_fit(d, 'ESCORT  3', 92, 'mono', w - 50), fill=(36, 32, 24), anchor='mm')
            for xx in range(36, w, 64):                       # stencil bridges
                d.line((xx, 20, xx, h - 20), fill=(170, 140, 62), width=3)
        else:
            d.rectangle((0, 0, w - 1, h - 1), outline=(40, 34, 22), width=5)
            for k in range(-h, w, 34):
                d.line((k, h, k + h, 0), fill=(40, 34, 22), width=12)
        a = np.asarray(t).astype(float)
        wear = _noise(w, h, 9, seed + 5)
        lino = np.array([60, 44, 26], float)
        m = np.clip((wear - 0.52) * 4.0, 0, 1)[..., None]
        a = a * (1 - m) + lino * m
        img.paste(Image.fromarray(np.clip(a, 0, 255).astype('uint8')), (x0, y0))
    # The figure's card: buff board, PUPIL in a teacher's capitals, a punched hole either side.
    x0, y0, x1, y1 = CELLS['pupil']
    w, h = x1 - x0, y1 - y0
    p = Image.new('RGB', (w, h), (196, 178, 136))
    d = ImageDraw.Draw(p)
    d.rectangle((2, 2, w - 3, h - 3), outline=(120, 100, 70), width=2)
    d.text((w // 2, int(h * 0.58)), 'PUPIL', font=_font(38, 'carlito'), fill=(26, 24, 30), anchor='mm')
    for xx in (14, w - 15):
        d.ellipse((xx - 5, 9, xx + 5, 19), fill=(40, 36, 30))
    img.paste(_fade(p, 1420, k=0.1, dust=0.22), (x0, y0))
    # The height chart in the bay: an enamel strip with feet and inches, and pencil marks at a child's height.
    x0, y0, x1, y1 = CELLS['chart']
    w, h = x1 - x0, y1 - y0                  # 128 x 384 px for 0.3 x 0.9 m (z 0.3 .. 1.2)
    p = Image.new('RGB', (w, h), (204, 196, 172))
    d = ImageDraw.Draw(p)
    d.rectangle((2, 2, w - 3, h - 3), outline=green, width=4)
    pz = lambda z: (1.2 - z) / 0.9 * h
    for k in range(0, 91):
        z = 0.3 + k * 0.01
        long_ = k % 10 == 0
        d.line((8, pz(z), 8 + (30 if long_ else 12 if k % 5 == 0 else 6), pz(z)), fill=green, width=2 if long_ else 1)
        if long_:
            d.text((44, pz(z)), '%d' % int(round(z * 100)), font=_font(15, 'carlito'), fill=green, anchor='lm')
    rnd = random.Random(1421)
    for z, nm in ((0.98, 'R.A.'), (1.02, 'T.O.'), (0.93, 'M')):
        yy = pz(z) + rnd.uniform(-2, 2)
        d.line((70, yy, 118, yy - 1), fill=(60, 60, 76), width=2)
        d.text((96, yy - 9), nm, font=_font(14, 'hand'), fill=(60, 60, 76), anchor='mm')
    img.paste(_fade(p, 1422, k=0.12, dust=0.2), (x0, y0))
    # Fascias: MODEL PUPIL (painted on the bay's hood); CLOAKS (a small enamel on niche A's).
    x0, y0, x1, y1 = CELLS['model']
    w, h = x1 - x0, y1 - y0
    p = Image.new('RGB', (w, h), (48, 34, 22))
    d = ImageDraw.Draw(p)
    d.text((w // 2, h // 2 + 1), 'MODEL PUPIL  ·  FOR ESCORT PRACTICE', font=_fit(d, 'MODEL PUPIL  ·  FOR ESCORT PRACTICE', 30, 'carlito', w - 20), fill=(200, 184, 140),
           anchor='mm')
    img.paste(_fade(p, 1423, k=0.08, dust=0.2), (x0, y0))
    plate('cloaks', cream, green, (('CLOAKS', 34, 0.5, 0.55, 'carlito', None),), 8, chips=3, radius=6)
    for name, rgb in SWATCH.items():
        x0, y0, x1, y1 = CELLS[name]
        ImageDraw.Draw(img).rectangle((x0, y0, x1 - 1, y1 - 1), fill=rgb)
    img.filter(ImageFilter.GaussianBlur(0.35)).save(path, optimize=True)


# =====================================================================================================================
# Mesh building (as art/ch1/dl15.py's MB)
# =====================================================================================================================
class MB:
    """One object being built: faces tagged by material name. Faces flagged 'flat' keep the winding they were built
    with (decals, one-sided in the game); the rest have their normals recalculated outward."""

    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.flat = self.bm.faces.layers.int.new('flat')
        self.names = []

    def __call__(self, name):
        return self.m(name)

    def m(self, name):
        if name not in self.names:
            self.names.append(name)
        return self.names.index(name)

    def mark(self):
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

    def rbox(self, mt, size, c, p=6.0, cuts=4, rot=None):
        """A soft-cornered box (build_d17.rounded_box)."""
        n0 = self.mark()
        d17.rounded_box(size, c, p=p, cuts=cuts, bm=self.bm, mat=self.m(mt), rot=rot)
        return self.since(n0)

    def face(self, mt, corners, uvs=None, flat=True):
        f = self.bm.faces.new([self.bm.verts.new(c) for c in corners])
        f.material_index = self.m(mt)
        f[self.flat] = 1 if flat else 0
        if uvs:
            for lp, t in zip(f.loops, uvs):
                lp[self.uv].uv = t
        return f

    def decal(self, x0, x1, z0, z1, y, cell, facing=-1, mt=ATLAS_MAT):
        """A picture on a vertical plane at y, facing -y (the camera) or +y, reading the right way round."""
        u0, v0, u1, v1 = cell_uv(cell)
        if facing < 0:
            return self.face(mt, [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])
        return self.face(mt, [(x1, y, z0), (x0, y, z0), (x0, y, z1), (x1, y, z1)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

    def floor_decal(self, x0, x1, y0, y1, z, cell, mt=ATLAS_MAT):
        """A picture on the floor, facing up, its bottom edge toward the camera."""
        u0, v0, u1, v1 = cell_uv(cell)
        return self.face(mt, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])

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

    def chalk(self, pts, w=0.016, z=0.0015, closed=False):
        """A chalk line on the floor along (x, y) points: flat strips facing up."""
        u, v = cell_mid('sw_chalk')
        seq = list(pts) + ([pts[0]] if closed else [])
        for p, q in zip(seq, seq[1:]):
            d = Vector((q[0] - p[0], q[1] - p[1]))
            if d.length < 1e-6:
                continue
            d.normalize()
            n = Vector((-d.y, d.x)) * (w / 2)
            self.face(ATLAS_MAT, [(p[0] - n.x, p[1] - n.y, z), (q[0] - n.x, q[1] - n.y, z), (q[0] + n.x, q[1] + n.y, z),
                                  (p[0] + n.x, p[1] + n.y, z)], [(u, v)] * 4)

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


def wall(B, x0, x1, y0, y1, z0, z1, dado=DADO):
    """A plastered wall slab: dado paint below `dado`, plaster above."""
    if z0 < dado < z1:
        B.box('WinDado', x0, x1, y0, y1, z0, dado)
        B.box('WinPlaster', x0, x1, y0, y1, dado, z1)
    else:
        B.box('WinDado' if z1 <= dado else 'WinPlaster', x0, x1, y0, y1, z0, z1)


def holed_wall(B, x0, x1, y0, y1, z0, z1, holes, split=DADO):
    """A wall slab with rectangular holes (hx0, hx1, hz0, hz1), as boxes over the grid the holes make (dl14's)."""
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
                B.box('WinDado' if cz < split else 'WinPlaster', run[0], run[1], y0, y1, za, zb)
                run = None


def wall_runs(holes, z0, z1, xa=X0, xb=X1):
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


# =====================================================================================================================
# The corridor
# =====================================================================================================================
def build_shell(B):
    holes = [(NICHE[0], NICHE[1], 0.0, NICHE[2]), (BAY[0], BAY[1], 0.0, BAY[2])]
    holed_wall(B, X0, X1, WALL_Y, WALL_Y2, 0.0, CEIL, holes)
    # Floor (lino) and ceiling; the cornice along the back wall.
    B.box('WinLino', X0, X1, FLOOR_FRONT, WALL_Y2, -0.2, 0.0)
    B.box('WinPlaster', X0, X1, CEIL_FRONT, WALL_Y2, CEIL, CEIL + 0.15)
    B.box('WinPlaster', X0, X1, WALL_Y - 0.08, WALL_Y, CEIL - 0.08, CEIL)
    B.box('WinPlaster', X0, X1, WALL_Y - 0.03, WALL_Y, CEIL - 0.12, CEIL - 0.08)
    # Skirting and dado rail between the openings.
    for a, b in wall_runs(holes, 0.0, 0.12):
        B.box('PigeonWood', a, b, WALL_Y - 0.02, WALL_Y, 0.0, 0.12)
    for a, b in wall_runs(holes, 0.98, 1.03):
        B.box('PigeonWood', a, b, WALL_Y - 0.03, WALL_Y, 0.98, 1.03)
    return holes


def build_recess(B, x0, x1, head):
    """A recess in the back wall: the opening cut back to RECESS_BACK, with its own floor, reveals and ceiling; slim
    timber cheeks either side standing forward from the wall to CHEEK_Y; and a hood over it at `head`, reaching
    forward to RECESS_Y[0] on two iron brackets (the recess reads from the lane as y 0.25 to 1.0, head high)."""
    rb = RECESS_BACK
    B.box('WinLino', x0, x1, WALL_Y2, rb, -0.2, 0.0)
    wall(B, x0 - 0.15, x0, WALL_Y2, rb + 0.15, 0.0, head + 0.15)
    wall(B, x1, x1 + 0.15, WALL_Y2, rb + 0.15, 0.0, head + 0.15)
    wall(B, x0, x1, rb, rb + 0.15, 0.0, head)
    B.box('WinPlaster', x0 - 0.15, x1 + 0.15, WALL_Y2, rb + 0.15, head, head + 0.15)
    B.box('PigeonWood', x0, x1, rb - 0.02, rb, 0.0, 0.12)                       # skirting round the inside
    B.box('PigeonWood', x0, x0 + 0.02, WALL_Y, rb, 0.0, 0.12)
    B.box('PigeonWood', x1 - 0.02, x1, WALL_Y, rb, 0.0, 0.12)
    B.box('PigeonWood', x0, x1, rb - 0.03, rb, 0.98, 1.03)
    # The cheeks (timber, panelled) and the hood.
    for a, b in ((x0 - 0.05, x0), (x1, x1 + 0.05)):
        B.box('PigeonWood', a, b, CHEEK_Y, WALL_Y, 0.0, head)
        B.box('CrateWood', a - 0.005, b + 0.005, CHEEK_Y - 0.01, CHEEK_Y + 0.02, 0.0, head)      # the nosing strip
    hy0 = RECESS_Y[0]
    B.box('PigeonWood', x0 - 0.06, x1 + 0.06, hy0, WALL_Y, head, head + 0.1)
    B.box('CrateWood', x0 - 0.07, x1 + 0.07, hy0 - 0.01, WALL_Y, head + 0.1, head + 0.125)        # its top board
    for x in (x0 - 0.025, x1 + 0.025):                                                   # brackets under the hood
        B.cyl('WornIron', (x, CHEEK_Y, head - 0.42), (x, hy0 + 0.06, head - 0.005), 0.012, seg=6)
        B.box('WornIron', x - 0.012, x + 0.012, hy0 + 0.04, CHEEK_Y, head - 0.02, head)
        B.cyl('WornIron', (x, CHEEK_Y + 0.004, head - 0.42), (x, CHEEK_Y + 0.012, head - 0.42), 0.02, seg=8)


def build_niche(B):
    """Niche A, the cloakroom recess: child-height pegs on its back wall, a small coat left on one, a scarf on another,
    a low bench at the back; CLOAKS on the hood."""
    x0, x1, head = NICHE
    build_recess(B, x0, x1, head)
    rb = RECESS_BACK
    B.box('PigeonWood', x0 + 0.02, x1 - 0.02, rb - 0.03, rb, 1.04, 1.12)          # the peg rail
    pegs = (263.78, 264.05, 264.32)
    for x in pegs:
        B.cyl('WornIron', (x, rb - 0.03, 1.08), (x, rb - 0.1, 1.1), 0.008, seg=5)
        B.sphere('WornIron', (x, rb - 0.1, 1.1), 0.012, seg=6)
    # a small navy duffle coat on the right peg: hung by its hood, flaring to the hem, its sleeves hanging alongside
    x = pegs[2]
    n0 = B.mark()
    d17.rounded_box((0.27, 0.05, 0.44), (x, rb - 0.075, 0.79), p=4.0, cuts=3, bm=B.bm, mat=B.m(ATLAS_MAT),
                    taper=lambda zc: 0.62 + 0.38 * (1 - zc) / 2)
    B.sphere(ATLAS_MAT, (x, rb - 0.085, 1.03), 0.055, seg=8, scale=(0.9, 0.7, 1.0))
    for sx in (-1, 1):
        B.cbox(ATLAS_MAT, (x + sx * 0.105, rb - 0.1, 0.78), (0.06, 0.045, 0.3), rot=Matrix.Rotation(math.radians(sx * 6), 4, 'Y'))
    B.paint(B.since(n0), 'sw_coat')
    for k in range(3):                                                                   # toggles
        B.cbox(ATLAS_MAT, (x, rb - 0.105, 0.9 - k * 0.1), (0.04, 0.012, 0.012), cell='sw_wood')
    # a red scarf over the left peg, hanging in two tails
    for dx, ln in ((-0.03, 0.42), (0.035, 0.34)):
        B.sbox('sw_scarf', pegs[0] + dx - 0.03, pegs[0] + dx + 0.03, rb - 0.115, rb - 0.095, 1.1 - ln, 1.11)
    # the bench at the back
    B.box('CrateWood', x0 + 0.04, x1 - 0.04, rb - 0.24, rb - 0.02, 0.27, 0.3)
    for x in (x0 + 0.1, x1 - 0.1):
        B.box('PigeonWood', x - 0.02, x + 0.02, rb - 0.22, rb - 0.04, 0.0, 0.27)
    # CLOAKS on the hood's fascia
    xc = (x0 + x1) / 2
    B.decal(xc - 0.225, xc + 0.225, head + 0.012, head + 0.088, RECESS_Y[0] - 0.002, 'cloaks')


def build_bay(B):
    """The figure's bay: the recess, a height chart on its back wall, MODEL PUPIL on the hood; in its floor the spur: an
    iron traverser plate from the main rail back to y 0.98 with a short stub of rail at y 0.85 (the figure stands on it)
    and two guide slots across it (the figure is slid out along them to the main rail at y 0.55)."""
    x0, x1, head = BAY
    build_recess(B, x0, x1, head)
    rb = RECESS_BACK
    B.decal(269.75, 270.05, 0.3, 1.2, rb - 0.003, 'chart')
    B.decal(x0 + 0.05, x1 - 0.05, head + 0.006, head + 0.094, RECESS_Y[0] - 0.002, 'model')
    sx0, sx1, sy0, sy1 = SPUR
    B.box('CastIron', sx0, sx1, CHAN[0], 0.98, -0.004, 0.004)                     # the traverser plate
    for x in (sx0 + 0.06, sx1 - 0.06):                                            # its guide slots, across
        B.sbox('sw_dark', x - 0.008, x + 0.008, CHAN[0] + 0.01, 0.97, 0.0035, 0.0045)
    for x in (sx0 + 0.02, sx1 - 0.02):                                            # bolts
        for y in (CHAN[0] + 0.02, 0.96):
            B.cyl('WornIron', (x, y, 0.004), (x, y, 0.009), 0.01, seg=6)
    rails(B, sx0 + 0.02, sx1 - 0.02, 0.0, y=sy1)                                # the stub the figure stands on
    for x, s in ((sx0 + 0.02, 1), (sx1 - 0.02, -1)):                              # its chocks
        B.box('WornIron', min(x, x + s * 0.035), max(x, x + s * 0.035), sy1 - 0.12, sy1 + 0.12, 0.004, 0.06)


def rails(B, x0, x1, z, y=RAIL_Y):
    """DL-15's rail profile: two low iron rails (foot, web, head) either side of y, rail top z + 0.03."""
    for s in (-1, 1):
        yc = y + s * RAIL_G
        B.box('WornIron', x0, x1, yc - 0.012, yc + 0.012, z, z + 0.008)
        B.box('WornIron', x0, x1, yc - 0.005, yc + 0.005, z + 0.008, z + 0.024)
        B.box('WornIron', x0, x1, yc - 0.009, yc + 0.009, z + 0.024, z + RAIL_H)


def build_rail(B):
    """The figures' rail along the corridor (DL-15's: a timber channel on the floor, the rails on it), the buffer stop
    at its right end under the stair's first tread, and the trolley's dock: a painted bay, a brass contact."""
    x0, x1 = RAIL
    B.box('PigeonWood', x0, SPUR[0], CHAN[0], CHAN[1], -0.002, 0.003)
    B.box('PigeonWood', SPUR[1], x1, CHAN[0], CHAN[1], -0.002, 0.003)
    rails(B, x0, x1, 0.0)
    B.box('WornIron', x1 - 0.08, x1, RAIL_Y - 0.11, RAIL_Y + 0.11, 0.0, 0.12)        # the buffer stop
    B.box('CrateWood', x1 - 0.1, x1 - 0.08, RAIL_Y - 0.09, RAIL_Y + 0.09, 0.03, 0.1)
    # The dock: yellow floor paint either side of the channel, ESCORT 3 stencilled in front; the brass contact.
    d0, d1 = DOCK
    B.floor_decal(d0, d1, 0.07, CHAN[0] - 0.005, 0.0012, 'dockfloor')
    B.floor_decal(d0, d1, CHAN[1] + 0.005, 0.98, 0.0012, 'dockback')
    B.box('HandledBrass', DOCK_STOP - 0.06, DOCK_STOP + 0.06, 0.505, 0.595, 0.003, 0.007)
    for x in (DOCK_STOP - 0.045, DOCK_STOP + 0.045):
        B.cyl('WornIron', (x, 0.55, 0.007), (x, 0.55, 0.01), 0.006, seg=6)
    # ESCORT 3 DOCK on the wall over it, and the charging socket under it (its cable long since cut).
    px0, px1, pz0, pz1 = DOCK_PLATE
    B.box('WornIron', px0 - 0.01, px1 + 0.01, WALL_Y - 0.01, WALL_Y, pz0 - 0.01, pz1 + 0.01)
    B.decal(px0, px1, pz0, pz1, WALL_Y - 0.0105, 'dockplate')
    B.box('CastIron', 264.9, 265.1, WALL_Y - 0.05, WALL_Y, 0.3, 0.46)
    B.box('HandledBrass', 264.93, 265.07, WALL_Y - 0.055, WALL_Y - 0.05, 0.33, 0.43)
    B.cyl('Rubber', (265.0, WALL_Y - 0.055, 0.38), (265.0, WALL_Y - 0.09, 0.38), 0.012, seg=8)


def build_stair(B):
    """The stair up to the sick bay: nine open iron treads (chequer plate, a worn nosing) on two sawtooth stringers,
    a balustrade on its back edge (the wall side), and the landing at 1.6 on iron posts against DL-15's wall.
    Collision: each tread is solid from x0 to x1 at its top (TREADS); the landing 277.6 to 278.0 at 1.6."""
    y0, y1 = STAIR_Y
    for x0, x1, top in TREADS:
        B.box('CastIron', x0, x1, y0, y1, top - 0.02, top)
        B.box('WornIron', x0, x0 + 0.03, y0, y1, top - 0.045, top + 0.002)            # the nosing, worn bright
    # The stringers: the step profile on top (0.02 under the plates), a straight edge under.
    s = RISE / RUN
    prof = [(STAIR[0], 0.0)]
    for x0, x1, top in TREADS:
        prof += [(x0, top - 0.02), (x1, top - 0.02)]
    zb = lambda x: (x - STAIR[0]) * s - 0.16
    prof += [(STAIR[1], zb(STAIR[1])), (STAIR[0] + 0.16 / s, 0.0)]
    for a, b in ((y0 + 0.01, y0 + 0.03), (y1 - 0.03, y1 - 0.01)):
        B.prism_xz('WornIron', prof, a, b)
    # The landing: a chequer plate on an iron frame, two posts and a brace.
    lx0, lx1, lt = LAND
    B.box('CastIron', lx0, lx1, y0, y1, lt - 0.025, lt)
    B.box('WornIron', lx0, lx0 + 0.03, y0, y1, lt - 0.05, lt + 0.002)
    for a, b in ((y0, y0 + 0.04), (y1 - 0.04, y1)):
        B.box('WornIron', lx0, lx1, a, b, lt - 0.14, lt - 0.025)
        B.box('WornIron', lx0 + 0.02, lx0 + 0.07, a, b, 0.0, lt - 0.14)                  # the posts
        B.box('WornIron', lx0 - 0.01, lx0 + 0.08, a - 0.01, b + 0.01, 0.0, 0.02)          # their feet
    B.box('WornIron', lx1 - 0.03, lx1, y0, y1, lt - 0.14, lt - 0.025)                   # bearer against DL-15's wall
    L = math.hypot(lx1 - lx0 - 0.1, lt - 0.2)
    a = math.atan2(lt - 0.2, lx1 - lx0 - 0.1)
    B.cbox('WornIron', ((lx0 + 0.07 + lx1 - 0.03) / 2, y0 + 0.02, (0.06 + lt - 0.14) / 2), (L, 0.012, 0.035),
           rot=Matrix.Rotation(-a, 4, 'Y'))
    # The balustrade on the back edge: a newel at the foot, a baluster per tread, the handrail; along the landing.
    yb = y1 - 0.02
    hr = 0.86
    B.box('PigeonWood', STAIR[0] + 0.01, STAIR[0] + 0.07, yb - 0.03, yb + 0.03, 0.0, RISE + hr + 0.08)
    for x0, x1, top in TREADS:
        x = x0 + 0.13
        B.cyl('WornIron', (x, yb, top), (x, yb, min(top + hr + (x - x0) * s, lt + hr)), 0.008, seg=6)
    xa, za = STAIR[0] + 0.04, RISE + hr + 0.04 * s
    xb, zb2 = TREADS[-1][0], lt + hr
    B.cyl('PigeonWood', (xa, yb, za), (xb, yb, zb2), 0.022, seg=8)
    B.cyl('PigeonWood', (xb, yb, zb2), (lx1, yb, zb2), 0.022, seg=8)
    for x in (lx0 + 0.15, lx1 - 0.05):
        B.cyl('WornIron', (x, yb, lt), (x, yb, lt + hr), 0.008, seg=6)
    B.sphere('PigeonWood', (xb, yb, zb2), 0.03, seg=8)


def build_signs(B):
    """The enamels on the back wall: NO PUPIL UNACCOMPANIED (big), ESCORTS KEEP TO THE RAIL, SICK BAY (arrow up)."""
    for (x0, x1, z0, z1), cell in ((SIGN_BIG, 'unacc'), (SIGN_RAIL, 'rail'), (SIGN_SICK, 'sickbay')):
        B.box('WornIron', x0 - 0.008, x1 + 0.008, WALL_Y - 0.012, WALL_Y, z0 - 0.008, z1 + 0.008)
        B.decal(x0, x1, z0, z1, WALL_Y - 0.0125, cell)


def build_dressing(B):
    """The lost slipper by niche A; the chalk marks where children were told to stand (pairs of feet, facing the way
    on, a cross by each; a chalked line along the front of the channel, mostly scuffed away)."""
    x, y, turn = SLIPPER
    n0 = B.mark()
    B.rbox(ATLAS_MAT, (0.17, 0.066, 0.022), (0, 0, 0.011), p=3.0, cuts=3)
    B.paint(B.since(n0), 'sw_rubber')
    n1 = B.mark()
    B.rbox(ATLAS_MAT, (0.13, 0.062, 0.05), (0.02, 0, 0.034), p=2.6, cuts=3)
    B.paint(B.since(n1), 'sw_felt')
    n2 = B.mark()
    B.sphere(ATLAS_MAT, (-0.045, 0, 0.042), 1.0, seg=8, scale=(0.04, 0.026, 0.012))
    B.paint(B.since(n2), 'sw_fleece')
    B.xform(n0, Matrix.Translation((x, y, 0.0)) @ Matrix.Rotation(math.radians(turn), 4, 'Z'))
    rnd = random.Random(1430)
    for xc in CHALK_FEET:
        yc = -0.02 + rnd.uniform(-0.03, 0.03)
        for sy in (-1, 1):
            cx, cy = xc + rnd.uniform(-0.01, 0.01), yc + sy * 0.055
            pts = [(cx + 0.075 * math.cos(a) * (1.0 if math.cos(a) > 0 else 0.85), cy + 0.03 * math.sin(a))
                   for a in [k * 2 * math.pi / 12 for k in range(12)]]
            B.chalk(pts, w=0.014, closed=True)
        cx = xc - 0.2
        B.chalk([(cx - 0.05, yc - 0.05), (cx + 0.05, yc + 0.05)], w=0.016)
        B.chalk([(cx - 0.05, yc + 0.05), (cx + 0.05, yc - 0.05)], w=0.016)
    x = 263.3
    while x < 275.0:                                                       # the line: dashes, scuffed
        ln = rnd.uniform(0.25, 0.9)
        if rnd.random() < 0.6 and not (DOCK[0] < x < DOCK[1]):
            B.chalk([(x, 0.33 + rnd.uniform(-0.006, 0.006)), (min(x + ln, 275.0), 0.33 + rnd.uniform(-0.006, 0.006))], w=0.018)
        x += ln + rnd.uniform(0.1, 0.5)


def service_cable(bm, runs, mc, ms, out=Vector((0, -1, 0)), r=0.011, pitch=1.05, sag=0.007, joints=(0.33, 0.71)):
    """The present-day service thread (the prologue's 'new cable', art/pass6/build_ending_secrets.py): glossy black
    cable (material index mc) run in straight lengths along a wall, `out` the wall's normal into the room; galvanised
    clips (ms) about every `pitch` m, the cable sagging a little between them (run by hand, not the school's tidy
    conduit); two taped joints (black bands) at fractions `joints` of the whole length. runs: lists of points."""
    total = sum((Vector(b) - Vector(a)).length for run in runs for a, b in zip(run, run[1:]))
    done, tapes = 0.0, [t * total for t in joints]
    for run in runs:
        run = [Vector(p) for p in run]
        pts = [run[0]]
        clips = []
        for a, b in zip(run, run[1:]):
            L = (b - a).length
            n = max(1, int(round(L / pitch)))
            for k in range(1, n + 1):
                mid = a.lerp(b, (k - 0.5) / n)
                if abs((b - a).normalized().z) < 0.3:
                    mid = mid - Vector((0, 0, sag))
                pts += [mid, a.lerp(b, k / n)]
            d = (b - a).normalized()
            for k in range(n + 1 if L > 0.4 else 0):
                p = a + d * 0.12 if k == 0 else (b - d * 0.12 if k == n else a.lerp(b, k / n))
                clips.append((p, d))
        for a, b in zip(pts, pts[1:]):
            add_cyl(bm, a, b, r, mat=mc, seg=6)
            seg = (b - a).length
            for t in tapes:
                if done <= t < done + seg:
                    p = a.lerp(b, (t - done) / seg)
                    d = (b - a).normalized()
                    add_cyl(bm, p - d * 0.03, p + d * 0.03, r * 1.45, mat=mc, seg=6)
            done += seg
        for p, d in clips:
            side = d.cross(out).normalized()
            for sgn in (-1, 1):
                add_box(bm, p + side * sgn * 0.02 - out * (r - 0.004), (0.014, 0.014, 0.014), mat=ms)
            add_cyl(bm, p - side * 0.024 + out * 0.006, p + side * 0.024 + out * 0.006, 0.0065, mat=ms, seg=4)


def build_service(B, coll):
    """The present-day service thread: the new cable along the back wall just under the cornice, the whole length,
    through one small new galvanised relay box at 271 with a green pilot lamp (Att14bRelayLamp, EMIT, lit). Recent
    work on an old building: glossy black, clipped by hand, nothing like the school's own wiring."""
    x0, x1, yf, z0, z1 = RELAY
    y, z = SERVICE_Y, SERVICE_Z
    service_cable(B.bm, [[(X0, y, z), (x0, y, z)], [(x1, y, z), (X1, y, z)]], B.m('NewCable'), B.m('NewSteel'))
    B.box('NewSteel', x0, x1, yf + 0.004, WALL_Y, z0, z1)                        # the box
    B.box('NewSteel', x0 + 0.012, x1 - 0.012, yf, yf + 0.004, z0 + 0.012, z1 - 0.012)   # its lid
    for xx, zz in ((x0 + 0.025, z0 + 0.025), (x1 - 0.025, z0 + 0.025), (x0 + 0.025, z1 - 0.025), (x1 - 0.025, z1 - 0.025)):
        B.cyl('NewSteel', (xx, yf, zz), (xx, yf - 0.006, zz), 0.007, seg=6)
    for xx in (x0, x1):                                                           # glands where the cable goes in
        s = -1 if xx == x0 else 1
        B.cyl('NewSteel', (xx, y - 0.04, z), (xx + s * 0.025, y - 0.04, z), 0.017, seg=8)
    lx, lz, lr = RELAY_LAMP
    B.cyl('NewSteel', (lx, yf, lz), (lx, yf - 0.008, lz), lr + 0.007, seg=12)      # the lamp's bezel
    B.cyl('NewSteel', (lx, yf, lz + 0.075), (lx, yf - 0.004, lz + 0.075), 0.022, seg=6)    # a small switch
    L = MB()
    c = (lx, yf - 0.012, lz)
    L.sphere('Att14bRelayLamp', c, lr, seg=10, scale=(1, 0.6, 1))
    return L.obj('Att14bRelayLamp', coll, origin=c)


def build_lighting(B, coll):
    """Globe pendants on short rods (the lit globes are their own object, EMIT AttGlobeLamp); a dead one between."""
    for x in LAMPS + (DEAD_LAMP,):
        B.cyl('WornIron', (x, 0.0, CEIL), (x, 0.0, GLOBE_Z + 0.13), 0.01, seg=6)
        B.cyl('WornIron', (x, 0.0, CEIL), (x, 0.0, CEIL - 0.03), 0.05, seg=10)
        B.cyl('WornIron', (x, 0.0, GLOBE_Z + 0.15), (x, 0.0, GLOBE_Z + 0.11), 0.045, 0.06, seg=10)
    B.sphere(ATLAS_MAT, (DEAD_LAMP, 0.0, GLOBE_Z), 0.12, seg=12, cell='sw_glass')
    L = MB()
    for x in LAMPS:
        L.sphere('AttGlobeLamp', (x, 0.0, GLOBE_Z), 0.12, seg=14)
    return L.obj('Att14bLamps', coll)


# =====================================================================================================================
# What the game moves
# =====================================================================================================================
def arc_shell(B, mt, c, r, t, a0, a1, x0, x1, seg=8):
    """A curved plate: part of a tube along x (radius r, thickness t) from angle a0 to a1 (0 = +y, 90 = +z)."""
    bm = B.bm
    rings = []
    for k in range(seg + 1):
        a = math.radians(a0 + (a1 - a0) * k / seg)
        ring = []
        for rr in (r, r + t):
            for x in (x0, x1):
                ring.append(bm.verts.new((x, c[1] + rr * math.cos(a), c[2] + rr * math.sin(a))))
        rings.append(ring)              # [inner x0, inner x1, outer x0, outer x1]
    fs = []
    for A, Bv in zip(rings, rings[1:]):
        fs.append(bm.faces.new((A[0], A[1], Bv[1], Bv[0])))        # inner
        fs.append(bm.faces.new((A[2], Bv[2], Bv[3], A[3])))        # outer
        fs.append(bm.faces.new((A[0], Bv[0], Bv[2], A[2])))        # x0 edge
        fs.append(bm.faces.new((A[1], A[3], Bv[3], Bv[1])))        # x1 edge
    for R in (rings[0], rings[-1]):
        fs.append(bm.faces.new((R[0], R[2], R[3], R[1])))
    for f in fs:
        f.material_index = B.m(mt)
    return [v for R in rings for v in R]


def build_trolley(coll):
    """Att14bTrolley: an old escort trolley, built in its own frame (origin on the rail top under the middle of its
    base, facing +x) and placed at (266.0, 0.55, 0.03). A cabinet in faded cream enamel with brass bands, a domed lid,
    a bell on top, ESCORT 3 plates on both sides, a push handle at the back (it was pushed by an escort, once); at the
    front a lamp at 1.0 under a drooping visor (it looks a little down, as its beam does) and a padded push-paddle low
    down; a bogie on the figures' rail (gauge 0.16) under a cast chassis. 0.70 long (x -0.347 to +0.36), 1.2 tall,
    0.29 deep (y +-0.145 at its brass bands)."""
    B = MB()
    hw = 0.14                                                                    # the cabinet's half depth
    # The bogie: side frames, four flanged wheels on the rails, axles, the chassis plate.
    for sy in (-1, 1):
        y = sy * RAIL_G
        B.box('CastIron', -0.26, 0.26, y - 0.009, y + 0.009, 0.035, 0.062)
        for sx in (-1, 1):
            x = sx * 0.19
            B.cyl('CastIron', (x, y - 0.008, 0.03), (x, y + 0.008, 0.03), 0.03, seg=12)
            yf = y - sy * 0.011
            B.cyl('CastIron', (x, yf - 0.003, 0.03), (x, yf + 0.003, 0.03), 0.038, seg=12)
            B.box('CastIron', x - 0.025, x + 0.025, y + sy * 0.009, y + sy * 0.019, 0.025, 0.055)
    for sx in (-1, 1):
        B.cyl('CastIron', (sx * 0.19, -RAIL_G, 0.03), (sx * 0.19, RAIL_G, 0.03), 0.008, seg=6)
    B.box('CastIron', -0.29, 0.23, -0.12, 0.12, 0.062, 0.092)
    # The cabinet: a soft-cornered body, a domed lid, brass bands.
    B.rbox('CreamPaint', (0.56, 2 * hw, 0.84), (-0.03, 0.0, 0.51), p=7.0, cuts=5)
    B.rbox('CreamPaint', (0.52, 0.262, 0.13), (-0.035, 0.0, 0.95), p=5.0, cuts=4)          # the domed lid
    B.box('Brass', -0.316, 0.256, -hw - 0.005, hw + 0.005, 0.09, 0.135)                 # the kick band
    B.box('Brass', -0.311, 0.251, -hw - 0.0015, hw + 0.0015, 0.585, 0.6)                # the waist band
    B.box('Brass', -0.312, 0.252, -hw - 0.002, hw + 0.002, 0.895, 0.915)                # under the lid
    B.box('Rubber', -0.324, -0.31, -0.1, 0.1, 0.15, 0.25)                               # the rear fender
    for sy in (-1, 1):                                                                  # both sides alike
        yf = sy * (hw + 0.001)
        # the door's seam, its brass knob, the vents
        for a, b, c, d in ((-0.24, 0.16, 0.19, 0.198), (-0.24, 0.16, 0.522, 0.53), (-0.24, -0.232, 0.19, 0.53),
                           (0.152, 0.16, 0.19, 0.53)):
            B.box('CastIron', a, b, yf - 0.0015, yf + 0.0015, c, d)
        B.cyl('HandledBrass', (0.12, sy * hw, 0.36), (0.12, sy * (hw + 0.005), 0.36), 0.013, 0.011, seg=8)
        for z in (0.80, 0.83, 0.86):
            B.box('CastIron', -0.24, -0.08, yf - 0.0015, yf + 0.0015, z, z + 0.012)
        # ESCORT 3 on a brass-rimmed plate
        B.box('Brass', -0.215, 0.095, min(sy * (hw - 0.004), sy * (hw + 0.004)), max(sy * (hw - 0.004), sy * (hw + 0.004)),
              0.655, 0.765)
        B.decal(-0.21, 0.09, 0.66, 0.76, sy * (hw + 0.0045), 'escort3', facing=sy)
    # The push handle at the back.
    B.cyl('HandledBrass', (-0.335, -0.115, 0.86), (-0.335, 0.115, 0.86), 0.012, seg=10)
    for sy in (-1, 1):
        B.cyl('HandledBrass', (-0.30, sy * 0.1, 0.86), (-0.335, sy * 0.1, 0.86), 0.008, seg=6)
    # The bell on the lid (Att14bBell's place: its mouth at about z 1.11, x -0.06), and its striker.
    bx = -0.06
    B.cyl('Brass', (bx, 0, 1.0), (bx, 0, 1.02), 0.03, 0.02, seg=10)
    B.cyl('Brass', (bx, 0, 1.02), (bx, 0, 1.115), 0.01, seg=8)
    B.cyl('Brass', (bx, 0, 1.11), (bx, 0, 1.165), 0.056, 0.042, seg=16)
    B.sphere('Brass', (bx, 0, 1.165), 0.042, seg=12, scale=(1, 1, 0.62))
    B.sphere('Brass', (bx, 0, 1.193), 0.008, seg=6)
    B.cyl('WornIron', (bx + 0.09, 0, 1.0), (bx + 0.09, 0, 1.12), 0.005, seg=5)
    B.cyl('WornIron', (bx + 0.09, 0, 1.12), (bx + 0.062, 0, 1.135), 0.004, seg=5)
    B.sphere('WornIron', (bx + 0.06, 0, 1.135), 0.009, seg=6)
    # The lamp: a housing on the front of the lid, tipped down along its beam (about the mouth), a brass rim, the glass
    # (its own emissive material), a drooping visor over it like a tired eyelid.
    tilt = math.atan2(LAMP_Z - CONE_END_Z, CONE_LEN)                            # the beam's axis: 9.8 degrees down
    mouth = (LAMP_DX, 0.0, LAMP_Z - RAIL_H)                                     # in the trolley's frame
    mz = mouth[2]
    n0 = B.mark()
    B.cyl('CastIron', (0.2, 0, mz), (LAMP_DX - 0.024, 0, mz), 0.068, 0.074, seg=16)
    B.sphere('CastIron', (0.2, 0, mz), 0.068, seg=12, scale=(0.55, 1, 1))
    B.cyl('HandledBrass', (LAMP_DX - 0.026, 0, mz), (LAMP_DX, 0, mz), 0.08, 0.079, seg=16)
    B.torus('HandledBrass', (LAMP_DX - 0.004, 0, mz), (1, 0, 0), 0.072, 0.008, seg=16, rseg=5)
    B.cyl('Att14bTrolleyLamp', (LAMP_DX - 0.016, 0, mz), (LAMP_DX - 0.006, 0, mz), 0.064, seg=16)
    B.xform(n0, Ry(tilt, mouth))
    nv = B.mark()
    arc_shell(B, 'CreamPaint', (0, 0, mz), 0.084, 0.006, 12, 168, 0.2, LAMP_DX + 0.025, seg=8)
    arc_shell(B, 'HandledBrass', (0, 0, mz), 0.09, 0.005, 12, 168, LAMP_DX + 0.012, LAMP_DX + 0.03, seg=8)
    B.xform(nv, Ry(tilt + math.radians(6), (0.2, 0, mz)))                       # the visor droops a little more
    B.cyl('CastIron', (0.235, 0, 0.99), (0.235, 0, mz - 0.03), 0.028, seg=10)           # the lamp's neck
    B.cyl('Brass', (0.235, 0, 0.995), (0.235, 0, 1.005), 0.04, seg=12)
    # The paddle: a padded leather push-pad on a backing plate, on two brass rods off the cabinet's front.
    for z in (0.24, 0.36):
        for sy in (-1, 1):
            B.cyl('HandledBrass', (0.245, sy * 0.07, z), (0.285, sy * 0.07, z), 0.009, seg=6)
    B.box('CastIron', 0.28, 0.292, -0.125, 0.125, 0.16, 0.44)
    B.rbox('SorterCushion', (0.07, 0.26, 0.30), (0.325, 0.0, 0.30), p=3.4, cuts=4)
    for sy in (-1, 1):
        for z in (0.24, 0.36):
            B.sphere('SorterCushion', (0.355, sy * 0.06, z), 0.01, seg=6)
    ob = B.obj('Att14bTrolley', coll)
    ob.location = Vector(TROLLEY)
    return ob


def build_cone(coll):
    """Att14bCone: the lamp's beam. Origin at the lamp's mouth; along +x, 2.6 long; its far end a circle of radius 0.6
    in the plane x = 2.6, centred 0.45 below the mouth (0.55 above the floor). 16 sides, open at both ends (a beam,
    not a solid), normals outward. UV u runs 0 at the mouth to 1 at the far end (for a fade), v round it."""
    B = MB()
    bm = B.bm
    mi = B.m('Att14bBeam')
    dz = CONE_END_Z - LAMP_Z
    rings = []
    for x, r, zc in ((0.0, CONE_R0, 0.0), (CONE_LEN, CONE_R, dz)):
        rings.append([bm.verts.new((x, r * math.cos(2 * math.pi * k / CONE_SEG), zc + r * math.sin(2 * math.pi * k / CONE_SEG)))
                      for k in range(CONE_SEG)])
    for k in range(CONE_SEG):
        j = (k + 1) % CONE_SEG
        f = bm.faces.new((rings[0][k], rings[1][k], rings[1][j], rings[0][j]))
        f.material_index = mi
        for lp, uv in zip(f.loops, ((0, k / CONE_SEG), (1, k / CONE_SEG), (1, (k + 1) / CONE_SEG), (0, (k + 1) / CONE_SEG))):
            lp[B.uv].uv = uv
    bm.normal_update()
    for f in bm.faces:                                       # outward: away from the axis
        c = f.calc_center_median()
        t = c.x / CONE_LEN
        axis = Vector((c.x, 0, dz * t))
        if f.normal.dot(c - axis) < 0:
            f.normal_flip()
        f[B.flat] = 1
    ob = B.obj('Att14bCone', coll, sharp=80)
    ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
    ob.location = Vector(MOUTH)
    return ob


def build_figure(coll):
    """Att14bFig: DL-15's rail figure (art/ch1/dl15.py figure_mesh: DL-12/13's jointed pupil on a rail bogie, facing +x,
    origin on the rail top under the stand's centre), a little shabbier: sticking plaster crossed on its cheek, a strip
    on its arm, a buff card on a string round its neck: PUPIL (the card hangs turned toward the corridor)."""
    import dl15
    B0 = dl15.figure_mesh()
    B = MB()
    me = bpy.data.meshes.new('_dl14b_fig')
    B0.bm.to_mesh(me)
    B0.bm.free()
    remap = {}
    for k, n in enumerate(B0.names):
        remap[k] = B.m(n)
    n0 = len(B.bm.faces)
    B.bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    B.bm.faces.ensure_lookup_table()
    for f in B.bm.faces[n0:]:
        f.material_index = remap.get(f.material_index, 0)
    # Sticking plaster, crossed, on the side of its head toward the corridor; a strip round its upper arm.
    for a in (35, -35):
        B.cbox(ATLAS_MAT, (0.0, -0.064, 0.88), (0.075, 0.006, 0.018), rot=Matrix.Rotation(math.radians(a), 4, 'Y'), cell='sw_tape')
    B.cyl(ATLAS_MAT, (0.0, -0.118, 0.6), (0.0, -0.12, 0.56), 0.027, seg=8, cell='sw_tape')
    # The card on its string.
    turn = math.radians(50.0)
    c = Vector((0.115, -0.045, 0.6))
    n1 = B.mark()
    B.tbox(-0.07, 0.07, -0.002, 0.002, -0.045, 0.045, {'-y': 'pupil', '+y': 'pupil', 'all': 'sw_card'})
    B.xform(n1, Matrix.Translation(c) @ Matrix.Rotation(turn, 4, 'Z'))
    side = Vector((math.cos(turn), math.sin(turn), 0))
    for s in (-1, 1):
        top = c + side * (s * 0.056) + Vector((0, 0, 0.033))
        neck = Vector((0.02, s * 0.035, 0.745))
        B.cyl(ATLAS_MAT, neck, top, 0.0025, seg=4, cell='sw_string')
    ob = B.obj('Att14bFig', coll)
    ob.location = Vector(FIG)
    return ob


# =====================================================================================================================
def tris(ob):
    if ob.type != 'MESH':
        return 0
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def build_set(dl01, m, coll):
    make_atlas(ATLAS_PATH)
    B = MB()
    build_shell(B)
    build_niche(B)
    build_bay(B)
    build_rail(B)
    build_stair(B)
    build_signs(B)
    build_dressing(B)
    relay = build_service(B, coll)
    lamps = build_lighting(B, coll)
    objs = [B.obj('Att14bSet', coll), lamps, relay]
    objs.append(build_trolley(coll))
    objs.append(build_cone(coll))
    objs.append(build_figure(coll))
    bpy.context.view_layer.update()
    total_t, total_p = 0, 0
    for ob in objs:
        t = tris(ob)
        total_t += t
        total_p += len(ob.material_slots)
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        print('dl14b: %-14s tris %6d mats %-90s x %.3f..%.3f y %.3f..%.3f z %.3f..%.3f  origin %s' % (
            ob.name, t, [s.material.name for s in ob.material_slots],
            min(v.x for v in bb), max(v.x for v in bb), min(v.y for v in bb), max(v.y for v in bb), min(v.z for v in bb),
            max(v.z for v in bb), tuple(round(c, 3) for c in ob.location)))
    print('dl14b: total tris %d, draw calls (material slots) %d' % (total_t, total_p))
    return objs


REPORT = """DL-14b Unaccompanied (art/ch1/dl14b.py), x 263.0 to 278.0, built in final coordinates (no shift).
Game coords: (x, y, z) = Blender (x, z, -y).

MOVED (origin = pivot, world, built pose):
- Att14bTrolley: origin (266.0, 0.03, -0.55) = the rail top under the middle of its base; facing +x. Slides along x;
  rotate 180 deg about game y (Blender z) to face -x. Footprint: x -0.347..+0.36 about the origin (0.70 long: push
  handle at the back, padded paddle's face at +0.36; the lamp visor's lip reaches +0.37 at z 1.07), depth z +-0.145
  (Blender y 0.405..0.695), cabinet +-0.14. Height 1.2 above the rail top (bell top 1.23 above the floor). Lamp mouth +0.35 at y 1.0.
  Paddle: x +0.29..+0.36, y 0.18..0.48 above the floor, z +-0.13. Bogie: wheels at x +-0.19 (r 0.03) on the rails at
  z -0.47 / -0.63; nothing below the rail top but flanges (inside the rails). Passing the bay it clears the figure
  (whose arm reaches z -0.703) by 8 mm. The bell (Att14bBell) is part of the
  trolley: its mouth about (x -0.06, y 1.14) in the trolley's frame, for a sound emitter.
- Att14bCone: origin (266.35, 1.0, -0.55) = the lamp's mouth (trolley x + 0.35). Points +x: a 16-sided truncated cone,
  r 0.064 at the mouth, r 0.6 at its far end, a circle in the plane x + 2.6 centred at y 0.55 (0.45 below the mouth;
  the axis dips 9.8 deg, the lamp housing is tipped down to match). Open at both ends, normals outward, 32 tris;
  UV u 0 (mouth) to 1 (far end). Material Att14bBeam (simple emissive; the game replaces it, additive, DoubleSide).
  Its far circle reaches y -0.05 (just under the floor) and z -1.15 (0.15 into the back wall), as the build sheet's
  numbers give; it reads fine additive. Parent it to the trolley at local (+0.35, +0.97, 0) or copy its transform.
- Att14bFig: origin (269.9, 0.03, -0.85) = on the spur's rail top under its bogie; facing +x; DL-15's figure mesh
  (0.95 tall above the rail top, body z +-0.15 at its arms, bogie 0.40 long with buffers) plus plaster on its cheek and arm and
  the PUPIL card on a string (hung at its chest, turned 50 deg toward the camera). Slide it to z -0.55 (out of the
  bay onto the main rail), then along x; at 262.2 it is in dl14a's rail stub.

SURFACES and the build sheet's gameplay numbers (all as specified):
- Floor (lino) 263.0-278.0, 0. The rail: timber channel z -0.39..-0.71 (y 0.003), rails z -0.47 / -0.63, top 0.03,
  263.0-275.3; a buffer stop at 275.22-275.3 (0.12 high, under the first tread's nosing).
- Niche A (cloakroom): opening 263.6-264.5, head 1.8. Gameplay depth z -0.25..-1.0: a hood (its underside 1.8, top
  1.925) reaches forward to z -0.25; cheeks either side (x 263.55-263.6, 264.5-264.55) stand from the wall to z -0.76;
  the recess behind the wall face is cut back to z -1.5 (visual depth: pegs, a coat, a scarf, a bench at the back,
  z -1.26..-1.48, seat 0.3). He hides at z -0.62 in front of it, under the hood.
- The bay: opening 269.4-270.4, head 1.9, the same hood/cheeks/recess (cheeks 269.35-269.4, 270.4-270.45). The spur:
  an iron traverser plate in its floor x 269.6-270.2, z -0.39..-0.98 (flush), two guide slots across it; on it a rail
  stub at z -0.77 / -0.93 (x 269.62-270.18, top 0.034) with chocks at its ends (x 269.62-269.655, 270.145-270.18,
  0.06 high, z -0.73..-0.97). The main rail runs on across the plate's front. MODEL PUPIL / FOR ESCORT PRACTICE on
  the hood; a height chart on the bay's back wall (pencil marks R.A., T.O., M).
- The dock: 264.6-265.4, painted on the floor either side of the channel (ESCORT 3 stencilled in front, hatching
  behind); a brass contact between the rails at x 265.0 (the trolley's patrol end); ESCORT 3 DOCK plate on the wall
  (264.7-265.3, y 1.13-1.31) and the dead charging socket under it.
- The stair: 9 open treads (iron chequer plate, a worn nosing), each 0.255 long, 0.1778 high: tread k (1..9) x
  275.3+0.255(k-1) .. +0.255, top 0.1778k (0.178 .. 1.6); the 9th (277.34-277.6) is at 1.6, flush with the landing
  (its run is 0.26 so the stair ends exactly at 277.6). Width z -0.6..+0.45 (Blender y -0.45..0.6). Sawtooth iron
  stringers; a balustrade on its back edge (z -0.58, handrail 0.86 above the treads); nothing on the camera side.
- The landing: 277.6-278.0, 1.6, z -0.6..+0.45; chequer plate on an iron frame, two posts at x 277.62-277.67 and a
  brace on its front face. It butts DL-15's left wall (278.0) under the sick bay's door (sill 1.6).
WALLS/LIMITS: back wall face z -1.0 (0.2 thick), dado to 1.0, ceiling 3.0. The left end is dl14a's wall (263.0), the
right DL-15's (278.0). The dormitory door, opened 90 deg into the corridor, lies along z -0.45 to x 263.82: clear of
niche A's left cheek (which starts at z -0.76).

SIGNS (enamel, on the back wall face): NO PUPIL UNACCOMPANIED x 265.95-268.75, y 1.88-2.43 (over the trolley's built
place); ESCORTS KEEP TO THE RAIL (and "Pupils found in the corridor are returned to the dormitory.") x 271.0-272.3,
y 1.15-1.45; SICK BAY with an arrow up the stair, red, x 275.55-276.45, y 2.05-2.39. CLOAKS on niche A's hood.
DRESSING: a lost slipper by niche A (263.93, 0, -0.1); chalk feet in pairs with a cross by each at x 266.9, 268.55,
271.15, 272.75, 274.25 (along the lane, facing +x) and a scuffed chalk line at z -0.33.

SERVICE THREAD (the director's addition): the prologue's new cable (PLAIN NewCable, glossy black, r 0.011; NewSteel
galvanised clips about every 1.05 m, sagging a little between; two taped joints) along the back wall at y 2.7, z
-0.987, the whole length 263.0-278.0, through a new galvanised relay box at x 270.88-271.12, y 2.58-2.80 (0.11 deep).
Att14bRelayLamp: its green pilot lamp, own object, EMIT Att14bRelayLamp [.45, 1, .5, 5] (lit), origin
(271.0, 2.635, -0.878). Static; nothing for the game to do but keep it lit.

LAMPS: Att14bLamps (EMIT AttGlobeLamp, existing): two globes at (267.35, 2.62, 0) and (276.9, 2.62, 0) (over the
stair); a dead globe at 272.3. Trolley lamp glass: material Att14bTrolleyLamp inside Att14bTrolley (r 0.064, at the
mouth). Suggested lights (index.html P/S format):
P(0xffd8a8, 1.2, 4.5, 267.35, 2.5, 0.0)    the first globe (dim)
P(0xffd8a8, 1.2, 4.0, 276.9, 2.5, 0.0)     the globe over the stair
S(0xffd49a, 6, 3.4, [trolley x + 0.35, 1.0, -0.55], [trolley x + 2.95, 0.55, -0.55], 0.24, true)   the trolley's lamp
P(0xb8c8dc, 0.3, 3, 270.0, 1.2, -1.3)      the bay's recess, cool

MATERIALS: reused WORN WinPlaster, WinDado, WinLino, PigeonWood, CrateWood, WornIron, CastIron, HandledBrass,
PupilWood, CreamPaint (the trolley's faded enamel), SorterCushion (its paddle); PLAIN Brass (the bell), Rubber; EMIT
AttGlobeLamp. New: image Att14bAtlas (textures/dl14b_atlas.png, passes through as a map); EMIT
Att14bTrolleyLamp: [1, .8, .5, 4], Att14bBeam: [1, .85, .6, 1] (the cone; the game overrides it) and
Att14bRelayLamp: [.45, 1, .5, 5]. PLAIN NewCable and NewSteel (existing, pass 6).
"""
