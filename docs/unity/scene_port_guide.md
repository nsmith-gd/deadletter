# Porting a scene to Unity (U-20/21/22)

**Status:** 27 October 2026, from the DL-01 vertical slice (issue #16), with the motor acts and generic loose things
of U-11b (#22). DL-01 is the worked example; copy it.
**Reference files:** `Core/Scenes/SceneDefinition.cs`, `SceneRunner.cs`, `LaneGeometry.cs`, `LaneContributors.cs`,
`MechanismReadout.cs`, `Prologue/Dl01Wake.cs`; `unity/core-tests/Dl01PlaythroughTests.cs`; Runtime `Scenes/SceneHost.cs`,
`Scenes/MechanismView.cs`; Editor `Builders/SceneBuilder.cs`.

## 1. How a ported scene works

```
SceneDefinition (Core, plain C# data, L-cited)  ──►  SceneRunner (Core)  ──►  SceneHost (Runtime)  ──►  adapters
  mechanisms in update order, resolver set,          one 60 Hz step in §3.1      FixedTick, input,        D17Controller (hosted)
  LaneGeometry, spawns, checkpoint/cue/moment         order: gate → motor →       presents cues and         LaneCameraDriver (bound)
  rules, opening, exit, views, control-return         graph → rules → escorts →   moments                   DirectedMomentPlayer (hosted)
  beats                                               ride sync (#9) → checkpoints                          MechanismView per MECH_ node
                                                      → camera
SceneBuilder (Editor) writes Assets/Scenes/<Chapter>/DLnn.unity from the same definition.
```

Core owns every outcome. Runtime only reads `SceneRunner` state. Nothing in the `.unity` file is placed by hand.

## 2. What to read (and only that)

1. `docs/unity/port_architecture.md`: your scene's §5 row, then the §4 sections its "Systems used" column names.
   Also §3.1 (the step order), §4.6 (the lane), §4.28 (checkpoints).
2. The scene's `docs/scenes/DL-nn_*.md`: §1 (what it must do), the checkpoints section, the acceptance or scene card,
   and **every "Pass n" section** (later passes override the plan; the code overrides both, §10 #9).
3. index.html, **only the line ranges in the §5 row**, with `sed -n 'a,bp'`. Never open it whole. Look for the
   scene's constants, its `CHECKPOINTS` entries (L7975–8014), its part of `floorAt/surfaceAt/ceilingAt/limits`
   (L1617–1769, L4135–4201), its exit or transit, and its `updateXx` rules.
4. `tools/sim/bot.js`: only your scene's coroutine (e.g. `wake()` for DL-01). It is the route your test bot copies.
5. Existing Core: `grep -rn "Dlnn" unity/DeadLetter/Assets/DeadLetter/Core` finds the params factories
   (`DoorParams.Dl01Shutter()`) U-10 already wrote. `Core/Mechanisms/README.md` explains the family classes.
6. Art names: `docs/unity/name_map.csv` and the region's `Assets/Art/<region>/<region>.art.json` (PR #24). Each view
   targets `MECH_<CoreClass>_<scene>_<name>[__part]`.

## 3. Files to create

| File | What goes in it |
|---|---|
| `Core/Scenes/<Chapter>/DlNnName.cs` | `sealed class DlNnName : SceneDefinition` (template: `Dl01Wake`). |
| `Core/Scenes/MechanismReadout.cs` | One line in `SceneCatalog` (`Ids`, `Create`); a `ViewChannel` case only if a view needs a new value. |
| `unity/core-tests/DlNnPlaythroughTests.cs` | A state-driven bot plus the tests in §5. |
| `Editor/Builders/SceneBuilder.cs` | One menu line: `[MenuItem("Dead Letter/Build/Scenes/DL-nn")] … Build(new DlNnName(), "Assets/Scenes/<Chapter>/DLnn.unity")`. |
| New mechanism types, if the §5 row needs one Core lacks | One class per **type** under `Core/Mechanisms/<Family>/`, per its README. Never scene logic in a mechanism. |

Do not edit the framework files (`Mechanism.cs`, `MechanismGraph.cs`, `Signals.cs`, `Station.cs`, `StepContext.cs`)
or the Motor/Interaction contracts. If you need a change there, work around it in the scene and write it down (as
U-10 did; #22 then replaced those workarounds with the contracts in §4a).

## 4. Writing the definition, member by member

- **Ids**: `public static readonly MechanismId XxxId = "dlnn.xxx"`: the §5 IDs; they are save keys, never rename.
  Suffix fields with `Id` so they never shadow the Core type of the same name.
- **Constants**: `public const` with the prototype's name in the comment and `// Lnnnn`. Resolve the offsets
  (`OFF3 + 52.45` → `85.45`) and negate three.js z for Unity (§0.2).
- **`AddMechanisms`**: in the prototype's update order (relays #5, `updateMechanisms`/`updateDLxx` #6, `updateCh1`
  etc. #7). A mechanism that reads another (`link.Read`) must be added after it.
- **`RegisterInteractables`**: everything D-17 can use here: stations (`IUsable`), place targets, pushables (a
  two-sided `Pushable` also registers its `Twin`; one with a deck its `DeckTarget`), carryables, hide spots
  (`HideSpot`) and rides (`CarrierLine.Rider`).
- **`BuildLane`**: floor as boxes (a pit is a lower box between two floor boxes); `PLATFORMS`-style blocks; ceilings;
  `LeftLimit/RightLimit`. Anything that changes with a mechanism is an `ILaneContributor`: reuse `WallUntilEngaged`,
  `HingedCeiling`, `TippingBridgeLane`, `CarryableLane` (a weight or box resting in the lane), `PushableLane` (a
  trolley's deck or ballast), `ReturnsBeltLane` (crates are ground; it is also an `ILaneConveyor`, so the motor is
  carried while he stands on the running belt), `SweptVolumeLane` (a folding leaf: ground when down, a ceiling while
  it moves or is propped), or add a small one to `LaneContributors.cs` (no allocation in it).
- **`Spawns`**: one per checkpoint in this scene (`CHECKPOINTS[cp].x/y`).
- **`CheckpointRules`**: `Past(cp, x, minY)` for place triggers, `When(cp, id)` for state triggers.
- **`Cues`, `Moments`**: place/state-triggered music cues and directed moments. A moment plays once per game: its
  `seen` key (`MomentRule.Key`, default the moment's name; §4.5's `realise`, `awe`...) is saved with the slot
  (`SaveModel.Seen`, v3) and cleared by Start over. Act-triggered ones (DL-04 `kin`, DL-10 `ringc`) call
  `runner.StartMoment` from `AfterMechanisms`, mark `runner.MarkSeen(key)` and set `runner.MomentActReady`.
- **`Opening`**: DL-01 only (its Skip is `runner.SkipOpening`: `MomentDirector.Skip` jumps to the control-return
  state). **`Exit`**: the walk-through seam to the next scene (§7) and its `NextScene`.
- **`OnControlReturned(runner, fromOpening)`**: `startPlay`'s beats when a moment or the opening hands control back
  (natural end, cut or skip), before that step's motor update: DL-01's `labelWake` label check
  (`runner.Motor.PlayQuirk(ClipNames.CheckLabel, …)`, once per game with `HasSeen`/`MarkSeen`).
- **`AfterMechanisms`**: read `runner.Graph.Log` for this step's one-shots: shakes, failures (`runner.Stuck()` for a
  stuck act, `runner.Die(DeathKind.X)` for a death: the motor's act asks for the respawn itself; `RequestRespawn(delay)`
  only for a reload with no act of his), framing signals (`runner.FramingSignals.Set`). No allocation. Ride sync is
  the runner's (#9): every `ILiftRide` in the graph that is `Carrying`, and whatever he rides (`D17Motor.SyncRide`);
  an `IEscort` in the graph that wants him starts the escorted act. Do not move him from here.
- **`Shot`**: authored shots (the label check: `runner.LabelShot()`; moment shots via `MomentShots`) for the camera,
  else null. Runtime's `SceneHost` gives the runner the label's measured centre (`LabelCentre`).
- **`Views`**: one `MechanismViewDef` per moving art node and value: `On(type, id, part, channel, motion, cite)`, then
  `.About(pivot)` (Unity axes), `.Scaled(scale, offset)` (offset so the art's built pose reads 0), `.Reading(other)`
  when a node rides another mechanism. Rotations about z keep the three.js sign.

## 4a. What D-17 can do for a scene (motor acts and contracts, #22)

| Need | Use | Reference |
|---|---|---|
| A control he works (lever, crank, cord, valve) | `StationMechanism` + `Station(standX, reach, face, standZ, floorY, reachX, faceTowards)`; `Profile`; `OnActFrame` → `ActStep` | `Latch`, `Pawl`, `CrankActuator`, `CycleBrake` |
| A follow-up clip in the same act (latch Pull → Flinch 1.6 s) | `ActStep.Then("Flinch", 0.06)`; `ActFrame.Part` says which clip | `Latch` (L1875) |
| A hop after the clip (DL-18 strap: 0.4 m back) | `ActStep.HopBy(-0.4)` / `HopTo(x, y, z)`: Hop f8–f18, 0.38 arc, done f23 | `FoldingLeafParams.Dl18Bench` |
| The clip decided once he has stepped in | the motor asks `ProfileFor` again before the clip; read `ActFrame.Clip` | `Pawl` (L3305), `PointsLever` |
| Something he lifts and sets down; plates weigh it | `Loose/Carryable` (+ `CarryableLane`); decks via `CarryableParams.Decks` | `Dl03Weight`, `Dl02Box`; `LooseTests` |
| Something he pushes/pulls; plates weigh it | `Loose/Pushable` (twin, deck, blockers, loaded speed, `Accel`, `LetGoAtMax`) (+ `PushableLane`) | `Dl03Trolley`, `Dl08Trolley` |
| Something that tips into a pit | `Bridges/TippingBridge` (+ `TippingBridgeLane`) | `Dl01Cart` |
| A carrier he boards and rides | `IRide` (`CarrierLine.Rider`); Use or a standing jump boards; ride sync at #9 | `RideAndLaneTests` |
| A lift that carries him | `Lifts/Lift` (`ILiftRide.Carrying`): the runner snaps him to `FloorY` at #9 | `SlippingCage`, `Dl09SceneTests` |
| A belt that carries him | `ReturnsBeltLane` in the lane (`ILaneConveyor`) | `RideAndLaneTests` |
| A recess he hides in from a beam | `Beings/HideSpot` (`IHideSpot`); `PlayerPose.Hiding` and his z | `MotorActTests` |
| A being that walks him back | `IEscort` (`WantsEscort`, `Walk`): the runner starts `BeginEscort`; follow `PlayerPose.X`, stop when `Escorted` ends | `EscortTrolley` |
| Stuck (a dead end he cannot leave) | `runner.Stuck()`: Flinch from 0.2 s, reload 2.0 + 1.3 s later | DL-01 trench (L4519–L4521) |
| A death | `runner.Die(DeathKind.Crush/Shock/Grabbed/Fall)`: holds dropped, clip, shake, cut after 0.7–1.15 s, reload 0.6 s later | L7419–L7453 |
| A reaction or a held look (CheckLabel, Proud, PeekDown, Flinch) | `runner.Motor.PlayQuirk(clip, cancel, holdFor, cancelAfter)`, `Flinch()` | DL-01 `labelWake` (L8107) |

## 5. Test checklist (`DlNnPlaythroughTests.cs`)

Write a bot like `Dl01Bot`: it picks each step's input from Core state only (so it can start at any checkpoint),
presses Use when `Motor.PreviewUse` offers the target it wants, and hops after 8 still steps (bot.js `walk`).

- [ ] **Beats in order**: new game (or the scene's first checkpoint) → `Exited`, asserting every mechanism state,
      checkpoint, cue and key motor event (jump, mantle, grab) in order by step. Print the beat log.
- [ ] **Same-step rules**: checkpoints set by a state land on the step of that state (e.g. `shutter` on the release).
- [ ] **Save and continue at every checkpoint**: keep each save's bytes and `SaveKit.Dump(CheckpointSnapshot)`;
      a fresh runner on a copy continues, matches the dump, stands at the spawn, and the bot still reaches the exit.
- [ ] **Determinism**: two full runs; motor snapshot + `Mech.Dump` + camera pose + cues equal at every step.
- [ ] **Each failure path**: walk into the hazard or dead end; assert the act (`Motor.ActVerb == Verb.Stuck`,
      `Motor.IsDead`), its timing (`RespawnPending` 2.0 s after the stuck act starts; the reload 1.3 s later; a death's
      hold, then 0.6 s) and the respawn checkpoint.
- [ ] **Once-only beats**: moments and label checks play once per game, are in the save's `Seen`, survive a respawn
      and a continue, and come back after Start over; the opening's Skip hands control over at once and still plays
      the control-return beats.
- [ ] **Allocation**: `GC.GetAllocatedBytesForCurrentThread()` is unchanged over 240 steps of ordinary play.
- [ ] **Definition**: lane spot checks against index.html values (theory rows); every view names an art node
      (from name_map.csv) whose Core class equals `Type` and answers its channel; views read 0 at rest.
- [ ] `dotnet build unity/core-build` (netstandard2.1) and `dotnet test unity/core-tests` green.

## 6. Mapping a scene doc's acceptance checks

| Acceptance check (DL-01 §9 wording) | Where it is covered |
|---|---|
| Control by 0:20 / non-interactive time | Headless: the opening or moment's control step (`ControlReturnedThisStep`) |
| No failure states / no lethal hazards (or: each hazard is fair) | Headless: no `respawn` beat on the route; failure-path tests time each one |
| Completion time (median 1.5–2.5 min with players) | Headless gives a floor (bot time, logged). The median needs playtests |
| Players find the puzzle (90 % without the glyph), clear a climb in 1–2 tries | Playtest only. Headless proves it is possible and that `PreviewUse` offers the right target |
| Understanding ("what is he?", "what does he want?") | Playtest only |
| Readability at 720p handheld (label, latch, head direction) | Unity on a 1280×720 Game view and Switch profile; not headless |
| Photosensitivity, reduced flicker | Headless: calm mode changes mechanism output (`Graph.Calm`); the limit check is a Unity/cert task |
| Recovery: quit and reload at each checkpoint restores the exact state | Headless: save-and-continue test (mechanisms); Unity: the views and camera after a reload |
| Frame time on the Switch profile | Unity profiler only |

When the scene doc has no §9 acceptance section, use §1 "what the scene must do", its checkpoints section and the
"Pass n" changes as the beat list, and the table above for the categories.

## 7. Unity checks (no Editor in the container; do these once per scene in Unity 6)

1. Import PR #24's region art; run **Dead Letter → Art → Build Region Prefabs**, **Build → D17 Animator**, then
   **Build → Scenes → DL-nn**. Read the builder's warnings: each missing `MECH_` node is a name to fix.
2. Play from a clean save: the opening (if any), the route, the exit; then continue from each checkpoint.
3. Check each view moves the right way and pivots where it should (signs and pivots are the error-prone part).

## 8. Naming

Core class `DlNnName` (e.g. `Dl02SortingHall`), file of the same name; IDs `dlnn.name`; scene file
`Assets/Scenes/<Chapter>/DLnn.unity`; art region `DL-nn` (DL-06/07 share `DL-06_07`); tests `DlNnPlaythroughTests`,
`DlNnDefinitionTests`. Cite every value as `// Lnnnn` and every rule's `Cite`.
