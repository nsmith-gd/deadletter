using System;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Docks
{
    public enum RackState { Empty, Partial, Full }

    public enum RackEvent
    {
        /// <summary>A figure rolled in and was taken to a hook: ratchet. Index = the figure, Value = its slot (L5753–L5756).</summary>
        Stored,
        /// <summary>Every hook is taken: the music steps out (bed off, stop over 5 s) (L5759).</summary>
        Full,
    }

    public sealed class RackParams
    {
        /// <summary>The figures it takes, in the order a reload hangs them on hooks 0, 1, ... (L5550).</summary>
        public MechanismId[] Figures = Array.Empty<MechanismId>();
        /// <summary>A figure is stored once its x reaches RackIn (− 1e-3) (L5753).</summary>
        public double RackIn;
        public int Hooks = 2;
        /// <summary>Seconds to lift a stored figure onto its hook (L5762).</summary>
        public double HangTime = 1.8;
        public string StoredAfter;

        /// <summary>DL-16: the rack at 305.6 with two hooks; full from <c>store</c> (ATT2.rackIn/hooks L5526–L5527, L5753–L5762, L5548–L5552).</summary>
        public static RackParams Dl16Rack() => new RackParams
        {
            Figures = new MechanismId[] { "dl15.figB", "dl15.figA" }, RackIn = 305.6, StoredAfter = "store",
        };
    }

    /// <summary>
    /// The DL-16 rack (§4.13b, L5744–L5766): procession figures rolling in at RackIn are taken, in arrival order, onto
    /// the hooks and lifted over 1.8 s. The procession reads <see cref="IsStored"/> (with <c>ReadAnyOrder</c>) and stops
    /// moving a stored figure. Signals: <see cref="Position"/> = hooks taken / hooks (the <c>dl16.latch</c> releases 1.2 s
    /// after it reaches 1, <c>Latch</c> with Trigger and Delay, L5764); <see cref="Engaged"/> = full.
    /// </summary>
    public sealed class Rack : Mechanism, IPositionSource, IEngageable
    {
        private readonly RackParams _p;
        private IPlateBody[] _figs;
        private readonly int[] _slot;
        private readonly double[] _hang;
        private int _stored;

        public Rack(MechanismId id, RackParams p) : base(id)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            _slot = new int[p.Figures.Length];
            _hang = new double[p.Figures.Length];
        }

        public RackState State => (RackState)StateCode;
        public int StoredCount => _stored;
        public double Position => (double)_stored / _p.Hooks;
        public bool Engaged => State == RackState.Full;
        public bool IsStored(int figure) => _slot[figure] >= 0;
        /// <summary>The hook figure <paramref name="figure"/> hangs on (−1 = not stored); hooks past the last share it (<c>min(slot, 1)</c>).</summary>
        public int HookOf(int figure) => _slot[figure] < 0 ? -1 : Math.Min(_slot[figure], _p.Hooks - 1);
        /// <summary>Its lift onto the hook, 0..1 (<c>stored.t</c>).</summary>
        public double Hang(int figure) => _hang[figure];

        public override void Link(MechanismLinker link)
        {
            _figs = new IPlateBody[_p.Figures.Length];
            for (int i = 0; i < _figs.Length; i++) _figs[i] = link.Read<IPlateBody>(_p.Figures[i]);
        }

        public override void Reset(in Checkpoint cp)
        {
            bool stored = cp.Past(_p.StoredAfter);
            for (int i = 0; i < _slot.Length; i++)
            {
                bool on = stored && i < _p.Hooks;
                _slot[i] = on ? i : -1;
                _hang[i] = on ? 1 : 0;
            }
            _stored = stored ? Math.Min(_p.Hooks, _slot.Length) : 0;
            Init((int)StateFor(_stored));
        }

        public override void Step(in StepContext ctx)
        {
            // In the procession's order, front first (sorted by x descending, L5743).
            while (true)
            {
                int next = -1;
                for (int i = 0; i < _figs.Length; i++)
                    if (_slot[i] < 0 && _figs[i].Support != BodySupport.Away && _figs[i].X >= _p.RackIn - 1e-3 && (next < 0 || _figs[i].X > _figs[next].X)) next = i;
                if (next < 0) break;
                _slot[next] = _stored++;
                Emit(ctx, (int)RackEvent.Stored, next, _slot[next]);
                if (_stored == _p.Hooks) Emit(ctx, (int)RackEvent.Full);                                   // L5759
            }
            for (int i = 0; i < _hang.Length; i++)
                if (_slot[i] >= 0 && _hang[i] < 1) _hang[i] = Math.Min(1, _hang[i] + ctx.Dt / _p.HangTime);   // L5762
            Enter(ctx, (int)StateFor(_stored));
        }

        private RackState StateFor(int n) => n >= _p.Hooks ? RackState.Full : n > 0 ? RackState.Partial : RackState.Empty;

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteLong("n", _stored);
            for (int i = 0; i < _slot.Length; i++)
            {
                w.WriteLong(SlotKeys[i], _slot[i]);
                w.WriteDouble(HangKeys[i], _hang[i]);
            }
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            _stored = (int)r.ReadLong("n");
            for (int i = 0; i < _slot.Length; i++)
            {
                _slot[i] = (int)r.ReadLong(SlotKeys[i]);
                _hang[i] = r.ReadDouble(HangKeys[i]);
            }
        }

        private static readonly string[] SlotKeys = { "slot0", "slot1", "slot2", "slot3" };
        private static readonly string[] HangKeys = { "hang0", "hang1", "hang2", "hang3" };
    }
}
