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

        /// <summary>
        /// The stair up to ring A beyond the door (<c>ATT2.door17</c> L5530; dl17.py's 18 treads): from the landing at 341.1,
        /// 0.18 up for every 0.26 along (the prototype's way out walks it, L2094) to its top, 3.24, then the upper landing on
        /// to the stair head at 347.0, where chapter 2's set and its datum begin (chapter2_plan §4: the top of DL-17's stair is
        /// ring A's 0). Not in the lane: he only goes up it in <see cref="Scenes.Dl17.Dl17StairAct"/>, after the chapter's end.
        /// </summary>
        public const double StairX0 = 341.1, Tread = 0.26, Rise = 0.18, StairTop = 18 * Rise, StairHeadX = 347.0;

        /// <summary>His feet on the stair at <paramref name="x"/> (L2094, capped at the flight's top: the upper landing).</summary>
        public static double StairY(double x) => Math.Min(StairTop, Math.Max(0, x - StairX0) * Rise / Tread);

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
