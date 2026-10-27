# Core/Scenes

One `ChapterSim` per chapter (port_architecture §7, "Core state is global"). It builds every scene of a `ChapterDef`
into one world: one `MechanismGraph`, one `LaneGeometry` (per region, the scenes' tables joined and all their
contributors), one `InteractionResolver`, one `CheckpointService`. Nothing freezes when he leaves a scene, and a
respawn or continue anywhere rebuilds the whole world there. `Current` is the scene that holds him (`sceneName`);
`SceneChanged(from, to, dir)` fires at the end of the step he crosses a seam; `Next`/`DistanceToSeam` feed streaming;
`MechanismsOf(scene)` is a scene view's read-only binding. The step order is in `ChapterSim`'s summary.

**Mechanism update order:** each scene's own order, scenes in lane order. The prototype updates by system (§3.1,
L8511–L8518), which interleaves scenes, but no mechanism reads another scene's, so the two agree:
`PrologueChapterTraceTests` replays DL-01 to DL-06 (#1768–#14016) in one sim at 1e-6.

## Adding DL-07 to the prologue

1. **Lane table** (`Lane/Tables/Dl07Lane.cs`): the static lane of its stretch, every value cited, plus a
   `Contributors(graph)` factory adapting its own mechanisms. A region's tables are joined at the scenes' X0
   (`LaneTable.Join`): each answers only on its own stretch, so it need not repeat its neighbours' parts.
2. **Scene def** (`Scenes/Dl07/Dl07Scene.cs`, `Def()` with no parameters): `Id`, `Region`, `X0`/`X1` (in a region each
   scene starts where the one before ends), its mechanisms in step order, `Lane`, `LaneContributors`, `Interactables`,
   `Rules`, and `Motor` only for a #28 tuning. **DL-07 shares DL-06's floor**: give it DL-06's span (`X0`/`X1` equal:
   `ChapterDef` allows a scene on the same stretch) and only the mechanisms DL-06's def does not already build (the
   weights, line and levers are there once; a second `Dl06Scene.Floor(...)` would add them twice). Who holds him is
   then `ReturnToSender06.HasLeft` (state, L8141), not x.
3. **Rules** (`SceneRules`): hooks get the `ChapterSim`. They run while the scene holds him; set `Always` when a rule
   reaches past the stretch (DL-03's slam startles him on either side of the gate) and guard it as the prototype does.
   Set `Motor.SlowWalkLimit` in `BeforeMotor` each step it applies (the chapter clears it). State another scene reads
   goes in the graph or in `sim.Shared<T>()` (DL-03/04's `RacksReveal`), taken in `OnBegin`; never in `Def(...)`.
   `PlayerPose` has no region: a mechanism under a gallery (DL-07's `game.upper`) checks it through its rules.
4. **Acts and cues:** use the motor's acts where they match the prototype: `sim.Die(kind)`, `Motor.BeginStuck()`,
   `Motor.PlayQuirk` only from inside #4 before the motor steps. A quirk started after the motor's step is
   `SceneQuirk.Start` (a `QuirkAct`; the motor's runs a step long, #28). Cues are `CueId.Of("name")` in a static
   field, raised with `sim.Cue(id, arg)`; nothing is formatted per step.
5. **Checkpoints:** add the rows to `ChapterDefs.PrologueCheckpoints` (DL-07's are there already: `landing`, `gallery`),
   then list the def in `ChapterDefs.Prologue()` in lane order.
6. **Trace tests:** a scene replay (`Dl07TraceTests`, `TraceReplay.Run` with the `SceneSim` test shim, from a rest
   before the scene, `handover: true`), then extend `PrologueChapterTraceTests` to DL-07's last step: its act mapping,
   its mechanisms over its steps, and the seam steps in `CurrentScene_IsTheSceneName_EveryStep...`. The chapter replay
   is the proof; a per-scene window only localises a failure.

## Known motor gaps kept as scene acts (#28)

`QuirkAct` for quirks started after the motor's step (DL-03 Startle, DL-05 CheckLabel/Pat, DL-06 Startle/PeekDown/
Proud) and for DL-01's wake label (the motor's quirk counts its start step in cancelAfter and the hold: two steps
early); `HoldAct` for DL-06's label check (a motor act cannot be ended from outside); `Place` to stop him (M9) in
`SceneQuirk.Stop`, DL-04's realisation and DL-06's check; `DeathAct` for a death he sinks in (DL-07's sump).
