"""Chapter 1, pass 4 (docs/chapter1_pass4_plan.md): story_depot. Built in FINAL world x, after the pass 3 modules.

What happened here, said plainly, in the depot's scenes (DL-01 to DL-05):

  DL-02  The last night shift. The sorters died at their posts, in their aprons: one slumped over the sorting table's
         end under the work lamp (Sorter1), one sitting on the floor against the back wall, knees up, holding
         a mailbag (Sorter2), one over the tea table in the alcove (Sorter3), two side by side at a
         sorting bench under the gantry (Sorter4, Sorter5). Dry, dark remains in clothes, no faces; two meshes
         (seated, sitting) as linked duplicates, each one draw call in the remains atlas (art/pass3, RemainsMat).
  DL-05  The famine and the weigh-in are art/pass3/build_ration_hall.py's (this module only reports them).
  Quest  RING C with an arrow down-and-on, stencilled at each scene's way on (WayRingC01 to WayRingC05); the DL-01
         dispatch board's last line lit, C-114 / RING C / UNDELIVERED, with its lamp (DispatchLineLamp, blinks).
         The parcel label's UNDELIVERED stamp is art/d17/build_d17.py's make_label_texture.

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
from build_d17 import add_box, add_cyl, add_sphere, add_torus, rounded_box
import build_ration_hall as rh

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')

# --------------------------------------------------------------------------
# Layout (shared with the game)
# --------------------------------------------------------------------------
# The sorters: (name, mesh, x, y, z, turn in degrees). The seated pose faces +x with the table's edge 0.46 ahead of
# the origin (the stool's centre on the floor); the sitting one faces +x
# with her back 0.12 behind the origin.
SORTERS = [
    ('Sorter1', 'seated', 18.14, 0.40, 0.0, 0),        # the sorting table's left end (art/sorting_hall TABLE x 18.6)
    ('Sorter2', 'sitting', 17.95, 0.87, 0.0, -90),     # on the floor against the back wall (y 1.0), with the mailbag
    ('Sorter3', 'seated', 16.54, 1.42, -0.03, 180),    # the tea corner: on the crate, over the tea table (x 15.48-16.08)
    ('Sorter4', 'seated', 23.96, 0.16, 0.0, 90),       # under the gantry, at the sorting bench (front edge y 0.62)
    ('Sorter5', 'seated', 24.56, 0.16, 0.0, 90),
]
STOOLS = [(18.14, 0.40), (23.96, 0.16), (24.56, 0.16)]
KNOCKED_STOOL = (23.62, 0.40)                          # on its side, by the bench
BENCH = (23.68, 24.86, 0.62, 0.98, 0.75)               # x0, x1, y0, y1, top: a sorting bench with a case of holes
MAILBAG = (17.95, 0.66, 0.17)                          # on Sorter2's lap, in her arms

# RING C, down and on: (name, x, z) on the first wall behind; the stencil is STENCIL wide and high.
STENCIL = (0.84, 0.42)                                 # as DL-06 to DL-10's (art/pass4 story_shafts, story_ringc)
WAYS = [
    ('WayRingC01', 11.36, 0.94),                       # DL-01: right of the exit door (10.0 to 10.8)
    ('WayRingC02', 24.45, 1.95),                       # DL-02: over the gantry, by the weight room's door (x 25)
    ('WayRingC03', 30.08, 1.86),                       # DL-03: by the gate (30.6), over its linkage
    ('WayRingC04', 47.1, 1.2),                         # DL-04: in the passage past the bay door (46.3 to 46.7)
    ('WayRingC05', 57.32, 2.09),                       # DL-05: in the kitchen past the hatch, over the shelves
]

# The DL-01 dispatch board (art/dl01 build_dispatch_board: centre x 1.05, z 1.72, 0.72 x 0.45, face y 0.968).
BOARD = (1.05, 1.72, 0.72, 0.45, 0.968)
BOARD_LINE = (0.80, 0.97)                              # the lit line's band, as fractions of the board's height from its top
LINE_LAMP = (1.475, 0.958)                             # the lamp's x, y; its z is the line's


def mat(name):
    return rh.mat(name)


# --------------------------------------------------------------------------
# Textures
# --------------------------------------------------------------------------

def _font(size):
    from PIL import ImageFont
    try:
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size)
    except OSError:
        return ImageFont.load_default()


def make_ring_c(path):
    """RING C and an arrow down and on, sprayed through a stencil in the depot's cream: soft overspray, the stencil's
    bridges, the paint thin in places."""
    from PIL import Image, ImageDraw, ImageFilter, ImageChops
    rnd = random.Random(4501)
    w, h = 512, 256
    ink = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(ink)
    f = _font(88)
    text = 'RING C'
    tx, ty = 14, 0
    bb = d.textbbox((0, 0), text, font=f)
    ty = (h - (bb[3] - bb[1])) // 2 - bb[1]
    d.text((tx, ty), text, font=f, fill=255)
    top, bot = ty + bb[1], ty + bb[3]
    # Stencil bridges: the cutter's ties across the closed and curled letters (R's bowl, G and C top and bottom).
    for k, ch in enumerate(text):
        if ch not in 'RGC':
            continue
        x0 = tx + d.textlength(text[:k], font=f)
        cw = d.textlength(ch, font=f)
        if ch == 'R':
            d.rectangle((x0 + cw * 0.5, top, x0 + cw * 0.5 + 6, top + (bot - top) * 0.22), fill=0)
            d.rectangle((x0 + cw * 0.5, top + (bot - top) * 0.36, x0 + cw * 0.5 + 6, top + (bot - top) * 0.52), fill=0)
        else:
            d.rectangle((x0 + cw * 0.5, top - 2, x0 + cw * 0.5 + 6, top + (bot - top) * 0.25), fill=0)
            d.rectangle((x0 + cw * 0.5, bot - (bot - top) * 0.25, x0 + cw * 0.5 + 6, bot + 2), fill=0)
    # The arrow, down and on (toward +x), after the words: a thick shaft from upper left to lower right, a solid head.
    end = tx + d.textlength(text, font=f) + 22
    ax0, ay0 = end, top - 6
    ax1, ay1 = w - 44, bot + 18                             # the head's tip, down and right
    ux, uy = (ax1 - ax0), (ay1 - ay0)
    n = math.hypot(ux, uy)
    ux, uy = ux / n, uy / n
    px, py = -uy, ux
    neck = (ax1 - ux * 46, ay1 - uy * 46)
    d.line((ax0, ay0, neck[0], neck[1]), fill=255, width=24)
    d.polygon([(ax1, ay1), (neck[0] + px * 34, neck[1] + py * 34), (neck[0] - px * 34, neck[1] - py * 34)], fill=255)
    bx, by = neck[0] - ux * 4, neck[1] - uy * 4                # the bridge between shaft and head
    d.line((bx + px * 16, by + py * 16, bx - px * 16, by - py * 16), fill=0, width=6)
    # Under the stencil's edge, the overspray; then the paint's own thin patches.
    spray = ink.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.35))
    holes = Image.new('L', (w, h), 255)
    hd = ImageDraw.Draw(holes)
    for _ in range(160):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(1.5, 7)
        hd.ellipse((x - r, y - r, x + r, y + r), fill=rnd.randint(60, 200))
    paint = ImageChops.multiply(ink.filter(ImageFilter.GaussianBlur(0.8)), holes.filter(ImageFilter.GaussianBlur(1.2)))
    alpha = ImageChops.lighter(paint.point(lambda v: int(v * 0.93)), spray)
    img = Image.new('RGBA', (w, h), (214, 206, 182, 0))
    img.putalpha(alpha)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True)


def make_dispatch_board(dl01, path):
    """DL-01's chalk route board (art/dl01 make_dispatch_board) with its last line along the bottom, lit: an enamel
    line plate, C-114 / RING C / UNDELIVERED, the way the board's other lines were once shown."""
    from PIL import Image, ImageDraw, ImageFilter
    src = path + '.chalk.png'
    dl01.make_dispatch_board(src)
    chalk = Image.open(src).convert('RGB')
    os.remove(src)
    w, h = chalk.size                                               # 768 x 480
    rnd = random.Random(4503)
    img = Image.new('RGB', (w, h), (26, 34, 30))
    d = ImageDraw.Draw(img, 'RGBA')
    for _ in range(60):                                             # the board's own wiped chalk, as the original's
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(30, 120)
        d.ellipse((x - r, y - r * 0.4, x + r, y + r * 0.4), fill=(200, 205, 190, rnd.randint(4, 10)))
    k = BOARD_LINE[0] - 0.02
    sm = chalk.resize((int(w * k), int(h * k)), Image.LANCZOS)      # the chalk, kept in proportion, above the line
    mask = Image.new('L', sm.size, 0)
    ImageDraw.Draw(mask).rectangle((14, 0, sm.size[0] - 14, sm.size[1] - 10), fill=255)
    img.paste(sm, ((w - sm.size[0]) // 2, 0), mask.filter(ImageFilter.GaussianBlur(8)))
    d = ImageDraw.Draw(img, 'RGBA')
    y0, y1 = int(h * BOARD_LINE[0]), int(h * BOARD_LINE[1])
    d.rectangle((0, y0 - 6, w, y1 + 6), fill=(14, 16, 14))                       # the line's slot
    d.rectangle((10, y0, w - 10, y1), fill=(232, 226, 200))                      # its enamel plate, lit from beside
    for x in range(10, w - 10, 3):                                               # the light falling off to the left
        a = int(70 * (1 - (x - 10) / (w - 20)) ** 1.5)
        d.line((x, y0, x, y1), fill=(30, 26, 20, a))
    t = 'C-114 · RING C · UNDELIVERED'
    size = 60
    f = _font(size)
    while f.getlength(t) > w - 60:
        size -= 2
        f = _font(size)
    bb = d.textbbox((0, 0), t, font=f)
    d.text(((w - (bb[2] - bb[0])) / 2 - bb[0], (y0 + y1) / 2 - (bb[3] - bb[1]) / 2 - bb[1]), t, font=f, fill=(24, 22, 20))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.convert('RGB').quantize(48).save(path, optimize=True)


def _image_material(name, path, rough=0.8, alpha=False):
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


# --------------------------------------------------------------------------
# The sorters (DL-02)
# --------------------------------------------------------------------------

V = Vector
SEATED = dict(
    pelvis=V((0.0, 0.0, 0.53)), chest=V((0.29, 0.0, 0.86)),
    shoulder=(V((0.27, 0.17, 0.84)), V((0.27, -0.17, 0.84))),
    neck=V((0.38, 0.0, 0.88)), head=V((0.50, -0.02, 0.865)), face=V((0.3, -0.15, -0.94)),
    # Left forearm on the table under the head; right arm hanging.
    elbow=(V((0.50, 0.22, 0.785)), V((0.28, -0.20, 0.58))),
    wrist=(V((0.56, 0.0, 0.785)), V((0.30, -0.19, 0.34))),
    hand=((V((0.1, -1.0, 0.0)), V((0, 0, 1))), (V((0.08, 0.02, -1.0)), V((1, 0, 0)))),
    hip=(V((0.0, 0.1, 0.50)), V((0.0, -0.1, 0.50))),
    knee=(V((0.40, 0.12, 0.50)), V((0.40, -0.12, 0.49))),
    ankle=(V((0.43, 0.13, 0.10)), V((0.42, -0.13, 0.10))),
    foot=(V((1, 0.05, 0)), V((1, -0.05, 0))),
    skirt=[V((0.06, 0.0, 0.585)), V((0.42, 0.0, 0.585)), V((0.47, 0.0, 0.36))],
)
SITTING = dict(                                        # on the floor, her back to the wall, knees up, head down
    pelvis=V((0.0, 0.0, 0.13)), chest=V((-0.03, 0.0, 0.55)),
    shoulder=(V((-0.02, 0.17, 0.53)), V((-0.02, -0.17, 0.53))),
    neck=V((0.02, 0.0, 0.60)), head=V((0.11, 0.03, 0.61)), face=V((0.6, 0.15, -0.8)),
    # Both arms round the mailbag on her lap.
    elbow=(V((0.10, 0.24, 0.33)), V((0.10, -0.24, 0.33))),
    wrist=(V((0.25, 0.12, 0.42)), V((0.25, -0.12, 0.42))),
    hand=((V((0.3, -0.6, -0.2)), V((0, 0, 1))), (V((0.3, 0.6, -0.2)), V((0, 0, 1)))),
    hip=(V((0.02, 0.1, 0.11)), V((0.02, -0.1, 0.11))),
    knee=(V((0.30, 0.13, 0.43)), V((0.30, -0.12, 0.42))),
    ankle=(V((0.40, 0.13, 0.08)), V((0.41, -0.12, 0.08))),
    foot=(V((1, 0.1, 0)), V((1, -0.1, 0))),
    skirt=[V((0.09, 0.0, 0.17)), V((0.31, 0.0, 0.50))],
)


def _frame(z, y_hint):
    """Columns (x, y, z) for a box whose local z runs along `z` and local y as near `y_hint` as can be."""
    z = z.normalized()
    y = (y_hint - z * y_hint.dot(z))
    if y.length < 1e-6:
        y = Vector((0, 1, 0)) if abs(z.y) < 0.9 else Vector((1, 0, 0))
    y.normalize()
    x = y.cross(z)
    M = Matrix((x, y, z)).transposed().to_4x4()
    return M


def sorter(J):
    """One of the night shift, dead at the post: dry dark bone at the skull and hands, the clothes slack on it, the
    sorter's apron (bib, skirt, ties). One Painted mesh in the remains atlas; no face, no detail that reads as gore."""
    P = rh.Painted()
    pel, ch = J['pelvis'], J['chest']
    sl, sr = J['shoulder']
    up = (ch - pel).normalized()
    lat = (sl - sr)
    lat = (lat - up * lat.dot(up)).normalized()
    fwd = lat.cross(up)
    L = (ch - pel).length
    rot = _frame(up, lat)                                   # local x = forward, y = left, z = up the spine
    mid = (pel + ch) / 2
    # The shirt over the ribs: a slack tapered block; the pelvis; the shoulders.
    P.add('cloth', lambda bm: rounded_box((0.17, 0.29, L + 0.08), mid, p=2.3, cuts=5, taper=lambda z: 0.82 + 0.18 * (z + 1) / 2,
                                          dents=((0.006, 7.0),), seed=1.0, bm=bm, mat=0, rot=rot))
    P.add('cloth', lambda bm: add_sphere(bm, pel, 0.11, mat=0, seg=10, scale=(1.0, 1.3, 0.8)))
    for s in (sl, sr):
        P.add('cloth', lambda bm, s=s: add_sphere(bm, s, 0.05, mat=0, seg=8))
    # The apron: a bib on the chest, its skirt over the lap, its ties round the back in a bow.
    P.add('apron', lambda bm: rounded_box((0.012, 0.25, L * 0.82), mid + fwd * 0.09 - up * 0.02, p=6, cuts=3,
                                          bm=bm, mat=0, rot=rot))
    sk = J['skirt']
    for a, b in zip(sk, sk[1:]):
        dz = (b - a)
        P.add('apron', lambda bm, a=a, b=b, dz=dz: rounded_box((0.012, 0.32, dz.length + 0.02), (a + b) / 2, p=6, cuts=3,
                                                                bm=bm, mat=0, rot=_frame(dz, lat)))
    back = pel - fwd * 0.08 + up * 0.08
    down = Vector((0, 0, -1))
    for s in (1, -1):
        P.add('apron', lambda bm, s=s: add_cyl(bm, pel + lat * s * 0.15 + fwd * 0.04 + up * 0.08, back, 0.006, mat=0, seg=4))
        P.add('apron', lambda bm, s=s: add_cyl(bm, back, back + lat * s * 0.03 + down * 0.11, 0.007, 0.005, mat=0, seg=4))
    P.add('apron', lambda bm: add_sphere(bm, back, 0.016, mat=0, seg=6))
    # The neck and the skull: a dark cranium, the jaw a small block under it.
    P.add('bone', lambda bm: add_cyl(bm, ch, J['neck'], 0.025, 0.022, mat=0, seg=6))
    H, face = J['head'], J['face'].normalized()
    P.add('bone', lambda bm: add_sphere(bm, H, 0.085, mat=0, seg=10, scale=(1.0, 0.88, 1.06)))
    P.add('bone', lambda bm: add_box(bm, H + face * 0.06, (0.05, 0.065, 0.035), mat=0, rot=_frame(face, Vector((0, 0, 1)))))
    P.add('dark', lambda bm: add_sphere(bm, H - face * 0.03, 0.082, mat=0, seg=8, scale=(1.0, 0.9, 0.7)))   # what is left of the hair
    # Arms: sleeves to the wrists, the hands bone, fingers.
    for s in range(2):
        S, E, W = J['shoulder'][s], J['elbow'][s], J['wrist'][s]
        hd, hn = J['hand'][s]
        hd = hd.normalized()
        P.add('cloth', lambda bm, S=S, E=E: add_cyl(bm, S, E, 0.045, 0.038, mat=0, seg=8))
        P.add('cloth', lambda bm, E=E: add_sphere(bm, E, 0.038, mat=0, seg=8))
        P.add('cloth', lambda bm, E=E, W=W: add_cyl(bm, E, W, 0.038, 0.03, mat=0, seg=8))
        P.add('bone', lambda bm, W=W, hd=hd: add_cyl(bm, W - hd * 0.01, W + hd * 0.035, 0.016, 0.018, mat=0, seg=6))
        side = hd.cross(hn.normalized())
        palm = W + hd * 0.065
        P.add('bone', lambda bm, palm=palm, hd=hd, hn=hn: add_box(bm, palm, (0.022, 0.06, 0.07), mat=0, rot=_frame(hd, hn.cross(hd))))
        for f in (-1, 0, 1):
            a = palm + hd * 0.03 + side * f * 0.018
            b = a + hd * 0.05 - hn.normalized() * 0.015
            P.add('bone', lambda bm, a=a, b=b: add_cyl(bm, a, b, 0.006, 0.005, mat=0, seg=4))
    # Legs: trousers, the boots.
    for s in range(2):
        Hp, K, A, fd = J['hip'][s], J['knee'][s], J['ankle'][s], J['foot'][s].normalized()
        P.add('cloth', lambda bm, Hp=Hp, K=K: add_cyl(bm, Hp, K, 0.068, 0.055, mat=0, seg=8))
        P.add('cloth', lambda bm, K=K: add_sphere(bm, K, 0.055, mat=0, seg=8))
        P.add('cloth', lambda bm, K=K, A=A: add_cyl(bm, K, A, 0.05, 0.04, mat=0, seg=8))
        P.add('shoe', lambda bm, A=A, fd=fd: rounded_box((0.25, 0.095, 0.085), A + fd * 0.07 + Vector((0, 0, -0.035)) * (1 if abs(fd.z) < 0.5 else 0),
                                                          p=3.0, cuts=3, bm=bm, mat=0, rot=_frame(fd, Vector((0, 0, 1))) @ Matrix.Rotation(math.pi / 2, 4, 'Y')))
    return P


def build_sorters(coll):
    meshes = {'seated': sorter(SEATED).mesh('SorterRemainsSeated', 'RemainsMat'),
              'sitting': sorter(SITTING).mesh('SorterRemainsSitting', 'RemainsMat')}
    out = []
    for name, kind, x, y, z, turn in SORTERS:
        ob = bpy.data.objects.new(name, meshes[kind])
        coll.objects.link(ob)
        ob.location = (x, y, z)
        ob.rotation_euler = (0, 0, math.radians(turn))
        out.append(ob)
    return out


def stool(wood, steel, c, rot=None):
    """A sorter's stool: round wooden seat at 0.45, three splayed steel legs and a ring. Optionally turned (4x4)."""
    c = Vector(c)
    M = Matrix.Translation(c) @ (rot or Matrix.Identity(4))
    a, b = len(wood.verts), len(steel.verts)
    add_cyl(wood, (0, 0, 0.415), (0, 0, 0.45), 0.15, 0.15, mat=0, seg=16)
    for k in range(3):
        t = 2 * math.pi * k / 3 + 0.4
        add_cyl(steel, (0.07 * math.cos(t), 0.07 * math.sin(t), 0.415), (0.16 * math.cos(t), 0.16 * math.sin(t), 0.0), 0.012, mat=0, seg=6)
    add_torus(steel, (0, 0, 0.16), (0, 0, 1), 0.115, 0.008, mat=0, seg=16, rseg=4)
    bmesh.ops.transform(wood, matrix=M, verts=list(wood.verts)[a:])
    bmesh.ops.transform(steel, matrix=M, verts=list(steel.verts)[b:])


def build_dl02_props(coll):
    """The stools, the knocked one, the sorting bench under the gantry with its case of holes and the post left in
    it, the mailbag in Sorter2's arms with letters spilled from its mouth."""
    rnd = random.Random(4502)
    wood, steel, pig, letters = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    for x, y in STOOLS:
        stool(wood, steel, (x, y, 0.0))
    kx, ky = KNOCKED_STOOL                                  # on its side, legs toward the heap
    stool(wood, steel, (kx, ky, 0.15), Matrix.Rotation(math.radians(-88), 4, 'Y') @ Matrix.Translation((0, 0, -0.225)))
    # The bench: a top on four legs, a case of holes along its back, letters still in some of them.
    x0, x1, y0, y1, top = BENCH
    rounded_box((x1 - x0, y1 - y0, 0.035), Vector(((x0 + x1) / 2, (y0 + y1) / 2, top - 0.0175)), p=6, cuts=3,
                dents=((0.0015, 8.0),), seed=2.0, bm=wood, mat=0)
    for x in (x0 + 0.04, x1 - 0.04):
        for y in (y0 + 0.04, y1 - 0.04):
            add_box(wood, (x, y, (top - 0.035) / 2), (0.04, 0.04, top - 0.035), mat=0)
        add_box(wood, (x, (y0 + y1) / 2, 0.18), (0.03, y1 - y0 - 0.08, 0.03), mat=0)
    cy0, cz1 = 0.80, 1.25
    cols, rows = 6, 3
    add_box(pig, ((x0 + x1) / 2, y1 - 0.01, (top + cz1) / 2), (x1 - x0, 0.02, cz1 - top), mat=0)
    for c in range(cols + 1):
        x = x0 + (x1 - x0) * c / cols
        add_box(pig, (x, (cy0 + y1) / 2, (top + cz1) / 2), (0.018, y1 - cy0, cz1 - top), mat=0)
    for r in range(rows + 1):
        z = top + (cz1 - top) * r / rows
        add_box(pig, ((x0 + x1) / 2, (cy0 + y1) / 2, z + 0.009), (x1 - x0, y1 - cy0, 0.018), mat=0)
    for c in range(cols):
        for r in range(rows):
            if rnd.random() < 0.55:
                x = x0 + (x1 - x0) * (c + 0.5) / cols
                z = top + (cz1 - top) * r / rows + 0.02
                for k in range(rnd.randint(1, 4)):
                    add_box(letters, (x + rnd.uniform(-0.05, 0.05), (cy0 + y1) / 2 + 0.01, z + 0.04),
                            (0.004, 0.13, 0.1), mat=0, rot=Matrix.Rotation(rnd.uniform(-0.3, 0.3), 4, 'Y'))
    for k in range(9):                                      # sorted into heaps on the bench, the last night's
        add_box(letters, (rnd.uniform(x0 + 0.08, x1 - 0.08), rnd.uniform(y0 + 0.03, 0.74), top + 0.003 + 0.004 * k % 3),
                (0.16, 0.11, 0.003), mat=0, rot=Matrix.Rotation(rnd.uniform(-0.5, 0.5), 4, 'Z'))
    # Letters spilled from the mailbag's mouth onto the floor in front of Sorter2.
    mx, my, _ = MAILBAG
    for k in range(10):
        add_box(letters, (mx + 0.25 + rnd.uniform(-0.05, 0.35), my - 0.08 + rnd.uniform(-0.12, 0.1), 0.002 + 0.003 * (k % 3)),
                (0.16, 0.11, 0.003), mat=0, rot=Matrix.Rotation(rnd.uniform(-3, 3), 4, 'Z'))
    d17.mesh_object('StorySortersWood', wood, [mat('CrateWood')], coll)
    d17.mesh_object('StorySortersSteel', steel, [mat('DepotSteel')], coll)
    d17.mesh_object('StorySortersBench', pig, [mat('PigeonWood')], coll)
    d17.mesh_object('StorySortersLetters', letters, [mat('LetterPaper')], coll)
    # The mailbag: canvas, gathered at its neck by a drawstring, a brass tag, lying in her arms.
    P = rh.Painted()
    c = Vector(MAILBAG) + Vector((0, 0, 0.17))
    P.add('bag', lambda bm: rounded_box((0.40, 0.22, 0.26), c, p=2.4, cuts=6, dents=((0.02, 4.0), (0.006, 12.0)), seed=5.0,
                                        bm=bm, mat=0, rot=Matrix.Rotation(0.35, 4, 'Z') @ Matrix.Rotation(0.2, 4, 'X')),
          size=0.4)
    neck = c + Vector((0.2, -0.06, 0.07))
    P.add('bag', lambda bm: add_cyl(bm, c + Vector((0.14, -0.04, 0.05)), neck + Vector((0.08, -0.02, 0.0)), 0.06, 0.035, mat=0, seg=8))
    P.add('rope', lambda bm: add_torus(bm, neck + Vector((0.03, -0.01, 0)), (0.9, -0.2, 0.1), 0.04, 0.006, mat=0, seg=10, rseg=4))
    P.add('rope', lambda bm: add_cyl(bm, neck + Vector((0.05, -0.02, -0.02)), neck + Vector((0.12, -0.08, -0.15)), 0.004, mat=0, seg=4))
    P.add('tag', lambda bm: add_box(bm, neck + Vector((0.14, -0.1, -0.17)), (0.05, 0.004, 0.08), mat=0, rot=Matrix.Rotation(0.4, 4, 'Z')))
    return P.obj('SorterMailbag', 'RemainsMat', coll)


# --------------------------------------------------------------------------
# RING C, the way on (DL-01 to DL-05)
# --------------------------------------------------------------------------

def wall_y(x, z, y0=-0.3, maxd=4.0, skip=('Way', 'Lore', 'Tube', 'Story')):
    """The first surface straight back from the lane (+y) at (x, z), passing thin props and decals."""
    dg = bpy.context.evaluated_depsgraph_get()
    origin = Vector((x, y0, z))
    for _ in range(8):
        hit, loc, nrm, idx, ob, mtx = bpy.context.scene.ray_cast(dg, origin, Vector((0, 1, 0)), distance=maxd)
        if not hit:
            return None
        if ob.name.startswith(skip):
            origin = loc + Vector((0, 0.003, 0))
            continue
        return loc.y
    return None


def build_ways(coll):
    path = os.path.join(TEX, 'ring_c.png')
    if not os.path.exists(path):
        make_ring_c(path)
    mt = _image_material('WayRingCMat', path, rough=0.85, alpha=True)
    bpy.context.view_layer.update()
    out = []
    w, h = STENCIL
    for name, x, z in WAYS:
        hits = sorted(t for t in (wall_y(x + u * w * 0.4, z + v * h * 0.4) for u in (-1, 0, 1) for v in (-1, 0, 1)) if t is not None)
        if not hits:
            print('story_depot: no wall behind', name)
            continue
        med = hits[len(hits) // 2]
        y = min(t for t in hits if med - 0.08 <= t <= med + 0.02) - 0.004
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new('UVMap')
        f = bm.faces.new([bm.verts.new(p) for p in rh._face_quad((0.0, 0.0), w, h, 0.0)])
        for lp, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
            lp[uvl].uv = t
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        me.materials.append(mt)
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        ob.location = (x, y, z)
        out.append(ob)
    return out


# --------------------------------------------------------------------------
# The dispatch board's last line (DL-01)
# --------------------------------------------------------------------------

def build_dispatch_line(dl01, coll):
    path = os.path.join(TEX, 'dispatch_board.png')
    if not os.path.exists(path):
        make_dispatch_board(dl01, path)
    board = bpy.data.materials.get('DispatchBoardMat')
    if board is not None and board.node_tree:
        for n in board.node_tree.nodes:
            if n.type == 'TEX_IMAGE':
                n.image = bpy.data.images.load(path, check_existing=True)
    bx, bz, bw, bh, by = BOARD
    lz = bz + bh / 2 - bh * (BOARD_LINE[0] + BOARD_LINE[1]) / 2
    lx, ly = LINE_LAMP
    # The lamp: a small round bulb in a steel bezel on the wall at the line's right end, a conduit up from it.
    bm = bmesh.new()
    add_cyl(bm, (lx, ly + 0.025, lz), (lx, ly + 0.002, lz), 0.034, 0.03, mat=0, seg=16)
    add_torus(bm, (lx, ly - 0.001, lz), (0, 1, 0), 0.026, 0.005, mat=0, seg=16, rseg=4)
    add_cyl(bm, (lx, ly + 0.018, lz + 0.03), (lx, ly + 0.018, lz + 0.3), 0.008, mat=0, seg=6)
    d17.mesh_object('DispatchLineBezel', bm, [mat('DepotSteel')], coll)
    lamp_mat = bpy.data.materials.get('DispatchLineLamp') or d17.emission_material('DispatchLineLamp', (1.0, 0.62, 0.26), 4.0)
    bm = bmesh.new()
    add_sphere(bm, (0, 0, 0), 0.02, mat=0, seg=12, scale=(1, 0.7, 1))
    lamp = d17.mesh_object('DispatchLineLamp', bm, [lamp_mat], coll)
    lamp.location = (lx, ly - 0.004, lz)
    return lamp


# --------------------------------------------------------------------------

def build_set(dl01, m, coll):
    os.makedirs(TEX, exist_ok=True)
    build_sorters(coll)
    build_dl02_props(coll)
    build_ways(coll)
    build_dispatch_line(dl01, coll)


def add_clips(dl01, arm):
    pass
