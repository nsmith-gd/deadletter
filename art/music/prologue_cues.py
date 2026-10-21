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
                              machine_thud, march_bar, organ, snare_march, tannoy_chime)
from sketch_identity import horn, pizz, taiko

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


def cue_kin(m, rng):
    """DL-04: among the couriers he stops and touches his chest. Out of the heaps' choir: four low piano
    notes (A, F, D, E-flat), then the lament broadens on the cello, violins in octaves take it up, the
    choir grows, a timpani roll and a cymbal swell lift it to one moderate peak on B-flat over D. It
    lets go through G minor to D minor, and leaves room for the music box: the parcel's notes, the E
    sagging. Back into the heaps."""
    L = at(10)
    pedal(m, L + RING, rng, fade_out=L)
    m['choir'].add(choir(['D3', 'A3', 'F4'], 2 * BAR, 0.75, rng, attack=1.0, release=2.0), 0.0, 0.0)
    for k, name in enumerate(('A2', 'F2', 'D2', 'Eb2')):
        m['piano'].add(piano(name, 0.36 - 0.03 * k, 4, rng), at(1) + 1.2 * k, -0.3)
    ln, l0 = legato_line(line([(n, b * 1.2) for n, b in LAMENT], at(2)), 0, 'cello', 0.42, rng, vib_cents=16, tail=2.0,
                         shape=[(at(2), 0.7), (at(4), 0.9), (at(6), 1.0), (at(7), 0.8)])
    m['lament'].add(ln, l0, -0.2)
    vl, v0 = legato_line(line([('D5', 3), ('C5', 1.5), ('A4', 1.5), ('G4', 2), ('F4', 2)], at(4)), 0, 'violin', 0.3, rng,
                         vib_cents=16, tail=1.5)
    m['solo'].add(vl, v0, 0.2)
    for bar, names, dyn in ((3, ['D3', 'A3', 'F4'], 0.18), (4, ['Eb3', 'Bb3', 'G4'], 0.22), (5, ['D3', 'F3', 'Bb3', 'D4'], 0.26)):
        chord(m, names, at(bar), BAR + 0.3, dyn, rng, attack=1.2, release=1.0)
        m['choir'].add(choir(names[:3], BAR, 0.5 + 0.12 * (bar - 3), rng, attack=0.8, release=1.0), at(bar), 0.0)
    # The peak, moderate: B-flat over D.
    peak = at(6)
    timp_roll(m['perc'], 'F2', peak - 3.0, peak, 0.05, 0.55, rng, hit=0.5)
    m['perc'].add(cymbal_swell(8, 3.0, 0.016, rng, decay=1.6), peak - 3.0, 0.2)
    chord(m, ['D2', 'Bb2', 'F3', 'D4', 'F4', 'Bb4', 'D5'], peak, BAR + 1, 0.34, rng, attack=0.4, release=2.0,
          shape=[1, 0.85, 0.6])
    m['choir'].add(choir(['Bb3', 'D4', 'F4'], BAR, 0.8, rng, attack=0.3, release=2.0), peak, 0.0)
    for name in ('Bb3', 'D4'):
        m['horns'].add(horn(name, BAR, 0.45, rng, attack=0.3, release=1.5, shape=[1, 0.8, 0.5]), peak, -0.1)
    chord(m, ['D2', 'G2', 'D3', 'Bb3', 'G4'], at(7), BAR, 0.18, rng, attack=1.0, release=2.0)
    chord(m, ['D2', 'A2', 'F3', 'A3'], at(8), 2 * BAR, 0.12, rng, attack=1.5, release=2.5)
    parcel(m, at(8) + 0.5, rng, vel=0.3, gaps=(1.1, 1.4))
    m['choir'].add(choir(['D3', 'A3', 'F4'], BAR + 1, 0.7, rng, attack=2.0, release=2.0), at(9), 0.0)
    return dict(handover=L, hands_to='heaps', intro_bars=1, hits={'peak': peak})


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


def cue_refuge(m, rng):
    """DL-09: out of the tunnel onto the balcony; the camera cranes up and back over the dark city,
    widest at about 8 s. Out of silence: air, a high string light, a far choir on an open fifth, and the
    Steward's anthem heard from the city above on a far organ and horns, cresting gently at 8 s. It
    thins, and the march comes in quietly to hand to the lobby's order loop (which opens on the tannoy's
    chime)."""
    L = at(8)
    m['air'].add(wind(L + RING, 0.06, rng) * env_curve(int((L + RING) * SR), 2.0, 3), 0)
    pedal(m, L + RING, rng, fade_in=6.0, fade_out=L)
    string_note(m['strings'], 'A5', 0.0, 14, 0.03, 'violin', 0.45, 2.5, 4, players=1, rng=rng)
    string_note(m['strings'], 'D6', 0.6, 12, 0.02, 'violin', 0.55, 2.5, 4, players=1, rng=rng)
    m['choir'].add(choir(['D4', 'A4'], 10.0, 0.6, rng, attack=4.0, release=4.0, shape=[0.5, 1, 0.7, 0.5]), 1.0, 0.0)
    for bar, chordn in enumerate(ANTHEM_CHORDS[:5]):
        m['organ'].add(organ(chordn, BAR, 0.35 * (1.0 if bar == 1 else 0.75), rng, attack=0.8, release=1.6), 2.0 + bar * BAR, 0.1)
    t = 2.0
    for name, beats in ANTHEM[:10]:
        m['horns'].add(horn(name, beats * 0.95, 0.3, rng, attack=0.2, release=0.5), t + human(rng, 5), 0.15)
        t += beats
    for bar in (6, 7):
        march_bar(m, bar, MARCH[bar % 2], 0.12 + 0.05 * (bar - 6), rng)
    snare_march(m, 7, 0.22, rng)
    thuds(m, at(6), L, rng, level=0.6)
    return dict(handover=L, hands_to='order', intro_bars=0, starts_from='silence', hits={'widest': 8.0})


def cue_child(m, rng):
    """DL-11: C-114's bedroom. Out of the heaps, low: the desk scrapes clear and the music box finds the
    parcel's notes, and for the first time it holds the true E. They become the lullaby's cascade, slowly,
    over soft strings (D minor, B-flat, F, G minor), warming to F at the tree. The terminal answers (no one
    at this address): it thins to one high note over D, and to silence."""
    L = at(10)
    pedal(m, L + RING, rng, level=0.6, fade_out=at(8), fade_len=8.0)
    m['choir'].add(choir(['D3', 'A3', 'F4'], BAR, 0.42, rng, attack=1.0, release=2.0), 0.0, 0.0)
    parcel(m, at(1), rng, vel=0.32, gaps=(1.1, 1.4), true_e=True)
    box_line(m, CASCADE, at(2, 2), 0.28, rng, stretch=1.6)
    for bar, names in ((2, ['D3', 'A3', 'E4', 'F4']), (3, ['Bb2', 'F3', 'A3', 'D4']), (4, ['A2', 'F3', 'C4', 'F4']),
                       (5, ['G2', 'D3', 'Bb3', 'F4'])):
        chord(m, names, at(bar), BAR + 0.3, 0.1, rng, attack=1.5, release=1.8)
        m['piano'].add(piano(names[0], 0.24, 3.5, rng), at(bar), -0.3)
        m['piano'].add(piano(names[2], 0.16, 2.5, rng), at(bar, 1.5), 0.0)
    # The tree: F, warm, a little more.
    chord(m, ['F2', 'C3', 'A3', 'C4', 'G4'], at(6), BAR + 1, 0.16, rng, attack=1.2, release=2.5)
    m['horns'].add(horn('A3', BAR, 0.25, rng, attack=1.0, release=2.0), at(6), -0.1)
    box_line(m, [('A5', 1.0), ('C6', 1.0), ('D6', 2.5)], at(6, 1), 0.24, rng, stretch=1.2)
    # The terminal answers: one high note over D, and silence.
    string_note(m['strings'], 'A5', at(7, 2), 12, 0.03, 'violin', 0.4, 2.0, 6, shape=[1, 0.9, 0.6, 0.3], players=1, rng=rng)
    string_note(m['strings'], 'D3', at(7, 2), 10, 0.07, 'cello', -0.3, 2.0, 6, shape=[1, 0.8, 0.4], rng=rng)
    return dict(handover=L, hands_to=None, intro_bars=1, hits={'true_e': at(1) + 1.1, 'tree': at(6), 'terminal': at(7, 2)})


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
    ('kin', cue_kin, 70, 'DL-04: among the couriers he touches his chest.'),
    ('dead', cue_dead, 78, 'DL-06: the scanner refuses his label; the pit; the label check; purpose.'),
    ('latch', cue_latch, 11, 'DL-08: the pawl drops home.'),
    ('refuge', cue_refuge, 40, 'DL-09: the balcony over the dark city, into DL-10 lobby.'),
    ('child', cue_child, 50, "DL-11: the desk clears; the growth marks and the tree; no one at this address."),
    ('end', cue_end, 100, "The prologue's end card."),
]


def render_cue(build, seed):
    rng = np.random.default_rng(seed)
    m = PrologueMix(75.0)
    meta = build(m, rng)
    st = master(m.render())
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
