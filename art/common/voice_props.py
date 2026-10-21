"""Shared prop builders for the refuge's voices (docs/audio_audit.md, docs/voice_script.md): the voice-card player, the
wall tannoy, a loose voice card and a child's music box. Built from the d17 primitives, gathered by material so callers
merge them into their own set pieces.

API (stable: other agents build on it; new names and options may be added, these keep working)
------------------------------------------------------------------------------------------------
    import sys; sys.path.insert(0, '<repo>/art/common')
    import voice_props as VP

    Targets. Every builder adds its geometry to a target T, through the 4x4 Matrix M (None: identity):
      - VP.Kit(): one bmesh with a 'UVMap' layer and its material list (T('Name') -> slot index, T.bm).
        K.obj(name, coll, origin=None, sharp=35) writes it out as one object (origin: a world point to put the
        object's origin at, the geometry kept where it is); K.mesh(name) as mesh data; K.tris() its triangle count.
      - anything shaped like art/pass6/build_ending_secrets.Batch (callable: name -> slot index, and .bm): the same;
      - a dict {material name: bmesh} or art/pass3 build_ration_hall.Parts (T[name] -> bmesh): one bmesh per
        material, created on demand (a dict via setdefault).
      Parts are closed and wound outward; a mirror in M (negative determinant) is handled.

    VP.xform(loc=(0, 0, 0), turn=0.0, scale=1.0) -> Matrix   (turn: degrees about z)

    info = VP.card_player(T, M=None, lid='closed', horn=35.0, card=True, crank=True, pose='upright', crank_angle=0.0)
        The voice-card player: a wooden box 0.22 x 0.16 x 0.12 on four bun feet (0.148 to its top), a brass horn about
        0.25 long rising from its back right corner and flaring out (the silhouette: a gramophone), a hand crank on its
        right side (+x; the handle worn bright, HandledBrass), and a slot across the top's front with a thin tin card
        standing half in it (card=False: the slot empty).
          lid    'closed' | 'open' (the lid over the top's back left stands up, hinged at its back edge, the dark
                 works and a brass drum showing) | 'off' (gone: the works showing).
          horn   the bell's heading in degrees: 0 toward -y (the front), +90 toward +x, -90 toward -x.
          crank  True: built in; False: left off (build it apart with VP.crank, for an object the game turns).
          crank_angle  degrees the crank's arm is turned about its axis from hanging straight down (+ toward -y).
          pose   'upright' | 'tipped': fallen onto its left side (-x down) and set on the floor (lowest point z 0
                 in its frame); with horn=90 the horn then points up out of a heap.
        Returns a dict of world points/vectors: 'crank_pivot', 'crank_axis' (unit), 'card' (the card's centre),
        'slot', 'top' (the top's centre), 'mouth' (the horn bell's centre), 'height' (the highest z).
    info = VP.crank(T, M=None, angle=0.0)
        The crank alone, in its own frame: the origin on its axis at the box's side face, the axis local +x (it turns
        about x), the arm hanging down (-z) at angle 0. Use with M = Translation(info['crank_pivot']) @ the player's
        rotation for a separate object (origin the pivot: rotate it about the player's local x).
    info = VP.tannoy(T, M=None, tilt=20.0, aim=0.0, conduit=0.6, conduit_dir=90.0, cable=True)
        A wall horn speaker, period institutional: a bolted wall plate, a bracket arm out from the wall with a strut,
        the driver can and a grey-green enamelled horn 0.3 long, its mouth 0.27 across with a rolled lip, dark inside;
        a steel conduit from a junction box up (or along) the wall and a short cable loop to the driver.
        Frame: the origin is the mount point ON the wall's face; the wall lies behind, at +y (the horn comes out
        toward -y, the camera); z up. tilt: degrees the horn points down; aim: degrees it turns about z
        (+ toward +x). conduit: metres of conduit; conduit_dir: its heading in the wall's plane in degrees
        (90 up, 0 toward +x, 180 toward -x). Returns 'mouth' (the horn mouth's centre), 'axis', 'mount'.
    info = VP.card(T, M=None, sleeve=True, out=0.35, upright=False, label=True)
        A loose voice card: a thin tin disc 0.12 across with a paper centre label, in a brown paper sleeve 0.135
        square with a small address label; `out`: how far the disc has slid out of the sleeve's +x edge (0 .. 0.9 of
        its diameter). Lying flat, the origin under the sleeve's centre (it is 0.004 thick). upright=True: stood on
        its edge in the xz plane, its face toward -y (on a shelf, against a wall at +y), the origin under its bottom edge.
        Returns 'centre' (the disc's centre), 'top' (its highest point).
    info = VP.music_box(T, M=None, lid=105.0, key=True)
        A child's music box: a little box 0.15 x 0.10 x 0.065, painted blue and chipped (ChildPaint), its lid open
        `lid` degrees on its back hinge (0: shut) with a felt lining, inside a brass cylinder over a steel comb with
        its teeth and a bed plate; a butterfly winding key on its right side (+x; HandledBrass). key=False leaves it
        off (VP.music_box_key builds it apart). Origin under its centre. Returns 'key_pivot', 'key_axis', 'top'.
    info = VP.music_box_key(T, M=None, angle=0.0)
        The key alone: origin on its axis at the box's side face, turning about local +x.

    me = VP.mesh(kind, name=None, **opts)    kind: 'card_player' | 'tannoy' | 'card' | 'music_box'
        The prop alone as a bpy Mesh, its origin the prop's own (cached on its arguments): for linked duplicates.
    ob = VP.place(me, loc, turn=0.0, coll=None, name=None)
    VP.material(name)                         the scene's material of that name, or the game table's fallback.
    VP.MATERIALS                              every material these props may use.
    VP.EXTENT[kind] -> (x0, x1, y0, y1, z0, z1): the rough local bounds of the default prop.

Materials (all in index.html's tables except TannoyEnamel, new: WORN, below):
    player:    CrateWood (the box), PigeonWood (plinth, moulding, lid, feet), Brass (horn, slot, works), HandledBrass
               (the crank's handle), DarkMetal (the slot, the works' well, the crank's arm), HandWorn (the tin card),
               ParcelPaper (the card's label)
    tannoy:    TannoyEnamel (new), DepotSteel (plate, bracket, conduit), DarkMetal (inside the horn), Cable
    card:      HandWorn (the tin), ParcelPaper (the sleeve), LetterPaper (the labels)
    music box: ChildPaint (the box), ToyFabric (its lining), Brass (cylinder, bed plate), HandWorn (the comb),
               HandledBrass (the key)
    TannoyEnamel (game WORN): { base: [.2, .24, .21], dirt: [.09, .1, .085], chip: [.05, .048, .042], rough: .45,
               chipRough: .7, metal: .1, grime: 4, chipScale: 30, chipAmt: .68, dust: [.16, .16, .14], dustAmt: .5,
               streak: .6 }

Triangles (default options): card_player ~2.9k (its crank ~0.3k of that), tannoy ~2.3k, card ~0.4k, music_box ~1.4k.
The tannoy reads best turned (aim +-35..60): head-on to the camera its horn is only a ring.

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y. Game (x, y, z) = (x, z, -y).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
for _d in ('d17',):
    _p = os.path.join(HERE, '..', _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

from build_d17 import add_box, add_cyl, add_sphere, rounded_box, worn_material, simple_material  # noqa: E402

V = Vector

# =====================================================================================================================
# Materials
# =====================================================================================================================

NEW_WORN = {
    # Period institutional enamel, grey-green, gone chalky; chipped to dark iron at the rim.
    'TannoyEnamel': dict(base=(0.20, 0.24, 0.21), dirt=(0.09, 0.10, 0.085), chip=(0.05, 0.048, 0.042), rough=0.45,
                         chip_rough=0.7, metallic=0.1, dust=(0.16, 0.16, 0.14), grime_scale=4.0, chip_scale=30.0,
                         chip_amount=0.68, dust_amount=0.5, streaks=0.6),
}
# Fall-backs for a lone run, matching index.html's tables (the full build already has them).
KNOWN_WORN = {
    'CrateWood': dict(base=(.18, .12, .07), dirt=(.08, .055, .035), chip=(.25, .19, .12), rough=.85, chip_rough=.8, metallic=0,
                      grime_scale=6, chip_scale=30, chip_amount=.75, streaks=.6),
    'PigeonWood': dict(base=(.12, .085, .055), dirt=(.06, .045, .03), chip=(.2, .15, .1), rough=.85, chip_rough=.8, metallic=0,
                       dust=(.1, .09, .08), grime_scale=6, chip_scale=30, chip_amount=.75, dust_amount=.6),
    'HandledBrass': dict(base=(.2, .14, .06), dirt=(.08, .06, .03), chip=(.62, .46, .2), rough=.5, chip_rough=.2, metallic=.85,
                         dust=(.12, .1, .07), grime_scale=8, chip_scale=26, chip_amount=.5, dust_amount=.2),
    'DarkMetal': dict(base=(.017, .016, .014), dirt=(.03, .024, .016), chip=(.075, .068, .055), rough=.72, chip_rough=.45,
                      metallic=.25, dust=(.075, .072, .062), grime_scale=5, chip_scale=34, chip_amount=.78, dust_amount=.7),
    'HandWorn': dict(base=(.46, .44, .39), dirt=(.2, .18, .15), chip=(.62, .6, .55), rough=.35, chip_rough=.3, metallic=.3,
                     grime_scale=22, chip_scale=60, chip_amount=.72, streaks=.2),
    'ParcelPaper': dict(base=(.36, .27, .17), dirt=(.2, .15, .09), chip=(.45, .38, .28), rough=.85, chip_rough=.8, metallic=0,
                        grime_scale=30, chip_scale=80, chip_amount=.8),
    'LetterPaper': dict(base=(.55, .52, .45), dirt=(.3, .27, .2), chip=(.62, .6, .55), rough=.9, chip_rough=.9, metallic=0,
                        dust=(.5, .48, .42), grime_scale=18, chip_scale=40, chip_amount=.8, dust_amount=.5),
    'DepotSteel': dict(base=(.05, .052, .05), dirt=(.05, .03, .018), chip=(.16, .15, .13), rough=.6, chip_rough=.4, metallic=.6,
                       dust=(.09, .085, .075), grime_scale=6, chip_scale=40, chip_amount=.74, dust_amount=.6),
    'ChildPaint': dict(base=(.12, .24, .42), dirt=(.06, .09, .12), chip=(.20, .14, .08), rough=.6, chip_rough=.8, metallic=0,
                       grime_scale=8, chip_scale=40, chip_amount=.7),
    'ToyFabric': dict(base=(.36, .33, .30), dirt=(.18, .15, .12), chip=(.42, .40, .36), rough=.95, chip_rough=.95, metallic=0,
                      grime_scale=20, chip_scale=60, chip_amount=.8),
}
KNOWN_PLAIN = {
    'Brass': ((0.45, 0.32, 0.12), 0.45, 0.8),
    'Cable': ((0.014, 0.013, 0.012), 0.55, 0.0),
}
MATERIALS = ('CrateWood', 'PigeonWood', 'Brass', 'HandledBrass', 'DarkMetal', 'HandWorn', 'ParcelPaper', 'LetterPaper',
             'TannoyEnamel', 'DepotSteel', 'Cable', 'ChildPaint', 'ToyFabric')


def material(name):
    mt = bpy.data.materials.get(name)
    if mt is not None:
        return mt
    if name in NEW_WORN:
        return worn_material(name, **NEW_WORN[name])
    if name in KNOWN_WORN:
        return worn_material(name, **KNOWN_WORN[name])
    if name in KNOWN_PLAIN:
        c, r, mtl = KNOWN_PLAIN[name]
        return simple_material(name, c, r, metallic=mtl)
    raise KeyError(name)


# =====================================================================================================================
# Targets
# =====================================================================================================================

def _merge_bm(dst, src):
    me = bpy.data.meshes.new('_vp_tmp')
    src.to_mesh(me)
    src.free()
    dst.from_mesh(me)
    bpy.data.meshes.remove(me)


class Kit:
    """One bmesh (with a UV layer) and its material list: a prop, or a set piece's props, merged."""
    def __init__(self):
        self.bm = bmesh.new()
        self.uv = self.bm.loops.layers.uv.new('UVMap')
        self.mats = []

    def __call__(self, name):
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def tris(self):
        return sum(len(f.verts) - 2 for f in self.bm.faces)

    def _write(self, name, origin):
        if origin is not None:
            bmesh.ops.translate(self.bm, vec=-V(origin), verts=self.bm.verts[:])
        me = bpy.data.meshes.new(name)
        self.bm.to_mesh(me)
        self.bm.free()
        for n in self.mats:
            me.materials.append(material(n))
        me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
        me.set_sharp_from_angle(angle=math.radians(35))
        return me

    def mesh(self, name, origin=None):
        return self._write(name, origin)

    def obj(self, name, coll, origin=None, sharp=35):
        old = bpy.data.objects.get(name)
        if old is not None:
            bpy.data.objects.remove(old, do_unlink=True)
        me = self._write(name, origin)
        me.set_sharp_from_angle(angle=math.radians(sharp))
        ob = bpy.data.objects.new(name, me)
        if origin is not None:
            ob.location = V(origin)
        coll.objects.link(ob)
        return ob


class _Parts(dict):
    """A prop's geometry while it is built: one bmesh per material, in the prop's own frame."""
    def __missing__(self, key):
        self[key] = bmesh.new()
        return self[key]


def _emit(T, parts, M):
    """Move the parts through M into the target."""
    flip = M is not None and M.to_3x3().determinant() < 0
    for name, bm in parts.items():
        if not bm.verts:
            bm.free()
            continue
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
        if M is not None:
            bmesh.ops.transform(bm, matrix=M, verts=bm.verts[:])
            if flip:
                bmesh.ops.reverse_faces(bm, faces=bm.faces[:])
        if callable(T) and hasattr(T, 'bm') and not isinstance(T, dict):
            idx = T(name)
            for f in bm.faces:
                f.material_index = idx
            _merge_bm(T.bm, bm)
        else:
            if isinstance(T, dict):
                dst = T.setdefault(name, bmesh.new())
            else:
                dst = T[name]
            for f in bm.faces:
                f.material_index = 0
            _merge_bm(dst, bm)


def xform(loc=(0, 0, 0), turn=0.0, scale=1.0):
    M = Matrix.Translation(V(loc)) @ Matrix.Rotation(math.radians(turn), 4, 'Z')
    if scale != 1.0:
        M = M @ Matrix.Diagonal((scale, scale, scale, 1.0))
    return M


def _M(M):
    return Matrix.Identity(4) if M is None else M


def _pt(M, p):
    return _M(M) @ V(p)


def _dirv(M, d):
    return (_M(M).to_3x3() @ V(d)).normalized()


# =====================================================================================================================
# Geometry helpers
# =====================================================================================================================

def _perp(t):
    a = V((0, 0, 1)) if abs(t.z) < 0.9 else V((1, 0, 0))
    return t.cross(a).normalized()


def _frames(pts):
    """Tangents and parallel-transported normals along a path."""
    n = len(pts)
    ts = [(pts[min(n - 1, i + 1)] - pts[max(0, i - 1)]).normalized() for i in range(n)]
    nrm = _perp(ts[0])
    out = []
    for t in ts:
        nrm = (nrm - t * nrm.dot(t)).normalized()
        out.append((t, nrm, t.cross(nrm)))
    return out


def _horn(bm, pts, radii, seg=18, wall=0.0025, petals=0, petal_amp=0.0, lip=0.0):
    """A thin-walled flaring horn along pts: an outer skin, an inner skin, the lip rolled between them at the mouth and
    the throat closed. petals: scallops round the bell (the seams of a gramophone horn's panels), growing toward the
    mouth. lip: a rolled bead's radius at the mouth (0: a plain edge). Returns (outer rings, inner rings)."""
    fr = _frames(pts)
    n = len(pts)
    outer, inner = [], []
    for i, (p, (t, nr, bi)) in enumerate(zip(pts, fr)):
        r = radii[i]
        g = (i / (n - 1)) ** 3
        ro, ri = [], []
        for k in range(seg):
            a = 2 * math.pi * k / seg
            s = 1.0 + petal_amp * g * math.cos(petals * a) if petals else 1.0
            d = nr * math.cos(a) + bi * math.sin(a)
            ro.append(bm.verts.new(p + d * r * s))
            ri.append(bm.verts.new(p + d * max(0.001, r * s - wall)))
        outer.append(ro)
        inner.append(ri)
    for i in range(n - 1):
        a, b = outer[i], outer[i + 1]
        c, d = inner[i], inner[i + 1]
        for k in range(seg):
            k1 = (k + 1) % seg
            bm.faces.new((a[k], a[k1], b[k1], b[k]))
            bm.faces.new((c[k], d[k], d[k1], c[k1]))
    # the mouth: a lip (a rolled bead) or a flat edge between the skins
    lo, li = outer[-1], inner[-1]
    if lip > 0:
        t = fr[-1][0]
        steps = 4
        prev = lo
        for j in range(1, steps):
            ang = math.pi * j / steps
            ring = []
            for k in range(seg):
                ctr = (lo[k].co + li[k].co) / 2
                rad = (lo[k].co - ctr)
                ring.append(bm.verts.new(ctr + rad * math.cos(ang) + t * (lip * math.sin(ang))
                                         + rad.normalized() * lip * math.sin(ang) * 0.6))
            for k in range(seg):
                k1 = (k + 1) % seg
                bm.faces.new((prev[k], prev[k1], ring[k1], ring[k]))
            prev = ring
        for k in range(seg):
            k1 = (k + 1) % seg
            bm.faces.new((prev[k], prev[k1], li[k1], li[k]))
    else:
        for k in range(seg):
            k1 = (k + 1) % seg
            bm.faces.new((lo[k], lo[k1], li[k1], li[k]))
    # the throat: the skins closed together
    for k in range(seg):
        k1 = (k + 1) % seg
        bm.faces.new((outer[0][k], inner[0][k], inner[0][k1], outer[0][k1]))
    return outer, inner


def _bezier(p0, p1, p2, n):
    p0, p1, p2 = V(p0), V(p1), V(p2)
    return [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2 for t in (i / (n - 1) for i in range(n))]


def _box(bm, x0, x1, y0, y1, z0, z1, rot=None):
    add_box(bm, ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), (x1 - x0, y1 - y0, z1 - z0), mat=0, rot=rot)


def _rbox(bm, x0, x1, y0, y1, z0, z1, p=8.0, cuts=3, rot=None, dents=(), seed=0.0):
    rounded_box((x1 - x0, y1 - y0, z1 - z0), ((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2), p=p, cuts=cuts, mat=0,
                bm=bm, rot=rot, dents=dents, seed=seed)


def _disc(bm, c, axis, r, thick, seg=24):
    c, axis = V(c), V(axis).normalized()
    add_cyl(bm, c - axis * thick / 2, c + axis * thick / 2, r, mat=0, seg=seg)


def _bake(parts, M):
    """Apply M to every part in place (for building a sub-piece at an angle inside the prop's frame)."""
    for bm in parts.values():
        bmesh.ops.transform(bm, matrix=M, verts=bm.verts[:])


# =====================================================================================================================
# The voice-card player
# =====================================================================================================================

P_W, P_D = 0.22, 0.16                   # the box
P_FOOT = 0.022                          # the feet's height
P_TOP = 0.148                           # its top
P_SLOT_Y = -0.045                       # the slot across the top's front
P_CRANK = V((0.11, 0.0, 0.088))         # the crank's pivot on the right side face
P_NECK = V((0.07, 0.05, P_TOP))         # where the horn's neck leaves the top
CARD_R = 0.06


def _crank_parts(parts, angle):
    """The crank in its own frame (origin the pivot on the side face, axis +x, the arm hanging -z at angle 0)."""
    st, br, hb = parts['DarkMetal'], parts['Brass'], parts['HandledBrass']
    _disc(br, (0.0015, 0, 0), (1, 0, 0), 0.016, 0.003, seg=14)                       # the escutcheon
    add_cyl(st, (0.0, 0, 0), (0.024, 0, 0), 0.0055, mat=0, seg=8)                     # the shaft
    a = math.radians(angle)
    d = V((0.0, -math.sin(a), -math.cos(a)))
    L = 0.058
    add_cyl(st, V((0.024, 0, 0)) - d * 0.006, V((0.024, 0, 0)) + d * L, 0.0075, 0.0055, mat=0, seg=8)   # the arm
    add_sphere(st, (0.024, 0, 0), 0.009, mat=0, seg=8, scale=(0.7, 1, 1))              # its boss
    end = V((0.024, 0, 0)) + d * L
    add_cyl(hb, end + V((0.002, 0, 0)), end + V((0.03, 0, 0)), 0.0075, 0.0085, mat=0, seg=10)   # the handle, worn bright
    add_sphere(hb, end + V((0.031, 0, 0)), 0.0088, mat=0, seg=10, scale=(0.6, 1, 1))
    return end


def crank(T, M=None, angle=0.0):
    parts = _Parts()
    _crank_parts(parts, angle)
    _emit(T, parts, M)
    return {'pivot': _pt(M, (0, 0, 0)), 'axis': _dirv(M, (1, 0, 0))}


def _player_parts(lid, horn, card, with_crank, crank_angle):
    parts = _Parts()
    wd, dk, br, st = parts['CrateWood'], parts['PigeonWood'], parts['Brass'], parts['DarkMetal']
    hw, w2 = P_W / 2, P_D / 2
    # Bun feet and the plinth.
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_sphere(dk, (sx * (hw - 0.02), sy * (w2 - 0.02), 0.012), 0.014, mat=0, seg=8, scale=(1, 1, 0.85))
    _rbox(dk, -hw - 0.006, hw + 0.006, -w2 - 0.006, w2 + 0.006, P_FOOT - 0.002, P_FOOT + 0.016, p=6, cuts=2)
    # The case, its top moulding and a sunk front panel.
    _rbox(wd, -hw, hw, -w2, w2, P_FOOT + 0.014, P_TOP - 0.01, p=10, cuts=3, dents=((0.0008, 30.0),), seed=1.3)
    _rbox(dk, -hw - 0.004, hw + 0.004, -w2 - 0.004, w2 + 0.004, P_TOP - 0.013, P_TOP, p=6, cuts=2)
    _rbox(dk, -0.085, 0.085, -w2 - 0.004, -w2 + 0.002, 0.056, 0.112, p=6, cuts=1)
    _rbox(wd, -0.074, 0.074, -w2 - 0.0055, -w2, 0.064, 0.104, p=6, cuts=1)
    add_sphere(br, (0.0, -w2 - 0.006, 0.084), 0.006, mat=0, seg=8, scale=(1, 0.5, 1))  # a brass stud on the panel
    # The slot across the top's front: a brass bezel round a dark slit.
    sy = P_SLOT_Y
    _box(st, -0.066, 0.066, sy - 0.005, sy + 0.005, P_TOP, P_TOP + 0.002)
    for a, b, c, d in ((-0.074, 0.074, sy - 0.012, sy - 0.005), (-0.074, 0.074, sy + 0.005, sy + 0.012),
                       (-0.074, -0.066, sy - 0.005, sy + 0.005), (0.066, 0.074, sy - 0.005, sy + 0.005)):
        _box(br, a, b, c, d, P_TOP, P_TOP + 0.004)
    if card:
        c = V((0.0, sy, P_TOP + 0.004))
        _disc(parts['HandWorn'], c, (0, 1, 0), CARD_R, 0.0018, seg=28)
        _disc(parts['ParcelPaper'], c, (0, 1, 0), 0.021, 0.0026, seg=16)
    # The lid over the top's back left (hinged at its back edge), or the works where it is open.
    lx0, lx1, ly0, ly1 = -0.098, 0.03, -0.028, 0.072
    if lid in ('open', 'off'):
        _box(st, lx0 + 0.006, lx1 - 0.006, ly0 + 0.006, ly1 - 0.006, P_TOP, P_TOP + 0.0015)
        add_cyl(br, (-0.034, 0.022, P_TOP), (-0.034, 0.022, P_TOP + 0.009), 0.03, mat=0, seg=16)      # the drum
        add_cyl(br, (-0.034, 0.022, P_TOP + 0.009), (-0.034, 0.022, P_TOP + 0.02), 0.004, mat=0, seg=6)  # its spindle
        add_cyl(br, (0.008, 0.05, P_TOP + 0.012), (-0.02, 0.016, P_TOP + 0.012), 0.003, mat=0, seg=6)    # the reed arm
    if lid != 'off':
        lp = _Parts()
        _rbox(lp['PigeonWood'], lx0, lx1, ly0 - ly1, 0.0, 0.0, 0.009, p=14, cuts=2)
        add_sphere(lp['Brass'], ((lx0 + lx1) / 2, ly0 - ly1 + 0.008, 0.011), 0.005, mat=0, seg=8)   # its knob
        rot = Matrix.Rotation(math.radians(-102.0 if lid == 'open' else 0.0), 4, 'X')
        _bake(lp, Matrix.Translation((0, ly1, P_TOP)) @ rot)
        for k, bm in lp.items():
            _merge_bm(parts[k], bm)
    # The horn: a neck up out of the top's back right, then curving over and flaring toward `horn`.
    _rbox(br, P_NECK.x - 0.02, P_NECK.x + 0.02, P_NECK.y - 0.02, P_NECK.y + 0.02, P_TOP, P_TOP + 0.008, p=4, cuts=1)
    add_cyl(br, P_NECK, P_NECK + V((0, 0, 0.05)), 0.011, 0.01, mat=0, seg=10)
    add_sphere(br, P_NECK + V((0, 0, 0.05)), 0.014, mat=0, seg=10)
    h = math.radians(horn)
    d = V((math.sin(h), -math.cos(h), 0.0))
    p0 = P_NECK + V((0, 0, 0.05))
    pts = _bezier(p0, p0 + V((0, 0, 0.1)), p0 + d * 0.19 + V((0, 0, 0.15)), 13)
    radii = [0.0095 + 0.077 * (i / 12) ** 2.7 for i in range(13)]
    _horn(br, pts, radii, seg=18, wall=0.0022, petals=8, petal_amp=0.05, lip=0.003)
    # its stay: a thin rod from the top's back edge up to the horn's elbow
    add_cyl(st, (P_NECK.x - 0.05, w2 - 0.01, P_TOP), pts[5], 0.0025, mat=0, seg=5)
    mouth = pts[-1]
    if with_crank:
        cp = _Parts()
        _crank_parts(cp, crank_angle)
        _bake(cp, Matrix.Translation(P_CRANK))
        for k, bm in cp.items():
            _merge_bm(parts[k], bm)
    return parts, mouth


def _tip_matrix(parts):
    """Lay the player on its left side (-x down), resting on z 0."""
    R = Matrix.Rotation(math.radians(-90.0), 4, 'Y')
    lo = min((R @ v.co).z for bm in parts.values() for v in bm.verts)
    return Matrix.Translation((0, 0, -lo)) @ R


def card_player(T, M=None, lid='closed', horn=35.0, card=True, crank=True, pose='upright', crank_angle=0.0):
    parts, mouth = _player_parts(lid, horn, card, crank, crank_angle)
    L = Matrix.Identity(4)
    if pose == 'tipped':
        L = _tip_matrix(parts)
    hi = max((L @ v.co).z for bm in parts.values() for v in bm.verts)
    ML = _M(M) @ L
    _emit(T, parts, ML)
    return {'crank_pivot': ML @ P_CRANK, 'crank_axis': (ML.to_3x3() @ V((1, 0, 0))).normalized(),
            'card': ML @ V((0, P_SLOT_Y, P_TOP + 0.004)), 'slot': ML @ V((0, P_SLOT_Y, P_TOP)),
            'top': ML @ V((0, 0, P_TOP)), 'mouth': ML @ mouth, 'height': (_M(M) @ V((0, 0, hi))).z,
            'local': L}


# =====================================================================================================================
# The tannoy
# =====================================================================================================================

def tannoy(T, M=None, tilt=20.0, aim=0.0, conduit=0.6, conduit_dir=90.0, cable=True):
    parts = _Parts()
    en, sl, dk = parts['TannoyEnamel'], parts['DepotSteel'], parts['DarkMetal']
    # The wall plate, bolted, and a junction box over it.
    _rbox(sl, -0.055, 0.055, -0.012, 0.0, -0.08, 0.08, p=6, cuts=1)
    for bx in (-0.038, 0.038):
        for bz in (-0.062, 0.062):
            add_cyl(dk, (bx, -0.012, bz), (bx, -0.018, bz), 0.006, mat=0, seg=6)
    # The bracket: an arm out from the wall and a strut under it.
    arm_out = 0.17
    _box(sl, -0.012, 0.012, -arm_out - 0.01, -0.012, 0.035, 0.06)
    add_cyl(sl, (0, -0.014, -0.065), (0, -arm_out + 0.01, 0.04), 0.008, mat=0, seg=6)
    # The driver can, hung from the arm's end on a swivel, and the horn.
    a_t, a_y = math.radians(tilt), math.radians(aim)
    axis = V((math.sin(a_y) * math.cos(a_t), -math.cos(a_y) * math.cos(a_t), -math.sin(a_t)))
    piv = V((0, -arm_out, 0.035))
    add_cyl(sl, piv, piv + V((0, 0, -0.03)), 0.011, mat=0, seg=8)
    C = piv + V((0, 0, -0.085))
    can0, can1 = C - axis * 0.075, C + axis * 0.03
    add_cyl(en, can0, can1, 0.058, 0.062, mat=0, seg=16)
    add_sphere(en, can0, 0.058, mat=0, seg=14, scale=(1, 1, 1))     # its domed back
    # yoke: a strap over the can from the swivel
    add_cyl(sl, piv + V((0, 0, -0.03)), C + V((0, 0, 0.064)), 0.009, mat=0, seg=6)
    hp = [can1 + axis * (0.3 * i / 9) for i in range(10)]
    hr = [0.045 + 0.09 * (i / 9) ** 1.9 for i in range(10)]
    _horn(en, hp, hr, seg=18, wall=0.004, lip=0.007)
    # the horn's inside dark: an inner liner just within the inner skin, open to the mouth
    liner = bmesh.new()
    _horn(liner, hp[:-1:2], [r - 0.0045 for r in hr[:-1:2]], seg=18, wall=0.001, lip=0.0)
    _merge_bm(dk, liner)
    _disc(dk, can1 + axis * 0.004, axis, 0.04, 0.004, seg=14)    # the throat's grille
    mouth = hp[-1]
    # The conduit: from a junction box on the plate along the wall, and a cable loop down to the can.
    cd = math.radians(conduit_dir)
    u = V((math.cos(cd), 0.0, math.sin(cd)))
    jb = V((0.0, -0.02, 0.0)) + u * 0.11
    _rbox(sl, jb.x - 0.035, jb.x + 0.035, -0.04, 0.0, jb.z - 0.035, jb.z + 0.035, p=6, cuts=1)
    if conduit > 0:
        a = V((jb.x, -0.016, jb.z)) + u * 0.03
        b = a + u * conduit
        add_cyl(sl, a, b, 0.011, mat=0, seg=8)
        for k in range(1, int(conduit / 0.3) + 1):                   # saddles along it
            p = a + u * min(conduit - 0.02, 0.3 * k - 0.1)
            _box(sl, p.x - 0.018 * abs(u.z) - 0.006 * abs(u.x), p.x + 0.018 * abs(u.z) + 0.006 * abs(u.x), -0.006, 0.0,
                 p.z - 0.018 * abs(u.x) - 0.006 * abs(u.z), p.z + 0.018 * abs(u.x) + 0.006 * abs(u.z))
    if cable:
        s = V((jb.x, -0.04, jb.z - 0.02))
        e = can0 + V((0, 0.0, -0.01))
        mid = (s + e) / 2 + V((0, -0.02, -0.08))
        pts = _bezier(s, mid, e, 8)
        cb = parts['Cable']
        for p, q in zip(pts, pts[1:]):
            add_cyl(cb, p, q, 0.006, mat=0, seg=6)
            add_sphere(cb, q, 0.006, mat=0, seg=6)
    _emit(T, parts, M)
    return {'mouth': _pt(M, mouth), 'axis': _dirv(M, axis), 'mount': _pt(M, (0, 0, 0))}


# =====================================================================================================================
# A loose voice card
# =====================================================================================================================

def _card_parts(sleeve, out, label):
    parts = _Parts()
    S = 0.135
    th = 0.004
    if sleeve:
        _rbox(parts['ParcelPaper'], -S / 2, S / 2, -S / 2, S / 2, 0.0, th, p=10, cuts=3, dents=((0.0006, 40.0),), seed=2.0)
        if label:
            _box(parts['LetterPaper'], -0.05, 0.005, -0.045, -0.015, th, th + 0.0006)       # the address label
            _box(parts['LetterPaper'], 0.035, 0.055, 0.03, 0.054, th, th + 0.0006)          # the stamp
    c = V((out * 2 * CARD_R, 0.0, th / 2 if sleeve else 0.0009))
    _disc(parts['HandWorn'], c, (0, 0, 1), CARD_R, 0.0016, seg=28)
    _disc(parts['ParcelPaper'], c, (0, 0, 1), 0.021, 0.0024, seg=16)
    return parts, c


def card(T, M=None, sleeve=True, out=0.35, upright=False, label=True):
    parts, c = _card_parts(sleeve, out, label)
    L = Matrix.Identity(4)
    if upright:
        # stood on edge in the xz plane: its lowest point at z 0, its face toward -y
        L = Matrix.Rotation(math.radians(90.0), 4, 'X')
        lo = min((L @ v.co).z for bm in parts.values() for v in bm.verts)
        L = Matrix.Translation((0, 0.004, -lo)) @ L
    hi = max((L @ v.co).z for bm in parts.values() for v in bm.verts)
    ML = _M(M) @ L
    _emit(T, parts, ML)
    return {'centre': ML @ c, 'top': (_M(M) @ V((0, 0, hi))).z}


# =====================================================================================================================
# The music box
# =====================================================================================================================

MB = (0.15, 0.10, 0.065)
MB_KEY = V((MB[0] / 2, 0.0, 0.03))


def _key_parts(parts, angle):
    hb = parts['HandledBrass']
    add_cyl(hb, (0, 0, 0), (0.014, 0, 0), 0.0035, mat=0, seg=6)
    a = math.radians(angle)
    for sd in (1, -1):
        d = V((0, math.sin(a), math.cos(a))) * sd
        add_sphere(hb, V((0.017, 0, 0)) + d * 0.011, 0.011, mat=0, seg=10, scale=(0.25, 1, 1))
    add_sphere(hb, (0.016, 0, 0), 0.005, mat=0, seg=8)


def music_box_key(T, M=None, angle=0.0):
    parts = _Parts()
    _key_parts(parts, angle)
    _emit(T, parts, M)
    return {'pivot': _pt(M, (0, 0, 0)), 'axis': _dirv(M, (1, 0, 0))}


def music_box(T, M=None, lid=105.0, key=True, key_angle=20.0):
    parts = _Parts()
    pb, fb, br, hw = parts['ChildPaint'], parts['ToyFabric'], parts['Brass'], parts['HandWorn']
    w, d, h = MB
    t = 0.008
    # the box: a floor and four walls (open at the top), a moulded foot round it
    _rbox(pb, -w / 2, w / 2, -d / 2, d / 2, 0.0, t, p=8, cuts=1)
    for x0, x1, y0, y1 in ((-w / 2, w / 2, -d / 2, -d / 2 + t), (-w / 2, w / 2, d / 2 - t, d / 2),
                           (-w / 2, -w / 2 + t, -d / 2, d / 2), (w / 2 - t, w / 2, -d / 2, d / 2)):
        _rbox(pb, x0, x1, y0, y1, 0.0, h, p=10, cuts=1)
    _rbox(pb, -w / 2 - 0.004, w / 2 + 0.004, -d / 2 - 0.004, d / 2 + 0.004, 0.0, 0.008, p=6, cuts=1)
    # the felt floor inside and the works
    _box(fb, -w / 2 + t, w / 2 - t, -d / 2 + t, d / 2 - t, t, t + 0.002)
    _box(br, -0.055, 0.045, -0.032, 0.03, t + 0.002, t + 0.006)                        # the bed plate
    for xx in (-0.045, 0.035):                                                           # the cylinder's cheeks
        _box(br, xx - 0.003, xx + 0.003, 0.0, 0.018, t + 0.006, 0.04)
    add_cyl(br, (-0.045, 0.01, 0.031), (0.035, 0.01, 0.031), 0.012, mat=0, seg=14)      # the pinned cylinder
    for k in range(9):                                                                   # pins (bright dots)
        xx = -0.038 + k * 0.0085
        aa = k * 2.1
        add_sphere(hw, (xx, 0.01 - 0.012 * math.cos(aa), 0.031 + 0.012 * math.sin(aa)), 0.0016, mat=0, seg=4)
    _box(hw, -0.044, 0.034, -0.03, -0.018, t + 0.006, t + 0.012)                         # the comb's base
    for k in range(14):                                                                  # and its teeth
        xx = -0.042 + k * 0.0057
        _box(hw, xx - 0.0018, xx + 0.0018, -0.018, -0.004 - 0.0004 * k, t + 0.009, t + 0.011)
    # the governor's little fan at the right
    add_cyl(br, (0.04, -0.02, t + 0.006), (0.04, -0.02, 0.03), 0.002, mat=0, seg=5)
    _box(br, 0.034, 0.046, -0.021, -0.019, 0.026, 0.034)
    # the lid, hinged on the back edge, felt inside
    lp = _Parts()
    _rbox(lp['ChildPaint'], -w / 2 - 0.002, w / 2 + 0.002, -d - 0.002, 0.0, 0.0, 0.012, p=8, cuts=2)
    _box(lp['ToyFabric'], -w / 2 + 0.008, w / 2 - 0.008, -d + 0.008, -0.008, -0.0015, 0.0005)
    _bake(lp, Matrix.Translation((0, d / 2, h)) @ Matrix.Rotation(math.radians(-lid), 4, 'X'))
    for k, bm in lp.items():
        _merge_bm(parts[k], bm)
    # brass hinges
    for xx in (-0.045, 0.045):
        add_cyl(br, (xx - 0.012, d / 2 + 0.001, h), (xx + 0.012, d / 2 + 0.001, h), 0.003, mat=0, seg=6)
    if key:
        kp = _Parts()
        _key_parts(kp, key_angle)
        _bake(kp, Matrix.Translation(MB_KEY))
        for k, bm in kp.items():
            _merge_bm(parts[k], bm)
    _emit(T, parts, M)
    return {'key_pivot': _pt(M, MB_KEY), 'key_axis': _dirv(M, (1, 0, 0)), 'top': _pt(M, (0, 0, h))}


# =====================================================================================================================
# Linked duplicates
# =====================================================================================================================

BUILDERS = {'card_player': card_player, 'tannoy': tannoy, 'card': card, 'music_box': music_box}
EXTENT = {
    'card_player': (-0.12, 0.2, -0.2, 0.09, 0.0, 0.48),
    'tannoy': (-0.16, 0.16, -0.5, 0.0, -0.25, 0.75),
    'card': (-0.07, 0.115, -0.07, 0.07, 0.0, 0.005),
    'music_box': (-0.08, 0.1, -0.06, 0.08, 0.0, 0.17),
}
_CACHE = {}


def mesh(kind, name=None, **opts):
    key = (kind, tuple(sorted(opts.items())))
    me = _CACHE.get(key)
    if me is not None and me.name in bpy.data.meshes:
        return me
    K = Kit()
    BUILDERS[kind](K, None, **opts)
    me = K.mesh(name or ('VP_' + kind))
    _CACHE[key] = me
    return me


def place(me, loc, turn=0.0, coll=None, name=None):
    ob = bpy.data.objects.new(name or me.name, me)
    ob.location = V(loc)
    ob.rotation_euler = (0.0, 0.0, math.radians(turn))
    (coll or bpy.context.scene.collection).objects.link(ob)
    return ob
