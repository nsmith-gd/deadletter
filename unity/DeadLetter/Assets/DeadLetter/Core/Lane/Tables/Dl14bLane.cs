using System;
using DeadLetter.Core.Mechanisms;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-14b Unaccompanied's lane: region 6 from 263 to DL-15 (278): the night corridor (flat), the stair up to the sick
    /// bay's door (walked as a slope, 9 treads to 1.6) and its landing, and the sick bay's wall, which he passes only from
    /// the landing. Lines are index.html at 7b3c123 (<c>ATT3</c> L5897–L5900, <c>floorAtt3</c> L5947–L5953,
    /// <c>limitsAtt3</c> L5958–L5961, <c>onRamp</c> L6351).
    /// </summary>
    public static class Dl14bLane
    {
        public const int Region = 6;

        /// <summary><c>ATT3.stair</c>, <c>landing</c>, <c>wall15</c> (L5900).</summary>
        public const double StairX0 = 275.3, StairX1 = 277.6, StairH = 1.6, LandingX0 = 277.6, LandingX1 = 278.0, LandingH = 1.6;
        public const double Wall15X0 = 278.0, Wall15X1 = 278.15;
        /// <summary>Below this the sick bay's wall stands (<c>y &lt; 1.45</c>, L5958); its far side holds him to 294, its near side from 274.</summary>
        public const double WallBelowY = 1.45, WallFarTo = 294, WallNearFrom = 274;

        /// <summary>The static lane of region 6 around DL-14b: the landing, and the stair as a ramp (<c>onRamp</c>: x0 − 0.2 to x1 + 0.1).</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-14b (region 6)",
            Left = Dl12Lane.Left, Right = Dl12Lane.Right,
            Floor = 0,
            Floors = new[] { new LaneSpan(LandingX0, LandingX1, LandingH, SpanEdges.ClosedOpen) },                 // L5950
            Ramps = new[] { new LaneSpan(StairX0 - 0.2, StairX1 + 0.1, 0, SpanEdges.ClosedOpen) },                // L6351
            Ceiling = Dl12Lane.Ceiling,
        };

        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new Dl14bStairFloor(),
            new Dl14bWallLane(),
        };
    }

    /// <summary>The stair up to the sick bay, walked as a slope (<c>floorAtt3</c>, L5949; the 23 Oct playtest): 0 to 1.6 over [275.3, 277.6).</summary>
    public sealed class Dl14bStairFloor : LaneContributor
    {
        public override double Floor(double x, double floor)
            => x >= Dl14bLane.StairX0 && x < Dl14bLane.StairX1 ? Dl14bLane.StairH * (x - Dl14bLane.StairX0) / (Dl14bLane.StairX1 - Dl14bLane.StairX0) : floor;
    }

    /// <summary>The sick bay's wall (<c>limitsAtt3</c>, L5958–L5961): below 1.45, past it he stays HALF clear of its far face, and before it HALF short.</summary>
    public sealed class Dl14bWallLane : LaneContributor
    {
        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (!(y < Dl14bLane.WallBelowY)) return;
            if (x >= Dl14bLane.Wall15X0 && x < Dl14bLane.WallFarTo) left = Math.Max(left, Dl14bLane.Wall15X1 + Dl12Lane.Half);
            else if (x > Dl14bLane.WallNearFrom && x < Dl14bLane.Wall15X0) right = Math.Min(right, Dl14bLane.Wall15X0 - Dl12Lane.Half);
        }
    }
}
