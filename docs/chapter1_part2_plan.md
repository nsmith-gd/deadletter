# Chapter 1 Attendance, part 2: DL-15 to DL-17

**Status:** built, 21 October 2026 (pass 9). The second half of Chapter 1, after `docs/chapter1_attendance_plan.md` (DL-12
to DL-14). Same standard: multi-step puzzles built from known relationships plus one twist, a
secret room, tableaux, voice letters. Story follows `docs/full_game_plan.md`: the school of the last childhoods, where Mara and her two friends
were loved, confined and curious.

**Coordinates:** game x from `OFF6 = 200`; floor at height 0; the lane at z 0. Blender (x, y, z) becomes game
(x, z, −y): **Blender +y is away from the camera**. Every scene module builds in final world coordinates, as
`art/ch1/dl12.py` to `dl14.py` do, and is called by `art/ch1/build_attendance.py` as `build_set(dl01, m, coll)`.

**Rules from the play tests that every scene keeps:**
- No two interactions answer Use in the same place (the game audits this: `tools/sim/audit_near.mjs`). Interaction
  spots below are at least 0.5 m apart unless they can never be live at the same time.
- Anything the player must notice is lit and in the side view's frame, not hidden behind a desk or in the dark.
- Climbs: D-17 steps up 0.07 without a climb; climbs (mantles) 0.24 to 0.62; with a jump catches a ledge up to about
  1.1 above the floor he jumps from. He stands 0.76 tall, 0.58 crouched, 0.34 wide.

**What the chapter says, in these three scenes:** the school kept its routines for children who had stopped coming.
D-17, following Mara's trail, sits in her place, watches the stand-in pupils go to a playground that is a storage rack,
and finds where she went next: not out of the school's rules but into a workshop, where an old volunteer turned her
crooked tree into an irrigation drawing and put her name down for the Works.

## The way in: the duct from DL-14

DL-14's hatch (x 239.25 to 240.15, sill 2.15) opens into a duct that runs back into the wall and right, behind
DL-14's back wall and end wall, and comes out high in DL-15's back wall. In play: he crawls into the hatch, the camera
follows him right behind the wall (hidden, heard crawling), and he comes out of DL-15's hatch onto the sick bay balcony.
No cut. DL-15's module builds its end of the duct: a dark box behind its hatch, Blender y 1.4 to 2.6.

## DL-15 One Pupil Missing (x 248 to 264): developed puzzle, about 5 minutes

**The room:** Class 6, the last class. A small classroom built for forty: rows of empty desks fade into the dark at
the back; three places in the front row are kept ready. A raised sick bay balcony over the door he came in by, a small
pupil lift down from it, an attendance board with three lamps, and a door out that opens only on dismissal.

**Layout (game x; Blender y is depth, +y away from the camera):**

| x | What |
|---|---|
| 248.0 to 248.15 | The left wall (DL-14's end wall is at 247.85; leave the gap dark). |
| 248.55 to 249.35 | **The hatch** in the back wall (y 1.4), sill 1.6, head 2.4: the duct's end, dark inside. |
| 248.15 to 251.4 | **The sick bay balcony**, top **1.6**, lane-deep (y −0.3 to 1.4), iron framed, timber deck. Open at the front and at its right end (no railing across the lane). Under it, at floor level, a low dark space (clear height 1.5). |
| on the balcony | The sick bay: a child's cot at the back (x 249.6 to 250.9, y 0.9 to 1.35), a folding screen, a drip of a washbasin, notices. The rail stub (below) runs along y 0.55 from 248.4 to 251.4. |
| 249.9 | **`Att15FigB`**, a teaching figure on a rail stand, on the balcony's rail stub (origin on the rail top, z 1.6 + rail height). The missing pupil, in the sick bay. |
| 251.4 to 252.4 | **The pupil lift** (`Att15Lift`): an open platform, lane-deep (y −0.3 to 0.9), deck built at the **top, 1.6**, with its own short length of rail at y 0.55. Two guide posts at the back (y 0.95), a counterweight shaft behind them against the back wall (`Att15LiftCW`, up when the lift is down). A folding gate on its right edge (`Att15LiftGate`), shut while the lift is up. A sign on the post: PUPIL LIFT · NO PUPIL UNACCOMPANIED. Two small lamps on the post at about 0.5 above the deck: PUPIL (`Att15LampPupil`, green-white) and ESCORT (`Att15LampEscort`, amber). |
| 251.4 to 263.4 | **The floor rail** at y 0.55 (two low rails, top 0.03, in a timber floor channel), from the lift to the end wall. It passes through the end partition under a flap (`Att15Flap`) into DL-16. |
| 253.2, 254.6 | **Seats S1 and S2**: front-row places at the rail. Each: a child's desk behind the rail (y 0.8 to 1.2, top 0.55), its chair *missing* and replaced by a brass seat-sensor plate set in the rail channel, with a small brass name holder on the desk front (chalked card: R. ABEL; T. ORME). |
| 256.0 | **Seat S3, Mara's place.** Her desk (same as the others) with a crooked tree carved into the lid (a knot in one branch), visible from the camera (the lid slopes toward us). Her chair pulled out and turned, at y 0.3, just behind the lane, as if she had got up in a hurry: **`Att15Chair`** (static; D-17 sits on it; seat top 0.30). The name card: M. D. |
| 253 to 262, y 1.3 to 3.6 | The rest of the class: four more rows of desks and chairs going back into the dark (static, low detail, dusty, some chairs on desks), so the room reads as built for forty. |
| 257.4 to 258.8, height 1.7 to 2.5 | **The attendance board** on the back wall (y 1.38): CLASS 6 · PRESENT, three lamps in a row (`Att15Lamp1`, `Att15Lamp2`, `Att15Lamp3`, warm white) with the three names chalked under them (R. ABEL, T. ORME, M. D.), a bell above (`Att15Bell`, static). |
| 258.9 to 261.6 | The blackboard on the back wall. Chalk: a headcount ON ROLL with 31, 9 and 4 crossed out and **3** written smaller; today's date-line rubbed out; a half-cleaned diagram of a tree (straight, tall). The Steward's portrait above it (reuse the order-era portrait if it can be imported, else a pale rectangle where it hung). |
| 259.2 | **`Att15FigA`** on the floor rail at the blackboard, as if at the board for a lesson. |
| 261.8 to 262.6 | The teacher's desk against the back wall (not in the lane), a chair, a register book open on it. |
| 262.8 to 263.9 | The end partition (x 263.75 to 263.9) with **the class door** (`Att15Door`) in the lane (y −0.3 to 0.55, height 2.0), shut, opening away into DL-16 (hinged at its back edge, x 263.9, y 0.55; swings 95° toward +x). Over it: DISMISSAL. Beside it, low on the rail at y 0.4 to 0.72, **the flap** (`Att15Flap`, 0.32 wide, 1.05 high), hinged at its top edge, swings up toward +x as a figure passes. |

**The secret room: under the balcony** (floor level, x 248.3 to 251.2, y 0.4 to 1.4, behind a hanging blanket at
y 0.35 that is pulled half aside; entered at x 249.8):
- Mara's hiding place, from when she was a protected pupil sent to the sick bay: a nest of a blanket and a cushion, a
  torch, a biscuit tin, pencil stubs, and the underside of the balcony deck covered with crooked trees in pencil.
  A copper pipe runs along the back wall here, with a cup held to it (she listened to the pipes).
- A **voice-card player** on the biscuit tin with a card in it: `att_escort` (an escort's log: she was found here again).
- A small warm lamp (EMIT `Att15HideLamp`), a slit of light the player can notice from the floor.

**The puzzle:**
1. **Out of the duct**, onto the sick bay balcony at 1.6. The sick bay figure (B) stands on its rail stub by the cot.
   The lift is up at the balcony's edge, empty. Its gate is shut.
2. **He steps on the lift alone.** ESCORT lights; a buzzer; nothing moves. NO PUPIL UNACCOMPANIED.
3. **He pushes B** right along the stub, onto the lift (it clicks into place on the lift's rail). PUPIL lights.
   He steps on beside it: both lamps lit, and the lift goes down. At the bottom the gate folds open.
4. **He pushes B off the lift** onto the floor rail: it clicks into the first seat it reaches, S1. R. ABEL lights.
5. **He pushes A** (from the blackboard, leftward): it clicks into Mara's seat, S3, first. M. D. lights, and the only
   chair left for him is in the wrong place. The aha: push A on, past Mara's seat, to S2. T. ORME lights.
6. **He sits in Mara's chair** (Use). M. D. lights: all three present. A beat; then the bell. The figures fold their
   arms, turn, and roll away along the rail, out under the flap. The door opens and stays open.
7. He gets up when the player moves him, alone in the classroom, and goes out through the door.

Figures on the rail go both ways, can be pushed from either side, stop at each seat they reach (Use again pushes on),
and can't pass each other. Any order works if the player ends with B and A in S1 and S2 and D-17 in S3.

**Camera:** at his seat, a low shot at child-desk height past him into the emptying room; it holds while the figures
go.

## DL-16 After the Bell (x 264 to 280): applied challenge, about 3 minutes

**The room:** the dismissal corridor. The back wall is painted with a playground mural (swings, a slide, a sun,
children holding hands, faded) and a big painted arrow: PLAYGROUND →. The figures' rail runs along it. Halfway, a light
well drops into the boiler room, fenced at the back, crossed by a bascule bridge that is raised. At the far end, where
the arrow points, the rail runs into a tall storage rack of folded teaching figures: the school's surplus, dozens of
them.

**Layout:**

| x | What |
|---|---|
| 264.0 | In through the class door (DL-15's partition). |
| 264.0 to 280.0 | Corridor: back wall face y 1.4, ceiling 3.0. Lino floor. The rail at y 0.55 continues from DL-15's flap. |
| 265.4 | A school tannoy high on the back wall (`art/common/voice_props.py` `tannoy`), the bell's speaker. |
| 266.0 | **The crossing lever** (`Att16Lever`): a tall floor lever at the lane's back edge (y 0.35), handle at 0.6, pivot at the floor; pulls toward +x (rotates about the Blender y axis, −35° pulled). A brass plate: HOLD UNTIL CLEAR. |
| 267.0, 266.2 | Where the two figures wait in line on the rail when they arrive (no art; the game moves DL-15's figures). |
| 267.9 to 269.9 | **The light well**: a pit across the lane and the rail, 2.0 wide, floor at −1.6 (dark, a glimpse of boiler pipes), a fence at the back (y 1.0). |
| 267.9 to 269.9 | **The bridge** (`Att16Bridge`): a timber-decked iron bascule section spanning the pit, lane-deep (y −0.3 to 0.9), deck top at 0, with the rail on it. **Built down** (spanning); origin on its hinge at the far end (x 269.9, z 0, centre y 0.3); the game raises it by rotating it about the Blender y axis to stand up (90°). A latch hook on the far post (`Att16Latch`, origin on its pivot) that the game drops onto the deck when the bridge is locked down. |
| 270.0 to 273.4 | Corridor on: mural continues (the playground's gate, painted). |
| 273.6 to 277.6 | **The storage rack** against the back wall (y 0.6 to 1.4, up to 2.9): five tiers of folded teaching figures hung on hooks, dozens, dusty, labels on the tiers (MODELS · CLASS 1 to 6). The rail runs into its bottom bay at 274.6 to 276.6, where two hooks hang empty, waiting (report their positions: the game lifts the arriving figures onto them). |
| 277.8 to 279.2 | **The rack's counterweight** (`Att16CW`): an iron box 1.4 wide, 0.5 deep, 1.5 tall, in a guide frame across the lane, resting on the floor; it blocks the way. Its chain runs up over a sheave to the rack. The game lifts it 2.0 when the rack has taken both figures. Behind it, the doorway on (x 279.6 to 280.0, height 2.1) into DL-17, dark until then. |

**The puzzle:**
1. He comes through the door. The figures are ahead, stopped in line at the raised bridge, facing the well.
2. **He politely lets them go first** (a quirk: a little after-you gesture) and walks to the lever.
3. **Hold the lever** (Use and keep holding; letting go of Use, or moving, lets go). The bridge comes down; the figures
   roll across one after the other, on along the corridor and into the rack, which lifts each onto a hook.
4. If he lets go before the second figure is across, the bridge goes back up and the second waits at the edge. Hold it
   again.
5. **When the rack has both**, it takes up its slack with a clunk: the latch drops onto the bridge (down for good) and
   the counterweight rises out of the lane, opening the doorway on. The figures hang among the others.
6. He crosses, sees where the playground arrow leads, and goes through.

**Story beat:** he steps aside for the figures as if they were children. Then the rack. The rail's wheels keep ticking
a while after the figures have stopped.

## DL-17 A Different Lesson (x 280 to 296): quiet interaction, about 2 minutes

**The room:** the school's workshop: a volunteer maintenance bench, warm light, the most lived-in room in the school.
Children's growing experiments everywhere: beans in jars with names on them, a seed tray per pupil, a cracked pot
mended with wire and putty. A grow-lamp still on over the window shelf, and under it the one living pale shoot.

**Layout:**

| x | What |
|---|---|
| 280.0 | In through the doorway. Back wall face y 1.3, ceiling 3.0, timber floor. |
| 281.0 to 282.4 | A tall slatted shelf of seedling trays and pots, each with a child's name tag; most are dead and dry. |
| 282.8 to 288.6 | **The bench** against the back wall (y 0.65 to 1.3, top 0.9): vice, tools on a board above it, a soldering iron, a kettle, a mug, a radio, a pair of reading glasses. Under the bench, a plan chest of shallow drawers. |
| 285.3 to 286.7 | **The big drawer** (`Att17Drawer`), the plan chest's lowest, front face at y 0.62, front from z 0.12 to 0.48, label PLACEMENTS. Built **shut**; origin on the middle of its front face; the game slides it 0.45 toward the camera (Blender −y). Inside it (parented to it, moved with it): papers; on top, Mara's **irrigation drawing** (her crooked tree turned into a garden bed with water channels, pencil, ruled lines over the childish ones) and her **placement card** (texture, readable in a close-up: PLACEMENT · M. D. · age 14 · WORKS DEPT., RING A · water and irrigation · sponsor E. LISLE, with a stamp). |
| 286.9 | **The repaired pot** on the floor at the bench's end (y 0.35), the crack wired: when the drawer is out, the drawing sits beside it in the close-up. |
| 285.7, y −0.05 | **`Att17Tray`**: a heavy seed tray of damp soil that slid off the bench and wedged against the drawer's handle, lying on the floor in front of it (a carried item, about 0.42 by 0.30 by 0.09; origin at its bottom centre). |
| 287.6 to 288.4 | A low stool (top 0.45) at the bench end with a **voice-card player** on it: `att_volunteer`. |
| 289.0 to 292.0 | The window shelf: a grow-lamp (EMIT `Att17GrowLamp`) on, over a shelf of pots; one with a single pale living shoot. |
| 293.0 to 295.6 | The way on: a stair door marked WORKS · RING A ↑ (shut: Chapter 2 starts here). |

**The scene:**
1. He comes in. The lamp, the bench, the names on the trays.
2. **The drawer is stuck**: the tray is wedged against its handle. He lifts the tray and puts it down out of the way
   (anywhere; on the floor in the lane).
3. **He pulls the drawer** (Use): it slides out toward the camera.
4. **He reads it** (Use): close on the drawing beside the repaired pot, then the placement card. He checks his label:
   it is stamped again, FWD WORKS DEPT RING A.
5. The voice card on the stool is optional (the volunteer).
6. The end of Chapter 1.

## Voice letters (add to `docs/voice_script.md`)

- `att_escort` (DL-15, under the balcony; treatment `card_worn`): an escort's log card, recorded for the file.
- `att_bell` (DL-16, the corridor tannoy; treatment `tannoy`): the end-of-lessons announcement.
- `att_volunteer` (DL-17, on the stool; treatment `elder`): the volunteer, Mr Lisle, to Mara.

## Art: what the game moves (names and pivots)

| Scene | Moved or animated by the game |
|---|---|
| DL-15 | `Att15FigA`, `Att15FigB` (origin on the rail top under the stand's centre; facing +x); `Att15Lift` (origin at the deck's top centre, built up at 1.6; includes its rail stub); `Att15LiftGate` (origin on its hinge post, built shut at the top; the game moves it with the deck and swings it open about z); `Att15LiftCW` (origin centre, built at its position for the lift up); `Att15LampPupil`, `Att15LampEscort`, `Att15Lamp1` to `Att15Lamp3`, `Att15HideLamp` (emissive, own objects); `Att15Door` (origin on its hinge, built shut); `Att15Flap` (origin on its top hinge, built shut). |
| DL-16 | `Att16Lever` (origin on its pivot); `Att16Bridge` (origin on its far hinge, built down); `Att16Latch` (origin on its pivot, built up); `Att16CW` (origin at its bottom centre, built resting on the floor). |
| DL-17 | `Att17Drawer` (origin on its front face's middle, built shut; contents parented); `Att17Tray` (origin at its bottom centre, built where it lies); `Att17GrowLamp` (emissive). |

Each module ends with a `REPORT` string (as `dl14.py` does) listing every number the game needs: the objects' world
positions, surfaces D-17 can stand on (x0, x1, top), walls and ceilings he can't pass, light positions and colours,
new materials (WORN, PLAIN, EMIT tables in `game/undelivered/index.html` format), and the voice player's position.

## Checkpoints

| Name | Where |
|---|---|
| `sickbay` | DL-15, out of the duct on the balcony, x 249.0, y 1.6 |
| `class6` | DL-15, down the lift, x 252.6, y 0 |
| `dismissed` | DL-15, the door open, x 263.2 |
| `crossing` | DL-16, at the lever, x 265.4 |
| `store` | DL-16, over the bridge, x 270.4 |
| `workshop` | DL-17, x 281.0 |
