# DL-22 The Shared Landing: production plan

**Status:** scene design for director review, 26 October 2026 (task C-01, #6). Design only; nothing is built.
**Contract:** `docs/chapter2_plan.md` sections 4 and 5; `docs/full_game_plan.md` §7 DL-22.
**Sequence:** DL-21 → DL-22 → DL-23, with no cut on either side
**Duration target:** 4.0 minutes first play (set piece: a puzzle-led run, difficulty 3); floor about 0:35.

## 1. What the scene must do

| Requirement (plan and §7) | How the scene meets it |
|---|---|
| A service trolley traverses three fire shutters | The service trolley waits at its bay behind the walkway, loaded with the last consignment. The service track runs behind the walkway (z −1.0) through fire shutters 1, 2 and 3, swings into the lane at 415.5, and crosses the gap on a bare rail bridge to the goods lift. |
| One pneumatic selector opens exactly one shutter | The selector at 406.0 takes one air line and has three positions under a plate: three shutters in pictogram, one raised, and the words ONE SHUTTER. Each turn closes the open shutter and opens the next. From the first frame, shutter 3 is up and 1 and 2 are down. |
| An occupied threshold visibly blocks switching; no contradictory rule | Each shutter has a tail-clear marker, a white flag on its frame. It rises with its shutter and drops, with a wooden clack, when the trolley's tail clears. While the open shutter's flag is up, the selector stops against the interlock. Nothing closes, nothing resets. |
| Freight unloads at the lift; the returning trolley is caught at the gap and crossed | The forks lift the trays away, and the trolley comes back as a bare deck. The gap catch takes whatever passes: set it for the return, and the empty deck stops spanning the gap. |
| Recovery: a recall prevents stranding | A missed catch leaves the trolley at shutter 2's buffer. The recall push sends it out and back in 12 s. A drop into the courtyard is safe, and the courtyard stair climbs back at 405. |
| Former ration track, now propagation trays; grade labels become garden allocations | The grade plates on the track parapet are painted over with crops and growers' marks. The trays' end boards are the gallery's old green boards, and the missing walkway over the gap is where they came from. |
| The new cable's first featured use | It drops from the terrace ceiling to the air compressor by the kitchen door and runs on, slung across the gap, to the goods lift's motor. Shared services are kept live with nobody left to share them. |
| The chapter's one wide shot | `courtyard`, about 6 s, as the forks lift the trays. It ends before the empty trolley sets off and shows nothing the side view doesn't. |
| A courier's habit | New quirk `StepAside`: as the trolley passes him he steps back against the front rail to let it by. |
| The secret pays off | If D-17 carries Rowan's card from DL-21, he posts it in the Commons post box at 407.0. |

**Player understanding:** the Commons' last delivery never went. A courier seventy-six years late finishes it.

## 2. Beats

| Beat | Time (approx.) | What happens |
|---|---|---|
| **Out the back door** | 0:00 | From the lower flat's kitchen (DL-21's hatch sill, 5.1) through the back door at 404.0 onto the shared landing. The framing opens and rises: the walkway, the track behind it, the courtyard 3.6 m below, open air coming up. The compressor pants by the door. |
| **The consignment** | 0:10 | The trolley at its bay behind the parapet rail, twelve trays in a cage, Abel's creatures on the tray ends, the tag. The haul chain clanks in the trough and the trolley's grip chatters against the bay stop: it wants to go. |
| **The post box** | 0:25 | If he carries Rowan's card, the post box's slot is lit. He posts it; a stamp thunks inside. |
| **One shutter** | 0:40 | At the selector. Turned once (3 → 1), shutter 3 drops, shutter 1 and its flag rise, the bay stop drops, and the trolley rolls through to shutter 2. Turned again too soon, the drum stops dead against the interlock with flag 1 still up. When the flag clacks down, it turns. |
| **Dispatch** | 1:30 | Selector 2, then 3. The trolley runs out, swings into the lane and passes him (`StepAside`), crosses the rail bridge and strikes the lift buffer. The haul stops. Checkpoint `dispatched`. |
| **The wide shot** | 1:45 | The forks lift the caged trays up the shaft. `courtyard` plays (6 s, `Awe`). |
| **The return** | 2:00 | The forks come down empty. The haul restarts, and a bare deck comes back over the gap, its middle boards worn pale by feet. If the catch isn't set, it passes him and stops at shutter 2's buffer. |
| **The catch** | 2:30 | He sets the gap catch and presses the recall. The deck goes out and back and stops dead over the gap with a clack. It holds, the grip chattering. |
| **Across** | 3:30 | He walks the worn boards over the courtyard to the far landing. Checkpoint `courtyard`. Past the empty lift bay to the upper flat's door at 424.0, the lit window across the shaft. |

## 3. Layout (metres along the lane; walkway 5.1, courtyard floor 1.5)

```
x: 404.0 kitchen back door   404.2-404.9 compressor   404.5-407.1 trolley bay (z -1.0)   405.0 courtyard stair top
   406.0 SELECTOR   407.0 post box   407.2 bay stop   408.0 SHUTTER 1   411.0 SHUTTER 2   414.0 SHUTTER 3
   415.0 parapet ends   415.5 track swings into the lane   416.2 POST: gap catch, recall push
   416.5-418.8 GAP (bare rail bridge; catch jaw at 417.65)   418.8 far landing   419.6 checkpoint `courtyard`
   420.2-422.8 GOODS LIFT bay (buffer 422.8)   424.0 upper flat door (DL-23)
courtyard (1.5): drop lands about 417.6; rota board 407.6; stair foot 409.0, eight 0.45 risers up to 405.0
```

- **Heights** below are above the walkway (5.1) unless marked absolute. The walkway is steel chequer plate with an
  open front rail (0.9), broken only at the gap.
- **The track:** rails are sunk 0.3 in a channel, so the trolley's deck top is level with the walkway. Behind the
  walkway it runs past a parapet rail (0.9, mesh infill): not mantleable, and nothing reaches over it. From 415.5
  it runs in the back half of the lane. D-17 walks the front half, so the trolley never collides with him on the walkway.
- **The gap** (2.3) is beyond D-17's reach. From the prototype's numbers (run 1.6 m/s, jump apex 0.4, so 0.57 s of
  airtime; 0.1 s coyote; feet supported 0.08 past an edge), a running jump lands at most about 1.25 m out, and
  catching the far edge in the air (up to 0.72 above his feet, within 0.32 of his centre) reaches about 1.77 m. The
  old 1.6 m was inside that. 2.3 leaves half a metre spare. The bare rail bridge is a girder with two rails 0.3
  below the walkway, still showing the bolt holes of the boards that were taken up. It is not walkable.

**The trolley's stopping places** (its centre; the trolley is 2.6 long, so its held deck rests 0.15 on each edge):

| Where | Centre | Why it stops |
|---|---|---|
| Bay | 405.8 | Against the bay stop, while the selector isn't at 1 |
| Between 1 and 2 | 409.6 (outward) / 409.4 (homeward) | Against shutter 2 / shutter 1 |
| Between 2 and 3 | 412.6 (outward) / 412.4 (homeward, "shutter 2's buffer") | Against shutter 3 / shutter 2 |
| Over the gap | 417.65 | Held by the catch jaw. Its deck spans 416.35–418.95 |
| Lift bay | 421.5 | Against the lift buffer |

## 4. The puzzle

**Central inference:** finish the outward transfer before reusing what comes back.

**Elements (4, the limit):** the selector; the service trolley; the gap catch; the recall push.

**What drives it.** One motor at the lift drives the **haul**, an endless chain in the track trough at 1.8 m/s.
The trolley's grip takes the outward strand when its deck is loaded and the homeward strand when it is empty. The
deck sits visibly low on its springs under the trays and lifts 4 cm when they go. A closed shutter, the bay stop, the
lift buffer or the catch jaw holds it, and the grip chatters while it is held. While the forks run, the motor
declutches the haul, so the trolley waits at the lift.

**Plausible wrong assumptions, and how the world corrects each:**
- **Switching before the tail clears** (DL-06's "stop, switch, restart", done too fast). He turns the selector
  while the trolley is still in the open shutter. The handle moves 10° and stops with a dull clunk, then springs
  back. The open shutter's flag stays up beside the trolley's moving tail, and the interlock wire, running along
  the parapet from that flag to the drum, twitches. Under 2.5 s later the flag clacks down, and the next turn goes.
  Nothing closes on the trolley, and nothing has to be redone.
- **Setting the catch first** (DL-08 and DL-19: retain the state you want, then act). He sets the catch before
  the loaded trolley reaches it. The trolley stops dead over the gap with its deck spanning it, but its cage of trays
  stands 1.1 high across the walkway's edge: a wall he can't mantle, with Abel's creatures facing him. The grip
  chatters, straining outward, and the lift's call lamp stays lit. He releases the catch and it carries on to the
  lift. The freight has to go before the deck is any use.
- **Jumping the gap.** He falls 3.6 m into the courtyard, lands on the bottle-cap mosaic and looks up at the
  bridge he couldn't cross. The rota board is beside the stair foot. He climbs back in about 20 s.

**Solution:**
1. Turn the selector (3 → 1). The trolley runs through shutter 1 to shutter 2. Wait for flag 1 to drop (2.4 s).
2. Turn to 2 (wait 2.4 s), then to 3. The trolley runs out, passes him at the curve (`StepAside`), crosses the
   bridge and strikes the lift buffer. (Turned the moment each flag drops, it never stops on the way.)
3. The forks lift the trays away (`courtyard` plays) and come down empty: 12 s at the lift in all.
4. While the trolley is at the lift, set the gap catch. The empty trolley comes back and the jaw takes it, deck
   spanning the gap. Walk across.

**Accepted alternatives** (they keep to the rules, so they work):
- **Catch on a recall,** outward or homeward: the same thought, and the likely first-play route.
- **Riding it.** Over the gap, the empty deck is a floor that moves. Riding it out on a recall run gets him across.
  Riding it home just sets him back down at the near edge, and shows him that the deck is a floor. Either way the
  transfer has to be finished first, which keeps the inference.

**Reset:** none needed. A blocked turn costs nothing, a missed catch the 12 s recall, a drop about 20 s by the
stair. With the selector at 1, the empty trolley runs home into its bay.

**Checklist (principles 1–14).** Rule 3 at its limit (four elements). Rule 14 bends slightly: shutters 2 and 3 repeat
shutter 1's thought as execution, so each wait is held under 2.5 s. Rule 6: every link is a visible pipe, wire or rod
in one frame. Rule 12: the wide shot shows nothing the side view doesn't.

## 5. New models

- **The shared landing:** the kitchen block's back wall and door (404.0); the walkway, front rail and parapet rail;
  the terrace ceiling with the new cable on galvanised clips, a relay box (green pilot lamp, 7 s cycle) at 405.2, and
  the cable slung on a catenary wire across the gap to the lift's motor house.
- **The air compressor:** a squat tank and pump on the kitchen wall, with a green pilot lamp and one air line out.
- **The selector:** a drum with a three-spoke handle worn bright, a window showing 1, 2 or 3, and the ONE SHUTTER plate.
  Three air pipes branch from it along the parapet to the shutter rams. The interlock bolt is brass, on the drum's
  face, with three flag wires on pulleys coming into it.
- **Fire shutters 1–3:** steel roller shutters in frames 1.7 high, with rams, sprung bottom edges and treadles.
  Their tail-clear markers are white flag plates (0.35 × 0.25) on hinged arms, each under its own small caged lamp.
- **The service trolley:** a flat deck (2.6 × 1.0) on four wheels, with sprung bumpers at both ends, the grip
  underneath and a centre lug for the jaw. The deck boards are worn pale down the middle by feet. **The last
  consignment:** twelve trays in two stacks of six, in a cage 1.1 high with fork lugs at the top.
- **The bay stop**, a buffer arm on shutter 1's air line, and the haul chain in its trough.
- **The post** (416.2): the gap catch lever, worn bright, and the recall push (a brass mushroom, worn), with the rod
  out along the bridge girder to the jaw. **The rail bridge**, with its old bolt holes.
- **The goods lift:** a bay with a buffer, forks on a carriage, and an open shaft rising out of frame toward a faint
  green glow. A call lamp and a plate showing trays, an up arrow and a leaf.
- **The courtyard** (absolute 1.5): the bottle-cap mosaic (a sun in rings sorted by colour; one ring is mixed where
  the yellow ran out), the kitchen rota board, the courtyard stair in its cage, and the light-well's terraced walls.
- **The far landing**, to the upper flat's door; **the Commons post box** (407.0), red, its slot under a small lamp.

## 6. Lore

| Where | What it says | What it means |
|---|---|---|
| Selector plate | Three shutters, one up; ONE SHUTTER | One air line, one door at a time. The fire rule outlived the fires. |
| Grade plates on the parapet | RATION GRADE 1, 2, 3, painted over: BEANS with Rowan's root glyph; KALE · A. K.; SEED ↑ with Mara's crooked tree | The ration line became garden allocations. Shared services found a future purpose. |
| The consignment tag | 12 TRAYS DRY SEED · P.A. 377 in A. K.'s round capitals; under it, in Mara's hand, "UP. M." | Packed by the last two neighbours and never sent. A. K. died the next year. |
| Tray ends | Abel's creatures: a fish in boots, a snail towing a seed, an owl in a colander | Friends kept turning up. People are wonderful and weird. |
| The trolley's deck | Boards worn pale across the middle | People walked over it here for years. It was their bridge. |
| The bridge girder | Bolt holes where boards were; the trays' end boards are the same green | They took up their own walkway to make seed trays. |
| Rota board (courtyard) | COMMONS KITCHEN: initials by the week. Margins full of jokes, Orme's carets: "^ soup (allegedly). T.O." | They ate together, and teased each other. |
| The mosaic | A sun, sorted by colour, cap by cap | Years of patient, pointless, lovely work, under no sky. |
| The new cable | Glossy, clipped, new: to the compressor and the lift | Someone keeps this live, now, for a community that is gone. |
| The lit window | Across the shaft, warm, closer than ever | Perhaps she is home. |

## 7. Camera

| Framing | When | What it holds |
|---|---|---|
| `landing` | He steps out at 404.0 | Wide and raised (about 32 mm): 403.5–417.0, the courtyard floor along the frame's foot, the shutters' flags at about 95 px/m at 720p. The bay, selector, flags, curve and gap edge all read in one frame. |
| `gap` | D-17 past 413.0 | Blends over 2 s to 411.0–424.0: the post, the jaw, the bridge, the lift bay and the far landing in one frame, with the courtyard below. |
| `courtyard` | The forks begin to lift, the first time only | The chapter's one wide shot, below. |
| `well` | In the courtyard after a drop | Lower and closer (36 mm), the stair and the rota board in frame, the bridge overhead. |
| The far landing | Past 419.6 | Eases up so the lit window sits in the upper right. |

**`courtyard`** (24 to 28 mm, 6 s, `Awe`). Times are from the forks starting to lift, which is also the start of
cue `consignment`. Control returns at 6.0; the trolley sets off at 10.0.

| t | Camera | D-17 | Music and sound |
|---|---|---|---|
| −1.0–0 | Side view. | Wherever he is. | The take-away: the haul declutches with a thunk and the chain falls silent. Only the air from below. |
| 0–2.5 | Eases back and up out over the courtyard, 28 mm, pitched down: the mosaic's sun turns into view below the landing. | `Awe`: he looks up the shaft at the rising cage. | The winch's low hum. A high string harmonic; a horn enters at 1.0. |
| 2.5–3.5 | Tilts up as it rises, widening to 24 mm: the terraces wrap the shaft, the lit window across, the cage rising toward the faint green. Eases to a stop at 3.5. | Holds his parcel. | Strings broaden under the horn. |
| **3.5** | **The widest frame.** | | **The peak:** moderate, about 3 dB over the build. Not a full swell; the chapter's is DL-23's. |
| 3.5–6.0 | Hold. The cage passes out of frame into the green. | | The chord holds, then thins. |
| 6.0–7.5 | Eases back to the side view. Control returns at 6.0. | | Decays under the forks' descent; out by 18 s. |

## 8. Music

| Cue | When | What |
|---|---|---|
| (none) | The puzzle | No bed. Room tone carries it: the haul's clank, the grip's chatter, the compressor's pant after each shutter, the shutters' hiss and thud, the flags' clack, the relay's click every 7 s, and the open air from the courtyard. |
| `consignment` | The forks lift, first time only | As above. About 18 s, built on the chapter theme's first phrase. Restrained wonder: the trays are going somewhere green. The post box has no cue: the slot's flap, then the stamp's thunk inside, as in chapter 1. |

## 9. Checkpoints

- **service**: at 404.8, outside the kitchen door.
- **dispatched**: marker at 414.6, armed when the loaded trolley first strikes the lift buffer (the trays are gone).
- **courtyard**: on the far landing at 419.6, with the trolley held over the gap.

## 10. Acceptance checks

- A first-time player who turns the selector twice in a row sees the handle stop and spring back within 0.3 s, with
  flag 1 up beside the moving trolley. The same input succeeds once the flag drops, at most 2.5 s after the first turn.
- Each wait from a turn to its flag dropping is under 2.5 s (2.4 s for each shutter). Only one
  shutter is ever up, in every state, including the start.
- A player who sets the catch before dispatch sees the loaded trolley stop over the gap within 4 s of turning to 3,
  with a 1.1 m cage at the walkway's edge, and hears the grip chatter. Released, the trolley reaches the lift within 3 s.
- From turning to 3, the empty trolley reaches the jaw after about 19 s, 13 of them under the player's control.
  Walking from the selector to the post takes under 8 s. After a miss, the recall brings it over the jaw in about 8 s.
- `courtyard` never plays before the forks lift, never repeats, and ends 4 s before the trolley sets off.
- A player who drops into the gap is in control on landing (no fade) and back at the post in about 20 s.
- At 720p handheld: the flags are at least 30 px, D-17 at least 60 px tall, and the jaw and the post in one frame.
- Mechanical floor (simulated player, no hesitation): about 0:35. First-play target: median 4:00, range 3:00–5:00.

## 11. Grey-box, in Unity

Primitives first: D-17's capsule as section 4 of the plan; x in game x, heights above the walkway. Pivots as listed;
solved states persist; light pools on the selector handle, the flags, the lift's call lamp, the post and the slot.

| Object (§5 name) | Rule | Pivot | x | Height | States |
|---|---|---|---|---|---|
| the selector | Routes | Drum axle | 406.0 | Axle 0.8; handle grip 0.55 | P1, P2, P3 (start P3); Turning 0.3 s; Blocked (10°, spring back, 0.3 s) |
| interlock | Routes | Bolt on the drum | 406.0 | 0.8 | Locked while the flag of the selected shutter is up; else Free |
| fire shutters 1–3 | Routes | Bottom centre of door, z −1.0 | 408.0 / 411.0 / 414.0 | Opening 1.7 | Down; Rising 0.4 s; Up; Falling 0.5 s (stops on contact) |
| tail-clear markers 1–3 | Routes | Arm hinge, walkway side | 408.1 / 411.1 / 414.1 | Hinge 1.0; flag up at 1.3 | Up from when its shutter opens until the trolley's tail leaves the clear treadle (shutter line + 0.1), and whenever the trolley is over the shutter line; else Down |
| bay stop | Brakes and catches | Hinge | 407.2 | 0.3 | Down iff the selector is at P1 |
| haul | Routes | Trough, z −1.0 to the lift | 404.5–422.8 | −0.3 | Running at 1.8 m/s; Declutched while the forks run |
| service trolley | Routes; Movable access | Deck centre, deck top | Start 405.8 | 0.0 | Held, Running (out or home), AtLift. Grip: Outward if loaded or recall-latched, else Homeward. Deck is a floor where it lies over the gap or far rails (x ≥ 416.5) |
| the last consignment | (load) | Cage base | On the trolley | 0.0–1.1 | OnTrolley, Lifting, Gone. Its cage is a 1.1 wall to D-17 |
| gap catch | Brakes and catches | Lever on the post; jaw on the bridge | Lever 416.2; jaw 417.65 | Lever 0.5; jaw −0.15 | Clear, Set (jaw up), Holding (lug in the jaw; trolley centre 417.65). Use toggles. Worked only from the landing side (x ≤ 416.4) |
| recall push | Routes | Push face | 416.2 | 0.45 | Press: latches the grip outward until the trolley next strikes the lift buffer. Does nothing to a loaded or held trolley |
| goods lift | Routes | Bay floor centre | 421.5 (buffer 422.8) | 0.0 | Idle, ForksIn, Lifting, CageOff, ForksDown. Forks run only for a loaded deck |
| rail bridge / gap | (none) | Girder | 416.5–418.8 | Rails −0.3 | No floor for D-17. A drop lands on the courtyard floor (absolute 1.5) |
| courtyard stair | (traversal) | Foot | 409.0 → top 405.0 | Abs. 1.5 → 5.1 | Eight 0.45 risers |
| post box | (secret) | Slot | 407.0 | 0.55 | Slot lamp lit while he carries a letter; Use: Posted |
| checkpoint markers | — | Marker | `service` 404.8; `dispatched` 414.6; `courtyard` 419.6 | 0.0 | `dispatched` arms on the first loaded buffer strike |

**Sequence with timings** (from the Use; trolley speed 1.8 m/s, 0.3 s ramps):

| Step | t (s) | Selector | Shutters up | Flags up | Trolley |
|---|---|---|---|---|---|
| Start | — | P3 | 3 | none | At the bay against the bay stop, grip chattering |
| Turn to 1 | 0–0.3 | P1 | 1 (3 falls) | 1 | Bay stop drops; runs from 0.3 |
| | 2.4 | P1 | 1 | none | Tail clears 408.1; selector free. Stops at 409.6 |
| Turn to 2 | 0–0.7 | P2 | 2 (1 falls) | 2 | Starts once shutter 2 is up (0.7) |
| | 2.4 | P2 | 2 | none | Tail clears 411.1. Stops at 412.6 |
| Turn to 3 | 2.4 | P3 | 3 | none | Tail clears 414.1 |
| | 5.9 | P3 | 3 | none | Strikes the lift buffer (centre 421.5). Haul declutches; `dispatched` |
| Unload | +1.0–7.0 | | | | Forks lift the cage (`courtyard` 1.0–7.0); the deck rises and the grip goes Homeward |
| | +7.0–11.0 | | | | Cage off at the top; forks descend empty; haul re-engages at 11.0 |
| Return | +11.0–13.3 | | | | Lug reaches the jaw at 417.65: Holding if Set; else on through shutter 3, stopping at 412.4 |
| Recall | 0–8.2 | | | | Out 5.4 s, lift buffer 0.5 s (no forks), back to the jaw 2.3 s; to 412.4 at about 12 s if not caught |
