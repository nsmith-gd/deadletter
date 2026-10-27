using System;

namespace DeadLetter.Core.Push
{
    /// <summary>
    /// Stops along a pushable's travel (pass 8: DL-15's seats and lift, DL-16a's stool; <c>figRange15</c>, L5569–L5573,
    /// L6457): a push stops at the first detent it reaches either way, measured from where he took hold (<c>pushFrom</c>),
    /// and the motor lets go there (<see cref="Interaction.IPushable.HasDetents"/>, L4717–L4722). A detent within 0.02 of
    /// the start does not hold it, so a push from a detent goes on to the next one.
    /// </summary>
    public static class Detents
    {
        /// <summary>A detent closer than this to where the push started does not stop it (<c>d &gt; from + 0.02</c>, L5571).</summary>
        public const double Slack = 0.02;

        /// <summary>
        /// Narrows the travel [<paramref name="lo"/>, <paramref name="hi"/>] to the detents either side of
        /// <paramref name="from"/> (ascending <paramref name="detents"/>), and keeps hi ≥ lo (<c>[lo, max(lo, hi)]</c>, L5573).
        /// </summary>
        public static void Clamp(double[] detents, double from, ref double lo, ref double hi)
        {
            if (detents == null) throw new ArgumentNullException(nameof(detents));
            for (int i = 0; i < detents.Length; i++)
                if (detents[i] > from + Slack) { hi = Math.Min(hi, detents[i]); break; }       // L5571
            for (int i = detents.Length - 1; i >= 0; i--)
                if (detents[i] < from - Slack) { lo = Math.Max(lo, detents[i]); break; }       // L5572
            if (hi < lo) hi = lo;                                                             // L5573
        }

        /// <summary>True when <paramref name="detents"/> is ascending (checked once by <see cref="PushableParams"/> users).</summary>
        public static bool IsAscending(double[] detents)
        {
            if (detents == null) return false;
            for (int i = 1; i < detents.Length; i++) if (!(detents[i] > detents[i - 1])) return false;
            return true;
        }
    }
}
