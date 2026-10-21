# Undelivered, the prologue (DL-01 to DL-11): playable prototype

A browser-playable build of chapter 1, eleven scenes played as one continuous level with no cut between them. It
follows the chapter plan in `docs/chapter1_plan.md`, its pass 2 to 6 plans (`docs/chapter1_pass2_plan.md`,
`docs/chapter1_pass3_plan.md`, `docs/chapter1_pass4_plan.md`, `docs/chapter1_pass5_plan.md`, `docs/chapter1_pass6_plan.md`), the scene plans in `docs/scenes/` and the standing direction in `docs/direction.md`.
It uses D-17 and the set from Blender, and the gameplay code mirrors the mechanisms planned for the Unity build.

## Run locally

```sh
cd game/undelivered
python3 -m http.server 8765
# open http://127.0.0.1:8765/index.html
```

three.js 0.169.0 loads from jsDelivr. The models are in `assets/` as `.glb`, and also as `.json`
(base64-wrapped GLB), because the artifact host serves `.json` but not `.glb`.
- **Parts:** the host takes files up to 16 MB, so a large model is split into parts of 10 MB of base64:
  `set.json` (which says how many parts there are), then `set.1.json`, `set.2.json` and `set.3.json`. The game
  fetches the rest and joins them.
- **The White** (`white.json`) loads before the title card's Begin. Without it, the game still plays, with the White
  unseen.
- **Warm-up:** at load every material is compiled and every texture uploaded (`warmUp`), with each region's lights
  and light zones switched on in turn, so nothing hitches when it first appears. Pass 4: it compiles into the
  composer's render target (`composer.renderTarget1`), as every frame is drawn (linear colour, no tone mapping until
  the output pass). Compiling for the screen built variants play never used, so every material compiled again at
  first sight: the stutters. With the light pool (see *Lights* below) and the pooled ripples, shader programs went
  from 247 to 54, and none compile during play except 3 in the opening.

## Controls

| | Keyboard | Gamepad |
|---|---|---|
| Move | A D, or the arrow keys | Left stick or D-pad (push fully to run) |
| Walk while Auto-run is on | Hold Shift | Hold B |
| Jump | Space (also W or Up) | A (south) |
| Use | E (or Enter) | X (west) |
| Pause | Esc (or P) | Menu |
| Back to checkpoint | R | (in the pause menu) |
| Developer overlay | ` | |

Auto-run is on by default; turn it off in the title or pause menu and Shift runs instead. Sound and
Music have separate toggles. "Show a button prompt if I'm stuck" turns on the key glyph (see Hints), and "Reduce
flicker and flashes" (calm mode) steadies flickering lights and turns off camera shake. On
touch devices, on-screen buttons appear once play begins.

## The level

The eleven scenes run left to right along one lane. The pause card shows the scene D-17 is in (`sceneName()` in the
game).

| Scene | Was (pass 2) | World x | Built by | Plan estimate | Pass 3 measured |
|---|---|---|---|---|---|
| DL-01 The Wake | DL-01 | 0 to 12 | `art/dl01` | 2:00 | 1:39 |
| DL-02 The Sorting Hall | DL-02 | 12 to 25 | `art/sorting_hall` | 1:45 | 0:52 |
| DL-03 The Weight of the Job | DL-03 | 25 to 30.6 (the gate) | `art/dl02`, moved by OFF2 | 2:30 | 1:25 |
| DL-04 The Racks | DL-04 | 30.6 to 47.9 | `art/dl02`'s racks hall, then `art/racks` | 2:30 | 1:15 |
| DL-05 The Ration Hall | new in pass 3 | 47.9 to 59.8 | `art/pass3/build_ration_hall.py` | 2:30 | 0:53 |
| DL-06 Return to Sender | DL-05 | 59.8 to 80.5, shared with DL-07 | `art/dl03`, moved by OFF3 | 2:45 | 1:28 |
| DL-07 The Heap | DL-06 | the same space, then the gallery | `art/dl03`, moved by OFF3 | 2:30 | 2:15 |
| DL-08 The Handbrake | DL-07 | 80.5 to 97.6 | `art/dl04` (belt side), moved by OFF3 | 3:00 | 2:06 |
| DL-09 The Slipping Cage | DL-08 | 97.6 to 118.8 | `art/cage`, then `art/dl04` (tunnel side), moved by OFF4 | 2:00 | 2:11 |
| DL-10 Up Only | new in pass 3 | 118.8 to 127.9 (ring C's level) | `art/pass3/build_up_only.py` | 2:30 | 1:11 |
| DL-11 The Child at the Address | DL-09 | 127.9 to 170.1 | `art/dl05`, moved by OFF5 | 3:30 | 2:08 |

Measured: (pending)

Pass 3, measured: the median of 20 simulated first playthroughs (`tools/sim`, results in
`tools/sim/results_pass3_first_playthrough.jsonl`). The whole chapter: median 17:47 (13:01 to 20:51), plus 0:20 of
opening; 0.8 deaths a run on average; 6.2 of 12 curiosities found. The floor (the simulated player with no hesitation
or mistakes, `results_pass3_mechanical.jsonl`) is 7:13. Pass 2's nine scenes measured 15:08 by the same method, and the
director played them in 16:57.

The lore dressing across scenes 1 to 9, the cage's readability pieces and the interactables' new materials are
`art/pass3/build_lore.py`'s. The estimates are first-time play from `docs/chapter1_plan.md` and
`docs/chapter1_pass3_plan.md`, not measurements. Pass 4's set pieces are in the scenes' own builders and
`art/pass4` (see *What happened here*).

The code keeps its original module names, so they use the old numbers: `art/dl02` and `updateDL02` are DL-03 (and the
start of DL-04), `updateDL03` is DL-06 and DL-07, `updateDL04` is DL-08 and the tunnel and balcony of DL-09, and
`updateDL05` is DL-11. The rework (the scenes added then, the reworked DL-01, DL-08 and DL-11, and the letters) is the
Chapter 1 module before `const HINTS`. Pass 2 (`docs/chapter1_pass2_plan.md`) follows it there: the curiosities
(`CURIOS`), the White (`WATERS`, `updateWhite`), ring C (`updateRingC`), the hazards (`updateHazards`) and deaths
(`DEATH`, `die`). Its props, hazards and D-17's clips for them come from `art/pass2`, and the White from `art/white`.
Pass 3 is in the same module: the Ration Hall (`RATION5`, `RH5`; pass 4's weigh-in is `PUSHABLES.drum`,
`PUSHABLES.body` and the `weigh` state in `updateCh1`), Up Only (`UPONLY`, `UO`,
`updateAct10`, `updateUpOnly`), the cage's readability (`BalanceNeedle` and the pawl lever in `updateCage`), C-114's
shut door (`C114DOOR`, `KNOCK5_X`) and the light zones (`lightZoneFor`). Pass 4 adds the light pool
(`buildLightPool`, `updateLightPool`, at the end of the script), the ripple pool (`ripplePool`), the head look's limits
(`headLook`), the careful pace by the White's water, the label checks (`labelWake`, `label5`, `label9`, `label11`) and
the label close-up (the `label` shot), and DL-10's echoes (`uoNeedle`, `CarPlateLamp0` to `2`).

**Lights: a fixed pool (pass 4).** Every light the scenes build is a proxy, moved to layer 31, which the camera never
renders. Each frame the lit proxies nearest the camera are copied into a fixed pool: 10 point, 4 spot, 2 shadowed
spot, 2 directional and 2 hemisphere lights (`LIGHT_POOL`). Unused slots go dark, and an empty shadowed slot stops
updating its shadow map. A shadowed spot beyond the two shadow slots still lights, without its shadow. The number of
lights never changes, so switching a scene's lights on or off no longer recompiles every lit material, and no pixel
pays for more lights than the pool.

**Light zones.** Each region's lights are switched on only while D-17 is in it (they are proxies now; the pool picks
from those that are on). Pass 3 adds two zones inside regions:
in the Ration Hall (from 47.4) its own lights (the counter's flickering strip light, the shrine's candles, a vent's
grey daylight, the kitchen's fill) replace DL-01's and the Sorting Hall's, long out of sight; in Up Only (from 117.8)
its own (the failing pendant, the two UP lamps, the crank's work lamp, the car's lamp, the cold light down the
counterweight's shaft) replace the goods hall's and the cage's.

**Interactables without red** (`docs/direction.md`). Red no longer says "use me". What D-17 can use is shown by wear
(grips and handles worn bright through tired paint: `HandledSteel`, `HandledBrass`, `WornIron`, `WornStrap`), by the
scene's light and by motion and sound. Red is kept for what the world itself painted red: the franking press's hazard
bands. The curiosities' red tags are gone.

## Chapter 1, part 2: DL-15 to DL-17 (pass 9)

The rest of Chapter 1, Attendance (design: `docs/chapter1_part2_plan.md`; art: `art/ch1/dl15.py` to `dl17.py`, built by
`art/ch1/build_attendance.py` into `assets/attendance.json` and `attendance.1.json`):
- **The way in:** DL-14's hatch is now a duct. He crawls in, the camera follows him behind the wall, and he comes out
  onto DL-15's sick bay balcony. No cut.
- **DL-15 One Pupil Missing:** a class of three kept ready.
  - The sick bay figure rides down the pupil lift only with an escort (NO PUPIL UNACCOMPANIED).
  - The two stand-in figures roll on a floor rail in either direction and stop at each seat. The one from the board
    stops in Mara's seat first.
  - D-17 sits in Mara's chair (her tree carved in the lid). Three lamps, the bell, dismissal: the figures bow and roll
    away, and he is left at child-desk height in the empty room.
  - Secret room: under the sick bay balcony, her hiding place (`att_escort`).
- **DL-16 After the Bell:** the procession waits at the raised bridge over a light well. He steps aside for them (the
  `AfterYou` clip), then holds the crossing lever until both are over. The rack, where the PLAYGROUND arrow points,
  takes them; its counterweight lifts out of the lane and the bridge latches down. The tannoy plays `att_bell`.
- **DL-17 A Different Lesson:** the workshop. Lift the tray wedged against the PLACEMENTS drawer, pull the drawer, read
  it. A close-up shows Mara's irrigation drawing beside a mended pot, then her placement card (Works Dept., ring A).
  His label is stamped again, FWD WORKS RING A, and Chapter 1 ends. `att_volunteer` is on the stool.
- **New D-17 clips:** `Sit`, `SitIdle`, `SitUp`, `AfterYou`. **Held Use** (keys, pad, touch) drives the lever.
- **Sims:** `CHAPTER=att2` starts at DL-15. The whole chapter plays from DL-12 to the end.

**Years are P.A.** Now is P.A. 387 (the old refuge years plus 268). In-world dates, the opening card, the docs and the
story board all use it.

## Pass 8: the Version 19 play test

Fixes from the director's Version 19 playthrough (play log, 21 October):
- **Interaction overlaps can't ship.** Each source of interactions (items, curiosities, secret rooms, voices,
  letters, pushables, each scene's fixed controls) is a category. `auditNear` sweeps D-17 along the level and lists any
  spot where two answer Use at once; `tools/sim/audit_near.mjs` runs it from every checkpoint and fails if the list
  isn't empty. It found three (the DL-14 cupboard over the pole, the DL-01 cord against the dispatch board, the DL-10
  suitcase against the last-car card), all fixed. Things he carries now win over everything else, so an item put down
  on top of another interaction can always be picked back up.
- **DL-14, the pole.** It starts through A's wheel, holding A up, so the first wind of the crank shows the jam working
  (B comes down alone, the pole rattles, he looks at it). Use at the wheel takes it out or puts it back, whatever A is
  doing. The peel no longer takes the camera.
- **Stuck inputs.** Held keys are tracked as a set and dropped when the page loses focus (keyup never arrives then);
  the gamepad's jump no longer sticks on once pressed.
- **The opening ends on the label, without a cut.** The side view starts where the opening's camera is and eases to
  its frame beneath a slow push in to his label.
- **A reason for the wake.** Dispatch speaks as the relays come on (`dispatch_wake`: *Supply restored. Resuming
  dispatch.*), then over the label (`dispatch_item`: *Courier D-17. One item outstanding. Deliver to: Mara. C-114,
  ring C.*). The old night-shift tannoy now plays once, from the hall.
- **The tannoys.** A two-note chime, a cleaner horn, and the next speaker along answering late. The placeholder for
  unrecorded lines is a voiced murmur (a buzz through moving vowel formants), not filtered noise. Tannoys play once
  as he passes; again only if he leaves earshot and comes back, and not within 150 s.
- **DL-05, the weigh-in.** The plate weighs the share of each thing on it, so the needle climbs, ticking, as the body
  comes on.
- **DL-06, the bucket gate.** One weight lifts the gate 0.38, well under his crouch: never a gap that looks passable.
- **DL-09, the cage.** With a plate in his hands, the tray's lamp beats and he looks at the tray.
- **DL-11, the desk.** He lets go himself once the marks are uncovered; Use anywhere between the toy and the terminal
  walks him to it; the held look at the marks is shorter and ends as soon as the player does anything.
- **DL-13, the classroom.** The camera first frames the figure, the seat and the brake together (eased in over the
  doorway); it steps back to the dial and the steps once the lesson runs. Use on the brake with no lesson running
  clunks, and the empty seat's lamp blinks. (The seat lamp had never lit: its setup line was lost inside a comment.)
- **A fall.** D-17 has a `Fall` clip (arms up, legs paddling, antenna streaming) for any real drop.

## Pass 6: the prologue

The eleven scenes are now the game's **prologue** (`docs/full_game_plan.md` plans the chapters after it). See
`docs/chapter1_pass6_plan.md` for the notes and what shipped. In the game:
- **The opening card** is three lines: *P.A. 387 · Seventy-six years of dark. · Then, tonight, the lights came on.*
- **Tableaux, not signs:** the remains have come apart where people were, doing something (`art/pass6`). The game
  only lights them: DL-02's fan and tea corner, and the pair on DL-11's coal-store roof.
- **The lip** (`teeter`, `tipOver`): the cart and the duct teeter at a pit's lip while he holds them. Letting go there,
  or pushing on into the lip for 0.45 s (a last shove, `Nudge`), sends them in.
- **The reveal** fires when he first crosses DL-04's gate, however it was opened.
- **The courier** stays in his hands to the bay. **The body** in DL-05 is taken by the foot (`RH5.bodyGap` 1.05).
- **Two weights in one carrier** (`c.load2`).
- **Music** cues fade in (`Music.play(name, fadeIn)`).
- **Up Only's lobby** comes back after the city's crane shot only once it is out of frame (`uoLobbyShown`).
- **Secret rooms** (`SECRETS`, `secretHere`, `updateSecretAct`):
  - `reader` in DL-06, the one who stayed;
  - `den` in DL-09, the children's den.

  How they play:
  - Use at the gap. He walks in along depth (crouching through the den's vent), and the camera frames the room.
  - Any move after 2 s brings him back out.
  - The end card counts the rooms found. Telemetry logs `secret`.
- **The ending** (`END5`, `updateEnd5`): from C-114's back door onto a landing over a dark well. He stops and looks up,
  the fog thins, and the camera rises with his look to the one lit window 24 m up and its new cable. He checks his
  label and climbs the iron stair as the picture fades to the end card: *End of the prologue*.

## Pass 5: time, cause, and a world gone dark

See `docs/chapter1_pass5_plan.md` for the notes and what shipped. In the game:
- **The opening card** (`#intertitle`): four lines say why D-17 wakes (the lower rings dark for 76 years, the power
  back tonight, one courier with a parcel still to deliver). It holds 12.5 s, or until any key or tap, then the wake
  plays with the `wake` cue.
- **Pushing into pits** (`tipInto`): DL-01's cart and DL-11's duct can be pushed on past a pit's lip. The front wheels
  drop, it slides, and it settles in the pit.
- **The couriers reveal** waits for the gate in DL-04 (`game.revealPending`). Walking through it, the camera pans
  across the racks and the sombre `racks` cue plays; the realisation (`kin`) waits 10 s after it.
- **The weigh-in body's sheet** ripples as it is dragged (`refs.bodyRipple`, a vertex wave on a clone of its
  material).
- **The light at ring C's seal:** ring C's lights come on and Up Only's go off out of view, so nothing switches in shot.
- **The ending** (`finish()`): he walks out of C-114, the screen fades over 4 s, and the end card reads *End of
  chapter one, Undelivered*. It no longer looks like the title.
- **The rider** (`syncRide`): carriers move after the player is updated, so D-17 is placed again once they have. He
  used to trail his carrier by one frame, a gap that changed with every frame's length: the judder riding up the
  ramp.
- **Scene select** and **telemetry**: see *Testing hooks* and *Telemetry*.

## The quest (pass 4)

Within the first minute the player knows what D-17 is for: a birthday parcel for Mara, C-114, ring C, three levels
down, 76 years overdue.
- **His label** carries the depot's stamp, UNDELIVERED, under the address. Starting play from the opening, he looks
  down and checks it (`CheckLabel`, `labelWake`), and the camera goes in close enough to read (the `label` shot): for
  MARA · C-114 · RING C, UNDELIVERED. The same close-up plays each time he checks it: at the child's drawing in DL-05
  (`label5`), on the balcony after the city (`label9`), and on reaching ring C's street (`label11`). Each plays once.
- **The dispatch board** (DL-01): one line still lit, C-114 · RING C · UNDELIVERED, its lamp blinking
  (`DispatchLineLamp`).
- **The way down:** RING C ↓ stencilled at each scene's way on, the same stencil every time (`WayRingC01` to
  `WayRingC10`), and "C-114 →" on ring C's barricade (`WayC114`, 134.6).
- **The pause card:** "Delivering: a birthday parcel for Mara, C-114, ring C. Three levels down. 76 years late."

## What happened here: set pieces (pass 4)

Each set piece shows one step of the refuge's fall at full scale, without words where it can. The remains are
shrouds and dry bones in clothes, never gore. Built by `art/pass4/build_story_depot.py` (DL-02, the stencils of DL-01 to
DL-05, the dispatch line), `build_story_shafts.py` (DL-08, DL-09, the stencils of DL-06 to DL-09) and
`build_story_ringc.py` (DL-10, its stencil, ring C's mark); DL-05's famine is `art/pass3/build_ration_hall.py`'s and
DL-11's drowning `art/dl05/build_dl05.py`'s.

| Scene | Set piece | What it shows | What it says |
|---|---|---|---|
| DL-02 | The last night shift | Five sorters' remains in their aprons: one over the sorting table's end, one against the wall holding a mailbag, one over the tea table, two at a bench under the gantry | They died at their posts, still sorting. |
| DL-05 | The famine | Rows of the dead under sheets with ration tags on their toes; NO RATIONS · GRADE 4 over the counter, hacked through | The lower grades starved here, waiting. |
| DL-08 | The fall | The goods lift's car crashed in a flooded pit under the near landing: snapped rope, burst gate, luggage, coats, a pram | People tried to ride the goods lift up, and it fell. |
| DL-09 | The cut bridge | Across the atrium, the bridge to the upper city with its middle 24 m blown out; the near stump barricaded and heaped with belongings under GRADE 1–2 BEYOND THIS POINT; the far stump lit. Seen in the awe shot, through the coin viewer and from the balcony | The way up was cut, on purpose. |
| DL-10 | The crush | 215 shoes, the queue barrier flattened toward the lift, LAST CAR hanging from one hook, hand marks and scratches down the lift front and the counterweight's shaft | The last car, and everyone who didn't fit. |
| DL-11 | The drowning | A 1.4 m high-water line on every house, a table lashed into a raft, a pram half under, and a bed of bones in the alley's flooded foot under the White's water | Ring C drowned, and something has lived on what was left. |

Each has at most one light of its own (the sorters, the wreck, the lair).

## DL-01 The Wake (plan estimate 2:00)

1. **Opening, 20 s.**
   - D-17 wakes in the cradle. The parcel lamp, the relay pulses he answers, sparks, the work lamp, grit, then the camera move.
   - The parcel's label behind his chest window: "for MARA · C-114 · RING C" in a parent's hand, initials I.V. with a small
     crooked tree, the postmark P.A. 310, a BIRTHDAY / DO NOT OPEN stamp, the child's crayon drawing, and (pass 4) the
     depot's UNDELIVERED stamp across it.
   - Skip appears after 1.5 s.
   - As play begins, he checks his label and the camera goes in close on it (see *The quest*).
2. **Curiosities by the cradle.** All optional (see Curiosities).
   - The parcel scale, the first: its Use glyph shows as soon as he is near, so the player learns that props can be
     used. He steps up, the needle swings, and a POSTAGE DUE ticket pops up for him to read. Stepping on it without
     Use still swings the needle.
   - The pull-cord lamp. He tiptoes up, tugs the cord, and the lamp warms the alcove, revealing a depot route map
     (depot, homes, school, works, ward, then up).
   - The dispatch board: its last line still lit and blinking, C-114 · RING C · UNDELIVERED. He finds his own route
     card (D-17 · ROUTE C · C-114, MARA pencilled in) in the rack under it and taps his label. Beside it, the night shift's roster, every name struck through but IVO and D-17.
3. **Shutter.**
   - He crouches automatically under it.
   - Use on the T-handle: two heaves, the latch gives, the counterweight drops and the shutter swings up. He flinches.
     (Pass 3: the counterweight's chain always draws now; it was culled by the camera.)
4. **Fallen conveyor (0.22 m).** The first jump.
5. **The depot cart and the trench.**
   - The drain trench is too wide to jump and too deep (0.8 m) to climb out of. Drop in and he flinches, and he is
     back at the checkpoint.
   - Use at the cart's worn push bar and push it right. It rolls to the edge and drops in, and becomes the bridge.
   - Step down onto it and climb out on the far side. The cart (0.55 m) can also be climbed before it is pushed.
6. **The hall.** The camera pulls back to show the scale: a gantry, columns, a huge backlit sorting carousel,
   chutes, light shafts, a slow searchlight, swaying parcel hooks, a sparking live cable and a steam vent. A camp cot
   with ration tins in the hall behind.
7. **Bulkhead.**
   - Over it, the refuge's grade chart: four painted bands, gold at the top, the depot at the bottom in plain grey
     (GRADE 4 · LABOUR).
   - Use the crank wheel. D-17 turns his back to the camera and hauls it hand over hand, five strokes, as the door
     rises, then bounces proudly.
   - He walks through the door, along a service passage behind the wall, and steps out into DL-02.
     The camera follows the whole way, with no cut.

**Movement:**
- Walk 0.9 m/s, run 1.6 m/s, crouch-walk 0.5 m/s.
- Jump apex 0.4 m, with 100 ms coyote time and a 120 ms input buffer.
- Ledges between 0.24 and 0.62 m are climbed rather than jumped; from a jump he catches ledges up to about 0.72 m.
- A climb is a 2.3 s authored beat, and the camera pushes in for it:
  1. He looks up, hops and grabs the edge.
  2. Heave, slip back, heave again.
  3. His old left knee over the edge, then he tips onto the top.
  4. He stands and glances back down.
- Carrying something, he walks slowly and can't jump. Pushing or dragging, Use or Jump lets go.
- Setting down never refuses: if the spot in front isn't flat, he puts it at the nearest flat spot within reach, or
  at his feet.

**Hints:** after about 5 s idle near the next useful thing, D-17 looks at it; at about 10 s he leans in. With the
stuck-prompt option on, a key glyph appears at about 18 s. The look is held to a neck's range (pass 4): 70° either
side, 35° up or down; a target behind him is let go.

## DL-02 The Sorting Hall (plan estimate 1:45)

1. **Out of the passage.** He steps out into the hall where post came in by tube. The lamp over the gantry door at the
   far end is the brightest point. Behind him, left of the doorway, a hand franker (optional): he franks his own
   claw, RECEIVED, and the stamp stays on it.
2. **The franking press.** Between the passage and the tube, a press still stamps its routine every 2.6 s, over the
   only way on. Its lamp blinks before each stroke. Walk under it while it is up; caught under it, he is crushed
   (see Danger).
3. **The tube.** The first time he passes the tube station, its cup drops an old letter onto the lane: Mara's own
   letter to the post office ("IS D-17 LOST?"), with her crayon drawing on the back. A brass mail slot stands a few
   steps on (see Undelivered letters).
4. **The tea corner.** Mugs on numbered hooks, one gone, with the night shift's names (ODA, TOMAS, IVO with a crooked
   tree, RUTH); the courier-of-the-year board, its last frame a pale silhouette; a wordless notice that ring C
   deliveries stopped in P.A. 310, with a water drop; a notice board, NIGHT SHIFT CUT and GRADE 3 TRANSFERS SUSPENDED;
   a bedroll. On the couriers' shelf, his own mug (optional): he lifts it as if to drink, can't, and puts it back
   carefully.
5. **The table.**
   - The way on is a gantry over a long sorting table. A collapsed pigeonhole wall blocks the floor.
   - The table top (0.75 m) is just out of a jump's reach.
   - Use to lift the parcel box (by its worn strap), carry it to the table's foot, and Use again to set it down.
   - Hop onto the box, climb onto the table, then up to the gantry (1.35 m).
6. **The gantry.** Along it over the wreck to the lit doorway, and down into the weight room (DL-03).
7. **The last night shift** (pass 4). The sorters' remains at their posts: over the table's end, against the back
   wall with a mailbag, over the tea table, and at a bench under the gantry (see *What happened here*).

Only the press can kill here; he is back just out of the passage.

## DL-03 The Weight of the Job (plan estimate 2:30)

1. **The weighing room.** Standing on the floor plate lifts the gate, and stepping off drops it. A gauge on the gate post
   reads the load on the plate, and a sign shows the rule. Wet drag marks run from a floor drain across the room and
   back: the White's first sign. On the wall, WE KEEP YOU ALIVE, and a half-torn poster: WHO CARRIES WHOM?
2. **The weight and the trolley.**
   - Neither the sorting weight nor the trolley is heavy enough on its own.
   - Use to lift the weight. He carries it slowly, and Use again sets it down, onto the trolley's deck if it is in front of him.
   - Use at either end of the trolley to take hold, then push or pull it. Use or Jump lets go.
   - Park it, with the weight, on the plate.
3. **The reveal.** The rack lights come on row by row over 55 dormant couriers like D-17, and the camera widens for a
   few seconds. Climb over the trolley (the weight is a ledge) and walk under the gate.

## DL-04 The Racks (plan estimate 2:30)

1. **The realisation.**
   - As he walks in among the couriers, he stops and understands (`Realise`) while the music swells.
   - He walks on slowly past the racks, with the camera at the couriers' eye level.
   - Optional: Use at the courier slumped by the lane, and he tries to wake it.
2. **The bay.** At the end of the racks, a charging bay: a floor plate with a courier pictogram, and a shutter door
   with three lamps. Standing on the plate opens the door; stepping off drops it before he can reach it. The trolley
   can't follow him: it is holding the gate.
3. **The fallen courier.** One of his own lies fallen from its rack by the lane, its right leg gone below the knee:
   bitten, not cut. Use at its tow loop and drag it, walking backwards, slowly, toward the plate. Use or Jump lets go.
4. **The cradle.** Once the courier is within 0.6 m of it, he lets go and the cradle's arms reach out, draw it in,
   close on it and seat it. Its lamps flicker weakly, then hold, and the door stays open. He lays a claw on its head
   (`TouchHead`), once, and walks on through a service passage into the Ration Hall.
   - Optional, once the courier is seated: back at the empty slot under the chalk flowers and the couriers' memorial
     tags (41.08), Use, and he sits in it for a moment.

## DL-05 The Ration Hall (plan estimate 2:30)

New in pass 3; pass 4 made it the weigh-in (`docs/scenes/DL-05_the_ration_hall.md`, *Pass 4*).

1. **The canteen.** The depot workers' canteen, where families slept when ring C flooded and where the lower grades
   starved: queue barriers folded into a maze, a shrine of names and candles, a sky painted on the back wall, the
   RELOCATION BY GRADE notice with Grade 4 struck through, SUSPENDED. The tables are gone; the floor is rows of the
   dead under sheets with ration tags on their toes, and one on each cot. A checkpoint just inside (`ration`).
2. **The weigh-in.** The way on is through the serving hatch in the kitchen wall. Over the counter, NO RATIONS ·
   GRADE 4 in whitewash, and the counter hacked through. In front of the hatch, a weighbridge plate (53.85 to 55.75);
   on a post at the counter's end (53.68), its dial and a sign: WEIGH-IN · ONE RATION PER HEAD. Taped beside it, a
   child's crayon drawing of a little courier carrying a parcel to a house, signed M; passing it, he checks his label.
   The hatch opens only while the plate reads a person.
3. **Too light.** Standing on the plate, the needle barely moves: UNDER, and a buzzer.
4. **Too heavy.** An olive ration drum stands by the counter (53.45). Use at its left side and push it right: it stops
   on the plate, the needle slams to OVER, a clank and a bell. The hatch stays shut. Push again and it runs on past the
   plate to the wall by the hatch (56.02), and stays.
5. **A person.** One of the dead lies on the lane's back edge (52.3), a rope round its ankles; the drum blocked it until
   now. Use at its feet and drag it right, walking backwards, slowly, as the courier in DL-04 (the first time he
   hesitates before he takes hold). On the plate (54.8) the needle settles in PERSON; after a second the hatch winds
   up to its serving height (0.64), the SERVED flag drops over the dial, and it stays. He pats the sheet.
6. **Under.** He crouches under the hatch automatically (a checkpoint past it, `hatch`), and walks on through the
   stripped kitchen, past RING C ↓, into the scanner corridor.

The winch is gone, and so is the slam: nothing here kills. The shrouds are 16 draw calls, over the set
pieces' budget of 12.

## DL-06 Return to Sender (plan estimate 2:45)

1. **The scanner.**
   - Optional, before the arch: the sorter's chair. Use, and he climbs up and sits; the cushion fits him.
   - He stands to attention as it sweeps him. It reads his label (room 114) and refuses it: ring C is sealed.
   - The pit of dead letters opens below. He can only walk slowly while he takes it in, and the music swells.
   - Then he checks his label and the theme turns hopeful.
2. **The return line.**
   - Carriers rise from the return hatch, stop at the dock and are hauled to the chute, where they tip their load into the pile.
   - Any carrier standing on the floor can be boarded: Use, or a standing jump (no direction held), beside it.
     A running jump beside one is just a jump. Use or Jump again to hop out.
   - Ride one to the chute and it tips him into the pile with the dead letters. He respawns at the scanner checkpoint.
   - Stop the belt (the stop lever), throw the points (the lever on a yellow stand), restart the belt, and board at
     the dock. A chase of green lamps along the ramp shows the way the points now send the carriers.
   - Behind the belt, a barricade of sorting crates, pulled apart; by the pit, UP IS FOR THEM rollered over, with
     EVERYONE UP painted across it.

Once the belt runs with the points set to the ramp, the game counts the rest of this space as DL-07.

## DL-07 The Heap (plan estimate 2:30)

1. **Up, for nothing.** He rides up the service ramp over the pit and hops out at the landing. The empty carrier sinks
   back down through the return slot. A counterweighted gate closes the gallery a few steps on; its chain runs over a
   drum in the roof to a bucket hanging at the ramp's head.
2. **Back down.** Walk off the gallery's left end and he sits into a parcel slide back down to the sorting floor.
3. **The delivery.** The gate needs both iron sorting weights in its bucket.
   - One stands beside the dock; the other at the far end of the floor by the pit edge, where the slide puts him
     down. On the floor they are low obstacles to hop.
   - Lift one, carry it to a carrier, and Use: he sets it in. A carrier waiting at the dock always takes it; while the
     belt is stopped, so does any carrier standing on the floor line.
   - With the points on the ramp, the carrier climbs and tips; the weight tumbles into the bucket. The camera widens
     to hold the climb, the bucket and the gate. One weight lifts the gate half way, and it stalls with a strain; the
     second lifts it all the way.
   - The first time a weight drops into the bucket while he is on the floor, something pale rolls once in the dark
     water of the sump under the chute, and is gone. Running near the sump draws it again.
   - A weight sent to the chute is lost with the post, and back where it stood 4 s later. Riding a loaded carrier up
     himself also works.
4. **Up again.** Ride the next carrier up and walk under the gate.
5. **The gallery.** A letter caught on the rail in a shaft of light falls at his feet as he passes (optional).
   - The stopped clock (optional): Use, and he winds it. It ticks for a minute or so.
   - Walk past the old sorting desk and the day board. The walkway panel before the residential access doorway
     sags and creaks under him, and once he is past it, it gives way and falls. There is no way back.
   - On through the doorway, under EVERYONE UP, into DL-08.

## DL-08 The Handbrake (plan estimate 3:00)

1. **Goods Lift 2.**
   - The goods hall ends in an open shaft, flooded to 1.75 below the landing, with the platform at the bottom, under
     the water. The first time the platform rises, something pale surfaces below it and sinks.
   - Under the near landing (82.0 to 85.8), seen in section, the flooded pit runs on, and in it the goods lift's
     car lies crashed on its side (pass 4, the fall).
   - A pan in the floor drives the head drum: load on it raises the platform. D-17 alone raises it halfway; stepping off drops it with a crash.
   - The goods trolley, still loaded with ballast, raises it all the way. Use at its push bar, then push it onto the pan.
2. **The pawl.**
   - Step onto the platform as it is, and it drops under him; he scrambles back (`Teeter`).
   - Use the pawl lever at the shaft's edge, behind the lane. Below the landing the dog only rattles on the rack.
     At the landing it drops home with a click.
3. **The far rail.**
   - A safety rail on the far landing is too high to climb from the platform.
   - With the pawl set, the platform no longer needs the trolley. Push the trolley off the pan, across the platform to
     the rail, climb onto it and over the rail.
   - **The White's first meeting.** Running, or landing from a jump, over the shaft is loud: the White comes up and
     slaps the water, and he is knocked back off his feet, unhurt. By the shaft he goes carefully whatever the auto-run
     setting (pass 4), and walking is quiet; Shift or B runs. Falling into the sump is a death.
4. **The returns belt.**
   - On the far landing (a checkpoint), a stove, a pan and ration tins where people camped; the belt starts after a
     bell, a beacon and the klaxon.
   - It runs against him, bringing crates of returned post down from the rings: hop the low ones, climb the tall ones.
     At worst it carries him back to the landing. On the wall beside it, Lift 1's relocation timetable, every
     departure struck through, the last ringed: LAST.
   - The depot's relay pulse fades out as he climbs it.

## DL-09 The Slipping Cage (plan estimate 2:00)

1. **The climbs.** Off the belt's top end, three climbs to an upper landing at the edge of a shaft (a checkpoint).
   Across the shaft and lower down, a lit landing leads on.
2. **The counterweight.**
   - A balance gauge on the landing has two pans drawn on it, its needle deep in "too light". The counterweight hangs
     in plain view beside the landing, its open tray lit by its own lamp, and two weight plates lie in the lamp's pool.
   - He walks into the open freight cage and it drops a hand's breadth under him: the needle kicks, the brake squeals
     and holds, an alarm bell rings, and the chain hauls it back up. He has to step out and in again to try.
   - Lift a plate, carry it to the counterweight, and Use: he turns and sets it in the tray. Each plate moves the
     needle half the way; with both it reads balanced, and the cage takes him. Plates can't be set down in the cage.
3. **The cage.**
   - It starts down by itself, with him braced, his claw on the pawl lever (`CageRideLever`). It lets down,
     shudders, then slips.
   - It catches once just above the lit landing, hangs for a moment, then slips again. The landing's lamp blinks
     faster as the cage nears it, and white chevrons on the shaft wall line up with one on the cage when it is level.
   - Use pulls the lever, visibly (`CagePullPawl`). Pulled between the catch and the landing, the pawl bites and the
     cage settles at the landing, and he bounces proudly.
   - Too early, it rattles and the lever springs back; pull it again. Too late, the cage drops onto the buffers in
     its flooded sump: a death, and he is back on the upper landing. Once both plates are in, they stay in.
4. **The cable.** Past the lit landing (a checkpoint; a pram wheel and a tied bundle against its wall), the
   antechamber's floor is wet, and a downed cable arcs over it in two places in turn, every 2.4 s, each with a
   crackle first. Cross the first once it dies, wait on the dry hatch cover between them, then cross the second. The
   first touch only throws him back; after that, a touch is a death.
5. **The tunnel.**
   - Past the RESIDENTIAL ACCESS sign to the tunnel mouth. (Pass 3 cut the look back toward the depot.)
   - He plays the whole chalk hopscotch (`HopscotchLong`, 12 s): he checks that nobody is watching, wobbles on 6,
     cheers on HOME, and hops back. Moving left or jumping in its first 3 s cancels it. Use on the chalk afterwards
     plays it again.
6. **The refuge.**
   - The tunnel opens onto a balcony high in the atrium: three rings of homes around a void.
   - He stops at the rail (`Awe`), the camera cranes up and out, and the music swells. Across the void, the cut
     bridge (pass 4): the way up, its middle blown out.
   - The atrium is the refuge's underground city: a chasm dug into the rock, the poorest industrial levels at the
     bottom, the upper city rising into the haze.
   - On the balcony, a coin viewer (optional): he has no coin, presses the plunger anyway, and looks through it at the
     lit upper city. Left and right swing it, slowly; Use or Jump steps away.
   - Walking on along the balcony, he checks his label, looking down toward ring C.
   - The balcony's deck runs on into the relocation lift's lobby (DL-10). The old stair down to ring C is gone.

The tunnel and the balcony are built with DL-08's set (`art/dl04`); the game counts them as DL-09, as the plan does.
The counterweight's plates, the cage's sump and the antechamber's cable are `art/pass2`'s; the gauge, the tray lamp,
the chevrons and the cage's clips are `art/pass3/build_lore.py`'s.

## DL-10 Up Only (plan estimate 2:30)

New in pass 3 (`docs/scenes/DL-10_up_only.md`).

1. **The lobby.** The ring C relocation lift lobby, where the families left from (a checkpoint inside). A heap of left
   luggage; a painted queue line to the lift with what was dropped along it (a shoe, a doll, a birdcage); the
   departures board; over the lift, RELOCATION — GRADES 1–2 ONLY with EVERYONE painted across it. The car stands
   behind a lattice gate, its floor a plate that weighs passengers, with a load needle. Ring C is below; the old stair
   lies collapsed beside the lift. Pass 4, the crush: shoes by the hundred, the queue barrier flattened toward the
   lift, LAST CAR hanging from one hook, hand marks down the lift front. On the lift front, DL-09's balance gauge,
   reading car against counterweight: too light.
2. **UP.** The panel has one button (123.95). Use: he turns to the wall and presses (`PressButtonHigh`). The car is
   empty, so the panel buzzes and nothing moves.
3. **A passenger.** Under the failing pendant, the last suitcase, tagged C-114. Lift it, carry it to the car, and Use
   in its doorway: he sets it on the plate. The plate dips, DL-04's three bay lamps on the car's sill light one by one,
   the balance gauge swings to balanced, the gate draws shut, and the UP lamps glow. Pressing the lobby's UP now sends the car up while the counterweight comes down its shaft, empty; 3 s later
   the car comes back. It works, without him.
4. **The service door.** Use at the crank on the pier (126.45): four strokes wind a striped service door up out of
   the lane, and it stays up. Behind it, the counterweight's open shaft, the counterweight at the deck with a
   footplate and rails, and its own service UP on the far wall.
5. **Down.** Stand on the counterweight's footplate and Use its UP: the car goes up with the suitcase, the way its
   family did, and he rides the counterweight down to ring C (`RideCounterweight`: he looks up at the car leaving,
   then down at ring C). He walks on along the bottom landing to ring C's ledge.

## DL-11 The Child at the Address (plan estimate 3:30)

1. **Ring C.**
   - From the bottom landing to ring C's ledge. The lane is sealed (RING C SEALED · P.A. 311), "C-114 →" painted on
     the barricade; crouch under it. On the street he checks his label.
   - Ring C is a street he walks through, abandoned and nearly dark. Behind the lane: C-102 and C-104 (split, a plank
     door 104A cut into it), both chalked GONE UP; a cross alley with the neighbourhood's standpipe, the ration queue's
     post and its painted marks, and a RATIONS / GRADE 4 – TUES sign; C-106, with UP IS FOR THEM half whitewashed under
     EVERYONE UP; then C-108 (through its dim window, a table still set for a meal), C-110, and C-112, boarded and
     taped. In front of the lane, a row of ruined homes, cut down below his height. Washing lines, a cable of four
     bulbs, and ring B's tier above in the haze.
2. **The flood.**
   - The lane's back half has sunk into deep water along C-108 and C-110, and at the narrow point by C-110 the whole
     lane has. The White lives in it: as he comes along, something pale surfaces far off and sinks.
   - Pass 4, the drowning: a high-water line at 1.4 m on every house, a table lashed into a raft and a pram half under
     at the narrow point, and in the alley's flooded foot between C-108 and C-110, a bed of bones, the White's lair.
   - Running or landing near the water is loud; walking is quiet. The first time it hears him, it surfaces, hisses
     and sinks: a warning. After that, heard, it comes and surfaces, and if he is on the bank within reach, it takes
     him (see The White).
   - He won't step into the water at the narrow point: a spark at his foot, and he jerks back.
   - **The doorbell:** C-108's brass bell with its small amber lamp, at the water's near end. Use: he turns to the
     wall and presses it. It rings for 12 s, and the White swims to C-108's sunken step and noses at it.
   - **The duct:** Use at the fallen duct's worn grip and push it right. It drops into the narrow point with a loud
     splash and becomes the bridge. While the bell rings, the splash doesn't turn the White; otherwise it brings it.
   - **Walk across.** Running near the White breaks the bell's hold.
   - **Or the junction box** by C-110 (optional): its lever shorts the live cable into the water, and the White
     flees for 20 s.
   - As he reaches the bridge, a letter slips out of C-110's slot onto it (optional).
3. **The square.** The noticeboard with the evacuation notice and the children's drawings of the White, a bench, a
   dry fountain, a swing, and ring C's mail slot.
4. **C-114.** Its front door is shut. He steps toward the camera, square to it, and knocks twice (`Knock`), seen close
   over his shoulder. He waits; nobody comes. He pulls the cord the family hung from the door's lever for the child
   (`Tug`), the latch gives, and the door swings in. Through it, the street wall fades and the house is seen in
   section, like a dollhouse.
5. **The home.**
   - The hall, with a small yellow raincoat on the hooks. A light switch (optional): click, and the hall bulb comes on.
   - The kitchen and living room: a table with three chairs, one a child's. A radio (optional): static, then half a
     verse of a children's song, and he does a little two-step.
6. **The bedroom.**
   - Passing the bed, he sits the patched rabbit up and pats it (`Straighten`). Any move cancels it. On the shelf, the
     photograph: her father in his sorter's apron, Mara on his shoulders.
   - A low desk has fallen against the back wall, over the forwarding terminal. Use at its grip bar and drag it
     clear. Pencil growth marks and a crooked carved tree are behind it, and the music comes in.
7. **The terminal.** Use at it. He presents his chest window to the reader (`Present`), his three lamps answer its
   three, and the screen reads NO ONE AT THIS ADDRESS, then FORWARD TO SCHOOL, RING B. His label is stamped.
8. **Out the back.** The back door opens onto a service passage and a sign for the school. The end card.

## Undelivered letters

Chapter 1's secret, and entirely optional: the story reads without them.
- **Three letters:** one dropped by the tube in DL-02 (Mara's own), one caught on the gallery rail in DL-07, and one
  slipped out of C-110's slot in DL-11.
- **Three mail slots,** brass, polished by use: `MailSlot2` (DL-02), `MailSlot6` (DL-07, by the old sorting desk) and
  `MailSlot9` (DL-11, in the square before C-114).
- Use near a letter on the floor to pick it up (`PickUpLetter`). Use at a slot while holding one to post it
  (`PostLetter`): the slot's stamp lamp blinks, with a knock and a chirp.
- A letter can be posted at any slot, not only its own.
- What he has picked up or posted (`letterState`) is kept through respawns and checkpoint reloads. Start over clears it.

## Curiosities

Twelve props D-17 can Use for a small payoff: a joke, a sound, a fact or a view (`CURIOS` in the game). None is
needed. Each plays its own clip (`art/pass2/build_curios.py`), and its props move with it.

| Scene | Curiosity | Where (world x) | What happens |
|---|---|---|---|
| DL-01 | Parcel scale | 1.45 | He weighs himself; a ticket pops up: POSTAGE DUE. |
| DL-01 | Cord lamp | 0.59 | The lamp warms the alcove (its own interaction). |
| DL-01 | Dispatch board | 1.0 | His own route card, C-114, MARA pencilled in; he taps his label. |
| DL-02 | Hand franker | 12.8 | He franks his own claw: RECEIVED. The stamp stays. |
| DL-02 | His mug | 15.2 | He lifts it, can't drink, and puts it back carefully. |
| DL-04 | The empty rack | 41.08 | Once the courier is seated: he sits in the slot under the chalk flowers. |
| DL-06 | The sorter's chair | 60.8 | He climbs up and sits; the cushion fits him. |
| DL-07 | The stopped clock | 73.38, on the gallery | He winds it; it ticks for about 75 s. |
| DL-09 | Hopscotch | 108.15 | Once he has played it: the long hopscotch again. |
| DL-09 | Coin viewer | 114.6 | No coin, the plunger anyway, and a long look at the lit upper city, swung slowly by the player. |
| DL-11 | Hall light switch | 158.72 | Click: the hall bulb comes on and stays on. |
| DL-11 | Radio | 163.0 | Static, then half a verse of a children's song. |

The new scenes, DL-05 and DL-10, have no curiosities.

- **The early ones** (the scale, the cord lamp, the dispatch board, the franker and the mug) are made obvious: a warm
  pool of light with a faint glow behind (not the cord lamp), and as he passes one he turns his head to it, until he
  has used it. Pass 3 removed their small red tags. The scale shows its Use glyph at once.
- **The later ones** are easter eggs: no light and no glance.
- **A find:** a soft chime and "◆ n / 12" in the corner. The pause card and the end card show "Curiosities n of 12 ·
  letters posted n of 3". Finds (`curioFound`) are kept through respawns and checkpoint reloads; Start over clears
  them.

## Danger

Deaths are shown, then cut. He is a machine: his own death clip, sparks, his eye stutters out, a hard cut to black
(no fade), and he is back at the checkpoint 0.6 s later, 1.3 to 2.2 s in all. Whatever he carried is dropped where he
was. The bed plays on, but a cue that is playing fades out on the respawn. Calm mode drops the sparks and the shake.

| Hazard | Scene | World x | What it does |
|---|---|---|---|
| The franking press | DL-02 | 13.62 to 14.28 | Stamps every 2.6 s, its lamp blinking for 0.5 s first. Under it while it is down: crushed (`DeathCrush`), back at `room`. |
| The gallery collapse | DL-07 | 78.95 to 80.05 | Sags under him, then falls once he is past. Not lethal; no way back. |
| The shaft sump | DL-08 | 85.8 to 88.3 | The White slaps the water and knocks him back, unhurt (`Knockback`). Falling in is a death. |
| The cage crash | DL-09 | 101.2 to 102.8 | Onto the buffers in the sump: `DeathFall`, back at `cage`, the plates still in the tray. |
| The tunnel cable | DL-09 | 105.04 to 105.44, 105.77 to 106.17 | Two arcs in turn every 2.4 s, a dry hatch between. The first touch in a game knocks him back; after that, `DeathShock`, back at `landing8`. |
| The lane | DL-11 | 145.95 to 150.6 | The first time, the White surfaces and hisses: a warning. After that it lunges and drags him under (`DeathGrabbed`), back at `ringc`. |

The older failures are unchanged and are not deaths: the trench (DL-01) and the chute (DL-06) fade back to the
checkpoint as before. Nothing kills in DL-05 or DL-10 (pass 4 removed the ration hatch's slam).

## The White

A pale, blind cave animal like a giant olm, about 2.5 m long, with feathery pink gills and no eyes
(`art/white/build_white.py`). It hunts by sound, never by sight, and never leaves the water.
- **Noise:** running near its water (within 1.4 m; it was 2.2 before pass 3), or landing from a jump, is loud. Walking (Shift, B, or a
  half-pushed stick) is quiet. A splash or a bell is louder still.
- **Careful by its water (pass 4):** within 2 m of the waters where it scares or hunts (DL-08's sump, DL-11's lane), he
  goes carefully whatever the auto-run setting, so auto-run no longer sets it off. Shift or B still runs.
- **The hunt:** it patrols, hears, listens for a moment, swims to the sound with ripples ahead of it, and surfaces.
  If he is on the edge within reach, it strikes about a body length; otherwise it sinks after about 2 s and patrols
  again.
- **It warns first:** the first time it finds him on ring C's lane, it surfaces, rears, hisses and sinks, and doesn't
  strike. Only after that does it lunge. The warning is kept through respawns; Start over clears it.
- **A bell** draws it and holds it while it rings (DL-11's doorbell, 12 s). A footstep doesn't turn it, but running
  near it does.
- **The shorted cable** (DL-11's junction box) sends it deep for 20 s, hearing nothing.
- **Each water has a part** (`WATERS` in the game): DL-07's heap sump, a glimpse (it rolls once and sinks); DL-08's
  shaft sump, a scare (a slap and a knockback); DL-11's lane, the hunt (a warning, then it kills).
- **It fits its water:** each water scales it (smaller in the sumps), its whole body is kept inside the water, and it
  turns only while deep.
- **Its signs before it:** wet drag marks from a drain in DL-03, and the fallen courier's bitten leg in DL-04.
- **Clips:** `WhiteGlide`, `WhiteSwim`, `WhiteListen`, `WhiteSurface`, `WhiteSink`, `WhiteRoll`, `WhiteSlap`,
  `WhiteLunge`, `WhiteDrag` and `WhiteNose`. Its skin is pale and a little translucent, with a wet rim.

## Checkpoints

- DL-01: start, shutter open, the hall (across the trench), door open.
- DL-02: out of the passage.
- DL-03: the weight room's floor, and solved (the gate held open).
- DL-04: through the bay door (`bay`).
- DL-05: just inside the Ration Hall (`ration`, 48.6), and past the hatch (`hatch`, 57.05: the body on the plate, served).
- DL-06: scanned (63.3).
- DL-07: the gallery landing (73.0), and past the gate (75.3).
- DL-08: the goods hall (81.9), and the far landing, pawl set (89.2).
- DL-09: the shaft's edge (`cage`, 100.8), the lit landing (`landing8`, 103.3: once the cage is held there and he
  steps off), and the tunnel mouth (107.7).
- DL-10: on the deck just inside the lift lobby (`uponly`, 119.4).
- DL-11: through the seal (`ringc`, 135.25), the bedroom (164.1), and after the terminal (167.1).

A respawn fades out and back in about 1.3 s; a death cuts instead (see Danger). Authored moments play once: after a
respawn or a checkpoint reload, the ones already seen are skipped (at C-114's door he goes straight to the cord).
Three states also outlive a respawn: both plates in the counterweight's tray, the tunnel cable's one free touch, and
the White's one warning. Start over clears all of this.

## Camera, quirks and performance

- **Camera:** one continuous side-on shot. Its framing widens, closes in or rises as D-17 moves (wider over the hall
  and the rack reveal; the Ration Hall's shrine and cots, then its counter, plate, drum and hatch together; wider
  again to watch a loaded carrier climb the ramp, holding the gate in frame as it rises; the climbs, the shaft and
  the lit landing together for the cage; tall and wide over Up Only's lobby, lift and counterweight shaft, then down
  the shaft on the ride), and pushes in a little for climbs and actions. Gameplay never takes it away.
  - Authored shots are kept for emotional beats, and blend in and out of the side view:
    - Pass 4, the label (`label`): whenever he checks his label (as play begins, and in DL-05, DL-09 and DL-11), the
      camera goes in close enough to read it.
    - DL-04: the realisation among the couriers.
    - DL-06: the scan, the crane out over the pit, and the label close-up.
    - DL-09: the hopscotch (the long version: close and low while he checks nobody is watching, a crane up to about
      45° over the whole court, then down and in for the cheer); the coin viewer (through the eyepieces, a 110 mm
      lens across the chasm to the lit upper city; left and right swing it, slowly, and Use or Jump steps away); and
      the crane out over the atrium (the chapter's one wide shot). Pass 3 cut the look back from the tunnel.
    - DL-11: the knock at C-114's shut door (close, three-quarters, over his shoulder), a held look at the growth
      marks (first time only), the terminal over his shoulder, and the rabbit.
  - On ring C's lane the framing is raised (2.15 m, looking down to 0.4 m) so the water and the White read. In C-114
    it frames the hall, the kitchen and living room, the bedroom and the back door in turn.
  - Cranks, levers, lifts, pawls, the cage and pushes all play in the side view.
  - Heavy impacts shake it a little; calm mode turns the shake off.
- **Quirks:** D-17 has short reactions for particular moments.
  - Proud: he bounces when the bulkhead opens, when the points are set to the ramp, and when the cage's pawl bites.
  - PeekDown: he peeks over the trench, the cart's far edge, the pit rail and Lift 2's shaft.
  - Startle: a slam or a crash close by (the weight room's gate, a carrier tipping at the chute, the lift platform).
  - Startle also when the cage hauls itself back up after dipping under him, the first time the lift's UP buzzes,
    and at the White's warning.
  - Knockback: thrown off his feet by the White's slap in DL-08 or the cable's first arc in DL-09.
  - Others: he stands to attention at the scanner, brushes himself off after the ride up, scrambles off the unlatched
    platform, rides the slipping cage braced with his claw on the pawl lever, flinches at the water, hops the chalk
    squares, stands in awe at the rail, rides the counterweight down looking up at the car, knocks at C-114 and pulls
    its cord, sits the rabbit up and lays a claw on the seated courier's head.
  - Glance: passing an early curiosity he hasn't used yet, he turns his head to it, once (pass 4: no more than 70° and
    35°, never round to one behind him).
  - Pass 4: he hesitates before taking hold of the body in DL-05, and pats its sheet once it is on the plate.
- **Performance:** see the budget in `docs/direction.md`. The resolution adapts to the frame rate. Lights come from
  the fixed pool (see *Lights* above), and ripples from a pool built at load.

## Music

The score is in `assets/music/` and is composed and rendered by `art/music/compose_dl01.py` (see its
README). It is sparse:
- A cue for the wake.
- A quiet 48 s loop under play.
- A cello cue as he first walks into DL-01's hall.
- A short threshold cue as the bulkhead opens and D-17 walks through into DL-02.
- DL-03 and DL-04: a roll call when the rack lights come on, then a full swell as he walks in among the couriers.
- DL-06: the refusal, a swell over the pit, near silence for the label check, then the theme in F major.
- DL-08: a warm F major and the parcel's three notes when the pawl drops home.
- DL-09: `refuge`: near silence, then phrase B broadening into F major, peaking as the camera reaches its widest over
  the atrium. It plays out over the start of DL-10.
- DL-11: `child`: when the desk clears the marks, the parcel's three notes become a lullaby on the music box, piano and strings.
- DL-05 and DL-10 have no cue of their own: the bed plays on through the Ration Hall, and Up Only has only the
  machinery.
- After it, over the end card, the full theme ending in a music-box *Happy Birthday*.

The bed stops at the tunnel mouth. The depot's relay pulse, which has sounded every six seconds since the wake, fades
out on the returns belt.

Music has its own toggle in the title and pause menus, and it dips while paused.

## Rebuild the assets

```sh
cd art/dl01
python build_dl01.py --out ../../game/undelivered/assets     # needs bpy 5.2 (Python 3.13)
```

This builds the whole chapter. `build_dl01.py` calls every other builder: `art/dl02`, `art/dl03`, `art/dl04`,
`art/dl05`, `art/sorting_hall`, `art/racks` and `art/cage`, then pass 2's `art/pass2` (`build_pass2.py`: the hazards,
the White's signs and D-17's knockback and death clips; `build_curios.py`: the curiosity props and clips), then
`insert_scenes()` to open the two gaps, then pass 3's `art/pass3` (`build_ration_hall.py`, `build_up_only.py` and its
clips `PressButtonHigh` and `RideCounterweight`, and `build_lore.py`: the lore dressing of scenes 1 to 9, the cage's
gauge, tray lamp and chevrons, its clips `CageRideLever` and `CagePullPawl`, the red remap and the curiosity tags'
removal), then pass 4's `art/pass4` (`build_story_depot.py`, `build_story_shafts.py`, `build_story_ringc.py`: the
set pieces and the stencils; see *What happened here*), and `art/white`. It writes `set`, `d17`, `couriers` (the dormant couriers' three poses and their rack
slots) and `white`, each as `.glb` and `.json`. A `.json` is split into parts of 10 MB of base64 (`pack_for_web`), so
`set` is `set.json` and `set.1.json` to `set.3.json`. `--blend <path>` also saves the Blender file.

`HOPSCOTCH_LONG` in the game copies the long hopscotch's root-motion numbers from `art/dl04/hopscotch_long.json`,
which `art/dl04/hopscotch_clip.py` writes. Keep them in step.

**Segment offsets.** The later stretches of the level sit further along x than where they were first built, so that new
scenes fit between them. The game uses `OFF2 = 13`, `OFF3 = 33`, `OFF4 = 42` and `OFF5 = 54` (`index.html`).
- `OFF2` moves the weight room and the racks hall (`art/dl02`, which applies it itself).
- `OFF3` moves the return line, the heap and the gallery (`art/dl03`) and Lift 2 and its belt (`art/dl04`).
- `OFF4` moves the tunnel and the city (`art/dl04`).
- `OFF5` moves ring C (`art/dl05`): game x is `art/dl05`'s x + 54.
- `build_dl01.py` keeps pass 2's `OFF2 = 13`, `OFF3 = 21` and `OFF4 = 30` and builds everything there, then
  `insert_scenes()` moves whatever starts past 47.3 by 12 (room for the Ration Hall) and whatever starts past 104.6
  by 12 more (room for Up Only). The results are the game's offsets; keep the two files in step.
- The other new builders (`art/sorting_hall`, `art/racks`, `art/cage`, `art/pass2`) build in world coordinates
  before the gaps open; `art/pass3` builds in final world x.

## Telemetry

The `Telemetry` module records anonymous play events (scenes, checkpoints, deaths, prompts, idles, puzzle signals,
frame rate) for playtests. Send them to a collector with `?telemetry=https://your-host/events`; the pause card's
**Save play log** saves the log as JSON (in the artifact viewer, through its downloads capability, which asks the
viewer first). Players can turn it off in Options. `tools/telemetry/README.md` covers the events, the collector and the
summary.

## Testing hooks

- **Scene select:** the title card and the pause card have "For testing, start at" with DL-01 to DL-11. Each scene
  starts from its checkpoint, with everything before it done (`startAt(cp)`).

- **`window.__dl01`:** for automated traversal checks. It exposes:
  - the game state, `play(checkpoint)` to start at any checkpoint, `scene()` (the current scene's name), `near()`
    (what Use would do now) and `music()` (the cue playing);
  - `world` (the three.js scene) and `THREE`;
  - `letters` (`letterState`), `offsets`, the layout constants (`k`), and the carriers and crates;
  - pass 2: `pressT()` and `arcT()` (where the press and the tunnel cable are in their cycles), `k2` (`CW8`,
    `ARCS8`, `BELL9`, `JUNCTION9`, `PRESS2`, `SHAFT`, and pass 3's `RH5`, `RATION5`, `C114DOOR`, `UO`, `UPONLY`,
    `CG`), `white()` (its state, x, water and whether a bell holds it),
    `waters` (`WATERS`), `curios` (`curioFound`), `curioList()` (each curiosity's id, x, region, upper and early),
    and `die(how)` to kill him (`crush`, `shock`, `grabbed` or `fall`).
- **`window.__sim`:** test only. When it is set, a simulated player drives the game at a fixed 60 Hz, several steps per
  frame, rendering now and then. `tools/sim/` uses it to play the whole chapter (see its README).
- **Developer overlay:** ` shows the mode, frame rate, position, clip, checkpoint and current action.
