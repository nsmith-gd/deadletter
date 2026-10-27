using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-05 The Ration Hall's lane: region 2 (12.2 → 60.3, §0.3), whose east end the hall is (<c>RATION5</c> 47.9 → 59.8,
    /// L3447), with the kitchen and the scanner corridor's mouth up to the region's end (<c>REGION3_X</c> 60.3, L2457).
    /// Lines are index.html at 7b3c123.
    /// <para>The static lane is region 2's one table (<see cref="Dl03Lane.Table"/>): the floor at 0 all the way (<c>floorAt</c>,
    /// L1712–L1718), the walls <c>SH.x0 + 0.2</c> and <c>REGION3_X + 1</c> (L1761, L1768), the ceiling 5.5 past the gate and the
    /// corridor's 2.4 from <c>CORRIDOR_X0</c> 59.9 (L1628–L1629). Nothing in the hall is solid in the lane: the drum and the
    /// body stand behind it (<c>drumZ</c> −0.38, <c>bodyZ</c> −0.35, L3451–L3452) and no probe reads them
    /// (<c>surfaceCh1</c>, L4142–L4162). The one moving part is the hatch (<see cref="HatchLane"/>).</para>
    /// <para>Not here: DL-04's bay door (<c>limitsCh1</c>, L4173), a wall only for x &lt; 46.3 while it is shut: it is DL-04's
    /// contributor, and open once the courier is seated (<c>bay</c>, L4097).</para>
    /// </summary>
    public static class Dl05Lane
    {
        public const int Region = Dl03Lane.Region;

        /// <summary><c>RATION5.x0</c> = OFF2 + 34.9 (L3447): the hall's west end (and DL-05's, <c>sceneName</c> L8139).</summary>
        public const double HallX0 = 13 + 34.9;
        /// <summary><c>REGION3_X</c> = OFF3 + 27.3 (L2457): past it is region 3 (L2042), DL-06.</summary>
        public const double Region3X = 33 + 27.3;
        /// <summary><c>RH5.shutterX</c>, <c>RH5.foot</c> (L3454): the shutter's line and the foot of the kitchen wall either side.</summary>
        public const double ShutterX = 13 + 43.48, FootX0 = 13 + 43.30, FootX1 = 13 + 43.50;
        /// <summary><c>RH5.crawl</c> (L3454): under the hatch, its lower edge is the ceiling.</summary>
        public const double CrawlX0 = 13 + 43.10, CrawlX1 = 13 + 43.70;
        /// <summary><c>RH5.onDrum</c> (L3454): the serving height.</summary>
        public const double ServeH = 0.64;
        /// <summary><c>HALF</c> (L309).</summary>
        public const double Half = Dl03Lane.Half;

        /// <summary>Region 2's static lane (shared with DL-03 and DL-04).</summary>
        public static LaneTable Table()
        {
            var t = Dl03Lane.Table();
            t.Name = "DL-05 (region 2)";
            return t;
        }

        /// <summary>The hatch (<c>dl05.hatch</c>, a <see cref="Door"/> whose Position is <c>rh.h</c>).</summary>
        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new HatchLane(g.Get<Door>("dl05.hatch")),
        };
    }

    /// <summary>
    /// DL-05's serving hatch in the lane, from its height h (the <c>dl05.hatch</c> door's Position; the twitch is the view's,
    /// L4920): under it (<c>RH5.crawl</c>, open ends) the ceiling is h, at least 0.01, while h &lt; 1.15, and it overrides the
    /// rest (<c>ceilingCh1</c> returns first, L4165, L1628); and until it stands within 0.02 of its serving height it is a wall:
    /// from the hall side his centre stops HALF + 0.01 short of the wall's foot, from the kitchen side likewise
    /// (<c>limitsCh1</c>, L4176–L4178, for x past the hall's west end).
    /// </summary>
    public sealed class HatchLane : LaneContributor
    {
        /// <summary><c>rh.h &lt; 1.15</c> (L4165) and <c>rh.h &lt; RH5.onDrum − 0.02</c> (L4176).</summary>
        public const double CeilingBelow = 1.15, WallBelow = Dl05Lane.ServeH - 0.02, MinGap = 0.01;

        private readonly IPositionSource _h;

        public HatchLane(IPositionSource height) { _h = height ?? throw new ArgumentNullException(nameof(height)); }

        public override double Ceiling(double x, double ceiling)
        {
            double h = _h.Position;
            return x > Dl05Lane.CrawlX0 && x < Dl05Lane.CrawlX1 && h < CeilingBelow ? Math.Max(h, MinGap) : ceiling;
        }

        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (!(x > Dl05Lane.HallX0) || !(_h.Position < WallBelow)) return;
            if (x < Dl05Lane.ShutterX) right = Math.Min(right, Dl05Lane.FootX0 - Dl05Lane.Half - 0.01);   // L4177
            else left = Math.Max(left, Dl05Lane.FootX1 + Dl05Lane.Half + 0.01);
        }
    }
}
