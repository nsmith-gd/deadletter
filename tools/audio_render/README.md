# Audio render (U-16a, issue #20)

Renders the web build's synthesized sound effects to WAV for the Unity port. The game makes nearly every SFX live in
WebAudio (`game/undelivered/index.html`, the `Sound`, `Ambience` and `Voice` modules). Unity needs files, and the
director-approved sound must stay the same, so this tool runs **the game's own code** in an offline WebAudio context
rather than a re-typed copy.

The output is in `art/sfx/out/`, and the import table is in `docs/unity/audio_inventory.md`.

## Re-running

```sh
cd tools/audio_render
npm ci                      # node-web-audio-api (Rust WebAudio for Node, prebuilt binaries)
node render.mjs             # everything -> art/sfx/out/*.wav, art/sfx/out/ir/*.wav, art/sfx/out/manifest.json
node render.mjs thud chain  # only the entries whose names contain these words (the manifest isn't rewritten)
node verify.mjs             # spot-checks against the code, and loop-seam checks
node callsites.mjs          # every Sound.* call in index.html: name, line, enclosing function, arguments
```

Node 22 (`/opt/node22/bin/node` in the cloud container). A full render takes about a minute. Renders are
deterministic: `Math.random` is replaced by a seeded generator per file (seeded from the file name), so re-running
gives the same bytes unless index.html changes.

## How it works

- `lib.mjs` reads index.html and slices out each module **verbatim**: from `const Sound = (() => {` to its closing
  `})();` (the same for `Ambience` and `Voice`). Nothing is re-typed. The source is evaluated with
  `new Function(...)`, with three things supplied from outside:
  - `window.AudioContext`, which hands back an `OfflineAudioContext` (48 kHz, stereo) from `node-web-audio-api`;
  - `setTimeout`, and the context's `currentTime`, on a **virtual clock**. The game schedules its notes with
    `ctx.currentTime` and staggers them with `setTimeout`. Here, each `setTimeout` callback runs in time order with
    `currentTime` reading the moment it was due, so every node is scheduled exactly where the game would schedule it.
    Then the whole graph is rendered offline in one go.
  - a seeded `Math.random`.
- **Patches.** These are the only edits to the extracted code. Each must match exactly once, or the render stops.
  - `Ambience`: the emitter bus `bus.gain.value = 0.9` is set to `1`, so the 0.9 is applied in the Unity mixer.
  - `Voice`: its returned object also exposes `chain`, `TREAT`, `crackleBuffer` and `impulse`, so the renderer can
    build a treatment's chain on its own.
  - Two short blocks from `Voice.play` are run on their own, still verbatim: the tannoy chime's loop (taken by
    balanced braces) and the crackle bed (from `const cr = …` to `cr.start(); c.nodes.push(cr);`).
- **Master.** After `Sound.start()`, the master gain (0.8 in the game) is set to 1. Every file is at the level the
  game produces **before** its master. In Unity, put the SFX on a mixer group at 0.8 (−1.94 dB) to match.
- **Dry and wet.**
  - Every `Sound` one-shot sends to the depot reverb: `out(node, dry = 1, rev)` feeds the master directly and also a
    send into a 2.4 s convolver at a 0.32 return.
  - The dry file cuts the return (`Sound.send.disconnect()`).
  - The `_wet` file is the full mix as heard in the browser: dry plus return.
  - For 66 quiet or very short sounds the return lies wholly below the −60 dBFS trim, so their wet file would be the
    dry one again. Those are skipped and listed in `manifest.json` under `wetSkipped`.
  - Random sounds get several takes (`_v1`, `_v2`, …); only `_v1` gets a `_wet` file.
  - The depot impulse is exported as `ir/ir_depot_2400ms.wav`, so Unity can rebuild the send exactly with a
    convolution reverb.
- **Trim.** Trailing samples below −60 dBFS (absolute, at the pre-master level above) are cut, with a 5 ms fade on the
  end. Nothing is normalized: relative levels between files are the game's.
- **Format.** 48 kHz, 16-bit PCM. A file is mono when its two channels are identical (every dry sound), and stereo
  otherwise (wet files, the chime, the impulses).
- **Parameters.** `node callsites.mjs` lists the arguments used at each call site.
  - A parameter that changes pitch or timing gets one file per value used: `servo(dur, f0, f1, peak)`, `chain(dur)`,
    `creak(dur)`, `rattle(dur)`, `rowOn(i)`, `relay(i)`, `answer(i)`, `setDown(onDeck)`, `curio(kind)` and
    `death(how)`.
  - Parameters that only scale amplitude are rendered at 1 and become a volume in Unity: `v`, `strength` and `soft`
    in `land`, `step`, `splash`, `zap`, `crackle`, `drip`, `clack`, `gateSlam` and `crateLand`.
  - These parameters scale the whole sound. For `env()` this is exact, except for its fixed 0.0001 floor (−80 dBFS).
  - `liftCrash(v)` is the exception: its inner `chain(0.5)` doesn't scale, so the cage's `v = 0.4` has its own file.

### Loops

The continuous layers have fixed graphs. Only their gain follows the game, through `setTargetAtTime`. So a loop at
level 1 is the whole sound, and Unity drives the AudioSource volume (the mapping is in the inventory).

- Each loop is rendered after a 6 s warm-up (3 s for emitters), so the gain glide and the filters have settled.
- The game's noise buffers loop every 2 s. Every oscillator and LFO in `hum`, `buzz`, `hiss`, `roll`, `tubes`, `belt`,
  `drum` and `drag` fits whole cycles into 2 s, so those layers repeat exactly every 2 s. Their 2 s loops are
  sample-exact cuts, with a 50 ms linear crossfade only to absorb oscillator phase rounding.
- Layers with a slow LFO are cut to a whole number of LFO periods, where that's practical, with an equal-power
  crossfade (the noise either side is uncorrelated):
  - `air`: 11.11 s, one 0.09 Hz period;
  - the `lap` emitter: 6.45 s;
  - the `buzz` emitter: 7.7 s;
  - the `machine` emitter: 10 s.
- The `wind` emitter's two LFOs (0.07 and 0.05 Hz) only realign at 100 s. It is cut at 20 s with a 2 s crossfade, so
  the swell is slightly irregular across the seam.
- The music box emitter's loop is one full turn of its tune: 11 notes and 4 rests, cut from the second turn of an
  every-frame render.

## Spot-check method (acceptance)

`verify.mjs` checks five renders against **numbers read off the code, not off the render**:

- **The envelope model.** `tone(freq, dur, type, peak)` runs its gain through `env()`: an exponential ramp from 0.0001
  up to `peak` over 4 ms, then an exponential ramp down to 0.0001 over `dur`.
- **Expected RMS.** The expected RMS of a partial is its envelope times the waveform's RMS factor: sine 1/√2,
  square 1, sawtooth 1/√3. Partials at different pitches add in power.
- **Comparison.** The render's RMS is measured in frames (10 ms, or longer where one period or one beat is longer:
  62.5 ms for the 48 Hz groan, 1/11 s for the 196 + 207 Hz beat in `reject`). It is compared frame by frame with the
  expected value, over frames whose expected level is above −50 dBFS.
- **Length.** The expected length is where the summed envelope crosses −60 dBFS, plus the 5 ms fade.

Results (render of 26 October 2026):

| File | Code | Length (got / expected) | Peak (got / envelope) | RMS envelope max deviation |
|---|---|---|---|---|
| `d17_strain` | `tone(780, 0.16, 'sine', 0.035)` | 106.0 / 106.0 ms | −29.17 / −29.12 dBFS | 0.10 dB |
| `mech_tick` | `tone(1900, 0.03, 'square', 0.03)` | 26.9 / 26.5 ms | −30.46 / −30.46 dBFS | 0.42 dB |
| `env_groan` | `tone(48, 1.4, 'sawtooth', 0.02)` | 800.0 / 800.5 ms | −34.21 / −33.98 dBFS | 0.30 dB |
| `mech_bell` | `tone(1568, .5, sine, .04)`, then 160 ms later `tone(1175, .7, sine, .035)` | 593.8 / 593.5 ms | −27.92 / −27.77 dBFS | 0.12 dB (second note's onset at 160 ms visible) |
| `mech_reject` | two square pairs (196 and 207 Hz), 320 ms apart | 520.5 / 520.0 ms | −20.92 / −20.92 dBFS | 1.80 dB (beating within a fast decay; the onset at 320 ms is visible) |

`verify.mjs` also checks every loop's seam. It measures the step from the last sample back to the first, against the
loop's RMS sample-to-sample step. All loops come out between 0.04 and 1.8, which is within the normal spread, so no
loop clicks.

## Hand-ported functions

None. Every rendered sound is the game's own code. The only hand-written parts are the drivers:

- which method is called, and with what arguments;
- a per-frame `Ambience.update` loop at 60 Hz;
- the composite `mech_relay_pulse`, which is the main loop's `[0, 1, 2].forEach(i => setTimeout(() => relay(i), i * 500))`
  at strength 1.

## What isn't rendered (runtime)

Each of these is listed with its reason in `docs/unity/audio_inventory.md`:

- the voice placeholder murmur, which is random, shaped to each voice's subtitle lines, and stands in until the
  director's recordings exist (`assets/voice/` doesn't exist yet);
- the radio's static swell, whose automation spans the voice's length;
- the `Music` module, which plays MP3 files already.

## Size

228 files and 27.9 MB (`manifest.json` lists every file's channels, length, peak and RMS).
