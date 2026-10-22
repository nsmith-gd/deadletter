"""The prologue's scene cues, in the language of the prologue theme ("Undelivered").

Ten cues replace the chapter 1 score's cues in the prologue (DL-01 to DL-11). Each grows out of the
loop that is playing when it fires and hands back into the loop that follows, on the theme's D pedal,
tempo (60 bpm, 4 s bars), palette and mastering (the theme's master gain, read from
prologue/prologue_music.json):

    python3 prologue_cues.py --out prologue      # after compose_prologue.py; numpy, scipy, ffmpeg

Each cue's notes end at `handover`, a bar line: the game starts the next loop there, from its
loop_start, while the cue's last sounds ring out under it for a few seconds. `intro_bars` is how
long the cue spends in the incoming loop's texture before it changes anything, so the loop can be
faded out across it.

The parcel's music box keeps its sagging E (the old box can't hold the note, so it slides toward
E-flat) until the bedroom, DL-11, where it plays the true E for the first time.
"""

import argparse
import json
import os
import subprocess

import numpy as np

from compose_dl01 import (SR, cymbal_swell, env_curve, far_bell, hiss, human, legato_line, master, music_box,
                          piano, string_note, timp_roll, wind, write_wav)
from compose_prologue import (ANTHEM, ANTHEM_CHORDS, BAR, LAMENT, MARCH, PrologueMix, anvil, at, choir, drone, line,
                              machine_thud, march_bar, organ, run_down, snare_march, tannoy_chime)
from sketch_identity import crash, horn, pizz, snare_roll, taiko

RING = 6.0       # how long a cue rings on past its handover
CASCADE = [('D6', 1.0), ('C6', 0.75), ('A5', 0.55), ('G5', 0.42), ('F5', 0.9), ('E5', 0.6), ('D5', 1.8)]
UPTURN = [('D5', 0.5), ('F5', 0.5), ('G5', 0.5), ('A5', 0.5), ('C6', 1.0), ('D6', 3.0)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def pedal(m, seconds, rng, level=1.0, fade_in=0.0, fade_out=None, fade_len=2.0, start=0.0):
    """The theme's D pedal and the air, with optional fades: in from `start` over `fade_in` s, and
    out from `fade_out` s over `fade_len` s (the next loop brings its own pedal)."""
    n = int(round(seconds * SR))
    t = np.arange(n) / SR
    env = np.ones(n, np.float32) * level
    if fade_in:
        env *= np.clip((t - start) / fade_in, 0, 1) ** 1.5
    if fade_out is not None:
        env *= np.clip(1 - (t - fade_out) / fade_len, 0, 1)
    for name, kind, lvl, pan in (('D1', 'bass', 1.0, -0.15), ('D2', 'cello', 0.8, -0.3), ('A2', 'cello', 0.45, 0.05)):
        m['drone'].add(drone(name, seconds, lvl, kind, rng) * env, 0, pan)
    m['air'].add(wind(seconds, 0.05, rng) * env, 0)


def thuds(m, t0, t1, rng, level=1.0, ramp=None):
    """The far machinery, a thud on every beat from t0 to t1 (lower_works' texture)."""
    b = int(np.ceil(t0))
    while b < t1:
        v = (0.5 if b % 4 == 0 else 0.3) * level
        if ramp:
            v *= float(np.clip((b - ramp[0]) / (ramp[1] - ramp[0]), 0.15, 1))
        m['drums'].add(machine_thud(v, rng), b + human(rng, 8), 0.0)
        b += 1


def box_sag(name, vel, rng, cents=-70, start=0.12, length=0.7):
    """A music-box note that can't hold its pitch: it slides `cents` flat after it is struck."""
    x = music_box(name, vel, rng)
    n = len(x)
    t = np.arange(n) / SR
    u = np.clip((t - start) / length, 0, 1)
    speed = 2 ** (cents * (u * u * (3 - 2 * u)) / 1200)
    src = np.cumsum(speed) - speed[0]
    return np.interp(src, np.arange(n), x).astype(np.float32)


def parcel(m, t, rng, vel=0.32, gaps=(0.9, 1.2), true_e=False, pan=0.3):
    """The parcel's three notes on the music box: F, E (sagging unless true_e), D."""
    m['box'].add(music_box('F5', vel, rng), t, pan)
    e = music_box('E5', vel * 0.9, rng) if true_e else box_sag('E5', vel * 0.9, rng)
    m['box'].add(e, t + gaps[0], pan)
    m['box'].add(music_box('D5', vel, rng), t + gaps[0] + gaps[1], pan)


def box_line(m, notes, t0, vel, rng, stretch=1.0, pan=0.35, sag_e=False):
    t = t0
    for name, beats in notes:
        x = box_sag(name, vel, rng) if (sag_e and name.startswith('E')) else music_box(name, vel * rng.uniform(0.9, 1.05), rng)
        m['box'].add(x, t + human(rng, 10), pan)
        t += beats * stretch


def chord(m, names, start, dur, dyn, rng, attack=1.0, release=2.0, shape=None):
    for k, name in enumerate(names):
        o = int(name[-1])
        kind = 'bass' if o <= 1 else 'cello' if o == 2 or name in ('C3', 'D3', 'Eb3', 'F3') else 'viola' if o == 3 else 'violin'
        string_note(m['strings'], name, start, dur, dyn * (0.85 if kind in ('bass', 'cello') else 0.6), kind,
                    -0.4 + 0.8 * k / max(1, len(names) - 1), attack, release, shape=shape, rng=rng)


# ---------------------------------------------------------------------------
# The cues. Each returns its metadata; the notes go into the mix it is given.
# ---------------------------------------------------------------------------
def cue_wake(m, rng):
    """The opening, out of silence on black. The power returns with the lights at 8.17 s (dispatch's
    first line at 8.5): the pedal and a breath of choir come up, the machinery starts turning over. The
    parcel's three notes on the old music box as he answers. He stands (12.5 s): low piano. Play begins
    at 20 s, with a far bell, under dispatch's "Courier D-17. One item outstanding." When it has said
    "Deliver to: Mara. C-114, ring C." (about 23 to 26.5 s), a cello answers the name with the lament,
    the cascade flattened. It settles into the lower works by 48 s."""
    L = at(12)
    power = 8.17
    m['air'].add(wind(L + RING, 0.035, rng) * env_curve(int((L + RING) * SR), 2.5, 3), 0)
    pedal(m, L + RING, rng, fade_in=4.0, fade_out=L, start=power)     # nothing until the power returns
    m['choir'].add(choir(['D3', 'A3'], 6.0, 0.5, rng, attack=2.0, release=3.0, shape=[0.5, 1, 0.6]), power, 0.0)
    thuds(m, power + 1.0, L, rng, ramp=(power + 1.0, 20.0))
    parcel(m, 11.6, rng, vel=0.34)
    m['piano'].add(piano('D2', 0.36, 5, rng), 12.5, -0.3)
    m['piano'].add(piano('A2', 0.26, 4, rng), 12.62, -0.2)
    m['piano'].add(piano('Eb2', 0.2, 4, rng), 14.4, -0.25)
    m['bells'].add(far_bell('D3', 0.45, rng, length=11), 20.0, -0.1)
    lament = 26.6
    ln, l0 = legato_line(line(LAMENT, lament), 0, 'cello', 0.36, rng, vib_cents=14, tail=2.0,
                         shape=[(lament, 0.7), (lament + 3, 1.0), (lament + 12, 0.85), (lament + 19, 0.55)])
    m['lament'].add(ln, l0, -0.15)
    string_note(m['strings'], 'A5', 33.0, 11, 0.025, 'violin', 0.4, 3, 3, players=1, rng=rng)
    return dict(handover=L, hands_to='lower_works', intro_bars=0, starts_from='silence',
                hits={'power_on': power, 'parcel_notes': 11.6, 'stands': 12.5, 'play_begins': 20.0, 'lament': lament})


def cue_hall(m, rng):
    """DL-01, the dark depot hall, under the night-shift tannoy. Out of the lower works, the Steward's
    anthem is heard as if from far up the building: its first phrase on a distant organ, the march
    barely there beneath it. Then it thins back to the machinery."""
    L = at(8)
    pedal(m, L + RING, rng, fade_out=L)
    thuds(m, 0, L, rng, level=0.85)
    for bar, chordn in enumerate(ANTHEM_CHORDS[:4]):
        m['organ'].add(organ(chordn, BAR, 0.45 * (0.7 if bar == 0 else 1.0), rng, attack=0.6, release=1.5), at(1 + bar), 0.1)
    t = at(1)
    for name, beats in ANTHEM[:10]:
        m['horns'].add(horn(name, beats * 0.95, 0.32, rng, attack=0.15, release=0.4), t + human(rng, 5), 0.15)
        t += beats
    for bar in range(1, 5):
        march_bar(m, bar, MARCH[bar % 2], 0.1, rng)
    m['bells'].add(far_bell('D3', 0.4, rng, length=11), at(5), -0.1)
    string_note(m['strings'], 'Bb5', at(5, 2), 7, 0.022, 'violin', 0.45, 3, 3, players=1, rng=rng)
    return dict(handover=L, hands_to='lower_works', intro_bars=1)


def cue_threshold(m, rng):
    """DL-01: the bulkhead cranks open and he walks through into the sorting hall. A rise out of the
    lower works, B-flat, C minor, then an open D, with a soft choir and horns, then it settles."""
    L = at(6)
    pedal(m, L + RING, rng, fade_out=L)
    thuds(m, 0, at(1), rng, level=0.8)
    thuds(m, at(4), L, rng, level=0.7)
    for bar, names in ((1, ['Bb3', 'D4', 'F4']), (2, ['C4', 'Eb4', 'G4']), (3, ['D4', 'A4', 'D5'])):
        chord(m, names, at(bar), BAR + 0.5, 0.2 + 0.05 * (bar - 1), rng, attack=1.2, release=1.8)
    m['choir'].add(choir(['D4', 'A4'], BAR + 1, 0.55, rng, attack=1.0, release=2.5), at(3), 0.0)
    for name in ('D3', 'A3'):
        m['horns'].add(horn(name, BAR + 1, 0.35, rng, attack=1.0, release=1.5), at(3), -0.1)
    string_note(m['strings'], 'A5', at(3), 8, 0.03, 'violin', 0.4, 1.5, 3, players=1, rng=rng)
    return dict(handover=L, hands_to='lower_works', intro_bars=1)


def cue_racks(m, rng):
    """End of DL-03: the gate opens, he walks under it, and the rack lights come on row by row over
    the dormant couriers, under the tannoy's roll call. The machinery stops; a stack of low strings
    builds one row at a time (D, A, D, then the E-flat against it); a cello sings the lament's opening;
    it settles into the heaps' choir."""
    L = at(9)
    pedal(m, L + RING, rng, fade_out=L)
    thuds(m, 0, at(2), rng, level=0.8)
    rows = [('D2', 'cello'), ('A2', 'cello'), ('D3', 'cello'), ('Eb3', 'viola'), ('F3', 'viola'), ('A3', 'viola'),
            ('D4', 'violin'), ('Eb4', 'violin')]
    for k, (name, kind) in enumerate(rows):
        t = at(1) + k * 2.0
        m['metal'].add(anvil(0.12, rng, f0=1900), t, 0.35 - 0.1 * k)          # each row's lights clunk on
        string_note(m['strings'], name, t, at(7) - t, 0.11 + 0.01 * k, kind, -0.35 + 0.1 * k, 1.5, 3, rng=rng)
    ln, l0 = legato_line(line(LAMENT[:5], at(5)), 0, 'cello', 0.4, rng, vib_cents=14, tail=2.0)
    m['lament'].add(ln, l0, -0.15)
    m['choir'].add(choir(['D3', 'A3', 'F4'], 2 * BAR, 0.75, rng, attack=2.0, release=2.0), at(7), 0.0)
    return dict(handover=L, hands_to='heaps', intro_bars=1, hits={'first_row': at(1), 'rows_every': 2.0})


def cue_dead(m, rng):
    """DL-06: the scanner refuses his label. A blow at once (anvil, low horns on D against E-flat), the
    march cut off; carriers rise from the return hatch over trembling low strings and a choir swell on
    E-flat over D. Near silence and the music box as he checks his label (the parcel's notes, the E
    sagging). Then something turns: F major, and the cascade turned upward on a solo violin. Into the
    lower works."""
    L = at(10)
    pedal(m, L + RING, rng, fade_out=L)
    m['metal'].add(anvil(0.7, rng, f0=640), 0.0, 0.1)
    m['drums'].add(taiko(0.45, rng, f0=58), 0.0, 0.0)
    for name in ('D3', 'Eb3', 'A3'):
        m['horns'].add(horn(name, 1.6, 0.6, rng, attack=0.04, release=0.8), 0.0, -0.1)
    for j in range(32):
        name = ('D3', 'Eb3')[j % 2]
        string_note(m['strings'], name, 1.5 + j * 0.25 + human(rng, 4), 0.14, 0.08 + 0.002 * j, 'viola', 0.25, 0.02, 0.1,
                    players=2, rng=rng)
    m['choir'].add(choir(['D3', 'Eb4', 'Bb4'], 2 * BAR, 0.75, rng, attack=2.5, release=2.5, shape=[0.5, 1, 0.6]), at(1), 0.0)
    chord(m, ['D2', 'A2', 'Eb3', 'Bb3'], at(1), 2 * BAR, 0.18, rng, attack=2.0, release=2.5)
    parcel(m, at(4), rng, vel=0.32, gaps=(1.2, 1.6))
    # Something turns: F major, and the cascade upturned.
    m['piano'].add(piano('F2', 0.32, 5, rng), at(5), -0.3)
    for j, name in enumerate(('C3', 'A3', 'F4')):
        m['piano'].add(piano(name, 0.24, 4, rng), at(5) + 0.12 * (j + 1), 0.0)
    chord(m, ['F2', 'C3', 'A3', 'C4'], at(5), BAR, 0.16, rng, attack=1.0, release=1.5)
    chord(m, ['D2', 'Bb2', 'F3', 'D4'], at(6), BAR, 0.16, rng, attack=1.0, release=1.5)
    chord(m, ['D2', 'A2', 'D3', 'A3'], at(7), 2 * BAR, 0.13, rng, attack=1.0, release=2.0)
    for name in ('F3', 'A3'):
        m['horns'].add(horn(name, BAR, 0.3, rng, attack=0.8, release=1.0), at(5), -0.1)
    vl, v0 = legato_line(line(UPTURN, at(5, 2)), 0, 'violin', 0.32, rng, vib_cents=16, tail=1.5)
    m['solo'].add(vl, v0, 0.2)
    thuds(m, at(8), L, rng, level=0.8)
    return dict(handover=L, hands_to='lower_works', intro_bars=0, hits={'refusal': 0.0, 'label_check': at(4), 'turn': at(5)})


def cue_latch(m, rng):
    """DL-08: the pawl drops home. A warm F major rolled on the piano, a horn's A, a soft string chord;
    the music box answers F and D (it leaves the E out). Back to the pedal."""
    L = at(2)
    pedal(m, L + RING, rng, fade_out=L)
    for j, name in enumerate(('F2', 'C3', 'A3', 'F4', 'C5')):
        m['piano'].add(piano(name, 0.4 - 0.04 * j, 4, rng), 0.05 + 0.07 * j, -0.3 + 0.15 * j)
    chord(m, ['F2', 'C3', 'A3', 'C4'], 0.0, 3.5, 0.16, rng, attack=0.6, release=2.0)
    m['horns'].add(horn('A3', 3.0, 0.3, rng, attack=0.5, release=1.5), 0.2, -0.1)
    m['box'].add(music_box('F5', 0.3, rng), 1.3, 0.3)
    m['box'].add(music_box('D5', 0.3, rng), 2.5, 0.3)
    thuds(m, at(1), L, rng, level=0.7)
    return dict(handover=L, hands_to='lower_works', intro_bars=0, hits={'click': 0.0})


def cue_child(m, rng):
    """DL-11: C-114's bedroom. Out of the heaps, low: the desk scrapes clear and the music box finds the
    parcel's notes, and for the first time it holds the true E. They become the lullaby's cascade, slowly,
    over soft strings (D minor, B-flat, F, G minor), warming to F at the tree. The terminal answers (no one
    at this address): it thins to one high note over D, and to silence."""
    L = at(9)
    pedal(m, L + RING, rng, level=0.6, fade_out=at(7), fade_len=8.0)
    m['choir'].add(choir(['D3', 'A3', 'F4'], BAR, 0.42, rng, attack=0.3, release=2.0), 0.0, 0.0)
    parcel(m, 1.2, rng, vel=0.32, gaps=(1.1, 1.4), true_e=True)       # on the held marks: the true E at 2.3 s
    box_line(m, CASCADE, at(1, 2), 0.28, rng, stretch=1.6)
    for bar, names in ((1, ['D3', 'A3', 'E4', 'F4']), (2, ['Bb2', 'F3', 'A3', 'D4']), (3, ['A2', 'F3', 'C4', 'F4']),
                       (4, ['G2', 'D3', 'Bb3', 'F4'])):
        chord(m, names, at(bar), BAR + 0.3, 0.1, rng, attack=1.5, release=1.8)
        m['piano'].add(piano(names[0], 0.24, 3.5, rng), at(bar), -0.3)
        m['piano'].add(piano(names[2], 0.16, 2.5, rng), at(bar, 1.5), 0.0)
    # The tree: F, warm, a little more.
    chord(m, ['F2', 'C3', 'A3', 'C4', 'G4'], at(5), BAR + 1, 0.16, rng, attack=1.2, release=2.5)
    m['horns'].add(horn('A3', BAR, 0.25, rng, attack=1.0, release=2.0), at(5), -0.1)
    box_line(m, [('A5', 1.0), ('C6', 1.0), ('D6', 2.5)], at(5, 1), 0.24, rng, stretch=1.2)
    # The terminal answers: one high note over D, and silence.
    string_note(m['strings'], 'A5', at(6, 2), 12, 0.03, 'violin', 0.4, 2.0, 6, shape=[1, 0.9, 0.6, 0.3], players=1, rng=rng)
    string_note(m['strings'], 'D3', at(6, 2), 10, 0.07, 'cello', -0.3, 2.0, 6, shape=[1, 0.8, 0.4], rng=rng)
    return dict(handover=L, hands_to=None, intro_bars=0, hits={'true_e': 2.3, 'tree': at(5), 'terminal': at(6, 2)},
                camera=[dict(t=0.0, shot='the marks shot (as now), held to 6.0 s instead of 2.6, so the true E lands on it')])


# ---------------------------------------------------------------------------
# Directed moments. Each is written to one timeline that the camera shares: the game reads the cue's
# own audio clock (seconds since it started) to drive the shot, so the swell and the frame cannot
# drift apart. `camera` gives the keyframes in the cue's seconds; `control` is when the player gets
# the character back. Four moments, rationed: two full swells (the city, ring C), two quiet ones
# (one of many, the lit window).
# ---------------------------------------------------------------------------
def cue_kin(m, rng):
    """Moment, grief: one of many (DL-04). He stops among the couriers and the camera comes round to his
    face as he touches his chest. The music is taken away first: only the pedal under the over-the-
    shoulder look along the rows. A beat after the touch, on the held close-up, a solo cello enters.
    As the camera pulls back and up from him to the rows stretching away, strings and choir gather under
    it into one gentle swell that lands on B-flat over D exactly as the wide frame settles, holds while
    the violins sigh E-flat to D, then lets go to the music box (its E sagging) as he walks on."""
    L = at(7)
    pedal(m, L + RING, rng, fade_out=L)
    m['choir'].add(choir(['D3', 'A3'], 4.0, 0.35, rng, attack=0.5, release=2.5, shape=[1, 0.7, 0.3]), 0.0, 0.0)
    # 6.0: the cello, a beat after the touch, on the close-up.
    cello = [('D4', 3), ('C4', 1.5), ('A3', 1.5), ('G3', 2), ('A3', 1), ('D4', 4), ('C4', 2), ('Bb3', 3)]
    ln, l0 = legato_line(line(cello, 6.0), 0, 'cello', 0.36, rng, vib_cents=16, tail=2.5,
                         shape=[(6.0, 0.6), (8.0, 0.9), (15.0, 1.0), (19.0, 0.8), (22.0, 0.5)])
    m['lament'].add(ln, l0, -0.15)
    # 9.0 to 15.0: the pull back; the strings and choir gather under it.
    for t, names, dyn in ((9.0, ['D2', 'A2'], 0.09), (11.0, ['D2', 'A2', 'F3'], 0.12), (13.0, ['D2', 'Bb2', 'Eb3', 'G3'], 0.16)):
        chord(m, names, t, 2.4, dyn, rng, attack=1.4, release=1.0)
    m['choir'].add(choir(['D3', 'A3', 'F4'], 6.0, 0.4, rng, attack=4.0, release=1.0, shape=[0.3, 0.6, 1.0]), 9.0, 0.0)
    timp_roll(m['perc'], 'F2', 12.6, 15.0, 0.03, 0.45, rng, hit=0.4)
    m['perc'].add(cymbal_swell(8, 2.4, 0.014, rng, decay=1.8), 12.6, 0.2)
    # 15.0: the wide frame. B-flat over D, held; the violins sigh E-flat to D.
    chord(m, ['D2', 'Bb2', 'F3', 'D4', 'F4', 'Bb4'], 15.0, 6.0, 0.48, rng, attack=0.35, release=3.0, shape=[1, 0.9, 0.7, 0.5])
    m['choir'].add(choir(['Bb3', 'D4', 'F4'], 6.0, 1.15, rng, attack=0.3, release=3.0, shape=[1, 0.8, 0.5]), 15.0, 0.0)
    for name in ('Bb3', 'D4'):
        m['horns'].add(horn(name, 5.0, 0.55, rng, attack=0.3, release=2.0, shape=[1, 0.75, 0.45]), 15.0, -0.1)
    vl, v0 = legato_line(line([('F5', 2), ('Eb5', 2.5), ('D5', 3.5)], 15.0), 0, 'violin', 0.28, rng, vib_cents=16, tail=2.0)
    m['solo'].add(vl, v0, 0.2)
    v8, v80 = legato_line(line([('F6', 2), ('Eb6', 2.5), ('D6', 3.5)], 15.0), 0, 'violin', 0.12, rng, vib_cents=14, tail=2.0)
    m['strings'].add(v8, v80, 0.35)
    # 21: it lets go; the music box as he walks on.
    chord(m, ['D2', 'A2', 'F3', 'A3'], 21.0, 6.0, 0.1, rng, attack=1.5, release=2.5)
    parcel(m, 22.0, rng, vel=0.3, gaps=(1.1, 1.4))
    m['choir'].add(choir(['D3', 'A3', 'F4'], 4.5, 0.6, rng, attack=2.0, release=2.0), 24.0, 0.0)
    return dict(handover=L, hands_to='heaps', intro_bars=0, moment='grief',
                hits={'cello': 6.0, 'wide': 15.0, 'music_box': 22.0},
                camera=[dict(t=0.0, shot='over his shoulder along the rows (the realise shot as now)'),
                        dict(t=3.7, shot='round to his face as he touches his chest (as now; settled by 5.3)'),
                        dict(t=5.3, shot='hold close on his face and chest'),
                        dict(t=9.0, shot='start a slow pull back and up from him: he gets small, the rows stretch away'),
                        dict(t=15.0, shot='arrive on the wide over the racks, easing to a stop over the last 1 s'),
                        dict(t=21.0, shot='hold ends; ease back to the side view over 2.5 s')],
                control=22.5, notes='Stop racks (1 s fade) and the ambience at once; no voices from 0 to 21 s.')


def cue_refuge(m, rng):
    """Moment, wonder: the city (DL-09). It starts when he stops and turns at the balcony, not as he
    walks up. Two seconds of held breath: air and one high note. Then, as the camera cranes up and back
    for eight seconds, the music climbs with it, a violin line rising a step a beat over D minor, B-flat,
    F and C, choir and strings gathering, a timpani roll and a cymbal swell, and lands on F major exactly
    as the frame reaches its widest. It holds six seconds while the horns, far off, play the anthem's
    opening (the city is the Order's), then lets go through B-flat to F as the camera comes back, and the
    march creeps in for the lobby."""
    L = at(6)
    m['air'].add(wind(L + RING, 0.06, rng) * env_curve(int((L + RING) * SR), 1.0, 3), 0)
    pedal(m, L + RING, rng, fade_in=3.0, fade_out=L, start=2.0)
    string_note(m['strings'], 'A5', 0.0, 10.5, 0.03, 'violin', 0.45, 1.2, 2.0, players=1, rng=rng)
    # 2.0 to 10.0: the crane, a chord every two seconds and a step every beat.
    for t, names, dyn in ((2.0, ['D3', 'A3', 'F4'], 0.12), (4.0, ['Bb2', 'F3', 'D4'], 0.16), (6.0, ['A2', 'F3', 'C4'], 0.2),
                          (8.0, ['C3', 'G3', 'C4', 'F4'], 0.25)):
        chord(m, names, t, 2.3, dyn, rng, attack=0.9, release=0.6)
    m['choir'].add(choir(['D4', 'A4'], 8.0, 0.7, rng, attack=3.0, release=0.4, shape=[0.3, 0.6, 1.0]), 2.0, 0.0)
    climb = [('D5', 1), ('F5', 1), ('G5', 1), ('A5', 1), ('Bb5', 1), ('C6', 1), ('D6', 1), ('C6', 1)]
    for tr, kind, dyn, pan in (('', 'violin', 0.38, 0.15), ('low', 'violin', 0.2, -0.1)):
        notes = climb if not tr else [(n[:-1] + str(int(n[-1]) - 1), b) for n, b in climb]
        ln, l0 = legato_line(line(notes, 2.0), 0, kind, dyn, rng, vib_cents=14, tail=0.2,
                             shape=[(2.0, 0.5), (6.0, 0.75), (10.0, 1.0)])
        m['solo'].add(ln, l0, pan)
    timp_roll(m['perc'], 'C2', 7.4, 10.0, 0.04, 0.7, rng, hit=0.6)
    m['perc'].add(cymbal_swell(9, 2.6, 0.02, rng, decay=2.0), 7.4, 0.2)
    # 10.0: the widest frame. F major, everything, held.
    chord(m, ['F1', 'F2', 'C3', 'A3', 'C4', 'G4', 'A4'], 10.0, 6.0, 0.36, rng, attack=0.25, release=3.0, shape=[1, 0.9, 0.75, 0.6])
    m['choir'].add(choir(['F3', 'A3', 'C4', 'F4'], 6.0, 1.0, rng, attack=0.25, release=3.0, shape=[1, 0.85, 0.6]), 10.0, 0.0)
    m['organ'].add(organ(['F2', 'C3', 'F3', 'A3'], 6.0, 0.6, rng, attack=0.3, release=3.0), 10.0, 0.1)
    for name in ('F3', 'A3', 'C4'):
        m['horns'].add(horn(name, 2.5, 0.55, rng, attack=0.2, release=1.0), 10.0, -0.1)
    for tr, dyn, pan in ((0, 0.42, 0.15), (1, 0.2, 0.35)):
        ln, l0 = legato_line(line([('F6' if tr else 'F5', 6)], 10.0), 0, 'violin', dyn, rng, vib_cents=16, tail=2.5,
                             shape=[(10.0, 1.0), (14.0, 0.85), (16.0, 0.6)])
        m['solo'].add(ln, l0, pan)
    for j, name in enumerate(('F1', 'F2', 'C3', 'A3')):
        m['piano'].add(piano(name, 0.5 - 0.05 * j, 5, rng), 10.0 + 0.02 * j, -0.3 + 0.15 * j)
    t = 11.5                                    # the city's own voice, far off: the anthem's opening
    for name, beats in (('F4', 1.5), ('Bb4', 0.75), ('A4', 0.75), ('G4', 1.5)):
        m['horns'].add(horn(name, beats * 0.95, 0.3, rng, attack=0.15, release=0.6), t, 0.25)
        t += beats
    # 16.0: it lets go as the camera comes back; 20.0: the march creeps in for the lobby.
    chord(m, ['Bb1', 'Bb2', 'F3', 'D4'], 16.0, 2.2, 0.14, rng, attack=1.0, release=1.5)
    chord(m, ['F2', 'C3', 'A3'], 18.0, 2.5, 0.1, rng, attack=1.0, release=2.0)
    for bar in (5,):
        march_bar(m, bar, MARCH[bar % 2], 0.12, rng)
    snare_march(m, 5, 0.18, rng)
    return dict(handover=L, hands_to='order', intro_bars=0, starts_from='silence', moment='wonder',
                hits={'crane_starts': 2.0, 'widest': 10.0, 'release': 16.0},
                camera=[dict(t=0.0, shot='he stops and turns; the camera on his shoulder looking out into the dark (as now)'),
                        dict(t=2.0, shot='start the crane up and back (the vista shot as now, but driven by this clock)'),
                        dict(t=10.0, shot='arrive on the widest frame, easing to a stop over the last 1 s'),
                        dict(t=16.0, shot='hold ends; come back to him over 2.5 s')],
                control=18.5, notes='Trigger at the awe stop (AWE_X), not at VISTA_X0; drop the separate refuge trigger.')


def cue_ringc(m, rng):
    """Moment, grief and horror: ring C (DL-10). From UP on the counterweight's panel. The anthem's
    closing bars on the organ and horns as the car rises with the suitcase; three seconds in, the tape
    runs down, and it dies as the car leaves the frame. He lands into silence: the absence. The camera
    rises over his shoulder to look down the lane in the dark; the tannoy's chime sounds alone; the cold
    light comes up over the lane as the riser, snare and timpani climb; and on the frame where the lane's
    dead are lit, the collapse: E-flat major over D, everything. It holds eight seconds, the anthem's
    opening falling in Phrygian, then lets go to the cello's lament as he is handed back."""
    L = at(6)
    # 0 to 5.5: the anthem's close, running down (rendered apart, then laid in; see premix).
    sub = PrologueMix(20.0)
    for t, chordn in ((0.0, ['C3', 'G3', 'C4', 'Eb4']), (4.0, ['F2', 'C3', 'F3', 'A3'])):
        sub['organ'].add(organ(chordn, 4.0, 0.8, rng, attack=0.1, release=0.6), t, 0.1)
    t = 0.0
    for name, beats in (('C5', 1), ('Bb4', 1), ('A4', 1), ('G4', 1), ('F4', 4)):
        sub['horns'].add(horn(name, beats * 0.95, 0.6, rng, attack=0.06, release=0.3), t, 0.1)
        sub['horns'].add(horn(name[:-1] + str(int(name[-1]) - 1), beats * 0.95, 0.45, rng, attack=0.06, release=0.3), t, -0.15)
        t += beats
    for bar in (0, 1):
        march_bar(sub, bar, MARCH[bar % 2], 0.16, rng)
    anthem = run_down(sub.render(), 2.5, 3.0)
    # 9.5: the chime, alone in the dark.
    m['chime'].add(tannoy_chime(0.75, rng), 9.5, 0.3)
    # 9.5 to 12.0: the climb, as the light comes up.
    pedal(m, L + RING, rng, fade_in=2.0, fade_out=L, start=10.0)
    m['tail'].add(cymbal_swell(2.9, 2.5, 0.05, rng, decay=0.3), 9.5, 0.2)
    snare_roll(m['drums'], 10.2, 11.95, 0.03, 0.75, rng, 12, 30)
    timp_roll(m['perc'], 'D2', 9.6, 12.0, 0.0, 1.0, rng)
    # 12.0: the lane's dead are lit. The collapse.
    hit = 12.0
    for name in ('D1', 'D2'):
        string_note(m['strings'], name, hit, 8.0, 1.0, 'bass' if name == 'D1' else 'cello', -0.2, 0.05, 3.0, shape=[1, 0.85, 0.6], rng=rng)
    chord(m, ['Eb3', 'G3', 'Bb3', 'Eb4', 'G4', 'Bb4'], hit, 4.0, 0.55, rng, attack=0.06, release=1.0)
    chord(m, ['G2', 'D3', 'G3', 'Bb3', 'D4', 'G4'], hit + 4.0, 4.0, 0.36, rng, attack=0.6, release=3.0, shape=[1, 0.7, 0.45])
    m['choir'].add(choir(['Eb3', 'G3', 'Bb3', 'Eb4'], 4.0, 1.8, rng, attack=0.06, release=1.0), hit, 0.0)
    m['choir'].add(choir(['G3', 'Bb3', 'D4'], 4.0, 1.1, rng, attack=0.6, release=3.0, shape=[1, 0.6, 0.35]), hit + 4.0, 0.0)
    for name in ('Eb3', 'G3', 'Bb3'):
        m['horns'].add(horn(name, 3.6, 0.9, rng, attack=0.05, release=0.6), hit, -0.1)
    m['drums'].add(taiko(1.0, rng, f0=55), hit, 0.0)
    m['metal'].add(anvil(0.9, rng, f0=610), hit, 0.1)
    m['crash'].add(crash(1.0, rng, length=6.0), hit, 0.0)
    m['bells'].add(far_bell('D3', 1.0, rng, length=11), hit, -0.1)
    m['bells'].add(far_bell('A2', 0.8, rng, length=9), hit + 2.0, 0.15)
    m['drums'].add(taiko(0.6, rng), hit + 2.0, 0.0)
    fall = [('F4', 1.5), ('Bb4', 0.75), ('A4', 0.75), ('G4', 1.5), ('F4', 0.75), ('Eb4', 0.75), ('D4', 4.0)]
    for shift, kind, dyn, pan in ((0, 'violin', 0.7, 0.15), (12, 'violin', 0.32, 0.35), (-12, 'cello', 0.55, -0.3)):
        notes = [(n if not shift else n[:-1] + str(int(n[-1]) + shift // 12), b) for n, b in fall]
        ln, l0 = legato_line(line(notes, hit + 0.5), 0, kind, dyn, rng, vib_cents=16, tail=2.5,
                             shape=[(hit, 1.0), (hit + 5, 0.85), (hit + 9, 0.5)])
        m['lament'].add(ln, l0, pan)
    # 20.0: it lets go to the lament as he is handed back.
    ln, l0 = legato_line(line(LAMENT[:4], 20.0), 0, 'cello', 0.36, rng, vib_cents=14, tail=2.0)
    m['lament'].add(ln, l0, -0.2)
    m['choir'].add(choir(['D3', 'A3', 'F4'], 5.0, 0.6, rng, attack=2.0, release=2.0), 20.0, 0.0)
    return dict(handover=L, hands_to='heaps', intro_bars=0, moment='grief', premix=[(anthem, 0.0)],
                hits={'run_down': 2.5, 'landing': 5.5, 'chime': 9.5, 'collapse': hit, 'release': 20.0},
                camera=[dict(t=0.0, shot='low beside him, up at the car leaving (car10, as now)'),
                        dict(t=5.5, shot='he lands; hold a beat in the silence'),
                        dict(t=6.0, shot='rise over his shoulder to look down ring C\'s lane, in the dark (ringc10), arriving by 9.0'),
                        dict(t=9.5, shot='hold; the cold light starts to come up over the lane'),
                        dict(t=12.0, shot='the light is full on the lane and its dead: the collapse lands on this frame'),
                        dict(t=20.0, shot='hold ends; ease back to him over 2.5 s')],
                control=22.0, notes='Replaces lastcar + collapse with one cue; no queue. The light ramp ends exactly at 12.0.')


def cue_window(m, rng):
    """Moment, intrigue and hope: the lit window (the prologue's end). He stops and looks up. A second and
    a half of near silence. As the camera rises with his look, the music box climbs, one note a beat, over a
    thin high string and a soft choir; on the frame where the one lit window is held, it opens onto F with a
    major seventh, and a high violin sings the true E: someone up there turned the lights on. It does not
    resolve. While it holds, the music box sounds a few irregular notes, like a signal. As the camera comes
    back down he checks his label, and the music box plays the parcel's notes with the true E. Then the
    stair, the dark, and the end card."""
    L = at(5)
    pedal(m, L + RING, rng, level=0.45, fade_out=16.0, fade_len=4.0)
    string_note(m['strings'], 'A5', 1.5, 9.0, 0.025, 'violin', 0.45, 2.5, 3.0, players=1, rng=rng)
    box_line(m, [('D5', 1), ('F5', 1), ('G5', 1), ('A5', 1), ('C6', 1)], 1.5, 0.26, rng)
    m['choir'].add(choir(['F4', 'A4'], 5.0, 0.28, rng, attack=3.0, release=0.5, shape=[0.4, 0.8, 1.0]), 1.5, 0.0)
    chord(m, ['D3', 'A3'], 1.5, 2.6, 0.06, rng, attack=1.5, release=0.6)
    chord(m, ['Bb2', 'F3', 'D4'], 4.0, 2.6, 0.08, rng, attack=1.0, release=0.5)
    # 6.5: the window. F with a major seventh; the true E, high.
    chord(m, ['F2', 'C3', 'A3', 'E4', 'G4'], 6.5, 5.5, 0.22, rng, attack=0.8, release=3.0, shape=[1, 0.9, 0.7])
    m['choir'].add(choir(['F3', 'C4', 'E4', 'A4'], 5.5, 0.9, rng, attack=0.8, release=3.0, shape=[1, 0.85, 0.6]), 6.5, 0.0)
    ln, l0 = legato_line(line([('E6', 5.0)], 6.5), 0, 'violin', 0.16, rng, vib_cents=10, tail=3.0, shape=[(6.5, 1.0), (11.5, 0.6)])
    m['solo'].add(ln, l0, 0.3)
    m['box'].add(music_box('C6', 0.24, rng), 6.5, 0.4)
    for t, name in ((7.6, 'A5'), (8.3, 'E6'), (9.9, 'C6'), (10.4, 'A5'), (11.6, 'G5')):     # irregular, like a signal
        m['box'].add(music_box(name, 0.18, rng), t, 0.45)
    # 11.5 to 13.5: the camera comes down; 13.8: the label, and the parcel's notes, true.
    chord(m, ['D3', 'A3'], 12.0, 6.0, 0.06, rng, attack=1.5, release=3.0)
    parcel(m, 13.8, rng, vel=0.3, gaps=(1.0, 1.2), true_e=True)
    return dict(handover=L, hands_to=None, intro_bars=0, moment='intrigue',
                hits={'rise': 1.5, 'window': 6.5, 'label': 13.8},
                camera=[dict(t=0.0, shot='he stops on the landing and looks up; camera still, low behind him (ending, as now)'),
                        dict(t=1.5, shot='rise with his look up the well'),
                        dict(t=6.5, shot='arrive on the one lit window, easing to a stop over the last 1 s'),
                        dict(t=11.5, shot='hold ends; come back down to him over 2 s'),
                        dict(t=13.6, shot='he checks his label (as now)')],
                control=None, notes='Replaces end here; prologue_cue_end then plays on the end card after the fade.')


HAPPY = [  # Happy Birthday (public domain), in F, as (note, beats in 3/4)
    ('C5', 0.75), ('C5', 0.25), ('D5', 1), ('C5', 1), ('F5', 1), ('E5', 2),
    ('C5', 0.75), ('C5', 0.25), ('D5', 1), ('C5', 1), ('G5', 1), ('F5', 2),
    ('C5', 0.75), ('C5', 0.25), ('C6', 1), ('A5', 1), ('F5', 1), ('E5', 1), ('D5', 2)]


def cue_end(m, rng):
    """The prologue's end card, fading to black as he climbs away. The dead below: the pedal, a soft
    choir, the lament on the cello. Hope above: the music box answers with the cascade and its true E,
    and D-17 hops once, small. Then the music box plays the parent's birthday tune, slowing as its spring
    runs down, and stops one phrase short. The tannoy's chime, far off: the order still running."""
    L = at(15)
    pedal(m, L + RING, rng, fade_in=4.0, fade_out=at(13), fade_len=8.0)
    m['choir'].add(choir(['D3', 'A3', 'F4'], 2 * BAR, 0.4, rng, attack=2.5, release=3.0), 0.0, 0.0)
    ln, l0 = legato_line(line(LAMENT, at(0, 2)), 0, 'cello', 0.36, rng, vib_cents=14, tail=2.0)
    m['lament'].add(ln, l0, -0.15)
    box_line(m, CASCADE, at(5), 0.27, rng, stretch=1.5)
    chord(m, ['F2', 'C3', 'A3', 'C4'], at(5), 2 * BAR, 0.08, rng, attack=2.0, release=2.5)
    t = at(8)
    for name, beats in (('C5', 0.5), ('F5', 0.5), (None, 0.5), ('E5', 0.25), ('F5', 0.25), ('A5', 1.0)):
        if name:
            m['pizz'].add(pizz(name, 0.3, rng), t + human(rng, 8), 0.25)
        t += beats * 0.8
    # The birthday tune, winding down: each beat a little longer than the last.
    t, beat = at(9, 2), 0.62
    for name, beats in HAPPY:
        m['box'].add(music_box(name, 0.26 * rng.uniform(0.9, 1.05), rng), t + human(rng, 6), 0.3)
        t += beats * beat
        beat *= 1.022
    chord(m, ['F2', 'C3', 'A3'], at(9, 2), t - at(9, 2), 0.06, rng, attack=2.5, release=3.0)
    m['chime'].add(tannoy_chime(0.3, rng), t + 2.0, 0.4)
    return dict(handover=L, hands_to=None, intro_bars=0, starts_from='silence', hits={'birthday_tune': at(9, 2), 'tune_stops': round(t, 1)})


CUE_LIST = [  # name, builder, the old cue's length (s), the beat
    ('wake', cue_wake, 58, 'Opening: power returns, he answers, stands, play begins.'),
    ('hall', cue_hall, 60, 'DL-01: the dark depot hall, under the night-shift tannoy.'),
    ('threshold', cue_threshold, 44, 'DL-01: the bulkhead cranks open; through into the sorting hall.'),
    ('racks', cue_racks, 60, 'DL-03: the gate opens; the rack lights come on row by row over the couriers.'),
    ('kin', cue_kin, 70, 'Moment (grief), DL-04: one of many.'),
    ('dead', cue_dead, 78, 'DL-06: the scanner refuses his label; the pit; the label check; purpose.'),
    ('latch', cue_latch, 11, 'DL-08: the pawl drops home.'),
    ('refuge', cue_refuge, 40, 'Moment (wonder), DL-09: the city.'),
    ('ringc', cue_ringc, 26, 'Moment (grief and horror), DL-10: the car leaves; ring C.'),
    ('child', cue_child, 50, "DL-11: the desk clears; the growth marks and the tree; no one at this address."),
    ('window', cue_window, 0, 'Moment (intrigue and hope), the end: the one lit window.'),
    ('end', cue_end, 100, "The prologue's end card."),
]


def render_cue(build, seed):
    rng = np.random.default_rng(seed)
    m = PrologueMix(75.0)
    meta = build(m, rng)
    st = m.render()
    for buf, start in meta.pop('premix', []):            # parts rendered apart (e.g. run down), laid in before mastering
        i = int(start * SR)
        n = min(buf.shape[1], st.shape[1] - i)
        st[:, i:i + n] += buf[:, :n]
    st = master(st)
    n = int((meta['handover'] + RING) * SR)
    st = st[:, :n]
    k = int(2.0 * SR)
    st[:, -k:] *= np.linspace(1, 0, k) ** 2
    return st, meta


def to_mp3(wav, mp3):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-c:a', 'libmp3lame', '-q:a', '3', mp3], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='prologue')
    ap.add_argument('--wav', default=None, help='also keep the WAV masters here')
    ap.add_argument('--only', nargs='*')
    args = ap.parse_args()
    manifest_path = os.path.join(args.out, 'prologue_music.json')
    with open(manifest_path) as f:
        manifest = json.load(f)
    gain = manifest['master_gain']
    wavdir = args.wav or args.out
    os.makedirs(wavdir, exist_ok=True)
    scene_cues = {c['name']: c for c in manifest.get('scene_cues', [])}
    for k, (name, build, old, beat) in enumerate(CUE_LIST):
        if args.only and name not in args.only:
            continue
        print('rendering cue', name, flush=True)
        st, meta = render_cue(build, 7000 + k)
        st = st * gain
        st = np.where(np.abs(st) > 0.7, np.sign(st) * (0.7 + 0.25 * np.tanh((np.abs(st) - 0.7) / 0.25)), st)
        st = (st + hiss(st.shape[1], 0.0011, np.random.default_rng(5))).astype(np.float32)
        stem = f'prologue_cue_{name}'
        wav = os.path.join(wavdir, f'{stem}.wav')
        write_wav(wav, st)
        to_mp3(wav, os.path.join(args.out, f'{stem}.mp3'))
        if not args.wav:
            os.remove(wav)
        scene_cues[name] = dict(name=name, file=f'{stem}.mp3', beat=beat, seconds=round(st.shape[1] / SR, 2),
                                handover=meta['handover'], hands_to=meta['hands_to'], intro_bars=meta['intro_bars'],
                                starts_from=meta.get('starts_from', 'loop'), hits=meta.get('hits', {}),
                                old_seconds=old, level=0.9)
        for key in ('moment', 'camera', 'control', 'notes'):
            if key in meta:
                scene_cues[name][key] = meta[key]
    manifest['scene_cues'] = [scene_cues[n] for n, *_ in CUE_LIST if n in scene_cues]
    manifest['scene_cue_notes'] = (
        'Play each scene cue at the loops\' gain (level 0.9 at the game\'s current loop gain), since they are mastered '
        'together. Start it at once (its first bar is the incoming loop\'s texture; fade the loop out over intro_bars, or '
        '2 s). At `handover` s into the cue, start hands_to from its loop_start with a 1 to 2 s fade-in while the cue '
        'rings out (its notes have ended; only tails and the pedal remain, and the pedal fades over 2 s). hands_to null '
        'means silence follows.')
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)


if __name__ == '__main__':
    main()
