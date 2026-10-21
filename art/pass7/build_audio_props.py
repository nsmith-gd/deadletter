"""Prologue pass 7 (docs/audio_audit.md, docs/voice_script.md): the voices' props, placed in the prologue's sets. Built in
FINAL world coordinates after every other set builder (art/dl01/build_dl01.py appends this module to its PASS6 list);
other builders' objects are only read here (ray casts against the built scene), never changed. The props are
art/common/voice_props.py's.

Tannoys (they play as he passes; high, just heard):
    TannoyDepot1      tan_depot_1     DL-01, on the alcove's back wall right of the dispatch board, over the roster
    TannoyRacks       tan_racks       DL-04, high on a column of the racks hall, over the row lights
    TannoyRations     tan_rations     DL-05, on the kitchen wall over the serving hatch's shutter box
    TannoyScanner     tan_scanner     DL-06, the scanner's own speaker, on the corridor's back wall over its screen
    TannoyBridge      tan_bridge      DL-09, out at the cut bridge, on the GRADE 1-2 sign's post (big: a street horn)
    TannoyRelocation  tan_relocation  DL-10, on the lobby's back wall, left of the departures board

Voice cards (players he winds; loose cards; the secret rooms' players play when he goes in):
    VoicePlayerSorter (+ ...Crank)   card_sorter       DL-02, on a tea chest at the tea corner's mouth, before the three
                                                       who sat down together there (the shelf over the mugs is out of
                                                       his reach: 1.6 back and 1.2 up)
    VoiceCardQueue                   card_queue        DL-05, on the near thigh of the second seated in the queue
    VoicePlayerReader                card_reader       DL-06 secret room A, on a crate beside his crate table ("his desk")
    VoicePlayerHeap (+ ...Crank)     card_heap         DL-07, tipped on its side at the sorting floor's end, half-buried
                                                       in spilt returns by the parcels the slide comes down to
    VoicePlayerDen                   card_den          DL-09 secret room B, among the open treasure tins
    MusicBoxDen (+ MusicBoxDenKey)   (the music box)   DL-09 secret room B, on the floor just inside the vent, lid open
    VoiceCardLastCar                 card_lastcar      DL-10, on the stacked cases the parent with the child's coat sits on
    VoicePlayerMara (+ ...Crank)     card_mara_parent  DL-11, on a small hall table (new, in the object) under the top of
                                                       C-114's stair, left of the switch

Every object's origin is its prop's own (a player's or a card's base centre; a tannoy's wall mount); a crank's or the
key's origin is on its axis (see REPORT, printed by report()). Positions come from the built scene by ray casts at the
points named in PLACE below (each from the builders' own numbers, cited there), so a builder's small move is followed.

Coordinates: metres, Blender Z up, the lane at y = 0, travel along +x, the camera at -y. Game (x, y, z) = (x, z, -y).
"""
import math
import os
import random
import sys

import bpy
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
for _d in ('common', 'd17'):
    _p = os.path.join(HERE, '..', _d)
    if _p not in sys.path:
        sys.path.insert(0, _p)

import voice_props as VP  # noqa: E402
from build_d17 import add_box, add_cyl, rounded_box  # noqa: E402

V = Vector
DECK = 1.6                                   # DL-08 to DL-10's deck

# =====================================================================================================================
# Ray casts against the built scene
# =====================================================================================================================

_OURS = set()


def _ray(o, d, dist=20.0, skip=()):
    """The first hit from o along d, past our own objects and any named in skip: (location, object) or (None, None)."""
    dg = bpy.context.evaluated_depsgraph_get()
    sc = bpy.context.scene
    o, d = V(o), V(d).normalized()
    p = o.copy()
    for _ in range(12):
        hit, loc, nrm, idx, ob, mw = sc.ray_cast(dg, p, d, distance=dist - (p - o).length)
        if not hit:
            return None, None
        if ob.name in _OURS or ob.name in skip or ob.name.startswith('D17'):
            p = loc + d * 0.002
            continue
        return loc, ob
    return None, None


def wall(x, z, y_from=0.0, d=(0, 1, 0), skip=()):
    """The wall's face hit from (x, y_from, z) along d (default +y)."""
    loc, ob = _ray((x, y_from, z), d, skip=skip)
    if loc is None:
        raise RuntimeError('no wall at x %.2f z %.2f' % (x, z))
    return loc, ob


def ground(x, y, z_from, skip=(), only=None):
    """The surface under (x, y) cast down from z_from: (z, object name)."""
    loc, ob = _ray((x, y, z_from), (0, 0, -1), skip=skip)
    if loc is None:
        raise RuntimeError('no ground at %.2f %.2f' % (x, y))
    if only is not None and ob.name not in only:
        raise RuntimeError('ground at %.2f %.2f is %s, not %s' % (x, y, ob.name, only))
    return loc.z, ob.name


def up_to(p, skip=()):
    """Distance straight up from p to the first thing over it (a ceiling)."""
    loc, ob = _ray(p, (0, 0, 1), skip=skip)
    return (loc.z - V(p).z) if loc is not None else 1.0


# =====================================================================================================================
# Placements (Blender world). Sources: the builders named; checked against the built scene by ray casts.
# =====================================================================================================================

# Tannoys: (id, object, x, mount z, turn, tilt, aim, scale, wall ray: (y_from, direction), note)
#  - DL-01: the dispatch board is x 0.66..1.44, z 1.45..1.98 on the alcove's back wall (y 1.0; art/dl01
#    build_dispatch_board); the roster under its lamp to 1.79, the relay cabinet from 1.87; the ceiling 2.46.
#  - DL-04: the racks hall's columns (art/racks); its row lights hang at z 2.58 (RowTube*); high, over them.
#  - DL-05: the serving hatch is the kitchen wall x 56.6..56.84, its shutter box over the hatch to z 2.62 (art/pass3
#    build_ration_hall: the hatch y -0.6..0.77, 1.30 high); the tannoy on the wall's hall face (x 56.6) above the box,
#    over the hatch's middle, its horn turned out over the counter and the lane.
#  - DL-06: the scanner arch x 61.47..62.33 (SCANNER_X 61.9), its screen 62.35..62.95 at z 1.14..1.58 on the corridor's
#    back wall (ScannerScreenFrame); over the screen, aimed back at him coming through.
#  - DL-09: the cut bridge's GRADE 1-2 sign (AtriumCutBridgeSign x 115.81..120.2, y 62.0, z 9.93..12.13); on its
#    face's left end, big (scale 2.6) so it reads that far off.
#  - DL-10: the lobby's back wall (UOShell), between the UP poster and the departures board, at the bulb's height.
TANNOYS = [
    ('tan_depot_1', 'TannoyDepot1', 1.69, 1.97, 0.0, 22.0, -38.0, 1.0, (0.4, (0, 1, 0)), 'DL-01 by the dispatch board'),
    ('tan_racks', 'TannoyRacks', 38.2, 3.25, 0.0, 26.0, 40.0, 1.0, (-0.6, (0, 1, 0)), 'DL-04 racks hall, high'),
    ('tan_rations', 'TannoyRations', 56.0, 3.0, -90.0, 24.0, 28.0, 1.0, (0.3, (1, 0, 0)), 'DL-05 over the hatch'),
    ('tan_scanner', 'TannoyScanner', 62.65, 1.86, 0.0, 22.0, -42.0, 0.72, (0.0, (0, 1, 0)), "DL-06 the scanner's speaker"),
    ('tan_bridge', 'TannoyBridge', 116.1, 11.75, 0.0, 18.0, -30.0, 2.6, (58.0, (0, 1, 0)), 'DL-09 the cut bridge'),
    ('tan_relocation', 'TannoyRelocation', 120.45, 4.5, 0.0, 22.0, 38.0, 1.0, (0.4, (0, 1, 0)), 'DL-10 the lobby'),
]

# The DL-02 tea corner: the alcove x 15.35..17.3 (art/sorting_hall ALCOVE); MailSlot2's pillar x 15.82..16.17 (y to
# 0.62); the carry box at 17.4; the three sat down together at 16.45 and 16.97, y 1.54 (art/pass6 TEA_SEATED). Free
# floor between the pillar and the box, behind the lane: the tea chest at 16.6, y 0.5.
SORTER = dict(chest=(16.6, 0.52, 0.42, 0.34, 0.40), turn=-90.0, horn=22.0, lid='open')
# DL-05: the queue's second (art/pass6 build_tableaux_depot QUEUE[1]: (51.32, 0.94), turn -3, seated, facing +x):
# the card on the near thigh, the lap's front.
QUEUE_CARD = dict(at=(51.55, 0.83), turn=-28.0, out=0.3)
# DL-06 room A (art/pass6 build_ending_secrets ROOM_A, CHAIR_A; the crate table at chair x - 0.3, y + 0.62: 67.42,
# 3.97): a second crate to its left, the player on it, its horn turned to the chair.
READER = dict(crate=(66.93, 3.95, 0.40, 0.32, 0.36), turn=-90.0, horn=-70.0, lid='closed')
# DL-07: the sorting floor's end, at the pit edge (69.4); the return slide's lip at 68.78; the returned parcels from
# 68.38 (y 0.17..0.3); the points lever's reach ends 67.63, the far heap weight's starts 68.35; the carriers' line from
# y 0.34. The player tipped at 68.0, y 0.22.
HEAP = dict(at=(68.0, 0.215), turn=180.0, horn=90.0)
# DL-09 room B (ROOM_B; the fort's tins at (107.37, 2.9), (107.84, 2.78), (108.57, 2.95), lids by them; the doll's
# tea party round (108.35, 2.63); the vent 106.86..107.48 and his path (107.17, 1.9) -> (107.6, 2.35)).
DEN = dict(at=(108.2, 3.0), turn=-125.0, horn=-20.0, scale=0.9)
MUSIC_BOX = dict(at=(107.0, 2.42), turn=-115.0)
# DL-10: the queue (art/pass6 build_tableaux_ringc QUEUE[1], 121.88: two cases stacked, the coat in that lap); the
# card on the lower case's... the top case's corner nearest the lane, left of the coat's hanging sleeve.
LASTCAR_CARD = dict(at=(121.74, 0.3), turn=12.0, out=0.45)
# DL-11 C-114's hall (art/dl05: the front wall 157.6, the switch 158.72 at 0.62 on the back wall y 1.0; the stair
# (art/pass6 C114Stair) from its top at 158.13 down to its foot at 159.95, y 0.42..0.99): a small hall table under the
# stair's top end, left of the switch.
MARA = dict(table=(158.04, 0.80, 0.46, 0.32, 0.58), turn=-90.0, horn=28.0, lid='closed')

REPORT = []


def game(p):
    return (p[0], p[2], -p[1])


def _note(id_, ob, kind, p, stand=None, face=None, z=None, reach=None, extra=''):
    REPORT.append(dict(id=id_, ob=ob.name if ob is not None else '-', kind=kind, p=tuple(p), stand=stand, face=face, z=z,
                       reach=reach, extra=extra))


# =====================================================================================================================
# Small set dressing
# =====================================================================================================================

def tea_chest(K, x, y, z, w, d, h, rnd):
    """A plywood tea chest, its edges battened and its corners bound in tin."""
    wd, st = 'CrateWood', 'DepotSteel'
    rounded_box((w, d, h - 0.006), (x, y, z + (h - 0.006) / 2), p=12, cuts=2, mat=K(wd), bm=K.bm,
                dents=((0.002, 9.0),), seed=rnd.uniform(0, 9))
    for sx in (-1, 1):
        for sy in (-1, 1):
            add_box(K.bm, (x + sx * (w / 2 - 0.012), y + sy * (d / 2 - 0.012), z + h / 2), (0.032, 0.032, h), mat=K(st))
    for zz in (z + 0.012, z + h - 0.012):
        add_box(K.bm, (x, y - d / 2 - 0.002, zz), (w - 0.06, 0.008, 0.022), mat=K(wd))
        add_box(K.bm, (x, y + d / 2 + 0.002, zz), (w - 0.06, 0.008, 0.022), mat=K(wd))


def hall_table(K, x, y, w, d, h):
    """A small hall table against the wall: a top with a moulded edge, a drawer, four turned legs."""
    wd, br = 'PigeonWood', 'Brass'
    rounded_box((w, d, 0.026), (x, y, h - 0.013), p=8, cuts=2, mat=K(wd), bm=K.bm)
    rounded_box((w - 0.05, d - 0.05, 0.075), (x, y, h - 0.065), p=10, cuts=1, mat=K(wd), bm=K.bm)    # the apron
    add_box(K.bm, (x, y - d / 2 + 0.024, h - 0.065), (w * 0.5, 0.004, 0.05), mat=K(wd))              # the drawer front
    add_cyl(K.bm, (x, y - d / 2 + 0.02, h - 0.065), (x, y - d / 2 + 0.008, h - 0.065), 0.008, mat=K(br), seg=8)
    for sx in (-1, 1):
        for sy in (-1, 1):
            px, py = x + sx * (w / 2 - 0.035), y + sy * (d / 2 - 0.035)
            add_cyl(K.bm, (px, py, 0.0), (px, py, h - 0.1), 0.014, 0.018, mat=K(wd), seg=8)
            add_cyl(K.bm, (px, py, h * 0.45), (px, py, h * 0.5), 0.022, mat=K(wd), seg=8)          # a turned collar


def envelope(K, c, yaw, tilt=(0.0, 0.0), size=(0.16, 0.11)):
    M = Matrix.Translation(V(c)) @ Matrix.Rotation(yaw, 4, 'Z') @ Matrix.Rotation(tilt[0], 4, 'X') @ Matrix.Rotation(tilt[1], 4, 'Y')
    add_box(K.bm, (0, 0, 0), (size[0], size[1], 0.003), mat=K('LetterPaper'), rot=M)


# =====================================================================================================================
# The builders
# =====================================================================================================================

def _finish(K, name, coll, origin):
    ob = K.obj(name, coll, origin=origin)
    _OURS.add(ob.name)
    return ob


def build_tannoys(coll):
    obs = []
    for id_, name, x, z, turn, tilt, aim, scale, (y_from, d), note in TANNOYS:
        d = V(d)
        if d.x != 0:                                 # a wall facing -x: cast along +x at the given y
            loc, hit = _ray((x - 1.0, y_from, z), d)
        else:
            loc, hit = _ray((x, y_from, z), d)
        if loc is None:
            raise RuntimeError('tannoy %s: no wall' % id_)
        mount = V(loc)
        # the conduit up to the ceiling (or 0.6 when there is none within 2 m)
        jb = mount + V((0, 0, 0.11 * scale))
        head = up_to(jb + (Matrix.Rotation(math.radians(turn), 3, 'Z') @ V((0, -0.03 * scale, 0))))
        conduit = max(0.15, min(head / scale - 0.03, 2.0)) if head < 2.0 else 0.6
        K = VP.Kit()
        M = VP.xform(mount, turn, scale)
        info = VP.tannoy(K, M, tilt=tilt, aim=aim, conduit=conduit, conduit_dir=90.0)
        ob = _finish(K, name, coll, mount)
        obs.append(ob)
        _note(id_, ob, 'tannoy', mount, reach=None, extra='%s; wall %s; mouth %s' % (
            note, hit.name, tuple(round(v, 2) for v in info['mouth'])))
    return obs


def build_sorter(coll, rnd):
    x, y, w, d, h = SORTER['chest']
    z0, gname = ground(x, y, 1.5)
    K = VP.Kit()
    tea_chest(K, x, y, z0, w, d, h, rnd)
    base = V((x, y + 0.01, z0 + h))
    info = VP.card_player(K, VP.xform(base, SORTER['turn']), lid=SORTER['lid'], horn=SORTER['horn'], crank=False)
    # a mug left on the chest beside it, and the tea's ring
    add_cyl(K.bm, (x - 0.15, y + 0.08, z0 + h), (x - 0.15, y + 0.08, z0 + h + 0.085), 0.034, mat=K('TeaEnamel'), seg=12)
    ob = _finish(K, 'VoicePlayerSorter', coll, base)
    cr = _crank(coll, 'VoicePlayerSorterCrank', info, SORTER['turn'])
    _note('card_sorter', ob, 'card', base, stand=x, face='into the set (-z)', z=0.0,
          reach=round(info['crank_pivot'].y, 2), extra='crank %s at %s, axis %s; on %s' % (
              cr.name, tuple(round(v, 3) for v in info['crank_pivot']), tuple(round(v, 2) for v in info['crank_axis']), gname))
    return [ob, cr]


def _crank(coll, name, info, turn, extra_rot=None):
    """The crank apart, its origin on its pivot, its local x the turning axis."""
    K = VP.Kit()
    R = Matrix.Rotation(math.radians(turn), 4, 'Z') if extra_rot is None else extra_rot
    VP.crank(K, Matrix.Translation(info['crank_pivot']) @ R)
    ob = _finish(K, name, coll, info['crank_pivot'])
    return ob


def build_queue_card(coll):
    x, y = QUEUE_CARD['at']
    hits = []
    for dx, dy in ((0, 0), (0.05, 0.04), (-0.05, 0.04), (0.05, -0.04), (-0.05, -0.04)):
        zz, n = ground(x + dx, y + dy, 1.2)
        hits.append((zz, n))
    z = max(h[0] for h in hits)
    names = sorted(set(h[1] for h in hits))
    K = VP.Kit()
    M = Matrix.Translation((x, y, z - 0.004)) @ Matrix.Rotation(math.radians(QUEUE_CARD['turn']), 4, 'Z') @ Matrix.Rotation(0.12, 4, 'X')
    info = VP.card(K, M, out=QUEUE_CARD['out'])
    ob = _finish(K, 'VoiceCardQueue', coll, V((x, y, z)))
    _note('card_queue', ob, 'card', (x, y, z), stand=round(x, 2), face='into the set (-z)', z=-0.3, reach=round(y, 2),
          extra='loose card on %s' % names)
    return [ob]


def build_reader(coll, rnd):
    x, y, w, d, h = READER['crate']
    z0, gname = ground(x, y, 1.5)
    K = VP.Kit()
    tea_chest(K, x, y, z0, w, d, h, rnd)
    base = V((x, y - 0.02, z0 + h))
    VP.card_player(K, VP.xform(base, READER['turn']), lid=READER['lid'], horn=READER['horn'])
    # letters of his, stacked by it
    for k in range(4):
        envelope(K, (x + 0.12, y + 0.06, z0 + h + 0.002 + k * 0.004), rnd.uniform(-0.2, 0.2) + math.pi / 2)
    ob = _finish(K, 'VoicePlayerReader', coll, base)
    _note('card_reader', ob, 'card (secret A)', base, stand=66.95, face='game face of the secret (plays on entry)', z=-2.4,
          extra='on a crate beside his crate table; ground %s' % gname)
    return [ob]


def build_heap(coll, rnd):
    x, y = HEAP['at']
    z0, gname = ground(x, y, 1.0)
    K = VP.Kit()
    base = V((x, y, z0))
    M = VP.xform(base, HEAP['turn'])
    info = VP.card_player(K, M, lid='open', horn=HEAP['horn'], pose='tipped', crank=False)
    # half-buried: a drift of spilt returns banked against it, a parcel fallen against its foot
    L = info['local']
    for k in range(34):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(0.05, 0.3)
        px, py = x + math.cos(a) * r * 1.3, y + math.sin(a) * r * 0.45
        py = min(max(py, 0.14), 0.27)
        mound = 0.075 * math.exp(-((px - x) / 0.2) ** 2 - ((py - y) / 0.12) ** 2)
        envelope(K, (px, py, z0 + 0.002 + mound * rnd.uniform(0.3, 1.0)), rnd.uniform(0, math.pi),
                 (rnd.uniform(-0.35, 0.35), rnd.uniform(-0.35, 0.35)))
    rounded_box((0.24, 0.15, 0.13), (x + 0.25, y - 0.01, z0 + 0.064), p=8, cuts=2, mat=K('ParcelBrown'), bm=K.bm,
                rot=Matrix.Rotation(0.15, 4, 'Z') @ Matrix.Rotation(-0.2, 4, 'X'))
    ob = _finish(K, 'VoicePlayerHeap', coll, base)
    R = M @ L                                         # the tipped player's frame: the crank's axis is its local x
    cr = _crank(coll, 'VoicePlayerHeapCrank', info, 0.0, extra_rot=Matrix.Translation(-R.to_translation()) @ R)
    _note('card_heap', ob, 'card', base, stand=round(x, 2), face='into the set (-z)', z=0.0, reach=round(y, 2),
          extra='tipped; crank %s at %s, axis %s; ground %s' % (cr.name, tuple(round(v, 3) for v in info['crank_pivot']),
                                                              tuple(round(v, 2) for v in info['crank_axis']), gname))
    return [ob, cr]


def build_den(coll):
    obs = []
    x, y = DEN['at']
    z0, gname = ground(x, y, DECK + 1.0)
    K = VP.Kit()
    base = V((x, y, z0))
    VP.card_player(K, VP.xform(base, DEN['turn'], DEN['scale']), lid='open', horn=DEN['horn'])
    ob = _finish(K, 'VoicePlayerDen', coll, base)
    obs.append(ob)
    _note('card_den', ob, 'card (secret B)', base, stand=107.6, face='game face of the secret (plays on entry)', z=-2.35,
          extra='among the treasure tins; ground %s' % gname)
    mx, my = MUSIC_BOX['at']
    mz, gname = ground(mx, my, DECK + 1.0)
    K = VP.Kit()
    mbase = V((mx, my, mz))
    M = VP.xform(mbase, MUSIC_BOX['turn'])
    info = VP.music_box(K, M, lid=105.0, key=False)
    mb = _finish(K, 'MusicBoxDen', coll, mbase)
    K = VP.Kit()
    R = Matrix.Rotation(math.radians(MUSIC_BOX['turn']), 4, 'Z')
    VP.music_box_key(K, Matrix.Translation(info['key_pivot']) @ R, angle=20.0)
    key = _finish(K, 'MusicBoxDenKey', coll, info['key_pivot'])
    obs += [mb, key]
    _note('music_box', mb, 'music box', mbase, stand=107.17, face='(in the den)', z=-1.9,
          extra='key %s at %s, axis %s; ground %s' % (key.name, tuple(round(v, 3) for v in info['key_pivot']),
                                                      tuple(round(v, 2) for v in info['key_axis']), gname))
    return obs


def build_lastcar_card(coll):
    x, y = LASTCAR_CARD['at']
    hits = []
    for dx, dy in ((0, 0), (0.05, 0.05), (-0.05, 0.05), (0.05, -0.05), (-0.05, -0.05)):
        hits.append(ground(x + dx, y + dy, DECK + 1.2))
    z = max(h[0] for h in hits)
    names = sorted(set(h[1] for h in hits))
    K = VP.Kit()
    M = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(LASTCAR_CARD['turn']), 4, 'Z')
    VP.card(K, M, out=LASTCAR_CARD['out'])
    ob = _finish(K, 'VoiceCardLastCar', coll, V((x, y, z)))
    _note('card_lastcar', ob, 'card', (x, y, z), stand=round(x, 2), face='into the set (-z)', z=0.0, reach=round(y, 2),
          extra='loose card on %s' % names)
    return [ob]


def build_mara(coll, rnd):
    x, y, w, d, h = MARA['table']
    z0, gname = ground(x, y, 2.0)
    K = VP.Kit()
    M0 = Matrix.Translation((0, 0, z0))
    tk = VP.Kit()
    hall_table(tk, x, y, w, d, h)
    bmesh.ops.transform(tk.bm, matrix=M0, verts=tk.bm.verts[:])
    for f in tk.bm.faces:
        f.material_index = K(tk.mats[f.material_index])
    VP._merge_bm(K.bm, tk.bm)
    base = V((x + 0.03, y + 0.02, z0 + h))
    info = VP.card_player(K, VP.xform(base, MARA['turn']), lid=MARA['lid'], horn=MARA['horn'], crank=False)
    envelope(K, (x - 0.16, y + 0.04, z0 + h + 0.002), 0.25, size=(0.12, 0.085))     # a birthday card's envelope
    ob = _finish(K, 'VoicePlayerMara', coll, base)
    cr = _crank(coll, 'VoicePlayerMaraCrank', info, MARA['turn'])
    _note('card_mara_parent', ob, 'card', base, stand=round(x + 0.03, 2), face='into the set (-z)', z=0.0,
          reach=round(info['crank_pivot'].y, 2), extra='crank %s at %s, axis %s; table on %s' % (
              cr.name, tuple(round(v, 3) for v in info['crank_pivot']), tuple(round(v, 2) for v in info['crank_axis']), gname))
    return [ob, cr]


# =====================================================================================================================
# Entry points
# =====================================================================================================================

def tris(ob):
    return sum(len(p.vertices) - 2 for p in ob.data.polygons)


def report(objs):
    print('audio_props: %d objects' % len(objs))
    tot = 0
    mats = set()
    for ob in objs:
        t = tris(ob)
        tot += t
        ms = [m.name for m in ob.data.materials]
        mats.update(ms)
        lo = [min((ob.matrix_world @ V(c))[i] for c in ob.bound_box) for i in range(3)]
        hi = [max((ob.matrix_world @ V(c))[i] for c in ob.bound_box) for i in range(3)]
        print('audio_props: %-24s tris %5d draws %d %s  origin (%.3f, %.3f, %.3f)  x %.2f..%.2f y %.2f..%.2f z %.2f..%.2f' % (
            ob.name, t, len(ms), ms, *ob.location, lo[0], hi[0], lo[1], hi[1], lo[2], hi[2]))
    print('audio_props: total tris %d, materials %d %s' % (tot, len(mats), sorted(mats)))
    for r in REPORT:
        g = game(r['p'])
        print('audio_props: VOICE %-16s %-20s %-16s blender (%.3f, %.3f, %.3f) game (%.3f, %.3f, %.3f) stand %s face %s z %s '
              'reach %s | %s' % (r['id'], r['ob'], r['kind'], *r['p'], *g, r['stand'], r['face'], r['z'], r['reach'], r['extra']))


def build_set(dl01, m, coll):
    bpy.context.view_layer.update()
    REPORT.clear()
    rnd = random.Random(7070)
    objs = []
    objs += build_tannoys(coll)
    objs += build_sorter(coll, rnd)
    objs += build_queue_card(coll)
    objs += build_reader(coll, rnd)
    objs += build_heap(coll, rnd)
    objs += build_den(coll)
    objs += build_lastcar_card(coll)
    objs += build_mara(coll, rnd)
    bpy.context.view_layer.update()
    report(objs)


def add_clips(dl01, arm):
    pass
