"""The White: a pale, blind cave animal like a giant olm (docs/chapter1_pass2_plan.md, section 2).

    build_white(dl01, coll)   called from art/dl01/build_dl01.py main(); exported as white.glb

One skinned mesh (materials WhiteSkin, WhiteGill, WhiteMouth) on one armature, with every clip as its own
action stashed on an NLA track, as D-17's are.

Layout (metres, Blender Z up; the game sees (x, y, z) as (x, z, -y)):
  - head toward +x; at rest the snout tip is at x = 0 and the tail tip at x = -2.5;
  - z = 0 is the water surface; at rest the spine runs at z = -0.13, just under it;
  - the object origin is on the water surface above the snout tip. Clips are in place (the Root bone never moves);
    where a clip reaches forward (Slap, Lunge, Drag, Nose) the body moves through its spine bones only.

The body is posed as a centreline: heading angles along the arc length s (snout s = 0, tail tip s = 2.5) are
integrated from an anchor at mid-body, so the body never stretches. Spine and head bones follow the centreline;
jaw, gills and legs are posed by angle.

Run on its own to build, export and preview it:
    python build_white.py --out <dir> [--preview]
"""
import math
import os
import random
import sys

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Quaternion, Vector  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')
FPS = 24

L = 2.5                     # body length, snout to tail tip
Z0 = -0.13                  # spine line at rest, below the water surface (z = 0)
HEAD_S = 0.28               # the head bone pivots here (where the neck starts)
SPINE_S = [0.28, 0.42, 0.58, 0.76, 0.95, 1.14, 1.33, 1.52, 1.71, 1.89, 2.06, 2.22, 2.37, 2.5]
DS = 0.01
NS = int(round(L / DS))
ANCHOR_K = 120              # s = 1.2: the pose anchor (mid-body)

# Where the authored strikes land (shared with the game; see the report in the commit).
LEDGE_X = 0.78              # the ledge edge the Slap and Lunge are authored against
LEDGE_Z = 0.25              # its top, above the water surface
SLAP_SNOUT = Vector((0.95, 0.0, 0.31))
LUNGE_SNOUT = Vector((1.32, 0.0, 0.40))
NOSE_X = 0.5                # the step the Nose loop noses at

SIDES = (('L', 1), ('R', -1))
SKIN, GILL, MOUTH = range(3)
JAW_HINGE = Vector((-0.235, 0.0, Z0 - 0.012))
JAW_CHIN = Vector((-0.008, 0.0, Z0 - 0.022))
JAWTIP = Vector((-0.07, 0.0, Z0 - 0.008))       # between the jaws, where a bitten thing is held

# Gills: (base s, base height above the spine line, rest direction, fold direction, flare direction, length)
GILLS = [
    (0.272, 0.032, (-0.55, 0.45, 0.70), (-0.92, 0.25, 0.30), (0.0, 0.75, 0.95), 0.12),
    (0.298, 0.006, (-0.60, 0.70, 0.25), (-0.95, 0.30, 0.05), (0.05, 1.0, 0.20), 0.135),
    (0.324, -0.024, (-0.62, 0.65, -0.25), (-0.93, 0.30, -0.20), (0.0, 0.85, -0.55), 0.115),
]
# Legs: (prefix, hip s, parent bone, upper rest, lower rest, upper tucked, lower tucked, upper reach,
#        lower reach, lengths, toe angles)
LEGS = [
    ('FrontLeg', 0.47, 'Spine02', (0.10, 0.75, -0.65), (0.35, 0.20, -0.90), (-0.85, 0.42, -0.30),
     (-0.95, 0.15, -0.05), (0.60, 0.55, -0.55), (0.75, 0.10, -0.60), (0.08, 0.075), (-20, 15, 50)),
    ('HindLeg', 1.50, 'Spine07', (-0.05, 0.75, -0.65), (0.20, 0.20, -0.95), (-0.90, 0.38, -0.20),
     (-0.98, 0.12, 0.0), (0.40, 0.60, -0.65), (0.60, 0.15, -0.75), (0.085, 0.08), (-10, 35)),
]


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def smooth(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def keys(f, ks, ease=smooth):
    """Piecewise-eased value from [(frame, value), ...]."""
    if f <= ks[0][0]:
        return ks[0][1]
    for (f0, v0), (f1, v1) in zip(ks, ks[1:]):
        if f <= f1:
            return v0 + (v1 - v0) * ease((f - f0) / (f1 - f0))
    return ks[-1][1]


def lin(x):
    return x


def ease_out(x):
    x = min(1.0, max(0.0, x))
    return 1 - (1 - x) ** 3


def ease_in(x):
    x = min(1.0, max(0.0, x))
    return x * x * x


def interp(s, table):
    """Smoothly interpolated profile value at s from [(s, v), ...]."""
    return keys(s, table)


def mirror(v, s):
    return Vector((v[0], v[1] * s, v[2]))


# --------------------------------------------------------------------------
# Body profile (half-width, height above and depth below the spine line, fins)
# --------------------------------------------------------------------------

HW = [(0.0, 0.036), (0.005, 0.042), (0.014, 0.052), (0.03, 0.062), (0.06, 0.07), (0.14, 0.077), (0.22, 0.083),
      (0.28, 0.079), (0.34, 0.074), (0.45, 0.084), (0.7, 0.094), (1.1, 0.097), (1.4, 0.091), (1.6, 0.078),
      (1.8, 0.058), (2.1, 0.038), (2.35, 0.021), (2.5, 0.004)]
TOP = [(0.0, 0.006), (0.005, 0.012), (0.014, 0.02), (0.03, 0.028), (0.08, 0.038), (0.2, 0.05), (0.3, 0.058),
       (0.5, 0.074), (1.0, 0.08), (1.5, 0.078), (1.7, 0.075), (2.0, 0.062), (2.3, 0.038), (2.5, 0.004)]
BOT = [(0.0, 0.004), (0.2, 0.004), (0.34, 0.075), (0.5, 0.086), (1.0, 0.09), (1.5, 0.085), (1.7, 0.075),
       (2.0, 0.056), (2.3, 0.032), (2.5, 0.004)]
FIN_TOP = [(1.2, 0.0), (1.6, 0.02), (1.9, 0.032), (2.2, 0.026), (2.45, 0.01), (2.5, 0.0)]
FIN_BOT = [(1.55, 0.0), (1.75, 0.018), (2.1, 0.024), (2.45, 0.008), (2.5, 0.0)]
JAW_HW = [(0.008, 0.026), (0.02, 0.046), (0.035, 0.055), (0.1, 0.066), (0.2, 0.075), (0.26, 0.072),
          (0.325, 0.048)]
JAW_BOT = [(0.008, 0.012), (0.04, 0.03), (0.12, 0.045), (0.2, 0.058), (0.26, 0.064), (0.325, 0.05)]
JAW_TOP_Z = Z0 - 0.0065     # the mouth floor, just under the palate


def sup(c, n):
    return math.copysign(abs(c) ** (2.0 / n), c)


def section_n(s):
    return interp(s, [(0.0, 2.9), (0.25, 2.8), (0.4, 2.35), (1.6, 2.3), (2.5, 2.2)])


def body_point(s, phi):
    """Rest-pose surface point of the main body at arc length s and angle phi (0 = top, pi/2 = +y side)."""
    n = section_n(s)
    c, sn = math.cos(phi), math.sin(phi)
    hw = interp(s, HW)
    z = (interp(s, TOP) if c >= 0 else interp(s, BOT)) * sup(c, n)
    z += interp(s, FIN_TOP) * max(0.0, c) ** 12 - interp(s, FIN_BOT) * max(0.0, -c) ** 12
    p = Vector((-s, hw * sup(sn, n), Z0 + z))
    # Faint eye pits under the skin, high on the head's sides.
    for side in (1, -1):
        e = Vector((-0.085, side * 0.05, Z0 + 0.03))
        d2 = (p - e).length_squared
        if d2 < 0.0009:
            p += (p - Vector((-s, 0, Z0))).normalized() * -0.004 * math.exp(-d2 / (2 * 0.009 ** 2))
    return p


# --------------------------------------------------------------------------
# Rig
# --------------------------------------------------------------------------

def spine_names():
    return [f'Spine{i + 1:02d}' for i in range(len(SPINE_S) - 1)]


def gill_name(i, side):
    return f'Gill{i + 1}.{side}'


def build_armature(coll):
    data = bpy.data.armatures.new('WhiteRig')
    arm = bpy.data.objects.new('WhiteRig', data)
    coll.objects.link(arm)
    for o in bpy.context.view_layer.objects:
        o.select_set(False)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    eb = data.edit_bones

    def bone(name, head, tail, parent=None, deform=True):
        b = eb.new(name)
        b.head, b.tail = head, tail
        b.roll = 0.0
        b.use_deform = deform
        b.use_connect = False
        if parent:
            b.parent = eb[parent]
        return b

    bone('Root', (0, 0, 0), (0.25, 0, 0), deform=False)
    prev = 'Root'
    for i, name in enumerate(spine_names()):
        bone(name, (-SPINE_S[i], 0, Z0), (-SPINE_S[i + 1], 0, Z0), prev)
        prev = name
    bone('Head', (-HEAD_S, 0, Z0), (0, 0, Z0), 'Spine01')
    bone('Jaw', JAW_HINGE, JAW_CHIN, 'Head')
    bone('JawTip', JAWTIP, JAWTIP + Vector((0.06, 0, 0)), 'Jaw', deform=False)
    for i, (s, dz, rest, _f, _F, ln) in enumerate(GILLS):
        for side, sg in SIDES:
            base = gill_base(i, sg)
            bone(gill_name(i, side), base, base + mirror(Vector(rest).normalized(), sg) * ln, 'Head')
    for (pre, s, parent, up, lo, *_rest) in LEGS:
        lens = _rest[-2]
        for side, sg in SIDES:
            hip, knee, ankle = leg_points(pre, sg)
            bone(f'{pre}Upper.{side}', hip, knee, parent)
            bone(f'{pre}Lower.{side}', knee, ankle, f'{pre}Upper.{side}')
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    return arm


def gill_base(i, sg):
    s, dz = GILLS[i][0], GILLS[i][1]
    hw = interp(s, HW)
    return Vector((-s, sg * hw * 0.92, Z0 + dz))


def leg_points(pre, sg):
    leg = next(lg for lg in LEGS if lg[0] == pre)
    s, up, lo, lens = leg[1], leg[3], leg[4], leg[9]
    hip = Vector((-s, sg * (interp(s, HW) - 0.012), Z0 - 0.045))
    knee = hip + mirror(Vector(up).normalized(), sg) * lens[0]
    ankle = knee + mirror(Vector(lo).normalized(), sg) * lens[1]
    return hip, knee, ankle


# --------------------------------------------------------------------------
# Mesh
# --------------------------------------------------------------------------

def skin_weights(s):
    """Spine/head weights for a point of the body at arc length s."""
    names = spine_names()
    if s < 0.22:
        return {'Head': 1.0}
    if s < 0.34:
        t = smooth((s - 0.22) / 0.12)
        return {'Head': 1 - t, 'Spine01': t}
    mids = [(SPINE_S[i] + SPINE_S[i + 1]) / 2 for i in range(len(names))]
    if s <= mids[0]:
        return {names[0]: 1.0}
    if s >= mids[-1]:
        return {names[-1]: 1.0}
    for i in range(len(mids) - 1):
        if mids[i] <= s < mids[i + 1]:
            t = (s - mids[i]) / (mids[i + 1] - mids[i])
            return {names[i]: 1 - t, names[i + 1]: t}
    return {names[-1]: 1.0}


class MeshBuilder:
    def __init__(self, bone_names):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.dl = self.bm.verts.layers.deform.verify()
        self.gi = {n: i for i, n in enumerate(bone_names)}
        self.names = bone_names

    def vert(self, co, weights):
        v = self.bm.verts.new(co)
        for n, w in weights.items():
            if w > 1e-4:
                v[self.dl][self.gi[n]] = w
        return v

    def face(self, verts, uvs, mat):
        try:
            f = self.bm.faces.new(verts)
        except ValueError:
            return None
        f.material_index = mat
        for loop, uv in zip(f.loops, uvs):
            loop[self.uv].uv = uv
        return f

    def loft(self, rings, uvs, mats, cap0=None, cap1=None, cap_uv=((0, 0), (0, 0))):
        """rings: lists of verts (same count); uvs[i][j]: (u, v) for ring i, vertex j, with uvs[i][n] the seam.
        mats(i, j) -> material of the quad from ring i, vertex j."""
        n = len(rings[0])
        for i in range(len(rings) - 1):
            a, b = rings[i], rings[i + 1]
            for j in range(n):
                j1 = (j + 1) % n
                self.face([a[j], b[j], b[j1], a[j1]],
                          [uvs[i][j], uvs[i + 1][j], uvs[i + 1][j + 1], uvs[i][j + 1]], mats(i, j))
        if cap0 is not None:
            r = rings[0]
            for j in range(n):
                self.face([cap0, r[(j + 1) % n], r[j]], [cap_uv[0], uvs[0][j + 1], uvs[0][j]], mats(0, j))
        if cap1 is not None:
            r = rings[-1]
            for j in range(n):
                self.face([cap1, r[j], r[(j + 1) % n]], [cap_uv[1], uvs[-1][j], uvs[-1][j + 1]],
                          mats(len(rings) - 2, j))


def body_ring_s():
    ss = [0.005, 0.014, 0.026, 0.04, 0.056, 0.074, 0.094, 0.116, 0.14, 0.165, 0.19, 0.215, 0.24, 0.265, 0.29,
          0.315, 0.34]
    s = 0.38
    while s < 1.62:
        ss.append(round(s, 4))
        s += 0.04
    s = 1.62
    while s < 2.49:
        ss.append(round(s, 4))
        s += 0.035
    return ss


def build_body(mb):
    n = 24
    ss = body_ring_s()
    rings, uvs = [], []
    for s in ss:
        w = skin_weights(s)
        ring = [mb.vert(body_point(s, 2 * math.pi * j / n), w) for j in range(n)]
        rings.append(ring)
        uvs.append([(s / L, j / n) for j in range(n + 1)])
    cap0 = mb.vert((0.0, 0.0, Z0 + 0.001), {'Head': 1.0})
    cap1 = mb.vert((-L, 0.0, Z0), skin_weights(L))

    def mats(i, j):
        s = (ss[i] + ss[i + 1]) / 2
        phi = 2 * math.pi * (j + 0.5) / n
        # The palate and the throat's inside: under the head, inboard of the lip.
        if s < 0.27 and math.cos(phi) < -0.05 and abs(math.sin(phi)) < 0.93:
            return MOUTH
        return SKIN
    mb.loft(rings, uvs, mats, cap0, cap1, cap_uv=((0.0, 0.5), (1.0, 0.5)))


def build_jaw(mb):
    n = 16
    ss = [0.012, 0.02, 0.035, 0.055, 0.08, 0.11, 0.14, 0.17, 0.2, 0.23, 0.26, 0.29, 0.315]
    rings, uvs = [], []
    for s in ss:
        hw = interp(s, JAW_HW)
        bot = interp(s, JAW_BOT)
        ring = []
        for j in range(n):
            phi = 2 * math.pi * j / n
            c, sn = math.cos(phi), math.sin(phi)
            z = JAW_TOP_Z - 0.001 + (0.0012 * sup(c, 2.6) if c >= 0 else bot * sup(c, 2.6))
            ring.append(mb.vert((-s, hw * sup(sn, 2.6), z), {'Jaw': 1.0}))
        rings.append(ring)
        # Map the jaw onto the belly of the texture, so its chin reads like the throat.
        uvs.append([(s / L, 0.5 + 0.38 * ((j / n) - 0.5)) for j in range(n + 1)])
    cap0 = mb.vert((-0.006, 0, JAW_TOP_Z - 0.006), {'Jaw': 1.0})
    cap1 = mb.vert((-0.325, 0, JAW_TOP_Z - 0.02), {'Jaw': 1.0})

    def mats(i, j):
        phi = 2 * math.pi * (j + 0.5) / n
        return MOUTH if math.cos(phi) > 0.25 else SKIN
    mb.loft(rings, uvs, mats, cap0, cap1, cap_uv=((0.0, 0.5), (0.13, 0.5)))


def cone(mb, base, tip, r, sides, weights, mat, uv, up=Vector((0, 0, 1))):
    """An open cone (a tooth, a toe, a gill filament)."""
    d = (tip - base).normalized()
    a = d.cross(up)
    if a.length < 1e-4:
        a = d.cross(Vector((1, 0, 0)))
    a.normalize()
    b = d.cross(a)
    ring = [mb.vert(base + (a * math.cos(2 * math.pi * k / sides) + b * math.sin(2 * math.pi * k / sides)) * r,
                    weights) for k in range(sides)]
    t = mb.vert(tip, weights)
    for k in range(sides):
        mb.face([ring[k], ring[(k + 1) % sides], t], [uv, uv, uv], mat)


def tube(mb, pts, radii, weights, sides, mat, uvs, tip=None, tip_weights=None):
    """A tapered tube through pts; weights[i] per ring. Open at the base (it sits inside the body)."""
    rings = []
    for i, (p, r) in enumerate(zip(pts, radii)):
        d = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = d.cross(Vector((0, 0, 1)))
        if a.length < 1e-3:
            a = d.cross(Vector((1, 0, 0)))
        a.normalize()
        b = d.cross(a)
        rings.append([mb.vert(p + (a * math.cos(2 * math.pi * k / sides) + b * math.sin(2 * math.pi * k / sides)) * r,
                              weights[i]) for k in range(sides)])
    for i in range(len(rings) - 1):
        for k in range(sides):
            k1 = (k + 1) % sides
            mb.face([rings[i][k], rings[i][k1], rings[i + 1][k1], rings[i + 1][k]],
                    [uvs[i], uvs[i], uvs[i + 1], uvs[i + 1]], mat)
    if tip is not None:
        t = mb.vert(tip, tip_weights or weights[-1])
        for k in range(sides):
            mb.face([rings[-1][k], rings[-1][(k + 1) % sides], t], [uvs[-1]] * 3, mat)
    return rings


def build_teeth(mb):
    s = 0.016
    while s < 0.18:
        for sg in (1, -1):
            hw = interp(s, HW)
            base = Vector((-s, sg * hw * 0.85, Z0 - 0.002))
            cone(mb, base, base + Vector((0.001, -sg * 0.001, -0.009)), 0.0022, 3, {'Head': 1.0}, SKIN,
                 (s / L, 0.5), up=Vector((1, 0, 0)))
            jw = interp(s, JAW_HW)
            base = Vector((-s - 0.007, sg * (jw - 0.008), JAW_TOP_Z + 0.0005))
            cone(mb, base, base + Vector((0.001, 0, 0.008)), 0.002, 3, {'Jaw': 1.0}, SKIN,
                 (s / L, 0.5), up=Vector((1, 0, 0)))
        s += 0.016


def build_gills(mb):
    rnd = random.Random(7)
    for i, (s, dz, rest, _f, _F, ln) in enumerate(GILLS):
        for side, sg in SIDES:
            name = gill_name(i, side)
            base = gill_base(i, sg) - mirror(Vector((0, 0.012, 0)), sg)
            d = mirror(Vector(rest).normalized(), sg)
            tipp = gill_base(i, sg) + d * ln
            pts = [base + (tipp - base) * t for t in (0.0, 0.3, 0.62, 0.9)]
            sw = skin_weights(s)
            root_w = {k: 0.5 * v for k, v in sw.items()}
            root_w[name] = root_w.get(name, 0) + 0.5
            tube(mb, pts, [0.011, 0.0085, 0.006, 0.0035], [root_w, {name: 1}, {name: 1}, {name: 1}], 4, GILL,
                 [(0, 0)] * 4, tip=tipp + d * 0.012, tip_weights={name: 1})
            # Feathery filaments, three to a station, swept toward the tip.
            a = d.cross(Vector((0, 0, 1))).normalized()
            b = d.cross(a).normalized()
            for k, t in enumerate((0.22, 0.36, 0.5, 0.63, 0.76, 0.88)):
                p = base + (tipp - base) * t
                flen = 0.034 * (1.0 - 0.55 * t)
                for m in range(3):
                    ang = 2 * math.pi * m / 3 + k * 1.05 + rnd.uniform(-0.25, 0.25)
                    radial = a * math.cos(ang) + b * math.sin(ang)
                    fd = (radial + d * 0.75).normalized()
                    cone(mb, p, p + fd * flen, 0.0045, 3, {name: 1}, GILL, (0, 0), up=d)


def build_legs(mb):
    for (pre, s, parent, *_r) in LEGS:
        toes = _r[-1]
        for side, sg in SIDES:
            hip, knee, ankle = leg_points(pre, sg)
            up_n, lo_n = f'{pre}Upper.{side}', f'{pre}Lower.{side}'
            inside = hip - mirror(Vector((0, 0.02, -0.01)), sg)
            mid = (hip + knee) / 2
            v = 0.32 if sg > 0 else 0.68
            sw = skin_weights(s)
            tube(mb, [inside, mid, knee, ankle], [0.017, 0.013, 0.011, 0.008],
                 [sw, {up_n: 1}, {up_n: 0.5, lo_n: 0.5}, {lo_n: 1}], 6, SKIN,
                 [(s / L, v), (s / L, v + 0.02), (s / L, v + 0.04), (s / L, v + 0.06)])
            for a in toes:
                r = math.radians(a)
                td = Vector((math.cos(r), sg * math.sin(r), -0.35)).normalized()
                cone(mb, ankle - Vector((0, 0, 0.002)), ankle + td * 0.03, 0.0055, 4, {lo_n: 1}, SKIN,
                     (s / L, v + 0.06))


# --------------------------------------------------------------------------
# Materials and the mottled skin texture
# --------------------------------------------------------------------------

def make_skin_texture(path):
    """Pinkish-white, mottled, warmer and pinker where blood shows (throat, belly), faint eye pits.
    x runs snout to tail (u = s / L), y runs around the body from the top (v = 0 at the top, 0.5 the belly)."""
    import numpy as np
    from PIL import Image, ImageFilter
    w, h = 1024, 256
    rng = np.random.default_rng(42)

    def noise(cells_x, cells_y, blur):
        g = rng.random((cells_y, cells_x)).astype(np.float32)
        im = Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)
        a = np.asarray(im, dtype=np.float32) / 255.0
        a3 = np.vstack([a, a, a])                     # wrap around the body before blurring
        b = Image.fromarray((a3 * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(blur))
        return np.asarray(b, dtype=np.float32)[h:2 * h] / 255.0

    u = np.linspace(0, 1, w)[None, :]
    v = np.linspace(0, 1, h)[:, None]                 # image row 0 is v = 1 in Blender; symmetric, so no flip
    s = u * L
    belly = 0.5 - 0.5 * np.cos(2 * np.pi * v)         # 0 on the back, 1 on the belly
    back = np.array([0.88, 0.80, 0.77])               # sRGB, 0..1
    flank = np.array([0.93, 0.86, 0.83])
    under = np.array([0.95, 0.82, 0.80])
    col = (back[None, None, :] * (1 - belly[..., None]) + flank[None, None, :] * belly[..., None])
    col = col * (1 - belly[..., None] ** 3) + under[None, None, :] * belly[..., None] ** 3
    col = np.broadcast_to(col, (h, w, 3)).copy()
    # Blood showing: the throat behind the jaw, the gill roots, a faint line along the belly, the snout.
    throat = np.exp(-((s - 0.34) / 0.12) ** 2) * belly ** 2
    gillroot = np.exp(-((s - 0.30) / 0.05) ** 2) * np.exp(-((belly - 0.45) / 0.22) ** 2)
    midline = np.exp(-((v - 0.5) / 0.03) ** 2) * np.clip((s - 0.4) / 0.4, 0, 1) * np.clip((1.9 - s) / 0.4, 0, 1)
    snout = np.exp(-(s / 0.05) ** 2) * 0.6
    pink = np.clip(0.55 * throat + 0.45 * gillroot + 0.22 * midline + snout, 0, 1)
    blood = np.array([0.86, 0.55, 0.55])
    col = col * (1 - pink[..., None]) + blood[None, None, :] * pink[..., None]
    # Mottling: soft greyish-lilac blotches, more on the back, and a finer grain.
    m1 = noise(64, 10, 6)
    m2 = noise(180, 28, 2.2)
    blot = np.clip((m1 - 0.52) * 4.0, 0, 1) * (0.75 - 0.5 * belly)
    grain = (m2 - 0.5) * 0.06
    dark = np.array([0.72, 0.64, 0.66])
    col = col * (1 - 0.45 * blot[..., None]) + dark[None, None, :] * 0.45 * blot[..., None]
    col += grain[..., None]
    # Faint veins: a few thin, wandering pink lines on the flanks.
    vr = np.random.default_rng(3)
    for _ in range(26):
        x0 = vr.uniform(0.04, 0.75)
        y0 = vr.uniform(0.1, 0.9)
        pts = [(x0, y0)]
        for _k in range(30):
            x0 += vr.uniform(0.002, 0.006)
            y0 += vr.uniform(-0.012, 0.012)
            pts.append((x0, y0))
        for (xa, ya) in pts:
            xi, yi = int(xa * w) % w, int(ya * h) % h
            col[max(0, yi - 1):yi + 1, max(0, xi - 1):xi + 1] = col[max(0, yi - 1):yi + 1, max(0, xi - 1):xi + 1] * 0.94 + \
                np.array([0.82, 0.55, 0.56]) * 0.06
    # Eye pits: dim, bruised spots under the skin, where an eye would be.
    for ve in (50 / 360, 1 - 50 / 360):
        d2 = ((s - 0.085) / 0.012) ** 2 + ((v - ve) / 0.03) ** 2
        k = np.exp(-d2)[..., None] * 0.45
        col = col * (1 - k) + np.array([0.6, 0.5, 0.55])[None, None, :] * k
    # The fin edges on the tail are thinner and pinker.
    fin = np.clip((s - 1.6) / 0.6, 0, 1) * (np.exp(-(v / 0.04) ** 2) + np.exp(-((1 - v) / 0.04) ** 2)
                                            + np.exp(-((v - 0.5) / 0.04) ** 2))
    col = col * (1 - 0.35 * fin[..., None]) + np.array([0.95, 0.72, 0.70])[None, None, :] * 0.35 * fin[..., None]
    img = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8), 'RGB')
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def _material(name):
    mat = bpy.data.materials.new(name)
    try:
        mat.use_nodes = True
    except AttributeError:
        pass
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
    return mat, nt, bsdf


def build_materials():
    tex = os.path.join(TEX, 'white_skin.png')
    make_skin_texture(tex)
    skin, nt, bsdf = _material('WhiteSkin')
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = bpy.data.images.load(tex, check_existing=True)
    nt.links.new(t.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = 0.42
    bsdf.inputs['Subsurface Weight'].default_value = 0.35
    bsdf.inputs['Subsurface Radius'].default_value = (1.0, 0.35, 0.25)
    bsdf.inputs['Subsurface Scale'].default_value = 0.02
    gill, _nt, bsdf = _material('WhiteGill')
    bsdf.inputs['Base Color'].default_value = (0.60, 0.10, 0.12, 1)
    bsdf.inputs['Roughness'].default_value = 0.5
    bsdf.inputs['Subsurface Weight'].default_value = 0.4
    bsdf.inputs['Subsurface Radius'].default_value = (1.0, 0.2, 0.2)
    bsdf.inputs['Subsurface Scale'].default_value = 0.01
    mouth, _nt, bsdf = _material('WhiteMouth')
    bsdf.inputs['Base Color'].default_value = (0.20, 0.03, 0.035, 1)
    bsdf.inputs['Roughness'].default_value = 0.3
    return [skin, gill, mouth]


def build_mesh(arm, coll):
    names = [b.name for b in arm.data.bones if b.use_deform]
    mb = MeshBuilder(names)
    build_body(mb)
    build_jaw(mb)
    build_teeth(mb)
    build_gills(mb)
    build_legs(mb)
    bm = mb.bm
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new('White')
    bm.to_mesh(me)
    bm.free()
    for m in build_materials():
        me.materials.append(m)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    ob = bpy.data.objects.new('White', me)
    coll.objects.link(ob)
    for n in names:
        ob.vertex_groups.new(name=n)
    ob.parent = arm
    mod = ob.modifiers.new('Armature', 'ARMATURE')
    mod.object = arm
    return ob


# --------------------------------------------------------------------------
# Poses
# --------------------------------------------------------------------------

class Pose:
    """yaw/pitch/roll: heading of the head-ward tangent along s (radians); anchor: where s = 1.2 sits.
    jaw: degrees open. gills: flare per gill (L1..L3, R1..R3; -1 folded back, 0 rest, 1 flared wide).
    legs: (tuck, reach, swing degrees) per leg ('FrontLeg.L', ...)."""

    def __init__(self):
        n = NS + 1
        self.yaw = [0.0] * n
        self.pitch = [0.0] * n
        self.roll = [0.0] * n
        self.anchor = Vector((-ANCHOR_K * DS, 0.0, Z0))
        self.jaw = 0.0
        self.gills = [0.0] * 6
        self.legs = {f'{pre}.{side}': (1.0, 0.0, 0.0) for pre in ('FrontLeg', 'HindLeg') for side in 'LR'}

    def copy(self):
        p = Pose()
        p.yaw, p.pitch, p.roll = self.yaw[:], self.pitch[:], self.roll[:]
        p.anchor = self.anchor.copy()
        p.jaw = self.jaw
        p.gills = self.gills[:]
        p.legs = dict(self.legs)
        return p

    # Authoring helpers --------------------------------------------------
    def bend(self, attr, s0, ang, w):
        """A joint at s0: everything head-ward of it turns by ang (radians), blended over width w."""
        arr = getattr(self, attr)
        for k in range(NS + 1):
            arr[k] += ang * smooth((s0 - k * DS) / w + 0.5)

    def wave(self, attr, amp, lam, phase):
        """A displacement wave d(s) = amp(s) sin(2 pi s / lam - phase), as heading angles."""
        arr = getattr(self, attr)
        tau = 2 * math.pi
        d = [amp(k * DS) * math.sin(tau * k * DS / lam - phase) for k in range(NS + 1)]
        for k in range(NS + 1):
            a, b = max(0, k - 1), min(NS, k + 1)
            arr[k] += math.atan(-(d[b] - d[a]) / ((b - a) * DS))

    def add(self, attr, fn):
        arr = getattr(self, attr)
        for k in range(NS + 1):
            arr[k] += fn(k * DS)

    def set_gills(self, fn):
        """fn(i, side_sign) -> flare."""
        self.gills = [fn(i, sg) for sg in (1, -1) for i in range(3)]

    # Geometry -----------------------------------------------------------
    def points(self):
        P = [None] * (NS + 1)
        P[ANCHOR_K] = self.anchor.copy()
        for k in range(ANCHOR_K + 1, NS + 1):
            P[k] = P[k - 1] - self.tangent(k - 0.5) * DS
        for k in range(ANCHOR_K - 1, -1, -1):
            P[k] = P[k + 1] + self.tangent(k + 0.5) * DS
        return P

    def tangent(self, kf):
        k0 = int(math.floor(kf))
        k1 = min(NS, k0 + 1)
        t = kf - k0
        yaw = self.yaw[k0] * (1 - t) + self.yaw[k1] * t
        pitch = self.pitch[k0] * (1 - t) + self.pitch[k1] * t
        return Vector((math.cos(pitch) * math.cos(yaw), math.cos(pitch) * math.sin(yaw), math.sin(pitch)))

    def place(self, k, target):
        """Move the whole body so the centreline point at index k lands on target."""
        self.anchor += target - self.points()[k]

    def centre_lateral(self):
        P = self.points()
        self.anchor.y -= sum(p.y for p in P) / len(P)

    def snout(self):
        return self.points()[0]


def blend(a, b, w):
    p = Pose()
    p.yaw = [x + (y - x) * w for x, y in zip(a.yaw, b.yaw)]
    p.pitch = [x + (y - x) * w for x, y in zip(a.pitch, b.pitch)]
    p.roll = [x + (y - x) * w for x, y in zip(a.roll, b.roll)]
    p.anchor = a.anchor.lerp(b.anchor, w)
    p.jaw = a.jaw + (b.jaw - a.jaw) * w
    p.gills = [x + (y - x) * w for x, y in zip(a.gills, b.gills)]
    p.legs = {k: tuple(x + (y - x) * w for x, y in zip(a.legs[k], b.legs[k])) for k in a.legs}
    return p


def frame_matrix(pos, t, roll):
    """Orthonormal frame with X along the head-ward tangent t, Z up (rolled by roll about X)."""
    x = t.normalized()
    up = Vector((0, 0, 1))
    z = (up - x * x.dot(up)).normalized()
    if roll:
        z = Quaternion(x, roll) @ z
    y = z.cross(x)
    m = Matrix((x, y, z)).transposed().to_4x4()
    m.translation = pos
    return m


class Poser:
    """Turns a Pose into bone transforms and keys them."""

    def __init__(self, arm):
        self.arm = arm
        self.rest = {b.name: b.matrix_local.copy() for b in arm.data.bones}
        self.parent = {b.name: (b.parent.name if b.parent else None) for b in arm.data.bones}
        self.prevq = {}

    def local_from_world(self, name, M, Mw):
        R = self.rest[name]
        p = self.parent[name]
        if p is None:
            return R.inverted() @ M
        Rp = self.rest[p]
        return (Rp.inverted() @ R).inverted() @ (Mw[p].inverted() @ M)

    def local_rot(self, name, q_rest):
        """A rotation given in rest (armature) coordinates, about the bone's head, as the bone's local basis."""
        r3 = self.rest[name].to_3x3()
        return (r3.inverted() @ q_rest.to_matrix() @ r3).to_quaternion()

    def solve(self, pose):
        P = pose.points()
        Mw = {'Root': self.rest['Root']}
        basis = {'Root': Matrix.Identity(4)}
        names = spine_names()
        for i, n in enumerate(names):
            k0, k1 = int(round(SPINE_S[i] / DS)), int(round(SPINE_S[i + 1] / DS))
            t = P[k0] - P[k1]
            W = frame_matrix(P[k0], t, pose.roll[(k0 + k1) // 2])
            W0 = Matrix.Translation(self.rest[n].translation)
            Mw[n] = W @ W0.inverted() @ self.rest[n]
        kh = int(round(HEAD_S / DS))
        W = frame_matrix(P[kh], P[0] - P[kh], pose.roll[kh // 2])
        Mw['Head'] = W @ Matrix.Translation(self.rest['Head'].translation).inverted() @ self.rest['Head']
        for n in names + ['Head']:
            basis[n] = self.local_from_world(n, Mw[n], Mw)
        # Jaw: open about the lateral axis (chin down).
        basis['Jaw'] = self.local_rot('Jaw', Quaternion(Vector((0, 1, 0)), math.radians(pose.jaw))).to_matrix().to_4x4()
        basis['JawTip'] = Matrix.Identity(4)
        for i, (s, dz, rest, fold, flare, ln) in enumerate(GILLS):
            for j, (side, sg) in enumerate(SIDES):
                g = pose.gills[j * 3 + i]
                r = mirror(Vector(rest).normalized(), sg)
                tgt = r.lerp(mirror(Vector(fold).normalized(), sg), -g) if g < 0 else \
                    r.lerp(mirror(Vector(flare).normalized(), sg), g)
                q = r.rotation_difference(tgt.normalized())
                basis[gill_name(i, side)] = self.local_rot(gill_name(i, side), q).to_matrix().to_4x4()
        for (pre, s, parent, up, lo, upt, lot, upr, lor, lens, toes) in LEGS:
            for side, sg in SIDES:
                tuck, reach, swing = pose.legs[f'{pre}.{side}']
                sw = math.sin(math.radians(swing))

                def aim(rest_v, tuck_v, reach_v):
                    r = Vector(rest_v).normalized()
                    v = r + (Vector(tuck_v).normalized() - r) * tuck + (Vector(reach_v).normalized() - r) * reach
                    v.x += sw
                    return mirror(r, sg), mirror(v.normalized(), sg)
                ru, tu = aim(up, upt, upr)
                rl, tl = aim(lo, lot, lor)
                qu = ru.rotation_difference(tu)
                ql_total = (qu @ rl).rotation_difference(tl) @ qu
                ql = qu.inverted() @ ql_total
                basis[f'{pre}Upper.{side}'] = self.local_rot(f'{pre}Upper.{side}', qu).to_matrix().to_4x4()
                basis[f'{pre}Lower.{side}'] = self.local_rot(f'{pre}Lower.{side}', ql).to_matrix().to_4x4()
        return basis

    def key(self, pose, frame):
        basis = self.solve(pose)
        for pb in self.arm.pose.bones:
            m = basis[pb.name]
            loc, q, _sc = m.decompose()
            prev = self.prevq.get(pb.name)
            if prev is not None and prev.dot(q) < 0:
                q = -q
            self.prevq[pb.name] = q
            pb.location = loc
            pb.rotation_quaternion = q
            pb.keyframe_insert('location', frame=frame)
            pb.keyframe_insert('rotation_quaternion', frame=frame)

    def clip(self, name, frames, pose_at, loop=False):
        """Key pose_at(f) for f = 0..frames-1 (and the closing frame of a loop) at Blender frames 1.., then stash
        the action on an NLA track named after the clip."""
        arm = self.arm
        arm.animation_data_create()
        act = bpy.data.actions.new(name)
        arm.animation_data.action = act
        self.prevq = {}
        for f in range(frames + (1 if loop else 0)):
            self.key(pose_at(f), f + 1)
        ad = arm.animation_data
        tr = ad.nla_tracks.new()
        tr.name = name
        tr.strips.new(name, 1, act)
        ad.action = None


# --------------------------------------------------------------------------
# Clips
# --------------------------------------------------------------------------

TAU = 2 * math.pi
R = math.radians


def swim_amp(s):
    return 0.016 + 0.085 * (s / L) ** 1.6


def swim_pose(t, amp=1.0, gill0=-0.35, legs_tuck=1.0, lam=1.45):
    """The calm undulation at phase t (0..1); amp scales it."""
    p = Pose()
    p.wave('yaw', lambda s: amp * swim_amp(s), lam, TAU * t)
    p.wave('pitch', lambda s: amp * 0.006 * (s / L), 2.4, TAU * t + 1.0)
    p.add('roll', lambda s: amp * 0.05 * math.sin(TAU * (s / lam - t)))
    p.anchor.z = Z0 + amp * 0.008 * math.sin(TAU * t)
    p.centre_lateral()
    p.set_gills(lambda i, sg: gill0 + 0.15 * math.sin(TAU * t - 0.6 * i))
    for k in p.legs:
        p.legs[k] = (legs_tuck, 0.0, 4 * amp * math.sin(TAU * t + (0 if k.endswith('L') else math.pi)))
    p.jaw = 1.0 + 1.0 * math.sin(TAU * t)
    return p


def clip_swim(t):
    return swim_pose(t)


def clip_glide(f):
    t = f / 72
    p = Pose()
    p.wave('yaw', lambda s: 0.35 * swim_amp(s), 1.8, TAU * t)
    p.add('pitch', lambda s: R(1.5) * math.sin(TAU * t) * (0.5 - s / L))
    p.add('roll', lambda s: 0.03 * math.sin(TAU * (s / 1.8 - t)))
    p.anchor.z = Z0 + 0.006 * math.sin(TAU * t + 0.8)
    p.centre_lateral()
    p.set_gills(lambda i, sg: 0.12 + 0.13 * math.sin(TAU * t + 0.9 * i + (0.4 if sg < 0 else 0)))
    for k in p.legs:
        ph = 0 if k.endswith('L') else math.pi
        p.legs[k] = (0.6, 0.0, 6 * math.sin(TAU * t + ph))
    p.jaw = 1.5 + 1.0 * math.sin(TAU * t)
    return p


def clip_listen(f):
    """Stops, lifts its head toward a sound, gills wide, and sweeps its head slowly side to side."""
    amp = keys(f, [(0, 1.0), (16, 0.15), (60, 0.1)])
    p = swim_pose(f / 48, amp=amp)
    p.bend('pitch', 0.55, R(keys(f, [(6, 0), (26, 14), (60, 14)])), 0.4)
    p.bend('pitch', 0.3, R(keys(f, [(10, 0), (28, 9), (60, 9)])), 0.12)
    p.bend('pitch', 1.6, R(keys(f, [(6, 0), (26, -2.5)])), 0.8)
    sweep = keys(f, [(24, 0), (35, 18), (47, -16), (57, 4), (60, 4)])
    p.bend('yaw', 0.5, R(sweep * 0.6), 0.35)
    p.bend('yaw', 0.3, R(sweep * 0.5), 0.12)
    p.add('roll', lambda s: R(-sweep * 0.15) * max(0, 1 - s / 0.8))
    flare = keys(f, [(4, -0.35), (22, 1.0), (60, 0.95)])
    p.set_gills(lambda i, sg: flare + 0.06 * math.sin(f * 0.9 + i * 1.3) * min(1, f / 20))
    tuck = keys(f, [(4, 1.0), (24, 0.25)])
    p.legs['FrontLeg.L'] = p.legs['FrontLeg.R'] = (tuck, 0.3 * (1 - tuck), 0.0)
    p.legs['HindLeg.L'] = p.legs['HindLeg.R'] = (keys(f, [(4, 1.0), (24, 0.55)]), 0.0, 0.0)
    p.jaw = keys(f, [(20, 1), (30, 4), (50, 4), (58, 2)])
    return p


def surfaced(f=48):
    """WhiteSurface's pose at frame f."""
    amp = keys(f, [(0, 1.0), (12, 0.25)])
    p = swim_pose(f / 48, amp=amp)
    p.bend('pitch', 0.95, R(keys(f, [(0, 0), (6, -6), (30, 39), (36, 34), (48, 35)])), 0.45)
    p.bend('pitch', 0.32, R(keys(f, [(0, 0), (30, -22), (40, -18), (48, -20)])), 0.16)
    p.bend('pitch', 1.9, R(keys(f, [(0, 0), (30, -4)])), 0.5)
    p.anchor += Vector((keys(f, [(0, 0), (30, 0.16)]), 0, keys(f, [(0, 0), (6, -0.03), (30, -0.02)])))
    shake = math.exp(-max(0, f - 32) / 5) * math.sin(max(0, f - 32) * 1.7) if f > 32 else 0
    p.bend('yaw', 0.3, R(5 * shake), 0.12)
    g = keys(f, [(0, -0.35), (14, -0.65), (30, 0.4), (36, 1.1), (42, 0.9), (48, 0.95)])
    p.set_gills(lambda i, sg: g + 0.12 * shake * (1 if i % 2 else -1))
    front = keys(f, [(8, 1.0), (30, 0.3)])
    p.legs['FrontLeg.L'] = p.legs['FrontLeg.R'] = (front, 0.5 * (1 - front) / 0.7, 0.0)
    p.legs['HindLeg.L'] = p.legs['HindLeg.R'] = (keys(f, [(8, 1.0), (30, 0.8)]), 0.0, 0.0)
    p.jaw = keys(f, [(30, 1), (36, 7), (42, 2), (48, 2)])
    return p


def clip_surface(f):
    return surfaced(f)


def clip_sink(f):
    a = surfaced(48)
    b = swim_pose((f - 36) / 48)
    w = keys(f, [(3, 0), (30, 1)])
    p = blend(a, b, w)
    dip = math.sin(math.pi * min(1, max(0, (f - 2) / 22)))
    p.bend('pitch', 0.32, R(-14 * dip), 0.14)
    p.anchor.z -= 0.05 * dip
    g = keys(f, [(0, 0.95), (12, -0.7), (26, -0.6), (36, b.gills[0])])
    p.gills = [g + (bg - b.gills[0]) * w for bg in b.gills]
    p.jaw = keys(f, [(0, 2), (8, 0), (30, b.jaw)])
    return p


def clip_roll(f):
    """The glimpse: rises from below, rolls lazily once (head first, belly up at the surface), dives and is gone.
    Drifts 0.25 m along +x."""
    p = swim_pose(f / 48, amp=0.4)
    p.bend('pitch', 1.6, R(keys(f, [(0, 12), (14, 4), (24, 0), (36, -14), (48, -22)])), 1.0)
    p.bend('yaw', 1.25, R(keys(f, [(0, 0), (24, 22), (48, 34)])), 1.2)
    for k in range(NS + 1):
        s = k * DS
        p.roll[k] += TAU * smooth((f - 6 - 16 * s / L) / 26)
    p.anchor = Vector((-1.2 + keys(f, [(0, 0), (48, 0.25)], lin),
                       p.anchor.y, keys(f, [(0, -0.38), (14, -0.12), (26, -0.10), (40, -0.45), (48, -0.62)])))
    p.set_gills(lambda i, sg: -0.7 + 0.1 * math.sin(f * 0.3 + i))
    for k in p.legs:
        flop = math.sin(f * 0.25 + (0 if k.endswith('L') else 1.5))
        p.legs[k] = (0.5 + 0.15 * flop, 0.0, 10 * flop)
    p.jaw = 2.0
    return p


def strike_shape(rise=40.0, rise_s=1.25, level_s=0.45, neck=10.0, tail=-10.0, amp=0.3, t=0.0):
    """A body reared out of the water: rising from rise_s, level again from level_s, the tail driving down."""
    p = swim_pose(t, amp=amp)
    p.bend('pitch', rise_s, R(rise), 0.35)
    p.bend('pitch', level_s, R(-rise), 0.3)
    p.bend('pitch', 0.3, R(neck), 0.12)
    p.bend('pitch', 1.7, R(tail), 0.4)
    return p


def clip_slap(f):
    """From surfaced: rears, slams head and front body onto the ledge edge ahead (contact at frame 9), recoils
    and sinks back under."""
    start = surfaced(48)
    rear = surfaced(48)
    rear.bend('pitch', 0.95, R(14), 0.45)
    rear.bend('pitch', 0.32, R(18), 0.16)
    rear.anchor.x -= 0.06
    hit = strike_shape(rise=32, rise_s=1.15, level_s=0.55, neck=-6, tail=-8, amp=0.2)
    hit.place(0, SLAP_SNOUT)
    recoil = strike_shape(rise=26, rise_s=1.15, level_s=0.5, neck=18, tail=-6, amp=0.3)
    recoil.place(0, SLAP_SNOUT + Vector((-0.45, 0, 0.12)))
    end = swim_pose(0.0)
    if f <= 4:
        p = blend(start, rear, smooth(f / 4))
    elif f <= 9:
        p = blend(rear, hit, ease_in((f - 4) / 5) * 0.6 + 0.4 * smooth((f - 4) / 5))
    elif f <= 13:
        p = hit.copy()
        sq = math.sin(math.pi * (f - 9) / 4)
        p.anchor += Vector((0.0, 0, -0.012 * sq))
        p.bend('pitch', 0.3, R(-4 * sq), 0.12)
    elif f <= 19:
        p = blend(hit, recoil, smooth((f - 13) / 6))
    else:
        p = blend(recoil, end, smooth((f - 19) / 11))
    g = keys(f, [(0, 0.95), (4, 1.25), (9, 1.25), (11, 0.6), (16, 1.0), (30, end.gills[0])])
    shudder = math.exp(-max(0, f - 9) / 3) * math.sin(max(0, f - 9) * 2.4) if f >= 9 else 0
    p.set_gills(lambda i, sg: g + 0.25 * shudder * (1 if i % 2 else -1))
    p.jaw = keys(f, [(0, 2), (4, 12), (8, 6), (9, 0), (16, 3), (30, end.jaw)])
    reach = keys(f, [(0, 0.5), (6, 1.0), (16, 1.0), (28, 0.0)])
    p.legs['FrontLeg.L'] = p.legs['FrontLeg.R'] = (keys(f, [(0, 0.3), (6, 0.0), (20, 0.0), (30, 1.0)]),
                                                   reach * 0.8, 0.0)
    return p


def lunge_poses():
    start = surfaced(48)
    coil = surfaced(48)
    coil.wave('yaw', lambda s: 0.6 * swim_amp(s), 1.4, 0.6)
    coil.bend('pitch', 0.95, R(8), 0.45)
    coil.bend('pitch', 0.32, R(-10), 0.14)
    coil.anchor.x -= 0.12
    reach = strike_shape(rise=42, rise_s=1.25, level_s=0.45, neck=14, tail=-10, amp=0.25)
    reach.place(0, LUNGE_SNOUT + Vector((-0.06, 0, 0.08)))
    bite = strike_shape(rise=40, rise_s=1.25, level_s=0.45, neck=-4, tail=-10, amp=0.25)
    bite.place(0, LUNGE_SNOUT)
    return start, coil, reach, bite


def clip_lunge(f):
    """Fast strike from surfaced onto the ledge ahead: the jaws open wide on the way and snap shut at frame 14,
    then hold. The snout reaches LUNGE_SNOUT."""
    start, coil, reach, bite = lunge_poses()
    if f <= 5:
        p = blend(start, coil, smooth(f / 5))
    elif f <= 12:
        p = blend(coil, reach, ease_out((f - 5) / 7))
    elif f <= 14:
        p = blend(reach, bite, smooth((f - 12) / 2))
    else:
        p = bite.copy()
        k = max(0, f - 14)
        shake = math.exp(-k / 3.5) * math.sin(k * 1.9)
        p.bend('yaw', 0.3, R(6 * shake), 0.14)
        p.bend('pitch', 0.3, R(-2 * shake), 0.14)
        p.anchor.x -= 0.02 * smooth(k / 10)
    p.jaw = keys(f, [(0, 2), (4, 0), (11, 55), (12, 58), (14, -1), (24, -1)])
    g = keys(f, [(0, 0.95), (5, -0.6), (10, 1.2), (14, 1.1), (24, 1.0)])
    p.set_gills(lambda i, sg: g)
    fr = keys(f, [(0, 0.3), (6, 0.8), (11, 0.0)])
    p.legs['FrontLeg.L'] = p.legs['FrontLeg.R'] = (fr, keys(f, [(6, 0), (12, 1.0)]), 0.0)
    p.legs['HindLeg.L'] = p.legs['HindLeg.R'] = (keys(f, [(0, 0.8), (8, 1.0)]), 0.0, 0.0)
    return p


def clip_drag(f):
    """From the end of the lunge: pulls back and down under the water, twisting (a full roll). The jaws stay shut
    on whatever JawTip holds."""
    _s, _c, _r, bite = lunge_poses()
    p = bite.copy()
    pull = keys(f, [(0, 0), (4, -0.04), (22, 1.0), (36, 1.35)])
    # The reared front comes down as it pulls back: the rise flattens and the head goes in nose first.
    p.bend('pitch', 1.25, R(-40 * min(1, max(0, pull))), 0.35)
    p.bend('pitch', 0.45, R(40 * min(1, max(0, pull))), 0.3)
    p.bend('pitch', 0.6, R(keys(f, [(4, 0), (20, -32), (36, -20)])), 0.4)
    p.wave('yaw', lambda s: keys(f, [(8, 0), (20, 1.6), (36, 1.2)]) * swim_amp(s), 1.3, TAU * f / 18)
    for k in range(NS + 1):
        s = k * DS
        p.roll[k] += TAU * smooth((f - 6 - 10 * s / L) / 22)
    p.anchor = bite.anchor + Vector((keys(f, [(0, 0), (4, 0.02), (22, -1.05), (36, -1.4)]), 0,
                                     keys(f, [(0, 0), (4, 0.01), (22, -0.5), (36, -0.85)])))
    p.jaw = -1.5
    p.set_gills(lambda i, sg: keys(f, [(0, 1.0), (14, -0.8), (36, -0.9)]))
    for k in p.legs:
        p.legs[k] = (keys(f, [(0, 0.2), (16, 1.0)]), 0.0, 8 * math.sin(f * 0.5))
    return p


def nose_base():
    p = Pose()
    p.bend('pitch', 0.5, R(12), 0.35)
    p.bend('pitch', 0.3, R(-6), 0.12)
    p.place(0, Vector((NOSE_X - 0.04, 0, -0.06)))
    return p


def clip_nose(f):
    """Nosing at a step 0.5 m ahead (the doorbell): pushes, pulls back, tilts, pushes again; gills pulsing."""
    t = f / 60
    base = nose_base()
    p = Pose()
    p.yaw, p.pitch, p.roll = base.yaw[:], base.pitch[:], base.roll[:]
    p.wave('yaw', lambda s: 0.4 * swim_amp(s) * (s / L), 1.6, TAU * t)
    nudge = max(0.0, math.sin(TAU * 2 * t)) ** 2
    p.bend('pitch', 0.3, R(7 * math.sin(TAU * 2 * t + 1.2)), 0.12)
    p.bend('yaw', 0.42, R(10 * math.sin(TAU * t)), 0.3)
    p.add('roll', lambda s: R(4 * math.sin(TAU * t + 0.5)) * max(0, 1 - s / 0.8))
    p.anchor = base.anchor.copy()
    p.anchor.x += -0.03 + 0.045 * nudge
    p.anchor.z += 0.01 * math.sin(TAU * t)
    p.set_gills(lambda i, sg: 0.5 + 0.35 * math.sin(TAU * 2 * t - 0.7 * i))
    for k in p.legs:
        ph = 0 if k.endswith('L') else math.pi
        if k.startswith('Front'):
            p.legs[k] = (0.25, 0.45, 10 * math.sin(TAU * 2 * t + ph))
        else:
            p.legs[k] = (0.7, 0.0, 5 * math.sin(TAU * t + ph))
    p.jaw = 2 + 3 * max(0.0, math.sin(TAU * 2 * t + 2.0))
    return p


CLIPS = [
    # name, frames, pose function of the clip frame (0-based), loops
    ('WhiteSwim', 48, lambda f: clip_swim(f / 48), True),
    ('WhiteGlide', 72, clip_glide, True),
    ('WhiteListen', 60, clip_listen, False),
    ('WhiteSurface', 48, clip_surface, False),
    ('WhiteSink', 36, clip_sink, False),
    ('WhiteRoll', 48, clip_roll, False),
    ('WhiteSlap', 30, clip_slap, False),
    ('WhiteLunge', 24, clip_lunge, False),
    ('WhiteDrag', 36, clip_drag, False),
    ('WhiteNose', 60, clip_nose, True),
]


# --------------------------------------------------------------------------
# Entry point
# --------------------------------------------------------------------------

def build_white(dl01, coll):
    """Build the White into coll (mesh + armature, every clip as an NLA track). Returns the armature."""
    arm = build_armature(coll)
    build_mesh(arm, coll)
    poser = Poser(arm)
    for name, frames, fn, loop in CLIPS:
        poser.clip(name, frames, fn, loop)
    for t in arm.animation_data.nla_tracks:
        t.mute = False
    for pb in arm.pose.bones:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
    return arm


def _standalone():
    """Build only the White and export white.glb (the full build does this from build_dl01.main())."""
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--blend', default=None)
    args = ap.parse_args()
    sys.path.insert(0, os.path.join(HERE, '..', 'dl01'))
    import build_dl01 as dl01
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = FPS
    coll = bpy.data.collections.new('White')
    scene.collection.children.link(coll)
    build_white(dl01, coll)
    out = os.path.abspath(args.out)
    os.makedirs(out, exist_ok=True)
    dl01.export(os.path.join(out, 'white.glb'), [o for o in coll.all_objects if o.type in ('MESH', 'ARMATURE')])
    if args.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend))


if __name__ == '__main__':
    _standalone()
