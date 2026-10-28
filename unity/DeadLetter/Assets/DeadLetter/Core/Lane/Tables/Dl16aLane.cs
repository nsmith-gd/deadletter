using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Lifts;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-16a Her Way Round's lane: region 6 from 310 to DL-17 (324): the servery, the dumbwaiter's car (its floor, to
    /// someone no more than 0.35 below it), the gate to pupils on the floor, the passage over it (2.4, to someone up there)
    /// and the stair down from it, walked as a slope. Lines are index.html at 7b3c123 (<c>ATT3</c> L5901–L5904,
    /// <c>surfaceAtt3</c> L5942–L5943, <c>floorAtt3</c> L5951, <c>limitsAtt3</c> L5963–L5967, <c>onRamp</c> L6351).
    /// </summary>
    public static class Dl16aLane
    {
        public const int Region = 6;

        /// <summary><c>ATT3.car</c> (L5903): the car's span; standable from 0.35 below its floor, up to the passage.</summary>
        public const double CarX0 = 312.6, CarX1 = 313.4, CarBelow = 0.35;
        /// <summary><c>ATT3.passage</c>, <c>stair16a</c> (L5903): the passage over the gate and the stair down to the workshop.</summary>
        public const double PassageX0 = 313.5, PassageX1 = 321.2, PassageH = 2.4, PassageMinY = 2.0;
        public const double StairX0 = 321.2, StairX1 = 323.6, StairH = 2.4;
        /// <summary><c>ATT3.gateX</c> (L5903): to anyone below 2.0, a wall from 309 to 324.5 (L5964–L5966).</summary>
        public const double GateX = 314.0, GateBelowY = 2.0, GateFrom = 309, GateTo = 324.5;
        /// <summary>While the car is up (above 0.15) its empty shaft is a wall to someone on the floor (L5967).</summary>
        public const double ShaftAbove = 0.15, ShaftBelowY = 0.3;

        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-16a (region 6)",
            Left = Dl12Lane.Left, Right = Dl12Lane.Right,
            Floor = 0,
            Ramps = new[] { new LaneSpan(StairX0 - 0.1, StairX1 + 0.2, 0, SpanEdges.ClosedOpen) },                  // L6351
            Ceiling = Dl12Lane.Ceiling,
        };

        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new Dl16aLaneParts(g.Get<Dumbwaiter>("dl16a.car")),
        };
    }

    /// <summary>The car and the passage by his height, the stair down, the gate and the empty shaft (L5942–L5943, L5951, L5963–L5967).</summary>
    public sealed class Dl16aLaneParts : LaneContributor, ILaneHeightContributor
    {
        private readonly Dumbwaiter _car;

        public Dl16aLaneParts(Dumbwaiter car) { _car = car ?? throw new ArgumentNullException(nameof(car)); }

        public override double Floor(double x, double floor)
            => x >= Dl16aLane.StairX0 && x < Dl16aLane.StairX1 ? Dl16aLane.StairH * (1 - (x - Dl16aLane.StairX0) / (Dl16aLane.StairX1 - Dl16aLane.StairX0)) : floor;

        public double Surface(double x, double refY, double surface)
        {
            double h = _car.H;
            if (x >= Dl16aLane.CarX0 && x < Dl16aLane.PassageX0 && refY > h - Dl16aLane.CarBelow) surface = Math.Max(surface, h);             // L5942
            if (refY > Dl16aLane.PassageMinY && x >= Dl16aLane.PassageX0 && x <= Dl16aLane.PassageX1) surface = Math.Max(surface, Dl16aLane.PassageH);   // L5943
            return surface;
        }

        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (!(y < Dl16aLane.GateBelowY)) return;
            if (x < Dl16aLane.GateX && x > Dl16aLane.GateFrom) right = Math.Min(right, Dl16aLane.GateX - 0.05 - Dl12Lane.Half);
            else if (x >= Dl16aLane.GateX && x < Dl16aLane.GateTo) left = Math.Max(left, Dl16aLane.GateX + 0.05 + Dl12Lane.Half);
            if (_car.H > Dl16aLane.ShaftAbove && y < Dl16aLane.ShaftBelowY && x < Dl16aLane.CarX0) right = Math.Min(right, Dl16aLane.CarX0 - 0.1 - Dl12Lane.Half);
        }
    }
}
