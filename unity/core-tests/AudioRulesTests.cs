using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using DeadLetter.Core.Audio;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// The SFX catalog against the renders in <c>art/sfx/out/</c> (manifest.json), the pan law, stable GUIDs, the
    /// continuous layers, the emitters (<c>Ambience</c>, L1145–L1211) and the voices (<c>Voice</c>, L966–L1143;
    /// <c>updateTannoys</c>, L6679–L6692).
    /// </summary>
    public class AudioRulesTests
    {
        private static List<(string File, string Kind)> _manifest;

        private static List<(string File, string Kind)> Manifest
        {
            get
            {
                if (_manifest != null) return _manifest;
                using var doc = JsonDocument.Parse(File.ReadAllText(RepoFiles.Find("art/sfx/out/manifest.json")));
                _manifest = doc.RootElement.GetProperty("files").EnumerateArray()
                    .Select(f => (f.GetProperty("file").GetString(), f.GetProperty("kind").GetString())).ToList();
                return _manifest;
            }
        }

        private static IEnumerable<string> ImportedFiles => Manifest.Where(f => f.Kind != "ir").Select(f => f.File);

        private static SfxCatalog Bank => SfxCatalog.FromFiles(ImportedFiles);

        // ---- SFX naming and catalog -------------------------------------------------------------------------------------

        [Theory]
        [InlineData("d17_step_v3.wav", "d17_step", 3, false)]
        [InlineData("mech_spark_v1_wet.wav", "mech_spark", 1, true)]
        [InlineData("mech_lift_crash_v040.wav", "mech_lift_crash_v040", 1, false)]   // v = 0.40, not a take
        [InlineData("mech_lift_crash_v040_wet", "mech_lift_crash_v040", 1, true)]
        [InlineData("loop_air_wet.wav", "loop_air", 1, true)]
        [InlineData("some/dir/mech_tick.wav", "mech_tick", 1, false)]
        [InlineData("mech_row_on_5.wav", "mech_row_on_5", 1, false)]
        public void Naming_SplitsKeyTakeAndWet(string file, string key, int take, bool wet)
        {
            Assert.True(SfxNaming.TryParse(file, out string k, out int t, out bool w));
            Assert.Equal((key, take, wet), (k, t, w));
        }

        [Fact]
        public void Catalog_CoversEveryCallTheGameMakes()
        {
            SfxCatalog bank = Bank;
            foreach (string key in SfxKeys.AllKeys()) Assert.True(bank.Find(key) != null, key + " has no render");
            foreach (EmitterKind k in Enum.GetValues(typeof(EmitterKind))) Assert.NotNull(bank.Find(EmitterRules.BankKey(k)));
            foreach (string k in SfxLoopMixer.Keys) Assert.NotNull(bank.Find(k));
            foreach (TreatmentDef t in VoiceCatalog.Treatments) Assert.NotNull(bank.Find(t.CrackleKey));
            Assert.NotNull(bank.Find("voice_tannoy_chime"));
        }

        [Fact]
        public void Catalog_GroupsTakes_PrefersWet_AndFlagsLoopsAsTheManifestDoes()
        {
            SfxCatalog bank = Bank;
            Assert.Equal(new[] { "d17_step_v1", "d17_step_v2", "d17_step_v3", "d17_step_v4" }, bank.Find("d17_step").Files);
            Assert.Equal(new[] { "mech_spark_v1_wet", "mech_spark_v2", "mech_spark_v3" }, bank.Find("mech_spark").Files);
            Assert.Equal(new[] { "mech_clank_wet" }, bank.Find("mech_clank").Files);
            Assert.Equal(new[] { "mech_clank" }, SfxCatalog.FromFiles(ImportedFiles, WetPolicy.Dry).Find("mech_clank").Files);
            Assert.Equal(new[] { "loop_air_wet" }, bank.Find("loop_air").Files);
            // Every imported file is reachable from exactly one key; no take of the same key is listed twice.
            int playable = bank.Entries.Sum(e => e.Takes);
            int dryOrOnly = ImportedFiles.Count(f => !f.EndsWith("_wet.wav") || !ImportedFiles.Contains(f.Replace("_wet.wav", ".wav")));
            Assert.Equal(dryOrOnly, playable);
            foreach ((string file, string kind) in Manifest.Where(f => f.Kind != "ir"))
            {
                SfxNaming.TryParse(file, out string key, out _, out _);
                Assert.True((kind == "loop") == SfxNaming.IsLoop(key), file);
            }
            Assert.DoesNotContain(bank.Entries, e => e.Key.StartsWith("ir"));
        }

        [Fact]
        public void Picker_NeverRepeatsATakeBackToBack_UsesThemAll_AndIsSeeded()
        {
            var a = new SfxPicker(42);
            var b = new SfxPicker(42);
            var seen = new int[4];
            int last = -1;
            for (int i = 0; i < 2000; i++)
            {
                int t = a.Next("d17_step", 4);
                Assert.Equal(t, b.Next("d17_step", 4));
                Assert.NotEqual(last, t);
                seen[t]++;
                last = t;
            }
            Assert.All(seen, n => Assert.InRange(n, 400, 600));
            Assert.Equal(0, a.Next("mech_clank", 1));
        }

        [Fact]
        public void Picker_RoundRobin_CyclesTheTakes()
        {
            var p = new SfxPicker(1, SfxPickMode.RoundRobin);
            Assert.Equal(new[] { 0, 1, 2, 0, 1, 2, 0 }, Enumerable.Range(0, 7).Select(_ => p.Next("env_drip", 3)).ToArray());
        }

        [Fact]
        public void Keys_ParameterisedCalls()
        {
            Assert.Equal("mech_creak_500", SfxKeys.Creak());
            Assert.Equal("mech_creak_300", SfxKeys.Creak(0.3));
            Assert.Equal("mech_chain_550", SfxKeys.Chain(0.55));
            Assert.Equal("mech_chain_1200", SfxKeys.Chain(1.2));
            Assert.Equal("mech_rattle_900", SfxKeys.Rattle(0.9));
            Assert.Equal("mech_servo_350_900_1500", SfxKeys.Servo(0.35, 900, 1500));   // the letter close-up
            Assert.Null(SfxKeys.Servo(0.5, 100, 200));
            Assert.Equal(("mech_lift_crash_v040", 1.0), (SfxKeys.LiftCrash(0.4), SfxKeys.LiftCrashVolume(0.4)));
            Assert.Equal(("mech_lift_crash", 0.7), (SfxKeys.LiftCrash(0.7), SfxKeys.LiftCrashVolume(0.7)));
            Assert.Equal("curio_mug_down", SfxKeys.Curio("mugDown"));
            Assert.Equal("death_grabbed", SfxKeys.Death("grabbed"));
            Assert.Equal("d17_setdown_deck", SfxKeys.SetDown(true));
            Assert.Throws<ArgumentOutOfRangeException>(() => SfxKeys.RowOn(6));
        }

        // ---- Pan, GUIDs, envelopes --------------------------------------------------------------------------------------

        [Theory]
        [InlineData(0.0, -0.4)]
        [InlineData(1.0, 0.4)]
        [InlineData(0.5, 0.0)]
        [InlineData(0.75, 0.2)]
        [InlineData(-0.5, -0.4)]   // off-screen left: held at the edge
        [InlineData(3.0, 0.4)]
        [InlineData(double.NaN, 0.0)]
        public void PanLaw_GentleAtTheFrameEdges(double viewportX, double pan)
        {
            Assert.Equal(pan, PanLaw.FromViewportX(viewportX), 12);
        }

        [Fact]
        public void PanLaw_EdgeIsOneTunable()
        {
            Assert.Equal(-0.25, PanLaw.FromViewportX(0, 0.25), 12);
            Assert.Equal(0.0, PanLaw.FromViewportX(1, 0), 12);
            Assert.Equal(1.0, PanLaw.FromViewportX(1, 2), 12);
        }

        [Fact]
        public void StableGuid_IsTheMd5OfThePath()
        {
            Assert.Equal("c7705b6e3a227085094fc431e5e9e454", StableGuid.ForPath("Assets/Audio/Sfx/mech_tick.wav"));
            Assert.Equal(StableGuid.ForPath("Assets/Audio/Sfx/mech_tick.wav"), StableGuid.ForPath("Assets\\Audio\\Sfx\\mech_tick.wav"));
            Assert.NotEqual(StableGuid.ForPath("Assets/Audio/Sfx/a.wav"), StableGuid.ForPath("Assets/Audio/Sfx/b.wav"));
            string meta = StableGuid.FileMeta("Assets/Audio/Music/prologue_cue_wake.mp3");
            Assert.StartsWith("fileFormatVersion: 2\nguid: ", meta);
            Assert.Equal(StableGuid.ForPath("Assets/Audio/Music/prologue_cue_wake.mp3"), StableGuid.ReadGuid(meta));
            Assert.Contains("folderAsset: yes", StableGuid.FolderMeta("Assets/Audio/Sfx"));
            Assert.Null(StableGuid.ReadGuid("fileFormatVersion: 2\n"));
        }

        [Fact]
        public void GainEnvelope_LinearTargetAndHoldFromTheCurrentValue()
        {
            var g = new GainEnvelope();
            g.Ramp(10, 0, 1, 2);
            Assert.Equal(0.5, g.ValueAt(11), 12);
            g.TargetAt(11, 0, 0.5);                       // a fade-out halfway through the ramp starts from 0.5, not 0
            Assert.Equal(0.5, g.ValueAt(11), 12);
            Assert.Equal(0.5 * Math.Exp(-1), g.ValueAt(11.5), 12);
            g.Set(20, 0.3);
            Assert.Equal(0.3, g.ValueAt(25));
            Assert.Equal(0.0, g.Destination - 0.3, 12);
        }

        // ---- Continuous layers and the atmosphere -----------------------------------------------------------------------

        [Fact]
        public void LoopMixer_GlidesWithEachLayersTau()
        {
            var m = new SfxLoopMixer();
            m.Set(SfxLoop.Hum, 1);
            m.Set(SfxLoop.Buzz, 1);
            for (int i = 0; i < 24; i++) m.Step(i / 60.0, 1 / 60.0);    // 0.4 s
            Assert.Equal(1 - Math.Exp(-1), m.Volume(SfxLoop.Hum), 9);    // hum τ 0.4
            Assert.True(m.Volume(SfxLoop.Buzz) > 0.999);                  // buzz τ 0.01
        }

        [Fact]
        public void WhiteHiss_IsHeardEvenWhileTheSteamHissIsSetToZeroEveryFrame()
        {
            // §9 #16: in the web build hiss(1) for the White is overwritten by the steam's hiss(0) on the next frame.
            var m = new SfxLoopMixer();
            double t = 100, peak = 0;
            m.WhiteWarning(t);
            for (int i = 0; i < 120; i++)
            {
                m.Set(SfxLoop.Hiss, AtmosphereRules.SteamHiss(60, true));   // far from DL-01's steam: 0
                m.Step(t, 1 / 60.0);
                peak = Math.Max(peak, m.Volume(SfxLoop.WhiteHiss));
                if (i == 50) Assert.Equal(1, m.Target(SfxLoop.WhiteHiss));
                t += 1 / 60.0;
            }
            Assert.True(peak > 0.98, "peak " + peak);
            Assert.Equal(0, m.Volume(SfxLoop.Hiss));
            Assert.Equal(0, m.Target(SfxLoop.WhiteHiss));   // off after 0.9 s
            Assert.True(m.Volume(SfxLoop.WhiteHiss) < 0.1);
        }

        [Fact]
        public void SteamHiss_FollowsThePrototypeFormula()
        {
            Assert.Equal(1.0, AtmosphereRules.SteamHiss(8.7, true), 12);
            Assert.Equal(0.6 * 0.35, AtmosphereRules.SteamHiss(9.7, true, AtmosphereRules.HissLevel(false)), 12);
            Assert.Equal(0.0, AtmosphereRules.SteamHiss(11.3, true), 12);
            Assert.Equal(0.0, AtmosphereRules.SteamHiss(8.7, false), 12);
        }

        [Fact]
        public void DistantMachinery_EverySixToFourteenSeconds_HeldUnderAMoment()
        {
            var a = new AtmosphereRules(7);
            Assert.Equal(DistantSound.None, a.Update(8.0, true, false));     // strictly after 8 s
            double last = 0;
            int distant = 0, groan = 0;
            for (double t = 8.01; t < 5000; t += 0.01)
            {
                DistantSound s = a.Update(t, true, false);
                if (s == DistantSound.None) continue;
                if (last > 0) Assert.InRange(t - last, 6, 14.02);
                last = t;
                if (s == DistantSound.Distant) distant++; else groan++;
            }
            Assert.InRange(distant / (double)(distant + groan), 0.5, 0.7);
            var held = new AtmosphereRules(7);
            Assert.Equal(DistantSound.None, held.Update(9, true, true));
            Assert.Equal(DistantSound.None, held.Update(9, false, false));
            Assert.NotEqual(DistantSound.None, held.Update(9.02, true, false));   // fires as soon as it may
        }

        // ---- Emitters --------------------------------------------------------------------------------------------------

        [Fact]
        public void Emitters_TheTableAsPlaced()
        {
            Assert.Equal(19, PrologueEmitters.All.Length);
            Assert.Equal(61.9, PrologueEmitters.ScannerX, 9);
            Assert.Equal(87.05, PrologueEmitters.ShaftMid, 9);
            EmitterDef clock = PrologueEmitters.All.Single(e => e.Region == 6 && e.Kind == EmitterKind.Tick);
            Assert.Equal((224.0, 0.25, 0.5, 7.0, PrologueEmitters.LessonRunning), (clock.X, clock.Period, clock.Level, clock.Reach, clock.Condition));
            Assert.Equal(2, PrologueEmitters.All.Count(e => e.Deck == EmitterDeck.Lower));
        }

        [Fact]
        public void Emitter_GainIsLevelTimesKSquared_GlidedWithTau025()
        {
            var e = new EmitterDef(2, 23.4, EmitterKind.Buzz, 0.5, 4);
            var s = new EmitterState(1);
            EmitterStep step = default;
            for (int i = 0; i < 600; i++) step = s.Update(e, 25.4, 2, false, true, i / 60.0, 1 / 60.0);
            Assert.Equal(0.5, step.K, 12);
            Assert.Equal(0.125, step.Target, 12);
            Assert.Equal(0.25, step.Tau);
            Assert.Equal(0.125, s.Gain, 6);
            Assert.Equal(0.125, EmitterRules.Gain(0.5, 2, 4), 12);
            Assert.False(step.Blip);
        }

        [Fact]
        public void Emitter_SilentOutsideItsRegionDeckOrCondition()
        {
            var lower = new EmitterDef(3, 61.9, EmitterKind.Hum, 0.5, 3.5, EmitterDeck.Lower);
            Assert.Equal(0, new EmitterState(1).Update(lower, 61.9, 3, true, true, 0, 1 / 60.0).K);    // on the upper deck
            Assert.Equal(1, new EmitterState(1).Update(lower, 61.9, 3, false, true, 0, 1 / 60.0).K);
            Assert.Equal(0, new EmitterState(1).Update(lower, 61.9, 2, false, true, 0, 1 / 60.0).K);   // other region
            Assert.Equal(0, new EmitterState(1).Update(lower, 61.9, 3, false, false, 0, 1 / 60.0).K);  // when() false
        }

        [Fact]
        public void Emitter_OutOfReach_FadesThenIsFreedAfterThreeSeconds()
        {
            var e = new EmitterDef(1, 7.3, EmitterKind.Drip, 0.7, 4.5);
            var s = new EmitterState(3);
            s.Update(e, 7.3, 1, false, true, 10, 1 / 60.0);
            Assert.True(s.Live);
            EmitterStep out1 = s.Update(e, 20, 1, false, true, 11, 1 / 60.0);
            Assert.Equal((0.0, 0.4, false), (out1.Target, out1.Tau, out1.Freed));
            EmitterStep out2 = s.Update(e, 20, 1, false, true, 13.01, 1 / 60.0);
            Assert.Equal((0.3, true), (out2.Tau, out2.Freed));
            Assert.False(s.Live);
        }

        [Fact]
        public void Emitter_Blips_FirstAtOnce_ThenAtTheKindsInterval()
        {
            var tick = new EmitterDef(1, 1.0, EmitterKind.Tick, 0.45, 3, period: 0.9);
            var s = new EmitterState(5);
            var at = new List<double>();
            for (int i = 0; i <= 600; i++)
            {
                double t = 50 + i / 60.0;
                if (s.Update(tick, 1.5, 1, false, true, t, 1 / 60.0).Blip) at.Add(t);
            }
            Assert.Equal(50.0, at[0], 9);
            for (int i = 1; i < at.Count; i++) Assert.InRange(at[i] - at[i - 1], 0.9 - 1e-9, 0.9 + 1 / 60.0 + 1e-9);

            var drip = new EmitterDef(1, 7.3, EmitterKind.Drip, 0.7, 4.5);
            var rng = new AudioRng(9);
            for (int i = 0; i < 500; i++) Assert.InRange(EmitterRules.Interval(drip, rng), 0.7, 2.9);
            Assert.False(new EmitterDef(4, 107.17, EmitterKind.MusicBox, 0.5, 3.2).IsEvent);   // a loop in Unity
        }

        // ---- Voices ----------------------------------------------------------------------------------------------------

        [Fact]
        public void VoiceCatalog_LinesPlacementsAndTreatments()
        {
            Assert.Equal(27, VoiceCatalog.Lines.Length);
            Assert.All(VoiceCatalog.Placements, p => Assert.NotNull(VoiceCatalog.Find(p.Id)));
            Assert.Equal(11.0, VoiceCatalog.Find("tan_racks").Length, 9);
            Assert.Equal(25.2, VoiceCatalog.Find("card_den").Length, 9);
            Assert.Equal(3, VoiceCatalog.Find("card_den").Files.Length);
            Assert.Equal(VoiceTreatment.CardWorn, VoiceCatalog.Find("card_queue").Treat);
            Assert.Equal(0.24, VoiceCatalog.Treatment(VoiceTreatment.Card).RoomWet, 12);
            Assert.Equal(1.06 * Math.Pow(2, 4 / 12.0), VoiceCatalog.Treatment(VoiceTreatment.Child).PlaybackRate, 12);
            Assert.Equal("voice_crackle_card_worn", VoiceCatalog.Treatment(VoiceTreatment.CardWorn).CrackleKey);
        }

        [Fact]
        public void Voice_TannoyChimeLeadsAndTheSubtitlesAndEndFollowTheLines()
        {
            var v = new VoiceRules();
            VoiceDef def = VoiceCatalog.Find("tan_racks");   // 2.2, 1.4 ×4, 3.2 = 11 s
            VoicePlayback p = v.Play(def, 100, VoicePlayOptions.At(38.2, 9, 0.85));
            Assert.True(p.Chime);
            Assert.Equal(101.35, p.VoiceAt, 12);
            Assert.Equal(new[] { 101.35, 103.55, 104.95, 106.35, 107.75, 109.15 }, p.LineAt.Select(x => Math.Round(x, 9)).ToArray());
            Assert.Equal(101.35 + 11 + 0.6, p.EndAt, 9);
            Assert.Equal(-1, p.LineIndexAt(101.0));
            Assert.Equal(1, p.LineIndexAt(104.0));
            Assert.True(v.Ducking);
            Assert.False(v.Update(112.9, 38.2));
            Assert.True(v.Update(112.96, 38.2));    // ends by itself
            Assert.Null(v.Playing);
            Assert.False(v.Ducking);
            Assert.Equal(112.96 + 1.2 + 0.3, v.Fading.StopAt, 9);

            VoicePlayback card = new VoiceRules().Play(VoiceCatalog.Find("card_heap"), 0, VoicePlayOptions.At(68, 6));
            Assert.False(card.Chime);
            Assert.Equal(0.25, card.VoiceAt, 12);
        }

        [Fact]
        public void Voice_RecordingsStretchTheSubtitles()
        {
            VoiceDef den = VoiceCatalog.Find("card_den");
            double rate = VoiceCatalog.Treatment(VoiceTreatment.Child).PlaybackRate;
            var opts = VoicePlayOptions.Flat();
            opts.RecordedLengths = new[] { 10.0, 10.0, 10.0 };
            VoicePlayback p = new VoiceRules().Play(den, 0, opts);
            double dur = 3 * (10 / rate + 0.15);
            Assert.Equal(dur, p.Duration, 9);
            Assert.Equal(0.25 + dur + 0.6, p.EndAt, 9);
            Assert.Equal(0.25 + den.Lines[0].Seconds * dur / den.Length, p.LineAt[1], 9);
        }

        [Fact]
        public void Voice_PositionalFadesWithDistance_AndStopsOnceOutOfEarshot()
        {
            var v = new VoiceRules();
            VoicePlayback p = v.Play(VoiceCatalog.Find("tan_rations"), 0, VoicePlayOptions.At(56.6, 9, 0.85));
            v.Update(0.5, 56.6 + 4.5);
            Assert.Equal(0.425, p.Out.Destination, 12);
            v.Update(0.6, 70);               // out of reach, but under 1 s old: keeps playing
            Assert.Equal("tan_rations", v.Playing);
            v.Update(1.1, 70);
            Assert.Null(v.Playing);
            Assert.Equal(1.1 + 0.2 + 0.3, p.StopAt, 9);
        }

        [Fact]
        public void Voice_OneAtATime_ANewOneReplacesTheOld()
        {
            var v = new VoiceRules();
            VoicePlayback a = v.Play(VoiceCatalog.Find("card_sorter"), 0, VoicePlayOptions.At(16.6, 6));
            VoicePlayback b = v.Play(VoiceCatalog.Find("tan_scanner"), 5, VoicePlayOptions.At(61.9, 6, 0.8));
            Assert.Equal("tan_scanner", v.Playing);
            Assert.Same(a, v.Fading);
            Assert.Equal(5 + 0.3 + 0.3, a.StopAt, 9);
            Assert.Equal(-1, a.LineIndexAt(5.1));   // its subtitles clear at once
            Assert.Equal(0.8, b.Level);

            var stuck = VoicePlayOptions.At(224, 10, 0.7);
            stuck.StickAt = 9.2;
            VoicePlayback lesson = v.Play(VoiceCatalog.Find("att_lesson"), 10, stuck);
            Assert.Equal(double.PositiveInfinity, lesson.EndAt);
            Assert.Equal(10.25, lesson.VoiceAt, 12);
        }

        [Fact]
        public void Tannoy_PlaysOnceAsHePasses_AgainOnlyAfterLeavingEarshotAnd150Seconds()
        {
            VoicePlacement tan = VoiceCatalog.FindPlacement("tan_rations");   // x 56.6, trigger 2.6, reach 9
            var s = new TannoyState();
            Assert.False(TannoyRules.Update(tan, s, 2, false, true, 50, 0, false, false, out _));      // not near
            Assert.False(TannoyRules.Update(tan, s, 2, false, true, 55, 1, true, false, out _));       // a voice plays
            Assert.False(TannoyRules.Update(tan, s, 2, false, true, 55, 1, false, true, out _));       // a moment holds
            Assert.True(TannoyRules.Update(tan, s, 2, false, true, 55, 2, false, false, out double first));
            Assert.Equal(0.85, first);
            Assert.False(TannoyRules.Update(tan, s, 2, false, true, 56, 3, false, false, out _));      // once
            TannoyRules.Update(tan, s, 2, false, true, 70, 10, false, false, out _);                   // beyond reach: away
            Assert.False(TannoyRules.Update(tan, s, 2, false, true, 56, 100, false, false, out _));    // too soon
            Assert.True(TannoyRules.Update(tan, s, 2, false, true, 56, 152.5, false, false, out double again));
            Assert.Equal(0.5, again);
            Assert.False(TannoyRules.Update(tan, s, 2, false, true, 56, 400, false, false, out _));    // not away since
        }

        [Fact]
        public void Tannoy_UsesItsTriggerPointAndCondition()
        {
            VoicePlacement depot = VoiceCatalog.FindPlacement("tan_depot_1");   // x 1.69, at 8.6, trigger 0.6, reach 14
            Assert.Equal(8.6, depot.TriggerX);
            Assert.False(TannoyRules.Update(depot, new TannoyState(), 1, false, false, 8.6, 0, false, false, out _));   // not released
            Assert.False(TannoyRules.Update(depot, new TannoyState(), 1, false, true, 1.69, 0, false, false, out _));
            Assert.True(TannoyRules.Update(depot, new TannoyState(), 1, false, true, 8.3, 0, false, false, out _));
            Assert.Equal(2.5, new VoicePlacement("x", VoicePlacementKind.Tannoy, 1, 0).TriggerDistance);   // `trigger || 2.5`
            Assert.Equal(9.0, VoiceCatalog.FindPlacement("tan_racks").EffectiveReach);
            Assert.Equal(6.0, VoiceCatalog.FindPlacement("card_heap").EffectiveReach);
        }

        [Fact]
        public void VoiceCard_InReachWithin022OfItsStandPoint()
        {
            VoicePlacement sorter = VoiceCatalog.FindPlacement("card_sorter");
            Assert.True(VoiceCardAct.Here(sorter, 2, false, 16.6, null));
            Assert.False(VoiceCardAct.Here(sorter, 2, false, 16.7, null));
            Assert.False(VoiceCardAct.Here(sorter, 2, false, 16.45, "card_sorter"));   // already playing
            Assert.False(VoiceCardAct.Here(VoiceCatalog.FindPlacement("card_heap"), 3, true, 68.0, null));   // upper deck
            Assert.Equal((1.2, 0.9), (VoiceCardAct.VoiceAt(false), VoiceCardAct.VoiceAt(true)));
        }
    }
}
