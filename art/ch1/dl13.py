"""DL-13 The Repeated Lesson (game x 216.0 to 232.0): the classroom, the lesson apparatus, the gallery.

Design: docs/chapter1_attendance_plan.md (DL-13), docs/audio_audit.md (att_lesson from the apparatus's horn).
Called by art/ch1/build_attendance.py as build_set(dl01, m, coll), in final world coordinates.

Blender (x, y, z) -> game (x, z, -y). The lane is y = 0, the floor z = 0, the camera at -y.

The room, left to right:
  216.0-217.0  the door in from DL-12's corridor (a door frame across the lane; the leaf stands open into the room)
  217.2-218.0  the rack of teaching figures, two chained in, a slot empty; AttFigure2 free on the lane at 217.6
  216.4-220.1  behind the lane (y 0.9 to 3.8), rows of small desks; jointed wooden figures sit in most of them
  219.2-219.9  the front seat on the lane: the pupil pad on the floor (219.18-219.5), the desk (219.5-219.9, top 0.52)
               with the LESSON lamp (AttLessonLamp) on a stalk; its chair pushed back off the lane
  220.4-227.55 the lesson apparatus against the front wall (its face at y 0.9): the clockwork tower and the horn
               speaker (220.4-222.0), the pawl brake AttPawl on its base at 220.6, the rod along the floor to the cycle
               dial at 224.0 (height 1.4, AttDialHand), the three hinged steps AttStep1-3 and their slots
  222.0-228.0  the model tree's glass case (height 2.6-3.6) over the steps, its parts AttTree*
  227.6-232.0  the gallery at 2.05 (solid beneath), its rail on the camera side, the seedling tray behind glass
               (AttShoot, the one living shoot), the door out at 230.6 into DL-14

Moving parts (origins at their pivots, final world coordinates):
  AttFigure2       origin on the floor under its centre; faces +x. Pushable (half-width 0.22, height 0.95).
  AttStep1..3      hinged on the wall at the board's bottom back edge (y 0.9). Built OUT (horizontal, rotation 0);
                   rotation about x of -90 deg folds each up flat into its slot in the apparatus face.
  AttPawl          the red brake lever; pivot at its foot. Built released (leaning 20 deg back, toward the wall);
                   +40 deg about x throws it (it leans 20 deg toward the camera).
  AttDialHand      the dial's hand; origin on the dial's spindle. Built pointing straight up (t = 0, the bell).
                   It turns clockwise as the camera sees it: Blender rotation about +y of +t/12 * 360 deg
                   (game: about +z by -t/12 * 360 deg).
  AttLessonLamp    the LESSON lamp's glass (emissive material AttLessonLamp, off as built).
  AttTreeTrunk, AttTreeBranch1..3, AttTreeLeaves   the model tree; origins at their attachment points, scaled 0 -> 1.
  AttShoot         the pale living shoot in the seedling tray (static; its own object so the game can light it).
  AttLessonSpeaker an empty at the horn's mouth: the emitter for att_lesson.
"""
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Euler, Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
COMMON = os.path.join(HERE, '..', 'common')
FONT = '/usr/share/fonts/truetype/crosextra/Carlito-Bold.ttf'

# --------------------------------------------------------------------------------------------------------------------
# The layout (the design's numbers: the game codes against them)
# --------------------------------------------------------------------------------------------------------------------
X0, X1 = 216.0, 232.0
CEIL = 4.3                          # the classroom's ceiling (the case reaches 3.6 and the gallery door 3.98)
FRONT_Y = -0.6                      # the cut toward the camera: the ceiling stops here
LINTEL_Y = -0.5                     # the door lintels stop here (nothing stands in front of the lane but the low rail)
ALCOVE = (216.15, 220.4)            # where the desks are, the room runs back to ALCOVE_Y
ALCOVE_Y = 4.0
BACK_Y = 1.6                        # the wall behind the apparatus and the gallery
FACE_Y = 0.9                        # the apparatus's face: the steps' hinge line
DOOR_IN = (216.0, 216.15, 2.1)      # the cross wall at the scene's left edge: x0, x1, the door's height
FIG2_X = 217.6
RACK = (217.2, 218.0, 0.6, 1.3)
PAD = (219.18, 219.5)               # the pupil pad, flush in the floor
DESK = (219.5, 219.9, 0.52)         # the front seat's desk: x0, x1, top
SEATED_X = 219.40                   # AttFigure2's origin when it is in the front seat (its stand's nose under the desk)
LAMP = (219.84, 0.12, 1.0)          # the LESSON lamp's glass
PAWL = (220.6, 0.45, 0.2)           # the brake lever's pivot
PAWL_LEN, PAWL_REST = 0.5, -20.0    # rest: leaning back 20 degrees (top toward +y)
DIAL = (224.0, 0.85, 1.4)           # the dial's spindle (its face at y 0.87)
DIAL_R = 0.3
STEPS = ((224.6, 225.4, 0.55), (225.6, 226.4, 1.05), (226.6, 227.4, 1.55))
STEP_T = 0.06
STEP_Y = (-0.3, 0.9)
APP_X = (220.4, 227.6)
CASE = (222.0, 228.0, 2.6, 3.6)
CASE_Y = (1.0, 1.55)
TREE = (225.0, 1.27, 2.78)          # the trunk's foot in the case
GALLERY = (227.6, 232.0, 2.05)
DOOR_OUT = 230.6
DOOR_OUT_H = 1.85
VEST = (230.7, 0.9, 3.95)           # past the door out: DL-14's back wall face (y) and ceiling, so the seam at 232 meets
GAL_FRONT = -0.5                    # the gallery's front face (DL-14's landing front is at -0.47)
RAIL_Y = -0.44
SHOOT = (229.42, 1.16)

# The cycle dial (12 s a lesson): the steps out at 1.0, 2.6, 4.2 s; all out 4.2-5.6 s (the red sector).
CYCLE = 12.0
MARKS = (1.0, 2.6, 4.2)             # each step out (the game's ATT.cycle.out) ...
FOLDS = (5.6, 6.2, 6.8)             # ... and folded again (ATT.cycle.fold)
RED = (4.2, 5.6)                    # all three out: the useful window; its middle (4.9 s) is the brake's chevron
TREE_T = (6.8, 10.4)                # the model tree grows

# The seated figures are linked duplicates of one mesh (LessonFigureSeated), as asked: 10 objects, 2 draw calls each
# unless the game instances them. True merges them into AttLessonRoom instead (one more material there, 19 fewer calls).
MERGE_SEATED = True

I4 = Matrix.Identity(4)


def _rz(a):
    return Matrix.Rotation(a, 4, 'Z')


def _rx(a):
    return Matrix.Rotation(a, 4, 'X')


def _ry(a):
    return Matrix.Rotation(a, 4, 'Y')


# --------------------------------------------------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------------------------------------------------
# New (game WORN / EMIT entries are in the report):
NEW_WORN = {
    'LessonPlaster': dict(base=(0.27, 0.25, 0.2), dirt=(0.14, 0.12, 0.09), chip=(0.17, 0.15, 0.12), rough=0.9,
                          chip_rough=0.85, metallic=0.0, grime_scale=3.0, chip_scale=18.0, chip_amount=0.7, streaks=0.6),
    'LessonDado': dict(base=(0.13, 0.19, 0.15), dirt=(0.07, 0.09, 0.07), chip=(0.25, 0.23, 0.19), rough=0.75,
                       chip_rough=0.9, metallic=0.0, grime_scale=4.0, chip_scale=24.0, chip_amount=0.68, streaks=0.5),
    'LessonLeaf': dict(base=(0.11, 0.17, 0.08), dirt=(0.06, 0.08, 0.04), chip=(0.3, 0.24, 0.16), rough=0.6,
                       chip_rough=0.5, metallic=0.0, grime_scale=10.0, chip_scale=40.0, chip_amount=0.72, streaks=0.3),
}
# Known names, with the game table's numbers (made here only when nothing else in the build has made them).
KNOWN_WORN = {
    # DL-12's pupil models' pale beech (art/ch1/dl12.py NEW_WORN): the figures, the steps and the model tree share it.
    'PupilWood': dict(base=(.36, .27, .17), dirt=(.17, .12, .08), chip=(.46, .38, .27), rough=.7, chip_rough=.6, metallic=0,
                      grime_scale=12, chip_scale=40, chip_amount=.74, dust=(.3, .28, .24), dust_amount=.5),
    'WornIron': dict(base=(.045, .043, .04), dirt=(.06, .035, .02), chip=(.3, .29, .27), rough=.7, chip_rough=.35,
                     metallic=.6, dust=(.09, .085, .075), grime_scale=9, chip_scale=40, chip_amount=.6, dust_amount=.4),
    'PigeonWood': dict(base=(.12, .085, .055), dirt=(.06, .045, .03), chip=(.2, .15, .1), rough=.85, chip_rough=.8,
                       metallic=0, dust=(.1, .09, .08), grime_scale=6, chip_scale=30, chip_amount=.75, dust_amount=.6),
    'CastIron': dict(base=(.035, .034, .032), dirt=(.05, .03, .018), chip=(.13, .12, .1), rough=.75, chip_rough=.45,
                     metallic=.5, dust=(.08, .075, .065), grime_scale=9, chip_scale=50, chip_amount=.72, dust_amount=.5),
}
KNOWN_PLAIN = {'Brass': ((.45, .32, .12), .45, .8), 'GaugeNeedle': ((.02, .018, .016), .4, .3)}


def materials(dl01, m):
    d17 = dl01.d17
    M = {}

    def worn(name, kw):
        return bpy.data.materials.get(name) or d17.worn_material(name, **kw)
    for name, kw in NEW_WORN.items():
        M[name] = worn(name, kw)
    for name, kw in KNOWN_WORN.items():
        M[name] = worn(name, kw)
    for name, (c, r, mt) in KNOWN_PLAIN.items():
        M[name] = bpy.data.materials.get(name) or d17.simple_material(name, c, r, metallic=mt)
    M['Window'] = bpy.data.materials.get('Window') or d17.simple_material('Window', (0.8, 0.82, 0.8), 0.12, transmission=0.95)
    M['CrateWood'] = m['wood']
    M['LeverRed'] = m['red']
    M['AttLessonLamp'] = bpy.data.materials.get('AttLessonLamp') or d17.emission_material('AttLessonLamp', (1.0, 0.78, 0.42), 0.0)
    # DL-12's lit bulb (the game's EMIT table has it): the gallery's lamp over the lesson sheet.
    M['AttBulbGlow'] = bpy.data.materials.get('AttBulbGlow') or d17.emission_material('AttBulbGlow', (1.0, 0.82, 0.58), 4.0)
    path = os.path.join(TEX, 'dl13_atlas.png')
    make_atlas(path)
    M['LessonAtlas'] = bpy.data.materials.get('LessonAtlas') or dl01.image_material('LessonAtlas', path)
    path = os.path.join(TEX, 'dl13_sheet.png')
    make_sheet(path)
    M['LessonSheet'] = bpy.data.materials.get('LessonSheet') or sheet_material('LessonSheet', path)
    return M


def sheet_material(name, path):
    """The lesson sheet and the crayon past its edge: an image with alpha (the game keeps a textured material's alpha
    when the glTF says it blends: it draws it as a decal)."""
    import build_d17 as d17
    mat, nt, bsdf = d17._new_material(name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    nt.links.new(tex.outputs['Alpha'], bsdf.inputs['Alpha'])
    bsdf.inputs['Roughness'].default_value = 0.85
    for attr, value in (('surface_render_method', 'BLENDED'), ('blend_method', 'BLEND')):
        if hasattr(mat, attr):
            try:
                setattr(mat, attr, value)
            except (TypeError, ValueError):
                pass
    return mat


# --------------------------------------------------------------------------------------------------------------------
# The atlas: every painted thing in the room on one 1024 x 1024 texture (one material, one draw call)
# --------------------------------------------------------------------------------------------------------------------
ATLAS = 1024
R_CASE = (0, 0, 1024, 128)          # the case's painted backdrop (5.84 x 0.73 m)
R_BOARD = (0, 128, 512, 384)        # the blackboard (2.0 x 1.0)
R_DIAL = (512, 128, 768, 384)       # the cycle dial's face
R_MARK = (768, 128, 1024, 384)      # the school's mark: a sun over an open book
R_TITLE = (0, 384, 512, 448)        # HOW A TREE GROWS
R_LESSON = (512, 384, 704, 432)     # the lamp's label
R_CLASS = (704, 384, 896, 448)      # the door's plate
R_CLOCK = (896, 384, 1024, 512)
R_SEED = (0, 448, 384, 544)         # the seedling tray's card
R_PUPIL = (384, 448, 640, 512)      # stamped in the pad
R_EXIT = (640, 448, 896, 512)       # over the door out
R_FRIEZE = (0, 544, 1024, 608)      # the alphabet frieze
R_POSTER = (0, 608, 256, 928)       # THE PARTS OF A TREE
R_TIMES = (256, 608, 512, 928)      # the timetable: every lesson the same
R_BELLPLATE = (512, 608, 768, 672)  # under the bell: LESSON BELL
R_MOTTO = (512, 672, 1024, 720)     # ORDER ABOVE ALL, stencilled over the apparatus (the order era)
R_NOTICE = (512, 720, 768, 848)     # NO PUPIL TO APPROACH THE APPARATUS UNACCOMPANIED (the protective era)
R_STEWARD = (768, 720, 896, 880)    # the Steward's portrait
R_STEWPLATE = (896, 720, 1024, 752) # its brass plate
R_NUM = [(768 + 64 * k, 608, 832 + 64 * k, 672) for k in range(3)]   # enamel step numbers 1, 2, 3
R_POINTER = (960, 608, 1024, 672)   # the brake's pointer plate on the dial's bezel
R_WHITE = (896, 752, 960, 784)      # white enamel (the pointer's edge)
R_SOIL = (0, 928, 512, 1024)        # the seedling tray's dry, cracked soil


def make_atlas(path):
    from PIL import Image, ImageDraw, ImageFilter, ImageFont
    os.makedirs(os.path.dirname(path), exist_ok=True)
    rnd = random.Random(1313)

    def font(size):
        return ImageFont.truetype(FONT, size)
    img = Image.new('RGB', (ATLAS, ATLAS), (40, 38, 34))
    d = ImageDraw.Draw(img, 'RGBA')
    cream, ink, green, gold = (214, 204, 174), (30, 27, 22), (36, 60, 46), (206, 170, 76)
    chalk = (200, 204, 196)

    def enamel(r, bg, text, fg, size, border=True):
        x0, y0, x1, y1 = r
        d.rectangle(r, fill=bg)
        if border:
            d.rounded_rectangle((x0 + 4, y0 + 4, x1 - 4, y1 - 4), radius=8, outline=fg, width=3)
        d.text(((x0 + x1) / 2, (y0 + y1) / 2 + 1), text, font=font(size), fill=fg, anchor='mm')

    def mark(cx, cy, k, sun=gold, book=cream, bg=green):
        d.pieslice((cx - 44 * k, cy - 74 * k, cx + 44 * k, cy + 14 * k), 180, 360, fill=sun)
        for a in range(200, 341, 28):
            r = math.radians(a)
            d.line((cx + 54 * k * math.cos(r), cy - 30 * k + 54 * k * math.sin(r),
                    cx + 76 * k * math.cos(r), cy - 30 * k + 76 * k * math.sin(r)), fill=sun, width=max(2, int(6 * k)))
        d.polygon([(cx - 70 * k, cy - 8 * k), (cx, cy + 8 * k), (cx + 70 * k, cy - 8 * k), (cx + 70 * k, cy + 52 * k),
                   (cx, cy + 70 * k), (cx - 70 * k, cy + 52 * k)], fill=book)
        d.line((cx, cy + 8 * k, cx, cy + 70 * k), fill=bg, width=max(2, int(5 * k)))

    def straight_tree(cx, base, h, col, w=3, labels=None):
        """The lesson's tree: straight, symmetric, the same every time."""
        d.line((cx, base, cx, base - h), fill=col, width=w + 1)
        for k, (zf, sp) in enumerate(((0.38, 0.42), (0.58, 0.32), (0.76, 0.2))):
            y = base - h * zf
            for s in (-1, 1):
                d.line((cx, y, cx + s * h * sp, y - h * 0.16), fill=col, width=w)
        d.ellipse((cx - h * 0.46, base - h * 1.12, cx + h * 0.46, base - h * 0.5), outline=col, width=w)
        for s in (-1, 0, 1):
            d.line((cx, base, cx + s * h * 0.14, base + h * 0.12), fill=col, width=w)

    # --- the case's backdrop: a painted sky, a sun to the right, the ground and the stages along the bottom ---------
    x0, y0, x1, y1 = R_CASE
    for y in range(y0, y1):
        f = (y - y0) / (y1 - y0)
        c = tuple(int(a + (b - a) * f) for a, b in zip((92, 104, 108), (150, 142, 116)))
        d.line((x0, y, x1, y), fill=c)
    gy = y1 - 18
    d.rectangle((x0, gy, x1, y1), fill=(70, 52, 34))
    for k in range(40):                                     # the soil's grain
        gx = rnd.uniform(x0, x1)
        d.line((gx, gy + rnd.uniform(3, 15), gx + rnd.uniform(4, 14), gy + rnd.uniform(3, 15)), fill=(56, 40, 26), width=2)
    for s in (-1, -0.4, 0.4, 1):                            # painted roots under the trunk, at the middle
        d.line((512, gy, 512 + s * 40, y1 - 2), fill=(110, 84, 52), width=3)
    sx, sy = 905, 40                                        # the sun the tree grows toward
    for a in range(0, 360, 20):
        r = math.radians(a)
        d.line((sx + 30 * math.cos(r), sy + 30 * math.sin(r), sx + 48 * math.cos(r), sy + 48 * math.sin(r)), fill=(214, 176, 80), width=4)
    d.ellipse((sx - 24, sy - 24, sx + 24, sy + 24), fill=(222, 184, 84))
    d.text((905, 96), 'TOWARD THE SUN', font=font(15), fill=(60, 50, 34), anchor='mm')
    for k, word in enumerate(('1  ROOT', '2  TRUNK', '3  BRANCHES', '4  LEAVES')):   # the stages, bottom to top
        cy = y1 - 32 - 26 * k
        d.rounded_rectangle((24, cy - 11, 150, cy + 11), radius=5, fill=(196, 186, 156))
        d.text((87, cy), word, font=font(16), fill=ink, anchor='mm')
        d.line((150, cy, 168, cy), fill=(120, 96, 50), width=3)

    # --- the blackboard: the lesson in chalk, half wiped, and the line written out in rows ------------------------
    x0, y0, x1, y1 = R_BOARD
    d.rectangle(R_BOARD, fill=(26, 34, 30))
    for _ in range(26):                                     # wiped chalk haze
        wx, wy = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        d.ellipse((wx - 60, wy - 14, wx + 60, wy + 14), fill=(120, 126, 118, 16))
    d.text((x0 + 140, y0 + 26), 'HOW A TREE GROWS', font=font(28), fill=chalk, anchor='mm')
    d.line((x0 + 30, y0 + 46, x0 + 250, y0 + 46), fill=chalk, width=2)
    straight_tree(x0 + 130, y0 + 210, 120, chalk, w=3)
    for k, word in enumerate(('1. the root', '2. the trunk', '3. the branches', '4. the leaves')):
        d.text((x0 + 268, y0 + 68 + 30 * k), word, font=font(22), fill=chalk, anchor='lm')
    for k in range(3):
        d.text((x0 + 268, y0 + 196 + 20 * k), 'A tree always grows straight.', font=font(15), fill=(170, 176, 168), anchor='lm')

    # --- the cycle dial: its shapes are the lesson's phases. Clockwise from the bell at the top, 12 s a turn: a band
    #     for each step's time out (step 1 inner, its enamel number where it comes out), the window where all three are
    #     out cut red through them (the bands white in it), a white chevron on the rim at the window's middle (the
    #     brake's pointer on the bezel matches it), and the model tree's growth on the left, in green.
    x0, y0, x1, y1 = R_DIAL
    cx, cy, R = (x0 + x1) / 2, (y0 + y1) / 2, 126
    d.rectangle(R_DIAL, fill=(60, 50, 34))
    face, dark, red, white = (214, 204, 174), (34, 40, 36), (168, 30, 22), (246, 242, 228)
    d.ellipse((cx - R, cy - R, cx + R, cy + R), fill=face, outline=(70, 62, 50), width=3)

    def ang(t):                                             # clockwise from the top, in PIL's degrees
        return t / CYCLE * 360.0 - 90.0

    def pt(t, r):
        a = math.radians(ang(t))
        return cx + r * math.cos(a), cy + r * math.sin(a)

    def band(r0, r1, t0, t1, col):
        d.arc((cx - r1, cy - r1, cx + r1, cy + r1), ang(t0), ang(t1), fill=col, width=int(r1 - r0))
    d.pieslice((cx - R + 3, cy - R + 3, cx + R - 3, cy + R - 3), ang(RED[0]), ang(RED[1]), fill=red)      # all out
    d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), fill=face)
    for k in range(12):                                     # the seconds
        if k == 0:
            continue
        a = math.radians(k * 30 - 90)
        d.line((cx + 110 * math.cos(a), cy + 110 * math.sin(a), cx + 122 * math.cos(a), cy + 122 * math.sin(a)), fill=(70, 62, 50), width=3)
    band(102, 109, TREE_T[0], TREE_T[1], (58, 104, 54))     # the tree grows
    tx, ty = pt((TREE_T[0] + TREE_T[1]) / 2, 64)
    d.line((tx, ty + 20, tx, ty - 6), fill=(96, 70, 40), width=5)
    d.ellipse((tx - 17, ty - 30, tx + 17, ty + 2), fill=(58, 104, 54))
    for s in (-1, 1):
        d.line((tx, ty + 4, tx + s * 10, ty - 6), fill=(96, 70, 40), width=3)
    BANDS = ((32, 49), (54, 71), (76, 93))
    for k, ((r0, r1), t0, t1) in enumerate(zip(BANDS, MARKS, FOLDS)):
        band(r0, r1, t0, t1, dark)
        band(r0 + 2, r1 - 2, RED[0], RED[1], white)        # white where they are all out
    for k, ((r0, r1), t0) in enumerate(zip(BANDS, MARKS)):  # the steps' enamel numbers, where each comes out
        nx, ny = pt(t0 + 0.12, (r0 + r1) / 2)
        d.ellipse((nx - 14, ny - 14, nx + 14, ny + 14), fill=(206, 196, 166), outline=(120, 92, 44), width=3)
        d.text((nx, ny + 1), str(k + 1), font=font(22), fill=ink, anchor='mm')
    # The chevron on the rim at the window's middle, pointing in.
    tm = (RED[0] + RED[1]) / 2
    a, w = math.radians(ang(tm)), math.radians(12)
    tip, base = 90, 126
    chev = [(cx + tip * math.cos(a), cy + tip * math.sin(a)), (cx + base * math.cos(a - w), cy + base * math.sin(a - w)),
            (cx + (base - 11) * math.cos(a), cy + (base - 11) * math.sin(a)), (cx + base * math.cos(a + w), cy + base * math.sin(a + w))]
    d.polygon(chev, fill=white, outline=dark, width=3)
    # The bell at the top, where the hand starts.
    bx, by = cx, cy - 113
    d.pieslice((bx - 9, by - 9, bx + 9, by + 9), 180, 360, fill=(170, 130, 52))
    d.rectangle((bx - 9, by - 1, bx + 9, by + 3), fill=(170, 130, 52))
    d.ellipse((bx - 3, by + 2, bx + 3, by + 8), fill=(120, 88, 36))
    d.ellipse((cx - 13, cy - 13, cx + 13, cy + 13), fill=(60, 50, 34))

    # --- the brake's pointer plate on the bezel (behind the white chevron, upright): three stairs, all out, on red --
    x0, y0, x1, y1 = R_POINTER
    d.rectangle(R_POINTER, fill=dark)
    d.rectangle((x0 + 3, y0 + 3, x1 - 4, y1 - 4), fill=red)
    d.polygon([(x0 + 9, y1 - 10), (x0 + 9, y1 - 22), (x0 + 24, y1 - 22), (x0 + 24, y1 - 35), (x0 + 39, y1 - 35), (x0 + 39, y1 - 48),
               (x0 + 55, y1 - 48), (x0 + 55, y1 - 10)], fill=white)
    x0, y0, x1, y1 = R_WHITE
    d.rectangle(R_WHITE, fill=white)

    # --- the school's mark, an enamel roundel -----------------------------------------------------------------------
    x0, y0, x1, y1 = R_MARK
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    d.rectangle(R_MARK, fill=(60, 50, 34))
    d.ellipse((x0 + 4, y0 + 4, x1 - 4, y1 - 4), fill=green, outline=cream, width=8)
    mark(cx, cy + 6, 1.2)

    # --- the plates --------------------------------------------------------------------------------------------------
    enamel(R_TITLE, green, 'HOW A TREE GROWS', cream, 40)
    for cx in (R_TITLE[0] + 34, R_TITLE[2] - 34):
        mark(cx, R_TITLE[1] + 34, 0.26)
    enamel(R_LESSON, (26, 24, 20), 'LESSON', (210, 190, 140), 30)
    enamel(R_CLASS, (40, 56, 78), 'CLASS 2', cream, 40)
    enamel(R_EXIT, green, 'TO THE HALL  >', cream, 34)
    x0, y0, x1, y1 = R_BELLPLATE
    enamel(R_BELLPLATE, (120, 92, 44), 'LESSON BELL', (40, 30, 16), 34, border=False)
    x0, y0, x1, y1 = R_PUPIL
    d.rectangle(R_PUPIL, fill=(128, 98, 46))
    d.rectangle((x0 + 6, y0 + 6, x1 - 6, y1 - 6), outline=(74, 56, 26), width=3)
    d.text(((x0 + x1) / 2, (y0 + y1) / 2), 'PUPIL  HERE', font=font(34), fill=(64, 48, 22), anchor='mm')

    for k, r in enumerate(R_NUM):
        d.rectangle(r, fill=(60, 50, 34))
        d.ellipse((r[0] + 3, r[1] + 3, r[2] - 3, r[3] - 3), fill=(206, 196, 166), outline=(120, 92, 44), width=4)
        d.text(((r[0] + r[2]) / 2, (r[1] + r[3]) / 2 + 1), str(k + 1), font=font(40), fill=ink, anchor='mm')

    # --- the order era: the motto in stencil, cream on a dark band; the Steward's portrait, kindly and stern ----------
    x0, y0, x1, y1 = R_MOTTO
    d.rectangle(R_MOTTO, fill=(34, 40, 34))
    d.text(((x0 + x1) / 2, (y0 + y1) / 2 + 1), 'ORDER   ABOVE   ALL', font=font(38), fill=(196, 186, 150), anchor='mm')
    for k in range(9):                                     # the stencil's bridges: gaps cut through the letters
        bx = x0 + 70 + k * 46
        d.line((bx, y0 + 18, bx, y0 + 22), fill=(34, 40, 34), width=3)
    x0, y0, x1, y1 = R_STEWARD
    d.rectangle(R_STEWARD, fill=(40, 34, 26))
    for yy in range(y0, y1):                               # a painted, varnished dark ground, lighter behind the head
        f = abs((yy - y0) / (y1 - y0) - 0.35)
        d.line((x0, yy, x1, yy), fill=(int(70 - 50 * f), int(60 - 42 * f), int(42 - 28 * f)))
    cx = (x0 + x1) / 2
    d.polygon([(x0 + 8, y1), (x0 + 18, y0 + 100), (cx - 18, y0 + 84), (cx + 18, y0 + 84), (x1 - 18, y0 + 100), (x1 - 8, y1)], fill=(30, 34, 40))
    d.line((x0 + 30, y0 + 98, x1 - 34, y1 - 6), fill=(150, 124, 62), width=9)           # the sash
    for k in range(4):
        d.ellipse((cx - 3, y0 + 104 + 12 * k, cx + 3, y0 + 110 + 12 * k), fill=(170, 140, 70))
    d.ellipse((cx - 22, y0 + 34, cx + 22, y0 + 88), fill=(150, 118, 92))                 # the head
    d.chord((cx - 23, y0 + 26, cx + 23, y0 + 70), 180, 360, fill=(170, 170, 160))          # grey hair
    for ex in (-9, 9):
        d.line((cx + ex - 4, y0 + 56, cx + ex + 4, y0 + 56), fill=(50, 36, 28), width=2)
    d.arc((cx - 7, y0 + 68, cx + 7, y0 + 74), 30, 150, fill=(90, 50, 40), width=2)       # the painted half-smile
    enamel(R_STEWPLATE, (120, 92, 44), 'THE STEWARD', (40, 30, 16), 18, border=False)
    # --- the protective era: the notice by the apparatus ---------------------------------------------------------------
    x0, y0, x1, y1 = R_NOTICE
    d.rectangle(R_NOTICE, fill=(206, 198, 172))
    d.rectangle((x0 + 5, y0 + 5, x1 - 5, y1 - 5), outline=(40, 52, 44), width=4)
    for k, line in enumerate(('NO PUPIL', 'TO APPROACH THE APPARATUS', 'UNACCOMPANIED')):
        d.text(((x0 + x1) / 2, y0 + 30 + 34 * k), line, font=font(30 if k != 1 else 17), fill=(40, 34, 28), anchor='mm')

    # --- the clock: stopped -------------------------------------------------------------------------------------------
    x0, y0, x1, y1 = R_CLOCK
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    d.rectangle(R_CLOCK, fill=(30, 28, 24))
    d.ellipse((x0 + 4, y0 + 4, x1 - 4, y1 - 4), fill=(208, 200, 176))
    for k in range(12):
        a = math.radians(k * 30 - 60)
        d.text((cx + 46 * math.cos(a), cy + 46 * math.sin(a)), str(k + 1), font=font(15), fill=ink, anchor='mm')
    d.line((cx, cy, cx + 22 * math.cos(math.radians(-60)), cy + 22 * math.sin(math.radians(-60))), fill=ink, width=4)  # ten past nine
    d.line((cx, cy, cx - 34, cy), fill=ink, width=3)

    # --- the seedling card, in a teacher's hand ------------------------------------------------------------------------
    x0, y0, x1, y1 = R_SEED
    d.rectangle(R_SEED, fill=(196, 186, 160))
    d.text((x0 + 16, y0 + 26), 'Class 2 - our seedlings', font=font(30), fill=(44, 52, 90), anchor='lm')
    d.text((x0 + 16, y0 + 66), 'please water each morning', font=font(24), fill=(44, 52, 90), anchor='lm')

    # --- the alphabet frieze ------------------------------------------------------------------------------------------
    x0, y0, x1, y1 = R_FRIEZE
    d.rectangle(R_FRIEZE, fill=(176, 166, 136))
    cols = [(150, 80, 60), (70, 110, 140), (90, 130, 80), (180, 150, 70)]
    for k, ch in enumerate('ABCDEFGHIJKLMNOPQRSTUVWXYZ'):
        lx = x0 + 6 + k * 39.1
        d.rectangle((lx, y0 + 6, lx + 34, y1 - 6), fill=tuple(int(c * 0.55 + 60) for c in cols[k % 4]))
        d.text((lx + 17, (y0 + y1) / 2), ch + ch.lower(), font=font(22), fill=(232, 224, 200), anchor='mm')

    # --- the poster: the parts of a tree -------------------------------------------------------------------------------
    x0, y0, x1, y1 = R_POSTER
    d.rectangle(R_POSTER, fill=(186, 176, 146))
    d.rectangle((x0 + 6, y0 + 6, x1 - 6, y1 - 6), outline=(80, 70, 50), width=3)
    d.text(((x0 + x1) / 2, y0 + 30), 'THE PARTS', font=font(30), fill=(50, 70, 50), anchor='mm')
    d.text(((x0 + x1) / 2, y0 + 62), 'OF A TREE', font=font(30), fill=(50, 70, 50), anchor='mm')
    straight_tree((x0 + x1) / 2 - 26, y0 + 270, 130, (70, 60, 40), w=4)
    for k, word in enumerate(('leaves', 'branches', 'trunk', 'root')):
        d.text((x1 - 14, y0 + 110 + 52 * k), word, font=font(18), fill=(50, 40, 30), anchor='rm')

    # --- the timetable: every period, the same lesson ---------------------------------------------------------------
    x0, y0, x1, y1 = R_TIMES
    d.rectangle(R_TIMES, fill=(190, 182, 156))
    d.text(((x0 + x1) / 2, y0 + 24), 'TIMETABLE', font=font(28), fill=(40, 40, 60), anchor='mm')
    for r in range(6):
        ry = y0 + 52 + r * 44
        d.line((x0 + 8, ry, x1 - 8, ry), fill=(90, 84, 70), width=2)
        if r < 5:
            d.text((x0 + 16, ry + 22), ('MON', 'TUE', 'WED', 'THU', 'FRI')[r], font=font(16), fill=(40, 40, 60), anchor='lm')
            for c in range(2):
                d.text((x0 + 104 + c * 76, ry + 22), 'the tree', font=font(15), fill=(60, 50, 40), anchor='mm')
    d.line((x0 + 62, y0 + 52, x0 + 62, y0 + 272), fill=(90, 84, 70), width=2)

    # --- the seedling tray's soil, long dry: pale, shrunk from the tray's sides, cracked into plates ------------------
    import numpy as np
    x0, y0, x1, y1 = R_SOIL
    w, h = x1 - x0, y1 - y0
    rs = np.random.default_rng(1390)
    seeds = np.stack([rs.uniform(0, w, 70), rs.uniform(0, h, 70)], 1)
    yy, xx = np.mgrid[0:h, 0:w]
    dist = np.sqrt((xx[..., None] - seeds[None, None, :, 0]) ** 2 + ((yy[..., None] - seeds[None, None, :, 1]) * 1.15) ** 2)
    dist.sort(axis=2)
    gap = dist[..., 1] - dist[..., 0]
    plate = np.clip(dist[..., 0] / 22.0, 0, 1)
    base = np.array((156, 138, 112), float)
    col = base[None, None, :] * (1.04 - 0.12 * plate[..., None]) * (1 + rs.normal(0, 0.05, (h, w, 1)))
    crack = gap < 2.2
    col[crack] = (62, 48, 36)
    col[(gap >= 2.2) & (gap < 3.6)] *= 0.82
    edge = np.minimum.reduce([xx, w - 1 - xx, yy * 2.5, (h - 1 - yy) * 2.5])
    col[edge < 6] = (40, 32, 24)                            # the soil pulled away from the tray's sides
    img.paste(Image.fromarray(np.clip(col, 0, 255).astype('uint8'), 'RGB'), (x0, y0))

    # Age it all: stains, a little fade and blur.
    for _ in range(140):
        x, y, r = rnd.uniform(0, ATLAS), rnd.uniform(0, ATLAS), rnd.uniform(4, 40)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(60, 46, 26, rnd.randint(6, 20)))
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    img.quantize(160, method=Image.Quantize.MEDIANCUT).save(path, optimize=True)


# --------------------------------------------------------------------------------------------------------------------
# Building kit
# --------------------------------------------------------------------------------------------------------------------
class Kit:
    """One bmesh (with a UV layer) and its materials. Called with a material (or a material's name) -> slot index.
    Decal quads keep the winding they are given (everything else is recalculated outward)."""
    def __init__(self, alias=None):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.mats = []
        self.decals = set()
        self.alias = alias or {}

    def __call__(self, mat):
        if isinstance(mat, str):
            name = self.alias.get(mat, mat)
            mat = bpy.data.materials.get(name)
            if mat is None:
                sys.path.insert(0, COMMON)
                import voice_props as VP
                mat = VP.material(name)
        if mat not in self.mats:
            self.mats.append(mat)
        return self.mats.index(mat)

    def tris(self):
        return sum(len(f.verts) - 2 for f in self.bm.faces)

    def mesh(self, name, origin=None, sharp=35):
        bm = self.bm
        bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f not in self.decals])
        if origin is not None:
            bmesh.ops.translate(bm, vec=-Vector(origin), verts=bm.verts[:])
        me = bpy.data.meshes.new(name)
        bm.to_mesh(me)
        bm.free()
        for mt in self.mats:
            me.materials.append(mt)
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        me.set_sharp_from_angle(angle=math.radians(sharp))
        return me

    def obj(self, name, coll, origin=None, sharp=35):
        me = self.mesh(name, origin, sharp)
        ob = bpy.data.objects.new(name, me)
        if origin is not None:
            ob.location = Vector(origin)
        coll.objects.link(ob)
        return ob


def place(me, name, loc, coll, rot=(0.0, 0.0, 0.0)):
    ob = bpy.data.objects.new(name, me)
    ob.location = Vector(loc)
    ob.rotation_euler = rot
    coll.objects.link(ob)
    return ob


def quad(K, center, u, v, rect, mat):
    """A painted quad from the atlas: centre, u (to the image's right) and v (to its top) as half-extent vectors;
    it faces u x v."""
    c, u, v = Vector(center), Vector(u), Vector(v)
    vs = [K.bm.verts.new(p) for p in (c - u - v, c + u - v, c + u + v, c - u + v)]
    f = K.bm.faces.new(vs)
    f.material_index = mat
    px0, py0, px1, py1 = rect
    uvs = ((px0, py1), (px1, py1), (px1, py0), (px0, py0))
    for loop, (px, py) in zip(f.loops, uvs):
        loop[K.uv].uv = (px / ATLAS, 1.0 - py / ATLAS)
    K.decals.add(f)
    return f


def disc_decal(K, center, r, rect, mat, seg=32):
    """A round painted face toward -y, mapped onto the inscribed circle of rect."""
    c = Vector(center)
    px0, py0, px1, py1 = rect
    ucx, ucy, hr = (px0 + px1) / 2, (py0 + py1) / 2, (px1 - px0) / 2
    vs = [K.bm.verts.new(c + Vector((r * math.cos(2 * math.pi * k / seg), 0, r * math.sin(2 * math.pi * k / seg))))
          for k in range(seg)]
    f = K.bm.faces.new(vs[::-1])           # wound to face -y
    f.material_index = mat
    for loop in f.loops:
        p = loop.vert.co - c
        loop[K.uv].uv = ((ucx + p.x / r * hr) / ATLAS, 1.0 - (ucy - p.z / r * hr) / ATLAS)
    K.decals.add(f)
    return f


# --------------------------------------------------------------------------------------------------------------------
# The teaching figures: a child-sized jointed wooden pupil model (a lay figure: egg head, ball joints, no face)
# --------------------------------------------------------------------------------------------------------------------
def pupil(bm, w, j, st, pose='stand', low=False):
    """DL-12's pupil model (art/ch1/dl12.py figure(): the same parts, sizes and materials), in its frame: the floor at
    z 0, centred, facing -y. 'stand': on its four-castor stand, 0.95 tall overall. 'seat': without the stand, sat on a
    chair whose seat is at 0.30, forearms on a desk top at 0.50 ahead of it (hands 0.25 forward). low: fewer
    segments, for the figures sat at the desks behind the lane."""
    import build_d17 as d17
    from build_d17 import add_box, add_torus
    V = Vector
    sg = (lambda n: max(5, n * 2 // 3)) if low else (lambda n: n)

    def add_cyl(bm, a, b, r1, r2=None, mat=0, seg=8):
        return d17.add_cyl(bm, a, b, r1, r2, mat=mat, seg=sg(seg))

    def add_sphere(bm, c, r, mat=0, seg=8, scale=(1, 1, 1)):
        return d17.add_sphere(bm, c, r, mat=mat, seg=sg(seg), scale=scale)

    def rounded_box(size, center, p=3.0, cuts=3, bm=None, mat=0, rot=None):
        return d17.rounded_box(size, center, p=p, cuts=(2 if low else cuts), bm=bm, mat=mat, rot=rot)
    if pose == 'stand':
        for sx in (-1, 1):
            for sy in (-1, 1):
                p = V((sx * 0.175, sy * 0.15, 0.072))
                add_cyl(bm, (0, 0, 0.08), p, 0.012, mat=st, seg=5)
                add_cyl(bm, p, p - V((0, 0, 0.02)), 0.01, mat=st, seg=5)
                add_box(bm, p - V((0, 0, 0.032)), (0.03, 0.012, 0.022), mat=st)
                add_cyl(bm, (p.x - 0.011, p.y, 0.028), (p.x + 0.011, p.y, 0.028), 0.028, mat=st, seg=10)
        add_cyl(bm, (0, 0, 0.055), (0, 0, 0.1), 0.032, mat=st, seg=10)
        add_cyl(bm, (0, 0, 0.1), (0, 0, 0.122), 0.125, mat=j, seg=18)
        add_cyl(bm, (0, 0.07, 0.12), (0, 0.07, 0.49), 0.009, mat=st, seg=6)
        add_cyl(bm, (0, 0.072, 0.49), (0, 0.03, 0.49), 0.011, mat=st, seg=6)
        add_torus(bm, (0, 0.074, 0.36), (0, 0, 1), 0.016, 0.004, mat=st, seg=8, rseg=4)
        for sx in (-1, 1):
            x = sx * 0.05
            rounded_box((0.048, 0.1, 0.034), (x, -0.022, 0.139), p=3.0, cuts=3, bm=bm, mat=w)
            add_sphere(bm, (x, 0, 0.168), 0.019, mat=j, seg=8)
            add_cyl(bm, (x, 0, 0.18), (x * 1.04, 0, 0.31), 0.021, 0.026, mat=w, seg=8)
            add_sphere(bm, (x * 1.04, 0, 0.325), 0.026, mat=j, seg=8)
            add_cyl(bm, (x * 1.04, 0, 0.34), (x * 1.1, 0, 0.452), 0.03, 0.036, mat=w, seg=8)
            add_sphere(bm, (x * 1.1, 0, 0.468), 0.031, mat=j, seg=8)
        z0 = 0.0
    else:
        z0 = -0.14                                     # the body sits 0.14 lower: the pelvis on the seat
        for sx in (-1, 1):
            x = sx * 0.055
            hip, knee, ank = V((x, -0.005, 0.328)), V((x * 1.05, -0.19, 0.335)), V((x * 1.05, -0.2, 0.06))
            add_sphere(bm, hip, 0.031, mat=j, seg=8)
            add_cyl(bm, hip + V((0, -0.016, 0)), knee + V((0, 0.016, 0)), 0.036, 0.03, mat=w, seg=8)
            add_sphere(bm, knee, 0.026, mat=j, seg=8)
            add_cyl(bm, knee + V((0, 0, -0.016)), ank + V((0, 0, 0.012)), 0.026, 0.021, mat=w, seg=8)
            add_sphere(bm, ank, 0.019, mat=j, seg=8)
            rounded_box((0.048, 0.1, 0.034), (ank.x, ank.y - 0.022, 0.022), p=3.0, cuts=3, bm=bm, mat=w)
    rounded_box((0.158, 0.098, 0.085), (0, 0, 0.5 + z0), p=3.0, cuts=4, bm=bm, mat=w)
    add_sphere(bm, (0, 0, 0.553 + z0), 1.0, mat=j, seg=10, scale=(0.05, 0.04, 0.03))
    rounded_box((0.186, 0.11, 0.165), (0, 0, 0.644 + z0), p=3.2, cuts=4, bm=bm, mat=w)
    add_cyl(bm, (0, 0, 0.728 + z0), (0, 0, 0.778 + z0), 0.021, mat=j, seg=8)
    add_sphere(bm, (0, 0, 0.864 + z0), 1.0, mat=w, seg=12, scale=(0.062, 0.068, 0.085))
    for sx in (-1, 1):
        sh = V((sx * 0.112, 0, 0.705 + z0))
        add_sphere(bm, sh, 0.029, mat=j, seg=8)
        if pose == 'stand':
            R1 = Matrix.Rotation(math.radians(4.0), 3, 'X') @ Matrix.Rotation(math.radians(sx * 5), 3, 'Y')
            el = sh + R1 @ V((0, 0, -0.135))
            R2 = R1 @ Matrix.Rotation(math.radians(12.0), 3, 'X')
            wr = el + R2 @ V((0, 0, -0.115))
            hc, hrot, hsize = wr + R2 @ V((0, 0, -0.042)), R2.to_4x4(), (0.022, 0.044, 0.062)
        else:
            el = V((sx * 0.125, -0.1, 0.47))
            wr = V((sx * 0.1, -0.21, 0.515))
            hc, hrot, hsize = V((sx * 0.095, -0.25, 0.516)), None, (0.044, 0.062, 0.022)
        d1 = (el - sh).normalized()
        add_cyl(bm, sh + d1 * 0.02, el - d1 * 0.014, 0.021, 0.018, mat=w, seg=8)
        add_sphere(bm, el, 0.02, mat=j, seg=8)
        d2 = (wr - el).normalized()
        add_cyl(bm, el + d2 * 0.012, wr, 0.017, 0.014, mat=w, seg=8)
        add_sphere(bm, wr, 0.014, mat=j, seg=6)
        rounded_box(hsize, hc, p=3.0, cuts=3, bm=bm, mat=w, rot=hrot)


def figure_meshes(M):
    """Two meshes for linked duplicates: the figure on its stand (AttFigure2 and the rack's), the seated figure (the
    desks'). Both turned to face +x (toward the apparatus)."""
    turn = _rz(math.radians(90))
    out = []
    for name, pose, low in (('LessonFigureStand', 'stand', False), ('LessonFigureSeated', 'seat', True)):
        K = Kit()
        pupil(K.bm, K(M['PupilWood']), K(M['CrateWood']), K(M['WornIron']), pose, low)
        bmesh.ops.transform(K.bm, matrix=turn, verts=K.bm.verts)
        out.append(K.mesh(name))
    return out


# --------------------------------------------------------------------------------------------------------------------
# The set
# --------------------------------------------------------------------------------------------------------------------
def build_set(dl01, m, coll):
    d17, dl05 = dl01.d17, dl01.dl05
    global add_box, add_cyl, add_sphere, add_torus, cbox, wall_x, prism
    add_box, add_cyl, add_sphere, add_torus = d17.add_box, d17.add_cyl, d17.add_sphere, d17.add_torus
    cbox, wall_x, prism = dl05.cbox, dl05.wall_x, dl05.prism
    M = materials(dl01, m)
    # The shared tannoy's materials fold into the room's own, all but its enamel horn.
    S = Kit(alias={'DepotSteel': 'CastIron', 'DarkMetal': 'CastIron', 'Cable': 'CastIron', 'PigeonWood': 'PigeonWood'})
    room(S, M)
    alcove(S, M)
    standing, seated = figure_meshes(M)
    desks(S, M, seated, coll)
    rack(S, M, standing, coll)
    ob = place(standing, 'AttFigure2', (FIG2_X, 0.0, 0.0), coll)
    front_seat(S, M, coll)
    apparatus(S, M, coll)
    tree(M, coll)
    gallery(S, M, coll)
    speaker(S, M, coll)
    S.obj('AttLessonRoom', coll)
    return ob


def room(S, M):
    """Floor, walls, ceiling, the two door frames, the solid under the gallery."""
    bm = S.bm
    pl, da, wd, dk, br = S(M['LessonPlaster']), S(M['LessonDado']), S(M['CrateWood']), S(M['PigeonWood']), S(M['Brass'])
    # The floor: boards along the room, a seam every 0.13.
    add_box(bm, ((X0 + X1) / 2, (-1.6 + ALCOVE_Y + 0.2) / 2, -0.1), (X1 - X0, ALCOVE_Y + 1.8, 0.2), mat=wd)
    y = -1.55
    while y < ALCOVE_Y:
        xa, xb = (X0, GALLERY[0]) if y < BACK_Y else ALCOVE
        if y > FACE_Y and y < BACK_Y:
            xa, xb = X0, APP_X[0]
        add_box(bm, ((xa + xb) / 2, y, 0.0), (xb - xa, 0.008, 0.004), mat=dk)
        y += 0.13
    # The walls: the alcove's back wall and its right side; the wall behind the apparatus and the gallery.
    def dado_wall(x0, x1, y0, y1, z0, z1, rail=1.0):
        wall_x(bm, x0, x1, y0, y1, z0, min(z1, z0 + rail), (), da)
        wall_x(bm, x0, x1, y0, y1, z0 + rail, z1, (), pl)
        cbox(bm, ((x0 + x1) / 2, y0 - 0.012, z0 + rail), (x1 - x0, 0.03, 0.05), 0.008, wd)
        cbox(bm, ((x0 + x1) / 2, y0 - 0.01, z0 + 0.06), (x1 - x0, 0.022, 0.12), 0.005, dk)
    dado_wall(X0, ALCOVE[1] + 0.15, ALCOVE_Y, ALCOVE_Y + 0.2, 0.0, CEIL)
    add_box(bm, (ALCOVE[1] + 0.075, (BACK_Y + ALCOVE_Y) / 2, 0.5), (0.15, ALCOVE_Y - BACK_Y, 1.0), mat=da)
    add_box(bm, (ALCOVE[1] + 0.075, (BACK_Y + ALCOVE_Y) / 2, (1.0 + CEIL) / 2), (0.15, ALCOVE_Y - BACK_Y, CEIL - 1.0), mat=pl)
    add_box(bm, ((APP_X[0] + GALLERY[0]) / 2, BACK_Y + 0.1, CEIL / 2), (GALLERY[0] - APP_X[0], 0.2, CEIL), mat=pl)
    dado_wall(GALLERY[0], VEST[0], BACK_Y, BACK_Y + 0.2, GALLERY[2], CEIL, rail=0.95)
    dado_wall(VEST[0], X1, VEST[1], VEST[1] + 0.2, GALLERY[2], VEST[2], rail=0.95)
    # The ceiling, with a deep plaster cornice along the back; lower past the door out, as DL-14's.
    add_box(bm, ((X0 + VEST[0]) / 2, (FRONT_Y + ALCOVE_Y + 0.2) / 2, CEIL + 0.1), (VEST[0] - X0, ALCOVE_Y + 0.2 - FRONT_Y, 0.2), mat=pl)
    add_box(bm, ((VEST[0] + X1) / 2, (FRONT_Y + BACK_Y + 0.2) / 2, (VEST[2] + CEIL + 0.2) / 2), (X1 - VEST[0], BACK_Y + 0.2 - FRONT_Y, CEIL + 0.2 - VEST[2]), mat=pl)
    prism(bm, [(ALCOVE_Y, CEIL), (ALCOVE_Y - 0.14, CEIL), (ALCOVE_Y, CEIL - 0.14)], 'x', ALCOVE[0], ALCOVE[1], mat=pl)
    # The door in: the cross wall at x 216 behind the lane, the lintel over it, an architrave on the room side.
    dx0, dx1, dh = DOOR_IN
    jamb = 0.62
    add_box(bm, ((dx0 + dx1) / 2, (jamb + ALCOVE_Y) / 2, 0.5), (dx1 - dx0, ALCOVE_Y - jamb, 1.0), mat=da)
    add_box(bm, ((dx0 + dx1) / 2, (jamb + ALCOVE_Y) / 2, (1.0 + CEIL) / 2), (dx1 - dx0, ALCOVE_Y - jamb, CEIL - 1.0), mat=pl)
    add_box(bm, ((dx0 + dx1) / 2, (LINTEL_Y + jamb) / 2, (dh + CEIL) / 2), (dx1 - dx0, jamb - LINTEL_Y, CEIL - dh), mat=pl)
    cbox(bm, (dx1 + 0.02, jamb + 0.05, dh / 2 + 0.04), (0.04, 0.1, dh + 0.08), 0.008, wd)
    cbox(bm, (dx1 + 0.02, (LINTEL_Y + jamb + 0.1) / 2, dh + 0.04), (0.04, jamb + 0.1 - LINTEL_Y, 0.08), 0.008, wd)
    cbox(bm, (dx0 + 0.075, (LINTEL_Y + jamb) / 2, dh - 0.01), (0.17, jamb - LINTEL_Y, 0.03), 0.006, wd)                   # the head jamb
    # Its leaf, open into the room flat against the jamb's line: panelled, a glazed upper light, the class's plate.
    lx0, lx1, ly = dx1 + 0.03, dx1 + 0.86, jamb + 0.03
    for (za, zb) in ((0.0, 0.12), (0.12, 1.0), (1.0, 1.1), (1.86, 2.04)):
        cbox(bm, ((lx0 + lx1) / 2, ly, (za + zb) / 2), (lx1 - lx0, 0.04, zb - za), 0.006, dk)
    for xa, xb in ((lx0, lx0 + 0.1), (lx1 - 0.1, lx1)):
        cbox(bm, ((xa + xb) / 2, ly, 1.48), (xb - xa, 0.04, 0.76), 0.006, dk)
    add_box(bm, ((lx0 + lx1) / 2, ly, 1.48), (lx1 - lx0 - 0.2, 0.008, 0.76), mat=S(M['Window']))
    cbox(bm, ((lx0 + lx1) / 2, ly - 0.022, 0.56), (lx1 - lx0 - 0.24, 0.012, 0.66), 0.004, dk)    # the lower panel
    quad(S, ((lx0 + lx1) / 2, ly - 0.03, 1.05), (0.13, 0, 0), (0, 0, 0.042), R_CLASS, S(M['LessonAtlas']))
    add_sphere(bm, (lx1 - 0.07, ly - 0.05, 0.92), 0.028, mat=br, seg=10)
    add_cyl(bm, (lx1 - 0.07, ly - 0.02, 0.92), (lx1 - 0.07, ly - 0.05, 0.92), 0.008, mat=br, seg=6)
    # The gallery: solid beneath, plastered with a dado like DL-14's landing; the deck at 2.05 with a brass nosing on
    # its mantle edge; a fascia under the deck's edge; a small locked store door low in its front.
    g0, g1, gz = GALLERY
    gf = GAL_FRONT
    add_box(bm, ((g0 + X1) / 2, (gf + BACK_Y) / 2, 0.475), (X1 - g0, BACK_Y - gf, 0.95), mat=da)
    add_box(bm, ((g0 + X1) / 2, (gf + BACK_Y) / 2, (0.95 + gz - 0.08) / 2), (X1 - g0, BACK_Y - gf, gz - 0.08 - 0.95), mat=pl)
    add_box(bm, ((g0 + X1) / 2, (gf + BACK_Y) / 2, gz - 0.04), (X1 - g0, BACK_Y - gf, 0.08), mat=wd)
    add_cyl(bm, (g0 - 0.005, gf, gz - 0.015), (g0 - 0.005, FACE_Y, gz - 0.015), 0.018, mat=br, seg=8)
    for k in range(6):                                                      # the deck's boards, along it
        add_box(bm, ((g0 + X1) / 2, gf + 0.05 + 0.34 * k, gz), (X1 - g0, 0.008, 0.004), mat=dk)
    cbox(bm, ((g0 + X1) / 2, gf - 0.03, gz - 0.07), (X1 - g0 + 0.04, 0.06, 0.1), 0.012, dk)       # the fascia
    cbox(bm, ((g0 + X1) / 2, gf - 0.012, 0.95), (X1 - g0, 0.025, 0.04), 0.006, wd)               # the dado rail
    cbox(bm, ((g0 + X1) / 2, gf - 0.01, 0.06), (X1 - g0, 0.02, 0.12), 0.005, dk)                 # skirting
    cbox(bm, (g0 - 0.012, (gf + FACE_Y) / 2, 0.95), (0.025, FACE_Y - gf, 0.04), 0.006, wd)
    cbox(bm, (g0 - 0.01, (gf + FACE_Y) / 2, 0.06), (0.02, FACE_Y - gf, 0.12), 0.005, dk)
    sd = (229.2, 229.85, 1.25)                                              # the store door
    cbox(bm, ((sd[0] + sd[1]) / 2, gf - 0.015, sd[2] / 2 + 0.06), (sd[1] - sd[0], 0.03, sd[2]), 0.008, dk)
    cbox(bm, ((sd[0] + sd[1]) / 2, gf - 0.03, sd[2] / 2 + 0.06), (sd[1] - sd[0] - 0.14, 0.012, sd[2] - 0.2), 0.004, wd)
    add_box(bm, (sd[1] - 0.08, gf - 0.045, 0.75), (0.03, 0.02, 0.08), mat=br)                 # its hasp, padlocked
    add_torus(bm, (sd[1] - 0.08, gf - 0.06, 0.69), (1, 0, 0), 0.02, 0.005, mat=br, seg=10, rseg=4)


def alcove(S, M):
    """The desks' end of the room: the blackboard, the frieze, a stopped clock, the tree poster, the timetable, the
    dead pendant globes."""
    bm = S.bm
    at, wd, dk, ir, gl = S(M['LessonAtlas']), S(M['CrateWood']), S(M['PigeonWood']), S(M['CastIron']), S(M['Window'])
    yw = ALCOVE_Y - 0.004
    bx = 218.25
    cbox(bm, (bx, yw - 0.02, 1.55), (2.12, 0.04, 1.12), 0.01, wd)                         # the board's frame
    quad(S, (bx, yw - 0.045, 1.55), (1.0, 0, 0), (0, 0, 0.5), R_BOARD, at)
    cbox(bm, (bx, yw - 0.07, 0.98), (2.12, 0.08, 0.03), 0.006, wd)                         # its chalk ledge
    for k, x in enumerate((217.6, 217.75, 218.9)):
        add_cyl(bm, (x, yw - 0.07, 1.003), (x + 0.07, yw - 0.07, 1.003), 0.006, mat=S(M['LessonPlaster']), seg=6)
    quad(S, ((ALCOVE[0] + ALCOVE[1]) / 2 + 0.05, yw - 0.01, 2.62), (2.08, 0, 0), (0, 0, 0.13), R_FRIEZE, at)
    add_cyl(bm, (219.75, yw, 3.1), (219.75, yw - 0.06, 3.1), 0.17, mat=dk, seg=24)          # the clock
    disc_decal(S, (219.75, yw - 0.062, 3.1), 0.15, R_CLOCK, at, seg=24)
    quad(S, (216.75, yw - 0.006, 1.62), (0.25, 0, 0), (0, 0, 0.31), R_POSTER, at)
    quad(S, (219.75, yw - 0.006, 1.62), (0.25, 0, 0), (0, 0, 0.31), R_TIMES, at)
    disc_decal(S, (216.75, yw - 0.006, 3.35), 0.22, R_MARK, at)                            # the school's roundel
    # The Steward over the board: an institutional portrait in a heavy frame, a brass plate under it.
    cbox(bm, (bx, yw - 0.03, 3.3), (0.62, 0.06, 0.76), 0.02, dk)
    cbox(bm, (bx, yw - 0.05, 3.3), (0.54, 0.02, 0.68), 0.006, S(M['Brass']))
    quad(S, (bx, yw - 0.062, 3.3), (0.25, 0, 0), (0, 0, 0.312), R_STEWARD, at)
    cbox(bm, (bx, yw - 0.008, 2.86), (0.24, 0.016, 0.06), 0.003, S(M['Brass']))
    quad(S, (bx, yw - 0.017, 2.86), (0.11, 0, 0), (0, 0, 0.0275), R_STEWPLATE, at)
    for x, y in ((217.3, 1.8), (219.3, 2.9)):                                              # enamel shades, dead
        add_cyl(bm, (x, y, CEIL), (x, y, 3.5), 0.006, mat=ir, seg=6)
        add_cyl(bm, (x, y, 3.52), (x, y, 3.42), 0.03, 0.05, mat=ir, seg=12)
        add_cyl(bm, (x, y, 3.43), (x, y, 3.33), 0.05, 0.21, mat=ir, seg=20)
        add_sphere(bm, (x, y, 3.37), 0.04, mat=S(M['Brass']), seg=8)


def desk_unit(S, M, o):
    """A child's desk and chair as one, facing +x: the chair's seat centre over o (on the floor), the seat at 0.30,
    the desk's top 0.20 to 0.58 ahead at 0.50, on cast-iron standards."""
    bm = S.bm
    wd, ir, br = S(M['CrateWood']), S(M['CastIron']), S(M['Brass'])
    x, y = o
    cbox(bm, (x, y, 0.29), (0.28, 0.3, 0.025), 0.006, wd)
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_cyl(bm, (x + sx * 0.115, y + sy * 0.125, 0.0), (x + sx * 0.115, y + sy * 0.125, 0.28), 0.012, mat=wd, seg=6)
        add_cyl(bm, (x - 0.125, y + sx * 0.125, 0.3), (x - 0.135, y + sx * 0.125, 0.6), 0.012, mat=wd, seg=6)
    cbox(bm, (x - 0.132, y, 0.52), (0.02, 0.28, 0.1), 0.004, wd)
    cbox(bm, (x + 0.39, y, 0.49), (0.4, 0.56, 0.025), 0.006, wd)
    cbox(bm, (x + 0.47, y, 0.37), (0.24, 0.5, 0.012), 0.003, wd)                          # the book shelf
    add_cyl(bm, (x + 0.55, y + 0.2, 0.505), (x + 0.55, y + 0.2, 0.495), 0.018, mat=br, seg=8)   # the inkwell's lid
    for sy in (-1, 1):
        yy = y + sy * 0.24
        add_box(bm, (x + 0.4, yy, 0.015), (0.42, 0.03, 0.03), mat=ir)
        add_box(bm, (x + 0.4, yy, 0.24), (0.035, 0.025, 0.46), mat=ir)
        add_box(bm, (x + 0.4, yy, 0.46), (0.36, 0.025, 0.03), mat=ir)


# Desk places (the chair's seat centre), and whether a figure sits in it.
DESKS = [
    ((218.45, 1.15), True), ((219.45, 1.15), True),
    ((216.55, 1.95), True), ((217.5, 1.95), False), ((218.45, 1.95), True), ((219.45, 1.95), True),
    ((216.55, 2.75), True), ((217.5, 2.75), True), ((218.45, 2.75), True), ((219.45, 2.75), False),
    ((216.55, 3.5), False), ((217.5, 3.5), True), ((218.45, 3.5), False), ((219.45, 3.5), True),
]


def desks(S, M, seated, coll):
    rnd = random.Random(213)
    k = 0
    for o, sat in DESKS:
        desk_unit(S, M, o)
        if sat and MERGE_SEATED:
            rot = (rnd.uniform(-0.04, 0.04), rnd.uniform(-0.05, 0.03), rnd.uniform(-0.12, 0.12))
            tmp = bmesh.new()
            pupil(tmp, S(M['PupilWood']), S(M['CrateWood']), S(M['WornIron']), 'seat', True)
            R = Matrix.Translation((o[0], o[1], 0.0)) @ Euler(rot).to_matrix().to_4x4() @ _rz(math.radians(90))
            bmesh.ops.transform(tmp, matrix=R, verts=tmp.verts)
            me = bpy.data.meshes.new('_dl13_tmp')
            tmp.to_mesh(me)
            tmp.free()
            S.bm.from_mesh(me)
            bpy.data.meshes.remove(me)
        elif sat:
            # Linked duplicates of one seated figure; a little turn and lean so they aren't stamped.
            place(seated, f'AttClassFigure.{k:02d}', (o[0], o[1], 0.0), coll,
                  rot=(rnd.uniform(-0.04, 0.04), rnd.uniform(-0.05, 0.03), rnd.uniform(-0.12, 0.12)))
            k += 1


def rack(S, M, standing, coll):
    """The figures' rack: a wheeled timber frame, two figures chained in facing the room, an empty place between
    them with its chain hanging open."""
    bm = S.bm
    wd, ir, br = S(M['CrateWood']), S(M['CastIron']), S(M['Brass'])
    x0, x1, y0, y1 = RACK
    for x in (x0 + 0.03, x1 - 0.03):
        add_box(bm, (x, (y0 + y1) / 2, 0.1), (0.05, y1 - y0, 0.06), mat=wd)
        for y in (y0 + 0.03, y1 - 0.03):
            add_box(bm, (x, y, 0.62), (0.05, 0.05, 1.04), mat=wd)
            add_cyl(bm, (x, y - 0.012, 0.035), (x, y + 0.012, 0.035), 0.035, mat=ir, seg=10)
        add_box(bm, (x, (y0 + y1) / 2, 1.14), (0.05, y1 - y0, 0.05), mat=wd)
    add_box(bm, ((x0 + x1) / 2, y1 - 0.03, 1.14), (x1 - x0, 0.05, 0.05), mat=wd)
    add_box(bm, ((x0 + x1) / 2, y1 - 0.03, 0.62), (x1 - x0, 0.04, 0.04), mat=wd)
    add_box(bm, ((x0 + x1) / 2, (y0 + y1) / 2, 0.08), (x1 - x0, 0.05, 0.04), mat=wd)
    # The chain across the front at 0.6, through each figure's arm: links as small tori.
    def chain(a, b, n):
        a, b = Vector(a), Vector(b)
        for i in range(n):
            p = a.lerp(b, (i + 0.5) / n)
            sag = 0.05 * 4 * ((i + 0.5) / n) * (1 - (i + 0.5) / n)
            add_torus(bm, p - Vector((0, 0, sag)), (0, 1, 0) if i % 2 else (0, 0, 1), 0.012, 0.0035, mat=ir, seg=8, rseg=4)
    chain((x0 + 0.03, y0 + 0.02, 0.6), (x0 + 0.38, y0 + 0.02, 0.6), 12)
    for k in range(6):                                                     # and the empty slot's end, hanging
        add_torus(bm, (x1 - 0.03, y0 + 0.02, 0.58 - 0.025 * k), (0, 1, 0) if k % 2 else (1, 0, 0), 0.012, 0.0035, mat=ir, seg=8, rseg=4)
    add_box(bm, (x1 - 0.03, y0 + 0.02, 0.41), (0.035, 0.015, 0.04), mat=br)            # its padlock, open
    # Four places, two deep: the front left and the back right still hold their figures; the front right is
    # AttFigure2's, empty, its chain hanging open (the figure behind shows through the gap); the back left is bare.
    place(standing, 'AttRackFigure.00', (x0 + 0.2, y0 + 0.2, 0.0), coll, rot=(0, 0, math.radians(-78)))
    place(standing, 'AttRackFigure.01', (x1 - 0.2, y1 - 0.2, 0.0), coll, rot=(0, 0, math.radians(-100)))


def front_seat(S, M, coll):
    """The front seat on the lane: the pupil pad in the floor, the desk (its knee-hole open on the left for the figure's
    stand to slot under), the LESSON lamp on its stalk, and the chair pushed back off the lane."""
    bm = S.bm
    wd, ir, br, at, dk = S(M['CrateWood']), S(M['CastIron']), S(M['Brass']), S(M['LessonAtlas']), S(M['PigeonWood'])
    hb = S(M['Brass'])
    p0, p1 = PAD
    cbox(bm, ((p0 + p1) / 2, 0.0, 0.004), (p1 - p0, 0.44, 0.012), 0.003, hb)
    quad(S, ((p0 + p1) / 2, 0.0, 0.0105), (0.15, 0, 0), (0, 0.0375, 0), R_PUPIL, at)          # read from the camera
    x0, x1, top = DESK
    cbox(bm, ((x0 + x1) / 2, 0.0, top - 0.015), (x1 - x0 + 0.04, 0.6, 0.03), 0.006, wd)
    cbox(bm, ((x0 + x1) / 2 + 0.06, 0.0, 0.38), (x1 - x0 - 0.12, 0.54, 0.014), 0.003, wd)     # the book shelf
    cbox(bm, (x1 - 0.01, 0.0, 0.26), (0.02, 0.56, 0.44), 0.004, dk)                        # its modesty panel
    for sy in (-1, 1):
        yy = sy * 0.27
        add_box(bm, ((x0 + x1) / 2, yy, 0.015), (x1 - x0 + 0.04, 0.03, 0.03), mat=ir)
        add_box(bm, ((x0 + x1) / 2 + 0.05, yy, 0.25), (0.04, 0.025, 0.48), mat=ir)
        add_box(bm, ((x0 + x1) / 2, yy, top - 0.045), (x1 - x0 - 0.02, 0.025, 0.03), mat=ir)
    add_cyl(bm, (x1 - 0.06, -0.2, top), (x1 - 0.06, -0.2, top + 0.01), 0.018, mat=br, seg=8)  # the inkwell
    cbox(bm, ((x0 + x1) / 2 - 0.04, -0.06, top + 0.008), (0.17, 0.22, 0.014), 0.003, S(M['LessonDado']))  # an exercise book
    # The lamp: a stalk from the desk's back corner, a brass cup and its glass (AttLessonLamp), the label under it.
    lx, ly, lz = LAMP
    add_cyl(bm, (lx, ly + 0.06, top), (lx, ly + 0.06, lz - 0.05), 0.012, mat=ir, seg=8)
    add_cyl(bm, (lx, ly + 0.06, top), (lx, ly + 0.06, top + 0.02), 0.035, mat=ir, seg=12)
    add_cyl(bm, (lx, ly + 0.06, lz - 0.06), (lx, ly + 0.0, lz), 0.012, mat=ir, seg=8)
    add_cyl(bm, (lx, ly + 0.03, lz), (lx, ly - 0.015, lz), 0.055, 0.06, mat=br, seg=16)
    add_torus(bm, (lx, ly - 0.018, lz), (0, 1, 0), 0.058, 0.007, mat=br, seg=18, rseg=6)
    cbox(bm, (lx - 0.03, ly + 0.035, lz - 0.2), (0.22, 0.012, 0.06), 0.003, ir)
    quad(S, (lx - 0.03, ly + 0.028, lz - 0.2), (0.1, 0, 0), (0, 0, 0.025), R_LESSON, at)
    K = Kit()
    add_sphere(K.bm, (0, 0, 0), 0.05, mat=K(M['AttLessonLamp']), seg=14, scale=(1, 0.6, 1))
    K.obj('AttLessonLamp', coll, origin=None).location = (lx, ly - 0.02, lz)
    # The wire: down the stalk, along the floor behind the lane to the apparatus's base.
    add_cyl(bm, (lx + 0.03, ly + 0.08, top - 0.03), (lx + 0.03, 0.31, 0.012), 0.007, mat=ir, seg=6)
    add_cyl(bm, (lx + 0.03, 0.31, 0.012), (APP_X[0] - 0.02, 0.62, 0.012), 0.007, mat=ir, seg=6)
    add_cyl(bm, ((p0 + p1) / 2, 0.22, 0.006), ((x0 + x1) / 2, 0.29, 0.006), 0.006, mat=ir, seg=6)   # the pad's lead
    # The chair, pushed back from the desk and turned away: the last one to leave.
    cx, cy, a = 219.28, 0.68, math.radians(28)
    rot = _rz(a)
    c = Vector((cx, cy, 0))
    cbox(bm, c + Vector((0, 0, 0.29)), (0.28, 0.3, 0.025), 0.006, wd, rot=rot)
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_cyl(bm, c + rot @ Vector((sx * 0.115, sy * 0.125, 0)), c + rot @ Vector((sx * 0.115, sy * 0.125, 0.28)), 0.012, mat=wd, seg=6)
        add_cyl(bm, c + rot @ Vector((-0.125, sx * 0.125, 0.3)), c + rot @ Vector((-0.135, sx * 0.125, 0.6)), 0.012, mat=wd, seg=6)
    cbox(bm, c + rot @ Vector((-0.132, 0, 0.52)), (0.02, 0.28, 0.1), 0.004, wd, rot=rot)


def apparatus(S, M, coll):
    """The lesson apparatus: wood and brass against the front wall. The plinth; the face (y 0.9) with the three step
    slots; the clockwork tower at the left with its gears, the bell and the school's roundel; the pawl's foot and the
    rod to the dial; the dial with its ratchet rim; the case for the model tree; the cornice and the title."""
    bm = S.bm
    dk, wd, br, ir, at = S(M['PigeonWood']), S(M['CrateWood']), S(M['Brass']), S(M['CastIron']), S(M['LessonAtlas'])
    gl, hb = S(M['Window']), S(M['Brass'])
    a0, a1 = APP_X
    # The plinth and the body behind the face.
    cbox(bm, ((a0 + a1) / 2, (0.82 + BACK_Y) / 2, 0.11), (a1 - a0 + 0.06, BACK_Y - 0.82, 0.22), 0.012, dk)
    add_box(bm, ((a0 + a1) / 2, 0.815, 0.05), (a1 - a0 + 0.04, 0.008, 0.035), mat=br)
    add_box(bm, ((a0 + a1) / 2, (0.98 + BACK_Y) / 2, 1.41), (a1 - a0, BACK_Y - 0.98, 2.38), mat=dk)
    # The face: a frame 8 cm deep round the step slots; each slot's back in dark iron, a brass hinge strip at its foot.
    holes = []
    for sx0, sx1, top in STEPS:
        hz = top - STEP_T
        holes.append((sx0 - 0.03, sx1 + 0.03, hz - 0.03, hz + 1.23))
        add_box(bm, ((sx0 + sx1) / 2, 0.976, hz + 0.6), (sx1 - sx0 + 0.06, 0.006, 1.26), mat=ir)
        add_box(bm, ((sx0 + sx1) / 2, FACE_Y + 0.01, hz - 0.04), (sx1 - sx0 + 0.1, 0.03, 0.02), mat=br)
    wall_x(bm, a0, a1, FACE_Y, 0.98, 0.22, CASE[2] + 0.14, holes, dk)
    # Each slot framed in brass, its enamel number under the hinge (the dial's marks carry the same numbers).
    for k, (h0, h1, z0, z1) in enumerate(holes):
        for x in (h0 - 0.012, h1 + 0.012):
            cbox(bm, (x, FACE_Y - 0.006, (z0 + min(z1, CASE[2] + 0.14)) / 2), (0.024, 0.014, min(z1, CASE[2] + 0.14) - z0), 0.004, br)
        if z1 < CASE[2]:
            cbox(bm, ((h0 + h1) / 2, FACE_Y - 0.006, z1 + 0.012), (h1 - h0 + 0.048, 0.014, 0.024), 0.004, br)
        nz = z0 - 0.1
        add_cyl(bm, ((h0 + h1) / 2, FACE_Y, nz), ((h0 + h1) / 2, FACE_Y - 0.012, nz), 0.058, mat=br, seg=20)
        disc_decal(S, ((h0 + h1) / 2, FACE_Y - 0.014, nz), 0.05, R_NUM[k], at, seg=20)
    # Raised panels, pilasters with brass caps dividing the machine into bays, a brass band low and high.
    cbox(bm, (222.85, FACE_Y - 0.01, 1.3), (1.3, 0.02, 1.95), 0.006, wd)
    for x in (222.06, 224.47, a1 - 0.06):
        cbox(bm, (x, FACE_Y - 0.025, 1.41), (0.1, 0.05, 2.38), 0.01, wd)
        cbox(bm, (x, FACE_Y - 0.035, 2.56), (0.13, 0.07, 0.06), 0.01, br)
        cbox(bm, (x, FACE_Y - 0.035, 0.26), (0.13, 0.07, 0.06), 0.01, br)
    add_box(bm, ((a0 + a1) / 2, FACE_Y - 0.008, 0.26), (a1 - a0, 0.016, 0.016), mat=br)
    add_box(bm, ((a0 + 222.0) / 2, FACE_Y - 0.008, 2.52), (222.0 - a0, 0.016, 0.016), mat=br)
    # The tower at the left: it rises past the case to the cornice; three brass wheels on its face, a weight's chain.
    t0, t1 = a0, 222.0
    cbox(bm, ((t0 + t1) / 2, (0.86 + BACK_Y) / 2, (CASE[2] + 3.62) / 2), (t1 - t0, BACK_Y - 0.86, 3.62 - CASE[2]), 0.012, dk)
    for (gx, gz, r, n) in ((220.95, 1.5, 0.27, 30), (221.6, 1.92, 0.17, 20), (221.18, 2.28, 0.13, 16)):
        add_cyl(bm, (gx, FACE_Y - 0.02, gz), (gx, FACE_Y - 0.035, gz), r, mat=br, seg=n * 2)
        for k in range(n):                                                    # teeth
            a = 2 * math.pi * k / n
            add_box(bm, (gx + (r + 0.012) * math.cos(a), FACE_Y - 0.028, gz + (r + 0.012) * math.sin(a)), (0.022, 0.012, 0.018),
                    mat=br, rot=_ry(-a))
        add_cyl(bm, (gx, FACE_Y, gz), (gx, FACE_Y - 0.06, gz), 0.025, mat=ir, seg=10)
        cbox(bm, (gx, FACE_Y - 0.008, gz), (r * 0.5, 0.012, r * 0.5), 0.003, dk)
    add_cyl(bm, (221.88, FACE_Y - 0.03, 2.5), (221.88, FACE_Y - 0.03, 0.9), 0.006, mat=ir, seg=6)   # the weight's line
    add_cyl(bm, (221.88, FACE_Y - 0.05, 0.9), (221.88, FACE_Y - 0.05, 0.62), 0.05, mat=ir, seg=12)  # and its weight
    quad(S, (221.2, FACE_Y - 0.005, 3.22), (0.25, 0, 0), (0, 0, 0.25), R_MARK, at)                # the roundel
    add_torus(bm, (221.2, FACE_Y - 0.01, 3.22), (0, 1, 0), 0.25, 0.012, mat=br, seg=32, rseg=6)
    # The lesson bell at the top of the face's left panel.
    bx, bz = 222.85, 2.12
    add_box(bm, (bx, FACE_Y - 0.04, bz + 0.17), (0.04, 0.08, 0.04), mat=ir)
    add_cyl(bm, (bx, FACE_Y - 0.13, bz + 0.15), (bx, FACE_Y - 0.13, bz + 0.05), 0.02, 0.12, mat=br, seg=20)
    add_sphere(bm, (bx, FACE_Y - 0.13, bz + 0.05), 1.0, mat=br, seg=20, scale=(0.12, 0.12, 0.09))
    add_sphere(bm, (bx + 0.13, FACE_Y - 0.13, bz - 0.02), 0.025, mat=ir, seg=8)                      # its striker
    add_cyl(bm, (bx + 0.13, FACE_Y - 0.13, bz - 0.02), (bx + 0.2, FACE_Y - 0.03, bz - 0.1), 0.006, mat=ir, seg=6)
    cbox(bm, (bx, FACE_Y - 0.012, bz - 0.2), (0.3, 0.01, 0.075), 0.003, br)
    quad(S, (bx, FACE_Y - 0.018, bz - 0.2), (0.13, 0, 0), (0, 0, 0.032), R_BELLPLATE, at)
    # The pawl's foot: a cast-iron block forward on the floor, a toothed brass quadrant beside the lever.
    px, py, pz = PAWL
    cbox(bm, (px, (0.3 + 0.84) / 2, pz / 2), (0.34, 0.54, pz), 0.015, ir)
    for s in (-1, 1):
        add_box(bm, (px + s * 0.05, py, pz + 0.05), (0.02, 0.1, 0.1), mat=ir)
    add_cyl(bm, (px - 0.07, py, pz + 0.05), (px + 0.07, py, pz + 0.05), 0.016, mat=hb, seg=10)
    for k in range(11):                                                      # the toothed quadrant the dog rides
        a = math.radians(-40 + k * 8.0)
        for r, size in ((0.2, (0.012, 0.034, 0.035)), (0.235, (0.012, 0.02, 0.026))):
            p = Vector((px + 0.075, py - r * math.sin(a), pz + 0.05 + r * math.cos(a) - 0.17))
            add_box(bm, p, size, mat=br, rot=_rx(a))
    # The rod: from a crank on the pawl's foot along the floor (in eyes on little posts) to a bell crank at 224.0, up the
    # face to the brake shoe on the dial's ratchet rim.
    rz, ry = 0.07, 0.62
    add_cyl(bm, (px + 0.17, ry, rz), (DIAL[0] - 0.03, ry, rz), 0.016, mat=hb, seg=10)
    for x in (221.4, 222.3, 223.2):
        add_box(bm, (x, ry, rz / 2), (0.03, 0.03, rz), mat=ir)
        add_torus(bm, (x, ry, rz), (1, 0, 0), 0.02, 0.006, mat=br, seg=12, rseg=4)
    vy = 0.79                                                                # the upright runs in front of the plinth
    add_cyl(bm, (DIAL[0], ry, rz), (DIAL[0], vy, rz), 0.016, mat=hb, seg=10)
    add_box(bm, (DIAL[0], vy, rz), (0.06, 0.05, 0.06), mat=ir)                             # the bell crank
    add_cyl(bm, (DIAL[0], vy, rz), (DIAL[0], vy, DIAL[2] - DIAL_R - 0.05), 0.016, mat=hb, seg=10)
    for z in (0.5, 0.85):
        add_box(bm, (DIAL[0], (vy + FACE_Y) / 2, z), (0.05, FACE_Y - vy, 0.02), mat=br)
    add_box(bm, (DIAL[0], vy + 0.02, DIAL[2] - DIAL_R - 0.03), (0.09, 0.06, 0.05), mat=hb)   # the shoe on the rim
    # The dial: a brass bezel, a ratchet rim round it, the enamel face (atlas), its spindle boss.
    dx, dyy, dz = DIAL
    add_cyl(bm, (dx, FACE_Y, dz), (dx, FACE_Y - 0.03, dz), DIAL_R + 0.03, mat=dk, seg=40)
    add_torus(bm, (dx, FACE_Y - 0.032, dz), (0, 1, 0), DIAL_R + 0.005, 0.016, mat=br, seg=40, rseg=6)
    for k in range(40):
        a = 2 * math.pi * k / 40
        add_box(bm, (dx + (DIAL_R + 0.03) * math.cos(a), FACE_Y - 0.02, dz + (DIAL_R + 0.03) * math.sin(a)), (0.026, 0.03, 0.014),
                mat=br, rot=_ry(-a + 0.4))
    disc_decal(S, (dx, FACE_Y - 0.036, dz), DIAL_R - 0.01, R_DIAL, at, seg=40)
    K = Kit()
    hw = K(M['GaugeNeedle'])
    prism(K.bm, [(-0.012, -0.01), (-0.004, DIAL_R - 0.03), (0.004, DIAL_R - 0.03), (0.012, -0.01), (0.0, -0.07)], 'y', -0.004, 0.004, mat=hw)
    add_cyl(K.bm, (0, 0.005, 0), (0, -0.012, 0), 0.03, mat=hw, seg=14)
    K.obj('AttDialHand', coll).location = (dx, FACE_Y - 0.045, dz)
    # The pawl lever: red, worn at the grip, its pivot at its foot, built released (leaning back toward the wall).
    K = Kit()
    rd = K(M['LeverRed'])
    add_cyl(K.bm, (0, 0, 0), (0, 0, PAWL_LEN), 0.018, 0.015, mat=rd, seg=10)
    add_cyl(K.bm, (-0.07, 0, PAWL_LEN), (0.07, 0, PAWL_LEN), 0.024, mat=rd, seg=12)
    add_cyl(K.bm, (-0.035, 0, 0), (0.035, 0, 0), 0.04, mat=rd, seg=14)                         # the boss on the pin
    add_box(K.bm, (0.0, 0.0, -0.05), (0.05, 0.04, 0.09), mat=rd)                               # the dog
    add_box(K.bm, (0.0, 0.05, 0.13), (0.035, 0.03, 0.04), mat=rd)                              # the latch's thumb catch
    bmesh.ops.transform(K.bm, matrix=_rx(math.radians(PAWL_REST)), verts=K.bm.verts)
    K.obj('AttPawl', coll).location = (px, py, pz + 0.05)
    # The steps: hinged boards, built out. Pale beech (worn at the front edge), brass knuckles at the hinge.
    for k, (sx0, sx1, top) in enumerate(STEPS):
        K = Kit()
        bw = K(M['PupilWood'])
        w = sx1 - sx0
        d = STEP_Y[1] - STEP_Y[0]
        cbox(K.bm, (0, -d / 2, STEP_T / 2), (w, d, STEP_T), 0.01, bw)
        for x in (-w / 2 + 0.08, w / 2 - 0.08):
            cbox(K.bm, (x, -d / 2 - 0.05, -0.02), (0.05, d - 0.2, 0.04), 0.006, bw)            # battens under it
        add_cyl(K.bm, (-w / 2 + 0.02, -d + 0.015, STEP_T - 0.012), (w / 2 - 0.02, -d + 0.015, STEP_T - 0.012), 0.014, mat=bw, seg=8)
        for x in (-w / 2 + 0.12, 0.0, w / 2 - 0.12):
            add_cyl(K.bm, (x - 0.06, -0.012, 0.0), (x + 0.06, -0.012, 0.0), 0.016, mat=bw, seg=8)  # knuckles
        K.obj(f'AttStep{k + 1}', coll).location = ((sx0 + sx1) / 2, FACE_Y, top - STEP_T)
    # The case over the steps: a bottom rail flush with the face, posts, a top rail, the glass front and ends, the
    # painted backdrop inside, a soil bar at the tree's foot. It runs on over the gallery's back to 228 on a console.
    c0, c1, cz0, cz1 = CASE
    gz0 = cz0 + 0.14
    cbox(bm, ((c0 + c1) / 2, (0.98 + BACK_Y) / 2, (cz0 + gz0) / 2), (c1 - c0, BACK_Y - 0.98, gz0 - cz0), 0.012, dk)
    cbox(bm, (APP_X[1] + (c1 - APP_X[1]) / 2, (FACE_Y + 0.98) / 2, (cz0 + gz0) / 2), (c1 - APP_X[1], 0.08, gz0 - cz0), 0.01, dk)
    add_box(bm, ((c0 + c1) / 2, FACE_Y - 0.005, gz0 - 0.03), (c1 - c0, 0.01, 0.018), mat=br)
    cbox(bm, ((c0 + c1) / 2, (FACE_Y + BACK_Y) / 2, cz1 - 0.06), (c1 - c0, BACK_Y - FACE_Y, 0.12), 0.012, dk)
    for x in (c0 + 0.04, 225.0 - 1.5, 225.0 + 1.5, c1 - 0.04):
        cbox(bm, (x, CASE_Y[0] + 0.02, (gz0 + cz1 - 0.12) / 2), (0.05 if x in (c0 + 0.04, c1 - 0.04) else 0.025, 0.04, cz1 - 0.12 - gz0),
             0.004, br if x not in (c0 + 0.04, c1 - 0.04) else dk)
    add_box(bm, ((c0 + c1) / 2, CASE_Y[0], (gz0 + cz1 - 0.12) / 2), (c1 - c0 - 0.1, 0.008, cz1 - 0.12 - gz0), mat=gl)
    add_box(bm, ((c0 + c1) / 2, (CASE_Y[0] + CASE_Y[1]) / 2, gz0 + 0.02), (c1 - c0 - 0.1, CASE_Y[1] - CASE_Y[0], 0.04), mat=S(M['PigeonWood']))
    quad(S, ((c0 + c1) / 2, CASE_Y[1] - 0.01, (gz0 + cz1 - 0.12) / 2), ((c1 - c0 - 0.16) / 2, 0, 0), (0, 0, (cz1 - 0.12 - gz0) / 2), R_CASE, at)
    prism(bm, [(FACE_Y + 0.05, cz0), (BACK_Y, cz0), (BACK_Y, cz0 - 0.45)], 'x', c1 - 0.1, c1 - 0.04, mat=dk)   # the console
    # The cornice over the whole machine and the title plate on it; the tower's crest.
    cbox(bm, ((a0 + c1) / 2, (FACE_Y - 0.06 + BACK_Y) / 2, cz1 + 0.07), (c1 - a0 + 0.1, BACK_Y - FACE_Y + 0.06, 0.14), 0.02, dk)
    add_box(bm, ((a0 + c1) / 2, FACE_Y - 0.065, cz1 + 0.02), (c1 - a0 + 0.1, 0.01, 0.02), mat=br)
    tx = 221.75                                             # the title plate, over the tower's end
    cbox(bm, (tx, FACE_Y + 0.02, cz1 + 0.3), (2.5, 0.04, 0.34), 0.01, dk)
    quad(S, (tx, FACE_Y - 0.002, cz1 + 0.3), (1.15, 0, 0), (0, 0, 0.144), R_TITLE, at)
    for x in (tx - 1.22, tx + 1.22):
        add_sphere(bm, (x, FACE_Y - 0.01, cz1 + 0.3), 0.03, mat=br, seg=10)
    # The order era's motto, stencilled on a dark band on the wall over the rest of the machine.
    quad(S, (225.75, BACK_Y - 0.004, cz1 + 0.34), (2.0, 0, 0), (0, 0, 0.1875), R_MOTTO, at)
    # The protective era's notice on the apparatus, screwed on over the left panel, below the bell.
    cbox(bm, (222.85, FACE_Y - 0.026, 1.42), (0.58, 0.012, 0.3), 0.003, S(M['CastIron']))
    quad(S, (222.85, FACE_Y - 0.033, 1.42), (0.27, 0, 0), (0, 0, 0.135), R_NOTICE, at)
    # And a soft mat on the floor under the steps (padded canvas, quilted): low, flat, walked over.
    mx0, mx1 = STEPS[0][0] - 0.1, STEPS[2][1] + 0.08
    cbox(bm, ((mx0 + mx1) / 2, 0.22, 0.015), (mx1 - mx0, 1.14, 0.03), 0.012, S(M["LessonDado"]))
    for k in range(1, 6):
        add_box(bm, (mx0 + (mx1 - mx0) * k / 6, 0.22, 0.03), (0.012, 1.1, 0.004), mat=S(M['PigeonWood']))


def tree(M, coll):
    """The model tree in its case: a straight turned trunk, three tiers of branches in symmetric pairs, a canopy of
    painted wooden leaves. Each part is its own object, its origin where it attaches (the game scales it 0 -> 1)."""
    tx, ty, tz = TREE
    K = Kit()
    w = K(M['PupilWood'])
    add_cyl(K.bm, (0, 0, 0), (0, 0, 0.62), 0.055, 0.03, mat=w, seg=12)
    add_cyl(K.bm, (0, 0, 0), (0, 0, 0.04), 0.09, 0.055, mat=w, seg=12)                    # the root flare
    for z in (0.12, 0.3, 0.48):
        add_torus(K.bm, (0, 0, z), (0, 0, 1), 0.05 - z * 0.035, 0.006, mat=w, seg=14, rseg=4)  # turned rings
    K.obj('AttTreeTrunk', coll).location = (tx, ty, tz)
    tiers = ((0.2, 0.55, 0.15), (0.34, 0.42, 0.13), (0.47, 0.28, 0.1))
    for k, (z, span, rise) in enumerate(tiers):
        K = Kit()
        w = K(M['PupilWood'])
        for s in (-1, 1):
            add_cyl(K.bm, (0, 0, 0), (s * span, 0, rise), 0.022, 0.01, mat=w, seg=8)
            add_cyl(K.bm, (s * span * 0.55, 0, rise * 0.55), (s * span * 0.75, 0, rise * 1.45), 0.011, 0.006, mat=w, seg=6)
        K.obj(f'AttTreeBranch{k + 1}', coll).location = (tx, ty, tz + z)
    K = Kit()
    lf = K(M['LessonLeaf'])
    rnd = random.Random(1325)
    # Leaves: flat painted wooden lozenges in a symmetric dome over the branches (mirrored, as the lesson wants it).
    def lozenge(c, rx, ry, rz, tilt):
        R = _ry(tilt)
        vs = [K.bm.verts.new(Vector(c) + R @ Vector(p)) for p in ((rx, 0, 0), (-rx, 0, 0), (0, ry, 0), (0, -ry, 0), (0, 0, rz), (0, 0, -rz))]
        for a, b, cc in ((0, 2, 4), (2, 1, 4), (1, 3, 4), (3, 0, 4), (2, 0, 5), (1, 2, 5), (3, 1, 5), (0, 3, 5)):
            K.bm.faces.new((vs[a], vs[b], vs[cc])).material_index = lf
    for i in range(46):
        a = rnd.uniform(0, 1)
        x = 0.74 * math.sqrt(a)
        z = rnd.uniform(-0.14, 0.12) * (1 - 0.5 * a) + 0.1 * (1 - a)
        y = rnd.uniform(-0.1, 0.1)
        t = rnd.uniform(-0.6, 0.6)
        for s in ((-1, 1) if x > 0.04 else (1,)):
            lozenge((s * x, y, z), 0.07, 0.012, 0.045, s * t)
    K.obj('AttTreeLeaves', coll).location = (tx, ty, tz + 0.42)


def gallery(S, M, coll):
    """On the gallery: the rail on the camera side, the seedling tray in its glazed case, the dry watering can, the
    door out at 230.6 (its frame behind the lane and a lintel over it; the leaf open beyond)."""
    bm = S.bm
    dk, wd, br, ir, gl, at = S(M['PigeonWood']), S(M['CrateWood']), S(M['Brass']), S(M['CastIron']), S(M['Window']), S(M['LessonAtlas'])
    pl, da = S(M['LessonPlaster']), S(M['LessonDado'])
    g0, g1, gz = GALLERY
    # The rail: slim iron posts, a brass top rail at 0.4 over the deck (below D-17's shoulders), a low middle bar.
    posts = (g0 + 0.06, 228.6, 229.6, 230.4, 231.2, X1 - 0.04)
    for x in posts:
        add_cyl(bm, (x, RAIL_Y, gz), (x, RAIL_Y, gz + 0.4), 0.012, mat=ir, seg=8)
        add_cyl(bm, (x, RAIL_Y, gz), (x, RAIL_Y, gz + 0.015), 0.025, mat=ir, seg=8)
    add_cyl(bm, (g0 + 0.03, RAIL_Y, gz + 0.41), (X1, RAIL_Y, gz + 0.41), 0.016, mat=br, seg=10)
    add_cyl(bm, (g0 + 0.06, RAIL_Y, gz + 0.16), (X1, RAIL_Y, gz + 0.16), 0.007, mat=ir, seg=6)
    # The seedling bench and its glazed case against the back wall.
    s0, s1 = 228.35, 230.3
    sy0, sy1 = 1.0, 1.52
    bz = gz + 0.52
    for x in (s0 + 0.04, s1 - 0.04):
        for y in (sy0 + 0.04, sy1 - 0.04):
            add_box(bm, (x, y, (gz + bz) / 2), (0.035, 0.035, bz - gz), mat=ir)
    cbox(bm, ((s0 + s1) / 2, (sy0 + sy1) / 2, bz - 0.02), (s1 - s0, sy1 - sy0, 0.04), 0.008, wd)
    add_box(bm, ((s0 + s1) / 2, (sy0 + sy1) / 2, gz + 0.12), (s1 - s0 - 0.08, sy1 - sy0 - 0.08, 0.02), mat=wd)   # a low shelf
    quad(S, ((s0 + s1) / 2 - 0.45, sy0 - 0.003, bz - 0.1), (0.2, 0, 0), (0, 0, 0.05), R_SEED, at)
    cbox(bm, ((s0 + s1) / 2 - 0.45, sy0 + 0.002, bz - 0.1), (0.42, 0.006, 0.11), 0.002, wd)
    tz0 = bz
    cbox(bm, ((s0 + s1) / 2, (sy0 + sy1) / 2, tz0 + 0.04), (s1 - s0 - 0.12, sy1 - sy0 - 0.1, 0.08), 0.006, wd)
    add_box(bm, ((s0 + s1) / 2, (sy0 + sy1) / 2, tz0 + 0.075), (s1 - s0 - 0.16, sy1 - sy0 - 0.14, 0.012), mat=dk)   # the soil
    soil = tz0 + 0.081
    hz = bz + 0.5
    for x in (s0 + 0.02, s1 - 0.02):                                          # the case's frame
        for y in (sy0 + 0.02, sy1 - 0.02):
            add_box(bm, (x, y, (bz + hz) / 2), (0.03, 0.03, hz - bz), mat=dk)
    for y in (sy0 + 0.02, sy1 - 0.02):
        add_box(bm, ((s0 + s1) / 2, y, hz), (s1 - s0, 0.03, 0.03), mat=dk)
    add_box(bm, ((s0 + s1) / 2, sy0 + 0.01, (bz + hz) / 2), (s1 - s0 - 0.04, 0.006, hz - bz), mat=gl)
    add_box(bm, ((s0 + s1) / 2, (sy0 + sy1) / 2, hz + 0.01), (s1 - s0 - 0.04, sy1 - sy0, 0.006), mat=gl)
    for x in (s0 + 0.01, s1 - 0.01):
        add_box(bm, (x, (sy0 + sy1) / 2, (bz + hz) / 2), (0.006, sy1 - sy0 - 0.04, hz - bz), mat=gl)
    # The seedlings: three rows, dead and bent over, dry; one place, the pale living shoot (AttShoot).
    rnd = random.Random(2290)
    sw = S(M['LessonPlaster'])                                                # dried to straw
    for r, y in enumerate((1.16, 1.26, 1.36, 1.44)):
        x = s0 + 0.14
        while x < s1 - 0.12:
            if abs(x - SHOOT[0]) < 0.05 and r == 0:
                x += 0.11
                continue
            h = rnd.uniform(0.06, 0.12)
            a = rnd.uniform(0, 2 * math.pi)
            lean = rnd.uniform(0.5, 1.3)
            p0 = Vector((x + rnd.uniform(-0.01, 0.01), y + rnd.uniform(-0.01, 0.01), soil))
            p1 = p0 + Vector((0.2 * h * math.cos(a), 0.2 * h * math.sin(a), h))
            p2 = p1 + Vector((h * lean * 0.7 * math.cos(a), h * lean * 0.7 * math.sin(a), -h * lean * 0.6))
            add_cyl(bm, p0, p1, 0.005, 0.004, mat=sw, seg=3)
            add_cyl(bm, p1, p2, 0.004, 0.003, mat=sw, seg=3)
            add_box(bm, p2 + Vector((0, 0, -0.004)), (0.026, 0.012, 0.004), mat=sw, rot=_rz(a))
            x += rnd.uniform(0.1, 0.12)
    K = Kit()
    sh = K(M['AttShoot'])
    add_cyl(K.bm, (0, 0, 0), (0.006, 0, 0.11), 0.005, 0.0035, mat=sh, seg=6)
    for s in (-1, 1):                                                         # two seed leaves, lifted toward the light
        vs = [K.bm.verts.new(Vector((0.006, 0, 0.11)) + _ry(s * math.radians(-35)) @ Vector(p))
              for p in ((0, 0, 0), (s * 0.022, 0.009, 0.002), (s * 0.04, 0, 0), (s * 0.022, -0.009, 0.002), (s * 0.022, 0, -0.003))]
        for a, b, c in ((0, 1, 2), (0, 2, 3), (0, 4, 1), (1, 4, 2), (2, 4, 3), (3, 4, 0)):
            K.bm.faces.new((vs[a], vs[b], vs[c])).material_index = sh
    K.obj('AttShoot', coll).location = (SHOOT[0], SHOOT[1], soil)
    # The watering can, dry, on the shelf under the bench.
    wx, wy = 229.75, 1.26
    add_cyl(bm, (wx, wy, gz + 0.13), (wx, wy, gz + 0.32), 0.08, mat=ir, seg=14)
    add_cyl(bm, (wx + 0.07, wy, gz + 0.17), (wx + 0.22, wy, gz + 0.33), 0.014, 0.009, mat=ir, seg=8)
    add_torus(bm, (wx - 0.02, wy, gz + 0.34), (0, 1, 0), 0.06, 0.008, mat=ir, seg=14, rseg=4)
    # The door out at 230.6: the cross wall behind the lane (from the jamb back), a lintel over the lane, the head and
    # the jamb's architrave; the leaf open beyond, flat against the jamb's line. A sign over it on the back wall.
    d0, d1 = DOOR_OUT - 0.1, DOOR_OUT + 0.1
    jamb = 0.62
    dtop = gz + DOOR_OUT_H
    add_box(bm, (DOOR_OUT, (jamb + BACK_Y) / 2, (gz + gz + 0.95) / 2), (d1 - d0, BACK_Y - jamb, 0.95), mat=da)
    add_box(bm, (DOOR_OUT, (jamb + BACK_Y) / 2, (gz + 0.95 + CEIL) / 2), (d1 - d0, BACK_Y - jamb, CEIL - gz - 0.95), mat=pl)
    add_box(bm, (DOOR_OUT, (LINTEL_Y + jamb) / 2, (dtop + CEIL) / 2), (d1 - d0, jamb - LINTEL_Y, CEIL - dtop), mat=pl)
    for s in (-1, 1):
        cbox(bm, (DOOR_OUT + s * 0.12, jamb + 0.05, (gz + dtop) / 2 + 0.04), (0.04, 0.1, DOOR_OUT_H + 0.08), 0.008, wd)
        cbox(bm, (DOOR_OUT + s * 0.12, (LINTEL_Y + jamb + 0.1) / 2, dtop + 0.04), (0.04, jamb + 0.1 - LINTEL_Y, 0.08), 0.008, wd)
    lx0, lx1, ly = d1 + 0.03, d1 + 0.84, jamb + 0.03
    for za, zb in ((gz, gz + 0.12), (gz + 0.12, dtop - 0.02)):
        cbox(bm, ((lx0 + lx1) / 2, ly, (za + zb) / 2), (lx1 - lx0, 0.04, zb - za), 0.006, dk)
    for z in (gz + 0.6, gz + 1.35):
        cbox(bm, ((lx0 + lx1) / 2, ly - 0.022, z), (lx1 - lx0 - 0.2, 0.012, 0.6), 0.004, wd)
    add_sphere(bm, (lx1 - 0.07, ly - 0.05, gz + 0.9), 0.028, mat=br, seg=10)
    cbox(bm, (DOOR_OUT - 0.55, BACK_Y - 0.01, dtop + 0.22), (0.52, 0.02, 0.14), 0.004, dk)
    quad(S, (DOOR_OUT - 0.55, BACK_Y - 0.022, dtop + 0.22), (0.24, 0, 0), (0, 0, 0.06), R_EXIT, at)


def speaker(S, M, coll):
    """The horn for the recorded lesson, on the tower's face over the clockwork, turned to the desks. The shared tannoy
    once art/common/VOICE_PROPS_READY exists; the empty AttLessonSpeaker marks the emitter either way."""
    mount = Vector((221.2, 0.86 - 0.002, 2.8))
    mouth = mount + Vector((-0.22, -0.4, -0.12))
    if os.path.exists(os.path.join(COMMON, 'VOICE_PROPS_READY')):
        if COMMON not in sys.path:
            sys.path.insert(0, COMMON)
        import voice_props as VP
        info = VP.tannoy(S, VP.xform(mount, 0.0, 1.25), tilt=12.0, aim=-35.0, conduit=0.5, conduit_dir=0.0)
        mouth = Vector(info['mouth'])
    e = bpy.data.objects.new('AttLessonSpeaker', None)
    e.empty_display_type = 'SPHERE'
    e.empty_display_size = 0.1
    e.location = mouth
    coll.objects.link(e)
