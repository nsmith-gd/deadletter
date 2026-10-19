"""DL-05 The Child at the Address: ring C's lane, home C-114 and the child's bedroom, D-17's clips for
the scene, and its lore. Called from art/dl01/build_dl01.py (chapter 1 is one level).

DL-05 runs straight on from the DL-04 balcony stair, on a floor at 0:
  - ring C's ledge, open to the cave behind a low lip of rock;
  - the barricade that seals ring C, with a gap under it to crouch through;
  - ring C's lane: a low rock tunnel of shuttered homes (C-108 to C-112), dead bulbs on a cable and
    a few still burning. The flood of R.Y. 42 is still told on it: a dried tideline at 1.0 m along the
    wall and the facades (and inside C-114), mud below it, and halfway along, a stretch of lane sunk
    into standing water (FloodDip, FloodWater). A length of ventilation duct fell on the lane before it
    (PushDuct, with a red strap): pushed into the water, it is the bridge. Beside the path: C-108's
    window, dimly lit, onto a table still set for a meal; letters jammed in C-110's slot, one sticking
    out (C110Letter); C-112's door taped shut with the water-drop mark; ring C's red mail slot
    (MailSlot9) by C-114;
  - home C-114, its door standing open: the hall with two pairs of shoes and a lamp still on, and the
    child's bedroom: the bed and the patched rabbit, a window painted on the wall and lit from behind,
    the photograph, the forwarding terminal and, behind the fallen desk, the growth marks and the tree;
  - the back door onto a service passage, with the stair up to ring B and the school.

Coordinates as before: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
import build_dl03 as dl03
from build_d17 import (add_box, add_cyl, add_sphere, add_torus, rounded_box, emission_material,
                       worn_material, simple_material, smoothstep, SIDES, CLAW_REST_OPEN)

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')

# Shared with the game (game/undelivered/index.html keeps the same numbers).
BACK_Y = 1.0                          # back walls of the lane, the hall and the bedroom (their faces)
LEDGE = (76.8, 80.0)                  # ring C's ledge, at the foot of the DL-04 balcony stair
LIP = (1.2, 0.34)                     # the rock lip behind the ledge: y, height
BARRICADE = (80.2, 81.0)
GAP = 0.62                            # clear height under the barricade
LANE_C = (81.0, 88.5)
LANE_CEIL = 2.6
DUCT = (81.6, 83.1, 0.26, 0.4)        # PushDuct, lying along the lane at y 0: x0, x1, height, depth (y)
DUCT_GRIP = (-0.775, 0.44)            # its red strap's grip bar: x from the duct's origin, height
DIP = (83.4, 84.9, -0.25)             # FloodDip, across the lane: x0, x1, floor. The duct, pushed in, is the bridge
WATER_Z = -0.1                        # FloodWater's surface
TIDE_Z = 1.0                          # the flood's line, one water level: the lane's wall, the facades, C-108, inside C-114
C108_WIN = (82.6, 0.78, 0.62, 1.58)   # C-108's window, dimly lit: x, width, sill, head (lower than its neighbours')
C110_SLOT = (83.8, 0.98)              # C-110's door slot: x, height
MAILSLOT9 = (87.4, 0.45, 0.55)        # ring C's mail slot on its post: x, post centre y, slot height
KNOCK_X = 88.2
DOOR114 = (88.6, 1.3, 0.36)           # the cross-section wall: x, lintel underside, back jamb (opening y < this)
KNOCK_AT = (88.52, 0.42, 0.57)        # the knock lands on the jamb's face here
HALL = (88.7, 90.6)
INNER = (90.6, 1.25, 0.40)            # the bedroom doorway: x, lintel, back jamb
BEDROOM = (90.65, 95.6)
HOME_CEIL = 2.3
BED = (91.0, 92.5, 0.42, 0.29)        # x0, x1, top, front edge (y)
TOY = (92.2, 0.35, 0.42)              # the rabbit's origin (its base)
TOY_SLUMP = (14.0, 42.0, -24.0)       # its node rotation, slumped (Blender XYZ degrees); upright is identity
SHELF = (92.76, 1.36)                 # the shelf and photograph: x, shelf top (clear of the desk's tall hutch once dragged)
TERM_X, SCREEN_Z, SCREEN = 94.7, 0.95, (0.32, 0.24)
SCREEN_Y = 1.0                        # the screen recess (the game draws the screen) sits in the wall face
READER_Z = 0.72
TERM_FRONT = 0.955                    # the terminal's front face (y); D-17 presents 0.26 m off it
TERM_HOUSING = (94.48, 94.92, 0.62, 1.26)
MARKS = (94.15, 95.25, 0.25, 1.25)      # the growth marks and the tree: x0, x1, z0, z1 (decal on the wall, stain included)
MARK_Z = (0.862, 0.928, 0.991, 1.064, 1.138)   # the five marks, M 2 to M 6: the first three at or under the flood's line
TREE_Z = (0.33, 0.85)                   # the carved tree, under the line: foot, crown
PAINTED_WINDOW = (91.72, 1.36, 0.8, 0.7)   # the window painted over the bed: x, z, width, height
DESK_X, DESK_HALF, DESK_TOP = 94.7, 0.55, 0.55
DESK_Y = 0.62                         # the desk's origin y (centre of its footprint, which runs 0.29 to 0.95)
DESK_TILT = -7.0                      # it leans back against the wall over the terminal (degrees about x)
DESK_SIDE_TILT = 4.0                  # and is down on its broken right side (degrees about y)
DESK_HUTCH = 1.86                     # its hutch: tall enough to hide the marks and the tree
DESK_HANDLE = (-0.585, 0.44)          # its red grip bar, on its left end: x from the origin, height
DESK_DRAG = 93.6                      # where it ends up (left end 93.05, right end 94.15)
BACK_DOOR = (95.6, 1.3, 0.40)
END_X = 97.2
PASSAGE_X1 = 98.5
STAIR_X = 97.6                        # the service stair up toward ring B starts here
WORLD_END = 102.0


def _obj(name, bm, mats, coll, sharp=35):
    return d17.mesh_object(name, bm, mats, coll, sharp=sharp)


_plane = dl03._plane
_font = dl03._font
_age = dl03._age


def _image_material(name, path, rough=0.7, alpha=False):
    mat, nt, bsdf = d17._new_material(name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    if alpha:
        nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
        for attr, value in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
            if hasattr(mat, attr):
                try:
                    setattr(mat, attr, value)
                except (TypeError, ValueError):
                    pass
    return mat


def _tex(name):
    return os.path.join(TEX, name)


def _rz(a):
    return Matrix.Rotation(a, 4, 'Z')


def _rx(a):
    return Matrix.Rotation(a, 4, 'X')


def _ry(a):
    return Matrix.Rotation(a, 4, 'Y')


# --------------------------------------------------------------------------
# Lore: pencil, scratches, paint and an old photograph
# --------------------------------------------------------------------------

def _line(d, pts, fill, width, rnd=None, jitter=0.0, passes=1):
    for _ in range(passes):
        q = [(x + (rnd.uniform(-jitter, jitter) if rnd else 0), y + (rnd.uniform(-jitter, jitter) if rnd else 0)) for x, y in pts]
        d.line(q, fill=fill, width=width, joint='curve')


def _crooked_tree(stroke, ox, oy, s, sx=None):
    """Mara's tree: a crooked trunk, four branches, a knot tied in the right-hand one. Coordinates are in
    a unit box (x right, y down, the trunk's foot at (0, 0)), placed at (ox, oy) with scale s."""
    def P(pts):
        return [(ox + x * (sx or s), oy + y * s) for x, y in pts]
    stroke(P([(0.0, 0.0), (-0.03, -0.14), (0.04, -0.27), (-0.04, -0.42), (0.03, -0.56), (-0.05, -0.72)]), 1.0)
    stroke(P([(-0.12, 0.02), (0.0, 0.0), (0.13, 0.03)]), 0.6)                       # roots
    stroke(P([(-0.02, -0.40), (-0.16, -0.48), (-0.24, -0.62), (-0.33, -0.66)]), 0.7)  # left branch
    stroke(P([(-0.17, -0.50), (-0.13, -0.62)]), 0.45)
    stroke(P([(0.02, -0.52), (0.14, -0.58), (0.2, -0.62)]), 0.7)                    # right branch, to the knot
    knot = [(0.2 + 0.055 * math.cos(a), -0.655 + 0.05 * math.sin(a)) for a in [math.pi * 0.5 + k * math.pi / 7 for k in range(15)]]
    stroke(P(knot), 0.55)                                                            # the loop of the knot
    stroke(P([(0.2, -0.61), (0.27, -0.66), (0.36, -0.7), (0.43, -0.78)]), 0.6)       # and the branch goes on
    stroke(P([(-0.05, -0.72), (-0.03, -0.84), (0.03, -0.93)]), 0.6)                 # crown
    stroke(P([(-0.04, -0.8), (0.1, -0.86)]), 0.4)
    stroke(P([(0.02, -0.25), (0.15, -0.3), (0.22, -0.28)]), 0.5)                    # low branch


def _save(img, name, colors):
    """Lore textures are flat colour: a small palette keeps them light in set.glb."""
    from PIL import Image
    q = img.quantize(colors, method=Image.Quantize.FASTOCTREE if img.mode == 'RGBA' else Image.Quantize.MEDIANCUT)
    if img.mode == 'RGBA':
        q = q.convert('RGBA')             # decals stay true RGBA: some loaders ignore a palette's transparency
    q.save(_tex(name), optimize=True)


def make_textures():
    from PIL import Image, ImageDraw, ImageFilter
    os.makedirs(TEX, exist_ok=True)
    ink, cream, yellow = (26, 24, 20), (222, 212, 184), (196, 168, 60)

    # Door plates: enamel numbers by each door. C-114's has a child's star stuck on it.
    for k, num in enumerate(('108', '110', '112', '114')):
        img = Image.new('RGB', (256, 112), (28, 42, 66))
        d = ImageDraw.Draw(img)
        d.rounded_rectangle((5, 5, 251, 107), radius=16, outline=cream, width=6)
        d.text((134, 57), 'C-' + num, font=_font(58), fill=cream, anchor='mm')
        for x in (20, 236):
            d.ellipse((x - 6, 50, x + 6, 62), fill=(120, 118, 108))
        if num == '114':
            cx, cy = 230, 20
            pts = [(cx + (14 if i % 2 == 0 else 6) * math.sin(i * math.pi / 5), cy - (14 if i % 2 == 0 else 6) * math.cos(i * math.pi / 5))
                   for i in range(10)]
            d.polygon(pts, fill=(226, 186, 60))
        _save(_age(img, 500 + k, 0.7 if num != '114' else 0.4), f'plate_c{num}.png', 24)

    # The seal across ring C.
    img = Image.new('RGB', (768, 300), yellow)
    d = ImageDraw.Draw(img)
    d.rectangle((10, 10, 758, 290), outline=ink, width=12)
    d.text((384, 104), 'RING C SEALED', font=_font(84), fill=ink, anchor='mm')
    d.line((60, 170, 708, 170), fill=ink, width=6)
    d.text((384, 226), 'R.Y. 43', font=_font(64, 'mono-bold'), fill=ink, anchor='mm')
    for x in (34, 734):
        d.ellipse((x - 9, 140, x + 9, 158), fill=(60, 52, 40))
    _save(_age(img, 510, 1.0), 'ringc_sealed.png', 32)

    # Hazard tape, tiled along its strips.
    img = Image.new('RGB', (128, 32), (206, 172, 40))
    d = ImageDraw.Draw(img)
    for k in range(-2, 6):
        x = k * 32
        d.polygon([(x, 32), (x + 16, 32), (x + 48, 0), (x + 32, 0)], fill=(22, 20, 18))
    _save(img.filter(ImageFilter.GaussianBlur(0.6)), 'tape.png', 8)

    # The school sign at the service stair: enamel, an arrow up, the school's mark (a sun over an open book).
    img = Image.new('RGB', (768, 320), (34, 58, 44))
    d = ImageDraw.Draw(img)
    d.rectangle((10, 10, 758, 310), outline=cream, width=10)
    d.polygon([(110, 46), (176, 130), (134, 130), (134, 270), (86, 270), (86, 130), (44, 130)], fill=cream)
    d.text((206, 112), 'SCHOOL', font=_font(80), fill=cream, anchor='lm')
    d.text((212, 228), 'RING B', font=_font(64, 'sans'), fill=(196, 188, 156), anchor='lm')
    mx, my, k = 680, 186, 0.78                                               # the school's mark
    d.pieslice((mx - 44 * k, my - 74 * k, mx + 44 * k, my + 14 * k), 180, 360, fill=(226, 186, 72))
    for a in range(200, 341, 28):
        r = math.radians(a)
        d.line((mx + 54 * k * math.cos(r), my - 30 * k + 54 * k * math.sin(r), mx + 76 * k * math.cos(r), my - 30 * k + 76 * k * math.sin(r)),
               fill=(226, 186, 72), width=6)
    d.polygon([(mx - 70 * k, my - 8 * k), (mx, my + 8 * k), (mx + 70 * k, my - 8 * k), (mx + 70 * k, my + 52 * k), (mx, my + 70 * k),
               (mx - 70 * k, my + 52 * k)], fill=cream)
    d.line((mx, my + 8 * k, mx, my + 70 * k), fill=(34, 58, 44), width=5)
    _save(_age(img, 511, 0.7), 'school_sign.png', 32)

    make_growth_marks()

    # The photograph: a parent kneeling beside a small child, the crooked tree chalked on the wall behind.
    w, h = 300, 380
    g = Image.new('L', (w, h), 120)
    d = ImageDraw.Draw(g)
    for y in range(h):                                                      # wall, then floor
        d.line((0, y, w, y), fill=int(128 - 30 * (y / h)) if y < 300 else int(150 - 40 * ((y - 300) / 80)))
    tree = ImageDraw.Draw(g)

    def chalk(pts, weight):
        tree.line(pts, fill=212, width=max(2, int(5 * weight)), joint='curve')
    _crooked_tree(chalk, 74, 292, 220)
    # The parent, kneeling on one knee and turned toward the child, an arm round her.
    d.polygon([(200, 264), (160, 262), (150, 270), (148, 322), (162, 324), (166, 284), (204, 286)], fill=52)   # raised knee
    d.polygon([(214, 258), (236, 262), (236, 318), (282, 318), (284, 330), (222, 332), (206, 290)], fill=46)   # knee down
    d.polygon([(168, 150), (212, 146), (232, 196), (236, 266), (178, 270), (160, 214)], fill=64)            # coat
    d.line((170, 162, 150, 206, 122, 236), fill=58, width=16, joint='curve')                               # the arm
    d.ellipse((168, 98, 214, 146), fill=40)                                                                # head, hair
    d.ellipse((166, 112, 190, 140), fill=118)                                                              # face, turned to her
    # The child, small, in a pale dress, holding the rabbit.
    d.ellipse((96, 184, 134, 222), fill=36)
    d.ellipse((100, 196, 122, 220), fill=140)
    d.polygon([(100, 220), (132, 220), (146, 290), (86, 290)], fill=168)
    d.rectangle((102, 290, 111, 330), fill=60)
    d.rectangle((121, 290, 130, 330), fill=60)
    d.ellipse((128, 236, 150, 262), fill=196)                                                              # the rabbit
    d.ellipse((130, 218, 138, 240), fill=196)
    d.ellipse((140, 220, 148, 242), fill=196)
    g = g.filter(ImageFilter.GaussianBlur(1.6))
    rnd = random.Random(530)
    px_ = g.load()
    for y in range(h):
        for x in range(w):
            r2 = ((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2
            px_[x, y] = max(0, min(255, int(px_[x, y] * (1.0 - 0.38 * r2) + rnd.uniform(-5, 5))))
    photo = Image.merge('RGB', [g.point(lambda v: min(255, int(v * 1.08 + 18))), g.point(lambda v: int(v * 0.94 + 10)),
                                g.point(lambda v: int(v * 0.74))])
    card = Image.new('RGB', (w + 36, h + 36), (214, 204, 182))
    card.paste(photo, (18, 18))
    d = ImageDraw.Draw(card)
    d.line((w + 36 - 56, 0, w + 36, 52), fill=(186, 176, 152), width=3)     # a bent corner
    _save(_age(card, 531, 0.8), 'photo.png', 48)

    # The painted window: a child's frame, curtains, sky, hills, a flower; the sun and its rays are left
    # unpainted, so the lamp behind shines through them.
    w, h = 512, 448
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rnd = random.Random(540)
    d.rectangle((0, 0, w, h), fill=(150, 196, 226, 255))
    for _ in range(70):                                                     # brush strokes of sky
        x, y = rnd.uniform(0, w), rnd.uniform(0, h * 0.7)
        d.line((x, y, x + rnd.uniform(30, 90), y + rnd.uniform(-6, 6)), fill=(rnd.randint(120, 170), rnd.randint(176, 210), rnd.randint(214, 240), 255),
               width=rnd.randint(6, 14))
    d.pieslice((-80, 300, 300, 560), 180, 360, fill=(110, 160, 80, 255))    # hills
    d.pieslice((180, 320, 620, 600), 180, 360, fill=(90, 146, 70, 255))
    for x in (130, 360):                                                    # flowers
        d.line((x, 400, x + 4, 340), fill=(60, 110, 50, 255), width=5)
        for a in range(0, 360, 60):
            r = math.radians(a)
            d.ellipse((x + 4 + 14 * math.cos(r) - 9, 334 + 14 * math.sin(r) - 9, x + 4 + 14 * math.cos(r) + 9, 334 + 14 * math.sin(r) + 9),
                      fill=(236, 140, 170, 255) if x < 200 else (236, 196, 80, 255))
        d.ellipse((x - 4, 326, x + 12, 342), fill=(250, 220, 90, 255))
    for k in range(3):                                                      # birds
        bx, by = 120 + k * 48, 110 + (k % 2) * 22
        d.line((bx - 14, by - 6, bx, by + 4, bx + 14, by - 6), fill=(50, 60, 80, 255), width=4)
    sx, sy, sr = 372, 120, 52                                               # the sun: cut out, with painted rays
    for k in range(12):
        a = k * math.pi / 6
        p = [(sx + (sr + 10) * math.cos(a - 0.09), sy + (sr + 10) * math.sin(a - 0.09)),
             (sx + (sr + 46) * math.cos(a), sy + (sr + 46) * math.sin(a)),
             (sx + (sr + 10) * math.cos(a + 0.09), sy + (sr + 10) * math.sin(a + 0.09))]
        d.polygon(p, fill=(0, 0, 0, 0))
    d.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=(0, 0, 0, 0))
    d.ellipse((sx - sr - 6, sy - sr - 6, sx + sr + 6, sy + sr + 6), outline=(236, 150, 40, 255), width=7)
    d.ellipse((sx - 22, sy - 16, sx - 10, sy - 4), fill=(200, 110, 30, 255))   # a face painted on the sun
    d.ellipse((sx + 10, sy - 16, sx + 22, sy - 4), fill=(200, 110, 30, 255))
    d.arc((sx - 26, sy - 18, sx + 26, sy + 30), 20, 160, fill=(200, 110, 30, 255), width=6)
    for side in (0, 1):                                                     # curtains with dots, tied back
        x0_, x1_ = (0, 92) if side == 0 else (w - 92, w)
        shape = ([(0, 0), (92, 0), (42, 230), (92, h), (0, h)] if side == 0
                 else [(w - 92, 0), (w, 0), (w, h), (w - 92, h), (w - 42, 230)])
        d.polygon(shape, fill=(222, 150, 160, 255))
        for _ in range(22):
            x, y = rnd.uniform(x0_ + 8, x1_ - 8), rnd.uniform(10, h - 10)
            d.ellipse((x - 5, y - 5, x + 5, y + 5), fill=(250, 236, 224, 255))
        d.line(((x0_ + x1_) / 2 - 20, 236, (x0_ + x1_) / 2 + 20, 226), fill=(240, 200, 80, 255), width=8)
    for xa, ya, xb, yb in ((0, 0, w, 0), (0, h, w, h), (0, 0, 0, h), (w, 0, w, h), (w / 2, 0, w / 2 + 4, h), (0, 196, w, 190)):
        _line(d, [(xa, ya), (xb, yb)], (60, 96, 170, 255), 22, rnd, 3, passes=2)  # the painted frame and bars
    # Where the water reached the painting, below the line it is faded and silted (the sun, high up, never).
    _, pz, _, ph = PAINTED_WINDOW
    line = int(round((pz + ph / 2 - TIDE_Z) / ph * h))
    if line < h:                                                              # (with the line at 1.0 it is all above it)
        _water_stain(img, line, rnd, scale=h / ph)
    _save(img.filter(ImageFilter.GaussianBlur(1.0)), 'window_paint.png', 64)

    # A crayon drawing pinned over the bed: the two of them and the rabbit, under the sun.
    w, h = 384, 288
    img = Image.new('RGB', (w, h), (232, 226, 206))
    d = ImageDraw.Draw(img)
    rnd = random.Random(550)

    def crayon(pts, col, wd=6):
        _line(d, pts, col, wd, rnd, 1.5, passes=2)
    crayon([(0, 238), (w, 232)], (90, 150, 70), 10)
    d.ellipse((300, 24, 352, 76), outline=(236, 180, 40), width=7)
    for k in range(8):
        a = k * math.pi / 4
        crayon([(326 + 34 * math.cos(a), 50 + 34 * math.sin(a)), (326 + 50 * math.cos(a), 50 + 50 * math.sin(a))], (236, 180, 40), 5)
    for cx, top, col in ((130, 70, (60, 80, 150)), (196, 140, (200, 90, 120))):   # a tall one and a small one
        d.ellipse((cx - 18, top, cx + 18, top + 36), outline=col, width=5)
        crayon([(cx, top + 36), (cx, 200)], col)
        crayon([(cx, 200), (cx - 18, 236)], col)
        crayon([(cx, 200), (cx + 18, 236)], col)
    crayon([(130, 120), (196, 170)], (60, 80, 150))                          # holding hands
    d.ellipse((236, 196, 266, 236), outline=(130, 120, 140), width=5)        # the rabbit, ears and a patch
    crayon([(244, 198), (236, 160)], (130, 120, 140), 5)
    crayon([(258, 198), (270, 162)], (130, 120, 140), 5)
    d.rectangle((246, 214, 256, 224), fill=(236, 180, 40))
    crayon([(30, 62), (38, 30), (45, 50), (52, 30), (60, 62)], (60, 80, 150), 5)    # an M, for her name
    px_ = img.load()
    for _ in range(2500):                                                   # crayon tooth
        x, y = rnd.randrange(w), rnd.randrange(h)
        r_, g_, b_ = px_[x, y]
        px_[x, y] = (min(255, r_ + 22), min(255, g_ + 22), min(255, b_ + 20))
    _save(_age(img, 551, 0.5), 'child_drawing.png', 40)

    # The quilt: patchwork, faded.
    img = Image.new('RGB', (256, 256), (200, 190, 166))
    d = ImageDraw.Draw(img)
    rnd = random.Random(560)
    cols = [(150, 170, 196), (214, 196, 150), (196, 160, 90), (150, 176, 140), (210, 160, 160), (226, 220, 200)]
    for i in range(8):
        for j in range(8):
            d.rectangle((i * 32 + 1, j * 32 + 1, i * 32 + 31, j * 32 + 31), fill=rnd.choice(cols))
            if rnd.random() < 0.25:
                d.line((i * 32 + 4, j * 32 + 16, i * 32 + 28, j * 32 + 16), fill=(240, 236, 226), width=2)
    for k in range(9):
        d.line((k * 32, 0, k * 32, 256), fill=(120, 108, 90), width=1)
        d.line((0, k * 32, 256, k * 32), fill=(120, 108, 90), width=1)
    _save(img.filter(ImageFilter.GaussianBlur(0.5)), 'quilt.png', 32)

    # A braided rug.
    img = Image.new('RGB', (256, 160), (40, 36, 30))
    d = ImageDraw.Draw(img)
    for k in range(12):
        col = ((150, 110, 80), (100, 120, 140), (190, 170, 120), (120, 90, 100))[k % 4]
        d.ellipse((4 + k * 10, 4 + k * 6, 252 - k * 10, 156 - k * 6), outline=col, width=7)
    _save(img.filter(ImageFilter.GaussianBlur(0.8)), 'rug.png', 24)

    make_tideline()
    make_drop_mark()


def make_growth_marks():
    """The growth marks and the tree, on the wall behind the desk (D5Marks), with the flood's stain painted in
    under them so they layer in the right order. The water took the early years: M 2 and M 3 are under the
    line, blurred, stained and half lifted but still legible; M 4 sits on the line, the stain's edge across it;
    M 5 and M 6 are crisp above it, with the child's star. The tree, scratched into the plaster below the line,
    survived as a carving does: the stain darkens the wall round it and the grooves read pale through it.
    1 px is about 1.07 mm. The terminal hides the middle (x 94.48 to 94.92), so the marks climb on its left and
    the tree is scratched on its right."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFilter
    x0, x1, z0, z1 = MARKS
    W = 1024
    H = int(round(W * (z1 - z0) / (x1 - x0)))
    ppm = W / (x1 - x0)

    def px(x, z):
        return ((x - x0) * ppm, (z1 - z) * ppm)
    rnd = random.Random(520)
    graphite = (34, 32, 38, 240)
    # The pencil: ticks and labels, on a graphite-coloured transparent ground (so blurring cannot darken it).
    pencil = Image.new('RGBA', (W, H), (34, 32, 38, 0))
    d = ImageDraw.Draw(pencil)
    for k, (age, year, z) in enumerate(zip((2, 3, 4, 5, 6), (38, 39, 40, 41, 42), MARK_Z)):
        a, b = px(94.35, z), px(94.47, z + rnd.uniform(-0.004, 0.004))
        _line(d, [a, b], graphite, 6, rnd, 1.0, passes=2)
        # The label, in a grown-up's pencil, each written a little askew.
        lab = Image.new('RGBA', (200, 52), (34, 32, 38, 0))
        ld = ImageDraw.Draw(lab)
        ld.text((4, 44), f'M {age}', font=_font(38, 'serif'), fill=graphite, anchor='ls')
        ld.text((72, 44), f'R.Y. {year}', font=_font(27, 'sans'), fill=(34, 32, 38, 225), anchor='ls')
        lab = lab.rotate(rnd.uniform(-4, 4), resample=Image.BICUBIC)
        pencil.alpha_composite(lab, (int(a[0] - 168), int(a[1] - 40)))
    sx, sy = px(94.47, MARK_Z[-1])                                          # a child's star by the last one
    d.line((sx + 12, sy - 22, sx + 26, sy + 6, sx + 2, sy - 12, sx + 30, sy - 12, sx + 6, sy + 6, sx + 12, sy - 22),
           fill=(70, 90, 170, 220), width=4)
    # Under the line the pencil is softened, faded and in places lifted with the paint.
    zc = z1 - (np.arange(H)[:, None] + 0.5) / ppm
    xc = x0 + (np.arange(W)[None, :] + 0.5) / ppm
    edge = TIDE_Z + 0.004 * np.sin(xc * 37.0) + 0.003 * np.sin(xc * 91.0 + 1.0)
    under = np.clip((edge - zc) / 0.008, 0, 1)                               # 1 well under the line, 0 above it
    noise = _tile_noise(W, H, 14, 5210)
    keep = np.clip(0.62 + 0.4 * (noise - 0.5), 0.4, 0.85)
    for _ in range(40):                                                      # flakes where the paint lifted
        cx_, cy_ = rnd.uniform(0, W * 0.4), rnd.uniform(*sorted(px(94.3, TIDE_Z)[1:] + px(94.3, 0.8)[1:]))
        r_ = rnd.uniform(3, 9)
        yy, xx = np.ogrid[:H, :W]
        keep = np.where((xx - cx_) ** 2 + (yy - cy_) ** 2 < r_ * r_, keep * 0.35, keep)
    p_sharp = np.asarray(pencil).astype(float)
    p_soft = np.asarray(pencil.filter(ImageFilter.GaussianBlur(2.0))).astype(float)
    p = p_sharp * (1 - under[..., None]) + p_soft * under[..., None]
    p[..., 3] *= 1 - under * (1 - keep)
    pencil = Image.fromarray(np.clip(p, 0, 255).astype('uint8'), 'RGBA')
    # The flood's stain, the same as the wall decal's either side (u = x / 1.6, v = z / 1.28).
    tide = _tide_rgba()
    th_, tw_ = tide.shape[:2]
    tiled = np.concatenate([tide, tide, tide], axis=1)
    c0 = (x0 / TIDE_TEX[0]) % 1.0 * tw_
    c1 = c0 + (x1 - x0) / TIDE_TEX[0] * tw_
    r0, r1 = (1 - z1 / TIDE_TEX[1]) * th_, (1 - z0 / TIDE_TEX[1]) * th_
    stain = Image.fromarray(tiled, 'RGBA').resize((W, H), Image.BICUBIC, box=(c0, r0, c1, r1))
    img = stain.copy()
    img.alpha_composite(pencil)
    veil = np.asarray(stain).astype(float)                                   # the water's film over the pencil it covered
    veil[..., 3] *= 0.35 * under
    img.alpha_composite(Image.fromarray(veil.astype('uint8'), 'RGBA'))
    # The tree: grooves cut into the plaster, pale through the stain.
    grooves = Image.new('RGBA', (W, H), (240, 232, 212, 0))
    d = ImageDraw.Draw(grooves)
    tx, ty = px(95.05, TREE_Z[0])
    ts = (TREE_Z[1] - TREE_Z[0]) / 0.93 * ppm                              # the unit tree is 0.93 tall, roots to crown

    def scratch(pts, weight):
        r = random.Random(int(pts[0][0] * 7 + pts[-1][1]))
        w = max(3, int(8 * weight))
        _line(d, [(x + 3, y + 3) for x, y in pts], (40, 32, 24, 190), w, r, 0.8, passes=2)   # the groove's shadow
        _line(d, pts, (236, 228, 206, 250), max(2, w - 2), r, 1.0, passes=3)              # the scratch itself
    _crooked_tree(scratch, tx, ty, ts, sx=ts * 0.74)
    for k in range(9):                                                      # false starts and stray marks
        x, y = tx + rnd.uniform(-110, 120), ty - rnd.uniform(0.05, 0.9) * ts
        d.line((x, y, x + rnd.uniform(-14, 14), y + rnd.uniform(-10, 10)), fill=(232, 222, 200, 160), width=2)
    img.alpha_composite(grooves)
    _save(img.filter(ImageFilter.GaussianBlur(0.7)), 'growth_marks.png', 64)


def _tile_noise(w, h, cells, seed, octaves=3):
    """Value noise in [0, 1] that tiles along x (cells: lattice cells across the width)."""
    import numpy as np
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w))
    amp, total = 1.0, 0.0
    for o in range(octaves):
        cx = cells * 2 ** o
        cy = max(1, int(round(cx * h / w)))
        lat = rng.random((cy + 2, cx))
        u = np.arange(w) * cx / w
        v = np.arange(h) * cy / h
        i0, fu = u.astype(int), u - u.astype(int)
        j0, fv = v.astype(int), v - v.astype(int)
        fu, fv = fu * fu * (3 - 2 * fu), fv * fv * (3 - 2 * fv)
        i1 = (i0 + 1) % cx
        a = lat[j0][:, i0] * (1 - fu) + lat[j0][:, i1] * fu
        b = lat[j0 + 1][:, i0] * (1 - fu) + lat[j0 + 1][:, i1] * fu
        out += amp * (a * (1 - fv[:, None]) + b * fv[:, None])
        total += amp
        amp *= 0.5
    return out / total


def _water_stain(img, line, rnd, scale):
    """Silt and fading over an RGBA picture below row `line` (the flood's line), with the line itself.
    scale: pixels per metre."""
    import numpy as np
    from PIL import Image
    a = np.asarray(img).astype(float)
    h, w = a.shape[:2]
    n = _tile_noise(w, h, 6, rnd.randint(0, 9999))
    rows = np.arange(h)[:, None]
    below = rows > line + 3 * (n - 0.5)
    silt = np.array([118.0, 100.0, 74.0])
    k = np.clip(0.42 + 0.35 * (n - 0.5) + 0.12 * np.clip((rows - line) / (0.15 * scale), 0, 1), 0, 0.8)
    k = np.where(below, k, 0.0)[..., None]
    grey = a[..., :3].mean(axis=2, keepdims=True)
    faded = a[..., :3] * 0.45 + grey * 0.55
    a[..., :3] = faded * (1 - k) + silt * k * 0.8 + faded * k * 0.2
    band = np.abs(rows - line - 2 * (n - 0.5)) < max(2, 0.01 * scale)
    a[..., :3] = np.where(band[..., None], a[..., :3] * 0.35 + np.array([40, 30, 20]) * 0.65, a[..., :3])
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype('uint8'), 'RGBA'))


TIDE_TEX = (1.6, 1.28)                # the tideline decal's texture tiles 1.6 m along x and covers z 0 to 1.28


_TIDE_CACHE = []


def _tide_rgba():
    """The flood's mark as an RGBA array (512 x 320, u = x / 1.6, v = z / 1.28): a dark ragged line at TIDE_Z
    where the water stood longest, fainter ones below where it paused going down, mottled silt and drips under
    it and caked mud at the foot. Darker and browner than the wall, never lighter: it is read as a change in
    the wall, not as a stripe of light. Shared by the wall decal and the growth marks' texture."""
    if _TIDE_CACHE:
        return _TIDE_CACHE[0]
    import numpy as np
    W, H = 512, 320
    k_z = TIDE_Z / 1.2                                                        # heights below were set for a line at 1.2
    tw, th = TIDE_TEX
    rnd = random.Random(5600)
    zc = (1.0 - (np.arange(H)[:, None] + 0.5) / H) * th                      # each row's height
    xs = np.arange(W)[None, :]
    n1 = _tile_noise(W, H, 8, 5601)
    n2 = _tile_noise(W, H, 24, 5602, octaves=2)
    ragged = (0.0035 * np.sin(2 * np.pi * 3 * xs / W + 0.4) + 0.0025 * np.sin(2 * np.pi * 11 * xs / W + 1.3)
              + 0.004 * (n2[0:1, :] - 0.5))
    top = TIDE_Z + ragged                                                     # the line's upper edge
    under = top - zc                                                          # metres below the line
    alpha = np.zeros((H, W))
    col = np.zeros((H, W, 3))
    silt, dark, mud = np.array([62.0, 51.0, 39.0]), np.array([30.0, 24.0, 18.0]), np.array([50.0, 41.0, 31.0])
    # Mottled silt below the line, a little heavier toward the floor.
    body = under > 0
    a_body = np.clip(0.2 + 0.3 * (n1 - 0.45) + 0.1 * np.clip((TIDE_Z - zc) / TIDE_Z, 0, 1) + 0.08 * (n2 - 0.5), 0.06, 0.5)
    alpha = np.where(body, a_body, alpha)
    col[:] = silt
    # Where the water paused on its way down: fainter lines at 0.88 and 0.62 of the line's height.
    for zl, a_l, wl in ((0.883 * TIDE_Z, 0.18, 0.006), (0.617 * TIDE_Z, 0.14, 0.007)):
        d_l = np.abs(zc - zl - 0.6 * ragged)
        m_l = np.clip(1 - d_l / wl, 0, 1) * a_l
        alpha = np.where(body, np.clip(alpha + m_l, 0, 1), alpha)
    # Drips: dark runs from the line, of every length.
    drip = np.zeros((H, W))
    for _ in range(70):
        x = rnd.randrange(W)
        ln = rnd.uniform(0.04, 0.5) * k_z
        wd = rnd.choice((1, 1, 2, 2, 3))
        strength = rnd.uniform(0.12, 0.3)
        for dx in range(wd):
            xx = (x + dx) % W
            fall = np.clip(1 - under[:, xx] / ln, 0, 1) * (under[:, xx] > 0)
            drip[:, xx] = np.maximum(drip[:, xx], fall * strength)
    alpha = np.where(body, np.clip(alpha + drip, 0, 0.7), alpha)
    col = np.where((drip > 0.02)[..., None], col * 0.75 + dark * 0.25, col)
    # The line itself: dark, about 1.5 cm, crisp on top and softer below.
    band = np.clip(1 - np.maximum(under, 0) / 0.016, 0, 1) * (under > -0.0015)
    band = band * np.clip(0.75 + 0.5 * (n2 - 0.5), 0.5, 0.95)
    alpha = np.maximum(alpha, band * 0.9)
    col = col * (1 - band[..., None]) + dark * band[..., None]
    # Caked mud at the foot, with a ragged top.
    foot = 0.2 * k_z + 0.06 * (n1[0:1, :] - 0.5) * 2 + 0.03 * (n2 - 0.5)
    m_f = np.clip((foot - zc) / 0.05, 0, 1)
    alpha = np.maximum(alpha, m_f * np.clip(0.62 + 0.3 * (n2 - 0.5), 0.4, 0.8))
    col = col * (1 - m_f[..., None]) + mud * m_f[..., None]
    rgba = np.dstack([np.clip(col, 0, 255), np.clip(alpha * 255, 0, 255)]).astype('uint8')
    _TIDE_CACHE.append(rgba)
    return rgba


def make_tideline():
    from PIL import Image, ImageFilter
    img = Image.fromarray(_tide_rgba(), 'RGBA').filter(ImageFilter.GaussianBlur(0.5))
    _save(img, 'tideline.png', 24)


def make_drop_mark():
    """The mark sprayed on C-112's door when ring C was cleared: a water drop over waves, and the year."""
    from PIL import Image, ImageDraw, ImageFilter
    w = h = 256
    img = Image.new('RGBA', (w, h), (214, 208, 176, 0))                       # paint-coloured, so the blur cannot darken it
    d = ImageDraw.Draw(img)
    paint = (214, 208, 176, 235)
    rnd = random.Random(5700)
    cx, cy, r, top = 108, 118, 44, 22                                           # the drop: a point over a round foot
    phi = math.acos(r / (cy - top))
    arc = [(cx + r * math.sin(t), cy - r * math.cos(t)) for t in [phi + (2 * math.pi - 2 * phi) * k / 28 for k in range(29)]]
    d.line([(cx, top)] + arc + [(cx, top)], fill=paint, width=10, joint='curve')
    d.text((206, 112), '42', font=_font(46, 'mono-bold'), fill=paint, anchor='mm')   # the year, stencilled
    for k in range(3):                                                         # waves under it
        y = 184 + k * 20
        wave = [(40 + i * 8, y + 6 * math.sin(i * 0.9 + k)) for i in range(23)]
        d.line(wave, fill=paint, width=8, joint='curve')
    for _ in range(160):                                                       # overspray
        a, rr = rnd.uniform(0, 2 * math.pi), rnd.uniform(40, 120)
        x, y = 124 + rr * math.cos(a), 130 + rr * math.sin(a) * 0.9
        s_ = rnd.uniform(0.6, 1.8)
        d.ellipse((x - s_, y - s_, x + s_, y + s_), fill=(214, 208, 176, rnd.randint(40, 140)))
    for x in (cx - r + 4, cx + r - 6, 70, 190):                                # drips
        y0 = rnd.uniform(150, 230)
        d.line((x, y0, x + rnd.uniform(-1, 1), y0 + rnd.uniform(10, 26)), fill=(214, 208, 176, 170), width=3)
    _save(img.filter(ImageFilter.GaussianBlur(0.8)), 'drop_mark.png', 24)


# --------------------------------------------------------------------------
# The set
# --------------------------------------------------------------------------

def dl05_materials(m):
    m['windowsun'] = emission_material('WindowSun', (1.0, 0.72, 0.38), 0.0)
    m['homelamp'] = emission_material('HomeLampBulb', (1.0, 0.76, 0.46), 0.0)
    m['lanebulb'] = emission_material('LaneBulb', (0.78, 0.88, 1.0), 0.0)
    m['termlamp'] = [emission_material(f'TermLamp{i}', (0.75, 1.0, 0.82), 0.0) for i in range(3)]
    m['rock'] = worn_material('CaveRock', base=(0.05, 0.048, 0.045), dirt=(0.028, 0.026, 0.024),
                              chip=(0.085, 0.08, 0.072), rough=0.95, chip_rough=0.9, metallic=0.0)
    m['homeplaster'] = worn_material('HomePlaster', base=(0.34, 0.29, 0.21), dirt=(0.17, 0.14, 0.1),
                                     chip=(0.24, 0.2, 0.15), rough=0.9, chip_rough=0.85, metallic=0.0)
    m['bedroom'] = worn_material('BedroomPaint', base=(0.46, 0.38, 0.22), dirt=(0.25, 0.2, 0.12),
                                 chip=(0.34, 0.29, 0.21), rough=0.85, chip_rough=0.9, metallic=0.0)
    m['dado'] = worn_material('BedroomDado', base=(0.2, 0.3, 0.26), dirt=(0.1, 0.13, 0.1),
                              chip=(0.34, 0.29, 0.21), rough=0.8, chip_rough=0.9, metallic=0.0)
    m['childpaint'] = worn_material('ChildPaint', base=(0.12, 0.24, 0.42), dirt=(0.06, 0.09, 0.12),
                                    chip=(0.2, 0.14, 0.08), rough=0.6, chip_rough=0.8, metallic=0.0)
    m['toy'] = worn_material('ToyFabric', base=(0.36, 0.33, 0.3), dirt=(0.18, 0.15, 0.12),
                             chip=(0.42, 0.4, 0.36), rough=0.95, chip_rough=0.95, metallic=0.0)
    m['toypatch'] = worn_material('ToyPatch', base=(0.42, 0.3, 0.08), dirt=(0.2, 0.14, 0.05),
                                  chip=(0.3, 0.32, 0.4), rough=0.95, chip_rough=0.95, metallic=0.0)
    m['deadbulb'] = simple_material('DeadBulb', (0.16, 0.16, 0.15), 0.25)
    # The flood: dried silt and mud, the lamp still on over C-108's table, ring C's stamp lamp.
    m['mud'] = worn_material('FloodMud', base=(0.062, 0.05, 0.036), dirt=(0.035, 0.028, 0.02),
                             chip=(0.09, 0.076, 0.058), rough=0.95, chip_rough=0.85, metallic=0.0)
    m['c108lamp'] = emission_material('C108Lamp', (1.0, 0.7, 0.42), 0.0)
    m['slotlamp9'] = emission_material('SlotLamp9', (1.0, 0.62, 0.22), 0.0)


def _rock(bm, center, size, seed, mat=0, cuts=5, p=2.0, rot=None, amp=None):
    a = amp if amp is not None else min(size) * 0.22
    rounded_box(size, center, p=p, cuts=cuts, dents=((a, 2.2), (a * 0.35, 7.0)), seed=seed, mat=mat, bm=bm, rot=rot)


def _rock_sheet(bm, origin, u, v, nu, nv, amp, seed, freq=1.6, thick=0.08, mat=0):
    """A rough rock surface: a grid along u and v, pushed along its normal by noise, given a back."""
    from mathutils import noise
    origin, u, v = Vector(origin), Vector(u), Vector(v)
    n = u.cross(v).normalized()
    grid = []
    for j in range(nv + 1):
        row = []
        for i in range(nu + 1):
            p = origin + u * (i / nu) + v * (j / nv)
            k = noise.noise(p * freq + Vector((seed, seed * 0.7, 0))) + 0.4 * noise.noise(p * freq * 3.1 + Vector((0, seed, seed)))
            row.append(bm.verts.new(p + n * amp * k))
        grid.append(row)
    faces = []
    for j in range(nv):
        for i in range(nu):
            f = bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            f.material_index = mat
            faces.append(f)
    bmesh.ops.solidify(bm, geom=faces, thickness=thick)


def _corrugated(bm, origin, u, v, width, height, pitch=0.09, depth=0.018, mat=0):
    """A corrugated sheet: ridges along v, across width along u."""
    origin, u, v = Vector(origin), Vector(u).normalized(), Vector(v).normalized()
    n = u.cross(v)
    k = max(2, int(round(width / (pitch / 2))))
    bot, top = [], []
    for i in range(k + 1):
        p = origin + u * (width * i / k) + n * (depth / 2 if i % 2 else -depth / 2)
        bot.append(bm.verts.new(p))
        top.append(bm.verts.new(p + v * height))
    faces = []
    for i in range(k):
        f = bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i]))
        f.material_index = mat
        faces.append(f)
    bmesh.ops.solidify(bm, geom=faces, thickness=0.004)


def _cross_wall(bm, x, jamb_y, lintel, top, t=0.12, back=1.12, front=-0.6, mat=0):
    """A wall across the lane with a doorway cut toward the camera: the part behind the opening, and a
    lintel over it. No front post."""
    add_box(bm, (x, (jamb_y + back) / 2, top / 2), (t, back - jamb_y, top), mat=mat)
    add_box(bm, (x, (front + jamb_y) / 2, (lintel + top) / 2), (t, jamb_y - front, top - lintel), mat=mat)


def _door_trim(bm, x, jamb_y, lintel, side=-1, front=-0.6, mat=0):
    """Architrave on one face of a cross wall: the back jamb and the head."""
    fx = x + side * 0.07
    add_box(bm, (fx, jamb_y + 0.05, lintel / 2), (0.025, 0.1, lintel), mat=mat)
    add_box(bm, (fx, (front + jamb_y + 0.1) / 2, lintel + 0.04), (0.025, jamb_y + 0.1 - front, 0.08), mat=mat)


def build_ledge(m, coll):
    """Ring C's ledge at the foot of the balcony stair: paving on a shelf of rock, open to the cave
    behind over a low lip; the rock face the tunnel enters."""
    x0, x1 = LEDGE[0], BARRICADE[0] + 0.05
    bm = bmesh.new()
    add_box(bm, ((x0 + x1) / 2, 0.3, -0.15), (x1 - x0, 2.0, 0.3))
    for k in range(int((x1 - x0) / 0.6)):                                  # paving joints
        add_box(bm, (x0 + 0.6 * (k + 1), 0.3, -0.004), (0.012, 2.0, 0.012))
    _obj('D5Ledge', bm, [m['concrete']], coll)

    bm = bmesh.new()
    rnd = random.Random(5001)
    _rock(bm, (78.4, 0.4, -1.5), (4.6, 2.5, 2.4), 1.0, cuts=4, p=3.0, amp=0.12)       # the shelf under the ledge
    x = x0 - 0.1
    while x < x1:                                                           # the lip, open to the cave behind
        sz = (rnd.uniform(0.5, 0.9), rnd.uniform(0.35, 0.5), rnd.uniform(0.28, 0.46))
        _rock(bm, (x + sz[0] / 2, LIP[0] + 0.12 + rnd.uniform(-0.05, 0.05), sz[2] / 2 - 0.06), sz, rnd.uniform(0, 50), cuts=3)
        x += sz[0] * 0.8
    for cx, cy, s in ((77.3, 1.75, 0.5), (79.1, 1.8, 0.38), (79.9, 1.6, 0.3)):
        _rock(bm, (cx, cy, s * 0.3), (s * 1.4, s, s), cx, cuts=3)
    # Rubble along the lip and a few stones on the paving.
    for k in range(10):
        s = rnd.uniform(0.05, 0.12)
        add_sphere(bm, (rnd.uniform(x0, x1), rnd.choice((rnd.uniform(0.8, 1.05), rnd.uniform(-0.6, -0.4))), s * 0.2), s,
                   seg=6, scale=(1.3, 1, 0.5), dents=(s * 0.2, 9))
    # The cliff the tunnel enters: rock over the barricade and up out of frame, and the portal's pillar.
    _rock(bm, (80.3, 1.45, 1.6), (0.7, 0.7, 3.4), 7.0, cuts=3, p=3.0, amp=0.07)
    _rock_sheet(bm, (79.95, -0.75, 3.0), (22.2, 0, 0), (0, 0, 2.2), 42, 3, 0.08, 3.0)
    add_box(bm, (91.05, 0.45, 4.1), (22.2, 2.4, 2.2))
    _obj('D5Rock', bm, [m['rock']], coll, sharp=75)


def build_barricade(m, coll):
    """Corrugated sheets bolted to posts across the tunnel mouth, from the gap (0.62) up to 3 m: two
    skins across the lane and one facing the camera, braced, signed and taped."""
    b0, b1 = BARRICADE
    top = 3.0
    bm = bmesh.new()                       # mats: 0 sheet, 1 steel, 2 yellow, 3 wood
    rnd = random.Random(5010)
    for x in (b0 + 0.06, b1 - 0.06):                                        # posts, front and back
        for y in (-0.5, 1.08):
            add_box(bm, (x, y, top / 2 + 0.1), (0.08, 0.1, top + 0.2), mat=1)
            add_box(bm, (x, y, 0.01), (0.2, 0.2, 0.02), mat=1)
        add_box(bm, (x, 0.29, GAP + 0.04), (0.09, 1.7, 0.08), mat=2)        # the rails the sheets sit on
        add_box(bm, (x, 0.29, top - 0.05), (0.09, 1.7, 0.08), mat=1)
    for x in (b0 + 0.11, b1 - 0.11):                                        # the two skins across the lane (seen edge on)
        add_box(bm, (x, 0.29, (GAP + 0.08 + top) / 2), (0.02, 1.64, top - GAP - 0.08), mat=0)
    # The face toward the camera: two sheets, a brace, and bolts.
    _corrugated(bm, (b0 - 0.02, -0.53, GAP + 0.08), (1, 0, 0), (0, 0, 1), 0.46, 1.3, mat=0)
    _corrugated(bm, (b0 + 0.4, -0.535, GAP + 0.06), (1, 0, 0), (0.03, 0, 1), 0.46, 1.42, mat=0)
    _corrugated(bm, (b0 - 0.02, -0.54, GAP + 1.32), (1, 0, 0), (-0.02, 0, 1), 0.88, top - GAP - 1.36, mat=0)
    add_box(bm, ((b0 + b1) / 2, -0.565, 1.2), (1.05, 0.04, 0.09), mat=3, rot=_ry(math.radians(28)))
    add_box(bm, ((b0 + b1) / 2, -0.565, 2.4), (1.0, 0.04, 0.09), mat=3, rot=_ry(math.radians(-24)))
    for x in (b0 + 0.06, b1 - 0.06):
        for z in (0.8, 1.4, 2.0, 2.6):
            add_cyl(bm, (x, -0.55, z), (x, -0.575, z), 0.012, seg=6, mat=1)
    # A gap marked under it: a yellow kick plate on the rail and a scuffed patch of floor.
    add_box(bm, ((b0 + b1) / 2, -0.535, GAP + 0.03), (b1 - b0 + 0.06, 0.03, 0.06), mat=2)
    # Sandbags and a crate at the back, left over.
    for k, (x, z) in enumerate(((b0 - 0.35, 0.09), (b0 - 0.05, 0.09), (b0 - 0.2, 0.25))):
        rounded_box((0.36, 0.22, 0.17), (x, 0.92, z), p=2.6, cuts=4, mat=3, bm=bm, dents=((0.01, 8.0),), seed=k)
    _obj('D5Barricade', bm, [m['shutter'], m['steel'], m['yellow'], m['paper']], coll)
    # The sign, and tape across the face.
    _plane('D5BarricadeSign', (0.66, 0.26), ((b0 + b1) / 2, -0.585, 1.62), _image_material('D5SealSignMat', _tex('ringc_sealed.png')), coll,
           rot=_ry(math.radians(-3)) @ _rx(math.radians(90)))
    tape = _image_material('D5TapeMat', _tex('tape.png'), rough=0.5)
    for k, (z, a, ln) in enumerate(((1.12, 8, 1.0), (1.98, -14, 1.02), (2.2, 10, 0.98))):
        _plane(f'D5BarricadeTape{k}', (ln, 0.06), ((b0 + b1) / 2, -0.59 - 0.002 * k, z), tape, coll,
               rot=_ry(math.radians(a)) @ _rx(math.radians(90)), uv_repeat=(ln / 0.24, 1))


def _obj_at(name, bm, mats, coll, origin, sharp=35):
    """A mesh object built in set coordinates, with its origin moved to `origin`."""
    bmesh.ops.translate(bm, vec=-Vector(origin), verts=bm.verts)
    ob = _obj(name, bm, mats, coll, sharp=sharp)
    ob.location = origin
    return ob


def _mud_patches(name, patches, mat, coll, seed):
    """Dried mud on a floor: flat ragged patches (x, y, z, radius), 2 mm proud, facing up."""
    rnd = random.Random(seed)
    verts, faces = [], []
    for x, y, z, r in patches:
        base, ring = len(verts), []
        rot, sx = rnd.uniform(0, math.pi), rnd.uniform(1.2, 1.7)
        for k in range(9):
            a = 2 * math.pi * k / 9
            rr = r * rnd.uniform(0.7, 1.05)
            u, v = rr * sx * math.cos(a), rr * math.sin(a)
            verts.append((x + u * math.cos(rot) - v * math.sin(rot), y + u * math.sin(rot) + v * math.cos(rot), z + 0.002))
            ring.append(base + k)
        faces.append(tuple(ring))
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def build_ring_c(m, coll):
    """Ring C's lane: the floor (broken by the flood dip), a low rock tunnel, three shuttered homes on the
    back wall with their plates, a cable of bulbs (two still burning), and the duct run under the roof
    with the gap where a length fell. C-108's window is open and dimly lit onto a table set for a meal;
    C-110's slot is jammed with letters, one sticking out; C-112 is taped shut with the water-drop mark."""
    l0, l1 = BARRICADE[0], DOOR114[0]
    d0, d1, _ = DIP
    bm = bmesh.new()
    for a, b in ((l0, d0), (d1, l1)):                                       # the lane floor, either side of the dip
        add_box(bm, ((a + b) / 2, 0.2, -0.15), (b - a, 1.9, 0.3))
        add_box(bm, ((a + b) / 2, 0.86, 0.004), (b - a, 0.06, 0.008))     # a drain channel's grating along the wall
    add_box(bm, ((BACK_DOOR[0] + WORLD_END) / 2, 0.2, -0.15), (WORLD_END - BACK_DOOR[0], 1.9, 0.3))
    _obj('D5Lane', bm, [m['concrete']], coll)
    # The tunnel: a rough rock roof at 2.6 over the lane, and the step up to the portal over the barricade.
    bm = bmesh.new()
    _rock_sheet(bm, (LANE_C[0] - 0.05, -0.75, LANE_CEIL), (l1 - LANE_C[0] + 0.1, 0, 0), (0, 1.95, 0), 24, 4, -0.06, 11.0)
    _rock_sheet(bm, (BARRICADE[0] - 0.15, -0.75, 3.0), (LANE_C[0] - BARRICADE[0] + 0.15, 0, 0), (0, 1.95, 0), 2, 4, -0.05, 12.0)
    _rock_sheet(bm, (LANE_C[0] - 0.05, -0.75, LANE_CEIL), (l1 - LANE_C[0] + 0.1, 0, 0), (0, 0, 0.45), 24, 1, 0.05, 13.0)
    _obj('D5Tunnel', bm, [m['rock']], coll, sharp=75)

    # The back wall and the homes along it. C-108's window (lower than the others) is cut through the wall.
    bm = bmesh.new()                       # mats: 0 wall, 1 trim, 2 shutter, 3 wood, 4 slats
    cw, cww, cz0, cz1 = C108_WIN
    wa, wb = cw - cww / 2, cw + cww / 2
    for a, b in ((LANE_C[0], wa), (wb, 87.2)):
        add_box(bm, ((a + b) / 2, BACK_Y + 0.08, LANE_CEIL / 2), (b - a, 0.16, LANE_CEIL))
    add_box(bm, (cw, BACK_Y + 0.08, cz0 / 2), (cww, 0.16, cz0))
    add_box(bm, (cw, BACK_Y + 0.08, (cz1 + LANE_CEIL) / 2), (cww, 0.16, LANE_CEIL - cz1))
    homes = (('108', 81.15, 'shutter'), ('110', 83.2, 'door'), ('112', 85.25, 'taped'))
    rnd = random.Random(5015)
    for num, a, kind in homes:
        dx, wx = a + 0.6, a + 1.45                                          # door and window centres
        add_box(bm, (a - 0.05, BACK_Y - 0.03, LANE_CEIL / 2), (0.14, 0.08, LANE_CEIL), mat=1)       # pilaster
        for sx in (-1, 1):                                                  # door frame
            add_box(bm, (dx + sx * 0.45, BACK_Y - 0.02, 1.0), (0.08, 0.06, 2.0), mat=1)
        add_box(bm, (dx, BACK_Y - 0.02, 2.02), (0.98, 0.06, 0.1), mat=1)
        if num == '110':                                                    # its threshold stood; the lane sank round it
            add_box(bm, (dx, BACK_Y - 0.06, (DIP[2] - 0.05 + 0.05) / 2), (0.95, 0.14, 0.05 - DIP[2] + 0.05), mat=1)
        else:
            add_box(bm, (dx, BACK_Y - 0.06, 0.025), (0.95, 0.14, 0.05), mat=1)   # doorstep
        if kind == 'shutter':                                               # a roller shutter, down
            for k in range(14):
                add_box(bm, (dx, BACK_Y + 0.004 - 0.003 * (k % 2), 0.07 + k * 0.132), (0.82, 0.02, 0.132), mat=2)
            add_box(bm, (dx, BACK_Y - 0.04, 1.93), (0.86, 0.1, 0.12), mat=2)
        else:                                                               # a wooden door, shut
            add_box(bm, (dx, BACK_Y + 0.01, 0.98), (0.82, 0.03, 1.96), mat=3)
            for z in (0.5, 1.35):
                add_box(bm, (dx, BACK_Y - 0.008, z), (0.6, 0.012, 0.6), mat=3)
            add_box(bm, (dx, BACK_Y - 0.01, C110_SLOT[1]), (0.2, 0.02, 0.04), mat=1)       # the letter slot
            add_sphere(bm, (dx + 0.32, BACK_Y - 0.03, 0.95), 0.025, seg=10, mat=1)
        if num == '108':                                                    # its window, low, the shutter broken open
            for sx in (-1, 1):
                add_box(bm, (wx + sx * 0.39, BACK_Y - 0.02, (cz0 + cz1) / 2), (0.06, 0.06, cz1 - cz0 + 0.04), mat=1)
            add_box(bm, (wx, BACK_Y - 0.04, cz0 - 0.025), (0.86, 0.1, 0.05), mat=1)
            add_box(bm, (wx, BACK_Y - 0.03, cz1 + 0.025), (0.86, 0.06, 0.05), mat=1)
            for k, (z, tilt, yaw) in enumerate(((cz1 - 0.05, -30, 0.0), (cz1 - 0.14, -12, 0.06), (cz1 - 0.24, 25, -0.1))):
                ln = 0.72 if k == 0 else 0.5 - 0.1 * k
                add_box(bm, (wx - 0.36 + ln / 2 + (0.0 if k == 0 else 0.03), BACK_Y - 0.03, z), (ln, 0.012, 0.078), mat=4,
                        rot=_rz(yaw) @ _ry(math.radians(4 * k)) @ _rx(math.radians(tilt)))
            continue
        for sx in (-1, 1):                                                  # window frame and a shutter, closed
            add_box(bm, (wx + sx * 0.39, BACK_Y - 0.02, 1.38), (0.06, 0.06, 0.8), mat=1)
        for z in (0.97, 1.79):
            add_box(bm, (wx, BACK_Y - 0.03, z), (0.86, 0.08 if z < 1 else 0.06, 0.05), mat=1)
        for k in range(8):
            add_box(bm, (wx, BACK_Y - 0.005, 1.04 + k * 0.092), (0.72, 0.012, 0.078), mat=4,
                    rot=_rx(math.radians(-30)))
    _obj('D5Homes', bm, [m['wall'], m['concrete'], m['shutter'], m['pigeon'], m['depot_green']], coll)
    for num, a, kind in homes:
        _plane(f'D5Plate{num}', (0.26, 0.114), (a + 1.06, BACK_Y - 0.052, 1.5), _image_material(f'D5Plate{num}Mat', _tex(f'plate_c{num}.png'), rough=0.3), coll)
    build_c108_room(m, coll)

    # Letters jammed in C-110's slot, more fallen on its threshold and on the lane short of the water, and
    # the one sticking out, which he can pull free (C110Letter).
    sx_, sz_ = C110_SLOT
    bm = bmesh.new()
    rnd = random.Random(5020)
    for k in range(5):
        add_box(bm, (sx_ + rnd.uniform(-0.07, 0.07), BACK_Y - 0.03, sz_ + 0.01 + k * 0.004), (0.16, 0.04, 0.003),
                rot=_rz(rnd.uniform(-0.15, 0.15)) @ _rx(math.radians(rnd.uniform(-20, 10))))
    for k in range(3):                                                        # on the threshold
        add_box(bm, (sx_ + rnd.uniform(-0.3, 0.3), BACK_Y - 0.075 + rnd.uniform(-0.02, 0.02), 0.052 + k * 0.002), (0.16, 0.11, 0.003),
                rot=_rz(rnd.uniform(-0.3, 0.3)))
    for k in range(4):                                                        # washed up short of the dip
        add_box(bm, (DIP[0] - rnd.uniform(0.12, 0.5), rnd.uniform(0.45, 0.85), 0.003 + k * 0.002), (0.16, 0.11, 0.003),
                rot=_rz(rnd.uniform(0, 3)))
    _obj('D5Letters', bm, [m['letters']], coll)
    build_c110_letter(m, coll)

    # C-112: taped shut, and the water-drop mark sprayed on its door above the tape.
    tape = bpy.data.materials['D5TapeMat']
    for k, a in enumerate((32, -32)):
        _plane(f'D5DoorTape{k}', (1.25, 0.06), (85.85, BACK_Y - 0.04 - 0.002 * k, 1.0), tape, coll,
               rot=_ry(math.radians(a)) @ _rx(math.radians(90)), uv_repeat=(5, 1))
    _plane('D5DropMark112', (0.34, 0.34), (85.85, BACK_Y - 0.016, 1.46),
           _image_material('D5DropMarkMat', _tex('drop_mark.png'), rough=0.6, alpha=True), coll,
           rot=_ry(math.radians(-3)) @ _rx(math.radians(90)))
    bm = bmesh.new()
    add_cyl(bm, (81.45, 0.85, 0.0), (81.45, 0.85, 0.22), 0.09, 0.12, seg=12)
    _obj('D5PlantPot', bm, [m['concrete']], coll)
    bm = bmesh.new()
    for k in range(6):
        a = k * 1.1
        add_cyl(bm, (81.45, 0.85, 0.2), (81.45 + 0.12 * math.cos(a), 0.85 + 0.08 * math.sin(a), 0.42 + 0.1 * (k % 3)), 0.004, seg=4)
    _obj('D5PlantDead', bm, [m['wood']], coll)

    # The cable of bulbs: hooks under the roof, a sagging cable, bulbs on drops. Ring C has been dark since
    # R.Y. 43: only two still burn, far apart, one inside the seal and one near C-114 (the LaneBulb object).
    hooks = [81.1, 83.15, 85.2, 87.2, 88.45]
    cy = 0.5
    bm, live, dead = bmesh.new(), bmesh.new(), bmesh.new()

    def cable_z(x):
        for a, b in zip(hooks, hooks[1:]):
            if a <= x <= b:
                t = (x - a) / (b - a)
                return 2.5 - 0.16 * math.sin(math.pi * t)
        return 2.5
    for a, b in zip(hooks, hooks[1:]):
        pts = [a + (b - a) * k / 5 for k in range(6)]
        for p, q in zip(pts, pts[1:]):
            add_cyl(bm, (p, cy, cable_z(p)), (q, cy, cable_z(q)), 0.006, seg=4)
    for x in hooks:
        add_cyl(bm, (x, cy, 2.5), (x, cy, LANE_CEIL + 0.02), 0.008, seg=5)
    bulbs = [(81.65, True), (82.55, False), (83.75, False), (84.75, False), (85.75, False), (86.6, True), (87.75, False)]
    for k, (x, lit) in enumerate(bulbs):
        z0 = cable_z(x)
        z1 = z0 - 0.22 - 0.06 * (k % 2)
        tilt = 0.06 if k == 4 else 0.0                                      # one hangs broken, askew
        add_cyl(bm, (x, cy, z0), (x + tilt, cy, z1), 0.004, seg=4)
        add_cyl(bm, (x + tilt, cy, z1), (x + tilt, cy, z1 - 0.05), 0.018, seg=8)
        add_sphere(live if lit else dead, (x + tilt * 1.1, cy, z1 - 0.085), 0.034, seg=8, scale=(1, 1, 1.2))
    _obj('D5Cable', bm, [m['rubber']], coll)
    _obj('LaneBulb', live, [m['lanebulb']], coll)
    _obj('D5DeadBulbs', dead, [m['deadbulb']], coll)

    # The duct run under the roof, broken over the stretch where a length came down (PushDuct, below it).
    bm = bmesh.new()
    dy, dz = 0.74, 2.32
    g0, g1 = DUCT[0] - 0.15, DUCT[1] + 0.15
    for a, b in ((LANE_C[0], g0), (g1, l1 - 0.1)):
        add_box(bm, ((a + b) / 2, dy, dz), (b - a, DUCT[3] - 0.024, DUCT[2] - 0.012))
        x = a + 0.4 if a > LANE_C[0] else a + 0.2
        while x < b:
            add_box(bm, (x, dy, dz), (0.03, DUCT[3], DUCT[2]))
            add_cyl(bm, (x, dy, dz + 0.13), (x, dy, LANE_CEIL + 0.05), 0.006, seg=4)
            x += 1.2
    for x, sgn in ((g0, 1), (g1, -1)):                                          # torn ends, bent down
        add_box(bm, (x + sgn * 0.05, dy - 0.06, dz - 0.15), (0.06, 0.28, 0.12), rot=_ry(sgn * 0.6))
        add_box(bm, (x + sgn * 0.04, dy + 0.12, dz - 0.12), (0.05, 0.1, 0.1), rot=_ry(sgn * 0.9) @ _rx(0.4))
    for x, ln in ((81.95, 0.5), (82.85, 0.36)):                                  # the hangers that let go
        add_box(bm, (x, dy, LANE_CEIL - ln / 2), (0.02, 0.004, ln), rot=_ry(0.12 if x < 82.4 else -0.2))
    _obj('D5DuctRun', bm, [m['plate']], coll)


def build_c108_room(m, coll):
    """Behind C-108's window: a small room, the lamp over the table still on, dimly, and the table set for
    a meal nobody came back to. The water stood over it too: the cloth is silted, a cup lies where it
    floated, the floor is mud; the plates stayed put."""
    cw, cww, cz0, cz1 = C108_WIN
    rx0, rx1, ry0, ry1 = cw - 0.62, cw + 0.62, BACK_Y + 0.16, 2.25
    bm = bmesh.new()                       # mats: 0 plaster, 1 floorboards
    add_box(bm, ((rx0 + rx1) / 2, ry1 + 0.06, 1.15), (rx1 - rx0 + 0.24, 0.12, 2.3))
    for x in (rx0 - 0.06, rx1 + 0.06):
        add_box(bm, (x, (ry0 + ry1) / 2, 1.15), (0.12, ry1 - ry0, 2.3))
    add_box(bm, ((rx0 + rx1) / 2, (ry0 + ry1) / 2, -0.03), (rx1 - rx0, ry1 - ry0, 0.06), mat=1)
    add_box(bm, ((rx0 + rx1) / 2, (ry0 + ry1) / 2, 2.3), (rx1 - rx0, ry1 - ry0, 0.08))
    _obj('D5Home108Room', bm, [m['homeplaster'], m['pigeon']], coll)
    tx, ty, top = cw, 1.72, 0.74
    bm = bmesh.new()                       # mats: 0 wood, 1 crockery, 2 cloth, 3 steel
    add_box(bm, (tx, ty, top - 0.02), (0.92, 0.66, 0.04))
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_box(bm, (tx + sx * 0.41, ty + sy * 0.28, (top - 0.04) / 2), (0.045, 0.045, top - 0.04))
    add_box(bm, (tx, ty, top + 0.003), (0.96, 0.7, 0.006), mat=2)                  # the cloth, and its front drop
    add_box(bm, (tx, ty - 0.35, top - 0.06), (0.96, 0.006, 0.12), mat=2)
    rnd = random.Random(5080)
    places = ((tx - 0.24, ty - 0.17, 0.1), (tx + 0.24, ty - 0.17, 0.1), (tx, ty + 0.18, 0.075))   # two grown-ups, one small
    for k, (px_, py_, r) in enumerate(places):
        add_cyl(bm, (px_, py_, top + 0.006), (px_, py_, top + 0.022), r, r * 0.8, seg=14, mat=1)
        add_box(bm, (px_ - r - 0.03, py_, top + 0.009), (0.012, 0.15, 0.004), mat=3)              # fork and knife
        add_box(bm, (px_ + r + 0.03, py_, top + 0.009), (0.012, 0.16, 0.004), mat=3)
        if k != 1:                                                                                  # cups
            cx_, cy_ = px_ + r + 0.08, py_ + 0.1
            add_cyl(bm, (cx_, cy_, top + 0.006), (cx_, cy_, top + 0.08), 0.032, 0.036, seg=8, mat=1)
            add_torus(bm, (cx_ + 0.04, cy_, top + 0.045), (0, 1, 0), 0.018, 0.005, seg=6, rseg=3, mat=1)
    cx_, cy_ = tx + 0.36, ty - 0.02                                                                 # the third, floated and tipped
    p0 = Vector((cx_, cy_, top + 0.04))
    add_cyl(bm, p0 - Vector((0.036, 0.012, 0)), p0 + Vector((0.036, 0.012, 0)), 0.034, 0.03, seg=8, mat=1)
    add_cyl(bm, (tx - 0.02, ty + 0.0, top + 0.006), (tx - 0.02, ty, top + 0.17), 0.055, 0.042, seg=10, mat=1)   # the jug
    add_torus(bm, (tx - 0.085, ty, top + 0.1), (0, 1, 0), 0.035, 0.007, seg=6, rseg=3, mat=1)
    add_cyl(bm, (tx + 0.12, ty + 0.05, top + 0.006), (tx + 0.12, ty + 0.05, top + 0.025), 0.09, seg=10, mat=0)     # a bread board
    for k, (x, y, ang) in enumerate(((tx - 0.3, ty + 0.46, 0.0), (tx + 0.3, ty + 0.46, 0.1), (tx + 0.02, ty - 0.32, math.pi - 0.25))):
        rot = _rz(ang)                                                       # chairs: two at the far side, one pulled out
        c = Vector((x, y, 0))
        add_box(bm, c + rot @ Vector((0, 0, 0.44)), (0.4, 0.38, 0.03), rot=rot)
        for sx in (-1, 1):                                                   # back posts to the floor; the front legs
            add_box(bm, c + rot @ Vector((sx * 0.17, 0.17, 0.46)), (0.03, 0.03, 0.92), rot=rot)   # are never seen past the sill
            add_box(bm, c + rot @ Vector((sx * 0.17, -0.16, 0.22)), (0.03, 0.03, 0.44), rot=rot)
        add_box(bm, c + rot @ Vector((0, 0.17, 0.84)), (0.38, 0.025, 0.08), rot=rot)
    # The lamp over the table: a cord from the ceiling, an enamel shade.
    lz = 1.5
    add_cyl(bm, (tx, ty, 2.26), (tx, ty, lz + 0.1), 0.004, seg=4, mat=3)
    add_cyl(bm, (tx, ty, lz + 0.1), (tx, ty, lz - 0.02), 0.04, 0.17, seg=12, mat=1)
    _obj('D5Table108', bm, [m['wood'], m['letters'], m['paper'], m['steel']], coll, sharp=50)
    bm = bmesh.new()
    add_sphere(bm, (tx, ty, lz + 0.0), 0.03, seg=10)
    _obj('C108Lamp', bm, [m['c108lamp']], coll)
    _mud_patches('D5Mud108', [(tx + rnd.uniform(-0.45, 0.45), rnd.uniform(1.3, 2.1), 0.0, rnd.uniform(0.14, 0.24)) for _ in range(4)],
                 m['mud'], coll, 5081)


LETTER_C110_TEX = os.path.join(HERE, '..', 'sorting_hall', 'textures', 'letter_c110.png')   # painted by the Sorting Hall module


def build_c110_letter(m, coll):
    """The letter sticking out of C-110's slot, drooping, its face to the lane: an envelope 0.16 x 0.11, its
    origin at its centre. The game pulls it free. Built like the Sorting Hall's envelopes (letter_mesh): long
    side along x, the address on +z, the flap's edge toward +y (here, the end still in the slot); its texture
    is an atlas, the front on the left half and the back on the right. Without that texture it is plain paper."""
    sx_, sz_ = C110_SLOT
    if os.path.exists(LETTER_C110_TEX):
        mat = bpy.data.materials.get('LetterC110') or _image_material('LetterC110', LETTER_C110_TEX, rough=0.85)
    else:
        mat = bpy.data.materials.get('C110LetterMat') or simple_material('C110LetterMat', (0.62, 0.58, 0.48), 0.85)
    w, h, t = 0.16, 0.11, 0.003
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    v = {(sx, sy, sz): bm.verts.new((sx * w / 2, sy * h / 2, sz * t / 2)) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)}

    def face(keys, uvs):
        f = bm.faces.new([v[k] for k in keys])
        for lp, co in zip(f.loops, uvs):
            lp[uv].uv = co
    face([(-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)], [(0, 0), (0.5, 0), (0.5, 1), (0, 1)])
    face([(-1, 1, -1), (1, 1, -1), (1, -1, -1), (-1, -1, -1)], [(1, 1), (0.5, 1), (0.5, 0), (1, 0)])
    edge = [(0.52, 0.04), (0.53, 0.04), (0.53, 0.05), (0.52, 0.05)]
    face([(-1, -1, -1), (1, -1, -1), (1, -1, 1), (-1, -1, 1)], edge)
    face([(1, 1, -1), (-1, 1, -1), (-1, 1, 1), (1, 1, 1)], edge)
    face([(1, -1, -1), (1, 1, -1), (1, 1, 1), (1, -1, 1)], edge)
    face([(-1, 1, -1), (-1, -1, -1), (-1, -1, 1), (-1, 1, 1)], edge)
    rot = _rz(math.radians(-7)) @ _rx(math.radians(52))                      # out of the slot and drooping toward the lane
    bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
    inner = rot @ Vector((0, h / 2, 0))                                       # the end still in the slot
    origin = Vector((sx_ + 0.05, BACK_Y - 0.005, sz_)) - inner
    me = bpy.data.meshes.new('C110Letter')                                    # no normal recalculation: the faces are wound outward
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new('C110Letter', me)
    coll.objects.link(ob)
    ob.location = origin
    return ob


def build_flood(m, coll):
    """Where the lane sank: the dip across the lane (FloodDip: its floor at -0.25, the slab's broken front lip,
    the footing under the wall, broken slab in the water, silt), the standing water (FloodWater, at -0.1:
    dark, still), mud dried on the lane each side, and a drowned shoe."""
    d0, d1, dz = DIP
    cx = (d0 + d1) / 2
    bm = bmesh.new()                       # mats: 0 concrete, 1 mud, 2 steel
    add_box(bm, (cx, 0.2, (dz - 0.07 + dz) / 2), (d1 - d0, 1.9, 0.07), mat=1)                      # the sunk floor, silted
    rnd = random.Random(5090)
    x = d0
    while x < d1 - 0.01:                                                      # the slab's broken front lip
        ln = min(d1 - x, rnd.uniform(0.18, 0.36))
        ztop = rnd.uniform(-0.075, -0.05)
        add_box(bm, (x + ln / 2, -0.685, (dz - 0.07 + ztop) / 2), (ln, 0.13, ztop - dz + 0.07),
                rot=_rx(rnd.uniform(-0.04, 0.04)))
        x += ln
    add_box(bm, (cx, BACK_Y + 0.08, (dz - 0.07) / 2), (d1 - d0, 0.16, -(dz - 0.07)), mat=1)          # the wall's footing, muddied
    for xe in (d0 + 0.0015, d1 - 0.0015):                                    # silt crusted on the broken ends, at the water
        add_box(bm, (xe, 0.19, WATER_Z + 0.04), (0.003, 1.62, 0.1), mat=1)
    for c, size, rx, ry in (((84.05, 0.6, -0.125), (0.46, 0.28, 0.07), -12, 10), ((83.72, -0.43, -0.13), (0.36, 0.24, 0.06), 14, -8)):
        add_box(bm, c, size, rot=_ry(math.radians(ry)) @ _rx(math.radians(rx)))   # slabs broken off, tipped
    rounded_box((0.36, 0.26, 0.1), (84.7, 0.74, -0.115), p=2.4, cuts=3, bm=bm, mat=1, dents=((0.01, 9.0),), seed=91)   # a silt bank
    for k in range(4):                                                        # the drain grating, broken down into it
        y = 0.83 + 0.02 * k
        add_cyl(bm, (d0, y, 0.0), (d0 + 0.12 + 0.03 * k, y - 0.01, -0.1 - 0.03 * k), 0.006, seg=5, mat=2)
    _obj_at('FloodDip', bm, [m['concrete'], m['mud'], m['steel']], coll, (cx, 0.0, dz))
    # The water: one still sheet between the broken ends, behind the lip.
    wy0, wy1 = -0.625, BACK_Y
    wo = Vector((cx, (wy0 + wy1) / 2, WATER_Z))
    me = bpy.data.meshes.new('FloodWater')                                     # facing up; no normal recalculation
    me.from_pydata([Vector(v) - wo for v in ((d0 + 0.004, wy0, WATER_Z), (d1 - 0.004, wy0, WATER_Z),
                                             (d1 - 0.004, wy1, WATER_Z), (d0 + 0.004, wy1, WATER_Z))], [], [(0, 1, 2, 3)])
    me.materials.append(m['water'])
    ob = bpy.data.objects.new('FloodWater', me)
    ob.location = wo
    coll.objects.link(ob)
    # Mud dried on the lane each side of the dip, kept off the duct's path (|y| < 0.26) on the near side.
    patches = []                                                              # (each reaches at most 1.7 r from its centre)
    for k in range(14):
        r = rnd.uniform(0.09, 0.17)
        if k < 6:
            x, y = d0 - 1.7 * r - rnd.uniform(0.0, 0.5), rnd.choice((rnd.uniform(0.3 + 1.7 * r, 0.82), rnd.uniform(-0.72 + 1.7 * r, -0.3 - 1.7 * r)))
        else:
            x, y = d1 + 1.7 * r + rnd.uniform(0.0, 0.7), rnd.uniform(-0.72 + 1.7 * r, 0.82)
        patches.append((x, y, 0.0, r))
    _mud_patches('D5Mud', patches, m['mud'], coll, 5091)
    # Pale scum floating at the water's edges, which shows the surface for what it is even in the dark (kept
    # off the bridge's line, |y| < 0.22).
    _mud_patches('D5Scum', [(84.78, 0.88, WATER_Z - 0.0015, 0.09), (83.55, 0.86, WATER_Z - 0.0015, 0.11), (84.3, 0.9, WATER_Z - 0.0015, 0.07),
                            (84.75, -0.5, WATER_Z - 0.0015, 0.08), (83.5, -0.56, WATER_Z - 0.0015, 0.06), (84.2, 0.42, WATER_Z - 0.0015, 0.05),
                            (83.95, -0.58, WATER_Z - 0.0015, 0.05)], m['plaster'], coll, 5092)
    # A drowned shoe: a grown-up's, on its side at the water's edge, half under.
    def upper(c):
        t = (c.x + 1) / 2                                                      # 0 at the heel, 1 at the toe
        c.z = -1 + (c.z + 1) * (1 - 0.5 * t)
        c.y *= 0.82 + 0.18 * math.sin(math.pi * min(1.0, t * 1.3))
    bm = bmesh.new()                       # mats: 0 leather, 1 sole, 2 the dark inside
    rounded_box((0.26, 0.092, 0.085), (0, 0, 0.056), p=2.4, cuts=4, mat=0, bm=bm, shape=upper, dents=((0.003, 9.0),), seed=93)
    add_box(bm, (0.005, 0, 0.007), (0.27, 0.09, 0.014), mat=1)
    add_box(bm, (-0.095, 0, 0.019), (0.07, 0.084, 0.022), mat=1)
    add_sphere(bm, (-0.05, 0, 0.099), 0.034, seg=10, scale=(1.7, 1.0, 0.22), mat=2)
    bmesh.ops.transform(bm, matrix=Matrix.Translation((84.48, -0.42, WATER_Z - 0.005)) @ _rz(0.5) @ _rx(math.radians(78)), verts=bm.verts)
    _obj('D5DrownedShoe', bm, [m['paper'], m['rubber'], m['shaft']], coll, sharp=60)


def build_duct(m, coll):
    """PushDuct: a length of rectangular ventilation duct fallen along the lane, 0.26 high and 0.4 deep, with a
    red strap round its left end and a grip on the strap at 0.44 (the push clips' height). Origin at its
    base centre; the game pushes it along x and drops it into the dip (top then at about 0.01)."""
    x0, x1, hh, dep = DUCT
    L = x1 - x0 - 0.01                       # 1.49: it drops between the dip's broken ends with a few mm to spare
    t = 0.008
    yb, zb0, zb1 = dep - 0.024, 0.006, hh - 0.006
    bm = bmesh.new()                       # mats: 0 sheet, 1 red, 2 dark inside, 3 steel
    zc = (zb0 + zb1) / 2
    for c, sz in (((0, 0, zb1 - t / 2), (L - 0.02, yb, t)), ((0, 0, zb0 + t / 2), (L - 0.02, yb, t)),
                  ((0, -yb / 2 + t / 2, zc), (L - 0.02, t, zb1 - zb0)), ((0, yb / 2 - t / 2, zc), (L - 0.02, t, zb1 - zb0))):
        add_box(bm, c, sz)
    for fx in (-L / 2 + 0.015, 0.0, L / 2 - 0.015):                           # flanged joints: hollow rings
        add_box(bm, (fx, 0, hh - 0.01), (0.03, dep, 0.02))
        add_box(bm, (fx, 0, 0.01), (0.03, dep, 0.02))
        for sy in (-1, 1):
            add_box(bm, (fx, sy * (dep / 2 - 0.01), hh / 2), (0.03, 0.02, hh - 0.04))
    span, hz = L / 2 - 0.03, zb1 - zb0                                        # cross-breaks: an X pressed into each side panel
    diag = math.hypot(span, hz)
    for cxp in (-span / 2 - 0.0075, span / 2 + 0.0075):
        for sgn in (-1, 1):
            for sy in (-1, 1):
                add_box(bm, (cxp, sy * (yb / 2 + 0.001), zc), (diag - 0.02, 0.002, 0.006), rot=_ry(sgn * math.atan2(hz, span)))
    for fx in (-L / 2 + 0.16, L / 2 - 0.16):                                  # dark inside, seen down the open ends
        add_box(bm, (fx, 0, zc), (0.004, yb - 2 * t, zb1 - zb0 - 2 * t), mat=2)
    # The strap, round the duct near its left end, its ratchet on the front.
    sxp, sw = -L / 2 + 0.12, 0.045
    add_box(bm, (sxp, 0, hh + 0.002), (sw, dep + 0.008, 0.004), mat=1)
    add_box(bm, (sxp, 0, 0.002), (sw, dep + 0.008, 0.004), mat=1)
    for sy in (-1, 1):
        add_box(bm, (sxp, sy * (dep / 2 + 0.002), hh / 2), (sw, 0.004, hh), mat=1)
    add_box(bm, (sxp, -dep / 2 - 0.014, hh * 0.55), (0.06, 0.022, 0.05), mat=3)
    add_cyl(bm, (sxp - 0.03, -dep / 2 - 0.026, hh * 0.55 + 0.012), (sxp + 0.03, -dep / 2 - 0.026, hh * 0.55 + 0.012), 0.006, seg=6, mat=3)
    # Its tail, looped up into a grip: two stiff runs from the top of the band to a red grip bar at 0.44.
    gx, gz = DUCT_GRIP
    for sy in (-1, 1):
        p0, p1 = Vector((sxp, sy * 0.115, hh + 0.004)), Vector((gx, sy * 0.115, gz))
        dv = p1 - p0
        add_box(bm, (p0 + p1) / 2, (dv.length + 0.02, 0.04, 0.004), mat=1, rot=_ry(math.atan2(-dv.z, dv.x)))
    add_cyl(bm, (gx, -0.135, gz), (gx, 0.135, gz), 0.017, seg=10, mat=1)
    origin = Vector(((x0 + x1) / 2, 0.0, 0.0))
    bmesh.ops.translate(bm, vec=origin, verts=bm.verts)
    _obj_at('PushDuct', bm, [m['plate'], m['red'], m['shaft'], m['steel']], coll, origin)


def build_mailslot(m, coll):
    """MailSlot9: ring C's post box on the lane by C-114, a depot-green post with a red rimmed slot at 0.55
    facing the lane, a hood over it and a stamp lamp (SlotLamp9) above. Origin at the post's foot."""
    x, y, sz = MAILSLOT9
    hw, top = 0.1, 0.84
    fy = -hw                                                                  # the front face, relative to the post
    bm = bmesh.new()                       # mats: 0 green, 1 red, 2 dark, 3 steel
    add_box(bm, (0, 0, 0.03), (0.28, 0.28, 0.06))
    add_box(bm, (0, 0, top / 2), (2 * hw, 2 * hw, top))
    add_box(bm, (0, 0, top + 0.02), (0.26, 0.26, 0.04))
    add_sphere(bm, (0, 0, top + 0.04), 0.13, seg=14, scale=(1, 1, 0.42), mat=0)        # a domed cap
    add_box(bm, (0, fy - 0.004, sz), (0.15, 0.01, 0.022), mat=2)            # the slot
    for dz_, w_, h_ in ((0.021, 0.19, 0.016), (-0.021, 0.19, 0.016)):       # its red rim
        add_box(bm, (0, fy - 0.007, sz + dz_), (w_, 0.014, h_), mat=1)
    for dx_ in (-0.087, 0.087):
        add_box(bm, (dx_, fy - 0.007, sz), (0.016, 0.014, 0.058), mat=1)
    add_box(bm, (0, fy - 0.025, sz + 0.05), (0.21, 0.05, 0.012), mat=3, rot=_rx(math.radians(-14)))   # the hood
    add_cyl(bm, (0, fy, sz + 0.13), (0, fy - 0.012, sz + 0.13), 0.026, seg=14, mat=3)               # the lamp's bezel
    for z in (0.12, top - 0.08):                                              # bands
        add_box(bm, (0, 0, z), (2 * hw + 0.008, 2 * hw + 0.008, 0.02), mat=3)
    bmesh.ops.translate(bm, vec=(x, y, 0.0), verts=bm.verts)
    _obj_at('MailSlot9', bm, [m['depot_green'], m['red'], m['shaft'], m['steel']], coll, (x, y, 0.0), sharp=40)
    bm = bmesh.new()
    add_sphere(bm, (x, y + fy - 0.013, sz + 0.13), 0.018, seg=12, scale=(1, 0.6, 1))
    _obj_at('SlotLamp9', bm, [m['slotlamp9']], coll, (x, y + fy - 0.013, sz + 0.13))


def _project_decal(verts, faces, uvs, bvh, x0, x1, z0, z1, step=0.01, ahead=0.002):
    """Lay a decal over whatever `bvh` shows the camera between x0..x1 and z0..z1: rays along +y find the
    front surface for each cell; cells at the same depth are merged into rectangles, each a quad just
    in front of its surface. UVs follow x and z, so the texture runs on unbroken across steps in depth."""
    nx, nz = int(round((x1 - x0) / step)), int(round((z1 - z0) / step))
    grid = []
    for j in range(nz):
        z = z0 + (j + 0.5) * step
        row = []
        for i in range(nx):
            hit = bvh.ray_cast(Vector((x0 + (i + 0.5) * step, -1.5, z)), Vector((0, 1, 0)), 6.0)
            row.append(None if hit[0] is None else int(round(hit[0].y * 1000)))
        grid.append(row)
    rects, active = [], {}
    for j in range(nz + 1):
        runs = set()
        if j < nz:
            row, i = grid[j], 0
            while i < nx:
                if row[i] is None:
                    i += 1
                    continue
                k = i
                while k + 1 < nx and row[k + 1] == row[i]:
                    k += 1
                runs.add((i, k + 1, row[i]))
                i = k + 1
        for key in list(active):
            if key not in runs:
                rects.append((key, active.pop(key), j))
        for key in runs:
            active.setdefault(key, j)
    tw, th = TIDE_TEX
    for (i0, i1, d), j0, j1 in rects:
        xa, xb = x0 + i0 * step, x0 + i1 * step
        za, zb = z0 + j0 * step, z0 + j1 * step
        y = d / 1000 - ahead
        base = len(verts)
        for (x, z) in ((xa, za), (xb, za), (xb, zb), (xa, zb)):
            verts.append((x, y, z))
            uvs.append((x / tw, z / th))
        faces.append((base, base + 1, base + 2, base + 3))
    return len(rects)


def build_tideline(m, coll):
    """Tideline: the flood's mark at TIDE_Z, laid as a decal along the lane's wall and the home facades, in
    C-108's room (seen through its window) and through C-114. The mud below it is in the same texture."""
    from mathutils.bvhtree import BVHTree

    def bvh_of(names):
        bm = bmesh.new()
        for n in names:
            ob = bpy.data.objects[n]
            me = ob.data.copy()
            me.transform(ob.matrix_world)
            bm.from_mesh(me)
            bpy.data.meshes.remove(me)
        tree = BVHTree.FromBMesh(bm)
        bm.free()
        return tree
    top = TIDE_Z + 0.04
    verts, faces, uvs = [], [], []
    n = _project_decal(verts, faces, uvs, bvh_of(['D5Homes', 'D5Facade114']), LANE_C[0], DOOR114[0], 0.0, top)
    cw, cww, cz0, _ = C108_WIN
    n += _project_decal(verts, faces, uvs, bvh_of(['D5Home108Room']), cw - cww / 2, cw + cww / 2, cz0, top)
    n += _project_decal(verts, faces, uvs, bvh_of(['D5Home114']), DOOR114[0], BACK_DOOR[0] + 0.07, 0.0, top)
    me = bpy.data.meshes.new('Tideline')
    me.from_pydata(verts, [], faces)
    uv = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            uv.data[li].uv = uvs[me.loops[li].vertex_index]
    me.materials.append(_image_material('D5TidelineMat', _tex('tideline.png'), rough=0.85, alpha=True))
    ob = bpy.data.objects.new('Tideline', me)
    coll.objects.link(ob)
    print(f'Tideline: {n} quads')
    return ob


def build_home114(m, coll):
    """C-114: the facade with its window and plate, the cross-section wall with the door standing open,
    the hall (shoes, coats and the lamp still on), the inner wall, the floors and ceilings, and the back
    wall at 95.6 with the back door."""
    fx0, wall_x = 87.2, DOOR114[0]
    x_end = BACK_DOOR[0]
    # Facade on the back wall, beside the door.
    bm = bmesh.new()                       # mats: 0 wall, 1 blue trim, 2 concrete
    wx, ww, wz0, wz1 = 87.8, 0.6, 0.98, 1.66                                  # the window opening
    for a, b in ((fx0, wx - ww / 2), (wx + ww / 2, wall_x)):
        add_box(bm, ((a + b) / 2, BACK_Y + 0.08, LANE_CEIL / 2), (b - a, 0.16, LANE_CEIL))
    add_box(bm, (wx, BACK_Y + 0.08, wz0 / 2), (ww, 0.16, wz0))
    add_box(bm, (wx, BACK_Y + 0.08, (wz1 + LANE_CEIL) / 2), (ww, 0.16, LANE_CEIL - wz1))
    add_box(bm, (fx0 - 0.02, BACK_Y - 0.03, LANE_CEIL / 2), (0.14, 0.08, LANE_CEIL), mat=2)
    for sx in (-1, 1):
        add_box(bm, (wx + sx * (ww / 2 + 0.03), BACK_Y - 0.03, (wz0 + wz1) / 2), (0.06, 0.07, wz1 - wz0 + 0.06), mat=1)
    add_box(bm, (wx, BACK_Y - 0.03, wz1 + 0.03), (ww + 0.12, 0.07, 0.06), mat=1)
    add_box(bm, (wx, BACK_Y - 0.06, wz0 - 0.03), (ww + 0.18, 0.13, 0.05), mat=1)
    add_box(bm, (wx, BACK_Y + 0.01, (wz0 + wz1) / 2), (0.025, 0.025, wz1 - wz0), mat=1)
    add_box(bm, (wx, BACK_Y + 0.01, (wz0 + wz1) / 2 + 0.05), (ww, 0.025, 0.025), mat=1)
    add_box(bm, (wx, BACK_Y - 0.11, 0.86), (0.6, 0.16, 0.13), mat=2)           # a window box, its plants long dead
    _obj('D5Facade114', bm, [m['wall'], m['childpaint'], m['concrete']], coll)
    bm = bmesh.new()
    for k in range(5):
        add_cyl(bm, (wx - 0.22 + k * 0.11, BACK_Y - 0.11, 0.92), (wx - 0.24 + k * 0.11 + 0.04 * (k % 2), BACK_Y - 0.13, 1.06 + 0.04 * (k % 3)), 0.004, seg=4)
    _obj('D5WindowBoxStalks', bm, [m['wood']], coll)
    bm = bmesh.new()                                                            # curtains, drawn back, gathered
    for sx in (-1, 1):
        for k in range(4):
            x = wx + sx * (ww / 2 - 0.03 - k * 0.028)
            add_box(bm, (x, BACK_Y + 0.03 + 0.008 * (k % 2), (wz0 + wz1) / 2), (0.03, 0.012, wz1 - wz0 - 0.02),
                    rot=_ry(sx * 0.03 * k))
    add_box(bm, (wx, BACK_Y + 0.03, wz1 - 0.04), (ww, 0.014, 0.07))                # a valance
    _obj('D5Curtains114', bm, [m['letters']], coll)
    bm = bmesh.new()                                                            # the lamp's warmth behind them
    add_box(bm, (wx, BACK_Y + 0.12, (wz0 + wz1) / 2), (ww, 0.01, wz1 - wz0))
    _obj('D5Window114Glow', bm, [m['homelamp']], coll)
    _plane('D5Plate114', (0.26, 0.114), (88.36, BACK_Y - 0.052, 1.5), _image_material('D5Plate114Mat', _tex('plate_c114.png'), rough=0.3), coll)

    # The walls of the home: the cross-section walls (door 1.3, bedroom door 1.25, back door 1.3) and
    # the back walls of the hall and the bedroom.
    bm = bmesh.new()                       # mats: 0 plaster, 1 bedroom paint, 2 dado
    _cross_wall(bm, wall_x, DOOR114[2], DOOR114[1], LANE_CEIL)
    _cross_wall(bm, INNER[0], INNER[2], INNER[1], HOME_CEIL)
    _cross_wall(bm, x_end, BACK_DOOR[2], BACK_DOOR[1], HOME_CEIL)
    add_box(bm, ((wall_x + INNER[0]) / 2, BACK_Y + 0.06, HOME_CEIL / 2), (INNER[0] - wall_x, 0.12, HOME_CEIL))
    # The bedroom's back wall, painted, with a hole for the terminal's screen recess.
    sx0, sx1 = TERM_X - SCREEN[0] / 2, TERM_X + SCREEN[0] / 2
    sz0, sz1 = SCREEN_Z - SCREEN[1] / 2, SCREEN_Z + SCREEN[1] / 2
    dado = 0.75
    add_box(bm, ((INNER[0] + x_end) / 2, BACK_Y + 0.06, dado / 2), (x_end - INNER[0], 0.12, dado), mat=2)
    for a, b in ((INNER[0], sx0), (sx1, x_end)):
        add_box(bm, ((a + b) / 2, BACK_Y + 0.06, (dado + HOME_CEIL) / 2), (b - a, 0.12, HOME_CEIL - dado), mat=1)
    add_box(bm, (TERM_X, BACK_Y + 0.06, (dado + sz0) / 2), (sx1 - sx0, 0.12, sz0 - dado), mat=1)
    add_box(bm, (TERM_X, BACK_Y + 0.06, (sz1 + HOME_CEIL) / 2), (sx1 - sx0, 0.12, HOME_CEIL - sz1), mat=1)
    # Ceilings at 2.3, cut away toward the camera.
    add_box(bm, ((wall_x + STAIR_X - 0.1) / 2, 0.29, HOME_CEIL + 0.06), (STAIR_X - 0.1 - wall_x, 1.66, 0.12))
    _obj('D5Home114', bm, [m['homeplaster'], m['bedroom'], m['dado']], coll)
    bm = bmesh.new()
    _rock_sheet(bm, (wall_x, -0.75, HOME_CEIL + 0.12), (STAIR_X - 0.1 - wall_x, 0, 0), (0, 0, 0.6), 18, 1, 0.05, 21.0)
    _obj('D5RockOverHome', bm, [m['rock']], coll, sharp=75)

    # Floorboards and skirting.
    bm = bmesh.new()                       # mats: 0 boards, 1 skirting
    add_box(bm, ((wall_x + x_end) / 2, 0.2, -0.15), (x_end - wall_x, 1.9, 0.3))
    for k in range(13):
        add_box(bm, ((wall_x + x_end) / 2, -0.62 + k * 0.13, -0.002), (x_end - wall_x, 0.008, 0.006))
    add_box(bm, ((wall_x + x_end) / 2, BACK_Y - 0.008, 0.045), (x_end - wall_x, 0.016, 0.09), mat=1)
    _obj('D5Home114Floor', bm, [m['pigeon'], m['wood']], coll)
    # Door frames, painted the family's blue.
    bm = bmesh.new()
    for x, jamb, lintel in ((wall_x, DOOR114[2], DOOR114[1]), (INNER[0], INNER[2], INNER[1])):
        for side in (-1, 1):
            _door_trim(bm, x, jamb, lintel, side=side)
    _obj('D5DoorFrames', bm, [m['childpaint']], coll)
    # The front door, standing open into the hall, its knocker and its own little plate.
    bm = bmesh.new()                       # mats: 0 door, 1 brass, 2 blue
    hinge = Vector((wall_x + 0.07, DOOR114[2] + 0.02, 0))
    rot = _rz(math.radians(100))
    leaf_w = 0.94
    add_box(bm, hinge + rot @ Vector((0.025, -leaf_w / 2, 0.635)), (0.045, leaf_w, 1.26), rot=rot)
    for z in (0.35, 0.95):
        add_box(bm, hinge + rot @ Vector((-0.002, -leaf_w / 2, z)), (0.01, leaf_w - 0.16, 0.45), mat=2, rot=rot)
    add_sphere(bm, hinge + rot @ Vector((-0.02, -leaf_w + 0.08, 0.62)), 0.025, seg=10, mat=1)
    add_torus(bm, hinge + rot @ Vector((-0.02, -leaf_w / 2, 0.98)), rot.to_3x3() @ Vector((1, 0, 0)), 0.04, 0.007, seg=16, rseg=6, mat=1)
    _obj('D5FrontDoor', bm, [m['pigeon'], m['brass'], m['childpaint']], coll)

    # The hall: a coir mat, two pairs of shoes, coats on hooks, and a lamp left on.
    bm = bmesh.new()
    add_box(bm, (89.0, 0.05, 0.006), (0.55, 0.42, 0.012))
    _obj('D5HallMat', bm, [m['paper']], coll)
    bm = bmesh.new()                       # mats: 0 the grown-up's boots, 1 the child's yellow boots, 2 soles
    for k, (x, y, rz) in enumerate(((89.72, 0.78, 0.1), (89.88, 0.8, -0.05))):     # the grown-up's
        rounded_box((0.28, 0.1, 0.09), (x, y, 0.05), p=2.6, cuts=2, mat=0, bm=bm, rot=_rz(math.pi / 2 + rz))
        rounded_box((0.11, 0.09, 0.16), (x, y + 0.08, 0.12), p=2.6, cuts=2, mat=0, bm=bm, rot=_rz(rz))
        add_box(bm, (x, y, 0.008), (0.1, 0.28, 0.016), mat=2, rot=_rz(rz))
    for k, (x, y, rz) in enumerate(((90.04, 0.86, 0.15), (90.13, 0.84, -0.2))):    # the child's, beside them
        rounded_box((0.15, 0.06, 0.06), (x, y, 0.035), p=2.6, cuts=2, mat=1, bm=bm, rot=_rz(math.pi / 2 + rz))
        rounded_box((0.065, 0.06, 0.11), (x, y + 0.04, 0.08), p=2.6, cuts=2, mat=1, bm=bm, rot=_rz(rz))
        add_box(bm, (x, y, 0.006), (0.06, 0.15, 0.012), mat=2, rot=_rz(rz))
    _obj('D5HallShoes', bm, [m['paper'], m['yellow'], m['rubber']], coll, sharp=60)
    bm = bmesh.new()                       # mats: 0 rail, 1 grown-up's coat, 2 the child's raincoat
    add_box(bm, (89.95, BACK_Y - 0.02, 1.62), (0.6, 0.03, 0.06))
    for x in (89.75, 89.95, 90.15):
        add_cyl(bm, (x, BACK_Y - 0.03, 1.62), (x, BACK_Y - 0.09, 1.66), 0.008, seg=6)
    rounded_box((0.36, 0.12, 0.92), (89.76, BACK_Y - 0.1, 1.15), p=4.0, cuts=3, mat=1, bm=bm, taper=lambda z: 0.85 + 0.15 * (-z), seed=3,
                dents=((0.008, 6.0),))
    rounded_box((0.24, 0.1, 0.5), (90.15, BACK_Y - 0.09, 1.33), p=4.0, cuts=3, mat=2, bm=bm, taper=lambda z: 0.8 + 0.2 * (-z), seed=4,
                dents=((0.006, 7.0),))
    add_sphere(bm, (90.15, BACK_Y - 0.08, 1.6), 0.07, seg=10, scale=(1.0, 0.8, 0.9), mat=2)     # its hood
    _obj('D5Coats', bm, [m['steel'], m['depot_green'], m['yellow']], coll, sharp=60)
    bm = bmesh.new()                       # the lamp: a little table, a stem and a paper shade
    lx, ly = 90.36, 0.8
    add_box(bm, (lx, ly, 0.5), (0.3, 0.26, 0.03))
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_box(bm, (lx + sx * 0.12, ly + sy * 0.1, 0.25), (0.025, 0.025, 0.5))
    add_cyl(bm, (lx, ly, 0.515), (lx, ly, 0.54), 0.06, seg=14)
    add_cyl(bm, (lx, ly, 0.54), (lx, ly, 0.76), 0.01, seg=6)
    _obj('D5HallTable', bm, [m['wood']], coll)
    bm = bmesh.new()
    add_cyl(bm, (lx, ly, 0.72), (lx, ly, 0.88), 0.11, 0.07, seg=18)
    _obj('D5LampShade', bm, [m['letters']], coll)
    bm = bmesh.new()
    add_sphere(bm, (lx, ly, 0.775), 0.03, seg=12)
    _obj('HomeLampBulb', bm, [m['homelamp']], coll)
    # The back door, standing open onto the service passage.
    bm = bmesh.new()
    _door_trim(bm, x_end, BACK_DOOR[2], BACK_DOOR[1], side=-1)
    _door_trim(bm, x_end, BACK_DOOR[2], BACK_DOOR[1], side=1)
    for z in (0.3, 1.0):                                                        # its hinges, the door long gone
        add_box(bm, (x_end + 0.075, BACK_DOOR[2] + 0.01, z), (0.02, 0.03, 0.09))
    _obj('D5BackDoor', bm, [m['plate']], coll)


def build_bedroom(m, coll):
    """The child's room: the bed with its quilt, the window painted on the wall and lit from behind,
    a drawing pinned over the bed, a paper mobile, the rug, the shelf and the photograph."""
    bx0, bx1, btop, bfront = BED
    by1 = BACK_Y - 0.02
    bm = bmesh.new()                       # mats: 0 frame, 1 blue paint
    add_box(bm, (bx0 + 0.03, (bfront + by1) / 2, 0.39), (0.06, by1 - bfront, 0.78), mat=1)             # headboard
    for k in range(4):
        add_box(bm, (bx0 + 0.065, bfront + 0.12 + k * 0.15, 0.62), (0.02, 0.06, 0.2), mat=0)
    add_box(bm, (bx1 - 0.03, (bfront + by1) / 2, 0.27), (0.06, by1 - bfront, 0.54), mat=1)             # footboard
    for y in (bfront + 0.03, by1 - 0.03):
        add_box(bm, ((bx0 + bx1) / 2, y, 0.2), (bx1 - bx0, 0.05, 0.12), mat=0)
    for x in (bx0 + 0.03, bx1 - 0.03):
        for y in (bfront + 0.03, by1 - 0.03):
            add_box(bm, (x, y, 0.1), (0.06, 0.06, 0.2), mat=0)
    _obj('ChildBed', bm, [m['wood'], m['childpaint']], coll)
    bm = bmesh.new()                       # mattress and pillow
    add_box(bm, ((bx0 + bx1) / 2, (bfront + by1) / 2, 0.31), (bx1 - bx0 - 0.12, by1 - bfront - 0.04, 0.16))
    rounded_box((0.26, 0.5, 0.11), (bx0 + 0.22, (bfront + by1) / 2 + 0.03, btop + 0.04), p=2.6, cuts=3, bm=bm, dents=((0.006, 6.0),), seed=31)
    _obj('D5Bedding', bm, [m['letters']], coll, sharp=60)
    quilt = _image_material('D5QuiltMat', _tex('quilt.png'), rough=0.9)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    # The quilt: over the top of the bed from the pillow to the foot, and hanging down the front.
    qx0, qx1 = bx0 + 0.36, bx1 - 0.07
    rows = [(qx0, by1, btop - 0.005), (qx0, bfront + 0.02, btop), (qx0, bfront - 0.015, btop - 0.05), (qx0, bfront - 0.02, 0.24)]
    vs = []
    for (x_, y, z) in rows:
        vs.append((bm.verts.new((x_, y, z)), bm.verts.new((qx1, y, z))))
    acc = [0.0]
    for (a, b) in zip(rows, rows[1:]):
        acc.append(acc[-1] + (Vector(a) - Vector(b)).length)
    for k in range(len(rows) - 1):
        f = bm.faces.new((vs[k][0], vs[k][1], vs[k + 1][1], vs[k + 1][0]))
        for lp, (u, v) in zip(f.loops, ((0, acc[k]), (qx1 - qx0, acc[k]), (qx1 - qx0, acc[k + 1]), (0, acc[k + 1]))):
            lp[uv].uv = (u * 2.2, v * 2.2)
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.012)
    _obj('D5Quilt', bm, [quilt], coll)

    # The painted window over the bed: a real frame and sill, the painting, and the lamp behind it.
    wx, wz, ww, wh = PAINTED_WINDOW
    bm = bmesh.new()
    for sx in (-1, 1):
        add_box(bm, (wx + sx * (ww / 2 + 0.03), BACK_Y - 0.02, wz), (0.06, 0.05, wh + 0.12))
    for sz in (-1, 1):
        add_box(bm, (wx, BACK_Y - 0.02, wz + sz * (wh / 2 + 0.03)), (ww + 0.12, 0.05, 0.06))
    add_box(bm, (wx, BACK_Y - 0.06, wz - wh / 2 - 0.07), (ww + 0.22, 0.12, 0.035))
    _obj('D5WindowFrame', bm, [m['wood']], coll)
    _plane('D5WindowPaint', (ww, wh), (wx, BACK_Y - 0.012, wz), _image_material('D5WindowPaintMat', _tex('window_paint.png'), rough=0.6, alpha=True), coll)
    bm = bmesh.new()
    add_box(bm, (wx, BACK_Y - 0.004, wz), (ww + 0.02, 0.004, wh + 0.02))
    _obj('WindowSun', bm, [m['windowsun']], coll)
    # A drawing pinned over the foot of the bed, above the flood's line.
    _plane('D5Drawing', (0.3, 0.225), (92.36, BACK_Y - 0.008, 1.42), _image_material('D5DrawingMat', _tex('child_drawing.png'), rough=0.85), coll,
           rot=_ry(math.radians(4)) @ _rx(math.radians(90)))
    bm = bmesh.new()
    add_sphere(bm, (92.36, BACK_Y - 0.016, 1.515), 0.008, seg=8)
    _obj('D5DrawingPin', bm, [m['steel']], coll)
    # A paper mobile from the ceiling over the bed: stars and a bird.
    bm, card = bmesh.new(), bmesh.new()
    mx, my = 91.8, 0.62
    add_cyl(bm, (mx, my, HOME_CEIL), (mx, my, 1.98), 0.002, seg=4)
    add_cyl(bm, (mx - 0.22, my, 1.98), (mx + 0.22, my, 1.98), 0.003, seg=4)
    for k, (dx, ln) in enumerate(((-0.22, 0.2), (0.0, 0.1), (0.22, 0.26))):
        add_cyl(bm, (mx + dx, my, 1.98), (mx + dx, my, 1.98 - ln), 0.0015, seg=4)
        c = Vector((mx + dx, my, 1.98 - ln - 0.05))
        pts = [c + Vector(((0.05 if i % 2 == 0 else 0.02) * math.sin(i * math.pi / 5), 0, (0.05 if i % 2 == 0 else 0.02) * math.cos(i * math.pi / 5)))
               for i in range(10)]
        vs = [card.verts.new(p) for p in pts]
        card.faces.new(vs)
    _obj('D5MobileWire', bm, [m['steel']], coll)
    star = d17.mesh_object('D5MobileStars', card, [m['yellow']], coll)
    star.data.polygons.foreach_set('use_smooth', [False] * len(star.data.polygons))
    # The rug.
    _plane('D5Rug', (1.25, 0.78), (93.2, 0.3, 0.004), _image_material('D5RugMat', _tex('rug.png'), rough=0.95), coll, rot=Matrix.Identity(4))

    # The shelf, with the photograph, two books, a cup of pencils and a little wooden bird.
    sx, sz = SHELF
    bm = bmesh.new()
    add_box(bm, (sx, BACK_Y - 0.09, sz - 0.012), (0.46, 0.18, 0.024))
    for d_ in (-0.17, 0.17):
        add_box(bm, (sx + d_, BACK_Y - 0.05, sz - 0.08), (0.02, 0.1, 0.12), rot=None)
    add_box(bm, (sx + 0.115, BACK_Y - 0.08, sz + 0.075), (0.035, 0.13, 0.15))
    add_box(bm, (sx + 0.15, BACK_Y - 0.08, sz + 0.065), (0.03, 0.12, 0.13), rot=_ry(-0.25))
    _obj('D5Shelf', bm, [m['wood']], coll)
    bm = bmesh.new()
    add_cyl(bm, (sx + 0.195, BACK_Y - 0.07, sz), (sx + 0.195, BACK_Y - 0.07, sz + 0.08), 0.028, seg=12)
    _obj('D5Cup', bm, [m['childpaint']], coll)
    bm = bmesh.new()
    for k in range(4):
        a = k * 0.5
        add_cyl(bm, (sx + 0.195, BACK_Y - 0.07, sz + 0.02), (sx + 0.195 + 0.03 * math.cos(a), BACK_Y - 0.07 + 0.02 * math.sin(a), sz + 0.14), 0.004, seg=5)
    _obj('D5Pencils', bm, [m['yellow']], coll)
    bm = bmesh.new()
    add_sphere(bm, (sx - 0.185, BACK_Y - 0.08, sz + 0.03), 0.026, seg=10, scale=(1.4, 0.9, 0.9))
    add_sphere(bm, (sx - 0.15, BACK_Y - 0.08, sz + 0.058), 0.016, seg=8)
    add_cyl(bm, (sx - 0.137, BACK_Y - 0.08, sz + 0.058), (sx - 0.12, BACK_Y - 0.08, sz + 0.054), 0.005, 0.001, seg=6)
    _obj('D5WoodenBird', bm, [m['pigeon']], coll)
    # The photograph in a standing frame, leaning back a little.
    lean = _rx(math.radians(-10))
    bm = bmesh.new()
    pc = Vector((sx - 0.02, BACK_Y - 0.1, sz + 0.108))
    for dx, dz, w_, h_ in ((-0.072, 0, 0.016, 0.22), (0.072, 0, 0.016, 0.22), (0, -0.102, 0.16, 0.016), (0, 0.102, 0.16, 0.016)):
        add_box(bm, pc + lean @ Vector((dx, 0.0, dz)), (w_, 0.014, h_), rot=lean)
    add_box(bm, pc + Vector((0, 0.05, -0.035)), (0.02, 0.012, 0.15), rot=_rx(math.radians(30)))
    _obj('D5PhotoFrame', bm, [m['wood']], coll)
    _plane('D5Photo', (0.128, 0.188), pc + Vector((0, -0.006, 0)), _image_material('D5PhotoMat', _tex('photo.png'), rough=0.35), coll,
           rot=_rx(math.radians(80)))


def build_terminal(m, coll):
    """The forwarding terminal on the bedroom wall: a depot-green housing round the screen recess (the
    game draws the screen at y 1.0), the reader below it angled down to a courier's chest, with a red
    ring, three lamps over the screen and a conduit up into the ceiling."""
    x0, x1, z0, z1 = TERM_HOUSING
    sx0, sx1 = TERM_X - SCREEN[0] / 2, TERM_X + SCREEN[0] / 2
    sz0, sz1 = SCREEN_Z - SCREEN[1] / 2, SCREEN_Z + SCREEN[1] / 2
    yc, dp = (TERM_FRONT + BACK_Y) / 2, BACK_Y - TERM_FRONT
    bm = bmesh.new()                       # mats: 0 green, 1 steel, 2 red, 3 dark
    add_box(bm, ((x0 + sx0) / 2, yc, (z0 + z1) / 2), (sx0 - x0, dp, z1 - z0))
    add_box(bm, ((sx1 + x1) / 2, yc, (z0 + z1) / 2), (x1 - sx1, dp, z1 - z0))
    add_box(bm, (TERM_X, yc, (z0 + sz0) / 2), (sx1 - sx0, dp, sz0 - z0))
    add_box(bm, (TERM_X, yc, (sz1 + z1) / 2), (sx1 - sx0, dp, z1 - sz1))
    add_box(bm, (TERM_X, TERM_FRONT - 0.01, z1 + 0.012), (x1 - x0 + 0.04, 0.07, 0.024))           # a little hood
    for z in (sz0 - 0.008, sz1 + 0.008):                                         # the bezel
        add_box(bm, (TERM_X, TERM_FRONT - 0.004, z), (sx1 - sx0 + 0.03, 0.008, 0.016), mat=1)
    for x in (sx0 - 0.008, sx1 + 0.008):
        add_box(bm, (x, TERM_FRONT - 0.004, SCREEN_Z), (0.016, 0.008, sz1 - sz0 + 0.03), mat=1)
    add_box(bm, (TERM_X, BACK_Y + 0.05, SCREEN_Z), (sx1 - sx0 + 0.02, 0.01, sz1 - sz0 + 0.02), mat=3)   # recess back
    for x in (sx0, sx1):
        add_box(bm, (x, (TERM_FRONT + BACK_Y + 0.05) / 2, SCREEN_Z), (0.006, BACK_Y + 0.05 - TERM_FRONT, sz1 - sz0), mat=3)
    for z in (sz0, sz1):
        add_box(bm, (TERM_X, (TERM_FRONT + BACK_Y + 0.05) / 2, z), (sx1 - sx0, BACK_Y + 0.05 - TERM_FRONT, 0.006), mat=3)
    # The reader: a short barrel out of the housing, tipped down 35 degrees, a dark lens and a red ring.
    a = math.radians(35)
    out = Vector((0, -math.cos(a), -math.sin(a)))
    base = Vector((TERM_X, TERM_FRONT, READER_Z + 0.012))
    add_cyl(bm, base + out * -0.005, base + out * 0.03, 0.052, seg=16)
    add_cyl(bm, base + out * 0.03, base + out * 0.034, 0.036, seg=16, mat=3)
    add_torus(bm, base + out * 0.032, out, 0.043, 0.006, seg=16, rseg=4, mat=2)
    # Bolts and the conduit up into the ceiling.
    for x in (x0 + 0.025, x1 - 0.025):
        for z in (z0 + 0.025, z1 - 0.025):
            add_cyl(bm, (x, TERM_FRONT, z), (x, TERM_FRONT - 0.006, z), 0.008, seg=6, mat=1)
    add_cyl(bm, (x1 - 0.05, BACK_Y - 0.02, z1), (x1 - 0.05, BACK_Y - 0.02, HOME_CEIL), 0.016, seg=10, mat=1)
    for z in (1.5, 1.9):
        add_box(bm, (x1 - 0.05, BACK_Y - 0.012, z), (0.05, 0.024, 0.02), mat=1)
    lamp_z = z1 - 0.055
    for i in range(3):
        add_torus(bm, (TERM_X - 0.07 + 0.07 * i, TERM_FRONT - 0.002, lamp_z), (0, 1, 0), 0.019, 0.0028, seg=12, rseg=3, mat=1)
    _obj('ForwardTerminal', bm, [m['depot_green'], m['steel'], m['red'], m['shaft']], coll)
    for i in range(3):
        bm = bmesh.new()
        add_sphere(bm, (TERM_X - 0.07 + 0.07 * i, TERM_FRONT - 0.004, lamp_z), 0.015, seg=12, scale=(1, 0.6, 1))
        _obj(f'TermLamp{i}', bm, [m['termlamp'][i]], coll)
    pic = bpy.data.materials.get('Pictogram')
    if pic is not None:                                                           # the depot's parcel-and-arrow
        _plane('D5TermPictogram', (0.06, 0.06), (x0 + 0.05, TERM_FRONT - 0.002, READER_Z + 0.01), pic, coll)

    # The growth marks and the tree, on the wall behind the desk.
    mx0, mx1, mz0, mz1 = MARKS
    _plane('D5Marks', (mx1 - mx0, mz1 - mz0), ((mx0 + mx1) / 2, BACK_Y - 0.003, (mz0 + mz1) / 2),
           _image_material('D5MarksMat', _tex('growth_marks.png'), rough=0.9, alpha=True), coll)


def build_desk(m, coll):
    """The child's desk, with a pinboard hutch, fallen back against the wall in front of the terminal and
    the marks. One object, origin on the floor at the centre of its footprint; the game slides it along
    x by its red grip bar on the left end (0.44 high)."""
    h, dd, top, hut = DESK_HALF, 0.42, DESK_TOP, DESK_HUTCH
    side = math.radians(DESK_SIDE_TILT)
    drop = (2 * h - 0.07) * math.sin(side)                                    # its right legs gave way
    bm = bmesh.new()                       # mats: 0 blue paint, 1 wood, 2 red, 3 paper, 4 cork
    add_box(bm, (0, 0, top - 0.015), (2 * h, dd, 0.03))
    for sx in (-1, 1):
        for sy in (-1, 1):
            ln = top - 0.03 - (0 if sx < 0 else (drop if sy > 0 else 0.3))   # the front right leg snapped off
            add_box(bm, (sx * (h - 0.035), sy * (dd / 2 - 0.03), top - 0.03 - ln / 2), (0.045, 0.045, ln))
        add_box(bm, (sx * (h - 0.035), 0, top - 0.08), (0.02, dd - 0.08, 0.09))
    add_box(bm, (0, -dd / 2 + 0.03, top - 0.08), (2 * h - 0.1, 0.02, 0.09))
    add_box(bm, (-0.2, -dd / 2 + 0.03, 0.12), (2 * h - 0.5, 0.02, 0.03))       # a footrest rail, broken off at one end
    # The drawer, slid half out as it fell, empty.
    add_box(bm, (0.12, -dd / 2 - 0.1, top - 0.085), (0.4, 0.018, 0.09))
    add_box(bm, (0.12, -dd / 2 + 0.02, top - 0.125), (0.38, 0.24, 0.012), mat=1)
    for sx in (-1, 1):
        add_box(bm, (0.12 + sx * 0.185, -dd / 2 + 0.02, top - 0.095), (0.012, 0.24, 0.06), mat=1)
    add_sphere(bm, (0.12, -dd / 2 - 0.115, top - 0.085), 0.016, seg=10, mat=1)
    # The hutch: painted sides and a cap, two shelves, a cork board with drawings pinned to it. It stands tall
    # enough to hide the marks and the tree on the wall behind it until it is dragged clear.
    for sx in (-1, 1):
        add_box(bm, (sx * (h - 0.01), dd / 2 - 0.08, (top + hut) / 2), (0.02, 0.16, hut - top))
    add_box(bm, (0, dd / 2 - 0.08, hut - 0.01), (2 * h, 0.17, 0.02))
    for z in (0.9, 1.4):
        add_box(bm, (0, dd / 2 - 0.08, z), (2 * h - 0.04, 0.15, 0.018))
    add_box(bm, (0, dd / 2 - 0.006, (top + hut) / 2), (2 * h - 0.02, 0.012, hut - top), mat=4)
    rnd = random.Random(5050)
    for k, (x, z) in enumerate(((-0.33, 0.74), (-0.05, 0.72), (0.3, 0.76), (-0.2, 1.04), (0.22, 1.06), (-0.3, 1.62), (0.2, 1.66))):
        add_box(bm, (x, dd / 2 - 0.014, z), (0.15, 0.003, 0.11), mat=3, rot=_ry(rnd.uniform(-0.2, 0.2)))
    bx = -h + 0.06                                                            # books on the upper shelf, slid over in the fall
    for k in range(7):
        bw, bh = rnd.uniform(0.022, 0.04), rnd.uniform(0.15, 0.22)
        lean = 0.0 if k < 5 else -0.5
        add_box(bm, (bx + bw / 2, dd / 2 - 0.085, 1.409 + bh / 2 * math.cos(lean)), (bw, 0.12, bh), mat=k % 2 * 3 + (1 if k % 3 == 0 else 0),
                rot=_ry(lean))
        bx += bw + 0.004 + (0.06 if k == 4 else 0)
    # Down on its broken right side, and tipped back until the hutch rests against the terminal.
    foot = Vector((-h + 0.035, 0, 0))
    bmesh.ops.transform(bm, matrix=Matrix.Translation(foot) @ _ry(side) @ Matrix.Translation(-foot), verts=bm.verts)
    pivot = Vector((0, dd / 2, 0))
    bmesh.ops.transform(bm, matrix=Matrix.Translation(pivot) @ _rx(math.radians(DESK_TILT)) @ Matrix.Translation(-pivot), verts=bm.verts)
    # It rests against the terminal's conduit (front y 0.964) above the terminal.
    ymax = max(v.co.y for v in bm.verts)
    bmesh.ops.translate(bm, vec=(0, (BACK_Y - 0.02 - 0.016 - 0.004 - DESK_Y) - ymax, -min(v.co.z for v in bm.verts)), verts=bm.verts)
    clear = min(TERM_FRONT - 0.045 - (DESK_Y + v.co.y) for v in bm.verts if TERM_HOUSING[2] - 0.02 < v.co.z < TERM_HOUSING[3] + 0.03)
    print(f'ChildDesk: clearance in front of the terminal and its hood {clear:.3f}')
    # The red grip bar on its left end, level, where a claw can take it.
    hx, hz = DESK_HANDLE
    add_cyl(bm, (hx, -0.11, hz), (hx, 0.11, hz), 0.014, seg=10, mat=2)
    for y in (-0.09, 0.09):
        add_cyl(bm, (hx, y, hz), (-h + 0.012, y, hz + 0.0), 0.009, seg=8, mat=2)
    ob = _obj('ChildDesk', bm, [m['childpaint'], m['wood'], m['red'], m['letters'], m['paper']], coll)
    ob.location = (DESK_X, DESK_Y, 0)
    ys = [v.co.y for v in ob.data.vertices]
    zs = [v.co.z for v in ob.data.vertices]
    print(f'ChildDesk: y {DESK_Y + min(ys):.3f}..{DESK_Y + max(ys):.3f}, z {min(zs):.3f}..{max(zs):.3f}')
    # What fell off it: crayons, a drawing, a pencil tin on the floor.
    bm = bmesh.new()
    for k in range(7):
        x, y = DESK_X + rnd.uniform(-0.4, 0.45), rnd.uniform(0.12, 0.36)
        a = rnd.uniform(0, math.pi)
        add_cyl(bm, (x, y, 0.006), (x + 0.07 * math.cos(a), y + 0.07 * math.sin(a), 0.006), 0.005, seg=6,
                mat=k % 3)
    add_cyl(bm, (DESK_X + 0.42, 0.26, 0.0), (DESK_X + 0.42, 0.26, 0.09), 0.035, seg=12, mat=3)
    _obj('D5Crayons', bm, [m['yellow'], m['childpaint'], m['depot_green'], m['steel']], coll)
    _plane('D5FloorDrawing', (0.24, 0.18), (DESK_X - 0.2, 0.22, 0.003), bpy.data.materials['D5DrawingMat'], coll,
           rot=_rz(0.4))
    bm = bmesh.new()                                                            # the snapped-off leg
    add_box(bm, (DESK_X + 0.62, 0.3, 0.023), (0.045, 0.045, 0.24), rot=_rz(0.5) @ _ry(math.pi / 2 - 0.08))
    _obj('D5DeskLeg', bm, [m['childpaint']], coll)


def build_toy(m, coll):
    """The patched rabbit: soft, lop-eared, one button eye and one sewn cross. Modelled upright with its
    origin at its base; the node's own rotation is the slump. The game eases it to identity to sit it up."""
    bm = bmesh.new()                       # mats: 0 fabric, 1 patch, 2 thread and buttons, 3 pale
    rounded_box((0.112, 0.09, 0.092), (0, 0, 0.045), p=2.2, cuts=4, bm=bm, dents=((0.002, 30.0),), seed=61)
    rounded_box((0.074, 0.066, 0.062), (0, -0.004, 0.106), p=2.2, cuts=4, bm=bm, dents=((0.002, 30.0),), seed=62)
    add_sphere(bm, (0, -0.034, 0.098), 0.017, seg=10, scale=(1.2, 0.8, 0.8), mat=3)
    rounded_box((0.026, 0.012, 0.085), (0.05, 0.004, 0.09), p=2.2, cuts=3, bm=bm, rot=_ry(math.radians(165)), seed=63)      # ears: one flopped
    rounded_box((0.026, 0.012, 0.085), (-0.03, 0.006, 0.168), p=2.2, cuts=3, bm=bm, rot=_ry(math.radians(-35)) @ _rx(0.2), seed=64)
    for sx in (-1, 1):
        rounded_box((0.024, 0.026, 0.056), (sx * 0.058, -0.014, 0.05), p=2.2, cuts=3, bm=bm, rot=_ry(sx * 0.4) @ _rx(-0.4), seed=65 + sx)
        rounded_box((0.032, 0.055, 0.026), (sx * 0.027, -0.034, 0.013), p=2.2, cuts=3, bm=bm, seed=67 + sx)
    add_sphere(bm, (0, 0.044, 0.026), 0.014, seg=8, mat=3)
    add_box(bm, (0.012, -0.0425, 0.045), (0.034, 0.005, 0.034), mat=1, rot=_ry(0.2))               # a patch on the tummy
    add_box(bm, (-0.031, 0.0, 0.17), (0.02, 0.016, 0.03), mat=1, rot=_ry(math.radians(-35)))        # and on the ear
    for k in range(6):                                                                              # its stitches
        a = 0.2 + k * 0.33
        add_box(bm, (0.012 + 0.019 * math.cos(a * 3), -0.0455, 0.045 + 0.019 * math.sin(a * 3)), (0.006, 0.002, 0.0015), mat=2,
                rot=_ry(a * 3))
    add_sphere(bm, (0.016, -0.036, 0.114), 0.0065, seg=8, mat=2)                                    # a button eye
    for a in (0.8, -0.8):                                                                           # and a sewn cross
        add_box(bm, (-0.016, -0.0375, 0.114), (0.012, 0.002, 0.002), mat=2, rot=_ry(a))
    add_box(bm, (0, -0.048, 0.092), (0.01, 0.002, 0.002), mat=2)
    ob = _obj('Toy', bm, [m['toy'], m['toypatch'], m['rubber'], m['letters']], coll, sharp=70)
    ob.location = TOY
    ob.rotation_euler = [math.radians(v) for v in TOY_SLUMP]


def build_passage(m, coll):
    """Through the back door: a service passage, pipes, a caged lamp, the stair up toward ring B and the
    school's sign."""
    x0 = BACK_DOOR[0]
    bm = bmesh.new()                       # mats: 0 wall, 1 concrete
    add_box(bm, ((x0 + WORLD_END) / 2, BACK_Y + 0.06, 1.8), (WORLD_END - x0, 0.12, 3.6))
    add_box(bm, (WORLD_END, 0.29, 1.8), (0.15, 1.8, 3.6))
    add_box(bm, ((STAIR_X - 0.1 + WORLD_END) / 2, 0.29, 3.6), (WORLD_END - STAIR_X + 0.1, 1.66, 0.12), mat=1)
    _obj('D5Passage', bm, [m['wall'], m['concrete']], coll)
    bm = bmesh.new()                       # mats: 0 concrete, 1 yellow nosing
    for k in range(16):
        x = STAIR_X + k * 0.26
        add_box(bm, (x + 0.13, 0.25, (k + 1) * 0.09), (0.26, 1.3, (k + 1) * 0.18), mat=0)
        add_box(bm, (x + 0.02, 0.25, (k + 1) * 0.18 - 0.005), (0.04, 1.3, 0.012), mat=1)
    _obj('D5Stair', bm, [m['concrete'], m['yellow']], coll)
    bm = bmesh.new()
    add_cyl(bm, (STAIR_X, BACK_Y - 0.06, 0.9), (STAIR_X + 4.16, BACK_Y - 0.06, 0.9 + 16 * 0.18), 0.02, seg=8)
    for k in (1, 5, 9, 13):
        x = STAIR_X + k * 0.26
        add_cyl(bm, (x, BACK_Y - 0.06, 0.9 + k * 0.18), (x, BACK_Y, 0.9 + k * 0.18), 0.008, seg=6)
    _obj('D5StairRail', bm, [m['yellow']], coll)
    bm = bmesh.new()
    for z, r in ((2.02, 0.04), (2.14, 0.025)):
        add_cyl(bm, (x0, BACK_Y - 0.08, z), (WORLD_END, BACK_Y - 0.08, z), r, seg=12)
    for x in (96.2, 97.4, 98.6, 99.8):
        add_box(bm, (x, BACK_Y - 0.04, 2.08), (0.04, 0.08, 0.2))
    _obj('D5Pipes', bm, [m['steel']], coll)
    bm = bmesh.new()                       # a caged lamp over the stair foot
    lx = 97.15
    lz = 1.92
    add_box(bm, (lx, BACK_Y - 0.03, lz), (0.12, 0.06, 0.12))
    for k in range(4):
        a = k * math.pi / 2
        add_cyl(bm, (lx + 0.05 * math.cos(a), BACK_Y - 0.1 + 0.05 * math.sin(a), lz - 0.05), (lx + 0.04 * math.cos(a), BACK_Y - 0.1 + 0.04 * math.sin(a), lz - 0.2), 0.003, seg=4)
    _obj('D5PassageLampCage', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_sphere(bm, (lx, BACK_Y - 0.1, lz - 0.14), 0.035, seg=12)
    _obj('LaneBulbPassage', bm, [m['lanebulb']], coll)
    _plane('D5SchoolSign', (0.78, 0.325), (97.15, BACK_Y - 0.006, 1.5), _image_material('D5SchoolSignMat', _tex('school_sign.png')), coll)


def build_set(dl01, m, coll):
    make_textures()
    dl05_materials(m)
    build_ledge(m, coll)
    build_barricade(m, coll)
    build_ring_c(m, coll)
    build_flood(m, coll)
    build_duct(m, coll)
    build_mailslot(m, coll)
    build_home114(m, coll)
    build_bedroom(m, coll)
    build_terminal(m, coll)
    build_desk(m, coll)
    build_toy(m, coll)
    build_passage(m, coll)
    build_tideline(m, coll)


# --------------------------------------------------------------------------
# D-17 clips
#
# Rig space: D-17 faces -y, his left is +x. Claw targets are kept outside the pod by design: the knock
# is made with the forearm out past his right shoulder; at the terminal both arms go back along his
# sides while he arches his chest window up to the reader; at the bed the claws reach forward of the
# chest window and below the head's rim.
# --------------------------------------------------------------------------

FINGER = 0.108                        # wrist to claw tip


def _body_inv(body, body_rot):
    import build_dl02
    return build_dl02.body_delta(body, body_rot).inverted()


def _aim(d):
    """hand_rot (degrees) that points the claws along d (body space): pitch about x, then turn about z."""
    d = Vector(d).normalized()
    a = -math.acos(max(-1.0, min(1.0, -d.z)))
    sa = math.sin(a)
    return (math.degrees(a), 0.0, math.degrees(math.atan2(-d.x / sa, d.y / sa)))


def _lerp3(a, b, k):
    return tuple(x + (y - x) * k for x, y in zip(a, b))


def _via(p0, p1, p2, t):
    """A wrist path from p0 to p2 bowed out through p1, so the forearm swings round the pod, not through it."""
    t = max(0.0, min(1.0, t))
    return p0 * (1 - t) ** 2 + p1 * (2 * (1 - t) * t) + p2 * t * t


def _path(pts, t):
    """Along a polyline of wrist positions, t from 0 to 1."""
    t = max(0.0, min(1.0, t)) * (len(pts) - 1)
    i = min(int(t), len(pts) - 2)
    return pts[i].lerp(pts[i + 1], t - i)


def _rest_rot(s):
    return (-24.0, s * 6.0, s * 10.0)


KNOCK_HITS = (14, 20)                 # the knuckles meet the frame
KNOCK_WRIST = Vector((-0.25, -0.2, 0.56))     # the right wrist at a hit (body space), out past his shoulder
KNOCK_AIM = Vector((0.25, -0.95, 0.15))       # the closed claw points ahead, a little in and up
KNOCK_VIA = Vector((-0.28, -0.2, 0.34))


def _knock_draw(f):
    """How far the knuckles are drawn back from the frame (0 on it, 1 fully back)."""
    a, b = KNOCK_HITS
    if f <= a - 3:
        return 1.0
    if f <= a:
        return 1 - ((f - (a - 3)) / 3) ** 2
    if f <= b - 3:
        return 0.85 * smoothstep((f - a) / 3)
    if f <= b:
        return 0.85 * (1 - ((f - (b - 3)) / 3) ** 2)
    return 0.6 * smoothstep(min(1.0, (f - b) / 6))


def clip_knock(dl01, arm):
    """At the open door, facing the frame: he raises his right claw, knocks twice, waits with his head
    on one side, listening, and lowers it. Nobody comes. The knock lands about 0.3 m ahead of him,
    0.22 m to his right and 0.57 m up (KNOCK_HITS)."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 48
    c = Clip(arm, 'Knock', frames)
    carry_w = REST[-1] + CARRY[-1]
    for frame in range(1, frames + 1):
        f = frame - 1
        up = track([(2, 0), (10, 1), (34, 1), (44, 0)], f)
        draw = _knock_draw(f)
        hit = sum(math.exp(-max(0, f - t0) / 2.0) for t0 in KNOCK_HITS if f >= t0)
        body = (0, -0.006 * up + 0.004 * hit, -0.004 * up)
        rot = (track([(0, 0), (10, 3), (22, 3), (30, -1), (40, 0)], f) + 1.2 * hit, track([(22, 0), (30, -2), (38, -2), (44, 0)], f), 0)
        wrist = _via(carry_w, KNOCK_VIA, KNOCK_WRIST + Vector((0, 0.05 * draw, 0.01 * draw)), up)
        hands = {1: CARRY[1], -1: wrist - REST[-1]}
        head = (track([(0, 0), (8, -6), (22, -4), (30, 2), (38, 4), (46, 0)], f),
                track([(20, 0), (27, 14), (37, 14), (44, 0)], f),
                track([(0, 0), (8, 6), (22, 4), (28, 0)], f))
        antenna = [(track([(0, 0), (10, -6), (22, -6), (28, -18), (36, -16), (42, 8), (48, 4)], f) * (0.8 + 0.15 * i)
                    + spring(f, KNOCK_HITS[0], -4) + spring(f, KNOCK_HITS[1], -4), 0) for i in range(3)]
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands,
               hand_rot={'L': _rest_rot(1), 'R': _lerp3(_rest_rot(-1), _aim(KNOCK_AIM), up)},
               claws={'L': CLAW_REST_OPEN['L'], 'R': track([(2, 1), (8, 3), (34, 3), (42, 1)], f)})
    c.done()


PRESENT_LAMPS = (20, 25, 30)          # the terminal's lamps answer his
PRESENT_NOD = 50


def clip_present(dl01, arm):
    """At the terminal, 0.26 m off it (the game turns him and steps him in): up on his toes, arms back,
    he arches his chest window up toward the reader and holds it there while the lamps answer; then he
    comes down and gives a small nod."""
    track, spring, Clip, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY
    frames = 64
    c = Clip(arm, 'Present', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        lean = track([(2, 0), (14, 1), (40, 1), (47, 0)], f)
        nod = track([(44, 0), (PRESENT_NOD, 1), (56, 0)], f)
        hands = {s: CARRY[s] + Vector((s * 0.03, 0.045, -0.012)) * lean for _, s in SIDES}
        feet = {side: ((0, 0, 0), (-9 * lean, 0, 0)) for side, s in SIDES}
        body = (0, 0.014 * lean, 0.03 * lean - 0.006 * nod)
        rot = (-20 * lean + 4 * nod, 0, 0)
        head = (track([(0, 0), (14, -14), (40, -14), (47, -2)], f) + 16 * nod, track([(30, 0), (36, 4), (44, 0)], f), 0)
        twitch = sum(spring(f, t0, -5, decay=3, freq=1.6) for t0 in PRESENT_LAMPS)
        antenna = [(track([(0, 0), (14, -14), (40, -14), (48, 0), (56, -8), (64, -4)], f) * (0.8 + 0.15 * i) + twitch * (1 + 0.3 * i), 0)
                   for i in range(3)]
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands, feet=feet,
               hand_rot={'L': (-24 + 20 * lean, 6, 10), 'R': (-24 + 20 * lean, -6, -10)},
               claws={'L': CLAW_REST_OPEN['L'] + 6 * lean, 'R': 1 + 10 * lean})
    c.done()


TOY_AHEAD = 0.35                      # D-17's root to the rabbit's origin when he starts Straighten
TOY_SIT = (14, 26)                    # the game rotates it upright between these frames
TOY_PAT = 33                          # the pat lands
GRIP_W = {s: Vector((s * 0.19, -0.3, 0.475)) for _, s in SIDES}   # wrists while holding it (body space)
GRIP_VIA = {s: (Vector((s * 0.28, -0.24, 0.34)), Vector((s * 0.27, -0.3, 0.44))) for _, s in SIDES}   # forward and up, outside the pod
PAT_W = Vector((-0.2, -0.3, 0.49))


def _toy_rot(k):
    from mathutils import Euler, Quaternion
    q0 = Euler([math.radians(v) for v in TOY_SLUMP], 'XYZ').to_quaternion()
    return q0.slerp(Quaternion(), k).to_matrix()


def _toy_point(local, k):
    """A point on the rabbit (its local coordinates) in D-17's rig space, k from slumped (0) to upright (1)."""
    w = _toy_rot(k) @ Vector(local)
    return Vector((-w.x, -TOY_AHEAD - w.y, TOY[2] + w.z))


def clip_straighten(dl01, arm):
    """Facing the bed: a step in, both claws to the slumped rabbit; he sits it up (the game turns it
    upright between frames 14 and 26), lets go, turns a little to pat its head once with his right
    claw, and steps back to where he started."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    frames = 52
    c = Clip(arm, 'Straighten', frames)
    carry_w = {s: REST[s] + CARRY[s] for _, s in SIDES}
    for frame in range(1, frames + 1):
        f = frame - 1
        step = track([(0, 0), (8, 1), (40, 1), (49, 0)], f)
        lift = [0.025 * math.sin(math.pi * min(1, max(0, (f - t0) / 6))) for t0 in (0, 3, 40, 43)]
        feet = {'R': ((0, -0.06 * track([(0, 0), (6, 1), (40, 1), (46, 0)], f), lift[0] + lift[2]), (0, 0, 0)),
                'L': ((0, -0.06 * track([(3, 0), (9, 1), (43, 1), (49, 0)], f), lift[1] + lift[3]), (0, 0, 0))}
        twist = track([(27, 0), (31, 1), (37, 1), (43, 0)], f)
        tap = math.sin(math.pi * min(1, max(0, (f - (TOY_PAT - 2)) / 4)))
        body = (0, -0.06 * step, 0.02 * step - 0.006 * tap)
        rot = (3 * step, 0, 15 * twist)
        inv = _body_inv(body, rot)
        k = smoothstep(min(1.0, max(0.0, (f - TOY_SIT[0]) / (TOY_SIT[1] - TOY_SIT[0]))))
        grip = {s: _toy_point((-s * 0.066, 0.0, 0.05), k) + Vector((0, 0, 0.008 * math.sin(math.pi * k))) for _, s in SIDES}
        hold = {1: track([(3, 0), (12, 1), (26, 1), (33, 0)], f), -1: track([(3, 0), (12, 1), (37, 1), (46, 0)], f)}
        pat_up = track([(26, 0), (30, 1), (36, 1), (40, 0)], f)
        head_top = _toy_point((0.0, 0.004, 0.14), 1.0) + Vector((0.0, 0, 0.022 * (1 - tap)))
        hands, hand_rot = {}, {}
        for side, s in SIDES:
            w_hold = GRIP_W[s].copy()
            aim = _aim(inv @ grip[s] - w_hold)
            if s == -1:
                pat_w = PAT_W + Vector((0, 0, 0.02 * (1 - tap)))
                aim = _lerp3(aim, _aim(inv @ head_top - pat_w), pat_up)
                w_hold = w_hold.lerp(pat_w, pat_up)
            w = _path([carry_w[s], GRIP_VIA[s][0], GRIP_VIA[s][1], w_hold], hold[s])
            hands[s], hand_rot[side] = w - REST[s], _lerp3(_rest_rot(s), aim, min(1.0, hold[s] * 1.4))
        clawL = track([(3, CLAW_REST_OPEN['L']), (9, 30), (13, 6), (26, 6), (29, 26), (36, CLAW_REST_OPEN['L'])], f)
        clawR = track([(3, 1), (9, 30), (13, 6), (26, 6), (29, 22), (32, 4), (40, 4), (46, 1)], f)
        head = (track([(0, 0), (8, 8), (26, 8), (32, 4), (40, 4), (48, 0)], f),
                track([(28, 0), (34, 10), (42, 10), (50, 0)], f), track([(26, 0), (31, -10), (38, -10), (44, 0)], f))
        antenna = [(track([(0, 0), (10, 4), (26, 4), (34, -8), (44, -10), (52, -2)], f) * (0.8 + 0.15 * i) + spring(f, TOY_PAT, -6), 0)
                   for i in range(3)]
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands, feet=feet,
               hand_rot=hand_rot, claws={'L': clawL, 'R': clawR})
    c.done()


WATER_SPARK = 9                       # his toe touches the water: the game sparks at his right foot
WATER_REACH = 0.125                   # how far ahead of where he stands the toe goes (he stops about this short of the water)


def clip_water_flinch(dl01, arm):
    """At the flood's edge, facing the water: he leans in and puts his right foot out to it; the toe touches
    (WATER_SPARK) and he jerks back, arms flung out, the foot snatched up. He holds it up and shakes it off,
    looking at it, and sets it down where it started. He ends where he began, at rest."""
    track, spring, Clip, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY
    frames = 30
    S = WATER_SPARK
    c = Clip(arm, 'WaterFlinch', frames)
    snap = lambda x: d17.ease_back(x, 0.8)   # noqa: E731
    for frame in range(1, frames + 1):
        f = frame - 1
        weight = track([(0, 0), (4, 1), (23, 1), (28, 0)], f)                 # onto the left foot while the right is up
        jolt = track([(S, 0), (S + 2, 1), (S + 7, 0.55), (22, 0.15), (27, 0)], f, ease=snap)
        shake = math.sin(2 * math.pi * (f - 13) / 2.6) * track([(12, 0), (14, 1), (20, 1), (22, 0)], f)
        fy = track([(0, 0), (S - 1, -WATER_REACH + 0.005), (S, -WATER_REACH), (S + 3, 0.025), (14, 0.03), (22, 0.025), (27, 0)], f)
        fz = track([(0, 0), (4, 0.045), (S - 1, 0.008), (S, -0.006), (S + 3, 0.08), (14, 0.075), (22, 0.065), (27, 0)], f)
        fz += 0.014 * shake
        fx = -0.012 * shake
        pitch = track([(0, 0), (4, 6), (S - 1, -12), (S, -14), (S + 3, 10), (14, 4), (22, 4), (27, 0)], f)   # toe down to the water
        feet = {'R': ((fx, fy, fz), (pitch, 0, 6 * shake)), 'L': ((0, 0, 0), (0, 0, 0))}
        body = (0.022 * weight + 0.004 * shake,
                track([(0, 0), (S - 1, -0.028), (S, -0.032), (S + 3, 0.016), (15, 0.008), (27, 0)], f),
                track([(0, 0), (S - 1, -0.012), (S, -0.014), (S + 2, 0.002), (S + 7, -0.006), (26, 0)], f))
        rot = (track([(0, 0), (S - 1, 8), (S, 9), (S + 3, -9), (15, -2), (27, 0)], f),
               -4 * weight + 1.5 * shake, track([(S, 0), (S + 3, 6), (14, 4), (22, 4), (27, 0)], f))
        head = (track([(0, 0), (5, 16), (S, 18), (S + 3, -10), (14, 14), (22, 14), (27, 0)], f),
                track([(S, 0), (S + 3, 10), (12, 6), (22, 6), (27, 0)], f),
                track([(0, 0), (5, -6), (S, -6), (S + 3, 4), (14, -14), (22, -14), (27, 0)], f))
        antenna = [(track([(0, 0), (S, -8), (S + 2, -46), (S + 8, -24), (22, -10), (29, 0)], f) * (0.8 + 0.15 * i)
                    + spring(f, S + 2, -10 * (i + 1), decay=4, freq=1.3), 0) for i in range(3)]
        flail = Vector((0, 0.03, 0.075))
        hands = {sg: CARRY[sg] + (flail + Vector((sg * 0.07, 0, 0))) * jolt + Vector((sg * 0.03, 0, 0.02)) * track([(0, 0), (S - 1, 1), (S + 1, 0)], f)
                 for _, sg in SIDES}
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, feet=feet, hands=hands,
               hand_rot={'L': (-24 - 30 * jolt, 6, 10 + 20 * jolt), 'R': (-24 - 30 * jolt, -6, -10 - 20 * jolt)},
               claws={'L': CLAW_REST_OPEN['L'] + 22 * jolt, 'R': 1 + 30 * jolt},
               elbows={'L': 0.6 * jolt, 'R': 0.6 * jolt})
    c.done()


def add_clips(dl01, arm):
    clip_knock(dl01, arm)
    clip_present(dl01, arm)
    clip_straighten(dl01, arm)
    clip_water_flinch(dl01, arm)
