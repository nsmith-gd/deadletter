using System;
using System.Collections.Generic;
using System.Linq;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Folding;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Presentation;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl18;
using DeadLetter.Core.Scenes.Dl19;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Chapter 2's presentation in Core (issue #57, #52's pattern): <see cref="SomeoneHomeSounds"/>,
    /// <see cref="SomeoneHomeLights"/>, <see cref="SomeoneHomeEmitters"/> and the region 7 mix, stepped as GameHost does
    /// through DL-18's and DL-19's scripted solves and wrong paths (<see cref="Dl18ChapterTests"/>,
    /// <see cref="Dl19ChapterTests"/>). No prototype and no trace: each sound is checked at the step the mechanism or the
    /// scene reports the moment it belongs to.
    /// </summary>
    public class SomeoneHomePresentationTests
    {
        private const double Dt = ChapterSim.StepSeconds;
        private static readonly MotorInput Right = new MotorInput { Move = 1 };
        private static readonly MotorInput Use = new MotorInput { UsePressed = true };

        private struct Ev
        {
            public string Id;
            public MechanismEventKind Kind;
            public int Code, Index;
            public double Value;
        }

        private sealed class Row
        {
            public double Clock, X;
            public readonly List<string> Sounds = new List<string>();
            public readonly List<double> Volumes = new List<double>();
            public readonly List<string> Cues = new List<string>();
            public readonly List<Ev> Events = new List<Ev>();
            public double[] Levels;
            public bool[] Visible;
            public Vec3d JackLight;
            public double JackX;
            public PinSound Pin;
            public bool ClockTicking;
            public MixSnapshot Mix;
        }

        private struct Vec3d { public double X, Y, Z; }

        /// <summary>A chapter 2 sim with its presentation, recording each step (call <see cref="Each"/> after a step).</summary>
        private sealed class Rig
        {
            public readonly ChapterSim S;
            public readonly ChapterPresentation V;
            public readonly bool Calm;
            public readonly List<Row> Rows = new List<Row>();
            private readonly int _jackLight = -1;

            public Rig(ChapterSim s, bool calm = false)
            {
                S = s; Calm = calm;
                V = new ChapterPresentation(s);
                V.OnPlaced();
                for (int i = 0; i < V.Lighting.Pool.Count; i++) if (V.Lighting.Pool[i].Driver == LightDriver.HomeJack) _jackLight = i;
            }

            public void Each(ChapterSim s)
            {
                V.AfterStep(voicePlaying: false, calm: Calm);
                V.Frame(s.Clock, Dt, s.X, Calm);
                var r = new Row { Clock = s.Clock, X = s.X };
                var q = V.Sounds.Sounds;
                for (int i = 0; i < q.Count; i++) { r.Sounds.Add(q[i].Key); r.Volumes.Add(q[i].Volume); }
                foreach (var c in s.Cues) r.Cues.Add(c.ToString());
                var log = s.Graph.Log;
                for (int i = 0; i < log.Count; i++)
                    if (!log[i].Id.IsNone) r.Events.Add(new Ev { Id = log[i].Id.Value, Kind = log[i].Kind, Code = log[i].Code, Index = log[i].Index, Value = log[i].Value });
                var pool = V.Lighting.Pool;
                r.Levels = new double[pool.Count];
                r.Visible = new bool[pool.Count];
                for (int i = 0; i < pool.Count; i++) { r.Levels[i] = pool.Level(i); r.Visible[i] = pool.Visible(i); }
                if (_jackLight >= 0) { var p = pool.Position(_jackLight); r.JackLight = new Vec3d { X = p.X, Y = p.Y, Z = p.Z }; }
                if (s.Graph.TryGet(Dl19Scene.Jack.Value, out RatchetJack jack)) r.JackX = jack.X;
                if (s.Graph.TryGet(Dl19Scene.Pins.Value, out BracketPins pins)) r.Pin = pins.Sound;
                r.ClockTicking = V.Ambience.Condition(SomeoneHomeEmitters.ClockTicking);
                r.Mix = V.Mix.Snapshot;
                Rows.Add(r);
            }

            /// <summary>Steps with <paramref name="input"/> (recorded) until <paramref name="done"/>.</summary>
            public void Until(MotorInput input, Func<ChapterSim, bool> done, int max = 6000)
            {
                for (int k = 0; k < max; k++)
                {
                    S.Step(input);
                    Each(S);
                    if (done(S)) return;
                }
                throw new Xunit.Sdk.XunitException("never: x=" + S.X + " y=" + S.Y);
            }
        }

        /// <summary>The rows where the log has <paramref name="id"/>'s event or state <paramref name="code"/> (and <paramref name="index"/>, unless null).</summary>
        private static List<int> When(Rig rig, MechanismId id, MechanismEventKind kind, int code, int? index = null)
        {
            var at = new List<int>();
            for (int k = 0; k < rig.Rows.Count; k++)
                if (rig.Rows[k].Events.Any(e => e.Id == id.Value && e.Kind == kind && e.Code == code && (index == null || e.Index == index))) at.Add(k);
            return at;
        }

        /// <summary>The rows where leaf <paramref name="id"/> enters <paramref name="moving"/> from rest (down, folded or propped), not resuming after a wait.</summary>
        private static List<int> FromRest(Rig rig, MechanismId id, FoldingLeafState moving)
        {
            var at = new List<int>();
            var was = FoldingLeafState.Folded;
            for (int k = 0; k < rig.Rows.Count; k++)
                foreach (var e in rig.Rows[k].Events)
                {
                    if (e.Id != id.Value || e.Kind != MechanismEventKind.State) continue;
                    var now = (FoldingLeafState)e.Code;
                    if (now == moving && (was == FoldingLeafState.Down || was == FoldingLeafState.Folded || was == FoldingLeafState.Propped)) at.Add(k);
                    was = now;
                }
            return at;
        }

        private static List<int> WhenCue(Rig rig, string cue)
        {
            var at = new List<int>();
            for (int k = 0; k < rig.Rows.Count; k++) if (rig.Rows[k].Cues.Contains(cue)) at.Add(k);
            return at;
        }

        /// <summary>Each moment hears every one of <paramref name="keys"/> at that very step.</summary>
        private static void Hears(Rig rig, List<int> moments, string what, params string[] keys)
        {
            Assert.True(moments.Count > 0, what + ": never happened");
            foreach (int m in moments)
                foreach (string key in keys)
                    Assert.True(rig.Rows[m].Sounds.Contains(key), what + " at t=" + rig.Rows[m].Clock.ToString("F3") + ": no " + key
                                                                 + " (heard " + string.Join(", ", rig.Rows[m].Sounds) + ")");
        }

        /// <summary>The first row at or after <paramref name="clock"/>.</summary>
        private static int At(Rig rig, double clock) => rig.Rows.FindIndex(r => r.Clock >= clock - 1e-9);

        private static void AllInTheBank(Rig rig)
        {
            var bank = new HashSet<string>(SfxKeys.AllKeys());
            foreach (var r in rig.Rows)
                foreach (string k in r.Sounds) Assert.True(k != null && bank.Contains(k), "not a bank key: " + k);
            foreach (var r in rig.Rows) Assert.All(r.Volumes, v => Assert.True(double.IsFinite(v) && v > 0, "volume " + v));
        }

        private static Rig Dl18Solved(bool calm = false)
        {
            var rig = new Rig(Dl18ChapterTests.Begin(), calm);
            Dl18ChapterTests.Solve(rig.S, rig.Each);
            Assert.Equal("terrace", rig.S.Checkpoints.Current.Name);
            return rig;
        }

        private static Rig Dl19Solved(bool calm = false)
        {
            var rig = new Rig(Dl19ChapterTests.Begin(), calm);
            new Dl19ChapterTests.Play(rig.S, rig.Each).Solve();
            Assert.Equal("repaired", rig.S.Checkpoints.Current.Name);
            return rig;
        }

        // ---- Sounds: DL-18 ---------------------------------------------------------------------------------------------------

        [Fact]
        public void Dl18_ScriptedSolve_TheBedsSprings_AndTheBenchsChains_SoundAsEachSetsOff_AndClunkAtItsStop()
        {
            var rig = Dl18Solved();
            var state = MechanismEventKind.State;
            Hears(rig, When(rig, Dl18Scene.Bed, state, (int)FoldingLeafState.Folding), "the bed folds away", SfxKeys.Creak(0.8));
            Hears(rig, When(rig, Dl18Scene.Bed, state, (int)FoldingLeafState.Folded), "the bed in its recess", SfxKeys.Simple["clunk"]);
            Hears(rig, FromRest(rig, Dl18Scene.Bench, FoldingLeafState.Unfolding), "the bench comes down", SfxKeys.Chain(1.2));
            Assert.Equal(FromRest(rig, Dl18Scene.Bench, FoldingLeafState.Unfolding).Count,                // not again when it resumes after waiting for him
                rig.Rows.Count(r => r.Sounds.Contains(SfxKeys.Chain(1.2))));
            Hears(rig, When(rig, Dl18Scene.Bench, state, (int)FoldingLeafState.Down), "the bench at its stop", SfxKeys.Simple["clunk"]);
            Assert.Single(When(rig, Dl18Scene.Bed, state, (int)FoldingLeafState.Folding));
            Assert.Equal(1, rig.Rows.Count(r => r.Sounds.Contains(SfxKeys.Creak(0.8))));             // once, as it sets off
            AllInTheBank(rig);
        }

        [Fact]
        public void Dl18_BenchPropsOnTheQuilt_WithAThump_AndTheSlideOffRocksAndBumps()
        {
            var rig = new Rig(Dl18ChapterTests.Begin());
            var s = rig.S;
            s.Motor.Place(353.45, 0.45);                                                           // on the bed, at the strap
            s.Step(Use); rig.Each(s);
            rig.Until(default, x => !x.Busy && x.Graph.Get<FoldingLeaf>(Dl18Scene.Bench).State == FoldingLeafState.Propped);
            Hears(rig, When(rig, Dl18Scene.Bench, MechanismEventKind.Event, (int)FoldingLeafEvent.Met, 0), "the bench meets the quilt", SfxKeys.Simple["thud"]);

            s.Step(new MotorInput { Move = 1, JumpPressed = true }); rig.Each(s);                  // at the tilted bench: rock, slide
            rig.Until(Right, x => x.SceneActKind == Dl18SlideAct.SlideKind, 120);
            rig.Until(default, x => !x.Busy, 120);
            Hears(rig, WhenCue(rig, "dl18.bench.rock"), "the rock", SfxKeys.Creak(0.5));
            Hears(rig, WhenCue(rig, "dl18.bench.slide"), "the slide", SfxKeys.Simple["scrape"], SfxKeys.Simple["land"]);
            AllInTheBank(rig);
        }

        [Fact]
        public void Dl18_TheChainClanks_AtEachTug_AndTheAlarmClockRingsTwoSeconds_ItsTickStoppedMeanwhile()
        {
            var rig = new Rig(Dl18ChapterTests.Begin());
            var s = rig.S;
            s.Motor.Place(348.0, 0);
            s.Step(Use); rig.Each(s);
            Assert.Equal(Dl18Rules.WorksDoor, s.SceneActKind);
            rig.Until(default, x => !x.Busy);
            var clanks = WhenCue(rig, "dl18.chain.clank");
            Assert.Equal(2, clanks.Count);
            Hears(rig, clanks, "a tug at the chain", SfxKeys.Simple["clank"], SfxKeys.Rattle(0.5));

            int from = rig.Rows.Count;
            s.Motor.Place(351.8, 0);
            s.Step(Use); rig.Each(s);
            Assert.Equal(Dl18Rules.AlarmClock, s.SceneActKind);
            Assert.False(rig.Rows[rig.Rows.Count - 1].ClockTicking);
            rig.Until(default, x => !x.Busy);
            int ring = WhenCue(rig, "dl18.clock.ring").Single();
            Hears(rig, new List<int> { ring }, "the ring", SfxKeys.Simple["alarmBell"]);
            string bell = SfxKeys.Simple["alarmBell"];
            var trills = Enumerable.Range(from, rig.Rows.Count - from).Where(k => rig.Rows[k].Sounds.Contains(bell)).ToList();
            Assert.Equal(4, trills.Count);                                                         // 0, 0.55, 1.1, 1.65 s: within the 2 s
            for (int i = 0; i < trills.Count; i++)
                Assert.InRange(rig.Rows[trills[i]].Clock - rig.Rows[ring].Clock, i * SomeoneHomeSounds.RingEvery - 1e-9, i * SomeoneHomeSounds.RingEvery + Dt + 1e-9);
            Hears(rig, WhenCue(rig, "dl18.clock.still"), "the pat", SfxKeys.Simple["tap"]);
            for (int k = from; k < rig.Rows.Count - 1; k++) Assert.False(rig.Rows[k].ClockTicking, "ticks while ringing at t=" + rig.Rows[k].Clock);
            Assert.True(rig.Rows[rig.Rows.Count - 1].ClockTicking);                                // idle again
            AllInTheBank(rig);
        }

        [Fact]
        public void Dl18_TheRelayBox_ClicksEvery7s_InStepWithItsPilotLamp()
        {
            var rig = new Rig(Dl18ChapterTests.Begin());
            var s = rig.S;
            s.Motor.Place(SomeoneHomeLights.RelayX[0], 0);
            rig.Until(default, x => x.Clock >= 15.5);
            string click = SfxKeys.Simple["click"];
            var clicks = Enumerable.Range(0, rig.Rows.Count).Where(k => rig.Rows[k].Sounds.Contains(click)).ToList();
            var expected = Enumerable.Range(1, rig.Rows.Count - 1)
                .Where(k => Math.Floor(rig.Rows[k].Clock / 7) > Math.Floor(rig.Rows[k - 1].Clock / 7)).ToList();
            Assert.True(expected.Count >= 2);
            Assert.Equal(expected, clicks);
            int pilot = Enumerable.Range(0, rig.V.Lighting.Pool.Count).First(i => rig.V.Lighting.Pool[i].Driver == LightDriver.HomeRelayPilot);
            double b = rig.V.Lighting.Pool[pilot].Intensity;
            foreach (int k in clicks)
            {
                int end = At(rig, rig.Rows[k].Clock + SomeoneHomeLights.BlinkSeconds);
                double peak = Enumerable.Range(k, end - k + 1).Max(j => rig.Rows[j].Levels[pilot]);
                Assert.True(peak > 0.95 * b, "the pilot blinks with the click: " + peak);
                Assert.Equal(b * SomeoneHomeLights.PilotRest, rig.Rows[k - 2].Levels[pilot], 9);     // at rest just before
                int quiet = At(rig, rig.Rows[k].Clock + 1);
                Assert.Equal(b * SomeoneHomeLights.PilotRest, rig.Rows[quiet].Levels[pilot], 9);
            }
        }

        // ---- Sounds: DL-19 ---------------------------------------------------------------------------------------------------

        [Fact]
        public void Dl19_ScriptedSolve_TheJackClunksAndClicksPerNotch_ThePinsClinkAndSeatWithADoubleClick()
        {
            var rig = Dl19Solved();
            var ev = MechanismEventKind.Event;
            Hears(rig, When(rig, Dl19Scene.Jack, ev, (int)RatchetJackEvent.Clunk), "the jack into its pocket", SfxKeys.Simple["clunk"]);
            var notches = When(rig, Dl19Scene.Jack, ev, (int)RatchetJackEvent.Click);
            Assert.True(notches.Count >= 10, "notches: " + notches.Count);
            Hears(rig, notches, "a ratchet notch", SfxKeys.Simple["gateTick"]);
            Hears(rig, When(rig, Dl19Scene.Pins, ev, (int)BracketPinsEvent.Clink), "the bent pin into the cup", SfxKeys.Simple["clack"]);
            Hears(rig, When(rig, Dl19Scene.Pins, ev, (int)BracketPinsEvent.Taken), "the spare from its clip", SfxKeys.Simple["tap"]);
            int seated = When(rig, Dl19Scene.Pins, ev, (int)BracketPinsEvent.Seated).Single();
            Hears(rig, new List<int> { seated }, "the spare seats", SfxKeys.Simple["click"]);
            int second = At(rig, rig.Rows[seated].Clock + SomeoneHomeSounds.DoubleClick);
            Assert.Contains(SfxKeys.Simple["click"], rig.Rows[second].Sounds);                    // "a clean double click"
            Assert.Contains("held", rig.Rows[seated].Cues);
            AllInTheBank(rig);
        }

        [Fact]
        public void Dl19_TheBentPin_CreaksOnTheSway_WhileLoaded_AndRattlesWhileSlack_NeverWhileQuiet()
        {
            var rig = Dl19Solved();
            string creak = SfxKeys.Creak(0.6), rattle = SfxKeys.Rattle(0.5);
            int creaks = 0;
            for (int k = 1; k < rig.Rows.Count; k++)
            {
                var r = rig.Rows[k];
                bool sway = Math.Floor(r.Clock / SomeoneHomeSounds.SwaySeconds) > Math.Floor(rig.Rows[k - 1].Clock / SomeoneHomeSounds.SwaySeconds);
                bool near = Math.Abs(r.X - SomeoneHomeSounds.PinX) < SomeoneHomeSounds.PinHear;
                Assert.Equal(sway && near && r.Pin == PinSound.Creak, r.Sounds.Contains(creak));
                if (r.Pin != PinSound.Rattle) Assert.DoesNotContain(rattle, r.Sounds);
                else if (sway && near) Assert.Contains(rattle, r.Sounds);
                if (r.Sounds.Contains(creak)) creaks++;
            }
            Assert.True(creaks >= 2, "creaks: " + creaks);
        }

        [Fact]
        public void Dl19_PinFirst_ScrapesAndBangsOntoTheStops_AStrainMovesNothing_AndSteppingOnLurchesAndSettles()
        {
            var rig = new Rig(Dl19ChapterTests.Begin());
            var play = new Dl19ChapterTests.Play(rig.S, rig.Each);
            play.UsePins();
            play.Until(default, x => !x.Busy && x.Act == null, 200);
            var ev = MechanismEventKind.Event;
            Hears(rig, When(rig, Dl19Scene.Pins, ev, (int)BracketPinsEvent.Draw), "the loaded pin draws and bites", SfxKeys.Simple["scrape"]);
            Hears(rig, When(rig, Dl19Scene.Landing, ev, (int)HalfLandingEvent.Drop, 0), "the drop onto the stops", SfxKeys.Simple["clank"], SfxKeys.Simple["thud"]);
            play.UsePins();
            Hears(rig, When(rig, Dl19Scene.Pins, ev, (int)BracketPinsEvent.Strain), "a strain", SfxKeys.Simple["strain"]);

            play.Until(Right, x => x.Vx == 0 && x.X > 363.3);                                      // step on: it rocks on the stops
            play.Step(new MotorInput { Move = 1, JumpPressed = true });
            play.Until(default, x => x.Act == null && !x.Motor.IsMantling && x.Grounded, 400);
            Hears(rig, WhenCue(rig, "dl19.rock"), "the rock", SfxKeys.Simple["lurch"], SfxKeys.Simple["clank"]);
            Hears(rig, WhenCue(rig, "dl19.settle"), "Settle", SfxKeys.Servo(0.3, 300, 420));
            AllInTheBank(rig);
        }

        [Fact]
        public void Dl19_StepOnDrooping_Lurches()
        {
            var rig = new Rig(Dl19ChapterTests.Begin());
            var play = new Dl19ChapterTests.Play(rig.S, rig.Each);
            play.Until(Right, x => x.Vx == 0 && x.X > 363.3);
            play.Step(new MotorInput { Move = 1, JumpPressed = true });
            play.Until(default, x => x.Act == null && !x.Motor.IsMantling && x.Grounded, 400);
            Hears(rig, WhenCue(rig, "dl19.lurch"), "the lurch", SfxKeys.Simple["lurch"]);
            Hears(rig, WhenCue(rig, "dl19.settle"), "Settle", SfxKeys.Servo(0.3, 300, 420));
        }

        [Fact]
        public void Dl19_TheDripTube_TicksOnceAMinute_WhereHeCanHearIt()
        {
            var rig = new Rig(Dl19ChapterTests.Begin());
            rig.Until(default, x => x.Clock >= Dl19Rules.DripSeconds + 1);
            var drips = WhenCue(rig, "dl19.drip");
            Assert.Single(drips);
            Hears(rig, drips, "the drip", SfxKeys.Simple["drip"]);
            Assert.Equal(1, rig.Rows.Count(r => r.Sounds.Contains(SfxKeys.Simple["drip"])));
        }

        // ---- Lights ----------------------------------------------------------------------------------------------------------

        [Fact]
        public void LightsFor_Chapter2_IsTheAlwaysOnesAndSomeoneHomesRows_ThePrologueAndChapter1Unchanged()
        {
            foreach (bool touch in new[] { false, true })
            {
                var ch2 = ChapterPresentation.LightsFor(ChapterDefs.SomeoneHomeId, touch);
                var always = PrologueLights.Build(touch).Where(d => d.Group == LightGroup.Always).Select(d => d.Name).ToArray();
                var home = SomeoneHomeLights.Build(touch);
                Assert.Equal(always.Concat(home.Select(d => d.Name)).ToArray(), ch2.Select(d => d.Name).ToArray());
                Assert.All(home, d => Assert.Equal(LightGroup.SomeoneHome, d.Group));
                Assert.All(home, d => Assert.True(d.Position.X >= Dl18Scene.X0 && d.Position.X <= Dl19Scene.X1, d.Name));

                Assert.Equal(PrologueLights.Build(touch).Select(d => d.Name), ChapterPresentation.LightsFor(ChapterDefs.PrologueId, touch).Select(d => d.Name));
                var ch1 = ChapterPresentation.LightsFor(ChapterDefs.AttendanceId, touch);
                Assert.DoesNotContain(ch1, d => d.Group == LightGroup.SomeoneHome);
                Assert.Equal(always.Length + AttendanceLights.Build(touch).Length, ch1.Length);
            }
            Assert.False(LightRegions.Visible(LightGroup.SomeoneHome, 6, LightZone.None, false));
            Assert.True(LightRegions.Visible(LightGroup.SomeoneHome, 7, LightZone.None, false));
            Assert.False(LightRegions.Visible(LightGroup.Attendance, 7, LightZone.None, false));
        }

        public static IEnumerable<object[]> Calm() => new[] { new object[] { false }, new object[] { true } };

        [Theory]
        [MemberData(nameof(Calm))]
        public void Lights_ThroughBothSolves_AreFinite_OnlyChapter2s_AndWithinTheFlashLimits(bool calm)
        {
            foreach (var rig in new[] { Dl18Solved(calm), Dl19Solved(calm) })
            {
                var pool = rig.V.Lighting.Pool;
                Assert.Equal(7, rig.V.Lighting.Regions.Region);
                foreach (var r in rig.Rows)
                    for (int i = 0; i < pool.Count; i++)
                    {
                        Assert.True(double.IsFinite(r.Levels[i]) && r.Levels[i] >= 0, pool[i].Name + " level " + r.Levels[i]);
                        Assert.Equal(pool[i].Group == LightGroup.Always || pool[i].Group == LightGroup.SomeoneHome, r.Visible[i]);
                    }
                for (int i = 0; i < pool.Count; i++)
                {
                    double[] curve = rig.Rows.Select(r => r.Levels[i]).ToArray();
                    FlashCount c = FlashSafety.Count(curve, 1 / Dt);
                    Assert.True(c.WithinLimit, pool[i].Name + ": " + c);
                    if (calm && pool[i].Group == LightGroup.SomeoneHome) Assert.Equal(0, c.Transitions);   // calm: nothing blinks
                }
            }
        }

        [Fact]
        public void TheRelayPilots_AreInFlashEffects_AndPass_CalmOnAndOff()
        {
            FlashEffect e = FlashEffects.All().Single(x => x.Id == "ch2.relayPilots");
            Assert.True(e.Ported);
            foreach (bool calm in new[] { false, true })
            {
                var a = FlashEffects.Assess(FlashEffects.All(), calm).Single(x => x.Effect.Id == e.Id);
                Assert.True(a.Passes, a.ToString());
                Assert.True(e.Measure(calm).WithinLimit);
            }
            Assert.Equal(0, e.Measure(calm: true).Transitions);
            Assert.True(e.Measure(calm: false).Transitions > 0);                                   // it does blink, slowly
            for (double t = 0; t < 21; t += 0.01)
            {
                double v = SomeoneHomeLights.PilotLevel(t, false);
                Assert.InRange(v, SomeoneHomeLights.PilotRest, 1.0);
                Assert.Equal(SomeoneHomeLights.PilotCalm, SomeoneHomeLights.PilotLevel(t, true));
            }
        }

        [Fact]
        public void TheJacksPool_RidesOverTheJack()
        {
            var rig = Dl19Solved();
            Assert.Contains(rig.Rows, r => r.JackX > 363.0);                                      // it went to the pocket and back
            foreach (var r in rig.Rows)
            {
                Assert.Equal(r.JackX, r.JackLight.X, 12);
                Assert.Equal(Dl19ChapterTests.Jack(rig.S).Params.FloorY + SomeoneHomeLights.JackY, r.JackLight.Y, 12);
                Assert.Equal(SomeoneHomeLights.JackZ, r.JackLight.Z, 12);
            }
        }

        // ---- Emitters and mix ------------------------------------------------------------------------------------------------

        [Fact]
        public void Chapter2_HasItsOwnEmitters_InRegion7_AndTheRingAMix()
        {
            var rig = Dl18Solved();
            Assert.Equal(SomeoneHomeEmitters.All.Length, rig.V.Ambience.Count);
            Assert.All(SomeoneHomeEmitters.All, e => Assert.Equal(7, e.Region));
            Assert.All(SomeoneHomeEmitters.All, e => Assert.InRange(e.X, Dl18Scene.X0, Dl19Scene.X1));
            Assert.Same(PrologueEmitters.All, ChapterPresentation.EmittersFor(ChapterDefs.PrologueId));
            Assert.Same(PrologueEmitters.All, ChapterPresentation.EmittersFor(ChapterDefs.AttendanceId));
            Assert.All(rig.Rows, r => Assert.Equal(MixSnapshot.RingA, r.Mix));
            Assert.True(rig.Rows.All(r => r.ClockTicking));                                        // the solve never rings it

            Assert.Equal(MixSnapshot.RingA, MixRules.SnapshotFor(7, LightZone.None));
            Assert.Equal("RingA", MixRules.Name(MixSnapshot.RingA));
            Assert.Equal(MixSnapshot.School, MixRules.SnapshotFor(6, LightZone.None));             // chapter 1 keeps its own
            Assert.Equal(MixSnapshot.RingC, MixRules.SnapshotFor(5, LightZone.None));

            // The gallery's lamps buzz near them; the clock ticks in the box room.
            var amb = rig.V.Ambience;
            int lamp = Enumerable.Range(0, amb.Count).First(i => amb[i].Kind == EmitterKind.Buzz);
            int tick = Enumerable.Range(0, amb.Count).Single(i => amb[i].Kind == EmitterKind.Tick);
            Assert.Equal(351.95, amb[tick].X);
            var s = Dl18ChapterTests.Begin();
            var view = new ChapterPresentation(s);
            view.OnPlaced();
            s.Motor.Place(348.0, 0);
            bool blipped = false;
            for (int k = 0; k < 60; k++) { s.Step(default); view.Frame(s.Clock, Dt, s.X, false); }
            Assert.True(view.Ambience.Gain(lamp) > 0);
            s.Motor.Place(351.95, 0);
            for (int k = 0; k < 120; k++) { s.Step(default); view.Frame(s.Clock, Dt, s.X, false); blipped |= view.Ambience.Blip(tick); }
            Assert.True(blipped);
        }

        [Fact]
        public void TheChapter2Sounds_AreOnlyInChapter2()
        {
            // The prologue and chapter 1 never step SomeoneHomeSounds: their sims have no chapter 2 mechanisms, and
            // ChapterSounds builds it only for someone_home. A chapter 1 view still has chapter 1's lights and emitters.
            var view = new ChapterPresentation(new ChapterSim(ChapterDefs.Attendance()));
            Assert.Equal(PrologueEmitters.All.Length, view.Ambience.Count);
            for (int i = 0; i < view.Ambience.Count; i++) Assert.Same(PrologueEmitters.All[i], view.Ambience[i]);
            Assert.DoesNotContain(Enumerable.Range(0, view.Lighting.Pool.Count), i => view.Lighting.Pool[i].Group == LightGroup.SomeoneHome);
        }
    }
}
