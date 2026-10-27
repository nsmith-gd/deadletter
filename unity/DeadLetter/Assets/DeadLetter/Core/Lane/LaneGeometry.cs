using System;
using System.Collections.Generic;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Lane
{
    /// <summary>
    /// D-17's collision: the prototype's 1-D height field along the lane (port_architecture §4.6; index.html L1617–L1769,
    /// L4135–L4201), answering the motor's <see cref="IMotorWorld"/> probes. Not physics: <see cref="FloorAt"/> (the
    /// ground), <see cref="SurfaceAt(double)"/> (the highest standable thing at a point), <see cref="SupportAt"/> (max over
    /// ±FOOT), <see cref="CeilingAt(double)"/>, <see cref="Limits(double, double, out double, out double)"/> and
    /// <see cref="IsRamp"/>.
    /// <para>The lane is split into regions, as the prototype's <c>game.region</c> selects its collision code
    /// (§0.3): each region is a static <see cref="LaneTable"/> plus the <see cref="ILaneContributor"/>s registered on it.
    /// Exactly one region is active (<see cref="Region"/>); the scene simulation switches it where the prototype changes
    /// <c>game.region</c>. Probes ignore <c>refY</c>: the height field has one answer per x, as in the prototype.</para>
    /// <para>Per probe: no allocation, no lookup (the active region is resolved when <see cref="Region"/> is set).</para>
    /// </summary>
    public sealed class LaneGeometry : IMotorWorld
    {
        /// <summary><c>FOOT</c>: the support probe's half-spread, L310 (<c>supportAt</c>, L1737).</summary>
        public const double Foot = 0.08;

        private sealed class RegionLane
        {
            public readonly int Id;
            public readonly LaneTable Table;
            public readonly List<ILaneContributor> Contributors = new List<ILaneContributor>();
            public RegionLane(int id, LaneTable table) { Id = id; Table = table; }
        }

        private readonly List<RegionLane> _regions = new List<RegionLane>();
        private RegionLane _active;

        /// <summary>Adds a region's static lane. The first region added becomes active.</summary>
        public LaneGeometry AddRegion(int region, LaneTable table)
        {
            if (table == null) throw new ArgumentNullException(nameof(table));
            if (Find(region) != null) throw new ArgumentException("Region " + region + " already has a lane.");
            var r = new RegionLane(region, table);
            _regions.Add(r);
            if (_active == null) _active = r;
            return this;
        }

        /// <summary>Registers a dynamic contributor on a region (asked after the table, in registration order).</summary>
        public LaneGeometry AddContributor(int region, ILaneContributor contributor)
        {
            if (contributor == null) throw new ArgumentNullException(nameof(contributor));
            var r = Find(region) ?? throw new ArgumentException("No lane for region " + region + ": add its table first.");
            r.Contributors.Add(contributor);
            return this;
        }

        public bool HasRegion(int region) => Find(region) != null;

        /// <summary>The active region (<c>game.region</c>). Setting a region without a lane throws.</summary>
        public int Region
        {
            get => _active != null ? _active.Id : 0;
            set
            {
                if (_active != null && _active.Id == value) return;
                _active = Find(value) ?? throw new ArgumentException("No lane for region " + value + ".");
            }
        }

        /// <summary>The active region's static table.</summary>
        public LaneTable Table => Active.Table;

        // ---- Probes ---------------------------------------------------------------------------------------------------
        /// <summary><c>floorAt</c> (L1711–L1717, with <c>floorCh1</c> L4135–L4141 as contributors).</summary>
        public double FloorAt(double x)
        {
            var r = Active;
            var t = r.Table;
            double f = t.Floor;
            for (int i = 0; i < t.Floors.Length; i++)
                if (t.Floors[i].Contains(x)) { f = t.Floors[i].Y; break; }
            var c = r.Contributors;
            for (int i = 0; i < c.Count; i++) f = c[i].Floor(x, f);
            return f;
        }

        /// <summary><c>surfaceAt</c> (L1719–L1735, with <c>surfaceCh1</c> L4143–L4163 as contributors): the surface under one point.</summary>
        public double SurfaceAt(double x)
        {
            var r = Active;
            var t = r.Table;
            double h = FloorAt(x);
            for (int i = 0; i < t.Platforms.Length; i++)
                if (t.Platforms[i].Contains(x)) h = Math.Max(h, t.Platforms[i].Y);
            var c = r.Contributors;
            for (int i = 0; i < c.Count; i++) h = c[i].Surface(x, h);
            return h;
        }

        /// <summary><c>supportAt</c>, L1737: the highest surface under his feet (centre and ±FOOT).</summary>
        public double SupportAt(double x) => Math.Max(SurfaceAt(x - Foot), Math.Max(SurfaceAt(x), SurfaceAt(x + Foot)));

        /// <summary><c>ceilingAt</c> (L1624–L1642, with <c>ceilingCh1</c> L4165–L4169 as contributors).</summary>
        public double CeilingAt(double x)
        {
            var r = Active;
            var t = r.Table;
            double h = t.Ceiling;
            for (int i = 0; i < t.Ceilings.Length; i++)
                if (t.Ceilings[i].Contains(x)) h = Math.Min(h, t.Ceilings[i].Y);
            var c = r.Contributors;
            for (int i = 0; i < c.Count; i++) h = c[i].Ceiling(x, h);
            return h;
        }

        /// <summary><c>minCeiling</c>, L1643: the lowest ceiling over seven samples from x0 to x1.</summary>
        public double MinCeiling(double x0, double x1)
        {
            double h = double.PositiveInfinity;
            for (int i = 0; i <= 6; i++) h = Math.Min(h, CeilingAt(x0 + (x1 - x0) * i / 6));
            return h;
        }

        /// <summary><c>leftLimit/rightLimit</c> (L1750–L1769, with <c>limitsCh1</c> L4171–L4201 as contributors).</summary>
        public void Limits(double x, double y, out double left, out double right)
        {
            var r = Active;
            left = r.Table.Left;
            right = r.Table.Right;
            var c = r.Contributors;
            for (int i = 0; i < c.Count; i++) c[i].Limits(x, y, ref left, ref right);
        }

        /// <summary><c>onRamp</c>, L6351.</summary>
        public bool IsRamp(double x)
        {
            var z = Active.Table.Ramps;
            for (int i = 0; i < z.Length; i++) if (z[i].Contains(x)) return true;
            return false;
        }

        // ---- IMotorWorld ----------------------------------------------------------------------------------------------
        double IMotorWorld.SurfaceAt(double x, double refY) => SurfaceAt(x);
        double IMotorWorld.CeilingAt(double x, double refY) => CeilingAt(x);

        /// <summary><c>ledgeAhead</c>, L1738–L1748, sampled as <see cref="LaneProbe.ScanLedge"/> does.</summary>
        public bool LedgeAhead(double x, double y, int dir, double range, double stepUp, out Ledge ledge)
            => LaneProbe.ScanLedge(this, x, y, dir, range, stepUp, out ledge);

        private RegionLane Active => _active ?? throw new InvalidOperationException("The lane has no regions.");

        private RegionLane Find(int region)
        {
            for (int i = 0; i < _regions.Count; i++) if (_regions[i].Id == region) return _regions[i];
            return null;
        }
    }
}
