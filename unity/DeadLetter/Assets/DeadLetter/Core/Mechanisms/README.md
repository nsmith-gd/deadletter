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

**The class.** Derive from `Mechanism`, or from `StationMechanism` if D-17 uses it (it implements U-11's `IUsable`).
- `public XState State => (XState)StateCode;`. Change state only in `Step`, via `Enter(ctx, (int)XState.Y)` (logged
  once per change); one-shots (sounds, shakes, cues) via `Emit(ctx, (int)XEvent.Z, index, value)`.
- Interaction callbacks (`OnActFrame`, `Throw()`...) only record input; `Step` applies it. Stations keep a
  `private ActInput _act;`: `OnActFrame` calls `_act.Receive(f)` and returns "act over" from the frame alone;
  `Step` starts with `_act.Take()` and uses `_act.Started/Active/Frame/Time`.
- `Reset(in Checkpoint cp)`: derive everything from `cp.Past(_p.XAfter)` and from sources (already reset); `Init(...)`,
  not `Enter`. Clear pending input.
- Time: accumulate `ctx.Dt`; compare clip frames with `ClipClock.Reached/Crossed`, time thresholds with a 1e-9 slack.
- Per tick: no allocation, no LINQ, no lookups, no `Math.random` (use SimRng when it lands), no UnityEngine.

**Reading another mechanism.** Producers implement `ILoad`, `IPositionSource`, `IEngageable` (Signals.cs; document the
unit). Consumers resolve once in `Link`: `_src = link.Read<IPositionSource>(_p.Source);`. The graph steps in `Add`
order (the scene definition's order = the prototype's update order), and `Read` requires the source to be added
first, so it sees this tick's value. Use `link.ReadAnyOrder<T>` for reads from an act callback (acts run before the
graph) or to break a cycle with a one-tick lag (pawl ↔ platform: pawl first). `None` returns null (optional input).

**Snapshot.** `WriteFields`/`ReadFields`: every field that changes over time, including pending input and `_act`
(`_act.Write(w)`). Short, stable keys; the graph prefixes `id/`. Not params, not links. Restore then step must equal
the original run bit for bit (test it).

**Testing** (xUnit, `Mech` kit): every state transition; each event with its frame or time; every rule-table row
(name tests `What_Rule_L1234`); `Reset` for each relevant checkpoint (theory rows); restore mid-motion, then compare
`Mech.Dump(g)` every tick; one scene test per scene that uses the family with the real motor (see `Dl01SceneTests`).
`Mech.PlayAct(g, station)` plays a clip as the motor does (frames 0.4, 0.8, ... at 60 Hz).

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

**U-11 contract gaps** (worked around here): `IUsable.Profile` is read when Use starts, but the DL-08 pawl picks
LeverPull/LeverStuck at the end of step-in (L3305); a station cannot chain a follow-up clip (latch Pull → Flinch 1.6 s,
L1875); `IStation.Face` cannot face him toward the control from his side (DL-01 crank, L1835); reach is centred on
`StandX` (the DL-13 brake stands 0.2 off its reach centre: `Station.ReachX` widens `Reach` and tests in `IsAvailable`).
