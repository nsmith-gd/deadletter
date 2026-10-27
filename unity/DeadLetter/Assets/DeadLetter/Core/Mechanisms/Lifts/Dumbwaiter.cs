using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Lifts
{
    /// <summary>The prototype's <c>f16a.mode</c> (L6233–L6245).</summary>
    public enum DumbwaiterState
    {
        Top,
        /// <summary>Called down (or sent down from the top), 4.2 s.</summary>
        Down,
        Bottom,
        /// <summary>The right load: up over 4.2 s.</summary>
        Rise,
        /// <summary>Too light: it leaps 1.5 m, the catch bites, it is lowered back on the brake.</summary>
        Shoot,
    }

    public enum DumbwaiterEvent
    {
        /// <summary>Bell pressed too heavy: buzz, shake 0.08; it stays (<c>overAt</c>, L6173).</summary>
        Over,
        /// <summary>Shooting up, the catch bites (clank, ratchet, shake 0.45; L6241).</summary>
        CatchBite,
        /// <summary>It stopped (clunk). Index 0 = at the top (shake 0.12; <c>rode16a</c>, L6236), 1 = at the bottom (L6237, L6244).</summary>
        Arrive,
    }

    public sealed class DumbwaiterParams
    {
        /// <summary>The car's load (an <see cref="ILoad"/>): the weight of the tins in it (<c>load16a</c>, L5939).</summary>
        public MechanismId Load;
        /// <summary>The load that sends it up (<c>ATT3.need</c>: 0 after the redesign, L5904).</summary>
        public double Need = 0;
        /// <summary>The car (<c>ATT3.car</c>, L5903): x0, x1, floor 0.05, top 2.45.</summary>
        public double X0, X1, Floor = 0.05, Top = 2.45;
        /// <summary>Up or down over 4.2 s, smoothstep (L6236–L6237).</summary>
        public double TravelTime = 4.2;
        /// <summary>Shoot: up 1.5 m as (t / 0.8)^1.6, caught at 0.8 s, lowered from 1.4 s over 2.6 s, at the bottom at 4.0 s (L6238–L6244).</summary>
        public double ShootPeak = 1.5, ShootUp = 0.8, ShootPower = 1.6, LowerFrom = 1.4, LowerOver = 2.6, ShootEnd = 4.0;
        /// <summary>He rides it while it moves and he stands in the car within 0.1 of its floor (L6182).</summary>
        public double RideTolerance = 0.1;

        /// <summary>DL-16a: the servery dumbwaiter (<c>ATT3.car</c>, L5903; L6144–L6191, L6233–L6246).</summary>
        public static DumbwaiterParams Dl16aCar() => new DumbwaiterParams
        {
            Load = "dl16a.carLoad",
            X0 = 312.6, X1 = 313.4,
        };
    }

    /// <summary>
    /// The DL-16a dumbwaiter (<c>dl16a.car</c>, with <c>dl16a.counterweight</c>; §4.13f "<c>dl16a.dumbwaiter</c>";
    /// L6233–L6246). It starts at the top; the call push outside brings it down; the bell inside sends it by its load:
    /// the right load rises, too light shoots and is caught and lowered, too heavy buzzes.
    /// Signals: <see cref="Position"/> = the car floor's y, metres (<c>f16a.h</c>); <see cref="ILiftRide"/> carries him
    /// while it moves (<c>ride16a</c>, L6187, L6246).
    /// Inputs (from the acts, before the graph): <see cref="Call"/> (call push, a.t &gt; 0.45, L6146) and
    /// <see cref="Bell"/> (bell push, a.t &gt; 0.55, L6169). Both answer only at the top or the bottom (L5995–L5996).
    /// </summary>
    public sealed class Dumbwaiter : Lift
    {
        private readonly DumbwaiterParams _p;
        private ILoad _load;
        private double _t;
        private bool _caught, _call, _bell;

        public Dumbwaiter(MechanismId id, DumbwaiterParams p) : base(id) { _p = p; }

        public DumbwaiterState State => (DumbwaiterState)StateCode;
        /// <summary>The car floor's y, metres.</summary>
        public override double Position => H;
        public double H { get; private set; }
        public bool Moving => State == DumbwaiterState.Rise || State == DumbwaiterState.Down || State == DumbwaiterState.Shoot;

        /// <summary>The call push (L6146): from the top it comes down; otherwise only the ding.</summary>
        public void Call() => _call = true;

        /// <summary>The bell push inside the car (L6169–L6175).</summary>
        public void Bell() => _bell = true;

        public override void Link(MechanismLinker link) => _load = link.Read<ILoad>(_p.Load)
            ?? throw new InvalidOperationException(Id + " needs a Load.");

        public override void Reset(in Checkpoint cp)
        {
            H = _p.Top;                                                                           // "sent up: he calls it down", L5919
            Init((int)DumbwaiterState.Top);
            _t = 0;
            _caught = _call = _bell = false;
            InitFloor(H);
        }

        public override void Step(in StepContext ctx)
        {
            double dt = ctx.Dt, h = H;
            var pl = ctx.Player;
            bool atStop = State == DumbwaiterState.Top || State == DumbwaiterState.Bottom;
            // The acts (#4).
            if (_call && State == DumbwaiterState.Top) { Enter(ctx, (int)DumbwaiterState.Down); _t = 0; }   // L6146
            else if (_bell && atStop)
            {
                double n = _load.Load;
                if (State == DumbwaiterState.Top) { Enter(ctx, (int)DumbwaiterState.Down); _t = 0; }       // L6172
                else if (n > _p.Need) Emit(ctx, (int)DumbwaiterEvent.Over, 0, n);                           // L6173
                else if (n < _p.Need) { Enter(ctx, (int)DumbwaiterState.Shoot); _t = 0; }                   // L6174
                else { Enter(ctx, (int)DumbwaiterState.Rise); _t = 0; }                                     // L6175
            }
            _call = _bell = false;
            bool rideFrom = Moving && pl.X >= _p.X0 && pl.X <= _p.X1 && Math.Abs(pl.Y - h) < _p.RideTolerance;

            // updateAtt3 (#7).
            _t += dt;                                                                             // L6235
            double floor = _p.Floor, top = _p.Top;
            switch (State)
            {
                case DumbwaiterState.Rise:
                    h = floor + (top - floor) * Smooth.Step(Math.Min(1, _t / _p.TravelTime));        // L6236
                    if (Reached(_t, _p.TravelTime)) { Enter(ctx, (int)DumbwaiterState.Top); h = top; Emit(ctx, (int)DumbwaiterEvent.Arrive, 0); }
                    break;
                case DumbwaiterState.Down:
                    h = top - (top - floor) * Smooth.Step(Math.Min(1, _t / _p.TravelTime));          // L6237
                    if (Reached(_t, _p.TravelTime)) { Enter(ctx, (int)DumbwaiterState.Bottom); h = floor; Emit(ctx, (int)DumbwaiterEvent.Arrive, 1); }
                    break;
                case DumbwaiterState.Shoot:
                    if (!Reached(_t, _p.ShootUp)) h = floor + _p.ShootPeak * Math.Min(1, Math.Pow(_t / _p.ShootUp, _p.ShootPower));   // L6240
                    else if (!_caught) { _caught = true; Emit(ctx, (int)DumbwaiterEvent.CatchBite); }                                 // L6241
                    if (After(_t, _p.LowerFrom)) h = floor + _p.ShootPeak * (1 - Smooth.Step((_t - _p.LowerFrom) / _p.LowerOver));    // L6242
                    if (After(_t, _p.ShootEnd)) { Enter(ctx, (int)DumbwaiterState.Bottom); h = floor; _caught = false; Emit(ctx, (int)DumbwaiterEvent.Arrive, 1); }   // L6244
                    break;
            }
            H = h;
            MoveFloor(ctx, h);
            Carrying = rideFrom;
        }

        protected override void WriteLift(ISnapshotWriter w)
        {
            w.WriteDouble("h", H);
            w.WriteDouble("t", _t);
            w.WriteBool("caught", _caught);
            w.WriteBool("call", _call);
            w.WriteBool("bell", _bell);
        }

        protected override void ReadLift(ISnapshotReader r)
        {
            H = r.ReadDouble("h");
            _t = r.ReadDouble("t");
            _caught = r.ReadBool("caught");
            _call = r.ReadBool("call");
            _bell = r.ReadBool("bell");
        }
    }
}
