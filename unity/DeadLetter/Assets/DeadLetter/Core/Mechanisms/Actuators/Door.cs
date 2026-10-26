using System;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Actuators
{
    public enum DoorState { Closed, Opening, Open }

    public enum DoorEvent
    {
        /// <summary><see cref="DoorParams.CueAt"/> seconds into the opening (DL-01: the counterweight's thud and shake at 0.56 s, L1683).</summary>
        Cue,
    }

    public enum DoorCurve
    {
        /// <summary><c>door = min(1, door + dt / T)</c> (L5737, L5794, L6228).</summary>
        Linear,
        /// <summary><c>1 − (1 − p)³</c> (C-114, L7277).</summary>
        EaseOutCubic,
        /// <summary>DL-01's shutter: snaps to 104 %, settles to 100 % by 0.9 s, jitters for 0.8 s unless calm (L1693–L1696). Travel in degrees.</summary>
        ShutterSwing,
    }

    public sealed class DoorParams
    {
        /// <summary>Follow mode: the opening is this source's Position (0..1) × <see cref="Travel"/> (a crank-driven door).</summary>
        public MechanismId Follow;
        /// <summary>Timed mode: opens once this <see cref="IEngageable"/> has been engaged for more than <see cref="Delay"/> seconds.</summary>
        public MechanismId Trigger;
        public double Delay;
        public double Duration = 1;
        /// <summary>Full opening in the view's unit (metres of lift, or degrees of swing).</summary>
        public double Travel = 1;
        public DoorCurve Curve = DoorCurve.Linear;
        /// <summary>
        /// True: the opening advances on the step it is triggered (<c>door += dt / T</c> in the same update). False: it
        /// starts from t = 0 on that step (DL-01's shutter: <c>t = clock − releaseTime</c>, L1692).
        /// </summary>
        public bool CountTriggerStep = true;
        /// <summary>
        /// Timed mode: a persist flag (<c>StoryFlags</c>) that must also be set before it opens; null = none. The delay
        /// runs from the trigger alone, so a trigger held long enough opens it on the step the flag is set.
        /// </summary>
        public string RequiresFlag;
        /// <summary>Seconds into the opening at which to emit <see cref="DoorEvent.Cue"/>; &lt; 0 = none.</summary>
        public double CueAt = -1;

        /// <summary>DL-01: the exit door rises with the crank to DOOR.h − 0.05 (L300, L7957).</summary>
        public static DoorParams Dl01Door() => new DoorParams { Follow = "dl01.crank", Travel = 1.05 - 0.05 };

        /// <summary>DL-01: the shutter swings to 15° when the latch releases (L277, L1681–L1696).</summary>
        public static DoorParams Dl01Shutter() => new DoorParams
        {
            Trigger = "dl01.latch", Duration = 0.9, Travel = 15, Curve = DoorCurve.ShutterSwing,
            CountTriggerStep = false, CueAt = 0.56,
        };

        /// <summary>DL-11: C-114's front door swings 95° over 1.6 s, easing out (L7274–L7277). The trigger is the cord pull of the knock act.</summary>
        public static DoorParams Dl11C114Door(MechanismId cord) => new DoorParams
        {
            Trigger = cord, Duration = 1.6, Travel = 95, Curve = DoorCurve.EaseOutCubic,      // C114DOOR.open, L3470
        };

        /// <summary>DL-14a: opens 1.2 s after the room has been dark (sun &lt; 0.05 and both blinds down), over 1.4 s (L6225–L6228).</summary>
        public static DoorParams Dl14aDoor() => new DoorParams { Trigger = "dl14a.nightLight", Delay = 1.2, Duration = 1.4 };

        /// <summary>DL-15: the classroom door opens over 1.6 s on dismissal (L5737).</summary>
        public static DoorParams Dl15ClassDoor() => new DoorParams { Trigger = "dl15.seats", Duration = 1.6 };

        /// <summary>
        /// DL-17: the stair door opens 0.8 s after the float latch, over 1.8 s, once Lisle's drawing has been read
        /// (the door rule sits inside <c>if (d.read)</c>, L5776, L5789, L5794).
        /// </summary>
        public static DoorParams Dl17StairDoor() => new DoorParams
        {
            Trigger = "dl17.latch", Delay = 0.8, Duration = 1.8, RequiresFlag = StoryFlags.Dl17DrawerRead,
        };
    }

    /// <summary>
    /// A door, shutter or gate that opens once (§4.13d). Follow mode mirrors a crank; timed mode opens over a duration
    /// after a trigger has held for a delay (a trigger that drops before the delay restarts it, <c>darkSince = null</c>,
    /// L6224). Once opening it never closes. Signals: <see cref="Position"/> (Travel units), <see cref="Engaged"/> = fully open.
    /// </summary>
    public sealed class Door : Mechanism, IPositionSource, IEngageable
    {
        private readonly DoorParams _p;
        private IPositionSource _follow;
        private IEngageable _trigger;
        private IPersistFlagReader _flags;
        private int _flag = -1;
        private double _held = -1, _t;
        private bool _cued;

        public Door(MechanismId id, DoorParams p) : base(id) { _p = p; }

        public DoorState State => (DoorState)StateCode;
        public double Position { get; private set; }
        public bool Engaged => State == DoorState.Open;
        /// <summary>Seconds since it started opening, held at Duration once open (drives <see cref="ShutterCounterweightY"/> in the DL-01 view).</summary>
        public double Elapsed => _t;

        public override void Link(MechanismLinker link)
        {
            _follow = link.Read<IPositionSource>(_p.Follow);
            _trigger = link.Read<IEngageable>(_p.Trigger);
            if ((_follow == null) == (_trigger == null)) throw new InvalidOperationException(Id + " needs exactly one of Follow or Trigger.");
            if (_p.RequiresFlag != null)
            {
                if (_trigger == null) throw new InvalidOperationException(Id + ": RequiresFlag needs a Trigger.");
                _flags = link.Flags;
                _flag = _flags.Resolve(_p.RequiresFlag);
            }
        }

        /// <summary>Derived from its source, which is already reset: open if the trigger is engaged (no replay of the swing).</summary>
        public override void Reset(in Checkpoint cp)
        {
            _held = -1;
            if (_follow != null) { Position = _follow.Position * _p.Travel; Init((int)FollowState(_follow.Position)); return; }
            bool open = _trigger.Engaged && Allowed;
            Init((int)(open ? DoorState.Open : DoorState.Closed));
            _t = open ? _p.Duration : 0;
            _cued = open;
            Position = open ? Shape(1, _t, true) : 0;
        }

        public override void Step(in StepContext ctx)
        {
            if (_follow != null) { Position = _follow.Position * _p.Travel; Enter(ctx, (int)FollowState(_follow.Position)); return; }

            if (State == DoorState.Closed)
            {
                if (!_trigger.Engaged) { _held = -1; return; }
                _held = _held < 0 ? 0 : _held + ctx.Dt;
                if (!(_p.Delay <= 0 || _held > _p.Delay)) return;
                if (!Allowed) return;
                Enter(ctx, (int)DoorState.Opening);
                _t = _p.CountTriggerStep ? ctx.Dt : 0;
            }
            else if (State == DoorState.Opening) _t += ctx.Dt;
            else return;

            double p = _t >= _p.Duration - 1e-9 ? 1 : _t / _p.Duration;
            Position = Shape(p, _t, ctx.Calm);
            if (_p.CueAt >= 0 && !_cued && _t >= _p.CueAt - 1e-9) { _cued = true; Emit(ctx, (int)DoorEvent.Cue); }
            if (p >= 1) Enter(ctx, (int)DoorState.Open);
        }

        private bool Allowed => _flag < 0 || _flags.Get(_flag);

        private static DoorState FollowState(double p) => p >= 1 ? DoorState.Open : p > 0 ? DoorState.Opening : DoorState.Closed;

        private double Shape(double p, double t, bool calm)
        {
            switch (_p.Curve)
            {
                case DoorCurve.EaseOutCubic: { double q = 1 - p; return _p.Travel * (1 - q * q * q); }
                case DoorCurve.ShutterSwing:
                {
                    double k1 = p - 1;                                                                  // k = min(1, t / 0.9)
                    double settle = 1 + 0.9 * k1 * k1 * k1 + 1.5 * k1 * k1 * (p < 1 ? 1 : 0);           // L1694
                    double jitter = t < 0.8 && !calm ? Math.Sin(t * 90) * 0.4 * (1 - t / 0.8) : 0;     // L1695
                    return _p.Travel * Math.Min(1.04, settle) + jitter;                                // L1696
                }
                default: return _p.Travel * p;
            }
        }

        /// <summary>DL-01's counterweight y, metres, <paramref name="t"/> s after the release: falls 0.54 s from 1.56 to 0.12, bounces 3 cm (L1697–L1699).</summary>
        public static double ShutterCounterweightY(double t)
        {
            double fallT = Math.Min(t, 0.54);
            double y = Math.Max(0.12, 1.56 - 0.5 * 9.8 * fallT * fallT * 1.8);
            if (t > 0.54 && t < 0.7) y = 0.12 + 0.03 * Math.Sin((t - 0.54) / 0.16 * Math.PI);
            return y;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("pos", Position);
            w.WriteDouble("held", _held);
            w.WriteDouble("t", _t);
            w.WriteBool("cued", _cued);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Position = r.ReadDouble("pos");
            _held = r.ReadDouble("held");
            _t = r.ReadDouble("t");
            _cued = r.ReadBool("cued");
        }
    }
}
