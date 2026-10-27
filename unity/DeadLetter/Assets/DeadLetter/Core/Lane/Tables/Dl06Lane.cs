using DeadLetter.Core.Carry;
using DeadLetter.Core.Mechanisms;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-06 Return to Sender's lane: region 3 (60.3 → 80.75, §0.3) on the sorting floor (<c>!game.upper</c>), from the
    /// scanner corridor to the pit's rail. Lines are index.html at 7b3c123.
    /// <para>The static lane: the floor at 0 past <c>CORRIDOR_X0</c> (<c>floorAt</c>, L1717); the walls
    /// <c>REGION3_X − 0.15</c> and <c>FLOOR3_X1 − 0.25</c> (<c>leftLimit0</c>/<c>rightLimit0</c>, L1759, L1765); the
    /// corridor's ceiling 2.4 up to <c>OFF3 + 30.0</c>, then the hall's 6.5 (<c>ceilingAt</c>, L1629). Nothing in
    /// <c>PLATFORMS</c> or <c>floorCh1</c>/<c>ceilingCh1</c>/<c>limitsCh1</c> applies down here.</para>
    /// <para>The carriers add nothing: they run on a rail behind the lane (<c>RAIL_Z</c> −0.55, L2457) and no probe reads them
    /// (<c>surfaceAt</c>, L1719–L1735); he is on one only by riding it (<see cref="Mechanisms.Routes.CarrierLine"/>). What is
    /// solid on the floor is DL-07's two sorting weights by the dock and the tip (<c>HP.weights</c> 64.6, 69.05, L3893):
    /// 0.22 high within 0.1 of their x while they lie there (<c>surfaceCh1</c>, L4154; <see cref="Contributors"/>).</para>
    /// <para>DL-07 shares this floor and adds the gallery (<c>game.upper</c>: floor <c>GALLERY.h</c> 1.6, walls
    /// <c>GALLERY.x0 + 0.15</c> and <c>REGION4_X + 1</c>, its gate and collapse, L1717, L1759, L1765, L4179–L4181), which is
    /// not here.</para>
    /// </summary>
    public static class Dl06Lane
    {
        public const int Region = 3;

        /// <summary><c>OFF3</c> (L274).</summary>
        public const double Off3 = 33;
        /// <summary><c>CORRIDOR_X0</c>, <c>REGION3_X</c>, <c>FLOOR3_X1</c> (L2457).</summary>
        public const double CorridorX0 = Off3 + 26.9, Region3X = Off3 + 27.3, Floor3X1 = Off3 + 36.4;
        /// <summary>Walls on the floor: <c>REGION3_X − 0.15</c>, <c>FLOOR3_X1 − 0.25</c> (L1759, L1765).</summary>
        public const double Left = Region3X - 0.15, Right = Floor3X1 - 0.25;
        /// <summary>The corridor's ceiling to <c>OFF3 + 30.0</c>, the sorting hall's beyond (L1629).</summary>
        public const double CorridorX1 = Off3 + 30.0, CorridorCeiling = 2.4, HallCeiling = 6.5;
        /// <summary>The sorting weights (<c>HP.weights</c>, L3893; <c>WEIGHT_R</c>, <c>WEIGHT_H</c>, L320).</summary>
        public const double Weight0X = Off3 + 31.6, Weight1X = Off3 + 36.05, WeightR = 0.1, WeightH = 0.22;

        /// <summary>The sorting floor's static lane.</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-06 (region 3, the sorting floor)",
            Left = Left, Right = Right,                                                             // L1759, L1765
            Floor = 0,                                                                               // x > CORRIDOR_X0: 0 below the gallery, L1717
            Ceiling = HallCeiling,                                                                   // L1629
            Ceilings = new[] { new LaneSpan(CorridorX0, CorridorX1, CorridorCeiling, SpanEdges.Open) },   // x > CORRIDOR_X0 && x < OFF3 + 30.0
        };

        /// <summary>DL-07's weights (<c>dl07.weight0</c>, <c>dl07.weight1</c>), solid while they lie on the floor (L4154).</summary>
        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new CarriedItemLane(g.Get<CarriedItem>("dl07.weight0")),
            new CarriedItemLane(g.Get<CarriedItem>("dl07.weight1")),
        };
    }
}
