using System;
using System.Collections.Generic;
using DeadLetter.Core.Beings;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-14b's escort trolley (§4.16; L5897–L5900, L5917, L6127–L6134, L6352–L6421). The escorted walk is the real motor's
    /// act (<see cref="IEscort"/>): the rig starts it as the pipeline does, after the graph step.
    /// </summary>
    public class EscortTrolleyTests
    {
        private const double Dt = Mech.Dt;
        private const string Id = "dl14b.trolley";
        private const string Fig = "dl14b.figure";

        /// <summary>A stand-in for the figure: settable, and follows the trolley while it is held (one step behind).</summary>
        private sealed class TestFigure : Mechanism, IDecoy
        {
            private IDecoyEscort _t;
            public TestFigure() : base(Fig) { }
            public double DecoyX { get; set; } = 269.9;
            public bool DecoyInView { get; set; }
            public override void Link(MechanismLinker link) => _t = link.ReadAnyOrder<IDecoyEscort>(EscortTrolleyTests.Id);
            public override void Reset(in Checkpoint cp) { }
            public override void Step(in StepContext ctx)
            {
                if (_t.HoldsDecoy) { DecoyX = _t.DecoyX; DecoyInView = false; }
            }
            protected override void WriteFields(ISnapshotWriter w) { w.WriteDouble("x", DecoyX); w.WriteBool("in", DecoyInView); }
            protected override void ReadFields(ISnapshotReader r) { DecoyX = r.ReadDouble("x"); DecoyInView = r.ReadBool("in"); }
        }

        private sealed class Rig
        {
            public readonly BeingSenses S = new BeingSenses { Region = 6 };
            public readonly TestFigure F = new TestFigure();
            public readonly EscortTrolley T;
            public readonly MechanismGraph G;
            /// <summary>The motor walks him while he is escorted; otherwise his pose is the fields below.</summary>
            public readonly D17Motor M = Sim.Make(BoxWorld.Flat(200, 300));
            public double X = 250, Y, Z;
            public bool Hiding, Driven;
            public readonly List<MechanismEvent> Log = new List<MechanismEvent>();

            public Rig(string cp = "corridor", ulong seed = 0)
            {
                var p = EscortTrolleyParams.Dl14b(Fig);
                if (seed != 0) p.Seed = seed;
                T = new EscortTrolley(Id, p, S);
                G = Mech.Graph(cp, F, T);
            }

            /// <summary>His x: the motor's while it walks him, else the field.</summary>
            public double HeroX => Driven ? M.X : X;

            public void Step()
            {
                S.BeginStep();
                if (Driven) { M.Step(MotorInput.None, Dt); G.Step(Dt, PlayerPose.Of(M)); }      // #4, then #6–#7
                else G.Step(Dt, new PlayerPose(X, Y, Z, hiding: Hiding));
                Log.AddRange(Mech.Events(G));
                if (Driven && !M.IsEscorted) { Driven = false; X = M.X; }
                if (T.WantsEscort && !M.IsEscorted)                                                // the pipeline's escort hook
                {
                    M.Place(X, 0);
                    M.BeginEscort(T.Walk);
                    Driven = true;
                }
            }

            /// <summary>One step seen with someone else's pose (a restored copy follows the original's motor).</summary>
            public void StepWith(in PlayerPose pose)
            {
                S.BeginStep();
                G.Step(Dt, pose);
                Log.AddRange(Mech.Events(G));
            }

            public void Run(int n) { for (int i = 0; i < n; i++) Step(); }

            public int Until(Func<bool> cond, int max = 5000)
            {
                for (int i = 1; i <= max; i++) { Step(); if (cond()) return i; }
                return -1;
            }

            public bool Entered(EscortState s) => Mech.Entered(G, Id, s);
            public bool Emitted(EscortEvent e) => Mech.Emitted(G, Id, e);
        }

        [Fact]
        public void Patrol_RollsAt11_PausesAndTurns12s_AtEachEnd_L6370_L6380()
        {
            var r = new Rig();
            Assert.Equal(EscortState.Patrol, r.T.State);
            Assert.Equal(270.0, r.T.X);
            r.Step();
            Assert.Equal(270.0 + 1.1 * Dt, r.T.X, 12);
            int k = r.Until(() => r.T.State == EscortState.Turn);
            Assert.InRange(k + 1, 267, 268);                                   // 4.9 m at 1.1 m/s = 4.45 s
            Assert.Equal(274.9, r.T.X);
            Assert.Equal(0, r.T.Facing01);
            r.Run(36);
            Assert.InRange(r.T.Facing01, 0.45, 0.55);                          // half-way round at 0.6 s
            int pause = r.Until(() => r.T.State == EscortState.Patrol) + 36;
            Assert.InRange(pause, 72, 73);                                     // > 1.2 s
            Assert.True(r.Emitted(EscortEvent.Turned));
            Assert.Equal(-1, r.T.Dir);
            Assert.Equal(1, r.T.Facing01);
            int back = r.Until(() => r.T.State == EscortState.Turn);
            Assert.InRange(back, 539, 541);                                    // 9.9 m in 9 s
            Assert.Equal(265.0, r.T.X);
        }

        [Fact]
        public void Beam_Covers26m_Starting035Ahead_L6354_L6357()
        {
            var r = new Rig();
            Assert.Equal(270.35, r.T.BeamLo, 12);
            Assert.Equal(272.95, r.T.BeamHi, 12);
            r.Until(() => r.T.Dir < 0);
            Assert.Equal(r.T.X - 0.35 - 2.6, r.T.BeamLo, 12);
            Assert.Equal(r.T.X - 0.35, r.T.BeamHi, 12);
        }

        [Fact]
        public void SeeingHim_WalksHimBackToTheDoor_ThenStops2s_L6397_L6403_L6127_L6134()
        {
            var r = new Rig { X = 271.0 };
            r.Step();
            Assert.True(r.Entered(EscortState.EscortHim));
            Assert.True(r.Emitted(EscortEvent.CaughtHim));
            Assert.True(r.T.HeroHeld);
            Assert.True(r.M.IsEscorted);                                       // the motor's escorted act (#22)
            Assert.Equal(271.0, r.HeroX);
            int hold = r.Until(() => r.HeroX < 271.0, 100);
            Assert.InRange(hold, 42, 43);                                      // he stands 0.7 s first
            Assert.Equal(r.HeroX + 0.75, r.T.X, 9);                            // then it is 0.75 behind him (it jumps there, L6132)
            Assert.Equal(-1, r.M.Facing);
            Assert.Equal(ClipNames.Walk, r.M.Clip);
            int walked = 0;
            while (r.T.HeroHeld && walked++ < 2000)
            {
                double h = r.HeroX;
                r.Step();
                if (r.T.HeroHeld)
                {
                    Assert.Equal(h - 0.8 * Dt, r.HeroX, 9);
                    Assert.InRange(r.T.X - r.HeroX, 0.75 - 1e-9, 0.9 + 1e-9);
                }
            }
            Assert.InRange(walked, (int)(7.55 / 0.8 * 60) - 1, (int)(7.55 / 0.8 * 60) + 2);
            Assert.True(r.Emitted(EscortEvent.HimHome));
            Assert.True(r.Entered(EscortState.Stop));
            Assert.InRange(r.HeroX, 263.45, 263.46);                            // the act ends at ≤ 263.46 (L6133)
            Assert.False(r.M.IsActing);
            Assert.Equal(+1, r.M.Facing);                                      // then he faces +x
            r.X = 263.45;
            Assert.InRange(r.Until(() => r.T.State == EscortState.Patrol), 119, 120);   // 2 s
            Assert.Equal(1, r.T.Dir);
        }

        [Theory]
        [InlineData(271.0, 0.0, 0.0, false, 6, true)]
        [InlineData(271.0, 0.0, 0.62, true, 6, false)]   // tucked into the bay
        [InlineData(271.0, 0.0, 0.3, true, 6, true)]     // hiding, but not yet stepped back
        [InlineData(271.0, 1.25, 0.0, false, 6, false)]  // up high
        [InlineData(271.0, 0.0, 0.0, false, 5, false)]   // another region
        [InlineData(273.0, 0.0, 0.0, false, 6, false)]   // past the beam's end
        [InlineData(270.3, 0.0, 0.0, false, 6, false)]   // behind the lamp
        public void Sees_HimInTheBeam_NotHiddenNorHigh_L6364_L6368_L5973(double x, double y, double z, bool hiding, int region, bool seen)
        {
            var r = new Rig { X = x, Y = y, Z = z };
            r.Hiding = hiding; r.S.Region = region;
            r.Step();
            Assert.Equal(seen, r.T.State == EscortState.EscortHim);
        }

        [Fact]
        public void NeverSeesThroughTheDormitoryWall_L6367()
        {
            var r = new Rig();
            r.Until(() => r.T.Dir < 0 && r.T.X < 265.3);
            r.X = 263.05;                                                       // inside the beam, but behind the wall line
            r.Until(() => r.T.State == EscortState.Turn);
            r.Run(30);
            Assert.Equal(EscortState.Turn, r.T.State);                         // still looking toward −x
            Assert.InRange(263.05, r.T.BeamLo, r.T.BeamHi);
            Assert.DoesNotContain(r.Log, e => e.Kind == MechanismEventKind.State && e.Code == (int)EscortState.EscortHim);
            r.X = 263.15;
            r.Step();
            Assert.Equal(EscortState.EscortHim, r.T.State);
        }

        [Fact]
        public void NotInPlay_HeIsNotSeen_AndAnEscortCutShortStops2s_L6366_L6421()
        {
            var r = new Rig { X = 271.0 };
            r.S.Alive = false;
            r.Run(10);
            Assert.Equal(EscortState.Patrol, r.T.State);
            r.S.Alive = true; r.X = r.T.X + 1;
            r.Step();
            Assert.Equal(EscortState.EscortHim, r.T.State);
            r.Run(10);
            r.S.Alive = false;
            r.Step();
            Assert.True(r.Entered(EscortState.Stop));
            Assert.False(r.T.HeroHeld);
            Assert.InRange(r.Until(() => r.T.State == EscortState.Patrol), 120, 121);
        }

        [Fact]
        public void TheFigure_IsEscortedTo2622_ThenItWaits6s_TheWindow_L6381_L6388_L6405()
        {
            var r = new Rig();
            r.F.DecoyX = 272.0; r.F.DecoyInView = true;
            r.Step();
            Assert.True(r.Entered(EscortState.EscortFigure));
            Assert.True(r.Emitted(EscortEvent.FigureSeen));
            Assert.Equal(-1, r.T.Dir);
            Assert.True(r.T.HoldsDecoy);
            double x0 = r.T.X;
            int wait = r.Until(() => r.T.X != x0, 100);
            Assert.InRange(wait, 48, 49);                                      // 0.8 s
            Assert.Equal(r.T.DecoyX + 0.65, r.T.X, 12);
            int push = r.Until(() => r.T.State != EscortState.EscortFigure, 2000);
            Assert.InRange(push + 1, (int)(9.8 / 0.8 * 60) - 1, (int)(9.8 / 0.8 * 60) + 2);
            Assert.True(r.Emitted(EscortEvent.FigureKept));
            Assert.Equal(EscortState.Stop, r.T.State);
            Assert.True(r.T.DecoyKept);
            Assert.Equal(262.2, r.T.DecoyX, 3);
            r.Step();
            Assert.Equal(262.2, r.F.DecoyX, 3);                                // the figure follows it
            Assert.InRange(r.Until(() => r.T.State == EscortState.Patrol), 359, 360);   // 6 s
            r.F.DecoyInView = true;                                            // kept: never seen again
            r.Run(600);
            Assert.DoesNotContain(r.Log, e => e.Kind == MechanismEventKind.State && e.Code == (int)EscortState.EscortFigure && e.Tick > 1);
        }

        [Theory]
        [InlineData(272.5, 271.0, EscortState.EscortFigure)]   // the nearer wins
        [InlineData(271.0, 272.5, EscortState.EscortHim)]
        [InlineData(271.5, 271.5, EscortState.EscortFigure)]   // a tie goes to the figure
        public void HimOrTheFigure_TheNearerWins_L6394_L6396(double him, double fig, EscortState expected)
        {
            var r = new Rig { X = him };
            r.F.DecoyX = fig; r.F.DecoyInView = true;
            r.Run(2);
            Assert.Equal(expected, r.T.State);
        }

        [Theory]
        [InlineData("dorm", false)]
        [InlineData("corridor", false)]
        [InlineData("sickbay", true)]
        [InlineData("workshop", true)]
        public void Reset_FromCheckpoint_PatrolsFrom270_TheFigureKeptPastTheSickBay_L5917(string cp, bool kept)
        {
            var r = new Rig("corridor") { X = 271 };
            r.Run(30);
            r.G.Reset(Mech.Cp(cp));
            Assert.Equal(EscortState.Patrol, r.T.State);
            Assert.Equal(270.0, r.T.X);
            Assert.Equal(1, r.T.Dir);
            Assert.False(r.T.HeroHeld);
            Assert.False(r.T.HoldsDecoy);
            Assert.Equal(kept, r.T.DecoyKept);
            if (kept) Assert.Equal(262.2, r.T.DecoyX);
        }

        [Fact]
        public void SnapshotMidPatrol_RestoresAndContinuesBitIdentically()
        {
            var a = new Rig { X = 250 };
            a.Run(700);
            var b = new Rig("sickbay");
            b.Run(13);
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            for (int k = 0; k < 600; k++)
            {
                a.Step(); b.StepWith(new PlayerPose(a.X, a.Y, a.Z));
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
                Assert.Equal(Mech.Events(a.G).Count, Mech.Events(b.G).Count);
            }
        }

        /// <summary>
        /// A checkpoint taken mid-escort: the motor that walks him is not in the snapshot, so a reload must not start the
        /// escort over (#25 review). The restored trolley has let him go and stops 2 s where it was, as a cut act does.
        /// </summary>
        [Fact]
        public void SnapshotMidEscort_ReloadDoesNotRestartTheEscort_ItStops2sWhereItWas()
        {
            var a = new Rig { X = 250 };
            a.Run(700);
            a.X = a.T.X + (a.T.Dir > 0 ? 1.5 : -1.5);
            a.Until(() => a.T.HeroHeld, 10);
            a.Run(100);
            Assert.Equal(EscortState.EscortHim, a.T.State);
            Assert.True(a.Driven);

            var b = new Rig("sickbay") { X = a.M.X };                      // reloaded: he is placed where he stood
            b.Run(13);
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.False(b.T.HeroHeld);
            Assert.False(b.T.WantsEscort);
            Assert.Equal(EscortState.Stop, b.T.State);
            Assert.Equal(a.T.X, b.T.X);
            Assert.Equal(a.T.Dir, b.T.Dir);
            b.Log.Clear();
            for (int k = 0; k < 110; k++)
            {
                b.Step();
                Assert.False(b.Driven);                                        // the motor never begins an escort
                Assert.False(b.M.IsEscorted);
            }
            Assert.Equal(EscortState.Stop, b.T.State);
            Assert.DoesNotContain(b.Log, e => e.Kind == MechanismEventKind.Event && e.Code == (int)EscortEvent.CaughtHim);
            Assert.DoesNotContain(b.Log, e => e.Kind == MechanismEventKind.Event && e.Code == (int)EscortEvent.HimHome);
            Assert.InRange(b.Until(() => b.T.State == EscortState.Patrol), 10, 11);   // B.stopFor 2 s (120 steps)
        }

        [Fact]
        public void TwoRuns_WithTheSameSeed_AreBitIdentical_SqueaksIncluded()
        {
            var traces = new List<string>[2];
            string squeaks = null;
            for (int run = 0; run < 2; run++)
            {
                var r = new Rig();
                var trace = traces[run] = new List<string>();
                for (int i = 0; i < 2400; i++)
                {
                    if (i == 900) { r.F.DecoyX = r.T.X + r.T.Dir * 1.0; r.F.DecoyInView = true; }
                    r.Step();
                    trace.Add(Mech.Dump(r.G) + string.Join(",", Mech.Events(r.G)));
                }
                squeaks = Squeaks(r);
            }
            Assert.Equal(traces[0], traces[1]);
            Assert.InRange(squeaks.Split(',').Length, 30, 150);                // ~2.5/s rolling, 3/s pushing
            var other = new Rig(seed: 99);
            other.Run(2400);
            Assert.NotEqual(squeaks, Squeaks(other));                          // the seed is the only source of chance
        }

        private static string Squeaks(Rig r)
        {
            var ticks = new List<long>();
            foreach (var e in r.Log) if (e.Kind == MechanismEventKind.Event && e.Code == (int)EscortEvent.Squeak) ticks.Add(e.Tick);
            return string.Join(",", ticks);
        }
    }
}
