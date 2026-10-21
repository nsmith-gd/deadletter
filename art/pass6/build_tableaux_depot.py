"""Chapter 1, pass 6 (docs/chapter1_pass6_plan.md section 3): the depot's tableaux, DL-02 and DL-05. Built in FINAL
world coordinates, after the pass 4 modules (art/dl01/build_dl01.py main() calls build_set). The remains are
art/pass6/remains.py's.

DL-02  The fans stopped. Every one of them is part of it:
         - one climbed onto the sorting table to the extract fan hanging over it, tore its grille off and fell back:
           they lie on the floor in front of the table, arms flung back, the grille on the floor by them, the fan's
           housing open over the table, the blades stopped in the dark (TableauFan, TableauFanGrille);
         - two went for the stairs and found the bulkhead shut (art/pass4's StoryWeldedDoor, its hand prints and
           nail scratches kept): they sit against it, one slumped onto the other, the pry bar dropped beside them, its
           gouges bright at the seam (TableauPryMarks);
         - the rest gave up together in the tea corner, on mailbags emptied and laid down: two sat against the
           alcove's back wall, one slumped onto the other, the third lying with their head in a lap; the crate they
           sat on at tea is gone from the alcove;
         - the stool the climber stood on lies knocked over in front of the table (art/pass4's stool at the table's
           end is gone from there);
         - a row of candles on the sorting table's back edge, gone out barely burned (TableauCandles).
       Goes: art/pass4's sorters at their posts (Sorter1 to Sorter5, SorterMailbag), the AIR order (StoryAirNotice) and
       the air gauge with its NO AIR dial and the fan over the door (StoryAirGauge). The pass 3 notice board (NIGHT SHIFT
       CUT, over the passage in) stays, smaller: an ordinary period notice.
DL-05  The food ran out.
         - the rows under sheets, laid out by the living: the sheets now lie low and flat over what has fallen in
           (RationDead01 to 09 keep their names and places, new linked meshes);
         - at the row's end the last one lies uncovered beside a folded sheet: no one was left to cover them
           (RationDead06 is now that one, in TableauDL05Remains);
         - the queue that never moved: three seated in line toward the counter's end, bowls in their laps (in
           front of the rows, behind the drag line: the counter's own front is the weigh-in's);
         - the rows moved back a little (y 1.985 to ROW_Y) to make room for the queue;
         - tally marks scratched into the counter's front by the hatch (TableauTally).
       Goes: NO RATIONS / GRADE 4 (RationNoRations).
       RationBody (the one D-17 drags): same name, origin and length; no rope or toggle now. Its bare foot bones
       stand out of the hem at its +x end, where he takes hold (FOOT_GRIP, reported by report()).

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y.
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
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bpy  # noqa: E402
import bmesh  # noqa: E402
from mathutils import Matrix, Vector, noise  # noqa: E402

import build_d17 as d17  # noqa: E402
from build_d17 import add_box, add_cyl, add_sphere, add_torus, rounded_box  # noqa: E402
import build_ration_hall as rh  # noqa: E402
import build_story_depot as sd  # noqa: E402
import remains as R  # noqa: E402

TEX = os.path.join(HERE, 'textures')

# --------------------------------------------------------------------------
# Layout
# --------------------------------------------------------------------------
# DL-02 (art/sorting_hall: TABLE 18.6 to 22.6, y -0.45 to 0.65, top 0.75; the back wall y 1.0; the tea corner's
# alcove 15.35 to 17.3, back 1.7; art/pass4: the bulkhead door, centre 17.89, its leaf's face y 0.932).
FAN = (19.78, 0.16, 2.30, 0.62, 0.40, 0.60)       # the extract fan's housing: centre x, front face y, bottom z, w, d, h
GRILLE_AT = (20.62, -0.92, 0.0, 28.0)             # the torn-off grille on the floor: x, y, z, turn
CLIMBER = ((19.95, -1.05, 0.0), 172.0)            # fallen back off the table: (loc, turn)
KNOCKED = ((19.32, -0.72, 0.0), 0.6)              # the stool they climbed from, on its side: (loc, its turn)
STOOL_GONE = (18.14, 0.40)                        # art/pass4's stool at the table's end: taken to climb from
DOOR_SITTERS = [((18.06, 0.775, 0.0), -78.0, 0.85, 'floor', 'rag', True, 0.0),       # against the bulkhead: (loc, turn,
                ((17.6, 0.79, 0.0), -104.0, 0.55, 'lap', 'apron', False, 0.6)]      #  knees, skull, coat, cap, lean)
PRY_BAR = ((18.31, 0.7, 0.012), (18.5, 0.24, 0.012))    # dropped by the right-hand one's hip, short of the table
TEA_SEATED = [((16.97, 1.54, 0.04), -96.0, 0.5, 'floor', 'cloth', 0.0),   # sat down together against the alcove's
              ((16.45, 1.54, 0.04), -84.0, 0.3, 'lap', 'apron', 0.75)]  # back wall, on mailbags, one slumped onto the other
                                                                        # (loc, turn, knees, skull, coat, lean)
TEA_LYING = ((15.66, 0.9, 0.035), 200.0)          # lying with their head in the other's lap, out under the tea table
CRATE_GONE = (16.55, 1.25)                        # art/sorting_hall's upturned crate (in TeaTable): taken for a pillow
MAILBAGS = [(16.95, 1.42, 0.05, 0.0), (16.42, 1.44, -0.06, 0.0), (16.2, 1.12, 0.35, 0.0), (15.6, 0.9, 0.3, 0.0),
            (15.0, 0.68, 0.4, 0.0), (15.9, 1.0, 0.25, 0.05)]      # (x, y, turn, z): emptied and laid down for a bed
CANDLES = [(21.05, 0.615), (21.2, 0.62), (21.36, 0.612), (21.5, 0.62), (21.66, 0.616), (21.82, 0.62)]
LORE_SCALE = 0.6

# DL-05 (art/pass3/build_ration_hall.py: the row y 1.985, feet to the camera; the counter 53.2 to 56.6, its front
# y 0.68; the drag line y 0.35 from x 51.47 to 55.63; the drum y 0.38 up to x 56.25; the hatch 56.6).
SHROUD_OF = {'RationDead01': 'flat', 'RationDead02': 'flat_hand', 'RationDead03': 'flat', 'RationDead04': 'flat_hand_r',
             'RationDead05': 'flat_hand', 'RationDead07': 'flat_child', 'RationDead08': 'flat', 'RationDead09': 'flat'}
ROW_Y = 2.12                                      # the row moved back from 1.985 to clear room in front for the queue
LAST = ((52.02, 2.1, 0.0), -90.0)                 # RationDead06: the last one, uncovered, feet to the camera
FOLDED = (52.6, 2.55, 0.0, 6.0)                   # the folded sheet beside them: x, y, z, turn
QUEUE = [((50.38, 0.95, 0.0), 2.0, 1.0), ((51.32, 0.94, 0.0), -3.0, 2.0), ((52.26, 0.95, 0.0), 3.0, 3.0)]
                                                  # seated in line toward the counter's end: (loc, turn, seed)
TALLY = (55.06, 55.8, 0.3, 0.81)                 # x0, x1, z0, z1 scratched into the counter's front by the hatch, clear
                                                  # of the drum both on the plate (to 55.03) and parked (from 55.8)

FOOT_GRIP = []                                    # filled by rebuild_body: RationBody's foot (x, y, z from its origin)


def mat(name):
    return rh.mat(name)


def delete(names):
    gone = []
    for n in names:
        ob = bpy.data.objects.get(n)
        if ob is not None:
            me = ob.data if ob.type == 'MESH' else None
            bpy.data.objects.remove(ob, do_unlink=True)
            if me is not None and me.users == 0:
                bpy.data.meshes.remove(me)
            gone.append(n)
    return gone


# --------------------------------------------------------------------------
# DL-02
# --------------------------------------------------------------------------

def _air():
    """art/pass4's story atlas (its door, steel, hole, fan and bare cells; the notice and the gauge cells unused now)."""
    path = os.path.join(sd.TEX, 'story_air.png')
    if not os.path.exists(path):
        sd.make_story_air(path)
    return sd._image_material('StoryAirMat', path, rough=0.72)


def build_fan(coll):
    """The extract fan over the sorting table: a steel housing hung from its duct, its front open where the grille was
    torn off (the screw tabs bent and bright), the dark duct and the stopped blades behind; the grille on the floor."""
    _air()
    cx, fy, z0, w, dp, h = FAN
    P = rh.Painted(sd.air_uv)
    x0, x1, z1 = cx - w / 2, cx + w / 2, z0 + h
    # The housing: four walls round a front frame, the back closed; the duct up to the ceiling.
    t = 0.035
    for a, b, c, d in ((x0, x1, z0, z0 + t), (x0, x1, z1 - t, z1), (x0, x0 + t, z0, z1), (x1 - t, x1, z0, z1)):
        P.add('steel', lambda bm, a=a, b=b, c=c, d=d: rh.rbox(bm, a, b, fy, fy + dp, c, d, p=6, cuts=2), size=0.3)
    P.add('steel', lambda bm: rh.rbox(bm, x0, x1, fy + dp - 0.02, fy + dp, z0, z1, p=6, cuts=2), size=0.3)
    P.add('steel', lambda bm: rh.rbox(bm, cx - 0.17, cx + 0.17, fy + 0.08, fy + 0.32, z1, 4.42, p=8, cuts=2), size=0.3)
    P.add('steel', lambda bm: rh.rbox(bm, cx - 0.2, cx + 0.2, fy + 0.05, fy + 0.35, z1, z1 + 0.04, p=6, cuts=2), size=0.3)
    # The lip of the front frame (where the grille was screwed on), and the dark inside.
    P.quads('hole', [[Vector((x0 + t, fy + dp - 0.025, z0 + t)), Vector((x1 - t, fy + dp - 0.025, z0 + t)),
                      Vector((x1 - t, fy + dp - 0.025, z1 - t)), Vector((x0 + t, fy + dp - 0.025, z1 - t))]])
    # The fan: the motor's drum on a spider, four blades, stopped.
    hc = Vector((cx, fy + 0.16, z0 + h / 2))
    P.add('fan', lambda bm: add_cyl(bm, hc + Vector((0, 0.16, 0)), hc - Vector((0, 0.03, 0)), 0.075, mat=0, seg=14), size=0.12)
    for k in range(3):
        a = math.radians(90 + 120 * k)
        dv = Vector((math.cos(a), 0, math.sin(a)))
        P.add('fan', lambda bm, dv=dv: add_cyl(bm, hc + Vector((0, 0.1, 0)) + dv * 0.07, hc + Vector((0, 0.1, 0)) + dv * (w / 2 - t),
                                               0.008, mat=0, seg=5), size=0.12)
    for k in range(4):
        a = math.radians(32 + 90 * k)
        dv = Vector((math.cos(a), 0, math.sin(a)))
        P.add('fan', lambda bm, dv=dv: d17.add_wedge(bm, hc + dv * 0.06, hc + dv * 0.25, 0.08, 0.13, 0.006, 0.004,
                                                     (Vector((0, 1, 0)) * 0.6 + Vector((dv.z, 0, -dv.x))).normalized(), mat=0),
              size=0.15)
    # The screw tabs, torn and bent out where the grille was wrenched off: bright steel; one corner of the frame
    # bent forward.
    rnd = random.Random(6201)
    for (x, z, sx, sz) in ((x0 + 0.03, z0 + 0.03, 1, 1), (x1 - 0.03, z0 + 0.03, -1, 1), (x0 + 0.03, z1 - 0.03, 1, -1), (x1 - 0.03, z1 - 0.03, -1, -1)):
        tilt = rnd.uniform(0.5, 1.1)
        P.add('bare', lambda bm, x=x, z=z, tilt=tilt, sx=sx: add_box(bm, (x, fy - 0.02, z), (0.05, 0.04, 0.006), mat=0,
                                                                      rot=Matrix.Rotation(sx * tilt, 4, 'X')), size=0.08)
    P.add('bare', lambda bm: add_box(bm, (x1 - 0.08, fy - 0.03, z0 + 0.02), (0.16, 0.06, 0.012), mat=0,
                                     rot=Matrix.Rotation(-0.7, 4, 'X')), size=0.1)
    fan = sd._place(P, 'TableauFan', (cx, fy, z0), coll)
    # The grille, torn off, on the floor: its frame bent at one corner, the louvres.
    G = rh.Painted(sd.air_uv)
    gw, gh = w - 0.02, h - 0.02
    for a, b, c, d in ((-gw / 2, gw / 2, 0, 0.04), (-gw / 2, gw / 2, gh - 0.04, gh), (-gw / 2, -gw / 2 + 0.04, 0, gh), (gw / 2 - 0.04, gw / 2, 0, gh)):
        G.add('steel', lambda bm, a=a, b=b, c=c, d=d: rh.rbox(bm, a, b, c, d, 0.0, 0.022, p=6, cuts=2), size=0.3)
    yy = 0.07
    while yy < gh - 0.05:
        G.add('steel', lambda bm, yy=yy: add_box(bm, (0, yy, 0.012), (gw - 0.08, 0.04, 0.006), mat=0,
                                                 rot=Matrix.Rotation(math.radians(35), 4, 'X')), size=0.3)
        yy += 0.062
    G.add('bare', lambda bm: add_box(bm, (gw / 2 - 0.02, gh - 0.02, 0.03), (0.05, 0.04, 0.006), mat=0,
                                     rot=Matrix.Rotation(0.8, 4, 'Y')), size=0.08)
    # bend: lift the far corner a little, as it landed on its own twisted frame
    for v in G.bm.verts:
        v.co.z += 0.06 * max(0.0, (v.co.x / gw + 0.5) * (v.co.y / gh)) ** 2
    G.transform(Matrix.Translation((0, -gh / 2, 0)))
    gx, gy, gz, gt = GRILLE_AT
    G.transform(Matrix.Rotation(math.radians(gt), 4, 'Z'))
    grille = sd._place(G, 'TableauFanGrille', (0, 0, 0), coll)
    grille.location = (gx, gy, gz)
    return fan, grille


def build_door_marks(coll):
    """The pry bar dropped by the one sitting against the bulkhead, and its gouges, bright, at the leaf's seam (on
    the latch side, where they worked it), over the welds; the hand prints and nail scratches are art/pass4's."""
    _air()
    cx, wy = sd.DOOR_X, sd.WALL_Y
    lw, ltop = sd.DOOR_LEAF
    ly = wy - 0.068 - 0.011
    rnd = random.Random(6202)
    P = rh.Painted(sd.air_uv)
    xs = cx + lw / 2
    for k in range(9):
        z = rnd.uniform(0.75, 1.55)
        L = rnd.uniform(0.05, 0.16)
        a = rnd.uniform(-0.5, 0.5)
        x = xs + rnd.uniform(-0.05, 0.015)
        d = Vector((math.sin(a), 0, math.cos(a)))
        r = Vector((d.z, 0, -d.x))
        c = Vector((x, ly - 0.001 * k, z))
        wd = rnd.uniform(0.008, 0.016)
        P.quads('bare', [[c - d * L / 2 - r * wd / 2, c - d * L / 2 + r * wd / 2, c + d * L / 2 + r * wd / 2, c + d * L / 2 - r * wd / 2]])
    # The weld bead bitten into where the bar's claw went in: a bright notch.
    for z in (1.02, 1.21, 1.38):
        P.add('bare', lambda bm, z=z: add_box(bm, (xs, ly - 0.004, z), (0.03, 0.01, 0.04), mat=0), size=0.06)
    # The pry bar: a hexagonal steel bar, a claw at one end bent over, a chisel at the other.
    a, b = Vector(PRY_BAR[0]), Vector(PRY_BAR[1])
    d = (b - a).normalized()
    P.add('needle', lambda bm: add_cyl(bm, a, b, 0.012, mat=0, seg=6), size=0.2)
    claw = b + d * 0.06 + Vector((0, 0, 0.05))
    P.add('needle', lambda bm: rh.sweep(bm, [b, b + d * 0.05 + Vector((0, 0, 0.015)), claw], [0.012, 0.011, 0.007], seg=6), size=0.2)
    P.add('needle', lambda bm: d17.add_wedge(bm, a, a - d * 0.05, 0.024, 0.02, 0.012, 0.003, (0, 0, 1), mat=0), size=0.2)
    return sd._place(P, 'TableauPryMarks', (cx, ly, 0.0), coll)


def build_candles(coll):
    """Candles in a row along the sorting table's back edge, stuck down in their own wax: lit when the air was going,
    gone out barely burned. Wax (CandleWax); the wicks are in the remains mesh."""
    rnd = random.Random(6203)
    bm = bmesh.new()
    wicks = []
    for k, (x, y) in enumerate(CANDLES):
        top = sd_table_top()
        hgt = rnd.uniform(0.15, 0.19)
        r = rnd.uniform(0.011, 0.014)
        add_cyl(bm, (x, y, top), (x, y, top + hgt), r, r * 0.95, mat=0, seg=10)
        add_cyl(bm, (x, y, top), (x, y, top + 0.006), r * 1.9, r * 1.6, mat=0, seg=10)          # the wax pooled at its foot
        if k % 2 == 0:                                                                       # a drip down one side
            add_cyl(bm, (x + r * 0.8, y - r * 0.4, top + hgt - 0.005), (x + r * 0.9, y - r * 0.5, top + hgt - 0.05), 0.003, 0.004, mat=0, seg=5)
        wicks.append(Vector((x, y, top + hgt)))
    d17.mesh_object('TableauCandles', bm, [mat('CandleWax')], coll)
    return wicks


def _cut_out(name, c, r, zmax):
    """Delete the faces of another module's object within r (plan) of c and under zmax: a prop taken away."""
    ob = bpy.data.objects.get(name)
    if ob is None or ob.type != 'MESH':
        return 0
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    Mw = ob.matrix_world
    kill = [f for f in bm.faces if all(math.hypot((Mw @ v.co).x - c[0], (Mw @ v.co).y - c[1]) < r and (Mw @ v.co).z < zmax
                                         for v in f.verts)]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    bm.to_mesh(ob.data)
    bm.free()
    return len(kill)


def sd_table_top():
    return 0.75


def build_dl02(coll):
    gone = delete(['Sorter1', 'Sorter2', 'Sorter3', 'Sorter4', 'Sorter5', 'SorterMailbag', 'StoryAirNotice', 'StoryAirGauge'])
    for me in [m for m in bpy.data.meshes if m.users == 0 and m.name.startswith('SorterRemains')]:
        bpy.data.meshes.remove(me)
    # The notice board over the passage in: smaller, an ordinary notice among the others.
    obs = [o for o in (bpy.data.objects.get(n) for n in ('LoreNoticeBoard', 'LoreNoticeFrame')) if o is not None]
    if obs:
        cs = [obs[0].matrix_world @ Vector(c) for c in obs[0].bound_box]
        c = sum(cs, Vector()) / 8
        S = Matrix.Translation(c) @ Matrix.Diagonal((LORE_SCALE, 1.0, LORE_SCALE, 1.0)) @ Matrix.Translation(-c)
        for o in obs:
            o.matrix_world = S @ o.matrix_world
    build_fan(coll)
    build_door_marks(coll)
    wicks = build_candles(coll)
    _cut_out('StorySortersWood', STOOL_GONE, 0.24, 0.5)
    _cut_out('StorySortersSteel', STOOL_GONE, 0.24, 0.5)
    _cut_out('TeaTable', CRATE_GONE, 0.18, 0.45)
    P = R.painted()
    (loc, turn) = CLIMBER
    R.add(P, 'fallen', R.xform(loc, turn), seed=21.0, coat='apron', trousers='cloth')
    for k, (loc, turn, knees, skull, coat, cap, lean) in enumerate(DOOR_SITTERS):
        R.add(P, 'seated', R.xform(loc, turn), seed=22.0 + k, support=True, knees=knees, skull=skull, arms='hip', coat=coat, cap=cap,
              lean=lean, detail=0.85)
    for k, (loc, turn, knees, skull, coat, lean) in enumerate(TEA_SEATED):
        R.add(P, 'seated', R.xform(loc, turn), seed=24.0 + k, support=True, knees=knees, skull=skull, coat=coat, lean=lean, detail=0.85)
    (loc, turn) = TEA_LYING
    R.add(P, 'lying', R.xform(loc, turn), seed=26.0, arms='chest', coat='rag', legs='bent', detail=0.8)
    for (x, y, a, z) in MAILBAGS:
        P.add('bag', lambda bm, x=x, y=y, a=a, z=z: rounded_box((0.74, 0.46, 0.05), Vector((x, y, 0.022 + z)), p=2.2, cuts=4,
                                                                  dents=((0.01, 5.0), (0.004, 12.0)), seed=x + y, bm=bm, mat=0,
                                                                  rot=Matrix.Rotation(a, 4, 'Z')), size=0.5)
    # The stool they climbed from, knocked over in front of the table.
    (kx, ky, kz), ka = KNOCKED
    Rk = Matrix.Translation((kx, ky, 0.15)) @ Matrix.Rotation(ka, 4, 'Z') @ Matrix.Rotation(math.radians(-88), 4, 'Y') @ \
        Matrix.Translation((0, 0, -0.225))
    P.add('wood', lambda bm: sd.stool(bm, bmesh.new(), (0, 0, 0), Rk), size=0.3)
    P.add('shoe', lambda bm: sd.stool(bmesh.new(), bm, (0, 0, 0), Rk), size=0.3)
    for w in wicks:
        P.add('dark', lambda bm, w=w: add_cyl(bm, w, w + Vector((0.002, 0, 0.012)), 0.0022, mat=0, seg=4))
    ob = P.obj('TableauDL02Remains', 'RemainsMat', coll)
    return gone, ob


# --------------------------------------------------------------------------
# DL-05
# --------------------------------------------------------------------------

def rebuild_body():
    """RationBody: the same shroud, the same name, origin and length, the rope and its toggle gone. Its feet, bare
    bone, stand up out of the hem at its +x end, toes up, side by side: D-17 takes it by them."""
    ob = bpy.data.objects.get('RationBody')
    if ob is None:
        return None
    old = ob.data
    ox = [v.co.x for v in old.vertices]
    spec = dict(rh.SHROUDS['bound'], feet=[((0.645, 0.055, 0.07), (0.16, 0.2, 0.97), (0.99, 0.0, -0.16)),
                                           ((0.645, -0.055, 0.07), (0.16, -0.2, 0.97), (0.99, 0.0, -0.16))], shins=0.055)
    rh.SHROUDS['p6_body'] = spec
    P, _ = rh.shroud('p6_body', 4.0, rope=False)
    me = P.mesh('RationBody', 'RemainsMat')
    old.name = 'RationBody_old'
    ob.data = me
    if old.users == 0:
        bpy.data.meshes.remove(old)
    me.name = 'RationBody'
    vs = [v.co for v in me.vertices]
    nx = [v.x for v in vs]
    feet = [v for v in vs if v.x > 0.55 and v.z > 0.12]
    if feet:
        c = sum(feet, Vector()) / len(feet)
        FOOT_GRIP[:] = [round(c.x, 3), 0.0, round(c.z, 3), round(max(v.z for v in feet), 3), round(max(v.x for v in feet), 3)]
    print('tableaux_depot: RationBody x %.3f..%.3f (was %.3f..%.3f), foot grip %s' % (min(nx), max(nx), min(ox), max(ox), FOOT_GRIP))
    return ob


def _folded_sheet(P, x, y, z, turn):
    """A sheet folded in four, squared off, laid ready: the next one's."""
    Rz = Matrix.Rotation(math.radians(turn), 4, 'Z')
    for k in range(4):
        P.add('sheet', lambda bm, k=k: rounded_box((0.46 - 0.004 * k, 0.34 - 0.003 * k, 0.018), Vector((x, y, z + 0.01 + 0.017 * k)),
                                                   p=3.0, cuts=3, dents=((0.0015, 9.0),), seed=k + 0.3, bm=bm, mat=0, rot=Rz), size=0.5)


def tally_texture(path):
    """Tally marks scratched deep into the counter's paint with something sharp: rows of fives, many days, the rows
    drifting, the later ones shakier and shallower, the last group unfinished; pale where the paint is cut through."""
    from PIL import Image, ImageDraw, ImageFilter
    rnd = random.Random(6205)
    W, H = 1024, 704
    img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rows = 4
    for r in range(rows):
        y0 = 22 + r * 172 + rnd.uniform(-8, 8)
        slope = rnd.uniform(-0.06, 0.06)
        x = 16 + rnd.uniform(0, 24)
        n = 7 if r < rows - 1 else 4
        for g in range(n):
            k_ = (r * 7 + g) / (rows * 7)
            shaky = 1.0 + 6.0 * k_
            fade = max(120, 245 - int(120 * k_))
            yy = y0 + slope * (x - 16)
            strokes = 5 if not (r == rows - 1 and g == n - 1) else 2
            for k in range(strokes):
                L = rnd.uniform(118, 140)
                if k < 4:
                    xx = x + k * rnd.uniform(24, 30)
                    lean = rnd.uniform(-8, 8) * (1 + k_)
                    pts = [(xx + lean * t + rnd.uniform(-shaky, shaky), yy + t * L) for t in (0, 0.33, 0.66, 1)]
                else:
                    pts = [(x - 16, yy + L * 0.82 + rnd.uniform(-8, 8)), (x + 50, yy + L * 0.45), (x + 116, yy + 12 + rnd.uniform(-8, 8))]
                wd = rnd.choice((7, 8, 9))
                d.line([(p[0] + 3, p[1] + 3) for p in pts], fill=(10, 12, 10, fade * 3 // 4), width=wd)
                d.line(pts, fill=(214, 216, 200, fade), width=wd)
                if rnd.random() < 0.5:                                  # gone over twice
                    d.line([(p[0] + rnd.uniform(-3, 3), p[1] + 2) for p in pts], fill=(230, 230, 216, fade // 2), width=4)
            x += rnd.uniform(140, 158)
            if x > W - 120:
                break
    img = img.filter(ImageFilter.GaussianBlur(0.8))
    img.save(path)


def build_tally(coll):
    os.makedirs(TEX, exist_ok=True)
    path = os.path.join(TEX, 'scratched_tally.png')
    if not os.path.exists(path):
        tally_texture(path)
    if bpy.data.materials.get('TallyScratchMat') is None:
        rh.NEW['TallyScratchMat'] = lambda: rh._image_material('TallyScratchMat', path, 0.9, alpha=True)
    x0, x1, z0, z1 = TALLY
    return rh.decal('TableauTally', 'TallyScratchMat', x0, x1, z0, z1, rh.COUNTER_Y[0] - 0.004, coll)


def build_dl05(coll):
    gone = delete(['RationNoRations'])
    # The rows: the same places, the sheets lying low now over what has fallen in. Linked duplicates.
    meshes = {}
    for k, (name, kind) in enumerate(sorted(SHROUD_OF.items())):
        ob = bpy.data.objects.get(name)
        if ob is None:
            continue
        if kind not in meshes:
            P = R.painted()
            R.add(P, 'shrouded', None, seed=31.0 + len(meshes), kind=kind)
            meshes[kind] = P.mesh('RationShroudFlat_' + kind, 'RemainsMat')
        old = ob.data
        ob.data = meshes[kind]
        if abs(ob.location.y - 1.985) < 0.01:
            ob.location.y = ROW_Y
        if old.users == 0:
            bpy.data.meshes.remove(old)
    gone += delete(['RationDead06'])
    P = R.painted()
    (loc, turn) = LAST
    R.add(P, 'lying', R.xform(loc, turn), seed=41.0, arms='chest', coat='cloth', trousers='cloth', boots=False)
    _folded_sheet(P, *FOLDED)
    for (loc, turn, seed) in QUEUE:
        R.add(P, 'seated', R.xform(loc, turn), seed=50.0 + seed, support=False, bowl=True, detail=0.8,
              skull=('floor' if int(seed) == 3 else 'chest' if int(seed) == 2 else 'lap'), lean=[0.0, 0.3, -0.25][int(seed) - 1], coat=('cloth' if int(seed) % 3 else 'rag'), knees=0.6)
    ob = P.obj('TableauDL05Remains', 'RemainsMat', coll)
    build_tally(coll)
    rebuild_body()
    return gone, ob


# --------------------------------------------------------------------------

def build_set(dl01, m, coll):
    os.makedirs(TEX, exist_ok=True)
    bpy.context.view_layer.update()
    g2, _ = build_dl02(coll)
    g5, _ = build_dl05(coll)
    print('tableaux_depot: removed', g2 + g5)


def report():
    for pre, names in (('DL-02', ('TableauDL02Remains', 'TableauFan', 'TableauFanGrille', 'TableauPryMarks', 'TableauCandles',
                                  'StoryWeldedDoor')),
                       ('DL-05', ('TableauDL05Remains', 'TableauTally', 'RationBody') + tuple(SHROUD_OF))):
        tris, mats, n = 0, set(), 0
        for nm in names:
            ob = bpy.data.objects.get(nm)
            if ob is None:
                continue
            n += 1
            tris += sum(len(p.vertices) - 2 for p in ob.data.polygons)
            mats.update(mm.name for mm in ob.data.materials)
        print('REPORT %s objects %d tris %d materials %s' % (pre, n, tris, sorted(mats)))
    body = bpy.data.objects.get('RationBody')
    if body is not None:
        vs = [v.co for v in body.data.vertices]
        feet = [v for v in vs if v.x > 0.55 and v.z > 0.12]
        xs = [v.x for v in vs]
        if feet:
            c = sum(feet, Vector()) / len(feet)
            print('REPORT RationBody origin %s, local x %.3f..%.3f; foot bones (x > 0.55, z > 0.12): centre (%.3f, %.3f, %.3f), '
                  'x %.3f..%.3f, y %.3f..%.3f, top z %.3f' % (tuple(round(v, 3) for v in body.location), min(xs), max(xs), c.x, c.y, c.z,
                                                              min(v.x for v in feet), max(v.x for v in feet), min(v.y for v in feet),
                                                              max(v.y for v in feet), max(v.z for v in feet)))
    for nm in ('TableauDL02Remains', 'TableauFan', 'TableauFanGrille', 'TableauPryMarks', 'TableauCandles', 'TableauDL05Remains',
               'TableauTally', 'RationBody') + tuple(sorted(SHROUD_OF)):
        ob = bpy.data.objects.get(nm)
        if ob is not None:
            print('REPORT  %-20s tris %6d loc %s mesh %s' % (nm, sum(len(p.vertices) - 2 for p in ob.data.polygons),
                                                            tuple(round(v, 3) for v in ob.location), ob.data.name))


def add_clips(dl01, arm):
    pass
