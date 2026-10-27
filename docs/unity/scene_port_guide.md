# Porting a scene to Unity (U-20/21/22)

**Status:** 27 October 2026, from the DL-01 vertical slice (issue #16). DL-01 is the worked example; copy it.
**Reference files:** `Core/Scenes/SceneDefinition.cs`, `SceneRunner.cs`, `LaneGeometry.cs`, `LaneContributors.cs`,
`MechanismReadout.cs`, `Prologue/Dl01Wake.cs`; `unity/core-tests/Dl01PlaythroughTests.cs`; Runtime `Scenes/SceneHost.cs`,
`Scenes/MechanismView.cs`; Editor `Builders/SceneBuilder.cs`.

## 1. How a ported scene works

```
SceneDefinition (Core, plain C# data, L-cited)  ──►  SceneRunner (Core)  ──►  SceneHost (Runtime)  ──►  adapters
  mechanisms in update order, resolver set,          one 60 Hz step in §3.1      FixedTick, input,        D17Controller (hosted)
  LaneGeometry, spawns, checkpoint/cue/moment         order: gate → motor →       presents cues and         LaneCameraDriver (bound)
  rules, opening, exit, views                         graph → rules → checkpoints moments                   DirectedMomentPlayer (hosted)
                                                      → camera                                              MechanismView per MECH_ node
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
or the Motor/Interaction contracts. If you need a change there, work around it in the scene and write it down.

## 4. Writing the definition, member by member

- **Ids**: `public static readonly MechanismId XxxId = "dlnn.xxx"`: the §5 IDs; they are save keys, never rename.
  Suffix fields with `Id` so they never shadow the Core type of the same name.
- **Constants**: `public const` with the prototype's name in the comment and `// Lnnnn`. Resolve the offsets
  (`OFF3 + 52.45` → `85.45`) and negate three.js z for Unity (§0.2).
- **`AddMechanisms`**: in the prototype's update order (relays #5, `updateMechanisms`/`updateDLxx` #6, `updateCh1`
  etc. #7). A mechanism that reads another (`link.Read`) must be added after it.
- **`RegisterInteractables`**: every station (`IUsable`), pushable and carryable D-17 can use here.
- **`BuildLane`**: floor as boxes (a pit is a lower box between two floor boxes); `PLATFORMS`-style blocks; ceilings;
  `LeftLimit/RightLimit`. Anything that changes with a mechanism is an `ILaneContributor`: reuse `WallUntilEngaged`,
  `HingedCeiling`, `TippingBridgeLane`, or add a small one to `LaneContributors.cs` (no allocation in it).
- **`Spawns`**: one per checkpoint in this scene (`CHECKPOINTS[cp].x/y`).
- **`CheckpointRules`**: `Past(cp, x, minY)` for place triggers, `When(cp, id)` for state triggers.
- **`Cues`, `Moments`**: place/state-triggered music cues and directed moments. Act-triggered ones (DL-04 `kin`,
  DL-10 `ringc`) call `runner.StartMoment` from `AfterMechanisms` and set `runner.MomentActReady`.
- **`Opening`**: DL-01 only. **`Exit`**: the walk-through seam to the next scene (§7) and its `NextScene`.
- **`AfterMechanisms`**: read `runner.Graph.Log` for this step's one-shots: shakes, `RequestRespawn` (deaths,
  stuck), ride sync (#9: place D-17 on a lift's `FloorY`), framing signals (`runner.FramingSignals.Set`). No allocation.
- **`Shot`**: authored shots (label checks, moment shots via `MomentShots`) for the camera, else null.
- **`Views`**: one `MechanismViewDef` per moving art node and value: `On(type, id, part, channel, motion, cite)`, then
  `.About(pivot)` (Unity axes), `.Scaled(scale, offset)` (offset so the art's built pose reads 0), `.Reading(other)`
  when a node rides another mechanism. Rotations about z keep the three.js sign.

## 5. Test checklist (`DlNnPlaythroughTests.cs`)

Write a bot like `Dl01Bot`: it picks each step's input from Core state only (so it can start at any checkpoint),
presses Use when `Motor.PreviewUse` offers the target it wants, and hops after 8 still steps (bot.js `walk`).

- [ ] **Beats in order**: new game (or the scene's first checkpoint) → `Exited`, asserting every mechanism state,
      checkpoint, cue and key motor event (jump, mantle, grab) in order by step. Print the beat log.
- [ ] **Same-step rules**: checkpoints set by a state land on the step of that state (e.g. `shutter` on the release).
- [ ] **Save and continue at every checkpoint**: keep each save's bytes and `SaveKit.Dump(CheckpointSnapshot)`;
      a fresh runner on a copy continues, matches the dump, stands at the spawn, and the bot still reaches the exit.
- [ ] **Determinism**: two full runs; motor snapshot + `Mech.Dump` + camera pose + cues equal at every step.
- [ ] **Each failure path**: walk into the hazard or dead end; assert the stuck/death timing and the respawn checkpoint.
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
