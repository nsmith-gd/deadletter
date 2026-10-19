# DL-06 The Heap: production plan

**Status:** built as a playable prototype (`game/undelivered/`), for director review; not yet timed
**Source:** `docs/chapter1_plan.md`, scene 6; `docs/chapter1_build_spec.md`, sections 2 and 5 (18 October 2026)
**Sequence:** DL-05 → DL-06 → DL-07, with no cut on either side
**Duration target:** about 2:30 first time, 1:00 floor (`docs/chapter1_plan.md`)

New in the Chapter 1 rework, in the gallery end of DL-05's space. Where this plan and the build spec differ, this
describes the game; section 11 lists the differences.

## 1. What the scene must do

| Requirement (plan and overview) | How the build meets it |
|---|---|
| The ride up the ramp ends short of the gallery's way on | DL-05's ride still ends at the landing, but a counterweighted shutter now closes the gallery 2.2 m further on. Its chain runs up to a stepped drum in the roof, and from the drum's small hub, over a sheave, down to a steel bucket hanging at the ramp's head. |
| Wrong assumption: ride up with nothing | It half works: he reaches the landing and the gate is down. A parcel slide at the gallery's left end takes him back down to the sorting floor, sitting, in about 2 s. |
| Send a delivery: carry a sorting weight into an empty carrier, route it up, watch it tip into the bucket | Two sorting weights stand on the lane beside the dock, the same red-bailed casting as DL-03's. He lifts one, carries it to the dock and sets it into the waiting carrier. With the points set to the ramp, the carrier climbs, stops at the landing, tips toward the bucket and drops the weight in with a clank. The bucket sinks 0.4 and the gate ratchets up 1.4. |
| Then ride the next carrier up | He boards the next one and hops off at the landing. The gate is open. |
| Combine carry, routing and substitution | Carry from DL-02 and DL-03, routing from DL-05, and substitution twisted: the system delivers the weight for him. |
| The chapter's secret letter | Caught by twine on the gallery's front rail beyond the gate, in a shaft of light. It falls to the deck as he walks under it. He posts it at MailSlot6, by the old sorting desk. |

## 2. Beats

| Beat | Time (approx.) | What happens |
|---|---|---|
| **Up, for nothing** | 0:00 | From DL-05: he rides up and hops out at the landing (`BrushOff`). Ahead, the gate is down; the bucket hangs empty by the ramp's head, its chain running up to the drum and across to the gate. |
| **Back down** | 0:20 | He walks off the gallery's left end and sits into the slide (`Slide`), along the front of the ramp, the chute and the pit, to the sorting floor. |
| **The weight** | 0:40 | Beside the dock, the two sorting weights. He lifts one (`Lift`) and carries it to the dock. |
| **Loading** | 1:00 | A carrier waits at the dock with its bell. He turns to the rail and sets the weight in (`SetDownHigh`). |
| **The delivery** | 1:15 | The camera widens and slides right to watch the loaded carrier climb the ramp. At the landing it tips; the weight drops into the bucket (a clank, a thud, a small shake); the drum turns and the gate ratchets up. |
| **Up again** | 1:45 | He boards the next carrier and rides up. Past the gate: checkpoint. |
| **The letter** | 2:00 | Optional. Under the lit letter on the rail it falls at his feet; he picks it up and posts it at MailSlot6. Then on past the day board to the residential access doorway (DL-07). |

## 3. Layout (game x in metres; the sorting floor is at 0, the gallery deck at 1.6)

```
sorting floor:  49.9 SCANNER   51.5 hatch   52.0 DOCK   52.6, 52.85 SORTING WEIGHTS   53.9 STOP lever   55.25 POINTS lever
                55.6 junction   56.7 slide lip   57.4 pit edge   57.5 tip -> chute -> the heap
gallery:        59.5 ramp top   59.85 slide head (gallery's left end)   60.0 BUCKET (behind, rim 1.2)   60.7 landing
                61.7 clock   62.3 return slot   62.7 drum (roof, z 5.0)   62.9 GATE   63.6 old sorting desk
                64.4 LETTER on the front rail   65.2 MAILSLOT6   66.3 day board   68.5 residential access doorway (DL-07)
```

**The sorting weights sit beside the dock, between the scanner and the levers**, on the lane. On the floor each is a
0.22 obstacle that he hops over. A jump with no direction held beside a carrier boards it (a standing jump), while a
jump on the move is just a jump (a running jump), so hopping over the weights never boards a carrier by accident.

| In the bucket | Gate |
|---|---|
| Nothing | Down (it blocks him while under 0.8) |
| One weight | Rises 1.4 at 0.45 m/s, about 3 s, and stays up; the bucket sinks 0.4 |

**Rules:**
- **The drum:** the gate's chain winds on its big wheel while the bucket's pays off its small hub: 1.4 of gate for
  0.4 of bucket. Both turn as the gate rises.
- **Loading:** Use with a weight in his hands, within 0.7 of the dock while a carrier waits there. He walks to the
  dock, turns to the rail and sets it in. With no carrier waiting, Use just sets it down on the floor.
- **A weight sent to the chute** tips down it with the post. Another stands in its place by the dock 4 s later.
- **A loaded carrier he rides himself** also works: he hops out at the landing, and it tips the weight about a second later.
- **The slide:** at the gallery's left end, walking left sits him into it. It runs along the lane's front edge.

## 4. Verbs

| Verb | Rules | What you see |
|---|---|---|
| Lift, carry | As DL-03's weight | `Lift`, `CarryWalk` at 0.42 m/s |
| Load | Use at the dock, carrying, with a carrier waiting | He turns to the rail; `SetDownHigh` into the tub |
| Board | Use, or a standing jump, beside a carrier on the floor | `Hop`, then `Ride` |
| Hop out | Use or Jump while riding on the floor; automatic at the landing | `Hop`; `BrushOff` on the gallery |
| Slide | Walk left off the gallery's left end | `Slide`, seated, claws out for balance; `Land` at the bottom |
| Pick up, post | As DL-02 | `PickUpLetter`, `PostLetter` |

## 5. Models (`art/dl03/build_dl03.py`, `build_heap`)

- **`GalleryGate`:** a ribbed shutter with a yellow bottom bar in two channels, with its frame, hangers and the
  chain's guide tube. Its chain rises with it.
- **The hoist:** a roof beam, `GatePulley` (the stepped drum), `GateSheave` over the bucket in its block, and the run
  of chain between them.
- **`GateBucket`:** a steel hopper on a bail with a yellow rim and stiffening bands, its chain, and a tipping spout
  from the deck's back edge down over it.
- **`HeapWeight0`, `HeapWeight1`:** red, with a paper band, not quite lined up.
- **`ReturnSlide`:** steel, flat at the head, a 40-degree run, a long bend into the run-out and a rounded lip; legs
  down into the pit.
- **`HeapLetter`** on its twine, `HeapLightShaft`, and **`MailSlot6`** with its pictogram plate and `SlotLamp6`.
- **The gallery:** its rails now open at the slide's head and over the bucket; the clock and the day board moved to
  make room.
- **Clip:** `Slide`, 24 frames, looping.

## 6. Lore

| Where | What it says | What it means |
|---|---|---|
| The letter's front | Addressed to C-114, postmarked R.Y. 43, a heart pictogram | Post for the same room as his parcel, sent after the seal. |
| The letter's back | In wax crayon: a little courier carrying a parcel to a house under a big sun, a child waving at the window, a row of hearts | A child drew a courier like him delivering to her. |
| MailSlot6's plate | An envelope going into a slot, and a stamp | How to post, without words. |
| The heap below, the desk, the clock, the day board | As DL-05 | The service ran down, and the post kept coming. |

## 7. Camera and light

- **The floor:** as DL-05's. When a loaded carrier is on the ramp route, the framing widens and slides right (to
  about x 57.4) so the climb, the bucket and the tip are in one side-on frame.
- **The gallery:** it follows him between x 61.2 and 66.4, with the bucket, drum, chain and gate in frame.
- **Light:** the gallery's two bulbs; a soft shaft of light over the letter.
- **Shots:** none.

## 8. Sound and music

- DL-05's bed plays on; nothing new is cued.
- The tip into the bucket is a clank, then a thud. The gate ticks as it ratchets up. The slide scrapes.

## 9. Checkpoints

- **scanned**: DL-05's, on the sorting floor (x 51.3), the belt running.
- **landing**: on the gallery when he hops out (x 61.0), the route set to the ramp. The gate is down, the weights are
  by the dock, and the slide takes him back down.
- **gallery**: past the gate (x 63.3), with the weight in the bucket.

## 10. Scene card (`docs/puzzle_principles.md`)

| Rule | This scene |
|---|---|
| Arc step | Routing: develop (send a load where he can't go). Substitution: twist (the system delivers the weight). Carry: combine. |
| Builds on | DL-05's routing and boarding, DL-03's weight. New: a carrier can carry something other than him. |
| Wrong assumption | Ride up with nothing. It reaches the landing; the gate stays down. |
| Checkpoints | `landing` after riding up, `gallery` after the gate. A wrong route costs a weight for 4 s, not a life. |
| Linkage | Gate, chain, drum, hub, chain, sheave, bucket: one visible run, all moving together. |
| Gear | Puzzle (combine), after DL-05's routing puzzle; the letter is the curiosity after it. |
| Curiosity | The letter on the rail, and MailSlot6. |
| Tableau | The old sorting desk left mid-shift beside the slot, over the heap of dead letters. |
| Emotional shot | None. |

## 11. Where the build differs from the plan and spec

- **The letter** is on the gallery's rail past the gate, as the spec says, not down on the heap as the plan
  proposed. It falls when he walks under it rather than when he bumps the rail.
- **The sorter's chair** (the plan's curiosity, a cushion worn into D-17's shape) is not built.
- **Riding a loaded carrier** is accepted as well as sending it alone.
- **Scene label:** the game names this scene from the moment the belt runs to the exit (DL-05 solved), so the loading
  on the sorting floor counts as DL-06.

## 12. Open questions

- **Two puzzles in a row.** DL-05's routing and this one share a room and a camera. Does the slide down read as a
  new beat, or should something new (the chair, a sound from the heap) sit between them?
- **Two weights.** One is enough, and a lost one comes back. Is the second one needed?
- **The letter's sender.** C-114 in R.Y. 43, with a courier drawn on the back: who sent it is left open. Is that the
  right amount of mystery for the chapter's major secret?
