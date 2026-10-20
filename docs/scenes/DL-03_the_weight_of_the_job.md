# DL-03 The Weight of the Job: production plan

**Status:** built as a playable prototype (`game/undelivered/`), for director review
**Source:** Dead Letter 45 Scene Overview, scene 02 (16 October 2026)
**Sequence:** DL-02 → DL-03 → DL-04, with no cut on either side

> **Renumbered 18 October 2026.** Chapter 1 then had nine scenes (eleven since pass 3); this was DL-02. The rework in
> `docs/chapter1_plan.md` and `docs/chapter1_build_spec.md` supersedes this plan where they differ.
**Duration target:** 4 minutes

## 1. What the scene must do

| Requirement (from the overview) | How the build meets it |
|---|---|
| Stand on a floor plate to open a gate; discover that leaving closes it | The plate is the first thing in the room's path. Standing on it lifts the gate all the way; stepping off drops it at once, with a clang. |
| Carry a sorting weight onto a trolley and park it on the plate | The weight is too light on its own and so is the trolley (the gate lifts only partway). The weight on the trolley, parked on the plate, holds the gate open. |
| Both plate and gate stay in view | The room's camera barely moves. It frames the whole 5.5 m room, with the plate and gate always on screen. |
| Introduce substitution: an object can hold a state after the player leaves | A gauge on the gate post reads the load on the plate, with a green band for enough. A sign over the plate shows the rule without words: a weight on the plate, an arrow, a raised gate. |
| Rows of failed couriers in recharge racks beyond the gate | The recharge hall holds six rows of cradles, with 55 dormant couriers in three slumped poses and some empty slots. |
| D-17 is ordinary equipment, not a saviour | The couriers are D-17's own model, with dark lamps, dusty paint and empty compartments. He can try to wake one. |
| His careful handling of a mundane weight shows his temperament | He squats, checks his grip, heaves twice, carries it with short, careful steps, sets it down gently and pats it once. |
| Cinematic beat: keep plate and gate together; widen only after the solution | Once the plate holds without him, the rack lights come on row by row. The camera widens over the hall for about 8 s, and D-17 stops to look. |

## 1a. The realisation (added after review)

Seeing the other couriers should feel like realising D-17 may be the last of his kind (`docs/direction.md`):
- **Roll call.** When the plate holds, the rack lights come on row by row, each with a low piano note. The camera widens and he looks.
- **He stops.** When he first walks in among the racks, he plays `Realise` (6.5 s):
  - He looks along the rows as his antenna sinks.
  - He touches his own chest window, then looks back at them, and his head goes down.
- **The swell.** The music (`kin`) builds over about 25 s to the biggest climax so far.
- **He walks slowly.** Until the far end of the hall, he can only walk with `SadWalk` (0.39 m/s), and the camera sits low at the couriers' eye level, easing slowly.

## 2. No cut between scenes

DL-01 used to end with a fade and a card. Now the bulkhead door leads straight on:

1. D-17 walks through the DL-01 door, away from the camera.
2. He turns right along a service passage behind the bulkhead wall. The wall now runs on to x 12.45 to hide him.
3. He steps back out toward the camera through a second doorway into the weighing room.
4. Control returns as he turns to face along the lane.

The camera trucks with him the whole way, from the hall's framing to the room's, and nothing fades. The far scene's lights switch over while he is behind the wall, so only one scene's lights cost anything at a time.

DL-03 runs on the same way through DL-04 and DL-05 (the Ration Hall) to the scanner corridor (DL-06). The single end card is at the end of the last built scene.

## 3. Layout (metres along the lane)

```
x: 12.1   12.6     13.2        14.55          15.8-16.55    17.6                       25.6  26.9
   | end  | weight | doorway   | trolley      | PLATE       | GATE |  recharge hall: 6 rows of racks  | exit -> DL-05
   | wall | + stand| (passage) | (push bar on |             | +gauge                                |
   |      |        |           |  its left)   |             |      |  near row: the courier he nudges  |
```

**Loads (fraction of what fully opens the gate):**

| On the plate | Load | Gate |
|---|---|---|
| D-17 | 1.0 | Full open (1.2 m) |
| The weight | 0.42 | 0.5 m, too low even crouched |
| The trolley | 0.30 | 0.36 m |
| The weight on the trolley | 0.72 | 0.86 m, enough to walk under (green on the gauge) |

**Rules:**
- The gate rises slowly with a ratchet and drops fast. It never comes down onto D-17.
- The trolley can't be pushed past the gate.
- The trolley stops against the weight if it's left on the floor.

## 4. Verbs

All of these use Use. Holding something slows him and stops him running and jumping.

| Verb | Rules | What you see |
|---|---|---|
| Lift | Next to the weight on the floor | `Lift`, 40 frames: squat, both claws on the bail, check, a false start, then up |
| Carry | Carrying the weight | `CarryWalk` / `CarryIdle` at 0.42 m/s; Jump does nothing |
| Set down | Use while carrying | `SetDownHigh` onto the deck if the trolley is in front of him, otherwise `SetDown` onto clear floor, then a pat |
| Grab | At either end of the trolley | `Grab`, then `PushIdle` |
| Push / pull | Holding the trolley | `PushWalk` (played backwards to pull), at 0.55 m/s, or 0.42 m/s loaded |
| Let go | Use or Jump while holding the trolley | |
| Nudge | Optional, at the near-row courier | `Nudge`, 84 frames: he steps in and taps its shoulder twice. Nothing. His head goes down. |

**Climbing over the loaded trolley:** the deck and the weight climb as one ledge, so he uses the authored mantle onto the weight.

## 5. Hints

D-17's curiosity again, as in DL-01:
- the plate, then the weight once he has seen the gate drop
- the trolley while carrying, then the push bar
- the gate once it holds
- the near courier in the hall

The optional key glyph follows the same targets.

## 6. Music

- **`threshold`** plays as the bulkhead opens and carries him through the passage.
- **`racks`** plays at the solution. A low piano note sounds as each row of lights comes on, then a slow chorale on phrase B. The music box ends it with the parcel's three notes.
- **`end`** plays over the end card at the end of the last built scene.

See `art/music/README.md`.

## 7. Checkpoints

- **room**: just out of the passage, with everything reset.
- **solved**: the weight on the trolley, parked on the plate, and the gate open.

## 8. Open questions

- **The nudge.** Should the courier he nudges show any response, like a lamp flicker? The build keeps it completely dead, as the overview's "ordinary equipment" reading asks. A flicker would seed hope that later scenes would have to pay off.
- **The trolley.** Two solutions are accepted:
  - The intended one: the weight on the trolley, then the trolley on the plate.
  - The weight left on the plate, then the trolley pushed up against it. This works if both centres sit on the plate, but the plate is too small for both, so it rarely happens.
- **Courier count and density** are set for the browser. The Unity build can afford more rows and some variety in wear and parts.

## Pass 2 (built 19 October 2026)

From `docs/chapter1_pass2_plan.md`. Game x is section 3's x + 13 (`OFF2`).

- **The White's first sign:** `WeightRoomDrain`, a floor drain at the back of the lane (game 26.35, section 3's
  13.35), and `DragMarks`, wet drag marks from it across the weight room and back (game 25.7 to 28.0). Set dressing
  only: the plan's sound behind the wall is not built.
- **No hazards, curiosities or checkpoint changes.**
