using System;
using DeadLetter.Core.Mechanisms;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-17 A Different Lesson's lane: region 6 from 324 to the school's end (<c>ATT.x1</c> 342.4): the workshop, flat, and
    /// the stair door in its end wall, shut until she is forwarded and the rig's float has lifted its latch (rev 0.3). Lines
    /// are index.html at 7b3c123 (<c>ATT2.door17</c> L5530, <c>limitsAtt2</c> L5612).
    /// </summary>
    public static class Dl17Lane
    {
        public const int Region = 6;

        /// <summary><c>ATT2.door17.x</c> (L5530): a wall for his centre HALF short of it while it is less than 0.7 open (L5612).</summary>
        public const double DoorX = 339.8, DoorOpenAt = 0.7;

        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-17 (region 6)",
            Left = Dl12Lane.Left, Right = Dl12Lane.Right,
            Floor = 0,
            Ceiling = Dl12Lane.Ceiling,
        };

        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new Dl17DoorLane(g.Get<IPositionSource>("dl17.stairDoor")),
        };
    }

    /// <summary>The stair door, shut (<c>limitsAtt2</c>, L5612: wherever he is in region 6, as the prototype has it).</summary>
    public sealed class Dl17DoorLane : LaneContributor
    {
        private readonly IPositionSource _door;

        public Dl17DoorLane(IPositionSource door) { _door = door ?? throw new ArgumentNullException(nameof(door)); }

        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (_door.Position < Dl17Lane.DoorOpenAt) right = Math.Min(right, Dl17Lane.DoorX - Dl12Lane.Half);
        }
    }
}
