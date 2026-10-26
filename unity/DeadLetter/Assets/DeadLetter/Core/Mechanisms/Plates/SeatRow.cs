using System;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Plates
{
    public enum SeatRowState { Waiting, AllSeated, Dismissed }

    public enum SeatRowEvent
    {
        /// <summary>A seat lamp lit (<c>Sound.plate</c>); Index = the seat (the last one is the sitter's chair) (L5726).</summary>
        Lamp,
        /// <summary>Dismissal: the bell, and again Value = 0.7 s later (L5731).</summary>
        Bell,
    }

    public sealed class SeatRowParams
    {
        /// <summary>Seat x's a figure docks at (lit when one stands within <see cref="Tolerance"/>, on the floor).</summary>
        public double[] Seats = Array.Empty<double>();
        public double Tolerance = 0.03;
        public MechanismId[] Figures = Array.Empty<MechanismId>();
        /// <summary>The last lamp: D-17 seated on this chair (an <see cref="IEngageable"/>).</summary>
        public MechanismId Sitter;
        /// <summary>Every lamp lit for more than this → dismissed (L5729).</summary>
        public double HoldFor = 1.6;
        public double SecondBell = 0.7;
        public string DismissedAfter;

        /// <summary>DL-15: figures A and B at 283.2 and 284.6, him on Mara's chair at 286.0, 1.6 s (ATT2.seats L5523, L5723–L5733).</summary>
        public static SeatRowParams Dl15Seats() => new SeatRowParams
        {
            Seats = new[] { 283.2, 284.6 }, Figures = new MechanismId[] { "dl15.figA", "dl15.figB" },
            Sitter = "dl15.chair", DismissedAfter = "dismissed",
        };
    }

    /// <summary>
    /// DL-15's seat plates (§4.13a, L5723–L5736): one lamp per seat a figure is docked at (on the floor, within 0.03),
    /// one for D-17 seated on the chair; all lit for 1.6 s dismisses the class (latched; the checkpoint
    /// <c>dismissed</c>, the procession and the class door follow). Signals: <see cref="Engaged"/> = dismissed (the
    /// class door is a <c>Door</c> on it, <c>DoorParams.Dl15ClassDoor</c>).
    /// </summary>
    public sealed class SeatRow : Mechanism, IEngageable
    {
        private readonly SeatRowParams _p;
        private IPlateBody[] _figures;
        private IEngageable _sitter;
        private readonly bool[] _lit;
        private double _allFor = -1;

        public SeatRow(MechanismId id, SeatRowParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            _lit = new bool[p.Seats.Length + 1];
        }

        public SeatRowState State => (SeatRowState)StateCode;
        public bool Engaged => State == SeatRowState.Dismissed;
        /// <summary>Lamp <paramref name="i"/> (seats in order, then the chair).</summary>
        public bool Lit(int i) => _lit[i];
        public int Lamps => _lit.Length;

        public override void Link(MechanismLinker link)
        {
            _figures = new IPlateBody[_p.Figures.Length];
            for (int i = 0; i < _figures.Length; i++) _figures[i] = link.Read<IPlateBody>(_p.Figures[i]);
            _sitter = link.Read<IEngageable>(_p.Sitter) ?? throw new InvalidOperationException(Id + " needs a Sitter.");
        }

        public override void Reset(in Checkpoint cp)
        {
            bool dismissed = cp.Past(_p.DismissedAfter);
            for (int i = 0; i < _lit.Length; i++) _lit[i] = false;
            if (!dismissed) for (int i = 0; i < _p.Seats.Length; i++) _lit[i] = Docked(_p.Seats[i]);
            _allFor = -1;
            Init((int)(dismissed ? SeatRowState.Dismissed : SeatRowState.Waiting));
        }

        public override void Step(in StepContext ctx)
        {
            bool dismissed = Engaged, all = true;
            for (int i = 0; i < _lit.Length; i++)
            {
                bool v = i < _p.Seats.Length ? !dismissed && Docked(_p.Seats[i]) : _sitter.Engaged;      // L5724–L5725
                if (v && !_lit[i]) Emit(ctx, (int)SeatRowEvent.Lamp, i);
                _lit[i] = v;
                all &= v;
            }
            if (dismissed) return;
            _allFor = all ? (_allFor < 0 ? 0 : _allFor + ctx.Dt) : -1;                                    // L5728
            if (_allFor > _p.HoldFor)                                                                       // L5729
            {
                Enter(ctx, (int)SeatRowState.Dismissed);
                Emit(ctx, (int)SeatRowEvent.Bell, 0, _p.SecondBell);
            }
            else Enter(ctx, (int)(all ? SeatRowState.AllSeated : SeatRowState.Waiting));
        }

        /// <summary>A figure is docked at x: free on the floor (base &lt; 0.05), within the tolerance (L5724).</summary>
        private bool Docked(double x)
        {
            for (int i = 0; i < _figures.Length; i++)
            {
                var f = _figures[i];
                if ((f.Support == BodySupport.Floor || f.Support == BodySupport.Pushed) && Math.Abs(f.X - x) < _p.Tolerance) return true;
            }
            return false;
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            for (int i = 0; i < _lit.Length; i++) w.WriteBool(LitKeys[i], _lit[i]);
            w.WriteDouble("allFor", _allFor);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            for (int i = 0; i < _lit.Length; i++) _lit[i] = r.ReadBool(LitKeys[i]);
            _allFor = r.ReadDouble("allFor");
        }

        private static readonly string[] LitKeys = { "lit0", "lit1", "lit2", "lit3", "lit4", "lit5", "lit6", "lit7" };
    }
}
