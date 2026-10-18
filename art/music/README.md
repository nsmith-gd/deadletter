# Chapter 1 (DL-01 and DL-02): score

The music for the first two scenes is written as a score in `compose_dl01.py`. The script renders it with small synthesized
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
| `hall` | 60 s | The first time he enters the sorting hall | A solo cello sings phrase A over strings and a broken piano, with violins two octaves up from bar 5. The coda is bars 13 to 16: E♭, then it stays open on A. |
| `threshold` | 44 s | The crank's last stroke, as the bulkhead opens | High string light and phrase A's first four bars on the felt piano while D-17 walks through the passage. Two music-box notes as he steps out into DL-02, then it settles into the bed. |
| `racks` | 62 s | The DL-02 plate holds the gate up without him | A low piano note for each row of rack lights as it comes on (1.0 s to 7.0 s, the game lights the rows at these times). Then phrase B as a slow strings chorale, a bar every 4 s, with the violins on the melody. The music box ends it with the parcel's three notes. |
| `end` | 100 s | Near the far end of the recharge hall, into the end card | High string light. Phrase A on piano, with the music box in bars 5 and 6, then phrase B on violins and cello. The motif slows, then a Picardy D major. Over it, the music box plays *Happy Birthday*, slowing as its spring runs down, and stops one phrase short. |

The GDD asks for sparse music at transitions and the ending, not continuous emotional instruction. So
the bed sits low, around 18 dB under the cues, and gives way to each cue. Puzzles keep their room tone
and mechanisms.

All cues share one gain so their balance is as written, so render them together for the game. Use `--only`
only to audition one.

## Instruments

- **Felt piano**: inharmonic partials, two detuned strings per note, a two-stage decay, a felt thump,
  and a damper. Softer notes are darker.
- **Music box**: tine modes at 1, 5.93 and 17.4 times the fundamental, a pluck click, up to ±5 cents of
  tuning error, and extra wow.
- **Strings**: additive bowed strings with body formants for violin, viola, cello and bass. Each note
  has an ensemble of detuned players with independent vibrato, and louder playing brightens the tone.
- **Solo lines**: one continuous pitch curve per phrase, with portamento, swells and bow changes.
- **Room**: a 4.2 s stereo convolution hall with early reflections and a longer, darker low end.
- **Tape**: wow and flutter, plus hiss about 64 dB down.

*Happy Birthday to You* is in the public domain in the United States (Marya v. Warner/Chappell, 2016).
