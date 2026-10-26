namespace DeadLetter.Core.Mechanisms.Docks
{
    /// <summary>
    /// Detents on a push rail (§4.13b, DL-15 L5535, L5569–L5572): a push stops at the first detent it reaches. A pure
    /// rule (no state), for the Push family's range function (<c>figRange15</c>) to apply after its own limits.
    /// </summary>
    public static class RailDetents
    {
        /// <summary>DL-15: the lift's middle 281.9 and the two seats 283.2, 284.6 (<c>ATT2_DETENTS</c>, L5535).</summary>
        public static readonly double[] Dl15 = { 281.9, 283.2, 284.6 };

        /// <summary>A detent closer than this to where the push started does not stop it (L5571–L5572).</summary>
        public const double Slack = 0.02;

        /// <summary>
        /// Narrow [lo, hi] to the nearest detent beyond <paramref name="from"/> (the x the push started at) on each side,
        /// then return hi ≥ lo (<c>[lo, max(lo, hi)]</c>, L5570–L5573). <paramref name="detents"/> are ascending.
        /// </summary>
        public static void Limit(double[] detents, double from, ref double lo, ref double hi)
        {
            for (int i = 0; i < detents.Length; i++)
                if (detents[i] > from + Slack) { if (detents[i] < hi) hi = detents[i]; break; }
            for (int i = detents.Length - 1; i >= 0; i--)
                if (detents[i] < from - Slack) { if (detents[i] > lo) lo = detents[i]; break; }
            if (hi < lo) hi = lo;
        }
    }
}
