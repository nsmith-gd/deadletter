# Chapter 1: Attendance (DL-12 to DL-14)

**Status:** in build, 21 October 2026. These are the first three scenes after the prologue, built to the roadmap's
standard (`docs/roadmap.md`):
- multi-step puzzles that combine what the prologue taught;
- at least one secret room;
- the tableau principle;
- voice letters (`docs/voice_script.md`).

**Where:**
- The prologue ends on the iron stair up from ring C's well. Chapter 1 starts at its top, on ring B, at the refuge's
  lower school.
- The chapter is its own set (`art/ch1/`, exported as `attendance.json`), loaded when the player continues from the
  prologue's end card, or picks DL-12 to DL-14 on the scene select.
- **Coordinates:** game x from `OFF6 = 200`; floor at height 0; the lane at z 0. Blender (x, y, z) becomes game
  (x, z, −y), as in the prologue.

**What the school says:** it was built for many more children than it ever had. It kept running its routines (the
register, the lesson, the window drill) for pupils who stopped coming. One of the last of them was Mara, who drew her
crooked tree where nobody was meant to look.

## The mechanics, and what they build on

| Scene | Known from the prologue | New, or a twist |
|---|---|---|
| DL-12 | A plate reads a presence (DL-03). A body stands in for a person (DL-04, DL-05). Carry an item and climb (DL-02). Push (DL-01). | A machine wants **two** conditions at once: someone present, and their coat on the peg. |
| DL-13 | A stand-in for a person (DL-12). A brake latches a moving thing (DL-08). | **Reading a cycle**: the lesson's steps come out in turn. Throw the brake in the one moment they are all out. |
| DL-14 | A latch (DL-08, DL-13). A crank (DL-01). | **Paired outputs**: one chain drives two blinds, so one goes up as the other comes down. Jam one with an object, the window pole, to have both. |

## DL-12 Coats Without Children (x 200 to 216): developed puzzle, about 4 minutes

**The room:**
- He comes up the stair into a long cloakroom, the school's way in.
- **Coat hooks** fill the back wall: six rows, numbered, hundreds of them.
- Almost every hook is empty. A handful hold the same few coats, patched and patched again.
- At the far end an **attendance gate** (a barred grille that winds up) bars the way into the school.
- In front of the gate, an **occupancy strip** in the floor, with a post carrying two lamps:
  - PRESENT;
  - COAT 7.

**Layout (game x):**

| x | What |
|---|---|
| 200.0–201.6 | Arrival: the stair's top door (left edge); the school's mark over the arch (a sun over an open book). |
| 202.2–203.0 | The **lost-property bin**: a wire cage on castors, top 0.55. A small child's coat lies folded on top (carriable item `coat`). |
| 203.6–204.4 | **Teaching figures**: a rack of jointed, child-sized wooden pupil models on wheeled stands, chained in (story: the class). |
| 207.0 | The free figure, `AttFigure`, on the lane between the bench and the strip. Pushable: half-width 0.22, height 0.95. |
| 204.9–205.9 | A **bench** across the lane (top 0.42, solid), under peg 7. |
| 205.4 | **Peg 7**, on a coat stand at the bench's back edge: hook at height 1.18, with a small lamp over it that blinks when wanted. The coat hangs from it (the game parents it there). |
| 208.0–208.8 | The **occupancy strip** (floor plate) and its lamp post (PRESENT, COAT 7) at 208.9, behind the lane. |
| 209.3–209.5 | The **attendance gate**: it winds up to 1.3 while both lamps are lit, and drops when either goes out. |
| 209.5–216.0 | The corridor to the classroom door at 216. |
| 211.6–212.3 | The **secret room's door**, ajar, low in the corridor's back wall. |

**The puzzle:**
1. **He steps on the strip.**
   - PRESENT lights and COAT 7 blinks.
   - A buzzer sounds and a voice from the gate's speaker says the register line (`att_gate_*` in the voice script).
   - The gate stays down.
   - Peg 7's lamp blinks over the bench.
2. **The coat.** He takes the coat from the lost-property bin, climbs the bench while carrying it, and hangs it on
   peg 7 (Use). COAT 7 lights steady.
3. **Back on the strip:** both lamps light and the gate winds up. But stepping off the strip to reach the gate drops
   PRESENT, and the gate slams. The gate is a step too far from the strip.
4. **The aha:** a stand-in pupil. He pushes the free teaching figure (`AttFigure`, between the bench and the strip) onto
   the strip. The route is easy; the difficulty is the idea: the gate wants a pupil and a coat, and he can't be the
   pupil.
5. **Through:** with the figure on the strip and the coat on peg 7, the gate stays up and he walks through. The figure
   stays behind, the only pupil present.

**The secret room: lost property** (opening at 211.6–212.3, room x 211.0–214.5, z −1.2 to −3.6):
- The caretaker's room. Every lost thing kept and labelled in rows on shelves: mittens, a shoe, a scarf, a lunch tin,
  each tagged with a name and a date.
- On the desk, the register, open. Its columns of ticks thin out page by page until a page with one tick (M.).
- The caretaker's own coat on the door hook. Nobody died here.
- A **voice-card player** on the desk with a card in it: `att_caretaker` (Use to play).

**The way on:** the classroom door at 216.

## DL-13 The Repeated Lesson (x 216 to 232): developed puzzle, about 5 minutes

**The room:**
- A classroom with rows of small desks. Teaching figures sit at most of them: the school sat its models in the empty
  places.
- At the front, the **lesson apparatus**: a tall wooden-and-brass machine against the wall that teaches how a tree grows.
  - While a lesson runs, three **steps** (hinged boards) fold out of the wall one after another.
  - A **model tree** assembles in a glass case above them, then everything folds away and the lesson starts again.
- A horn **speaker** plays the recorded lesson, `att_lesson`, in time with it.
- Above the apparatus, a **gallery** (height 2.4) runs to the door out, at x 230.6. Behind glass on the gallery, a
  **seedling tray**: real seedlings, long dead, except one pale shoot.

**Layout (game x):**

| x | What |
|---|---|
| 216.0–217.0 | The door in from the corridor. |
| 217.2–218.0 | A **rack of teaching figures**, one free: `AttFigure2`, pushable, at 217.6. |
| 219.2–219.9 | The **front seat**: a pupil's desk and chair facing the apparatus, with an occupancy pad in the seat (reads the figure pushed against it; the figure's stand slots under the desk). Lamp: LESSON. |
| 220.6 | The **brake**, a red pawl lever on the apparatus's base, linked by a visible rod along the floor to the cycle dial at 224.0, height 1.4. The dial has a hand that goes round once per lesson, with three marks (the steps out) and a red sector (all out). |
| 224.6–225.4 | Step 1 folds out at height 0.55 (lane-deep, z −0.9 to +0.3). |
| 225.6–226.4 | Step 2 at 1.05. |
| 226.6–227.4 | Step 3 at 1.55. |
| 227.6–232.0 | The gallery at 2.05 (one mantle up from step 3), with the seedling tray and the door out at 230.6. |
| 222.0–228.0 | The **model tree's case** above, at height 2.6–3.6. |

**The cycle (one lesson, 12 s; the game drives it):**

| t (s) | What happens |
|---|---|
| 0 | The bell. |
| 1.0 | Step 1 out. |
| 2.6 | Step 2 out. |
| 4.2 | Step 3 out. |
| 4.2–5.6 | All three out: the dial's red sector. |
| 5.6 | Step 1 folds. |
| 6.2 | Step 2 folds. |
| 6.8 | Step 3 folds. |
| 6.8–12 | The model tree finishes, holds, and dismantles. |

**The puzzle:**
1. **Start the lesson.** The apparatus is silent. The LESSON lamp is dark over the front seat. He pushes the free
   figure to the front seat. LESSON lights, the bell rings and the lesson begins: voice, steps, tree. (The DL-12 idea,
   now a key.)
2. **Try to climb it.** Step 1 is easy. By the time he is up, step 2 is folding, and he drops to the floor (safe;
   nothing here kills). The steps are a staircase only for a moment.
3. **The brake.** The red pawl at 220.6 (the DL-08 handbrake, in a new role) stops the dial's hand where it is, and
   everything stops with it.
   - Thrown at the wrong moment, it holds whatever is out (one step, or none). Use again to release.
   - Thrown in the red sector, all three steps stay out. The lesson stops mid-sentence: the recording sticks on one
     word, and the machine strains.
4. **Climb** steps 1, 2 and 3 and the gallery: four mantles, and the way out.

**What the room says:**
- The lesson ran for decades to an audience of models.
- The real seedlings behind the glass died waiting for someone to water them, while the machine built its perfect
  wooden tree over and over.
- One pale shoot is still alive. Nothing explains it.

## DL-14 The Window (x 232 to 248): developed puzzle, about 4 minutes

**The room:** a corridor whose back wall is a row of tall classroom windows, each glazed over a painted panel of
blue sky, a field and a sun. Each window has a roller blind, and each blind has a window-cleaner's ledge on hinges
under it that swings out when the blind is down. Two blinds, A and B, run on one endless chain over pulleys along the
ceiling to one crank at 242.4. Wind it one way and A comes down while B goes up; wind it back and B comes down while A
goes up.

**Layout (game x):**

| x | What |
|---|---|
| 232.0–233.0 | In from the classroom's gallery: the floor here is the gallery level, height 2.05. A stair down, 233.0 to 234.4, to the corridor floor at 0. |
| 235.0 (wall) | The **window pole**, a long brass-hooked pole for high windows, starts laid through A's wheel bracket (carriable item `pole`). |
| 235.4–236.2 | A **teacher's desk** across the lane, top 0.62. |
| 236.4–237.6 | **Blind A** and its ledge: out, at height 1.1, lane-deep, when A is down. |
| 237.8–239.0 | **Blind B** and its ledge: out, at height 1.6, when B is down. |
| 239.2–240.2 | The **way on**: a high hatch in the wall at height 2.15 (one mantle from ledge B), to DL-15. |
| 235.0 (floor) | **A's chain wheel**: a sprocket in a bracket low on the wall, between the pole and the desk, with a slot the pole fits through to jam it. Its chain runs up the wall and along the ceiling to A's roller. (Moved from 236.6 after the first play test: under ledge A it could only be reached by circling back from the far side.) |
| 242.4 | The **crank**, with the chain running up from it over the ceiling pulleys to both blinds: visible all the way. |
| 233.2–233.8 | The **secret room's door**: the stock cupboard under the stair. Entered from the stair's foot (Use at 234.3–234.7; pass 8, clear of the wheel's 234.75–235.25). |

**The puzzle** (reworked in pass 8, after the Version 19 play test: the pole had never been introduced, and the
player didn't know what it was for):
1. **The pole starts in A's wheel**, laid through both lugs of the bracket, where the teacher left it, holding A up.
2. **Wind the crank.** A can't move, so the chain slips on its locked wheel: B comes down alone, its ledge swings out at
   1.6, and the pole rattles in A's wheel. He looks round at the rattle. The jam is shown before it is needed.
   Ledge B alone is out of reach from the desk.
3. **Take the pole out** (Use at the wheel), put it down, and wind the crank: now the pair runs free. A comes down
   (ledge A at 1.1) and B goes up.
4. **The aha:** put the pole back while A is down (Use at the wheel, carrying it). The pole holds A wherever A is.
5. **Wind the crank again.** B comes down alone; both ledges are out.
6. **Climb:** desk, ledge A, ledge B, the hatch.

The pole can go in and come out as often as he likes; whatever A is doing when it goes in, A stays. The peel (below)
no longer takes the camera: it happens in the room's frame, with the music, and doesn't pull attention off the wheel.

**What the room says:** as B comes down, its blind catches the corner of its painted panel and peels it back. Behind
the panel is concrete, not sky, and a child has drawn on it in pencil, over and over, a crooked tree with a knot in one
branch: Mara's mark. She looked behind the picture she was given.

**The secret room: the stock cupboard** (door at 233.2–233.8, under the stair, room x 232.4–235.0, z −1.2 to −3.4):
- The last teacher's corner: a chair and a lamp, chalk and exercise books in boxes, and a voice-card recorder.
- A stack of recorded cards, addressed to pupils' families and never sent, tied with string.
- One card is in the player: `att_teacher` (Use to play).

## Checkpoints

| Name | Where |
|---|---|
| `school` | DL-12 arrival, x 200.6 |
| `register` | through the gate, x 210.0 |
| `lesson` | DL-13 door, x 216.6 |
| `gallery` | on the gallery, x 228.4 |
| `window` | DL-14, foot of the stair, x 234.6 |
| `hatch` | through the hatch: the end of what is built |

## Art: what the game moves (names and pivots)

Every moving object's origin is its pivot, in final world coordinates.

| Scene | Moved or animated by the game |
|---|---|
| DL-12 | `AttFigure` (origin at the floor, centre); `AttGate` (rises along y); `AttLampPresent`, `AttLampCoat`, `AttPegLamp` (emissive); `AttCoat` (the carried item; origin at its hanger hook). |
| DL-13 | `AttFigure2`; `AttStep1`, `AttStep2`, `AttStep3` (hinged at the wall, rotating about x, so 0 is out and −90° is folded flat against the wall); `AttDialHand` (rotates about z); `AttPawl` (rotates about x); `AttLessonLamp`; `AttTree` parts (`AttTreeTrunk`, `AttTreeBranch1` to `AttTreeBranch3`, `AttTreeLeaves`), which the game scales from 0 to 1 in turn. |
| DL-14 | `AttBlindA`, `AttBlindB` (roller blinds, scaled along y from their top roller); `AttLedgeA`, `AttLedgeB` (hinged at the wall, as the steps are); `AttPanelPeel` (the panel corner, hinged); `AttCrank` (rotates about z); `AttWheelA` (rotates); `AttPole` (the carried item); `AttChain` (texture scroll, or static). |
