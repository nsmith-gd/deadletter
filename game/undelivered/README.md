# Undelivered (DL-01 to DL-11): playable prototype

A browser-playable build of chapter 1, eleven scenes played as one continuous level with no cut between them. It
follows the chapter plan in `docs/chapter1_plan.md`, its pass 2 and pass 3 plans (`docs/chapter1_pass2_plan.md`,
`docs/chapter1_pass3_plan.md`), the scene plans in `docs/scenes/` and the standing direction in `docs/direction.md`. It uses D-17 and the set from Blender, and the gameplay code mirrors the
mechanisms planned for the Unity build.

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
- **The White** loads before the title card's Begin, and at load every material is compiled and every texture
  uploaded (`warmUp`), with each region's lights switched on in turn, so nothing hitches when it first appears.
- **Without `white.json`** the game still plays, with the White unseen.

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

| Scene | Was (pass 2) | World x | Built by | Plan estimate | Measured |
|---|---|---|---|---|---|
| DL-01 The Wake | DL-01 | 0 to 12 | `art/dl01` | 2:00 | — |
| DL-02 The Sorting Hall | DL-02 | 12 to 25 | `art/sorting_hall` | 1:45 | — |
| DL-03 The Weight of the Job | DL-03 | 25 to 30.6 (the gate) | `art/dl02`, moved by OFF2 | 2:30 | — |
| DL-04 The Racks | DL-04 | 30.6 to 47.9 | `art/dl02`'s racks hall, then `art/racks` | 2:30 | — |
| DL-05 The Ration Hall | new in pass 3 | 47.9 to 59.8 | `art/pass3/build_ration_hall.py` | 2:30 | — |
| DL-06 Return to Sender | DL-05 | 59.8 to 80.5, shared with DL-07 | `art/dl03`, moved by OFF3 | 2:45 | — |
| DL-07 The Heap | DL-06 | the same space, then the gallery | `art/dl03`, moved by OFF3 | 2:30 | — |
| DL-08 The Handbrake | DL-07 | 80.5 to 97.6 | `art/dl04` (belt side), moved by OFF3 | 3:00 | — |
| DL-09 The Slipping Cage | DL-08 | 97.6 to 118.8 | `art/cage`, then `art/dl04` (tunnel side), moved by OFF4 | 2:00 | — |
| DL-10 Up Only | new in pass 3 | 118.8 to 127.9 (ring C's level) | `art/pass3/build_up_only.py` | 2:30 | — |
| DL-11 The Child at the Address | DL-09 | 127.9 to 170.1 | `art/dl05`, moved by OFF5 | 3:30 | — |

The lore dressing across scenes 1 to 9, the cage's readability pieces and the interactables' new materials are
`art/pass3/build_lore.py`'s. The estimates are first-time play from `docs/chapter1_plan.md` and
`docs/chapter1_pass3_plan.md`, not measurements. Pass 3's simulated timings are pending; the pass 2 runs
(`tools/sim/README.md`) predate the new scenes.

The code keeps its original module names, so they use the old numbers: `art/dl02` and `updateDL02` are DL-03 (and the
start of DL-04), `updateDL03` is DL-06 and DL-07, `updateDL04` is DL-08 and the tunnel and balcony of DL-09, and
`updateDL05` is DL-11. The rework (the scenes added then, the reworked DL-01, DL-08 and DL-11, and the letters) is the
Chapter 1 module before `const HINTS`. Pass 2 (`docs/chapter1_pass2_plan.md`) follows it there: the curiosities
(`CURIOS`), the White (`WATERS`, `updateWhite`), ring C (`updateRingC`), the hazards (`updateHazards`) and deaths
(`DEATH`, `die`). Its props, hazards and D-17's clips for them come from `art/pass2`, and the White from `art/white`.
Pass 3 is in the same module: the Ration Hall (`RATION5`, `RH5`, `updateWinch5`), Up Only (`UPONLY`, `UO`,
`updateAct10`, `updateUpOnly`), the cage's readability (`BalanceNeedle` and the pawl lever in `updateCage`), C-114's
shut door (`C114DOOR`, `KNOCK5_X`) and the light zones (`lightZoneFor`).

**Light zones.** Each region's lights are switched on only while D-17 is in it. Pass 3 adds two zones inside regions:
in the Ration Hall (from 47.4) its own lights (the counter's flickering strip light, the shrine's candles, a vent's
grey daylight, the kitchen's fill) replace DL-01's and the Sorting Hall's, long out of sight; in Up Only (from 117.8)
its own (the failing pendant, the two UP lamps, the crank's work lamp, the car's lamp, the cold light down the
counterweight's shaft) replace the goods hall's and the cage's.

**Interactables without red** (`docs/direction.md`). Red no longer says "use me". What D-17 can use is shown by wear
(grips and handles worn bright through tired paint: `HandledSteel`, `HandledBrass`, `WornIron`, `WornStrap`), by the
scene's light and by motion and sound. Red is kept for what the world itself painted red: the franking press's hazard
bands. The curiosities' red tags are gone.

## DL-01 The Wake (plan estimate 2:00)

1. **Opening, 20 s.**
   - D-17 wakes in the cradle. The parcel lamp, the relay pulses he answers, sparks, the work lamp, grit, then the camera move.
   - Skip appears after 1.5 s.
2. **Curiosities by the cradle.** All optional (see Curiosities).
   - The parcel scale, the first: its Use glyph shows as soon as he is near, so the player learns that props can be
     used. He steps up, the needle swings, and a POSTAGE DUE ticket pops up for him to read. Stepping on it without
     Use still swings the needle.
   - The pull-cord lamp. He tiptoes up, tugs the cord, and the lamp warms the alcove, revealing a depot route map
     (depot, homes, school, works, ward, then up).
   - The dispatch board: he finds his own route card (C-114) in the rack under it and taps his label.
3. **Shutter.**
   - He crouches automatically under it.
   - Use on the T-handle: two heaves, the latch gives, the counterweight drops and the shutter swings up. He flinches.
4. **Fallen conveyor (0.22 m).** The first jump.
5. **The depot cart and the trench.**
   - The drain trench is too wide to jump and too deep (0.8 m) to climb out of. Drop in and he flinches, and he is
     back at the checkpoint.
   - Use at the cart's red push bar and push it right. It rolls to the edge and drops in, and becomes the bridge.
   - Step down onto it and climb out on the far side. The cart (0.55 m) can also be climbed before it is pushed.
6. **The hall.** The camera pulls back to show the scale: a gantry, columns, a huge backlit sorting carousel,
   chutes, light shafts, a slow searchlight, swaying parcel hooks, a sparking live cable and a steam vent.
7. **Bulkhead.**
   - Use the red crank wheel. D-17 turns his back to the camera and hauls it hand over hand, five strokes, as the door
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

**Hints:** after about 5 s idle near the next useful thing, D-17 looks at it; at about 10 s he leans in. With the
stuck-prompt option on, a key glyph appears at about 18 s.

## DL-02 The Sorting Hall (plan estimate 1:45)

1. **Out of the passage.** He steps out into the hall where post came in by tube. The lamp over the gantry door at the
   far end is the brightest point. Behind him, left of the doorway, a hand franker (optional): he franks his own
   claw, RECEIVED, and the stamp stays on it.
2. **The franking press.** Between the passage and the tube, a press still stamps its routine every 2.6 s, over the
   only way on. Its lamp blinks before each stroke. Walk under it while it is up; caught under it, he is crushed
   (see Danger).
3. **The tube.** The first time he passes the tube station, its cup drops an old letter onto the lane: the first
   undelivered letter. A red mail slot stands a few steps on (see Undelivered letters).
4. **The tea corner.** Mugs on numbered hooks, one gone; the courier-of-the-year board, its last frame a pale
   silhouette; a wordless notice that ring C deliveries stopped in R.Y. 42, with a water drop. On the couriers'
   shelf, his own mug (optional): he lifts it as if to drink, can't, and puts it back carefully.
5. **The table.**
   - The way on is a gantry over a long sorting table. A collapsed pigeonhole wall blocks the floor.
   - The table top (0.75 m) is just out of a jump's reach.
   - Use to lift the parcel box (red strap), carry it to the table's foot, and Use again to set it down.
   - Hop onto the box, climb onto the table, then up to the gantry (1.35 m).
6. **The gantry.** Along it over the wreck to the lit doorway, and down into the weight room (DL-03).

Only the press can kill here; he is back just out of the passage.

## DL-03 The Weight of the Job (plan estimate 2:30)

1. **The weighing room.** Standing on the floor plate lifts the gate, and stepping off drops it. A gauge on the gate post
   reads the load on the plate, and a sign shows the rule. Wet drag marks run from a floor drain across the room and
   back: the White's first sign.
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
   bitten, not cut. Use at its red tow loop and drag it, walking backwards, slowly, onto the plate. Use or Jump lets
   go.
4. **The cradle.** Its arms close on the courier and seat it. Its lamps flicker weakly, then hold, and the door stays
   open. He lays a claw on its head (`TouchHead`), once, and walks on through a service passage into the scanner
   corridor.
   - Optional, once the courier is seated: back at the empty slot under the chalk flowers (41.08), Use, and he sits
     in it for a moment.

## DL-05 Return to Sender (plan estimate 2:45)

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
   - Stop the belt (red lever), throw the points (red lever on a yellow stand), restart the belt, and board at the dock.
     A chase of green lamps along the ramp shows the way the points now send the carriers.

Once the belt runs with the points set to the ramp, the game counts the rest of this space as DL-06.

## DL-06 The Heap (plan estimate 2:30)

1. **Up, for nothing.** He rides up the service ramp over the pit and hops out at the landing. The empty carrier sinks
   back down through the return slot. A counterweighted gate closes the gallery a few steps on; its chain runs over a
   drum in the roof to a bucket hanging at the ramp's head.
2. **Back down.** Walk off the gallery's left end and he sits into a parcel slide back down to the sorting floor.
3. **The delivery.** The gate needs both red-bailed sorting weights in its bucket.
   - One stands beside the dock; the other at the far end of the floor by the pit edge, where the slide puts him
     down. On the floor they are low obstacles to hop.
   - Lift one, carry it to the dock, and Use while a carrier waits there: he sets it in.
   - With the points on the ramp, the carrier climbs and tips the weight into the bucket. The camera widens to watch
     the climb. One weight lifts the gate half way, and it stalls with a strain; the second lifts it all the way.
   - The first time a weight drops into the bucket while he is on the floor, something pale rolls once in the dark
     water of the sump under the chute, and is gone. Running near the sump draws it again.
   - A weight sent to the chute is lost with the post, and back where it stood 4 s later. Riding a loaded carrier up
     himself also works.
4. **Up again.** Ride the next carrier up and walk under the gate.
5. **The gallery.** A letter caught on the rail in a shaft of light falls at his feet as he passes (optional).
   - The stopped clock (optional): Use, and he winds it. It ticks for a minute or so.
   - Walk past the old sorting desk and the day board. The walkway panel before the residential access doorway
     sags and creaks under him, and once he is past it, it gives way and falls. There is no way back.
   - On through the doorway into DL-07.

## DL-07 The Handbrake (plan estimate 3:00)

1. **Goods Lift 2.**
   - The goods hall ends in an open shaft, flooded to 1.75 below the landing, with the platform at the bottom, under
     the water. The first time the platform rises, something pale surfaces below it and sinks.
   - A pan in the floor drives the head drum: load on it raises the platform. D-17 alone raises it halfway; stepping off drops it with a crash.
   - The goods trolley, still loaded with ballast, raises it all the way. Use at its push bar, then push it onto the pan.
2. **The pawl.**
   - Step onto the platform as it is, and it drops under him; he scrambles back (`Teeter`).
   - Use the red pawl lever at the shaft's edge, behind the lane. Below the landing the dog only rattles on the rack.
     At the landing it drops home with a click.
3. **The far rail.**
   - A safety rail on the far landing is too high to climb from the platform.
   - With the pawl set, the platform no longer needs the trolley. Push the trolley off the pan, across the platform to
     the rail, climb onto it and over the rail.
   - **The White's first meeting.** Running, or landing from a jump, over the shaft is loud: the White comes up and
     slaps the water, and he is knocked back off his feet, unhurt. Walking (Shift or B) is quiet. Falling into the
     sump is a death.
4. **The returns belt.**
   - On the far landing (a checkpoint), the belt starts after a bell, a beacon and the klaxon.
   - It runs against him, bringing crates of returned post down from the rings: hop the low ones, climb the tall ones.
     At worst it carries him back to the landing.
   - The depot's relay pulse fades out as he climbs it.

## DL-08 The Slipping Cage (plan estimate 2:00)

1. **The climbs.** Off the belt's top end, three climbs to an upper landing at the edge of a shaft (a checkpoint).
   Across the shaft and lower down, a lit landing leads on.
2. **The counterweight.**
   - He walks into the open freight cage and it drops a hand's breadth under him: the brake squeals and holds, an
     alarm bell rings, and the chain hauls it back up. He has to step out and in again to try.
   - The counterweight beside it has lost its top slab, and two weight plates lie on the landing. Lift one, carry it
     to the counterweight, and Use: he turns and sets it in the tray. With one plate the cage dips less; with both,
     it takes him.
3. **The cage.**
   - It starts down by itself. It lets down, shudders, then slips, and he braces (`CageBrace`).
   - It catches once just above the lit landing, hangs for a moment, then slips again.
   - Use throws the red pawl lever on the cage's post. Thrown between the catch and the landing, the pawl bites and the
     cage settles at the landing, and he bounces proudly.
   - Too early, it rattles and the lever springs back; throw it again. Too late, the cage drops onto the buffers in
     its flooded sump: a death, and he is back on the upper landing. Once both plates are in, they stay in.
4. **The cable.** Past the lit landing (a checkpoint), the antechamber's floor is wet, and a downed cable arcs over
   it in two places in turn, every 2.4 s, each with a crackle first. Cross the first once it dies, wait on the dry hatch
   cover between them, then cross the second. The first touch only throws him back; after that, a touch is a death.
5. **The tunnel.**
   - Past the RESIDENTIAL ACCESS sign to the tunnel mouth, where he looks back at the depot (`LookBack`).
   - He plays the whole chalk hopscotch (`HopscotchLong`, 12 s): he checks that nobody is watching, wobbles on 6,
     cheers on HOME, and hops back. Moving left or jumping in its first 3 s cancels it. Use on the chalk afterwards
     plays it again.
6. **The refuge.**
   - The tunnel opens onto a balcony high in the atrium: three rings of homes around a void.
   - He stops at the rail (`Awe`), the camera cranes up and out, and the music swells.
   - The atrium is the refuge's underground city: a chasm dug into the rock, the poorest industrial levels at the
     bottom, the upper city rising into the haze.
   - On the balcony, a coin viewer (optional): he has no coin, presses the plunger anyway, and looks through it at the
     lit upper city.
   - He walks on slowly to the stair down to ring C, and into DL-09.

The tunnel and the balcony are built with DL-07's set (`art/dl04`); the game counts them as DL-08, as the plan does.
The counterweight's plates, the cage's sump and the antechamber's cable are `art/pass2`'s.

## DL-09 The Child at the Address (plan estimate 3:30)

1. **Ring C.**
   - The stair brings him down to ring C's ledge. The lane is sealed (RING C SEALED · R.Y. 43); crouch under the barricade.
   - Ring C is a street, abandoned and nearly dark: homes behind the lane (through C-108's dim window, a table still
     set for a meal; C-110; C-112, boarded and taped), a kerb and the roofs of the lower row in front, a cable of bulbs
     with two still burning, washing on its lines, and ring B's tier above in the haze.
2. **The flood.**
   - The lane's back half has sunk into deep water along C-108 and C-110, and at the narrow point by C-110 the whole
     lane has. The White lives in it: as he comes along, something pale surfaces far off and sinks.
   - Running or landing near the water is loud; walking is quiet. Heard, the White comes and surfaces, and if he is
     on the bank within reach, it takes him (see The White).
   - He won't step into the water at the narrow point: a spark at his foot, and he jerks back.
   - **The doorbell:** C-108's red bell, at the water's near end. Use rings it for 12 s, and the White swims to
     C-108's sunken step and noses at it.
   - **The duct:** Use at the fallen duct's red strap and push it right. It drops into the narrow point with a loud
     splash and becomes the bridge. While the bell rings, the splash doesn't turn the White; otherwise it brings it.
   - **Walk across.** Running near the White breaks the bell's hold.
   - **Or the junction box** by C-110 (optional): its lever shorts the live cable into the water, and the White
     flees for 20 s.
   - As he reaches the bridge, a letter slips out of C-110's slot onto it (optional).
3. **The square.** The noticeboard with the evacuation notice and the children's drawings of the White, a bench, a
   dry fountain, a swing, and ring C's red mail slot.
4. **C-114.** He steps up to the front door, knocks twice (`Knock`), and waits. Nobody. Through the door, the street
   wall fades and the house is seen in section, like a dollhouse.
5. **The home.**
   - The hall, with a small yellow raincoat on the hooks. A light switch (optional): click, and the hall bulb comes on.
   - The kitchen and living room: a table with three chairs, one a child's. A radio (optional): static, then half a
     verse of a children's song, and he does a little two-step.
6. **The bedroom.**
   - Passing the bed, he sits the patched rabbit up and pats it (`Straighten`). Any move cancels it.
   - A low desk has fallen against the back wall, over the forwarding terminal. Use at its red grip bar and drag it
     clear. Pencil growth marks and a crooked carved tree are behind it, and the music comes in.
7. **The terminal.** Use at it. He presents his chest window to the reader (`Present`), his three lamps answer its
   three, and the screen reads NO ONE AT THIS ADDRESS, then FORWARD TO SCHOOL, RING B. His label is stamped.
8. **Out the back.** The back door opens onto a service passage and a sign for the school. The end card.

## Undelivered letters

Chapter 1's secret, and entirely optional: the story reads without them.
- **Three letters:** one dropped by the tube in DL-02, one caught on the gallery rail in DL-06, and one slipped out of
  C-110's slot in DL-09.
- **Three red mail slots:** `MailSlot2` (DL-02), `MailSlot6` (DL-06, by the old sorting desk) and `MailSlot9`
  (DL-09, in the square before C-114).
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
| DL-01 | Dispatch board | 1.0 | His own route card, C-114; he taps his label. |
| DL-02 | Hand franker | 12.8 | He franks his own claw: RECEIVED. The stamp stays. |
| DL-02 | His mug | 15.2 | He lifts it, can't drink, and puts it back carefully. |
| DL-04 | The empty rack | 41.08 | Once the courier is seated: he sits in the slot under the chalk flowers. |
| DL-05 | The sorter's chair | 48.8 | He climbs up and sits; the cushion fits him. |
| DL-06 | The stopped clock | 61.38, on the gallery | He winds it; it ticks for about 75 s. |
| DL-08 | Hopscotch | 96.15 | Once he has played it: the long hopscotch again. |
| DL-08 | Coin viewer | 102.6 | No coin, the plunger anyway, and a long look at the lit upper city. |
| DL-09 | Hall light switch | 125.72 | Click: the hall bulb comes on and stays on. |
| DL-09 | Radio | 130.0 | Static, then half a verse of a children's song. |

- **The early ones** (the scale, the cord lamp, the dispatch board, the franker and the mug) are made obvious: a warm
  pool of light with a faint glow behind and a small red tag (not the cord lamp), and as he passes one he turns his
  head to it, until he has used it. The scale shows its Use glyph at once.
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
| The gallery collapse | DL-06 | 66.95 to 68.05 | Sags under him, then falls once he is past. Not lethal; no way back. |
| The shaft sump | DL-07 | 73.8 to 76.3 | The White slaps the water and knocks him back, unhurt (`Knockback`). Falling in is a death. |
| The cage crash | DL-08 | 89.2 to 90.8 | Onto the buffers in the sump: `DeathFall`, back at `cage`. |
| The tunnel cable | DL-08 | 93.04 to 93.44, 93.77 to 94.17 | Two arcs in turn every 2.4 s, a dry hatch between. The first touch in a game knocks him back; after that, `DeathShock`, back at `landing8`. |
| The lane | DL-09 | 112.95 to 117.6 | The White lunges and drags him under (`DeathGrabbed`), back at `ringc`. |

The older failures are unchanged and are not deaths: the trench (DL-01) and the chute (DL-05) fade back to the
checkpoint as before.

## The White

A pale, blind cave animal like a giant olm, about 2.5 m long, with feathery pink gills and no eyes
(`art/white/build_white.py`). It hunts by sound, never by sight, and never leaves the water.
- **Noise:** running near its water (within about 2.2 m), or landing from a jump, is loud. Walking (Shift, B, or a
  half-pushed stick) is quiet. A splash or a bell is louder still.
- **The hunt:** it patrols, hears, listens for a moment, swims to the sound with ripples ahead of it, and surfaces.
  If he is on the edge within reach, it strikes about a body length; otherwise it sinks after about 2 s and patrols
  again.
- **A bell** draws it and holds it while it rings (DL-09's doorbell, 12 s). A footstep doesn't turn it, but running
  near it does.
- **The shorted cable** (DL-09's junction box) sends it deep for 20 s, hearing nothing.
- **Each water has a part** (`WATERS` in the game): DL-06's heap sump, a glimpse (it rolls once and sinks); DL-07's
  shaft sump, a scare (a slap and a knockback); DL-09's lane, the hunt (it kills).
- **Its signs before it:** wet drag marks from a drain in DL-03, and the fallen courier's bitten leg in DL-04.
- **Clips:** `WhiteGlide`, `WhiteSwim`, `WhiteListen`, `WhiteSurface`, `WhiteSink`, `WhiteRoll`, `WhiteSlap`,
  `WhiteLunge`, `WhiteDrag` and `WhiteNose`. Its skin is pale and a little translucent, with a wet rim.

## Checkpoints

- DL-01: start, shutter open, the hall (across the trench), door open.
- DL-02: out of the passage.
- DL-03: the weight room's floor, and solved (the gate held open).
- DL-04: through the bay door.
- DL-05: scanned.
- DL-06: the gallery landing, and past the gate.
- DL-07: the goods hall, and the far landing (pawl set).
- DL-08: the shaft's edge (`cage`), the lit landing (`landing8`, new: once the cage is held there and he steps off),
  and the tunnel mouth.
- DL-09: through the seal, the bedroom (now at 131.1), and after the terminal (134.1).

A respawn fades out and back in about 1.3 s; a death cuts instead (see Danger). Authored moments play once: after a
respawn or a checkpoint reload, the ones already seen are skipped. Two solved states also outlive a respawn: both
plates in the counterweight's tray, and the tunnel cable's one free touch. Start over clears all of this.

## Camera, quirks and performance

- **Camera:** one continuous side-on shot. Its framing widens, closes in or rises as D-17 moves (wider over the hall
  and the rack reveal, wider again to watch a loaded carrier climb the ramp, holding the climbs, the shaft and the lit
  landing together for the cage), and pushes in a little for climbs and actions. Gameplay never takes it away.
  - Authored shots are kept for emotional beats, and blend in and out of the side view:
    - DL-04: the realisation among the couriers.
    - DL-05: the scan, the crane out over the pit, and the label close-up.
    - DL-08: the look back from the tunnel; the hopscotch (the long version: close and low while he checks nobody is
      watching, a crane up to about 45° over the whole court, then down and in for the cheer); the coin viewer
      (through the eyepieces, a 110 mm lens across the chasm to the lit upper city, swinging as he swings it); and
      the crane out over the atrium (the chapter's one wide shot).
    - DL-09: a held look at the growth marks (first time only), the terminal over his shoulder, and the rabbit.
  - On ring C's lane the framing is raised (2.15 m, looking down to 0.4 m) so the water and the White read. In C-114
    it frames the hall, the kitchen and living room, the bedroom and the back door in turn.
  - Cranks, levers, lifts, pawls, the cage and pushes all play in the side view.
  - Heavy impacts shake it a little; calm mode turns the shake off.
- **Quirks:** D-17 has short reactions for particular moments.
  - Proud: he bounces when the bulkhead opens, when the points are set to the ramp, and when the cage's pawl bites.
  - PeekDown: he peeks over the trench, the cart's far edge, the pit rail and Lift 2's shaft.
  - Startle: a slam or a crash close by (the weight room's gate, a carrier tipping at the chute, the lift platform).
  - Startle also when the cage hauls itself back up after dipping under him.
  - Knockback: thrown off his feet by the White's slap in DL-07 or the cable's first arc in DL-08.
  - Others: he stands to attention at the scanner, brushes himself off after the ride up, scrambles off the unlatched
    platform, braces in the slipping cage, flinches at the water, looks back at the depot, hops the chalk squares,
    stands in awe at the rail, knocks at C-114, sits the rabbit up and lays a claw on the seated courier's head.
  - Glance: passing an early curiosity he hasn't used yet, he turns his head to it.
- **Performance:** see the budget in `docs/direction.md`. The resolution adapts to the frame rate.

## Music

The score is in `assets/music/` and is composed and rendered by `art/music/compose_dl01.py` (see its
README). It is sparse:
- A cue for the wake.
- A quiet 48 s loop under play.
- A cello cue as he first walks into DL-01's hall.
- A short threshold cue as the bulkhead opens and D-17 walks through into DL-02.
- DL-03 and DL-04: a roll call when the rack lights come on, then a full swell as he walks in among the couriers.
- DL-05: the refusal, a swell over the pit, near silence for the label check, then the theme in F major.
- DL-07: a warm F major and the parcel's three notes when the pawl drops home.
- DL-08: `refuge`: near silence, then phrase B broadening into F major, peaking as the camera reaches its widest over the atrium.
- DL-09: `child`: when the desk clears the marks, the parcel's three notes become a lullaby on the music box, piano and strings.
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
the White's signs and D-17's knockback and death clips; `build_curios.py`: the curiosity props and clips) and
`art/white`. It writes `set`, `d17`, `couriers` (the dormant couriers' three poses and their rack slots) and `white`,
each as `.glb` and `.json`. A `.json` is split into parts of 10 MB of base64 (`pack_for_web`), so `set` is
`set.json`, `set.1.json` and `set.2.json`. `--blend <path>` also saves the Blender file.

`HOPSCOTCH_LONG` in the game copies the long hopscotch's root-motion numbers from `art/dl04/hopscotch_long.json`,
which `art/dl04/hopscotch_clip.py` writes. Keep them in step.

**Segment offsets.** The later stretches of the level sit further along x than where they were first built, so that new
scenes fit between them. `OFF2 = 13`, `OFF3 = 21` and `OFF4 = 30` are defined in both `build_dl01.py` and
`index.html`, and must be kept in step.
- `OFF2` moves the weight room and the racks hall (`art/dl02`, which applies it itself).
- `OFF3` moves the return line, the heap and the gallery (`art/dl03`) and Lift 2 and its belt (`art/dl04`).
- `OFF4` moves the tunnel and the city (`art/dl04`) and ring C (`art/dl05`).
- The new builders (`art/sorting_hall`, `art/racks`, `art/cage`, `art/pass2`) build in world coordinates, from the
  same offsets.

## Testing hooks

- **`window.__dl01`:** for automated traversal checks. It exposes:
  - the game state, `play(checkpoint)` to start at any checkpoint, `scene()` (the current scene's name), `near()`
    (what Use would do now) and `music()` (the cue playing);
  - `world` (the three.js scene) and `THREE`;
  - `letters` (`letterState`), `offsets`, the layout constants (`k`), and the carriers and crates;
  - pass 2: `pressT()` and `arcT()` (where the press and the tunnel cable are in their cycles), `k2` (`CW8`,
    `ARCS8`, `BELL9`, `JUNCTION9`, `PRESS2`, `SHAFT`), `white()` (its state, x, water and whether a bell holds it),
    `waters` (`WATERS`), `curios` (`curioFound`), `curioList()` (each curiosity's id, x, region, upper and early),
    and `die(how)` to kill him (`crush`, `shock`, `grabbed` or `fall`).
- **`window.__sim`:** test only. When it is set, a simulated player drives the game at a fixed 60 Hz, several steps per
  frame, rendering now and then. `tools/sim/` uses it to play the whole chapter (see its README).
- **Developer overlay:** ` shows the mode, frame rate, position, clip, checkpoint and current action.
