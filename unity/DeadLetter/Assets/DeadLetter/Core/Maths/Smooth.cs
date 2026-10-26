using System;

namespace DeadLetter.Core.Maths
{
    /// <summary>Easing helpers shared with the prototype and the Blender generators.</summary>
    public static class Smooth
    {
        /// <summary>Clamped smoothstep, <c>smooth</c> in index.html L1527.</summary>
        public static double Step(double x)
        {
            if (x < 0) x = 0; else if (x > 1) x = 1;
            return x * x * (3 - 2 * x);
        }

        /// <summary>
        /// Frame-rate independent version of the prototype's per-frame <c>v *= max(0, 1 - k·dt)</c>
        /// (e.g. release friction, L1984). It is exact at the reference rate (60 Hz) and compounds correctly at any
        /// other step, so the replay harness and the web sim agree (port_architecture §3.1, §9 #10).
        /// </summary>
        public static double DecayFactor(double ratePerSecond, double dt, double referenceHz = 60.0)
        {
            double perRef = 1.0 - ratePerSecond / referenceHz;
            if (perRef <= 0) return 0;
            return Math.Pow(perRef, dt * referenceHz);
        }

        /// <summary>Move <paramref name="value"/> toward <paramref name="target"/> by at most <paramref name="maxDelta"/>.</summary>
        public static double MoveTowards(double value, double target, double maxDelta)
        {
            double d = target - value;
            if (d > maxDelta) d = maxDelta; else if (d < -maxDelta) d = -maxDelta;
            return value + d;
        }

        /// <summary>JavaScript's Math.sign for doubles: -1, 0 or 1.</summary>
        public static int Sign(double v) => v > 0 ? 1 : v < 0 ? -1 : 0;

        public static double Clamp(double v, double lo, double hi) => v < lo ? lo : v > hi ? hi : v;
    }
}
