"""Chapter 1, pass 3 (docs/chapter1_pass3_plan.md, sections 2, 3 and 5): the lore dressing of scenes 1 to 9, the
cage's readability pieces, and the interactables' new materials. Built in FINAL world x, after insert_scenes() has
opened the gaps (so DL-05 The Ration Hall is x 47.9 to 59.8 and DL-10 Up Only is x 118.8 to 131; neither is
touched here). Other builders' objects are only changed by name.

What happened down here, told from the walls (visuals first; the words are for readers):
  DL-01  LoreGradeChart: the refuge in four painted bands, gold at the top, the depot at the bottom in plain grey,
         "GRADE 4 · LABOUR", on the bulkhead over the exit. LoreRoster: the torn night-shift roster, names
         struck out, by the dispatch board; chalk tallies. A cot, a blanket and ration tins in the hall behind.
  DL-02  LoreNoticeBoard: "NIGHT SHIFT CUT" and "GRADE 3 TRANSFERS SUSPENDED" (an up arrow, crossed out).
         LoreMugNames: the night shift's names on the hanging mugs; the third is IVO, with a crooked tree (the
         sender of D-17's parcel signs I.V. under the same tree). A bedroll and a tin in the tea corner.
  DL-03  LoreStencilKeep "WE KEEP YOU ALIVE" across the weighing room wall; LoreProtest, a poster of a sorter
         holding the domes up on his back, half torn down (LoreProtestFlap hangs off it).
  DL-04  LoreMemorial: couriers' tags on a wire over the empty rack with the chalk flowers.
  DL-06  LoreBarricade: sorting crates once stacked across the floor, pulled apart and pushed to the wall;
         LoreUpStencil: "UP IS FOR THEM" stencilled, rollered over, "EVERYONE UP" painted across it.
  DL-07  (pass 5: LoreEveryoneUp, the same hand by the residential door, is cut: EVERYONE UP is kept to DL-06 and
         ring C's C-106 wall.)
  DL-08  LoreTimetable: the relocation lift timetable, every departure struck through; tallies beside it;
         a stove, a pan and tins by the broom.
  DL-09  LoreBelongings: a pram wheel and a tied bundle left at the lower landing.
  Dregs  LoreSoot* streaks, LorePatch* plates bolted over holes.

The cage (DL-09), section 3:
  BalanceGauge   a dial on a post at the top landing's left end, two pans drawn on it (the counterweight's left,
                 the cage's right), a hatched "too light" arc on the cage's side and a white mark at the top.
  BalanceNeedle  origin at the dial's centre; it points up when balanced. It turns about Blender +Y (game -Z):
                 rotation_euler.y = +48 deg (game rotation.z = -48 deg) is "too light" (leaning to the cage),
                 +24 deg one plate, 0 balanced. Ticks are painted at 48, 32, 24, 16 and 0.
  TrayLamp       a small warm lamp (emissive) in a cage shade on the shaft's back wall over the counterweight's
                 tray at its starting height; TrayLampShade is its fitting.
  LoreChevrons   white chevrons on the shaft's back wall at the lit landing's level (z 1.6), either side;
  CageMarker     a white chevron on the cage's right front post at its floor (parented to Cage): the two line up
                 when the floor is level with the landing.

Interactables without red (section 2): every slot that uses LeverRed is reassigned by role (REMAP below) to
HandledSteel, HandledBrass, WornIron, WornStrap, GaugeNeedle or SafetyYellow; LeverRed stays only on the franking
press's hazard bands (FrankingPress, PressRam). The CurioTag_* objects are deleted.

Clips (add_clips): CageRideLever (48 f, loops) and CagePullPawl (18 f), at the stand point RIDE_STAND.

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y. Game (x, z, -y).
"""
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
sys.path.insert(0, HERE)
import handwriting as hw  # noqa: E402

FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_C = '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf'
FONT_M = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
FONT_S = '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'


# =====================================================================================================================
# Textures (PIL, into art/pass3/textures/lore_*.png; rewritten only when missing, or all with make_textures(True))
# =====================================================================================================================

def _font(path, size):
    from PIL import ImageFont
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _wear_alpha(img, seed, holes=60, rmin=2, rmax=9, keep=(90, 210), blur=1.5):
    """Knock patchy holes into an RGBA image's alpha: old paint, flaking."""
    from PIL import Image, ImageDraw, ImageFilter, ImageChops
    rnd = random.Random(seed)
    w, h = img.size
    m = Image.new('L', (w, h), 255)
    d = ImageDraw.Draw(m)
    for _ in range(holes):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(rmin, rmax)
        d.ellipse((x - r, y - r * rnd.uniform(0.4, 1), x + r, y + r), fill=rnd.randint(*keep))
    img.putalpha(ImageChops.multiply(img.split()[3], m.filter(ImageFilter.GaussianBlur(blur))))
    return img


def _grime(img, seed, amount=0.5):
    """Stains and streaks over an RGB(A) image, composited (its alpha is kept)."""
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(seed)
    src = img.convert('RGBA')
    w, h = src.size
    over = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    for _ in range(int(40 * amount)):
        x, y, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(4, w * 0.08)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(50, 38, 24, rnd.randint(8, 26)))
    for _ in range(int(12 * amount)):
        x = rnd.uniform(0, w)
        d.line((x, rnd.uniform(0, h * 0.4), x + rnd.uniform(-10, 10), h), fill=(30, 24, 18, rnd.randint(10, 30)),
               width=rnd.randint(2, 7))
    out = Image.alpha_composite(src, over.filter(ImageFilter.GaussianBlur(3)))
    out.putalpha(src.split()[3])
    out = out.filter(ImageFilter.GaussianBlur(0.7))
    return out if img.mode == 'RGBA' else out.convert(img.mode)


def _torn_edge(img, side, seed, depth=0.18, rough=14):
    """Tear an RGBA image along one side ('right', 'bottom', 'top', 'diag'), leaving a ragged paper edge."""
    from PIL import ImageDraw
    rnd = random.Random(seed)
    w, h = img.size
    a = img.split()[3]
    d = ImageDraw.Draw(a)
    if side == 'right':
        pts, x = [], w * (1 - depth)
        for y in range(0, h + rough, rough):
            x += rnd.uniform(-rough, rough) * 0.8
            pts.append((x, y))
        d.polygon(pts + [(w, h), (w, 0)], fill=0)
    elif side == 'bottom':
        pts, y = [], h * (1 - depth)
        for x in range(0, w + rough, rough):
            y += rnd.uniform(-rough, rough) * 0.8
            pts.append((x, y))
        d.polygon(pts + [(w, h), (0, h)], fill=0)
    elif side == 'diag':                                   # from the top right corner down to the bottom middle
        pts = []
        for k in range(0, 21):
            t = k / 20
            pts.append((w * (0.98 - 0.5 * t) + rnd.uniform(-rough, rough), h * t))
        d.polygon(pts + [(w, h), (w, 0)], fill=0)
    img.putalpha(a)
    return img


def make_grade_chart(path):
    """The refuge's grade chart, painted on the bulkhead: four bands from the surface down, each plainer than the
    one above. GRADE 1 · RING A gold, with domes and a sun over it; GRADE 2 · RING B green; GRADE 3 blue-grey;
    GRADE 4 · LABOUR (ring C, the works, the depot) in bare grey with pipes, a cog and a parcel. An arrow points up
    beside the bands, and somebody has scratched a small tally into the bottom band. Alpha: painted on concrete."""
    from PIL import Image, ImageDraw
    w, h = 1024, 704
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cream, dark = (214, 204, 176, 255), (26, 26, 24, 255)
    x0, x1 = 150, 990
    bands = [  # (top, bottom, fill, label, sub)
        (70, 220, (176, 138, 52, 255), 'GRADE 1', 'RING A'),
        (226, 356, (70, 104, 76, 255), 'GRADE 2', 'RING B'),
        (362, 482, (66, 80, 92, 255), 'GRADE 3', ''),
        (488, 660, (92, 92, 88, 255), 'GRADE 4 · LABOUR', 'RING C · WORKS · DEPOT'),
    ]
    # The surface: a line of ground with grass tufts and a sun above it, over the top band.
    d.line((x0, 40, x1, 40), fill=cream, width=8)
    for k in range(18):
        gx = x0 + 20 + k * 46
        d.line((gx, 40, gx - 8, 22), fill=cream, width=5)
        d.line((gx, 40, gx + 6, 20), fill=cream, width=5)
    d.ellipse((x1 - 120, -40, x1 - 40, 40), outline=cream, width=8)
    for top, bot, fill, label, sub in bands:
        d.rectangle((x0, top, x1, bot), fill=fill)
        d.text((x0 + 24, top + 14), label, font=_font(FONT, 46 if label.startswith('GRADE 4') else 52), fill=cream)
        if sub:
            d.text((x0 + 26, top + 74), sub, font=_font(FONT_C, 42), fill=cream)
    # Pictograms per band: domes and a tower (1), houses with gardens (2), plain rows of doors (3), pipes, a cog
    # and a parcel (4).
    gx = 640
    for k, r in enumerate((52, 36, 44)):
        cx = gx + k * 110
        d.pieslice((cx - r, 208 - 2 * r, cx + r, 208), 180, 360, fill=cream)
        d.rectangle((cx - r, 168, cx + r, 210), fill=cream)
    d.rectangle((gx + 300, 92, gx + 324, 210), fill=cream)
    for k in range(3):
        hx = 640 + k * 110
        d.polygon([(hx - 40, 300), (hx, 262), (hx + 40, 300)], fill=cream)
        d.rectangle((hx - 32, 300, hx + 32, 346), fill=cream)
        d.rectangle((hx + 8, 316, hx + 22, 346), fill=fill_of(bands, 1))
        d.ellipse((hx + 44, 318, hx + 66, 346), fill=(150, 190, 120, 255))
    for k in range(7):
        dx = 600 + k * 52
        d.rectangle((dx, 396, dx + 30, 468), outline=cream, width=6)
    py = 570
    d.line((560, py, 980, py), fill=cream, width=14)
    d.line((560, py + 46, 980, py + 46), fill=cream, width=8)
    for k in range(4):
        d.line((600 + k * 110, py - 50, 600 + k * 110, py + 60), fill=cream, width=8)
    cx, cy = 680, 600
    for k in range(8):
        a = k * math.pi / 4
        d.line((cx + 30 * math.cos(a), cy + 30 * math.sin(a), cx + 48 * math.cos(a), cy + 48 * math.sin(a)), fill=cream, width=14)
    d.ellipse((cx - 32, cy - 32, cx + 32, cy + 32), outline=cream, width=12)
    d.rectangle((830, 590, 900, 646), fill=cream)
    d.line((865, 590, 865, 646), fill=fill_of(bands, 3), width=6)
    d.line((830, 616, 900, 616), fill=fill_of(bands, 3), width=6)
    # The up arrow beside the bands, from the bottom to the surface.
    d.rectangle((54, 120, 92, 660), fill=cream)
    d.polygon([(30, 130), (73, 50), (116, 130)], fill=cream)
    # Somebody's scratched tally in the bottom band, and a chalk "us" arrow pointing at it.
    for k in range(9):
        tx = 470 + k * 14 + (8 if k > 4 else 0)
        d.line((tx, 590, tx + 3, 640), fill=(232, 228, 214, 230), width=4)
    d.line((464, 628, 534, 598), fill=(232, 228, 214, 230), width=4)
    img = _wear_alpha(img, 101, holes=150, rmin=2, rmax=8, keep=(60, 210))
    img = _grime(img, 102, 0.8)
    # Soot from the door's lamp, up the middle.
    from PIL import ImageFilter
    soot = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(soot)
    for k in range(9):
        sd.ellipse((380 + k * 14, 380 - k * 40, 560 - k * 6, h + 40), fill=(10, 9, 8, 40))
    soot = soot.filter(ImageFilter.GaussianBlur(30))
    img.alpha_composite(soot)
    img.save(path)


def fill_of(bands, i):
    return bands[i][2]


def make_roster(path):
    """The night-shift roster, torn off down its right side: a ruled sheet with a typed head, NIGHT SHIFT and a
    week's days, names in a column, most struck through, two left. Alpha: the tear."""
    from PIL import Image, ImageDraw
    w, h = 384, 512
    img = Image.new('RGBA', (w, h), (210, 200, 170, 255))
    d = ImageDraw.Draw(img)
    ink, pencil = (40, 38, 34, 255), (70, 70, 80, 255)
    d.rectangle((0, 0, w, 64), fill=(186, 176, 146, 255))
    d.text((16, 10), 'NIGHT SHIFT', font=_font(FONT, 34), fill=ink)
    d.text((16, 72), 'SORTING · DEPOT 4', font=_font(FONT_C, 20), fill=ink)
    for k, day in enumerate(('M', 'T', 'W', 'T', 'F', 'S', 'S')):
        d.text((176 + k * 28, 104), day, font=_font(FONT_M, 18), fill=ink)
    names = ['ODA', 'TOMAS', 'IVO', 'RUTH', 'BRANKO', 'PELL', 'SAMI', 'D-17', 'D-04', 'D-11', 'HANNA']
    struck = {0, 1, 3, 4, 5, 6, 8, 9, 10}
    for i, n in enumerate(names):
        y = 136 + i * 32
        d.line((10, y + 28, w - 10, y + 28), fill=(150, 140, 116, 255), width=2)
        hw.write(d, n, 18, y + 4, 20, 'clerk', ink, 3, seed=200 + i)
        for k in range(7):
            if (i * 3 + k) % 4 != 1:
                hw.write(d, '/', 180 + k * 28, y + 6, 16, 'parent', pencil, 2, seed=300 + i * 7 + k)
        if i in struck:
            d.line((10, y + 15, 170, y + 13), fill=pencil, width=4)
    hw.write(d, 'CUT', 210, 470, 30, 'parent', (150, 40, 34, 255), 4, seed=11)
    img = _torn_edge(img, 'right', 7, depth=0.22, rough=18)
    img = _torn_edge(img, 'bottom', 8, depth=0.04, rough=12)
    _grime(img, 103, 0.7).save(path)


def make_notices(path):
    """The Sorting Hall's notice board: cork in a frame, two notices pinned. NIGHT SHIFT CUT (a moon with a pair of
    scissors through a row of figures) and GRADE 3 TRANSFERS SUSPENDED (a figure on the bottom band, an arrow up to
    the band above, crossed out). A third notice torn away, its pins and corner left."""
    from PIL import Image, ImageDraw
    w, h = 768, 640
    img = Image.new('RGB', (w, h), (118, 86, 54))
    d = ImageDraw.Draw(img)
    rnd = random.Random(5)
    for _ in range(3000):                                      # cork
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        c = rnd.randint(-22, 22)
        d.point((x, y), fill=(118 + c, 86 + c, 54 + c))
    d.rectangle((0, 0, w - 1, h - 1), outline=(52, 38, 24), width=22)
    ink, paper, navy = (34, 32, 30), (214, 206, 180), (34, 46, 70)
    pin = (180, 150, 70)
    # NIGHT SHIFT CUT
    a = (40, 40, 380, 470)
    d.rectangle(a, fill=paper)
    d.rectangle((a[0], a[1], a[2], a[1] + 70), fill=navy)
    d.text((a[0] + 18, a[1] + 12), 'NOTICE', font=_font(FONT, 40), fill=paper)
    d.text((a[0] + 20, a[1] + 84), 'NIGHT SHIFT', font=_font(FONT, 44), fill=ink)
    d.text((a[0] + 20, a[1] + 134), 'CUT', font=_font(FONT, 74), fill=(150, 40, 34))
    mx, my = a[0] + 260, a[1] + 168                           # a moon over a row of figures, scissors through them
    d.ellipse((mx - 34, my - 34, mx + 34, my + 34), fill=(196, 170, 70))
    d.ellipse((mx - 18, my - 44, mx + 44, my + 22), fill=paper)
    for k in range(5):
        fx = a[0] + 40 + k * 58
        d.ellipse((fx - 13, 296, fx + 13, 322), fill=ink)
        d.rectangle((fx - 16, 326, fx + 16, 372), fill=ink)
    d.line((a[0] + 20, 360, a[2] - 20, 300), fill=(150, 40, 34), width=10)
    for k in range(4):
        d.line((a[0] + 24, 396 + k * 18, a[2] - 24 - (k % 2) * 60, 396 + k * 18), fill=(120, 116, 104), width=5)
    d.text((a[0] + 20, 446 - 4), 'P.A. 309', font=_font(FONT_M, 18), fill=ink)
    for px, py in ((a[0] + 14, a[1] + 8), (a[2] - 14, a[1] + 8)):
        d.ellipse((px - 8, py - 8, px + 8, py + 8), fill=pin)
    # GRADE 3 TRANSFERS SUSPENDED
    b = (404, 120, 734, 600)
    d.rectangle(b, fill=(206, 200, 176))
    d.text((b[0] + 16, b[1] + 16), 'GRADE 3', font=_font(FONT, 44), fill=ink)
    d.text((b[0] + 16, b[1] + 66), 'TRANSFERS', font=_font(FONT, 38), fill=ink)
    d.text((b[0] + 16, b[1] + 108), 'SUSPENDED', font=_font(FONT, 38), fill=(150, 40, 34))
    by = b[1] + 176
    d.rectangle((b[0] + 30, by, b[2] - 30, by + 90), fill=(66, 80, 92))          # grade 3's band
    d.rectangle((b[0] + 30, by + 190, b[2] - 30, by + 280), fill=(120, 120, 114))   # grade 4's
    fx = b[0] + 110
    d.ellipse((fx - 16, by + 206, fx + 16, by + 238), fill=ink)
    d.rectangle((fx - 20, by + 240, fx + 20, by + 276), fill=ink)
    d.rectangle((b[0] + 206, by + 110, b[0] + 226, by + 186), fill=ink)            # the arrow up
    d.polygon([(b[0] + 186, by + 116), (b[0] + 216, by + 86), (b[0] + 246, by + 116)], fill=ink)
    d.line((b[0] + 160, by + 96, b[0] + 272, by + 190), fill=(150, 40, 34), width=14)   # crossed out
    d.line((b[0] + 272, by + 96, b[0] + 160, by + 190), fill=(150, 40, 34), width=14)
    d.text((b[0] + 16, b[3] - 36), 'BY ORDER · P.A. 310', font=_font(FONT_M, 18), fill=ink)
    for px, py in ((b[0] + 14, b[1] + 8), (b[2] - 14, b[1] + 8)):
        d.ellipse((px - 8, py - 8, px + 8, py + 8), fill=pin)
    # The torn one: a corner left under a pin.
    d.polygon([(40, 500), (130, 496), (96, 530), (70, 600), (40, 604)], fill=paper)
    d.ellipse((52, 508, 68, 524), fill=pin)
    # Somebody's pencil on NIGHT SHIFT CUT: "AND US?"
    hw.write(d, 'AND US?', a[0] + 160, 432, 28, 'parent', (70, 70, 80), 4, seed=17)
    _grime(img, 104, 0.6).save(path)


def make_stencil_keep(path):
    """WE KEEP YOU ALIVE, sprayed through a stencil (the letters' bridges show), with overspray and drips."""
    from PIL import Image, ImageDraw, ImageFilter
    f = _font(FONT, 140)
    w, h = int(ImageDraw.Draw(Image.new('L', (1, 1))).textlength('WE KEEP YOU ALIVE', font=f)) + 40, 192
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    paint = (222, 214, 196, 255)
    d.text((20, 18), 'WE KEEP YOU ALIVE', font=f, fill=paint)
    # The stencil's bridges: thin gaps cut through O, P, A, E... (vertical clear strips).
    rnd = random.Random(9)
    a = img.split()[3]
    ad = ImageDraw.Draw(a)
    x = 20
    for ch in 'WE KEEP YOU ALIVE':
        cw = d.textlength(ch, font=f)
        if ch in 'OPAEKYW':
            ad.rectangle((x + cw * 0.45, 18, x + cw * 0.45 + 7, 180), fill=0)
        x += cw
    for _ in range(40):                                        # drips
        dx = rnd.uniform(30, w - 60)
        if a.getpixel((int(dx), 150)) > 0:
            ad.line((dx, 150, dx, 150 + rnd.uniform(10, 40)), fill=200, width=4)
    img.putalpha(a)
    halo = img.filter(ImageFilter.GaussianBlur(9))            # overspray
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    halo.putalpha(halo.split()[3].point(lambda v: int(v * 0.35)))
    out.alpha_composite(halo)
    out.alpha_composite(img)
    out = _wear_alpha(out, 105, holes=120, rmin=2, rmax=8, keep=(40, 200))
    out.save(path)


def make_protest(path):
    """A protest poster, half torn down: a sorter in an apron, bent under the domes of the upper rings he carries
    on his back. Its slogan (WHO CARRIES WHOM?) is on the half that hangs. Two images: the poster on the wall
    (torn diagonally) and the flap that hangs from it, in one atlas (left half the poster, right half the flap)."""
    from PIL import Image, ImageDraw
    w, h = 384, 512
    full = Image.new('RGBA', (w, h), (198, 170, 120, 255))
    d = ImageDraw.Draw(full)
    ink, red = (30, 26, 22, 255), (150, 44, 32, 255)
    d.rectangle((10, 10, w - 10, h - 10), outline=ink, width=8)
    # The sorter: bent, legs apart, arms up behind his head holding a slab, the domes on it.
    cx = 190
    d.ellipse((cx - 30, 250, cx + 22, 300), fill=ink)                          # head, bowed
    d.polygon([(cx - 40, 300), (cx + 50, 286), (cx + 70, 400), (cx - 30, 410)], fill=ink)   # body
    d.polygon([(cx - 30, 410), (cx + 70, 400), (cx + 90, 470), (cx - 50, 476)], fill=red)   # the apron
    d.rectangle((cx - 40, 470, cx - 14, 500), fill=ink)
    d.rectangle((cx + 50, 466, cx + 76, 500), fill=ink)
    d.line((cx - 30, 300, cx - 80, 222), fill=ink, width=22)
    d.line((cx + 44, 290, cx + 94, 222), fill=ink, width=22)
    d.rectangle((40, 196, 344, 226), fill=ink)                                 # the slab
    for k, r in enumerate((44, 62, 40)):                                       # the domes on it
        dx = 90 + k * 100
        d.pieslice((dx - r, 196 - 2 * r, dx + r, 196), 180, 360, fill=(220, 190, 90, 255))
    d.rectangle((300, 60, 316, 196), fill=(220, 190, 90, 255))
    d.text((24, 22), 'WHO CARRIES', font=_font(FONT, 40), fill=red)
    d.text((24, 64), 'WHOM?', font=_font(FONT, 40), fill=red)
    full = _grime(full, 106, 0.7)
    wall = _torn_edge(full.copy(), 'diag', 3, rough=16)
    flap = full.copy()
    fa = flap.split()[3]
    wa = wall.split()[3]
    from PIL import ImageChops
    flap.putalpha(ImageChops.subtract(fa, wa))
    atlas = Image.new('RGBA', (2 * w, h), (0, 0, 0, 0))
    atlas.alpha_composite(_wear_alpha(wall, 107, holes=20), (0, 0))
    atlas.alpha_composite(flap, (w, 0))
    atlas.save(path)


def make_up_stencil(path):
    """UP IS FOR THEM, stencilled in black; rollered over later with grey (the words still ghost through); then
    EVERYONE UP brushed across it in white, with an arrow."""
    from PIL import Image, ImageDraw, ImageFilter
    w, h = 1024, 512
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    under = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ud = ImageDraw.Draw(under)
    ud.text((40, 60), 'UP IS', font=_font(FONT, 150), fill=(18, 18, 18, 255))
    ud.text((40, 230), 'FOR THEM', font=_font(FONT, 150), fill=(18, 18, 18, 255))
    under = _wear_alpha(under, 108, holes=60, rmin=4, rmax=16)
    img.alpha_composite(under)
    roller = Image.new('RGBA', (w, h), (0, 0, 0, 0))           # the grey roller, streaky, not quite covering
    rd = ImageDraw.Draw(roller)
    rnd = random.Random(10)
    for k in range(9):
        x = 20 + k * 112
        rd.rectangle((x, 30 + rnd.uniform(0, 30), x + 120, 420 + rnd.uniform(0, 40)), fill=(84, 86, 82, rnd.randint(105, 140)))
    roller = roller.filter(ImageFilter.GaussianBlur(3))
    img.alpha_composite(roller)
    over = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    od = ImageDraw.Draw(over)
    white = (232, 228, 214, 255)
    hw.write(od, 'EVERYONE', 70, 120, 120, 'paint', white, 20, seed=40)
    hw.write(od, 'UP', 330, 290, 150, 'paint', white, 24, seed=41)
    od.rectangle((800, 190, 840, 470), fill=white)
    od.polygon([(760, 210), (820, 80), (880, 210)], fill=white)
    for _ in range(14):
        x = rnd.uniform(80, 880)
        if over.getpixel((int(x), 270))[3] > 0:
            od.line((x, 270, x, 270 + rnd.uniform(20, 60)), fill=white, width=5)
    img.alpha_composite(_wear_alpha(over, 109, holes=40, rmin=3, rmax=10, keep=(80, 200)))
    img.save(path)


def make_everyone_up(path):
    """EVERYONE UP and an arrow, the same hand, smaller, by the residential door."""
    from PIL import Image, ImageDraw
    w, h = 512, 512
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    white = (232, 228, 214, 255)
    hw.write(d, 'EVERYONE', 20, 300, 66, 'paint', white, 13, seed=42)
    hw.write(d, 'UP', 170, 390, 90, 'paint', white, 16, seed=43)
    d.rectangle((236, 80, 272, 280), fill=white)
    d.polygon([(190, 100), (254, 10), (318, 100)], fill=white)
    _wear_alpha(img, 110, holes=30, rmin=3, rmax=10, keep=(60, 200)).save(path)


def make_timetable(path):
    """RELOCATION · LIFT 1 · UP: a departures sheet, eight rows (date, time, grades, a lift pictogram), every row
    struck through in pencil; the last, P.A. 311, ringed and crossed: LAST."""
    from PIL import Image, ImageDraw
    w, h = 512, 704
    img = Image.new('RGBA', (w, h), (212, 204, 178, 255))
    d = ImageDraw.Draw(img)
    ink, navy, pencil, red = (34, 32, 30, 255), (34, 46, 70, 255), (64, 64, 74, 255), (150, 44, 32, 255)
    d.rectangle((0, 0, w, 110), fill=navy)
    d.text((20, 10), 'RELOCATION', font=_font(FONT, 52), fill=(214, 206, 180, 255))
    d.text((20, 66), 'LIFT 1  ·  UP', font=_font(FONT_C, 34), fill=(214, 206, 180, 255))
    d.polygon([(440, 30), (470, 80), (410, 80)], fill=(214, 206, 180, 255))
    rows = [('P.A. 310', '06.00', '3'), ('P.A. 310', '18.00', '3'), ('P.A. 310', '06.00', '4'), ('P.A. 310', '18.00', '4'),
            ('P.A. 311', '06.00', '4'), ('P.A. 311', '12.00', '4'), ('P.A. 311', '18.00', '4'), ('P.A. 311', '06.00', 'ALL')]
    rnd = random.Random(12)
    for i, (dte, tm, gr) in enumerate(rows):
        y = 140 + i * 66
        d.line((16, y + 58, w - 16, y + 58), fill=(150, 140, 116, 255), width=2)
        d.text((24, y + 10), dte, font=_font(FONT_M, 28), fill=ink)
        d.text((190, y + 10), tm, font=_font(FONT_M, 28), fill=ink)
        d.text((310, y + 10), 'GR ' + gr, font=_font(FONT_M, 28), fill=ink)
        d.rectangle((440, y + 6, 476, y + 50), outline=ink, width=4)               # a lift car
        d.polygon([(450, y + 30), (458, y + 16), (466, y + 30)], fill=ink)
        y0 = y + 24 + rnd.uniform(-4, 4)
        d.line((14, y0, w - 18, y0 + rnd.uniform(-8, 8)), fill=pencil, width=5)
    d.ellipse((290, 600, 500, 680), outline=red, width=6)
    hw.write(d, 'LAST', 330, 620, 40, 'parent', red, 6, seed=13)
    img = _torn_edge(img, 'bottom', 14, depth=0.02, rough=10)
    _grime(img, 111, 0.8).save(path)


def make_tally(path):
    """Chalk tallies, rows of five, a lot of them: days counted."""
    from PIL import Image, ImageDraw
    w, h = 384, 384
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rnd = random.Random(15)
    chalk = (226, 224, 210, 220)
    for row in range(5):
        for g in range(4 if row < 4 else 2):
            x0, y0 = 20 + g * 90, 20 + row * 72
            for k in range(4):
                x = x0 + k * 16 + rnd.uniform(-2, 2)
                d.line((x, y0 + rnd.uniform(-3, 3), x + rnd.uniform(-4, 4), y0 + 54), fill=chalk, width=5)
            d.line((x0 - 6, y0 + 44, x0 + 64, y0 + 8), fill=chalk, width=5)
    _wear_alpha(img, 112, holes=30, rmin=2, rmax=6, keep=(60, 200), blur=1).save(path)


def make_mug_names(path):
    """The night shift's names on their mugs, in enamel paint, one per row: ODA, TOMAS, IVO (with a crooked tree),
    RUTH. Alpha."""
    from PIL import Image, ImageDraw
    w, h = 512, 512
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cols = [(40, 62, 92, 255), (60, 96, 64, 255), (34, 40, 80, 255), (120, 70, 40, 255)]
    for i, (n, col) in enumerate(zip(('ODA', 'TOMAS', 'IVO', 'RUTH'), cols)):
        y = i * 128
        size = 76 if len(n) <= 4 else 60
        x = hw.write(d, n, 30, y + 26, size, 'paint', col, 11, seed=50 + i)
        if n == 'IVO':
            hw.crooked_tree(d, x + 40, y + 112, 96, col, random.Random(4), width=7)
    img.save(path)


def make_gauge(path):
    """The cage's balance gauge: a cream dial in a dark bezel. A balance beam drawn on it: the counterweight's pan
    on the left (a stack of slabs and an open tray), the cage's on the right (a cage with a little courier in it).
    A scale arc over the pivot: a hatched amber band on the cage's side (too light), a white mark at the top
    (balanced), ticks at 48, 32, 24, 16 and 0 degrees. The needle is a separate object."""
    from PIL import Image, ImageDraw
    s = 512
    img = Image.new('RGB', (s, s), (20, 20, 18))
    d = ImageDraw.Draw(img)
    c = s / 2
    d.ellipse((8, 8, s - 8, s - 8), fill=(40, 40, 36))
    d.ellipse((30, 30, s - 30, s - 30), fill=(214, 206, 180))
    ink = (34, 32, 30)
    R0, R1 = 150, 206
    # The too-light band, from 16 to 60 degrees right of top (the needle leans toward the heavy cage).
    for a in range(16, 61, 2):
        t = math.radians(a)
        d.line((c + R0 * math.sin(t), c - R0 * math.cos(t), c + R1 * math.sin(t), c - R1 * math.cos(t)),
               fill=(206, 140, 40), width=6)
    for a in range(16, 61, 8):                                   # its hatching
        t0, t1 = math.radians(a), math.radians(a + 6)
        d.line((c + R0 * math.sin(t0), c - R0 * math.cos(t0), c + R1 * math.sin(t1), c - R1 * math.cos(t1)),
               fill=ink, width=4)
    d.arc((c - R1, c - R1, c + R1, c + R1), 210, 330, fill=ink, width=5)
    for a, L in ((48, 34), (32, 24), (24, 34), (16, 24), (0, 44), (-24, 24), (-48, 24)):
        t = math.radians(a)
        d.line((c + (R1 - L) * math.sin(t), c - (R1 - L) * math.cos(t), c + (R1 + 6) * math.sin(t), c - (R1 + 6) * math.cos(t)),
               fill=ink, width=7)
    d.polygon([(c - 18, c - R1 - 26), (c + 18, c - R1 - 26), (c, c - R1 + 8)], fill=(250, 248, 236), outline=ink)
    # The beam and its two pans (drawn level), under the arc.
    by = c + 70
    d.line((c - 170, by, c + 170, by), fill=ink, width=10)
    d.polygon([(c - 22, by + 70), (c + 22, by + 70), (c, by + 6)], fill=ink)
    for sx in (-1, 1):
        px = c + sx * 150
        d.line((px - 40, by + 66, px, by), fill=ink, width=4)
        d.line((px + 40, by + 66, px, by), fill=ink, width=4)
        d.arc((px - 50, by + 46, px + 50, by + 96), 0, 180, fill=ink, width=8)
    px = c - 150                                                 # counterweight: slabs, the tray on top
    for k in range(3):
        d.rectangle((px - 26, by + 18 - k * 0, px + 26, by + 24), fill=None)
    d.rectangle((px - 22, by + 36 - 64, px + 22, by + 36 - 14), outline=ink, width=5)
    for k in range(3):
        d.line((px - 22, by - 18 - k * 12, px + 22, by - 18 - k * 12), fill=ink, width=3)
    d.line((px - 30, by - 30, px + 30, by - 30), fill=(206, 140, 40), width=8)       # the tray, amber
    px = c + 150                                                 # the cage, with a little courier in it
    d.rectangle((px - 28, by - 44, px + 28, by + 40), outline=ink, width=5)
    for k in range(3):
        d.line((px - 28 + k * 19, by - 44, px - 28 + k * 19, by + 40), fill=ink, width=2)
    d.rounded_rectangle((px - 14, by - 6, px + 14, by + 16), radius=4, fill=ink)
    d.rectangle((px - 16, by - 20, px + 16, by - 8), fill=ink)
    d.line((px - 8, by + 16, px - 8, by + 30), fill=ink, width=4)
    d.line((px + 8, by + 16, px + 8, by + 30), fill=ink, width=4)
    d.ellipse((c - 16, c - 16, c + 16, c + 16), fill=(60, 60, 56))                    # the hub
    img = _grime(img.convert('RGBA'), 113, 0.4)
    img.convert('RGB').save(path)


def make_chevrons(path):
    """White painted chevrons, three nested, pointing right (alpha). Mirrored by UV for the left-pointing ones."""
    from PIL import Image, ImageDraw
    w, h = 256, 256
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    white = (240, 238, 228, 255)
    for k in range(3):
        x = 20 + k * 70
        d.polygon([(x, 20), (x + 40, 20), (x + 110, 128), (x + 40, 236), (x, 236), (x + 70, 128)], fill=white)
    _wear_alpha(img, 114, holes=25, rmin=2, rmax=8, keep=(100, 220)).save(path)


def make_soot(path):
    """A soot plume, black, soft (alpha): above a lamp or a stove."""
    from PIL import Image, ImageDraw, ImageFilter
    w, h = 256, 512
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rnd = random.Random(16)
    for k in range(30):
        y = h - k * 16
        r = 30 + k * 2.5 + rnd.uniform(-8, 8)
        d.ellipse((w / 2 - r + rnd.uniform(-10, 10), y - r, w / 2 + r, y + r * 0.5), fill=(8, 7, 6, max(0, 120 - k * 4)))
    img.filter(ImageFilter.GaussianBlur(16)).save(path)


TEXTURES = {
    'chart': ('lore_grade_chart.png', make_grade_chart),
    'roster': ('lore_roster.png', make_roster),
    'notices': ('lore_notices.png', make_notices),
    'keep': ('lore_stencil_keep.png', make_stencil_keep),
    'protest': ('lore_protest.png', make_protest),
    'upstencil': ('lore_up_stencil.png', make_up_stencil),
    'everyone': ('lore_everyone_up.png', make_everyone_up),
    'timetable': ('lore_timetable.png', make_timetable),
    'tally': ('lore_tally.png', make_tally),
    'mugs': ('lore_mug_names.png', make_mug_names),
    'gauge': ('lore_gauge.png', make_gauge),
    'chevron': ('lore_chevrons.png', make_chevrons),
    'soot': ('lore_soot.png', make_soot),
}


def texture(key, force=False):
    name, fn = TEXTURES[key]
    path = os.path.join(TEX, name)
    if force or not os.path.exists(path):
        os.makedirs(TEX, exist_ok=True)
        fn(path)
    return path


def make_textures(force=False):
    for k in TEXTURES:
        texture(k, force)



# =====================================================================================================================
# Materials
# =====================================================================================================================

# New worn materials (index.html WORN): grips and handles worn bright where hands went; bails bare iron.
NEW_WORN = {
    'HandledSteel': dict(base=(0.06, 0.065, 0.06), dirt=(0.04, 0.035, 0.03), chip=(0.55, 0.53, 0.50), rough=0.55,
                         chip_rough=0.22, metallic=0.6, dust=(0.08, 0.075, 0.07), chip_scale=22.0, chip_amount=0.52,
                         grime_scale=6.0, dust_amount=0.2),
    'HandledBrass': dict(base=(0.20, 0.14, 0.06), dirt=(0.08, 0.06, 0.03), chip=(0.62, 0.46, 0.20), rough=0.5,
                         chip_rough=0.2, metallic=0.85, dust=(0.12, 0.1, 0.07), chip_scale=26.0, chip_amount=0.5,
                         grime_scale=8.0, dust_amount=0.2),
    'WornIron': dict(base=(0.045, 0.043, 0.04), dirt=(0.06, 0.035, 0.02), chip=(0.30, 0.29, 0.27), rough=0.7,
                     chip_rough=0.35, metallic=0.6, dust=(0.09, 0.085, 0.075), chip_scale=40.0, chip_amount=0.6,
                     grime_scale=9.0, dust_amount=0.4),
    'WornStrap': dict(base=(0.20, 0.17, 0.11), dirt=(0.10, 0.08, 0.05), chip=(0.32, 0.28, 0.20), rough=0.95,
                      chip_rough=0.9, metallic=0.0, dust=(0.2, 0.18, 0.14), chip_scale=50.0, chip_amount=0.7,
                      grime_scale=14.0, dust_amount=0.3),
}

# Every LeverRed slot, by object and role. The franking press's red is its hazard banding and stays.
REMAP = {
    # grips, handles, levers: worn steel with polished wear
    'LatchLever': 'HandledSteel', 'DepotCartGrip': 'HandledSteel', 'CrankWheel': 'HandledSteel',
    'TrolleyGrip': 'HandledSteel', 'StopLever': 'HandledSteel', 'PointsLever': 'HandledSteel',
    'PawlLever': 'HandledSteel', 'CagePawlLever': 'HandledSteel', 'JunctionLever': 'HandledSteel',
    'PushDuct': 'HandledSteel', 'ChildDesk': 'HandledSteel',
    # small brass fittings people pressed, posted into or wound: brass, polished by use
    'HandFrankerLever': 'HandledBrass', 'MailSlot2': 'HandledBrass', 'MailSlot6': 'HandledBrass',
    'MailSlot9': 'HandledBrass', 'ClockWinder': 'HandledBrass', 'CoinViewer': 'HandledBrass',
    'CoinViewerHead': 'HandledBrass', 'C108Bell': 'HandledBrass', 'ForwardTerminal': 'HandledBrass',
    # weights, plates and their bails: bare worn iron
    'SortWeight': 'WornIron', 'HeapWeight0': 'WornIron', 'HeapWeight1': 'WornIron', 'CwPlate0': 'WornIron',
    'CwPlate1': 'WornIron', 'CwTray': 'WornIron',
    # straps: worn webbing
    'CarryBoxStrap': 'WornStrap', 'FallenCourier': 'WornStrap',
    # read-outs, not handles: black enamel needles on cream dials; the franker's inked die
    'GateNeedle': 'GaugeNeedle', 'LiftNeedle': 'GaugeNeedle', 'HandFrankerHead': 'Rubber',
    # the points' heel goes with its yellow stand
    'PointsHeel': 'SafetyYellow',
}
KEEP_RED = ('FrankingPress', 'PressRam')


def material(name):
    """An existing material by name, or a new one for the names this module introduces."""
    from build_d17 import worn_material, simple_material, emission_material
    mt = bpy.data.materials.get(name)
    if mt is not None:
        return mt
    if name in NEW_WORN:
        return worn_material(name, **NEW_WORN[name])
    plain = {'GaugeNeedle': ((0.02, 0.018, 0.016), 0.4, 0.3), 'Rubber': ((0.012, 0.012, 0.011), 0.7, 0.0),
             'Brass': ((0.45, 0.32, 0.12), 0.45, 0.8)}
    if name in plain:
        c, r, mtl = plain[name]
        return simple_material(name, c, r, metallic=mtl)
    if name == 'TrayLamp':
        return emission_material('TrayLamp', (1.0, 0.78, 0.45), 4.0)
    worn = {  # fall-backs matching index.html's WORN table
        'BareMetal': dict(base=(0.42, 0.40, 0.35), dirt=(0.2, 0.18, 0.14), chip=(0.05, 0.045, 0.04), rough=0.5, chip_rough=0.6, metallic=0.6),
        'ToyFabric': dict(base=(0.36, 0.33, 0.30), dirt=(0.18, 0.15, 0.12), chip=(0.42, 0.40, 0.36), rough=0.95, chip_rough=0.95, metallic=0.0),
        'ToteGreen': dict(base=(0.08, 0.11, 0.09), dirt=(0.05, 0.05, 0.04), chip=(0.16, 0.18, 0.15), rough=0.7, chip_rough=0.6, metallic=0.0),
        'CastIron': dict(base=(0.035, 0.034, 0.032), dirt=(0.05, 0.03, 0.018), chip=(0.13, 0.12, 0.1), rough=0.75, chip_rough=0.45, metallic=0.5),
    }
    return worn_material(name, **worn[name])


def remap_red():
    """Reassign every LeverRed slot by role (REMAP). Returns (done, kept, unmapped) object names."""
    done, kept, unmapped = [], [], []
    for ob in list(bpy.data.objects):
        if ob.type != 'MESH':
            continue
        for slot in ob.material_slots:
            if slot.material is None or slot.material.name != 'LeverRed':
                continue
            if ob.name in REMAP:
                slot.material = material(REMAP[ob.name])
                done.append(ob.name)
            elif ob.name in KEEP_RED:
                kept.append(ob.name)
            else:
                unmapped.append(ob.name)
    return sorted(set(done)), sorted(set(kept)), sorted(set(unmapped))


def remove_curio_tags():
    gone = []
    for ob in [o for o in bpy.data.objects if o.name.startswith('CurioTag_')]:
        me = ob.data
        gone.append(ob.name)
        bpy.data.objects.remove(ob, do_unlink=True)
        if me is not None and me.users == 0:
            bpy.data.meshes.remove(me)
    return gone


def image_mat(name, key, rough=0.8, alpha=True):
    import build_d17 as d17
    mt = bpy.data.materials.get(name)
    if mt is not None:
        return mt
    mt, nt, bsdf = d17._new_material(name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(texture(key), check_existing=True)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    if alpha:
        nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
        for attr, value in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
            if hasattr(mt, attr):
                try:
                    setattr(mt, attr, value)
                except (TypeError, ValueError):
                    pass
    return mt


# =====================================================================================================================
# Placement helpers
# =====================================================================================================================

PLACED = []          # (world x, name, what) for the report


def note(name, x, what):
    PLACED.append((round(x, 2), name, what))


def wall_y(x, z, y0=-0.3, maxd=4.0, skip=()):
    """The first surface straight back from the lane (+y) at (x, z): where a decal goes."""
    dg = bpy.context.evaluated_depsgraph_get()
    origin = Vector((x, y0, z))
    for _ in range(6):
        hit, loc, nrm, idx, ob, mtx = bpy.context.scene.ray_cast(dg, origin, Vector((0, 1, 0)), distance=maxd)
        if not hit:
            return None
        if ob.name.startswith(skip) if skip else False:
            origin = loc + Vector((0, 0.002, 0))
            continue
        return loc.y
    return None


def decal(name, mat, center, size, coll, uv=((0, 0), (1, 0), (1, 1), (0, 1)), rot_y=0.0, gap=0.004, y=None):
    """A textured quad facing the camera (-y), on the wall found behind `center` (x, z) unless `y` is given."""
    cx, cz = center
    w, h = size
    if y is None:
        # Sample the wall across the decal (panels bulge), keep the hits near the median (not props in front, not
        # holes behind), and stand the decal just in front of the most forward of them.
        hits = [wall_y(cx + u * w * 0.4, cz + v * h * 0.4) for u in (-1, 0, 1) for v in (-1, 0, 1)]
        hits = sorted(t for t in hits if t is not None)
        if not hits:
            print('lore: no wall behind', name, cx, cz)
            return None
        med = hits[len(hits) // 2]
        y = min(t for t in hits if med - 0.1 <= t <= med + 0.02) - gap
    r = Matrix.Rotation(rot_y, 3, 'Y')
    pts = [Vector((cx, y, cz)) + r @ Vector(p) for p in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    f = bm.faces.new([bm.verts.new(p) for p in pts])
    for lp, t in zip(f.loops, uv):
        lp[uvl].uv = t
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def solid(name, build, mats, coll, sharp=35):
    """A mesh built by `build(bm)` from the d17 primitives."""
    import build_d17 as d17
    bm = bmesh.new()
    build(bm)
    return d17.mesh_object(name, bm, [material(m) if isinstance(m, str) else m for m in mats], coll, sharp=sharp)


# =====================================================================================================================
# The scenes
# =====================================================================================================================

def dress_dl01(coll):
    from build_d17 import add_box, add_cyl
    decal('LoreGradeChart', image_mat('LoreGradeChartMat', 'chart'), (10.42, 1.97), (1.78, 1.224), coll)
    note('LoreGradeChart', 10.42, 'DL-01 painted grade chart on the bulkhead over the exit door (GRADE 4 · LABOUR at the bottom)')
    decal('LoreRoster', image_mat('LoreRosterMat', 'roster'), (1.655, 1.3), (0.26, 0.347), coll, rot_y=math.radians(3))
    note('LoreRoster', 1.66, 'DL-01 torn NIGHT SHIFT roster, names struck out (IVO and D-17 left), beside the dispatch board')
    decal('LoreTally01', image_mat('LoreTallyMat', 'tally'), (1.66, 0.86), (0.24, 0.24), coll)
    note('LoreTally01', 1.66, 'DL-01 chalk tallies under the roster')

    def cot(bm):                           # a camp cot in the hall behind, a blanket on it, tins and a crate by it
        x0, x1, y0, y1, top = 3.6, 5.4, 2.75, 3.4, 0.38
        add_box(bm, ((x0 + x1) / 2, (y0 + y1) / 2, top - 0.02), (x1 - x0, y1 - y0, 0.03), mat=1)
        for x in (x0 + 0.05, x1 - 0.05):
            for y in (y0 + 0.04, y1 - 0.04):
                add_box(bm, (x, y, (top - 0.03) / 2), (0.03, 0.03, top - 0.03), mat=0)
        for y in (y0 + 0.03, y1 - 0.03):
            add_cyl(bm, (x0, y, top - 0.02), (x1, y, top - 0.02), 0.02, seg=8, mat=0)
        add_box(bm, (x0 + 1.05, (y0 + y1) / 2 - 0.02, top + 0.05), (1.3, y1 - y0 + 0.06, 0.09), mat=2,
                rot=Matrix.Rotation(0.06, 4, 'Z'))                                   # the blanket, rucked
        add_box(bm, (x0 + 0.2, (y0 + y1) / 2, top + 0.06), (0.3, 0.45, 0.1), mat=2)  # a rolled coat for a pillow
        add_box(bm, (x1 + 0.3, 3.0, 0.2), (0.4, 0.34, 0.4), mat=3)                    # a crate for a table
        for k, (x, y, h) in enumerate(((x1 + 0.22, 2.95, 0.12), (x1 + 0.38, 3.06, 0.1), (x1 + 0.12, 3.12, 0.12))):
            add_cyl(bm, (x, y, 0.4), (x, y, 0.4 + h), 0.045, seg=12, mat=4)       # ration tins
        add_cyl(bm, (x1 + 0.6, 2.9, 0.0), (x1 + 0.6, 2.9, 0.11), 0.05, seg=12, mat=4)   # one on the floor, opened
    solid('LoreCot01', cot, ['DepotSteel', 'ToteGreen', 'ToyFabric', 'CrateWood', 'BareMetal'], coll)
    note('LoreCot01', 4.5, 'DL-01 a camp cot with a blanket, a crate and ration tins in the hall behind (y 2.75 to 3.4)')

    def patch(bm):                         # a plate bolted over a hole low on the bulkhead
        y = (wall_y(11.45, 0.5) or 0.62) - 0.008
        add_box(bm, (11.45, y, 0.5), (0.34, 0.012, 0.26), mat=0, rot=Matrix.Rotation(0.05, 4, 'Y'))
        for dx in (-0.14, 0.14):
            for dz in (-0.1, 0.1):
                add_cyl(bm, (11.45 + dx, y - 0.006, 0.5 + dz), (11.45 + dx, y - 0.014, 0.5 + dz), 0.012, seg=6, mat=1)
    solid('LorePatch01', patch, ['DepotSteel', 'CastIron'], coll)
    note('LorePatch01', 11.45, 'DL-01 a plate bolted over a hole in the bulkhead, right of the door')


def dress_dl02(coll):
    from build_d17 import add_box, add_cyl
    y = wall_y(17.86, 1.7)
    board = image_mat('LoreNoticesMat', 'notices', alpha=False)
    decal('LoreNoticeBoard', board, (17.86, 1.7), (0.84, 0.7), coll, y=y - 0.03)
    solid('LoreNoticeFrame', lambda bm: add_box(bm, (17.86, y - 0.012, 1.7), (0.9, 0.024, 0.76), mat=0), ['CrateWood'], coll)
    note('LoreNoticeBoard', 17.86, 'DL-02 notice board: NIGHT SHIFT CUT and GRADE 3 TRANSFERS SUSPENDED (an up arrow crossed out)')
    # The night shift's names on the hanging mugs (art/sorting_hall TeaMugs: hooks at a0 + 0.2 + k * 0.17, k = 3 empty).
    a0, ay = 15.35, 1.7
    mat = image_mat('LoreMugNamesMat', 'mugs', rough=0.35)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    for row, k in enumerate((0, 1, 2, 4)):
        cx, cy, r = a0 + 0.2 + k * 0.17, ay - 0.06, 0.035 * 1.03
        n = 8
        for i in range(n):
            a0_, a1_ = math.radians(-150 + 120 * i / n), math.radians(-150 + 120 * (i + 1) / n)   # the front, round -y
            pts = [Vector((cx + r * math.cos(a), cy + r * math.sin(a), z)) for a, z in ((a0_, 1.145), (a1_, 1.145), (a1_, 1.205), (a0_, 1.205))]
            f = bm.faces.new([bm.verts.new(p) for p in pts])
            v0, v1 = 1 - (row + 1) / 4, 1 - row / 4
            for lp, t in zip(f.loops, ((0.75 * i / n, v0), (0.75 * (i + 1) / n, v0), (0.75 * (i + 1) / n, v1), (0.75 * i / n, v1))):
                lp[uvl].uv = t
    me = bpy.data.meshes.new('LoreMugNames')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    coll.objects.link(bpy.data.objects.new('LoreMugNames', me))
    note('LoreMugNames', 15.89, 'DL-02 names on the hanging mugs: ODA, TOMAS, IVO (with a crooked tree; x 15.89), RUTH; D-17\'s mug untouched')

    def bedroll(bm):
        add_cyl(bm, (16.82, 1.5, 0.08), (17.22, 1.5, 0.08), 0.08, seg=14, mat=0)
        add_cyl(bm, (16.9, 1.5, 0.08), (16.9, 1.5, 0.08), 0.0815, seg=14, mat=1)
        add_cyl(bm, (17.12, 1.42, 0.0), (17.12, 1.42, 0.1), 0.04, seg=12, mat=2)
    solid('LoreBedroll02', bedroll, ['ToyFabric', 'WornStrap', 'BareMetal'], coll)
    note('LoreBedroll02', 17.0, 'DL-02 a bedroll and a ration tin in the tea corner (y 1.5)')


def dress_dl03(coll):
    from PIL import Image
    w, h = Image.open(texture('keep')).size
    decal('LoreStencilKeep', image_mat('LoreStencilKeepMat', 'keep'), (27.75, 2.12), (0.3 * w / h, 0.3), coll)
    note('LoreStencilKeep', 27.75, 'DL-03 stencil WE KEEP YOU ALIVE across the weighing room wall (z 2.12)')
    mat = image_mat('LoreProtestMat', 'protest', rough=0.85)
    y = wall_y(28.2, 1.2)
    decal('LoreProtest', mat, (28.2, 1.2), (0.4, 0.533), coll, uv=((0, 0), (0.5, 0), (0.5, 1), (0, 1)), y=y - 0.004)
    # The torn-off flap hangs from the tear, upside down and peeling off the wall.
    ob = decal('LoreProtestFlap', mat, (28.38, 0.8), (0.4, 0.533), coll, uv=((1, 1), (0.5, 1), (0.5, 0), (1, 0)),
               rot_y=math.radians(-12), y=y - 0.03)
    note('LoreProtest', 28.2, 'DL-03 protest poster WHO CARRIES WHOM? (a sorter holding up the domes), half torn down, its flap hanging')

    def patch(bm):
        from build_d17 import add_box, add_cyl
        yy = (wall_y(25.95, 0.95) or 0.61) - 0.008
        add_box(bm, (25.95, yy, 0.95), (0.3, 0.012, 0.36), mat=0, rot=Matrix.Rotation(-0.04, 4, 'Y'))
        for dx in (-0.12, 0.12):
            for dz in (-0.15, 0.15):
                add_cyl(bm, (25.95 + dx, yy - 0.006, 0.95 + dz), (25.95 + dx, yy - 0.014, 0.95 + dz), 0.011, seg=6, mat=1)
    solid('LorePatch03', patch, ['ShutterSteel', 'CastIron'], coll)
    decal('LoreSoot03', image_mat('LoreSootMat', 'soot'), (25.95, 1.45), (0.42, 0.75), coll, y=(wall_y(25.95, 1.45, y0=0.3) or 0.61) - 0.003)
    note('LorePatch03', 25.95, 'DL-03 a plate bolted over a burnt hole in the wall, soot (LoreSoot03) up the wall above it')


def dress_dl04(coll):
    from build_d17 import add_box, add_cyl
    y = (wall_y(41.1, 1.3) or 1.07) - 0.012
    x0, x1, z = 40.93, 41.27, 1.42

    def memorial(bm):
        pts = [Vector((x0 + (x1 - x0) * t, y, z - 0.035 * math.sin(math.pi * t))) for t in [k / 8 for k in range(9)]]
        for a, b in zip(pts, pts[1:]):
            add_cyl(bm, a, b, 0.0015, seg=4, mat=1)
        for x in (x0, x1):
            add_cyl(bm, (x, y + 0.01, z), (x, y - 0.005, z), 0.004, seg=6, mat=1)
        rnd = random.Random(4)
        for k in range(6):                                  # couriers' tags, each on a twist of wire
            t = (k + 0.7) / 7
            p = Vector((x0 + (x1 - x0) * t, y - 0.002, z - 0.035 * math.sin(math.pi * t)))
            add_cyl(bm, p, p + Vector((0, 0, -0.02)), 0.001, seg=4, mat=1)
            add_box(bm, p + Vector((0, 0, -0.045)), (0.032, 0.003, 0.045), mat=0,
                    rot=Matrix.Rotation(rnd.uniform(-0.25, 0.25), 4, 'Y'))
    solid('LoreMemorial', memorial, ['ReflectTag', 'Copper'], coll)
    note('LoreMemorial', 41.1, 'DL-04 couriers\' tags on a wire over the empty rack with the chalk flowers (z 1.42)')


def dress_dl06(coll):
    from build_d17 import add_box, add_cyl
    wy = wall_y(65.3, 0.6) or 1.56

    def barricade(bm):
        rnd = random.Random(66)
        crates = [(64.85, 0.0, 0), (65.38, 0.0, 0), (65.12, 0.36, 0), (65.9, 0.0, 1)]
        for x, z, kind in crates:                           # sorting crates pushed back against the wall
            add_box(bm, (x, wy - 0.24, z + 0.18), (0.5, 0.44, 0.36), mat=kind,
                    rot=Matrix.Rotation(rnd.uniform(-0.06, 0.06), 4, 'Z'))
        add_box(bm, (66.25, wy - 0.3, 0.25), (0.5, 0.44, 0.28), mat=0,                 # one on its end
                rot=Matrix.Rotation(math.radians(80), 4, 'Y') @ Matrix.Rotation(0.2, 4, 'X'))
        for k in range(5):                                  # the planks that were nailed across, pulled off
            add_box(bm, (64.7 + k * 0.2, wy - 0.06 - 0.03 * k, 0.5 + 0.08 * k), (0.08, 0.025, 1.0), mat=1,
                    rot=Matrix.Rotation(math.radians(12 + 6 * k), 4, 'Y'))
        add_box(bm, (65.0, wy - 0.5, 0.01), (1.4, 0.06, 0.02), mat=2,                  # a strip of hazard tape
                rot=Matrix.Rotation(0.3, 4, 'Z'))
    solid('LoreBarricade', barricade, ['ToteGreen', 'CrateWood', 'SafetyYellow'], coll)
    note('LoreBarricade', 65.4, 'DL-06 the dismantled barricade: sorting crates and pulled planks against the wall, behind the belt (y >= 0.9)')
    decal('LoreUpStencil', image_mat('LoreUpStencilMat', 'upstencil'), (68.3, 1.85), (1.8, 0.9), coll)
    note('LoreUpStencil', 68.3, 'DL-06 UP IS FOR THEM stencil, rollered grey, EVERYONE UP painted over it with an arrow')


def dress_dl07(coll):
    # Pass 5 (docs/chapter1_pass5_plan.md, section 3): EVERYONE UP is not repeated here; it stays on DL-06's stencil
    # (LoreUpStencil) and C-106's wall in ring C. make_everyone_up() is kept for the atlas's history only.
    pass


def dress_dl08(coll):
    from build_d17 import add_box, add_cyl, add_torus
    decal('LoreTimetable', image_mat('LoreTimetableMat', 'timetable', rough=0.85), (92.5, 2.6), (0.5, 0.6875), coll)
    note('LoreTimetable', 92.5, 'DL-08 RELOCATION · LIFT 1 · UP timetable, every departure struck through, LAST ringed')
    decal('LoreTally08', image_mat('LoreTallyMat', 'tally'), (93.12, 2.5), (0.36, 0.36), coll)
    note('LoreTally08', 93.12, 'DL-08 chalk tallies beside the timetable')
    wy = wall_y(89.35, 2.0) or 1.78

    def stove(bm):
        add_cyl(bm, (89.35, wy - 0.2, 1.6), (89.35, wy - 0.2, 1.84), 0.12, 0.1, seg=16, mat=0)
        add_torus(bm, (89.35, wy - 0.2, 1.85), (0, 0, 1), 0.08, 0.01, seg=14, rseg=4, mat=0)
        add_cyl(bm, (89.35, wy - 0.2, 1.86), (89.35, wy - 0.2, 1.94), 0.09, seg=16, mat=1)      # a pan
        add_cyl(bm, (89.44, wy - 0.2, 1.92), (89.6, wy - 0.24, 1.93), 0.008, seg=6, mat=1)
        for k, (x, h) in enumerate(((89.12, 0.11), (89.04, 0.09), (89.6, 0.12))):
            add_cyl(bm, (x, wy - 0.12 - 0.05 * k, 1.6), (x, wy - 0.12 - 0.05 * k, 1.6 + h), 0.04, seg=12, mat=1)
        add_box(bm, (89.3, wy - 0.06, 1.62), (0.5, 0.1, 0.04), mat=2)                   # a folded blanket
    solid('LoreStove08', stove, ['CastIron', 'BareMetal', 'ToyFabric'], coll)
    decal('LoreSoot08', image_mat('LoreSootMat', 'soot'), (89.35, 2.3), (0.45, 0.8), coll)
    note('LoreStove08', 89.35, 'DL-08 a stove with a pan, ration tins and a blanket by the broom, soot up the wall')


def dress_dl09(coll):
    from build_d17 import add_box, add_cyl, add_torus
    wy = wall_y(104.0, 1.9) or 1.46

    def belongings(bm):
        c = Vector((103.75, wy - 0.06, 1.6 + 0.2))
        add_torus(bm, c, (0, 1, 0), 0.18, 0.016, seg=24, rseg=6, mat=0)                 # a pram wheel, leaning
        for k in range(8):
            a = k * math.pi / 8
            add_cyl(bm, c + Vector((0.17 * math.cos(a), 0, 0.17 * math.sin(a))),
                    c - Vector((0.17 * math.cos(a), 0, 0.17 * math.sin(a))), 0.003, seg=4, mat=1)
        add_cyl(bm, c + Vector((0, -0.03, 0)), c + Vector((0, 0.03, 0)), 0.03, seg=10, mat=1)
        b = Vector((104.12, wy - 0.22, 1.6))                                              # a bundle tied up in a cloth
        from build_d17 import add_sphere
        add_sphere(bm, b + Vector((0, 0, 0.14)), 0.17, seg=14, scale=(1.2, 0.9, 0.85), mat=2)
        add_sphere(bm, b + Vector((0.02, 0, 0.3)), 0.05, seg=10, mat=2)                 # its knot
        add_torus(bm, b + Vector((0, 0, 0.16)), (0, 0, 1), 0.17, 0.008, seg=20, rseg=4, mat=3)
        add_box(bm, (104.38, wy - 0.12, 1.66), (0.12, 0.08, 0.12), mat=4)               # a child's shoe box
    solid('LoreBelongings', belongings, ['Rubber', 'BareMetal', 'ToyFabric', 'WornStrap', 'ParcelBrown'], coll)
    note('LoreBelongings', 103.95, 'DL-09 a pram wheel and a tied bundle left at the lower landing, against the back wall')


# =====================================================================================================================
# The cage (DL-09): the balance gauge, the tray lamp, the landing chevrons
# =====================================================================================================================

GAUGE = (100.3, 0.5, 3.4)            # the post's foot: x, y, the upper landing's top
GAUGE_C = (100.3, 0.452, 4.38)       # the dial's centre (its face toward -y)
GAUGE_R = 0.14
NEEDLE = {'too light': 48.0, 'one plate': 24.0, 'balanced': 0.0}   # degrees about Blender +Y (game: rotation.z = -this)


def build_gauge(coll):
    from build_d17 import add_box, add_cyl, add_torus
    x, y, z0 = GAUGE
    cx, cy, cz = GAUGE_C

    def post(bm):
        add_box(bm, (x, y, z0 + 0.01), (0.16, 0.16, 0.02), mat=0)
        add_box(bm, (x, y + 0.02, (z0 + cz - GAUGE_R) / 2), (0.05, 0.05, cz - GAUGE_R - z0), mat=0)
        add_cyl(bm, (cx, cy + 0.07, cz), (cx, cy - 0.005, cz), GAUGE_R + 0.025, seg=28, mat=1)     # the case
        add_torus(bm, (cx, cy - 0.006, cz), (0, 1, 0), GAUGE_R + 0.012, 0.012, seg=28, rseg=6, mat=2)   # its bezel
        add_cyl(bm, (cx, cy + 0.07, cz + GAUGE_R + 0.02), (x, y + 0.02, 6.0), 0.008, seg=6, mat=3)       # conduit up
    solid('BalanceGauge', post, ['DepotGreen', 'DepotSteel', 'HandledBrass', 'Rubber'], coll)
    face = image_mat('BalanceGaugeMat', 'gauge', rough=0.4, alpha=False)
    n = 32
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    rr = GAUGE_R + 0.005
    c0 = bm.verts.new((cx, cy - 0.008, cz))
    ring = [bm.verts.new((cx + rr * math.cos(2 * math.pi * k / n), cy - 0.008, cz + rr * math.sin(2 * math.pi * k / n))) for k in range(n)]
    for k in range(n):
        a, b = ring[k], ring[(k + 1) % n]
        f = bm.faces.new((c0, a, b))                       # wound to face -y
        for lp in f.loops:
            p = lp.vert.co
            lp[uvl].uv = (0.5 + (p.x - cx) / (2 * rr) * (rr / (rr + 0.0)) * 0.94, 0.5 + (p.z - cz) / (2 * rr) * 0.94)
    me = bpy.data.meshes.new('BalanceGaugeFace')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(face)
    coll.objects.link(bpy.data.objects.new('BalanceGaugeFace', me))
    # The needle: modelled pointing up from its pivot (the dial's centre, its origin), with a short tail.
    bm = bmesh.new()
    add_box(bm, (0, 0, 0.055), (0.012, 0.004, 0.11), mat=0)
    add_box(bm, (0, 0, 0.112), (0.02, 0.004, 0.02), mat=0, rot=Matrix.Rotation(math.radians(45), 4, 'Y'))
    add_box(bm, (0, 0, -0.025), (0.02, 0.004, 0.05), mat=0)
    add_cyl(bm, (0, -0.004, 0), (0, 0.004, 0), 0.016, seg=14, mat=1)
    import build_d17 as d17
    nd = d17.mesh_object('BalanceNeedle', bm, [material('GaugeNeedle'), material('HandledBrass')], coll)
    nd.location = (cx, cy - 0.016, cz)
    nd.rotation_euler = (0, math.radians(NEEDLE['too light']), 0)
    note('BalanceGauge', 100.3, 'DL-09 balance gauge on a post at the top landing\'s left end; BalanceNeedle pivot at (100.3, 0.436, 4.38) Blender')


def build_tray_lamp(coll):
    from build_d17 import add_box, add_cyl, add_sphere
    cw = bpy.data.objects.get('CageCounterweight')
    tray = bpy.data.objects.get('CwTray')
    bpy.context.view_layer.update()
    if tray is not None:
        bb = [tray.matrix_world @ Vector(c) for c in tray.bound_box]
        tx, ttop = sum(v.x for v in bb) / 8, max(v.z for v in bb)
    else:
        tx, ttop = (cw.matrix_world.translation.x if cw else 101.45), 3.81
    back = (wall_y(tx, ttop + 0.5, y0=0.95) or 1.05)
    lz = ttop + 0.48
    ly = 0.995

    def shade(bm):
        add_box(bm, (tx, (back + ly) / 2 + 0.01, lz + 0.09), (0.03, back - ly + 0.02, 0.025), mat=0)   # the bracket
        add_cyl(bm, (tx, ly, lz + 0.09), (tx, ly, lz + 0.03), 0.012, 0.055, seg=14, mat=0)             # the shade
        for k in range(4):                                                                              # its guard
            a = k * math.pi / 4
            add_cyl(bm, (tx + 0.04 * math.cos(a), ly + 0.04 * math.sin(a), lz + 0.03),
                    (tx - 0.04 * math.cos(a), ly - 0.04 * math.sin(a), lz - 0.04), 0.002, seg=4, mat=0)
    solid('TrayLampShade', shade, ['DepotSteel'], coll)
    bm = bmesh.new()
    add_sphere(bm, (tx, ly, lz + 0.015), 0.022, seg=12)
    import build_d17 as d17
    d17.mesh_object('TrayLamp', bm, [material('TrayLamp')], coll)
    note('TrayLamp', tx, f'DL-09 warm lamp over the counterweight tray at its start height (bulb at z {lz + 0.015:.2f}, y {ly})')


def build_chevrons(coll):
    mat = image_mat('LoreChevronMat', 'chevron', rough=0.7)
    z = 1.6
    for name, x, uv in (('LoreChevronL', 101.33, ((0, 0), (1, 0), (1, 1), (0, 1))),
                        ('LoreChevronR', 102.68, ((1, 0), (0, 0), (0, 1), (1, 1)))):
        y = wall_y(x, z, y0=0.75)
        decal(name, mat, (x, z), (0.16, 0.16), coll, uv=uv, y=(y or 1.05) - 0.004)
    note('LoreChevrons', 102.0, 'DL-09 white chevrons on the shaft back wall at the lit landing (z 1.6), x 101.33 and 102.68')
    cage = bpy.data.objects.get('Cage')
    if cage is not None:
        ob = decal('CageMarker', mat, (0.0, 0.0), (0.07, 0.07), coll, y=0.0)
        me = ob.data
        for v in me.vertices:                              # into cage-local space: the right front post, floor level
            v.co = Vector((0.72 + v.co.x, -0.603, v.co.z))
        ob.parent = cage
        ob.matrix_parent_inverse = Matrix.Identity(4)
        ob.location = (0, 0, 0)
        note('CageMarker', 102.72, 'DL-09 white chevron on the cage\'s right front post at its floor (child of Cage)')


# =====================================================================================================================
# build_set
# =====================================================================================================================

def build_set(dl01, m, coll):
    PLACED.clear()
    make_textures()
    bpy.context.view_layer.update()
    gone = remove_curio_tags()
    done, kept, unmapped = remap_red()
    print('lore: curio tags removed:', ', '.join(gone))
    print('lore: LeverRed remapped on:', ', '.join(done))
    print('lore: LeverRed kept (hazard) on:', ', '.join(kept))
    if unmapped:
        print('lore: WARNING LeverRed still on (no role given):', ', '.join(unmapped))
    dress_dl01(coll)
    dress_dl02(coll)
    dress_dl03(coll)
    dress_dl04(coll)
    dress_dl06(coll)
    dress_dl07(coll)
    dress_dl08(coll)
    dress_dl09(coll)
    build_gauge(coll)
    build_tray_lamp(coll)
    build_chevrons(coll)
    for x, n, what in sorted(PLACED):
        print(f'lore: x {x:7.2f}  {n}: {what}')
    # D-17's clips for the cage: build_dl01.main() calls cage.add_clips but not this module's add_clips, so chain
    # ours after the cage's (once; a later direct call is a no-op).
    cage_mod = getattr(dl01, 'cage', None)
    if cage_mod is not None and not getattr(cage_mod.add_clips, '_lore', False):
        orig = cage_mod.add_clips

        def chained(d, arm):
            orig(d, arm)
            add_clips(d, arm)
        chained._lore = True
        cage_mod.add_clips = chained


# =====================================================================================================================
# D-17's clips: CageRideLever (loops) and CagePullPawl
#
# Authored in stand space at RIDE_STAND (the rig as the game places it: facing +x in the world, which is -Y in rig
# space; rig +X is his left, world +y). The cage's lever (art/cage: pivot at cage-local (-0.6, 0.3, 0), leaning 10
# degrees toward -x, thrown 55 degrees about +Y) is then 0.12 m behind him and 0.3 m to his left: his left claw
# holds its shaft at GRIP_H up from the pivot; his right claw holds the near side rail. The game's braceX should be
# RIDE_STAND (cage-local -0.48, world 101.52; OFF3 + 68.52) for these, instead of 102.2.
# =====================================================================================================================

RIDE_LOCAL_X = -0.48                 # cage-local x of his root (the cage's centre is world 102.0)
LEVER = dict(pivot=(-0.6, 0.3, 0.0), rest=-10.0, throw=55.0)
GRIP_H = 0.26                        # where his claw holds the shaft, up from the pivot
RAIL = (-0.34, 0.11)                 # the near side rail: cage-local y, height above the floor
RAIL_GRIP_X = -0.26                  # where his right claw holds it (cage-local x; the rail starts at -0.3)
RIDE_FRAMES, PULL_FRAMES = 48, 18
PULL_KEYS = ((0, 0.0), (3, 0.0), (9, 1.0), (11, 1.04), (14, 1.0), (18, 1.0))   # lever throw fraction by frame


def _rig(p):
    """Cage-local (x, y, z) to stand space (rig armature space)."""
    return Vector((p[1], -(p[0] - RIDE_LOCAL_X), p[2]))


def lever_grip(k, h=GRIP_H):
    """The point on the lever's shaft at height h when it is thrown by fraction k (rig space), and its up dir."""
    a = math.radians(LEVER['rest'] + LEVER['throw'] * k)
    up = Vector((math.sin(a), 0, math.cos(a)))
    return _rig(Vector(LEVER['pivot']) + up * h), Vector((0, -up.x, up.z)), a


def _ride_pose(c, frame, f, dl01, k=0.0, effort=0.0, look=0.0, settle=0.0, cyc=0.0):
    import build_dl02
    tau = 2 * math.pi
    breathe = math.sin(tau * cyc)
    body = (0.0, -0.01 * effort, -0.075 - 0.012 * effort + 0.004 * breathe)
    rot = (7 + 5 * effort + 0.8 * breathe, -3 - 2 * effort, 8 + 6 * effort)
    grip, up, a = lever_grip(k)
    targets = {1: grip + up * 0.07, -1: _rig((RAIL_GRIP_X, RAIL[0] + 0.015, RAIL[1] + 0.063))}
    hands = build_dl02.reach(targets, body, rot, dl01.REST_WRIST)
    # Looking down the shaft: the head pitched down over the cage's edge, turned a little toward the camera; `look`
    # turns it to the lever (a glance down at his own claw).
    head = (24 - rot[0] + 6 * settle + 3 * math.sin(tau * cyc + 1.0) - 14 * look,
            -rot[1] * 0.5 + 2 * math.sin(tau * cyc),
            -rot[2] - 14 + 50 * look + 3 * math.sin(tau * cyc + 2.0))
    antenna = [(-18 + 4 * math.sin(tau * cyc - i * 0.8) + 10 * effort, 2 * math.sin(tau * cyc - i)) for i in range(3)]
    c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands,
           hand_rot={'L': (math.degrees(a) - 10, 0, 18), 'R': (-70, 0, -10)},
           claws={'L': 3 - 2 * effort, 'R': 3 - 2 * effort}, elbows={'L': 0.3, 'R': 1})


def clip_cage_ride_lever(dl01, arm):
    """Riding the cage: crouched and braced, his left claw on the pawl lever behind him, his right on the near
    rail, looking down the shaft for the lit landing; halfway through a glance down at the lever. Loops."""
    c = dl01.Clip(arm, 'CageRideLever', RIDE_FRAMES)
    for frame in range(1, RIDE_FRAMES + 2):
        f = frame - 1
        t = f / RIDE_FRAMES
        look = max(0.0, math.sin(math.pi * (t - 0.45) / 0.3)) if 0.45 <= t <= 0.75 else 0.0
        _ride_pose(c, frame, f, dl01, look=look ** 1.5, cyc=t)
    c.done()


def clip_cage_pull_pawl(dl01, arm):
    """The pull: a beat to brace (frames 0 to 3), then a firm pull of the lever forward through its 55 degrees
    (3 to 9, a small overshoot to 11), his body driving into it; he holds it thrown and looks down at the pawl."""
    c = dl01.Clip(arm, 'CagePullPawl', PULL_FRAMES)
    for frame in range(1, PULL_FRAMES + 1):
        f = frame - 1
        k = dl01.track(list(PULL_KEYS), f)
        effort = dl01.track([(0, 0.0), (3, 0.6), (7, 1.0), (11, 0.8), (18, 0.3)], f)
        settle = dl01.track([(0, 0.0), (9, 0.0), (13, 1.0), (18, 0.6)], f)
        _ride_pose(c, frame, f, dl01, k=k, effort=effort, settle=settle, cyc=0.0)
    c.done()


def add_clips(dl01, arm):
    ad = arm.animation_data
    if ad is not None and any(t.name == 'CageRideLever' for t in ad.nla_tracks):
        return
    clip_cage_ride_lever(dl01, arm)
    clip_cage_pull_pawl(dl01, arm)

if __name__ == '__main__':
    make_textures(force=True)
    for k, (n, _) in TEXTURES.items():
        print(f'{os.path.getsize(os.path.join(TEX, n)) / 1024:7.1f} KB  {n}')
