using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Save;
using DeadLetter.Core.Simulation;

namespace DeadLetter.Core.Mechanisms.Lifts
{
    public enum CounterweightRackState { Down, Lifting, Up }

    public enum CounterweightRackEvent
    {
        /// <summary>A random ratchet while it lifts (<c>Math.random() &lt; dt · 6</c>, L5766).</summary>
        Ratchet,
    }

    public sealed class CounterweightRackParams
    {
        /// <summary>The rack's latch (an <see cref="IEngageable"/>): once engaged, the counterweight lifts (<c>b.latched</c>, L5766).</summary>
        public MechanismId Latch;
        /// <summary>Rises <see cref="Rise"/> metres (smoothstep) over <see cref="Time"/> s (<c>ATT2.cw.lift</c> 2.0, L5528; L5766, L5839).</summary>
        public double Rise = 2.0, Time = 1.8;
        /// <summary>It blocks the lane between X0 and X1 until progress reaches <see cref="ClearAt"/> (L5608).</summary>
        public double X0, X1, ClearAt = 0.75;
        /// <summary>resetAtt2: lifted past this checkpoint (<c>cw: stored ? 1 : 0</c>, L5551).</summary>
        public string LiftedAfter;
        /// <summary>Ratchets per second while lifting (L5766), drawn from a <see cref="SimRng"/> seeded with <see cref="Seed"/> on Reset.</summary>
        public double RatchetRate = 6;
        public ulong Seed = 0x0D16_0C70_5766UL;

        /// <summary>DL-16: the rack's counterweight (<c>ATT2.cw</c>, L5528).</summary>
        public static CounterweightRackParams Dl16RackCw() => new CounterweightRackParams
        {
            Latch = "dl16.latch",
            X0 = 307.8, X1 = 309.2,
            LiftedAfter = "store",
        };
    }

    /// <summary>
    /// The DL-16 rack's counterweight (<c>dl16.rackCW</c>; §4.13f; L5766, L5608, L5839): when the rack is full its latch
    /// drops and the counterweight lifts 2.0 m out of the lane over 1.8 s. Nobody rides it.
    /// Signals: <see cref="Position"/> = its rise, metres (2.0 · smoothstep(progress), the view's height, L5839);
    /// <see cref="Engaged"/> = the lane is clear (progress ≥ 0.75; below that lane collision walls X0 … X1 off, L5608).
    /// The random ratchet while lifting (L5766) draws from its own <see cref="SimRng"/>.
    /// </summary>
    public sealed class CounterweightRack : Mechanism, IPositionSource, IEngageable
    {
        private readonly CounterweightRackParams _p;
        private IEngageable _latch;
        private SimRng _rng;

        public CounterweightRack(MechanismId id, CounterweightRackParams p) : base(id) { _p = p; _rng = SimRng.Xorshift(p.Seed); }

        public CounterweightRackState State => (CounterweightRackState)StateCode;
        /// <summary>0 … 1, linear in time (<c>b.cw</c>).</summary>
        public double Progress { get; private set; }
        /// <summary>Rise, metres.</summary>
        public double Position => _p.Rise * Smooth.Step(Progress);
        /// <summary>The lane under it is clear.</summary>
        public bool Engaged => Progress >= _p.ClearAt;

        public override void Link(MechanismLinker link) => _latch = link.Read<IEngageable>(_p.Latch)
            ?? throw new InvalidOperationException(Id + " needs a Latch.");

        public override void Reset(in Checkpoint cp)
        {
            _rng = SimRng.Xorshift(_p.Seed);   // the same checkpoint replays the same sounds and crates
            Progress = cp.Past(_p.LiftedAfter) ? 1 : 0;                                           // L5551
            _rng.Reseed((long)_p.Seed);
            Init((int)(Progress >= 1 ? CounterweightRackState.Up : CounterweightRackState.Down));
        }

        public override void Step(in StepContext ctx)
        {
            if (!_latch.Engaged || Progress >= 1) return;
            Progress = Math.Min(1, Progress + ctx.Dt / _p.Time);                                  // L5766
            Enter(ctx, (int)(Progress >= 1 ? CounterweightRackState.Up : CounterweightRackState.Lifting));
            if (_rng.Chance(ctx.Dt * _p.RatchetRate)) Emit(ctx, (int)CounterweightRackEvent.Ratchet);
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("cw", Progress);
            _rng.Write(w, "rng");
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Progress = r.ReadDouble("cw");
            _rng.Read(r, "rng");
        }
    }
}
