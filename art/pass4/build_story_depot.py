"""Chapter 1, pass 4 (docs/chapter1_pass4_plan.md): story_depot. Built in FINAL world x, after the pass 3 modules.
Pass 5 (docs/chapter1_pass5_plan.md sections 1 and 2): the dead are 76 years dead, and what killed them is shown.

What happened here, said plainly, in the depot's scenes (DL-01 to DL-05):

  DL-02  The last night shift. The sorters died at their posts, and they have been dead seventy-six years: skeletons,
         dry dark-ivory bone in the rags of their shirts and trousers, their canvas aprons, a cap. One slumped over
         the sorting table's end, the skull on a forearm, the finger bones of the other hand on the letters
         (Sorter1); one sitting on the floor against the welded door, knees up, her cap on, her arms round a mailbag
         (Sorter2); one over the tea table in the alcove (Sorter3); two side by side at a sorting bench under the
         gantry (Sorter4, Sorter5). Two meshes (seated, sitting) as linked duplicates, each one draw call in the
         remains atlas (art/pass3, RemainsMat).
         What killed them: the air was cut. On the back wall between the tea corner and the pigeonholes, the
         bulkhead to the stairs, welded shut (StoryWeldedDoor), hand marks and nail scratches at its foot; pasted on
         it, the order: AIR / RINGS A-B PRIORITY / LOWER WORKS ON RESERVE / BY ORDER OF THE GRADE COUNCIL, stamped
         R.Y. 42 (StoryAirNotice); over it the depot's air gauge, its needle on zero in the red NO AIR, and over that
         the fan's grille, the fan stopped behind it (StoryAirGauge). One atlas, story_air.png (StoryAirMat).
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
CAP_FLOOR = (18.42, 0.78)                              # Sorter1's cap, fallen by the stool, toward the wall

# What killed them (pass 5): the bulkhead to the stairs, between the tea corner (its jamb x 17.34) and the
# pigeonholes (x 18.44), on the back wall (its face y 1.0); Sorter2 sits against it.
DOOR_X = 17.89                                         # the door's centre (its frame 17.38 to 18.40)
WALL_Y = 1.0
DOOR_LEAF = (0.83, 1.995)                              # the leaf's width and top
NOTICE = (0.56, 0.756)                                 # the order on the leaf: width, height
NOTICE_Z = 1.36                                        # its centre's height
GAUGE_Z, GAUGE_R = 2.37, 0.235                         # the air gauge over the door: centre height, dial radius
FAN_Z, FAN_W = (2.70, 3.12), 0.62                      # the fan's grille over the gauge: bottom, top; width
LORE_MOVE = (12.97 - 17.86, 0.62 - 1.0, 1.95 - 1.7)    # art/pass3 lore's DL-02 notice board, off the door's wall to the
                                                       # wall over the passage in (face y 0.62, x 12.52 to 13.42)

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


# --------------------------------------------------------------------------
# Pass 5: what killed the night shift (DL-02). One painted atlas for the welded door, the order on it, the air
# gauge and the dead fan: story_air.png, 1024 x 1024, cells in pixels (x0, y0, x1, y1).
# --------------------------------------------------------------------------
AIR_CELLS = {
    'door': (0, 0, 420, 1024),          # the bulkhead door's leaf, front: paint, STAIRS, hand marks, scratches
    'notice': (420, 0, 820, 540),       # the order, pasted on the door
    'gauge': (420, 540, 820, 940),      # the air gauge's dial
    'steel': (820, 0, 1024, 200),       # the door's frame, the gauge's case, the fan's grille: worn grey-green paint
    'weld': (820, 200, 1024, 400),      # weld beads: dark, slag-flecked, heat-tinted
    'needle': (820, 400, 1024, 480),    # black
    'hole': (820, 480, 1024, 600),      # the duct behind the grille: dark
    'fan': (820, 600, 1024, 720),       # the fan's blades: dark steel, furred with dust
    'bare': (820, 720, 1024, 840),      # steel scraped bright
    'leaf': (820, 840, 1024, 1024),     # the leaf's edges: the same paint, plain
}


def air_uv(cell):
    x0, y0, x1, y1 = AIR_CELLS[cell]
    return x0 / 1024, 1 - y1 / 1024, x1 / 1024, 1 - y0 / 1024


def _cond(size):
    from PIL import ImageFont
    try:
        return ImageFont.truetype('/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf', size)
    except OSError:
        return _font(size)


def _fit(d, text, font_of, size, width):
    f = font_of(size)
    while f.getlength(text) > width and size > 8:
        size -= 2
        f = font_of(size)
    return f


def make_story_air(path):
    from PIL import Image, ImageDraw, ImageFilter, ImageChops
    rnd = random.Random(5501)
    img = Image.new('RGB', (1024, 1024), (40, 44, 40))
    d = ImageDraw.Draw(img, 'RGBA')

    def mottle(cell, base, blot=12, n=60, rmax=30, speck=12, streaks=0, streak_col=(30, 22, 14)):
        x0, y0, x1, y1 = AIR_CELLS[cell]
        d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=base)
        for _ in range(n):
            x, y, r = rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(3, rmax)
            c = tuple(max(0, min(255, b + rnd.randint(-blot, blot))) for b in base)
            d.ellipse((max(x0, x - r), max(y0, y - r * 0.7), min(x1 - 1, x + r), min(y1 - 1, y + r * 0.7)), fill=(*c, rnd.randint(20, 60)))
        for _ in range(streaks):
            x = rnd.uniform(x0, x1)
            ya = rnd.uniform(y0, y1 - 20)
            d.line((x, ya, x + rnd.uniform(-3, 3), min(y1 - 1, ya + rnd.uniform(30, 300))), fill=(*streak_col, rnd.randint(30, 80)), width=rnd.randint(2, 6))
        for _ in range((x1 - x0) * (y1 - y0) // speck):
            x, y = rnd.randrange(x0, x1), rnd.randrange(y0, y1)
            c = rnd.randint(0, 255)
            d.point((x, y), fill=(c, c, c, rnd.randint(8, 26)))

    # ---- The door's leaf: grey-green bulkhead paint, rust run from its rivets, grime thicker toward the floor.
    X0, Y0, X1, Y1 = AIR_CELLS['door']
    mottle('door', (86, 96, 86), blot=12, n=120, rmax=40, speck=10, streaks=26)
    for y in range(Y0, Y1, 4):                                      # grime: darker toward the foot
        a = int(70 * max(0.0, (y - Y0) / (Y1 - Y0) - 0.45) / 0.55)
        d.line((X0, y, X1, y), fill=(28, 26, 22, a), width=4)
    for x in (X0 + 22, X1 - 22):                                    # rivet rows, each with its rust run
        for y in range(Y0 + 40, Y1 - 20, 92):
            d.ellipse((x - 6, y - 6, x + 6, y + 6), fill=(60, 66, 60), outline=(40, 44, 40), width=2)
            d.line((x, y + 6, x + rnd.uniform(-2, 2), y + rnd.uniform(20, 70)), fill=(96, 58, 30, 90), width=3)
    for x in (X0 + 6, X1 - 6):                                      # heat-tint along the welded edges
        for k in range(12):
            d.line((x + (k if x < 200 else -k), Y0, x + (k if x < 200 else -k), Y1), fill=(40, 34, 44, 90 - 7 * k), width=1)
    for k in range(12):
        d.line((X0, Y0 + 4 + k, X1, Y0 + 4 + k), fill=(40, 34, 44, 90 - 7 * k), width=1)
    # STAIRS, stencilled across the top, and the way it once went: up to ring B.
    f = _fit(d, 'STAIRS', lambda s: _font(s), 84, X1 - X0 - 40)
    bb = d.textbbox((0, 0), 'STAIRS', font=f)
    d.text(((X0 + X1 - (bb[2] - bb[0])) / 2 - bb[0], Y0 + 14 - bb[1]), 'STAIRS', font=f, fill=(206, 198, 170, 230))
    f2 = _cond(44)
    t2 = 'RING B  ↑'
    bb2 = d.textbbox((0, 0), t2, font=f2)
    d.text(((X0 + X1 - (bb2[2] - bb2[0])) / 2 - bb2[0], Y0 + 92 - bb2[1]), t2, font=f2, fill=(206, 198, 170, 220))
    # Hands: grimy palms and fingers pressed flat, some dragged down the paint, around and below where the order is
    # pasted (it covers 0.26 to 0.66 of the leaf's height from the top); the most at a crouch's height.
    def handprint(cx, cy, s, ang, smear, alpha):
        hm = Image.new('L', (220, 420), 0)
        hd = ImageDraw.Draw(hm)
        ox, oy = 110, 160
        hd.ellipse((ox - 30, oy - 26, ox + 30, oy + 34), fill=255)                         # the palm
        for k, (dx, L) in enumerate(((-24, 46), (-8, 58), (8, 60), (24, 50))):             # four fingers, up
            hd.rounded_rectangle((ox + dx - 7, oy - 26 - L, ox + dx + 7, oy - 18), radius=7, fill=255)
        hd.rounded_rectangle((ox + 30, oy - 22, ox + 44, oy + 18), radius=7, fill=255)    # the thumb
        hm = hm.rotate(ang, resample=Image.BICUBIC, center=(ox, oy))
        if smear:                                                                         # dragged down the door
            acc = hm.copy()
            for k in range(3, smear, 3):
                sh = Image.new('L', hm.size, 0)
                sh.paste(hm.point(lambda v, k=k: int(v * 0.6 * (1 - k / smear))), (0, k))
                acc = ImageChops.lighter(acc, sh)
            hm = acc
        hm = hm.resize((int(220 * s), int(420 * s)), Image.LANCZOS)
        hm = hm.filter(ImageFilter.GaussianBlur(1.6)).point(lambda v: int(v * alpha / 255))
        col = Image.new('RGB', hm.size, (26, 23, 20))
        img.paste(col, (int(cx - hm.size[0] / 2), int(cy - 160 * s)), hm)
    # (The order covers 51 to 358 across, 133 to 531 down; the sorter sitting against the door hides the middle below
    # 680: the marks crowd round the order's edges, under it, and down both sides of her.)
    marks = [(30, 290, 0.62, 14, 0, 170), (396, 250, 0.6, -12, 40, 160), (26, 460, 0.64, 22, 60, 190),
             (394, 470, 0.62, -16, 80, 180), (80, 590, 0.66, 8, 50, 200), (170, 615, 0.64, -4, 90, 190),
             (262, 600, 0.66, 6, 70, 200), (346, 625, 0.64, -10, 110, 190), (120, 665, 0.6, 16, 40, 170),
             (300, 672, 0.6, -14, 30, 170), (44, 750, 0.6, 24, 90, 190), (384, 770, 0.6, -22, 70, 180),
             (58, 860, 0.56, -6, 40, 170), (396, 890, 0.54, 12, 30, 160)]
    for cx, cy, s, ang, smear, alpha in marks:
        handprint(X0 + cx, Y0 + cy, s, ang, smear, alpha)
    d = ImageDraw.Draw(img, 'RGBA')
    # Scratches at its foot: nails dragged through the paint to the steel, in fours, most near the edges and the
    # floor, where someone tried to get a grip on the seam.
    for _ in range(34):
        side = rnd.random()
        x = X0 + (rnd.uniform(8, 90) if side < 0.4 else rnd.uniform(X1 - X0 - 90, X1 - X0 - 8) if side < 0.8 else rnd.uniform(90, 330))
        y = Y0 + rnd.uniform(690, 1000)
        L = rnd.uniform(40, 170)
        ang = rnd.uniform(-0.25, 0.25)
        for k in range(rnd.choice((3, 4, 4))):
            ox = k * rnd.uniform(9, 13)
            pts = [(x + ox + math.sin(ang) * L * t + 3 * math.sin(t * 3 + k), y - L * t) for t in (0, 0.33, 0.66, 1)]
            d.line(pts, fill=(176, 174, 162, rnd.randint(150, 230)), width=rnd.choice((2, 3, 3)))
            d.line([(p[0] + 2, p[1]) for p in pts], fill=(32, 30, 26, 120), width=1)
    for _ in range(120):                                            # and the small ones, everywhere low down
        x, y = X0 + rnd.uniform(6, X1 - X0 - 6), Y0 + rnd.uniform(560, 1015)
        L = rnd.uniform(6, 28)
        d.line((x, y, x + rnd.uniform(-4, 4), y - L), fill=(160, 158, 146, rnd.randint(80, 170)), width=2)
    # ---- The order: yellowed paper, printed, stamped.
    nx0, ny0, nx1, ny1 = AIR_CELLS['notice']
    mottle('notice', (196, 186, 152), blot=10, n=40, rmax=40, speck=10)
    for _ in range(14):                                             # foxing, a damp tide at its foot
        x, y, r = rnd.uniform(nx0, nx1), rnd.uniform(ny0, ny1), rnd.uniform(3, 14)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(150, 120, 74, rnd.randint(30, 80)))
    d.rectangle((nx0, ny1 - 70, nx1, ny1), fill=(140, 116, 72, 50))
    ink = (24, 22, 22)
    W = nx1 - nx0
    d.rectangle((nx0 + 16, ny0 + 16, nx1 - 16, ny1 - 16), outline=ink, width=4)
    fa = _font(150)
    bb = d.textbbox((0, 0), 'AIR', font=fa)
    d.text((nx0 + (W - (bb[2] - bb[0])) / 2 - bb[0], ny0 + 34 - bb[1]), 'AIR', font=fa, fill=ink)
    y = ny0 + 34 + (bb[3] - bb[1]) + 22
    for text, size, gap in (('RINGS A–B PRIORITY', 62, 22), (None, 0, 18), ('LOWER WORKS', 66, 10), ('ON RESERVE', 66, 22),
                            (None, 0, 18), ('BY ORDER OF THE GRADE COUNCIL', 34, 0)):
        if text is None:
            d.line((nx0 + 40, y, nx1 - 40, y), fill=ink, width=4)
            y += gap
            continue
        f = _fit(d, text, _cond, size, W - 60)
        bb = d.textbbox((0, 0), text, font=f)
        d.text((nx0 + (W - (bb[2] - bb[0])) / 2 - bb[0], y - bb[1]), text, font=f, fill=ink)
        y += (bb[3] - bb[1]) + gap
    # The stamp, struck crooked at the foot: GRADE COUNCIL, the date.
    st = Image.new('L', (300, 120), 0)
    sd = ImageDraw.Draw(st)
    sd.rounded_rectangle((6, 6, 294, 114), radius=10, outline=255, width=6)
    fs = _cond(34)
    sd.text((24, 14), 'GRADE COUNCIL', font=fs, fill=255)
    sd.text((70, 60), 'R.Y. 42', font=_cond(44), fill=255)
    holes = Image.effect_noise((300, 120), 90).point(lambda v: 255 if v > 90 else 120)
    st = Image.composite(st, Image.new('L', st.size, 0), holes).rotate(-8, expand=True, resample=Image.BICUBIC)
    st = st.point(lambda v: int(v * 0.72))
    img.paste(Image.new('RGB', st.size, (112, 34, 34)), (nx1 - st.size[0] - 18, ny1 - st.size[1] - 12), st)
    d = ImageDraw.Draw(img, 'RGBA')
    # ---- The air gauge's dial: cream enamel, 0 to 100 round 270 degrees from lower left, NO AIR in red at zero.
    gx0, gy0, gx1, gy1 = AIR_CELLS['gauge']
    cx, cy, R = (gx0 + gx1) / 2, (gy0 + gy1) / 2, (gx1 - gx0) / 2
    d.rectangle((gx0, gy0, gx1 - 1, gy1 - 1), fill=(30, 32, 30))
    d.ellipse((cx - R + 2, cy - R + 2, cx + R - 2, cy + R - 2), fill=(206, 198, 168))

    def at(v, r):                                                   # v 0..100 -> a point at radius r
        a = math.radians(-135 + 270 * v / 100)
        return cx + r * math.sin(a), cy - r * math.cos(a)

    def band(v0, v1, r0, r1, col):
        pts = [at(v0 + (v1 - v0) * k / 24, r1) for k in range(25)] + [at(v1 - (v1 - v0) * k / 24, r0) for k in range(25)]
        d.polygon(pts, fill=col)
    band(0, 18, R * 0.7, R * 0.9, (150, 36, 28))
    band(18, 40, R * 0.8, R * 0.9, (190, 140, 50))
    for v in range(0, 101, 5):
        r0 = R * (0.7 if v % 25 == 0 else 0.78)
        d.line((at(v, r0), at(v, R * 0.9)), fill=ink, width=6 if v % 25 == 0 else 3)
    for v in (0, 25, 50, 75, 100):
        f = _font(30)
        t = str(v)
        p = at(v, R * 0.57)
        bb = d.textbbox((0, 0), t, font=f)
        d.text((p[0] - (bb[2] + bb[0]) / 2, p[1] - (bb[3] + bb[1]) / 2), t, font=f, fill=ink)
    f = _font(56)
    bb = d.textbbox((0, 0), 'AIR', font=f)
    d.text((cx - (bb[2] + bb[0]) / 2, cy - R * 0.02 - (bb[3] + bb[1]) / 2), 'AIR', font=f, fill=ink)
    f = _cond(22)
    t = 'LOWER WORKS · SUPPLY %'
    bb = d.textbbox((0, 0), t, font=f)
    d.text((cx - (bb[2] + bb[0]) / 2, cy + R * 0.24 - (bb[3] + bb[1]) / 2), t, font=f, fill=ink)
    f = _font(36)
    t = 'NO AIR'
    bb = d.textbbox((0, 0), t, font=f)
    d.text((cx - (bb[2] + bb[0]) / 2, cy + R * 0.78 - (bb[3] + bb[1]) / 2), t, font=f, fill=(150, 36, 28))
    for _ in range(50):                                             # grime and a crack across the enamel
        x, y, r = rnd.uniform(gx0 + 30, gx1 - 30), rnd.uniform(gy0 + 30, gy1 - 30), rnd.uniform(4, 20)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(70, 60, 44, rnd.randint(4, 12)))
    d.line([(cx - R * 0.8, cy - R * 0.1), (cx - R * 0.3, cy - R * 0.25), (cx + R * 0.1, cy - R * 0.15), (cx + R * 0.7, cy - R * 0.5)],
           fill=(60, 54, 44, 160), width=2)
    # ---- The small cells.
    mottle('steel', (78, 88, 80), blot=12, n=50, rmax=26, speck=8, streaks=10)
    mottle('weld', (66, 62, 58), blot=20, n=80, rmax=12, speck=4)
    wx0, wy0, wx1, wy1 = AIR_CELLS['weld']
    for _ in range(60):                                             # temper colours and slag flecks
        x, y, r = rnd.uniform(wx0, wx1), rnd.uniform(wy0, wy1), rnd.uniform(2, 9)
        d.ellipse((x - r, y - r, x + r, y + r), fill=rnd.choice(((70, 70, 110, 90), (130, 100, 50, 90), (150, 148, 140, 110), (30, 26, 24, 120))))
    mottle('needle', (18, 17, 16), blot=4, n=4, speck=40)
    mottle('hole', (10, 10, 10), blot=3, n=6, speck=60)
    mottle('fan', (46, 46, 42), blot=10, n=30, rmax=20, speck=8)
    fx0, fy0, fx1, fy1 = AIR_CELLS['fan']
    for _ in range(400):                                            # dust furred on the blades
        x, y = rnd.uniform(fx0, fx1), rnd.uniform(fy0, fy1)
        d.point((x, y), fill=(120, 116, 104, rnd.randint(60, 150)))
    mottle('bare', (150, 150, 142), blot=14, n=30, rmax=16, speck=6)
    mottle('leaf', (82, 92, 82), blot=10, n=30, rmax=20, speck=10, streaks=6)
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.convert('RGB').save(path, optimize=True)


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
# The sorters (DL-02): 76 years dead (pass 5)
# --------------------------------------------------------------------------

V = Vector
SEATED = dict(                                         # slumped over the table, the skull on the left forearm
    pelvis=V((0.0, 0.0, 0.53)), chest=V((0.29, 0.0, 0.86)),
    shoulder=(V((0.27, 0.17, 0.84)), V((0.27, -0.17, 0.84))),
    neck=V((0.38, 0.0, 0.88)), head=V((0.50, -0.03, 0.857)), face=V((0.25, -0.5, -0.83)), crown=V((0.9, 0.1, 0.25)),
    # Left forearm on the table under the skull; the right reaching on along it, its finger bones on the letters.
    elbow=(V((0.50, 0.22, 0.785)), V((0.45, -0.26, 0.778))),
    wrist=(V((0.56, 0.0, 0.783)), V((0.66, -0.24, 0.772))),
    hand=((V((0.1, -1.0, -0.05)), V((0, 0, 1))), (V((1.0, 0.1, -0.08)), V((0, 0, 1)))),
    curl=(0.35, 0.3),
    hip=(V((0.0, 0.1, 0.50)), V((0.0, -0.1, 0.50))),
    knee=(V((0.40, 0.12, 0.50)), V((0.40, -0.12, 0.49))),
    ankle=(V((0.43, 0.13, 0.10)), V((0.42, -0.13, 0.10))),
    foot=(V((1, 0.05, 0)), V((1, -0.05, 0))),
    skirt=[V((0.06, 0.0, 0.585)), V((0.42, 0.0, 0.585)), V((0.47, 0.0, 0.36))],
    table=0.751,                                       # the letters under the right hand lie on the table's top
)
SITTING = dict(                                        # on the floor, her back to the welded door, knees up, head down
    pelvis=V((0.0, 0.0, 0.13)), chest=V((-0.03, 0.0, 0.55)),
    shoulder=(V((-0.02, 0.17, 0.53)), V((-0.02, -0.17, 0.53))),
    neck=V((0.02, 0.0, 0.60)), head=V((0.11, 0.03, 0.61)), face=V((0.6, 0.15, -0.8)), crown=V((0.8, 0.0, 0.6)),
    # Both arms round the mailbag on her lap, the finger bones in its canvas.
    elbow=(V((0.10, 0.24, 0.33)), V((0.10, -0.24, 0.33))),
    wrist=(V((0.25, 0.12, 0.42)), V((0.25, -0.12, 0.42))),
    hand=((V((0.3, -0.6, -0.2)), V((0, 0, 1))), (V((0.3, 0.6, -0.2)), V((0, 0, 1)))),
    curl=(0.55, 0.55),
    hip=(V((0.02, 0.1, 0.11)), V((0.02, -0.1, 0.11))),
    knee=(V((0.30, 0.13, 0.43)), V((0.30, -0.12, 0.42))),
    ankle=(V((0.40, 0.13, 0.08)), V((0.41, -0.12, 0.08))),
    foot=(V((1, 0.1, 0)), V((1, -0.1, 0))),
    skirt=[V((0.09, 0.0, 0.17)), V((0.31, 0.0, 0.50))],
    table=None,
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


def _cap(P, H, crown, face, s=1.0):
    """A sorter's peaked cap (depot green cloth, the peak stiffened), on the crown of a skull or wherever it fell."""
    z = crown.normalized()
    x = (face - z * face.dot(z)).normalized()
    y = z.cross(x)
    R = Matrix((x, y, z)).transposed().to_4x4()
    c = Vector(H) + z * 0.088 * s - x * 0.008 * s
    P.add('cap', lambda bm: rounded_box((0.205 * s, 0.18 * s, 0.062 * s), c, p=2.6, cuts=4, dents=((0.004, 9.0),), seed=3.0,
                                        bm=bm, mat=0, rot=R), size=0.2)
    P.add('cap', lambda bm: rounded_box((0.075 * s, 0.17 * s, 0.009 * s), c + (x * 0.105 - z * 0.028) * s, p=3.0, cuts=2,
                                        bm=bm, mat=0, rot=R @ Matrix.Rotation(0.3, 4, 'Y')), size=0.2)


def sorter(J, bib=True, cap=False, seed=1.0):
    """One of the night shift, 76 years dead at the post: a dry dark-ivory skeleton (the skull's dome, its eye sockets
    and nose dark hollows, the jaw dropped; the spine, the rib cage, the pelvis, the long bones; the finger bones on
    the letters or the mailbag) in what is left of the clothes: the shirt rotted to a yoke of rags on the back and
    torn sleeves, the trousers collapsed onto the leg bones, the canvas apron (it lasted) hanging from its neck strap,
    its skirt over the lap, the boots. One Painted mesh in the remains atlas; no flesh, no face."""
    P = rh.Painted()
    Z = Vector((0, 0, 1))
    pel, ch, nk = J['pelvis'], J['chest'], J['neck']
    sl, sr = J['shoulder']
    up = (ch - pel).normalized()
    lat = (sl - sr)
    lat = (lat - up * lat.dot(up)).normalized()
    fwd = lat.cross(up)
    H, face, crown = J['head'], J['face'].normalized(), J['crown'].normalized()
    # The spine, the skull on it, the rib cage, the collar bones.
    t1 = ch - fwd * 0.05
    t12 = pel + (ch - pel) * 0.4 - fwd * 0.055
    sac = pel - fwd * 0.035 + up * 0.04
    base = H - crown * 0.055 - face * 0.012
    rh.spine(P, [sac, t12, (t12 + t1) / 2 - fwd * 0.015, t1, nk, base])
    rh.skull(P, H, face, crown, s=1.0, jaw=0.3)
    st = rh.ribcage(P, t1 - up * 0.01, t12, lat, fwd, s=1.0, n=8)
    for S in (sl, sr):
        P.add('bone', lambda bm, S=S: rh.long_bone(bm, st, S, 0.0065, knob=1.3, seg=5))
    lat_h = Vector((lat.x, lat.y, 0)).normalized()
    rh.pelvis(P, pel, Z, lat_h, lat_h.cross(Z))
    # Arms: the humerus, the two bones of the forearm, the hand.
    for s in range(2):
        S, E, W = J['shoulder'][s], J['elbow'][s], J['wrist'][s]
        hd, hn = J['hand'][s]
        P.add('bone', lambda bm, S=S, E=E: rh.long_bone(bm, S, E, 0.011, seg=6))
        sd = (E - S).cross(W - E)
        sd = sd.normalized() if sd.length > 1e-5 else lat
        for o in (-0.009, 0.009):
            P.add('bone', lambda bm, o=o, E=E, W=W, sd=sd: rh.long_bone(bm, E + sd * o, W + sd * o * 0.7, 0.0062, knob=1.4, seg=5))
        rh.hand(P, W, hd.normalized(), hn, s=1.0, curl=J['curl'][s])
    # Legs: the femur, the knee cap, the shin bones into the boots.
    for s in range(2):
        Hp, K, A, fd = J['hip'][s], J['knee'][s], J['ankle'][s], J['foot'][s].normalized()
        P.add('bone', lambda bm, Hp=Hp, K=K: rh.long_bone(bm, Hp, K, 0.013, seg=6))
        kn = (K - Hp).normalized()
        P.add('bone', lambda bm, K=K, kn=kn: add_sphere(bm, K + kn * 0.022 + Z * 0.012, 0.019, mat=0, seg=6))
        P.add('bone', lambda bm, K=K, A=A: rh.long_bone(bm, K, A + Z * 0.05, 0.011, seg=6))
        P.add('shoe', lambda bm, A=A, fd=fd: rounded_box((0.25, 0.095, 0.075), A + fd * 0.07 + Vector((0, 0, -0.035)) * (1 if abs(fd.z) < 0.5 else 0),
                                                          p=3.0, cuts=2, dents=((0.004, 9.0),), seed=seed + s, bm=bm, mat=0,
                                                          rot=_frame(fd, Vector((0, 0, 1))) @ Matrix.Rotation(math.pi / 2, 4, 'Y')))
        # The trousers, collapsed onto the bones: slung under the thigh, the shin torn short above the boot.
        rh.rag_tube(P, 'cloth', Hp, K + kn * 0.03, 0.045, sag=0.035, flat=0.7, seed=seed * 3 + s, ragged=0.12, side=Z)
        rh.rag_tube(P, 'cloth', K - kn * 0.01, A + Z * 0.06, 0.036, sag=0.0, flat=0.8, seed=seed * 5 + s, ragged=0.55)
    # The shirt: a yoke of rags over the shoulder blades, sleeves torn to the upper arm, a few strips hanging.
    rnd = random.Random(int(seed * 100) + 7)
    cols = 6
    pts = []
    for i in range(cols + 1):
        u = -1 + 2 * i / cols
        col = []
        rows = 3
        reach = 0.45 + 0.25 * rnd.random()
        for j in range(rows + 1):
            v = j / rows * reach
            p = t1.lerp(t12, v) - fwd * 0.045 + lat * u * 0.15
            over = max(0.0, abs(u) - 0.45)
            p += fwd * over * 0.12 - Z * over * 0.1
            col.append(p)
        pts.append(col)
    rh.cloth(P, 'rag', pts)
    for s, S in enumerate((sl, sr)):
        E = J['elbow'][s]
        rh.rag_tube(P, 'rag', S - (E - S).normalized() * 0.02, S.lerp(E, 0.5), 0.03, sag=0.02, seed=seed * 7 + s, ragged=0.6, seg=6, rows=2)
        rh.rag_strip(P, 'rag', S - fwd * 0.03 - Z * 0.02, -Z, fwd, 0.12 + 0.08 * rnd.random(), 0.05, seed=seed * 11 + s)
    # The apron: canvas outlasts the shirt. Its neck strap, the bib hanging from it below the ribs (seated), the skirt
    # over the lap and the knees, the ties at the back.
    P.add('apron', lambda bm: add_torus(bm, nk + fwd * 0.012 - up * 0.01, (up * 0.8 + fwd * 0.45).normalized(), 0.058, 0.0055,
                                        mat=0, seg=12, rseg=4))
    if bib:
        top = [nk + fwd * 0.06 + lat * u * 0.085 for u in (-1, -0.33, 0.33, 1)]
        bot = [pel + up * 0.14 + fwd * 0.12 + lat * u * 0.13 for u in (-1, -0.33, 0.33, 1)]
        pts = [[top[i].lerp(bot[i], v) - Z * 0.09 * math.sin(math.pi * v) for v in (0, 0.25, 0.5, 0.75, 1.0)] for i in range(4)]
        rh.cloth(P, 'apron', pts)
    sk = J['skirt']
    pts = []
    for u in (-1, -0.5, 0.0, 0.5, 1.0):
        col = []
        for k, p in enumerate(sk):
            q = p + lat * u * 0.17
            if 0 < k < len(sk) - 1 or len(sk) == 2:
                q = q - Z * 0.03 * (1 - u * u)                 # sagging between the thighs
            col.append(q)
        pts.append(col)
    rh.cloth(P, 'apron', pts)
    back = pel - fwd * 0.08 + up * 0.08
    for s in (1, -1):
        P.add('apron', lambda bm, s=s: add_cyl(bm, pel + lat * s * 0.15 + fwd * 0.04 + up * 0.08, back, 0.006, mat=0, seg=4))
        P.add('apron', lambda bm, s=s: add_cyl(bm, back, back + lat * s * 0.03 - Z * 0.11, 0.007, 0.005, mat=0, seg=4))
    if cap:
        _cap(P, H, crown, face)
    # The letters under the right hand's finger bones, on the table.
    if J['table'] is not None:
        W, (hd, hn) = J['wrist'][1], J['hand'][1]
        c = W + hd.normalized() * 0.07
        for k in range(4):
            P.add('paper', lambda bm, k=k: add_box(bm, (c.x + 0.02 * k - 0.03, c.y + 0.015 * (k % 2), J['table'] + 0.0016 + 0.0032 * k),
                                                     (0.16, 0.11, 0.003), mat=0, rot=Matrix.Rotation(0.25 * k - 0.3, 4, 'Z')), size=0.2)
    return P


def build_sorters(coll):
    meshes = {'seated': sorter(SEATED, bib=True, cap=False, seed=1.0).mesh('SorterRemainsSeated', 'RemainsMat'),
              'sitting': sorter(SITTING, bib=False, cap=True, seed=2.0).mesh('SorterRemainsSitting', 'RemainsMat')}
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
    # Sorter1's cap, fallen by the stool toward the wall (in this object: one draw call for the bag and the cap).
    _cap(P, Vector((CAP_FLOOR[0], CAP_FLOOR[1], -0.056)), Vector((0.12, 0.05, 1.0)), Vector((0.6, 0.8, 0.0)))
    return P.obj('SorterMailbag', 'RemainsMat', coll)


# --------------------------------------------------------------------------
# What killed them (DL-02, pass 5): the air was cut. Between the tea corner and the pigeonholes, behind the sorting
# table's end: the bulkhead to the stairs, welded shut, the order pasted on it, hands and nails at its foot; over it
# the depot's air gauge on zero, and over that the dead fan.
# --------------------------------------------------------------------------

def _uv_grid(P, cell, pts, uvs):
    """A sheet pts[i][j] with its own UVs uvs[i][j] (fractions of the cell), wound +u x +v."""
    u0, v0, u1, v1 = P.rect_of(cell)
    tmp = bmesh.new()
    uvl = tmp.loops.layers.uv.new('UVMap')
    nx, ny = len(pts) - 1, len(pts[0]) - 1
    vs = [[tmp.verts.new(pts[i][j]) for j in range(ny + 1)] for i in range(nx + 1)]
    for i in range(nx):
        for j in range(ny):
            f = tmp.faces.new((vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1]))
            for lp, (a, b) in zip(f.loops, (uvs[i][j], uvs[i + 1][j], uvs[i + 1][j + 1], uvs[i][j + 1])):
                lp[uvl].uv = (u0 + (u1 - u0) * a, v0 + (v1 - v0) * b)
    P._merge(tmp)


def _bead(P, pts, seed, r=0.0085):
    """A weld bead along pts: lumpy, uneven."""
    rnd = random.Random(int(seed * 1000) + 3)
    path = []
    for a, b in zip(pts, pts[1:]):
        a, b = Vector(a), Vector(b)
        k = max(2, int((b - a).length / 0.022))
        path += [a.lerp(b, i / k) for i in range(k)]
    path.append(Vector(pts[-1]))
    rs = [r * (0.75 + 0.5 * rnd.random()) for _ in path]
    rs[0] = rs[-1] = r * 0.4
    P.add('weld', lambda bm: rh.sweep(bm, path, rs, seg=5), size=0.08)


def _place(P, ob_name, origin, coll):
    P.transform(Matrix.Translation(-Vector(origin)))
    ob = P.obj(ob_name, 'StoryAirMat', coll)
    ob.location = origin
    return ob


def build_cause(coll):
    path = os.path.join(TEX, 'story_air.png')
    if not os.path.exists(path):
        make_story_air(path)
    _image_material('StoryAirMat', path, rough=0.72)
    cx, wy = DOOR_X, WALL_Y
    lw, ltop = DOOR_LEAF
    fy0, fy1 = wy - 0.085, wy - 0.025                         # the frame's depth, proud of the wall and its dado
    ly = wy - 0.068                                           # the leaf's face (recessed in its frame)
    rnd = random.Random(5502)
    # ---- StoryWeldedDoor: the frame, the leaf and its painted face, the hinges, the dogging lever, the welds.
    P = rh.Painted(air_uv)
    jw = 0.09
    for sx in (-1, 1):
        P.add('steel', lambda bm, sx=sx: rh.rbox(bm, cx + sx * (lw / 2 + 0.005), cx + sx * (lw / 2 + 0.005 + jw), fy0, fy1, 0.0,
                                                 ltop + 0.11, p=8, cuts=2), size=0.25)
    P.add('steel', lambda bm: rh.rbox(bm, cx - lw / 2 - 0.005 - jw, cx + lw / 2 + 0.005 + jw, fy0, fy1, ltop + 0.005, ltop + 0.11,
                                      p=8, cuts=2), size=0.25)
    P.add('steel', lambda bm: rh.rbox(bm, cx - lw / 2 - jw, cx + lw / 2 + jw, fy0 - 0.05, fy1, 0.0, 0.035, p=6, cuts=2), size=0.25)
    P.add('leaf', lambda bm: rh.rbox(bm, cx - lw / 2, cx + lw / 2, ly, ly + 0.035, 0.04, ltop, p=10, cuts=2), size=0.3)
    P.quads('door', [[Vector((cx - lw / 2 + 0.004, ly - 0.0012, 0.044)), Vector((cx + lw / 2 - 0.004, ly - 0.0012, 0.044)),
                      Vector((cx + lw / 2 - 0.004, ly - 0.0012, ltop - 0.004)), Vector((cx - lw / 2 + 0.004, ly - 0.0012, ltop - 0.004))]])
    for z in (0.3, 1.0, 1.7):                                 # hinges on the left
        P.add('steel', lambda bm, z=z: add_cyl(bm, (cx - lw / 2 - 0.012, ly - 0.012, z - 0.07), (cx - lw / 2 - 0.012, ly - 0.012, z + 0.07),
                                               0.02, mat=0, seg=10), size=0.15)
    hub = Vector((cx + lw / 2 - 0.09, ly - 0.004, 1.02))      # the dogging lever, down, welded to its hub
    P.add('steel', lambda bm: add_cyl(bm, hub, hub - Vector((0, 0.03, 0)), 0.035, mat=0, seg=14), size=0.15)
    P.add('steel', lambda bm: add_cyl(bm, hub - Vector((0, 0.02, 0)), hub + Vector((-0.06, -0.03, -0.2)), 0.013, mat=0, seg=8), size=0.15)
    P.add('weld', lambda bm: add_torus(bm, hub - Vector((0, 0.03, 0)), (0, 1, 0), 0.036, 0.009, mat=0, seg=14, rseg=4), size=0.08)
    # The welds: a bead all round the leaf's seam, and straps across it, beaded at their ends.
    by = ly - 0.006
    for k, sx in enumerate((-1, 1)):
        x = cx + sx * (lw / 2 + 0.002)
        _bead(P, [(x, by, 0.045), (x, by, ltop)], seed=k + 1)
    _bead(P, [(cx - lw / 2, by, ltop + 0.004), (cx + lw / 2, by, ltop + 0.004)], seed=3)
    _bead(P, [(cx - lw / 2, by, 0.042), (cx + lw / 2, by, 0.042)], seed=4)
    for sx in (-1, 1):
        x = cx + sx * (lw / 2 + 0.002)
        for z in (0.26, 0.86, 1.52):
            z += rnd.uniform(-0.04, 0.04)
            tilt = rnd.uniform(-0.12, 0.12)
            P.add('fan', lambda bm, x=x, z=z, tilt=tilt: add_box(bm, (x, by - 0.006, z), (0.17, 0.012, 0.05), mat=0,
                                                                 rot=Matrix.Rotation(tilt, 4, 'Y')), size=0.15)
            for ex in (-0.085, 0.085):
                p = Vector((x + ex * math.cos(tilt), by - 0.008, z - ex * math.sin(tilt)))
                _bead(P, [p + Vector((0, 0, -0.03)), p + Vector((0, 0, 0.03))], seed=x * 7 + z + ex, r=0.007)
    for x in (cx - 0.22, cx + 0.2):
        P.add('fan', lambda bm, x=x: add_box(bm, (x, by - 0.006, ltop + 0.01), (0.05, 0.012, 0.17), mat=0), size=0.15)
        for ez in (-0.085, 0.085):
            p = Vector((x, by - 0.008, ltop + 0.01 + ez))
            _bead(P, [p + Vector((-0.03, 0, 0)), p + Vector((0.03, 0, 0))], seed=x + ez, r=0.007)
    door = _place(P, 'StoryWeldedDoor', (cx, ly, 0.0), coll)

    # ---- StoryAirNotice: the order, pasted on the leaf at a reader's height, its paper cockled, one corner torn away.
    P = rh.Painted(air_uv)
    nw, nh = NOTICE
    nc = Vector((cx - 0.03, ly - 0.0035, NOTICE_Z))
    nx, nz = 6, 8
    pts, uvs = [], []
    for i in range(nx + 1):
        prow, urow = [], []
        for j in range(nz + 1):
            u, v = i / nx, j / nz
            e = (u + (1 - v) - 1.78) / 2                       # the torn corner, lower right
            if e > 0:
                u, v = u - e, v + e
            yo = -0.004 * math.sin(math.pi * u) * math.sin(math.pi * v)
            if u < 0.3 and v > 0.75:                          # the top left corner peeling off the paint
                yo -= 0.03 * ((0.3 - u) / 0.3) ** 1.5 * ((v - 0.75) / 0.25) ** 1.5
            prow.append(nc + Vector(((u - 0.5) * nw, yo, (v - 0.5) * nh)))
            urow.append((u, v))
        pts.append(prow)
        uvs.append(urow)
    _uv_grid(P, 'notice', pts, uvs)
    notice = _place(P, 'StoryAirNotice', tuple(nc), coll)
    notice.rotation_euler = (0, math.radians(-1.5), 0)

    # ---- StoryAirGauge: the depot's air gauge over the door, its needle on zero against the stop, in the NO AIR red;
    # over it, the fan's grille, the fan dead behind it, and the sensing pipe between them.
    P = rh.Painted(air_uv)
    gz, gr = GAUGE_Z, GAUGE_R
    gy = wy - 0.075                                           # the dial's face
    P.add('steel', lambda bm: add_cyl(bm, (cx, wy - 0.005, gz), (cx, gy + 0.004, gz), gr + 0.025, mat=0, seg=32), size=0.3)
    P.add('steel', lambda bm: add_torus(bm, (cx, gy - 0.002, gz), (0, 1, 0), gr + 0.012, 0.014, mat=0, seg=32, rseg=5), size=0.3)
    n = 40
    tmp = bmesh.new()
    uvl = tmp.loops.layers.uv.new('UVMap')
    u0, v0, u1, v1 = air_uv('gauge')
    for i in range(n):
        a0, a1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n
        tri = [Vector((cx, gy, gz)), Vector((cx + gr * math.cos(a0), gy, gz + gr * math.sin(a0))),
               Vector((cx + gr * math.cos(a1), gy, gz + gr * math.sin(a1)))]
        f = tmp.faces.new([tmp.verts.new(p) for p in tri])
        for lp, (a, b) in zip(f.loops, ((0.5, 0.5), (0.5 + 0.49 * math.cos(a0), 0.5 + 0.49 * math.sin(a0)),
                                        (0.5 + 0.49 * math.cos(a1), 0.5 + 0.49 * math.sin(a1)))):
            lp[uvl].uv = (u0 + (u1 - u0) * a, v0 + (v1 - v0) * b)
    bmesh.ops.remove_doubles(tmp, verts=tmp.verts[:], dist=1e-6)
    P._merge(tmp)
    zero = math.radians(-135.0)                               # the scale runs 270 degrees clockwise from lower left
    d = Vector((math.sin(zero), 0, math.cos(zero)))
    c = Vector((cx, gy - 0.006, gz))
    P.add('needle', lambda bm: d17.add_wedge(bm, c - d * 0.045, c + d * gr * 0.86, 0.024, 0.005, 0.005, 0.004,
                                             (d.z, 0, -d.x), mat=0), size=0.1)
    P.add('needle', lambda bm: add_cyl(bm, c + Vector((0, 0.004, 0)), c - Vector((0, 0.008, 0)), 0.022, mat=0, seg=12), size=0.1)
    pin = Vector((cx, gy, gz)) + Vector((math.sin(zero - 0.12), 0, math.cos(zero - 0.12))) * gr * 0.8
    P.add('steel', lambda bm: add_cyl(bm, pin, pin - Vector((0, 0.012, 0)), 0.006, mat=0, seg=6), size=0.1)
    # The grille: a frame, louvres, the dark duct, the fan's hub and blades stopped behind.
    fz0, fz1 = FAN_Z
    fw = FAN_W
    fz = (fz0 + fz1) / 2
    for a, b, c0, c1 in ((cx - fw / 2, cx + fw / 2, fz0, fz0 + 0.045), (cx - fw / 2, cx + fw / 2, fz1 - 0.045, fz1),
                         (cx - fw / 2, cx - fw / 2 + 0.045, fz0, fz1), (cx + fw / 2 - 0.045, cx + fw / 2, fz0, fz1)):
        P.add('steel', lambda bm, a=a, b=b, c0=c0, c1=c1: rh.rbox(bm, a, b, wy - 0.075, wy - 0.002, c0, c1, p=6, cuts=2), size=0.25)
    P.quads('hole', [[Vector((cx - fw / 2 + 0.04, wy - 0.008, fz0 + 0.04)), Vector((cx + fw / 2 - 0.04, wy - 0.008, fz0 + 0.04)),
                      Vector((cx + fw / 2 - 0.04, wy - 0.008, fz1 - 0.04)), Vector((cx - fw / 2 + 0.04, wy - 0.008, fz1 - 0.04))]])
    hc = Vector((cx, wy - 0.03, fz))
    P.add('fan', lambda bm: add_cyl(bm, hc + Vector((0, 0.012, 0)), hc - Vector((0, 0.02, 0)), 0.045, mat=0, seg=12), size=0.1)
    for k in range(4):
        a = math.radians(20 + 90 * k)
        dv = Vector((math.cos(a), 0, math.sin(a)))
        P.add('fan', lambda bm, dv=dv: d17.add_wedge(bm, hc + dv * 0.035, hc + dv * 0.17, 0.06, 0.1, 0.006, 0.004,
                                                     (Vector((0, 1, 0)) * 0.5 + Vector((dv.z, 0, -dv.x))).normalized(), mat=0), size=0.15)
    z = fz0 + 0.075
    while z < fz1 - 0.05:
        P.add('steel', lambda bm, z=z: add_box(bm, (cx, wy - 0.06, z), (fw - 0.09, 0.006, 0.04), mat=0,
                                               rot=Matrix.Rotation(math.radians(40), 4, 'X')), size=0.25)
        z += 0.062
    pp = cx + 0.14
    P.add('steel', lambda bm: add_cyl(bm, (pp, wy - 0.03, gz + gr * 0.9), (pp, wy - 0.03, fz0 + 0.01), 0.009, mat=0, seg=6), size=0.1)
    gauge = _place(P, 'StoryAirGauge', (cx, gy, gz), coll)
    return door, notice, gauge


def move_lore_board():
    """The pass 3 notice board (art/pass3/build_lore.py: NIGHT SHIFT CUT) hung where the welded door now is: it goes
    to the wall over the passage DL-02 is entered by, where the shift would have read it coming on."""
    for name in ('LoreNoticeBoard', 'LoreNoticeFrame'):
        ob = bpy.data.objects.get(name)
        if ob is not None:
            ob.location += Vector(LORE_MOVE)


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
    move_lore_board()
    build_cause(coll)
    build_ways(coll)
    build_dispatch_line(dl01, coll)


def add_clips(dl01, arm):
    pass
