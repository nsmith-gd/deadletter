# DL-01 The Wake: production plan

> **Renumbered 18 October 2026.** Chapter 1 then had nine scenes (eleven since pass 3); the next scene is DL-02
> The Sorting Hall. The rework in `docs/chapter1_plan.md` and `docs/chapter1_build_spec.md` supersedes this plan
> where they differ.

**Status:** proposal for director review
**Source:** Dead Letter 45 Scene Overview, scene 01 (16 October 2026)
**Character:** D-17 as built in `art/d17/`. He is 0.71 m to the top of his head and walks on two legs. His claw arms carry things and climb; they are never used to walk.
**Duration target:** 2 minutes, of which no more than 20 seconds is non-interactive.

## 1. What the scene must do

| Requirement (from the overview) | How this plan meets it |
|---|---|
| Reach a release latch from beneath a collapsed sorting shutter, open it, climb over one fallen crate | The layout in section 3 has exactly these three obstacles, in that order |
| Teach move, jump and interact without a tutorial panel | Each verb is forced by geometry the player can read before acting. D-17's own curiosity acts as the hint system (section 6) |
| A current reaches a long-dead charging cradle through a relay with the depot pictogram; its three-lamp pulse lights D-17 | The relay is the scene's light source and its clock. Its pulse also lights the latch, guiding the eye |
| He checks his sealed parcel before his own casing | Authored boot beat: he shields and checks the compartment first, then straightens himself |
| A child silhouette and destination mark establish the job; the power source is unexplained | The parcel label is legible in one close framing. The relay cable runs up into darkness with no payoff until DL-42 |
| Player understanding: dormant machine → courier with an unfinished assignment | Tested directly (section 9) |
| Cinematic beat: parcel lamp first, then the relay pulse reveals the collapse | Opening shot list (section 4) |

## 2. D-17 changes needed for this scene

The current model has no parcel compartment. Scene 1 depends on one, so the model needs these changes before anything else:

1. **Chest compartment.** A hinged hatch about 22 × 11 cm on the front of the pod, with a scuffed window.
   - Inside is the parcel: a wrapped box about 20 × 12 × 10 cm, sized for a six-year-old's boots.
   - The warm glow behind the window is the **parcel lamp**, the first thing the player sees.
2. **Parcel label.** It must read at Switch handheld size inside the close framing.
   - It carries a bold child silhouette and a destination mark (room glyph and number).
   - Proposal: one small stamp beside the mark, so the crooked tree in DL-11 can pay it off. See decision D3.
3. **Three indicator lamps.** The pod's three warm slits already exist. They become D-17's half of a handshake with the relay: when the relay pulses its three lamps, his three answer.
   - This marks him as depot equipment, not a saviour, which is the point of DL-03.
   - It gives DL-42's repeated relay pulse a visible echo on his body.
4. **Eye sensors.** Optional: a faint glint deep inside each eye socket that flickers on at boot (decision D4).
   - Without it, "looking" relies only on head direction, which is weak in a dark room at handheld size.
5. **Knee foreshadow.** The left knee actuator is visibly older: a strap repair and a slightly different finish.
   - It makes one audible click when he first stands. This seeds DL-38 (the knee buckles) and DL-41 (Mara repairs it) without a limp.
6. **Charging cradle.** A wall-mounted cradle shaped to receive his backpack drums, with two contact arms that spark when power arrives.
   - Design it as standard depot equipment; DL-03 shows rows of identical cradles.

## 3. Layout

A single 2.5D plane, read left to right. Distances are in metres at D-17's scale. The playable floor is about 7 m long; the camera frames about 5 m.

```
x:  0        1        2        3        4        5        6        7
    |  dead  | CRADLE |  RELAY on wall (y 1.4), cable rises into dark
    |  end   |  D-17  |        ______ fallen shutter ________
    |  racks |  start |       /  low passage (0.6 m)   |latch|  CRATE (0.45 m)   → DL-03
    |________|________|______/________________________|_____|____[####]______________
                                                       x 3.1
```

- **Dead end (x 0–0.6):** collapsed racks and darkness. Moving left teaches movement without punishing it.
- **Cradle (x 0.6–1.4):** D-17 starts here, facing right.
- **Relay (x 2.0, 1.4 m up):** a box with the depot pictogram and three lamps. Its cable climbs out of frame. It pulses every 6 seconds, at no more than 3 flashes per second.
- **Fallen shutter (x 2.2–3.4):** its bottom bar rests at 0.6 m, so D-17 crouches automatically underneath (the GDD's "low passages resolve contextually").
  - Its lowest slats touch the floor at x 3.4 and close the way.
  - The **release latch** is on the shutter's side rail at x 3.1, 0.35 m up, reachable while crouched.
  - A visible chain runs from the latch to the counterweight drum overhead, so cause and effect is readable before touching anything.
- **Crate (x 4.5–5.1):** 0.45 m tall. That is too high to step (step limit 0.12 m) and well within a jump-and-mantle (decision D1). A few spilled parcels lie nearby.
- **Exit (x 7):** DL-03's floor plate and gate are visible beyond, so the player's next goal is already in view.

**Background layers:**
- parallax rows of dead sorting conveyors
- an empty cradle rack, previewing DL-03
- distant collapsed ceiling

Nothing in the background implies a path the player can't take (GDD rule).

## 4. Beat sheet and shot list

| Time | Beat | Camera | D-17 performance | Sound |
|---|---|---|---|---|
| 0:00–0:05 | Black. The parcel lamp flickers on. | Tight on the compartment window (frame about 1 m wide) | Dormant: slumped in the cradle, head pitched down about 30°, antenna drooped, claws folded over the compartment | Low hum; the lamp's faint tick |
| 0:05–0:09 | Relay clicks; three lamps pulse left to right, twice. The cradle contacts spark. | Slow pull back to about 4 m as each pulse reveals more of the collapse | D-17's three indicator lamps answer the second pulse | Three-tone relay click (the pattern reused in DL-42); spark crackle |
| 0:09–0:15 | Boot | Settles to the gameplay frame (about 5 m) | Antenna twitches; eye glints flicker; the head lifts in small servo steps; the knee clicks; the legs unfold and he rises off the cradle | Servo whirs, rising in pitch; one knee click |
| 0:15–0:18 | Grit falls from the shutter | Holds | Both claws shield the compartment and the head ducks. He looks down, taps the window and checks the seal; the label is legible here. Then a small antenna perk of relief | Grit patter; one soft two-note servo chirp (his "voice") |
| 0:18–0:20 | Straightens himself | Holds | Shakes the dust off his head, a little shimmy. Control passes over with no cut | Rattle of loose panels |
| 0:20–1:00 | Explore; find the latch | Follow camera, slight look-ahead to the right | Contextual crouch-walk under the shutter; reaches toward the latch | Shutter creaks; the relay keeps pulsing |
| about 1:00 | Pull the latch | Small push in on the latch and drum together | Two-claw pull with his whole body leaning back. When the counterweight drops he **flinches** (timid), then peeks up | Chain run-out, counterweight thud, shutter rattling up |
| 1:10–1:40 | Crate | Follow | Jump: crouch for anticipation, spring, claws up. Mantle: the claws hook the edge, the feet scrabble, he pulls up and hops down | Claw scrape; soft landing thump; antenna wobble |
| 1:40–2:00 | Exit toward DL-03 | Look-ahead widens to show the plate and gate | Walks on. Optionally a single glance back at the cradle (not forced) | Depot rhythm starts in the distance |

## 5. Verbs taught and how

| Verb | Forced by | Read before acting |
|---|---|---|
| Move | The only exit is to the right; the left is a short dead end | Light from the relay falls to the right |
| Interact | The shutter blocks the way. The latch is the only lit, reachable object | Red handle, chain to the drum, and the relay pulse catches the latch's reflective tag |
| Jump and mantle | The crate is too high to walk over and clearly scalable | The crate's top edge has a strap handhold; spilled parcels make a low visual step |

Run exists but isn't required here.

## 6. Hints through character, not panels

D-17's curiosity is the hint system:

- After the player has been near an unused interactable for about 6 seconds, D-17 turns his head toward it. This uses the idle look-around, aimed at a point of interest.
- After about 12 seconds he also leans toward it slightly.
- The GDD's optional glyph appears after about 20 seconds, and only when assistance is enabled.

This keeps the screen clean and shows his personality from the first minute.

## 7. Animation list (from the existing rig)

**Already built:**

| Clip | Change needed |
|---|---|
| Idle look-around | Add aim targets so it can serve as the hint system |
| Timid walk | Becomes the **careful walk** at 0.1–0.3 m/s; too slow for normal play (see D1) |
| Run | Retime to the gameplay run speed |

**New clips:**

| Clip | Notes |
|---|---|
| Dormant pose | Slumped in the cradle, claws over the compartment |
| Boot sequence (6 s, authored) | Servo-step head lift, knee click, rise |
| Shield compartment (reflex) | Claws cover, head ducks |
| Check parcel | Look down, tap the window, relief perk (reuses the idle look-down) |
| Shake off dust | Shimmy and settle |
| Gameplay walk | About 0.6 m/s |
| Start, stop and turn | A side-scroller facing flip; he turns through the camera so his face is seen |
| Contextual crouch-walk | Knees bent, head lowered, antenna flattened |
| Reach and two-claw latch pull | Heavy pull with body lean |
| Flinch and peek | Reaction to the shutter release |
| Jump | Anticipation, takeoff, airborne, land |
| Mantle (0.3–0.6 m) | Claw hook, scrabble, pull up, hop down |

**Procedural, in engine:** head aim (look-at), antenna follow-through, foot IK on uneven floor.

Clips are in place (no root motion). The Unity motor moves him and the animation follows.

## 8. Build tasks

**Character, in Blender (I can do all of this here):**

1. Model changes from section 2, plus a parcel prop with its label.
2. The animation clips from section 7, exported to FBX with consistent clip names.
3. A 2D sprite variant of the same clips, with normal maps for 2D lights (see D6).
4. A Blender animatic of beats 0:00–0:20, to lock the opening timing before engine work.

**Grey-box, in Unity:**

1. Kinematic, plane-constrained motor tuned at D-17's scale, with contextual crouch and mantle.
2. Interaction resolver (nearest target in facing direction).
3. Mechanisms with named states:
   - latch: Locked → Pulled
   - shutter: Closed → Releasing → Open
   - relay: a pulse sequencer driving the lights and D-17's lamps
4. Camera volumes, plus the authored opening pull-back.
5. Look-at hint system.
6. Checkpoints:
   - at control handover
   - after the shutter opens (the solved state is saved)
7. Placeholder audio for every cue in section 4, each with a visual equivalent.

**Tests:**

1. A recorded input replay that completes the scene; it runs on every merge.
2. Save, quit and reload at both checkpoints, restoring the shutter state.
3. Frame time on the Switch-profile build.

## 9. Acceptance checks

**Timing and control:**
- Control by 0:20.
- Median completion 1.5–2.5 minutes with unfamiliar players.
- No failure states and no lethal hazards.

**Discovery:**
- 90% or more find and use the latch without the optional glyph.
- 90% or more clear the crate on their first or second try.

**Understanding (asked afterwards, not prompted during play):**
- "What is he?" → a delivery robot.
- "What does he want?" → to deliver the parcel he's carrying.

**Readability:**
- The label, the latch and D-17's head direction read at 720p handheld size.
- The relay pulse doesn't exceed photosensitivity limits, and there's a reduced-flicker setting.

**Recovery:** quit and reload at either checkpoint restores the exact state.

## 10. Decisions for the director

**D1 · Movement scale.** The GDD's starting values (3 m/s run, 1 m jump apex) were written for a larger hero. For a 0.71 m robot they would read as frantic and superhuman. I propose:

| Value | Proposal |
|---|---|
| Careful walk | 0.1–0.3 m/s |
| Walk | 0.6 m/s |
| Run | 1.4–1.6 m/s (about 2 body heights a second, similar to Inside's boy relative to his size) |
| Jump apex | 0.4 m |
| Mantle | up to 0.6 m |
| Step | 0.12 m |

The world is then scaled around him.

**D2 · Parcel compartment.** A front hatch with a window and lamp on the pod, as in section 2. Do his three indicator lamps answer the relay?

**D3 · Tree stamp.** Show a small tree stamp on the parcel label now, so DL-11 pays it off? Or keep the tree entirely for DL-11?

**D4 · Eye glints.** Faint sensor glints inside the eye sockets, or keep them pure dark holes, as in the concept?

**D5 · Knee.** An older left knee with one click at boot, to foreshadow DL-38 and DL-41?

**D6 · DL-01 as the motion and contact proof.** The overview leaves 2D-spline versus stylised-3D open until an in-engine proof. DL-01 tests the hardest presentation problem early: a dark room lit by pulsing light, with contact between claws and latch and between feet and crate. I propose building it twice from the same rig:
- the 3D D-17 in the 2.5D plane
- D-17 sprites with normal maps under 2D lights

Then compare them at handheld size.

**D7 · Running in DL-01.** Allow it from the start, or hold it back until there's somewhere worth running?

## 11. Risks

| Risk | Mitigation |
|---|---|
| The opening runs long | A hard cap of 20 s non-interactive; the boot plays during the camera pull-back rather than after it |
| A dark scene on a handheld screen | The relay pulse is the guide light. Brightness calibration exists (GDD). Test early at 720p |
| The latch isn't found | It's the only lit interactable, the chain makes its function visible, and D-17's look-at hint follows |
| The mantle doesn't read as possible | The handhold strap on the crate edge, a parcel at its foot as a visual step, and a mantle height kept well under the limit |
| Timid performance reads as weak | The timidity is in reactions (flinch, peek, shield). He still acts decisively when the player commits |

## Pass 2 (built 19 October 2026)

`docs/chapter1_pass2_plan.md` adds the chapter's first curiosities here. There are no hazards and no sign of the
White. Positions are game x.

| Curiosity | Where D-17 stands | What happens |
|---|---|---|
| Parcel scale (the first) | 1.27, facing right (the scale at 1.45) | He steps up (`WeighSelf`); the needle swings, he bounces to test it, and a ticket pops up from the dial column. He startles, pinches it up and reads it (POSTAGE DUE), pushes it back, and steps down. |
| Cord lamp | 0.59 | The pull-cord lamp, as before (`Tug`). Tugging it counts as a find. |
| Dispatch board | 1.18, facing left (the board at 1.0) | In a small card rack under the board, his own route card (a house pictogram, C-114). He draws it up, reads it, taps his chest label twice (that's me), and slides it back (`ReadRoute`). |

- **Made obvious:** the scale and the board sit in pools of warm light, with a faint glow behind and a small red
  enamel tag. As he passes each (within 1.8 m), D-17 turns his head to it, until he has used it. The cord lamp gets
  the glance but no pool or tag.
- **The first one teaches the rest:** the scale shows the Use glyph as soon as he is within 0.9 m, without waiting
  for a hint.
- **The scale (art):** its dial column moves to the platform's right end (1.64) so the dial reads past him, and the
  platform drops to 0.028. Stepping on it without Use still swings the needle.
- **A find:** a soft chime, and "◆ n / 12" in the corner for a moment.
- **Checkpoints:** unchanged.
