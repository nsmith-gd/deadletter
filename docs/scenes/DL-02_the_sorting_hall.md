# DL-02 The Sorting Hall: production plan

**Status:** built as a playable prototype (`game/undelivered/`), for director review; not yet timed
**Source:** `docs/chapter1_plan.md`, scene 2; `docs/chapter1_build_spec.md`, sections 2 and 3 (18 October 2026)
**Sequence:** DL-01 → DL-02 → DL-03, with no cut on either side
**Duration target:** about 1:45 first time, 0:40 floor (`docs/chapter1_plan.md`)

New in the Chapter 1 rework. Where this plan and the build spec differ, this describes the game; section 11 lists
the differences.

## 1. What the scene must do

| Requirement (plan and overview) | How the build meets it |
|---|---|
| Introduce carrying, safely, on the path | The way on is a gantry above a long sorting table. The table is too high to climb from the floor, and a fallen pigeonhole wall shuts the floor route. A parcel box with a red strap sits in the open floor before the table. Carry it to the table's foot, hop onto it, climb onto the table, then up to the gantry. Nothing here can fail. |
| The first try nearly works | The table top is at 0.75. From a jump he can catch a ledge up to 0.72, so he hits its edge and drops back. The answer is a box's height away. |
| The tube coughs out the first undelivered letter | The first time he passes the tube station, its cup drops an old letter onto the floor in front of him. |
| Teach the chapter's secret verb at a red mail slot | A post pillar with a red rimmed slot stands two steps further on. He picks up the letter (`PickUpLetter`), turns to the slot and posts it (`PostLetter`). The slot's stamp lamp blinks, with a knock and a chirp, and he bobs, pleased. Optional, and never in the way. |
| A workplace that stopped mid-shift | A tea corner with mugs on numbered hooks, one hook empty, a kettle and a dead bulb; the courier-of-the-year board; sorting trays still half full on the table. |
| The first sign of the flood | A wordless notice by the tube: ring C, a water drop, R.Y. 42, a crossed-out envelope. Water seeps out from under the wreck below the gantry. |
| The goal reads at once | The gantry doorway's lamp is the brightest point in the hall from the moment he steps out of the passage. |

## 2. Beats

| Beat | Time (approx.) | What happens |
|---|---|---|
| **Out of the passage** | 0:00 | From DL-01's bulkhead, along the passage behind the wall, he steps out toward the camera at x 13.2. The camera trucks with him from the hall's framing to this one; nothing fades. |
| **The tube** | 0:10 | Passing the tube station, the cup lets go of its letter (a short chain rattle and a tap). It lands flat on the lane. |
| **The slot** | 0:20 | Optional. He picks it up and posts it at MailSlot2. |
| **The table** | 0:40 | He tries the table from the floor and falls short. The box is in the open, its red strap the only red on the lane. |
| **The box** | 1:00 | He lifts it (`Lift`), carries it (`CarryWalk`, 0.42 m/s) to the table's foot and sets it down (`SetDown`). |
| **Up** | 1:20 | Box, table, gantry. Along the gantry over the wreck to the lit doorway. |
| **Down** | 1:40 | He drops from the doorway's sill into the weight room (DL-03). |

## 3. Layout (game x in metres; the hall's floor is at 0)

```
x: 12.0 left wall   13.2 emerge   14.6 TUBE CUP   15.1 notice   15.35-17.3 tea corner (alcove)   16.0 MAILSLOT2
   17.4 BOX   18.6-22.6 SORTING TABLE (top 0.75)   22.6-23.5 collapse   22.4-25.0 GANTRY (deck 1.35)
   25.0-25.32 doorway in the weight room's wall (sill 1.35)   25.6 weight room floor (DL-03)
```

| From | To | Height | How |
|---|---|---|---|
| Floor | Box | 0.20 | A hop |
| Box | Table | 0.55 more | A standing climb |
| Floor | Table | 0.75 | Out of reach: from a jump he catches ledges up to 0.72 |
| Table | Gantry | 0.60 more | A standing climb |
| Sill | Weight room | 1.35 down | A drop |

**Rules:**
- **The box:** carried like DL-03's weight, with Jump disabled while he holds it. It can be set down anywhere flat, so
  any spot against the table's foot works.
- **The collapse:** under the gantry, the wreck is solid from the floor to the deck. The table's front is closed
  with drawers, so nothing passes underneath.
- **The left wall:** he can't go back into the passage.

## 4. Verbs

| Verb | Rules | What you see |
|---|---|---|
| Lift | Use beside the box on the floor | `Lift`, as DL-03's weight; the box's red handle is at 0.22, like the weight's bail |
| Carry | Holding the box | `CarryWalk` / `CarryIdle` at 0.42 m/s |
| Set down | Use while carrying, on flat floor | `SetDown`; on uneven ground he hesitates (a worried sound) and keeps it |
| Pick up a letter | Use within 0.4 of a letter on the floor | `PickUpLetter`, 30 frames |
| Post | Use within 0.4 of a slot, holding a letter | He turns to the slot; `PostLetter`, 40 frames; the stamp lamp blinks |

Letters he picks up are kept through respawns and checkpoints. A letter he doesn't post here can be posted at any
later slot.

## 5. Models (`art/sorting_hall/build_sorting_hall.py`)

- **The shell:** walls, a 4.5 m ceiling and beams, the doorway out of the passage, panels and a green dado.
- **The tube station:** a cabinet on the back wall, brass tubes down from a manifold under the ceiling, the
  delivery mouth over the cup (`TubeCup`), the letter in it (`TubeLetter`), a rack of brass tube carriers with one
  dropped on the floor.
- **MailSlot2** with `SlotLamp2` on its cap.
- **The tea corner:** table, three mugs, kettle, five hooks with number tags (one empty), a crate for a stool, a dead
  bulb on its flex, the courier-of-the-year board, the ring C notice.
- **`CarryBox`:** 0.40 × 0.34 × 0.20 with a red strap and handle.
- **`SortTable`**, trays, parcels and letters on its back half, the pigeonhole wall behind it, the work lamp.
- **The collapse:** a tall pigeonhole unit fallen against the back wall, a second unit on its back across the lane,
  parcels, letters and boards heaped round them, and the puddle seeping out.
- **`SortGantry`:** deck, treads, yellow toe board and handrails, its legs jammed on the wreck, its torn left end.
- **Shared by all three letters:** the envelope mesh, `HeldLetter` and the letter textures.
- **Also:** the doorway and `GantryLamp` in the weight room's left wall (`art/dl02`).

## 6. Lore

| Where | What it says | What it means |
|---|---|---|
| The tube letter | Addressed to C-106, postmarked R.Y. 42, a star pictogram | Post for ring C, from the year it stopped. |
| The ring C notice | Ring C, a water drop over waves, R.Y. 42, an envelope crossed out | Deliveries to ring C stopped because of water. |
| The courier-of-the-year board | Five photographs, R.Y. 37 to 41, each a D-unit with a rosette and a hand on its shoulder: D-04, D-11, D-02, D-09, and **D-17** for R.Y. 41. The frame for R.Y. 42 is pale, a silhouette. | The staff were proud of their couriers, and of him. The year after, nobody was chosen. |
| The tea corner | Mugs on numbered hooks, one gone; the kettle; a dead bulb | People worked here, and left. |
| The water under the wreck | | The flood reached the depot too. |

## 7. Camera and light

- **One framing** holds the tube, the slot, the table, the wreck and the gantry door. It follows him between x 15.2
  and 20.9, then eases into the weight room's framing as he crosses the gantry.
- **Lights:** a warm work lamp over the table (x 20.6); the gantry door's warm lamp (x 24.7), the brightest; a cool
  glint at the tube. The tea corner stays dim.
- **Shots:** none.

## 8. Sound and music

- The `threshold` cue from DL-01's bulkhead carries him in; the hall has no cue of its own.
- The tube's cough is a short chain rattle and a tap; posting is a knock, a chirp and the stamp lamp's blink.

## 9. Checkpoints

- **room**: just out of the passage (x 13.2). Before pass 2, nothing in the hall could fail; now the franking press
  can (see *Pass 2*).
- **weighroom**: on the weight room's floor, after the drop (x 25.9).

## 10. Scene card (`docs/puzzle_principles.md`)

| Rule | This scene |
|---|---|
| Arc step | Carry: introduce. The letters: introduce. |
| Builds on | Climbing (DL-01's crate and gantry) and pushing a thing into place to stand on (DL-01's cart). New: carrying. |
| Wrong assumption | The table is a jump. It is 3 cm out of reach; the box is the step. |
| Checkpoints | Before (`room`) and after (`weighroom`). There is no failure state between them. |
| Linkage | The tube's brass runs from the ceiling manifold to the cup, so the letter visibly arrives by tube. |
| Gear | Traversal and a first-use puzzle, with an optional curiosity. |
| Curiosity | The tube and the slot; the tea corner and the board. |
| Tableau | The courier-of-the-year board, its last frame a silhouette. |
| Emotional shot | None. |

## 11. Where the build differs from the spec

- **The box** is 0.20 high, not 0.32. A 0.32 box would leave a 0.43 climb to the table; at 0.20 it is a hop, then a
  0.55 climb.
- **The stamp** (plan: "stamps it RETURN, with a thud") is a blinking stamp lamp, a knock and a chirp. No stamp is
  seen on the letter.

## 12. Open questions

- **D-17 on the board.** Is "courier of the year, R.Y. 41" right for him, and does it need to read without zooming?
  At the game's distance the unit numbers are too small to read.
- **The stamp.** Show a RETURN stamp landing on the letter, or keep it to the lamp?
- **The jump.** The table is 3 cm above a jump's reach. Playtests should show whether players read that as "nearly"
  or as a bug.

## Pass 2 (built 19 October 2026)

From `docs/chapter1_pass2_plan.md`. Positions are game x.

**The franking press** (`FrankingPress`, `art/pass2/build_pass2.py`): a C-frame stamping press, its column against
the passage wall behind the lane, still stamping its routine. It stands on the lane between where he steps out (13.2)
and the tube (14.6), so every route passes under it. The plan had it guarding only the tube letter. It is the
hall's only way to fail.
- **Its cycle, 2.6 s:** the lamp (`PressLamp`) blinks for 0.5 s (the tell; steady in calm mode), the ram drops in
  0.12 s, stays down 0.35 s, rises over 0.6 s, and stays up about 1 s. Each stroke thuds and clanks, with a small
  shake close by. The flywheel turns once per stroke.
- **Deadly:** under the ram (13.62 to 14.28) while its face is below 0.74, about 0.85 s of each cycle. That leaves
  about 1.75 s, enough to walk under it (about a second). Its bed is 0.045 high, a step.
- **A death:** crushed (`DeathCrush`), sparks, the cut, and back at `room` (13.2), just before it.

**Curiosities** (both early: a light pool, a red tag, and a glance as he passes until used):

| Curiosity | Where D-17 stands | What happens |
|---|---|---|
| Franking machine (`FrankerCounter`, `HandFranker`) | 12.8, facing left, left of the passage doorway | He lays his right claw under the head and hauls the lever: thunk. RECEIVED (`FrankHand`). He shows it to nobody in particular, pleased. The stamp stays on his claw (`ClawStamp`) from then on. |
| Named mugs (`CourierShelf`, `MugD17`) | 15.2, facing right, by the tea corner | He lifts the mug marked D-17, raises it as if to drink (he can't), a small droop, and sets it back with great care, nudging the handle round (`HoldMug`). |

**Checkpoints:** unchanged (`room`, `weighroom`).

## Pass 3 (built 20 October 2026)

From `docs/chapter1_pass3_plan.md`. Positions are game x.

- **Fix, setting the box down:** setting down never refuses. If the spot in front of him isn't flat, he puts the box at
  the nearest flat spot within reach, or at his feet. (The director had trouble here; watch for it on mobile.)
- **Use without red** (`docs/direction.md`): the box's strap is worn webbing (`WornStrap`); the hand franker's lever
  and `MailSlot2` are brass, polished by use (`HandledBrass`). The franking press keeps its red hazard bands: it
  kills. The red tags on the franker and the mugs are gone; their light pools and the glance stay.
- **The tube letter is Mara's** (`art/sorting_hall/textures_sorting_hall.py`): a six-year-old's pencil capitals to the
  post office, "DEAR POST, MY BIRTHDAY PARCEL HASNT COME. IS D-17 LOST? LOVE MARA C-114", stamped and postmarked
  R.Y. 42. On the back, in crayon, what it says without words: a girl crying at the door of her house beside a
  crooked tree, and far off in the dark a little courier with a parcel and a question mark over it.
- **Lore** (`art/pass3/build_lore.py`):

| Where | What it says | What it means |
|---|---|---|
| The tea corner (17.86), `LoreNoticeBoard` | NIGHT SHIFT CUT and GRADE 3 TRANSFERS SUSPENDED (an up arrow, crossed out), BY ORDER · R.Y. 42 | The year the parcel was posted, the work below was cut and the way up was shut. |
| The hanging mugs (15.89), `LoreMugNames` | The night shift's names in enamel paint: ODA, TOMAS, IVO (with a crooked tree), RUTH. D-17's mug is untouched. | IVO is Mara's father; the parcel's sender signs I.V. under the same tree. |
| The tea corner (17.0), `LoreBedroll02` | A bedroll and a ration tin | Someone slept here. |

The plan put the notices in DL-03; the build puts them on the tea corner's board, where the mugs are.

- **Hazards and checkpoints:** unchanged (`room`, `weighroom`).
