"""Pass 6 (docs/chapter1_pass6_plan.md section 2): human remains that have come apart where they lay.

Every set of remains in chapter 1 is built here: DL-02's sorters, DL-05's dead, the bones in DL-10 and DL-11. They are
76 years dead. Nothing holds a skeleton together that long: the skull has rolled from the collar, its jaw lies apart
from it, the ribs have fallen in between the lapels, the long bones lie loose, the clothes have gone flat over what is
left and keep only a little of the shape. Dry, dark-ivory bone, low-key cloth, no faces, nothing that reads as gore.

All geometry is in the remains atlas (art/pass3 RemainsMat, cells: bone, dark, cloth, rag, apron, cap, shoe, bag,
sheet, paper, tag, rope, wood): one material, one draw call per merged object.

API (stable: DL-10/DL-11 build on it; new names may be added, these keep working)
-------------------------------------------------------------------------------
    import remains as R

    P = R.painted()
        A Painted (art/pass3/build_ration_hall.py): a bmesh with a 'UVMap' layer, in the remains atlas. P.bm is the
        bmesh; P.obj(name, 'RemainsMat', coll) writes it out as one object, P.mesh(name, 'RemainsMat') as mesh data.

    R.add(P, pose, M=None, seed=0.0, **opts)
        Add one set of remains in `pose` to P, transformed by the 4x4 Matrix M (None: identity; see R.xform). A mirror
        (negative determinant) is handled. `seed` varies the details (how the skull rolled, which bones strayed, the
        cloth's creases), so a few seeds and mirrors keep a row from reading as copies.

    R.xform(loc=(0, 0, 0), turn=0.0, mirror=False, scale=1.0) -> Matrix
        A 4x4 placing a pose: `turn` in degrees about z, `mirror` flips the figure's left and right (local y).

    me = R.mesh(pose, seed=0.0, name=None, **opts)
        The pose alone as a bpy Mesh in RemainsMat, its origin the pose's origin (cached on its arguments), for linked
        duplicates.

    ob = R.place(me, loc, turn=0.0, coll=None, name=None, mirror=False)
        An object instancing `me` (mirror: scale y -1).

    R.POSES
        The pose names below. R.extent(pose) -> (x0, x1, y0, y1, height): its rough footprint in the local frame.

The local frame: metres, z up, the origin on the floor. A figure faces +x (lying: the head at -x, the feet at +x);
+y is its left.

    'lying'       On the back, the clothes flat: the coat open, the ribs fallen in between its lapels, the sleeves
                  and trouser legs flat over the long bones with the hand bones at the cuffs and the boots fallen
                  outward. The skull turned and rolled a hand's width from the collar, the jaw apart, a few small
                  bones strayed. Origin under the pelvis; head to x -0.85, feet to x +1.0.
                  opts: arms='side'|'chest'|'folded'|'out'|'up' (the arms: by the sides, one across the waist, both
                  across it, flung out, over the head), legs='straight'|'bent' (one knee fallen out), coat=cell, trousers=cell, boots=True.
    'fallen'      'lying' with arms='up', legs='bent' and the skull rolled further: fallen back from a height.
    'curled'      On the side, knees drawn up, the coat slumped over the hips, the skull fallen from the collar.
    'seated'      Sat on the floor, collapsed: the pelvis on the floor, the coat slumped into the lap over the ribs
                  that fell into it, the arm bones across the thighs (or one by the hip), the legs out. The skull
                  dropped into the lap or rolled to the floor (skull='lap'|'floor'|'chest'), the jaw apart.
                  opts: support=True (the back against something at x -0.16: a wall, a door, a counter, the coat's
                  shoulders still leaning on it), knees=0..1 (legs out .. drawn up), lean=-1..1 (slumped over toward
                  its right .. left, onto a neighbour), arms='lap'|'hip', bowl=False (a bowl in the lap,
                  the hand bones round it), coat=cell, trousers=cell, cap=False (a cap fallen beside), boots=True.
    'pair'        A huddled pair: two lying close on their backs, heads together, one's arm across the other (its
                  sleeve over the other's coat, the hand's bones on their chest). Origin between them; they lie along
                  x at y -0.24 and +0.26. opts: a={...}, b={...} per-figure 'lying' opts; others apply to both.
    'scattered'   A skull, its jaw, a few long bones, a pelvis and a scrap of cloth, strewn over about 0.9 x 0.6.
    'skull'       A skull alone, resting on the floor, its jaw beside it.
    'shrouded'    Under a sheet laid over them by the living, long since settled flat: the sheet's dome over the
                  skull, low ridges over the ribs and the long bones, the foot bones out from under the hem with a
                  ration tag on a toe. Lying along x, feet to +x, origin at the centre of its footprint; 1.65 long.
                  opts: hand=None|1|-1 (a forearm and hand from under the left/right edge), child=False, tag=True.

    Common opts: detail=1.0 (0.6 for figures seen only far off: fewer segments), cloth cells as above.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for _d in ('pass3', 'pass4', 'd17'):
    _p = os.path.join(HERE, '..', _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402

from build_d17 import add_cyl, add_sphere, add_torus, rounded_box  # noqa: E402
import build_ration_hall as rh  # noqa: E402

V = Vector
Z = Vector((0, 0, 1))
POSES = ('lying', 'fallen', 'curled', 'seated', 'pair', 'scattered', 'skull', 'shrouded')
MAT = 'RemainsMat'


def painted():
    return rh.Painted()


def xform(loc=(0, 0, 0), turn=0.0, mirror=False, scale=1.0):
    M = Matrix.Translation(Vector(loc)) @ Matrix.Rotation(math.radians(turn), 4, 'Z')
    if scale != 1.0:
        M = M @ Matrix.Diagonal((scale, scale, scale, 1.0))
    if mirror:
        M = M @ Matrix.Diagonal((1.0, -1.0, 1.0, 1.0))
    return M


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def _merge_into(P, Q, M=None):
    """Move Q's geometry (a Painted) into P through M (a mirror flips the winding back out)."""
    if M is not None:
        bmesh.ops.transform(Q.bm, matrix=M, verts=Q.bm.verts[:])
        if M.to_3x3().determinant() < 0:
            bmesh.ops.reverse_faces(Q.bm, faces=Q.bm.faces[:])
    P._merge(Q.bm)


def _rest_on(Q, z=0.0):
    """Lift or drop everything in Q so its lowest point sits at z."""
    if not Q.bm.verts:
        return
    lo = min(v.co.z for v in Q.bm.verts)
    bmesh.ops.translate(Q.bm, vec=(0, 0, z - lo), verts=Q.bm.verts[:])


def _seg(detail, n, lo=3):
    return max(lo, int(round(n * detail)))


def _dir(a):
    return Vector((math.cos(a), math.sin(a), 0.0))


def cranium(P, H, face, crown, s=1.0, detail=1.0, mouth=True):
    """The skull without its jaw (art/pass3's skull, the mandible left off): the dome, the face, the cheekbones, the
    eye sockets and the nose as dark hollows, the upper teeth's dark line."""
    F = rh.frame3(face, crown)
    f, u = F.col[0], F.col[1]
    l = u.cross(f)
    M = Matrix((f, l, u)).transposed()

    def at(x, y, z):
        return Vector(H) + (f * x + l * y + u * z) * s
    R = lambda r: tuple(v * s for v in r)                     # noqa: E731
    sg = _seg(detail, 12, 8)
    P.add('bone', lambda bm: rh.ellipsoid(bm, at(-0.015, 0, 0.025), M, R((0.092, 0.07, 0.075)), seg=sg), size=0.12)
    P.add('bone', lambda bm: rh.ellipsoid(bm, at(0.058, 0, -0.035), M, R((0.035, 0.048, 0.04)), seg=_seg(detail, 8, 6)), size=0.12)
    for sd in (1, -1):
        P.add('bone', lambda bm, sd=sd: rh.ellipsoid(bm, at(0.052, sd * 0.05, -0.012), M, R((0.022, 0.018, 0.014)), seg=6), size=0.12)
        P.add('dark', lambda bm, sd=sd: rh.ellipsoid(bm, at(0.071, sd * 0.027, 0.0), M, R((0.012, 0.019, 0.017)), seg=_seg(detail, 8, 6)))
    P.add('dark', lambda bm: rh.ellipsoid(bm, at(0.088, 0, -0.03), M, R((0.008, 0.01, 0.014)), seg=6))
    if mouth:
        P.add('dark', lambda bm: rh.ellipsoid(bm, at(0.078, 0, -0.064), M, R((0.01, 0.028, 0.007)), seg=6))


def mandible(P, c, fwd, up, s=1.0, open_=0.0):
    """The jaw on its own: a U from one hinge round the chin to the other. c: the middle of the U's open end; fwd: toward
    the chin; up: out of its upper face. open_ splays the hinge ends a little."""
    F = rh.frame3(fwd, up)
    f, u = F.col[0], F.col[1]
    l = u.cross(f)
    pts = [(-0.005, 0.05 + open_, 0.04), (0.0, 0.048, 0.0), (0.05, 0.036, -0.012), (0.085, 0.0, -0.01),
           (0.05, -0.036, -0.012), (0.0, -0.048, 0.0), (-0.005, -0.05 - open_, 0.04)]
    pts = [Vector(c) + (f * x + l * y + u * z) * s for x, y, z in pts]
    P.add('bone', lambda bm: rh.sweep(bm, pts, [0.008 * s, 0.011 * s, 0.01 * s, 0.012 * s, 0.01 * s, 0.011 * s, 0.008 * s], seg=5), size=0.12)


def skull_on_floor(P, x, y, yaw, roll=0.0, pitch=0.0, s=1.0, jaw=None, detail=1.0, z=0.0):
    """A skull resting on the floor at (x, y): its face toward `yaw` (radians), rolled onto its side by `roll`, tipped
    back by `pitch`. jaw: None (lost), 'beside' (lying a little in front of it) or (dx, dy, yaw) relative to the skull."""
    Q = painted()
    face = Vector((1, 0, 0))
    crown = Vector((0, 0, 1))
    Rm = Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(roll, 3, 'X') @ Matrix.Rotation(-pitch, 3, 'Y')
    cranium(Q, (0, 0, 0), Rm @ face, Rm @ crown, s=s, detail=detail)
    _rest_on(Q, 0.0)
    _merge_into(P, Q, Matrix.Translation((x, y, z)))
    if jaw is not None:
        if jaw == 'beside':
            jaw = (0.16 * s, 0.05 * s, yaw + 0.6)
        jx, jy, jyaw = jaw
        jaw_on_floor(P, x + jx, y + jy, jyaw, s=s, z=z)


def jaw_on_floor(P, x, y, yaw, s=1.0, z=0.0, flip=False):
    """A jaw lying apart on the floor (or on whatever is at height z) at (x, y), its chin toward yaw."""
    Q = painted()
    mandible(Q, (0, 0, 0), _dir(yaw), -Z if flip else Z, s=s * 0.97, open_=0.008)
    _rest_on(Q, 0.0)
    _merge_into(P, Q, Matrix.Translation((x, y, z)))


def bone_on_floor(P, a, b, r, z=0.0):
    """A long bone lying on the floor from plan point a to b."""
    a = Vector((a[0], a[1], z + r * 1.2))
    b = Vector((b[0], b[1], z + r * 1.2))
    P.add('bone', lambda bm: rh.long_bone(bm, a, b, r, seg=5))


def small_bones(P, c, n, rnd, spread=0.12, z=0.0):
    """Finger bones, a vertebra or two: little pale bits strayed on the floor round c."""
    c = Vector((c[0], c[1], 0.0))
    for k in range(n):
        p = c + Vector((rnd.uniform(-spread, spread), rnd.uniform(-spread, spread), 0))
        a = rnd.uniform(0, math.pi)
        L = rnd.uniform(0.02, 0.04)
        if k % 3 == 2:          # a vertebra: a squat lump
            P.add('bone', lambda bm, p=p: add_sphere(bm, (p.x, p.y, z + 0.012), 0.016, mat=0, seg=6, scale=(1, 1, 0.7)), size=0.1)
        else:
            q0 = Vector((p.x, p.y, z + 0.005)) - _dir(a) * L / 2
            q1 = Vector((p.x, p.y, z + 0.005)) + _dir(a) * L / 2
            P.add('bone', lambda bm, q0=q0, q1=q1: rh.sweep(bm, [q0, q1], [0.0055, 0.0045], seg=3), size=0.1)


def hand_lo(P, W, hd, curl=0.25, spread=1.0, s=1.0, n=4, up=None):
    """A hand's bones, simplified for distance: the wrist's knot and four fingers (palm down on whatever is below)."""
    W = Vector(W)
    hd = Vector((hd[0], hd[1], hd[2] if len(hd) > 2 else 0.0)).normalized()
    up = Vector(up) if up is not None else Z
    sd = hd.cross(up).normalized()
    M = rh.frame3(hd, up)
    P.add('bone', lambda bm: rh.ellipsoid(bm, W + hd * 0.024 * s, M, (0.026 * s, 0.01 * s, 0.028 * s), seg=6), size=0.1)
    for k in range(n):
        o = (k - (n - 1) / 2) * 0.016 * s
        d0 = (hd + sd * 0.12 * (k - (n - 1) / 2) * spread).normalized()
        b = W + hd * 0.04 * s + sd * o
        p1 = b + d0 * 0.06 * s
        d1 = (d0 * math.cos(curl) - up * math.sin(curl)).normalized()
        p2 = p1 + d1 * 0.045 * s
        P.add('bone', lambda bm, b=b, p1=p1, p2=p2: rh.sweep(bm, [b, p1, p2], [0.0055 * s, 0.005 * s, 0.004 * s], seg=3), size=0.1)


def boot(P, A, fd, up, s=1.0, seed=0.0):
    """A boot (the foot's bones inside it), the ankle at A, toes along fd, its top along up."""
    fd = Vector(fd).normalized()
    up = Vector(up)
    up = (up - fd * up.dot(fd)).normalized()
    lat = up.cross(fd)
    R = Matrix((fd, lat, up)).transposed().to_4x4()
    c = Vector(A) + fd * 0.07 * s - up * 0.02 * s
    P.add('shoe', lambda bm: rounded_box((0.25 * s, 0.088 * s, 0.08 * s), c, p=4.0, cuts=2, dents=((0.004, 9.0),), seed=seed,
                                         bm=bm, mat=0, rot=R), size=0.25)
    P.add('shoe', lambda bm: add_cyl(bm, Vector(A) - fd * 0.035 * s + up * 0.0, Vector(A) - fd * 0.03 * s + up * 0.07 * s,
                                     0.042 * s, 0.046 * s, mat=0, seg=8), size=0.25)


def ribs_fallen(P, top, bottom, lat, rnd, n=6, s=1.0, lift=0.03, splay=1.0, missing=0.15, z=0.0):
    """The ribs of someone lying on their back, fallen in: arcs from the spine (top to bottom, on the floor) lying
    nearly flat out to each side, sagging toward the feet; some strayed or gone."""
    top, bottom = Vector(top), Vector(bottom)
    dn = (bottom - top)
    L = dn.length
    dn.normalize()
    lat = Vector(lat).normalized()
    for i in range(n):
        u = (i + 0.5) / n
        S = top.lerp(bottom, 0.05 + 0.85 * u)
        a = (0.11 + 0.07 * math.sin(math.pi * (0.2 + 0.7 * u))) * s * splay
        drop = (0.06 + 0.05 * u) * s * L / 0.3
        for side in (1, -1):
            if rnd.random() < missing:
                continue
            j = rnd.uniform(-0.25, 0.25)
            off = dn * rnd.uniform(-0.015, 0.015)
            pts = []
            for k in range(5):
                t = math.pi * 0.85 * k / 4
                q = S + off + lat * side * a * math.sin(t) + dn * drop * ((1 - math.cos(t)) / 2 + j * 0.3 * math.sin(t))
                q.z = z + 0.008 + lift * math.sin(t * 0.9) * (0.6 + 0.4 * rnd.random())
                pts.append(q)
            P.add('bone', lambda bm, pts=pts: rh.sweep(bm, pts, [0.0085 * s] * 4 + [0.0065 * s], seg=3), size=0.15)


def rib_pile(P, c, rnd, n=7, radius=0.1, z0=0.03, z1=0.14, s=1.0):
    """Ribs fallen into a heap (a lap, the floor under a slumped back): loose arcs at all angles."""
    c = Vector(c)
    for _ in range(n):
        p = c + Vector((rnd.uniform(-radius, radius), rnd.uniform(-radius, radius) * 1.2, rnd.uniform(z0, z1)))
        yaw = rnd.uniform(0, 2 * math.pi)
        tilt = rnd.uniform(-0.6, 0.6)
        r = rnd.uniform(0.07, 0.12) * s
        R = Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(tilt, 3, 'X')
        a0 = rnd.uniform(0, 1.0)
        pts = [p + R @ Vector((r * math.cos(a0 + 1.9 * k / 4), r * math.sin(a0 + 1.9 * k / 4), 0)) for k in range(5)]
        P.add('bone', lambda bm, pts=pts: rh.sweep(bm, pts, [0.0085 * s] * 4 + [0.0065 * s], seg=3), size=0.15)


def spine_loose(P, pts, rnd, z=None, breaks=1):
    """The spine come apart: the chain of vertebrae along pts, broken into a few runs with gaps, each jogged a little."""
    pts = [Vector(p) for p in pts]
    path = []
    for a, b in zip(pts, pts[1:]):
        k = max(1, int((b - a).length / 0.05))
        path += [a.lerp(b, i / k) for i in range(k)]
    path.append(pts[-1])
    cut = sorted(rnd.sample(range(2, max(3, len(path) - 2)), min(breaks, max(0, len(path) - 4)))) if len(path) > 5 else []
    runs, prev = [], 0
    for c in cut + [len(path)]:
        runs.append(path[prev:c])
        prev = c + 1
    for run in runs:
        if len(run) < 2:
            continue
        jog = Vector((rnd.uniform(-0.02, 0.02), rnd.uniform(-0.02, 0.02), 0))
        rr = [p + jog for p in run]
        rh.spine(P, rr, step=0.05)


# --------------------------------------------------------------------------
# Cloth lying over what is left: height fields over the bones (capsules as art/pass3's shrouds)
# --------------------------------------------------------------------------

def _support(caps, x, y):
    h = 0.0
    for c in caps:
        v = rh._cap_height(x, y, c)
        if v > h:
            h = v
    return h


def _tent(caps, x, y, k=2.6, r=(0.035, 0.07)):
    """The cloth's height at (x, y): the bones under it, the cloth tenting from them at slope k."""
    h = _support(caps, x, y)
    for rr in r:
        for i in range(8):
            a = math.pi * 2 * i / 8
            v = _support(caps, x + rr * math.cos(a), y + rr * math.sin(a)) - k * rr
            if v > h:
                h = v
    return h


def panel(P, cell, line, wl, wr, caps, seed=0.0, nx=None, ny=4, layer=0, thick=0.008, k=2.6, edge_z=0.004,
          end_drop=(1.0, 0.5), ragged=0.014, floor=0.0, fill=0.014, creases=1.0):
    """A piece of cloth lying over the bones: along the plan polyline `line` [(x, y), ...], reaching wl to its left and
    wr to its right (per point or one number), its height the bones' (caps) tented, or at least `fill` (the cloth's own
    folds), rounded across so its long edges come down onto the floor, its ends lowered by end_drop (the fraction of
    the height kept at the start and the end). One-sided, facing up."""
    line = [Vector((p[0], p[1], 0.0)) for p in line]
    n = len(line)
    wl = wl if hasattr(wl, '__len__') else [wl] * n
    wr = wr if hasattr(wr, '__len__') else [wr] * n
    L = [0.0]
    for a, b in zip(line, line[1:]):
        L.append(L[-1] + (b - a).length)
    tot = L[-1]
    if nx is None:
        nx = max(2, int(tot / 0.05))
    rnd = random.Random(int(seed * 977) + 5)
    lift = 0.002 * layer
    ph = rnd.uniform(0, 6.28)

    def sample(t):
        d = t * tot
        for i in range(n - 1):
            if d <= L[i + 1] or i == n - 2:
                f = 0.0 if L[i + 1] == L[i] else (d - L[i]) / (L[i + 1] - L[i])
                f = max(0.0, min(1.0, f))
                p = line[i].lerp(line[i + 1], f)
                tg = (line[i + 1] - line[i]).normalized()
                if 0 < i and f < 0.3:                          # ease the turn at a joint
                    tg = (tg + (line[i] - line[i - 1]).normalized() * (0.3 - f) / 0.3).normalized()
                return p, tg, wl[i] + (wl[i + 1] - wl[i]) * f, wr[i] + (wr[i + 1] - wr[i]) * f
        return line[-1], (line[-1] - line[-2]).normalized(), wl[-1], wr[-1]
    pts = []
    for i in range(nx + 1):
        t = i / nx
        p, tg, a, b = sample(t)
        left = Vector((-tg.y, tg.x, 0.0))
        col = []
        for j in range(ny + 1):
            v = j / ny                                        # 0: the right edge .. 1: the left edge (faces up)
            w = -b + (a + b) * v
            q = p + left * w
            edge = j in (0, ny)
            if edge:
                q += left * (ragged * noise.noise(Vector((q.x * 9.0, q.y * 9.0, seed))) * (1 if j == ny else -1))
            if i in (0, nx):
                q += tg * (ragged * 0.8 * noise.noise(Vector((q.y * 11.0, seed, q.x * 3.0))) * (1 if i == nx else -1))
            h = _tent(caps, q.x, q.y, k=k)
            base = max(h + thick, fill)
            base += creases * (0.005 * noise.noise(Vector((q.x * 11.0, q.y * 11.0, seed * 1.7)))
                               + 0.004 * math.sin(ph + t * tot * 38.0 + 3.0 * v))
            prof = min(1.0, math.sin(math.pi * v) ** 0.5 * 1.12)
            z = edge_z + max(0.0, base - edge_z) * prof
            if i == 0:
                z = edge_z + (z - edge_z) * end_drop[0]
            elif i == nx:
                z = edge_z + (z - edge_z) * end_drop[1]
            q.z = floor + lift + max(edge_z + 0.001 * rnd.random(), z)
            col.append(q)
        pts.append(col)
    P.grid(cell, pts, nx, ny)


def _seg_d(x, y, a, b):
    ax, ay = a[0], a[1]
    dx, dy = b[0] - ax, b[1] - ay
    L2 = dx * dx + dy * dy
    t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, ((x - ax) * dx + (y - ay) * dy) / L2))
    return math.hypot(x - (ax + dx * t), y - (ay + dy * t)), t


_STEP = [0.032]


def garment(P, cell, segs, caps, seed=0.0, step=None, cuts=(), thick=0.008, fill=0.016, k=1.6, soft=0.05, edge_z=0.004,
            layer=0, creases=1.0, floor=0.0, ragged=0.012):
    """A garment gone flat over what is left: its outline the union of plan capsules segs [(a, b, ra, rb)] (a torso, a
    sleeve, a trouser leg: radius ra at a to rb at b) less the capsules cuts [(a, b, r)] (an open front), its height
    the bones under it (caps, tented at slope k) or at least `fill`, falling softly (over `soft`) to the floor at its
    edges, which are rotted a little ragged. One-sided, facing up, over a regular grid of `step`."""
    rnd = random.Random(int(seed * 613) + 3)
    step = step or _STEP[0]

    def mask(x, y):
        m = -1e9
        for a, b, ra, rb in segs:
            d, t = _seg_d(x, y, a, b)
            m = max(m, ra + (rb - ra) * t - d)
        for a, b, r in cuts:
            d, _ = _seg_d(x, y, a, b)
            m = min(m, d - r)
        return m + ragged * noise.noise(Vector((x * 7.0, y * 7.0, seed * 1.3)))
    x0 = min(min(a[0], b[0]) - max(ra, rb) for a, b, ra, rb in segs) - step
    x1 = max(max(a[0], b[0]) + max(ra, rb) for a, b, ra, rb in segs) + step
    y0 = min(min(a[1], b[1]) - max(ra, rb) for a, b, ra, rb in segs) - step
    y1 = max(max(a[1], b[1]) + max(ra, rb) for a, b, ra, rb in segs) + step
    nx, ny = int((x1 - x0) / step) + 1, int((y1 - y0) / step) + 1
    M = [[mask(x0 + i * step, y0 + j * step) for j in range(ny + 1)] for i in range(nx + 1)]
    keep = []
    for i in range(nx):
        for j in range(ny):
            if sum(1 for (a, b) in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)) if M[a][b] > 0) >= 2:
                keep.append((i, j))
    if not keep:
        return
    u0, v0, u1, v1 = P.rect_of(cell)
    tmp = bmesh.new()
    uvl = tmp.loops.layers.uv.new('UVMap')
    verts = {}
    e = 0.004
    lift = 0.0025 * layer
    ph = rnd.uniform(0, 6.28)

    def vert(i, j):
        if (i, j) in verts:
            return verts[(i, j)]
        x, y = x0 + i * step, y0 + j * step
        m = M[i][j]
        for _ in range(3):                                  # pull an outside corner in onto the outline
            if m >= 0:
                break
            gx = (mask(x + e, y) - mask(x - e, y)) / (2 * e)
            gy = (mask(x, y + e) - mask(x, y - e)) / (2 * e)
            g2 = gx * gx + gy * gy
            if g2 < 1e-8:
                break
            x, y = x - gx * m / g2, y - gy * m / g2
            m = mask(x, y)
        m = max(0.0, m)
        h = _tent(caps, x, y, k=k)
        base = max(h + thick, fill)
        base += creases * (0.005 * noise.noise(Vector((x * 11.0, y * 11.0, seed * 1.7))) + 0.003 * math.sin(ph + x * 31.0 + y * 7.0))
        f = min(1.0, m / soft)
        f = f * f * (3 - 2 * f)
        z = floor + lift + edge_z + 0.001 * rnd.random() + max(0.0, base - edge_z) * f
        v = tmp.verts.new((x, y, z))
        verts[(i, j)] = v
        return v
    for (i, j) in keep:
        q = [vert(a, b) for (a, b) in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))]
        try:
            f = tmp.faces.new(q)
        except ValueError:
            continue
        for lp in f.loops:
            co = lp.vert.co
            a = min(1.0, max(0.0, (co.x - x0) / (x1 - x0)))
            b = min(1.0, max(0.0, (co.y - y0) / (y1 - y0)))
            lp[uvl].uv = (u0 + (u1 - u0) * (0.04 + 0.92 * a), v0 + (v1 - v0) * (0.04 + 0.92 * b))
    P._merge(tmp)


def curtain(P, cell, x, w, top, seed=0.0, lean=0.0, nu=10, nv=6, folds=0.012):
    """The back of a coat slumped against a wall (or hunched forward over the lap, lean > 0): cloth standing at x, w to
    each side, its top the line of the shoulders (rounded off at the ends), its foot spread on the floor; facing +x."""
    pts = []
    for i in range(nu + 1):
        u = -1 + 2 * i / nu
        t = top * max(0.0, 1 - u * u) ** 0.45 * (1 + 0.06 * noise.noise(Vector((u * 3.0, seed, 0.5))))
        col = []
        for j in range(nv + 1):
            v = j / nv
            z = t * v
            xx = x + lean * z + 0.04 * math.sin(math.pi * v) * (1 - u * u) + folds * math.sin(u * 9.0 + seed * 3.0) * (1 - 0.5 * v)
            xx += 0.06 * v * v                               # the collar fallen forward onto the pile
            yy = u * w * (1 + 0.45 * (1 - v) ** 2)          # spread wide where it meets the floor
            col.append(Vector((xx, yy, max(0.004, z))))
        pts.append(col)
    P.grid(cell, pts, nu, nv)


def _cap(a, b, rl, rv):
    return ((a[0], a[1], a[2] if len(a) > 2 else 0.0), (b[0], b[1], b[2] if len(b) > 2 else 0.0), rl, rv)


# --------------------------------------------------------------------------
# Poses
# --------------------------------------------------------------------------

def _lying_joints(arms, legs, rnd):
    J = dict(neck=V((-0.64, 0.0)), sl=V((-0.53, 0.19)), sr=V((-0.53, -0.19)), hl=V((0.02, 0.095)), hr=V((0.02, -0.095)))
    J['kl'], J['kr'] = V((0.44, 0.11)), V((0.44, -0.11))
    J['al'], J['ar'] = V((0.85, 0.12)), V((0.85, -0.12))
    if legs == 'bent':                                       # the left knee fallen out to the side
        J['kl'] = V((0.36, 0.34))
        J['al'] = V((0.78, 0.22))
    A = {'side': ((V((-0.27, 0.27)), V((-0.02, 0.29))), (V((-0.27, -0.27)), V((-0.02, -0.29)))),
         'chest': ((V((-0.25, 0.27)), V((-0.16, 0.02))), (V((-0.27, -0.27)), V((-0.02, -0.29)))),
         'out': ((V((-0.62, 0.45)), V((-0.66, 0.73))), (V((-0.3, -0.4)), V((-0.12, -0.6)))),
         'up': ((V((-0.8, 0.38)), V((-1.05, 0.45))), (V((-0.78, -0.33)), V((-1.03, -0.36)))),
         'folded': ((V((-0.27, 0.22)), V((-0.12, -0.06))), (V((-0.28, -0.22)), V((-0.09, 0.07)))),
         'across': ((V((-0.36, 0.33)), V((-0.22, 0.56))), (V((-0.27, -0.27)), V((-0.02, -0.29))))}[arms]
    (J['el'], J['wl']), (J['er'], J['wr']) = A
    for k in list(J):
        J[k] = J[k] + V((rnd.uniform(-0.012, 0.012), rnd.uniform(-0.012, 0.012)))
    return J


def _lying(P, rnd, seed, arms='side', legs='straight', coat='cloth', trousers='cloth', boots=True, skull_far=0.0,
           detail=1.0, skull=True, cap=False, under=()):
    J = _lying_joints(arms, legs, rnd)
    nk = J['neck']
    # The bones under the cloth, as capsules for its height: the ribs fallen in, the spine, the pelvis, the long bones.
    caps = [_cap((-0.55, 0.0), (-0.22, 0.0), 0.15, 0.045), _cap((-0.2, 0.0), (-0.06, 0.0), 0.03, 0.03),
            _cap((-0.04, 0.09), (0.03, 0.1), 0.06, 0.07), _cap((-0.04, -0.09), (0.03, -0.1), 0.06, 0.07),
            _cap((0.0, 0.0), (0.04, 0.0), 0.05, 0.05)]
    caps += list(under)                                      # whatever else the arms lie over (the other of a pair)
    for s_ in 'lr':
        caps += [_cap(J['s' + s_], J['e' + s_], 0.026, 0.028), _cap(J['e' + s_], J['w' + s_], 0.028, 0.024),
                 _cap(J['h' + s_], J['k' + s_], 0.028, 0.034), _cap(J['k' + s_], J['a' + s_], 0.026, 0.03),
                 _cap(J['k' + s_], J['k' + s_], 0.035, 0.045)]
    # Bones seen: the ribs between the lapels, the spine down the middle, the pelvis's wings at the coat's hem.
    ribs_fallen(P, (-0.55, 0.0, 0.0), (-0.24, 0.0, 0.0), (0, 1, 0), rnd, n=6, lift=0.035)
    spine_loose(P, [V((-0.6, rnd.uniform(-0.01, 0.01), 0.018)), V((-0.4, 0.0, 0.016)), V((-0.08, 0.0, 0.016))], rnd, breaks=1)
    rh.pelvis(P, V((0.0, 0.0, 0.055)), Z, V((0, 1, 0)), Z)
    # The coat lying open from the collar to the hem, the ribs fallen in between its fronts; the sleeves flat over
    # the arm bones, the hand bones out of the cuffs; the trousers flat over the leg bones, the boots fallen outward.
    gap = 0.045 + 0.025 * rnd.random()
    sl, sr = J['sl'], J['sr']
    garment(P, coat, [((-0.6, 0.0), (0.14, 0.0), 0.19, 0.2), (sl, sr, 0.075, 0.075)], caps, seed=seed + 1, layer=2,
            cuts=[((-0.72, 0.0), (0.2, 0.0), gap)], soft=0.06)
    sleeves = []
    for s_ in 'lr':
        S, E, W = J['s' + s_], J['e' + s_], J['w' + s_]
        cuff = W - (W - E).normalized() * 0.03
        sleeves += [(S, E, 0.07, 0.062), (E, cuff, 0.062, 0.056)]
    garment(P, coat, sleeves, caps, seed=seed + 3, layer=3, fill=0.026, soft=0.04)
    legs = [((-0.02, -0.11), (-0.02, 0.11), 0.1, 0.1)]
    for s_ in 'lr':
        Hp, K, A = J['h' + s_], J['k' + s_], J['a' + s_]
        legs += [(Hp, K, 0.085, 0.075), (K, A - (A - K).normalized() * 0.02, 0.075, 0.066)]
    garment(P, trousers, legs, caps, seed=seed + 5, layer=1, fill=0.026, soft=0.045)
    for s_ in 'lr':
        S, E, W = J['s' + s_], J['e' + s_], J['w' + s_]
        hd = (W - E).normalized()
        hz = max((_support(under, W.x + hd.x * 0.06, W.y + hd.y * 0.06) if under else 0.0), 0.0) + 0.012
        hand_lo(P, (W.x, W.y, hz), (hd.x, hd.y, 0.0), curl=0.15 if hz < 0.03 else 0.45, spread=1.3)
        # The foot fallen outward: a boot on its side, its toes out and a little up, or the bare bones.
        Hp, K, A = J['h' + s_], J['k' + s_], J['a' + s_]
        out = 1.0 if s_ == 'l' else -1.0
        lg = (A - K).normalized()
        lg3 = Vector((lg.x, lg.y, 0.0))
        po = Vector((-lg.y, lg.x, 0.0)) * out
        if boots:
            boot(P, Vector((A.x, A.y, 0.046)) + lg3 * 0.02, po * 0.95 + Z * 0.15 + lg3 * 0.2, -lg3, seed=seed + out)
        else:
            rh.foot(P, Vector((A.x, A.y, 0.035)) + lg3 * 0.03, lg3 * 0.5 + po * 0.65 + Z * 0.3, po * 0.8 + Z * 0.35 - lg3 * 0.3)
    # The skull: turned, rolled from the collar; the jaw apart from it. A few small bones strayed.
    if skull:
        side = 1 if rnd.random() < 0.5 else -1
        sx = nk.x - 0.13 - skull_far * 0.7 - rnd.uniform(0, 0.04)
        sy = side * (0.06 + skull_far * 0.5 + rnd.uniform(0, 0.05))
        skull_on_floor(P, sx, sy, yaw=math.pi + side * rnd.uniform(0.9, 1.6), roll=side * rnd.uniform(0.6, 1.3), detail=detail,
                       jaw=(0.12 - skull_far * 0.2, -side * 0.11, rnd.uniform(0, 6.28)))
    small_bones(P, (nk.x + 0.05, rnd.uniform(-0.25, 0.25)), 3, rnd, spread=0.12)
    small_bones(P, ((J['wl'].x + J['wr'].x) / 2 + 0.1, J['wl'].y + 0.06), 2, rnd, spread=0.08)
    if cap:
        _floor_cap(P, (nk.x - 0.1, -0.28), rnd.uniform(0, 6.28))


def _floor_cap(P, c, yaw, s=1.0):
    from build_story_depot import _cap as sorter_cap
    face = _dir(yaw)
    sorter_cap(P, Vector((c[0], c[1], -0.056)), Vector((0.12 * face.x, 0.12 * face.y, 1.0)), face)


def _curled(P, rnd, seed, coat='cloth', trousers='cloth', boots=True, detail=1.0):
    """On the right side, facing -y... (the figure faces +x: its front toward +y is its left side up)."""
    # Plan: the back along y -0.05 from x -0.45 (shoulders) to 0.05 (hips); knees drawn up toward +y.
    caps = [_cap((-0.45, 0.0, 0.0), (-0.12, 0.0, 0.0), 0.12, 0.13), _cap((-0.1, 0.0), (0.06, 0.0), 0.1, 0.13),
            _cap((0.05, 0.05), (0.2, 0.32), 0.05, 0.1), _cap((0.2, 0.32), (0.45, 0.2), 0.04, 0.07),
            _cap((0.02, -0.02), (0.18, 0.28), 0.05, 0.05), _cap((0.18, 0.28), (0.42, 0.12), 0.04, 0.04)]
    rib_pile(P, (-0.25, 0.04, 0.0), rnd, n=6, radius=0.08, z0=0.02, z1=0.08)
    spine_loose(P, [V((-0.5, -0.06, 0.02)), V((-0.2, -0.08, 0.02)), V((0.0, -0.06, 0.02))], rnd)
    rh.pelvis(P, V((0.04, 0.0, 0.08)), Z, V((0, 0, 1)), V((0, 1, 0)))
    garment(P, coat, [((-0.6, 0.0), (0.12, 0.03), 0.19, 0.17), ((-0.5, -0.16), (-0.5, 0.18), 0.07, 0.07)], caps, seed=seed + 1,
            layer=2, soft=0.08, k=1.6)
    legs = []
    for (a, b, c) in (((0.05, 0.05), (0.2, 0.32), (0.45, 0.2)), ((0.02, -0.04), (0.18, 0.26), (0.42, 0.1))):
        legs += [(a, b, 0.085, 0.075), (b, c, 0.075, 0.065)]
        if boots:
            boot(P, Vector((c[0] + 0.03, c[1], 0.048)), Vector((0.55, -0.35, 0.3)), Vector((-0.4, 0.4, 0.2)), seed=seed + a[1])
    garment(P, trousers, legs, caps, seed=seed + 4, layer=1, fill=0.026, soft=0.045)
    # The arms folded in front, the hands' bones out of the cuffs by the knees.
    sleeves = []
    for (S, E, W) in (((-0.45, 0.12), (-0.25, 0.3), (-0.02, 0.36)), ((-0.42, 0.06), (-0.2, 0.22), (0.0, 0.25))):
        sleeves += [(S, E, 0.065, 0.06), (E, W, 0.06, 0.055)]
        hd = (Vector(W) - Vector(E)).normalized()
        hand_lo(P, (W[0], W[1], _tent(caps, W[0], W[1]) + 0.012), hd, curl=0.4)
    garment(P, coat, sleeves, caps, seed=seed + 6, layer=3, fill=0.026, soft=0.04)
    skull_on_floor(P, -0.74, 0.12 + rnd.uniform(-0.04, 0.04), yaw=rnd.uniform(1.2, 2.2), roll=rnd.uniform(1.0, 1.4), detail=detail,
                   jaw=(0.1, 0.13, rnd.uniform(0, 6)))
    small_bones(P, (-0.55, 0.3), 3, rnd)


def _seated(P, rnd, seed, support=True, knees=0.3, bowl=False, skull='lap', coat='cloth', trousers='cloth', boots=True,
            cap=False, detail=1.0, arms='lap', hood=0.0):
    """Sat on the floor facing +x, collapsed."""
    back = 0.38 if support else 0.24                         # where the coat's shoulders came to rest
    bx = -0.12 if support else -0.06
    kz = 0.06 + 0.2 * knees                                  # the knees' height
    kx = 0.42 - 0.1 * knees
    ax = 0.82 - 0.32 * knees
    J = dict(hl=V((0.04, 0.1)), hr=V((0.04, -0.1)), kl=V((kx, 0.13)), kr=V((kx, -0.12)), al=V((ax, 0.15)), ar=V((ax, -0.14)))
    caps = [_cap((bx, 0.0, 0.0), (bx + 0.06, 0.0, 0.0), 0.24, 0.16),                       # the coat's fold at the back
            _cap((0.0, 0.0, 0.0), (0.16, 0.0, 0.0), 0.17, 0.17)]                          # the pile in the lap
    for s_ in 'lr':
        caps += [_cap(J['h' + s_], J['k' + s_], 0.05, 0.05 + 0.6 * (kz - 0.06)), _cap(J['k' + s_], J['k' + s_], 0.05, kz + 0.02),
                 _cap(J['k' + s_], J['a' + s_], 0.04, 0.03 + 0.5 * (kz - 0.06))]
    # The bones that fell: the ribs into the lap (between the fronts), the spine down the coat's back, the pelvis.
    rib_pile(P, (0.07, 0.0, 0.0), rnd, n=6, radius=0.07, z0=0.1, z1=0.17)
    rh.pelvis(P, V((0.02, 0.0, 0.07)), Z, V((0, 1, 0)), V((1, 0, 0.3)).normalized())
    # The coat: its back still up against the support, slumped over the pile, its fronts fallen open into the lap
    # (the ribs between them); the trousers over the leg bones.
    curtain(P, coat, bx - 0.02, 0.22, back + 0.02, seed=seed, lean=0.0 if support else 0.45, folds=0.022)
    garment(P, coat, [((bx + 0.04, 0.0), (0.3, 0.0), 0.25, 0.17)], caps, seed=seed + 1,
            layer=2, cuts=[((0.04, 0.0), (0.5, 0.0), 0.04)], soft=0.12, k=1.4, ragged=0.006)
    legs = []
    for s_ in 'lr':
        Hp, K, A = J['h' + s_], J['k' + s_], J['a' + s_]
        legs += [(Hp, K, 0.085, 0.075), (K, A - (A - K).normalized() * 0.02, 0.075, 0.066)]
    garment(P, trousers, legs, caps, seed=seed + 5, layer=1, fill=0.026, soft=0.045, k=2.0)
    for s_ in 'lr':
        Hp, K, A = J['h' + s_], J['k' + s_], J['a' + s_]
        out = 1.0 if s_ == 'l' else -1.0
        lg3 = Vector(((A - K).x, (A - K).y, 0.0)).normalized()
        po = Vector((-lg3.y, lg3.x, 0.0)) * out
        if boots:
            boot(P, Vector((A.x, A.y, 0.048)) + lg3 * 0.02, po * 0.85 + Z * 0.4 + lg3 * 0.2, -lg3 + Z * 0.3 * knees, seed=seed + out)
        else:
            rh.foot(P, Vector((A.x, A.y, 0.035)) + lg3 * 0.03, lg3 * 0.5 + po * 0.6 + Z * 0.35, po * 0.8 + Z * 0.35 - lg3 * 0.3)
    # The arms: the sleeves from the shoulders down over the thighs, the hand bones at the cuffs on the knees (or round
    # the bowl); or one fallen by the hip to the floor.
    H = lambda x, y: _tent(caps, x, y, k=1.4)               # noqa: E731
    sleeves = []
    hands = []
    for s_, sd in (('l', 1), ('r', -1)):
        S = V((bx + 0.04, sd * 0.2))
        if bowl:
            E, W = V((0.12, sd * 0.2)), V((0.28, sd * 0.08))
        elif arms == 'lap' or (arms == 'hip' and sd > 0):
            E, W = V((0.12, sd * 0.21)), V((0.34, sd * 0.12))
        else:                                                # by the hip, on the floor
            E, W = V((0.02, sd * 0.3)), V((0.2, sd * 0.36))
        hands.append((E, W))
        # The sleeve: from the shoulder, still up against the support, down over the thigh (or to the floor).
        S3 = Vector((bx + 0.04, sd * 0.15, (back + 0.02) * 0.74))
        E3 = Vector((E.x, E.y, H(E.x, E.y) + 0.035))
        W3 = Vector((W.x, W.y, H(W.x, W.y) + 0.03))
        rh.rag_tube(P, coat, S3, E3, 0.046, sag=0.01, seed=seed * 3 + sd, ragged=0.0, flat=0.75, seg=6, rows=2, side=Z)
        rh.rag_tube(P, coat, E3 - (E3 - S3).normalized() * 0.02, W3, 0.042, sag=0.0, seed=seed * 5 + sd, ragged=0.25, flat=0.7, seg=6,
                    rows=2, side=Z)
    for E, W in hands:
        hd = (W - E).normalized()
        hz = H(W.x + hd.x * 0.05, W.y + hd.y * 0.05) + 0.015
        hand_lo(P, (W.x, W.y, hz), (hd.x, hd.y, -0.2), curl=0.5)
    if bowl:                                                 # a tin bowl in the lap, the hands round it
        c = V((0.36, 0.0, 0.0))
        c.z = H(c.x, c.y) + 0.005
        prof = [(0.01, 0.0), (0.05, 0.0), (0.07, 0.025), (0.085, 0.05), (0.08, 0.052), (0.064, 0.026), (0.042, 0.006), (0.01, 0.006)]
        P.add('paper', lambda bm: rh.lathe(bm, prof, _seg(detail, 14, 10), center=c), size=0.2, closed=False)
    # The skull: dropped into the lap, rolled to the floor beside the hip, or still on the chest (sunk on the pile).
    if skull == 'lap':
        x, y = 0.3 + rnd.uniform(-0.03, 0.03), rnd.uniform(-0.05, 0.05)
        if bowl:
            x, y = 0.2, rnd.choice((-1, 1)) * 0.1
        skull_on_floor(P, x, y, yaw=rnd.uniform(-0.8, 0.8) + (0 if not bowl else math.pi * 0.5), roll=rnd.uniform(-0.5, 0.5),
                       pitch=rnd.uniform(0.2, 0.6), z=H(x, y) - 0.01, detail=detail)
        jx, jy = (0.5, rnd.uniform(-0.06, 0.06)) if not bowl else (0.12, 0.3)
        jaw_on_floor(P, jx, jy, rnd.uniform(0, 6), z=H(jx, jy))
    elif skull == 'floor':
        sd = rnd.choice((1, -1))
        skull_on_floor(P, 0.1 + rnd.uniform(-0.04, 0.04), sd * (0.36 + rnd.uniform(0, 0.06)), yaw=rnd.uniform(-1, 1) + sd * 0.8,
                       roll=sd * rnd.uniform(0.4, 1.2), detail=detail, jaw=(0.16, -sd * 0.04, rnd.uniform(0, 6)))
    elif skull == 'chest':
        x, y = 0.05, rnd.uniform(-0.03, 0.03)
        skull_on_floor(P, x, y, yaw=rnd.uniform(-0.4, 0.4), roll=rnd.uniform(-0.3, 0.3), pitch=0.9, z=H(x, y) - 0.03, detail=detail)
        jaw_on_floor(P, 0.36, 0.03, rnd.uniform(0, 6), z=H(0.36, 0.03))
    small_bones(P, (0.2, rnd.choice((-1, 1)) * 0.3), 3, rnd, spread=0.08)
    if cap:
        _floor_cap(P, (0.0, -0.36), rnd.uniform(0, 6.28))


def _scattered(P, rnd, seed, cloth_cell='rag', detail=1.0):
    skull_on_floor(P, -0.3 + rnd.uniform(-0.05, 0.05), 0.1, yaw=rnd.uniform(0, 6.28), roll=rnd.uniform(-1.4, 1.4), detail=detail,
                   jaw=(0.25, -0.15, rnd.uniform(0, 6)))
    for k in range(4):
        a = V((rnd.uniform(-0.35, 0.35), rnd.uniform(-0.25, 0.25)))
        ang = rnd.uniform(0, math.pi)
        L = rnd.uniform(0.25, 0.42)
        bone_on_floor(P, a - _dir(ang).to_2d() * L / 2, a + _dir(ang).to_2d() * L / 2, rnd.uniform(0.011, 0.014))
    rh.pelvis(P, V((0.25, -0.05, 0.06)), Z, V((0, 1, 0)), V((0.3, 0.2, 1)).normalized())
    rib_pile(P, (0.05, 0.1, 0.0), rnd, n=4, radius=0.12, z0=0.008, z1=0.02)
    panel(P, cloth_cell, [(-0.1, -0.2), (0.15, -0.12), (0.35, 0.05)], 0.12, 0.1, [], seed=seed, ny=2)
    small_bones(P, (0.0, 0.0), 5, rnd, spread=0.3)


SHROUD_SPEC = {}


def _shroud_specs():
    """art/pass3's sheet machinery, the bones under it long since fallen in: lower, flatter, the skull turned."""
    if SHROUD_SPEC:
        return SHROUD_SPEC
    flat = [((-0.735, 0.03, 0.0), (-0.665, 0.04, 0.0), 0.075, 0.11),                     # the skull, on its side
            ((-0.56, 0.0, 0.0), (-0.3, 0.0, 0.0), 0.15, 0.065),                            # the ribs, fallen in
            ((-0.3, 0.0, 0.0), (-0.1, 0.0, 0.0), 0.024, 0.022),
            ((-0.08, 0.1, 0.0), (0.0, 0.11, 0.0), 0.05, 0.06), ((-0.08, -0.1, 0.0), (0.0, -0.11, 0.0), 0.05, 0.06),
            ((-0.05, 0.0, 0.0), (0.02, 0.0, 0.0), 0.05, 0.035),
            ((0.03, 0.10, 0.0), (0.39, 0.10, 0.0), 0.022, 0.024), ((0.03, -0.10, 0.0), (0.39, -0.11, 0.0), 0.022, 0.024),
            ((0.39, 0.10, 0.0), (0.42, 0.10, 0.0), 0.03, 0.034), ((0.39, -0.11, 0.0), (0.42, -0.11, 0.0), 0.03, 0.034),
            ((0.42, 0.10, 0.0), (0.66, 0.11, 0.0), 0.022, 0.022), ((0.42, -0.11, 0.0), (0.66, -0.12, 0.0), 0.022, 0.022)]
    arm_in = [((-0.50, 0.21, 0.0), (-0.24, 0.22, 0.0), 0.022, 0.022), ((-0.24, 0.22, 0.0), (0.0, 0.21, 0.0), 0.022, 0.02)]
    arm_out = [((-0.50, 0.21, 0.0), (-0.26, 0.26, 0.0), 0.022, 0.022), ((-0.26, 0.26, 0.0), (-0.07, 0.35, 0.0), 0.022, 0.02)]
    feet = [((0.645, 0.11, 0.035), (0.5, 0.65, 0.3), (-0.3, 0.8, 0.35)),                   # fallen outward, low
            ((0.645, -0.12, 0.035), (0.5, -0.65, 0.3), (-0.3, -0.8, 0.35))]
    base = dict(rh.SHROUDS['adult'], caps=flat + arm_in + rh._mirror(arm_in), ribs=(-0.55, -0.32, 0.14, 0.045, 0.12),
                fine=(-0.79, -0.3), sheet=(-0.81, 0.58, -0.275, 0.275, 9), settle=3.6, feet=feet, shins=0.1, hand=None, length=1.65)
    SHROUD_SPEC['flat'] = base
    SHROUD_SPEC['flat_hand'] = dict(base, caps=flat + arm_out + rh._mirror(arm_in), hand=1)
    SHROUD_SPEC['flat_hand_r'] = dict(base, caps=flat + arm_in + rh._mirror(arm_out), hand=-1)
    SHROUD_SPEC['flat_child'] = dict(base, length=1.02, scale=(0.62, 0.72, 0.72))
    for k, v in SHROUD_SPEC.items():
        rh.SHROUDS['p6_' + k] = v
    return SHROUD_SPEC


def _shrouded(P, rnd, seed, hand=None, child=False, tag=True, kind=None):
    _shroud_specs()
    if kind is None:
        kind = 'flat_child' if child else {None: 'flat', 1: 'flat_hand', -1: 'flat_hand_r'}[hand]
    Q, _ = rh.shroud('p6_' + kind, seed)
    _merge_into(P, Q)


# --------------------------------------------------------------------------
# The API
# --------------------------------------------------------------------------

def add(P, pose, M=None, seed=0.0, **opts):
    """Add one set of remains in `pose` to the Painted P, through the 4x4 M (see the module's docstring)."""
    rnd = random.Random(int(seed * 7919) + 13)
    Q = painted()
    detail = opts.pop('detail', 1.0)
    _STEP[0] = 0.032 / max(0.3, detail)
    if pose == 'lying':
        _lying(Q, rnd, seed, detail=detail, **opts)
    elif pose == 'fallen':
        o = dict(arms='up', legs='bent', skull_far=0.35)
        o.update(opts)
        _lying(Q, rnd, seed, detail=detail, **o)
    elif pose == 'curled':
        _curled(Q, rnd, seed, detail=detail, **opts)
    elif pose == 'seated':
        lean = opts.pop('lean', 0.0)
        _seated(Q, rnd, seed, detail=detail, **opts)
        if lean:                                             # slumped to one side (+ its left): sheared over, lower
            for v in Q.bm.verts:
                z = v.co.z
                v.co.y += lean * 0.55 * z
                v.co.z = z * (1.0 - 0.22 * abs(lean))
    elif pose == 'pair':
        a = dict(opts.pop('a', {}))
        b = dict(opts.pop('b', {}))
        a.setdefault('arms', 'across')                       # one's arm across the other
        b.setdefault('arms', 'folded')
        if a['arms'] == 'across':
            a.setdefault('under', [_cap((-0.55, 0.5), (-0.1, 0.5), 0.2, 0.075), _cap((-0.1, 0.5), (0.05, 0.5), 0.15, 0.08)])
        A = painted()
        _lying(A, rnd, seed, detail=detail, **dict(opts, **a))
        _merge_into(Q, A, Matrix.Translation((0, -0.24, 0)) @ Matrix.Rotation(math.radians(-4), 4, 'Z'))
        B = painted()
        _lying(B, random.Random(int(seed * 7919) + 99), seed + 0.5, detail=detail, **dict(opts, **b))
        _merge_into(Q, B, Matrix.Translation((0.05, 0.26, 0)) @ Matrix.Rotation(math.radians(5), 4, 'Z') @ Matrix.Diagonal((1, -1, 1, 1)))
    elif pose == 'scattered':
        _scattered(Q, rnd, seed, detail=detail, **opts)
    elif pose == 'skull':
        skull_on_floor(Q, 0.0, 0.0, yaw=rnd.uniform(0, 6.28), roll=rnd.uniform(-1.2, 1.2), detail=detail,
                       jaw=opts.get('jaw', 'beside'))
    elif pose == 'shrouded':
        _shrouded(Q, rnd, seed, **opts)
    else:
        raise ValueError('remains: no pose %r (have %s)' % (pose, ', '.join(POSES)))
    _merge_into(P, Q, M)
    return P


_MESHES = {}


def mesh(pose, seed=0.0, name=None, **opts):
    """The pose alone as a bpy Mesh in RemainsMat (cached on the arguments), for linked duplicates."""
    key = (pose, seed, tuple(sorted((k, repr(v)) for k, v in opts.items())))
    me = _MESHES.get(key)
    if me is not None and me.name in bpy.data.meshes:
        return me
    P = painted()
    add(P, pose, None, seed, **opts)
    me = P.mesh(name or 'Remains_%s_%d' % (pose, len(_MESHES)), MAT)
    _MESHES[key] = me
    return me


def place(me, loc, turn=0.0, coll=None, name=None, mirror=False):
    ob = bpy.data.objects.new(name or me.name, me)
    (coll or bpy.context.scene.collection).objects.link(ob)
    ob.location = loc
    ob.rotation_euler = (0, 0, math.radians(turn))
    if mirror:
        ob.scale = (1, -1, 1)
    return ob


EXTENT = {'lying': (-1.0, 1.05, -0.4, 0.4, 0.12), 'fallen': (-1.2, 1.0, -0.65, 0.55, 0.12), 'curled': (-0.9, 0.6, -0.25, 0.45, 0.16),
          'seated': (-0.18, 0.95, -0.45, 0.45, 0.46), 'pair': (-1.0, 1.1, -0.65, 0.65, 0.12), 'scattered': (-0.5, 0.5, -0.35, 0.35, 0.1),
          'skull': (-0.12, 0.25, -0.12, 0.15, 0.14), 'shrouded': (-0.83, 0.83, -0.4, 0.4, 0.12)}


def extent(pose):
    return EXTENT[pose]
