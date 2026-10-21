"""Painted textures for DL-02 The Sorting Hall and the chapter's three undelivered letters.

    python textures_sorting_hall.py          # (re)writes every PNG in ./textures

The letters' textures are shared: DL-06 (art/dl03) and DL-09 (art/dl05) use letter_heap.png and
letter_c110.png from here. Each letter texture is an atlas: the envelope's front on the left half, its
back on the right half (see build_sorting_hall.letter_mesh for the UV layout).
"""
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')

INK = (34, 30, 36)
PAPER = (206, 194, 164)
CREAM = (222, 212, 184)
CHALK = (218, 216, 200)


def _font(size, kind='sans-bold'):
    from PIL import ImageFont
    paths = {'sans-bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
             'sans': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
             'mono': '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
             'serif': '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'}
    try:
        return ImageFont.truetype(paths[kind], size)
    except OSError:
        return ImageFont.load_default()


def _age(img, seed, amount=0.5, blur=0.7):
    """Stains, foxing and a little blur, so nothing looks freshly printed."""
    from PIL import ImageDraw, ImageFilter
    rnd = random.Random(seed)
    d = ImageDraw.Draw(img, 'RGBA')
    w, h = img.size
    for _ in range(int(40 * amount)):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(3, w * 0.07)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(70, 50, 25, rnd.randint(5, 20)))
    for _ in range(int(10 * amount)):
        x = rnd.uniform(0, w)
        d.line((x, 0, x + rnd.uniform(-20, 20), h), fill=(40, 30, 20, rnd.randint(5, 14)), width=rnd.randint(2, 6))
    return img.filter(ImageFilter.GaussianBlur(blur))


def _save(img, name, colors=48):
    """Flat painted textures: a small palette keeps them light in set.glb."""
    from PIL import Image
    os.makedirs(TEX, exist_ok=True)
    q = img.convert('RGB').quantize(colors, method=Image.Quantize.MEDIANCUT)
    q.save(os.path.join(TEX, name), optimize=True)


def _scribble(d, x0, y, w, rnd, fill, width=3, amp=5):
    """A line of handwriting without words: a loose wave with loops."""
    pts = []
    x = x0
    while x < x0 + w:
        pts.append((x, y + rnd.uniform(-amp, amp) * (0.5 + 0.5 * math.sin(x * 0.4))))
        x += rnd.uniform(4, 8)
    d.line(pts, fill=fill, width=width, joint='curve')
    for _ in range(int(w / 40)):
        cx = rnd.uniform(x0, x0 + w)
        d.arc((cx - 5, y - 9, cx + 5, y + 2), 0, 300, fill=fill, width=max(1, width - 1))


# --------------------------------------------------------------------------
# The letters
# --------------------------------------------------------------------------

LW, LH = 320, 224                     # one face of the atlas (0.16 x 0.11 m, about 2 px per mm)


def _stamp(d, x, y, colour, glyph, rnd):
    """A postage stamp with perforated edges and a small pictogram."""
    w, h = 46, 56
    d.rectangle((x, y, x + w, y + h), fill=(236, 230, 214))
    for k in range(0, w + 1, 6):                      # perforations
        d.ellipse((x + k - 2, y - 2, x + k + 2, y + 2), fill=PAPER)
        d.ellipse((x + k - 2, y + h - 2, x + k + 2, y + h + 2), fill=PAPER)
    for k in range(0, h + 1, 6):
        d.ellipse((x - 2, y + k - 2, x + 2, y + k + 2), fill=PAPER)
        d.ellipse((x + w - 2, y + k - 2, x + w + 2, y + k + 2), fill=PAPER)
    d.rectangle((x + 5, y + 5, x + w - 5, y + h - 5), fill=colour)
    cx, cy = x + w / 2, y + h / 2 + 2
    pale = (230, 222, 196)
    if glyph == 'lamp':                               # a lamp, the refuge's emblem
        d.polygon([(cx - 11, cy - 2), (cx + 11, cy - 2), (cx + 6, cy - 12), (cx - 6, cy - 12)], fill=pale)
        d.ellipse((cx - 5, cy - 1, cx + 5, cy + 9), fill=pale)
        d.line((cx, cy - 20, cx, cy - 12), fill=pale, width=2)
    elif glyph == 'tree':
        d.rectangle((cx - 2, cy + 2, cx + 2, cy + 14), fill=pale)
        d.ellipse((cx - 12, cy - 16, cx + 12, cy + 6), fill=pale)
    else:                                             # 'arch': a viaduct
        d.rectangle((cx - 14, cy - 10, cx + 14, cy - 5), fill=pale)
        for k in (-10, 0, 10):
            d.rectangle((cx + k - 3, cy - 5, cx + k + 3, cy + 14), fill=pale)


def _postmark(d, cx, cy, year, rnd, ink=(48, 44, 60)):
    """A round postmark, 'P.A. 310', with wavy cancel lines running off it."""
    r = 30
    d.ellipse((cx - r, cy - r, cx + r, cy + r), outline=ink, width=3)
    d.ellipse((cx - r + 7, cy - r + 7, cx + r - 7, cy + r - 7), outline=ink, width=1)
    d.text((cx, cy - 7), 'P.A.', font=_font(12), fill=ink, anchor='mm')
    d.text((cx, cy + 8), str(year), font=_font(17), fill=ink, anchor='mm')
    for k in range(4):
        y = cy - 15 + k * 10
        pts = [(cx + r + 4 + t, y + 3 * math.sin(t * 0.25)) for t in range(0, 70, 4)]
        d.line(pts, fill=ink, width=2)


def _address(d, x, y, room, rnd, ink=INK):
    """Two lines of wordless handwriting, then the ring and room in clear capitals."""
    _scribble(d, x, y, 120, rnd, ink, 3)
    _scribble(d, x, y + 24, 96, rnd, ink, 3)
    d.text((x, y + 40), room, font=_font(38, 'serif'), fill=ink)
    d.line((x, y + 88, x + 150, y + 86), fill=ink, width=2)


def _back(d, ox, rnd):
    """The back of an envelope: the flap's V and the side seams."""
    line = (150, 138, 112)
    d.line((ox + 4, 6, ox + LW / 2, LH * 0.58, ox + LW - 4, 6), fill=line, width=3)
    d.line((ox + 4, LH - 6, ox + LW * 0.38, LH * 0.5), fill=line, width=2)
    d.line((ox + LW - 4, LH - 6, ox + LW * 0.62, LH * 0.5), fill=line, width=2)


def _child_drawing(d, ox, rnd):
    """In wax crayon on the back of the heap letter: a little courier carrying a parcel to a house
    under a big sun, a child waving at the window, and a row of hearts. No words."""
    def crayon(pts, colour, width=5, passes=3, jitter=1.6):
        for _ in range(passes):
            q = [(x + rnd.uniform(-jitter, jitter), y + rnd.uniform(-jitter, jitter)) for x, y in pts]
            d.line(q, fill=colour, width=width, joint='curve')

    def circle(cx, cy, r, colour, width=5, n=28):
        crayon([(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n + 1)],
               colour, width)
    blue, orange, green, brown, pink = (52, 86, 168), (226, 138, 40), (70, 140, 70), (120, 80, 50), (214, 92, 120)
    X = lambda v: ox + v                              # noqa: E731
    # The sun, with rays.
    circle(X(270), 42, 20, orange)
    for k in range(9):
        a = 2 * math.pi * k / 9
        crayon([(X(270) + 26 * math.cos(a), 42 + 26 * math.sin(a)), (X(270) + 38 * math.cos(a), 42 + 38 * math.sin(a))], orange, 4, 2)
    # The house, its window and a waving child in it.
    crayon([(X(170), 190), (X(170), 112), (X(235), 112), (X(235), 190)], brown)
    crayon([(X(162), 116), (X(202), 78), (X(243), 116)], brown)
    crayon([(X(186), 128), (X(218), 128), (X(218), 158), (X(186), 158), (X(186), 128)], blue, 4)
    circle(X(202), 137, 5, pink, 3, 12)
    crayon([(X(202), 142), (X(202), 152)], pink, 3, 2)
    crayon([(X(196), 146), (X(210), 140), (X(214), 133)], pink, 3, 2)
    # The courier: a box body on two legs, a flat head, three antenna stalks, carrying a parcel.
    crayon([(X(52), 150), (X(98), 150), (X(98), 118), (X(52), 118), (X(52), 150)], blue)
    crayon([(X(48), 112), (X(102), 112), (X(98), 92), (X(52), 92), (X(48), 112)], blue)
    circle(X(66), 102, 4, blue, 3, 10)
    circle(X(86), 102, 4, blue, 3, 10)
    for k in range(3):
        crayon([(X(84 + k * 5), 92), (X(88 + k * 7), 74 - k * 4)], blue, 3, 2)
    crayon([(X(62), 150), (X(58), 186)], blue)
    crayon([(X(88), 150), (X(92), 186)], blue)
    crayon([(X(98), 128), (X(126), 132)], blue, 4)
    crayon([(X(122), 122), (X(150), 122), (X(150), 146), (X(122), 146), (X(122), 122)], orange, 4)
    crayon([(X(136), 122), (X(136), 146)], orange, 3, 2)
    # The ground, and a row of hearts along it.
    crayon([(X(16), 192), (X(304), 194)], green, 6)
    for k in range(4):
        cx = X(250 + k * 16)
        crayon([(cx, 176), (cx - 6, 168), (cx - 3, 163), (cx, 167), (cx + 3, 163), (cx + 6, 168), (cx, 176)], pink, 3, 2)


def make_letter(name, room, year, stamp, glyph, seed, back='plain', pictogram='house'):
    from PIL import Image, ImageDraw
    rnd = random.Random(seed)
    img = Image.new('RGB', (2 * LW, LH), PAPER)
    d = ImageDraw.Draw(img)
    # Front: address, stamp, postmark, a small pictogram in the corner.
    d.rectangle((2, 2, LW - 3, LH - 3), outline=(178, 164, 134), width=2)
    _stamp(d, LW - 64, 14, stamp, glyph, rnd)
    _postmark(d, LW - 116, 54, year, rnd)
    _address(d, 92, 100, room, rnd)
    pic = (90, 84, 100)
    if pictogram == 'house':
        d.polygon([(22, 44), (42, 26), (62, 44)], outline=pic, width=3)
        d.rectangle((28, 44, 56, 66), outline=pic, width=3)
    elif pictogram == 'heart':
        d.ellipse((24, 28, 42, 46), outline=pic, width=3)
        d.ellipse((38, 28, 56, 46), outline=pic, width=3)
        d.polygon([(25, 41), (40, 64), (55, 41)], outline=pic, width=3)
    else:                                             # 'star'
        pts = []
        for k in range(10):
            a = -math.pi / 2 + math.pi * k / 5
            r = 20 if k % 2 == 0 else 8
            pts.append((40 + r * math.cos(a), 46 + r * math.sin(a)))
        d.polygon(pts, outline=pic, width=3)
    # Back.
    _back(d, LW, rnd)
    if back == 'drawing':
        _child_drawing(d, LW, rnd)
    img = _age(img, seed, 0.6, blur=0.6)
    _save(img, name, 40)


def make_mara_letter(name='letter_tube.png'):
    """The tube letter (pass 3): Mara's own letter to the post office, in a six-year-old's pencil capitals,
    "DEAR POST, MY BIRTHDAY PARCEL HASNT COME. IS D-17 LOST? LOVE MARA C-114", stamped and postmarked P.A. 310.
    On the back, in crayon, what it says without words: a girl crying at the door of her house beside a crooked
    tree, and far off in the dark, a little courier with a parcel and a question mark over it, its dotted path
    looping. Drawn at twice the other letters' size so the hand reads (the UVs are fractions of the atlas)."""
    import sys
    from PIL import Image, ImageDraw
    sys.path.insert(0, os.path.join(HERE, '..', 'pass3'))
    import handwriting as hw
    rnd = random.Random(42)
    S = 2
    fw, fh = LW * S, LH * S
    img = Image.new('RGB', (2 * fw, fh), (214, 204, 178))                  # a child's notepaper envelope, paler
    d = ImageDraw.Draw(img)
    d.rectangle((3, 3, fw - 4, fh - 4), outline=(178, 164, 134), width=3)
    # The stamp and the postmark, top right (drawn at 1x, scaled up).
    tmp = Image.new('RGB', (130, 90), (214, 204, 178))
    td = ImageDraw.Draw(tmp)
    _stamp(td, 74, 10, (60, 90, 120), 'lamp', rnd)
    _postmark(td, 40, 48, 310, rnd)
    img.paste(tmp.resize((195, 135)), (fw - 205, 8))
    pencil = (58, 58, 66)
    lines = [('DEAR POST,', 42, 0.5), ('MY BIRTHDAY', 40, 0.4), ('PARCEL HASNT', 46, 0.42),
             ('COME. IS D-17', 46, 0.42), ('LOST?', 54, 0.5), ('LOVE MARA', 44, 0.45)]
    y = 22
    for i, (text, size, spacing) in enumerate(lines):
        x = 24 + rnd.uniform(0, 14)
        mirror = {text.index('N')} if text.startswith('PARCEL') else set()      # the N in HASNT, backwards
        if text.startswith('COME'):
            mirror = {text.index('7')}                                            # and the 7
        x = hw.write(d, text, x, y, size, 'child', pencil, 6, seed=60 + i, mirror=mirror, spacing=spacing)
        if text.startswith('LOVE'):
            hx, hy = x + 16, y + 24                                               # a heart, coloured in
            heart = (206, 64, 96)
            d.ellipse((hx - 2, hy - 14, hx + 16, hy + 4), fill=heart)
            d.ellipse((hx + 12, hy - 14, hx + 30, hy + 4), fill=heart)
            d.polygon([(hx - 1, hy - 2), (hx + 29, hy - 2), (hx + 14, hy + 20)], fill=heart)
            hw.write(d, 'C-114', x + 64, y + 8, 36, 'child', pencil, 5, seed=70, spacing=0.5)
        y += 70
    # Back: the flap, then the drawing in wax crayon.
    ox = fw
    line = (150, 138, 112)
    d.line((ox + 8, 12, ox + fw / 2, fh * 0.58, ox + fw - 8, 12), fill=line, width=5)
    blue, orange, green, brown, pink, grey, dark = ((52, 86, 168), (226, 138, 40), (70, 140, 70), (120, 80, 50),
                                                    (214, 92, 120), (110, 110, 120), (40, 40, 52))
    cr = random.Random(43)
    X = lambda v: ox + v                                                          # noqa: E731
    hw.crayon(d, [(X(14), 410), (X(330), 412)], green, 8, rnd=cr)                # the ground at home
    # The house: walls, roof, a window, the door open, and a girl in the doorway crying.
    hw.crayon(d, [(X(100), 410), (X(100), 262), (X(250), 262), (X(250), 410)], brown, 7, rnd=cr)
    hw.crayon(d, [(X(84), 268), (X(175), 186), (X(266), 268)], brown, 7, rnd=cr)
    hw.crayon(d, [(X(198), 286), (X(234), 286), (X(234), 320), (X(198), 320), (X(198), 286)], blue, 5, rnd=cr)
    hw.crayon(d, [(X(122), 410), (X(122), 318), (X(178), 318), (X(178), 410)], dark, 5, rnd=cr)
    gx = 300                                                                     # her, outside, crying
    hw.crayon_circle(d, X(gx), 300, 22, pink, 6, rnd=cr)
    hw.crayon(d, [(X(gx - 8), 312), (X(gx), 306), (X(gx + 8), 312)], pink, 3, 2, rnd=cr)   # a turned-down mouth
    hw.crayon(d, [(X(gx - 20), 288), (X(gx - 26), 306), (X(gx - 24), 322)], brown, 5, 2, rnd=cr)   # her hair
    hw.crayon(d, [(X(gx + 20), 288), (X(gx + 26), 306), (X(gx + 24), 322)], brown, 5, 2, rnd=cr)
    hw.crayon(d, [(X(gx - 20), 290), (X(gx - 6), 278), (X(gx + 10), 278), (X(gx + 20), 290)], brown, 5, 2, rnd=cr)
    for tx, ty in ((gx - 10, 304), (gx - 13, 322), (gx - 12, 340), (gx + 10, 306), (gx + 14, 326)):   # tears
        d.ellipse((X(tx) - 4, ty - 6, X(tx) + 4, ty + 6), fill=(60, 120, 220))
    hw.crayon(d, [(X(gx), 324), (X(gx - 30), 384), (X(gx + 30), 384), (X(gx), 324)], blue, 7, rnd=cr)   # her dress
    hw.crayon(d, [(X(gx - 12), 340), (X(gx - 30), 364)], pink, 5, rnd=cr)
    hw.crayon(d, [(X(gx + 12), 340), (X(gx + 30), 364)], pink, 5, rnd=cr)
    hw.crayon(d, [(X(gx - 12), 384), (X(gx - 14), 410)], pink, 5, rnd=cr)
    hw.crayon(d, [(X(gx + 12), 384), (X(gx + 14), 410)], pink, 5, rnd=cr)
    hw.crooked_tree(d, X(48), 410, 150, brown, cr, width=8, leaves=green)        # the crooked tree by the house
    # Night: a moon and stars over everything.
    hw.crayon_circle(d, X(300), 64, 26, (220, 200, 90), 6, rnd=cr)
    hw.crayon_circle(d, X(312), 56, 22, (214, 204, 178), 10, rnd=cr)
    for sx, sy in ((X(220), 40), (X(380), 30), (X(470), 70), (X(150), 90)):
        hw.crayon(d, [(sx - 8, sy), (sx + 8, sy)], (220, 200, 90), 3, 2, rnd=cr)
        hw.crayon(d, [(sx, sy - 8), (sx, sy + 8)], (220, 200, 90), 3, 2, rnd=cr)
    # Far off, in a dark scribble, the little courier carrying a parcel, with a question mark over it.
    for k in range(80):                                                           # the dark: loops of pencil round him
        a_, rr = cr.uniform(0, 2 * math.pi), cr.uniform(78, 130)
        cx_, cy_, r_ = X(500 + rr * math.cos(a_) * 0.9), 316 + rr * math.sin(a_) * 0.85, cr.uniform(14, 30)
        hw.crayon_circle(d, cx_, cy_, r_, (84, 84, 98), 3, 14, rnd=cr, ry=r_ * cr.uniform(0.5, 1.0))
    rx = 500
    hw.crayon(d, [(X(rx - 34), 350), (X(rx + 26), 350), (X(rx + 26), 310), (X(rx - 34), 310), (X(rx - 34), 350)], blue, 6, rnd=cr)
    hw.crayon(d, [(X(rx - 40), 304), (X(rx + 32), 304), (X(rx + 26), 278), (X(rx - 34), 278), (X(rx - 40), 304)], blue, 6, rnd=cr)
    for ex in (rx - 18, rx + 8):
        hw.crayon_circle(d, X(ex), 291, 5, (230, 210, 120), 4, 10, rnd=cr)
    for k in range(3):
        hw.crayon(d, [(X(rx + 10 + k * 6), 278), (X(rx + 16 + k * 9), 254 - k * 5)], blue, 3, 2, rnd=cr)
    hw.crayon(d, [(X(rx - 22), 350), (X(rx - 26), 396)], blue, 6, rnd=cr)
    hw.crayon(d, [(X(rx + 12), 350), (X(rx + 16), 396)], blue, 6, rnd=cr)
    hw.crayon(d, [(X(rx - 34), 326), (X(rx - 62), 330)], blue, 5, rnd=cr)
    hw.crayon(d, [(X(rx - 98), 314), (X(rx - 62), 314), (X(rx - 62), 344), (X(rx - 98), 344), (X(rx - 98), 314)], orange, 6, rnd=cr)
    hw.crayon(d, [(X(rx - 80), 314), (X(rx - 80), 344)], orange, 3, 2, rnd=cr)
    hw.write(d, '?', X(rx - 12), 176, 64, 'child', (190, 60, 60), 8, seed=71)
    # Its path home: dots that wander and loop and never reach the door.
    path = [(rx - 100, 390), (rx - 120, 410), (rx - 150, 396), (rx - 140, 370), (rx - 116, 384), (rx - 130, 420), (rx - 160, 428)]
    for a, b in zip(path, path[1:]):
        for t in range(0, 10, 3):
            px, py = a[0] + (b[0] - a[0]) * t / 10, a[1] + (b[1] - a[1]) * t / 10
            d.ellipse((X(px) - 3, py - 3, X(px) + 3, py + 3), fill=grey)
    img = _age(img, 44, 0.5, blur=0.7)
    _save(img, name, 64)


def make_letters():
    make_mara_letter('letter_tube.png')                    # pass 3: Mara's own letter (was C-106's)
    make_letter('letter_heap.png', 'C-114', 311, (70, 110, 70), 'tree', 12, back='drawing', pictogram='heart')
    make_letter('letter_c110.png', 'C-110', 310, (130, 96, 50), 'arch', 13, pictogram='house')


# --------------------------------------------------------------------------
# The hall's notices
# --------------------------------------------------------------------------

def make_ring_c_notice():
    """Ring C deliveries suspended: the ring letter, a water drop, the date, a crossed-out envelope."""
    from PIL import Image, ImageDraw
    w, h = 320, 448
    img = Image.new('RGB', (w, h), (214, 204, 176))
    d = ImageDraw.Draw(img)
    navy, amber = (30, 44, 70), (196, 150, 50)
    d.rectangle((8, 8, w - 9, h - 9), outline=navy, width=6)
    d.rectangle((8, 8, w - 9, 96), fill=navy)
    d.regular_polygon((59, 53, 38), 6, rotation=30, outline=CREAM, width=6)   # the ring plate, as on the ring signs
    d.text((59, 54), 'C', font=_font(44), fill=CREAM, anchor='mm')
    d.text((200, 54), 'P.A. 310', font=_font(34), fill=CREAM, anchor='mm')
    # The water drop.
    cx, cy = w / 2, 186
    d.polygon([(cx, cy - 66), (cx - 44, cy + 6), (cx + 44, cy + 6)], fill=navy)
    d.ellipse((cx - 47, cy - 30, cx + 47, cy + 62), fill=navy)
    d.arc((cx - 28, cy - 4, cx + 10, cy + 40), 100, 190, fill=(140, 170, 200), width=6)
    for k in range(3):                                # waves under it
        y = 284 + k * 16
        d.line([(40 + t, y + 5 * math.sin(t * 0.09)) for t in range(0, 241, 6)], fill=navy, width=5)
    # The envelope, crossed out.
    ex0, ey0, ex1, ey1 = 92, 340, 228, 420
    d.rectangle((ex0, ey0, ex1, ey1), outline=navy, width=6)
    d.line((ex0, ey0, (ex0 + ex1) / 2, 384, ex1, ey0), fill=navy, width=5)
    d.line((ex0 - 18, ey1 + 10, ex1 + 18, ey0 - 12), fill=amber, width=10)
    d.line((ex0 - 18, ey0 - 12, ex1 + 18, ey1 + 10), fill=amber, width=10)
    img = _age(img, 21, 0.7)
    _save(img, 'ringc_notice.png', 32)


def make_courier_board():
    """Courier of the year: six photographs of couriers (each one a D-unit with its number and a
    rosette), P.A. 305 to 41, and a sixth frame for P.A. 310 left pale, only a silhouette."""
    from PIL import Image, ImageDraw
    w, h = 704, 448
    rnd = random.Random(31)
    img = Image.new('RGB', (w, h), (54, 40, 28))
    d = ImageDraw.Draw(img)
    gold = (196, 160, 82)
    d.rectangle((6, 6, w - 7, h - 7), outline=gold, width=6)
    # The header: a rosette and a star, no words.
    d.ellipse((w / 2 - 30, 16, w / 2 + 30, 76), fill=gold)
    pts = []
    for k in range(10):
        a = -math.pi / 2 + math.pi * k / 5
        r = 22 if k % 2 == 0 else 9
        pts.append((w / 2 + r * math.cos(a), 46 + r * math.sin(a)))
    d.polygon(pts, fill=(54, 40, 28))
    d.polygon([(w / 2 - 22, 70), (w / 2 - 34, 100), (w / 2 - 8, 86)], fill=gold)
    d.polygon([(w / 2 + 22, 70), (w / 2 + 34, 100), (w / 2 + 8, 86)], fill=gold)
    units = ['D-04', 'D-11', 'D-02', 'D-09', 'D-17']
    for i in range(6):
        col, row = i % 3, i // 3
        x0, y0 = 40 + col * 222, 116 + row * 166
        pale = i == 5
        mount = (226, 218, 196)
        d.rectangle((x0, y0, x0 + 180, y0 + 132), fill=mount)
        photo = (196, 190, 172) if pale else (rnd.randint(88, 110), rnd.randint(84, 100), rnd.randint(70, 84))
        d.rectangle((x0 + 10, y0 + 10, x0 + 170, y0 + 104), fill=photo)
        figure = (210, 204, 186) if pale else (34, 32, 30)
        cx, base = x0 + 90, y0 + 100
        if not pale:                                  # someone's hand on its shoulder: the staff were proud of them
            skin = (150, 118, 92)
            d.line((x0 + 170, y0 + 30, cx + 40, base - 70), fill=skin, width=14)
            d.ellipse((cx + 24, base - 82, cx + 48, base - 62), fill=skin)
        # A D-unit: legs, a pod, a flat head, antennae; the rosette on its chest.
        d.rectangle((cx - 16, base - 22, cx - 10, base), fill=figure)
        d.rectangle((cx + 10, base - 22, cx + 16, base), fill=figure)
        d.rounded_rectangle((cx - 28, base - 54, cx + 28, base - 20), radius=8, fill=figure)
        d.rounded_rectangle((cx - 32, base - 76, cx + 32, base - 56), radius=6, fill=figure)
        d.line((cx + 18, base - 76, cx + 24, base - 92), fill=figure, width=3)
        if pale:
            d.rectangle((x0 + 10, y0 + 10, x0 + 170, y0 + 104), outline=(170, 164, 148), width=2)
        else:
            d.ellipse((cx - 8, base - 46, cx + 8, base - 30), fill=gold)
        if i < 5:
            d.text((x0 + 50, y0 + 118), units[i], font=_font(18, 'mono'), fill=INK, anchor='mm')
        d.text((x0 + 132, y0 + 118), f'P.A. {305 + i}', font=_font(16), fill=INK if not pale else (150, 144, 126), anchor='mm')
    img = _age(img, 32, 0.5)
    _save(img, 'courier_board.png', 40)


def make_textures(force=False):
    """Write any texture that is missing (all of them with force)."""
    jobs = {'letter_tube.png': make_letters, 'letter_heap.png': make_letters, 'letter_c110.png': make_letters,
            'ringc_notice.png': make_ring_c_notice, 'courier_board.png': make_courier_board}
    done = set()
    for name, fn in jobs.items():
        if (force or not os.path.exists(os.path.join(TEX, name))) and fn not in done:
            fn()
            done.add(fn)


if __name__ == '__main__':
    make_textures(force=True)
    for n in sorted(os.listdir(TEX)):
        print(f'{os.path.getsize(os.path.join(TEX, n)) / 1024:6.1f} KB  {n}')
