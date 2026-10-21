# Chapter 1, pass 6: what they did, not what killed them

**Status:** built, 21 October 2026 (see *Status: built* at the end). These are the director's notes from playing pass 5 (Version 17), in two rounds.

**Liked:** performance feels better.

**The notes:**
- **The remains still read as whole skeleton people.** After this long they should have come apart: a skull rolled
  from the rest, ribs fallen in, long bones loose, clothes flat over what is left.
- **The cause-of-death signs are too on the nose.** A giant AIR notice is too obvious.
- **The storytelling should be more interesting.** Lay out a scene where something clearly happened, and show the
  people in it reacting naturally (trying, helping, waiting, giving up together) and then not making it.

## 1. The principle

Each set piece is a moment, frozen: something went wrong, people did what people do, and they didn't make it. The
player reads what happened from what they were doing, never from a sign that names the cause. Signs that would really
have been there (a lift's LAST CAR, a grade barrier) can stay; signs that exist to explain the deaths go.

**The timeline:**
- D-17 has been dormant 76 years (the opening card).
- The GDD's "nine years" is how long ago the last other resident died.
- Either way, the lower rings' dead have long since come apart.

## 2. Remains, taken apart

One shared builder, `art/pass6/remains.py`, makes remains that have come apart in place, in a few poses:
- **Seated, collapsed:** the clothes keep a little of the shape. The skull has dropped into the lap or rolled to the
  floor, the ribs have fallen in, and the arm bones lie across the thighs or by the hip.
- **Lying:** the clothes lie flat, with bones at the cuffs and collar. The skull is turned, the jaw apart from it, and
  a few small bones are scattered.
- **Huddled pair:** two sets of remains together, one arm's bones across the other.
- **Scattered:** a skull, a few long bones and a scrap of cloth.

**Look:** low-key and dry, never gory, with no faces. Linked duplicates keep the draw calls down, and a few variants
with mirrors and turns stop them reading as copies.

Every human remains in the chapter uses it:
- the DL-02 sorters;
- the DL-05 dead;
- the bones in DL-11's lair.

The weigh-in body stays a tied shroud, since it has to drag as one piece.

## 3. Tableaux

| Scene | What happened | What they did (what we see) | Goes |
|---|---|---|---|
| DL-02 | The fans stopped. | One climbed onto the sorting table to reach the stopped fan, tore its grille off and fell back; the grille lies on the floor by them. Two went for the stairs and found the bulkhead shut: one sits against it, a pry bar dropped beside, scratch marks above. The rest lay down together in the tea corner, on mailbags. A row of candle stubs on the table went out barely burned. | The AIR notice and the NO AIR gauge. |
| DL-05 | The food ran out. | The rows under sheets were laid out by the living, carefully, tags on toes. At the row's end, the last one lies uncovered beside a folded sheet: there was no one left to cover them. By the hatch, a queue that never moved: remains seated along the counter in line, bowls in laps. Tally marks scratched by the hatch, many days. | The NO RATIONS / GRADE 4 whitewash. |
| DL-10 | The last car went up and didn't come back. | They waited for it: remains seated on cases facing the lift gate, in the order they queued, one with a child's coat across their lap. | Nothing. |
| DL-11 | The water rose. | They went up: a ladder against a house to its roof, and on the roof two remains together among the things they carried up. The lashed table raft, empty, caught against a wall. | Nothing. |

## 4. Rules

- **Readable from the side camera at a glance,** in silhouette and with the scene's own light. Nothing goes between the
  camera and the lane.
- **Budget per tableau:** at most 25k triangles and 12 draw calls; no new lights in Blender. Ask the game for one if
  needed.
- **Gameplay:** no change to what D-17 can do, to the puzzles or to the lane's collision.

## 5. The second round of notes (an audio playthrough of Version 17)

**Liked:**
- DL-01;
- DL-02's hand prints and scratch marks;
- the covered rows in DL-05 ("a sad tone");
- dragging the body onto the weigh-in;
- the level design's storytelling in DL-06/07;
- the cage's visible plates;
- the hopscotch;
- the dark city;
- the junk that now reads as people's baggage;
- LAST CAR;
- no more judder riding the carrier.

| Note | Fix |
|---|---|
| The opening card is too on the nose, with no mystery. | Three lines: *P.A. 387 · Seventy-six years of dark. · Then, tonight, the lights came on.* Nothing says why. |
| The cart slips out of his hands into the pit. | The cart and the duct stop at the lip with their front wheels over, teetering. They go in when he lets go there, or when he keeps pushing into the lip for a moment: he gives a last shove (`Nudge`). |
| DL-02 has a struggle, but the sorters still sit at their desks. | Every remains in DL-02 is part of the struggle. One climbed to the stopped fan and fell. Two are at the shut stair door with a pry bar. The rest lay down together in the tea corner. |
| The couriers reveal comes late. | It fires the moment he is through the gate, however the gate was opened. A half-open gate can be crawled under, and then it never fired until later. |
| The courier snaps out of his hands at the bay. | He drags it all the way himself. The cradle only reaches out if he lets go near it. |
| DL-05: grab the skeleton's foot, not a handle. | The rope and toggle are gone. He takes the bare foot bones at the hem. |
| DL-06: handles clip through the carts. Allow two weights in one cart. | A carrier takes two weights side by side, and its own parcels make way; both tip out at the bucket. |
| An LED pops in the foreground at the city reveal. | Up Only's lit lobby, hidden for the crane shot, came back in view the instant the shot ended. It now comes back only once it is out of frame. |
| The music sometimes pops in out of nowhere. | Every cue fades in: 1.2 s by default, 3 s for the city, and short for the stingers. |
| DL-10's hand prints don't make sense. | Removed. The queue that waited for the last car to come back sits facing the gate instead. |
| DL-11: no floor under the seal's crawl gap; he floats. | Floored. |
| The M-and-sunshine card appears twice at C-114. | Only the door's remains. |
| Mara seems the only one with a room in C-114. | A stair up to the floor above, in the hall. |
| The ending ("a staircase that's a school") should be an emotional reveal. | Out of the back door is a landing on a dark well through the rings. He looks up, and the camera goes with him to the one lit window, 24 m above, and the new cable running down from it to a splice box here: someone up there turned the power back on. He checks his label and climbs the iron stair toward ring B as the picture fades. |
| Secret rooms that tell stories. | Two: the one who stayed (DL-06, behind a panel: a cot, tins, 384 opened letters pinned to the walls, a chair turned to face them), and the children's den (DL-09, through a vent by the hopscotch: a blanket fort, chalk drawings, handprints, Mara's crooked tree). Use at the gap; he goes in, the camera frames the room, and any move brings him back out. |
| It's a tutorial, not a chapter; the game must run past two hours. | This becomes the **prologue**. The plan for the rest is `docs/roadmap.md`. |

## Status: built

Built 21 October 2026:
- the art in `art/pass6/`:
  - `remains.py` (the shared remains builder);
  - `build_tableaux_depot.py` (DL-02, DL-05);
  - `build_tableaux_ringc.py` (DL-10, DL-11, C-114);
  - `build_ending_secrets.py` (the well, the window and its cable, the two secret rooms);
- the game in `game/undelivered/index.html`.

**Where the build differs from the plan:**
- **DL-05's queue** sits behind the counter's drag line, not along the counter: the counter's front is the path the body and drum take.
- **DL-11's roof pair** is on a coal store's tin roof against C-112, under the high-water line. The camera can't see real roofs.
- **DL-02's third tea-corner figure** is mostly hidden behind the mail-slot pillar.
