# DL-09 The Child at the Address: production plan

**Status:** built as a playable prototype (`game/undelivered/`), for director review
**Source:** Dead Letter 45 Scene Overview, scene 05 (16 October 2026)
**Sequence:** DL-08 → DL-09 → DL-10, with no cut on either side

> **Renumbered 18 October 2026.** Chapter 1 now has nine scenes; this was DL-05. The rework in
> `docs/chapter1_plan.md` and `docs/chapter1_build_spec.md` supersedes this plan where they differ.
**Duration target:** 3 to 4 minutes. The overview gives 2; scenes run a touch longer from DL-07 on.

## 1. What the scene must do

| Requirement (from the overview) | How the build meets it |
|---|---|
| Slide a fallen low desk clear of a forwarding terminal | In the child's bedroom of home C-114, a small desk has fallen against the back wall, in front of the forwarding terminal. D-17 grabs it, as he did the trolleys, and drags it clear. It scrapes, heavy for him. |
| Moving it exposes the growth marks and tree carving behind it | Behind the desk, pencil lines climb the wall, one per year: M 2 (R.Y. 38) to M 6 (R.Y. 42). Beside them, scratched into the plaster, is a crooked tree with a knot in one branch. |
| Presenting the parcel retrieves the school destination | Use at the terminal. D-17 leans his chest window to its reader, and his three lamps answer its three: the handshake again. The screen reads C-114, then NO ONE AT THIS ADDRESS, then FORWARD TO SCHOOL with the school's mark, RING B, and the class of R.Y. 42. |
| A patched toy, imagined sunlight, and the parent-and-child photograph make the addressee concrete | A patched rabbit slumps on the bed. Over the bed, a window painted on the wall, lit warm from behind, with a sun. On a shelf, a photograph of a parent kneeling beside a small child. |
| Establish Mara's crooked tree with a knot in one branch | The carving, revealed by the desk. The photograph shows the same tree, chalked on a wall behind them. |
| D-17 straightens the toy, then leaves the bedroom undisturbed | Passing the bed, he stops to sit the rabbit upright and pats its head (`Straighten`). It is brief, and any move cancels it. He leaves by the back door; nothing else is touched. |
| Move slightly closer as the desk shifts; the growth marks occupy the new empty space | As the desk scrapes, the camera eases in a little. When it clears, the camera holds on the marks and the carving for a moment, the first time only. |

**Player understanding:** an abstract addressee → a particular child, with a home and a parent.

## 2. Beats

| Beat | What happens |
|---|---|
| **Down to ring C** | The stair off the DL-07 balcony brings him down to ring C's ledge. The cave city rises behind him. |
| **The seal** | A barricade of sheet metal across the lane: RING C SEALED · R.Y. 43, and tape. There is a gap under it; he crouches through. |
| **Ring C** | Abandoned and nearly dark: shuttered homes (C-108 to C-112), dead bulbs on a cable, two still burning, one of them failing. A fallen duct to hop. |
| **C-114** | The last door stands open. He steps up beside it, knocks on the jamb twice and waits (`Knock`): nobody. He goes in. |
| **The hall** | A small pair of shoes beside a large pair. A lamp still on. |
| **The bedroom** | The rabbit on the bed, the painted window, the photograph. The desk fallen against the wall, the terminal above it. |
| **The desk** | He steps in to its red grip bar and drags it clear. The music comes in: the parcel's three notes become a lullaby. |
| **The terminal** | The handshake, and the school destination. His label changes: the screen's school mark replaces the door. |
| **The rabbit** | Passing the bed on his way to the desk, he sits it up. |
| **Out the back** | A back door onto a service stair, with a sign for the school on ring B. The end card. |

## 3. Layout (metres along the lane; this scene's floor is at 0)

```
x: 74.65-76.8 stair down from the DL-07 balcony (1.6 -> 0)   76.8 ledge   80.2-81.0 BARRICADE (gap 0.62 high)
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
