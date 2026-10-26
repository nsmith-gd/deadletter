using System;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Plates
{
    public enum PlateDoorState { Closed, Opening, Open, Closing }

    public sealed class PlateDoorParams
    {
        /// <summary>Opens while this plate is engaged (D-17 on it) ...</summary>
        public MechanismId Plate;
        /// <summary>... or while this holds it (the seated courier). Optional.</summary>
        public MechanismId Hold;
        /// <summary>Seconds to open fully for the plate / for the hold; seconds to close (L4815).</summary>
        public double OpenTime = 1.1, HoldOpenTime = 2.2, CloseTime = 0.5;
        /// <summary>Full lift, metres (L4816).</summary>
        public double Travel = 1.7;

        /// <summary>DL-04: the bay door: him on the bay plate (1.1 s) or the seated courier (2.2 s); closes in 0.5 s (L4813–L4816).</summary>
        public static PlateDoorParams Dl04BayDoor() => new PlateDoorParams { Plate = "dl04.bayPlate", Hold = "dl04.cradle" };
    }

    /// <summary>
    /// A door held open by a plate, closing when it is let off (§4.13a, DL-04 bay door, L4813–L4816). Linear both ways.
    /// Deliberate deviation: the prototype's <c>if (want &gt; door) … else close</c> also closes a step while fully
    /// open, so the open door saws 0.03 below the top; here it holds at 1. Signals: <see cref="Position"/> = lift,
    /// metres; <see cref="Engaged"/> = fully open.
    /// </summary>
    public sealed class PlateDoor : Mechanism, IPositionSource, IEngageable
    {
        private readonly PlateDoorParams _p;
        private IEngageable _plate, _hold;

        public PlateDoor(MechanismId id, PlateDoorParams p) : base(id) { _p = p ?? throw new ArgumentNullException(nameof(p)); }

        public PlateDoorState State => (PlateDoorState)StateCode;
        /// <summary>Opening, 0..1 (<c>s.bayDoor</c>).</summary>
        public double Open01 { get; private set; }
        public double Position => _p.Travel * Open01;
        public bool Engaged => Open01 >= 1;
        /// <summary>The plate or the hold wants it open (bay lamps 5 vs 0.4, plate dip 0.01; L4817–L4823).</summary>
        public bool Want { get; private set; }

        public override void Link(MechanismLinker link)
        {
            _plate = link.Read<IEngageable>(_p.Plate) ?? throw new InvalidOperationException(Id + " needs a Plate.");
            _hold = link.Read<IEngageable>(_p.Hold);
        }

        /// <summary>Open iff the hold is engaged (the courier seated past <c>bay</c>: <c>bayDoor = 1</c>, L4097).</summary>
        public override void Reset(in Checkpoint cp)
        {
            Want = _hold != null && _hold.Engaged;
            Open01 = Want ? 1 : 0;
            Init((int)(Want ? PlateDoorState.Open : PlateDoorState.Closed));
        }

        public override void Step(in StepContext ctx)
        {
            bool held = _hold != null && _hold.Engaged;
            Want = held || _plate.Engaged;                                                                  // L4813
            double want = Want ? 1 : 0, prev = Open01;
            if (want > Open01) Open01 = Math.Min(1, Open01 + ctx.Dt / (held ? _p.HoldOpenTime : _p.OpenTime));   // L4814
            else if (want < Open01) Open01 = Math.Max(0, Open01 - ctx.Dt / _p.CloseTime);
            Enter(ctx, (int)(Open01 >= 1 ? PlateDoorState.Open : Open01 <= 0 ? PlateDoorState.Closed
                : Open01 > prev ? PlateDoorState.Opening : Open01 < prev ? PlateDoorState.Closing : State));
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("open", Open01);
            w.WriteBool("want", Want);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Open01 = r.ReadDouble("open");
            Want = r.ReadBool("want");
        }
    }
}
