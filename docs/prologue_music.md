# Prologue music: "Undelivered"

**Status:** 21 October 2026. A proposal for the director. The music is rendered but not yet in the game.
**Source:** `art/music/compose_prologue.py`.
**Files:** `art/music/prologue/`: the theme, four loops, two cues, and `prologue_music.json`, which gives the sections,
loop points and cues.

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

## Two cues cut from the theme for DL-10

These are cut from the theme master at the theme's gain, so they match the loops.

| Cue | From the theme | Length | Beat |
|---|---|---|---|
| `prologue_lastcar` | 1:20–1:36 | 16 s | DL-10: the relocation car leaves with the suitcase. The anthem's last phrase, then the world runs down. |
| `prologue_collapse` | 2:28.5–2:52 | 23.5 s | DL-10: riding the counterweight down, he looks down at ring C. The chime alone, the climb, the collapse (E-flat over D), and the first bar of the lament. |

DL-10 is where the Failure is told most directly: "the moment they left, and who went". So the theme's climax lives there.

## The beat map: when the music moves between loops and the big moments

The loops replace `bed` in the prologue. The rule is simple:
- **A loop fades out under a cue.** Every existing cue (`wake`, `hall`, `threshold`, `racks`, `kin`, `dead`, `latch`,
  `refuge`, `child`, `end`) and the two new ones play exactly as cues play now. The ambience fades out under them over
  about 1.5 s, as `bed` does today.
- **When a cue ends, the scene's loop fades back in** over about 4 s. That can be the same loop or a new one. It never
  comes back in the middle of a moment.
- **Voices and tannoys duck the loops** as they duck everything now.

| # | Beat (in the game today) | Music |
|---|---|---|
| 1 | Opening: `Music.play('wake')` | `wake` cue, then **lower_works** fades in when it ends. |
| 2 | DL-01: first entry to the sorting hall (`hall`) | `hall` cue, then back to **lower_works**. |
| 3 | DL-01: the bulkhead opens (`threshold`) | `threshold` cue, then **lower_works** through DL-02 and DL-03's puzzle. |
| 4 | DL-03: the gate opens and the camera pans over the couriers (`racks`) | `racks` cue, then **heaps**: he is among the dead couriers. |
| 5 | DL-04: the realisation (`kin`) | `kin` cue, then **heaps** until he leaves the racks. |
| 6 | DL-05: entering the ration hall (region 2, before `tan_rations` at x 56.6) | Crossfade **heaps → order** over 4 s. This is the Steward's portrait, the grade notices, and "Rations are suspended". |
| 7 | DL-06: the scanner rejects him (`dead`) | `dead` cue. When it ends (the belt, `scanned`), **lower_works**. |
| 8 | DL-07 and DL-08's puzzles | **lower_works**. The pawl (`latch`) plays its cue and returns to **lower_works**. |
| 9 | DL-08: into the residential tunnel (`tunnel`) | Ambience off, as `bed` is today: the tunnel is silent. |
| 10 | DL-09: the cage's brake gives, and it shudders and slips | **failure** fades in fast (about 1 s) and holds while the cage is in danger, including each retry. |
| 11 | DL-09: the pawl holds | **failure** fades out (about 2 s) under the pawl's click and `latch`, if it plays. Then silence into the tunnel. |
| 12 | DL-09: onto the balcony (`refuge`) | `refuge` cue, as now. It runs on into DL-10. |
| 13 | DL-10: the relocation lobby (`uponly`) | **order** fades in when `refuge` ends. This is the strongest Order room: RELOCATION — GRADES 1–2 ONLY, and the bridge and relocation tannoys, which duck it. |
| 14 | DL-10: he presses UP and the car rises with the suitcase | **`prologue_lastcar`** cue (the anthem's last phrase runs down). |
| 15 | DL-10: on the counterweight's ride down, as the camera looks down at ring C | **`prologue_collapse`** cue. It crossfades from `lastcar` if that is still playing. |
| 16 | DL-10/11: ring C (`ringc`) after the collapse | **heaps**, low, in place of today's silence. |
| 17 | DL-11: the bedroom (`bedroom`) | **heaps** fades out on entering the bedroom; the room is quiet. The desk reveal plays `child` as now. |
| 18 | The end card | `end`, as now. |

**Levels:** play all the loops at one gain, about **0.5**, against today's `BED_LEVEL` of 0.26. At that gain:

| Loop | Level in the game |
|---|---|
| lower_works | −35 LUFS (as quiet as `bed`) |
| order | −30 LUFS |
| heaps | −30 LUFS |
| failure | −24 LUFS |

Their relative levels are as written. The two new cues take a `LEVEL` of about 0.6, like the others.

## What the game needs

`Music` plays one cue at a time and loops one bed. It needs:
- **An ambience layer in place of the bed.** `Music.ambience(name | null, fade)` should crossfade between two looping
  sources, each looped from its own `loop_start` to `loop_end` (2.0 s and 34.0 s). It hides while a cue plays (as
  `updateBed` does) and comes back with the scene's current loop when the cue ends.
- **The two new cues** in `FILES` and `LEVEL`.
- **The calls at the beats above,** mostly where `Music.bed(...)` is called today, plus:
  - the ration-hall entry;
  - the cage's slip and hold;
  - the UP press;
  - the look down at ring C.

## Limits

- **The sound:**
  - Everything is synthesized. The organ, the choir and the siren work best; the horns least.
  - Real brass and a real choir would be the biggest upgrade, then real bells and taiko.
- **The anthem:** it is original, written as a generic institutional hymn. It quotes no national or real-world anthem.
