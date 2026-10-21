"""A sketch of the score's musical identity: one 80 s cue, not used in the game.

It tries out the identity set out in docs/research/musical_identity.md with the
score's own instruments (from compose_dl01.py), plus three new ones: a plucked
string, a whistle, and a soft analog-style synth pad.

    python3 sketch_identity.py --out /tmp/sketch      # needs numpy and scipy, and ffmpeg with libmp3lame

The shape, in D minor and F major, 3/4 at 60 bpm:
     0-14 s  The pedal. A held F, low and high, with music-box glints from the
             pentatonic (F G A C D) above it.
    14-29 s  The hearth. A plucked string rocks in 3/4; a whistle sings the cascade,
             a pentatonic fall that speeds up and lands on the parcel's F, E, D.
    29-47 s  Plateaus. The strings come in a step at a time (low, middle, high), then
             the synth pad, each step a few dB above the last, never a ramp.
    47-50 s  The breath. Near silence; one music-box note.
    50-61 s  The arrival, without drums. The timpani and cymbal rise out of the
             silence into B-flat (the subdominant), the cascade broad in the violins,
             then F major with D on top.
    61-80 s  Hard cut, long tail. The music box alone plays the cascade, small, and
             stops on E: the last D is left for the listener.
"""

import argparse
import os
import subprocess

import numpy as np

from compose_dl01 import (SR, BAR, HARMONY, Mix, Track, butter, master, reverb, tape, cymbal_swell, env_curve, hiss, human, hz,
                          legato_line, lh_arpeggio, midi, music_box, octave, pan_for, piano, smooth_noise, string_bar,
                          string_note, timp_roll, wind, write_wav)

# The cascade: a pentatonic fall that speeds up, then the parcel's E and D, slower. (note, beats)
CASCADE = [('D6', 1.0), ('C6', 0.75), ('A5', 0.55), ('G5', 0.42), ('F5', 0.9), ('E5', 0.6), ('D5', 1.8)]
GLINTS = [(3.0, 'C6'), (5.2, 'A5'), (6.1, 'D6'), (8.8, 'G5'), (10.4, 'C6'), (12.2, 'F6')]


def events(notes, t0, stretch=1.0, transpose=0):
    out, t = [], t0
    for name, beats in notes:
        out.append((t, octave(name, transpose) if transpose else name, beats * stretch))
        t += beats * stretch
    return out


# ---------------------------------------------------------------------------
# New instruments
# ---------------------------------------------------------------------------
def pluck(name, vel, rng):
    """A plucked steel string with a small, bright body: between a nylon guitar and a banjo."""
    f = hz(name, cents=rng.normal(0, 3))
    length = 3.0
    t = np.arange(int(length * SR)) / SR
    pos = 0.18 + 0.03 * rng.uniform(-1, 1)      # where it is plucked
    out = np.zeros_like(t)
    for n in range(1, 30):
        fn = n * f * (1 + 0.0004 * n * n)
        if fn > 9000:
            break
        a = abs(np.sin(np.pi * n * pos)) / n ** 0.9
        tau = 1.4 * (220 / f) ** 0.35 / n ** 0.65
        out += a * np.exp(-t / tau) * np.sin(2 * np.pi * fn * t + rng.uniform(0, 6.28))
    # The head: a short resonant ring around 900 Hz that colours the attack.
    head = butter(rng.standard_normal(len(t)).astype(np.float32), [700, 1300], 'band') * np.exp(-t / 0.04)
    out = out * np.minimum(1, t / 0.002) + head * 0.6
    return (out * 0.05 * vel).astype(np.float32)


def whistle_line(notes, start, dyn, rng, glide=0.07):
    """A whistled line: a near-sine with breath, a delayed vibrato and small slides between notes.
    Returns (signal, offset) like legato_line."""
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
        inside = (t >= tn) & (t < tn + d)
        u = np.clip((t - tn) / max(d, 1e-3), 0, 1)
        amp = np.where(inside, 0.8 + 0.2 * np.sin(np.pi * u), amp)
    amp *= env_curve(n, 0.08, 0.5)
    since = t - t0
    vib = 18 * np.clip(since / 0.9, 0, 1) * np.sin(2 * np.pi * 5.6 * since) * (0.7 + 0.3 * smooth_noise(n, 1.0, rng))
    f = 2 ** logf * 2 ** ((vib + 4 * smooth_noise(n, 0.8, rng)) / 1200)
    ph = 2 * np.pi * np.cumsum(f, dtype=np.float64) / SR
    tone = np.sin(ph) + 0.06 * np.sin(2 * ph)
    breath = butter(rng.standard_normal(n).astype(np.float32), [1500, 7000], 'band')
    out = (tone * amp + breath * amp * 0.05) * dyn * 0.05
    return out.astype(np.float32), t0 - start


def synth_pad(names, dur, level, rng, pump=0.0, cutoff=(500, 1800)):
    """A soft analog-style pad: detuned saws through a slowly opening low-pass, with an optional
    quaver pump, the one electronic pulse in the identity."""
    n = int(dur * SR)
    t = np.arange(n, dtype=np.float32) / SR
    fc = cutoff[0] + (cutoff[1] - cutoff[0]) * (0.5 - 0.5 * np.cos(np.pi * np.clip(t / dur, 0, 1)))
    out = np.zeros(n, np.float32)
    for name in names:
        for det in (-7, 0, 7):
            f = hz(name, cents=det + rng.normal(0, 1))
            ph0 = rng.uniform(0, 6.28)
            for h in range(1, 40):
                if h * f > 5000:
                    break
                g = (1 / h) / (1 + (h * f / fc) ** 4)
                out += (g * np.sin(2 * np.pi * h * f * t + ph0 * h)).astype(np.float32)
    out *= env_curve(n, min(2.0, dur / 3), min(2.5, dur / 3))
    if pump:
        beat = (t % 0.5) / 0.5
        out *= 1 - pump * np.exp(-beat / 0.12)
    return (out * level * 0.01).astype(np.float32)


class SketchMix(Mix):
    """Mix with three more stems, and cuts: spans where the listed stems, reverb tails included, drop
    to nothing within a quarter of a second (a hard cut, which a long hall would otherwise smear)."""

    def __init__(self, seconds):
        super().__init__(seconds)
        for k, wet, gain in (('pluck', 0.35, 0.33), ('whistle', 0.45, 0.24), ('synth', 0.55, 0.5), ('tail', 0.6, 0.55)):
            self.stems[k] = Track(seconds)
            self.wet[k] = wet
            self.gain[k] = gain
        self.cuts = []      # (start, end or None, stems)

    def render(self, period=None):
        total = None
        for k, tr in self.stems.items():
            st = tr.buf
            if k == 'box':
                st = tape(st, wow=0.0016)
            st = reverb(st, self.wet[k]) * self.gain[k]
            for a, b, stems in self.cuts:
                if k in stems:
                    t = np.arange(st.shape[1]) / SR
                    down = np.clip((t - a) / 0.25, 0, 1)
                    up = np.clip((t - b) / 0.05, 0, 1) if b is not None else 0
                    st = st * np.maximum(1 - down, up).astype(np.float32)
            total = st if total is None else total + st
        return master(tape(total, wow=0.0005, flutter=0.00003))


# ---------------------------------------------------------------------------
# The sketch
# ---------------------------------------------------------------------------
def pluck_bar(tr, t, chord, vel, rng):
    """One bar of rocking quavers: root, fifth, a colour tone, fifth, a higher tone, fifth."""
    root, fifth, colour, top = chord
    for j, name in enumerate((root, fifth, colour, fifth, top, fifth)):
        v = vel * (1.0 if j == 0 else 0.6 if j % 2 else 0.75) * rng.uniform(0.9, 1.05)
        tr.add(pluck(name, v, rng), t + j * 0.5 + human(rng, 9), pan_for(name, 0.6) - 0.2)


def sketch():
    rng = np.random.default_rng(2026)
    total = 80.0
    m = SketchMix(total)
    m['air'].add(wind(total, 0.045, rng) * env_curve(int(total * SR), 4, 14), 0)

    # 1. The pedal: F, low and high, and pentatonic glints.
    string_note(m['strings'], 'F2', 0.0, 46.0, 0.22, 'cello', -0.3, 5, 1.2, shape=[0.5, 1, 1, 1], rng=rng)
    string_note(m['strings'], 'F1', 2.0, 44.0, 0.16, 'bass', -0.15, 6, 1.2, rng=rng)
    string_note(m['strings'], 'F5', 1.0, 45.5, 0.035, 'violin', 0.45, 6, 1.0, shape=[0.6, 1, 1, 0.8], players=1, rng=rng)
    for t, name in GLINTS:
        m['box'].add(music_box(name, 0.24 * rng.uniform(0.85, 1.1), rng), t, 0.4)

    # 2. The hearth: the pluck rocks over the pedal; the whistle sings the cascade twice.
    hearth = [('F2', 'C3', 'A3', 'C4'), ('F2', 'C3', 'G3', 'D4'), ('F2', 'C3', 'A3', 'C4'), ('F2', 'C3', 'G3', 'A3'),
              ('F2', 'C3', 'A3', 'D4')]
    for k, chord in enumerate(hearth):
        pluck_bar(m['pluck'], 14.0 + k * BAR, chord, 0.5 + 0.05 * min(k, 2), rng)
    w, off = whistle_line(events(CASCADE, 0), 0, 0.9, rng)
    m['whistle'].add(w, 17.0 + off, 0.15)
    w, off = whistle_line(events(CASCADE[:5], 0, 0.9), 0, 0.75, rng)
    m['whistle'].add(w, 23.5 + off, 0.15)
    for t, name, v in ((26.6, 'F5', 0.36), (27.3, 'E5', 0.3), (28.3, 'D5', 0.34)):   # the parcel answers
        m['box'].add(music_box(name, v, rng), t, 0.3)

    # 3. Plateaus: phrase A's harmony at 4.5 s a bar, one layer added per step.
    t0, bl = 29.0, 4.5
    bars = [0, 1, 2, 3]
    for k, bar in enumerate(bars):
        t = t0 + k * bl
        h = HARMONY[bar]
        low = h['bass'] if midi(h['bass']) >= midi('C2') else octave(h['bass'], 1)
        pluck_bar(m['pluck'], t, (low, h['lh'][0], h['lh'][1], h['lh'][2]), 0.45, rng)
        pluck_bar(m['pluck'], t + BAR, (octave(h['bass'], 1), h['lh'][0], h['lh'][2], h['lh'][1]), 0.38, rng)
        # Step 1: low strings.  Step 2: the middle.  Step 3: violins in octaves with the cascade.
        string_bar(m['strings'], bar, t, 0.27 + 0.04 * k, rng, bars=bl / BAR, bass=True, attack=0.6, release=0.5,
                   upper_kind='viola' if k >= 1 else 'cello')
        if k >= 2:
            lh_arpeggio(m['piano'], bar, t, 0.22, rng, 'sparse')
    vl, voff = legato_line(events(CASCADE, 0, 1.25), 0, 'violin', 0.32, rng, vib_cents=14, tail=0.4)
    m['solo'].add(vl, t0 + 2 * bl + voff, 0.2)
    v8, v8off = legato_line(events(CASCADE, 0, 1.25, transpose=-1), 0, 'violin', 0.2, rng, vib_cents=12, tail=0.4)
    m['strings'].add(v8, t0 + 2 * bl + v8off, 0.35)
    # Step 4: the pad and its pump, on G minor 7 (the last plateau).
    m['synth'].add(synth_pad(['G2', 'D3', 'Bb3', 'F4'], bl + 0.6, 0.9, rng, pump=0.35, cutoff=(400, 1600)), t0 + 3 * bl, 0.0)

    # 4. The breath: everything has released by 47.5; one note.
    breath = t0 + 4 * bl        # 47.0
    m.cuts.append((breath + 0.2, breath + 1.5, ('piano', 'strings', 'solo', 'pluck', 'whistle', 'synth', 'air')))
    m['box'].add(music_box('C6', 0.11, rng), breath + 0.9, 0.4)

    # 5. The arrival, on B-flat, out of the silence: roll and cymbal rise from nothing.
    peak = breath + 3.4         # 50.4
    timp_roll(m['perc'], 'Bb1', breath + 1.6, peak, 0.0, 0.75, rng, hit=0.8)
    m['perc'].add(cymbal_swell(9, 1.8, 0.02, rng, decay=1.6), breath + 1.6, 0.2)
    for name, kind, pan, d in (('Bb1', 'bass', -0.15, 0.5), ('Bb2', 'cello', -0.3, 0.55), ('F3', 'cello', -0.2, 0.42),
                               ('D4', 'viola', 0.0, 0.4), ('C4', 'viola', 0.1, 0.32), ('F4', 'violin', 0.25, 0.34),
                               ('A4', 'violin', 0.35, 0.28)):
        string_note(m['strings'], name, peak, 5.2, d, kind, pan, 0.35, 1.2, shape=[1, 0.95, 0.85], rng=rng)
    m['synth'].add(synth_pad(['Bb2', 'F3', 'C4', 'D4'], 10.4, 1.2, rng, cutoff=(900, 2400)), peak, 0.0)
    for j, name in enumerate(('Bb1', 'F2', 'D3', 'A3', 'C4', 'F4')):
        m['piano'].add(piano(name, 0.5 - 0.03 * j, 5, rng), peak + 0.03 * j, pan_for(name))
    broad = events(CASCADE, 0, 1.45)
    for transpose, kind, dyn, pan in ((0, 'violin', 0.55, 0.15), (1, 'violin', 0.26, 0.35), (-1, 'cello', 0.36, -0.3)):
        ln, lo = legato_line(broad if not transpose else events(CASCADE, 0, 1.45, transpose=transpose), 0, kind, dyn, rng,
                             vib_cents=16, tail=0.3)
        m['solo'].add(ln, peak + lo, pan)
    # Then F major with D on top (F6): home, but not closed.
    t_f = peak + 5.2
    for name, kind, pan, d in (('F1', 'bass', -0.15, 0.42), ('F2', 'cello', -0.3, 0.46), ('C3', 'cello', -0.2, 0.36),
                               ('A3', 'viola', 0.0, 0.34), ('C4', 'viola', 0.1, 0.3), ('F4', 'violin', 0.25, 0.3),
                               ('D5', 'violin', 0.35, 0.24)):
        string_note(m['strings'], name, t_f, 5.6, d, kind, pan, 0.6, 0.25, shape=[0.9, 1, 0.95], rng=rng)
    for j, name in enumerate(('F1', 'C2', 'A2', 'F3', 'C4', 'D5')):
        m['piano'].add(piano(name, 0.4 - 0.03 * j, 5.4, rng), t_f + 0.03 * j, pan_for(name))

    # 6. Hard cut, long tail: the music box alone, the cascade small, stopping on E.
    cut = t_f + 5.8             # about 61.4
    m.cuts.append((cut, None, ('piano', 'strings', 'solo', 'synth', 'perc')))
    string_note(m['tail'], 'A5', cut + 0.2, 16, 0.035, 'violin', 0.4, 0.3, 8, shape=[1, 0.8, 0.5], players=1, rng=rng)
    string_note(m['tail'], 'D3', cut + 2.0, 14, 0.06, 'cello', -0.3, 4, 8, rng=rng)
    for t, name, d in events(CASCADE[:-1], cut + 1.2, 1.6):
        m['box'].add(music_box(name, 0.13 * rng.uniform(0.9, 1.05), rng), t + human(rng, 12), 0.35)
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
