using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Bridges;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-01 The Wake's lane: region 1, x −0.3 to 11.45 (port_architecture §0.3, §4.6). Lines are index.html at 7b3c123.
    /// <para>The pattern for every scene (DL-02 … DL-17 add a class like this one): a <see cref="Table"/> of the static
    /// lane with every value resolved and cited, and one factory per moving contributor that adapts the scene's
    /// mechanisms (<see cref="Contributors"/>). The scene definition registers both on its region.</para>
    /// </summary>
    public static class Dl01Lane
    {
        public const int Region = 1;

        /// <summary><c>LEFT_LIMIT</c>, <c>RIGHT_LIMIT</c>, <c>LOCKED_LIMIT</c>, L303.</summary>
        public const double Left = -0.3, Right = 11.45, LockedRight = 3.02;
        /// <summary><c>PIT</c> (the drain trench), L283.</summary>
        public const double PitX0 = 6.6, PitX1 = 8.0, PitY = -0.8;
        /// <summary><c>STEP</c> (the fallen conveyor, the first hop), L281; in <c>PLATFORMS</c>, L295.</summary>
        public const double StepX0 = 3.6, StepX1 = 4.4, StepH = 0.22;
        /// <summary>The depot's roof: 2.45 left of x 2.6, 4 from there (<c>ceilingAt</c>, L1632).</summary>
        public const double LowCeiling = 2.45, LowCeilingTo = 2.6, Ceiling = 4;
        /// <summary><c>SHUTTER_PATH</c> and <c>SHUTTER_PIVOT</c>, L275–L276: the shutter's lower edge at angle 0.</summary>
        public static readonly double[] ShutterPath = { 0.2, 1.6, 2.0, 0.62, 3.2, 0.6, 3.4, 0.02 };
        public const double ShutterPivotX = 0.2, ShutterPivotY = 1.6;
        /// <summary>The cart counts as a box only for 4 &lt; x &lt; <c>SH.x1</c> + 0.4 = 25.4 (<c>surfaceCh1</c>, L4145; <c>SH.x1</c> L3887).</summary>
        public const double CartWindowX0 = 4, CartWindowX1 = 25.0 + 0.4;

        /// <summary>The static lane of region 1.</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-01 (region 1)",
            Left = Left, Right = Right,                                                             // leftLimit0/rightLimit0, L1757, L1765
            Floor = 0,                                                                               // floorAt, L1716
            Floors = new[] { new LaneSpan(PitX0, PitX1, PitY, SpanEdges.Open) },                    // x > PIT.x0 && x < PIT.x1, L1716
            Platforms = new[] { new LaneSpan(StepX0, StepX1, StepH, SpanEdges.Closed) },            // PLATFORMS, L1722
            Ceiling = Ceiling,                                                                       // x < 2.6 ? 2.45 : 4, L1632
            Ceilings = new[] { new LaneSpan(double.NegativeInfinity, LowCeilingTo, LowCeiling, SpanEdges.Open) },
        };

        /// <summary>
        /// The moving parts, adapted from DL-01's mechanisms: the shutter's swinging edge (<c>dl01.shutter</c>, degrees),
        /// the locked shutter's wall until <c>dl01.latch</c> releases, and the cart (<c>dl01.cart</c>) as a box, then a
        /// bridge in the trench.
        /// </summary>
        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new SwingingPathCeiling(g.Get<IPositionSource>("dl01.shutter"), ShutterPivotX, ShutterPivotY, ShutterPath),   // L1621–L1642
            new LockedWall(g.Get<IEngageable>("dl01.latch"), right: LockedRight),                                       // L1765
            new TippingBridgeLane(g.Get<TippingBridge>("dl01.cart"), TippingBridgeParams.Dl01Cart(), CartWindowX0, CartWindowX1),   // L4138, L4146
        };
    }
}
