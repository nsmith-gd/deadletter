"""DL-01 The Wake: the score.

Renders four cues for the playable scene from a written score with small
synthesized instruments: a felt piano, an old music box, a string section, a
solo cello, and wind and room tone. All are mixed through a convolution hall
and a little tape.

    python compose_dl01.py --out ../../game/dl01/assets/music

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


def legato_line(notes, start, kind, dyn, rng=RNG, glide=0.09, vib_cents=20.0, tail=1.6):
    """One connected, sung line for a soloist: notes as (time, name, beats) relative to start."""
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
        self.stems = {k: Track(seconds) for k in ('piano', 'box', 'strings', 'solo', 'air')}
        self.wet = {'piano': 0.55, 'box': 0.7, 'strings': 0.5, 'solo': 0.42, 'air': 0.25}
        self.gain = {'piano': 1.0, 'box': 0.8, 'strings': 0.55, 'solo': 0.5, 'air': 0.4}

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
    ap.add_argument('--out', default='../../game/dl01/assets/music')
    ap.add_argument('--wav', default=None, help='also keep the WAV masters here')
    ap.add_argument('--only', nargs='*')
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    cues = {'wake': cue_wake, 'bed': cue_bed, 'hall': cue_hall, 'end': cue_end}
    rendered = {}
    for name, fn in cues.items():
        if args.only and name not in args.only:
            continue
        print('rendering', name, flush=True)
        st = fn()
        if name != 'bed':
            st = fade_tail(st)
        rendered[name] = st
    # One gain for every cue, so their balance is as written.
    peak = max(float(np.abs(s).max()) for s in rendered.values())
    gain = 10 ** (-1.0 / 20) / peak
    for name, st in rendered.items():
        # Tape hiss, added at its final level, about 64 dB down.
        st = st * gain + hiss(st.shape[1], 0.0011, np.random.default_rng(5))
        rms = 20 * np.log10(np.sqrt((st ** 2).mean()) + 1e-9)
        print(f'{name}: {st.shape[1] / SR:.1f} s, peak {20 * np.log10(np.abs(st).max()):.1f} dBFS, rms {rms:.1f} dBFS')
        wav = os.path.join(args.wav or args.out, f'dl01_{name}.wav')
        if args.wav:
            os.makedirs(args.wav, exist_ok=True)
        write_wav(wav, st)
        mp3 = os.path.join(args.out, f'dl01_{name}.mp3')
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', wav, '-c:a', 'libmp3lame', '-q:a', '3', mp3], check=True)
        if not args.wav:
            os.remove(wav)


if __name__ == '__main__':
    main()
