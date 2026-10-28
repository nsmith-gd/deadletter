using System;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes.Attendance;

namespace DeadLetter.Core.Scenes.Dl16a
{
    /// <summary>
    /// DL-16a Her Way Round (port_architecture §5; docs/chapter1_expansion_build.md, the design review's redesign: no
    /// ballast): the servery. A gate keeps pupils on the floor; her way round was the dumbwaiter. He calls the car down from
    /// outside, steps in, rings the bell and rides it up to the passage over the gate, and walks down the stair to the
    /// workshop. Region 6 from 310 to DL-17 at 324 (<c>sceneName</c>, L8136). Lines are index.html at 7b3c123 (<c>ATT3</c>
    /// L5901–L5904, <c>resetAtt3</c> L5918–L5921, <c>nearAtt3Fixed</c> L5994–L5996, <c>updateAtt3Act</c> L6144–L6191,
    /// <c>updateAtt3</c> L6232–L6246, L6257).
    /// </summary>
    public static class Dl16aScene
    {
        public const string Id = "DL-16a";

        public const double X0 = 310, X1 = 324;

        /// <summary>The call push outside: within 0.24 of 312.42; he stands at 312.3 (L5996, L6004).</summary>
        public const double CallX = 312.42, CallReach = 0.24, CallStand = 312.3;
        /// <summary>The bell inside the car: 0.15 inside its ends, on its floor within 0.05 (L5995).</summary>
        public const double BellInset = 0.15, BellTolerance = 0.05;
        /// <summary>Riding, he stays 0.18 inside the car's ends (L6187).</summary>
        public const double RideInset = 0.18;
        /// <summary>The <c>kitchen</c> checkpoint between 310.4 and 314 (L6257).</summary>
        public const double KitchenX0 = 310.4, KitchenX1 = 314;

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "Her Way Round",
            X0 = X0, X1 = X1,
            Region = Dl16aLane.Region,                                                            // its checkpoint: kitchen
            // Step order = the prototype's updateAtt3 (#7, L6233–L6246): the car moves (on its load).
            Mechanisms = new[]
            {
                new MechanismDef("dl16a.tin1", () => new Dl16aTin("dl16a.tin1", inCarAfter: "workshop")),
                new MechanismDef("dl16a.tin2", () => new Dl16aTin("dl16a.tin2", inCarAfter: null)),
                new MechanismDef("dl16a.carLoad", () => new LoadPlate("dl16a.carLoad", LoadPlateParams.Dl16aCarLoad())),
                new MechanismDef("dl16a.car", () => new Dumbwaiter("dl16a.car", DumbwaiterParams.Dl16aCar())),
            },
            Lane = Dl16aLane.Table,
            LaneContributors = Dl16aLane.Contributors,
            Rules = () => new Dl16aRules(),
        };
    }

    /// <summary>
    /// One of the servery's tins (<c>f16a.tin1</c>, <c>tin2</c>, L5920): after the redesign nothing offers them to him
    /// (<c>nearAtt3Item</c> has no DL-16a items, L5983), so they only weigh in the car: tin 1 is in it from <c>workshop</c>.
    /// </summary>
    public sealed class Dl16aTin : Mechanism, IPlateBody
    {
        private readonly string _inCarAfter;
        private bool _inCar;

        public Dl16aTin(MechanismId id, string inCarAfter) : base(id) { _inCarAfter = inCarAfter; }

        public double X => 311.2;
        public double SupportX => X;
        public BodySupport Support => _inCar ? BodySupport.Placed : BodySupport.Floor;

        public override void Reset(in Checkpoint cp) { _inCar = cp.Past(_inCarAfter); Init(_inCar ? 1 : 0); }
        public override void Step(in StepContext ctx) { }
        protected override void WriteFields(ISnapshotWriter w) => w.WriteBool("inCar", _inCar);
        protected override void ReadFields(ISnapshotReader r) => _inCar = r.ReadBool("inCar");
    }

    /// <summary>
    /// DL-16a's rules: the call push and the bell (fixed controls, <c>nearAtt3Fixed</c> L5995–L5996: they give way to
    /// anything Use would lift), the car's ride (the bell act follows the car after it moves, <c>game.y = F.h</c>, L6246) and
    /// the <c>kitchen</c> checkpoint (L6257).
    /// </summary>
    public sealed class Dl16aRules : SceneRules
    {
        public static readonly CueId SoundBell = CueId.Of("sound:bell");
        private Dumbwaiter _car;
        private LoadPlate _load;

        public override bool Always => true;

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            _car = sim.Graph.Get<Dumbwaiter>("dl16a.car"); _load = sim.Graph.Get<LoadPlate>("dl16a.carLoad");
        }

        public override void BeforeMotor(ChapterSim sim, ref MotorInput input)
        {
            var m = sim.Motor;
            if (!input.UsePressed || m.IsActing || m.IsMantling || m.Ride != null || !m.Grounded || m.Hold != HoldKind.None || sim.Region != Dl16aLane.Region) return;
            var st = _car.State;
            if (st != DumbwaiterState.Top && st != DumbwaiterState.Bottom) return;
            double x = m.X, y = m.Y;
            SceneAct act = null;
            if (x > Dl16aLane.CarX0 + Dl16aScene.BellInset && x < Dl16aLane.CarX1 - Dl16aScene.BellInset && Math.Abs(y - _car.H) < Dl16aScene.BellTolerance)
                act = new BellAct(sim, _car, _load);                                                                              // L5995
            else if (y < 0.05 && Math.Abs(x - Dl16aScene.CallX) < Dl16aScene.CallReach) act = new CallAct(sim, _car);         // L5996
            if (act == null) return;
            if (m.PreviewUse(out var c) && c.Category < InteractionCategory.Fixed) return;                                     // an item answers first
            input = MotorInput.None;
            sim.StartAct(act);
        }

        public override void AfterGraph(ChapterSim sim)
        {
            if (sim.Act is BellAct bell) bell.Follow(_car.H);                                                                    // L6246
            if (sim.Region == Dl16aLane.Region && sim.X > Dl16aScene.KitchenX0 && sim.X < Dl16aScene.KitchenX1) sim.Checkpoints.Reach("kitchen");   // L6257
        }
    }

    /// <summary>The call push outside (<c>'att:call16a'</c>, L6025, L6144–L6148): to 312.3 facing +1, PressButtonHigh turned into the set; at 0.45 s the car is called; at 1.1 s he is done.</summary>
    public sealed class CallAct : AttAct
    {
        public static readonly ActId Call = ActId.Of("dl16a.callPush"), Press = ActId.Of("PressButtonHigh");
        private readonly Dumbwaiter _car;
        private bool _done;

        public CallAct(ChapterSim sim, Dumbwaiter car) : base(sim, Call, Dl16aScene.CallStand, 1) { _car = car; }

        protected override void OnArrive() { FaceSet(Math.PI); Phase = Press; }

        protected override bool OnClip(double dt)
        {
            if (T > 0.45 && !_done) { _done = true; _car.Call(); }
            return !(T > 1.1);
        }
    }

    /// <summary>
    /// The bell inside the car, and the ride (<c>'att:bell16a'</c>, <c>'ride16a'</c>, L6162–L6191): no approach; he turns into
    /// the set and presses it (PressButtonHigh); at 0.55 s it rings, and the car goes by its load (from the top, down; the
    /// right load, up; too light, it shoots; too heavy, it buzzes and stays). If it moves with him in it, he rides from that
    /// step, turned back to the lane: held 0.18 inside the car's ends on its floor, until it stops (at the top he faces +1).
    /// Otherwise he is done at 1.1 s (riding then if it is moving with him on its floor).
    /// <para>The prototype decides the car's move inside the act (#4); the car here decides at its own step after, so the
    /// act asks the same question of the car's load to know at once whether he rides.</para>
    /// </summary>
    public sealed class BellAct : AttAct
    {
        public static readonly ActId Bell = ActId.Of("dl16a.car"), Press = ActId.Of("PressButtonHigh"), Ride = ActId.Of("Ride");
        private readonly Dumbwaiter _car;
        private readonly LoadPlate _load;
        private bool _rang, _riding;

        public BellAct(ChapterSim sim, Dumbwaiter car, LoadPlate load) : base(sim, Bell, double.NaN, 0) { _car = car; _load = load; Phase = Press; }

        protected override void OnArrive() { }

        protected override bool OnClip(double dt)
        {
            if (_riding)                                                                                                      // L6185–L6190
            {
                X = Smooth.Clamp(X, Dl16aLane.CarX0 + Dl16aScene.RideInset, Dl16aLane.CarX1 - Dl16aScene.RideInset);
                Y = _car.H;
                var st = _car.State;
                if (st == DumbwaiterState.Top || st == DumbwaiterState.Bottom) { if (st == DumbwaiterState.Top) Facing = 1; return false; }
                return true;
            }
            if (T < 0.02) FaceSet(Math.PI);                                                                                   // L6166
            if (T > 0.55 && !_rang)                                                                                           // L6167–L6178
            {
                _rang = true;
                bool top = _car.State == DumbwaiterState.Top;
                _car.Bell();
                bool moves = top || !(_load.Load > LoadPlateParams.Dl16aNeed);                                                // down, rise or shoot
                if (moves && InCar(X)) { _riding = true; T = 0; FaceLane(); Phase = Ride; return true; }
            }
            if (T > 1.1)                                                                                                      // L6180–L6183
            {
                FaceLane();
                if (_car.Moving && Math.Abs(Y - _car.H) < 0.1 && InCar(X)) { _riding = true; T = 0; Phase = Ride; return true; }
                return false;
            }
            return true;
        }

        /// <summary>After the car moved this step (#7): he is on its floor (<c>game.y = F.h</c>, L6246).</summary>
        public void Follow(double h) { if (_riding) Y = h; }

        private static bool InCar(double x) => x >= Dl16aLane.CarX0 && x <= Dl16aLane.CarX1;                                   // inBox(game.x, ATT3.car)
    }
}
