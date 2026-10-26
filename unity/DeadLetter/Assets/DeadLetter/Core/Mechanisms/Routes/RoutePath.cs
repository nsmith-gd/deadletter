using System;

namespace DeadLetter.Core.Mechanisms.Routes
{
    /// <summary>
    /// A carrier route: a polyline in the lane plane (x, y), measured by arc length (<c>along</c>, <c>lengthTo</c>,
    /// L2474–L2486). Built once from params; queries do not allocate.
    /// </summary>
    public sealed class RoutePath
    {
        private readonly double[] _x, _y, _cum;

        /// <param name="xy">Points as x0, y0, x1, y1, ...</param>
        public RoutePath(params double[] xy)
        {
            if (xy == null || xy.Length < 4 || xy.Length % 2 != 0) throw new ArgumentException("A route needs two or more (x, y) points.");
            int n = xy.Length / 2;
            _x = new double[n]; _y = new double[n]; _cum = new double[n];
            for (int i = 0; i < n; i++) { _x[i] = xy[2 * i]; _y[i] = xy[2 * i + 1]; }
            for (int i = 1; i < n; i++) _cum[i] = _cum[i - 1] + Seg(i - 1);
        }

        public int Count => _x.Length;
        public double X(int i) => _x[i];
        public double Y(int i) => _y[i];
        public double Length => _cum[_cum.Length - 1];

        /// <summary><c>lengthTo(pts, i)</c>: arc length from the start to point i.</summary>
        public double LengthTo(int i) => _cum[i];

        /// <summary><c>along(pts, s)</c> (L2480–L2486): the point at arc length s, clamped to the ends, and the segment's angle (radians).</summary>
        public void At(double s, out double x, out double y, out double angle)
        {
            int last = _x.Length - 2;
            for (int i = 0; i <= last; i++)
            {
                double l = Seg(i);
                if (s <= l || i == last)
                {
                    double k = Math.Min(1, Math.Max(0, s / l));
                    x = _x[i] + (_x[i + 1] - _x[i]) * k;
                    y = _y[i] + (_y[i + 1] - _y[i]) * k;
                    angle = Math.Atan2(_y[i + 1] - _y[i], _x[i + 1] - _x[i]);
                    return;
                }
                s -= l;
            }
            throw new InvalidOperationException("unreachable");
        }

        private double Seg(int i)
        {
            double dx = _x[i + 1] - _x[i], dy = _y[i + 1] - _y[i];
            return Math.Sqrt(dx * dx + dy * dy);
        }
    }
}
