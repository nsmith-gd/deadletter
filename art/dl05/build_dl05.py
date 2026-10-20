"""DL-09 The Child at the Address (built as DL-05): ring C's street, home C-114 and the child's bedroom, D-17's
clips for the scene, and its lore. Called from art/dl01/build_dl01.py (chapter 1 is one level).

Ring C is the bottom of a graded refuge that collapsed: the labour grades' housing, cramped, patched with whatever
could be carried, every door stencilled with its grade (a 4). Pass 3 makes it a street he walks THROUGH, three
depths of it: a ruined row in front of the lane (cut down below his height, so it never hides him), the row he
walks past behind the lane, and ring B's tier above, with stairs between them.

It runs straight on from the DL-08 balcony stair (DL-10 Up Only now arrives here), on a floor at 0:
  - ring C's ledge, open to the cave behind a low lip of rock, and the barricade that seals ring C, with a gap
    under it to crouch through (both where they always were);
  - the street. Behind the lane, the back row: C-102 (chalked GONE UP, a sheet nailed over its plaster), C-104
    (split in two, a plank door 104A cut into it and chalked GONE UP, its window blocked up with odd blocks), a
    cross alley (the neighbourhood's standpipe and the ration queue's post and painted marks at its mouth, steps up
    toward ring B and down toward the lower lanes), C-106 (its door on the alley, chalked GONE UP; on its blank
    face an old "UP IS FOR THEM" in an early hand, half whitewashed, and a later "EVERYONE UP" with an arrow to
    the stairs; a stovepipe through its window), then the flood's three: C-108 (its window dimly lit onto a table still set; its
    door's steps going down into the water; its bell, a brass push with a small amber lamp, on the gate pillar),
    a stepped alley up toward ring B, C-110 (letters jammed in its slot, one sticking out: C110Letter; the junction
    box in front, its lever with a worn black grip), C-112 (boarded, taped, the water-drop mark). In front of the
    lane, the front row, odd numbers, every one cut down or fallen in: garden walls, gates, porches, wall stumps,
    rooms open to the sky (instanced: D5FrontRowA/B/C, linked duplicates), and C-111, which went into the sink
    with the lane. Over the lane washing lines, the street cable of bulbs, the duct run with the gap where PushDuct
    fell. Ring B's tier, its stairs and a few lit windows, and the lift going up, in the haze behind;
  - the flood (DL-09's puzzle): the lane's back half sank along C-108 and C-110 into deep standing water (the
    White's), and at the narrow point the lane went down across its width onto a slab 0.25 under: pushed in
    there, the duct is the bridge. At the far end a cable hangs down into the water from a broken lamp bracket
    (LaneCable, LaneCableTip), fed from the junction box;
  - the square before C-114: the noticeboard (the evacuation notice, the children's drawings of the White), a
    bench, a dry fountain and a standpipe, a swing frame with one swing, ring C's mail slot (MailSlot9), a stair up;
  - C-114, a dollhouse section on the play line: the front step and its door, SHUT (C114FrontDoor, hinged; its
    lever C114DoorHandle and the child's pull-cord C114DoorCord), the hall (the light switch: CurioSwitch,
    HallBulb), the kitchen and living room (CurioRadio, the lamp left on), the child's bedroom (the bed and the
    patched rabbit, the painted window, the photograph of her father in his sorter's apron with her on his
    shoulders, the forwarding terminal and, behind the fallen desk, the growth marks and the tree), the back door.
    Its street wall is C114Facade, which the game fades out when he is inside; the cut edges behind it are
    capped near-black (C114Section);
  - the back door onto a service passage, with the stair up to ring B and the school.

Nothing in ring C is painted red to say "use me" any more (docs/chapter1_pass3_plan.md section 2): what he can
use reads by wear (handled metal polished bright through tired paint: PawlSteel, HandleBlack, Brass), by light
and by form. Red is kept only for real alarm and danger markings.

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y. The full build moves
all of this by OFF4 along x and insert_scenes() by 24 more: game x = these + OFF5 (54).
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
import build_dl03 as dl03
from build_d17 import (add_box, add_cyl, add_sphere, add_torus, add_wedge, rounded_box, emission_material,
                       worn_material, simple_material, smoothstep, SIDES, CLAW_REST_OPEN)

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')

# Shared with the game (game/undelivered/index.html keeps the same numbers). Game x = these + OFF5; game z = -y.
# Pass 3: the street grew by S9 = 9 m between the barricade and C-108 (C-102, C-104, the cross alley, C-106);
# C-108 and everything after it (the flood's puzzle, the square, C-114, the passage) moved right by S9 unchanged.
S9 = 9.0
BACK_Y = 1.0                          # the back-row facades along the lane, and the back walls of C-114 (their faces)
LEDGE = (76.8, 80.0)                  # ring C's ledge, at the foot of the DL-04 balcony stair
LIP = (1.2, 0.34)                     # the rock lip behind the ledge: y, height
BARRICADE = (80.2, 81.0)
GAP = 0.62                            # clear height under the barricade
LANE_C = (81.0, 94.5 + S9)            # the street: from the barricade to C-114's front step
LANE_Y = (-0.85, BACK_Y)              # the lane's front kerb and the back-row facades
TIDE_Z = 1.0                          # the flood's line, one water level: the street, the square, inside C-114
# The new homes before the flood, and the cross alley between them (the neighbourhood's tap and ration queue).
NEW_HOMES = (('102', 81.1, 83.7), ('104', 83.8, 86.2), ('106', 87.4, 90.0))
CROSS = (86.2, 87.4)                  # the cross alley: steps up toward ring B behind, down to the lower lanes in front
TAP = (86.5, 0.74)                    # the standpipe at the cross alley's mouth: x, y
QUEUE_POST = (85.95, 0.66)            # the ration queue's post; its painted marks run back along the lane from it
C106_WIN = 89.3                       # C-106's one window on the lane (its door is on the alley); its blank face carries the graffiti
FRONT_Y = (-0.99, -0.85)              # the lane's front edge (the kerb); the front row stands beyond it, toward -y
# The flood (DL-09's puzzle): the lane's back half sank along C-108 and C-110 into standing water, and at the
# narrow point the whole lane went down across its width. On the play line the lane stays dry up to the narrow
# point; the duct, pushed in there, is the bridge.
WATER_Z = -0.1                        # FloodWater's surface
POOL = (82.95 + S9, 87.6 + S9)        # the water along the back of the lane (y BANK_Y..BACK_Y), C-108's step to C-112
BANK_Y = 0.28                         # the lane's broken back edge along the pool
POOL_BED = -0.9                       # deep: the White's water
DIP = (86.1 + S9, 87.6 + S9, -0.25)   # the narrow point (DIP9): x0, x1, and the sunk slab the duct comes to rest on
DUCT = (84.25 + S9, 85.75 + S9, 0.26, 0.4)   # PushDuct, lying along the lane at y 0: x0, x1, height, depth (y)
DUCT_GRIP = (-0.775, 0.44)            # its strap's grip bar (bare steel, polished): x from the duct's origin, height
HOMES = (('108', 81.1 + S9, 84.05 + S9), ('110', 84.95 + S9, 87.95 + S9), ('112', 88.05 + S9, 90.5 + S9))   # the flood's three
ALLEY = (84.05 + S9, 84.95 + S9)      # a stepped alley up between C-108 and C-110, flooded at its foot
C108_WIN = (81.85 + S9, 0.78, 0.62, 1.58)  # C-108's window, dimly lit: x, width, sill, head (lower than its neighbours')
C108_DOOR = 83.4 + S9                 # its door; its steps go down into the water (the White noses there)
BELL = (82.72 + S9, 0.3, 0.56)        # C108Bell, on the gate pillar at the water's near end: x, button face y, height
WHITE_NOSE = (83.4 + S9, 0.64)        # where the White noses at C-108's step (on the water, x and y)
C110_DOOR = 86.85 + S9
C110_SLOT = (86.85 + S9, 0.98)        # C-110's door slot: x, height (behind the narrow point: the letter slips onto the bridge)
JUNCTION = (85.8 + S9, 0.22, 0.55)    # JunctionBox on the bank by C-110: lever pivot x, box face y, pivot height
CABLE_TOP = (87.72 + S9, 0.6, 2.42)   # LaneCable hangs from the broken lamp bracket here ...
CABLE_TIP = (87.4 + S9, 0.76)         # ... down into the water (LaneCableTip, at WATER_Z)
C112_DOOR = 88.85 + S9
SQUARE = (90.5 + S9, 94.5 + S9)       # the square before C-114
NOTICE = (91.0 + S9, 0.42)            # the noticeboard: x, face y
MAILSLOT9 = (93.75 + S9, 0.45, 0.55)  # ring C's mail slot on its post: x, post centre y, slot height
# C-114, a dollhouse section on the play line: front door in its end wall, the hall, the kitchen and living room,
# the child's bedroom, the back door. Doorways are 0.84 wide (|y| < 0.42), 2.0 high, thresholds 0.02.
FACADE_Y = (-0.8, -0.62)              # C114Facade (the street wall toward the camera); the section cut is at its back
CUT_Y = FACADE_Y[1]
DOOR_HALF, DOOR_H = 0.42, 2.0
FRONT114 = 94.6 + S9                  # the front wall (centre, 0.18 thick) with the front door
STEP114 = (94.12 + S9, 0.04)          # the front step: x0 (to the wall), height
DOOR114 = (FRONT114, DOOR_H, DOOR_HALF)   # x, lintel underside, back jamb
# The front door, shut (C114FrontDoor): hinged on the back jamb at its inner face, it swings in about +Z (Blender;
# +Y in the game) by DOOR_OPEN degrees, its free edge (camera side) going in first. Its lever handle (C114DoorHandle,
# turns about its own x, tip down) is on the free edge; a loop of parcel twine hangs from the lever's tip to a
# wooden toggle at the child's height (C114DoorCord): the family's, so she could let herself in.
DOOR_FACE = FRONT114 - 0.09 + 0.05   # the shut leaf's outer face (5 cm into the reveal)
DOOR_T = 0.045
DOOR_HINGE = (DOOR_FACE + DOOR_T + 0.0025, DOOR_HALF - 0.005)   # the hinge axis: x, y (vertical, from the floor)
DOOR_OPEN = 95.0                      # degrees about +Z, open
HANDLE = (DOOR_FACE - 0.062, -0.34, 0.92)    # the lever's spindle (x: its rose stands proud of the face), y, height
HANDLE_LEN = 0.14                     # the lever points back toward the hinge, along +y
CORD_TOGGLE = 0.56                    # the toggle's height: the Tug clip's reach, 0.21 ahead and 0.13 to his right
KNOCK_X = DOOR_FACE - 0.30            # where he stands to knock and to tug the cord: x ...
KNOCK_Y = HANDLE[1] + HANDLE_LEN + 0.13   # ... and y (-0.07: the game's KNOCK5_Z is +0.07); his right is -y
KNOCK_AT = (DOOR_FACE, KNOCK_Y - 0.22, 0.57)   # the knock lands on the shut door's lock-side panel here
P1 = 96.96 + S9                       # hall | kitchen and living room
DX = 9.9 + S9                         # the bedroom and all after it, moved along x from where they were (90.6 ..)
INNER = (90.6 + DX, DOOR_H, DOOR_HALF)    # living room | bedroom (109.5)
HALL = (FRONT114 + 0.09, P1 - 0.06)
LIVING = (P1 + 0.06, INNER[0] - 0.06)
BEDROOM = (INNER[0] + 0.06, 95.6 + DX - 0.06)
HOME_CEIL = 2.4
UPPER = (2.62, 4.85)                  # the upper floor of the main block (over the hall and living room)
SWITCH = (95.72 + S9, 0.62)           # CurioSwitch on the hall's back wall: x, height
HALL_BULB = (95.85 + S9, 0.25, 2.02)
RADIO_X = 100.0 + S9
BED = (91.0 + DX, 92.5 + DX, 0.42, 0.29)   # x0, x1, top, front edge (y)
TOY = (92.2 + DX, 0.35, 0.42)         # the rabbit's origin (its base)
TOY_SLUMP = (14.0, 42.0, -24.0)       # its node rotation, slumped (Blender XYZ degrees); upright is identity
SHELF = (92.76 + DX, 1.36)            # the shelf and photograph: x, shelf top (clear of the desk's tall hutch once dragged)
TERM_X, SCREEN_Z, SCREEN = 94.7 + DX, 0.95, (0.32, 0.24)
SCREEN_Y = 1.0                        # the screen recess (the game draws the screen) sits in the wall face
READER_Z = 0.72
TERM_FRONT = 0.955                    # the terminal's front face (y); D-17 presents 0.26 m off it
TERM_HOUSING = (94.48 + DX, 94.92 + DX, 0.62, 1.26)
MARKS = (94.15 + DX, 95.25 + DX, 0.25, 1.25)   # the growth marks and the tree: x0, x1, z0, z1 (decal on the wall, stain included)
MARK_Z = (0.862, 0.928, 0.991, 1.064, 1.138)   # the five marks, M 2 to M 6: the first three at or under the flood's line
TREE_Z = (0.33, 0.85)                   # the carved tree, under the line: foot, crown
PAINTED_WINDOW = (91.72 + DX, 1.36, 0.8, 0.7)   # the window painted over the bed: x, z, width, height
DESK_X, DESK_HALF, DESK_TOP = 94.7 + DX, 0.55, 0.55
DESK_Y = 0.62                         # the desk's origin y (centre of its footprint, which runs 0.29 to 0.95)
DESK_TILT = -9.0                      # it leans back against the terminal (degrees about x)
DESK_SIDE_TILT = 2.0                  # and is down on its broken right side (degrees about y; more swings the
                                      # hutch's top right, off the marks' labels)
DESK_HUTCH = 1.22                     # its hutch's top (left end); it hides the marks and the tree
DESK_HANDLE = (-0.585, 0.44)          # its grip bar (bare steel, polished), on its left end: x from the origin, height
DESK_DRAG = 93.6 + DX                 # where it ends up (its left end 0.55 short of this, its right end 0.55 past)
BACK_DOOR = (95.6 + DX, DOOR_H, DOOR_HALF)
END_X = 97.2 + DX
PASSAGE_X1 = 98.5 + DX
STAIR_X = 97.6 + DX                   # the service stair up toward ring B starts here
WORLD_END = 102.0 + DX



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
        import numpy as np
        q = np.array(q.convert('RGBA'))   # decals stay true RGBA: some loaders ignore a palette's transparency
        q[..., 3] = np.where(np.asarray(img)[..., 3] < 3, 0, q[..., 3])   # and what was clear stays clear
        q = Image.fromarray(q, 'RGBA')
    q.save(_tex(name), optimize=True)


def make_textures():
    from PIL import Image, ImageDraw, ImageFilter
    os.makedirs(TEX, exist_ok=True)
    ink, cream, yellow = (26, 24, 20), (222, 212, 184), (196, 168, 60)

    # Door plates: enamel numbers by each door. C-114's has a child's star stuck on it.
    for k, num in enumerate(('108', '110', '112', '114', '102', '104', '106')):
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

    make_photo_father()

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
    make_lore9()
    make_lore3()


def make_growth_marks():
    """The growth marks and the tree, on the wall behind the desk (D5Marks), with the flood's stain painted in
    under them so they layer in the right order. The water took the early years: M 2 and M 3 are under the
    line, blurred, stained and half lifted but still legible; M 4 sits on the line, the stain's edge across it;
    M 5 and M 6 are crisp above it, with the child's star. The tree, scratched into the plaster below the line,
    survived as a carving does: the stain darkens the wall round it and the grooves read pale through it.
    1 px is about 1.07 mm. The terminal hides the middle (TERM_HOUSING), so the marks climb on its left and
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
        a, b = px(x0 + 0.2, z), px(x0 + 0.32, z + rnd.uniform(-0.004, 0.004))
        _line(d, [a, b], graphite, 6, rnd, 1.0, passes=2)
        # The label, in a grown-up's pencil, each written a little askew.
        lab = Image.new('RGBA', (110, 54), (34, 32, 38, 0))                  # the name over the year, kept narrow so the
        ld = ImageDraw.Draw(lab)                                             # fallen hutch's left side covers it
        ld.text((4, 26), f'M {age}', font=_font(32, 'serif'), fill=graphite, anchor='ls')
        ld.text((6, 48), f'R.Y. {year}', font=_font(20, 'sans'), fill=(34, 32, 38, 225), anchor='ls')
        lab = lab.rotate(rnd.uniform(-4, 4), resample=Image.BICUBIC)
        pencil.alpha_composite(lab, (int(a[0] - 98), int(a[1] - 44)))
    sx, sy = px(x0 + 0.32, MARK_Z[-1])                                          # a child's star by the last one
    d.line((sx + 12, sy - 22, sx + 26, sy + 6, sx + 2, sy - 12, sx + 30, sy - 12, sx + 6, sy + 6, sx + 12, sy - 22),
           fill=(70, 90, 170, 220), width=4)
    # Under the line the pencil is softened, faded and in places lifted with the paint.
    zc = z1 - (np.arange(H)[:, None] + 0.5) / ppm
    xc = x0 + (np.arange(W)[None, :] + 0.5) / ppm
    edge = TIDE_Z + 0.004 * np.sin(xc * 37.0) + 0.003 * np.sin(xc * 91.0 + 1.0)
    under = np.clip((edge - zc) / 0.008, 0, 1)                               # 1 well under the line, 0 above it
    noise = _tile_noise(W, H, 14, 5210)
    keep = np.clip(0.76 + 0.35 * (noise - 0.5), 0.58, 0.92)
    for _ in range(40):                                                      # flakes where the paint lifted
        cx_, cy_ = rnd.uniform(0, W * 0.4), rnd.uniform(*sorted(px(x0 + 0.15, TIDE_Z)[1:] + px(x0 + 0.15, 0.8)[1:]))
        r_ = rnd.uniform(3, 9)
        yy, xx = np.ogrid[:H, :W]
        keep = np.where((xx - cx_) ** 2 + (yy - cy_) ** 2 < r_ * r_, keep * 0.45, keep)
    p_sharp = np.asarray(pencil).astype(float)
    p_soft = np.asarray(pencil.filter(ImageFilter.GaussianBlur(1.4))).astype(float)
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
    veil[..., 3] *= 0.25 * under
    img.alpha_composite(Image.fromarray(veil.astype('uint8'), 'RGBA'))
    # The tree: grooves cut into the plaster, pale through the stain.
    grooves = Image.new('RGBA', (W, H), (240, 232, 212, 0))
    d = ImageDraw.Draw(grooves)
    tx, ty = px(x0 + 0.9, TREE_Z[0])
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
    _save(img.filter(ImageFilter.GaussianBlur(0.7)), 'growth_marks.png', 32)


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


def _white(d, ox, oy, s, rnd, variant=0):
    """A child's crayon drawing of the White: a long pale body that wiggles, four little legs with toes, feathery pink
    gills behind the head, and no eyes (two small pits, pressed hard). Head at (ox, oy), body toward +x, s px per unit."""
    grey, pale, pink = (128, 128, 140), (246, 244, 236), (232, 120, 156)
    n = 26
    cl, hw = [], []
    for i in range(n + 1):
        t = i / n
        cl.append((ox + 2.0 * s * t, oy + 0.1 * s * math.sin(3.2 * t * math.pi + variant)))
        hw.append(s * (0.17 * min(1.0, 0.35 + t * 4) * (1 - 0.86 * t ** 1.4)))
    top = [(x, y - w) for (x, y), w in zip(cl, hw)]
    bot = [(x, y + w) for (x, y), w in zip(cl, hw)]
    head = [(ox - 0.12 * s * math.cos(a), oy + 0.17 * s * math.sin(a) * 0.4 + 0.06 * s * math.sin(a)) for a in
            [math.pi / 2 - k * math.pi / 8 for k in range(9)]]
    d.polygon(top + bot[::-1] + head, fill=pale)
    _line(d, top, grey, max(3, int(s * 0.045)), rnd, s * 0.01, passes=2)
    _line(d, bot, grey, max(3, int(s * 0.045)), rnd, s * 0.01, passes=2)
    _line(d, [top[0]] + [(ox - 0.13 * s, oy)] + [bot[0]], grey, max(3, int(s * 0.045)), rnd, s * 0.01, passes=2)
    for k in range(3):                                                      # feathery gills, both sides of the neck
        gx = ox + (0.16 + 0.07 * k) * s
        for sg in (-1, 1):
            base = (gx, cl[2][1] + sg * hw[2] * 0.9)
            tip = (gx - 0.06 * s + 0.04 * s * k, base[1] + sg * (0.2 + 0.03 * k) * s)
            _line(d, [base, tip], pink, max(3, int(s * 0.04)), rnd, s * 0.008, passes=2)
            for j in range(1, 5):                                           # the feathers
                p = (base[0] + (tip[0] - base[0]) * j / 5, base[1] + (tip[1] - base[1]) * j / 5)
                for side in (-1, 1):
                    _line(d, [p, (p[0] + side * 0.04 * s, p[1] + sg * 0.03 * s)], pink, max(2, int(s * 0.02)), rnd, 0, 1)
    for k, t in enumerate((0.22, 0.3, 0.58, 0.66)):                         # four little legs, three toes each
        i = int(t * n)
        x, y = cl[i][0], cl[i][1] + hw[i] * (1 if k % 2 == 0 else 0.6)
        foot = (x - 0.05 * s, y + 0.12 * s)
        _line(d, [(x, y), foot], grey, max(3, int(s * 0.035)), rnd, 0, 2)
        for a in (-0.5, 0.0, 0.5):
            _line(d, [foot, (foot[0] + 0.05 * s * math.sin(a) - 0.02 * s, foot[1] + 0.04 * s * math.cos(a))], grey, max(2, int(s * 0.02)), rnd, 0, 1)
    for dx in (0.0, 0.06):                                                  # no eyes: two pits
        d.ellipse((ox + dx * s - 0.012 * s, oy - 0.07 * s, ox + dx * s + 0.012 * s, oy - 0.046 * s), fill=(170, 168, 176))


def _drawing_paper(w, h, seed, tint=(236, 232, 218)):
    from PIL import Image
    img = Image.new('RGB', (w, h), tint)
    rnd = random.Random(seed)
    px_ = img.load()
    for _ in range(w * h // 40):                                            # paper tooth
        x, y = rnd.randrange(w), rnd.randrange(h)
        r_, g_, b_ = px_[x, y]
        k = rnd.randint(-10, 6)
        px_[x, y] = (r_ + k, g_ + k, b_ + k)
    return img


def make_white_drawing(seed, variant, w=512, h=360, label=True, child=False, house=False):
    """A whole drawing: the White in the water (blue crayon waves), labelled in big uneven capitals."""
    from PIL import ImageDraw
    img = _drawing_paper(w, h, seed)
    d = ImageDraw.Draw(img)
    rnd = random.Random(seed)
    s = w * 0.36
    water = h * 0.5
    for k in range(4):                                                      # the water
        y = water + k * h * 0.11
        _line(d, [(x, y + 7 * math.sin(x * 0.05 + k)) for x in range(0, w + 16, 16)], (70, 110, 190), 6, rnd, 1.0, 1)
    if house:                                                               # a house up on the bank, the White under it
        d.rectangle((w * 0.62, h * 0.18, w * 0.86, h * 0.44), outline=(150, 90, 50), width=6)
        _line(d, [(w * 0.6, h * 0.19), (w * 0.74, h * 0.06), (w * 0.88, h * 0.19)], (150, 90, 50), 6, rnd, 1, 2)
        d.rectangle((w * 0.71, h * 0.3, w * 0.77, h * 0.44), fill=(70, 110, 190))
    if child:                                                               # a stick child on the bank, and an arrow: away
        cx, cy = w * 0.8, h * 0.2
        d.ellipse((cx - 14, cy - 14, cx + 14, cy + 14), outline=(200, 90, 120), width=5)
        _line(d, [(cx, cy + 14), (cx, cy + 62)], (200, 90, 120), 5, rnd, 1, 2)
        _line(d, [(cx - 22, cy + 30), (cx + 22, cy + 30)], (200, 90, 120), 5, rnd, 1, 2)
        _line(d, [(cx, cy + 62), (cx - 16, cy + 90)], (200, 90, 120), 5, rnd, 1, 2)
        _line(d, [(cx, cy + 62), (cx + 16, cy + 90)], (200, 90, 120), 5, rnd, 1, 2)
        _line(d, [(cx + 40, cy + 40), (cx + 90, cy + 40)], (60, 60, 70), 6, rnd, 1, 2)
        _line(d, [(cx + 72, cy + 26), (cx + 90, cy + 40), (cx + 72, cy + 54)], (60, 60, 70), 6, rnd, 1, 2)
    _white(d, w * 0.12, water + h * 0.16, s, rnd, variant)
    if label:
        txt = 'THE WHITE'
        x = w * 0.06
        for k, ch in enumerate(txt):                                        # a child's capitals, each its own size
            if ch == ' ':
                x += 18
                continue
            f = _font(int(rnd.uniform(34, 46)), 'sans-bold')
            d.text((x, h * 0.13 + rnd.uniform(-6, 6)), ch, font=f, fill=(60, 70, 150), anchor='lm')
            x += rnd.uniform(28, 36)
    return img


def make_lore9():
    """The square's noticeboard (the evacuation notice and the children's drawings of the White, pinned low, at their
    height), one more drawing for the board's leg, and C-114's name card: a child's sun and an M."""
    from PIL import Image, ImageDraw, ImageFilter
    ink, cream = (26, 24, 20), (222, 212, 184)
    W, H = 1024, 720                                                        # the board's face, 1.0 x 0.7 m
    img = Image.new('RGB', (W, H), (128, 92, 58))
    rnd = random.Random(9100)
    d = ImageDraw.Draw(img)
    for _ in range(9000):                                                   # cork
        x, y = rnd.randrange(W), rnd.randrange(H)
        c = rnd.choice(((104, 72, 44), (150, 110, 70), (92, 64, 40), (160, 122, 80)))
        d.ellipse((x - 1.5, y - 1.5, x + 1.5, y + 1.5), fill=c)
    for _ in range(26):                                                     # old pin holes and torn corners
        x, y = rnd.randrange(W), rnd.randrange(H)
        d.ellipse((x - 2, y - 2, x + 2, y + 2), fill=(40, 28, 18))
        if rnd.random() < 0.4:
            d.polygon([(x, y), (x + rnd.uniform(8, 22), y + rnd.uniform(-4, 4)), (x + rnd.uniform(0, 8), y + rnd.uniform(8, 18))],
                      fill=(196, 188, 164))

    def pin(x, y, col=(196, 196, 200)):
        d.ellipse((x - 7, y - 7, x + 7, y + 7), fill=(30, 30, 30))
        d.ellipse((x - 6, y - 8, x + 6, y + 4), fill=col)

    def paste(card, x, y, ang, pins=((0.5, 0.05),)):
        card = card.convert('RGBA').rotate(ang, resample=Image.BICUBIC, expand=True)
        img.paste(card, (int(x), int(y)), card)
        cw, ch = card.size
        for u, v in pins:
            pin(x + cw * u, y + ch * v + 8)
    # The evacuation notice, high on the board where the grown-ups put it.
    note = Image.new('RGB', (420, 470), (214, 206, 180))
    nd = ImageDraw.Draw(note)
    nd.rectangle((10, 10, 410, 460), outline=ink, width=4)
    nd.text((210, 46), 'REFUGE COUNCIL', font=_font(34), fill=ink, anchor='mm')
    nd.line((34, 76, 386, 76), fill=ink, width=3)
    nd.text((210, 110), 'NOTICE TO THE', font=_font(30, 'mono-bold'), fill=ink, anchor='mm')
    nd.text((210, 146), 'RESIDENTS OF RING C', font=_font(28, 'mono-bold'), fill=ink, anchor='mm')
    for k, line in enumerate(('The ring is to be cleared.', 'All residents to ring B', 'by the north stair.', 'One bag each.',
                              'Leave doors unlocked.')):
        nd.text((36, 188 + k * 34), line, font=_font(25, 'mono'), fill=ink, anchor='lm')
    nd.text((210, 382), 'KEEP OUT OF THE WATER', font=_font(27, 'mono-bold'), fill=ink, anchor='mm')
    nd.text((210, 430), 'R.Y. 42', font=_font(30, 'mono-bold'), fill=ink, anchor='mm')
    stamp = Image.new('RGBA', (300, 90), (0, 0, 0, 0))                     # SEALED, stamped over it a year later
    sd = ImageDraw.Draw(stamp)
    sd.rectangle((4, 4, 296, 86), outline=(40, 52, 96, 200), width=6)
    sd.text((150, 46), 'SEALED R.Y. 43', font=_font(34, 'mono-bold'), fill=(40, 52, 96, 200), anchor='mm')
    stamp = stamp.rotate(16, resample=Image.BICUBIC, expand=True)
    note.paste(stamp, (70, 230), stamp)
    note = _age(note, 9101, 1.2)
    paste(note, 40, 18, 1.5, pins=((0.08, 0.02), (0.9, 0.02)))
    # A card about a lost cat, gone with the rest.
    cat = Image.new('RGB', (230, 170), (226, 220, 196))
    cd = ImageDraw.Draw(cat)
    cd.text((115, 34), 'LOST', font=_font(40), fill=ink, anchor='mm')
    cd.text((115, 84), 'grey cat, "Button"', font=_font(19, 'sans'), fill=ink, anchor='mm')
    cd.text((115, 116), 'please ask at C-110', font=_font(19, 'sans'), fill=ink, anchor='mm')
    cd.text((115, 146), 'R.Y. 42', font=_font(17, 'mono'), fill=ink, anchor='mm')
    paste(_age(cat, 9102, 0.9), 500, 40, -4)
    # The children's drawings, low down, at their height; one has slipped and hangs by a corner.
    for k, (x, y, ang, kw) in enumerate(((470, 300, 6, {}), (740, 250, -5, {'child': True}), (90, 476, -8, {'house': True}),
                                         (560, 470, 3, {'label': False}))):
        dr = make_white_drawing(9110 + k, 0.7 * k, w=300, h=212, **kw)
        paste(_age(dr, 9120 + k, 0.5), x, y, ang, pins=((0.5, 0.03),) if k != 3 else ((0.05, 0.04),))
    _save(img.filter(ImageFilter.GaussianBlur(0.6)), 'noticeboard.png', 64)
    _save(_age(make_white_drawing(9130, 2.1, w=384, h=270, child=False), 9131, 0.6), 'white_drawing.png', 40)

    # C-114's name card, in a child's hand: a sun with a face, an M, flowers.
    w, h = 320, 200
    card = _drawing_paper(w, h, 9140, tint=(232, 226, 204))
    d2 = ImageDraw.Draw(card)
    r2 = random.Random(9141)
    d2.rectangle((4, 4, w - 4, h - 4), outline=(150, 140, 120), width=3)
    sx, sy = 74, 78
    d2.ellipse((sx - 34, sy - 34, sx + 34, sy + 34), fill=(244, 200, 60))
    for k in range(10):
        a = k * math.pi / 5
        _line(d2, [(sx + 42 * math.cos(a), sy + 42 * math.sin(a)), (sx + 60 * math.cos(a), sy + 60 * math.sin(a))], (236, 170, 40), 6, r2, 1, 2)
    d2.ellipse((sx - 14, sy - 10, sx - 6, sy - 2), fill=(170, 100, 30))
    d2.ellipse((sx + 6, sy - 10, sx + 14, sy - 2), fill=(170, 100, 30))
    d2.arc((sx - 16, sy - 10, sx + 16, sy + 18), 20, 160, fill=(170, 100, 30), width=4)
    _line(d2, [(160, 150), (176, 52), (204, 118), (232, 50), (250, 150)], (60, 80, 160), 11, r2, 1.5, 2)   # M
    for fx in (40, 120, 290):
        _line(d2, [(fx, 196), (fx + 3, 168)], (60, 120, 60), 4, r2, 0.5, 1)
        for a in range(0, 360, 72):
            ra = math.radians(a)
            d2.ellipse((fx + 3 + 8 * math.cos(ra) - 5, 162 + 8 * math.sin(ra) - 5, fx + 3 + 8 * math.cos(ra) + 5, 162 + 8 * math.sin(ra) + 5),
                       fill=(226, 120, 150))
    _save(_age(card, 9142, 0.5), 'namecard114.png', 40)


def _brush_text(d, text, x, y, size, fill, rnd, jitter=4.0, spacing=0.92, kind='sans-bold', wobble=5.0):
    """Hand-painted capitals: each letter its own size and tilt, the baseline wandering; drawn at (x, y) left-middle."""
    from PIL import Image, ImageDraw
    for ch in text:
        if ch == ' ':
            x += size * 0.45
            continue
        s = int(size * rnd.uniform(0.86, 1.12))
        f = _font(s, kind)
        L = Image.new('RGBA', (int(s * 1.6), int(s * 1.6)), fill[:3] + (0,))
        ImageDraw.Draw(L).text((s * 0.8, s * 0.8), ch, font=f, fill=fill, anchor='mm')
        L = L.rotate(rnd.uniform(-wobble, wobble), resample=Image.BICUBIC)
        d.alpha_composite(L, (int(x - s * 0.8 + s * 0.4), int(y - s * 0.8 + rnd.uniform(-jitter, jitter))))
        x += s * spacing * (0.78 if ch in 'I' else 1.0)
    return x


def _drips(img, rnd, col, n, x0, x1, y0, y1, lmax=40):
    from PIL import ImageDraw
    d = ImageDraw.Draw(img)
    for _ in range(n):
        x, y = rnd.uniform(x0, x1), rnd.uniform(y0, y1)
        ln = rnd.uniform(6, lmax)
        d.line((x, y, x + rnd.uniform(-1, 1), y + ln), fill=col, width=rnd.randint(2, 4))
        d.ellipse((x - 2.5, y + ln - 2, x + 2.5, y + ln + 3), fill=col)


def _wear_alpha(img, rnd, keep=(0.55, 1.0), cells=10, seed=0):
    """Paint worn off a wall: the alpha broken up by blotchy noise (keep: the alpha's range, worst to best)."""
    import numpy as np
    from PIL import Image
    a = np.asarray(img).astype(float)
    h, w = a.shape[:2]
    n = _tile_noise(w, h, cells, seed or rnd.randint(0, 9999))
    fine = _tile_noise(w, h, cells * 6, (seed or 1) + 7, octaves=2)
    k = np.clip(keep[0] + (keep[1] - keep[0]) * (0.6 * n + 0.4 * fine) * 1.4 - 0.2, 0, 1)
    a[..., 3] *= k
    img.paste(Image.fromarray(np.clip(a, 0, 255).astype('uint8'), 'RGBA'))
    return img


def make_lore3():
    """Ring C as the bottom of a graded refuge (pass 3): the grade stencilled on the doors, the chalk marks of the
    families that went up, the slogans of two times, the ration queue, the standpipe's plate, the new homes' plates."""
    from PIL import Image, ImageDraw, ImageFilter
    ink, cream = (26, 24, 20), (222, 212, 184)
    paint = (214, 206, 182)
    # The grade, stencilled on every door in the labour rows by the housing office: a 4 in a ring, the bridges of
    # the stencil left in, overspray and a drip.
    w = h = 256
    img = Image.new('RGBA', (w, h), paint + (0,))
    d = ImageDraw.Draw(img)
    rnd = random.Random(5800)
    d.ellipse((22, 22, 234, 234), outline=paint + (235,), width=18)
    d.text((128, 132), '4', font=_font(170, 'mono-bold'), fill=paint + (235,), anchor='mm')
    for x0_, y0_, x1_, y1_ in ((122, 10, 134, 40), (122, 216, 134, 246), (92, 120, 160, 132)):   # the stencil's bridges
        d.rectangle((x0_, y0_, x1_, y1_), fill=paint + (0,))
    for _ in range(260):
        a_, rr = rnd.uniform(0, 2 * math.pi), rnd.uniform(100, 128)
        x, y = 128 + rr * math.cos(a_), 128 + rr * math.sin(a_)
        s_ = rnd.uniform(0.5, 1.6)
        d.ellipse((x - s_, y - s_, x + s_, y + s_), fill=paint + (rnd.randint(40, 150),))
    _drips(img, rnd, paint + (170,), 3, 60, 200, 200, 230, 28)
    img = _wear_alpha(img.filter(ImageFilter.GaussianBlur(0.8)), rnd, keep=(0.5, 1.0), cells=6, seed=5801)
    _save(img, 'grade4.png', 16)

    # GONE UP, chalked on the doors by whoever was left, as each family went: the date, an arrow, a tally of how many.
    W3, H3 = 768, 256
    img = Image.new('RGBA', (W3, H3), (236, 232, 222, 0))
    d = ImageDraw.Draw(img)
    chalk = (236, 232, 222, 225)
    for k, (date, n) in enumerate((('R.Y. 41', 4), ('R.Y. 42', 3), ('41  -  6th', 5))):
        rnd = random.Random(5810 + k)
        ox = 256 * k
        _brush_text(img, 'GONE UP', ox + 18, 64, 52, chalk, rnd, jitter=3, spacing=0.86, kind='sans', wobble=4)
        _brush_text(img, date, ox + 30, 128, 36, chalk, rnd, jitter=2, spacing=0.82, kind='sans', wobble=3)
        ax = ox + 222                                                            # the arrow, up
        _line(d, [(ax, 210), (ax + 2, 40)], chalk, 6, rnd, 1.2, passes=2)
        _line(d, [(ax - 22, 70), (ax + 2, 38), (ax + 24, 68)], chalk, 6, rnd, 1.2, passes=2)
        for t in range(n):                                                       # the tally: who went
            tx = ox + 34 + 18 * t
            if t == 4:
                _line(d, [(ox + 26, 214), (ox + 104, 176)], chalk, 5, rnd, 1.0, 2)
            else:
                _line(d, [(tx, 172), (tx + 3, 218)], chalk, 5, rnd, 1.0, 2)
    import numpy as np
    a = np.asarray(img).astype(float)
    grain = np.random.default_rng(5819).random(a.shape[:2])
    a[..., 3] *= np.clip(0.45 + 0.7 * grain, 0, 1)                             # chalk on a rough door: broken strokes
    _save(Image.fromarray(a.astype('uint8'), 'RGBA').filter(ImageFilter.GaussianBlur(0.6)), 'goneup.png', 16)

    # The two slogans, one atlas: above, UP IS FOR THEM, brushed long ago in a careful early hand, faded, a patch of
    # whitewash over half of it that never quite covered it; below, EVERYONE UP, later, quick and big, with an
    # arrow to the stairs.
    W2, H2 = 1024, 512
    img = Image.new('RGBA', (W2, H2), (0, 0, 0, 0))
    rnd = random.Random(5830)
    old = Image.new('RGBA', (W2, 256), (58, 42, 32, 0))           # tar-black, not red: red is for danger only
    od = ImageDraw.Draw(old)
    _brush_text(old, 'UP IS FOR THEM', 30, 132, 104, (58, 42, 32, 245), rnd, jitter=3, spacing=0.78, kind='serif', wobble=2)
    old = _wear_alpha(old.filter(ImageFilter.GaussianBlur(1.0)), rnd, keep=(0.45, 1.0), cells=8, seed=5831)
    wash = Image.new('RGBA', (W2, 256), (190, 186, 170, 0))                      # the whitewash, over FOR THEM
    wd = ImageDraw.Draw(wash)
    for k in range(26):
        y = rnd.uniform(40, 220)
        x = rnd.uniform(470, 560)
        wd.line((x, y, x + rnd.uniform(380, 480), y + rnd.uniform(-10, 10)), fill=(196, 192, 176, rnd.randint(60, 110)), width=rnd.randint(18, 34))
    wash = _wear_alpha(wash.filter(ImageFilter.GaussianBlur(2.0)), rnd, keep=(0.2, 0.7), cells=5, seed=5832)
    old.alpha_composite(wash)
    img.alpha_composite(old, (0, 0))
    new = Image.new('RGBA', (W2, 256), (226, 222, 206, 0))
    nd = ImageDraw.Draw(new)
    white = (226, 222, 206, 240)
    _brush_text(new, 'EVERYONE UP', 128, 128, 104, white, rnd, jitter=7, spacing=0.8, kind='sans-bold', wobble=6)
    _line(nd, [(130, 150), (36, 150)], white, 16, rnd, 2, passes=2)              # the arrow: left, to the alley, and up
    _line(nd, [(36, 150), (36, 40)], white, 16, rnd, 2, passes=2)
    _line(nd, [(8, 74), (36, 32), (64, 74)], white, 16, rnd, 2, passes=2)
    _drips(new, rnd, white[:3] + (200,), 14, 160, 980, 160, 200, 60)
    new = _wear_alpha(new.filter(ImageFilter.GaussianBlur(0.9)), rnd, keep=(0.7, 1.0), cells=9, seed=5833)
    img.alpha_composite(new, (0, 256))
    _save(img, 'graffiti.png', 32)

    # The ration queue's tin sign on its post: enamel, the office's stencil, a grade's day, chalk under it.
    img = Image.new('RGB', (480, 400), (196, 186, 150))
    d = ImageDraw.Draw(img)
    d.rectangle((8, 8, 472, 392), outline=ink, width=8)
    d.text((240, 60), 'RATIONS', font=_font(72), fill=ink, anchor='mm')
    d.line((40, 112, 440, 112), fill=ink, width=5)
    d.text((240, 160), 'QUEUE HERE', font=_font(46, 'mono-bold'), fill=ink, anchor='mm')
    d.text((240, 222), 'GRADE 4 - TUES', font=_font(38, 'mono-bold'), fill=ink, anchor='mm')
    d.text((240, 272), 'CARDS IN HAND', font=_font(30, 'mono'), fill=ink, anchor='mm')
    rnd = random.Random(5840)
    _line(d, [(60, 330), (200, 322)], (236, 232, 222), 5, rnd, 1, 2)           # chalk under it: halved, and halved again
    d.text((70, 350), '1/2', font=_font(34, 'sans'), fill=(232, 228, 214), anchor='lm')
    d.text((250, 352), '1/4', font=_font(34, 'sans'), fill=(232, 228, 214), anchor='lm')
    _line(d, [(240, 330), (330, 372)], (232, 228, 214), 4, rnd, 1, 2)
    for x in (24, 456):
        d.ellipse((x - 8, 192, x + 8, 208), fill=(60, 52, 40))
    _save(_age(img, 5841, 1.1), 'ration_sign.png', 32)

    # The queue's marks, painted along the back of the lane: a bar and a number for each place, worn by feet.
    img = Image.new('RGBA', (1024, 112), (222, 214, 160, 0))
    d = ImageDraw.Draw(img)
    rnd = random.Random(5850)
    col = (222, 214, 160, 225)
    for k in range(7):
        x = 980 - k * 146
        d.rectangle((x - 6, 10, x + 6, 102), fill=col)
        d.text((x - 50, 56), str(k + 1), font=_font(58, 'mono-bold'), fill=col, anchor='mm')
    img = _wear_alpha(img.filter(ImageFilter.GaussianBlur(0.8)), rnd, keep=(0.25, 0.9), cells=16, seed=5851)
    _save(img, 'queue_marks.png', 16)

    # The standpipe's plate.
    img = Image.new('RGB', (256, 176), (36, 58, 80))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((5, 5, 251, 171), radius=14, outline=cream, width=6)
    d.text((128, 52), 'STANDPIPE 3', font=_font(30), fill=cream, anchor='mm')
    d.text((128, 98), 'GRADE 4', font=_font(30, 'mono-bold'), fill=cream, anchor='mm')
    d.text((128, 140), '2 BUCKETS', font=_font(24, 'mono'), fill=cream, anchor='mm')
    _save(_age(img, 5860, 0.9), 'tap_sign.png', 16)

    # 104A: painted on the plank door that was cut into C-104 when it was split.
    img = Image.new('RGBA', (256, 112), (226, 220, 196, 0))
    rnd = random.Random(5870)
    _brush_text(img, '104A', 20, 58, 72, (226, 220, 196, 235), rnd, jitter=4, spacing=0.84, wobble=5)
    _drips(img, rnd, (226, 220, 196, 190), 4, 30, 220, 80, 96, 20)
    _save(img.filter(ImageFilter.GaussianBlur(0.7)), 'plate_c104a.png', 16)


def make_photo_father():
    """The photograph in C-114: her father in his sorter's apron, just off the night shift, with Mara on his
    shoulders holding the rabbit; behind them the wall of their street with her crooked tree chalked on it. Sepia,
    vignetted, a bent corner. Mid-greys: it reads small, on a shelf and in the hall."""
    from PIL import Image, ImageDraw, ImageFilter
    w, h = 300, 380
    g = Image.new('L', (w, h), 120)
    d = ImageDraw.Draw(g)
    for y in range(h):                                                      # wall, then the lane's flags
        d.line((0, y, w, y), fill=int(132 - 26 * (y / h)) if y < 318 else int(150 - 40 * ((y - 318) / 62)))
    for y in range(318, h, 14):
        d.line((0, y, w, y), fill=118)
    d.rectangle((228, 40, 300, 318), fill=96)                                # a door's dark beside them
    d.rectangle((236, 50, 292, 160), outline=82, width=3)
    tree = ImageDraw.Draw(g)

    def chalk(pts, weight):
        tree.line(pts, fill=214, width=max(2, int(5 * weight)), joint='curve')
    _crooked_tree(chalk, 56, 300, 200)
    # Her father, standing square to the camera: boots, work trousers, a shirt with the sleeves rolled, the sorter's
    # apron over it (pale canvas, a bib, two deep pockets, letters in one, the grade stencilled on it), a cap. Mara
    # sits on his shoulders, behind his head: her hands on his cap, her legs down over his shoulders, his hands round
    # her ankles, the rabbit in the crook of her arm.
    cx = 158
    d.polygon([(cx - 34, 318), (cx - 14, 318), (cx - 10, 252), (cx - 30, 250)], fill=46)          # legs
    d.polygon([(cx + 14, 318), (cx + 36, 318), (cx + 32, 250), (cx + 10, 252)], fill=44)
    d.ellipse((cx - 42, 310, cx - 8, 326), fill=30)                                                  # boots
    d.ellipse((cx + 10, 310, cx + 44, 326), fill=30)
    d.polygon([(cx - 46, 152), (cx + 46, 152), (cx + 48, 256), (cx - 48, 256)], fill=62)            # shirt, body
    # Mara first (he stands in front of her): her body and head above his shoulders.
    d.polygon([(cx - 21, 104), (cx + 21, 104), (cx + 17, 60), (cx - 17, 60)], fill=182)            # her dress
    d.ellipse((cx - 15, 20, cx + 15, 58), fill=38)                                                   # her hair
    d.ellipse((cx - 10, 30, cx + 10, 56), fill=164)                                                  # her face
    d.line((cx - 18, 66, cx - 20, 98), fill=160, width=7)                                            # her arms, down to his cap
    d.line((cx + 18, 66, cx + 16, 98), fill=160, width=7)
    d.ellipse((cx + 16, 62, cx + 36, 82), fill=206)                                                  # the rabbit, in her arm
    d.ellipse((cx + 19, 44, cx + 25, 66), fill=206)
    d.ellipse((cx + 27, 46, cx + 33, 68), fill=206)
    # His head, in front of her.
    d.ellipse((cx - 19, 106, cx + 19, 148), fill=134)                                                # his face
    d.chord((cx - 21, 96, cx + 21, 128), 180, 360, fill=42)                                          # cap
    d.rectangle((cx - 23, 110, cx + 25, 115), fill=42)
    d.arc((cx - 9, 128, cx + 9, 140), 20, 160, fill=80, width=2)                                    # smiling
    for sx in (-1, 1):
        d.ellipse((cx + sx * 18 - 5, 94, cx + sx * 18 + 5, 104), fill=162)                         # her hands on his cap
    # The apron over his shirt.
    d.polygon([(cx - 36, 168), (cx + 36, 168), (cx + 42, 292), (cx - 42, 292)], fill=170)           # long, pale
    d.rectangle((cx - 22, 150, cx + 22, 170), fill=166)                                              # its bib
    d.line((cx - 22, 152, cx - 32, 150), fill=152, width=4)                                          # the straps
    d.line((cx + 22, 152, cx + 32, 150), fill=152, width=4)
    for px in (cx - 32, cx + 4):                                                                     # deep pockets
        d.rectangle((px, 212, px + 28, 252), outline=134, width=3)
    d.polygon([(cx + 8, 210), (cx + 28, 204), (cx + 30, 216), (cx + 10, 222)], fill=212)             # letters in one
    d.polygon([(cx + 12, 206), (cx + 26, 198), (cx + 28, 208), (cx + 14, 214)], fill=200)
    d.text((cx, 188), '4', font=_font(18, 'mono-bold'), fill=122, anchor='mm')                     # the grade, stencilled on it
    # Her legs down over his shoulders, his hands round her ankles.
    d.polygon([(cx - 24, 116), (cx - 12, 118), (cx - 30, 178), (cx - 42, 174)], fill=156)           # pale socks
    d.polygon([(cx + 12, 118), (cx + 24, 116), (cx + 42, 174), (cx + 30, 178)], fill=156)
    d.ellipse((cx - 48, 172, cx - 28, 186), fill=34)                                                 # her shoes
    d.ellipse((cx + 28, 172, cx + 48, 186), fill=34)
    for sx in (-1, 1):                                                                               # his arms, up to her ankles
        d.line((cx + sx * 44, 158, cx + sx * 56, 196, cx + sx * 42, 172), fill=60, width=14, joint='curve')
        d.ellipse((cx + sx * 40 - 8, 162, cx + sx * 40 + 8, 178), fill=126)
    g = g.filter(ImageFilter.GaussianBlur(1.4))
    rnd = random.Random(530)
    px_ = g.load()
    for y in range(h):
        for x in range(w):
            r2 = ((x - w / 2) / (w / 2)) ** 2 + ((y - h / 2) / (h / 2)) ** 2
            px_[x, y] = max(0, min(255, int(px_[x, y] * (1.0 - 0.36 * r2) + rnd.uniform(-5, 5))))
    photo = Image.merge('RGB', [g.point(lambda v: min(255, int(v * 1.08 + 18))), g.point(lambda v: int(v * 0.94 + 10)),
                                g.point(lambda v: int(v * 0.74))])
    card = Image.new('RGB', (w + 36, h + 36), (214, 204, 182))
    card.paste(photo, (18, 18))
    d = ImageDraw.Draw(card)
    d.line((w + 36 - 56, 0, w + 36, 52), fill=(186, 176, 152), width=3)     # a bent corner
    d.text((24, h + 24), 'M. & Dad, after nights', font=_font(13, 'sans'), fill=(110, 100, 84), anchor='lm')   # pencil, on the border
    _save(_age(card, 531, 0.8), 'photo.png', 48)


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
    # Pass 2: the street, the bell, the house's section.
    m['sectioncap'] = simple_material('SectionCap', (0.012, 0.011, 0.01), 0.95)
    m['hallbulb9'] = emission_material('HallBulbGlow', (1.0, 0.82, 0.55), 0.0)
    m['belllamp'] = emission_material('C108BellLamp', (1.0, 0.55, 0.16), 0.0)     # pass 3: amber, a small lamp over a brass push
    m['scum'] = simple_material('FloodScum', (0.09, 0.095, 0.075), 0.9)
    m['glass'] = simple_material('DirtyGlass', (0.03, 0.035, 0.035), 0.25, metallic=0.2)
    m['plasterA'] = worn_material('RingPlasterA', base=(0.2, 0.22, 0.22), dirt=(0.1, 0.1, 0.09),
                                  chip=(0.13, 0.12, 0.1), rough=0.9, chip_rough=0.85, metallic=0.0)
    m['plasterB'] = worn_material('RingPlasterB', base=(0.3, 0.2, 0.17), dirt=(0.15, 0.1, 0.08),
                                  chip=(0.2, 0.16, 0.13), rough=0.9, chip_rough=0.85, metallic=0.0)
    m['slate'] = worn_material('RoofSlate', base=(0.045, 0.05, 0.055), dirt=(0.03, 0.03, 0.03),
                               chip=(0.08, 0.08, 0.075), rough=0.7, chip_rough=0.8, metallic=0.0)
    m['living'] = worn_material('LivingPaint', base=(0.3, 0.27, 0.2), dirt=(0.16, 0.13, 0.09),
                                chip=(0.22, 0.19, 0.14), rough=0.85, chip_rough=0.9, metallic=0.0)
    m['enamel'] = bpy.data.materials.get('TeaEnamel') or simple_material('TeaEnamel', (0.58, 0.55, 0.47), 0.35)
    # Pass 3: what he can use reads by wear, not red. A black grip worn back to bright steel where hands went
    # (HandleBlack, new), and bare steel polished by use (PawlSteel, the cage's: the same name and numbers).
    m['handleblack'] = bpy.data.materials.get('HandleBlack') or worn_material(
        'HandleBlack', base=(0.02, 0.02, 0.018), dirt=(0.035, 0.03, 0.024), chip=(0.55, 0.53, 0.5), rough=0.5, chip_rough=0.22,
        metallic=0.55, dust=(0.06, 0.058, 0.05), chip_scale=45.0, chip_amount=0.58, dust_amount=0.3)
    m['pawlsteel'] = m.get('pawlsteel') or bpy.data.materials.get('PawlSteel') or worn_material(
        'PawlSteel', base=(0.3, 0.29, 0.27), dirt=(0.08, 0.06, 0.04), chip=(0.55, 0.53, 0.5), rough=0.4, chip_rough=0.3, metallic=0.85)
    for key, name, args in (('iron', 'CastIron', ((0.035, 0.034, 0.032), (0.05, 0.03, 0.018), (0.13, 0.12, 0.1), 0.75, 0.45, 0.5)),
                            ('brass', 'Brass', None), ('copper', 'Copper', None), ('tag', 'ReflectTag', None)):
        if key not in m:                                       # shared materials, made by other scenes in the full build
            mat = bpy.data.materials.get(name)
            if mat is None and args:
                mat = worn_material(name, base=args[0], dirt=args[1], chip=args[2], rough=args[3], chip_rough=args[4], metallic=args[5])
            elif mat is None:
                mat = simple_material(name, (0.45, 0.32, 0.12), 0.45, metallic=0.8)
            m[key] = mat


# --- building kit -----------------------------------------------------------

I4 = Matrix.Identity(4)


class Batch:
    """Static geometry merged into one object: one draw call per material, however many parts."""
    def __init__(self, m, alias=None):
        self.m, self.bm, self.mats = m, bmesh.new(), []
        self.alias = alias or {}                       # material keys folded into others, to keep its draw calls down

    def __call__(self, key):
        key = self.alias.get(key, key) if isinstance(key, str) else key
        mat = self.m[key] if isinstance(key, str) else key
        for i, x in enumerate(self.mats):
            if x == mat:
                return i
        self.mats.append(mat)
        return len(self.mats) - 1

    def done(self, name, coll, sharp=35):
        if not len(self.bm.verts):
            self.bm.free()
            return None
        return _obj(name, self.bm, self.mats, coll, sharp=sharp)


def _merge(dst, src):
    me = bpy.data.meshes.new('_merge')
    src.to_mesh(me)
    src.free()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)


def cbox(bm, center, size, b=0.012, mat=0, rot=None):
    """A box with its edges chamfered b wide (45 degrees): it catches the light along every edge."""
    h = (size[0] / 2, size[1] / 2, size[2] / 2)
    b = max(0.0005, min(b, h[0] * 0.45, h[1] * 0.45, h[2] * 0.45))
    M = Matrix.Translation(center) @ (rot or I4)
    P = {}
    for s in [(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]:
        for a in range(3):
            co = [s[i] * (h[i] - b) for i in range(3)]
            co[a] = s[a] * h[a]
            P[(s, a)] = bm.verts.new(M @ Vector(co))
    cyc = ((-1, -1), (-1, 1), (1, 1), (1, -1))
    faces = []
    for a in range(3):
        b1, b2 = [i for i in range(3) if i != a]

        def S(sa, s1, s2):
            s = [0, 0, 0]
            s[a], s[b1], s[b2] = sa, s1, s2
            return tuple(s)
        for sa in (-1, 1):
            faces.append([P[(S(sa, s1, s2), a)] for s1, s2 in cyc])
        for s1 in (-1, 1):
            for s2 in (-1, 1):
                faces.append([P[(S(-1, s1, s2), b1)], P[(S(1, s1, s2), b1)], P[(S(1, s1, s2), b2)], P[(S(-1, s1, s2), b2)]])
    for s in [(sx, sy, sz) for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]:
        faces.append([P[(s, 0)], P[(s, 1)], P[(s, 2)]])
    for f in faces:
        bm.faces.new(f).material_index = mat


def _wall_pieces(a0, a1, z0, z1, holes):
    """Split a wall's face (a0..a1 along it, z0..z1) round rectangular holes (ha0, ha1, hz0, hz1), which may sit one
    over another: column by column, the solid runs between the holes. Yields (a0, a1, z0, z1) pieces."""
    cuts = sorted({a0, a1, *[h[0] for h in holes], *[h[1] for h in holes]})
    cuts = [c for c in cuts if a0 <= c <= a1]
    for ca, cb in zip(cuts, cuts[1:]):
        if cb - ca < 1e-4:
            continue
        zs = z0
        for ha0, ha1, hz0, hz1 in sorted((h for h in holes if h[0] <= ca + 1e-6 and h[1] >= cb - 1e-6), key=lambda h: h[2]):
            if hz0 > zs + 1e-4:
                yield (ca, cb, zs, min(hz0, z1))
            zs = max(zs, hz1)
        if z1 > zs + 1e-4:
            yield (ca, cb, zs, z1)


def wall_x(bm, x0, x1, y0, y1, z0, z1, holes=(), mat=0, b=0.0):
    """A wall running along x (thickness y0..y1) with rectangular holes (hx0, hx1, hz0, hz1): reveals come free."""
    for xa, xb, za, zb in _wall_pieces(x0, x1, z0, z1, holes):
        c, sz = ((xa + xb) / 2, (y0 + y1) / 2, (za + zb) / 2), (xb - xa, y1 - y0, zb - za)
        cbox(bm, c, sz, b, mat) if b else add_box(bm, c, sz, mat=mat)


def wall_y(bm, y0, y1, x0, x1, z0, z1, holes=(), mat=0):
    """A wall across the lane (running along y, thickness x0..x1) with holes (hy0, hy1, hz0, hz1)."""
    for ya, yb, za, zb in _wall_pieces(y0, y1, z0, z1, holes):
        add_box(bm, ((x0 + x1) / 2, (ya + yb) / 2, (za + zb) / 2), (x1 - x0, yb - ya, zb - za), mat=mat)


def prism(bm, poly, axis, a0, a1, mat=0):
    """Extrude a convex polygon along an axis: poly in (y, z) for axis 'x', in (x, z) for axis 'y'."""
    def P(u, v, a):
        return Vector((a, u, v)) if axis == 'x' else Vector((u, a, v))
    va = [bm.verts.new(P(u, v, a0)) for u, v in poly]
    vb = [bm.verts.new(P(u, v, a1)) for u, v in poly]
    bm.faces.new(va).material_index = mat
    bm.faces.new(vb[::-1]).material_index = mat
    n = len(poly)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((va[i], va[j], vb[j], vb[i])).material_index = mat


def _catenary(p0, p1, sag, n=8):
    p0, p1 = Vector(p0), Vector(p1)
    return [p0.lerp(p1, k / n) - Vector((0, 0, sag * 4 * (k / n) * (1 - k / n))) for k in range(n + 1)]


def _wire(bm, pts, r, mat=0, seg=4):
    for a, b in zip(pts, pts[1:]):
        add_cyl(bm, a, b, r, seg=seg, mat=mat)


def door_leaf(B, M, w, h, t, mat, metal, slot_z=None, both=True, knocker=False, knobs=True):
    """A four-panel door: hinge edge at local x 0, the leaf along +x, its outer face to -y, foot at z 0; M places it.
    Moulded panels (both faces, or the outer only), a knob each side (unless its handle is its own object), a letter
    plate, a knocker."""
    sub = bmesh.new()
    cbox(sub, (w / 2, 0, h / 2), (w, t, h), 0.006, mat)
    pw = (w - 0.3) / 2
    mid = slot_z if slot_z else h * 0.46
    for side in ((-1, 1) if both else (-1,)):
        yf = side * (t / 2 + 0.005)
        for px0 in (0.1, w - 0.1 - pw):
            for pz0, pz1 in ((0.14, mid - 0.06), (mid + 0.06, h - 0.13)):
                for cx, cz, sx, sz in ((px0 + pw / 2, pz0, pw + 0.02, 0.02), (px0 + pw / 2, pz1, pw + 0.02, 0.02),
                                       (px0, (pz0 + pz1) / 2, 0.02, pz1 - pz0), (px0 + pw, (pz0 + pz1) / 2, 0.02, pz1 - pz0)):
                    add_box(sub, (cx, yf, cz), (sx, 0.01, sz), mat=mat)
    for side in ((-1, 1) if knobs else ()):
        add_cyl(sub, (w - 0.075, side * t / 2, 0.95), (w - 0.075, side * (t / 2 + 0.03), 0.95), 0.008, seg=6, mat=metal)
        add_sphere(sub, (w - 0.075, side * (t / 2 + 0.035), 0.95), 0.026, seg=10, mat=metal)
        add_cyl(sub, (w - 0.075, side * t / 2, 0.95), (w - 0.075, side * (t / 2 + 0.006), 0.95), 0.032, seg=10, mat=metal)
    if slot_z:
        cbox(sub, (w / 2, -t / 2 - 0.006, slot_z), (0.25, 0.012, 0.07), 0.003, metal)
        add_box(sub, (w / 2, -t / 2 - 0.0125, slot_z), (0.19, 0.002, 0.022), mat=B('shaft'))
    if knocker:
        cbox(sub, (w / 2, -t / 2 - 0.008, h * 0.7), (0.06, 0.016, 0.07), 0.004, metal)
        add_torus(sub, (w / 2, -t / 2 - 0.022, h * 0.7 - 0.055), (0, 1, 0), 0.05, 0.008, seg=16, rseg=6, mat=metal)
    cbox(sub, (w / 2, -t / 2 - 0.003, 0.08), (w - 0.06, 0.006, 0.14), 0.002, metal)          # kick plate
    bmesh.ops.transform(sub, matrix=M, verts=sub.verts)
    _merge(B.bm, sub)


def window_unit(B, cx, yf, z0, z1, w, kind='glass', frame='wood', sill='concrete', rnd=None, bars=True, curtains=None):
    """A window in a hole (cx +- w/2, z0..z1) through a wall whose face is at yf (the wall behind, toward +y): the frame
    7 cm into the reveal, glass and glazing bars, a stone sill proud of the face and a lintel over the hole.
    kind: 'glass', 'shutters' (louvred, closed), 'boarded', 'open' (an empty frame)."""
    bm, rnd = B.bm, rnd or random.Random(int(cx * 100))
    fy, fw = yf + 0.07, 0.05
    F, G = B(frame), B('glass')
    for sx in (-1, 1):
        cbox(bm, (cx + sx * (w / 2 - fw / 2), fy + 0.03, (z0 + z1) / 2), (fw, 0.06, z1 - z0), 0.008, F)
    for z in (z0 + fw / 2, z1 - fw / 2):
        cbox(bm, (cx, fy + 0.03, z), (w - 2 * fw, 0.06, fw), 0.008, F)
    cbox(bm, (cx, yf + 0.025, z0 - 0.03), (w + 0.14, 0.17, 0.06), 0.012, B(sill))
    cbox(bm, (cx, yf + 0.03, z1 + 0.07), (w + 0.16, 0.11, 0.14), 0.01, B(sill))
    inner_w, inner_h = w - 2 * fw, z1 - z0 - 2 * fw
    if kind != 'open':
        add_box(bm, (cx, fy + 0.04, (z0 + z1) / 2), (inner_w, 0.006, inner_h), mat=G)
        if bars:
            cbox(bm, (cx, fy + 0.03, (z0 + z1) / 2), (0.03, 0.04, inner_h), 0.005, F)
            cbox(bm, (cx, fy + 0.03, z0 + fw + inner_h * 0.62), (inner_w, 0.04, 0.03), 0.005, F)
    if kind == 'shutters':                                   # two louvred leaves, closed, in the reveal
        for sx in (-1, 1):
            lx = cx + sx * inner_w / 4
            for z in (z0 + fw + 0.02, z1 - fw - 0.02):
                cbox(bm, (lx, yf + 0.03, z), (inner_w / 2 - 0.01, 0.03, 0.04), 0.004, B(frame))
            for xx in (lx - inner_w / 4 + 0.02, lx + inner_w / 4 - 0.02):
                cbox(bm, (xx, yf + 0.03, (z0 + z1) / 2), (0.04, 0.03, inner_h - 0.02), 0.004, B(frame))
            k, n = 0, int((inner_h - 0.08) / 0.07)
            for k in range(n):
                add_box(bm, (lx, yf + 0.03, z0 + fw + 0.07 + k * 0.07), (inner_w / 2 - 0.06, 0.006, 0.06), mat=B(frame),
                        rot=_rx(math.radians(-35)))
    if kind == 'boarded':                                    # planks nailed across the face, the year it was sealed
        for k, (z, a) in enumerate(((z0 + 0.2, 6), (z0 + (z1 - z0) * 0.55, -9), (z1 - 0.18, 4))):
            ln = w + 0.3
            cbox(bm, (cx + rnd.uniform(-0.04, 0.04), yf - 0.018, z), (ln, 0.022, 0.13 + 0.03 * (k % 2)), 0.004, B('wood'),
                 rot=_ry(math.radians(a)))
            for sx in (-1, 1):
                add_cyl(bm, (cx + sx * (ln / 2 - 0.06), yf - 0.03, z + sx * math.tan(math.radians(-a)) * (ln / 2 - 0.06)),
                        (cx + sx * (ln / 2 - 0.06), yf - 0.034, z + sx * math.tan(math.radians(-a)) * (ln / 2 - 0.06)), 0.008, seg=6, mat=B('steel'))
    if curtains:                                             # drawn back and gathered, a valance across
        C = B(curtains)
        for sx in (-1, 1):
            for k in range(4):
                x = cx + sx * (inner_w / 2 - 0.03 - k * 0.026)
                cbox(bm, (x, fy + 0.075 + 0.008 * (k % 2), (z0 + z1) / 2 - 0.02), (0.03, 0.014, inner_h - 0.06), 0.004, C,
                     rot=_ry(sx * 0.03 * k))
        cbox(bm, (cx, fy + 0.075, z1 - fw - 0.05), (inner_w, 0.016, 0.09), 0.004, C)


def drainpipe(B, x, y, ztop, zbot=0.06, r=0.032, shoe=-1):
    """A cast-iron downpipe with its hopper head, wall brackets and a shoe kicked out at the foot."""
    bm, M = B.bm, B('iron')
    add_cyl(bm, (x, y, ztop - 0.12), (x, y, zbot + 0.1), r, seg=10, mat=M)
    add_cyl(bm, (x, y, ztop), (x, y, ztop - 0.14), r * 2.4, r * 1.2, seg=10, mat=M)
    z = ztop - 0.35
    while z > zbot + 0.3:
        cbox(bm, (x, y + 0.03, z), (r * 2.8, 0.06, 0.04), 0.004, M)
        z -= 0.75
    add_cyl(bm, (x, y, zbot + 0.12), (x, y + shoe * 0.09, zbot), r, seg=10, mat=M)


def dead_plant(B, x, y, z, rnd, pot='concrete', r=0.09, h=0.2):
    """A pot of something long dead: a few dry stalks, bent, and a crust of soil."""
    bm = B.bm
    add_cyl(bm, (x, y, z), (x, y, z + h), r * 0.75, r, seg=12, mat=B(pot))
    add_cyl(bm, (x, y, z + h - 0.015), (x, y, z + h + 0.004), r * 1.08, seg=12, mat=B(pot))
    add_cyl(bm, (x, y, z + h - 0.03), (x, y, z + h - 0.015), r * 0.95, seg=10, mat=B('mud'))
    for k in range(rnd.randint(4, 7)):
        a = rnd.uniform(0, 2 * math.pi)
        p0 = Vector((x + 0.03 * math.cos(a), y + 0.03 * math.sin(a), z + h - 0.02))
        p1 = p0 + Vector((0.05 * math.cos(a), 0.05 * math.sin(a), rnd.uniform(0.12, 0.26)))
        p2 = p1 + Vector((rnd.uniform(-0.08, 0.08), rnd.uniform(-0.08, 0.08), rnd.uniform(-0.1, 0.02)))
        _wire(bm, [p0, p1, p2], 0.004, mat=B('wood'), seg=4)


def chair(B, x, y, ang, seat_h=0.44, seat=0.4, back_h=0.9, mat='wood', child=False, cushion=None):
    """A kitchen chair, turned ang about z (0: facing -y). A child's chair is a tall one, with a footrest."""
    bm, M = B.bm, B(mat)
    rot = _rz(ang)
    c = Vector((x, y, 0))
    s2 = seat / 2 - 0.02
    cbox(bm, c + rot @ Vector((0, 0, seat_h)), (seat, seat, 0.035), 0.008, M, rot=rot)
    for sx in (-1, 1):
        add_cyl(bm, c + rot @ Vector((sx * s2, s2, 0)), c + rot @ Vector((sx * s2, s2, back_h)), 0.016, seg=8, mat=M)
        add_cyl(bm, c + rot @ Vector((sx * s2, -s2, 0)), c + rot @ Vector((sx * s2, -s2, seat_h)), 0.016, 0.014, seg=8, mat=M)
    for z in (back_h - 0.06, back_h - 0.2):
        cbox(bm, c + rot @ Vector((0, s2, z)), (seat - 0.02, 0.022, 0.05 if z > back_h - 0.1 else 0.03), 0.006, M, rot=rot)
    for sy in (-1, 1):
        add_cyl(bm, c + rot @ Vector((-s2, sy * s2, seat_h * 0.35)), c + rot @ Vector((s2, sy * s2, seat_h * 0.35)), 0.009, seg=6, mat=M)
    if child:
        add_cyl(bm, c + rot @ Vector((-s2, -s2, seat_h * 0.42)), c + rot @ Vector((s2, -s2, seat_h * 0.42)), 0.014, seg=8, mat=M)
        cbox(bm, c + rot @ Vector((0, -s2 + 0.02, seat_h * 0.42 + 0.01)), (seat - 0.02, 0.08, 0.018), 0.004, M, rot=rot)
    if cushion:
        rounded_box((seat - 0.05, seat - 0.05, 0.05), c + rot @ Vector((0, 0, seat_h + 0.04)), p=2.6, cuts=3, bm=bm, mat=B(cushion),
                    rot=rot, dents=((0.004, 7.0),), seed=x)


def cloth(B, p, ang, kind, mat, rnd):
    """A piece of washing, pegged at p (its top middle), hanging; ang turns it about z to follow its line."""
    bm, M = B.bm, B(mat)
    rot = _rz(ang) @ _rx(math.radians(rnd.uniform(-6, 6)))
    P = Vector(p)
    if kind == 'shirt':
        cbox(bm, P + rot @ Vector((0, 0, -0.24)), (0.36, 0.012, 0.46), 0.004, M, rot=rot)
        for sx in (-1, 1):
            cbox(bm, P + rot @ Vector((sx * 0.24, 0, -0.1)), (0.16, 0.012, 0.18), 0.004, M, rot=rot @ _ry(sx * 0.5))
    elif kind == 'trousers':
        for sx in (-1, 1):
            cbox(bm, P + rot @ Vector((sx * 0.08, 0, -0.3)), (0.15, 0.012, 0.6), 0.004, M, rot=rot @ _ry(sx * 0.05))
    elif kind == 'dress':                                  # a child's, small
        for k in range(5):
            wd = 0.16 + 0.05 * k
            cbox(bm, P + rot @ Vector((0, 0, -0.03 - 0.065 * k)), (wd, 0.012, 0.07), 0.003, M, rot=rot)
    elif kind == 'sock':
        cbox(bm, P + rot @ Vector((0, 0, -0.09)), (0.06, 0.012, 0.18), 0.003, M, rot=rot)
        cbox(bm, P + rot @ Vector((0.03, 0, -0.18)), (0.1, 0.012, 0.05), 0.003, M, rot=rot)
    elif kind == 'sheet':
        cbox(bm, P + rot @ Vector((0, 0, -0.42)), (0.7, 0.01, 0.84), 0.003, M, rot=rot @ _ry(math.radians(rnd.uniform(-2, 2))))
    for dx in ((-0.12, 0.12) if kind in ('shirt', 'sheet') else (0.0,)):                      # pegs
        cbox(bm, P + rot @ Vector((dx * (2.5 if kind == 'sheet' else 1), 0, 0.0)), (0.012, 0.022, 0.06), 0.003, B('wood'), rot=rot)


# --- ring C's ledge and the seal ------------------------------------------------

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


def build_ledge(m, coll):
    """Ring C's ledge at the foot of the balcony stair: paving on a shelf of rock, open to the cave
    behind over a low lip; the rock portal over the seal, where ring C's cavern begins."""
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
    for k in range(10):
        s = rnd.uniform(0.05, 0.12)
        add_sphere(bm, (rnd.uniform(x0, x1), rnd.choice((rnd.uniform(0.8, 1.05), rnd.uniform(-0.6, -0.4))), s * 0.2), s,
                   seg=6, scale=(1.3, 1, 0.5), dents=(s * 0.2, 9))
    # The portal: rock over the seal and up out of frame, its pillars; ring C's cavern opens beyond it.
    _rock(bm, (80.3, 1.45, 1.6), (0.7, 0.7, 3.4), 7.0, cuts=3, p=3.0, amp=0.07)
    _rock(bm, (81.0, 1.7, 1.8), (0.5, 1.2, 3.8), 8.0, cuts=3, p=3.0, amp=0.08)
    _rock_sheet(bm, (79.95, -0.75, 3.0), (1.35, 0, 0), (0, 0, 2.2), 4, 4, 0.08, 3.0)
    _rock_sheet(bm, (BARRICADE[0] - 0.15, -0.75, 3.0), (1.2, 0, 0), (0, 1.95, 0), 3, 4, -0.05, 12.0)
    _rock(bm, (80.6, 0.6, 4.1), (1.6, 2.6, 1.9), 9.0, cuts=3, p=3.0, amp=0.15)
    _obj('D5Rock', bm, [m['rock']], coll, sharp=75)


def build_barricade(m, coll):
    """Corrugated sheets bolted to posts across the tunnel mouth, from the gap (0.62) up to 3 m: two
    skins across the lane and one facing the camera, braced, signed and taped."""
    b0, b1 = BARRICADE
    top = 3.0
    bm = bmesh.new()                       # mats: 0 sheet, 1 steel, 2 yellow, 3 wood
    for x in (b0 + 0.06, b1 - 0.06):                                        # posts, front and back
        for y in (-0.5, 1.08):
            add_box(bm, (x, y, top / 2 + 0.1), (0.08, 0.1, top + 0.2), mat=1)
            add_box(bm, (x, y, 0.01), (0.2, 0.2, 0.02), mat=1)
        add_box(bm, (x, 0.29, GAP + 0.04), (0.09, 1.7, 0.08), mat=2)        # the rails the sheets sit on
        add_box(bm, (x, 0.29, top - 0.05), (0.09, 1.7, 0.08), mat=1)
    for x in (b0 + 0.11, b1 - 0.11):                                        # the two skins across the lane (seen edge on)
        add_box(bm, (x, 0.29, (GAP + 0.08 + top) / 2), (0.02, 1.64, top - GAP - 0.08), mat=0)
    _corrugated(bm, (b0 - 0.02, -0.53, GAP + 0.08), (1, 0, 0), (0, 0, 1), 0.46, 1.3, mat=0)
    _corrugated(bm, (b0 + 0.4, -0.535, GAP + 0.06), (1, 0, 0), (0.03, 0, 1), 0.46, 1.42, mat=0)
    _corrugated(bm, (b0 - 0.02, -0.54, GAP + 1.32), (1, 0, 0), (-0.02, 0, 1), 0.88, top - GAP - 1.36, mat=0)
    add_box(bm, ((b0 + b1) / 2, -0.565, 1.2), (1.05, 0.04, 0.09), mat=3, rot=_ry(math.radians(28)))
    add_box(bm, ((b0 + b1) / 2, -0.565, 2.4), (1.0, 0.04, 0.09), mat=3, rot=_ry(math.radians(-24)))
    for x in (b0 + 0.06, b1 - 0.06):
        for z in (0.8, 1.4, 2.0, 2.6):
            add_cyl(bm, (x, -0.55, z), (x, -0.575, z), 0.012, seg=6, mat=1)
    add_box(bm, ((b0 + b1) / 2, -0.535, GAP + 0.03), (b1 - b0 + 0.06, 0.03, 0.06), mat=2)
    for k, (x, z) in enumerate(((b0 - 0.35, 0.09), (b0 - 0.05, 0.09), (b0 - 0.2, 0.25))):
        rounded_box((0.36, 0.22, 0.17), (x, 0.92, z), p=2.6, cuts=4, mat=3, bm=bm, dents=((0.01, 8.0),), seed=k)
    _obj('D5Barricade', bm, [m['shutter'], m['steel'], m['yellow'], m['paper']], coll)
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


# --- ring C's street ------------------------------------------------------------

def street_home(B, num, x0, x1, door_x, win_x, wall, door_mat, rnd, win=(0.82, 0.95, 1.9), kind='glass', slot_z=0.95,
                step=True, lamp=True, pipe_x=None, mat_out=True, extra_doors=()):
    """One home of the back row, its face on the lane at BACK_Y: a plinth, a plastered wall 0.2 thick with real
    reveals, pilasters at the party walls, the door (architrave, panelled leaf set back, a stone step), the window,
    a cornice, a slate roof rising back from a gutter at the eaves, a downpipe, the service cable and a dead lamp.
    kind 'blocked': the window's hole filled with odd blocks, flush-ish (a scavenged repair). extra_doors: (x, width,
    leaf material) for a home split in two, a second door cut into its face."""
    bm, Y = B.bm, BACK_Y
    ww, wz0, wz1 = win
    dh, dw = 1.98, 0.86
    main = [] if door_x is None else [(door_x - dw / 2, door_x + dw / 2, 0.0, dh)]   # None: its door is round the side
    holes = main + [(ex - ew / 2, ex + ew / 2, 0.0, dh) for ex, ew, _ in extra_doors]
    if kind != 'blocked':
        holes.append((win_x - ww / 2, win_x + ww / 2, wz0, wz1))
    wall_x(bm, x0 + 0.08, x1 - 0.08, Y, Y + 0.2, 0.24, 2.62, holes, B(wall))
    wall_x(bm, x0 + 0.08, x1 - 0.08, Y - 0.03, Y + 0.2, 0.0, 0.24, holes[:len(main) + len(extra_doors)], B('concrete'), b=0.01)
    for ex, ew, emat in extra_doors:                                         # cut in later: a plain frame, a plank door
        for sx in (-1, 1):
            cbox(bm, (ex + sx * (ew / 2 + 0.025), Y + 0.02, dh / 2), (0.05, 0.08, dh), 0.006, B('wood'))
        cbox(bm, (ex, Y + 0.02, dh + 0.03), (ew + 0.1, 0.08, 0.06), 0.006, B('wood'))
        for k in range(5):
            pw_ = (ew - 0.02) / 5
            cbox(bm, (ex - ew / 2 + 0.01 + pw_ * (k + 0.5), Y + 0.09, dh / 2 - 0.01), (pw_ - 0.006, 0.03, dh - 0.03), 0.004, B(emat))
        for z in (0.35, dh - 0.4):
            cbox(bm, (ex, Y + 0.068, z), (ew - 0.06, 0.02, 0.1), 0.004, B(emat))
        add_cyl(bm, (ex + ew / 2 - 0.08, Y + 0.06, 0.95), (ex + ew / 2 - 0.08, Y + 0.02, 0.95), 0.012, seg=8, mat=B('steel'))
        cbox(bm, (ex, Y - 0.1, 0.05), (ew + 0.14, 0.26, 0.1), 0.01, B('concrete'))
    if kind == 'blocked':                                                    # the window bricked up with what came to hand
        bx0, bx1 = win_x - ww / 2, win_x + ww / 2
        rows = int((wz1 - wz0) / 0.11)
        for r in range(rows):
            z = wz0 + (r + 0.5) * (wz1 - wz0) / rows
            x = bx0 - (0.06 if r % 2 else 0.0)
            while x < bx1 - 0.01:
                bw = rnd.choice((0.18, 0.22, 0.26))
                a, b = max(x, bx0), min(x + bw, bx1)
                if b - a > 0.03:
                    cbox(bm, ((a + b) / 2, Y + 0.05 + rnd.uniform(-0.008, 0.008), z), (b - a - 0.012, 0.1, (wz1 - wz0) / rows - 0.012), 0.006,
                         B(rnd.choice(('masonry', 'concrete', 'masonry'))))
                x += bw
        cbox(bm, (win_x, Y + 0.025, wz0 - 0.03), (ww + 0.14, 0.17, 0.06), 0.012, B('concrete'))
        cbox(bm, (win_x, Y + 0.03, wz1 + 0.07), (ww + 0.16, 0.11, 0.14), 0.01, B('concrete'))
    for x in (x0 + 0.08, x1 - 0.08):                                         # pilasters on the party walls
        cbox(bm, (x, Y + 0.07, 1.31), (0.16, 0.26, 2.62), 0.015, B('concrete'))
    cbox(bm, ((x0 + x1) / 2, Y + 0.06, 2.65), (x1 - x0 + 0.04, 0.3, 0.1), 0.02, B('concrete'))     # cornice
    cbox(bm, ((x0 + x1) / 2, Y + 0.08, 2.56), (x1 - x0 - 0.1, 0.24, 0.05), 0.01, B('concrete'))
    # The door: an architrave, the leaf set back 12 cm, a step.
    T = B('concrete')
    for sx in ((-1, 1) if door_x is not None else ()):
        cbox(bm, (door_x + sx * (dw / 2 + 0.04), Y - 0.015, dh / 2 + 0.03), (0.08, 0.05, dh + 0.06), 0.01, T)
    if door_x is not None:
        cbox(bm, (door_x, Y - 0.02, dh + 0.1), (dw + 0.24, 0.07, 0.12), 0.012, T)
        door_leaf(B, Matrix.Translation((door_x - dw / 2, Y + 0.13, 0.0)), dw, dh, 0.045, B(door_mat), B('brass'), slot_z=slot_z, both=False,
                  knocker=(num == '112'))
        if step:
            cbox(bm, (door_x, Y - 0.1, 0.06), (dw + 0.2, 0.3, 0.12), 0.012, T)
        cbox(bm, (door_x + dw / 2 + 0.2, Y - 0.012, 1.28), (0.11, 0.012, 0.04), 0.003, B('brass'))       # a nameplate
    else:
        lamp = False
    if kind != 'blocked':
        window_unit(B, win_x, Y, wz0, wz1, ww, kind=kind, frame='wood' if num != '112' else 'pigeon', rnd=rnd)
    # The roof: a gutter on brackets, the eaves board, slate courses rising back to a ridge.
    E = B('slate')
    zf, yf, zr, yr = 2.76, Y - 0.32, 3.55, Y + 1.3
    ang = math.atan2(zr - zf, yr - yf)
    n = 9
    for k in range(n):
        t = (k + 0.5) / n
        c = Vector((0, yf + (yr - yf) * t, zf + (zr - zf) * t + 0.012 * (k % 2)))
        cbox(bm, ((x0 + x1) / 2, c.y, c.z), (x1 - x0 + 0.06, (yr - yf) / math.cos(ang) / n + 0.04, 0.035), 0.006, E,
             rot=_rx(ang))
    add_cyl(bm, (x0 - 0.02, yr, zr + 0.03), (x1 + 0.02, yr, zr + 0.03), 0.055, seg=8, mat=E)
    cbox(bm, ((x0 + x1) / 2, Y - 0.27, 2.72), (x1 - x0 + 0.06, 0.03, 0.14), 0.006, B('wood'))
    add_cyl(bm, (x0 - 0.02, Y - 0.34, 2.68), (x1 + 0.02, Y - 0.34, 2.68), 0.05, seg=8, mat=B('iron'))
    drainpipe(B, pipe_x if pipe_x is not None else x1 - 0.24, Y - 0.06, 2.66)
    add_cyl(bm, (pipe_x if pipe_x is not None else x1 - 0.24, Y - 0.06, 2.62), (pipe_x if pipe_x is not None else x1 - 0.24, Y - 0.34, 2.68),
            0.03, seg=8, mat=B('iron'))
    # The service cable along the face, with its clips, and a meter box.
    add_cyl(bm, (x0 + 0.1, Y - 0.025, 2.46), (x1 - 0.1, Y - 0.025, 2.46), 0.007, seg=5, mat=B('rubber'))
    for x in [x0 + 0.3 + 0.55 * k for k in range(int((x1 - x0 - 0.5) / 0.55) + 1)]:
        cbox(bm, (x, Y - 0.02, 2.46), (0.02, 0.025, 0.03), 0.003, B('steel'))
    mx = x0 + 0.38
    cbox(bm, (mx, Y - 0.05, 1.95), (0.22, 0.1, 0.3), 0.01, B('steel'))
    add_cyl(bm, (mx, Y - 0.025, 2.1), (mx, Y - 0.025, 2.46), 0.012, seg=6, mat=B('steel'))
    if lamp:                                                                  # a wall lamp by the door, long dead
        lx = door_x + dw / 2 + 0.22
        cbox(bm, (lx, Y - 0.02, 2.02), (0.08, 0.03, 0.12), 0.006, B('iron'))
        add_cyl(bm, (lx, Y - 0.03, 2.05), (lx, Y - 0.16, 2.1), 0.012, seg=6, mat=B('iron'))
        add_cyl(bm, (lx, Y - 0.17, 2.12), (lx, Y - 0.17, 2.04), 0.05, 0.035, seg=10, mat=B('iron'))
        add_sphere(bm, (lx, Y - 0.17, 2.0), 0.045, seg=10, mat=B('deadbulb'))


# --- pass 3: the street he walks through ----------------------------------------------
# The lane camera (index.html, region 5) is 2.15 up and about 5.8 out (35 mm, looking at 0.4). Anything in front of
# the lane is kept low enough that, seen from there, it rises no higher than his soles on the play line (front_cap):
# the front row never hides him, not even his feet (the director's limit is 0.5). Nothing tall stands in it:
# the washing lines cross the lane to a messenger wire hung from the dark, out of the top of the frame.
LANE_CAM = (2.15, 5.83)


def front_cap(y, zp=0.02):
    """The tallest anything standing at depth y (y < 0, toward the camera) may be so that, from the lane camera, it
    reaches no higher than zp on the play line."""
    H, D = LANE_CAM
    return H - (H - zp) * (D + y) / D


def _cuts(a0, a1, holes, rnd, wmin, wmax):
    """Column edges from a0 to a1, random widths, falling on every hole's edges (so jambs come out clean)."""
    fixed = sorted({a0, a1, *[h for hole in holes for h in hole[:2] if a0 < h < a1]})
    out = [a0]
    for a, b in zip(fixed, fixed[1:]):
        x = a
        while b - x > wmax:
            x += rnd.uniform(wmin, wmax)
            if b - x < wmin * 0.7:
                break
            out.append(x)
        out.append(b)
    return out


def ragged_x(B, x0, x1, y0, y1, top, mat, rnd, holes=(), z0=0.0, wmin=0.1, wmax=0.3, loose=0.25):
    """A wall along x (thickness y0..y1, toward the lane at y1) broken down to columns of random width whose tops
    follow top(x), jittered, never over front_cap(y1). holes: openings (hx0, hx1, hz0, hz1). A few loose bricks."""
    cap = front_cap(max(y0, y1))
    xs = _cuts(x0, x1, holes, rnd, wmin, wmax)
    for a, b in zip(xs, xs[1:]):
        c = (a + b) / 2
        h = min(cap, top(c) + rnd.uniform(-0.07, 0.05))
        segs = [(z0, h)]
        for hx0, hx1, hz0, hz1 in holes:
            if hx0 < c < hx1:
                segs = [(lo, min(hi, hz0)) for lo, hi in segs if lo < hz0] + [(max(lo, hz1), hi) for lo, hi in segs if hi > hz1]
        for lo, hi in segs:
            if hi - lo > 0.02:
                add_box(B.bm, (c, (y0 + y1) / 2, (lo + hi) / 2), (b - a, abs(y1 - y0), hi - lo), mat=B(mat))
                if rnd.random() < loose and hi < cap - 0.08:
                    cbox(B.bm, (c + rnd.uniform(-0.03, 0.03), (y0 + y1) / 2, hi + 0.035), (0.2, 0.09, 0.065), 0.008, B('masonry'),
                         rot=_rz(rnd.uniform(-0.4, 0.4)) @ _ry(rnd.uniform(-0.15, 0.15)))


def ragged_y(B, y0, y1, x0, x1, top, mat, rnd, z0=0.0, wmin=0.12, wmax=0.32):
    """A wall across the lane (running along y from y0 < y1, thickness x0..x1) broken down, its tops following
    top(y), each column under front_cap at its lane-side end."""
    ys = _cuts(y0, y1, (), rnd, wmin, wmax)
    for a, b in zip(ys, ys[1:]):
        h = min(front_cap(b), top((a + b) / 2) + rnd.uniform(-0.07, 0.04))
        if h - z0 > 0.02:
            add_box(B.bm, ((x0 + x1) / 2, (a + b) / 2, (z0 + h) / 2), (x1 - x0, b - a, h - z0), mat=B(mat))


def rubble(B, cx, cy, r, h, rnd, mats=('masonry', 'homeplaster', 'concrete'), n=14, z0=0.0):
    """A heap of broken wall: chunks scattered round (cx, cy), higher toward the middle, no higher than h."""
    for _ in range(n):
        a, d = rnd.uniform(0, 2 * math.pi), r * math.sqrt(rnd.random())
        s = (rnd.uniform(0.1, 0.24), rnd.uniform(0.07, 0.16), rnd.uniform(0.04, 0.09))
        z = z0 + s[2] / 2 + (h - s[2]) * (1 - d / r) * rnd.uniform(0.3, 1.0)
        cbox(B.bm, (cx + d * math.cos(a), cy + d * math.sin(a), z), s, 0.012, B(rnd.choice(mats)),
             rot=_rz(rnd.uniform(0, math.pi)) @ _rx(rnd.uniform(-0.45, 0.45)))


def _bedstead(B, x, y, z, ang, rnd):
    """An iron bedstead, its mattress long gone, a spring frame sagging between its ends."""
    rot, M = _rz(ang), B('iron')
    c = Vector((x, y, z))
    for sx, hh in ((-0.48, 0.55), (0.48, 0.42)):
        for sy in (-0.36, 0.36):
            add_cyl(B.bm, c + rot @ Vector((sx, sy, 0)), c + rot @ Vector((sx, sy, hh)), 0.014, seg=6, mat=M)
        add_cyl(B.bm, c + rot @ Vector((sx, -0.36, hh)), c + rot @ Vector((sx, 0.36, hh)), 0.012, seg=6, mat=M)
        for k in range(4):
            yy = -0.27 + 0.18 * k
            add_cyl(B.bm, c + rot @ Vector((sx, yy, 0.22)), c + rot @ Vector((sx, yy, hh)), 0.006, seg=4, mat=M)
    for sy in (-0.36, 0.36):
        add_cyl(B.bm, c + rot @ Vector((-0.48, sy, 0.22)), c + rot @ Vector((0.48, sy, 0.2)), 0.01, seg=5, mat=M)
    for k in range(6):
        add_cyl(B.bm, c + rot @ Vector((-0.45, -0.33 + 0.13 * k, 0.21)), c + rot @ Vector((0.45, -0.33 + 0.13 * k, 0.15)), 0.004, seg=4, mat=M)


def _fallen_table(B, x, y, z, ang):
    rot, M = _rz(ang), B('wood')
    c = Vector((x, y, z))
    cbox(B.bm, c + rot @ Vector((0, 0, 0.36)), (0.8, 0.035, 0.6), 0.006, M, rot=rot @ _rx(math.pi / 2))     # on its side
    for sx in (-0.35, 0.35):
        for sz in (0.1, 0.62):
            add_cyl(B.bm, c + rot @ Vector((sx, 0.0, sz)), c + rot @ Vector((sx, 0.66, sz)), 0.022, seg=6, mat=M)


def front_ruin(m, kind, W, seed):
    """One home of the front row (odd numbers), cut down: what the camera sees of it is its garden, porch or front
    wall stump and the floor of its front room, all under front_cap. Built at x 0..W, y from the lane's edge
    (FRONT_Y[0]) out toward the camera; the street places linked duplicates of it (some mirrored). Kinds:
    'A' a garden wall and gate, a porch with snapped posts, the house's front wall broken down, an iron bed inside;
    'B' the front wall right on the lane, broken to the sills, a kitchen open to the sky (the range, a table on its
    side, a scavenged sheet); 'C' a planter wall, a yard, and the roof fallen in across the rooms."""
    rnd = random.Random(seed)
    # Five or six materials a home (each is a draw call per instance): mud, a bucket's zinc, a sheet's steel and,
    # but where the roof fell in, the slates are folded into the masonry and iron.
    B = Batch(m, alias={'mud': 'masonry', 'steel': 'iron', 'shutter': 'iron', 'slate': 'slate' if kind == 'C' else 'masonry'})
    ye = FRONT_Y[0]                                     # the lane's edge
    yr = -4.05                                          # the rear wall's outer face
    plaster = {'A': 'homeplaster', 'B': 'plasterA', 'C': 'plasterB'}[kind]
    add_box(B.bm, (W / 2, (ye + yr) / 2, -0.15), (W, ye - yr, 0.3), mat=B('concrete'))      # the ground it stands on
    for x0_, x1_ in ((0.0, 0.12), (W - 0.12, W)):                                      # party walls, rising toward the camera
        y_front = {'A': -2.4, 'B': ye - 0.2, 'C': -1.55}[kind]
        ragged_y(B, yr + 0.15, y_front, x0_, x1_, lambda y: 0.66 + (y + 3.9) * -0.1 + 0.18 * math.sin(y * 5.3 + x0_), plaster, rnd)
        ragged_y(B, y_front, ye - 0.14, x0_, x1_, lambda y: 0.28, plaster, rnd)            # the garden's side walls
    ragged_x(B, 0.0, W, yr, yr + 0.15, lambda x: 0.95 + 0.12 * math.sin(x * 3.1), plaster, rnd)   # the rear wall
    if kind == 'A':
        # The garden wall and its gate, the gate hanging open off one hinge.
        g0, g1 = 0.85, 1.55
        for a, b in ((0.12, g0 - 0.09), (g1 + 0.09, W - 0.12)):
            cbox(B.bm, ((a + b) / 2, ye - 0.07, 0.12), (b - a, 0.14, 0.24), 0.01, B(plaster))
            cbox(B.bm, ((a + b) / 2, ye - 0.07, 0.26), (b - a + 0.02, 0.19, 0.05), 0.012, B('concrete'))
        for x in (g0 - 0.045, g1 + 0.045):
            cbox(B.bm, (x, ye - 0.07, 0.16), (0.17, 0.17, 0.32), 0.015, B('concrete'))
            add_sphere(B.bm, (x, ye - 0.07, 0.35), 0.045, seg=10, mat=B('concrete'))
        hinge = Vector((g0 + 0.02, ye - 0.12, 0.0))
        rot = _rz(math.radians(-62)) @ _ry(math.radians(5))
        for k in range(7):
            add_cyl(B.bm, hinge + rot @ Vector((0.05 + 0.09 * k, 0, 0.06)), hinge + rot @ Vector((0.05 + 0.09 * k, 0, 0.36)), 0.007, seg=5, mat=B('iron'))
        for z in (0.08, 0.22, 0.34):
            add_cyl(B.bm, hinge + rot @ Vector((0.02, 0, z)), hinge + rot @ Vector((0.64, 0, z - 0.02)), 0.01, seg=5, mat=B('iron'))
        # The yard: flags, a path, pots and a bucket; then the porch: a step, the slab, two posts snapped off.
        cbox(B.bm, ((g0 + g1) / 2, -1.5, 0.008), (g1 - g0 - 0.05, 0.7, 0.016), 0.004, B('concrete'))
        for x, y in ((0.4, -1.35), (2.05, -1.45)):
            dead_plant(B, x, y, 0.0, rnd, pot='concrete', r=0.1, h=0.22)
        add_cyl(B.bm, (1.85, -1.75, 0.0), (1.85, -1.75, 0.22), 0.11, 0.13, seg=12, mat=B('steel'))
        cbox(B.bm, (W / 2, -1.93, 0.06), (1.3, 0.16, 0.12), 0.01, B('concrete'))
        cbox(B.bm, (W / 2, -2.2, 0.12), (W - 0.3, 0.42, 0.24), 0.012, B('concrete'))
        for x, h in ((0.32, 0.76), (W - 0.32, 0.55)):
            cbox(B.bm, (x, -2.08, 0.24 + (h - 0.24) / 2), (0.1, 0.1, h - 0.24), 0.01, B('wood'))
        cbox(B.bm, (W * 0.55, -2.15, 0.32), (W - 0.2, 0.09, 0.08), 0.01, B('wood'), rot=_rz(0.12) @ _ry(0.04))    # the porch beam, down
        for k in range(4):
            cbox(B.bm, (0.5 + 0.42 * k, -2.25 - 0.04 * k, 0.29 + 0.01 * k), (0.05, 0.44, 0.03), 0.005, B('wood'), rot=_rz(0.3 - 0.15 * k))
        # The house's front wall, broken down; the doorway and a window's sill.
        holes = [(0.85, 1.6, 0.24, 2.0), (1.85, 2.25, 0.78, 1.9)]
        ragged_x(B, 0.12, W - 0.12, -2.6, -2.4, lambda x: 0.8 - 0.2 * math.sin(x * 2.3 + 0.5), plaster, rnd, holes)
        cbox(B.bm, (2.05, -2.38, 0.755), (0.52, 0.12, 0.05), 0.01, B('concrete'))
        for sx in (0.85, 1.6):                                                         # the door frame's stumps
            cbox(B.bm, (sx + (0.03 if sx < 1 else -0.03), -2.5, 0.24 + 0.3), (0.06, 0.22, 0.6), 0.006, B('wood'))
        add_box(B.bm, (W / 2, -3.25, 0.22), (W - 0.24, 1.3, 0.04), mat=B('wood'))         # the room's boards
        _bedstead(B, 0.85, -3.3, 0.24, 0.15, rnd)
        cbox(B.bm, (1.7, -3.2, 0.62), (0.1, 1.6, 0.12), 0.01, B('wood'), rot=_rx(0.42) @ _rz(0.5))   # a roof beam, fallen in
        rubble(B, 1.9, -3.6, 0.4, 0.4, rnd, mats=('masonry', plaster, 'slate'), z0=0.24)
    elif kind == 'B':
        holes = [(0.75, 1.55, 0.0, 2.0)]
        ragged_x(B, 0.12, W - 0.12, ye - 0.2, ye, lambda x: 0.3 + 0.06 * math.sin(x * 4.1), plaster, rnd, holes, loose=0.2)
        cbox(B.bm, (1.15, ye - 0.1, 0.05), (0.92, 0.3, 0.1), 0.01, B('concrete'))      # the doorstep, on the lane
        cbox(B.bm, (2.03, ye - 0.08, 0.3), (0.55, 0.14, 0.05), 0.01, B('concrete'))     # the window's sill, fallen to the wall's stump
        add_box(B.bm, (W / 2, (ye - 0.2 + yr + 0.15) / 2, 0.02), (W - 0.24, ye - 0.2 - yr - 0.15, 0.04), mat=B('concrete'))
        for i in range(int((W - 0.24) / 0.3)):                                          # the kitchen's tiles
            add_box(B.bm, (0.27 + 0.3 * i, (ye + yr) / 2, 0.041), (0.008, ye - yr - 0.4, 0.004), mat=B('masonry'))
        x_r, y_r = 0.45, -3.55                                                         # the range, against the back
        cbox(B.bm, (x_r, y_r, 0.38), (0.62, 0.42, 0.72), 0.015, B('iron'))
        cbox(B.bm, (x_r, y_r, 0.76), (0.68, 0.46, 0.04), 0.01, B('iron'))
        add_cyl(B.bm, (x_r + 0.18, y_r - 0.1, 0.78), (x_r + 0.18, y_r - 0.1, 1.2), 0.05, seg=10, mat=B('iron'))
        add_cyl(B.bm, (x_r + 0.6, y_r + 0.3, 0.1), (x_r + 1.2, y_r + 0.9, 0.06), 0.05, seg=10, mat=B('iron'))   # its pipe, down
        _fallen_table(B, 1.45, -2.9, 0.04, 0.35)
        chair(B, 1.95, -2.55, 2.5)
        cbox(B.bm, (0.5, -2.05, 0.2), (0.1, 0.9, 0.4), 0.01, B('wood'), rot=_ry(1.2) @ _rz(0.2))   # a dresser, face down
        cbox(B.bm, (0.48, -2.0, 0.08), (0.95, 0.42, 0.14), 0.01, B('wood'), rot=_rz(0.2))
        for k in range(9):                                                             # the crockery, broken on the tiles
            cbox(B.bm, (rnd.uniform(0.4, 2.0), rnd.uniform(-3.2, -1.6), 0.05), (rnd.uniform(0.03, 0.07), rnd.uniform(0.02, 0.05), 0.012), 0.002,
                 B('masonry'), rot=_rz(rnd.uniform(0, 3)))
        _corrugated(B.bm, (1.2, -1.32, 0.04), (1, 0, 0), (0, -0.55, 0.9), 0.9, 0.62, mat=B('shutter'))   # a sheet propped behind the wall
        rubble(B, 2.1, -3.5, 0.45, 0.42, rnd, mats=('masonry', plaster, 'concrete'), z0=0.04)
    else:
        g0, g1 = 1.45, 2.15
        for a, b in ((0.12, g0), (g1, W - 0.12)):
            cbox(B.bm, ((a + b) / 2, ye - 0.065, 0.13), (b - a, 0.13, 0.26), 0.01, B('concrete'))
            for x in [a + 0.16 + 0.3 * k for k in range(int((b - a - 0.1) / 0.3))]:
                add_cyl(B.bm, (x, ye - 0.065, 0.26), (x, ye - 0.065, 0.31 + 0.03 * rnd.random()), 0.008, seg=5, mat=B('iron'))   # railings, sawn off
        cbox(B.bm, (0.7, -1.26, 0.12), (1.0, 0.22, 0.24), 0.01, B('wood'))                  # a planter, its soil, dead stalks
        cbox(B.bm, (0.7, -1.26, 0.23), (0.94, 0.17, 0.02), 0.004, B('mud'))
        for k in range(4):
            dead_plant(B, 0.35 + 0.23 * k, -1.26, 0.18, rnd, pot='wood', r=0.025, h=0.02)
        holes = [(1.45, 2.15, 0.0, 2.0)]
        ragged_x(B, 0.12, W - 0.12, -1.75, -1.55, lambda x: 0.66 + 0.14 * math.sin(x * 3.3 + 1.0), plaster, rnd, holes)
        cbox(B.bm, (1.8, -1.48, 0.05), (0.8, 0.26, 0.1), 0.01, B('concrete'))
        add_box(B.bm, (W / 2, -2.85, 0.03), (W - 0.24, 2.2, 0.06), mat=B('wood'))
        # The roof, fallen in: its rafters and slates lying from the rear wall's top down to the floor inside the front wall.
        p_hi, p_lo = Vector((0, -3.88, 1.3)), Vector((0, -1.95, 0.18))
        d = p_lo - p_hi
        ang = math.atan2(d.z, -d.y)
        for k in range(6):
            x = 0.3 + (W - 0.6) * k / 5
            cbox(B.bm, (x, (p_hi.y + p_lo.y) / 2, (p_hi.z + p_lo.z) / 2 + 0.04), (0.06, d.length + 0.1, 0.1), 0.008, B('wood'), rot=_rx(-ang))
        for k in range(7):
            t = (k + 0.5) / 7
            c = p_hi.lerp(p_lo, t)
            if k == 4:
                continue                                                               # a hole where the slates slid off
            cbox(B.bm, (W / 2 + rnd.uniform(-0.05, 0.05), c.y, c.z + 0.1), (W - 0.36 - rnd.uniform(0, 0.3), d.length / 7 + 0.03, 0.03), 0.005,
                 B('slate'), rot=_rx(-ang + rnd.uniform(-0.04, 0.04)))
        for k in range(10):                                                             # slates slid off the end
            cbox(B.bm, (rnd.uniform(0.3, W - 0.3), rnd.uniform(-1.95, -1.78), 0.03 + 0.01 * k), (0.24, 0.16, 0.012), 0.003, B('slate'),
                 rot=_rz(rnd.uniform(0, 3)) @ _rx(rnd.uniform(-0.3, 0.3)))
        cbox(B.bm, (W - 0.55, yr + 0.3, 0.62), (0.5, 0.3, 1.24), 0.015, B('masonry'))   # the chimney breast, standing
    return B


def build_front_row(m, coll):
    """The front row: three kinds of cut-down home (D5FrontRowA/B/C), placed along the lane as linked duplicates,
    some mirrored; C-111, which went into the sink with the lane at the narrow point, is the street's own (in
    D5LaneFront). Their numbers are odd: C-101 by the barricade to C-113 at the square."""
    W = 2.5
    meshes = {}
    for kind, seed in (('A', 5401), ('B', 5402), ('C', 5403)):
        ob = front_ruin(m, kind, W, seed).done(f'D5FrontRow{kind}', coll)
        meshes[kind] = ob
    # (No gate posts or porch posts in front of the bell, the junction box, the duct or the narrow point: C and B there.)
    place = [('A', 81.05, False), ('B', 83.6, True), ('C', CROSS[1] + 0.1, False), ('C', 90.05, True), ('B', 92.6, False),
             ('A', DIP[1] + 0.1, True)]
    used = set()
    for k, (kind, x0, mirror) in enumerate(place):
        src = meshes[kind]
        if kind in used:
            ob = bpy.data.objects.new(f'D5FrontRow{kind}.{k}', src.data)        # a linked duplicate: one mesh, many homes
            coll.objects.link(ob)
        else:
            ob = src
            used.add(kind)
        ob.location = (x0 + (W if mirror else 0.0), 0.0, 0.0)
        ob.scale = (-1.0 if mirror else 1.0, 1.0, 1.0)
    return [o for o in coll.objects if o.name.startswith('D5FrontRow')]


def build_cross_alley(m, B, F, R, rnd):
    """The cross alley between C-104 and C-106: the homes' side walls run back along it, steps go up toward ring B
    (out of sight, as the families went), and in front of the lane steps go down between the front row to the lower
    lanes, with a rail. The standpipe at its mouth, the ration queue's post."""
    a0, a1 = CROSS
    Y = BACK_Y
    for x, sx, mat in ((a0, 1, 'plasterA'), (a1, -1, 'plasterB')):
        add_box(B.bm, (x + sx * 0.08, (Y + 3.4) / 2, 1.3), (0.16, 3.4 - Y, 2.62), mat=B(mat))
    ys = 2.3                                                               # the alley's foot, then the steps
    add_box(F.bm, ((a0 + a1) / 2, (Y + ys) / 2, -0.15), (a1 - a0, ys - Y, 0.3), mat=F('concrete'))
    for k in range(15):                                                    # up: 0.19 a step
        y, z = ys + 0.24 * k, 0.19 * (k + 1)
        cbox(B.bm, ((a0 + a1) / 2, y + 0.12, z / 2), (a1 - a0 - 0.3, 0.26, z), 0.01, B('concrete'))
        cbox(B.bm, ((a0 + a1) / 2, y + 0.015, z - 0.01), (a1 - a0 - 0.3, 0.04, 0.025), 0.004, B('steel'))     # worn nosings
    _wire(B.bm, [Vector((a0 + 0.25, ys - 0.1, 0.9)), Vector((a0 + 0.25, ys + 0.24 * 15, 0.9 + 0.19 * 15))], 0.016, B('iron'), seg=8)
    for k in (0, 5, 10, 15):
        y = ys + 0.24 * k
        add_cyl(B.bm, (a0 + 0.25, y, 0.19 * k), (a0 + 0.25, y, 0.19 * k + 0.9), 0.012, seg=6, mat=B('iron'))
    add_cyl(B.bm, (a0, Y + 0.5, 2.3), (a1, Y + 0.5, 2.3), 0.05, seg=10, mat=B('iron'))   # a water main across, high
    # Down, toward the camera: the stair to the lower lanes, between the front row, with low walls and a rail.
    s0, s1 = a0 - 0.1, a1 + 0.1
    for k in range(12):
        y, z = FRONT_Y[0] - 0.26 * k, -0.19 * (k + 1)
        cbox(R.bm, ((s0 + s1) / 2, y - 0.13, z - 0.15), (s1 - s0 - 0.2, 0.26, 0.3), 0.008, R('concrete'))
    for x in (s0 + 0.05, s1 - 0.05):                                       # its walls, stepping down with it
        for k in range(12):
            y, z = FRONT_Y[0] - 0.26 * k, -0.19 * (k + 1)
            h = min(front_cap(y), z + 0.45)
            add_box(R.bm, (x, y - 0.13, (h - 2.4) / 2), (0.1, 0.26, h + 2.4), mat=R('plasterA'))
    rx = s0 + 0.2
    pts = [Vector((rx, FRONT_Y[0] - 0.05, min(0.55, front_cap(FRONT_Y[0] - 0.05)))), Vector((rx, FRONT_Y[0] - 0.26 * 12, -0.19 * 12 + 0.85))]
    _wire(R.bm, pts, 0.016, R('iron'), seg=8)
    for k in (1, 5, 9):
        y = FRONT_Y[0] - 0.26 * k
        add_cyl(R.bm, (rx, y, -0.19 * (k + 1)), (rx, y, pts[0].z + (pts[1].z - pts[0].z) * (0.26 * k) / (0.26 * 12)), 0.011, seg=6, mat=R('iron'))
    add_box(R.bm, ((s0 + s1) / 2, -5.6, -2.45), (s1 - s0 + 1.2, 2.6, 0.1), mat=R('concrete'))   # the lower lane it reaches
    # The standpipe: a cast-iron column, its brass tap worn bright, a stone trough under it, silted; the buckets
    # left standing in the queue for it.
    tx, ty = TAP
    cbox(B.bm, (tx, ty + 0.08, 0.15), (0.62, 0.34, 0.3), 0.02, B('concrete'))
    cbox(B.bm, (tx, ty + 0.08, 0.27), (0.5, 0.24, 0.04), 0.008, B('mud'))
    add_cyl(B.bm, (tx + 0.18, ty + 0.2, 0.3), (tx + 0.18, ty + 0.2, 0.98), 0.04, seg=12, mat=B('iron'))
    add_sphere(B.bm, (tx + 0.18, ty + 0.2, 1.0), 0.05, seg=10, mat=B('iron'))
    add_cyl(B.bm, (tx + 0.18, ty + 0.2, 0.78), (tx + 0.04, ty + 0.12, 0.74), 0.022, 0.018, seg=10, mat=B('iron'))
    add_cyl(B.bm, (tx + 0.04, ty + 0.12, 0.74), (tx + 0.02, ty + 0.1, 0.62), 0.016, seg=8, mat=B('brass'))   # the spout, polished
    add_cyl(B.bm, (tx + 0.18, ty + 0.2, 0.86), (tx + 0.18, ty + 0.05, 0.86), 0.01, seg=6, mat=B('brass'))     # the tap's handle, worn bright
    add_cyl(B.bm, (tx + 0.1, ty + 0.05, 0.86), (tx + 0.26, ty + 0.05, 0.86), 0.012, seg=6, mat=B('brass'))
    for k, (x, y) in enumerate(((tx - 0.35, 0.56), (tx - 0.9, 0.6), (tx - 1.3, 0.62))):     # left standing on the queue's marks
        add_cyl(B.bm, (x, y, 0.0), (x, y, 0.28), 0.12, 0.14, seg=12, mat=B('steel' if k != 1 else 'depot_green'))
        add_torus(B.bm, (x, y, 0.28), (0, 0, 1), 0.14, 0.008, seg=14, rseg=4, mat=B('steel'))
        add_torus(B.bm, (x, y, 0.32), (1, 0, 0), 0.12, 0.005, seg=12, rseg=3, mat=B('iron'))
    # The ration queue's post: iron, its tin sign (D5RationSign) at a grown-up's eye level.
    qx, qy = QUEUE_POST
    add_cyl(B.bm, (qx, qy, 0.0), (qx, qy, 1.62), 0.025, seg=8, mat=B('iron'))
    cbox(B.bm, (qx, qy, 0.02), (0.2, 0.2, 0.04), 0.008, B('concrete'))
    cbox(B.bm, (qx, qy + 0.012, 1.38), (0.36, 0.012, 0.3), 0.004, B('steel'))


def build_new_homes(m, B, rnd):
    """C-102, C-104 (and the 104A cut into it) and C-106: cramped, patched with what came to hand."""
    Y = BACK_Y
    (n2, a2, b2), (n4, a4, b4), (n6, a6, b6) = NEW_HOMES
    street_home(B, n2, a2, b2, 82.95, 81.9, 'plasterB', 'pigeon', rnd, kind='glass', pipe_x=a2 + 0.22)
    street_home(B, n4, a4, b4, 84.45, 85.15, 'homeplaster', 'depot_green', rnd, win=(0.46, 1.0, 1.75), kind='blocked',
                extra_doors=((85.75, 0.58, 'wood'),), lamp=False)
    street_home(B, n6, a6, b6, None, C106_WIN, 'plasterA', 'dado', rnd, kind='glass', pipe_x=b6 - 0.2)
    bm = B.bm
    # C-102: a corrugated sheet nailed over the plaster that fell off, a crate for a step, a water butt.
    _corrugated(bm, (a2 + 0.3, Y - 0.02, 0.28), (1, 0, 0), (0, 0, 1), 0.85, 0.62, mat=B('rust'))
    for x in (a2 + 0.34, a2 + 1.1):
        for z in (0.35, 0.82):
            add_cyl(bm, (x, Y - 0.03, z), (x, Y - 0.045, z), 0.008, seg=5, mat=B('steel'))
    cbox(bm, (82.95, Y - 0.16, 0.1), (0.5, 0.3, 0.2), 0.01, B('wood'))
    add_cyl(bm, (83.45, Y - 0.25, 0.0), (83.45, Y - 0.25, 0.62), 0.2, 0.22, seg=14, mat=B('depot_green'))
    add_torus(bm, (83.45, Y - 0.25, 0.5), (0, 0, 1), 0.215, 0.012, seg=16, rseg=4, mat=B('iron'))
    add_cyl(bm, (83.6, Y - 0.06, 2.4), (83.45, Y - 0.22, 0.66), 0.025, seg=8, mat=B('iron'))    # a gutter's run led into it
    # C-104: a tarpaulin over the eaves, held with bricks; the 104A door's step a slab of something else.
    cbox(bm, (85.0, Y - 0.25, 2.62), (2.2, 0.6, 0.02), 0.004, B('depot_green'), rot=_rx(0.35))
    cbox(bm, (85.0, Y - 0.38, 2.45), (2.0, 0.02, 0.3), 0.004, B('depot_green'), rot=_rx(-0.1))
    # C-106: its door is round the corner, on the alley (a plank door in the side wall, its step); on the lane, a
    # long blank face (the graffiti's), and a stovepipe out through a broken pane, elbowed up past the eaves.
    dx_, dy_ = CROSS[1] - 0.17, 1.72                                     # on the alley wall's face, toward -x
    for sx_ in (-1, 1):
        cbox(bm, (dx_ - 0.02, dy_ + sx_ * 0.38, 1.0), (0.06, 0.06, 2.0), 0.006, B('wood'))
    for k in range(5):
        cbox(bm, (dx_ - 0.005, dy_ - 0.33 + 0.132 * (k + 0.5), 0.98), (0.03, 0.126, 1.94), 0.004, B('dado'))
    for z in (0.35, 1.55):
        cbox(bm, (dx_ - 0.03, dy_, z), (0.02, 0.6, 0.1), 0.004, B('dado'))
    add_cyl(bm, (dx_ - 0.02, dy_ - 0.26, 0.95), (dx_ - 0.06, dy_ - 0.26, 0.95), 0.012, seg=8, mat=B('steel'))
    cbox(bm, (dx_ - 0.02, dy_, 2.04), (0.06, 0.84, 0.08), 0.006, B('wood'))
    cbox(bm, (dx_ - 0.15, dy_, 0.05), (0.26, 0.9, 0.1), 0.01, B('concrete'))
    sx, sz = C106_WIN + 0.17, 1.62
    add_cyl(bm, (sx, Y + 0.15, sz), (sx, Y - 0.22, sz), 0.055, seg=12, mat=B('iron'))
    add_cyl(bm, (sx, Y - 0.22, sz - 0.04), (sx, Y - 0.22, 2.95), 0.055, seg=12, mat=B('iron'))
    add_cyl(bm, (sx, Y - 0.22, 2.95), (sx, Y - 0.22, 3.08), 0.09, 0.07, seg=12, mat=B('iron'))
    for z in (1.95, 2.45):
        cbox(bm, (sx, Y - 0.12, z), (0.04, 0.2, 0.03), 0.004, B('steel'))
    cbox(bm, (sx, Y + 0.075, sz), (0.36, 0.01, 0.3), 0.003, B('shutter'))   # a tin plate round it in the pane
    # Pots and a crate by the doors.
    dead_plant(B, C106_WIN - 0.62, Y - 0.2, 0.0, rnd, pot='paper', r=0.1, h=0.24)
    cbox(bm, (a6 + 0.3, Y - 0.22, 0.17), (0.4, 0.3, 0.34), 0.01, B('wood'), rot=_rz(0.1))
    # Their side walls on the cross alley, and on the barricade side.
    add_box(bm, (a2 + 0.08, (Y + 2.2) / 2, 1.3), (0.16, 2.2 - Y, 2.62), mat=B('plasterB'))


def build_street(m, coll):
    """Ring C as a street he walks through. Behind the lane, the back row: C-102, C-104 (and 104A), the cross alley,
    C-106, then the flood's three: C-108 (its window dimly lit onto a table still set, its door's steps going down
    into the water, the bell on its gate pillar), a stepped alley up to ring B, C-110 (the letters in its slot, the
    junction box in front), C-112 (boarded and taped shut, the water-drop mark). In front of the lane: the front row,
    cut down (build_front_row), C-111 fallen into the sink at the narrow point, the stair down at the cross alley.
    Over it: the street cable of bulbs (four still burning), the duct run with the gap where a length fell, washing
    lines across the lane. Then the square: the noticeboard, a bench, the dry fountain, the swing frame, a standpipe
    and a stair up to ring B."""
    rnd = random.Random(5015)
    back, floor_, front, over, rails, square = (Batch(m) for _ in range(6))
    Y = BACK_Y
    # ---- the lane's floor -------------------------------------------------------
    F = floor_
    l0, l1 = LANE_C
    y0 = LANE_Y[0]
    p0, p1 = POOL
    for a, b, ya, yb in ((l0, p0, y0, Y), (p0, DIP[0], y0, BANK_Y - 0.04), (DIP[1], l1, y0, Y)):
        add_box(F.bm, ((a + b) / 2, (ya + yb) / 2, -0.15), (b - a, yb - ya, 0.3), mat=F('concrete'))
    add_box(F.bm, ((SQUARE[0] + l1) / 2, (Y + 3.3) / 2, -0.15), (l1 - SQUARE[0], 3.3 - Y, 0.3), mat=F('concrete'))   # the square, deeper
    add_box(F.bm, ((ALLEY[0] + ALLEY[1]) / 2, 2.5, -0.15), (ALLEY[1] - ALLEY[0], 0.2, 0.3), mat=F('concrete'))
    # The broken back edge along the pool: slabs cracked off at the water, some tipped in.
    x = p0
    while x < DIP[0] - 0.01:
        ln = min(DIP[0] - x, rnd.uniform(0.22, 0.42))
        reach = rnd.uniform(-0.03, 0.05)
        cbox(F.bm, (x + ln / 2, BANK_Y - 0.06 + reach / 2, -0.15 - rnd.uniform(0, 0.01)), (ln - 0.01, 0.12 + reach, 0.3), 0.01, F('concrete'),
             rot=_rx(rnd.uniform(-0.03, 0.02)))
        x += ln
    for x, ang in ((83.55 + S9, 14), (85.25 + S9, -18), (86.6 + S9, 10)):
        cbox(F.bm, (x, BANK_Y + 0.16, -0.18), (0.42, 0.26, 0.08), 0.01, F('concrete'), rot=_ry(math.radians(ang)) @ _rx(math.radians(-22)))
    # Paving joints (raised grout), a kerb at the front edge, a drain channel along the back.
    for a, b, ya, yb in ((l0, p0, y0 + 0.14, Y - 0.12), (p0, DIP[0], y0 + 0.14, BANK_Y - 0.1), (DIP[1], SQUARE[0], y0 + 0.14, Y - 0.12)):
        k = math.ceil(a / 0.6)
        while k * 0.6 < b:
            add_box(F.bm, (k * 0.6, (ya + yb) / 2, 0.0), (0.012, yb - ya, 0.004), mat=F('concrete'))
            k += 1
        add_box(F.bm, ((a + b) / 2, (ya + yb) / 2 + 0.0, 0.0), (b - a, 0.012, 0.004), mat=F('concrete'))
    for a, b in ((l0, CROSS[0] - 0.1), (CROSS[1] + 0.1, DIP[0] - 0.02), (DIP[1] + 0.02, l1)):
        cbox(F.bm, ((a + b) / 2, y0 + 0.07, 0.02), (b - a, 0.14, 0.06), 0.012, F('concrete'))
    for a, b in ((l0 + 0.1, p0 - 0.1), (DIP[1] + 0.1, SQUARE[0])):
        add_box(F.bm, ((a + b) / 2, Y - 0.07, 0.002), (b - a, 0.08, 0.006), mat=F('steel'))
        for k in range(int((b - a) / 0.05)):
            add_box(F.bm, (a + 0.025 + 0.05 * k, Y - 0.07, 0.004), (0.012, 0.08, 0.006), mat=F('steel'))
    # The square's setts: a grid of joints, and a ring of kerb round the fountain.
    for k in range(int((l1 - SQUARE[0]) / 0.2)):
        add_box(F.bm, (SQUARE[0] + 0.1 + 0.2 * k, (y0 + 0.14 + 3.25) / 2, 0.0), (0.01, 3.25 - y0 - 0.14, 0.004), mat=F('concrete'))
    for k in range(int((3.25 - y0 - 0.14) / 0.2)):
        add_box(F.bm, ((SQUARE[0] + l1) / 2, y0 + 0.24 + 0.2 * k, 0.0), (l1 - SQUARE[0], 0.01, 0.004), mat=F('concrete'))

    # ---- the back row -------------------------------------------------------------
    build_new_homes(m, back, rnd)
    build_cross_alley(m, back, floor_, front, rnd)
    street_home(back, '108', *HOMES[0][1:], C108_DOOR, C108_WIN[0], 'homeplaster', 'depot_green', rnd,
                win=(C108_WIN[1], C108_WIN[2], C108_WIN[3]), kind='open', step=False, lamp=False, pipe_x=HOMES[0][2] - 0.2)
    street_home(back, '110', *HOMES[1][1:], C110_DOOR, 85.55 + S9, 'plasterA', 'pigeon', rnd, kind='shutters', slot_z=C110_SLOT[1],
                step=False, pipe_x=HOMES[1][1] + 0.24)
    street_home(back, '112', *HOMES[2][1:], C112_DOOR, 89.85 + S9, 'plasterB', 'dado', rnd, kind='boarded')
    B = back
    # The homes' feet go down into the water along the pool, and their side walls run back along the alley.
    add_box(B.bm, ((p0 + DIP[1]) / 2, Y + 0.1, (POOL_BED - 0.05) / 2), (DIP[1] - p0, 0.2, -POOL_BED + 0.05), mat=B('mud'))
    for x, sx in ((ALLEY[0], 1), (ALLEY[1], -1)):
        add_box(B.bm, (x + sx * 0.08, (Y + 3.3) / 2, 1.25), (0.16, 3.3 - Y, 2.9), mat=B('homeplaster' if sx > 0 else 'plasterA'))
        add_box(B.bm, (x + sx * 0.08, (Y + 2.4) / 2, (POOL_BED - 0.2) / 2), (0.16, 2.4 - Y, -POOL_BED + 0.2), mat=B('mud'))
    add_box(B.bm, (HOMES[2][2] - 0.08, (Y + 3.3) / 2, 1.31), (0.16, 3.3 - Y, 2.62), mat=B('plasterB'))      # C-112's side, on the square
    prism(B.bm, [(Y - 0.32, 2.62), (Y + 1.3, 3.58), (3.4, 2.7), (3.4, 2.62)], 'x', HOMES[2][2] - 0.16, HOMES[2][2], mat=B('plasterB'))   # its gable end
    for x0, x1 in ((HOMES[0][1], HOMES[0][2]), (HOMES[1][1], HOMES[1][2]), (HOMES[2][1], HOMES[2][2])):
        cbox(B.bm, ((x0 + x1) / 2, Y + 1.3 + 0.55, 3.18), (x1 - x0 + 0.06, 1.25, 0.035), 0.006, B('slate'), rot=_rx(-math.atan2(0.88, 1.1)))
    for x, y, z, r, h in ((C112_DOOR - 0.66, Y - 0.2, 0.0, 0.12, 0.3), (C112_DOOR + 0.64, Y - 0.17, 0.0, 0.09, 0.22),
                          (C108_WIN[0] - 0.22, Y - 0.01, C108_WIN[2], 0.055, 0.12), (HOMES[0][1] + 0.4, Y - 0.2, 0.0, 0.1, 0.26)):
        dead_plant(B, x, y, z, rnd, pot='paper', r=r, h=h)                        # pots by the doors, long dead
    # The alley: steps up from the water between C-108 and C-110, toward ring B, under a pipe and an arch.
    for k in range(14):
        y, z = 2.4 + 0.18 * k, -0.1 + 0.2 * (k + 1)
        cbox(B.bm, ((ALLEY[0] + ALLEY[1]) / 2, y + 0.09, z / 2 - 0.15), (ALLEY[1] - ALLEY[0] - 0.32, 0.2, z + 0.3), 0.01, B('concrete'))
    cbox(B.bm, ((ALLEY[0] + ALLEY[1]) / 2, Y + 0.1, 2.7), (ALLEY[1] - ALLEY[0], 0.24, 0.2), 0.02, B('concrete'))
    add_cyl(B.bm, (ALLEY[0], Y + 0.6, 2.35), (ALLEY[1], Y + 0.6, 2.35), 0.06, seg=10, mat=B('iron'))
    # ---- C-108: the gate pillar with the bell, and the steps down into the water ---------------------
    bx, by, bz = BELL
    cbox(B.bm, (bx, by + 0.12, 0.47), (0.24, 0.24, 0.94), 0.02, B('homeplaster'))
    cbox(B.bm, (bx, by + 0.12, 0.98), (0.3, 0.3, 0.07), 0.015, B('concrete'))
    add_sphere(B.bm, (bx, by + 0.12, 1.07), 0.08, seg=12, mat=B('concrete'))
    cbox(B.bm, (bx, by - 0.012, bz + 0.015), (0.085, 0.024, 0.15), 0.006, B('brass'))               # the bell push's plate
    cbox(B.bm, (bx, by - 0.026, bz + 0.065), (0.06, 0.004, 0.028), 0.002, B('letters'))             # a name card in it
    _wire(B.bm, _catenary((bx, by + 0.12, 0.98), (C108_DOOR - 0.6, Y - 0.02, 2.1), 0.25, 8), 0.005, B('rubber'))
    add_cyl(B.bm, (C108_DOOR - 0.6, Y - 0.02, 2.1), (C108_DOOR - 0.12, Y - 0.02, 2.22), 0.005, seg=4, mat=B('rubber'))
    for k, (ya, yb, top) in enumerate(((0.8, Y + 0.02, -0.03), (0.6, 0.8, -0.21), (0.42, 0.6, -0.4))):   # into the water
        cbox(B.bm, (C108_DOOR, (ya + yb) / 2, (top + POOL_BED) / 2), (0.98, yb - ya, top - POOL_BED), 0.012, B('concrete'))
    # A fallen garden gate, rusted, in the water by the step.
    for k in range(7):
        add_cyl(B.bm, (82.95 + S9 + 0.07 * k, 0.48, -0.32 + 0.02 * k), (82.98 + S9 + 0.07 * k, 0.78, -0.05 + 0.01 * k), 0.008, seg=5, mat=B('iron'))
    add_cyl(B.bm, (82.92 + S9, 0.5, -0.3), (83.45 + S9, 0.52, -0.18), 0.012, seg=6, mat=B('iron'))
    # ---- C-110: its threshold stood when the lane sank round it -----------------------------------
    cbox(B.bm, (C110_DOOR, Y - 0.06, (0.05 + POOL_BED) / 2), (0.98, 0.2, 0.05 - POOL_BED), 0.012, B('concrete'))
    # ---- the junction box by C-110 (its lever is the JunctionLever), its pole and the cable to the far lamp -
    jx, jy, jz = JUNCTION
    cbox(B.bm, (jx, jy + 0.12, -0.28), (0.46, 0.32, 0.6), 0.02, B('concrete'))                    # footing, down into the water
    add_cyl(B.bm, (jx + 0.1, jy + 0.27, 0.0), (jx + 0.1, jy + 0.27, 2.6), 0.035, seg=10, mat=B('steel'))
    cbox(B.bm, (jx + 0.1, jy + 0.27, 2.6), (0.08, 0.08, 0.04), 0.006, B('steel'))
    _wire(over.bm, _catenary((jx + 0.1, jy + 0.27, 2.55), (C110_DOOR - 0.55, Y - 0.03, 2.5), 0.12, 6), 0.008, over('rubber'))
    _wire(over.bm, [Vector((C110_DOOR - 0.55, Y - 0.03, 2.5)), Vector((CABLE_TOP[0], Y - 0.03, 2.5))], 0.008, over('rubber'))
    cx_, cy_, cz_ = CABLE_TOP                                                   # the lamp bracket the cable came down from
    cbox(over.bm, (cx_, Y - 0.02, 2.5), (0.1, 0.04, 0.16), 0.006, over('iron'))
    _wire(over.bm, [Vector((cx_, Y - 0.03, 2.52)), Vector((cx_, 0.75, 2.5)), Vector((cx_ + 0.02, cy_ + 0.02, cz_ + 0.02))], 0.016, over('iron'), seg=8)
    add_cyl(over.bm, (cx_ + 0.05, 0.62, 1.95), (cx_ + 0.09, 0.66, 1.82), 0.06, 0.04, seg=10, mat=over('iron'))   # its shade, fallen, caught
    # ---- the square ---------------------------------------------------------------------------------------
    S = square
    nx, ny = NOTICE
    for x in (nx - 0.46, nx + 0.46):                                            # the noticeboard: posts, frame, a little roof
        cbox(S.bm, (x, ny + 0.06, 0.68), (0.07, 0.07, 1.36), 0.01, S('wood'))
    cbox(S.bm, (nx, ny + 0.045, 0.82), (1.06, 0.05, 0.78), 0.012, S('wood'))
    for sx in (-1, 1):
        cbox(S.bm, (nx + sx * 0.3, ny + 0.06, 1.33), (0.66, 0.24, 0.03), 0.006, S('slate'), rot=_ry(sx * 0.32))
    # The bench, facing the lane: cast-iron ends, slats.
    bx0, bx1, by_ = 91.75 + S9, 92.65 + S9, 1.08
    for x in (bx0 + 0.05, bx1 - 0.05):
        cbox(S.bm, (x, by_ - 0.12, 0.2), (0.05, 0.05, 0.4), 0.008, S('iron'))
        cbox(S.bm, (x, by_ + 0.12, 0.4), (0.05, 0.05, 0.8), 0.008, S('iron'), rot=_rx(-0.12))
        cbox(S.bm, (x, by_, 0.39), (0.05, 0.36, 0.04), 0.008, S('iron'))
        cbox(S.bm, (x, by_ - 0.02, 0.62), (0.05, 0.3, 0.035), 0.008, S('iron'))
    for k in range(4):
        cbox(S.bm, ((bx0 + bx1) / 2, by_ - 0.13 + 0.085 * k, 0.43), (bx1 - bx0, 0.07, 0.025), 0.006, S('wood'))
    for k in range(3):
        cbox(S.bm, ((bx0 + bx1) / 2, by_ + 0.15 + 0.012 * k, 0.55 + 0.1 * k), (bx1 - bx0, 0.022, 0.07), 0.006, S('wood'), rot=_rx(-0.12))
    # The fountain: a round basin, dry and silted, its pedestal and bowl, a stone fish that spouted.
    fx, fy, fr = 92.95 + S9, 2.25, 0.72
    for k in range(18):
        a = 2 * math.pi * k / 18
        rot = _rz(a + math.pi / 2)
        cbox(S.bm, (fx + fr * math.cos(a), fy + fr * math.sin(a), 0.2), (2 * fr * math.sin(math.pi / 18) + 0.02, 0.14, 0.4), 0.01, S('concrete'), rot=rot)
        cbox(S.bm, (fx + (fr + 0.01) * math.cos(a), fy + (fr + 0.01) * math.sin(a), 0.43), (2 * fr * math.sin(math.pi / 18) + 0.04, 0.22, 0.06), 0.012,
             S('concrete'), rot=rot)
    add_cyl(S.bm, (fx, fy, 0.0), (fx, fy, 0.08), fr, seg=24, mat=S('mud'))
    add_cyl(S.bm, (fx, fy, 0.08), (fx, fy, 0.8), 0.13, 0.09, seg=14, mat=S('concrete'))
    add_cyl(S.bm, (fx, fy, 0.78), (fx, fy, 0.92), 0.12, 0.32, seg=18, mat=S('concrete'))
    add_cyl(S.bm, (fx, fy, 0.92), (fx, fy, 0.96), 0.33, seg=18, mat=S('concrete'))
    rounded_box((0.16, 0.08, 0.1), (fx, fy, 1.08), p=2.4, cuts=4, bm=S.bm, mat=S('concrete'), rot=_ry(-0.5), dents=((0.004, 9.0),), seed=7)
    add_wedge(S.bm, (fx + 0.06, fy, 1.13), (fx + 0.13, fy, 1.24), 0.02, 0.1, 0.02, 0.01, (0, 1, 0), mat=S('concrete'))
    add_cyl(S.bm, (fx - 0.08, fy, 1.06), (fx - 0.12, fy, 1.03), 0.018, seg=8, mat=S('concrete'))
    # The swing frame: an A at each end, the top bar; one swing hangs (SquareSwing), the other by one chain.
    sx0, sx1, sy_, top = 93.42 + S9, 94.3 + S9, 1.45, 1.95
    for x in (sx0, sx1):
        for dy in (-0.32, 0.32):
            add_cyl(S.bm, (x, sy_ + dy, 0.0), (x, sy_, top), 0.028, seg=8, mat=S('iron'))
        add_cyl(S.bm, (x, sy_ - 0.2, 0.7), (x, sy_ + 0.2, 0.7), 0.018, seg=6, mat=S('iron'))
    add_cyl(S.bm, (sx0 - 0.05, sy_, top), (sx1 + 0.05, sy_, top), 0.035, seg=10, mat=S('iron'))
    x2 = 94.08 + S9                                                                  # the broken swing: one chain, the seat hanging from it
    add_cyl(S.bm, (x2, sy_, top - 0.02), (x2 + 0.01, sy_, 0.62), 0.006, seg=4, mat=S('steel'))
    cbox(S.bm, (x2 + 0.01, sy_, 0.48), (0.03, 0.14, 0.3), 0.006, S('wood'), rot=_ry(0.08))
    _wire(S.bm, [Vector((x2 + 0.18, sy_, top - 0.02)), Vector((x2 + 0.18, sy_ + 0.02, top - 0.25)), Vector((x2 + 0.12, sy_ - 0.05, top - 0.35))], 0.006,
          S('steel'))
    # A tricycle, on its side by the bench; a ball under it.
    tx, ty = 91.55 + S9, 1.55
    for (ox, oy, r) in ((tx - 0.18, ty, 0.11), (tx + 0.14, ty - 0.1, 0.07), (tx + 0.14, ty + 0.1, 0.07)):
        add_torus(S.bm, (ox, oy, 0.03 + (0.0 if ox < tx else 0.0)), (0, 0, 1), r, 0.012, seg=16, rseg=5, mat=S('rubber'))
    _wire(S.bm, [Vector((tx - 0.18, ty, 0.05)), Vector((tx + 0.0, ty, 0.06)), Vector((tx + 0.14, ty, 0.05))], 0.014, S('childpaint'), seg=6)
    add_cyl(S.bm, (tx + 0.14, ty - 0.1, 0.05), (tx + 0.14, ty + 0.1, 0.05), 0.01, seg=6, mat=S('steel'))
    cbox(S.bm, (tx, ty, 0.08), (0.12, 0.05, 0.03), 0.006, S('childpaint'))
    # The square's back: a retaining wall with a stair along it up toward ring B.
    cbox(S.bm, ((SQUARE[0] + l1) / 2, 3.42, 1.45), (l1 - SQUARE[0], 0.24, 3.1), 0.02, S('concrete'))
    cbox(S.bm, ((SQUARE[0] + l1) / 2, 3.3, 2.98), (l1 - SQUARE[0], 0.32, 0.08), 0.015, S('concrete'))
    for k in range(15):
        x, z = 90.9 + S9 + 0.22 * k, 0.19 * (k + 1)
        cbox(S.bm, (x + 0.11, 3.0, z / 2), (0.22, 0.55, z), 0.008, S('concrete'))
    _wire(S.bm, [Vector((90.95 + S9, 2.74, 0.9)), Vector((90.9 + S9 + 0.22 * 15, 2.74, 0.9 + 0.19 * 15))], 0.018, S('iron'), seg=8)
    for k in range(0, 16, 3):
        add_cyl(S.bm, (90.95 + S9 + 0.22 * k, 2.74, 0.19 * k), (90.95 + S9 + 0.22 * k, 2.74, 0.19 * k + 0.9), 0.012, seg=6, mat=S('iron'))
    # ---- the front side: the lane's edge; the front row stands on beyond it (build_front_row); C-111, gone into
    # the sink at the narrow point; the square's parapet and a storey's drop to the lower roofs past it -----------
    # (front_cap: from the lane camera, 2.15 up and 5.8 out, nothing here rises over about 0.42 on the play line.)
    R = front
    yk0, yk1 = FRONT_Y
    lf = WORLD_END
    add_box(R.bm, ((l0 - 1.5 + lf) / 2, -6.2, -2.7), (lf - l0 + 1.5, 4.4, 0.2), mat=R('concrete'))   # the lower lanes, far below
    add_box(R.bm, ((l0 + SQUARE[0]) / 2, -4.1, -1.4), (SQUARE[0] - l0, 0.14, 2.8), mat=R('concrete'))   # the front row's terrace, its drop
    add_box(R.bm, ((SQUARE[0] + lf) / 2, -1.08, -1.4), (lf - SQUARE[0], 0.18, 2.8), mat=R('concrete'))   # the square's, nearer
    for k in range(1, 6):
        add_box(R.bm, ((SQUARE[0] + lf) / 2, -1.172, -0.46 * k), (lf - SQUARE[0], 0.006, 0.018), mat=R('concrete'))
    add_box(R.bm, (SQUARE[0] + 0.07, -2.6, -1.4), (0.14, 3.0, 2.8), mat=R('concrete'))
    cbox(R.bm, ((SQUARE[0] + lf) / 2, (yk0 + yk1) / 2, 0.06), (lf - SQUARE[0], yk1 - yk0, 0.12), 0.01, R('concrete'))    # the square's parapet
    cbox(R.bm, ((SQUARE[0] + lf) / 2, (yk0 + yk1) / 2, 0.135), (lf - SQUARE[0] + 0.02, yk1 - yk0 + 0.04, 0.05), 0.014, R('concrete'))
    for x in (SQUARE[0] + 0.8, SQUARE[0] + 2.6, SQUARE[0] + 4.2, 105.0, 108.4):            # weep holes
        add_cyl(R.bm, (x, -1.16, -0.32), (x, -1.24, -0.34), 0.04, seg=8, mat=R('iron'))
    # C-111, at the narrow point: when the lane went down it took the house's front with it. Its floor tips toward the
    # water, its walls are a line of stumps and a heap, a door lies flat in the rubble; nothing stands.
    d0, d1 = DIP[0], DIP[1]
    yf = -1.21
    for k in range(5):                                                         # its floor, broken and tipped toward the lane
        xa = d0 + 0.05 + (d1 - d0 - 0.1) * k / 5
        cbox(R.bm, (xa + (d1 - d0 - 0.1) / 10, -2.6, -0.32 + 0.06 * (k % 2)), ((d1 - d0 - 0.1) / 5 - 0.03, 2.7, 0.14), 0.01, R('concrete'),
             rot=_rx(math.radians(-11 + 3 * (k % 3))))
    ragged_x(R, d0 - 0.12, d0 + 0.08, -4.05, yf, lambda x: 0.55, 'plasterB', rnd)
    ragged_y(R, -4.05, yf, d0 - 0.06, d0 + 0.06, lambda y: 1.2 + (y + 3.9) * -0.3, 'plasterB', rnd, z0=-0.4)
    ragged_y(R, -4.05, yf, d1 - 0.06, d1 + 0.06, lambda y: 1.1 + (y + 3.9) * -0.3, 'plasterA', rnd, z0=-0.4)
    ragged_x(R, d0, d1, -4.05, -3.9, lambda x: 1.0 + 0.25 * math.sin(x * 4.0), 'plasterB', rnd, z0=-0.4)
    rubble(R, (d0 + d1) / 2 - 0.2, -2.0, 0.6, 0.12, rnd, mats=('masonry', 'plasterB', 'slate', 'concrete'), n=22, z0=-0.3)
    rubble(R, d1 - 0.35, -3.2, 0.5, 0.45, rnd, mats=('masonry', 'plasterB', 'slate'), n=14, z0=-0.2)
    door_leaf(R, Matrix.Translation((d0 + 0.25, -3.75, -0.14)) @ _rz(0.12) @ _rx(math.radians(-88)), 0.82, 1.96, 0.045, R('pigeon'), R('brass'), slot_z=0.9,
              both=False)
    cbox(R.bm, (d0 + 0.75, -2.9, 0.05), (0.09, 1.9, 0.12), 0.01, R('wood'), rot=_rz(0.5) @ _rx(0.2))
    # Washing poles in the front row's walls (thin: they may stand tall), and the gaps between its homes.
    for x0_, x1_ in ((83.55, 83.6), (CROSS[0] - 0.1, CROSS[0]), (CROSS[1], CROSS[1] + 0.1), (92.55, 92.6), (99.25, SQUARE[0])):
        ragged_y(R, -4.05, yk0, x0_, x1_, lambda y: 0.3, 'concrete', rnd)
    # ---- over the lane: the cable of bulbs, its brackets, the duct run, the washing ---------------------
    O = over
    brackets = [81.35, 83.75, CROSS[0] - 0.05, CROSS[1] + 0.05, 89.95, HOMES[0][2] - 0.3, 86.3 + S9, 88.2 + S9, HOMES[2][2] - 0.08]
    cy = 0.5

    def cable_z(x):
        for a, b in zip(brackets, brackets[1:]):
            if a <= x <= b:
                return 2.5 - 0.15 * math.sin(math.pi * (x - a) / (b - a))
        return 2.5
    for x in brackets:
        _wire(O.bm, [Vector((x, Y - 0.02, 2.62)), Vector((x, cy, 2.52))], 0.012, O('iron'), seg=6)
        add_cyl(O.bm, (x, Y - 0.02, 2.45), (x, (Y + cy) / 2, 2.58), 0.008, seg=5, mat=O('iron'))
    for a, b in zip(brackets, brackets[1:]):
        pts = [a + (b - a) * k / 6 for k in range(7)]
        _wire(O.bm, [Vector((p, cy, cable_z(p))) for p in pts], 0.006, O('rubber'))
    live, dead = bmesh.new(), bmesh.new()
    bulbs = [(81.65, True), (82.9, False), (84.6, False), (85.6, False), (86.8, True), (88.4, False), (89.4, False),
             (81.65 + S9, True), (82.7 + S9, False), (83.9 + S9, False), (85.2 + S9, False), (86.3 + S9, True), (87.3 + S9, False),
             (89.2 + S9, False)]
    for k, (x, lit) in enumerate(bulbs):
        z0 = cable_z(x)
        z1 = z0 - 0.2 - 0.05 * (k % 2)
        tilt = 0.06 if k in (3, 10) else 0.0
        add_cyl(O.bm, (x, cy, z0), (x + tilt, cy, z1), 0.004, seg=4, mat=O('rubber'))
        add_cyl(O.bm, (x + tilt, cy, z1), (x + tilt, cy, z1 - 0.05), 0.018, seg=8, mat=O('steel'))
        add_sphere(live if lit else dead, (x + tilt * 1.1, cy, z1 - 0.085), 0.034, seg=10, scale=(1, 1, 1.2))
    # The square's lamp, on a bracket off C-112's corner, over the noticeboard: it still burns, unsteadily.
    lx, lz = HOMES[2][2] + 0.2, 2.3
    _wire(O.bm, [Vector((HOMES[2][2] - 0.08, Y - 0.04, 2.5)), Vector((lx, 0.62, 2.48)), Vector((lx, 0.62, lz + 0.1))], 0.014, O('iron'), seg=8)
    add_cyl(O.bm, (lx, 0.62, lz + 0.1), (lx, 0.62, lz - 0.02), 0.03, 0.15, seg=14, mat=O('depot_green'))
    add_sphere(live, (lx, 0.62, lz - 0.05), 0.036, seg=10, scale=(1, 1, 1.2))
    _obj('LaneBulb', live, [m['lanebulb']], coll)
    _obj('D5DeadBulbs', dead, [m['deadbulb']], coll)
    # The duct run on brackets along the facades, broken where a length fell (PushDuct, below it).
    dy, dz = 0.78, 2.3
    g0, g1 = DUCT[0] - 0.15, DUCT[1] + 0.15
    for a, b in ((NEW_HOMES[0][1] + 0.1, CROSS[0] - 0.12), (CROSS[1] + 0.12, g0), (g1, HOMES[2][2] - 0.1)):
        cbox(O.bm, ((a + b) / 2, dy, dz), (b - a, DUCT[3] - 0.024, DUCT[2] - 0.012), 0.01, O('plate'))
        x = a + 0.3
        while x < b:
            cbox(O.bm, (x, dy, dz), (0.03, DUCT[3], DUCT[2]), 0.006, O('plate'))
            add_box(O.bm, (x, (dy + Y) / 2 + 0.05, dz + 0.15), (0.03, Y - dy + 0.12, 0.03), mat=O('steel'))
            x += 1.2
    for x, sgn in ((g0, 1), (g1, -1)):                                          # torn ends, bent down
        add_box(O.bm, (x + sgn * 0.05, dy - 0.06, dz - 0.15), (0.06, 0.28, 0.12), mat=O('plate'), rot=_ry(sgn * 0.6))
        add_box(O.bm, (x + sgn * 0.04, dy + 0.12, dz - 0.12), (0.05, 0.1, 0.1), mat=O('plate'), rot=_ry(sgn * 0.9) @ _rx(0.4))
    for x, ln in ((g0 + 0.5, 0.3), (g1 - 0.6, 0.22)):                           # the hangers that let go
        add_box(O.bm, (x, dy + 0.12, dz + 0.15 - ln / 2), (0.02, 0.004, ln), mat=O('steel'), rot=_ry(0.2))
    # Washing lines across the lane, from the back row out to a messenger wire strung along the front from the
    # barricade's rock to the square's lamp bracket, hung from the dark overhead (all of it above the lane camera's
    # frame), the washing long dry on them: it hangs into the top of the frame, over his head.
    W = Batch(m)
    MESSENGER_Z = 2.48
    mx0, mx1 = 81.25, HOMES[2][2] + 0.1
    hangers = [mx0 + (mx1 - mx0) * k / 5 for k in range(6)]
    for a, b in zip(hangers, hangers[1:]):
        _wire(W.bm, _catenary((a, -1.0, MESSENGER_Z), (b, -1.0, MESSENGER_Z), 0.04, 6), 0.005, W('iron'))
    for x in hangers:
        add_cyl(W.bm, (x, -1.0, MESSENGER_Z), (x + 0.05, -1.1, 6.5), 0.006, seg=4, mat=W('iron'))
    add_cyl(W.bm, (mx1, -1.0, MESSENGER_Z), (HOMES[2][2] - 0.08, Y - 0.04, 2.5), 0.006, seg=4, mat=W('iron'))
    for (xa, za), (xb, zb), items in (((81.6, 2.42), (83.4, 2.3), (('shirt', 'paper'), ('sock', 'toy'), ('sock', 'toy'), ('trousers', 'dado'))),
                                      ((CROSS[1] + 0.15, 2.4), (CROSS[0] - 0.3, 2.28), (('sheet', 'letters'), ('dress', 'childpaint'), ('sock', 'toypatch'),
                                                                                      ('sock', 'toypatch'))),
                                      ((81.45 + S9, 2.42), (92.9, 2.3), (('shirt', 'letters'), ('sock', 'toy'), ('sock', 'toy'), ('trousers', 'dado'),
                                                                         ('dress', 'toypatch'))),
                                      ((88.3 + S9, 2.42), (99.0, 2.32), (('sheet', 'letters'), ('shirt', 'toy'), ('sock', 'childpaint')))):
        pa, pb = Vector((xa, Y - 0.05, za)), Vector((xb, -1.0, MESSENGER_Z))
        add_torus(W.bm, (xb, -1.0, MESSENGER_Z - 0.012), (1, 0, 0), 0.014, 0.003, seg=8, rseg=3, mat=W('iron'))   # hooked over the wire
        cbox(W.bm, (xa, Y - 0.04, za), (0.04, 0.08, 0.04), 0.006, W('iron'))
        pts = _catenary(pa, pb, 0.22, 12)
        _wire(W.bm, pts, 0.004, W('rubber'))
        ang = math.atan2(pb.y - pa.y, pb.x - pa.x)
        for k, (kind, mat) in enumerate(items):
            t = (k + 1) / (len(items) + 1)
            i = t * 12
            p = pts[int(i)].lerp(pts[min(12, int(i) + 1)], i - int(i))
            cloth(W, p, ang, kind, mat, rnd)
    W.done('D5Washing', coll)
    floor_.done('D5Lane', coll)
    back.done('D5Homes', coll)
    front.done('D5LaneFront', coll)
    over.done('D5Overhead', coll)
    rails.done('D5Railings', coll)
    square.done('D5Square', coll)
    # Door plates (and C-114's by its door is with the house).
    for num, x0, x1 in HOMES:
        dx = {'108': C108_DOOR, '110': C110_DOOR, '112': C112_DOOR}[num]
        _plane(f'D5Plate{num}', (0.26, 0.114), (dx + 0.43 + 0.2, BACK_Y - 0.014, 1.5),
               _image_material(f'D5Plate{num}Mat', _tex(f'plate_c{num}.png'), rough=0.3), coll)
    # The noticeboard's face, and a drawing pinned low on its leg.
    _plane('D5Noticeboard', (1.0, 0.7), (NOTICE[0], NOTICE[1] + 0.017, 0.82), _image_material('D5NoticeMat', _tex('noticeboard.png'), rough=0.85), coll)
    _plane('D5WhiteDrawing', (0.24, 0.17), (NOTICE[0] - 0.46, NOTICE[1] + 0.022, 0.42),
           _image_material('D5WhiteDrawingMat', _tex('white_drawing.png'), rough=0.85), coll, rot=_ry(math.radians(5)) @ _rx(math.radians(90)))
    build_street_props(m, coll, rnd)


def build_street_props(m, coll, rnd):
    """The street's working parts and its few left-behind things, as their own objects: C-108's bell and its lamp and
    gong, the junction box and its lever, the downed cable and its tip, the swing that still hangs, a bicycle."""
    bx, by, bz = BELL
    bm = bmesh.new()                       # the push: a domed brass button in its collar, rubbed bright
    add_cyl(bm, (bx, by - 0.024, bz), (bx, by - 0.034, bz), 0.019, 0.018, seg=16)
    add_sphere(bm, (bx, by - 0.034, bz), 0.014, seg=14, scale=(1, 0.55, 1))
    _obj_at('C108Bell', bm, [m['brass']], coll, (bx, by - 0.032, bz))
    bm = bmesh.new()                       # the lamp: a small amber jewel over the push, in a brass bezel on the plate
    add_sphere(bm, (bx, by - 0.03, bz + 0.05), 0.0085, seg=12, scale=(1, 0.7, 1))
    _obj_at('C108BellLamp', bm, [m['belllamp']], coll, (bx, by - 0.03, bz + 0.05))
    bm = bmesh.new()                                                            # the bell itself, over C-108's door
    gx, gz = C108_DOOR - 0.12, 2.24
    add_sphere(bm, (0, -0.05, 0), 0.075, seg=16, scale=(1, 0.55, 1), mat=0)
    cbox(bm, (0, -0.005, 0), (0.05, 0.02, 0.05), 0.004, 1)
    add_cyl(bm, (0.07, -0.06, -0.06), (0.02, -0.09, 0.0), 0.006, seg=6, mat=1)
    add_sphere(bm, (0.02, -0.095, 0.005), 0.012, seg=8, mat=1)
    bmesh.ops.translate(bm, vec=(gx, BACK_Y, gz), verts=bm.verts)
    _obj_at('C108Gong', bm, [m['brass'], m['iron']], coll, (gx, BACK_Y, gz))
    # The junction box: a green feeder pillar on the bank by C-110, its door, a danger plate; the lever on its face.
    jx, jy, jz = JUNCTION
    bm = bmesh.new()                       # mats: 0 green, 1 steel, 2 yellow, 3 dark
    cbox(bm, (jx, jy + 0.11, 0.44), (0.38, 0.22, 0.8), 0.02, 0)
    cbox(bm, (jx, jy + 0.11, 0.87), (0.42, 0.26, 0.06), 0.015, 0)
    cbox(bm, (jx - 0.03, jy - 0.002, 0.42), (0.26, 0.008, 0.6), 0.004, 0)
    for z in (0.22, 0.62):
        add_cyl(bm, (jx - 0.165, jy - 0.002, z), (jx - 0.165, jy - 0.002, z + 0.07), 0.01, seg=6, mat=1)
    cbox(bm, (jx - 0.03, jy - 0.008, 0.73), (0.11, 0.004, 0.09), 0.002, 2)
    add_wedge(bm, (jx - 0.03, jy - 0.011, 0.7), (jx - 0.03, jy - 0.011, 0.76), 0.06, 0.005, 0.002, 0.002, (1, 0, 0), mat=3)
    for k in range(4):
        add_box(bm, (jx + 0.05, jy - 0.003, 0.18 + 0.03 * k), (0.12, 0.004, 0.01), mat=3)
    add_cyl(bm, (jx + 0.12, jy - 0.004, jz), (jx + 0.12, jy - 0.004, jz + 0.001), 0.05, seg=16, mat=1)   # the lever's boss
    for a_ in (0.0, -130.0):                                                    # OFF and ON, stamped on the door, worn
        r_ = math.radians(-25 + a_)
        cbox(bm, (jx + 0.12 + 0.085 * math.sin(r_), jy - 0.006, jz + 0.085 * math.cos(r_)), (0.016, 0.003, 0.016), 0.002, 1)
    _obj_at('JunctionBox', bm, [m['depot_green'], m['steel'], m['yellow'], m['shaft']], coll, (jx, jy + 0.11, 0.0))
    bm = bmesh.new()                       # the lever: a hub, a steel arm, a black grip worn bright; modelled OFF, up and tipped back left
    lx = jx + 0.12
    add_cyl(bm, (0, 0.0, 0), (0, -0.03, 0), 0.032, seg=14, mat=1)
    arm = _ry(math.radians(-25))
    add_cyl(bm, arm @ Vector((0, -0.02, 0)), arm @ Vector((0, -0.02, 0.2)), 0.011, seg=8, mat=2)
    add_cyl(bm, arm @ Vector((0, -0.02, 0.17)), arm @ Vector((0, -0.02, 0.27)), 0.02, 0.018, seg=12, mat=0)
    add_sphere(bm, arm @ Vector((0, -0.02, 0.272)), 0.02, seg=10, mat=0)
    add_cyl(bm, arm @ Vector((0, -0.02, 0.165)), arm @ Vector((0, -0.02, 0.175)), 0.021, seg=12, mat=2)      # a steel ferrule
    bmesh.ops.translate(bm, vec=(lx, jy - 0.005, jz), verts=bm.verts)
    _obj_at('JunctionLever', bm, [m['handleblack'], m['steel'], m['pawlsteel']], coll, (lx, jy - 0.005, jz))
    # The downed cable: from the broken bracket, a long sagging loop down into the water; its frayed end (the tip).
    cx, cy, cz = CABLE_TOP
    tx, ty = CABLE_TIP
    pts = []
    for k in range(17):
        t = k / 16
        p = Vector((cx + (tx - cx) * t, cy + (ty - cy) * t, cz + (WATER_Z + 0.06 - cz) * t))
        p.x += 0.22 * math.sin(math.pi * t) * (1 - t)
        p.y -= 0.12 * math.sin(math.pi * t)
        pts.append(p)
    bm = bmesh.new()
    _wire(bm, pts, 0.012, 0, seg=6)
    _obj_at('LaneCable', bm, [m['rubber']], coll, (cx, cy, cz))
    bm = bmesh.new()                       # mats: 0 copper strands, 1 rubber, scorched
    add_cyl(bm, (tx, ty, WATER_Z + 0.07), (tx, ty, WATER_Z + 0.02), 0.015, 0.016, seg=8, mat=1)
    r2 = random.Random(5150)
    for k in range(7):
        a = r2.uniform(0, 2 * math.pi)
        add_cyl(bm, (tx, ty, WATER_Z + 0.025), (tx + 0.03 * math.cos(a), ty + 0.03 * math.sin(a), WATER_Z - r2.uniform(0.02, 0.06)), 0.0025,
                seg=4, mat=0)
    _obj_at('LaneCableTip', bm, [m['copper'], m['rubber']], coll, (tx, ty, WATER_Z))
    # The swing that still hangs, its origin at the top bar: the game can let it sway.
    sx0, sy_, top = 93.62 + S9, 1.45, 1.95
    bm = bmesh.new()                       # mats: 0 chain, 1 seat
    for x in (sx0, sx0 + 0.3):
        add_cyl(bm, (x, sy_, top - 0.02), (x, sy_, 0.47), 0.006, seg=4, mat=0)
        for k in range(10):
            add_torus(bm, (x, sy_, top - 0.08 - k * 0.14), (1, 0, 0) if k % 2 else (0, 1, 0), 0.016, 0.003, seg=8, rseg=3, mat=0)
        add_torus(bm, (x, sy_, top - 0.01), (1, 0, 0), 0.03, 0.006, seg=10, rseg=4, mat=0)
    cbox(bm, (sx0 + 0.15, sy_, 0.45), (0.42, 0.16, 0.035), 0.008, 1)
    _obj_at('SquareSwing', bm, [m['steel'], m['wood']], coll, (sx0 + 0.15, sy_, top))
    # A bicycle, left leaning on C-112's wall.
    bm = bmesh.new()                       # mats: 0 frame, 1 tyres, 2 seat
    bxx, byy = 89.25 + S9, BACK_Y - 0.16
    lean = _rx(math.radians(10))
    def L(v):
        return Vector((bxx, byy, 0)) + lean @ Vector(v)
    for x in (-0.42, 0.42):
        add_torus(bm, L((x, 0, 0.3)), lean @ Vector((0, 1, 0)), 0.29, 0.016, seg=24, rseg=5, mat=1)
        add_cyl(bm, L((x, -0.02, 0.3)), L((x, 0.02, 0.3)), 0.03, seg=8, mat=0)
    for a, b in (((-0.42, 0, 0.3), (-0.08, 0, 0.3)), ((-0.08, 0, 0.3), (-0.16, 0, 0.72)), ((-0.08, 0, 0.3), (0.3, 0, 0.68)),
                 ((-0.16, 0, 0.72), (0.3, 0, 0.68)), ((0.3, 0, 0.68), (0.42, 0, 0.3)), ((-0.42, 0, 0.3), (-0.16, 0, 0.72)),
                 ((0.3, 0, 0.68), (0.27, 0, 0.84))):
        add_cyl(bm, L(a), L(b), 0.014, seg=6, mat=0)
    add_cyl(bm, L((0.27, -0.2, 0.86)), L((0.27, 0.2, 0.86)), 0.012, seg=6, mat=0)
    rounded_box((0.2, 0.08, 0.05), L((-0.17, 0, 0.76)), p=2.4, cuts=3, bm=bm, mat=2)
    _obj('D5Bicycle', bm, [m['depot_green'], m['rubber'], m['paper']], coll, sharp=50)


def build_c108_room(m, coll):
    """Behind C-108's window: a small room, the lamp over the table still on, dimly, and the table set for
    a meal nobody came back to. The water stood over it too: the cloth is silted, a cup lies where it
    floated, the floor is mud; the plates stayed put."""
    cw, cww, cz0, cz1 = C108_WIN
    rx0, rx1, ry0, ry1 = cw - 0.62, cw + 0.62, BACK_Y + 0.2, 2.35
    bm = bmesh.new()                       # mats: 0 plaster, 1 floorboards
    add_box(bm, ((rx0 + rx1) / 2, ry1 + 0.06, 1.15), (rx1 - rx0 + 0.24, 0.12, 2.3))
    for x in (rx0 - 0.06, rx1 + 0.06):
        add_box(bm, (x, (ry0 + ry1) / 2, 1.15), (0.12, ry1 - ry0, 2.3))
    add_box(bm, ((rx0 + rx1) / 2, (ry0 + ry1) / 2, -0.03), (rx1 - rx0, ry1 - ry0, 0.06), mat=1)
    add_box(bm, ((rx0 + rx1) / 2, (ry0 + ry1) / 2, 2.3), (rx1 - rx0, ry1 - ry0, 0.08))
    _obj('D5Home108Room', bm, [m['homeplaster'], m['pigeon']], coll)
    tx, ty, top = cw, 1.82, 0.74
    bm = bmesh.new()                       # mats: 0 wood, 1 crockery, 2 cloth, 3 steel
    add_box(bm, (tx, ty, top - 0.02), (0.92, 0.66, 0.04))
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_box(bm, (tx + sx * 0.41, ty + sy * 0.28, (top - 0.04) / 2), (0.045, 0.045, top - 0.04))
    add_box(bm, (tx, ty, top + 0.003), (0.96, 0.7, 0.006), mat=2)
    add_box(bm, (tx, ty - 0.35, top - 0.06), (0.96, 0.006, 0.12), mat=2)
    rnd = random.Random(5080)
    places = ((tx - 0.24, ty - 0.17, 0.1), (tx + 0.24, ty - 0.17, 0.1), (tx, ty + 0.18, 0.075))   # two grown-ups, one small
    for k, (px_, py_, r) in enumerate(places):
        add_cyl(bm, (px_, py_, top + 0.006), (px_, py_, top + 0.022), r, r * 0.8, seg=14, mat=1)
        add_box(bm, (px_ - r - 0.03, py_, top + 0.009), (0.012, 0.15, 0.004), mat=3)
        add_box(bm, (px_ + r + 0.03, py_, top + 0.009), (0.012, 0.16, 0.004), mat=3)
        if k != 1:
            cx_, cy_ = px_ + r + 0.08, py_ + 0.1
            add_cyl(bm, (cx_, cy_, top + 0.006), (cx_, cy_, top + 0.08), 0.032, 0.036, seg=8, mat=1)
            add_torus(bm, (cx_ + 0.04, cy_, top + 0.045), (0, 1, 0), 0.018, 0.005, seg=6, rseg=3, mat=1)
    cx_, cy_ = tx + 0.36, ty - 0.02
    p0 = Vector((cx_, cy_, top + 0.04))
    add_cyl(bm, p0 - Vector((0.036, 0.012, 0)), p0 + Vector((0.036, 0.012, 0)), 0.034, 0.03, seg=8, mat=1)
    add_cyl(bm, (tx - 0.02, ty + 0.0, top + 0.006), (tx - 0.02, ty, top + 0.17), 0.055, 0.042, seg=10, mat=1)
    add_torus(bm, (tx - 0.085, ty, top + 0.1), (0, 1, 0), 0.035, 0.007, seg=6, rseg=3, mat=1)
    add_cyl(bm, (tx + 0.12, ty + 0.05, top + 0.006), (tx + 0.12, ty + 0.05, top + 0.025), 0.09, seg=10, mat=0)
    for k, (x, y, ang) in enumerate(((tx - 0.3, ty + 0.46, 0.0), (tx + 0.3, ty + 0.46, 0.1), (tx + 0.02, ty - 0.32, math.pi - 0.25))):
        rot = _rz(ang)
        c = Vector((x, y, 0))
        add_box(bm, c + rot @ Vector((0, 0, 0.44)), (0.4, 0.38, 0.03), rot=rot)
        for sx in (-1, 1):
            add_box(bm, c + rot @ Vector((sx * 0.17, 0.17, 0.46)), (0.03, 0.03, 0.92), rot=rot)
            add_box(bm, c + rot @ Vector((sx * 0.17, -0.16, 0.22)), (0.03, 0.03, 0.44), rot=rot)
        add_box(bm, c + rot @ Vector((0, 0.17, 0.84)), (0.38, 0.025, 0.08), rot=rot)
    lz = 1.5
    add_cyl(bm, (tx, ty, 2.26), (tx, ty, lz + 0.1), 0.004, seg=4, mat=3)
    add_cyl(bm, (tx, ty, lz + 0.1), (tx, ty, lz - 0.02), 0.04, 0.17, seg=12, mat=1)
    _obj('D5Table108', bm, [m['wood'], m['letters'], m['paper'], m['steel']], coll, sharp=50)
    bm = bmesh.new()
    add_sphere(bm, (tx, ty, lz + 0.0), 0.03, seg=10)
    _obj('C108Lamp', bm, [m['c108lamp']], coll)
    _mud_patches('D5Mud108', [(tx + rnd.uniform(-0.45, 0.45), rnd.uniform(1.4, 2.2), 0.0, rnd.uniform(0.14, 0.24)) for _ in range(4)],
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
    rot = _rz(math.radians(-7)) @ _rx(math.radians(52))
    bmesh.ops.transform(bm, matrix=rot, verts=bm.verts)
    inner = rot @ Vector((0, h / 2, 0))
    origin = Vector((sx_ + 0.05, BACK_Y + 0.13 - 0.03, sz_)) - inner
    me = bpy.data.meshes.new('C110Letter')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new('C110Letter', me)
    coll.objects.link(ob)
    ob.location = origin
    return ob


def build_c110_letters(m, coll):
    """Letters jammed in C-110's slot (its door is set back in the reveal), more on its threshold, a few washed up
    on the bank, and the one sticking out, which he can pull free (C110Letter)."""
    sx_, sz_ = C110_SLOT
    yd = BACK_Y + 0.13 - 0.03
    bm = bmesh.new()
    rnd = random.Random(5020)
    for k in range(5):
        add_box(bm, (sx_ + rnd.uniform(-0.07, 0.07), yd, sz_ + 0.01 + k * 0.004), (0.16, 0.04, 0.003),
                rot=_rz(rnd.uniform(-0.15, 0.15)) @ _rx(math.radians(rnd.uniform(-20, 10))))
    for k in range(3):
        add_box(bm, (sx_ + rnd.uniform(-0.3, 0.3), BACK_Y - 0.06 + rnd.uniform(-0.02, 0.02), 0.052 + k * 0.002), (0.16, 0.11, 0.003),
                rot=_rz(rnd.uniform(-0.3, 0.3)))
    for k in range(4):
        add_box(bm, (POOL[0] + 0.3 + rnd.uniform(0.0, 2.2), rnd.uniform(-0.5, 0.15), 0.003 + k * 0.002), (0.16, 0.11, 0.003),
                rot=_rz(rnd.uniform(0, 3)))
    _obj('D5Letters', bm, [m['letters']], coll)
    build_c110_letter(m, coll)
    # C-112: taped shut, and the water-drop mark sprayed on its door above the tape.
    tape = bpy.data.materials['D5TapeMat']
    yd = BACK_Y + 0.13 - 0.03
    for k, a in enumerate((32, -32)):
        _plane(f'D5DoorTape{k}', (1.15, 0.06), (C112_DOOR, yd - 0.004 - 0.002 * k, 1.0), tape, coll,
               rot=_ry(math.radians(a)) @ _rx(math.radians(90)), uv_repeat=(5, 1))
    _plane('D5DropMark112', (0.34, 0.34), (C112_DOOR, yd - 0.002, 1.46),
           _image_material('D5DropMarkMat', _tex('drop_mark.png'), rough=0.6, alpha=True), coll,
           rot=_ry(math.radians(-3)) @ _rx(math.radians(90)))


def build_flood(m, coll):
    """Where the lane sank: the pool along the back of the lane from C-108's step to C-112, deep (the White's
    water), into the alley's foot, and across the whole lane at the narrow point, where one slab went down only
    0.25 and lies there under the water: the duct, pushed in, comes to rest on it, its top level with the lane.
    FloodDip: the bed, the pool's walls, the sunk slab, rubble. FloodWater: one still dark sheet. A scum line on
    every wall at the water, pale scum drifted into the corners, a few things afloat; mud dried on the lane."""
    p0, p1 = POOL
    d0, d1, dz = DIP
    rnd = random.Random(5090)
    B = Batch(m)
    # The bed, deep, and the walls of the hole: the lane's broken slab edges and the earth under them.
    add_box(B.bm, ((p0 + p1) / 2, (BANK_Y + BACK_Y) / 2, POOL_BED - 0.05), (p1 - p0, BACK_Y - BANK_Y, 0.1), mat=B('mud'))
    add_box(B.bm, ((d0 + d1) / 2, (-1.1 + BANK_Y) / 2, POOL_BED - 0.05), (d1 - d0, BANK_Y + 1.1, 0.1), mat=B('mud'))
    add_box(B.bm, ((ALLEY[0] + ALLEY[1]) / 2, (BACK_Y + 2.4) / 2, POOL_BED - 0.05), (ALLEY[1] - ALLEY[0], 2.4 - BACK_Y, 0.1), mat=B('mud'))
    add_box(B.bm, ((p0 + d0) / 2, BANK_Y - 0.1, (POOL_BED - 0.3) / 2), (d0 - p0, 0.2, -POOL_BED - 0.3), mat=B('mud'))   # under the bank's edge
    for x, sx in ((d0, -1), (d1, 1)):                                          # the cut's two ends, under the slab
        add_box(B.bm, (x + sx * 0.1, (LANE_Y[0] + BANK_Y) / 2, (POOL_BED - 0.3) / 2), (0.2, BANK_Y - LANE_Y[0], -POOL_BED - 0.3), mat=B('mud'))
        add_box(B.bm, (x + sx * 0.1, (BANK_Y + BACK_Y) / 2, (POOL_BED - 0.3) / 2), (0.2, BACK_Y - BANK_Y, -POOL_BED - 0.3), mat=B('mud'))
    add_box(B.bm, (p0 - 0.1, (BANK_Y + BACK_Y) / 2, (POOL_BED - 0.3) / 2), (0.2, BACK_Y - BANK_Y, -POOL_BED - 0.3), mat=B('mud'))
    add_box(B.bm, (p0 - 0.1, (BANK_Y + BACK_Y) / 2, -0.15), (0.2, BACK_Y - BANK_Y, 0.3), mat=B('concrete'))
    add_box(B.bm, ((d0 + d1) / 2, -1.12, (POOL_BED - 0.05) / 2), (d1 - d0 + 0.3, 0.18, -POOL_BED + 0.05), mat=B('concrete'))   # the front wall held
    x = d0 - 0.15                                                              # its top, broken down to the water
    while x < d1 + 0.15:
        ln = rnd.uniform(0.16, 0.3)
        cbox(B.bm, (x + ln / 2, -1.12, -0.12 + rnd.uniform(0, 0.08)), (ln, 0.2, 0.12), 0.02, B('concrete'), rot=_ry(rnd.uniform(-0.15, 0.15)))
        x += ln
    # The sunk slab at the narrow point: level, 0.15 under the water, its edges broken.
    cbox(B.bm, ((d0 + d1) / 2, -0.04, dz - 0.07), (d1 - d0 - 0.02, 1.32, 0.14), 0.015, B('concrete'))
    for x in (d0 + 0.02, d1 - 0.02):
        for k in range(4):
            cbox(B.bm, (x, -0.55 + 0.33 * k, dz - 0.03), (0.06, 0.28, 0.08), 0.012, B('concrete'), rot=_rx(rnd.uniform(-0.2, 0.2)))
    # The lane slab's broken ends at the cut, showing their thickness down to the water.
    for x in (d0, d1):
        for k in range(6):
            y = LANE_Y[0] + 0.05 + 0.2 * k
            cbox(B.bm, (x, y + 0.1, -0.16), (0.04, 0.19, 0.28 - 0.05 * (k % 2)), 0.008, B('concrete'), rot=_ry(rnd.uniform(-0.08, 0.08)))
    # Rubble and broken slab in the deep water, the drain grating fallen in.
    for k in range(6):
        c = (rnd.uniform(p0 + 0.3, d0 - 0.2), rnd.uniform(BANK_Y + 0.15, BACK_Y - 0.2), rnd.uniform(-0.75, -0.45))
        cbox(B.bm, c, (rnd.uniform(0.3, 0.5), rnd.uniform(0.2, 0.3), 0.07), 0.01, B('concrete'), rot=_ry(rnd.uniform(-0.5, 0.5)) @ _rx(rnd.uniform(-0.4, 0.4)))
    for k in range(5):
        y = 0.83 + 0.02 * k
        add_cyl(B.bm, (p0 + 0.1, y, -0.05), (p0 + 0.3 + 0.03 * k, y - 0.01, -0.3 - 0.03 * k), 0.006, seg=5, mat=B('steel'))
    B.done('FloodDip', coll)

    # The water: one sheet, facing up (no normal recalculation): along the back, across the cut, into the alley.
    quads = [(p0 + 0.004, BANK_Y + 0.02, p1 - 0.004, BACK_Y), (d0 + 0.004, -1.03, d1 - 0.004, BANK_Y + 0.02),
             (ALLEY[0] + 0.16, BACK_Y, ALLEY[1] - 0.16, 2.4)]
    wo = Vector(((p0 + p1) / 2, 0.3, WATER_Z))
    verts, faces = [], []
    for xa, ya, xb, yb in quads:
        n = len(verts)
        verts += [Vector(v) - wo for v in ((xa, ya, WATER_Z), (xb, ya, WATER_Z), (xb, yb, WATER_Z), (xa, yb, WATER_Z))]
        faces.append((n, n + 1, n + 2, n + 3))
    me = bpy.data.meshes.new('FloodWater')
    me.from_pydata(verts, [], faces)
    me.materials.append(m['water'])
    ob = bpy.data.objects.new('FloodWater', me)
    ob.location = wo
    coll.objects.link(ob)
    # The scum line: a pale crust on every wall where the water has stood (2 cm proud, just over the surface).
    S = Batch(m)
    for xa, xb, y, sy in ((p0, d0, BANK_Y + 0.005, 0), (p0, ALLEY[0], BACK_Y - 0.075, 0), (ALLEY[1], d0 + 0.42, BACK_Y - 0.075, 0),
                          (d1 - 0.42, p1, BACK_Y - 0.075, 0)):
        add_box(S.bm, ((xa + xb) / 2, y, WATER_Z + 0.008), (xb - xa, 0.012, 0.03), mat=S('scum'))
    for x in (p0 + 0.005, d0 + 0.005, d1 - 0.005):
        add_box(S.bm, (x, (BANK_Y + BACK_Y) / 2 if x < d0 - 0.01 else (LANE_Y[0] + BACK_Y) / 2, WATER_Z + 0.008),
                (0.012, BACK_Y - BANK_Y if x < d0 - 0.01 else BACK_Y - LANE_Y[0], 0.03), mat=S('scum'))
    S.done('D5ScumLine', coll)
    _mud_patches('D5Scum', [(p0 + 0.12, 0.85, WATER_Z - 0.0015, 0.1), (p0 + 0.5, 0.42, WATER_Z - 0.0015, 0.07), (85.6 + S9, 0.9, WATER_Z - 0.0015, 0.09),
                            (86.3 + S9, 0.88, WATER_Z - 0.0015, 0.08), (87.45 + S9, -0.85, WATER_Z - 0.0015, 0.09), (86.25 + S9, -0.9, WATER_Z - 0.0015, 0.07),
                            (87.4 + S9, 0.45, WATER_Z - 0.0015, 0.06), (ALLEY[0] + 0.3, 2.2, WATER_Z - 0.0015, 0.1)], m['scum'], coll, 5092)
    # Afloat: a plank, a child's ball, a tin bowl, a shutter slat, two letters gone soft.
    A = Batch(m)
    cbox(A.bm, (85.05 + S9, 0.62, WATER_Z + 0.005), (0.9, 0.12, 0.025), 0.005, A('wood'), rot=_rz(0.25))
    add_sphere(A.bm, (83.95 + S9, 0.5, WATER_Z + 0.03), 0.07, seg=14, mat=A('childpaint'))
    add_cyl(A.bm, (86.55 + S9, -0.62, WATER_Z - 0.01), (86.55 + S9, -0.62, WATER_Z + 0.03), 0.07, 0.09, seg=12, mat=A('steel'))
    cbox(A.bm, (84.5 + S9, 0.9, WATER_Z + 0.003), (0.5, 0.06, 0.012), 0.003, A('depot_green'), rot=_rz(-0.4))
    for x, y, a in ((85.7 + S9, 0.72, 0.6), (87.15 + S9, -0.3, 2.2)):
        add_box(A.bm, (x, y, WATER_Z + 0.001), (0.16, 0.11, 0.002), mat=A('letters'), rot=_rz(a))
    A.done('D5Afloat', coll)
    # Mud dried on the lane each side of the water, kept off the duct's path (|y| < 0.26).
    patches = []
    for k in range(16):
        r = rnd.uniform(0.09, 0.17)
        if k < 6:
            x, y = p0 - 1.7 * r - rnd.uniform(0.0, 0.8), rnd.choice((rnd.uniform(0.3 + 1.7 * r, 0.82), rnd.uniform(-0.72 + 1.7 * r, -0.3 - 1.7 * r)))
        elif k < 10:
            x, y = rnd.uniform(p0 + 0.2, d0 - 0.2), rnd.uniform(-0.72 + 1.7 * r, -0.3 - 1.7 * r)
        else:
            x, y = d1 + 1.7 * r + rnd.uniform(0.0, 0.9), rnd.uniform(-0.72 + 1.7 * r, 0.82)
        patches.append((x, y, 0.0, r))
    _mud_patches('D5Mud', patches, m['mud'], coll, 5091)
    # A drowned shoe: a grown-up's, on its side at the water's edge, half under.
    def upper(c):
        t = (c.x + 1) / 2
        c.z = -1 + (c.z + 1) * (1 - 0.5 * t)
        c.y *= 0.82 + 0.18 * math.sin(math.pi * min(1.0, t * 1.3))
    bm = bmesh.new()
    rounded_box((0.26, 0.092, 0.085), (0, 0, 0.056), p=2.4, cuts=4, mat=0, bm=bm, shape=upper, dents=((0.003, 9.0),), seed=93)
    add_box(bm, (0.005, 0, 0.007), (0.27, 0.09, 0.014), mat=1)
    add_box(bm, (-0.095, 0, 0.019), (0.07, 0.084, 0.022), mat=1)
    add_sphere(bm, (-0.05, 0, 0.099), 0.034, seg=10, scale=(1.7, 1.0, 0.22), mat=2)
    bmesh.ops.transform(bm, matrix=Matrix.Translation((87.05 + S9, 0.4, WATER_Z - 0.005)) @ _rz(0.5) @ _rx(math.radians(78)), verts=bm.verts)
    _obj('D5DrownedShoe', bm, [m['paper'], m['rubber'], m['shaft']], coll, sharp=60)


def build_duct(m, coll):
    """PushDuct: a length of rectangular ventilation duct fallen along the lane, 0.26 high and 0.4 deep, with a
    canvas strap round its left end and a bare steel grip bar on the strap at 0.44 (the push clips' height),
    polished by hands, catching the light (pass 3: no red). Origin at its
    base centre; the game pushes it along x and drops it into the narrow point (top then at about 0.01)."""
    x0, x1, hh, dep = DUCT
    L = x1 - x0 - 0.01
    t = 0.008
    yb, zb0, zb1 = dep - 0.024, 0.006, hh - 0.006
    bm = bmesh.new()                       # mats: 0 sheet, 1 canvas strap, 2 dark inside, 3 steel, 4 polished steel
    zc = (zb0 + zb1) / 2
    for c, sz in (((0, 0, zb1 - t / 2), (L - 0.02, yb, t)), ((0, 0, zb0 + t / 2), (L - 0.02, yb, t)),
                  ((0, -yb / 2 + t / 2, zc), (L - 0.02, t, zb1 - zb0)), ((0, yb / 2 - t / 2, zc), (L - 0.02, t, zb1 - zb0))):
        add_box(bm, c, sz)
    for fx in (-L / 2 + 0.015, 0.0, L / 2 - 0.015):
        add_box(bm, (fx, 0, hh - 0.01), (0.03, dep, 0.02))
        add_box(bm, (fx, 0, 0.01), (0.03, dep, 0.02))
        for sy in (-1, 1):
            add_box(bm, (fx, sy * (dep / 2 - 0.01), hh / 2), (0.03, 0.02, hh - 0.04))
    span, hz = L / 2 - 0.03, zb1 - zb0
    diag = math.hypot(span, hz)
    for cxp in (-span / 2 - 0.0075, span / 2 + 0.0075):
        for sgn in (-1, 1):
            for sy in (-1, 1):
                add_box(bm, (cxp, sy * (yb / 2 + 0.001), zc), (diag - 0.02, 0.002, 0.006), rot=_ry(sgn * math.atan2(hz, span)))
    for fx in (-L / 2 + 0.16, L / 2 - 0.16):
        add_box(bm, (fx, 0, zc), (0.004, yb - 2 * t, zb1 - zb0 - 2 * t), mat=2)
    sxp, sw = -L / 2 + 0.12, 0.045
    add_box(bm, (sxp, 0, hh + 0.002), (sw, dep + 0.008, 0.004), mat=1)
    add_box(bm, (sxp, 0, 0.002), (sw, dep + 0.008, 0.004), mat=1)
    for sy in (-1, 1):
        add_box(bm, (sxp, sy * (dep / 2 + 0.002), hh / 2), (sw, 0.004, hh), mat=1)
    add_box(bm, (sxp, -dep / 2 - 0.014, hh * 0.55), (0.06, 0.022, 0.05), mat=3)
    add_cyl(bm, (sxp - 0.03, -dep / 2 - 0.026, hh * 0.55 + 0.012), (sxp + 0.03, -dep / 2 - 0.026, hh * 0.55 + 0.012), 0.006, seg=6, mat=3)
    gx, gz = DUCT_GRIP
    for sy in (-1, 1):
        p0, p1 = Vector((sxp, sy * 0.115, hh + 0.004)), Vector((gx, sy * 0.115, gz))
        dv = p1 - p0
        add_box(bm, (p0 + p1) / 2, (dv.length + 0.02, 0.04, 0.004), mat=1, rot=_ry(math.atan2(-dv.z, dv.x)))
    add_cyl(bm, (gx, -0.135, gz), (gx, 0.135, gz), 0.017, seg=12, mat=4)
    for sy in (-1, 1):                                                          # the bar's steel eyes in the strap
        add_cyl(bm, (gx, sy * 0.125, gz), (gx, sy * 0.105, gz), 0.024, seg=10, mat=3)
    origin = Vector(((x0 + x1) / 2, 0.0, 0.0))
    bmesh.ops.translate(bm, vec=origin, verts=bm.verts)
    _obj_at('PushDuct', bm, [m['plate'], m['paper'], m['shaft'], m['steel'], m['pawlsteel']], coll, origin)


def build_mailslot(m, coll):
    """MailSlot9: ring C's post box in the square by C-114, a depot-green post with a brass-rimmed slot at 0.55
    facing the lane (worn bright by letters), a hood over it and a stamp lamp (SlotLamp9) above. Origin at the
    post's foot."""
    x, y, sz = MAILSLOT9
    hw, top = 0.1, 0.84
    fy = -hw
    bm = bmesh.new()                       # mats: 0 green, 1 brass, 2 dark, 3 steel
    add_box(bm, (0, 0, 0.03), (0.28, 0.28, 0.06))
    add_box(bm, (0, 0, top / 2), (2 * hw, 2 * hw, top))
    add_box(bm, (0, 0, top + 0.02), (0.26, 0.26, 0.04))
    add_sphere(bm, (0, 0, top + 0.04), 0.13, seg=14, scale=(1, 1, 0.42), mat=0)
    add_box(bm, (0, fy - 0.004, sz), (0.15, 0.01, 0.022), mat=2)
    for dz_, w_, h_ in ((0.021, 0.19, 0.016), (-0.021, 0.19, 0.016)):
        add_box(bm, (0, fy - 0.007, sz + dz_), (w_, 0.014, h_), mat=1)
    for dx_ in (-0.087, 0.087):
        add_box(bm, (dx_, fy - 0.007, sz), (0.016, 0.014, 0.058), mat=1)
    add_box(bm, (0, fy - 0.025, sz + 0.05), (0.21, 0.05, 0.012), mat=3, rot=_rx(math.radians(-14)))
    add_cyl(bm, (0, fy, sz + 0.13), (0, fy - 0.012, sz + 0.13), 0.026, seg=14, mat=3)
    for z in (0.12, top - 0.08):
        add_box(bm, (0, 0, z), (2 * hw + 0.008, 2 * hw + 0.008, 0.02), mat=3)
    bmesh.ops.translate(bm, vec=(x, y, 0.0), verts=bm.verts)
    _obj_at('MailSlot9', bm, [m['depot_green'], m['brass'], m['shaft'], m['steel']], coll, (x, y, 0.0), sharp=40)
    bm = bmesh.new()
    add_sphere(bm, (x, y + fy - 0.013, sz + 0.13), 0.018, seg=12, scale=(1, 0.6, 1))
    _obj_at('SlotLamp9', bm, [m['slotlamp9']], coll, (x, y + fy - 0.013, sz + 0.13))


# The DL-08 balcony's views out over the city look the same way as ring C's background (+y), across the same chasm:
# whatever stands behind ring C must stay out of them. The vista crane (from his shoulder at the balcony up and back,
# 32 to 24 mm, wherever along the balcony he stands) and the balcony's side-on framing, in dl05 coordinates.
VISTA_DX = -12.0     # pass 3: the balcony stayed (game OFF4 + 70) while ring C moved 12 m further right (OFF5 = OFF4 + 12)


def _vista_cams():
    cams = []
    for X in (71.3 + VISTA_DX, 72.9 + VISTA_DX, 74.55 + VISTA_DX):
        for k in (0.0, 0.25, 0.5, 0.75, 1.0):
            pos = Vector((X + 0.45, -1.35, 1.6 + 0.95)).lerp(Vector((X + 3.2, -8.5, 1.6 + 7.9)), k)
            look = Vector((95.0, 160.0, 12.0)).lerp(Vector((92.0, 150.0, 22.0)), k)
            cams.append((pos, look, 32 - 8 * k))
    for x in (71.2 + VISTA_DX, 72.6 + VISTA_DX, 74.0 + VISTA_DX):
        cams.append((Vector((x, -7.6, 3.0)), Vector((x, 0.0, 1.7)), 35.0))
    return cams


VISTA_CAMS = []


def in_vista(points, margin=1.08):
    """True if any point falls inside any balcony view (16:9 or narrower: a tall phone sees more above and below)."""
    if not VISTA_CAMS:
        VISTA_CAMS.extend(_vista_cams())
    for pos, look, lens in VISTA_CAMS:
        f = (look - pos).normalized()
        r = f.cross(Vector((0, 0, 1))).normalized()
        u = r.cross(f)
        hw = 17.5 / lens * margin
        hh = hw / (16 / 9) * 1.35
        for p in points:
            v = Vector(p) - pos
            d = v.dot(f)
            if d > 0.1 and abs(v.dot(r) / d) < hw and abs(v.dot(u) / d) < hh:
                return True
    return False


def build_far(m, coll):
    """The background, flat and plain (cheap, unshadowed, read through the haze): the slope behind the back row up
    to ring B's terrace and its tier of homes, a few windows still lit up there; stairs between the tiers (the alley's
    and the square's, going on up); the lift's lattice tower going up into the dark, its cage lamp lit; the cavern.
    Built piece by piece, and any piece the DL-08 balcony's views would see is left out (in_vista)."""
    rnd = random.Random(5300)
    B = Batch(m)
    bm = B.bm
    dropped = [0, 0]

    def piece(build):
        bm.verts.ensure_lookup_table()
        n0 = len(bm.verts)
        build()
        bm.verts.ensure_lookup_table()
        new = bm.verts[n0:]
        if not new:
            return
        xs, ys, zs = zip(*[v.co[:] for v in new])
        box = [(x, y, z) for x in (min(xs), max(xs)) for y in (min(ys), max(ys)) for z in (min(zs), max(zs))]
        box.append((sum(xs) / len(xs), sum(ys) / len(ys), sum(zs) / len(zs)))
        if in_vista(box):
            bmesh.ops.delete(bm, geom=list(new), context='VERTS')
            dropped[0] += 1
        else:
            dropped[1] += 1
    x0, x1, step = 79.5, 112.5 + S9, 2.2
    chunks = [(x0 + step * i, min(x1, x0 + step * (i + 1))) for i in range(int(math.ceil((x1 - x0) / step)))]
    for ca, cb in chunks:
        # The slope from behind the back row (y 3.4) up to ring B's terrace edge (y 7.0, z 4.3); the terrace's parapet and walk.
        piece(lambda ca=ca, cb=cb: _rock_sheet(bm, (ca, 3.5, 0.0), (cb - ca, 0, 0), (0, 3.6, 4.4), 3, 5, 0.25, 51.0, freq=0.9, thick=0.3,
                                                mat=B('stone')))
        piece(lambda ca=ca, cb=cb: cbox(bm, ((ca + cb) / 2, 7.1, 4.5), (cb - ca, 0.25, 0.45), 0.03, B('masonry')))
        piece(lambda ca=ca, cb=cb: add_box(bm, ((ca + cb) / 2, 8.2, 4.2), (cb - ca, 2.2, 0.2), mat=B('masonry')))
        piece(lambda ca=ca, cb=cb: _rock_sheet(bm, (ca, 11.5, 4.4), (cb - ca, 0, 0), (0, 2.4, 5.2), 2, 3, 0.35, 61.0, freq=0.6, thick=0.4,
                                                mat=B('stone')))
    # Ring B's homes along its terrace.
    x, lit = x0, [0]
    while x < x1:
        w = rnd.uniform(2.1, 3.0)
        h = rnd.uniform(2.6, 3.4)
        wins = [rnd.random() < 0.18 for _ in range(int((w - 1.2) / 0.9))]

        def home(x=x, w=w, h=h, wins=wins):
            yb = 9.2
            add_box(bm, (x + w / 2, yb + 1.0, 4.3 + h / 2), (w - 0.12, 2.0, h), mat=B('plaster'))
            add_box(bm, (x + w / 2, yb + 1.0, 4.3 + h + 0.25), (w + 0.1, 2.2, 0.1), mat=B('dark'))
            prism(bm, [(yb - 0.15, 4.3 + h + 0.3), (yb + 1.0, 4.3 + h + 0.95), (yb + 2.15, 4.3 + h + 0.3)], 'x', x + 0.02, x + w - 0.02, mat=B('cut'))
            add_box(bm, (x + 0.55, yb - 0.01, 4.3 + 0.95), (0.7, 0.02, 1.9), mat=B('dark'))
            for k, on in enumerate(wins):
                wx = x + 1.3 + 0.9 * k
                on = on and lit[0] < 9
                lit[0] += on
                add_box(bm, (wx, yb - 0.012, 4.3 + 1.55), (0.55, 0.02, 0.7), mat=B('windowglow' if on else 'dark'))
                add_box(bm, (wx, yb - 0.03, 4.3 + 1.17), (0.65, 0.06, 0.05), mat=B('masonry'))
        piece(home)
        x += w
    # Stairs between the tiers: the alley's and the cross alley's go on up the slope; the square's turns back across it.
    for a_, b_ in (ALLEY, CROSS):
        for k in range(9):
            piece(lambda k=k, a_=a_, b_=b_: cbox(bm, ((a_ + b_) / 2, 4.75 + 0.26 * k + (1.2 if a_ == CROSS[0] else 0.0),
                                                      2.6 + 0.19 * k - 0.2 + (0.25 if a_ == CROSS[0] else 0.0)), (0.62, 0.28, 0.4), 0.01, B('cut')))
    for k in range(10):
        piece(lambda k=k: cbox(bm, (94.0 + S9 - 0.24 * k, 4.4, 3.05 + 0.13 * k - 0.15), (0.26, 0.6, 0.3), 0.01, B('cut')))
    piece(lambda: _wire(bm, [Vector((94.0 + S9, 4.12, 3.9)), Vector((91.6 + S9, 4.12, 5.2))], 0.016, B('rust')))
    # The lift: a lattice tower behind C-114, going up out of sight; its cage up at ring B, its lamp lit.
    lx, ly, s = 98.8 + S9, 8.6, 1.1
    z = -1.5
    while z < 14:
        def bay(z=z):
            for dx in (-s / 2, s / 2):
                for dy in (-s / 2, s / 2):
                    add_box(bm, (lx + dx, ly + dy, z + 0.55), (0.08, 0.08, 1.1), mat=B('rust'))
            for (a_, b_) in (((-1, -1), (1, -1)), ((1, -1), (1, 1)), ((1, 1), (-1, 1)), ((-1, 1), (-1, -1))):
                p_, q_ = Vector((lx + a_[0] * s / 2, ly + a_[1] * s / 2, z)), Vector((lx + b_[0] * s / 2, ly + b_[1] * s / 2, z + 1.1))
                add_cyl(bm, p_, q_, 0.02, seg=4, mat=B('rust'))
                add_cyl(bm, p_, Vector((q_.x, q_.y, z)), 0.025, seg=4, mat=B('rust'))
        piece(bay)
        z += 1.1

    def cage():
        cz = 6.4
        add_box(bm, (lx, ly, cz), (0.9, 0.9, 1.9), mat=B('sheet'))
        add_box(bm, (lx, ly - 0.46, cz + 0.2), (0.6, 0.02, 0.9), mat=B('windowglow'))
        add_box(bm, (lx, ly - 0.47, cz + 1.05), (0.12, 0.04, 0.08), mat=B('windowglow'))
        for dx in (-0.15, 0.15):
            add_cyl(bm, (lx + dx, ly, cz + 0.95), (lx + dx, ly, 14.0), 0.012, seg=4, mat=B('dark'))
    piece(cage)
    # Cables sagging across the void from ring B's parapet down to the back row's roofs.
    for xa, xb in ((81.6, 82.8), (84.4, 85.6), (88.2, 89.4), (82.0 + S9, 83.4 + S9), (86.2 + S9, 87.0 + S9), (89.2 + S9, 90.6 + S9), (95.5 + S9, 97.0 + S9)):
        piece(lambda xa=xa, xb=xb: _wire(bm, _catenary((xa, 7.0, 4.75), (xb, 2.4, 3.6), 0.5, 8), 0.012, B('dark')))
    print(f'D5FarTiers: {dropped[1]} pieces kept, {dropped[0]} left out of the balcony views')
    B.done('D5FarTiers', coll)


def _imgmat(name, file, rough=0.7, alpha=False):
    return bpy.data.materials.get(name) or _image_material(name, _tex(file), rough=rough, alpha=alpha)


def _quads(name, mat, quads, coll):
    """Decals sharing one texture as one object (one draw call): quads of (centre, (w, h), facing, uv rect).
    facing: '-y' (to the camera), '-x' (to the street, an end wall), '+z' (on the ground, top toward +y)."""
    verts, faces, uvs = [], [], []
    for c, (w, h), facing, (u0, v0, u1, v1) in quads:
        c = Vector(c)
        if facing == '-y':
            ax, ay = Vector((1, 0, 0)), Vector((0, 0, 1))
        elif facing == '-x':
            ax, ay = Vector((0, -1, 0)), Vector((0, 0, 1))
        else:
            ax, ay = Vector((1, 0, 0)), Vector((0, 1, 0))
        n = len(verts)
        for sx, sy, uv in ((-1, -1, (u0, v0)), (1, -1, (u1, v0)), (1, 1, (u1, v1)), (-1, 1, (u0, v1))):
            verts.append(c + ax * (sx * w / 2) + ay * (sy * h / 2))
            uvs.append(uv)
        faces.append((n, n + 1, n + 2, n + 3))
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    layer = me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        for li in poly.loop_indices:
            layer.data[li].uv = uvs[me.loops[li].vertex_index]
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


DOOR_LEAF_Y = BACK_Y + 0.13 - 0.0225 - 0.012      # in front of a back-row door's outer mouldings


def build_lore3(m, coll):
    """What says, without a word of explanation, where this is and what happened: the grade stencilled on every door,
    the chalk on the doors of the families that went up, the two slogans, the ration queue's sign and its marks, the
    standpipe's plate, the new homes' numbers."""
    full = (0, 0, 1, 1)
    Y = BACK_Y
    a6 = NEW_HOMES[2][1]
    side_x = CROSS[1] - 0.17 - 0.04                     # C-106's door, on the alley wall, facing the street (-x)
    g4 = _imgmat('D5Grade4Mat', 'grade4.png', rough=0.8, alpha=True)
    q = [((x, DOOR_LEAF_Y, z), (0.15, 0.15), '-y', full) for x, z in ((82.95, 1.38), (84.45, 1.38), (C108_DOOR, 1.42), (C110_DOOR, 1.5),
                                                                       (C112_DOOR, 1.62))]
    q.append(((85.75, Y + 0.068, 1.36), (0.14, 0.14), '-y', full))
    q.append(((side_x, 1.72, 1.38), (0.14, 0.14), '-x', full))
    _quads('D5Grade4', g4, q, coll)
    gu = _imgmat('D5GoneUpMat', 'goneup.png', rough=0.9, alpha=True)
    third = lambda k: (k / 3, 0, (k + 1) / 3, 1)      # noqa: E731
    _quads('D5GoneUp', gu, [((82.95, DOOR_LEAF_Y - 0.001, 1.0), (0.42, 0.14), '-y', third(0)),
                             ((85.75, Y + 0.067, 1.02), (0.4, 0.133), '-y', third(1)),
                             ((C110_DOOR, DOOR_LEAF_Y - 0.001, 1.25), (0.42, 0.14), '-y', third(2)),
                             ((side_x - 0.001, 1.72, 1.0), (0.4, 0.133), '-x', third(0))], coll)
    gr = _imgmat('D5GraffitiMat', 'graffiti.png', rough=0.85, alpha=True)
    gx0, gx1 = a6 + 0.17, C106_WIN - 0.47                # C-106's blank face, between the pilaster and the window
    gw = gx1 - gx0
    _quads('D5Graffiti', gr, [(((gx0 + gx1) / 2, Y - 0.004, 1.42), (gw, gw / 4), '-y', (0, 0.5, 1, 1)),
                               (((gx0 + gx1) / 2 - 0.04, Y - 0.006, 0.78), (gw + 0.08, (gw + 0.08) / 4), '-y', (0, 0, 1, 0.5))], coll)
    qx, qy = QUEUE_POST
    _plane('D5RationSign', (0.34, 0.283), (qx, qy + 0.004, 1.38), _imgmat('D5RationSignMat', 'ration_sign.png', rough=0.5), coll)
    _quads('D5QueueMarks', _imgmat('D5QueueMarksMat', 'queue_marks.png', rough=0.9, alpha=True),
           [((qx - 1.18, qy - 0.04, 0.003), (2.2, 0.24), '+z', full)], coll)
    tx, ty = TAP
    _plane('D5TapSign', (0.14, 0.096), (tx + 0.18, ty + 0.2 - 0.043, 1.16), _imgmat('D5TapSignMat', 'tap_sign.png', rough=0.4), coll)
    for num, x, y, z, facing in (('102', 82.95, DOOR_LEAF_Y, 1.62, '-y'), ('104', 84.45, DOOR_LEAF_Y, 1.62, '-y'),
                                 ('106', side_x, 1.72, 1.62, '-x')):
        _quads(f'D5Plate{num}', _imgmat(f'D5Plate{num}Mat', f'plate_c{num}.png', rough=0.3), [((x, y, z), (0.2, 0.0875), facing, full)], coll)
    _quads('D5Plate104A', _imgmat('D5Plate104AMat', 'plate_c104a.png', rough=0.8, alpha=True),
           [((85.75, Y + 0.067, 1.62), (0.3, 0.13), '-y', full)], coll)


def build_front_door114(m, coll):
    """C-114's front door, SHUT (docs/chapter1_pass3_plan.md section 1). C114FrontDoor: its origin on the hinge (the
    back jamb, at the leaf's inner face, on the floor); it swings in about +Z by DOOR_OPEN degrees, the free edge
    (toward the camera) going first, and stands open along the hall with its outer face to the camera. Its outer face:
    the panels, the letter plate, the knocker, the name card, the grade's 4; brass hinges. Children of it:
    C114DoorHandle, the lever (Brass, its grip worn bright), its origin on the spindle at the door's face, turning about
    its own x (tip down, about -35 degrees, to open); C114DoorCord, a loop of parcel twine from the lever's tip down to a
    wooden toggle at the child's height (CORD_TOGGLE), its origin at the tie (the lever's tip): the game keeps it
    hanging from the tip as the lever turns."""
    hx, hy = DOOR_HINGE
    w, h = 2 * DOOR_HALF - 0.01, DOOR_H - 0.01
    D = Batch(m)
    closed = _rz(math.radians(-90)) @ Matrix.Translation((0, -DOOR_T / 2 - 0.0025, 0))    # door_leaf's frame -> shut, hinge at the origin
    door_leaf(D, closed, w, h, DOOR_T, D('childpaint'), D('brass'), slot_z=0.86, both=True, knocker=True, knobs=False)
    for z in (0.3, 1.65):                                                     # the hinges' knuckles, at the inner face
        add_cyl(D.bm, (0.0, -0.004, z - 0.06), (0.0, -0.004, z + 0.06), 0.012, seg=8, mat=D('brass'))
    for zc in (HANDLE[2],):                                                   # the lock's escutcheon, and its plate inside
        cbox(D.bm, (DOOR_FACE - hx - 0.004, HANDLE[1] - hy, zc - 0.11), (0.008, 0.036, 0.07), 0.002, D('brass'))
        cbox(D.bm, (0.0005, HANDLE[1] - hy, zc - 0.03), (0.006, 0.05, 0.22), 0.002, D('brass'))
    door = D.done('C114FrontDoor', coll)
    door.location = (hx, hy, 0.0)
    bpy.context.view_layer.update()
    # The handle: a rose on the face, the spindle through, a lever each side pointing back toward the hinge.
    sx_, sy_, sz_ = HANDLE
    o = Vector((DOOR_FACE, sy_, sz_))
    bm = bmesh.new()                                                          # mats: 0 brass
    for side, x_face, x_lever in ((-1, 0.0, sx_ - DOOR_FACE), (1, DOOR_T, DOOR_T + 0.05)):
        add_cyl(bm, (x_face, 0, 0), (x_face + side * 0.008, 0, 0), 0.03, seg=16)
        add_cyl(bm, (x_face, 0, 0), (x_lever, 0, 0), 0.009, seg=8)
        add_cyl(bm, (x_lever, -0.012, 0), (x_lever, HANDLE_LEN - 0.012, -0.006), 0.011, seg=10)
        add_sphere(bm, (x_lever, HANDLE_LEN - 0.012, -0.006), 0.016, seg=10, scale=(1, 1.3, 0.9))
    bmesh.ops.translate(bm, vec=o, verts=bm.verts)
    handle = _obj_at('C114DoorHandle', bm, [m['brass']], coll, o)
    # The cord: two strands from a knot at the lever's tip down to the toggle, the toggle worn smooth.
    tie = Vector((sx_, sy_ + HANDLE_LEN - 0.012, sz_ - 0.02))
    bm = bmesh.new()                                                          # mats: 0 twine, 1 toggle
    add_sphere(bm, tie, 0.013, seg=8, mat=0)
    top_t = CORD_TOGGLE + 0.035
    for dy in (-0.012, 0.012):
        _wire(bm, [tie, tie + Vector((0.004, dy * 0.6, -0.12)), Vector((tie.x + 0.006, tie.y + dy, top_t))], 0.0032, 0, seg=4)
    add_cyl(bm, (tie.x + 0.006, tie.y - 0.035, CORD_TOGGLE), (tie.x + 0.006, tie.y + 0.035, CORD_TOGGLE), 0.012, seg=10, mat=1)
    for dy in (-0.035, 0.035):
        add_sphere(bm, (tie.x + 0.006, tie.y + dy, CORD_TOGGLE), 0.0125, seg=8, scale=(1, 0.5, 1), mat=1)
    cord = _obj_at('C114DoorCord', bm, [m['paper'], m['pigeon']], coll, tie)
    # Its card and the grade's 4, on the outer face.
    card = _plane('D5NameCard114', (0.16, 0.1), (DOOR_FACE - 0.0125, 0.0, 1.16), _imgmat('D5NameCardMat', 'namecard114.png', rough=0.8), coll,
                  rot=_rz(math.radians(-90)) @ _rx(math.radians(90)))
    four = _plane('D5Grade4Door114', (0.13, 0.13), (DOOR_FACE - 0.0125, 0.0, 1.62), _imgmat('D5Grade4Mat', 'grade4.png', rough=0.8, alpha=True), coll,
                  rot=_rz(math.radians(-90)) @ _rx(math.radians(90)))
    bpy.context.view_layer.update()
    for ob in (handle, cord, card, four):
        ob.parent = door
        ob.matrix_parent_inverse = door.matrix_world.inverted()
    return door


# --- C-114 ----------------------------------------------------------------------

X0_114 = FRONT114 - 0.09                  # the front wall's outer face
XM_114 = INNER[0] + 0.06                  # the main block's end (the bedroom wing runs on from here)
X1_114 = BACK_DOOR[0] + 0.06              # the back wall's outer face
RIDGE = ((X0_114 + XM_114) / 2, 6.6)      # the main block's roof ridge (it runs back from the gable on the street)
EAVE = 4.93
WING = (-0.95, 2.72, 0.2, 3.45, 1.35)     # the wing's roof: front eave y, eave z, ridge y, ridge z, back eave y
ROOF_T = 0.15


def _wing_z(y):
    ye, ze, yr, zr, yb = WING
    return ze + (zr - ze) * (y - ye) / (yr - ye) if y <= yr else zr - (zr - ze) * (y - yr) / (yb - yr)


def build_home114(m, coll):
    """C-114, the house at the end of the street, as a dollhouse section on the play line. A front step under a
    little canopy, the front door in the end wall (shut: build_front_door114); the hall; the kitchen and living room; the
    child's bedroom in the wing at the end; the back door. Two storeys and a gable over the hall and living room, a
    lower roof over the bedroom. The street wall (C114Facade) is a separate object the game fades out when he steps
    in; behind it every cut wall, floor, ceiling and roof is capped in near-black (C114Section)."""
    rnd = random.Random(5114)
    IN, EX, FA, CAP = Batch(m), Batch(m), Batch(m), Batch(m)
    X0, XM, X1, Y = X0_114, XM_114, X1_114, BACK_Y
    door = [(-DOOR_HALF, DOOR_HALF, 0.0, DOOR_H)]
    # ---- the shell ------------------------------------------------------------------------------------
    add_box(IN.bm, ((X0 + X1) / 2, (CUT_Y + Y + 0.12) / 2, -0.15), (X1 - X0, Y + 0.12 - CUT_Y, 0.3), mat=IN('pigeon'))
    for k in range(int((Y - CUT_Y) / 0.13)):                                   # floorboards
        add_box(IN.bm, ((X0 + X1) / 2, CUT_Y + 0.13 * (k + 1), -0.002), (X1 - X0, 0.008, 0.006), mat=IN('wood'))
    wall_y(IN.bm, CUT_Y, Y + 0.12, X0, X0 + 0.18, 0.0, UPPER[1] + 0.08, door, IN('homeplaster'))       # the front wall
    wall_y(IN.bm, CUT_Y, Y, P1 - 0.06, P1, 0.0, HOME_CEIL, door, IN('homeplaster'))
    wall_y(IN.bm, CUT_Y, Y, P1, P1 + 0.06, 0.0, HOME_CEIL, door, IN('living'))
    xi = INNER[0]
    wall_y(IN.bm, CUT_Y, Y, xi - 0.06, xi, 0.0, HOME_CEIL, door, IN('living'))
    wall_y(IN.bm, CUT_Y, Y, xi, xi + 0.06, 0.0, 0.75, door, IN('dado'))
    wall_y(IN.bm, CUT_Y, Y, xi, xi + 0.06, 0.75, HOME_CEIL, door, IN('bedroom'))
    wall_y(IN.bm, CUT_Y, Y + 0.12, xi - 0.06, xi + 0.06, HOME_CEIL + 0.22, UPPER[1] + 0.08, (), IN('homeplaster'))
    xb = BACK_DOOR[0]
    wall_y(IN.bm, CUT_Y, Y, xb - 0.06, xb, 0.0, 0.75, door, IN('dado'))
    wall_y(IN.bm, CUT_Y, Y, xb - 0.06, xb, 0.75, HOME_CEIL, door, IN('bedroom'))
    wall_y(IN.bm, CUT_Y, Y + 0.12, xb, xb + 0.06, 0.0, HOME_CEIL + 0.22, door, IN('homeplaster'))
    prism(IN.bm, [(CUT_Y, HOME_CEIL + 0.22), (CUT_Y, _wing_z(CUT_Y) - 0.12), (WING[2], WING[3] - 0.14), (Y + 0.12, _wing_z(Y + 0.12) - 0.12),
                  (Y + 0.12, HOME_CEIL + 0.22)], 'x', xb - 0.06, xb + 0.06, mat=IN('homeplaster'))
    # The back walls: the hall's, the living room's with the window over the sink, the bedroom's (dado, paint,
    # the terminal's screen recess), the upper floor's, the gable under the ridge.
    wall_x(IN.bm, X0 + 0.18, P1 - 0.06, Y, Y + 0.12, 0.0, HOME_CEIL, (), IN('homeplaster'))
    KW = (97.8 + S9, 98.5 + S9, 1.05, 1.75)
    wall_x(IN.bm, P1 + 0.06, xi - 0.06, Y, Y + 0.12, 0.0, HOME_CEIL, [KW], IN('living'))
    sx0, sx1 = TERM_X - SCREEN[0] / 2, TERM_X + SCREEN[0] / 2
    sz0, sz1 = SCREEN_Z - SCREEN[1] / 2, SCREEN_Z + SCREEN[1] / 2
    wall_x(IN.bm, xi + 0.06, xb - 0.06, Y, Y + 0.12, 0.0, 0.75, (), IN('dado'))
    wall_x(IN.bm, xi + 0.06, xb - 0.06, Y, Y + 0.12, 0.75, HOME_CEIL, [(sx0, sx1, sz0, sz1)], IN('bedroom'))
    wall_x(IN.bm, X0 + 0.18, xi - 0.06, Y, Y + 0.12, UPPER[0], UPPER[1], (), IN('homeplaster'))
    prism(IN.bm, [(X0, UPPER[1]), (RIDGE[0], RIDGE[1] - ROOF_T - 0.02), (XM, UPPER[1])], 'y', Y, Y + 0.12, mat=IN('homeplaster'))
    # Ceilings and the upper floor: the slab at 2.4 under its boards, the upper rooms, their ceiling, a partition.
    add_box(IN.bm, ((X0 + X1) / 2, (CUT_Y + Y + 0.12) / 2, HOME_CEIL + 0.1), (X1 - X0, Y + 0.12 - CUT_Y, 0.2), mat=IN('homeplaster'))
    add_box(IN.bm, ((X0 + XM) / 2, (CUT_Y + Y + 0.12) / 2, UPPER[0] - 0.01), (XM - X0, Y + 0.12 - CUT_Y, 0.02), mat=IN('pigeon'))
    add_box(IN.bm, ((XM + X1) / 2, (CUT_Y + Y + 0.12) / 2, UPPER[0] - 0.01), (X1 - XM, Y + 0.12 - CUT_Y, 0.02), mat=IN('homeplaster'))
    add_box(IN.bm, ((X0 + XM) / 2, (CUT_Y + Y + 0.12) / 2, UPPER[1] + 0.075), (XM - X0, Y + 0.12 - CUT_Y, 0.15), mat=IN('homeplaster'))
    wall_y(IN.bm, CUT_Y, Y, 97.54 + S9, 97.66 + S9, UPPER[0], UPPER[1], [(-0.36, 0.36, UPPER[0], UPPER[0] + 1.95)], IN('homeplaster'))
    # Skirting, a dado rail in the bedroom, coving, the door linings (the back jamb faces the camera) and thresholds.
    for a, b in ((X0 + 0.18, P1 - 0.06), (P1 + 0.06, xi - 0.06), (xi + 0.06, xb - 0.06)):
        cbox(IN.bm, ((a + b) / 2, Y - 0.009, 0.05), (b - a, 0.018, 0.1), 0.004, IN('wood'))
        cbox(IN.bm, ((a + b) / 2, Y - 0.012, HOME_CEIL - 0.04), (b - a, 0.024, 0.08), 0.006, IN('homeplaster'))
    for a, b in ((X0 + 0.18, P1 - 0.06), (P1 + 0.06, 97.54 + S9), (97.66 + S9, xi - 0.06)):
        cbox(IN.bm, ((a + b) / 2, Y - 0.009, UPPER[0] + 0.05), (b - a, 0.018, 0.1), 0.004, IN('wood'))
    cbox(IN.bm, ((xi + xb) / 2, Y - 0.01, 0.76), (xb - xi - 0.12, 0.02, 0.03), 0.005, IN('wood'))
    for xw, t in ((X0 + 0.09, 0.18), (P1, 0.12), (xi, 0.12), (xb, 0.12)):
        cbox(IN.bm, (xw, DOOR_HALF - 0.01, DOOR_H / 2), (t + 0.02, 0.02, DOOR_H), 0.004, IN('childpaint'))     # back jamb lining
        cbox(IN.bm, (xw, 0.0, DOOR_H - 0.01), (t + 0.02, 2 * DOOR_HALF, 0.02), 0.004, IN('childpaint'))          # head lining
        cbox(IN.bm, (xw, -DOOR_HALF + 0.01, DOOR_H / 2), (t + 0.02, 0.02, DOOR_H), 0.004, IN('childpaint'))
        cbox(IN.bm, (xw, 0.0, 0.01), (t + 0.04, 2 * DOOR_HALF, 0.02), 0.004, IN('wood'))                        # threshold, 2 cm
        for side in (-1, 1):                                                   # architraves on both faces
            if xw == X0 + 0.09 and side < 0:
                continue
            fx = xw + side * (t / 2 + 0.01)
            cbox(IN.bm, (fx, DOOR_HALF + 0.04, DOOR_H / 2 + 0.03), (0.02, 0.08, DOOR_H + 0.06), 0.004, IN('childpaint'))
            cbox(IN.bm, (fx, 0.0, DOOR_H + 0.05), (0.02, 2 * DOOR_HALF + 0.16, 0.08), 0.004, IN('childpaint'))
            cbox(IN.bm, (fx, -DOOR_HALF - 0.04, DOOR_H / 2 + 0.03), (0.02, 0.08, DOOR_H + 0.06), 0.004, IN('childpaint'))
    # ---- the roof (behind the cut) and the outside of the house ------------------------------------------------
    t = ROOF_T
    left = [(X0 - 0.26, EAVE), (RIDGE[0], RIDGE[1]), (RIDGE[0], RIDGE[1] - t), (X0 - 0.26, EAVE - t)]
    right = [(RIDGE[0], RIDGE[1]), (XM + 0.26, EAVE), (XM + 0.26, EAVE - t), (RIDGE[0], RIDGE[1] - t)]
    for poly in (left, right):
        prism(EX.bm, poly, 'y', CUT_Y, Y + 0.35, mat=EX('slate'))
        prism(CAP.bm, poly, 'y', CUT_Y - 0.006, CUT_Y, mat=CAP('sectioncap'))
        prism(FA.bm, poly, 'y', -0.95, CUT_Y, mat=FA('slate'))
    add_cyl(EX.bm, (RIDGE[0], CUT_Y, RIDGE[1] + 0.02), (RIDGE[0], Y + 0.35, RIDGE[1] + 0.02), 0.07, seg=10, mat=EX('slate'))
    add_cyl(FA.bm, (RIDGE[0], -0.97, RIDGE[1] + 0.02), (RIDGE[0], CUT_Y, RIDGE[1] + 0.02), 0.07, seg=10, mat=FA('slate'))
    for x in (X0 - 0.3, XM + 0.3):
        add_cyl(EX.bm, (x, CUT_Y, EAVE - 0.06), (x, Y + 0.35, EAVE - 0.06), 0.05, seg=8, mat=EX('iron'))
        add_cyl(FA.bm, (x, -0.97, EAVE - 0.06), (x, CUT_Y, EAVE - 0.06), 0.05, seg=8, mat=FA('iron'))
    cbox(EX.bm, (99.6 + S9, 0.75, 6.0), (0.46, 0.42, 1.7), 0.02, EX('plasterB'))       # the chimney stack, its pots
    cbox(EX.bm, (99.6 + S9, 0.75, 6.88), (0.56, 0.52, 0.08), 0.015, EX('concrete'))
    for dx in (-0.1, 0.1):
        add_cyl(EX.bm, (99.6 + S9 + dx, 0.75, 6.9), (99.6 + S9 + dx, 0.75, 7.15), 0.07, 0.055, seg=10, mat=EX('paper'))
    wing_back = [(WING[2], WING[3]), (WING[4], WING[1]), (WING[4], WING[1] - t), (WING[2], WING[3] - t)]
    wing_front = [(WING[0], WING[1]), (WING[2], WING[3]), (WING[2], WING[3] - t), (WING[0], WING[1] - t)]
    prism(EX.bm, wing_back, 'x', XM - 0.02, X1 + 0.14, mat=EX('slate'))
    prism(FA.bm, wing_front, 'x', XM - 0.02, X1 + 0.14, mat=FA('slate'))
    add_cyl(EX.bm, (XM, WING[2], WING[3] + 0.02), (X1 + 0.14, WING[2], WING[3] + 0.02), 0.06, seg=10, mat=EX('slate'))
    add_cyl(FA.bm, (XM, WING[0] - 0.03, WING[1] - 0.04), (X1 + 0.14, WING[0] - 0.03, WING[1] - 0.04), 0.05, seg=8, mat=FA('iron'))
    cbox(FA.bm, ((XM + X1) / 2 + 0.07, WING[0] + 0.02, WING[1] - 0.06), (X1 - XM + 0.16, 0.03, 0.12), 0.006, FA('childpaint'))
    # The front step under its canopy, a boot scraper, the door's architrave outside, a name card in a holder.
    x0s, hs = STEP114
    cbox(EX.bm, ((x0s + X0) / 2, 0.08, hs / 2), (X0 - x0s, 1.36, hs), 0.008, EX('concrete'))
    for y in (-0.52, 0.68):
        cbox(EX.bm, (X0 - 0.12, y, 2.36), (0.24, 0.05, 0.05), 0.006, EX('wood'), rot=_ry(math.radians(-8)))
        cbox(EX.bm, (X0 - 0.06, y, 2.22), (0.04, 0.05, 0.28), 0.006, EX('wood'), rot=_ry(math.radians(30)))
    cbox(EX.bm, (X0 - 0.2, 0.08, 2.42), (0.46, 1.42, 0.04), 0.008, EX('slate'), rot=_ry(math.radians(-14)))
    for sy in (-1, 1):
        cbox(EX.bm, (X0 - 0.012, sy * (DOOR_HALF + 0.045), DOOR_H / 2 + 0.04), (0.025, 0.09, DOOR_H + 0.08), 0.005, EX('childpaint'))
    cbox(EX.bm, (X0 - 0.015, 0.0, DOOR_H + 0.08), (0.03, 2 * DOOR_HALF + 0.24, 0.1), 0.006, EX('childpaint'))
    sx_, sy_ = X0 - 0.22, 0.6                                                  # the boot scraper
    cbox(EX.bm, (sx_, sy_, 0.012), (0.12, 0.3, 0.024), 0.004, EX('iron'))
    for dy in (-0.12, 0.12):
        cbox(EX.bm, (sx_, sy_ + dy, 0.09), (0.02, 0.02, 0.16), 0.003, EX('iron'))
    cbox(EX.bm, (sx_, sy_, 0.12), (0.006, 0.26, 0.05), 0.002, EX('iron'))
    cbox(EX.bm, (X0 - 0.006, DOOR_HALF + 0.22, 1.32), (0.012, 0.15, 0.1), 0.003, EX('brass'))
    add_cyl(EX.bm, (X0 - 0.3, -0.62, EAVE - 0.08), (X0 - 0.05, -0.6, EAVE - 0.3), 0.032, seg=8, mat=EX('iron'))
    drainpipe(EX, X0 - 0.05, -0.6, EAVE - 0.3)
    # Behind the window over the sink, the back lane: a wall of rock, a pipe, a window across the way still lit.
    cbox(EX.bm, ((KW[0] + KW[1]) / 2, 2.3, 1.4), (2.2, 0.3, 2.8), 0.05, EX('rock'))
    add_cyl(EX.bm, (KW[0] - 0.8, 1.9, 2.2), (KW[1] + 0.8, 1.9, 2.0), 0.05, seg=8, mat=EX('iron'))
    add_box(EX.bm, (KW[1] + 0.25, 2.14, 1.55), (0.36, 0.02, 0.42), mat=EX('windowglow'))
    add_box(EX.bm, (KW[1] + 0.25, 2.13, 1.55), (0.02, 0.02, 0.42), mat=EX('dark'))
    # ---- the street wall: C114Facade -------------------------------------------------------------------------
    fy0, fy1 = FACADE_Y
    HW, LW = (95.35 + S9, 96.0 + S9, 1.0, 1.75), (98.25 + S9, 99.45 + S9, 0.85, 1.85)
    UW = ((95.4 + S9, 96.2 + S9, 3.05, 3.95), (98.6 + S9, 99.4 + S9, 3.05, 3.95))
    wall_x(FA.bm, X0, XM, fy0, fy1, 0.0, UPPER[1], [HW, LW, *UW], FA('homeplaster'))
    wall_x(FA.bm, XM, X1, fy0, fy1, 0.0, HOME_CEIL + 0.22, (), FA('homeplaster'))
    prism(FA.bm, [(X0, UPPER[1]), (RIDGE[0], RIDGE[1] - ROOF_T - 0.02), (XM, UPPER[1])], 'y', fy0, fy1, mat=FA('homeplaster'))
    prism(FA.bm, [(fy0, HOME_CEIL + 0.22), (fy0, _wing_z(fy0) - 0.12), (fy1, _wing_z(fy1) - 0.12), (fy1, HOME_CEIL + 0.22)], 'x', XM, X1, mat=FA('homeplaster'))
    cbox(FA.bm, ((X0 + X1) / 2, fy0 + 0.07, 0.15), (X1 - X0 + 0.04, 0.2, 0.3), 0.015, FA('concrete'))          # plinth
    cbox(FA.bm, ((X0 + XM) / 2, fy0 + 0.06, HOME_CEIL + 0.16), (XM - X0 + 0.06, 0.22, 0.12), 0.02, FA('concrete'))   # string course
    cbox(FA.bm, ((X0 + XM) / 2, fy0 + 0.05, UPPER[1] + 0.04), (XM - X0 + 0.06, 0.2, 0.08), 0.015, FA('concrete'))
    for corner, sgn, zq0, zq1 in ((X0, 1, 0.3, UPPER[1]), (XM, -1, HOME_CEIL + 0.3, UPPER[1]), (X1, -1, 0.3, HOME_CEIL + 0.15)):   # quoins
        z, k = zq0, 0
        while z + 0.2 < zq1:
            w_ = 0.3 if k % 2 == 0 else 0.18
            cbox(FA.bm, (corner + sgn * w_ / 2, fy0 - 0.012, z + 0.1), (w_, 0.04, 0.2), 0.008, FA('plasterA'))
            z += 0.235
            k += 1
    for (rx0, rz0), (rx1, rz1) in (((X0 - 0.26, EAVE + 0.02), RIDGE), (RIDGE, (XM + 0.26, EAVE + 0.02))):   # barge boards
        ln = math.hypot(rx1 - rx0, rz1 - rz0)
        cbox(FA.bm, ((rx0 + rx1) / 2, -0.965, (rz0 + rz1) / 2 - 0.05), (ln, 0.04, 0.16), 0.008, FA('childpaint'),
             rot=_ry(-math.atan2(rz1 - rz0, rx1 - rx0)))
    window_unit(FA, (HW[0] + HW[1]) / 2, fy0, HW[2], HW[3], HW[1] - HW[0], frame='childpaint', rnd=rnd)
    window_unit(FA, (LW[0] + LW[1]) / 2, fy0, LW[2], LW[3], LW[1] - LW[0], frame='childpaint', rnd=rnd, curtains='letters')
    for w in UW:
        window_unit(FA, (w[0] + w[1]) / 2, fy0, w[2], w[3], w[1] - w[0], frame='childpaint', kind='shutters', rnd=rnd)
    add_torus(FA.bm, (RIDGE[0], fy0 - 0.01, 5.5), (0, 1, 0), 0.2, 0.035, seg=20, rseg=6, mat=FA('childpaint'))     # the gable's round window
    add_cyl(FA.bm, (RIDGE[0], fy0 + 0.02, 5.5), (RIDGE[0], fy0 - 0.005, 5.5), 0.19, seg=20, mat=FA('glass'))
    add_torus(FA.bm, (103.0 + S9, fy0 - 0.01, 2.05), (0, 1, 0), 0.12, 0.025, seg=16, rseg=5, mat=FA('concrete'))        # the wing's air brick
    for k in range(5):
        add_box(FA.bm, (103.0 + S9 - 0.08 + 0.04 * k, fy0 - 0.003, 2.05), (0.012, 0.01, 0.2 - 0.06 * abs(k - 2)), mat=FA('shaft'))
    cbox(FA.bm, ((LW[0] + LW[1]) / 2, fy0 - 0.09, LW[2] - 0.15), (LW[1] - LW[0] + 0.04, 0.16, 0.16), 0.01, FA('wood'))   # a window box
    for k in range(5):
        dead_plant(FA, LW[0] + 0.15 + 0.22 * k, fy0 - 0.09, LW[2] - 0.08, rnd, pot='wood', r=0.02, h=0.01)
    drainpipe(FA, XM + 0.12, fy0 - 0.06, EAVE - 0.08, zbot=HOME_CEIL + 0.5)
    drainpipe(FA, X1 - 0.1, WING[0] + 0.03, WING[1] - 0.06)
    cbox(FA.bm, (X0 + 0.42, fy0 - 0.008, 1.36), (0.15, 0.012, 0.1), 0.003, FA('brass'))
    cbox(FA.bm, (X0 + 0.42, fy0 - 0.02, 2.05), (0.08, 0.04, 0.12), 0.006, FA('iron'))                            # a lamp by the corner, dead
    add_cyl(FA.bm, (X0 + 0.42, fy0 - 0.03, 2.08), (X0 + 0.42, fy0 - 0.16, 2.12), 0.012, seg=6, mat=FA('iron'))
    add_sphere(FA.bm, (X0 + 0.42, fy0 - 0.17, 2.03), 0.05, seg=10, mat=FA('deadbulb'))
    add_cyl(FA.bm, (X0 + 0.12, fy0 - 0.03, 2.45), (XM - 0.3, fy0 - 0.03, 2.45), 0.007, seg=5, mat=FA('rubber'))   # its service cable
    facade = FA.done('C114Facade', coll)
    for v in facade.data.vertices:                                             # its origin at the street corner, on the floor
        v.co -= Vector((X0, fy0, 0.0))
    facade.location = (X0, fy0, 0.0)
    bpy.context.view_layer.update()
    kids = []
    bm = bmesh.new()                                                           # the lamp's warmth through the curtains
    add_box(bm, ((LW[0] + LW[1]) / 2, fy1 + 0.035, (LW[2] + LW[3]) / 2), (LW[1] - LW[0] - 0.12, 0.004, LW[3] - LW[2] - 0.12))
    kids.append(_obj('D5Window114Glow', bm, [m['homelamp']], coll))
    kids.append(_plane('D5NameCard114Wall', (0.12, 0.075), (X0 + 0.42, fy0 - 0.016, 1.36), _imgmat('D5NameCardMat', 'namecard114.png', rough=0.8), coll))
    kids.append(_plane('D5Plate114', (0.26, 0.114), (X0 + 0.42, fy0 - 0.006, 1.55), _imgmat('D5Plate114Mat', 'plate_c114.png', rough=0.3), coll))
    bpy.context.view_layer.update()
    for ob in kids:
        ob.parent = facade
        ob.matrix_parent_inverse = facade.matrix_world.inverted()
    # ---- section caps: every cut face, near-black ------------------------------------------------------------
    cy = CUT_Y - 0.003
    for xa, xb, za, zb in ((X0, X1, -0.3, 0.0), (X0, X0 + 0.18, 0.0, UPPER[1]), (P1 - 0.06, P1 + 0.06, 0.0, HOME_CEIL),
                           (xi - 0.06, xi + 0.06, 0.0, UPPER[1]), (xb - 0.06, xb + 0.06, 0.0, _wing_z(CUT_Y) - 0.12),
                           (X0, X1, HOME_CEIL, UPPER[0]), (97.54 + S9, 97.66 + S9, UPPER[0], UPPER[1]), (X0, XM, UPPER[1], UPPER[1] + 0.15)):
        add_box(CAP.bm, ((xa + xb) / 2, cy, (za + zb) / 2), (xb - xa, 0.006, zb - za), mat=CAP('sectioncap'))
    prism(CAP.bm, [(X0, UPPER[1] + 0.15), (RIDGE[0], RIDGE[1] - ROOF_T - 0.02), (XM, UPPER[1] + 0.15)], 'y', CUT_Y - 0.004, CUT_Y - 0.001,
          mat=CAP('sectioncap'))                                               # the attic's dark
    CAP.done('C114Section', coll)
    build_front_door114(m, coll)                                             # shut, hinged; its handle and the child's cord
    _plane('D5NameCard114Out', (0.12, 0.075), (X0 - 0.014, DOOR_HALF + 0.22, 1.32), bpy.data.materials['D5NameCardMat'], coll,
           rot=_rz(math.radians(-90)) @ _rx(math.radians(90)))
    IN.done('C114Interior', coll)
    EX.done('C114Exterior', coll)
    build_home114_rooms(m, coll, rnd, KW)


def build_home114_rooms(m, coll, rnd, KW):
    """What is in C-114: in the hall, a mat, the light switch (CurioSwitch) and the bulb it lights (HallBulb), the
    photograph, a shoe rack with a child's yellow boots beside a grown-up's, coat hooks with a small yellow raincoat.
    In the kitchen and living room: the range and its kettle, the sink under the window, the table with three chairs,
    one a child's, a sideboard with the radio (CurioRadio) and the lamp left on (HomeLampBulb), a rug. Upstairs, a
    bed and a wardrobe in the dark."""
    Y = BACK_Y
    # ---- the hall ------------------------------------------------------------------------------------------------
    H = Batch(m)
    cbox(H.bm, (X0_114 + 0.62, 0.0, 0.008), (0.6, 0.46, 0.016), 0.004, H('paper'))                 # the doormat
    rx0, rx1 = 96.0 + S9, 96.78 + S9                                                     # the shoe rack, two shelves
    for x in (rx0, rx1):
        for y in (Y - 0.3, Y - 0.04):
            cbox(H.bm, (x, y, 0.17), (0.03, 0.03, 0.34), 0.004, H('wood'))
    for z in (0.05, 0.27):
        for y in (Y - 0.27, Y - 0.17, Y - 0.07):
            cbox(H.bm, ((rx0 + rx1) / 2, y, z), (rx1 - rx0, 0.05, 0.015), 0.003, H('wood'))
    for k, (x, y, rz) in enumerate(((96.2 + S9, Y - 0.17, 0.1), (96.36 + S9, Y - 0.15, -0.05))):            # the grown-up's boots, on the floor
        rounded_box((0.28, 0.1, 0.09), (x, y, 0.08), p=2.6, cuts=2, mat=H('paper'), bm=H.bm, rot=_rz(math.pi / 2 + rz))
        rounded_box((0.11, 0.09, 0.16), (x, y + 0.08, 0.15), p=2.6, cuts=2, mat=H('paper'), bm=H.bm, rot=_rz(rz))
    for k, (x, y, rz) in enumerate(((96.56 + S9, Y - 0.17, 0.15), (96.66 + S9, Y - 0.15, -0.2))):          # the child's, on the shelf above
        rounded_box((0.15, 0.06, 0.06), (x, y, 0.31), p=2.6, cuts=2, mat=H('yellow'), bm=H.bm, rot=_rz(math.pi / 2 + rz))
        rounded_box((0.065, 0.06, 0.11), (x, y + 0.04, 0.36), p=2.6, cuts=2, mat=H('yellow'), bm=H.bm, rot=_rz(rz))
    for k, x in enumerate((96.16 + S9, 96.34 + S9)):                                     # slippers
        rounded_box((0.2, 0.08, 0.04), (x, Y - 0.17, 0.28), p=2.6, cuts=2, mat=H('dado'), bm=H.bm, rot=_rz(math.pi / 2 + 0.1 * k))
    cbox(H.bm, ((rx0 + rx1) / 2, Y - 0.02, 1.58), (rx1 - rx0 + 0.04, 0.03, 0.08), 0.006, H('wood'))      # the coat rail
    for x in (96.12 + S9, 96.4 + S9, 96.66 + S9):
        add_cyl(H.bm, (x, Y - 0.03, 1.58), (x, Y - 0.1, 1.62), 0.008, seg=6, mat=H('brass'))
    rounded_box((0.36, 0.12, 0.92), (96.12 + S9, Y - 0.11, 1.13), p=4.0, cuts=3, mat=H('depot_green'), bm=H.bm, taper=lambda z: 0.85 + 0.15 * (-z),
                seed=3, dents=((0.008, 6.0),))
    rounded_box((0.24, 0.1, 0.5), (96.62 + S9, Y - 0.1, 1.33), p=4.0, cuts=3, mat=H('yellow'), bm=H.bm, taper=lambda z: 0.8 + 0.2 * (-z), seed=4,
                dents=((0.006, 7.0),))
    add_sphere(H.bm, (96.62 + S9, Y - 0.09, 1.6), 0.07, seg=10, scale=(1.0, 0.8, 0.9), mat=H('yellow'))
    sx, sz = SWITCH                                                            # the photograph over the switch
    cbox(H.bm, (sx, Y - 0.012, 1.5), (0.24, 0.024, 0.3), 0.005, H('wood'))
    cbox(H.bm, (X0_114 + 1.2, Y - 0.012, 2.33), (0.18, 0.024, 0.04), 0.004, H('homeplaster'))
    add_cyl(H.bm, (HALL_BULB[0], HALL_BULB[1], HOME_CEIL), (HALL_BULB[0], HALL_BULB[1], HOME_CEIL - 0.012), 0.08, seg=16, mat=H('homeplaster'))
    add_cyl(H.bm, (HALL_BULB[0], HALL_BULB[1], HOME_CEIL), (HALL_BULB[0], HALL_BULB[1], HALL_BULB[2] + 0.1), 0.004, seg=4, mat=H('rubber'))
    add_cyl(H.bm, (HALL_BULB[0], HALL_BULB[1], HALL_BULB[2] + 0.11), (HALL_BULB[0], HALL_BULB[1], HALL_BULB[2] + 0.04), 0.017, seg=10, mat=H('brass'))
    add_cyl(H.bm, (HALL_BULB[0], HALL_BULB[1], HALL_BULB[2] + 0.07), (HALL_BULB[0], HALL_BULB[1], HALL_BULB[2] - 0.02), 0.03, 0.09, seg=16,
            mat=H('enamel'))
    H.done('C114HallProps', coll)
    _plane('D5HallPhoto', (0.17, 0.23), (sx, Y - 0.026, 1.5), _imgmat('D5PhotoMat', 'photo.png', rough=0.35), coll)
    bm = bmesh.new()
    add_sphere(bm, (HALL_BULB[0], HALL_BULB[1], HALL_BULB[2]), 0.032, seg=12, scale=(1, 1, 1.25))
    _obj_at('HallBulb', bm, [m['hallbulb9']], coll, HALL_BULB)
    bm = bmesh.new()                                                           # the light switch: a plate and its toggle
    cbox(bm, (sx, Y - 0.006, sz), (0.075, 0.012, 0.11), 0.004, 0)
    add_cyl(bm, (sx, Y - 0.012, sz), (sx, Y - 0.018, sz), 0.022, seg=12, mat=1)
    sw = _obj_at('CurioSwitch', bm, [m['enamel'], m['brass']], coll, (sx, Y - 0.012, sz))
    bm = bmesh.new()
    add_cyl(bm, (0, -0.006, 0), (0, -0.03, 0.012), 0.006, 0.005, seg=8)
    add_sphere(bm, (0, -0.031, 0.013), 0.008, seg=8)
    tog = _obj('CurioSwitchToggle', bm, [m['brass']], coll)
    tog.location = (sx, Y - 0.012, sz)
    tog.rotation_euler = (math.radians(-25), 0, 0)                             # down: off
    bpy.context.view_layer.update()
    tog.parent = sw
    tog.matrix_parent_inverse = sw.matrix_world.inverted()
    # ---- the kitchen: the range and kettle, the sink under the window ----------------------------------------------
    K = Batch(m)
    kx = P1 + 0.42
    cbox(K.bm, (kx, Y - 0.24, 0.42), (0.6, 0.46, 0.84), 0.015, K('iron'))
    cbox(K.bm, (kx, Y - 0.24, 0.86), (0.66, 0.5, 0.04), 0.01, K('iron'))
    for dx in (-0.14, 0.14):
        add_cyl(K.bm, (kx + dx, Y - 0.22, 0.88), (kx + dx, Y - 0.22, 0.895), 0.1, seg=16, mat=K('steel'))
    cbox(K.bm, (kx, Y - 0.475, 0.45), (0.42, 0.02, 0.36), 0.006, K('iron'))
    add_cyl(K.bm, (kx - 0.25, Y - 0.52, 0.75), (kx + 0.25, Y - 0.52, 0.75), 0.012, seg=8, mat=K('brass'))
    for dx in (-0.25, 0.25):
        add_cyl(K.bm, (kx + dx, Y - 0.47, 0.75), (kx + dx, Y - 0.52, 0.75), 0.01, seg=6, mat=K('brass'))
    cbox(K.bm, (kx + 0.12, Y - 0.49, 0.45), (0.04, 0.02, 0.1), 0.004, K('brass'))
    add_cyl(K.bm, (kx + 0.16, Y - 0.06, 0.88), (kx + 0.16, Y - 0.06, HOME_CEIL), 0.055, seg=12, mat=K('iron'))        # the stovepipe
    add_cyl(K.bm, (kx + 0.16, Y - 0.06, 1.6), (kx + 0.16, Y - 0.06, 1.66), 0.07, seg=12, mat=K('iron'))
    kt = Vector((kx - 0.14, Y - 0.22, 0.895))                                  # the kettle on the hob, enamelled
    add_cyl(K.bm, kt, kt + Vector((0, 0, 0.13)), 0.08, 0.065, seg=16, mat=K('enamel'))
    add_cyl(K.bm, kt + Vector((0, 0, 0.13)), kt + Vector((0, 0, 0.15)), 0.04, 0.02, seg=12, mat=K('enamel'))
    add_sphere(K.bm, kt + Vector((0, 0, 0.16)), 0.012, seg=8, mat=K('iron'))
    add_cyl(K.bm, kt + Vector((0.06, 0, 0.04)), kt + Vector((0.14, 0, 0.12)), 0.016, 0.009, seg=8, mat=K('enamel'))
    add_torus(K.bm, kt + Vector((0, 0, 0.16)), (1, 0, 0), 0.06, 0.006, seg=12, rseg=4, mat=K('iron'))
    cx0, cx1 = 97.62 + S9, 98.68 + S9                                                    # the sink's cupboard and worktop
    cbox(K.bm, ((cx0 + cx1) / 2, Y - 0.25, 0.42), (cx1 - cx0, 0.5, 0.84), 0.012, K('pigeon'))
    for k in range(2):
        cbox(K.bm, (cx0 + (cx1 - cx0) * (k + 0.5) / 2, Y - 0.505, 0.44), ((cx1 - cx0) / 2 - 0.06, 0.012, 0.66), 0.004, K('pigeon'))
        add_sphere(K.bm, (cx0 + (cx1 - cx0) * (k + 0.5) / 2 + (0.18 if k == 0 else -0.18), Y - 0.52, 0.62), 0.015, seg=8, mat=K('brass'))
    cbox(K.bm, ((cx0 + cx1) / 2, Y - 0.26, 0.86), (cx1 - cx0 + 0.04, 0.54, 0.04), 0.008, K('concrete'))
    cbox(K.bm, ((KW[0] + KW[1]) / 2, Y - 0.26, 0.84), (0.5, 0.36, 0.06), 0.01, K('enamel'))
    add_cyl(K.bm, ((KW[0] + KW[1]) / 2, Y - 0.06, 0.88), ((KW[0] + KW[1]) / 2, Y - 0.06, 1.04), 0.012, seg=8, mat=K('brass'))
    add_cyl(K.bm, ((KW[0] + KW[1]) / 2, Y - 0.06, 1.04), ((KW[0] + KW[1]) / 2, Y - 0.18, 1.0), 0.01, seg=8, mat=K('brass'))
    for k, x in enumerate((KW[0] + 0.1, KW[0] + 0.22, KW[1] - 0.12)):          # cups on the sill
        add_cyl(K.bm, (x, Y + 0.02, KW[2] + 0.005), (x, Y + 0.02, KW[2] + 0.085), 0.03, 0.034, seg=10, mat=K('childpaint' if k == 1 else 'enamel'))
    cbox(K.bm, (cx1 - 0.05, Y - 0.012, 1.4), (0.3, 0.024, 0.02), 0.004, K('wood'))
    for sx in (-1, 1):                                                         # the window's frame, glass, bars, a curtain
        cbox(K.bm, ((KW[0] + KW[1]) / 2 + sx * (KW[1] - KW[0]) / 2, Y + 0.02, (KW[2] + KW[3]) / 2), (0.05, 0.05, KW[3] - KW[2] + 0.05), 0.006,
             K('childpaint'))
    for z in (KW[2], KW[3]):
        cbox(K.bm, ((KW[0] + KW[1]) / 2, Y + 0.02, z), (KW[1] - KW[0] + 0.05, 0.05, 0.05), 0.006, K('childpaint'))
    add_box(K.bm, ((KW[0] + KW[1]) / 2, Y + 0.06, (KW[2] + KW[3]) / 2), (KW[1] - KW[0], 0.006, KW[3] - KW[2]), mat=K('glass'))
    cbox(K.bm, ((KW[0] + KW[1]) / 2, Y + 0.05, (KW[2] + KW[3]) / 2), (0.025, 0.03, KW[3] - KW[2]), 0.004, K('childpaint'))
    cbox(K.bm, ((KW[0] + KW[1]) / 2, Y - 0.03, KW[3] - 0.05), (KW[1] - KW[0] + 0.12, 0.02, 0.12), 0.004, K('toypatch'))
    for k in range(3):
        cbox(K.bm, (KW[0] + 0.03 + 0.025 * k, Y - 0.025 - 0.006 * (k % 2), (KW[2] + KW[3]) / 2 + 0.02), (0.03, 0.012, KW[3] - KW[2] - 0.04),
             0.004, K('toypatch'))
    cbox(K.bm, (KW[0] + 0.06, Y - 0.012, 1.3), (0.06, 0.004, 0.02), 0.002, K('wood'))
    K.done('C114Kitchen', coll)
    # ---- the table and three chairs: one at each end, one at the back; the child's is the tall one, with a cushion ----
    T = Batch(m)
    tx, ty, top = 99.12 + S9, 0.52, 0.72
    cbox(T.bm, (tx, ty, top - 0.018), (0.88, 0.56, 0.036), 0.008, T('wood'))
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_cyl(T.bm, (tx + sx * 0.38, ty + sy * 0.23, 0.0), (tx + sx * 0.38, ty + sy * 0.23, top - 0.036), 0.02, 0.025, seg=10, mat=T('wood'))
    for sy in (-1, 1):
        cbox(T.bm, (tx, ty + sy * 0.23, top - 0.08), (0.74, 0.02, 0.08), 0.004, T('wood'))
    cbox(T.bm, (tx, ty, top + 0.003), (0.92, 0.6, 0.006), 0.002, T('letters'))                       # the cloth
    cbox(T.bm, (tx, ty - 0.302, top - 0.05), (0.92, 0.006, 0.1), 0.002, T('letters'))
    chair(T, tx - 0.56, ty, -math.pi / 2)
    chair(T, tx + 0.03, ty + 0.4, math.pi + 0.08)
    chair(T, tx + 0.6, ty, math.pi / 2, seat_h=0.6, seat=0.32, back_h=1.0, child=True, cushion='toypatch')
    add_cyl(T.bm, (tx - 0.05, ty + 0.05, top + 0.006), (tx - 0.05, ty + 0.05, top + 0.08), 0.12, 0.16, seg=16, mat=T('enamel'))   # a bowl
    for x, y, mat in ((tx - 0.28, ty - 0.12, 'enamel'), (tx + 0.26, ty - 0.1, 'childpaint')):
        add_cyl(T.bm, (x, y, top + 0.006), (x, y, top + 0.085), 0.032, 0.036, seg=10, mat=T(mat))
        add_torus(T.bm, (x + 0.04, y, top + 0.045), (0, 1, 0), 0.018, 0.005, seg=8, rseg=3, mat=T(mat))
    add_cyl(T.bm, (tx + 0.1, ty + 0.14, top + 0.006), (tx + 0.1, ty + 0.14, top + 0.2), 0.05, 0.04, seg=12, mat=T('enamel'))
    add_cyl(T.bm, (tx, ty, HOME_CEIL), (tx, ty, 1.62), 0.004, seg=4, mat=T('rubber'))                       # the lamp over it, dead
    add_cyl(T.bm, (tx, ty, 1.66), (tx, ty, 1.52), 0.04, 0.2, seg=16, mat=T('depot_green'))
    T.done('C114Table', coll)
    _plane('D5RugLiving', (1.55, 1.05), (tx, 0.36, 0.004), _imgmat('D5RugMat', 'rug.png', rough=0.95), coll, rot=Matrix.Identity(4))
    # ---- the sideboard, the radio and the lamp left on ---------------------------------------------------------------
    SB = Batch(m)
    bx0, bx1, btop = 99.78 + S9, INNER[0] - 0.1, 0.58
    cbox(SB.bm, ((bx0 + bx1) / 2, Y - 0.2, btop / 2), (bx1 - bx0, 0.4, btop), 0.012, SB('pigeon'))
    cbox(SB.bm, ((bx0 + bx1) / 2, Y - 0.2, btop + 0.015), (bx1 - bx0 + 0.04, 0.44, 0.03), 0.008, SB('wood'))
    for k in range(2):
        cx = bx0 + (bx1 - bx0) * (k + 0.5) / 2
        cbox(SB.bm, (cx, Y - 0.405, btop / 2), ((bx1 - bx0) / 2 - 0.05, 0.012, btop - 0.12), 0.004, SB('pigeon'))
        add_sphere(SB.bm, (cx + (0.1 if k == 0 else -0.1), Y - 0.42, btop * 0.6), 0.013, seg=8, mat=SB('brass'))
    lx, ly = bx1 - 0.12, Y - 0.2                                               # the lamp: a base, a stem, a pleated shade
    add_cyl(SB.bm, (lx, ly, btop + 0.03), (lx, ly, btop + 0.06), 0.07, seg=14, mat=SB('brass'))
    add_cyl(SB.bm, (lx, ly, btop + 0.06), (lx, ly, btop + 0.3), 0.012, seg=8, mat=SB('brass'))
    add_cyl(SB.bm, (lx, ly, btop + 0.27), (lx, ly, btop + 0.45), 0.12, 0.075, seg=16, mat=SB('letters'))     # its shade
    add_cyl(SB.bm, (lx, ly, btop + 0.44), (lx, ly, btop + 0.455), 0.078, seg=16, mat=SB('brass'))
    cbox(SB.bm, (bx0 + 0.15, Y - 0.012, 1.45), (0.24, 0.006, 0.32), 0.002, SB('letters'))                  # a calendar
    for k in range(4):
        add_box(SB.bm, (bx0 + 0.15, Y - 0.016, 1.38 - 0.04 * k), (0.18, 0.002, 0.008), mat=SB('shaft'))
    SB.done('C114Sideboard', coll)
    bm = bmesh.new()
    add_sphere(bm, (lx, ly, btop + 0.3), 0.032, seg=12, scale=(1, 1, 1.2))
    _obj_at('HomeLampBulb', bm, [m['homelamp']], coll, (lx, ly, btop + 0.3))
    # CurioRadio: a wireless set on the sideboard, its origin at its foot: a rounded wooden case, a cloth speaker
    # behind a fretwork, a lit-glass dial (unlit), two knobs.
    rx, ry = RADIO_X, Y - 0.2
    bm = bmesh.new()                       # mats: 0 case, 1 cloth, 2 dial, 3 knobs
    rounded_box((0.3, 0.15, 0.2), (0, 0, 0.1), p=3.0, cuts=4, bm=bm, mat=0, dents=((0.001, 12.0),), seed=21)
    add_cyl(bm, (-0.05, -0.068, 0.115), (-0.05, -0.078, 0.115), 0.06, seg=20, mat=1)
    for k in range(5):
        add_box(bm, (-0.05 - 0.05 + 0.025 * k, -0.08, 0.115), (0.006, 0.006, 0.11 - 0.02 * abs(k - 2)), mat=0)
    cbox(bm, (0.075, -0.074, 0.13), (0.09, 0.008, 0.05), 0.003, 2)
    for dx in (0.05, 0.1):
        add_cyl(bm, (dx, -0.07, 0.05), (dx, -0.09, 0.05), 0.016, seg=12, mat=3)
    bmesh.ops.translate(bm, vec=(rx, ry, btop + 0.03), verts=bm.verts)
    _obj_at('CurioRadio', bm, [m['wood'], m['paper'], m['enamel'], m['brass']], coll, (rx, ry, btop + 0.03))
    # ---- upstairs, in the dark: the parents' bed, a wardrobe; a suitcase and boxes in the box room -----------------
    U = Batch(m)
    z0 = UPPER[0]
    cbox(U.bm, (99.2 + S9, 0.3, z0 + 0.25), (1.9, 1.3, 0.22), 0.02, U('pigeon'))
    cbox(U.bm, (99.2 + S9, 0.32, z0 + 0.42), (1.86, 1.24, 0.14), 0.04, U('letters'))
    cbox(U.bm, (98.22 + S9, 0.3, z0 + 0.55), (0.06, 1.34, 1.1), 0.01, U('pigeon'))
    cbox(U.bm, (100.1 + S9, Y - 0.3, z0 + 0.95), (0.55, 0.55, 1.9), 0.02, U('pigeon'))
    for k, (x, w, h) in enumerate(((95.2 + S9, 0.6, 0.4), (95.3 + S9, 0.45, 0.3), (96.0 + S9, 0.5, 0.45), (96.7 + S9, 0.7, 0.25))):
        cbox(U.bm, (x, Y - 0.35, z0 + (0.4 if k == 1 else 0) + h / 2), (w, 0.5, h), 0.01, U('paper' if k != 3 else 'depot_green'))
    U.done('C114Upstairs', coll)


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
    _plane('D5Drawing', (0.3, 0.225), (92.36 + DX, BACK_Y - 0.008, 1.42), _image_material('D5DrawingMat', _tex('child_drawing.png'), rough=0.85), coll,
           rot=_ry(math.radians(4)) @ _rx(math.radians(90)))
    bm = bmesh.new()
    add_sphere(bm, (92.36 + DX, BACK_Y - 0.016, 1.515), 0.008, seg=8)
    _obj('D5DrawingPin', bm, [m['steel']], coll)
    # A paper mobile from the ceiling over the bed: stars and a bird.
    bm, card = bmesh.new(), bmesh.new()
    mx, my = 91.8 + DX, 0.62
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
    _plane('D5Rug', (1.25, 0.78), (93.2 + DX, 0.3, 0.004), _imgmat('D5RugMat', 'rug.png', rough=0.95), coll, rot=Matrix.Identity(4))

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
    _plane('D5Photo', (0.128, 0.188), pc + Vector((0, -0.006, 0)), _imgmat('D5PhotoMat', 'photo.png', rough=0.35), coll,
           rot=_rx(math.radians(80)))


def build_terminal(m, coll):
    """The forwarding terminal on the bedroom wall: a depot-green housing round the screen recess (the
    game draws the screen at y 1.0), the reader below it angled down to a courier's chest, its bezel bare
    steel worn bright, three lamps over the screen and a conduit up into the ceiling."""
    x0, x1, z0, z1 = TERM_HOUSING
    sx0, sx1 = TERM_X - SCREEN[0] / 2, TERM_X + SCREEN[0] / 2
    sz0, sz1 = SCREEN_Z - SCREEN[1] / 2, SCREEN_Z + SCREEN[1] / 2
    yc, dp = (TERM_FRONT + BACK_Y) / 2, BACK_Y - TERM_FRONT
    bm = bmesh.new()                       # mats: 0 green, 1 steel, 2 polished steel, 3 dark
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
    # The reader: a short barrel out of the housing, tipped down 35 degrees, a dark lens and a bright steel ring.
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
    _obj('ForwardTerminal', bm, [m['depot_green'], m['steel'], m['pawlsteel'], m['shaft']], coll)
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
    x by its grip bar on the left end (0.44 high): bare steel, polished where hands went."""
    h, dd, top, hut = DESK_HALF, 0.42, DESK_TOP, DESK_HUTCH
    side = math.radians(DESK_SIDE_TILT)
    drop = (2 * h - 0.07) * math.sin(side)                                    # its right legs gave way
    bm = bmesh.new()                       # mats: 0 blue paint, 1 wood, 2 polished steel, 3 paper, 4 cork
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
    # The hutch: painted sides and a cap, a small shelf, a cork board with drawings pinned to it.
    for sx in (-1, 1):
        add_box(bm, (sx * (h - 0.01), dd / 2 - 0.08, (top + hut) / 2), (0.02, 0.16, hut - top))
    add_box(bm, (0, dd / 2 - 0.08, hut - 0.01), (2 * h, 0.17, 0.02))
    add_box(bm, (0, dd / 2 - 0.08, 0.9), (2 * h - 0.04, 0.15, 0.018))
    add_box(bm, (0, dd / 2 - 0.006, (top + hut) / 2), (2 * h - 0.02, 0.012, hut - top), mat=4)
    rnd = random.Random(5050)
    for k, (x, z) in enumerate(((-0.33, 0.74), (-0.05, 0.72), (0.3, 0.76), (-0.2, 1.04), (0.22, 1.06))):
        add_box(bm, (x, dd / 2 - 0.014, z), (0.15, 0.003, 0.11), mat=3, rot=_ry(rnd.uniform(-0.2, 0.2)))
    # Down on its broken right side, and tipped back until the hutch rests against the terminal.
    foot = Vector((-h + 0.035, 0, 0))
    bmesh.ops.transform(bm, matrix=Matrix.Translation(foot) @ _ry(side) @ Matrix.Translation(-foot), verts=bm.verts)
    pivot = Vector((0, dd / 2, 0))
    bmesh.ops.transform(bm, matrix=Matrix.Translation(pivot) @ _rx(math.radians(DESK_TILT)) @ Matrix.Translation(-pivot), verts=bm.verts)
    ymax = max(v.co.y for v in bm.verts)
    bmesh.ops.translate(bm, vec=(0, (TERM_FRONT - 0.004 - DESK_Y) - ymax, -min(v.co.z for v in bm.verts)), verts=bm.verts)
    # The grip bar on its left end, level, where a claw can take it.
    hx, hz = DESK_HANDLE
    add_cyl(bm, (hx, -0.11, hz), (hx, 0.11, hz), 0.014, seg=10, mat=2)
    for y in (-0.09, 0.09):
        add_cyl(bm, (hx, y, hz), (-h + 0.012, y, hz + 0.0), 0.009, seg=8, mat=2)
    ob = _obj('ChildDesk', bm, [m['childpaint'], m['wood'], m['pawlsteel'], m['letters'], m['paper']], coll)
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
    for x in (96.2 + DX, 97.4 + DX, 98.6 + DX, 99.8 + DX):
        add_box(bm, (x, BACK_Y - 0.04, 2.08), (0.04, 0.08, 0.2))
    _obj('D5Pipes', bm, [m['steel']], coll)
    bm = bmesh.new()                       # a caged lamp over the stair foot
    lx = 97.15 + DX
    lz = 1.92
    add_box(bm, (lx, BACK_Y - 0.03, lz), (0.12, 0.06, 0.12))
    for k in range(4):
        a = k * math.pi / 2
        add_cyl(bm, (lx + 0.05 * math.cos(a), BACK_Y - 0.1 + 0.05 * math.sin(a), lz - 0.05), (lx + 0.04 * math.cos(a), BACK_Y - 0.1 + 0.04 * math.sin(a), lz - 0.2), 0.003, seg=4)
    _obj('D5PassageLampCage', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_sphere(bm, (lx, BACK_Y - 0.1, lz - 0.14), 0.035, seg=12)
    _obj('LaneBulbPassage', bm, [m['lanebulb']], coll)
    _plane('D5SchoolSign', (0.78, 0.325), (97.15 + DX, BACK_Y - 0.006, 1.5), _imgmat('D5SchoolSignMat', 'school_sign.png', rough=0.7), coll)


def _project_decal(verts, faces, uvs, bvh, x0, x1, z0, z1, step=0.02, ahead=0.002, y_from=-1.5, reach=8.0, bucket=0.02):
    """Lay a decal over whatever `bvh` shows the camera between x0..x1 and z0..z1: rays along +y from y_from find the
    front surface for each cell; cells whose surfaces lie within one depth bucket are merged into rectangles, each a
    quad just in front of the nearest surface under it. UVs follow x and z, so the texture runs on unbroken across
    steps in depth."""
    nx, nz = int(round((x1 - x0) / step)), int(round((z1 - z0) / step))
    grid = []
    for j in range(nz):
        z = z0 + (j + 0.5) * step
        row = []
        for i in range(nx):
            hit = bvh.ray_cast(Vector((x0 + (i + 0.5) * step, y_from, z)), Vector((0, 1, 0)), reach)
            row.append(None if hit[0] is None else hit[0].y)
        grid.append(row)
    key = lambda y: int(math.floor((y + 0.0073) / bucket))   # noqa: E731  (off the cm grid, where walls stand)
    rects, active = [], {}
    for j in range(nz + 1):
        runs = {}
        if j < nz:
            row, i = grid[j], 0
            while i < nx:
                if row[i] is None:
                    i += 1
                    continue
                k, lo = i, row[i]
                while k + 1 < nx and row[k + 1] is not None and key(row[k + 1]) == key(row[i]):
                    k += 1
                    lo = min(lo, row[k])
                runs[(i, k + 1, key(row[i]))] = lo
                i = k + 1
        for rk in list(active):
            if rk not in runs:
                j0, lo = active.pop(rk)
                rects.append((rk, j0, j, lo))
        for rk, lo in runs.items():
            if rk in active:
                active[rk] = (active[rk][0], min(active[rk][1], lo))
            else:
                active[rk] = (j, lo)
    tw, th = TIDE_TEX
    for (i0, i1, _), j0, j1, lo in rects:
        xa, xb = x0 + i0 * step, x0 + i1 * step
        za, zb = z0 + j0 * step, z0 + j1 * step
        y = lo - ahead
        base = len(verts)
        for (x, z) in ((xa, za), (xb, za), (xb, zb), (xa, zb)):
            verts.append((x, y, z))
            uvs.append((x / tw, z / th))
        faces.append((base, base + 1, base + 2, base + 3))
    return len(rects)


def build_tideline(m, coll):
    """Tideline: the flood's mark at TIDE_Z, one water level, laid as a decal over whatever the camera sees below it:
    the street (the back row, the cross alley's foot, the square's fountain and bench and noticeboard), C-108's room
    through its window, C-114's street wall (a child of C114Facade, so it fades with it) and, inside, its walls."""
    from mathutils.bvhtree import BVHTree

    def bvh_of(names):
        bpy.context.view_layer.update()
        bm = bmesh.new()
        for n in names:
            ob = bpy.data.objects.get(n)
            if ob is None:
                continue
            me = ob.data.copy()
            me.transform(ob.matrix_world)
            bm.from_mesh(me)
            bpy.data.meshes.remove(me)
        tree = BVHTree.FromBMesh(bm)
        bm.free()
        return tree
    mat = _imgmat('D5TidelineMat', 'tideline.png', rough=0.85, alpha=True)
    top = TIDE_Z + 0.04

    def decal(name, parts):
        verts, faces, uvs = [], [], []
        n = 0
        for names, x0, x1, z0, z1, y_from in parts:
            n += _project_decal(verts, faces, uvs, bvh_of(names), x0, x1, z0, z1, y_from=y_from)
        me = bpy.data.meshes.new(name)
        me.from_pydata(verts, [], faces)
        uv = me.uv_layers.new(name='UVMap')
        for poly in me.polygons:
            for li in poly.loop_indices:
                uv.data[li].uv = uvs[me.loops[li].vertex_index]
        me.materials.append(mat)
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        print(f'{name}: {n} quads')
        return ob
    street = ['D5Homes', 'D5Square']                       # (from the lane: the front row is in front of where the rays start)
    cw, cww, cz0, _ = C108_WIN
    decal('Tideline', [(street, LANE_C[0], LANE_C[1], 0.0, top, LANE_Y[0] + 0.05), (['D5Home108Room'], cw - cww / 2 + 0.05, cw + cww / 2 - 0.05, cz0, top, 1.15)])
    home = ['C114Interior']
    y_in = CUT_Y + 0.03
    decal('TidelineHome', [(home, X0_114 + 0.18, MARKS[0], 0.0, top, y_in), (home, MARKS[0], MARKS[1], 0.0, MARKS[2], y_in),
                           (home, MARKS[1], BACK_DOOR[0] - 0.06, 0.0, top, y_in)])
    facade = bpy.data.objects['C114Facade']
    ob = decal('TidelineFacade', [(['C114Facade'], X0_114, X1_114, 0.0, top, -3.0)])
    bpy.context.view_layer.update()
    ob.parent = facade
    ob.matrix_parent_inverse = facade.matrix_world.inverted()


def merge_objects(coll, names, new_name):
    """Join finished static objects into one (its materials the union of theirs): one draw call per material."""
    bpy.context.view_layer.update()
    mats, bm = [], bmesh.new()
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob is None or ob.type != 'MESH':
            continue
        assert not ob.children, n
        me = ob.data.copy()
        me.transform(ob.matrix_world)
        remap = []
        for slot in me.materials:
            if slot not in mats:
                mats.append(slot)
            remap.append(mats.index(slot))
        idx = [0] * len(me.polygons)
        me.polygons.foreach_get('material_index', idx)
        me.polygons.foreach_set('material_index', [remap[i] if remap else 0 for i in idx])
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        old = ob.data
        bpy.data.objects.remove(ob)
        if old.users == 0:
            bpy.data.meshes.remove(old)
    me = bpy.data.meshes.new(new_name)
    bm.to_mesh(me)
    bm.free()
    for mt in mats:
        me.materials.append(mt)
    ob = bpy.data.objects.new(new_name, me)
    coll.objects.link(ob)
    return ob


STREET_STATIC = ['D5Lane', 'D5Homes', 'D5LaneFront', 'D5Square', 'D5Overhead', 'D5Railings', 'D5Washing', 'FloodDip', 'D5ScumLine', 'D5Afloat',
                 'D5Letters', 'D5DeadBulbs', 'D5Bicycle', 'D5DrownedShoe', 'D5Home108Room', 'D5Table108', 'D5Mud', 'D5Mud108', 'D5Scum']
HOME_STATIC = ['C114Interior', 'C114Exterior', 'C114HallProps', 'C114Kitchen', 'C114Table', 'C114Sideboard', 'C114Upstairs',
               'ChildBed', 'D5Bedding', 'D5Quilt', 'D5WindowFrame', 'D5Drawing', 'D5DrawingPin', 'D5MobileWire', 'D5MobileStars', 'D5Rug', 'D5RugLiving',
               'D5Shelf', 'D5Cup', 'D5Pencils', 'D5WoodenBird', 'D5PhotoFrame', 'D5Photo', 'D5HallPhoto', 'D5Crayons', 'D5FloorDrawing', 'D5DeskLeg',
               'D5NameCard114Out']


def build_set(dl01, m, coll):
    make_textures()
    dl05_materials(m)
    build_ledge(m, coll)
    build_barricade(m, coll)
    build_street(m, coll)
    build_front_row(m, coll)
    build_lore3(m, coll)
    build_c108_room(m, coll)
    build_c110_letters(m, coll)
    build_flood(m, coll)
    build_duct(m, coll)
    build_mailslot(m, coll)
    build_far(m, coll)
    build_home114(m, coll)
    build_bedroom(m, coll)
    build_terminal(m, coll)
    build_desk(m, coll)
    build_toy(m, coll)
    build_passage(m, coll)
    build_tideline(m, coll)
    merge_objects(coll, STREET_STATIC, 'D5Street')
    merge_objects(coll, HOME_STATIC, 'C114Home')


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
    """At C-114's shut door, facing it: he raises his right claw, knocks twice, waits with his head
    on one side, listening, and lowers it. Nobody comes. The knock lands about 0.3 m ahead of him,
    0.22 m to his right and 0.57 m up (KNOCK_HITS; KNOCK_AT, on the door's lock-side panel)."""
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
