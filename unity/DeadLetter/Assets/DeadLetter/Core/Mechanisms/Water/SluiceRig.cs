using System;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Water
{
    public enum SluiceRigState
    {
        /// <summary>Tank full (or never run): the valve can start a run.</summary>
        Ready,
        /// <summary>Water runs from the tank through the open sluices into their beds.</summary>
        Running,
        /// <summary>After a run the tank refills from empty over <see cref="SluiceRigParams.Refill"/> seconds; the pump relay blinks (L6316).</summary>
        Refilling,
    }

    public enum SluiceRigEvent
    {
        /// <summary>The valve opened a run: ratchet and splash (L6205).</summary>
        Started,
        /// <summary>The valve was turned with the tank below <see cref="SluiceRigParams.LowTank"/>: clunk, worried (L6203).</summary>
        RefusedLow,
        /// <summary>The valve was turned with every sluice shut: clunk, groan (L6204).</summary>
        RefusedShut,
        /// <summary>The run is over; the tank starts refilling (L6254).</summary>
        Ended,
        /// <summary>The run ended and the float latch had not lifted: a failed try, for stall hints (<c>failAtt('17')</c>, L6254, L7501).</summary>
        Failed,
    }

    public sealed class SluiceRigParams
    {
        public const double Dl17ValveX = 336.55;                                   // ATT3.valveX, L5906
        public static readonly double[] Dl17SluiceX = { 337.45, 338.1, 338.8 };   // ATT3.sluices, L5906

        /// <summary>The valve (a <see cref="SluiceValve"/> or any one-step <see cref="IEngageable"/> pulse). Must step first.</summary>
        public MechanismId Valve;
        /// <summary>The sluices (each an <see cref="IEngageable"/>, engaged = open), in order. Must step first.</summary>
        public MechanismId[] Sluices;
        /// <summary>Which bed each sluice waters: <c>ATT3.feeds</c> [2, 0, 1], so A → bed 3, B → bed 1, C → bed 2 (L5905–L5906).</summary>
        public int[] Feeds = { 2, 0, 1 };
        public int BedCount = 3;
        /// <summary>A full tank runs for this long (<c>ATT3.run</c> 6, L5906).</summary>
        public double Run = 6;
        /// <summary>The tank refills from empty over this long once a run is over (<c>ATT3.refill</c> 10).</summary>
        public double Refill = 10;
        /// <summary>A bed nobody waters drains from full over this long (<c>ATT3.drain</c> 20).</summary>
        public double Drain = 20;
        /// <summary>A full run gives each of n open sluices' beds 1.06 / n (L6251): one sluice fills its bed, two never do.</summary>
        public double Overfill = 1.06;
        /// <summary>The valve refuses below this tank level (L6203).</summary>
        public double LowTank = 0.95;
        /// <summary>The bed whose float lifts the latch (bed 1 = index 0, L6258) and how far the float rises when it is full (L6311).</summary>
        public int FloatBed;
        public double FloatRise = 0.12;
        /// <summary>Optional: the float latch (an <see cref="IEngageable"/>); a run that ends with it down logs <see cref="SluiceRigEvent.Failed"/>.</summary>
        public MechanismId Latch;

        /// <summary>DL-17: Lisle's apprentice test rig (L5905–L5906, L6193–L6259).</summary>
        public static SluiceRigParams Dl17Rig() => new SluiceRigParams
        {
            Valve = "dl17.valve",
            Sluices = new MechanismId[] { "dl17.sluiceA", "dl17.sluiceB", "dl17.sluiceC" },
            Latch = "dl17.latch",
        };
    }

    /// <summary>
    /// A tank, sluices and beds (§4.13i, the "Water" permanent rule; DL-17's test rig, L6198–L6259). The valve opens a run
    /// of <see cref="SluiceRigParams.Run"/> seconds if the tank is full and a sluice is open. During the run the tank
    /// empties linearly and is shared by the sluices open at each step: each one's bed gains
    /// <c>dt / run / n · 1.06</c>. Beds that are not being watered drain over <see cref="SluiceRigParams.Drain"/> seconds;
    /// after the run the tank refills over <see cref="SluiceRigParams.Refill"/> seconds. The tank and beds always reset to
    /// full and empty (L5923: nothing about the rig is derived from a checkpoint).
    /// Signals: <see cref="Position"/> = the float bed's water (0..1), <see cref="Engaged"/> = water running.
    /// Step order: valve and sluices, then the rig, then the float latch (L6193–L6208 acts before L6247–L6259).
    /// </summary>
    public sealed class SluiceRig : Mechanism, IPositionSource, IEngageable
    {
        private readonly SluiceRigParams _p;
        private readonly double[] _beds;
        private readonly IEngageable[] _sluices;
        private IEngageable _valve, _latch;
        private double _run, _sinceRun;

        public SluiceRig(MechanismId id, SluiceRigParams p) : base(id)
        {
            _p = p;
            if (p.Sluices == null || p.Feeds == null || p.Sluices.Length != p.Feeds.Length)
                throw new ArgumentException(id + " needs one feed per sluice.");
            if (p.BedCount < 1 || p.BedCount > BedKeys.Length) throw new ArgumentException(id + ": 1 to " + BedKeys.Length + " beds.");
            _beds = new double[p.BedCount];
            _sluices = new IEngageable[p.Sluices.Length];
        }

        public SluiceRigState State => (SluiceRigState)StateCode;
        /// <summary>The float bed's water, 0..1 (what lifts the float and its latch).</summary>
        public double Position => _beds[_p.FloatBed];
        /// <summary>Water is running.</summary>
        public bool Engaged => _run > 0;
        /// <summary>Tank level, 0..1 (<c>d.tank</c>).</summary>
        public double Tank { get; private set; }
        /// <summary>Seconds of run left (<c>d.run</c>).</summary>
        public double RunLeft => _run;
        public int BedCount => _beds.Length;
        /// <summary>Bed <paramref name="b"/>'s water, 0..1 (bed 1 is index 0).</summary>
        public double Bed(int b) => _beds[b];
        /// <summary>The float's lift above its rest, metres (<c>0.12 · beds[0]</c>, L6311).</summary>
        public double FloatY => _p.FloatRise * _beds[_p.FloatBed];
        /// <summary>The pump relay blinks while the tank refills (L6316).</summary>
        public bool Refilling => State == SluiceRigState.Refilling;

        /// <summary>Bed <paramref name="b"/>'s stream is running (L6309).</summary>
        public bool Fed(int b)
        {
            if (_run <= 0) return false;
            for (int i = 0; i < _sluices.Length; i++) if (_p.Feeds[i] == b && _sluices[i].Engaged) return true;
            return false;
        }

        /// <summary>Water shows in sluice <paramref name="i"/>'s pipe (L6315).</summary>
        public bool PipeFlow(int i) => _run > 0 && _sluices[i].Engaged;

        public override void Link(MechanismLinker link)
        {
            _valve = link.Read<IEngageable>(_p.Valve);
            for (int i = 0; i < _sluices.Length; i++)
                _sluices[i] = link.Read<IEngageable>(_p.Sluices[i]) ?? throw new InvalidOperationException(Id + " needs every sluice.");
            _latch = link.ReadAnyOrder<IEngageable>(_p.Latch);                        // judged after the run, as d.latched (L6254)
        }

        public override void Reset(in Checkpoint cp)
        {
            Tank = 1;                                                                  // L5923
            _run = 0;
            _sinceRun = -1;                                                            // refillAt: null
            for (int b = 0; b < _beds.Length; b++) _beds[b] = 0;
            Init((int)SluiceRigState.Ready);
        }

        public override void Step(in StepContext ctx)
        {
            double dt = ctx.Dt;
            if (_valve != null && _valve.Engaged)                                      // L6200–L6206
            {
                if (_run > 0) { }                                                      // already running
                else if (Tank < _p.LowTank) Emit(ctx, (int)SluiceRigEvent.RefusedLow);
                else if (OpenCount() == 0) Emit(ctx, (int)SluiceRigEvent.RefusedShut);
                else { _run = _p.Run; Emit(ctx, (int)SluiceRigEvent.Started); }
            }

            if (_run > 0)                                                              // L6249–L6254
            {
                int n = OpenCount();
                double rate = 1 / _p.Run, step = Math.Min(dt, _run);
                _run -= step;
                Tank = Math.Max(0, _run / _p.Run);
                for (int i = 0; i < _sluices.Length; i++)
                {
                    if (!_sluices[i].Engaged) continue;
                    int b = _p.Feeds[i];
                    _beds[b] = Math.Min(1, _beds[b] + step * rate / Math.Max(1, n) * _p.Overfill);
                }
                if (_run <= 0)
                {
                    _run = 0;
                    _sinceRun = 0;
                    Emit(ctx, (int)SluiceRigEvent.Ended);
                    if (_latch == null || !_latch.Engaged) Emit(ctx, (int)SluiceRigEvent.Failed);
                }
            }
            else if (Tank < 1 && _sinceRun >= 0)                                       // L6255
            {
                _sinceRun += dt;
                Tank = Math.Min(1, _sinceRun / _p.Refill);
            }

            for (int b = 0; b < _beds.Length; b++)                                     // L6256–L6257: fed after the step
                if (!Fed(b)) _beds[b] = Math.Max(0, _beds[b] - dt / _p.Drain);

            Enter(ctx, (int)(_run > 0 ? SluiceRigState.Running
                : Tank < 1 && _sinceRun >= 0 ? SluiceRigState.Refilling : SluiceRigState.Ready));
        }

        private int OpenCount()
        {
            int n = 0;
            for (int i = 0; i < _sluices.Length; i++) if (_sluices[i].Engaged) n++;
            return n;
        }

        private static readonly string[] BedKeys = { "bed0", "bed1", "bed2", "bed3", "bed4", "bed5", "bed6", "bed7" };

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("tank", Tank);
            w.WriteDouble("run", _run);
            w.WriteDouble("since", _sinceRun);
            for (int b = 0; b < _beds.Length; b++) w.WriteDouble(BedKeys[b], _beds[b]);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Tank = r.ReadDouble("tank");
            _run = r.ReadDouble("run");
            _sinceRun = r.ReadDouble("since");
            for (int b = 0; b < _beds.Length; b++) _beds[b] = r.ReadDouble(BedKeys[b]);
        }
    }
}
