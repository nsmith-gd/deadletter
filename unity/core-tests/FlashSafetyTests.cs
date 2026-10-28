using System;
using System.Collections.Generic;
using System.Linq;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Presentation;
using DeadLetter.Core.Scenes;
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

        /// <summary>
        /// The effects that fail with calm off (over three flashes a second, over more than the small area once everything
        /// flashing in the same scene is summed), as documented.
        /// </summary>
        private static readonly string[] CalmOffFailures =
        {
            "dl01.openingWorkBulb", "dl01.cable", "dl01.cordLamp", "dl04.rowLamps", "dl04.rackLights", "dl04.cradleLamps",
            "dl05.rationStrip", "dl08.arcLight", "dl10.upLamps", "dl10.lobbyBulb", "dl11.laneBulb", "dl14.clutchLight", "death.eye",
        };

        public static IEnumerable<object[]> Effects() => FlashEffects.All().Where(e => e.HasCurve).Select(e => new object[] { e.Id });

        private static FlashEffect Effect(string id) => FlashEffects.All().Single(e => e.Id == id);

        private static readonly Dictionary<(bool, double), FlashAssessment[]> Assessed = new Dictionary<(bool, double), FlashAssessment[]>();

        /// <summary>The whole catalogue assessed once per calm setting and rate (combined areas need every effect).</summary>
        private static FlashAssessment Assessment(string id, bool calm, double rate)
        {
            FlashAssessment[] all;
            lock (Assessed)
                if (!Assessed.TryGetValue((calm, rate), out all)) Assessed.Add((calm, rate), all = FlashEffects.Assess(FlashEffects.All(), calm, rate));
            return all.Single(a => a.Effect.Id == id);
        }

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
                Assert.True(e.Measure(calm: true, r, red: true).WithinLimit, id + " (red rule) at " + r + " Hz in calm mode");
                Assert.True(Assessment(id, calm: true, r).Passes, Assessment(id, true, r).ToString());
            }
        }

        /// <summary>With calm off, exactly the documented effects fail (a newly failing or newly fixed effect updates accessibility.md).</summary>
        [Theory]
        [MemberData(nameof(Effects))]
        public void CalmOff_FailuresAreTheDocumentedOnes(string id)
        {
            var failing = Rates.Select(r => Assessment(id, calm: false, r)).Where(a => !a.Passes).ToArray();
            bool fails = failing.Length > 0;
            Assert.True(fails == CalmOffFailures.Contains(id),
                id + " with calm off: " + (fails ? failing[0].ToString() : Assessment(id, false, 240).ToString()));
        }

        /// <summary>
        /// The small effects that flash over the limit with calm off: each is under the area threshold alone, but only the
        /// cage bulb stays under it once its scene's other fast flashers are summed (WCAG's combined area). All are calmed.
        /// </summary>
        [Fact]
        public void CalmOff_SmallFastEffects_AreJudgedByTheCombinedArea()
        {
            foreach (string id in new[] { "dl04.cradleLamps", "dl09.cageBulb", "dl10.upLamps", "death.eye" })
            {
                FlashEffect e = Effect(id);
                Assert.False(Worst(e, false).WithinLimit, id);
                Assert.True(e.ScreenFraction <= FlashSafety.SmallAreaFraction, id);
                Assert.True(Worst(e, true).WithinLimit, id);
            }
            Assert.True(Assessment("dl09.cageBulb", false, 240).Passes);                                    // with the dying eye: 1.2 %
            Assert.InRange(Assessment("dl09.cageBulb", false, 240).CombinedArea, 0.0119, 0.0121);
            Assert.False(Assessment("dl04.cradleLamps", false, 240).Passes);                                 // with the row lamps and rack lights
            Assert.False(Assessment("dl10.upLamps", false, 240).Passes);                                     // with the lobby bulb
            Assert.False(Assessment("death.eye", false, 240).Passes);                                        // anywhere: its worst scene
        }

        [Fact]
        public void CombinedArea_SumsWhatFlashesInOneScene_AndEverywhereEffectsTakeTheirWorstScene()
        {
            Func<double, bool, double> fast = (t, calm) => Math.Sin(t * 40) > 0 ? 1 : 0;   // 6.4 Hz
            Func<double, bool, double> slow = (t, calm) => Math.Sin(t * 2) > 0 ? 1 : 0;    // 0.3 Hz
            var a = new FlashEffect("s1.a", "L1", FlashKind.Emissive, 0.02, 0, 3, fast, ported: false);
            var b = new FlashEffect("s1.b", "L1", FlashKind.Emissive, 0.02, 0, 3, fast, ported: false);
            var c = new FlashEffect("s1.c", "L1", FlashKind.Light, 0.5, 0, 3, slow, ported: false);   // large but slow: not summed
            var d = new FlashEffect("s2.d", "L1", FlashKind.Emissive, 0.02, 0, 3, fast, ported: false);
            var e = new FlashEffect("any.e", "L1", FlashKind.Emissive, 0.001, 0, 3, fast, ported: false, scene: FlashEffects.Everywhere);
            Assert.Equal("s1", a.Scene);

            var lone = FlashEffects.Assess(new[] { a, c, d }, calm: false, 240);
            Assert.All(lone, r => Assert.True(r.Passes, r.ToString()));                                     // 2 % each, alone in its scene
            var all = FlashEffects.Assess(new[] { a, b, c, d, e }, calm: false, 240);
            Assert.Equal(0.041, all[0].CombinedArea, 12);                                                    // a + b + e
            Assert.False(all[0].Passes);
            Assert.False(all[1].Passes);
            Assert.True(all[2].Passes);                                                                      // within the limit
            Assert.Equal(0.021, all[3].CombinedArea, 12);                                                    // d + e: s1 is not on screen
            Assert.True(all[3].Passes);
            Assert.Equal(0.041, all[4].CombinedArea, 12);                                                    // e's worst scene is s1
            Assert.False(all[4].Passes);
        }

        // ---- The red flash rule -----------------------------------------------------------------------------------------

        [Fact]
        public void RedFlash_LargeSaturatedRedOverTheLimitFails_SmallPasses()
        {
            var red = FlashEffects.PressLampColour;
            Assert.True(FlashSafety.IsSaturatedRed(red));
            double[] fast = Square(5, 3, 240);
            Assert.False(FlashSafety.Passes(fast, 240, red, combinedArea: 0.2));
            Assert.True(FlashSafety.Passes(fast, 240, red, combinedArea: 0.01));
            Assert.True(FlashSafety.Passes(Square(2, 3, 240), 240, red, combinedArea: 0.2));                 // within three a second

            // A bright-only flicker (never below 0.80) is no general flash, but every transition into and out of the red counts.
            double[] bright = Square(5, 3, 240, 0.85, 1.0);
            Assert.Equal(0, FlashSafety.Count(bright, 240).Transitions);
            Assert.False(FlashSafety.Count(bright, 240, red: true).WithinLimit);
            Assert.False(FlashSafety.Passes(bright, 240, red, combinedArea: 0.2));
            Assert.True(FlashSafety.Passes(bright, 240, red, combinedArea: 0.01));
            Assert.True(FlashSafety.Passes(bright, 240, new Rgb(1, 0.55, 0.16), combinedArea: 0.2));          // amber: the general rule only
        }

        [Fact]
        public void RedFlash_AppliesToTheCataloguesRedSources()
        {
            var big = new FlashEffect("red.big", "L1", FlashKind.Light, 0.2, 0, 3, (t, calm) => Math.Sin(t * 31) > 0 ? 1 : 0.85,
                ported: false, colour: FlashEffects.PressLampColour);
            var small = new FlashEffect("red.small", "L1", FlashKind.Emissive, 0.005, 0, 3, (t, calm) => Math.Sin(t * 31) > 0 ? 1 : 0.85,
                ported: false, colour: FlashEffects.PressLampColour);
            Assert.True(big.Measure(false, 240).WithinLimit);                                                // no general flash
            var r = FlashEffects.Assess(new[] { big }, calm: false, 240);
            Assert.False(r[0].Passes, r[0].ToString());
            Assert.True(FlashEffects.Assess(new[] { small }, calm: false, 240)[0].Passes);
            Assert.True(Effect("dl02.pressLamp").Red);
            Assert.False(Effect("pips.reject").Red);                                                         // 0.77: just under
        }

        [Fact]
        public void Particles_AndShake_AreCalmDeviationsOrCalmGated()
        {
            var noCurve = FlashEffects.All().Where(e => !e.HasCurve).ToArray();
            Assert.Equal(new[] { "dl14.clutchSparks", "death.sparks", "camera.shake" }, noCurve.Select(e => e.Id));
            Assert.True(Effect("dl14.clutchSparks").CalmDeviation);   // L5459 bursts them whatever game.calm says; the port does not in calm
            Assert.False(Effect("death.sparks").CalmDeviation);       // L7440, L7448: the prototype gates them itself

            // death.sparks, through Core: the profile and the death act, with calm read from the graph (Settings.Calm).
            foreach (DeathKind kind in Enum.GetValues(typeof(DeathKind)))
            {
                var p = DeathProfile.Of(kind);
                Assert.Equal(0, p.SparksFor(calm: true));
                Assert.Equal(0, p.SparkRateFor(calm: true));
                Assert.Equal(p.Sparks, p.SparksFor(calm: false));
                Assert.Equal(kind == DeathKind.Shock ? DeathProfile.ShockSparkRate : 0, p.SparkRateFor(calm: false));
            }
            foreach (bool calm in new[] { false, true })
            {
                var sim = new ChapterSim(ChapterDefs.Prologue()) { Clock = 40 };
                sim.Begin("room");
                sim.Graph.Calm = calm;
                Assert.True(sim.Die(DeathKind.Shock, sinkRate: 0.8));
                var act = (DeathAct)sim.Act;
                Assert.Equal(calm, act.Calm);
                Assert.Equal(calm ? 0 : 44, act.Sparks);
                Assert.Equal(calm ? 0 : 14, act.SparkRate);
                sim.Step(default);
                Assert.Equal(calm ? 0 : 14, act.SparkRate);
                sim.Graph.Calm = !calm;                                                                      // the option changes mid-death
                sim.Step(default);
                Assert.Equal(!calm, act.Calm);
                Assert.Equal(calm ? 44 : 0, act.Sparks);
            }
        }

        [Fact]
        public void DeathAct_TheEyeFollowsCalm_FromTheGraph()
        {
            foreach (bool calm in new[] { false, true })
            {
                var sim = new ChapterSim(ChapterDefs.Prologue()) { Clock = 40 };
                sim.Begin("room");
                sim.Graph.Calm = calm;
                sim.Die(DeathKind.Grabbed, sinkRate: 0.8);
                var act = (DeathAct)sim.Act;
                var eye = new List<double>();
                for (int i = 0; i < 40; i++)
                {
                    sim.Step(default);
                    Assert.Equal(DeathProfile.EyeLevel(act.T, calm), act.EyeLevel, 12);
                    eye.Add(act.EyeLevel);
                }
                int transitions = FlashSafety.Count(eye.ToArray(), 1 / ChapterSim.StepSeconds).Transitions;
                if (calm) Assert.True(transitions <= 1, "calm eye: " + transitions);                         // a plain fade: one fall
                else Assert.True(transitions > 2, "eye: " + transitions);                                    // the stutter
            }
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
            Assert.Equal(0.1, DeathProfile.EyeLevel(Math.PI / 70 + 0.01, calm: false));                  // sin(70t) < 0: the stutter's dark
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
