using System;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Lifts
{
    public enum HalfLandingState
    {
        /// <summary>Hanging on the bent pin, its left end low (1.55): the start. It creaks (the pin's <c>Sound</c>).</summary>
        Drooping,
        /// <summary>Dropping onto whatever is below it (the stops, the bent pin, the jack's saddle).</summary>
        Falling,
        /// <summary>Resting on the safety stops (1.45), steeper.</summary>
        OnStops,
        /// <summary>Carried by the jack's saddle, off its level band (1.45 to 1.85).</summary>
        Held,
        /// <summary>Within the level band (1.75 ± 0.02): the marks meet. The jack carries it.</summary>
        Level,
        /// <summary>On the spare pin with the jack clear of it: level, standable. The solved state; it persists.</summary>
        Pinned,
    }

    public enum HalfLandingEvent
    {
        /// <summary>It landed hard (a bang and a damped shake). Index: 0 the stops, 1 the bent pin, 2 the jack's saddle. Value = speed, m/s.</summary>
        Drop,
        /// <summary>
        /// D-17 stepped onto it while it was not pinned: the scene plays <c>Teeter</c>, a hop back and <c>Settle</c>.
        /// Index: 0 it lurches and springs back (drooping, held), 1 it rocks toward the shaft and clangs (on the stops).
        /// Value = the dip, metres.
        /// </summary>
        Lurch,
    }

    public sealed class HalfLandingParams
    {
        /// <summary>Its free (left) end and its hinge (right end), lane x; the hinge's top height, which is also level.</summary>
        public double LeftX, HingeX, HingeY;
        /// <summary>The left end's top at the start (on the bent pin), on the safety stops, and level (± <see cref="LevelTolerance"/>).</summary>
        public double StartY, StopsY, LevelY, LevelTolerance = 0.02;
        /// <summary>The saddle cup under it (lane x) and the plate's depth: the saddle meets it this far below the top there.</summary>
        public double CupX, Depth;
        /// <summary>It falls under gravity (m/s²); a landing at <see cref="BangSpeed"/> or faster is a <see cref="HalfLandingEvent.Drop"/>.</summary>
        public double Gravity = 9.81, BangSpeed = 0.4;
        /// <summary>
        /// The fastest the saddle lifts the left end, m/s. Cranking stays under it (0.1 m/s at the cup); it matters when a
        /// jack already wound up rolls in under a lower plate: the saddle rides up the cup's chamfer and lifts it smoothly
        /// instead of in one step (#47 review).
        /// </summary>
        public double LiftSpeed = 0.2;
        /// <summary>D-17 is on it when grounded within this of its top; the lurch dips this far (view).</summary>
        public double StandTolerance = 0.06, LurchDip = 0.03, RockDip = 0.05;
        /// <summary>The jack (<see cref="IPositionSource"/>: saddle top y; <see cref="IEngageable"/>: in its pocket, under the cup).</summary>
        public MechanismId Jack;
        /// <summary>The bracket's pins (<see cref="IPositionSource"/>: the height the pin in the fork holds the left end at; <see cref="IEngageable"/>: the spare is seated).</summary>
        public MechanismId Pins;
        /// <summary>From this checkpoint on it is pinned (solved states persist).</summary>
        public string PinnedAfter;

        /// <summary>The plate's top at lane x for a left-end top <paramref name="leftTop"/> (it pivots at its hinge).</summary>
        public double TopAt(double leftTop, double x) => HingeY + (leftTop - HingeY) * (HingeX - x) / (HingeX - LeftX);

        /// <summary>Where the saddle meets the cup for a left-end top <paramref name="leftTop"/> (saddle top y).</summary>
        public double CupY(double leftTop) => TopAt(leftTop, CupX) - Depth;

        /// <summary>The left-end top a saddle at <paramref name="saddleY"/> holds it at (the inverse of <see cref="CupY"/>).</summary>
        public double LeftTopForSaddle(double saddleY) => HingeY + (saddleY + Depth - HingeY) * (HingeX - LeftX) / (HingeX - CupX);

        // DL-19 A Repair That Held: docs/scenes/DL-19_a_repair_that_held.md §3 (layout, "The half landing's states"), §4, §11. No prototype.

        /// <summary>
        /// DL-19: the half landing, 363.6–366.2, hinged at its right end to the upper flight's stringer (366.2, top 1.75).
        /// Its left end droops to 1.55 on the bent pin, rests at 1.45 on the safety stops, is level at 1.75 ± 0.02 and
        /// pinned there on the spare from <c>repaired</c>. The jack's saddle cup is at 363.9; the plate is 0.08 deep (the
        /// skirt under it tops out at 1.67 under a level 1.75 top).
        /// </summary>
        public static HalfLandingParams Dl19HalfLanding() => new HalfLandingParams
        {
            LeftX = 363.6, HingeX = 366.2, HingeY = 1.75,           // §3 table "Half landing"; §11 HalfLanding pivot 366.2, 1.75
            StartY = 1.55, StopsY = 1.45,                           // §3 states: drooping 1.55, on the stops 1.45
            LevelY = 1.75, LevelTolerance = 0.02,                   // §3 states: level 1.75 ± 0.02
            CupX = 363.9, Depth = 1.75 - 1.67,                      // §3 "Pocket": the saddle cup at 363.9; "Skirt" 1.2–1.67
            Jack = "dl19.jack", Pins = "dl19.pins",
            PinnedAfter = "repaired",                               // §9: repaired, with the half landing pinned
        };
    }

    /// <summary>
    /// A platform hinged at one end whose free end hangs on whatever holds it highest (chapter2_plan §7; DL-19 §3–§4,
    /// §11 <c>HalfLanding</c>): the pin in the bracket's fork (<see cref="Catches.BracketPins"/>), the safety stops (a
    /// fixed floor at <see cref="HalfLandingParams.StopsY"/>) and the jack's saddle when the jack is in its pocket
    /// (<see cref="Actuators.RatchetJack"/>). The saddle lifts it rigidly and it rides the saddle down; when nothing
    /// higher holds it, it falls under gravity onto the next support (a bang if fast). A seated spare pins it at level:
    /// the jack can carry it only within the level band above that, and lowering settles it onto the pin. Standing on it
    /// unpinned emits <see cref="HalfLandingEvent.Lurch"/>. No prototype exists; the type is new for chapter 2.
    /// <para>Signals: <see cref="Position"/> = the left end's top, metres; <see cref="Load"/> = its weight on the jack
    /// (0 or 1); <see cref="Engaged"/> = pinned (standable). The lane reads <see cref="TopAt"/> (its top at x, any
    /// state, so he can mantle onto the drooping end and lurch) and <see cref="Standable"/>.</para>
    /// </summary>
    public sealed class HalfLanding : Mechanism, IPositionSource, ILoad, IEngageable
    {
        private const double Eps = 1e-9;

        private readonly HalfLandingParams _p;
        private IPositionSource _saddle, _pin;
        private IEngageable _inPocket, _spare;
        private double _v;
        private bool _onJack, _wasOn;

        public HalfLanding(MechanismId id, HalfLandingParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            if (!(p.HingeX > p.CupX && p.CupX > p.LeftX)) throw new ArgumentException(id + ": the cup lies between the left end and the hinge.");
        }

        public HalfLandingParams Params => _p;
        public HalfLandingState State => (HalfLandingState)StateCode;
        /// <summary>The left end's top, metres (Unity y).</summary>
        public double Position { get; private set; }
        /// <summary>Its weight on the jack's saddle: 1 while the saddle carries it, else 0.</summary>
        public double Load => _onJack ? 1 : 0;
        /// <summary>Pinned on the spare with the jack clear: standable.</summary>
        public bool Engaged => State == HalfLandingState.Pinned;
        public bool Standable => Engaged;
        /// <summary>The marks on the bracket and the lug meet.</summary>
        public bool MarksMeet => Math.Abs(Position - _p.LevelY) <= _p.LevelTolerance + Eps;
        /// <summary>Its vertical speed while falling, m/s (+ down).</summary>
        public double FallSpeed => _v;
        /// <summary>Its tilt from level, degrees (+ = the left end low).</summary>
        public double TiltDeg => Math.Atan2(_p.HingeY - Position, _p.HingeX - _p.LeftX) * 180 / Math.PI;

        /// <summary>Its top at lane x (it slopes from the left end to the hinge), or NaN off its length. Read by the lane.</summary>
        public double TopAt(double x) => x >= _p.LeftX && x <= _p.HingeX ? _p.TopAt(Position, x) : double.NaN;

        public override void Link(MechanismLinker link)
        {
            _saddle = link.Read<IPositionSource>(_p.Jack);
            _inPocket = link.Read<IEngageable>(_p.Jack);
            _pin = link.Read<IPositionSource>(_p.Pins) ?? throw new InvalidOperationException(Id + " needs its pins.");
            _spare = link.Read<IEngageable>(_p.Pins);
        }

        public override void Reset(in Checkpoint cp)
        {
            bool pinned = cp.Past(_p.PinnedAfter);
            Position = pinned ? _p.LevelY : _p.StartY;
            Init((int)(pinned ? HalfLandingState.Pinned : HalfLandingState.Drooping));
            _v = 0;
            _onJack = _wasOn = false;
        }

        public override void Step(in StepContext ctx)
        {
            double pinY = _pin.Position;                                       // −∞ while the fork holds nothing
            double jackY = _inPocket != null && _inPocket.Engaged ? _p.LeftTopForSaddle(_saddle.Position) : double.NegativeInfinity;

            if (_spare.Engaged)
            {
                // Pinned: the pin holds it at level; the jack can carry it only within the band above (the hole's play).
                Position = jackY <= pinY ? pinY : Math.Min(jackY, pinY + _p.LevelTolerance);
                _v = 0;
                _onJack = jackY >= Position - Eps;
                Enter(ctx, (int)(_onJack ? HalfLandingState.Level : HalfLandingState.Pinned));
            }
            else
            {
                double other = Math.Max(_p.StopsY, pinY);
                if (jackY > other + Eps && (jackY >= Position - Eps || _onJack))
                {
                    Position = Math.Min(jackY, Position + _p.LiftSpeed * ctx.Dt); // the saddle lifts it, or it rides the saddle down
                    _v = 0;
                    _onJack = true;
                }
                else
                {
                    _onJack = false;
                    double target = Math.Max(other, jackY);
                    if (Position > target + Eps)
                    {
                        _v += _p.Gravity * ctx.Dt;
                        Position -= _v * ctx.Dt;
                        if (Position <= target)
                        {
                            Position = target;
                            int support = jackY > other + Eps ? 2 : pinY >= _p.StopsY + Eps ? 1 : 0;
                            if (_v >= _p.BangSpeed) Emit(ctx, (int)HalfLandingEvent.Drop, support, _v);
                            _v = 0;
                            _onJack = support == 2;
                        }
                    }
                    else { Position = target; _v = 0; }
                }
                Enter(ctx, (int)Resting(pinY));
            }

            bool on = OnIt(ctx.Player);
            if (on && !_wasOn && State != HalfLandingState.Pinned)
            {
                bool stops = State == HalfLandingState.OnStops;
                Emit(ctx, (int)HalfLandingEvent.Lurch, stops ? 1 : 0, stops ? _p.RockDip : _p.LurchDip);
            }
            _wasOn = on;
        }

        private HalfLandingState Resting(double pinY)
        {
            if (_v > 0) return HalfLandingState.Falling;
            if (_onJack) return MarksMeet ? HalfLandingState.Level : HalfLandingState.Held;
            return pinY >= _p.StopsY + Eps && Position <= pinY + Eps ? HalfLandingState.Drooping : HalfLandingState.OnStops;
        }

        /// <summary>He stands on its top.</summary>
        private bool OnIt(in PlayerPose pl)
        {
            if (!pl.Grounded || pl.X < _p.LeftX || pl.X > _p.HingeX) return false;
            return Math.Abs(pl.Y - _p.TopAt(Position, pl.X)) <= _p.StandTolerance;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("y", Position);
            w.WriteDouble("v", _v);
            w.WriteBool("onJack", _onJack);
            w.WriteBool("wasOn", _wasOn);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Position = r.ReadDouble("y");
            _v = r.ReadDouble("v");
            _onJack = r.ReadBool("onJack");
            _wasOn = r.ReadBool("wasOn");
        }
    }
}
