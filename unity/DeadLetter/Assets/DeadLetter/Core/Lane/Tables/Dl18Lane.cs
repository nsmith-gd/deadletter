using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Folding;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-18 Room for One's lane: region 7, chapter 2's set (docs/chapter2_plan.md §4 "Fixed across scenes"), game x 347.0
    /// to 361.0, heights in metres above the ring A datum (docs/scenes/DL-18_room_for_one.md §3). No prototype: values cite
    /// the scene doc's sections. The gallery and the box room are one floor at 0.0 (347.0–354.2); the landing doorway's
    /// sill lip at 354.2 is a 1.2 face, a mantle edge, and the doorway and the terrace landing beyond it are one floor at
    /// 1.2 (354.2–361.0), on into DL-19. The two leaves are contributors (<see cref="FoldingLeafLane"/>).
    /// <para>Nothing else in the room is climbable (§3 "Nothing else to climb"): the hook (1.0) by the door, the clock's
    /// bracket, the frame and the sketch are dressing, not platforms. No ceiling: the room's is not given a height in §3,
    /// and the frame's top rail (1.5) is behind his lane.</para>
    /// </summary>
    public static class Dl18Lane
    {
        /// <summary>Chapter 2 is region 7 (its own set, chapter2_plan §4).</summary>
        public const int Region = 7;

        /// <summary>The stair head, where DL-17's stair comes up onto ring A (§2 "Stair head", §3).</summary>
        public const double StairHeadX = 347.0;
        /// <summary>DL-18's end, where DL-19 begins on the terrace landing (chapter2_plan §4 table).</summary>
        public const double EndX = 361.0;
        /// <summary>The box room's door and floor (§3: door 351.4, room 351.6–354.2).</summary>
        public const double RoomDoorX = 351.4, RoomX0 = 351.6;
        /// <summary>The landing doorway's sill lip (§3, §11 <c>LandingDoor</c>: "sill is a mantle edge"), at 1.2.</summary>
        public const double SillX = 354.2, SillY = 1.2;
        /// <summary>The terrace landing (§3: 355.0–361.0 at 1.2).</summary>
        public const double LandingX0 = 355.0, LandingY = 1.2;
        /// <summary>D-17's half-width (chapter2_plan §4 "D-17's body": half-width 0.17, as chapter 1's HALF).</summary>
        public const double Half = 0.17;

        /// <summary>The static lane of DL-18's stretch.</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-18 (region 7)",
            // The stair head: the stair down is DL-17's (chapter 1's set), so his centre stops HALF in from it here.
            Left = StairHeadX + Half,
            Floor = 0,                                                                 // gallery and box room (§3)
            Floors = new[]
            {
                new LaneSpan(SillX, EndX, SillY, SpanEdges.ClosedOpen),               // doorway (sill lip at 354.2) and landing, 1.2 (§3)
            },
        };

        /// <summary>The fold bed (its top, not the heaped quilt) and the fold bench, each standable only while down on its stop.</summary>
        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new FoldingLeafLane(g.Get<FoldingLeaf>("dl18.bed"), standableBoxes: 1),
            new FoldingLeafLane(g.Get<FoldingLeaf>("dl18.bench")),
        };
    }

    /// <summary>
    /// A folding leaf in the lane (DL-18 §3 "The two leaves", §11): while it is down on its stop (<see cref="FoldingLeaf.Engaged"/>)
    /// the top of its first <c>standableBoxes</c> boxes is ground (<see cref="SweptVolumeProbe.Surface"/> in D-17's depth
    /// band); folding, unfolding, waiting or propped it is not, so he never lands on a propped leaf (§4: "it was never
    /// level"). The fold bed's second box, the quilt heaped at its foot to 0.7, is what the bench meets (§11 <c>Quilt</c>),
    /// not a step: it is soft, and as a step it would put the sill (1.2) within a 0.5 mantle of it.
    /// <para>No ceiling: <see cref="ILaneContributor.Ceiling"/> has no reference height (the lane ignores it), and
    /// <see cref="SweptVolumeProbe.Ceiling"/> needs one; a leaf that meets him stops and waits instead (it never crushes).</para>
    /// </summary>
    public sealed class FoldingLeafLane : LaneContributor
    {
        private readonly FoldingLeaf _leaf;
        private readonly Leading _boxes;

        /// <param name="standableBoxes">How many of its boxes, from the first, are ground (all by default).</param>
        public FoldingLeafLane(FoldingLeaf leaf, int standableBoxes = int.MaxValue)
        {
            _leaf = leaf ?? throw new ArgumentNullException(nameof(leaf));
            if (standableBoxes < 1) throw new ArgumentOutOfRangeException(nameof(standableBoxes));
            _boxes = new Leading(leaf, standableBoxes);
        }

        public override double Surface(double x, double surface) => SweptVolumeProbe.Surface(_boxes, _leaf.Engaged, x, surface);

        /// <summary>The leaf's first boxes only (one instance per contributor: a probe allocates nothing).</summary>
        private sealed class Leading : ISweptVolume
        {
            private readonly ISweptVolume _v;
            private readonly int _n;
            public Leading(ISweptVolume v, int n) { _v = v; _n = n; }
            public int VolumeCount => Math.Min(_n, _v.VolumeCount);
            public SweptBox Volume(int i) => _v.Volume(i);
        }
    }
}
