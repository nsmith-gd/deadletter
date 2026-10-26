using System;
using DeadLetter.Core.Save;
using DeadLetter.Core.Simulation;

namespace DeadLetter.Core.Mechanisms.Lifts
{
    public enum PupilLiftState { Still, Descending, Ascending }

    public enum PupilLiftEvent
    {
        /// <summary>He stepped on alone at the top: the lift buzzes and stays (L5716).</summary>
        Buzz,
        /// <summary>It reached where it was going (clunk, shake 0.12; L5722).</summary>
        Arrive,
        /// <summary>A random ratchet while it moves (<c>Math.random() &lt; dt · 5</c>, L5722).</summary>
        Ratchet,
    }

    public sealed class PupilLiftParams
    {
        /// <summary>
        /// Optional (an <see cref="IEngageable"/>): a pupil stands free on the lift at its height (<c>pupil</c>, L5714).
        /// Wired by the DL-15 scene to the figures on the rail (§4.13b); None: never a pupil.
        /// </summary>
        public MechanismId Pupil;
        /// <summary>Optional (an <see cref="IEngageable"/>): a figure is still partly over its deck (<c>occupied</c>, L5719).</summary>
        public MechanismId Occupied;
        /// <summary>The deck (<c>ATT2.lift</c> x0, x1, L5521); he escorts within 0.05 of either end and 0.08 of its floor (L5715).</summary>
        public double X0, X1, EscortInset = 0.05, EscortTolerance = 0.08;
        /// <summary><c>ATT2.lift.top</c> 1.6, the floor 0, speed 0.65 m/s (L5521, L5720–L5722).</summary>
        public double Top = 1.6, Bottom = 0, Speed = 0.65;
        /// <summary>He buzzes it only near the top (<c>f15.lift &gt; 1.5</c>, L5716).</summary>
        public double BuzzAbove = 1.5;
        /// <summary>resetAtt2: down (at the bottom) past <see cref="DownAfter"/> unless past <see cref="UpAfter"/> (L5546).</summary>
        public string DownAfter, UpAfter;
        /// <summary>Ratchets per second while moving (L5722), drawn from a <see cref="SimRng"/> seeded with <see cref="Seed"/> on Reset.</summary>
        public double RatchetRate = 5;
        public ulong Seed = 0x0D15_11F7_5722UL;

        /// <summary>DL-15: the pupil lift from the sick-bay balcony (<c>ATT2.lift</c>, L5521; L5712–L5724).</summary>
        public static PupilLiftParams Dl15Lift() => new PupilLiftParams
        {
            X0 = 281.4, X1 = 282.4,
            DownAfter = "class6", UpAfter = "dismissed",
        };
    }

    /// <summary>
    /// The DL-15 pupil lift (<c>dl15.lift</c>; §4.13f "<c>dl15.pupilLift</c>"; <c>updateAtt2</c> L5711–L5724): it goes
    /// down only with a pupil AND him (the escort) aboard, back up when nobody is on it, and holds where it is while a
    /// figure is still on it without him; alone at the top he only makes it buzz.
    /// Signals: <see cref="Position"/> = its floor's y, metres (the figures ride it: <c>f.base = f15.lift</c>, L5713,
    /// read with ReadAnyOrder); <see cref="ILiftRide"/> carries him while he escorts on his feet (L5724:
    /// <c>escort &amp;&amp; game.grounded</c>, <see cref="PlayerPose.Grounded"/>).
    /// The random ratchet (L5722) draws from its own <see cref="SimRng"/>.
    /// </summary>
    public sealed class PupilLift : Lift
    {
        private readonly PupilLiftParams _p;
        private IEngageable _pupil, _occupied;
        private bool _escortWas;
        private SimRng _rng;

        public PupilLift(MechanismId id, PupilLiftParams p) : base(id) { _p = p; _rng = SimRng.Xorshift(p.Seed); }

        public PupilLiftState State => (PupilLiftState)StateCode;
        /// <summary>Its floor's y, metres (<c>f15.lift</c>).</summary>
        public override double Position => Y;
        public double Y { get; private set; }

        public override void Link(MechanismLinker link)
        {
            _pupil = link.Read<IEngageable>(_p.Pupil);
            _occupied = link.Read<IEngageable>(_p.Occupied);
        }

        public override void Reset(in Checkpoint cp)
        {
            _rng = SimRng.Xorshift(_p.Seed);   // the same checkpoint replays the same sounds and crates
            Y = cp.Past(_p.DownAfter) && !cp.Past(_p.UpAfter) ? _p.Bottom : _p.Top;                 // L5546
            _escortWas = false;
            _rng.Reseed((long)_p.Seed);
            Init((int)PupilLiftState.Still);
            InitFloor(Y);
        }

        /// <summary>He is on the deck at its floor and not in an act (<c>escort</c>, L5715).</summary>
        public bool IsEscort(in PlayerPose p, double y)
            => p.X >= _p.X0 + _p.EscortInset && p.X <= _p.X1 - _p.EscortInset && Math.Abs(p.Y - y) < _p.EscortTolerance && !p.Busy;

        public override void Step(in StepContext ctx)
        {
            double y = Y;
            bool pupil = _pupil != null && _pupil.Engaged;
            bool occupied = _occupied != null && _occupied.Engaged;
            bool escort = IsEscort(ctx.Player, y);
            if (escort && !pupil && !_escortWas && y > _p.BuzzAbove) Emit(ctx, (int)PupilLiftEvent.Buzz);   // L5716
            _escortWas = escort;
            double want = pupil && escort ? _p.Bottom : !occupied && !escort ? _p.Top : y;           // L5720
            if (want != y)
            {
                double step = _p.Speed * ctx.Dt;                                                   // L5722
                if (Math.Abs(want - y) <= step) y = want;
                else y += want > y ? step : -step;
                if (_rng.Chance(ctx.Dt * _p.RatchetRate)) Emit(ctx, (int)PupilLiftEvent.Ratchet);
                if (y == want) Emit(ctx, (int)PupilLiftEvent.Arrive);
            }
            Enter(ctx, (int)(y < Y ? PupilLiftState.Descending : y > Y ? PupilLiftState.Ascending : PupilLiftState.Still));
            Y = y;
            MoveFloor(ctx, y);
            Carrying = escort && ctx.Player.Grounded;                                             // L5724 (prev floor within 0.08)
        }

        protected override void WriteLift(ISnapshotWriter w)
        {
            w.WriteDouble("y", Y);
            w.WriteBool("escortWas", _escortWas);
            _rng.Write(w, "rng");
        }

        protected override void ReadLift(ISnapshotReader r)
        {
            Y = r.ReadDouble("y");
            _escortWas = r.ReadBool("escortWas");
            _rng.Read(r, "rng");
        }
    }
}
