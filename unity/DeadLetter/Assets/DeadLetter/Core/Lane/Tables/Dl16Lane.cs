using System;
using DeadLetter.Core.Mechanisms;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-16 After the Bell's lane: region 6 from 294 to DL-16a (310): the corridor and the well across it, bridged while
    /// the bridge is down (open, its floor is the pit's, 1.6 down, and its walls hold anyone in it), and the rack's
    /// counterweight across the lane until it is lifted out. Lines are index.html at 7b3c123 (<c>ATT2</c> L5526–L5528,
    /// <c>floorAtt2</c> L5593–L5597, <c>limitsAtt2</c> L5608–L5610).
    /// </summary>
    public static class Dl16Lane
    {
        public const int Region = 6;

        /// <summary><c>ATT2.pit</c> (L5526): the well, its floor; its walls hold anyone below −0.3 (L5610).</summary>
        public const double PitX0 = 297.9, PitX1 = 299.9, PitFloor = -1.6, PitWallsBelow = -0.3;
        /// <summary>The bridge is open (the well is a well) above this (<c>b.bridge &gt; 0.05</c>, L5596).</summary>
        public const double OpenAbove = 0.05;
        /// <summary><c>ATT2.cw</c> (L5528): across the lane until lifted (<c>cw &lt; 0.75</c>, L5608).</summary>
        public const double CwX0 = 307.8, CwX1 = 309.2;

        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-16 (region 6)",
            Left = Dl12Lane.Left, Right = Dl12Lane.Right,
            Floor = 0,
            Ceiling = Dl12Lane.Ceiling,
        };

        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new Dl16PitLane(g.Get<IPositionSource>("dl16.bridge")),
            new Dl16CounterweightLane(g.Get<IEngageable>("dl16.rackCW")),
        };
    }

    /// <summary>The well (<c>floorAtt2</c>, L5596; <c>limitsAtt2</c>, L5610): with the bridge open its floor is the pit's; down in it, its walls hold him.</summary>
    public sealed class Dl16PitLane : LaneContributor
    {
        private readonly IPositionSource _bridge;

        public Dl16PitLane(IPositionSource bridge) { _bridge = bridge ?? throw new ArgumentNullException(nameof(bridge)); }

        public override double Floor(double x, double floor)
            => _bridge.Position > Dl16Lane.OpenAbove && x > Dl16Lane.PitX0 && x < Dl16Lane.PitX1 ? Dl16Lane.PitFloor : floor;

        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (!(y < Dl16Lane.PitWallsBelow)) return;
            left = Math.Max(left, Dl16Lane.PitX0 + Dl12Lane.Half);
            right = Math.Min(right, Dl16Lane.PitX1 - Dl12Lane.Half);
        }
    }

    /// <summary>The rack's counterweight across the lane until it is clear (<c>limitsAtt2</c>, L5608).</summary>
    public sealed class Dl16CounterweightLane : LaneContributor
    {
        private readonly IEngageable _clear;

        public Dl16CounterweightLane(IEngageable clear) { _clear = clear ?? throw new ArgumentNullException(nameof(clear)); }

        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (_clear.Engaged) return;
            if (x < Dl16Lane.CwX0) right = Math.Min(right, Dl16Lane.CwX0 - Dl12Lane.Half);
            else left = Math.Max(left, Dl16Lane.CwX1 + Dl12Lane.Half);
        }
    }
}
