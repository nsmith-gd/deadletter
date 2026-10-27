using DeadLetter.Core.Carry;
using DeadLetter.Core.Mechanisms;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-02 The Sorting Hall's lane: region 2 from the passage's doorway (x 12.2) to the gantry's sill (25.32), where
    /// DL-03 begins (port_architecture §0.3, §4.6; scene doc §3). Lines are index.html at 7b3c123. Region 2 runs on to
    /// x 60.3 (DL-03 to DL-05); this table is valid for DL-02's stretch, x &lt; 25.4, and leaves DL-03's room (its trolley,
    /// its weight, its gate) to that scene's table.
    /// <para>Region 2's collision in the prototype is <c>floorAt</c>/<c>surfaceAt</c>/<c>ceilingAt</c>/<c>leftLimit0</c>/
    /// <c>rightLimit0</c> (L1624–L1769) with <c>surfaceCh1</c>/<c>limitsCh1</c> (L4143–L4178) on top; in DL-02 that is the
    /// floor at 0, the sorting table and the gantry (<c>SH</c>, L3887–L3888), the box, a 4 m ceiling and the passage's wall.</para>
    /// </summary>
    public static class Dl02Lane
    {
        public const int Region = 2;

        /// <summary><c>SH.x0</c>, <c>SH.x1</c> (L3887): the hall; <c>sceneName</c> is DL-02 for x &lt; <c>SH.x1</c> (L8139).</summary>
        public const double X0 = 12.0, X1 = 25.0;
        /// <summary>He can't go back into the passage: <c>SH.x0 + 0.2</c> (<c>leftLimit0</c> L1760, <c>limitsCh1</c> L4174).</summary>
        public const double Left = X0 + 0.2;
        /// <summary>
        /// <c>GATE_X − 0.06 − HALF</c> (<c>rightLimit0</c> L1768; GATE_X = OFF2 + 17.6 L323, HALF L310): DL-03's gate is shut
        /// (its load is 0 from <c>room</c>, L8030–L8031) all through DL-02. Never reached from DL-02.
        /// </summary>
        public const double Right = 13 + 17.6 - 0.06 - 0.17;
        /// <summary><c>SH.table</c> (L3888): the sorting table, top 0.75, x 18.6–22.6 inclusive (L4148).</summary>
        public const double TableX0 = 18.6, TableX1 = 22.6, TableH = 0.75;
        /// <summary><c>SH.gantry.x0</c> to <c>SH.sill.x1</c> = OFF2 + 12.32 (L3888): the gantry and the doorway's sill, 1.35 (L4149).</summary>
        public const double GantryX0 = 22.4, GantryX1 = 13 + 12.32, GantryH = 1.35;
        /// <summary>The ceiling: <c>x &lt; 2.6 ? 2.45 : 4</c> applies up to ROOM_X0 = OFF2 + 12.1 (L1636, L1630, L319); DL-03's room is 2.6 high to GATE_X.</summary>
        public const double Ceiling = 4, RoomX0 = 13 + 12.1, RoomCeiling = 2.6, GateX = 13 + 17.6;
        /// <summary>The box counts only for <c>SH.x0 &lt; x &lt; SH.x1 + 0.4</c> (<c>surfaceCh1</c>, L4145–L4147).</summary>
        public const double BoxWindowX0 = X0, BoxWindowX1 = X1 + 0.4;

        /// <summary>The static lane of region 2, DL-02's stretch.</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-02 (region 2, x 12.2–25.32)",
            Left = Left, Right = Right,                                                                  // L1760, L1768, L4174
            Floor = 0,                                                                                    // floorAt, L1712–L1718
            Platforms = new[]
            {
                new LaneSpan(TableX0, TableX1, TableH, SpanEdges.Closed),                               // x >= table.x0 && x <= table.x1, L4148
                new LaneSpan(GantryX0, GantryX1, GantryH, SpanEdges.Closed),                            // x >= gantry.x0 && x <= sill.x1, L4149
            },
            Ceiling = Ceiling,                                                                            // L1636
            Ceilings = new[] { new LaneSpan(RoomX0, GateX, RoomCeiling, SpanEdges.Open) },              // x > ROOM_X0: x < GATE_X ? 2.6, L1630–L1631
        };

        /// <summary>The moving parts: the box (<c>dl02.box</c>), standable while it rests on the floor.</summary>
        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new CarriedItemLane(g.Get<CarriedItem>("dl02.box"), BoxWindowX0, BoxWindowX1),                // L4150
        };
    }
}
