# Dead Letter: a musical identity from Prahlow, Lober and Richards/Hahlweg

**Status:** 21 October 2026. A proposal for the director, built on the composer studies in
`reports/Dead Letter soundtrack composer studies.md` and on measurements of three tracks the director supplied.
**Sketch:** `art/music/sketch_identity.py` renders an 80-second cue in this identity
(`art/music/sketches/identity_sketch.mp3`). The sketch is for listening, not for the game.

## The identity in one paragraph

The score is rooted in D minor and F major and played on instruments a person could hold: a whistle, a plucked string,
the music box and the felt piano. It speaks rarely. When it does, it stands on a held note, a pedal, and builds in steps, not
ramps. Just before its biggest arrival it takes a breath of near silence. It arrives warm rather than triumphant, landing on
B-flat (the subdominant) before F, without drums. Then it cuts away at once and leaves one small voice to finish. Its
melodies fall through the pentatonic scale and land on the parcel's F, E, D. The one note outside the pentatonic, E, is the
parcel's voice. The refuge's machinery gets the opposite sound: synth pulses and open fifths with no third.

## How this was built, and how sure it is

- **Phil Lober, measured.** The director supplied "Almost Alive" and "We Rule the World" as WAVs. I can't hear audio, so I
  measured them with `librosa` and `ffmpeg`. The measurements are loudness per second and per frequency band, stereo width,
  how percussive the sound is, tempo, key, chord and bass-line estimates, and section boundaries. Loudness, timing and
  stereo figures are reliable. Key, chords and melody are estimates from the spectrum, so treat them as approximate.
  Written sources on Lober are almost empty, so these measurements are now the main evidence for him.
- **Zack Hemsey, measured.** "The Way" was measured the same way. Hemsey isn't one of the three anchors, but two of his
  habits proved useful and are kept (see "What comes from Hemsey").
- **Andrew Prahlow, sourced.** From the composer study: his own statements as reported, and the design of *Outer Wilds*.
  It is moderately well sourced, through search excerpts only.
- **Tal Richards and Hahlweg, sourced, thin.** From the composer study: reviews and the soundtrack's track list. No
  analysis of the music exists. Treat this as the weakest of the four inputs.
- **What would sharpen it.** The director has listened to "We Rule the World" for ten years. A list of the moments that
  matter, with rough timestamps, would let each rule below be checked against what a listener actually responds to.

## What the measurements show

### "We Rule the World" (Lober, 4:05)

| Time | What happens (measured) |
|---|---|
| 0:00–0:05 | Fades in from nothing. |
| 0:06–0:48 | The hook: a falling run in the F-major pentatonic (G, F, D, C, A, G, F) that **speeds up as it falls**, from about 0.9 s a note to about 0.3 s, landing on F. It comes back about every 5.3 s. The bass moves B♭, F, G, D (IV, I, ii, vi in F). The low end (sub and bass) comes in at 0:26, about 8 dB up. |
| 0:48–1:04 | A pull-back: the low end thins and the texture gets busier and quieter. |
| 1:04–2:19 | **Plateaus, not a ramp.** Each section steps up 2 to 4 dB: −24.8, −21.9, then −19.1 dB. The upper frequencies (4–10 kHz) jump about 11 dB at 1:58. The tonal centre moves toward B♭ from about 1:36, with E♭ and C minor colours. |
| **2:19–2:24** | **The breath.** Five seconds of near silence (−47 to −60 dB) in which only a bright, high residue remains. |
| 2:24–2:29 | Re-entry, rising. |
| 2:29–3:15 | The arrival: the loudest part of the track (−14.7 dB average), full range from sub-bass to 8 kHz and above, **centred on B♭** (B♭ is the strongest pitch class in the section, and F is second). The melody sits low and sighs between F and G. |
| **3:15** | **A hard cut** to −35 dB within a second, with no tail-off. |
| 3:15–4:05 | A long, airy fade. The stereo image is at its widest here (0.96–0.98), and darker borrowed notes (A♭, G♭) appear before it dies away. |

Across the whole track, three things stand out:

- **Percussion:** the percussive share of the sound stays between 0.02 and 0.13. The climax is carried by register,
  harmonic density and brightness, not by drums.
- **Dynamic range:** the loudness range is 19.2 LU, very wide for produced music.
- **Tempo:** the track sits at about 90 bpm, with strong 0.5 s and 1.0 s spacings that suggest dotted rhythms. This is
  approximate, because the beat tracker disagreed with itself.

### "Almost Alive" (Lober, 1:27)

| Time | What happens (measured) |
|---|---|
| 0:00–0:44 | **A pedal.** For 44 seconds the only steady pitch is F. In this section F's pitch-class weight is 1.00 and no other is above 0.25. Over it, sparse high glints from the pentatonic (C6, G5, F6, D6, G6) come every few seconds. |
| 0:35–0:42 | It brightens: the upper frequencies come up about 20 dB. |
| 0:42 | Everything enters at once, 11 dB up. The stereo image **narrows** to 0.53, so the big entry is focused, not wide. The harmony turns to F major 7 and F add 9 (E and G against F). |
| 1:17 | A hard drop. It ends on F with D above it, so the "almost" stays unresolved and hands over to "Alive". |

### "The Way" (Hemsey, 7:06)

| Time | What happens (measured) |
|---|---|
| 0:00–2:16 | A bass ostinato, F, E♭, D♭, about 4 s a chord, under **a high F held for six minutes**. It uses open fifths: A♭, the third, is nearly absent (weight 0.13), so the music is neither major nor minor. It is drumless (percussive share about 0.05). |
| **2:16–2:24** | A breath of about 8 s at −38.6 dB. |
| 2:39 | The drums arrive for the first time (percussive share 0.35). |
| **3:23–3:29** | A second breath, about 6 s at −31 dB. |
| 3:29–6:04 | The full climax, about 2.5 minutes at −11 to −12.6 dB, with the sound brightening steadily (centroid 1,300 to 1,900 Hz). |
| **6:04** | A hard cut back to the ostinato, then a long fade. |

### What the three tracks share

1. **A pedal underneath.** A sustained F runs under both "Almost Alive" (low) and "The Way" (high).
2. **A pentatonic fall.** Lober's hook falls through the pentatonic and speeds up as it goes.
3. **Building in plateaus.** "We Rule the World" and "The Way" both rise in level by steps, not a smooth ramp.
4. **A breath before the arrival.** A near-silence of 5 to 8 seconds comes right before the biggest entry. "We Rule the
   World" has one and "The Way" has two.
5. **A hard cut, then a long tail.** All three tracks end their climax by cutting away at once, then fade slowly.
6. **Wide dynamic range.** The loudness range is 16 to 19 LU in all three. Dead Letter's existing `kin` and `refuge` cues
   are already 23 and 19 LU, so the game is already built for this.

## What each composer contributes

### Lober: the shape of an arrival

Lober contributes the dramatic form, and it is the strongest evidence here because it is measured:

- a pedal to stand on;
- a pentatonic fall that speeds up into its last note;
- plateaus that step up;
- the breath;
- an arrival on the subdominant rather than a dominant-to-tonic cadence;
- no drums at the climax;
- a hard cut, then a long, airy tail;
- a narrow image at the punch and a wide one in the tail.

The "Almost Alive" ending (F with D above it, unresolved) is also a model for Dead Letter's chapter endings.

### Prahlow: when to speak, and with whose voice

From the composer study, Prahlow contributes four things:

- **Silence as policy.** Music that loops constantly becomes "wallpaper". He treated the game "like a film", with music
  only at emotionally important moments.
- **Folk instruments for the living, synths for the dead.** Banjo, harmonica and whistling stand for the Hearthians;
  ambient synths stand for the Nomai.
- **Suite first.** He wrote full pieces, then cut them into loops.
- **One song in scattered parts.** Each Traveler plays one part, and they all join at the end. The last voice joins only
  by consent.

In Dead Letter, the people of the refuge get Prahlow's folk side: whistle, pluck, hummed or whistled voices on the voice
cards. The machinery and protocols get his synth side.

### Richards and Hahlweg: the score that recedes, and its re-dressings

From the composer study (thin evidence), Richards and Hahlweg contribute four things:

- **Recede, then swell.** The score fades under the ambience and swells at key moments.
- **Re-dressed versions.** The album's Music Boxes, String Quartet, Orchestral and Alternate versions retell the same
  tunes.
- **Piano with electronics.** Emotional piano meets electronic pulse at the boss fights.
- **A finale that subtracts.** The player's powers are taken away one by one while the music plays.

In Dead Letter this becomes three things:

- one tune re-dressed for each story state, and especially a **music-box version** of anything important;
- a soft electronic pulse as the only beat in the identity;
- subtraction as a way to end a sequence.

### What comes from Hemsey

Two habits from "The Way" carry over:

- **Open fifths with no third, under a long ostinato,** as the sound of the Order and its machinery. It is cold, certain
  and neither happy nor sad.
- **The second breath.** A longer piece can breathe twice: once before the first big entry and once before the real
  climax.

His drums are held back for at most one moment in the whole game (see rule 6).

## The rules

1. **Silence first; the pedal is the floor.** Between cues the score is room tone and emitters, as `direction.md` already
   asks. When music comes in, it comes in on a held note. Use D or F, low or high, or both.
   - The bed (`bed`) should become a pedal with occasional music-box glints from the D-minor pentatonic (D, F, G, A, C),
     rather than a moving chord pad.
2. **Two palettes and a swell.**
   - **The hearth:** whistle, a plucked string (between nylon guitar and banjo), the music box and the felt piano, for
     the living, for Mara and for memory.
   - **The machine:** a soft analog-style pad and a quaver pump, for the protocols, the attendant and Protective
     Custody.
   - **The swell:** the existing strings, violins in octaves, cello, timpani roll and suspended cymbal, as
     `direction.md` specifies.
   - **Mixing them:** a scene may mix palettes. The meaning comes from which palette leads.
3. **Melody falls through the pentatonic and lands on the parcel.** The core cell is **the cascade**: D6, C6, A5, G5, F5,
   speeding up, then E5 and D5, slower.
   - The first five notes are pentatonic. The last three are the parcel's F, E, D, so every cascade ends by quoting the
     parcel.
   - The E is the only note outside the pentatonic: the parcel's "wrong" note, the one that hurts.
   - The cascade can be cut at any point. Ending on F is home, ending on E is unfinished, and ending on D is delivered.
4. **Harmony: pedals, colour, warm arrivals.**
   - **Keys:** stay in the D-minor and F-major pair the score already uses.
   - **Colour:** add 9ths and major 7ths, the colour of "Almost Alive".
   - **Arrivals:** land big moments on **B♭** (the subdominant in F), then move to F. The ending sounds like coming home,
     not like winning.
   - **The Order:** give it open fifths with no third.
   - **D major:** keep it back, as the composer studies recommend, for DL-51.
5. **Form: plateaus, the breath, the hard cut.**
   - **Plateaus:** build by adding a layer every one or two bars, a few dB each time, never with a smooth crescendo.
   - **The breath:** before the biggest arrival, hold 2 to 5 seconds of near silence (at least 10 dB below the plateau
     before it), with at most one small sound.
   - **The hard cut:** end the arrival by cutting to one voice at once, then let a long tail fade.
   - **Longer set pieces:** these may breathe twice.
6. **No drums at the climax.** Power comes from register spread, harmonic density and brightness. Percussion is the
   timpani roll and cymbal swell rising *out of the breath* into the peak, as `direction.md` asks. Hemsey's drums are for
   at most one mechanical set piece in the whole game. The DL-34 alarm is the candidate the composer studies already
   name.
7. **Mix: wide space, focused punch, wide dynamics.**
   - Keep the tails wide and the arrivals narrower, as "Almost Alive" narrows to 0.53 at its entry.
   - Keep each cue's loudness range around 15 to 20 LU, and don't compress swells flat.
8. **Re-dress and scatter.**
   - **Re-dress:** every important tune gets a music-box version (Richards/Hahlweg).
   - **Scatter:** the in-world sources each carry one part of a single piece: the den's music box, the radio's children's
     song, a whistler on a voice card. The parts join at DL-51, and D-17's voice joins last, only if the player sits
     (Prahlow).

## The sketch

`sketch_identity.py` uses the score's own instruments from `compose_dl01.py` (felt piano, music box, strings, timpani,
cymbal, wind, hall, tape) and adds three:
- a plucked string;
- a whistle;
- an analog-style pad with an optional quaver pump.

It is 80 seconds long, in 3/4 at 60 bpm:

| Time | Rule it shows | What plays |
|---|---|---|
| 0–14 s | 1, 3 | An F pedal (low cello and bass, a very quiet high violin F) with music-box glints from the pentatonic. |
| 14–29 s | 2, 3 | The pluck rocks in 3/4 over the pedal. The whistle sings the cascade, then half of it, and the music box answers with the parcel's F, E, D. |
| 29–47 s | 5, 2 | Phrase A's harmony (Dm add9, B♭maj7, F/A, Gm7) at 4.5 s a bar. Each bar adds a layer: low strings, then violas, then violins in octaves on the cascade, then the synth pad and its pump. |
| 47–50 s | 5 | The breath: everything stops within a quarter of a second, and one quiet music-box note sounds. |
| 50–61 s | 4, 6 | The roll and cymbal rise out of the silence into **B♭ add 9**, with the cascade broad in violins, octave violins and cello. Then F major with D on top. There are no drums. |
| 61–80 s | 5, 3 | A hard cut. The music box alone plays the cascade, small, and **stops on E**: the last D is left unplayed. |

Measured with the same tools as the reference tracks, the sketch behaves as designed:
- **Plateaus:** from −25/−26 dB, the build steps to −24, then −21 dB.
- **The breath:** it reaches −36 dB, about 15 dB below the last plateau.
- **The arrival:** −15 to −17 dB.
- **The cut:** within a second it drops to −34 dB, and the tail fades over 18 s.
- **Percussion:** the percussive share stays under 0.2.
- **Overall:** −18.5 LUFS integrated, with a loudness range of 16.3 LU, inside the range of the reference tracks.

**Known limits.** The whistle and pluck are synthesized and sound it. A recorded whistle (the director could record it)
and a real nylon guitar or banjo would lift the hearth palette most. The cascade is new material. It shares only a
generic idea with Lober's hook: a pentatonic fall that speeds up. It differs in metre (3/4), contour, starting note and
ending, since it ends on the parcel's E and D rather than the tonic.

## What it would change in the existing cues

These are recommendations; nothing in the game has been changed.

| Cue | Change |
|---|---|
| `bed` | Replace the chord pad with a D (or F) pedal and rare pentatonic music-box glints. |
| `wake` | Keep it. The music box's three notes are already the end of the cascade. Let the whistle or pluck hint at the cascade's first notes once, far off. |
| `hall`, `threshold` | Keep them. They are already sparse and end open, which is rule 3's "unfinished". |
| `racks` | Keep it. Its low pedal and bare, unresolved ending already lean toward the Order's sound. |
| `kin` | Build it in plateaus and add **the breath** (2 to 3 s) before the bar-8 peak. Then hard-cut to the music box. |
| `dead` | Fine as it is. Its turn to F major can land via B♭ (rule 4). |
| `refuge` | Already the closest to the identity (near silence, then a peak). Move the peak from F major to **B♭ add 9 then F**, and take a short breath before the roll. |
| `child` | Re-dress phrase A as a music-box version (rule 8). It already is one. |
| `end` | End with a hard cut to the music box and stop the cascade on E. This holds the full resolution back for DL-51. |

## Appendix: the numbers

| Track | Length | Loudness (integrated) | Loudness range | Peak section | Breath | Percussive share at peak |
|---|---|---|---|---|---|---|
| Lober, "Almost Alive" | 1:27 | −11.6 LUFS | 15.9 LU | 0:42–1:17, −13.2 dB | none (it is an intro) | 0.17 |
| Lober, "We Rule the World" | 4:05 | −14.0 LUFS | 19.2 LU | 2:29–3:15, −14.7 dB | 2:19–2:24, −47 to −60 dB | 0.13 |
| Hemsey, "The Way" | 7:06 | −10.3 LUFS | 16.5 LU | 3:29–6:04, about −11 dB | 2:16–2:24 and 3:23–3:29 | 0.15–0.35 |
| Dead Letter `kin` | — | −13.7 LUFS | 23.2 LU | — | — | — |
| Dead Letter `refuge` | — | −14.5 LUFS | 19.4 LU | — | — | — |
| Identity sketch | 1:20 | −18.5 LUFS | 16.3 LU | 0:50–0:59, −15 to −17 dB | 0:47–0:50, −36 dB | under 0.2 |

The analysis scripts, figures and per-second tables are kept outside the repository, together with the source audio,
which is the director's own copy and is not committed here.
