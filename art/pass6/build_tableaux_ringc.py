"""Chapter 1, pass 6 (docs/chapter1_pass6_plan.md): the tableaux of DL-10 and DL-11. Built in FINAL world x, after the
pass 4 modules (art/dl01/build_dl01.py imports it once it exists). Every human remains here is art/pass6/remains.py's.

DL-10 Up Only. The last car went up and didn't come back.
  UOQueueRemains  They waited for it: five sets of remains seated on their cases in the waiting area behind the lane,
                  in a line facing the lift gate, in the order they queued (the head of the queue at the lift front).
                  Collapsed where they sat: the coats slumped into the laps, the skulls dropped, the trouser legs
                  over the cases' edges, the boots on the floor. One static object, RemainsMat.
  UOQueueCases    What they sat on: suitcases lying flat, a pair stacked, a trunk, a crate; a bundle or a holdall
                  beside some. Static; LuggageLeather, LuggageCanvas, DepotSteel, CrateWood.
  UOQueueCoat     A child's coat across the lap of the third in line: small, blue wool, its sleeves hanging either side,
                  a hood. Static; ChildCoat (new).
  Pass 4's belongings (UOBelongings) are rebuilt without the sewing machine, its cover and the kettle that stood
  where the queue sits; pass 3's burst case and doll (UODropped) are taken out from under it. Pass 4's hand marks
  (UOHandMarks) are removed (the director: they confused more than they told).
DL-11 ring C. The water rose.
  D5Outshot112    They went up: C-112's lean-to coal store against its front, a ladder up to its sloping tin roof.
  D5RoofRemains   On the roof, two together against the house wall, under one blanket, among what they carried up:
                  bundles, a case, a lamp, a kettle; the high water's line on the wall above them (the water came
                  over them). RemainsMat (the bundles, the blanket and the case are in its atlas too).
  D5RaftEmpty     The lashed table raft (pass 4's D5Raft, cut out of D5Street), empty, caught against the slot's
                  front wall, one edge riding up it.
  D5LairBank      The White's lair (pass 4's D5Lair, cut out of D5Street): the bank of silt at the alley's flooded
  D5LairRemains   foot, raised so its top breaks the surface at the steps; on it remains that have come apart, half
                  in the water: one lying head up the bank, a skull and long bones strewn down into the deep, a skull
                  on the first step. Pale bone near the surface, so it reads through the White's water.
  D5SealFloor     The floor under the seal (the barricade's crawl gap, x 134.2 .. 135.0 had none).
  C114Stair       A steep cottage stair up to the parents' rooms, along the living room's back wall.
  D5NameCard114Wall (on the facade) and the card beside the door (in C114Home) are removed: the one on the door stays.

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y. Game (x, y, z) = (x, z, -y).
"""
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector
from mathutils.kdtree import KDTree

HERE = os.path.dirname(os.path.abspath(__file__))
for _d in ('pass3', 'pass4', 'dl05', 'd17'):
    _p = os.path.join(HERE, '..', _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import build_d17 as d17  # noqa: E402
from build_d17 import add_box, add_cyl, add_sphere, add_torus, rounded_box, worn_material  # noqa: E402
import build_up_only as uo  # noqa: E402
import build_story_ringc as src  # noqa: E402
import remains as R  # noqa: E402

DECK = uo.DECK
OFF5 = 54.0                            # art/dl05's x + OFF5 = the final x


def _rz(a):
    return Matrix.Rotation(a, 4, 'Z')


def _rx(a):
    return Matrix.Rotation(a, 4, 'X')


def _ry(a):
    return Matrix.Rotation(a, 4, 'Y')


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


# =====================================================================================================================
# Materials
# =====================================================================================================================

NEW_WORN = {
    # A child's coat: blue wool, faded, dust on its folds.
    'ChildCoat': dict(base=(0.07, 0.11, 0.19), dirt=(0.04, 0.05, 0.06), chip=(0.12, 0.15, 0.2), rough=0.95, chip_rough=0.95,
                      metallic=0.0, grime_scale=8.0, chip_scale=30.0, chip_amount=0.75, dust_amount=0.5),
}
KNOWN_WORN = {
    'RingPlasterB': dict(base=(0.3, 0.2, 0.17), dirt=(0.15, 0.1, 0.08), chip=(0.2, 0.15, 0.12), rough=0.9, chip_rough=0.85, metallic=0.0),
    'FloodMud': dict(base=(0.062, 0.05, 0.036), dirt=(0.035, 0.028, 0.02), chip=(0.09, 0.076, 0.058), rough=0.95, chip_rough=0.85,
                     metallic=0.0),
    'Concrete': dict(base=(0.075, 0.074, 0.07), dirt=(0.035, 0.034, 0.03), chip=(0.12, 0.115, 0.105), rough=0.92, chip_rough=0.9,
                     metallic=0.0),
    'ShutterSteel': dict(base=(0.14, 0.16, 0.15), dirt=(0.09, 0.05, 0.025), chip=(0.2, 0.2, 0.19), rough=0.6, chip_rough=0.4,
                         metallic=0.5),
    'ParcelBrown': dict(base=(0.3, 0.22, 0.13), dirt=(0.15, 0.11, 0.07), chip=(0.4, 0.32, 0.2), rough=0.85, chip_rough=0.85,
                        metallic=0.0),
    'PigeonWood': dict(base=(0.16, 0.2, 0.2), dirt=(0.08, 0.08, 0.07), chip=(0.2, 0.14, 0.08), rough=0.8, chip_rough=0.8,
                       metallic=0.0),
}


def mat(name):
    """A material by name: the scene's own (the full build has them all), else made here."""
    mt = bpy.data.materials.get(name)
    if mt is not None:
        return mt
    if name in NEW_WORN:
        return worn_material(name, **NEW_WORN[name])
    if name in KNOWN_WORN:
        return worn_material(name, **KNOWN_WORN[name])
    return src.material(name)


def obj(name, bm, mats, coll, sharp=40):
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    return d17.mesh_object(name, bm, [mat(n) for n in mats], coll, sharp=sharp)


def painted_obj(name, P, coll):
    old = bpy.data.objects.get(name)
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    return P.obj(name, R.MAT, coll)


def merge_bm(dst, src_bm, M=None):
    if M is not None:
        bmesh.ops.transform(src_bm, matrix=M, verts=src_bm.verts[:])
    me = bpy.data.meshes.new('_t')
    src_bm.to_mesh(me)
    src_bm.free()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)


def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def report(ob, what):
    pts = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
    lo = [min(p[i] for p in pts) for i in range(3)]
    hi = [max(p[i] for p in pts) for i in range(3)]
    print(f'tableaux_ringc: {ob.name}: {tris(ob)} tris, mats {[m_.name for m_ in ob.data.materials]}, '
          f'Blender x {lo[0]:.2f}..{hi[0]:.2f} y {lo[1]:.2f}..{hi[1]:.2f} z {lo[2]:.2f}..{hi[2]:.2f} :: {what}')


def remove(name):
    ob = bpy.data.objects.get(name)
    if ob is not None:
        bpy.data.objects.remove(ob, do_unlink=True)
        print('tableaux_ringc: removed', name)
        return True
    print('tableaux_ringc: (nothing to remove:', name + ')')
    return False


def delete_faces(ob, pred, what):
    """Delete the faces of a mesh object for which pred(face, bm) is true (mesh-local coordinates)."""
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bm.faces.ensure_lookup_table()
    dead = [f for f in bm.faces if pred(f, bm)]
    bmesh.ops.delete(bm, geom=dead, context='FACES')
    bm.to_mesh(ob.data)
    bm.free()
    ob.data.update()
    print(f'tableaux_ringc: {ob.name}: {len(dead)} faces cut ({what})')
    return len(dead)


def drop_unused_slots(ob):
    """Remove material slots no face uses (they would be empty draw calls)."""
    me = ob.data
    used = sorted({p.material_index for p in me.polygons})
    if len(used) == len(me.materials):
        return
    remap = {old: new for new, old in enumerate(used)}
    idx = [0] * len(me.polygons)
    me.polygons.foreach_get('material_index', idx)
    keep = [me.materials[i] for i in used]
    me.materials.clear()
    for mt in keep:
        me.materials.append(mt)
    me.polygons.foreach_set('material_index', [remap[i] for i in idx])
    me.update()


# =====================================================================================================================
# Remains, composed from remains.py's poses
# =====================================================================================================================

def _islands(bm):
    """Connected pieces of a bmesh, as lists of verts."""
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
        out.append(isl)
    return out


def seated_on(P, M, h, seed, half_y=0.27, knee=0.42, **opts):
    """remains.py's 'seated' (on the floor, facing +x), lifted onto a seat h high: what lay on the floor round the
    figure (a skull rolled off, small bones) stays on the floor; the rest is raised; past the knee the shins and boots
    swing down over the seat's front edge onto the floor; the coat's skirts beyond the seat's sides (half_y) hang down
    them. Then placed by M."""
    Q = R.painted()
    o = dict(knees=0.0)
    o.update(opts)
    R.add(Q, 'seated', None, seed, **o)
    bm = Q.bm
    bm.verts.index_update()
    floor = set()
    for isl in _islands(bm):
        zs = [v.co.z for v in isl]
        cx = sum(v.co.x for v in isl) / len(isl)
        cy = sum(v.co.y for v in isl) / len(isl)
        if max(zs) < 0.16 and (abs(cy) > half_y - 0.02 or cx < -0.24) and len(isl) < 400:
            floor.update(v.index for v in isl)
    kz = 0.06 + 0.2 * o['knees']
    piv = Vector((knee, 0.0, kz + h))

    def place(co, ang):
        x, y, z = co
        if x <= knee:
            z2 = z + h
            x2 = x
        else:
            a = ang * smooth(knee, knee + 0.12, x)
            dx, dz = x - piv.x, (z + h) - piv.z
            x2 = piv.x + dx * math.cos(a) + dz * math.sin(a)
            z2 = piv.z - dx * math.sin(a) + dz * math.cos(a)
        over = abs(y) - half_y                               # beyond the seat's sides: hanging down them
        if over > 0 and x <= knee + 0.05:
            z2 = max(0.004, z2 - over * 2.4)
        return Vector((x2, y, z2))

    lifted = [v for v in bm.verts if v.index not in floor]
    lo, hi = 0.0, 1.45                                       # swing the shins down until the boots touch the floor
    for _ in range(18):
        mid = (lo + hi) / 2
        mz = min(place(v.co, mid).z for v in lifted if v.co.x > knee + 0.05)
        if mz > 0.0:
            lo = mid
        else:
            hi = mid
    ang = lo
    for v in lifted:
        v.co = place(v.co, ang)
    R._merge_into(P, Q, M)


def draped(P, pose, M2, ground, seed, **opts):
    """remains.py's pose placed by the plan transform M2 (xy and a turn) and laid over the ground: z += ground(x, y)."""
    Q = R.painted()
    R.add(Q, pose, None, seed, **opts)
    bmesh.ops.transform(Q.bm, matrix=M2, verts=Q.bm.verts[:])
    if M2.to_3x3().determinant() < 0:
        bmesh.ops.reverse_faces(Q.bm, faces=Q.bm.faces[:])
    for v in Q.bm.verts:
        v.co.z += ground(v.co.x, v.co.y)
    P._merge(Q.bm)


# =====================================================================================================================
# DL-10: the queue
# =====================================================================================================================

QUEUE_Y = 0.47                         # the line they sat in, behind the lane (the lane: y -0.32 .. 0.16)
# Who sat where, from the head of the queue: (x of the seat's centre, seat, the remains' opts, seed).
# Seats: ('flat', L, W, H, body) a suitcase lying flat; ('stack', ...) two; ('trunk', L, W, H); ('crate', L, W, H).
QUEUE = [
    (122.72, ('trunk', 0.62, 0.42, 0.4), dict(support=True, skull='lap', arms='lap', coat='cloth'), 1.0),
    (121.86, ('stack', 0.58, 0.38, 0.19, 'LuggageLeather'), dict(support=True, skull='floor', arms='lap', coat='cloth'), 2.0),
    (121.0, ('flat', 0.6, 0.38, 0.22, 'LuggageCanvas'), dict(support=True, skull='chest', arms='hip', coat='rag'), 3.0),
    (120.12, ('crate', 0.5, 0.4, 0.34), dict(support=True, skull='lap', arms='lap', coat='cloth', cap=True), 4.0),
    (119.3, ('flat', 0.56, 0.36, 0.2, 'LuggageLeather'), dict(support=False, skull='floor', arms='lap', coat='rag', knees=0.15), 5.0),
]
COAT_ON = 1                            # the child's coat is across the lap of QUEUE[1]
LEA, CAN, STL, WOOD = range(4)
QUEUE_MATS = ('LuggageLeather', 'LuggageCanvas', 'DepotSteel', 'CrateWood')


def seat_height(seat):
    kind = seat[0]
    if kind == 'stack':
        return seat[3] * 2 - 0.01
    return seat[3]


def build_seat(bm, x, y, seat, rnd):
    """A seat in the queue (its top at seat_height): turned a little, as each was put down."""
    kind = seat[0]
    yaw = rnd.uniform(-0.12, 0.12)
    M = Matrix.Translation((x, y, DECK)) @ _rz(yaw)
    t = bmesh.new()
    if kind in ('flat', 'stack'):
        L, W, H, body = seat[1], seat[2], seat[3], seat[4]
        b = LEA if body == 'LuggageLeather' else CAN
        n = 2 if kind == 'stack' else 1
        base = 0.0
        for k in range(n):
            # a suitcase lying on its side: its length across the line (y), its thickness now its height
            tmp = bmesh.new()
            uo.suitcase(tmp, (0, 0, 0), (L, H, W), _rx(math.radians(90)), b if k == 0 else (CAN if b == LEA else LEA), STL, LEA)
            lo = min(v.co.z for v in tmp.verts)
            ys = [v.co.y for v in tmp.verts]
            Mk = (Matrix.Translation((rnd.uniform(-0.02, 0.02) * k, 0, base - lo)) @ _rz(math.pi / 2 + rnd.uniform(-0.08, 0.08) * k)
                  @ Matrix.Translation((0, -(min(ys) + max(ys)) / 2, 0)))
            merge_bm(t, tmp, Mk)
            base = max(v.co.z for v in t.verts) - 0.012
    elif kind == 'trunk':
        L, W, H = seat[1], seat[2], seat[3]
        uo.bx(t, (-W / 2, W / 2), (-L / 2, L / 2), (0, H - 0.04), LEA, 0.012)
        uo.bx(t, (-W / 2 - 0.004, W / 2 + 0.004), (-L / 2 - 0.004, L / 2 + 0.004), (H - 0.06, H), LEA, 0.01)     # the lid
        for yy in (-L / 2 + 0.06, L / 2 - 0.06):
            uo.bx(t, (-W / 2 - 0.006, W / 2 + 0.006), (yy - 0.025, yy + 0.025), (-0.002, H + 0.004), WOOD, 0.004)  # its battens
        for zz in (0.08, H - 0.1):
            uo.bx(t, (-W / 2 - 0.008, W / 2 + 0.008), (-L / 2 - 0.008, L / 2 + 0.008), (zz - 0.012, zz + 0.012), STL, 0.003)
        uo.bx(t, (W / 2, W / 2 + 0.012), (-0.04, 0.04), (H - 0.13, H - 0.06), STL, 0.003)                         # the hasp
    elif kind == 'crate':
        L, W, H = seat[1], seat[2], seat[3]
        for zz in (0.0, H / 2):
            for sx in (-1, 1):
                uo.bx(t, (sx * W / 2 - 0.012, sx * W / 2 + 0.012), (-L / 2, L / 2), (zz + 0.01, zz + H / 2 - 0.02), WOOD, 0.004)
                uo.bx(t, (-W / 2, W / 2), (sx * L / 2 - 0.012, sx * L / 2 + 0.012), (zz + 0.01, zz + H / 2 - 0.02), WOOD, 0.004)
        uo.bx(t, (-W / 2, W / 2), (-L / 2, L / 2), (H - 0.02, H), WOOD, 0.004)
        for sx in (-1, 1):
            for sy in (-1, 1):
                uo.bx(t, (sx * (W / 2 - 0.02) - 0.02, sx * (W / 2 - 0.02) + 0.02), (sy * (L / 2 - 0.02) - 0.02, sy * (L / 2 - 0.02) + 0.02),
                      (0, H), WOOD, 0.004)
    merge_bm(bm, t, M)
    return yaw


def build_beside(bm, rnd):
    """Bundles and bags put down beside them in the line (behind the lane, low)."""
    for kind, args, x, y, yaw in (
            ('bag', (0.42, 0.1, CAN, False), 122.25, 0.82, 0.1),
            ('bundle', (0.34, 0.3, 0.2, CAN, 11.0), 121.42, 0.86, -0.3),
            ('bag', (0.4, 0.09, LEA, False), 120.55, 0.42, 1.4),
            ('bundle', (0.3, 0.28, 0.18, CAN, 12.0), 119.72, 0.43, 0.6)):
        t = bmesh.new()
        if kind == 'bag':
            L, r, m_, burst = args
            src.it_bag(t, L, r, m_)
        else:
            L, W, H, m_, seed = args
            src.it_bundle(t, L, W, H, m_, seed)
        for f in t.faces:                                        # src's indices are BELONG_MATS'; ours are QUEUE_MATS'
            f.material_index = {src.LEA: LEA, src.CAN: CAN, src.STL: STL, src.WOOD: WOOD}.get(f.material_index, CAN)
        merge_bm(bm, t, Matrix.Translation((x, y, DECK)) @ _rz(yaw))


def child_coat(bm, c, yaw, lap_z, rnd):
    """A child's coat laid across a lap: the body folded over the thighs (across them, along y), the sleeves and the
    hem hanging down either side, a hood, three buttons. c: the middle of the lap (x, y), lap_z: the thighs' top."""
    M = Matrix.Translation((c[0], c[1], 0.0)) @ _rz(yaw)
    t = bmesh.new()

    rounded_box((0.26, 0.6, 0.05), (0, 0, 0), p=2.2, cuts=8, mat=0, bm=t, seed=rnd.uniform(0, 9), dents=((0.006, 9.0),))
    for v in t.verts:                                            # the drape, by hand (the shape hook sees normalised coords)
        y = v.co.y
        over = max(0.0, abs(y) - 0.12)
        v.co.z = v.co.z * 0.5 + lap_z + 0.035 - over * 1.4 - over * over * 3.0
        v.co.x += 0.03 * math.sin(y * 9.0)
    for sd in (-1, 1):                                           # the sleeves, hanging down the near side
        a = Vector((0.1, sd * 0.13, lap_z + 0.04))
        b = Vector((0.2, sd * 0.2, lap_z - 0.08))
        cc = Vector((0.22, sd * 0.22, lap_z - 0.2))
        add_cyl(t, a, b, 0.032, 0.03, mat=0, seg=7)
        add_cyl(t, b, cc, 0.03, 0.027, mat=0, seg=7)
    add_sphere(t, (-0.06, 0.26, lap_z - 0.07), 0.07, mat=0, seg=8, scale=(1.0, 0.7, 1.1))      # the hood, hanging
    for k in range(3):
        add_sphere(t, (0.06, -0.08 + 0.08 * k, lap_z + 0.065), 0.011, mat=1, seg=6, scale=(1, 1, 0.5))
    merge_bm(bm, t, M)


def build_queue(coll):
    rnd = random.Random(6101)
    cases = bmesh.new()
    P = R.painted()
    coat = bmesh.new()
    for k, (x, seat, opts, seed) in enumerate(QUEUE):
        y = QUEUE_Y + rnd.uniform(-0.03, 0.03)
        build_seat(cases, x, y, seat, rnd)
        h = seat_height(seat)
        turn = rnd.uniform(-8, 8)                               # facing the gate (+x), each a little askew
        M = Matrix.Translation((x - 0.02, y, DECK)) @ _rz(math.radians(turn))
        if k % 2:
            M = M @ Matrix.Diagonal((1, -1, 1, 1))
        o = dict(opts)
        if k == COAT_ON:
            o['skull'] = 'floor'
        seated_on(P, M, h, seed, **o)
        if k == COAT_ON:
            child_coat(coat, (x + 0.22, y), math.radians(turn), DECK + h + 0.13, rnd)
    build_beside(cases, rnd)
    oc = obj('UOQueueCases', cases, QUEUE_MATS, coll, sharp=40)
    orr = painted_obj('UOQueueRemains', P, coll)
    oco = obj('UOQueueCoat', coat, ('ChildCoat', 'DepotSteel'), coll, sharp=50)
    for ob, what in ((oc, 'DL-10: what the queue sat on'), (orr, 'DL-10: the queue, seated, facing the gate'),
                     (oco, "DL-10: the child's coat across a lap")):
        report(ob, what)


def rebuild_belongings(coll):
    """Pass 4's UOBelongings again, without what stood where the queue sits."""
    drop = {('sewing', 121.33), ('cover', 121.36), ('kettle', 122.48)}
    orig = src._pieces

    def pieces():
        return [p for p in orig() if (p[0], round(p[2], 2)) not in drop]
    remove('UOBelongings')
    src._pieces = pieces
    try:
        ob = src.build_belongings(coll)
    finally:
        src._pieces = orig
    report(ob, 'DL-10: pass 4 belongings, rebuilt around the queue')


def trim_dropped():
    """Pass 3's dropped things (UODropped): the burst case and its clothes and the doll go (the queue sits there);
    the child's shoe on the front line and the birdcage stay."""
    ob = bpy.data.objects.get('UODropped')
    if ob is None:
        return
    W = ob.matrix_world
    doll = Vector((122.88, 0.44))

    def pred(f, bm):
        c = W @ f.calc_center_median()
        if c.z > DECK + 0.3:
            return False
        if 121.45 < c.x < 122.45 and 0.15 < c.y < 1.0:            # the case burst open, its clothes
            return True
        return (Vector((c.x, c.y)) - doll).length < 0.32 and not (123.1 < c.x and c.y > 0.56)
    delete_faces(ob, pred, 'the burst case and the doll, under the queue')
    drop_unused_slots(ob)


# =====================================================================================================================
# DL-11: cut pass 4's raft and lair out of D5Street
# =====================================================================================================================

class _AnyMat(dict):
    """build_dl05's material dict, for a rebuild whose geometry only is wanted."""
    def __missing__(self, key):
        mt = bpy.data.materials.get('_p6_any') or bpy.data.materials.new('_p6_any')
        return mt


def strip_drowning():
    """Find pass 4's D5Raft and D5Lair in D5Street (rebuilt from build_dl05.build_drowning, in its own coordinates as
    D5Street's mesh still is) and cut them out, face by face. D5Pram stays."""
    import build_dl05 as d5
    street = bpy.data.objects.get('D5Street')
    if street is None:
        print('tableaux_ringc: no D5Street')
        return
    tmp = bpy.data.collections.new('_p6_tmp')
    keep = {n: bpy.data.objects.get(n) for n in ('D5Raft', 'D5Pram', 'D5Lair')}
    for n, o in keep.items():                                    # names free for the rebuild
        if o is not None:
            o.name = n + '_p6keep'
    d5.build_drowning(_AnyMat(), tmp)
    centres = []
    for n in ('D5Raft', 'D5Lair'):
        o = bpy.data.objects.get(n)
        for p in o.data.polygons:
            centres.append((o.matrix_world @ p.center, len(p.vertices)))
    for o in list(tmp.objects):
        me = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if me.users == 0:
            bpy.data.meshes.remove(me)
    bpy.data.collections.remove(tmp)
    for n, o in keep.items():
        if o is not None:
            o.name = n
    any_ = bpy.data.materials.get('_p6_any')
    if any_ is not None and any_.users == 0:
        bpy.data.materials.remove(any_)
    kd = KDTree(len(centres))
    for i, (c, _) in enumerate(centres):
        kd.insert(c, i)
    kd.balance()

    def pred(f, bm):
        c = f.calc_center_median()
        co, i, d = kd.find(c)
        return co is not None and d < 2e-4 and centres[i][1] == len(f.verts)
    n = delete_faces(street, pred, "pass 4's raft and lair")
    print(f'tableaux_ringc: D5Street: {len(centres)} faces looked for, {n} cut')
    drop_unused_slots(street)


# =====================================================================================================================
# DL-11: the raft, empty, caught against a wall
# =====================================================================================================================

RAFT = (150.12, -0.74, -0.03, 8.0, -21.0, 4.0)     # x, y, deck centre height, yaw, roll (its front edge up the wall), pitch


def build_raft(coll):
    x, y, z, yaw, roll, pitch = RAFT
    M = Matrix.Translation((x, y, z)) @ _rz(math.radians(yaw)) @ _rx(math.radians(roll)) @ _ry(math.radians(pitch))
    tb = bmesh.new()
    wd, stl, rope = 0, 1, 2
    L, D = 0.66, 0.5
    uo.cbox(tb, (0, 0, -0.0175), (L, D, 0.035), 0.006, wd)                             # the top, upside down
    for s in (-1, 1):
        uo.cbox(tb, (0, s * (D / 2 - 0.05), 0.03), (L - 0.08, 0.022, 0.06), 0.004, wd)   # its apron
        uo.cbox(tb, (s * (L / 2 - 0.05), 0, 0.03), (0.022, D - 0.1, 0.06), 0.004, wd)
        for t_ in (-1, 1):
            uo.cbox(tb, (s * (L / 2 - 0.05), t_ * (D / 2 - 0.05), 0.07), (0.045, 0.045, 0.14), 0.005, wd)   # the legs, sawn short
    for k, (yy, ln, a) in enumerate(((-0.1, 0.8, 0.0), (0.1, 0.78, 0.03))):              # planks lashed across
        uo.cbox(tb, (0.01 * k, yy, 0.071), (ln, 0.1, 0.022), 0.004, wd, rot=_rz(a))
    for sx in (-1, 1):
        for yy in (-0.1, 0.1):
            add_torus(tb, (sx * (L / 2 - 0.05), yy, 0.06), (1, 0, 0), 0.045, 0.006, mat=rope, seg=8, rseg=3)
    add_cyl(tb, (-L / 2 + 0.05, -D / 2 + 0.05, 0.12), (L / 2 - 0.05, -D / 2 + 0.05, 0.12), 0.006, seg=4, mat=rope)   # the hand line
    pts = [Vector((-L / 2 + 0.05, D / 2 - 0.05, 0.12)), Vector((0.05, D / 2 - 0.04, 0.11)), Vector((0.2, D / 2 + 0.02, 0.02)),
           Vector((0.28, D / 2 + 0.1, -0.06))]                                            # the other, cut: its end in the water
    for a_, b_ in zip(pts, pts[1:]):
        add_cyl(tb, a_, b_, 0.006, seg=4, mat=rope)
    add_cyl(tb, (-0.26, -0.13, -0.17), (0.26, -0.13, -0.17), 0.13, seg=14, mat=stl)      # the drum lashed under
    for sx in (-0.16, 0.16):
        add_torus(tb, (sx, -0.13, -0.17), (1, 0, 0), 0.134, 0.006, mat=rope, seg=14, rseg=3)
    bmesh.ops.transform(tb, matrix=M, verts=tb.verts)
    ob = obj('D5RaftEmpty', tb, ('CrateWood', 'DepotSteel', 'ParcelBrown'), coll, sharp=40)
    report(ob, 'DL-11: the lashed table raft, empty, caught against the slot\'s front wall')


# =====================================================================================================================
# DL-11: the White's lair
# =====================================================================================================================

ALLEY = (93.05 + OFF5, 93.95 + OFF5)        # the stepped alley between C-108 and C-110 (its walls 0.16 thick)
LAIR_X = (ALLEY[0] + 0.17, ALLEY[1] - 0.17)
WATER_Z = -0.1
BANK = ((1.05, -0.9), (1.45, -0.66), (1.85, -0.42), (2.12, -0.22), (2.3, -0.1), (2.42, -0.05))   # (y, z): out of the water at the steps


def bank_z(y):
    pts = BANK
    if y <= pts[0][0]:
        return pts[0][1]
    for (ya, za), (yb, zb) in zip(pts, pts[1:]):
        if y <= yb:
            return za + (zb - za) * (y - ya) / (yb - ya)
    return pts[-1][1]


def build_lair(coll):
    rnd = random.Random(6201)
    x0, x1 = LAIR_X
    bm = bmesh.new()
    # The bank of silt, from the alley's bed up to the foot of its steps; lumps in it.
    prof = [(BANK[0][0], -0.95), (BANK[-1][0], -0.95)] + list(BANK[::-1])
    verts = []
    for xx in (x0 - 0.02, x1 + 0.02):
        verts.append([bm.verts.new((xx, yy, zz)) for yy, zz in prof])
    n = len(prof)
    bm.faces.new(verts[0][::-1])
    bm.faces.new(verts[1])
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((verts[0][i], verts[0][j], verts[1][j], verts[1][i]))
    for k in range(6):
        yy = rnd.uniform(1.4, 2.35)
        rounded_box((rnd.uniform(0.14, 0.26), rnd.uniform(0.12, 0.22), 0.07), (rnd.uniform(x0 + 0.08, x1 - 0.08), yy, bank_z(yy) - 0.012),
                    p=2.0, cuts=1, seed=k, mat=0, bm=bm)
    ob = obj('D5LairBank', bm, ('FloodMud',), coll, sharp=60)
    report(ob, "DL-11: the White's lair, the bank of silt up to the alley's steps")

    P = R.painted()
    xc = (x0 + x1) / 2
    ground = lambda x, y: bank_z(y)                                                     # noqa: E731
    # One lying head up the bank, the skull out of the water at the steps' foot, the legs down into the deep.
    draped(P, 'lying', Matrix.Translation((xc + 0.02, 1.62, 0.0)) @ _rz(math.radians(-90 + 6)), ground, 11.0, arms='folded',
           coat='rag', trousers='cloth', boots=True)
    # Strewn down into the water: a skull and its jaw, long bones, a pelvis, a rag.
    draped(P, 'scattered', Matrix.Translation((xc - 0.04, 2.05, 0.0)) @ _rz(math.radians(80)) @ Matrix.Diagonal((0.62, 0.55, 1, 1)),
           ground, 12.0, cloth_cell='rag')
    draped(P, 'scattered', Matrix.Translation((xc + 0.03, 1.28, 0.0)) @ _rz(math.radians(-70)) @ Matrix.Diagonal((0.6, 0.6, 1, 1)),
           ground, 13.0, cloth_cell='cloth')
    # A skull on the first step, its jaw on the next one down (the bank); long bones across the step's edge.
    R.skull_on_floor(P, xc + 0.12, 2.5, yaw=math.radians(-120), roll=0.9, z=0.1, jaw=None)
    R.jaw_on_floor(P, xc - 0.1, 2.36, 1.2, z=bank_z(2.36))
    R.bone_on_floor(P, (xc - 0.2, 2.47), (xc + 0.02, 2.56), 0.013, z=0.1)
    R.bone_on_floor(P, (xc - 0.05, 2.28), (xc + 0.2, 2.2), 0.012, z=bank_z(2.24))
    for v in P.bm.verts:                                                                 # keep it inside the alley's walls
        v.co.x = max(x0 - 0.12, min(x1 + 0.12, v.co.x))
    ob = painted_obj('D5LairRemains', P, coll)
    report(ob, "DL-11: remains come apart on the lair's bank, half out of the water")


# =====================================================================================================================
# DL-11: they went up (C-112's coal store, its roof)
# =====================================================================================================================

C112 = (151.05, 153.5)
OUT_X = (152.3, 153.42)                 # the lean-to against C-112's front (over its boarded window's lower half)
OUT_Y = (0.46, 0.995)                   # its front wall's face .. the house's face
OUT_Z = (1.06, 1.46)                    # its roof: at the eave (front) .. at the house wall
LADDER = ((152.5, 0.24, 0.0), (152.43, 0.47, 1.4))   # foot, top (against the eave and up past it)


def roof_z(y):
    y0, y1 = OUT_Y
    z0, z1 = OUT_Z
    t = max(0.0, min(1.0, (y - y0) / (y1 - y0)))
    return z0 + (z1 - z0) * t


def roof_drape(y):
    """The roof, and past its eave a fall (what hangs over the edge hangs down)."""
    if y >= OUT_Y[0]:
        return roof_z(y)
    return OUT_Z[0] - (OUT_Y[0] - y) * 2.5


def build_outshot(coll):
    """The coal store: rough block walls plastered, a plank door, a tin roof sloping down to the street; the ladder."""
    x0, x1 = OUT_X
    y0, y1 = OUT_Y
    z0, z1 = OUT_Z
    bm = bmesh.new()
    PL, TIN, WD, STL = 0, 1, 2, 3
    ang = math.atan2(z1 - z0, y1 - y0)
    # Walls: the front (with the door's hole), the two sides (sloped tops).
    T = 0.1
    uo.bx(bm, (x0, x0 + 0.3), (y0, y0 + T), (0.0, z0 - 0.02), PL, 0.01)
    uo.bx(bm, (x1 - 0.12, x1), (y0, y0 + T), (0.0, z0 - 0.02), PL, 0.01)
    uo.bx(bm, (x0 + 0.3, x1 - 0.12), (y0, y0 + T), (0.92, z0 - 0.02), PL, 0.01)
    for xa, xb in ((x0, x0 + T), (x1 - T, x1)):
        prof = [(y0, 0.0), (y1, 0.0), (y1, z1 - 0.02), (y0, z0 - 0.02)]
        vs = [[bm.verts.new((xx, yy, zz)) for yy, zz in prof] for xx in (xa, xb)]
        bm.faces.new(vs[0][::-1]).material_index = PL
        bm.faces.new(vs[1]).material_index = PL
        for i in range(4):
            j = (i + 1) % 4
            bm.faces.new((vs[0][i], vs[0][j], vs[1][j], vs[1][i])).material_index = PL
    # The plank door, shut, in the front.
    for k in range(4):
        uo.bx(bm, (x0 + 0.3 + 0.002 + k * 0.1, x0 + 0.3 + 0.098 + k * 0.1), (y0 + 0.03, y0 + 0.06), (0.02, 0.9), WD, 0.004)
    uo.bx(bm, (x0 + 0.32, x1 - 0.14), (y0 + 0.01, y0 + 0.03), (0.6, 0.66), WD, 0.004)
    add_cyl(bm, (x1 - 0.2, y0 - 0.0, 0.5), (x1 - 0.2, y0 - 0.03, 0.5), 0.012, seg=6, mat=STL)
    # The roof: corrugated tin sheets on two purlins, lapped, overhanging the front; a batten along the wall.
    L = (y1 - y0 + 0.12) / math.cos(ang)
    n = 3
    w = (x1 - x0 + 0.08) / n
    for k in range(n):
        cx = x0 - 0.04 + w * (k + 0.5)
        Mr = Matrix.Translation((cx, (y0 + y1) / 2 - 0.06, (z0 + z1) / 2 - 0.035 + 0.012 * (k % 2))) @ _rx(ang) @ _rz(math.radians((k - 1) * 1.2))
        tmp = bmesh.new()
        ribs = 7
        verts = []
        for i in range(ribs * 4 + 1):
            xx = -w / 2 - 0.01 + (w + 0.02) * i / (ribs * 4)
            zz = 0.012 * math.sin(i * math.pi / 2)
            verts.append((tmp.verts.new((xx, -L / 2, zz)), tmp.verts.new((xx, L / 2, zz))))
        for (a0, a1), (b0, b1) in zip(verts, verts[1:]):
            tmp.faces.new((a0, b0, b1, a1)).material_index = TIN
        for (a0, a1), (b0, b1) in zip(verts, verts[1:]):                                # its underside
            tmp.faces.new((a1, b1, b0, a0)).material_index = TIN
        bmesh.ops.translate(tmp, vec=(0, 0, 0.0), verts=tmp.verts)
        merge_bm(bm, tmp, Mr)
    for yy in (y0 + 0.05, y1 - 0.06):
        add_box(bm, ((x0 + x1) / 2, yy, roof_z(yy) - 0.06), (x1 - x0, 0.06, 0.06), mat=WD, rot=_rx(ang))
    uo.bx(bm, (x0 - 0.04, x1 + 0.04), (y1 - 0.03, y1), (z1 - 0.02, z1 + 0.05), WD, 0.004)
    # The ladder: two rails and rungs, leaning on the eave, up past it.
    (fx, fy, fz), (tx, ty, tz) = LADDER
    a, b = Vector((fx, fy, fz)), Vector((tx, ty, tz))
    d = (b - a).normalized()
    side = Vector((1, 0, 0))
    for s in (-1, 1):
        add_cyl(bm, a + side * s * 0.17, b + side * s * 0.17, 0.022, seg=6, mat=WD)
    nr = int((b - a).length / 0.27)
    for k in range(1, nr + 1):
        p = a + d * (k * 0.27)
        add_cyl(bm, p - side * 0.17, p + side * 0.17, 0.014, seg=6, mat=WD)
    ob = obj('D5Outshot112', bm, ('RingPlasterB', 'ShutterSteel', 'CrateWood', 'DepotSteel'), coll, sharp=40)
    report(ob, "DL-11: C-112's coal store against its front, its tin roof, the ladder up to it")


def build_roof_remains(coll):
    """Two together against the house wall, sat on the sloping roof, under one blanket; what they carried up round them."""
    rnd = random.Random(6301)
    P = R.painted()
    ground = lambda x, y: roof_drape(y)                                                 # noqa: E731
    yb = OUT_Y[1] - 0.16
    # Seated with their backs to the wall, facing the street (-y), close: the second's shoulder against the first's.
    for k, (x, seed, o) in enumerate(((152.66, 21.0, dict(support=True, skull='lap', knees=1.0, coat='cloth', arms='lap')),
                                      (153.07, 22.0, dict(support=True, skull='chest', knees=0.9, coat='rag', arms='lap', boots=True)))):
        M2 = Matrix.Translation((x, yb, 0.0)) @ _rz(math.radians(-90 + (6 if k else -6)))
        if k:
            M2 = M2 @ Matrix.Diagonal((1, -1, 1, 1))
        draped(P, 'seated', M2, ground, seed, **o)
    # One blanket over both laps, its edge hanging over the eave.
    caps = []
    line = [(152.42, yb - 0.32), (152.86, yb - 0.35), (153.3, yb - 0.31)]
    Q = R.painted()
    R.panel(Q, 'sheet', line, 0.18, 0.16, caps, seed=3.0, ny=4, fill=0.03)
    for v in Q.bm.verts:
        v.co.z += roof_z(v.co.y) + 0.12 + 0.05 * math.exp(-((v.co.y - (yb - 0.33)) / 0.08) ** 2)
    P._merge(Q.bm)
    # What they carried up: a bundle in a sheet, a holdall, a case on its side, a lamp, a kettle.
    def at(x, y, dz=0.0):
        return Vector((x, y, roof_z(y) + dz))
    ang = math.atan2(OUT_Z[1] - OUT_Z[0], OUT_Y[1] - OUT_Y[0])
    tilt = _rx(ang)
    P.add('sheet', lambda bm: rounded_box((0.36, 0.3, 0.2), at(152.42, 0.86, 0.09), p=2.0, cuts=3, dents=((0.015, 6.0),), seed=4,
                                          mat=0, bm=bm, rot=tilt @ _rz(0.3)), size=0.35)
    P.add('rope', lambda bm: add_sphere(bm, at(152.44, 0.86, 0.22), 0.04, mat=0, seg=6, scale=(1.3, 1, 0.7)), size=0.1)
    P.add('bag', lambda bm: rounded_box((0.4, 0.2, 0.16), at(153.32, 0.82, 0.07), p=2.4, cuts=2, dents=((0.01, 6.0),), seed=5, mat=0,
                                        bm=bm, rot=tilt @ _rz(1.35)), size=0.35)
    P.add('shoe', lambda bm: rounded_box((0.48, 0.15, 0.34), at(152.87, 0.93, 0.17), p=6.0, cuts=2, seed=6, mat=0, bm=bm,
                                         rot=tilt @ _rz(0.04)), size=0.4)                     # a case stood against the wall
    lamp = at(153.36, 0.62, 0.0)
    P.add('dark', lambda bm: add_cyl(bm, lamp, lamp + Vector((0, 0, 0.16)), 0.05, 0.045, mat=0, seg=10), size=0.2)   # a hurricane lamp
    P.add('rope', lambda bm: add_torus(bm, lamp + Vector((0, 0, 0.2)), (1, 0, 0), 0.045, 0.004, mat=0, seg=10, rseg=3), size=0.1)
    k0 = at(152.36, 0.6, 0.0)
    P.add('paper', lambda bm: add_cyl(bm, k0, k0 + Vector((0, 0, 0.11)), 0.08, 0.06, mat=0, seg=10), size=0.2)          # a kettle
    P.add('dark', lambda bm: add_cyl(bm, k0 + Vector((0.07, 0, 0.03)), k0 + Vector((0.14, 0, 0.09)), 0.015, 0.008, mat=0, seg=5), size=0.1)
    # A rope from the case's handle round them both: they tied themselves to what they had.
    pts = [at(152.87, 0.86, 0.36), at(152.5, 0.78, 0.3), at(152.42, 0.66, 0.24), at(152.7, 0.58, 0.22), at(153.1, 0.6, 0.2),
           at(153.28, 0.72, 0.3), at(152.87, 0.86, 0.36)]
    P.add('rope', lambda bm: __import__('build_ration_hall').sweep(bm, pts, 0.008, seg=4), size=0.1)
    ob = painted_obj('D5RoofRemains', P, coll)
    report(ob, "DL-11: two together on the coal store's roof, among what they carried up")


# =====================================================================================================================
# DL-11: the seal's floor, C-114's name cards, its stair
# =====================================================================================================================

def build_seal_floor(coll):
    """The ledge's paving ends at the barricade's front (x 134.25) and the street's lane starts behind it (135.0): the
    crawl gap had nothing under it. A slab of the same paving, its sill worn, and grit swept against the posts."""
    x0, x1 = 134.2, 135.06
    bm = bmesh.new()
    add_box(bm, ((x0 + x1) / 2, 0.25, -0.15), (x1 - x0, 2.0, 0.3), mat=0)
    add_box(bm, (134.62, 0.25, -0.004), (0.012, 2.0, 0.012), mat=0)                       # a paving joint
    rnd = random.Random(6401)
    for k in range(9):
        s = rnd.uniform(0.02, 0.05)
        add_sphere(bm, (rnd.uniform(x0 + 0.05, x1 - 0.05), rnd.choice((rnd.uniform(-0.62, -0.42), rnd.uniform(0.4, 0.95))), s * 0.15), s,
                   mat=0, seg=6, scale=(1.3, 1.0, 0.45))
    ob = obj('D5SealFloor', bm, ('Concrete',), coll, sharp=40)
    report(ob, 'DL-11: the floor under the seal, where he crawls (top at 0)')


def remove_namecards():
    """C-114's name card (the child's sun, M and flowers) was on the door, on the facade and on the wall by the door:
    the door's stays."""
    remove('D5NameCard114Wall')
    home = bpy.data.objects.get('C114Home')
    if home is None:
        return
    names = [m_.name for m_ in home.data.materials]
    if 'D5NameCardMat' not in names:
        return
    idx = names.index('D5NameCardMat')
    delete_faces(home, lambda f, bm: f.material_index == idx, 'the name card by the door (D5NameCard114Out)')
    drop_unused_slots(home)


# The stair: up the living room's back wall from its right end to the upper floor (2.62) over the kitchen's end.
STAIR_X = (161.62, 163.32)                 # top (left) .. foot (right)
STAIR_Y = (0.36, 0.99)                     # its open side (the banister) .. the back wall
STAIR_TOP = 2.62
UPPER0 = 2.62


def build_stair114(coll):
    """A steep cottage stair: closed strings, treads and risers, its underside boarded (a cupboard under, a door), a
    banister on the open side with square balusters, a newel at the foot; it rises into the dark of the upper floor."""
    x_top, x_foot = STAIR_X
    y0, y1 = STAIR_Y
    n = 12
    rise = STAIR_TOP / n
    going = (x_foot - x_top) / n
    bm = bmesh.new()
    WD, PNT, DK = 0, 1, 2
    for k in range(n):
        x = x_foot - going * (k + 1)                       # tread k's front edge (stepping up toward -x)
        z = rise * (k + 1)
        uo.bx(bm, (x - 0.015, x + going), (y0 + 0.03, y1 - 0.01), (z - 0.024, z), WD, 0.004)                # the tread
        uo.bx(bm, (x + going - 0.012, x + going), (y0 + 0.03, y1 - 0.01), (z - rise, z - 0.02), PNT, 0.0)      # the riser
    # The strings, the open one stepping with the treads (as a plank along the slope).
    a = Vector((x_foot + 0.06, 0, 0.0))
    b = Vector((x_top - 0.04, 0, STAIR_TOP + 0.06))
    ang = math.atan2(b.z - a.z, a.x - b.x)
    ln = (b - a).length
    for yy in (y0 + 0.015, y1 - 0.005):
        Ms = Matrix.Translation(((a.x + b.x) / 2, yy, (a.z + b.z) / 2 + 0.02)) @ _ry(ang)
        add_box(bm, (0, 0, 0), (ln, 0.03, 0.24), mat=PNT, rot=Ms)
    # Boarded under (a cupboard), its little door.
    zt = lambda x: (x_foot - x) * STAIR_TOP / (x_foot - x_top) - 0.2          # noqa: E731
    xb = x_top + 0.35
    vs = [bm.verts.new(p_) for p_ in ((x_foot - 0.02, y0 + 0.02, 0.0), (xb, y0 + 0.02, 0.0), (xb, y0 + 0.02, zt(xb)))]
    bm.faces.new(vs[::-1]).material_index = PNT
    uo.bx(bm, (162.3, 162.82), (y0 + 0.004, y0 + 0.016), (0.04, 0.98), DK, 0.0)                           # the cupboard's door
    add_sphere(bm, (162.37, y0 - 0.0, 0.55), 0.016, mat=WD, seg=6)
    # The banister: a newel at the foot, the rail up the slope, square balusters, one to a tread.
    uo.bx(bm, (x_foot - 0.05, x_foot + 0.04), (y0 - 0.045, y0 + 0.045), (0.0, 1.08), WD, 0.008)
    add_sphere(bm, (x_foot - 0.005, y0, 1.12), 0.045, mat=WD, seg=8)
    r0 = Vector((x_foot - 0.005, y0, 0.98))
    r1 = Vector((x_top, y0, STAIR_TOP + 0.9))
    add_cyl(bm, r0, r1, 0.025, seg=6, mat=WD)
    for k in range(1, n):
        x = x_foot - going * (k + 0.5)
        z = rise * (k + 1)
        t = (x_foot - x) / (x_foot - x_top)
        zr = r0.z + (r1.z - r0.z) * t
        uo.bx(bm, (x - 0.014, x + 0.014), (y0 - 0.014, y0 + 0.014), (z, zr), WD, 0.0)
    ob = obj('C114Stair', bm, ('CrateWood', 'LivingPaint', 'DustyDark'), coll, sharp=40)
    report(ob, "DL-11: C-114's stair up to the parents' rooms, along the living room's back wall")


# =====================================================================================================================
# Entry points
# =====================================================================================================================

def build_set(dl01, m, coll):
    bpy.context.view_layer.update()
    # DL-10
    remove('UOHandMarks')
    rebuild_belongings(coll)
    trim_dropped()
    build_queue(coll)
    # DL-11
    strip_drowning()
    build_raft(coll)
    build_lair(coll)
    build_outshot(coll)
    build_roof_remains(coll)
    build_seal_floor(coll)
    remove_namecards()
    build_stair114(coll)


def add_clips(dl01, arm):
    pass
