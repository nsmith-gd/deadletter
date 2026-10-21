"""Chapter 1 Attendance, DL-12 Coats Without Children (game x 200.0 to 216.0). Design: docs/chapter1_attendance_plan.md.

Built in final world coordinates (game x = Blender x, game y = Blender z, game z = -Blender y). build_set(dl01, m, coll).

The room: the lower school's cloakroom, its way in. He comes up the iron stair from ring C's well and through an arched
door in the back wall at the left edge (the stair's top platform and rails go down into the dark behind it, the school's
sun-over-open-book mark over the arch). The back wall is six rows of numbered coat hooks (312 of them), all but a
handful empty; those few hold the same patched coats. Along it, left to right: the wire lost-property bin with a
small mustard coat laid on top; the rack of jointed wooden pupil models, chained in, one place empty with its chain
open and the padlock on the floor; the bench across the lane, and behind it peg 7 on its iron coat stand with a lamp
over it; the free pupil model on the lane; the occupancy strip in the floor and its lamp post (PRESENT, COAT 7); the
attendance gate in an arched iron frame (the school's mark on a roundel over the arch), a small speaker by it. Conduits
run on the floor from peg 7 and the strip to the lamp post, and from the post up the wall to the gate's winding box:
cause and effect in the side view. Past the gate the corridor runs to 216, where DL-13's classroom door is (the end is
left open for it). In the corridor's back wall, low, a door stands open on a lit room: the lost property room.

Objects (origins are pivots, in world coordinates):
    AttCloakroom    everything static (cloakroom, corridor, the arrival stair, the lost property room): one object
    AttFigure       the free pupil model: origin on the floor at its centre (207.0, 0, 0); pushable
    AttGate         the grille: origin at its foot on the lane line (209.4, 0, 0); built down (closed); rises +z (game +y)
    AttLampPresent  the PRESENT lamp's dome (EMIT AttLampPresent), origin at the dome's centre
    AttLampCoat     the COAT 7 lamp's dome (EMIT AttLampCoat)
    AttPegLamp      peg 7's little bulb (EMIT AttPegLamp)
    AttCoat         the carried coat, built hanging on its hanger (origin at the inside top of the hanger's hook, the coat
                    hanging along -z, its front to -y); placed as found, laid flat along x on top of the bin
Voice props (art/common/voice_props.py, once VOICE_PROPS_READY exists): the gate's speaker (att_gate_*) and the
caretaker's card player on his desk (att_caretaker).

Textures (PIL, at build time): art/ch1/textures/dl12_atlas.png (1024 x 1024): hook tags, coats and their patches, enamel
labels, the mark, the strip's mat, the clock, the register's pages, lost-property tags, fabrics, notices.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
from build_d17 import add_box, add_cyl, add_sphere, add_torus, rounded_box, worn_material, simple_material, emission_material

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
ATLAS_PATH = os.path.join(TEX, 'dl12_atlas.png')
COMMON = os.path.join(HERE, '..', 'common')

# =====================================================================================================================
# Where things are (Blender world: x = game x, y = -game z, z = game y). Contracts from the design are marked *.
# =====================================================================================================================
X0, X1 = 200.0, 216.0
FLOOR_Y0 = -1.6                     # the floor's front edge (toward the camera)
CEIL = 3.2
WALL_Y = 1.2                        # the cloakroom's back wall face (the hooks' wall)
WALL_T = 0.15
CORR_Y = 1.08                       # the corridor's back wall face; its back face (1.2) is the lost property room's front
DADO = 0.75
ARRIVE = (200.3, 201.2, 2.0)        # the stair's top door in the back wall: x0, x1, head (a fanlight arch over it)
LANDING_Y1 = 1.95                   # the stair's top platform behind the door runs back to here; the flight goes on down
BIN = (202.2, 203.0, 0.32, 0.86, 0.55)       # * lost-property bin: x0, x1, y0, y1, top
RACK = (203.6, 204.4)                         # * the chained pupil models
BENCH = (204.9, 205.9, -0.3, 0.3, 0.42)       # * x0, x1, y0, y1, top (solid)
PEG7 = (205.4, 0.38, 1.18)                    # * the hook's top (where the hanger rests): x, y, z
PEG_POST_Y = 0.5
FIGURE = (207.0, 0.0)                         # * AttFigure
FIG_H, FIG_HW = 0.95, 0.22
STRIP = (208.0, 208.8, -0.34, 0.34)           # * the occupancy strip
POST = (208.9, 0.58)                          # * the lamp post
LAMP_Z = (1.6, 1.34)                          # PRESENT, COAT 7
GATE = (209.3, 209.5, -0.5, 0.98, 1.62)       # * the grille: x0, x1, y0, y1 (between its posts), height; rises 1.3
GATE_X = 209.4
PART = (209.22, 209.58)                       # the gate's partition (the arch over it)
ARCH = (1.66, 1.86)                           # the arch's springing and crown
DOOR_S = (211.6, 212.3, 1.3)                  # * the lost property room's low door: x0, x1, height
DOOR_OPEN = 75.0                              # degrees into the room, hinged at x1
ROOM = (211.0, 214.5, 1.2, 3.6, 2.4)          # * x0, x1, y0, y1, ceiling
DESK = (212.7, 213.9, 2.98, 3.56, 0.74)       # the caretaker's desk: x0, x1, y0, y1, top
COAT_REST = (202.92, 0.59, 0.555)             # AttCoat as found: its hook (laid along x, the coat's hem toward -x)
HOOK_X = (201.45, 209.05)                     # the hook rows
HOOK_ROWS = (0.92, 1.19, 1.46, 1.73, 2.0, 2.27)
HOOK_PITCH = 0.15
HOOK_N = int(round((HOOK_X[1] - HOOK_X[0]) / HOOK_PITCH)) + 1     # 52 to a row, 312 in all

# =====================================================================================================================
# Materials
# =====================================================================================================================
NEW_WORN = {
    # The pupil models' pale beech, handled smooth (DL-13's figures should share it).
    'PupilWood': dict(base=(.36, .27, .17), dirt=(.17, .12, .08), chip=(.46, .38, .27), rough=.7, chip_rough=.6, metallic=0,
                      grime_scale=12, chip_scale=40, chip_amount=.74, dust=(.3, .28, .24), dust_amount=.5),
}
NEW_EMIT = {       # name: (colour, strength), as index.html EMIT (0: the game switches it)
    'AttLampPresent': ((0.55, 1.0, 0.62), 0.0),
    'AttLampCoat': ((1.0, 0.68, 0.28), 0.0),
    'AttPegLamp': ((1.0, 0.68, 0.28), 0.0),
    'AttBulbGlow': ((1.0, 0.82, 0.58), 4.0),
}
# Existing names (the game's tables), for a build where an earlier builder hasn't made them.
FALLBACK_WORN = {
    'Concrete': dict(base=(.075, .074, .07), dirt=(.035, .034, .03), chip=(.12, .115, .105), rough=.92, chip_rough=.9, metallic=0),
    'CrateWood': dict(base=(.18, .12, .07), dirt=(.08, .055, .035), chip=(.25, .19, .12), rough=.85, chip_rough=.8, metallic=0),
    'PigeonWood': dict(base=(.12, .085, .055), dirt=(.06, .045, .03), chip=(.2, .15, .1), rough=.85, chip_rough=.8, metallic=0),
    'HomePlaster': dict(base=(.34, .29, .21), dirt=(.17, .14, .10), chip=(.24, .20, .15), rough=.9, chip_rough=.85, metallic=0),
    'BedroomDado': dict(base=(.20, .30, .26), dirt=(.10, .13, .10), chip=(.34, .29, .21), rough=.8, chip_rough=.9, metallic=0),
    'WornIron': dict(base=(.045, .043, .04), dirt=(.06, .035, .02), chip=(.3, .29, .27), rough=.7, chip_rough=.35, metallic=.6),
    'DepotGreen': dict(base=(.06, .09, .07), dirt=(.04, .035, .025), chip=(.12, .11, .1), rough=.65, chip_rough=.5, metallic=.2),
    'HandledSteel': dict(base=(.06, .065, .06), dirt=(.04, .035, .03), chip=(.55, .53, .5), rough=.55, chip_rough=.22, metallic=.6),
}
FALLBACK_PLAIN = {
    'AtriumDark': ((0.006, 0.006, 0.006), 0.8, 0.0), 'Brass': ((.45, .32, .12), .45, .8), 'DeadBulb': ((.16, .16, .15), .25, 0),
}
FALLBACK_EMIT = {}
ATLAS = 'Dl12AtlasMat'
LORE = 'Dl12LoreMat'
LORE_PATH = os.path.join(TEX, 'dl12_lore.png')


def material(name):
    mt = bpy.data.materials.get(name)
    if mt is not None:
        return mt
    if name in NEW_WORN:
        return worn_material(name, **NEW_WORN[name])
    if name in FALLBACK_WORN:
        return worn_material(name, **FALLBACK_WORN[name])
    if name in NEW_EMIT:
        c, s = NEW_EMIT[name]
        return emission_material(name, c, s)
    if name in FALLBACK_EMIT:
        c, s = FALLBACK_EMIT[name]
        return emission_material(name, c, s)
    if name in FALLBACK_PLAIN:
        c, r, mtl = FALLBACK_PLAIN[name]
        return simple_material(name, c, r, metallic=mtl)
    if name in (ATLAS, LORE):
        path = ATLAS_PATH if name == ATLAS else LORE_PATH
        if not os.path.exists(path):
            (make_atlas if name == ATLAS else make_lore)(path)
        mt, nt, bsdf = d17._new_material(name)
        tex = nt.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(path, check_existing=True)
        nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
        bsdf.inputs['Roughness'].default_value = 0.8
        return mt
    VP = _vp()
    if VP is not None:
        return VP.material(name)
    raise KeyError(name)


# =====================================================================================================================
# The atlas (PIL)
# =====================================================================================================================
AW = 1024
CELLS = {
    'paper': (1008, 0, 1024, 320),
    'coatA': (0, 320, 192, 576), 'coatB': (192, 320, 384, 576), 'coatC': (384, 320, 576, 576),
    'coatM': (576, 320, 768, 576), 'coatK': (768, 320, 960, 576),
    'wood': (960, 320, 1024, 384), 'brass': (960, 384, 1024, 448), 'card': (960, 448, 1024, 512), 'leather': (960, 512, 1024, 576),
    'present': (0, 576, 256, 624), 'coat7': (0, 624, 256, 672), 'cplate': (0, 672, 256, 704),
    'peg7': (256, 576, 384, 704), 'mark': (384, 576, 640, 832), 'strip': (640, 576, 880, 768),
    'clock': (880, 576, 1024, 720), 'notice2': (880, 720, 1024, 768), 'lostsign': (640, 768, 1024, 832),
    'regL': (0, 704, 128, 880), 'regR': (128, 704, 256, 880), 'notice': (256, 704, 384, 832),
    'spines': (256, 832, 640, 880), 'boxlab': (640, 832, 1024, 880),
    'mitten': (0, 880, 64, 960), 'scarf': (64, 880, 128, 960), 'hat': (128, 880, 192, 960), 'shoe': (192, 880, 256, 960),
    'tin': (768, 880, 832, 960), 'jumper': (832, 880, 896, 960), 'cork': (896, 880, 960, 960), 'iron': (960, 880, 1024, 960),
    'banner': (0, 960, 1024, 1024),
}
TAG_W, TAG_H, TAG_COLS = 48, 20, 21
for _k in range(16):                     # the lost-property tags, 64 x 40
    CELLS['ltag%d' % _k] = (256 + (_k % 8) * 64, 880 + (_k // 8) * 40, 256 + (_k % 8) * 64 + 64, 880 + (_k // 8) * 40 + 40)
for _k in range(8):                      # box labels, 48 x 48
    CELLS['box%d' % _k] = (640 + _k * 48, 832, 640 + _k * 48 + 48, 880)
for _k in range(8):                      # register spines, 48 x 48
    CELLS['spine%d' % _k] = (256 + _k * 48, 832, 256 + _k * 48 + 48, 880)


def tag_cell(n):
    k = n - 1
    x0, y0 = (k % TAG_COLS) * TAG_W, (k // TAG_COLS) * TAG_H
    return (x0, y0, x0 + TAG_W, y0 + TAG_H)


def cell_uv(cell):
    x0, y0, x1, y1 = CELLS[cell] if isinstance(cell, str) else cell
    return x0 / AW, 1 - y1 / AW, x1 / AW, 1 - y0 / AW


def _font(size, kind='bold'):
    from PIL import ImageFont
    paths = {'bold': '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf',
             'regular': '/usr/share/fonts/truetype/crosextra/Carlito-Regular.ttf',
             'hand': '/usr/share/fonts/truetype/crosextra/Carlito-Italic.ttf',
             'serif': '/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf',
             'sans': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'}
    try:
        return ImageFont.truetype(paths[kind], size)
    except OSError:
        return ImageFont.load_default()


def _noise_fill(img, box, base, amp, seed, weave=False):
    import numpy as np
    from PIL import Image
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    rng = np.random.default_rng(seed)
    n = rng.normal(0, 1, (h, w)) * amp * 0.5
    coarse = rng.normal(0, 1, (h // 8 + 2, w // 8 + 2))
    coarse = np.asarray(Image.fromarray(((coarse + 3) * 40).clip(0, 255).astype('uint8')).resize((w, h), Image.BILINEAR), dtype=float) / 40 - 3
    n += coarse * amp * 0.6
    if weave:
        yy, xx = np.mgrid[0:h, 0:w]
        n += ((xx + yy) % 4 < 2) * amp * 0.5 - amp * 0.25
    arr = np.clip(np.array(base, dtype=float)[None, None, :] * (1 + n[..., None] / 100.0), 0, 255).astype('uint8')
    img.paste(Image.fromarray(arr, 'RGB'), (x0, y0))


def _stitch_rect(d, box, col, dash=4):
    x0, y0, x1, y1 = box
    for (a, b) in (((x0, y0), (x1, y0)), ((x1, y0), (x1, y1)), ((x1, y1), (x0, y1)), ((x0, y1), (x0, y0))):
        L = math.hypot(b[0] - a[0], b[1] - a[1])
        k = int(L // (dash * 2))
        for i in range(k):
            t0, t1 = i * 2 * dash / L, (i * 2 + 1) * dash / L
            d.line((a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0, a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1),
                   fill=col, width=1)


def _crooked_tree(d, ox, oy, s, ink, w=1):
    """Mara's tree (as dl05's): a crooked trunk, branches, a knot in the right-hand one."""
    def P(pts):
        return [(ox + x * s, oy + y * s) for x, y in pts]
    d.line(P([(0.0, 0.0), (-0.03, -0.14), (0.04, -0.27), (-0.04, -0.42), (0.03, -0.56), (-0.05, -0.72)]), fill=ink, width=w)
    d.line(P([(-0.02, -0.40), (-0.16, -0.48), (-0.24, -0.62), (-0.33, -0.66)]), fill=ink, width=w)
    d.line(P([(0.02, -0.52), (0.14, -0.58), (0.2, -0.62)]), fill=ink, width=w)
    knot = [(0.2 + 0.055 * math.cos(a), -0.655 + 0.05 * math.sin(a)) for a in [math.pi * 0.5 + k * math.pi / 7 for k in range(15)]]
    d.line(P(knot), fill=ink, width=w)
    d.line(P([(0.2, -0.61), (0.27, -0.66), (0.36, -0.7), (0.43, -0.78)]), fill=ink, width=w)
    d.line(P([(-0.05, -0.72), (-0.03, -0.84), (0.03, -0.93)]), fill=ink, width=w)


def _mark(d, mx, my, k, sun, book, ground):
    """The school's mark (dl05's school sign): a sun rising over an open book."""
    d.pieslice((mx - 44 * k, my - 74 * k, mx + 44 * k, my + 14 * k), 180, 360, fill=sun)
    for a in range(200, 341, 28):
        r = math.radians(a)
        d.line((mx + 54 * k * math.cos(r), my - 30 * k + 54 * k * math.sin(r), mx + 76 * k * math.cos(r), my - 30 * k + 76 * k * math.sin(r)),
               fill=sun, width=max(2, int(6 * k)))
    d.polygon([(mx - 70 * k, my - 8 * k), (mx, my + 8 * k), (mx + 70 * k, my - 8 * k), (mx + 70 * k, my + 52 * k), (mx, my + 70 * k),
               (mx - 70 * k, my + 52 * k)], fill=book)
    d.line((mx, my + 8 * k, mx, my + 70 * k), fill=ground, width=max(2, int(5 * k)))


def make_atlas(path):
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(1212)
    img = Image.new('RGB', (AW, AW), (60, 56, 50))
    d = ImageDraw.Draw(img, 'RGBA')
    cream, green, ink, sun = (214, 204, 176), (36, 60, 46), (30, 28, 24), (214, 172, 70)

    # Hook tags: enamel, cream on the school's green, numbered along each row from the bottom left.
    f = _font(15)
    for n in range(1, len(HOOK_ROWS) * HOOK_N + 1):
        x0, y0, x1, y1 = tag_cell(n)
        if n == 7:                                            # its tag went to peg 7's stand: bare wood, two screw holes
            d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(70, 50, 32))
            d.rectangle((x0 + 6, y0 + 3, x1 - 7, y1 - 4), fill=(92, 70, 46))
            for xx in (x0 + 9, x1 - 10):
                d.ellipse((xx - 2, y0 + 8, xx + 2, y0 + 12), fill=(30, 22, 16))
            continue
        d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(70, 50, 32))
        tone = rnd.randint(-14, 8)
        d.rounded_rectangle((x0 + 2, y0 + 2, x1 - 3, y1 - 3), radius=4, fill=(212 + tone, 204 + tone, 178 + tone),
                            outline=(40, 40, 36), width=1)
        d.text(((x0 + x1) / 2, (y0 + y1) / 2), str(n), font=f, fill=(24, 24, 22), anchor='mm')
        if rnd.random() < 0.25:                               # chipped enamel
            cx, cy = rnd.uniform(x0 + 4, x1 - 4), rnd.uniform(y0 + 4, y1 - 4)
            d.ellipse((cx - 2, cy - 1.5, cx + 2, cy + 1.5), fill=(20, 20, 18))
    _noise_fill(img, CELLS['paper'], (206, 198, 174), 6, 1)

    # Coats: wool, a centre seam, buttons, pockets, and patches on patches (elbows at u .08/.92, v .56; see coat_body).
    def coat(cell, base, seed, patches, buttons, toggles=False, tape=None):
        x0, y0, x1, y1 = CELLS[cell]
        w, h = x1 - x0, y1 - y0
        _noise_fill(img, CELLS[cell], base, 10, seed, weave=True)
        cx = x0 + w / 2
        dk = tuple(int(c * 0.55) for c in base)
        d.line((cx, y0 + h * 0.1, cx, y1), fill=dk, width=2)                         # the front opening
        for k in range(4):                                                            # buttons or toggles
            by = y0 + h * (0.2 + k * 0.17)
            if toggles:
                d.rounded_rectangle((cx - 9, by - 3, cx + 9, by + 3), radius=3, fill=buttons)
                d.line((cx - 14, by, cx + 14, by), fill=dk, width=1)
            else:
                d.ellipse((cx - 5, by - 5, cx + 5, by + 5), fill=buttons)
                d.point((cx - 1, by), fill=dk)
        for sx in (-1, 1):                                                            # pockets
            px = cx + sx * w * 0.22
            d.rectangle((px - w * 0.11, y0 + h * 0.62, px + w * 0.11, y0 + h * 0.64), fill=dk)
            _stitch_rect(d, (px - w * 0.11, y0 + h * 0.62, px + w * 0.11, y0 + h * 0.8), tuple(int(c * 0.8) for c in base))
        for (u, v, pw, ph, col) in patches:                                           # patches, stitched on
            px, py = x0 + u * w, y0 + (1 - v) * h
            _noise_fill(img, (int(px - pw / 2), int(py - ph / 2), int(px + pw / 2), int(py + ph / 2)), col, 12, seed + int(u * 100), weave=True)
            _stitch_rect(d, (px - pw / 2 + 2, py - ph / 2 + 2, px + pw / 2 - 2, py + ph / 2 - 2), (200, 190, 160, 200), dash=3)
        d.line((x0, y1 - 3, x1, y1 - 3), fill=dk, width=3)                            # the hem
        if tape:
            d.rectangle((cx + 14, y0 + h * 0.12, cx + 44, y0 + h * 0.17), fill=(220, 214, 196))
            d.text((cx + 29, y0 + h * 0.145), tape, font=_font(11, 'hand'), fill=(40, 40, 90), anchor='mm')
    coat('coatA', (92, 90, 84), 11, [(0.08, 0.56, 30, 36, (70, 64, 52)), (0.92, 0.56, 30, 36, (84, 78, 66)), (0.33, 0.35, 34, 26, (60, 70, 80)),
                                     (0.36, 0.38, 18, 14, (110, 96, 70))], (40, 36, 30))
    coat('coatB', (48, 56, 74), 12, [(0.08, 0.56, 28, 34, (86, 80, 66)), (0.92, 0.56, 28, 34, (86, 80, 66)), (0.7, 0.25, 30, 30, (66, 74, 66)),
                                     (0.25, 0.7, 22, 18, (96, 90, 84))], (160, 150, 120))
    coat('coatC', (96, 72, 52), 13, [(0.08, 0.56, 30, 36, (60, 66, 60)), (0.92, 0.56, 30, 36, (110, 96, 70)), (0.6, 0.4, 26, 22, (80, 70, 90)),
                                     (0.3, 0.18, 30, 24, (70, 60, 50))], (40, 30, 22))
    coat('coatM', (156, 118, 46), 14, [(0.92, 0.56, 26, 30, (118, 104, 70)), (0.3, 0.3, 22, 18, (90, 98, 96))], (70, 52, 30), toggles=True,
         tape='M.')
    coat('coatK', (58, 54, 50), 15, [(0.08, 0.56, 32, 40, (78, 70, 58)), (0.92, 0.56, 32, 40, (78, 70, 58))], (30, 28, 24))

    # Swatches.
    _noise_fill(img, CELLS['wood'], (96, 70, 44), 14, 21)
    for k in range(6):
        y = CELLS['wood'][1] + 6 + k * 10
        d.line((CELLS['wood'][0], y, CELLS['wood'][2], y + rnd.randint(-3, 3)), fill=(70, 50, 30, 120), width=1)
    _noise_fill(img, CELLS['brass'], (150, 112, 50), 12, 22)
    _noise_fill(img, CELLS['card'], (120, 92, 60), 10, 23)
    _noise_fill(img, CELLS['leather'], (64, 38, 26), 16, 24)
    _noise_fill(img, CELLS['iron'], (40, 40, 38), 14, 25)
    _noise_fill(img, CELLS['cork'], (120, 90, 58), 22, 26)

    # Enamel labels on the lamp post, and the caretaker's door plate.
    for cell, text in (('present', 'PRESENT'), ('coat7', 'COAT  7'), ('cplate', 'CARETAKER')):
        x0, y0, x1, y1 = CELLS[cell]
        d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(24, 36, 28))
        d.rounded_rectangle((x0 + 3, y0 + 3, x1 - 4, y1 - 4), radius=8, fill=green, outline=cream, width=3)
        d.text(((x0 + x1) / 2, (y0 + y1) / 2 + 1), text, font=_font(34 if cell != 'cplate' else 24), fill=cream, anchor='mm')
        for xx in (x0 + 12, x1 - 13):
            d.ellipse((xx - 3, (y0 + y1) / 2 - 3, xx + 3, (y0 + y1) / 2 + 3), fill=(110, 106, 92))

    # Peg 7's number disc: cream enamel, a black 7; scratched small beside it in pencil, a crooked tree with a knot.
    x0, y0, x1, y1 = CELLS['peg7']
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(40, 40, 38))
    d.ellipse((x0 + 4, y0 + 4, x1 - 5, y1 - 5), fill=(200, 192, 164), outline=(60, 60, 54), width=4)
    d.text(((x0 + x1) / 2 - 6, (y0 + y1) / 2 + 2), '7', font=_font(84), fill=(26, 26, 24), anchor='mm')
    _crooked_tree(d, x0 + 96, y0 + 96, 34, (96, 96, 104), w=2)

    # The school's mark on a green enamel roundel: RING B LOWER SCHOOL round the rim.
    x0, y0, x1, y1 = CELLS['mark']
    cx, cy, R = (x0 + x1) / 2, (y0 + y1) / 2, 126
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(30, 30, 28))
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=green, outline=(176, 150, 80), width=8)
    d.ellipse((cx - R + 30, cy - R + 30, cx + R - 30, cy + R - 30), outline=cream, width=3)
    _mark(d, cx, cy - 6, 1.05, sun, cream, green)
    ft = _font(19)
    r = R - 16
    for text, centre, step, sign in (('RING  B', -90, 12.5, 1), ('LOWER  SCHOOL', 90, 11.0, -1)):
        n = len(text)
        for i, ch in enumerate(text):
            a = math.radians(centre + sign * (i - (n - 1) / 2) * step)
            d.text((cx + r * math.cos(a), cy + r * math.sin(a)), ch, font=ft, fill=cream, anchor='mm')

    # The occupancy strip: a ribbed rubber treadle in a brass frame, two small painted footprints, STAND HERE.
    x0, y0, x1, y1 = CELLS['strip']
    _noise_fill(img, CELLS['strip'], (34, 33, 31), 14, 31)
    for k in range(x0 + 6, x1 - 4, 9):
        d.line((k, y0 + 4, k, y1 - 4), fill=(20, 20, 19), width=3)
    for sx in (-1, 1):
        fx, fy = (x0 + x1) / 2 + sx * 30, (y0 + y1) / 2 + 12
        d.ellipse((fx - 15, fy - 34, fx + 15, fy + 22), fill=(160, 150, 120, 150))
        for t in range(5):
            d.ellipse((fx - 15 + t * 7, fy - 50 + abs(t - 1) * 2, fx - 9 + t * 7, fy - 43 + abs(t - 1) * 2), fill=(160, 150, 120, 150))
    d.text(((x0 + x1) / 2, y0 + 26), 'STAND HERE', font=_font(30), fill=(170, 160, 128, 170), anchor='mm')

    # The clock, stopped at five to nine: register time.
    x0, y0, x1, y1 = CELLS['clock']
    cx, cy, R = (x0 + x1) / 2, (y0 + y1) / 2, 68
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(30, 28, 26))
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=(206, 198, 172), outline=(40, 36, 30), width=5)
    fn = _font(15)
    for h in range(1, 13):
        a = math.radians(h * 30 - 90)
        d.text((cx + 52 * math.cos(a), cy + 52 * math.sin(a)), str(h), font=fn, fill=ink, anchor='mm')
    for a_deg, L, w in ((8 * 30 + 27.5 - 90, 32, 5), (55 * 6 - 90, 50, 3)):
        a = math.radians(a_deg)
        d.line((cx, cy, cx + L * math.cos(a), cy + L * math.sin(a)), fill=ink, width=w)
    d.ellipse((cx - 4, cy - 4, cx + 4, cy + 4), fill=ink)

    # LOST PROPERTY, enamel, on the bin.
    x0, y0, x1, y1 = CELLS['lostsign']
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(24, 36, 28))
    d.rounded_rectangle((x0 + 4, y0 + 4, x1 - 5, y1 - 5), radius=10, fill=green, outline=cream, width=4)
    d.text(((x0 + x1) / 2, (y0 + y1) / 2 + 2), 'LOST PROPERTY', font=_font(44), fill=cream, anchor='mm')

    # The register, open at its last page: the left page's ticks thin out week by week; on the right, one tick, M.
    def page(cell, names, ticks, head, seed):
        x0, y0, x1, y1 = CELLS[cell]
        _noise_fill(img, CELLS[cell], (212, 204, 180), 4, seed)
        d.text((x0 + 6, y0 + 8), head, font=_font(13, 'hand'), fill=(40, 40, 80), anchor='lm')
        for k in range(14):
            y = y0 + 20 + k * 11
            d.line((x0 + 2, y, x1 - 2, y), fill=(150, 160, 170), width=1)
        for c in range(6):
            x = x0 + 46 + c * 13
            d.line((x, y0 + 16, x, y1 - 4), fill=(170, 140, 140), width=1)
        fh = _font(11, 'hand')
        for k, nm in enumerate(names):
            y = y0 + 25 + k * 11
            d.text((x0 + 4, y), nm, font=fh, fill=(40, 40, 80), anchor='lm')
            for c in range(6):
                if ticks(k, c):
                    x = x0 + 46 + c * 13 + 6
                    d.line((x - 3, y, x - 1, y + 3, x + 4, y - 4), fill=(40, 40, 90), width=1)
    rr = random.Random(77)
    page('regL', ['A. Tull', 'B. Okoro', 'C. Vane', 'D. Pry', 'J. Arden', 'L. Moss', 'M.', 'P. Kell', 'R. Hale', 'S. Ives'],
         lambda k, c: (k == 6) or (rr.random() < 0.55 - c * 0.1 and k in (1, 4, 9)), 'Wk 39', 41)
    page('regR', ['M.'], lambda k, c: k == 0 and c == 0, 'Wk 40', 42)

    # Notices: the cloakroom's rule, and a faded one in the corridor.
    x0, y0, x1, y1 = CELLS['notice']
    _noise_fill(img, CELLS['notice'], (200, 192, 166), 5, 51)
    for k, line in enumerate(('COATS ON PEGS', 'SHOES UNDER', 'THE BENCH', '', 'WALK, DO NOT', 'RUN')):
        d.text(((x0 + x1) / 2, y0 + 16 + k * 18), line, font=_font(15), fill=(40, 40, 36), anchor='mm')
    x0, y0, x1, y1 = CELLS['notice2']
    _noise_fill(img, CELLS['notice2'], (190, 184, 160), 5, 52)
    d.text(((x0 + x1) / 2, y0 + 14), 'WINDOW DRILL', font=_font(14), fill=(50, 50, 46), anchor='mm')
    d.text(((x0 + x1) / 2, y0 + 32), 'every Tuesday', font=_font(12, 'hand'), fill=(60, 60, 90), anchor='mm')

    # Register spines (volumes) and box labels (weeks).
    for k in range(8):
        x0, y0, x1, y1 = CELLS['spine%d' % k]
        col = [(52, 40, 30), (40, 46, 40), (60, 44, 34), (44, 40, 50)][k % 4]
        _noise_fill(img, CELLS['spine%d' % k], col, 12, 60 + k)
        d.rectangle((x0 + 4, y0 + 14, x1 - 5, y0 + 34), fill=(190, 180, 150))
        d.text(((x0 + x1) / 2, y0 + 24), 'REG ' + ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII'][k], font=_font(11), fill=ink, anchor='mm')
    for k in range(8):
        x0, y0, x1, y1 = CELLS['box%d' % k]
        _noise_fill(img, CELLS['box%d' % k], (118, 90, 58), 10, 70 + k)
        d.rectangle((x0 + 5, y0 + 10, x1 - 6, y1 - 12), fill=(206, 198, 172))
        d.text(((x0 + x1) / 2, (y0 + y1) / 2 - 1), 'WK %d' % (32 + k), font=_font(13, 'hand'), fill=(40, 40, 80), anchor='mm')

    # Lost-property tags: a brown label, a name and a week in the caretaker's hand.
    names = ['J. Arden', 'B. Okoro', 'L. Moss', 'T. Finch', 'A. Tull', 'R. Hale', 'S. Ives', 'C. Vane', 'P. Kell', 'D. Pry',
             'N. Ashe', 'E. Lowe', 'F. Grey', 'H. Rook', 'K. Dunn', 'M.D.']
    for k in range(16):
        x0, y0, x1, y1 = CELLS['ltag%d' % k]
        d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(40, 36, 30))
        d.polygon([(x0 + 2, y0 + 8), (x0 + 10, y0 + 2), (x1 - 3, y0 + 2), (x1 - 3, y1 - 3), (x0 + 10, y1 - 3), (x0 + 2, y1 - 9)],
                  fill=(196, 176, 130))
        d.ellipse((x0 + 6, y0 + 16, x0 + 12, y0 + 22), fill=(40, 36, 30))
        d.text((x0 + 38, y0 + 14), names[k], font=_font(12, 'hand'), fill=(36, 36, 80), anchor='mm')
        d.text((x0 + 38, y0 + 28), 'wk %d' % (8 + k * 2), font=_font(11, 'hand'), fill=(36, 36, 80), anchor='mm')

    # Fabrics for the lost things. (The mitten is red, faded to brick: the caretaker says so.)
    _noise_fill(img, CELLS['mitten'], (118, 62, 50), 14, 81, weave=True)
    x0, y0, x1, y1 = CELLS['mitten']
    for y in range(y0 + 50, y0 + 70, 5):
        d.line((x0, y, x1, y), fill=(190, 176, 150, 160), width=2)
    x0, y0, x1, y1 = CELLS['scarf']
    for k in range(8):
        col = [(70, 96, 82), (190, 180, 150), (60, 66, 90), (190, 180, 150)][k % 4]
        _noise_fill(img, (x0 + k * 8, y0, x0 + k * 8 + 8, y1), col, 12, 82 + k, weave=True)
    _noise_fill(img, CELLS['hat'], (66, 84, 112), 14, 83, weave=True)
    _noise_fill(img, CELLS['shoe'], (74, 46, 30), 14, 84)
    x0, y0, x1, y1 = CELLS['tin']
    _noise_fill(img, CELLS['tin'], (70, 96, 116), 8, 85)
    d.rectangle((x0 + 4, y0 + 4, x1 - 5, y1 - 5), outline=(170, 160, 130), width=2)
    d.text(((x0 + x1) / 2, (y0 + y1) / 2), 'M.D.', font=_font(18), fill=(206, 196, 160), anchor='mm')
    _noise_fill(img, CELLS['jumper'], (84, 96, 80), 14, 86, weave=True)

    # The cloakroom's frieze board: the rule, as the gate's voice says it.
    x0, y0, x1, y1 = CELLS['banner']
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(30, 46, 36))
    d.rectangle((x0 + 4, y0 + 4, x1 - 5, y1 - 5), outline=(170, 150, 90), width=3)
    d.text(((x0 + x1) / 2, (y0 + y1) / 2 + 2), 'PLEASE  HANG  YOUR  COAT  ON  YOUR  PEG', font=_font(42), fill=cream, anchor='mm')
    for xx in (x0 + 40, x1 - 40):
        _mark(d, xx, (y0 + y1) / 2 - 2, 0.32, sun, cream, (30, 46, 36))

    # Age it all a little.
    d2 = ImageDraw.Draw(img, 'RGBA')
    for _ in range(260):
        x, y, r = rnd.uniform(0, AW), rnd.uniform(0, AW), rnd.uniform(3, 30)
        d2.ellipse((x - r, y - r, x + r, y + r), fill=(70, 55, 30, rnd.randint(4, 14)))
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.quantize(160, method=Image.Quantize.MEDIANCUT).save(path, optimize=True)


# =====================================================================================================================
# Geometry helpers
# =====================================================================================================================

class Batch:
    """One bmesh (with a UV layer) and its material list."""
    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.mats = []

    def __call__(self, name):
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def box(self, x, y, z, mat, rot=None, bm=None):
        return add_box(bm or self.bm, ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2),
                       (x[1] - x[0], y[1] - y[0], z[1] - z[0]), mat=self(mat), rot=rot)

    def cyl(self, a, b, r, mat, r2=None, seg=8, bm=None):
        return add_cyl(bm or self.bm, a, b, r, r2, mat=self(mat), seg=seg)

    def rbox(self, size, center, mat, p=6.0, cuts=4, rot=None, dents=(), seed=0.0, bm=None):
        return rounded_box(size, center, p=p, cuts=cuts, rot=rot, dents=dents, seed=seed, bm=bm or self.bm, mat=self(mat))

    def quad(self, pts, mat, uv=None):
        """A quad, wound as given (its face is (p1 - p0) x (p2 - p1)); uv: (u0, v0, u1, v1) over its corners."""
        f = self.bm.faces.new([self.bm.verts.new(Vector(p)) for p in pts])
        f.material_index = self(mat)
        if uv:
            u0, v0, u1, v1 = uv
            for lp, (a, b) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
                lp[self.uv].uv = (a, b)
        return f

    def face_quad(self, c, w, h, normal, cell, mat=ATLAS, both=False):
        """A quad centred on c facing `normal` (horizontal normals: -y, +x, ... or +z for one lying flat, its top to +y)."""
        n = Vector(normal).normalized()
        up = Vector((0, 0, 1)) if abs(n.z) < 0.9 else Vector((0, 1, 0))
        right = up.cross(n).normalized()
        c = Vector(c)
        pts = [c - right * w / 2 - up * h / 2, c + right * w / 2 - up * h / 2, c + right * w / 2 + up * h / 2, c - right * w / 2 + up * h / 2]
        self.quad(pts, mat, cell_uv(cell))
        if both:
            self.quad([pts[1], pts[0], pts[3], pts[2]], mat, cell_uv(cell))

    def sub(self):
        tmp = bmesh.new()
        tmp.loops.layers.uv.new('UVMap')
        return tmp

    def merge(self, tmp, M=None):
        if M is not None:
            bmesh.ops.transform(tmp, matrix=M, verts=tmp.verts)
        me = bpy.data.meshes.new('_dl12_tmp')
        tmp.to_mesh(me)
        tmp.free()
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    def painted(self, cell, build, M=None, margin=0.03):
        """build(tmp) adds geometry in local coordinates; each face is projected along its main axis into the atlas
        cell, spread over the geometry's bounds; then it is moved by M and merged."""
        tmp = self.sub()
        build(tmp)
        uvl = tmp.loops.layers.uv['UVMap']
        lo = [min(v.co[i] for v in tmp.verts) for i in range(3)]
        hi = [max(v.co[i] for v in tmp.verts) for i in range(3)]
        u0, v0, u1, v1 = cell_uv(cell)
        mu, mv = (u1 - u0) * margin, (v1 - v0) * margin
        for f in tmp.faces:
            f.normal_update()
            n = f.normal
            ax = max(range(3), key=lambda k: abs(n[k]))
            i, j = [(1, 2), (0, 2), (0, 1)][ax]
            for lp in f.loops:
                p = lp.vert.co
                a = (p[i] - lo[i]) / max(1e-6, hi[i] - lo[i])
                b = (p[j] - lo[j]) / max(1e-6, hi[j] - lo[j])
                lp[uvl].uv = (u0 + mu + (u1 - u0 - 2 * mu) * a, v0 + mv + (v1 - v0 - 2 * mv) * b)
            f.material_index = self(ATLAS)
        self.merge(tmp, M)

    def done(self, name, coll, origin=None, sharp=35):
        if origin is not None:
            bmesh.ops.translate(self.bm, vec=-Vector(origin), verts=self.bm.verts)
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for n in self.mats:
            me.materials.append(material(n))
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        me.set_sharp_from_angle(angle=math.radians(sharp))
        ob = bpy.data.objects.new(name, me)
        if origin is not None:
            ob.location = Vector(origin)
        coll.objects.link(ob)
        return ob


def M_at(x, y, z, turn=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(turn), 4, 'Z')


def sweep(bm, pts, radii, mi, seg=6, caps=True):
    import build_ration_hall as rh
    tmp = bmesh.new()
    rh.sweep(tmp, [Vector(p) for p in pts], radii, seg=seg, caps=caps)
    for f in tmp.faces:
        f.material_index = mi
    me = bpy.data.meshes.new('_dl12_sw')
    tmp.to_mesh(me)
    tmp.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def arc(c, r, a0, a1, n, plane='xz'):
    pts = []
    for k in range(n + 1):
        a = math.radians(a0 + (a1 - a0) * k / n)
        if plane == 'xz':
            pts.append(Vector((c[0] + r * math.cos(a), c[1], c[2] + r * math.sin(a))))
        else:
            pts.append(Vector((c[0], c[1] + r * math.cos(a), c[2] + r * math.sin(a))))
    return pts


def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


# =====================================================================================================================
# Coats
# =====================================================================================================================

def coat_body(bm, s=1.0, hanger=True, hood=False, wide=1.0, length=1.0):
    """A small coat in local coordinates: its top (the hanger's hook, or the coat's own loop) at the origin, hanging
    along -z, its front to -y. Body rings, two sleeves, a collar (and a hood behind)."""
    mi = 0
    if hanger:
        L = [(-0.074, .05, .03), (-0.09, .148, .046), (-0.17, .146, .052), (-0.33, .138, .05), (-0.56, .158, .046)]
    else:   # hung by its loop: the shoulders slump, the collar peaks
        L = [(-0.03, .036, .03), (-0.075, .118, .048), (-0.17, .136, .055), (-0.34, .136, .052), (-0.56, .152, .048)]
    seg = 12
    rings = []
    for z, w, dd in L:
        z = z * s * length if z < -0.12 else z * s
        w = w * s * wide
        dd = dd * s
        ring = []
        for k in range(seg):
            t = 2 * math.pi * k / seg
            ring.append(bm.verts.new((w * math.cos(t), dd * math.sin(t) * (1.05 if math.sin(t) < 0 else 0.95), z)))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(seg):
            bm.faces.new((a[k], a[(k + 1) % seg], b[(k + 1) % seg], b[k])).material_index = mi
    bm.faces.new(rings[0]).material_index = mi
    bm.faces.new(rings[-1][::-1]).material_index = mi
    zs, ws = L[1][0] * s, L[1][1] * s * wide
    for sx in (-1, 1):
        wb = L[2][1] * s * wide
        pts = [(sx * (ws - 0.012 * s), 0.0, zs - 0.012 * s), (sx * (wb + 0.02 * s), -0.004 * s, zs - 0.09 * s),
               (sx * (wb + 0.03 * s), -0.012 * s, (zs - 0.2 * s * length)), (sx * (wb + 0.028 * s), -0.02 * s, zs - 0.33 * s * length)]
        sweep(bm, pts, [0.036 * s, 0.04 * s, 0.037 * s, 0.034 * s], mi, seg=6)
    rounded_box((0.125 * s * wide, 0.082 * s, 0.032 * s), (0, 0.002, L[0][0] * s - 0.006 * s), p=3.0, cuts=2, bm=bm, mat=mi)
    if hood:
        add_sphere(bm, (0, 0.046 * s, L[1][0] * s - 0.05 * s), 1.0, mat=mi, seg=10, scale=(0.082 * s, 0.04 * s, 0.085 * s))


def hanger_bar(bm, s=1.0):
    add_cyl(bm, (-0.16 * s, 0, -0.084 * s), (0.16 * s, 0, -0.084 * s), 0.0075, mat=0, seg=6)
    add_cyl(bm, (-0.03, 0, -0.084 * s), (0.03, 0, -0.084 * s), 0.013, mat=0, seg=6)


def hanger_hook(bm):
    """The wire hook: up from the bar's middle, over the top (the origin is the inside top of the bend), and down."""
    r = 0.0035
    pts = [Vector((0, 0, -0.082)), Vector((-0.012, 0, -0.05))] + arc((0.0, 0, -0.024), 0.024 + r, 200, -20, 8)
    sweep(bm, pts, r, 0, seg=5, caps=True)


# =====================================================================================================================
# The pupil model (a jointed wooden lay figure, child-sized, on a four-castor stand)
# =====================================================================================================================

def figure(B, M, wood='PupilWood', joint='CrateWood', stand='WornIron', pose=None):
    """In local coordinates: the floor at z 0, centred, facing -y, 0.95 tall overall, x within +-0.22. pose: head (tilt,
    turn) in degrees, arms (left, right) forward swing in degrees, elbows bend."""
    pose = pose or {}
    tmp = B.sub()
    w, j, st = B(wood), B(joint), B(stand)
    # The stand: hub, four legs out to castors, a wooden plinth the feet stand on, a rod up into the pelvis.
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = Vector((sx * 0.175, sy * 0.15, 0.072))
            add_cyl(tmp, (0, 0, 0.08), p, 0.012, mat=st, seg=5)
            add_cyl(tmp, p, p - Vector((0, 0, 0.02)), 0.01, mat=st, seg=5)
            add_box(tmp, p - Vector((0, 0, 0.032)), (0.03, 0.012, 0.022), mat=st)
            add_cyl(tmp, (p.x - 0.011, p.y, 0.028), (p.x + 0.011, p.y, 0.028), 0.028, mat=st, seg=8)
    add_cyl(tmp, (0, 0, 0.055), (0, 0, 0.1), 0.032, mat=st, seg=10)
    add_cyl(tmp, (0, 0, 0.1), (0, 0, 0.122), 0.125, mat=j, seg=18)
    add_cyl(tmp, (0, 0.07, 0.12), (0, 0.07, 0.49), 0.009, mat=st, seg=6)
    add_cyl(tmp, (0, 0.072, 0.49), (0, 0.03, 0.49), 0.011, mat=st, seg=6)
    add_torus(tmp, (0, 0.074, 0.36), (0, 0, 1), 0.016, 0.004, mat=st, seg=8, rseg=4)      # the push collar on the rod
    # Legs.
    for sx in (-1, 1):
        x = sx * 0.05
        rounded_box((0.048, 0.1, 0.034), (x, -0.022, 0.139), p=3.0, cuts=2, bm=tmp, mat=w)
        add_sphere(tmp, (x, 0, 0.168), 0.019, mat=j, seg=6)
        add_cyl(tmp, (x, 0, 0.18), (x * 1.04, 0, 0.31), 0.021, 0.026, mat=w, seg=8)
        add_sphere(tmp, (x * 1.04, 0, 0.325), 0.026, mat=j, seg=8)
        add_cyl(tmp, (x * 1.04, 0, 0.34), (x * 1.1, 0, 0.452), 0.03, 0.036, mat=w, seg=8)
        add_sphere(tmp, (x * 1.1, 0, 0.468), 0.031, mat=j, seg=8)
    # Body: pelvis, waist ball, chest, neck, head (an egg: no face).
    rounded_box((0.158, 0.098, 0.085), (0, 0, 0.5), p=3.0, cuts=3, bm=tmp, mat=w)
    add_sphere(tmp, (0, 0, 0.553), 1.0, mat=j, seg=10, scale=(0.05, 0.04, 0.03))
    rounded_box((0.186, 0.11, 0.165), (0, 0, 0.644), p=3.2, cuts=3, bm=tmp, mat=w)
    ht, hy = pose.get('head', (0.0, 0.0))
    Hm = Matrix.Translation((0, 0, 0.728)) @ Matrix.Rotation(math.radians(hy), 4, 'Z') @ Matrix.Rotation(math.radians(ht), 4, 'X')
    hv0 = len(tmp.verts)
    add_cyl(tmp, (0, 0, 0.0), (0, 0, 0.05), 0.021, mat=j, seg=8)
    add_sphere(tmp, (0, 0, 0.136), 1.0, mat=w, seg=12, scale=(0.062, 0.068, 0.085))
    tmp.verts.ensure_lookup_table()
    for v in tmp.verts[hv0:]:
        v.co = Hm @ v.co
    # Arms: shoulder balls, upper arm, elbow, forearm, wrist, a paddle hand.
    for side, sx in (('left', -1), ('right', 1)):
        swing = pose.get(side, 4.0)
        bend = pose.get(side + '_bend', 12.0)
        sh = Vector((sx * 0.112, 0, 0.705))
        add_sphere(tmp, sh, 0.029, mat=j, seg=8)
        R1 = Matrix.Rotation(math.radians(swing), 3, 'X') @ Matrix.Rotation(math.radians(sx * 5), 3, 'Y')
        el = sh + R1 @ Vector((0, 0, -0.135))
        add_cyl(tmp, sh + R1 @ Vector((0, 0, -0.02)), el + R1 @ Vector((0, 0, 0.014)), 0.021, 0.018, mat=w, seg=8)
        add_sphere(tmp, el, 0.02, mat=j, seg=6)
        R2 = R1 @ Matrix.Rotation(math.radians(bend), 3, 'X')
        wr = el + R2 @ Vector((0, 0, -0.115))
        add_cyl(tmp, el + R2 @ Vector((0, 0, -0.012)), wr, 0.017, 0.014, mat=w, seg=8)
        add_sphere(tmp, wr, 0.014, mat=j, seg=5)
        hc = wr + R2 @ Vector((0, 0, -0.042))
        rounded_box((0.022, 0.044, 0.062), hc, p=3.0, cuts=2, bm=tmp, mat=w, rot=R2.to_4x4())
    B.merge(tmp, M)


# =====================================================================================================================
# The cloakroom
# =====================================================================================================================

def build_shell(B):
    # Floor (wood boards on a slab), the room's left end, the ceiling and its beams.
    B.box((X0 - 1.0, X1), (FLOOR_Y0, WALL_Y + WALL_T), (-0.2, -0.004), 'Concrete')
    B.box((X0 - 1.0, X1), (FLOOR_Y0, FLOOR_Y0 + 0.3), (-3.2, -0.2), 'Concrete')        # the foundation's cut face
    for k in range(int((WALL_Y - FLOOR_Y0) / 0.16)):                          # the boards, along the room
        y0 = FLOOR_Y0 + k * 0.16
        B.box((X0, X1), (y0 + 0.003, y0 + 0.157), (-0.01, 0.0), 'PigeonWood')
    B.box((X0 - 1.0, X0), (FLOOR_Y0, WALL_Y + WALL_T), (0.0, CEIL + 0.3), 'Concrete')   # the left end: rock and block
    B.box((X0 - 0.2, X1), (-1.0, WALL_Y + WALL_T), (CEIL, CEIL + 0.25), 'Concrete')
    for x in (201.5, 203.5, 205.5, 207.5, 211.0, 213.5, 215.5):
        B.box((x - 0.1, x + 0.1), (-1.0, WALL_Y), (CEIL - 0.22, CEIL), 'HomePlaster')
    # The cloakroom's back wall (x 200 to the gate's partition), the stair's door in it.
    a0, a1, ah = ARRIVE
    yb = (WALL_Y, WALL_Y + WALL_T)
    for (x0, x1) in ((X0, a0), (a1, PART[0])):
        B.box((x0, x1), yb, (0.0, DADO), 'BedroomDado')
        B.box((x0, x1), yb, (DADO, CEIL), 'HomePlaster')
    B.box((a0, a1), yb, (ah, CEIL), 'HomePlaster')
    B.box((X0, PART[0]), (WALL_Y - 0.025, WALL_Y), (DADO - 0.02, DADO + 0.03), 'CrateWood')     # dado rail
    B.box((a1, PART[0]), (WALL_Y - 0.02, WALL_Y), (0.0, 0.1), 'CrateWood')                     # skirting
    B.box((X0, a0), (WALL_Y - 0.02, WALL_Y), (0.0, 0.1), 'CrateWood')
    # The door's surround: architrave, the fanlight's arch (dark glass, iron glazing bars), the mark over it.
    cx = (a0 + a1) / 2
    R = (a1 - a0) / 2
    yf = WALL_Y - 0.004
    for x in (a0 - 0.05, a1 + 0.05):
        B.box((x - 0.05, x + 0.05), (WALL_Y - 0.03, WALL_Y), (0.0, ah), 'CrateWood')
    B.box((a0 - 0.1, a1 + 0.1), (WALL_Y - 0.03, WALL_Y), (ah - 0.03, ah + 0.05), 'CrateWood')
    fan = [Vector((cx, yf, ah + 0.05))] + arc((cx, yf, ah + 0.05), R, 180, 0, 12)
    f = B.bm.faces.new([B.bm.verts.new(p) for p in [fan[0]] + fan[1:][::-1]])
    f.material_index = B('AtriumDark')
    for k in range(1, 6):
        a = math.radians(180 * k / 6)
        B.cyl((cx, yf - 0.01, ah + 0.05), (cx + R * math.cos(a), yf - 0.01, ah + 0.05 + R * math.sin(a)), 0.008, 'WornIron', seg=4)
    sweep(B.bm, arc((cx, WALL_Y - 0.02, ah + 0.05), R + 0.05, 180, 0, 14), 0.035, B('CrateWood'), seg=6)
    B.box((cx - 0.06, cx + 0.06), (WALL_Y - 0.05, WALL_Y), (ah + 0.05 + R - 0.02, ah + 0.05 + R + 0.14), 'CrateWood')   # keystone
    mz = ah + R + 0.42
    B.cyl((cx, WALL_Y, mz), (cx, WALL_Y - 0.025, mz), 0.2, 'DepotGreen', seg=24)
    B.face_quad((cx, WALL_Y - 0.027, mz), 0.38, 0.38, (0, -1, 0), 'mark')
    # Behind the door: the stair's top platform and the flight going down into the well, its rails; dark beyond.
    yl = WALL_Y + WALL_T
    B.box((a0 - 0.3, a1 + 0.3), (yl, LANDING_Y1), (-0.25, 0.0), 'WornIron')
    for k in range(9):                                                            # treads, open risers, going down and away
        y0 = LANDING_Y1 + k * 0.28
        z = -0.2 * (k + 1)
        B.box((a0 + 0.1, a1 - 0.1), (y0, y0 + 0.3), (z - 0.03, z), 'WornIron')
    for x in (a0 + 0.12, a1 - 0.12):
        B.cyl((x, LANDING_Y1, -0.05), (x, LANDING_Y1 + 9 * 0.28, -1.85), 0.03, 'WornIron', seg=4)       # stringers
        top = [(x, yl + 0.05, 0.92), (x, LANDING_Y1, 0.92), (x, LANDING_Y1 + 9 * 0.28, 0.92 - 1.8)]
        sweep(B.bm, top, 0.026, B('WornIron'), seg=6)                                                    # the handrail
        for k, yy in enumerate((yl + 0.05, LANDING_Y1, LANDING_Y1 + 0.84, LANDING_Y1 + 1.68)):
            ztop = 0.92 if yy <= LANDING_Y1 else 0.92 - (yy - LANDING_Y1) / 0.28 * 0.2
            zbot = 0.0 if yy <= LANDING_Y1 else ztop - 0.92
            B.cyl((x, yy, zbot), (x, yy, ztop), 0.02, 'WornIron', seg=5)
        B.cyl((x, LANDING_Y1, 0.92), (x, LANDING_Y1, 1.0), 0.03, 'WornIron', seg=6)                     # the newel's knob
    for x in (a0 - 0.3, a1 + 0.3):                                                                       # the well's walls
        B.box((x - 0.12 if x < cx else x, x if x < cx else x + 0.12), (yl, 4.6), (-3.0, CEIL), 'Concrete')
    B.quad([(a0 - 0.3, 4.5, -3.0), (a1 + 0.3, 4.5, -3.0), (a1 + 0.3, 4.5, CEIL), (a0 - 0.3, 4.5, CEIL)], 'AtriumDark')
    B.box((a0 - 0.42, a1 + 0.42), (yl, 4.6), (2.45, 2.6), 'Concrete')
    # The door, swung right back flat against the wall's far side (its edge shows at the left jamb).
    B.box((a0 - 0.86, a0 + 0.01), (yl, yl + 0.045), (0.02, 1.96), 'CrateWood')


def build_hooks(B, rnd):
    """Six rows of numbered hooks on rails along the back wall, 52 to a row; a handful of coats."""
    n_per = HOOK_N
    yf = WALL_Y
    coats = {(0, 4): 'coatA', (0, 17): 'coatB', (1, 9): 'coatC', (0, 30): 'coatA', (1, 38): 'coatB', (0, 44): 'coatC',
             (2, 24): 'coatB'}
    n = 0
    for r, z in enumerate(HOOK_ROWS):
        B.box((HOOK_X[0] - 0.12, HOOK_X[1] + 0.12), (yf - 0.022, yf), (z - 0.05, z + 0.05), 'CrateWood')
        for k in range(n_per):
            n += 1
            x = HOOK_X[0] + k * HOOK_PITCH
            # the tag over the hook, the hook below it
            B.quad([(x - 0.03, yf - 0.0235, z + 0.008), (x + 0.03, yf - 0.0235, z + 0.008), (x + 0.03, yf - 0.0235, z + 0.044),
                    (x - 0.03, yf - 0.0235, z + 0.044)], ATLAS, cell_uv(tag_cell(n)))
            bent = rnd.random() < 0.03
            B.quad([(x - 0.01, yf - 0.0235, z - 0.046), (x + 0.01, yf - 0.0235, z - 0.046), (x + 0.01, yf - 0.0235, z - 0.004),
                    (x - 0.01, yf - 0.0235, z - 0.004)], 'Brass')
            tip = Vector((x + (0.012 if bent else 0), yf - 0.085, z - 0.04 + (-0.02 if bent else 0.0)))
            sweep(B.bm, [(x, yf - 0.02, z - 0.022), tip, tip + Vector((0, -0.006, 0.026))], 0.0055, B('Brass'), seg=4, caps=False)
            if (r, k) in coats:
                cell = coats[(r, k)]
                M = Matrix.Translation(tip + Vector((0, 0.022, 0.012))) @ Matrix.Rotation(math.radians(rnd.uniform(-4, 4)), 4, 'Z')
                B.painted(cell, lambda bm, h=(r + k) % 2 == 0: coat_body(bm, s=1.0, hanger=False, hood=h,
                                                                          length=1.0 if r == 0 else 0.9), M)
    # The shoe rack under the hooks: low cubbies along the wall, nearly all empty.
    x0, x1 = HOOK_X[0] - 0.1, HOOK_X[1] + 0.1
    B.box((x0, x1), (0.96, WALL_Y), (0.24, 0.262), 'CrateWood')
    B.box((x0, x1), (0.96, WALL_Y), (0.04, 0.06), 'CrateWood')
    x = x0
    while x <= x1 + 1e-6:
        B.box((x - 0.01, x + 0.01), (0.96, WALL_Y), (0.0, 0.24), 'CrateWood')
        x += 0.3
    for (sx, cell) in ((x0 + 0.3 * 7 + 0.15, 'shoe'), (x0 + 0.3 * 19 + 0.15, 'shoe')):
        for dx in (-0.045, 0.045):
            B.painted(cell, lambda bm: rounded_box((0.06, 0.13, 0.05), (0, 0, 0), p=2.6, cuts=4, bm=bm, mat=0),
                      Matrix.Translation((sx + dx, 1.08, 0.085)))
    # The frieze board over the hooks, and the rule notice by the door.
    B.box((202.0, 208.4), (yf - 0.02, yf), (2.42, 2.66), 'CrateWood')
    B.quad([(202.04, yf - 0.021, 2.44), (208.36, yf - 0.021, 2.44), (208.36, yf - 0.021, 2.64), (202.04, yf - 0.021, 2.44 + 0.2)],
           ATLAS, cell_uv('banner'))


def build_bin(B):
    """The lost-property bin: a wire cage on castors, top 0.55, a pile of lost things in it; its enamel sign."""
    x0, x1, y0, y1, top = BIN
    iron = 'WornIron'
    for x in (x0, x1):
        for y in (y0, y1):
            B.box((x - 0.012, x + 0.012), (y - 0.012, y + 0.012), (0.08, top), iron)
            B.cyl((x, y, 0.08), (x, y, 0.05), 0.006, iron, seg=4)
            B.box((x - 0.016, x + 0.016), (y - 0.006, y + 0.006), (0.03, 0.06), iron)
            B.cyl((x - 0.01, y, 0.035), (x + 0.01, y, 0.035), 0.035, 'AtriumDark', seg=8)
    for z in (0.08, top):
        for (a, b) in (((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)), ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1))):
            B.cyl((a[0], a[1], z), (b[0], b[1], z), 0.01, iron, seg=4)
    B.box((x0, x1), (y0, y1), (0.075, 0.085), iron)
    for z in (0.2, 0.32, 0.44):
        for (a, b) in (((x0, y0), (x1, y0)), ((x0, y1), (x1, y1)), ((x0, y0), (x0, y1)), ((x1, y0), (x1, y1))):
            B.cyl((a[0], a[1], z), (b[0], b[1], z), 0.003, iron, seg=3)
    k = 0
    x = x0 + 0.05
    while x < x1 - 0.02:
        for y in (y0, y1):
            B.cyl((x, y, 0.08), (x, y, top), 0.003, iron, seg=3)
        x += 0.05
    y = y0 + 0.05
    while y < y1 - 0.02:
        for xx in (x0, x1):
            B.cyl((xx, y, 0.08), (xx, y, top), 0.003, iron, seg=3)
        y += 0.05
    # The pile: a jumper, a hat, mittens, a scarf trailing over the side, a shoe.
    pile = [('jumper', (0.5, 0.36, 0.18), (202.45, 0.6, 0.16), 10), ('hat', (0.16, 0.16, 0.11), (202.78, 0.48, 0.3), -20),
            ('scarf', (0.42, 0.12, 0.05), (202.6, 0.72, 0.33), 30), ('jumper', (0.32, 0.28, 0.16), (202.8, 0.7, 0.26), -8),
            ('mitten', (0.07, 0.03, 0.1), (202.35, 0.45, 0.3), 50), ('shoe', (0.06, 0.13, 0.05), (202.5, 0.78, 0.38), 70),
            ('card', (0.36, 0.3, 0.12), (202.55, 0.58, 0.4), 4)]
    for cell, size, c, turn in pile:
        B.painted(cell, lambda bm, size=size: rounded_box(size, (0, 0, 0), p=2.4, cuts=2, bm=bm, mat=0, dents=((0.006, 9.0),), seed=size[0]),
                  M_at(*c, turn))
    B.painted('scarf', lambda bm: sweep(bm, [(0, 0, 0), (0.0, -0.06, -0.02), (0.0, -0.085, -0.12), (0.01, -0.09, -0.24)], 0.022, 0, seg=5),
              Matrix.Translation((202.32, y0 + 0.08, top)))
    # LOST PROPERTY, hung on the cage's front.
    B.box((x0 + 0.12, x1 - 0.12), (y0 - 0.012, y0 - 0.004), (0.36, 0.46), 'DepotGreen')
    B.face_quad(((x0 + x1) / 2, y0 - 0.0135, 0.41), 0.54, 0.09, (0, -1, 0), 'lostsign')


def build_rack(B):
    """The class, chained in: three pupil models in their places, one place empty, its chain open, the padlock down."""
    x0, x1 = RACK
    yb = 1.12
    for x in (x0 - 0.04, x1 + 0.04):
        B.box((x - 0.025, x + 0.025), (yb - 0.025, yb + 0.025), (0.0, 1.05), 'CrateWood')
    for z in (0.32, 0.98):
        B.box((x0 - 0.065, x1 + 0.065), (yb - 0.02, yb + 0.02), (z - 0.035, z + 0.035), 'CrateWood')
    B.box((x0 - 0.065, x1 + 0.065), (0.38, yb), (0.0, 0.02), 'CrateWood')                       # the floor board they stand on
    places = [((203.82, 0.92), 8, {'head': (6, 12), 'left': 3, 'right': 8}),
              ((204.2, 0.86), -10, {'head': (-4, -18), 'left': 10, 'right': 2, 'right_bend': 30}),
              ((203.84, 0.56), 4, {'head': (10, 28), 'left': 6, 'right': 0})]
    for (x, y), turn, pose in places:
        figure(B, M_at(x, y, 0.02, turn), pose=pose)
    # The chain: from a ring in the wall, round each stand's hub, to the empty place, open, and its padlock on the floor.
    ring = Vector((x0 - 0.04, yb - 0.03, 0.32))
    add_torus(B.bm, ring, (0, 1, 0), 0.03, 0.006, mat=B('WornIron'), seg=10, rseg=4)
    path = [ring, Vector((203.82, 0.92, 0.09)), Vector((204.2, 0.86, 0.09)), Vector((203.84, 0.56, 0.09)),
            Vector((204.22, 0.5, 0.03)), Vector((204.3, 0.42, 0.02))]
    pts = []
    for a, b in zip(path, path[1:]):
        L = (b - a).length
        n = max(1, int(L / 0.034))
        for k in range(n):
            pts.append((a.lerp(b, k / n), (b - a).normalized()))
    for k, (p, t) in enumerate(pts):
        side = t.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = Vector((1, 0, 0))
        axis = side if k % 2 == 0 else t.cross(side)
        add_torus(B.bm, p, axis.normalized(), 0.014, 0.004, mat=B('WornIron'), seg=6, rseg=3)
    # the padlock, open, on the floor where the fourth stood
    px, py = 204.34, 0.4
    B.box((px - 0.03, px + 0.03), (py - 0.012, py + 0.012), (0.022, 0.07), 'Brass')
    sweep(B.bm, [(px - 0.02, py, 0.07), (px - 0.02, py, 0.1)] + [tuple(v) for v in arc((px, py, 0.1), 0.02, 180, 0, 6)][1:]
          + [(px + 0.02, py, 0.085)], 0.004, B('WornIron'), seg=4)


def build_bench(B):
    """The bench across the lane (solid, top 0.42): slats on iron trestles, a shoe shelf under, an apron to the front."""
    x0, x1, y0, y1, top = BENCH
    for k in range(4):
        ya = y0 + k * 0.152
        B.rbox((x1 - x0, 0.142, 0.032), ((x0 + x1) / 2, ya + 0.071, top - 0.016), 'CrateWood', p=8, cuts=3)
    for x in (x0 + 0.06, x1 - 0.06):
        for y in (y0 + 0.04, y1 - 0.04):
            B.box((x - 0.022, x + 0.022), (y - 0.022, y + 0.022), (0.0, top - 0.032), 'WornIron')
        B.box((x - 0.02, x + 0.02), (y0 + 0.04, y1 - 0.04), (top - 0.07, top - 0.032), 'WornIron')
        B.box((x - 0.016, x + 0.016), (y0 + 0.04, y1 - 0.04), (0.1, 0.12), 'WornIron')
    B.box((x0 + 0.04, x1 - 0.04), (y0 - 0.005, y0 + 0.02), (top - 0.11, top - 0.032), 'CrateWood')     # the apron
    for k in range(3):
        ya = y0 + 0.06 + k * 0.17
        B.box((x0 + 0.08, x1 - 0.08), (ya, ya + 0.13), (0.12, 0.14), 'CrateWood')                    # the shoe shelf
    # one pair of small wellingtons under it, left behind
    for dx in (-0.05, 0.05):
        bx = 205.18 + dx
        B.painted('iron', lambda bm: (rounded_box((0.055, 0.13, 0.04), (0, -0.03, 0.02), p=2.6, cuts=3, bm=bm, mat=0),
                                      rounded_box((0.055, 0.07, 0.15), (0, 0.0, 0.1), p=2.6, cuts=3, bm=bm, mat=0)),
                  Matrix.Translation((bx, 0.05, 0.14)))


def build_peg7(B, coll):
    """Peg 7: an iron coat stand at the bench's back edge, a brass peg (top at 1.18), its number disc, a caged bulb over
    it, and the conduit from its foot along the floor to the lamp post."""
    x, yp = PEG7[0], PEG_POST_Y
    hz = PEG7[2]
    B.cyl((x, yp, 0.0), (x, yp, 0.03), 0.09, 'WornIron', r2=0.07, seg=12)
    B.cyl((x, yp, 0.03), (x, yp, 1.58), 0.022, 'WornIron', seg=8)
    B.cyl((x, yp, 1.58), (x, yp, 1.62), 0.03, 'WornIron', seg=8)
    add_sphere(B.bm, (x, yp, 1.64), 0.026, mat=B('WornIron'), seg=8)
    # the peg: out of a collar on the post toward the lane, its tip turned up; its top at 1.18
    r = 0.009
    B.cyl((x, yp + 0.0, hz - r - 0.01), (x, yp + 0.0, hz - r + 0.03), 0.03, 'WornIron', seg=8)
    B.cyl((x, yp - 0.02, hz - r), (x, PEG7[1] - 0.04, hz - r), r, 'Brass', seg=8)
    B.cyl((x, PEG7[1] - 0.04, hz - r), (x, PEG7[1] - 0.052, hz + 0.025), r, 'Brass', seg=8)
    add_sphere(B.bm, (x, PEG7[1] - 0.053, hz + 0.028), 0.012, mat=B('Brass'), seg=8)
    # its number, on a plate on the post above the peg
    B.box((x - 0.05, x + 0.05), (yp - 0.03, yp - 0.022), (1.25, 1.35), 'WornIron')
    B.face_quad((x, yp - 0.031, 1.3), 0.092, 0.092, (0, -1, 0), 'peg7')
    # the bulb's bracket and cage (the bulb is AttPegLamp)
    lc = Vector((x, yp - 0.1, 1.45))
    B.cyl((x, yp - 0.02, 1.49), (x, lc.y, 1.49), 0.008, 'WornIron', seg=5)
    B.cyl((x, lc.y, 1.49), (x, lc.y, 1.475), 0.022, 'WornIron', seg=10)
    for k in range(4):
        a = k * math.pi / 2 + math.pi / 4
        p = Vector((math.cos(a) * 0.03, math.sin(a) * 0.03, 0))
        sweep(B.bm, [lc + Vector((0, 0, 0.025)) + p * 0.6, lc + p + Vector((0, 0, 0.0)), lc + p * 0.5 + Vector((0, 0, -0.035))],
              0.002, B('WornIron'), seg=3, caps=False)
    L = Batch()
    add_sphere(L.bm, lc, 0.019, mat=L('AttPegLamp'), seg=10)
    L.done('AttPegLamp', coll, origin=lc)
    # conduit: down the post and along the floor behind the lane to the lamp post
    c_y = 0.64
    B.cyl((x + 0.03, yp + 0.0, 1.45), (x + 0.03, yp, 0.02), 0.009, 'WornIron', seg=5)
    B.cyl((x + 0.03, yp, 0.012), (x + 0.03, c_y, 0.012), 0.011, 'WornIron', seg=5)
    B.cyl((x + 0.03, c_y, 0.012), (POST[0] - 0.05, c_y, 0.012), 0.011, 'WornIron', seg=5)
    for xx in [x + 0.3 + k * 0.6 for k in range(6)]:
        if xx < POST[0] - 0.1:
            B.box((xx - 0.015, xx + 0.015), (c_y - 0.02, c_y + 0.02), (0.0, 0.026), 'WornIron')


def build_strip_and_post(B, coll):
    """The occupancy strip (a treadle in a brass frame, flush) and the lamp post: PRESENT over COAT 7."""
    x0, x1, y0, y1 = STRIP
    B.box((x0 - 0.03, x1 + 0.03), (y0 - 0.03, y1 + 0.03), (-0.01, 0.006), 'Brass')
    B.box((x0, x1), (y0, y1), (-0.01, 0.0075), 'AtriumDark')
    B.quad([(x0, y0, 0.0085), (x1, y0, 0.0085), (x1, y1, 0.0085), (x0, y1, 0.0085)], ATLAS, cell_uv('strip'))
    # the strip's lead to the post
    px, py = POST
    B.cyl((x1 + 0.03, y1 + 0.03, 0.01), (px, y1 + 0.03, 0.01), 0.011, 'WornIron', seg=5)
    B.cyl((px, y1 + 0.03, 0.01), (px, py, 0.01), 0.011, 'WornIron', seg=5)
    # the post: cast iron, school green, a lamp panel at its top with two domes and their enamel labels
    B.box((px - 0.08, px + 0.08), (py - 0.08, py + 0.08), (0.0, 0.05), 'DepotGreen')
    B.cyl((px, py, 0.05), (px, py, 0.14), 0.05, 'DepotGreen', r2=0.036, seg=10)
    B.cyl((px, py, 0.14), (px, py, 1.17), 0.032, 'DepotGreen', seg=10)
    pf = py - 0.05
    B.box((px - 0.19, px + 0.19), (pf, py + 0.03), (1.13, 1.74), 'DepotGreen')
    B.box((px - 0.21, px + 0.21), (pf - 0.03, py + 0.05), (1.74, 1.78), 'DepotGreen')
    for z, lname, cell in ((LAMP_Z[0], 'AttLampPresent', 'present'), (LAMP_Z[1], 'AttLampCoat', 'coat7')):
        B.cyl((px, pf, z), (px, pf - 0.018, z), 0.056, 'Brass', seg=16)
        L = Batch()
        c = Vector((px, pf - 0.018, z))
        add_sphere(L.bm, c, 0.045, mat=L(lname), seg=14, scale=(1, 0.7, 1))
        L.done(lname, coll, origin=c)
        B.face_quad((px, pf - 0.002, z - 0.1), 0.35, 0.066, (0, -1, 0), cell)
    # the post's lead up the wall to the gate's winding box
    B.cyl((px + 0.08, py + 0.02, 1.7), (px + 0.08, WALL_Y - 0.02, 1.7), 0.011, 'WornIron', seg=5)
    B.cyl((px + 0.08, WALL_Y - 0.02, 1.7), (px + 0.08, WALL_Y - 0.02, 2.74), 0.011, 'WornIron', seg=5)
    B.cyl((px + 0.08, WALL_Y - 0.02, 2.74), (PART[0] - 0.02, WALL_Y - 0.02, 2.74), 0.011, 'WornIron', seg=5)


def build_gate(B, coll):
    """The attendance gate: a barred grille (AttGate) in an arched iron frame across the way, the partition over it
    (it winds up into the partition), the school's mark on a roundel over the arch's front, the winding box."""
    gx0, gx1, gy0, gy1, gh = GATE
    p0, p1 = PART
    # posts, front and back, and the threshold
    B.box((p0 + 0.04, p1 - 0.04), (gy0 - 0.1, gy0), (0.0, ARCH[0] + 0.02), 'DepotGreen')
    B.box((p0 + 0.04, p1 - 0.04), (gy1, WALL_Y + WALL_T), (0.0, ARCH[0] + 0.02), 'DepotGreen')
    B.box((gx0 - 0.03, gx1 + 0.03), (gy0, gy1), (-0.004, 0.006), 'Brass')
    # the partition over the arch: plaster, its underside a segmental arch (in y), iron facing round it
    n = 12
    yy = [gy0 + (gy1 - gy0) * k / n for k in range(n + 1)]
    sag = ARCH[1] - ARCH[0]
    zz = [ARCH[0] + sag * (1 - ((2 * (y - gy0) / (gy1 - gy0)) - 1) ** 2) for y in yy]
    for k in range(n):
        B.box((p0, p1), (yy[k], yy[k + 1]), (min(zz[k], zz[k + 1]), CEIL), 'HomePlaster')
    B.box((p0, p1), (gy0 - 0.1, gy0), (ARCH[0] + 0.02, CEIL), 'HomePlaster')
    B.box((p0, p1), (gy1, WALL_Y + WALL_T), (ARCH[0] + 0.02, CEIL), 'HomePlaster')
    for xf in (p0 - 0.004, p1 + 0.004):
        sweep(B.bm, [(xf, y, z - 0.01) for y, z in zip(yy, zz)], 0.022, B('DepotGreen'), seg=5)
    # the roundel on the partition's front end, facing the camera
    mz = 2.2
    B.cyl((GATE_X, gy0 - 0.1, mz), (GATE_X, gy0 - 0.13, mz), 0.21, 'DepotGreen', seg=24)
    B.face_quad((GATE_X, gy0 - 0.132, mz), 0.4, 0.4, (0, -1, 0), 'mark')
    # the winding box on the partition's near face, and its chain into the slot
    B.box((p0 - 0.14, p0), (0.62, 0.98), (2.56, 2.92), 'DepotGreen')
    B.cyl((p0 - 0.07, 0.62, 2.74), (p0 - 0.07, 0.56, 2.74), 0.09, 'DepotGreen', seg=14)
    B.cyl((p0 - 0.07, 0.555, 2.74), (p0 - 0.07, 0.545, 2.74), 0.03, 'Brass', seg=10)
    # The grille: built down (closed), origin at its foot on the lane line; the game raises it 1.3 along +z.
    G = Batch()
    nb = 16
    for k in range(nb + 1):
        y = gy0 + 0.04 + (gy1 - gy0 - 0.08) * k / nb
        G.cyl((GATE_X, y, 0.02), (GATE_X, y, gh), 0.012, 'DepotGreen', seg=6)
    for z in (0.04, 0.8, gh - 0.03):
        G.box((GATE_X - 0.02, GATE_X + 0.02), (gy0 + 0.01, gy1 - 0.01), (z - 0.025, z + 0.025), 'DepotGreen')
    for k in range(nb):                                                         # rings between the low rails
        y = gy0 + 0.04 + (gy1 - gy0 - 0.08) * (k + 0.5) / nb
        add_torus(G.bm, (GATE_X, y, 0.42), (1, 0, 0), 0.032, 0.006, mat=G('DepotGreen'), seg=10, rseg=4)
    for y in (gy0 + 0.25, (gy0 + gy1) / 2, gy1 - 0.25):                         # brass bosses on the mid rail
        G.cyl((GATE_X - 0.026, y, 0.8), (GATE_X + 0.026, y, 0.8), 0.028, 'Brass', seg=10)
    return G.done('AttGate', coll, origin=(GATE_X, 0.0, 0.0))


def build_corridor(B):
    """Past the gate: the corridor to 216 (left open at its end for DL-13's door), the low door to lost property."""
    cy = (CORR_Y, ROOM[2])
    d0, d1, dh = DOOR_S
    xa = PART[1]
    for (x0, x1) in ((xa, d0), (d1, X1)):
        B.box((x0, x1), cy, (0.0, DADO), 'BedroomDado')
        B.box((x0, x1), cy, (DADO, CEIL), 'HomePlaster')
    B.box((d0, d1), cy, (dh, CEIL), 'HomePlaster')
    B.box((xa, d0 - 0.06), (CORR_Y - 0.025, CORR_Y), (DADO - 0.02, DADO + 0.03), 'CrateWood')
    B.box((d1 + 0.06, X1), (CORR_Y - 0.025, CORR_Y), (DADO - 0.02, DADO + 0.03), 'CrateWood')
    B.box((xa, d0 - 0.06), (CORR_Y - 0.02, CORR_Y), (0.0, 0.1), 'CrateWood')
    B.box((d1 + 0.06, X1), (CORR_Y - 0.02, CORR_Y), (0.0, 0.1), 'CrateWood')
    # the low door's frame and its plate
    for x in (d0 - 0.035, d1 + 0.035):
        B.box((x - 0.035, x + 0.035), (CORR_Y - 0.025, CORR_Y), (0.0, dh + 0.06), 'CrateWood')
    B.box((d0 - 0.07, d1 + 0.07), (CORR_Y - 0.025, CORR_Y), (dh, dh + 0.07), 'CrateWood')
    B.box(((d0 + d1) / 2 - 0.14, (d0 + d1) / 2 + 0.14), (CORR_Y - 0.008, CORR_Y), (dh + 0.12, dh + 0.18), 'DepotGreen')
    B.face_quad(((d0 + d1) / 2, CORR_Y - 0.009, dh + 0.15), 0.27, 0.052, (0, -1, 0), 'cplate')
    # the reveal (the wall's thickness round the opening)
    B.box((d0 - 0.002, d0), cy, (0.0, dh), 'HomePlaster')
    B.box((d1, d1 + 0.002), cy, (0.0, dh), 'HomePlaster')
    # a notice board, a stopped clock, a radiator, a stack of small chairs
    B.box((210.62, 211.36), (CORR_Y - 0.03, CORR_Y), (1.1, 1.66), 'CrateWood')
    B.face_quad((210.99, CORR_Y - 0.031, 1.38), 0.68, 0.48, (0, -1, 0), 'cork')
    for (nx, nz, cell, w, h, a) in ((210.82, 1.45, 'notice', 0.22, 0.22, -3), (211.16, 1.5, 'notice2', 0.24, 0.085, 4),
                                     (211.16, 1.3, 'ltag3', 0.12, 0.075, -8)):
        Mn = Matrix.Translation((nx, CORR_Y - 0.033, nz)) @ Matrix.Rotation(math.radians(a), 4, 'Y')
        pts = [Mn @ Vector(p) for p in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]
        B.quad(pts, ATLAS, cell_uv(cell))
    B.cyl((213.6, CORR_Y, 2.35), (213.6, CORR_Y - 0.05, 2.35), 0.17, 'CrateWood', seg=24)
    B.face_quad((213.6, CORR_Y - 0.052, 2.35), 0.3, 0.3, (0, -1, 0), 'clock')
    for k in range(12):
        x = 212.95 + k * 0.085
        B.rbox((0.06, 0.08, 0.6), (x, CORR_Y - 0.06, 0.48), 'WornIron', p=5, cuts=2)
    for z in (0.22, 0.74):
        B.cyl((212.92, CORR_Y - 0.06, z), (213.95, CORR_Y - 0.06, z), 0.016, 'WornIron', seg=6)
    for k in range(3):                                                               # three small chairs, stacked
        z = 0.0 + k * 0.06
        cx, cyy = 215.1, 0.72
        B.box((cx - 0.17, cx + 0.17), (cyy - 0.15, cyy + 0.15), (0.3 + z, 0.325 + z), 'CrateWood')
        B.box((cx - 0.17, cx + 0.17), (cyy + 0.13, cyy + 0.15), (0.45 + z, 0.6 + z), 'CrateWood')
        for sx in (-1, 1):
            for sy in (-1, 1):
                B.cyl((cx + sx * 0.15, cyy + sy * 0.13, z), (cx + sx * 0.15, cyy + sy * 0.13, 0.3 + z), 0.011, 'WornIron', seg=4)
    B.cyl((215.1 - 0.15, 0.72 + 0.13, 0.42), (215.1 - 0.15, 0.72 + 0.13, 0.66), 0.011, 'WornIron', seg=4)
    B.cyl((215.1 + 0.15, 0.72 + 0.13, 0.42), (215.1 + 0.15, 0.72 + 0.13, 0.66), 0.011, 'WornIron', seg=4)


def build_lamps(B):
    """Pendant globes on rods: two lit (AttBulbGlow), the rest dead."""
    for x, lit in ((202.6, False), (205.4, True), (208.3, False), (212.4, True), (214.9, False)):
        B.cyl((x, 0.3, CEIL - 0.22), (x, 0.3, 2.72), 0.008, 'WornIron', seg=4)
        B.cyl((x, 0.3, 2.74), (x, 0.3, 2.69), 0.05, 'Brass', seg=10)
        add_sphere(B.bm, (x, 0.3, 2.6), 0.1, mat=B('AttBulbGlow' if lit else 'DeadBulb'), seg=12)


# =====================================================================================================================
# The lost property room
# =====================================================================================================================

def _thing(B, kind, M, rnd):
    """One lost thing in local coordinates (sitting on z 0, its front to -y), moved by M. Returns its height."""
    if kind == 'mittens':
        for dx in (-0.04, 0.04):
            B.painted('mitten', lambda bm, dx=dx: (rounded_box((0.06, 0.025, 0.085), (dx, 0, 0.0125), p=2.4, cuts=2, bm=bm, mat=0,
                                                               rot=Matrix.Rotation(math.radians(90), 4, 'X')),
                                                   rounded_box((0.022, 0.02, 0.035), (dx + 0.03, -0.02, 0.0125), p=2.4, cuts=2, bm=bm, mat=0)), M)
        return 0.03
    if kind == 'mitten':
        B.painted('mitten', lambda bm: (rounded_box((0.06, 0.085, 0.025), (0, 0, 0.0125), p=2.4, cuts=2, bm=bm, mat=0),
                                        rounded_box((0.022, 0.035, 0.02), (0.03, -0.02, 0.0125), p=2.4, cuts=2, bm=bm, mat=0)), M)
        return 0.03
    if kind == 'shoe':
        B.painted('shoe', lambda bm: (rounded_box((0.065, 0.14, 0.04), (0, 0, 0.02), p=2.6, cuts=2, bm=bm, mat=0),
                                      rounded_box((0.06, 0.07, 0.05), (0, 0.035, 0.045), p=2.6, cuts=2, bm=bm, mat=0)), M)
        return 0.07
    if kind == 'scarf':
        B.painted('scarf', lambda bm: rounded_box((0.15, 0.1, 0.035), (0, 0, 0.0175), p=3.0, cuts=2, bm=bm, mat=0), M)
        return 0.035
    if kind == 'tin':
        B.painted('tin', lambda bm: rounded_box((0.17, 0.11, 0.065), (0, 0, 0.0325), p=8.0, cuts=2, bm=bm, mat=0), M)
        return 0.065
    if kind == 'hat':
        B.painted('hat', lambda bm: (add_sphere(bm, (0, 0, 0.0), 1.0, mat=0, seg=8, scale=(0.075, 0.075, 0.07)),
                                     bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.001], context='VERTS')), M)
        return 0.07
    if kind == 'jumper':
        B.painted('jumper', lambda bm: rounded_box((0.18, 0.15, 0.055), (0, 0, 0.0275), p=2.6, cuts=2, bm=bm, mat=0,
                                                   dents=((0.004, 12.0),), seed=rnd.random()), M)
        return 0.055
    if kind == 'ball':
        B.painted('hat', lambda bm: add_sphere(bm, (0, 0, 0.05), 0.05, mat=0, seg=8), M)
        return 0.1
    if kind == 'case':
        B.painted('leather', lambda bm: add_cyl(bm, (-0.09, 0, 0.025), (0.09, 0, 0.025), 0.025, mat=0, seg=8), M)
        return 0.05
    if kind == 'box':
        cell = 'box%d' % rnd.randrange(8)
        B.painted('card', lambda bm: add_box(bm, (0, 0.0, 0.1), (0.3, 0.28, 0.2), mat=0), M)
        c = M @ Vector((0, -0.141, 0.1))
        nrm = (M.to_3x3() @ Vector((0, -1, 0))).normalized()
        B.face_quad(c, 0.09, 0.09, nrm, cell)
        return 0.2
    return 0.0


def _tag(B, c, normal, k, w=0.09, h=0.056):
    """A brown paper tag hung from the shelf's front edge under its thing, facing out, a little askew."""
    n = Vector(normal)
    side = Vector((0, 0, 1)).cross(n).normalized()
    tilt = Matrix.Rotation(math.radians(((k * 37) % 13) - 6), 3, n)
    pts = [Vector(c) + tilt @ (side * a + Vector((0, 0, b))) for a, b in ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
    B.quad(pts, ATLAS, cell_uv('ltag%d' % (k % 16)))


def build_room(B, rnd):
    x0, x1, y0, y1, zc = ROOM
    T = 0.12
    B.box((x0 - T, x0), (y0, y1 + T), (-0.2, zc + T), 'HomePlaster')
    B.box((x1, x1 + T), (y0, y1 + T), (-0.2, zc + T), 'HomePlaster')
    B.box((x0, x1), (y1, y1 + T), (-0.2, zc), 'HomePlaster')
    B.box((x0 - T, x1 + T), (y0, y1 + T), (zc, zc + T), 'HomePlaster')
    B.box((x0, x1), (y0, y1), (-0.2, -0.004), 'Concrete')
    for k in range(int((y1 - y0) / 0.16)):
        ya = y0 + k * 0.16
        B.box((x0, x1), (ya + 0.003, ya + 0.157), (-0.01, 0.0), 'PigeonWood')
    for (a, b, c, d_) in (((x0, x0 + 0.02), (y0, y1), 0.0, 0.1), ((x1 - 0.02, x1), (y0, y1), 0.0, 0.1), ((x0, x1), (y1 - 0.02, y1), 0.0, 0.1)):
        B.box(a, b, (c, d_), 'CrateWood')
    # The door: open into the room, hinged at its right jamb; the caretaker's coat on its hook.
    d0, d1, dh = DOOR_S
    a = math.radians(DOOR_OPEN)
    Md = Matrix.Translation((d1, y0, 0.0)) @ Matrix.Rotation(-a, 4, 'Z')
    for v in B.box((-(d1 - d0) + 0.01, 0.0), (0.0, 0.035), (0.0, dh - 0.01), 'CrateWood'):
        v.co = Md @ v.co
    for (zz0, zz1) in ((0.12, 0.6), (0.7, dh - 0.12)):
        for v in B.box((-(d1 - d0) + 0.09, -0.08), (0.035, 0.045), (zz0, zz1), 'CrateWood'):
            v.co = Md @ v.co
    hook = Md @ Vector((-(d1 - d0) / 2, 0.075, dh - 0.12))
    B.cyl(Md @ Vector((-(d1 - d0) / 2, 0.035, dh - 0.12)), hook, 0.007, 'Brass', seg=5)
    nrm = (Md.to_3x3() @ Vector((0, 1, 0))).normalized()
    turn = math.degrees(math.atan2(nrm.y, nrm.x)) - math.degrees(math.atan2(-1, 0))
    Mc = Matrix.Translation(hook + Vector((0, 0, 0.01))) @ Matrix.Rotation(math.radians(turn), 4, 'Z') @ Matrix.Translation((0, -0.065, 0))
    B.painted('coatK', lambda bm: coat_body(bm, s=1.75, hanger=False, hood=False, wide=1.05, length=1.08), Mc)
    # Shelves on the left wall and the back wall's left half: lost things in rows, each tagged.
    kinds = ['mittens', 'mitten', 'shoe', 'scarf', 'tin', 'hat', 'jumper', 'ball', 'case', 'shoe', 'mitten', 'scarf']
    k_tag = 0
    shelf_z = (0.32, 0.72, 1.12, 1.52, 1.92)
    # back wall
    bx0, bx1, by0 = x0 + 0.05, 212.6, y1 - 0.32
    for x in (bx0, (bx0 + bx1) / 2, bx1):
        B.box((x - 0.015, x + 0.015), (by0, y1), (0.0, 2.1), 'CrateWood')
    for z in shelf_z:
        B.box((bx0, bx1), (by0, y1), (z - 0.022, z), 'CrateWood')
    # left wall
    lx0, lx1, ly0, ly1 = x0, x0 + 0.32, 1.95, by0 - 0.01
    for y in (ly0, (ly0 + ly1) / 2, ly1):
        B.box((lx0, lx1), (y - 0.015, y + 0.015), (0.0, 2.1), 'CrateWood')
    for z in shelf_z:
        B.box((lx0, lx1), (ly0, ly1), (z - 0.022, z), 'CrateWood')
    # the things: rows along each shelf (the top shelves: boxes by the week)
    for si, z in enumerate(shelf_z):
        if si == 4:
            x = bx0 + 0.2
            while x < bx1 - 0.15:
                _thing(B, 'box', M_at(x, by0 + 0.16, z, rnd.uniform(-3, 3)), rnd)
                x += 0.34
            y = ly0 + 0.2
            while y < ly1 - 0.15:
                _thing(B, 'box', M_at(lx0 + 0.16, y, z, -90 + rnd.uniform(-3, 3)), rnd)
                y += 0.34
            continue
        S = Matrix.Diagonal((1.3, 1.3, 1.3, 1.0))
        x = bx0 + 0.15
        while x < bx1 - 0.12:
            kind = kinds[rnd.randrange(len(kinds))]
            if si == 2 and abs(x - 212.25) < 0.14:
                kind = 'tin'                                    # M.D.'s lunch tin, at eye level, toward the desk
            M = M_at(x, by0 + 0.15 + rnd.uniform(-0.02, 0.02), z, rnd.uniform(-10, 10)) @ S
            _thing(B, kind, M, rnd)
            _tag(B, (x, by0 - 0.004, z - 0.05), (0, -1, 0), 15 if kind == 'tin' and si == 2 else k_tag)
            k_tag += 1
            x += 0.27 + rnd.uniform(0, 0.03)
        y = ly0 + 0.15
        while y < ly1 - 0.12:
            kind = kinds[rnd.randrange(len(kinds))]
            M = M_at(lx0 + 0.16 + rnd.uniform(-0.02, 0.02), y, z, -90 + rnd.uniform(-10, 10)) @ S
            _thing(B, kind, M, rnd)
            _tag(B, (lx1 + 0.004, y, z - 0.05), (1, 0, 0), k_tag)
            k_tag += 1
            y += 0.27 + rnd.uniform(0, 0.03)
    # The caretaker's desk: the register open (one tick on the last page), the older volumes, a lamp, a mug, keys.
    dx0, dx1, dy0, dy1, dt = DESK
    B.box((dx0, dx1), (dy0, dy1), (dt - 0.035, dt), 'CrateWood')
    for x in (dx0 + 0.04, dx1 - 0.04):
        for y in (dy0 + 0.04, dy1 - 0.04):
            B.box((x - 0.025, x + 0.025), (y - 0.025, y + 0.025), (0.0, dt - 0.035), 'CrateWood')
    B.box((dx1 - 0.42, dx1 - 0.03), (dy0 + 0.02, dy1 - 0.02), (0.08, dt - 0.035), 'CrateWood')            # the drawers
    for z in (0.22, 0.42, 0.6):
        B.box((dx1 - 0.25, dx1 - 0.19), (dy0 + 0.005, dy0 + 0.02), (z - 0.01, z + 0.01), 'Brass')
    rx, ry = 213.22, 3.2
    for s in (-1, 1):                                                            # the register's covers and its two pages
        B.painted('leather', lambda bm, s=s: add_box(bm, (s * 0.125, 0, 0.006), (0.25, 0.34, 0.012), mat=0), M_at(rx, ry, dt, 4))
    Mr = M_at(rx, ry, dt + 0.014, 4)
    for s, cell in ((-1, 'regL'), (1, 'regR')):
        tilt = Matrix.Rotation(math.radians(-s * 5), 4, 'Y')
        pts = [Mr @ tilt @ Vector(p) for p in ((0, -0.16, 0), (s * 0.235, -0.16, 0), (s * 0.235, 0.16, 0), (0, 0.16, 0))]
        if s < 0:
            pts = [pts[1], pts[0], pts[3], pts[2]]
        B.quad(pts, ATLAS, cell_uv(cell))
    B.cyl((rx + 0.12, ry - 0.21, dt + 0.006), (rx + 0.24, ry - 0.24, dt + 0.006), 0.005, 'WornIron', seg=5)     # his pen
    for k in range(5):                                                           # the old registers, stacked
        z = dt + k * 0.045
        Mk = M_at(dx1 - 0.17, dy1 - 0.19, z, rnd.uniform(-4, 4))
        B.painted('leather', lambda bm: add_box(bm, (0, 0, 0.0215), (0.26, 0.34, 0.043), mat=0), Mk)
        c = Mk @ Vector((0, -0.171, 0.0215))
        B.face_quad(c, 0.08, 0.04, (Mk.to_3x3() @ Vector((0, -1, 0))).normalized(), 'spine%d' % k)
    lx, ly = 213.08, dy1 - 0.07                                                  # the lamp (lit: AttBulbGlow)
    B.cyl((lx, ly, dt), (lx, ly, dt + 0.02), 0.07, 'DepotGreen', seg=12)
    sweep(B.bm, [(lx, ly, dt + 0.02), (lx, ly, dt + 0.26), (lx - 0.06, ly - 0.07, dt + 0.4)], 0.008, B('DepotGreen'), seg=5)
    B.cyl((lx - 0.06, ly - 0.07, dt + 0.43), (lx - 0.1, ly - 0.13, dt + 0.32), 0.03, 'DepotGreen', r2=0.085, seg=14)
    add_sphere(B.bm, (lx - 0.097, ly - 0.125, dt + 0.33), 0.026, mat=B('AttBulbGlow'), seg=10)
    B.cyl((dx1 - 0.1, dy0 + 0.1, dt), (dx1 - 0.1, dy0 + 0.1, dt + 0.09), 0.04, 'DepotGreen', seg=10)      # his mug
    add_torus(B.bm, (dx1 - 0.055, dy0 + 0.1, dt + 0.045), (0, 1, 0), 0.022, 0.006, mat=B('DepotGreen'), seg=8, rseg=4)
    for k in range(4):                                                           # his keys, on a ring
        add_torus(B.bm, (dx1 - 0.3 + k * 0.025, dy0 + 0.07, dt + 0.004), (0, 0, 1), 0.012, 0.0025, mat=B('Brass'), seg=6, rseg=3)
    add_torus(B.bm, (dx1 - 0.27, dy0 + 0.07, dt + 0.004), (0, 0, 1), 0.035, 0.003, mat=B('Brass'), seg=12, rseg=3)
    # his chair, pulled out and turned toward the door, as if he had just got up
    cx, cy, ca = 213.95, 2.55, -45.0
    R = Matrix.Rotation(math.radians(ca), 4, 'Z')
    C = Vector((cx, cy, 0))
    for v in B.box((-0.21, 0.21), (-0.2, 0.2), (0.43, 0.46), 'CrateWood'):
        v.co = C + R @ v.co
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = C + R @ Vector((sx * 0.18, sy * 0.17, 0))
            q = C + R @ Vector((sx * 0.18, sy * 0.17, 0.43 if sy < 0 else 0.92))
            B.cyl(p, q, 0.016, 'CrateWood', seg=6)
    for z in (0.7, 0.86):
        for v in B.box((-0.18, 0.18), (0.155, 0.185), (z - 0.03, z + 0.03), 'CrateWood'):
            v.co = C + R @ v.co
    # a broom and a bucket in the right corner, his ceiling bulb (dead)
    B.cyl((x1 - 0.12, y1 - 0.5, 0.0), (x1 - 0.04, y1 - 0.52, 1.25), 0.013, 'CrateWood', seg=6)
    B.rbox((0.28, 0.07, 0.12), (x1 - 0.13, y1 - 0.5, 0.06), 'CrateWood', p=3, cuts=3)
    B.cyl((x1 - 0.3, y0 + 0.5, 0.0), (x1 - 0.3, y0 + 0.5, 0.26), 0.13, 'WornIron', r2=0.15, seg=14)
    B.cyl((212.8, 2.4, zc), (212.8, 2.4, zc - 0.3), 0.005, 'WornIron', seg=4)
    add_sphere(B.bm, (212.8, 2.4, zc - 0.34), 0.03, mat=B('DeadBulb'), seg=8)



# =====================================================================================================================
# The layers of time (the director's lore): the order era's motto and rules, the protective era's notice and headcount
# =====================================================================================================================
LW, LH = 1024, 256
LCELLS = {
    'motto': (0, 0, 1024, 72),          # ORDER ABOVE ALL, painted on the plaster, half painted over
    'rules': (0, 72, 320, 256),         # the order era's enamel rules board
    'safety': (320, 72, 576, 256),      # the protective era's notice, newer and brighter
    'headcount': (576, 72, 832, 256),   # the roll, in chalk: 214 ... 1
}


def lore_uv(cell):
    x0, y0, x1, y1 = LCELLS[cell]
    return x0 / LW, 1 - y1 / LH, x1 / LW, 1 - y0 / LH


def make_lore(path):
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(1213)
    img = Image.new('RGB', (LW, LH), (60, 56, 50))
    d = ImageDraw.Draw(img, 'RGBA')
    # The motto: big stencilled capitals in old oxide paint on a dark band, and over the right half a later coat of
    # cream, brushed on in strokes, the letters ghosting through it.
    x0, y0, x1, y1 = LCELLS['motto']
    _noise_fill(img, LCELLS['motto'], (122, 108, 84), 8, 91)
    d.rectangle((x0, y0 + 4, x1, y0 + 8), fill=(70, 52, 40, 160))
    d.rectangle((x0, y1 - 8, x1, y1 - 4), fill=(70, 52, 40, 160))
    d.text(((x0 + x1) / 2, (y0 + y1) / 2 + 2), 'ORDER   ABOVE   ALL', font=_font(66, 'serif'), fill=(66, 40, 30), anchor='mm')
    over = Image.new('RGBA', (LW, LH), (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    xa = 520
    for k in range(40):                                                     # brush strokes, ragged at the left edge
        yy = y0 + k * 1.8
        xs = xa + rnd.uniform(-40, 30) + 18 * math.sin(k * 0.7)
        od.line((xs, yy, x1, yy + rnd.uniform(-1, 1)), fill=(150, 138, 112, rnd.randint(120, 170)), width=3)
    img.paste(over, (0, 0), over)
    # The rules board: enamel, the school's green, cream capitals.
    x0, y0, x1, y1 = LCELLS['rules']
    cream, green = (214, 204, 176), (36, 60, 46)
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(24, 34, 28))
    d.rounded_rectangle((x0 + 4, y0 + 4, x1 - 5, y1 - 5), radius=10, fill=green, outline=cream, width=4)
    d.text(((x0 + x1) / 2, y0 + 26), 'RULES', font=_font(30), fill=cream, anchor='mm')
    d.line((x0 + 40, y0 + 44, x1 - 40, y0 + 44), fill=cream, width=2)
    for k, line in enumerate(('PUPILS WILL FORM', 'ONE LINE', 'AND WAIT IN SILENCE', 'ORDER ABOVE ALL')):
        d.text(((x0 + x1) / 2, y0 + 70 + k * 30), line, font=_font(26 if k < 3 else 20), fill=cream, anchor='mm')
    for _ in range(14):                                                     # chips in the enamel
        cx, cy = rnd.uniform(x0 + 6, x1 - 6), rnd.uniform(y0 + 6, y1 - 6)
        d.ellipse((cx - 3, cy - 2, cx + 3, cy + 2), fill=(18, 18, 16))
    # The safety notice: newer, printed, pale yellow, a black border; worded anxiously.
    x0, y0, x1, y1 = LCELLS['safety']
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(222, 200, 92))
    d.rectangle((x0 + 6, y0 + 6, x1 - 7, y1 - 7), outline=(26, 24, 20), width=5)
    d.text(((x0 + x1) / 2, y0 + 30), 'NOTICE', font=_font(30), fill=(26, 24, 20), anchor='mm')
    for k, line in enumerate(('PROTECTED PUPILS', 'MUST REMAIN WITH', 'AN ATTENDANT', 'AT ALL TIMES')):
        d.text(((x0 + x1) / 2, y0 + 70 + k * 27), line, font=_font(23), fill=(26, 24, 20), anchor='mm')
    # The headcount board: a slate in a wooden frame, ON ROLL painted, the chalk numbers crossed out, each one smaller.
    x0, y0, x1, y1 = LCELLS['headcount']
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(92, 66, 40))
    _noise_fill(img, (x0 + 8, y0 + 8, x1 - 8, y1 - 8), (34, 40, 36), 10, 92)
    d.text(((x0 + x1) / 2, y0 + 24), 'ON ROLL', font=_font(24), fill=(200, 192, 164), anchor='mm')
    chalk = (206, 204, 194, 220)
    rows = [('214', 40, 64, 60), ('160', 36, 150, 58), ('97', 32, 66, 106), ('31', 28, 140, 104), ('9', 24, 196, 98),
            ('4', 20, 70, 144), ('1', 15, 128, 146)]
    for k, (txt, size, tx, ty) in enumerate(rows):
        d.text((x0 + tx, y0 + ty), txt, font=_font(size, 'hand'), fill=chalk, anchor='mm')
        if txt != '1':
            w = size * 0.32 * len(txt) + 6
            d.line((x0 + tx - w, y0 + ty + 4, x0 + tx + w, y0 + ty - 5), fill=chalk, width=2)
    for _ in range(30):                                                     # old chalk dust and smears
        cx, cy = rnd.uniform(x0 + 10, x1 - 10), rnd.uniform(y0 + 40, y1 - 10)
        d.ellipse((cx - 8, cy - 3, cx + 8, cy + 3), fill=(200, 200, 190, 18))
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.quantize(96, method=Image.Quantize.MEDIANCUT).save(path, optimize=True)


def build_lore(B):
    """Static dressing only: the motto high over the frieze, the rules board by the door, the safety notice on the
    gate's front post, the headcount board on the corridor wall just past the gate."""
    yf = WALL_Y - 0.003
    B.quad([(201.98, yf, 2.72), (207.6, yf, 2.72), (207.6, yf, 2.96), (201.98, yf, 2.96)], LORE, lore_uv('motto'))   # the lit globe in the gap after ABOVE
    B.box((201.36, 201.96), (WALL_Y - 0.02, WALL_Y), (2.36, 2.79), 'DepotGreen')
    B.quad([(201.38, WALL_Y - 0.021, 2.38), (201.94, WALL_Y - 0.021, 2.38), (201.94, WALL_Y - 0.021, 2.77),
            (201.38, WALL_Y - 0.021, 2.77)], LORE, lore_uv('rules'))
    gy0 = GATE[2] - 0.1
    B.box((GATE_X - 0.17, GATE_X + 0.17), (gy0 - 0.012, gy0), (1.12, 1.5), 'WornIron')
    B.quad([(GATE_X - 0.16, gy0 - 0.013, 1.13), (GATE_X + 0.16, gy0 - 0.013, 1.13), (GATE_X + 0.16, gy0 - 0.013, 1.49),
            (GATE_X - 0.16, gy0 - 0.013, 1.49)], LORE, lore_uv('safety'))
    B.box((209.78, 210.46), (CORR_Y - 0.03, CORR_Y), (1.08, 1.6), 'CrateWood')
    B.quad([(209.8, CORR_Y - 0.031, 1.1), (210.44, CORR_Y - 0.031, 1.1), (210.44, CORR_Y - 0.031, 1.58),
            (209.8, CORR_Y - 0.031, 1.58)], LORE, lore_uv('headcount'))
    B.box((209.8, 210.44), (CORR_Y - 0.07, CORR_Y - 0.03), (1.06, 1.08), 'CrateWood')        # its chalk ledge
    for k, dx in enumerate((0.12, 0.2)):
        B.box((209.8 + dx, 209.8 + dx + 0.05), (CORR_Y - 0.06, CORR_Y - 0.045), (1.08, 1.094), 'HomePlaster')

# =====================================================================================================================
# Voice props (art/common/voice_props.py)
# =====================================================================================================================
SPEAKER = (209.0, WALL_Y, 2.32)             # the gate's speaker, on the back wall over the lamp post, facing the camera
CARD_PLAYER = (212.84, 3.2, DESK[4])       # the caretaker's card player, on his desk


def _vp():
    import sys
    if not os.path.exists(os.path.join(COMMON, 'VOICE_PROPS_READY')):
        return None
    if COMMON not in sys.path:
        sys.path.insert(0, COMMON)
    import voice_props
    return voice_props


def place_voice_props(B):
    """The gate's speaker and the caretaker's card player (the shared props), merged into B. Returns their info."""
    VP = _vp()
    if VP is None:
        print('dl12: VOICE_PROPS_READY not there yet: no speaker or card player placed')
        return {}
    spk = VP.tannoy(B, VP.xform(SPEAKER), tilt=22.0, aim=-12.0, conduit=0.5, conduit_dir=90.0, cable=False)
    ply = VP.card_player(B, VP.xform(CARD_PLAYER, turn=30.0), lid='closed', horn=-40.0, card=True)
    return {'speaker': spk, 'player': ply}


# =====================================================================================================================

def build_set(dl01, m, coll):
    if not os.path.exists(ATLAS_PATH) or os.environ.get('DL12_RETEX'):
        make_atlas(ATLAS_PATH)
    if not os.path.exists(LORE_PATH) or os.environ.get('DL12_RETEX'):
        make_lore(LORE_PATH)
    rnd = random.Random(1201)
    B = Batch()
    def step(label, fn, *a):
        n0 = sum(len(f.verts) - 2 for f in B.bm.faces)
        out = fn(*a)
        print('dl12: %-12s %6d tris' % (label, sum(len(f.verts) - 2 for f in B.bm.faces) - n0))
        return out
    step('shell', build_shell, B)
    step('hooks', build_hooks, B, rnd)
    step('bin', build_bin, B)
    step('rack', build_rack, B)
    step('bench', build_bench, B)
    step('peg7', build_peg7, B, coll)
    step('strip+post', build_strip_and_post, B, coll)
    gate = step('gate', build_gate, B, coll)
    step('corridor', build_corridor, B)
    step('lamps', build_lamps, B)
    step('room', build_room, B, rnd)
    step('lore', build_lore, B)
    props = step('voice props', place_voice_props, B)
    static = B.done('AttCloakroom', coll)
    # The free pupil model, on the lane between the bench and the strip; the stand's metal is handled bright.
    F = Batch()
    figure(F, M_at(FIGURE[0], FIGURE[1], 0.0, -6.0), stand='HandledSteel', pose={'head': (4, -10), 'left': 6, 'right': 2})
    fig = F.done('AttFigure', coll, origin=(FIGURE[0], FIGURE[1], 0.0))
    # The coat: built hanging on its hanger (origin at the inside top of the hook); placed as found, laid along x on the bin.
    C = Batch()
    C.painted('coatM', lambda bm: coat_body(bm, s=1.0, hanger=True, hood=True))
    C.painted('wood', lambda bm: hanger_bar(bm))
    C.painted('brass', hanger_hook)
    coat = C.done('AttCoat', coll, origin=(0.0, 0.0, 0.0))
    coat.rotation_mode = 'XYZ'
    coat.rotation_euler = (math.radians(-90), 0.0, math.radians(-90))
    coat.location = COAT_REST
    bpy.context.view_layer.update()
    total, calls = 0, 0
    for ob in [static, fig, gate, coat] + [bpy.data.objects.get(n) for n in ('AttLampPresent', 'AttLampCoat', 'AttPegLamp')]:
        t = tri_count(ob)
        total += t
        calls += len(ob.data.materials)
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        print('dl12: %-15s tris %6d  mats %2d  x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f  %s' % (
            ob.name, t, len(ob.data.materials), min(v.x for v in bb), max(v.x for v in bb), min(v.y for v in bb),
            max(v.y for v in bb), min(v.z for v in bb), max(v.z for v in bb), [mm.name for mm in ob.data.materials]))
    print('dl12: total tris %d, draw calls %d' % (total, calls))
    for k, info in props.items():
        print('dl12: voice prop %s %s' % (k, {a: (tuple(round(float(c), 3) for c in b) if isinstance(b, Vector) else b) for a, b in info.items() if not isinstance(b, Matrix)}))
