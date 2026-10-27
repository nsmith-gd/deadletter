using System;

namespace DeadLetter.Core.Mechanisms.Folding
{
    /// <summary>
    /// A swept volume (<see cref="ISweptVolume"/>: DL-18's fold bed and bench) as the lane sees it: each box's cross-section
    /// clipped to the depth band D-17 fills (<c>d0</c>..<c>d1</c>, the leaf's own BodyD0/BodyD1), within its lane x-extent.
    /// While the leaf is <c>standable</c> (down on its stop) its top is ground; otherwise (folding, propped, waiting) its
    /// underside is a ceiling above his feet, never ground: he slides off a propped leaf and cannot pass through a moving
    /// one. No prototype: DL-18 §3–§4, §11. A lane contributor adapts these two probes (allocation-free).
    /// </summary>
    public static class SweptVolumeProbe
    {
        /// <summary>D-17's depth band in the leaf's cross-section (BodyD0, BodyD1).</summary>
        public const double DefaultD0 = 0.10, DefaultD1 = 0.44;

        /// <summary>The ground at x given <paramref name="h"/> so far: the highest top inside the band, only while <paramref name="standable"/>.</summary>
        public static double Surface(ISweptVolume v, bool standable, double x, double h, double d0 = DefaultD0, double d1 = DefaultD1)
        {
            if (!standable) return h;
            for (int i = 0, n = v.VolumeCount; i < n; i++)
            {
                var b = v.Volume(i);
                if (x < b.X0 || x > b.X1 || !Band(b, d0, d1, out _, out double top)) continue;
                if (top > h) h = top;
            }
            return h;
        }

        /// <summary>The ceiling at x above <paramref name="refY"/> given <paramref name="h"/> so far: the lowest underside inside the band, unless standable.</summary>
        public static double Ceiling(ISweptVolume v, bool standable, double x, double refY, double h, double d0 = DefaultD0, double d1 = DefaultD1)
        {
            if (standable) return h;
            for (int i = 0, n = v.VolumeCount; i < n; i++)
            {
                var b = v.Volume(i);
                if (x < b.X0 || x > b.X1 || !Band(b, d0, d1, out double bottom, out _)) continue;
                if (bottom >= refY && bottom < h) h = bottom;
            }
            return h;
        }

        /// <summary>The lowest and highest Y of the box's (D, Y) rectangle inside d0 ≤ D ≤ d1; false if it misses the band.</summary>
        public static bool Band(in SweptBox b, double d0, double d1, out double lo, out double hi)
        {
            if (!(d0 < d1)) throw new ArgumentException("d0 must be below d1.");
            lo = double.PositiveInfinity; hi = double.NegativeInfinity;
            double vx = -b.Uy, vy = b.Ux;                                         // the second axis
            for (int k = 0; k < 4; k++)
            {
                double su = k == 0 || k == 3 ? 1 : -1, sv = k < 2 ? 1 : -1;
                // Corner k and the next one round the rectangle: (+u, +v), (−u, +v), (−u, −v), (+u, −v).
                double ad = b.Cd + su * b.Hu * b.Ux + sv * b.Hv * vx, ay = b.Cy + su * b.Hu * b.Uy + sv * b.Hv * vy;
                int n = (k + 1) & 3;
                double nu = n == 0 || n == 3 ? 1 : -1, nv = n < 2 ? 1 : -1;
                double bd = b.Cd + nu * b.Hu * b.Ux + nv * b.Hv * vx, by = b.Cy + nu * b.Hu * b.Uy + nv * b.Hv * vy;
                if (ad >= d0 && ad <= d1) { if (ay < lo) lo = ay; if (ay > hi) hi = ay; }
                Cross(ad, ay, bd, by, d0, ref lo, ref hi);
                Cross(ad, ay, bd, by, d1, ref lo, ref hi);
            }
            return hi >= lo;
        }

        private static void Cross(double ad, double ay, double bd, double by, double d, ref double lo, ref double hi)
        {
            if ((ad - d) * (bd - d) > 0 || ad == bd) return;
            double y = ay + (by - ay) * (d - ad) / (bd - ad);
            if (y < lo) lo = y;
            if (y > hi) hi = y;
        }
    }
}
