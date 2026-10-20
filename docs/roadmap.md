# Dead Letter: roadmap to a full game

**Status:** proposed, 20 October 2026, after the director's playthrough of Version 17.

## Where we are

The eleven scenes built so far (DL-01 to DL-11) play in about 10:40 for the director and about 19 minutes for a
first-time simulated player. The director's verdict: good, but a tutorial, not a chapter. The game must run past two
hours, with more complicated, multi-step interaction puzzles and much more world building.

## The shape

The eleven scenes become the **prologue, "Undelivered"**: they teach every basic relationship (weight on a plate, a
body for a machine, counterweights, brakes, cycles, routing, the White) and end on a reveal. The chapters after it
follow `docs/scene_overview.md` (Attendance, Someone Home, The Work Above, Protective Custody, Recipient Found, First
Delivery). Each chapter is rebuilt for depth rather than count.

| Part | Scenes (overview) | Target |
|---|---|---|
| Prologue: Undelivered | 1–11 (built) | 15–20 min |
| 1 Attendance | 12–17 | 25–30 min |
| 2 Someone Home | 18–25 | 30–35 min |
| 3 The Work Above | 26–33 | 30–35 min |
| 4 Protective Custody | 34–41 | 30 min |
| 5 Recipient Found | 42–46 | 20 min |
| 6 First Delivery | 47–51 | 15 min |
| **Total** | | **about 2:45–3:00** |

## What changes from here on

- **Multi-step puzzles.** Each chapter has two or three set-piece puzzles of three to five steps. Each combines two
  relationships the player already knows with one new twist. For example:
  - at a cycle, wait for the right phase and latch it;
  - use the latched part as a counterweight;
  - ride the other side;
  - carry the piece back to undo it.

  A puzzle's state stays visible, so a player can stop, look and plan.
- **Puzzles that reuse the room.** The room a puzzle is solved in is crossed again from another side or level, and the
  solution changes it (a flooded floor drained, a carousel stopped and boarded).
- **Secret rooms.** At least two optional rooms per chapter, found by noticing something odd: a draught under a
  panel, a duct one crate-height up, a door that only opens from behind. Each one tells one small story by its layout
  (who sheltered here, what they did, what they left). Curiosities move into these rooms.
- **World building.** Every chapter shows how ordinary people lived, not only how they died: homes, a school day,
  shift rotas, repairs, gardens. The tableau principle from pass 6 holds: show what people did.
- **The thread.** The lights came back on, and someone turned them on. Each chapter brings D-17 closer to whoever did it
  (Mara, an old woman now, still working above), and the ending of the prologue shows it for the first time: one lit window in
  the dark city, high above.

## Order of work

1. **Prologue pass 6:**
   - the director's notes;
   - remains that come apart, and tableaux in place of cause signs;
   - the ending reveal (the lit window above);
   - two secret rooms;
   - renamed "Prologue".
2. **Chapter 1 Attendance:** design doc (`docs/chapter1_attendance_plan.md`) with three multi-step puzzles and two
   secret rooms, then build and playtest.
3. Then the next chapter, one at a time, each played and noted by the director before the next starts.
