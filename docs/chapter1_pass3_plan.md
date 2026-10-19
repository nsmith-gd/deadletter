# Chapter 1, pass 3: clarity, two more puzzles, the collapse below

**Status:** in build, 19 October 2026. These are the director's notes from playing pass 2 (Version 12, finished in 16:57).

**What worked and stays:**
- the box-and-desk introduction;
- the walk past the dormant couriers;
- dragging the fallen courier to the bay;
- going back to pat its hand;
- the hopscotch and its dance;
- the city reveal and the viewer;
- delivering the ring C letter;
- the house now reading as a house;
- the bunny.

## 1. Fixes

| Note | Fix |
|---|---|
| DL-01: something drops from above, held up by nothing | The shutter counterweight's chain was culled by the camera (its bounds sat at the origin). It now always draws. |
| DL-02: trouble setting the box down (watch for it on mobile) | Setting down never refuses. If the spot in front isn't flat, he puts it at the nearest flat spot within reach, or at his feet. |
| DL-04: the bay struggles to take the courier | The cradle reaches out: once the courier is within 0.6 m of the bay, its arms swing out and draw it in. |
| Hitches when things first appear | At load, every material is compiled and every texture uploaded, with everything briefly made visible. The creature loads before the title card's Begin. |
| The creature clips out of small pools | Each water scales it to fit (smaller in the sumps). Its whole body is kept inside the water, and it turns only while deep. |
| DL-06: a weight only goes into a carrier at the dock | While the belt is stopped, he can load any carrier on the floor line. |
| DL-06: the weight tipping out isn't shown | The weight tumbles from the carrier into the bucket, visibly. |
| DL-06: the gate opening isn't in frame | While a loaded carrier climbs and the bucket drops, the framing widens to hold the gate. |
| DL-08: the cage puzzle is confusing | Reworked; see section 3. |
| DL-08: a pan back toward the cage before the hopscotch | The tunnel look-back is cut. With the cage and cable behind him it no longer reads. |
| The viewer pans too quickly | The viewer is his: left and right swing it slowly, and Use or Jump steps away. |
| DL-11: the White is too hard the first time | The first time it hears him it surfaces and hisses, a warning, and doesn't strike. Walking is always safe. It hears running from 1.4 m, not 2.2. |
| DL-11: the bell's red lamp; he doesn't turn to press it | The bell is a brass push with a small amber lamp. He turns to the wall and presses it. |
| DL-11: knocking at an open door | C-114's front door is shut. He knocks (a close, polite shot), waits, and nobody comes. He tries the handle, it gives, and he goes in. |
| DL-11: no sense of a neighbourhood | Ring C gets longer, with more homes on both depths: a row in front of the lane, the row he walks past, and the tier above. You pass through a street, not past one wall. |

## 2. Interactables without red

**Red stops being the code.** Players learned "touch anything red" and stopped looking. Instead:
- **Wear:** handles, bails, grips and levers are worn bright where hands went: polished metal showing through tired paint. The paint itself varies: faded oxide, green and black, as the period would have had it.
- **Light:** the scene's light falls on what matters (the established "pool of light" rule), and the important thing sits against a clean, readable background.
- **Motion and sound:** some things move or hum (a swinging tag, a ticking clock, a crackle), which draws the eye without colour.
- **The curiosity tags** are removed; their light pools stay.
- **Red is kept** only for what the world itself painted red: fire and alarm points, and danger stripes on machines that kill.

`docs/direction.md` changes to match.

## 3. DL-09 The Slipping Cage, made readable

The cage's two steps stay. Each is now shown before it is asked for:

**The counterweight**
- A balance gauge on the landing has two pans drawn on it and a needle that sits deep in "too light".
- The counterweight hangs in plain view beside the landing, with an open tray lit by its own lamp.
- When he steps in with the tray empty, the cage drops, the needle swings, the counterweight jerks upward, and the cage hauls back.
- The two plates lie in the lamp's pool. Each plate he drops into the tray moves the needle a third of the way.
- Plates can't be set down inside the cage; held near the tray, they go in.

**The pawl**
- He rides with his claw on the pawl lever, in his pose.
- A painted mark on the shaft wall lines up with the lit landing, and the lever's lamp blinks as the cage nears it.
- Use pulls the lever with a visible pull.
- A miss still kills him (the cage's sump). The respawn is at the top, with the plates still in the tray.

## 4. Two more puzzle scenes

Chapter 1 becomes eleven scenes. The two new ones carry most of the new story (section 5).

### DL-05 The Ration Hall (new; between the Racks and Return to Sender)

The depot workers' canteen and ration counter, the dregs of the refuge at its end. Families slept here when ring C flooded.

**Puzzle (carry, crank, crouch; three steps):**
- **The block:** the way on is through the serving hatch. Its steel shutter is wound by a winch on the counter, which drops it the moment the handle is let go.
- **Wrong assumption:** wind it up and run under. It slams, he's thrown back, and it stays shut. That's not lethal, but it's loud.
- **The answer:**
  1. carry a ration crate to the hatch, under the shutter's line;
  2. wind the winch;
  3. let go: the shutter slams onto the crate and leaves a gap he crawls under.

  The crate is in plain sight, stacked by the queue barriers. The crate-shaped dent in the shutter's bottom edge says it's been done before.
- **The tableau:**
  - queue barriers folded into a maze;
  - a ration board with chalked halvings;
  - the class notice "RELOCATION BY GRADE";
  - cots between the tables;
  - a shrine of names and candle stubs.
  - A child's crayon drawing taped to the counter shows a little robot carrying a parcel to a house, with a sun and a crooked tree, signed with an M. It is D-17 and Mara, before the player has met either name.

### DL-10 Up Only (new; between the city reveal and ring C)

The ring C relocation lift lobby: the place the families left from.

**Puzzle (carry, substitution, ride; three steps):**
- **The block:** ring C is below, and the only way down is the lift. Its panel has one button: UP. The stair beside it is collapsed.
- **Wrong assumption:** press UP and ride, and wait to come back down. The car won't leave empty. The doors stay open and the panel buzzes.
- **The answer:**
  1. **Make it think someone is aboard:** the car's floor plate weighs passengers. Carry a suitcase from the pile of left luggage into the car. The doors close.
  2. **Press UP from outside:** the car goes up.
  3. **Ride the counterweight down:** it comes down its open shaft beside the car's and stops at ring C's landing. He has to be standing on its frame when UP is pressed. The service door to the counterweight's shaft opens with a crank.

  The aha: riding the counterweight of a lift that only goes up.
- **The tableau:**
  - a painted queue line to the lift doors;
  - belongings dropped along it: a shoe, a doll, a birdcage;
  - signs: "RELOCATION — GRADES 1–2 ONLY" over the doors, with "EVERYONE" painted across "GRADES 1–2";
  - the last suitcase in the pile is tagged "C-114".

  He picks that suitcase to be the passenger. It goes up without him, the way its family did.

**Placement:** the new scenes are inserted with offsets, as in pass 1. A new OFF5 moves ring C right to make room for Up Only.

## 5. The story: the refuge's bottom, and Mara

**Premise (sharpened):**
- The refuge was built in grades. Grade 1 lives nearest the surface. The lowest rings (the depot, the works, ring C) are the labour grades: the people who sorted the post, ran the pumps and fixed the lifts.
- As the refuge emptied, homes above stood vacant, and grades stopped meaning anything. The lower families moved up because the system collapsed, not because they earned it.
- Mara's family is one of them. Her father sorted post in this depot on nights; D-17 was the courier on their route.

**What the player sees** (visuals first; every beat must read without text):

| Scene | Beat |
|---|---|
| 1 The Wake | D-17's parcel in close-up when he wakes, the label in a child's hand ("for Mara, C-114"), plus the dispatch board's route card. The depot's wall carries a grade chart: rings A to C, with C at the bottom in the plainest colour. |
| 2 The Sorting Hall | The tube letter is Mara's own: a child's letter to the post office, with a drawing of a little robot and a crying girl beside a house ("my parcel hasnt come, is D-17 lost?"). It reads without words. The mugs carry the night shift's names, one of them her father's. |
| 3 The Weight of the Job | Notices: "NIGHT SHIFT CUT · GRADE 3 TRANSFERS SUSPENDED". The drag marks. |
| 4 The Racks | One empty rack with chalked flowers; a courier memorial. |
| 5 The Ration Hall (new) | The collapse at its worst: rationing, cots, the grade notice, the shrine, the crayon drawing of D-17 and Mara. |
| 6 to 9 (depot, lift, cage) | Graffiti "WE KEEP YOU ALIVE" by the goods lift; a stencilled "UP IS FOR THEM", painted over by a later "EVERYONE UP"; a barricade, dismantled. |
| 10 Up Only (new) | The relocation lobby; the C-114 suitcase. |
| 11 The Child at the Address | The street, the house, the marks, the photograph: a father in a sorter's apron, with her on his shoulders. |

**The mystery:** what happened down here, and where did everyone go? The answer stays at the edges: up. Who sent the parcel? Her father; the label is his hand, the drawing hers. That is paid off later in the game.

## 6. Order of work

1. Game fixes (section 1), the interactable look (section 2) and the cage rework (section 3), in the game. Then the art agents:
   - the Ration Hall;
   - Up Only;
   - ring C's longer street with C-114's shut door;
   - the lore dressing across scenes 1 to 9.
2. Offsets and the two scenes' logic, then renumbering, the simulated player, measuring, a visual check, publishing and the docs.
