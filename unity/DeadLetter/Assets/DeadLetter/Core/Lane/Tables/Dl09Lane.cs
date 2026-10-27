using System;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Lifts;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-09 The Slipping Cage's lane: region 4 (80.75 → 127.9, §0.3) from <c>CG.x0</c> 97.6, the top of DL-08's returns
    /// belt, to <c>UPONLY.x0</c> 118.8, where DL-10 begins (<c>sceneName</c>, L8142). Lines are index.html at 7b3c123.
    /// <para>The static lane: the deck at <c>GALLERY.h</c> 1.6 (<c>floorAt</c>: past <c>CORRIDOR_X0</c> the floor is
    /// <c>game.upper ? GALLERY.h : 0</c>, L1717, and <c>game.upper</c> holds from <c>landing</c> to <c>school</c>, which takes in
    /// every state of region 4); the three climbs to the upper landing, 2.2, 2.8 and 3.4 (<c>CG.climbs</c>, ends inclusive,
    /// <c>surfaceCh1</c> L4159); the hall's ceiling 6.5 (<c>ceilingAt</c>, L1629) and the antechamber's 3.3 between the shaft
    /// and the tunnel mouth (<c>CG.anteCeil</c>, open ends, <c>ceilingCh1</c> L4166, which overrides it); the walls
    /// <c>DOOR4_X − 0.6</c> and <c>REGION5_X + 1</c> (<c>leftLimit0</c>/<c>rightLimit0</c>, L1764, L1769: the left one is DL-08's
    /// platform wall while it is unlatched, which is never once he is here).</para>
    /// <para>The moving parts (<see cref="Contributors"/>): the cage's floor in the shaft and its walls (<see cref="CageShaftLane"/>,
    /// L4138, L4182–L4189), and the plates where they lie (<see cref="PlateLane"/>, L4152).</para>
    /// </summary>
    public static class Dl09Lane
    {
        public const int Region = 4;

        /// <summary><c>OFF3</c>, <c>OFF4</c>, <c>OFF5</c> (L274).</summary>
        public const double Off3 = 33, Off4 = 42, Off5 = 54;
        /// <summary><c>DECK</c> (L3007) = <c>GALLERY.h</c> = <c>CG.landing</c>; <c>CG.top</c> (L3900).</summary>
        public const double Deck = 1.6, Top = 3.4;
        /// <summary><c>CG.x0</c> (L3899): DL-09 begins (<c>sceneName</c>, L8142).</summary>
        public const double X0 = Off3 + 64.6;
        /// <summary><c>UPONLY.x0</c> (L3455): DL-10 begins.</summary>
        public const double X1 = Off4 + 76.8;
        /// <summary><c>CG.climbs</c> (L3899): [x0, x1, top], ends inclusive.</summary>
        public const double Climb1X0 = Off3 + 65.8, Climb1X1 = Off3 + 66.4, Climb1H = 2.2,
            Climb2X0 = Off3 + 66.4, Climb2X1 = Off3 + 67.2, Climb2H = 2.8,
            Climb3X0 = Off3 + 67.2, Climb3X1 = Off3 + 68.2, Climb3H = 3.4;
        /// <summary><c>CG.shaft</c> (L3900): the cage's shaft, open ends.</summary>
        public const double ShaftX0 = Off3 + 68.2, ShaftX1 = Off3 + 69.8;
        /// <summary><c>CG.anteCeil</c> (L3900) under the antechamber, from the shaft to the tunnel mouth (<c>OFF4 + 64.6</c>, L4166).</summary>
        public const double AnteCeiling = 3.3, TunnelX0 = Off4 + 64.6, HallCeiling = 6.5;
        /// <summary><c>DOOR4_X − 0.6</c> (L3007, L1764) and <c>REGION5_X + 1</c> (L3446, L1769).</summary>
        public const double Left = Off3 + 47.5 - 0.6, Right = Off5 + 73.9 + 1;
        /// <summary><c>HALF</c> (L310).</summary>
        public const double Half = Dl03Lane.Half;

        /// <summary>DL-09's static lane.</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-09 (region 4, the cage)",
            Left = Left, Right = Right,                                                                // L1764, L1769
            Floor = Deck,                                                                              // game.upper ? GALLERY.h : 0, L1717
            Platforms = new[]                                                                          // CG.climbs, x >= a && x <= b (L4159)
            {
                new LaneSpan(Climb1X0, Climb1X1, Climb1H, SpanEdges.Closed),
                new LaneSpan(Climb2X0, Climb2X1, Climb2H, SpanEdges.Closed),
                new LaneSpan(Climb3X0, Climb3X1, Climb3H, SpanEdges.Closed),
            },
            Ceiling = HallCeiling,                                                                     // L1629
            Ceilings = new[] { new LaneSpan(ShaftX1, TunnelX0, AnteCeiling, SpanEdges.Open) },        // L4166
        };

        /// <summary>The cage (<c>dl09.cage</c>) and the plates (<c>dl09.plate0</c>, <c>dl09.plate1</c>).</summary>
        public static ILaneContributor[] Contributors(MechanismGraph g)
        {
            var cage = g.Get<SlippingCage>("dl09.cage");
            return new ILaneContributor[]
            {
                new CageShaftLane(cage),
                new PlateLane(g.Get<CarriedItem>("dl09.plate0"), cage),
                new PlateLane(g.Get<CarriedItem>("dl09.plate1"), cage),
            };
        }
    }

    /// <summary>
    /// The slipping cage in the lane (<c>dl09.cage</c>): its floor is the shaft's (<c>c.y</c> for x inside the shaft, open
    /// ends, <c>floorCh1</c> L4138), and its walls (<c>limitsCh1</c>, L4182–L4189): on the upper landing he cannot step
    /// toward the shaft unless the cage stands at the top (within 0.05); in the shaft its sides hold him, the left one
    /// unless it is at the top, the right one unless it is caught at the landing (within 0.02); past the shaft, under the
    /// antechamber, he cannot step back into it (<c>CG.shaft.x1 − 0.1</c>).
    /// </summary>
    public sealed class CageShaftLane : LaneContributor
    {
        /// <summary>The walls' slack: in the shaft for walls within 0.05 of it; at the top within 0.05, held within 0.02; the landing's wall only above 3.1 (L4183–L4189).</summary>
        public const double ShaftSlack = 0.05, AtTop = 0.05, AtLanding = 0.02, UpperBand = 0.3, LandingEdge = 0.02, AnteBack = 0.1;

        private readonly SlippingCage _cage;

        public CageShaftLane(SlippingCage cage) { _cage = cage ?? throw new ArgumentNullException(nameof(cage)); }

        public override double Floor(double x, double floor)
            => x > Dl09Lane.ShaftX0 && x < Dl09Lane.ShaftX1 ? _cage.Y : floor;                                  // L4138

        public override void Limits(double x, double y, ref double left, ref double right)
        {
            double cy = _cage.Y;
            bool inShaft = x > Dl09Lane.ShaftX0 - ShaftSlack && x < Dl09Lane.ShaftX1 + ShaftSlack;             // L4183
            bool atTop = !(Math.Abs(cy - Dl09Lane.Top) > AtTop);
            if (!inShaft && x < Dl09Lane.ShaftX0 && y > Dl09Lane.Top - UpperBand && !atTop)
                right = Math.Min(right, Dl09Lane.ShaftX0 - Dl09Lane.Half + LandingEdge);                     // L4184
            if (inShaft)
            {
                if (!atTop) left = Math.Max(left, Dl09Lane.ShaftX0 + Dl09Lane.Half);                          // L4186
                if (!(_cage.State == SlippingCageState.Caught && Math.Abs(cy - Dl09Lane.Deck) < AtLanding))
                    right = Math.Min(right, Dl09Lane.ShaftX1 - Dl09Lane.Half);                                 // L4187
            }
            if (x > Dl09Lane.ShaftX1 && x < Dl09Lane.TunnelX0) left = Math.Max(left, Dl09Lane.ShaftX1 - AnteBack);   // L4189
        }
    }

    /// <summary>
    /// A cage plate lying in the lane (<c>surfaceCh1</c>, L4152): standable to its base + 0.21 within 0.06 of its x, but
    /// only where the surface below it (the floor, before the climbs: the prototype tests the plates before
    /// <c>CG.climbs</c>, L4152, L4159) is within 0.05 of its base. On the upper landing, where they start, the floor under
    /// them is the deck, 1.8 below their base: they are not solid there.
    /// </summary>
    public sealed class PlateLane : LaneContributor
    {
        public const double Reach = 0.06, Height = 0.21, Level = 0.05;

        private readonly CarriedItem _plate;
        private readonly SlippingCage _cage;

        public PlateLane(CarriedItem plate, SlippingCage cage)
        {
            _plate = plate ?? throw new ArgumentNullException(nameof(plate));
            _cage = cage ?? throw new ArgumentNullException(nameof(cage));
        }

        public override double Surface(double x, double surface)
        {
            if (_plate.State != ItemState.Floor || !(Math.Abs(x - _plate.X) <= Reach)) return surface;
            double below = x > Dl09Lane.ShaftX0 && x < Dl09Lane.ShaftX1 ? _cage.Y : Dl09Lane.Deck;              // floorAt (L4138, L1717)
            return Math.Abs(below - _plate.BaseY) < Level ? Math.Max(surface, _plate.BaseY + Height) : surface;
        }
    }
}
