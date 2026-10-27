using System;
using System.Collections.Generic;
using DeadLetter.Core.Camera;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Motor;
using Xunit;

namespace DeadLetter.Core.Tests
{
    public sealed class FakeMusicClock : IMusicClock
    {
        public double Now { get; set; }
        public bool Running { get; set; } = true;
        public double OutputLatency { get; set; }
    }

    public class CueClockTests
    {
        private const double Dt = 1.0 / 60.0;

        /// <summary>Drives a moment at 60 Hz with the audio clock advancing in step (when running).</summary>
        private sealed class Harness
        {
            public readonly FakeMusicClock Music = new FakeMusicClock { Now = 100.0 };
            public readonly MomentDirector Director;
            public double Sim = 5.0;

            public Harness(double latency = 0.0)
            {
                Music.OutputLatency = latency;
                Director = new MomentDirector(Music);
            }

            public void Start(DirectedMoment m)
            {
                Director.Start(m, Sim, musicAvailable: true);
                Director.Clock.Scheduled(Music.Now + CueClock.ScheduleLeadIn);
            }

            public double? Step(MotorInput input, out MotorInput gated, bool actReady = true)
            {
                Sim += Dt;
                if (Music.Running) Music.Now += Dt;
                gated = Director.GateInput(input, Sim, actReady);
                return Director.Time(Sim);
            }
        }

        private static readonly MotorInput Right = new MotorInput { Move = 1 };

        public static IEnumerable<object[]> ControlMoments()
        {
            yield return new object[] { "kin", 22.5 };
            yield return new object[] { "refuge", 16.6 };   // the awe act lets go at release + 0.6 (L3390)
            yield return new object[] { "ringc", 22.0 };
        }

        [Fact]
        public void Moments_HaveThePrototypeTimes()
        {
            Assert.Equal((19.0, 21.0, 22.5), (PrologueMoments.Kin.Lock, PrologueMoments.Kin.Release, PrologueMoments.Kin.Control));
            Assert.Equal((14.0, 16.0, 18.5), (PrologueMoments.Refuge.Lock, PrologueMoments.Refuge.Release, PrologueMoments.Refuge.Control));
            Assert.Equal((16.0, 20.0, 22.0), (PrologueMoments.RingC.Lock, PrologueMoments.RingC.Release, PrologueMoments.RingC.Control));
            Assert.Equal((99.0, 13.6, 99.0), (PrologueMoments.Window.Lock, PrologueMoments.Window.Release, PrologueMoments.Window.Control));
        }

        [Theory]
        [MemberData(nameof(ControlMoments))]
        public void WithoutInput_ControlReturnsOnTheFirstStepAtTheControlTime(string name, double freeAt)
        {
            DirectedMoment m = PrologueMoments.Find(name);
            Assert.Equal(freeAt, m.FreeAt, 12);
            var h = new Harness();
            h.Start(m);
            double? prev = 0;
            while (true)
            {
                double? t = h.Step(Right, out MotorInput gated);   // holding right before lock does nothing
                Assert.NotNull(t);
                if (t < m.Lock) Assert.False(h.Director.Cut);
                if (h.Director.ControlReturned && t >= m.Lock)
                {
                    // Input after lock cuts: this is the lock step, not the control step.
                    Assert.True(t >= m.Lock && prev < m.Lock, "cut at " + t);
                    Assert.True(h.Director.Cut);
                    break;
                }
                Assert.Equal(MotorInput.None.Move, gated.Move);
                prev = t;
            }

            // Again without touching the controls: control comes back on the first step at or after FreeAt.
            h = new Harness();
            h.Start(m);
            prev = 0;
            while (true)
            {
                double? t = h.Step(MotorInput.None, out _);
                if (h.Director.ControlReturned)
                {
                    Assert.True(t >= freeAt && prev < freeAt, "freed at " + t);
                    Assert.False(h.Director.Cut);
                    break;
                }
                Assert.Equal(t >= m.Lock ? MomentControl.Cuttable : MomentControl.Locked, h.Director.ControlAt(t));
                prev = t;
            }
            h.Step(Right, out MotorInput after);
            Assert.Equal(1.0, after.Move);   // raw input passes from the next step
            Assert.Equal(MomentControl.Player, h.Director.ControlAt(h.Director.Time(h.Sim)));
        }

        [Theory]
        [InlineData("kin")]
        [InlineData("refuge")]
        [InlineData("ringc")]
        [InlineData("window")]
        public void Shot_AndVoices_HoldUntilRelease(string name)
        {
            DirectedMoment m = PrologueMoments.Find(name);
            var h = new Harness();
            h.Start(m);
            double? t;
            do
            {
                t = h.Step(MotorInput.None, out _);
                bool before = t < m.Release;
                Assert.Equal(before, h.Director.ShotTime(name, h.Sim) != null);
                Assert.Equal(before, h.Director.VoicesHeld(h.Sim));
            } while (t < m.Release + 0.1);
        }

        [Fact]
        public void Cut_EndsTheShotAtOnce()
        {
            var h = new Harness();
            h.Start(PrologueMoments.Kin);
            double? t;
            do t = h.Step(MotorInput.None, out _); while (t < 19.5);
            Assert.NotNull(h.Director.ShotTime("kin", h.Sim));
            h.Step(new MotorInput { JumpPressed = true }, out _);
            Assert.True(h.Director.Cut && h.Director.ControlReturned);
            Assert.Null(h.Director.ShotTime("kin", h.Sim));
        }

        [Fact]
        public void Window_NeverFrees_TheEndingOwnsHim()
        {
            var h = new Harness();
            h.Start(PrologueMoments.Window);
            for (int n = 0; n < 60 * 40; n++)
            {
                h.Step(Right, out MotorInput gated);
                Assert.False(h.Director.ControlReturned);
                Assert.Equal(0.0, gated.Move);
            }
            Assert.False(PrologueMoments.Window.ReturnsControl);
        }

        [Fact]
        public void Time_IsHeardTime_FromTheScheduledStart_LessLatency()
        {
            var a = new Harness(latency: 0.0);
            var b = new Harness(latency: 0.045);
            a.Start(PrologueMoments.Refuge); b.Start(PrologueMoments.Refuge);
            double? ta = null, tb = null;
            for (int n = 0; n < 600; n++) { ta = a.Step(MotorInput.None, out _); tb = b.Step(MotorInput.None, out _); }
            // 600 steps = 10 s of audio; the cue started 0.1 s after the trigger.
            Assert.Equal(10.0 - CueClock.ScheduleLeadIn, ta.Value, 9);
            Assert.Equal(ta.Value - 0.045, tb.Value, 9);
            // Before the scheduled start the clock stays at 0 (never negative, never backwards).
            var c = new Harness(latency: 0.045);
            c.Start(PrologueMoments.Kin);
            Assert.Equal(0.0, c.Step(MotorInput.None, out _).Value);
        }

        [Fact]
        public void Latency_DelaysControlReturn_ByTheLatency()
        {
            double ReturnSim(double latency)
            {
                var h = new Harness(latency);
                h.Start(PrologueMoments.RingC);
                while (true) { h.Step(MotorInput.None, out _); if (h.Director.ControlReturned) return h.Sim - 5.0; }
            }
            double a = ReturnSim(0), b = ReturnSim(0.05);
            // 22.0 s of heard cue + 0.1 s lead-in (+ latency), quantised to 60 Hz steps.
            Assert.InRange(a, 22.1, 22.1 + Dt + 1e-9);
            Assert.InRange(b, 22.15, 22.15 + Dt + 1e-9);
        }

        [Fact]
        public void Paused_FreezesTheClock_ThenItCarriesOn()
        {
            var h = new Harness();
            h.Start(PrologueMoments.Kin);
            for (int n = 0; n < 300; n++) h.Step(MotorInput.None, out _);
            double frozen = h.Director.Time(h.Sim).Value;
            h.Music.Running = false;
            for (int n = 0; n < 90; n++) Assert.Equal(frozen, h.Step(MotorInput.None, out _).Value);   // 1.5 s < 2.0 s
            h.Music.Running = true;
            double? t = h.Step(MotorInput.None, out _);
            Assert.Equal(frozen + Dt, t.Value, 9);
            Assert.False(h.Director.Clock.Fallback);
        }

        [Fact]
        public void End_MidHold_LetsRawInputThroughOnTheNextStep()
        {
            var h = new Harness();
            h.Start(PrologueMoments.Kin);
            double? t;
            do
            {
                t = h.Step(Right, out MotorInput gated);
                Assert.Equal(0.0, gated.Move);
            } while (t < 5.0);   // well before lock: input is held
            Assert.True(h.Director.Holding);

            h.Director.End();   // checkpoint reset mid-hold
            Assert.Null(h.Step(Right, out MotorInput after));
            Assert.Equal(1.0, after.Move);
            Assert.False(h.Director.Holding);
            Assert.False(h.Director.ControlReturned);
            Assert.Equal(MomentControl.Player, h.Director.ControlAt(h.Director.Time(h.Sim)));
            Assert.False(h.Director.VoicesHeld(h.Sim));
        }

        [Fact]
        public void MusicClock_SeekingBackwards_HoldsTheTimeUntilItCatchesUp()
        {
            var h = new Harness();
            h.Start(PrologueMoments.Kin);
            for (int n = 0; n < 300; n++) h.Step(MotorInput.None, out _);
            double held = h.Director.Time(h.Sim).Value;
            h.Music.Now -= 0.5;   // the audio clock jumps back half a second (Math.max in momentTime, L926)
            int heldSteps = 0;
            double? t;
            while ((t = h.Step(MotorInput.None, out _)).Value == held) heldSteps++;
            // It sat on the old time while the clock re-covered the 0.5 s, then carried on from the clock, never backwards.
            Assert.InRange(heldSteps, 29, 30);
            Assert.True(t.Value > held && t.Value - held <= Dt + 1e-9, "resumed at " + t);
            Assert.False(h.Director.Clock.Fallback);
        }

        [Fact]
        public void LongPause_WithTheSimFrozen_DoesNotAdvanceTheMoment()
        {
            var h = new Harness();
            h.Start(PrologueMoments.Kin);
            for (int n = 0; n < 300; n++) h.Step(MotorInput.None, out _);
            double frozen = h.Director.Time(h.Sim).Value;
            double music = h.Music.Now;
            // Pause card open for 5 s of wall time: the sim does not step and the paused music clock stands still.
            h.Music.Running = false;
            for (int n = 0; n < 300; n++)
            {
                Assert.Equal(frozen, h.Director.Time(h.Sim).Value);
                Assert.Equal(0.0, h.Director.GateInput(Right, h.Sim).Move);
            }
            Assert.False(h.Director.Clock.Fallback);   // the 2.0 s stall limit is on the sim clock, which did not move
            // Unpause: the clock comes back where it stopped (the paused span removed) and the moment carries on.
            h.Music.Running = true;
            Assert.Equal(music, h.Music.Now);
            Assert.Equal(frozen + Dt, h.Step(MotorInput.None, out _).Value, 9);
            Assert.False(h.Director.Clock.Fallback);
            Assert.True(h.Director.Holding);
        }

        [Fact]
        public void Fallbacks_RunOnTheSimClock()
        {
            // Suspended audio before the cue starts, for more than 0.6 s: the sim clock takes over from where it stood (L918).
            var music = new FakeMusicClock { Now = 10, Running = false };
            var clock = new CueClock(music);
            clock.Begin("kin", 0, musicAvailable: true);
            Assert.Equal(0.0, clock.Time("kin", 0.5).Value);
            Assert.Equal(0.0, clock.Time("kin", 0.7).Value, 12);
            Assert.True(clock.Fallback);
            Assert.Equal(0.5, clock.Time("kin", 1.2).Value, 12);
            // Stalled for more than 2.0 s after starting: sim clock from where it stood.
            music = new FakeMusicClock { Now = 10, Running = true };
            clock = new CueClock(music);
            clock.Begin("ringc", 0, true);
            clock.Scheduled(10);
            music.Now = 13; Assert.Equal(3.0, clock.Time("ringc", 3).Value, 12);
            music.Running = false;
            Assert.Equal(3.0, clock.Time("ringc", 4.9).Value, 12);
            Assert.Equal(3.0, clock.Time("ringc", 5.1).Value, 12);   // falls back at 5.1 (> 2.0 s since last heard)
            Assert.Equal(3.5, clock.Time("ringc", 5.6).Value, 12);
            // No music at all (headless replay): the sim clock from the trigger.
            clock = new CueClock(null);
            clock.Begin("window", 2.0, true);
            Assert.Equal(1.25, clock.Time("window", 3.25).Value, 12);
            Assert.Null(clock.Time("kin", 3.25));
        }

        [Fact]
        public void RingCLight_IsFullOnThePeak_AndOffAfter()
        {
            Assert.Equal(0, MomentShots.RingCLight(9.5, null), 12);
            Assert.Equal(2.6, MomentShots.RingCLight(12.0, null), 12);
            Assert.Equal(2.6, MomentShots.RingCLight(20.0, null), 12);
            Assert.Equal(0, MomentShots.RingCLight(21.5, null), 12);
            Assert.Equal(0, MomentShots.RingCLight(17.5, 16.0), 12);   // freed at 16: off over 1.5 s
        }

        [Fact]
        public void MomentShots_LandOnTheirPeaks()
        {
            // kin: the wide at 15 (REALISE_KEYS, L3692).
            ShotRequest k = MomentShots.Kin(31, 15);
            Assert.Equal(new Maths.Vec3(31 - 0.7, 3.6, 4.6), k.Position);
            Assert.Equal(22, k.Focal, 12);
            // refuge: the widest frame at 10 (L3789–L3792).
            ShotRequest r = MomentShots.Refuge(113.3, 1.6, 10);
            Assert.Equal(24, r.Focal, 12);
            Assert.Equal(MomentShots.Atrium, r.Look);
            // ringc: the lane by 9 (L3719).
            Assert.Equal("ringc10", MomentShots.RingC(128.2, 0, 9, 3).Name);
            Assert.Equal(22, MomentShots.RingC(128.2, 0, 9, 3).Focal, 12);
            // window: on the window at 6.5, back by 13.5 (L3749).
            Assert.Equal(38, MomentShots.Window(173.2, 0, 6.5, 6.5).Focal, 12);
            Assert.Equal(28, MomentShots.Window(173.2, 0, 13.5, 13.5).Focal, 12);
        }

        [Fact]
        public void Director_IsDeterministic()
        {
            List<double> Run()
            {
                var h = new Harness(0.03);
                var trace = new List<double>();
                h.Start(PrologueMoments.Kin);
                for (int n = 0; n < 60 * 25; n++)
                {
                    if (n == 400) h.Music.Running = false;
                    if (n == 460) h.Music.Running = true;
                    double? t = h.Step(n == 1250 ? Right : MotorInput.None, out MotorInput g);
                    trace.Add(t ?? -1); trace.Add(g.Move); trace.Add(h.Director.ControlReturned ? 1 : 0);
                }
                return trace;
            }
            Assert.Equal(Run(), Run());
        }

        // ---- Skip (#22): jump to the moment's control-return state ---------------------------------------------------

        [Fact]
        public void Skip_BeforeLock_ReleasesTheHold_ReportsControlOnTheNextGate_ShotLetsGo_CuePlaysOn_L8071()
        {
            var h = new Harness();
            h.Start(PrologueMoments.Kin);
            for (int i = 0; i < 120; i++) h.Step(Right, out _);                       // 2 s in: locked
            Assert.Equal(MomentControl.Locked, h.Director.ControlAt(h.Director.Time(h.Sim)));
            Assert.True(h.Director.VoicesHeld(h.Sim));
            double t = h.Director.Time(h.Sim).Value;
            Assert.True(h.Director.Skip(h.Sim));
            Assert.False(h.Director.Skip(h.Sim));                                       // control is already back
            Assert.True(h.Director.Skipped && h.Director.Cut);
            Assert.False(h.Director.Holding);
            Assert.Equal(t, h.Director.ReturnedAt.Value, 9);
            Assert.Null(h.Director.ShotTime("kin", h.Sim));                             // the shot lets go
            Assert.False(h.Director.VoicesHeld(h.Sim));                                 // voices may play again
            Assert.Equal(MomentControl.Player, h.Director.ControlAt(h.Director.Time(h.Sim)));

            h.Step(Right, out var gated);                                               // reported once, that input consumed
            Assert.True(h.Director.ControlReturned);
            Assert.Equal(0.0, gated.Move);
            h.Step(Right, out gated);
            Assert.False(h.Director.ControlReturned);
            Assert.Equal(1.0, gated.Move);
            Assert.Same(PrologueMoments.Kin, h.Director.Current);                       // its cue plays on (startPlay, L8086)
            Assert.True(h.Director.Time(h.Sim) > t);
        }

        [Fact]
        public void Skip_WithNoMoment_DoesNothing()
        {
            var h = new Harness();
            Assert.False(h.Director.Skip(h.Sim));
            h.Step(Right, out var gated);
            Assert.False(h.Director.ControlReturned);
            Assert.Equal(1.0, gated.Move);
        }
    }
}
