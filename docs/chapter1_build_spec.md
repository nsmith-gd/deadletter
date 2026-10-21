# Chapter 1 rework: build spec

**Status:** in production, 18 October 2026
**Plan:** `docs/chapter1_plan.md` · **Rules:** `docs/puzzle_principles.md` · **Direction:** `docs/direction.md`

This is the working spec for the sets, props and clips of the reworked Chapter 1, and for the game logic that drives
them. Numbers are metres.

## 1. Conventions

### Coordinates
- **Axes:**
  - Blender (x, y, z) maps to the game as (x, z, −y).
  - The lane is at y = 0. Behind the lane is +y; the camera is in front, at −y.
  - Floors are at z = 0 unless stated.
- **Scene numbering:** new numbers from here on.

  | Scene | Name | Built in | Built where |
  |---|---|---|---|
  | DL-01 | The Wake | `art/dl01` | at 0 |
  | DL-02 | The Sorting Hall | `art/sorting_hall` | **new**, world coordinates |
  | DL-03 | The Weight of the Job | `art/dl02` | moved by OFF2 |
  | DL-04 | The Racks | `art/racks`; its first half is the existing racks hall in `art/dl02` | **new**, world coordinates |
  | DL-05 | Return to Sender | `art/dl03` | moved by OFF3 |
  | DL-06 | The Heap | `art/dl03`: the gallery end of the same space | moved by OFF3 |
  | DL-07 | The Handbrake | `art/dl04`, belt side | moved by OFF3 |
  | DL-08 | The Slipping Cage | `art/cage` | **new**, world coordinates |
  | DL-09 | The Child at the Address | `art/dl04` (tunnel side) and `art/dl05` | moved by OFF4 |

- **Offsets** (`build_dl01.py` and the game, kept in step):

  | Offset | Value |
  |---|---|
  | `OFF2` | 13.0 |
  | `OFF3` | 21.0 |
  | `OFF4` | 30.0 |

  The existing builders still work in their original coordinates, and `build_dl01.main()` moves their objects
  afterwards. New scene modules build **in world coordinates**, computing their positions from `dl01.OFF2..4`.
  The free gaps are:

  | Gap (world x) | Filled by |
  |---|---|
  | 11.9 to 25.0 | the Sorting Hall |
  | 38.6 to 47.9 | the Racks (end of the racks hall to the scanner corridor) |
  | 85.6 to 94.6 | the Slipping Cage (top of the returns belt to the tunnel) |

### D-17 and his movement (the game's physics)
- **Body:**
  - 0.71 m to the top of his head; half-width 0.17.
  - Stands about 0.62 high when crouched under things; the crouch gap is 0.62.
- **Movement:**
  - Walk 0.9 m/s, run 1.6 m/s (auto-run is the default).
  - Jump apex 0.4 m; a running jump clears about 1.2 m of gap.
  - **Mantle** (climb onto a ledge): from standing, 0.24 to 0.62 above his feet; airborne, up to about 0.72.
  - Steps under 0.07 he simply walks.
- **Carrying and pushing:**
  - Carry walk 0.42 m/s; push 0.55, heavy push 0.34, drag 0.26.
  - Push and drag grips are at **0.44 high**, like the trolley's push bar and the desk's grip bar, so the existing
    `PushWalk`/`PushIdle` clips fit them.
  - Lifting uses `Lift`, `CarryIdle`, `CarryWalk` and `SetDown` (`art/dl02`). The bail or handle sits on top of
    a load, about 0.22 high.
- **Clips:** the existing clips are listed in `build_dl01.main()` and each scene's `add_clips`.
  - New clips need unique names. Check arm clearance with
    `/tmp/claude-0/-home-user-deadletter/228ec196-fd3f-53d1-bee6-a1339d260a7f/scratchpad/clipfix/arm_clearance.py`.
  - The forearms must stay outside the pod, the chest-window housing and the head.

### Look and readability
- **Interactables are red** (red handle, strap, rim or lever), and nothing else on the lane is red. Story props
  (letters, photographs) are lit instead.
- **Every mechanism shows its linkage:** a cable, chain, rod or pipe from the control to what it moves.
- **The goal or blocker of each puzzle is in frame** and lit.
- **Lower levels are dark;** the path and the interactables stay readable.
- **Materials:** use the shared `m[...]` palette where it fits, for example `steel`, `concrete`, `wall`, `wood`,
  `red`, `yellow`, `paper`, `pigeon`, `plaster`, `rust`, `sheet`, `stone`, `rock`, `water` and the bulb emissives.
  Report any new material names, so the game can map them (WORN, PLAIN, EMIT or image).
- **Text:** wordless where possible; pictograms, numbers, years (P.A.) and ring and room numbers.
- **Budget:** keep each new scene's meshes and textures under about 0.8 MB in `set.glb`. Use quads for distant
  detail, and no shadows on decals.

### Object naming
The game looks objects up by name. Give movable parts their own objects, with the origin where the game needs to
pivot or slide them (stated below). Static dressing can be merged.

## 2. The letters (shared by DL-02, DL-06 and DL-09)

Undelivered letters are Chapter 1's secret. D-17 finds a letter, picks it up, and posts it at a red mail slot, where
it is stamped. Story first: **the main story must read without them**; they add depth for those who look.

**Props:**
- Each letter is an envelope, 0.16 × 0.11, with a front texture: a ring and room address, an P.A. 310 or 43
  postmark, a stamp and a small pictogram.
- `HeldLetter`: a single envelope mesh with its origin at its centre. The game attaches it to his right claw
  during `PickUpLetter` and `PostLetter`.
- Mail slots `MailSlot2`, `MailSlot6` and `MailSlot9`: a post pillar or wall box, with a red rimmed slot at 0.55
  high, and a small stamp lamp `SlotLamp2/6/9` (emissive).

**Clips (Sorting Hall agent):**
- `PickUpLetter`, about 30 frames: he bends, picks a letter off the floor 0.25 ahead with his right claw, looks at
  it, and tucks it to his chest.
- `PostLetter`, about 40 frames: facing a slot 0.3 ahead at 0.55 high, he raises the letter and pushes it in. A
  small pause, then a pleased bob.

## 3. DL-02 The Sorting Hall (new) · `art/sorting_hall/build_sorting_hall.py`

**World x:** 11.9 to 25.0. The weight room (DL-03) now starts at 25.1.

**Role:**
- Carry, introduced: carry a box and use it as a step.
- The letters: the first one, taught on the path.
- Curiosities and the first sign of the flood.

**What is there already:**
- The passage behind the wall: `Passage`, from `art/dl02`, staying at x 9.5 to 13.9. It runs behind DL-01's back
  wall at y = 1.25.
- D-17 walks through it from DL-01's bulkhead and turns out toward the camera at **x 13.2**. The hall's back wall
  needs a doorway there: x 12.9 to 13.5, 1.05 high, at the passage.
- DL-01's floor (`Floor`) now runs on to x 43, so the hall can sit on it. The hall needs its own walls, ceiling
  (about 4.5 m) and dressing.

**Layout:**

| x | What |
|---|---|
| 12.0 | The hall's left wall: the bulkhead side. DL-01's bulkhead ends at 12.44. |
| 13.2 | Emerge doorway, in the back wall at y ≈ 1.0. |
| 14.0 to 15.2 | **The tube station.** A pneumatic tube terminal on the back wall: brass tubes from the ceiling into a delivery cup at x 14.6, 0.9 high, y ≈ 0.85. `TubeCup` (static), and `TubeLetter`, an envelope in the cup with its origin at its centre. When he first passes, the game drops it from the cup to the floor at x 14.6. |
| 16.0 | **`MailSlot2`**: a post pillar on the lane's back edge (y ≈ 0.45) with a red rimmed slot at 0.55 high, and `SlotLamp2`. |
| 15.0 to 17.0 (background) | Tea corner: a small table with mugs and a kettle. "Courier of the year" board on the back wall with faded photographs; the last frame is a pale silhouette. The notice `RingCNotice`: ring C, a water-drop pictogram and "P.A. 310", with a crossed-out envelope (deliveries suspended). |
| 17.4 | **The box**, `CarryBox`: a parcel box 0.40 (x) × 0.34 (y) × 0.32 (z) with a red strap and a handle on top. Origin at its base centre. Carried like the weight. |
| 18.6 to 22.6 | **The sorting table**, `SortTable` (static, a solid surface). Top at **0.75**, too high to climb from the floor, front face closed with drawers so nothing passes underneath. Sorting trays and a few parcels on top, at the back half only, so the walking strip along the front of the top stays clear. |
| 22.6 to 23.5 | **The collapse:** a fallen pigeonhole wall across the lane, 2.2 high, blocking the floor route. It is static and reads clearly as impassable. |
| 22.4 to 25.0 | **The gantry**, `SortGantry`: a steel walkway at **1.35** (deck top), resting on the wreck and the far wall. It leads to a lit doorway into the weight room. From the table top, the gantry is a 0.6 climb. |
| 25.0 | The doorway, **cut by this agent in `art/dl02`'s weight-room left wall:** x 25.0 to 25.32 after the move (12.0 to 12.32 in that file's own coordinates), from 1.35 to 2.4 high, with a warm lamp `GantryLamp` above it. He drops from the gantry to the weight room's floor; that's fine. |

**Lighting:**
- One work lamp over the table (warm).
- The tube cup glints.
- The gantry doorway lamp is the brightest point, so it reads as the goal.
- The tea corner is dim.

**Linkage:** the tube's brass runs are visible from the ceiling to the cup.

**Clips:** `PickUpLetter` and `PostLetter` (section 2). Carrying the box reuses `Lift`, `CarryWalk` and `SetDown`.

## 4. DL-04 The Racks (new) · `art/racks/build_racks.py`

**World x:** 38.6 to 47.9. The existing racks hall (`art/dl02`, now at world x 31 to 40.1) ends at about 40.1, and
the scanner corridor (DL-05) starts at 47.9. Continue the hall's back wall, ceiling, floor dressing, row lighting and
tubes to 47.9, so the join is invisible.

**Role:**
- Substitution, developed and twisted.
- Carry, twisted: he moves one of his own.

**Layout:**

| x | What |
|---|---|
| 39.5 to 43.0 | The end of the racks: two more rack bays (empty slots, tags). One slot is empty, with flowers chalked on the wall above it. |
| 41.2 | **The fallen courier**, `FallenCourier`: a dormant courier (D-17's model, a spare rig as `art/dl02/build_couriers` does) lying on its side on the lane, 0.75 long along x. Baked to a static mesh, origin on the floor at its centre. It has a red tow loop on its back, on a short strap, with the loop at **0.44 high** at its left end (x ≈ 40.85), so the push/drag clips fit. Its three chest lamps are a separate mesh `FallenLamps` (emissive material `FallenLamp`). |
| 44.4 to 45.4 | **The bay plate**, `BayPlate`: a charging bay floor plate with a courier pictogram, origin at its top centre, so the game can press it down. |
| 44.9 | **The cradle**: two arms that lift a courier from the plate into a seated charging pose. `CradleArmL` and `CradleArmR`, each pivoting at its shoulder on the bay's back frame (y ≈ 0.7). `SeatedCourier`: the same courier baked seated in the cradle (hidden until used), with `SeatedLamps`. |
| 45.6 to 46.0 | **The bay door**, `BayDoor`: a sliding shutter 1.6 high across the lane. Origin at its base, so the game lifts it. Above it, three lamps `BayLamp0..2` (emissive). The door's frame and a cable from the plate to the door's motor are visible. |
| 46.0 to 47.9 | Beyond the door: a short service passage into the scanner corridor. |

**Lighting:**
- The bay is lit cold and clinical.
- The fallen courier lies in a pool of the racks' light.

**Clips:**
- `TouchHead`, about 48 frames: after the cradle takes the courier, D-17 lays his right claw on its head for a
  moment and lets go.
- Dragging the courier reuses `PushWalk` and `PushIdle`, with the tow loop at 0.44.

## 5. DL-06 The Heap (rework of `art/dl03`, in that file's own coordinates; moved by OFF3)

**Role:**
- Routing, developed: send a delivery where he can't go.
- Substitution, twisted.

| Element | Original x | Details |
|---|---|---|
| **The gallery gate** `GalleryGate` | 41.9 | A counterweighted shutter across the gallery lane, on the gallery deck (z 1.6), 1.6 high. Origin at its base: the game lifts it 1.4. A chain runs from its top, over a pulley `GatePulley` in the gallery ceiling, down to the bucket. The return slot (41.3) stays on the near side of the gate. |
| **The bucket** `GateBucket` | 39.0 | A steel hopper hanging beside the ramp's top end, its rim just below the landing (z ≈ 1.2), where carriers arriving on the exit route can tip into it. Origin at its chain hook: the game lowers it about 0.4 as it fills. |
| **The sorting weights** `HeapWeight0`, `HeapWeight1` | 31.6 and 31.85 | Two cast-iron sorting weights on the sorting floor, beside the dock, on the lane. They have the same shape and red bail as DL-03's weight, so the player recognises them. Origin at each base. |
| **The slide** `ReturnSlide` | 38.9 down to 35.7 | A parcel slide (static) from the landing (z 1.6) down to the sorting floor (z 0), along the lane's front edge (y ≈ −0.35) and in front of the ramp, the chute and the pit. A curved lip at the bottom. D-17 rides it down sitting. |
| **The letter** `HeapLetter` | 43.4 | Snagged on the gallery rail at z ≈ 2.3, in a narrow shaft of light (a light-shaft card is fine). Origin at its centre. It falls to the deck when he bumps the rail, which the game does. |
| **`MailSlot6`** | 44.2 | A wall slot on the gallery beside the old sorting desk, red rimmed, with `SlotLamp6`. |

**Clips:** `Slide`, about 24 frames, looping: seated, sliding, claws out for balance.

## 6. DL-08 The Slipping Cage (new) · `art/cage/build_cage.py`

**World x:** 85.6 to 94.6. In local coordinates, u = x − 85.6.
- The returns belt's top end and its turn hatch end at u = 0, on the deck at z 1.6.
- The tunnel (DL-09) begins at u = 9.0, on the deck at z 1.6.

**Role:**
- Latch, twisted under pressure.
- The chapter's set piece.

**Layout:**

| u | z (top) | What |
|---|---|---|
| 0 to 1.2 | 1.6 | Deck beyond the belt end. |
| 1.2 to 1.8 | 2.2 | **Climb 1:** the hatch housing. |
| 1.8 to 2.6 | 2.8 | **Climb 2:** a conveyor gantry. |
| 2.6 to 3.6 | 3.4 | **Climb 3:** the upper landing. |
| 3.6 to 5.2 | starts at 3.4 | **The shaft and the cage.** |
| 5.2 to 9.0 | 1.6 | **The lower landing and antechamber**, on the far side of the shaft. Wall above 3.3, so he can't go across at the upper level. |

All three climbs are mantles of about 0.6.

**The shaft and the cage:**
- **`Cage`:** an open freight cage, 1.5 wide, with a floor, three sides of mesh and an overhead frame. Origin at its floor-top centre; the game moves it in z. It starts with its floor level with the upper landing (z 3.4).
- **`CagePawlLever`:** a red lever inside the cage on its left post, pivot at its base, about 0.6 high. A child of `Cage` is fine.
- **`CageRack`:** a toothed rack on the shaft's back wall, z −0.6 to 3.6.
- **`ShaftBuffers`:** at the pit bottom, z −0.6.
- **`CageCounterweight`:** chains up into the dark, over a sheave `CageSheave` at the top, and down to the counterweight, which the game moves opposite the cage. It hangs in the shaft's back corner.

**The lower landing:**
- **`LandingLamp`:** an amber lamp (emissive) and a painted stripe at the lower landing's edge (z 1.6), so the stop point is unmistakable.
- **Sign:** RESIDENTIAL ACCESS, with ring letters.

**Dressing:**
- Rough, industrial and poor, like the belt and the goods hall.
- The shaft runs on up into darkness (the rings are above).

**Also in `art/dl04`, the DL-07 rework, in that file's own coordinates:**
- **`G4FarRail`:** a steel safety rail across the lane just beyond the shaft, at x 55.6 to 55.75 on the far landing (z 1.6), **0.8 high**. That is too high to climb from the platform, but climbable from the trolley's top (0.44).
- **The buffer stop:** remove it at the pan's far end (or fold it down flat), so the trolley can be pushed off the pan and across the latched platform.

**Clips:** `CageBrace`, about 48 frames, looping: crouched low, claws gripping the cage's side rails, braced against shudders.

## 7. DL-09 Ring C (rework of `art/dl05`, in that file's own coordinates; moved by OFF4)

| Element | x | Details |
|---|---|---|
| **The flood dip** `FloodDip` | 83.4 to 84.9 | The lane floor sinks: dip floor at z −0.25, with standing water `FloodWater` at z −0.1 (dark, still, faintly reflective). Mud, a drowned shoe. |
| **The duct** `PushDuct` | 81.6 to 83.1 | Replaces `D5Duct` at 84.2. A long fallen ventilation duct lying along the lane, 0.26 high and 0.4 deep, with a red strap at its left end (0.44 handle height, so push clips fit). Origin at its base centre. Pushed right, it drops into the dip, where its top sits at about 0.01 and becomes the bridge. |
| **The tideline** `Tideline` | the lane | A dark band at z 1.2 along the lane's back wall and the home facades, with mud staining below it. It runs above D-17's head. Inside C-114 it is at the same height, with the growth marks above it (the marks are already at 0.86 to 1.14; raise them to 1.25 to 1.55 and the tree to 1.2 to 1.7, so they are above the line). |
| **C-108** | 82.2 | A lit window (dim) onto a table set for a meal. |
| **C-110** | 84.26 | Letters jammed in its slot (`D5Letters`). One of them, `C110Letter`, sticks out and can be pulled free; origin at its centre. |
| **C-112** | 86.31 | The taped door gets the water-drop pictogram. |
| **`MailSlot9`** | 87.4 | A red rimmed slot on a post on the lane, with `SlotLamp9`. |

**Clips:** `WaterFlinch`, about 30 frames: he steps toward the water, a spark at his foot, then he jerks back and
shakes it off.

## 8. DL-01 The Wake (rework, `art/dl01`)

| Element | Old | New |
|---|---|---|
| **The trench** | 6.6 to 7.1, depth 0.35 | 6.6 to 8.0, depth **0.8**, too deep to climb out of. A little standing water at the bottom. |
| **The crate** | 5.6 to 6.2, 0.45 high | Becomes **`DepotCart`**: a wheeled parcel cart 1.3 long (x) by 0.5 (y), **0.55 high**, with a red push bar at 0.44 on its left end. Origin at its base centre, at x 5.55 (spanning 4.9 to 6.2). It can still be climbed (0.55). Pushed right, it rolls into the trench, where its top sits at −0.25, and becomes the bridge. |
| **Parcel scale** `ParcelScale` | | At the dispatch counter, x about 2.2, near the start: a floor platform scale with a dial (`ScaleNeedle`, pivot at the dial centre). Its platform top is at 0.05, on the lane. |
| **Dispatch board** | | On the back wall near the start, with D-17's route chalked on it (a texture). |

## 9. Deliverables for each agent

- **Your builder:** `build_set(dl01, m, coll)` and `add_clips(dl01, arm)` in your module, or your edits in the
  named existing builder.
- **Textures:** new textures in your module's `textures/` folder, as 8-bit PNGs where possible.
- **Test in isolation:** build only what you need, not the whole game, for example with a script that calls
  `build_dl01.set_materials()` and your `build_set`. Other agents are editing other builders at the same time, so a
  full build may fail for reasons that aren't yours.
- **Previews:** Cycles CPU renders (there is no GPU) from the game's side-on view at about 35 mm, plus close-ups,
  in your scratch folder.
- **Report:**
  - every object name with its origin and dimensions, and anything that differs from this spec;
  - new material names;
  - clip names, frame counts and key frames;
  - size in KB.
- **Don't** edit `game/`, `build_dl01.main()`, or another agent's files, and don't commit.
