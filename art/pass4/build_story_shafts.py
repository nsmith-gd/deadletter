"""Chapter 1, pass 4 (docs/chapter1_pass4_plan.md, sections 2 and 3): story_shafts. DL-08 The Fall, DL-09 The Cut
Bridge, and the RING C stencils for DL-06 to DL-09. Built in FINAL world x, after the pass 3 modules; other builders'
objects are only changed here, by name.

  DL-08  The fall. Lift 2's sump runs on under the near landing (x 83.3 to the shaft at 85.8): the landing's slab is
         cut back to a 0.35 m deck on beams, and the flooded pit beneath it is seen in section, like the shaft. In it
         a goods-lift car lies where it fell, on its side and half under the water: its corner posts buckled, its
         lattice gate burst outward, its snapped cable piled on top with the frayed end standing up. Suitcases, a
         trunk and coats have spilled out of it: two coats float face down. A pram lies nose down in the water,
         one wheel up. Nothing of it is in the shaft (x >= 85.8), so the platform's travel and the White's water
         (SHAFT.x0..x1 at game z 1.2) are untouched.
           StoryFallPit    the cavity's walls, beams and tide line (Concrete, WallPanel, DepotSteel, FloodMud)
           StoryFallWater  its water, level with the sump's (-0.15)
           StoryFallWreck  the car, the cable, the luggage, the coats, the pram
         Changed: G4Floor (its first slab is rebuilt round the cavity), G4ShaftFaces (the near face stops at the
         cavity's ceiling, except behind the rack), Sump7Scum (the strip on the near face goes; the cavity has its own).
  DL-09  The cut bridge. From ring C's lip, left of the balcony, a girder bridge on masonry piers climbs out across
         the chasm toward the upper city's first tier; its middle spans are blown out. The near stump is heaped with
         belongings behind a barricade of beds, doors and crates, and at its broken end a board on two posts says
         GRADE 1-2 BEYOND THIS POINT. Twisted girders and cables hang from both stumps. The far stump runs into a lit
         gatehouse on the upper city's tier. Far detail: plain atrium materials, faces toward the balcony only.
           AtriumCutBridge* (named Atrium* so it moves and culls with the atrium): Masonry, Steel, Rust, Junk, Lamps,
           Glow, Sign.
  Stencils  WayRingC06..09: RING C and an arrow down and on, the same worn stencil each time (WayRingCMat).

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y. Game (x, z, -y).
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
FONT_C = '/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf'

DECK = 1.6
# DL-08: Lift 2's shaft and sump (art/dl04 SHAFT 52.8..55.3 + OFF3 33; art/pass2 Sump7Water).
SHAFT = (85.8, 88.3)
SUMP_WATER = -0.15
SUMP_FRONT = -1.6                     # the slab's front face: the section the camera looks through
PIT_FLOOR = -1.22
CAV = dict(x0=83.3, x1=SHAFT[0], back=0.95, ceil=1.25)   # the cavity under the near landing
RACK_Y = 0.35                         # the shaft's near face stays full height behind this (the rack is at 0.5)


# =====================================================================================================================
# Textures (PIL, art/pass4/textures; rewritten only when missing)
# =====================================================================================================================

def _font(path, size):
    from PIL import ImageFont
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _wear(img, seed, holes=70, rmin=2, rmax=10, keep=(70, 200), blur=1.4):
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


def make_ring_c(path):
    """RING C and an arrow down and on (to the lower right), sprayed through a cut stencil: the letters' bridges
    show, the edges carry a little overspray, the paint is worn through in patches and has run in places."""
    from PIL import Image, ImageDraw, ImageFilter, ImageChops
    w, h = 1024, 512
    paint = (226, 219, 198)
    mask = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(mask)
    f = _font(FONT, 236)
    x0, y0 = 40, 120
    text = 'RING C'
    d.text((x0, y0), text, font=f, fill=255)
    # The stencil's bridges: thin uncut strips through the counters and across the open bowls.
    x = x0
    ad = ImageDraw.Draw(mask)
    for ch in text:
        cw = d.textlength(ch, font=f)
        if ch == 'R':
            ad.rectangle((x + cw * 0.18, y0 + 96, x + cw * 0.7, y0 + 108), fill=0)      # across the bowl's foot
            ad.rectangle((x + cw * 0.46, y0 + 30, x + cw * 0.46 + 11, y0 + 80), fill=0)  # through the bowl's top
        elif ch == 'G':
            ad.rectangle((x + cw * 0.47, y0 + 30, x + cw * 0.47 + 11, y0 + 70), fill=0)
        elif ch == 'C':
            ad.rectangle((x + cw * 0.52, y0 + 30, x + cw * 0.52 + 11, y0 + 70), fill=0)
            ad.rectangle((x + cw * 0.52, y0 + 200, x + cw * 0.52 + 11, y0 + 250), fill=0)
        elif ch == 'N':
            ad.rectangle((x + cw * 0.45, y0 + 120, x + cw * 0.45 + 10, y0 + 160), fill=0)
        x += cw
    # The arrow: a thick shaft down to the right, its head at the lower right, a bridge between them.
    ax0, ay0, ax1, ay1 = 790, 110, 930, 330
    t = 26
    d.polygon([(ax0 - t, ay0 + t * 0.4), (ax0 + t * 0.4, ay0 - t), (ax1 - 52 + t * 0.6, ay1 - 52 - t * 0.6),
               (ax1 - 52 - t * 0.6, ay1 - 52 + t * 0.6)], fill=255)
    d.polygon([(ax1 + 40, ay1 + 40), (ax1 + 46, ay1 - 118), (ax1 - 118, ay1 + 46)], fill=255)
    ad.line((ax1 - 92, ay1 - 30, ax1 - 30, ay1 - 92), fill=0, width=14)
    # A bar under it all, as such stencils have.
    d.rectangle((x0 + 6, 412, 980, 440), fill=255)
    for bx in (300, 640):
        ad.rectangle((bx, 410, bx + 12, 442), fill=0)
    # Overspray: a soft halo at low strength, then the crisp paint over it.
    halo = mask.filter(ImageFilter.GaussianBlur(7)).point(lambda v: int(v * 0.22))
    rnd = random.Random(808)
    runs = Image.new('L', (w, h), 0)                 # paint runs from the bottoms of a few strokes
    rd = ImageDraw.Draw(runs)
    for _ in range(16):
        xx = rnd.uniform(60, 960)
        yy = 360 if rnd.random() < 0.7 else 440
        if mask.getpixel((int(xx), int(yy) - 4)) > 128:
            rd.line((xx, yy - 6, xx + rnd.uniform(-2, 2), yy + rnd.uniform(18, 60)), fill=205, width=rnd.randint(3, 6))
    alpha = ImageChops.lighter(ImageChops.lighter(halo, mask.filter(ImageFilter.GaussianBlur(1.1))), runs)
    img = Image.new('RGBA', (w, h), paint + (0,))
    img.putalpha(alpha)
    _wear(img, 809, holes=110, rmin=3, rmax=16, keep=(40, 190), blur=2.0)
    # Grime settled over it, darker toward the bottom.
    grime = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(grime)
    for _ in range(50):
        xx, yy, r = rnd.uniform(0, w), rnd.uniform(0, h), rnd.uniform(10, 70)
        gd.ellipse((xx - r, yy - r, xx + r, yy + r), fill=(70, 62, 48, rnd.randint(20, 60)))
    grime = grime.filter(ImageFilter.GaussianBlur(10))
    rgb = Image.alpha_composite(Image.new('RGBA', (w, h), paint + (255,)), grime).convert('RGB')
    rgb.putalpha(img.split()[3])
    rgb.save(path)


def make_grade_sign(path):
    """The checkpoint board at the cut bridge's near end: GRADE 1-2 / BEYOND THIS POINT, black on cream with a red
    band, BY ORDER; weathered, a corner gone, smeared with something thrown at it."""
    from PIL import Image, ImageDraw, ImageFilter
    w, h = 1024, 512
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cream, ink, red = (214, 204, 176, 255), (22, 20, 18, 255), (150, 36, 28, 255)
    d.rectangle((0, 0, w, h), fill=cream)
    d.rectangle((0, 0, w, 64), fill=red)
    d.rectangle((0, h - 40, w, h), fill=red)
    d.rectangle((10, 10, w - 10, h - 10), outline=ink, width=8)
    f1, f2, f3 = _font(FONT_C, 200), _font(FONT_C, 104), _font(FONT, 34)
    s = 'GRADE 1–2'
    d.text(((w - d.textlength(s, font=f1)) / 2, 66), s, font=f1, fill=ink)
    s = 'BEYOND THIS POINT'
    d.text(((w - d.textlength(s, font=f2)) / 2, 300), s, font=f2, fill=ink)
    s = 'BY ORDER · REFUGE AUTHORITY'
    d.text(((w - d.textlength(s, font=f3)) / 2, 14), s, font=f3, fill=cream)
    rnd = random.Random(912)
    for _ in range(26):                                   # thrown muck and rust runs
        x, y, r = rnd.uniform(0, w), rnd.uniform(60, h), rnd.uniform(6, 34)
        d.ellipse((x - r, y - r, x + r, y + r), fill=(60, 48, 34, rnd.randint(60, 150)))
    for _ in range(14):
        x = rnd.uniform(0, w)
        d.line((x, rnd.uniform(0, 200), x + rnd.uniform(-6, 6), h), fill=(90, 50, 30, rnd.randint(40, 90)), width=rnd.randint(3, 9))
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    a = img.split()[3]
    ad = ImageDraw.Draw(a)
    ad.polygon([(w, h), (w - 150, h), (w - 90, h - 60), (w - 40, h - 130), (w, h - 170)], fill=0)   # a corner gone
    img.putalpha(a)
    img.save(path)


TEXTURES = {'ringc': ('way_ring_c.png', make_ring_c), 'grade': ('grade_sign.png', make_grade_sign)}


def texture(key):
    name, fn = TEXTURES[key]
    path = os.path.join(TEX, name)
    if not os.path.exists(path):
        os.makedirs(TEX, exist_ok=True)
        fn(path)
    return path


# =====================================================================================================================
# Materials
# =====================================================================================================================

NEW_WORN = {      # index.html WORN entries are given in the report
    'CoatWool': dict(base=(0.035, 0.034, 0.036), dirt=(0.03, 0.026, 0.02), chip=(0.07, 0.066, 0.06), rough=0.95,
                     chip_rough=0.95, metallic=0.0, dust=(0.06, 0.058, 0.052), chip_scale=30.0, chip_amount=0.75,
                     grime_scale=8.0, dust_amount=0.2),
}
FALLBACK_WORN = {  # matching index.html's WORN table, in case the module that makes them has not run
    'LuggageLeather': dict(base=(0.15, 0.08, 0.045), dirt=(0.06, 0.035, 0.02), chip=(0.27, 0.18, 0.11), rough=0.62, chip_rough=0.8, metallic=0.0),
    'LuggageCanvas': dict(base=(0.13, 0.135, 0.105), dirt=(0.07, 0.065, 0.05), chip=(0.21, 0.2, 0.16), rough=0.9, chip_rough=0.9, metallic=0.0),
    'FloodMud': dict(base=(0.062, 0.05, 0.036), dirt=(0.035, 0.028, 0.02), chip=(0.09, 0.076, 0.058), rough=0.95, chip_rough=0.85, metallic=0.0),
    'HandleBlack': dict(base=(0.02, 0.02, 0.018), dirt=(0.035, 0.03, 0.024), chip=(0.55, 0.53, 0.5), rough=0.5, chip_rough=0.22, metallic=0.55),
    'WornIron': dict(base=(0.045, 0.043, 0.04), dirt=(0.06, 0.035, 0.02), chip=(0.30, 0.29, 0.27), rough=0.7, chip_rough=0.35, metallic=0.6),
    'Concrete': dict(base=(0.075, 0.074, 0.07), dirt=(0.035, 0.034, 0.03), chip=(0.12, 0.115, 0.105), rough=0.92, chip_rough=0.9, metallic=0.0),
    'WallPanel': dict(base=(0.09, 0.095, 0.09), dirt=(0.04, 0.04, 0.035), chip=(0.14, 0.13, 0.11), rough=0.9, chip_rough=0.85, metallic=0.0),
    'ShutterSteel': dict(base=(0.14, 0.16, 0.15), dirt=(0.09, 0.05, 0.025), chip=(0.16, 0.08, 0.035), rough=0.7, chip_rough=0.6, metallic=0.4),
    'DepotSteel': dict(base=(0.05, 0.052, 0.05), dirt=(0.05, 0.03, 0.018), chip=(0.16, 0.15, 0.13), rough=0.6, chip_rough=0.4, metallic=0.6),
}
PLAIN = {          # name: (colour, roughness, metallic), as index.html PLAIN
    'Water': ((0.01, 0.012, 0.012), 0.04, 0.3), 'Rubber': ((0.012, 0.012, 0.011), 0.7, 0.0),
    'AtriumMasonry': ((0.15, 0.135, 0.115), 0.85, 0.0), 'AtriumSheet': ((0.075, 0.082, 0.08), 0.6, 0.4),
    'AtriumRust': ((0.11, 0.048, 0.025), 0.85, 0.0), 'AtriumWood': ((0.085, 0.06, 0.04), 0.88, 0.0),
    'AtriumCloth': ((0.2, 0.13, 0.065), 0.9, 0.0), 'AtriumDark': ((0.006, 0.006, 0.006), 0.8, 0.0),
    'Barricade': ((0.4, 0.06, 0.04), 0.7, 0.0), 'AtriumCut': ((0.085, 0.078, 0.066), 0.95, 0.0),
}
EMIT = {           # name: (colour, strength), as index.html EMIT
    'AtriumWindowGlow': ((1.0, 0.6, 0.28), 2.5), 'RingLamp': ((1.0, 0.78, 0.5), 3.0),
}


def material(name):
    from build_d17 import worn_material, simple_material, emission_material
    mt = bpy.data.materials.get(name)
    if mt is not None:
        return mt
    if name in NEW_WORN:
        return worn_material(name, **NEW_WORN[name])
    if name in FALLBACK_WORN:
        return worn_material(name, **FALLBACK_WORN[name])
    if name in PLAIN:
        c, r, mtl = PLAIN[name]
        return simple_material(name, c, r, metallic=mtl)
    if name in EMIT:
        c, s = EMIT[name]
        return emission_material(name, c, s)
    raise KeyError(name)


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
# Helpers
# =====================================================================================================================

PLACED = []


def note(name, what):
    PLACED.append((name, what))


def bx(bm, x, y, z, mat=0, rot=None):
    """A box from (min, max) ranges."""
    from build_d17 import add_box
    return add_box(bm, ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2),
                   (x[1] - x[0], y[1] - y[0], z[1] - z[0]), mat=mat, rot=rot)


def solid(name, build, mats, coll, sharp=35):
    import build_d17 as d17
    bm = bmesh.new()
    build(bm)
    return d17.mesh_object(name, bm, [material(m) if isinstance(m, str) else m for m in mats], coll, sharp=sharp)


def xform(verts, M):
    for v in verts:
        v.co = M @ v.co
    return verts


def rot(axis, deg):
    return Matrix.Rotation(math.radians(deg), 4, axis)


def wall_y(x, z, y0=-0.3, maxd=4.0, skip=()):
    """The first surface straight back from (x, y0, z) along +y."""
    dg = bpy.context.evaluated_depsgraph_get()
    origin = Vector((x, y0, z))
    for _ in range(8):
        hit, loc, nrm, idx, ob, mtx = bpy.context.scene.ray_cast(dg, origin, Vector((0, 1, 0)), distance=maxd)
        if not hit:
            return None
        if skip and ob.name.startswith(skip):
            origin = loc + Vector((0, 0.002, 0))
            continue
        return loc.y
    return None


def decal(name, mat, center, size, coll, y, rot_y=0.0):
    """A textured quad facing the camera (-y) at depth y."""
    cx, cz = center
    w, h = size
    r = Matrix.Rotation(rot_y, 3, 'Y')
    pts = [Vector((cx, y, cz)) + r @ Vector(p) for p in ((-w / 2, 0, -h / 2), (w / 2, 0, -h / 2), (w / 2, 0, h / 2), (-w / 2, 0, h / 2))]
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    f = bm.faces.new([bm.verts.new(p) for p in pts])
    for lp, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uvl].uv = t
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def edit_mesh(ob, fn):
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    fn(bm)
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()


def tri_count(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


# =====================================================================================================================
# DL-08 The fall: the goods-lift car in the flooded pit under the near landing
# =====================================================================================================================

def open_cavity():
    """Cut the near landing's slab back to a deck over the pit, and open the shaft's near face below it."""
    x0, x1, back, ceil = CAV['x0'], CAV['x1'], CAV['back'], CAV['ceil']
    fl = bpy.data.objects.get('G4Floor')
    if fl is not None:
        inv = fl.matrix_world.inverted()
        M = fl.matrix_world

        def cut(bm):
            gone = [f for f in bm.faces if (M @ f.calc_center_median()).x < x1 + 0.05]
            ys = [(M @ v.co).y for f in gone for v in f.verts]
            zs = [(M @ v.co).z for f in gone for v in f.verts]
            xs = [(M @ v.co).x for f in gone for v in f.verts]
            assert gone and abs(min(xs) - 80.3) < 0.05 and abs(max(xs) - x1) < 0.05, (min(xs), max(xs))
            ya, yb, za, zb = min(ys), max(ys), min(zs), max(zs)
            bmesh.ops.delete(bm, geom=gone, context='FACES')
            for (xa, xb), (yy0, yy1), (zz0, zz1) in (
                    ((80.3, x1), (ya, yb), (ceil, zb)),                  # the deck over the pit
                    ((80.3, x0), (ya, yb), (za, ceil)),                  # the solid slab left of it
                    ((x0, x1), (back, yb), (za, ceil)),                  # behind it
                    ((x0, x1), (ya, back), (za, PIT_FLOOR))):            # under it
                vs = bx(bm, (xa, xb), (yy0, yy1), (zz0, zz1), mat=0)
                xform(vs, inv)
        edit_mesh(fl, cut)
    sf = bpy.data.objects.get('G4ShaftFaces')
    if sf is not None:
        M = sf.matrix_world
        inv = M.inverted()

        def trim(bm):
            near = [f for f in bm.faces if (M @ f.calc_center_median()).x < x1 + 0.03]
            if not near:
                return
            vs = {v for f in near for v in f.verts}
            xs = [(M @ v.co).x for v in vs]
            ys = [(M @ v.co).y for v in vs]
            zs = [(M @ v.co).z for v in vs]
            bmesh.ops.delete(bm, geom=near, context='FACES')
            xa, xb, ya, yb, za, zb = min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)
            xform(bx(bm, (xa, xb), (ya, yb), (ceil, zb)), inv)
            xform(bx(bm, (xa, xb), (RACK_Y, yb), (za, ceil)), inv)
        edit_mesh(sf, trim)
    sc = bpy.data.objects.get('Sump7Scum')
    if sc is not None:
        M = sc.matrix_world

        def strip(bm):
            gone = [f for f in bm.faces if all((M @ v.co).x < x1 + 0.02 for v in f.verts)]
            bmesh.ops.delete(bm, geom=gone, context='FACES')
        edit_mesh(sc, strip)


def build_pit(coll):
    """The cavity's own surfaces: a panelled back wall like the shaft's, the beams carrying the deck (their cut ends in
    the section), a pipe, the tide line, and the water."""
    from build_d17 import add_cyl
    x0, x1, back, ceil = CAV['x0'], CAV['x1'], CAV['back'], CAV['ceil']

    def pit(bm):
        bx(bm, (x0, x1), (back - 0.04, back), (PIT_FLOOR, ceil), 1)                     # the back wall's panel face
        for k in range(1, 3):                                                          # its panel seams
            xx = x0 + (x1 - x0) * k / 3
            bx(bm, (xx - 0.015, xx + 0.015), (back - 0.06, back - 0.04), (PIT_FLOOR, ceil), 2)
        for xx in (x0 + 0.35, x0 + 1.25, x1 - 0.3):                                     # deck beams, front to back
            bx(bm, (xx - 0.07, xx + 0.07), (SUMP_FRONT, back), (ceil - 0.18, ceil - 0.15), 2)
            bx(bm, (xx - 0.012, xx + 0.012), (SUMP_FRONT, back), (ceil - 0.15, ceil - 0.02), 2)
            bx(bm, (xx - 0.07, xx + 0.07), (SUMP_FRONT, back), (ceil - 0.02, ceil), 2)
        add_cyl(bm, (x0 + 0.02, back - 0.16, ceil - 0.32), (x1 - 0.02, back - 0.16, ceil - 0.32), 0.05, seg=10, mat=2)
        # The tide line: mud on the back wall and the pit's left face, a band of old, higher water above it.
        bx(bm, (x0, x1), (back - 0.046, back - 0.04), (SUMP_WATER - 0.02, SUMP_WATER + 0.07), 3)
        bx(bm, (x0, x1), (back - 0.045, back - 0.041), (SUMP_WATER + 0.28, SUMP_WATER + 0.33), 3)
        bx(bm, (x0, x0 + 0.006), (SUMP_FRONT, back), (SUMP_WATER - 0.02, SUMP_WATER + 0.07), 3)
        bx(bm, (x0, x0 + 0.005), (SUMP_FRONT, back), (SUMP_WATER + 0.28, SUMP_WATER + 0.33), 3)
    solid('StoryFallPit', pit, ['Concrete', 'WallPanel', 'DepotSteel', 'FloodMud'], coll)

    def water(bm):
        vs = bx(bm, (x0 + 0.003, x1 - 0.002), (SUMP_FRONT, back - 0.045), (-1.3, SUMP_WATER))
        side = [f for f in bm.faces if all(abs(v.co.x - (x1 - 0.002)) < 1e-4 for v in f.verts)]
        bmesh.ops.delete(bm, geom=side, context='FACES')                                 # open to the sump's own water
    solid('StoryFallWater', water, ['Water'], coll)
    note('StoryFallPit', f'DL-08 the flooded pit under the near landing, x {x0}..{x1}, deck underside {ceil}, back wall y {back}')
    note('StoryFallWater', f'DL-08 its water, surface {SUMP_WATER} (game y), joining Sump7Water at x {x1}')


def _car(bm):
    """The goods-lift car, upright in its own space: origin at its floor's centre, 1.2 wide (x), 1.0 deep (y),
    1.7 high; the gate on its front (-y). Built crushed: the posts buckle near the floor."""
    from build_d17 import add_box, add_cyl
    W, D, H = 1.2, 1.0, 1.7
    S, F_, C = 0, 1, 2                                     # ShutterSteel, DepotSteel, (unused)
    bx(bm, (-W / 2, W / 2), (-D / 2, D / 2), (-0.08, 0.0), S)                       # the floor
    for y in (-D / 2 + 0.03, D / 2 - 0.03):
        bx(bm, (-W / 2, W / 2), (y - 0.03, y + 0.03), (-0.16, -0.06), F_)          # its channels
    rnd = random.Random(8)
    for sx in (-1, 1):                                     # corner posts, kinked where the floor came up into them
        for sy in (-1, 1):
            base = Vector((sx * (W / 2 - 0.03), sy * (D / 2 - 0.03), 0.0))
            kink = base + Vector((sx * rnd.uniform(0.03, 0.09), sy * rnd.uniform(0.0, 0.06), 0.28))
            top = Vector((sx * (W / 2 - 0.03), sy * (D / 2 - 0.03), H))
            add_cyl(bm, base, kink, 0.028, seg=6, mat=F_)
            add_cyl(bm, kink, top, 0.028, seg=6, mat=F_)
    bx(bm, (-W / 2, W / 2), (-D / 2, D / 2), (H, H + 0.05), S)                      # the roof
    bx(bm, (-0.08, 0.08), (-D / 2 - 0.04, D / 2 + 0.04), (H + 0.05, H + 0.2), F_)    # the crosshead
    add_cyl(bm, (0, -0.07, H + 0.28), (0, 0.07, H + 0.28), 0.06, seg=10, mat=F_)     # the rope's shackle
    bx(bm, (-0.03, 0.03), (-0.05, 0.05), (H + 0.2, H + 0.3), F_)
    # Sides and back: kick plates to 0.6, a mesh of bars above. The left side (-x) buckled in.
    for sx in (-1, 1):
        bow = -0.06 if sx < 0 else 0.0
        bx(bm, (sx * W / 2 - 0.01 + bow, sx * W / 2 + 0.01 + bow), (-D / 2, D / 2), (0.0, 0.6), S)
        for k in range(6):
            y = -D / 2 + 0.08 + k * (D - 0.16) / 5
            add_box(bm, (sx * W / 2 + bow * 0.5, y, (0.6 + H) / 2), (0.015, 0.015, H - 0.6), mat=F_)
        bx(bm, (sx * W / 2 - 0.02, sx * W / 2 + 0.02), (-D / 2, D / 2), (1.15, 1.19), F_)
    bx(bm, (-W / 2, W / 2), (D / 2 - 0.01, D / 2 + 0.01), (0.0, 0.6), S)
    for k in range(7):
        x = -W / 2 + 0.08 + k * (W - 0.16) / 6
        add_box(bm, (x, D / 2, (0.6 + H) / 2), (0.015, 0.015, H - 0.6), mat=F_)
    bx(bm, (-W / 2, W / 2), (D / 2 - 0.02, D / 2 + 0.02), (1.15, 1.19), F_)
    # The front: the gate's track over the opening, and its lattice burst out (see _gate).
    bx(bm, (-W / 2, W / 2), (-D / 2 - 0.03, -D / 2 + 0.01), (H - 0.1, H - 0.04), F_)
    bx(bm, (-W / 2, W / 2), (-D / 2 - 0.03, -D / 2 + 0.01), (0.0, 0.06), F_)


def _gate(bm, mat):
    """The car's collapsible gate, burst outward: two leaves of diagonal lattice, one bowed out from the car's front
    and hanging from its top track, the other torn free and lying out flat (in car space; front is -y)."""
    from build_d17 import add_box
    W, D, H = 1.2, 1.0, 1.7
    y = -D / 2 - 0.02
    # Leaf 1: from the left post, bowed out toward the camera, hanging from the track.
    n = 6
    for k in range(n + 1):
        x = -W / 2 + 0.04 + k * 0.1
        bow = -0.32 * math.sin(math.pi * k / n)
        add_box(bm, (x, y + bow, H / 2 + 0.05), (0.014, 0.014, H - 0.2), mat=mat)
        if k < n:
            for z in (0.35, 0.85, 1.35):
                a = Vector((x, y + bow, z - 0.25))
                e = Vector((x + 0.1, y - 0.32 * math.sin(math.pi * (k + 1) / n), z + 0.25))
                for p, q in ((a, e), (a + Vector((0, 0, 0.5)), e - Vector((0, 0, 0.5)))):
                    c, d = (p + q) / 2, q - p
                    add_box(bm, c, (0.012, 0.012, d.length),
                            mat=mat, rot=Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4())
    # Leaf 2: torn off its track, lying out over the water from the car's foot.
    M = Matrix.Translation((0.25, y - 0.15, 0.0)) @ rot('X', 78) @ rot('Z', 8)
    for k in range(5):
        vs = add_box(bm, (k * 0.1, 0, 0.7), (0.014, 0.014, 1.3), mat=mat)
        xform(vs, M)
        if k < 4:
            for z in (0.3, 0.75, 1.2):
                for s in (-1, 1):
                    vs = add_box(bm, (k * 0.1 + 0.05, 0, z), (0.012, 0.012, 0.52), mat=mat, rot=rot('Y', s * 11))
                    xform(vs, M)


def _cable(bm, mat, coil_c, end_up):
    """The snapped hoist rope, fallen after the car: loose loops piled on it, a tail over the edge, the frayed end
    standing up with its strands splayed."""
    from build_d17 import add_cyl
    rnd = random.Random(31)
    pts = []
    for k in range(int(4.6 * 24)):
        t = k / 24
        r = 0.34 - 0.03 * t + 0.04 * math.sin(t * 5.1)
        a = 2 * math.pi * t
        pts.append(coil_c + Vector((r * math.cos(a) * 1.15, r * math.sin(a) * 0.8, 0.028 * t + 0.02 * math.sin(a * 2.3))))
    tail = [pts[-1] + Vector((0.12 * i, -0.06 * i, -0.09 * i * i)) for i in range(1, 8)]
    for a, b in zip(pts + tail[:-1], pts[1:] + tail):
        add_cyl(bm, a, b, 0.016, seg=6, mat=mat)
    # The frayed end, standing out of the pile.
    a = coil_c + Vector((-0.2, 0.05, 0.05))
    e = a + end_up
    add_cyl(bm, a, e, 0.017, seg=6, mat=mat)
    for k in range(7):
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.5, 1.6))).normalized() * rnd.uniform(0.08, 0.16)
        add_cyl(bm, e, e + d, 0.004, seg=4, mat=mat)


def _suitcase(bm, c, size, R, mat, strap=None, open_lid=0.0):
    """A suitcase (or trunk): body, a lid seam, corners, a handle; strap straps round it."""
    from build_d17 import add_box, add_cyl, add_torus
    sx, sy, sz = size
    M = Matrix.Translation(c) @ R
    out = []
    out += add_box(bm, (0, 0, 0), (sx, sy, sz * (0.62 if open_lid else 1.0)), mat=mat)
    if open_lid:                                           # the lid flung back, clothes spilling over its lip
        out += add_box(bm, (0, sy / 2 + 0.02, sz * 0.31 + sy * 0.4 * math.sin(math.radians(open_lid))), (sx, 0.03, sy * 0.85),
                       mat=mat, rot=rot('X', -open_lid + 90))
    else:
        out += add_box(bm, (0, 0, sz * 0.12), (sx + 0.008, sy + 0.008, 0.012), mat=strap if strap is not None else mat)
    out += add_cyl(bm, (-0.06, -sy / 2 - 0.02, sz * 0.3), (0.06, -sy / 2 - 0.02, sz * 0.3), 0.012, seg=6, mat=mat)
    if strap is not None:
        for x in (-sx * 0.3, sx * 0.3):
            out += add_box(bm, (x, 0, 0), (0.04, sy + 0.012, sz + 0.012), mat=strap)
    xform(out, M)
    return out


def _coat(bm, c, yaw, mat, spread=1.0, drape=None):
    """A long coat lying face down, sleeves out: from above and from the side it reads as somebody. No head, no
    hands: the collar ends at the water (or the edge)."""
    from build_d17 import add_box, add_cyl, add_sphere
    out = []
    out += add_sphere(bm, (0, 0, 0), 0.3, seg=10, scale=(1.0, 0.62, 0.17), mat=mat)            # the back, shoulders
    out += add_sphere(bm, (-0.42, 0, -0.01), 0.3, seg=10, scale=(1.05, 0.6, 0.12), mat=mat)    # the skirt, spread
    out += add_box(bm, (0.3, 0, 0.02), (0.08, 0.26, 0.07), mat=mat)                            # the collar
    for s in (-1, 1):                                                                         # sleeves
        sh = Vector((0.18, s * 0.17, 0.0))
        el = sh + Vector((-0.05 + 0.1 * spread, s * 0.26 * spread, -0.03))
        wr = el + Vector((0.12 * spread, s * 0.18, -0.04))
        out += add_cyl(bm, sh, el, 0.07, 0.06, seg=7, mat=mat)
        out += add_cyl(bm, el, wr, 0.06, 0.055, seg=7, mat=mat)
    M = Matrix.Translation(c) @ rot('Z', yaw) @ (drape or Matrix.Identity(4))
    xform(out, M)
    return out


def _pram(bm, c, R, body, tyre, metal):
    """A coach-built pram: a deep body, its hood half up, a handle, four spoked wheels (big at the back); in its own
    space the axles run along y and the hood is at -x."""
    from build_d17 import add_box, add_cyl, add_sphere, add_torus
    out = []
    out += add_sphere(bm, (0, 0, 0.5), 0.38, seg=12, scale=(1.0, 0.55, 0.42), mat=body)       # the body
    out += add_sphere(bm, (-0.22, 0, 0.62), 0.27, seg=10, scale=(0.8, 1.05, 1.0), mat=body)   # the hood
    out += add_cyl(bm, (0.3, -0.2, 0.62), (0.62, -0.2, 0.98), 0.012, seg=6, mat=metal)       # the handle
    out += add_cyl(bm, (0.3, 0.2, 0.62), (0.62, 0.2, 0.98), 0.012, seg=6, mat=metal)
    out += add_cyl(bm, (0.62, -0.22, 0.98), (0.62, 0.22, 0.98), 0.016, seg=6, mat=tyre)
    for x, r in ((-0.25, 0.17), (0.25, 0.22)):
        for s in (-1, 1):
            wc = Vector((x, s * 0.25, r))
            out += add_torus(bm, wc, (0, 1, 0), r, 0.014, seg=16, rseg=4, mat=tyre)
            for k in range(5):
                a = k * math.pi / 5
                d = Vector((math.cos(a), 0, math.sin(a))) * r
                out += add_cyl(bm, wc - d, wc + d, 0.004, seg=4, mat=metal)
        out += add_cyl(bm, (x, -0.26, r), (x, 0.26, r), 0.01, seg=6, mat=metal)
        out += add_box(bm, (x * 0.6, 0, (r + 0.32) / 2), (0.03, 0.4, 0.03), mat=metal)
    xform(out, Matrix.Translation(c) @ R)
    return out


def build_wreck(coll):
    """The car on its side in the pit, half under, its roof end raised toward the shaft; what it carried around it."""
    from build_d17 import add_box, add_cyl, add_sphere
    # The car: toppled onto its right side (its top toward +x, toward the shaft), the long axis 20 degrees up,
    # turned a little, its floor end deep in the water at the cavity's far left.
    car_at = Vector((83.86, -0.32, -0.63))
    R = rot('Z', -7) @ rot('Y', 70) @ rot('X', -6)
    M = Matrix.Translation(car_at) @ R
    up = (R @ Vector((-1, 0, 0, 0))).to_3d()               # the car's left side, now facing up
    axis = (R @ Vector((0, 0, 1, 0))).to_3d()

    def wreck(bm):
        # 0 ShutterSteel, 1 DepotSteel, 2 WornIron, 3 LuggageLeather, 4 LuggageCanvas, 5 CoatWool, 6 HandleBlack, 7 Rubber
        tmp = bmesh.new()
        _car(tmp)
        _gate(tmp, 1)
        bmesh.ops.transform(tmp, matrix=M, verts=tmp.verts)
        me = bpy.data.meshes.new('_car')
        tmp.to_mesh(me)
        tmp.free()
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
        # The rope, piled on the car's upturned side about two thirds of the way up it.
        top = car_at + axis * 1.0 + up * 0.62
        _cable(bm, 2, top, Vector((0.12, -0.05, 0.42)))
        # The luggage: a trunk wedged in the gate, a case burst open on the car's side, cases floating.
        _suitcase(bm, car_at + axis * 0.55 + Vector((0, -0.62, 0.05)), (0.62, 0.36, 0.34), rot('Z', 18) @ rot('X', -24), 3, strap=4)
        _suitcase(bm, top + Vector((-0.42, -0.12, 0.08)), (0.5, 0.3, 0.14), rot('Z', -30) @ rot('Y', -12), 3, open_lid=120)
        add_sphere(bm, top + Vector((-0.36, -0.36, 0.12)), 0.14, seg=8, scale=(1.4, 1.0, 0.45), mat=5)  # clothes out of it
        for c, s, r, mt in (((84.45, -1.32, SUMP_WATER - 0.05), (0.5, 0.3, 0.17), rot('Z', 12) @ rot('Y', 9), 4),
                            ((85.25, -1.05, SUMP_WATER - 0.07), (0.44, 0.28, 0.16), rot('Z', -38) @ rot('X', 14), 3),
                            ((83.55, -1.38, SUMP_WATER - 0.09), (0.4, 0.26, 0.15), rot('Z', 64) @ rot('Y', -25), 4),
                            ((85.35, 0.62, SUMP_WATER - 0.04), (0.56, 0.32, 0.2), rot('Z', 80) @ rot('Y', 6), 3)):
            _suitcase(bm, Vector(c), s, r, mt, strap=4 if mt == 3 else None)
        # Coats: two face down in the water, one hung half out of the car's mouth over the torn gate.
        _coat(bm, Vector((84.95, -1.28, SUMP_WATER + 0.01)), 196, 5, spread=1.0)
        _coat(bm, Vector((83.62, -0.98, SUMP_WATER + 0.0)), 128, 5, spread=0.7)
        _coat(bm, car_at + axis * 1.15 + Vector((0.0, -0.66, 0.0)), 262, 5, spread=0.4, drape=rot('Y', 38) @ rot('X', 20))
        # A hat, floating.
        add_cyl(bm, (84.38, -0.9, SUMP_WATER - 0.01), (84.38, -0.9, SUMP_WATER + 0.02), 0.17, seg=14, mat=5)
        add_cyl(bm, (84.38, -0.9, SUMP_WATER + 0.02), (84.38, -0.9, SUMP_WATER + 0.11), 0.1, 0.09, seg=12, mat=5)
        # The pram, nose down at the pit's left, a big wheel up out of the water toward the camera.
        _pram(bm, Vector((83.62, -1.06, SUMP_WATER - 0.62)), rot('Z', 8) @ rot('Y', -52), 6, 7, 1)
        # Odds: a shoe, a bundle, letters, on the car's side and the water.
        add_box(bm, top + Vector((0.3, -0.2, 0.04)), (0.11, 0.05, 0.05), mat=3, rot=rot('Z', 40))
        add_sphere(bm, car_at + axis * 1.45 + up * 0.62 + Vector((0, 0.15, 0.1)), 0.16, seg=8, scale=(1.2, 1.0, 0.7), mat=4)
    ob = solid('StoryFallWreck', wreck, ['ShutterSteel', 'DepotSteel', 'WornIron', 'LuggageLeather', 'LuggageCanvas',
                                         'CoatWool', 'HandleBlack', 'Rubber'], coll, sharp=40)
    note('StoryFallWreck', f'DL-08 the goods-lift car on its side in the pit, half under (car floor at {tuple(round(v, 2) for v in car_at)}), '
                           'its rope piled on it, luggage, coats and a pram spilled; all of it at x < 85.8')
    return ob


def build_fall(coll):
    open_cavity()
    build_pit(coll)
    build_wreck(coll)


# =====================================================================================================================
# DL-09 The cut bridge: far detail across the atrium's void
# =====================================================================================================================

# The gap's centre, the bridge's heading (horizontal, from the near stump toward the far one) and its climb: chosen so
# the near stump, the sign and the gap sit in the coin viewer's frame at its rest yaw, cross the top band of the
# balcony's side view, and run from the lower left to the middle of the awe crane's last frame.
BRIDGE_GAP = Vector((121.5, 72.0, 7.6))
BRIDGE_DIR = Vector((52.0, 53.5, 0.0)).normalized()
BRIDGE_SLOPE = 0.115                  # rise per metre along it
BRIDGE_GAP_LEN = 17.0
BRIDGE_W = 6.0                        # the deck's width
TRUSS_H = 3.2
VIEWER_EYE = Vector((114.7, -0.25, 2.7))   # the coin viewer's eyepieces (game (X + 0.1, Y + 1.1, 0.25))
EYES = [Vector((x, y, z)) for x in (110.0, 121.0) for y in (-9.0, 0.0) for z in (1.5, 10.0)]
VIADUCT_NEAR = (76.0, 84.0, -2.0)     # art/dl04 VIADUCTS[0]: the old viaduct under the far stump (y range, deck z)
CATWALK_Y = (41.5, 46.5)              # art/dl04's low catwalk at y 44: no pier there


def _seen(c, n):
    return any(n.dot(e - c) > 0.0 for e in EYES)


def _quad(bm, pts, mat):
    c = sum(pts, Vector()) / len(pts)
    n = (pts[1] - pts[0]).cross(pts[2] - pts[0])
    if n.length < 1e-9:
        return
    n.normalize()
    if not _seen(c, n):
        if not _seen(c, -n):
            return
        pts = pts[::-1]
    f = bm.faces.new([bm.verts.new(p) for p in pts])
    f.material_index = mat


def _beam(bm, a, e, w, h, mat, up=Vector((0, 0, 1))):
    """A box from a to e, w wide and h deep: only the faces that face the balcony."""
    a, e = Vector(a), Vector(e)
    d = (e - a)
    if d.length < 1e-6:
        return
    T = d.normalized()
    S = T.cross(up)
    if S.length < 1e-4:
        S = T.cross(Vector((1, 0, 0)))
    S.normalize()
    U = S.cross(T).normalized()
    c = [a + S * sx * w / 2 + U * sz * h / 2 for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    c2 = [p + d for p in c]
    for i in range(4):
        j = (i + 1) % 4
        _quad(bm, [c[i], c[j], c2[j], c2[i]], mat)
    _quad(bm, c[::-1], mat)
    _quad(bm, c2, mat)


def _rock_hit(origin, direction, maxd=80.0):
    """Where a ray first meets the chasm's rock (AtriumRock), in world space."""
    rock = bpy.data.objects.get('AtriumRock')
    if rock is None:
        return None
    inv = rock.matrix_world.inverted()
    o = inv @ origin
    d = (inv.to_3x3() @ direction).normalized()
    ok, loc, nrm, idx = rock.ray_cast(o, d, distance=maxd)
    return rock.matrix_world @ loc if ok else None


def _at(s):
    """The deck's top centre at s metres along the bridge from the gap's centre (negative: toward the near end)."""
    return BRIDGE_GAP + BRIDGE_DIR * s + Vector((0, 0, BRIDGE_SLOPE * s))


def _break_end(b, p, T, S, sign, rnd):
    """A blown end at p (deck top centre), the void toward T * sign: the deck torn ragged and drooping, girders bent
    down and twisted out, cables hanging into the void."""
    U = Vector((0, 0, 1))
    out = T * sign
    for k, sx in enumerate((-0.38, -0.1, 0.18, 0.4)):                              # ragged deck chunks, drooping
        a = p + S * (sx * BRIDGE_W) + U * -0.3
        ln = rnd.uniform(0.6, 2.4)
        e = a + out * ln + U * -ln * rnd.uniform(0.3, 0.9) + S * rnd.uniform(-0.4, 0.4)
        _beam(b['steel'], a, e, BRIDGE_W * 0.22, 0.5, 0)
    for side in (-1, 1):                                                        # the girders, bent and twisted
        base = p + S * (side * BRIDGE_W / 2)
        a = base + out * 0.2
        e = a + out * rnd.uniform(2.0, 3.5) + U * -rnd.uniform(1.5, 3.0) + S * side * rnd.uniform(0.5, 1.5)
        f = e + out * rnd.uniform(0.5, 1.5) + U * -rnd.uniform(2.0, 4.0) + S * side * rnd.uniform(0.2, 1.0)
        _beam(b['rust'], a, e, 0.4, 0.5, 0)
        _beam(b['rust'], e, f, 0.35, 0.45, 0)
        top = base + U * TRUSS_H
        e2 = top + out * rnd.uniform(1.5, 3.0) + U * rnd.uniform(-0.5, 1.2) + S * side * rnd.uniform(0.8, 2.0)
        _beam(b['rust'], top, e2, 0.35, 0.4, 0)
        e3 = e2 + U * -rnd.uniform(2.5, 4.5) + out * 0.4
        _beam(b['rust'], e2, e3, 0.3, 0.3, 0)
    for k in range(6):                                                         # cables, hanging into the void
        a = p + S * rnd.uniform(-BRIDGE_W / 2, BRIDGE_W / 2) + out * rnd.uniform(0.2, 1.6) + U * -rnd.uniform(0.2, 0.8)
        ln = rnd.uniform(6.0, 22.0)
        e = a + U * -ln + out * rnd.uniform(-0.8, 1.2) + S * rnd.uniform(-0.8, 0.8)
        _beam(b['cable'], a, e, 0.09, 0.09, 0)
        if k == 2:                                                             # a slab of deck dangling on one
            _beam(b['steel'], e + U * 0.4, e + U * -1.6 + S * 0.6, 1.4, 0.25, 0)


def build_bridge(coll):
    rnd = random.Random(909)
    keys = ('masonry', 'steel', 'rust', 'cable', 'junk', 'cloth', 'red', 'lamp', 'glow')
    b = {k: bmesh.new() for k in keys}
    T, U = BRIDGE_DIR, Vector((0, 0, 1))
    S = T.cross(U).normalized()                          # across the deck (to its right, looking along T)
    half = BRIDGE_GAP_LEN / 2
    # The ends: where the line meets the rock, each a little into it.
    near_hit = _rock_hit(_at(-half), -(T + U * BRIDGE_SLOPE).normalized())
    far_hit = _rock_hit(_at(half), (T + U * BRIDGE_SLOPE).normalized())
    s_near = -half - ((near_hit - _at(-half)).length if near_hit else 30.0) - 1.5
    s_far = half + ((far_hit - _at(half)).length if far_hit else 30.0) + 1.5
    print(f'story_shafts: bridge near end s {s_near:.1f} at {tuple(round(v, 1) for v in _at(s_near))}, '
          f'far end s {s_far:.1f} at {tuple(round(v, 1) for v in _at(s_far))}')

    def span(s0, s1):
        """Deck, kerbs and the two through-trusses from s0 to s1."""
        a, e = _at(s0), _at(s1)
        _beam(b['steel'], a + U * -0.35, e + U * -0.35, BRIDGE_W, 0.7, 0)                       # deck
        n = max(1, int(round(abs(s1 - s0) / 4.5)))
        for side in (-1, 1):
            o = S * (side * BRIDGE_W / 2)
            _beam(b['steel'], a + o, e + o, 0.4, 0.55, 0)                                       # bottom chord
            _beam(b['steel'], a + o + U * TRUSS_H, e + o + U * TRUSS_H, 0.4, 0.45, 0)          # top chord
            for i in range(n + 1):
                p = a.lerp(e, i / n) + o
                _beam(b['steel'], p, p + U * TRUSS_H, 0.3, 0.3, 0)                               # verticals
                if i < n:
                    q = a.lerp(e, (i + 1) / n) + o
                    if i % 2 == 0:
                        _beam(b['steel'], p, q + U * TRUSS_H, 0.25, 0.25, 0)
                    else:
                        _beam(b['steel'], p + U * TRUSS_H, q, 0.25, 0.25, 0)
        for i in range(0, n + 1, 2):                                                             # top bracing
            p = a.lerp(e, i / n) + U * TRUSS_H
            _beam(b['steel'], p - S * BRIDGE_W / 2, p + S * BRIDGE_W / 2, 0.25, 0.25, 0)

    def pier(s, base_z):
        p = _at(s) + U * -0.7
        h = p.z - base_z
        for k, (w0, w1) in enumerate(((3.2, 2.2),)):
            c0 = Vector((p.x, p.y, base_z))
            # A tapered pier: four faces from a wide foot to the deck's underside, a cap under the bearings.
            pts0 = [c0 + T * (sx * w0 / 2) + S * (sy * (BRIDGE_W + 1.2) / 2) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
            pts1 = [Vector((q.x, q.y, p.z - 0.5)) + (Vector((p.x, p.y, 0)) - Vector((q.x, q.y, 0))) * (1 - w1 / w0) for q in pts0]
            for i in range(4):
                j = (i + 1) % 4
                _quad(b['masonry'], [pts0[i], pts0[j], pts1[j], pts1[i]], 0)
            _beam(b['masonry'], p + U * -0.5 - T * (w1 / 2 + 0.3), p + U * -0.5 + T * (w1 / 2 + 0.3), BRIDGE_W + 1.6, 0.6, 0)

    # The stumps.
    s_n1, s_f0 = -half, half
    span(s_near, s_n1)
    span(s_f0, s_far)
    _break_end(b, _at(s_n1), T, S, 1, rnd)
    _break_end(b, _at(s_f0), T, S, -1, rnd)
    # Piers: under each stump (none on the catwalk's line); the far stump's first stands on the old viaduct's deck.
    for s in (s_near + 0.45 * (s_n1 - s_near), s_n1 - 3.0, s_f0 + 3.0, s_f0 + 0.55 * (s_far - s_f0)):
        y = _at(s).y
        if CATWALK_Y[0] <= y <= CATWALK_Y[1]:
            s += 6.0
            y = _at(s).y
        on_viaduct = VIADUCT_NEAR[0] <= y <= VIADUCT_NEAR[1]
        pier(s, VIADUCT_NEAR[2] if on_viaduct else -44.0)
    # Abutments: masonry blocks into the rock at both ends.
    for s, d in ((s_near, -1), (s_far, 1)):
        p = _at(s)
        _beam(b['masonry'], p + T * (d * -3.0) + U * -0.8, p + T * (d * 4.0) + U * -0.8, BRIDGE_W + 2.0, 6.0, 0)

    # The near stump: a barricade across it 4 m short of the break, belongings heaped against it, the sign at the end.
    s_bar = s_n1 - 4.5
    bar = _at(s_bar)
    for k in range(9):                                     # beds, doors, timbers and sheets on end, leaning out
        o = S * (-BRIDGE_W / 2 + 0.4 + k * (BRIDGE_W - 0.8) / 8)
        lean = T * rnd.uniform(-0.9, -0.2)
        h = rnd.uniform(1.6, 2.6)
        _beam(b['junk'] if k % 3 else b['steel'], bar + o, bar + o + lean + U * h, rnd.uniform(0.6, 1.1), 0.12, 0)
    _beam(b['junk'], bar + S * (-BRIDGE_W / 2) + U * 1.2, bar + S * (BRIDGE_W / 2) + U * 1.5 + T * -0.3, 0.25, 0.25, 0)
    for side in (-1, 1):                                   # crossed timbers, their ends standing out
        p = bar + S * (side * BRIDGE_W * 0.3) + T * -0.6
        _beam(b['junk'], p + U * 0.0 + S * -0.9, p + U * 2.4 + S * 0.9, 0.22, 0.22, 0)
        _beam(b['junk'], p + U * 0.0 + S * 0.9, p + U * 2.4 + S * -0.9, 0.22, 0.22, 0)
    _beam(b['red'], bar + T * 0.6 + S * (-BRIDGE_W / 2 - 0.3) + U * 1.0, bar + T * 0.6 + S * (BRIDGE_W / 2 + 0.6) + U * 1.0,
          0.16, 0.16, 0)                                    # the checkpoint's boom, still down
    for k in range(70):                                    # the heap: cases, bundles, a cart, chairs, against it
        d = rnd.random() ** 1.6 * 13.0                      # thickest against the barricade
        p = _at(s_bar - 0.8 - d) + S * rnd.uniform(-BRIDGE_W / 2 + 0.3, BRIDGE_W / 2 - 0.3)
        hgt = (1.0 - d / 13.0) * 1.3 * rnd.uniform(0.3, 1.0)
        sz = rnd.uniform(0.35, 0.9)
        bk = b['cloth'] if rnd.random() < 0.55 else b['junk']
        a = p + U * hgt * 0.3
        _beam(bk, a, a + U * sz * rnd.uniform(0.5, 1.0) + T * rnd.uniform(-0.2, 0.2), sz * rnd.uniform(0.9, 1.6), sz, 0)
    for k in range(3):                                     # handcarts on their noses, wheels up
        p = _at(s_bar - rnd.uniform(4.0, 11.0)) + S * rnd.uniform(-2.0, 2.0)
        _beam(b['junk'], p, p + U * 1.3 + T * 0.5, 0.9, 0.12, 0)
        _beam(b['steel'], p + U * 1.25 + T * 0.45 - S * 0.5, p + U * 1.25 + T * 0.45 + S * 0.5, 0.1, 0.1, 0)
    # The sign: a board on two posts at the stump's end, turned to face the balcony and the coin viewer.
    end = _at(s_n1 - 1.2)
    to_eye = Vector((VIEWER_EYE.x - end.x, VIEWER_EYE.y - end.y, 0)).normalized()
    side = to_eye.cross(U).normalized()
    sw, sh, sz0 = 4.4, 2.2, 1.7
    for sx in (-1, 1):
        q = end + side * (sx * sw * 0.36)
        _beam(b['steel'], q, q + U * (sz0 + sh), 0.18, 0.18, 0)
    c = end + U * (sz0 + sh / 2) + to_eye * 0.12
    sign_pts = [c + side * (sx * sw / 2) + U * (sz * sh / 2) for sx, sz in ((1, -1), (-1, -1), (-1, 1), (1, 1))]
    # The far stump: lamps on posts along it, still lit, and the lit gate it runs into on the far side.
    s = s_f0 + 2.0
    while s < s_far - 3.0:
        for side_ in (-1, 1):
            q = _at(s) + S * (side_ * (BRIDGE_W / 2 + 0.25))
            _beam(b['steel'], q, q + U * (TRUSS_H + 1.2), 0.15, 0.15, 0)
            _beam(b['lamp'], q + U * (TRUSS_H + 1.2), q + U * (TRUSS_H + 1.65), 0.45, 0.45, 0)
        s += 5.5
    g = _at(s_far - 2.5)
    for side_ in (-1, 1):                                  # the gatehouse: two towers and an arch over the deck
        q = g + S * (side_ * (BRIDGE_W / 2 + 1.4))
        _beam(b['masonry'], q + U * -1.0, q + U * 11.0, 2.6, 3.0, 0)
        _beam(b['masonry'], q + U * 11.0, q + U * 12.6, 3.2, 3.6, 0)
        for zz in (5.0, 8.0):
            w0 = q - T * 1.52 + U * zz
            _quad(b['glow'], [w0 + S * -0.4, w0 + S * 0.4, w0 + S * 0.4 + U * 1.3, w0 + S * -0.4 + U * 1.3], 0)
    _beam(b['masonry'], g + S * (-BRIDGE_W / 2 - 1.4) + U * 8.0, g + S * (BRIDGE_W / 2 + 1.4) + U * 8.0, 2.4, 3.0, 0)
    w0 = g - T * 0.3 + U * 0.2                              # the gate's mouth, lit from within
    _quad(b['glow'], [w0 + S * (-BRIDGE_W / 2 + 0.2), w0 + S * (BRIDGE_W / 2 - 0.2), w0 + S * (BRIDGE_W / 2 - 0.2) + U * 6.2,
                      w0 + S * (-BRIDGE_W / 2 + 0.2) + U * 6.2], 0)

    mats = {'masonry': 'AtriumMasonry', 'steel': 'AtriumSheet', 'rust': 'AtriumRust', 'cable': 'Rubber', 'junk': 'AtriumWood',
            'cloth': 'AtriumCloth', 'red': 'Barricade', 'lamp': 'RingLamp', 'glow': 'AtriumWindowGlow'}
    names = {'masonry': 'AtriumCutBridgeMasonry', 'steel': 'AtriumCutBridgeSteel', 'rust': 'AtriumCutBridgeTwisted',
             'cable': 'AtriumCutBridgeCables', 'junk': 'AtriumCutBridgeJunk', 'cloth': 'AtriumCutBridgeBundles',
             'red': 'AtriumCutBridgeBoom', 'lamp': 'AtriumCutBridgeLamps', 'glow': 'AtriumCutBridgeGlow'}
    import build_d17 as d17
    for k in keys:
        if not len(b[k].faces):
            b[k].free()
            continue
        me = bpy.data.meshes.new(names[k])
        b[k].to_mesh(me)
        b[k].free()
        me.materials.append(material(mats[k]))
        ob = bpy.data.objects.new(names[k], me)
        coll.objects.link(ob)
        note(names[k], f'DL-09 the cut bridge ({k})')
    # The sign: its own quad with the painted board.
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new('UVMap')
    f = bm.faces.new([bm.verts.new(p) for p in sign_pts])
    for lp, t in zip(f.loops, ((0, 0), (1, 0), (1, 1), (0, 1))):
        lp[uvl].uv = t
    f.normal_update()
    if f.normal.dot(to_eye) < 0:
        f.normal_flip()
    me = bpy.data.meshes.new('AtriumCutBridgeSign')
    bm.to_mesh(me)
    bm.free()
    me.materials.append(image_mat('GradeSignMat', 'grade', rough=0.8))
    ob = bpy.data.objects.new('AtriumCutBridgeSign', me)
    coll.objects.link(ob)
    note('AtriumCutBridgeSign', f'DL-09 GRADE 1-2 BEYOND THIS POINT, {sw} x {sh} m, centre {tuple(round(v, 1) for v in c)}, facing the coin viewer')


# =====================================================================================================================
# RING C stencils, DL-06 to DL-09: the same stencil at each scene's way on
# =====================================================================================================================

STENCIL_SIZE = (0.84, 0.42)
# name: (centre x, centre z, the y to stand in front of (None: the first wall behind), why there)
STENCILS = {
    'WayRingC06': (72.6, 2.3, None, 'DL-06: over the service ramp\'s head, where the carrier brings him up to the gallery'),
    'WayRingC07': (80.0, 2.05, None, 'DL-07: beside the residential door, the gallery\'s way on'),
    'WayRingC08': (97.0, 2.3, None, 'DL-08: at the belt\'s end, by the way on to the cage'),
    'WayRingC09': (118.4, 2.2, None, 'DL-09: at the balcony\'s end, over the stair down'),
}


def ring_c_material():
    """Shared by name with the other pass 4 modules: whichever runs first makes it."""
    mt = bpy.data.materials.get('WayRingCMat')
    return mt if mt is not None else image_mat('WayRingCMat', 'ringc', rough=0.85)


def build_stencils(coll):
    mat = ring_c_material()
    for name, (x, z, y, why) in STENCILS.items():
        if y is None:
            hits = [wall_y(x + u * STENCIL_SIZE[0] * 0.4, z + v * STENCIL_SIZE[1] * 0.4) for u in (-1, 0, 1) for v in (-1, 0, 1)]
            hits = sorted(t for t in hits if t is not None)
            if not hits:
                print('story_shafts: no wall behind', name)
                continue
            med = hits[len(hits) // 2]
            y = min(t for t in hits if med - 0.1 <= t <= med + 0.02) - 0.005
        decal(name, mat, (x, z), STENCIL_SIZE, coll, y, rot_y=math.radians(random.Random(name).uniform(-2.5, 2.5)))
        note(name, f'{why}; centre ({x}, {z}) at y {y:.3f}')


# =====================================================================================================================
# build_set
# =====================================================================================================================

def report(coll_objs):
    for n, what in PLACED:
        ob = bpy.data.objects.get(n)
        if ob is None:
            print(f'story_shafts: {n}: MISSING')
            continue
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        mn = [min(v[i] for v in bb) for i in range(3)]
        mx = [max(v[i] for v in bb) for i in range(3)]
        mats = [s.material.name for s in ob.material_slots if s.material]
        print(f'story_shafts: {n}: tris {tri_count(ob)}, mats {mats}, Blender x {mn[0]:.2f}..{mx[0]:.2f} y {mn[1]:.2f}..{mx[1]:.2f} '
              f'z {mn[2]:.2f}..{mx[2]:.2f} :: {what}')


def build_set(dl01, m, coll):
    PLACED.clear()
    bpy.context.view_layer.update()
    build_fall(coll)
    build_bridge(coll)
    bpy.context.view_layer.update()
    build_stencils(coll)
    report(coll)


def add_clips(dl01, arm):
    pass
