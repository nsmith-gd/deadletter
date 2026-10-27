using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-12 Coats Without Children's lane: region 6 (the school, <c>ATT.x0</c> 200.3 → <c>ATT.x1</c> 342.4, L294) from its
    /// arrival door to DL-13 (216): the floor, the cloakroom bench (the step up to peg 7) and the register gate, a wall
    /// while it is down. Lines are index.html at 7b3c123.
    /// <para>Region 6's ceiling is 3.4 everywhere (<c>ceilingAt</c>, L1624): no ceiling of its own at the gate.</para>
    /// </summary>
    public static class Dl12Lane
    {
        public const int Region = 6;

        /// <summary><c>ATT.x0</c>, <c>ATT.x1</c> (L294): <c>leftLimit0</c>/<c>rightLimit0</c> in region 6 (L1752, L1761), and <c>limitsAtt</c> again (L5269).</summary>
        public const double Left = 200.3, Right = 342.4;
        /// <summary><c>ceilingAt</c> in region 6 (L1624).</summary>
        public const double Ceiling = 3.4;
        /// <summary><c>ATT.bench</c> (L287): the step up to the pegs (<c>surfaceAtt</c>, L5254).</summary>
        public const double BenchX0 = 204.9, BenchX1 = 205.9, BenchH = 0.42;
        /// <summary><c>ATT.gate.x</c> (L288).</summary>
        public const double GateX = 209.4;
        /// <summary><c>HALF</c>, <c>CROUCH_H</c> (L309–L310).</summary>
        public const double Half = 0.17, CrouchH = 0.58;

        /// <summary>The static lane of region 6 around DL-12.</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-12 (region 6)",
            Left = Left, Right = Right,
            Floor = 0,                                                                              // floorAtt2's 0, L5597
            Platforms = new[] { new LaneSpan(BenchX0, BenchX1, BenchH, SpanEdges.Closed) },        // x >= bench.x0 && x <= bench.x1, L5254
            Ceiling = Ceiling,
        };

        /// <summary>
        /// The register gate (<c>dl12.gate</c>): below CROUCH_H + 0.02 a wall 0.06 + HALF either side of it for his centre
        /// (<c>limitsAtt</c>, L5270–L5271); no ceiling (it has none in region 6).
        /// </summary>
        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new FollowerGateLane(g.Get<FollowerActuator>("dl12.gate"), GateX, CrouchH + 0.02, 0, 0.06 + Half),
        };
    }
}
