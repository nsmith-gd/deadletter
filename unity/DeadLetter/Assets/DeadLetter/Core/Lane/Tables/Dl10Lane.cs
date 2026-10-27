using System;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Lifts;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-10 Up Only's lane: region 4 (80.75 → 127.9, §0.3) from <c>UPONLY.x0</c> 118.8, the balcony's end, to <c>REGION5_X</c>
    /// 127.9, ring C's level under the counterweight's shaft, where region 5 (DL-11) begins (<c>sceneName</c>, L8142; L2047).
    /// Lines are index.html at 7b3c123.
    /// <para>The static lane: the deck at <c>GALLERY.h</c> 1.6 (<c>game.upper</c> holds from <c>landing</c> to <c>school</c>,
    /// L1717) up to the counterweight's shaft; past its far side ring C's bottom landing at 0 (<c>floorCh1</c>: past
    /// <c>UO.cw.x0</c>, <c>x &lt; UO.cw.x1 ? DECK − uo.d : 0</c>, L4137); the hall's ceiling 6.5 (<c>ceilingAt</c>, L1629); the
    /// walls <c>DOOR4_X − 0.6</c> and <c>REGION5_X + 1</c> (L1760, L1766).</para>
    /// <para>The moving parts (<see cref="Contributors"/>): the counterweight's floor in its shaft and DL-10's walls (the service
    /// door while it is down, the open shaft while the counterweight is down, the shaft's far wall at deck level, ring C's
    /// side below; <see cref="CounterweightShaftLane"/>, L4137, L4191–L4197), and the suitcase where it lies
    /// (<see cref="SuitcaseLane"/>, L4156–L4157).</para>
    /// </summary>
    public static class Dl10Lane
    {
        public const int Region = 4;

        /// <summary><c>OFF4</c>, <c>OFF5</c> (L274); <c>DECK</c> (L3007).</summary>
        public const double Off4 = 42, Off5 = 54, Deck = 1.6;
        /// <summary><c>UPONLY.x0</c> (L3455): DL-10 begins (<c>sceneName</c>, L8142).</summary>
        public const double X0 = Off4 + 76.8;
        /// <summary><c>REGION5_X</c> (L3446): past it he is in region 5 (L2047), DL-11's.</summary>
        public const double X1 = Off5 + 73.9;
        /// <summary><c>UO.caseX</c>, <c>UO.caseHalf</c> (L3458): the C-114 suitcase on the lane.</summary>
        public const double CaseX = Off5 + 67.3, CaseHalf = 0.16;
        /// <summary><c>UO.car</c> (L3458): the car behind the lane (three z −0.85).</summary>
        public const double CarX0 = Off5 + 70.35, CarX1 = Off5 + 71.55, CarMid = Off5 + 70.95;
        /// <summary><c>UO.upStand</c>, <c>UO.crankStand</c>, <c>UO.door</c> (L3459).</summary>
        public const double UpStand = Off5 + 69.95, CrankStand = Off5 + 72.45, Door = Off5 + 72.76;
        /// <summary><c>UO.cw</c> (L3459): the counterweight's shaft and where he stands on its footplate.</summary>
        public const double CwX0 = Off5 + 72.85, CwX1 = Off5 + 73.75, CwStand = Off5 + 73.37;
        /// <summary>The hall's ceiling (L1629); the walls (L1760, L1766).</summary>
        public const double Ceiling = 6.5, Left = Dl08Lane.Left, Right = X1 + 1;
        /// <summary><c>HALF</c> (L310).</summary>
        public const double Half = Dl03Lane.Half;

        /// <summary>
        /// The lobby's light zone, <c>uo</c> (<c>lightZoneFor</c>, L2627–L2628): in region 4's lights past <c>UPONLY.x0 − 1.0</c>, kept
        /// to <c>UPONLY.x0 − 1.4</c> once in it, its lights replace the goods hall's and the cage's (the view's, §7 of the scene doc).
        /// </summary>
        public const string LightZone = "uo";
        public const double LightZoneIn = 1.0, LightZoneKeep = 1.4;

        /// <summary>Whether region 4's lights are the lobby's at <paramref name="x"/> (<paramref name="wasIn"/>: they were last step).</summary>
        public static bool InLightZone(int region, double x, bool wasIn) => region >= Region && x > X0 - (wasIn ? LightZoneKeep : LightZoneIn);

        /// <summary>DL-10's static lane.</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-10 (region 4, the lobby)",
            Left = Left, Right = Right,                                                                // L1760, L1766
            Floor = Deck,                                                                              // game.upper ? GALLERY.h : 0, L1717
            Floors = new[] { new LaneSpan(CwX1, Right + 1, 0, SpanEdges.Closed) },                     // past the shaft: ring C, L4137
            Ceiling = Ceiling,                                                                         // L1629
        };

        /// <summary>The counterweight and the service door (<c>dl10.lift</c>, <c>dl10.serviceCrank</c>), and the suitcase (<c>dl10.case</c>).</summary>
        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new CounterweightShaftLane(g.Get<RelocationLift>("dl10.lift"), g.Get<CrankActuator>("dl10.serviceCrank")),
            new SuitcaseLane(g.Get<CarriedItem>("dl10.case")),
        };
    }

    /// <summary>
    /// The counterweight's shaft and the service door (<c>floorCh1</c> L4137, <c>limitsCh1</c> L4191–L4197): in the shaft the
    /// floor is the counterweight's top, <c>DECK − uo.d</c>. Past <c>UPONLY.x0</c>, on the deck (above <c>DECK − 0.3</c>): the
    /// service door blocks the lane until it is wound to 0.98 (<c>uo.door</c>, the crank's opening); while the counterweight
    /// is down (d &gt; 0.01) the open shaft stops him at its edge; the shaft's far wall stops him at deck level. Below the deck
    /// (on the counterweight at the bottom, or on ring C's landing) the shaft's near wall keeps him out from under the lobby.
    /// </summary>
    public sealed class CounterweightShaftLane : LaneContributor
    {
        /// <summary>The deck band (L4193), the door's open mark (L4194), the shaft's edge slack (L4195), its "down" (L4195).</summary>
        public const double DeckBand = 0.3, DoorOpen = 0.98, DoorGap = 0.01, EdgeSlack = 0.05, Down = 0.01, NearEdge = 0.1;

        private readonly RelocationLift _lift;
        private readonly CrankActuator _crank;

        public CounterweightShaftLane(RelocationLift lift, CrankActuator crank)
        {
            _lift = lift ?? throw new ArgumentNullException(nameof(lift));
            _crank = crank ?? throw new ArgumentNullException(nameof(crank));
        }

        public override double Floor(double x, double floor)
            => x > Dl10Lane.CwX0 && x < Dl10Lane.CwX1 ? _lift.CounterweightY : floor;                          // L4137

        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (!(x > Dl10Lane.X0)) return;                                                                      // L4191
            if (y > Dl10Lane.Deck - DeckBand)
            {
                if (x < Dl10Lane.Door && _crank.Position < DoorOpen) right = Math.Min(right, Dl10Lane.Door - Dl10Lane.Half - DoorGap);   // L4194
                if (x < Dl10Lane.CwX0 + NearEdge && _lift.D > Down) right = Math.Min(right, Dl10Lane.CwX0 - Dl10Lane.Half + EdgeSlack);   // L4195
                right = Math.Min(right, Dl10Lane.CwX1 - Dl10Lane.Half);                                          // L4196
            }
            else left = Math.Max(left, Dl10Lane.CwX0 + Dl10Lane.Half);                                           // L4197
        }
    }

    /// <summary>
    /// The suitcase lying in the lane (<c>surfaceCh1</c>, L4156–L4157): standable to its base + 0.2 within <c>UO.caseHalf</c>
    /// of its x, where the surface there is within 0.05 of its base. In his hands or in the car it is nothing.
    /// </summary>
    public sealed class SuitcaseLane : LaneContributor
    {
        public const double Height = 0.2, Level = 0.05;

        private readonly CarriedItem _case;

        public SuitcaseLane(CarriedItem suitcase) { _case = suitcase ?? throw new ArgumentNullException(nameof(suitcase)); }

        public override double Surface(double x, double surface)
        {
            if (_case.State != ItemState.Floor || !(Math.Abs(x - _case.X) <= Dl10Lane.CaseHalf)) return surface;
            return Math.Abs(surface - _case.BaseY) < Level ? Math.Max(surface, _case.BaseY + Height) : surface;
        }
    }
}
