# DL-06 Return to Sender: production plan

**Status:** built as a playable prototype (`game/undelivered/`), for director review
**Source:** Dead Letter 45 Scene Overview, scene 03 (16 October 2026); GDD v0.1 world history
**Sequence:** DL-05 → DL-06 → DL-07, with no cut on either side

> **Renumbered 20 October 2026 (pass 3).** Chapter 1 now has eleven scenes; this was DL-05. See *Pass 3* at
> the end.
>
> **Renumbered 18 October 2026.** Chapter 1 then had nine scenes; this was DL-03. The rework in
> `docs/chapter1_plan.md` and `docs/chapter1_build_spec.md` supersedes this plan where they differ.
**Duration target:** 2 to 3 minutes

## 1. What the scene must do

| Requirement (from the overview) | How the build meets it |
|---|---|
| A sorting scanner rejects the obsolete address and directs its carrier toward a storage chute | D-17 walks under the scanner and it sweeps him. His three chest lamps answer its three lamps, the same handshake as the DL-01 relay. Its screen reads his label (a door glyph and **114**), then refuses it: **RING C SEALED**, with a red cross and RETURN. The floor arrows light toward the chute, and a carrier rises from the dispatch hatch to take him there. |
| Stop the belt and switch the track to a manual service exit before boarding it | Carriers are hauled along the return line by a chain belt to a junction. Straight on is the chute; the points can lift to a service ramp that climbs to the gallery. The points are interlocked: while the belt runs, they won't move (a red lamp, and D-17 tugs and fails). Stop the belt with the red lever, throw the points lever (red, on a yellow stand), restart the belt, then board a carrier at the dock. |
| A visible pile of permanently undeliverable parcels explains the automated response | **Dead Letters**: a pit of decades of returned post, heaped up to the mouth of the chute, under a wall of pigeonholes and an enamel sign. Carriers keep tipping more into it. |
| Let the rejected parcels appear before the chute starts | The pit is revealed right after the refusal while everything is still. The belt and its carriers start only after D-17 has checked his label. |
| D-17 checks the label again, then moves with renewed purpose | `CheckLabel`: he looks down, taps the window twice, reads, lifts his head, antenna up, a small nod and a chirp. The music turns to the theme in F major. |
| The parcel stays secured in his chest throughout | He rides in the carrier with the parcel in his compartment. Only the returned post goes into the pit. |
| Player understanding: an invalid address ends the task → the task still deserves a physical search | The notice by the scanner says why. The residential access sign at the far end (tape across ring C) says where he is going anyway. |

## 2. The emotional beat (see `docs/direction.md`)

| Time from the refusal | What happens |
|---|---|
| 0 to 0.8 s | The refusal: a dissonant low chord, the buzzer, the screen's red cross. |
| 0 to 3.2 s (before the refusal) | **The scan.** He stands to attention (`Attention`) as the bar sweeps him, and the camera is close and low beside the arch. At the refusal he deflates. |
| 0.8 to 11.5 s | **The pit.** He walks slowly to the rail by himself (the player can steer). The camera starts behind him and cranes up and out over the heap, and the music swells to a timpani-and-cymbal peak as he reaches the rail. |
| 11.5 to 14.5 s | **The edge.** He leans over the rail and looks down (`PeekDown`), seen from high over his shoulder, while the climax falls away. |
| 14.5 to 18 s | **The label.** Near silence: a held high A and the music box finding the first bars. He checks his label in close-up. |
| From 18.4 s | **Purpose.** The theme at a walking tempo, turning for the first time to the relative major. The belt starts with a klaxon. |

DL-03 now has the same treatment. When D-17 first walks in among the couriers:
- **He stops** for `Realise`, 6.5 s:
  - He looks along the rows as his antenna sinks.
  - He touches his own chest, then looks back at them.
- **The music:** `kin` swells to the biggest climax so far.
- **Then slowly:** he walks with `SadWalk` past the racks, with the camera low at the couriers' eye level, until the far end of the hall.

## 3. Layout (metres along the lane)

```
x: 26.9 corridor  28.9 SCANNER  30.5 hatch  31.0 DOCK   32.9 STOP   34.25 POINTS   34.6 junction   36.4 pit edge
                                 |rail behind the lane (z -0.55): hatch -> dock -> junction -> tip (36.5) -> chute
                                                                     \-> points lift -> ramp -> gallery (1.6 m)
   gallery 38.85 ... landing 39.7 ... desk 42.6 ... day board 44.6 ... residential access doorway 47.5 (on into DL-08)
```

- **Carriers:**
  - A new one rises at the hatch about every 6 s while the belt runs, and waits 3.4 s at the dock with a bell.
  - Each takes the route the points are set to when it reaches the junction.
  - Chute carriers tip their parcels into the chute, where they slide and tumble onto the heap.
- **Boarding:**
  - Any carrier standing on the floor can be boarded, with Use or Jump beside it (playtest: let the player try things).
  - He hops in and rides crouched with his claws on the rim. Use or Jump again hops him out.
  - On the service ramp, a chase of green lamps shows the route; he hops out onto the gallery, and the empty carrier
    sinks back down through the return slot.
- **Failure:** ridden to the chute, the carrier tips him into the pile with the dead letters. He respawns at the
  `scanned` checkpoint, and the pit's reveal is not replayed.
- **The carriers' return:** after tipping, each carrier runs back along the return line and sinks through a return
  hatch in the sorting floor, instead of vanishing.

## 4. New models

All are procedural, in `art/dl03/build_dl03.py`:
- **Scanner:** the arch, with a housing, three lamps and a sweeping bar. The game draws its screen.
- **Return line:**
  - Rails, sleepers and a scrolling chain belt.
  - The dispatch hatch and shaft.
  - The hinged points blade.
- **Levers and board:**
  - The stop lever and the points lever on their stands.
  - The interlock lamp.
  - The route board, which the game draws.
- **Sorting carrier:** a steel tub, a flanged chassis, a lamp and a plate. The game clones it.
- **Chute, ramp and pit:**
  - The storage chute.
  - The ramp trestle over the pit edge.
  - The pit hall, with a pigeonhole wall of about 800 cubbies, most still holding letters.
- **Pit dressing:** hanging lamps and the enamel UNDELIVERABLE sign.
- **The heap:** about 1,700 parcels and 600 letters, instanced by the game on the same height function the Blender scene uses for the stamped parcels.
- **Gallery:**
  - The deck and railings, and the return slot.
  - A sorting desk left mid-shift: stamps, an ink pad, a stack of letters, a mug.
  - The stopped clock and the day board on its easel.
  - The residential access wall.

## 5. Lore

Everything here is read from the world; there are no logs.

| Where | What it says | What it means |
|---|---|---|
| Notice by the scanner | Ring C is sealed; rooms C-100 to C-160 are out of service; their post is held at Dead Letters; couriers must not attempt delivery past the seal. P.A. 311. | Room 114 is in ring C. The ring was sealed a year after the parcel was posted (P.A. 310). |
| Poster on the sorting floor | REFUGE POSTAL SERVICE: "Every parcel finds its door." | The service's old promise. D-17 is the last thing keeping it. |
| The heap and its stamps | RETURN TO SENDER · ADDRESS NOT IN SERVICE | What the system has done with every such parcel since. |
| The enamel sign | UNDELIVERABLE · HELD FOR CLAIM · DO NOT SORT | What the pit is for. (The playtest found the title on it too on the nose, so it is gone.) |
| The day board | Deliveries per day by year: 1,240 in P.A. 298, 540 in 310, then 210, 96, 41, 12, 5, 2 in 377, and nothing chalked against 378. | The community shrank to nothing. The last other resident died around P.A. 378, nine years before the game (P.A. 387). |
| The stopped clock, the desk left mid-shift | | Work ended without anyone deciding it should. |
| Residential access sign | Rings A, B and C, with tape across C. | Where he is going anyway. |

The dates are proposals that fit the GDD:
- The refuge has stood about 118 years.
- Mara was born 82 years ago, and the parcel was posted when she was six (P.A. 310).
- The last other resident died 9 years ago.

## 6. Checkpoints

- **scanned**: on the sorting floor after the label check. The belt is running and the route is set to the chute.
- **landing**: on the gallery.

## 7. Open questions

- **The ring C seal.** Does it need a physical seal in DL-08 or DL-11, or is the notice enough?
- **The day board.** Is it too explicit? It is optional to read, and the GDD's three essential conclusions don't depend on it.
- **The ride up.** It is about 7 s with no control. Allow hopping out partway, or keep it as a short breather after the beat?

## Pass 2 (built 19 October 2026)

From `docs/chapter1_pass2_plan.md`. Game x is section 3's x + 21 (`OFF3`).

- **Curiosity, the sorter's chair** (`SorterChair`, `SorterCushion`): in the scanner corridor, before the arch.
  D-17 stands at game 48.8 (section 3's 27.8) and Use plays `SitChair`: he climbs up, turns round and sits down into
  the cushion (it fits), feet swinging, and hops down. The plan put the chair in DL-07 and the stopped clock here;
  the build swaps them. A later curiosity: no light pool or glance.
- **No hazards, signs of the White or checkpoint changes.**

## Pass 3 (built 20 October 2026)

From `docs/chapter1_pass3_plan.md`. This was DL-05; the Ration Hall (DL-05) now comes before it.

- **Moved:** the stretch is 12 m further right, to make room for the Ration Hall. Game x is now section 3's x + 33
  (`OFF3`), and the game x in *Pass 2* above is 12 more: the sorter's chair at 60.8, the scanner at 61.9. The scanner
  corridor starts at 59.9, where the Ration Hall's kitchen runs into it.
- **Use without red** (`docs/direction.md`): the stop lever and the points lever are worn steel, bright where hands
  went (`HandledSteel`); the points' heel goes yellow with its stand. Section 1's "red lever" and "red, on a yellow
  stand" are no longer red.
- **Loading carriers:** while the belt is stopped, a carrier standing anywhere on the floor line can be loaded, not
  only one at the dock (see DL-07).
- **Lore** (`art/pass3/build_lore.py`), on the sorting floor:

| Where | What it says | What it means |
|---|---|---|
| Behind the belt (65.4), `LoreBarricade` | Sorting crates and planks once stacked across the floor, pulled apart and pushed to the wall | There was a barricade here, between the depot and the way up; then it came down. |
| By the pit (68.3), `LoreUpStencil` | UP IS FOR THEM, stencilled, rollered over in grey, and EVERYONE UP painted across it with an arrow | Two times: when the way up was for the upper grades, and when everyone went. |

  The game counts the sorting floor as DL-07 once the belt runs to the exit, so both are still in view during the
  Heap.
- **Checkpoints:** `scanned` is now at 63.3.

## Pass 4 (built 20 October 2026)

From `docs/chapter1_pass4_plan.md`, section 2: the same stencil marks every scene's way on, so the direction is never
in doubt. Here, RING C ↓ on the sorting floor's back wall at its end, where the carriers go up the service
ramp, under UP IS FOR THEM (`WayRingC06`, 68.72). Nothing else changed.

## Pass 5 (built 20 October 2026)

See `docs/chapter1_pass5_plan.md`.

- **EVERYONE UP** appears here (its first) and on C-106's wall in ring C only.
- **The weights into the bucket:** the wide frame keeps D-17 in shot.
- **Riding a carrier:** he no longer judders against it on the ramp (`syncRide`).
