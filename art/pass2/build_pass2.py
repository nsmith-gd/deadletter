"""Chapter 1, pass 2 (docs/chapter1_pass2_plan.md): danger from the world, and D-17's clips for it.

Built in world coordinates (the OFF2..OFF4 offsets are already applied), after every other scene. Other builders'
objects are only changed here, by name (moved, cut or extended), never in their own files.

  DL-02  FrankingPress: a C-frame stamping press beside the tube station, still running its routine. PressRam (the
         game moves it in z), PressLamp (the tell, emissive), PressFlywheel (the game may spin it).
  DL-03  WeightRoomDrain and DragMarks: wet drag marks from a floor drain across the weight room and back (a sign).
  DL-04  FallenCourier and SeatedCourier lose their right leg below the knee: a bitten stump, torn cable ends.
  DL-06  HeapWeight1 moves to the far end of the sorting floor, by the pit edge. HeapSump: a cistern of dark water
         in the pit under the chute's head, where the White rolls once. GalleryCollapse: a walkway panel just past
         the gate, hinged at its left end, that gives way behind him (the deck and rails are cut to fit it).
  DL-07  Sump7Water: the goods-lift shaft flooded to 1.75 below the landing; the platform rests under it.
  DL-08  CwTray on CageCounterweight (one slab out of its frame, the top bar replaced by a bail), CwPlate0/1 on the
         upper landing, CageSump under the cage, TunnelCable over TunnelWet in the antechamber, with two arc points.

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y.
Game coordinates are (x, z, -y).
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
from build_d17 import (add_box, add_cyl, add_sphere, add_torus, emission_material, worn_material,
                       simple_material, smoothstep, ease_back, SIDES, CLAW_REST_OPEN, _key)

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')

# ---------------------------------------------------------------------------------------------------------
# Shared with the game (world x; Blender z is the game's y). See the report for the game-side behaviours.
# ---------------------------------------------------------------------------------------------------------
# DL-02 The franking press, on the lane just before the tube letter (SH.tubeX 14.6).
PRESS_X = 13.95                       # the ram's centre line
PRESS_RAM = (0.32, (-0.30, 0.24), 0.26)   # x size, y range, height; origin at the die face's centre
PRESS_REST, PRESS_DOWN = 0.98, 0.055  # die face height: up (rest), and down on the bed
PRESS_BED = (13.74, 14.16, (-0.36, 0.30), 0.045)   # x0, x1, y range, top (a step he walks: under 0.07)
PRESS_CROWN = (1.62, 1.98)
PRESS_COL_Y = (0.28, 0.60)            # the C-frame's column behind the lane, against the passage wall
# DL-03 The drain and the drag marks.
DRAIN = (26.35, 0.36)                 # world x, y of the grate's centre (the back of the lane)
DRAG = (25.7, 28.0, -0.9, 0.52)       # the decal: x0, x1, y0, y1
# DL-06 The Heap.
HEAP_WEIGHT1_X = 57.05                # was 52.85; the slide drops him at 56.6, the guard rail is at 57.32
SUMP6 = (57.5, 60.05, -1.7, 0.0)      # the cistern: x0, x1, y0, y1 (outside faces)
SUMP6_WALL, SUMP6_TOP, SUMP6_WATER, SUMP6_FLOOR = 0.12, -0.62, -0.75, -2.4
COLLAPSE = (66.95, 68.05)             # the panel that gives way, world x (gallery deck at 1.6)
COLLAPSE_Y = (-0.52, 0.86)            # the full width of the deck (the residential wall stays, at 0.87)
COLLAPSE_HINGE = (66.95, 0.0, 1.57)   # its origin: the hinge line along y, mid-thickness of the deck
GALLERY_OFF = 21.0                    # art/dl03's gallery is built in its own x and moved by OFF3
# DL-07 Lift 2's shaft (art/dl04 52.8..55.3, moved by OFF3).
SHAFT7 = (73.8, 76.3)
SUMP7_WATER, SUMP7_BACK = -0.15, 0.95
# DL-08 The cage (art/cage, X0 85.6).
CAGE_X0 = 85.6
CAGE_SHAFT = (89.2, 90.8)
CAGE_PIT_Z, CAGE_BACK = -0.6, 1.05
CAGE_SUMP_WATER = 0.05                # the cage on its buffers (floor -0.1) stands 0.15 deep in it
UPPER_LANDING = 3.4
PLATE = (0.10, 0.14, 0.115)           # CwPlate: x, y, body height; the bail's top is at 0.21, as on the weights
PLATES_AT = ((88.55, 14.0), (88.95, -10.0))   # world x on the upper landing, yaw (degrees)
CW_SLAB_GONE = 6                      # the counterweight's top slab (of 7) is the one missing
TRAY_SEATS = (-0.05, 0.05)            # where the plates sit in the counterweight's frame (cw-local x)
TRAY_FLOOR = -0.235                   # cw-local z of the plates' base: on the tray's floor plate, on slab 5
# DL-08 The antechamber (lower landing, floor 1.6): the downed cable over a wet patch.
WET = (92.85, 94.3, -1.0, 1.3)
DRY_PLATE = (93.42, 93.72)            # a raised hatch cover between the two arcs: dry, a place to wait
ARC_A = ((93.15, 0.0, 1.635), (93.33, -0.06, 1.602))     # Blender (x, y, z): from the split insulation...
ARC_B = ((94.07, 0.42, 1.632), (93.87, 0.04, 1.602))     # ...and from the frayed end, both to the wet floor


def _obj(name, bm, mats, coll, sharp=35):
    return d17.mesh_object(name, bm, mats, coll, sharp=sharp)


def bx(bm, x, y, z, mat=0, rot=None):
    """A box from (min, max) ranges."""
    return add_box(bm, ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2),
                   (x[1] - x[0], y[1] - y[0], z[1] - z[0]), mat=mat, rot=rot)


def _ry(a):
    return Matrix.Rotation(a, 4, 'Y')


def _rz(a):
    return Matrix.Rotation(a, 4, 'Z')


def _prism(bm, pts, y0, y1, mat=0):
    """A prism: the (x, z) outline `pts` from y0 to y1."""
    a = [bm.verts.new((x, y0, z)) for x, z in pts]
    b = [bm.verts.new((x, y1, z)) for x, z in pts]
    faces = [bm.faces.new(a[::-1]), bm.faces.new(b)]
    n = len(pts)
    for i in range(n):
        faces.append(bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])))
    for f in faces:
        f.material_index = mat


def _clip(poly, x0, x1, z0, z1):
    """Sutherland-Hodgman: a convex (x, z) polygon clipped to a rectangle."""
    def cut(pts, inside, inter):
        out = []
        for i, p in enumerate(pts):
            q = pts[i - 1]
            if inside(p):
                if not inside(q):
                    out.append(inter(q, p))
                out.append(p)
            elif inside(q):
                out.append(inter(q, p))
        return out

    def ix(v):
        return lambda q, p: (v, q[1] + (p[1] - q[1]) * (v - q[0]) / (p[0] - q[0]))

    def iz(v):
        return lambda q, p: (q[0] + (p[0] - q[0]) * (v - q[1]) / (p[1] - q[1]), v)
    for inside, inter in ((lambda p: p[0] >= x0, ix(x0)), (lambda p: p[0] <= x1, ix(x1)),
                          (lambda p: p[1] >= z0, iz(z0)), (lambda p: p[1] <= z1, iz(z1))):
        poly = cut(poly, inside, inter)
        if not poly:
            break
    return poly


def _stripes(bm, x0, x1, z0, z1, y, width, mat, depth=0.004):
    """Diagonal hazard bands on a face at plane y (facing -y): every other band of `width`, at 45 degrees."""
    k = -int((z1 - z0) / width) - 2
    while x0 + k * width < x1 + (z1 - z0):
        a = x0 + k * width
        band = [(a, z0), (a + width, z0), (a + width + (z1 - z0), z1), (a + (z1 - z0), z1)]
        poly = _clip(band, x0, x1, z0, z1)
        if len(poly) >= 3:
            _prism(bm, poly, y - depth, y, mat)
        k += 2


def _plane(name, mat, x, y, z, coll):
    """A flat decal quad (UVs 0..1), facing up."""
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new('UVMap')
    vs = [bm.verts.new((x[0], y[0], z)), bm.verts.new((x[1], y[0], z)), bm.verts.new((x[1], y[1], z)),
          bm.verts.new((x[0], y[1], z))]
    f = bm.faces.new(vs)
    for lp, c in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uv].uv = c
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def _image_material(name, path, rough=0.6, alpha=False):
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


def _islands(bm):
    """Connected vertex islands (each add_box/add_cyl is one), with their bounding boxes."""
    bm.verts.index_update()
    seen, out = set(), []
    for v in bm.verts:
        if v.index in seen:
            continue
        stack, isl = [v], []
        seen.add(v.index)
        while stack:
            a = stack.pop()
            isl.append(a)
            for e in a.link_edges:
                b = e.other_vert(a)
                if b.index not in seen:
                    seen.add(b.index)
                    stack.append(b)
        lo = Vector((min(p.co.x for p in isl), min(p.co.y for p in isl), min(p.co.z for p in isl)))
        hi = Vector((max(p.co.x for p in isl), max(p.co.y for p in isl), max(p.co.z for p in isl)))
        out.append((isl, lo, hi))
    return out


def _near(a, b, tol=0.006):
    return all(abs(p - q) <= tol for p, q in zip(a, b))


def _edit_mesh(ob, fn, sharp=35):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    fn(bm)
    bm.to_mesh(ob.data)
    bm.free()
    me = ob.data
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.set_sharp_from_angle(angle=math.radians(sharp))
    me.update()


def _mat_index(me, mat):
    for i, s in enumerate(me.materials):
        if s == mat:
            return i
    me.materials.append(mat)
    return len(me.materials) - 1


# ---------------------------------------------------------------------------------------------------------
# Textures and materials
# ---------------------------------------------------------------------------------------------------------

def make_textures():
    from PIL import Image, ImageDraw, ImageFilter
    os.makedirs(TEX, exist_ok=True)
    rnd = random.Random(611)

    # Drag marks: a broad damp smear from the drain out across the floor in a loop and back in, with the
    # toe-scrapes of four small limbs either side of it. The decal spans DRAG; the drain is at its back left.
    W, H = 1024, 640
    x0, x1, y0, y1 = DRAG
    to_px = lambda x, y: ((x - x0) / (x1 - x0) * W, (y1 - y) / (y1 - y0) * H)   # noqa: E731
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, 'RGBA')
    pts = [(DRAIN[0], DRAIN[1] - 0.05), (26.5, 0.0), (26.85, -0.45), (27.35, -0.62), (27.75, -0.4), (27.7, -0.05),
           (27.3, 0.15), (26.85, 0.22), (26.45, 0.32)]
    path = []
    for (ax, ay), (bxx, byy) in zip(pts, pts[1:]):
        for k in range(12):
            t = k / 12
            path.append((ax + (bxx - ax) * t, ay + (byy - ay) * t))
    path.append(pts[-1])
    smooth = []
    for i in range(len(path)):
        js = [path[min(len(path) - 1, max(0, i + o))] for o in range(-4, 5)]
        smooth.append((sum(p[0] for p in js) / len(js), sum(p[1] for p in js) / len(js)))
    for i, (x, y) in enumerate(smooth):                         # the body's smear: soft, wide, uneven
        px, py = to_px(x, y)
        r = 34 + 10 * math.sin(i * 0.37) + rnd.uniform(-4, 4)
        d.ellipse((px - r, py - r * 0.75, px + r, py + r * 0.75), fill=(12, 11, 9, 62))
    for i, (x, y) in enumerate(smooth):                         # a darker, wetter core
        px, py = to_px(x, y)
        r = 15 + 6 * math.sin(i * 0.53 + 1)
        d.ellipse((px - r, py - r * 0.7, px + r, py + r * 0.7), fill=(6, 6, 5, 95))
    for i in range(6, len(smooth) - 6, 7):                     # toe scrapes: three short claws, both sides
        (ax, ay), (bxx, byy) = smooth[i - 2], smooth[i + 2]
        tx, ty = bxx - ax, byy - ay
        ln = math.hypot(tx, ty) or 1
        tx, ty = tx / ln, ty / ln
        nx, ny = -ty, tx
        for side in (-1, 1):
            cx, cy = smooth[i][0] + side * nx * 0.16, smooth[i][1] + side * ny * 0.16
            for toe in (-1, 0, 1):
                sx, sy = cx + toe * 0.018 * tx, cy + toe * 0.018 * ty
                ex, ey = sx - tx * 0.07 + side * nx * 0.025 * toe, sy - ty * 0.07 + side * ny * 0.025 * toe
                d.line((*to_px(sx, sy), *to_px(ex, ey)), fill=(5, 5, 4, 210), width=5)
    for k in range(40):                                          # drips and dabs along the way
        x, y = smooth[rnd.randrange(len(smooth))]
        px, py = to_px(x + rnd.uniform(-0.2, 0.2), y + rnd.uniform(-0.2, 0.2))
        r = rnd.uniform(3, 9)
        d.ellipse((px - r, py - r, px + r, py + r), fill=(10, 10, 9, 70))
    img.filter(ImageFilter.GaussianBlur(2.2)).save(os.path.join(TEX, 'drag_marks.png'))

    # The wet patch in the antechamber: water across the floor from a split pipe, dark and glossy, ragged edged.
    W = H = 512
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, 'RGBA')
    for k in range(70):
        a = rnd.uniform(0, 2 * math.pi)
        rr = rnd.uniform(0, 0.33) ** 0.8
        cx, cy = W * (0.5 + rr * math.cos(a) * 0.95), H * (0.52 + rr * math.sin(a) * 0.8)
        r = rnd.uniform(40, 95)
        d.ellipse((cx - r, cy - r * 0.8, cx + r, cy + r * 0.8), fill=(5, 6, 7, 80))
    img = img.filter(ImageFilter.GaussianBlur(6))
    d = ImageDraw.Draw(img, 'RGBA')
    for k in range(28):                                          # splashes off the edge
        cx, cy = rnd.uniform(40, W - 40), rnd.uniform(40, H - 40)
        r = rnd.uniform(3, 10)
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(5, 6, 7, 140))
    img.filter(ImageFilter.GaussianBlur(1.2)).save(os.path.join(TEX, 'tunnel_wet.png'))


def pass2_materials(m):
    # Shared names the other builders make; made here only if a partial build left them out.
    fallback = {
        'iron': lambda: worn_material('CastIron', base=(0.035, 0.034, 0.032), dirt=(0.05, 0.03, 0.018),
                                      chip=(0.13, 0.12, 0.1), rough=0.75, chip_rough=0.45, metallic=0.5),
        'plate': lambda: worn_material('PlateSteel', base=(0.11, 0.115, 0.11), dirt=(0.06, 0.04, 0.025),
                                       chip=(0.2, 0.19, 0.17), rough=0.55, chip_rough=0.4, metallic=0.7),
        'letters': lambda: worn_material('LetterPaper', base=(0.55, 0.52, 0.45), dirt=(0.3, 0.27, 0.2),
                                         chip=(0.62, 0.6, 0.55), rough=0.9, chip_rough=0.9, metallic=0.0),
        'shaft': lambda: simple_material('Shaft', (0.005, 0.005, 0.005), 0.9),
    }
    for k, make in fallback.items():
        if k not in m:
            m[k] = make()
    mud = bpy.data.materials.get('FloodMud')                    # art/dl05's (WORN in the game)
    m['mud'] = mud or worn_material('FloodMud', base=(0.062, 0.05, 0.036), dirt=(0.035, 0.028, 0.02),
                                    chip=(0.09, 0.076, 0.058), rough=0.95, chip_rough=0.85, metallic=0.0)
    cable = bpy.data.materials.get('Cable')
    m['cable'] = cable or simple_material('Cable', (0.014, 0.013, 0.012), 0.55)
    m['presslamp'] = emission_material('PressLamp', (1.0, 0.16, 0.08), 0.0)
    m['dragmarks'] = _image_material('DragMarksMat', os.path.join(TEX, 'drag_marks.png'), rough=0.25, alpha=True)
    m['wetpatch'] = _image_material('TunnelWetMat', os.path.join(TEX, 'tunnel_wet.png'), rough=0.12, alpha=True)


# ---------------------------------------------------------------------------------------------------------
# DL-02 The franking press
# ---------------------------------------------------------------------------------------------------------

def build_press(m, coll):
    """A C-frame stamping press, its column against the passage wall behind the lane and its crown over the
    lane; the ram strikes a bed on the lane. Still running: the flywheel turns, the ram stamps every few seconds."""
    px = PRESS_X
    rw, (ry0, ry1), rh = PRESS_RAM
    bx0, bx1, (by0, by1), btop = PRESS_BED
    cz0, cz1 = PRESS_CROWN
    cy0, cy1 = PRESS_COL_Y
    hx = 0.25                                                   # half-width of the column and crown
    # 0 depot green (cast frame), 1 steel, 2 iron, 3 rubber, 4 letters, 5 yellow (the bed's nosing), 6 red
    bm = bmesh.new()
    # The bed: a steel plate on the lane, an ink-black die pad on it, a nosed front edge.
    bx(bm, (bx0, bx1), (by0, by1), (0.0, btop - 0.008), 1)
    bx(bm, (px - 0.15, px + 0.15), (ry0 + 0.02, ry1 - 0.02), (btop - 0.008, btop), 3)
    for x in (bx0, bx1 - 0.02):                                 # bevelled ends, so it reads as a step
        bx(bm, (x, x + 0.02), (by0, by1), (0.0, btop - 0.012), 1)
    # The column: a cast C-frame standing behind the lane, ribbed, with its foot bolted down.
    bx(bm, (px - hx, px + hx), (cy0, cy1), (0.0, cz1), 0)
    bx(bm, (px - hx - 0.05, px + hx + 0.05), (cy0 - 0.08, cy1), (0.0, 0.08), 0)       # foot
    for s in (-1, 1):
        bx(bm, (px + s * hx - 0.02, px + s * hx + 0.02), (cy0 - 0.12, cy0), (0.08, cz0), 0)   # ribs facing the lane
        for z in (0.3, 0.9, 1.4):
            add_cyl(bm, (px + s * (hx - 0.06), cy0 - 0.005, z), (px + s * (hx - 0.06), cy0 - 0.03, z), 0.016, mat=2, seg=8)
    # The gibs the ram slides in, on the column's face.
    for s in (-1, 1):
        bx(bm, (px + s * (rw / 2 + 0.005) - 0.025, px + s * (rw / 2 + 0.005) + 0.025), (ry1, cy0), (btop + 0.05, cz0), 1)
    # The crown over the lane: a heavy head with a sleeve for the ram's screw.
    bx(bm, (px - hx, px + hx), (ry0 - 0.08, cy1), (cz0, cz1), 0)
    bx(bm, (px - hx - 0.02, px + hx + 0.02), (ry0 - 0.1, ry0 - 0.06), (cz0 - 0.02, cz0 + 0.06), 0)   # its lip
    add_cyl(bm, (px, (ry0 + ry1) / 2, cz1), (px, (ry0 + ry1) / 2, cz1 + 0.24), 0.07, mat=0, seg=16)
    add_cyl(bm, (px, (ry0 + ry1) / 2, cz1 + 0.24), (px, (ry0 + ry1) / 2, cz1 + 0.27), 0.09, mat=1, seg=16)
    # The flywheel's bearings and a motor on the crown, its belt down to the wheel.
    fy = 0.47
    for s in (-1, 1):
        bx(bm, (px - 0.03, px + 0.03), (fy + s * 0.06 - 0.02, fy + s * 0.06 + 0.02), (cz1, cz1 + 0.45), 1)
    add_cyl(bm, (px - 0.36, 0.36, cz1 - 0.2), (px - 0.36, 0.56, cz1 - 0.2), 0.11, mat=0, seg=16)     # the motor
    bx(bm, (px - 0.42, px - 0.26), (0.3, 0.6), (cz0 - 0.1, cz1 - 0.3), 0)
    add_cyl(bm, (px - 0.36, 0.3, cz1 - 0.2), (px - 0.36, 0.28, cz1 - 0.2), 0.05, mat=1, seg=12)
    for dz in (-0.04, 0.04):                                    # the belt: two runs, pulley to flywheel rim
        add_cyl(bm, (px - 0.36, 0.29, cz1 - 0.2 + dz), (px - 0.05, 0.4, cz1 + 0.45 + dz * 5), 0.008, mat=3, seg=6)
    # A conduit from the motor down the wall, and a guard rail of steel round the column's foot.
    add_cyl(bm, (px - 0.36, 0.58, cz1 - 0.3), (px - 0.36, 0.58, 0.1), 0.018, mat=1, seg=8)
    # Dressing: a wire tray of franked envelopes on the column's side, a few fallen on the floor.
    bx(bm, (px + hx, px + hx + 0.22), (cy0 + 0.02, cy1 - 0.02), (0.62, 0.64), 1)
    for k in range(6):
        r = random.Random(620 + k)
        add_box(bm, (px + hx + 0.11 + r.uniform(-0.04, 0.04), (cy0 + cy1) / 2, 0.66 + k * 0.012), (0.16, 0.11, 0.008), mat=4,
                rot=_rz(r.uniform(-0.25, 0.25)))
    for x, y, a in ((px + 0.36, -0.2, 0.5), (px + 0.48, 0.12, -0.3), (px - 0.33, 0.18, 1.2), (px + 0.05, -0.45, 0.2)):
        add_box(bm, (x, y, 0.003), (0.16, 0.11, 0.004), mat=4, rot=_rz(a))
    for k in range(3):                                          # envelopes on the bed, franked flat
        r = random.Random(630 + k)
        add_box(bm, (px + r.uniform(-0.1, 0.1), r.uniform(-0.15, 0.1), btop + 0.003 + k * 0.002), (0.16, 0.11, 0.003), mat=4,
                rot=_rz(r.uniform(-0.6, 0.6)))
    _obj('FrankingPress', bm, [m['depot_green'], m['steel'], m['iron'], m['rubber'], m['letters'], m['yellow'], m['red']], coll)

    # PressRam: the ram and its screw, origin at the die face's centre; the game moves it in z
    # (PRESS_REST up, PRESS_DOWN on the bed). Dark iron, red hazard bands on its front face.
    bm = bmesh.new()
    yc = (ry0 + ry1) / 2
    bx(bm, (-rw / 2, rw / 2), (ry0, ry1), (0.03, rh), 0)
    bx(bm, (-rw / 2 + 0.03, rw / 2 - 0.03), (ry0 + 0.03, ry1 - 0.03), (0.0, 0.03), 1)          # the die
    for k in range(5):                                          # the die's postmark rings, in relief
        add_torus(bm, (0, yc, 0.0), (0, 0, 1), 0.02 + k * 0.022, 0.003, mat=1, seg=24, rseg=4)
    bx(bm, (-rw / 2 - 0.01, rw / 2 + 0.01), (ry0 - 0.01, ry1 + 0.01), (rh - 0.04, rh), 1)        # the ram's cap
    for s in (-1, 1):                                           # shoes in the gibs
        bx(bm, (s * rw / 2 - 0.01, s * rw / 2 + 0.02 * s), (ry1 - 0.06, ry1 + 0.04), (0.06, rh - 0.04), 1)
    add_cyl(bm, (0, yc, rh), (0, yc, rh + 1.5), 0.045, mat=1, seg=14)                             # the screw
    for k in range(14):
        add_torus(bm, (0, yc, rh + 0.25 + k * 0.08), (0, 0, 1), 0.046, 0.006, mat=1, seg=12, rseg=4)
    _stripes(bm, -rw / 2, rw / 2, 0.05, rh - 0.05, ry0, 0.045, 2)
    ram = _obj('PressRam', bm, [m['iron'], m['steel'], m['red']], coll)
    ram.location = (px, 0.0, PRESS_REST)

    # PressLamp: the tell, a red lamp in a cage on the crown's front corner, lit a beat before each stroke.
    bm = bmesh.new()
    add_sphere(bm, (0, 0, 0), 0.032, seg=12, scale=(1, 0.8, 1))
    lamp = _obj('PressLamp', bm, [m['presslamp']], coll)
    lamp.location = (px + hx - 0.06, ry0 - 0.12, cz0 + 0.2)
    bm = bmesh.new()
    lx, ly, lz = lamp.location
    bx(bm, (lx - 0.05, lx + 0.05), (ly + 0.02, ly + 0.05), (lz - 0.05, lz + 0.05), 0)
    for k in range(3):
        a = k * math.pi / 3
        add_torus(bm, (lx, ly, lz), (math.cos(a), 0, math.sin(a)), 0.042, 0.003, mat=0, seg=12, rseg=3)
    _obj('PressLampCage', bm, [m['steel']], coll)

    # PressFlywheel: spoked, on its axle behind the screw; origin on the axle (along y). The game may turn it.
    bm = bmesh.new()
    R = 0.3
    add_torus(bm, (0, 0, 0), (0, 1, 0), R - 0.03, 0.035, seg=32, rseg=6)
    add_cyl(bm, (0, -0.06, 0), (0, 0.06, 0), 0.06, seg=14)
    for k in range(6):
        a = k * math.pi / 3
        add_box(bm, (math.cos(a) * R * 0.48, 0, math.sin(a) * R * 0.48), (R * 0.9, 0.03, 0.04), rot=_ry(-a))
    add_box(bm, (R - 0.06, 0, 0), (0.06, 0.06, 0.08), mat=1)                                         # a balance weight
    fw = _obj('PressFlywheel', bm, [m['iron'], m['steel']], coll)
    fw.location = (px, fy, cz1 + 0.45)


# ---------------------------------------------------------------------------------------------------------
# DL-03 The drain and the drag marks
# ---------------------------------------------------------------------------------------------------------

def build_drag_marks(m, coll):
    dx, dy = DRAIN
    bm = bmesh.new()
    bx(bm, (dx - 0.15, dx + 0.15), (dy - 0.11, dy + 0.11), (0.0005, 0.002), 1)              # the dark beneath
    for xs, ys in (((dx - 0.17, dx + 0.17), (dy - 0.13, dy - 0.11)), ((dx - 0.17, dx + 0.17), (dy + 0.11, dy + 0.13)),
                   ((dx - 0.17, dx - 0.15), (dy - 0.11, dy + 0.11)), ((dx + 0.15, dx + 0.17), (dy - 0.11, dy + 0.11))):
        bx(bm, xs, ys, (0.0, 0.008), 0)                                                    # the frame
    rot = _rz(math.radians(7))                                 # its grate pushed askew, as if something came up through it
    for k in range(7):
        x = -0.12 + k * 0.04
        add_box(bm, Vector((dx, dy + 0.015, 0.006)) + rot @ Vector((x, 0, 0)), (0.016, 0.22, 0.008), mat=0, rot=rot)
    _obj('WeightRoomDrain', bm, [m['iron'], m['shaft']], coll)
    x0, x1, y0, y1 = DRAG
    _plane('DragMarks', m['dragmarks'], (x0, x1), (y0, y1), 0.003, coll)


# ---------------------------------------------------------------------------------------------------------
# DL-04 The fallen courier's bitten leg
# ---------------------------------------------------------------------------------------------------------

def _probe_leg(dl01, racks, pose, bake=False):
    """Pose a spare rig like art/racks does, and read the posed right knee and ankle (rig space). With `bake`,
    also return the lying courier's rig-to-object transform, computed the same way art/racks does."""
    arm = d17.build_robot('Pass2Probe', (0, 0, 0), 0)
    rcoll = bpy.data.collections['Pass2Probe']
    xform = None
    if bake:
        body, mats, lamps = racks.bake_pose(dl01, arm, rcoll, 'Pass2ProbeLying', pose)
        rot = Matrix.Rotation(math.radians(90.0 + racks.LYING_TILT), 4, 'Y')
        ps = [rot @ v.co for v in body.verts]
        shift = Vector((-(min(p.x for p in ps) + max(p.x for p in ps)) / 2, 0.0, -min(p.z for p in ps)))
        xform = Matrix.Translation(shift) @ rot
        body.free()
        lamps.free()
        c = dl01.Clip(arm, 'Pass2ProbeHold', 1)
        c.pose(1, **pose)
        arm.animation_data.action = bpy.data.actions['Pass2ProbeHold']
    else:
        c = dl01.Clip(arm, 'Pass2ProbeHold', 1)
        c.pose(1, **pose)
        arm.animation_data.action = bpy.data.actions['Pass2ProbeHold']
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    pb = arm.pose.bones['shin.R']
    knee, ankle = arm.matrix_world @ pb.head, arm.matrix_world @ pb.tail
    arm.animation_data.action = None
    for ob in list(rcoll.all_objects):
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.collections.remove(rcoll)
    for name in ('Pass2ProbeLying', 'Pass2ProbeHold'):
        a = bpy.data.actions.get(name)
        if a:
            bpy.data.actions.remove(a)
    return knee, ankle, xform


def _bite(ob, to_rig, knee, ankle, m):
    """Remove the right leg below the knee (rig space via `to_rig`) and leave a bitten stump: a ragged ring of
    torn shell, a dark hollow, and a few torn cables. Returns the number of faces removed."""
    d = (ankle - knee).normalized()
    L = (ankle - knee).length
    cut = knee + d * 0.18 * L
    to_obj = to_rig.inverted()
    me = ob.data
    i_dark = _mat_index(me, m['plate'])                         # torn shell: bright bare metal at the bite
    i_hole = _mat_index(me, m['shaft'])
    i_cu = _mat_index(me, m['copper'])
    i_rub = _mat_index(me, m['rubber'])
    removed = [0]

    def edit(bm):
        dead = []
        for f in bm.faces:
            c = to_rig @ f.calc_center_median()
            if c.x > -0.03 or c.y > 0.1:
                continue
            if (c - cut).dot(d) <= 0.0:
                continue
            # within the shin and the foot below it
            t = (c - cut).dot(d)
            radial = (c - (cut + d * t)).length
            if (t < L * 0.95 and radial < 0.08) or (c - ankle).length < 0.14:
                dead.append(f)
        removed[0] = len(dead)
        bmesh.ops.delete(bm, geom=dead, context='FACES')
        loose = [v for v in bm.verts if not v.link_faces]
        bmesh.ops.delete(bm, geom=loose, context='VERTS')
        # The stump, built in rig space and taken to the object's.
        u = d.orthogonal().normalized()
        w = d.cross(u).normalized()
        rnd = random.Random(404)
        tmp = bmesh.new()
        n = 14
        ring = []
        for k in range(n):
            a = 2 * math.pi * k / n
            ring.append(cut + (u * math.cos(a) + w * math.sin(a)) * 0.034)
        for k in range(n):                                       # torn shell: teeth of uneven length
            a0, a1 = ring[k], ring[(k + 1) % n]
            mid = (a0 + a1) / 2
            out = (mid - cut).normalized()
            tip = mid + d * rnd.uniform(0.01, 0.035) * (1.7 if k % 3 == 0 else 1.0) + out * rnd.uniform(-0.002, 0.01)
            vs = [tmp.verts.new(p) for p in (a0 - d * 0.012, a1 - d * 0.012, tip)]
            vs2 = [tmp.verts.new(p + out * 0.004) for p in (a0 - d * 0.012, a1 - d * 0.012, tip)]
            for face in (vs, vs2[::-1], (vs[0], vs[1], vs2[1], vs2[0]), (vs[1], vs[2], vs2[2], vs2[1]), (vs[2], vs[0], vs2[0], vs2[2])):
                tmp.faces.new(face).material_index = i_dark
        disc = [tmp.verts.new(cut + d * 0.002 + (u * math.cos(2 * math.pi * k / n) + w * math.sin(2 * math.pi * k / n)) * 0.031)
                for k in range(n)]
        tmp.faces.new(disc).material_index = i_hole
        for k in range(5):                                       # torn cables, splayed, bare copper at their ends
            a = rnd.uniform(0, 2 * math.pi)
            base = cut - d * 0.01 + (u * math.cos(a) + w * math.sin(a)) * rnd.uniform(0.004, 0.016)
            end = base + d * rnd.uniform(0.05, 0.09) + (u * math.cos(a) + w * math.sin(a)) * rnd.uniform(0.015, 0.04)
            add_cyl(tmp, base, end, 0.0045, mat=i_rub, seg=6)
            add_cyl(tmp, end, end + (end - base).normalized() * 0.014, 0.003, mat=i_cu, seg=5)
        bmesh.ops.transform(tmp, matrix=to_obj, verts=tmp.verts)
        me2 = bpy.data.meshes.new('_stump')
        for s in me.materials:                                   # same slots, so the indices survive
            me2.materials.append(s)
        tmp.to_mesh(me2)
        tmp.free()
        # keep material indices: from_mesh maps them by slot index, and the slots are this mesh's
        bm.from_mesh(me2)
        bpy.data.meshes.remove(me2)

    _edit_mesh(ob, edit, sharp=40)
    return removed[0]


def build_bitten_leg(dl01, m, coll):
    import build_racks as racks
    out = {}
    fallen, seated = bpy.data.objects.get('FallenCourier'), bpy.data.objects.get('SeatedCourier')
    if fallen is not None:
        pose = dict(racks.LYING_POSE, hands=racks.lying_hands(dl01),
                    hand_rot={'L': racks.aim((-0.2, -0.3, 0.93)), 'R': racks.aim((0.8, -0.4, -0.45))})
        knee, ankle, xform = _probe_leg(dl01, racks, pose, bake=True)
        out['fallen'] = _bite(fallen, xform.inverted(), knee, ankle, m)       # mesh = xform @ rig
    if seated is not None:
        pose = dict(racks.SEATED_POSE, hands=racks.seated_hands(dl01))
        knee, ankle, _ = _probe_leg(dl01, racks, pose)
        py, pz = racks.cradle_pivot()
        off = Vector((0.0, racks.SEATED_Y - py, racks.PLATE_TOP - pz))        # mesh = rig + off
        out['seated'] = _bite(seated, Matrix.Translation(-off), knee, ankle, m)
    return out


# ---------------------------------------------------------------------------------------------------------
# DL-06 The Heap: the second weight, the sump, the gallery that gives way
# ---------------------------------------------------------------------------------------------------------

def _floaters(bm, x, y, z, n, seed, mat_letter, mat_parcel=None, parcel=0):
    rnd = random.Random(seed)
    for k in range(n):
        add_box(bm, (rnd.uniform(*x), rnd.uniform(*y), z + 0.003), (0.16, 0.11, 0.004), mat=mat_letter,
                rot=_rz(rnd.uniform(0, 3.1)) @ Matrix.Rotation(rnd.uniform(-0.08, 0.08), 4, 'X'))
    for k in range(parcel):
        add_box(bm, (rnd.uniform(*x), rnd.uniform(*y), z + 0.02), (0.26, 0.2, 0.1), mat=mat_parcel,
                rot=_rz(rnd.uniform(0, 3.1)) @ Matrix.Rotation(rnd.uniform(-0.2, 0.2), 4, 'Y'))


def _scum(bm, x, y, zw, mat, axis):
    """A scum line just above the water and a fainter stain over it, on a wall face: axis 'x' runs along x at
    plane y, 'y' along y at plane x."""
    for z0, z1, off in ((zw - 0.02, zw + 0.07, 0.006), (zw + 0.07, zw + 0.2, 0.003)):
        if axis == 'x':
            bx(bm, x, (y - off, y), (z0, z1), mat)
        else:
            bx(bm, (x - off / 2, x + off / 2), y, (z0, z1), mat)


def _culvert(bm, x, y, zw, r, mat_rim, mat_dark):
    """A half-drowned culvert mouth in a back wall at plane y (facing -y): the arch over the water and the
    dark inside it. The White's way in."""
    n = 12
    pts = [(x + r * math.cos(math.pi * k / n), zw + r * math.sin(math.pi * k / n)) for k in range(n + 1)]
    _prism(bm, [(x - r, zw - 0.02)] + pts[::-1][:-1] + [(x + r, zw - 0.02)], y - 0.004, y - 0.002, mat_dark)
    for k in range(n):
        a0, a1 = math.pi * k / n, math.pi * (k + 1) / n
        p0 = Vector((x + (r + 0.04) * math.cos(a0), y - 0.02, zw + (r + 0.04) * math.sin(a0)))
        p1 = Vector((x + (r + 0.04) * math.cos(a1), y - 0.02, zw + (r + 0.04) * math.sin(a1)))
        add_cyl(bm, p0, p1, 0.035, mat=mat_rim, seg=6)


def build_heap(m, coll):
    # (a) The second sorting weight, out at the far end of the floor by the pit edge (its band is its child).
    w = bpy.data.objects.get('HeapWeight1')
    if w is not None:
        w.location.x = HEAP_WEIGHT1_X
        w.rotation_euler.z = math.radians(-31)

    # (b) The sump: a concrete cistern standing in the pit under the head of the chute, brim-full of dark water.
    x0, x1, y0, y1 = SUMP6
    t = SUMP6_WALL
    bm = bmesh.new()
    bx(bm, (x0, x1), (y0, y0 + t), (-6.0, SUMP6_TOP), 0)                  # its walls, up from the pit floor
    bx(bm, (x0, x1), (y1 - t, y1), (-6.0, SUMP6_TOP + 0.05), 0)
    for xa in ((x0, x0 + t), (x1 - t, x1)):
        bx(bm, xa, (y0, y1), (-6.0, SUMP6_TOP), 0)
    bx(bm, (x0, x1), (y0, y1), (SUMP6_FLOOR - 0.2, SUMP6_FLOOR), 0)
    bx(bm, (x0 - 0.02, x1 + 0.02), (y0 - 0.02, y0 + t + 0.02), (SUMP6_TOP - 0.06, SUMP6_TOP + 0.01), 1)   # a steel lip
    for z in (-2.5, -4.2):                                                  # pour lines down its face
        bx(bm, (x0 - 0.005, x1 + 0.005), (y0 - 0.006, y0), (z, z + 0.04), 0)
    _scum(bm, (x0 + t, x1 - t), y1 - t, SUMP6_WATER, 2, 'x')
    add_cyl(bm, (x1 - 0.4, y0 + 0.06, SUMP6_TOP - 0.25), (x1 - 0.4, y0 - 0.25, SUMP6_TOP - 0.3), 0.06, mat=3, seg=10)   # overflow
    add_cyl(bm, (x1 - 0.4, y0 - 0.25, SUMP6_TOP - 0.3), (x1 - 0.4, y0 - 0.3, SUMP6_TOP - 0.45), 0.06, mat=3, seg=10)
    _culvert(bm, x0 + 0.75, y1 - t, SUMP6_WATER, 0.28, 0, 4)
    _obj('HeapSumpTank', bm, [m['concrete'], m['steel'], m['mud'], m['rust'] if 'rust' in m else m['steel'], m['shaft']], coll)
    bm = bmesh.new()
    bx(bm, (x0 + t, x1 - t), (y0 + t, y1 - t), (SUMP6_FLOOR, SUMP6_WATER), 0)
    ob = _obj('HeapSump', bm, [m['water']], coll)
    _recentre(ob, Vector(((x0 + x1) / 2, (y0 + y1) / 2, SUMP6_WATER)))
    bm = bmesh.new()
    _floaters(bm, (x0 + 0.3, x1 - 0.3), (y0 + 0.3, y1 - 0.3), SUMP6_WATER, 6, 661, 0, 1, parcel=1)
    _obj('HeapSumpFloat', bm, [m['letters'], m['paper']], coll)

    # (c) The gallery gives way behind him: cut the walkway strip out of the deck and its rails, and build the
    # panel that falls, hinged at its left end.
    build_gallery_collapse(m, coll)


def _recentre(ob, origin):
    """Move an object's origin to `origin` (world) without moving its mesh."""
    off = origin - ob.location
    ob.data.transform(Matrix.Translation(-off))
    ob.location = origin


def build_gallery_collapse(m, coll):
    """A full-width section of the gallery walkway between the day board and the residential door: the deck,
    both rails and the hanger over it are cut out of art/dl03's objects, and rebuilt as one panel that falls."""
    c0, c1 = COLLAPSE[0] - GALLERY_OFF, COLLAPSE[1] - GALLERY_OFF          # in art/dl03's own x
    cy0, cy1 = COLLAPSE_Y
    deck = bpy.data.objects.get('GalleryDeck')
    rails = bpy.data.objects.get('GalleryRails')
    if deck is not None:
        assert abs(deck.location.x - GALLERY_OFF) < 1e-6

        def cut_deck(bm):
            for isl, lo, hi in _islands(bm):
                if lo.x < c0 and hi.x > c1:
                    yl, yh, zl, zh, xl, xh = lo.y, hi.y, lo.z, hi.z, lo.x, hi.x
                    bmesh.ops.delete(bm, geom=isl, context='VERTS')
                    bx(bm, (xl, c0), (yl, yh), (zl, zh))
                    bx(bm, (c1, xh), (yl, yh), (zl, zh))
        _edit_mesh(deck, cut_deck)
    posts, hanger = [], None
    if rails is not None:
        assert abs(rails.location.x - GALLERY_OFF) < 1e-6

        def cut_rails(bm):
            nonlocal hanger
            for isl, lo, hi in _islands(bm):
                if lo.x < c0 and hi.x > c1:                              # a long rail: split it round the gap
                    yl, yh, zl, zh, xl, xh = lo.y, hi.y, lo.z, hi.z, lo.x, hi.x
                    bmesh.ops.delete(bm, geom=isl, context='VERTS')
                    bx(bm, (xl, c0), (yl, yh), (zl, zh))
                    bx(bm, (c1, xh), (yl, yh), (zl, zh))
                elif lo.x > c0 and hi.x < c1:                            # a post or a hanger in the gap
                    mid = (lo + hi) / 2
                    bmesh.ops.delete(bm, geom=isl, context='VERTS')
                    if hi.z > 4.0:                                       # the hanger: snapped, its top left hanging
                        hanger = mid.copy()
                        add_cyl(bm, (mid.x, mid.y, 3.15), (mid.x, mid.y, hi.z), 0.012, seg=6)
                        add_cyl(bm, (mid.x, mid.y, 3.15), (mid.x + 0.05, mid.y - 0.03, 3.02), 0.012, seg=6)
                    else:
                        posts.append(mid.copy())
        _edit_mesh(rails, cut_rails)

    # GalleryCollapse: origin on the hinge line (along y) at its left end, deck mid-thickness. Swung about the
    # game's z axis (Blender y) its right end drops; the game then lets it go into the heap.
    hx, hy, hz = COLLAPSE_HINGE
    L = COLLAPSE[1] - COLLAPSE[0]
    bm = bmesh.new()
    # 0 steel (the grating), 1 yellow (its rails), 2 rust
    bx(bm, (0.004, L - 0.004), (cy0 + 0.02, cy1), (-0.03, 0.03), 0)
    for k in range(int(L / 0.06)):                                         # the grating's bars, so it reads as a panel
        x = 0.03 + k * 0.06
        bx(bm, (x - 0.006, x + 0.006), (cy0 + 0.04, cy1 - 0.02), (0.03, 0.034), 0)
    for y in (cy0 + 0.06, 0.2, cy1 - 0.06):                                # stringers underneath
        bx(bm, (0.0, L), (y - 0.03, y + 0.03), (-0.12, -0.03), 0)
    for x in (0.02, L - 0.02):                                             # its end bars, rusted through at the bolts
        bx(bm, (x - 0.02, x + 0.02), (cy0 + 0.02, cy1), (-0.1, -0.03), 2)
    for p in posts:                                                        # its posts and its runs of both rails
        bx(bm, (p.x + GALLERY_OFF - hx - 0.02, p.x + GALLERY_OFF - hx + 0.02), (p.y - 0.02, p.y + 0.02), (0.03, 1.03), 1)
    for y, zs in ((-0.52, (0.53, 1.01)), (0.88, (1.01,))):
        for z in zs:
            bx(bm, (0.005, L - 0.005), (y - 0.02, y + 0.02), (z - 0.02, z + 0.02), 1)
    if hanger is not None:                                                 # the hanger's lower end, snapped
        px = hanger.x + GALLERY_OFF - hx
        add_cyl(bm, (px, hanger.y, 0.03), (px, hanger.y, 0.75), 0.012, mat=0, seg=6)
        add_cyl(bm, (px, hanger.y, 0.75), (px - 0.04, hanger.y + 0.02, 0.86), 0.012, mat=0, seg=6)
    ob = _obj('GalleryCollapse', bm, [m['steel'], m['yellow'], m['rust'] if 'rust' in m else m['steel']], coll)
    ob.location = (hx, hy, hz)

    # GalleryCollapseEdges: what it leaves, torn grating bent down at both ends of the gap (static; the game shows
    # it when the panel goes).
    rnd = random.Random(612)
    bm = bmesh.new()
    for xe, sgn in ((COLLAPSE[0], 1), (COLLAPSE[1], -1)):
        y = cy0 + 0.05
        while y < cy1 - 0.05:
            w = rnd.uniform(0.06, 0.14)
            ln = rnd.uniform(0.06, 0.2)
            ang = math.radians(rnd.uniform(40, 80))
            a = Vector((xe, y + w / 2, 1.585))
            dvec = Vector((sgn * math.cos(ang), 0, -math.sin(ang))) * ln
            add_box(bm, a + dvec / 2, (ln, w * 0.9, 0.012), mat=0, rot=_ry(sgn * ang))
            y += w + rnd.uniform(0.0, 0.05)
    _obj('GalleryCollapseEdges', bm, [m['steel']], coll)


# ---------------------------------------------------------------------------------------------------------
# DL-07 The goods-lift sump
# ---------------------------------------------------------------------------------------------------------

def build_sump7(m, coll):
    s0, s1 = SHAFT7
    zw = SUMP7_WATER
    bm = bmesh.new()
    bx(bm, (s0 + 0.002, s1 - 0.002), (-1.6, SUMP7_BACK), (-1.3, zw), 0)
    ob = _obj('Sump7Water', bm, [m['water']], coll)
    _recentre(ob, Vector(((s0 + s1) / 2, (-1.6 + SUMP7_BACK) / 2, zw)))
    bm = bmesh.new()
    _scum(bm, (s0, s1), SUMP7_BACK, zw, 0, 'x')                            # the back wall
    for x, sgn in ((s0, 1), (s1, -1)):                                     # the slab ends either side
        _scum(bm, x + sgn * 0.003, (-1.6, SUMP7_BACK), zw, 0, 'y')
    _culvert(bm, s0 + 1.75, SUMP7_BACK, zw, 0.32, 1, 2)
    _obj('Sump7Scum', bm, [m['mud'], m['concrete'], m['shaft']], coll)
    bm = bmesh.new()                                                       # only in front of the platform's path
    _floaters(bm, (s0 + 0.25, s1 - 0.25), (-1.5, -0.95), zw, 5, 707, 0, 1, parcel=1)
    _obj('Sump7Float', bm, [m['letters'], m['paper']], coll)


# ---------------------------------------------------------------------------------------------------------
# DL-08 The counterweight's tray, its plates, the sump under the cage, the downed cable
# ---------------------------------------------------------------------------------------------------------

def plate_mesh(bm, m_iron=0, m_red=1):
    """A counterweight plate, half a slab of the counterweight's own, with a lifting boss and bail like the
    sorting weights' (red): origin at its base centre; the bail's top at 0.21, so Lift/Carry fit as for a weight."""
    px, py, ph = PLATE
    bx(bm, (-px / 2, px / 2), (-py / 2, py / 2), (0.0, ph - 0.012), m_iron)
    bx(bm, (-px / 2 + 0.006, px / 2 - 0.006), (-py / 2 + 0.006, py / 2 - 0.006), (ph - 0.012, ph), m_iron)
    bx(bm, (-px / 2 - 0.002, px / 2 + 0.002), (-py / 2 - 0.002, py / 2 + 0.002), (ph - 0.03, ph - 0.012), m_red)   # a red band
    add_cyl(bm, (0, 0, ph), (0, 0, 0.15), 0.04, 0.03, mat=m_red, seg=16)
    add_torus(bm, (0, 0, 0.165), (1, 0, 0), 0.042, 0.009, mat=m_red, seg=20, rseg=6)
    for s in (-1, 1):                                                      # cast figures: two pips on its face
        add_cyl(bm, (s * 0.025, -py / 2, 0.05), (s * 0.025, -py / 2 - 0.004, 0.05), 0.008, mat=m_iron, seg=8)


def build_counterweight(m, coll):
    cw = bpy.data.objects.get('CageCounterweight')
    if cw is None:
        return
    import build_cage as cage
    cwx, cwd, cwh = cage.CW_SIZE
    n = 7
    step = (cwh - 0.19) / n
    gone = []

    def lighten(bm):
        for isl, lo, hi in _islands(bm):
            # the top bar of the frame
            if _near((lo.x, hi.x, lo.z, hi.z), (-cwx / 2, cwx / 2, -0.09, -0.02)):
                gone.append('bar')
                bmesh.ops.delete(bm, geom=isl, context='VERTS')
                continue
            k = CW_SLAB_GONE
            z = -cwh + 0.09 + k * step
            if _near((lo.x, hi.x, lo.z, hi.z), (-cwx / 2 + 0.02, cwx / 2 - 0.02, z, z + step - 0.015)):
                gone.append('slab')
                bmesh.ops.delete(bm, geom=isl, context='VERTS')
    _edit_mesh(cw, lighten)
    assert sorted(gone) == ['bar', 'slab'], gone

    # CwTray: the open top of the frame where the slab is missing, lipped front and back, with a bail over it
    # up to the chain's hook (the top bar is gone). A child of the counterweight: it rides with it.
    z0 = TRAY_FLOOR
    bm = bmesh.new()
    # 0 steel, 1 yellow, 2 iron
    for y in (-cwd / 2, cwd / 2):
        bx(bm, (-cwx / 2 + 0.02, cwx / 2 - 0.02), (y - 0.006, y + 0.006), (z0 - 0.01, z0 + 0.07), 0)    # lips
        bx(bm, (-cwx / 2 + 0.02, cwx / 2 - 0.02), (y - 0.009, y + 0.009), (z0 + 0.07, z0 + 0.085), 3)   # red: put them here
    bx(bm, (-cwx / 2 + 0.02, cwx / 2 - 0.02), (-cwd / 2, cwd / 2), (z0 - 0.01, z0), 0)                # its floor plate
    for s in (-1, 1):                                                      # the bail: a strap from each side up to the hook
        a = Vector((s * (cwx / 2), 0, -0.02))
        b = Vector((s * 0.012, 0, -0.004))
        mid, ln = (a + b) / 2, (b - a).length
        ang = math.atan2(b.z - a.z, b.x - a.x)
        add_box(bm, mid, (ln, 0.05, 0.012), mat=1, rot=_ry(-ang))
    add_cyl(bm, (0, -0.03, -0.004), (0, 0.03, -0.004), 0.016, mat=2, seg=10)   # the eye
    tray = _obj('CwTray', bm, [m['steel'], m['yellow'], m['iron'], m['red']], coll)
    tray.parent = cw
    tray.matrix_parent_inverse = Matrix.Identity(4)
    tray.location = (0, 0, 0)

    # CwPlate0, CwPlate1: fallen out of it onto the upper landing.
    for i, (x, yaw) in enumerate(PLATES_AT):
        bm = bmesh.new()
        plate_mesh(bm)
        ob = _obj(f'CwPlate{i}', bm, [m['iron'], m['red']], coll)
        ob.location = (x, 0.0, UPPER_LANDING)
        ob.rotation_euler = (0, 0, math.radians(yaw))


def build_cage_sump(m, coll):
    s0, s1 = CAGE_SHAFT
    zw = CAGE_SUMP_WATER
    bm = bmesh.new()
    bx(bm, (s0 + 0.01, s1 - 0.01), (-1.6, CAGE_BACK - 0.01), (CAGE_PIT_Z, zw), 0)
    ob = _obj('CageSump', bm, [m['water']], coll)
    _recentre(ob, Vector(((s0 + s1) / 2, (-1.6 + CAGE_BACK) / 2, zw)))
    bm = bmesh.new()
    _scum(bm, (s0, s1), CAGE_BACK, zw, 0, 'x')
    for x, sgn in ((s0, 1), (s1, -1)):
        _scum(bm, x + sgn * 0.003, (-1.6, CAGE_BACK), zw, 0, 'y')
    _culvert(bm, s0 + 0.32, CAGE_BACK, zw, 0.26, 1, 2)
    _obj('CageSumpScum', bm, [m['mud'], m['concrete'], m['shaft']], coll)
    bm = bmesh.new()                                                       # in front of the cage's footprint
    _floaters(bm, (s0 + 0.2, s1 - 0.2), (-1.5, -0.85), zw, 4, 808, 0)
    _obj('CageSumpFloat', bm, [m['letters']], coll)


def build_tunnel_cable(m, coll):
    z = 1.6
    x0, x1, y0, y1 = WET
    _plane('TunnelWet', m['wetpatch'], (x0, x1), (y0, y1), z + 0.003, coll)
    # The dry hatch cover between the arcs: steel, raised a little out of the wet.
    d0, d1 = DRY_PLATE
    bm = bmesh.new()
    bx(bm, (d0, d1), (-0.4, 0.4), (z, z + 0.022), 0)
    for k in range(5):
        x = d0 + 0.03 + k * (d1 - d0 - 0.06) / 4
        bx(bm, (x - 0.004, x + 0.004), (-0.36, 0.36), (z + 0.022, z + 0.025), 0)
    for x in (d0 + 0.03, d1 - 0.03):
        for y in (-0.36, 0.36):
            add_cyl(bm, (x, y, z + 0.022), (x, y, z + 0.028), 0.008, mat=1, seg=8)
    _obj('TunnelHatch', bm, [m['plate'], m['iron']], coll)
    # TunnelCable: torn out of a junction box under the ceiling at the back, down the wall, across the lane at
    # the first arc, in a loop in front, back across at the second, its frayed end lying in the water.
    pts = [Vector(p) for p in ((93.62, 1.25, 3.0), (93.61, 1.24, 2.6), (93.6, 1.22, 1.9), (93.57, 1.16, z + 0.03),
                               (93.45, 0.95, z + 0.018), (93.25, 0.6, z + 0.018), (93.15, 0.0, z + 0.018),
                               (93.22, -0.45, z + 0.018), (93.45, -0.78, z + 0.018), (93.72, -0.8, z + 0.018),
                               (93.92, -0.5, z + 0.018), (93.98, -0.05, z + 0.018), (94.03, 0.25, z + 0.018),
                               (94.07, 0.42, z + 0.018))]
    curve = []
    for i in range(len(pts) - 1):                                            # Catmull-Rom through the points
        p0, p1, p2, p3 = pts[max(0, i - 1)], pts[i], pts[i + 1], pts[min(len(pts) - 1, i + 2)]
        for k in range(6):
            t = k / 6
            curve.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t
                                + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    curve.append(pts[-1])
    split = Vector(ARC_A[0])
    bm = bmesh.new()
    # 0 cable, 1 copper, 2 steel, 3 yellow
    for a, b in zip(curve, curve[1:]):
        mid = (a + b) / 2
        if (mid - split).length < 0.035:                                   # the split: its copper bared
            add_cyl(bm, a, b, 0.01, mat=1, seg=8)
        else:
            add_cyl(bm, a, b, 0.018, mat=0, seg=8)
        add_sphere(bm, b, 0.018 if (b - split).length >= 0.035 else 0.01, mat=0 if (b - split).length >= 0.035 else 1, seg=8)
    end = curve[-1]
    dirn = (curve[-1] - curve[-3]).normalized()
    rnd = random.Random(818)
    for k in range(7):                                                     # the frayed end: strands splayed
        sp = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0, 0.4))).normalized()
        add_cyl(bm, end, end + dirn * rnd.uniform(0.03, 0.06) + sp * rnd.uniform(0.01, 0.035), 0.0025, mat=1, seg=4)
    # The junction box it was torn from, on the pipe run under the ceiling, its lid hanging, a hazard flash.
    bx(bm, (93.45, 93.79), (1.12, 1.42), (2.98, 3.26), 2)
    bx(bm, (93.45, 93.79), (1.07, 1.1), (2.72, 2.98), 2)                   # its lid, hanging open
    bx(bm, (93.51, 93.73), (1.105, 1.115), (3.12, 3.2), 3)
    add_cyl(bm, (93.62, 1.25, 3.26), (93.62, 1.25, 3.3), 0.03, mat=2, seg=10)
    _obj('TunnelCable', bm, [m['cable'], m['copper'], m['steel'], m['yellow']], coll)


# ---------------------------------------------------------------------------------------------------------

def build_set(dl01, m, coll):
    make_textures()
    pass2_materials(m)
    build_press(m, coll)
    build_drag_marks(m, coll)
    bitten = build_bitten_leg(dl01, m, coll)
    print('pass2: bitten leg faces removed', bitten)
    build_heap(m, coll)
    build_sump7(m, coll)
    build_counterweight(m, coll)
    build_cage_sump(m, coll)
    build_tunnel_cable(m, coll)


# ---------------------------------------------------------------------------------------------------------
# D-17's clips: deaths (shown, then cut), the knock-back and the startle
# ---------------------------------------------------------------------------------------------------------

def _root(pb, frame, rot=(0, 0, 0), loc=(0, 0, 0), pivot=None):
    """Key the root bone's rotation (degrees, rig axes) and location. With `pivot` (rig space) the rotation
    turns him about that point instead of about his feet."""
    r = Matrix.Rotation(math.radians(rot[2]), 3, 'Z') @ Matrix.Rotation(math.radians(rot[1]), 3, 'Y') @ \
        Matrix.Rotation(math.radians(rot[0]), 3, 'X')
    pb['root'].rotation_euler = [math.radians(v) for v in rot]
    loc = Vector(loc)
    if pivot is not None:
        p = Vector(pivot)
        loc = loc + p - r @ p
    pb['root'].location = loc
    _key(pb['root'], 'location', 'rotation_euler', frame=frame)


def clip_death_crush(dl01, arm):
    """Something heavy comes down on him: his knees fold, the pod is driven down, the head pressed onto the chest,
    the arms flung out flat, the antenna bent back. A twitch, then still (the eye goes out: the game). 20 frames;
    the hit lands by frame 3; held from frame 12."""
    track, spring, Clip, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY
    frames = 20
    c = Clip(arm, 'DeathCrush', frames)
    hit = lambda x: 1 - (1 - x) ** 3                                     # noqa: E731
    for frame in range(1, frames + 1):
        f = frame - 1
        k = track([(0, 0), (3, 1)], f, ease=hit)
        bounce = spring(f, 3, 0.02, decay=2.5, freq=1.6)
        twitch = spring(f, 8, 1.0, decay=2.0, freq=2.2)
        z = -0.21 * k + bounce
        rot = (17 * k + 2 * twitch, 5 * k + 1.5 * twitch, -3 * k)
        hands = {s: CARRY[s] + Vector((s * 0.15 * k, 0.03 * k, -0.02 * k + 0.01 * twitch * s)) for _, s in SIDES}
        feet = {side: ((s * 0.06 * k, -0.07 * k, 0), (0, 0, s * 18 * k)) for side, s in SIDES}
        head = (26 * k + 3 * twitch, -6 * k, 4 * k)
        antenna = [(-30 * k - 50 * k * (i / 2) + spring(f, 3, 14, decay=3), 12 * k * (1 if i % 2 else -1)) for i in range(3)]
        c.pose(frame, body=(0, 0.015 * k, z), body_rot=rot, head=head, antenna=antenna, hands=hands, feet=feet,
               hand_rot={'L': (-24 + 30 * k, 6, 10 + 40 * k), 'R': (-24 + 30 * k, -6, -10 - 40 * k)},
               claws={'L': CLAW_REST_OPEN['L'] + 20 * k, 'R': CLAW_REST_OPEN['R'] + 24 * k}, elbows={'L': k, 'R': k})
    c.done()


def clip_death_shock(dl01, arm):
    """Current through him: rigid, up on his toes, arms locked out, claws sprung, antenna stiff; a fast jittering
    seize (frames 1 to 18), then the power drops and he slumps, knees buckling, head down. 30 frames; slumped from 25."""
    track, spring, Clip, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY
    frames = 30
    c = Clip(arm, 'DeathShock', frames)
    rnd = random.Random(30)
    jit = [rnd.uniform(-1, 1) for _ in range(frames * 6)]
    for frame in range(1, frames + 1):
        f = frame - 1
        seize = track([(0, 0), (1, 1), (17, 1), (19, 0)], f, ease=lambda x: x)
        slump = track([(18, 0), (25, 1)], f)
        j = lambda i: jit[f * 6 + i] * seize                                # noqa: E731
        z = 0.02 * seize - 0.2 * slump + 0.006 * j(0)
        rot = (-7 * seize + 24 * slump + 2.5 * j(1), 3.5 * j(2) + 3 * slump, 2.5 * j(3))
        stiff = {s: CARRY[s] + Vector((s * 0.09, 0.02, -0.04)) + Vector((0.012 * j(4), 0.01 * j(5), 0.012 * j(1))) for _, s in SIDES}
        limp = {s: CARRY[s] + Vector((s * 0.02, 0.06, -0.07)) for _, s in SIDES}
        hands = {s: stiff[s].lerp(limp[s], slump) for _, s in SIDES}
        feet = {side: ((0, 0, 0.012 * seize * (1 - slump)), (-10 * seize * (1 - slump), 0, s * 6 * slump)) for side, s in SIDES}
        head = (-10 * seize + 38 * slump + 4 * j(5), 4 * j(0) - 8 * slump, 3 * j(2))
        antenna = [(6 * seize * (1 - slump) + 4 * j(i) + (36 + 8 * i) * slump + spring(f, 25, 10, decay=3), 3 * j(i + 2))
                   for i in range(3)]
        claw = 42 * seize * (1 - slump) + CLAW_REST_OPEN['L'] * slump
        c.pose(frame, body=(0, 0.01 * slump, z), body_rot=rot, head=head, antenna=antenna, hands=hands, feet=feet,
               hand_rot={'L': (-10, 10 * seize, 20 * seize), 'R': (-10, -10 * seize, -20 * seize)},
               claws={'L': claw + 6 * j(3), 'R': claw + 6 * j(4)}, elbows={'L': seize, 'R': seize})
    c.done()


def clip_death_grabbed(dl01, arm):
    """Taken by the waist and yanked off his feet (the game carries him with the White's jaw): he folds over the
    grip, legs kicking clear of the floor, claws flailing and snapping, head whipping, antenna lashing. 24 frames,
    the yank on frames 0 to 4; it keeps flailing, weaker, to the end."""
    track, spring, Clip, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY
    frames = 24
    c = Clip(arm, 'DeathGrabbed', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        k = track([(0, 0), (3, 1)], f, ease=lambda x: 1 - (1 - x) ** 2)
        fl = track([(2, 0), (5, 1), (16, 0.8), (24, 0.35)], f)
        z = 0.04 * k
        rot = (26 * k + 8 * fl * math.sin(f * 0.9), 7 * fl * math.sin(f * 0.7 + 1), 5 * fl * math.sin(f * 0.5))
        hands = {s: CARRY[s] + Vector((s * (0.1 + 0.06 * math.sin(f * 1.1 + s)), -0.05 + 0.05 * math.sin(f * 0.8 + s * 2),
                                       0.12 * k + 0.08 * fl * math.sin(f * 1.3 + (0 if s > 0 else 2.2))))
                 for _, s in SIDES}
        feet = {side: ((s * 0.04 * k, 0.1 * k + 0.05 * fl * math.sin(f * 1.4 + (0 if s > 0 else math.pi)),
                        0.12 * k + 0.04 * fl * math.sin(f * 1.4 + (1.2 if s > 0 else 1.2 + math.pi))),
                       (40 * k + 25 * fl * math.sin(f * 1.4 + s), 0, 0)) for side, s in SIDES}
        head = (-24 * k + 18 * fl * math.sin(f * 0.9 + 0.8), 14 * fl * math.sin(f * 0.6), 8 * fl * math.sin(f * 1.1))
        antenna = [(-35 * k + 28 * fl * math.sin(f * 1.3 - i), 14 * fl * math.sin(f * 0.9 + i)) for i in range(3)]
        snap = 0.5 + 0.5 * math.sin(f * 1.7)
        c.pose(frame, body=(0, 0.03 * k, z), body_rot=rot, head=head, antenna=antenna, hands=hands, feet=feet,
               hand_rot={'L': (-60 * k, 10, 20), 'R': (-60 * k, -10, -20)},
               claws={'L': 6 + 34 * snap * fl, 'R': 6 + 34 * (1 - snap) * fl}, elbows={'L': 0.4 + 0.6 * k, 'R': 0.4 + 0.6 * k})
    c.done()


def clip_death_fall(dl01, arm):
    """Over an edge backwards: a teeter as the foot goes, then he tips back and tumbles, arms flung up and
    wheeling, legs kicking, head thrown back, antenna streaming. The game moves him down (gravity); the clip
    turns him about his middle, 200 degrees back by frame 24. 24 frames."""
    track, spring, Clip, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY
    frames = 24
    c = Clip(arm, 'DeathFall', frames)
    pb = arm.pose.bones
    for frame in range(1, frames + 1):
        f = frame - 1
        tip = track([(0, 0), (4, 12), (24, 200)], f, ease=lambda x: x ** 1.4)
        up = track([(0, 0), (4, 1)], f)
        wheel = math.sin(f * 1.1) * up
        hands = {s: CARRY[s] + Vector((s * 0.12 * up, 0.03 * up + 0.03 * wheel * s, 0.2 * up + 0.04 * wheel)) for _, s in SIDES}
        feet = {side: ((s * 0.02, -0.06 * up + 0.05 * math.sin(f * 1.2 + s), 0.08 * up + 0.04 * math.sin(f * 1.2 + s + 1)),
                       (30 * up, 0, 0)) for side, s in SIDES}
        head = (-30 * up + 6 * math.sin(f * 0.8), 5 * wheel, 0)
        antenna = [(-50 * up + 10 * math.sin(f * 1.5 - i), 6 * math.sin(f + i)) for i in range(3)]
        c.pose(frame, body=(0, 0, -0.03 * up), body_rot=(-10 * up, 4 * wheel, 0), head=head, antenna=antenna,
               hands=hands, feet=feet, hand_rot={'L': (-60 * up, 0, 20), 'R': (-60 * up, 0, -20)},
               claws={'L': 34 * up + 4, 'R': 30 * up + 4}, elbows={'L': up, 'R': up})
        _root(pb, frame, rot=(-tip, 0, 0), pivot=(0, 0, 0.36))
    c.done()
    pb['root'].location = (0, 0, 0)
    pb['root'].rotation_euler = (0, 0, 0)


def clip_knockback(dl01, arm):
    """The safe scare (DL-07): something slaps the walkway in front of him. He is thrown back off his feet onto his
    seat, legs out in front, claws back on the floor behind him; he stares at the water, then scrambles up and
    stands, still watching it. The game moves him back about 0.18 m over the first 0.4 s. 40 frames.
    Key frames: 0 hit, 4 airborne, 8 seated, 8 to 20 staring, 20 to 34 scrambling up, 40 standing."""
    import build_dl02 as dl02
    track, spring, Clip, CARRY, REST = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY, dl01.REST_WRIST
    frames = 40
    c = Clip(arm, 'Knockback', frames)
    pb = arm.pose.bones
    sit_z = -0.245
    for frame in range(1, frames + 1):
        f = frame - 1
        fly = track([(0, 0), (2, 1), (6, 1), (8, 0)], f)
        sit = track([(2, 0), (8, 1), (20, 1), (32, 0)], f, ease=lambda x: smoothstep(x))
        up = track([(20, 0), (34, 1)], f)
        z = sit_z * sit + 0.04 * fly * (1 - sit) + spring(f, 8, -0.025, decay=2.5, freq=1.4)
        lean = -22 * fly * (1 - sit) - 12 * sit + 14 * track([(22, 0), (28, 1), (34, 0)], f)
        body, rot = (0, 0.05 * sit, z), (lean, 0, 0)
        # Claws: flung up, then back onto the floor behind him to prop him, then up again as he rises.
        flung = {s: CARRY[s] + Vector((s * 0.1, 0.04, 0.2)) for _, s in SIDES}
        prop = dl02.reach({s: Vector((s * 0.24, 0.16, 0.035)) for _, s in SIDES}, body, rot, REST)
        hands = {s: CARRY[s].lerp(flung[s], fly).lerp(prop[s], track([(5, 0), (9, 1), (26, 1), (32, 0)], f)) for _, s in SIDES}
        legs_out = sit * (1 - up)
        feet = {side: ((s * 0.03 * legs_out, -0.2 * legs_out - 0.05 * fly, 0.03 * legs_out + 0.04 * fly),
                       (-20 * legs_out + 10 * fly, 0, s * 8 * legs_out)) for side, s in SIDES}
        # Feet scrabble under him as he gets up.
        for side, s in SIDES:
            t0 = 22 if s > 0 else 26
            lift = 0.04 * math.sin(math.pi * (f - t0) / 5) if t0 <= f <= t0 + 5 else 0.0
            loc, r = feet[side]
            feet[side] = ((loc[0], loc[1], loc[2] + lift), r)
        stare = track([(6, 0), (10, 1), (34, 1), (40, 0.6)], f)
        head = (-12 * fly + 24 * stare - lean * 0.6, track([(10, 0), (14, -6), (18, 4), (24, 0)], f), 0)
        antenna = [(-45 * fly - 30 * stare + spring(f, 8, 16 * (1 + 0.3 * i), decay=4) + 3 * math.sin(f * 0.6 - i), 0) for i in range(3)]
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands, feet=feet,
               hand_rot={'L': (-24 - 40 * fly, 6, 10), 'R': (-24 - 40 * fly, -6, -10)},
               claws={'L': CLAW_REST_OPEN['L'] + 26 * fly, 'R': CLAW_REST_OPEN['R'] + 24 * fly},
               elbows={'L': max(fly, sit * (1 - up)), 'R': max(fly, sit * (1 - up))})
        for side, _ in SIDES:                                     # knees up while he sits, not down through the floor
            pb[f'pole_knee.{side}'].location = (0, 0.3 * legs_out, 0.6 * legs_out)
            _key(pb[f'pole_knee.{side}'], 'location', frame=frame)
    c.done()
    for side, _ in SIDES:
        pb[f'pole_knee.{side}'].location = (0, 0, 0)


def clip_startled(dl01, arm):
    """A small jump back with his claws up (the game moves him back about 0.22 m, frames 2 to 9): a dip, the hop
    (feet off 3 to 8), the landing (9), then the claws come down and he stays braced, looking. 18 frames."""
    track, spring, Clip, CARRY = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY
    frames = 18
    c = Clip(arm, 'Startled', frames)
    for frame in range(1, frames + 1):
        f = frame - 1
        arms = track([(0, 0), (3, 1), (10, 1), (18, 0.25)], f, ease=lambda x: ease_back(x, 0.5))
        hop = track([(2, 0), (5, 1), (8, 0)], f)
        z = track([(0, 0), (2, -0.035), (5, 0.035), (9, -0.04), (13, -0.012), (18, -0.01)], f)
        hands = {s: CARRY[s] + Vector((s * 0.06 * arms, -0.03 * arms, 0.17 * arms)) for _, s in SIDES}
        feet = {side: ((0, 0.03 * hop, 0.05 * hop), (-15 * hop, 0, 0)) for side, s in SIDES}
        c.pose(frame, body=(0, 0.01 * arms, z), body_rot=(track([(0, 2), (3, -10), (9, -6), (13, 4), (18, 2)], f), 0, 0),
               head=(track([(0, 0), (3, 10), (9, 6), (18, 4)], f), 0, 0),
               antenna=[(-50 * arms + spring(f, 9, 12 * (1 + 0.3 * i), decay=3), 0) for i in range(3)],
               hands=hands, feet=feet, hand_rot={'L': (-40 - 30 * arms, 0, 20), 'R': (-40 - 30 * arms, 0, -20)},
               claws={'L': 30 * arms + CLAW_REST_OPEN['L'] * (1 - arms), 'R': 28 * arms + CLAW_REST_OPEN['R'] * (1 - arms)},
               elbows={'L': arms, 'R': arms})
    c.done()


def add_clips(dl01, arm):
    clip_death_crush(dl01, arm)
    clip_death_shock(dl01, arm)
    clip_death_grabbed(dl01, arm)
    clip_death_fall(dl01, arm)
    clip_knockback(dl01, arm)
    clip_startled(dl01, arm)
