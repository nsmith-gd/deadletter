# DL-18 Room for One: production plan

**Status:** design only, for director review (task C-01, #6). Nothing here is built.
**Contract:** `docs/chapter2_plan.md` §4 (DL-18 brief and "Fixed across scenes") and §5 (names).
**Sequence:** DL-17 → DL-18 → DL-19, with no cut on either side.
**Lane:** game x 347.0 to 361.0. Heights are metres above the ring A datum (the top of DL-17's stair is 0).
**Duration target:** 3.0 minutes of first play: a 40 s arrival, then a short puzzle. Difficulty 2, low tension.

## 1. What the scene must do

| Requirement (chapter plan) | How the scene meets it |
|---|---|
| Arrive on ring A; the direct way to the Works is shut | The stair comes up into a gallery. At its head the Works door is sealed by a fallen beam and a chain, under the Works pictogram. The new cable comes up the stair ahead of him and turns along the gallery ceiling: the long way round, through the Commons. |
| Hold out the chapter's hope | Across the shaft, high up, one window is lit. The arrival framing holds the sealed door, the gallery and that window together. |
| Teach that two leaves can share one space | Mara's box room has a fold bed and a fold bench on one steel frame. The bench's swing passes through the bed. With the bed down, the bench lands on the quilt and props there, tilted. |
| Correct DL-14's "hold one, move the other" | Nothing forbids having both down; the shared volume does. The player sees the bench stop on the quilt, and finds it won't bear him. |
| Make a cramped life read as hers | One hook, one mug with "M" scratched over a grade number, resoled boots, overalls with a sleeve let down and turned up again, her sketch with her friends' marks on it, and a painted sky. |
| Leave on the terrace landing at 1.2 | The landing door is set high in the room's back wall at its right-hand end. Bench (0.6), then sill (1.2). |

## 2. Beats

| Beat | Time (approx.) | What happens |
|---|---|---|
| **Stair head** | 0:00 | He comes up the last steps of DL-17's stair onto ring A at 347.0. Checkpoint `ring_a`. |
| **The sealed door** | 0:05 | The Works door is in the back wall beside him: a beam fallen across it, a chain through its handles, the pictogram above. Use on the chain: he tugs it twice; it clanks and sheds dust, and nothing gives. |
| **The window** | 0:15 | The framing has widened and lifted: past the gallery rail, across the shaft and high up, one window glows warm. Nothing points at it but the light. |
| **The gallery** | 0:25 | He walks the gallery under maintained lamps, along the new cable and its relay box (green pilot lamp, a click every 7 s). The box room's door stands open at the gallery's end. |
| **Her room** | 0:40 | Inside: dark, close air, the clock ticking. The bed is down, quilt heaped at the foot. The bench is folded on the same frame above it. The landing door is high in the back wall at the far end, 1.2 up, out of reach. Two light pools: the bed's foot rail and the bench's strap. |
| **Try** | 0:55 | Typical first try: climb the bed (0.45) and reach for the sill (0.75 above him). The jump falls short and he lands back on the mattress. |
| **More furniture** | 1:15 | The plausible wrong move: pull the bench down too. It swings onto the heaped quilt with a soft thump and rests tilted, its free edge raised. He mantles onto it and slides back off onto the bed. |
| **Fold** | 1:45 | Use at the foot rail: the bed folds up into its recess. Use at the strap: the bench swings down to its stop at 0.6. With the bench out of the way, a band of painted sky shows on the back wall where the bench was folded, with the crooked tree in it. |
| **Up and out** | 2:15 | Bench (0.6), sill (1.2), through the doorway onto the terrace landing. Checkpoint `terrace` at 355.8. |
| **On** | 2:30 | The terrace landing runs on to the right into DL-19, the shaft open behind its rail. |

## 3. Layout (metres along the lane)

```
x: 347.0 stair head   347.4-348.6 Works door (sealed)   347.6 ring_a   348.6-351.4 gallery
   351.4 box room door   351.6-354.2 box room   351.9-353.8 fold bed   353.4-354.2 fold bench
   354.2-355.0 landing doorway (sill 1.2)   355.0-361.0 terrace landing (1.2)   355.8 terrace
```

| Thing | x | Height | Notes |
|---|---|---|---|
| Gallery floor | 347.0–351.6 | 0.0 | Rail along its back edge; the shaft opens beyond |
| Works door | 347.4–348.6 | 0.0–2.1 | Back wall. Beam fallen diagonally across it, chain through both handles |
| Gallery lamps | 348.0, 350.4 | 2.3 | Maintained: clean glass, new lamp in an old fitting |
| Relay box | 349.4 | 2.2 | On the new cable; green pilot lamp, 7 s click |
| Box room floor | 351.6–354.2 | 0.0 | 2.6 m: one of everything |
| Hook, mug, overalls, boots | 351.8 | hook 1.0 | Boots on the floor beneath |
| Alarm clock | 351.95 | 0.5 | On a bracket at the bed's head; a pipe clamp for its broken leg |
| Common frame | 351.9–354.2 | 0.0–1.5 | Steel, bolted to the back wall, both hinge rails plain to see |
| Fold bed | 351.9–353.8 | top 0.45 | Down at start. Folds toward the wall into its recess (0.0–0.6). Quilt heaped at the foot to 0.7 (its last 0.6). Port: foot moved in from 353.9, see below |
| Foot rail | 353.8 | 0.55 | Worn bright; in a light pool. Use from the floor at 353.6–354.15, standing at 354.0 |
| Fold bench | 353.4–354.2 | seat 0.6 (stop) | Folded up at start: a vertical leaf on the frame, 0.6–1.05. Hinged along its back edge at 0.6 |
| Strap | 353.45 | loop at 0.75 | On the bench's free edge; worn leather; in a light pool. Use from the floor or the bed. The bench is let go at the hop (Tug f43) |
| Painted sky | 353.4–354.2 | 0.62–1.02 | On the back wall behind the folded bench, above the bed's recess |
| Sketch | 353.5–354.0 | 1.1–1.45 | Pinned to the frame's top rail, over the bench |
| Landing doorway | 354.2–355.0 | sill 1.2 | A deep doorway through the back wall's end; its sill lip at 354.2 |
| Terrace landing | 355.0–361.0 | 1.2 | Continues into DL-19 |

**The two leaves (the shared volume):**

| Bed | Bench | Result |
|---|---|---|
| Down | Folded | Start. Bed top 0.45. Sill 0.75 above it: out of reach |
| Down | Pulled | The bench swings down and meets the heaped quilt at about 30° above level, its free edge at about 0.82. It rests there. Mantling onto it slides him back onto the bed |
| Folded | Folded | Bare floor. Sill 1.2 above it |
| Folded | Pulled | The solution. Bench at its stop, seat 0.6, flat. Floor → bench 0.6 → sill 0.6 |
| Pulled down while the bench is down | | The bed swings out until the quilt meets the bench's underside and stops, propped at about 20°. Same lesson, the other way round |

- **Motion:** every leaf moves on one Use and is counterbalanced (coil springs on the frame, visible). Bed 1.4 s each
  way; bench 1.2 s each way. A leaf that meets D-17 stops and waits; nothing crushes. Any order works, and either leaf
  goes back with the same Use.
- **Stepping clear:** Use at the strap is a tug, then a 0.4 m hop back to the left as the bench comes down, so he is
  never under it. Use at the foot rail is taken from beyond the bed's foot, outside its swing.
- **Nothing else to climb:** no hooks or ledges within reach of the sill; the hook by the door (1.0) is too far from it.
- **Port deviations (U-26, #45):** the bed's foot is at 353.8, not 353.9: at 353.9 the gap to the sill's face (354.2)
  was 0.30 m for D-17's 0.34 m body, so at the foot rail he stood inside the bed's swing and it waited for ever. The
  bench is let go as the hop starts (Tug f43), not at the tug's click (f19), where it swung onto him and waited; so he is
  never under it, and it props on the quilt within 1.5 s. The heaped quilt is soft, not a step.
- **Port: the slide-off (#47 review).** A propped leaf is never ground. Whenever D-17's body meets the propped bench's
  swept box while he moves freely (a jump or mantle attempt at it from the bed, a fall, or walking into it along the
  bed), a scene act puts him up on its raised edge (0.25 s), rocks it (0.3 s, cue `dl18.bench.rock`) and slides him back
  onto the bed with a soft bump (0.35 s, cue `dl18.bench.slide`), at rest at 353.18 (the strap within reach), 0.9 s after
  the contact. So with the bench propped, the bed's foot and the floor beyond it are out of reach; the strap folds it.

## 4. The puzzle

- **Central inference:** the bed and the bench share one space. Fold one away to have the other.
- **Builds on:** DL-14's two blinds on one chain (paired outputs) and every pushed or pulled step since DL-01 (movable
  access). New: a shared *space*, not a shared drive.
- **Plausible wrong assumption:** DL-14 taught "hold one, move the other", and every room so far has said "more things
  out, more steps". So he leaves the bed down as his first step and pulls the bench down as his second.
- **How the world corrects it:** the bench swings down and meets the heaped quilt with a soft thump. The quilt bunches
  under it and it rests at a tilt, its free edge raised, half in the light. He mantles onto it; it rocks on the quilt
  and he slides back off onto the mattress with a soft bump (no `Teeter`: nothing has given way, it was never level).
  The correction is in one frame: frame, both leaves, quilt and sill. No sound says "wrong"; the thump and the slide do.
- **Elements (3):** the fold bed (Use at the foot rail), the fold bench (Use at the strap), the landing door (the goal,
  in frame from the room's first framing).
- **Solution:** Use the foot rail (the bed folds up into its recess). Use the strap (the bench comes down to its stop).
  Climb the bench, then the sill.
- **Reset:** none needed. Every state is reachable from every other with at most two Uses; nothing can trap him.
- **Story link:** choosing a useful configuration instead of adding things is how a young adult makes a cramped life
  fit. The bench, put down for the day's work, uncovers the sky she painted above it.
- **Why it holds (principles):** rule 3, three elements, the goal in frame; rule 4, DL-14's true rule applied too
  broadly, corrected visibly; rule 6, both handles lit and worn, the common frame and its springs in plain view; rule
  13, the fold verb's first use is safe (folding the bed is the first thing most players try, and it is right).

## 5. New models

- **Ring A stair head and gallery:** the stair's last flight and its newel; the gallery floor and rail; the shaft beyond.
- **The Works door:** a heavy panelled door, the fallen beam (cracked at one end, its bracket torn), the chain and
  padlock, and the Works pictogram above.
- **Across the shaft:** the far terraces as flat background, mostly dark, and one lit window high up (the upper flat's
  kitchen window, DL-25's keepsake lamp). A quad with a warm card; no point light.
- **The box room:** walls, low ceiling, one bulb fitting with no bulb, the door with its card holder.
- **The common frame:** a steel frame with two hinge rails, coil springs and their brackets, and the bed's recess.
- **The fold bed:** a narrow Commons fold bed (0.55 deep) with its foot rail, thin mattress, pillow, and her patched
  quilt (the same quilt returns in DL-20), modelled heaped at the foot. It needs a heaped and a strapped-flat pose.
- **The fold bench:** a slatted bench leaf with its strap and a fold-down stop on chains.
- **Props:** hook, mug, overalls, boots, alarm clock, the sketch, the painted sky panel.

## 6. Lore

Everything here is read from the world.

| Where | What it says | What it means |
|---|---|---|
| The Works door | Beam, chain, the Works pictogram | The short way is shut. He goes round, as the cable does. |
| The lit window | One warm window, high across the shaft | Someone keeps a light. Perhaps she is home. |
| The door card | A slot card with "M." in her hand | One name on the door. |
| The mug | An institutional mug, its grade number scratched out, "M" scratched in | Issued, then made hers. |
| The boots | Work boots resoled with cut tyre rubber | She mends what she has. |
| The overalls | One sleeve let down, then turned up again | Growing, or making do with someone else's length. Both are hers now. |
| The sketch | Her irrigation sketch of the crooked tree (the knot in one branch). Orme's caret: "^ needs a drain. Unless it's a pond tree." Abel's creature rides a pipe | Her school friends still drew on her work. |
| The painted sky | A band of sky with the crooked tree, on the back wall behind the folded bench | She made a window where there wasn't one. |
| The alarm clock | Wind-up, a pipe clamp for a leg; it rings when touched | Early starts, and a fix that worked. |

**Curiosities:** the alarm clock (Use or bump: it rings 2 s, he `Startle`s, then stills it with a pat); the sketch
(Use: a close look in the side view, 3 s). Neither is needed.

## 7. Camera

| Framing | When | What it holds |
|---|---|---|
| Arrival | 347.0 to 349.5 | Wider and lifted (32 mm): the sealed door left, the gallery ahead, and the lit window high across the shaft, all in one frame for at least 4 s while he walks. |
| Gallery | 349.5 to 351.4 | Normal framing; the window drifts out of the top of frame. |
| Box room | 351.6 to 355.0 | Closer and lower (40 mm): door to landing doorway, floor to frame top, in one frame. The whole puzzle stays in frame while he thinks. |
| Terrace landing | 355.0 onward | Eases wider, with the shaft behind the rail, handing to DL-19. |

No authored shots (the brief allows none). The sky panel is seen in the side view only.

## 8. Music and sound

- **Music:** sparse. The chapter's bed enters low at the stair head, a held open fifth that brightens slightly while
  the lit window is in frame. Nothing in the room but room tone. No cue on the solve: the painted sky is enough.
- **Gallery:** the maintained lamps' faint buzz; the relay box's click every 7 s; the shaft's air below.
- **Room:** close air, the clock's tick (the loudest thing), the bed's springs, the bench's chains, the quilt's thump.
- **Do not** use the two-note chime here; it belongs to the evening routine.

## 9. Checkpoints

- **ring_a**: at 347.6, on the gallery floor at the stair head.
- **terrace**: at 355.8, on the terrace landing past the doorway. Solved leaves persist.

## 10. Acceptance checks

- **Arrival:** at 720p, from `ring_a`, the sealed Works door, the gallery and the lit window are all in frame together
  for at least 4 s of walking, and the lit window is at least 10 px tall.
- **Goal in frame:** on entering the room, the landing door, both leaves, the frame and both light pools are in one
  frame.
- **Wrong path, bench:** a first-time player who pulls the bench with the bed down sees it stop on the quilt, tilted,
  within 1.5 s of the Use; if they mantle onto it, they slide back onto the bed within 1 s. *Port:* the slide-off
  plays on any contact with the propped bench (§3 port notes) and ends 0.9 s after it.
- **Wrong path, reach:** from the bed, a jump at the sill falls short and lands him back on the bed within 1 s.
  *Pending #46:* the port's mid-air catch reaches about 1.09 m above takeoff, so with the bench folded a running jump
  right from the bed (takeoff 353.05–353.85; walking, 353.40–353.85) catches the sill (0.75 up). `Dl18SkipSearchTests`
  asserts this is the only skip and that it exists, until #46 is decided. With the bench propped the slide-off meets him
  first.
- **Reverse case:** with the bench down, pulling the bed down stops it propped against the bench within 1.5 s.
- **No traps:** in every combination of leaf states, and with D-17 at every x in the room, every leaf can be returned
  with one Use and D-17 can reach the gallery and the sill route.
- **No crushing:** a leaf that meets D-17 stops within 0.1 s and resumes when he moves.
- **Readability:** foot rail and strap each sit in their own pool, read as handles at 720p; nothing else in the room
  looks usable except the curiosities.
- **Mechanical floor:** about 25 s from `ring_a` to `terrace` (walk, two Uses, two climbs).
- **First play:** median about 3.0 minutes; at least 90% of first-time players leave the room within 3 minutes of
  entering it, with no hint.

## 11. Grey-box, in Unity

Primitives first. D-17 is a 0.71 × 0.34 capsule with the chapter 1 reach (hook 0.76, mantle 0.24–0.62). Every element
is a named object with its pivot at its origin; solved states persist across checkpoints; light pools are placeholder
spots.

| Object | Rule | Pivot | Position (x, height) | States and transitions |
|---|---|---|---|---|
| `WorksDoor` | dressing | bottom centre | 348.0, 0.0 | Sealed only. Use on its chain plays a tug; no state change |
| `LitWindow` | dressing | centre | far background, high | Lit always |
| `CommonFrame` | Paired outputs (shared space) | bottom left | 351.9, 0.0 | Static; parents both leaves |
| `FoldBed` | Paired outputs (shared space); Movable access | hinge rail, floor, back edge | 351.9–353.8, 0.0 | `down` ⇄ `folded` (1.4 s). While moving down: if its swept volume meets `FoldBench` (down), it stops as `propped` (about 20°); Use returns it to `folded`. Stops and waits if it meets D-17 |
| `FootRail` | use point of `FoldBed` | centre | 353.8, 0.55 | Use from floor at 353.6–354.15 (standing at 354.0, clear of its swing) toggles `FoldBed` |
| `Quilt` | part of `FoldBed` | | heaped at the foot to 0.7 | The collider that the bench meets; strapped flat when the bed is folded |
| `FoldBench` | Paired outputs (shared space); Movable access | hinge rail at 0.6, back edge | 353.4–354.2, 0.6 | `folded` ⇄ `down` (1.2 s). While moving down: if it meets `Quilt`, it stops as `propped` (about 30°; not standable: any landing on it plays the slide-off; port: any contact with it, see §3); Use returns it to `folded`. Stops and waits if it meets D-17 |
| `Strap` | use point of `FoldBench` | loop | 353.45, 0.75 | Use from floor or bed toggles `FoldBench`; plays the tug and 0.4 m hop back. The bench is let go as the hop starts (Tug f43), not at the tug's click (f19) |
| `SkyPanel` | dressing | centre | 353.8, 0.82 | Hidden behind `FoldBench` when folded |
| `LandingDoor` | goal | sill lip | 354.2, 1.2 | Open always; sill is a mantle edge |
| `AlarmClock` | curiosity | base | 351.95, 0.5 | Use or contact: rings 2 s, then idle |
| `Sketch` | curiosity | centre | 353.75, 1.27 | Use: close look in the side view |
| `CP_ring_a` | checkpoint | floor | 347.6, 0.0 | |
| `CP_terrace` | checkpoint | floor | 355.8, 1.2 | |

**Light pools (placeholder):** `FootRail`, `Strap`, the two gallery lamps, the relay box's pilot lamp. The room
otherwise dark; the sky panel unlit but readable by spill from the strap's pool.

**Measure twice:** the mechanical floor with the simulated player, then first play with testers (principle 14).
