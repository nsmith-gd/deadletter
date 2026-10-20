# DL-10 Up Only: production plan

**Status:** built as a playable prototype (`game/undelivered/`), for director review; not yet timed
**Source:** `docs/chapter1_pass3_plan.md`, sections 4 and 5 (19 October 2026)
**Sequence:** DL-09 → DL-10 → DL-11, with no cut on either side
**Duration target:** about 2:30 first time (plan estimate)

New in pass 3, between the city reveal and ring C: the ring C relocation lift lobby, the place the families left
from. Where this plan and the pass 3 plan differ, this describes the game; section 11 lists the differences.

## 1. What the scene must do

| Requirement (pass 3 plan) | How the build meets it |
|---|---|
| The block: ring C is below, and the only way down is the lift; its panel has one button, UP; the stair beside it is collapsed | The balcony's deck runs on into the lobby at the deck's height (1.6). The lift's car stands behind the lane, its call panel has one worn brass button, UP, and the old stair lies collapsed at the foot of the lift, at ring C's level. |
| Wrong assumption: press UP and ride | He presses UP: the panel buzzes, the UP lamps stutter, and the car stays. It won't leave empty. He startles the first time. |
| Make it think someone is aboard: the car's floor plate weighs passengers; carry a suitcase from the left luggage into the car; the doors close | The last suitcase from the heap of left luggage lies on the lane under a failing pendant, tagged C-114. He carries it into the car and sets it on the floor plate. The plate dips, the load needle swings over, the lattice gate draws shut, and both UP lamps glow. |
| Press UP from outside: the car goes up | Pressing the lobby's UP now sends the car up, and the counterweight comes down its shaft beside the lane, empty. After 3 s at the top the car comes back. It shows how the lift works, and that it doesn't take him. |
| Ride the counterweight down; it comes down its open shaft and stops at ring C; he must stand on its frame when UP is pressed; the service door opens with a crank | A crank on the pier winds a striped service door up out of the lane (four strokes; it stays up). Behind it, the counterweight stands at the deck with a footplate and side rails, and the shaft's far wall has its own service UP. Standing on the footplate, he presses it: the car goes up with the suitcase, and he rides the counterweight down to ring C. |
| The aha: riding the counterweight of a lift that only goes up | The car and the counterweight are roped over the same sheaves, in view, moving opposite each other. |
| He picks the C-114 suitcase as the passenger; it goes up without him, the way its family did | On the ride (`RideCounterweight`) he looks up and back at the car going away with the suitcase, then down at ring C coming. |

## 2. Beats

| Beat | Time (approx.) | What happens |
|---|---|---|
| **The lobby** | 0:00 | Off the balcony's porch into the lobby. Checkpoint. The framing widens and rises: the luggage, the queue line, the car, the crank, the counterweight's shaft and the ropes over them all. |
| **UP** | 0:20 | He walks the queue line to the panel and presses UP (`PressButtonHigh`). It buzzes; the car stays. `Startle`. |
| **The suitcase** | 0:45 | Back to the luggage, under the failing pendant: the C-114 suitcase. He lifts it (`Lift`) and carries it to the car. |
| **A passenger** | 1:10 | He steps into the car's doorway and sets it on the plate (`SetDown`). The needle swings, the gate creaks shut and slams, the UP lamps glow. |
| **The demonstration** | 1:25 | He presses UP again: the car goes up, the counterweight comes down its shaft, empty. The car comes back. |
| **The crank** | 1:55 | He winds the service door up (`Crank`, four strokes). Behind it, the counterweight at the deck, and its UP. |
| **Down** | 2:15 | On the footplate, he presses its UP. The car goes up with the suitcase; he rides down (`RideCounterweight`), looking up at it, then down at ring C. On along the bottom landing to ring C's ledge (DL-11). |

## 3. Layout (game x in metres; the deck is at 1.6, ring C's level at 0)

```
x: 116.6-118.8 porch (the balcony's deck carried on)   118.8 LOBBY entrance
   119.05-120.95 the left luggage (against the back wall)   121.3 SUITCASE C-114 (on the lane, under the pendant)
   119.3-124.4 the painted queue line, with what was dropped along it; the bench, the departures board
   123.55-126.85 the lift's front wall:  123.95 UP (left of the gate)   124.35-125.55 LIFT CAR (behind the lane)
                                         126.45 SERVICE CRANK (on the pier, a work lamp over it)
   126.76 SERVICE DOOR (across the lane)   126.85-127.75 COUNTERWEIGHT SHAFT (stand at 127.37; its UP on the far wall)
   127.75-130.8 ring C's bottom landing (at 0; the collapsed stair against its back wall)   127.9 DL-11 begins
```

| State | Car | Counterweight |
|---|---|---|
| Empty, UP pressed | Stays; the panel buzzes | Stays |
| Suitcase on the plate | Gate shuts (after 0.8 s, over 1.4 s); UP lamps glow | Stays |
| Loaded, the lobby's UP | Up 1.6 in 5.5 s; 3 s at the top; back down in 5.5 s | Down 1.6 and back, empty |
| Loaded, the counterweight's UP, D-17 on its footplate | Up 1.6 with the suitcase, and stays | Down 1.6 to ring C with D-17 |

**Rules:**
- **The suitcase:** Use to lift it; he carries it slowly and can't jump. Use within the car's doorway (124.1 to 125.8)
  while the car is at the deck: he steps into the doorway (0.5 behind the lane), sets it on the plate and steps back
  out. Elsewhere, Use sets it down (setting down never refuses).
- **UP:** Use within 0.22 of 123.95 while the car is at rest. He turns to the wall and presses. The car goes only with
  the suitcase aboard and its gate shut; otherwise it buzzes.
- **The crank:** Use within 0.25 of 126.45. He turns his back to the camera and winds, as DL-01's bulkhead: each
  stroke lifts the door a quarter of its 1.45. It stays where it is left; after four it is fully up and stays up. A
  move lets go.
- **The edges:** the service door blocks the lane until it is fully up. While the counterweight is down, the open
  shaft stops him at its edge. At deck level the shaft's far wall stops him.
- **The counterweight's UP:** Use while standing on its footplate (126.95 to 127.75), with the car at rest at the
  deck. The same rule as the lobby's: it goes only with the suitcase aboard.
- **The ride:** about 5.5 s, with no control. At the bottom he stands at ring C's level and walks on.
- **No way back:** the car stays up, and the counterweight stays down.
- **Nothing kills here.**

## 4. Verbs

| Verb | Rules | What you see |
|---|---|---|
| Lift, carry, set down | As DL-02's box | `Lift`, `CarryWalk`, `SetDown` |
| Load the car | Use in its doorway, carrying the suitcase | A step into the doorway, `SetDown` onto the plate, a step back out |
| Press UP | Use at either panel | He turns to the wall; `PressButtonHigh` (36 frames, the push at frame 16) |
| Wind | Use at the crank; four strokes | `Crank` |
| Ride | Automatic once the counterweight goes | `RideCounterweight` (96 frames): he crouches and takes a rail in each claw; looks up and back over his left shoulder at the car going (frames 16 to 58), then down at ring C (64 to 90) |

## 5. Models (`art/pass3/build_up_only.py`)

Built in final world x, after the scene gap is opened (`insert_scenes()` in `art/dl01/build_dl01.py`).

- **The porch:** the balcony's deck carried on where the balcony stair used to go down.
- **The lobby:** its walls and ceiling (4.9), the failing pendant (`LobbyBulb`), the heap of left luggage, and
  `Suitcase114` with its swinging tag (`Suitcase114Tag`, C-114 in a parent's hand). The painted queue line with what
  was dropped along it: a suitcase burst open, a child's shoe, a doll, an empty birdcage. A bench; the departures
  board.
- **The lift:** the lattice gate (`LiftDoorL`, `LiftDoorR`) under the sign; the car (`LiftCar`) with its lamp, its
  floor a weighing plate (`LiftFloorPlate`) and a load gauge (`LiftLoadNeedle`); the call panel with one worn brass
  button (`LiftPanel`, `LiftUpButton`, `LiftUpLamp`).
- **The service door:** `ServiceDoor`, striped, in the lane; `ServiceCrank` on the pier and its chain; the work lamp
  (`CrankLamp`).
- **The counterweight:** `Counterweight`, with its footplate and side rails, in its open shaft; roped to the car over
  two sheaves on the head frame (`LiftSheave`, `LiftSheaveIdler`, `LiftRopeCar`, `LiftRopeCW`); the service panel on
  the far wall (`ServicePanel`, `ServiceUpButton`, `ServiceUpLamp`).
- **Ring C's bottom landing:** at the shaft's foot, and against its back wall the stair that came down from the
  lobby's level, collapsed: its head, a torn stub, the fallen flight on its rubble.
- **Clips:** `PressButtonHigh`, `RideCounterweight`.

## 6. Lore

| Where | What it says | What it means |
|---|---|---|
| Over the gate | RELOCATION — GRADES 1–2 ONLY, with EVERYONE painted across the grades | The lift was for the upper grades; then everyone took it. |
| The departures board | DEPARTURES RING C: family numbers with their dates, each ticked; C-114 last; LAST CAR · UP 19.00 | Ring C left family by family. Mara's family was the last. |
| The left luggage | A heap against the wall; the last suitcase, tagged C-114, slid off onto the lane | They left with less than they packed. The tag is the parcel's address. |
| Along the queue line | A burst suitcase, a child's shoe, a doll, an empty birdcage | A crowd, in a hurry. |
| The panel | One button: UP | The lift was built to take people away. |
| The collapsed stair | | Nobody was meant to come back down. |

## 7. Camera and light

- **The framing:** from about 118.0 it widens and rises to hold the luggage, the car, the crank, the counterweight's
  shaft and the ropes over them, following him between 122.2 and 125.6. On the ride it follows him down the shaft
  and closes in at ring C's level.
- **Light:** the lobby has its own light zone (`lightZoneFor`): from about 117.8 its lights replace the goods hall's
  and the cage's. The failing pendant over the luggage (it flickers; steady in calm mode), its pool on the suitcase;
  the two UP lamps (a dull glow, a stutter when the panel buzzes, a steady pulse when the car will go); the crank's
  work lamp; the car's lamp, which rides with the car; and cold light falling down the counterweight's shaft from far
  above.
- **Shots:** none. The ride plays in the side view.

## 8. Sound and music

- **No new cue.** The bed stopped in the tunnel; `refuge`, from the balcony, plays out.
- The panel's click and buzz; the gate's creak and slam; a clunk and the chain as the car goes, squeaks while it
  moves, a clunk at each end; a ratchet and the door's rumble on each stroke of the crank.

## 9. Checkpoints

- **tunnel**: DL-09's, inside the tunnel mouth (107.7).
- **uponly**: on the deck just inside the lobby (119.4). The suitcase is on the lane, the car empty at the deck, the
  service door down.
- **ringc**: DL-11's, through ring C's barricade (135.25).

## 10. Scene card (`docs/puzzle_principles.md`)

| Rule | This scene |
|---|---|
| Arc step | Substitution: twist (a suitcase is the passenger, and he takes the counterweight's place). Carry: apply. |
| Builds on | DL-03's plate that reads a load; DL-09's counterweight, now ridden; DL-01's crank. New: riding the other end of a lift. |
| Wrong assumption | Press UP and ride: it won't go empty. Then: load it and press UP from the lobby: it goes, and comes back without him. |
| Checkpoints | `uponly` before, `ringc` after. No failure state. |
| Linkage | Car, ropes over the sheaves, counterweight: one run in view, moving opposite. Crank, chain, service door. |
| Gear | Puzzle (develop), after the chapter's one wide shot. |
| Curiosity | None. |
| Tableau | The queue line and what was dropped on it, the left luggage, the sign with EVERYONE painted across it. |
| Emotional shot | None. On the ride he watches the suitcase go up as he goes down. |

## 11. Where the build differs from the plan

- **Two UP buttons.** The plan had one UP, pressed from outside while he stood on the counterweight. In the build the
  lobby's UP is a demonstration: with the suitcase aboard it sends the car up and back, and shows the counterweight
  coming down. The solving press is the counterweight's own service UP on the shaft's far wall, pressed from its
  footplate.
- **The doors** are a lattice gate that draws shut once the plate feels a passenger.
- **The stair:** the balcony's old stair down to ring C is removed; it is the collapsed stair beside the lift.
- **The dropped belongings** include a burst suitcase.

## 12. Open questions

- **The demonstration.** Does the car going up and coming back read as "it works, but not with me on it", or as a
  dead end?
- **The second panel.** Is the counterweight's UP found once the service door is up, or does it need its lamp in the
  frame sooner?
- **The ride.** About 5.5 s without control. Right as a breather before ring C?
- **The suitcase.** Never seen to arrive. Keep it that way (the answer stays at the edges: up)?
- **Hints.** No idle look is authored yet for the suitcase, the crank or the counterweight.
