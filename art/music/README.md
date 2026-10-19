# Chapter 1 (DL-01 to DL-09): score

The music for chapter 1 is written as a score in `compose_dl01.py`. The script renders it with small synthesized
instruments, so the music can be rebuilt and changed like any other asset.

```sh
python3 compose_dl01.py --out ../../game/undelivered/assets/music       # needs numpy and scipy, and ffmpeg with libmp3lame
python3 compose_dl01.py --only hall --wav /tmp/dl01              # audition one cue, keeping the WAV master
```

## The theme

The theme is in D minor, 3/4, at 60 bpm, so a bar lasts 3 s. It is a lullaby in two eight-bar phrases, and
`THEME` and `HARMONY` in the script hold the melody and the chords.

- **Phrase A** turns on the falling F, E, D figure: Dm(add9), B♭maj7, F/A, Gm7, Dm, B♭maj7, Gm6, then
  Asus4 to A.
- **Phrase B** climbs, then opens onto E♭maj7 (the flat second, the widest moment), and falls back to A.

In the opening, D-17's waking is three music-box notes: the motif's first three. The music box is the
parcel's voice. It is old, slightly out of tune, and it wobbles like tape.

## The cues

| Cue | Length | When | What |
|---|---|---|---|
| `wake` | 58 s | On Begin, under the opening | Wind and a low string floor, then the music box as he answers the relay (7 s). The felt piano comes in as he stands (12.5 s) and plays phrase A, but leaves bars 5 to 8 unfinished. The music box echoes the three notes. |
| `bed` | 48 s loop | During play, between cues | A low string pad (Dm, B♭maj7, Dm/A, Gm6), stray piano notes and air. It is written as one period, padded by 2 s each side, and the game loops 2 s to 50 s. |
| `hall` | 60 s | The first time he enters DL-01's sorting hall | A solo cello sings phrase A over strings and a broken piano, with violins two octaves up from bar 5. The coda is bars 13 to 16: E♭, then it stays open on A. |
| `threshold` | 44 s | The crank's last stroke, as the bulkhead opens | High string light and phrase A's first four bars on the felt piano while D-17 walks through the passage. Two music-box notes as he steps out into DL-02, then it settles into the bed. |
| `racks` | 26 s | The DL-03 plate holds the gate up without him | A low piano note for each row of rack lights as it comes on (1.0 s to 7.0 s; the game lights the rows at these times), then a held D minor, waiting. |
| `kin` | 70 s | D-17 first walks in among the couriers | He stops and looks: a low pedal and single high notes. Phrase A broadens to a bar every 3.5 s and builds over about 25 s: cello, then violins in octaves, the piano, a timpani roll and a cymbal swell into the peak on bar 8. Then it lets go, and the music box plays the parcel's three notes. |
| `dead` | 76 s | DL-05's scanner refuses room 114 | A close dissonance at the refusal. A swell over the pit on phrase B's last bars (E-flat to A), with a timpani roll. Near silence and the music box while he checks his label. Then the theme at a walking tempo, turning to F major for the first time. |
| `latch` | 11 s | DL-07's safety pawl drops home | A warm F major rolled on the piano, a soft string pad, and the music box's parcel notes (F, E, D, then C). It settles. |
| `refuge` | 40 s | D-17 steps out of the tunnel onto the balcony over the atrium | Awe, not grief. Near silence (a high string light over a low F pedal), then phrase B broadens toward F major, with the cello, then the violins in octaves. A timpani roll on C and a cymbal swell lead into the peak on F major, held at about 11.4 s, timed to the camera's widest. Then B-flat, D minor, the parcel's three notes on the music box, and an open fifth. The scene runs on into DL-09 under it. |
| `child` | 50 s | DL-09: the desk scrapes clear of the growth marks | The music box finds the parcel's three notes, slowly, and they become a lullaby (phrase A at a rocking pace) over soft piano and strings, which swell a little at the marks and the tree. It thins to a single high note as the terminal answers. `end` follows it over the end card. |
| `end` | 100 s | Over the end card, after `refuge` | High string light. Phrase A on piano, with the music box in bars 5 and 6, then phrase B on violins and cello. The motif slows, then a Picardy D major. Over it, the music box plays *Happy Birthday*, slowing as its spring runs down, and stops one phrase short. |

The GDD asks for sparse music at transitions and the ending, not continuous emotional instruction. So
the bed sits low, around 18 dB under the cues, and gives way to each cue. Puzzles keep their room tone
and mechanisms.

All cues share one gain so their balance is as written. `--only` renders just the named cues, but it always renders the
reference cues (`wake`, `hall`, `end`) to set that gain, so a cue rendered alone still matches the rest. DL-07's and
DL-08's cues are written as `dl04_latch` and `dl04_refuge`, and DL-09's as `dl05_child` (the files keep the old scene
numbers).

## Emotional moments

Following `docs/direction.md`, the realisation among the couriers (`kin`) and the pit (`dead`) are written
to swell rather than murmur:
- They build to real climaxes with timpani and a suspended cymbal.
- They are normalised against the gentler cues, so they can rise a few dB above them.
- A soft limiter catches their peaks.

## Instruments

- **Felt piano**: inharmonic partials, two detuned strings per note, a two-stage decay, a felt thump,
  and a damper. Softer notes are darker.
- **Music box**: tine modes at 1, 5.93 and 17.4 times the fundamental, a pluck click, up to ±5 cents of
  tuning error, and extra wow.
- **Strings**: additive bowed strings with body formants for violin, viola, cello and bass. Each note
  has an ensemble of detuned players with independent vibrato, and louder playing brightens the tone.
- **Solo lines**: one continuous pitch curve per phrase, with portamento, swells and bow changes.
- **Room**: a 4.2 s stereo convolution hall with early reflections and a longer, darker low end.
- **Timpani**: soft-mallet strokes with inharmonic membrane modes, rolled at 15 strokes per second with a crescendo curve.
- **Suspended cymbal**: a mallet roll of band-limited noise and metallic resonances, swelling to its peak.
- **Tape**: wow and flutter, plus hiss about 64 dB down.

*Happy Birthday to You* is in the public domain in the United States (Marya v. Warner/Chappell, 2016).
