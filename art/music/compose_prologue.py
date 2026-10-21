"""The prologue's theme, "Undelivered": the Order and the Failure.

The lower works are the refuge at its darkest: sealed, graded, rationed, ruled by the Steward under
ORDER ABOVE ALL, and then failed, with the lower rings left to die. The theme is in D Phrygian (D minor
with E-flat, the colour of `racks`), in a rigid 4/4 at 60 bpm, so a bar is 4 s and a beat lines up
with the rest of the score's.

    python3 compose_prologue.py --out prologue      # needs numpy and scipy, and ffmpeg with libmp3lame

It renders the whole theme (about 3:45) and four loops cut from it. Every section sits on the same D
pedal, tempo and bar grid, so the game can crossfade from the theme into a loop, between loops, and
back, on any bar line.

The theme's sections (start s, length s):
      0  32  lower_works  The far machinery, a tolling bell, wind, a high E-flat over D. (loop)
     32  32  order        The tannoy's chime (E, C) and a march: low strings on D, a muffled snare. (loop)
     64  32  anthem       The Steward's anthem on organ and horns, stately and harsh over the march.
                          In its last two bars it runs down like a dying tannoy.
     96  72  failure      Three rounds that build (drums, bells, siren, choir); the first two pull
                          back for a breath. A drop that fades to near silence and the chime alone;
                          then the collapse: E-flat over D, the anthem's opening turned Phrygian.
    168  32  heaps        The lament: a choir and a cello carry the cascade flattened (E-flat for E). (loop)
    200  24  hope         At the edges: the music box plays the parcel's notes with the true E, and
                          D-17 hops once, small. The chime still runs.
The loops: lower_works, order, heaps, and failure (the failure's middle round, held steady).

Each loop file has 2 s of padding either side; the game loops exactly loop_start to loop_end (see
the manifest), so the seam is the same whatever priming delay the MP3 decoder adds.
"""

import argparse
import json
import os
import subprocess

import numpy as np

from compose_dl01 import (SR, body_gain, butter, cymbal_swell, env_curve, far_bell, hiss, human, hz, legato_line,
                          master, music_box, onepole_lp, piano, reverb, smooth_noise, string_note, tape, timp_roll,
                          wind, write_wav)
import compose_dl01
from sketch_identity import (SketchMix, crash, horn, kick, pizz, saw_voice, snare, snare_roll, taiko, tom)

BEAT = 1.0
BAR = 4 * BEAT                # 4/4 at 60 bpm
compose_dl01.BEAT = BEAT      # importing sketch_identity set it to 90 bpm; legato_line counts in beats
P = 8 * BAR                   # every loop is eight bars
TAIL = 12.0                   # room for a section's last notes and reverb
PAD = 2.0


def at(bar, beat=0.0):
    return bar * BAR + beat * BEAT


def line(notes, t0):
    """(time, note, beats) for legato_line from (note, beats)."""
    out, t = [], t0
    for name, beats in notes:
        out.append((t, name, beats))
        t += beats * BEAT
    return out


# The cascade, flattened: the parcel's E becomes E-flat down here.
LAMENT = [('D4', 3), ('C4', 1.5), ('A3', 1.5), ('G3', 2), ('F3', 3), ('Eb3', 2), ('D3', 6)]
# The Steward's anthem: a square, stately hymn in B-flat over the D pedal.
ANTHEM = [('F4', 2), ('Bb4', 1), ('A4', 1), ('G4', 2), ('F4', 2), ('Eb4', 1), ('F4', 1), ('G4', 1), ('Bb4', 1), ('A4', 4),
          ('Bb4', 2), ('C5', 1), ('D5', 1), ('Eb5', 2), ('D5', 2), ('C5', 1), ('Bb4', 1), ('A4', 1), ('G4', 1), ('F4', 4)]
ANTHEM_CHORDS = [['Bb2', 'D3', 'F3', 'Bb3'], ['Eb3', 'G3', 'Bb3', 'Eb4'], ['C3', 'Eb3', 'G3', 'Bb3'], ['F2', 'C3', 'F3', 'A3'],
                 ['G2', 'D3', 'G3', 'Bb3'], ['Eb3', 'G3', 'Bb3', 'Eb4'], ['C3', 'G3', 'C4', 'Eb4'], ['F2', 'C3', 'F3', 'A3']]
# The march: eight quavers a bar on the low strings, two patterns that alternate.
MARCH = [['D2', 'D2', 'D3', 'D2', 'Eb2', 'D2', 'C2', 'D2'], ['D2', 'D2', 'D3', 'D2', 'Bb1', 'C2', 'D2', 'D2']]


# ---------------------------------------------------------------------------
# Instruments
# ---------------------------------------------------------------------------
def drone(name, seconds, level, kind, rng, period=P):
    """A sustained bowed tone that repeats exactly every `period` seconds: each partial is tuned to a
    whole number of cycles per period, and its slow shimmer does whole cycles too."""
    n = int(round(seconds * SR))
    t = np.arange(n) / SR
    f = hz(name)
    out = np.zeros(n)
    for h in range(1, 40):
        fh = h * f
        if fh > 6000:
            break
        fq = round(fh * period) / period
        shimmer = 1 + 0.25 * np.sin(2 * np.pi * rng.integers(1, 4) * t / period + rng.uniform(0, 6.28))
        out += body_gain(fh, kind) / h * shimmer * np.sin(2 * np.pi * fq * t + rng.uniform(0, 6.28))
    out *= 1 + 0.12 * np.sin(2 * np.pi * 2 * t / period + rng.uniform(0, 6.28))
    return (out * level * 0.03).astype(np.float32)


def machine_thud(vel, rng):
    """The far machinery: a low, padded thump, felt more than heard."""
    t = np.arange(int(0.6 * SR)) / SR
    body = np.sin(2 * np.pi * (44 + 20 * np.exp(-t / 0.04)) * t) * np.exp(-t / 0.22)
    rumble = onepole_lp(rng.standard_normal(len(t)).astype(np.float32), 180) * np.exp(-t / 0.08)
    return ((body + rumble * 0.6) * 0.3 * vel).astype(np.float32)


def anvil(vel, rng, f0=820):
    """A struck steel plate: inharmonic, bright, and long enough to ring."""
    t = np.arange(int(2.2 * SR)) / SR
    out = sum(a * np.exp(-t / d) * np.sin(2 * np.pi * f0 * r * t + rng.uniform(0, 6.28))
              for r, a, d in ((1.0, 1.0, 0.7), (2.32, 0.6, 0.45), (4.25, 0.45, 0.3), (6.63, 0.3, 0.2), (9.38, 0.2, 0.12)))
    click = butter(rng.standard_normal(len(t)).astype(np.float32), 3000, 'high') * np.exp(-t / 0.004)
    return ((out + click * 0.5) * 0.08 * vel).astype(np.float32)


def siren(seconds, level, rng):
    """An air-raid siren heard from far off: a horn tone that winds up, holds and winds down."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    u = t / seconds
    up, down = np.clip(u / 0.4, 0, 1), np.clip((u - 0.6) / 0.4, 0, 1)
    f = np.where(u < 0.4, 260 + 330 * up ** 0.7, np.where(u < 0.6, 590, 590 - 330 * down ** 1.3))
    f = f * (1 + 0.004 * np.sin(2 * np.pi * 5 * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    tone = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph)
    amp = np.where(u < 0.4, up ** 0.8, np.where(u < 0.6, 1.0, 1 - down ** 0.8))
    x = np.tanh(1.8 * tone * amp)
    return (butter(x.astype(np.float32), [380, 3000], 'band') * level * 0.05).astype(np.float32)


def tannoy_chime(vel, rng):
    """The public-address chime the game plays before every announcement: E then C, through the
    same narrow, driven horn."""
    t = np.arange(int(3.0 * SR)) / SR
    out = np.zeros_like(t)
    for f0, t0 in ((659.3, 0.05), (523.3, 0.6)):
        u = np.clip(t - t0, 0, None)
        on = (t >= t0)
        out += on * np.exp(-u / 0.9) * (np.sin(2 * np.pi * f0 * u) + 0.25 * np.sin(2 * np.pi * 2 * f0 * u) * np.exp(-u / 0.3))
    x = np.tanh(1.6 * out)
    return (butter(x.astype(np.float32), [380, 3400], 'band') * 0.05 * vel).astype(np.float32)


def choir(names, dur, level, rng, attack=1.5, release=2.0, shape=None):
    """A wordless choir on "ah": detuned saw voices with vibrato through three vowel formants."""
    n = int((dur + release) * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = env_curve(n, attack, release, shape)
    src = np.zeros(n, np.float32)
    for name in names:
        for v in range(4):
            vib = 14 * np.sin(2 * np.pi * rng.uniform(4.6, 5.6) * t + rng.uniform(0, 6.28)) * np.minimum(1, t / 1.0)
            cents = rng.uniform(-9, 9) + vib + 5 * smooth_noise(n, 0.6, rng)
            f = (hz(name) * 2 ** (cents / 1200)).astype(np.float32)
            src += saw_voice(f, env, np.full(n, 3200, np.float32), rng, top=4500)
    voice = sum(butter(src, [fc - bw, fc + bw], 'band') * g for fc, bw, g in ((750, 110, 1.0), (1150, 140, 0.55), (2600, 220, 0.22)))
    return (voice * level * 0.02).astype(np.float32)


def organ(names, dur, level, rng, attack=0.08, release=0.5):
    """A church organ: 16', 8', 4', 2 2/3' and 2' ranks, a slow tremulant, and a little chiff."""
    n = int((dur + release) * SR)
    t = np.arange(n, dtype=np.float32) / SR
    env = env_curve(n, attack, release)
    out = np.zeros(n, np.float32)
    for name in names:
        f = hz(name)
        for ratio, a in ((0.5, 0.45), (1, 1.0), (2, 0.55), (3, 0.28), (4, 0.22), (6, 0.08)):
            if f * ratio > 7000:
                continue
            for det in (-0.6, 0.6):          # two pipes a hair apart
                out += a * np.sin(2 * np.pi * (f * ratio + det) * t + rng.uniform(0, 6.28)).astype(np.float32)
        chiff = butter(rng.standard_normal(n).astype(np.float32), [f * 2, min(f * 8, 9000)], 'band') * np.exp(-t / 0.05)
        out += chiff * 0.4
    out *= 1 + 0.03 * np.sin(2 * np.pi * 5.5 * t)
    return (out * env * level * 0.006).astype(np.float32)


def run_down(st, start, length):
    """The tape running down from `start`: speed falls to about half over `length` seconds, and
    it fades to nothing, the way the game drags a failing tannoy."""
    n = st.shape[1]
    a, m = int(start * SR), int(length * SR)
    u = np.arange(m) / m
    speed = 1 - 0.5 * u ** 1.4
    src = a + np.cumsum(speed)
    out = st.copy()
    for ch in range(2):
        out[ch, a:a + m] = np.interp(src, np.arange(n), st[ch]) * (1 - u) ** 1.3
    out[:, a + m:] = 0
    return out


# ---------------------------------------------------------------------------
# The mix
# ---------------------------------------------------------------------------
class PrologueMix(SketchMix):
    """SketchMix with the prologue's stems, and loops: with a period, each stem is laid three times
    end to end before the room and tape, and the middle period is kept, so the loop is seamless."""

    STEMS = {**SketchMix.STEMS, 'drone': (0.3, 1.0), 'march': (0.38, 7.0), 'choir': (0.55, 3.0), 'organ': (0.55, 4.0),
             'metal': (0.45, 1.5), 'siren': (0.8, 1.0), 'chime': (0.6, 3.0), 'bells': (0.45, 4.0), 'lament': (0.45, 4.0)}

    def render(self, period=None):
        total = None
        for k, tr in self.stems.items():
            wet, gain = self.STEMS[k]
            st = tr.buf
            if period is not None:
                n = int(round(period * SR))
                tiled = np.zeros((2, 3 * n + st.shape[1]), np.float32)
                for i in range(3):
                    tiled[:, i * n:i * n + st.shape[1]] += st
                st = tiled
            if not st.any():
                continue
            if k == 'box':
                st = tape(st, wow=0.0016, period=period)
            st = reverb(st, wet) * gain
            for a, length, back, stems in self.fades:
                if k not in stems:
                    continue
                t = np.arange(st.shape[1]) / SR
                u = np.clip((t - a) / length, 0, 1)
                st = st * (1 - u) + butter(st, 500) * u
                g = (1 - u) ** 2.2
                if back is not None:
                    g = np.where(t >= back, 1.0, g)
                st = (st * g).astype(np.float32)
            total = st if total is None else total + st
        total = tape(total, wow=0.0005, flutter=0.00003, period=period)
        if period is not None:
            total = master(total)
            n = int(round(period * SR))
            return total[:, n:2 * n]
        return total


# ---------------------------------------------------------------------------
# Section builders. Each adds its notes from t = 0; the drone and wind are laid separately.
# ---------------------------------------------------------------------------
def bed(m, seconds, rng, loop):
    """The pedal under everything: D and A, low, and the air in the shafts."""
    for name, kind, level, pan in (('D1', 'bass', 1.0, -0.15), ('D2', 'cello', 0.8, -0.3), ('A2', 'cello', 0.45, 0.05)):
        m['drone'].add(drone(name, seconds, level, kind, rng), 0, pan)
    m['air'].add(wind(seconds, 0.05, rng, circular=loop), 0)


def march_bar(m, bar, pattern, dyn, rng, root_shift=0):
    for j, name in enumerate(pattern):
        if root_shift:
            name = compose_shift(name, root_shift)
        d = dyn * (1.0 if j % 4 == 0 else 0.8 if j % 2 == 0 else 0.62)
        t = at(bar, j * 0.5) + human(rng, 5)
        string_note(m['march'], name, t, 0.32, d, 'cello', -0.25, 0.02, 0.16, players=3, rng=rng)
        low = name[:-1] + str(int(name[-1]) - 1)
        string_note(m['march'], low, t, 0.32, d * 0.7, 'bass', -0.1, 0.02, 0.16, players=2, rng=rng)


NAMES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']


def compose_shift(name, semis):
    """The note `semis` semitones away, spelled with flats."""
    m = compose_dl01.midi(name) + semis
    return NAMES[m % 12] + str(m // 12 - 1)


def snare_march(m, bar, level, rng):
    """A muffled parade snare: one, a ruff into two, three, a pickup into the next bar."""
    for beat, v in ((0, 1.0), (0.75, 0.45), (1.0, 0.8), (2.0, 0.9), (3.0, 0.6), (3.5, 0.5), (3.75, 0.55)):
        m['drums'].add(onepole_lp(snare(level * v * rng.uniform(0.9, 1.0), rng), 3500), at(bar, beat) + human(rng, 4), 0.1)
    m['drums'].add(kick(level * 0.8, rng), at(bar), 0.0)
    m['drums'].add(kick(level * 0.6, rng), at(bar, 2), 0.0)


def sec_lower(m, rng, level=1.0):
    for b in range(32):
        m['drums'].add(machine_thud((0.5 if b % 4 == 0 else 0.3) * level, rng), b * BEAT + human(rng, 8), 0.0)
    for bar in (0, 4):
        m['bells'].add(far_bell('D3', 0.6 * level, rng, length=11), at(bar), -0.1)
    string_note(m['strings'], 'A5', at(1), 10, 0.03 * level, 'violin', 0.4, 3, 3, players=1, rng=rng)
    string_note(m['strings'], 'Bb5', at(4, 2), 9, 0.025 * level, 'violin', 0.45, 3, 3, players=1, rng=rng)
    for bar in (1, 5):
        m['piano'].add(piano('D2', 0.3 * level, 3, rng), at(bar, 2), -0.3)
        m['piano'].add(piano('Eb2', 0.22 * level, 3, rng), at(bar, 2) + 0.06, -0.25)


def sec_order(m, rng, level=1.0, chime=True):
    sec_lower(m, rng, 0.7)
    for bar in range(8):
        march_bar(m, bar, MARCH[bar % 2], 0.2 * level, rng)
        snare_march(m, bar, 0.35 * level, rng)
    if chime:
        for bar in (0, 4):
            m['chime'].add(tannoy_chime(0.8, rng), at(bar), 0.3)
    for bar, names in ((2, ('D3', 'A3')), (6, ('Eb3', 'Bb3'))):
        for name in names:
            m['horns'].add(horn(name, 7.0, 0.35 * level, rng, attack=2.5, release=0.8, shape=[0.4, 1, 0.8]), at(bar), -0.1)


def sec_anthem(m, rng):
    sec_order(m, rng, 1.2, chime=False)
    m['chime'].add(tannoy_chime(0.9, rng), 0.0, 0.3)
    for bar, chord in enumerate(ANTHEM_CHORDS):
        m['organ'].add(organ(chord, BAR, 1.0, rng), at(bar), 0.0)
    for tr_, gain, pan in ((0, 0.8, 0.1), (-12, 0.6, -0.15)):
        t = 0.0
        for name, beats in ANTHEM:
            nm = compose_shift(name, tr_) if tr_ else name
            m['horns'].add(horn(nm, beats * BEAT * 0.95, gain, rng, attack=0.08, release=0.3), t + human(rng, 5), pan)
            t += beats * BEAT


def sec_failure(m, rng):
    # Three rounds of four bars that build; the first two pull back on their last half bar.
    climb = [0, 1, 2, 3]       # round three's bass: D, E-flat, E, F
    for r in range(3):
        for k in range(4):
            bar = 4 * r + k
            shift = climb[k] if r == 2 else 0
            tease = r < 2 and k == 3
            march_bar(m, bar, MARCH[bar % 2], 0.3 + 0.1 * r, rng, shift)
            m['bells'].add(far_bell(compose_shift('D3', shift), 0.7 + 0.15 * r, rng, length=9), at(bar), -0.1)
            if r == 2:
                m['bells'].add(far_bell(compose_shift('A2', shift), 0.6, rng, length=7), at(bar, 2), 0.15)
            for beat in ((0, 2) if not tease else (0,)):
                m['drums'].add(taiko(0.45 + 0.15 * r, rng), at(bar, beat), 0.0)
            for beat in (1, 3):
                m['metal'].add(anvil(0.5 + 0.15 * r, rng), at(bar, beat) + human(rng, 4), 0.2)
            if tease:
                m['drums'].add(kick(0.5, rng), at(bar, 2.5), 0.0)
                m['drums'].add(kick(0.4, rng), at(bar, 3.25), 0.0)
                continue
            if r >= 1:
                snare_march(m, bar, 0.5 + 0.2 * r, rng)
                for j in range(4):
                    m['drums'].add(tom(95 - 8 * j, 0.5, rng), at(bar, 3 + j * 0.25), -0.2 + 0.15 * j)
                for j in range(16):     # strings driving in semiquavers, D against E-flat
                    name = compose_shift(('D4', 'Eb4', 'D4', 'A3')[j % 4], shift)
                    string_note(m['strings'], name, at(bar, j * 0.25) + human(rng, 4), 0.12, 0.12 + 0.05 * r, 'viola', 0.3,
                                0.015, 0.1, players=2, rng=rng)
            if r == 2:
                for beat in (1, 3):
                    m['drums'].add(taiko(0.5, rng, f0=70), at(bar, beat), 0.1)
                for j in range(16):
                    name = compose_shift(('D5', 'Eb5', 'D5', 'A4')[j % 4], shift)
                    string_note(m['strings'], name, at(bar, j * 0.25) + human(rng, 4), 0.12, 0.09, 'violin', 0.45,
                                0.015, 0.1, players=2, rng=rng)
        # The voices of each round.
        if r == 0:
            ln, l0 = legato_line(line([('D4', 2), ('C4', 1), ('A3', 1), ('G3', 2), ('F3', 1), ('Eb3', 1), ('D3', 4)], at(1)),
                                 0, 'cello', 0.5, rng, tail=0.6)
            m['lament'].add(ln, l0, -0.2)
            m['siren'].add(siren(9.0, 0.6, rng), at(1, 1), 0.4)
        elif r == 1:
            for k, names in ((0, ('D3', 'A3', 'D4')), (2, ('Eb3', 'Bb3', 'Eb4'))):
                m['choir'].add(choir(names, 2 * BAR - 0.5, 0.8, rng, attack=1.2, release=1.0), at(4 + k), 0.0)
                for name in names[:2]:
                    m['horns'].add(horn(name, 2 * BAR - 0.3, 0.5, rng, attack=1.5, release=0.5), at(4 + k), -0.1)
        else:
            for k in range(4):
                names = [compose_shift(n, climb[k]) for n in ('D3', 'A3', 'D4', 'A4')]
                m['choir'].add(choir(names, BAR, 0.7 + 0.12 * k, rng, attack=0.4, release=0.4), at(8 + k), 0.0)
                for name in names[:3]:
                    m['horns'].add(horn(name, BAR, 0.45 + 0.08 * k, rng, attack=0.15, release=0.3), at(8 + k), -0.1)
            m['siren'].add(siren(8.0, 0.7, rng), at(9), -0.4)
    snare_roll(m['drums'], at(11), at(12), 0.2, 0.9, rng)
    timp_roll(m['perc'], 'A1', at(11), at(12), 0.3, 1.0, rng)
    m['perc'].add(cymbal_swell(6.0, 4.0, 0.035, rng, decay=1.0), at(11), 0.2)

    # The drop: one blow on D with E-flat against it, then everything fades and darkens; the chime, alone.
    drop = at(12)
    for name in ('D2', 'A2', 'D3', 'Eb3', 'A3', 'D4', 'Eb4', 'A4'):
        string_note(m['strings'], name, drop, 3.5, 0.3, 'cello' if name[-1] in '23' else 'viola', 0.0, 0.03, 0.6, rng=rng)
    m['choir'].add(choir(['D3', 'A3', 'Eb4', 'A4'], 3.5, 1.3, rng, attack=0.05, release=0.6), drop, 0.0)
    m['drums'].add(taiko(1.0, rng, f0=55), drop, 0.0)
    m['metal'].add(anvil(1.0, rng, f0=610), drop, 0.0)
    m['crash'].add(crash(0.8, rng), drop, 0.2)
    m.fades.append((drop + 0.1, 5.0, at(14) - 0.01, ('piano', 'strings', 'solo', 'march', 'horns', 'drums', 'crash', 'perc',
                                                    'choir', 'metal', 'bells', 'siren', 'lament')))
    m['tail'].add(tannoy_chime(0.6, rng), drop + 5.5, 0.3)
    hit = at(14)
    m['tail'].add(cymbal_swell(3.4, 3.0, 0.05, rng, decay=0.3), hit - 3.0, 0.2)
    snare_roll(m['tail'], hit - 2.5, hit - 0.05, 0.03, 0.9, rng, 12, 30)
    timp_roll(m['tail'], 'D2', hit - 3.0, hit, 0.0, 1.0, rng)

    # The collapse: E-flat major over D, everything; the anthem's opening falls in Phrygian; a bare fifth.
    collapse = [(['D1', 'D2'], ['Eb3', 'G3', 'Bb3', 'Eb4', 'G4', 'Bb4']), (['D1', 'D2'], ['Eb3', 'G3', 'Bb3', 'Eb4', 'G4', 'Bb4']),
                (['D1', 'D2'], ['G2', 'D3', 'G3', 'Bb3', 'D4', 'G4']), (['D1', 'D2'], ['D3', 'A3', 'D4', 'A4'])]
    for k, (bass, upper) in enumerate(collapse):
        bar = 14 + k
        last = k == 3
        for name in bass:
            string_note(m['strings'], name, at(bar), BAR + 0.1, 1.0, 'bass' if name == 'D1' else 'cello', -0.2, 0.05, 0.5 if not last else 4,
                        rng=rng)
        for j, name in enumerate(upper):
            string_note(m['strings'], name, at(bar), BAR + 0.1, 0.78, 'viola' if j < 3 else 'violin', -0.3 + 0.12 * j, 0.06,
                        0.5 if not last else 4, rng=rng)
        m['choir'].add(choir(upper[:4], BAR, 2.3, rng, attack=0.1, release=0.5 if not last else 4), at(bar), 0.0)
        for name in upper[:3]:
            m['horns'].add(horn(name, BAR, 1.0, rng, attack=0.06, release=0.4 if not last else 3), at(bar), -0.1)
        m['bells'].add(far_bell('D3', 1.0, rng, length=10), at(bar), -0.1)
        m['bells'].add(far_bell('A2', 0.8, rng, length=8), at(bar, 2), 0.15)
        m['drums'].add(taiko(1.0 if k == 0 else 0.85, rng, f0=55 if k == 0 else 62), at(bar), 0.0)
        m['crash'].add(crash(1.0 if k == 0 else 0.7, rng), at(bar), 0.0 if k == 0 else 0.25)
        if last:
            continue
        m['drums'].add(taiko(0.75, rng), at(bar, 2), 0.0)
        for beat in (1, 3):
            m['metal'].add(anvil(0.85, rng), at(bar, beat), 0.2)
        snare_march(m, bar, 0.9, rng)
    fall = [('F4', 2), ('Bb4', 1), ('A4', 1), ('G4', 2), ('F4', 1), ('Eb4', 1), ('D4', 6)]
    for shift, kind, dyn, pan, stem in ((0, 'violin', 0.8, 0.15, 'lament'), (12, 'violin', 0.4, 0.35, 'lament'),
                                        (-12, 'cello', 0.65, -0.3, 'lament')):
        notes = [(compose_shift(n, shift) if shift else n, b) for n, b in fall]
        ln, l0 = legato_line(line(notes, at(14)), 0, kind, dyn, rng, vib_cents=16, tail=2.0)
        m[stem].add(ln, l0, pan)
    t = at(14)
    for name, beats in fall:
        m['horns'].add(horn(name, beats * 0.95, 1.0, rng, attack=0.06, release=0.4), t, 0.05)
        t += beats


def sec_failure_loop(m, rng):
    """The failure held steady for eight bars: round two's force, without the build, for the set piece."""
    for bar in range(8):
        march_bar(m, bar, MARCH[bar % 2], 0.4, rng)
        snare_march(m, bar, 0.7, rng)
        m['bells'].add(far_bell('D3', 0.85, rng, length=9), at(bar), -0.1)
        for beat in (0, 2):
            m['drums'].add(taiko(0.6, rng), at(bar, beat), 0.0)
        for beat in (1, 3):
            m['metal'].add(anvil(0.65, rng), at(bar, beat) + human(rng, 4), 0.2)
        for j in range(16):
            string_note(m['strings'], ('D4', 'Eb4', 'D4', 'A3')[j % 4], at(bar, j * 0.25) + human(rng, 4), 0.12, 0.17, 'viola',
                        0.3, 0.015, 0.1, players=2, rng=rng)
        if bar % 4 == 3:
            for j in range(4):
                m['drums'].add(tom(95 - 8 * j, 0.5, rng), at(bar, 3 + j * 0.25), -0.2 + 0.15 * j)
    for bar, names in ((0, ('D3', 'A3', 'D4')), (2, ('Eb3', 'Bb3', 'Eb4')), (4, ('D3', 'A3', 'D4')), (6, ('C3', 'G3', 'C4'))):
        m['choir'].add(choir(names, 2 * BAR - 0.5, 0.8, rng, attack=1.2, release=1.0), at(bar), 0.0)
        for name in names[:2]:
            m['horns'].add(horn(name, 2 * BAR - 0.3, 0.5, rng, attack=1.5, release=0.5), at(bar), -0.1)
    m['siren'].add(siren(9.0, 0.6, rng), at(2), 0.4)


def sec_heaps(m, rng):
    for bar, names in ((0, ('D3', 'A3', 'F4')), (2, ('Eb3', 'Bb3', 'G4')), (4, ('G3', 'Bb3', 'D4')), (6, ('D3', 'A3', 'F4'))):
        m['choir'].add(choir(names, 2 * BAR, 0.55, rng, attack=2.0, release=2.0), at(bar), 0.0)
    ln, l0 = legato_line(line(LAMENT, at(1)), 0, 'cello', 0.45, rng, vib_cents=14, tail=2.0,
                         shape=[(at(1), 0.6), (at(2), 1.0), (at(5), 0.8), (at(6, 2), 0.5)])
    m['lament'].add(ln, l0, -0.15)
    for bar in (0, 4):
        m['bells'].add(far_bell('D3', 0.45, rng, length=11), at(bar), -0.1)
    m['piano'].add(piano('D2', 0.28, 3, rng), at(3, 2), -0.3)
    m['piano'].add(piano('Eb2', 0.2, 3, rng), at(3, 2) + 0.06, -0.25)
    string_note(m['strings'], 'A5', at(5), 9, 0.025, 'violin', 0.4, 3, 3, players=1, rng=rng)


def sec_hope(m, rng):
    string_note(m['strings'], 'A5', at(0, 2), 12, 0.025, 'violin', 0.4, 3, 4, players=1, rng=rng)
    for t, name, v in ((at(1), 'F5', 0.32), (at(1) + 1.6, 'E5', 0.28), (at(1) + 3.4, 'D5', 0.3)):
        m['box'].add(music_box(name, v, rng), t, 0.3)
    t = at(3)
    for name, beats in (('C5', 0.5), ('F5', 0.5), (None, 0.5), ('E5', 0.25), ('F5', 0.25), ('A5', 1.0)):
        if name:
            m['pizz'].add(pizz(name, 0.32, rng), t + human(rng, 8), 0.25)
        t += beats * 0.75        # a little slower than he'd like
    m['chime'].add(tannoy_chime(0.35, rng), at(4, 2), 0.35)


SECTIONS = [  # name, builder, bars
    ('lower_works', sec_lower, 8),
    ('order', sec_order, 8),
    ('anthem', sec_anthem, 8),
    ('failure', sec_failure, 18),
    ('heaps', sec_heaps, 8),
    ('hope', sec_hope, 6),
]
CUES = [  # name, from (s), to (s) in the theme, fade in, fade out, the beat it is for
    ('lastcar', 86.0, 96.0, 0.3, 1.0,
     "DL-10: the relocation car leaves with the suitcase. The anthem's closing bars, then the world runs down as he "
     'rides the counterweight down (the run-down starts 3 s in and is gone by 10 s).'),
    ('collapse', 148.5, 172.0, 0.3, 4.0,
     'DL-10: riding the counterweight down, he looks down at ring C. The chime alone, the climb, the collapse, '
     'and the first bar of the lament.'),
]
LOOPS = [  # name, builder, loop file stem, what it is for
    ('lower_works', sec_lower, 'prologue_loop_lower_works', 'Exploring the depot and the dark lower works.'),
    ('order', sec_order, 'prologue_loop_order', 'Rooms of the Order: the ration hall, the relocation lobby, signage and tannoys.'),
    ('heaps', sec_heaps, 'prologue_loop_heaps', 'Among the dead: the racks, the heap, the queue line.'),
    ('failure', sec_failure_loop, 'prologue_loop_failure', 'Set pieces under threat: the slipping cage, a held moment of danger.'),
]


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def render_theme():
    total = sum(bars for _, _, bars in SECTIONS) * BAR
    rng = np.random.default_rng(4142)
    layer = PrologueMix(total + TAIL)
    bed(layer, total + TAIL, rng, loop=False)
    out = layer.render()
    # The pedal fades in under the first bars and away under the last.
    n = out.shape[1]
    t = np.arange(n) / SR
    out *= np.clip(t / 6.0, 0, 1) * np.clip((total + 4 - t) / 12.0, 0, 1)
    # It sinks with the failure's drop (to -20 dB over 5 s) and comes back with the climb into the collapse.
    fail = sum(bars for name, _, bars in SECTIONS[:[s[0] for s in SECTIONS].index('failure')]) * BAR
    drop, hit = fail + at(12), fail + at(14)
    dip = 1 - 0.9 * np.clip((t - drop - 0.1) / 5.0, 0, 1) ** 0.8 * np.clip((hit - t) / 2.5, 0, 1)
    out *= dip.astype(np.float32)
    starts = {}
    t0 = 0.0
    for k, (name, build, bars) in enumerate(SECTIONS):
        length = bars * BAR
        m = PrologueMix(length + TAIL)
        build(m, np.random.default_rng(500 + k))
        st = m.render()
        if name == 'anthem':
            st = run_down(st, length - 2 * BAR + 1.0, 2 * BAR - 1.0)
        i = int(t0 * SR)
        out[:, i:i + st.shape[1]] += st[:, :n - i]
        starts[name] = (t0, length)
        t0 += length
    return master(out)[:, :int((total + 4) * SR)], starts


def render_loop(build, seed):
    rng = np.random.default_rng(seed)
    m = PrologueMix(P + TAIL)
    bed(m, P, rng, loop=True)
    build(m, rng)
    return m.render(period=P)


def finish(st, gain, rng_seed=5):
    st = st * gain
    st = np.where(np.abs(st) > 0.7, np.sign(st) * (0.7 + 0.25 * np.tanh((np.abs(st) - 0.7) / 0.25)), st)
    return (st + hiss(st.shape[1], 0.0011, np.random.default_rng(rng_seed))).astype(np.float32)


def to_mp3(wav, mp3):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-c:a', 'libmp3lame', '-q:a', '3', mp3], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='prologue')
    ap.add_argument('--wav', default=None, help='also keep the WAV masters here')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    wavdir = args.wav or args.out
    os.makedirs(wavdir, exist_ok=True)

    print('rendering the theme', flush=True)
    theme, starts = render_theme()
    # One gain for the theme and every loop, so a crossfade between them keeps its level.
    gain = 10 ** (-1.0 / 20) / float(np.abs(theme).max())
    theme = finish(theme, gain)
    n = int(3.0 * SR)
    theme[:, -n:] *= np.linspace(1, 0, n) ** 2
    files = []
    wav = os.path.join(wavdir, 'prologue_theme.wav')
    write_wav(wav, theme)
    to_mp3(wav, os.path.join(args.out, 'prologue_theme.mp3'))
    files.append(wav)

    # Cues cut from the theme for single story beats, at the theme's gain.
    cues = []
    for name, a, b, fade_in, fade_out, use in CUES:
        x = theme[:, int(a * SR):int(b * SR)].copy()
        x[:, :int(fade_in * SR)] *= np.linspace(0, 1, int(fade_in * SR)) ** 2
        x[:, -int(fade_out * SR):] *= np.linspace(1, 0, int(fade_out * SR)) ** 2
        wav = os.path.join(wavdir, f'prologue_{name}.wav')
        write_wav(wav, x)
        to_mp3(wav, os.path.join(args.out, f'prologue_{name}.mp3'))
        files.append(wav)
        cues.append(dict(name=name, file=f'prologue_{name}.mp3', from_theme=dict(start=a, end=b), seconds=b - a, use=use))

    loops = []
    sections = {build for _, build, _ in SECTIONS}
    for k, (name, build, stem, use) in enumerate(LOOPS):
        print('rendering loop', name, flush=True)
        x = render_loop(build, 900 + k)
        x = x * gain
        x = np.where(np.abs(x) > 0.7, np.sign(x) * (0.7 + 0.25 * np.tanh((np.abs(x) - 0.7) / 0.25)), x)
        x = x + hiss(x.shape[1], 0.0011, np.random.default_rng(5))     # the same length, so the hiss loops too
        pad = int(PAD * SR)
        padded = np.concatenate([x[:, -pad:], x, x[:, :pad]], axis=1).astype(np.float32)
        wav = os.path.join(wavdir, f'{stem}.wav')
        write_wav(wav, padded)
        to_mp3(wav, os.path.join(args.out, f'{stem}.mp3'))
        files.append(wav)
        rms = 20 * np.log10(np.sqrt((x ** 2).mean()) + 1e-9)
        loops.append(dict(name=name, file=f'{stem}.mp3', loop_start=PAD, loop_end=PAD + P, bars=8, rms_dbfs=round(float(rms), 1), use=use,
                          in_theme=dict(start=starts[name][0], end=starts[name][0] + starts[name][1]) if build in sections else None))

    manifest = dict(
        title='Undelivered (prologue theme)', key='D Phrygian (D minor with E-flat)', tempo_bpm=60, meter='4/4', bar_seconds=BAR,
        theme=dict(file='prologue_theme.mp3', sections=[dict(name=k, start=v[0], end=v[0] + v[1]) for k, v in starts.items()]),
        loops=loops,
        cues=cues,
        crossfade=('Every loop and every section sits on the same D pedal, tempo and bar grid. Crossfade on a bar line '
                   '(a multiple of 4 s from a section or loop start) over 2 to 4 s. Loop each file from loop_start to '
                   'loop_end.'))
    with open(os.path.join(args.out, 'prologue_music.json'), 'w') as f:
        json.dump(manifest, f, indent=2)
    if not args.wav:
        for w in files:
            os.remove(w)
    print(json.dumps(manifest, indent=2))


if __name__ == '__main__':
    main()
