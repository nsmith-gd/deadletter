# DL-08 The Handbrake: production plan

**Status:** built as a playable prototype (`game/undelivered/`), for director review
**Source:** Dead Letter 45 Scene Overview, scene 04 (16 October 2026)
**Sequence:** DL-07 → DL-08 → DL-09, with no cut on either side

> **Renumbered 20 October 2026 (pass 3).** Chapter 1 now has eleven scenes; this was DL-07. See *Pass 3* at
> the end.
>
> **Renumbered 18 October 2026.** Chapter 1 then had nine scenes; this was DL-04. The rework in
> `docs/chapter1_plan.md` and `docs/chapter1_build_spec.md` supersedes this plan where they differ.
**Duration target:** 6 to 7 minutes. The overview gives 5; from this scene on, scenes run a touch longer.

## 1. What the scene must do

| Requirement (from the overview) | How the build meets it |
|---|---|
| Use the weighted trolley to raise a goods platform | Goods Lift 2's platform sits at the bottom of its shaft, 2.7 m down. A load pan in the landing floor drives the head drum: load on the pan raises the platform. D-17 alone raises it halfway. The goods trolley, still loaded with iron ballast, raises it all the way, level with both landings. |
| Engage its mechanical safety pawl | Without the pawl, the platform is only balanced: when D-17 steps onto it, it lurches down under him and he scrambles back (`Teeter`). The pawl lever at the shaft edge drops a steel dog into the platform's bracket, but only when the platform is at the landing. Pulled any lower, it clatters on the rack face (`LeverStuck`). |
| Then leave the trolley behind and cross | The trolley stays on the pan, against its buffer stop. D-17 pats it goodbye (`Pat`) and walks across the latched platform. |
| One slow belt crossing adds a brief execution test | Beyond the far landing, the access route runs up the returns belt: a broad conveyor that brings crates of returned post down from the rings to Dead Letters. It carries D-17 back toward the landing, and its crates are obstacles to hop or climb. There is no failure state: at worst he is carried back to the landing. |
| Warn before the moving hazard; checkpoint after the puzzle, before the crossing | The belt is still when he reaches the far landing. Then a bell, an amber beacon and the klaxon start it, and the first crate slides down its chute in full view before he can step on. The checkpoint `latched` is on the far landing. |
| Handmade reinforcement surrounds the original safety catch | The pawl housing is patched with welded plates, extra bolts, a strap clamp and a wired-on spare spring. Six brass repair tags are wired to it, each stamped with a refuge year and initials. Lift 1, beside it, failed: its platform lies broken at the bottom of its shaft. |
| Crossing into the residential access tunnel commits D-17 to a journey beyond his depot | At the tunnel mouth he stops and looks back at the depot (`LookBack`). The depot's three-lamp relay pulse, heard since the first second of DL-01, fades out behind him. |
| Familiar depot → a much larger inhabited system now gone quiet | The tunnel has children's chalk on its floor and walls. It opens onto a balcony over the refuge itself: a city dug into a chasm in the rock. The poorest, most industrial levels are at the bottom, near-dark and abandoned; the levels climb the cliffs, lit more and more toward the upper city in the haze. A larger world lies ahead and above. |
| The latch has a distinct mechanical click | The pawl gets its own sound (a ratchet, then a hard double click), a close-up insert on the dog dropping home, a small shake and `Proud`. |
| Beyond the crossing, lose the depot rhythm and reveal the size of the refuge | The relay pulse and the hum fall away in the tunnel. On the balcony the camera cranes up and out over the atrium, `refuge` swells, and D-17 stands in awe (`Awe`). |

## 2. Beats

| Beat | Time (approx.) | What happens |
|---|---|---|
| **Through the residential door** | 0:00 | He walks out of the DL-06 gallery through the residential access doorway into the goods hall of Lift 2. |
| **The shaft** | 0:20 | The landing ends in an open shaft. If he is left at the edge, he leans over and looks down at the platform (`PeekDown`), and the camera looks down the shaft. Across it, the far landing and the tunnel sign. |
| **The pan** | 0:40 | A hazard-bordered pan in the floor, a dial on the head frame, a sign showing a trolley on the pan and the platform up. Standing on it, the head drum turns and the platform climbs halfway. Stepping off drops it with a crash (`Startle`). |
| **The trolley** | 1:30 | The goods trolley is parked by the door, loaded with ballast. He grabs it and pushes it onto the pan (slow, heavy). The platform comes up out of the dark, the camera low beside it, and arrives level with the landing. The amber `AT LANDING` lamp lights. |
| **Not yet** | 2:15 | Stepping onto the platform: it drops under him and he scrambles back (`Teeter`). The pawl lamp is red. |
| **The click** | 2:40 | The pawl lever. With the platform at the landing, the dog drops home: the click, the close-up, the green lamp, `Proud` and a short music sting (`latch`). |
| **Goodbye** | 3:00 | Passing the trolley, he pats its handle (`Pat`). He walks across the platform to the far landing. |
| **Warning** | 3:20 | Checkpoint. The returns belt starts with the bell, the beacon and the klaxon, and the first crate comes down its chute. |
| **The crossing** | 3:40 | 6.8 m of belt running against him at 0.32 m/s, with a crate about every 3.5 s. Low crates are hopped, tall ones climbed. |
| **The tunnel** | 4:40 | At the tunnel mouth he looks back at the depot (`LookBack`). The relay pulse fades. A chalk hopscotch grid on the floor: he hops it (`Hopscotch`). Chalk suns, houses and stick figures on the wall at a child's height. |
| **The refuge** | 5:30 | The tunnel's back wall opens onto a balcony over the chasm city. He stops at the rail and takes it in (`Awe`, 6.5 s): the camera cranes up and out, and `refuge` swells to its peak. Then he walks on slowly, down the stair to ring C, and into DL-11 with no cut. |

## 3. Layout (metres along the lane; deck height 1.6 m)

```
x: 47.5 door   48.6 goods hall   49.5 trolley   50.5-51.9 PAN   52.45 PAWL   52.8-55.3 SHAFT   57.8 belt end
   64.6 tunnel mouth   66.4-68.2 hopscotch   70.0-74.6 balcony   71.4 awe   74.75 stair down to ring C (DL-11)
```

**Loads on the pan** (a fraction of what brings the platform to the landing):

| On the pan | Load | Platform |
|---|---|---|
| D-17 | 0.5 | Halfway (1.35 m below the landing) |
| The goods trolley | 1.05 | At the landing |
| D-17 standing on the unlatched platform | −0.5 | It drops under him, and he scrambles back |
| Pawl set | | Held at the landing whatever is on the pan |

- **The platform:** it rises at about 0.6 m/s and falls fast.
- **The edge:** the edge of the shaft stops him unless the platform is at the landing.
- **The trolley:** its buffer stop at the end of the pan keeps it off the platform. The pawl is one-way.

## 4. New models (`art/dl04/build_dl04.py`)

- **The goods hall:**
  - The residential doorway, now open in the DL-06 wall.
  - The vestibule, and the hall's walls, beams and lamps.
  - Lift 1's shaft behind, with its wrecked platform and hanging chains.
- **The goods trolley:** a heavier flatbed with a push bar, loaded with ballast pigs strapped under a frame.
- **Lift 2:**
  - The load pan and its border.
  - The head frame, the drum and the pulleys. The game draws the chains.
  - The platform with its yoke and back rail, and the shaft walls and the rack.
  - The pawl, its lever on a stand, the reinforcement and the repair tags.
  - The dial and the two lamps.
- **The returns belt:** the conveyor frame, its rollers and the belt surface (the game scrolls it), the chute from the rings, the turn hatch at the end (lit, with rubber flaps that swing as each crate passes through, so the crates visibly go somewhere), the beacon, and three crate templates that the game clones.
- **The tunnel:** arched ribs, a tiled back wall, lamps, the ring signs, and the chalk floor and wall.
- **The chasm city** (the director's reference: a whole city in a deep chasm, read in layers; not a clean silo):
  - The balcony and the stair, on ring C's lip.
  - **Foreground:** two noise-displaced rock walls with tool-cut terraces. Ring C (the poorest) has container stacks,
    doors cut into the rock, barricades and a few failing red lamps, with steel galleries stacked down toward the mist.
    Ring B is the works: arched halls, galleries, a crane, pipes and a lift tower. Ring A has plaster homes, a few lit.
  - **Mid-ground:** arched viaducts at four heights with piers into the mist, two catwalks, five waterfalls, cables,
    stalactites and low mist.
  - **Background:** the upper city on three rock tiers 150 to 300 m off: lit window grids, towers, domes, chimneys and a
    great domed hall, with skyline cards and a cool haze behind, under a crack of sky in the roof.
  - **Light by level:** no point lights. The chance that a lamp or window is lit grows with height, from 2% in the depths
    and 5% on ring C to 65% in the upper city. A cool haze makes the dark levels read as silhouettes.

## 5. Lore

Everything here is read from the world.

| Where | What it says | What it means |
|---|---|---|
| Lift 2 sign | GOODS LIFT 2: load the pan to raise the platform; SET PAWL BEFORE BOARDING (pictograms) | How the lift worked, and the one rule. |
| Lift 1 plate | LIFT 1 OUT OF SERVICE · R.Y. 97 | It failed, and nobody replaced it. |
| Repair tags on the pawl | R.Y. 58 J.O., 71 T.M., 84 J.O., 96 A.K., 103 M., 107 M. | The catch was kept going by hand for fifty years. The last two tags are the same single initial, ten years after the others stop. |
| Returns belt sign | RETURNS FROM THE RINGS → DEAD LETTERS | The rings' post still comes down by itself, to the pit he has just left. |
| Chalk in the tunnel | Hopscotch 1 to 8, a big sun, houses, stick figures | Children played here, in a tunnel, under a sun they had to draw. |
| The chasm city | Ring letters A, B and C painted metres high; ring C barricaded, dark and failing; light growing level by level up to the upper city; one lit home window on ring A, far across | The bottom of a class system, abandoned first. A larger world above, and perhaps one person left nearby. |

## 6. Camera

| Shot | When | Framing |
|---|---|---|
| `shaft` | He peers over the edge | High, over his shoulder, straight down the shaft (28 mm). |
| `rise` | The platform's first full rise with the trolley | Closer and lower than the hall framing: him and the trolley on the pan to the left, the shaft opening to the right as the platform comes up (30 mm). |
| `pawl` | The dog drops home | A close-up on the patched housing and its repair tags, the dog swinging down into its bracket, him at the lever beside it (48 mm, 1.8 s). |
| The far landing | While the belt starts | The framing widens over the belt, so the whole belt and its first crate read. |
| `lookback` | `LookBack` | From inside the tunnel, low, back past him to the depot (34 mm). |
| `hopscotch` | `Hopscotch` | Up and over him, so the chalk squares read (36 mm). |
| `vista` | `Awe` and the slow walk after | From his shoulder down the chasm over the low viaduct, craning up and back to a high wide view: the cliffs either side, the stacked viaducts, and the upper city rising in the haze (32 mm, then 24 mm). |

The goods hall's own framing is lower and wider than the hall before it, so the shaft's depth and the platform at
its bottom stay in view.

## 7. Music

| Cue | When | What |
|---|---|---|
| `latch` | The pawl drops home | A warm chord under the music box's three parcel notes. About 8 s. |
| `refuge` | He steps out of the tunnel | Awe rather than grief. It starts from near silence (high strings and a long pedal), then phrase B broadens toward F major with violins in octaves and a timpani roll. The cymbal swell peaks on F major at about 11.4 s, as the camera reaches its widest. It lets go into the music box and an open fifth. 40 s, playing on over the end card; then `end`. |

The bed stops in the tunnel, along with the depot's relay pulse: the depot's rhythm is gone. The depot's hum fades as
he crosses the belt, and the refuge's air (a low, slow wind with a long reverb) comes up in the tunnel.

## 8. Checkpoints

- **goods**: at the door of the goods hall.
- **latched**: on the far landing, with the pawl set.
- **tunnel**: inside the tunnel mouth, past the belt.

## 9. Open questions

- **The tags.** Are the repair tags' initials too pointed? The last two, "M.", ten years after the others stop, are a quiet hint at Mara that later scenes can pay off or ignore.
- **The lit window.** The one lit window on ring A seeds chapter 3, "Someone Home". Should it be findable later, or only a feeling here?
- **The chalk tree.** The chalk on the tunnel walls avoids the crooked tree that DL-11 has to establish.
- **The pawl insert.** The click is mostly sound and a small shake. Is the 1.8 s close-up enough, or should the dog be larger, or lit?
- **The belt.** It has no failure state. If playtests find it too gentle, a faster second half or a pair of crates close together would add bite without adding death.

## Pass 2 (built 19 October 2026)

From `docs/chapter1_pass2_plan.md`: the White's first meeting, which teaches that running is loud. Game x is
section 3's x + 21 (`OFF3`).

**The sump** (`Sump7Water`): Lift 2's shaft (section 3's 52.8 to 55.3, game 73.8 to 76.3) is flooded to 1.75 below the
landing (surface −0.15), and the platform rests under the water.
- **First sight:** the first time the platform rises, the White surfaces in the shaft (game 75.05) and sinks again.
- **The scare:** running, or landing from a jump, near the shaft is loud. The White listens, comes, surfaces and
  slaps the water (`WhiteSlap`): a splash, a shake, and D-17 is knocked back off his feet (`Knockback`), unhurt. It
  never leaves the water and can't reach the platform, so this happens while he is over the latched platform or on
  the first 0.3 of the far landing, not on a walkway as the plan had it. It stops listening once he is 3 m past the
  shaft (game 79.3).
- **Walking** (Shift, B, or a half-pushed stick) is quiet. Pushing the trolley is slow enough to be quiet.
- **Falling in** (below −0.2 in the shaft) is a death: he sinks with a splash, then the cut. The shaft's edges
  normally keep him out.

**Checkpoints:** unchanged (`goods`, `latched`, `tunnel`; `tunnel` now also moves on from DL-09's `landing8`).
No curiosities in this scene; the tunnel's hopscotch and the balcony's coin viewer count as DL-09 (see
`DL-09_the_slipping_cage.md`).

## Pass 3 (built 20 October 2026)

From `docs/chapter1_pass3_plan.md`. This was DL-07.

- **Moved:** game x is now section 3's x + 33 (`OFF3`), 12 more than in *Pass 2* above: the goods hall's door at
  80.5, the pan 83.5 to 84.9, the pawl lever 85.45, the shaft (and its sump) 85.8 to 88.3, the belt 90.7 to 97.6. The
  tunnel, the hopscotch and the balcony belong to DL-09 and are placed by `OFF4` (now 42).
- **The White** in the shaft's sump is scaled to fit it and kept wholly inside the water; it turns only while deep.
- **Use without red** (`docs/direction.md`): the trolley's push bar and the pawl lever are worn steel, bright where
  hands went (`HandledSteel`). Section 1's red pawl lever is no longer red.
- **Lore** (`art/pass3/build_lore.py`):

| Where | What it says | What it means |
|---|---|---|
| By the residential door he comes through (79.98), `LoreEveryoneUp` | EVERYONE UP, with an arrow | The last word on the depot's walls before the lift hall. |
| On the far landing (89.35), `LoreStove08` | A stove with a pan, ration tins and a blanket by the broom; soot up the wall | People camped here, by the lift, waiting. |
| Along the belt (92.5), `LoreTimetable`, with chalk tallies beside it (93.12) | RELOCATION · LIFT 1 · UP: every departure struck through in pencil; the last, R.Y. 43, ringed and crossed: LAST | The lift that took people up ran to a timetable, and the timetable ran out. Lift 1 is the one lying broken in its shaft. |

- **Checkpoints:** `goods` at 81.9 and `latched` at 89.2; otherwise unchanged.

## Pass 4 (built 20 October 2026)

From `docs/chapter1_pass4_plan.md`. Positions are game x.

**The fall** (`art/pass4/build_story_shafts.py`, `StoryFallWreck`, `StoryFallWater`). People tried to ride the goods
lift up, and it fell.
- **Where:** Lift 2's flooded sump runs on under the near landing (82.0 to the shaft at 85.8). The landing's slab is
  cut back to a 0.35 m deck on beams, and the pit beneath is seen in section, like the shaft.
- **What lies in it:** a goods-lift car on its side, half under the water: its corner posts buckled, its gate burst
  outward, its snapped rope piled on top with the frayed end standing up. A trunk caught in its mouth, a case burst
  open on it and others floating; a coat over it and two more floating face down; a pram capsized at the back, wheels
  up.
- **Light:** one cold light on the wreck (84.3).
- **Nothing in the shaft moves:** the wreck stops at 85.8, so the platform's travel and the White's water are as
  before. The pit's water is level with the sump's and open to it.

**The White, less sensitive:** beside the shaft's sump D-17 goes carefully whatever the auto-run setting, so he no
longer runs into its slap by default. Shift or B still runs, and running is still loud.

**The way on:** RING C ↓ on the goods hall's back wall at the belt's end (`WayRingC08`, 96.1).

**Checkpoints and hazards:** unchanged.
