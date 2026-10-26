using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Water
{
    public enum FloatLatchState { Down, Latched }

    public enum FloatLatchEvent
    {
        /// <summary>The float lifts the latch home: clank and creak (L6258).</summary>
        Clank,
    }

    public sealed class FloatLatchParams
    {
        /// <summary>The float's bed (an <see cref="IPositionSource"/>, water 0..1): a <see cref="SluiceRig"/>. Must step first.</summary>
        public MechanismId Source;
        /// <summary>Latches once the bed holds this much (L6258).</summary>
        public double Threshold = 0.95;
        /// <summary>Once latched it swings fully home over this long (<c>d.latch + dt / 0.8</c>, L6259).</summary>
        public double LiftTime = 0.8;
        /// <summary>The latch arm's full swing, degrees, and its share of the bed's level before and after latching (L6314).</summary>
        public double SwingDeg = 70, LiftBefore = 0.7, LiftAfter = 0.85;
        /// <summary>
        /// Checkpoint from which it starts latched. DL-17: none, as the prototype: <c>latched</c> lives on the per-reset
        /// <c>f17</c> (L5552) and is never derived (L5923).
        /// </summary>
        public string LatchedAfter;

        /// <summary>DL-17: bed 1's float lifts the latch that holds the stair door (§4.13c <c>dl17.floatLatch</c>; L6258–L6259, L6314).</summary>
        public static FloatLatchParams Dl17Latch() => new FloatLatchParams { Source = "dl17.rig" };
    }

    /// <summary>
    /// A latch lifted by a float (§4.13c, §4.13i): its arm rises with the water (a shared run lifts it part-way and lets it
    /// fall again), and once the bed holds <see cref="FloatLatchParams.Threshold"/> it latches for good and swings fully home
    /// (DL-17, L6258–L6259, L6314). Unlike <see cref="Catches.Latch"/>'s threshold mode, its arm follows the water before it
    /// latches. Signals: <see cref="Engaged"/> = latched (the stair door's trigger, <c>DoorParams.Dl17StairDoor</c>).
    /// </summary>
    public sealed class FloatLatch : Mechanism, IEngageable
    {
        private readonly FloatLatchParams _p;
        private IPositionSource _src;

        public FloatLatch(MechanismId id, FloatLatchParams p) : base(id) { _p = p; }

        public FloatLatchState State => (FloatLatchState)StateCode;
        public bool Engaged => State == FloatLatchState.Latched;
        /// <summary>How far it has swung home since it latched, 0..1 (<c>d.latch</c>).</summary>
        public double Lift { get; private set; }
        /// <summary>The latch arm's angle, degrees (L6314).</summary>
        public double ArmDeg { get; private set; }

        public override void Link(MechanismLinker link) => _src = link.Read<IPositionSource>(_p.Source)
            ?? throw new InvalidOperationException(Id + " needs a Source.");

        public override void Reset(in Checkpoint cp)
        {
            bool latched = cp.Past(_p.LatchedAfter);
            Init((int)(latched ? FloatLatchState.Latched : FloatLatchState.Down));
            Lift = latched ? 1 : 0;                                                       // L5923
            ArmDeg = Angle();
        }

        public override void Step(in StepContext ctx)
        {
            if (State == FloatLatchState.Down && _src.Position >= _p.Threshold)            // L6258
            {
                Enter(ctx, (int)FloatLatchState.Latched);
                Emit(ctx, (int)FloatLatchEvent.Clank);
            }
            if (Engaged) Lift = Math.Min(1, Lift + ctx.Dt / _p.LiftTime);                  // L6259
            ArmDeg = Angle();
        }

        private double Angle()
        {
            double bed = _src.Position;                                                    // L6314
            return _p.SwingDeg * Smooth.Step(Engaged ? Math.Max(Lift, _p.LiftAfter * bed) : _p.LiftBefore * bed);
        }

        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("lift", Lift);
            w.WriteDouble("deg", ArmDeg);
        }

        protected override void ReadFields(ISnapshotReader r)
        {
            Lift = r.ReadDouble("lift");
            ArmDeg = r.ReadDouble("deg");
        }
    }
}
