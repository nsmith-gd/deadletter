using System;
using System.Collections.Generic;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Cycles;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>Cycle clocks (§4.13k): DL-13's lesson and DL-14a's night-light exactly; DL-21 and DL-23 as chapter 2 data.</summary>
    public class CycleTests
    {
        private const double Dt = Mech.Dt;

        private static List<MechanismEvent> Of(MechanismGraph g, MechanismId id, CycleClockEvent e)
            => Mech.Events(g).FindAll(x => x.Id == id && x.Kind == MechanismEventKind.Event && x.Code == (int)e);

        // ---- CycleTrack -----------------------------------------------------------------------------------------------------

        [Theory]
        [InlineData(-1, 0)] [InlineData(0.99, 0)] [InlineData(1.0, 1)] [InlineData(5.59, 1)] [InlineData(5.6, 0)] [InlineData(20, 0)]
        public void Track_Window_IsOneOnHalfOpenInterval_L5422(double t, double v)
        {
            Assert.Equal(v, CycleTrack.Window("w", 1.0, 5.6).At(t));
        }

        [Theory]
        [InlineData(0, 1)] [InlineData(3, 1)] [InlineData(3.75, 0.5)] [InlineData(4.5, 0)] [InlineData(8, 0)] [InlineData(9, 0.5)] [InlineData(10, 1)] [InlineData(11, 1)]
        public void Track_Keys_AreLinearBetweenKeys_Sun14a_L5931(double t, double v)
        {
            Assert.Equal(v, CycleClockParams.Dl14aNightLight().Tracks[0].At(t), 12);
        }

        // ---- DL-13 the lesson -----------------------------------------------------------------------------------------------

        private sealed class Lesson
        {
            public readonly TestSource Seat = new TestSource("dl13.seat");
            public readonly CycleBrake Brake = new CycleBrake("dl13.brake", CycleBrakeParams.Dl13Brake());
            public readonly CycleClock C = new CycleClock("dl13.lesson", CycleClockParams.Dl13Lesson());
            public readonly MechanismGraph G;
            public Lesson(string cp = "lesson") { G = Mech.Graph(cp, Seat, Brake, C); }

            /// <summary>Seat the pupil and run until the phase reaches <paramref name="t"/>.</summary>
            public void RunTo(double t)
            {
                Seat.Engaged = true;
                Mech.RunUntil(G, () => C.On && C.Phase >= t);
            }
        }

        private static double Tree(double t) => t < 6.8 ? 0 : t < 10.4 ? (t - 6.8) / 3.6 : Math.Max(0, 1 - (t - 10.4) / 1.2);   // L5426

        [Fact]
        public void Lesson_StartsWhenThePupilSits_ALapEvery12s_L5411_L5419()
        {
            var l = new Lesson();
            Mech.Run(l.G, 10);
            Assert.Equal(CycleClockState.Off, l.C.State);
            Assert.False(l.C.Engaged);
            l.Seat.Engaged = true;
            Mech.Run(l.G, 1);
            Assert.Single(Of(l.G, "dl13.lesson", CycleClockEvent.Started));
            Assert.Single(Of(l.G, "dl13.lesson", CycleClockEvent.Lap));       // the lesson's bell and voice (L5419)
            Assert.True(Mech.Entered(l.G, "dl13.lesson", CycleClockState.Running));
            Assert.Equal(Dt, l.C.Phase, 15);
            Assert.True(l.C.Engaged);                                         // lesson.on: the brake now holds it
            int n = Mech.RunUntil(l.G, () => Of(l.G, "dl13.lesson", CycleClockEvent.Lap).Count > 0);
            Assert.InRange(n + 1, 719, 721);
            Assert.True(l.C.Phase < 2 * Dt);
            Assert.Equal(l.C.Phase / 12, l.C.Dial, 15);                       // the dial hand (L5431)
        }

        [Fact]
        public void Lesson_StepsComeOutAt1_0_2_6_4_2_AndFoldAt5_6_6_2_6_8_At1Over0_35s_L291_L5420_L5425()
        {
            var l = new Lesson();
            l.Seat.Engaged = true;
            var up = new List<(int, double)>();
            var down = new List<(int, double)>();
            var solid = new double[3];
            for (int k = 0; k < 720 - 2; k++)
            {
                Mech.Run(l.G, 1);
                double t = l.C.Phase;
                foreach (var e in Of(l.G, "dl13.lesson", CycleClockEvent.TrackUp)) up.Add((e.Index, t));
                foreach (var e in Of(l.G, "dl13.lesson", CycleClockEvent.TrackDown)) down.Add((e.Index, t));
                for (int i = 0; i < 3; i++) if (solid[i] == 0 && l.C.IsOut(i)) solid[i] = t;
                Assert.Equal(Tree(t), l.C.Value(3), 12);
            }
            double[] outAt = { 1.0, 2.6, 4.2 }, foldAt = { 5.6, 6.2, 6.8 };
            Assert.Equal(3, up.Count);
            Assert.Equal(3, down.Count);
            for (int i = 0; i < 3; i++)
            {
                Assert.Equal(i, up[i].Item1);
                Assert.InRange(up[i].Item2, outAt[i] + 0.175 - Dt, outAt[i] + 0.175 + Dt);             // the clack, through 0.5
                Assert.InRange(down[i].Item2, foldAt[i] + 0.175 - Dt, foldAt[i] + 0.175 + Dt);         // the thud
                Assert.InRange(solid[i], outAt[i] + 0.95 * 0.35 - Dt, outAt[i] + 0.95 * 0.35 + Dt);    // attOut (L5243)
            }
        }

        [Fact]
        public void Lesson_PupilLeaves_ItStops_StepsFoldAt1Over0_35s_TreeAt1PerSecond_DialStays_L5412_L5428()
        {
            var l = new Lesson();
            l.RunTo(9.0);
            double t = l.C.Phase, tree = l.C.Value(3), s3 = l.C.Value(2);
            Assert.True(tree > 0.5 && s3 < 0.1);
            l.Seat.Engaged = false;
            Mech.Run(l.G, 1);
            Assert.Equal(0, Assert.Single(Of(l.G, "dl13.lesson", CycleClockEvent.Stopped)).Index);
            Assert.Equal(CycleClockState.Returning, l.C.State);
            Assert.False(l.C.Engaged);
            Assert.Equal(tree - Dt, l.C.Value(3), 12);
            Assert.Equal(Math.Max(0, s3 - Dt / 0.35), l.C.Value(2), 12);
            Assert.Empty(Of(l.G, "dl13.lesson", CycleClockEvent.TrackDown));   // folding home is silent (L5428)
            int n = Mech.RunUntil(l.G, () => l.C.State == CycleClockState.Off);
            Assert.InRange((n + 1) * Dt, tree - Dt, tree + Dt);
            Assert.Equal(t, l.C.Phase);                                         // the dial hand stays where it stopped
            l.Seat.Engaged = true;
            Mech.Run(l.G, 1);
            Assert.Single(Of(l.G, "dl13.lesson", CycleClockEvent.Started));
            Assert.Equal(Dt, l.C.Phase, 15);                                    // a new lesson from the top (L5411)
        }

        [Fact]
        public void Lesson_TheBrakeFreezesItWhereItIs_EvenIfThePupilLeaves_L5350_L5413()
        {
            var l = new Lesson();
            l.RunTo(4.6);
            Mech.PlayAct(l.G, l.Brake);
            Assert.Equal(CycleClockState.Braked, l.C.State);
            var values = new double[4];
            for (int i = 0; i < 4; i++) values[i] = l.C.Value(i);
            double t = l.C.Phase;
            Assert.InRange(t, 4.6 + 0.3, 4.6 + 0.4);                           // it froze 0.35 s into the pull
            for (int i = 0; i < 3; i++) Assert.True(l.C.IsOut(i));             // all three steps out: the way up (L5355)
            l.Seat.Engaged = false;
            Mech.Run(l.G, 600);
            Assert.Equal(CycleClockState.Braked, l.C.State);
            Assert.Equal(t, l.C.Phase);
            Assert.True(l.C.Engaged);
            for (int i = 0; i < 4; i++) Assert.Equal(values[i], l.C.Value(i));
            bool stopped = false;                                               // released with nobody seated: it stops
            Mech.PlayAct(l.G, l.Brake, onStep: (k, f) => stopped |= Of(l.G, "dl13.lesson", CycleClockEvent.Stopped).Count > 0);
            Assert.True(stopped);
            Assert.False(l.C.On);
        }

        [Fact]
        public void Lesson_BrakeWithNoLessonRunning_OnlyClunks_L5344()
        {
            var l = new Lesson();
            int clunks = 0;
            Mech.PlayAct(l.G, l.Brake, onStep: (k, f) => { if (Mech.Emitted(l.G, "dl13.brake", CycleBrakeEvent.Clunk)) clunks++; });
            Assert.Equal(1, clunks);
            Assert.Equal(CycleClockState.Off, l.C.State);
            l.Seat.Engaged = true;
            Mech.Run(l.G, 1);
            Assert.Equal(CycleClockState.Running, l.C.State);
        }

        [Theory]
        [InlineData("lesson", CycleClockState.Off, 0.0, 0.0)]
        [InlineData("gallery13", CycleClockState.Braked, 4.9, 1.0)]
        [InlineData("workshop", CycleClockState.Braked, 4.9, 1.0)]
        public void Lesson_ResetFromCheckpoint_L5236(string cp, CycleClockState state, double t, double steps)
        {
            var l = new Lesson(cp);
            l.Seat.Engaged = cp != "lesson";                                    // fig2 is at the seat past gallery13
            Assert.Equal(state, l.C.State);
            Assert.Equal(t, l.C.Phase);
            for (int i = 0; i < 3; i++) Assert.Equal(steps, l.C.Value(i));
            Assert.Equal(0, l.C.Value(3));
            Assert.Equal(cp != "lesson", l.C.Engaged);
            Mech.Run(l.G, 60);
            Assert.Equal(state == CycleClockState.Braked ? 4.9 : 0, l.C.Phase, 9);   // braked, or nobody seated
        }

        [Fact]
        public void Lesson_RestoredMidLap_ContinuesBitIdentically()
        {
            var a = new Lesson();
            a.RunTo(5.5);
            var b = new Lesson("gallery13");
            b.G.Restore(Mech.Snapshot(a.G));
            b.Seat.Engaged = true;
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            for (int k = 0; k < 900; k++)
            {
                if (k == 400) a.Seat.Engaged = b.Seat.Engaged = false;
                Mech.Run(a.G, 1);
                Mech.Run(b.G, 1);
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
                Assert.Equal(Mech.Events(a.G).Count, Mech.Events(b.G).Count);
            }
        }

        // ---- DL-14a the night-light -----------------------------------------------------------------------------------------

        private sealed class Night
        {
            public readonly TestSource Blinds = new TestSource("dl14a.blinds");
            public readonly CycleBrake Brake = new CycleBrake("dl14a.brake", CycleBrakeParams.Dl14aBrake());
            public readonly CycleClock C = new CycleClock("dl14a.nightLight", CycleClockParams.Dl14aNightLight());
            public readonly Door Door = new Door("dl14a.door", DoorParams.Dl14aDoor());
            public readonly MechanismGraph G;

            public Night(bool blinds, string cp = "dorm")
            {
                Blinds.Engaged = blinds;
                G = new MechanismGraph();
                G.Add(Blinds); G.Add(Brake); G.Add(C); G.Add(Door);
                G.Build();
                G.Reset(Mech.Cp(cp));
            }
        }

        private static double Sun(double t) => t < 3 ? 1 : t < 4.5 ? 1 - (t - 3) / 1.5 : t < 8 ? 0 : (t - 8) / 2;   // sun14a, L5931

        [Fact]
        public void NightLight_A10sCycle_AlwaysRunning_SunAsThePrototype_L5931_L6219()
        {
            var n = new Night(false);
            Assert.Equal(CycleClockState.Running, n.C.State);
            double prev = 0;
            int wraps = 0;
            for (int k = 0; k < 1300; k++)
            {
                Mech.Run(n.G, 1);
                double t = n.C.Phase;
                if (t < prev) { wraps++; Assert.InRange(t, 0, Dt); }
                prev = t;
                Assert.Equal(Sun(t), n.C.Value(0), 15);
                Assert.False(n.C.Engaged);                                  // blinds up: never dark
            }
            Assert.Equal(2, wraps);
        }

        [Fact]
        public void NightLight_DarkIsSunAtMost0_05AndBothBlindsDown_TheDoorOpens1_2sLater_Over1_4s_L6222_L6228()
        {
            var n = new Night(true);
            int dark = -1, opening = -1, open = -1;
            for (int k = 1; k <= 900 && open < 0; k++)
            {
                Mech.Run(n.G, 1);
                Assert.Equal(Sun(n.C.Phase) <= 0.05, n.C.Engaged);
                if (dark < 0 && n.C.Engaged) dark = k;
                if (Mech.Entered(n.G, "dl14a.door", DoorState.Opening)) opening = k;
                if (Mech.Entered(n.G, "dl14a.door", DoorState.Open)) open = k;
            }
            Assert.InRange(dark * Dt, 4.425, 4.425 + Dt);                  // 1 − (t − 3) / 1.5 ≤ 0.05
            Assert.InRange((opening - dark) * Dt, 1.2, 1.2 + 2 * Dt);
            Assert.InRange((open - opening) * Dt, 1.4 - 2 * Dt, 1.4 + Dt);
        }

        [Fact]
        public void NightLight_TheBrakeHoldsItDark_L6079_L6219()
        {
            var n = new Night(true);
            Mech.RunUntil(n.G, () => n.C.Phase >= 4.6);
            Mech.PlayAct(n.G, n.Brake);
            Assert.Equal(CycleClockState.Braked, n.C.State);
            double t = n.C.Phase;
            Mech.Run(n.G, 1200);
            Assert.Equal(t, n.C.Phase);
            Assert.True(n.C.Engaged);
            Assert.Equal(DoorState.Open, n.Door.State);
            Mech.PlayAct(n.G, n.Brake);
            Assert.Equal(CycleClockState.Running, n.C.State);
        }

        [Theory]
        [InlineData("dorm", true, CycleClockState.Running, 0.0, 1.0, DoorState.Closed)]
        [InlineData("corridor", true, CycleClockState.Braked, 6.0, 0.0, DoorState.Open)]
        [InlineData("corridor", false, CycleClockState.Braked, 6.0, 0.0, DoorState.Closed)]
        public void NightLight_ResetFromCheckpoint_L5913_L5914(string cp, bool blinds, CycleClockState state, double t, double sun, DoorState door)
        {
            var n = new Night(blinds, cp);
            Assert.Equal(state, n.C.State);
            Assert.Equal(t, n.C.Phase);
            Assert.Equal(sun, n.C.Value(0));
            Assert.Equal(door, n.Door.State);
        }

        // ---- DL-21 the evening routine (chapter 2 data) ---------------------------------------------------------------------

        private sealed class Evening
        {
            public readonly TestSource Places = new TestSource("dl21.places");
            public readonly TestSource Brake = new TestSource("dl21.brake");
            public readonly TestSource Top = new TestSource("dl21.tableTop");
            public readonly CycleClock C = new CycleClock("dl21.evening", CycleClockParams.Dl21Evening());
            public readonly MechanismGraph G;
            public Evening(bool places = true) { Places.Engaged = places; G = Mech.Graph(Places, Brake, Top, C); }
            public double Table => C.Value(0);
            public double Shutter => C.Value(1);
            public double Ledge => C.Value(2);

            public void RunTo(double t) => Mech.RunUntil(G, () => C.On && C.Phase >= t);
        }

        [Fact]
        public void Evening_The14sTimeline_EveryCueOncePerLap_AtItsTime_ChapterPlan4()
        {
            var e = new Evening();
            var p = CycleClockParams.Dl21Evening();
            var seen = new int[p.Cues.Length];
            for (int k = 0; k < 3 * 840 - 10; k++)
            {
                Mech.Run(e.G, 1);
                foreach (var ev in Of(e.G, "dl21.evening", CycleClockEvent.Cue))
                {
                    seen[ev.Index]++;
                    double at = p.Cues[ev.Index].At, t = e.C.Phase;
                    double since = t >= at ? t - at : t + 14 - at;                 // the step that passed it
                    Assert.InRange(since, 0, Dt + 1e-9);
                    Assert.Equal(at, ev.Value);
                }
            }
            foreach (int c in seen) Assert.Equal(3, c);
            Assert.Equal(2, e.C.CueIndex("bowl1Set"));
        }

        [Fact]
        public void Evening_TheTableAndTheLedgeServeTogetherOnlyFrom4_5To7_5_ChapterPlan4()
        {
            var e = new Evening();
            int both = 0;
            for (int k = 0; k < 840; k++)
            {
                Mech.Run(e.G, 1);
                double t = e.C.Phase;
                bool serves = e.Table >= 0.75 && e.Ledge >= 1 && e.Shutter <= 1.3;
                if (serves) both++;
                if (t >= 4.5 && t < 7.5) Assert.True(serves, "t " + t);
                if (t < 4.5 || t >= 7.5 + Dt) Assert.False(serves, "t " + t);
                if (t >= 0.5 && t < 2.5) Assert.Equal(0.3 + 0.45 * (t - 0.5) / 2, e.Table, 12);
                if (t >= 10 && t < 12) Assert.Equal(0.75 - 0.45 * (t - 10) / 2, e.Table, 12);
                if (t >= 2.5 && t < 4.5) Assert.Equal(1.85 - 0.55 * (t - 2.5) / 2, e.Shutter, 12);
                if (t >= 12) { Assert.Equal(0.3, e.Table); Assert.Equal(1.85, e.Shutter); Assert.Equal(0, e.Ledge); }
            }
            Assert.InRange(both * Dt, 3.0 - Dt, 3.0 + 2 * Dt);                     // 4.5 to 7.5: the window opens with the ledge
        }

        [Fact]
        public void Evening_BrakedAsBowl2Lands_HoldsTableShutterAndLedge_ReleaseResumes_DL21()
        {
            var e = new Evening();
            Mech.RunUntil(e.G, () => Of(e.G, "dl21.evening", CycleClockEvent.Cue).Exists(x => x.Index == e.C.CueIndex("bowl2Set")));
            e.Brake.Engaged = true;
            Mech.Run(e.G, 1);
            double t = e.C.Phase;
            Assert.Equal(CycleClockState.Braked, e.C.State);
            Mech.Run(e.G, 900);
            Assert.Equal(t, e.C.Phase);
            Assert.Equal(0.75, e.Table);
            Assert.Equal(1.3, e.Shutter);
            Assert.Equal(1, e.Ledge);
            e.Top.Engaged = true;                                               // braked, the table is a fixed step
            Mech.Run(e.G, 60);
            Assert.Equal(CycleClockState.Braked, e.C.State);
            e.Top.Engaged = false;
            e.Brake.Engaged = false;
            Mech.Run(e.G, 1);
            Assert.Equal(CycleClockState.Running, e.C.State);
            Assert.Equal(t + Dt, e.C.Phase, 12);                                 // resumes where it stopped
        }

        [Fact]
        public void Evening_BrakedTooEarly_TheShutterIsStillUp_DL21()
        {
            var e = new Evening();
            e.RunTo(2.6);
            e.Brake.Engaged = true;
            Mech.Run(e.G, 300);
            Assert.Equal(0.75, e.Table);
            Assert.True(e.Shutter > 1.8);
            Assert.Equal(0, e.Ledge);
        }

        [Fact]
        public void Evening_SomethingOnTheTableTop_ReversesToRest_RestartsFrom0OnceClearFor1s_DL21()
        {
            var e = new Evening();
            e.RunTo(6.0);
            e.Top.Engaged = true;
            Mech.Run(e.G, 1);
            Assert.Equal(1, Assert.Single(Of(e.G, "dl21.evening", CycleClockEvent.Stopped)).Index);
            Assert.Equal(CycleClockState.Returning, e.C.State);
            int home = Mech.RunUntil(e.G, () => e.C.State == CycleClockState.Off);
            Assert.InRange((home + 1) * Dt, 0, 4.5);                              // all home within 4.5 s
            Assert.InRange((home + 1) * Dt, 2.0 - Dt, 2.0 + 2 * Dt);              // the table and shutter take 2 s
            Assert.Equal(0.3, e.Table);
            Assert.Equal(1.85, e.Shutter);
            Mech.Run(e.G, 600);
            Assert.Equal(CycleClockState.Off, e.C.State);                         // waits while he stands there
            e.Top.Engaged = false;
            int n = Mech.RunUntil(e.G, () => e.C.On);
            Assert.Equal(60, n);                                                  // clear for 1 s
            Assert.Equal(1, Assert.Single(Of(e.G, "dl21.evening", CycleClockEvent.Started)).Index);
            Assert.Equal(Dt, e.C.Phase, 15);
        }

        [Fact]
        public void Evening_ClearingBeforeItIsHome_RestartsOnlyOnceHome_DL21()
        {
            var e = new Evening();
            e.RunTo(6.0);
            e.Top.Engaged = true;
            Mech.Run(e.G, 5);
            e.Top.Engaged = false;
            int n = Mech.RunUntil(e.G, () => e.C.On);
            Assert.InRange((n + 5) * Dt, 2.0 - Dt, 2.0 + 2 * Dt);                 // home first (2 s), then at once
        }

        [Fact]
        public void Evening_APlaceEmpties_StandsDownHome_ThenStartsAgainFrom0_DL21()
        {
            var e = new Evening();
            e.RunTo(6.0);
            e.Places.Engaged = false;
            Mech.Run(e.G, 1);
            Assert.Equal(0, Assert.Single(Of(e.G, "dl21.evening", CycleClockEvent.Stopped)).Index);
            Assert.Equal(1 - Dt / 0.3, e.Ledge, 12);                              // the ledge snaps up within 0.3 s
            Mech.Run(e.G, 18);
            Assert.Equal(0, e.Ledge);
            Mech.RunUntil(e.G, () => e.C.State == CycleClockState.Off);
            e.Places.Engaged = true;
            Mech.Run(e.G, 1);
            Assert.Single(Of(e.G, "dl21.evening", CycleClockEvent.Started));
            Assert.Single(Of(e.G, "dl21.evening", CycleClockEvent.Cue));          // the chime at 0
        }

        [Fact]
        public void Evening_BrakedWhenAPlaceEmpties_StandsDownOnRelease_ReleasedWithSomeoneOnTheTop_Reverses_DL21()
        {
            var e = new Evening();
            e.RunTo(5.2);
            e.Brake.Engaged = true;
            e.Places.Engaged = false;
            Mech.Run(e.G, 120);
            Assert.Equal(CycleClockState.Braked, e.C.State);
            e.Brake.Engaged = false;
            Mech.Run(e.G, 1);
            Assert.Equal(0, Assert.Single(Of(e.G, "dl21.evening", CycleClockEvent.Stopped)).Index);

            var f = new Evening();
            f.RunTo(5.2);
            f.Brake.Engaged = true;
            Mech.Run(f.G, 60);
            f.Top.Engaged = true;
            f.Brake.Engaged = false;
            Mech.Run(f.G, 1);
            Assert.Equal(1, Assert.Single(Of(f.G, "dl21.evening", CycleClockEvent.Stopped)).Index);
        }

        [Fact]
        public void Evening_RestoredWhileReversing_ContinuesBitIdentically()
        {
            var a = new Evening();
            a.RunTo(6.0);
            a.Top.Engaged = true;
            Mech.Run(a.G, 40);
            var b = new Evening(false);
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            for (int k = 0; k < 1200; k++)
            {
                if (k == 200) a.Top.Engaged = b.Top.Engaged = false;
                Mech.Run(a.G, 1);
                Mech.Run(b.G, 1);
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
                Assert.Equal(Mech.Events(a.G).Count, Mech.Events(b.G).Count);
            }
            Assert.True(b.C.On);
        }

        // ---- DL-23 held at a point (chapter 2 data) -------------------------------------------------------------------------

        [Fact]
        public void Serving_HoldsAt17_5WhileBothLampsAreLit_ThenGoesHomeWhenOneGoesOut_DL23()
        {
            var lamps = new TestSource("dl23.lamps") { Engaged = true };
            var top = new TestSource("dl23.tableTop");
            var c = new CycleClock("dl23.serving", CycleClockParams.Dl23Serving());
            var g = Mech.Graph(lamps, top, c);
            var cues = new List<int>();
            int held = Mech.RunUntil(g, () =>
            {
                foreach (var e in Of(g, "dl23.serving", CycleClockEvent.Cue)) cues.Add(e.Index);
                return c.State == CycleClockState.Held;
            });
            Assert.InRange(held * Dt, 17.5 - Dt, 17.5 + Dt);
            Assert.Equal(new[] { 0, 1, 2, 3, 4, 5, 6, 7 }, cues);                 // served (17.5) fires on the hold step
            Assert.Equal(17.5, c.Phase);
            Assert.Equal(0.75, c.Value(0));
            top.Engaged = true;                                                   // held, the table is a fixed step
            Mech.Run(g, 600);
            Assert.Equal(CycleClockState.Held, c.State);
            Assert.Empty(Of(g, "dl23.serving", CycleClockEvent.Cue));
            top.Engaged = false;
            lamps.Engaged = false;
            int home = Mech.RunUntil(g, () => c.State == CycleClockState.Off);
            Assert.InRange((home + 1) * Dt, 2.0 - Dt, 2.0 + Dt);
            lamps.Engaged = true;
            Mech.Run(g, 1);
            Assert.Single(Of(g, "dl23.serving", CycleClockEvent.Started));
        }

        // ---- Determinism ----------------------------------------------------------------------------------------------------

        [Fact]
        public void TwoRuns_WithTheSameInputs_AreBitIdentical()
        {
            var runs = new List<string>[2];
            for (int r = 0; r < 2; r++)
            {
                var e = new Evening();
                var l = new Lesson();
                runs[r] = new List<string>();
                for (int k = 0; k < 3000; k++)
                {
                    e.Top.Engaged = k % 700 > 600;
                    e.Brake.Engaged = k > 2000 && k < 2300;
                    l.Seat.Engaged = k % 1000 < 800;
                    Mech.Run(e.G, 1);
                    Mech.Run(l.G, 1);
                    runs[r].Add(Mech.Dump(e.G) + "#" + Mech.Dump(l.G));
                }
            }
            Assert.Equal(runs[0], runs[1]);
        }
    }
}
