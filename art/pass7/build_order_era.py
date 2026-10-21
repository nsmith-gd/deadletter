"""Prologue pass 7 (docs/full_game_plan.md, the motto thread: enamel authority in the lower rings): the Order era's institutional
furniture, sparingly. Built in FINAL world coordinates after every other set builder (art/dl01/build_dl01.py appends
this module to its PASS6 list, after art/pass7/build_audio_props.py); other builders' objects are only read here (ray
casts against the built scene to find the wall faces), never changed.

The Steward's portrait (one mesh, StewardPortrait, as two linked duplicates):
    StewardPortraitRations  DL-05, over the ration hatch's end of the counter: hung from behind the RATION ISSUE fascia
                            in front of the servery grille, right of the ration board, clear of the shutter (x 56.30+)
    StewardPortraitUpOnly   DL-10, on the pier of the lobby's back wall between the UP poster and the departures board,
                            under the pendant lamp, over the heap of left luggage, clear of TannoyRelocation
    A large institutional oil portrait (canvas 0.64 x 0.80) in a heavy gilt frame (0.82 x 0.98 outside) with corner
    cartouches, a crest and a brass title plaque, hung on a cord from one hook and leaning out at the top. The painting
    is steward_portrait.png (StewardPortraitMat): a stern, kindly-painted older man in a high-collared uniform,
    half-length, dim and varnished, the varnish crazed. Origin: the hook (on the wall plane), the frame hanging below.

ORDER ABOVE ALL (order_motto.png, OrderMottoMat, an alpha decal), at most two per scene, depot scenes only:
    OrderMottoDL01  a stencilled band high on the alcove's back wall under the pipe run (left of the dispatch board);
                    and an enamel plate hung on the hall gantry's railing, over the hall
    OrderMottoDL02  a stencilled band high on the sorting hall's back wall, over the tea corner and the stair door
    OrderMottoDL04  a long stencilled band high on the recharge hall's far wall, over the racks
    OrderMottoDL06  a stencilled band on the sorting floor's wall, over the postal service poster, between the lamps
    The bands are sprayed through a stencil (the counters bridged) in the depot's cream on a band of institutional
    green between two cream rules, worn back to the wall in patches; the plate is vitreous enamel, cream on the
    Order's dark blue, chipped to black iron at its edges and screws. None is at eye level near a puzzle or in front
    of anything the player reads; all are behind the lane (y > 0.5).

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y. Game (x, y, z) = (x, z, -y).
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

import build_d17 as d17
from build_d17 import add_box, add_cyl, add_sphere, add_torus

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
PORTRAIT_PNG = os.path.join(TEX, 'steward_portrait.png')
MOTTO_PNG = os.path.join(TEX, 'order_motto.png')
V = Vector


# =====================================================================================================================
# Textures (PIL): the portrait and the motto
# =====================================================================================================================

CARLITO = '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf'
CALADEA = '/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf'

PW, PH = 768, 1024                    # steward_portrait.png
CANVAS_PX = (0, 0, 768, 960)          # the painting (0.64 x 0.80 m)
PLAQUE_PX = (0, 960, 256, 1024)       # the brass title plaque on the frame's bottom rail


def _font(size, path=CARLITO):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.truetype(CARLITO, size)


def _noise(w, h, scale, seed, octaves=4):
    """Value noise in 0..1 (numpy), smooth at `scale` pixels."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    s = scale
    for _ in range(octaves):
        gw, gh = max(2, int(w / s) + 2), max(2, int(h / s) + 2)
        g = rng.random((gh, gw)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8), 'L').resize((int(gw * s), int(gh * s)), Image.BICUBIC)
        a = np.asarray(im, np.float32)[:h, :w] / 255.0
        out += a * amp
        tot += amp
        amp *= 0.5
        s = max(1.0, s / 2)
    return out / tot


def _blend(img, layer, mask):
    """Paste `layer` (RGB) over img through `mask` (L or float array 0..1)."""
    if isinstance(mask, np.ndarray):
        mask = Image.fromarray(np.clip(mask * 255, 0, 255).astype(np.uint8), 'L')
    return Image.composite(layer, img, mask)


def _soft(shape_fn, size, blur):
    m = Image.new('L', size, 0)
    shape_fn(ImageDraw.Draw(m))
    return m.filter(ImageFilter.GaussianBlur(blur)) if blur else m


def make_portrait(path):
    """The Steward: an institutional oil portrait, half-length, in a high-collared uniform. Dark varnished ground lit
    from the upper left, the face simple and a little idealised, kindly and stern; the varnish yellowed, crazed and
    dulled, the bottom grimy where hands and smoke reached."""
    rnd = random.Random(7310)
    x0, y0, x1, y1 = CANVAS_PX
    W, H = x1 - x0, y1 - y0
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    # The ground: warm umber, a glow behind the head (upper left), a heavy dark curtain at the right.
    glow = np.exp(-(((xx - W * 0.42) / (W * 0.42)) ** 2 + ((yy - H * 0.30) / (H * 0.38)) ** 2))
    n = _noise(W, H, 90, 11)
    base = np.stack([46 + 40 * glow + 14 * n, 38 + 32 * glow + 10 * n, 26 + 20 * glow + 6 * n], -1)
    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8), 'RGB')
    d = ImageDraw.Draw(img)
    # a drape at the upper right: deep oxblood folds
    drape = Image.new('RGB', (W, H), (58, 20, 16))
    fold = _noise(W, H, 40, 12, 2)
    folds = np.sin(xx / 23.0 + fold * 5.0) * 0.5 + 0.5
    dr = np.stack([40 + 40 * folds, 14 + 12 * folds, 12 + 8 * folds], -1)
    drape = Image.fromarray(np.clip(dr, 0, 255).astype(np.uint8), 'RGB')
    dmask = _soft(lambda g: g.polygon([(W * 0.70, 0), (W, 0), (W, H * 0.62), (W * 0.86, H * 0.5), (W * 0.78, H * 0.28)],
                                      fill=200), (W, H), 18)
    img = _blend(img, drape, dmask)
    # a column's base and plinth at the left, barely there
    col = Image.new('RGB', (W, H), (70, 60, 44))
    cmask = _soft(lambda g: (g.rectangle((0, H * 0.18, W * 0.13, H), fill=110),
                             g.rectangle((0, H * 0.16, W * 0.17, H * 0.2), fill=120)),
                  (W, H), 10)
    img = _blend(img, col, cmask)

    # The body: the tunic (dark bottle green, near black), shoulders sloping, epaulettes, the stand collar.
    cx = W * 0.5
    shade = np.clip((xx - cx) / (W * 0.5), -1, 1)           # light from the left
    tn = _noise(W, H, 30, 13, 3)
    tc = np.stack([22 - 9 * shade + 7 * tn, 33 - 13 * shade + 9 * tn, 28 - 11 * shade + 7 * tn], -1)
    tunic = Image.fromarray(np.clip(tc, 0, 255).astype(np.uint8), 'RGB')

    def body(g):
        g.polygon([(cx - 84, 470), (cx + 84, 470), (cx + 190, 520), (cx + 278, 572), (cx + 322, 660), (cx + 350, H),
                   (cx - 350, H), (cx - 322, 660), (cx - 278, 572), (cx - 190, 520)], fill=255)
        g.ellipse((cx - 330, 545, cx - 220, 680), fill=255)
        g.ellipse((cx + 220, 545, cx + 330, 680), fill=255)
    img = _blend(img, tunic, _soft(body, (W, H), 3))
    d = ImageDraw.Draw(img, 'RGBA')
    # the front's edge and the cloth's folds
    d.line((cx + 4, 500, cx + 10, H), fill=(8, 13, 11, 200), width=5)
    for k in range(7):
        xa = cx - 250 + k * 80 + rnd.uniform(-10, 10)
        d.line((xa, 700 + rnd.uniform(0, 60), xa + rnd.uniform(-40, 40), H), fill=(10, 15, 13, 70), width=14)
    d.line((cx - 260, 600, cx - 300, H), fill=(60, 74, 62, 60), width=10)       # the lit arm's edge
    # the sash, from his right shoulder (picture left) down across to his left hip: dark oxblood, gilt-edged
    sash = [(cx - 215, 548), (cx - 160, 530), (cx + 250, H), (cx + 175, H)]
    d.polygon(sash, fill=(78, 26, 22, 240))
    d.line((cx - 215, 548, cx + 175, H), fill=(128, 98, 46, 190), width=3)
    d.line((cx - 160, 530, cx + 250, H), fill=(128, 98, 46, 190), width=3)
    for k in range(9):                                        # the sash's sheen where the light catches it
        t = k / 9
        d.line((cx - 196 + 400 * t, 548 + 430 * t, cx - 180 + 400 * t, 540 + 430 * t), fill=(120, 46, 36, 50), width=7)
    # buttons down the front (gilt), the lower ones under the sash
    for k in range(7):
        by = 530 + k * 66
        if by > H - 20:
            break
        d.ellipse((cx - 13, by - 10, cx + 7, by + 10), fill=(150, 116, 52, 255))
        d.ellipse((cx - 9, by - 7, cx - 1, by + 1), fill=(214, 184, 112, 220))
    # epaulettes: small gilt boards on the shoulders, a short fringe
    for s in (-1, 1):
        ex = cx + s * 238
        lit = 1.0 if s < 0 else 0.7
        g1 = tuple(int(v * lit) for v in (150, 116, 54))
        g2 = tuple(int(v * lit) for v in (190, 154, 82))
        d.polygon([(ex - s * 70, 528), (ex + s * 54, 548), (ex + s * 60, 572), (ex - s * 66, 556)], fill=(*g1, 255))
        d.line((ex - s * 60, 536, ex + s * 44, 552), fill=(*g2, 200), width=6)
        for k in range(12):
            t = k / 11
            fx0 = ex - s * 66 + s * 126 * t
            fy0 = 556 + 16 * t
            d.line((fx0, fy0, fx0 + s * 1, fy0 + 30), fill=(*g1, 255), width=5)
    # a star of an order on his left breast (picture right) and a ribbon bar over it
    sx, sy = cx + 118, 690
    for k in range(8):
        a = k * math.pi / 4
        d.polygon([(sx, sy), (sx + 26 * math.cos(a - 0.22), sy + 26 * math.sin(a - 0.22)),
                   (sx + 36 * math.cos(a), sy + 36 * math.sin(a)),
                   (sx + 26 * math.cos(a + 0.22), sy + 26 * math.sin(a + 0.22))], fill=(150, 140, 112, 255))
    d.ellipse((sx - 11, sy - 11, sx + 11, sy + 11), fill=(98, 32, 26, 255))
    for k, c in enumerate(((98, 32, 26), (150, 124, 60), (34, 46, 74), (150, 124, 60))):
        d.rectangle((cx + 72 + k * 18, 626, cx + 88 + k * 18, 638), fill=(*c, 255))

    # The head: face, ears, hair. Skin lit from the upper left.
    fx, fy, fw, fh = cx - 4, 292, 222, 290                    # the face's centre and size
    lx = np.clip((xx - (fx - 70)) / 150.0, -1, 1.5)
    ly = np.clip((yy - (fy - 90)) / 240.0, -0.5, 1.5)
    lit = np.clip(1.0 - 0.5 * np.maximum(lx, 0) - 0.22 * np.maximum(ly, 0), 0.3, 1.0)
    sn = _noise(W, H, 14, 17, 3)
    sk = np.stack([(178 + 10 * sn) * lit + 16, (138 + 8 * sn) * lit + 10, (106 + 6 * sn) * lit + 8], -1)
    skin = Image.fromarray(np.clip(sk, 0, 255).astype(np.uint8), 'RGB')

    def head(g):
        g.rectangle((fx - 66, fy + 80, fx + 66, 470), fill=255)                    # the neck (under the collar)
        g.ellipse((fx - fw / 2, fy - fh / 2, fx + fw / 2, fy + fh / 2), fill=255)  # the face
        g.polygon([(fx - fw / 2 + 3, fy + 4), (fx - 58, fy + fh / 2 + 2), (fx + 58, fy + fh / 2 + 2), (fx + fw / 2 - 3, fy + 4)],
                  fill=255)                                                        # a firm jaw
        g.ellipse((fx - fw / 2 - 18, fy - 22, fx - fw / 2 + 14, fy + 48), fill=255)  # ears
        g.ellipse((fx + fw / 2 - 14, fy - 22, fx + fw / 2 + 18, fy + 48), fill=255)
    img = _blend(img, skin, _soft(head, (W, H), 2.5))
    # modelling: the shadow side, the eye sockets, under the jaw, the cheeks' warmth, the brow's light
    sh = _soft(lambda g: g.ellipse((fx + 30, fy - 100, fx + 140, fy + 150), fill=170), (W, H), 34)
    img = _blend(img, Image.new('RGB', (W, H), (84, 54, 38)), np.asarray(sh, np.float32) / 255 * 0.85)
    sock = _soft(lambda g: (g.ellipse((fx - 82, fy - 30, fx - 10, fy + 14), fill=150),
                            g.ellipse((fx + 12, fy - 30, fx + 84, fy + 14), fill=190)), (W, H), 10)
    img = _blend(img, Image.new('RGB', (W, H), (104, 66, 48)), np.asarray(sock, np.float32) / 255 * 0.7)
    jaw = _soft(lambda g: g.rectangle((fx - 76, fy + fh / 2 - 8, fx + 76, fy + fh / 2 + 40), fill=220), (W, H), 14)
    img = _blend(img, Image.new('RGB', (W, H), (54, 36, 26)), np.asarray(jaw, np.float32) / 255 * 0.85)
    cheek = _soft(lambda g: (g.ellipse((fx - 88, fy + 16, fx - 30, fy + 70), fill=120),
                             g.ellipse((fx + 34, fy + 16, fx + 84, fy + 66), fill=70)),
                  (W, H), 16)
    img = _blend(img, Image.new('RGB', (W, H), (190, 112, 88)), np.asarray(cheek, np.float32) / 255 * 0.4)
    brow = _soft(lambda g: g.ellipse((fx - 80, fy - 120, fx + 30, fy - 50), fill=140), (W, H), 20)
    img = _blend(img, Image.new('RGB', (W, H), (226, 190, 156)), np.asarray(brow, np.float32) / 255 * 0.5)
    # Hair: grey, short, receding at the temples, combed back; grey at the sides over the ears
    hn = _noise(W, H, 6, 19, 2)
    hlit = np.clip(1.15 - 0.55 * np.clip((xx - fx + 40) / 140, 0, 1), 0.5, 1.2)
    hc = np.stack([112 + 64 * hn, 109 + 62 * hn, 102 + 58 * hn], -1) * hlit[..., None]
    hair = Image.fromarray(np.clip(hc, 0, 255).astype(np.uint8), 'RGB')

    def hairline(g):
        g.ellipse((fx - fw / 2 - 8, fy - fh / 2 - 22, fx + fw / 2 + 8, fy + fh / 2 - 60), fill=255)   # the skull
        g.rectangle((fx - fw, fy - 52, fx + fw, H), fill=0)                                           # cut at the brow
        g.ellipse((fx - 70, fy - fh / 2 + 2, fx + 66, fy - 40), fill=0)                              # the forehead, receded
        for s in (-1, 1):                                                                    # sideburns
            e = fx + s * fw / 2
            g.polygon([(e + s * 6, fy - 60), (e - s * 16, fy - 60), (e - s * 10, fy + 20), (e + s * 2, fy + 20)], fill=255)
    img = _blend(img, hair, _soft(hairline, (W, H), 3.5))
    d = ImageDraw.Draw(img, 'RGBA')
    for k in range(60):                                       # combed-back strokes
        a = rnd.uniform(-0.82, 0.82)
        hx = fx + a * (fw / 2)
        hy = fy - fh / 2 - 4 + abs(a) ** 2 * 70
        d.line((hx, hy + rnd.uniform(0, 30), hx + a * 26, hy + 34 + rnd.uniform(0, 20)), fill=(70, 68, 62, 60), width=2)
        d.line((hx + 3, hy + rnd.uniform(0, 30), hx + 3 + a * 22, hy + 30), fill=(196, 192, 182, 50), width=2)
    # the features: brows, eyes (calm, heavy-lidded, looking out), nose, moustache, mouth
    ey = fy - 6
    for s, tone in ((-1, 1.0), (1, 0.72)):
        ex = fx + s * 46
        t = lambda c, a: (int(c[0] * tone), int(c[1] * tone), int(c[2] * tone), a)
        d.ellipse((ex - 15, ey - 4, ex + 15, ey + 6), fill=t((214, 200, 178), 200))       # the white
        d.ellipse((ex - 7, ey - 6, ex + 7, ey + 7), fill=(46, 42, 44, 255))               # the iris
        d.ellipse((ex - 4 + (2 if s > 0 else 0), ey - 4, ex - 1 + (2 if s > 0 else 0), ey - 1), fill=(232, 226, 210, 220))
        d.chord((ex - 19, ey - 11, ex + 19, ey + 9), 180, 360, fill=t((150, 104, 80), 255))   # the heavy upper lid
        d.arc((ex - 19, ey - 11, ex + 19, ey + 9), 190, 350, fill=(60, 38, 28, 255), width=3)
        d.arc((ex - 16, ey - 4, ex + 16, ey + 12), 20, 160, fill=t((130, 88, 66), 140), width=2)   # under the eye
        d.line((ex - s * 30, ey - 22 + (3 if s > 0 else 0), ex + s * 22, ey - 27), fill=t((186, 182, 172), 255), width=7)  # brow
        d.line((ex - s * 26, ey - 20, ex + s * 20, ey - 23), fill=(96, 92, 84, 160), width=3)
    # the nose: the lit ridge, its shadow side, the nostrils
    d.line((fx + 6, ey + 4, fx + 12, fy + 58), fill=(104, 64, 46, 150), width=7)
    d.line((fx - 5, ey + 2, fx - 2, fy + 54), fill=(226, 184, 150, 120), width=5)
    d.ellipse((fx - 22, fy + 52, fx + 26, fy + 70), fill=(96, 58, 40, 170))
    # a neat grey moustache; the mouth a firm line, its corners just turned up
    d.chord((fx - 48, fy + 62, fx + 48, fy + 100), 180, 360, fill=(160, 156, 146, 255))
    d.chord((fx - 2, fy + 66, fx + 48, fy + 100), 180, 360, fill=(110, 106, 98, 160))
    d.line((fx - 30, fy + 98, fx + 30, fy + 98), fill=(86, 46, 36, 255), width=4)
    d.line((fx - 30, fy + 98, fx - 38, fy + 93), fill=(86, 46, 36, 220), width=3)
    d.line((fx + 30, fy + 98, fx + 38, fy + 93), fill=(86, 46, 36, 220), width=3)
    d.ellipse((fx - 22, fy + 104, fx + 22, fy + 116), fill=(170, 104, 80, 100))    # the lower lip's light
    d.line((fx - 42, fy + 48, fx - 52, fy + 92), fill=(130, 80, 58, 90), width=4)   # the folds by the mouth
    d.line((fx + 42, fy + 48, fx + 52, fy + 92), fill=(90, 56, 40, 110), width=4)
    # The stand collar: high and stiff, up under the jaw, gilt braid at its edges and oak leaves on it
    d.polygon([(cx - 98, 404), (cx + 98, 404), (cx + 104, 486), (cx + 18, 500), (cx - 18, 500), (cx - 104, 486)],
              fill=(22, 33, 28, 255))
    d.polygon([(cx + 10, 404), (cx + 98, 404), (cx + 104, 486), (cx + 18, 500)], fill=(14, 22, 18, 160))
    d.line([(cx - 98, 405), (cx + 98, 405)], fill=(150, 118, 56, 255), width=5)
    d.line([(cx - 104, 486), (cx - 18, 500), (cx + 18, 500), (cx + 104, 486)], fill=(170, 136, 66, 255), width=7)
    for k in range(4):
        d.ellipse((cx - 86 + k * 14, 424 + k * 14, cx - 68 + k * 14, 438 + k * 14), fill=(160, 126, 58, 210))
        d.ellipse((cx + 68 - k * 14, 424 + k * 14, cx + 86 - k * 14, 438 + k * 14), fill=(104, 82, 40, 210))

    # Paint: soften, then brushwork across it.
    img = img.filter(ImageFilter.GaussianBlur(1.6))
    arr = np.asarray(img, np.float32)
    strokes = _noise(W, H, 3, 23, 2)
    sx_ = Image.fromarray((strokes * 255).astype(np.uint8), 'L').resize((W // 6, H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
    st = np.asarray(sx_, np.float32) / 255.0
    arr *= (0.92 + 0.16 * st)[..., None]
    # Varnish: yellowed and darkened, more so toward the edges (a vignette), grime settled at the bottom.
    vig = np.clip(1.0 - 0.55 * (((xx - W / 2) / (W * 0.62)) ** 2 + ((yy - H * 0.42) / (H * 0.66)) ** 2), 0.3, 1.0)
    arr = arr * vig[..., None]
    lum = arr.mean(-1, keepdims=True)
    arr = arr * 0.8 + lum * 0.2
    arr = arr * np.array([0.84, 0.76, 0.54], np.float32) + np.array([8, 6, 1], np.float32)
    grime = np.clip((yy / H - 0.7) / 0.3, 0, 1) * (0.25 + 0.3 * _noise(W, H, 50, 29))
    arr = arr * (1 - grime[..., None] * 0.6)
    # Craquelure: a fine net of dark cracks over everything
    cr = Image.new('L', (W, H), 0)
    cd = ImageDraw.Draw(cr)
    for _ in range(900):
        px, py = rnd.uniform(0, W), rnd.uniform(0, H)
        a = rnd.uniform(0, math.pi)
        pts = [(px, py)]
        for k in range(rnd.randint(2, 5)):
            a += rnd.uniform(-0.9, 0.9)
            px += math.cos(a) * rnd.uniform(6, 16)
            py += math.sin(a) * rnd.uniform(6, 16)
            pts.append((px, py))
        cd.line(pts, fill=rnd.randint(40, 110), width=1)
    crk = np.asarray(cr, np.float32) / 255.0
    arr = arr * (1 - 0.45 * crk[..., None])
    # flaking: a few small losses to the dark ground near the edges
    fl = _noise(W, H, 8, 31, 3)
    edge = np.clip(1.0 - np.minimum.reduce([xx, W - xx, yy, H - yy]) / 60.0, 0, 1)
    loss = (fl > 0.72 - 0.12 * edge).astype(np.float32) * (0.3 + 0.7 * edge)
    arr = arr * (1 - 0.6 * loss[..., None]) + np.array([30, 24, 16], np.float32) * 0.6 * loss[..., None]
    paint = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB')

    out = Image.new('RGB', (PW, PH), (30, 24, 16))
    out.paste(paint, (x0, y0))
    _plaque(out)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.save(path, optimize=True)


def _plaque(img):
    """The brass title plaque: THE STEWARD engraved, the brass tarnished, its screws."""
    x0, y0, x1, y1 = PLAQUE_PX
    W, H = x1 - x0, y1 - y0
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    n = _noise(W, H, 10, 41, 3)
    sheen = 0.75 + 0.25 * np.cos((yy / H - 0.35) * 3.0)
    arr = np.stack([150 * sheen * (0.8 + 0.3 * n), 112 * sheen * (0.8 + 0.3 * n), 50 * sheen * (0.8 + 0.3 * n)], -1)
    pl = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), 'RGB')
    d = ImageDraw.Draw(pl)
    d.rectangle((2, 2, W - 3, H - 3), outline=(80, 58, 24), width=2)
    d.text((W / 2, H / 2 + 1), 'THE STEWARD', font=_font(30, CALADEA), fill=(40, 28, 12), anchor='mm')
    for sx in (10, W - 11):
        d.ellipse((sx - 4, H / 2 - 4, sx + 4, H / 2 + 4), fill=(70, 52, 22))
        d.line((sx - 3, H / 2 - 2, sx + 3, H / 2 + 2), fill=(30, 22, 10), width=1)
    img.paste(pl, (x0, y0))


MW, MH = 1024, 512                    # order_motto.png (RGBA: alpha decals)
BAND_A = (0, 0, 1024, 128)            # the stencilled band, worn one way
BAND_B = (0, 128, 1024, 256)          # ... and another (so two in one scene never match)
PLATE = (0, 256, 1024, 480)           # the enamel plate


def _stencil_mask(text, size, spacing, bridge):
    """The text set in Carlito Bold as a stencil: every counter tied to the outside by a bridge (O and D at top and
    bottom); bridge 0 sets it solid (enamel). Returns an L image, the letters 255."""
    f = _font(size)
    glyphs = []
    for ch in text:
        if ch == ' ':
            glyphs.append(None)
            continue
        l, t, r, b = f.getbbox(ch)
        g = Image.new('L', (r - l + 8, size + 16), 0)
        ImageDraw.Draw(g).text((4 - l, 8), ch, font=f, fill=255)
        a = (np.asarray(g) > 127).astype(np.uint8) * 255
        g = Image.fromarray(a, 'L')
        # the counters: what the outside cannot reach
        ff = Image.fromarray(a.copy(), "L").copy()
        ImageDraw.floodfill(ff, (0, 0), 128)
        fa = np.asarray(ff).copy()
        out = a.copy()
        k = 0
        while bridge > 0:
            zs = np.argwhere(fa == 0)
            if not len(zs):
                break
            k += 1
            im = Image.fromarray(fa, "L").copy()
            ImageDraw.floodfill(im, (int(zs[0][1]), int(zs[0][0])), 60 + k)
            fa = np.asarray(im).copy()
            ys, xs = np.where(fa == 60 + k)
            hx = int(round(xs.mean()))
            top, bot = ys.min(), ys.max()
            mid = a.shape[0] / 2
            ends = []
            if ch in 'ODQ0' or (top + bot) / 2 < mid:
                ends.append('up')
            if ch in 'ODQ0' or (top + bot) / 2 >= mid:
                ends.append('down')
            if ch == 'A':
                ends = ['up']
            for e in ends:
                if e == 'up':
                    out[:top, max(0, hx - bridge // 2):hx + bridge // 2 + 1] = 0
                else:
                    out[bot + 1:, max(0, hx - bridge // 2):hx + bridge // 2 + 1] = 0
        glyphs.append(Image.fromarray(out, 'L'))
    wsp = int(size * 0.42)
    total = sum((g.width if g else wsp) for g in glyphs) + spacing * (len(glyphs) - 1)
    m = Image.new('L', (total, size + 16), 0)
    x = 0
    for g in glyphs:
        if g is None:
            x += wsp + spacing
            continue
        m.paste(g, (x, 0))
        x += g.width + spacing
    bb = m.getbbox()
    return m.crop(bb)


def _band(img, box, seed, fade):
    """ORDER ABOVE ALL sprayed through a stencil in the depot's cream on a band of institutional green between two
    cream rules; the band brushed on, both worn back to the wall in patches and the cream gone thin."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    # the green band (alpha) with ragged ends and wear
    n1 = _noise(W, H, 24, seed, 4)
    n2 = _noise(W, H, 5, seed + 1, 3)
    wear = np.clip((n1 * 0.85 + n2 * 0.15 - (0.24 + fade)) * 5, 0, 1)
    ends = np.clip(np.minimum(xx - 6 - 10 * n2, W - 6 - 10 * n2 - xx) / 8, 0, 1)
    edge = np.clip(np.minimum(yy - 3 - 4 * n2, H - 3 - 4 * n2 - yy) / 2.5, 0, 1)
    band_a = wear * ends * edge * 0.92
    gcol = np.stack([26 + 8 * n2, 40 + 10 * n2, 33 + 8 * n2], -1)
    # cream rules and letters
    rules = ((np.abs(yy - 12) < 2.6) | (np.abs(yy - (H - 13)) < 2.6)).astype(np.float32)
    m = _stencil_mask('ORDER  ABOVE  ALL', 84, 14, 5)
    scale = min((W - 130) / m.width, (H - 44) / m.height)
    m = m.resize((int(m.width * scale), int(m.height * scale)), Image.LANCZOS)
    lay = Image.new('L', (W, H), 0)
    lay.paste(m, ((W - m.width) // 2, (H - m.height) // 2))
    over = lay.filter(ImageFilter.GaussianBlur(2.2))            # the overspray round the letters
    let = np.asarray(lay, np.float32) / 255 * 0.95 + np.asarray(over, np.float32) / 255 * 0.18
    cream_wear = np.clip((_noise(W, H, 22, seed + 2, 4) - (0.2 + fade)) * 3.0, 0, 1) * (0.7 + 0.3 * n2)
    let = np.clip(let, 0, 1) * cream_wear
    rules = rules * cream_wear * ends * 0.85
    cream = np.array([120, 112, 90], np.float32)
    cr_a = np.clip(let + rules, 0, 1)
    rgb = gcol * (1 - cr_a[..., None]) + cream * cr_a[..., None]
    alpha = np.clip(band_a + cr_a * 0.9 * ends, 0, 1)
    # drips and rust streaks from the wall above, through the paint
    for _ in range(14):
        sx = rnd.uniform(10, W - 10)
        w = rnd.uniform(1.5, 4)
        ln = rnd.uniform(0.3, 1.0) * H
        st = np.clip(1 - np.abs(xx - sx) / w, 0, 1) * np.clip(1 - yy / ln, 0, 1)
        rgb = rgb * (1 - st[..., None] * 0.5) + np.array([60, 34, 18], np.float32) * st[..., None] * 0.5
    arr = np.dstack([np.clip(rgb, 0, 255), np.clip(alpha * 255, 0, 255)]).astype(np.uint8)
    img.paste(Image.fromarray(arr, 'RGBA'), (x0, y0))


def _plate(img, box, seed):
    """ORDER ABOVE ALL on a vitreous enamel plate: cream on the Order's dark blue, a cream line round it, four screws;
    chipped to black iron at its edges and screws, rust bled from the chips."""
    rnd = random.Random(seed)
    x0, y0, x1, y1 = box
    W, H = x1 - x0, y1 - y0
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    n = _noise(W, H, 30, seed, 3)
    blue = np.stack([21 + 8 * n, 28 + 10 * n, 48 + 14 * n], -1)
    # the plate's shape (rounded corners) as alpha
    shp = Image.new('L', (W, H), 0)
    ImageDraw.Draw(shp).rounded_rectangle((1, 1, W - 2, H - 2), radius=22, fill=255)
    alpha = np.asarray(shp, np.float32) / 255
    lay = Image.new('L', (W, H), 0)
    ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle((16, 16, W - 17, H - 17), radius=14, outline=255, width=6)
    m = _stencil_mask('ORDER ABOVE ALL', 120, 10, 0)
    sc = min((W - 150) / m.width, (H - 70) / m.height)
    m = m.resize((int(m.width * sc), int(m.height * sc)), Image.LANCZOS)
    lay.paste(m, ((W - m.width) // 2, (H - m.height) // 2 + 2), m)
    let = np.asarray(lay.filter(ImageFilter.GaussianBlur(0.6)), np.float32) / 255
    cream = np.array([196, 188, 160], np.float32) * (0.9 + 0.1 * n[..., None])
    rgb = blue * (1 - let[..., None]) + cream * let[..., None]
    # the gloss's dull sheen, lighter at the top
    rgb = rgb * (1.05 - 0.15 * (yy / H))[..., None]
    # chips: round bites at the edges and screws, a few in the field, black iron with a rust halo
    chip = np.zeros((H, W), np.float32)
    rust = np.zeros((H, W), np.float32)
    screws = [(34, 34), (W - 35, 34), (34, H - 35), (W - 35, H - 35)]
    bites = [(rnd.uniform(0, W), rnd.choice((rnd.uniform(0, 6), rnd.uniform(H - 6, H))), rnd.uniform(5, 13)) for _ in range(6)]
    bites += [(rnd.choice((rnd.uniform(0, 6), rnd.uniform(W - 6, W))), rnd.uniform(0, H), rnd.uniform(5, 12)) for _ in range(2)]
    bites += [(sx + rnd.uniform(-5, 5), sy + rnd.uniform(-5, 5), rnd.uniform(9, 14)) for sx, sy in screws]
    bites += [(rnd.uniform(80, W - 80), rnd.uniform(50, H - 50), rnd.uniform(3, 6)) for _ in range(3)]
    jag = _noise(W, H, 4, seed + 9, 2)
    for bx, by, r in bites:
        dist = np.sqrt((xx - bx) ** 2 + ((yy - by) * 1.1) ** 2) + 9 * (jag - 0.5)
        chip = np.maximum(chip, np.clip((r - dist) / 2, 0, 1))
        rust = np.maximum(rust, np.clip((r * 1.6 - dist) / (r * 0.6), 0, 1) * 0.8)
    for sx, sy in screws:                                   # the screw heads
        dist = np.sqrt((xx - sx) ** 2 + (yy - sy) ** 2)
        chip = np.maximum(chip, np.clip((7 - dist) / 1.5, 0, 1))
    # rust bled down from the chips
    rs = Image.fromarray((rust * 255).astype(np.uint8), 'L').filter(ImageFilter.BoxBlur(2))
    rs = np.asarray(rs, np.float32) / 255
    rdown = rs.copy()
    for k in range(1, 30, 3):
        rdown[k:] = np.maximum(rdown[k:], rs[:-k] * (1 - k / 30) * 0.7)
    rgb = rgb * (1 - rdown[..., None] * 0.55) + np.array([92, 48, 22], np.float32) * rdown[..., None] * 0.55
    iron = np.array([18, 17, 16], np.float32)
    rgb = rgb * (1 - chip[..., None]) + iron * chip[..., None]
    # grime: the plate's lower half and the letters' edges, years of dust
    gr = _noise(W, H, 60, seed + 5, 3)
    rgb = rgb * (1 - 0.5 * gr[..., None] * (0.4 + 0.6 * yy / H)[..., None])
    arr = np.dstack([np.clip(rgb, 0, 255), alpha * 255]).astype(np.uint8)
    img.paste(Image.fromarray(arr, 'RGBA'), (x0, y0))


def make_motto(path):
    img = Image.new('RGBA', (MW, MH), (0, 0, 0, 0))
    _band(img, BAND_A, 9101, 0.0)
    _band(img, BAND_B, 9202, 0.03)
    _plate(img, PLATE, 9303)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True)


# =====================================================================================================================
# Placements (Blender world). Sources: the builders named; each wall face found by ray casts against the built scene.
# =====================================================================================================================

# The portrait: (object, x of its centre, z of its hook, wall ray (y_from, y_cap), note).
#  - DL-05 (art/pass3/build_ration_hall.py): the ration board is x 53.85..55.15 on the grille (y 0.93, z 1.27..1.97);
#    the fascia (RATION ISSUE) is y 0.82.., its underside z 2.20; the counter top 0.95, with things on it to z 1.15
#    at y 0.9; the hacked gap 55.92..56.27; the shutter from x 56.30 (y -0.55..0.72), its box 56.40..56.60. The grille
#    rays pass (bars), so the portrait hangs on the grille's plane (y 0.975), its hook inside the fascia: top 2.15,
#    crest 2.195 (under the fascia), foot 1.17, x 55.39..56.21. The counter's strip lamp (y 0.25, z 2.05) crosses its
#    top rail as the side camera sees it.
#  - DL-10 (art/pass3/build_up_only.py build_waiting): the back wall y 1.2, and a pier (UOShell) x 121.03..121.38
#    standing to y 1.1 the full height; the UP poster x 119.74..120.16, z 3.13..3.97; the departures board 121.9..123.3;
#    TannoyRelocation 120.35..120.75, z 4.20..4.79; the pendant lamp's shade at x 121.35, y 0.2, z 4.07..4.17; the
#    luggage to z 2.87. Hung on the pier, centred (its sides over the wall behind): x 120.79..121.61, z 2.97..3.95,
#    the hook 4.07, under the lamp.
# (object, x, hook z, ray y_from, the wall plane's y if not ray-found, the wall's object, rays' half-width, note)
PORTRAITS = [
    ('StewardPortraitRations', 55.80, 2.27, 0.4, 0.975, 'RationSetWallPanel', 0.36, 'DL-05 over the ration hatch end of the counter'),
    ('StewardPortraitUpOnly', 121.205, 4.07, 0.5, None, 'UOShell', 0.1, "DL-10 Up Only's lobby, on the pier by the UP poster"),
]

# ORDER ABOVE ALL bands: (scene, x centre, z centre, length, variant, ray y_from, the wall's object, note). Height =
# length / 8.
#  - DL-01: the alcove's back wall (art/dl01 build_set: panels y 1.0..1.06, the pipe run at z 2.04 and 2.17 with its
#    brackets from 1.97; the route map x -0.55..0.45 to z 1.61; the dispatch board from x 0.66). The opening's frame
#    shows the wall from x -1.3: the band x -1.25..0.50, z 1.74..1.96, the racking's uprights in front of its left.
#  - DL-02: the sorting hall's back wall (y 1.0) over the tea corner (alcove x 15.35..17.3) and the welded stair door
#    (17.38..18.40, top 2.1); the pigeonholes start at 18.44. The band x 15.0..17.9, z 2.77..3.13 (the side camera's
#    frame top there is ~3.4).
#  - DL-04: the recharge hall's far wall (RechargeHall, face y 9.1) behind the racks: the side camera (height 1.6)
#    sees the racks below its horizon and the row lights' tubes (z 2.58, y 1.6..6.9) against the wall at z 2.8..3.4,
#    so the band goes between them: x 32.6..37.4, z 1.95..2.55, seen past the hall's columns.
#  - DL-06: the sorting floor's wall (SortingWall, face y 1.56) over the postal service poster (66.3..66.9, top 2.13),
#    between the pendant lamps (64.6 and 67.6, y 0.2); EVERYONE UP from 67.40. The band x 65.0..67.3, z 2.39..2.68
#    (the frame's top there is ~2.95).
BANDS = [
    ('DL01', -0.375, 1.85, 1.75, 'A', -0.5, 'AlcoveWalls', 'DL-01 alcove, under the pipe run'),
    ('DL02', 16.45, 2.95, 2.90, 'B', -0.5, 'SortHallWalls', 'DL-02 over the tea corner and the stair door'),
    ('DL04', 35.0, 2.25, 4.80, 'A', -0.5, 'RechargeHall', 'DL-04 far wall over the racks'),
    ('DL06', 66.15, 2.535, 2.30, 'A', 0.5, 'SortingWall', 'DL-06 over the postal service poster'),
]

# The enamel plate on DL-01's hall gantry (art/dl01 build_extension: the deck x 5..17, y 2.1..2.7, z 3.14..3.26; its
# railing posts every metre at y 2.15 (3 cm), z 3.2..3.7, the top rail at z 3.68): hung from the top rail by two
# hooks between the posts at x 6 and 7, clear of the cargo hooks (x 7.7 on).
PLATE_AT = ('DL01', 6.5, 2.128, 3.56, 0.80, 'DL-01 hall gantry railing')   # scene, x, back y, top z, width, note
RAIL = (2.15, 3.68, 0.02)                                                  # the top rail: y, z, half-size

REPORT = []


def game(p):
    return (p[0], p[2], -p[1])


# =====================================================================================================================
# Materials
# =====================================================================================================================

def _image_material(name, path, rough, alpha=False):
    mt = bpy.data.materials.get(name)
    if mt is not None:
        return mt
    mt, nt, bsdf = d17._new_material(name)
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    if alpha:
        nt.links.new(t.outputs['Alpha'], bsdf.inputs['Alpha'])
        for attr, value in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
            if hasattr(mt, attr):
                try:
                    setattr(mt, attr, value)
                except (TypeError, ValueError):
                    pass
    return mt


NEW = {
    # Gilt over red bole: the gold dulled and dirty, chipped through to the bole at the edges and the ornament.
    'GiltFrame': lambda: d17.worn_material('GiltFrame', base=(0.3, 0.21, 0.08), dirt=(0.1, 0.07, 0.032),
                                           chip=(0.2, 0.09, 0.05), rough=0.42, chip_rough=0.8, metallic=0.75,
                                           dust=(0.14, 0.12, 0.09), grime_scale=14, chip_scale=60, chip_amount=0.74,
                                           streaks=0.3, dust_amount=0.6),
    'StewardPortraitMat': lambda: _image_material('StewardPortraitMat', PORTRAIT_PNG, 0.55),
    'OrderMottoMat': lambda: _image_material('OrderMottoMat', MOTTO_PNG, 0.75, alpha=True),
    'Brass': lambda: d17.simple_material('Brass', (0.45, 0.32, 0.12), 0.45, metallic=0.8),
    'Cable': lambda: d17.simple_material('Cable', (0.014, 0.013, 0.012), 0.55),
    'CastIron': lambda: d17.worn_material('CastIron', base=(0.035, 0.034, 0.032), dirt=(0.05, 0.03, 0.018),
                                          chip=(0.13, 0.12, 0.1), rough=0.75, chip_rough=0.45, metallic=0.5),
}


def mat(name):
    m = bpy.data.materials.get(name)
    if m is None:
        m = NEW[name]() if name in NEW else d17.simple_material(name, (0.1, 0.1, 0.1), 0.8)
    return m


class Kit:
    """One bmesh with a UV layer and its materials by name."""
    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.mats = []

    def __call__(self, name):
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def quad(self, pts, name, uv):
        """A quad (corners counter-clockwise as its front sees them) mapped to uv = (u0, v0, u1, v1)."""
        f = self.bm.faces.new([self.bm.verts.new(V(p)) for p in pts])
        f.material_index = self(name)
        u0, v0, u1, v1 = uv
        for lp, t in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
            lp[self.uv].uv = t
        return f

    def mesh(self, name):
        bm = self.bm
        bmesh.ops.remove_doubles(bm, verts=bm.verts[:], dist=1e-6)
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for n in self.mats:
            me.materials.append(mat(n))
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        me.set_sharp_from_angle(angle=math.radians(35))
        return me


def _uv(region, size):
    """A pixel region (x0, y0, x1, y1), y down, of an image size (w, h) -> (u0, v0, u1, v1)."""
    x0, y0, x1, y1 = region
    w, h = size
    return x0 / w, 1 - y1 / h, x1 / w, 1 - y0 / h


# =====================================================================================================================
# Ray casts against the built scene
# =====================================================================================================================

_OURS = set()


def _ray(o, d, dist=20.0, only=None):
    """The first hit from o along d past our own objects, the voices' tannoys and the decals (and, given `only`, past
    everything but the objects named there): (location, object) or (None, None)."""
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    o, d = V(o), V(d).normalized()
    p = o.copy()
    for _ in range(12):
        hit, loc, nrm, idx, ob, mw = sc.ray_cast(dg, p, d, distance=dist - (p - o).length)
        if not hit:
            return None, None
        if ob.name in _OURS or ob.name.startswith(('D17', 'Way', 'Lore', 'Tannoy')) or (only and ob.name not in only):
            p = loc + d * 0.002
            continue
        return loc, ob
    return None, None


def wall_face(x0, x1, z0, z1, y_from, n=4, only=None):
    """The wall's face behind a rectangle: the nearest of a grid of +y rays that agree with their median (thin props
    in front and decals passed; given `only`, everything but those objects), and the names of what was hit."""
    hits = []
    names = set()
    for i in range(n):
        for j in range(3):
            x = x0 + (x1 - x0) * (i + 0.5) / n
            z = z0 + (z1 - z0) * (j + 0.5) / 3
            loc, ob = _ray((x, y_from, z), (0, 1, 0), only=only)
            if loc is not None:
                hits.append(loc.y)
                names.add(ob.name)
    if not hits:
        raise RuntimeError('order_era: no wall at x %.2f..%.2f z %.2f..%.2f' % (x0, x1, z0, z1))
    hits.sort()
    med = hits[len(hits) // 2]
    return min(t for t in hits if med - 0.06 <= t <= med + 0.03), sorted(names)


# =====================================================================================================================
# The Steward's portrait
# =====================================================================================================================

CANVAS_W, CANVAS_H = 0.64, 0.80
MOULD = 0.09                                       # the moulding's width
OUT_W, OUT_H = CANVAS_W + 2 * MOULD, CANVAS_H + 2 * MOULD
TILT = 4.0                                         # degrees: the top leans out from the wall, hung on its cord
HOOK_UP = 0.12                                     # the hook over the frame's top edge
BACK_GAP = 0.012                                   # the foot's back stands this far off the wall
# The moulding's section, (out from the sight edge, out from the back toward the viewer): the sight edge's lip and
# bead, a cove rising to the ridge (the ornament's line), an ogee down to the outer edge, the back.
PROFILE = [(-0.006, 0.006), (-0.002, 0.016), (0.005, 0.024), (0.011, 0.022), (0.016, 0.027), (0.028, 0.036),
           (0.041, 0.049), (0.052, 0.058), (0.064, 0.061), (0.075, 0.056), (0.083, 0.045), (0.089, 0.028),
           (0.09, 0.0), (0.03, 0.0), (-0.006, 0.0)]
RIDGE = (0.064, 0.061)


def portrait_mesh():
    """The portrait in its own frame (origin at the hook on the wall, the wall the plane y = 0, the canvas facing -y):
    the gilt moulding with its beads, corner cartouches and crest, the canvas, the brass plaque, the cord and hook."""
    K = Kit()
    bm = K.bm
    gilt = K('GiltFrame')
    hw, hh = CANVAS_W / 2, CANVAS_H / 2
    # ---- the moulding: one closed ring per profile point, mitred at the corners
    rings = []
    for u, v in PROFILE:
        rings.append([bm.verts.new((sx * (hw + u), -v, sz * (hh + u))) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for i in range(len(rings)):
        a, b = rings[i], rings[(i + 1) % len(rings)]
        for j in range(4):
            f = bm.faces.new((a[j], a[(j + 1) % 4], b[(j + 1) % 4], b[j]))
            f.material_index = gilt
    # ---- beads along the ridge, a cartouche at each corner, a crest on the top rail
    ru, rv = RIDGE
    step = 0.042
    for side in range(4):
        horiz = side in (0, 2)
        half = (hw if horiz else hh) + ru
        n = int((2 * half - 0.2) / step)
        for k in range(n + 1):
            t = -half + 0.1 + k * (2 * half - 0.2) / n
            if horiz:
                p = (t, -rv - 0.003, (hh + ru) * (1 if side == 2 else -1))
                if side == 2 and abs(t) < 0.16:
                    continue                                  # the crest
                if side == 0 and abs(t) < 0.13:
                    continue                                  # the plaque
            else:
                p = ((hw + ru) * (1 if side == 1 else -1), -rv - 0.003, t)
            add_sphere(bm, p, 0.0068, mat=gilt, seg=4, scale=(1, 0.7, 1))
    for sx in (-1, 1):
        for sz in (-1, 1):
            c = V((sx * (hw + ru - 0.004), -rv - 0.006, sz * (hh + ru - 0.004)))
            add_sphere(bm, c, 0.03, mat=gilt, seg=8, scale=(1, 0.55, 1))
            add_sphere(bm, c + V((-sx * 0.055, 0.004, 0)), 0.02, mat=gilt, seg=6, scale=(2.3, 0.5, 0.75))     # leaves
            add_sphere(bm, c + V((0, 0.004, -sz * 0.055)), 0.02, mat=gilt, seg=6, scale=(0.75, 0.5, 2.3))
            add_sphere(bm, c + V((-sx * 0.03, -0.006, -sz * 0.03)), 0.012, mat=gilt, seg=6, scale=(1, 0.6, 1))
    top = hh + ru
    add_sphere(bm, (0, -rv - 0.004, top + 0.012), 0.05, mat=gilt, seg=10, scale=(1.35, 0.4, 0.75))       # the shell
    for k in range(5):                                                                                # its flutes
        a = math.radians(-60 + k * 30)
        add_sphere(bm, (0.045 * math.sin(a), -rv - 0.02, top + 0.012 + 0.02 * math.cos(a)), 0.009, mat=gilt, seg=4,
                   scale=(0.8, 0.6, 1.8))
    for sx in (-1, 1):                                                                                # the scrolls
        add_sphere(bm, (sx * 0.1, -rv - 0.004, top + 0.004), 0.022, mat=gilt, seg=6, scale=(2.4, 0.5, 0.7))
        add_torus(bm, (sx * 0.15, -rv - 0.006, top + 0.008), (0, 1, 0), 0.016, 0.0055, mat=gilt, seg=10, rseg=4)
    # ---- the canvas, just behind the sight edge's lip
    K.quad([(-hw, -0.005, -hh), (hw, -0.005, -hh), (hw, -0.005, hh), (-hw, -0.005, hh)], 'StewardPortraitMat',
           _uv(CANVAS_PX, (PW, PH)))
    # a backing board closing the frame behind the canvas
    bk = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)['verts']
    bmesh.ops.transform(bm, verts=bk, matrix=Matrix.Translation((0, -0.0005, 0)) @ Matrix.Rotation(-math.pi / 2, 4, 'X')
                        @ Matrix.Diagonal((CANVAS_W + 0.02, CANVAS_H + 0.02, 1, 1)))
    for f in {f for v in bk for f in v.link_faces}:
        f.material_index = gilt
    # ---- the plaque on the bottom rail, on a brass backing
    pz = -(hh + 0.046)
    add_box(bm, (0, -0.058, pz), (0.214, 0.006, 0.062), mat=K('Brass'))
    K.quad([(-0.1, -0.0615, pz - 0.025), (0.1, -0.0615, pz - 0.025), (0.1, -0.0615, pz + 0.025), (-0.1, -0.0615, pz + 0.025)],
           'StewardPortraitMat', _uv(PLAQUE_PX, (PW, PH)))
    # ---- hang it: tilt the top out about the foot's back edge, the foot off the wall, the hook at the origin
    a = math.radians(TILT)
    foot = V((0, 0, -(hh + MOULD)))
    drop = OUT_H * math.cos(a) + HOOK_UP
    M = (Matrix.Translation((0, -BACK_GAP, -drop)) @ Matrix.Rotation(a, 4, 'X') @ Matrix.Translation(-foot))
    bmesh.ops.transform(bm, verts=bm.verts[:], matrix=M)
    # ---- the cord: from two screw eyes on the back up to the hook; the hook's plate and nail on the wall
    for sx in (-1, 1):
        eye = M @ V((sx * 0.24, 0.004, hh - 0.1))
        add_cyl(bm, eye, (sx * 0.004, -0.007, -0.012), 0.0022, mat=K('Cable'), seg=5)
    br = K('Brass')
    add_box(bm, (0, -0.003, 0.004), (0.022, 0.004, 0.034), mat=br)
    add_cyl(bm, (0, -0.005, -0.006), (0, -0.016, -0.016), 0.003, mat=br, seg=6)
    add_cyl(bm, (0, -0.002, 0.016), (0, -0.012, 0.012), 0.0035, mat=br, seg=6)                    # the nail
    return K.mesh('StewardPortrait')


def build_portraits(coll):
    me = portrait_mesh()
    obs = []
    for name, x, zh, y_from, y_cap, wall, phw, note in PORTRAITS:
        a = math.radians(TILT)
        z_top = zh - HOOK_UP
        z_foot = z_top - OUT_H * math.cos(a)
        if y_cap is not None:
            y, names = y_cap, ['(the grille plane)']
            yw, wn = wall_face(x - phw, x + phw, z_foot + 0.05, z_top - 0.05, y_from, only=(wall,))
            names = ['grille plane %.3f; wall behind %.3f %s' % (y_cap, yw, wn)]
        else:
            y, names = wall_face(x - phw, x + phw, z_foot + 0.05, z_top - 0.05, y_from, only=(wall,))
            y -= 0.002
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        ob.location = (x, y, zh)
        _OURS.add(ob.name)
        obs.append(ob)
        REPORT.append((name, (x, y, zh), '%s; frame x %.2f..%.2f, z %.2f..%.2f (crest to %.3f); wall %s' % (
            note, x - OUT_W / 2, x + OUT_W / 2, z_foot, z_top, z_top + 0.045, names)))
    return obs


# =====================================================================================================================
# ORDER ABOVE ALL
# =====================================================================================================================

def band(K, x, y, z, length, variant):
    h = length * (BAND_A[3] - BAND_A[1]) / (BAND_A[2] - BAND_A[0])
    region = BAND_A if variant == 'A' else BAND_B
    K.quad([(x - length / 2, y, z - h / 2), (x + length / 2, y, z - h / 2), (x + length / 2, y, z + h / 2),
            (x - length / 2, y, z + h / 2)], 'OrderMottoMat', _uv(region, (MW, MH)))
    return h


def plate(K, x, y, ztop, w):
    """The enamel plate hung from the gantry's top rail by two S-hooks: an iron backing, the enamel face on it."""
    h = w * (PLATE[3] - PLATE[1]) / (PLATE[2] - PLATE[0])
    zc = ztop - h / 2
    ci = K('CastIron')
    add_box(K.bm, (x, y - 0.004, zc), (w - 0.012, 0.008, h - 0.012), mat=ci)
    K.quad([(x - w / 2, y - 0.0095, zc - h / 2), (x + w / 2, y - 0.0095, zc - h / 2), (x + w / 2, y - 0.0095, zc + h / 2),
            (x - w / 2, y - 0.0095, zc + h / 2)], 'OrderMottoMat', _uv(PLATE, (MW, MH)))
    ry, rz, rs = RAIL
    for sx in (-1, 1):
        hx = x + sx * (w / 2 - 0.034)
        # from the plate's top hole up over the rail and down its back: an S-hook of rod
        pts = [V((hx, y - 0.006, ztop - 0.03)), V((hx, y - 0.012, ztop + 0.01)), V((hx, ry - rs - 0.006, rz - 0.02)),
               V((hx, ry - rs - 0.006, rz + rs + 0.004)), V((hx, ry, rz + rs + 0.012)), V((hx, ry + rs + 0.006, rz + rs + 0.004)),
               V((hx, ry + rs + 0.006, rz - 0.01))]
        for p0, p1 in zip(pts, pts[1:]):
            add_cyl(K.bm, p0, p1, 0.0035, mat=ci, seg=6)
    return h


def build_motto(coll):
    by_scene = {}
    for scene, x, z, length, variant, y_from, wall, note in BANDS:
        h = length / 8.0
        y, names = wall_face(x - length / 2 + 0.05, x + length / 2 - 0.05, z - h / 2 + 0.02, z + h / 2 - 0.02, y_from, n=6,
                             only=(wall,))
        y -= 0.004
        K = by_scene.setdefault(scene, Kit())
        hh = band(K, x, y, z, length, variant)
        REPORT.append(('OrderMotto' + scene, (x, y, z), '%s: stencilled band %.2f x %.3f (variant %s), x %.2f..%.2f, '
                       'z %.2f..%.2f; wall %s' % (note, length, hh, variant, x - length / 2, x + length / 2, z - hh / 2,
                                                  z + hh / 2, names)))
    scene, x, y, ztop, w, note = PLATE_AT
    K = by_scene.setdefault(scene, Kit())
    h = plate(K, x, y, ztop, w)
    REPORT.append(('OrderMotto' + scene, (x, y, ztop - h / 2), '%s: enamel plate %.2f x %.3f, x %.2f..%.2f, z %.3f..%.3f' % (
        note, w, h, x - w / 2, x + w / 2, ztop - h, ztop)))
    obs = []
    for scene, K in sorted(by_scene.items()):
        lo = V([min(v.co[i] for v in K.bm.verts) for i in range(3)])
        hi = V([max(v.co[i] for v in K.bm.verts) for i in range(3)])
        c = (lo + hi) / 2                                  # the origin at its bounds' centre (for the game's culling)
        bmesh.ops.translate(K.bm, verts=K.bm.verts[:], vec=-c)
        me = K.mesh('OrderMotto' + scene)
        ob = bpy.data.objects.new('OrderMotto' + scene, me)
        ob.location = c
        coll.objects.link(ob)
        _OURS.add(ob.name)
        obs.append(ob)
    return obs


# =====================================================================================================================
# Entry points
# =====================================================================================================================

def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def report(objs):
    tot = 0
    mats = set()
    for ob in objs:
        t = tris(ob)
        tot += t
        ms = [m.name for m in ob.data.materials]
        mats.update(ms)
        lo = [min((ob.matrix_world @ V(c))[i] for c in ob.bound_box) for i in range(3)]
        hi = [max((ob.matrix_world @ V(c))[i] for c in ob.bound_box) for i in range(3)]
        print('order_era: %-24s mesh %-18s tris %5d draws %d %s  origin (%.3f, %.3f, %.3f) game (%.3f, %.3f, %.3f)  '
              'x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (ob.name, ob.data.name, t, len(ms), ms, *ob.location,
                                                          *game(ob.location), lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    print('order_era: total tris %d (drawn), materials %d %s' % (tot, len(mats), sorted(mats)))
    for name, p, note in REPORT:
        print('order_era: PLACE %-24s blender (%.3f, %.3f, %.3f) game (%.3f, %.3f, %.3f) | %s' % (name, *p, *game(p), note))


def build_set(dl01, m, coll):
    os.makedirs(TEX, exist_ok=True)
    make_portrait(PORTRAIT_PNG)
    make_motto(MOTTO_PNG)
    bpy.context.view_layer.update()
    REPORT.clear()
    objs = build_portraits(coll)
    objs += build_motto(coll)
    bpy.context.view_layer.update()
    report(objs)


def add_clips(dl01, arm):
    pass
