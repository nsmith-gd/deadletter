# Chapter 1, pass 6: what they did, not what killed them

**Status:** in build, 20 October 2026. These are the director's notes from playing pass 5 (Version 17).

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
