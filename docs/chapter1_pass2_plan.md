# Chapter 1, pass 2: whimsy, curiosity, danger, depth

**Status:** built, 19 October 2026 (see below). Director's notes on the nine-scene build (Version 10).
**Decisions:** danger is **the failing place itself plus something living**; deaths are **shown, then cut** (he is a
machine: sparks and a dead eye, no gore; back in control in 1.5 to 3 s).

## Status: built

Pass 2 is in the game (`game/undelivered/index.html`) and the art builders (`art/pass2/build_pass2.py`,
`art/pass2/build_curios.py`, `art/white/build_white.py`, `art/dl05/build_dl05.py`, `art/dl04/hopscotch_clip.py`,
and the atrium in `art/dl04/build_dl04.py`). The scene docs in `docs/scenes/` each have a *Pass 2* section, and
`game/undelivered/README.md` describes the build. Positions below are game x.

| Plan item | As built |
|---|---|
| Hopscotch clip and shot (§1) | `HopscotchLong`, 288 frames (12 s): all eight squares and HOME, a wobble on 6, a cheer, two hops back. He plays it once on his own; after that, Use on the chalk plays it again. A crane from low over the chalk up to about 45° over the court, then down for the cheer. |
| Curiosities (§1, §6) | All twelve, with D-17's clips and moving props. The five early ones (cord lamp, scale, dispatch board, franker, mug) have warm light pools (not the cord lamp), red tags (not the cord lamp) and a glance as he passes, until each is used. The scale shows the Use glyph at once. A chime and "◆ n / 12" mark each find; the pause and end cards show "Curiosities n of 12 · letters posted n of 3". |
| Atrium art pass (§1, §7) | Recessed windows, balconies, stairs, cables and lamps, cliff homes and haze layers, at three levels of detail by distance from the balcony. |
| If-then sequences (§1, §4) | DL-06: two weights. DL-07: three steps plus the sump scare. DL-08: two plates into the counterweight, then the pawl. DL-09: the bell (or the junction box), the duct, then walk across. |
| Ring C as a street, the square (§1, §5) | Built: the back row (C-108, the alley, C-110, C-112), the kerb and the lower row's roofs, the cable of bulbs, washing lines, ring B's tier and the lift behind, and the square (noticeboard with the drawings of the White, bench, dry fountain, swing, MailSlot9). |
| C-114 as a home (§1, §5) | Front step and door, hall (switch, coat hooks, raincoat, shoe rack), kitchen and living room (table and three chairs, range and kettle, radio, lamp), the bedroom, the back door. The street wall (`C114Facade`) fades once he is through the front door; the cut edges are capped near-black. |
| The White (§2) | Model and ten clips (`art/white`); hears running (and landings), not walking; lured by a bell, scared off by the shorted cable; strikes about a body length onto an edge. |
| Arc beats (§2) | DL-03 drag marks and drain; DL-04 the bitten leg; DL-06 the roll in the heap's sump; DL-07 the sump; DL-09 the lane. |
| Deaths (§2) | Crush, shock, grabbed and fall, each with its own clip: sparks, the eye stutters out, a hard cut to black, back at the checkpoint 0.6 s later (1.3 to 2.2 s in all). |
| Hazards (§3) | The franking press (DL-02), the gallery collapse (DL-06), the shaft sump (DL-07), the cage crash and the tunnel cable (DL-08), the lane (DL-09). |
| New checkpoint | `landing8`: on the lit landing once the cage is held there, so the tunnel cable doesn't send him back up to the cage. |

**Where the build differs from the plan:**
- **The franking press** stands on the lane between the passage and the tube (13.62 to 14.28), so it is on the only
  route, not just guarding the letter.
- **The gallery collapse** is the panel between the day board and the residential access door (66.95 to 68.05), not
  just past the gate. It gives way once he is past it.
- **The tunnel cable** is in the antechamber, between the lit landing and the tunnel mouth (arcs at 93.04 to 93.44 and
  93.77 to 94.17), with a raised, dry hatch cover between the arcs to wait on.
- **The cage's step 1** has no call button. He steps in and it dips (0.38 m, or 0.22 with one plate), the brake squeals
  and holds, and it hauls itself back up; he has to step out and in again. It keeps doing this until both plates are
  in the counterweight's tray.
- **The cage ride** is unchanged from pass 1: the same speeds and pawl window. The heavier counterweight doesn't make it
  run faster.
- **The cage crash** is a fall death with a splash, and he is back on the upper landing beside the cage. The White
  isn't there: the cage's sump is its own water, not DL-07's, and no White lives in it.
- **The doorbell** lures the White for 12 s, not about 8.
- **The junction lever** scares the White away for 20 s (the cable sparks for 3.5 s). It can be thrown once per
  attempt; the bell can be rung again once it stops.
- **The White never leaves the water.** At DL-07's shaft sump it can't reach the platform, 1.75 m above it: it slaps
  the water with a splash and he is knocked back, unhurt. This happens over the latched platform and the first 0.3 m
  of the far landing, not on a walkway.
- **Falling into DL-07's sump** is a death (he sinks with a splash), but the White isn't shown taking him.
- **DL-03** has the drain and the drag marks, but no sound behind the wall.
- **The tunnel cable's grace** (the first touch only knocks him back) is once per game, not once per attempt.
- **The clock and the chair** swapped scenes: the stopped clock is on DL-06's gallery (61.38), and the sorter's chair
  is in DL-05's scanner corridor (48.8).
- **The coin viewer** shows the lit upper city. The cargo lift isn't built.
- **The hall light** stays on after he flicks the switch, rather than lighting the hall for a second.
- **The glance** at an early curiosity comes each time he passes it until he has used it, not only the first time.
- **The ring C lane's camera** is raised (2.15 m, looking down to 0.4 m, was 1.15 and 0.75) so the water and the White
  read.
- **Music:** the bed plays on through a death, but a cue that is playing (`refuge` on ring C's lane, for example)
  fades out on the respawn.
- **Large models** come in parts: `set.json`, `set.1.json`, `set.2.json` (10 MB of base64 each, under the host's
  16 MB limit). The game reads `parts` from the first file and fetches the rest.
- **Timings** for pass 2 are not yet measured: `tools/sim/`'s result files predate it.

## 1. The notes, and what we do about each

| Note | Response |
|---|---|
| The new puzzles felt better | Keep the ladder. Build on it; don't replace it. |
| The hopscotch needs its camera and a longer animation | Restore an authored shot (from above, chalk in frame), and a new ~11 s clip over all eight squares and HOME. Whimsy counts as an emotional beat for the camera rule. |
| Props look usable but aren't, with no visible link | A **curiosity** system: early ones made obvious, later ones become easter eggs. A count in the pause menu and on the end card. |
| The city reveal looks low-poly | An art pass on the atrium: silhouettes, bevels, window depth, balconies, cables, signage, lights, haze layers. |
| Puzzles are one-note; we need "if, then" sequences | DL-06 to DL-09 become 2- and 3-step sequences, the chapter's last third. The opening scenes stay single-step. |
| No neighbourhood around the house | Ring C becomes a street: homes on both depths, a small square, the ring's upper tiers in the background. |
| The house feels flat; the wall cut-outs are weird | C-114 is rebuilt as a home with a front door, hall, kitchen and living room, and the child's bedroom at the end. It is shown as a proper dollhouse section. |
| No sense of danger | Hazards that kill (shown, then cut) and **something living in the water**: the White. |

## 2. The White (something living)

**What it is:**
- A pale, blind cave animal, like a giant olm.
- About 2.5 m long: eel-bodied, with four small limbs and feathery pink gills, and no eyes, only pits.
- The flood of P.A. 310 came up from the deep cave river, and it came with the water. That is why ring C stayed
  sealed, and why nobody came back for the post.
- **Name:** the children of ring C drew it and called it "the White". Their drawings carry the name; the game never
  says it in words.

**How it hunts:**
- **By sound and vibration, never by sight.** Light and shadow don't hide him; quiet does.
- **Running** near its water is loud: ripples gather toward him, then it surfaces.
- **Walking** (Shift or B, or a half-pushed stick) is quiet. A noise somewhere else draws it there and holds it for a
  few seconds: a dropped weight, a bell, a splash.
- **It never leaves the water.** It can lunge about a body length onto a ledge or walkway at the edge. Water is its
  ground, so the rule stays readable.

**Its arc, like a mechanic's** (introduce, develop, twist, combine):

| Scene | Beat |
|---|---|
| 3 | **Sign:** wet drag marks run from a floor drain across the weight room and back. There is a sound behind the wall. |
| 4 | **Sign:** one fallen courier in the racks has lost a leg below the knee. The stump is bitten, not cut. |
| 6 | **Glimpse:** when the gate's bucket drops, something pale rolls once under the heap's sump water and is gone. |
| 7 | **First meeting, safe:** the goods lift shaft's sump. As the platform first rises, it surfaces below and sinks. On the walkway past the shaft, running makes it slap the walkway: he is knocked back, startled, but unhurt. That is the safe first use: it teaches that running is loud. Falling into the sump is a death. |
| 8 | **Develop:** the cage hangs over the same sump. A crash is a death: the cage drops into the water, and the White takes him. |
| 9 | **Combine:** the flooded lane in ring C is its home. Lure it with the doorbell, bridge the water with the duct, then cross quietly. |

**Deaths** (shown, then cut): a pale lunge, the jaws close, he is dragged under. One frame of the eye dying, a
crackle, a cut to black, and he respawns at the checkpoint. Music and ambience keep running.

## 3. Hazards (the failing place)

| Scene | Hazard | What it does |
|---|---|---|
| 2 | **The franking press**, still stamping its routine beside the Sorting Hall's tube | A rhythm-timed pass. Caught: crushed, with sparks. It is optional in DL-02: it guards the tube letter, not the path. |
| 6 | **The gallery walkway** | A section gives way behind him once he is through the gate. There is no going back, which you feel. Not lethal. |
| 7 | **The sump** | Death by the White (above). |
| 8 | **The cage crash** | Now a death: the cage drops into the sump, and he is back in the cage at the top. |
| 8 | **The tunnel** | A downed cable arcs on a wet patch: two arcs, a gap, cross in the gap. Not lethal on the first touch, which knocks him back. On the second touch, he is shorted out. |
| 9 | **The lane's live cable**, sparking at the far end of the flood | Part of the puzzle (below). |

## 4. If-then sequences, scenes 6 to 9

Each step below must leave a visible state change that sets up the next. The first five scenes stay single-step,
by design.

### DL-06 The Heap (2 steps)

The gate needs **two** weights in its bucket.
1. A single weight lifts the gate only half way: he can see it rise and stall.
2. The second weight is out on the heap's edge. Climbing down to it takes him past the sump, where the White first
   rolls.

The two weights go up in two carriers, or he rides one carrier up with a weight. Both work.

### DL-07 The Handbrake (3 steps, as built, plus the sump)

1. Trolley onto the pan; the platform rises.
2. Set the pawl.
3. Take the trolley off the pan, across, and up to the far rail.

The White's safe scare happens on the walkway between steps 2 and 3, so the player learns *walk* before DL-09
needs it.

### DL-08 The Slipping Cage (2 steps)

1. **The counterweight is too light.** The call button brings the cage halfway, and it sinks back. Its weight plates
   lie on the landing where they fell. Carry two plates into the counterweight's tray. (Carry, now in a new role.)
2. Ride the cage down. The heavier counterweight makes it run fast, so catch it with the pawl at the lit landing, as
   built (latch, against time). A miss is a death in the sump.

### DL-09 The Child at the Address (3 steps)

1. **The flooded lane is wider now** (about 4 m), and the White is in it. Push the duct toward the water while it
   is near and the splash brings it. Pulling back to the near side is safe.
2. **The doorbell:** C-108's bell (red button, lit) rings and rings, and the White swims to that end and noses at
   the step for about eight seconds.
3. **In that window, push the duct in at the narrow point, and walk across it.** Run, and it turns and comes.

**Optional:** the live cable at the far end shorts into the water if the junction box by C-110 is thrown. The
water fizzes, and the White flees for longer (about 20 s). This is an alternative to the bell, for players who look
around.

Then the house.

## 5. Ring C and the house

**The street:**
- Ring C is a lane curving around the cavern wall, with homes on both sides:
  - behind the lane, the homes we enter or look into (C-108, C-110, C-112, C-114);
  - in front of it, low walls, steps down to doors, planters, and laundry lines across the lane.
- A **small square** before C-114: a dry fountain, a bench, a swing frame with one swing, and a noticeboard with the
  evacuation notice and the children's drawings of the White.
- **Background:** ring B's tier of homes above, stairs between tiers, lit windows high up, and the lift up.
- The flood line runs at 1.0 m across everything below the square.

**C-114 as a home** (a dollhouse section: the front wall is cut away along a clean line with a dark section cap, so
it reads as a cut, not a hole):
- **Front step and door,** with the number, a mail slot, a boot scraper and a name card.
- **Hall:** coat hooks with a small yellow raincoat, a shoe rack, and a light switch he can flick.
- **Kitchen and living room:** a table with three chairs (one a child's), a stove, a kettle and a radio (a
  curiosity), and a window to the lane.
- **The child's bedroom** at the end: the bed, the window painting, the desk, the marks and the terminal, as now.
- **The path** runs naturally: front door, along the hall, through the living room, and into the bedroom. Doorways
  are real doorways with frames, and there are no holes in walls.

## 6. Curiosities

**The rules:**
- Each curiosity is a prop D-17 can **Use** for a small action and a payoff: a joke, a sound, a fact or a view.
- **Early ones are obvious:**
  - they sit in a pool of warm light;
  - they carry the red usable mark;
  - D-17's head turns to each as he passes, the first time;
  - the very first one, the parcel scale in DL-01, shows the Use glyph without waiting.
- **Later ones are easter eggs:** no light pool and no glance.
- **Found count:** the pause menu and the end card show "Curiosities n/12". Letters are counted separately.

| Scene | Curiosity | What happens |
|---|---|---|
| 1 | Parcel scale | He steps on, the needle swings, and it prints a ticket: POSTAGE DUE. He looks at it. |
| 1 | Cord lamp | (built) |
| 1 | Dispatch board | He finds his own route card (a house pictogram, C-114) and taps his label. |
| 2 | Franking machine | He franks his own hand. RECEIVED. He looks at it, pleased. |
| 2 | Named mugs | He picks up the one marked D-17, can't drink, and puts it back carefully. |
| 4 | The empty rack with chalked flowers | He sits in it, for a moment. |
| 5 | The stopped clock | He winds it. It ticks for a while. |
| 6 | The sorter's chair | He sits; the cushion fits him. |
| 8 | Hopscotch | (the moment; Use on the chalk plays it again) |
| 8 | Coin viewer on the balcony | He looks through it, and the camera zooms to the lit upper city and the cargo lift. |
| 9 | C-114's radio | It crackles into a children's song, half a verse. |
| 9 | The hall light switch | Click, a bulb, and the hall seen lit for a second as it was. |

## 7. The art pass

- **Atrium:** silhouettes with depth, window recesses and frames, balconies with rails, stairs between tiers,
  cables and pipes, painted signage, many warm point lights, two or three haze layers, and soft spill lights in the
  fog. Detail goes where the camera is; nothing goes behind the cave wall.
- **Ring C:** as above, built at the new quality bar.
- **Budget:** hold the frame rate. Merge static meshes, use instancing for repeated homes, and give the far tiers
  simplified geometry.

## 8. Order of work

1. Hopscotch clip and shot; the atrium art pass; the White (model, rig, clips). In parallel.
2. Ring C street and house; the hazards; the curiosity props and D-17's clips.
3. The game: deaths, the White's behaviour, hazards, curiosities, the puzzle sequences, the camera.
4. Measure (sims, mechanical floor), check visually, publish, document.
