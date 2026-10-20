# DL-05 The Ration Hall: production plan

**Status:** built as a playable prototype (`game/undelivered/`), for director review; not yet timed
**Source:** `docs/chapter1_pass3_plan.md`, sections 4 and 5 (19 October 2026)
**Sequence:** DL-04 → DL-05 → DL-06, with no cut on either side
**Duration target:** about 2:30 first time (plan estimate)

New in pass 3, between the Racks and Return to Sender. Where this plan and the pass 3 plan differ, this describes the
game; section 11 lists the differences.

> **Pass 4 (20 October 2026):** the winch puzzle in sections 1 to 4 is gone. The hatch is now a weigh-in, and the hall
> is where the lower grades starved. *Pass 4* at the end supersedes sections 1 to 5, 9 and 10 where they differ.

## 1. What the scene must do

| Requirement (pass 3 plan) | How the build meets it |
|---|---|
| The depot workers' canteen and ration counter, the dregs of the refuge at its end; families slept here when ring C flooded | Through the Racks' service passage, a canteen with tables and cots between them, bedrolls, queue barriers folded into a maze, a shrine, and a ration counter behind the lane. The way on is through the kitchen beyond it. |
| The block: the way on is through the serving hatch, whose steel shutter drops the moment the winch is let go | The hatch in the kitchen wall is closed by a steel shutter. A handwheel winch at the counter's left end winds it up: four strokes to 1.2 m. He holds it at the top; any move, Use or Jump lets go, and it falls at once. |
| Wrong assumption: wind it up and run under | It slams shut before he can take a step: a crash, a clank, a hard shake, and he startles. It's loud, not lethal, and he can wind it again. |
| The answer: something under the shutter's line, wind, let go | An olive ration drum stands on a floor guide by the counter. He pushes it along the guide until it stops against the shutter, its rim under the shutter's lip. He winds, lets go, and the shutter slams onto the drum's chime and holds at 0.64. He crouches under it by himself. |
| The prop in plain sight, and a sign it's been done before | The drum stands in the counter's light, on its guide. The shutter's lip has a drum-shaped dent where chimes have bitten it, and the floor under it a rust ring. |
| The tableau: rationing, cots, the grade notice, the shrine, the child's drawing of D-17 and Mara | All built (section 6). The crayon drawing is taped beside the winch, so the player looks at it while winding. |

## 2. Beats

| Beat | Time (approx.) | What happens |
|---|---|---|
| **In** | 0:00 | Out of the Racks' passage into the canteen. Checkpoint. The framing holds the shrine, the cots and the queue maze. |
| **The hall** | 0:15 | He walks past the shrine's candles, the bedrolls and the painted sky. The framing slides on to the counter. |
| **The hatch** | 0:40 | The counter, the winch, the drum and the shut hatch, in one frame under the counter's flickering strip light. |
| **Wind and go** | 1:00 | He winds the shutter up (`Crank`, four strokes), then moves to go under: it drops and slams. `Startle`. |
| **The drum** | 1:30 | He takes hold of the drum and pushes it along its guide until it stops against the shutter, with a thud. |
| **Wind and let go** | 1:55 | He winds again and lets go. The shutter slams onto the drum's rim and holds, a crawl-height gap under it. |
| **Under** | 2:10 | He crouches under the shutter into the kitchen. Checkpoint. On through the kitchen to the scanner corridor (DL-06). |

## 3. Layout (game x in metres; the floor is at 0)

```
x: 47.9-48.1 end wall and doorway (from the Racks' service passage)   48.1-53.2 THE CANTEEN
   49.65 shrine (on the first column)   50.1-52.6 queue barriers, folded into a maze behind the lane
   52.85 second column: the grade notice and tally marks   tables with cots between them; the painted sky on the back wall
   53.2-56.6 RATION COUNTER (behind the lane)   53.55 WINCH (handwheel; the crayon drawing beside it)
   54.25 the drum's guide begins   54.6 DRUM (start)   56.22 DRUM (stop: its rim under the shutter's lip)
   56.48 SHUTTER (on the hall face of the kitchen wall, 56.6-56.84)   56.1-56.7 the crawl under it
   56.84-59.9 THE KITCHEN (stripped, low: 2.4)   59.9 the scanner corridor (DL-06)
```

**The shutter:**

| State | Height of its bottom edge |
|---|---|
| Shut | 0 (it blocks him) |
| Wound | 0.3 a stroke, to 1.2 after four; held there while he holds the wheel |
| Let go, nothing under it | Falls at once and slams shut |
| Let go, the drum under its line | Slams onto the drum's chime and holds at 0.64 |

**Rules:**
- **The winch:** Use within 0.26 of the handwheel (53.55). He walks to it, turns his back to the camera and winds,
  stroke by stroke, a ratchet and the chain's rattle on each. After four he holds it. Moving, Use or Jump lets go,
  whether or not he has finished.
- **The drum:** Use at its left side to take hold; push right along the guide at 0.3 m/s. It stops against the
  shutter (56.22) and stays there. It stands 0.38 behind the lane, so he steps in to push it and back out after.
- **The crawl:** with the shutter on the drum, the gap is under his standing height; he crouches automatically, as
  under DL-01's shutter, and crouch-walks through.
- **Nothing kills here.** A slam close by (within 4 m) startles him.

## 4. Verbs

| Verb | Rules | What you see |
|---|---|---|
| Wind | Use at the winch; four strokes; any input lets go | `Crank`, as DL-01's bulkhead (the wheel sits where DL-01's does relative to him, so no new clip) |
| Push | Use at the drum, then move right; Use or Jump lets go | `PushWalk`, the drum rumbling on its guide; a thud as it seats |
| Crouch | Automatic under the shutter | `CrouchWalk` |

## 5. Models (`art/pass3/build_ration_hall.py`)

Built in final world x, after the scene gap is opened (`insert_scenes()` in `art/dl01/build_dl01.py`).

- **The shell:** the end wall with a doorway the size of the Racks' passage; the canteen's back wall and ceiling,
  two columns; the kitchen wall with the serving hatch (1.30 high); the kitchen, low, running into the scanner
  corridor's section at 59.9. `RationFloor` fills the floor between the Racks' and the sorting floor's.
- **The counter:** its front, grille and fascia, the servery behind, and the chalked ration board (`RationBoard`)
  and sign (`RationSign`, RATION ISSUE) over it.
- **The puzzle (driven by the game):**
  - `RationShutter`: ribbed slats with a lip reaching toward the hall, a drum-shaped dent in it; its housing above.
  - `RationWinch`: the handwheel, worn bright, with the cable's run up to the shutter's housing. It turns 60° a
    stroke.
  - `RationDrum`: olive, stencilled RATIONS · GR.4 · 25 KG · LOT 117, with chimes and rolling hoops; its floor guide
    and the rust ring (`RationDrumRing`) where drums have stood under the shutter.
  - `RationLamp`: the strip tube over the counter. It flickers.
- **The canteen:** tables, benches (some upturned), cots with blankets, bedrolls; the queue barriers folded into a
  maze; the painted sky (`RationMural`); the grade notice (`RationGradeNotice`) and tally marks (`RationTally`).
- **The shrine** on the first column: names on scraps (`RationShrineNames`), three photographs, a pressed flower,
  a ribbon, and candle stubs (`RationCandle`, the flames `RationCandles`).
- **The drawing** (`RationDrawing`), taped by the winch.
- **The kitchen:** stripped, its fittings gone.
- **Textures:** `art/pass3/textures_ration_hall.py`.

## 6. Lore

| Where | What it says | What it means |
|---|---|---|
| The ration board | RATION · PER HEAD · PER DAY: four painted rations (a loaf, a bowl, a cup, a tin), each halved in chalk, each halving struck through for the next; a "?" at the end | Rations halved, and halved again. |
| The grade notice, on the second column | RELOCATION BY GRADE · REFUGE AUTHORITY · ORDER OF ASCENT: four steps up to a sun, Grade 1 at the top, Grade 4 (the labour grades: the depot, the works, ring C) at the bottom, that step struck through and stamped SUSPENDED; "when?" pencilled under it | They were promised a turn to go up, and their turn was cancelled. |
| The queue maze, the cots between the tables, the bedrolls | | Families lived here when ring C flooded. |
| The shrine | Names in many hands, photographs, a flower, a ribbon, candle stubs | The ones they lost. |
| The painted sky | A big sun, fat clouds, birds as ticks, green hills, children's handprints along the bottom | A sky painted by people who had never seen one. |
| The crayon drawing, beside the winch | A little courier (box body, flat head, three antenna stalks) carrying a parcel along a dotted path to a house with a lit window; a sun, a crooked tree, a big M | D-17 and Mara, before the player has met either name. |
| The drum's dent in the shutter's lip, the rust ring | | People got through this way before him. |

## 7. Camera and light

- **The framing:** from about 47.1 it eases from the passage's into the hall's (a little wider and higher). It holds
  the shrine and the cots first, then from about 51.6 slides on to the counter, holding the winch, the drum and the
  hatch in one frame.
- **Light:** the hall has its own light zone (`lightZoneFor` in the game): while he is in it (from 47.4), its lights
  replace DL-01's and the Sorting Hall's, which are long out of sight. The counter's strip light, a spot on the winch,
  the drum and the hatch, flickers now and then (steady in calm mode); a fill under it; the shrine's candles, warm and
  unsteady; grey daylight from a high vent at the back; and a dim fill in the kitchen.
- **Shots:** none.

## 8. Sound and music

- **No new cue:** the depot's bed plays on.
- The winch ratchets and the chain rattles on each stroke. A slam onto the floor is a gate slam, a clank and a heavy
  shake; onto the drum, the same, a little lighter. The drum rumbles on its guide and seats with a thud.

## 9. Checkpoints

- **bay**: DL-04's, just through the bay door (47.1).
- **ration**: just inside the hall (48.6), the drum at its start, the shutter shut.
- **hatch**: past the shutter (57.05), the drum under it and the shutter resting on it.

## 10. Scene card (`docs/puzzle_principles.md`)

| Rule | This scene |
|---|---|
| Arc step | Latch and hold: twist (a hold that can't be kept, so something else holds it). Substitution: develop (a drum holds the shutter instead of his hand). |
| Builds on | DL-01's shutter and crouch and its crank wheel; DL-01's cart and DL-04's courier for pushing. New: a mechanism that only works while he holds it. |
| Wrong assumption | Wind it up and go under. It slams the moment he lets go. |
| Checkpoints | `ration` before, `hatch` after. No failure state. |
| Linkage | Wheel, cable up to the housing, shutter: one run in view. The drum's guide leads to the shutter's line. |
| Gear | Puzzle (develop), after DL-04's emotional beat. |
| Curiosity | None. |
| Tableau | The canteen as the refuge's bottom: the queue maze, the cots, the shrine, the ration board. |
| Emotional shot | None. The crayon drawing is seen in the side view, beside the winch. |

## 11. Where the build differs from the plan

- **A pushed drum, not a carried crate.** The plan had a ration crate, stacked by the queue barriers, carried to the
  hatch. The build uses a pushable drum on a floor guide that ends at the shutter's line, so it can only be left in
  the right place, and its chime takes the shutter's lip.
- **The slam:** the plan had him thrown back. In the build the shutter falls before he can reach it, and he startles;
  no knockback.
- **The drawing** is taped beside the winch, not elsewhere on the counter, so it is in view while he winds.

## 12. Open questions

- **The candles.** Some of the shrine's candles burn. Read literally, someone lit them not long ago. Intended (a seed
  for "Someone Home"), or should they be stubs, long out?
- **The wrong assumption.** The slam is loud and startles him, but costs nothing. Is that enough to read as "it won't
  stay up", or do players just wind again?
- **Hints.** When he stands idle he looks at the drum, then (with the drum set) the winch; the assist option shows the Use prompt there.
- **The drawing.** At the game's distance, does it read as D-17 and a house, or does it need a close-up?

## Pass 4 (built 20 October 2026)

From `docs/chapter1_pass4_plan.md`, sections 3 and 4. Positions are game x.

### The famine

The lower grades starved here, waiting (`art/pass3/build_ration_hall.py`, `build_famine`).
- **The dead:** the canteen's tables and benches are gone, burned or broken up, and the floor is the dead's, under
  sheets with ration tags tied to their toes: six in a row along the back, feet to the camera (48.5 to 52.0), a child
  in front of them by the door (48.75), and one on each cot, one curled. Shrouds only; nothing shows under them.
- **NO RATIONS · GRADE 4** in whitewash on the wall over the counter, and the counter hacked through (55.92 to 56.27)
  where someone took an axe to it to reach the servery.
- **The one he drags** (`RationBody`) lies on the lane's back edge at 52.3, a rope round its ankles.
- **Remains** share one painted palette with DL-02's sorters (`RemainsMat`), one draw call each.

### The weigh-in (replaces the winch)

The serving hatch opens only while the WEIGH-IN plate in front of it reads a person: one ration per head. It builds on
DL-03 (he alone is too light for a plate) and DL-04 (a machine wants a body, so drag one on), and makes them dark.

```
x: 52.3 THE BODY (start; dragged by the rope at its feet)   53.45 DRUM (start)
   53.68 WEIGH-IN post: the dial, its needle, the SERVED flag; the crayon drawing on the counter's front beside it
   53.85-55.75 THE PLATE (a goods weighbridge let into the floor)   54.8 the drum's or the body's place on it
   56.02 the drum, pushed on to the wall by the hatch   56.48 SHUTTER   56.1-56.7 the crawl
```

| On the plate | Reads | What happens |
|---|---|---|
| Nothing | Empty | The needle at rest. |
| D-17 | UNDER | The needle barely moves; a short buzzer. Too light, as in DL-03. |
| The drum | OVER | The needle slams round; a clank, then a bell and a shake. The hatch stays shut. |
| The body | PERSON | A click; held for a second, the hatch winds up to its serving height (0.64, a crawl) with a ratchet and the chain, the SERVED flag drops over the dial, and it stays. |

**Rules:**
- **The drum** stands between the body and the plate. Use at its left side and push right (0.3 m/s): it stops first on
  the plate (OVER). Push again and it runs on past the plate to the wall by the hatch (56.02), where it stays.
- **The body:** once the drum is out of the way, Use at the rope round its feet and drag it, walking backwards, slowly
  (0.2 m/s), as he dragged the courier in DL-04. The first time he takes hold, he hesitates (about 1.6 s). While the
  drum is still in the way, the body stops against it.
- **On the plate** he lets go. The needle settles in the PERSON band, the hatch winds up, and he pats the sheet
  (`Pat`), as he patted the courier.
- **Through:** he crouches under the hatch automatically and crawls through into the kitchen.
- **The winch is gone,** and so is the slam: the shutter only ever winds up. Nothing kills here.

| Verb | Rules | What you see |
|---|---|---|
| Push | Use at the drum, then move right; Use or Jump lets go | `PushWalk`; a thud and a shake at each stop |
| Drag | Use at the body's rope, then move right; Use or Jump lets go | `PushWalk` backwards, the sheet dragging; a hesitation the first time; `Pat` at the end |
| Crouch | Automatic under the hatch | `CrouchWalk` |

**Hints:** idle, he looks at the drum; once it is at the wall, at the body's rope.

**His label:** passing the crayon drawing (51.9 to 53.9) the first time, he checks his label, and the camera goes in
close on it: for MARA · C-114 · RING C, UNDELIVERED.

**The way on:** RING C ↓ stencilled in the kitchen past the hatch, over the shelves (`WayRingC05`, 57.3).

**Checkpoints:** `ration` just inside (48.6): the body and the drum at their starts, the hatch shut. `hatch` past it
(57.05): the drum at the wall, the body on the plate, the hatch at its serving height with SERVED showing.

**Scene card, updated:**

| Rule | This scene |
|---|---|
| Arc step | Weight on a plate: twist (it wants exactly a person). Give a machine a body: apply, made dark. |
| Builds on | DL-03's plate and gauge (he is too light); DL-04's drag to the bay and his touch after it. |
| Wrong assumptions | Stand on it: UNDER. Push the drum on: OVER. |
| Linkage | The plate in front of the hatch, its dial and SERVED flag on a post at the counter's end. |
| Tableau | The famine: the dead in rows, NO RATIONS · GRADE 4, the counter hacked through. |
| Emotional shot | The label close-up at the drawing. |

**Budget:** the shrouds are 16 draw calls, over the set pieces' 12 (`docs/chapter1_pass4_plan.md`, section 5).
