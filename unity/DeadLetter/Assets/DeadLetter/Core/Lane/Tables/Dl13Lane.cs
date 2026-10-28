using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Cycles;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-13 The Repeated Lesson's lane: region 6 from 216 to DL-14 (232): the front desk across the lane, the lesson's
    /// three steps (boards that fold out of the wall in turn) and the gallery they lead up to (2.05), which runs on into
    /// DL-14. Lines are index.html at 7b3c123 (<c>ATT</c> L289–L291, <c>floorAtt</c> L5244–L5251, <c>surfaceAtt</c> L5252–L5258).
    /// </summary>
    public static class Dl13Lane
    {
        public const int Region = 6;

        /// <summary><c>ATT.desk13</c> (L289): the front desk, across the lane (L5255).</summary>
        public const double DeskX0 = 219.48, DeskX1 = 219.92, DeskH = 0.52;
        /// <summary><c>ATT.gallery</c> (L291): from 227.6 the floor is the gallery's, up to the stair at 233 (L5245).</summary>
        public const double GalleryX0 = 227.6, GalleryH = 2.05, StairX0 = 233.0;

        /// <summary>The static lane of region 6 around DL-13.</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-13 (region 6)",
            Left = Dl12Lane.Left, Right = Dl12Lane.Right,
            Floor = 0,
            Floors = new[] { new LaneSpan(GalleryX0, StairX0, GalleryH, SpanEdges.ClosedOpen) },   // x >= gallery.x0 && x < stair14.x0, L5245
            Platforms = new[] { new LaneSpan(DeskX0, DeskX1, DeskH, SpanEdges.Closed) },        // L5255
            Ceiling = Dl12Lane.Ceiling,
        };

        /// <summary>The steps (<c>dl13.lesson</c>'s tracks 0–2), standable only from the level below each.</summary>
        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new Dl13StepsLane(g.Get<CycleClock>("dl13.lesson")),
        };
    }

    /// <summary>
    /// DL-13's three steps (<c>ATT.steps</c>, L290; <c>surfaceAtt</c>, L5256–L5258): step i is a board at its height over
    /// [x0, x1] (ends inclusive) while it is out (<see cref="CycleClock.IsOut"/>, <c>attOut</c>: ≥ 0.95, L5243) and only
    /// for someone whose feet are above the level below it less 0.01 (0, 0.5, 1.0): he walks under them to the brake.
    /// </summary>
    public sealed class Dl13StepsLane : LaneContributor, ILaneHeightContributor
    {
        /// <summary><c>ATT.steps</c> (L290).</summary>
        public static readonly double[] X0 = { 224.6, 225.6, 226.6 }, X1 = { 225.4, 226.4, 227.4 }, H = { 0.55, 1.05, 1.55 };
        /// <summary>The level below each (<c>up</c>, L5257).</summary>
        public static readonly double[] Up = { 0, 0.5, 1.0 };

        private readonly CycleClock _lesson;

        public Dl13StepsLane(CycleClock lesson) { _lesson = lesson ?? throw new ArgumentNullException(nameof(lesson)); }

        public double Surface(double x, double refY, double surface)
        {
            for (int i = 0; i < 3; i++)
                if (_lesson.IsOut(i) && refY > Up[i] - 0.01 && x >= X0[i] && x <= X1[i]) surface = Math.Max(surface, H[i]);
            return surface;
        }
    }
}
