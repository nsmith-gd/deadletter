using System;
using System.Collections.Generic;
using System.Linq;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Presentation;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// U-17b (#29): the photosensitivity check of port_architecture §4.29 (docs/unity/accessibility.md). The limits are
    /// WCAG 2.3.1's (three flashes in any second, a flash being a pair of opposing changes of ≥ 10 % where the darker state
    /// is below 0.80, unless the area is under a quarter of the 10° field). Each effect's curve is sampled over a few
    /// seconds at 60, 120 and 240 Hz: calm mode must always pass, whatever the area; with calm off the prototype's look is
    /// kept and the failures are the documented list.
    /// </summary>
    public class FlashSafetyTests
    {
        private static readonly double[] Rates = { 60, 120, 240 };

        /// <summary>The effects that fail with calm off (over three flashes a second over more than the small area), as documented.</summary>
        private static readonly string[] CalmOffFailures =
        {
            "dl01.openingWorkBulb", "dl01.cable", "dl01.cordLamp", "dl04.rowLamps", "dl04.rackLights", "dl05.rationStrip",
            "dl08.arcLight", "dl10.lobbyBulb", "dl11.laneBulb", "dl14.clutchLight",
        };

        public static IEnumerable<object[]> Effects() => FlashEffects.All().Where(e => e.HasCurve).Select(e => new object[] { e.Id });

        private static FlashEffect Effect(string id) => FlashEffects.All().Single(e => e.Id == id);

        private static FlashCount Worst(FlashEffect e, bool calm)
        {
            FlashCount worst = default;
            foreach (double r in Rates)
            {
                FlashCount c = e.Measure(calm, r);
                if (c.MaxTransitionsInWindow >= worst.MaxTransitionsInWindow) worst = c;
            }
            return worst;
        }

        private static double[] Square(double hz, double seconds, double rate, double lo = 0, double hi = 1)
            => Enumerable.Range(0, (int)(seconds * rate)).Select(i => Math.Sin(2 * Math.PI * hz * (i / rate) + 0.3) > 0 ? hi : lo).ToArray();

        [Fact]
        public void Limits_AreWcag231()
        {
            Assert.Equal(3, FlashSafety.MaxFlashesPerSecond);
            Assert.Equal(1.0, FlashSafety.Window);
            Assert.Equal(0.10, FlashSafety.LuminanceStep);
            Assert.Equal(0.80, FlashSafety.DarkerBelow);
            Assert.Equal(0.25 * 341 * 256 / (1024.0 * 768), FlashSafety.SmallAreaFraction, 12);   // ≈ 2.8 % of the screen
            Assert.InRange(FlashSafety.SmallAreaFraction, 0.0277, 0.0278);
        }

        [Theory]
        [InlineData(2.0, 2.0, true)]
        [InlineData(2.9, 3.0, true)]
        [InlineData(5.0, 5.0, false)]
        [InlineData(10.0, 10.0, false)]
        public void Counter_SquareWave_CountsOneFlashPerCycle(double hz, double flashes, bool within)
        {
            FlashCount c = FlashSafety.Count(Square(hz, 4, 240), 240);
            Assert.InRange(c.MaxFlashesPerSecond, flashes - 0.5, flashes + 0.5);
            Assert.Equal(within, c.WithinLimit);
        }

        [Fact]
        public void Counter_IgnoresSmallSteps_AndBrightOnlyFlicker()
        {
            // 9 % changes never count.
            Assert.Equal(0, FlashSafety.Count(Square(8, 3, 240, 0.91, 1.0), 240).Transitions);
            // Big enough, but the darker state is at or above 0.80: not a flash.
            Assert.Equal(0, FlashSafety.Count(Square(8, 3, 240, 0.80, 1.0), 240).Transitions);
            // The same swing reaching below 0.80 is.
            Assert.False(FlashSafety.Count(Square(8, 3, 240, 0.79, 1.0), 240).WithinLimit);
            // Relative to a given peak: 0.2 ↔ 0.3 of a peak of 2 is a 5 % change.
            Assert.Equal(0, FlashSafety.Count(Square(8, 3, 240, 0.2, 0.3), 240, peak: 2).Transitions);
        }

        [Fact]
        public void Counter_OnePulse_IsOneFlash()
        {
            var s = Enumerable.Range(0, 240).Select(i => i >= 60 && i < 80 ? 1.0 : 0).ToArray();
            FlashCount c = FlashSafety.Count(s, 240);
            Assert.Equal(2, c.Transitions);
            Assert.Equal(1, c.MaxFlashesPerSecond);
            Assert.Equal(1, c.LargestStep, 12);
        }

        [Fact]
        public void Counter_FollowRate_SmoothsAsThePrototypesLerpDoes()
        {
            // A 5 Hz ±0.4 target through a dt·10 follow (the DL-14 jam light, L5466) still swings well over 10 %.
            Func<double, double> target = t => 0.6 + 0.4 * Math.Sin(t * 31);
            FlashCount raw = FlashSafety.Count(target, 0, 4);
            FlashCount eased = FlashSafety.Count(target, 0, 4, followRate: 10);
            Assert.True(eased.LargestStep < raw.LargestStep);
            Assert.False(eased.WithinLimit);
        }

        [Fact]
        public void SaturatedRed_PressLampIs_ScannerIsNot()
        {
            Assert.True(FlashSafety.IsSaturatedRed(new Rgb(1, .16, .08)));     // EMIT.PressLamp, L483
            Assert.False(FlashSafety.IsSaturatedRed(Rgb.Hex(0xff4a2a)));          // the scanner's light, L2220
            Assert.False(FlashSafety.IsSaturatedRed(new Rgb(1, .55, .16)));     // C108BellLamp, L483
            Assert.False(FlashSafety.IsSaturatedRed(Rgb.Black));
            Assert.True(Effect("dl02.pressLamp").Red);
        }

        [Fact]
        public void Catalogue_IdsAreUnique_AndCiteLines()
        {
            var all = FlashEffects.All();
            Assert.Equal(all.Length, all.Select(e => e.Id).Distinct().Count());
            Assert.All(all, e => Assert.StartsWith("L", e.Lines));
            Assert.All(CalmOffFailures, id => Assert.Contains(all, e => e.Id == id));
        }

        /// <summary>Calm mode keeps every effect within three flashes a second, whatever its area or the frame rate.</summary>
        [Theory]
        [MemberData(nameof(Effects))]
        public void Calm_EveryEffectIsWithinTheLimit(string id)
        {
            FlashEffect e = Effect(id);
            foreach (double r in Rates)
            {
                FlashCount c = e.Measure(calm: true, r);
                Assert.True(c.WithinLimit, id + " at " + r + " Hz in calm mode: " + c);
            }
        }

        /// <summary>With calm off, exactly the documented effects fail (a newly failing or newly fixed effect updates accessibility.md).</summary>
        [Theory]
        [MemberData(nameof(Effects))]
        public void CalmOff_FailuresAreTheDocumentedOnes(string id)
        {
            FlashEffect e = Effect(id);
            bool fails = !FlashSafety.Passes(Worst(e, calm: false), e.ScreenFraction);
            Assert.True(fails == CalmOffFailures.Contains(id), id + " with calm off: " + Worst(e, false) + ", area " + e.ScreenFraction);
        }

        /// <summary>Every small-area effect that flashes over the limit with calm off still passes on area, and is calmed.</summary>
        [Fact]
        public void CalmOff_SmallFastEffects_PassOnAreaOnly()
        {
            foreach (string id in new[] { "dl04.cradleLamps", "dl09.cageBulb", "dl10.upLamps", "death.eye" })
            {
                FlashEffect e = Effect(id);
                Assert.False(Worst(e, false).WithinLimit, id);
                Assert.True(e.ScreenFraction <= FlashSafety.SmallAreaFraction, id);
            }
        }

        [Fact]
        public void Particles_AndShake_AreCalmDeviationsOrCalmGated()
        {
            var noCurve = FlashEffects.All().Where(e => !e.HasCurve).ToArray();
            Assert.Equal(new[] { "dl14.clutchSparks", "death.sparks", "camera.shake" }, noCurve.Select(e => e.Id));
            Assert.True(Effect("dl14.clutchSparks").CalmDeviation);   // L5459 bursts them whatever game.calm says; the port does not in calm
        }

        // ---- The ported curves themselves -----------------------------------------------------------------------------

        [Fact]
        public void Relay_IsOnePulseEverySixSeconds_CalmOrNot()
        {
            var relay = new PulseSequencer("dl01.relay", PulseParams.Dl01Relay());
            foreach (bool calm in new[] { false, true })
            {
                // Lamp 0 alone (its emissive, 18 · v) and the summed light, from the opening (sets at 5, 7, 14 s) into the repeats.
                FlashCount lamp = FlashSafety.Count(t => relay.ValueAtUnits(0, t * 24, calm), 0, 40, 0, 240);
                Assert.Equal(1, lamp.MaxFlashesPerSecond);
                Assert.True(Effect("dl01.relay").Measure(calm, 240).MaxFlashesPerSecond <= 1);
            }
        }

        [Fact]
        public void Cable_CalmIsASteadyGlow_OffIsTheStutter_L7939()
        {
            Assert.Equal(0.4, PrologueLighting.CableLevel(true, 1.234, calm: true));
            Assert.Equal(0, PrologueLighting.CableLevel(false, 1.234, calm: true));
            Assert.Equal(2.5, PrologueLighting.CableLevel(true, 0.01, calm: false));
            Assert.Equal(0.75, PrologueLighting.CableLevel(true, Math.PI / 90 + 0.01, calm: false), 12);
        }

        [Fact]
        public void Cradle_CalmEasesTheSeatedLamps_WithoutFlicker()
        {
            Assert.Equal(Cradle.SeatedLamp(0.05), Cradle.SeatedLamp(0.05, calm: false));   // the prototype's, unchanged
            double prev = 0;
            for (double t = 0; t < 4; t += 1 / 60.0)
            {
                double v = Cradle.SeatedLamp(t, calm: true);
                Assert.True(v >= prev - 1e-12);
                prev = v;
            }
            Assert.Equal(0.55, Cradle.SeatedLamp(2.2, calm: true), 12);
            Assert.Equal(0.55, Cradle.SeatedLamp(9, calm: true), 12);
            Assert.Equal(0, Cradle.SeatedLamp(-1, calm: true));
        }

        [Fact]
        public void DeathEye_CalmFadesOut_WithoutTheStutter_L7447()
        {
            Assert.Equal(DeathProfile.EyeLevel(0.1), DeathProfile.EyeLevel(0.1, calm: false));
            Assert.Equal(1 - 0.1 / DeathProfile.EyeOut, DeathProfile.EyeLevel(0.1, calm: true), 12);
            Assert.Equal(0, DeathProfile.EyeLevel(DeathProfile.EyeOut, calm: true));
            Assert.True(FlashSafety.Count(t => DeathProfile.EyeLevel(t, true), 0, 1, 0, 240).WithinLimit);
        }

        [Fact]
        public void PressLamp_CalmHoldsTheTell_L7347()
        {
            var p = PeriodicCrusherParams.Dl02Press();
            Assert.Equal(2, PeriodicCrusher.LampAt(p, 0.2, calm: true));
            Assert.Equal(0.4, PeriodicCrusher.LampAt(p, 0.2, calm: false));     // sin(5) < −0.2
            Assert.Equal(0, PeriodicCrusher.LampAt(p, 1.2, calm: false));
        }

        [Fact]
        public void RationStrip_StuttersNearTenHertz_WhenCalmOff()
        {
            FlashCount c = Effect("dl05.rationStrip").Measure(calm: false, 240);
            Assert.InRange(c.MaxFlashesPerSecond, 9, 11);                          // sin(61t) square: 9.7 Hz for ~1.08 s every 8.98 s
            Assert.Equal(0, Effect("dl05.rationStrip").Measure(calm: true, 240).Transitions);
        }
    }
}
