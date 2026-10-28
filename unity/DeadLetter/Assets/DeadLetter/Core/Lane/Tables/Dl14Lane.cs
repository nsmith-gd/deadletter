using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Drives;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-14 The Window's lane: region 6 from 232 to DL-14a (248): the end of the gallery, the stair down (five open treads),
    /// the desk, the two ledges that fold out of the wall under the blinds, the hatch high in the end wall, and the wall
    /// at 247.85 between DL-14's room and the dormitory beyond (the duct runs behind it). Lines are index.html at 7b3c123
    /// (<c>ATT</c> L291–L294, <c>floorAtt</c> L5244–L5251, <c>surfaceAtt</c> L5259–L5264, <c>limitsAtt2</c> L5601).
    /// </summary>
    public static class Dl14Lane
    {
        public const int Region = 6;

        /// <summary><c>ATT.stair14</c> (L292): five treads down from the gallery, 0.3417 apart.</summary>
        public const double StairX0 = 233.0, StairX1 = 234.4, Tread = 0.3417;
        public const int Treads = 5;
        /// <summary><c>ATT.desk</c> (L292).</summary>
        public const double DeskX0 = 235.4, DeskX1 = 236.2, DeskH = 0.62;
        /// <summary><c>ATT.hatch</c> (L293): a sill only for someone above 1.3 (L5264).</summary>
        public const double HatchX0 = 239.2, HatchX1 = 240.2, HatchH = 2.15, HatchMinY = 1.3;
        /// <summary><c>ATT2.wall</c> (L5517): between DL-14 and DL-14a; its far face holds him until 264 (L5601).</summary>
        public const double WallX0 = 247.85, WallX1 = 248.15, WallBackTo = 264;

        /// <summary>The static lane of region 6 around DL-14.</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-14 (region 6)",
            Left = Dl12Lane.Left, Right = Dl12Lane.Right,
            Floor = 0,
            Floors = new[] { new LaneSpan(Dl13Lane.GalleryX0, StairX0, Dl13Lane.GalleryH, SpanEdges.ClosedOpen) },   // L5245
            Platforms = new[] { new LaneSpan(DeskX0, DeskX1, DeskH, SpanEdges.Closed) },                            // L5259
            Ceiling = Dl12Lane.Ceiling,
        };

        /// <summary>The stair's treads; the ledges (<c>dl14.blinds</c>) and the hatch's sill, by his height; the wall.</summary>
        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new Dl14StairFloor(),
            new Dl14BoardsLane(g.Get<PairedBlindDrive>("dl14.blinds")),
            new Dl14WallLane(),
        };
    }

    /// <summary>
    /// DL-14's stair (<c>floorAtt</c>, L5246–L5249): over [233, 234.4) the floor is the gallery's less 0.3417 for every tread
    /// down, <c>ceil(k · 5)</c> with k the fraction of the way down.
    /// </summary>
    public sealed class Dl14StairFloor : LaneContributor
    {
        public override double Floor(double x, double floor)
        {
            if (!(x >= Dl14Lane.StairX0 && x < Dl14Lane.StairX1)) return floor;
            double k = (x - Dl14Lane.StairX0) / (Dl14Lane.StairX1 - Dl14Lane.StairX0);
            return Dl13Lane.GalleryH - Dl14Lane.Tread * Math.Ceiling(k * Dl14Lane.Treads);
        }
    }

    /// <summary>
    /// DL-14's boards in the air (<c>surfaceAtt</c>, L5261–L5264): the two ledges once their blinds are down, each solid
    /// only to someone above the level below (<see cref="PairedBlindDrive.SurfaceAt"/>), and the hatch's sill for someone
    /// above 1.3.
    /// </summary>
    public sealed class Dl14BoardsLane : LaneContributor, ILaneHeightContributor
    {
        private readonly PairedBlindDrive _blinds;

        public Dl14BoardsLane(PairedBlindDrive blinds) { _blinds = blinds ?? throw new ArgumentNullException(nameof(blinds)); }

        public double Surface(double x, double refY, double surface)
        {
            surface = _blinds.SurfaceAt(x, refY, surface);
            if (refY > Dl14Lane.HatchMinY && x >= Dl14Lane.HatchX0 && x <= Dl14Lane.HatchX1) surface = Math.Max(surface, Dl14Lane.HatchH);
            return surface;
        }
    }

    /// <summary>The wall between DL-14 and DL-14a (<c>limitsAtt2</c>, L5601): left of it his centre stays HALF short; right of it, to 264, HALF past it.</summary>
    public sealed class Dl14WallLane : LaneContributor
    {
        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (x < Dl14Lane.WallX0) right = Math.Min(right, Dl14Lane.WallX0 - Dl12Lane.Half);
            else if (x < Dl14Lane.WallBackTo) left = Math.Max(left, Dl14Lane.WallX1 + Dl12Lane.Half);
        }
    }
}
