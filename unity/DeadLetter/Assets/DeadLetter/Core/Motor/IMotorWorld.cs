using System;

namespace DeadLetter.Core.Motor
{
    /// <summary>
    /// The motor's view of the lane: probes along x in the play plane (z = 0), in metres (port_architecture §4.6).
    /// The prototype answers these from a 1-D height field (<c>surfaceAt</c>, <c>ceilingAt</c>, limits, L1709–L1769);
    /// Runtime answers them with physics casts confined to the lane; tests answer them from boxes (<see cref="BoxWorld"/>).
    /// </summary>
    public interface IMotorWorld
    {
        /// <summary>
        /// Ground probe: the top of the highest standable thing at lane x (prototype <c>surfaceAt</c>, L1720).
        /// <paramref name="refY"/> is his feet height, so a physics probe can start a bounded distance above him;
        /// anything taller than that probe should report at least its start height (a wall).
        /// Returns <see cref="LaneProbe.NoGround"/> over a bottomless gap.
        /// </summary>
        double SurfaceAt(double x, double refY);

        /// <summary>
        /// Ceiling probe: the underside of the lowest thing above <paramref name="refY"/> at lane x (prototype
        /// <c>ceilingAt</c>, L1624). Returns <see cref="LaneProbe.NoCeiling"/> when open.
        /// </summary>
        double CeilingAt(double x, double refY);

        /// <summary>Wall probe: the lane limits for the body centre (prototype <c>leftLimit/rightLimit</c>, L1752–L1769).</summary>
        void Limits(double x, double y, out double left, out double right);

        /// <summary>True on a ramp, where the step-up allowance is 0.45 m (prototype <c>onRamp</c>, L6351, used at L2004).</summary>
        bool IsRamp(double x);

        /// <summary>
        /// Ledge probe: the first raised face ahead within <paramref name="range"/> (prototype <c>ledgeAhead</c>, L1738).
        /// Implementations without a cheaper cast should return <see cref="LaneProbe.ScanLedge"/>.
        /// </summary>
        bool LedgeAhead(double x, double y, int dir, double range, double stepUp, out Ledge ledge);
    }

    /// <summary>A ledge found ahead: distance from his centre to its face, and its top.</summary>
    public readonly struct Ledge
    {
        public readonly double Distance;
        public readonly double Top;
        public Ledge(double distance, double top) { Distance = distance; Top = top; }
    }

    /// <summary>Probe helpers built on <see cref="IMotorWorld.SurfaceAt"/> and <see cref="IMotorWorld.CeilingAt"/>.</summary>
    public static class LaneProbe
    {
        public const double NoGround = -1000.0;
        public const double NoCeiling = 1000.0;

        /// <summary><c>supportAt</c>, L1737: highest surface under his feet (centre and ±FOOT).</summary>
        public static double SupportAt(IMotorWorld w, double x, double refY, double foot)
        {
            double a = w.SurfaceAt(x - foot, refY), b = w.SurfaceAt(x, refY), c = w.SurfaceAt(x + foot, refY);
            return Math.Max(a, Math.Max(b, c));
        }

        /// <summary><c>minCeiling</c>, L1643: lowest ceiling over seven samples from x0 to x1.</summary>
        public static double MinCeiling(IMotorWorld w, double x0, double x1, double refY)
        {
            double h = double.PositiveInfinity;
            for (int i = 0; i <= 6; i++) h = Math.Min(h, w.CeilingAt(x0 + (x1 - x0) * i / 6.0, refY));
            return h;
        }

        /// <summary>
        /// <c>ledgeAhead</c>, L1738–L1748, by sampling the ground probe every centimetre from 0.02 m. A step with a taller
        /// thing right behind it (within 6 cm) climbs as one. Integer stepping replaces the prototype's accumulated
        /// <c>d += 0.01</c> so every platform samples the same distances. The prototype's float accumulation overshoots
        /// <c>range</c> on the last step (0.02 + 30 × 0.01 &gt; 0.32), so its <c>d &lt;= range</c> never samples the end
        /// point: 0.02 … range − 0.01, i.e. 48 samples for 0.5 and 30 for 0.32 (<see cref="ScanSampleCount"/>).
        /// </summary>
        public static bool ScanLedge(IMotorWorld w, double x, double y, int dir, double range, double stepUp, out Ledge ledge)
        {
            int last = ScanLastIndex(range);
            for (int i = 2; i <= last; i++)
            {
                double d = i * 0.01;
                double h = w.SurfaceAt(x + dir * d, y);
                if (h > y + stepUp)
                {
                    double top = h;
                    for (int e = 1; e <= 6; e++) top = Math.Max(top, w.SurfaceAt(x + dir * (d + e * 0.01), y));
                    ledge = new Ledge(d, top);
                    return true;
                }
            }
            ledge = default;
            return false;
        }

        /// <summary>Index (centimetres) of the last distance <see cref="ScanLedge"/> samples: range − 0.01.</summary>
        private static int ScanLastIndex(double range) => (int)Math.Round(range * 100) - 1;

        /// <summary>How many distances <see cref="ScanLedge"/> samples for <paramref name="range"/> (48 for 0.5, 30 for 0.32).</summary>
        public static int ScanSampleCount(double range) => Math.Max(0, ScanLastIndex(range) - 1);
    }
}
