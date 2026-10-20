# DL-04 The Racks: production plan

**Status:** built as a playable prototype (`game/undelivered/`), for director review; not yet timed
**Source:** `docs/chapter1_plan.md`, scene 4 and decision 2; `docs/chapter1_build_spec.md`, section 4 (18 October 2026)
**Sequence:** DL-03 → DL-04 → DL-05, with no cut on either side
**Duration target:** about 2:30 first time, 0:45 floor (`docs/chapter1_plan.md`)

New in the Chapter 1 rework. Where this plan and the build spec differ, this describes the game; section 10 lists
the differences.

## 1. What the scene must do

| Requirement (plan and overview) | How the build meets it |
|---|---|
| The realisation plays among the dormant couriers | Unchanged from DL-03's build (`DL-03_the_weight_of_the_job.md`, section 1a): `Realise`, `kin`, and the slow walk at the couriers' eye level. The game counts the hall beyond DL-03's gate as this scene. |
| The exit is a charging bay door whose plate carries a courier pictogram | At the end of the racks, a charging bay: a steel floor plate with a seated-courier pictogram, a cradle frame behind it, and a shutter in the hall's end wall with three lamps over it. The same pictogram is on the bay's backboard. |
| He alone opens it, until he steps off | Standing on the plate, the bay reads him: its three lamps light, the plate sinks a centimetre and the door lifts. Stepping off drops it in half a second. The door is 1.3 m from the plate's edge, too far to reach before it shuts, even running. |
| Wrong assumption: fetch the trolley | The trolley is holding DL-03's gate open behind him, and it can't be pushed past the gate. Nothing he has carried so far can reach the bay. |
| The answer is one of his own | A courier lies fallen from its rack beside the lane, a red tow loop on its harness at its head end. He takes the loop and drags it, walking backwards, slowly, 3.3 m onto the plate. |
| The bay charges it; its lamps flicker weakly, then hold | The cradle's arms close on it where it lies and lift it into a seated charging pose. Its chest lamps flicker for about 2 s, faint and uneven, then hold steady at a low glow. The bay's lamps stay lit and the door lifts. |
| He leaves it there | He walks up to it once, lays his claw on its head (`TouchHead`), and lets go. The door stays open behind him. The empty outline it left in the dust stays on the floor where it lay. |

## 2. Beats

| Beat | Time (approx.) | What happens |
|---|---|---|
| **The realisation** | 0:00 | As DL-03's build: he stops among the racks, then walks slowly to the end of the hall. |
| **The bay** | 0:40 | The racks end; the bay is lit cold and clinical. The camera holds the fallen courier, the plate and the door in one frame. |
| **The plate** | 0:55 | He steps on: three lamps, the door lifts. He steps off toward it: it drops. As in DL-03, but it reads *him*. |
| **Looking for a weight** | 1:15 | Back toward the gate and the trolley, perhaps. There is nothing to carry here. |
| **The fallen courier** | 1:35 | He grabs its tow loop (`Grab`, then `PushIdle`). He drags it at 0.22 m/s with a scrape (`PushWalk`, played backwards), looking at it all the way. |
| **The cradle** | 2:00 | At the plate he lets go by himself. The arms close and lift it; its lamps flicker and hold; the door lifts over about 2 s. |
| **Goodbye** | 2:10 | `TouchHead`, 52 frames, played once. He walks on through the door into the service passage. |

## 3. Layout (game x in metres)

```
x: 30.6 DL-03's gate   32.1 Realise   36.6 slow walk ends   40.1 art/dl02's hall ends   41.1 empty slot, chalk flowers
   41.2 FALLEN COURIER (40.8-41.6, 0.35 behind the lane; tow loop at its head end, 41.55, 0.44 high)   41.87 where he grips it
   43.1 racks end   44.0-45.0 BAY PLATE   44.5 cradle   46.3-46.7 BAY DOOR   46.7-47.9 service passage   47.9 the Ration Hall (DL-05)
```

**The bay door:**

| On the plate | Door |
|---|---|
| Nothing | Shut (blocks him while it is under about half open) |
| D-17 | Lifts 1.7 m in 1.1 s; drops in 0.5 s when he steps off |
| The courier, seated in the cradle | Lifts in 2.2 s and stays open |

**Rules:**
- **The drag:** he steps in to the courier's line (0.35 behind the lane) to take the loop, and back out to the lane
  after letting go. He can let go anywhere (Use or Jump) and take it up again.
- **The end of travel:** it stops on the plate's centre, where he lets go.
- **The plate** ignores everything except D-17 and a courier.

## 4. Models (`art/racks/build_racks.py`)

- **The hall continued:** the back wall, columns and beams on from `art/dl02`'s racks hall to the end wall, the
  floor on to the sorting floor, and art/dl02's old end wall cut out so the join can't be seen.
- **The last bays:** five rows and the near row, every slot empty, with tags; row tubes that light with the hall's;
  the near row's slot at 41.1 mounted on a column, with flowers chalked above it.
- **The couriers:** a spare D-17 rig, posed and baked twice:
  - `FallenCourier`, lying on its left side, head toward the bay, with its harness and red tow loop, and
    `FallenLamps`;
  - `SeatedCourier`, in the cradle, with `SeatedLamps`, hidden until used.
- **`FallenDust`:** years of dust round where it lies, with its clean outline under it.
- **The bay:** `BayPlate` and its rim; the enamel back frame with a cold strip light and the pictogram sign;
  `CradleArmL` and `CradleArmR`, each pivoting on its shoulder; `BayDoor` in its frame, the door motor and
  `BayLamp0..2`; a yellow hazard edge along the lane's front.
- **Linkage:** a cable from the plate to a junction box at the frame's foot, a conduit up the frame to the arms'
  motors, another along the floor behind the lane to the door post and up to its motor, joined across the header.
- **The service passage:** the scanner corridor's section, so the two run together.
- **Clip:** `TouchHead`, 52 frames.

## 5. Lore

| Where | What it says | What it means |
|---|---|---|
| The empty slot on the column | Chalk flowers in a scribbled jar, petals fallen at its foot, a small heart | Someone mourned a courier here. |
| The bay's pictogram | A courier seated in the cradle, three lamps over it, a charge bolt | What the bay is for, without words. |
| The fallen courier | Lying where it fell from its rack, deep in dust | Nobody came for it. |
| The flicker | | It might wake, or it might not. The game never says. |

## 6. Camera and light

- **The racks:** as DL-03's build, low at the couriers' eye level until x 36.6.
- **The bay:** from about x 38.4 the framing eases to hold the fallen courier, the plate and the door together. It
  follows him between x 41.6 and 44.9 and is a little closer than the hall's.
- **Light:** a cold light over the bay (x 44.5); the fallen courier lies in a pool of the racks' light.
- **Shots:** none. The realisation is this stretch's shot; the flicker plays in the side view.

## 7. Sound and music

- No new cue: `kin`, from the realisation, is this stretch's music.
- The drag is a low scrape that follows his speed. The cradle has a servo whine and a clunk as it seats the courier.

## 8. Checkpoints

- **solved**: DL-03's, in the weight room by the gate. Nothing in this scene can fail.
- **bay**: just through the door (x 47.1), with the courier seated and the door open.

## 9. Scene card (`docs/puzzle_principles.md`)

| Rule | This scene |
|---|---|
| Arc step | Substitution: develop and twist (the bay wants a courier, not a weight). Carry: twist (he moves one of his own). |
| Builds on | DL-03's plate and gate. New: the bay reads what stands on it. |
| Wrong assumption | Fetch the trolley, or any weight. Neither can get here, and the bay wouldn't take them. |
| Checkpoints | `solved` before, `bay` after. There is no failure state. |
| Linkage | The plate's cable and conduits run to the arms' motors and the door's motor, joined over the header. |
| Gear | Puzzle (develop), after the realisation's emotional beat. |
| Curiosity | The chalk flowers over the empty slot. |
| Tableau | The fallen courier in its dust; after the drag, its clean outline on the floor. |
| Emotional shot | None. `TouchHead` and the flicker play in the side view. |

## 10. Where the build differs from the spec

- **Positions:** the plate is at 44.0 to 45.0 (spec 44.4 to 45.4), the cradle at 44.5 (spec 44.9) and the door at
  46.3 to 46.7 (spec 45.6 to 46.0).
- **Drag, not push:** the tow loop is at the courier's head end, toward the bay, and he drags it backwards from its
  right. The spec put the loop at its left end (40.85), to push it.
- **The dust outline** is not hidden and shown by the game: it lies under the courier, so it appears as he drags it
  away.

## 11. Open questions

- **The flicker.** It is weak and settles low. Does that seed a hope that later scenes must pay off (DL-03's own
  open question about the nudge)?
- **The drag.** At 0.22 m/s, 3.3 m takes about 15 s. Right for the weight of the moment, or too long to repeat?
- **The touch.** `TouchHead` plays by itself, once. Should it be the player's choice, as the nudge is in DL-03?

## Pass 2 (built 19 October 2026)

From `docs/chapter1_pass2_plan.md`. Positions are game x.

- **The White's second sign:** the fallen courier (`FallenCourier`, and `SeatedCourier` once it is in the cradle) has
  lost its right leg below the knee: a bitten stump with torn cable ends, not a cut.
- **Curiosity, the empty rack** (`RackSeat`, a low seat in the empty slot under the chalk flowers): D-17 stands at
  41.08 and Use plays `SitRack` (about 6 s). He backs into the slot, sits with his legs dangling, looks round, his
  antenna droops; a stillness, then he hops down. It is offered only once the courier is seated in the cradle, so it
  is found by walking back from the bay. A later curiosity: no light pool or glance.
- **No hazards or checkpoint changes.**

## Pass 3 (built 20 October 2026)

From `docs/chapter1_pass3_plan.md`. Positions are game x.

- **Fix, the bay draws the courier in:** the director found it hard to land the courier on the plate. Now, once the
  courier is within 0.6 m of the cradle (past 43.9), D-17 lets go by himself, the cradle's arms swing out and draw it
  in over about 1.2 s, then close on it and seat it as before. It no longer has to be placed exactly.
- **Use without red** (`docs/direction.md`): the fallen courier's tow loop is worn webbing (`WornStrap`).
- **Lore** (`art/pass3/build_lore.py`): `LoreMemorial`, couriers' tags hung on a wire over the empty rack with the
  chalk flowers (41.1). Someone kept the tags of the couriers that stopped.
- **The way on:** the service passage beyond the bay door now opens into DL-05 The Ration Hall at 47.9, not the
  scanner corridor (which is now at 59.9, in DL-06).
- **Checkpoints:** unchanged (`bay`, 47.1). The next, `ration`, is just inside the Ration Hall.
