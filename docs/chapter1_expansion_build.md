# Chapter 1 expansion: build spec

Status: building (22 October 2026). Design and reasons: `docs/chapter1_expansion_proposal.md`. This is the build sheet
the art modules and the game share: x ranges, every surface the player stands on, every object the game moves (name,
origin, built pose) and the lamps it switches.

Taken as decided (the user: "address them all"): nine scenes, three new; the escort trolley as a simple rail machine;
DL-17's rig works with water (a small preview of chapter 3's water).

## After the design review (23 October 2026)

`Dead_Letter_Post_Prologue_Change_Report.md`, accepted by the director: step count is not difficulty; neighbouring
puzzles need distinct inferences; clues depict, they don't solve. So: DL-16a is cut to a short ballast application (one
tin is the line); DL-17's drawing shows the crossed pipes without writing the answer; DL-14a's drive plate and tannoy
no longer state the solution, and the gown is a weighted cape; DL-16's dead waiting is trimmed, its window kept. And the
present-day service thread is approved: the prologue's new cable (NewCable, NewSteel clips, taped joints) runs through
the school with splice and relay boxes (Att12SpliceLamp, Att14bRelayLamp, Att16aRelayLamp, Att17RelayLamp: green pilot
lamps on their own 7 s relay cycle), feeds DL-17's refill pump, and goes on up the stair to ring A. Its changes follow
equipment cycles, never D-17's arrival.

## Conventions (as the other chapter 1 modules)

- Blender (x, y, z) is the game's (x, z, -y): +y is away from the camera, z is up. The lane is y = 0, the floor z = 0.
- A module is `art/ch1/<name>.py` with `build_set(dl01, m, coll)`, built by `art/ch1/build_attendance.py`. New modules
  are written in **final** world coordinates. dl15, dl16 and dl17 keep their old coordinates in their files; the
  builder moves everything they make by `SHIFT` (dl15 and dl16 +30, dl17 +44). So in dl15/dl16/dl17, keep using the
  numbers already in the file.
- D-17 is 0.71 m tall (antenna to 1.12), half-width 0.17. From a floor he reaches a hook at 0.76 above his feet. He
  mantles onto anything 0.24 to 0.62 above where he stands; drops of any height are safe.
- Look: the school's look (DL-12 to DL-17): worn enamel signs, dado and plaster, linoleum, brass, the children's
  pencil and chalk. Reuse `build_d17` helpers and the shared materials `m`, as dl15/dl16/dl17 do.
- Names the game looks up must be exact. Each object the game moves is its own object with its origin at its pivot.
  Lamps the game switches are their own objects (the game gives each its own emissive material).
- Each module ends with a `REPORT` string: the final numbers of everything listed here, and any deviation from it.

## Layout (game x)

| Scene | x | Module |
|---|---|---|
| DL-14 The Window (unchanged) | 232.0 to 247.85 | dl14 |
| **DL-14a Lights Out** (new) | 248.0 to 263.0 | **dl14a** |
| **DL-14b Unaccompanied** (new) | 263.0 to 278.0 | **dl14b** |
| DL-15 One Pupil Missing | 278.0 to 294.0 (old 248 to 264) | dl15, +30 |
| DL-16 After the Bell | 293.9 to 310.0 (old 263.9 to 280) | dl16, +30 |
| **DL-16a Her Way Round** (new) | 310.0 to 324.0 | **dl16a** |
| DL-17 A Different Lesson | 324.0 to 340.0, stairwell to 347 (old 280 to 296/303) | dl17, +44 |

DL-14's hatch duct (behind DL-14's painted windows, at y 1.3) now comes out in the dormitory, not on DL-15's balcony.

## DL-14a Lights Out (dl14a.py, x 248.0 to 263.0)

The dormitory at rest hour. Forty beds, most of them through tall arches in the back wall in a dim second ward; three
narrow bunks in the lane, pushed together, with name cards on their ends (R. ABEL, T. ORME, M. DALE). A painted tin sun
for a night-light. REST HOUR rules on the wall. A nurse's chair facing the beds. An eye on the wall over the door that
says whether the room is dark.

Shell: left wall 248.0 to 248.15 (DL-14's end wall at 247.85 stays as is; the gap stays dark). Back wall face y 1.4,
0.2 thick, with arches through it to the back ward (beds in rows to about y 6, dim). Ceiling 3.5. Right end wall
262.85 to 263.0 with the door. Floor: linoleum.

Gameplay geometry (the game's collision is these numbers, not the mesh):

| Thing | x | Top / height | Depth y | Notes |
|---|---|---|---|---|
| The duct's vent | 248.55 to 249.35 | sill 1.15, head 1.8 | in a cupboard face at y 1.4 | He comes out of it onto bunk 1 |
| Bunk 1 (arrival) | 248.3 to 250.3 | top deck 1.15 | -0.35 to 1.4 | A bunk: lower bed at 0.5 under the top deck (decor) |
| Locker 1 | 250.3 to 250.8 | 0.55 | -0.3 to 0.5 | The step down |
| The REST HOUR brake (pawl lever) | pivot x 252.3, z 0.6 | | on the back wall's face | Like DL-13's AttPawl |
| The night-light dial | centre x 253.0, z 1.35 | | back wall face | Bands for one cycle (below) |
| The night-light (tin sun) | centre x 253.9, z 2.55 | | back wall face | |
| Gown pegs (decoy) | 250.95 to 252.0 | hooks at 0.80 | back wall face, y 1.38 | A row of child-height pegs with small gowns; ONE free peg at x 251.5 |
| Locker 2 | 254.3 to 254.8 | 0.55 | -0.3 to 0.5 | |
| Bunks 2 (three pushed together) | 254.8 to 257.6 | top deck 1.15 | -0.35 to 1.3 | The three friends' beds |
| Locker 3 | 257.6 to 258.1 | 0.55 | -0.3 to 0.5 | |
| Window W1 (to the light well) | 255.4 to 257.0 | sill 1.6, head 3.1 | back wall | Cold blue-white beyond |
| W1's blackout blind | 255.3 to 257.1 | roller axis 3.25 | **hung out on brackets at y 1.0** | down: hem at 1.93 |
| The peg on W1's hem | x 256.2 | 1.93 when down | y 1.0 | He hangs the gown here from bunks 2 |
| The crank (one cord, two blinds) | 258.7 | handwheel centre z 0.5, r 0.19 | post at y 0.32 | Like DL-14's AttCrank; drive plate beside it |
| Window W2 (borrowed light from the night corridor) | 259.3 to 260.9 | sill 1.9, head 3.1 | back wall | Warm beyond |
| W2's blind | 259.2 to 261.0 | roller axis 3.25 | y 1.3 | down: hem at 1.95; no peg |
| The nurse's chair | 260.6 | seat 0.42 | y 0.4, facing -x | The dressing gown hangs on a hook on its back at 0.95 |
| The eye (lux meter) | centre x 261.9, z 2.25 | | back wall face | Four lamps, below |
| The door (LIGHTS OUT) | in the end wall, y -0.45 to 0.45 | head 1.75 | | Swings open into the corridor |
| The figures' rail | 261.6 to 263.0 | rail top 0.03 | rails at y 0.47 / 0.63 | DL-15's rail, as a short stub by the door (DL-14b's figure is brought back here) |

The cycle: the night-light runs a 10 s cycle, BRIGHT 0 to 3, DIMMING 3 to 4.5, DARK 4.5 to 8, BRIGHTENING 8 to 10. The
dial's face shows those bands round the circle (warm yellow, a gradient, black with a small painted moon, a gradient)
and has a fixed alignment mark at the top; the hand turns clockwise once per cycle, starting at the top.

What the game moves:

| Object | Origin (pivot) | Built pose | The game |
|---|---|---|---|
| Att14aPawl | its pivot on the wall (252.3, 1.36, 0.6) | off (handle up) | rotates about x by 40 degrees when braked (as AttPawl) |
| Att14aDialHand | the dial's centre | pointing up | rotates about the face normal, clockwise, one turn per cycle |
| Att14aSunLamp | the sun's centre | | the sun's glowing glass (own emissive) |
| Att14aCrank | the handwheel's centre | | spins while the blinds move |
| Att14aBlindW1 | the middle of its roller axis | DOWN (fabric to 1.97, not the hem bar) | scales its height (z) from 1 (down) to 0.04 (rolled up) |
| Att14aHemW1 | the peg's hook point on W1's hem bar (256.2, 1.0, 1.93) | down | moves up and down with the blind; carries the hem bar and the peg |
| Att14aBlindW2 | the middle of its roller axis | DOWN (to 1.95, hem included) | scales its height (z) |
| Att14aGown | the hanger's hook point | hanging on the chair's hook (260.6, 0.4 back, z 0.95) | moved to the hem peg, a wall peg, his hands or the floor |
| Att14aDoor | the hinge, at the back jamb (262.92, 0.45, 0) | shut | rotates about z by up to 90 degrees, opening into the corridor (+x) |
| Att14aEyeSun, Att14aEyeW1, Att14aEyeW2 | | | small amber lamps, labelled NIGHT-LIGHT, WELL WINDOW, CORRIDOR WINDOW: lit while that source lets light in |
| Att14aEyeDark | | | the big green lamp: DARK (REST HOUR) |

Signs and story: REST HOUR (the rules: "1. Lights out. 2. No talking. 3. Stay in your own bed. 4. Pupils are never
unaccompanied."); the drive plate by the crank ("ONE CORD - TWO BLINDS. W1 DOWN MEANS W2 UP. THE CLUTCH SLIPS WHEN A
BLIND IS HELD."); the eye's plate ("REST HOUR BEGINS WHEN THE ROOM IS DARK"); the three bunks' name cards; under the
three pushed-together bunks, a torch and three biscuits (they talked after lights out). Lamps: one dim ceiling globe
(EMIT AttGlobeLamp); an empty `Att14aSpeaker` at the tannoy's horn (for the rest-hour announcement).

## DL-14b Unaccompanied (dl14b.py, x 263.0 to 278.0)

The night corridor between the dormitory and the sick bay. NO PUPIL UNACCOMPANIED. An escort trolley still runs its
round on the floor rail: a slow, gentle machine with a lamp, a bell and a padded push-paddle, about a child's height.
Whatever pupil-sized thing it finds in its lamp's beam it takes back to the dormitory.

Shell: back wall face y 1.0 (0.2 thick) with two recesses; ceiling 3.0; the left end is the dormitory's wall (dl14a);
the right end is DL-15's left wall (dl15, 278.0 to 278.15), with the sick bay's door high in it (see dl15 below).

| Thing | x | Top / height | Depth y | Notes |
|---|---|---|---|---|
| The figures' rail (floor channel, as DL-15's) | 263.0 to 275.3 | rail top 0.03 | rails at y 0.47 / 0.63, channel 0.39 to 0.71 | The trolley runs on it |
| Niche A (a cloakroom recess) | 263.6 to 264.5 | 1.8 high | recess y 0.25 to 1.0 | A hiding place: he steps back into it to z -0.62 and crouches |
| The bay (a figure's alcove) | 269.4 to 270.4 | 1.9 high | recess y 0.25 to 1.0 | A teaching figure stands in it on a short spur rail (y 0.85 to 0.55) |
| The trolley's dock | 264.6 to 265.4 | | | A painted bay on the floor, ESCORT 3 |
| The stair up | 275.3 to 277.6 | 9 treads, each 0.255 long and 0.178 high, to 1.6 | -0.45 to 0.6 | Open treads, iron |
| The landing | 277.6 to 278.0 | 1.6 | -0.45 to 0.6 | To the sick bay's door |

What the game moves:

| Object | Origin (pivot) | Built pose | The game |
|---|---|---|---|
| Att14bTrolley | the middle of its base on the rail top (266.0, 0.55, 0.03) | facing +x (lamp and paddle on its +x end) | slides along x; turns 180 degrees about z to face -x |
| Att14bCone | the lamp's mouth (266.0 + 0.35, 0.55, 1.0) | pointing +x | follows the trolley and turns with it. A cone 2.6 long, base radius 0.6 at its end, centred 0.55 high there; a warm, very transparent beam (the game sets the material) |
| Att14bFig | as DL-15's figures: on the rail top under its bogie (269.9, 0.85, 0.03) | standing in the bay on the spur | moved out to y 0.55 and then along x |
| Att14bBell | on the trolley | | (part of the trolley is fine) |

The figure is a DL-15 teaching figure (copy dl15's figure build), a little shabbier, with a card on a string: PUPIL.
Signs: NO PUPIL UNACCOMPANIED (big enamel); ESCORTS KEEP TO THE RAIL; SICK BAY with an arrow up the stair. Lamps: two
dim globes (EMIT AttGlobeLamp), one over the stair. Dressing: a lost slipper by niche A; chalk marks on the floor
where children were told to stand.

## DL-15 changes (dl15.py, old coordinates, +30 at build)

- The left wall (LWALL, 248.0 to 248.15) gets a doorway at balcony level: y -0.45 to 0.45, sill 1.6, head 2.45, with an
  architrave on both faces and a sign on the corridor face: SICK BAY. (The player now comes in here from the stair.)
- The duct's end in the back wall (HATCH) is no longer the way in: close it with a grille (a vent).

## DL-16a Her Way Round (dl16a.py, x 310.0 to 324.0)

The kitchen corridor behind the dismissal corridor. The way to the workshop is barred to pupils. At child height on
the wall, a crooked chalk tree, then another, and an arrow: the servery's dumbwaiter. She went round.

Shell: left, DL-16's end partition (309.6 to 310.0, its doorway y -0.35 to 0.45, head 2.1). Right, DL-17's left wall
(324.0 to 324.15) with its doorway at the floor (dl17's DOORWAY, +44). Back wall face y 1.2. Ceiling **3.9** (a
two-storey servery: the upper passage needs head room).

| Thing | x | Top / height | Depth y | Notes |
|---|---|---|---|---|
| The high shelf (books) | 310.2 to 310.9 | shelf top 1.25 | y 0.1 to 0.6 | A bundle of books, string-tied, on it at x 310.55 |
| The step stool (pushable) | rest centre 312.0, half-width 0.25 | top 0.45 | -0.25 to 0.25 | Pushed under the shelf |
| Two ration tins | 311.2 and 311.45 | on the floor | y 0 | Small, heavy |
| The dumbwaiter car | inside 312.6 to 313.4 | car floor 0.05 at the bottom, 2.45 at the top | -0.4 to 0.6 | Open-fronted, for trays. A bell push inside on its back wall at 0.6 |
| The shaft | 312.5 to 313.5 | to the ceiling | -0.45 to 0.7 | Its frame; the counterweight behind the car |
| The gate (PUPILS NOT PERMITTED) | 314.0 | floor to 2.3 | -0.45 to 0.9 | Bars; the corridor goes on beyond it |
| The upper passage | 313.5 to 321.2 | floor 2.4 | -0.3 to 1.2 | A railing along its front edge |
| The stair down | 321.2 to 323.6 | 12 treads, 0.2 long and 0.2 high, 2.4 down to 0 | -0.45 to 0.6 | |
| The lower corridor beyond the gate | 314.0 to 324.0 | floor 0 | | Under the passage, on to DL-17's door |

What the game moves:

| Object | Origin | Built pose | The game |
|---|---|---|---|
| Att16aCar | the middle of the car floor's top (313.0, 0.1, 0.05) | at the bottom | moves in z (to 2.45) |
| Att16aCW | its bottom centre | at the top of the shaft, behind the car | moves opposite the car |
| Att16aStool | its bottom centre (312.0, 0, 0) | | slides in x |
| Att16aTin1, Att16aTin2 | bottom centre | on the floor | carried; set down in the car |
| Att16aBooks | bottom centre | on the shelf (310.55, 0.35, 1.25) | carried; set down in the car |
| Att16aLoad1, Att16aLoad2, Att16aLoad3 | | | three amber lamps on the load gauge (on the shaft's front frame at z 1.4): lit one per portion of load |
| Att16aLoadOver | | | a red lamp: overloaded |

The gauge's plate: "TRAYS ONLY - LOAD TO THE LINE" with three lamp windows and a line after the third; OVER beyond it.
A brass plate on the car: "MAX 3 PORTIONS". Story: chalk trees at 0.4 to 0.6 high at x 310.7, 311.6 and 312.3, an arrow
to the car; at the top, on the hatch frame by the upper passage (313.6, z 2.6 to 2.9), a fourth tree and a small
chalk handprint. A kitchen pendant, a lamp in the car (EMIT), a lamp over the upper passage. An empty `Att16aBellPush`
at the bell push.

## DL-17 changes (dl17.py, old coordinates, +44 at build)

Her drawing becomes the instructions. Vance's apprentice test rig stands between the sink and the stair door.

| Thing | x (old) | Height | Depth y | Notes |
|---|---|---|---|---|
| The valve (on the tank's down-pipe) | 292.55 | wheel centre 0.7 | y 0.5 | Turned by Vance's T-key, which is in the drawer |
| The tank | 293.0 to 294.2 | 1.7 to 2.3 | on wall brackets, y 1.0 | A sight glass on its front |
| The test bench | 293.05 to 295.3 | top 0.55 | 0.35 to 0.95 | |
| Bed 1 (M. D.), bed 2 (R. A.), bed 3 (T. O.) | 293.1 to 293.75, 293.8 to 294.45, 294.5 to 295.15 | trays on the bench, 0.15 deep | y 0.45 to 0.85 | Name cards on their fronts |
| Sluice levers A, B, C | 293.45, 294.1, 294.8 | pivot 0.45 on the bench front | y 0.33 | Each under a bed, but A feeds bed 3, B feeds bed 1, C feeds bed 2: the pipes cross behind the bench, plainly, in the same brass |
| The float | in bed 1 | | | Its chain runs up to a pulley and along under the ceiling to the stair door's latch |
| The latch | on the stair door at 295.8, z 1.9 | | | Lifted by the chain |

What the game moves:

| Object | Origin | Built pose | The game |
|---|---|---|---|
| Att17SluiceA/B/C | the lever's pivot | open (handle up) | rotates about x by 80 degrees to shut |
| Att17Valve | the wheel's centre | | spins while the water runs |
| Att17ValveKey | on the valve's spindle | | hidden until he has the key |
| Att17Key | in the drawer, on the papers | | hidden once he has read (he takes it) |
| Att17TankWater | the bottom of the sight glass | full | scales its height |
| Att17Water1/2/3 | the bottom of each bed's tray | full (0.13 deep) | scales its height (0 to 1) |
| Att17Stream1/2/3 | the pipe's mouth over each bed | | shown while that bed is being fed |
| Att17Float | its bottom, in bed 1 | low | rises 0.12 with bed 1's water |
| Att17Latch | its pivot on the door | down (locked) | rotates up by 70 degrees when the float is up |

The card on the rig (Vance's hand): "APPRENTICE TEST: WATER BED 1 ONLY. ONE TANK." The drawing in the drawer (the
drawing17 record) now includes her working for the rig: the three beds, the crossed pipes traced in pencil, "B goes to
1! (they cross)", "shut two, water the third", and Vance's margin note beside it: "Good eye. Most of them never look
behind the bench."

## Game summary (index.html)

- **DL-14a:** the night-light cycle and its brake; one crank, two blinds, the clutch slipping when W1 is held by the
  gown on its peg; the eye's lamps; the door opens (and stays open) once the room has read DARK for 1.2 s. The gown
  is an item like the coat: from the chair, to a peg, to the floor.
- **DL-14b:** the trolley patrols 265.0 to 274.9 at 1.1 m/s with a 1.2 s pause at each end; its beam is 2.6 m ahead.
  Seen (not hidden in a recess), he is escorted back to the dormitory door, unhurt. The figure, nudged out of its
  bay, is seen instead, and taken back to the dormitory (pushed to 262.2 and left there, a 6 s stop) while he goes on.
- **DL-16a:** the load is counted in portions: a tin 1, the books 2; 3 is right. Too light, the car shoots up, the
  catch bites and it lowers him back; too heavy, it won't go.
- **DL-17:** the drawer gives the key; the valve runs one tank (6 s) split across whichever sluices are open; bed 1
  needs it all. Beds drain over 20 s, the tank refills in 10 s.
