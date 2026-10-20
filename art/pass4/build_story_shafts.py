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
