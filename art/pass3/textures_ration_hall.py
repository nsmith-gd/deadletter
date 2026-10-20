"""Painted textures for DL-05 The Ration Hall (art/pass3/build_ration_hall.py).

    python textures_ration_hall.py          # (re)writes every PNG in ./textures

Visuals carry the story; the words are only for those who read:
  ration_board.png    the chalked ration board: a painted loaf, bowl, cup and tin, each issue struck and halved
  grade_notice.png    "RELOCATION BY GRADE": four steps up to the surface, the bottom one (the labour grades) struck out
  sky_mural.png       a painted sky over the cots: sun, clouds, birds, hills, children's handprints; peeling
  crayon_drawing.png  a child's crayon drawing: a little courier carrying a parcel to a house, a sun, a crooked tree, "M"
  shrine_names.png    names, photographs and a pressed flower pinned to a column (alpha)
  chalk_tally.png     tally marks in chalk, the last group unfinished (alpha)
  drum_stencil.png    the ration drum's stencil (alpha)
  ration_sign.png     the counter's fascia sign
  drum_ring.png       the rust ring a drum has left on the floor at the hatch, and its scrapes (alpha)
"""
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')

CHALK = (214, 214, 200)
PAINT = (226, 220, 196)
INK = (30, 28, 32)


def _font(size, kind='sans-bold'):
    from PIL import ImageFont
    paths = {'sans-bold': '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
             'sans': '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
             'cond': '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf',
             'mono': '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
             'serif': '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
             'hand': '/usr/share/fonts/truetype/freefont/FreeSansOblique.ttf'}
    for p in (paths.get(kind), paths['sans-bold']):
        try:
            return ImageFont.truetype(p, size)
        except (OSError, TypeError):
            continue
    return ImageFont.load_default()


def _save(img, name, colors=64):
    from PIL import Image
    os.makedirs(TEX, exist_ok=True)
    if img.mode == 'RGBA':
        img.save(os.path.join(TEX, name), optimize=True)
    else:
        q = img.convert('RGB').quantize(colors, method=Image.Quantize.MEDIANCUT)
        q.save(os.path.join(TEX, name), optimize=True)


def _grain(img, rnd, amount=10, step=3):
    """Speckle, so flat paint and paper aren't flat."""
    from PIL import ImageDraw
    d = ImageDraw.Draw(img, 'RGBA')
    w, h = img.size
    for _ in range(w * h // (step * step * 6)):
        x, y = rnd.randrange(w), rnd.randrange(h)
        c = rnd.randint(0, 255)
        d.point((x, y), fill=(c, c, c, rnd.randint(4, amount)))


def _stains(img, rnd, n=30, colour=(70, 50, 25), alpha=(5, 22), rmax=0.08):
    from PIL import ImageDraw
    d = ImageDraw.Draw(img, 'RGBA')
    w, h = img.size
    for _ in range(n):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(3, w * rmax)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(*colour, rnd.randint(*alpha)))


def _chalk_line(d, pts, rnd, width=5, colour=CHALK, passes=3, jitter=1.6, alpha=(150, 230)):
    for _ in range(passes):
        q = [(x + rnd.uniform(-jitter, jitter), y + rnd.uniform(-jitter, jitter)) for x, y in pts]
        d.line(q, fill=(*colour, rnd.randint(*alpha)), width=width, joint='curve')


def _hand_text(d, xy, text, size, rnd, fill, kind='hand', wobble=2.0, spacing=0.0):
    """Hand lettering: each glyph a little off its line and angle."""
    from PIL import Image
    f = _font(size, kind)
    x, y = xy
    for ch in text:
        if ch == ' ':
            x += size * 0.32
            continue
        bbox = f.getbbox(ch)
        gw, gh = bbox[2] + 4, bbox[3] + 6
        g = Image.new('L', (gw + 8, gh + 8), 0)
        from PIL import ImageDraw
        ImageDraw.Draw(g).text((4, 2), ch, font=f, fill=255)
        g = g.rotate(rnd.uniform(-7, 7), resample=Image.BICUBIC, expand=True)
        d._image.paste(Image.new('RGBA', g.size, fill), (int(x), int(y + rnd.uniform(-wobble, wobble))), g)
        x += bbox[2] * (0.92 + rnd.uniform(-0.05, 0.05)) + spacing


# --------------------------------------------------------------------------

def make_ration_board(path):
    """A blackboard: four painted rations down the left, the issue painted beside each, then chalked halvings
    across, each struck through for the next. The loaf row halves its own picture."""
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(505)
    w, h = 1024, 552
    img = Image.new('RGB', (w, h), (26, 32, 29))
    d = ImageDraw.Draw(img, 'RGBA')
    for _ in range(140):                                   # old chalk wiped round and round
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(20, 120)
        d.arc((x - r, y - r * 0.5, x + r, y + r * 0.5), rnd.uniform(0, 360), rnd.uniform(0, 360),
              fill=(200, 200, 190, rnd.randint(6, 18)), width=rnd.randint(6, 26))
    img = img.filter(ImageFilter.GaussianBlur(3))
    d = ImageDraw.Draw(img, 'RGBA')
    # Painted header and ruled columns (the original issue, signwritten).
    f = _font(40, 'cond')
    d.text((40, 22), 'RATION', font=f, fill=(*PAINT, 235))
    d.text((40 + f.getlength('RATION') + 18, 22), 'PER HEAD · PER DAY', font=_font(28, 'cond'), fill=(*PAINT, 200))
    d.line((30, 80, w - 30, 80), fill=(*PAINT, 180), width=4)
    for x in (200, 360):
        d.line((x, 92, x, h - 30), fill=(*PAINT, 120), width=3)
    rows = [130, 235, 340, 445]
    paint = (*PAINT, 230)

    def loaf(cx, cy, s, frac=1.0, col=paint, chalk=False):
        # A loaf in profile; frac cuts it from the right (half, quarter).
        x0, x1 = cx - 60 * s, cx - 60 * s + 120 * s * frac
        if chalk:
            pts = [(x0, cy + 22 * s)]
            n = 14
            for k in range(n + 1):
                t = k / n
                x = x0 + (cx + 60 * s - x0) * t
                if x > x1:
                    break
                pts.append((x, cy + 22 * s - 42 * s * math.sin(math.pi * t) ** 0.6))
            pts += [(x1, cy - 10 * s), (x1, cy + 22 * s), (x0, cy + 22 * s)]
            _chalk_line(d, pts, rnd, width=4)
            for k in range(3):
                sx = x0 + (k + 1) * 30 * s
                if sx < x1 - 6:
                    _chalk_line(d, [(sx - 6 * s, cy - 10 * s), (sx + 6 * s, cy - 22 * s)], rnd, width=3, passes=2)
        else:
            d.chord((cx - 60 * s, cy - 30 * s, cx + 60 * s, cy + 50 * s), 180, 360, fill=col)
            d.rectangle((cx - 60 * s, cy + 10 * s, cx + 60 * s, cy + 22 * s), fill=col)
            for k in range(3):
                sx = cx - 30 * s + k * 30 * s
                d.line((sx - 7 * s, cy - 2 * s, sx + 7 * s, cy - 18 * s), fill=(26, 32, 29, 255), width=int(5 * s))

    def bowl(cx, cy, s):
        d.chord((cx - 55 * s, cy - 40 * s, cx + 55 * s, cy + 40 * s), 0, 180, fill=paint)
        for k in range(3):
            x = cx - 22 * s + k * 22 * s
            d.arc((x - 8 * s, cy - 40 * s, x + 8 * s, cy - 8 * s), 90, 270, fill=paint, width=int(4 * s))

    def cup(cx, cy, s):
        d.polygon([(cx - 32 * s, cy - 34 * s), (cx + 32 * s, cy - 34 * s), (cx + 24 * s, cy + 30 * s), (cx - 24 * s, cy + 30 * s)], fill=paint)
        d.arc((cx + 18 * s, cy - 22 * s, cx + 52 * s, cy + 12 * s), 270, 90, fill=paint, width=int(7 * s))
        d.polygon([(cx - 26 * s, cy - 22 * s), (cx + 26 * s, cy - 22 * s), (cx + 24 * s, cy - 14 * s), (cx - 24 * s, cy - 14 * s)], fill=(26, 32, 29, 255))

    def tin(cx, cy, s):
        d.rectangle((cx - 34 * s, cy - 30 * s, cx + 34 * s, cy + 32 * s), fill=paint)
        d.ellipse((cx - 34 * s, cy - 40 * s, cx + 34 * s, cy - 20 * s), fill=paint)
        d.ellipse((cx - 28 * s, cy - 37 * s, cx + 28 * s, cy - 23 * s), outline=(26, 32, 29, 255), width=3)
        d.rectangle((cx - 34 * s, cy - 6 * s, cx + 34 * s, cy + 8 * s), fill=(26, 32, 29, 255))

    loaf(110, rows[0], 1.0)
    bowl(110, rows[1], 1.0)
    cup(110, rows[2], 1.0)
    tin(110, rows[3], 1.0)
    fnum = _font(64, 'cond')
    issue = ['4', '3', '2', '1']
    for y, t in zip(rows, issue):
        d.text((260, y - 38), t, font=fnum, fill=paint)
    # Chalked halvings, each earlier figure struck through.
    halvings = [['2', '1', '½'], ['1½', '¾', ''], ['1', '½', '¼'], ['½', '–', '']]
    cols = [430, 610, 790]
    for r, (y, seq) in enumerate(zip(rows, halvings)):
        prev_x = 260
        for c, t in enumerate(seq):
            # strike the figure before
            _chalk_line(d, [(prev_x - 12, y + 18), (prev_x + 70, y - 22)], rnd, width=6, passes=2)
            if not t:
                break
            _hand_text(d, (cols[c], y - 40), t, 58, rnd, (*CHALK, 225))
            prev_x = cols[c]
    # The loaf row draws its own halving: half a loaf, then a quarter, in chalk under the figures.
    loaf(cols[0] + 110, rows[0] + 2, 0.62, 0.5, chalk=True)
    loaf(cols[1] + 110, rows[0] + 2, 0.62, 0.25, chalk=True)
    # The last row is crossed right out, and a question mark.
    _chalk_line(d, [(420, rows[3] - 30), (700, rows[3] + 30)], rnd, width=5)
    _hand_text(d, (900, rows[0] - 40), '?', 70, rnd, (*CHALK, 220))
    # Smudges where a palm wiped a figure, and the chalk ledge's dust along the bottom.
    for _ in range(18):
        x, y = rnd.uniform(380, 980), rnd.uniform(100, 500)
        d.ellipse((x - 30, y - 12, x + 30, y + 12), fill=(200, 200, 190, rnd.randint(8, 20)))
    d.rectangle((0, h - 22, w, h), fill=(200, 200, 190, 30))
    _grain(img, rnd, 14)
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    _save(img, os.path.basename(path), 48)


def make_grade_notice(path):
    """A printed authority notice: four steps up to a sun, Grade 1 on top and Grade 4 (the labour grades:
    depot, works, ring C) at the bottom, that step struck through in brush and stamped SUSPENDED."""
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(517)
    w, h = 560, 800
    paper = (206, 196, 168)
    img = Image.new('RGB', (w, h), paper)
    d = ImageDraw.Draw(img, 'RGBA')
    _stains(img, rnd, 40)
    d = ImageDraw.Draw(img, 'RGBA')
    ink = (36, 40, 46, 255)
    d.rectangle((0, 0, w, 120), fill=ink)
    f = _font(46, 'cond')
    t = 'RELOCATION'
    d.text(((w - f.getlength(t)) / 2, 12), t, font=f, fill=paper)
    t = 'BY GRADE'
    d.text(((w - f.getlength(t)) / 2, 62), t, font=f, fill=paper)
    fs = _font(18, 'sans')
    t = 'REFUGE AUTHORITY · ORDER OF ASCENT'
    d.text(((w - fs.getlength(t)) / 2, 132), t, font=fs, fill=ink)
    # The sun at the top, an arrow up to it.
    cx = w - 110
    d.ellipse((cx - 34, 170, cx + 34, 238), outline=ink, width=6)
    for k in range(10):
        a = 2 * math.pi * k / 10
        d.line((cx + 46 * math.cos(a), 204 + 46 * math.sin(a), cx + 60 * math.cos(a), 204 + 60 * math.sin(a)), fill=ink, width=5)
    # Four steps: the widest at the bottom.
    fg = _font(30, 'cond')
    fl = _font(17, 'sans')
    labels = [('GRADE 1', 'RING A · ADMINISTRATION'), ('GRADE 2', 'RING B · SERVICES'),
              ('GRADE 3', 'TRADES · CLERKS'), ('GRADE 4', 'DEPOT · WORKS · RING C')]
    top, step_h = 270, 110
    for i, (g, sub) in enumerate(labels):
        y0 = top + i * step_h
        x0 = 40
        x1 = w - 60 - (3 - i) * 70
        shade = (90 + i * 22, 98 + i * 20, 104 + i * 16, 255)
        d.rectangle((x0, y0, x1, y0 + step_h - 14), fill=shade, outline=ink, width=3)
        d.text((x0 + 16, y0 + 12), g, font=fg, fill=paper)
        d.text((x0 + 16, y0 + 54), sub, font=fl, fill=paper)
        if i < 3:
            d.text((x1 - 64, y0 + 18), f'YR {104 + i}', font=fl, fill=paper)
    # The arrow from the top step to the sun.
    d.line((w - 160, top + 40, cx - 40, 236), fill=ink, width=7)
    d.polygon([(cx - 40, 236), (cx - 64, 238), (cx - 46, 214)], fill=ink)
    # Grade 4 struck through: two brush strokes in black, wet-edged.
    y0 = top + 3 * step_h
    for a, b in (((24, y0 - 6), (w - 30, y0 + step_h - 4)), ((24, y0 + step_h - 10), (w - 40, y0 + 4))):
        for k in range(6):
            off = rnd.uniform(-5, 5)
            d.line((a[0], a[1] + off, b[0], b[1] + off), fill=(12, 12, 14, rnd.randint(150, 230)), width=rnd.randint(8, 16))
    # A stamp at an angle across it.
    st = Image.new('RGBA', (300, 80), (0, 0, 0, 0))
    sd = ImageDraw.Draw(st)
    sd.rectangle((4, 4, 296, 76), outline=(40, 46, 92, 220), width=6)
    fst = _font(38, 'cond')
    sd.text((150 - fst.getlength('SUSPENDED') / 2, 16), 'SUSPENDED', font=fst, fill=(40, 46, 92, 220))
    st = st.rotate(14, expand=True, resample=Image.BICUBIC)
    img.paste(st, (150, top + 2 * step_h + 70), st)
    d = ImageDraw.Draw(img, 'RGBA')
    # Pencil in the margin: "when?"
    _hand_text(d, (40, h - 56), 'when?', 34, rnd, (60, 58, 66, 200))
    # Pin holes, a torn corner, damp.
    for x, y in ((14, 14), (w - 16, 14), (14, h - 16), (w - 16, h - 16)):
        d.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(50, 44, 36, 200))
    d.polygon([(w, h - 70), (w, h), (w - 60, h)], fill=(30, 30, 28, 255))
    for _ in range(8):
        x = rnd.uniform(0, w)
        d.line((x, 0, x + rnd.uniform(-10, 10), h * rnd.uniform(0.3, 1.0)), fill=(80, 60, 30, rnd.randint(8, 20)), width=rnd.randint(3, 9))
    _grain(img, rnd, 12)
    img = img.filter(ImageFilter.GaussianBlur(0.7))
    _save(img, os.path.basename(path), 48)


def make_sky_mural(path):
    """A sky painted on a canteen wall by people who had never seen one: a big sun, fat clouds, birds as
    ticks, green hills, and the children's handprints along the bottom. Faded, damp-streaked, peeling."""
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(530)
    w, h = 1536, 768
    plaster = (120, 116, 104)
    img = Image.new('RGB', (w, h), plaster)
    # The sky: a vertical gradient, painted in horizontal brushwork.
    sky = Image.new('RGB', (w, h))
    sd = ImageDraw.Draw(sky)
    for y in range(h):
        t = y / h
        c = (int(58 + 110 * t), int(92 + 92 * t), int(140 + 60 * t))
        sd.line((0, y, w, y), fill=c)
    sd = ImageDraw.Draw(sky, 'RGBA')
    for _ in range(900):
        y = rnd.uniform(0, h * 0.8)
        x = rnd.uniform(-50, w)
        t = y / h
        c = (int(58 + 110 * t) + rnd.randint(-14, 14), int(92 + 92 * t) + rnd.randint(-14, 14), int(140 + 60 * t) + rnd.randint(-10, 10))
        sd.line((x, y, x + rnd.uniform(60, 220), y + rnd.uniform(-6, 6)), fill=(*c, 70), width=rnd.randint(6, 16))
    # The sun, big and yellow, with painted rays.
    sx, sy, sr = 1180, 190, 105
    for k in range(16):
        a = 2 * math.pi * k / 16 + 0.1
        r0, r1 = sr + 22, sr + rnd.uniform(70, 110)
        sd.line((sx + r0 * math.cos(a), sy + r0 * math.sin(a), sx + r1 * math.cos(a), sy + r1 * math.sin(a)),
                fill=(236, 196, 84, 230), width=18)
    sd.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=(240, 202, 90))
    sd.ellipse((sx - sr + 16, sy - sr + 14, sx + sr - 30, sy + sr - 30), fill=(246, 214, 112))
    # A smiling face on it: a child had a brush too.
    sd.arc((sx - 42, sy - 10, sx + 42, sy + 50), 20, 160, fill=(170, 110, 40, 255), width=7)
    for ex in (-30, 30):
        sd.ellipse((sx + ex - 8, sy - 34, sx + ex + 8, sy - 18), fill=(170, 110, 40, 255))
    # Clouds: piles of white puffs, shaded underneath.
    for cx, cy, s in ((260, 170, 1.2), (640, 110, 0.9), (880, 300, 0.8), (430, 360, 0.7), (1400, 400, 0.6)):
        puffs = [(cx + rnd.uniform(-110, 110) * s, cy + rnd.uniform(-20, 20) * s, rnd.uniform(40, 75) * s) for _ in range(9)]
        for x, y, r in puffs:
            sd.ellipse((x - r, y - r + 12 * s, x + r, y + r + 12 * s), fill=(150, 168, 186, 255))
        for x, y, r in puffs:
            sd.ellipse((x - r, y - r, x + r, y + r * 0.8), fill=(232, 234, 228, 255))
    # Birds: little ticks.
    for _ in range(9):
        x, y, s = rnd.uniform(380, 1050), rnd.uniform(120, 420), rnd.uniform(12, 24)
        sd.line((x - s, y - s * 0.4, x, y, x + s, y - s * 0.5), fill=(40, 44, 54, 230), width=5, joint='curve')
    # Hills, a fence of flowers and the handprints.
    for k, (base, col) in enumerate(((560, (94, 132, 78)), (610, (72, 112, 62)), (660, (58, 96, 52)))):
        pts = [(0, h)]
        for x in range(0, w + 40, 40):
            pts.append((x, base + 40 * math.sin(x / (210 + 60 * k) + k * 1.7) + 18 * math.sin(x / 70 + k)))
        pts.append((w, h))
        sd.polygon(pts, fill=col)
    for _ in range(60):
        x, y = rnd.uniform(20, w - 20), rnd.uniform(640, 740)
        c = rnd.choice([(230, 220, 120), (230, 230, 220), (200, 130, 170), (240, 170, 80)])
        sd.line((x, y + 16, x, y), fill=(50, 90, 46, 255), width=3)
        sd.ellipse((x - 7, y - 7, x + 7, y + 7), fill=c)
    hand_cols = [(232, 196, 70), (226, 136, 60), (90, 140, 200), (210, 110, 150), (240, 236, 224), (120, 190, 120)]
    for k in range(13):
        x, y = 70 + k * 110 + rnd.uniform(-20, 20), 690 + rnd.uniform(-30, 20)
        s = rnd.uniform(0.7, 1.05)
        c = (*rnd.choice(hand_cols), 235)
        rot = rnd.uniform(-0.4, 0.4)
        sd.ellipse((x - 22 * s, y - 20 * s, x + 22 * s, y + 26 * s), fill=c)
        for j, (a, L) in enumerate(((-1.0, 30), (-0.45, 42), (-0.12, 46), (0.22, 42), (0.62, 34))):
            aa = a + rot - math.pi / 2
            if j == 0:
                aa = -2.4 + rot
            fx, fy = x + (18 + L * 0.5) * s * math.cos(aa), y + (18 + L * 0.5) * s * math.sin(aa)
            sd.line((x + 14 * s * math.cos(aa), y + 14 * s * math.sin(aa), fx + L * 0.4 * s * math.cos(aa), fy + L * 0.4 * s * math.sin(aa)),
                    fill=c, width=int(13 * s))
    sky = sky.filter(ImageFilter.GaussianBlur(1.2))
    # The mural's ragged painted edge on the plaster.
    mask = Image.new('L', (w, h), 0)
    md = ImageDraw.Draw(mask)
    md.rectangle((26, 22, w - 26, h - 20), fill=255)
    for _ in range(120):
        side = rnd.randrange(4)
        if side == 0:
            x, y = rnd.uniform(0, w), rnd.uniform(0, 40)
        elif side == 1:
            x, y = rnd.uniform(0, w), rnd.uniform(h - 36, h)
        elif side == 2:
            x, y = rnd.uniform(0, 42), rnd.uniform(0, h)
        else:
            x, y = rnd.uniform(w - 42, w), rnd.uniform(0, h)
        r = rnd.uniform(6, 26)
        md.ellipse((x - r, y - r, x + r, y + r), fill=rnd.choice((0, 255)))
    # Peeling: patches where the paint has come away, with a darker lip.
    peel = ImageDraw.Draw(mask)
    lips = []
    for _ in range(26):
        x, y = rnd.uniform(40, w - 40), rnd.uniform(40, h - 40)
        pts = []
        R = rnd.uniform(14, 60)
        for k in range(14):
            a = 2 * math.pi * k / 14
            rr = R * rnd.uniform(0.55, 1.25)
            pts.append((x + rr * math.cos(a), y + rr * 0.7 * math.sin(a)))
        peel.polygon(pts, fill=0)
        lips.append(pts)
    mask = mask.filter(ImageFilter.GaussianBlur(1.2))
    img.paste(sky, (0, 0), mask)
    d = ImageDraw.Draw(img, 'RGBA')
    for pts in lips:
        d.line(pts + [pts[0]], fill=(60, 56, 48, 120), width=3)
    # Fading: a wash of grime over everything, damp streaks from the top, a crack.
    d.rectangle((0, 0, w, h), fill=(84, 80, 70, 96))
    for _ in range(40):
        x = rnd.uniform(0, w)
        d.line((x, 0, x + rnd.uniform(-8, 8), rnd.uniform(80, 520)), fill=(60, 54, 40, rnd.randint(12, 38)), width=rnd.randint(4, 18))
    crack = [(rnd.uniform(300, 500), 0)]
    for _ in range(14):
        px, py = crack[-1]
        crack.append((px + rnd.uniform(-30, 40), py + rnd.uniform(30, 60)))
    d.line(crack, fill=(40, 38, 32, 200), width=3)
    _stains(img, rnd, 30, (50, 44, 34), (8, 26), 0.06)
    _grain(img, rnd, 12)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    _save(img, os.path.basename(path), 96)


def make_crayon_drawing(path):
    """Wax crayon on a sheet of ration paper: a little courier, box body, flat head, three antenna stalks,
    carrying a parcel along a dotted path to a house with a lit window; a sun; a crooked tree; a big "M"."""
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(541)
    w, h = 640, 480
    img = Image.new('RGB', (w, h), (222, 214, 190))
    _stains(img, rnd, 18, (120, 100, 60), (6, 16), 0.1)
    d = ImageDraw.Draw(img, 'RGBA')
    # A fold, opened out.
    d.line((w * 0.5, 0, w * 0.5 + 4, h), fill=(150, 140, 110, 60), width=3)
    d.line((0, h * 0.5, w, h * 0.5 - 3), fill=(150, 140, 110, 50), width=2)

    def crayon(pts, colour, width=7, passes=4, jitter=2.2):
        for _ in range(passes):
            q = [(x + rnd.uniform(-jitter, jitter), y + rnd.uniform(-jitter, jitter)) for x, y in pts]
            d.line(q, fill=(*colour, rnd.randint(150, 230)), width=width, joint='curve')

    def fill_scribble(box, colour, step=7, width=6):
        x0, y0, x1, y1 = box
        y = y0
        while y < y1:
            crayon([(x0, y), (x1, y + rnd.uniform(-3, 3))], colour, width, 1, 1.5)
            y += step

    def circle(cx, cy, r, colour, width=7, n=30):
        crayon([(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n)) for k in range(n + 1)], colour, width)

    yellow, orange, blue, green, brown, purple, dark = (236, 190, 40), (226, 128, 40), (52, 86, 170), (70, 146, 70), (122, 82, 50), (120, 70, 150), (60, 50, 50)
    # Sun, top left, with rays.
    circle(92, 82, 40, orange)
    fill_scribble((64, 56, 122, 108), yellow, 6, 7)
    for k in range(11):
        a = 2 * math.pi * k / 11
        crayon([(92 + 52 * math.cos(a), 82 + 52 * math.sin(a)), (92 + 76 * math.cos(a), 82 + 76 * math.sin(a))], orange, 6, 2)
    # Ground.
    crayon([(10, 400), (200, 396), (420, 404), (630, 398)], green, 10)
    for x in range(20, 620, 22):
        crayon([(x, 402), (x + 4, 384)], green, 4, 1)
    # The crooked tree, left of middle.
    crayon([(196, 398), (204, 340), (190, 300), (214, 250), (206, 214)], brown, 12)
    crayon([(204, 300), (236, 276)], brown, 7)
    for cx, cy, r in ((206, 200, 44), (176, 220, 30), (240, 214, 34), (214, 168, 30)):
        circle(cx, cy, r, green, 7, 22)
    fill_scribble((170, 170, 250, 236), green, 9, 6)
    # The house on the right: walls, roof, door, a lit window with someone in it.
    crayon([(440, 398), (440, 268), (590, 268), (590, 398)], brown, 8)
    crayon([(426, 274), (515, 196), (604, 274)], orange, 9)
    fill_scribble((470, 218, 560, 262), orange, 8, 6)
    crayon([(500, 398), (500, 336), (536, 336), (536, 398)], brown, 7)
    crayon([(458, 292), (494, 292), (494, 324), (458, 324), (458, 292)], blue, 6)
    fill_scribble((462, 296, 490, 320), yellow, 5, 5)
    circle(476, 306, 6, purple, 4, 12)
    # The dotted path from the courier to the door.
    for k in range(9):
        x = 330 + k * 19
        crayon([(x, 392 - k * 0.5), (x + 7, 392 - k * 0.5)], dark, 5, 2)
    # The little courier: box body, flat head with two eyes, three antenna stalks, two legs, both arms
    # out holding a parcel tied with string.
    bx, by = 252, 300
    crayon([(bx, by), (bx + 58, by), (bx + 58, by + 50), (bx, by + 50), (bx, by)], blue, 7)
    crayon([(bx - 6, by - 6), (bx + 64, by - 6), (bx + 58, by - 36), (bx, by - 36), (bx - 6, by - 6)], blue, 7)
    circle(bx + 18, by - 21, 5, dark, 4, 10)
    circle(bx + 42, by - 21, 5, dark, 4, 10)
    for k in range(3):
        crayon([(bx + 34 + k * 6, by - 36), (bx + 38 + k * 9, by - 62 - k * 5)], blue, 4, 2)
        circle(bx + 38 + k * 9, by - 66 - k * 5, 4, orange, 3, 8)
    crayon([(bx + 14, by + 50), (bx + 10, by + 94)], blue, 7)
    crayon([(bx + 44, by + 50), (bx + 50, by + 94)], blue, 7)
    crayon([(bx + 58, by + 18), (bx + 86, by + 24)], blue, 6)
    crayon([(bx + 86, by + 4), (bx + 124, by + 4), (bx + 124, by + 40), (bx + 86, by + 40), (bx + 86, by + 4)], brown, 6)
    fill_scribble((bx + 90, by + 8, bx + 120, by + 36), (196, 150, 90), 6, 5)
    crayon([(bx + 105, by + 4), (bx + 105, by + 40)], dark, 3, 2)
    crayon([(bx + 86, by + 22), (bx + 124, by + 22)], dark, 3, 2)
    # Motion ticks behind him: he's on his way.
    for k in range(3):
        crayon([(bx - 24, by + 8 + k * 16), (bx - 10, by + 8 + k * 16)], dark, 4, 2)
    # A heart in the sky, and the signature: a big M.
    hx, hy = 360, 120
    crayon([(hx, hy + 22), (hx - 18, hy + 4), (hx - 12, hy - 8), (hx, hy), (hx + 12, hy - 8), (hx + 18, hy + 4), (hx, hy + 22)], (210, 90, 120), 6)
    crayon([(560, 456), (568, 420), (582, 446), (596, 420), (604, 456)], purple, 7)
    # Tape at the two top corners.
    for cx, ang in ((40, -0.5), (w - 40, 0.5)):
        tape = Image.new('RGBA', (120, 44), (226, 220, 170, 120))
        td = ImageDraw.Draw(tape)
        for k in range(0, 120, 6):
            td.line((k, 0, k + 3, 3), fill=(0, 0, 0, 0), width=2)
        tape = tape.rotate(math.degrees(ang), expand=True, resample=Image.BICUBIC)
        img.paste(tape, (int(cx - tape.width / 2), -6), tape)
    _grain(img, rnd, 16, 2)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    _save(img, os.path.basename(path), 64)


def make_shrine_names(path):
    """Scraps pinned to a column: names in many hands, three photographs, a pressed flower, a ribbon."""
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(552)
    w, h = 640, 1024
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    names = ['ADA VOSS', 'Piotr - pumps', 'LENA K.', 'old Tomas', 'the Hale family', 'R. OKAFOR', 'Ines, 7',
             'Grandad Ben', 'MIRA & JON', 'Edda', 'S. Brandt', 'little Pim', 'Wen (ring C)', 'Our Davey']
    inks = [(30, 30, 40), (40, 40, 90), (60, 30, 30), (20, 50, 40), (70, 60, 50)]
    papers = [(214, 206, 180), (196, 204, 210), (220, 214, 196), (204, 190, 160), (230, 226, 210), (190, 196, 176)]
    slots = []
    for k, n in enumerate(names):
        pw, ph = rnd.randint(200, 300), rnd.randint(70, 110)
        x = rnd.uniform(10, w - pw - 10)
        y = 40 + k * 66 + rnd.uniform(-10, 10)
        slots.append((n, pw, ph, x, y))
    photos = [(70, 200), (380, 470), (120, 760)]
    items = [('name', s) for s in slots]
    for k, p in enumerate(photos):
        items.insert(3 + k * 4, ('photo', p))
    for kind, s in items:
        if kind == 'name':
            n, pw, ph, x, y = s
            card = Image.new('RGBA', (pw, ph), (*rnd.choice(papers), 255))
            cd = ImageDraw.Draw(card, 'RGBA')
            if rnd.random() < 0.4:                      # torn from an exercise book
                for ly in range(14, ph, 18):
                    cd.line((0, ly, pw, ly), fill=(110, 140, 170, 90), width=1)
            fsz = rnd.randint(30, 40)
            kind_f = rnd.choice(['hand', 'hand', 'sans-bold', 'serif'])
            f = _font(fsz, kind_f)
            tw = f.getlength(n)
            if tw > pw - 16:
                fsz = int(fsz * (pw - 16) / tw)
            _hand_text(cd, (10, (ph - fsz) / 2 - 4), n, fsz, rnd, (*rnd.choice(inks), 235), kind=kind_f, wobble=1.5)
            cd.ellipse((pw / 2 - 5, 3, pw / 2 + 5, 13), fill=(140, 130, 110, 255))           # the pin
            card = card.rotate(rnd.uniform(-9, 9), expand=True, resample=Image.BICUBIC)
            img.alpha_composite(card, (int(x), int(y)))
        else:
            x, y = s
            pw, ph = 150, 190
            ph_img = Image.new('RGBA', (pw, ph), (226, 222, 210, 255))
            pd = ImageDraw.Draw(ph_img)
            tone = (rnd.randint(90, 120), rnd.randint(84, 104), rnd.randint(70, 90))
            pd.rectangle((10, 10, pw - 10, ph - 34), fill=tone)
            for k in range(rnd.randint(1, 3)):          # head-and-shoulders, one to three people
                cx = pw / 2 + (k - 0.5 * (rnd.randint(1, 3) - 1)) * 34
                pd.ellipse((cx - 16, 44, cx + 16, 80), fill=(52, 46, 40))
                pd.chord((cx - 34, 82, cx + 34, 170), 180, 360, fill=(52, 46, 40))
            pd.rectangle((10, 10, pw - 10, ph - 34), outline=(150, 140, 120), width=2)
            ph_img = ph_img.filter(ImageFilter.GaussianBlur(0.8))
            ph_img = ph_img.rotate(rnd.uniform(-12, 12), expand=True, resample=Image.BICUBIC)
            img.alpha_composite(ph_img, (int(x), int(y)))
    d = ImageDraw.Draw(img, 'RGBA')
    # A pressed flower and a ribbon across the top.
    fx, fy = 470, 120
    d.line((fx, fy, fx - 30, fy + 130), fill=(80, 100, 60, 255), width=4)
    for k in range(6):
        a = 2 * math.pi * k / 6
        d.ellipse((fx + 22 * math.cos(a) - 14, fy + 22 * math.sin(a) - 14, fx + 22 * math.cos(a) + 14, fy + 22 * math.sin(a) + 14),
                  fill=(206, 180, 120, 255))
    d.ellipse((fx - 9, fy - 9, fx + 9, fy + 9), fill=(150, 110, 50, 255))
    d.line((0, 30, w * 0.4, 50, w, 24), fill=(70, 80, 120, 255), width=10, joint='curve')
    # Candle soot darkening the bottom of the scraps (only where there is paper).
    soot = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(soot)
    for _ in range(26):
        x, y, r = rnd.uniform(60, w - 60), rnd.uniform(h - 300, h), rnd.uniform(40, 90)
        sd.ellipse((x - r, y - r, x + r, y + r), fill=(24, 20, 16, rnd.randint(30, 70)))
    soot = soot.filter(ImageFilter.GaussianBlur(20))
    a = img.getchannel('A')
    from PIL import ImageChops
    soot.putalpha(ImageChops.multiply(soot.getchannel('A'), a))
    img.alpha_composite(soot)
    _save(img, os.path.basename(path))


def make_chalk_tally(path):
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(563)
    w, h = 512, 768
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, 'RGBA')
    groups = 37
    x, y = 30, 30
    for g in range(groups):
        n = 5 if g < groups - 1 else 3
        for k in range(min(n, 4)):
            _chalk_line(d, [(x + k * 14, y), (x + k * 14 + rnd.uniform(-3, 3), y + 58)], rnd, width=5, passes=2, alpha=(140, 220))
        if n == 5:
            _chalk_line(d, [(x - 8, y + 44), (x + 54, y + 10)], rnd, width=5, passes=2, alpha=(140, 220))
        x += 86
        if x > w - 80:
            x, y = 30 + rnd.uniform(-6, 6), y + 88
    img = img.filter(ImageFilter.GaussianBlur(0.9))
    _save(img, os.path.basename(path))


def make_drum_stencil(path):
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(574)
    w, h = 512, 192
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, 'RGBA')
    f = _font(76, 'cond')
    t = 'RATIONS'
    d.text(((w - f.getlength(t)) / 2, 10), t, font=f, fill=(206, 196, 150, 230))
    fs = _font(34, 'cond')
    t = 'GR.4  ·  25 KG  ·  LOT 117'
    d.text(((w - fs.getlength(t)) / 2, 112), t, font=fs, fill=(206, 196, 150, 210))
    # Stencil bridges and wear: knock holes in the paint.
    px = img.load()
    for _ in range(500):
        x, y = rnd.randrange(w), rnd.randrange(h)
        r = rnd.randint(1, 5)
        for yy in range(max(0, y - r), min(h, y + r)):
            for xx in range(max(0, x - r), min(w, x + r)):
                if px[xx, yy][3]:
                    px[xx, yy] = (0, 0, 0, 0)
    img = img.filter(ImageFilter.GaussianBlur(0.7))
    _save(img, os.path.basename(path))


def make_ration_sign(path):
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(585)
    w, h = 1024, 128
    img = Image.new('RGB', (w, h), (30, 46, 38))
    d = ImageDraw.Draw(img, 'RGBA')
    f = _font(78, 'cond')
    t = 'RATION  ISSUE'
    d.text(((w - f.getlength(t)) / 2, 14), t, font=f, fill=(196, 184, 140, 230))
    # A loaf and a bowl either side.
    for cx in (110, w - 110):
        d.chord((cx - 50, 30, cx + 50, 110), 180, 360, fill=(196, 184, 140, 220))
        d.rectangle((cx - 50, 70, cx + 50, 80), fill=(196, 184, 140, 220))
    for _ in range(120):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(2, 9)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(24, 30, 26, rnd.randint(60, 160)))
    _grain(img, rnd, 18)
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    _save(img, os.path.basename(path), 32)


def make_drum_ring(path):
    """Seen from above: the rust ring of a drum that stood here a long time, and the scrapes of the ones dragged in."""
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(596)
    s = 512
    img = Image.new('RGBA', (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, 'RGBA')
    c = s / 2
    for k in range(5):
        r = 200 + rnd.uniform(-6, 6)
        d.ellipse((c - r, c - r, c + r, c + r), outline=(70, 36, 16, rnd.randint(40, 90)), width=rnd.randint(8, 20))
    for _ in range(40):
        a = rnd.uniform(0, 2 * math.pi)
        r = 200 + rnd.uniform(-8, 8)
        x, y = c + r * math.cos(a), c + r * math.sin(a)
        d.ellipse((x - 10, y - 10, x + 10, y + 10), fill=(90, 44, 18, rnd.randint(30, 80)))
    img = img.filter(ImageFilter.GaussianBlur(3))
    _save(img, os.path.basename(path))


# --------------------------------------------------------------------------
# Pass 4 (docs/chapter1_pass4_plan.md): the weigh-in, the famine, the remains
# --------------------------------------------------------------------------

# The remains atlas: one small painted palette shared by every figure and shroud (DL-02's sorters, DL-05's dead), so
# each figure is one mesh with one material. Cells in pixels (x0, y0, x1, y1) of a 512 x 512 image.
ATLAS_CELLS = {
    'sheet': (0, 0, 256, 256),          # the shroud linen: grey, stained, creased
    'bone': (256, 0, 384, 128),         # dry bone, dark
    'cloth': (384, 0, 512, 128),        # shirts and trousers, near black
    'apron': (256, 128, 384, 256),      # sorters' aprons: faded canvas, a value lighter than the clothes
    'shoe': (384, 128, 512, 256),       # boots
    'tag': (0, 256, 128, 384),          # the ration tag: buff card, a grade and a number
    'rope': (128, 256, 256, 384),       # hemp
    'bag': (256, 256, 384, 384),        # mailbag canvas
    'dark': (384, 256, 512, 384),       # hair, shadows
    'cap': (0, 384, 128, 512),          # a depot cap's cloth
    'wood': (128, 384, 256, 512),       # the drag toggle
    # Pass 5 (76 years dead): the letters under the sorters' hands, and the rotted shirts' rags.
    'paper': (256, 384, 384, 512),      # envelopes, yellowed
    'rag': (384, 384, 512, 512),        # a shirt rotted to rags: dark, frayed, mould-bloomed
}


def atlas_uv(cell):
    """UV rectangle (u0, v0, u1, v1) of a cell (Blender's v runs up the image)."""
    x0, y0, x1, y1 = ATLAS_CELLS[cell]
    return x0 / 512, 1 - y1 / 512, x1 / 512, 1 - y0 / 512


def make_remains_atlas(path):
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(4401)
    img = Image.new('RGB', (512, 512), (40, 38, 34))
    d = ImageDraw.Draw(img, 'RGBA')

    def fill(cell, base, blot, n=40, rmax=0.25, speck=40, streaks=0):
        x0, y0, x1, y1 = ATLAS_CELLS[cell]
        w, h = x1 - x0, y1 - y0
        d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=base)
        for _ in range(n):
            x, y, r = rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(3, w * rmax)
            c = tuple(max(0, min(255, b + rnd.randint(-blot, blot))) for b in base)
            d.ellipse((max(x0, x - r), max(y0, y - r * 0.7), min(x1 - 1, x + r), min(y1 - 1, y + r * 0.7)), fill=(*c, rnd.randint(14, 44)))
        for _ in range(streaks):
            x = rnd.uniform(x0, x1)
            d.line((x, y0, x + rnd.uniform(-6, 6), y1 - 1), fill=(0, 0, 0, rnd.randint(14, 34)), width=rnd.randint(1, 4))
        for _ in range(w * h // speck):
            x, y = rnd.randrange(x0, x1), rnd.randrange(y0, y1)
            c = rnd.randint(0, 255)
            d.point((x, y), fill=(c, c, c, rnd.randint(8, 30)))
    # The sheet (pass 5: 76 years on the floor): linen gone the colour of dust, yellowed where it lay on the dead,
    # grey bloom of dust on the tops, long creases; damp tide-marks, never blood.
    fill('sheet', (104, 99, 86), 18, n=110, rmax=0.18, speck=8)
    x0, y0, x1, y1 = ATLAS_CELLS['sheet']
    for _ in range(26):                                    # creases
        y = rnd.uniform(y0, y1)
        d.line([(x0 + t, y + 6 * math.sin(t * 0.04 + y)) for t in range(0, x1 - x0, 8)], fill=(56, 52, 44, rnd.randint(50, 110)), width=rnd.randint(2, 4))
    for _ in range(12):                                    # tide-marks: dust and damp
        x, y, r = rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(8, 34)
        d.ellipse((x - r, y - r * 0.6, x + r, y + r * 0.6), outline=(84, 72, 52, rnd.randint(60, 110)), width=2,
                  fill=(92, 80, 58, rnd.randint(30, 70)))
    for _ in range(1400):                                  # the dust: a pale grey bloom, finer than the weave
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        r = rnd.uniform(0.6, 2.2)
        c = rnd.randint(128, 150)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(c, c - 3, c - 10, rnd.randint(30, 80)))
    # Bone, 76 years dry: dark ivory, stained brown in its hollows, dust-grey on top. Lighter than everything it lies
    # among, so a skull and a rib cage read at once in the dark.
    fill('bone', (162, 148, 118), 16, n=34, speck=8, streaks=8)
    x0, y0, x1, y1 = ATLAS_CELLS['bone']
    for _ in range(14):
        x, y, r = rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(4, 16)
        d.ellipse((x - r, y - r * 0.5, x + r, y + r * 0.5), fill=(110, 92, 64, rnd.randint(30, 70)))
    for _ in range(300):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        d.point((x, y), fill=(196, 188, 166, rnd.randint(60, 140)))
    fill('cloth', (64, 61, 55), 10, n=40, speck=14, streaks=6)
    fill('apron', (116, 104, 82), 14, n=40, speck=12, streaks=4)
    x0, y0, x1, y1 = ATLAS_CELLS['apron']
    for _ in range(18):                                    # mould and rot in the canvas
        x, y, r = rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(3, 12)
        d.ellipse((x - r, y - r * 0.7, x + r, y + r * 0.7), fill=(58, 52, 40, rnd.randint(50, 120)))
    fill('shoe', (40, 35, 31), 6, n=20, speck=20)
    fill('rope', (104, 88, 60), 10, n=10, speck=8, streaks=30)
    fill('bag', (86, 92, 76), 10, n=30, speck=12, streaks=8)
    fill('dark', (20, 17, 15), 3, n=10, speck=60)          # the eye sockets, the nose, the mouth: hollows
    fill('cap', (30, 40, 34), 6, n=20, speck=20)
    fill('wood', (70, 52, 34), 10, n=10, speck=10, streaks=24)
    fill('paper', (150, 138, 108), 12, n=30, speck=10)
    x0, y0, x1, y1 = ATLAS_CELLS['paper']
    for k in range(5):                                     # an address, in ink gone brown
        yy = y0 + 40 + k * 14
        d.line((x0 + 30, yy, x0 + 30 + rnd.randint(30, 70), yy), fill=(70, 58, 44, 140), width=2)
    fill('rag', (52, 49, 44), 10, n=30, speck=10, streaks=40)
    x0, y0, x1, y1 = ATLAS_CELLS['rag']
    for _ in range(40):                                    # frayed threads and mould bloom
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        d.line((x, y, x + rnd.uniform(-3, 3), y + rnd.uniform(6, 22)), fill=(84, 80, 70, rnd.randint(40, 100)), width=1)
    # The ration tag: buff card, a reinforced eyelet at its top, the grade and a number.
    x0, y0, x1, y1 = ATLAS_CELLS['tag']
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(176, 158, 116))
    d.ellipse((x0 + 54, y0 + 6, x0 + 74, y0 + 26), outline=(120, 100, 66), width=4)
    d.text((x0 + 20, y0 + 34), 'GR 4', font=_font(30, 'sans-bold'), fill=(40, 34, 30))
    d.text((x0 + 18, y0 + 74), 'R. %d' % rnd.randint(1000, 9999), font=_font(24, 'mono'), fill=(54, 46, 40))
    d.line((x0 + 10, y0 + 108, x1 - 12, y0 + 108), fill=(54, 46, 40), width=2)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    _save(img, os.path.basename(path), 96)


# The weigh-in atlas (1024 x 512): the dial's face (left half), the post's sign and the SERVED flag (right half).
WEIGH_CELLS = {
    'dial': (0, 0, 512, 512),
    'sign': (512, 0, 1024, 256),
    'served': (512, 256, 1024, 384),
    'flagback': (512, 384, 1024, 448),
    'enamel': (512, 448, 1024, 512),    # plain cream enamel, for the dial's rim
}
DIAL_SWEEP = 240.0                       # degrees, clockwise from zero (at -120 from straight up) to the stop
DIAL_BANDS = ((0.0, 110.0, 'UNDER'), (110.0, 170.0, 'PERSON'), (170.0, 240.0, 'OVER'))


def weigh_uv(cell):
    x0, y0, x1, y1 = WEIGH_CELLS[cell]
    return x0 / 1024, 1 - y1 / 512, x1 / 1024, 1 - y0 / 512


def make_weighin(path):
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(4402)
    img = Image.new('RGB', (1024, 512), (30, 34, 30))
    d = ImageDraw.Draw(img, 'RGBA')
    cream, ink = (206, 196, 164), (26, 24, 22)
    amber, black = (196, 132, 34), (24, 22, 20)
    # The dial: cream enamel, the bands round an arc of 240 degrees, zero at lower left.
    c, R = 256, 244
    d.ellipse((c - R, c - R, c + R, c + R), fill=cream, outline=ink, width=10)

    def at(sweep, r):
        a = math.radians(-120 + sweep)                     # clockwise from straight up
        return c + r * math.sin(a), c - r * math.cos(a)

    def band(s0, s1, r0, r1, colour):
        pts = [at(s0 + (s1 - s0) * k / 40, r1) for k in range(41)] + [at(s1 - (s1 - s0) * k / 40, r0) for k in range(41)]
        d.polygon(pts, fill=colour)
    r0, r1 = 150, 222
    # UNDER: amber hatching on the cream.
    band(0, 110, r0, r1, (226, 210, 168))
    for k in range(0, 110, 6):
        a, b = at(k, r0), at(k + 7, r1)
        d.line((a, b), fill=amber, width=7)
    # PERSON: clean, with a little standing figure in it.
    band(110, 170, r0, r1, (232, 226, 204))
    # OVER: amber and black stripes.
    band(170, 240, r0, r1, black)
    for k in range(170, 240, 8):
        pts = [at(k, r0), at(k + 4, r0), at(k + 7, r1), at(k + 3, r1)]
        d.polygon(pts, fill=amber)
    for s in (0, 110, 170, 240):                            # band edges
        d.line((at(s, r0 - 6), at(s, r1 + 6)), fill=ink, width=6)
    d.arc((c - r1, c - r1, c + r1, c + r1), -210, 30, fill=ink, width=4)
    d.arc((c - r0, c - r0, c + r0, c + r0), -210, 30, fill=ink, width=4)
    for k in range(0, 241, 10):                             # ticks
        d.line((at(k, r0 - 4), at(k, r0 - (22 if k % 30 == 0 else 12))), fill=ink, width=5 if k % 30 == 0 else 3)
    # The person pictogram, in the PERSON band: head, body, arms, legs.
    px, py = at(140, (r0 + r1) / 2)
    d.ellipse((px - 9, py - 30, px + 9, py - 12), fill=ink)
    d.line((px, py - 12, px, py + 12), fill=ink, width=8)
    d.line((px - 14, py - 4, px + 14, py - 4), fill=ink, width=6)
    d.line((px, py + 10, px - 9, py + 32), fill=ink, width=6)
    d.line((px, py + 10, px + 9, py + 32), fill=ink, width=6)
    # Labels inside the arc.
    for s0, s1, name in DIAL_BANDS:
        f = _font(34 if name != 'PERSON' else 30, 'sans-bold')
        x, y = at((s0 + s1) / 2, 112)
        tw = f.getlength(name)
        d.text((x - tw / 2, y - 18), name, font=f, fill=ink)
    f = _font(46, 'sans-bold')
    t = 'WEIGH-IN'
    d.text((c - f.getlength(t) / 2, c + 92), t, font=f, fill=ink)
    f = _font(22, 'sans-bold')
    t = 'ONE RATION PER HEAD'
    d.text((c - f.getlength(t) / 2, c + 148), t, font=f, fill=ink)
    d.ellipse((c - 26, c - 26, c + 26, c + 26), fill=(60, 58, 52))   # the hub's shadow
    for _ in range(60):                                     # chips in the enamel, rust at the rim
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.choice((rnd.uniform(228, 240), rnd.uniform(0, 236)))
        x, y, rr = c + r * math.cos(a), c + r * math.sin(a), rnd.uniform(2, 7)
        d.ellipse((x - rr, y - rr, x + rr, y + rr), fill=(70, 46, 26, rnd.randint(90, 200)))
    _stains(img, rnd, 18, (90, 70, 40), (6, 20), 0.1)
    # The post's sign: WEIGH-IN / ONE RATION PER HEAD, signwritten on enamel.
    x0, y0, x1, y1 = WEIGH_CELLS['sign']
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=cream)
    d.rectangle((x0 + 10, y0 + 10, x1 - 11, y1 - 11), outline=ink, width=8)
    def fit(t, size, width):
        f = _font(size, 'sans-bold')
        while f.getlength(t) > width and size > 10:
            size -= 2
            f = _font(size, 'sans-bold')
        return f
    t = 'WEIGH-IN'
    f = fit(t, 110, x1 - x0 - 70)
    d.text(((x0 + x1) / 2 - f.getlength(t) / 2, y0 + 30), t, font=f, fill=ink)
    t = 'ONE RATION PER HEAD'
    f = fit(t, 50, x1 - x0 - 70)
    d.text(((x0 + x1) / 2 - f.getlength(t) / 2, y0 + 168), t, font=f, fill=ink)
    for _ in range(40):
        x, y, r = rnd.uniform(x0, x1), rnd.uniform(y0, y1), rnd.uniform(2, 8)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(64, 44, 26, rnd.randint(80, 180)))
    # SERVED: white on black enamel, a flag like a cab meter's.
    x0, y0, x1, y1 = WEIGH_CELLS['served']
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(22, 22, 20))
    d.rectangle((x0 + 8, y0 + 8, x1 - 9, y1 - 9), outline=cream, width=5)
    t = 'SERVED'
    f = fit(t, 92, x1 - x0 - 80)
    d.text(((x0 + x1) / 2 - f.getlength(t) / 2, y0 + 10), t, font=f, fill=cream)
    x0, y0, x1, y1 = WEIGH_CELLS['flagback']
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(36, 34, 30))
    x0, y0, x1, y1 = WEIGH_CELLS['enamel']
    d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=(150, 142, 118))
    _grain(img, rnd, 14)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    _save(img, os.path.basename(path), 64)


def make_no_rations(path):
    """NO RATIONS · GRADE 4, slapped on the wall over the counter with a wide brush in whitewash: blunt, running."""
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(4403)
    w, h = 1024, 384
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, 'RGBA')
    paint = (214, 208, 190)

    def brush_text(text, size, y, x_pad=30):
        f = _font(size, 'sans-bold')
        tw = f.getlength(text)
        scale = min(1.0, (w - 2 * x_pad) / tw)
        f = _font(int(size * scale), 'sans-bold')
        tw = f.getlength(text)
        x = (w - tw) / 2
        for ch in text:
            if ch != ' ':
                for _ in range(3):                         # a wide brush, three loaded passes
                    d.text((x + rnd.uniform(-3, 3), y + rnd.uniform(-5, 5)), ch, font=f, fill=(*paint, rnd.randint(110, 170)))
                bb = f.getbbox(ch)
                for _ in range(rnd.randint(0, 2)):        # runs
                    dx = x + rnd.uniform(bb[0] + 6, bb[2] - 6)
                    d.line((dx, y + bb[3] - 6, dx, y + bb[3] + rnd.uniform(12, 70)), fill=(*paint, 150), width=rnd.randint(3, 6))
            x += f.getlength(ch) + rnd.uniform(-2, 6)
    brush_text('NO RATIONS', 190, 10)
    brush_text('GRADE 4', 130, 222, x_pad=200)
    # Dry brush: knock streaks out of it.
    px = img.load()
    for _ in range(900):
        x, y = rnd.randrange(w), rnd.randrange(h)
        L = rnd.randint(6, 40)
        for k in range(L):
            xx = min(w - 1, x + k)
            r, g, b, a = px[xx, y]
            if a:
                px[xx, y] = (r, g, b, int(a * 0.35))
    img = img.filter(ImageFilter.GaussianBlur(1.0))
    _save(img, os.path.basename(path))


MAKERS = {
    'remains_atlas.png': make_remains_atlas,
    'weighin.png': make_weighin,
    'no_rations.png': make_no_rations,
    'ration_board.png': make_ration_board,
    'grade_notice.png': make_grade_notice,
    'sky_mural.png': make_sky_mural,
    'crayon_drawing.png': make_crayon_drawing,
    'shrine_names.png': make_shrine_names,
    'chalk_tally.png': make_chalk_tally,
    'drum_stencil.png': make_drum_stencil,
    'ration_sign.png': make_ration_sign,
    'drum_ring.png': make_drum_ring,
}


def texture(name, force=False):
    path = os.path.join(TEX, name)
    if force or not os.path.exists(path):
        os.makedirs(TEX, exist_ok=True)
        MAKERS[name](path)
    return path


def make_textures(force=False):
    for name in MAKERS:
        texture(name, force)


if __name__ == '__main__':
    make_textures(force=True)
    print('textures in', TEX)
