"""Chapter 1, pass 4 (docs/chapter1_pass4_plan.md): story_ringc. Built in FINAL world x, after the pass 3 modules.

DL-10 Up Only, "the crush" (sections 3 and 4): the lift lobby after the last car went.
  UOShoes       shoes by the hundred: along the queue line in front of the lane, heaped against the lift front either
                side of the gate, under the bench, strays on the porch, a few fallen to ring C's landing at the
                shaft's foot. A few shoe meshes, baked into one static object (one node, three materials: see below).
                The lane (|y| < 0.25), the car's doorway, the UP button's and the crank's stands and the service
                door's path are kept clear.
  UOBarrier     the queue's barrier: steel posts bolted along the line's front edge, every one bent flat toward the
                lift, the rail between them crushed and lying on the deck, its end hanging over the deck's edge.
  UOLastCar     LAST CAR on an enamel board, hanging from one hook under the gate's head (the other hook bare, a
                snapped chain on it). Origin at the hook it hangs from; static (the game may sway it about Blender
                +y, game -z, a degree or two).
  UOHandMarks   hand marks, pale with dust, smeared down the lift front either side of the gate, on the gate's
                architrave, and down the counterweight shaft's back wall (seen as the counterweight goes down);
                fingernail scratches by the gate. One decal object.
  WayRingC10    RING C and an arrow down-and-on, stencilled on the counterweight shaft's back wall over the
                counterweight: the way on is down.
DL-11 ring C:
  WayC114       "C-114 ->" painted on the barricade's face over the gap he crouches through.

The atlas (art/pass4/textures/ringc_story.png, RingCStoryMat, alpha: a decal in the game) holds the board, the hand
marks, the scratches and both way marks. The DL-10 echoes of earlier puzzles (the balance gauge, the plate's lamps)
are built with the lift in art/pass3/build_up_only.py; DL-11's drowning (the high-water line, the raft, the pram, the
White's lair) with the street in art/dl05/build_dl05.py.

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y. Game (x, y, z) = (x, z, -y).
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
from build_d17 import add_box, add_cyl, add_torus, worn_material, simple_material
import build_up_only as uo

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
ATLAS = os.path.join(TEX, 'ringc_story.png')

DECK = uo.DECK
# Atlas rects (pixels, y down).
R_LAST = (0, 0, 768, 256)             # the LAST CAR board (0.84 x 0.28)
R_SCR = (768, 0, 1024, 256)           # fingernail scratches (0.3 x 0.3)
R_HAND_A = (0, 256, 256, 1024)        # hands sliding down a wall (0.33 x 1.0)
R_HAND_B = (256, 256, 512, 1024)      # ... another run of them
R_RING = (512, 256, 1024, 768)        # RING C and the arrow down-and-on, stencilled (0.62 x 0.62)
R_C114 = (512, 768, 1024, 1024)       # C-114 and an arrow, painted (0.62 x 0.31)

# Where things go (Blender world).
STENCIL10 = (127.3, uo.SHAFT_BACK - 0.014, 3.45, 0.62)     # WayRingC10: centre x, y, z, size (over the counterweight)
C114_MARK = (134.6, -0.557, 0.84, 0.6, 0.3)                 # WayC114: centre x, y, z, w, h (the barricade's face)
LASTCAR_HOOK = (124.62, 0.288, uo.DECK + uo.GATE[2])        # the hook it hangs from, under the gate's head
LASTCAR_HOOK2 = 125.28                                      # the bare hook, its chain snapped
LASTCAR_TILT = 64.0                                         # degrees, its free end down (about Blender +y)


def _rz(a):
    return Matrix.Rotation(a, 4, 'Z')


def _rx(a):
    return Matrix.Rotation(a, 4, 'X')


def _ry(a):
    return Matrix.Rotation(a, 4, 'Y')


# =====================================================================================================================
# The atlas
# =====================================================================================================================

def _font(size, kind='bold'):
    from PIL import ImageFont
    for path in ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'):
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    return ImageFont.load_default()


def _fit(text, width, size):
    """The bold font at the largest size up to `size` that sets `text` within `width` pixels."""
    while size > 8 and _font(size).getlength(text) > width:
        size -= 2
    return _font(size)


def _noise(w, h, cells, seed):
    """Smooth value noise in [0, 1]."""
    import numpy as np
    from PIL import Image
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp, tot = 1.0, 0.0
    for o in range(3):
        c = cells * 2 ** o
        lat = rng.random((max(2, int(c * h / w) + 2), c + 2))
        img = Image.fromarray((lat * 255).astype('uint8')).resize((w, h), Image.BICUBIC)
        out += amp * np.asarray(img) / 255.0
        tot += amp
        amp *= 0.5
    return out / tot


def _stencil_glyphs(text, font, gap):
    """Each glyph as an 'L' mask, cut by stencil bridges: through the bowls of C, G, O at their middle, between the
    stem and the rest of R, B, P, D, between the stems and the diagonal of N. Returns [(mask, advance)]."""
    import numpy as np
    from PIL import Image, ImageDraw
    out = []
    for ch in text:
        l, t, r, b = font.getbbox(ch)
        adv = font.getlength(ch)
        if ch == ' ' or r <= l:
            out.append((None, adv))
            continue
        w, h = r - l + 8, b - t + 8
        im = Image.new('L', (w, h), 0)
        ImageDraw.Draw(im).text((4 - l, 4 - t), ch, font=font, fill=255)
        a = np.asarray(im).astype(float)
        cols = (a > 128).sum(axis=0) / max(1.0, (a > 128).sum(axis=0).max())
        cuts = []
        if ch in 'CGOQ':
            cuts.append(w // 2)
        if ch in 'RBPDN':                                  # just right of the left stem
            k = 0
            while k < w and cols[k] < 0.85:
                k += 1
            while k < w and cols[k] >= 0.85:
                k += 1
            cuts.append(k + gap // 2)
        if ch in 'N':                                      # just left of the right stem
            k = w - 1
            while k > 0 and cols[k] < 0.85:
                k -= 1
            while k > 0 and cols[k] >= 0.85:
                k -= 1
            cuts.append(k - gap // 2)
        if ch == '4':
            cuts.append(int(w * 0.6))
        for c in cuts:
            a[:, max(0, c - gap // 2):c + (gap + 1) // 2] = 0
        out.append((Image.fromarray(a.astype('uint8')), adv))
    return out


def _paint_layer(mask, color, seed, wear=0.35, spray=True):
    """A mask turned into worn paint: overspray round the edges, patchy coverage, flakes, a few runs."""
    import numpy as np
    from PIL import Image, ImageFilter
    rnd = random.Random(seed)
    w, h = mask.size
    m = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.1))).astype(float) / 255.0
    if spray:
        halo = np.asarray(mask.filter(ImageFilter.GaussianBlur(5))).astype(float) / 255.0
        m = np.maximum(m, halo * 0.22)
    n = _noise(w, h, 9, seed)
    n2 = _noise(w, h, 40, seed + 1)
    keep = np.clip(1.0 - wear * 1.6 * np.clip(n - 0.42, 0, 1) - 0.35 * np.clip(n2 - 0.62, 0, 1) * 3, 0.15, 1.0)
    a = m * keep
    # Runs below the heavier strokes.
    src = np.asarray(mask).astype(float) / 255.0
    for _ in range(int(w * h / 9000)):
        x = rnd.randrange(w)
        col = np.where(src[:, x] > 0.5)[0]
        if not len(col):
            continue
        y0 = col.max()
        ln = rnd.randint(6, 34)
        for y in range(y0, min(h, y0 + ln)):
            a[y, x] = max(a[y, x], 0.7 * (1 - (y - y0) / ln))
            if x + 1 < w:
                a[y, x + 1] = max(a[y, x + 1], 0.45 * (1 - (y - y0) / ln))
    rgba = np.zeros((h, w, 4))
    rgba[..., :3] = color
    rgba[..., 3] = np.clip(a, 0, 1) * 255
    return Image.fromarray(rgba.astype('uint8'), 'RGBA')


def _hand_mask(size, ang, spread=1.0):
    """A hand print (fingers up), as an 'L' mask `size` px tall, turned by ang degrees."""
    from PIL import Image, ImageDraw
    s = size
    im = Image.new('L', (int(s * 1.4), int(s * 1.4)), 0)
    d = ImageDraw.Draw(im)
    cx, cy = s * 0.7, s * 0.9
    d.ellipse((cx - s * 0.24, cy - s * 0.22, cx + s * 0.24, cy + s * 0.26), fill=255)             # the palm
    for k, (dx, ln, a) in enumerate(((-0.17, 0.4, -14), (-0.06, 0.48, -4), (0.06, 0.46, 4), (0.16, 0.36, 13))):
        a = math.radians(a * spread)
        bx, by = cx + dx * s, cy - s * 0.12
        tx, ty = bx + math.sin(a) * ln * s, by - math.cos(a) * ln * s
        d.line((bx, by, tx, ty), fill=255, width=int(s * 0.1))
        d.ellipse((tx - s * 0.05, ty - s * 0.05, tx + s * 0.05, ty + s * 0.05), fill=255)
    tb = (cx - s * 0.22, cy + s * 0.02)
    tt = (tb[0] - s * 0.22, tb[1] - s * 0.2)
    d.line((*tb, *tt), fill=255, width=int(s * 0.11))
    d.ellipse((tt[0] - s * 0.055, tt[1] - s * 0.055, tt[0] + s * 0.055, tt[1] + s * 0.055), fill=255)
    return im.rotate(ang, resample=Image.BICUBIC)


def _hands(w, h, seed, n):
    """Hand marks in dust on a dark wall: some pressed flat, most dragged down, fingertips leaving streaks."""
    import numpy as np
    from PIL import Image, ImageChops, ImageDraw, ImageFilter
    rnd = random.Random(seed)
    acc = Image.new('L', (w, h), 0)
    for k in range(n):
        size = rnd.uniform(118, 140)
        hm = _hand_mask(int(size), rnd.uniform(-22, 22), rnd.uniform(0.7, 1.3))
        if rnd.random() < 0.5:
            hm = hm.transpose(Image.FLIP_LEFT_RIGHT)                     # left and right hands
        hw_, hh_ = hm.size
        x = rnd.uniform(-hw_ * 0.25, w - hw_ * 0.75)
        y0 = rnd.uniform(-hh_ * 0.2, h * 0.55)
        slide = rnd.choice((0, 0, 0.12, 0.25, 0.4)) * h * rnd.uniform(0.6, 1.0)
        steps = max(1, int(slide / 6))
        for j in range(steps + 1):
            t = j / steps
            yy = y0 + slide * t
            xx = x + rnd.uniform(-1.5, 1.5) + 8 * math.sin(t * 2.0 + k)
            strength = (0.07 + 0.13 * t) if slide else 1.0                 # heavier where the hand stopped
            stamp = hm.point(lambda v, s_=strength: int(v * s_))
            layer = Image.new('L', (w, h), 0)
            layer.paste(stamp, (int(xx), int(yy)))
            acc = ImageChops.lighter(acc, layer)
        if slide:                                                       # the last print, pressed
            layer = Image.new('L', (w, h), 0)
            layer.paste(hm.point(lambda v: int(v * 0.85)), (int(x), int(y0 + slide)))
            acc = ImageChops.lighter(acc, layer)
    a = np.asarray(acc.filter(ImageFilter.GaussianBlur(1.6))).astype(float) / 255.0
    n = _noise(w, h, 12, seed + 7)
    a = a * np.clip(0.55 + 0.6 * (n - 0.3), 0.3, 1.0) * 0.72
    rgba = np.zeros((h, w, 4))
    rgba[..., 0], rgba[..., 1], rgba[..., 2] = 162, 152, 130
    rgba[..., 3] = np.clip(a, 0, 1) * 255
    return Image.fromarray(rgba.astype('uint8'), 'RGBA')


def _scratches(w, h, seed):
    """Fingernail scratches through the paint by the gate: bunches of three or four, mostly downward."""
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(seed)
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for _ in range(9):
        x0, y0 = rnd.uniform(10, w - 40), rnd.uniform(0, h * 0.5)
        ln = rnd.uniform(0.35, 0.9) * h
        ang = math.radians(rnd.uniform(-14, 14))
        bend = rnd.uniform(-10, 10)
        for f in range(rnd.choice((3, 4, 4))):
            ox = f * rnd.uniform(9, 13)
            pts = []
            for k in range(9):
                t = k / 8
                pts.append((x0 + ox + math.sin(ang) * ln * t + bend * t * t, y0 + math.cos(ang) * ln * t * (1 - 0.1 * f)))
            d.line([(px + 2, py + 1) for px, py in pts], fill=(20, 18, 16, 120), width=4)
            d.line(pts, fill=(196, 190, 172, 215), width=4)
    return im.filter(ImageFilter.GaussianBlur(0.6))


def _arrow_mask(w, h, gap):
    """A thick arrow down-and-on (to the lower right), stencilled: the head cut from the shaft."""
    from PIL import Image, ImageDraw
    im = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(im)
    a, b = Vector((w * 0.18, h * 0.12)), Vector((w * 0.66, h * 0.6))
    dv = (b - a).normalized()
    nv = Vector((-dv.y, dv.x))
    sw = w * 0.085
    d.polygon([tuple(a + nv * sw), tuple(b + nv * sw), tuple(b - nv * sw), tuple(a - nv * sw)], fill=255)
    tip = Vector((w * 0.88, h * 0.82))
    hb = b - dv * (gap * 0.5)
    d.polygon([tuple(tip), tuple(hb + dv * gap + nv * w * 0.26), tuple(hb + dv * gap - nv * w * 0.26)], fill=255)
    return im


def make_atlas():
    from PIL import Image, ImageDraw, ImageFilter
    import numpy as np
    os.makedirs(TEX, exist_ok=True)
    img = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0))
    cream, green, ink = (214, 204, 176), (28, 52, 40), (20, 18, 16)
    paint = (224, 218, 198)

    # LAST CAR: an enamel board, cream on green with a border, chipped to black iron at the edges and screw holes.
    x0, y0, x1, y1 = R_LAST
    board = Image.new('RGBA', (x1 - x0, y1 - y0), (*green, 255))
    d = ImageDraw.Draw(board)
    d.rectangle((10, 10, x1 - x0 - 11, y1 - y0 - 11), outline=(*cream, 255), width=9)
    f = _fit('LAST CAR', x1 - x0 - 90, 140)
    l, t, r, b = d.textbbox((0, 0), 'LAST CAR', font=f)
    d.text(((x1 - x0 - (r - l)) / 2 - l, (y1 - y0 + 40 - (b - t)) / 2 - t), 'LAST CAR', font=f, fill=(*cream, 255))
    f2 = _font(30)
    l, t, r, b = d.textbbox((0, 0), 'RING C  ·  UP', font=f2)
    d.text(((x1 - x0 - (r - l)) / 2 - l, 34 - t), 'RING C  ·  UP', font=f2, fill=(*cream, 255))
    rnd = random.Random(4101)
    for x, y in ((34, 34), (x1 - x0 - 34, 34)):                     # the eyes it hung by
        d.ellipse((x - 12, y - 12, x + 12, y + 12), fill=(*ink, 255))
    for _ in range(26):                                             # chips to the iron
        ex = rnd.choice((rnd.uniform(0, 30), rnd.uniform(x1 - x0 - 30, x1 - x0), rnd.uniform(0, x1 - x0)))
        ey = rnd.choice((rnd.uniform(0, 26), rnd.uniform(y1 - y0 - 26, y1 - y0), rnd.uniform(0, y1 - y0)))
        r_ = rnd.uniform(3, 14)
        d.ellipse((ex - r_, ey - r_ * 0.7, ex + r_, ey + r_ * 0.7), fill=(*ink, 255))
    for _ in range(5):                                              # rust run from a chip
        ex = rnd.uniform(40, x1 - x0 - 40)
        d.line((ex, y1 - y0 - 30, ex + rnd.uniform(-3, 3), y1 - y0), fill=(70, 38, 18, 160), width=rnd.randint(3, 6))
    board = Image.alpha_composite(board, Image.new('RGBA', board.size, (60, 50, 30, 30)))
    img.paste(board.filter(ImageFilter.GaussianBlur(0.7)), (x0, y0))

    # Fingernail scratches.
    x0, y0, x1, y1 = R_SCR
    sc = _scratches(x1 - x0, y1 - y0, 4102)
    img.alpha_composite(sc, (x0, y0))

    # Hands, two runs.
    for k, (x0, y0, x1, y1) in enumerate((R_HAND_A, R_HAND_B)):
        img.alpha_composite(_hands(x1 - x0, y1 - y0, 4110 + k, 7 + k), (x0, y0))

    # RING C and the arrow, stencilled: the depot's plain stencil, sprayed, worn.
    x0, y0, x1, y1 = R_RING
    W, H = x1 - x0, y1 - y0
    mask = Image.new('L', (W, H), 0)
    f = _fit('RING C', W * 0.86, 160)
    glyphs = _stencil_glyphs('RING C', f, 12)
    total = sum(a for _, a in glyphs)
    x = (W - total) / 2
    for gm, adv in glyphs:
        if gm is not None:
            mask.paste(gm, (int(x), 30), gm)
        x += adv
    arrow = _arrow_mask(int(W * 0.8), int(H * 0.62), 26)
    mask.paste(arrow, (int(W * 0.12), int(H * 0.36)), arrow)
    img.alpha_composite(_paint_layer(mask, paint, 4120, wear=0.42), (x0, y0))

    # C-114 and an arrow on, painted by hand with a brush.
    x0, y0, x1, y1 = R_C114
    W, H = x1 - x0, y1 - y0
    mask = Image.new('L', (W, H), 0)
    f = _font(118)
    x = 22
    rnd = random.Random(4130)
    for ch in 'C-114':
        g = Image.new('L', (150, 190), 0)
        ImageDraw.Draw(g).text((20, 150), ch, font=f, fill=255, anchor='ls')      # on one baseline
        g = g.rotate(rnd.uniform(-5, 5), resample=Image.BICUBIC, center=(60, 120))
        mask.paste(g, (int(x - 20), int(-10 + rnd.uniform(-5, 5))), g)
        x += f.getlength(ch) * 0.94
    d = ImageDraw.Draw(mask)
    ay = 118
    d.line((x + 18, ay, W - 46, ay - 4), fill=255, width=22)
    d.polygon([(W - 14, ay - 5), (W - 70, ay - 46), (W - 64, ay + 38)], fill=255)
    img.alpha_composite(_paint_layer(mask.filter(ImageFilter.GaussianBlur(0.8)), paint, 4131, wear=0.3, spray=False), (x0, y0))

    img.save(ATLAS, optimize=True)


def atlas_material():
    mt = bpy.data.materials.get('RingCStoryMat')
    if mt is not None:
        return mt
    mt, nt, bsdf = d17._new_material('RingCStoryMat')
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(ATLAS, check_existing=True)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = 0.8
    for attr, value in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
        if hasattr(mt, attr):
            try:
                setattr(mt, attr, value)
            except (TypeError, ValueError):
                pass
    return mt


# =====================================================================================================================
# Helpers
# =====================================================================================================================

def material(name):
    """A material by name; the ones this module relies on are made here when built on their own (index.html's
    tables have them all)."""
    mt = bpy.data.materials.get(name)
    if mt is not None:
        return mt
    worn = {'DustyDark': dict(base=(0.03, 0.029, 0.026), dirt=(0.05, 0.045, 0.035), chip=(0.09, 0.085, 0.075), rough=0.82,
                              chip_rough=0.5, metallic=0.2),
            'LuggageLeather': dict(base=(0.15, 0.08, 0.045), dirt=(0.06, 0.035, 0.02), chip=(0.27, 0.18, 0.11), rough=0.62,
                                   chip_rough=0.8, metallic=0.0),
            'ChildPaint': dict(base=(0.12, 0.24, 0.42), dirt=(0.06, 0.09, 0.12), chip=(0.2, 0.14, 0.08), rough=0.6,
                               chip_rough=0.8, metallic=0.0),
            'DepotSteel': dict(base=(0.05, 0.052, 0.05), dirt=(0.05, 0.03, 0.018), chip=(0.16, 0.15, 0.13), rough=0.6,
                               chip_rough=0.4, metallic=0.6),
            'SafetyYellow': dict(base=(0.55, 0.42, 0.06), dirt=(0.2, 0.16, 0.05), chip=(0.07, 0.068, 0.062), rough=0.8,
                                 chip_rough=0.9, metallic=0.0),
            'DepotGreen': dict(base=(0.06, 0.09, 0.07), dirt=(0.04, 0.035, 0.025), chip=(0.12, 0.11, 0.1), rough=0.65,
                               chip_rough=0.5, metallic=0.2)}
    if name in worn:
        return worn_material(name, **worn[name])
    return simple_material(name, (0.2, 0.2, 0.2), 0.8)


def _decal_obj(name, quads, coll, mat):
    """Quads on the atlas as one object, wound to face where they were built to face (no normal recalculation).
    quads: (corners counter-clockwise from bottom left seen from the front, pixel rect)."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    for corners, (x0, y0, x1, y1) in quads:
        f = bm.faces.new([bm.verts.new(Vector(c)) for c in corners])
        for lp, (u, v) in zip(f.loops, ((x0, y1), (x1, y1), (x1, y0), (x0, y0))):
            lp[uvl].uv = (u / 1024.0, 1.0 - v / 1024.0)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def wall_quad(x0, x1, z0, z1, y, rect):
    """A quad facing the camera (-y) at depth y."""
    return [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], rect


def sub(rect, u0, v0, u1, v1):
    """Part of an atlas rect: u, v in 0..1 from its top left."""
    x0, y0, x1, y1 = rect
    return (x0 + (x1 - x0) * u0, y0 + (y1 - y0) * v0, x0 + (x1 - x0) * u1, y0 + (y1 - y0) * v1)


# =====================================================================================================================
# DL-10: the shoes
# =====================================================================================================================

SHOE_MATS = ('DustyDark', 'LuggageLeather', 'ChildPaint')


def _loft(bm, secs, mat):
    """A shoe lofted through cross sections (x, sole z, half width, height), toe toward +x: six-sided rings, capped."""
    rings = []
    for x, z0, w, h in secs:
        pts = ((-w, z0), (w, z0), (1.05 * w, z0 + 0.45 * h), (0.68 * w, z0 + h), (-0.68 * w, z0 + h), (-1.05 * w, z0 + 0.45 * h))
        rings.append([bm.verts.new((x, y, z)) for y, z in pts])
    for a, b in zip(rings, rings[1:]):
        for k in range(6):
            bm.faces.new((a[k], a[(k + 1) % 6], b[(k + 1) % 6], b[k])).material_index = mat
    bm.faces.new(rings[0][::-1]).material_index = mat
    bm.faces.new(rings[-1]).material_index = mat


def shoe_templates():
    """The few shoes everything is made of, as meshes: (mesh, material slot choices, weight)."""
    out = []

    def mk(name, build):
        bm = bmesh.new()
        build(bm)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        return me
    # A man's shoe, a laced boot, a woman's shoe on a small heel, a child's bar shoe.
    oxford = ((-0.135, 0, 0.032, 0.07), (-0.08, 0, 0.042, 0.075), (0.02, 0, 0.046, 0.062), (0.1, 0, 0.042, 0.05), (0.135, 0, 0.024, 0.032))
    boot = ((-0.135, 0, 0.034, 0.19), (-0.07, 0, 0.042, 0.2), (0.0, 0, 0.046, 0.12), (0.09, 0, 0.044, 0.055), (0.135, 0, 0.025, 0.034))
    court = ((-0.12, 0.055, 0.026, 0.045), (-0.07, 0.04, 0.032, 0.04), (0.0, 0.012, 0.036, 0.034), (0.08, 0, 0.034, 0.03), (0.12, 0, 0.018, 0.02))
    child = tuple((x * 0.56, z, w * 0.68, h * 0.78) for x, z, w, h in oxford)

    def court_b(bm, mat):
        _loft(bm, court, mat)
        add_box(bm, (-0.105, 0, 0.03), (0.026, 0.026, 0.06), mat=mat)
    for name, secs, mats, wt in (('UOShoeA', oxford, (0, 0, 1), 5), ('UOShoeB', boot, (0, 1), 3),
                                 ('UOShoeC', court, (0, 1, 1), 3), ('UOShoeD', child, (1, 2, 2), 2)):
        variants = []
        for mi in sorted(set(mats)):
            if name == 'UOShoeC':
                variants.append((mi, mk(f'{name}{mi}', lambda bm, mi=mi: court_b(bm, mi))))
            else:
                variants.append((mi, mk(f'{name}{mi}', lambda bm, mi=mi, s=secs: _loft(bm, s, mi))))
        out.append((variants, mats, wt))
    return out


def _drop(bm, me, M, z_base):
    """Add a template under M, its lowest point set on z_base."""
    n0 = len(bm.verts)
    bm.from_mesh(me)
    bm.verts.ensure_lookup_table()
    vs = bm.verts[n0:]
    bmesh.ops.transform(bm, matrix=M, verts=vs)
    lo = min(v.co.z for v in vs)
    for v in vs:
        v.co.z += z_base - lo


def build_shoes(coll):
    rnd = random.Random(4140)
    tmpl = shoe_templates()
    weights = [t[2] for t in tmpl]
    bm = bmesh.new()
    count = [0]

    def pick(kid_bias=0.0):
        t = rnd.choices(tmpl, weights=[w * (3 if (i == 3 and kid_bias) else 1) for i, w in enumerate(weights)])[0]
        variants, mats, _ = t
        mi = rnd.choice(mats)
        return dict(variants)[mi]

    def pose(heap=False):
        r = rnd.random()
        if r < 0.45:
            M = I4()
        elif r < 0.85:
            M = _rx(math.radians(rnd.choice((-1, 1)) * rnd.uniform(70, 100)))      # on its side
        else:
            M = _rx(math.radians(rnd.uniform(160, 200)))                         # sole up
        if heap:
            M = _ry(math.radians(rnd.uniform(-30, 30))) @ _rx(math.radians(rnd.uniform(-25, 25))) @ M
        return M

    def put(x, y, z, heap=False, kid=0.0, scale=1.0):
        me = pick(kid)
        s = scale * rnd.uniform(0.92, 1.06)
        M = Matrix.Translation((x, y, 0)) @ _rz(rnd.uniform(0, 2 * math.pi)) @ Matrix.Diagonal((s, s, s, 1)) @ pose(heap)
        _drop(bm, me, M, z)
        count[0] += 1

    def clear(x, y):
        for x0, x1, y0, y1 in KEEP_CLEAR:
            if x0 <= x <= x1 and y0 <= y <= y1:
                return False
        return True

    placed = []

    def scatter(n, x0, x1, y0, y1, z, density=lambda x, y: 1.0, gap=0.13, kid=0.0):
        tries = 0
        k = 0
        while k < n and tries < n * 60:
            tries += 1
            x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
            if rnd.random() > density(x, y) or not clear(x, y):
                continue
            if any((x - px) ** 2 + (y - py) ** 2 < gap * gap for px, py in placed):
                continue
            placed.append((x, y))
            put(x, y, z, kid=kid)
            k += 1

    def heap(n, cx, cy, rx, ry, hmax, z):
        k = 0
        tries = 0
        while k < n and tries < n * 40:
            tries += 1
            u, v = rnd.uniform(-1, 1), rnd.uniform(-1, 1)
            d2 = u * u + v * v
            if d2 > 1:
                continue
            x, y = cx + u * rx, cy + v * ry
            if not clear(x, y):
                continue
            hz = hmax * (1 - d2) * rnd.uniform(0.55, 1.0)
            put(x, y, z + hz, heap=True)
            k += 1

    z = DECK
    # In front of the lane, along the queue line: thicker toward the gate.
    front = lambda x, y: 0.25 if x < uo.LOBBY_X0 else min(1.0, 0.4 + 0.6 * max(0.0, (x - 120.5) / 3.6)) * (0.75 if x > 125.6 else 1.0)  # noqa: E731
    scatter(118, 116.8, 126.6, -0.95, -0.42, z, front)
    heap(24, 124.95, -0.66, 0.42, 0.26, 0.12, z)                    # crushed up in front of the gate
    # Behind the lane: round the heap of luggage and under the bench, in the waiting area.
    scatter(46, 118.95, 123.5, 0.38, 1.14, z, lambda x, y: 0.8, gap=0.12, kid=0.5)
    scatter(9, 116.8, 118.55, 0.35, 2.2, z, lambda x, y: 0.6, gap=0.2)          # strays on the porch
    # Heaped against the lift front either side of the gate (under the balance gauge), clear of the stands.
    heap(30, 125.93, 0.28, 0.3, 0.05, 0.22, z)
    heap(8, 123.66, 0.29, 0.08, 0.04, 0.12, z)
    # Fallen down the shaft, at ring C's landing by its foot.
    scatter(8, 127.85, 128.7, -0.62, 0.95, 0.0, lambda x, y: 0.0 if -0.3 < y < 0.32 else 1.0, gap=0.14)
    mats = [material(n) for n in SHOE_MATS]
    ob = d17.mesh_object('UOShoes', bm, mats, coll, sharp=50)
    for t in tmpl:
        for _, me in t[0]:
            bpy.data.meshes.remove(me)
    print(f'story_ringc: {count[0]} shoes')
    return ob


def I4():
    return Matrix.Identity(4)


# What the shoes keep clear of (x0, x1, y0, y1, Blender world): the lane, the things already on the floor, the stands.
KEEP_CLEAR = (
    (116.5, 128.8, -0.4, 0.26),         # the lane (shoe centres: none reaches |y| < 0.2)
    (118.62, 118.98, 0.5, 2.5),         # the entrance's wall
    (119.0, 121.02, 0.5, 1.22),         # the heap of left luggage
    (121.62, 122.3, 0.26, 0.85),        # the case burst open
    (122.25, 122.6, -0.5, -0.22),       # the child's shoe (pass 3)
    (122.66, 123.1, 0.25, 0.65),        # the doll
    (123.06, 123.45, 0.52, 0.92),       # the birdcage
    (121.78, 121.92, 0.74, 1.18), (123.28, 123.42, 0.74, 1.18),     # the bench's ends
    (123.5, 128.8, 0.36, 3.0),          # behind the lift front
    (123.74, 124.22, -0.3, 0.4),        # the UP button's stand
    (124.25, 125.66, -0.3, 0.6),        # the car's doorway
    (126.22, 126.68, -0.3, 0.4),        # the crank's stand
    (126.66, 127.82, -1.2, 3.0),        # the service door's path, the counterweight's shaft
)


# =====================================================================================================================
# DL-10: the barrier, the LAST CAR board, the marks
# =====================================================================================================================

def build_barrier(coll):
    """Steel queue posts bolted along the line's front edge, bent flat at the foot toward the lift, the rail crushed
    between their tops; its end torn off and hanging over the deck's edge. Nothing stands above 0.08."""
    rnd = random.Random(4150)
    bm = bmesh.new()
    stl, yel = 0, 1
    z = DECK
    y0 = uo.QUEUE_Y[0] + 0.01
    tops = []
    for k, xb in enumerate((119.45, 120.45, 121.45, 122.45, 123.4)):
        add_cyl(bm, (xb, y0, z), (xb, y0, z + 0.012), 0.07, seg=12, mat=stl)                  # the floor flange
        for a in range(3):
            ang = a * 2 * math.pi / 3 + 0.4
            add_cyl(bm, (xb + 0.05 * math.cos(ang), y0 + 0.05 * math.sin(ang), z + 0.012), (xb + 0.05 * math.cos(ang), y0 + 0.05 * math.sin(ang), z + 0.02),
                    0.01, seg=6, mat=stl)
        yaw = math.radians(rnd.uniform(-38, -22))                                              # toward the lift and the camera
        dv = Vector((math.cos(yaw), math.sin(yaw), 0))
        r = 0.022
        foot = Vector((xb, y0, z + 0.012))
        knee = foot + Vector((0, 0, 0.05)) + dv * 0.03
        pts = [foot, knee, knee + dv * 0.09 + Vector((0, 0, -0.025))]
        ln = rnd.uniform(0.66, 0.78)
        end = pts[-1] + dv * ln
        end.z = z + r
        pts.append(pts[-1] + (end - pts[-1]) * 0.5 + Vector((0, 0, -0.0)))
        pts.append(end)
        for a_, b_ in zip(pts, pts[1:]):
            add_cyl(bm, a_, b_, r, seg=8, mat=yel)
        add_cyl(bm, end, end + dv * 0.025, r * 1.25, seg=8, mat=stl)                        # its cap
        tops.append(end)
    # The rail: from top to top along the floor, kinked and twisted; past the last post it is torn and hangs down
    # over the deck's edge.
    rail = []
    for a_, b_ in zip(tops, tops[1:]):
        rail.append(a_)
        for t in (0.33, 0.66):
            p = a_.lerp(b_, t)
            p.y += rnd.uniform(-0.08, 0.06)
            p.y = max(-0.96, min(-0.5, p.y))
            p.z = z + 0.018
            rail.append(p)
    rail.append(tops[-1])
    last = tops[-1]
    rail += [Vector((last.x + 0.35, -0.9, z + 0.018)), Vector((last.x + 0.55, -1.02, z + 0.01)),
             Vector((last.x + 0.6, -1.06, z - 0.2)), Vector((last.x + 0.58, -1.07, z - 0.42))]
    for a_, b_ in zip(rail, rail[1:]):
        add_cyl(bm, a_, b_, 0.018, seg=8, mat=yel)
    # A loose rail section lying by the first post, where it came off.
    add_cyl(bm, (118.9, -0.86, z + 0.018), (119.38, -0.7, z + 0.018), 0.018, seg=8, mat=yel)
    ob = d17.mesh_object('UOBarrier', bm, [material('DepotSteel'), material('SafetyYellow')], coll, sharp=40)
    return ob


def build_last_car(coll, atlas):
    """LAST CAR, an enamel board, hanging from one hook under the gate's head: the chain from its left eye holds, the
    right one snapped (its stub still on the other hook). Origin at the hook it hangs from."""
    hx, hy, hz = LASTCAR_HOOK
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    stl, atl = 0, 1
    # Hooks under the head (a plate and a crook each), local to the holding hook.
    for dx in (0.0, LASTCAR_HOOK2 - hx):
        add_box(bm, (dx, 0.012, -0.006), (0.05, 0.03, 0.012), mat=stl)
        add_cyl(bm, (dx, 0.0, -0.012), (dx, 0.0, -0.05), 0.005, seg=6, mat=stl)
        add_torus(bm, (dx + 0.012, 0.0, -0.055), (0, 1, 0), 0.013, 0.004, mat=stl, seg=10, rseg=4)
    # The chain: three links to the board's eye.
    eye = Vector((0.0, 0.0, -0.13))
    for k in range(3):
        c = Vector((0, 0, -0.07 - k * 0.022))
        add_torus(bm, c, (0, 1, 0) if k % 2 else (1, 0, 0), 0.011, 0.0028, mat=stl, seg=8, rseg=4)
    # The snapped one: two links and a torn end on the bare hook.
    for k in range(2):
        c = Vector((LASTCAR_HOOK2 - hx + 0.012, 0, -0.075 - k * 0.022))
        add_torus(bm, c, (0, 1, 0) if k % 2 else (1, 0, 0), 0.011, 0.0028, mat=stl, seg=8, rseg=4)
    # The board in its own frame: origin at its left eye, x along its top, z up; hung by that eye, its right end down.
    W, H, T = 0.84, 0.28, 0.018
    ex = 0.08                                          # the eye, in from the left end
    R = Matrix.Translation(eye) @ _ry(math.radians(LASTCAR_TILT))
    tmp = bmesh.new()
    add_box(tmp, (W / 2 - ex, 0, -H / 2), (W, T, H), mat=stl)
    bmesh.ops.transform(tmp, matrix=R, verts=tmp.verts)
    me = bpy.data.meshes.new('_t')
    tmp.to_mesh(me)
    tmp.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])          # the solids; the face goes on after, wound to -y
    corners = [R @ Vector((u - ex, -T / 2 - 0.002, v)) for u, v in ((0, -H), (W, -H), (W, 0), (0, 0))]
    f = bm.faces.new([bm.verts.new(c) for c in corners])
    f.material_index = atl
    x0, y0, x1, y1 = R_LAST
    for lp, (u, v) in zip(f.loops, ((x0, y1), (x1, y1), (x1, y0), (x0, y0))):
        lp[uvl].uv = (u / 1024.0, 1.0 - v / 1024.0)
    me = bpy.data.meshes.new('UOLastCar')
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    me.materials.append(material('DepotSteel'))
    me.materials.append(atlas)
    me.polygons.foreach_set('use_smooth', [False] * len(me.polygons))
    ob = bpy.data.objects.new('UOLastCar', me)
    coll.objects.link(ob)
    ob.location = LASTCAR_HOOK
    return ob


def build_marks(coll, atlas):
    """UOHandMarks: hands in dust dragged down the lift front, the gate's architrave and the counterweight shaft's back
    wall; scratches by the gate. WayRingC10: RING C and the arrow, on the shaft's back wall."""
    yw = uo.WALL_Y - 0.023                         # just in front of the lift front's dado rail
    ya = uo.WALL_Y - 0.038                         # in front of the architrave
    ys = uo.SHAFT_BACK - 0.012
    g0, g1 = uo.GATE[0], uo.GATE[1]
    q = [
        wall_quad(123.71, 123.9, DECK + 0.12, DECK + 1.35, yw, sub(R_HAND_A, 0.2, 0.0, 0.78, 1.0)),
        wall_quad(g1 + 0.14, 126.01, DECK + 0.12, DECK + 1.25, yw, sub(R_HAND_B, 0.0, 0.0, 1.0, 0.9)),
        wall_quad(g0 - 0.13, g0 - 0.01, DECK + 0.35, DECK + 1.3, ya, sub(R_HAND_A, 0.55, 0.15, 0.98, 0.95)),
        wall_quad(g1 + 0.01, g1 + 0.13, DECK + 0.3, DECK + 1.2, ya, sub(R_HAND_B, 0.02, 0.3, 0.45, 1.0)),
        wall_quad(g0 - 0.13, g0 - 0.01, DECK + 0.08, DECK + 0.38, ya - 0.001, sub(R_SCR, 0.1, 0.0, 0.5, 1.0)),
        wall_quad(g1 + 0.01, g1 + 0.13, DECK + 0.06, DECK + 0.36, ya - 0.001, sub(R_SCR, 0.5, 0.0, 0.9, 1.0)),
        wall_quad(g1 + 0.15, g1 + 0.45, DECK + 0.55, DECK + 0.85, yw - 0.001, R_SCR),
        # Down the counterweight shaft's back wall, from the deck down toward ring C.
        wall_quad(126.9, 127.24, 0.55, 1.55, ys, R_HAND_A),
        wall_quad(127.3, 127.7, 0.75, 2.1, ys, sub(R_HAND_B, 0.0, 0.0, 1.0, 1.0)),
        wall_quad(126.88, 127.22, 1.6, 2.6, ys, sub(R_HAND_B, 0.0, 0.0, 1.0, 1.0)),
    ]
    marks = _decal_obj('UOHandMarks', q, coll, atlas)
    return marks, build_way_ringc10(coll, atlas)


def ring_c_material():
    """The RING C stencil every scene shares (WayRingCMat, made by whichever pass 4 module runs first; in the full
    build art/pass4/build_story_shafts.py, before this one). None if it cannot be had."""
    mt = bpy.data.materials.get('WayRingCMat')
    if mt is None:
        try:
            import build_story_shafts
            mt = build_story_shafts.ring_c_material()
        except Exception as e:                       # built on its own without it: the atlas's own stencil
            print('story_ringc: no WayRingCMat:', e)
            mt = None
    return mt


def build_way_ringc10(coll, atlas):
    """WayRingC10: the shared RING C stencil (0.84 x 0.42, as DL-06 to DL-09's) on the counterweight shaft's back wall,
    over the counterweight; or, failing that, the atlas's own."""
    x, y, zc, s = STENCIL10
    mt = ring_c_material()
    if mt is not None:
        w, h = 0.84, 0.42
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new('UVMap')
        f = bm.faces.new([bm.verts.new(c) for c in ((x - w / 2, y, zc - h / 2), (x + w / 2, y, zc - h / 2), (x + w / 2, y, zc + h / 2), (x - w / 2, y, zc + h / 2))])
        for lp, uv in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            lp[uvl].uv = uv
        me = bpy.data.meshes.new('WayRingC10')
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mt)
        ob = bpy.data.objects.new('WayRingC10', me)
        coll.objects.link(ob)
        return ob
    return _decal_obj('WayRingC10', [wall_quad(x - s / 2, x + s / 2, zc - s / 2, zc + s / 2, y, R_RING)], coll, atlas)


def build_way_c114(coll, atlas):
    x, y, zc, w, h = C114_MARK
    return _decal_obj('WayC114', [wall_quad(x - w / 2, x + w / 2, zc - h / 2, zc + h / 2, y, R_C114)], coll, atlas)


# =====================================================================================================================
# Entry points
# =====================================================================================================================

def build_set(dl01, m, coll):
    bpy.context.view_layer.update()
    make_atlas()
    atlas = atlas_material()
    build_shoes(coll)
    build_barrier(coll)
    build_last_car(coll, atlas)
    build_marks(coll, atlas)
    build_way_c114(coll, atlas)


def add_clips(dl01, arm):
    pass
