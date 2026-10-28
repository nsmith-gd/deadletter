using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Lifts;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-15 One Pupil Missing's lane: region 6 from 278 to DL-16 (294): the sick bay's balcony (1.6, a board solid only to
    /// someone up there), the pupil lift's deck (its floor, to someone no more than 0.3 below it), the lift's far gate (shut
    /// while it is up, to someone on it) and the class door at the room's end, shut until dismissal. Lines are index.html
    /// at 7b3c123 (<c>ATT2</c> L5520–L5525, <c>surfaceAtt2</c> L5586–L5590, <c>limitsAtt2</c> L5603–L5606).
    /// </summary>
    public static class Dl15Lane
    {
        public const int Region = 6;

        /// <summary><c>ATT2.balcony</c> (L5520): solid above 1.0.</summary>
        public const double BalconyX0 = 278.15, BalconyX1 = 281.4, BalconyH = 1.6, BalconyMinY = 1.0;
        /// <summary><c>ATT2.lift</c> (L5521): its deck, standable from 0.3 below its floor.</summary>
        public const double LiftX0 = 281.4, LiftX1 = 282.4, LiftMid = 281.9, LiftTop = 1.6, LiftBelow = 0.3;
        /// <summary>The far gate: shut to someone above 0.5 on the deck while the lift is above 0.02 (L5604).</summary>
        public const double GateAboveY = 0.5, GateOpenBelow = 0.02;
        /// <summary><c>ATT2.part</c> (L5525): the class door's frame; shut until it is 0.6 open (L5606).</summary>
        public const double PartX0 = 293.75, PartX1 = 293.9, DoorOpenAt = 0.6;

        /// <summary>The static lane of region 6 around DL-15 (everything here moves, or depends on his height).</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-15 (region 6)",
            Left = Dl12Lane.Left, Right = Dl12Lane.Right,
            Floor = 0,
            Ceiling = Dl12Lane.Ceiling,
        };

        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new Dl15BoardsLane(g.Get<PupilLift>("dl15.lift")),
            new Dl15WallsLane(g.Get<PupilLift>("dl15.lift"), g.Get<IPositionSource>("dl15.classDoor")),
        };
    }

    /// <summary>The balcony and the lift's deck, by his height (<c>surfaceAtt2</c>, L5588–L5589).</summary>
    public sealed class Dl15BoardsLane : LaneContributor, ILaneHeightContributor
    {
        private readonly PupilLift _lift;

        public Dl15BoardsLane(PupilLift lift) { _lift = lift ?? throw new ArgumentNullException(nameof(lift)); }

        public double Surface(double x, double refY, double surface)
        {
            if (refY > Dl15Lane.BalconyMinY && x >= Dl15Lane.BalconyX0 && x <= Dl15Lane.BalconyX1) surface = Math.Max(surface, Dl15Lane.BalconyH);
            double lift = _lift.Y;
            if (x >= Dl15Lane.LiftX0 && x <= Dl15Lane.LiftX1 && refY > lift - Dl15Lane.LiftBelow) surface = Math.Max(surface, lift);
            return surface;
        }
    }

    /// <summary>The lift's far gate and the class door (<c>limitsAtt2</c>, L5604, L5606).</summary>
    public sealed class Dl15WallsLane : LaneContributor
    {
        private readonly PupilLift _lift;
        private readonly IPositionSource _door;

        public Dl15WallsLane(PupilLift lift, IPositionSource door)
        {
            _lift = lift ?? throw new ArgumentNullException(nameof(lift));
            _door = door ?? throw new ArgumentNullException(nameof(door));
        }

        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (y > Dl15Lane.GateAboveY && x >= Dl15Lane.LiftX0 && x <= Dl15Lane.LiftX1 && _lift.Y > Dl15Lane.GateOpenBelow)
                right = Math.Min(right, Dl15Lane.LiftX1 - 0.06 - Dl12Lane.Half);
            if (_door.Position < Dl15Lane.DoorOpenAt)
            {
                if (x < Dl15Lane.PartX0) right = Math.Min(right, Dl15Lane.PartX0 - Dl12Lane.Half);
                else left = Math.Max(left, Dl15Lane.PartX1 + Dl12Lane.Half);
            }
        }
    }
}
