# Core/Mechanisms: patterns for the mechanism families (U-10)

Spec: `docs/unity/port_architecture.md` §4.13 (rules and IDs), §4.28 (reset is derived), §3.1 (step order).
Reference family: `Catches/` (Latch, Pawl, CageCatch, CycleBrake), `Actuators/` (FollowerActuator, CrankActuator,
Door), `Drives/PulseSequencer`. Copy them; touch the framework files only through a reviewed change.

**Layout.** One class per mechanism *type*, in the §2 folder (`Plates/`, `Lifts/`, `Drives/`, `Routes/`, `Water/`,
`Cycles/`), namespace `DeadLetter.Core.Mechanisms.<Folder>`. A file holds, in order: `enum XState`, `enum XEvent`,
`sealed class XParams`, `sealed class X`. Tests: `unity/core-tests/<Family>Tests.cs`, using `MechanismTestKit.cs`.

**Params.** Public fields whose defaults are the prototype's constants, plus one static factory per instance, named
after its §5 ID (`LatchParams.Dl01Latch()`), with resolved values (`OFF3 + 52.45` → `85.45`), Unity z (three z negated),
and an `L` citation per value. Inputs are `MechanismId` fields; the "solved" flag is a checkpoint name
(`ReleasedAfter = "shutter"`). Instance quirks are params (`CountTriggerStep`, `CancelAfter`), never subclasses.

**The class.** Derive from `Mechanism`, or from `StationMechanism` if D-17 uses it (it implements `IUsable`).
- `public XState State => (XState)StateCode;`. Change state only in `Step`, via `Enter(ctx, (int)XState.Y)` (logged
  once per change); one-shots (sounds, shakes, cues) via `Emit(ctx, (int)XEvent.Z, index, value)`.
- Interaction callbacks (`OnActFrame`, `OnLifted`, `Throw()`...) only record input; `Step` applies it. Stations keep a
  `private ActInput _act;`: `OnActFrame` calls `_act.Receive(f)` and answers an `ActStep` from the frame alone
  (`Continue`, `Done`, `Then(clip, fade)` for a follow-up clip, `HopBy(dx)`/`HopTo(x, y, z)` for a hop the motor plays);
  `Step` starts with `_act.Take()` and uses `_act.Started/Active/Frame/Time/Part` (frames restart in each `Part`).
- **The station contract** (#22). The resolver asks `Offer(in InteractionQuery q, out StationPose pose)`: the station
  says whether it answers from his pose (reach, floor, state) and where he stands (`StandX`, `StandZ`), which way he
  faces (`Face`: fixed, 0 = keep his, or toward it from his side with `Station(faceTowards: true)`, the DL-01 crank) and
  where it is (`AnchorX`). A `Station`'s reach may be centred off its stand point (`reachX`, the DL-13 brake). The
  motor asks `ProfileFor(q)` when Use starts (turn, crouch) and again once he has stepped in (the clip: the DL-08 pawl
  picks LeverPull/LeverStuck there, L3305); `ActFrame.Clip` tells the station which one it got.
- `Reset(in Checkpoint cp)`: derive everything from `cp.Past(_p.XAfter)` and from sources (already reset); `Init(...)`,
  not `Enter`. Clear pending input.
- Time: accumulate `ctx.Dt`; compare clip frames with `ClipClock.Reached/Crossed`, time thresholds with a 1e-9 slack.
  Exception: a clock the prototype itself sums from 0 a step at a time (`c.t += dt`) and compares raw (`c.t > 1.0`) is
  the same double here: compare it raw too. Sixty steps of 1/60 sum to 1.0000000000000013, so with the slack the
  threshold passes a step late (`SlippingCage`, found by the DL-09 trace at #22003; U-21). So is a clock the prototype
  takes as a difference of game clocks (`game.clock − since > d`, the cue's `momentTime`): `RelocationLift` compares raw,
  and a timed `Door` judges its delay on the bound game clock (`Door.BindClock`; DL-10's gate, #26061–#26062).
- Per tick: no allocation, no LINQ, no lookups, no UnityEngine. Randomness: a `SimRng` field (`Core/Simulation`),
  `SimRng.Xorshift(_p.Seed)`; `Reseed` in `Reset`, `_rng.Write(w, "rng")` in the snapshot; `_rng.Chance(dt * rate)`
  for the prototype's `Math.random() < dt · rate`.

**Reading another mechanism.** Producers implement a signal from Signals.cs (list below; document the unit). Consumers resolve once in `Link`: `_src = link.Read<IPositionSource>(_p.Source);`. The graph steps in `Add`
order (the scene definition's order = the prototype's update order), and `Read` requires the source to be added
first, so it sees this tick's value. Use `link.ReadAnyOrder<T>` for reads from an act callback (acts run before the
graph) or to break a cycle with a one-tick lag (pawl ↔ platform: pawl first). `None` returns null (optional input).

**Shared signals** (`Signals.cs`, namespace `DeadLetter.Core.Mechanisms`): `ILoad` (load shares), `IPositionSource`
(per producer), `IEngageable`; `IPlateBody` + `BodySupport` (items and pushables a plate weighs); `ILiftRide` (floor y,
its velocity, Carrying: ride sync #9, `MotorSync`, snaps him to every carrying lift in the graph); `ISweptVolume` +
`SweptBox` (space a folding leaf sweeps; `Folding/SweptVolumeProbe` answers the lane's surface and ceiling probes for
it). Contracts with the motor are in `Interaction/Contracts.cs`: `IRide` (carriers: `CarrierLine.Rider`), `IEscort`
(the escort trolley), `IHideSpot` (`Beings/HideSpot`), `IPlaceTarget` (`CarrierLine.Loader`).

**Persist flags** (U-14, §4.28): story state that outlives a reload (`StoryFlags`: the DL-17 drawer read, letters,
curios...) lives in `MechanismGraph.Flags`. A mechanism that depends on one resolves it once in `Link`
(`_h = link.Flags.Resolve(_p.RequiresFlag)`) and reads `link.Flags.Get(_h)` in Reset/Step (see `Door.RequiresFlag`).
State a mechanism keeps itself (`WhiteBrain.Warned`) is joined by `CheckpointService.BindFlag`, not read from here.

**D-17's pose** (`StepContext.Player`, built from the motor after #4 by `PlayerPose.Of(motor)`, the one way to fill
it: a scene simulator, Runtime's `D17Controller`, tests' `Mech.Pose(motor)`): x, y, z, `Vx`, `Crouched`, `Busy` (in an act),
`Grounded`, `Holding` (`Hold != None`), `Hiding` (the hide act), `Escorted` (the escorted act). Rules that need his
footing or hands read it here, never through a side call. World state (alive, region, upper) stays in
`Beings/BeingSenses`.

**Snapshot.** `WriteFields`/`ReadFields`: every field that changes over time, including pending input and `_act`
(`_act.Write(w)`). Short, stable keys; the graph prefixes `id/`. Not params, not links. Restore then step must equal
the original run bit for bit (test it).

**Testing** (xUnit, `Mech` kit): every state transition; each event with its frame or time; every rule-table row
(name tests `What_Rule_L1234`); `Reset` for each relevant checkpoint (theory rows); restore mid-motion, then compare
`Mech.Dump(g)` every tick; one scene test per scene that uses the family with the real motor (see `Dl01SceneTests`).
`Mech.PlayAct(g, station)` plays a clip as the motor does (frames 0.4, 0.8, ... at 60 Hz).

**Family index** (folder → classes → §4.13 → scenes with an ID in §5):

| Folder | Classes | § | Scenes |
|---|---|---|---|
| `Plates/` | LoadPlate, PlateSensor, WeighScale, PlateDoor, PresenceStrip, SeatRow, PlateOutputs | a | DL-01/03/04/05/08/09/10/12/15/16a |
| `Docks/` | Cradle, Rack, RailDetents | b | DL-04, 15, 16 |
| `Catches/` | Latch, Pawl, CageCatch, CycleBrake | c | DL-01, 08, 09, 13, 16 |
| `Actuators/` | Door, FollowerActuator, CrankActuator | d (a) | DL-01, 03, 10, 11, 12, 14a, 15, 17 |
| `Drives/` | PulseSequencer, WindCrank, PairedBlindDrive | e, g | DL-01, 14, 14a, 17 |
| `Lifts/` | Lift (base), CounterweightLift, SlippingCage, RelocationLift, CallButton, PupilLift, CounterweightRack, Dumbwaiter | f | DL-08, 09, 10, 15, 16, 16a |
| `Routes/` | CarrierLine (incl. the `dl06.dock`), PointsLever, ReturnsBelt, RoutePath | h | DL-06/07, 08 |
| `Water/` | Flood, Sluice, SluiceValve, SluiceRig, FloatLatch (`dl17.latch`) | i (c) | DL-11, 17 |
| `Bridges/` | TippingBridge | j | DL-01, 11 |
| `Cycles/` | CycleClock, CycleTimeline | k | DL-13, 14a, 21, 23 |
| `Folding/` | FoldingLeaf, LeafBox, SweptVolumeProbe | (DL-18 spec) | DL-18 |
| `../Beings/` | WhiteBrain, EscortTrolley, HideSpot, NoiseBus, BeingSenses | §4.15, §4.16 | DL-06/07, 11, 14b |

Scene tests with the real motor: `Dl01`, `Dl03`, `Dl09`, `Dl11White`, `Dl14`, `Dl17`, `Dl18SceneTests`; the acts and
contracts above: `MotorActTests`, `RideAndLaneTests`. Loose items and pushables are the scene layer's (`Core/Carry`,
`Core/Push`), not a family here.

**Citing index.html.** Never open it whole: `sed -n '3290,3324p' game/undelivered/index.html`. XML summary cites the
ranges; ported lines carry `// L1874`. Deliberate deviations say so (see `CrankActuator.WheelDeg`).

**Worked example** (a bell that rings once when a load arrives):
```csharp
public enum BellState { Quiet, Rung }
public enum BellEvent { Ring }
public sealed class BellParams { public MechanismId Source; public double Threshold = 0.05; public string RungAfter; }
public sealed class Bell : Mechanism
{
    private readonly BellParams _p; private ILoad _src;
    public Bell(MechanismId id, BellParams p) : base(id) { _p = p; }
    public BellState State => (BellState)StateCode;
    public override void Link(MechanismLinker link) => _src = link.Read<ILoad>(_p.Source);
    public override void Reset(in Checkpoint cp) => Init((int)(cp.Past(_p.RungAfter) ? BellState.Rung : BellState.Quiet));
    public override void Step(in StepContext ctx)
    {
        if (State == BellState.Quiet && _src.Load >= _p.Threshold) { Enter(ctx, (int)BellState.Rung); Emit(ctx, (int)BellEvent.Ring); }
    }
    protected override void WriteFields(ISnapshotWriter w) { }   // the state is written by the base
    protected override void ReadFields(ISnapshotReader r) { }
}
// var g = Mech.Graph("start", new TestSource("t.plate"), new Bell("t.bell", new BellParams { Source = "t.plate" }));
```

**Acts and holds the motor owns** (#22, U-11b): the latch's Flinch is a chained clip (`Then`), DL-18's strap a chained
hop (`HopBy`); boarding/riding/alighting a carrier is `IRide` (ride sync is the motor's `SyncRide`, called at #9 by
`MotorSync`); the escorted walk is the motor's act (`IEscort.WantsEscort` → `D17Motor.BeginEscort`; the trolley
follows `PlayerPose.X` and stops when `Escorted` ends); the hide act is `IHideSpot`; a pushable's push acceleration is
its own (`IPushable.Accel`) and whether he lets go at Max (`LetGoAtMax`). A mechanism that strands or kills him emits
an event and the scene rule calls `D17Motor.BeginStuck()`/`Die(kind)`; the motor's act asks for the respawn
(`MotorEvents.RespawnDue`). The call order for a scene simulator is in `Core/Motor/README.md`.
