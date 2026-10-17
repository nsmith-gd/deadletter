"""D-17: procedural model, rig and walk cycle, rendered with Cycles.

Everything (geometry, materials, rig, animation, lighting, cameras) is generated
from this file so the result can be rebuilt and tuned from source.

Usage (Blender as a Python module, `pip install bpy`):
    python build_d17.py --shot turnaround --out out/turnaround
    python build_d17.py --shot hero       --out out/hero --blend d17_walk.blend
    python build_d17.py --shot sprites    --out out/sprites
    python build_d17.py --shot closeup    --out out/check --still 1 --samples 16

Conventions: metres, Z up, D-17 faces -Y in its rest pose, robot's left is +X.
Dimensions were measured from the front/side turnaround concept (0.71 m to the
top of the head).
"""
import argparse
import math
import os

import bpy  # must be imported before bmesh/mathutils
import bmesh
from mathutils import Matrix, Vector, noise

STEP = 20            # frames per step; a walk cycle is two steps (40 frames, 1.67 s)
CYCLE = 2 * STEP
SWING = 14           # frames a foot is in the air; the rest is a hesitant double support
STRIDE = 0.16        # metres a foot advances per step it takes (small, careful steps)
LIFT = 0.03          # swing height in metres
FEET_START = {'L': -STRIDE / 2, 'R': 0.0}
HERO_STEPS = 5       # four steps plus a closing half step, then a curious look
STOP_AT = (HERO_STEPS - 1) * STEP + SWING
HERO_FRAMES = STOP_AT + 46

# Material slot indices shared by every part.
(DARK, CREAM, GLOW, EYE, CABLE, GLASS, GLOW_DIM, CREAM_LIMB, BARE, ROD) = range(10)


# --------------------------------------------------------------------------
# Materials
# --------------------------------------------------------------------------

def _new_material(name):
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


def _ramp(nt, src, stops, interp='LINEAR'):
    node = nt.nodes.new('ShaderNodeValToRGB')
    node.color_ramp.interpolation = interp
    els = node.color_ramp.elements
    while len(els) < len(stops):
        els.new(0.5)
    for el, (pos, col) in zip(els, stops):
        el.position = pos
        el.color = col if len(col) == 4 else (*col, 1.0)
    nt.links.new(src, node.inputs['Fac'])
    return node.outputs['Color']


def _noise(nt, coords, scale, detail, rough=0.55, stretch=None):
    node = nt.nodes.new('ShaderNodeTexNoise')
    node.inputs['Scale'].default_value = scale
    node.inputs['Detail'].default_value = detail
    node.inputs['Roughness'].default_value = rough
    if stretch:
        vm = nt.nodes.new('ShaderNodeVectorMath')
        vm.operation = 'MULTIPLY'
        vm.inputs[1].default_value = stretch
        nt.links.new(coords, vm.inputs[0])
        coords = vm.outputs['Vector']
    nt.links.new(coords, node.inputs['Vector'])
    return node.outputs['Fac']


def _mix(nt, fac, a, b, blend='MIX'):
    node = nt.nodes.new('ShaderNodeMix')
    node.data_type = 'RGBA'
    node.blend_type = blend
    fac_in = next(s for s in node.inputs if s.name == 'Factor' and s.type == 'VALUE')
    a_in, b_in = [s for s in node.inputs if s.type == 'RGBA'][:2]
    for sock, val in ((fac_in, fac), (a_in, a), (b_in, b)):
        if isinstance(val, (int, float)):
            sock.default_value = val
        elif isinstance(val, tuple):
            sock.default_value = val if len(val) == 4 else (*val, 1.0)
        else:
            nt.links.new(val, sock)
    return next(s for s in node.outputs if s.type == 'RGBA')


def _math(nt, op, a, b):
    node = nt.nodes.new('ShaderNodeMath')
    node.operation = op
    for sock, val in zip(node.inputs, (a, b)):
        if isinstance(val, (int, float)):
            sock.default_value = val
        else:
            nt.links.new(val, sock)
    return node.outputs['Value']


def worn_material(name, base, dirt, chip, rough, chip_rough, metallic, dust=(0.10, 0.095, 0.08),
                  grime_scale=4.0, chip_scale=26.0, chip_amount=0.66, edge_wear=True,
                  streaks=0.5, dust_amount=0.6):
    """Hand-worn surface: blotchy grime, vertical streaks, paint chips, worn edges,
    cavity dirt and dust settling on upward-facing surfaces."""
    mat, nt, bsdf = _new_material(name)
    coords = nt.nodes.new('ShaderNodeTexCoord').outputs['Object']
    geo = nt.nodes.new('ShaderNodeNewGeometry')

    grime = _ramp(nt, _noise(nt, coords, grime_scale, 8, 0.6),
                  [(0.45, (0, 0, 0)), (0.66, (1, 1, 1))])
    streak = _ramp(nt, _noise(nt, coords, 9, 6, 0.6, stretch=(1.0, 1.0, 0.12)),
                   [(0.5, (0, 0, 0)), (0.7, (streaks, streaks, streaks))])
    grime = _math(nt, 'MAXIMUM', grime, streak)
    chips_raw = _noise(nt, coords, chip_scale, 5, 0.72)
    chips = _ramp(nt, chips_raw, [(chip_amount, (0, 0, 0)), (chip_amount + 0.015, (1, 1, 1))])
    mask = chips
    if edge_wear:
        edges = _ramp(nt, geo.outputs['Pointiness'], [(0.53, (0, 0, 0)), (0.6, (1, 1, 1))])
        broken = _ramp(nt, chips_raw, [(0.47, (0, 0, 0)), (0.55, (1, 1, 1))])
        mask = _math(nt, 'MAXIMUM', chips, _math(nt, 'MULTIPLY', edges, broken))

    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(geo.outputs['Normal'], sep.inputs['Vector'])
    up = _ramp(nt, sep.outputs['Z'], [(0.35, (0, 0, 0)), (0.9, (1, 1, 1))])
    dust_mask = _math(nt, 'MULTIPLY', up,
                      _ramp(nt, _noise(nt, coords, 14, 4), [(0.35, (0, 0, 0)), (0.7, (dust_amount,) * 3)]))

    ao = nt.nodes.new('ShaderNodeAmbientOcclusion')
    ao.inputs['Distance'].default_value = 0.035
    cavity = _ramp(nt, ao.outputs['AO'], [(0.0, (0.3, 0.28, 0.25)), (0.85, (1, 1, 1))])

    col = _mix(nt, grime, base, dirt)
    col = _mix(nt, dust_mask, col, dust)
    col = _mix(nt, mask, col, chip)
    col = _mix(nt, 1.0, col, cavity, 'MULTIPLY')
    nt.links.new(col, bsdf.inputs['Base Color'])

    rough_out = _math(nt, 'ADD', _math(nt, 'MULTIPLY', mask, chip_rough - rough), rough)
    rough_out = _math(nt, 'ADD', rough_out, _math(nt, 'MULTIPLY', dust_mask, 0.25))
    nt.links.new(rough_out, bsdf.inputs['Roughness'])
    bsdf.inputs['Metallic'].default_value = metallic

    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.45
    bump.inputs['Distance'].default_value = 0.0025
    height = _math(nt, 'ADD', _math(nt, 'MULTIPLY', mask, -0.7), _noise(nt, coords, 70, 3))
    height = _math(nt, 'ADD', height, _math(nt, 'MULTIPLY', _noise(nt, coords, 9, 4), 0.6))
    nt.links.new(height, bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], bsdf.inputs['Normal'])
    return mat


def emission_material(name, color, strength):
    mat, nt, bsdf = _new_material(name)
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Emission Color'].default_value = (*color, 1)
    bsdf.inputs['Emission Strength'].default_value = strength
    return mat


def simple_material(name, color, rough, metallic=0.0, transmission=0.0):
    mat, nt, bsdf = _new_material(name)
    bsdf.inputs['Base Color'].default_value = (*color, 1)
    bsdf.inputs['Roughness'].default_value = rough
    bsdf.inputs['Metallic'].default_value = metallic
    bsdf.inputs['Transmission Weight'].default_value = transmission
    return mat


def build_materials():
    return [
        worn_material('DarkMetal', base=(0.017, 0.016, 0.014), dirt=(0.03, 0.024, 0.016),
                      chip=(0.075, 0.068, 0.055), rough=0.72, chip_rough=0.45, metallic=0.25,
                      grime_scale=5, chip_scale=34, chip_amount=0.78, edge_wear=False,
                      streaks=0.4, dust=(0.075, 0.072, 0.062), dust_amount=0.7),
        worn_material('CreamPaint', base=(0.66, 0.58, 0.40), dirt=(0.36, 0.30, 0.19),
                      chip=(0.028, 0.025, 0.02), rough=0.78, chip_rough=0.5, metallic=0.0,
                      grime_scale=3.0, chip_scale=20, chip_amount=0.63, streaks=0.55,
                      dust=(0.62, 0.57, 0.45), dust_amount=0.3),
        emission_material('Glow', (1.0, 0.36, 0.08), 7.0),
        simple_material('EyeDark', (0.003, 0.003, 0.003), 0.3),
        simple_material('Cable', (0.014, 0.013, 0.012), 0.55),
        simple_material('Canister', (0.45, 0.48, 0.45), 0.4, transmission=0.8),
        emission_material('GlowDim', (0.85, 0.30, 0.08), 0.9),
        worn_material('CreamLimb', base=(0.62, 0.55, 0.38), dirt=(0.30, 0.25, 0.16),
                      chip=(0.03, 0.027, 0.022), rough=0.72, chip_rough=0.5, metallic=0.0,
                      grime_scale=14, chip_scale=55, chip_amount=0.66, edge_wear=False,
                      streaks=0.6, dust_amount=0.2),
        worn_material('BareMetal', base=(0.42, 0.40, 0.35), dirt=(0.2, 0.18, 0.14),
                      chip=(0.05, 0.045, 0.04), rough=0.5, chip_rough=0.6, metallic=0.6,
                      grime_scale=10, chip_scale=40, chip_amount=0.7, edge_wear=False),
        worn_material('RodMetal', base=(0.10, 0.092, 0.075), dirt=(0.05, 0.042, 0.03),
                      chip=(0.2, 0.18, 0.15), rough=0.5, chip_rough=0.4, metallic=0.7,
                      grime_scale=20, chip_scale=60, chip_amount=0.75, edge_wear=False,
                      streaks=0.7, dust_amount=0.2),
    ]


def floor_material():
    mat, nt, bsdf = _new_material('Floor')
    coords = nt.nodes.new('ShaderNodeTexCoord').outputs['Object']
    stains = _ramp(nt, _noise(nt, coords, 0.9, 6, 0.6), [(0.42, (0, 0, 0)), (0.62, (1, 1, 1))])
    speck = _noise(nt, coords, 30, 4, 0.6)
    col = _mix(nt, stains, (0.06, 0.066, 0.06), (0.035, 0.04, 0.036))
    col = _mix(nt, _ramp(nt, speck, [(0.55, (0, 0, 0)), (0.8, (0.2, 0.2, 0.2))]),
               col, (0.09, 0.09, 0.085))
    nt.links.new(col, bsdf.inputs['Base Color'])
    rough = _math(nt, 'ADD', _math(nt, 'MULTIPLY', stains, -0.25), 0.92)
    nt.links.new(rough, bsdf.inputs['Roughness'])
    bsdf.inputs['Specular IOR Level'].default_value = 0.0
    return mat


# --------------------------------------------------------------------------
# Geometry helpers (all parts are authored in world rest-pose coordinates)
# --------------------------------------------------------------------------

def _tag(verts, mat_index):
    faces = set()
    for v in verts:
        faces.update(v.link_faces)
    for f in faces:
        f.material_index = mat_index


def _fbm(p, octaves=3):
    return sum(noise.noise(p * (2 ** o)) / (2 ** o) for o in range(octaves))


def dent(verts, amp, freq, seed=0.0, octaves=3):
    """Push vertices along their normals with fractal noise: hammered, hand-made surfaces."""
    off = Vector((seed * 17.31, seed * 5.13, seed * 9.77))
    for v in verts:
        v.co += v.normal * _fbm(v.co * freq + off, octaves) * amp


def add_cyl(bm, p1, p2, r1, r2=None, mat=DARK, seg=16, dents=None):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    res = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg,
                                radius1=r1, radius2=r1 if r2 is None else r2, depth=d.length)
    rot = Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
    bmesh.ops.transform(bm, matrix=Matrix.Translation((p1 + p2) / 2) @ rot, verts=res['verts'])
    _tag(res['verts'], mat)
    if dents:
        bm.normal_update()
        dent(res['verts'], *dents)
    return res['verts']


def add_box(bm, center, size, mat=DARK, rot=None):
    res = bmesh.ops.create_cube(bm, size=1.0)
    m = Matrix.Translation(center) @ (rot or Matrix.Identity(4)) @ Matrix.Diagonal((*size, 1))
    bmesh.ops.transform(bm, matrix=m, verts=res['verts'])
    _tag(res['verts'], mat)
    return res['verts']


def add_sphere(bm, center, r, mat=DARK, seg=16, scale=(1, 1, 1), dents=None):
    res = bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=max(6, seg // 2), radius=r)
    m = Matrix.Translation(center) @ Matrix.Diagonal((*scale, 1))
    bmesh.ops.transform(bm, matrix=m, verts=res['verts'])
    _tag(res['verts'], mat)
    if dents:
        bm.normal_update()
        dent(res['verts'], *dents)
    return res['verts']


def add_torus(bm, center, axis, R, r, mat=DARK, seg=28, rseg=8):
    axis = Vector(axis).normalized()
    rot = Vector((0, 0, 1)).rotation_difference(axis).to_matrix()
    rings = []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        ring = []
        for j in range(rseg):
            b = 2 * math.pi * j / rseg
            p = Vector(((R + r * math.cos(b)) * math.cos(a), (R + r * math.cos(b)) * math.sin(a),
                        r * math.sin(b)))
            ring.append(bm.verts.new(Vector(center) + rot @ p))
        rings.append(ring)
    for i in range(seg):
        a, b = rings[i], rings[(i + 1) % seg]
        for j in range(rseg):
            f = bm.faces.new((a[j], b[j], b[(j + 1) % rseg], a[(j + 1) % rseg]))
            f.material_index = mat
    return [v for ring in rings for v in ring]


def add_wedge(bm, base, tip, w0, w1, t0, t1, wdir, mat=DARK):
    """Tapered blade/toe from base to tip; width along `wdir`, thickness across it."""
    base, tip = Vector(base), Vector(tip)
    d = (tip - base).normalized()
    a = Vector(wdir)
    a = (a - d * a.dot(d)).normalized()
    b = d.cross(a).normalized()
    v = []
    for p, w, t in ((base, w0, t0), (tip, w1, t1)):
        for sa, sb in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            v.append(bm.verts.new(p + a * sa * w / 2 + b * sb * t / 2))
    for f in ((0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)):
        bm.faces.new([v[i] for i in f]).material_index = mat
    return v


def rounded_box(size, center, p=5.0, cuts=16, taper=None, shape=None, dents=(), seed=0.0,
                mat=DARK, bm=None, rot=None):
    """Superellipsoid box with optional shaping and hammered dents.

    `shape(c)` edits the normalised [-1, 1] coordinate before scaling.
    `dents` is a sequence of (amplitude, frequency) noise layers along the normal.
    """
    tmp = bmesh.new()
    bmesh.ops.create_cube(tmp, size=2.0)
    bmesh.ops.subdivide_edges(tmp, edges=tmp.edges[:], cuts=cuts, use_grid_fill=True)
    for v in tmp.verts:
        c = v.co.copy()
        c /= (abs(c.x) ** p + abs(c.y) ** p + abs(c.z) ** p) ** (1.0 / p)
        if taper:
            k = taper(c.z)
            c.x *= k
            c.y *= k
        if shape:
            shape(c)
        v.co = Vector((c.x * size[0] / 2, c.y * size[1] / 2, c.z * size[2] / 2))
    tmp.normal_update()
    for i, (amp, freq) in enumerate(dents):
        dent(tmp.verts, amp, freq, seed + i * 3.7)
    m = Matrix.Translation(center) @ (rot or Matrix.Identity(4))
    bmesh.ops.transform(tmp, matrix=m, verts=tmp.verts)
    for f in tmp.faces:
        f.material_index = mat
    if bm is None:
        return tmp
    me = bpy.data.meshes.new('_tmp')
    tmp.to_mesh(me)
    tmp.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)
    return bm


def bezier_points(p0, p1, p2, n=16):
    p0, p1, p2 = Vector(p0), Vector(p1), Vector(p2)
    return [(1 - t) ** 2 * p0 + 2 * (1 - t) * t * p1 + t ** 2 * p2
            for t in (i / (n - 1) for i in range(n))]


def helix(center, r, length, turns, n=60):
    c = Vector(center)
    return [c + Vector((r * math.cos(2 * math.pi * turns * t), r * math.sin(2 * math.pi * turns * t),
                        -length * t)) for t in (i / (n - 1) for i in range(n))]


def tube(name, pts, radius, mat, mats, coll):
    cu = bpy.data.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    cu.bevel_depth = radius
    cu.bevel_resolution = 2
    sp = cu.splines.new('POLY')
    sp.points.add(len(pts) - 1)
    for pt, co in zip(sp.points, pts):
        pt.co = (*co, 1.0)
    cu.materials.append(mats[mat])
    ob = bpy.data.objects.new(name, cu)
    coll.objects.link(ob)
    return ob


def mesh_object(name, bm, mats, coll, sharp=40):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for m in mats:
        me.materials.append(m)
    me.polygons.foreach_set('use_smooth', [True] * len(me.polygons))
    me.set_sharp_from_angle(angle=math.radians(sharp))
    ob = bpy.data.objects.new(name, me)
    coll.objects.link(ob)
    return ob


def parent_to_bone(ob, arm, bone_name):
    bone = arm.data.bones[bone_name]
    ob.parent = arm
    ob.parent_type = 'BONE'
    ob.parent_bone = bone_name
    ob.matrix_parent_inverse = (arm.matrix_world @ bone.matrix_local
                                @ Matrix.Translation((0, bone.length, 0))).inverted()


def bake_modifiers(ob):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    baked = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), depsgraph=dg)
    old = ob.data
    ob.modifiers.clear()
    ob.data = baked
    bpy.data.meshes.remove(old)


# --------------------------------------------------------------------------
# Rig layout (rest pose, world coordinates)
# --------------------------------------------------------------------------

SIDES = (('L', 1), ('R', -1))  # robot's left is +X because it faces -Y


def leg_points(s):
    return dict(hip=Vector((s * 0.13, 0.01, 0.315)), knee=Vector((s * 0.108, -0.045, 0.185)),
                ankle=Vector((s * 0.097, -0.005, 0.034)))


def arm_points(s):
    return dict(shoulder=Vector((s * 0.255, -0.01, 0.385)), elbow=Vector((s * 0.248, 0.035, 0.288)),
                wrist=Vector((s * 0.262, -0.01, 0.113)))


ANTENNA = [Vector((0.10, 0.115, 0.705)), Vector((0.107, 0.125, 0.84)),
           Vector((0.117, 0.137, 0.98)), Vector((0.13, 0.15, 1.12))]

CLAW_REST_OPEN = {'L': 20.0, 'R': 1.0}  # degrees; the concept has one open, one closed claw


def build_armature(coll):
    data = bpy.data.armatures.new('D17Rig')
    arm = bpy.data.objects.new('D17Rig', data)
    coll.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    eb = data.edit_bones

    def bone(name, head, tail, parent=None, connect=False):
        b = eb.new(name)
        b.head, b.tail = head, tail
        b.roll = 0.0
        b.use_deform = name.startswith('antenna') or name == 'head'
        if parent:
            b.parent = eb[parent]
            b.use_connect = connect
        return b

    y_ = Vector((0, 0.06, 0))
    bone('root', (0, 0, 0), (0, 0.2, 0))
    bone('body', (0, 0, 0.40), (0, 0.12, 0.40), 'root')
    bone('head', (0, 0, 0.515), (0, 0.12, 0.515), 'body')
    for i in range(3):
        bone(f'antenna_{i + 1}', ANTENNA[i], ANTENNA[i + 1],
             'head' if i == 0 else f'antenna_{i}', connect=i > 0)
    for side, s in SIDES:
        lp, ap = leg_points(s), arm_points(s)
        bone(f'thigh.{side}', lp['hip'], lp['knee'], 'body')
        bone(f'shin.{side}', lp['knee'], lp['ankle'], f'thigh.{side}', connect=True)
        bone(f'ik_foot.{side}', lp['ankle'], lp['ankle'] + y_, 'root')
        bone(f'pole_knee.{side}', lp['knee'] + Vector((0, -0.4, 0)),
             lp['knee'] + Vector((0, -0.4, 0)) + y_, 'body')
        bone(f'arm_upper.{side}', ap['shoulder'], ap['elbow'], 'body')
        bone(f'arm_lower.{side}', ap['elbow'], ap['wrist'], f'arm_upper.{side}', connect=True)
        bone(f'ik_hand.{side}', ap['wrist'], ap['wrist'] + y_, 'body')  # arms are carried
        bone(f'pole_elbow.{side}', ap['elbow'] + Vector((0, 0.4, 0)),
             ap['elbow'] + Vector((0, 0.4, 0)) + y_, 'body')
        w = ap['wrist']
        bone(f'finger_a.{side}', w + Vector((-0.010, 0, -0.026)), w + Vector((-0.004, 0, -0.112)),
             f'ik_hand.{side}')
        bone(f'finger_b.{side}', w + Vector((0.010, 0, -0.026)), w + Vector((0.004, 0, -0.112)),
             f'ik_hand.{side}')
    bpy.ops.object.mode_set(mode='OBJECT')

    for side, _ in SIDES:
        for chain, target, pole in (('shin', 'ik_foot', 'pole_knee'),
                                    ('arm_lower', 'ik_hand', 'pole_elbow')):
            c = arm.pose.bones[f'{chain}.{side}'].constraints.new('IK')
            c.target, c.subtarget = arm, f'{target}.{side}'
            c.pole_target, c.pole_subtarget = arm, f'{pole}.{side}'
            c.chain_count = 2
        for f in ('finger_a', 'finger_b'):
            arm.pose.bones[f'{f}.{side}'].rotation_mode = 'AXIS_ANGLE'
    return arm


def calibrate_poles(arm):
    """Pick each IK pole angle so the solved rest pose reproduces the authored joint."""
    dg = bpy.context.evaluated_depsgraph_get()
    for side, s in SIDES:
        for chain, joint in (('shin', leg_points(s)['knee']), ('arm_lower', arm_points(s)['elbow'])):
            con = arm.pose.bones[f'{chain}.{side}'].constraints['IK']
            best = None
            for deg in range(-180, 180, 3):
                con.pole_angle = math.radians(deg)
                dg.update()
                head = arm.evaluated_get(dg).pose.bones[f'{chain}.{side}'].head
                err = (arm.matrix_world @ head - joint).length
                if best is None or err < best[0]:
                    best = (err, deg)
            con.pole_angle = math.radians(best[1])
            print(f'pole {chain}.{side}: {best[1]} deg, err {best[0] * 1000:.2f} mm')


# --------------------------------------------------------------------------
# Head: a painted slab shell, open underneath, cut away at the rear-bottom
# around a dial, with machinery inside and poking out the back.
# --------------------------------------------------------------------------

HEAD_C = Vector((-0.003, 0.0, 0.6125))
HEAD_SIZE = (0.435, 0.34, 0.195)
DIAL = Vector((-0.2, 0.085, 0.578))


def _head_shape(c):
    c.z += 0.03 * max(0.0, c.z) * (1 - c.x * c.x)       # slight crown
    if c.y > 0.55 and c.z > 0.5:                          # softened rear-top corner
        c.z -= (c.y - 0.55) * (c.z - 0.5) * 0.12
    c.x *= 1.0 - 0.025 * (c.z + 1) * 0.5                 # a touch narrower at the top


def build_head(arm, mats, coll):
    bm = rounded_box(HEAD_SIZE, HEAD_C, p=8.0, cuts=40, shape=_head_shape,
                     dents=((0.0045, 5.0), (0.0015, 22.0)), seed=1.0, mat=CREAM)
    shell = mesh_object('HeadShell', bm, mats, coll)
    cutters = []

    def cut(name, cbm, mat=CREAM):
        ob = mesh_object(name, cbm, [mats[mat]], coll)
        ob.hide_render = True
        mod = shell.modifiers.new(name, 'BOOLEAN')
        mod.object = ob
        mod.solver = 'EXACT'
        mod.material_mode = 'TRANSFER'
        cutters.append(ob)

    t = 0.009                 # hollow it out: shell wall thickness
    inner = rounded_box([d - 2 * t for d in HEAD_SIZE], HEAD_C, p=8.0, cuts=24,
                        shape=_head_shape, mat=0)
    cut('Hollow', inner, DARK)
    for x in (-0.11, 0.104):  # countersunk eye holes
        cbm = bmesh.new()
        add_cyl(cbm, (x, -0.205, 0.588), (x, -0.155, 0.588), 0.064, 0.025, mat=0, seg=40)
        cut('EyeCountersink', cbm)
        cbm = bmesh.new()
        add_cyl(cbm, (x, -0.22, 0.588), (x, -0.10, 0.588), 0.026, mat=0, seg=40)
        cut('EyeBore', cbm)
    for x in (-0.25, 0.25):   # oval ear ports
        cbm = bmesh.new()
        add_cyl(cbm, (x * 0.7, -0.112, 0.585), (x, -0.112, 0.585), 0.015, mat=0, seg=24)
        bmesh.ops.scale(cbm, vec=(1, 1, 2.1), space=Matrix.Translation((0, 0, -0.585)),
                        verts=cbm.verts)
        cut('EarPort', cbm)
    cbm = bmesh.new()     # open underside, leaving a lip
    add_box(cbm, (0, 0.08, 0.47), (0.385, 0.45, 0.12), mat=0)
    cut('Underside', cbm)
    cbm = bmesh.new()     # bottom edge climbs toward the rear
    slope = math.atan(0.143)
    rot = Matrix.Rotation(slope, 4, 'X')
    add_box(cbm, Vector((0, 0.10, 0.5536)) - rot @ Vector((0, 0, 0.04)), (0.6, 0.62, 0.08),
            mat=0, rot=rot)
    cut('RearSlope', cbm)
    cbm = bmesh.new()     # rear-lower cutaway
    add_box(cbm, (0, 0.27, 0.52), (0.6, 0.29, 0.25), mat=0)
    cut('RearNotch', cbm)
    cbm = bmesh.new()     # round relief around the dial
    add_cyl(cbm, (-0.3, DIAL.y, DIAL.z), (0.3, DIAL.y, DIAL.z), 0.06, mat=0, seg=48)
    cut('DialRelief', cbm)

    bev = shell.modifiers.new('soften', 'BEVEL')
    bev.limit_method = 'ANGLE'
    bev.angle_limit = math.radians(40)
    bev.width = 0.0025
    bev.segments = 2
    bake_modifiers(shell)
    for c in cutters:
        bpy.data.meshes.remove(c.data)
    parent_to_bone(shell, arm, 'head')

    bm = bmesh.new()
    # Interior chassis and eye sensors, seen through the holes and the open underside.
    rounded_box((0.33, 0.21, 0.10), (0, 0.0, 0.595), p=4, cuts=6, mat=DARK, bm=bm,
                dents=((0.004, 8),), seed=4)
    for x in (-0.11, 0.104):
        add_cyl(bm, (x, -0.152, 0.588), (x, -0.11, 0.588), 0.03, mat=EYE, seg=24)
        add_torus(bm, (x, -0.15, 0.588), (0, 1, 0), 0.029, 0.003, mat=DARK, seg=24, rseg=6)
    # Ear port housings: dark oval cups set into the ports.
    for s in (-1, 1):
        cbm_v = add_cyl(bm, (s * 0.19, -0.112, 0.585), (s * 0.222, -0.112, 0.585), 0.016,
                        mat=DARK, seg=20)
        for v in cbm_v:
            v.co.z = 0.585 + (v.co.z - 0.585) * 2.1
        add_cyl(bm, (s * 0.218, -0.112, 0.585), (s * 0.224, -0.112, 0.585), 0.009, mat=EYE, seg=16)
    # Top flaps: dark plates on hinges, tipped back, one with a coil spring.
    for x0, x1, tilt, roll in ((-0.212, -0.128, -0.45, 0.22), (0.052, 0.168, -0.6, -0.08)):
        rot = Matrix.Rotation(roll, 4, 'Y') @ Matrix.Rotation(tilt, 4, 'X')
        cx = (x0 + x1) / 2
        add_box(bm, (cx, -0.112, 0.724), (x1 - x0, 0.03, 0.008), rot=rot)
        add_cyl(bm, (x0 + 0.01, -0.124, 0.716), (x1 - 0.01, -0.124, 0.716), 0.006)
        add_box(bm, (cx, -0.124, 0.708), (0.03, 0.02, 0.014))
    rounded_box((0.042, 0.034, 0.03), (0.098, -0.128, 0.712), p=2.5, cuts=4, mat=DARK, bm=bm,
                dents=((0.003, 30),), seed=2)
    # Rear dial: a sensor drum sitting in the relief on the right-hand side.
    add_cyl(bm, (DIAL.x - 0.004, DIAL.y, DIAL.z), (DIAL.x + 0.05, DIAL.y, DIAL.z), 0.052, seg=40)
    for r in (0.043, 0.022):
        add_torus(bm, (DIAL.x - 0.004, DIAL.y, DIAL.z), (1, 0, 0), r, 0.0014, seg=32, rseg=6)
    add_cyl(bm, (DIAL.x - 0.01, DIAL.y, DIAL.z), (DIAL.x - 0.002, DIAL.y, DIAL.z), 0.01, seg=16)
    add_sphere(bm, (DIAL.x + 0.012, DIAL.y - 0.035, DIAL.z + 0.03), 0.004, mat=BARE)
    # Camera module and clutter poking out of the back of the shell.
    add_box(bm, (-0.11, 0.195, 0.632), (0.05, 0.05, 0.034))
    add_cyl(bm, (-0.125, 0.22, 0.64), (-0.125, 0.245, 0.64), 0.011, seg=16)
    add_cyl(bm, (-0.125, 0.244, 0.64), (-0.125, 0.248, 0.64), 0.007, mat=EYE, seg=16)
    add_cyl(bm, (-0.09, 0.21, 0.648), (-0.09, 0.21, 0.69), 0.0025)
    add_box(bm, (-0.15, 0.2, 0.6), (0.03, 0.04, 0.05), rot=Matrix.Rotation(0.3, 4, 'X'))
    add_cyl(bm, (-0.05, 0.13, 0.555), (-0.05, 0.21, 0.6), 0.012)
    add_box(bm, (0.05, 0.15, 0.58), (0.08, 0.06, 0.05))
    add_sphere(bm, (-0.06, 0.04, 0.625), 0.004, mat=EYE)
    add_cyl(bm, ANTENNA[0] - Vector((0, 0, 0.02)), ANTENNA[0] + Vector((0, 0, 0.018)), 0.011)
    add_box(bm, ANTENNA[0] + Vector((0, 0.0, 0.0)), (0.03, 0.03, 0.012))
    # Glowing lamp tucked under the front lip.
    add_cyl(bm, (-0.075, -0.112, 0.52), (0.055, -0.112, 0.52), 0.004, mat=GLOW, seg=10)
    add_box(bm, (-0.01, -0.104, 0.528), (0.15, 0.014, 0.01))
    parent_to_bone(mesh_object('HeadParts', bm, mats, coll), arm, 'head')

    spring = tube('HeadSpring', helix((0.172, -0.128, 0.755), 0.0065, 0.022, 4.5), 0.0011,
                  BARE, mats, coll)
    spring.rotation_euler = (0, 0, 0)
    parent_to_bone(spring, arm, 'head')

    lamp = bpy.data.lights.new('NeckLamp', 'POINT')
    lamp.energy = 0.08
    lamp.color = (1.0, 0.45, 0.15)
    lamp.shadow_soft_size = 0.01
    lamp_ob = bpy.data.objects.new('NeckLamp', lamp)
    lamp_ob.location = (-0.01, -0.09, 0.505)
    coll.objects.link(lamp_ob)
    parent_to_bone(lamp_ob, arm, 'head')


def build_antenna(arm, mats, coll):
    rings, seg, r = 48, 8, 0.0028
    bm = bmesh.new()
    lengths = [(ANTENNA[i + 1] - ANTENNA[i]).length for i in range(3)]
    total = sum(lengths)
    rows = []
    prev = None
    for i in range(rings + 1):
        d = total * i / rings
        k, acc = 0, 0.0
        while k < 2 and acc + lengths[k] < d:
            acc += lengths[k]
            k += 1
        t = (d - acc) / lengths[k]
        c = ANTENNA[k].lerp(ANTENNA[k + 1], t)
        c += Vector((noise.noise(Vector((d * 9, 0, 0))), noise.noise(Vector((0, d * 9, 3))), 0)) * 0.0025
        ring = [bm.verts.new(c + Vector((math.cos(a) * r, math.sin(a) * r, 0)))
                for a in (2 * math.pi * j / seg for j in range(seg))]
        if prev:
            for j in range(seg):
                bm.faces.new((prev[j], prev[(j + 1) % seg], ring[(j + 1) % seg], ring[j]))
        prev = ring
        rows.append((ring, k, t))
    bm.faces.new(prev)
    bm.verts.index_update()
    idx_rows = [([v.index for v in ring], k, t) for ring, k, t in rows]
    ob = mesh_object('Antenna', bm, mats, coll)
    groups = [ob.vertex_groups.new(name=f'antenna_{i + 1}') for i in range(3)]
    for ids, k, t in idx_rows:
        if k > 0 and t < 0.25:  # blend across joints
            w = 0.5 + 2 * t
            groups[k].add(ids, w, 'REPLACE')
            groups[k - 1].add(ids, 1 - w, 'REPLACE')
        else:
            groups[k].add(ids, 1.0, 'REPLACE')
    ob.parent = arm
    mod = ob.modifiers.new('rig', 'ARMATURE')
    mod.object = arm


# --------------------------------------------------------------------------
# Body: dented bowl pod with a rolled lip, neck gimbal, shoulders, backpack.
# --------------------------------------------------------------------------

def _pod_shape(c):
    if c.z < 0:                                  # rounder belly, sagging forward
        c.y -= 0.06 * (-c.z) * max(0.0, -c.y)
        c.z -= 0.03 * (1 - c.x * c.x) * (-c.z)


def build_body(arm, mats, coll):
    bm = rounded_box((0.415, 0.255, 0.175), (-0.005, -0.045, 0.387), p=3.8, cuts=22,
                     taper=lambda z: 0.95 + 0.05 * (z + 1) / 2 if z < 0 else 1.0,
                     shape=_pod_shape, dents=((0.009, 4.0), (0.003, 14.0)), seed=7.0, mat=DARK)
    rounded_box((0.421, 0.262, 0.022), (-0.005, -0.045, 0.468), p=3.8, cuts=10, mat=DARK, bm=bm,
                dents=((0.004, 9.0),), seed=8.0)
    rounded_box((0.34, 0.19, 0.02), (-0.005, -0.04, 0.474), p=4.0, cuts=8, mat=DARK, bm=bm,
                dents=((0.003, 10.0),), seed=9.0)
    parent_to_bone(mesh_object('Pod', bm, mats, coll), arm, 'body')

    bm = bmesh.new()
    # Neck gimbal rising into the head.
    add_cyl(bm, (0, -0.01, 0.47), (0, -0.01, 0.56), 0.055, 0.05, seg=24, dents=(0.003, 20))
    add_cyl(bm, (-0.11, -0.01, 0.535), (0.11, -0.01, 0.535), 0.016)
    for s in (-1, 1):
        add_box(bm, (s * 0.1, -0.01, 0.52), (0.022, 0.05, 0.05))
    # Warm indicator slits on the pod front.
    for x in (-0.085, -0.05, 0.03):
        add_box(bm, (x, -0.168, 0.452), (0.022, 0.01, 0.007), mat=GLOW_DIM)
    # Rivets along the lip.
    for i in range(11):
        x = -0.19 + i * 0.037
        add_sphere(bm, (x, -0.184, 0.466), 0.0035, seg=8)
    # Shoulder (robot's right, -X): cloth-wrapped motor.
    rounded_box((0.042, 0.05, 0.1), (-0.247, -0.01, 0.432), p=2.4, cuts=8, mat=DARK, bm=bm,
                dents=((0.006, 25.0), (0.002, 60.0)), seed=11)
    add_box(bm, (-0.222, -0.01, 0.445), (0.03, 0.04, 0.035))
    # Shoulder (robot's left, +X): bracket, motor and a hanging pale plate.
    add_box(bm, (0.228, -0.01, 0.452), (0.05, 0.026, 0.022))
    rounded_box((0.036, 0.042, 0.095), (0.262, -0.01, 0.432), p=3.0, cuts=8, mat=DARK, bm=bm,
                dents=((0.004, 25.0),), seed=12)
    add_box(bm, (0.24, -0.02, 0.38), (0.006, 0.026, 0.05), mat=BARE,
            rot=Matrix.Rotation(0.08, 4, 'Y'))
    add_cyl(bm, (0.24, -0.035, 0.404), (0.24, -0.005, 0.404), 0.003, seg=8)
    for s in (-1, 1):
        sh = arm_points(s)['shoulder']
        add_cyl(bm, sh + Vector((-0.016, 0, 0)), sh + Vector((0.016, 0, 0)), 0.011, seg=16)
        hip = leg_points(s)['hip']
        add_box(bm, hip + Vector((0, 0, 0.012)), (0.04, 0.04, 0.02))
        add_cyl(bm, hip + Vector((-0.02, 0, 0)), hip + Vector((0.02, 0, 0)), 0.012, seg=16)

    # Backpack: drum motors seen end-on from the side, a translucent canister, straps.
    for (x0, x1, y, z, r) in ((-0.135, 0.07, 0.10, 0.425, 0.064), (-0.125, 0.05, 0.172, 0.505, 0.046),
                              (-0.14, -0.02, 0.035, 0.505, 0.036), (0.0, 0.13, 0.16, 0.38, 0.04)):
        add_cyl(bm, (x0, y, z), (x1, y, z), r, seg=32, dents=(0.004, 25))
        add_torus(bm, (x0, y, z), (1, 0, 0), r * 0.8, 0.0016, seg=28, rseg=6)
        add_cyl(bm, (x0 - 0.006, y, z), (x0, y, z), r * 0.3, seg=16)
    rounded_box((0.22, 0.13, 0.15), (0.0, 0.11, 0.43), p=2.3, cuts=10, mat=DARK, bm=bm,
                dents=((0.012, 6.0), (0.004, 18.0)), seed=13)
    for z in (0.39, 0.47):
        rounded_box((0.235, 0.15, 0.016), (0.0, 0.11, z), p=3.0, cuts=6, mat=DARK, bm=bm,
                    dents=((0.002, 30.0),), seed=z * 10)
    rounded_box((0.06, 0.052, 0.112), (-0.112, 0.215, 0.425), p=4.0, cuts=8, mat=GLASS, bm=bm)
    add_box(bm, (-0.112, 0.215, 0.487), (0.066, 0.058, 0.014))
    add_box(bm, (-0.112, 0.215, 0.363), (0.066, 0.058, 0.014))
    add_cyl(bm, (-0.112, 0.215, 0.375), (-0.112, 0.215, 0.46), 0.012, seg=12)
    add_box(bm, (-0.095, 0.205, 0.345), (0.04, 0.05, 0.03), mat=CREAM_LIMB)
    add_box(bm, (0.08, 0.2, 0.47), (0.06, 0.05, 0.08))
    add_cyl(bm, (0.12, 0.18, 0.35), (0.12, 0.18, 0.50), 0.018, seg=12)
    parent_to_bone(mesh_object('BodyParts', bm, mats, coll), arm, 'body')

    for i, (a, mid, b, r, m) in enumerate((
            ((-0.17, -0.03, 0.31), (-0.06, 0.0, 0.23), (0.03, 0.04, 0.305), 0.003, CABLE),
            ((0.05, 0.03, 0.305), (0.13, 0.0, 0.24), (0.19, -0.04, 0.32), 0.0028, CABLE),
            ((-0.09, -0.06, 0.305), (-0.02, -0.08, 0.255), (0.05, -0.05, 0.305), 0.0022, CABLE),
            ((-0.05, 0.10, 0.33), (0.0, 0.12, 0.26), (0.06, 0.13, 0.335), 0.0035, CABLE),
            ((0.03, 0.12, 0.33), (0.07, 0.15, 0.275), (0.11, 0.14, 0.34), 0.003, CABLE),
            ((-0.14, 0.17, 0.44), (-0.17, 0.12, 0.36), (-0.21, 0.02, 0.4), 0.0045, DARK),
            ((-0.112, 0.215, 0.49), (-0.12, 0.17, 0.56), (-0.05, 0.14, 0.565), 0.005, DARK),
            ((0.12, 0.2, 0.5), (0.15, 0.1, 0.55), (0.07, 0.0, 0.53), 0.004, CABLE),
            ((-0.23, 0.0, 0.40), (-0.2, 0.06, 0.32), (-0.13, 0.05, 0.31), 0.003, CABLE))):
        parent_to_bone(tube(f'Cable{i}', bezier_points(a, mid, b), r, m, mats, coll), arm, 'body')


# --------------------------------------------------------------------------
# Limbs
# --------------------------------------------------------------------------

def build_limbs(arm, mats, coll):
    for side, s in SIDES:
        lp, ap = leg_points(s), arm_points(s)
        hip, knee, ankle = lp['hip'], lp['knee'], lp['ankle']

        # Inner leg: twin thigh struts and piston, chunky knee actuator, weathered shin.
        bm = bmesh.new()
        for dx in (-0.006, 0.006):
            add_cyl(bm, hip + Vector((dx, 0, 0)), knee + Vector((dx, 0, 0)), 0.007, mat=DARK)
        back = Vector((0, 0.014, 0))
        add_cyl(bm, hip.lerp(knee, 0.15) + back, hip.lerp(knee, 0.6) + back, 0.009, 0.009)
        add_cyl(bm, hip.lerp(knee, 0.6) + back, hip.lerp(knee, 0.92) + back, 0.004, mat=ROD)
        parent_to_bone(mesh_object(f'Thigh.{side}', bm, mats, coll), arm, f'thigh.{side}')

        bm = bmesh.new()
        add_cyl(bm, knee + Vector((-0.018, 0, 0)), knee + Vector((0.018, 0, 0)), 0.013, seg=16)
        top, bot = knee.lerp(ankle, -0.02), knee.lerp(ankle, 0.42)
        rounded_box((0.034, 0.03, (bot - top).length), (top + bot) / 2, p=3.0, cuts=6, mat=DARK,
                    bm=bm, dents=((0.003, 40.0),), seed=20 + s,
                    rot=Vector((0, 0, 1)).rotation_difference(top - bot).to_matrix().to_4x4())
        add_cyl(bm, knee.lerp(ankle, 0.3), ankle, 0.0055, mat=ROD)
        add_cyl(bm, knee.lerp(ankle, 0.72), knee.lerp(ankle, 0.8), 0.0085)
        parent_to_bone(mesh_object(f'Shin.{side}', bm, mats, coll), arm, f'shin.{side}')

        # Bird-like foot: knotted ankle, cream toes splayed sideways and forward, rear spur.
        bm = bmesh.new()
        add_sphere(bm, ankle, 0.013, dents=(0.003, 60))
        add_box(bm, ankle + Vector((0, -0.003, -0.018)), (0.03, 0.03, 0.016))
        base = ankle + Vector((0, -0.004, -0.026))
        for tip, w in (((-0.052, -0.012), 0.016), ((0.052, -0.012), 0.016), ((0.0, -0.045), 0.014)):
            add_wedge(bm, base, ankle + Vector((tip[0], tip[1], -0.031)), w * 1.3, 0.007, 0.016,
                      0.006, (tip[1], -tip[0], 0), mat=CREAM_LIMB)
        add_wedge(bm, base, ankle + Vector((0, 0.03, -0.03)), 0.01, 0.003, 0.009, 0.003, (1, 0, 0))
        parent_to_bone(mesh_object(f'Foot.{side}', bm, mats, coll), arm, f'ik_foot.{side}')

        sh, el, wr = ap['shoulder'], ap['elbow'], ap['wrist']
        # Upper arm: dark strut, piston and an elbow bracket with a hook.
        bm = bmesh.new()
        add_cyl(bm, sh, el, 0.0075)
        off = Vector((s * 0.011, 0.004, 0))
        add_cyl(bm, sh.lerp(el, 0.1) + off, sh.lerp(el, 0.6) + off, 0.0095)
        add_cyl(bm, sh.lerp(el, 0.6) + off, el + off * 0.6, 0.004, mat=ROD)
        parent_to_bone(mesh_object(f'ArmUpper.{side}', bm, mats, coll), arm, f'arm_upper.{side}')

        # Forearm: two cream sleeves split by a dark collar, hinge at the elbow.
        bm = bmesh.new()
        add_cyl(bm, el + Vector((-0.017, 0, 0)), el + Vector((0.017, 0, 0)), 0.012, seg=16)
        add_box(bm, el + Vector((0, 0.004, -0.012)), (0.028, 0.02, 0.03))
        add_cyl(bm, el + Vector((s * 0.014, 0.0, -0.005)), el + Vector((s * 0.024, 0.0, -0.022)),
                0.003)
        add_cyl(bm, el.lerp(wr, 0.12), el.lerp(wr, 0.46), 0.0125, 0.0115, mat=CREAM_LIMB, seg=18,
                dents=(0.0015, 80, 30 + s))
        add_cyl(bm, el.lerp(wr, 0.45), el.lerp(wr, 0.53), 0.0135, seg=16)
        add_cyl(bm, el.lerp(wr, 0.52), el.lerp(wr, 0.9), 0.0098, 0.009, mat=CREAM_LIMB, seg=18,
                dents=(0.0012, 80, 31 + s))
        add_cyl(bm, el.lerp(wr, 0.89), wr, 0.0115, seg=16)
        parent_to_bone(mesh_object(f'ArmLower.{side}', bm, mats, coll), arm, f'arm_lower.{side}')

        # Hand: wrist knuckle and palm block; a fixed thumb angled toward the body.
        bm = bmesh.new()
        add_sphere(bm, wr, 0.0125, dents=(0.002, 70))
        rounded_box((0.034, 0.026, 0.03), wr + Vector((0, 0, -0.017)), p=3.0, cuts=4, mat=DARK,
                    bm=bm, dents=((0.0025, 50.0),), seed=40 + s)
        add_cyl(bm, wr + Vector((0, -0.016, -0.027)), wr + Vector((0, 0.016, -0.027)), 0.005)
        thumb_base = wr + Vector((-s * 0.012, 0.0, -0.02))
        add_wedge(bm, thumb_base, thumb_base + Vector((-s * 0.032, 0.0, -0.04)),
                  0.012, 0.004, 0.007, 0.0025, (0, 1, 0))
        parent_to_bone(mesh_object(f'Hand.{side}', bm, mats, coll), arm, f'ik_hand.{side}')

        # Fingers: broad two-segment blades that close into a spade.
        for f, sx in (('finger_a', -1), ('finger_b', 1)):
            b = arm.data.bones[f'{f}.{side}']
            h, t = b.head_local, b.tail_local
            mid = h.lerp(t, 0.5) + Vector((sx * 0.005, 0, 0))
            bm = bmesh.new()
            add_cyl(bm, h + Vector((0, -0.012, 0)), h + Vector((0, 0.012, 0)), 0.006, seg=12)
            add_wedge(bm, h, mid, 0.022, 0.019, 0.014, 0.011, (0, 1, 0))
            add_wedge(bm, mid, t, 0.019, 0.004, 0.011, 0.003, (0, 1, 0))
            add_cyl(bm, mid + Vector((0, -0.01, 0)), mid + Vector((0, 0.01, 0)), 0.005, seg=10)
            parent_to_bone(mesh_object(f'Finger.{f}.{side}', bm, mats, coll, sharp=30), arm,
                           f'{f}.{side}')


# --------------------------------------------------------------------------
# Animation
# --------------------------------------------------------------------------

def smoothstep(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def window(f, a, b):
    """0 before frame a, 1 after frame b, eased in between."""
    return smoothstep((f - a) / (b - a))


def settle(f, f0, amp, rate=0.18, freq=0.55):
    """Damped spring: rises to `amp` at f0 with a small overshoot and wobble."""
    if f < f0:
        return 0.0
    d = f - f0
    return amp * (1 - math.exp(-rate * d) * math.cos(freq * d))


def foot_events(n_steps, close_last):
    """Step schedule: alternate feet, each step carries a foot one stride ahead.
    With `close_last` the final step only brings the foot beside the other one."""
    pos = dict(FEET_START)
    events = {'L': [], 'R': []}
    for i in range(n_steps):
        foot, other = ('L', 'R') if i % 2 == 0 else ('R', 'L')
        start = i * STEP
        to = pos[other] if close_last and i == n_steps - 1 else pos[foot] + STRIDE
        events[foot].append((start, start + SWING, pos[foot], to))
        pos[foot] = to
    return events


def foot_at(events, foot, f):
    """Forward progress, lift height and swing progress (None when planted) at frame f."""
    p = FEET_START[foot]
    for a, b, p0, p1 in events[foot]:
        if f < a:
            break
        if f >= b:
            p = p1
            continue
        s = (f - a) / (b - a)
        # Quick lift, slow careful set-down.
        return p0 + (p1 - p0) * smoothstep(s), LIFT * math.sin(math.pi * s ** 0.65), s
    return p, 0.0, None


def _key(pbone, *paths, frame):
    for path in paths:
        pbone.keyframe_insert(path, frame=frame)


def animate(arm, frames, hero):
    """Timid biped walk on the inner legs; the claw arms are carried, never walked on.

    Loop mode repeats one two-step cycle in place. Hero mode walks forward, stops
    with a closing half step, then turns to the camera with a curious head tilt.
    Returns the body's forward progress per frame so a camera can follow it.
    """
    pb = arm.pose.bones
    events = foot_events(HERO_STEPS if hero else 2, close_last=hero)
    tau = 2 * math.pi
    rad = math.radians
    axes = {}
    for side, _ in SIDES:
        for f in ('finger_a', 'finger_b'):
            b = arm.data.bones[f'{f}.{side}']
            axes[f'{f}.{side}'] = (b.matrix_local.to_3x3().inverted() @ Vector((0, 1, 0))).normalized()
    for name in pb.keys():
        if not name.startswith('finger'):
            pb[name].rotation_mode = 'XYZ'

    progress = []
    for frame in range(1, frames + 1):
        f = frame - 1
        fl = f if hero else f % CYCLE
        u = (fl % CYCLE) / CYCLE                      # phase within the two-step cycle
        walk = 1.0 - window(f, STOP_AT - 12, STOP_AT + 4) if hero else 1.0
        look = window(f, STOP_AT - 2, STOP_AT + 12) if hero else 0.0
        idle = f - STOP_AT if hero else 0

        feet = {side: foot_at(events, side, fl) for side, _ in SIDES}
        body_p = (feet['L'][0] + feet['R'][0]) / 2    # body moves only while a foot is in the air
        progress.append(body_p)

        pb['root'].location = (0, -body_p if hero else 0.0, 0)
        _key(pb['root'], 'location', frame=frame)

        for side, s in SIDES:
            p, lift, sw = feet[side]
            ik = pb[f'ik_foot.{side}']
            ik.location = (0, -(p - body_p), lift)
            dangle = rad(14) * math.sin(math.pi * sw) if sw is not None else 0.0
            ik.rotation_euler = (dangle, 0, rad(-s * 7))      # toes dangle, feet slightly pigeon-toed
            _key(ik, 'location', 'rotation_euler', frame=frame)

        # Body: gentle waddle over the planted foot, a small dip on each landing, a forward lean.
        sway = math.sin(tau * u)
        breathe = 0.0015 * math.sin(tau * f / 50)
        body = pb['body']
        body.location = (-0.011 * sway * walk, 0,
                         (0.0035 * math.sin(2 * tau * u - 0.3 * math.pi) - 0.0035) * walk
                         + breathe * (1 - walk))
        body_rot = (3.5 * walk + 0.6 * math.sin(2 * tau * u - 1.0) * walk - 2.0 * look,
                    -2.5 * sway * walk,
                    1.5 * math.sin(tau * u + 0.4) * walk - 8.0 * look)
        body.rotation_euler = [rad(v) for v in body_rot]
        _key(body, 'location', 'rotation_euler', frame=frame)

        # Head: stabilised like a bird's. It holds a level gaze against the waddle and only
        # glances slowly around; in the hero shot it turns to the camera and tilts.
        head = pb['head']
        glance = math.sin(tau * f / 100) if hero else math.sin(tau * u)
        tilt = settle(f, STOP_AT + 10, 14.0) if hero else 0.0
        world = (2.5 * walk - 5.0 * look,
                 1.5 * math.sin(tau * u - 1.2) * walk + tilt,
                 (12.0 if hero else 7.0) * glance * walk - 34.0 * look)
        head.rotation_euler = [rad(w - b) for w, b in zip(world, body_rot)]
        _key(head, 'rotation_euler', frame=frame)

        # Antenna: light follow-through, plus a springy perk when the head tilts.
        perk_t = f - (STOP_AT + 10)
        perk = 12.0 * math.exp(-perk_t / 7) * math.sin(perk_t * 0.9) if hero and perk_t > 0 else 0.0
        for i, amp in enumerate((2.0, 2.5, 3.0)):
            lag = 1.2 + 0.5 * i
            pb[f'antenna_{i + 1}'].rotation_euler = (
                rad(amp * math.sin(2 * tau * u - lag) * walk + perk * (0.5 + 0.25 * i)), 0,
                rad(amp * 1.2 * math.sin(tau * u - lag) * walk))
            _key(pb[f'antenna_{i + 1}'], 'rotation_euler', frame=frame)

        # Claw arms carried in front, a little raised, with a timid counter-swing.
        shy = look * smoothstep(idle / 20) if hero else 0.0
        for side, s in SIDES:
            hand = pb[f'ik_hand.{side}']
            hand.location = (-s * (0.04 + 0.012 * shy),
                             -0.09 + 0.012 * s * math.cos(tau * u) * walk,
                             0.112 + 0.007 * math.sin(2 * tau * u - 1.6) * walk + 0.018 * shy)
            hand.rotation_euler = (rad(-24 - 10 * shy), rad(s * 6), rad(s * 10))
            _key(hand, 'location', 'rotation_euler', frame=frame)

            fidget = 0.0
            if side == 'L':
                fidget = 6.0 * math.sin(2 * tau * u) * walk
                if hero and idle > 14:
                    fidget += 14.0 * (0.5 - 0.5 * math.cos(tau * (idle - 14) / 18))
            else:
                fidget = 2.5 * math.sin(2 * tau * u + 1.0) * walk
            opening = rad(CLAW_REST_OPEN[side] + fidget)
            for fname, sign in (('finger_a', 1), ('finger_b', -1)):
                fp = pb[f'{fname}.{side}']
                fp.rotation_axis_angle = (sign * opening, *axes[f'{fname}.{side}'])
                _key(fp, 'rotation_axis_angle', frame=frame)
    return progress


IDLE_FRAMES = 168    # 7 s loop

# Idle look-around beats: (start frame, frames to get there, head (pitch, roll, yaw) in degrees).
# Positive yaw looks to D-17's left; negative pitch looks up.
IDLE_LOOKS = [
    (0, 1, (3, 0, 0)),
    (16, 8, (2, 4, 30)),       # quick glance to his left...
    (38, 10, (0, 9, 30)),      # ...and a curious tilt at whatever is there
    (60, 9, (-13, -4, -8)),    # something above
    (98, 8, (2, -3, -32)),     # glance to his right
    (122, 9, (17, 6, 10)),     # down at his own claw
    (142, 14, (3, 0, 0)),      # back to centre, settle
]


def ease_back(x, overshoot=1.3):
    """Ease out with a small overshoot: quick, alert head darts that settle."""
    x = min(1.0, max(0.0, x))
    return 1 + (overshoot + 1) * (x - 1) ** 3 + overshoot * (x - 1) ** 2


def idle_head(f):
    pose = IDLE_LOOKS[0][2]
    for start, dur, target in IDLE_LOOKS[1:]:
        if f < start:
            break
        k = ease_back((f - start) / dur)
        pose = tuple(a + (b - a) * k for a, b in zip(pose, target))
    return pose


def animate_idle(arm, frames):
    """Standing idle that loops: breathing, weight shifts, and a curious look-around in quick
    darts and holds. The body follows the head a little late; the antenna whips after it."""
    pb = arm.pose.bones
    tau = 2 * math.pi
    rad = math.radians
    axes = {}
    for side, _ in SIDES:
        for f in ('finger_a', 'finger_b'):
            b = arm.data.bones[f'{f}.{side}']
            axes[f'{f}.{side}'] = (b.matrix_local.to_3x3().inverted() @ Vector((0, 1, 0))).normalized()
    for name in pb.keys():
        if not name.startswith('finger'):
            pb[name].rotation_mode = 'XYZ'

    for frame in range(1, frames + 1):
        f = frame - 1
        head_w = idle_head(f)
        lagged = idle_head(max(0, f - 5))
        prev = idle_head(max(0, f - 3))

        _key(pb['root'], 'location', frame=frame)
        for side, s in SIDES:
            ik = pb[f'ik_foot.{side}']
            tap = 0.0
            if side == 'R' and 128 <= f < 140:   # a little nervous toe tap
                tap = 0.012 * math.sin(math.pi * (f - 128) / 12)
            ik.location = (0, 0, tap)                # feet side by side
            ik.rotation_euler = (rad(20) * tap / 0.012, 0, rad(-s * 7))
            _key(ik, 'location', 'rotation_euler', frame=frame)

        body = pb['body']
        body_rot = (2.0 + 0.25 * lagged[0], 0.15 * lagged[1] + 1.2 * math.sin(tau * f / frames),
                    0.25 * lagged[2])
        body.location = (0.006 * math.sin(tau * f / frames), 0,
                         -0.006 + 0.0018 * math.sin(tau * 3 * f / frames))
        body.rotation_euler = [rad(v) for v in body_rot]
        _key(body, 'location', 'rotation_euler', frame=frame)

        head = pb['head']
        head.rotation_euler = [rad(w - b) for w, b in zip(head_w, body_rot)]
        _key(head, 'rotation_euler', frame=frame)

        whip = [h - p for h, p in zip(head_w, prev)]   # head angular change drives the antenna
        for i in range(3):
            k = 0.9 + 0.5 * i
            pb[f'antenna_{i + 1}'].rotation_euler = (
                rad(-whip[0] * k + 1.0 * math.sin(tau * 3 * f / frames - i)), 0,
                rad(whip[2] * k * 0.6))
            _key(pb[f'antenna_{i + 1}'], 'rotation_euler', frame=frame)

        # Claws held in front; the left one fidgets while he looks down at it.
        look_down = smoothstep((f - 122) / 8) * (1 - smoothstep((f - 142) / 10))
        for side, s in SIDES:
            hand = pb[f'ik_hand.{side}']
            lift = 0.02 * look_down if side == 'L' else 0.0
            hand.location = (-s * 0.04, -0.09 - 0.015 * (look_down if side == 'L' else 0),
                             0.112 + lift + 0.0015 * math.sin(tau * 3 * f / frames - 0.8))
            hand.rotation_euler = (rad(-24 - 12 * (look_down if side == 'L' else 0)),
                                   rad(s * 6), rad(s * 10))
            _key(hand, 'location', 'rotation_euler', frame=frame)
            if side == 'L':
                fidget = 16.0 * look_down * (0.5 - 0.5 * math.cos(tau * (f - 122) / 10))
            else:
                fidget = 4.0 * smoothstep((f - 40) / 4) * (1 - smoothstep((f - 52) / 6))
            opening = rad(CLAW_REST_OPEN[side] + fidget)
            for fname, sign in (('finger_a', 1), ('finger_b', -1)):
                fp = pb[f'{fname}.{side}']
                fp.rotation_axis_angle = (sign * opening, *axes[f'{fname}.{side}'])
                _key(fp, 'rotation_axis_angle', frame=frame)


# --------------------------------------------------------------------------
# Scene, lighting, cameras
# --------------------------------------------------------------------------

def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def add_light(name, kind, loc, target, energy, size, color=(1, 1, 1)):
    data = bpy.data.lights.new(name, kind)
    data.energy = energy
    data.color = color
    if kind == 'AREA':
        data.size = size
    ob = bpy.data.objects.new(name, data)
    ob.location = loc
    look_at(ob, target)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def setup_world_and_floor(transparent):
    scene = bpy.context.scene
    world = bpy.data.worlds.new('World')
    scene.world = world
    try:
        world.use_nodes = True
    except AttributeError:
        pass
    bg = next(n for n in world.node_tree.nodes if n.type == 'BACKGROUND')
    bg.inputs['Color'].default_value = (0.15, 0.175, 0.16, 1)
    bg.inputs['Strength'].default_value = 1.0
    if transparent:
        scene.render.film_transparent = True
        return
    me = bpy.data.meshes.new('Floor')
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=30)
    bm.to_mesh(me)
    bm.free()
    me.materials.append(floor_material())
    floor = bpy.data.objects.new('Floor', me)
    scene.collection.objects.link(floor)


def setup_render(args):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = args.samples
    scene.cycles.use_adaptive_sampling = True
    scene.cycles.use_denoising = True
    scene.cycles.max_bounces = 6
    scene.cycles.diffuse_bounces = 2
    scene.cycles.glossy_bounces = 2
    scene.render.resolution_x, scene.render.resolution_y = args.res
    scene.render.resolution_percentage = 100
    scene.render.fps = 24
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA' if args.shot == 'sprites' else 'RGB'
    scene.view_settings.view_transform = 'AgX'
    try:
        scene.view_settings.look = 'AgX - Medium High Contrast'
    except TypeError:
        pass


def camera(name, loc, target, lens=50, ortho=None):
    data = bpy.data.cameras.new(name)
    data.lens = lens
    if ortho:
        data.type = 'ORTHO'
        data.ortho_scale = ortho
    ob = bpy.data.objects.new(name, data)
    ob.location = loc
    look_at(ob, target)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    return ob


def build_robot(name='D17', loc=(0, 0, 0), rot_z=0.0):
    """Build one robot. Real copies, not collection instances: instances cast no shadows."""
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    mats = build_materials()
    arm = build_armature(coll)
    build_head(arm, mats, coll)
    build_antenna(arm, mats, coll)
    build_body(arm, mats, coll)
    build_limbs(arm, mats, coll)
    calibrate_poles(arm)
    arm.location = loc
    arm.rotation_euler = (0, 0, math.radians(rot_z))
    return arm


SHOTS = {
    # name: (robot placements, default resolution)
    'turnaround': ([('D17Front', (-0.33, 0, 0), 0), ('D17Side', (0.36, 0.05, 0), 90)], [960, 640]),
    'hero': ([('D17', (0, 0, 0), 0)], [960, 640]),
    'idle': ([('D17', (0, 0, 0), 0)], [960, 640]),
    'sprites': ([('D17', (0, 0, 0), 90)], [256, 256]),
    'closeup': ([('D17Front', (-0.33, 0, 0), 0), ('D17Side', (0.36, 0.05, 0), 90)], [1440, 960]),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--shot', default='turnaround', choices=list(SHOTS))
    ap.add_argument('--out', required=True)
    ap.add_argument('--samples', type=int, default=48)
    ap.add_argument('--res', type=int, nargs=2, default=None)
    ap.add_argument('--still', type=int, nargs='+', default=None, help='render only these frames')
    ap.add_argument('--blend', default=None, help='also save the finished scene as a .blend')
    args = ap.parse_args()
    placements, res = SHOTS[args.shot]
    args.res = args.res or res

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    rigs = [build_robot(*p) for p in placements]

    hero = args.shot == 'hero'
    frames = {'hero': HERO_FRAMES, 'idle': IDLE_FRAMES}.get(args.shot, CYCLE)
    scene.frame_start, scene.frame_end = 1, frames
    if args.shot == 'idle':
        for arm in rigs:
            animate_idle(arm, frames)
    else:
        progress = [animate(arm, frames, hero) for arm in rigs][0]

    setup_world_and_floor(transparent=args.shot == 'sprites')
    setup_render(args)
    add_light('Key', 'AREA', (-1.2, -1.6, 2.4), (0, 0, 0.45), 150, 1.6, (1.0, 0.96, 0.9))
    add_light('Fill', 'AREA', (1.8, -1.2, 0.8), (0, 0, 0.4), 45, 2.5, (0.85, 0.95, 1.0))
    add_light('Rim', 'AREA', (0.6, 2.0, 1.6), (0, 0, 0.5), 140, 1.2)
    add_light('Top', 'AREA', (0, -0.3, 2.6), (0, 0, 0), 260, 1.2, (0.95, 1.0, 0.95))

    if args.shot == 'turnaround':
        camera('Cam', (0.0, -2.35, 0.26), (0.0, 0, 0.42), lens=45)
    elif args.shot == 'idle':
        camera('Cam', (-1.05, -1.55, 0.42), (0, 0, 0.43), lens=45)
    elif args.shot == 'closeup':
        camera('Cam', (0.0, -1.75, 0.45), (0.0, 0, 0.45), lens=38)
    elif args.shot == 'hero':
        rig = bpy.data.objects.new('CamRig', None)
        scene.collection.objects.link(rig)
        cam = camera('Cam', (-1.25, -1.75, 0.42), (0, -0.05, 0.40), lens=42)
        cam.parent = rig
        for i in range(frames):  # follow the body's progress, smoothed so the camera glides
            near = progress[max(0, i - 10):i + 11]
            rig.location = (0, -sum(near) / len(near), 0)
            rig.keyframe_insert('location', frame=i + 1)
    else:
        camera('Cam', (0, -4, 0.55), (0, 0, 0.55), ortho=1.25)

    if args.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend))

    os.makedirs(args.out, exist_ok=True)
    if args.still:
        for n in args.still:
            scene.frame_set(n)
            scene.render.filepath = os.path.join(os.path.abspath(args.out), f'still_{n:04d}.png')
            bpy.ops.render.render(write_still=True)
    else:
        scene.render.filepath = os.path.join(os.path.abspath(args.out), 'frame_')
        bpy.ops.render.render(animation=True)


if __name__ == '__main__':
    main()
