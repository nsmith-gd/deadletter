# Prologue music: "Undelivered"

**Status:** 21 October 2026. A proposal for the director. The music is rendered but not yet in the game.
**Source:** `art/music/compose_prologue.py`.
**Files:** `art/music/prologue/`: the theme, four loops, and `prologue_music.json`, which gives the sections and loop
points.

## What it is about

The prologue is the lower works in the Order era and the Failure (R.Y. 0–43, `docs/story_bible.md`):
- a sealed refuge graded and rationed under the Steward and ORDER ABOVE ALL;
- then the systems failing, and order saving the top and leaving the lower rings to die in heaps.

It is the world at its darkest: authoritarian, then apocalyptic. The theme takes the general identity
(`docs/research/musical_identity.md`) and turns each part of it toward that darkness:

| Identity | In the prologue |
|---|---|
| D minor and F major | **D Phrygian**: D minor with E-flat, the colour the `racks` lament already uses. |
| The lullaby's 3/4 | **A rigid 4/4 march at 60 bpm.** The Order's metre never agrees with the child's lullaby. Its beat still lines up with the rest of the score. |
| The cascade (D C A G F E D) | **The cascade flattened:** the parcel's E becomes E-flat. The true E is heard once, at the very end, on the music box. |
| D-17's hop | **One hop,** small and a little slow, at the end. Hope is kept at the edges. |
| The machine palette | The **tannoy's own chime** (E, C, the two notes the game plays before every "Order above all"), the far machinery, **open fifths with no third**, and a march on the low strings with a muffled parade snare. |
| The swell | Organ and horns for the **Steward's anthem**. Then the apocalypse: **tolling bells, an air-raid siren, anvils, taiko and a wordless choir.** |
| Long builds, a drop that fades, a crash | The failure builds in three rounds, and the first two pull back. The drop fades to near silence and leaves the tannoy chime playing alone. Then comes the climb into **the collapse.** |

## The theme (3:44)

| Time | Section | What happens |
|---|---|---|
| 0:00 | **lower_works** | The pedal: low D and A, wind in the shafts. The far machinery thuds on every beat. A bell tolls on D, far off. A high A and B-flat shimmer, and the piano drops D and E-flat together. |
| 0:32 | **order** | The tannoy chime. The march comes in on the low strings, D with E-flat and C around it, with a muffled parade snare. Low horns swell in open fifths, D–A and then E-flat–B-flat. |
| 1:04 | **anthem** | The Steward's anthem, a stately hymn in B-flat on organ and horns, over the march and the D pedal. It is benevolent and harsh, and the E-flat chords grind against the D. In its last two bars the whole world **runs down like a dying tannoy**: the tape slows to half speed and dies. |
| 1:36 | **failure** | Round 1: taiko, anvils, a bell on every bar, a far siren, and the flattened cascade on a cello. Round 2: the snare, toms, semiquaver strings on D and E-flat, and the choir and horns in open fifths. Round 3: the bass climbs D, E-flat, E, F with everything on it, then the siren, a snare roll and a timpani roll. The first two rounds pull back to a heartbeat on their last half bar. |
| 2:24 | (drop) | One blow on D with E-flat against it, with taiko, anvil and crash. Then everything fades and darkens over five seconds, down to −48 dB, and even the pedal sinks. In the silence the **tannoy chime plays alone**: *order above all*. Then a riser, a snare roll and a timpani roll climb out. |
| 2:32 | (collapse) | The loudest point. **E-flat major over the D pedal** (the Phrygian clash as catastrophe), with choir, horns, strings, bells, anvils and taiko. The anthem's opening returns in strings and horns, now falling in Phrygian (F, B-flat, A, G, F, E-flat, D), through G minor over D to a bare D–A fifth. |
| 2:48 | **heaps** | The lament. A soft choir moves D minor, E-flat over D, G minor over D. A cello carries the flattened cascade slowly. A bell tolls, and the piano's D and E-flat return. |
| 3:20 | **hope** | Over the pedal, the music box plays the parcel's F, E, D with the **true E**, the first E natural that isn't the tannoy's. D-17 hops once on pizzicato, a little slower than he'd like, and no one answers. The tannoy chime still runs, faintly. Then the pedal fades away. |

Measured by section, the levels are: lower works −32 dB, order −28, anthem −23, the failure's rounds −23, −21 and −17,
the drop down to −48, the collapse −15, the heaps −25, and hope −32. The theme measures −17.5 LUFS integrated with a
loudness range of 18.3 LU, as wide as the reference tracks.

## The loops

Every loop is eight bars (32 s) on the same D pedal, tempo and bar grid as the theme and as each other. So any of these
work on a bar line:
- a crossfade from the theme into a loop;
- a crossfade from one loop to another;
- a crossfade from a loop back to the theme.

Each file has 2 s of padding at each end. Loop it from `loop_start` (2.0 s) to `loop_end` (34.0 s). That is how the
game already loops `bed`, so the MP3 decoder's priming delay can't shift the seam. All the loops are mastered with the
theme's gain, so a crossfade keeps its level. The seams were checked: the step across each seam is smaller than the
loop's ordinary sample-to-sample steps, so there is no click.

| Loop | Level | What it is | Where |
|---|---|---|---|
| `prologue_loop_lower_works` | −30 dB | The pedal, far machinery, the bell, the high shimmer. The same as the theme's 0:00–0:32. | Exploring the depot and the dark lower works: DL-01, DL-02, DL-03, DL-08, DL-11. |
| `prologue_loop_order` | −26 dB | The lower works plus the march, the snare, the tannoy chime and horns in fifths. The same as the theme's 0:32–1:04. | Rooms of the Order: DL-05 The Ration Hall (the Steward's portrait), DL-06 at the scanner, DL-10 Up Only (RELOCATION — GRADES 1–2 ONLY). |
| `prologue_loop_heaps` | −26 dB | The lament: choir, cello, bell. The same as the theme's 2:48–3:20. | Among the dead: DL-04 The Racks, DL-06's pit, DL-07 The Heap, DL-10's queue line. |
| `prologue_loop_failure` | −20 dB | The failure held steady at round 2's force: march, snare, taiko, anvils, bells, semiquaver strings, choir and horns, one siren. Not in the theme as such. | Danger in a set piece: DL-09's slipping cage, from the slip until the pawl holds. |

**Suggested use:**
- **The score's cues still lead.** `wake`, `kin`, `dead`, `refuge` and `child` play over the loops as they do over
  `bed` now, and the loop ducks under them. These loops would replace `bed` in the prologue.
- **Crossfades:** move between loops over 2 to 4 s, on a bar line if the game counts bars from when the loop started.
  Otherwise a 3 to 4 s crossfade hides any phase difference, because every loop sits on the same D.
- **The full theme:** it suits the end card or a trailer. Its anthem, failure and collapse (1:04–2:48) could also play
  through DL-10's relocation lift going up without anyone.

## What the game needs

`Music` plays one cue at a time and loops one bed. To use these loops it needs:
- an ambience layer that holds two loop buffers, crossfades between them with each loop's own loop points, and ducks
  under cues and voices as `bed` does;
- a per-scene choice of loop: the "Where" column above, plus the cage's slip for `failure`.

This is a small change, and it isn't made yet.

## Limits

- **The sound:**
  - Everything is synthesized. The organ, the choir and the siren work best; the horns least.
  - Real brass and a real choir would be the biggest upgrade, then real bells and taiko.
- **The anthem:** it is original, written as a generic institutional hymn. It quotes no national or real-world anthem.
