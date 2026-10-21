# DL-11 The Child at the Address: production plan

**Status:** built as a playable prototype (`game/undelivered/`), for director review
**Source:** Dead Letter 45 Scene Overview, scene 05 (16 October 2026)
**Sequence:** DL-10 → DL-11 → DL-12, with no cut on either side

> **Renumbered 20 October 2026 (pass 3).** Chapter 1 now has eleven scenes; this was DL-09. See *Pass 3* at
> the end.
>
> **Renumbered 18 October 2026.** Chapter 1 then had nine scenes; this was DL-05. The rework in
> `docs/chapter1_plan.md` and `docs/chapter1_build_spec.md` supersedes this plan where they differ.
**Duration target:** 3 to 4 minutes. The overview gives 2; scenes run a touch longer from DL-08 on.

## 1. What the scene must do

| Requirement (from the overview) | How the build meets it |
|---|---|
| Slide a fallen low desk clear of a forwarding terminal | In the child's bedroom of home C-114, a small desk has fallen against the back wall, in front of the forwarding terminal. D-17 grabs it, as he did the trolleys, and drags it clear. It scrapes, heavy for him. |
| Moving it exposes the growth marks and tree carving behind it | Behind the desk, pencil lines climb the wall, one per year: M 2 (P.A. 306) to M 6 (P.A. 310). Beside them, scratched into the plaster, is a crooked tree with a knot in one branch. |
| Presenting the parcel retrieves the school destination | Use at the terminal. D-17 leans his chest window to its reader, and his three lamps answer its three: the handshake again. The screen reads C-114, then NO ONE AT THIS ADDRESS, then FORWARD TO SCHOOL with the school's mark, RING B, and the class of P.A. 310. |
| A patched toy, imagined sunlight, and the parent-and-child photograph make the addressee concrete | A patched rabbit slumps on the bed. Over the bed, a window painted on the wall, lit warm from behind, with a sun. On a shelf, a photograph of a parent kneeling beside a small child. |
| Establish Mara's crooked tree with a knot in one branch | The carving, revealed by the desk. The photograph shows the same tree, chalked on a wall behind them. |
| D-17 straightens the toy, then leaves the bedroom undisturbed | Passing the bed, he stops to sit the rabbit upright and pats its head (`Straighten`). It is brief, and any move cancels it. He leaves by the back door; nothing else is touched. |
| Move slightly closer as the desk shifts; the growth marks occupy the new empty space | As the desk scrapes, the camera eases in a little. When it clears, the camera holds on the marks and the carving for a moment, the first time only. |

**Player understanding:** an abstract addressee → a particular child, with a home and a parent.

## 2. Beats

| Beat | What happens |
|---|---|
| **Down to ring C** | The stair off the DL-08 balcony brings him down to ring C's ledge. The cave city rises behind him. |
| **The seal** | A barricade of sheet metal across the lane: RING C SEALED · P.A. 311, and tape. There is a gap under it; he crouches through. |
| **Ring C** | Abandoned and nearly dark: shuttered homes (C-108 to C-112), dead bulbs on a cable, two still burning, one of them failing. A fallen duct to hop. |
| **C-114** | The last door stands open. He steps up beside it, knocks on the jamb twice and waits (`Knock`): nobody. He goes in. |
| **The hall** | A small pair of shoes beside a large pair. A lamp still on. |
| **The bedroom** | The rabbit on the bed, the painted window, the photograph. The desk fallen against the wall, the terminal above it. |
| **The desk** | He steps in to its red grip bar and drags it clear. The music comes in: the parcel's three notes become a lullaby. |
| **The terminal** | The handshake, and the school destination. His label changes: the screen's school mark replaces the door. |
| **The rabbit** | Passing the bed on his way to the desk, he sits it up. |
| **Out the back** | A back door onto a service stair, with a sign for the school on ring B. The end card. |

## 3. Layout (metres along the lane; this scene's floor is at 0)

> Before pass 2. Most of this has moved: see *Pass 2* at the end.

```
x: 74.65-76.8 stair down from the DL-08 balcony (1.6 -> 0)   76.8 ledge   80.2-81.0 BARRICADE (gap 0.62 high)
   81.0-88.5 ring C lane (duct 84.2-84.6, 0.26 high)   88.2 knock   88.6 C-114 door (lintel 1.3)
   88.7-90.6 hall   90.6 inner door (lintel 1.25)   90.65-95.6 bedroom   95.6 back door   97.2 end
bedroom: bed 91.0-92.5 (top 0.42, behind the lane)   toy (92.2, top of bed)   painted window over the bed
         shelf and photograph 93.4   terminal 94.48-94.92 (screen 0.95 high, reader 0.73)   growth marks 94.15-95.25
         the desk: x 94.7 (half-length 0.55, about 0.55 high), dragged left to a centre of 93.55 (93.0-94.1)
```

Blender coordinates as before: the lane at y = 0, behind it +y, travel along +x. The back walls of the lane, the
hall and the bedroom are at y = 1.0. The homes are cut away toward the camera.

The bed, the desk and the terminal stand against the back wall, off the lane, so D-17 walks in front of them. To
use the desk he steps in to its grip bar (y 0.62) and steps back out when he lets go. He steps in to y 0.64 to
knock, and to y 0.70 to present.

**Light:** ring C is abandoned and nearly dark (see *Light by level* in `docs/direction.md`). Two bulbs burn on the
lane, at x 81.65 (just inside the seal, failing) and 86.6. Inside C-114 the hall lamp, left on, and the painted
window are the main lights; C-114's front window glows faintly with the lamp behind its curtains. The home is the one
warm pocket in the dark.

## 4. Models (`art/dl05/build_dl05.py`)

| Object (game name) | What it is |
|---|---|
| `D5Ledge`, `D5Lane`, `D5Rock` | The ledge and the lane floor at 0, a rough rock face behind the ledge, and the lane's back wall. |
| `D5Barricade`, `D5BarricadeSign`, tape | Corrugated sheets bolted to posts, from 0.62 up to 3 m, with a sign and tape. |
| `D5Duct` | A fallen ventilation duct across the lane, 0.26 high. |
| `D5Homes`, door plates | Shuttered home fronts along ring C's back wall (C-108, C-110 and C-112), dead bulbs on a cable, and working bulbs (`LaneBulb`). |
| `D5Home114`, `D5Plate114` | C-114: its front facade with a window and its number plate, the cross-section wall with the door opening, the hall, the inner wall, the bedroom, and the back wall with the back door. |
| `D5HallShoes`, `HomeLampBulb` | A child's shoes and a grown-up's, and the hall lamp. |
| `ChildBed`, `Toy` | The bed, and the patched rabbit, its origin at its base, modelled slumped. The game sits it up. |
| `WindowSun` | The painted window over the bed, emissive and warm. |
| `D5Shelf`, `D5Photo` | The shelf and the photograph. |
| `ForwardTerminal`, `TermLamp0`, `TermLamp1`, `TermLamp2` | The terminal, with a screen recess (the game draws the screen) at (94.7, 1.0, 0.95), 0.32 x 0.24, and its three lamps. |
| `D5Marks` | The growth marks and the carved tree, on the wall behind the desk. |
| `ChildDesk` | The fallen desk, its origin on the floor at the centre of its footprint (x 94.7, y 0.62). Half-length 0.55, so it covers the marks and the tree on both sides of the terminal. It leans back 9° against the terminal, its hutch reaching about 1.2 m, with a red grip bar on its left end (0.585 from the centre). The game slides it along x. |
| `D5BackDoor`, `D5SchoolSign` | The back door frame and a sign: SCHOOL, RING B, with an arrow. |

## 5. Clips

| Clip | Frames | What it is |
|---|---|---|
| `Knock` | 48 | Stepped in beside the door, facing along the lane: he raises his right claw, knocks twice on the jamb at about 0.56 m (frames 14 and 20), waits with his head tilted, and lowers it. |
| `Present` | 64 | Facing the terminal 0.26 m away (the game turns him and steps him in): he rises onto his toes and arches his chest window up toward the reader, and holds still while the lamps answer (frames 20, 25 and 30). He comes down with a small nod (frame 50). |
| `Straighten` | 52 | Facing the bed: both claws to the toy (0.35 ahead, about 0.47 high), he sits it up (the game rotates it between frames 14 and 26), pats its head once (frame 33), and steps back. |

## 6. Camera

| Shot | When | Framing |
|---|---|---|
| `knock` | `Knock` | Low, in front and to the left of him, past him to the doorway and the lit hall (30 mm). |
| `desk` | While the desk moves | Eases in a little from the room framing toward the wall (40 mm). |
| `marks` | The desk clears, the first time only | Close on the growth marks and the tree (50 mm, 3.5 s). |
| `terminal` | `Present` | Over his shoulder to the screen. |
| `toy` | `Straighten` | From his right, above the bed's foot, so the rabbit reads as it sits up (34 mm). |

## 7. Music

`child`: when the desk clears the marks. The music box plays the parcel's three notes, slowly, and becomes a
lullaby over a soft piano and strings. It is warm, then it thins to a single note as the terminal answers.

## 8. Checkpoints

- **ringc**: through the barricade.
- **bedroom**: just inside the bedroom.
- **forwarded**: after the terminal.

## Pass 2 (built 19 October 2026)

From `docs/chapter1_pass2_plan.md`: ring C becomes a street with a square, C-114 becomes a whole home, and the flood is
the White's. This supersedes section 3's layout, the light in section 3, and the checkpoint positions. x is this
scene's own, as in section 3; game x is 30 more (`OFF4`).

**Layout:**

```
x: 74.75-76.75 stair down   76.8-80.0 ledge   80.2-81.0 BARRICADE (gap 0.62)   81.0-94.5 the street
   behind the lane: C-108 81.1-84.05 (window 81.85, BELL 82.72, door 83.4, its steps down into the water)
                    alley 84.05-84.95   C-110 84.95-87.95 (JUNCTION 85.92, door and letter slot 86.85)
                    C-112 88.05-90.5 (boarded, taped)
   the water: 82.95-87.6 along the back of the lane (surface -0.1, bed -0.9); the narrow point 86.1-87.6 across the
              whole lane (a slab 0.25 down); LaneCable hangs into the water at 87.4
   DUCT 84.25-85.75 on the lane (0.26 high, grip 84.23), pushed to 86.1-87.6 as the bridge
   SQUARE 90.5-94.5: square lamp 90.75, noticeboard 91.0, bench, dry fountain, swing, MAILSLOT9 93.75
C-114: front step 94.12   knock 94.2   front door 94.6
       HALL 94.7-96.9 (switch 95.72, bulb 95.85)   KITCHEN AND LIVING ROOM 97.0-100.4 (radio 100.0, lamp 100.28)
       inner door 100.5   BEDROOM 100.6-105.4   back door 105.5   end 107.1   stair up toward ring B 107.5
bedroom: bed 100.9-102.4   toy 102.1   painted window 101.62   shelf and photograph 102.66
         terminal 104.38-104.82 (screen at 104.6)   growth marks 104.05-105.15
         the desk: x 104.6, dragged left to a centre of 103.45
```

| Moved | Before | Pass 2 |
|---|---|---|
| The duct, and the narrow point it bridges | 81.6-83.1, into 83.4-84.9 | 84.25-85.75, into 86.1-87.6 |
| C-110's letter; `MailSlot9` | 83.85; 87.4 | 86.9; 93.75 (in the square) |
| The knock; C-114's door | 88.2; 88.6 | 94.2; 94.6 |
| The toy; the terminal and the desk | 92.2; 94.7 | 102.1; 104.6 |
| The back door; the end | 95.6; 97.2 | 105.5; 107.1 |

**The street** (`art/dl05/build_dl05.py`): the back row behind the lane (C-108's dim window onto a table still set,
the stepped alley up toward ring B, C-110 with letters jammed in its slot, C-112 boarded and taped); in front, a low
kerb wall and steps down to the lower row, its roofs a storey below. Over it, a cable of bulbs (two still burn: 81.65,
failing, and 86.3) and washing long dry on its lines. Ring B's tier, its stairs, a few lit windows and the lift going
up, in the haze behind. The flood line runs at 1.0 across everything.

**The square:** the noticeboard with the evacuation notice and the children's drawings of the White, a bench, a dry
fountain, a swing frame with one swing (it sways), and ring C's red mail slot.

**C-114, a dollhouse section:** the front step and door with its number, a letter plate, a boot scraper and a name
card; the hall (coat hooks with a small yellow raincoat, a shoe rack, the light switch); the kitchen and living room
(a table with three chairs, one a child's, the range and its kettle, the radio, the lamp left on); the bedroom as
before; the back door. Its street wall (`C114Facade`) fades out once he is through the front door (past 94.3), and the
cut edges behind it are capped near-black (`C114Section`), so it reads as a cut, not a hole.

**The White** (the water is its home while he is short of the square, 90.5):
- **First sight:** as he comes along the lane (past 82.3), it surfaces far off (86.9) and sinks.
- **It hears running and landings** within about 2.5 m of the water, never walking. It listens, swims to the sound,
  and surfaces. If he is beside the water and within 1.35 m, it lunges (`WhiteLunge`), the jaws close, and he is
  dragged under (`WhiteDrag`, `DeathGrabbed`). Back at `ringc`.
- **The duct's splash** as it drops into the narrow point is loud, and brings it there, right beside him.

**The sequence:**
1. **The doorbell** (`C108Bell`, red and lit, on C-108's gate pillar at the water's near end). Use rings it for 12 s:
   a trill every half second, its lamp blinking, the gong over the door shaking. The White swims to C-108's sunken
   step and noses at it (`WhiteNose`). While it rings, walking and the duct's splash don't turn it; running within
   2.2 m of it does. When the bell stops, it sinks and patrols again. It can be rung again.
2. **The duct:** push it in at the narrow point while the White is at the bell.
3. **Walk across** the duct, and on to the square.

**The junction box** (optional, instead of the bell): `JunctionLever`, on the bank by C-110 (85.92). Thrown
(`LeverPull`), the live cable shorts into the water at its far end: a clunk, a zap, 3.5 s of sparks and fizzing
ripples. The White flees deep for 20 s and hears nothing. Once per attempt.

**Curiosities** (both later ones: no light pool or glance):

| Curiosity | Where D-17 stands | What happens |
|---|---|---|
| The hall light switch (`CurioSwitch`, `HallBulb`) | 95.72, stepped in to the hall's back wall | Click (`FlickSwitch`): he looks up, startled, then pleased, with two little bounces. The hall bulb lights, and stays lit. |
| The radio (`CurioRadio`) | 100.0, stepped in to the living room's back wall | He turns the knob in little jerks (`TuneRadio`); static, then half a verse of a children's song, thin and far away. He jumps, then sways and does a little two-step. |

**Camera:** the lane's framing is raised (camera 2.15 high, looking down to 0.4; it was 1.15 and 0.75) so the water
and the White read. Then C-114 room by room: the hall (from 94.2), the kitchen and living room (97.0), the bedroom
(100.3), the back door (105.3). The `marks` shot is now at 104.55.

**Checkpoints:**
- **ringc**: through the barricade (81.25), unchanged. The duct is back on the lane, the bell and the junction box
  reset.
- **bedroom**: just inside the bedroom (101.1, was 91.2). The duct is already the bridge.
- **forwarded**: after the terminal (104.1, was 94.2).

## Pass 3 (built 20 October 2026)

From `docs/chapter1_pass3_plan.md`. This was DL-09; DL-10 Up Only now comes before it. This supersedes *Pass 2*'s
layout and the knock in section 2.

**Arrival:** the balcony's stair is gone. He comes down to ring C on Up Only's counterweight, onto the bottom landing
at the foot of its shaft (section x 73.75 to 76.8), and on to the ledge. The game counts ring C from the shaft's foot
(game x 127.9).

**Positions:** ring C is now placed by `OFF5` (54): game x = section x + 54. The street grew 9 m between the barricade
and C-108, so C-108 and everything after it is 9 further on in section x than in *Pass 2* (`S9` in
`art/dl05/build_dl05.py`).

```
section x: 76.8-80.0 ledge   80.2-81.0 BARRICADE   81.0-103.5 the street
   behind the lane: C-102 81.1-83.7   C-104 (and 104A) 83.8-86.2
                    CROSS ALLEY 86.2-87.4 (standpipe 86.5; the ration queue's post 85.95)
                    C-106 87.4-90.0 (window 89.3)   C-108 90.1-93.05 (BELL 91.72)   C-110 (JUNCTION 94.92)   C-112
   the water: 91.95-96.6 (the narrow point 95.1-96.6)   DUCT 93.25-94.75, pushed into the narrow point as the bridge
   SQUARE 99.5-103.5 (MAILSLOT9 102.75)
C-114: knock 103.26   front door 103.61   switch 104.72   radio 109.0   inner door 109.5   toy 111.1
       terminal and desk 113.6   end 116.1
```

**The street** (`art/dl05/build_dl05.py`): you pass through a neighbourhood, not past one wall.
- **The new homes behind the lane:** C-102, chalked GONE UP, a sheet nailed over its fallen plaster; C-104, split in
  two, a plank door 104A cut into it and chalked GONE UP, its window blocked up with odd blocks; the cross alley, with
  the neighbourhood's standpipe (STANDPIPE 3 · GRADE 4), the ration queue's post and its painted marks back along the
  lane, a RATIONS / GRADE 4 – TUES sign, steps up toward ring B and down toward the lower lanes; C-106, its door on the
  alley, chalked GONE UP, and on its blank face an old UP IS FOR THEM, half whitewashed, under a later EVERYONE UP with
  an arrow to the stairs. Every door is stencilled with its grade, a 4.
- **The front row**, on the camera's side of the lane: odd numbers, every one cut down or fallen in (garden walls,
  gates, porches, wall stumps, rooms open to the sky), kept below his height so it never hides him. C-111 went into
  the sink with the lane.
- **Over the lane:** washing lines, and the street cable with four bulbs.

**The White** (the plan's section 1: too hard the first time):
- **It warns first.** The first time it hears him (in a game), it surfaces, rears and hisses, and sinks again: a
  startle, not a strike. After that, as in *Pass 2*, it lunges if he is on the bank within reach.
- **It hears running from 1.4 m** of its water, not 2.2. Walking is always safe.
- **It fits its water:** scaled to the lane's flood and kept wholly inside it; it turns only while deep.

**The doorbell** (`C108Bell`) is a brass push with a small amber lamp, not red. He turns to the wall to press it.

**C-114's front door is shut** (`C114FrontDoor`, its lever `C114DoorHandle` and the child's pull-cord
`C114DoorCord`):
1. At the front step (game 157.26) he steps toward the camera, square to the door, and knocks twice (`Knock`), seen
   in a close three-quarter shot over his shoulder (`knock`, 28 mm).
2. He waits, about 2 s. Nobody comes.
3. He steps on 3 cm and pulls the cord the family hung from the lever so the child could reach it (`Tug`). The lever
   goes down, the latch gives, and the door swings in.

After a respawn the knock isn't repeated: he goes straight to the cord. Through the door, the street wall fades as in
*Pass 2*.

**The photograph** (`D5Photo`) is now her father in his sorter's apron, with Mara on his shoulders: IVO, from the
mugs in DL-02.

**Use without red** (`docs/direction.md`): the duct's grip, the junction box's lever and the desk's grip bar are worn
steel (`HandledSteel`); `MailSlot9` and the forwarding terminal are brass. Section 4's red grip bar is no longer red.

**Curiosities:** the hall light switch at game 158.72 and the radio at 163.0.

**Checkpoints:** `ringc` at game 135.25, `bedroom` at 164.1 and `forwarded` at 167.1.

## Pass 4 (built 20 October 2026)

From `docs/chapter1_pass4_plan.md`. Positions are game x (section x + 54).

**The drowning** (`art/dl05/build_dl05.py`): ring C drowned, and something has lived on what was left.
- **The high water** (`D5HighWater`, `D5HighWaterFacade`): a line at 1.4 m on every house in the street, C-114's
  included, above the lower tideline where the water stood longest.
- **A raft and a pram** (`D5Raft`, `D5Pram`), half under in the narrow point's front slot (150.2, 149.5), clear of
  the duct's bridge and the White's line: a kitchen table turned over, its legs sawn short, planks and an oil drum
  lashed to it; a coach-built pram on its side, nose down.
- **The lair** (`D5Lair`): in the flooded foot of the alley between C-108 and C-110 (147.05 to 147.95), the deepest
  water, a bank of silt with a bed of bones on it in rags, long bones, ribs, skull domes with no faces, a boot, a tin
  mug. One cold light on it (147.5). It barely reads through the water.

**The quest:**
- **"C-114 →"** painted on the barricade's face over the gap he crouches through (`WayC114`, 134.6).
- **His label:** on reaching the street (137 to 140) he checks his label the first time, and the camera goes in close
  on it.

**The White, less sensitive:** beside the lane's water he goes carefully whatever the auto-run setting. Shift or B
still runs, and running near it is still loud.

**Checkpoints and hazards:** unchanged.

## Pass 5 (built 20 October 2026)

See `docs/chapter1_pass5_plan.md`.

- **The duct into the dip:** it tips in like DL-01's cart.
- **The ending:** he walks out of C-114 into the dark, the screen fades, and the end card reads *End of chapter one*.
