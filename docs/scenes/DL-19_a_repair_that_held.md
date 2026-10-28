# DL-19 A Repair That Held: production plan

**Status:** design only, for director review (task C-01, #6). Nothing here is built.
**Contract:** `docs/chapter2_plan.md` §4 (DL-19 brief and "Fixed across scenes") and §5 (names).
**Sequence:** DL-18 → DL-19 → DL-20, with no cut on either side.
**Lane:** game x 361.0 to 377.0. Heights are metres above the ring A datum.
**Duration target:** 4.0 minutes of first play: the chapter's first principal puzzle, then a 30 s walk along the upper
terrace. Difficulty 3; medium tension (strain, creak, a lurch).

## 1. What the scene must do

| Requirement (chapter plan, §7) | How the scene meets it |
|---|---|
| Restore a sagging landing | The stair up from the terrace landing turns at the half landing, a steel platform cantilevered on a forked bracket and a stop pin. The pin is bent; the platform droops at its free end and creaks. |
| Show what is failing and what will replace it | The bent pin's head is cocked, its lug sits low in the fork, and it creaks. The spare pin waits in a spring clip on the bracket post. The jack stands in a wall bay; worn wheel tracks run from the bay to a polished pocket under the platform. |
| Correct "pull and replace" safely | Pulling the bent pin first lets the platform drop onto its safety stops with a bang. The pin bites and won't move. Nothing breaks, and he can see what the pin was holding. |
| Teach support transfer | The jack takes the load. When the platform is level, the creak stops and the bent pin rattles: it is carrying nothing, and it comes out. |
| Make the swap required, not optional | The raised jack stands on the only spot from which D-17 can mantle onto the half landing. He cannot climb while it holds; he must pin, lower and draw back. |
| Mara's repair, and a hand for whoever came next | Her strap on the bracket, her tag "M. 349", her two witness taps; the spare she clipped. Her repair held; only the pin wore out. |
| Domestic context | Barnaby, Rowan's plant, alive in a pot wired to the bracket's upper strut, on a ticking drip tube. |
| Protect the bracket's silhouette | The forked bracket is modelled once, cleanly, and lit. It is the reference for D-17's knee bracket in DL-43. |

## 2. Beats

| Beat | Time (approx.) | What happens |
|---|---|---|
| **The terrace landing** | 0:00 | He comes along the terrace landing from DL-18. Checkpoint `half_landing` at 362.0. Ahead, the stair's half landing hangs crooked, its guard rail tilted, and creaks. |
| **What's here** | 0:15 | In one pool: the bracket, the bent pin, the spare in its clip, the safety stops beneath, Barnaby above. In a second pool, to the left: the jack in its bay, and the worn tracks from bay to pocket. |
| **Step on it** | 0:30 | Many players mantle the drooping end first. It lurches under him with a bang; `Teeter`, a hop back, then `Settle`: his knee gives a 0.3 s dip and a small servo whine. |
| **Replace me** | 0:50 | The plausible wrong move: Use the bent pin. It slides part-way, and the platform drops onto the safety stops with a bang (`Startle`). Steeper now. The pin bites; more Use only strains. |
| **The jack** | 1:30 | He draws the jack out of its bay and pushes it along the tracks; its wheels drop into the pocket with a clunk and its saddle sits under the cup on the platform's underside. |
| **Crank** | 2:00 | Holding Use at the crank, the ratchet clicks and the platform lifts off the stops. As it levels, the painted marks on bracket and lug meet. The creak stops; the bent pin rattles. |
| **The swap** | 2:30 | He pulls the bent pin out (it drops into the tin cup wired under the fork, clink), takes the spare from its clip and seats it. A clean double click. The `witness` insert. Cue `held`. |
| **Lower and climb** | 3:00 | He winds the jack down: the platform settles onto the new pin with no creak. He draws the jack back out of the pocket and mantles onto the half landing, then up three steps to the upper terrace. |
| **Upper terrace** | 3:30 | Checkpoint `repaired`. A 30 s walk with the shaft open beside him. The lit window is closer; below, the gallery he came along. |
| **On** | 4:00 | The terrace ends at the lower flat's front door at 377.0, where DL-20 begins. |

## 3. Layout (metres along the lane)

```
x: 361.0 terrace landing (1.2)   362.0 half_landing   362.5-363.2 jack bay   363.35-364.05 pocket
   363.6-366.2 HALF LANDING (level top 1.75)   363.65 bracket   366.2-367.4 upper flight (3 steps)
   367.4-377.0 upper terrace (2.3)   371.0 repaired   377.0 lower flat's front door (DL-20)
```

| Thing | x | Height | Notes |
|---|---|---|---|
| Terrace landing | 361.0–366.2 | 1.2 | Rail along its back edge; ends against the stair's closed skirt |
| Jack bay | 362.5–363.2 | 1.2 | Shallow bay in the back wall, off the lane line; the jack is parked here |
| Worn tracks | 362.5–364.05 | floor | Two polished wheel lines from the bay to the pocket |
| Pocket | 363.35–364.05 | floor | Two dished wheel seats, polished; and the saddle cup under the platform at 363.9 |
| Half landing | 363.6–366.2 | top 1.75 level | Hinged to the upper flight's stringer at 366.2. Guard rail along its front from 364.1; open only at its left end |
| Skirt | 364.3–366.2 | 1.2–1.67 | Boarded; closes the space under the platform. The jack fits in under 363.6–364.3 |
| Bracket | post at 363.65 | 1.2–1.65 | Forked, bolted to the back wall; the fork holds the platform's lug. Upper strut from fork head to the wall at 2.3 |
| Bent pin | 363.65 | 1.62 | Through fork and lug, head toward the camera, cocked |
| Spare pin | 363.6 | 1.42 | In a spring clip on the post's left face |
| Safety stops | 363.65 | 1.38 | Two steel blocks on the post below the lug; tops polished by old strikes |
| Tin cup | 363.7 | 1.3 | Wired under the fork; catches a pulled pin |
| Barnaby | 363.5 | pot at 2.0 | Wired to the upper strut, in the bracket's pool |
| Drip tube | 363.3–363.5 | 2.0–2.5 | Teed off the service pipe on the back wall (2.5), through a little float regulator |
| Upper flight | 366.2–367.4 | 1.75–2.3 | Three steps of about 0.18; walkable |
| Upper terrace | 367.4–377.0 | 2.3 | Rail along its back edge, the shaft open beyond; the new cable on the ceiling |

**The half landing's states** (its left end; it pivots at its right end):

| State | Left end top | Above the floor | Stand on it? |
|---|---|---|---|
| Drooping on the bent pin (start) | 1.55 | 0.35 | It lurches 3 cm and springs back: `Teeter`, hop back, `Settle` |
| On the safety stops | 1.45 | 0.25 | It rocks toward the shaft and clangs: `Teeter`, hop back, `Settle` |
| Held by the jack | 1.45 to 1.85 | | Can't be reached: the jack stands on the mantle spot |
| Level (marks meet) | 1.75 ± 0.02 | 0.55 | The bent pin is slack; the spare seats only here |
| Pinned on the spare, jack down | 1.75 | 0.55 | Yes. The solved state; it persists |

- **The mantle spot:** the only open edge is the left end. To mantle he must stand at 363.35–363.6, which is where the
  jack's crank post stands when the jack is in its pocket. The jack is not climbable: no flat surface, the crank wheel
  and ratchet on top.
- **The jack:** a wheeled ratchet jack, chassis 0.7 long and 0.25 tall, crank post 0.65 tall at its back end. Hold Use
  at the crank to wind up (one click per 0.02 m, 0.1 m/s); hold Use while pulling back to wind down. The ratchet holds
  wherever he lets go. Top of travel: left end at 1.85, where the pin binds again and the creak returns. Loaded, the
  jack won't roll: he heaves and it stays.
- **The pins:** Use at the bent pin while it is loaded draws it part-way and it bites. While it is slack (level), Use
  draws it out into the tin cup. Use at the clip takes the spare; Use at the empty fork seats it if the marks meet,
  and otherwise it chatters against the lug and he keeps it. Every pin is always in the fork, the cup, the clip or his
  hands; on a respawn a carried spare returns to its clip.
- **Lowering with no pin:** the platform settles back onto the safety stops. Re-jack in a few seconds.
- **Port notes (U-26, #45):**
  - *Stand points.* With the jack in its pocket the floor ends 0.17 short of its crank post (363.18), and three Uses share
    the 0.6 m before it, each in its own reach so none outranks another: the bracket against the jack (363.08–363.45,
    standing at 363.15; with the jack in its bay the same reach is open floor), the crank behind it (362.85–363.08,
    standing at 362.98), and the jack's push bar behind that (taken from up to 0.6 behind its stand: 362.55–362.85).
  - *The jack is a column.* Out of its bay, the jack's chassis left of the plate is a column in the lane: D-17 can't step,
    mantle or catch it. The motor mantles onto a face up to 0.47 m ahead, so "the mantle spot is the jack's" alone would
    not block the climb; the column does, at any jack height (§10 "Blocked spot").
  - *The skirt is never a step.* A fixed 1.67 top would stand proud of a plate drooping to 1.60 at 364.3; the lane is the
    plate's top over 363.6–366.2 in every state.
  - *The upper flight* is the hinge tread at 1.75 (366.2–366.6), then risers of 0.183 at 366.6, 367.0 and 367.4, walked as
    a ramp.
  - *Step on:* the plate's top is ground in every state; unpinned, he teeters 0.6 s, hops back to 363.38 in 0.45 s and
    settles 0.3 s, then stands at rest (his next jump is unchanged).
  - *Persistence at `half_landing`:* the checkpoint's snapshot is taken again whenever the jack and the pins come to rest
    somewhere new with his hands free, except while he holds the spare (it returns to its clip).
  - *Pin first:* the drop happens during his tug, so `Startle` plays when the tug ends (within 1.5 s of the drop).

## 4. The puzzle

- **Central inference:** another support must take the weight before you remove what is failing.
- **Builds on:** DL-08 (retain a state to free the trolley), the pushed trolleys of chapter 1, and DL-13's crank. New:
  the order of supports.
- **Plausible wrong assumption:** the spare in its clip says "replace me", so he pulls the bent pin.
- **How the world corrects it:** the pin slides part-way; the half landing drops onto its safety stops with a bang and
  a damped shake, steeper now. The pin bites. The failure shows that the platform hangs on that pin, and that the stops
  are there to catch it. Stepping on it first teaches the same: it lurches under him. Both are safe, take under 2 s and
  leave the solution intact.
- **The tell that the jack is right:** the creak. Loaded, the pin creaks in time with the platform's sway. Lifted off
  it, the creak stops and the pin rattles in its hole.
- **Elements (3):** the jack (push, crank), the bent pin (Use to pull), the spare pin (Use to take, Use to seat).
- **Solution:**
  1. Push the jack into its pocket.
  2. Crank. The platform lifts off the stops and levels; the marks meet; the bent pin goes slack and rattles.
  3. Pull the bent pin (into the cup). Take the spare and seat it.
  4. Wind the jack down, draw it back, and climb.
- **Reset:** the jack can be re-raised at any time; no pin can be lost; nothing is ever worse than on the stops.
- **Story link:** this is Mara's old repair. She strapped the bracket, tagged it "M. 349", punched her two witness
  taps, and clipped a spare for whoever came next. Her repair held; only the pin wore out. Rowan's plant is wired to
  the same bracket: their life was right here.
- **Why it holds (principles):** rule 4, the spare's "replace me" taken at its word, before anything else holds the
  load, corrected visibly; rule 5, the lurch and the drop are safe and teach; rule 6, bracket, pin, stops and pocket share
  one pool, the jack's ratchet is visible and the creak links cause to effect; rule 3, three elements.

## 5. New models

- **The terrace landing and the stair:** the landing floor and rail, the half landing (steel plate, lug, guard rail,
  hinge), the skirt, the upper flight and the upper terrace.
- **The bracket:** a forked wall bracket with its post, fork, upper strut, safety stops, Mara's strap and tag, the two
  witness taps, the alignment marks (a painted tick on the fork's cheek and on the lug), the spring clip and the tin
  cup. **Model the silhouette with care** (fork, rounded heel, strut): it is the reference for DL-43's knee bracket.
- **The pins:** bent (a visible kink) and spare (clean, greased).
- **The jack:** chassis, four wheels, ram and saddle, crank post, crank wheel, ratchet pawl. Worn bright on the push
  bar and the crank handle.
- **Barnaby:** a leggy plant in a clay pot, wired on; the drip tube, its float regulator and its tee.
- **The shaft beyond the upper terrace:** far terraces as flat background, the lit window, and the gallery below.

## 6. Lore

| Where | What it says | What it means |
|---|---|---|
| The strap on the bracket | A steel strap clamped round the fork's heel; a tag "M. 349"; two witness taps beside it | Mara mended this, and signed it her way. |
| The spare in its clip | A clean pin, greased, clipped where the next person would reach | She thought of whoever came after her. |
| The bent pin | Worn and kinked; the strap and bracket sound | Her repair held; only the pin wore out. |
| The worn tracks and pocket | Polished lines from the bay to the pocket | This has been jacked before, the same way. |
| Barnaby | A plant on the bracket; tag "BARNABY" and a three-stroke root glyph | Someone with that glyph names plants. We don't yet know who. |
| The drip tube | Teed off the service pipe; ticks once a minute | Someone made sure it would be watered without them. |

**Curiosities:** the drip tube's tick (he tilts his head to it); the pot (Use: a close look in the side view, the tag
legible, 3 s). Neither is needed.

## 7. Camera

| Framing | When | What it holds |
|---|---|---|
| The repair | 361.5 to 366.5 | Lower and a little closer (38 mm): jack bay, tracks, pocket, bracket, the whole half landing and the top of the upper flight, floor to Barnaby. Holds while he thinks. |
| `witness` | The spare seats | A 1.5 s close insert (48 mm), eased in and out: the strap, the tag, the two taps, D-17's head tilting. It shows nothing the side view doesn't. Plays once. |
| Upper terrace | 367.4 to 377.0 | Eases wider and higher (30 mm): the shaft beside him, the lit window closer across it, the gallery below. |

## 8. Music and sound

- **Room tone:** the pin's creak in time with a slow sway; the jack's ratchet clicks as it rises; the drip tube's tick
  once a minute; the relay's click every 7 s along the cable above.
- **Impacts:** the drop onto the stops and the lurch each get a bang and a short damped shake (off in Calm mode).
- **`held`:** as the spare seats, a low warm chord under the music box's three parcel notes, about 6 s, softer than
  DL-08's `latch`. Then sparse again for the walk; the chapter bed returns on the upper terrace.
- **`Settle`:** a small servo whine on the knee dip, quiet, never comic.

## 9. Checkpoints

- **half_landing**: at 362.0 on the terrace landing, before the jack bay. The jack's position and every pin persist.
- **repaired**: at 371.0 on the upper terrace, with the half landing pinned.

## 10. Acceptance checks

- **One frame:** at 720p from `half_landing`, the jack, tracks, pocket, bracket, both pins, the stops and the whole
  half landing are in frame; the alignment ticks are each at least 4 px long.
- **Wrong path, pin first:** a first-time player who Uses the bent pin before jacking sees the platform drop onto the
  stops within 0.5 s and the pin left half out; another Use plays a strain and nothing moves.
- **Wrong path, step on:** mantling onto the platform in any unpinned state plays the lurch or rock, `Teeter` and a
  hop back within 1.5 s, then `Settle`. `Settle` never changes jump distance.
- **The tell:** when the jack brings the marks together, the creak stops and the rattle starts within 0.2 s.
- **Blocked spot:** with the jack in its pocket at any height, D-17 cannot mantle onto the platform or climb the jack.
- **No lost pin:** in every state, every pin is in the fork, the cup, the clip or his hands.
- **Recovery:** from the stops, a player can re-jack to level in under 8 s.
- **Mechanical floor:** about 35 s from `half_landing` to `repaired`, and about 45 s to 377.0.
  *Port (U-26):* the scripted solve takes 28.5 s to `repaired` and 32.2 s to 377.0: the upper terrace's 6 m take about
  4 s at a run, so the 45 s figure holds only for first play's slower walk.
- **First play:** median about 4.0 minutes; at least 80% of first-time players reach `repaired` within 5 minutes of
  `half_landing`, with no hint.

## 11. Grey-box, in Unity

Primitives first; D-17 as in DL-18's grey-box. Pivots at origins; solved states persist; placeholder pools on the
bracket and the jack.

| Object | Rule | Pivot | Position (x, height) | States and transitions |
|---|---|---|---|---|
| `Jack` | Support transfer; Brakes and catches (ratchet hold); Movable access | chassis bottom centre | parked 362.85, 1.2 (bay); crank used from 362.85–363.08, push bar from behind (§3 port notes) | `parked` → pushed/pulled freely → `in_pocket` when its wheels drop into `JackPocket`. In pocket: crank raises/lowers `JackSaddle`; won't roll while loaded |
| `JackSaddle` | part of `Jack` | top of saddle | 363.9 | Height 0 to travel; holds any height (ratchet) |
| `JackPocket` | Support transfer | centre | 363.7, 1.2 | Snap target; blocks the mantle spot while the jack is in it |
| `HalfLanding` | Support transfer | hinge at its right end | 366.2, 1.75 | `drooping` → `on_stops` (bent pin drawn while loaded) → `held` (saddle in contact) → `level` (1.75 ± 0.02) → `pinned` (spare seated and jack lowered). Standable only when `pinned` |
| `Bracket` | Support transfer | post foot | 363.65, 1.2 | Static. Child marks, strap, tag, taps, clip, cup |
| `BentPin` | Brakes and catches | head | 363.65, 1.62 | `seated` → `half_out` (loaded pull) → `out` (slack pull; into cup). Creaks when loaded, rattles when slack |
| `SparePin` | Brakes and catches | centre | 363.6, 1.42 | `in_clip` ⇄ `carried` → `seated` (only when `level`). Respawn: `carried` → `in_clip` |
| `SafetyStops` | Brakes and catches | top | 363.65, 1.38 | Static; catch `HalfLanding` |
| `AlignmentMarks` | readability | | 363.65, 1.62 | Meet when `level` |
| `Barnaby`, `DripTube` | curiosity | pot base | 363.5, 2.0 | Tick every 60 s. Pot: Use from the pinned half landing's left end (363.6–363.9) |
| `CP_half_landing` | checkpoint | floor | 362.0, 1.2 | |
| `CP_repaired` | checkpoint | floor | 371.0, 2.3 | |

**Measure twice:** the mechanical floor with the simulated player, then first play with testers (principle 14).
