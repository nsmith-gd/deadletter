# Puzzle design for 2D and 2.5D puzzle-platformers: a working guide for Dead Letter

**Status:** research brief for the director, 23 October 2026.
**Why:** the director's chapter 1 playtest: "Some things just aren't legible to the human eye. If there are hints I'm
not seeing them. I'm not feeling like we're building upon previous knowledge, and new things aren't introduced well."
**Reads with:** `docs/puzzle_principles.md`, the accepted post-prologue design review, and
`docs/chapter1_expansion_build.md`.

**Method and limits.**
- Every source was fetched and read in full unless marked *secondary*.
- Game Maker's Toolkit (GMTK) videos could not be fetched, so they are cited through a third-party summary.
- I found no designer's account of puzzle design for Inside or Little Nightmares. Inside is represented by Jeppe
  Carlsen, who spent eight years designing puzzles at Playdead.

## 1. Principles

**1. The puzzle is what you can do with the parts, not working out what the parts are.**
- Carlsen: "The challenge shouldn't lie in figuring out what you have, but rather what you can do with what you have."
- He keeps the elements few. With too many, players "force their way through it with trial and error."
- Jensen: "What is really necessary for this puzzle? What can we throw out?"
- Sources: [Escapist, GDC 2011](https://www.escapistmagazine.com/gdc-2011-limbos-puzzle-creator-is-your-enemy/);
  [Hanging in Limbo](https://www.gamedeveloper.com/business/hanging-in-limbo).
- *So for us:* what each object is must read at a glance: heavy, hangable, on a rail, fed by that pipe.

**2. The goal is obvious; the method is not.**
- Carlsen's three-element room: "it takes no time at all for you to realize your goal."
- GMTK (*secondary*): the challenge is "how to get there, not what it is."
- Sources: [Escapist](https://www.escapistmagazine.com/gdc-2011-limbos-puzzle-creator-is-your-enemy/);
  GMTK, [What Makes a Good Puzzle?](https://www.youtube.com/watch?v=zsjC6fa_YBg), via
  [notes](https://notes.hamatti.org/gaming/puzzle-game-design).
- *So for us:* the exit, what blocks it and what releases it (a latch, a chain, a gauge) are in the first framing.

**3. Every wrong attempt says that it failed, that it always will, and why.**
- Carlsen, on Cocoon: "Each wrong attempt at solving a puzzle needs to very clearly give the feedback that the
  solution did not work, that it never will work (with repeated attempts), and why it won't work." He makes that
  feedback as polished as the solution.
- On Limbo, he says the correct solution must be "fairly easy to execute", because players drop a right idea that
  fails and are slow to come back to it.
- Sources: [Remap Radio](https://remapradio.com/articles/a-house-of-cards-built-on-trust-puzzle-design-in-cocoon-2/);
  [GDC Europe 2010](https://www.gamedeveloper.com/game-platforms/gdc-europe-i-limbo-i-s-carlsen-on-making-players-your-worst-enemy-and-your-best-friend).
- *So for us:* a player who toggles until a door opens has met failures that taught them nothing.

**4. Trust comes from consistent rules.**
- Carlsen: a stumped player must already trust "that solutions are always fair and logical."
- Blow tests each rule "with everything in your world."
- Sahlin (Unravel): "If it looks like you should be able to grab and pull an object, you likely can."
- Sources: [Remap Radio](https://remapradio.com/articles/a-house-of-cards-built-on-trust-puzzle-design-in-cocoon-2/);
  [Blow at IndieCade](https://www.gamedeveloper.com/design/indiecade-inside-jonathan-blow-s-puzzle-design-process);
  [Unravel's puzzles](https://www.ea.com/games/unravel/amp/news/unravel-game-puzzles).
- *So for us:* if one heavy thing on a peg holds a blind, any heavy hangable thing does.

**5. Introduce one thing at a time.**
- Portal's first energy-ball room "introduced too many new concepts at once", so Valve put two rooms in front of it.
- "Overwhelmed players tend not to digest new information."
- Teaching rooms have one solution; a glass barrier blocked a clever bypass that would have skipped the lesson.
- Source: [Portal developer commentary](https://theportalwiki.com/wiki/Portal_developer_commentary).
- *So for us:* a room brings in at most one new ingredient or one new use.

**6. Introduce, develop, twist, conclude.**
- Hayashida: learn the mechanic, then "a slightly more complicated scenario", then "something crazy happens that makes
  you think about it in a way you weren't expecting", then mastery.
- McEntee divides teaching into exposition (a safe glimpse), validation (a safe use that blocks the way on) and
  challenge.
- Sources: [Hayashida](https://www.gamedeveloper.com/design/the-secret-to-i-mario-i-level-design);
  [McEntee, Rational Design](https://www.gamedeveloper.com/design/rational-design-the-core-of-i-rayman-origins-i-).
- *So for us:* we skip exposition. Ingredients first appear in the room that needs them.

**7. Signs come before an action, feedback after it.**
- McEntee: signs prepare the player "for the result of their interaction", and "the best feedback is immediate".
- Good signs "will be subconsciously understood."
- Source: [McEntee](https://www.gamedeveloper.com/design/rational-design-the-core-of-i-rayman-origins-i-).
- *So for us:* sag, a strap or a visible pipe is a sign; a clunk, movement or lamp after an action is feedback. A glow
  that names the next step is neither.

**8. Composition and sound direct attention, not markers.**
- Portal lit the box warm, angled shadows at it, and made interactables round against sharp backgrounds.
- Portal cut clutter after a tester "spent half an hour trying to push a shelf onto a button."
- Carlsen moved a bear trap off-screen so players would watch the spider; the trap's fall is heard.
- Sources: [Portal commentary](https://theportalwiki.com/wiki/Portal_developer_commentary);
  [GMTK, Valve's Secret Weapon](https://gmtk.substack.com/p/valves-secret-weapon);
  [GDC Europe 2010](https://www.gamedeveloper.com/game-platforms/gdc-europe-i-limbo-i-s-carlsen-on-making-players-your-worst-enemy-and-your-best-friend).
- *So for us:* use light pools, shape and sound to lead the eye, not glowing outlines.

**9. The aha is something understood, reached by correcting a wrong assumption.**
- Blow: "what interests me is not that rush... but it's the thing that the player understands now."
- He asks what the player thinks on seeing a thing "before they understand what it means".
- GMTK (*secondary*): a good puzzle has a catch, and the obvious approach fails, forcing the player to "rebuild your
  mental model".
- Source: [Bearing Witness](https://www.gamedeveloper.com/business/bearing-i-witness-i-).
- *So for us:* design each puzzle backwards from the assumption the player has to drop.

**10. In a Rube Goldberg machine, every link is visible and every run can be watched.**
- The Incredible Machine gives a goal, a visible incomplete machine, and parts.
- Each run is watched, "getting a little closer each time".
- Source: [Digital Antiquarian](https://www.filfre.net/?p=3440).
- *So for us:* show the whole chain on screen, and let a partial success move the effect part of the way.

**11. Watch first-time players, and cut.**
- Playdead watched "150-ish tissue testers" and asked them nothing.
- About 70% of Limbo's ideas were cut (Jensen, via [Kill Screen](https://www.killscreen.com/must-read-history-limbo/),
  *secondary*).
- Valve playtested Portal every week.
- Sources: [Hanging in Limbo](https://www.gamedeveloper.com/business/hanging-in-limbo);
  [Valve's Secret Weapon](https://gmtk.substack.com/p/valves-secret-weapon).

## 2. Introduce, develop, twist

**Introduce: exposition, then validation.**
- Show the ingredient doing its one thing where nothing depends on it, or in a room with nothing else to try.
- Limbo's first bear traps are two, close together. The player jumps, dies, and learns both that traps kill and that
  he can clear only one. With nothing else on screen, he drags one aside. From a fan analysis:
  [Level Design in Limbo](https://www.gamedeveloper.com/design/level-design-in-limbo).
- Portal teaches box-on-button before portals, and aims the first portal so that players "invariably see themselves".
- Some puzzles in The Witness unlock nothing and only teach
  ([Bearing Witness](https://www.gamedeveloper.com/business/bearing-i-witness-i-)).

**Develop: change one parameter.**
- Limbo's next bear trap acts on an object, not on the boy: it catches a hanging corpse and lightens the rope.
- In Super Mario 3D World's "Cakewalk Flip" stage, the safety net goes, then the flipping platforms become a climb
  ([Kotaku on GMTK](https://kotaku.com/what-made-super-mario-3d-world-so-great-1691916400)).

**Twist: a role the player assumed was fixed.**
- The spider knocks a trap down from a tree, and the trap becomes a weapon.
- Portal forces players through an orange portal because testers assumed orange was exit-only.
- The assumption must be set up first: the player has used the ingredient the "normal" way at least once.

**Conclude, then rest.** Limbo reuses the bear trap a few more times in new contexts, then drops it.

**A fair aha:**
- **The clue is on screen before it's needed,** as a property, not an instruction. DL-14 does this: the jam he is
  shown first is the tool.
- **The failure shows why.** A blind that rises *with* a light gown on it shows that the gown was too light.
- **Revalidate before a hard use.** Portal reintroduces flinging because "player training doesn't always stick".
- **Don't let a near miss look like progress.** Players get attached to approaches that almost work.

## 3. Legibility checklist for physical puzzles

**State.** From the screen alone, the player can tell:
- whether each mechanism is moving, held, latched or free;
- how far it is from its goal: a gauge, a sight glass, a chain's slack, a latch half-lifted.

**Cause and effect.**
- Every control has a visible link to what it moves.
- Where a link is hidden, the effect at the far end shows which control caused it, at the moment it happens.

**Feedback on every action, including useless ones.**
- A dead lever clunks against its stop.
- A load that is too heavy strains and buzzes; one that is too light drifts visibly up.

**An object's nature reads before he touches it.**
- Weight: sag, a two-handed carry, a slow swing, a thud.
- Hangability: a loop or a strap.
- On a rail: a bogie in a channel.
- These signs mean the same thing in every scene.

**Showing what is interactable without glowing the answer.**
- One family of signs (red, a pool of light, round shapes) goes on *everything* usable, the decoys included.
- A sign says "this is a thing", never "this is the thing". If only the solution object is marked, the marker is the
  answer.

**Feedback versus giveaway.**
- Feedback describes what just happened, where it happened: sparks and grinding at the jammed wheel.
- A giveaway names the next step before the player has tried it. DL-14's pole pulsing at its bracket was one; it was
  removed in commit `29e2e4f`, and the sparks were rightly kept.
- Hints wait for a stall (a failure, then idle time), and point at an ingredient, never a destination.

**Text.**
- Labels name controls and constraints ("ONE TANK"), and never do the deduction for the player (the review's F3).
- Anything the player needs is drawn in the world, at a readable size, not only in a record overlay.

## 4. Our scenes

| Ingredient (RGD family) | Introduce | Develop | Twist | Combine |
|---|---|---|---|---|
| Stand-in figure (movable object) | DL-12 weight on a strip | DL-13 key in a seat | DL-14b decoy | DL-15 figures plus him |
| Cycle and brake (controller) | DL-13 | DL-14a night-light | | |
| One drive, two outputs (machinery) | DL-14 pole as a jam | DL-14a garment as a hold | DL-17, not presented as such | |
| Hang on a peg (movable object) | DL-12 coat as a condition | | DL-14a hung thing as a weight | |
| Lift and counterweight | prologue | DL-16 (watched) | DL-16a ballast (illegible) | |
| Water and float (forces) | DL-17, along with three other new things | | | |

**What the table shows.**
- The figure arc is healthy, and it is what the director enjoyed.
- The drive arc is sound, but DL-17 doesn't look like part of it.
- Water arrives without any exposition.
- The school has no hints at all: `HINTS` in `game/undelivered/index.html` has no entries for region 6.

**DL-12 to DL-14.**
- They introduce the stand-in, the cycle and the paired outputs, each with a clean wrong first try.
- They are legible. DL-14's glow gave the answer away; it is already gone.

**DL-14a Lights Out.**
- A good combination: the cycle and paired outputs, with hang-on-a-peg turned into a weight. The aha landed.
- **Illegible:** the object. A "weighted cape" reads as neither a cape nor a weight. Today's commit also carries it
  like a light thing, removing its strongest sign.
- Nothing shows why a light thing on the peg would fail.

**DL-14b Unaccompanied.**
- Introduces the predictable agent, and turns the figure into a decoy.
- Legible: she read the trolley, was caught once, and got past.

**DL-15 One Pupil Missing.**
- The twist (he must be the pupil) is right.
- **Illegible:** the interface. The rule that seats take whoever arrives first is invisible, and pushing a figure "on"
  past Mara's seat has no visible cause.
- The director's ask matches the review's "honest interfaces": her chair should read as a person's place.

**DL-16 After the Bell.** Develops "hold until the transfer is done". Legible.

**DL-16a Her Way Round.**
- **Three unfamiliar things at once:** a gauge in "portions", a bell push *inside* the car, and riding it.
- The only control that matters isn't visible from outside the car.
- Loading gave feedback (lamps), so she stayed in that loop, a near miss that looked like progress.
- Its inference repeats DL-10.

**DL-17 A Different Lesson.**
- **Too much new at once,** in the chapter's last puzzle: water, the float, crossed routing, a one-tank budget and a
  key errand.
- **The deduction is hidden:** the crossing is behind the bench, and the drawing lives in an overlay.
- **Nothing ties a run to its cause.** Seven combinations, and no run's result says which lever did it, so toggling
  was the rational strategy.

## 5. Recommendations (ranked)

Tags: **[family | skill]**, from the RGD list.

**1. Rebuild DL-17 around visible cause, as the drive arc's twist.** [triggers and controllers, physical forces |
observation and causal inference]
- Bring the three feed pipes into the play plane, so the crossing is visible from the levers. Match the lever handles
  to brass bands on the pipes.
- Make water visible running through a clear section of each open pipe, so every run says which lever fed which bed.
- Keep the float, chain, pulley and latch in frame. Make the latch rise in proportion to bed 1's level, so a split run
  lifts it part-way and drops it.
- Let the first open-everything run be the exposition: the sight glass empties into three thirds.
- Pin her drawing above the rig at a readable size, showing the pipes crossing, with no letters.
- Cut the T-key errand.
- Use the same drive-plate pictogram style as DL-14 and DL-14a, so the player recognises "one supply, hold the others".

**2. Cut DL-16a's ballast puzzle and keep Mara's way round as a 40 to 60 second ride.** [moving machinery |
execution]
- Her chalk trees lead to the hatch.
- An outside bell push at child height, with a bell pictogram, calls the car down. The same push inside sends it up.
- If a puzzle is wanted here, it must ask for a new inference. Otherwise merge the space into DL-16's exit, as the
  review allows.

**3. DL-14a: make the weight read, and let failure show why.** [movable objects, barriers and shelters | causal
inference]
- Swap the cape for a recognisable load: a pupil's suitcase on a strap (DL-10's ballast, which the director
  half-guessed), or a bag of wet laundry.
- Give it a heavy carry, a thud, and a bent hook on the chair.
- Start with a child's light gown on W1's hem peg. Winding lifts it with the blind, which shows the peg and shows
  the light thing failing.
- W1 tugs visibly when unloaded.
- Any object at least as heavy works.

**4. DL-15: make the seats honest.** [movable objects, triggers and controllers | spatial reasoning, behavioural
inference]
- Brass docks under R. ABEL's and T. ORME's seats click, and light their lamps on the register.
- Mara's is an ordinary chair with no dock, and the figures roll past it. Her lamp lights only when someone sits.
- A soft pool of light on her chair once both figures are seated marks the goal, not the method.
- This removes the push-past fiddle.

**5. Add school hints that wait.** [all | all]
- Give region 6 hint entries in the prologue's style.
- Trigger one only after a failure plus 20 to 30 seconds without progress.
- Point at the ingredient: the bell push, the float chain, the hem peg.
- Log each hint in telemetry.

**6. Author the wrong attempts.** [all | all]
- Each scene card lists the wrong attempts seen in playtests and the feedback each one gets.
- Known cases:
  - DL-14a: the wall pegs, the light gown.
  - DL-17: opening everything; the lever under bed 1.

**7. Keep as built:**
- DL-12, DL-13 and DL-16.
- DL-14, with its grinding feedback, and without the glow.
- DL-14b. Optionally allow getting past without a capture, so that watching alone is enough.

**8. Test with five first-time players after items 1 to 4.**
- Watch without helping. Record the time to the first correct hypothesis, and the toggles in DL-17.
- If DL-17 is still brute-forced, cut it to two sluices before adding anything.
