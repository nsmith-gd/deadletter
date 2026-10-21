"""Prologue pass 6 (docs/chapter1_pass6_plan.md): the ending reveal and the prologue's two secret rooms.
Built in FINAL world coordinates (game x = Blender x), after every other set builder; other builders' objects are only
changed here, by name.

The ending (DL-11, out of C-114's back door; replaces dl05's service passage, stair and school sign)
  He forwards the parcel at the terminal and walks out of the back of the house. Out there is a small landing, and from
  it the space opens upward: a tall, dark light-well through the rings above ring C, dark windows, slab edges, a broken
  balcony, pipes. Far above (24 m) one window is lit, the only light in all that dark: a curtain half drawn, a plant on
  the sill, washing on a line. From that window a new cable (glossy black, bright galvanised clips, taped joints: a
  repair, not the refuge's) runs to the well's corner and down the wall, over every slab edge, round onto the landing's
  back wall and into a new splice box bolted beside ring C's old supply box, whose door hangs open: jumpered in, its
  pilot lamp lit. Whoever lives up there turned the power back on, tonight. At the landing's right end an iron stair
  goes up the well's right wall, flight by flight, into the dark: the way on, to ring B (the school's enamel sign is on
  its first post).
    EndWell          the landing, the well's walls, slabs, windows, balconies, pipes, the parapet and its rail, the old
                     supply box and conduits, the new splice box and cable, the stair: one static object
    EndWindowGlow    the lit window's glass (EMIT EndWindowGlow) and its curtain (EMIT EndCurtainGlow)
    EndPilotLamp     the splice box's pilot lamp (EMIT EndPilotLamp)
  Removed by name: D5Passage, D5Stair, D5StairRail, D5Pipes, D5PassageLampCage, LaneBulbPassage; D5FarTiers' faces inside
  the well. D5SchoolSign is moved onto the stair's first post.

Secret room A (DL-06/07 sorting floor): someone who stayed.
  Behind the sorting floor's back wall, a store room a sorter lived on in, alone, after everyone had gone up, reading
  the dead letters for company. A wall panel low in the sorting wall has been pulled off and leant back against the
  wall over half the hole; a warm light from inside, two envelopes dropped by the gap. Inside: a camp cot made up
  with an army blanket, ration tins stacked in a neat pyramid, two mail sacks of unread post, and three walls of opened
  letters pinned in neat rows, the last row on the right wall unfinished. A chair turned to face them, and in it what
  is left of him, a letter in his lap; a bulb he wired from the depot's supply hangs over the chair, and since tonight
  it burns again.
    SecretA          the room, the panel, the cot, tins, sacks, crate table, chair, letters, bulb: one static object
    SecretARemains   him (art/pass6/remains.py, 'seated', folded over the chair's edge)
  SortingWall gets the hole (its wall box is rebuilt round it).

Secret room B (DL-09 tunnel, by the hopscotch): the children's den.
  Behind the tunnel's tiled wall, a forgotten plant room the children made theirs. A vent at floor level beside their
  chalk drawings, its grille off and laid on the floor; Mara's tree chalked small beside it. Inside, warm: a blanket
  fort (a broom across stacked crates, a check blanket over it, a striped one closing its end), cushions and a rag
  rug, a paper lantern lit, tins of small treasures open at its mouth, a doll's tea set on a crate, bunting, books;
  chalk drawings on every wall (Mara's crooked tree with the knot in its branch among them) and a row of chalk-traced
  handprints at child height. Nobody died here; the den was simply left.
    SecretB          the room, grille, fort, crates, tins, tea set, bunting, books, lantern: one static object
    SecretBChalk     the chalk on the den's walls and the little tree outside (SecretChalkMat, alpha: a decal)
  G4TunnelBack and G4TunnelTiles get the vent hole (rebuilt round it).

Textures are drawn here with PIL and packed into the blend (no files written): SecretAtlasMat (1024 x 1024: letter
pages, envelopes, blankets, rug, tins, treasures, bunting, books, sack) and SecretChalkMat (1024 x 1024, alpha).

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y. Game (x, y, z) = (x, z, -y).
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
from build_d17 import add_box, add_cyl, add_sphere, add_torus, rounded_box, worn_material, simple_material, emission_material

HERE = os.path.dirname(os.path.abspath(__file__))

# =====================================================================================================================
# Where things are (Blender world; game x = x, game y = z, game z = -y)
# =====================================================================================================================

# The ending. C-114's back wall's outer face is at 168.56 (dl05 X1_114 + 54); its back door at y +-0.42.
LAND = (168.56, 178.0, -0.95, 1.0)      # the landing: x0, x1, front edge y, back wall face y (the left block)
BLOCK_L = (168.74, 171.6)               # the left block: its front face (y LAND[3]) is the landing's back wall
WELL = (171.6, 178.0, 1.0, 10.3)        # the well's void: x0 (left wall face), x1 (right wall face), y0, y1 (back wall face)
WELL_FLOOR = -5.5                       # the well's bottom, below the landing, lost in the dark
WELL_TOP = 44.0                         # the rock over it
RAIL_Y = 1.22                           # the parapet's rail over the well (x WELL[0]..STAIR_X0)
LEVELS = (5.6, 11.2, 16.8, 22.4, 28.0, 33.6, 39.2)   # the rings' floors, as slab edges in the well's walls
WIN = (173.6, 23.2, 24.75, 1.2)          # the lit window: centre x, sill z, head z, width (on the back wall, y WELL[3])
STAIR_X0 = 174.4                        # the iron stair's foot (flight 1 rises along +x)
STAIR_RISE, STAIR_RUN, STAIR_W = 0.2, 0.28, 0.8
STAIR_Y0 = -0.25                        # flight 1's front edge: it stands on the lane's line (y -0.25..0.55)
STAIR_DOOR = [1.2, 2.05, 5.6]           # ring B's door at the stair's top: y0, y1, sill (set by build_stair)
OLD_BOX = (170.12, 170.58, 1.04, 1.64)  # ring C's old supply box: x0, x1, z0, z1 (on the block's front face)
NEW_BOX = (170.72, 170.98, 1.30, 1.62)  # the new splice box beside it

# Secret room A: behind the sorting floor's back wall (SortingWall: x 63..69.4, y 1.56..1.68, z 0..5).
SORT_WALL = (1.56, 1.68)
HOLE_A = (66.52, 67.22, 0.8)            # the hole: x0, x1, height
ROOM_A = (65.30, 68.70, 1.68, 4.35, 2.45)   # x0, x1, y0 (the wall's back face), y1 (back wall face), ceiling
CHAIR_A = (67.72, 3.35, -72.0)          # x, y, turn (degrees from facing +y, toward -x): he faces the right wall's unfinished row

# Secret room B: behind the tunnel's back wall (G4TunnelBack: x 106.6..112, y 1.37..1.47, z 1.6..4.0; tiles at 1.36).
DECK = 1.6
TUN_WALL = (1.37, 1.47)
HOLE_B = (106.86, 107.48, 0.66)         # the vent: x0, x1, height above the deck
ROOM_B = (106.72, 109.95, 1.47, 4.2, 3.75)  # x0, x1, y0, y1 (back wall face), ceiling z
TUN_FLOOR_Y1 = 1.8                      # G4TunnelFloor runs back to here under the wall

# =====================================================================================================================
# Materials
# =====================================================================================================================

# New materials the game needs entries for (see the report): as index.html's tables.
NEW_PLAIN = {
    'NewCable': ((0.016, 0.016, 0.018), 0.28, 0.0),      # new rubber-sheathed cable: blacker and glossier than 'Cable'
    'NewSteel': ((0.26, 0.27, 0.28), 0.4, 0.8),          # galvanised: the new clips, saddles and splice box
}
NEW_EMIT = {       # name: (colour, strength), as index.html EMIT
    'EndWindowGlow': ((1.0, 0.64, 0.32), 9.0),
    'EndCurtainGlow': ((1.0, 0.42, 0.16), 3.2),
    'EndPilotLamp': ((1.0, 0.6, 0.18), 6.0),
    'SecretLampGlow': ((1.0, 0.78, 0.5), 6.0),
    'DenLanternGlow': ((1.0, 0.55, 0.22), 2.5),
}
# Fallbacks for a lone run (the full build has them all, made by the earlier builders).
FALLBACK_WORN = {
    'Concrete': dict(base=(.075, .074, .07), dirt=(.035, .034, .03), chip=(.12, .115, .105), rough=.92, chip_rough=.9, metallic=0),
    'WallPanel': dict(base=(.09, .095, .09), dirt=(.04, .04, .035), chip=(.14, .13, .11), rough=.9, chip_rough=.85, metallic=0),
    'RingPlasterA': dict(base=(.20, .22, .22), dirt=(.10, .10, .09), chip=(.13, .12, .10), rough=.9, chip_rough=.85, metallic=0),
    'CaveRock': dict(base=(.05, .048, .045), dirt=(.028, .026, .024), chip=(.085, .08, .072), rough=.95, chip_rough=.9, metallic=0),
    'CastIron': dict(base=(.035, .034, .032), dirt=(.05, .03, .018), chip=(.13, .12, .1), rough=.75, chip_rough=.45, metallic=.5),
    'WornIron': dict(base=(.045, .043, .04), dirt=(.06, .035, .02), chip=(.3, .29, .27), rough=.7, chip_rough=.35, metallic=.6),
    'DepotSteel': dict(base=(.05, .052, .05), dirt=(.05, .03, .018), chip=(.16, .15, .13), rough=.6, chip_rough=.4, metallic=.6),
    'CrateWood': dict(base=(.18, .12, .07), dirt=(.08, .055, .035), chip=(.25, .19, .12), rough=.85, chip_rough=.8, metallic=0),
    'PigeonWood': dict(base=(.12, .085, .055), dirt=(.06, .045, .03), chip=(.2, .15, .1), rough=.85, chip_rough=.8, metallic=0),
    'CotCanvas': dict(base=(.16, .15, .10), dirt=(.08, .07, .045), chip=(.2, .19, .15), rough=.95, chip_rough=.95, metallic=0),
    'HomePlaster': dict(base=(.34, .29, .21), dirt=(.17, .14, .10), chip=(.24, .20, .15), rough=.9, chip_rough=.85, metallic=0),
}
FALLBACK_PLAIN = {
    'AtriumDark': ((0.006, 0.006, 0.006), 0.8, 0.0), 'Copper': ((0.55, 0.3, 0.18), 0.35, 1.0),
    'Rubber': ((0.012, 0.012, 0.011), 0.7, 0.0), 'AtriumCloth': ((0.2, 0.13, 0.065), 0.9, 0.0),
    'TeaEnamel': ((0.58, 0.55, 0.47), 0.35, 0.0),
}


def material(name):
    mt = bpy.data.materials.get(name)
    if mt is not None:
        return mt
    if name in NEW_PLAIN:
        c, r, mtl = NEW_PLAIN[name]
        return simple_material(name, c, r, metallic=mtl)
    if name in NEW_EMIT:
        c, s = NEW_EMIT[name]
        return emission_material(name, c, s)
    if name in FALLBACK_WORN:
        return worn_material(name, **FALLBACK_WORN[name])
    if name in FALLBACK_PLAIN:
        c, r, mtl = FALLBACK_PLAIN[name]
        return simple_material(name, c, r, metallic=mtl)
    if name == 'SecretAtlasMat':
        return _image_material(name, atlas_image(), rough=0.85, alpha=False)
    if name == 'SecretChalkMat':
        return _image_material(name, chalk_image(), rough=0.95, alpha=True)
    raise KeyError(name)


def _image_material(name, image, rough=0.8, alpha=False):
    mt, nt, bsdf = d17._new_material(name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = image
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


def _pil_to_image(name, img):
    """A PIL image as a packed Blender image (8-bit sRGB, PNG when exported)."""
    import numpy as np
    img = img.convert('RGBA')
    w, h = img.size
    im = bpy.data.images.get(name)
    if im is not None:
        bpy.data.images.remove(im)
    im = bpy.data.images.new(name, w, h, alpha=True)
    arr = (np.asarray(img, dtype=np.float32) / 255.0)[::-1].ravel()
    im.pixels.foreach_set(arr)
    im.file_format = 'PNG'
    try:
        im.pack()
    except RuntimeError as e:                                  # an older Blender: save it next to the blend's temp files
        path = os.path.join(bpy.app.tempdir or '/tmp', name + '.png')
        im.filepath_raw = path
        im.save()
        print('ending_secrets: could not pack %s (%s); saved %s' % (name, e, path))
    return im


# =====================================================================================================================
# Textures (PIL, drawn at build time)
# =====================================================================================================================

ATLAS = 1024
# Cells of SecretAtlasMat (pixels, y down).
ACELLS = {}
for _k in range(8):
    ACELLS['page%d' % _k] = (_k * 128, 0, _k * 128 + 128, 176)
    ACELLS['env%d' % _k] = (_k * 128, 176, _k * 128 + 128, 272)
for _k, _n in enumerate(('check', 'stripe', 'rug', 'cushion')):
    ACELLS[_n] = (_k * 256, 272, _k * 256 + 256, 528)
for _k, _n in enumerate(('tin0', 'tin1', 'tin2', 'treasure')):
    ACELLS[_n] = (_k * 256, 528, _k * 256 + 256, 720)
for _k, _n in enumerate(('bunting', 'books', 'army', 'sack')):
    ACELLS[_n] = (_k * 256, 720, _k * 256 + 256, 976)
ACELLS['paper'] = (0, 976, 512, 1024)
ACELLS['dark'] = (512, 976, 1024, 1024)
# Cells of SecretChalkMat.
CCELLS = {
    'muralA': (0, 0, 1024, 256),        # the den's back wall, right of the fort: 1.2 x 0.3 per 256 px
    'muralB': (0, 256, 512, 512),       # over the fort
    'hands': (512, 256, 1024, 512),     # the handprints, traced round in chalk
    'tree': (0, 512, 256, 768),         # Mara's tree, small (outside, by the vent)
    'muralC': (256, 512, 1024, 768),    # the right wall
    'muralD': (0, 768, 1024, 1024),     # the left wall, by the way in
}


def cell_uv(cell, cells=None):
    x0, y0, x1, y1 = (cells or ACELLS)[cell]
    return x0 / ATLAS, 1 - y1 / ATLAS, x1 / ATLAS, 1 - y0 / ATLAS


def _grain(w, h, seed, lo=0.6):
    import numpy as np
    rng = np.random.default_rng(seed)
    return lo + (1 - lo) * rng.random((h, w))


def _wavy(d, x0, x1, y, rnd, ink, width=2, amp=1.2):
    pts, x = [], x0
    while x < x1:
        pts.append((x, y + rnd.uniform(-amp, amp) + 1.5 * math.sin(x * 0.7)))
        x += rnd.uniform(3, 6)
    if len(pts) > 1:
        d.line(pts, fill=ink, width=width)


_ATLAS_IMG = [None]
_CHALK_IMG = [None]


def atlas_image():
    if _ATLAS_IMG[0] is not None and _ATLAS_IMG[0].name in bpy.data.images:
        return _ATLAS_IMG[0]
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(6070)
    img = Image.new('RGB', (ATLAS, ATLAS), (60, 56, 50))
    d = ImageDraw.Draw(img, 'RGBA')
    # Letter pages: aged paper, a written hand, fold lines; some ruled, some with a drawing in the corner.
    papers = [(214, 204, 178), (222, 214, 190), (204, 196, 170), (226, 220, 200), (210, 198, 166), (218, 206, 178),
              (198, 192, 172), (224, 210, 180)]
    inks = [(30, 34, 70), (40, 36, 30), (52, 60, 98), (60, 40, 30), (24, 26, 40), (70, 74, 110), (36, 44, 58), (50, 36, 60)]
    for k in range(8):
        x0, y0, x1, y1 = ACELLS['page%d' % k]
        d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=papers[k])
        if k % 3 == 1:
            for y in range(y0 + 22, y1 - 8, 10):
                d.line((x0 + 6, y, x1 - 6, y), fill=(150, 160, 180, 90), width=1)
        ink = inks[k]
        y = y0 + 14
        _wavy(d, x0 + 12, x0 + 60, y, rnd, ink)                      # the greeting
        y += 14
        n = rnd.randint(8, 12)
        for i in range(n):
            xa = x0 + (18 if i == 0 or rnd.random() < 0.15 else 10)
            xb = x1 - rnd.randint(8, 22) if i < n - 1 else x0 + rnd.randint(40, 80)
            _wavy(d, xa, xb, y, rnd, ink)
            y += 11
            if y > y1 - 34:
                break
        _wavy(d, x1 - 60, x1 - 16, y1 - 18, rnd, ink, width=2)          # the name
        for f in (1, 2):                                               # folds
            fy = y0 + (y1 - y0) * f // 3
            d.line((x0, fy, x1, fy), fill=(120, 110, 90, 70), width=2)
        if k in (2, 6):                                                # a child's drawing in the corner: a sun, a house
            d.ellipse((x1 - 34, y0 + 8, x1 - 16, y0 + 26), outline=(200, 140, 40), width=2)
        if k == 5:                                                     # a pressed flower stain
            d.ellipse((x0 + 80, y1 - 50, x0 + 110, y1 - 30), fill=(150, 120, 90, 80))
        for _ in range(30):                                            # foxing
            fx, fy = rnd.randint(x0, x1 - 4), rnd.randint(y0, y1 - 4)
            d.ellipse((fx, fy, fx + rnd.randint(2, 6), fy + rnd.randint(2, 6)), fill=(140, 110, 70, rnd.randint(20, 60)))
    # Envelopes: an address, a stamp, a postmark; some with RETURN struck across.
    for k in range(8):
        x0, y0, x1, y1 = ACELLS['env%d' % k]
        base = (196, 182, 150) if k % 2 else (214, 206, 182)
        d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=base)
        d.rectangle((x1 - 30, y0 + 8, x1 - 10, y0 + 32), fill=[(120, 40, 40), (40, 70, 110), (60, 100, 60), (130, 90, 30)][k % 4])
        d.ellipse((x1 - 50, y0 + 10, x1 - 22, y0 + 38), outline=(40, 40, 40, 150), width=2)
        for i in range(3):
            _wavy(d, x0 + 30, x1 - 30 - i * 6, y0 + 50 + i * 12, rnd, inks[k])
        if k in (1, 4, 7):
            d.rectangle((x0 + 18, y0 + 40, x1 - 18, y0 + 62), outline=(110, 30, 26, 180), width=3)
        d.line((x0, y0, (x0 + x1) // 2, y0 + 40, x1, y0), fill=(150, 140, 110), width=2)
    # Blankets and cloth.
    x0, y0, x1, y1 = ACELLS['check']
    d.rectangle((x0, y0, x1, y1), fill=(150, 46, 36))
    for i in range(0, 256, 32):
        d.rectangle((x0 + i, y0, x0 + i + 12, y1), fill=(222, 206, 170, 150))
        d.rectangle((x0, y0 + i, x1, y0 + i + 12), fill=(222, 206, 170, 150))
        d.rectangle((x0 + i + 20, y0, x0 + i + 23, y1), fill=(40, 40, 60, 160))
    x0, y0, x1, y1 = ACELLS['stripe']
    d.rectangle((x0, y0, x1, y1), fill=(70, 96, 140))
    for i, c in enumerate([(210, 200, 170), (70, 96, 140), (196, 150, 60), (70, 96, 140), (210, 200, 170), (40, 56, 90)] * 3):
        d.rectangle((x0, y0 + i * 15, x1, y0 + i * 15 + 7), fill=c)
    x0, y0, x1, y1 = ACELLS['rug']
    cols = [(150, 60, 50), (210, 170, 90), (80, 110, 150), (190, 120, 120), (100, 130, 90), (220, 200, 170), (170, 90, 50)]
    for i in range(14):
        m = i * 9
        d.ellipse((x0 + m, y0 + m, x1 - m, y1 - m), fill=cols[i % len(cols)])
    x0, y0, x1, y1 = ACELLS['cushion']
    for i in range(4):
        for j in range(4):
            c = [(190, 110, 90), (226, 200, 140), (110, 140, 170), (170, 190, 120), (210, 150, 170)][(i * 3 + j) % 5]
            d.rectangle((x0 + i * 64, y0 + j * 64, x0 + i * 64 + 63, y0 + j * 64 + 63), fill=c)
            d.ellipse((x0 + i * 64 + 20, y0 + j * 64 + 20, x0 + i * 64 + 44, y0 + j * 64 + 44), fill=(250, 240, 220, 120))
    # Tins: a biscuit tin, a cocoa tin, a toffee tin (sides wrap along u).
    for k, (a, b) in enumerate((((160, 40, 40), (230, 200, 120)), ((40, 70, 130), (240, 220, 180)), ((50, 110, 70), (230, 190, 60)))):
        x0, y0, x1, y1 = ACELLS['tin%d' % k]
        d.rectangle((x0, y0, x1, y1), fill=a)
        d.rectangle((x0, y0 + 60, x1, y0 + 130), fill=b)
        for i in range(6):
            cx = x0 + 20 + i * 42
            if k == 0:
                d.ellipse((cx - 12, y0 + 80, cx + 12, y0 + 104), fill=a)
            elif k == 1:
                d.polygon([(cx, y0 + 74), (cx + 8, y0 + 92), (cx + 22, y0 + 92), (cx + 11, y0 + 103), (cx + 16, y0 + 120),
                           (cx, y0 + 110), (cx - 16, y0 + 120), (cx - 11, y0 + 103), (cx - 22, y0 + 92), (cx - 8, y0 + 92)], fill=a)
            else:
                d.rectangle((cx - 10, y0 + 84, cx + 10, y0 + 104), fill=(120, 40, 60))
        d.rectangle((x0, y0 + 8, x1, y0 + 14), fill=(200, 170, 80))
        d.rectangle((x0, y1 - 14, x1, y1 - 8), fill=(200, 170, 80))
    x0, y0, x1, y1 = ACELLS['treasure']                         # buttons, marbles, a key, a shell, bottle caps, a feather
    d.rectangle((x0, y0, x1, y1), fill=(70, 50, 40))
    for _ in range(70):
        cx, cy, r = rnd.randint(x0 + 8, x1 - 8), rnd.randint(y0 + 8, y1 - 8), rnd.randint(5, 11)
        c = rnd.choice([(200, 60, 50), (60, 120, 200), (230, 200, 80), (240, 240, 230), (90, 170, 100), (190, 120, 200),
                        (180, 180, 190), (220, 150, 60)])
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c)
        if rnd.random() < 0.4:
            d.ellipse((cx - r // 3, cy - r // 3, cx, cy), fill=(255, 255, 255, 140))
    d.line((x0 + 40, y0 + 60, x0 + 110, y0 + 60), fill=(200, 170, 70), width=7)      # a key
    d.ellipse((x0 + 20, y0 + 46, x0 + 50, y0 + 74), outline=(200, 170, 70), width=6)
    d.pieslice((x0 + 150, y0 + 100, x0 + 210, y0 + 160), 180, 360, fill=(236, 210, 190))   # a shell
    # Bunting (four colour bands), books (spines), the army blanket, the mail sack.
    x0, y0, x1, y1 = ACELLS['bunting']
    for i, c in enumerate([(200, 70, 60), (230, 190, 80), (80, 130, 190), (110, 170, 100)]):
        d.rectangle((x0 + i * 64, y0, x0 + i * 64 + 63, y1), fill=c)
    x0, y0, x1, y1 = ACELLS['books']
    x = x0
    while x < x1:
        w = rnd.randint(14, 30)
        c = rnd.choice([(120, 40, 40), (40, 70, 110), (70, 90, 50), (150, 110, 50), (90, 60, 90), (180, 160, 120)])
        d.rectangle((x, y0, x + w - 2, y1), fill=c)
        d.rectangle((x + 3, y0 + 40, x + w - 5, y0 + 46), fill=(220, 200, 140))
        x += w
    x0, y0, x1, y1 = ACELLS['army']
    d.rectangle((x0, y0, x1, y1), fill=(62, 66, 52))
    for yy in (y0 + 40, y0 + 200):
        d.rectangle((x0, yy, x1, yy + 10), fill=(30, 32, 28))
    x0, y0, x1, y1 = ACELLS['sack']
    d.rectangle((x0, y0, x1, y1), fill=(120, 112, 92))
    for i in range(0, 256, 6):
        d.line((x0 + i, y0, x0 + i, y1), fill=(100, 92, 74, 90))
    d.line((x0, y0 + 128, x1, y0 + 128), fill=(90, 84, 66), width=4)
    x0, y0, x1, y1 = ACELLS['paper']
    d.rectangle((x0, y0, x1, y1), fill=(196, 170, 120))
    x0, y0, x1, y1 = ACELLS['dark']
    d.rectangle((x0, y0, x1, y1), fill=(18, 16, 14))
    img = img.filter(ImageFilter.GaussianBlur(0.5))
    _ATLAS_IMG[0] = _pil_to_image('SecretAtlas', img)
    return _ATLAS_IMG[0]


def chalk_image():
    """The children's chalk: drawings, traced hands, Mara's tree (transparent, chalk-grained)."""
    if _CHALK_IMG[0] is not None and _CHALK_IMG[0].name in bpy.data.images:
        return _CHALK_IMG[0]
    import numpy as np
    from PIL import Image, ImageDraw
    import handwriting as hw
    import build_dl05 as dl05
    rnd = random.Random(909)
    img = Image.new('RGBA', (ATLAS, ATLAS), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    WHITE, PINK, YEL, BLUE, GREEN, ORANGE = (236, 232, 220, 255), (236, 160, 176, 255), (240, 214, 110, 255), (140, 180, 236, 255), \
        (150, 210, 140, 255), (240, 160, 90, 255)

    def chalk(pts, col, w=5):
        hw.crayon(d, pts, col, width=w, passes=2, jitter=1.4, rnd=rnd)

    def circle(cx, cy, r, col, w=5, ry=None):
        hw.crayon_circle(d, cx, cy, r, col, width=w, rnd=rnd, ry=ry)

    def mara(ox, oy, s, col=WHITE, w=6):
        def stroke(pts, k):
            chalk(pts, col, max(2, int(w * k + 0.5)))
        dl05._crooked_tree(stroke, ox, oy, s)

    def house(x, y, s, col):
        chalk([(x, y), (x, y - s), (x + s * 0.5, y - s * 1.5), (x + s, y - s), (x + s, y), (x, y)], col)
        chalk([(x + s * 0.4, y), (x + s * 0.4, y - s * 0.5), (x + s * 0.65, y - s * 0.5), (x + s * 0.65, y)], col, 4)

    def person(x, y, s, col, arm=None):
        circle(x, y - s * 0.85, s * 0.13, col, 4)
        chalk([(x, y - s * 0.72), (x, y - s * 0.3)], col, 4)
        chalk([(x - s * 0.2, y), (x, y - s * 0.3), (x + s * 0.2, y)], col, 4)
        chalk([(x - s * 0.25, y - s * 0.62), (x, y - s * 0.55), (x + s * 0.25, y - (arm if arm is not None else s * 0.62))], col, 4)

    def sun(cx, cy, r, col):
        circle(cx, cy, r, col, 6)
        for k in range(10):
            a = k * math.pi / 5
            chalk([(cx + math.cos(a) * r * 1.3, cy + math.sin(a) * r * 1.3), (cx + math.cos(a) * r * 1.8, cy + math.sin(a) * r * 1.8)], col, 5)

    def star(cx, cy, r, col):
        pts = []
        for k in range(11):
            a = -math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else r * 0.45
            pts.append((cx + math.cos(a) * rr, cy + math.sin(a) * rr))
        chalk(pts, col, 4)

    def hand(cx, cy, s, ang, col):
        """A hand traced round in chalk: the palm and five fingers, the thumb out."""
        pts = []
        fingers = [(-0.55, 0.62, 0.17), (-0.2, 0.95, 0.15), (0.1, 1.0, 0.15), (0.36, 0.9, 0.14), (0.58, 0.68, 0.12)]
        base = []
        for k, (fx, fy, fw) in enumerate(fingers):
            a0 = math.atan2(fy, fx)
            tip = (fx * 1.0, fy)
            root = (fx * 0.45, 0.35 if k else 0.15)
            base += [(root[0] - fw / 2, root[1]), (tip[0] - fw / 2, tip[1] - 0.06), (tip[0], tip[1] + 0.04),
                     (tip[0] + fw / 2, tip[1] - 0.06), (root[0] + fw / 2, root[1])]
        palm = [(0.5, 0.2), (0.48, -0.25), (0.25, -0.5), (-0.25, -0.5), (-0.5, -0.2), (-0.62, 0.2)]
        outline = base + palm + [base[0]]
        ca, sa = math.cos(ang), math.sin(ang)
        pts = [(cx + (px * ca - py * sa) * s, cy - (px * sa + py * ca) * s) for px, py in outline]
        chalk(pts, col, 4)

    # muralA: a row of houses and the family; a dog; the sun; a ladder up to a star; the tree with the knot.
    x0, y0, x1, y1 = CCELLS['muralA']
    sun(x0 + 90, y0 + 70, 32, YEL)
    house(x0 + 170, y0 + 220, 70, PINK)
    house(x0 + 260, y0 + 220, 60, BLUE)
    person(x0 + 360, y0 + 236, 110, WHITE)
    person(x0 + 410, y0 + 236, 80, PINK, arm=50)
    person(x0 + 450, y0 + 236, 60, YEL)
    chalk([(x0 + 500, y0 + 236), (x0 + 520, y0 + 210), (x0 + 560, y0 + 210), (x0 + 580, y0 + 236)], ORANGE)   # the dog
    circle(x0 + 590, y0 + 200, 12, ORANGE, 4)
    chalk([(x0 + 520, y0 + 236), (x0 + 518, y0 + 248)], ORANGE, 4)
    chalk([(x0 + 570, y0 + 236), (x0 + 572, y0 + 248)], ORANGE, 4)
    for k in range(8):                                                   # a ladder up to a star: going up
        chalk([(x0 + 660, y0 + 246 - k * 26), (x0 + 700, y0 + 246 - k * 26)], WHITE, 4)
    chalk([(x0 + 655, y0 + 250), (x0 + 670, y0 + 40)], WHITE, 4)
    chalk([(x0 + 705, y0 + 250), (x0 + 690, y0 + 40)], WHITE, 4)
    star(x0 + 682, y0 + 24, 20, YEL)
    mara(x0 + 860, y0 + 246, 230, GREEN, 8)
    # muralB: stars and a moon over the fort, a rocket, a bird.
    x0, y0, x1, y1 = CCELLS['muralB']
    for _ in range(9):
        star(x0 + rnd.randint(30, 480), y0 + rnd.randint(30, 220), rnd.randint(10, 20), rnd.choice([YEL, WHITE, BLUE]))
    circle(x0 + 420, y0 + 80, 40, WHITE, 5)
    chalk([(x0 + 120, y0 + 220), (x0 + 120, y0 + 120), (x0 + 145, y0 + 80), (x0 + 170, y0 + 120), (x0 + 170, y0 + 220), (x0 + 120, y0 + 220)], PINK)
    chalk([(x0 + 120, y0 + 220), (x0 + 100, y0 + 245)], PINK)
    chalk([(x0 + 170, y0 + 220), (x0 + 190, y0 + 245)], PINK)
    circle(x0 + 145, y0 + 150, 10, BLUE, 4)
    chalk([(x0 + 260, y0 + 160), (x0 + 280, y0 + 145), (x0 + 300, y0 + 160), (x0 + 320, y0 + 145), (x0 + 340, y0 + 160)], WHITE, 4)
    # hands: six traced hands, small to big, all colours, one with a smaller one inside it.
    x0, y0, x1, y1 = CCELLS['hands']
    for k, (s, col) in enumerate(((52, PINK), (66, WHITE), (44, YEL), (70, BLUE), (58, GREEN), (40, ORANGE))):
        cx = x0 + 50 + k * 80
        cy = y0 + 150 + rnd.randint(-30, 30)
        hand(cx, cy, s, rnd.uniform(-0.25, 0.25), col)
    hand(x0 + 290, y0 + 160, 36, 0.1, PINK)
    # tree: Mara's mark, small, white.
    x0, y0, x1, y1 = CCELLS['tree']
    mara(x0 + 128, y0 + 236, 210, WHITE, 7)
    # muralC: the right wall: a big sun, a train of boxes (the post!), houses with smoke, a girl with a kite.
    x0, y0, x1, y1 = CCELLS['muralC']
    sun(x0 + 650, y0 + 70, 40, ORANGE)
    for k in range(4):
        bx = x0 + 60 + k * 90
        chalk([(bx, y0 + 200), (bx, y0 + 150), (bx + 70, y0 + 150), (bx + 70, y0 + 200), (bx, y0 + 200)], [BLUE, YEL, PINK, GREEN][k])
        circle(bx + 18, y0 + 210, 10, WHITE, 4)
        circle(bx + 52, y0 + 210, 10, WHITE, 4)
    person(x0 + 520, y0 + 240, 120, PINK, arm=100)
    chalk([(x0 + 545, y0 + 140), (x0 + 600, y0 + 40)], WHITE, 3)
    chalk([(x0 + 600, y0 + 40), (x0 + 620, y0 + 10), (x0 + 640, y0 + 40), (x0 + 620, y0 + 70), (x0 + 600, y0 + 40)], YEL, 5)
    house(x0 + 660, y0 + 240, 70, WHITE)
    chalk([(x0 + 700, y0 + 120), (x0 + 690, y0 + 90), (x0 + 705, y0 + 60), (x0 + 690, y0 + 30)], WHITE, 3)
    # muralD: the left wall: tally of a game (dots), a big flower, a cat, kisses.
    x0, y0, x1, y1 = CCELLS['muralD']
    for k in range(6):
        a = k * math.pi / 3
        circle(x0 + 120 + math.cos(a) * 30, y0 + 100 + math.sin(a) * 30, 18, PINK, 4)
    circle(x0 + 120, y0 + 100, 14, YEL, 5)
    chalk([(x0 + 120, y0 + 130), (x0 + 125, y0 + 240)], GREEN, 5)
    circle(x0 + 320, y0 + 190, 40, WHITE, 5, ry=30)                       # a cat
    circle(x0 + 290, y0 + 140, 22, WHITE, 5)
    chalk([(x0 + 275, y0 + 128), (x0 + 278, y0 + 108), (x0 + 288, y0 + 122)], WHITE, 4)
    chalk([(x0 + 298, y0 + 122), (x0 + 306, y0 + 108), (x0 + 307, y0 + 128)], WHITE, 4)
    chalk([(x0 + 360, y0 + 200), (x0 + 400, y0 + 160), (x0 + 390, y0 + 130)], WHITE, 4)
    for k in range(5):
        cx = x0 + 480 + k * 60
        chalk([(cx - 12, y0 + 120), (cx + 12, y0 + 150)], PINK, 4)
        chalk([(cx + 12, y0 + 120), (cx - 12, y0 + 150)], PINK, 4)
    star(x0 + 850, y0 + 120, 40, YEL)
    mara(x0 + 960, y0 + 240, 120, WHITE, 5)
    # Chalk grain: the strokes are dusty, not solid.
    a = np.asarray(img).astype(np.float32)
    a[..., 3] *= _grain(ATLAS, ATLAS, 77, lo=0.45) * 0.92
    img = Image.fromarray(a.clip(0, 255).astype('uint8'), 'RGBA')
    _CHALK_IMG[0] = _pil_to_image('SecretChalk', img)
    return _CHALK_IMG[0]


# =====================================================================================================================
# Geometry helpers
# =====================================================================================================================

class Batch:
    """One bmesh (with a UV layer) and its material list: everything static of one set piece, merged."""
    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.mats = []

    def __call__(self, name):
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def box(self, x, y, z, mat, rot=None):
        """A box from (min, max) ranges."""
        return add_box(self.bm, ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2),
                       (x[1] - x[0], y[1] - y[0], z[1] - z[0]), mat=self(mat), rot=rot)

    def quad(self, pts, mat, uv=None):
        """A quad, wound as given (its face is (p1 - p0) x (p2 - p1)); uv: (u0, v0, u1, v1) over its corners."""
        f = self.bm.faces.new([self.bm.verts.new(Vector(p)) for p in pts])
        f.material_index = self(mat)
        if uv:
            u0, v0, u1, v1 = uv
            for lp, (a, b) in zip(f.loops, ((u0, v0), (u1, v0), (u1, v1), (u0, v1))):
                lp[self.uv].uv = (a, b)
        return f

    def painted(self, mat, cell, build, size=0.3, cells=None):
        """build(bm) adds closed geometry (mat index 0); its faces are box-projected into the atlas cell."""
        tmp = bmesh.new()
        tuv = tmp.loops.layers.uv.new('UVMap')
        build(tmp)
        u0, v0, u1, v1 = cell_uv(cell, cells)
        mu, mv = (u1 - u0) * 0.04, (v1 - v0) * 0.04
        for f in tmp.faces:
            f.normal_update()
            n = f.normal
            ax = max(range(3), key=lambda k: abs(n[k]))
            i, j = [(1, 2), (0, 2), (0, 1)][ax]
            for lp in f.loops:
                p = lp.vert.co
                a = (p[i] / size) % 1.0
                b = (p[j] / size) % 1.0
                lp[tuv].uv = (u0 + mu + (u1 - u0 - 2 * mu) * a, v0 + mv + (v1 - v0 - 2 * mv) * b)
            f.material_index = self(mat)
        self._merge(tmp)

    def _merge(self, tmp):
        me = bpy.data.meshes.new('_es_tmp')
        tmp.to_mesh(me)
        tmp.free()
        self.bm.from_mesh(me)
        bpy.data.meshes.remove(me)

    def done(self, name, coll, sharp=35):
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for n in self.mats:
            me.materials.append(material(n))
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        me.set_sharp_from_angle(angle=math.radians(sharp))
        ob = bpy.data.objects.new(name, me)
        coll.objects.link(ob)
        return ob


def tube(B, pts, r, mat, seg=6):
    """A tube along pts (no caps)."""
    import build_ration_hall as rh
    tmp = bmesh.new()
    rh.sweep(tmp, [Vector(p) for p in pts], r, seg=seg, caps=True)
    for f in tmp.faces:
        f.material_index = B(mat)
    B._merge(tmp)


def M_at(x, y, z, turn=0.0):
    return Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(turn), 4, 'Z')


def xform(verts, M):
    for v in verts:
        v.co = M @ v.co
    return verts


def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def remove(names):
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob is not None:
            bpy.data.objects.remove(ob, do_unlink=True)


def edit_world(ob, fn):
    """fn(bm, M) on the object's mesh, with M its world matrix (geometry added by fn is in world space and is moved
    into the object's space afterwards: return the list of new verts)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    M = ob.matrix_world.copy()
    new = fn(bm, M) or []
    inv = M.inverted()
    for v in new:
        v.co = inv @ v.co
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def wall_with_hole(bm, x, y, z, hole, mat):
    """Rebuild a wall box x (x0, x1), y (y0, y1), z (z0, z1) with a rectangular hole (hx0, hx1, hz1) at its foot."""
    hx0, hx1, hz1 = hole
    new = []
    for xx, zz in (((x[0], hx0), z), ((hx1, x[1]), z), ((hx0, hx1), (hz1, z[1]))):
        new += add_box(bm, ((xx[0] + xx[1]) / 2, (y[0] + y[1]) / 2, (zz[0] + zz[1]) / 2),
                       (xx[1] - xx[0], y[1] - y[0], zz[1] - zz[0]), mat=mat)
    return new


# =====================================================================================================================
# The ending: the landing and the light-well
# =====================================================================================================================

def clear_passage():
    remove(('D5Passage', 'D5Stair', 'D5StairRail', 'D5Pipes', 'D5PassageLampCage', 'LaneBulbPassage'))
    ft = bpy.data.objects.get('D5FarTiers')
    if ft is not None:
        def cut(bm, M):
            gone = []
            for f in bm.faces:
                c = M @ f.calc_center_median()
                if c.x > BLOCK_L[0] + 0.02 and c.y > LAND[3] - 0.05:
                    gone.append(f)
            bmesh.ops.delete(bm, geom=gone, context='FACES')
            print('ending: D5FarTiers: %d faces cut out of the well' % len(gone))
        edit_world(ft, cut)


def _floor_hits(x0, x1, y0, y1, step=0.25):
    """Where the existing set already has a floor at z ~0 under this rectangle (cells of `step`)."""
    dg = bpy.context.evaluated_depsgraph_get()
    hits = set()
    nx, ny = int(round((x1 - x0) / step)), int(round((y1 - y0) / step))
    for i in range(nx):
        for j in range(ny):
            p = Vector((x0 + (i + 0.5) * step, y0 + (j + 0.5) * step, 1.0))
            hit, loc, nrm, idx, ob, mtx = bpy.context.scene.ray_cast(dg, p, Vector((0, 0, -1)), distance=1.2)
            if hit and abs(loc.z) < 0.03 and not ob.name.startswith('End'):
                hits.add((i, j))
    return hits, nx, ny


def build_landing(B):
    x0, x1, yf, yb = LAND
    # The floor: only where the street's own floor does not already run (no doubled faces).
    FY0 = yf
    hits, nx, ny = _floor_hits(x0, x1, FY0, WELL[2] + 0.3)
    print('ending: existing floor cells under the landing: %d of %d' % (len(hits), nx * ny))
    dg = bpy.context.evaluated_depsgraph_get()
    for xx in (169.0, 171.0, 173.0, 175.0, 176.5):
        row = []
        for yy in (-3.0, -2.0, -1.2, -0.9, -0.5, 0.0, 0.5, 0.9, 1.1):
            hit, loc, nrm, idx, ob, mtx = bpy.context.scene.ray_cast(dg, Vector((xx, yy, 3.0)), Vector((0, 0, -1)), distance=8)
            row.append('%.1f:%s' % (yy, ('%s@%.2f' % (ob.name[:10], loc.z)) if hit else '-'))
        print('ending: floor x %.1f  %s' % (xx, ' '.join(row)))
    step = 0.25
    for i in range(nx):
        run = [j for j in range(ny) if (i, j) not in hits]
        if not run:
            continue
        # merge contiguous j runs
        start = prev = run[0]
        for j in run[1:] + [None]:
            if j is not None and j == prev + 1:
                prev = j
                continue
            B.box((x0 + i * step, x0 + (i + 1) * step), (FY0 + start * step, FY0 + (prev + 1) * step), (-0.35, 0.0), 'Concrete')
            if j is not None:
                start = prev = j
    # The street's kerb runs on to the end wall (dl05's stops at 174.9), and the slab's edge goes down into the dark.
    B.box((174.9, x1), (-0.99, -0.85), (0.0, 0.16), 'Concrete')
    B.box((x0, x1), (yf, yf + 0.35), (-2.8, -0.35), 'Concrete')
    # The parapet over the well: a low concrete upstand and an iron rail on posts (behind the lane).
    B.box((WELL[0], STAIR_X0 + 10 * STAIR_RUN), (RAIL_Y - 0.06, RAIL_Y + 0.1), (-0.35, 0.22), 'Concrete')
    x = WELL[0] + 0.15
    while x < STAIR_X0 + 10 * STAIR_RUN:
        add_cyl(B.bm, (x, RAIL_Y + 0.02, 0.22), (x, RAIL_Y + 0.02, 0.96), 0.018, seg=6, mat=B('WornIron'))
        x += 0.9
    add_cyl(B.bm, (WELL[0] + 0.02, RAIL_Y + 0.02, 0.96), (STAIR_X0 + 10 * STAIR_RUN, RAIL_Y + 0.02, 0.96), 0.022, seg=8, mat=B('WornIron'))
    add_cyl(B.bm, (WELL[0] + 0.02, RAIL_Y + 0.02, 0.6), (STAIR_X0 + 10 * STAIR_RUN, RAIL_Y + 0.02, 0.6), 0.012, seg=6, mat=B('WornIron'))
    # A slab end under the landing seen from the well, and the well's bottom: rubble in a dark sump.
    B.box((WELL[0], WELL[1]), (WELL[2] + 0.3, WELL[3]), (WELL_FLOOR - 0.3, WELL_FLOOR), 'Concrete')
    rnd = random.Random(171)
    for _ in range(14):
        c = (rnd.uniform(WELL[0] + 0.4, WELL[1] - 0.4), rnd.uniform(WELL[2] + 0.8, WELL[3] - 0.4), WELL_FLOOR + 0.1)
        B.box((c[0] - 0.3, c[0] + 0.3), (c[1] - 0.25, c[1] + 0.25), (WELL_FLOOR, WELL_FLOOR + rnd.uniform(0.1, 0.5)), 'Concrete',
              rot=None)


def build_well(B):
    """The left block (the landing's back wall) and the well's walls, the rings' slab edges, windows, balconies, pipes."""
    rnd = random.Random(1170)
    lx0, lx1 = BLOCK_L
    wx0, wx1, wy0, wy1 = WELL
    yb = LAND[3]
    T = 0.4                                                    # wall thickness
    # The left block: its face on the landing (panelled, like the old passage) and its face into the well.
    B.box((lx0, lx1), (yb, wy1 + T), (-0.35, 3.6), 'RingPlasterA')
    B.box((lx0, lx1), (yb, wy1 + T), (3.6, WELL_TOP), 'RingPlasterA')
    B.box((lx0 - 0.02, lx1 + 0.02), (yb - 0.04, yb + 0.02), (3.52, 3.68), 'Concrete')         # a band over the landing
    # The right block (the landing's end and the well's right wall), the back wall, the bottom of the well's walls.
    B.box((wx1, wx1 + T + 2.0), (LAND[2] - 0.1, wy1 + T), (WELL_FLOOR - 0.3, 3.6), 'RingPlasterA')
    B.box((wx1, wx1 + T + 2.0), (LAND[2] - 0.1, wy1 + T), (3.6, WELL_TOP), 'RingPlasterA')
    B.box((wx0, wx1), (wy1, wy1 + T), (WELL_FLOOR - 0.3, WELL_TOP), 'RingPlasterA')
    B.box((lx0, lx1), (yb, wy1 + T), (WELL_FLOOR - 0.3, -0.35), 'Concrete')
    B.box((lx0 - 0.3, wx1 + T + 2.0), (LAND[2] - 1.0, wy1 + T + 1.0), (WELL_TOP, WELL_TOP + 1.5), 'Concrete')      # the rock over all
    # Over the landing the well goes up too, closed on the camera's side above what the side view sees (from 3.8 m), and on
    # the left over C-114's roof: from the landing it is a shaft all round.
    B.box((lx0 - 0.3, wx1 + T + 2.0), (LAND[2] - 0.75, LAND[2] - 0.35), (3.8, WELL_TOP), 'RingPlasterA')
    B.box((lx0 - 0.3, lx0), (LAND[2] - 0.35, yb), (3.6, WELL_TOP), 'RingPlasterA')
    B.box((lx0 - 0.3, wx1), (LAND[2] - 0.35, LAND[2] - 0.13), (3.62, 3.8), 'Concrete')        # its lintel over the landing
    # Under the landing, its slab end facing the well.
    B.box((wx0, wx1), (RAIL_Y - 0.06, RAIL_Y + 0.1), (WELL_FLOOR, -0.35), 'Concrete')

    # Each ring's floor: a slab edge round the three walls; windows and doors above it, every one dark.
    walls = (('L', wx0), ('B', wy1), ('R', wx1))

    def on_wall(w, u, z, dn, size):
        """A box on wall w at u along it (y for the side walls, x for the back), height z, standing dn out of it."""
        sx, sz, sd = size
        if w == 'L':
            return (wx0 + dn - sd / 2, wx0 + dn + sd / 2), (u - sx / 2, u + sx / 2), (z - sz / 2, z + sz / 2)
        if w == 'R':
            return (wx1 - dn - sd / 2, wx1 - dn + sd / 2), (u - sx / 2, u + sx / 2), (z - sz / 2, z + sz / 2)
        return (u - sx / 2, u + sx / 2), (wy1 - dn - sd / 2, wy1 - dn + sd / 2), (z - sz / 2, z + sz / 2)

    def opening(w, u, z0, z1, width):
        """A dark opening (a quad just off the wall) with a sill and a lintel."""
        e = 0.006
        if w == 'L':                                           # faces +x: u (y) increasing
            B.quad([(wx0 + e, u - width / 2, z0), (wx0 + e, u + width / 2, z0), (wx0 + e, u + width / 2, z1), (wx0 + e, u - width / 2, z1)],
                   'AtriumDark')
        elif w == 'R':                                         # faces -x: u (y) decreasing
            B.quad([(wx1 - e, u + width / 2, z0), (wx1 - e, u - width / 2, z0), (wx1 - e, u - width / 2, z1), (wx1 - e, u + width / 2, z1)],
                   'AtriumDark')
        else:
            B.quad([(u - width / 2, wy1 - e, z0), (u + width / 2, wy1 - e, z0), (u + width / 2, wy1 - e, z1), (u - width / 2, wy1 - e, z1)],
                   'AtriumDark')
        x, y, z = on_wall(w, u, z0 - 0.04, 0.05, (width + 0.12, 0.08, 0.1))
        B.box(x, y, z, 'Concrete')
        x, y, z = on_wall(w, u, z1 + 0.05, 0.03, (width + 0.1, 0.1, 0.06))
        B.box(x, y, z, 'Concrete')

    for li, zl in enumerate(LEVELS):
        # the slab edge: a band standing 0.22 out of each wall
        B.box((wx0, wx0 + 0.22), (wy0 + 0.2, wy1), (zl - 0.3, zl + 0.05), 'Concrete')
        B.box((wx1 - 0.22, wx1), (wy0 - 1.95, wy1), (zl - 0.3, zl + 0.05), 'Concrete')
        B.box((wx0, wx1), (wy1 - 0.22, wy1), (zl - 0.3, zl + 0.05), 'Concrete')
        for w, _ in walls:
            span = (wy0 + 0.6, wy1 - 0.6) if w != 'B' else (wx0 + 0.6, wx1 - 0.6)
            n = 3 if w != 'B' else 3
            for k in range(n):
                u = span[0] + (span[1] - span[0]) * (k + 0.5) / n + rnd.uniform(-0.25, 0.25)
                if w == 'B' and abs(zl - 22.4) < 0.1 and abs(u - WIN[0]) < 1.4:
                    continue                                   # the lit window's own wall
                if w == 'R' and zl < 7 and u < 3.0:
                    continue                                   # the stair's top: its own door (below)
                tall = rnd.random() < 0.25
                z0 = zl + (0.15 if tall else 0.95)
                opening(w, u, z0, zl + 2.15, 0.8 if not tall else 0.9)
                if rnd.random() < 0.2:                         # a shutter hanging from one hinge
                    x, y, z = on_wall(w, u + 0.5, (z0 + zl + 2.15) / 2 - 0.15, 0.12, (0.42, 1.0, 0.03))
                    B.box(x, y, z, 'WornIron', rot=None)
        # A walkway along one wall at some levels (iron, on brackets); one broken off and hanging.
        if li in (1, 3):
            y0g, y1g = wy0 + 1.0, wy1 - 0.25
            B.box((wx0 + 0.22, wx0 + 0.95), (y0g, y1g), (zl - 0.02, zl + 0.04), 'WornIron')
            yy = y0g
            while yy <= y1g:
                add_cyl(B.bm, (wx0 + 0.95, yy, zl + 0.04), (wx0 + 0.95, yy, zl + 1.0), 0.015, seg=5, mat=B('WornIron'))
                add_cyl(B.bm, (wx0 + 0.22, yy, zl - 0.6), (wx0 + 0.9, yy, zl - 0.03), 0.018, seg=5, mat=B('WornIron'))
                yy += 1.2
            add_cyl(B.bm, (wx0 + 0.95, y0g, zl + 1.0), (wx0 + 0.95, y1g, zl + 1.0), 0.02, seg=6, mat=B('WornIron'))
        if li == 2:                                            # the right wall's walkway, broken, its end hanging down
            B.box((wx1 - 0.95, wx1 - 0.22), (wy0 + 4.0, wy1 - 0.25), (zl - 0.02, zl + 0.04), 'WornIron')
            p = Matrix.Translation((wx1 - 0.6, wy0 + 4.0, zl)) @ Matrix.Rotation(math.radians(58), 4, 'X')
            xform(B.box((-0.37, 0.37), (-2.4, 0.0), (-0.02, 0.04), 'WornIron'), p)
            xform(B.box((-0.38, -0.34), (-2.4, 0.0), (0.04, 0.9), 'WornIron'), p)
    # Pipes: two downpipes in the back corners, a fat main across the well, a duct.
    for x in (wx0 + 0.3, wx1 - 0.3):
        add_cyl(B.bm, (x, wy1 - 0.25, WELL_FLOOR), (x, wy1 - 0.25, WELL_TOP), 0.07, seg=8, mat=B('DepotSteel'))
    add_cyl(B.bm, (wx0, wy1 - 1.2, 26.2), (wx1, wy1 - 1.4, 26.4), 0.11, seg=10, mat=B('DepotSteel'))
    add_cyl(B.bm, (wx0, 4.4, 14.6), (wx1, 4.9, 14.4), 0.07, seg=8, mat=B('DepotSteel'))
    B.box((wx0, wx1), (wy1 - 0.75, wy1 - 0.25), (31.0, 31.5), 'DepotSteel')


def build_window(B, coll):
    """The lit window (EndWindowGlow, its own object) and what is round it: frame, sill, plant, balcony, washing."""
    cx, z0, z1, w = WIN
    y = WELL[3]
    # The glass and the curtain: their own object, so the game can set the glow.
    G = Batch()
    G.quad([(cx - w / 2, y - 0.004, z0), (cx + w / 2, y - 0.004, z0), (cx + w / 2, y - 0.004, z1), (cx - w / 2, y - 0.004, z1)], 'EndWindowGlow')
    G.quad([(cx - w / 2 + 0.03, y - 0.012, z0 + 0.06), (cx - w / 2 + 0.42, y - 0.012, z0 + 0.06),
            (cx - w / 2 + 0.36, y - 0.012, z1 - 0.08), (cx - w / 2 + 0.03, y - 0.012, z1 - 0.08)], 'EndCurtainGlow')
    G.done('EndWindowGlow', coll)
    y -= 0.16                                                  # the reveal stands proud of the wall; the glass is set back in it
    e = 0.16
    # The reveal, the frame and its cross, the sill, the plant on it.
    B.box((cx - w / 2 - 0.08, cx - w / 2), (y - 0.04, y + e), (z0, z1), 'HomePlaster')
    B.box((cx + w / 2, cx + w / 2 + 0.08), (y - 0.04, y + e), (z0, z1), 'HomePlaster')
    B.box((cx - w / 2 - 0.08, cx + w / 2 + 0.08), (y - 0.04, y + e), (z1, z1 + 0.1), 'HomePlaster')
    B.box((cx - w / 2 - 0.12, cx + w / 2 + 0.12), (y - 0.2, y + e), (z0 - 0.07, z0), 'Concrete')
    for xx in (cx - w / 2 + 0.02, cx + w / 2 - 0.02, cx):
        B.box((xx - 0.025, xx + 0.025), (y + e - 0.04, y + e - 0.01), (z0, z1), 'WornIron')
    for zz in (z0 + 0.02, z1 - 0.02, (z0 + z1) / 2 + 0.1):
        B.box((cx - w / 2, cx + w / 2), (y + e - 0.04, y + e - 0.01), (zz - 0.022, zz + 0.022), 'WornIron')
    add_cyl(B.bm, (cx + 0.3, y - 0.1, z0), (cx + 0.3, y - 0.1, z0 + 0.13), 0.07, 0.09, seg=10, mat=B('WornIron'))     # a pot
    for k in range(6):                                                                             # its plant
        a = k * 1.1
        add_cyl(B.bm, (cx + 0.3, y - 0.1, z0 + 0.13), (cx + 0.3 + 0.12 * math.cos(a), y - 0.1 + 0.08 * math.sin(a), z0 + 0.32 + 0.05 * k % 3),
                0.012, 0.004, seg=4, mat=B('WornIron'))
    # A little iron balcony under it (its rail crosses the window's foot) and a washing line to the right wall.
    zb = LEVELS[3]
    B.box((cx - 0.9, cx + 0.9), (y - 0.62, y), (zb - 0.06, zb + 0.02), 'WornIron')
    for k in range(9):
        xx = cx - 0.85 + k * 0.2125
        add_cyl(B.bm, (xx, y - 0.6, zb), (xx, y - 0.6, zb + 1.05), 0.01, seg=4, mat=B('WornIron'))
    add_cyl(B.bm, (cx - 0.9, y - 0.6, zb + 1.05), (cx + 0.9, y - 0.6, zb + 1.05), 0.016, seg=6, mat=B('WornIron'))
    for s in (-1, 1):
        add_cyl(B.bm, (cx + s * 0.9, y - 0.6, zb + 1.05), (cx + s * 0.9, y, zb + 1.05), 0.016, seg=6, mat=B('WornIron'))
        add_cyl(B.bm, (cx + s * 0.85, y, zb - 0.45), (cx + s * 0.85, y - 0.55, zb - 0.05), 0.02, seg=5, mat=B('WornIron'))
    a, b = Vector((cx + 0.9, y - 0.55, zb + 1.55)), Vector((WELL[1] - 0.02, y - 1.6, zb + 1.75))
    line = [a.lerp(b, t) - Vector((0, 0, 0.25 * math.sin(math.pi * t))) for t in [i / 12 for i in range(13)]]
    tube(B, line, 0.006, 'NewCable', seg=4)
    for k, (t, col, wd, ht) in enumerate(((0.25, 'HomePlaster', 0.32, 0.42), (0.45, 'HomePlaster', 0.24, 0.3), (0.62, 'HomePlaster', 0.4, 0.55))):
        p = a.lerp(b, t) - Vector((0, 0, 0.25 * math.sin(math.pi * t)))
        d = (b - a).normalized()
        q0, q1 = p - d * wd / 2, p + d * wd / 2
        B.quad([q0 - Vector((0, 0, ht)), q1 - Vector((0, 0, ht)), q1, q0], col)
        B.quad([q0, q1, q1 - Vector((0, 0, ht)), q0 - Vector((0, 0, ht))], col)


def cable_path():
    """The new cable, from the window's sill to the splice box: along the back wall to the corner, down the left wall
    on a long diagonal (over each slab edge), round the corner onto the landing's back wall, down into the box."""
    cx, z0, z1, w = WIN
    wx0, wx1, wy0, wy1 = WELL
    yb = LAND[3]
    pts = [Vector((cx - w / 2 - 0.02, wy1 - 0.05, z0 + 0.08)), Vector((cx - w / 2 - 0.15, wy1 - 0.035, z0 - 0.02))]
    # along the back wall to the corner, dipping a little between clips
    a, b = Vector((cx - w / 2 - 0.25, wy1 - 0.02, z0 - 0.08)), Vector((wx0 + 0.25, wy1 - 0.02, z0 - 0.15))
    for i in range(9):
        t = i / 8
        pts.append(a.lerp(b, t) - Vector((0, 0, 0.03 * math.sin(math.pi * t * 4) ** 2)))
    # the long diagonal down the left wall (x = wx0), over the slab edges (they stand 0.22 out, from z - 0.3 to + 0.05)
    top = Vector((wx0 + 0.02, wy1 - 0.3, z0 - 0.25))
    bot = Vector((wx0 + 0.02, yb + 0.12, 3.3))
    L = (top - bot).length
    n = int(L / 0.2)
    for i in range(n + 1):
        p = top.lerp(bot, i / n)
        lift = 0.0
        for zl in LEVELS:
            dz = p.z - (zl - 0.125)
            if abs(dz) < 0.42:
                lift = max(lift, 0.235 * min(1.0, (0.42 - abs(dz)) / 0.18))
        p.x += lift
        pts.append(p)
    # round the corner onto the landing's back wall (y = yb), along under the band and down into the splice box
    pts += [Vector((wx0 + 0.03, yb - 0.03, 3.28)), Vector((wx0 - 0.1, yb - 0.035, 3.25)), Vector((wx0 - 0.4, yb - 0.035, 3.18)),
            Vector(((NEW_BOX[0] + NEW_BOX[1]) / 2 + 0.2, yb - 0.035, 2.6)), Vector(((NEW_BOX[0] + NEW_BOX[1]) / 2 + 0.02, yb - 0.035, 2.0)),
            Vector(((NEW_BOX[0] + NEW_BOX[1]) / 2, yb - 0.04, NEW_BOX[3] + 0.06))]
    return pts


def build_cable(B):
    pts = cable_path()
    tube(B, pts, 0.011, 'NewCable', seg=6)
    # Galvanised clips every metre or so, and taped joints (two black bands) where a length was joined.
    acc, nxt = 0.0, 0.5
    for a, b in zip(pts, pts[1:]):
        seg = (b - a).length
        while acc + seg >= nxt:
            t = (nxt - acc) / seg
            p = a.lerp(b, t)
            d = (b - a).normalized()
            n = Vector((1, 0, 0)) if abs(p.x - WELL[0]) < 0.3 and p.y > LAND[3] + 0.05 else (
                Vector((0, -1, 0)) if p.y < LAND[3] + 0.05 else Vector((0, -1, 0)))
            side = d.cross(n).normalized()
            for s in (-1, 1):
                c = p + side * s * 0.022 - n * 0.004
                add_box(B.bm, c, (0.012, 0.012, 0.012), mat=B('NewSteel'))
            add_cyl(B.bm, p - side * 0.026 + n * 0.004, p + side * 0.026 + n * 0.004, 0.0065, seg=4, mat=B('NewSteel'))
            nxt += 1.05
        acc += seg
    for t in (0.33, 0.71):
        k = int(len(pts) * t)
        a, b = pts[k], pts[k + 1]
        add_cyl(B.bm, a, a + (b - a).normalized() * 0.06, 0.016, seg=6, mat=B('NewCable'))


def build_supply(B, coll):
    """Ring C's old supply box with its door hanging open, the old conduits, the new splice box and its pilot lamp."""
    yb = LAND[3]
    x0, x1, z0, z1 = OLD_BOX
    B.box((x0, x1), (yb - 0.2, yb), (z0, z1), 'WornIron')
    B.box((x0 + 0.03, x1 - 0.03), (yb - 0.205, yb - 0.17), (z0 + 0.03, z1 - 0.03), 'AtriumDark')           # its open mouth
    for k in range(3):                                                                               # busbars, and fresh copper
        xx = x0 + 0.1 + k * 0.13
        B.box((xx - 0.012, xx + 0.012), (yb - 0.16, yb - 0.13), (z0 + 0.12, z1 - 0.1), 'Copper')
    # the door, hinged at its left edge, swung right open and hanging a little
    hinge = Matrix.Translation((x0, yb - 0.2, z0)) @ Matrix.Rotation(math.radians(-112), 4, 'Z') @ Matrix.Rotation(math.radians(3), 4, 'Y')
    xform(B.box((0.0, x1 - x0), (-0.02, 0.0), (0.0, z1 - z0), 'WornIron'), hinge)
    xform(B.box((0.14, 0.32), (-0.03, -0.02), (0.36, 0.5), 'HomePlaster'), hinge)                  # the old circuit card inside it
    # old conduits: two along the wall at 2.05 and 2.17 from C-114 round to the box's top, one down from its foot
    for k, z in enumerate((2.06, 2.18)):
        xa = x0 + 0.12 + k * 0.2
        add_cyl(B.bm, (BLOCK_L[0], yb - 0.06 - 0.06 * k, z), (xa, yb - 0.06 - 0.06 * k, z), 0.026, seg=8, mat=B('DepotSteel'))
        add_cyl(B.bm, (xa, yb - 0.06 - 0.06 * k, z), (xa, yb - 0.06 - 0.06 * k, z1), 0.026, seg=8, mat=B('DepotSteel'))
        add_sphere(B.bm, (xa, yb - 0.06 - 0.06 * k, z), 0.03, seg=8, mat=B('DepotSteel'))
    add_cyl(B.bm, ((x0 + x1) / 2, yb - 0.08, z0), ((x0 + x1) / 2, yb - 0.08, 0.0), 0.03, seg=8, mat=B('DepotSteel'))
    # the new splice box (galvanised, clean), its jumper into the old box's side through a fresh hole, a roll of tape
    a0, a1, b0, b1 = NEW_BOX
    B.box((a0, a1), (yb - 0.13, yb), (b0, b1), 'NewSteel')
    B.box((a0 + 0.01, a1 - 0.01), (yb - 0.135, yb - 0.13), (b0 + 0.01, b1 - 0.01), 'NewSteel')
    for xx, zz in ((a0 + 0.02, b0 + 0.02), (a1 - 0.02, b0 + 0.02), (a0 + 0.02, b1 - 0.02), (a1 - 0.02, b1 - 0.02)):
        add_cyl(B.bm, (xx, yb - 0.135, zz), (xx, yb - 0.142, zz), 0.008, seg=6, mat=B('NewSteel'))
    add_cyl(B.bm, ((a0 + a1) / 2, yb - 0.065, b1), ((a0 + a1) / 2, yb - 0.065, b1 + 0.03), 0.02, seg=8, mat=B('NewSteel'))   # the gland
    jump = [Vector((a0, yb - 0.07, b0 + 0.08)), Vector((a0 - 0.05, yb - 0.08, b0 - 0.02)), Vector((x1 + 0.04, yb - 0.09, b0 - 0.06)),
            Vector((x1, yb - 0.1, b0 + 0.02))]
    tube(B, jump, 0.009, 'NewCable', seg=6)
    add_torus(B.bm, (a1 - 0.07, yb - 0.07, b1 + 0.022), (0, 0, 1), 0.03, 0.012, seg=12, rseg=5, mat=B('NewCable'))
    # the pilot lamp (its own object, so the game can make it glow)
    P = Batch()
    add_cyl(P.bm, ((a0 + a1) / 2, yb - 0.13, b1 - 0.07), ((a0 + a1) / 2, yb - 0.152, b1 - 0.07), 0.016, seg=10, mat=P('EndPilotLamp'))
    P.done('EndPilotLamp', coll)
    B.box(((a0 + a1) / 2 - 0.024, (a0 + a1) / 2 + 0.024), (yb - 0.142, yb - 0.13), (b1 - 0.094, b1 - 0.046), 'NewSteel')


def build_stair(B):
    """The iron stair: flight 1 rises along +x on the lane's own line (he can climb it as he walks: game z -0.15 at its
    middle, 0.8 wide), then switchbacks up the well's right wall along y to ring B's door, into the dark."""
    x0 = STAIR_X0
    r, run, W = STAIR_RISE, STAIR_RUN, STAIR_W
    wx1 = WELL[1]
    iron = 'WornIron'
    ya, yb_ = STAIR_Y0, STAIR_Y0 + W
    n1 = 10
    for k in range(n1):
        B.box((x0 + k * run, x0 + (k + 1) * run + 0.02), (ya, yb_), ((k + 1) * r - 0.025, (k + 1) * r), iron)
        B.box((x0 + k * run + 0.01, x0 + k * run + 0.03), (ya + 0.02, yb_ - 0.02), (k * r + 0.04, (k + 1) * r - 0.025), iron)   # risers, open below
    top1 = n1 * r
    px0 = x0 + n1 * run
    for yy in (ya, yb_):                                                        # the stringers
        add_cyl(B.bm, (x0 - 0.05, yy, 0.0), (px0, yy, top1 - 0.06), 0.035, seg=4, mat=B(iron))
    # platform 1, against the end wall, wide enough to turn on
    y1p = ya + 1.8
    B.box((px0, wx1), (ya, y1p), (top1 - 0.05, top1), iron)
    # flight 2: along +y up the right wall
    fx = (wx1 - W, wx1)
    n2 = 10
    for k in range(n2):
        B.box(fx, (y1p + k * run, y1p + (k + 1) * run + 0.02), (top1 + (k + 1) * r - 0.025, top1 + (k + 1) * r), iron)
    top2 = top1 + n2 * r
    y2 = y1p + n2 * run
    for xx in fx:
        add_cyl(B.bm, (xx, y1p, top1 - 0.05), (xx, y2, top2 - 0.05), 0.035, seg=4, mat=B(iron))
    B.box((wx1 - 2 * W, wx1), (y2, y2 + 0.9), (top2 - 0.05, top2), iron)
    # flight 3: back along -y, beside flight 2, up to ring B's door
    gx = (wx1 - 2 * W, wx1 - W)
    n3 = 8
    for k in range(n3):
        y_hi = y2 - k * run
        B.box(gx, (y_hi - run - 0.02, y_hi), (top2 + (k + 1) * r - 0.025, top2 + (k + 1) * r), iron)
    top3 = top2 + n3 * r
    y3 = y2 - n3 * run
    for xx in gx:
        add_cyl(B.bm, (xx, y2, top2 - 0.05), (xx, y3, top3 - 0.05), 0.035, seg=4, mat=B(iron))
    B.box((wx1 - 2 * W, wx1), (y3 - 1.0, y3), (top3 - 0.05, top3), iron)
    STAIR_DOOR[:] = [y3 - 0.92, y3 - 0.06, top3]

    def rail(a, b, n):
        a, b = Vector(a), Vector(b)
        for i in range(n + 1):
            p = a.lerp(b, i / n)
            add_cyl(B.bm, p - Vector((0, 0, 0.9)), p, 0.014, seg=5, mat=B(iron))
        add_cyl(B.bm, a, b, 0.02, seg=6, mat=B(iron))
    h = 0.9
    rail((x0 + 0.05, yb_, r + h), (px0, yb_, top1 + h), 4)                      # flight 1, on its well side
    rail((px0, yb_, top1 + h), (px0, y1p, top1 + h), 1)
    rail((wx1 - W, y1p, top1 + h), (wx1 - W, y2, top2 + h), 4)                  # flight 2
    rail((wx1 - 2 * W, y2 + 0.9, top2 + h), (wx1, y2 + 0.9, top2 + h), 2)       # platform 2
    rail((wx1 - 2 * W, y2 + 0.9, top2 + h), (wx1 - 2 * W, y3, top3 + h), 3)     # flight 3
    rail((wx1 - 2 * W, y3, top3 + h), (wx1 - 2 * W, y3 - 1.0, top3 + h), 1)
    rail((wx1 - 2 * W, y3 - 1.0, top3 + h), (wx1, y3 - 1.0, top3 + h), 2)
    # brackets into the right wall
    for yy, z in ((y1p + 0.5, top1 + 0.3), (y1p + 2.0, top1 + 1.4), (y2 + 0.45, top2 - 0.1), (y3 - 0.5, top3 - 0.1)):
        add_cyl(B.bm, (wx1, yy, z - 0.7), (wx1 - 0.7, yy, z - 0.06), 0.025, seg=4, mat=B(iron))
    return dict(foot=(x0, (ya + yb_) / 2, 0.0), top1=(px0, top1), top=((gx[0] + wx1) / 2, y3 - 0.5, top3))


def build_ending(coll):
    clear_passage()
    B = Batch()
    build_landing(B)
    build_well(B)
    build_window(B, coll)
    build_cable(B)
    build_supply(B, coll)
    info = build_stair(B)
    # The stair's door on the right wall at ring B's first floor, dark: the way on.
    wx1 = WELL[1]
    d0, d1, sill = STAIR_DOOR
    B.quad([(wx1 - 0.006, d1, sill + 0.05), (wx1 - 0.006, d0, sill + 0.05), (wx1 - 0.006, d0, sill + 2.1), (wx1 - 0.006, d1, sill + 2.1)],
           'AtriumDark')
    B.box((wx1 - 0.05, wx1), (d0 - 0.1, d1 + 0.1), (sill + 2.1, sill + 2.22), 'Concrete')
    ob = B.done('EndWell', coll)
    # The school's enamel sign onto the stair's first post, square to the camera.
    sign = bpy.data.objects.get('D5SchoolSign')
    if sign is not None:
        bb = [sign.matrix_world @ Vector(c) for c in sign.bound_box]
        cur = Vector((sum(v.x for v in bb) / 8, sum(v.y for v in bb) / 8, sum(v.z for v in bb) / 8))
        want = Vector((STAIR_X0 - 0.5, RAIL_Y - 0.02, 0.78))          # wired to the parapet's rail, by the stair's foot
        sign.location += want - cur
        sign.scale *= 0.7
    return ob, info


# =====================================================================================================================
# Secret room A: the one who stayed (behind the sorting floor's wall)
# =====================================================================================================================

def cut_sorting_wall():
    ob = bpy.data.objects.get('SortingWall')
    if ob is None:
        print('secret A: no SortingWall')
        return

    def fn(bm, M):
        gone = [f for f in bm.faces if (M @ f.calc_center_median()).y > 1.0]
        vs = {v for f in gone for v in f.verts}
        xs = [(M @ v.co).x for v in vs]
        zs = [(M @ v.co).z for v in vs]
        ys = [(M @ v.co).y for v in vs]
        bmesh.ops.delete(bm, geom=gone, context='FACES')
        return wall_with_hole(bm, (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs)), HOLE_A, 0)
    edit_world(ob, fn)


def _letter_grid(B, rnd, wall, fixed, z0, z1, u0, u1, stop=None):
    """Opened letters pinned in neat rows on a wall, read left to right as he stood facing it, top row first. wall: 'back'
    (y = fixed, facing -y; u is x), 'left' (x = fixed, facing +x; u is y), 'right' (x = fixed, facing -x; u is y, and his
    left is +y). `stop` ends the last row early (the fraction of it done)."""
    pw, ph, gx, gz = 0.11, 0.15, 0.135, 0.19
    ncol = int((u1 - u0) / gx)
    nrow = int((z1 - z0) / gz)
    off = (u1 - u0 - ncol * gx) / 2
    count = 0
    for r in range(nrow):
        zt = z1 - r * gz
        last = stop is not None and r == nrow - 1
        for c in range(ncol):
            if last and c >= int(ncol * stop):
                break
            cc = (ncol - 1 - c) if wall == 'right' else c
            uc = u0 + off + (cc + 0.5) * gx + rnd.uniform(-0.004, 0.004)
            zc = zt - ph / 2 - 0.02 + rnd.uniform(-0.004, 0.004)
            tilt = rnd.uniform(-0.03, 0.03)
            q = []
            for du, dz in ((-pw / 2, -ph / 2), (pw / 2, -ph / 2), (pw / 2, ph / 2), (-pw / 2, ph / 2)):
                q.append((uc + du * math.cos(tilt) - dz * math.sin(tilt), zc + du * math.sin(tilt) + dz * math.cos(tilt)))
            off_w = 0.004 + 0.002 * (c % 2)
            if wall == 'back':
                pts = [(uu, fixed - off_w, zz) for uu, zz in q]
            elif wall == 'left':
                pts = [(fixed + off_w, uu, zz) for uu, zz in q]
            else:
                q = [q[1], q[0], q[3], q[2]]
                pts = [(fixed - off_w, uu, zz) for uu, zz in q]
            B.quad(pts, 'SecretAtlasMat', cell_uv('page%d' % rnd.randrange(8)))
            count += 1
    return count


def _chair(B, x, y, turn, seat=0.44):
    """A plain wooden chair (sorter's), facing +y turned by `turn` degrees; origin at the seat's centre on the floor."""
    M = M_at(x, y, 0.0, turn)
    w, dp = 0.42, 0.4
    xform(B.box((-w / 2, w / 2), (-dp / 2, dp / 2), (seat - 0.04, seat), 'PigeonWood'), M)
    for sx in (-1, 1):
        for sy in (-1, 1):
            h = seat - 0.04 if sy > 0 else 0.92
            xform(B.box((sx * w / 2 - 0.02 * sx - 0.02, sx * w / 2 - 0.02 * sx + 0.02), (sy * dp / 2 - 0.02 * sy - 0.02, sy * dp / 2 - 0.02 * sy + 0.02),
                        (0.0, h), 'PigeonWood'), M)
    for z in (0.6, 0.84):
        xform(B.box((-w / 2, w / 2), (-dp / 2 + 0.0, -dp / 2 + 0.03), (z - 0.04, z + 0.04), 'PigeonWood'), M)
    xform(B.box((-w / 2 + 0.02, w / 2 - 0.02), (-0.01, 0.01), (0.12, 0.15), 'PigeonWood'), M)


def _remains_in_chair(coll, x, y, turn, seat=0.44):
    """The 'seated' remains (art/pass6/remains.py) on a chair: sat into it, the coat's back against the chair's back, the
    lap's pile on the seat, the legs folded down over the seat's front edge, the boots fallen on the floor."""
    import remains as R
    Q = R.painted()
    R.add(Q, 'seated', None, seed=3.7, support=True, knees=0.0, skull='chest', arms='hip', coat='cloth', trousers='cloth')
    xf, ys = 0.25, -0.2                                        # the seat's front edge and its right edge, in the pose's frame
    ang, side = math.radians(78), math.radians(80)
    for v in Q.bm.verts:
        v.co.z *= 0.82 if v.co.z > 0.12 else 1.0               # slumped lower into the chair than against a wall
        if v.co.x > xf:                                        # the legs over the seat's front edge, down to the floor
            dx, dz = v.co.x - xf, v.co.z
            v.co.x = xf + dx * math.cos(ang) + dz * math.sin(ang) * 0.4
            v.co.z = dz - dx * math.sin(ang)
        elif v.co.y < ys:                                      # the right arm hanging down by the chair, its hand on the floor
            dy, dz = ys - v.co.y, v.co.z
            v.co.y = ys - dy * math.cos(side) - 0.02
            v.co.z = dz - dy * math.sin(side)
    for v in Q.bm.verts:
        v.co.z += seat
        if v.co.z < 0.012:
            v.co.z = 0.012 + (v.co.z - 0.012) * 0.05
    P = R.painted()
    R._merge_into(P, Q, M_at(x, y, 0.0, turn + 90.0) @ Matrix.Translation((-0.05, 0.0, 0.0)))
    # A letter in the lap, the hand bones on it.
    import build_ration_hall as rh
    ob = P.obj('SecretARemains', 'RemainsMat', coll)
    return ob


def build_room_a(coll):
    cut_sorting_wall()
    rnd = random.Random(6601)
    B = Batch()
    x0, x1, y0, y1, zc = ROOM_A
    T = 0.12
    # The shell: side walls, back wall, ceiling (the sorting floor's slab is its floor).
    B.box((x0 - T, x0), (y0, y1 + T), (0.0, zc + T), 'WallPanel')
    B.box((x1, x1 + T), (y0, y1 + T), (0.0, zc + T), 'WallPanel')
    B.box((x0, x1), (y1, y1 + T), (0.0, zc), 'WallPanel')
    B.box((x0 - T, x1 + T), (SORT_WALL[0], y1 + T), (zc, zc + T), 'WallPanel')
    # The hole's reveal (the wall's cut edges are the rebuilt wall's), dust on the floor inside it.
    hx0, hx1, hz = HOLE_A
    # The panel: pulled off and leant back against the wall, over the hole's right side.
    # (a sheet 2 cm thick; leant on its long edge against the wall, foot out, turned so its edge shows)
    pw, ph = hx1 - hx0 + 0.06, hz + 0.06
    lean = math.radians(14)
    Mp = Matrix.Translation((hx1 - 0.12, SORT_WALL[0] - 0.015 - ph * math.sin(lean), 0.0)) @ Matrix.Rotation(-lean, 4, 'X')
    xform(B.box((0.0, pw), (-0.02, 0.0), (0.0, ph), 'WallPanel'), Mp)
    xform(B.box((0.03, pw - 0.03), (-0.026, -0.02), (ph * 0.46, ph * 0.5), 'WallPanel'), Mp)       # its stiffener
    for xx in (0.03, pw - 0.03):                                                                   # its bent screw tabs
        xform(B.box((xx - 0.012, xx + 0.012), (-0.024, -0.02), (ph - 0.05, ph - 0.02), 'DepotSteel'), Mp)
    # Two envelopes dropped by the gap.
    for (ex, ey, a, c) in ((hx0 + 0.15, SORT_WALL[0] - 0.25, 20, 'env3'), (hx0 - 0.25, SORT_WALL[0] - 0.42, -35, 'env6')):
        M = M_at(ex, ey, 0.004, a)
        pts = [M @ Vector(p) for p in ((-0.075, -0.05, 0), (0.075, -0.05, 0), (0.075, 0.05, 0), (-0.075, 0.05, 0))]
        B.quad(pts, 'SecretAtlasMat', cell_uv(c))
    # The letters: around the three walls, top rows first, the right wall's last row unfinished.
    n = _letter_grid(B, rnd, 'left', x0, 0.62, 2.22, y0 + 0.75, y1 - 0.12)
    n += _letter_grid(B, rnd, 'back', y1, 0.62, 2.22, x0 + 0.1, x1 - 0.1)
    n += _letter_grid(B, rnd, 'right', x1, 0.62, 2.22, y0 + 0.75, y1 - 0.12, stop=0.45)
    print('secret A: %d letters on the walls' % n)
    # The cot along the left wall: a canvas sling on a wooden frame, an army blanket folded at its foot, a sack pillow.
    cx0, cx1, cy0, cy1, ct = x0 + 0.08, x0 + 0.74, y0 + 0.32, y0 + 2.22, 0.38
    for xx in (cx0, cx1):
        B.box((xx - 0.02, xx + 0.02), (cy0, cy1), (ct - 0.04, ct), 'CrateWood')
    for yy in (cy0 + 0.05, (cy0 + cy1) / 2, cy1 - 0.05):
        for xx in (cx0, cx1):
            B.box((xx - 0.02, xx + 0.02), (yy - 0.02, yy + 0.02), (0.0, ct), 'CrateWood')
    B.box((cx0 + 0.02, cx1 - 0.02), (cy0, cy1), (ct - 0.05, ct - 0.02), 'CotCanvas')
    B.painted('SecretAtlasMat', 'army', lambda bm: rounded_box((cx1 - cx0 - 0.04, 0.42, 0.1), ((cx0 + cx1) / 2, cy1 - 0.3, ct + 0.04),
                                                                 p=4.0, cuts=4, bm=bm, mat=0), size=0.8)
    B.painted('SecretAtlasMat', 'army', lambda bm: rounded_box((cx1 - cx0 - 0.08, 0.9, 0.025), ((cx0 + cx1) / 2, cy0 + 0.75, ct + 0.0),
                                                                 p=4.0, cuts=4, bm=bm, mat=0), size=0.9)
    B.painted('SecretAtlasMat', 'sack', lambda bm: rounded_box((0.46, 0.3, 0.12), ((cx0 + cx1) / 2, cy0 + 0.2, ct + 0.05),
                                                                p=3.0, cuts=6, bm=bm, mat=0), size=0.5)
    # Ration tins in a neat pyramid by the way in (the right front corner), empty, labels long gone.
    tx, ty = x1 - 0.32, y1 - 0.3
    for row, k in enumerate((4, 3, 2, 1)):
        for i in range(k):
            xx = tx - (k - 1) * 0.048 + i * 0.096
            add_cyl(B.bm, (xx, ty, row * 0.105), (xx, ty, row * 0.105 + 0.1), 0.044, seg=10, mat=B('DepotSteel'))
    for i in range(3):                                                   # a second row behind, done
        xx = tx - 0.096 + i * 0.096
        add_cyl(B.bm, (xx, ty - 0.1, 0.0), (xx, ty - 0.1, 0.1), 0.044, seg=10, mat=B('DepotSteel'))
    # Two mail sacks of the unread by the right wall, letters spilling from one.
    for (sx, sy, s) in ((x1 - 0.26, y0 + 0.3, 0.9), (x1 - 0.68, y0 + 0.28, 0.75)):
        B.painted('SecretAtlasMat', 'sack', lambda bm, sx=sx, sy=sy, s=s: rounded_box((0.42 * s, 0.4 * s, 0.6 * s), (sx, sy, 0.3 * s), p=2.6,
                                                                                      cuts=8, bm=bm, mat=0, dents=((0.03, 4.0),), seed=sx), size=0.6)
    for k in range(7):
        M = M_at(x1 - 0.55 + rnd.uniform(-0.2, 0.15), y0 + 0.62 + rnd.uniform(-0.12, 0.2), 0.004 + k * 0.002, rnd.uniform(0, 360))
        pts = [M @ Vector(p) for p in ((-0.075, -0.05, 0), (0.075, -0.05, 0), (0.075, 0.05, 0), (-0.075, 0.05, 0))]
        B.quad(pts, 'SecretAtlasMat', cell_uv('env%d' % rnd.randrange(8)))
    # The chair, turned to face the wall of letters; a crate beside it for a table: a stack of opened letters, a mug.
    chx, chy, cturn = CHAIR_A
    _chair(B, chx, chy, cturn)
    # The letter he was reading, in his lap; another fallen by his feet.
    fwd = Vector((-math.sin(math.radians(cturn)), math.cos(math.radians(cturn)), 0.0))
    side = Vector((-fwd.y, fwd.x, 0.0))
    for (c, k, z, tilt, yaw) in ((Vector((chx, chy, 0)) + fwd * 0.1 + side * 0.04, 'page3', 0.44 + 0.2, 0.35, 0.0),
                                 (Vector((chx, chy, 0)) + fwd * 0.5 - side * 0.22, 'page6', 0.006, 0.0, 0.7)):
        M = Matrix.Translation((c.x, c.y, z)) @ Matrix.Rotation(math.atan2(fwd.y, fwd.x) + yaw, 4, 'Z') @ Matrix.Rotation(tilt, 4, 'Y')
        pts = [M @ Vector(p) for p in ((-0.075, -0.055, 0), (0.075, -0.055, 0), (0.075, 0.055, 0), (-0.075, 0.055, 0))]
        B.quad(pts, 'SecretAtlasMat', cell_uv(k))
        B.quad(pts[::-1], 'SecretAtlasMat', cell_uv(k))
    kx, ky = chx - 0.3, chy + 0.62
    B.box((kx - 0.22, kx + 0.22), (ky - 0.17, ky + 0.17), (0.0, 0.42), 'CrateWood')
    for k in range(9):
        M = M_at(kx - 0.06 + rnd.uniform(-0.01, 0.01), ky + rnd.uniform(-0.01, 0.01), 0.42 + 0.004 + k * 0.006, rnd.uniform(-6, 6))
        pts = [M @ Vector(p) for p in ((-0.075, -0.1, 0), (0.075, -0.1, 0), (0.075, 0.1, 0), (-0.075, 0.1, 0))]
        B.quad(pts, 'SecretAtlasMat', cell_uv('page%d' % rnd.randrange(8)))
    add_cyl(B.bm, (kx + 0.12, ky + 0.05, 0.42), (kx + 0.12, ky + 0.05, 0.5), 0.035, seg=10, mat=B('DepotSteel'))
    add_torus(B.bm, (kx + 0.16, ky + 0.05, 0.46), (0, 1, 0), 0.022, 0.006, seg=8, rseg=4, mat=B('DepotSteel'))
    # The bulb he wired from the depot's supply: a cord from a hook in the ceiling, a tin shade; lit again tonight.
    bx, by, bz = chx - 0.3, chy - 0.2, 1.92
    add_cyl(B.bm, (bx, by, zc), (bx, by, bz + 0.1), 0.004, seg=4, mat=B('Rubber'))
    add_cyl(B.bm, (bx, by, bz + 0.1), (bx, by, bz - 0.02), 0.025, 0.14, seg=14, mat=B('DepotSteel'))
    add_sphere(B.bm, (bx, by, bz - 0.04), 0.032, seg=10, mat=B('SecretLampGlow'))
    tube(B, [Vector((bx, by, zc - 0.01)), Vector((x0 + 0.6, y0 + 0.1, zc - 0.01)), Vector((x0 + 0.6, y0 + 0.02, zc - 0.01))], 0.004, 'Rubber', seg=4)
    ob = B.done('SecretA', coll)
    rem = _remains_in_chair(coll, chx, chy, cturn)
    return ob, rem


# =====================================================================================================================
# Secret room B: the children's den (behind the tunnel's tiled wall)
# =====================================================================================================================

def cut_tunnel_wall():
    hx0, hx1, hh = HOLE_B
    ob = bpy.data.objects.get('G4TunnelBack')
    if ob is not None:
        def fn(bm, M):
            vs = [M @ v.co for v in bm.verts]
            xs, ys, zs = [v.x for v in vs], [v.y for v in vs], [v.z for v in vs]
            bmesh.ops.delete(bm, geom=list(bm.verts), context='VERTS')
            return wall_with_hole(bm, (min(xs), max(xs)), (min(ys), max(ys)), (min(zs), max(zs)), (hx0, hx1, DECK + hh), 0)
        edit_world(ob, fn)
    ob = bpy.data.objects.get('G4TunnelTiles')
    if ob is not None:
        def fn2(bm, M):
            uvl = bm.loops.layers.uv.active
            bm.faces.ensure_lookup_table()
            f = bm.faces[0] if len(bm.faces) else None
            if f is None or uvl is None:
                return []
            # the plane's UV as a linear function of world x and z, from its corners
            corners = [(M @ lp.vert.co, lp[uvl].uv.copy()) for lp in f.loops]
            xs = [c[0].x for c in corners]
            zs = [c[0].z for c in corners]
            X0, X1, Z0, Z1 = min(xs), max(xs), min(zs), max(zs)
            y = corners[0][0].y
            def uvat(x, z):
                # bilinear from the four corners
                tx, tz = (x - X0) / (X1 - X0), (z - Z0) / (Z1 - Z0)
                def c(xx, zz):
                    return min(corners, key=lambda q: abs(q[0].x - xx) + abs(q[0].z - zz))[1]
                a, b, cc, d = c(X0, Z0), c(X1, Z0), c(X1, Z1), c(X0, Z1)
                return a * (1 - tx) * (1 - tz) + b * tx * (1 - tz) + cc * tx * tz + d * (1 - tx) * tz
            nrm = f.normal.copy()
            bmesh.ops.delete(bm, geom=[f], context='FACES')
            new = []
            rects = ((X0, hx0, Z0, Z1), (hx1, X1, Z0, Z1), (hx0, hx1, DECK + hh, Z1))
            for (a0, a1, b0, b1) in rects:
                q = [(a0, b0), (a1, b0), (a1, b1), (a0, b1)]
                vs = [bm.verts.new(Vector((x, y, z))) for x, z in q]
                nf = bm.faces.new(vs)
                for lp, (x, z) in zip(nf.loops, q):
                    lp[uvl].uv = uvat(x, z)
                new += vs
            return new
        edit_world(ob, fn2)


def build_room_b(coll):
    cut_tunnel_wall()
    rnd = random.Random(9090)
    B = Batch()
    x0, x1, y0, y1, zc = ROOM_B
    T = 0.12
    z0 = DECK
    hx0, hx1, hh = HOLE_B
    # The shell: floor (behind the tunnel's own), walls, ceiling; the vent's lining.
    B.box((x0 - T, x1 + T), (TUN_FLOOR_Y1, y1 + T), (z0 - 0.3, z0), 'Concrete')
    B.box((x0 - T, x0), (y0, y1 + T), (z0, zc + T), 'WallPanel')
    B.box((x1, x1 + T), (y0, y1 + T), (z0, zc + T), 'WallPanel')
    B.box((x0, x1), (y1, y1 + T), (z0, zc), 'WallPanel')
    B.box((x0 - T, x1 + T), (TUN_WALL[0] + 0.1, y1 + T), (zc, zc + T), 'WallPanel')
    for xx in (hx0, hx1):                                                  # the vent's steel lining
        B.box((xx - 0.012, xx + 0.012), (TUN_WALL[0] - 0.012, TUN_WALL[1] + 0.03), (z0, z0 + hh), 'DepotSteel')
    B.box((hx0 - 0.012, hx1 + 0.012), (TUN_WALL[0] - 0.012, TUN_WALL[1] + 0.03), (z0 + hh, z0 + hh + 0.024), 'DepotSteel')
    # The grille: off, laid on the floor in front of the vent, a little askew; its four screws beside it.
    Mg = M_at((hx0 + hx1) / 2 + 0.06, TUN_WALL[0] - 0.42, z0 + 0.012, 7.0)
    gw, gd = hx1 - hx0 + 0.04, hh + 0.04
    xform(B.box((-gw / 2, gw / 2), (-gd / 2, -gd / 2 + 0.03), (-0.008, 0.008), 'DepotSteel'), Mg)
    xform(B.box((-gw / 2, gw / 2), (gd / 2 - 0.03, gd / 2), (-0.008, 0.008), 'DepotSteel'), Mg)
    for s in (-1, 1):
        xform(B.box((s * gw / 2 - 0.015, s * gw / 2 + 0.015), (-gd / 2, gd / 2), (-0.008, 0.008), 'DepotSteel'), Mg)
    for k in range(7):
        yy = -gd / 2 + 0.07 + k * (gd - 0.14) / 6
        xform(B.box((-gw / 2, gw / 2), (yy - 0.012, yy + 0.012), (-0.004, 0.012), 'DepotSteel'), Mg)
    # The fort, in the back left corner: a check blanket hooked to the back wall, over a broom laid across the backs of
    # two little chairs, its front edge hanging down and caught up in the middle for a door; a striped blanket closes
    # its left end against the wall. Cushions inside, the lantern hung in its door, a rag rug in front.
    fx0, fx1 = x0 + 0.1, x0 + 1.75                    # its ends
    fy = y1 - 1.0                                     # the broom, on the chairs' backs
    ridge = z0 + 0.62
    hook = z0 + 1.12                                  # the blanket's top edge, hooked on the back wall
    for xx in (fx0 + 0.2, fx1 - 0.2):                 # the chairs, facing into the fort, their backs at the front
        yb_ = fy + 0.02
        B.box((xx - 0.15, xx + 0.15), (yb_, yb_ + 0.28), (z0 + 0.26, z0 + 0.29), 'CrateWood')
        for sx in (-1, 1):
            B.box((xx + sx * 0.13 - 0.015, xx + sx * 0.13 + 0.015), (yb_ - 0.015, yb_ + 0.015), (z0, ridge - 0.01), 'CrateWood')
            B.box((xx + sx * 0.13 - 0.015, xx + sx * 0.13 + 0.015), (yb_ + 0.25, yb_ + 0.28), (z0, z0 + 0.27), 'CrateWood')
        B.box((xx - 0.14, xx + 0.14), (yb_ - 0.012, yb_ + 0.012), (ridge - 0.12, ridge - 0.04), 'CrateWood')
    add_cyl(B.bm, (fx0 - 0.08, fy, ridge + 0.012), (fx1 + 0.3, fy - 0.02, ridge + 0.012), 0.013, seg=6, mat=B('CrateWood'))   # the broom
    add_cyl(B.bm, (fx1 + 0.3, fy - 0.02, ridge + 0.012), (fx1 + 0.42, fy - 0.03, ridge - 0.0), 0.022, 0.03, seg=6, mat=B('CotCanvas'))
    for xx in (fx0 + 0.25, (fx0 + fx1) / 2, fx1 - 0.25):        # the hooks on the back wall
        add_cyl(B.bm, (xx, y1, hook + 0.02), (xx, y1 - 0.05, hook + 0.03), 0.008, seg=4, mat=B('DepotSteel'))

    def drape(bm, pts):
        """A blanket as a sheet over a grid of points pts[i][j]."""
        for lay, dz in ((0, 0.0), (1, -0.006)):              # two layers, wound opposite, so it shows from both sides
            vs = [[bm.verts.new(p + Vector((0, 0, dz))) for p in row] for row in pts]
            for i in range(len(vs) - 1):
                for j in range(len(vs[0]) - 1):
                    f = (vs[i][j], vs[i + 1][j], vs[i + 1][j + 1], vs[i][j + 1])
                    bm.faces.new(f if lay == 0 else f[::-1])

    def blanket(cell, pts, size=0.9):
        B.painted('SecretAtlasMat', cell, lambda bm: drape(bm, pts), size=size)

    nx_ = 10
    roof = []                                          # from the wall's hooks down over the broom
    for i in range(nx_ + 1):
        x = fx0 - 0.12 + (fx1 - fx0 + 0.24) * i / nx_
        sag = 0.05 * math.sin(math.pi * i / nx_ * 2) ** 2
        row = []
        for j in range(6):
            t = j / 5
            yy = y1 - 0.03 + (fy - y1 + 0.03) * t
            zz = hook + (ridge + 0.03 - hook) * t - 0.07 * math.sin(math.pi * t) - sag * math.sin(math.pi * t)
            if j == 0:
                zz = hook - 0.04 * (1 - math.cos(math.pi * 2 * i / (nx_ / 3)))      # scalloped between the hooks
            row.append(Vector((x, yy, zz)))
        roof.append(row)
    blanket('check', roof)
    front = []                                         # over the broom and down, caught up in the middle for a door
    for i in range(nx_ + 1):
        x = fx0 - 0.12 + (fx1 - fx0 + 0.24) * i / nx_
        door = math.exp(-((x - (fx0 + fx1) / 2) / 0.4) ** 2)
        drop = (ridge - z0 - 0.02) * (1 - 0.82 * door)
        row = [Vector((x, fy - 0.025 - 0.07 * (j / 4) * (1 - door) - 0.04 * math.sin(math.pi * j / 4), ridge + 0.03 - drop * (j / 4))) for j in range(5)]
        front.append(row)
    blanket('check', front)
    side = []                                          # the left end, closed with the striped blanket
    for k in range(6):
        s_ = k / 5
        yy = fy - 0.04 + (y1 - fy) * s_
        top = ridge + (hook - ridge) * s_
        side.append([Vector((fx0 - 0.1 - 0.03 * math.sin(math.pi * t), yy, top - (top - z0 - 0.01) * t)) for t in (0, 0.25, 0.5, 0.75, 1.0)])
    blanket('stripe', side)
    for (cx_, cy_, s, a) in ((fx0 + 0.45, fy + 0.45, 1.0, 10), (fx0 + 0.9, fy + 0.6, 0.9, -20), (fx0 + 1.25, fy + 0.38, 0.8, 35)):
        B.painted('SecretAtlasMat', 'cushion', lambda bm, cx_=cx_, cy_=cy_, s=s, a=a: rounded_box(
            (0.42 * s, 0.36 * s, 0.13 * s), (cx_, cy_, z0 + 0.07 * s), p=2.4, cuts=6, bm=bm, mat=0,
            rot=Matrix.Rotation(math.radians(a), 4, 'Z')), size=0.5)
    rx, ry = (fx0 + fx1) / 2 + 0.25, fy - 0.62
    B.quad([(rx - 0.8, ry - 0.48, z0 + 0.006), (rx + 0.8, ry - 0.48, z0 + 0.006), (rx + 0.8, ry + 0.48, z0 + 0.006),
            (rx - 0.8, ry + 0.48, z0 + 0.006)], 'SecretAtlasMat', cell_uv('rug'))
    # The paper lantern hanging from the broom in the fort's door, lit.
    lx, ly, lz = (fx0 + fx1) / 2 + 0.05, fy - 0.16, ridge - 0.17
    add_cyl(B.bm, (lx, fy - 0.02, ridge), (lx, ly, lz + 0.1), 0.003, seg=4, mat=B('Rubber'))
    rounded_box((0.15, 0.15, 0.17), (lx, ly, lz), p=2.2, cuts=8, bm=B.bm, mat=B('DenLanternGlow'))
    for dz in (0.085, -0.085):
        add_cyl(B.bm, (lx, ly, lz + dz), (lx, ly, lz + dz * 1.18), 0.05, seg=10, mat=B('DepotSteel'))
    for k in range(4):                                                  # its paper's ribs
        a = k * math.pi / 4
        add_torus(B.bm, (lx, ly, lz), (math.cos(a), math.sin(a), 0), 0.08, 0.0025, seg=14, rseg=3, mat=B('CrateWood'))
    # Tins of treasures open at the fort's door, their lids beside them.
    for k, (tx, ty, r_, h_) in enumerate(((fx0 + 0.55, fy - 0.3, 0.09, 0.11), (fx0 + 1.02, fy - 0.42, 0.075, 0.13), (fx1 + 0.1, fy - 0.25, 0.1, 0.08))):
        B.painted('SecretAtlasMat', 'tin%d' % k, lambda bm, tx=tx, ty=ty, r_=r_, h_=h_: add_cyl(bm, (tx, ty, z0), (tx, ty, z0 + h_), r_, seg=14, mat=0), size=0.6)
        B.quad([(tx - r_ * 0.7, ty - r_ * 0.7, z0 + h_ + 0.003), (tx + r_ * 0.7, ty - r_ * 0.7, z0 + h_ + 0.003),
                (tx + r_ * 0.7, ty + r_ * 0.7, z0 + h_ + 0.003), (tx - r_ * 0.7, ty + r_ * 0.7, z0 + h_ + 0.003)],
               'SecretAtlasMat', cell_uv('treasure'))
        a = k * 2.1 + 3.6
        lid = (tx + math.cos(a) * (r_ * 2.2), ty + math.sin(a) * (r_ * 2.2))
        B.painted('SecretAtlasMat', 'tin%d' % k, lambda bm, lid=lid, r_=r_: add_cyl(bm, (lid[0], lid[1], z0), (lid[0], lid[1], z0 + 0.018), r_ + 0.005,
                                                                               seg=14, mat=0), size=0.6)
    for _ in range(8):                                                    # marbles strayed on the floor
        add_sphere(B.bm, (fx0 + rnd.uniform(0.3, 2.0), fy - rnd.uniform(0.5, 1.3), z0 + 0.008), 0.008, seg=6, mat=B('TeaEnamel'))
    # A doll's tea party laid on the rug: a tray, a teapot, four cups, a cup on its side.
    tcx, tcy = rx + 0.45, ry + 0.05
    add_sphere(B.bm, (tcx, tcy, z0 + 0.05), 0.034, seg=10, mat=B('TeaEnamel'))
    add_cyl(B.bm, (tcx + 0.03, tcy, z0 + 0.05), (tcx + 0.075, tcy, z0 + 0.075), 0.008, 0.005, seg=5, mat=B('TeaEnamel'))
    for k in range(4):
        a = k * math.pi / 2 + 0.4
        add_cyl(B.bm, (tcx + math.cos(a) * 0.2, tcy + math.sin(a) * 0.17, z0 + 0.006), (tcx + math.cos(a) * 0.2, tcy + math.sin(a) * 0.17, z0 + 0.034),
                0.015, 0.019, seg=8, mat=B('TeaEnamel'))
    # Books in a stack by the fort's right end, one open face down beside them.
    for k in range(5):
        B.painted('SecretAtlasMat', 'books', lambda bm, k=k: add_box(bm, (fx1 + 0.3 + rnd.uniform(-0.01, 0.01), fy + 0.35, z0 + 0.018 + k * 0.036),
                                                                         (0.2, 0.15, 0.034), mat=0, rot=Matrix.Rotation(rnd.uniform(-0.2, 0.2), 4, 'Z')), size=0.3)
    # Bunting across the room, corner to corner, under the ceiling.
    a, b = Vector((x0 + 0.05, y1 - 0.1, zc - 0.15)), Vector((x1 - 0.05, y0 + 0.5, zc - 0.12))
    line = [a.lerp(b, i / 16) - Vector((0, 0, 0.22 * math.sin(math.pi * i / 16))) for i in range(17)]
    tube(B, line, 0.003, 'Rubber', seg=3)
    for i in range(16):
        p, q = line[i], line[i + 1]
        m = (p + q) / 2
        u0, v0, u1, v1 = cell_uv('bunting')
        c = i % 4
        uu = (u0 + (u1 - u0) * (c + 0.5) / 4, (v0 + v1) / 2)
        tip = m - Vector((0, 0, 0.13))
        for tri in ((p, q, tip), (tip, q, p)):
            f = B.bm.faces.new([B.bm.verts.new(v) for v in tri])
            f.material_index = B('SecretAtlasMat')
            for lp in f.loops:
                lp[B.uv].uv = uu
    ob = B.done('SecretB', coll)

    # The chalk: on the back wall right of the fort, over the fort, on the right wall, on the left wall by the way in,
    # the handprints at child height; Mara's little tree outside, beside the vent.
    C = Batch()
    e = 0.004

    def back(cell, xa, xb, za, zb):
        C.quad([(xa, y1 - e, za), (xb, y1 - e, za), (xb, y1 - e, zb), (xa, y1 - e, zb)], 'SecretChalkMat', cell_uv(cell, CCELLS))

    def right(cell, ya, yb, za, zb):                                       # the right wall faces -x: u runs along -y
        C.quad([(x1 - e, yb, za), (x1 - e, ya, za), (x1 - e, ya, zb), (x1 - e, yb, zb)], 'SecretChalkMat', cell_uv(cell, CCELLS))

    def left(cell, ya, yb, za, zb):                                        # the left wall faces +x: u runs along +y
        C.quad([(x0 + e, ya, za), (x0 + e, yb, za), (x0 + e, yb, zb), (x0 + e, ya, zb)], 'SecretChalkMat', cell_uv(cell, CCELLS))

    back('hands', fx1 + 0.2, x1 - 0.1, z0 + 0.3, z0 + 0.3 + (x1 - 0.3 - fx1) / 2.0)          # the prints at 0.45 to 0.8 m
    back('tree', fx1 + 0.14, fx1 + 0.66, z0 + 0.92, z0 + 1.44)                              # Mara's tree, big, by them
    back('muralB', fx0, fx1 + 0.1, hook + 0.25, hook + 0.25 + (fx1 + 0.1 - fx0) / 2.0)
    left('muralC', y0 + 0.4, fy - 0.1, z0 + 0.55, z0 + 0.55 + (fy - 0.5 - y0) / (768 / 256))
    right('muralA', y0 + 0.15, y1 - 0.12, z0 + 0.62, z0 + 0.62 + (y1 - 0.27 - y0) / 4.0)
    # outside, on the tiles beside the vent (the tiles' face is TUN_WALL[0] - 0.01)
    yt = TUN_WALL[0] - 0.01 - e
    C.quad([(hx1 + 0.04, yt, z0 + 0.08), (hx1 + 0.26, yt, z0 + 0.08), (hx1 + 0.26, yt, z0 + 0.3), (hx1 + 0.04, yt, z0 + 0.3)],
           'SecretChalkMat', cell_uv('tree', CCELLS))
    chalk = C.done('SecretBChalk', coll)
    return ob, chalk


# =====================================================================================================================
# build_set
# =====================================================================================================================

def report(objs):
    for ob in objs:
        if ob is None:
            continue
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        mn = [min(v[i] for v in bb) for i in range(3)]
        mx = [max(v[i] for v in bb) for i in range(3)]
        mats = [m.name for m in ob.data.materials]
        print('ending_secrets: %-16s tris %6d  mats %2d %s  Blender x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (
            ob.name, tri_count(ob), len(mats), mats, mn[0], mx[0], mn[1], mx[1], mn[2], mx[2]))


def build_set(dl01, m, coll):
    bpy.context.view_layer.update()
    end, info = build_ending(coll)
    a, a_rem = build_room_a(coll)
    b, b_chalk = build_room_b(coll)
    bpy.context.view_layer.update()
    report([end, bpy.data.objects.get('EndWindowGlow'), bpy.data.objects.get('EndPilotLamp'), a, a_rem, b, b_chalk])
    print('ending_secrets: stair', info)


def add_clips(dl01, arm):
    pass
