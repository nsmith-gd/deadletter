using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Plates;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-04 The Racks' lane: region 2 (12.2 → 60.3, §0.3), whose static lane is the one DL-03's table describes (the
    /// racks hall past the gate under its 5.5 m ceiling, floor 0, out to the scanner corridor), with the bay door as
    /// DL-04's one moving part on it. Lines are index.html at 7b3c123 (<c>RK</c> L3890; <c>limitsCh1</c> L4171–L4174).
    /// <para>The fallen courier lies 0.35 behind the lane (<c>RK.courierZ</c>): nothing he stands on or bumps into
    /// (<c>surfaceCh1</c>, L4143–L4162, has no courier). The bay plate is flush with the floor (its 1 cm dip is view only).</para>
    /// <para>Not here: DL-03's trolley, weight and gate (DL-03's contributors, <see cref="Dl03Lane.Contributors"/>), behind
    /// him at 28.8–30.6, and DL-05's shutter and crawl (from <c>RATION5.x0</c> 47.9, L4166, L4176): those scenes' own.
    /// From DL-04's checkpoints (<c>solved</c>'s gate held at 0.72 · 1.2 = 0.864 by the parked trolley) the gate neither
    /// walls him (≥ CROUCH_H + 0.02) nor brings the clearance he reads under 0.85, so on the way from the weighing room to
    /// the racks it changes no probe the motor makes (the parity windows start 0.63 m short of it).</para>
    /// </summary>
    public static class Dl04Lane
    {
        public const int Region = Dl03Lane.Region;

        /// <summary><c>RK.plate</c> 44.0–45.0, <c>RK.bayX</c> 44.5, <c>RK.door</c> 46.3–46.7 (L3890).</summary>
        public const double PlateX0 = 44.0, PlateX1 = 45.0, BayX = 44.5, DoorX0 = 46.3, DoorX1 = 46.7;
        /// <summary>The door walls him while under 0.55 open, 0.04 + HALF short of its face (<c>limitsCh1</c>, L4174).</summary>
        public const double DoorBlocksBelow = 0.55, DoorGap = 0.04 + Dl03Lane.Half;

        /// <summary>The static lane of region 2 (<see cref="Dl03Lane.Table"/>: the same walls, floor, platforms and ceilings).</summary>
        public static LaneTable Table()
        {
            var t = Dl03Lane.Table();
            t.Name = "DL-04 (region 2)";
            return t;
        }

        /// <summary>The bay door (<c>dl04.bayDoor</c>): a wall while it is under half open (L4174).</summary>
        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new BayDoorLane(g.Get<PlateDoor>("dl04.bayDoor"), DoorX0, DoorBlocksBelow, DoorGap),
        };
    }

    /// <summary>
    /// A door he cannot pass while it is less than <c>blockBelow</c> open (<see cref="PlateDoor.Open01"/>): from its
    /// near side (his x &lt; its face) his centre stops <c>gap</c> short of the face (DL-04's bay door, <c>limitsCh1</c>
    /// L4174: <c>x &lt; RK.door.x0 &amp;&amp; bayDoor &lt; 0.55 → hi = RK.door.x0 − 0.04 − HALF</c>). From beyond it, nothing.
    /// </summary>
    public sealed class BayDoorLane : LaneContributor
    {
        private readonly PlateDoor _door;
        private readonly double _face, _blockBelow, _gap;

        public BayDoorLane(PlateDoor door, double face, double blockBelow, double gap)
        {
            _door = door ?? throw new ArgumentNullException(nameof(door));
            _face = face; _blockBelow = blockBelow; _gap = gap;
        }

        public bool Blocks => _door.Open01 < _blockBelow;

        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (x < _face && Blocks) right = Math.Min(right, _face - _gap);
        }
    }
}
