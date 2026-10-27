using System;

namespace DeadLetter.Core.Maths
{
    /// <summary>
    /// Frame-rate independent replacement for the prototype's per-frame easing <c>x += (target − x)·min(1, dt·k)</c>
    /// (port_architecture §3.1, §9 #10). The returned fraction equals <c>min(1, k/60)</c> for one 60 Hz step and
    /// compounds exactly at any other step, so two 1/120 s steps cover the same ground as one 1/60 s step.
    /// </summary>
    public static class Damp
    {
        public const double ReferenceHz = 60.0;

        /// <summary>The fraction of the remaining distance to cover this step (0..1).</summary>
        public static double Factor(double ratePerSecond, double dt, double referenceHz = ReferenceHz)
        {
            if (dt <= 0 || ratePerSecond <= 0) return 0;
            return 1.0 - Smooth.DecayFactor(ratePerSecond, dt, referenceHz);
        }

        /// <summary><c>value</c> moved toward <c>target</c> by <see cref="Factor"/>.</summary>
        public static double Toward(double value, double target, double ratePerSecond, double dt) =>
            value + (target - value) * Factor(ratePerSecond, dt);

        public static Vec3 Toward(Vec3 value, Vec3 target, double ratePerSecond, double dt) =>
            Vec3.Lerp(value, target, Factor(ratePerSecond, dt));
    }
}
