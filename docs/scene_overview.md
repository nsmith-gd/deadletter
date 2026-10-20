# Dead Letter 51 Scene Overview

**Status:** Proposed scene sequence for director review  
**Date:** 16 October 2026  
**Basis:** Dead Letter GDD version 0.2 and the current conversation  
**Duration target:** 160 minutes including ordinary discovery and local retries (155 before Chapter 1 grew to eleven scenes on 20 October 2026; 150 before it grew to nine)

## Story and pacing premise

D17 learns to respond to a person rather than perpetuate a procedure. Mara has spent her life helping make a future; her final change is allowing herself to experience it. The two journeys meet when she repairs him, they finish a task together, and she chooses departure. The ending resolves the delivery and their relationship without claiming that grief or mortality has been defeated.

The first half pairs world curiosity with Mara's biography. The second turns that understanding into present-tense suspense and then cooperation. The restoration reveal lands around minute 85; the strongest danger ends around minute 127; the final 32 minutes develop the relationship and allow the tension to settle.

This is a scene overview, ready to develop into the GDD's full production cards after review. Duration, dramatic effect and puzzle comprehension remain design hypotheses to test. The new injury, relay payoff and individual scene solutions below are proposals, not previously approved canon.

| Chapter | Scenes | Minutes | Running time |
|---|---:|---:|---:|
| Undelivered | 1–11 | 25 | 0–25 |
| Attendance | 12–17 | 18 | 25–43 |
| Someone Home | 18–25 | 27 | 43–70 |
| The Work Above | 26–33 | 30 | 70–100 |
| Protective Custody | 34–41 | 28 | 100–128 |
| Recipient Found | 42–46 | 18 | 128–146 |
| First Delivery | 47–51 | 14 | 146–160 |

The allocation is 11 / 6 / 8 / 8 / 8 / 5 / 5 scenes (Chapter 1 revised from 5 to 9 on 18 October 2026, and to 11 on 20 October 2026). It revises the provisional 4 / 6 / 7 / 8 / 8 / 6 / 6 allocation in GDD Appendix A, giving the homes and works more room while tightening the final ascent. The seven chapters are retained; the game is now 51 scenes and about 160 minutes.

| Interaction intensity | Scenes | Total minutes |
|---|---:|---:|
| Developed puzzles | 22 | 92 |
| Short applied challenges | 20 | 51 |
| Quiet interactive discoveries | 9 | 17 |

Every scene requires a meaningful physical action. Quiet scenes use an immediately understandable obstacle so the player has attention left for its consequence. A unique scene is a distinct playable situation and dramatic change; it is not necessarily a separate room, a new mechanic, or a Unity Scene asset.

## The two journeys

D17's journey happens through the player's actions. Mara's earlier journey is reconstructed through environments, then continues in person. The heroic pattern remains implicit: a call beyond familiar life, relationships and trials, an ordeal that changes understanding, mutual help, and a return to ordinary life. Mara's return is to participation in life, not a literal return to her childhood bedroom. Neither needs a destiny, a villain to defeat, or a speech explaining the lesson.

| Movement | Scenes | D17 | Mara |
|---|---|---|---|
| The familiar world and its limits | 1 to 17 | A courier follows an assignment beyond the depot. He discovers that correct procedure can preserve an absence. | A child grows curious about a world she cannot enter. Other people give that curiosity a practical outlet. |
| Commitment and relationship | 18 to 25 | He recognises a life in its belongings and learns when to stop an empty routine. | She becomes a neighbour, technician and partner. Loss changes how she lives, but does not end her participation in the community. |
| Purpose tested at scale | 26 to 33 | His work becomes useful to something beyond the delivery. He understands why the recipient persisted. | Her contribution forms part of a collective restoration effort. Age changes her methods and eventually limits her access. |
| The ordeal and reversal | 34 to 41 | He learns to trust a frightening system, suffers a failure of his own body, and needs protection himself. | She has survived through care that also restricted her. Her continuing bypass work is evidence that her agency never disappeared. |
| The meeting and mutual aid | 42 to 46 | He lets somebody repair him and learns to respond to her actual intention. | She accepts useful help, assesses departure for herself and permits work to remain unfinished. |
| Return to ordinary life | 47 to 51 | He fulfils the task, then chooses company without a new instruction. | She enters the future she helped build and takes part in it as a person, not only as its caretaker. |

## Mechanical learning across the journey

| Relationship | Safe introduction | Development | Emotional reinterpretation |
|---|---|---|---|
| Occupy or substitute | Weight opens gate in 3 | School attendance in 12–15; dinner in 21–23 | Two willing travellers in 48 |
| Hold and latch | Goods-platform brake in 8 | Human repair in 19; retained water in 27–31 | Mara and D17 take turns supporting each other in 44 and 47–48 |
| Read a cycle | Teaching apparatus in 13 | Domestic routine in 21–23; service platforms in 32 | Stop an empty routine in 25; leave safe work unfinished in 46 |
| Route a service | Conveyor track in 6 | Shared carrier in 22; power in 25; water in 26–31 | Reach Mara while preserving care in 39 |
| Predict retrieval | Gentle demonstration in 34 | Evade in 35; choose a powered destination in 37 | Apparent threat protects D17 in 40 |
| Offer and receive | Parcel at a terminal in 11 | Tool exchange in 42; accept repair in 43 | Offer a hand in 47; deliver when Mara is ready in 51 |
| Sit | Satisfy attendance in 15 | Accept repair in 43 | Choose company after work is complete in 51 |

Each developed puzzle introduces at most one unfamiliar relationship. Execution peaks use rules already learned. New geometry, priorities and consequences provide variety; puzzle complexity does not rise in every consecutive scene.

## The 51 scenes

### Chapter 1 Undelivered

Revised 18 October 2026: nine scenes, not five. See `docs/chapter1_plan.md` for the puzzle ladder and the story spine, and `docs/chapter1_build_spec.md` for the build. Revised again 20 October 2026 (pass 3): eleven scenes, with The Ration Hall (5) and Up Only (10) added and the story of the refuge's grades and Mara's family told along the way. See `docs/chapter1_pass3_plan.md`.

**Scenes 1–11 · 25 minutes.** A delivery becomes a search for a child.

#### 01 The Wake

**DL-01 · Applied challenge · 2 minutes**  
**Sequence:** Opening → DL-01 → DL-02  
**Production plan:** `docs/scenes/DL-01_the_wake.md`

**Play:** Reach a release latch from beneath a collapsed sorting shutter, open it, and climb over one fallen crate. These safe actions teach movement, jump and interact without a tutorial panel.

**Learning and connection:** Introduce direct cause and effect. Prepare the player to read a mechanism before touching it.

**Story evidence:** A new current reaches a long-dead charging cradle through a relay bearing the depot pictogram. Its three-lamp pulse briefly illuminates D17. He checks his sealed parcel before his own casing. A child silhouette and destination mark establish the job; the power source is unexplained.

**Player understanding:** Dormant machine → a courier with an unfinished assignment.

**Cinematic beat:** Start with the parcel lamp, then let the relay pulse reveal the surrounding collapse. D17 protects the parcel before he straightens himself.

#### 02 The Sorting Hall

**DL-02 · Applied challenge · 2 minutes**  
**Sequence:** DL-01 → DL-02 → DL-03  
**Production plan:** `docs/scenes/DL-02_the_sorting_hall.md`

**Play:** A sorting table stands too high to climb, and a fallen pigeonhole wall closes the floor. Carry a parcel box to the table's foot and climb box, table and gantry to the lit doorway. A pneumatic tube coughs out one ancient letter; posting it at a red mail slot stamps it RETURN.

**Learning and connection:** Introduce carrying, and the chapter's optional letters, on the path and without risk. Carrying returns in scenes 3, 4, 7 and 10.

**Story evidence:** Named mugs, a courier-of-the-year board fading to a silhouette, and a notice with a water-drop pictogram: ring C deliveries suspended, R.Y. 42. The first sign of the flood.

**Player understanding:** A dead depot → a workplace that stopped mid-shift, for a reason.

**Cinematic beat:** None. The lit gantry doorway is the frame's brightest point from the moment he enters.

#### 03 The Weight of the Job

**DL-03 · Developed puzzle · 2 minutes**  
**Sequence:** DL-02 → DL-03 → DL-04  
**Production plan:** `docs/scenes/DL-03_the_weight_of_the_job.md`

**Play:** Stand on a floor plate to open a gate, discover that leaving closes it, then carry a sorting weight onto a trolley and park it on the plate. Both the plate and gate stay in view.

**Learning and connection:** Introduce substitution: an object can hold a state after the player moves away. Reused in scenes 4, 5 and 10, and later in 13, 15 and 44.

**Story evidence:** Rows of failed couriers occupy recharge racks beyond the gate. D17 is ordinary equipment that happened to wake, not a purpose-built saviour. His careful handling of a mundane weight establishes his working temperament.

**Player understanding:** Possibly exceptional survivor → ordinary equipment in an extraordinary situation.

**Cinematic beat:** Keep plate and gate together in frame. Widen only after the solution to reveal the other couriers in their racks.

#### 04 The Racks

**DL-04 · Developed puzzle · 2 minutes**  
**Sequence:** DL-03 → DL-04 → DL-05  
**Production plan:** `docs/scenes/DL-04_the_racks.md`

**Play:** The racks end at a charging bay door whose plate carries a courier pictogram. Standing on it opens the door; stepping off closes it, as in scene 3, and the trolley can't follow him past the gate. D-17 drags a fallen courier onto the plate. The cradle lifts it, its lamps flicker weakly and hold, and the door opens.

**Learning and connection:** Develop and twist substitution: the bay wants a courier, not a weight. Carrying becomes care.

**Story evidence:** D-17 is one of many. He leaves another courier on charge, a success that leaves something behind.

**Player understanding:** A solved mechanism → a choice with feeling in it.

**Cinematic beat:** The realisation among the couriers stays this stretch's only shot; the flicker plays in the side view.

#### 05 The Ration Hall

**DL-05 · Developed puzzle · 2.5 minutes**  
**Sequence:** DL-04 → DL-05 → DL-06  
**Production plan:** `docs/scenes/DL-05_the_ration_hall.md`

**Play:** The way on is through a serving hatch whose steel shutter is wound up by a winch on the counter and drops the moment the winch is let go. Wind it and go, and it slams. Push a ration drum under the shutter's line, wind, and let go: the shutter slams onto the drum and leaves a gap to crawl under.

**Learning and connection:** Twist the hold: a state the player can't keep is kept by an object. Develops substitution from scenes 3 and 4, before routing in scene 6.

**Story evidence:** The depot workers' canteen, where families slept when ring C flooded: queue barriers folded into a maze, a ration board of chalked halvings, cots between the tables, a RELOCATION BY GRADE notice with Grade 4 suspended, a shrine of names and candles. A child's crayon drawing of a little courier carrying a parcel to a house, signed M: D-17 and Mara, before either is named.

**Player understanding:** A depot that stopped work → a community left at the bottom.

**Cinematic beat:** None. The winch, the drum and the hatch share one frame under a failing strip light; the drawing is taped beside the winch.

#### 06 Return to Sender

**DL-06 · Applied challenge · 2 minutes**  
**Sequence:** DL-05 → DL-06 → DL-07  
**Production plan:** `docs/scenes/DL-06_return_to_sender.md`

**Play:** A sorting scanner rejects the obsolete address and directs its carrier toward a storage chute. Stop the belt and switch the track to a manual service exit before boarding it.

**Learning and connection:** Apply observation and introduce route selection. The same readable switches later route domestic carriers and service power.

**Story evidence:** A visible pile of permanently undeliverable parcels explains the automated response. D17 proceeds because his delivery is unfinished; his persistence begins as professional stubbornness. The parcel stays secured in his chest throughout.

**Player understanding:** An invalid address ends the task → the task still deserves a physical search.

**Cinematic beat:** Let the rejected parcels appear before the chute starts. D17 checks the label again, then moves with renewed purpose.

#### 07 The Heap

**DL-07 · Developed puzzle · 2 minutes**  
**Sequence:** DL-06 → DL-07 → DL-08  
**Production plan:** `docs/scenes/DL-07_the_heap.md`

**Play:** The ride up the ramp now ends at a gallery gate held shut by a counterweight bucket. Load a sorting weight into an empty carrier at the dock, route it up the ramp and watch it tip into the bucket; the gate rises. Ride the next carrier up. A parcel slide returns him to the floor if he goes up too soon. A letter caught on the gallery rail is the chapter's secret.

**Learning and connection:** Develop routing and twist substitution: the system delivers the weight for him. Combines carrying, routing and substitution.

**Story evidence:** The day board and the stopped clock above the heap of returns.

**Player understanding:** Machines that refused him → machines he can direct.

**Cinematic beat:** None. The bucket, chain and gate are in one side-on frame.

#### 08 The Handbrake

**DL-08 · Developed puzzle · 3 minutes**  
**Sequence:** DL-07 → DL-08 → DL-09  
**Production plan:** `docs/scenes/DL-08_the_handbrake.md`

**Play:** Use the weighted trolley to raise a goods platform, engage its mechanical safety pawl, then leave the trolley behind and cross. One slow belt crossing adds a brief execution test after the reasoning.

**Learning and connection:** Combine substitution with a latched state. Warn before the moving hazard; checkpoint after the puzzle, before the crossing.

**Story evidence:** Handmade reinforcement surrounds the original safety catch. People repeatedly repaired this place before it failed. Crossing into the residential access tunnel commits D17 to a journey beyond his familiar depot.

**Player understanding:** Familiar depot → a much larger inhabited system now gone quiet.

**Cinematic beat:** The latch has a distinct mechanical click. Beyond the crossing, lose the familiar depot rhythm and reveal the size of the refuge.

#### 09 The Slipping Cage

**DL-09 · Applied challenge (set piece) · 2 minutes**  
**Sequence:** DL-08 → DL-09 → DL-10  
**Production plan:** `docs/scenes/DL-09_the_slipping_cage.md`

**Play:** Beyond the returns belt, climb to an old freight cage and ride it down toward the residential tunnel. Its brake gives: it shudders, then slips. Throw the cage's pawl as it passes the lit landing. Too early or late, it rattles down to the buffers and the counterweight hauls it back up to try again. Then the tunnel, the look back, the hopscotch, and the city reveal.

**Learning and connection:** Twist the latch under time pressure. The chapter's set piece, with a checkpoint on the cage floor.

**Story evidence:** A cargo lift full of furniture climbing toward the lit upper city, and never coming back: moving up was the promise.

**Player understanding:** A depot and its routines → a city that left its lowest levels behind.

**Cinematic beat:** The city reveal is the chapter's one wide shot, and it hands back to D-17.

#### 10 Up Only

**DL-10 · Developed puzzle · 2.5 minutes**  
**Sequence:** DL-09 → DL-10 → DL-11  
**Production plan:** `docs/scenes/DL-10_up_only.md`

**Play:** Ring C is below; the relocation lift only goes up, and won't go empty, and the stair beside it has collapsed. Carry the suitcase tagged C-114 into the car, whose floor weighs passengers. Wind open the service door to the counterweight's shaft, stand on the counterweight and press its UP: the car goes up with the suitcase, and D-17 rides the counterweight down.

**Learning and connection:** Twist substitution: an object stands in for a passenger, and D-17 takes the counterweight's place. Applies carrying, and the counterweight from scene 9.

**Story evidence:** The lobby the lower grades left from: a painted queue line with a shoe, a doll and a birdcage dropped along it, the left luggage, RELOCATION — GRADES 1–2 ONLY with EVERYONE painted across it. The C-114 suitcase goes up without him, the way its family did.

**Player understanding:** A city that left its lowest levels → the moment they left, and who went.

**Cinematic beat:** On the ride down he looks up at the car leaving with the suitcase, then down at ring C.

#### 11 The Child at the Address

**DL-11 · Quiet interaction · 3 minutes**  
**Sequence:** DL-10 → DL-11 → DL-12  
**Production plan:** `docs/scenes/DL-11_the_child_at_the_address.md`

**Play:** Slide a fallen low desk clear of a forwarding terminal. Moving it exposes the growth marks and tree carving behind it; presenting the parcel retrieves the school destination.

**Learning and connection:** A familiar manipulation reveals evidence. The first forwarding stop supplies a person and a question, not just another waypoint.

**Story evidence:** A patched toy, imagined sunlight and the parent-and-child photograph make the addressee concrete. Establish Mara's distinctive crooked tree with a knot in one branch. D17 straightens the toy, then leaves the bedroom undisturbed.

**Player understanding:** Abstract addressee → a particular child with a home and a parent.

**Cinematic beat:** Move slightly closer as the desk shifts. The growth marks occupy the new empty space; the toy adjustment is brief and interruptible.

### Chapter 2 Attendance

**Scenes 12–17 · 18 minutes.** Empty routines reveal the child who questioned them.

#### 12 Coats Without Children

**DL-12 · Applied challenge · 2 minutes**  
**Sequence:** DL-11 → DL-12 → DL-13

**Play:** Roll a clearly jointed teaching figure across an occupancy strip. Its light changes and the cloakroom gate opens. Park the figure there and pass into the school.

**Learning and connection:** Reframe scene 3: a machine interprets occupancy as attendance. No new player command is needed.

**Story evidence:** Hundreds of coat hooks are mostly empty. Several carry the same few garments repeatedly repaired. The school was designed for a community that had already begun to shrink.

**Player understanding:** Merely empty school → an institution built for more children than remained.

**Cinematic beat:** Follow the occupancy light, then show its tiny working pool beneath a disproportionate number of unused hooks.

#### 13 The Repeated Lesson

**DL-13 · Developed puzzle · 4 minutes**  
**Sequence:** DL-12 → DL-13 → DL-14

**Play:** Use a teaching figure to start a demonstration cycle. Observe its folding boards, stop the apparatus at the raised position, and latch one board into a climbing route.

**Learning and connection:** Introduce readable cycles in safety; combine occupancy from scene 12 and the latch from scene 8.

**Story evidence:** The lesson endlessly assembles a perfect model tree while a neglected real seedling tray sits behind glass. The institution retained the demonstration after losing anyone who might learn from it.

**Player understanding:** Apparently useful lesson → routine detached from learning.

**Cinematic beat:** Use the same precise lesson rhythm three times. Frame the neglected seedling tray at its edge without an explanatory cutaway.

#### 14 The Window

**DL-14 · Applied challenge · 2 minutes**  
**Sequence:** DL-13 → DL-14 → DL-15

**Play:** Lower a classroom blind to extend its cleaning ledge, then use the ledge to reach the next opening. A small demonstration shows both motions before the player commits.

**Learning and connection:** Apply the cycle rule to a paired output. Prepare shutters and folding furniture in the homes.

**Story evidence:** The apparent outdoor window is a faded landscape panel backed by concrete. Behind its edge are Mara's drawings of an imperfect, crooked tree. Her interest exceeded the tidy version she was taught.

**Player understanding:** A window onto the world → an inherited image that the child questioned.

**Cinematic beat:** The blind lowers across a convincing painted sky, then exposes its concrete backing. Hold the discovery within player control.

#### 15 One Pupil Missing

**DL-15 · Developed puzzle · 5 minutes**  
**Sequence:** DL-14 → DL-15 → DL-16

**Play:** Position two teaching figures at two occupied-seat sensors, then sit in the third place. Three visible lamps trigger dismissal; the cycle remains latched long enough for an unhurried exit.

**Learning and connection:** Combine counting, substitution and cycles. Establish sitting through play for scenes 43 and 51.

**Story evidence:** The final desk carries Mara's crooked-tree carving. D17 occupies the place of the child he is following. When the figures retract, he is briefly left alone in the classroom.

**Player understanding:** Observation of an absent pupil → briefly occupying her place.

**Cinematic beat:** Frame D17 at child-desk height. Mechanical dismissal empties the composition around him; allow a beat before the exit draws attention.

#### 16 After the Bell

**DL-16 · Applied challenge · 3 minutes**  
**Sequence:** DL-15 → DL-16 → DL-17

**Play:** Guide the dismissed figures onto their return rail, lower a crossing section and hold its gate until the last figure clears. Their departure leaves a service passage accessible.

**Learning and connection:** Apply scene 6 routing to moving occupants. Teach waiting for a full transfer before changing a mechanism.

**Story evidence:** The procession feeds into a storage rack instead of a playground. D17 initially gives way as though they were pupils, then notices their destination. His small courtesy is funny before the empty routine becomes sad.

**Player understanding:** Normal dismissal → a closed loop with nobody to go home.

**Cinematic beat:** A polite hand gesture precedes his discovery of the storage rack. Let the wheels keep ticking after the figures disappear.

#### 17 A Different Lesson

**DL-17 · Quiet interaction · 2 minutes**  
**Sequence:** DL-16 → DL-17 → DL-18

**Play:** Move a jammed seedling tray to open the school's workshop drawer and recover the apprenticeship destination. Its mechanism is simple; the discovery supplies the scene's weight.

**Learning and connection:** Recognition links a personal motif to a function. Set up the transition from classroom rules to human repairs.

**Story evidence:** Several pupils' growing experiments surround a volunteer maintenance bench. Mara's crooked tree becomes a rough irrigation drawing beside a repaired pot. People inside the institution also helped her curiosity find practical use.

**Player understanding:** A child who imagined trees → a learner finding practical support.

**Cinematic beat:** The drawer movement brings the rough drawing beside the repaired pot. Include other pupils' attempts so the room belongs to a community.

### Chapter 3 Someone Home

**Scenes 18–25 · 27 minutes.** A life acquires work, companionship and loss.

#### 18 Room for One

**DL-18 · Applied challenge · 3 minutes**  
**Sequence:** DL-17 → DL-18 → DL-19

**Play:** Fold the bed into its wall recess so a workbench can extend, then use the bench to reach a shared landing. The two occupy the same space, making the relationship obvious.

**Learning and connection:** Develop the paired outputs of scene 14. Introduce domestic space being reconfigured by routine.

**Story evidence:** An apprentice's work coat has replaced the child's coat. The patched toy and tree ornament survived the move. Mara became someone with skills, cramped living conditions and an ordinary working life.

**Player understanding:** A remembered child → an adult organising a working life.

**Cinematic beat:** Let the bed and workbench share the same framing, showing how little space this adult life occupied.

#### 19 A Repair That Held

**DL-19 · Developed puzzle · 5 minutes**  
**Sequence:** DL-18 → DL-19 → DL-20

**Play:** Roll a maintenance jack beneath a sagging landing, raise it, then seat a safety pin in an old handmade bracket. The jack can now be lowered without the landing falling.

**Learning and connection:** Deepen scene 8: transfer a load safely between supports. The bracket shape becomes familiar before Mara uses it in scene 44.

**Story evidence:** The bracket bears Mara's crooked-tree mark; its handhold is polished by years of neighbours passing. This was a modest repair that helped many people, not a grand invention made for the player.

**Player understanding:** Anonymous technician → a neighbour whose small repair served others.

**Cinematic beat:** Show the handmade bracket before the jack takes the load. Its polished grip and several different repairs remain visible after success.

#### 20 Two Hooks

**DL-20 · Quiet interaction · 1.5 minutes**  
**Sequence:** DL-19 → DL-20 → DL-21

**Play:** Pull a narrow sleeping platform clear of the shelf obstructing it. Its second section unfolds, providing a step to the next room.

**Learning and connection:** A quick use of scene 18 changes its emotional meaning. Let the player notice without an immediate threat.

**Story evidence:** The single bed has become a double. Two coats hang above mismatched mugs; the photograph now includes another adult. The familiar tree ornament sits beside somebody else's handmade object. Mara's life widened beyond work.

**Player understanding:** An individual life → a shared home.

**Cinematic beat:** The second bed section quietly changes the room's proportions. Give the paired belongings time to register without a score cue.

#### 21 The Evening Cycle

**DL-21 · Developed puzzle · 5 minutes**  
**Sequence:** DL-20 → DL-21 → DL-22

**Play:** Set two stools on the dining sensors, start the evening routine, then latch the raised table before it folds away. The table and lowered shutters form a route through a serving hatch.

**Learning and connection:** Combine occupancy, paired outputs and latching. Establish the normal two-place routine before scene 23 changes its significance.

**Story evidence:** The home once accommodated two people's differing routines: two workstations, shared repairs, practical compromises. The automated arm lays empty bowls; it does not conjure fresh meals decades after abandonment.

**Player understanding:** An abstract relationship → two people accommodating each other every day.

**Cinematic beat:** Use matching motions for two bowls and two work areas. Establish a rhythm the player can recognise when it is repeated later.

#### 22 The Shared Landing

**DL-22 · Applied challenge · 3 minutes**  
**Sequence:** DL-21 → DL-22 → DL-23

**Play:** Open service shutters in sequence to guide a shared trolley onto a balcony lift, then use its empty return tray as a crossing. The route stays visible across the courtyard.

**Learning and connection:** Combine routing from scenes 6 and 16 with the household cycles. Broaden the story from one couple to a community.

**Story evidence:** Apartments have been converted into a communal workshop and food station. Repairs carry different signatures, including Mara's. Scarcity produced cooperation as well as deterioration; the bunker was never only a cruel machine.

**Player understanding:** Private perseverance → a community adapting together.

**Cinematic beat:** Pull wide across the shared landing while the trolley moves. Keep the communal repair bench and several makers' marks in view.

#### 23 The Second Place

**DL-23 · Developed puzzle · 5 minutes**  
**Sequence:** DL-22 → DL-23 → DL-24

**Play:** In Mara's later home, reach the rear service recess, retrieve a disconnected chair coupling and reconnect it so the dining table locks at balcony height. Restarting the cycle sets a second empty bowl.

**Learning and connection:** Reinterpret scene 21 without changing its rules. Success can expose loss rather than provide a celebratory payoff.

**Story evidence:** One chair is worn; the other has been deliberately withdrawn. A shared portrait and carefully stored cardigan make the absence personal. The player's practical solution briefly reinstates a routine Mara had chosen to stop.

**Player understanding:** A dinner routine → evidence of a consequential absence.

**Cinematic beat:** Repeat scene 21's serving rhythm, now into a vacant place. Stay with the second bowl for a moment after the route opens.

#### 24 What She Kept

**DL-24 · Quiet interaction · 1.5 minutes**  
**Sequence:** DL-23 → DL-24 → DL-25

**Play:** Fold down a small workbench to clear the balcony exit. Its underside reveals a familiar two-person repair jig adapted for use by one pair of hands.

**Learning and connection:** Give the previous scene room to register. Human modification, rather than another record, shows her response to loss.

**Story evidence:** The second mug is wrapped safely beside the childhood ornament, while the tools remain in use. Mara kept a relationship's traces without leaving every part of her life frozen around them. We need no explanation of how her partner died.

**Player understanding:** A life frozen by loss → a person who kept both memories and useful work.

**Cinematic beat:** The workbench rotates the adapted jig into view. Let the wrapped mug sit nearby without centring every keepsake at once.

#### 25 Leaving a Light

**DL-25 · Applied challenge · 3 minutes**  
**Sequence:** DL-24 → DL-25 → DL-26

**Play:** Park the serving arm in its safe position, then move its local power coupling to the service lift. A separate small lamp remains lit over the keepsakes.

**Learning and connection:** Introduce routing power through the same visible connection logic as tracks. Only verified empty domestic service circuits are involved.

**Story evidence:** D17 stops preserving an empty routine when it obstructs a useful task. The lift carries him toward Mara's work address. It is his first clear practical departure from treating every functioning process as something to perpetuate.

**Player understanding:** Functioning routines should continue → some should be stopped to make progress.

**Cinematic beat:** The serving arm stops, but the small keepsake lamp remains. Let the reduction in domestic noise make the departure perceptible.

### Chapter 4 The Work Above

**Scenes 26–33 · 30 minutes.** The purpose of the bunker is reinterpreted.

#### 26 The Intake

**DL-26 · Applied challenge · 2 minutes**  
**Sequence:** DL-25 → DL-26 → DL-27

**Play:** Turn a valve and watch water lift a float connected to a gate. Let it drain once, then refill and cross. A small inspection tank keeps the entire cause and effect visible.

**Learning and connection:** Translate weight and counterweights into water states. No simulated fluid skill or new input is introduced.

**Story evidence:** Huge pipes disappear upward while the surrounding industrial level is dark. The first impression is that a failing population spent its remaining resources feeding an unseen destination.

**Player understanding:** Unexplained industry → a question about where scarce resources went.

**Cinematic beat:** Frame valve, float and gate together. The pipe leaving the little demonstration tank points into a much larger dark space.

#### 27 A Share of the Water

**DL-27 · Developed puzzle · 5 minutes**  
**Sequence:** DL-26 → DL-27 → DL-28

**Play:** Fill a reserve tank from an abandoned wash line, close its retaining gate, then use the stored water to raise a service platform while the main circulation continues.

**Learning and connection:** Combine storage from scene 8, route selection from scene 25 and the float rule from scene 26.

**Story evidence:** Improvised branch connections show successive residents extending the system with whatever was available. Resource pressure is visible, but the puzzle never requires stealing water from an occupied ward.

**Player understanding:** Resources simply consumed → scarcity managed through adaptations.

**Cinematic beat:** Make the retained water visibly distinct from the continuing main flow. Repairs in several materials convey accumulated ingenuity.

#### 28 Other Hands

**DL-28 · Applied challenge · 3 minutes**  
**Sequence:** DL-27 → DL-28 → DL-29

**Play:** Switch a maintenance carrier onto a repaired track, stop it beneath a broken ladder and latch it before climbing. Apply familiar actions while machinery moves on a much larger scale.

**Learning and connection:** Confident reuse of routing and latching between substantial puzzles. Shift from personal biography to the scale of shared work.

**Story evidence:** Different welding, repairs and makers' marks accumulate along the route. Mara's work belongs to a collective effort spanning generations. Damaged surface instruments suggest the world outside needed deliberate help.

**Player understanding:** One person's project → many people's accumulated work.

**Cinematic beat:** The carrier passes human-scale handrails beneath machinery too large for one person. Avoid an individual hero portrait.

#### 29 The Root Lift

**DL-29 · Developed puzzle · 5 minutes**  
**Sequence:** DL-28 → DL-29 → DL-30

**Play:** Fill a counterweight reservoir, ride its lift to the brake, secure the mechanism, then release water through a second channel. Early draining merely lowers the lift and allows a quick retry.

**Learning and connection:** A clear synthesis of scenes 8, 26 and 27. Finish the reasoning before the major visual reveal.

**Story evidence:** Following the outflow reveals the structure from Mara's drawings at enormous scale. The destination is beginning to look biological. The player discovers purpose by making the system work.

**Player understanding:** A personal drawing → a functioning structure on an immense scale.

**Cinematic beat:** Follow the released water with one restrained camera move, stopping short of showing the entire root chamber.

#### 30 The First Leaf

**DL-30 · Quiet interaction · 2 minutes**  
**Sequence:** DL-29 → DL-30 → DL-31

**Play:** Crank open an inspection shutter. Its task lamp reveals established roots receiving the water, and small leaves moving high beyond the machinery.

**Learning and connection:** A simple action changes the interpretation of the preceding chapter. This is the main midpoint release, around minute 75.

**Story evidence:** The bunker was helping restore the surface. Growth was already underway; D17 has reopened one neglected branch. At the midpoint, apparent industrial futility becomes evidence of care for a future its workers might never see.

**Player understanding:** Apparently futile industry → a restoration effort already sustaining life.

**Cinematic beat:** The shutter opening reveals a living leaf against machinery. Water and leaf movement carry the release before any music enters.

#### 31 The Broken Branch

**DL-31 · Developed puzzle · 5 minutes**  
**Sequence:** DL-30 → DL-31 → DL-32

**Play:** Guide overflow into a holding basin, use its float to reach a failed branch coupling, replace the coupling, then reopen the nursery channel while preserving the trunk's flow.

**Learning and connection:** Combine load transfer, stored water and connection placement. This is the most demanding reasoning puzzle in the works.

**Story evidence:** Mara completed most of the repair before losing access to the high connection. Her work was tangible, unfinished and useful. The wider restoration system keeps operating regardless of this local repair.

**Player understanding:** A finished legacy → a specific useful task still awaiting completion.

**Cinematic beat:** Show the broken branch and the continuing trunk together. Success sends water beyond D17's route to an area he never needs to enter.

#### 32 What She Could Reach

**DL-32 · Developed puzzle · 5 minutes**  
**Sequence:** DL-31 → DL-32 → DL-33

**Play:** Carry a small valve link across slow phased service platforms, latch the carrier at a handrail, and install the link through a narrow access gap. No new rule is introduced under pressure.

**Learning and connection:** A developed execution sequence after scene 31's reasoning. Save each completed stage and reset only the failed crossing.

**Story evidence:** Mara's repairs become lower, grips become larger, and two-handed controls acquire one-handed adaptations. She continued working as her body changed. The final inaccessible gap explains why D17 can complete something she could not.

**Player understanding:** A repair left undone → physical limits met with continued ingenuity.

**Cinematic beat:** Match the current grip and repair shape to the earlier landing, now lower and adapted. Readability takes priority over industrial clutter.

#### 33 The Upward Line

**DL-33 · Applied challenge · 3 minutes**  
**Sequence:** DL-32 → DL-33 → DL-34

**Play:** Park the ascending service carrier beside the medical balcony and release its bridge. A local forwarding terminal identifies the ward as Mara's next recorded address.

**Learning and connection:** A low-pressure application of the chapter's carrier logic. Reduce intensity before introducing a new behavioural system.

**Story evidence:** From the quiet ascent, see living growth continuing beyond the repaired branch. Then the view narrows into clinical architecture. The question changes from what Mara built to what happened to her afterward.

**Player understanding:** What did Mara build → what happened to her afterward.

**Cinematic beat:** Allow a distant view of growth during the lift, then let the medical wall close that view. The audio changes from water to regulated breathing machinery.

### Chapter 5 Protective Custody

**Scenes 34–41 · 28 minutes.** An apparent threat becomes evidence of surviving care.

#### 34 Please Remain

**DL-34 · Applied challenge · 3 minutes**  
**Sequence:** DL-33 → DL-34 → DL-35

**Play:** An attendant gently retrieves D17 from a marked active hazard zone and puts him on a powered safe bay. A rolling transport dummy demonstrates the same sequence before the next crossing.

**Learning and connection:** Introduce one consistent rule: movement in an active zone triggers transport to the nearest powered safe bay along its rail.

**Story evidence:** The machine is enormous and frightening, yet its padding and careful deposit are unmistakably protective. Its instructions outlived the community they served. Capture is information rather than a death penalty.

**Player understanding:** Predatory machine → frightening equipment with a protective rule.

**Cinematic beat:** Stage the first reach as alarming, then reveal the padded cradle and careful deposit. Keep D17's recovery visible.

#### 35 An Empty Bed

**DL-35 · Developed puzzle · 4 minutes**  
**Sequence:** DL-34 → DL-35 → DL-36

**Play:** Send the transport dummy rolling into one hazard zone. Cross a second while the attendant completes its visible retrieval trip. Safe islands allow observation without a strict reaction test.

**Learning and connection:** Apply timing from the school to the retrieval rule. The machine responds to sensed movement, not hidden knowledge of the player.

**Story evidence:** Entire ward rows are empty, with equipment consolidated near one maintained room. The player can see how a system designed for many inhabitants contracted around fewer people.

**Player understanding:** Abandoned medical system → care concentrated around fewer occupants.

**Cinematic beat:** The attendant's headlamp traces its whole trip. A distant maintained bay contrasts with the surrounding dark beds.

#### 36 A Handrail for One

**DL-36 · Applied challenge · 3 minutes**  
**Sequence:** DL-35 → DL-36 → DL-37

**Play:** Lower a patient-transfer platform, brake its supports and cross a damaged floor outside the active retrieval zones. Familiar load transfer creates a breather within the ward.

**Learning and connection:** Reuse scenes 19 and 32 with a different human purpose. Keep the player's reasoning load low between retrieval puzzles.

**Story evidence:** The familiar grip modifications and tree mark appear beside a patient bed. Mara was both a user and repairer of this equipment. The maintained room is becoming personal, but these traces do not yet establish that she is alive.

**Player understanding:** Unknown patient → someone connected to Mara's repair history.

**Cinematic beat:** Bring the familiar handmade grip into the foreground beside a patient bed. Keep the next active retrieval zone visually separate.

#### 37 The Safe Place

**DL-37 · Developed puzzle · 5 minutes**  
**Sequence:** DL-36 → DL-37 → DL-38

**Play:** Move a service coupling so an elevated bay becomes the nearest powered destination. Test the route with the dummy, then deliberately enter the hazard zone and let the attendant lift D17.

**Learning and connection:** Combine power routing and retrieval. This is the ward's central reinterpretation, not a new ability or an enemy surrender.

**Story evidence:** The same behaviour that felt like imprisonment becomes assistance. Nothing about the attendant's intentions changes; the player has learned how its limited definition of help works.

**Player understanding:** Capture prevents progress → the same transport can provide a route.

**Cinematic beat:** Show the dummy arriving at the high bay before the player commits. Repeat exactly the same framing when D17 takes its place.

#### 38 The Long Watch

**DL-38 · Quiet interaction · 1.5 minutes**  
**Sequence:** DL-37 → DL-38 → DL-39

**Play:** Turn a bedside task lamp to find a manual release behind a folded privacy screen. Opening it reveals a service recess connected to the next corridor.

**Learning and connection:** A quiet familiar interaction complicates the threat before the climax. Give the machine a consistent purpose, not a hidden evil reveal.

**Story evidence:** Human wire repairs and machine-made braces reinforce the same bed. Through the recess, the attendant replaces one of its worn lifting pads. Its persistent care helped somebody survive even as its rules restricted them.

**Player understanding:** Care only as confinement → care also as prolonged survival.

**Cinematic beat:** The task lamp reveals human and machine repairs together. Let the attendant's pad replacement read as maintenance rather than a threatening flourish.

#### 39 The Care Circuit

**DL-39 · Developed puzzle · 5 minutes**  
**Sequence:** DL-38 → DL-39 → DL-40

**Play:** Use two service couplings to route the attendant between a low bay and an elevated maintenance bay, carrying a replacement bridge pin upward with D17. Seat the pin before changing bay power again.

**Learning and connection:** Combine scenes 19, 25 and 37. The load must be latched before support moves; the bed circuit is never a solvable sacrifice.

**Story evidence:** Bedside ventilation remains on an explicitly separate protected circuit. D17 gains passage by working around care that is still needed. A familiar hand-built bypass leads toward the upper residence.

**Player understanding:** Escape may require disruption → passage can preserve essential care.

**Cinematic beat:** Keep the separate bedside circuit visibly steady while service couplings change. Let the player see that solving the route preserves care.

#### 40 The Broken Reach

**DL-40 · Developed puzzle · 5 minutes**  
**Sequence:** DL-39 → DL-40 → DL-41

**Play:** Secure the crossing, send the dummy through a lower retrieval zone to clear the rail, then route D17 to the final upper bay. Telegraph the damaged machinery along the transfer with sparks and motion.

**Learning and connection:** Mechanical climax using known rules. The short landing beat is not a failed input or a hidden lethal trap; the puzzle remains solved.

**Story evidence:** After the player's successful transfer, a brief authored landing failure makes D17's old knee buckle; the attendant's support prevents the fall. He is left on a safe landing, damaged but intact. His supposed enemy has just protected him.

**Player understanding:** D17 only helps others → he is also vulnerable and can be helped.

**Cinematic beat:** During the deposit, D17's knee gives way; the cradle maintains support until he settles. Use contact and mechanical strain, not an extended injury cutscene.

#### 41 Still Warm

**DL-41 · Quiet interaction · 1.5 minutes**  
**Sequence:** DL-40 → DL-41 → DL-42

**Play:** Release a recently repaired latch and enter a workshop antechamber. A short safe approach lets D17 move carefully on the damaged knee.

**Learning and connection:** Reward accumulated attention with a change in expectation. No chase interrupts the inference.

**Story evidence:** Fresh shavings, a steaming mug, a living plant and light moving beneath an inner door provide independent signs of recent habitation. An optional cough supports the visual evidence. For the first time, hope of finding someone is well grounded.

**Player understanding:** Historical traces → credible evidence of someone here now.

**Cinematic beat:** The small steam plume is visible before the sound of a cough. A second sign, the fresh repair surface, keeps the inference accessible without audio.

### Chapter 6 Recipient Found

**Scenes 42–46 · 18 minutes.** An imagined recipient becomes a willing collaborator.

#### 42 The Wrong Delivery

**DL-42 · Applied challenge · 3 minutes**  
**Sequence:** DL-41 → DL-42 → DL-43

**Play:** An outstretched hand beneath a lift assembly wants a spanner. D17 first offers the parcel; Mara nudges it aside. Move a small tool trolley within reach and give her the matching tool.

**Learning and connection:** Use familiar carry and place to read a person's gesture. Wrong tools receive brief feedback, not a repeated comedy lock.

**Story evidence:** The recipient is busy, practical and faintly impatient. Her ordinary humour breaks the dread. The shared motifs identify her workshop, but her response immediately exceeds the personality we inferred from her belongings.

**Player understanding:** An imagined recipient → a busy person with her own immediate intention.

**Cinematic beat:** Frame Mara's hand, the wrong parcel and the correct tool together. Her small impatient correction is enough; do not repeat the joke.

#### 43 The Receiver

**DL-43 · Quiet interaction · 2 minutes**  
**Sequence:** DL-42 → DL-43 → DL-44

**Play:** Sit on a service stool when Mara notices the bad knee. She repairs it with the same bracket technique seen earlier. Present the parcel close enough for her to inspect its old address.

**Learning and connection:** Recall sitting from scene 15 and the repair from scene 19. Restore normal movement here; never make the finale a prolonged limp.

**Story evidence:** She recognises her parent's markings and touches the crooked tree on the wrapper, then the matching keepsake. D17 accepts care. Mara holds the parcel for a moment, then lets him secure it while they finish opening the route outside.

**Player understanding:** D17 as giver → D17 as a willing recipient of care.

**Cinematic beat:** Move close for the repaired knee and label recognition. Mara's pause at the familiar mark carries the feeling without spoken history.

#### 44 Two at the Bench

**DL-44 · Developed puzzle · 5 minutes**  
**Sequence:** DL-43 → DL-44 → DL-45

**Play:** D17 braces a counterweight while Mara seats its safety pin; she then holds the release while he passes through a narrow service duct and reconnects the lift coupling. Each partner waits until the other is ready.

**Learning and connection:** Reinterpret substitution: a collaborator can hold a state, communicate and respond. No simultaneous-button precision or new companion command.

**Story evidence:** Neither can finish alone. Behind the panel, a fresh bypass feeds the depot branch and repeats the opening relay pulse: Mara's earlier repairs woke D17. Now his help finishes hers. Their cooperation adds a new relationship without pretending to replace the partner she lost.

**Player understanding:** A chance meeting → a reciprocal chain set in motion by Mara's earlier work.

**Cinematic beat:** The lift panel displays the depot branch and repeats the opening relay pulse. Then concentrate on two hands completing the same repair.

#### 45 The Window Test

**DL-45 · Developed puzzle · 5 minutes**  
**Sequence:** DL-44 → DL-45 → DL-46

**Play:** Raise a blocked sampling shutter using a latched counterweight. Mara operates the analyser while D17 connects the exterior intake, then returns to let her inspect the result.

**Learning and connection:** A cooperative synthesis of support, routing and observation. The world is recovering; a useful environmental reading is not a promise of personal immortality.

**Story evidence:** The exterior reading moves into an acceptable band; the hospital still flags the physical risks of her departure. Mara considers both, takes her walking support and releases the manual exit latch herself. D17 does not decide for her.

**Player understanding:** A person to extract → a person assessing and choosing departure.

**Cinematic beat:** Keep the improved environmental reading and unresolved personal-risk symbol distinct. Frame Mara choosing the manual release herself.

#### 46 What to Take

**DL-46 · Applied challenge · 3 minutes**  
**Sequence:** DL-45 → DL-46 → DL-47

**Play:** Park the unfinished work safely, bring Mara her walking support and place the portable rest seat on the lift trolley. She pockets the small tree keepsake. No inventory selection screen is needed.

**Learning and connection:** Apply the shutdown sequence from scene 25 to a living person's priorities. Prepare the support prop used in scene 50.

**Story evidence:** D17 begins arranging more tools; she gently redirects him toward the exit. Mara leaves a noncritical repair for another day. Her change is accepting that she may experience the world she helped prepare before every task is complete.

**Player understanding:** Every job must be finished first → safe unfinished work can wait.

**Cinematic beat:** Let D17 reach for another tool and Mara redirect that same hand toward the exit. Leave the safely parked work visible behind them.

### Chapter 7 First Delivery

**Scenes 47–51 · 14 minutes.** Both characters learn how to leave a task behind.

#### 47 The Open Door

**DL-47 · Applied challenge · 3 minutes**  
**Sequence:** DL-46 → DL-47 → DL-48

**Play:** Reach a release lever in a narrow side recess and hold the heavy door open for Mara. She crosses, takes over the manual hold on the far side, and lets D17 release his lever and follow.

**Learning and connection:** Apply shared state holding from scene 44 to traversal. Safe waiting nodes replace escort urgency.

**Story evidence:** The assistance immediately goes both ways. D17 no longer interprets an outstretched hand as a request for the parcel; at the next support point he offers his own.

**Player understanding:** One companion assists the other → both take responsibility in turn.

**Cinematic beat:** Hold both sides of the door in frame so the transfer of responsibility is unmistakable. Her return gesture should arrive before his thanks.

#### 48 The Last Lift

**DL-48 · Developed puzzle · 5 minutes**  
**Sequence:** DL-47 → DL-48 → DL-49

**Play:** With Mara holding the brake, position the counterweight, latch it and route power to the passenger platform. Lower its boarding bridge, bring the seat trolley aboard, then join her on the occupancy plate so she can start the car.

**Learning and connection:** Final synthesis of weight, latching, routing and cooperation. Difficulty comes from understanding the sequence, with no lethal timing or new rule.

**Story evidence:** Occupancy finally refers to actual people who intend to travel. The school required D17 to impersonate an absent child; here the system works because both companions are ready.

**Player understanding:** Occupancy as compliance → occupancy as shared readiness.

**Cinematic beat:** Echo the school's occupancy lamps, now beside two willing travellers. The lift moves only after their preparation and boarding are clear.

#### 49 The Threshold

**DL-49 · Applied challenge · 2 minutes**  
**Sequence:** DL-48 → DL-49 → DL-50

**Play:** Use a maintenance bar to brace the wind-loaded outer shutter while Mara turns its handle. Open it together and cross onto stable ground. Let the player control the walk into daylight.

**Learning and connection:** Echo the release latch in scene 1, now through mutual effort. Offer sensory contrast rather than a final attack.

**Story evidence:** Leaves move without a motor. The outside is weathered and uneven, with surviving infrastructure still visible. Mara sees a real landscape after spending her life imagining and preparing for one.

**Player understanding:** An imagined future → an imperfect living place they can enter.

**Cinematic beat:** Open into ordinary daylight, moving leaves and distant water. Avoid a triumphant panoramic cutscene; keep the small figures in the world.

#### 50 Somewhere to Sit

**DL-50 · Applied challenge · 2 minutes**  
**Sequence:** DL-49 → DL-50 → DL-51

**Play:** Move the portable seat onto a level patch Mara indicates and place a flat support beneath its short leg. Clear the immediate approach, then let her choose when to sit.

**Learning and connection:** Reframe balancing from scene 3 as practical care. No alignment puzzle, hidden score or forced precision diminishes the moment.

**Story evidence:** D17 starts to straighten an irrelevant crooked stone; Mara rests a hand on his wrist and looks toward the view. He stops. A slightly imperfect arrangement can be sufficient for somebody's comfort.

**Player understanding:** Correct arrangement → sufficient comfort for this particular person.

**Cinematic beat:** Frame the crooked stone, D17's hand and Mara's light touch in one readable composition. His unfinished adjustment is the performance.

#### 51 Delivered

**DL-51 · Quiet interaction · 2 minutes**  
**Sequence:** DL-50 → DL-51 → Credits

**Play:** Present the parcel when Mara reaches for it. She opens the children's outdoor boots, compares one with her own foot and sets them nearby. Delivery completes; the player can move in the safe vista and choose to sit beside her.

**Learning and connection:** Resolve the established sit and delivery interactions. The last uncertainty is what D17 does after his assignment is finished.

**Story evidence:** The parent's hope arrives too late in one sense and in time in another. Mara accepts the present without erasing her losses. D17 has no next address and stays anyway. The credits begin on the shared rest, with no death scene or threat sting.

**Player understanding:** Complete the delivery and proceed → complete it and freely remain.

**Cinematic beat:** The tiny boot against her adult foot permits one quiet shared joke. Let wind continue after the delivery lamp clears and before the voluntary sit.

## Continuity and pacing constraints

- **Timeline:** Mara is 82; the parcel was sent when she was six; D17 has been dormant for 76 years. Her current work restored power to the buried depot. The workshop relay pays off that opening cause without implying that she knew the courier had survived.
- **Scale of human effort:** Mara is a contributor to a collective restoration project. The surface is already recovering; repairing one branch does not save the entire biosphere. The bunker is the last known refuge, and global extinction remains unverified.
- **Evidence:** Pair the distinctive crooked-tree mark with recurring belongings and repair habits. Essential inferences need independent cues. A missed ornament must not make the final recipient unrecognisable.
- **Forwarding:** Explicit records occur at the bedroom, school exit and medical approach. Between those, the route follows life, work and physical infrastructure. Avoid repeated empty-address reveals at every door.
- **Attendant rule:** Movement in a marked active zone triggers retrieval along the visible rail to the nearest powered safe bay at dispatch. The attendant completes that trip before responding again. Preserve both readable destinations and consistent sensing.
- **Essential care:** Bedside ventilation remains on a separate protected circuit. The solution is never to endanger an unseen patient to open a door. Service couplings alter service machinery only.
- **Injury:** The brief knee failure is an authored deposit beat after successful play, not an unforeseeable lethal test. It creates a reason for reciprocal care and ends in scene 43. Do not impose a long limp or replay the injury on every failed attempt.
- **Companion:** Mara waits at visible safe nodes, reads prepared mechanisms and contributes automatically when the player is ready. No escort health bar, abandonment timer or deliberately unsafe pathing. Let the player work ahead while she rests.
- **Parcel:** It remains safely stowed except for presentation and the brief recognition exchange. It is never an arbitrary puzzle weight or a repeatedly dropped key. The boots stay unseen until scene 51.
- **Pacing:** Separate reasoning from execution where possible. Give scenes 23, 30, 41, 43 and 51 reaction time. After the ward, retain problems and cooperation while reducing danger; do not install a surprise final boss.
- **Recovery:** Save permanent puzzle solutions before execution tests. Target under three seconds to regain control and avoid repeating more than twenty seconds of already-solved traversal. Carryable components have recoverable positions and placement sockets.
- **Presentation:** Use the approved mature D17 and dark tonal references. The GDD keeps the 2D spline-driven versus stylised-3D implementation decision open until an in-engine motion/contact proof. These scene requirements work with either pipeline.
- **Accessibility:** Important sound has a visual equivalent. Keep the active mechanism and consequence in frame or reveal their connection deliberately. Verify critical clues and expressions at handheld screen size.
- **Ending:** Mara chooses departure after reading the conditions; D17 supports the choice. The voluntary final sit is companionship. No death scene, hidden punishment for waiting, or threat sting reframes that conclusion.

## Review before production

Review the sequence in contiguous blocks, then as a complete journey. The priority proofs remain the empty classroom, protective retrieval and Mara's tool exchange. Scenes 23, 29, 44 and 51 add checks for emotionally mixed success, spatial reasoning, reciprocal contact and the voluntary ending.

Use unfamiliar-player observations to test what people actually infer. Ask what they think the machinery is doing, who Mara became, what they expect next, and whether her departure feels like her own decision. Keep completion time and puzzle success separate from emotional interpretation.

Before implementation, expand each approved overview into the GDD's full scene card: identity and neighbours, belief change, playable objective, performance, camera/light/sound, continuity flags, accessibility, recovery and acceptance evidence. An overview is not a substitute for the storyboard, playable timing or director review.

The central design risk is repeated handling becoming predictable. If two adjacent scenes ask for the same inference, consolidate their mechanical work while retaining the distinct discovery. Cut redundant waiting and transit before cutting reaction time or adding extra complexity.

The final emotional claim should remain modest and specific: the gift cannot return Mara's childhood or the people she lost. It can arrive while she is still here, and the courier can become someone who stays.
