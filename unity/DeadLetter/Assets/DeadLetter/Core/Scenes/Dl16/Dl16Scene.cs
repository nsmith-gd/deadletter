using System;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes.Dl15;

namespace DeadLetter.Core.Scenes.Dl16
{
    /// <summary>
    /// DL-16 After the Bell (port_architecture §5; docs/chapter1_part2_plan.md, rev 0.3): dismissed, the two figures bow, then
    /// roll off along the rail, out under the flap, to the well. The bridge over it goes down only while he holds the lever
    /// (a figure on it holds it down too); the figures cross and roll on into the storage rack, which takes them onto its
    /// hooks; full, its latch drops and its counterweight lifts out of the lane. The first time he comes up behind the
    /// waiting figures he lets them go first. Region 6 from 294 to DL-16a at 310 (<c>sceneName</c>, L8136). Lines are
    /// index.html at 7b3c123 (<c>ATT2</c> L5525–L5528, <c>resetAtt2</c> L5551, <c>nearAtt2Fixed</c> L5625,
    /// <c>updateAtt2Act</c> L5685–L5694, <c>updateAtt2</c> L5738–L5770, L5796–L5804).
    /// </summary>
    public static class Dl16Scene
    {
        public const string Id = "DL-16";

        public const double X0 = 294, X1 = 310;

        /// <summary><c>ATT2.lever</c> (L5526): stand 0.25 short of it, within 0.3 (L5625, L5630).</summary>
        public const double LeverX = 296.0, LeverStand = LeverX - 0.25, LeverReach = 0.3;
        /// <summary>His courtesy, past 294.6 and short of <c>lever + 0.4</c> (L5768).</summary>
        public const double BowX0 = 294.6, BowX1 = LeverX + 0.4;
        /// <summary>The checkpoints: <c>crossing</c> past 295 once dismissed (L5801), <c>store</c> past <c>pit.x1 + 0.4</c> once latched (L5802).</summary>
        public const double CrossingAt = 295.0, StoreAt = Dl16Lane.PitX1 + 0.4;
        /// <summary>Down the well (y &lt; −1): back to the checkpoint after 1.3 s, no death (<c>respawn</c>, L2997–L3000, L5797).</summary>
        public const double FellBelow = -1.0, RespawnDelay = 1.3;

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "After the Bell",
            X0 = X0, X1 = X1,
            Region = Dl16Lane.Region,                                                             // its checkpoints: crossing, store
            // Step order = the prototype's: the lever is held in updatePlayer (#4); then updateAtt2 moves the bridge, rolls
            // the procession on, stores the figures, drops the latch 1.2 s after the rack is full and lifts the
            // counterweight (#7, L5738–L5766).
            Mechanisms = new[]
            {
                new MechanismDef("dl16.lever", () => new Dl16Lever("dl16.lever")),
                new MechanismDef("dl16.bridge", () => new Dl16Bridge("dl16.bridge")),
                new MechanismDef("dl16.procession", () => new Dl16Procession("dl16.procession")),
                new MechanismDef("dl16.rack", () => new Rack("dl16.rack", RackParams.Dl16Rack())),
                new MechanismDef("dl16.latch", () => new Latch("dl16.latch", LatchParams())),
                new MechanismDef("dl16.rackCW", () => new CounterweightRack("dl16.rackCW", CounterweightRackParams.Dl16RackCw())),
            },
            Lane = Dl16Lane.Table,
            LaneContributors = Dl16Lane.Contributors,
            Rules = () => new Dl16Rules(),
        };

        /// <summary>The rack's latch (<c>b.latched</c>, L5764): 1.2 s after the rack is full; latched from <c>store</c> (L5551).</summary>
        public static LatchParams LatchParams() => new LatchParams { Trigger = "dl16.rack", Threshold = 1, Delay = 1.2, ReleasedAfter = "store" };
    }

    /// <summary>
    /// The crossing lever (<c>'att:lever16'</c>, L5625, L5660, L5685–L5694): once the class is dismissed and until the rack
    /// latches, on the floor within 0.3 of it, he pulls it (Pull, where he stands) and holds it as long as Use is held:
    /// held from 0.25 s; letting go after 0.5 s, moving, or the latch dropping ends it, and it springs back.
    /// Signals: <see cref="Engaged"/> = held (<c>b.held</c>).
    /// </summary>
    public sealed class Dl16Lever : StationMechanism, IEngageable
    {
        public const double HeldAfter = 0.25, LetGoAfter = 0.5;
        private static readonly ActProfile Pull = new ActProfile(ClipNames.Pull);

        private IEngageable _dismissed, _latched;
        private ActInput _act;
        private bool _ending, _held;

        public Dl16Lever(MechanismId id) : base(id, new Station(Dl16Scene.LeverStand, Dl16Scene.LeverReach, +1, reachX: Dl16Scene.LeverX)) { }

        public bool Engaged => _held;
        /// <summary>The bridge's latch has dropped (the lever stays down for good, L5837).</summary>
        public bool Latched => _latched != null && _latched.Engaged;
        public override ActProfile Profile => Pull;

        public override void Link(MechanismLinker link)
        {
            _dismissed = link.ReadAnyOrder<IEngageable>("dl15.seats");
            _latched = link.ReadAnyOrder<IEngageable>("dl16.latch");
        }

        protected override bool CanUse(in InteractionQuery q) => _dismissed.Engaged && !_latched.Engaged;   // L5625

        public override ActStep OnActFrame(in ActFrame f)
        {
            _act.Receive(f);
            var i = f.Input;
            bool moving = i.Move != 0 || i.JumpPressed;                                                         // L5689
            _ending = (f.Time > LetGoAfter && !i.UseHeld) || moving || _latched.Engaged;                        // L5690
            return ActStep.DoneIf(_ending);
        }

        public override void Reset(in Checkpoint cp) { _act.Clear(); _ending = _held = false; Init(0); }

        public override void Step(in StepContext ctx)
        {
            _act.Take();
            _held = _act.Active && !_ending && _act.Time > HeldAfter;                                         // L5687, L5691
            Enter(ctx, _held ? 1 : 0);
        }

        protected override void WriteFields(ISnapshotWriter w) { _act.Write(w); w.WriteBool("ending", _ending); w.WriteBool("held", _held); }
        protected override void ReadFields(ISnapshotReader r) { _act.Read(r); _ending = r.ReadBool("ending"); _held = r.ReadBool("held"); }
    }

    /// <summary>
    /// The bridge over the well (<c>b.bridge</c>, L5739–L5742): 1 open (the well is a well), 0 down (it carries); it goes
    /// down at 1/1.3 per second while the lever is held, a procession figure is on it, or the rack has latched, and back up
    /// otherwise. Down from <c>store</c> (L5551). Signals: <see cref="Position"/> = how open.
    /// </summary>
    public sealed class Dl16Bridge : Mechanism, IPositionSource
    {
        public const double Travel = 1.3;
        private IEngageable _held, _latched;
        private Dl15Figure _a, _b;

        public Dl16Bridge(MechanismId id) : base(id) { }

        public double Position { get; private set; }

        public override void Link(MechanismLinker link)
        {
            _held = link.Read<IEngageable>("dl16.lever");
            _latched = link.ReadAnyOrder<IEngageable>("dl16.latch");
            _a = link.Read<Dl15Figure>("dl15.figA"); _b = link.Read<Dl15Figure>("dl15.figB");
        }

        public override void Reset(in Checkpoint cp) { Position = cp.Past("store") ? 0 : 1; Init(Position > 0 ? 1 : 0); }

        public override void Step(in StepContext ctx)
        {
            double want = _latched.Engaged || _held.Engaged || OnIt(_a) || OnIt(_b) ? 0 : 1;                // L5741
            double v = Position;
            if (v != want) v += Math.Sign(want - v) * Math.Min(Math.Abs(want - v), ctx.Dt / Travel);
            Position = v;
            Enter(ctx, v > 0 ? 1 : 0);
        }

        private static bool OnIt(Dl15Figure f)                                                               // L5740
            => f.State == Dl15Figure.FigureState.Procession && f.X > Dl16Lane.PitX0 - Dl15Figure.Half && f.X < Dl16Lane.PitX1 + Dl15Figure.Half;

        protected override void WriteFields(ISnapshotWriter w) => w.WriteDouble("open", Position);
        protected override void ReadFields(ISnapshotReader r) => Position = r.ReadDouble("open");
    }

    /// <summary>
    /// The procession (<c>dl16.procession</c>, L5731, L5743–L5757): on dismissal the figures leave the class; front first,
    /// each bows (its lean) for 1.4 s, the next 0.4 s longer, then rolls on along the rail at 0.95 m/s, 0.8 over the well,
    /// 0.8 behind the one ahead, waiting at the well's edge while the bridge is open, into the rack at 305.6, where it is
    /// stored. It moves the figures itself (they are its while dismissed). Signals: <see cref="Engaged"/> = a figure is still
    /// rolling (not stored), which his courtesy waits for (L5768).
    /// </summary>
    public sealed class Dl16Procession : Mechanism, IEngageable
    {
        public const double Bow = 1.4, BowEach = 0.4, Gap = 0.8, Speed = 0.95, WellSpeed = 0.8, WellFrom = Dl16Lane.PitX0 - 1.2;

        private IEngageable _dismissed;
        private IPositionSource _bridge;
        private Dl15Figure _a, _b;
        private readonly Dl15Figure[] _order = new Dl15Figure[2];
        private bool _begun;
        private double _since;
        private ClockMark _at = ClockMark.None;

        public Dl16Procession(MechanismId id) : base(id) { }

        public bool Engaged => Rolling(_a) || Rolling(_b);
        /// <summary>Seconds since the dismissal (∞ for a class dismissed before the reset: no bow, L5745).</summary>
        public double Since => _since;

        private static bool Rolling(Dl15Figure f) => f.State == Dl15Figure.FigureState.Procession;

        public override void Link(MechanismLinker link)
        {
            _dismissed = link.Read<IEngageable>("dl15.seats");
            _bridge = link.Read<IPositionSource>("dl16.bridge");
            _a = link.Read<Dl15Figure>("dl15.figA"); _b = link.Read<Dl15Figure>("dl15.figB");
        }

        public override void Reset(in Checkpoint cp)
        {
            _begun = cp.Past("dismissed");
            _since = double.PositiveInfinity; _at.Clear();                                                       // dismissedAt undefined
            Init(0);
        }

        public override void Step(in StepContext ctx)
        {
            double dt = ctx.Dt;
            if (!_begun && _dismissed.Engaged) { _begun = true; _since = 0; _at.Mark(ctx); _a.BeginProcession(); _b.BeginProcession(); }   // L5731
            else if (_begun) { double s = _at.Since(ctx); _since = double.IsNaN(s) ? _since + dt : s; }                         // game.clock − dismissedAt
            // The figures in procession, front first (sort by x descending; a tie keeps A before B, L5743).
            int n = 0;
            if (Rolling(_a)) _order[n++] = _a;
            if (Rolling(_b)) { if (n == 1 && _b.X > _a.X) { _order[1] = _a; _order[0] = _b; } else _order[n] = _b; n++; }
            for (int i = 0; i < n; i++)
            {
                var f = _order[i];
                if (_since < Bow + i * BowEach) { f.Bow(dt); continue; }                                       // L5745
                double target = Dl15Figure.RackIn;
                if (_bridge.Position > Dl16Lane.OpenAbove && f.X <= Dl15Figure.Edge + 1e-3) target = Math.Min(target, Dl15Figure.Edge);   // L5747
                if (i > 0) target = Math.Min(target, _order[i - 1].X - Gap);                                     // L5748
                double speed = f.X < WellFrom ? Speed : WellSpeed;                                               // L5749
                double step = Math.Min(speed * dt, Math.Max(0, target - f.X));
                f.Roll(f.X + step, step / Math.Max(dt, 1e-4));                                                  // L5750–L5751
                if (f.X >= Dl15Figure.RackIn - 1e-3) f.Store();                                                  // L5753–L5754 (the rack hangs it)
            }
            Enter(ctx, Engaged ? 1 : 0);
        }

        protected override void WriteFields(ISnapshotWriter w) { w.WriteBool("begun", _begun); w.WriteDouble("since", _since); _at.Write(w, "atElapsed"); }
        protected override void ReadFields(ISnapshotReader r) { _begun = r.ReadBool("begun"); _since = r.ReadDouble("since"); _at.Read(r, "atElapsed"); }
    }

    /// <summary>
    /// DL-16's rules: his courtesy (<c>AfterYou</c>, the first time he comes up behind the waiting figures, L5767–L5769), the
    /// well (down it: back to the checkpoint, L5797), the rack's hush (L5759) and the checkpoints <c>crossing</c> and
    /// <c>store</c> (L5801–L5802).
    /// </summary>
    public sealed class Dl16Rules : SceneRules
    {
        public static readonly CueId MusicHush = CueId.Of("music:hush");
        /// <summary>His bow (<c>actions.AfterYou</c>, 36 frames, Motor/ClipTimings).</summary>
        public const string AfterYou = "AfterYou";
        private static readonly MechanismId RackId = "dl16.rack";

        private IEngageable _dismissed, _latched;
        private Dl16Procession _procession;
        private bool _bowed;

        public override bool Always => true;

        public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening)
        {
            var g = sim.Graph;
            _dismissed = g.Get<IEngageable>("dl15.seats"); _latched = g.Get<IEngageable>("dl16.latch");
            _procession = g.Get<Dl16Procession>("dl16.procession");
            _bowed = sim.Checkpoints.Current.Past("store");                                                     // bowed: stored, L5551
        }

        public override void AfterGraph(ChapterSim sim)
        {
            if (sim.Graph.Log.Has(RackId, MechanismEventKind.Event, (int)RackEvent.Full)) sim.Cue(MusicHush);
            if (sim.Region != Dl16Lane.Region) return;
            double x = sim.X;
            if (_dismissed.Engaged && !_bowed && x > Dl16Scene.BowX0 && x < Dl16Scene.BowX1 && _procession.Engaged
                && SceneQuirk.CanStart(sim) && SceneQuirk.Start(sim, AfterYou, cancel: true)) _bowed = true;   // L5768–L5769
            if (sim.Y < Dl16Scene.FellBelow && !(sim.RespawnAt > 0)) sim.RespawnAt = sim.Clock + Dl16Scene.RespawnDelay;  // L5797
            if (x > Dl16Scene.CrossingAt && _dismissed.Engaged) sim.Checkpoints.Reach("crossing");                  // L5801
            if (x > Dl16Scene.StoreAt && _latched.Engaged) sim.Checkpoints.Reach("store");                           // L5802
        }
    }
}
