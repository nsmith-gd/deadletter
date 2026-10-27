using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Docks
{
    public enum CradleState { Free, Drawing, Closing, Seated }

    public enum CradleEvent
    {
        /// <summary>
        /// It took the courier: the drag sound stops, servo whine (L4791). Index 1: he dragged it to the end of its travel
        /// and the arms close on it at once (the drag sound stops, no whine; L4727).
        /// </summary>
        Take,
        /// <summary>Seated: servo, clunk; the scene starts the <c>bayTouch</c> act once (stand 44.92, face −1; L4806–L4807).</summary>
        Seat,
    }

    public sealed class CradleParams
    {
        /// <summary>The body it draws in (its x, and <see cref="BodySupport.Pushed"/> while he drags it).</summary>
        public MechanismId Body;
        /// <summary>Seat x, and how near it must be let go (L4790).</summary>
        public double BayX, TakeWithin = 0.6;
        /// <summary>Arms reach over ReachTime; the body is drawn from DrawAfter at DrawRate /s; at ReachTime it lies at BayX (L4792–L4797).</summary>
        public double ReachTime = 1.2, DrawAfter = 0.3, DrawRate = 3;
        /// <summary>Arms close from CloseDelay over CloseTime; seated after SeatAfter (L4801–L4803).</summary>
        public double CloseDelay = 0.3, CloseTime = 0.8, SeatAfter = 1.1;
        /// <summary>Seated, the arms lift back from LiftDelay over LiftTime (L4811).</summary>
        public double LiftDelay = 0.15, LiftTime = 1.2;
        /// <summary>Arm angles, radians (rotation.x): reach 0.3, closed −0.558 (L4794, L4802).</summary>
        public double ReachRad = 0.3, ClosedRad = -0.558;
        public string SeatedAfter;

        /// <summary>DL-04: the bay cradle at <c>RK.bayX</c> 44.5 (L3890, L4787–L4812); seated from <c>bay</c> (L4096).</summary>
        public static CradleParams Dl04Cradle() => new CradleParams { Body = "dl04.courier", BayX = 44.5, SeatedAfter = "bay" };
    }

    /// <summary>
    /// A cradle that takes a body let go near it, draws it in, closes on it and seats it (§4.13b, DL-04 L4787–L4812).
    /// A body dragged all the way to the end of its travel (a pushable docked there: its <see cref="IEngageable.Engaged"/>)
    /// is not drawn in: the arms close on it where it lies (<c>s.state = 'cradle'</c>, L4727).
    /// Once it has taken the body it owns its x: the scene reads <see cref="Position"/> and <see cref="Taken"/>.
    /// Signals: <see cref="Position"/> = the body's x, metres; <see cref="Engaged"/> = seated (holds the bay door).
    /// Deliberate deviation: after a reload the prototype's seated lamps stay at their first flicker frame
    /// (<c>seatedAt</c> is not reset, L4818); here they hold steady (<see cref="SeatedFor"/> starts large).
    /// </summary>
    public sealed class Cradle : Mechanism, IPositionSource, IEngageable
    {
        private readonly CradleParams _p;
        private IPlateBody _body;
        private IEngageable _docked;
        private double _x, _t, _seatedFor;

        public Cradle(MechanismId id, CradleParams p) : base(id) { _p = p ?? throw new ArgumentNullException(nameof(p)); }

        public CradleState State => (CradleState)StateCode;
        public bool Engaged => State == CradleState.Seated;
        public bool Taken => State != CradleState.Free;
        /// <summary>The body's x: the cradle's while taken, else the body's own.</summary>
        public double Position => Taken ? _x : _body.X;
        /// <summary>Both arms' rotation.x, radians (also the seated courier's tilt once seated).</summary>
        public double ArmRad { get; private set; }
        /// <summary>Seconds since it seated (−1 before): drives the lamps through <see cref="SeatedLamp"/>.</summary>
        public double SeatedFor => _seatedFor;

        public override void Link(MechanismLinker link)
        {
            _body = link.Read<IPlateBody>(_p.Body) ?? throw new InvalidOperationException(Id + " needs a Body.");
            _docked = _body as IEngageable;                                          // optional: a pushable docks at its travel's end
        }

        public override void Reset(in Checkpoint cp)
        {
            bool seated = cp.Past(_p.SeatedAfter);                                   // L4096
            Init((int)(seated ? CradleState.Seated : CradleState.Free));
            _x = seated ? _p.BayX : _body.X;
            _t = seated ? 99 : 0;
            _seatedFor = seated ? 1e3 : -1;
            ArmRad = 0;
        }

        public override void Step(in StepContext ctx)
        {
            double dt = ctx.Dt;
            if (State == CradleState.Seated) _seatedFor += dt;
            var s = _body.Support;
            if (State == CradleState.Free && s != BodySupport.Away && _docked != null && _docked.Engaged)             // L4727
            {
                // Dragged to the end of its travel: he let go there and it is the cradle's, closing at once (t = 0, then
                // the closing below runs this step too, as updateCh1 follows updateHoldCh1).
                Enter(ctx, (int)CradleState.Closing); _x = _body.X; _t = 0;
                Emit(ctx, (int)CradleEvent.Take, 1, _x);
            }
            if (State == CradleState.Free && s != BodySupport.Pushed && s != BodySupport.Away && _body.X > _p.BayX - _p.TakeWithin)   // L4790
            {
                Enter(ctx, (int)CradleState.Drawing); _x = _body.X; _t = 0;
                Emit(ctx, (int)CradleEvent.Take);
            }
            if (State == CradleState.Drawing)                                                              // L4792–L4797
            {
                _t += dt;
                ArmRad = _p.ReachRad * Math.Sin(Math.PI * Math.Min(1, _t / _p.ReachTime));
                if (_t > _p.DrawAfter) _x += (_p.BayX - _x) * (1 - Smooth.DecayFactor(_p.DrawRate, dt));
                if (_t > _p.ReachTime) { _x = _p.BayX; Enter(ctx, (int)CradleState.Closing); _t = 0; }
            }
            if (State == CradleState.Closing)                                                              // L4799–L4808
            {
                _t += dt;
                ArmRad = _p.ClosedRad * Smooth.Step((_t - _p.CloseDelay) / _p.CloseTime);
                if (_t > _p.SeatAfter)
                {
                    Enter(ctx, (int)CradleState.Seated); _t = 0; _seatedFor = 0;
                    Emit(ctx, (int)CradleEvent.Seat);
                }
            }
            if (State == CradleState.Seated)                                                               // L4809–L4812
            {
                _t += dt;
                ArmRad = _p.ClosedRad * (1 - Smooth.Step((_t - _p.LiftDelay) / _p.LiftTime));
            }
        }

        /// <summary>The seated lamps <paramref name="t"/> s after seating: flicker for 2.2 s, then hold 0.55 (L4818–L4819).</summary>
        public static double SeatedLamp(double t)
        {
            if (t < 0) return 0;
            if (t < 2.2) return (Math.Sin(t * 31) > 0.2 ? 0.6 : 0.05) * (0.4 + 0.6 * Smooth.Step(t / 2.2));
            return 0.55;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("x", _x);
            w.WriteDouble("t", _t);
            w.WriteDouble("seatedFor", _seatedFor);
            w.WriteDouble("arm", ArmRad);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _x = r.ReadDouble("x");
            _t = r.ReadDouble("t");
            _seatedFor = r.ReadDouble("seatedFor");
            ArmRad = r.ReadDouble("arm");
        }
    }
}
