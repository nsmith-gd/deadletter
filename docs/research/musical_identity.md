# Dead Letter: a musical identity from Prahlow, Lober and Richards/Hahlweg

**Status:** 21 October 2026, second version. A proposal for the director, built on the composer studies in
`reports/Dead Letter soundtrack composer studies.md` and on measurements of three tracks the director supplied.
**Sketch:** `art/music/sketch_identity.py` renders a cue of about 2:25 in this identity
(`art/music/sketches/identity_sketch.mp3`). The sketch is for listening, not for the game.

**What changed after the first sketch.** The director heard the first sketch and asked for four things:
- more intrigue and a sense of exploration, as in Richards and Hahlweg's *Sheepy*;
- D-17's whimsy, because the character is playful;
- a longer, teasing build that drums push upward, ending in a giant crashing crescendo;
- a drop before full power that fades rather than stops suddenly.

Rules 2 to 6 and the sketch are rewritten to match. The director's direction overrides the measured evidence where the
two differ. The clearest case is drums: Lober's climaxes are drumless, but this score's are not.

## The identity in one paragraph

The score is rooted in D minor and F major, and it is curious before it is sad. It walks: a moving ostinato over a held
note, with a raised note (B natural, the Dorian sixth and Lydian fourth) that gives it the colour of looking around a
corner. D-17 has a voice of its own, a skipping, slightly clumsy hop, traded between music box, pizzicato and whistle over
an oom-pah-pah bass. The big moments are earned through long builds in rounds. Each round adds drums and lifts the
strings, and the early rounds tease by pulling back for a bar before pushing on. At the top the music falls away, fading and
darkening into near silence. Then it climbs back out of that silence on a riser and rolls, into a crashing arrival with drums,
horns and strings in octaves. Its melodies fall through the pentatonic scale and land on the parcel's F, E, D, or, at the
arrivals, turn upward. When the arrival is spent, D-17 has the last, small, playful word. The refuge's machinery gets the
opposite sound: synth pulses and open fifths with no third.

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

A third habit, his drums arriving only after a long drumless stretch (the first at 2:39 in "The Way"), is now part of
rule 6: drums are kept for the big moments, and each build earns them.

## The rules

1. **Silence first; the pedal is the floor.** Between cues the score is room tone and emitters, as `direction.md` already
   asks. When music comes in, it comes in on a held note. Use D or F, low or high, or both.
   - The bed (`bed`) should become a pedal with occasional music-box glints from the D-minor pentatonic (D, F, G, A, C),
     rather than a moving chord pad.
2. **Three palettes and a swell.**
   - **The hearth:** whistle, a plucked string (between nylon guitar and banjo), the music box and the felt piano, for
     the living, for Mara and for memory.
   - **D-17's play:** pizzicato strings, the music box and the whistle, trading short figures in call and response,
     over an oom-pah-pah pizzicato bass (bass on one, chord on two and three). A shaker ticking quavers keeps it walking.
     This is the palette of curiosity and of D-17's whimsy.
   - **The machine:** a soft analog-style pad and a quaver pump, for the protocols, the attendant and Protective
     Custody.
   - **The swell:** the existing strings (now with spiccato ostinatos as well as long notes), violins in octaves, cello,
     horns, timpani, a drum section (taiko, toms, kick, snare) and cymbals.
   - **Mixing them:** a scene may mix palettes. The meaning comes from which palette leads.
3. **Two melodic cells: the cascade and the hop.**
   - **The cascade** is the parcel's cell: D6, C6, A5, G5, F5, speeding up, then E5 and D5, slower.
     - The first five notes are pentatonic. The last three are the parcel's F, E, D, so every cascade ends by quoting the
       parcel.
     - The E is the only note outside the pentatonic: the parcel's "wrong" note, the one that hurts.
     - The cascade can be cut at any point. Ending on F is home, ending on E is unfinished, and ending on D is
       delivered.
     - At the arrivals it turns **upward**: D, F, G, A, C, D, the same scale climbing. That is D-17's spirit lifting.
   - **The hop** is D-17's cell: C5, F5, a rest, then E5, F5 and a leap to A5, then G5, **B5**, A5, F5.
     - It skips up, stumbles, leaps and winks. The B natural is the wink: a note just outside the key, curious rather
       than wrong.
     - It belongs to pizzicato and the music box. It can grow onto the cello in a build, and it gets the last word after
       an arrival.
4. **Harmony: curiosity, pedals, colour, warm landings.**
   - **Keys:** stay in the D-minor and F-major pair the score already uses.
   - **Curiosity:** for exploration, raise one note. D Dorian (D minor with B natural) and F Lydian (F major with B
     natural) are the colours of looking around a corner. G major over a D pedal, and G over F, are the signature chords.
   - **Colour:** add 9ths and major 7ths, the colour of "Almost Alive".
   - **Builds:** climb the bass by step into the top (G, A, B♭, C), so the dominant is the edge of the drop.
   - **Arrivals:** crash onto F. Let the arrival's own phrase close **plagal** (B♭ to F), so it ends like coming home
     rather than winning.
   - **The Order:** give it open fifths with no third.
   - **D major:** keep it back, as the composer studies recommend, for DL-51.
5. **Form: long builds in rounds, a drop that fades, a climb out of the silence.**
   - **Rounds:** build in rounds of about eight bars (16 seconds at 90 bpm). Each round adds a layer of drums, lifts the
     strings an octave or adds one, and moves the melody to a higher, fuller voice. A big moment wants at least three
     rounds, about 45 seconds of build.
   - **The tease:** the first rounds end by pulling back for a bar, to a heartbeat and a held chord, before the next
     round pushes on harder. The listener should feel it about to break more than once.
   - **The drop:** at the top of the last round, land a final chord with a crash, then let everything fade and darken
     (the low-pass closing) over four to five seconds into near silence. It does not stop dead. In the silence, one small
     sound at most: a far whistle, a heartbeat.
   - **The climb:** from the silence, a riser (reverse cymbal), a snare roll and a timpani roll climb for about three
     seconds into the arrival.
   - **The tail:** after the arrival, let the final chord ring and fall away. Then the music box or D-17's hop finishes
     alone.
   - **Longer set pieces:** these may drop twice, with the first drop shallower than the second.
6. **Drums drive the build and crash the arrival.**
   - **In the build:** drums enter in layers. First a taiko on the downbeat and a shaker, then a full 3/4 groove (taiko on
     one, toms on two and three, a snare on three), then fills and a snare roll into the top.
   - **At the arrival:** a crash and the biggest taiko hit on the downbeat, the groove at full strength, a crash every
     four bars, and one last hit on the final chord.
   - **Elsewhere:** exploration and whimsy keep percussion light (shaker and pizzicato), and quiet scenes have none.
     Drums are what tell the player this is a big moment, so use them only for big moments.
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
cymbal swell, wind, hall, tape) and adds new ones:
- pizzicato strings;
- a whistle;
- an analog-style pad with a quaver pump;
- a horn section built from saw waves;
- a drum section: taiko, toms, kick, snare, shaker and crash cymbal.

It runs about 2:25, in 3/4 at 90 bpm (a bar is 2 s). The first sketch was 80 seconds at 60 bpm; the faster tempo gives
the exploration room to walk.

| Time | Rule it shows | What plays |
|---|---|---|
| 0–20 s | 1, 4 | **Intrigue.** A D pedal. A felt-piano ostinato walks in quavers through D minor 9, G over D (the Dorian B natural), B♭ with an E, and A sus 4. Music-box glints on B, E and A. A shaker starts ticking at 10 s, and pizzicato footsteps join at 14 s. |
| 20–44 s | 2, 3 | **Whimsy.** An oom-pah-pah pizzicato bass in F, with G over F for the Lydian wink. D-17's hop on music box, doubled by pizzicato. The whistle answers with half the cascade, then takes the hop itself, and the music box answers with the cascade. They hop together, then the whistle sings the whole cascade into the build. |
| 44–60 s | 5, 6 | **Build, round 1.** B♭, C, D minor. Viola spiccato, taiko on the downbeats, a shaker, and the hop grown onto the cello. The last bar pulls back to a heartbeat. |
| 60–76 s | 5, 6 | **Build, round 2.** Violin spiccato over held string chords, the full 3/4 drum groove, the synth pad pumping, and the cascade turned upward on violins. The last bar pulls back again. |
| 76–92 s | 4, 5, 6 | **Build, round 3.** Spiccato in octaves, the groove harder, and the upward cascade in violins, octave violins and cello. Then the bass climbs G, A, B♭, C, with horns entering bar by bar, tom fills, a snare roll, a timpani roll and a cymbal swell into the top. |
| 92–100 s | 5 | **The drop.** A C major chord with a crash and taiko, then everything fades and darkens over five seconds into near silence. A far whistle and a faint heartbeat. Then the riser, a snare roll and a timpani roll climb out of the silence. |
| 100–124 s | 3, 4, 6 | **The arrival.** F, with the biggest taiko and a crash. The drum groove at full strength, with a crash every four bars. Horns, spiccato and held strings; the cascade turned upward and then falling home in violins, octave violins, cello and horns. It runs F, C over E, D minor, B♭, F over A, G minor 7, then **B♭ to F** at the close. |
| 124–146 s | 3, 8 | **It lets go.** The last F rings with a final hit. The music box plays the whole cascade over a D, and D-17 has the last word: the hop on pizzicato, and one more note, a little late. |

Measured with the same tools as the reference tracks, by section (average level):

| Section | Level |
|---|---|
| Intrigue | −31 dB |
| Whimsy | −24 dB |
| Build round 1 | −25 dB |
| Build round 2 | −22 dB |
| Build round 3 | −19 dB |
| Arrival | −16 dB (peak seconds −12 dB) |
| Outro | −28 dB |

The drop falls from −15 dB to −48 dB over three seconds, then climbs back through −32 and −27 dB into the arrival. The
whole sketch measures −17.4 LUFS integrated, with a loudness range of 15.5 LU.

**Known limits.**
- **The sound:** the whistle, pluck, horns and drums are synthesized and sound it. A recorded whistle and real drums or
  drum samples would lift this most. The horns are the weakest part.
- **The melodies:** the cascade and the hop are new material. The cascade shares only a generic idea with Lober's hook (a
  pentatonic fall that speeds up). It differs in metre, contour, starting note and ending, since it ends on the parcel's
  E and D rather than the tonic.

## What it would change in the existing cues

These are recommendations; nothing in the game has been changed.

| Cue | Change |
|---|---|
| `bed` | Replace the chord pad with a D (or F) pedal and rare pentatonic music-box glints. |
| `wake` | Keep it. The music box's three notes are already the end of the cascade. As he stands, add the hop once, on pizzicato, small: D-17's first playful step. |
| `hall`, `threshold` | `hall` can take the intrigue ostinato (Dorian, over its pedal) under the cello. `threshold` is a walk into a new space, so it suits a short exploration figure with a shaker. |
| `racks` | Keep it. Its low pedal and bare, unresolved ending already lean toward the Order's sound. |
| `kin` | Build it in rounds with a pull-back, let it fade into a short drop before the bar-8 peak, then roll back up into the peak. It is a moment of grief, so keep the drums out and let the timpani carry it. |
| `dead` | Fine as it is. Its turn to F major can land via B♭ (rule 4). |
| `refuge` | Already the closest to the identity (near silence, then a peak). It is the chapter's one wide reveal, so it can take the full shape: a short build with drums, a fading drop, then the crash into F, closing B♭ to F. |
| `child` | Re-dress phrase A as a music-box version (rule 8). It already is one. |
| `end` | Let the final chord fall away to the music box, stop the cascade on E, and give D-17's hop the last word. This holds the full resolution back for DL-51. |

## Appendix: the numbers

| Track | Length | Loudness (integrated) | Loudness range | Peak section | Breath | Percussive share at peak |
|---|---|---|---|---|---|---|
| Lober, "Almost Alive" | 1:27 | −11.6 LUFS | 15.9 LU | 0:42–1:17, −13.2 dB | none (it is an intro) | 0.17 |
| Lober, "We Rule the World" | 4:05 | −14.0 LUFS | 19.2 LU | 2:29–3:15, −14.7 dB | 2:19–2:24, −47 to −60 dB | 0.13 |
| Hemsey, "The Way" | 7:06 | −10.3 LUFS | 16.5 LU | 3:29–6:04, about −11 dB | 2:16–2:24 and 3:23–3:29 | 0.15–0.35 |
| Dead Letter `kin` | — | −13.7 LUFS | 23.2 LU | — | — | — |
| Dead Letter `refuge` | — | −14.5 LUFS | 19.4 LU | — | — | — |
| Identity sketch (first) | 1:20 | −18.5 LUFS | 16.3 LU | 0:50–0:59, −15 to −17 dB | 0:47–0:50, −36 dB | under 0.2 |
| Identity sketch (second) | 2:26 | −17.4 LUFS | 15.5 LU | 1:40–2:04, −16 dB | 1:32–1:37, fading to −48 dB | not comparable* |

\*The percussive-share measure separates sharp transients from sustained tones. The sketch's synthesized drums are
mostly pitched sine sweeps, so the measure reads them as tones and misses most of them. The stem levels confirm the drums
are there. Measured on their own, they lead the build: about 7 dB above the strings in round 1 and 4 dB above in
round 3. In the arrival they sit level with the strings, at about −20 dB each.

The analysis scripts, figures and per-second tables are kept outside the repository, together with the source audio,
which is the director's own copy and is not committed here.
