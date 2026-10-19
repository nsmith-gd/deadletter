"""DL-08 The Slipping Cage: the set and D-17's clips for this scene (docs/chapter1_build_spec.md, section 6).

Built in world coordinates, between the stretches that build_dl01.OFF2..OFF4 move: from the top end of
DL-04's returns belt (that file's x 64.6, moved by OFF3) to the residential tunnel (the same 64.6, moved by
OFF4). Locally u = x - X0, with X0 = 85.6.

  u 0 to 1.2    the deck beyond the belt end (z 1.6)
  u 1.2 to 1.8  climb 1: the hatch housing under the chute from the rings (top 2.2)
  u 1.8 to 2.6  climb 2: a dead conveyor gantry (top 2.8)
  u 2.6 to 3.6  climb 3: the upper landing (top 3.4), its lattice gate folded back
  u 3.6 to 5.2  the residential access shaft: the freight cage, its pawl and the rack on the back wall,
                the counterweight in the back corner, chains up into the dark over the sheave
  u 5.2 to 9.0  the lower landing (z 1.6) with its amber lamp and stop stripe, and the antechamber to
                the tunnel; the wall above 3.3 stops him crossing at the upper level

The cage, the counterweight, the sheave, the pawl and its lever are separate objects for the game to drive
(see the constants below). Static dressing is merged into a few C8* objects.

Coordinates as everywhere: metres, Blender Z up, the lane at y = 0, travel along +x.
"""
import math
import os
import random

import bpy
import bmesh
from mathutils import Matrix, Vector

import build_d17 as d17
import build_dl03 as dl03
from build_d17 import (add_box, add_cyl, add_sphere, add_torus, emission_material, worn_material,
                       simple_material, SIDES, CLAW_REST_OPEN)

HERE = os.path.dirname(os.path.abspath(__file__))
TEX = os.path.join(HERE, 'textures')

# Shared with the game. World x = X0 + u.
BELT_END = 64.6                      # DL-04's belt top end and its tunnel start, in that file's coordinates
X0 = 85.6                            # set from dl01.OFF3 in build_set
DECK = 1.6                           # the belt deck and the lower landing
CLIMBS = ((1.2, 1.8, 2.2), (1.8, 2.6, 2.8), (2.6, 3.6, 3.4))   # u0, u1, top: three mantles of 0.6
SHAFT = (3.6, 5.2)                   # u
SHAFT_U = 4.4                        # the cage's centre line (world x 90.0)
LANDING = (5.2, 9.0)                 # the lower landing and the antechamber, u
ANTE_CEIL = 3.3                      # the wall over the lower landing starts here
PIT_Z = -0.6                         # the pit floor, the buffers' base
# The cage: origin at its floor-top centre. Its floor runs level with the upper landing at the start.
CAGE_HALF, CAGE_Y, CAGE_H = 0.75, (-0.6, 0.6), 2.1
CAGE_TOP, CAGE_LAND, CAGE_BOTTOM = 3.4, 1.6, -0.1   # floor-top z: start, the lit landing, on the buffers
RAIL_Y, RAIL_Z, RAIL_X = 0.34, 0.11, (-0.3, 0.62)   # the side rails he grips (cage-local), either side of the lane
MESH_GAP = (0.08, 0.46)              # the back mesh's torn corner over the pawl: from this x to the right post, up to z
BACK_Y = 0.88                        # the plane of the rack, the pawl, the chains and the counterweight
SHAFT_BACK = 1.05                    # the shaft's back wall face
RACK_Z = (-0.6, 3.6)                 # CageRack, world z
RACK_X, RACK_ROOT, RACK_TIP, RACK_PITCH = 0.52, 0.48, 0.40, 0.08      # cage-local x: bar centre, tooth root, tip
# The rack and the pawl are in the back right corner, beside the lit landing and clear of D-17 at the lever;
# the counterweight hangs in the back left. The pawl rides behind the cage's back mesh just above the floor,
# where the side view sees it through the mesh. It is modelled lifted (dog 55 degrees above horizontal,
# pointing +x); thrown, it turns PAWL_THROW about +Y and its tip rests on a tooth, 20 degrees below horizontal.
PAWL_PIN, PAWL_LEN, PAWL_UP, PAWL_SET = (0.2, BACK_Y, 0.24), 0.25, 55.0, -20.0
PAWL_THROW = PAWL_UP - PAWL_SET      # +75 degrees about Blender +Y
PAWL_TIP_SET = PAWL_PIN[2] + PAWL_LEN * math.sin(math.radians(PAWL_SET))   # cage-local z of the biting tip
# The lever, red, inside the cage on its left post: pivot at its base, modelled at rest (leaning 10 degrees
# toward -x); thrown, it turns LEVER_THROW about +Y, its top toward +x (into the cage).
LEVER_PIVOT, LEVER_LEN, LEVER_REST, LEVER_THROW = (-0.6, 0.3, 0.0), 0.6, -10.0, 55.0
# The chains: from the cage's hitch (cage-local) over the sheave (world) down to the counterweight, 1:1.
HITCH = (0.05, BACK_Y, 2.27)
SHEAVE_X, SHEAVE_Z, SHEAVE_R = -0.25, 9.6, 0.3         # cage-local x of its axle, world z, pitch radius
CW_X, CW_SIZE = -0.55, (0.24, 0.16, 1.1)               # counterweight: local x, size; origin at its hook (top)
CW_SUM = 7.2                         # cage floor z + counterweight hook z, always (cage at 3.4 -> hook at 3.8)


def _obj(name, bm, mats, coll, sharp=35):
    return d17.mesh_object(name, bm, mats, coll, sharp=sharp)


_plane = dl03._plane
_font = dl03._font
_age = dl03._age


def _image_material(name, path, rough=0.7):
    mat, nt, bsdf = d17._new_material(name)
    tex = nt.nodes.new('ShaderNodeTexImage')
    tex.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(tex.outputs['Color'], bsdf.inputs['Base Color'])
    bsdf.inputs['Roughness'].default_value = rough
    return mat


def _rz(a):
    return Matrix.Rotation(a, 4, 'Z')


def _ry(a):
    return Matrix.Rotation(a, 4, 'Y')


def bx(bm, u, y, z, mat=0, rot=None):
    """A box from (min, max) ranges, u along the scene (world x = X0 + u)."""
    return add_box(bm, (X0 + (u[0] + u[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2),
                   (u[1] - u[0], y[1] - y[0], z[1] - z[0]), mat=mat, rot=rot)


def lbx(bm, x, y, z, mat=0, rot=None):
    """A box from (min, max) ranges in an object's own space."""
    return add_box(bm, ((x[0] + x[1]) / 2, (y[0] + y[1]) / 2, (z[0] + z[1]) / 2),
                   (x[1] - x[0], y[1] - y[0], z[1] - z[0]), mat=mat, rot=rot)


def W(u, y, z):
    return (X0 + u, y, z)


def _prism(bm, pts, y0, y1, mat=0):
    """A prism: the (x, z) outline `pts` (counter-clockwise seen from -y) from y0 to y1."""
    a = [bm.verts.new((x, y0, z)) for x, z in pts]
    b = [bm.verts.new((x, y1, z)) for x, z in pts]
    faces = [bm.faces.new(a[::-1]), bm.faces.new(b)]
    n = len(pts)
    for i in range(n):
        faces.append(bm.faces.new((a[i], a[(i + 1) % n], b[(i + 1) % n], b[i])))
    for f in faces:
        f.material_index = mat


def _chain(bm, x, y, z0, z1, pitch=0.1, mat=0):
    """A hanging chain: flat links turned alternately, from z0 up to z1."""
    for k in range(int((z1 - z0) / pitch)):
        z = z0 + (k + 0.5) * pitch
        add_box(bm, (x, y, z), (0.034, 0.009, pitch + 0.03), mat=mat, rot=_rz(math.pi / 2) if k % 2 else None)


def _mesh_panel(bm, axis, fixed, a, b, z, step_a, step_z, frame_mat, wire_mat, wire=0.006, frame=0.03):
    """A framed wire-mesh panel in a vertical plane: `axis` 'x' runs the panel along x at y = fixed, 'y'
    along y at x = fixed; spans a..b along it and z (z0, z1)."""
    def piece(lo_hi, zz, mat):
        if axis == 'x':
            lbx(bm, lo_hi, (fixed - wire, fixed + wire), zz, mat)
        else:
            lbx(bm, (fixed - wire, fixed + wire), lo_hi, zz, mat)
    z0, z1 = z
    n = max(1, int(round((b - a) / step_a)))
    for k in range(1, n):
        s = a + (b - a) * k / n
        piece((s - wire / 2, s + wire / 2), (z0, z1), wire_mat)
    n = max(1, int(round((z1 - z0) / step_z)))
    for k in range(1, n):
        s = z0 + (z1 - z0) * k / n
        piece((a, b), (s - wire / 2, s + wire / 2), wire_mat)
    for zz in ((z0, z0 + frame), (z1 - frame, z1)):
        if axis == 'x':
            lbx(bm, (a, b), (fixed - frame / 2, fixed + frame / 2), zz, frame_mat)
        else:
            lbx(bm, (fixed - frame / 2, fixed + frame / 2), (a, b), zz, frame_mat)


# --------------------------------------------------------------------------
# Signs
# --------------------------------------------------------------------------

def make_textures():
    from PIL import Image, ImageDraw
    os.makedirs(TEX, exist_ok=True)
    ink, cream, amber, red = (24, 22, 18), (214, 204, 176), (214, 140, 40), (150, 36, 30)

    # RESIDENTIAL ACCESS over the antechamber, with the rings it reaches.
    img = Image.new('RGB', (768, 224), (40, 58, 50))
    d = ImageDraw.Draw(img)
    d.rectangle((8, 8, 760, 216), outline=cream, width=6)
    d.text((34, 26), 'RESIDENTIAL ACCESS', font=_font(58), fill=cream)
    d.line((34, 104, 734, 104), fill=cream, width=4)
    for i, ring in enumerate('ABC'):
        cx = 92 + i * 120
        d.ellipse((cx - 42, 118, cx + 42, 202), outline=cream, width=6)
        d.text((cx - 18, 128), ring, font=_font(56), fill=cream)
    d.polygon([(470, 140), (600, 140), (600, 118), (680, 160), (600, 202), (600, 180), (470, 180)], fill=cream)
    _age(img, 81, 0.8).save(os.path.join(TEX, 'residential_sign.png'))

    # The plate on the cage's left post, wordless: the cage slipping past a lit landing, the lever thrown,
    # the pawl biting the rack.
    img = Image.new('RGB', (256, 256), (196, 168, 60))
    d = ImageDraw.Draw(img)
    d.rectangle((6, 6, 249, 249), outline=ink, width=8)
    d.rectangle((26, 30, 40, 226), fill=ink)                       # the rack
    for k in range(9):
        y = 40 + k * 21
        d.polygon([(40, y), (58, y), (40, y + 14)], fill=ink)
    d.rectangle((70, 70, 160, 170), outline=ink, width=7)           # the cage, slipping
    d.polygon([(110, 186), (130, 186), (120, 210)], fill=ink)
    d.line((54, 172, 76, 160), fill=red, width=9)                   # its pawl, biting
    d.rectangle((168, 170, 240, 182), fill=ink)                     # the landing
    d.rectangle((168, 182, 240, 190), fill=amber)
    d.ellipse((196, 122, 226, 152), fill=amber, outline=ink, width=4)   # its lamp, lit
    for a in range(0, 360, 45):
        r0, r1 = 20, 30
        d.line((211 + r0 * math.cos(math.radians(a)), 137 + r0 * math.sin(math.radians(a)),
                211 + r1 * math.cos(math.radians(a)), 137 + r1 * math.sin(math.radians(a))), fill=ink, width=4)
    d.line((92, 160, 120, 108), fill=red, width=10)                 # the lever, thrown
    d.ellipse((112, 96, 132, 116), fill=red)
    _age(img, 82, 0.5).save(os.path.join(TEX, 'cage_plate.png'))


# --------------------------------------------------------------------------
# The set
# --------------------------------------------------------------------------

def cage_materials(m):
    m['landingamber'] = emission_material('LandingAmber', (1.0, 0.55, 0.12), 0.0)
    m['stopstripe'] = emission_material('StopStripe', (0.95, 0.6, 0.14), 0.0)
    m['cagebulb'] = emission_material('CageBulb', (1.0, 0.86, 0.66), 0.0)
    m['pawlsteel'] = worn_material('PawlSteel', base=(0.3, 0.29, 0.27), dirt=(0.08, 0.06, 0.04),
                                   chip=(0.55, 0.53, 0.5), rough=0.4, chip_rough=0.3, metallic=0.85)
    # Shared materials the other chapters define; made here only when this scene is built on its own.
    fallback = {
        'iron': lambda: worn_material('CastIron', base=(0.035, 0.034, 0.032), dirt=(0.05, 0.03, 0.018),
                                      chip=(0.13, 0.12, 0.1), rough=0.75, chip_rough=0.45, metallic=0.5),
        'plate': lambda: worn_material('PlateSteel', base=(0.11, 0.115, 0.11), dirt=(0.06, 0.04, 0.025),
                                       chip=(0.2, 0.19, 0.17), rough=0.55, chip_rough=0.4, metallic=0.7),
        'letters': lambda: worn_material('LetterPaper', base=(0.55, 0.52, 0.45), dirt=(0.3, 0.27, 0.2),
                                         chip=(0.62, 0.6, 0.55), rough=0.9, chip_rough=0.9, metallic=0.0),
        'rust': lambda: simple_material('AtriumRust', (0.11, 0.048, 0.025), 0.85),
        'masonry': lambda: simple_material('AtriumMasonry', (0.15, 0.135, 0.115), 0.85),
        'sheet': lambda: simple_material('AtriumSheet', (0.075, 0.082, 0.08), 0.6, metallic=0.4),
        'tunnelbulb': lambda: emission_material('TunnelBulb', (0.95, 0.9, 0.78), 0.0),
    }
    for k, make in fallback.items():
        if k not in m:
            m[k] = make()


def build_climbs(m, coll):
    """The deck beyond the belt, the hatch housing, the conveyor gantry and the upper landing, under a
    cramped machine-room ceiling; the hall's end bulkhead; pipes and dressing."""
    rnd = random.Random(801)
    # Floors: the deck and its run under the climbs, the pit's floor, the lower landing (one slab each).
    bm = bmesh.new()
    bx(bm, (0, SHAFT[0]), (-1.6, 1.8), (-1.3, DECK))
    bx(bm, SHAFT, (-1.6, 1.8), (-1.3, PIT_Z))
    bx(bm, LANDING, (-1.6, 1.8), (-1.3, DECK))
    _obj('C8Floor', bm, [m['concrete']], coll)

    # Walls: the machine room's back wall and ceiling, the hall's end bulkhead above the belt's low ceiling,
    # the shaft's back wall up into the dark, the antechamber's back wall, its thick ceiling (the wall over
    # the lower landing) and the rock face above it, and the shaft's side walls above the openings.
    bm = bmesh.new()
    bx(bm, (0, SHAFT[0]), (1.85, 1.97), (DECK, 7.5))
    bx(bm, (0.15, SHAFT[0]), (-1.3, 1.95), (6.0, 6.25))
    bx(bm, (-0.1, 0.15), (-1.3, 1.95), (4.98, 7.5))
    bx(bm, (SHAFT[0] - 0.2, SHAFT[1] + 0.2), (SHAFT_BACK, SHAFT_BACK + 0.15), (PIT_Z, 16.0))
    bx(bm, (SHAFT[0] - 0.2, SHAFT[0]), (SHAFT_BACK, 1.95), (DECK, 6.25))      # closes the room beside the shaft
    bx(bm, (SHAFT[0] - 0.25, SHAFT[0]), (-1.3, SHAFT_BACK), (6.0, 16.0))      # the shaft's left wall over the room
    bx(bm, LANDING, (1.5, 1.62), (DECK, ANTE_CEIL))
    bx(bm, LANDING, (-1.3, 1.62), (ANTE_CEIL, 4.3))
    bx(bm, (SHAFT[1], LANDING[1]), (1.5, 1.62), (4.3, 10.0))
    bx(bm, (SHAFT[1], SHAFT[1] + 0.25), (-1.3, 1.62), (4.3, 16.0))           # the shaft's right wall
    _obj('C8Walls', bm, [m['wall']], coll)

    # Climb 1: the hatch housing, a riveted steel box under the chute from the rings, its hatch door
    # facing the camera, its lid on top, a duct from its back up through the ceiling.
    u0, u1, top = CLIMBS[0]
    bm = bmesh.new()
    bx(bm, (u0, u1), (-0.55, 1.75), (DECK, top - 0.02), 0)
    bx(bm, (u0 - 0.01, u1 + 0.01), (-0.56, 1.76), (top - 0.03, top), 1)       # lid plate
    bx(bm, (u0 + 0.08, u1 - 0.08), (-0.575, -0.555), (DECK + 0.08, top - 0.1), 1)   # the hatch door
    for z in (DECK + 0.14, top - 0.16):                                      # its hinges
        bx(bm, (u0 + 0.03, u0 + 0.1), (-0.6, -0.57), (z - 0.03, z + 0.03), 2)
    bx(bm, (u1 - 0.16, u1 - 0.1), (-0.6, -0.575), (DECK + 0.26, DECK + 0.34), 2)    # the dog handle
    for k in range(7):                                                       # rivets along the top edge
        add_sphere(bm, W(u0 + 0.05 + k * 0.083, -0.558, top - 0.06), 0.008, mat=2, seg=6)
    bx(bm, (u0 + 0.02, u1 - 0.02), (-0.565, -0.55), (top - 0.12, top - 0.07), 3)    # hazard band
    for u in (u0 + 0.015, u1 - 0.015):                                       # corner angles
        bx(bm, (u - 0.02, u + 0.02), (-0.58, -0.54), (DECK, top - 0.02), 2)
    bx(bm, (u0 + 0.05, u1 - 0.05), (1.25, 1.75), (top, 6.0), 0)                     # the duct
    for z in (2.9, 3.7, 4.5, 5.3):
        bx(bm, (u0 + 0.03, u1 - 0.03), (1.23, 1.77), (z, z + 0.05), 2)
    bx(bm, (u0 + 0.2, u1 - 0.12), (1.1, 1.25), (top + 0.25, top + 0.85), 4)          # a patch over a split
    _obj('C8Housing', bm, [m['steel'], m['shutter'], m['iron'], m['yellow'], m['rust']], coll)

    # Climb 2: the conveyor gantry, a grated deck on legs with a dead roller bed along its back half,
    # its gearbox and motor underneath, a crate left on the rollers.
    u0, u1, top = CLIMBS[1]
    bm = bmesh.new()
    bx(bm, (u0, u1), (-0.55, 0.32), (top - 0.08, top), 1)
    bx(bm, (u0, u1), (-0.58, -0.55), (top - 0.11, top - 0.01), 3)            # the fascia, painted
    for u in (u0 + 0.04, u1 - 0.04):
        for y in (-0.5, 1.12):
            bx(bm, (u - 0.03, u + 0.03), (y - 0.03, y + 0.03), (DECK, top - 0.08), 0)
    bx(bm, (u0 + 0.02, u1 - 0.02), (-0.52, -0.48), (DECK + 0.3, DECK + 0.34), 0)
    add_cyl(bm, W(u0 + 0.05, -0.52, DECK + 0.34), W(u1 - 0.05, -0.52, top - 0.12), 0.015, mat=0, seg=6)   # a brace
    for y in (0.33, 1.17):                                                     # the roller bed's side rails
        bx(bm, (u0 - 0.15, u1 + 0.02), (y - 0.025, y + 0.025), (top - 0.12, top + 0.04), 0)
    u = u0 - 0.1
    while u < u1:
        add_cyl(bm, W(u, 0.36, top - 0.03), W(u, 1.14, top - 0.03), 0.03, mat=2, seg=8)
        u += 0.09
    bx(bm, (u0 + 0.05, u1 - 0.1), (-0.48, 1.1), (DECK, top - 0.5), 4)        # gearbox and motor
    add_cyl(bm, W(u0 + 0.35, -0.5, top - 0.7), W(u0 + 0.35, -0.62, top - 0.7), 0.13, mat=4, seg=14)
    bx(bm, (u0 + 0.15, u0 + 0.6), (-0.53, -0.49), (DECK + 0.1, DECK + 0.3), 5)      # a sheet patch
    _obj('C8Gantry', bm, [m['steel'], m['plate'], m['iron'], m['yellow'], m['iron'], m['rust']], coll)
    bm = bmesh.new()
    add_box(bm, W((u0 + u1) / 2 + 0.05, 0.75, top + 0.15), (0.42, 0.42, 0.3), rot=_rz(0.12))
    _obj('C8GantryCrate', bm, [m['paper']], coll)

    # Climb 3: the upper landing, a steel deck on a patched brick pier, yellow nosing at the shaft edge,
    # its lattice gate folded back behind the lane, a dead call box.
    u0, u1, top = CLIMBS[2]
    bm = bmesh.new()
    bx(bm, (u0, u1), (-0.8, 1.85), (DECK, top - 0.1), 0)
    for row in range(6):                                                     # a bricked-up hole in it
        z = DECK + 0.32 + row * 0.085
        off = 0.06 if row % 2 else 0.0
        for k in range(3):
            ub = u0 + 0.14 + off + k * 0.13
            bx(bm, (ub, ub + 0.12), (-0.83, -0.8), (z, z + 0.075), 1)
    bx(bm, (u1 - 0.3, u1 - 0.05), (-0.82, -0.8), (top - 0.75, top - 0.35), 2)       # rust bleeding from the deck
    _obj('C8LandingPier', bm, [m['concrete'], m['masonry'], m['rust']], coll)
    bm = bmesh.new()
    bx(bm, (u0 - 0.02, u1), (-0.82, 1.85), (top - 0.1, top), 0)
    for k in range(int((u1 - u0) / 0.1)):
        bx(bm, (u0 + 0.04 + k * 0.1, u0 + 0.054 + k * 0.1), (-0.78, 1.8), (top, top + 0.002), 0)
    bx(bm, (u1 - 0.07, u1), (-0.82, 1.0), (top - 0.1, top + 0.004), 1)               # nosing at the shaft
    bx(bm, (u0 - 0.03, u0 + 0.04), (-0.82, 1.0), (top - 0.1, top + 0.004), 1)         # and at the climb
    _obj('C8UpperLanding', bm, [m['plate'], m['yellow']], coll)
    bm = bmesh.new()
    ug = u1 - 0.06
    for k in range(7):                                                       # the lattice, bunched at the back
        y = 0.42 + k * 0.075
        bx(bm, (ug - 0.008, ug + 0.008), (y - 0.007, y + 0.007), (top + 0.02, top + 2.1), 0)
        if k < 6:
            for z in (0.4, 1.0, 1.6):
                add_box(bm, W(ug, y + 0.037, top + z), (0.01, 0.1, 0.01), rot=Matrix.Rotation(0.75 * (1 if k % 2 else -1), 4, 'X'))
    bx(bm, (ug - 0.03, ug + 0.03), (-0.8, 1.0), (top + 2.12, top + 2.18), 1)        # its track
    bx(bm, (u0 + 0.2, u0 + 0.36), (1.72, 1.85), (top + 0.9, top + 1.18), 0)          # the call box
    add_sphere(bm, W(u0 + 0.28, 1.71, top + 1.08), 0.02, mat=0, seg=8)
    _obj('C8LandingGate', bm, [m['steel'], m['yellow']], coll)

    # Pipes along the machine room's back wall, turning up into the shaft; a cable tray; a dead lamp.
    bm = bmesh.new()
    for i, (y, z, r) in enumerate(((1.72, 4.6, 0.05), (1.62, 4.85, 0.035), (1.76, 2.9, 0.04))):
        add_cyl(bm, W(-0.1, y, z), W(SHAFT[0] - 0.25, y, z), r, mat=i % 2, seg=10)
        add_cyl(bm, W(SHAFT[0] - 0.25, y, z), W(SHAFT[0] - 0.25 + 0.0, y, 6.0), r, mat=i % 2, seg=10)
        for u in (0.6, 1.9, 3.0):
            bx(bm, (u - 0.02, u + 0.02), (y, 1.85), (z - r - 0.02, z + r + 0.01), 2)
    for k in range(3):                                                       # up the shaft's back wall
        x = SHAFT_U + 0.05 + k * 0.08
        add_cyl(bm, W(x, SHAFT_BACK - 0.05, 4.4 + k * 0.1), W(x, SHAFT_BACK - 0.05, 16.0), 0.025, mat=k % 2, seg=8)
    bx(bm, (0.2, SHAFT[0] - 0.3), (1.45, 1.85), (5.55, 5.59), 2)             # cable tray
    for k in range(6):
        u = 0.4 + k * 0.5
        add_cyl(bm, W(u, 1.5, 5.57), W(u + rnd.uniform(-0.05, 0.05), 1.5, 5.3 + rnd.uniform(-0.1, 0.1)), 0.008, mat=3, seg=5)
    add_cyl(bm, W(0.9, -0.2, 6.0), W(0.9, -0.2, 5.3), 0.006, mat=2, seg=5)    # the dead lamp's flex
    add_cyl(bm, W(0.9, -0.2, 5.3), W(0.9, -0.2, 5.18), 0.06, 0.13, mat=2, seg=12)
    _obj('C8Pipes', bm, [m['steel'], m['copper'], m['iron'], m['rubber']], coll)

    # Parcels fallen from the chute, on the deck beyond the belt.
    bm = bmesh.new()
    for u, y, sz, a in ((0.55, 0.85, (0.3, 0.24, 0.2), 0.3), (0.85, 1.05, (0.22, 0.2, 0.14), -0.4),
                        (0.7, 1.3, (0.34, 0.26, 0.22), 0.1)):
        add_box(bm, W(u, y, DECK + sz[2] / 2), sz, rot=_rz(a))
    _obj('C8Parcels', bm, [m['paper']], coll)


def build_shaft(m, coll):
    """The shaft: guide rails, ties up the back wall, the rack, the buffers in the pit, the stop stripe,
    the counterweight's guides, the sheave under its guard at the top, and a far glow above."""
    cx = X0 + SHAFT_U
    bm = bmesh.new()
    # Guide rails on the side walls, in front of and behind the lane (T profiles), and the ties.
    for s in (-1, 1):
        x = cx + s * 0.79
        for y in (-0.68, 0.68):
            add_box(bm, (x, y, (PIT_Z + 16.0) / 2), (0.025, 0.09, 16.0 - PIT_Z))
            add_box(bm, (x + s * 0.02, y, (PIT_Z + 16.0) / 2), (0.02, 0.025, 16.0 - PIT_Z))
    z = PIT_Z + 0.9
    while z < 16.0:
        add_box(bm, (cx, SHAFT_BACK - 0.04, z), (1.6, 0.08, 0.12))
        z += 1.9
    # The counterweight's guide rods.
    for dx in (CW_X - 0.14, CW_X + 0.14):
        add_cyl(bm, (cx + dx, BACK_Y, PIT_Z), (cx + dx, BACK_Y, SHEAVE_Z - 0.35), 0.012, seg=8)
        z = PIT_Z + 0.5
        while z < SHEAVE_Z - 0.4:
            add_box(bm, (cx + dx, (BACK_Y + SHAFT_BACK) / 2, z), (0.03, SHAFT_BACK - BACK_Y, 0.03))
            z += 1.6
    _obj('C8ShaftFrame', bm, [m['steel']], coll)

    # CageRack: a toothed bar on the back wall, the teeth's flat tops facing up (they hold a falling cage).
    bm = bmesh.new()
    rx = cx + RACK_X
    add_box(bm, (rx, BACK_Y + 0.03, sum(RACK_Z) / 2), (2 * abs(RACK_X - RACK_ROOT), 0.14, RACK_Z[1] - RACK_Z[0]))
    for z in (RACK_Z[0] + 0.3, 1.0, 2.2, 3.3):                                # brackets into the wall
        add_box(bm, (rx, (BACK_Y + SHAFT_BACK) / 2 + 0.03, z), (0.12, SHAFT_BACK - BACK_Y + 0.02, 0.06))
    tooth = RACK_TIP - RACK_ROOT
    stop_top = CAGE_LAND + PAWL_TIP_SET                                       # the tooth the pawl bites at the landing
    z0 = stop_top - RACK_PITCH * math.floor((stop_top - RACK_Z[0] - 0.1) / RACK_PITCH)
    tops = []
    z = z0
    while z < RACK_Z[1] - 0.04:
        if abs(z - stop_top) > 1e-6:
            _prism(bm, [(cx + RACK_ROOT, z - 0.065), (cx + RACK_TIP, z - 0.012), (cx + RACK_TIP, z), (cx + RACK_ROOT, z)],
                   BACK_Y - 0.04, BACK_Y + 0.04)
        tops.append(z)
        z += RACK_PITCH
    _obj('CageRack', bm, [m['iron']], coll)

    # ShaftBuffers: two spring buffers on the pit floor under the cage, rubber-capped, a yellow base.
    bm = bmesh.new()
    for dx in (-0.45, 0.45):
        add_box(bm, (cx + dx, 0.0, PIT_Z + 0.02), (0.26, 0.26, 0.04), mat=2)
        add_cyl(bm, (cx + dx, 0, PIT_Z + 0.04), (cx + dx, 0, PIT_Z + 0.08), 0.09, mat=0, seg=16)
        pts = d17.helix(Vector((cx + dx, 0, PIT_Z + 0.24)), 0.07, 0.16, 4, n=29)      # coils down from the cap
        for a, b in zip(pts, pts[1:]):
            add_cyl(bm, a, b, 0.012, mat=0, seg=4)
        add_cyl(bm, (cx + dx, 0, PIT_Z + 0.08), (cx + dx, 0, PIT_Z + 0.26), 0.035, mat=0, seg=10)
        add_cyl(bm, (cx + dx, 0, PIT_Z + 0.24), (cx + dx, 0, PIT_Z + 0.3), 0.085, mat=1, seg=16)
    _obj('ShaftBuffers', bm, [m['iron'], m['rubber'], m['yellow']], coll)

    # Debris in the pit: a split parcel, letters, a crate on its side.
    bm = bmesh.new()
    add_box(bm, (cx - 0.1, -0.45, PIT_Z + 0.07), (0.3, 0.22, 0.14), rot=_rz(0.5))
    add_box(bm, (cx + 0.15, 0.45, PIT_Z + 0.1), (0.22, 0.34, 0.2), rot=_rz(-0.3) @ Matrix.Rotation(1.4, 4, 'X'))
    for k in range(5):
        r = random.Random(810 + k)
        add_box(bm, (cx + r.uniform(-0.6, 0.6), r.uniform(-0.5, 0.5), PIT_Z + 0.005), (0.16, 0.11, 0.004), mat=1, rot=_rz(r.uniform(0, 3)))
    _obj('C8PitDebris', bm, [m['paper'], m['letters']], coll)

    # The head: a beam across the shaft, the sheave's bearings, the guard over its top half (the chains run
    # up behind it), a band brake on the sheave with a frayed cable; the sheave itself turns.
    sx = cx + SHEAVE_X
    bm = bmesh.new()
    add_box(bm, (cx, BACK_Y + 0.02, SHEAVE_Z + 0.55), (1.6, 0.3, 0.22), mat=0)
    for dy in (-0.12, 0.12):
        add_box(bm, (sx, BACK_Y + dy, SHEAVE_Z + 0.2), (0.1, 0.04, 0.5), mat=0)
    add_box(bm, (sx, BACK_Y - 0.14, SHEAVE_Z + 1.95), (0.9, 0.03, 3.9), mat=1)     # the guard: chain runs above it hidden
    add_box(bm, (sx, BACK_Y - 0.145, SHEAVE_Z + 0.02), (0.9, 0.04, 0.06), mat=2)
    add_box(bm, (sx - SHEAVE_R - 0.1, BACK_Y - 0.06, SHEAVE_Z - 0.05), (0.08, 0.06, 0.3), mat=0)  # brake arm
    add_cyl(bm, (sx - SHEAVE_R - 0.1, BACK_Y - 0.06, SHEAVE_Z - 0.2), (cx - 0.7, BACK_Y - 0.06, SHEAVE_Z - 2.6), 0.006, mat=0, seg=5)
    _obj('C8ShaftHead', bm, [m['steel'], m['sheet'], m['yellow']], coll)
    bm = bmesh.new()
    add_cyl(bm, (0, -0.035, 0), (0, 0.035, 0), SHEAVE_R - 0.02, seg=28)
    for dy in (-0.04, 0.04):
        add_cyl(bm, (0, dy - 0.008, 0), (0, dy + 0.008, 0), SHEAVE_R + 0.03, seg=28)
    add_cyl(bm, (0, -0.1, 0), (0, 0.1, 0), 0.045, seg=10)
    for k in range(5):                                                       # spokes, so it reads turning
        a = k * 2 * math.pi / 5
        add_box(bm, (math.cos(a) * SHEAVE_R * 0.45, -0.05, math.sin(a) * SHEAVE_R * 0.45), (SHEAVE_R * 0.85, 0.02, 0.04),
                rot=_ry(-a))
    ob = _obj('CageSheave', bm, [m['iron']], coll)
    ob.location = (sx, BACK_Y, SHEAVE_Z)

    # The far glow: light falling from the rings, high above the shaft's top.
    bm = bmesh.new()
    add_box(bm, (cx, 0.2, 16.1), (1.5, 1.6, 0.02))
    _obj('C8FarGlow', bm, [m['farglow']], coll)
    return tops


def build_cage(m, coll):
    """The freight cage and what rides with it (its lever, its pawl, its chain, its plate), and the
    counterweight with its chain."""
    cy0, cy1 = CAGE_Y
    h, H = CAGE_HALF, CAGE_H
    bm = bmesh.new()
    # 0 frame (safety yellow, like Lift 2's head frame), 1 mesh (steel), 2 floor (plate), 3 nosing (yellow),
    # 4 rust, 5 iron.
    lbx(bm, (-h, h), (cy0, cy1), (-0.05, 0.0), 2)                                   # the floor
    for k in range(14):
        x = -h + 0.06 + k * 0.105
        lbx(bm, (x, x + 0.012), (cy0 + 0.04, cy1 - 0.04), (0.0, 0.002), 2)
    for y in (cy0 + 0.05, 0.0, cy1 - 0.05):                                         # underframe channels
        lbx(bm, (-h, h), (y - 0.04, y + 0.04), (-0.2, -0.05), 5)
    for x in (-h + 0.04, h - 0.04):
        lbx(bm, (x - 0.04, x + 0.04), (cy0, cy1), (-0.2, -0.05), 5)
    for xs in ((-h, -h + 0.05), (h - 0.05, h)):                                      # yellow nosing at the doorways
        lbx(bm, xs, (cy0, 0.3), (-0.05, 0.004), 3)
    # Posts: four corners and the doorway posts (behind the lane, at y 0.3) on both sides.
    for x in (-h + 0.03, h - 0.03):
        for y in (cy0 + 0.03, 0.3, cy1 - 0.03):
            lbx(bm, (x - 0.03, x + 0.03), (y - 0.03, y + 0.03), (0.0, H), 0)
    # The top frame and the crosshead: a beam along y over the cage, out behind it to the chain's hitch.
    for y in (cy0 + 0.03, cy1 - 0.03):
        lbx(bm, (-h, h), (y - 0.03, y + 0.03), (H - 0.06, H), 0)
    for x in (-h + 0.03, h - 0.03):
        lbx(bm, (x - 0.03, x + 0.03), (cy0, cy1), (H - 0.06, H), 0)
    hx = HITCH[0]
    lbx(bm, (hx - 0.05, hx + 0.05), (cy0, BACK_Y + 0.05), (H, H + 0.12), 0)
    for s in (-1, 1):                                                                # braces up to the crosshead
        add_cyl(bm, (s * (h - 0.05), cy1 - 0.03, H - 0.4), (hx + s * 0.05, cy1 - 0.03, H), 0.016, mat=0, seg=6)
    lbx(bm, (hx - 0.08, hx + 0.08), (cy1 - 0.02, BACK_Y + 0.06), (H - 0.08, H), 0)    # gusset at the back
    add_torus(bm, (hx, BACK_Y, HITCH[2] + 0.02), (1, 0, 0), 0.035, 0.012, mat=5, seg=12, rseg=5)
    # Guide shoes out to the rails.
    for xs in ((-0.775, -h + 0.01), (h - 0.01, 0.775)):
        for ys in ((-0.73, cy0 + 0.02), (cy1 - 0.02, 0.73)):
            for z in (-0.12, H - 0.1):
                lbx(bm, xs, ys, (z - 0.04, z + 0.04), 5)
    # Mesh: the back to 1.05 (above it open, so the rack and the counterweight read), the sides behind the
    # lane full height, and transoms over the doorways.
    # The back mesh is torn out of its lower right corner, over the pawl: the pawl and the teeth it bites
    # read through the gap, framed by a post and a rail.
    _mesh_panel(bm, 'x', cy1 - 0.03, -h + 0.06, MESH_GAP[0], (0.03, 1.05), 0.08, 0.08, 0, 1)
    _mesh_panel(bm, 'x', cy1 - 0.03, MESH_GAP[0], h - 0.06, (MESH_GAP[1], 1.05), 0.08, 0.08, 0, 1)
    lbx(bm, (MESH_GAP[0] - 0.02, MESH_GAP[0] + 0.02), (cy1 - 0.05, cy1 - 0.01), (0.0, 1.05), 0)
    for k in range(4):                                                               # torn wire ends
        x = MESH_GAP[0] + 0.1 + k * 0.12
        add_cyl(bm, (x, cy1 - 0.03, MESH_GAP[1]), (x + 0.02 * (k % 2) - 0.01, cy1 - 0.05, MESH_GAP[1] - 0.05 - 0.02 * (k % 3)), 0.003, mat=1, seg=4)
    for s in (-1, 1):
        x = s * (h - 0.03)
        _mesh_panel(bm, 'y', x, 0.33, cy1 - 0.06, (0.03, H - 0.06), 0.09, 0.09, 0, 1)
        _mesh_panel(bm, 'y', x, cy0 + 0.06, 0.27, (1.05, H - 0.06), 0.09, 0.09, 0, 1)
    lbx(bm, (-h, h), (cy0, cy0 + 0.05), (0.0, 0.06), 0)                             # a toe board at the front
    # The side rails he grips, either side of the lane on short stanchions.
    for y in (-RAIL_Y, RAIL_Y):
        add_cyl(bm, (RAIL_X[0], y, RAIL_Z), (RAIL_X[1], y, RAIL_Z), 0.016, mat=0, seg=8)
        for x in (RAIL_X[0] + 0.02, 0.16, RAIL_X[1] - 0.02):
            add_cyl(bm, (x, y, 0.0), (x, y, RAIL_Z), 0.012, mat=0, seg=6)
    # Patches: a welded plate over a torn corner of the back mesh, a rusted strap, a sheet riveted on a side.
    lbx(bm, (-0.5, -0.18), (cy1 - 0.05, cy1 - 0.042), (0.12, 0.42), 4)
    lbx(bm, (0.08, 0.3), (cy1 - 0.05, cy1 - 0.042), (0.66, 0.82), 2)
    lbx(bm, (h - 0.045, h - 0.035), (0.36, 0.55), (0.5, 0.9), 4)
    for x, z in ((-0.48, 0.14), (-0.2, 0.14), (-0.48, 0.4), (-0.2, 0.4)):
        add_sphere(bm, (x, cy1 - 0.052, z), 0.008, mat=5, seg=6)
    # The stop pointer on the right front post at floor level, to line up with the stripe.
    lbx(bm, (h - 0.02, h + 0.02), (cy0 + 0.0, cy0 + 0.1), (-0.015, 0.015), 3)
    # The pawl's linkage: the lever's foot bracket on its post, a crank, and a rod along the floor behind
    # the rail and out through the back mesh to the pawl's tail; the pawl's bracket out behind the cage.
    lp = Vector(LEVER_PIVOT)
    pin = Vector(PAWL_PIN)
    lbx(bm, (-h + 0.03, lp.x + 0.05), (lp.y - 0.03, lp.y + 0.03), (0.0, 0.06), 5)
    add_cyl(bm, (lp.x, lp.y - 0.05, 0.03), (lp.x, lp.y + 0.05, 0.03), 0.02, mat=5, seg=10)
    add_box(bm, (lp.x + 0.02, lp.y + 0.07, 0.04), (0.1, 0.03, 0.025), mat=5)
    tail = pin + Vector((-math.cos(math.radians(PAWL_UP)), 0, -math.sin(math.radians(PAWL_UP)))) * 0.06
    bend = Vector((tail.x - 0.12, cy1 - 0.08, 0.04))
    add_cyl(bm, (lp.x + 0.07, lp.y + 0.07, 0.04), bend, 0.009, mat=5, seg=6)
    add_cyl(bm, bend, tail, 0.009, mat=5, seg=6)
    lbx(bm, (pin.x - 0.12, pin.x + 0.05), (cy1 - 0.04, BACK_Y + 0.07), (pin.z - 0.1, pin.z - 0.07), 0)   # the bracket
    for ys in ((pin.y - 0.06, pin.y - 0.045), (pin.y + 0.045, pin.y + 0.06)):            # and two cheeks on the pin
        lbx(bm, (pin.x - 0.07, pin.x + 0.05), ys, (pin.z - 0.07, pin.z + 0.05), 0)
    add_cyl(bm, (pin.x, pin.y - 0.065, pin.z), (pin.x, pin.y + 0.065, pin.z), 0.018, mat=5, seg=10)
    ob = _obj('Cage', bm, [m['yellow'], m['steel'], m['plate'], m['yellow'], m['rust'], m['iron']], coll)
    cage = ob
    cage.location = (X0 + SHAFT_U, 0.0, CAGE_TOP)

    # CagePawlLever: red, pivot at its base, modelled at rest (leaning 10 degrees toward -x).
    bm = bmesh.new()
    lean = _ry(math.radians(LEVER_REST))
    add_cyl(bm, (0, 0, 0), (0, 0, LEVER_LEN), 0.015, seg=8)
    add_cyl(bm, (0, -0.05, LEVER_LEN), (0, 0.05, LEVER_LEN), 0.024, seg=10)
    add_box(bm, (0, 0, 0.03), (0.06, 0.05, 0.06))
    bmesh.ops.transform(bm, matrix=lean, verts=bm.verts)
    ob = _obj('CagePawlLever', bm, [m['red']], coll)
    ob.parent = cage
    ob.location = LEVER_PIVOT

    # CagePawl: the dog on its pin, modelled lifted (pointing +x, up); with its tail, where the rod pulls.
    bm = bmesh.new()
    add_cyl(bm, (0, -0.035, 0), (0, 0.035, 0), 0.03, seg=12)
    up = math.radians(PAWL_UP)
    d = Vector((math.cos(up), 0, math.sin(up)))
    add_box(bm, d * PAWL_LEN * 0.5, (PAWL_LEN, 0.05, 0.04), rot=_ry(-up))
    add_box(bm, d * (PAWL_LEN - 0.02), (0.05, 0.05, 0.05), rot=_ry(-up))
    add_box(bm, -d * 0.05, (0.1, 0.04, 0.03), rot=_ry(-up))
    ob = _obj('CagePawl', bm, [m['pawlsteel']], coll)
    ob.parent = cage
    ob.location = PAWL_PIN

    # CageChain: from the hitch up, long enough to reach the sheave with the cage on its buffers; above the
    # sheave it runs on behind the guard.
    bm = bmesh.new()
    length = SHEAVE_Z - (CAGE_BOTTOM + HITCH[2]) + 0.15
    _chain(bm, HITCH[0], BACK_Y, HITCH[2] + 0.04, HITCH[2] + 0.04 + length)
    ob = _obj('CageChain', bm, [m['steel']], coll)
    ob.parent = cage

    # CageLamp: a work bulb under the top frame at the back, in a wire guard (the game can flicker it when
    # the brake gives); the guard and its box are part of the cage.
    bm = bmesh.new()
    add_sphere(bm, (-0.2, cy1 - 0.12, H - 0.2), 0.045, seg=12)
    ob = _obj('CageLamp', bm, [m['cagebulb']], coll)
    ob.parent = cage

    # CagePlate: the wordless instruction on the left post, by the lever.
    mat = _image_material('CagePlateMat', os.path.join(TEX, 'cage_plate.png'), rough=0.5)
    ob = _plane('CagePlate', (0.17, 0.17), (-h + 0.12, 0.262, 0.86), mat, coll)
    ob.parent = cage

    # CageCounterweight: a frame of cast slabs in the back right corner, origin at its hook (top centre).
    cw, cwd, cwh = CW_SIZE
    bm = bmesh.new()
    # 0 iron slabs, 1 its frame (painted yellow, so it reads passing the cage in the dark), 2 hazard band.
    for s in (-1, 1):
        lbx(bm, (s * cw / 2 - 0.018, s * cw / 2 + 0.018), (-cwd / 2, cwd / 2), (-cwh, -0.02), 1)
        for z in (-cwh + 0.08, -0.12):                                            # shoes on the guide rods
            lbx(bm, (s * 0.14 - 0.02, s * 0.14 + 0.02), (-0.03, 0.03), (z - 0.04, z + 0.04), 0)
    lbx(bm, (-cw / 2, cw / 2), (-cwd / 2, cwd / 2), (-0.09, -0.02), 1)
    lbx(bm, (-cw / 2, cw / 2), (-cwd / 2, cwd / 2), (-cwh, -cwh + 0.08), 1)
    for k in range(3):                                                             # chevrons on its foot
        x = -cw / 2 + 0.04 + k * 0.07
        add_box(bm, (x, -cwd / 2 - 0.002, -cwh + 0.04), (0.03, 0.004, 0.09), mat=2, rot=_ry(0.6))
    n = 7
    for k in range(n):
        z = -cwh + 0.09 + k * (cwh - 0.19) / n
        lbx(bm, (-cw / 2 + 0.02, cw / 2 - 0.02), (-cwd / 2 + 0.01, cwd / 2 - 0.01), (z, z + (cwh - 0.19) / n - 0.015), 0)
    add_torus(bm, (0, 0, 0.0), (1, 0, 0), 0.03, 0.011, mat=0, seg=12, rseg=5)
    ob = _obj('CageCounterweight', bm, [m['iron'], m['yellow'], m['rubber']], coll)
    cwo = ob
    cwo.location = (X0 + SHAFT_U + CW_X, BACK_Y, CW_SUM - CAGE_TOP)
    bm = bmesh.new()
    length = SHEAVE_Z - (CW_SUM - CAGE_TOP) + 0.15                            # from its lowest, at the start
    _chain(bm, 0, 0, 0.03, 0.03 + length)
    ob = _obj('CounterweightChain', bm, [m['steel']], coll)
    ob.parent = cwo
    return cage, cwo


def build_landing(m, coll):
    """The lower landing and the antechamber: the stop stripe and the amber lamp, the landing's steel
    edge, the jamb, the RESIDENTIAL ACCESS sign, a notice board, pipes, a bin."""
    stop_tooth = CAGE_LAND + PAWL_TIP_SET
    cx = X0 + SHAFT_U
    # LandingStripe: painted at the stop level, across the shaft's back wall behind the cage, along the
    # landing's edge, on the jamb, and on the tooth the pawl bites.
    bm = bmesh.new()
    bx(bm, SHAFT, (SHAFT_BACK - 0.012, SHAFT_BACK - 0.004), (CAGE_LAND - 0.05, CAGE_LAND + 0.05))
    bx(bm, (LANDING[0], LANDING[0] + 0.16), (-1.25, 1.45), (DECK - 0.002, DECK + 0.003))
    bx(bm, (LANDING[0] - 0.004, LANDING[0] + 0.004), (-1.6, 1.0), (DECK - 0.1, DECK - 0.002))
    bx(bm, (LANDING[0], LANDING[0] + 0.5), (-1.608, -1.6), (DECK - 0.12, DECK - 0.002))   # the slab's front face
    _prism(bm, [(cx + RACK_ROOT, stop_tooth - 0.065), (cx + RACK_TIP, stop_tooth - 0.012), (cx + RACK_TIP, stop_tooth),
                (cx + RACK_ROOT, stop_tooth)], BACK_Y - 0.041, BACK_Y + 0.041)
    _obj('LandingStripe', bm, [m['stopstripe']], coll)

    # The landing's steel edge and the jamb at the opening, the lamp's housing on it.
    bm = bmesh.new()
    bx(bm, (LANDING[0], LANDING[0] + 0.05), (-1.6, 1.5), (DECK - 0.12, DECK), 0)
    bx(bm, (LANDING[0] + 0.02, LANDING[0] + 0.12), (1.1, 1.5), (DECK, ANTE_CEIL), 0)
    bx(bm, (LANDING[0] + 0.02, LANDING[0] + 0.2), (-1.3, 1.5), (ANTE_CEIL - 0.14, ANTE_CEIL), 1)   # the lintel, chevrons
    bx(bm, (LANDING[0] + 0.12, LANDING[0] + 0.36), (0.78, 1.0), (ANTE_CEIL - 0.3, ANTE_CEIL - 0.14), 0)   # lamp box
    for k in range(4):                                                        # the guard's wires
        a = k * math.pi / 4
        add_torus(bm, W(LANDING[0] + 0.24, 0.89, ANTE_CEIL - 0.37), (math.cos(a), math.sin(a), 0), 0.09, 0.005, mat=0, seg=12, rseg=3)
    add_cyl(bm, W(LANDING[0] + 0.24, 1.0, ANTE_CEIL - 0.22), W(LANDING[0] + 0.24, 1.5, ANTE_CEIL - 0.05), 0.01, mat=2, seg=5)
    # The marker lamp beside the rack at the stop level, and its conduit up the wall.
    mk = SHAFT[1] - 0.1                                                       # beside the rack, right of its stop tooth
    bx(bm, (mk - 0.05, mk + 0.05), (SHAFT_BACK - 0.06, SHAFT_BACK), (CAGE_LAND + 0.1, CAGE_LAND + 0.22), 0)
    add_cyl(bm, W(mk, SHAFT_BACK - 0.03, CAGE_LAND + 0.22), W(mk, SHAFT_BACK - 0.03, ANTE_CEIL + 0.4), 0.01, mat=2, seg=5)
    _obj('C8LandingEdge', bm, [m['steel'], m['yellow'], m['rubber']], coll)
    bm = bmesh.new()
    add_sphere(bm, W(LANDING[0] + 0.24, 0.89, ANTE_CEIL - 0.37), 0.065, seg=14)
    add_sphere(bm, W(SHAFT[1] - 0.1, SHAFT_BACK - 0.07, CAGE_LAND + 0.16), 0.03, seg=10, scale=(1, 0.6, 1))
    _obj('LandingLamp', bm, [m['landingamber']], coll)

    # The antechamber: the sign, a notice board, a lamp, pipes under the ceiling, a bin, a mat.
    sign = _image_material('ResidentialSignMat', os.path.join(TEX, 'residential_sign.png'), rough=0.6)
    _plane('C8ResidentialSign', (1.5, 0.4375), W(7.15, 1.455, 2.72), sign, coll)
    bm = bmesh.new()
    bx(bm, (6.36, 7.94), (1.46, 1.5), (2.48, 2.96), 0)                         # its backing
    bx(bm, (5.8, 6.25), (1.46, 1.5), (1.95, 2.45), 1)                          # the notice board
    rnd = random.Random(820)
    for k in range(4):
        add_box(bm, W(5.9 + (k % 2) * 0.2, 1.455, 2.1 + (k // 2) * 0.2), (0.14, 0.004, 0.18), mat=2, rot=Matrix.Rotation(rnd.uniform(-0.15, 0.15), 4, 'Y'))
    for y, z, r in ((1.3, 3.15, 0.045), (1.18, 3.2, 0.03)):
        add_cyl(bm, W(LANDING[0] + 0.25, y, z), W(LANDING[1], y, z), r, mat=3, seg=10)
    add_cyl(bm, W(8.4, 1.3, DECK), W(8.4, 1.3, DECK + 0.38), 0.13, 0.15, mat=0, seg=14)   # the bin
    bx(bm, (8.2, 8.6), (1.1, 1.5), (2.7, 2.85), 0)                              # a wall lamp
    bx(bm, (6.0, 6.9), (-0.35, 0.35), (DECK, DECK + 0.006), 4)                  # a worn doormat
    _obj('C8Antechamber', bm, [m['steel'], m['wood'], m['letters'], m['copper'], m['rubber']], coll)
    bm = bmesh.new()
    add_sphere(bm, W(8.4, 1.08, 2.74), 0.04, seg=10, scale=(1.3, 0.6, 1))
    _obj('C8AnteBulb', bm, [m['tunnelbulb']], coll)


def build_set(dl01, m, coll):
    global X0
    X0 = dl01.OFF3 + BELT_END
    assert abs(X0 + LANDING[1] - (dl01.OFF4 + BELT_END)) < 1e-6, 'the cage must fill the gap between OFF3 and OFF4'
    make_textures()
    cage_materials(m)
    build_climbs(m, coll)
    build_shaft(m, coll)
    build_cage(m, coll)
    build_landing(m, coll)


# --------------------------------------------------------------------------
# D-17 clips
# --------------------------------------------------------------------------

BRACE_BODY, BRACE_ROT = -0.15, 7.0       # crouched low, leaning in
BRACE_GRIP = {s: Vector((s * (RAIL_Y - 0.015), -0.04, RAIL_Z + 0.063)) for _, s in SIDES}   # wrists just inboard of the rails: claw tips on them
BRACE_JOLTS = ((2, 1.0), (19, 0.45), (25, 0.7))   # (frame, strength): the cage shudders; loops every 48 frames


def _jolt(f, frames, decay=4.0, freq=1.25):
    """The shudders as a periodic damped ring (so the loop is seamless): sum over this and the next cycle."""
    v = 0.0
    for f0, a in BRACE_JOLTS:
        for k in (-1, 0):
            t = f - f0 - k * frames
            if t > 0:
                v += a * math.exp(-t / decay) * math.sin(t * freq)
    return v


def _kick(f, frames, decay=3.0):
    """The shudders' downward hit: a fast drop and a recovery."""
    v = 0.0
    for f0, a in BRACE_JOLTS:
        for k in (-1, 0):
            t = f - f0 - k * frames
            if t > 0:
                v += a * (t / 1.5) * math.exp(1 - t / 1.5) if t < 1.5 else a * math.exp(-(t - 1.5) / decay)
    return v


def clip_cage_brace(dl01, arm):
    """In the slipping cage (the game turns him to face along it): crouched low between the side rails, a
    claw clamped on each, braced. The cage shudders three times (frames 2, 19, 25); each one drops him onto
    his knees, rocks him, snaps the head down and whips the antenna; the claws clench tighter. Loops."""
    import build_dl02
    Clip = dl01.Clip
    frames = 48
    c = Clip(arm, 'CageBrace', frames)
    tau = 2 * math.pi
    for frame in range(1, frames + 2):
        f = frame - 1
        t = f / frames
        ring, kick = _jolt(f, frames), _kick(f, frames)
        body = (0.004 * ring, 0.006 * ring, BRACE_BODY - 0.02 * kick + 0.002 * math.sin(tau * t))
        rot = (BRACE_ROT + 3.0 * kick + 0.6 * math.sin(tau * t), 3.0 * ring, 1.2 * ring)
        hands = build_dl02.reach(BRACE_GRIP, body, rot, dl01.REST_WRIST)
        head = (-4 - rot[0] + 6 * kick + 2 * ring, -rot[1] * 0.6 + 2.0 * ring, 3 * math.sin(tau * t) - 2 * ring)
        antenna = [(-30 + 14 * _jolt(f - i, frames, decay=6, freq=1.0) + 4 * math.sin(tau * t - i), 0) for i in range(3)]
        clench = min(1.0, kick)
        c.pose(frame, body=body, body_rot=rot, head=head, antenna=antenna, hands=hands,
               hand_rot={'L': (-70, 0, 10), 'R': (-70, 0, -10)}, claws={'L': 4 - 3 * clench, 'R': 4 - 3 * clench},
               elbows={'L': 1, 'R': 1})
    c.done()


def add_clips(dl01, arm):
    clip_cage_brace(dl01, arm)
