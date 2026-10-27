using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Motor
{
    /// <summary>
    /// A lane made of axis-aligned boxes, answering <see cref="IMotorWorld"/> like the prototype's height field:
    /// solids are columns from below up to <c>Top</c> (prototype <c>PLATFORMS</c>, L1722–L1723; edges inclusive),
    /// ceilings are slabs whose underside is <c>Bottom</c>. Used by the Core tests, the EditMode tests, and as the
    /// reference behaviour any physics-backed world must match.
    /// </summary>
    public sealed class BoxWorld : IMotorWorld
    {
        public readonly struct Solid
        {
            public readonly double X0, X1, Top;
            public Solid(double x0, double x1, double top) { X0 = x0; X1 = x1; Top = top; }
        }

        public readonly struct Ceiling
        {
            public readonly double X0, X1, Bottom;
            public Ceiling(double x0, double x1, double bottom) { X0 = x0; X1 = x1; Bottom = bottom; }
        }

        /// <summary>A straight ramp whose top runs from (X0, Y0) to (X1, Y1).</summary>
        public readonly struct Ramp
        {
            public readonly double X0, Y0, X1, Y1;
            public Ramp(double x0, double y0, double x1, double y1) { X0 = x0; Y0 = y0; X1 = x1; Y1 = y1; }
        }

        public readonly List<Solid> Solids = new List<Solid>();
        public readonly List<Ceiling> Ceilings = new List<Ceiling>();
        public readonly List<Ramp> Ramps = new List<Ramp>();
        public double LeftLimit = -1000;
        public double RightLimit = 1000;

        /// <summary>A flat floor at y = 0 from <paramref name="x0"/> to <paramref name="x1"/>, walls at the ends.</summary>
        public static BoxWorld Flat(double x0 = -50, double x1 = 50)
        {
            var w = new BoxWorld { LeftLimit = x0, RightLimit = x1 };
            w.Solids.Add(new Solid(x0 - 1, x1 + 1, 0));
            return w;
        }

        public BoxWorld AddSolid(double x0, double x1, double top) { Solids.Add(new Solid(x0, x1, top)); return this; }
        public BoxWorld AddCeiling(double x0, double x1, double bottom) { Ceilings.Add(new Ceiling(x0, x1, bottom)); return this; }
        public BoxWorld AddRamp(double x0, double y0, double x1, double y1) { Ramps.Add(new Ramp(x0, y0, x1, y1)); return this; }

        public double SurfaceAt(double x, double refY)
        {
            double h = LaneProbe.NoGround;
            for (int i = 0; i < Solids.Count; i++)
            {
                var s = Solids[i];
                if (x >= s.X0 && x <= s.X1 && s.Top > h) h = s.Top;
            }
            for (int i = 0; i < Ramps.Count; i++)
            {
                var r = Ramps[i];
                if (x >= r.X0 && x <= r.X1 && r.X1 > r.X0)
                {
                    double t = r.Y0 + (r.Y1 - r.Y0) * (x - r.X0) / (r.X1 - r.X0);
                    if (t > h) h = t;
                }
            }
            return h;
        }

        public double CeilingAt(double x, double refY)
        {
            double h = LaneProbe.NoCeiling;
            for (int i = 0; i < Ceilings.Count; i++)
            {
                var c = Ceilings[i];
                if (x >= c.X0 && x <= c.X1 && c.Bottom >= refY && c.Bottom < h) h = c.Bottom;
            }
            return h;
        }

        public void Limits(double x, double y, out double left, out double right)
        {
            left = LeftLimit;
            right = RightLimit;
        }

        public bool IsRamp(double x)
        {
            for (int i = 0; i < Ramps.Count; i++)
                if (x >= Ramps[i].X0 && x <= Ramps[i].X1) return true;
            return false;
        }

        public bool LedgeAhead(double x, double y, int dir, double range, double stepUp, out Ledge ledge)
            => LaneProbe.ScanLedge(this, x, y, dir, range, stepUp, out ledge);
    }
}
