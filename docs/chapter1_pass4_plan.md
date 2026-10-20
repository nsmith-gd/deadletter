# Chapter 1, pass 4: what happened here, said bluntly

**Status:** in build, 20 October 2026. These are the director's notes from playing pass 3 (Version 13).

The notes:
- the White is too sensitive;
- the world doesn't tell how things happened through big set pieces;
- performance stutters;
- D-17's head turns strangely, often;
- in DL-01 there's a wall behind the spawn that he can pass through;
- the new puzzles are fine but don't build on the earlier aha moments;
- the quest is ambiguous;
- the storytelling should be dark and blunt.

## 1. Fixes

| Note | Cause | Fix |
|---|---|---|
| A wall at the spawn | Up Only's moving parts (the car, its gate leaves, the sheaves, the service crank and door) were built in their own space and then moved again. So they drew at the world origin, which is where D-17 wakes. | `Batch.done(local=True)` in `art/pass3/build_up_only.py`. |
| The White is too sensitive | Auto-run is on by default, so D-17 runs everywhere, and running is what it hears. | Beside water the White lives in, he goes carefully whatever the setting; Shift or B still runs. |
| The head turns strangely | The idle look and the curiosity glance turned his head straight at their target with no limit. A target behind him twisted it round or flipped it, and every early curiosity drew a glance each time he passed. | The look is held to a neck's range: 70° either side, 35° up or down. A target behind him is let go. Each curiosity gets one glance. |
| Stutters | One cause found so far: each ripple got its own material and was disposed when it faded. That released the shader, and the next ripple compiled it again. | A fixed pool of ripples built at load and compiled by the warm-up. Profiling continues (section 5). |

## 2. The quest, said plainly

Within the first minute the player must know what D-17 is for: a parcel for Mara, C-114, ring C, three levels down, 76 years overdue.
- **The wake:** he looks down at his label, and the camera cuts in hard on it, close enough to read:
  - for MARA · C-114 · RING C;
  - a stamp, UNDELIVERED.
- **The dispatch board:** one line is still lit, C-114 · RING C · UNDELIVERED, and its lamp blinks.
- **The way down:** stencilled RING C ↓ arrows at each scene's way on, the same stencil every time, so the direction is never in doubt.
- **The pause card** says it in words: *Parcel for Mara. C-114, ring C.*
- **Moments where he checks his label:** on seeing the crayon drawing (DL-05), on the balcony looking down at ring C (DL-09), and on reaching C-114's street (DL-11).

## 3. What happened here: set pieces

The history in order:
1. The refuge was sealed and divided into grades.
2. The night shift was cut.
3. Ring C's pumps failed and it flooded, and the lower grades crowded into the depot.
4. The rations ran out.
5. The relocation lift took grades 1 and 2 only. The bridge to the upper city was cut so nobody else could cross.
6. When the system fell apart, everyone left went up any way they could, and many died trying.

Each set piece shows one step at full scale, without words where possible. The remains are real but never gory: shrouds, dry bones in clothes, belongings.

| Scene | Set piece | What it says |
|---|---|---|
| DL-02 | **The last night shift.** Behind the lane, the sorters at their tables: dry remains in aprons, slumped over the frames, one still holding a mailbag. The work lamp is on them. | They died at their posts, still sorting. |
| DL-05 | **The famine.** The hall's floor is rows of the dead under sheets, ration tags tied to their toes. The serving counter is hacked through. Over it hangs NO RATIONS · GRADE 4, and a WEIGH-IN plate stands before the hatch. | The lower grades starved here, waiting. |
| DL-08 | **The fall.** Seen from the platform, the goods lift's cage lies crashed at the bottom of its shaft: its cable snapped, its gate burst, luggage and coats spilled out. | People tried to ride the goods lift up, and it fell. |
| DL-09 | **The cut bridge.** From the balcony, across the void: the bridge to the upper city with its middle span blown out. The near stump is heaped with belongings and a barricade; GRADE 1–2 BEYOND THIS POINT stands at its end. | The way up was cut, on purpose. |
| DL-10 | **The crush.** The lift's lattice gate is bent outward, shoes lie by the hundred, and hand marks run down the shaft wall. LAST CAR hangs on one hook. | The last car, and everyone who didn't fit. |
| DL-11 | **The drowning.** Every house in ring C has a waterline at 1.4 m. A table is lashed into a raft, and a pram is half under. Under the White's water, at its deepest, lies a bed of bones. | Ring C drowned, and something has lived on what was left. |

Mara's family got out (the photograph, the suitcase going up). The world around her didn't.

## 4. Puzzles that build on what the player has learned

The ahas so far:
- DL-01: an object becomes a bridge (the cart).
- DL-02: carry something and climb it (the box).
- DL-03: weight on a plate opens a gate, and he alone is too light (the trolley).
- DL-04: a machine wants a body, so give it one (the courier on the bay).
- DL-06 to DL-09: weight in a counterweight (the carriers, the pan, the tray).

### DL-05 The Ration Hall becomes a weigh-in (DL-03 + DL-04, made dark)

The serving hatch opens only while the WEIGH-IN plate in front of it reads a person: one ration per head.
1. **He stands on it:** the needle barely moves and the buzzer sounds. He is too light, as in DL-03.
2. **He pushes the drum onto it:** the needle slams to OVER, the bell clangs, and the hatch stays shut. Not a person.
3. **The answer:** he drags one of the shrouded dead onto the plate, as he dragged the courier in DL-04.
   - The needle settles in the PERSON band and the hatch winds up.
   - It ratchets, SERVED, and stays.
   - He crawls through.
   - At the plate he stops and pats the sheet, as he patted the courier's hand.

The winch is gone, and the drum stays as the wrong answer.

### DL-10 Up Only says what it builds on

- **The car's floor plate wears the bay's three lamps from DL-04.** They light one by one when a passenger is aboard.
- **The lobby wall has the cage's balance gauge from DL-09,** reading car against counterweight. With the car empty it sits deep in "too light", the same face the player has just learned.
- The suitcase goes in, the lamps light, the needle swings to balanced, and the gate closes.
- **Then the turn:** he rides the counterweight down, the side of the scale he has been loading all chapter.

## 5. Performance

To measure:
- shaders compiled after the warm-up;
- draw calls and triangles per scene;
- lights per zone.

To hold the new set pieces to a budget:
- at most 25k triangles and 12 draw calls each;
- repeated figures as linked duplicates of one mesh;
- no new lights beyond one per set piece.

## 6. Order of work

1. Game fixes (section 1): done in the game and the Up Only builder.
2. Art, in three modules, each owning its scenes:
   - `art/pass4/build_story_depot.py`: DL-02, DL-05 (with `art/pass3/build_ration_hall.py`), RING C ↓ stencils for DL-01 to DL-05, the label's UNDELIVERED stamp and the dispatch board line.
   - `art/pass4/build_story_shafts.py`: DL-08 and DL-09, and the RING C ↓ stencils for DL-06 to DL-09.
   - `art/pass4/build_story_ringc.py`: DL-10 (with `art/pass3/build_up_only.py`) and DL-11, and the RING C ↓ stencil for DL-10.
3. Game: the weigh-in, the quest beats, the DL-10 echoes, then measuring, checking, publishing and the docs.
