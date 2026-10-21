"""A sketch of the score's musical identity: one cue of about 2:25, not used in the game.

It tries out the identity in docs/research/musical_identity.md with the score's own
instruments (from compose_dl01.py) and some new ones: pizzicato, a whistle, an
analog-style pad, a synthesized horn section and a drum kit (taiko, toms,
kick, snare, shaker, crash).

    python3 sketch_identity.py --out /tmp/sketch      # needs numpy and scipy, and ffmpeg with libmp3lame

3/4 at 90 bpm, so a bar is 2 s. The shape:
      0-20 s  Intrigue. A D pedal and a felt-piano ostinato in D Dorian (the raised B is the
              colour of curiosity); music-box glints; shaker ticks start the walk.
     20-44 s  Whimsy. D-17's hop, a skipping figure with a B-natural wink, traded between the
              music box, pizzicato and whistle over an oom-pah-pah pizzicato bass; the whistle
              answers with the cascade.
     44-92 s  The build, three rounds of eight bars. Each adds drums and lifts the strings,
              and the first two tease: they drop back for a bar before pushing on. The last
              round climbs G, A, B-flat, C and rolls into the top.
    92-100 s  The drop. Everything fades and darkens over five seconds into near silence;
              a far whistle and a heartbeat; then the riser, the snare and the timpani
              climb out of it.
   100-124 s  The arrival on F with a crash: drums, horns, strings in octaves, the cascade
              turned upward, then falling home, ending plagal (B-flat, F).
   124-144 s  It lets go: the music box plays the cascade over D, and D-17 has the last
              word, one hop on pizzicato.
"""

import argparse
import os
import subprocess

import numpy as np

from compose_dl01 import (SR, Track, body_gain, butter, cymbal_swell, env_curve, hiss, human, hz, legato_line,
                          master, midi, music_box, octave, onepole_lp, pan_for, piano, reverb, smooth_noise,
                          string_note, tape, timp_roll, wind, write_wav)
import compose_dl01

BPM = 90
B = 60.0 / BPM          # a beat
BAR = 3 * B             # 2 s
compose_dl01.BEAT = B   # legato_line counts its note lengths in beats


def at(bar, beat=0.0):
    return bar * BAR + beat * B


# The cascade: a pentatonic fall that speeds up, then the parcel's E and D. (note, beats)
CASCADE = [('D6', 1.0), ('C6', 0.75), ('A5', 0.55), ('G5', 0.42), ('F5', 0.9), ('E5', 0.6), ('D5', 1.8)]
# D-17's hop: a skip up, a stumble, a leap, and a B-natural wink. None is a rest.
HOP = [('C5', 0.5), ('F5', 0.5), (None, 0.5), ('E5', 0.25), ('F5', 0.25), ('A5', 1.0),
       ('G5', 0.5), ('B5', 0.5), ('A5', 0.5), ('F5', 0.5), (None, 1.0)]


def events(notes, t0, stretch=1.0, transpose=0):
    """(time, note, seconds) from (note, beats); None is a rest."""
    out, t = [], t0
    for name, beats in notes:
        if name:
            out.append((t, octave(name, transpose) if transpose else name, beats * B * stretch))
        t += beats * B * stretch
    return out


def line(notes, t0, stretch=1.0, transpose=0):
    """The same as events, but in beats for legato_line (which multiplies by BEAT itself)."""
    return [(t, n, d / B) for t, n, d in events(notes, t0, stretch, transpose)]


# ---------------------------------------------------------------------------
# New instruments
# ---------------------------------------------------------------------------
def pizz(name, vel, rng):
    """A pizzicato string: a soft-fingered pluck through the bowed strings' body."""
    f = hz(name, cents=rng.normal(0, 4))
    kind = 'cello' if f < 200 else 'viola' if f < 400 else 'violin'
    length = 0.5 + 1.2 * (200 / f) ** 0.5
    t = np.arange(int(length * SR)) / SR
    out = np.zeros_like(t)
    for n in range(1, 24):
        fn = n * f
        if fn > 7000:
            break
        out += body_gain(fn, kind) / n * np.exp(-t / (0.5 * (200 / f) ** 0.4 / n ** 0.5)) * np.sin(2 * np.pi * fn * t + rng.uniform(0, 6.28))
    thump = onepole_lp(rng.standard_normal(len(t)).astype(np.float32), 900) * np.exp(-t / 0.01)
    return ((out * np.minimum(1, t / 0.003) + thump * 0.3) * 0.06 * vel).astype(np.float32)


def whistle_line(notes, dyn, rng, glide=0.07):
    """A whistled line from (time, note, seconds): a near-sine with breath, a delayed vibrato and
    small slides. Returns (signal, start time)."""
    t0 = notes[0][0] - 0.15
    end = notes[-1][0] + notes[-1][2] + 0.6
    n = int((end - t0) * SR)
    t = np.arange(n, dtype=np.float32) / SR + t0
    logf = np.full(n, np.log2(hz(notes[0][1])), np.float32)
    amp = np.zeros(n, np.float32)
    for k, (tn, name, d) in enumerate(notes):
        lf = np.log2(hz(name))
        if k:
            s = np.clip((t - tn + glide / 2) / glide, 0, 1)
            prev = np.log2(hz(notes[k - 1][1]))
            logf = np.where(t >= tn - glide / 2, prev + (lf - prev) * s * s * (3 - 2 * s), logf)
        u = np.clip((t - tn) / max(d, 1e-3), 0, 1)
        amp = np.where((t >= tn) & (t < tn + d), 0.8 + 0.2 * np.sin(np.pi * u), amp)
    amp = onepole_lp(amp, 40) * env_curve(n, 0.05, 0.4)
    since = t - t0
    vib = 18 * np.clip(since / 0.9, 0, 1) * np.sin(2 * np.pi * 5.6 * since) * (0.7 + 0.3 * smooth_noise(n, 1.0, rng))
    f = 2 ** logf * 2 ** ((vib + 4 * smooth_noise(n, 0.8, rng)) / 1200)
    ph = 2 * np.pi * np.cumsum(f, dtype=np.float64) / SR
    breath = butter(rng.standard_normal(n).astype(np.float32), [1500, 7000], 'band')
    return (((np.sin(ph) + 0.06 * np.sin(2 * ph)) * amp + breath * amp * 0.05) * dyn * 0.05).astype(np.float32), t0


def saw_voice(f, amp, cutoff, rng, top=5000):
    """Band-limited saw with a time-varying low-pass (per-harmonic gain), from per-sample arrays."""
    n = len(amp)
    ph = 2 * np.pi * np.cumsum(f, dtype=np.float64) / SR
    out = np.zeros(n, np.float32)
    f0 = float(np.median(f))
    for h in range(1, 60):
        if h * f0 > top:
            break
        g = 1 / (1 + (h * f0 / cutoff) ** 4) / h
        out += (g * np.sin(h * ph + rng.uniform(0, 6.28))).astype(np.float32)
    return out * amp


def synth_pad(names, dur, level, rng, pump=0.0, cutoff=(500, 1800)):
    """A soft analog-style pad: detuned saws through a slowly opening low-pass, with an optional
    quaver pump."""
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    fc = (cutoff[0] + (cutoff[1] - cutoff[0]) * (0.5 - 0.5 * np.cos(np.pi * np.clip(t / dur, 0, 1)))).astype(np.float32)
    env = env_curve(n, min(2.0, dur / 3), min(2.5, dur / 3))
    out = sum(saw_voice(np.full(n, hz(name, cents=det + rng.normal(0, 1)), np.float32), env, fc, rng)
              for name in names for det in (-7, 0, 7))
    if pump:
        out *= 1 - pump * np.exp(-((t % (B / 2)) / (B / 2)) / 0.12)
    return (out * level * 0.01).astype(np.float32)


def horn(name, dur, dyn, rng, shape=None, attack=0.25, release=0.7):
    """A horn section (three players) from saws: brighter as it gets louder, a small scoop up into
    each note."""
    n = int((dur + release) * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = env_curve(n, attack, release, shape)
    out = np.zeros(n, np.float32)
    for p in range(3):
        cents = rng.uniform(-5, 5) - 25 * np.exp(-t / 0.06) + 6 * smooth_noise(n, 0.8, rng)
        f = (hz(name) * 2 ** (cents / 1200)).astype(np.float32)
        lag = int(rng.uniform(0, 0.03) * SR)
        e = np.concatenate([np.zeros(lag, np.float32), env[:n - lag]])
        fc = (180 + 2600 * (e * dyn) ** 1.4 + hz(name) * 1.5).astype(np.float32)
        out += saw_voice(f, e, fc, rng, top=4000)
    return (onepole_lp(out, 3500) * dyn * 0.012).astype(np.float32)


# Drums. All return mono hits at full level.
def taiko(vel, rng, f0=62):
    t = np.arange(int(1.6 * SR)) / SR
    f = f0 * (1 + 0.5 * np.exp(-t / 0.03))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55) + 0.35 * np.sin(2 * np.pi * 2.3 * f0 * t) * np.exp(-t / 0.18)
    skin = onepole_lp(rng.standard_normal(len(t)).astype(np.float32), 500) * np.exp(-t / 0.04)
    return ((body + skin * 0.8) * np.minimum(1, t / 0.002) * 0.5 * vel).astype(np.float32)


def tom(f0, vel, rng):
    t = np.arange(int(0.9 * SR)) / SR
    f = f0 * (1 + 0.35 * np.exp(-t / 0.025))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.28)
    skin = butter(rng.standard_normal(len(t)).astype(np.float32), [200, 3000], 'band') * np.exp(-t / 0.03)
    return ((body + skin * 0.35) * 0.35 * vel).astype(np.float32)


def kick(vel, rng):
    t = np.arange(int(0.6 * SR)) / SR
    f = 48 + 110 * np.exp(-t / 0.035)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.3)
    click = butter(rng.standard_normal(len(t)).astype(np.float32), 2500, 'high') * np.exp(-t / 0.003)
    return ((body + click * 0.25) * 0.45 * vel).astype(np.float32)


def snare(vel, rng):
    t = np.arange(int(0.5 * SR)) / SR
    tone = np.sin(2 * np.pi * 185 * t) * np.exp(-t / 0.06) + 0.5 * np.sin(2 * np.pi * 330 * t) * np.exp(-t / 0.04)
    wires = butter(rng.standard_normal(len(t)).astype(np.float32), [1500, 9000], 'band') * np.exp(-t / 0.13)
    return ((tone * 0.6 + wires) * 0.25 * vel).astype(np.float32)


def shaker(vel, rng):
    t = np.arange(int(0.12 * SR)) / SR
    x = butter(rng.standard_normal(len(t)).astype(np.float32), 5000, 'high')
    return (x * (np.minimum(1, t / 0.012) * np.exp(-t / 0.035)) * 0.12 * vel).astype(np.float32)


def crash(vel, rng, length=5.0):
    n = int(length * SR)
    t = np.arange(n) / SR
    x = butter(rng.standard_normal(n).astype(np.float32), [2500, 14000], 'band') * np.exp(-t / 1.6)
    ring = sum(butter(rng.standard_normal(n).astype(np.float32), [f * 0.96, f * 1.04], 'band') * a * np.exp(-t / 2.2)
               for f, a in ((3400, 0.5), (5100, 0.45), (6900, 0.35), (9300, 0.25)))
    body = butter(rng.standard_normal(n).astype(np.float32), [400, 2500], 'band') * np.exp(-t / 0.25) * 0.5
    return ((x + ring + body) * np.minimum(1, t / 0.0015) * 0.12 * vel).astype(np.float32)


def snare_roll(tr, t0, t1, v0, v1, rng, r0=12.0, r1=24.0):
    t = t0
    while t < t1:
        u = (t - t0) / (t1 - t0)
        tr.add(snare((v0 + (v1 - v0) * u ** 1.5) * rng.uniform(0.85, 1.0), rng), t, 0.1 * rng.uniform(-1, 1))
        t += 1.0 / (r0 + (r1 - r0) * u)


class SketchMix:
    """Stems, each with a reverb send and gain, and fades: spans where listed stems, reverb tails
    included, darken and fade to nothing (then come back), so a drop can fall away rather than stop."""

    STEMS = {  # name: (wet, gain)
        'piano': (0.5, 2.8), 'box': (0.7, 3.5), 'strings': (0.45, 3.5), 'solo': (0.42, 4.0), 'air': (0.25, 0.8),
        'perc': (0.5, 1.0), 'pizz': (0.4, 4.0), 'whistle': (0.45, 1.5), 'synth': (0.5, 1.6),
        'horns': (0.45, 3.8), 'drums': (0.28, 0.8), 'crash': (0.35, 3.5), 'tail': (0.6, 2.0)}

    def __init__(self, seconds):
        self.stems = {k: Track(seconds) for k in self.STEMS}
        self.fades = []     # (start, length, back, stems)

    def __getitem__(self, k):
        return self.stems[k]

    def render(self):
        total = None
        for k, tr in self.stems.items():
            wet, gain = self.STEMS[k]
            st = tr.buf
            if k == 'box':
                st = tape(st, wow=0.0016)
            st = reverb(st, wet) * gain
            for a, length, back, stems in self.fades:
                if k not in stems:
                    continue
                t = np.arange(st.shape[1]) / SR
                u = np.clip((t - a) / length, 0, 1)
                dark = butter(st, 500)
                st = st * (1 - u) + dark * u               # the filter closing
                g = (1 - u) ** 2.2                         # and the level falling away
                if back is not None:
                    g = np.where(t >= back, 1.0, g)
                st = (st * g).astype(np.float32)
            total = st if total is None else total + st
        return master(tape(total, wow=0.0005, flutter=0.00003))


# ---------------------------------------------------------------------------
# Arranging helpers
# ---------------------------------------------------------------------------
def ostinato(tr, bar, notes, vel, rng, inst=piano, pan=None):
    """Six quavers across a bar."""
    for j, name in enumerate(notes):
        v = vel * (1.0 if j == 0 else 0.7 if j == 3 else 0.6) * rng.uniform(0.92, 1.05)
        x = inst(name, v, 0.6, rng) if inst is piano else inst(name, v, rng)
        tr.add(x, at(bar, j * 0.5) + human(rng, 8), pan_for(name, 0.6) if pan is None else pan)


def waltz_bass(tr, bar, bass, chord, vel, rng):
    """Oom-pah-pah on pizzicato: the bass on one, the chord on two and three."""
    tr.add(pizz(bass, vel, rng), at(bar) + human(rng, 8), -0.3)
    for beat in (1, 2):
        for name in chord:
            tr.add(pizz(name, vel * 0.45 * rng.uniform(0.85, 1.05), rng), at(bar, beat) + human(rng, 10), pan_for(name, 0.7))


def spiccato(tr, bar, notes, dyn, rng, kind='violin', pan=0.25):
    """Six short bowed quavers across a bar."""
    for j, name in enumerate(notes):
        d = dyn * (1.0 if j % 3 == 0 else 0.75)
        string_note(tr, name, at(bar, j * 0.5) + human(rng, 6), 0.16, d, kind, pan, 0.02, 0.12, players=2, rng=rng)


def chord_strings(tr, start, dur, voicing, dyn, rng, attack=0.4, release=1.0, shape=None):
    for k, name in enumerate(voicing):
        kind = 'bass' if midi(name) < midi('E2') else 'cello' if midi(name) < midi('G3') else 'viola' if midi(name) < midi('D4') else 'violin'
        string_note(tr, name, start, dur, dyn * (0.8 if kind in ('bass', 'cello') else 0.6), kind,
                    -0.4 + 0.8 * k / max(1, len(voicing) - 1), attack, release, shape=shape, rng=rng)


def groove(tr, bar, level, rng, fill=False):
    """A 3/4 drum bar: taiko on one, toms pushing on two and three, a shaker on every quaver."""
    tr.add(taiko(level, rng), at(bar), 0.0)
    tr.add(kick(level * 0.7, rng), at(bar), 0.0)
    tr.add(tom(110, level * 0.7, rng), at(bar, 1), -0.25)
    tr.add(taiko(level * 0.55, rng, f0=70), at(bar, 1.5), 0.1)
    tr.add(tom(82, level * 0.8, rng), at(bar, 2), 0.25)
    tr.add(snare(level * 0.45, rng), at(bar, 2), 0.05)
    if fill:
        for j, f in enumerate((140, 120, 100, 85)):
            tr.add(tom(f, level * (0.6 + 0.1 * j), rng), at(bar, 2 + j * 0.25), -0.3 + 0.2 * j)
    for j in range(6):
        tr.add(shaker(level * (0.8 if j % 2 else 0.5), rng), at(bar, j * 0.5) + human(rng, 5), 0.35)


# ---------------------------------------------------------------------------
# The sketch
# ---------------------------------------------------------------------------
def sketch():
    rng = np.random.default_rng(2026)
    total = 146.0
    m = SketchMix(total)
    m['air'].add(wind(total, 0.04, rng) * env_curve(int(total * SR), 4, 14), 0)

    # 1. Intrigue (bars 0-9). D pedal; a felt-piano ostinato in D Dorian; glints; the walk begins.
    string_note(m['strings'], 'D2', 0.0, 20.5, 0.22, 'cello', -0.3, 4, 2, rng=rng)
    string_note(m['strings'], 'D1', 1.0, 19.5, 0.16, 'bass', -0.15, 5, 2, rng=rng)
    string_note(m['strings'], 'A5', 2.0, 18.0, 0.03, 'violin', 0.45, 5, 2, players=1, rng=rng)
    intrigue = [['D3', 'A3', 'E4', 'F4', 'E4', 'A3'], ['D3', 'B3', 'D4', 'G4', 'D4', 'B3'],
                ['D3', 'Bb3', 'E4', 'A4', 'E4', 'Bb3'], ['D3', 'A3', 'D4', 'G4', 'E4', 'A3']]
    for bar in range(1, 10):
        ostinato(m['piano'], bar, intrigue[(bar - 1) % 4], 0.36 + 0.02 * bar, rng)
    for t, name in ((3.3, 'B5'), (6.2, 'E6'), (9.1, 'A5'), (12.5, 'B5'), (15.4, 'D6'), (17.8, 'G6')):
        m['box'].add(music_box(name, 0.22, rng), t, 0.4)
    for bar in range(5, 10):
        for j in range(6):
            m['drums'].add(shaker(0.2 + 0.05 * (bar - 5) * (1 if j % 2 else 0.6), rng), at(bar, j * 0.5) + human(rng, 6), 0.4)
    for bar in (7, 8, 9):
        m['pizz'].add(pizz('D2', 0.5, rng), at(bar), -0.3)
        m['pizz'].add(pizz('A2', 0.35, rng), at(bar, 2), -0.2)

    # 2. Whimsy (bars 10-21). Oom-pah-pah; D-17's hop traded around; the whistle answers with the cascade.
    whimsy = [('F2', ['A3', 'C4', 'F4']), ('F2', ['G3', 'B3', 'D4']), ('F2', ['A3', 'C4', 'F4']), ('E2', ['G3', 'C4', 'E4']),
              ('D2', ['F3', 'A3', 'D4']), ('B1', ['G3', 'B3', 'D4']), ('Bb1', ['F3', 'Bb3', 'D4']), ('C2', ['G3', 'C4', 'E4']),
              ('F2', ['A3', 'C4', 'F4']), ('F2', ['G3', 'B3', 'D4']), ('Bb1', ['F3', 'Bb3', 'D4']), ('C2', ['F3', 'Bb3', 'C4'])]
    for k, (bass, chord) in enumerate(whimsy):
        waltz_bass(m['pizz'], 10 + k, bass, chord, 0.55, rng)
        for j in range(6):
            m['drums'].add(shaker(0.35 * (1 if j % 2 else 0.6), rng), at(10 + k, j * 0.5) + human(rng, 6), 0.4)
    for t, name, d in events(HOP, at(10)):                       # the music box hops
        m['box'].add(music_box(name, 0.34, rng), t + human(rng, 6), 0.35)
    for t, name, d in events(HOP, at(10), transpose=-1):        # pizzicato doubles it, lower
        m['pizz'].add(pizz(name, 0.5, rng), t + human(rng, 6), 0.1)
    w, w0 = whistle_line(events(CASCADE[:5], at(12)), 0.9, rng)
    m['whistle'].add(w, w0, 0.15)
    w, w0 = whistle_line(events(HOP, at(14)), 0.85, rng)        # now the whistle hops
    m['whistle'].add(w, w0, 0.15)
    for t, name, d in events(CASCADE[:5], at(16)):               # and the music box answers
        m['box'].add(music_box(name, 0.3, rng), t, 0.35)
    for t, name, d in events(HOP, at(18)):                       # together, the second time
        m['box'].add(music_box(name, 0.3, rng), t, 0.35)
        m['pizz'].add(pizz(octave(name, -1), 0.45, rng), t, 0.1)
    w, w0 = whistle_line(events(CASCADE, at(20)), 0.95, rng)    # the whole cascade, into the build
    m['whistle'].add(w, w0, 0.15)
    m['tail'].add(pizz('C5', 0.4, rng), at(21, 2.5), 0.3)

    # 3. The build (bars 22-45): three rounds of eight bars on B-flat, C, D minor, D minor.
    rounds = [('Bb1', ['F3', 'Bb3', 'D4'], ['Bb3', 'D4', 'F4', 'A4', 'F4', 'D4']),
              ('C2', ['G3', 'C4', 'E4'], ['C4', 'E4', 'G4', 'C5', 'G4', 'E4']),
              ('D2', ['A3', 'D4', 'F4'], ['D4', 'F4', 'A4', 'D5', 'A4', 'F4']),
              ('D2', ['A3', 'C4', 'F4'], ['D4', 'F4', 'A4', 'C5', 'A4', 'F4'])]
    climb = [('G1', ['D3', 'G3', 'Bb3'], ['G4', 'Bb4', 'D5', 'G5', 'D5', 'Bb4']),
             ('A1', ['E3', 'A3', 'C#4'], ['A4', 'C#5', 'E5', 'A5', 'E5', 'C#5']),
             ('Bb1', ['F3', 'Bb3', 'D4'], ['Bb4', 'D5', 'F5', 'Bb5', 'F5', 'D5']),
             ('C2', ['G3', 'C4', 'E4'], ['C5', 'E5', 'G5', 'C6', 'G5', 'E5'])]
    rising = [('D5', 0.5), ('F5', 0.5), ('G5', 0.5), ('A5', 0.5), ('C6', 1.0), ('D6', 3.0)]   # the cascade upturned
    for r in range(3):
        for k in range(8):
            bar = 22 + 8 * r + k
            last_round = r == 2 and k >= 4
            bass, chord, figure = climb[k - 4] if last_round else rounds[k % 4]
            tease = r < 2 and k == 7
            lvl = 0.35 + 0.12 * r + 0.02 * k
            # Strings: spiccato rising by round; a held chord under them from round two.
            spiccato(m['strings'], bar, figure if r else [octave(n, -1) for n in figure], 0.26 + 0.05 * r + 0.012 * k, rng,
                     'violin' if r else 'viola')
            if r == 2:
                spiccato(m['strings'], bar, [octave(n, 1) for n in figure], 0.12 + 0.015 * k, rng, 'violin', 0.45)
            if r >= 1:
                chord_strings(m['strings'], at(bar), BAR, [bass, octave(bass, 1)] + chord, 0.14 + 0.06 * r + 0.01 * k, rng,
                              attack=0.3, release=0.4)
            m['pizz'].add(pizz(octave(bass, 1), 0.5 + 0.1 * r, rng), at(bar), -0.3)
            if tease:
                # Drop back for a bar: a heartbeat and a held breath, then push on.
                m['drums'].add(kick(0.5 + 0.2 * r, rng), at(bar), 0.0)
                m['drums'].add(kick(0.4 + 0.2 * r, rng), at(bar, 1.5), 0.0)
                continue
            if r == 0:
                m['drums'].add(taiko(0.35 + 0.03 * k, rng), at(bar), 0.0)
                if k % 2:
                    m['drums'].add(tom(100, 0.35, rng), at(bar, 2), 0.2)
                for j in range(6):
                    m['drums'].add(shaker(0.4 * (1 if j % 2 else 0.6), rng), at(bar, j * 0.5), 0.4)
            else:
                groove(m['drums'], bar, lvl, rng, fill=(k == 3 or (r == 2 and k == 7)))
        # A melody per round: the hop on cello; the cascade upturned on violins; then both, in octaves.
        if r == 0:
            ln, l0 = legato_line(line(HOP, at(24), 1.5, transpose=-2), 0, 'cello', 0.38, rng, tail=0.4)
            m['solo'].add(ln, l0, -0.2)
        elif r == 1:
            for tr_, dyn, pan in ((0, 0.4, 0.15), (-1, 0.26, -0.1)):
                ln, l0 = legato_line(line(rising, at(32), 1.0, transpose=tr_), 0, 'violin', dyn, rng, tail=0.4)
                m['solo'].add(ln, l0, pan)
        else:
            for tr_, kind, dyn, pan in ((0, 'violin', 0.45, 0.15), (1, 'violin', 0.22, 0.35), (-1, 'cello', 0.35, -0.25)):
                ln, l0 = legato_line(line(rising, at(38), 1.0, transpose=tr_), 0, kind, dyn, rng, tail=0.4)
                m['solo'].add(ln, l0, pan)
            for k, (bass, chord, _) in enumerate(climb):
                for name in (octave(chord[0], 1), octave(chord[1], 1)):
                    m['horns'].add(horn(name, BAR, 0.35 + 0.12 * k, rng, attack=0.3, release=0.3), at(42 + k), 0.0)
        m['synth'].add(synth_pad(['D3', 'A3', 'C4', 'F4'] if r < 2 else ['G2', 'D3', 'Bb3', 'D4'], 8 * BAR, 0.5 + 0.35 * r,
                                 rng, pump=0.25 + 0.1 * r, cutoff=(500 + 300 * r, 1500 + 600 * r)), at(22 + 8 * r), 0.0)
    snare_roll(m['drums'], at(44), at(46), 0.15, 0.7, rng)
    timp_roll(m['perc'], 'C2', at(44), at(46), 0.2, 1.0, rng)
    m['perc'].add(cymbal_swell(at(46) - at(43) + 2, at(46) - at(43), 0.03, rng, decay=1.2), at(43), 0.2)

    # 4. The drop (bars 46-49): it all falls away and darkens over five seconds; a far whistle, a
    # heartbeat; the riser climbs back out of the silence.
    drop = at(46)
    chord_strings(m['strings'], drop, 4.0, ['C2', 'G2', 'E3', 'G3', 'C4', 'E4', 'G4', 'C5'], 0.4, rng, attack=0.05, release=0.5)
    for name in ('E4', 'G4', 'C5'):
        m['horns'].add(horn(name, 3.5, 0.55, rng, attack=0.05), drop, 0.0)
    m['drums'].add(taiko(0.9, rng), drop, 0.0)
    m['crash'].add(crash(0.6, rng), drop, 0.2)
    m.fades.append((drop + 0.1, 5.0, at(50) - 0.01, ('piano', 'strings', 'solo', 'pizz', 'synth', 'horns', 'drums', 'crash', 'perc', 'air')))
    m['tail'].add(music_box('C6', 0.1, rng), drop + 5.6, 0.4)
    m['tail'].add(kick(0.12, rng), drop + 5.2, 0.0)
    m['tail'].add(kick(0.1, rng), drop + 5.9, 0.0)
    rise0, hit = at(48, 1.0), at(50)
    m['tail'].add(cymbal_swell(hit - rise0 + 0.4, hit - rise0, 0.045, rng, decay=0.3), rise0, 0.2)
    snare_roll(m['tail'], at(49), hit - 0.05, 0.03, 0.85, rng, 12, 30)
    timp_roll(m['tail'], 'C2', at(48, 2.0), hit, 0.0, 0.9, rng)
    m['tail'].add(whistle_line(events([('C5', 1.0), ('F5', 2.5)], at(48, 1.0)), 0.22, rng)[0], at(48, 1.0) - 0.15, 0.15)

    # 5. The arrival (bars 50-61): F, with a crash. Drums, horns, strings in octaves; the cascade upturned,
    # then falling home; it closes plagal.
    climax = [('F1', ['F2', 'C3', 'A3', 'C4', 'F4', 'A4']), ('F1', ['F2', 'C3', 'A3', 'C4', 'F4', 'A4']),
              ('E1', ['E2', 'C3', 'G3', 'C4', 'E4', 'G4']), ('E1', ['E2', 'C3', 'G3', 'C4', 'E4', 'G4']),
              ('D1', ['D2', 'A2', 'F3', 'A3', 'D4', 'F4']), ('D1', ['D2', 'A2', 'F3', 'A3', 'D4', 'F4']),
              ('Bb0', ['Bb1', 'F2', 'D3', 'F3', 'Bb3', 'D4']), ('Bb0', ['Bb1', 'F2', 'D3', 'F3', 'C4', 'D4']),
              ('A1', ['A2', 'C3', 'F3', 'A3', 'C4', 'F4']), ('G1', ['G2', 'D3', 'F3', 'Bb3', 'D4', 'F4']),
              ('Bb1', ['Bb2', 'F3', 'D4', 'F4', 'Bb4', 'D5']), ('F1', ['F2', 'C3', 'A3', 'C4', 'F4', 'A4'])]
    for k, (bass, voicing) in enumerate(climax):
        bar = 50 + k
        dyn = 0.62 if k < 10 else 0.66
        chord_strings(m['strings'], at(bar), BAR + 0.1, [octave(bass, 1)] + voicing, dyn, rng, attack=0.08, release=0.5)
        for name in voicing[2:5]:
            m['horns'].add(horn(name, BAR, 0.75 if k % 2 == 0 else 0.62, rng, attack=0.12, release=0.4), at(bar), 0.0)
        for name in (bass, octave(bass, 1)):
            m['piano'].add(piano(name, 0.55, BAR, rng), at(bar), pan_for(name))
        groove(m['drums'], bar, 0.95 if k % 4 == 0 else 0.85, rng, fill=(k % 4 == 3))
        spiccato(m['strings'], bar, [voicing[3], voicing[4], voicing[5], octave(voicing[3], 1), voicing[5], voicing[4]], 0.28, rng,
                 'violin', 0.4)
        if k % 4 == 0:
            m['crash'].add(crash(1.0 if k == 0 else 0.75, rng), at(bar), 0.25 if k else 0.0)
    m['drums'].add(taiko(1.0, rng, f0=55), at(50), 0.0)
    m['synth'].add(synth_pad(['F2', 'C3', 'A3', 'C4'], 12 * BAR, 1.3, rng, pump=0.15, cutoff=(1600, 2600)), at(50), 0.0)
    theme = [('C5', 1.0), ('D5', 0.5), ('F5', 0.5), ('G5', 0.5), ('A5', 0.5), ('C6', 3.0),
             ('D6', 1.5), ('C6', 0.5), ('A5', 1.0), ('G5', 3.0),
             ('A5', 1.0), ('C6', 1.0), ('D6', 1.0), ('F6', 3.0),
             ('E6', 1.5), ('D6', 0.5), ('C6', 1.0), ('D6', 3.0),
             ('D6', 1.0), ('C6', 0.75), ('A5', 0.75), ('G5', 0.5), ('F5', 2.0), ('A5', 1.0),
             ('C6', 1.0), ('A5', 1.0), ('G5', 1.0), ('F5', 3.0)]
    for tr_, kind, dyn, pan, stem in ((0, 'violin', 0.62, 0.15, 'solo'), (1, 'violin', 0.32, 0.35, 'solo'),
                                      (-1, 'cello', 0.5, -0.3, 'solo'), (-1, 'violin', 0.3, -0.05, 'strings')):
        ln, l0 = legato_line(line(theme, at(50), 1.0, transpose=tr_), 0, kind, dyn, rng, vib_cents=18, tail=1.2)
        m[stem].add(ln, l0, pan)
    for t, name, d in events(theme, at(50), transpose=-1):
        m['horns'].add(horn(name, d, 0.8, rng, attack=0.06, release=0.25), t, -0.1)

    # 6. It lets go (bars 62-72): the last F rings; the music box plays the cascade over D; D-17 hops.
    end = at(62)
    m['drums'].add(taiko(1.0, rng, f0=55), end, 0.0)
    m['crash'].add(crash(0.9, rng, length=7.0), end, 0.0)
    chord_strings(m['strings'], end, 5.0, ['F1', 'F2', 'C3', 'A3', 'C4', 'F4', 'A4', 'C5', 'F5'], 0.5, rng, attack=0.05, release=3.0,
                  shape=[1, 0.7, 0.45, 0.3])
    for name in ('A3', 'C4', 'F4'):
        m['horns'].add(horn(name, 3.0, 0.6, rng, attack=0.05, release=2.0, shape=[1, 0.6, 0.3]), end, 0.0)
    string_note(m['tail'], 'D3', end + 4.0, 16, 0.08, 'cello', -0.3, 3, 6, rng=rng)
    string_note(m['tail'], 'A4', end + 5.0, 14, 0.035, 'violin', 0.35, 3, 6, players=1, rng=rng)
    for t, name, d in events(CASCADE, end + 6.0, 1.3):
        m['box'].add(music_box(name, 0.2, rng), t + human(rng, 10), 0.35)
    for t, name, d in events(HOP[:6], end + 15.5):
        m['pizz'].add(pizz(name, 0.42, rng), t + human(rng, 6), 0.25)
    m['pizz'].add(pizz('D5', 0.32, rng), end + 15.5 + 4.2 * B, 0.3)   # and one more, a little late
    return m.render()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='.')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    st = sketch()
    n = int(3.0 * SR)
    st[:, -n:] *= np.linspace(1, 0, n) ** 2
    st = st * (10 ** (-1.0 / 20) / float(np.abs(st).max()))
    st = np.where(np.abs(st) > 0.7, np.sign(st) * (0.7 + 0.25 * np.tanh((np.abs(st) - 0.7) / 0.25)), st)
    st = st + hiss(st.shape[1], 0.0011, np.random.default_rng(5))
    rms = 20 * np.log10(np.sqrt((st ** 2).mean()) + 1e-9)
    print(f'sketch: {st.shape[1] / SR:.1f} s, peak {20 * np.log10(np.abs(st).max()):.1f} dBFS, rms {rms:.1f} dBFS')
    wav = os.path.join(args.out, 'identity_sketch.wav')
    write_wav(wav, st)
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-c:a', 'libmp3lame', '-q:a', '3',
                    os.path.join(args.out, 'identity_sketch.mp3')], check=True)


if __name__ == '__main__':
    main()
