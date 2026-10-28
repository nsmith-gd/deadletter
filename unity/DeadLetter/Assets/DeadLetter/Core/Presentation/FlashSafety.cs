using System;

namespace DeadLetter.Core.Presentation
{
    /// <summary>
    /// What a flash measurement found (<see cref="FlashSafety.Count(double[], double, double)"/>).
    /// </summary>
    public readonly struct FlashCount
    {
        /// <summary>Opposing luminance changes that qualify (≥ <see cref="FlashSafety.LuminanceStep"/> of the peak, darker state below <see cref="FlashSafety.DarkerBelow"/>), over the whole curve.</summary>
        public readonly int Transitions;
        /// <summary>The most qualifying transitions inside any <see cref="FlashSafety.Window"/>.</summary>
        public readonly int MaxTransitionsInWindow;
        /// <summary>The largest qualifying change, as a fraction of the peak (0 when none qualified).</summary>
        public readonly double LargestStep;

        public FlashCount(int transitions, int maxInWindow, double largestStep)
        {
            Transitions = transitions; MaxTransitionsInWindow = maxInWindow; LargestStep = largestStep;
        }

        /// <summary>Flashes in the worst window: a flash is a pair of opposing changes, so transitions / 2.</summary>
        public double MaxFlashesPerSecond => MaxTransitionsInWindow / 2.0;

        /// <summary>No more than <see cref="FlashSafety.MaxFlashesPerSecond"/> flashes in any window.</summary>
        public bool WithinLimit => MaxFlashesPerSecond <= FlashSafety.MaxFlashesPerSecond;

        public override string ToString()
            => MaxFlashesPerSecond.ToString("0.#") + " flashes/s, step " + LargestStep.ToString("0.##") + " (" + Transitions + " transitions)";
    }

    /// <summary>
    /// The photosensitivity limits (port_architecture §4.29; docs/unity/accessibility.md) as data, and a counter that
    /// measures a sampled intensity curve against them. The limits are WCAG 2.x SC 2.3.1 "Three Flashes or Below
    /// Threshold" (the same three-per-second rule as ITU-R BT.1702 and Ofcom's guidance): a <b>flash</b> is a pair of
    /// opposing changes in relative luminance of <see cref="LuminanceStep"/> or more of the maximum, where the darker state
    /// is below <see cref="DarkerBelow"/>; content may not flash more than <see cref="MaxFlashesPerSecond"/> times in any
    /// one second unless the flashing area stays under the general and red flash thresholds (<see cref="SmallAreaFraction"/>).
    /// <para>The counter is conservative: it takes a light's level relative to its own peak as the relative luminance of
    /// what it lights (the real change on screen is smaller: ambient, fog, tone mapping and the light's falloff all
    /// dilute it), and it counts each change once it has moved <see cref="LuminanceStep"/> from the last extreme.</para>
    /// </summary>
    public static class FlashSafety
    {
        /// <summary>WCAG 2.3.1: no more than three flashes in any one second.</summary>
        public const double MaxFlashesPerSecond = 3;
        /// <summary>The counting window, seconds.</summary>
        public const double Window = 1.0;
        /// <summary>A change counts when it is at least 10 % of the maximum relative luminance.</summary>
        public const double LuminanceStep = 0.10;
        /// <summary>…and the darker of the two states is below 0.80.</summary>
        public const double DarkerBelow = 0.80;
        /// <summary>A colour is saturated red when R / (R + G + B) ≥ 0.8 (WCAG 2.2's red flash definition).</summary>
        public const double SaturatedRedRatio = 0.8;

        /// <summary>The 10° visual field at typical viewing distance: 341 × 256 px of a 1024 × 768 screen (WCAG's note).</summary>
        public const int FieldWidth = 341, FieldHeight = 256, ScreenWidth = 1024, ScreenHeight = 768;
        /// <summary>A flash below a quarter of that field is below the general and red flash thresholds.</summary>
        public const double FieldShare = 0.25;
        /// <summary>That area as a fraction of the whole screen: 0.25 · 341 · 256 / (1024 · 768) ≈ 2.8 %.</summary>
        public const double SmallAreaFraction = FieldShare * FieldWidth * FieldHeight / (double)(ScreenWidth * ScreenHeight);

        /// <summary>The frame rate the curves are sampled at by default (the game's render rate).</summary>
        public const double FrameRate = 60;

        /// <summary>Saturated red per WCAG 2.2: R / (R + G + B) ≥ <see cref="SaturatedRedRatio"/>.</summary>
        public static bool IsSaturatedRed(Rgb c)
        {
            double sum = c.R + c.G + c.B;
            return sum > 0 && c.R / sum >= SaturatedRedRatio;
        }

        /// <summary>An effect passes when it is within the flash limit, or its flashing area is under the thresholds.</summary>
        public static bool Passes(in FlashCount count, double screenFraction) => count.WithinLimit || screenFraction <= SmallAreaFraction;

        /// <summary>
        /// Samples <paramref name="level"/> from <paramref name="from"/> for <paramref name="seconds"/> at
        /// <paramref name="sampleRate"/> and counts its flashes (<see cref="Count(double[], double, double)"/>).
        /// <paramref name="followRate"/> &gt; 0 passes the curve through the prototype's per-frame follow
        /// (<c>v += (target − v) · min(1, dt · rate)</c>) first, as a light that eases toward its target is seen.
        /// </summary>
        public static FlashCount Count(Func<double, double> level, double from, double seconds, double peak = 0,
            double sampleRate = FrameRate, double followRate = 0)
        {
            if (level == null) throw new ArgumentNullException(nameof(level));
            if (!(sampleRate > 0) || !(seconds > 0)) throw new ArgumentException("Need a positive sample rate and span.");
            int n = (int)Math.Ceiling(seconds * sampleRate) + 1;
            var s = new double[n];
            double dt = 1 / sampleRate, v = level(from);
            for (int i = 0; i < n; i++)
            {
                double target = level(from + i * dt);
                v = followRate > 0 && i > 0 ? v + (target - v) * Math.Min(1, dt * followRate) : target;
                s[i] = v;
            }
            return Count(s, sampleRate, peak);
        }

        /// <summary>
        /// Counts the flashes in <paramref name="samples"/> (taken at <paramref name="sampleRate"/>), each relative to
        /// <paramref name="peak"/> (≤ 0: the samples' own maximum). A transition is registered when the level has moved
        /// <see cref="LuminanceStep"/> away from the extreme since the last transition, in the opposite direction; it
        /// qualifies when the dark side of it (the trough before a rise, or the trough after a fall) is below
        /// <see cref="DarkerBelow"/>. Returns the qualifying transitions and the most of them in any <see cref="Window"/>.
        /// </summary>
        public static FlashCount Count(double[] samples, double sampleRate, double peak = 0)
        {
            if (samples == null) throw new ArgumentNullException(nameof(samples));
            if (samples.Length == 0) return new FlashCount(0, 0, 0);
            if (!(peak > 0)) { peak = 0; for (int i = 0; i < samples.Length; i++) peak = Math.Max(peak, samples[i]); }
            if (!(peak > 0)) return new FlashCount(0, 0, 0);

            int n = samples.Length;
            var at = new int[n];          // sample index of each raw transition
            var dir = new int[n];         // +1 rise, −1 fall
            var size = new double[n];     // change from the extreme, fraction of peak
            var trough = new double[n];   // the dark side: before a rise, after a fall
            int raw = 0, d = 0;
            double v0 = samples[0] / peak, hi = v0, lo = v0;
            for (int i = 1; i < n; i++)
            {
                double v = samples[i] / peak;
                if (d != 1 && v - lo >= LuminanceStep)
                {
                    if (raw > 0 && dir[raw - 1] == -1) trough[raw - 1] = lo;     // the fall bottomed out at lo
                    at[raw] = i; dir[raw] = 1; size[raw] = v - lo; trough[raw] = lo; raw++;
                    d = 1; hi = v;
                }
                else if (d != -1 && hi - v >= LuminanceStep)
                {
                    at[raw] = i; dir[raw] = -1; size[raw] = hi - v; trough[raw] = v; raw++;
                    d = -1; lo = v;
                }
                else if (d == 1) hi = Math.Max(hi, v);
                else if (d == -1) lo = Math.Min(lo, v);
                else { hi = Math.Max(hi, v); lo = Math.Min(lo, v); }
            }
            if (raw > 0 && dir[raw - 1] == -1) trough[raw - 1] = lo;

            var t = new double[raw];
            int count = 0;
            double largest = 0;
            for (int k = 0; k < raw; k++)
            {
                if (!(trough[k] < DarkerBelow)) continue;
                t[count++] = at[k] / sampleRate;
                largest = Math.Max(largest, size[k]);
            }
            int worst = 0;
            for (int i = 0, j = 0; i < count; i++)
            {
                if (j < i) j = i;
                while (j < count && t[j] - t[i] <= Window + 1e-9) j++;
                worst = Math.Max(worst, j - i);
            }
            return new FlashCount(count, worst, largest);
        }
    }
}
