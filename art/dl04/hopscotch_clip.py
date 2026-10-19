"""DL-08's long hopscotch (docs/chapter1_pass2_plan.md, section 1): D-17 plays the whole chalk court in the
tunnel, about 12 s. Called from build_dl04.add_clips, beside the short `Hopscotch` clip it extends.

The beats:
  - he stops, looks down at the chalk and tilts his head at it; a toe reaches out and taps square 1 twice;
  - he freezes, foot still out, and checks over each shoulder that nobody is watching;
  - one foot, one foot, one foot (1, 2, 3); both feet split (4 | 5); one foot on 6, where he wobbles, arms
    windmilling and antenna whipping, nearly goes over and catches himself; split (7 | 8); both feet on HOME;
  - a hop-turn on HOME, a two-claw cheer with an antenna wiggle and a single happy bounce;
  - two hops back (7 | 8, then 6 on one foot), poised as if to go again; the foot comes down, a shrug, and he
    turns back the way he was going.

The clip animates the body; the game moves the root (the same contract as the short clip). Every airborne
moment is a root window in HOPS_LONG: the game eases x by `dx` with smoothstep and lifts y by
`peak * sin(pi * k)`. The two turns are keyed on the root bone in the clip (the game does not turn him), and
the clip ends facing +x, the way he travels on. contract() gives the numbers; `python hopscotch_clip.py`
writes them to hopscotch_long.json beside this file.

Coordinates: DL-04's own x (the game adds OFF4). The chalk texture is 1080 x 360 px over 1.8 x 0.6 m
(600 px/m): its lines stand at px 20, 140, ..., 740 and HOME's arc reaches px 900, so squares are 0.2 m
along x. 4 and 7 are drawn at the top of the texture, which is the far side (+y), under his left foot as he
faces +x; 5 and 8 are on the near side, under his right.
"""
import json
import math
import os

import bpy  # noqa: F401  (loads mathutils when run on its own)
from mathutils import Vector

from build_d17 import SIDES, CLAW_REST_OPEN, smoothstep

HERE = os.path.dirname(os.path.abspath(__file__))
FPS = 24
FRAMES = 288                      # 12.0 s; the last keyed frame is f = 287
OFF4 = 30.0
DECK = 1.6
CHALK_X0, PX_PER_M = 66.4, 600.0  # build_dl04.HOP[0]; the chalk texture's scale


def _px(px):
    return round(CHALK_X0 + px / PX_PER_M, 4)


# Centre of each box along x (the pairs share one); HOME's centre sits between the 7|8 line and the arc.
SQUARES = {'1': _px(80), '2': _px(200), '3': _px(320), '4|5': _px(440), '6': _px(560), '7|8': _px(680),
           'HOME': _px(815)}
START_X = 66.30                   # his mark: toes just short of the first line (px 20, x 66.433)

# Root windows: (label, take-off f, landing f, to square, peak m, stance on landing). Stances: 'L' on the
# left foot (right tucked behind), 'R' on the right, 'split' a foot in each of a pair, 'both' feet together.
HOPS_LONG = (
    ('1', 80, 88, '1', 0.07, 'L'),
    ('2', 91, 99, '2', 0.07, 'L'),
    ('3', 102, 110, '3', 0.07, 'L'),
    ('4|5', 113, 122, '4|5', 0.08, 'split'),
    ('6', 126, 135, '6', 0.075, 'L'),           # the wobble, 135 to 160
    ('7|8', 166, 175, '7|8', 0.08, 'split'),
    ('HOME', 179, 190, 'HOME', 0.11, 'both'),
    ('hop-turn', 196, 207, 'HOME', 0.08, 'both'),
    ('bounce', 218, 225, 'HOME', 0.05, 'both'),
    ('back to 7|8', 240, 249, '7|8', 0.07, 'split'),
    ('back to 6', 252, 261, '6', 0.07, 'R'),
)
TURNS = ((196, 207, 0.0, -180.0), (274, 286, -180.0, 0.0))   # root-bone yaw, keyed in the clip: f0, f1, from, to
TOE_TAPS = (42, 48)
WOBBLE = (135, 160)
CHEER = (208, 234)
CANCEL_UNTIL = 76                 # input may cancel during the look and the toe test, not once he is hopping

STANCES = {
    'both': {'L': ((0, 0, 0), (0, 0, 0)), 'R': ((0, 0, 0), (0, 0, 0))},
    'split': {'L': ((0.036, 0, 0), (0, 0, 0)), 'R': ((-0.036, 0, 0), (0, 0, 0))},
    'L': {'L': ((-0.03, 0, 0), (0, 0, 0)), 'R': ((-0.012, 0.055, 0.075), (42, 0, 0))},
    'R': {'R': ((0.03, 0, 0), (0, 0, 0)), 'L': ((0.012, 0.055, 0.075), (42, 0, 0))},
}
SHIFT = {'both': 0.0, 'split': 0.0, 'L': 0.022, 'R': -0.022}   # body over the standing foot (+x is his left)


def contract():
    """The root motion the game needs, in game coordinates (x along the lane, y up, z toward the camera)."""
    x, hops = START_X, []
    for label, a, b, to, peak, stance in HOPS_LONG:
        nx = SQUARES[to]
        hops.append({'label': label, 'start': a, 'land': b, 'dx': round(nx - x, 4), 'to_x': round(nx + OFF4, 4),
                     'peak': peak, 'landing': {'L': 'left foot', 'R': 'right foot', 'split': 'split, both feet',
                                               'both': 'both feet together'}[stance]})
        x = nx
    return {
        'clip': 'HopscotchLong', 'fps': FPS, 'frames': FRAMES, 'end_frame': FRAMES - 1,
        'coords': 'game: x = DL-04 x + OFF4, y up, z toward the camera; frames are clip time * 24',
        'start_x': round(START_X + OFF4, 4), 'deck_y': DECK, 'lane_z': 0.0,
        'chalk': {'x0': round(CHALK_X0 + OFF4, 4), 'x1': round(CHALK_X0 + 1.8 + OFF4, 4), 'centre_z': -0.02,
                  'square_centres_x': {k: round(v + OFF4, 4) for k, v in SQUARES.items()},
                  'pairs_z': {'4, 7 (far, his left foot)': -0.153, '5, 8 (near, his right foot)': 0.113}},
        'hops': hops,
        'turns': [{'start': a, 'end': b, 'yaw_from_deg': y0, 'yaw_to_deg': y1, 'baked_in_clip': True,
                   'note': 'root-bone yaw keyed in the clip; both turns pass through -90 deg, his face to the camera; the game keeps facing +x'}
                  for a, b, y0, y1 in TURNS],
        'facing_during': [{'from': 207, 'to': 286, 'facing': -1}],
        'end_x': round(x + OFF4, 4), 'facing_after': 1,
        'cancel_until': CANCEL_UNTIL,
        'sounds': {'toe_taps': list(TOE_TAPS), 'landings': [b for _, _, b, _, _, _ in HOPS_LONG],
                   'wobble': list(WOBBLE), 'cheer': list(CHEER)},
    }


def _vtrack(keys, f):
    """track() for tuples."""
    if f <= keys[0][0]:
        return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f <= f1:
            k = smoothstep((f - f0) / (f1 - f0)) if f1 > f0 else 1.0
            return tuple(a + (b - a) * k for a, b in zip(v0, v1))
    return keys[-1][1]


def _bump(f, a, b):
    """0 -> 1 -> 0 as a half sine over [a, b]."""
    return math.sin(math.pi * (f - a) / (b - a)) if a < f < b else 0.0


def _foot_keys():
    """Per side: [(f, loc + rot)] over the whole clip, from the toe test and the hop windows."""
    flat = lambda pose: tuple(pose[0]) + tuple(pose[1])   # noqa: E731
    keys = {'L': [(0, flat(STANCES['both']['L']))], 'R': [(0, flat(STANCES['both']['R']))]}
    # The toe test: the right foot (near the camera) reaches into square 1, taps twice, stays out while he
    # looks round, then comes home.
    out = lambda z, toe=26: (0.0, -0.14, z, toe, 0, 0)   # noqa: E731
    keys['R'] += [(28, flat(STANCES['both']['R'])), (36, (0.0, -0.07, 0.05, 30, 0, 0)), (TOE_TAPS[0], out(0.014)),
                  (45, out(0.034)), (TOE_TAPS[1], out(0.014)), (66, out(0.014)), (71, (0.0, -0.06, 0.035, 12, 0, 0)),
                  (76, flat(STANCES['both']['R']))]
    prev = 'both'
    for _, a, b, _, _, stance in HOPS_LONG:
        mid = a + (b - a) * 0.5
        for side, _s in SIDES:
            p0, p1 = flat(STANCES[prev][side]), flat(STANCES[stance][side])
            air = [u + (v - u) * 0.5 for u, v in zip(p0, p1)]
            if not (prev in 'LR' and prev == stance and STANCES[prev][side][0][2] > 0):   # not the tucked foot
                air[2] += 0.03
                air[3] += 18
            keys[side] += [(a, p0), (mid, tuple(air)), (b, p1)]
        prev = stance
    # Poised on 6, facing back: the foot comes down (268 to 272).
    for side, _s in SIDES:
        keys[side] += [(268, flat(STANCES['R'][side])), (272, flat(STANCES['both'][side]))]
    return keys


def _stance_at(f):
    prev, k_prev = 'both', 0.0
    out = 'both'
    for _, a, b, _, _, stance in HOPS_LONG:
        if f >= b:
            out = stance
        elif f > a:
            return prev, stance, smoothstep((f - a) / (b - a))
        prev = stance
    if f >= 268:
        return 'R', 'both', smoothstep(min(1.0, (f - 268) / 4))
    return out, out, k_prev


def clip_hopscotch_long(dl01, arm):
    track, spring, Clip, CARRY, FOLDED = dl01.track, dl01.spring, dl01.Clip, dl01.CARRY, dl01.FOLDED
    c = Clip(arm, 'HopscotchLong', FRAMES)
    fkeys = _foot_keys()
    for frame in range(1, FRAMES + 1):
        f = frame - 1

        # --- the hops: airtime, anticipation and landing dips -------------------------------------
        air, dip, extend = 0.0, 0.0, 0.0
        for label, a, b, _, peak, stance in HOPS_LONG:
            amp = 0.05 if label == 'HOME' else 0.04 if stance in ('split', 'both') else 0.032
            air = max(air, _bump(f, a, b))
            dip += amp * (track([(a - 4, 0), (a - 1, 1), (a + 1, 0)], f) + track([(b - 1, 0), (b + 1, 1), (b + 5, 0)], f))
            extend = max(extend, _bump(f, a - 1, a + 3))
        s0, s1, ks = _stance_at(f)
        shift = SHIFT[s0] + (SHIFT[s1] - SHIFT[s0]) * ks
        one_foot = (1 if s0 in 'LR' else 0) * (1 - ks) + (1 if s1 in 'LR' else 0) * ks

        # --- beats ---------------------------------------------------------------------------------
        timid = track([(26, 0), (34, 1), (70, 1), (78, 0)], f)                 # claws up by his chest
        sneak = track([(48, 0), (52, 1), (70, 1), (74, 0)], f)                 # frozen, looking round
        wob = track([(WOBBLE[0], 0), (WOBBLE[0] + 3, 1), (150, 1), (158, 0)], f)
        cheer = track([(CHEER[0], 0), (CHEER[0] + 5, 1), (CHEER[1] - 4, 1), (CHEER[1] + 4, 0)], f, ease=lambda x: dl01.ease_back(x, 0.6))
        poised = track([(258, 0), (262, 1), (266, 1), (270, 0)], f)            # "again?"
        shrug = _bump(f, 268, 278)
        yaw = sum(track([(a, 0), (b, y1 - y0)], f) for a, b, y0, y1 in TURNS)

        # --- body ----------------------------------------------------------------------------------
        lurch = track([(137, 0), (141, 1), (146, 1.6), (151, -0.4), (156, 0.2), (160, 0)], f)
        body_z = (-dip + 0.012 * extend - 0.014 * timid - 0.008 * sneak - 0.02 * wob * abs(lurch) / 1.6
                  - 0.016 * _bump(f, 158, 168) - 0.012 * shrug + 0.008 * cheer)
        body_x = shift + 0.01 * wob * math.sin(0.5 * (f - WOBBLE[0])) - 0.018 * lurch * wob
        body_y = 0.02 * track([(34, 0), (40, 1), (64, 1), (72, 0)], f)        # weight back for the toe test
        pitch = track([(0, 0), (12, 6), (28, 5), (36, -3), (66, -3), (76, 5), (80, 4), (190, 4), (196, 2),
                       (CHEER[0], 0), (CHEER[0] + 6, -7), (CHEER[1], -5), (238, 3), (258, 4), (262, 9), (266, 10),
                       (272, 1), (288, 0)], f)
        pitch += 7 * dip / 0.04 + 3 * air + wob * 9 * lurch + 4 * shrug
        roll = 3.0 * shift / 0.022 + wob * (6 * math.sin(0.55 * (f - WOBBLE[0])) - 12 * lurch)
        roll += 4 * math.sin(f * 0.9) * track([(275, 0), (278, 1), (284, 1), (288, 0)], f)   # shuffle round
        twist = 5 * math.sin(0.5 * (f - WOBBLE[0])) * wob + 6 * math.sin((f - CHEER[0]) * 0.45) * cheer
        body_rot = (pitch, roll, twist)

        # --- head (authored in the world, then taken off the body) -----------------------------------
        hp = track([(0, 0), (12, 30), (28, 28), (36, 32), (48, 34), (52, -2), (70, -2), (74, 28), (80, 24),
                    (135, 22), (138, -8), (154, -4), (160, 16), (166, 24), (190, 20), (196, 6), (CHEER[0], 0),
                    (CHEER[0] + 6, -14), (CHEER[1] - 2, -12), (238, 20), (258, 24), (262, 34), (266, 32),
                    (270, 6), (276, 0), (288, 0)], f)
        hr = track([(8, 0), (16, 17), (24, 17), (30, -9), (36, 0), (CHEER[0], 0), (CHEER[0] + 8, 8), (CHEER[1], 0),
                    (264, 0), (268, -10), (276, 0)], f)
        hy = track([(48, 0), (53, -40), (59, -40), (64, 38), (69, 38), (73, 0)], f)
        hy += track([(156, 0), (159, 9), (162, -9), (165, 0)], f)              # a little shake: phew
        hy += track([(272, 0), (276, -12), (286, 0)], f)                       # leads the turn back
        head = (hp - pitch, hr - 0.6 * roll, hy - twist * 0.7)

        # --- antenna -------------------------------------------------------------------------------
        antenna = []
        for i in range(3):
            g = 1.0 + 0.35 * i
            ax = track([(0, 0), (10, -8), (30, -4), (48, -4), (52, -38), (70, -38), (74, 4), (80, -6),
                        (190, -6), (200, -2), (238, -6), (262, -12), (268, 10), (276, -4), (288, 0)], f) * (0.8 + 0.15 * i)
            ax -= spring(f, 8, 10, decay=5) * g + spring(f, 74, 16, decay=5, freq=1.2) * g
            ax += sum(spring(f, b, 7, decay=4, freq=1.3) for _, _, b, _, _, _ in HOPS_LONG) * g
            ax += wob * 28 * math.sin(0.7 * (f - WOBBLE[0]) - 0.6 * i) + spring(f, 158, 14, decay=5) * g
            ax += 12 * _bump(f, 160, 166)                                       # droops with the sigh
            ax += cheer * 10 * math.sin(f * 1.3 - 0.5 * i)
            az = wob * 22 * math.sin(0.55 * (f - WOBBLE[0]) - 0.8 * i) * g
            az += cheer * 14 * math.sin(f * 1.1 - 0.7 * i) * g
            az += spring(f, 207, 12, decay=5, freq=1.1) * g + spring(f, 286, -8, decay=5) * g   # the turns fling it
            az += 10 * shrug * (1 if i else 0.5)
            antenna.append((ax, az))

        # --- claws ---------------------------------------------------------------------------------
        hands, hand_rot, claws, elbows = {}, {}, {}, {}
        for side, s in SIDES:
            h = CARRY[s].lerp(FOLDED[s], 0.55 * timid)
            balance = 0.6 * one_foot + 0.4 * air
            h = h + Vector((s * 0.05 * balance, 0, 0.045 * balance))
            ph = 0.62 * (f - WOBBLE[0]) + (0 if s > 0 else math.pi)               # windmill, arms half a turn apart
            mill = Vector((s * 0.13, -0.1 * math.cos(ph), 0.22 + 0.12 * math.sin(ph)))
            h = h.lerp(CARRY[s] + mill, wob)
            up = Vector((s * 0.11, -0.05, 0.43)) + Vector((s * 0.01, 0, 0.012)) * math.sin(f * 1.2 + s)
            h = h.lerp(CARRY[s] + up, cheer)
            h = h + Vector((s * 0.02, -0.03, 0.06)) * poised + Vector((s * 0.03, 0, 0.05)) * shrug
            hands[s] = h
            rest_rot = (-24, s * 6, s * 10)
            rot = tuple(r + (t - r) * 0.55 * timid for r, t in zip(rest_rot, (-20, 0, 0)))
            rot = tuple(r + (t - r) * wob for r, t in zip(rot, (-95 + 45 * math.sin(ph), 0, -s * 25)))
            rot = tuple(r + (t - r) * cheer for r, t in zip(rot, (-160, 0, -s * 20)))
            hand_rot[side] = rot
            elbows[side] = max(0.55 * timid, wob, cheer, 0.4 * balance)
            rest = CLAW_REST_OPEN[side]
            clack = 18 + 14 * math.sin(f * 1.6 + s)                               # snapping with glee
            claws[side] = rest + (6 - rest) * timid + (34 - rest) * wob + (clack - rest) * cheer + 10 * shrug

        # --- feet ----------------------------------------------------------------------------------
        feet = {}
        for side, s in SIDES:
            v = list(_vtrack(fkeys[side], f))
            if side == 'R':                         # the tucked foot flails out to the side in the wobble
                v[0] += wob * (-0.05 * max(0.0, lurch) - 0.025 * math.sin(0.55 * (f - WOBBLE[0]) + 1))
                v[1] += wob * 0.03 * math.cos(0.55 * (f - WOBBLE[0]))
                v[3] += wob * 15 * math.sin(0.7 * (f - WOBBLE[0]))
            else:                                   # the standing foot rocks on its toes
                v[4] += wob * 7 * math.sin(0.55 * (f - WOBBLE[0]) + 0.4)
            # shuffling round on the turn back: two small steps
            v[2] += 0.024 * _bump(f, 275 if side == 'L' else 280, 280 if side == 'L' else 285)
            feet[side] = ((v[0], v[1], v[2]), (v[3], v[4], v[5]))

        c.pose(frame, body=(body_x, body_y, body_z), body_rot=body_rot, head=head, yaw=yaw, antenna=antenna,
               feet=feet, hands=hands, hand_rot=hand_rot, claws=claws, elbows=elbows)
    c.done()


if __name__ == '__main__':
    with open(os.path.join(HERE, 'hopscotch_long.json'), 'w') as fh:
        json.dump(contract(), fh, indent=2)
        fh.write('\n')
    print(json.dumps(contract(), indent=2))
