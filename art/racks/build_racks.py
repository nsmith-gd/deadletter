"""DL-04 The Racks: the set and D-17's clips for this scene (docs/chapter1_build_spec.md, section 4).

Built in world coordinates, between the stretches that build_dl01.OFF2..OFF4 move. The racks hall of
art/dl02 (moved by OFF2) ends at about x 40.1; this continues it to the charging bay and its door, then a
short service passage into DL-05's scanner corridor at x 47.9 (art/dl03, moved by OFF3).

    x 40.1 to 43.1   the end of the racks: the hall's last bays, every slot empty. The near row's slot at
                     41.1 is mounted on a column, with flowers chalked on the column above it.
    x 40.8 to 41.6   the fallen courier, lying on its left side just behind the lane, head toward the bay,
                     a red tow loop on its shoulder harness at the head end, 0.44 high.
    x 44.0 to 45.0   the charging bay: the plate, the cradle frame behind it, two cradle arms.
    x 46.3 to 46.7   the bay door in the hall's end wall, three lamps above it.
    x 46.7 to 47.9   the service passage, the same section as the scanner corridor it runs into.

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
from build_d17 import (add_box, add_cyl, add_sphere, add_torus, rounded_box, emission_material,
                       worn_material, smoothstep, SIDES, CLAW_REST_OPEN)

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')

# Shared with the game (game/undelivered/index.html should keep the same numbers).
HALL_X0 = 40.1                       # where art/dl02's racks hall stops (its x 27.1 after OFF2)
RACKS_X1 = 43.1                      # the racks end here
OLD_END_X = 39.9                     # art/dl02's hall end wall (its HALL2_X1 26.9), opened up here
ROWS_Y = (1.65, 2.95, 4.25, 5.55, 6.85)
NEAR_ROW_Y = 0.9
COLUMNS_X = (41.1, 44.0)             # the hall's column rhythm (2.9 m) carried on
COLUMN_Y = (1.23, 4.9, 8.6)
MEMORIAL_X = 41.1                    # the empty slot on the column, flowers chalked above it

FALLEN = (41.2, 0.35)                # the fallen courier's origin: on the floor at the centre of its footprint
LOOP_Z = 0.44                        # the tow loop's grip height (push and drag clips)

PLATE = (44.0, 45.0)                 # the bay plate, x0, x1
PLATE_Y = (-0.32, 0.66)              # y0, y1: the lane and the courier's line behind it
PLATE_TOP = 0.004
CRADLE_X = 44.5
ARM_DX = 0.275                       # cradle arms either side of the courier's pod
PIVOT_Y = 0.72                       # the arms' shoulders on the bay's back frame
SEATED_Y = 0.44                      # the seated courier's root, in the cradle
SEATED_BODY = (0.0, 0.0, -0.14)      # its pose: sitting low on its folded legs
SEATED_ROT = (9.0, 0.0, 0.0)
LYING_HOLD = (0.35, 0.45)            # (y, z) where the cups close on the lying courier, on the plate
FRAME_Y = 0.86                       # the bay's backboard

DOOR_X, DOOR_H, DOOR_W = 46.5, 1.6, 1.24   # the shutter's plane (frame 46.3 to 46.7), height, width across the lane
END_WALL = (46.4, 46.6)              # the hall's end wall, which the door is set in
PASSAGE = (46.6, 47.9)               # the service passage, into the scanner corridor
PASS_BACK_Y, PASS_CEIL = 0.67, 2.4   # the scanner corridor's section (art/dl03 build_corridor)


def cradle_pivot():
    """The arms' shoulder height: the pivot from which both hold points (the cup on the lying courier,
    and the cup at the seated courier's pod side) are the same distance, so a plain rotation about x
    carries the cup from one to the other."""
    a = Vector(LYING_HOLD)
    b = Vector((SEATED_Y - 0.045, seated_hold_z()))
    py = PIVOT_Y
    pz = ((py - b.x) ** 2 - (py - a.x) ** 2 + b.y ** 2 - a.y ** 2) / (2 * (b.y - a.y))
    return py, pz


def seated_hold_z():
    """The seated courier's pod centre (rest 0.387, dropped by its pose), on the plate."""
    return PLATE_TOP + 0.387 + SEATED_BODY[2]


def arm_angles():
    """(up, down) angles of the cup about the pivot, degrees from straight down, positive forward (-y)."""
    py, pz = cradle_pivot()
    up = math.degrees(math.atan2(py - (SEATED_Y - 0.045), pz - seated_hold_z()))
    down = math.degrees(math.atan2(py - LYING_HOLD[0], pz - LYING_HOLD[1]))
    return up, down


def _obj(name, bm, mats, coll, sharp=35):
    return d17.mesh_object(name, bm, mats, coll, sharp=sharp)


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


def _quad(bm, uv, corners, mat=0):
    """One UV-mapped quad: corners in order (u0 v0, u1 v0, u1 v1, u0 v1)."""
    vs = [bm.verts.new(c) for c in corners]
    f = bm.faces.new(vs)
    f.material_index = mat
    for lp, (u, v) in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uv].uv = (u, v)
    return f


def _plane(name, mat, corners, coll):
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    _quad(bm, uv, corners)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


# --------------------------------------------------------------------------
# Textures (8-bit PNGs, drawn once and kept in textures/)
# --------------------------------------------------------------------------

def make_chalk_flowers(path):
    """Flowers chalked on the column over the empty slot: three stems in a scribbled jar, a few petals
    fallen at its foot, and a small heart. Chalk on transparent."""
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(44)
    w, h = 192, 288
    W, H = 320, 480                                     # drawn at this size
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    chalk = (226, 222, 208, 235)
    pink = (222, 176, 178, 225)
    yellow = (226, 210, 150, 225)

    def stroke(pts, fill, width, passes=2, jitter=2.0):
        for _ in range(passes):
            q = [(x + rnd.uniform(-jitter, jitter), y + rnd.uniform(-jitter, jitter)) for x, y in pts]
            d.line(q, fill=fill, width=width, joint='curve')

    def curve(p0, p1, p2, n=14):
        return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
                 (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]

    # The jar.
    stroke([(108, 330), (100, 430), (220, 430), (212, 330)], chalk, 6)
    stroke([(100, 330), (220, 330)], chalk, 5)
    # Three stems, leaves, heads.
    heads = [((96, 150), pink), ((166, 96), chalk), ((238, 170), yellow)]
    for (hx, hy), col in heads:
        stroke(curve((160, 335), ((160 + hx) / 2 + rnd.uniform(-20, 20), 250), (hx, hy + 22)), chalk, 5)
        lx, ly = (160 + hx) / 2, 268
        side = -1 if hx < 160 else 1
        stroke(curve((lx, ly), (lx + side * 30, ly - 26), (lx + side * 48, ly - 8)), chalk, 4)
        for k in range(6):                                   # five or six looped petals
            a = 2 * math.pi * k / 6 + rnd.uniform(-0.2, 0.2)
            px, py = hx + 26 * math.cos(a), hy + 26 * math.sin(a)
            d.ellipse((px - 15, py - 15, px + 15, py + 15), outline=col, width=5)
        d.ellipse((hx - 9, hy - 9, hx + 9, hy + 9), fill=chalk)
    # Petals fallen beside the jar, and a little heart.
    for x, y in ((70, 438), (246, 444), (262, 430)):
        d.ellipse((x - 9, y - 6, x + 9, y + 6), outline=pink, width=4)
    stroke([(250, 60), (238, 46), (226, 56), (250, 84), (274, 56), (262, 46), (250, 60)], pink, 4, jitter=1.2)
    img = img.filter(ImageFilter.GaussianBlur(0.9))
    # Chalk grain: break the strokes up (in a few steps, so the PNG stays small), then down to size.
    px = img.load()
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a:
                px[x, y] = (r, g, b, int(a * (0.6, 0.8, 1.0, 1.0)[rnd.randrange(4)]))
    img = img.resize((w, h), Image.LANCZOS)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True)


def make_bay_pictogram(path):
    """The bay's sign, wordless: a courier seated in the cradle, three lamps over it, a charge bolt."""
    from PIL import Image, ImageDraw, ImageFilter
    s = 512
    img = Image.new('RGB', (s, s), (176, 186, 184))
    d = ImageDraw.Draw(img)
    ink = (28, 34, 36)
    d.rectangle((14, 14, s - 14, s - 14), outline=ink, width=14)
    # Cradle: two arms down from the shoulders to the seat.
    for x in (140, 372):
        d.line((x, 150, x, 300), fill=ink, width=16)
        d.line((x, 300, x + (40 if x < 256 else -40), 340), fill=ink, width=16)
        d.ellipse((x - 18, 132, x + 18, 168), fill=ink)
    # The courier: wide head, antenna, pod, folded legs.
    d.rounded_rectangle((176, 170, 336, 236), radius=14, fill=ink)
    d.line((300, 170, 312, 116), fill=ink, width=8)
    d.rounded_rectangle((196, 246, 316, 340), radius=18, fill=ink)
    for x in (214, 298):
        d.line((x, 340, x - 6, 396), fill=ink, width=14)
        d.line((x - 6, 396, x + 14, 400), fill=ink, width=12)
    for k in range(3):                                      # its three lamps lit
        d.ellipse((222 + k * 26, 288, 238 + k * 26, 304), fill=(176, 186, 184))
    # The charge bolt and the floor line.
    d.polygon([(410, 210), (440, 210), (424, 250), (452, 250), (404, 320), (418, 266), (392, 266)], fill=ink)
    d.rectangle((60, 420, s - 60, 434), fill=ink)
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def make_dust_outline(path, tris, bounds):
    """Years of dust on the floor around the fallen courier, and the clean shape it leaves when it is
    moved. `tris` are its triangles projected to the floor (x, y), `bounds` is (x0, y0, x1, y1)."""
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(12)
    w, h = 256, 160
    x0, y0, x1, y1 = bounds
    to_px = lambda x, y: ((x - x0) / (x1 - x0) * w, (1 - (y - y0) / (y1 - y0)) * h)  # noqa: E731
    clean = Image.new('L', (w, h), 0)
    dc = ImageDraw.Draw(clean)
    for t in tris:
        dc.polygon([to_px(*p) for p in t], fill=255)
    clean = clean.filter(ImageFilter.MaxFilter(3)).filter(ImageFilter.GaussianBlur(2))
    # Dust: soft-edged patch, mottled, thicker toward the rack.
    dust = Image.new('L', (w, h), 0)
    dd = ImageDraw.Draw(dust)
    for _ in range(260):
        cx, cy = rnd.uniform(0.05, 0.95) * w, rnd.uniform(0.05, 0.95) * h
        r = rnd.uniform(5, 21)
        dd.ellipse((cx - r, cy - r * 0.7, cx + r, cy + r * 0.7), fill=rnd.randint(60, 150))
    dust = dust.filter(ImageFilter.GaussianBlur(5))
    px, pc = dust.load(), clean.load()
    alpha = Image.new('L', (w, h))
    pa = alpha.load()
    for y in range(h):
        for x in range(w):
            ex = min(x, w - 1 - x) / (0.18 * w)
            ey = min(y, h - 1 - y) / (0.25 * h)
            edge = max(0.0, min(1.0, ex)) * max(0.0, min(1.0, ey))
            a = (0.35 + px[x, y] / 255 * 0.6) * edge * (1 - pc[x, y] / 255)
            pa[x, y] = int(255 * min(1.0, a)) & 0xFC              # a few levels fewer: smaller PNG
    grey = Image.new('L', (w, h), 118)
    out = Image.merge('RGBA', (grey, grey, Image.new('L', (w, h), 108), alpha))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    out.save(path)


# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------

def racks_materials(m):
    # The bay is the one clean, pale, cold thing down here: enamel on steel.
    m['bayenamel'] = worn_material('BayEnamel', base=(0.36, 0.4, 0.41), dirt=(0.29, 0.31, 0.31),
                                   chip=(0.2, 0.21, 0.2), rough=0.38, chip_rough=0.6, metallic=0.1,
                                   grime_scale=2.5, chip_scale=60, chip_amount=0.9, edge_wear=False,
                                   streaks=0.15, dust=(0.33, 0.34, 0.33), dust_amount=0.1)
    m['baylight'] = emission_material('BayLight', (0.72, 0.88, 1.0), 2.0)       # always on: the bay is lit
    m['baylamp'] = [emission_material(f'BayLamp{i}', (0.72, 0.92, 1.0), 0.0) for i in range(3)]
    m['fallenlamp'] = emission_material('FallenLamp', (0.85, 0.30, 0.08), 0.0)
    m['seatedlamp'] = emission_material('SeatedLamp', (0.85, 0.30, 0.08), 0.0)   # the same lamps, once seated
    # The fallen courier: D-17's own paint, under years of dust.
    m['dustycream'] = worn_material('DustyCream', base=(0.5, 0.46, 0.35), dirt=(0.3, 0.26, 0.18),
                                    chip=(0.03, 0.027, 0.022), rough=0.85, chip_rough=0.55, metallic=0.0,
                                    grime_scale=4.0, chip_scale=24, chip_amount=0.64, streaks=0.4,
                                    dust=(0.56, 0.54, 0.48), dust_amount=0.95)
    m['dustydark'] = worn_material('DustyDark', base=(0.03, 0.029, 0.026), dirt=(0.05, 0.045, 0.035),
                                   chip=(0.09, 0.085, 0.075), rough=0.82, chip_rough=0.5, metallic=0.2,
                                   grime_scale=5, chip_scale=34, chip_amount=0.78, edge_wear=False,
                                   streaks=0.4, dust=(0.15, 0.145, 0.13), dust_amount=1.0)


# --------------------------------------------------------------------------
# The hall, continued
# --------------------------------------------------------------------------

def open_old_end(dl01):
    """art/dl02 closes its hall with an end wall and a lane header at x 39.9 (its HALL2_X1 + OFF2). The hall
    runs on now, so cut those two slabs out of its RechargeHall mesh (nothing else of it lies in that slab)."""
    ob = bpy.data.objects.get('RechargeHall')
    if ob is None or ob.type != 'MESH':
        return 0
    bpy.context.view_layer.update()                 # art/dl02 has just moved it by OFF2
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    mw = ob.matrix_world
    doomed = [v for v in bm.verts if OLD_END_X - 0.11 < (mw @ v.co).x < OLD_END_X + 0.11]
    n = len(doomed)
    bmesh.ops.delete(bm, geom=doomed, context='VERTS')
    bm.to_mesh(ob.data)
    bm.free()
    return n


def build_hall(m, coll):
    rnd = random.Random(404)
    x1 = END_WALL[1]
    bm = bmesh.new()
    add_box(bm, ((HALL_X0 + x1) / 2, 9.2, 3.2), (x1 - HALL_X0, 0.2, 6.4))           # back wall
    for x in COLUMNS_X:
        for y in COLUMN_Y:
            add_box(bm, (x, y, 3.2), (0.32, 0.32, 6.4))
    for y in (1.2, 4.9, 8.6):
        add_box(bm, ((HALL_X0 + x1) / 2, y, 5.6), (x1 - HALL_X0, 0.25, 0.35))
    # The end wall the lane leaves through: behind the lane, and a header over the bay door.
    ex = (END_WALL[0] + END_WALL[1]) / 2
    ew = END_WALL[1] - END_WALL[0]
    add_box(bm, (ex, (0.68 + 9.2) / 2, 3.2), (ew, 9.2 - 0.68, 6.4))
    add_box(bm, (ex, (-0.86 + 0.68) / 2, (DOOR_H + 0.15 + 6.4) / 2), (ew, 1.54, 6.4 - DOOR_H - 0.15))
    add_box(bm, (ex, -0.78, (DOOR_H + 0.15) / 2), (ew, 0.16, DOOR_H + 0.15))         # in front of the door
    # The service passage: the scanner corridor's section, its wall running on up into the dark.
    px0, px1 = PASSAGE
    add_box(bm, ((px0 + px1) / 2, PASS_BACK_Y, 1.9), (px1 - px0, 0.1, 3.8))
    add_box(bm, ((px0 + px1) / 2, -0.35, PASS_CEIL + 0.05), (px1 - px0, 2.1, 0.1))
    _obj('RacksHall', bm, [m['wall']], coll)

    bm = bmesh.new()                                                                # floor on from DL-01's (ends at 43)
    add_box(bm, ((43.0 + 48.0) / 2, 4.0, -0.05), (5.0, 16.0, 0.1))
    _obj('RacksFloor', bm, [m['concrete']], coll)

    # The last bays of the racks. Rows step on as in art/dl02; every slot here is empty.
    racks, contacts, plinths, fixtures, tags = bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new(), bmesh.new()
    rows = [(NEAR_ROW_Y, [40.2, MEMORIAL_X, 42.0, 42.85])] + \
           [(y, [39.4 + 0.82 * k for k in range(1, 5)]) for y in ROWS_Y]
    for r, (y, xs) in enumerate(rows):
        xa = 39.55 if r == 0 else 39.65                                             # art/dl02's plinths end here
        add_box(plinths, ((xa + RACKS_X1) / 2, y + 0.1, 0.03), (RACKS_X1 - xa, 0.62, 0.06))
        for x in xs:
            if r == 0 and x == MEMORIAL_X:
                # The slot on the column: contacts straight out of its face, a tag, nothing in it.
                face = COLUMN_Y[0] - 0.16
                for z in (0.49, 0.57):
                    add_box(racks, (x, face - 0.04, z), (0.06, 0.08, 0.04))
                    add_cyl(contacts, Vector((x, face - 0.08, z)), Vector((x, face - 0.11, z)), 0.014, 0.011, seg=10)
                add_box(tags, (x, face - 0.003, 0.72), (0.05, 0.004, 0.03))
                continue
            post = Vector((x, y + 0.36, 0))
            add_box(racks, post + Vector((0, 0, 0.45)), (0.07, 0.07, 0.84))
            add_box(racks, post + Vector((0, 0, 0.88)), (0.1, 0.1, 0.04))
            seg = 8 if r == 0 else 5                                                # the far rows are distant
            for z in (0.43, 0.51):
                add_cyl(racks, post + Vector((0, 0, z)), Vector((x, y + 0.2, z + 0.06)), 0.01, seg=seg)
                add_cyl(contacts, Vector((x, y + 0.2, z + 0.06)), Vector((x, y + 0.17, z + 0.06)), 0.014, 0.011,
                        seg=seg + 2)
            add_box(tags, post + Vector((0, -0.036, 0.72)), (0.05, 0.004, 0.03))
        if r > 0:
            add_box(fixtures, ((xa + RACKS_X1) / 2, y, 2.62), (RACKS_X1 - xa, 0.12, 0.06))
            add_cyl(fixtures, (42.2, y, 2.65), (42.2, y, 5.4), 0.005, seg=4)
        # Row ends: a closing post, so the rows stop rather than run out.
        add_box(racks, Vector((RACKS_X1 - 0.03, y + 0.36, 0.45)), (0.07, 0.07, 0.9))
    _obj('RacksPlinths', plinths, [m['concrete']], coll)
    _obj('RacksPosts', racks, [m['depot_green']], coll)
    _obj('RacksContacts', contacts, [m['copper']], coll)
    _obj('RacksTags', tags, [m['tag']], coll)
    _obj('RacksRowFixtures', fixtures, [m['steel']], coll)
    for r, (y, xs) in enumerate(rows):
        bm = bmesh.new()
        xa = 39.4 if r == 0 else 39.55                                              # art/dl02's tubes end here
        if r == 0:
            add_box(bm, ((xa + RACKS_X1 - 0.1) / 2, y + 0.45, 1.6), (RACKS_X1 - 0.1 - xa, 0.03, 0.03))
        else:
            add_box(bm, ((xa + RACKS_X1 - 0.05) / 2, y, 2.585), (RACKS_X1 - 0.05 - xa, 0.05, 0.02))
        # Same materials as art/dl02's RowTube0..5, so they light with the rest of the hall.
        _obj(f'RacksRowTube{r}', bm, [m['rowlight'][r]], coll)

    # Chalk flowers on the column, over the empty slot.
    path = os.path.join(TEX, 'chalk_flowers.png')
    if not os.path.exists(path):
        make_chalk_flowers(path)
    mat = _image_material('ChalkFlowers', path, rough=0.95, alpha=True)
    fy = COLUMN_Y[0] - 0.161
    x0, x1, z0, z1 = MEMORIAL_X - 0.15, MEMORIAL_X + 0.15, 0.8, 1.25
    _plane('RacksChalkFlowers', mat, [(x0, fy, z0), (x1, fy, z0), (x1, fy, z1), (x0, fy, z1)], coll)

    # A few things left on the plinths and floor where the racks end.
    bm = bmesh.new()
    for x, y in ((42.35, 1.0), (42.5, 2.0), (40.6, 1.9)):
        sz = (rnd.uniform(0.12, 0.2), rnd.uniform(0.1, 0.16), rnd.uniform(0.06, 0.1))
        add_box(bm, (x, y, 0.06 + sz[2] / 2), sz, rot=Matrix.Rotation(rnd.uniform(-0.6, 0.6), 4, 'Z'))
    _obj('RacksParcels', bm, [m['paper']], coll)


# --------------------------------------------------------------------------
# The courier: a spare D-17 posed and baked, twice
# --------------------------------------------------------------------------

LAMP_MATS = ('LampA', 'LampB', 'LampC')
DEAD_MATS = ('Glow', 'GlowDim', 'EyeGlint', 'ParcelLamp')     # its lights are out
DROP_MATS = ('ParcelPaper',)                                   # its compartment is empty


def _base(name):
    return name.split('.')[0] if name else ''


def bake_pose(dl01, arm, coll, name, pose):
    """Pose the spare rig (one frame) and bake every part into two bmeshes in rig space: the body,
    with its materials, and the three chest lamps. Returns (body_bm, mats, lamps_bm)."""
    c = dl01.Clip(arm, name, 1)
    c.pose(1, **pose)
    arm.animation_data.action = bpy.data.actions[name]
    bpy.context.scene.frame_set(1)
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    body, lamps, mats = bmesh.new(), bmesh.new(), []
    for ob in list(coll.all_objects):
        if ob.type not in ('MESH', 'CURVE') or ob.name.startswith('ParcelLabel'):
            continue
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        me.transform(ev.matrix_world)
        names = [s.material.name if s.material else '' for s in ob.material_slots] or ['']
        tmp = bmesh.new()
        tmp.from_mesh(me)
        ev.to_mesh_clear()
        for f in list(tmp.faces):
            n = _base(names[min(f.material_index, len(names) - 1)])
            if n in DROP_MATS:
                tmp.faces.remove(f)
        lamp_faces = [f for f in tmp.faces if _base(names[min(f.material_index, len(names) - 1)]) in LAMP_MATS]
        if lamp_faces:
            lb = tmp.copy()
            keep = {f.index for f in lamp_faces}
            lb.faces.ensure_lookup_table()
            bmesh.ops.delete(lb, geom=[f for f in lb.faces if f.index not in keep], context='FACES')
            me2 = bpy.data.meshes.new('_lamps')
            lb.to_mesh(me2)
            lb.free()
            lamps.from_mesh(me2)
            bpy.data.meshes.remove(me2)
            bmesh.ops.delete(tmp, geom=lamp_faces, context='FACES')
        remap = []
        for n in names:
            b = _base(n)
            key = 'EyeDark' if b in DEAD_MATS else b
            if key not in mats:
                mats.append(key)
            remap.append(mats.index(key))
        for f in tmp.faces:
            f.material_index = remap[min(f.material_index, len(remap) - 1)]
        me2 = bpy.data.meshes.new('_part')
        tmp.to_mesh(me2)
        tmp.free()
        body.from_mesh(me2)
        bpy.data.meshes.remove(me2)
    arm.animation_data.action = None
    return body, mats, lamps


def _courier_object(name, bm, mats, m, coll, xform, ratio=0.09):
    """Turn a baked rig-space bmesh into a decimated static object: `xform` maps rig space to the
    object's local space. Paint and dark metal swap for their dusty versions."""
    bmesh.ops.transform(bm, matrix=xform, verts=bm.verts)
    swap = {'CreamPaint': m['dustycream'], 'CreamLimb': m['dustycream'], 'DarkMetal': m['dustydark']}
    used = sorted({f.material_index for f in bm.faces})
    final, remap = [], {}
    for i in used:
        key = mats[i]
        mat = swap.get(key) or bpy.data.materials.get(key)
        if mat is None:
            mat = next((x for x in bpy.data.materials if _base(x.name) == key), None)
        if mat not in final:
            final.append(mat)
        remap[i] = final.index(mat)
    for f in bm.faces:
        f.material_index = remap[f.material_index]
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for mat in final:
        me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    dec = ob.modifiers.new('lod', 'DECIMATE')
    dec.ratio = ratio
    d17.bake_modifiers(ob)
    ob.data.name = name
    while ob.data.uv_layers:                       # its paint is procedural: no UVs, a quarter less to ship
        ob.data.uv_layers.remove(ob.data.uv_layers[0])
    ob.data.polygons.foreach_set('use_smooth', [True] * len(ob.data.polygons))
    ob.data.set_sharp_from_angle(angle=math.radians(40))
    return ob


def _lamps_object(name, bm, mat, coll, xform, parent):
    bmesh.ops.transform(bm, matrix=xform, verts=bm.verts)
    for f in bm.faces:
        f.material_index = 0
    ob = _obj(name, bm, [mat], coll)
    ob.parent = parent
    ob.matrix_parent_inverse = Matrix.Identity(4)
    return ob


# Poses (dl01.Clip.pose keywords; rig space, the rig standing at its origin facing -y).
# Lying on its left side where it fell, facing the camera, head toward the bay and bowed to the floor;
# legs drawn up a little, the top one forward; the arm underneath stretched out along the floor past
# its face, claw open; the top arm fallen limp across its front.
LYING_POSE = dict(
    body=(0.0, 0.0, -0.02), body_rot=(8.0, 0.0, 0.0), head=(12.0, 16.0, 0.0),
    antenna=[(-34.0, 8.0), (-40.0, 10.0), (-44.0, 10.0)],
    feet={'L': ((0.02, -0.05, 0.05), (20.0, 0.0, 0.0)), 'R': ((-0.03, -0.14, 0.13), (45.0, 0.0, 0.0))},
    claws={'L': 36.0, 'R': 6.0}, elbows={'L': 0.4, 'R': 0.0})
# Seated in the cradle: low on its folded legs, head bowed, claws in its lap.
SEATED_POSE = dict(
    body=SEATED_BODY, body_rot=SEATED_ROT, head=(22.0, 5.0, 0.0),
    antenna=[(-40.0, 6.0), (-46.0, 8.0), (-40.0, 8.0)],
    feet={'L': ((0.01, -0.05, 0.0), (0.0, 0.0, 0.0)), 'R': ((-0.01, -0.03, 0.0), (0.0, 0.0, 4.0))},
    hand_rot={'L': (-40.0, 10.0, 30.0), 'R': (-40.0, -10.0, -30.0)},
    claws={'L': 10.0, 'R': 2.0}, elbows={'L': 0.5, 'R': 0.5})
LYING_TILT = 4.0                     # degrees the head end dips, so the head rests on the floor too


def lying_hands(dl01):
    return {1: Vector((0.215, -0.2, 0.6)) - dl01.REST_WRIST[1],                   # under it: out past its face
            -1: Vector((-0.03, -0.27, 0.26)) - dl01.REST_WRIST[-1]}               # on top: limp across its front


def aim(d):
    """hand_rot (degrees) that points the claws along d (body space): pitch about x, then turn about z."""
    d = Vector(d).normalized()
    a = -math.acos(max(-1.0, min(1.0, -d.z)))
    sa = math.sin(a)
    return (math.degrees(a), 0.0, math.degrees(math.atan2(-d.x / sa, d.y / sa)))


def seated_hands(dl01):
    return {s: Vector((-s * 0.07, -0.2, 0.17)) for _, s in SIDES}


def build_couriers(dl01, m, coll):
    arm = d17.build_robot('RacksCourier', (0, 0, 0), 0)
    rcoll = bpy.data.collections['RacksCourier']
    out = {}

    # Lying.
    pose = dict(LYING_POSE, hands=lying_hands(dl01), hand_rot={'L': aim((-0.2, -0.3, 0.93)), 'R': aim((0.8, -0.4, -0.45))})
    body, mats, lamps = bake_pose(dl01, arm, rcoll, 'RacksLying', pose)
    rot = Matrix.Rotation(math.radians(90.0 + LYING_TILT), 4, 'Y')   # up along +x, left side down
    xs, zs = [], []
    for v in body.verts:
        p = rot @ v.co
        xs.append(p.x)
        zs.append(p.z)
    shift = Vector((-(min(xs) + max(xs)) / 2, 0.0, -min(zs)))
    xform = Matrix.Translation(shift) @ rot
    fallen = _courier_object('FallenCourier', body, mats, m, coll, xform)
    _lamps_object('FallenLamps', lamps, m['fallenlamp'], coll, xform, fallen)
    fallen.location = (FALLEN[0], FALLEN[1], 0.0)
    out['fallen'] = fallen
    out['lying_xform'] = xform

    # Seated, its origin on the cradle's pivot line so the game can turn it with the arms.
    pose = dict(SEATED_POSE, hands=seated_hands(dl01))
    body, mats, lamps = bake_pose(dl01, arm, rcoll, 'RacksSeated', pose)
    py, pz = cradle_pivot()
    origin = Vector((CRADLE_X, py, pz))
    xform = Matrix.Translation(Vector((CRADLE_X, SEATED_Y, PLATE_TOP)) - origin)
    seated = _courier_object('SeatedCourier', body, mats, m, coll, xform)
    _lamps_object('SeatedLamps', lamps, m['seatedlamp'], coll, xform, seated)
    seated.location = origin
    seated.hide_render = False
    out['seated'] = seated

    for ob in list(rcoll.all_objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.collections.remove(rcoll)
    for name in ('RacksLying', 'RacksSeated'):
        a = bpy.data.actions.get(name)
        if a:
            bpy.data.actions.remove(a)
    return out


def build_tow_loop(m, fallen):
    """The recovery strap on its shoulder harness: a webbing band round its shoulders, a strap up over its
    back, and a red loop with a padded grip standing just above the back of its head, at 0.44, for D-17's
    claws. Added to FallenCourier's own mesh so it moves with it. Returns the grip's centre in world space."""
    me = fallen.data
    bm = bmesh.new()
    bm.from_mesh(me)
    head_end = max(v.co.x for v in bm.verts if v.co.z > 0.25 and abs(v.co.y) < 0.17)   # the crown
    back = LOOP_Z
    gx = head_end + 0.03                                                      # just past its crown
    grip = Vector((gx, 0.0, LOOP_Z))
    strap_i = len(me.materials)
    red_i = strap_i + 1
    # The harness: a band over its shoulders (the top flank, on its side), and the strap from it along
    # the back of its head to the crown.
    sx = head_end - 0.33
    top = max((v.co.z for v in bm.verts if abs(v.co.x - sx) < 0.03 and abs(v.co.y) < 0.2), default=0.45)
    ys = [v.co.y for v in bm.verts if abs(v.co.x - sx) < 0.03 and v.co.z > top - 0.06]
    add_box(bm, (sx, (min(ys) + max(ys)) / 2, top + 0.004), (0.04, max(ys) - min(ys) + 0.016, 0.008), mat=strap_i)
    back_y = max(v.co.y for v in bm.verts if head_end - 0.2 < v.co.x < head_end and v.co.z > 0.2)
    pts = [Vector((sx, max(ys) - 0.02, top + 0.006)), Vector((sx + 0.06, back_y + 0.006, top - 0.04)),
           Vector((head_end - 0.03, back_y + 0.006, LOOP_Z - 0.02))]
    for a, b in zip(pts, pts[1:]):
        d = b - a
        add_box(bm, (a + b) / 2, (d.length + 0.01, 0.006, 0.045), mat=strap_i,
                rot=Vector((1, 0, 0)).rotation_difference(d.normalized()).to_matrix().to_4x4())
    # The loop: the strap's red end wraps round the crown's back corner; two red tabs from it to a padded
    # red grip across (along y), just past the crown.
    y0, y1 = grip.y - 0.1, grip.y + 0.1
    base = Vector((head_end - 0.005, (back_y + y1) / 2, LOOP_Z - 0.02))
    add_box(bm, base, (0.03, back_y - y1 + 0.04, 0.045), mat=red_i)
    for y in (y0, y1):
        a, b = Vector((head_end - 0.02, y, LOOP_Z)), Vector((gx, y, LOOP_Z))
        add_box(bm, (a + b) / 2, (b.x - a.x + 0.02, 0.012, 0.03), mat=red_i)
    add_box(bm, (head_end - 0.01, grip.y, LOOP_Z), (0.012, y1 - y0 + 0.012, 0.03), mat=red_i)
    add_cyl(bm, (gx, y0 - 0.012, LOOP_Z), (gx, y1 + 0.012, LOOP_Z), 0.016, seg=12, mat=red_i)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(m['rubber'])
    me.materials.append(m['red'])
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.set_sharp_from_angle(angle=math.radians(40))
    return fallen.matrix_world @ grip


def build_dust(m, fallen, coll):
    """Dust on the floor round it, with its clean outline under it: hidden until it is dragged away."""
    mw = fallen.matrix_world
    tris = []
    for p in fallen.data.polygons:
        vs = [mw @ fallen.data.vertices[i].co for i in p.vertices]
        if min(v.z for v in vs) < 0.12:
            tris.append([(v.x, v.y) for v in vs])
    x0, x1 = FALLEN[0] - 0.6, FALLEN[0] + 0.6
    y0, y1 = FALLEN[1] - 0.36, FALLEN[1] + 0.4
    path = os.path.join(TEX, 'fallen_dust.png')
    make_dust_outline(path, tris, (x0, y0, x1, y1))         # drawn each build: it follows the pose
    mat = _image_material('DustOutline', path, rough=0.95, alpha=True)
    z = 0.0015
    _plane('FallenDust', mat, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], coll)


# --------------------------------------------------------------------------
# The charging bay
# --------------------------------------------------------------------------

def _arm_mesh(m, coll, name, x, py, pz):
    """One cradle arm, modelled holding the seated courier, its origin on its shoulder pivot. A hub on
    the axle, a flat bar down and forward to the cup, a rubber-lined cup with two copper contacts."""
    cup = Vector((0.0, (SEATED_Y - 0.045) - py, seated_hold_z() - pz))
    s = 1 if x > CRADLE_X else -1               # outward
    bm = bmesh.new()
    add_cyl(bm, (-s * 0.03, 0, 0), (s * 0.05, 0, 0), 0.045, seg=20)
    add_cyl(bm, (s * 0.05, 0, 0), (s * 0.07, 0, 0), 0.028, seg=16)
    d = cup.normalized()
    mid = cup * 0.55 + Vector((0, -0.03, 0.02))
    for a, b, r0, r1 in ((Vector((0, 0, 0)), mid, 0.03, 0.026), (mid, cup - d * 0.04, 0.026, 0.022)):
        add_cyl(bm, a, b, r0, r1, seg=12)
    # The cup: a curved pad facing in, against the pod's side.
    rnd_axis = Vector((0, -d.z, d.y))           # along the pod's side, across the arm
    for k in range(5):
        t = (k - 2) / 2
        p = cup + rnd_axis * (0.05 * t) + Vector((s * 0.012 * t * t, 0, 0))
        add_box(bm, p + Vector((s * 0.018, 0, 0)), (0.02, 0.03, 0.03), mat=1,
                rot=Matrix.Rotation(-math.atan2(d.y, -d.z), 4, 'X'))
    add_box(bm, cup + Vector((s * 0.04, 0, 0)), (0.03, 0.06, 0.14), rot=Matrix.Rotation(-math.atan2(d.y, -d.z), 4, 'X'))
    for t in (-0.035, 0.035):
        p = cup + rnd_axis * t
        add_cyl(bm, p + Vector((s * 0.006, 0, 0)), p + Vector((-s * 0.006, 0, 0)), 0.008, seg=10, mat=2)
    ob = _obj(name, bm, [m['bayenamel'], m['rubber'], m['copper']], coll)
    ob.location = (x, py, pz)
    return ob


def build_bay(m, coll):
    py, pz = cradle_pivot()
    x0, x1 = PLATE
    y0, y1 = PLATE_Y
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2

    # The plate: steel, a courier pictogram at its front, origin at its top centre.
    pic = os.path.join(TEX, 'bay_pictogram.png')
    if not os.path.exists(pic):
        make_bay_pictogram(pic)
    picmat = _image_material('BayPictogram', pic, rough=0.5)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    add_box(bm, (0, 0, -0.015), (x1 - x0 - 0.03, y1 - y0 - 0.03, 0.03))
    for k in range(6):                                          # tread ribs
        add_box(bm, (-0.3 + k * 0.12, (y1 - y0) / 2 - 0.2 - cy + cy, 0.0008), (0.06, 0.24, 0.0016))
    h = 0.2
    py0 = y0 + 0.06 + h - cy
    _quad(bm, uv, [(-h, py0 - h, 0.0012), (h, py0 - h, 0.0012), (h, py0 + h, 0.0012), (-h, py0 + h, 0.0012)], mat=1)
    plate = _obj('BayPlate', bm, [m.get('plate', m['steel']), picmat], coll)
    plate.location = (cx, cy, PLATE_TOP)
    bm = bmesh.new()                                            # its rim, and the well it sinks into
    for x in (x0 - 0.01, x1 + 0.01):
        add_box(bm, (x, cy, 0.003), (0.04, y1 - y0 + 0.06, 0.006))
    for y in (y0 - 0.01, y1 + 0.01):
        add_box(bm, (cx, y, 0.003), (x1 - x0 + 0.06, 0.04, 0.006))
    _obj('BayPlateRim', bm, [m['steel']], coll)

    # The back frame: uprights, the shoulder housings, a header with the cold strip light, the backboard.
    fx = (CRADLE_X - 0.5, CRADLE_X + 0.5)
    bm = bmesh.new()
    for x in fx:
        add_box(bm, (x, PIVOT_Y, 0.95), (0.08, 0.1, 1.9))
        add_box(bm, (x, PIVOT_Y, 0.02), (0.2, 0.22, 0.04))
    add_box(bm, (CRADLE_X, PIVOT_Y, 1.93), (1.12, 0.12, 0.1))
    for s in (-1, 1):                                           # shoulder housings from the uprights in to the axles
        ax = CRADLE_X + s * ARM_DX
        add_box(bm, ((ax + fx[0 if s < 0 else 1]) / 2 + s * 0.04, PIVOT_Y, pz), (abs(fx[0 if s < 0 else 1] - ax) - 0.06, 0.09, 0.12))
        add_cyl(bm, (ax + s * 0.08, PIVOT_Y, pz), (ax + s * 0.2, PIVOT_Y, pz), 0.07, seg=24)
    for i in range(2):                                          # backboard: two enamel panels
        rounded_box((0.98, 0.05, 0.96), (CRADLE_X, FRAME_Y, 0.5 + i * 0.98), p=10, cuts=3,
                    dents=((0.002, 3.0),), seed=60 + i, bm=bm, mat=0)
    _obj('BayFrame', bm, [m['bayenamel']], coll)
    bm = bmesh.new()
    add_box(bm, (CRADLE_X, PIVOT_Y - 0.08, 1.86), (0.9, 0.08, 0.06))
    for x in (CRADLE_X - 0.42, CRADLE_X + 0.42):
        add_box(bm, (x, PIVOT_Y - 0.06, 1.88), (0.03, 0.1, 0.06))
    _obj('BayLightFixture', bm, [m['steel']], coll)
    bm = bmesh.new()
    add_box(bm, (CRADLE_X, PIVOT_Y - 0.09, 1.825), (0.84, 0.05, 0.015))
    _obj('BayLight', bm, [m['baylight']], coll)
    _plane('BaySign', picmat, [(CRADLE_X - 0.17, FRAME_Y - 0.026, 1.24), (CRADLE_X + 0.17, FRAME_Y - 0.026, 1.24),
                               (CRADLE_X + 0.17, FRAME_Y - 0.026, 1.58), (CRADLE_X - 0.17, FRAME_Y - 0.026, 1.58)], coll)

    for side, s in (('L', -1), ('R', 1)):
        _arm_mesh(m, coll, f'CradleArm{side}', CRADLE_X + s * ARM_DX, py, pz)

    # The bay door: a sliding shutter in the hall's end wall, origin at its base so the game lifts it.
    bm = bmesh.new()
    n = int(DOOR_H / 0.08)
    for k in range(n):
        add_box(bm, (0, 0, 0.04 + k * 0.08), (0.05, DOOR_W, 0.074))
    add_box(bm, (0, 0, 0.012), (0.07, DOOR_W, 0.024))
    door = _obj('BayDoor', bm, [m['bayenamel']], coll)
    door.location = (DOOR_X, 0, 0)
    bm = bmesh.new()
    for y in (-DOOR_W / 2 - 0.05, DOOR_W / 2 + 0.05):
        add_box(bm, (DOOR_X, y, (DOOR_H + 0.15) / 2), (0.24, 0.1, DOOR_H + 0.15))
    add_box(bm, (DOOR_X, 0, DOOR_H + 0.08), (0.26, DOOR_W + 0.2, 0.14))
    _obj('BayDoorFrame', bm, [m['bayenamel']], coll)
    bm = bmesh.new()
    add_box(bm, (DOOR_X - 0.18, 0.5, DOOR_H + 0.26), (0.12, 0.26, 0.22))              # the door motor
    add_cyl(bm, (DOOR_X - 0.18, 0.36, DOOR_H + 0.26), (DOOR_X - 0.18, 0.3, DOOR_H + 0.26), 0.05, seg=16)
    add_box(bm, (DOOR_X - 0.135, -0.8, DOOR_H + 0.26), (0.03, 0.34, 0.14))           # lamp panel, facing the camera
    _obj('BayDoorMotor', bm, [m['steel']], coll)
    for i, mat in enumerate(m['baylamp']):
        bm = bmesh.new()
        add_sphere(bm, (DOOR_X - 0.155, -0.9 + i * 0.1, DOOR_H + 0.26), 0.022, seg=12, scale=(0.6, 1, 1))
        add_sphere(bm, (DOOR_X - 0.135, -0.9 + i * 0.1, DOOR_H + 0.26), 0.022, seg=12, scale=(1, 1, 1))
        _obj(f'BayLamp{i}', bm, [mat], coll)
    # Lamps also face the camera: three small lenses on the panel's front edge.
    bm = bmesh.new()
    add_box(bm, (DOOR_X - 0.135, -0.975, DOOR_H + 0.26), (0.05, 0.02, 0.18))
    _obj('BayLampHood', bm, [m['steel']], coll)

    # Linkage: the plate's cable to a junction box at the frame's foot; a conduit up the frame to the
    # shoulder motors, and another along the floor behind the lane to the door post and up to its motor.
    jx = fx[1] + 0.12
    bm = bmesh.new()
    add_box(bm, (jx, PIVOT_Y + 0.02, 0.12), (0.14, 0.1, 0.2))
    run = [Vector((jx, PIVOT_Y + 0.05, 0.03)), Vector((DOOR_X - 0.2, PIVOT_Y + 0.05, 0.03)),
           Vector((DOOR_X - 0.2, PIVOT_Y + 0.05, DOOR_H + 0.15)), Vector((DOOR_X - 0.2, 0.62, DOOR_H + 0.26))]
    for a, b in zip(run, run[1:]):
        add_cyl(bm, a, b, 0.014, seg=8)
    for t in (0.25, 0.5, 0.75):
        p = run[0].lerp(run[1], t)
        add_box(bm, p, (0.03, 0.05, 0.035))
    up = [Vector((fx[1] + 0.06, PIVOT_Y + 0.06, 0.2)), Vector((fx[1] + 0.06, PIVOT_Y + 0.06, pz)),
          Vector((CRADLE_X + ARM_DX + 0.2, PIVOT_Y + 0.06, pz))]
    for a, b in zip(up, up[1:]):
        add_cyl(bm, a, b, 0.012, seg=8)
    add_cyl(bm, (fx[0] - 0.06, PIVOT_Y + 0.06, pz), (CRADLE_X - ARM_DX - 0.2, PIVOT_Y + 0.06, pz), 0.012, seg=8)
    _obj('BayLinkage', bm, [m['steel']], coll)
    d17.tube('BayPlateCable', [Vector((x1 - 0.05, y1 - 0.05, 0.004)), Vector((x1 + 0.05, PIVOT_Y - 0.05, 0.01)),
                               Vector((jx - 0.05, PIVOT_Y + 0.0, 0.05))], 0.012, 0, [m['rubber']], coll)
    # The top run across the header, so the arms' conduit visibly joins the door's.
    bm = bmesh.new()
    add_cyl(bm, (fx[0] - 0.06, PIVOT_Y + 0.06, pz), (fx[0] - 0.06, PIVOT_Y + 0.06, 1.99), 0.012, seg=8)
    add_cyl(bm, (fx[0] - 0.06, PIVOT_Y + 0.06, 1.99), (fx[1] + 0.06, PIVOT_Y + 0.06, 1.99), 0.012, seg=8)
    add_cyl(bm, (fx[1] + 0.06, PIVOT_Y + 0.06, 1.99), (fx[1] + 0.06, PIVOT_Y + 0.06, pz), 0.012, seg=8)
    _obj('BayConduit', bm, [m['steel']], coll)

    # Hazard edge along the lane's back line, the passage threshold, and a service tag on the frame.
    bm = bmesh.new()
    add_box(bm, ((x1 + 0.1 + END_WALL[0]) / 2, -0.38, 0.0015), (END_WALL[0] - x1 - 0.1, 0.07, 0.003))
    add_box(bm, ((HALL_X0 + x0 - 0.1) / 2, -0.38, 0.0015), (x0 - 0.1 - HALL_X0, 0.07, 0.003))
    _obj('RacksSafetyLine', bm, [m['yellow']], coll)


def build_set(dl01, m, coll):
    racks_materials(m)
    open_old_end(dl01)
    build_hall(m, coll)
    build_bay(m, coll)
    couriers = build_couriers(dl01, m, coll)
    grip = build_tow_loop(m, couriers['fallen'])
    build_dust(m, couriers['fallen'], coll)
    return dict(grip=grip, **couriers)


# --------------------------------------------------------------------------
# D-17's clip
# --------------------------------------------------------------------------

TOUCH_FRAMES = 52
# Rig space (D-17 facing -y; in the game he faces -x, back toward the bay he dragged it from, so the seated
# courier is at his front right). The claw tip lands here, on top of its head, near its left side:
TOUCH_TIP = Vector((-0.34, -0.36, 0.558))
TOUCH_DIR = Vector((-0.45, -0.8, -0.35)).normalized()      # the claw laid along its head, pointing on
TOUCH_REACH = 0.104                                          # wrist to claw tip, along the claw
TOUCH_TRIM = Vector((0.0, 0.0, 0.014))                       # measured: the solved claw tip falls this short
TOUCH_YAW = 28.0                                             # he opens toward the camera as he reaches (root, degrees)
TOUCH_HOVER = Vector((0.01, 0.045, 0.022))                   # off its head, before and after
# Where to stand him (world, facing -x) for that, with SeatedCourier as built: root at
TOUCH_ROOT = (44.92, 0.0)                                    # the tip then lands at (44.56, 0.34, 0.558)


def clip_touch_head(dl01, arm):
    """After the cradle takes the courier: he turns his head to it, reaches up slowly, lays his right claw
    on top of its head and leaves it there a moment, head tilted. Then lets go, and his head comes up."""
    track, spring, Clip, REST, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.REST_WRIST, dl01.CARRY
    reach = dl01.dl02.reach
    c = Clip(arm, 'TouchHead', TOUCH_FRAMES)
    rest_rot = (-24.0, -6.0, -10.0)
    for frame in range(1, TOUCH_FRAMES + 1):
        f = frame - 1
        # The root turns; the courier's head stays where it is in the game's frame.
        yaw = track([(0, 0), (16, TOUCH_YAW), (40, TOUCH_YAW), (50, 0)], f)
        unturn = Matrix.Rotation(math.radians(-yaw), 3, 'Z')
        tip, along = unturn @ TOUCH_TIP, unturn @ TOUCH_DIR
        laid = aim(along)
        on = tip - along * TOUCH_REACH + TOUCH_TRIM             # the wrist with the claw on its head
        lean = track([(0, 0), (16, 1), (38, 1), (48, 0)], f)
        body = (-0.012 * lean, -0.04 * lean, -0.01 * lean)
        rot = (track([(0, 0), (16, 5), (30, 6), (40, 5), (50, 0)], f), -3.0 * lean, 0.0)
        # The right claw: up from his side and out, round the front corner of the pod, onto its head.
        out = track([(4, 0), (18, 1), (40, 1), (48, 0)], f)
        down = track([(16, 0), (21, 1), (38, 1), (42, 0)], f)                # from the hover onto the head
        press = 0.004 * track([(27, 0), (30, 1), (34, 0)], f)                 # the faintest press, once
        target = on + TOUCH_HOVER * (1 - down) - Vector((0, 0, press))
        held = reach({1: REST[1] + CARRY[1], -1: target}, body, rot, REST)[-1]
        bow = Vector((-0.05, 0.0, 0.0)) * math.sin(math.pi * min(1.0, out)) * (1 - down)   # out round his head
        hands = {1: CARRY[1] + Vector((0.0, -0.004 * lean, 0.004 * lean)),
                 -1: dl01.reach_around(CARRY[-1], held, out) + bow}
        k = track([(4, 0), (16, 1), (40, 1), (48, 0)], f)
        hand_rot = {'L': (-24.0, 6.0, 10.0), 'R': tuple(a + (b - a) * k for a, b in zip(rest_rot, laid))}
        claw = track([(4, CLAW_REST_OPEN['R']), (14, 14), (20, 4), (38, 4), (42, 12), (50, CLAW_REST_OPEN['R'])], f)
        # Head: turns to it and looks down at it, tilts while his claw is there, comes back up after.
        head = (track([(0, 0), (8, 6), (18, 6), (24, 10), (38, 12), (44, 4), (52, -2)], f),
                track([(18, 0), (26, 6), (38, 6), (46, 0)], f),
                track([(0, 0), (8, -10), (16, -24), (40, -24), (48, -4), (52, 0)], f))
        antenna = [(track([(0, 0), (10, 8), (24, 18), (38, 18), (44, 4)], f) * (0.7 + 0.2 * i)
                    - spring(f, 44, 6 * (1 + 0.3 * i), decay=6), 0) for i in range(3)]
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands, hand_rot=hand_rot,
               claws={'L': CLAW_REST_OPEN['L'], 'R': claw}, elbows={'R': min(1.0, 2 * out)}, yaw=yaw)
    c.done()


def add_clips(dl01, arm):
    clip_touch_head(dl01, arm)
