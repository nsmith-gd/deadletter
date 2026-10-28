using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-14a Lights Out's lane: region 6 from 248 to DL-14b (263): the dormitory's bunks (solid blocks) and the lockers that
    /// are the steps up to them, and the door at its far end, shut until the room has been dark. Lines are index.html at
    /// 7b3c123 (<c>ATT3</c> L5886–L5895, <c>surfaceAtt3</c> L5940–L5943, <c>limitsAtt3</c> L5957).
    /// </summary>
    public static class Dl14aLane
    {
        public const int Region = 6;

        /// <summary>The bunks and lockers (<c>ATT3</c>, L5887–L5888; <c>inBox</c>, ends inclusive).</summary>
        public static readonly LaneSpan[] Blocks =
        {
            new LaneSpan(248.3, 250.3, 1.15, SpanEdges.Closed),     // bunk1
            new LaneSpan(250.3, 250.8, 0.55, SpanEdges.Closed),     // locker1
            new LaneSpan(254.3, 254.8, 0.55, SpanEdges.Closed),     // locker2
            new LaneSpan(254.8, 257.6, 1.15, SpanEdges.Closed),     // bunk2
            new LaneSpan(257.6, 258.1, 0.55, SpanEdges.Closed),     // locker3
        };
        /// <summary><c>ATT3.door</c> (L5894): a wall at its near face while it is less than 0.7 open (L5957).</summary>
        public const double DoorX0 = 262.85, DoorX1 = 263.0, DoorOpenAt = 0.7;

        /// <summary>The static lane of region 6 around DL-14a.</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-14a (region 6)",
            Left = Dl12Lane.Left, Right = Dl12Lane.Right,
            Floor = 0,
            Platforms = Blocks,
            Ceiling = Dl12Lane.Ceiling,
        };

        /// <summary>The door (<c>dl14a.door</c>).</summary>
        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new Dl14aDoorLane(g.Get<Door>("dl14a.door")),
        };
    }

    /// <summary>The dormitory door, shut (<c>limitsAtt3</c>, L5957): left of its far face his centre stays HALF short of its near face.</summary>
    public sealed class Dl14aDoorLane : LaneContributor
    {
        private readonly IPositionSource _door;

        public Dl14aDoorLane(IPositionSource door) { _door = door ?? throw new ArgumentNullException(nameof(door)); }

        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (_door.Position < Dl14aLane.DoorOpenAt && x < Dl14aLane.DoorX1) right = Math.Min(right, Dl14aLane.DoorX0 - Dl12Lane.Half);
        }
    }
}
