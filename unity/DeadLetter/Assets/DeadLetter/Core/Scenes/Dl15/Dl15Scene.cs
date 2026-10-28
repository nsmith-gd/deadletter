using System;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Scenes.Dl15
{
    /// <summary>
    /// DL-15 One Pupil Missing (port_architecture §5; docs/chapter1_part2_plan.md, rev 0.3): in from the sick bay's balcony;
    /// a class of three kept ready. The two stand-in pupils run on one floor rail with a detent at each friend's place (and
    /// at the lift); the pupil lift takes a pupil down only with an escort (him) aboard; Mara's place is an ordinary chair
    /// off the rail, with a seat plate: after the stand-ins the third place is his. All three lit for 1.6 s: dismissal, the
    /// class door opens, and the figures leave in procession (DL-16's). Region 6 from 278 to DL-16 at 294 (<c>sceneName</c>,
    /// L8136). Lines are index.html at 7b3c123 (<c>ATT2</c> L5517–L5532, <c>resetAtt2</c> L5538–L5554,
    /// <c>figRange15</c>/<c>pushable15</c> L5556–L5585, <c>nearAtt2Fixed</c> L5620–L5624, <c>updateAtt2Act</c> L5655–L5684,
    /// <c>updateAtt2</c> L5709–L5736, L5795–L5803).
    /// </summary>
    public static class Dl15Scene
    {
        public const string Id = "DL-15";

        public const double X0 = 278, X1 = 294;

        /// <summary><c>ATT2.chair</c> (L5523): Mara's chair, 0.3 into the set (Unity +); free of the figures within 0.3 (L5622).</summary>
        public const double ChairX = 286.0, ChairZ = 0.3, ChairReach = 0.25, ChairClear = 0.3;
        /// <summary>The checkpoints: <c>sickbay</c> up on the balcony past <c>wall15.x1 + 0.15</c> (L6256); <c>class6</c> on the floor past the lift (L5800).</summary>
        public const double SickbayAt = Dl14bLane.Wall15X1 + 0.15, SickbayY = 1.5, Class6At = Dl15Lane.LiftX1 + 0.2, Class6Before = 293;

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "One Pupil Missing",
            X0 = X0, X1 = X1,
            Region = Dl15Lane.Region,                                                             // its checkpoints: sickbay, class6, dismissed
            // Step order = the prototype's updateAtt2 (#7, L5711–L5736): the figures ride the lift as it was, the lift moves,
            // the seats light and dismiss, the class door opens. The procession and the rack are DL-16's.
            Mechanisms = new[]
            {
                new MechanismDef("dl15.figA", () => new Dl15Figure("dl15.figA", Dl15Figure.Kind.A)),
                new MechanismDef("dl15.figB", () => new Dl15Figure("dl15.figB", Dl15Figure.Kind.B)),
                new MechanismDef("dl15.pupil", () => new Dl15LiftReader("dl15.pupil", occupied: false)),
                new MechanismDef("dl15.occupied", () => new Dl15LiftReader("dl15.occupied", occupied: true)),
                new MechanismDef("dl15.lift", () => new PupilLift("dl15.lift", LiftParams())),
                new MechanismDef("dl15.chair", () => new Dl15Chair("dl15.chair")),
                new MechanismDef("dl15.seats", () => new SeatRow("dl15.seats", SeatRowParams.Dl15Seats())),
                new MechanismDef("dl15.classDoor", () => new Door("dl15.classDoor", DoorParams.Dl15ClassDoor())),
            },
            Interactables = g => new IInteractable[]
            {
                new Dl15FigureFace(g.Get<Dl15Figure>("dl15.figA"), +1), new Dl15FigureFace(g.Get<Dl15Figure>("dl15.figA"), -1),   // f15A, f15Ar
                new Dl15FigureFace(g.Get<Dl15Figure>("dl15.figB"), +1), new Dl15FigureFace(g.Get<Dl15Figure>("dl15.figB"), -1),   // f15B, f15Br
            },
            Lane = Dl15Lane.Table,
            LaneContributors = Dl15Lane.Contributors,
            Rules = () => new Dl15Rules(),
        };

        /// <summary><see cref="PupilLiftParams.Dl15Lift"/> with its pupil and its occupant (the figures, <c>pupil</c>/<c>occupied</c>, L5714, L5719).</summary>
        public static PupilLiftParams LiftParams()
        {
            var p = PupilLiftParams.Dl15Lift();
            p.Pupil = "dl15.pupil"; p.Occupied = "dl15.occupied";
            return p;
        }
    }

    /// <summary>
    /// One of DL-15's two stand-in pupils (<c>f15.A</c>/<c>f15.B</c>, L5539–L5545): free on the rail, where he pushes it
    /// either way (<see cref="Dl15FigureFace"/>, <c>pushable15</c>, L5579–L5585) between the detents (the lift's middle and
    /// the friends' two places, <c>ATT2_DETENTS</c>) within <c>figRange15</c> (L5558–L5577); on the lift's deck it rides it
    /// (<c>f.base = f15.lift</c>, L5713). Dismissed, it is DL-16's procession's (<see cref="State"/> Procession), then the
    /// rack's (Stored). B starts on the balcony (1.6), A in the room.
    /// </summary>
    public sealed class Dl15Figure : Mechanism, IPlateBody, IPositionSource
    {
        public enum Kind { A, B }

        /// <summary><c>ATT2</c> (L5521–L5527): the stub and the buffer the rail runs between, the figures' half-length and gap, their starts.</summary>
        public const double Stub0 = 278.62, Buffer = 293.0, Half = 0.22, FigGap = 0.5, A0 = 289.2, B0 = 279.9, RailZ = 0.55;
        /// <summary>Dismissed, the rail runs on to 344 (L5562, L5565); the procession's places at reset (L5541–L5542).</summary>
        public const double RailEnd = 344, Edge = 297.62, RackIn = 305.6;
        /// <summary>The detents (<c>ATT2_DETENTS</c>: the lift's middle, the friends' places, L5534).</summary>
        public static readonly double[] Detents = { Dl15Lane.LiftMid, 283.2, 284.6 };

        public enum FigureState { Free, Procession, Stored }

        private readonly Kind _kind;
        private Dl15Figure _other;
        private PupilLift _lift;
        private IEngageable _dismissed;
        private bool _held;
        private double _from;

        public Dl15Figure(MechanismId id, Kind kind) : base(id) { _kind = kind; }

        public FigureState State { get; private set; }
        public double X { get; private set; }
        /// <summary>The height it stands at (<c>f.base</c>): the floor, the balcony, or the lift's deck.</summary>
        public double Base { get; private set; }
        /// <summary>Its bow, 0..1 (<c>f.lean</c>).</summary>
        public double Lean { get; private set; }
        public double Velocity { get; private set; }
        public double Position => X;
        public double SupportX => X;
        /// <summary>Stored: placed (the rack counts it; no seat does). Otherwise on the floor, or carried by the balcony or the lift.</summary>
        public BodySupport Support => State == FigureState.Stored ? BodySupport.Placed : Base < 0.05 ? BodySupport.Floor : BodySupport.Carrier;

        /// <summary>On the lift's deck: at its middle within 0.05 (<c>onLift15</c>, L5556).</summary>
        public bool OnLift => Math.Abs(X - Dl15Lane.LiftMid) < 0.05;
        /// <summary>The class is dismissed (DL-15's seat row).</summary>
        public bool Dismissed => _dismissed.Engaged;
        /// <summary>He can take hold of it (<c>avail</c>, L5583): free, the class not dismissed, the lift still.</summary>
        public bool Pushable => State == FigureState.Free && !Dismissed && Math.Abs(_lift.FloorVelocity) < 1e-3;

        public override void Link(MechanismLinker link)
        {
            _other = link.ReadAnyOrder<Dl15Figure>(_kind == Kind.A ? "dl15.figB" : "dl15.figA");
            _lift = link.ReadAnyOrder<PupilLift>("dl15.lift");
            _dismissed = link.ReadAnyOrder<IEngageable>("dl15.seats");
        }

        public override void Reset(in Checkpoint cp)
        {
            bool dismissed = cp.Past("dismissed"), stored = cp.Past("store"), down = cp.Past("class6");     // L5539
            if (_kind == Kind.A) { X = stored ? RackIn : dismissed ? Edge - 0.8 : A0; Base = 0; }              // L5541
            else { X = stored ? RackIn : dismissed ? Edge : down ? Dl15Lane.LiftMid : B0; Base = stored || dismissed || down ? 0 : Dl15Lane.BalconyH; }   // L5542
            State = stored ? FigureState.Stored : dismissed ? FigureState.Procession : FigureState.Free;         // L5547–L5550
            Lean = 0; Velocity = 0; _held = false;
            Init((int)State);
        }

        /// <summary>Riding the lift (L5713): free, on its deck, at the lift's height before it moves this step.</summary>
        public override void Step(in StepContext ctx)
        {
            if (State == FigureState.Free && X >= Dl15Lane.LiftX0 && X <= Dl15Lane.LiftX1 + 0.3 && OnLift) Base = _lift.Y;
            Enter(ctx, (int)State);
        }

        // ---- The push (its faces call these) ------------------------------------------------------------------------
        internal void Range(out double lo, out double hi)
        {
            double top = Dl15Lane.LiftTop, lift = _lift.Y;
            bool dismissed = Dismissed;
            if (OnLift)                                                                                         // L5560–L5564
            {
                if (lift > top - 0.02) { lo = Stub0; hi = Dl15Lane.LiftMid; }
                else if (lift < 0.02) { lo = Dl15Lane.LiftMid; hi = dismissed ? RailEnd : Buffer; }
                else { lo = hi = X; }
            }
            else if (Base > 1) { lo = Stub0; hi = lift > top - 0.02 ? Dl15Lane.LiftMid : Dl15Lane.BalconyX1 - Half; }   // L5565
            else { lo = lift < 0.02 ? Dl15Lane.LiftMid : Dl15Lane.LiftX1 + Half; hi = dismissed ? RailEnd : Buffer; }    // L5566
            var o = _other;
            if (o != null && o.State == FigureState.Free && Math.Abs(o.Base - Base) < 0.05)                    // L5567–L5569
            {
                if (o.X > X) hi = Math.Min(hi, o.X - FigGap); else lo = Math.Max(lo, o.X + FigGap);
            }
            double from = _held ? _from : X;                                                                    // L5571
            for (int i = 0; i < Detents.Length; i++) if (Detents[i] > from + 0.02) { hi = Math.Min(hi, Detents[i]); break; }
            for (int i = Detents.Length - 1; i >= 0; i--) if (Detents[i] < from - 0.02) { lo = Math.Max(lo, Detents[i]); break; }
            if (hi < lo) hi = lo;                                                                               // [lo, max(lo, hi)], L5576
        }

        internal void MoveTo(double x, double velocity)
        {
            if (!_held) { _held = true; _from = X; }                                                            // game.pushFrom
            X = x; Velocity = velocity;
        }

        internal void Release() => _held = false;

        // ---- The procession and the rack (DL-16's) -----------------------------------------------------------------
        /// <summary>Dismissed: it leaves with the class (L5731).</summary>
        public void BeginProcession() { State = FigureState.Procession; _held = false; }
        /// <summary>It bows a little more (<c>f.lean = min(1, f.lean + dt)</c>, L5745).</summary>
        public void Bow(double dt) => Lean = Math.Min(1, Lean + dt);
        /// <summary>Rolled on along the rail (L5750–L5751).</summary>
        public void Roll(double x, double velocity) { X = x; Velocity = velocity; }
        /// <summary>Into the rack (L5753–L5754).</summary>
        public void Store() => State = FigureState.Stored;

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteLong("state", (int)State); w.WriteDouble("x", X); w.WriteDouble("base", Base); w.WriteDouble("lean", Lean);
            w.WriteDouble("v", Velocity); w.WriteBool("held", _held); w.WriteDouble("from", _from);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            State = (FigureState)r.ReadLong("state"); X = r.ReadDouble("x"); Base = r.ReadDouble("base"); Lean = r.ReadDouble("lean");
            Velocity = r.ReadDouble("v"); _held = r.ReadBool("held"); _from = r.ReadDouble("from");
        }
    }

    /// <summary>A face of a DL-15 figure he pushes it by (<c>f15A</c>/<c>f15Ar</c>/<c>f15B</c>/<c>f15Br</c>, L5579–L5585): gap 0.6, 0.35 m/s, from 0.55 into the set, detents.</summary>
    public sealed class Dl15FigureFace : IPushable
    {
        public Dl15FigureFace(Dl15Figure of, int side)
        {
            Base = of ?? throw new ArgumentNullException(nameof(of));
            if (side != 1 && side != -1) throw new ArgumentOutOfRangeException(nameof(side));
            Side = side;
        }

        public Dl15Figure Base { get; }
        public InteractionCategory Category => InteractionCategory.Push;
        public bool IsAvailable(in InteractionQuery q) => Base.Pushable;
        public double X => Base.X;
        public int Side { get; }
        public double Gap => 0.6;
        public double Speed => 0.35;
        public double Accel => 1.4;
        public double Min { get { Base.Range(out double lo, out _); return lo; } }
        public double Max { get { Base.Range(out _, out double hi); return hi; } }
        public double FloorY => Base.Base;
        public double Z => Dl15Figure.RailZ;
        public double ForwardReach => 0.34;
        public double BackReach => 0.34;
        public bool TipsIntoPit => false;
        public bool HasDetents => true;
        public bool LetGoAtMax => false;
        public void MoveTo(double x, double velocity) => Base.MoveTo(x, velocity);
        public void SetAtLip(bool atLip) { }
        public void OnReleased(bool atLip) => Base.Release();
        public void OnShoved() { }
        public void OnTravelEnd() { }
    }

    /// <summary>
    /// What the pupil lift reads of the figures (L5714, L5719): a pupil free on its deck at its height (<c>pupil</c>), or a
    /// figure still partly over the deck at its height (<c>occupied</c>). Stateless: read when the lift steps.
    /// </summary>
    public sealed class Dl15LiftReader : Mechanism, IEngageable
    {
        private readonly bool _occupied;
        private Dl15Figure _a, _b;
        private PupilLift _lift;

        public Dl15LiftReader(MechanismId id, bool occupied) : base(id) { _occupied = occupied; }

        public bool Engaged => On(_a) || On(_b);

        private bool On(Dl15Figure f)
        {
            if (f.State != Dl15Figure.FigureState.Free || !(Math.Abs(f.Base - _lift.Y) < 0.05)) return false;
            return _occupied ? Math.Abs(f.X - Dl15Lane.LiftMid) < (Dl15Lane.LiftX1 - Dl15Lane.LiftX0) / 2 + Dl15Figure.Half : f.OnLift;
        }

        public override void Link(MechanismLinker link)
        {
            _a = link.Read<Dl15Figure>("dl15.figA"); _b = link.Read<Dl15Figure>("dl15.figB");
            _lift = link.ReadAnyOrder<PupilLift>("dl15.lift");
        }

        public override void Reset(in Checkpoint cp) => Init(0);
        public override void Step(in StepContext ctx) { }
        protected override void WriteFields(ISnapshotWriter w) { }
        protected override void ReadFields(ISnapshotReader r) { }
    }

    /// <summary>
    /// Mara's chair (<c>'att:sit'</c>, L5622–L5624, L5655–L5684): on the floor within 0.25 of it, the class not yet dismissed
    /// and no figure on the floor within 0.3 of it, he sits (the motor's sit: 0.3 into the set, facing +1). Engaged while he
    /// is seated (the seat row's last lamp).
    /// </summary>
    public sealed class Dl15Chair : Mechanism, ISeat, IEngageable
    {
        private Dl15Figure _a, _b;
        private IEngageable _dismissed;
        private bool _seated;

        public Dl15Chair(MechanismId id) : base(id) { }

        public InteractionCategory Category => InteractionCategory.Fixed;
        public bool Engaged => _seated;

        public bool Offer(in InteractionQuery q, out StationPose pose)
        {
            pose = default;
            if (q.Y > 0.05 || _dismissed.Engaged || Near(_a) || Near(_b) || !(Math.Abs(q.X - Dl15Scene.ChairX) < Dl15Scene.ChairReach)) return false;
            pose = new StationPose(Dl15Scene.ChairX, 1, Dl15Scene.ChairZ, Dl15Scene.ChairX);
            return true;
        }

        private static bool Near(Dl15Figure f) => f.Base < 0.05 && Math.Abs(f.X - Dl15Scene.ChairX) < Dl15Scene.ChairClear;   // L5623

        public bool IsAvailable(in InteractionQuery q) => Offer(q, out _);
        public void OnSeated(bool seated) => _seated = seated;

        public override void Link(MechanismLinker link)
        {
            _a = link.Read<Dl15Figure>("dl15.figA"); _b = link.Read<Dl15Figure>("dl15.figB");
            _dismissed = link.ReadAnyOrder<IEngageable>("dl15.seats");
        }

        public override void Reset(in Checkpoint cp) { _seated = false; Init(0); }
        public override void Step(in StepContext ctx) => Enter(ctx, _seated ? 1 : 0);
        protected override void WriteFields(ISnapshotWriter w) => w.WriteBool("seated", _seated);
        protected override void ReadFields(ISnapshotReader r) => _seated = r.ReadBool("seated");
    }

    /// <summary>
    /// DL-15's rules: the checkpoints <c>sickbay</c> (L6256), <c>class6</c> (L5800) and <c>dismissed</c> (the dismissal,
    /// L5731), the dismissal's bell and the <c>child</c> cue (L5731–L5733). <see cref="Always"/>: <c>sickbay</c> is reached up
    /// on the balcony from DL-14b's landing side of the seam.
    /// </summary>
    public sealed class Dl15Rules : SceneRules
    {
        public static readonly CueId MusicChild = CueId.Of("music:child"), SoundBell = CueId.Of("sound:bell");
        private static readonly MechanismId SeatsId = "dl15.seats";

        public override bool Always => true;

        public override void AfterGraph(ChapterSim sim)
        {
            if (sim.Graph.Log.Has(SeatsId, MechanismEventKind.State, (int)SeatRowState.Dismissed))
            {
                sim.Checkpoints.Reach("dismissed");                                                            // L5731
                sim.Cue(SoundBell); sim.Cue(MusicChild);
            }
            if (sim.Region != Dl15Lane.Region) return;
            double x = sim.X, y = sim.Y;
            var cp = sim.Checkpoints.Current;
            if (x > Dl15Scene.Class6At && y < 0.05 && x < Dl15Scene.Class6Before && cp.Past("sickbay")) sim.Checkpoints.Reach("class6");   // L5800
            if (x > Dl15Scene.SickbayAt && y > Dl15Scene.SickbayY) sim.Checkpoints.Reach("sickbay");                                         // L6256
        }
    }
}
