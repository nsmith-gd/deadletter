using System;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Drives;

namespace DeadLetter.Core.Presentation
{
    /// <summary>What an effect changes on screen.</summary>
    public enum FlashKind
    {
        /// <summary>A real light: it changes the surfaces it reaches.</summary>
        Light,
        /// <summary>An emissive lamp or bulb: only its own few pixels (and their bloom).</summary>
        Emissive,
        /// <summary>Spark particles: small moving points, each fading out.</summary>
        Particles,
        /// <summary>The whole screen (a cut or a fade).</summary>
        Screen,
        /// <summary>Camera motion (a shake): no luminance change of its own.</summary>
        Motion,
    }

    /// <summary>
    /// One flashing or flickering effect of the prologue and chapters 1 and 2, as data for the photosensitivity check
    /// (port_architecture §4.29; docs/unity/accessibility.md): where the prototype makes it, how much of the screen it
    /// can light (a conservative estimate from the framing, §4.17), and its level over time with calm mode off and on.
    /// <see cref="Ported"/> effects evaluate Core's own curve (the one the presentation uses); the others carry the
    /// prototype's curve as the spec for U-15's light curves, with the calm variant the port must use.
    /// </summary>
    public sealed class FlashEffect
    {
        /// <summary>How many trigger phases <see cref="Measure"/> tries across <see cref="PhaseSpan"/>.</summary>
        public const int PhaseSteps = 48;

        private readonly Func<double, double, bool, double> _level;

        public FlashEffect(string id, string lines, FlashKind kind, double screenFraction, double from, double seconds,
            Func<double, bool, double> level, bool ported, bool calmDeviation = false, Rgb? colour = null, double followRate = 0, string scene = null)
            : this(id, lines, kind, screenFraction, from, seconds, 0, level == null ? null : (Func<double, double, bool, double>)((t, phase, calm) => level(t, calm)),
                ported, calmDeviation, colour, followRate, scene)
        {
        }

        /// <param name="phaseSpan">The trigger can fall anywhere in this span relative to the clock its flicker runs on (a
        /// spark against <c>sin(90 · clock)</c>): <see cref="Measure"/> takes the worst of <see cref="PhaseSteps"/> phases.</param>
        /// <param name="colour">The source's colour when the red flash rule could apply (null: not red).</param>
        /// <param name="scene">What it can share the screen with (<see cref="Scene"/>); null: the id's scene prefix ("dl04").</param>
        public FlashEffect(string id, string lines, FlashKind kind, double screenFraction, double from, double seconds, double phaseSpan,
            Func<double, double, bool, double> level, bool ported, bool calmDeviation = false, Rgb? colour = null, double followRate = 0, string scene = null)
        {
            Id = id ?? throw new ArgumentNullException(nameof(id));
            Lines = lines; Kind = kind; ScreenFraction = screenFraction; From = from; Seconds = seconds; PhaseSpan = phaseSpan;
            _level = level; Ported = ported; CalmDeviation = calmDeviation; Colour = colour; FollowRate = followRate;
            int dot = id.IndexOf('.');
            Scene = scene ?? (dot > 0 ? id.Substring(0, dot) : id);
        }

        /// <summary>A stable name, "scene.effect".</summary>
        public string Id { get; }
        /// <summary>The prototype lines (index.html) the curve comes from.</summary>
        public string Lines { get; }
        public FlashKind Kind { get; }
        /// <summary>The largest share of a 1024 × 768 frame it can change at once (conservative; compare <see cref="FlashSafety.SmallAreaFraction"/>).</summary>
        public double ScreenFraction { get; }
        /// <summary>The span the curve is sampled over, seconds (local time: from the effect's trigger, or the game clock for a running one).</summary>
        public double From { get; }
        public double Seconds { get; }
        /// <summary>Core's own curve (the presentation evaluates this function), not a transcription of the prototype's.</summary>
        public bool Ported { get; }
        /// <summary>The prototype ignores calm mode here; the port's calm curve (this one) steadies it (§4.29).</summary>
        public bool CalmDeviation { get; }
        /// <summary>The source's colour, where it matters for the red flash rule (null: not red).</summary>
        public Rgb? Colour { get; }
        /// <summary>Its colour is saturated red (<see cref="FlashSafety.IsSaturatedRed"/>), so the red flash rule applies too.</summary>
        public bool Red => Colour.HasValue && FlashSafety.IsSaturatedRed(Colour.Value);
        /// <summary>
        /// The scene it plays in: effects of one scene can be on screen together, so their areas are summed
        /// (<see cref="FlashEffects.CombinedArea"/>). <see cref="FlashEffects.Everywhere"/>: it can play in any scene.
        /// </summary>
        public string Scene { get; }
        /// <summary>The prototype eases the light toward the curve (<c>v += (target − v) · min(1, dt · rate)</c>); 0: none.</summary>
        public double FollowRate { get; }
        /// <summary>The span of trigger phases measured (0: the curve has a fixed phase).</summary>
        public double PhaseSpan { get; }
        /// <summary>Whether a curve exists (particles and motion have none).</summary>
        public bool HasCurve => _level != null;

        /// <summary>The level at <paramref name="t"/> (in the effect's own units).</summary>
        public double Level(double t, bool calm, double phase = 0) => _level != null ? _level(t, phase, calm) : 0;

        /// <summary>
        /// The effect's flashes over its span, at <paramref name="sampleRate"/>: the worst trigger phase. <paramref name="red"/>
        /// counts under the red flash rule (<see cref="FlashSafety.Count(double[], double, double, bool)"/>).
        /// </summary>
        public FlashCount Measure(bool calm, double sampleRate = FlashSafety.FrameRate, bool red = false)
        {
            if (_level == null) return new FlashCount(0, 0, 0);
            int steps = PhaseSpan > 0 ? PhaseSteps : 1;
            FlashCount worst = default;
            for (int k = 0; k < steps; k++)
            {
                double phase = PhaseSpan * k / steps;
                FlashCount c = FlashSafety.Count(t => _level(t, phase, calm), From, Seconds, 0, sampleRate, FollowRate, red);
                if (k == 0 || c.MaxTransitionsInWindow > worst.MaxTransitionsInWindow) worst = c;
            }
            return worst;
        }

        public override string ToString() => Id;
    }

    /// <summary>One effect's result in <see cref="FlashEffects.Assess"/>.</summary>
    public readonly struct FlashAssessment
    {
        public readonly FlashEffect Effect;
        /// <summary>The general flash count.</summary>
        public readonly FlashCount General;
        /// <summary>The red flash count (the general one when the source is not saturated red).</summary>
        public readonly FlashCount RedCount;
        /// <summary>The combined area it was judged by (<see cref="FlashEffects.CombinedArea"/>).</summary>
        public readonly double CombinedArea;
        /// <summary>Both rules pass: within the limit, or the combined area is under the thresholds.</summary>
        public readonly bool Passes;

        public FlashAssessment(FlashEffect effect, FlashCount general, FlashCount redCount, double combinedArea, bool passes)
        {
            Effect = effect; General = general; RedCount = redCount; CombinedArea = combinedArea; Passes = passes;
        }

        public override string ToString()
            => Effect + ": " + General + (Effect != null && Effect.Red ? ", red " + RedCount : "") + ", combined area " + CombinedArea.ToString("0.###");
    }

    /// <summary>
    /// The catalogue of flashing and flickering effects in the prologue and chapter 1 (docs/unity/accessibility.md has the
    /// table). Calm mode must keep every one within <see cref="FlashSafety.MaxFlashesPerSecond"/> whatever its area; with
    /// calm off the prototype's look is kept, and the ones over the limit are listed as warnings.
    /// </summary>
    public static class FlashEffects
    {
        /// <summary>The <see cref="FlashEffect.Scene"/> of an effect that can play in any scene (a death, the glints, Pips).</summary>
        public const string Everywhere = "*";
        /// <summary><c>EMIT.PressLamp</c> (L483): saturated red (0.88).</summary>
        public static readonly Rgb PressLampColour = new Rgb(1, 0.16, 0.08);
        /// <summary>Pips' <c>RED</c> (L6853): 0.77, just under saturated red.</summary>
        public static readonly Rgb PipsRed = new Rgb(1, 0.22, 0.08);

        /// <summary>DL-01's frame rate for its authored timelines (FPS, L268).</summary>
        public const double Fps = 24;
        /// <summary>The cable's crackles come every 3–8 s (L7938): sampled at the closest spacing.</summary>
        public static readonly double[] CableSparks = { 0.5, 3.5, 6.5 };
        /// <summary>The crackle's 0.18 s against the stutter's <c>sin(90t)</c> (a period of 2π / 90 s): every phase is tried.</summary>
        public const double CablePhase = 2 * Math.PI / 90;
        /// <summary>The opening's spark frames (SPARKS, L333), lit for 2 frames each (L1565).</summary>
        public static readonly double[] OpeningSparks = { 150, 153, 196 };
        /// <summary>The opening's flicker patterns (frame offset, level), L1552–L1576.</summary>
        public static readonly double[,] ParcelPattern = { { 0, .5 }, { 3, 0 }, { 7, .8 }, { 9, .15 }, { 16, 1 }, { 19, .4 } };
        public static readonly double[,] BulbPattern = { { 0, .6 }, { 2, 0 }, { 6, .9 }, { 8, .1 }, { 13, 0 }, { 17, 1 }, { 19, .5 }, { 24, 1 } };
        public static readonly double[,] EyesPattern = { { 0, .8 }, { 2, 0 }, { 6, 1 }, { 9, .2 }, { 14, 1 } };

        /// <summary>
        /// The opening's <c>flicker(f, start, pattern, steady)</c> (L1528–L1533): before start 0; then the pattern's steps,
        /// then steady; calm: a smooth 20-frame ramp to steady.
        /// </summary>
        public static double OpeningFlicker(double f, double start, double[,] pattern, double steady, bool calm)
        {
            if (f < start) return 0;
            if (calm) return Smooth.Step((f - start) / 20) * steady;
            double v = 0;
            int n = pattern.GetLength(0);
            for (int i = 0; i < n; i++) if (f - start >= pattern[i, 0]) v = pattern[i, 1];
            return f - start >= pattern[n - 1, 0] ? steady : v;
        }

        /// <summary>A deterministic per-frame random in [0, 1) (for the prototype's <c>Math.random()</c> flickers).</summary>
        public static double Noise(double t, uint salt = 0)
        {
            unchecked
            {
                uint h = (uint)(long)Math.Floor(t * FlashSafety.FrameRate) * 2654435761u ^ salt * 2246822519u;
                h ^= h >> 15; h *= 2246822519u; h ^= h >> 13; h *= 3266489917u; h ^= h >> 16;
                return h / 4294967296.0;
            }
        }

        private static bool Within(double t, double[] starts, double length, double shift = 0)
        {
            for (int i = 0; i < starts.Length; i++) if (t >= starts[i] + shift && t < starts[i] + shift + length) return true;
            return false;
        }

        private static double RelayLight(PulseSequencer relay, double t, bool calm)
        {
            double sum = 0;
            for (int i = 0; i < relay.LampCount; i++) sum += relay.ValueAtUnits(i, t * Fps, calm);
            return 5.0 * Math.Min(1.4, sum);                                                                     // L1567
        }

        /// <summary>The DL-08 tunnel arcs are live 0.3–0.75 s and 1.5–1.95 s of every 2.4 s (ARCS8, ARC_PERIOD, L7321–L7325).</summary>
        public static bool ArcLive(double t)
        {
            double ta = t % 2.4;
            return (ta >= 0.3 && ta < 0.75) || (ta >= 1.5 && ta < 1.95);
        }

        /// <summary>
        /// The combined flashing area <paramref name="e"/> is judged by (WCAG 2.3.1 sums the area of everything flashing
        /// together): the screen share of every effect over the limit (<paramref name="overLimit"/>) that can be on screen
        /// with it. Conservatively, everything over the limit in one scene counts as flashing together and in phase,
        /// whenever in the scene it plays, and an <see cref="Everywhere"/> effect counts with every scene; an
        /// <see cref="Everywhere"/> effect takes its worst scene. <paramref name="e"/> itself counts when it is over the limit.
        /// </summary>
        public static double CombinedArea(FlashEffect e, FlashEffect[] all, Func<FlashEffect, bool> overLimit)
        {
            if (e == null) throw new ArgumentNullException(nameof(e));
            if (all == null) throw new ArgumentNullException(nameof(all));
            if (overLimit == null) throw new ArgumentNullException(nameof(overLimit));
            bool selfCounted = false;
            for (int i = 0; i < all.Length; i++) if (ReferenceEquals(all[i], e)) selfCounted = true;
            double self = !selfCounted && overLimit(e) ? e.ScreenFraction : 0;
            if (e.Scene != Everywhere) return self + SceneArea(e.Scene, all, overLimit);
            double worst = SceneArea(Everywhere, all, overLimit);
            for (int i = 0; i < all.Length; i++)
                if (all[i].Scene != Everywhere) worst = Math.Max(worst, SceneArea(all[i].Scene, all, overLimit));
            return self + worst;
        }

        private static double SceneArea(string scene, FlashEffect[] all, Func<FlashEffect, bool> overLimit)
        {
            double sum = 0;
            for (int i = 0; i < all.Length; i++)
                if ((all[i].Scene == scene || all[i].Scene == Everywhere) && overLimit(all[i])) sum += all[i].ScreenFraction;
            return sum;
        }

        /// <summary>
        /// Every effect of <paramref name="all"/> measured at <paramref name="sampleRate"/> against WCAG 2.3.1: the
        /// general flash rule and, for a saturated-red source, the red flash rule, each against the
        /// <see cref="CombinedArea"/>.
        /// </summary>
        public static FlashAssessment[] Assess(FlashEffect[] all, bool calm, double sampleRate = FlashSafety.FrameRate)
        {
            if (all == null) throw new ArgumentNullException(nameof(all));
            var general = new FlashCount[all.Length];
            var red = new FlashCount[all.Length];
            var over = new System.Collections.Generic.Dictionary<FlashEffect, bool>();
            for (int i = 0; i < all.Length; i++)
            {
                general[i] = all[i].Measure(calm, sampleRate);
                red[i] = all[i].Red ? all[i].Measure(calm, sampleRate, red: true) : general[i];
                over[all[i]] = !general[i].WithinLimit || !red[i].WithinLimit;
            }
            var result = new FlashAssessment[all.Length];
            for (int i = 0; i < all.Length; i++)
            {
                double area = CombinedArea(all[i], all, f => over.TryGetValue(f, out bool o) && o);
                bool passes = FlashSafety.Passes(general[i], area) && FlashSafety.Passes(red[i], area);
                result[i] = new FlashAssessment(all[i], general[i], red[i], area, passes);
            }
            return result;
        }

        /// <summary>Every effect, in play order.</summary>
        public static FlashEffect[] All()
        {
            var relay = new PulseSequencer("flash.relay", PulseParams.Dl01Relay());
            var att = new PulseSequencer("flash.att", PulseParams.AttRelays());
            var press = PeriodicCrusherParams.Dl02Press();
            return new[]
            {
                // ---- DL-01 -------------------------------------------------------------------------------------------
                new FlashEffect("dl01.openingParcelLamp", "L1552–L1553", FlashKind.Emissive, 0.01, 0, 3,
                    (t, calm) => t * Fps < 40 ? 6 * OpeningFlicker(t * Fps, 18, ParcelPattern, 1, calm) : 6, ported: false),
                new FlashEffect("dl01.openingWorkBulb", "L1569–L1572", FlashKind.Light, 0.6, 8, 4,
                    (t, calm) => 24 * OpeningFlicker(t * Fps, 226, BulbPattern, 1, calm), ported: false),
                new FlashEffect("dl01.openingEyes", "L1575–L1577", FlashKind.Emissive, 0.005, 8, 4,
                    (t, calm) => 7 * OpeningFlicker(t * Fps, 225, EyesPattern, 1, calm), ported: false),
                new FlashEffect("dl01.openingSparks", "L333, L1565–L1567", FlashKind.Light, 0.15, 5, 5,
                    (t, calm) => !calm && Within(t * Fps, OpeningSparks, 2) ? 5 : 0, ported: false),
                new FlashEffect("dl01.relay", "L332, L1534–L1548, L1567", FlashKind.Light, 0.3, 0, 30,
                    (t, calm) => RelayLight(relay, t, calm), ported: true),
                new FlashEffect("dl01.cable", "L7938–L7941", FlashKind.Light, 0.15, 0, 9, CablePhase,
                    (t, p, calm) => PrologueLighting.CableLevel(Within(t, CableSparks, ChapterSounds.SparkFor, p), t, calm), ported: true),
                new FlashEffect("dl01.cordLamp", "L7948–L7950", FlashKind.Light, 0.15, 0, 2,
                    (t, calm) => 3.2 * (calm ? 1 : Math.Min(1, t * 6) * (t < 0.4 ? (Math.Sin(t * 70) > 0 ? 1 : 0.2) : 1)), ported: false),
                new FlashEffect("dl01.crank", "L7962", FlashKind.Light, 0.2, 0, 10,
                    (t, calm) => PrologueLighting.CrankLevel(t, 0), ported: true),
                // ---- DL-02 to DL-06 ---------------------------------------------------------------------------------
                new FlashEffect("dl02.pressLamp", "L7347", FlashKind.Emissive, 0.005, 0, 8,
                    (t, calm) => PeriodicCrusher.LampAt(press, t % press.Period, calm), ported: true, colour: PressLampColour),
                new FlashEffect("dl04.rowLamps", "L2414–L2422", FlashKind.Emissive, 0.15, 0, 9,
                    (t, calm) => 2.4 * RackRows.Row(0, t, calm), ported: true),
                new FlashEffect("dl04.rackLights", "L2414–L2426", FlashKind.Light, 0.4, 0, 9,
                    (t, calm) => 0.1 + 3.6 * RackRows.Lit(true, t, calm), ported: true),
                new FlashEffect("dl04.cradleLamps", "L4818–L4820", FlashKind.Emissive, 0.005, 0, 4,
                    (t, calm) => Cradle.SeatedLamp(t, calm), ported: true, calmDeviation: true),
                new FlashEffect("dl05.rationStrip", "L4927–L4929", FlashKind.Light, 0.4, 0, 20,
                    (t, calm) => 14 * PrologueLighting.RationFlicker(t, calm), ported: true),
                new FlashEffect("dl05.candles", "L4930", FlashKind.Light, 0.04, 0, 20,
                    (t, calm) => PrologueLighting.CandlesLevel(t), ported: true),
                new FlashEffect("dl06.scanner", "L2429–L2432", FlashKind.Light, 0.08, 0, 10,
                    (t, calm) => PrologueLighting.ScannerIdle(t), ported: true),
                new FlashEffect("dl06.pitSky", "L2846–L2847", FlashKind.Light, 0.5, 0, 30,
                    (t, calm) => 120 * (0.85 + 0.15 * Math.Sin(t * 0.3)), ported: false),
                new FlashEffect("pips.reject", "L6873–L6883", FlashKind.Emissive, 0.005, 0, 3,
                    (t, calm) => t < 1.4 && Math.Sin(t * 18) > 0 ? 3 : 0.15, ported: false, colour: PipsRed, scene: Everywhere),
                // ---- DL-08 to DL-11 ---------------------------------------------------------------------------------
                new FlashEffect("dl08.beacon", "L3230–L3235", FlashKind.Emissive, 0.01, 0, 6,
                    (t, calm) => 7 * (calm ? 0.7 : 0.5 + 0.5 * Math.Sin(t * 7)), ported: false),
                new FlashEffect("dl08.arcLight", "L7386–L7415", FlashKind.Light, 0.1, 0, 5,
                    (t, calm) => !ArcLive(t) ? 0 : calm ? 0.6 * 0.8 : 2.5 * (0.6 + 0.4 * Noise(t, 8)), ported: false, calmDeviation: true),
                new FlashEffect("dl09.cageBulb", "L5077", FlashKind.Emissive, 0.01, 0, 3,
                    (t, calm) => calm ? 3 : Math.Sin(t * 37) > 0.1 ? 4 : 0.4, ported: false),
                new FlashEffect("dl09.trayLamp", "L5073", FlashKind.Emissive, 0.005, 0, 6,
                    (t, calm) => 6 + 6 * Math.Max(0, Math.Sin(t * 5)), ported: false),
                new FlashEffect("dl10.upLamps", "L4660–L4662", FlashKind.Emissive, 0.005, 0, 2, 2 * Math.PI / 40,
                    (t, p, calm) => t < 0.9 ? (calm ? 4 : Math.Sin((t + p) * 40) > 0 ? 4 : 0.2) : 0.4, ported: false, calmDeviation: true),
                new FlashEffect("dl10.lobbyBulb", "L4663–L4665", FlashKind.Light, 0.3, 0, 20,
                    (t, calm) => 1.4 * (calm ? 1 : Math.Sin(t * 0.9) > 0.9 ? 0.2 + 0.8 * (Math.Sin(t * 53) > 0 ? 1 : 0) : 0.9 + 0.1 * Math.Sin(t * 11)), ported: false),
                new FlashEffect("dl10.ringcLight", "L4610, L4618–L4621", FlashKind.Light, 0.4, 0, 25,
                    (t, calm) => 2.6 * Smooth.Step((t - 9.5) / 2.5) * (1 - Smooth.Step((t - 20) / 1.5)), ported: false),
                new FlashEffect("dl11.laneBulb", "L3489, L3562–L3568", FlashKind.Light, 0.15, 0, 20,
                    (t, calm) => calm ? 1 : (Math.Sin(t * 0.7) > 0.93 && Math.Sin(t * 31) > -0.2 ? 0.15 : 1) * (0.78 + 0.14 * Math.Sin(t * 1.3) + 0.08 * Math.Sin(t * 47)), ported: false),
                new FlashEffect("dl11.bellLamp", "L7255–L7258", FlashKind.Emissive, 0.005, 0, 4,
                    (t, calm) => Math.Sin(t * 18) > 0 ? 6 : 0.5, ported: false),
                // ---- Chapter 1 (DL-12 to DL-17) -----------------------------------------------------------------------
                new FlashEffect("dl12.gateLamps", "L5395–L5398", FlashKind.Emissive, 0.005, 0, 4,
                    (t, calm) => 5.5 * (calm ? 1 : Math.Sin(t * 7) > 0 ? 1 : 0.15), ported: false),
                new FlashEffect("dl12.pegReach", "L5397–L5398", FlashKind.Emissive, 0.005, 0, 3, 2 * Math.PI / 14,
                    (t, p, calm) => t < 2.4 ? (Math.Sin((t + p) * 14) > 0 ? 7 : 1) : 0.8, ported: false),
                new FlashEffect("dl14.clutchLight", "L5221, L5462–L5466", FlashKind.Light, 0.05, 0, 4,
                    (t, calm) => 1.2 * (calm ? 0.6 : 0.6 + 0.4 * Math.Sin(t * 31)), ported: false, calmDeviation: true, followRate: 10),
                new FlashEffect("dl14.clutchSparks", "L5459", FlashKind.Particles, 0.01, 0, 0, null, ported: false, calmDeviation: true),
                new FlashEffect("dl14a.eyes", "L6280–L6281", FlashKind.Emissive, 0.005, 0, 4,
                    (t, calm) => 4.5 * (calm ? 1 : Math.Sin(t * 7) > 0 ? 1 : 0.2), ported: false),
                new FlashEffect("dl16a.loadFlash", "L6299–L6300", FlashKind.Emissive, 0.005, 0, 3, 2 * Math.PI / 14,
                    (t, p, calm) => t < 2.4 ? (Math.Sin((t + p) * 14) > 0 ? 6 : 0.4) : 0.05, ported: false),
                new FlashEffect("att.relays", "L5160–L5166, L6316–L6325", FlashKind.Emissive, 0.005, 0, 21,
                    (t, calm) => Math.Max(att.ValueAtUnits(3, t, calm), Math.Sin(t * 6) > 0 ? 1 : 0), ported: true, scene: Everywhere),   // the service line runs through chapter 1
                // ---- Chapter 2 (DL-18, DL-19): no prototype, so "L—" and the doc sections --------------------------
                new FlashEffect("ch2.relayPilots", "L— (no prototype): chapter2_plan §4 \"The new cable\", DL-18 §3", FlashKind.Light, 0.02, 0, 21,
                    (t, calm) => SomeoneHomeLights.PilotLevel(t, calm), ported: true, colour: Rgb.Hex(0x7dff9a)),
                // ---- Everywhere -------------------------------------------------------------------------------------
                new FlashEffect("glints.pulse", "L7009", FlashKind.Emissive, 0.005, 0, 6,
                    (t, calm) => calm ? 1 : 0.85 + 0.15 * Math.Sin(t * 2.6), ported: false, scene: Everywhere),
                new FlashEffect("death.eye", "L7445–L7447", FlashKind.Emissive, 0.002, 0, 1,
                    (t, calm) => DeathProfile.EyeLevel(t, calm), ported: true, calmDeviation: true, scene: Everywhere),
                new FlashEffect("death.sparks", "L7440, L7448", FlashKind.Particles, 0.01, 0, 0, null, ported: false, scene: Everywhere),
                new FlashEffect("death.cut", "L7449–L7452, L8100, CSS L107", FlashKind.Screen, 1.0, 0, 4,
                    (t, calm) => t < 1.0 ? 1 : t < 1.6 ? 0 : Math.Min(1, (t - 1.6) / 1.2), ported: false, scene: Everywhere),
                new FlashEffect("camera.shake", "L3810, L3826–L3831", FlashKind.Motion, 0, 0, 0, null, ported: true, scene: Everywhere),
            };
        }
    }
}
