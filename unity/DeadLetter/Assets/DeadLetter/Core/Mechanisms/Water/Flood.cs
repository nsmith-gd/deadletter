using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Water
{
    public enum FloodState
    {
        /// <summary>Open water: D-17 will not step in.</summary>
        Wet,
        /// <summary>Something lies in it as a bridge: the floor over it is the bridge's top.</summary>
        Bridged,
    }

    public enum FloodEvent
    {
        /// <summary>
        /// He stepped to the water's edge: start the <c>WaterFlinch</c> act (spark and worried at f8, back to
        /// <see cref="FloodParams.BackOffset"/> before the edge, over at f29; L4511–L4516). Value = the x he backs to.
        /// Logged every step the rule holds; the act (Busy) stops it.
        /// </summary>
        TurnBack,
    }

    public sealed class FloodParams
    {
        /// <summary>The water's lane extent and its floor (below the lane floor).</summary>
        public double X0, X1, Floor;
        /// <summary>Optional: what bridges it (an <see cref="IEngageable"/>, engaged = lying in the water as a bridge).</summary>
        public MechanismId Bridge;
        /// <summary>The bridge's height above <see cref="Floor"/> once it lies there.</summary>
        public double BridgeHeight;
        /// <summary>He turns back once his leading edge passes X0: x + HALF · 0.6 &gt; X0 (HALF 0.17, L310, L4860).</summary>
        public double Lead = 0.17 * 0.6;
        /// <summary>... while on the lane floor: y &lt; 0.02 (L4860).</summary>
        public double FloorTolerance = 0.02;
        /// <summary>He backs off to X0 − 0.35 (L4861).</summary>
        public double BackOffset = 0.35;

        /// <summary>DL-11: ring C's flood (the prototype's DL-09 <c>DIP9</c>), bridged by the fallen duct, top at 0.01 (L3902–L3903, L4139, L4860).</summary>
        public static FloodParams Dl11Dip() => new FloodParams
        {
            X0 = 54 + 95.1, X1 = 54 + 96.6, Floor = -0.25,                             // OFF5 + 95.1 .. 96.6, L274, L3902
            Bridge = "dl11.duct", BridgeHeight = 0.26,                                  // DUCT9.h, L3903
        };
    }

    /// <summary>
    /// Standing water across the lane (§4.13i "Water, floods and floats"; DL-11's dip, L3902, L4139, L4860–L4862). D-17
    /// never wades: at its edge he flinches back (<see cref="FloodEvent.TurnBack"/>) unless something bridges it. The lane
    /// collision asks <see cref="FloorAt"/> for the floor over it. Signals: <see cref="Engaged"/> = bridged.
    /// </summary>
    public sealed class Flood : Mechanism, IEngageable
    {
        private readonly FloodParams _p;
        private IEngageable _bridge;

        public Flood(MechanismId id, FloodParams p) : base(id) { _p = p; }

        public FloodState State => (FloodState)StateCode;
        public bool Engaged => State == FloodState.Bridged;

        /// <summary>The floor at lane x, if x is over the water (<c>floorCh1</c>, L4139): the bridge's top or the water's floor.</summary>
        public bool FloorAt(double x, out double y)
        {
            y = 0;
            if (!(x > _p.X0 && x < _p.X1)) return false;
            y = Engaged ? _p.Floor + _p.BridgeHeight : _p.Floor;
            return true;
        }

        public override void Link(MechanismLinker link) => _bridge = link.Read<IEngageable>(_p.Bridge);

        /// <summary>Derived from the bridge (already reset: DL-11's duct is a bridge past <c>bedroom</c>, L4108).</summary>
        public override void Reset(in Checkpoint cp) => Init((int)(Bridged() ? FloodState.Bridged : FloodState.Wet));

        public override void Step(in StepContext ctx)
        {
            Enter(ctx, (int)(Bridged() ? FloodState.Bridged : FloodState.Wet));
            var pl = ctx.Player;
            if (State == FloodState.Wet && !pl.Busy && pl.Grounded && pl.X + _p.Lead > _p.X0 && pl.X < _p.X1 && pl.Y < _p.FloorTolerance)   // L4860
                Emit(ctx, (int)FloodEvent.TurnBack, 0, _p.X0 - _p.BackOffset);                                                 // L4861
        }

        private bool Bridged() => _bridge != null && _bridge.Engaged;

        protected override void WriteFields(ISnapshotWriter w) { }   // the state is written by the base
        protected override void ReadFields(ISnapshotReader r) { }
    }
}
