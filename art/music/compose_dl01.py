"""Chapter 1 (DL-01 to DL-04): the score.

Renders four cues for the playable scene from a written score with small
synthesized instruments: a felt piano, an old music box, a string section, a
solo cello, and wind and room tone. All are mixed through a convolution hall
and a little tape.

    python compose_dl01.py --out ../../game/undelivered/assets/music

The cues:
    wake  ~56 s  The opening and the first steps. The music box remembers three
                 notes, then the felt piano finds the theme and leaves it unfinished.
    bed   48 s   A seamless loop under play: a low string pad and stray piano notes.
    hall  ~56 s  The sorting-hall reveal. The cello carries the theme over strings
                 and a broken piano, swells into the E-flat bar, and stays open.
    end   ~96 s  The bulkhead opens. The whole theme on piano and strings, then a
                 picardy D major and a music box winding down through a birthday tune.

The theme is in D minor, 3/4, at 60 bpm, so a bar lasts 3 s. It has two
eight-bar phrases (A and B, see THEME and HARMONY).

The bed loop is written so that one period sits between LOOP_PAD and
LOOP_PAD + BED_LEN. The game loops exactly that span, so the seam is the same
whatever priming delay the MP3 decoder adds.
"""

import argparse
import os
import subprocess
import wave

import numpy as np
from scipy import signal

SR = 44100
BEAT = 1.0          # 60 bpm
BAR = 3 * BEAT
BED_LEN = 48.0
LOOP_PAD = 2.0
RNG = np.random.default_rng(1949)   # the year the parcel was posted

NAMES = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}


def midi(name):
    n = NAMES[name[0]]
    i = 1
    while i < len(name) and name[i] in '#b':
        n += 1 if name[i] == '#' else -1
        i += 1
    return n + 12 * (int(name[i:]) + 1)


def hz(name, cents=0.0):
    m = midi(name) if isinstance(name, str) else name
    return 440.0 * 2 ** ((m - 69 + cents / 100) / 12)


def octave(name, k):
    i = 1
    while name[i] in '#b':
        i += 1
    return name[:i] + str(int(name[i:]) + k)


# ---------------------------------------------------------------------------
# The theme
# ---------------------------------------------------------------------------
# Melody per bar as (note, beats). Phrase A is bars 1-8, phrase B bars 9-16.
THEME = [
    [('F5', 1.5), ('E5', 0.5), ('D5', 1)],
    [('D5', 2), ('A4', 1)],
    [('C5', 1.5), ('Bb4', 0.5), ('A4', 1)],
    [('G4', 3)],
    [('F5', 1.5), ('E5', 0.5), ('D5', 1)],
    [('D5', 1), ('F5', 1), ('A5', 1)],
    [('G5', 1.5), ('F5', 0.5), ('E5', 1)],
    [('E5', 2), ('C#5', 1)],
    [('D5', 2), ('F5', 1)],
    [('A5', 1.5), ('G5', 0.5), ('F5', 1)],
    [('G5', 1), ('F5', 1), ('D5', 1)],
    [('A4', 3)],
    [('G5', 1.5), ('F5', 0.5), ('Eb5', 1)],
    [('D5', 2), ('Bb4', 1)],
    [('C5', 1), ('Bb4', 1), ('G4', 1)],
    [('A4', 3)],
    # 17-18: a cadence into the relative major, for DL-03's renewed purpose.
    [('G5', 1.5), ('F5', 0.5), ('E5', 1)],
    [('F5', 3)],
]

# Harmony per bar: (bass, piano left-hand tones, string upper voices). A bar
# that turns from Asus4 to A on beat 3 carries the second voicing in 'turn'.
HARMONY = [
    dict(bass='D2', lh=['A2', 'E3', 'F3'], up=['F3', 'A3', 'E4']),
    dict(bass='Bb1', lh=['F2', 'D3', 'A3'], up=['F3', 'A3', 'D4']),
    dict(bass='A1', lh=['F2', 'C3', 'A3'], up=['F3', 'A3', 'C4']),
    dict(bass='G1', lh=['D2', 'Bb2', 'F3'], up=['F3', 'Bb3', 'D4']),
    dict(bass='D2', lh=['A2', 'D3', 'F3'], up=['F3', 'A3', 'D4']),
    dict(bass='Bb1', lh=['F2', 'D3', 'A3'], up=['F3', 'A3', 'D4']),
    dict(bass='G1', lh=['D2', 'Bb2', 'E3'], up=['E3', 'Bb3', 'D4']),
    dict(bass='A1', lh=['E2', 'A2', 'D3'], up=['E3', 'A3', 'D4'], turn=dict(lh=['C#3', 'E3'], up=['E3', 'A3', 'C#4'])),
    dict(bass='Bb1', lh=['F2', 'Bb2', 'D3'], up=['F3', 'Bb3', 'D4']),
    dict(bass='A1', lh=['F2', 'C3', 'F3'], up=['F3', 'A3', 'C4']),
    dict(bass='G1', lh=['D2', 'G2', 'Bb2'], up=['G3', 'Bb3', 'D4']),
    dict(bass='F1', lh=['A2', 'D3', 'F3'], up=['F3', 'A3', 'D4']),
    dict(bass='Eb2', lh=['Bb2', 'D3', 'G3'], up=['G3', 'Bb3', 'D4']),
    dict(bass='D2', lh=['F2', 'Bb2', 'D3'], up=['F3', 'Bb3', 'D4']),
    dict(bass='Bb1', lh=['D2', 'G2', 'Bb2'], up=['G3', 'Bb3', 'D4']),
    dict(bass='A1', lh=['E2', 'A2', 'D3'], up=['E3', 'A3', 'D4'], turn=dict(lh=['C#3', 'E3'], up=['E3', 'A3', 'C#4'])),
    dict(bass='C2', lh=['G2', 'C3', 'E3'], up=['E3', 'G3', 'C4']),
    dict(bass='F1', lh=['C2', 'F2', 'A2'], up=['F3', 'A3', 'C4']),
]


def melody_events(bars, t0, transpose=0, skip=()):
    """(time, note, beats) for the given 0-based theme bars, starting at t0."""
    out = []
    for k, b in enumerate(bars):
        t = t0 + k * BAR
        for j, (n, beats) in enumerate(THEME[b]):
            if (b, j) not in skip:
                out.append((t, octave(n, transpose) if transpose else n, beats))
            t += beats * BEAT
    return out


# ---------------------------------------------------------------------------
# Building blocks
# ---------------------------------------------------------------------------
class Track:
    """A stereo buffer that notes are dropped into."""

    def __init__(self, seconds):
        self.buf = np.zeros((2, int(seconds * SR) + 1), np.float32)

    def add(self, x, start, pan=0.0, gain=1.0):
        i = int(round(start * SR))
        if i < 0:
            x, i = x[-i:], 0
        n = min(len(x), self.buf.shape[1] - i)
        if n <= 0:
            return
        a = (pan + 1) * np.pi / 4
        self.buf[0, i:i + n] += x[:n] * (np.cos(a) * gain)
        self.buf[1, i:i + n] += x[:n] * (np.sin(a) * gain)


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    return signal.lfilter([1 - a], [1, -a], x).astype(np.float32)


def butter(x, fc, kind='low', order=2):
    sos = signal.butter(order, fc, kind, fs=SR, output='sos')
    return signal.sosfilt(sos, x, axis=-1).astype(np.float32)


def smooth_noise(n, rate, rng):
    """Slow random wander in [-1, 1], about `rate` changes per second."""
    k = max(2, int(n / SR * rate) + 3)
    pts = rng.uniform(-1, 1, k)
    xs = np.linspace(0, k - 1, n)
    i = np.floor(xs).astype(int).clip(0, k - 2)
    f = xs - i
    f = f * f * (3 - 2 * f)
    return (pts[i] * (1 - f) + pts[i + 1] * f).astype(np.float32)


def pan_for(name, spread=0.5):
    """Low notes a little left, high notes a little right, as heard from the bench."""
    return float(np.clip((midi(name) - 62) / 30, -1, 1)) * spread


# ---------------------------------------------------------------------------
# Instruments
# ---------------------------------------------------------------------------
def piano(name, vel, dur, rng=RNG):
    """A felt piano: soft hammers, two slightly detuned strings, a damper."""
    f = hz(name)
    tau2 = min(14.0, 7.5 * (261.6 / f) ** 0.7)
    tau1 = tau2 * 0.14
    length = dur + 0.9 if dur < tau2 * 1.5 else tau2 * 1.5 + 0.9
    t = np.arange(int(length * SR)) / SR
    B = 1.1e-4 * (f / 261.6) ** 1.1
    tilt = 0.55 - 0.25 * vel        # softer means darker
    hammer = 0.12 + 0.02 * rng.uniform(-1, 1)
    out = np.zeros_like(t)
    for n in range(1, 40):
        fn = n * f * np.sqrt(1 + B * n * n)
        if fn > 9000:
            break
        a = n ** -0.8 * np.exp(-(n - 1) * tilt) * (0.25 + abs(np.sin(np.pi * n * hammer)))
        if a < 1e-4:
            continue
        e = 0.62 * np.exp(-t / (tau1 / (1 + 0.25 * (n - 1)))) + 0.38 * np.exp(-t / (tau2 / (1 + 0.32 * (n - 1))))
        d = 0.00035 * rng.uniform(0.5, 1.4)
        p1, p2 = rng.uniform(0, 2 * np.pi, 2)
        out += a * e * 0.5 * (np.sin(2 * np.pi * fn * (1 + d) * t + p1) + np.sin(2 * np.pi * fn * (1 - d) * t + p2))
    att = 0.006 + 0.01 * (1 - vel)
    out *= np.minimum(1, t / att) ** 1.5
    damp = t > dur
    out[damp] *= np.exp(-(t[damp] - dur) / 0.22)
    # The felt: a short muffled thump under the note.
    thump = rng.standard_normal(len(t)).astype(np.float32) * np.exp(-t / 0.018)
    out += onepole_lp(thump, 500) * 0.25 * vel
    out = onepole_lp(out, 1800 + 3500 * vel)
    return (out * (0.12 * vel ** 1.5)).astype(np.float32)


def music_box(name, vel, rng=RNG):
    """An old music box tine: a bright pluck, a clear fundamental, slightly out of tune."""
    f = hz(name, cents=rng.normal(0, 5))
    length = 3.6
    t = np.arange(int(length * SR)) / SR
    tau = 1.9 * (880 / f) ** 0.45
    out = np.zeros_like(t)
    for ratio, amp, td in ((1.0, 1.0, tau), (2.0, 0.05, tau * 0.3), (5.93, 0.16, 0.16), (17.4, 0.05, 0.025)):
        fn = f * ratio
        if fn < 16000:
            out += amp * np.exp(-t / td) * np.sin(2 * np.pi * fn * t + rng.uniform(0, 6.28))
    click = rng.standard_normal(len(t)).astype(np.float32) * np.exp(-t / 0.0015)
    out += butter(click, 3000, 'high') * 0.12
    out *= np.minimum(1, t / 0.001)
    return (out * (0.06 * vel)).astype(np.float32)


_TIMP = {}


def timp_stroke(name, rng=RNG):
    """One soft-mallet timpani stroke at full level (cached per pitch)."""
    if name not in _TIMP:
        f = hz(name)
        t = np.arange(int(2.6 * SR)) / SR
        out = np.zeros_like(t)
        for ratio, amp, tau in ((1.0, 1.0, 1.3), (1.504, 0.45, 0.7), (1.742, 0.22, 0.45), (2.0, 0.3, 0.5), (2.245, 0.1, 0.3)):
            out += amp * np.exp(-t / tau) * np.sin(2 * np.pi * f * ratio * t * (1 + 0.006 * np.exp(-t / 0.06)) + rng.uniform(0, 6.28))
        thump = onepole_lp(rng.standard_normal(len(t)).astype(np.float32), 300) * np.exp(-t / 0.025)
        out = (out * np.minimum(1, t / 0.004) + thump * 1.5).astype(np.float32)
        _TIMP[name] = onepole_lp(out, 1800)
    return _TIMP[name]


def timp_roll(tr, name, t0, t1, dyn0, dyn1, rng=RNG, rate=15.0, hit=0.0):
    """A roll that swells from dyn0 to dyn1, optionally ending on an accented stroke."""
    x = timp_stroke(name, rng)
    t, k = t0, 0
    while t < t1:
        u = (t - t0) / max(1e-3, t1 - t0)
        v = dyn0 + (dyn1 - dyn0) * u ** 1.6
        tr.add(x * (0.035 * v * rng.uniform(0.8, 1.0)), t + rng.normal(0, 0.005), -0.1 if k % 2 else 0.05)
        t += 1.0 / rate
        k += 1
    if hit:
        tr.add(x * (0.07 * hit), t1, 0.0)


def cymbal_swell(seconds, peak, level, rng=RNG, decay=1.6):
    """A mallet roll on a suspended cymbal: shimmer rising to `peak` s, then ringing away."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    x = butter(rng.standard_normal(n).astype(np.float32), [2500, 13000], 'band')
    ring = sum(butter(rng.standard_normal(n).astype(np.float32), [f * 0.97, f * 1.03], 'band') * a
               for f, a in ((3150, 0.6), (5300, 0.5), (7900, 0.35)))
    env = np.where(t < peak, (t / peak) ** 3, np.exp(-(t - peak) / decay))
    trem = 1 + 0.25 * np.sin(2 * np.pi * 11 * t)
    return ((x + ring) * env * trem * level).astype(np.float32)


def far_bell(name, vel, rng=RNG, length=11.0):
    """A distant tower bell struck softly: hum, prime, a minor tierce, quint and nominal, heard through the
    building (so dark, and with a padded strike rather than a clang). `name` is the strike note (prime)."""
    f = hz(name, cents=rng.normal(0, 4))
    t = np.arange(int(length * SR)) / SR
    out = np.zeros_like(t)
    # (ratio to the prime, amplitude, decay seconds)
    for ratio, amp, tau in ((0.5, 0.55, 5.5), (1.0, 1.0, 3.6), (1.2, 0.5, 2.6), (1.5, 0.22, 1.8), (2.0, 0.45, 1.5),
                            (2.51, 0.12, 0.8), (2.66, 0.1, 0.7), (3.01, 0.08, 0.5)):
        # Each partial a pair a fraction of a hertz apart: the slow beating of a cast bell.
        beat = rng.uniform(0.15, 0.6)
        ph = rng.uniform(0, 6.28)
        out += amp * np.exp(-t / tau) * (np.sin(2 * np.pi * f * ratio * t + ph) + 0.6 * np.sin(2 * np.pi * (f * ratio + beat) * t + ph))
    out *= np.minimum(1, t / 0.025) ** 2       # a padded strike
    out = onepole_lp(out.astype(np.float32), 1400)
    return (out * (0.018 * vel)).astype(np.float32)


STRING_BODY = {
    # (formant centre Hz, relative gain, width in octaves), plus a top cut-off.
    'violin': ([(300, 0.6, 0.6), (1000, 0.9, 0.7), (2800, 0.7, 0.5)], 5200),
    'viola': ([(250, 0.7, 0.6), (850, 0.9, 0.7), (2300, 0.5, 0.5)], 4200),
    'cello': ([(180, 0.9, 0.6), (600, 0.8, 0.7), (1600, 0.5, 0.6)], 3200),
    'bass': ([(100, 1.0, 0.7), (380, 0.6, 0.7), (1100, 0.3, 0.6)], 1800),
}


def body_gain(freq, kind):
    peaks, top = STRING_BODY[kind]
    g = 0.25
    for fc, amp, width in peaks:
        g += amp * np.exp(-0.5 * (np.log2(freq / fc) / width) ** 2)
    return g / (1 + (freq / top) ** 4)


def bowed(freq, amp, kind, rng=RNG, vib_cents=12.0, players=3, detune=6.0):
    """A bowed string section (or a soloist with players=1) from a pitch curve and a dynamic curve.

    `freq` and `amp` are per-sample arrays. Louder playing brightens the tone.
    """
    n = len(freq)
    t = np.arange(n, dtype=np.float32) / SR
    out = np.zeros(n, np.float32)
    peak = max(1e-6, float(amp.max()))
    level = (amp / peak).astype(np.float32)
    f0 = float(np.median(freq))
    for p in range(players):
        rate = 5.1 + rng.uniform(-0.4, 0.4)
        onset = np.minimum(1, t / 0.6) if players > 1 else 1.0
        vib = vib_cents * onset * np.sin(2 * np.pi * rate * t + rng.uniform(0, 6.28))
        vib = vib * (0.75 + 0.25 * smooth_noise(n, 1.5, rng))
        wander = 3.0 * smooth_noise(n, 0.7, rng)
        cents = vib + wander + (rng.uniform(-detune, detune) if players > 1 else 0)
        f = freq * 2 ** (cents / 1200)
        phase = 2 * np.pi * np.cumsum(f, dtype=np.float64) / SR
        lag = int(rng.uniform(0, 0.05) * SR) if players > 1 else 0
        lv = np.concatenate([np.zeros(lag, np.float32), level[:n - lag]]) if lag else level
        lv = np.minimum(1, lv * (1 + 0.06 * smooth_noise(n, 2.5, rng)))  # bow pressure
        for h in range(1, 48):
            fh = h * f0
            if fh > 7500:
                break
            g = body_gain(fh, kind) / h
            out += g * np.power(lv, 1 + 0.16 * (h - 1)) * np.sin(h * phase + rng.uniform(0, 6.28)).astype(np.float32)
    hiss = butter(rng.standard_normal(n).astype(np.float32), [1800, 5000], 'band') * level * 0.006
    return (out / players ** 0.6 + hiss) * (peak * 0.04)


def env_curve(n, attack, release, shape=None):
    """A note envelope: smooth attack, optional dynamic shape, smooth release."""
    t = np.arange(n, dtype=np.float32) / SR
    total = n / SR
    a = np.clip(t / max(attack, 1e-3), 0, 1)
    r = np.clip((total - t) / max(release, 1e-3), 0, 1)
    e = (a * a * (3 - 2 * a)) * (r * r * (3 - 2 * r))
    if shape is not None:
        e *= np.interp(t / total, np.linspace(0, 1, len(shape)), shape).astype(np.float32)
    return e


def string_note(tr, name, start, dur, dyn, kind, pan=0.0, attack=1.2, release=1.8, shape=None, players=3, rng=RNG):
    n = int((dur + release) * SR)
    e = env_curve(n, attack, release, shape) * dyn
    tr.add(bowed(np.full(n, hz(name), np.float32), e, kind, rng, players=players), start, pan)


def legato_line(notes, start, kind, dyn, rng=RNG, glide=0.09, vib_cents=20.0, tail=1.6, shape=None):
    """One connected, sung line for a soloist: notes as (time, name, beats) relative to start.

    `shape`, if given, is a dynamic curve over the line as (time, level) points (times as in `notes`), so a
    phrase can swell and fall away; louder playing brightens the tone, as with the bow."""
    end = notes[-1][0] + notes[-1][2] * BEAT + tail
    n = int((end - notes[0][0] + 0.3) * SR)
    t0 = notes[0][0] - 0.3
    t = np.arange(n, dtype=np.float32) / SR + t0
    logf = np.full(n, np.log2(hz(notes[0][1])), np.float32)
    amp = np.zeros(n, np.float32)
    for k, (tn, name, beats) in enumerate(notes):
        lf = np.log2(hz(name))
        if k > 0:
            s = np.clip((t - tn + glide * 0.5) / glide, 0, 1)
            s = s * s * (3 - 2 * s)
            prev = np.log2(hz(notes[k - 1][1]))
            logf = np.where(t >= tn - glide * 0.5, prev + (lf - prev) * s, logf)
        d = beats * BEAT
        u = np.clip((t - tn) / d, 0, 1)
        inside = (t >= tn) & (t < tn + d + (tail if k == len(notes) - 1 else 0.05))
        # Each note swells a little and eases, with a soft bow change at the start.
        swell = (0.78 + 0.22 * np.sin(np.pi * np.minimum(u, 1) ** 0.8)) * np.minimum(1, (t - tn) / 0.12 + 0.55)
        amp = np.where(inside, np.maximum(amp, swell), amp)
    amp *= env_curve(n, 0.35, tail)
    if shape is not None:
        st, sv = zip(*shape)
        amp *= np.interp(t, st, sv).astype(np.float32)
    return bowed((2 ** logf).astype(np.float32), amp * dyn, kind, rng, vib_cents=vib_cents, players=1), t0 - start


def wind(seconds, level, rng=RNG, circular=False):
    """Air moving through a large, cold building, and a low room tone."""
    n = int(seconds * SR)
    spec = np.fft.rfft(rng.standard_normal(n))
    fr = np.fft.rfftfreq(n, 1 / SR)
    shape = np.exp(-0.5 * (np.log2(np.maximum(fr, 1) / 220) / 1.1) ** 2) + 0.6 * np.exp(-0.5 * (np.log2(np.maximum(fr, 1) / 60) / 0.6) ** 2)
    x = np.fft.irfft(spec * shape, n).astype(np.float32)
    x /= np.abs(x).max() + 1e-9
    if circular:
        # Swells that repeat exactly every period.
        k = np.arange(n) / n * 2 * np.pi
        mod = 0.65 + 0.2 * np.sin(2 * k + 1.0) + 0.15 * np.sin(5 * k + 2.3)
    else:
        mod = 0.7 + 0.3 * smooth_noise(n, 0.12, rng)
    return x * mod.astype(np.float32) * level


# ---------------------------------------------------------------------------
# The room and the tape
# ---------------------------------------------------------------------------
def make_ir(seconds=4.2, rng=np.random.default_rng(7)):
    """A stereo hall with early reflections and a darker, longer low end."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    fr = np.fft.rfftfreq(n, 1 / SR)
    ir = np.zeros((2, n))
    for ch in range(2):
        tail = np.zeros(n)
        for lo, hi, rt in ((0, 400, 4.0), (400, 3000, 3.2), (3000, 22050, 1.5)):
            spec = np.fft.rfft(rng.standard_normal(n))
            spec[(fr < lo) | (fr >= hi)] = 0
            tail += np.fft.irfft(spec, n) * np.exp(-6.9 * t / rt)
        tail *= np.clip((t - 0.03) / 0.08, 0, 1)
        for d, g in ((0.011, 0.5), (0.019, 0.35), (0.027, 0.3), (0.041, 0.22), (0.053, 0.18)):
            tail[int((d + 0.004 * ch * rng.uniform()) * SR)] += g * rng.choice([-1, 1]) * 3
        ir[ch] = tail
    return (ir / np.sqrt((ir ** 2).sum(axis=1, keepdims=True))).astype(np.float32)


IR = None


def reverb(st, wet, circular_len=None):
    global IR
    if IR is None:
        IR = make_ir()
    out = np.zeros_like(st)
    for ch in range(2):
        out[ch] = signal.fftconvolve(st[ch], IR[ch])[:st.shape[1]]
    return st * (1 - wet * 0.45) + out * wet


def tape(st, wow=0.0012, flutter=0.00005, period=None):
    """Wow and flutter: the gentle pitch drift of an old recording."""
    n = st.shape[1]
    t = np.arange(n) / SR
    fw, ff = (0.37, 6.3) if period is None else (round(0.37 * period) / period, round(6.3 * period) / period)
    d = wow * np.sin(2 * np.pi * fw * t) + flutter * np.sin(2 * np.pi * ff * t + 1.1)
    src = np.clip(t + d - wow, 0, None) * SR
    return np.stack([np.interp(src, np.arange(n), st[ch]) for ch in range(2)]).astype(np.float32)


def hiss(n, level, rng=RNG):
    x = rng.standard_normal((2, n)).astype(np.float32)
    return butter(x, [3000, 12000], 'band') * level


def master(st):
    st = butter(st, 28, 'high')
    st = butter(st, 13000, 'low')
    return np.tanh(st * 1.2) / 1.2


# ---------------------------------------------------------------------------
# Arranging helpers
# ---------------------------------------------------------------------------
def human(rng, ms=14):
    return rng.normal(0, ms / 1000)


def play_melody(tr, events, vel, rng=RNG, legato=1.05, accents=None):
    for k, (t, name, beats) in enumerate(events):
        v = vel * (accents[k] if accents else 1) * rng.uniform(0.92, 1.05)
        tr.add(piano(name, min(1, v), beats * BEAT * legato, rng), t + human(rng), pan_for(name))


def lh_arpeggio(tr, bar, t, vel, rng=RNG, pattern='flow'):
    """The piano's left hand for one bar of HARMONY."""
    h = HARMONY[bar]
    lh = h['lh']
    turn = h.get('turn')
    if pattern == 'flow':
        # Six quavers: bass, then up and back down through the chord.
        seq = [h['bass'], lh[0], lh[1], lh[2], lh[1], lh[0]]
        if turn:
            seq[4], seq[5] = turn['lh'][0], turn['lh'][1]
        for j, name in enumerate(seq):
            dur = BAR - j * 0.5 if j == 0 else 1.2
            v = vel * (1.0 if j == 0 else 0.62 if j != 3 else 0.7)
            tr.add(piano(name, v * rng.uniform(0.92, 1.04), dur, rng), t + j * 0.5 + human(rng, 10), pan_for(name))
    else:
        # Sparse: bass on 1, an open dyad on 2.
        tr.add(piano(h['bass'], vel, BAR, rng), t + human(rng), pan_for(h['bass']))
        for name in lh[:2]:
            tr.add(piano(name, vel * 0.6, BAR - 1, rng), t + BEAT + human(rng, 18), pan_for(name))
        if turn:
            tr.add(piano(turn['lh'][0], vel * 0.55, 1.5, rng), t + 2 * BEAT + human(rng), pan_for(turn['lh'][0]))


def string_bar(tr, bar, t, dyn, rng=RNG, bars=1, bass=True, attack=1.0, release=1.6, upper_kind='viola'):
    h = HARMONY[bar]
    turn = h.get('turn')
    dur = bars * BAR
    if bass:
        string_note(tr, octave(h['bass'], 1), t, dur, dyn * 0.9, 'cello', -0.35, attack, release, rng=rng)
        if midi(h['bass']) >= midi('C2'):
            string_note(tr, h['bass'], t, dur, dyn * 0.7, 'bass', -0.15, attack, release, rng=rng)
        else:
            string_note(tr, octave(h['bass'], 1), t, dur, dyn * 0.5, 'bass', -0.15, attack, release, rng=rng)
    for k, name in enumerate(h['up']):
        if turn and name not in turn['up']:
            string_note(tr, name, t, dur - BAR / 3 - 0.2, dyn * 0.55, upper_kind, 0.1 + 0.25 * k, attack, 0.6, rng=rng)
            new = [x for x in turn['up'] if x not in h['up']][0]
            string_note(tr, new, t + dur - BAR / 3 - 0.3, BAR / 3 + 0.3, dyn * 0.55, upper_kind, 0.1 + 0.25 * k, 0.4, release, rng=rng)
        else:
            string_note(tr, name, t, dur, dyn * 0.55, upper_kind, 0.1 + 0.25 * k, attack, release, rng=rng)


class Mix:
    """Stems with their own reverb send, summed and mastered."""

    def __init__(self, seconds):
        self.seconds = seconds
        self.stems = {k: Track(seconds) for k in ('piano', 'box', 'strings', 'solo', 'air', 'perc')}
        self.wet = {'piano': 0.55, 'box': 0.7, 'strings': 0.5, 'solo': 0.42, 'air': 0.25, 'perc': 0.5}
        self.gain = {'piano': 1.0, 'box': 0.8, 'strings': 0.55, 'solo': 0.5, 'air': 0.4, 'perc': 0.2}

    def __getitem__(self, k):
        return self.stems[k]

    def render(self, period=None):
        total = None
        for k, tr in self.stems.items():
            st = tr.buf
            if period is not None:
                st = np.tile(st, 3)
            if k == 'box':
                st = tape(st, wow=0.0016, period=period)
            st = reverb(st, self.wet[k]) * self.gain[k]
            total = st if total is None else total + st
        total = tape(total, wow=0.0005, flutter=0.00003, period=period)
        return master(total)


# ---------------------------------------------------------------------------
# The cues
# ---------------------------------------------------------------------------
def cue_wake():
    """D-17 wakes. Synced loosely to the 20 s opening: he answers the relay at 7 s."""
    rng = np.random.default_rng(101)
    m = Mix(58)
    m['air'].add(wind(58, 0.05, rng) * env_curve(int(58 * SR), 5, 8), 0)
    # A low, dark string floor: D and A, barely there.
    string_note(m['strings'], 'D2', 1.5, 46, 0.35, 'cello', -0.3, 6, 8, shape=[0.5, 1, 1, 0.8], rng=rng)
    string_note(m['strings'], 'A2', 4.0, 40, 0.22, 'viola', 0.1, 6, 8, shape=[0.4, 1, 0.9, 0.7], rng=rng)
    # He answers: the music box remembers three notes, unevenly.
    for t, name, v in ((7.25, 'F5', 0.55), (8.05, 'E5', 0.42), (9.15, 'D5', 0.5)):
        m['box'].add(music_box(name, v, rng), t, 0.25)
    # He stands: the felt piano, low, and the first colour.
    m['piano'].add(piano('D2', 0.42, 6, rng), 12.5, -0.3)
    m['piano'].add(piano('A2', 0.3, 5, rng), 12.62, -0.2)
    m['piano'].add(piano('F4', 0.3, 3, rng), 13.8, 0.05)
    m['piano'].add(piano('Bb1', 0.38, 4, rng), 15.5, -0.35)
    m['piano'].add(piano('A4', 0.28, 2.5, rng), 16.4, 0.1)
    # The theme, bars 1-4 in full, then 5-8 left open.
    t0 = 18.0
    play_melody(m['piano'], melody_events(range(4), t0), 0.5, rng)
    for k in range(4):
        lh_arpeggio(m['piano'], k, t0 + k * BAR, 0.36, rng, 'sparse')
    t1 = t0 + 4 * BAR
    play_melody(m['piano'], melody_events([4], t1), 0.42, rng)
    play_melody(m['piano'], [(t1 + BAR, 'D5', 2)], 0.36, rng)
    play_melody(m['piano'], melody_events([6], t1 + 2 * BAR), 0.34, rng)
    play_melody(m['piano'], [(t1 + 3 * BAR, 'E5', 4)], 0.3, rng)
    for k in range(4, 8):
        lh_arpeggio(m['piano'], k, t1 + (k - 4) * BAR, 0.3 - 0.02 * (k - 4), rng, 'sparse')
    # High strings settle in behind bars 3 to 8.
    for k in range(2, 8):
        string_bar(m['strings'], k, t0 + k * BAR, 0.16 + 0.03 * min(k - 2, 3), rng, bass=False, attack=1.4, release=2.2)
    string_note(m['strings'], 'E4', t1 + 3 * BAR + 2.5, 8, 0.12, 'violin', 0.3, 2, 5, rng=rng)
    string_note(m['strings'], 'A3', t1 + 3 * BAR + 2.5, 8, 0.1, 'viola', 0.1, 2, 5, rng=rng)
    # The music box echoes the opening three notes, slower, an octave up.
    for t, name, v in ((45.0, 'F6', 0.32), (46.3, 'E6', 0.26), (48.0, 'D6', 0.24)):
        m['box'].add(music_box(name, v, rng), t, 0.3)
    return m.render()


def cue_bed():
    """A seamless 48 s loop: low strings and stray piano notes, with air."""
    rng = np.random.default_rng(202)
    L = BED_LEN
    m = Mix(L + 14)
    m['air'].add(wind(L, 0.06, rng, circular=True), 0)
    chords = [('D2', ['A2', 'F3']), ('Bb1', ['F2', 'D3']), ('A1', ['D3', 'F3']), ('G1', ['D3', 'E3'])]
    for k, (bass, up) in enumerate(chords):
        t = k * 12.0
        string_note(m['strings'], octave(bass, 1), t, 13, 0.24, 'cello', -0.3, 4, 5, rng=rng)
        for j, name in enumerate(up):
            string_note(m['strings'], name, t + 0.6 * j, 12.5, 0.15, 'viola', 0.15 + 0.2 * j, 4.5, 5, rng=rng)
    for t, name, v in ((4.0, 'A4', 0.24), (5.1, 'D5', 0.2), (15.5, 'F4', 0.22), (17.0, 'A4', 0.2), (19.2, 'D5', 0.18),
                       (28.0, 'E5', 0.2), (29.4, 'D5', 0.18), (38.5, 'Bb4', 0.2), (40.0, 'A4', 0.17), (44.2, 'E5', 0.15)):
        m['piano'].add(piano(name, v, 3.5, rng), t + human(rng), pan_for(name))
    m['box'].add(music_box('A5', 0.16, rng), 33.0, 0.4)
    # Wrap everything after the period back onto the start.
    for tr in m.stems.values():
        n = int(L * SR)
        extra = tr.buf[:, n:]
        tr.buf = tr.buf[:, :n].copy()
        tr.buf[:, :extra.shape[1]] += extra
    st = m.render(period=L)
    n = int(L * SR)
    pad = int(LOOP_PAD * SR)
    # The middle period, with a pad of continuous audio on each side.
    return st[:, n - pad: 2 * n + pad]


def cue_hall():
    """The sorting hall. The cello sings the theme; the E-flat bar is the widest moment."""
    rng = np.random.default_rng(303)
    m = Mix(60)
    m['air'].add(wind(60, 0.05, rng) * env_curve(int(60 * SR), 4, 10), 0)
    string_note(m['strings'], 'D2', 0.0, 6.0, 0.3, 'bass', -0.2, 3.5, 2, rng=rng)
    string_note(m['strings'], 'D3', 0.5, 5.5, 0.22, 'cello', -0.3, 3.5, 2, rng=rng)
    t0 = 4.5
    # Bars 1-8 with the cello down an octave; strings and the broken piano underneath.
    line, off = legato_line(melody_events(range(8), 0, transpose=-1), 0, 'cello', 0.5, rng)
    m['solo'].add(line, t0 + off, -0.05)
    for k in range(8):
        string_bar(m['strings'], k, t0 + k * BAR, 0.22 + 0.025 * k, rng, bass=k > 0)
        lh_arpeggio(m['piano'], k, t0 + k * BAR, 0.23 + 0.015 * k, rng, 'flow')
    # Violins join the cello, two octaves up, for bars 5-8.
    vl, voff = legato_line(melody_events(range(4, 8), 0, transpose=1), 0, 'violin', 0.16, rng, vib_cents=14)
    m['strings'].add(vl, t0 + 4 * BAR + voff, 0.35)
    # Coda: bars 13-16, the E-flat bar and the open A.
    t2 = t0 + 8 * BAR
    line2, off2 = legato_line(melody_events(range(12, 16), 0, transpose=-1), 0, 'cello', 0.55, rng, tail=3.5)
    m['solo'].add(line2, t2 + off2, -0.05)
    for k in range(12, 16):
        dyn = [0.48, 0.4, 0.32, 0.26][k - 12]
        string_bar(m['strings'], k, t2 + (k - 12) * BAR, dyn, rng, release=3.0 if k == 15 else 1.6)
        lh_arpeggio(m['piano'], k, t2 + (k - 12) * BAR, [0.32, 0.28, 0.24, 0.22][k - 12], rng, 'flow' if k < 15 else 'sparse')
    vl2, voff2 = legato_line(melody_events([12], 0, transpose=1), 0, 'violin', 0.2, rng, vib_cents=14)
    m['strings'].add(vl2, t2 + voff2, 0.35)
    # It stays open on A, and the light hangs there.
    t3 = t2 + 4 * BAR
    string_note(m['strings'], 'A3', t3, 9, 0.16, 'viola', 0.1, 1.5, 6, rng=rng)
    string_note(m['strings'], 'E4', t3, 9, 0.12, 'violin', 0.3, 1.5, 6, rng=rng)
    string_note(m['strings'], 'A2', t3, 9, 0.18, 'cello', -0.3, 1.5, 6, rng=rng)
    m['piano'].add(piano('E6', 0.2, 3, rng), t3 + 2.0, 0.45)
    m['piano'].add(piano('A5', 0.16, 4, rng), t3 + 3.4, 0.4)
    return m.render()


def cue_end():
    """The bulkhead opens and D-17 walks on. The whole theme, then D major and a birthday tune."""
    rng = np.random.default_rng(404)
    m = Mix(100)
    m['air'].add(wind(100, 0.035, rng) * env_curve(int(100 * SR), 3, 14), 0)
    # Light through the door: a high, thin shimmer and a low D.
    string_note(m['strings'], 'A5', 0.0, 5.0, 0.07, 'violin', 0.4, 2.5, 2.5, rng=rng)
    string_note(m['strings'], 'D6', 0.4, 4.6, 0.05, 'violin', 0.5, 2.5, 2.5, rng=rng)
    m['piano'].add(piano('D2', 0.4, 4, rng), 0.6, -0.3)
    t0 = 3.0
    # Phrase A on the piano alone at first, strings from bar 3, the music box in bars 5-6.
    play_melody(m['piano'], melody_events(range(8), t0), 0.52, rng)
    for k in range(8):
        lh_arpeggio(m['piano'], k, t0 + k * BAR, 0.32 + 0.01 * k, rng, 'flow')
    for k in range(2, 8):
        string_bar(m['strings'], k, t0 + k * BAR, 0.18 + 0.025 * (k - 2), rng, bass=k >= 4)
    for t, name, beats in melody_events([4, 5], t0 + 4 * BAR, transpose=1):
        m['box'].add(music_box(name, 0.3, rng), t + 0.02, 0.35)
    # Phrase B: the violins take the theme; the piano flows under it.
    t1 = t0 + 8 * BAR
    vl, voff = legato_line(melody_events(range(8, 16), 0), 0, 'violin', 0.36, rng, vib_cents=16, tail=2.0)
    m['solo'].add(vl, t1 + voff, 0.2)
    cl, coff = legato_line(melody_events(range(8, 16), 0, transpose=-2), 0, 'cello', 0.22, rng, vib_cents=14, tail=2.0)
    m['solo'].add(cl, t1 + coff, -0.3)
    dyn = [0.32, 0.34, 0.36, 0.34, 0.46, 0.38, 0.32, 0.26]
    for k in range(8, 16):
        string_bar(m['strings'], k, t1 + (k - 8) * BAR, dyn[k - 8], rng)
        lh_arpeggio(m['piano'], k, t1 + (k - 8) * BAR, 0.3 + dyn[k - 8] * 0.2, rng, 'flow')
    # Bars 17-20: the motif once more, slowing.
    t2 = t1 + 8 * BAR
    slow = [0, 3.0, 6.2, 9.6]
    play_melody(m['piano'], [(t2, 'D5', 3)], 0.42, rng)
    play_melody(m['piano'], [(t2 + slow[1], 'F5', 1.6), (t2 + slow[1] + 1.6, 'E5', 0.6), (t2 + slow[1] + 2.25, 'D5', 1)], 0.4, rng)
    play_melody(m['piano'], [(t2 + slow[2], 'E5', 3.2)], 0.34, rng)
    play_melody(m['piano'], [(t2 + slow[3], 'E5', 2.2), (t2 + slow[3] + 2.3, 'C#5', 1.6)], 0.32, rng)
    for k, (bar, s) in enumerate(zip((0, 1, 6, 7), slow)):
        lh_arpeggio(m['piano'], bar, t2 + s, 0.3 - 0.02 * k, rng, 'sparse')
        string_bar(m['strings'], bar, t2 + s, 0.26 - 0.03 * k, rng, release=2.0)
    # D major. A rolled chord, a warm string pad, and the music box winding down.
    t3 = t2 + 13.6
    for j, name in enumerate(('D2', 'A2', 'F#3', 'D4', 'A4')):
        m['piano'].add(piano(name, 0.36 - 0.03 * j, 8, rng), t3 + 0.07 * j, pan_for(name))
    for name, kind, pan, d in (('D3', 'cello', -0.3, 0.26), ('A3', 'viola', 0.0, 0.18), ('F#4', 'violin', 0.25, 0.14), ('D2', 'bass', -0.15, 0.2)):
        string_note(m['strings'], name, t3, 17, d, kind, pan, 2.5, 9, shape=[1, 1, 0.8, 0.5], rng=rng)
    # Happy birthday, an octave up, slowing as the spring runs out, and stopping short.
    tune = [('A5', 0.75), ('A5', 0.25), ('B5', 1), ('A5', 1), ('D6', 1), ('C#6', 2), ('A5', 0.75), ('A5', 0.25), ('B5', 1)]
    t, beat = t3 + 3.0, 1.15
    for k, (name, beats) in enumerate(tune):
        m['box'].add(music_box(name, 0.34 - 0.012 * k, rng), t, 0.35)
        t += beats * beat
        beat *= 1.06
    m['piano'].add(piano('D6', 0.14, 5, rng), t + 3.2, 0.45)
    return m.render()


def scaled_events(bars, t0, bar_len, transpose=0):
    """Theme bars at another tempo: (time, note, seconds)."""
    out = []
    for k, b in enumerate(bars):
        t = t0 + k * bar_len
        for n, beats in THEME[b]:
            d = beats * bar_len / 3
            out.append((t, octave(n, transpose) if transpose else n, d))
            t += d
    return out


def cue_threshold():
    """The bulkhead opens and D-17 goes through: light, the theme's first breath, and a new room."""
    rng = np.random.default_rng(505)
    m = Mix(44)
    m['air'].add(wind(44, 0.04, rng) * env_curve(int(44 * SR), 2, 10), 0)
    string_note(m['strings'], 'A5', 0.0, 6.0, 0.07, 'violin', 0.4, 2.5, 3, rng=rng)
    string_note(m['strings'], 'D6', 0.5, 5.5, 0.05, 'violin', 0.5, 2.5, 3, rng=rng)
    m['piano'].add(piano('D2', 0.4, 5, rng), 0.6, -0.3)
    t0 = 3.5
    play_melody(m['piano'], melody_events(range(4), t0), 0.46, rng)
    for k in range(4):
        lh_arpeggio(m['piano'], k, t0 + k * BAR, 0.3 - 0.02 * k, rng, 'flow' if k < 3 else 'sparse')
        string_bar(m['strings'], k, t0 + k * BAR, 0.2 - 0.02 * k, rng, bass=k > 0, release=2.4 if k == 3 else 1.6)
    # He steps out into the weighing room: the music box answers with the first two notes, and it stops there.
    m['box'].add(music_box('F6', 0.26, rng), t0 + 4 * BAR + 0.6, 0.35)
    m['box'].add(music_box('E6', 0.22, rng), t0 + 4 * BAR + 1.5, 0.35)
    string_note(m['strings'], 'D3', t0 + 4 * BAR, 10, 0.16, 'cello', -0.3, 2.0, 7, rng=rng)
    string_note(m['strings'], 'A3', t0 + 4 * BAR, 10, 0.1, 'viola', 0.1, 2.0, 7, rng=rng)
    return m.render()


def cue_racks():
    """D-17 walks through the gate and the camera pans across the racks: rows of couriers like him, switched
    off in their slots. A lament, not a reveal. Cold and empty first (wind, a low D pedal, a far bell, an
    unresolved D and E-flat on the piano) while the camera pans (0-9 s). Then a solo cello sings phrase A low
    and at half speed over the pedal, darkened to the Phrygian (F, E-flat, D) and with a chord every two bars
    (9-33 s). It swells once, on the theme's E-flat bar over the D pedal (33-39 s), and falls back through
    B-flat to an open A with the piano's E-flat against it: near silence, unresolved (39-57 s).
    No music box: the parcel says nothing here. 'kin' takes over at his realisation."""
    rng = np.random.default_rng(616)
    L = 60
    m = Mix(L)
    m.stems['bell'] = Track(L)
    m.wet['bell'], m.gain['bell'] = 0.85, 0.25
    m['air'].add(wind(L, 0.055, rng) * env_curve(int(L * SR), 6, 12), 0)

    # The floor: a low D pedal under everything, never broken, rising a little into the swell.
    string_note(m['strings'], 'D2', 0.3, 50, 0.28, 'bass', -0.15, 7.0, 8, shape=[0.45, 0.65, 0.75, 0.85, 1, 0.8, 0.6, 0.5], rng=rng)
    string_note(m['strings'], 'D1', 8.0, 42, 0.12, 'bass', -0.1, 6.0, 8, shape=[0.6, 0.9, 1, 0.7], rng=rng)
    # Cold and empty: a far bell, an open fifth in the low cellos, and two piano notes a ninth apart.
    m['bell'].add(far_bell('D3', 0.5, rng), 1.2, -0.25)
    string_note(m['strings'], 'A2', 3.5, 11.5, 0.13, 'cello', -0.3, 5.0, 3.0, rng=rng)
    m['piano'].add(piano('D2', 0.24, 6, rng), 4.6, -0.3)
    m['piano'].add(piano('Eb3', 0.17, 5, rng), 5.5, -0.1)

    # The lament, phrase A at half speed and an octave below the hall's cello: (time, note, beats) from 9 s.
    t0 = 9.0
    lament = [(0, 'F3', 3), (3, 'Eb3', 1), (4, 'D3', 2),       # the falling figure, its E flattened
              (6, 'D3', 4), (10, 'A2', 2),                     # over B-flat
              (12, 'C3', 3), (15, 'Bb2', 1), (16, 'A2', 2),    # over G minor
              (18, 'G2', 6)]                                   # held low, the strings gathering
    line, off = legato_line(lament, 0, 'cello', 0.38, rng, vib_cents=15, tail=1.2,
                            shape=[(-0.3, 0.55), (6, 0.7), (12, 0.74), (18, 0.78), (24, 1.0)])
    m['solo'].add(line, t0 + off, -0.05)
    m['bell'].add(far_bell('D3', 0.32, rng), 13.6, -0.3)
    # The section under it, a chord every two bars: B-flat over D, then G minor over D, gathering.
    for start, names, d in ((15.0, (('Bb2', 'cello', -0.3), ('D3', 'viola', -0.05), ('F3', 'viola', 0.15)), 0.15),
                            (21.0, (('G2', 'cello', -0.3), ('Bb2', 'viola', -0.05), ('D3', 'viola', 0.15)), 0.16)):
        for j, (name, kind, pan) in enumerate(names):
            string_note(m['strings'], name, start, 6.0, d * (1 if j == 0 else 0.7), kind, pan, 2.5, 2.5, rng=rng)
    for name, kind, pan, d in (('G2', 'cello', -0.3, 0.18), ('Bb2', 'viola', -0.05, 0.13), ('D3', 'viola', 0.15, 0.12)):
        string_note(m['strings'], name, 27.0, 6.0, d, kind, pan, 1.5, 2.0, shape=[0.6, 0.8, 1.0], rng=rng)
    m['piano'].add(piano('G1', 0.2, 5, rng), 21.0 + human(rng), -0.35)

    # The one swell: the theme's E-flat bar (G, F, E-flat) over the D pedal, the cello up an octave and
    # the low violins under it; then D and B-flat, falling away, and an open A that does not resolve.
    t1 = 33.0
    lament2 = [(0, 'G3', 3), (3, 'F3', 1), (4, 'Eb3', 2),
               (6, 'D3', 4), (10, 'Bb2', 2),
               (12, 'A2', 9)]
    line2, off2 = legato_line(lament2, 0, 'cello', 0.58, rng, vib_cents=18, tail=3.5,
                              shape=[(-0.3, 0.55), (1.6, 1.0), (4.0, 0.95), (6.0, 0.72), (10, 0.55), (12, 0.45), (16, 0.3), (21, 0.16)])
    m['solo'].add(line2, t1 + off2, -0.05)
    vl_notes = [(t, octave(n, 1), b) for t, n, b in lament2[:4]]
    vl, voff = legato_line(vl_notes, 0, 'violin', 0.15, rng, vib_cents=13, tail=2.0,
                           shape=[(-0.3, 0.5), (1.6, 1.0), (6, 0.6), (10, 0.3)])
    m['strings'].add(vl, t1 + voff, 0.3)
    for name, kind, pan, d in (('Eb3', 'cello', -0.25, 0.3), ('G3', 'viola', 0.0, 0.24), ('Bb3', 'viola', 0.15, 0.2), ('D4', 'violin', 0.3, 0.12)):
        string_note(m['strings'], name, t1, 6.0, d, kind, pan, 1.4, 2.2, shape=[0.7, 1, 0.85, 0.6], rng=rng)
    m['piano'].add(piano('Eb2', 0.3, 5, rng), t1 + 0.05, -0.3)
    m['piano'].add(piano('Bb2', 0.22, 4.5, rng), t1 + 0.12, -0.2)
    for name, kind, pan, d in (('Bb2', 'cello', -0.3, 0.18), ('D3', 'viola', -0.05, 0.12), ('F3', 'viola', 0.15, 0.1)):
        string_note(m['strings'], name, t1 + 6.0, 6.0, d, kind, pan, 1.2, 3.0, shape=[1, 0.8, 0.6], rng=rng)
    # Near silence: the empty fifth again, the piano's E-flat against the cello's A, the bell once more.
    string_note(m['strings'], 'A2', t1 + 12.0, 9.0, 0.1, 'cello', -0.3, 2.5, 5.0, shape=[1, 0.8, 0.5], rng=rng)
    m['piano'].add(piano('D2', 0.2, 6, rng), t1 + 14.8, -0.3)
    m['piano'].add(piano('Eb3', 0.14, 5, rng), t1 + 15.7, -0.1)
    m['bell'].add(far_bell('D3', 0.26, rng), t1 + 18.5, -0.25)
    return m.render()


def cue_kin():
    """D-17 walks in among the couriers and understands what they are: like him, and gone. The
    realisation is slow (the game slows his walk and the camera); the music swells to the one full
    climax so far, phrase A broadened to a bar every 3.5 s, then lets go."""
    rng = np.random.default_rng(707)
    m = Mix(70)
    m['air'].add(wind(70, 0.04, rng) * env_curve(int(70 * SR), 3, 14), 0)
    # He stops and looks along the rows: a low pedal (the one 'racks' was holding) and single piano notes,
    # one for each look, low and dark like the racks cue; the last is its E-flat, which the theme's bar 1
    # lifts to E. (The looks have their own random stream, so the rest of the cue is as before.)
    string_note(m['strings'], 'D2', 0.0, 44, 0.24, 'bass', -0.15, 4.0, 10, shape=[0.5, 0.8, 1, 1, 0.6, 0.3], rng=rng)
    string_note(m['strings'], 'D3', 1.0, 6.5, 0.16, 'cello', -0.3, 3.0, 2.5, rng=rng)
    looks = np.random.default_rng(7071)
    for t, name, dur in ((1.2, 'A4', 3.5), (2.6, 'F4', 3.5), (4.1, 'D4', 3.0), (5.6, 'Eb4', 1.3)):
        m['piano'].add(piano(name, 0.28, dur, looks), t + human(rng), pan_for(name))
    # The theme broadens and builds: cello first, then the violins, then everything.
    t0, bl = 7.0, 3.5
    dyn = [0.18, 0.22, 0.27, 0.33, 0.42, 0.52, 0.62, 0.72]
    for k in range(8):
        string_bar(m['strings'], k, t0 + k * bl, dyn[k], rng, bars=bl / BAR, attack=1.0 + 0.2 * (k < 2),
                   release=3.5 if k == 7 else 1.8)
        if k < 6:
            lh_arpeggio(m['piano'], k, t0 + k * bl, 0.24 + 0.035 * k, rng, 'flow')
    line, off = legato_line(scaled_events(range(0, 4), 0, bl, transpose=-1), 0, 'cello', 0.5, rng, tail=1.0)
    m['solo'].add(line, t0 + off, -0.1)
    vl, voff = legato_line(scaled_events(range(4, 8), 0, bl), 0, 'violin', 0.6, rng, vib_cents=16, tail=3.0)
    m['solo'].add(vl, t0 + 4 * bl + voff, 0.15)
    v8, v8off = legato_line(scaled_events(range(5, 8), 0, bl, transpose=1), 0, 'violin', 0.26, rng, vib_cents=14, tail=3.0)
    m['strings'].add(v8, t0 + 5 * bl + v8off, 0.35)
    vc, vcoff = legato_line(scaled_events(range(4, 8), 0, bl, transpose=-2), 0, 'cello', 0.34, rng, vib_cents=12, tail=3.0)
    m['solo'].add(vc, t0 + 4 * bl + vcoff, -0.35)
    # The peak, bar 8: big chords on the piano, the timpani roll, the cymbal.
    peak = t0 + 7 * bl
    for k, bar in ((6, 6), (7, 7)):
        h = HARMONY[bar]
        for j, name in enumerate([h['bass'], octave(h['bass'], 1)] + h['lh']):
            m['piano'].add(piano(name, 0.5 + 0.08 * (k == 7), bl + 1.5, rng), t0 + k * bl + 0.02 * j, pan_for(name))
    timp_roll(m['perc'], 'A1', peak - 6.0, peak, 0.05, 0.75, rng, hit=0.9)
    m['perc'].add(cymbal_swell(14, 5.2, 0.022, rng), peak - 5.2, 0.2)
    # Then it lets go: D minor, B-flat, the dominant, quieter each time; the parcel's three notes.
    t1 = t0 + 8 * bl
    for k, (bar, d) in enumerate(((0, 0.42), (1, 0.26), (6, 0.18), (7, 0.13))):
        string_bar(m['strings'], bar, t1 + k * 3.6, d, rng, bars=3.6 / BAR, attack=0.8, release=3.0 if k == 3 else 1.8)
    m['piano'].add(piano('D2', 0.42, 6, rng), t1, -0.3)
    for t, name, v in ((t1 + 7.5, 'F5', 0.3), (t1 + 8.6, 'E5', 0.26), (t1 + 10.0, 'D5', 0.28)):
        m['box'].add(music_box(name, v, rng), t, 0.35)
    return m.render()


def cue_dead():
    """DL-03. The scanner rejects room 114 (0 s); the pit of undeliverable parcels opens below him and
    the music swells as he walks to the rail (peak about 10-11.5 s); it falls away while he peers over
    and checks his label in near silence (12.5-18 s); then the theme comes back with purpose and, for
    the first time, turns to a major key (18.4 s on). The game's scan timing matches."""
    rng = np.random.default_rng(808)
    m = Mix(78)
    m['air'].add(wind(78, 0.045, rng) * env_curve(int(78 * SR), 1, 14), 0)
    # Rejection: a low, close dissonance.
    for name, v in (('D2', 0.5), ('Eb2', 0.42), ('A2', 0.3)):
        m['piano'].add(piano(name, v, 3.5, rng), 0.05, pan_for(name))
    for name, kind in (('D2', 'cello'), ('Eb2', 'bass')):
        n = int(4.5 * SR)
        trem = 0.75 + 0.25 * np.sin(2 * np.pi * 7 * np.arange(n) / SR)
        e = env_curve(n, 0.6, 2.0, [0.6, 1, 0.8]) * trem.astype(np.float32) * 0.22
        m['strings'].add(bowed(np.full(n, hz(name), np.float32), e, kind, rng), 0.0, -0.2)
    # The pit: phrase B's last four bars, swelling.
    t0, bl = 2.0, 2.6
    for k, bar in enumerate(range(12, 16)):
        string_bar(m['strings'], bar, t0 + k * bl, [0.32, 0.46, 0.6, 0.66][k], rng, bars=bl / BAR, attack=0.8,
                   release=2.2 if k == 3 else 1.4)
    vl, voff = legato_line(scaled_events(range(12, 16), 0, bl), 0, 'violin', 0.55, rng, vib_cents=16, tail=1.2)
    m['solo'].add(vl, t0 + voff, 0.15)
    v2, v2off = legato_line(scaled_events(range(12, 16), 0, bl, transpose=1), 0, 'violin', 0.24, rng, vib_cents=14, tail=1.2)
    m['strings'].add(v2, t0 + v2off, 0.35)
    for k, bar in enumerate(range(12, 16)):
        h = HARMONY[bar]
        for j, name in enumerate([h['bass'], octave(h['bass'], 1)] + h['lh'][:2]):
            m['piano'].add(piano(name, 0.36 + 0.05 * k, bl + 1.2, rng), t0 + k * bl + 0.02 * j, pan_for(name))
    timp_roll(m['perc'], 'A1', 6.6, 9.8, 0.05, 0.6, rng, hit=0.7)
    m['perc'].add(cymbal_swell(10, 3.2, 0.018, rng, decay=1.6), 6.6, 0.2)
    # He checks his label: one high note held, the music box finding the first bars.
    string_note(m['strings'], 'A5', 12.6, 6.2, 0.06, 'violin', 0.4, 1.2, 2.5, rng=rng)
    for t, name, v in ((14.6, 'F5', 0.3), (15.2, 'E5', 0.26), (15.9, 'D5', 0.3), (16.9, 'D5', 0.24), (17.9, 'A4', 0.24)):
        m['box'].add(music_box(name, v, rng), t, 0.3)
    # Renewed purpose: phrase A at a walking tempo, turning at the end to F major.
    t1, bl = 18.4, 2.7
    bars = [0, 1, 2, 3, 4, 5, 16, 17]
    for k, bar in enumerate(bars):
        for t, name, beats in scaled_events([bar], t1 + k * bl, bl):
            m['piano'].add(piano(name, 0.5, beats * 1.05, rng), t + human(rng), pan_for(name))
        lh_arpeggio(m['piano'], bar, t1 + k * bl, 0.3, rng, 'flow' if k < 7 else 'sparse')
        if k >= 2:
            string_bar(m['strings'], bar, t1 + k * bl, 0.16 + 0.02 * k, rng, bars=bl / BAR, attack=0.9,
                       release=5.0 if k == 7 else 1.5)
    t2 = t1 + 7 * bl
    m['box'].add(music_box('F6', 0.26, rng), t2 + 0.3, 0.35)
    m['box'].add(music_box('C6', 0.2, rng), t2 + 1.2, 0.35)
    for name, kind, pan, d in (('F2', 'bass', -0.15, 0.18), ('F3', 'cello', -0.3, 0.2), ('A3', 'viola', 0.0, 0.14), ('C5', 'violin', 0.3, 0.08)):
        string_note(m['strings'], name, t2, 12, d, kind, pan, 1.5, 8, shape=[1, 0.9, 0.6], rng=rng)
    return m.render()


def cue_latch():
    """DL-04. The safety pawl drops home: a warm F major under the parcel's three notes, and it settles."""
    rng = np.random.default_rng(909)
    m = Mix(11)
    for j, name in enumerate(('F2', 'C3', 'A3', 'F4', 'C5')):
        m['piano'].add(piano(name, 0.34 - 0.03 * j, 6, rng), 0.12 + 0.06 * j, pan_for(name))
    for name, kind, pan, d in (('F2', 'bass', -0.15, 0.16), ('F3', 'cello', -0.3, 0.18), ('C4', 'viola', 0.0, 0.12), ('A4', 'violin', 0.3, 0.08)):
        string_note(m['strings'], name, 0.2, 8.5, d, kind, pan, 1.2, 3.5, shape=[0.7, 1, 0.8], rng=rng)
    for t, name, v in ((1.2, 'F5', 0.36), (1.9, 'E5', 0.3), (2.8, 'D5', 0.34), (4.1, 'C5', 0.26)):
        m['box'].add(music_box(name, v, rng), t, 0.3)
    m['piano'].add(piano('A5', 0.16, 4, rng), 5.4, 0.4)
    return m.render()


def cue_refuge():
    """DL-04. D-17 steps out of the tunnel onto a balcony high in the refuge's atrium. Awe, not grief:
    near silence (a high string light over a low pedal), then phrase B broadens toward F major with the
    violins in octaves and a timpani roll on the dominant; the peak on F major (about 11.4 s) is timed to
    the camera reaching its widest. Then it lets go: B-flat, D minor, the music box, an open fifth."""
    rng = np.random.default_rng(1010)
    m = Mix(40)
    m['air'].add(wind(40, 0.05, rng) * env_curve(int(40 * SR), 2, 12), 0)
    string_note(m['strings'], 'A5', 0.0, 4.0, 0.05, 'violin', 0.45, 2.0, 1.5, rng=rng)
    string_note(m['strings'], 'E6', 0.4, 3.6, 0.035, 'violin', 0.55, 2.0, 1.5, rng=rng)
    string_note(m['strings'], 'F1', 0.0, 18.0, 0.2, 'bass', -0.15, 3.0, 4, shape=[0.4, 0.8, 1, 1], rng=rng)
    m['piano'].add(piano('F2', 0.3, 5, rng), 0.3, -0.3)
    m['piano'].add(piano('C6', 0.14, 3, rng), 1.6, 0.45)
    # Phrase B, broadening: bars 9-11, then the cadence into F major (bars 17-18).
    t0, bl = 2.6, 2.2
    bars = [8, 9, 10, 16]
    dyn = [0.2, 0.28, 0.38, 0.5]
    for k, bar in enumerate(bars):
        string_bar(m['strings'], bar, t0 + k * bl, dyn[k], rng, bars=bl / BAR, attack=0.8 + 0.3 * (k == 0), release=1.6)
        lh_arpeggio(m['piano'], bar, t0 + k * bl, 0.24 + 0.04 * k, rng, 'flow')
    cl, coff = legato_line(scaled_events(bars, 0, bl, transpose=-1), 0, 'cello', 0.45, rng, tail=0.6)
    m['solo'].add(cl, t0 + coff, -0.15)
    vl, voff = legato_line(scaled_events(bars[1:], 0, bl), 0, 'violin', 0.5, rng, vib_cents=16, tail=0.6)
    m['solo'].add(vl, t0 + bl + voff, 0.15)
    v8, v8off = legato_line(scaled_events(bars[2:], 0, bl, transpose=1), 0, 'violin', 0.24, rng, vib_cents=14, tail=0.6)
    m['strings'].add(v8, t0 + 2 * bl + v8off, 0.35)
    # The peak: F major, held, everything in; the timpani on C rolls into it, the cymbal swells to it.
    peak = t0 + 4 * bl
    for name, kind, pan, d in (('F1', 'bass', -0.15, 0.5), ('F2', 'cello', -0.3, 0.55), ('C3', 'cello', -0.2, 0.4), ('A3', 'viola', 0.0, 0.42),
                               ('C4', 'viola', 0.1, 0.36), ('F4', 'violin', 0.25, 0.34), ('A4', 'violin', 0.35, 0.3)):
        string_note(m['strings'], name, peak, 6.0, d, kind, pan, 0.5, 3.0, shape=[1, 0.9, 0.75, 0.55], rng=rng)
    for line_note, kind, gain, pan in (('F5', 'violin', 0.55, 0.15), ('F6', 'violin', 0.25, 0.35), ('F4', 'cello', 0.36, -0.35)):
        string_note(m['solo'], line_note, peak, 5.0, gain, kind, pan, 0.3, 2.6, shape=[1, 0.95, 0.8], rng=rng)
    for j, name in enumerate(('F1', 'F2', 'C3', 'A3', 'F4', 'C5', 'A5')):
        m['piano'].add(piano(name, 0.52 - 0.03 * j, 6, rng), peak + 0.03 * j, pan_for(name))
    timp_roll(m['perc'], 'C2', peak - 3.6, peak, 0.05, 0.7, rng, hit=0.85)
    m['perc'].add(cymbal_swell(10, 3.6, 0.02, rng, decay=1.8), peak - 3.6, 0.2)
    # It lets go: B-flat, then D minor, quieter; the parcel's three notes; an open fifth that stays.
    t1 = peak + 6.2
    string_bar(m['strings'], 1, t1, 0.26, rng, bars=3.6 / BAR, attack=1.2, release=2.0)
    string_bar(m['strings'], 0, t1 + 3.6, 0.17, rng, bars=3.6 / BAR, attack=1.2, release=2.5)
    m['piano'].add(piano('Bb1', 0.34, 5, rng), t1, -0.3)
    m['piano'].add(piano('D2', 0.3, 6, rng), t1 + 3.6, -0.3)
    for t, name, v in ((t1 + 4.6, 'F6', 0.3), (t1 + 5.5, 'E6', 0.26), (t1 + 6.7, 'D6', 0.28)):
        m['box'].add(music_box(name, v, rng), t, 0.35)
    for name, kind, pan, d in (('D3', 'cello', -0.3, 0.14), ('A3', 'viola', 0.1, 0.1), ('A4', 'violin', 0.35, 0.05)):
        string_note(m['strings'], name, t1 + 7.0, 12, d, kind, pan, 2.0, 7, shape=[1, 0.9, 0.6], rng=rng)
    return m.render()


def cue_child():
    """DL-05. The desk scrapes clear and the growth marks are there. The music box finds the parcel's three
    notes, slowly, and they become a lullaby (phrase A at a rocking pace) over soft piano and strings that
    swell a little as he takes in the marks and the tree. It thins to a single high note, held, as the
    terminal answers."""
    rng = np.random.default_rng(1111)
    m = Mix(50)
    m['air'].add(wind(50, 0.03, rng) * env_curve(int(50 * SR), 3, 12), 0)
    string_note(m['strings'], 'A5', 0.0, 5.0, 0.05, 'violin', 0.4, 2.0, 2.0, rng=rng)
    m['piano'].add(piano('D2', 0.3, 5, rng), 0.2, -0.3)
    for t, name, v in ((1.2, 'F5', 0.34), (2.5, 'E5', 0.3), (4.0, 'D5', 0.34)):
        m['box'].add(music_box(name, v, rng), t, 0.3)
    # The lullaby: the music box on phrase A, the piano rocking under it.
    t0, bl = 6.0, 3.4
    for t, name, d in scaled_events(range(4), t0, bl, transpose=1):
        m['box'].add(music_box(name, 0.3, rng), t + human(rng, 8), 0.3)
    for k in range(8):
        lh_arpeggio(m['piano'], k, t0 + k * bl, 0.2 + 0.02 * min(k, 4), rng, 'sparse')
    dyn = [0.1, 0.13, 0.17, 0.22, 0.3, 0.34, 0.28, 0.2]
    for k in range(8):
        string_bar(m['strings'], k, t0 + k * bl, dyn[k], rng, bars=bl / BAR, bass=k >= 2, attack=1.6, release=2.2)
    # Bars 5-8: the piano takes the tune, the music box answers each phrase an octave up.
    for t, name, d in scaled_events(range(4, 8), t0 + 4 * bl, bl):
        m['piano'].add(piano(name, 0.36, d * 1.1, rng), t + human(rng), pan_for(name))
    for k, (name, v) in enumerate((('A5', 0.22), ('D6', 0.2), ('E6', 0.18), ('C#6', 0.18))):
        m['box'].add(music_box(name, v, rng), t0 + (4 + k) * bl + 2.2, 0.35)
    vl, voff = legato_line(scaled_events(range(4, 7), 0, bl, transpose=1), 0, 'violin', 0.16, rng, vib_cents=14, tail=1.5)
    m['strings'].add(vl, t0 + 4 * bl + voff, 0.35)
    # The terminal answers: one high note, held, and a low D under it.
    t1 = t0 + 8 * bl
    string_note(m['strings'], 'A5', t1, 12, 0.07, 'violin', 0.4, 1.5, 6, shape=[1, 1, 0.8, 0.5], rng=rng)
    string_note(m['strings'], 'D3', t1, 12, 0.1, 'cello', -0.3, 2.0, 6, rng=rng)
    m['box'].add(music_box('D6', 0.22, rng), t1 + 3.0, 0.35)
    return m.render()


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------
def write_wav(path, st):
    data = (np.clip(st.T, -1, 1) * 32767).astype('<i2')
    with wave.open(path, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(data.tobytes())


def fade_tail(st, seconds=2.0):
    n = int(seconds * SR)
    st[:, -n:] *= np.linspace(1, 0, n) ** 2
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='../../game/undelivered/assets/music')
    ap.add_argument('--wav', default=None, help='also keep the WAV masters here')
    ap.add_argument('--only', nargs='*')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    cues = {'wake': cue_wake, 'bed': cue_bed, 'hall': cue_hall, 'threshold': cue_threshold, 'racks': cue_racks,
            'kin': cue_kin, 'dead': cue_dead, 'latch': cue_latch, 'refuge': cue_refuge, 'child': cue_child, 'end': cue_end}
    files = {'latch': 'dl04_latch', 'refuge': 'dl04_refuge', 'child': 'dl05_child'}
    reference = ('wake', 'hall', 'end')
    rendered = {}
    for name, fn in cues.items():
        # The reference cues are always rendered, so a cue rendered alone still gets the shared gain.
        if args.only and name not in args.only and name not in reference:
            continue
        print('rendering', name, flush=True)
        st = fn()
        if name != 'bed':
            st = fade_tail(st)
        rendered[name] = st
    # One gain for every cue, so their balance is as written. The reference is the gentler cues, so a
    # swell can rise above them; a soft limiter catches its peaks.
    peak = max(float(np.abs(rendered[k]).max()) for k in reference)
    gain = 10 ** (-1.0 / 20) / peak
    for name, st in rendered.items():
        if args.only and name not in args.only:
            continue
        # Tape hiss, added at its final level, about 64 dB down.
        st = st * gain
        st = np.where(np.abs(st) > 0.7, np.sign(st) * (0.7 + 0.25 * np.tanh((np.abs(st) - 0.7) / 0.25)), st)
        st = st + hiss(st.shape[1], 0.0011, np.random.default_rng(5))
        rms = 20 * np.log10(np.sqrt((st ** 2).mean()) + 1e-9)
        print(f'{name}: {st.shape[1] / SR:.1f} s, peak {20 * np.log10(np.abs(st).max()):.1f} dBFS, rms {rms:.1f} dBFS')
        stem = files.get(name, f'dl01_{name}')
        wav = os.path.join(args.wav or args.out, f'{stem}.wav')
        if args.wav:
            os.makedirs(args.wav, exist_ok=True)
        write_wav(wav, st)
        mp3 = os.path.join(args.out, f'{stem}.mp3')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-c:a', 'libmp3lame', '-q:a', '3', mp3], check=True)
        if not args.wav:
            os.remove(wav)


if __name__ == '__main__':
    main()
