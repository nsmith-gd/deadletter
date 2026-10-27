# Core/Scenes

One `ChapterSim` per chapter (port_architecture §7, "Core state is global"). It builds every scene of a `ChapterDef`
into one world: one `MechanismGraph`, one `LaneGeometry` (per region, the scenes' tables joined and all their
contributors), one `InteractionResolver`, one `CheckpointService`. Nothing freezes when he leaves a scene, and a
respawn or continue anywhere rebuilds the whole world there. `Current` is the scene that holds him (`sceneName`);
`SceneChanged(from, to, dir)` fires at the end of the step he crosses a seam; `Next`/`DistanceToSeam` feed streaming;
`MechanismsOf(scene)` is a scene view's read-only binding. The step order is in `ChapterSim`'s summary.

**Mechanism update order:** each scene's own order, scenes in lane order. The prototype updates by system (§3.1,
L8511–L8518), which interleaves scenes, but a mechanism reads another scene's only when that scene comes first (DL-07's
bucket and loading read DL-06's line and weights, from this step's log), so the two agree:
`PrologueChapterTraceTests` replays DL-01 to DL-10 (#1768–#27923) in one sim at 1e-6.

## Adding a scene to the prologue (DL-11 next)

The steps as DL-07 took them (U-21); DL-07's specifics are kept where they show the pattern.

1. **Lane table** (`Lane/Tables/Dl07Lane.cs`): the static lane of its stretch, every value cited, plus a
   `Contributors(graph)` factory adapting its own mechanisms. A region's tables are joined at the scenes' X0
   (`LaneTable.Join`): each answers only on its own stretch, so it need not repeat its neighbours' parts.
2. **Scene def** (`Scenes/Dl07/Dl07Scene.cs`, `Def()` with no parameters): `Id`, `Region`, `X0`/`X1` (in a region each
   scene starts where the one before ends), its mechanisms in step order, `Lane`, `LaneContributors`, `Interactables`,
   `Rules`. There is no per-scene motor tuning: a station that steps in at its own speed says so itself
   (`Station.StepInSpeed`, as DL-06's levers and DL-08's pawl at 0.4). **DL-07 shares DL-06's floor**: give it DL-06's span (`X0`/`X1` equal:
   `ChapterDef` allows a scene on the same stretch) and only the mechanisms DL-06's def does not already build (the
   weights, line and levers are there once; a second `Dl06Scene.Floor(...)` would add them twice). Who holds him is
   then `ReturnToSender06.HasLeft` (state, L8141), not x.
3. **Rules** (`SceneRules`): hooks get the `ChapterSim`. They run while the scene holds him; set `Always` when a rule
   reaches past the stretch (DL-03's slam startles him on either side of the gate) and guard it as the prototype does.
   Set `Motor.SlowWalkLimit` in `BeforeMotor` each step it applies (the chapter clears it). State another scene reads
   goes in the graph or in `sim.Shared<T>()` (DL-03/04's `RacksReveal`), taken in `OnBegin`; never in `Def(...)`.
   `PlayerPose` has no region: a mechanism under a gallery (DL-07's `game.upper`) checks it through its rules.
4. **Acts and cues:** use the motor's acts where they match the prototype: `sim.Die(kind)`, `Motor.BeginStuck()`,
   `Motor.PlayQuirk` only from inside #4 before the motor steps; `Motor.Stop()` is a rule's `game.vx = 0`. A scene act
   (`SceneAct`) stands in where the motor still cannot (#28): `SceneQuirk.Start` for a quirk started after the motor's
   step (a `QuirkAct`; the motor's runs a step long), a `QuirkAct` for DL-01's wake label (the motor's counts its start
   step: two steps early), `HoldAct` for a hold a rule ends (DL-06's label check), `DeathAct` for a death he sinks in
   (DL-07's sump). A scene act's kind and phase are `ActId`s (interned, as cues are) in static fields next to it, the
   prototype's names; a view matches `sim.SceneActKind`/`SceneActPhase` alongside the motor's `ActPhase`. Cues are
   `CueId.Of("name")` in a static field, raised with `sim.Cue(id, arg)`; nothing is formatted per step.
5. **Checkpoints:** add the rows to `ChapterDefs.PrologueCheckpoints` (the later scenes' are there already; check each
   one's `y`: a row with `c.upper` stands on the deck, `GALLERY.h` 1.6, unless it has its own `y`, L8039, L4113),
   then list the def in `ChapterDefs.Prologue()` in lane order. Reach a checkpoint in `AfterGraph` (its snapshot is the
   world a respawn restores, so take it after the step's mechanisms), even where the prototype sets it at #4. The chapter begins, continues and respawns only at a
   row whose scene it has (`CanContinueAt`); a slot at another chapter's row is refused (`Continue()` false).
6. **Trace tests:** record the scene's fields (`tools/sim/record_trace.mjs`, names ending in the scene's digit, only
   while `sceneName()` is the scene and on its exit step; verify every earlier field of every step unchanged), then a
   scene replay where the scene starts from a rest (`TraceReplay.Run` with the `SceneSim` test shim, `handover: true`;
   DL-07 has none: it starts mid-act on a running floor), then a chapter probe (`core-tests/ChapterTrace/Dl07ChapterProbe.cs`:
   an `IChapterTraceProbe` with its first step, its key acts and cues, its act mapping, its mechanisms sampled each step
   and checked over its steps) and one line in `ChapterTraceProbes.Prologue()`. `PrologueChapterTraceTests` then runs
   to the first step past the scene and derives the window, the seams and the checkpoint order (with the next scene's
   checkpoint if its first step reaches one, as DL-08's `goods`) from the probes. The chapter replay is the proof; a
   per-scene window only localises a failure. Nothing is compensated: every replay is strict (#30).

## DL-10 as ported (U-21), and notes for DL-11

- DL-10 (`Dl10/`, `Lane/Tables/Dl10Lane.cs`) is region 4 from `UPONLY.x0` 118.8 to `REGION5_X` 127.9, after DL-09. Its row
  is `uponly` (119.4, y `Deck`), reached grounded past `UPONLY.x0 + 0.4` (L4937). Nothing kills here.
- Mechanisms, in order: `dl10.case` (`CarriedItem`, heavy; in the car past `ringc`), `dl10.carPlate` (`LoadPlate`),
  `dl10.carGate` (`Door` on the plate, its 0.8 s delay on the game clock: `Door.BindClock`, as `game.clock − uo.loadedAt`),
  `dl10.upButton` and `dl10.serviceUp` (`Lifts/CallButton`: PressButtonHigh, the press at f16, done at f34), the crank and
  `dl10.serviceDoor`, then `dl10.lift` (`RelocationLift`, which is also `dl10.counterweight`). The car loader
  (`Dl10CarLoader`, an `IPlaceTarget`) steps him 0.5 into the doorway. Lane: the counterweight's floor in its shaft, the
  service door's wall until 0.98, the open shaft's edge, its far wall, ring C's landing at 0 past `UO.cw.x1`.
- Rules (`UpOnly10`): the buzz (Pips `car10` while empty; the first ever startles him 0.2 s after the act, a motor quirk from
  `BeforeMotor`), the ride, the `ringc` moment (`UpOnly10.Moment`, started on the car's `Go` from the footplate; the car
  follows its clock), the cold light (`ColdLight`, `LightOff`), shakes, and region 5 past `REGION5_X` on free movement.
- Scene act (#32): `Dl10RideAct` (he stands on the counterweight as it was at the step's start, `game.y = DECK − uo.d` at #4;
  the moment lets him go). `RelocationLift` never carries him by ride sync (the prototype has none for it).
- Proven in the chapter replay (`Dl10ChapterProbe`, #25182–#27923, DL-11's first step, strict); no scene replay of its own.
- **DL-11 starts at #27923** (x 127.917, y 0, vx 1.6, region 5, checkpoint still `uponly`, no act or hold). Region 5 has no
  lane in Core yet: `SetRegion(5)` leaves the lane on region 4 until DL-11's def adds region 5's table (X0 `REGION5_X`;
  `leftLimit0` there is `UO.cw.x0 + HALF`, L1758; `floorCh1`'s counterweight/0 floor also holds in region 5, L4137). The way
  back (region 5 → 4 at `x < REGION5_X − 0.2`, L2048) is DL-11's to add. Handed over: the car gone for good with the suitcase
  (`Gone`, d 1.6, the counterweight at 0), the gate shut, the service door up, `ringc` playing on (t ≈ 22.48 at #27923,
  let go at 22.0167, not cut). Past `ringc` the mechanisms reset to that state themselves.
- Not ported: `card_lastcar`, `tan_relocation`, the ambience's `order` → `heaps` once riding (L8154), the camera's framings
  and the `car10`/`ringc10` shot, the lobby's lights, lamps, gauges and ropes (view), hints.

## DL-09 as ported (U-21)

- DL-09 (`Dl09/`, `Lane/Tables/Dl09Lane.cs`) is region 4 from `CG.x0` 97.6 to `UPONLY.x0` 118.8, listed in `Prologue()`
  after DL-08, which starts the region (left of 97.6 is DL-08's: `SceneAt` finds it there). DL-09 reads nothing of
  DL-08's (the deck is 1.6 throughout region 4: `game.upper` holds from `landing` to `school`; the left wall is DL-08's,
  outside DL-09's stretch).
  Its checkpoint rows are `cage`, `landing8` and `tunnel` (`tunnel` now stands on the deck, y 1.6); it reaches `tunnel`
  from DL-08's `goods` and `latched` too (L3421).
- Mechanisms, in order: `dl09.plate0/1` (`CarriedItem`; in the tray past `landing8`, or past `cage` with
  `persist.cw`: `CarriedItemParams.MovedWithFlag`), `dl09.tray` (`LoadPlate`), `dl09.cagePawl`, `dl09.cage`,
  `dl09.arc1/2` (`Hazards/LiveArc`, on the game clock). The tray's set-down is `Dl09TrayLoader` (an `IPlaceTarget`).
- Scene acts (motor gaps, #32): the cage act (`Dl09CageAct`: the prototype has him on the cage floor *as it was at the
  step's start*, `game.y = c.y` at #4, with no ride sync; `MotorSync`'s #9 snap would put him a step ahead), the long
  hopscotch (root motion), the city (`Dl09AweAct`: a yaw of its own, held on the `refuge` moment), the arcs' knock-back.
- Proven in the chapter replay (`Dl09ChapterProbe`, #20840–#25182, DL-10's first step, strict), and in its own window
  from a recorded rest (`Dl09TraceTests`, #20880–#25182), which localises a failure.
- Not ported: the den (a secret), the coin viewer and the hopscotch as curios, the tannoy, the camera.

## DL-07 as ported, and notes for DL-08

- DL-07 (`Dl07/`) has DL-06's span and adds `dl07.gallery` (`game.upper`, an `IEngageable` the lane's `GalleryLane`
  reads), `dl07.bucket` (fed from `dl06.line`'s log), `dl07.loading` (moves the weights as the prototype's receivers do,
  within the step: `CarriedItem.Take`), `dl07.gate`, `dl07.heapLetter`, `dl07.collapse`; the line's `Loader` is its
  interactable. Its rules (`Heap07`) extend `ReturnToSender06`. Scene acts: the parcel slide (`Dl07SlideAct`) and
  `Dl07LandingHopAct` (#32: the motor flies its alight hop where the prototype keeps him synced to the carrier).
- **DL-08 starts at `goods`** (#17677, region 4): DL-07's rules switch to region 4 and reach `goods` at the doorway
  (`REGION4_X`, L2044); with DL-08 in the chapter, `SceneAt` finds it there instead of the chapter's end. Its def adds
  region 4's lane table; its rules own the way back (`x < REGION4_X − 0.2` → region 3, L2045), where DL-07's rules
  hold him (the collapse's wall, L4181) and switch him to region 4 again past `REGION4_X`.
- `game.upper` stays true from `landing` until Attendance (`school`): read `dl07.gallery` (`IEngageable`) for it in
  region 4 (`floorCh1`'s counterweight, L4137) rather than adding another flag.
- The rows `goods`, `latched` and `tunnel` have no `y` but `c.upper`: they stand on the deck (1.6); set it when DL-08/09
  are ported (DL-07 set its own two).
- The collapse gives way at #17662 but hits (shake 0.6) at #17689 and is gone at 1.6 s, inside DL-08's window; it keeps
  stepping there (one graph), so DL-08's probe sees its cue.
- DL-07's trace fields are written on DL-08's first step too (#17677); DL-08's own fields end in 8.
- Not ported (other systems): picking up and posting the heap letter at MailSlot6 (letters, §4.26: like DL-02's tube
  letter, its fallen state comes back with a checkpoint's snapshot), the gallery clock's key (curios), the White's roll
  in the heap's sump (beings).

## DL-08 as ported (U-21), and notes for DL-09

- DL-08 (`Dl08/`, region 4, `REGION4_X` 80.75 to `CG.x0` 97.6): `dl08.trolley` (`PushableParams.Dl08Trolley`: its travel
  ends at the pan's buffer, or past it to the rail once `ExtendedBy` the pawl), `dl08.pan`, `dl08.pawl`, `dl08.platform`
  (never a ride: the shaft's floor is its top, `Dl08ShaftLane`), `dl08.belt`. The lane (`Dl08Lane`) adds the shaft's walls
  while the platform is down, the rail, the trolley's top, the crates, and the belt's carry (`LaneGeometry` is an
  `ILaneConveyor` over its region's contributors). Rules (`Handbrake08`, `Always`, guarded by region 4): Teeter
  (`Dl08TeeterAct`), Proud after the pawl, `latched`, careful by the sump (`Motor.Careful`), the sump's death
  (`Die(Grabbed, sink 0.8, hold 1.3)`), the way back into region 3. Scene act for #32: `Dl08BeltMantleAct` (the motor's
  climb cannot be carried along by the belt, L1942).
- The crates' draws: the prototype's come from the page's shared `Math.random`; the recorder finds each spawn's three LCG
  states (`rs8`) and `Dl08ChapterProbe` feeds them through `ReturnsBelt.Draws` (tests only), only while DL-08 holds him:
  the belt runs on behind him through DL-09, and once they are spent it draws its own again (no step it compares). Core's
  own runs use the belt's `SimRng`, reseeded on reset (a reload replays the same crates).
- **DL-09 starts at #20840** (x 97.616, region 4, checkpoint `latched`, the belt running with crates on it, the pawl set,
  the trolley by the rail): its X0 is `Dl08Lane.X1`; its table joins region 4's at that seam (the antechamber's ceiling,
  `ceilingCh1` L4166, and the cage's walls are DL-09's). Its rows: `cage` (y `CageTop`, set), `landing8` (y `Deck`, set),
  `tunnel` (no `y`, `c.upper`: set it to `Deck`). From `cage` the belt runs from the start (`RunningAfter`), and the
  trolley is parked at the rail.
- DL-08's rules keep running there: the belt and its crates are one graph's, and a climb started over the belt's end
  stays the belt-mantle act until it ends. `PlayerPose` has no mantle flag: the belt's trigger cannot see a climb (it
  needs a free step, L3416), harmless in DL-08's run.
- Not ported: the White in the sump (first sight, the scare and its knockback: beings), the idle look down the shaft
  (`PEEK_SPOTS`: no idle clock in Core), the camera's platform look.
