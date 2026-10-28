using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Actuators
{
    public enum RatchetJackState
    {
        /// <summary>In its bay (the start; and from <c>repaired</c>, drawn back).</summary>
        Parked,
        /// <summary>On the tracks between the bay and the pocket.</summary>
        Free,
        /// <summary>Its wheels in the pocket's seats, its saddle under the platform's cup: the crank works.</summary>
        InPocket,
    }

    public enum RatchetJackEvent
    {
        /// <summary>Its wheels drop into the pocket's seats (clunk). Value = x.</summary>
        Clunk,
        /// <summary>A ratchet click: the ram passed a notch. Index = the notch, Value = +1 winding up, −1 down.</summary>
        Click,
        /// <summary>Winding up met its end: the top of travel, or the platform pinned on the spare. Once per hold.</summary>
        Bind,
        /// <summary>He heaves at it while it is loaded and it stays put. Once per hold.</summary>
        Heave,
    }

    public sealed class RatchetJackParams
    {
        /// <summary>Where he stands to crank it when it is in its pocket (behind its crank post), holding Use.</summary>
        public Station Station;
        public ActProfile Profile = new ActProfile(ClipNames.Crank);
        /// <summary>The bay and the pocket (its centre, lane x): its push travel, with a detent at each end.</summary>
        public double BayX, PocketX;
        /// <summary>Chassis half-length and height, and the crank post's height at its back (−x) end. No flat top: not climbable.</summary>
        public double Half, Height, PostHeight;
        /// <summary>The saddle's lane x relative to the chassis centre.</summary>
        public double SaddleOffset;
        /// <summary>The saddle's top fully down (Unity y) and its travel, metres.</summary>
        public double SaddleLowY, Travel;
        /// <summary>Winding speed (m/s) and one click per <see cref="ClickStep"/> of travel.</summary>
        public double WindSpeed = 0.1, ClickStep = 0.02;
        /// <summary>The stick past this, away from the jack, winds it down.</summary>
        public double PullBack = 0.3;

        /// <summary>The push: he stands <see cref="Gap"/> behind its centre on its <see cref="Side"/>, at <see cref="Speed"/> / <see cref="Accel"/>.</summary>
        public int Side = +1;
        public double Gap, Speed, Accel = 1.3, FloorY, Z, ForwardReach = 0.34, BackReach = 0.34;

        /// <summary>The platform (<see cref="ILoad"/>: its weight on the saddle; loaded, it will not roll).</summary>
        public MechanismId Platform;
        /// <summary>The pins (<see cref="IEngageable"/>: the spare seated; loaded against it, the ram binds).</summary>
        public MechanismId Pins;

        // DL-19 A Repair That Held: docs/scenes/DL-19_a_repair_that_held.md §3 ("The jack", table), §4, §11 Jack/JackSaddle/JackPocket. No prototype.

        /// <summary>
        /// DL-19: the wheeled ratchet jack, parked in its bay at 362.85 (bay 362.5–363.2), pushed along the worn tracks into
        /// the pocket at 363.7 (363.35–364.05), its saddle at 363.9 under the platform's cup. Chassis 0.7 × 0.25, crank post
        /// 0.65 at its back end. The saddle sits 2.5 cm under the cup of a platform on its stops and its top of travel holds
        /// the left end at 1.85. Wound at 0.1 m/s, a click per 0.02 m.
        /// </summary>
        public static RatchetJackParams Dl19Jack()
        {
            var landing = HalfLandingParams.Dl19HalfLanding();
            const double low = 1.38;                                              // under the cup on the stops (1.4046)
            return new RatchetJackParams
            {
                // Behind the crank post (363.35) on the terrace landing (1.2), facing it; just left of the bracket's stand.
                Station = new Station(standX: 363.1, reach: 0.1, face: +1, floorY: 1.2),
                BayX = 362.85, PocketX = 363.7,                                   // §11 Jack parked 362.85; JackPocket 363.7
                Half = 0.35, Height = 0.25, PostHeight = 0.65,                    // §3 "The jack": chassis 0.7 long, 0.25 tall; post 0.65
                SaddleOffset = 363.9 - 363.7,                                     // §3 "Pocket": the saddle cup at 363.9
                SaddleLowY = low,
                Travel = landing.CupY(1.85) - low,                                // §3: top of travel, left end at 1.85
                WindSpeed = 0.1, ClickStep = 0.02,                                // §3: one click per 0.02 m, 0.1 m/s
                Side = +1, Gap = 0.35 + 0.2,                                      // he pushes from behind the crank post
                Speed = 0.35, Accel = 1.3,                                        // grey-box: a heavy hold (cf. L2332's 1.3)
                FloorY = 1.2,                                                     // §3: terrace landing 1.2
                Platform = "dl19.landing", Pins = "dl19.pins",
            };
        }
    }

    /// <summary>
    /// A wheeled ratchet jack (chapter2_plan §7 "Support transfer", "Brakes and catches"; DL-19 §3 "The jack", §4, §11):
    /// pushed along its tracks between its bay and its pocket (the <see cref="Chassis"/> face, an <see cref="IPushable"/>
    /// with a detent at each end), and wound with its crank while it is in the pocket. Hold Use to wind the saddle up,
    /// hold Use with the stick pulled back to wind it down; the ratchet holds wherever he lets go. In the pocket its saddle
    /// lifts the platform once it meets the cup (the platform reads <see cref="Position"/> and <see cref="Engaged"/>).
    /// Loaded (<see cref="ILoad"/> from the platform) it will not roll: he heaves and it stays. Winding up binds at the
    /// top of travel and against a platform pinned on the spare. It is not climbable: the lane walls its footprint
    /// (<see cref="X0"/>..<see cref="X1"/>). It resets to its bay, fully down, at every checkpoint (from <c>repaired</c>
    /// he has drawn it back). No prototype exists; the type is new for chapter 2.
    /// <para>Signals: <see cref="Position"/> = the saddle's top, Unity y, metres; <see cref="Engaged"/> = in its pocket.</para>
    /// </summary>
    public sealed class RatchetJack : StationMechanism, IPositionSource, IEngageable
    {
        /// <summary>Within this of the bay or the pocket it is there (the motor's <c>PushLipTolerance</c>, L4686).</summary>
        public const double SeatTolerance = 0.005;
        private const double Eps = 1e-9;

        private readonly RatchetJackParams _p;
        private readonly double[] _detents;
        private ILoad _platform;
        private IEngageable _pinned;
        private ActInput _act;
        private bool _useHeld, _held, _moved, _heaved, _bound;
        private double _from;
        private int _notch;

        public RatchetJack(MechanismId id, RatchetJackParams p) : base(id, p.Station)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            if (p.Side != 1 && p.Side != -1) throw new ArgumentException(id + ": Side is +1 or −1.");
            if (!(p.PocketX > p.BayX)) throw new ArgumentException(id + ": the pocket lies right of the bay.");
            if (!(p.Travel > 0) || !(p.WindSpeed > 0) || !(p.ClickStep > 0)) throw new ArgumentException(id + ": travel, speed and click step are positive.");
            _detents = new[] { p.BayX, p.PocketX };
            Chassis = new RatchetJackChassis(this);
        }

        public RatchetJackParams Params => _p;
        public RatchetJackState State => (RatchetJackState)StateCode;
        /// <summary>The push face: register it with the resolver beside the jack (the crank).</summary>
        public RatchetJackChassis Chassis { get; }

        /// <summary>The chassis centre, lane x.</summary>
        public double X { get; private set; }
        /// <summary>Velocity while he moves it, m/s; 0 once he lets go.</summary>
        public double Velocity { get; private set; }
        /// <summary>The ram's extension, 0 .. <see cref="RatchetJackParams.Travel"/>, metres.</summary>
        public double Extension { get; private set; }
        /// <summary>This step's winding: +1 up, −1 down, 0 not winding (the view's crank wheel and pawl).</summary>
        public int Winding { get; private set; }
        /// <summary>He has it in his hands (pushing or pulling).</summary>
        public bool Held => _held;
        /// <summary>The platform rests on its saddle: it will not roll.</summary>
        public bool Loaded => _platform != null && _platform.Load > 0.5;
        /// <summary>The saddle's lane x.</summary>
        public double SaddleX => X + _p.SaddleOffset;
        /// <summary>The chassis's footprint on the lane (the lane walls it: not climbable).</summary>
        public double X0 => X - _p.Half;
        public double X1 => X + _p.Half;

        /// <summary>The saddle's top, Unity y.</summary>
        public double Position => _p.SaddleLowY + Extension;
        public bool Engaged => State == RatchetJackState.InPocket;

        public override ActProfile Profile => _p.Profile;

        // ---- The push (through the Chassis face) ---------------------------------------------------------------------------

        /// <summary>Its travel now: bay .. pocket, narrowed to the detents either side of where he took hold; loaded, nowhere.</summary>
        public void Range(out double lo, out double hi)
        {
            if (Loaded) { lo = hi = X; return; }
            lo = _p.BayX; hi = _p.PocketX;
            Push.Detents.Clamp(_detents, _held ? _from : X, ref lo, ref hi);
        }

        internal void MoveTo(double x, double velocity)
        {
            if (!_held) { _held = true; _from = X; }
            X = x; Velocity = velocity; _moved = true;
        }

        internal void Release() => _held = false;

        // ---- The crank ---------------------------------------------------------------------------------------------------

        protected override bool CanUse(in InteractionQuery q) => State == RatchetJackState.InPocket && !_held;

        /// <summary>He cranks while he holds Use; letting go ends the act (the ratchet holds).</summary>
        public override ActStep OnActFrame(in ActFrame f)
        {
            _act.Receive(f);
            _useHeld = f.Input.UseHeld;
            return ActStep.DoneIf(!f.Input.UseHeld);
        }

        public override void Link(MechanismLinker link)
        {
            _platform = link.ReadAnyOrder<ILoad>(_p.Platform);                 // platform ↔ jack: the jack reads last step's load
            _pinned = link.ReadAnyOrder<IEngageable>(_p.Pins);
        }

        public override void Reset(in Checkpoint cp)
        {
            X = _from = _p.BayX;
            Velocity = 0;
            Extension = 0;
            Winding = 0;
            _notch = 0;
            _useHeld = _held = _moved = _heaved = _bound = false;
            _act.Clear();
            Init((int)RatchetJackState.Parked);
        }

        public override void Step(in StepContext ctx)
        {
            _act.Take();

            var s = Math.Abs(X - _p.PocketX) < SeatTolerance ? RatchetJackState.InPocket
                : Math.Abs(X - _p.BayX) < SeatTolerance ? RatchetJackState.Parked : RatchetJackState.Free;
            if (!_held && s != RatchetJackState.Free) X = s == RatchetJackState.InPocket ? _p.PocketX : _p.BayX;   // its wheels settle in the seats
            if (s == RatchetJackState.InPocket && State != RatchetJackState.InPocket) Emit(ctx, (int)RatchetJackEvent.Clunk, 0, X);
            Enter(ctx, (int)s);

            if (_held && _moved && Loaded && !_heaved) { _heaved = true; Emit(ctx, (int)RatchetJackEvent.Heave); }
            if (!_held) _heaved = false;

            Winding = 0;
            if (_act.Active && _useHeld && State == RatchetJackState.InPocket)
            {
                int dir = _act.Move * _p.Station.Face < -_p.PullBack ? -1 : +1;
                if (dir > 0 && (Extension >= _p.Travel - Eps || (Loaded && _pinned != null && _pinned.Engaged)))
                {
                    if (!_bound) { _bound = true; Emit(ctx, (int)RatchetJackEvent.Bind, 0, Extension); }
                }
                else
                {
                    _bound = false;
                    Winding = dir;
                    Extension = Math.Max(0, Math.Min(_p.Travel, Extension + dir * _p.WindSpeed * ctx.Dt));
                }
            }
            else _bound = false;

            int notch = (int)Math.Floor(Extension / _p.ClickStep + 1e-6);
            if (notch != _notch) { Emit(ctx, (int)RatchetJackEvent.Click, notch, notch > _notch ? 1 : -1); _notch = notch; }

            if (!_moved) Velocity = 0;
            _moved = false;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("x", X); w.WriteDouble("v", Velocity); w.WriteDouble("from", _from);
            w.WriteDouble("ext", Extension); w.WriteLong("wind", Winding); w.WriteLong("notch", _notch);
            w.WriteBool("held", _held); w.WriteBool("moved", _moved); w.WriteBool("heaved", _heaved);
            w.WriteBool("bound", _bound); w.WriteBool("useHeld", _useHeld);
            _act.Write(w);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            X = r.ReadDouble("x"); Velocity = r.ReadDouble("v"); _from = r.ReadDouble("from");
            Extension = r.ReadDouble("ext"); Winding = (int)r.ReadLong("wind"); _notch = (int)r.ReadLong("notch");
            _held = r.ReadBool("held"); _moved = r.ReadBool("moved"); _heaved = r.ReadBool("heaved");
            _bound = r.ReadBool("bound"); _useHeld = r.ReadBool("useHeld");
            _act.Read(r);
        }
    }

    /// <summary>
    /// The jack's push face (<see cref="IPushable"/>; the pattern of <see cref="Push.PushTwin"/>): the motor moves the
    /// jack's chassis with it while he holds it. Not a mechanism: register it with the resolver beside the jack. Its
    /// travel has a detent at the bay and at the pocket (he lets go there); loaded, its travel is where it stands.
    /// </summary>
    public sealed class RatchetJackChassis : IPushable
    {
        public RatchetJackChassis(RatchetJack of) { Jack = of ?? throw new ArgumentNullException(nameof(of)); }

        public RatchetJack Jack { get; }

        public InteractionCategory Category => InteractionCategory.Push;
        public bool IsAvailable(in InteractionQuery q) => true;

        public double X => Jack.X;
        public int Side => Jack.Params.Side;
        public double Gap => Jack.Params.Gap;
        public double Speed => Jack.Params.Speed;
        public double Accel => Jack.Params.Accel;
        public bool LetGoAtMax => true;
        public double Min { get { Jack.Range(out double lo, out _); return lo; } }
        public double Max { get { Jack.Range(out _, out double hi); return hi; } }
        public double FloorY => Jack.Params.FloorY;
        public double Z => Jack.Params.Z;
        public double ForwardReach => Jack.Params.ForwardReach;
        public double BackReach => Jack.Params.BackReach;
        public bool TipsIntoPit => false;
        public bool HasDetents => true;

        public void MoveTo(double x, double velocity) => Jack.MoveTo(x, velocity);
        public void SetAtLip(bool atLip) { }
        public void OnReleased(bool atLip) => Jack.Release();
        public void OnShoved() => Jack.Release();
        public void OnTravelEnd() => Jack.Release();

        public override string ToString() => "RatchetJackChassis " + Jack.Id;
    }
}
