using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Cues;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>Finds files in the repository from the test's bin directory.</summary>
    internal static class RepoFiles
    {
        public static string Find(string relativeToRepo)
        {
            for (var dir = new DirectoryInfo(AppContext.BaseDirectory); dir != null; dir = dir.Parent)
            {
                var p = Path.Combine(dir.FullName, relativeToRepo);
                if (File.Exists(p) || Directory.Exists(p)) return p;
            }
            throw new FileNotFoundException(relativeToRepo + " not found above " + AppContext.BaseDirectory);
        }
    }

    /// <summary>MusicDirectorModel against index.html's <c>Music</c> (L780–L943) and port_architecture §4.24.</summary>
    public class MusicDirectorTests
    {
        private const double Eps = 1e-9;

        [Fact]
        public void EndMoment_LeavesTheCuePlayingButNoLongerInAMoment()
        {
            var m = new MusicDirectorModel();
            m.Moment("refuge", 2);
            Assert.True(m.InMoment);
            m.EndMoment();                                   // checkpoint reload, L8016
            Assert.False(m.InMoment);
            Assert.Equal("refuge", m.CurrentCue.Key);
            m.Moment("kin", 10);
            Assert.True(m.InMoment);
        }

        private static MusicLayer Cue(MusicDirectorModel m) => m.CurrentCue;
        private static MusicLayer Amb(MusicDirectorModel m) => m.CurrentAmbience;

        /// <summary>Steps the model at 60 Hz from <paramref name="from"/> to <paramref name="to"/>.</summary>
        private static void Run(MusicDirectorModel m, double from, double to, double horizon = 0)
        {
            for (double t = from; t <= to + Eps; t += 1.0 / 60) m.Update(t, t + horizon);
        }

        [Fact]
        public void Catalog_MatchesThePrototypeTables()
        {
            Assert.Equal(14, MusicCatalog.All.Count(t => !t.IsLoop));
            Assert.Equal(5, MusicCatalog.All.Count(t => t.IsLoop));
            var hand = new Dictionary<string, (double, bool)>
            {
                { "wake", (48, false) }, { "hall", (32, true) }, { "threshold", (24, true) }, { "racks", (36, true) },
                { "kin", (28, false) }, { "dead", (40, false) }, { "latch", (8, false) }, { "refuge", (24, false) },
                { "ringc", (24, false) }, { "childP", (36, false) }, { "window", (20, false) }, { "end", (60, false) },
            };
            foreach (MusicTrack t in MusicCatalog.All.Where(t => !t.IsLoop))
            {
                if (hand.TryGetValue(t.Key, out var h)) { Assert.Equal(h.Item1, t.HandoverAt); Assert.Equal(h.Item2, t.IntroBars); }
                else Assert.False(t.HasHandover, t.Key);
                Assert.Equal(t.Key == "child" || t.Key == "endAtt" ? 0.6 : 0.9, t.Level);
            }
            Assert.Equal(0.26, MusicCatalog.Find("bed").Level);
            Assert.Equal((2.0, 50.0), (MusicCatalog.Find("bed").LoopStart, MusicCatalog.Find("bed").LoopEnd));
            Assert.Equal(32.0, MusicCatalog.Find("heaps").ClipLength);
            Assert.Equal("prologue_loop_order_loop", MusicCatalog.Find("order").AssetName);
        }

        [Fact]
        public void Catalog_ReferencesEveryUsedFileAndNoneOfTheUnusedOnes()
        {
            string dir = RepoFiles.Find("game/undelivered/assets/music");
            var onDisk = Directory.GetFiles(dir, "*.mp3").Select(Path.GetFileNameWithoutExtension).ToHashSet();
            var used = MusicCatalog.All.Select(t => t.File).ToHashSet();
            Assert.Equal(19, used.Count);
            Assert.All(used, f => Assert.Contains(f, onDisk));
            Assert.All(MusicCatalog.Unreferenced, f => { Assert.Contains(f, onDisk); Assert.DoesNotContain(f, used); });
            Assert.Equal(onDisk.Count, used.Count + MusicCatalog.Unreferenced.Length);
        }

        [Fact]
        public void Play_FadesTheCueInLinearlyAndHidesTheAmbience()
        {
            var m = new MusicDirectorModel();
            m.Ambience("order", 0);
            Run(m, 0, 10);
            MusicLayer order = Amb(m);
            Assert.Equal(0.9, order.Gain.ValueAt(10), 6);

            m.Play("dead", 10, 0.15);   // DL-06's reject: fade 0.15 (L2801); dead has no intro bars → the loop out over 2 s
            Assert.Equal("dead", m.Playing);
            Assert.Null(m.AmbienceName);
            Assert.Equal(0.0001, Cue(m).Gain.ValueAt(10), 9);
            Assert.Equal(0.45, Cue(m).Gain.ValueAt(10.075), 3);
            Assert.Equal(0.9, Cue(m).Gain.ValueAt(10.15), 9);
            Assert.Equal(0.9 * Math.Exp(-1), order.Gain.ValueAt(10.5), 6);   // τ = 2 / 4
            Assert.Equal(10 + 2 + 0.3, order.StopAt, 9);
        }

        [Theory]
        [InlineData("hall", 4.0)]       // intro bars: the loop fades across them (4 s a bar)
        [InlineData("latch", 2.0)]      // a handover, no intro
        [InlineData("child", 1.5)]      // no handover
        public void ACueHidesTheAmbienceAtItsOwnRate(string cue, double outSeconds)
        {
            var m = new MusicDirectorModel();
            m.Ambience("lower_works", 0);
            Run(m, 0, 5);
            MusicLayer loop = Amb(m);
            m.Play(cue, 5);
            Assert.Equal(5 + outSeconds + MusicDirectorModel.AmbienceTail, loop.StopAt, 9);
            double v0 = loop.Gain.ValueAt(5);
            Assert.Equal(v0 * Math.Exp(-1), loop.Gain.ValueAt(5 + outSeconds / 4), 6);
        }

        [Fact]
        public void Wake_HandsOverToTheSceneLoopAt48Seconds()
        {
            // startPlay → card (L8062) asks for lower_works, then the opening plays the wake at fade 0.6 (L8068).
            var m = new MusicDirectorModel();
            m.Ambience("lower_works", 0);
            m.Play("wake", 0, 0.6);
            Assert.Null(m.AmbienceName);
            Run(m, 0, 47.9);
            Assert.Null(m.AmbienceName);
            Run(m, 47.9, 48.1);
            MusicLayer loop = Amb(m);
            Assert.Equal("lower_works", loop.Key);
            Assert.Equal(48.0, loop.StartAt, 9);                      // on the bar, not on the frame
            Assert.Equal(0.9, loop.Gain.ValueAt(48 + 1.5), 9);        // fade-in 1.5 s
            Assert.Equal("wake", m.Playing);                           // its tail rings on
            Run(m, 48.1, 54.1);
            Assert.Null(m.Playing);
            Assert.Equal("lower_works", m.AmbienceName);
            Assert.Equal(new[] { "-|lower_works", "wake|-", "wake|lower_works", "-|lower_works" }, m.Log.Select(l => l.Value).ToArray());
            Assert.Equal(48.0, m.Log[2].Key, 3);
            Assert.Equal(54.0, m.Log[3].Key, 3);
        }

        [Fact]
        public void Queue_StartsAtTheHandoverWithNoAmbienceBetween()
        {
            var m = new MusicDirectorModel();
            m.Ambience("order", 0);
            m.Play("latch", 0, 0.15);
            m.Queue("childP", 1);
            Run(m, 0, 8.5);
            Assert.Equal("childP", m.Playing);
            Assert.Equal(8.0, Cue(m).StartAt, 9);
            Assert.Null(m.AmbienceName);
            MusicLayer latch = m.Layers.Single(l => l.Key == "latch");
            Assert.Equal(8 + 1.5 + 0.2, latch.StopAt, 9);   // the old cue out over 1.5 s
        }

        [Fact]
        public void Queue_OnACueWithoutHandover_FollowsItsEnd_AndWithNothingPlaying_StartsNow()
        {
            var m = new MusicDirectorModel();
            m.SetLength("child", 10);
            m.Play("child", 0, 2.5);
            m.Queue("endAtt", 3);
            Run(m, 0, 9.9);
            Assert.Equal("child", m.Playing);
            Run(m, 9.9, 10.1);
            Assert.Equal("endAtt", m.Playing);
            Assert.Equal(10.0, Cue(m).StartAt, 9);

            var idle = new MusicDirectorModel();
            idle.Queue("end", 4);
            Assert.Equal("end", idle.Playing);
            Assert.Equal(4.0, Cue(idle).StartAt);
        }

        [Fact]
        public void Moment_StartsAtFullLevelALeadInAhead_DropsTheQueue_AndClearsTheStageOverOneSecond()
        {
            var m = new MusicDirectorModel();
            m.Ambience("heaps", 0);
            m.Play("racks", 0, 0.6);
            Run(m, 0, 40);                       // racks handed over at 36: heaps is back under its tail
            Assert.Equal("heaps", m.AmbienceName);
            m.Queue("dead", 40);
            MusicLayer heaps = Amb(m), racks = Cue(m);
            double start = m.Moment("kin", 40);
            Assert.Equal(40 + CueClock.ScheduleLeadIn, start, 12);
            Assert.True(m.InMoment);
            Assert.Null(Cue(m).Next);
            Assert.Equal(0.9, Cue(m).Gain.ValueAt(40), 12);                        // no fade-in
            Assert.Equal(40 + 1 + 0.3, heaps.StopAt, 9);                           // ambience out over 1 s
            Assert.Equal(Math.Min(racks.EndsAt, 40 + 1 + 0.2), racks.StopAt, 9);   // old cue out over 1 s
            Assert.Equal(start + 28, Cue(m).HandAt, 9);                            // kin hands over at 28 s of its own clock
            Run(m, 40, start + 28 + 0.05);
            Assert.Equal("heaps", m.AmbienceName);
            Assert.Null(m.Layers.FirstOrDefault(l => l.Key == "dead"));
        }

        [Fact]
        public void Moment_StartIsTheCueClocksZero()
        {
            var clock = new FakeMusicClock { Now = 500 };
            var cue = new CueClock(clock);
            var m = new MusicDirectorModel();
            cue.Begin("refuge", 0, true);
            cue.Scheduled(m.Moment("refuge", clock.Now));
            clock.Now += 10.1;
            Assert.Equal(10.0, cue.Time("refuge", 10.1).Value, 9);
            Assert.Equal(10.0, m.CueTime(clock.Now).Value, 9);
        }

        [Fact]
        public void CueFailed_BringsTheAmbienceBack()
        {
            var m = new MusicDirectorModel();
            m.Ambience("order", 0);
            m.Moment("refuge", 2);
            Assert.Null(m.AmbienceName);
            m.CueFailed("refuge", 2.05);
            Assert.Null(m.Playing);
            Assert.Equal("order", m.AmbienceName);
            Assert.DoesNotContain(m.Layers, l => l.Key == "refuge");
        }

        [Fact]
        public void Stop_FadesTheCueAndReturnsTheAmbience_ThenFreesTheLayer()
        {
            var m = new MusicDirectorModel();
            m.Ambience("lower_works", 0);
            m.Play("hall", 0);
            m.Stop(5, 2);   // a checkpoint start (L8089)
            Assert.Null(m.Playing);
            Assert.Equal("lower_works", m.AmbienceName);
            Assert.Equal(0.9, Amb(m).Gain.ValueAt(5 + MusicDirectorModel.AmbienceCrossfade), 9);
            MusicLayer hall = m.Layers.Single(l => l.Key == "hall");
            Assert.Equal(5 + 2 + 0.2, hall.StopAt, 9);
            Run(m, 5, 7.3);
            Assert.DoesNotContain(m.Layers, l => l.Key == "hall");
        }

        [Fact]
        public void Ambience_CrossfadesOnChange_AndGlidesOnAScaleChange()
        {
            var m = new MusicDirectorModel();
            m.Ambience("order", 0);
            Run(m, 0, 6);
            MusicLayer order = Amb(m);
            m.Ambience("heaps", 6, scale: 0.6);
            MusicLayer heaps = Amb(m);
            Assert.NotSame(order, heaps);
            Assert.NotEqual(order.Slot, heaps.Slot);
            Assert.Equal(0.9 * Math.Exp(-1), order.Gain.ValueAt(7), 6);   // τ = 4/4
            Assert.Equal(0.54, heaps.Gain.ValueAt(10), 9);                 // 0.9 × 0.6 after a 4 s linear fade
            int layers = m.Layers.Count;
            m.Ambience("heaps", 12, scale: 1);                             // same loop, new scale: no restart
            Assert.Same(heaps, Amb(m));
            Assert.Equal(layers, m.Layers.Count);
            Assert.Equal(0.54 + (0.9 - 0.54) * (1 - Math.Exp(-1)), heaps.Gain.ValueAt(13), 6);   // τ 1.0
        }

        [Fact]
        public void Bed_FadesInOverSixSeconds_AndOutOverThree()
        {
            var m = new MusicDirectorModel();
            m.Bed(true, 0);
            Assert.Equal("bed", m.AmbienceName);
            Assert.Equal(0.13, Amb(m).Gain.ValueAt(3), 3);
            Assert.Equal(0.26, Amb(m).Gain.ValueAt(6), 9);
            MusicLayer bed = Amb(m);
            m.Bed(false, 10);
            Assert.Null(m.AmbienceName);
            Assert.Equal(10 + 3 + 0.3, bed.StopAt, 9);
        }

        [Fact]
        public void Bus_PausedDuckedAndDisabled()
        {
            var m = new MusicDirectorModel();
            Assert.Equal(1, m.BusLevel(0));
            m.SetPaused(true, 0);
            Assert.Equal(0.45 + 0.55 * Math.Exp(-1), m.BusLevel(0.3), 9);
            m.Duck(true, 10);
            Assert.Equal(0.18, m.BusLevel(20), 6);
            m.Duck(false, 20);
            Assert.Equal(0.45 - 0.27 * Math.Exp(-1), m.BusLevel(21.5), 6);   // back with τ 1.5
            m.SetEnabled(false, 30);
            Assert.Equal(0, m.BusLevel(40), 6);
        }

        [Fact]
        public void TwoSourcesPerKind_AThirdOverlappingFadeIsEvicted()
        {
            var m = new MusicDirectorModel();
            m.Play("hall", 0);
            m.Play("threshold", 0.5);
            m.Play("racks", 1.0);
            Assert.Equal(1, m.Evicted);
            Assert.Equal(2, m.Layers.Count(l => l.Kind == MusicLayerKind.Cue));
            Assert.DoesNotContain(m.Layers, l => l.Key == "hall");
            var slots = m.Layers.Where(l => l.Kind == MusicLayerKind.Cue).Select(l => l.Slot).OrderBy(s => s).ToArray();
            Assert.Equal(new[] { 0, 1 }, slots);
        }

        [Fact]
        public void Finish_AfterTheWindow_StartsTheEndCardCue5Point2SecondsLater()
        {
            var m = new MusicDirectorModel();
            m.Moment("window", 0);
            Run(m, 0, 14);
            MusicCues.Finish(m, 14, chapterOne: false);
            Run(m, 14, 19.1);
            Assert.Equal("window", m.Playing);
            Run(m, 19.1, 19.3);
            Assert.Equal("end", m.Playing);
            Assert.Equal(19.2, Cue(m).StartAt, 9);
            Assert.Equal(0.9, Cue(m).Gain.ValueAt(21.2), 9);   // fade 2 s

            var att = new MusicDirectorModel();
            att.Play("child", 0, 3);
            MusicCues.Finish(att, 5, chapterOne: true);
            Assert.Equal("endAtt", Cue(att).Next);
        }

        [Fact]
        public void Horizon_SchedulesAHandoverAheadOnTheBar()
        {
            var m = new MusicDirectorModel();
            m.Ambience("order", 0);
            m.Play("latch", 0);
            m.Update(7.85, 7.85 + 0.2);
            Assert.Equal("order", m.AmbienceName);
            Assert.Equal(8.0, Amb(m).StartAt, 12);
            Assert.Equal(0, Amb(m).Gain.ValueAt(7.9), 3);
        }

        [Fact]
        public void SameCalls_SameLog()
        {
            string Script()
            {
                var m = new MusicDirectorModel();
                var ctx = new AmbienceContext { Region = 1 };
                AmbienceRules.Apply(m, ctx, 0);
                m.Play("wake", 0, 0.6);
                double t = 0;
                for (int i = 0; i < 60 * 120; i++)
                {
                    t = i / 60.0;
                    ctx.X = t * 0.6;
                    ctx.Region = ctx.X < 13 ? 1 : 2;
                    ctx.Revealed = ctx.X > 31;
                    if (Math.Abs(t - 20) < 1e-9) m.Play("hall", t);
                    if (Math.Abs(t - 70) < 1e-9) m.Play("racks", t, 0.6);
                    AmbienceRules.Apply(m, ctx, t);
                    m.Update(t, t + 0.1);
                }
                return string.Join(";", m.Log.Select(l => l.Key.ToString("F3") + "=" + l.Value));
            }
            Assert.Equal(Script(), Script());
        }

        // ---- AmbienceRules (sceneAmbience L8147–L8162) ------------------------------------------------------------------

        [Theory]
        [InlineData(1, 3.0, false, "lower_works", 1.0)]
        [InlineData(2, 25.0, true, "lower_works", 1.0)]      // before the gate
        [InlineData(2, 40.0, false, "lower_works", 1.0)]     // past the gate, not revealed
        [InlineData(2, 40.0, true, "heaps", 1.0)]            // the racks
        [InlineData(2, 50.0, true, "order", 1.0)]            // the ration hall (x ≥ 47.9)
        [InlineData(5, 160.0, false, "heaps", 0.6)]          // ring C, low
        [InlineData(6, 250.0, false, null, 1.0)]
        public void SceneAmbience_ByRegionAndX(int region, double x, bool revealed, string want, double scale)
        {
            AmbienceChoice a = AmbienceRules.SceneAmbience(new AmbienceContext { Region = region, X = x, Revealed = revealed });
            Assert.Equal(want, a.Name);
            Assert.Equal(scale, a.Scale);
        }

        [Fact]
        public void SceneAmbience_Region4_TheCageTheCityAndUpOnly()
        {
            var c = new AmbienceContext { Region = 4, X = 100 };
            Assert.Equal("lower_works", AmbienceRules.SceneAmbience(c).Name);
            c.CageDanger = true;
            AmbienceChoice f = AmbienceRules.SceneAmbience(c);
            Assert.Equal(("failure", 1.0), (f.Name, f.FadeIn));
            c.CageCaught = true;
            Assert.Null(AmbienceRules.SceneAmbience(c).Name);   // silence into the tunnel
            c.X = 113.3; c.Awed = true;
            Assert.Equal("order", AmbienceRules.SceneAmbience(c).Name);
            c.X = 119; c.RidingUpOnly = true;
            Assert.Equal(("heaps", 0.6), (AmbienceRules.SceneAmbience(c).Name, AmbienceRules.SceneAmbience(c).Scale));
            Assert.Equal("lower_works", AmbienceRules.SceneAmbience(new AmbienceContext { Region = 4, X = 97.5, CageDanger = true }).Name);
            Assert.Equal(97.6, AmbienceRules.CgX0, 9);
            Assert.Equal(118.8, AmbienceRules.UpOnlyX0, 9);
        }

        [Fact]
        public void Apply_LeavingTheFailureLoop_FadesOutOverTwoSeconds_AndChapterOneIsLeftAlone()
        {
            var m = new MusicDirectorModel();
            var c = new AmbienceContext { Region = 4, X = 100, CageDanger = true };
            AmbienceRules.Apply(m, c, 0);
            MusicLayer failure = Amb(m);
            Assert.Equal(0.9, failure.Gain.ValueAt(1), 9);   // in over 1 s
            c.CageCaught = true;
            AmbienceRules.Apply(m, c, 10);
            Assert.Null(m.AmbienceName);
            Assert.Equal(10 + 2 + 0.3, failure.StopAt, 9);

            m.Bed(true, 20);
            AmbienceRules.Apply(m, new AmbienceContext { Region = 6, X = 250 }, 21);
            Assert.Equal("bed", m.AmbienceName);
        }
    }
}
