using System;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Catches
{
    public enum CageCatchState
    {
        Armed,
        /// <summary>Thrown outside the window: it rattles and misses; re-armed after <see cref="CageCatchParams.RearmAfter"/>.</summary>
        Rattling,
        Bitten,
    }

    public sealed class CageCatchParams
    {
        /// <summary>The cage (an <see cref="IPositionSource"/>: its floor y, metres).</summary>
        public MechanismId Source;
        /// <summary>Bites while the source is inside [BiteMin, BiteMax], inclusive.</summary>
        public double BiteMin, BiteMax;
        /// <summary>Wall-clock 600 ms in the prototype (setTimeout, L5092); simulation seconds here.</summary>
        public double RearmAfter = 0.6;
        public string BittenAfter;

        /// <summary>DL-09: the cage's pawl, thrown with Use while it lowers or slips (L5085–L5093).</summary>
        public static CageCatchParams Dl09CagePawl() => new CageCatchParams
        {
            Source = "dl09.cage",
            BiteMin = 1.6 - 0.06, BiteMax = 1.6 + 0.45,     // CG.landing − 0.06 … + 0.45 (L5089; landing = DECK, L3900)
            BittenAfter = "landing8",                        // resetCh1: caught iff past landing8 (L4100)
        };
    }

    /// <summary>
    /// A catch thrown once by a button press during a ride (<c>dl09.cagePawl</c>): inside the window it bites (the cage
    /// then eases to the landing), outside it rattles and re-arms (L5085–L5093). The ride owner calls <see cref="Throw"/>
    /// only in the phases the prototype allows (lower, shudder, slip, stall) and <see cref="Rearm"/> when a new ride
    /// starts (<c>settle</c>, L5031). Add it before the cage; the cage reads <see cref="Engaged"/> this tick, as
    /// <c>c.phase = 'bite'</c> took effect in the same step (L5089, L5046).
    /// </summary>
    public sealed class CageCatch : Mechanism, IEngageable
    {
        private readonly CageCatchParams _p;
        private IPositionSource _source;
        private bool _throwPending, _rearmPending;
        private double _rattleT;

        public CageCatch(MechanismId id, CageCatchParams p) : base(id) { _p = p; }

        public CageCatchState State => (CageCatchState)StateCode;
        public bool Engaged => State == CageCatchState.Bitten;
        /// <summary>The prototype's <c>c.thrown</c>: the lever is over (drives the lever and dog in the view).</summary>
        public bool Thrown => State != CageCatchState.Armed;

        /// <summary>Use pressed during the ride. Ignored unless armed (<c>!c.thrown</c>, L5085).</summary>
        public void Throw() => _throwPending = true;

        /// <summary>A new ride starts: re-arm (<c>c.thrown = false</c>, L5031). A bitten catch stays bitten.</summary>
        public void Rearm() => _rearmPending = true;

        public override void Link(MechanismLinker link) => _source = link.ReadAnyOrder<IPositionSource>(_p.Source)
            ?? throw new InvalidOperationException(Id + " needs a Source.");

        public override void Reset(in Checkpoint cp)
        {
            Init((int)(cp.Past(_p.BittenAfter) ? CageCatchState.Bitten : CageCatchState.Armed));
            _throwPending = _rearmPending = false;
            _rattleT = 0;
        }

        public override void Step(in StepContext ctx)
        {
            if (_rearmPending && State == CageCatchState.Rattling) Enter(ctx, (int)CageCatchState.Armed);
            _rearmPending = false;

            if (State == CageCatchState.Rattling)
            {
                _rattleT += ctx.Dt;
                if (_rattleT >= _p.RearmAfter - 1e-9) Enter(ctx, (int)CageCatchState.Armed);   // L5092
            }

            if (_throwPending && State == CageCatchState.Armed)
            {
                double y = _source.Position;
                if (y <= _p.BiteMax && y >= _p.BiteMin) Enter(ctx, (int)CageCatchState.Bitten);   // L5089
                else { Enter(ctx, (int)CageCatchState.Rattling); _rattleT = 0; }                 // L5091
            }
            _throwPending = false;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteBool("throw", _throwPending);
            w.WriteBool("rearm", _rearmPending);
            w.WriteDouble("rattleT", _rattleT);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _throwPending = r.ReadBool("throw");
            _rearmPending = r.ReadBool("rearm");
            _rattleT = r.ReadDouble("rattleT");
        }
    }
}
