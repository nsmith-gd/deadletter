# DL-05 The Child at the Address: production plan

**Status:** in production for the playable prototype (`game/undelivered/`)
**Source:** Dead Letter 45 Scene Overview, scene 05 (16 October 2026)
**Sequence:** DL-04 → DL-05 → DL-06, with no cut on either side
**Duration target:** 3 to 4 minutes. The overview gives 2; scenes run a touch longer from DL-04 on.

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
| **Down to ring C** | The stair off the DL-04 balcony brings him down to ring C's ledge. The cave city rises behind him. |
| **The seal** | A barricade of sheet metal across the lane: RING C SEALED · R.Y. 43, and tape. There is a gap under it; he crouches through. |
| **Ring C** | A dark lane of shuttered homes (C-108 to C-112), dead bulbs on a cable, a few still burning. A fallen duct to hop. |
| **C-114** | The last door stands open. He knocks on the frame twice and waits (`Knock`): nobody. He goes in. |
| **The hall** | A small pair of shoes beside a large pair. A lamp still on. |
| **The bedroom** | The rabbit on the bed, the painted window, the photograph. The desk fallen against the wall, the terminal above it. |
| **The desk** | He drags it clear. The music comes in: the parcel's three notes become a lullaby. |
| **The terminal** | The handshake, and the school destination. His label changes: the screen's school mark replaces the door. |
| **The rabbit** | On the way out, he sits it up. |
| **Out the back** | A back door onto a service stair, with a sign for the school on ring B. The end card. |

## 3. Layout (metres along the lane; this scene's floor is at 0)

```
x: 74.65-76.8 stair down from the DL-04 balcony (1.6 -> 0)   76.8 ledge   80.2-81.0 BARRICADE (gap 0.62 high)
   81.0-88.5 ring C lane (duct 84.2-84.6, 0.26 high)   88.2 knock   88.6 C-114 door (lintel 1.3)
   88.7-90.6 hall   90.6 inner door (lintel 1.25)   90.65-95.6 bedroom   95.6 back door   97.2 end
bedroom: bed 91.0-92.5 (top 0.42, behind the lane)   toy (92.2, top of bed)   painted window over the bed
         shelf and photograph 93.4   terminal 94.7 (screen 0.95 high, reader 0.72)   growth marks 94.0-95.3
         the desk: x 94.7 (half-length 0.36, 0.55 high), dragged left to between 93.4 and 94.15
```

Blender coordinates as before: the lane at y = 0, behind it +y, travel along +x. The back walls of the lane, the
hall and the bedroom are at y = 1.0. The homes are cut away toward the camera.

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
| `ChildDesk` | The fallen desk, its origin on the floor at the centre of its footprint (x 94.7). It leans back against the wall and covers it up to about 1.15 m. The game slides it along x. |
| `D5BackDoor`, `D5SchoolSign` | The back door frame and a sign: SCHOOL, RING B, with an arrow. |

## 5. Clips

| Clip | Frames | What it is |
|---|---|---|
| `Knock` | 48 | Facing a door frame 0.3 m ahead: he raises his right claw, knocks twice at about 0.6 m, waits with his head tilted, and lowers it. |
| `Present` | 64 | Facing a wall terminal 0.26 m away (the game turns him and steps him in): he leans his chest window toward the reader (0.72 high) and holds it still while the lamps answer (frames 20, 25 and 30). He straightens with a small nod (frame 50). |
| `Straighten` | 52 | Facing the bed: both claws to the toy (0.35 ahead, 0.5 high), he sits it up (the game rotates it between frames 14 and 26), pats its head once, and steps back. |

## 6. Camera

| Shot | When | Framing |
|---|---|---|
| `knock` | `Knock` | Low, behind and to the right of him at the doorway, looking into the dark hall. |
| `desk` | While the desk moves | Eases in a little from the room framing toward the wall (40 mm). |
| `marks` | The desk clears, the first time only | Close on the growth marks and the tree (50 mm, 3.5 s). |
| `terminal` | `Present` | Over his shoulder to the screen. |

## 7. Music

`child`: when the desk clears the marks. The music box plays the parcel's three notes, slowly, and becomes a
lullaby over a soft piano and strings. It is warm, then it thins to a single note as the terminal answers.

## 8. Checkpoints

- **ringc**: through the barricade.
- **bedroom**: just inside the bedroom.
- **forwarded**: after the terminal.
