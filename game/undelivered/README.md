# Undelivered (DL-01 to DL-09): playable prototype

A browser-playable build of chapter 1, reworked into nine scenes and played as one continuous level with no cut
between them. It follows the chapter plan in `docs/chapter1_plan.md`, the scene plans in `docs/scenes/` and the
standing direction in `docs/direction.md`. It uses D-17 and the set from Blender, and the gameplay code mirrors the
mechanisms planned for the Unity build.

## Run locally

```sh
cd game/undelivered
python3 -m http.server 8765
# open http://127.0.0.1:8765/index.html
```

three.js 0.169.0 loads from jsDelivr. The models are in `assets/` as `.glb`, and also as `.json`
(base64-wrapped GLB), because the artifact host serves `.json` but not `.glb`.

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

The nine scenes run left to right along one lane. The pause card shows the scene D-17 is in (`sceneName()` in the
game).

| Scene | Was | World x | Built by | Plan estimate |
|---|---|---|---|---|
| DL-01 The Wake | DL-01, reworked | 0 to 12 | `art/dl01` | 2:00 |
| DL-02 The Sorting Hall | new | 12 to 25 | `art/sorting_hall` | 1:45 |
| DL-03 The Weight of the Job | DL-02 | 25 to 30.6 (the gate) | `art/dl02`, moved by OFF2 | 2:30 |
| DL-04 The Racks | new | 30.6 to 47.9 | `art/dl02`'s racks hall, then `art/racks` | 2:30 |
| DL-05 Return to Sender | DL-03 | 47.9 to 68.5, shared with DL-06 | `art/dl03`, moved by OFF3 | 2:45 |
| DL-06 The Heap | new | the same space, then the gallery | `art/dl03`, moved by OFF3 | 2:30 |
| DL-07 The Handbrake | DL-04, reworked | 68.5 to 85.6 | `art/dl04` (belt side), moved by OFF3 | 3:00 |
| DL-08 The Slipping Cage | new | 85.6 to 106.75 | `art/cage`, then `art/dl04` (tunnel side), moved by OFF4 | 2:00 |
| DL-09 The Child at the Address | DL-05, reworked | 106.75 to 127.2 | `art/dl05`, moved by OFF4 | 3:30 |

The estimates are first-time play from `docs/chapter1_plan.md`, not measurements. Playtest timings are pending.

The code keeps its original module names, so they use the old numbers: `art/dl02` and `updateDL02` are DL-03 (and the
start of DL-04), `updateDL03` is DL-05 and DL-06, `updateDL04` is DL-07 and the tunnel and balcony of DL-08, and
`updateDL05` is DL-09. The rework (the new scenes, the reworked DL-01, DL-07 and DL-09, and the letters) is the
Chapter 1 module before `const HINTS`.

## DL-01 The Wake (plan estimate 2:00)

1. **Opening, 20 s.**
   - D-17 wakes in the cradle. The parcel lamp, the relay pulses he answers, sparks, the work lamp, grit, then the camera move.
   - Skip appears after 1.5 s.
2. **Curiosities by the cradle.** All optional.
   - The pull-cord lamp, the first use of Use. He tiptoes up, tugs the cord, and the lamp warms the alcove,
     revealing a depot route map (depot, homes, school, works, ward, then up).
   - The parcel scale: step on it and its needle swings round to postage due.
   - The dispatch board, with his last route chalked on it.
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
   far end is the brightest point.
2. **The tube.** The first time he passes the tube station, its cup drops an old letter onto the lane: the first
   undelivered letter. A red mail slot stands a few steps on (see Undelivered letters).
3. **The tea corner.** Mugs on numbered hooks, one gone; the courier-of-the-year board, its last frame a pale
   silhouette; a wordless notice that ring C deliveries stopped in R.Y. 42, with a water drop.
4. **The table.**
   - The way on is a gantry over a long sorting table. A collapsed pigeonhole wall blocks the floor.
   - The table top (0.75 m) is just out of a jump's reach.
   - Use to lift the parcel box (red strap), carry it to the table's foot, and Use again to set it down.
   - Hop onto the box, climb onto the table, then up to the gantry (1.35 m).
5. **The gantry.** Along it over the wreck to the lit doorway, and down into the weight room (DL-03).

Nothing here can fail.

## DL-03 The Weight of the Job (plan estimate 2:30)

1. **The weighing room.** Standing on the floor plate lifts the gate, and stepping off drops it. A gauge on the gate post
   reads the load on the plate, and a sign shows the rule.
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
3. **The fallen courier.** One of his own lies fallen from its rack by the lane. Use at its red tow loop and drag it,
   walking backwards, slowly, onto the plate. Use or Jump lets go.
4. **The cradle.** Its arms close on the courier and seat it. Its lamps flicker weakly, then hold, and the door stays
   open. He lays a claw on its head (`TouchHead`), once, and walks on through a service passage into the scanner
   corridor.

## DL-05 Return to Sender (plan estimate 2:45)

1. **The scanner.**
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
3. **The delivery.**
   - Two red-bailed sorting weights stand beside the dock. On the floor they are low obstacles to hop.
   - Lift one, carry it to the dock, and Use while a carrier waits there: he sets it in.
   - With the points on the ramp, the carrier climbs, tips the weight into the bucket, and the gate ratchets up.
     The camera widens to watch the climb.
   - A weight sent to the chute is lost with the post; another stands by the dock 4 s later. Riding the loaded
     carrier up himself also works.
4. **Up again.** Ride the next carrier up and walk under the gate.
5. **The gallery.** A letter caught on the rail in a shaft of light falls at his feet as he passes (optional). Walk
   past the old sorting desk, the stopped clock and the day board to the residential access doorway, and on into
   DL-07.

## DL-07 The Handbrake (plan estimate 3:00)

1. **Goods Lift 2.**
   - The goods hall ends in an open shaft with the platform at the bottom.
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
4. **The returns belt.**
   - On the far landing (a checkpoint), the belt starts after a bell, a beacon and the klaxon.
   - It runs against him, bringing crates of returned post down from the rings: hop the low ones, climb the tall ones.
     At worst it carries him back to the landing.
   - The depot's relay pulse fades out as he climbs it.

## DL-08 The Slipping Cage (plan estimate 2:00)

1. **The climbs.** Off the belt's top end, three climbs to an upper landing at the edge of a shaft (a checkpoint).
   Across the shaft and lower down, a lit landing leads on.
2. **The cage.**
   - He walks into the open freight cage and it starts down by itself. It lets down, shudders, then slips, and he
     braces (`CageBrace`).
   - It catches once just above the lit landing, hangs for a moment, then slips again.
   - Use throws the red pawl lever on the cage's post. Thrown between the catch and the landing, the pawl bites and the
     cage settles at the landing, and he bounces proudly.
   - Too early, it rattles and the lever springs back; throw it again. Too late, the cage drops onto the buffers, and
     the counterweight hauls it back to the top with him in it to try again. Nothing fades.
3. **The tunnel.**
   - Past the RESIDENTIAL ACCESS sign to the tunnel mouth, where he looks back at the depot (`LookBack`).
   - He hops the chalk hopscotch (`Hopscotch`).
4. **The refuge.**
   - The tunnel opens onto a balcony high in the atrium: three rings of homes around a void.
   - He stops at the rail (`Awe`), the camera cranes up and out, and the music swells.
   - The atrium is the refuge's underground city: a chasm dug into the rock, the poorest industrial levels at the
     bottom, the upper city rising into the haze. He walks on slowly to the stair down to ring C, and into DL-09.

The tunnel and the balcony are built with DL-07's set (`art/dl04`); the game counts them as DL-08, as the plan does.

## DL-09 The Child at the Address (plan estimate 3:30)

1. **Ring C.**
   - The stair brings him down to ring C's ledge. The lane is sealed (RING C SEALED · R.Y. 43); crouch under the barricade.
   - Ring C is abandoned and nearly dark: a failing bulb, shuttered homes, and a dried tideline along the walls.
     Through C-108's dim window, a table still set for a meal; C-112's door is taped shut.
2. **The flood.**
   - Halfway along, the lane sinks into standing water. He won't step in: a spark at his foot, and he jerks back.
   - Use at the fallen duct's red strap and push it right. It drops into the water and becomes the bridge.
   - As he reaches it, a letter slips out of C-110's slot onto the duct (optional). Ring C's red mail slot is just
     beyond.
3. **C-114.** The last door is open. He steps up to it and knocks twice (`Knock`), and waits. Nobody.
4. **The bedroom.**
   - Passing the bed, he sits the patched rabbit up and pats it (`Straighten`). Any move cancels it.
   - A low desk has fallen against the back wall, over the forwarding terminal. Use at its red grip bar and drag it
     clear. Pencil growth marks and a crooked carved tree are behind it, and the music comes in.
5. **The terminal.** Use at it. He presents his chest window to the reader (`Present`), his three lamps answer its three,
   and the screen reads NO ONE AT THIS ADDRESS, then FORWARD TO SCHOOL, RING B. His label is stamped.
6. **Out the back.** The back door opens onto a service passage and a sign for the school. The end card.

## Undelivered letters

Chapter 1's secret, and entirely optional: the story reads without them.
- **Three letters:** one dropped by the tube in DL-02, one caught on the gallery rail in DL-06, and one slipped out of
  C-110's slot in DL-09.
- **Three red mail slots:** `MailSlot2` (DL-02), `MailSlot6` (DL-06, by the old sorting desk) and `MailSlot9`
  (DL-09, on ring C's lane).
- Use near a letter on the floor to pick it up (`PickUpLetter`). Use at a slot while holding one to post it
  (`PostLetter`): the slot's stamp lamp blinks, with a knock and a chirp.
- A letter can be posted at any slot, not only its own.
- What he has picked up or posted (`letterState`) is kept through respawns and checkpoint reloads. Start over clears it.

## Checkpoints

- DL-01: start, shutter open, the hall (across the trench), door open.
- DL-02: out of the passage.
- DL-03: the weight room's floor, and solved (the gate held open).
- DL-04: through the bay door.
- DL-05: scanned.
- DL-06: the gallery landing, and past the gate.
- DL-07: the goods hall, and the far landing (pawl set).
- DL-08: the shaft's edge, and the tunnel mouth.
- DL-09: through the seal, the bedroom, and after the terminal.

A respawn fades out and back in about 1.3 s. Authored moments play once: after a respawn or a checkpoint reload,
the ones already seen are skipped. Start over clears this.

## Camera, quirks and performance

- **Camera:** one continuous side-on shot. Its framing widens, closes in or rises as D-17 moves (wider over the hall
  and the rack reveal, wider again to watch a loaded carrier climb the ramp, holding the climbs, the shaft and the lit
  landing together for the cage), and pushes in a little for climbs and actions. Gameplay never takes it away.
  - Authored shots are kept for emotional beats, and blend in and out of the side view:
    - DL-04: the realisation among the couriers.
    - DL-05: the scan, the crane out over the pit, and the label close-up.
    - DL-08: the look back from the tunnel, and the crane out over the atrium (the chapter's one wide shot).
    - DL-09: a held look at the growth marks (first time only), the terminal over his shoulder, and the rabbit.
  - Cranks, levers, lifts, pawls, the cage and pushes all play in the side view.
  - Heavy impacts shake it a little; calm mode turns the shake off.
- **Quirks:** D-17 has short reactions for particular moments.
  - Proud: he bounces when the bulkhead opens, when the points are set to the ramp, and when the cage's pawl bites.
  - PeekDown: he peeks over the trench, the cart's far edge, the pit rail and Lift 2's shaft.
  - Startle: a slam or a crash close by (the weight room's gate, a carrier tipping at the chute, the lift platform).
  - Others: he stands to attention at the scanner, brushes himself off after the ride up, scrambles off the unlatched
    platform, braces in the slipping cage, flinches at the water, looks back at the depot, hops the chalk squares,
    stands in awe at the rail, knocks at C-114, sits the rabbit up and lays a claw on the seated courier's head.
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
`art/dl05`, `art/sorting_hall`, `art/racks` and `art/cage`. It writes `set`, `d17` and `couriers` (the dormant
couriers' three poses and their rack slots), each as `.glb` and `.json`. `--blend <path>` also saves the Blender file.

**Segment offsets.** The later stretches of the level sit further along x than where they were first built, so that new
scenes fit between them. `OFF2 = 13`, `OFF3 = 21` and `OFF4 = 30` are defined in both `build_dl01.py` and
`index.html`, and must be kept in step.
- `OFF2` moves the weight room and the racks hall (`art/dl02`, which applies it itself).
- `OFF3` moves the return line, the heap and the gallery (`art/dl03`) and Lift 2 and its belt (`art/dl04`).
- `OFF4` moves the tunnel and the city (`art/dl04`) and ring C (`art/dl05`).
- The new builders (`art/sorting_hall`, `art/racks`, `art/cage`) build in world coordinates, from the same offsets.

## Testing hooks

- **`window.__dl01`:** for automated traversal checks. It exposes the game state, `play(checkpoint)` to start at
  any checkpoint, `scene()` (the current scene's name), `letters` (`letterState`), `offsets`, the layout constants
  (`k`), the carriers and crates, `near()` (what Use would do now) and `music()` (the cue playing).
- **`window.__sim`:** test only. When it is set, a simulated player drives the game at a fixed 60 Hz, several steps per
  frame, rendering now and then. `tools/sim/` uses it to play the whole chapter (see its README).
- **Developer overlay:** ` shows the mode, frame rate, position, clip, checkpoint and current action.
