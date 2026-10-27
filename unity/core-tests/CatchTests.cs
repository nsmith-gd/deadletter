using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Save;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>Latches, pawls, catches and brakes (§4.13c).</summary>
    public class CatchTests
    {
        private static InteractionQuery At(double x, double y = 0) => new InteractionQuery(x, y, 0, 1, true, false, HoldKind.None, null, null);

        // ---- Latch ----------------------------------------------------------------------------------------------------------

        [Fact]
        public void Latch_ReleasesOnTheStepPullPassesF31_L1874()
        {
            var latch = new Latch("dl01.latch", LatchParams.Dl01Latch());
            var g = Mech.Graph(latch);
            double releasedAt = -1;
            Mech.PlayAct(g, latch, onStep: (k, f) =>
            {
                if (Mech.Entered(g, "dl01.latch", LatchState.Released)) releasedAt = f;
                if (f < 31 - 1e-6) Assert.Equal(LatchState.Locked, latch.State);
            });
            Assert.InRange(releasedAt, 31 - 1e-6, 31.4);
            Assert.True(latch.Engaged);
        }

        [Fact]
        public void Latch_ActEndsAtF39_ThenFlinch_L1875()
        {
            var latch = new Latch("dl01.latch", LatchParams.Dl01Latch());
            var g = Mech.Graph(latch);
            int steps = Mech.PlayAct(g, latch);
            Assert.InRange(steps * Mech.FramesPerStep, 39 - 1e-6, 39.4);
            Assert.Equal("Pull", latch.Profile.Clip);
            Assert.True(latch.Profile.Crouch);
        }

        [Theory]
        [InlineData(0, 0)] [InlineData(12, 0)] [InlineData(20, 12)] [InlineData(24, 8)] [InlineData(30, 22)] [InlineData(33, 70)] [InlineData(40, 72)] [InlineData(55, 72)]
        public void Latch_LeverFollowsThePullKeys_L1645(double frame, double deg)
        {
            Assert.Equal(deg, Latch.LeverAngleAt(frame), 9);
        }

        [Fact]
        public void Latch_LeverAndCreak_FollowTheClip_L1872_L1873()
        {
            var latch = new Latch("dl01.latch", LatchParams.Dl01Latch());
            var g = Mech.Graph(latch);
            int creaks = 0;
            Mech.PlayAct(g, latch, onStep: (k, f) =>
            {
                Assert.Equal(Latch.LeverAngleAt(Math.Min(f, 40)), latch.LeverDeg, 12);
                if (Mech.Emitted(g, "dl01.latch", LatchEvent.Creak)) { creaks++; Assert.InRange(f, 20, 20.41); }
            });
            Assert.Equal(1, creaks);
        }

        [Fact]
        public void Latch_AnswersCrouchedFloorOnly_UntilReleased_L1810_L1812()
        {
            var latch = new Latch("dl01.latch", LatchParams.Dl01Latch());
            var g = Mech.Graph(latch);
            Assert.True(latch.IsAvailable(At(3.0 + 0.33)));
            Assert.False(latch.IsAvailable(At(3.0 + 0.35)));
            Assert.True(latch.IsAvailable(At(3.0, 0.05)));
            Assert.False(latch.IsAvailable(At(3.0, 0.06)));
            Assert.Equal(InteractionCategory.Fixed, latch.Category);
            Mech.PlayAct(g, latch);
            Assert.False(latch.IsAvailable(At(3.0)));
        }

        [Theory]
        [InlineData("start", LatchState.Locked, 0)]
        [InlineData("shutter", LatchState.Released, 72)]
        [InlineData("workshop", LatchState.Released, 72)]
        public void Latch_ResetFromCheckpoint_L8022(string cp, LatchState state, double lever)
        {
            var latch = new Latch("dl01.latch", LatchParams.Dl01Latch());
            var g = Mech.Graph(cp, latch);
            Assert.Equal(state, latch.State);
            Assert.Equal(lever, latch.LeverDeg);
            Assert.Equal(0, g.Log.Count);
        }

        [Fact]
        public void Latch_ThresholdTrigger_ReleasesMoreThanDelayAfterFirstReached_L5764()
        {
            var src = new TestSource("dl16.rack");
            var latch = new Latch("dl16.latch", new LatchParams { Trigger = "dl16.rack", Threshold = 1, Delay = 1.2 });
            var g = Mech.Graph(src, latch);
            Mech.Run(g, 10);
            src.Position = 1;
            Mech.Run(g, 1);                                       // fullAt = now
            src.Position = 0.5;                                   // it need not stay full
            int n = Mech.RunUntil(g, () => latch.Engaged);
            Assert.InRange(n, 72, 73);                            // clock − fullAt > 1.2 s
        }

        [Fact]
        public void Latch_ThresholdWithoutDelay_ReleasesOnTheSameStep_L6258()
        {
            var bed = new TestSource("dl17.beds");
            var latch = new Latch("dl17.latch", new LatchParams { Trigger = "dl17.beds", Threshold = 0.95 });
            var g = Mech.Graph(bed, latch);
            bed.Position = 0.949;
            Mech.Run(g, 5);
            Assert.False(latch.Engaged);
            bed.Position = 0.95;
            Mech.Run(g, 1);
            Assert.True(Mech.Entered(g, "dl17.latch", LatchState.Released));
        }

        [Fact]
        public void Latch_RestoredMidPull_ContinuesIdentically()
        {
            var a = new Latch("dl01.latch", LatchParams.Dl01Latch());
            var ga = Mech.Graph(a);
            Mech.PlayAct(ga, a, max: 50);                         // f 20: mid-pull, before the release
            var snap = Mech.Snapshot(ga);

            var b = new Latch("dl01.latch", LatchParams.Dl01Latch());
            var gb = Mech.Graph(b);
            gb.Restore(snap);
            var ta = new List<string>();
            var tb = new List<string>();
            Mech.PlayAct(ga, a, startStep: 51, onStep: (k, f) => ta.Add(Mech.Dump(ga)));
            Mech.PlayAct(gb, b, startStep: 51, onStep: (k, f) => tb.Add(Mech.Dump(gb)));
            Assert.Equal(ta, tb);
            Assert.True(b.Engaged);
        }

        // ---- Pawl -----------------------------------------------------------------------------------------------------------

        private static (MechanismGraph g, Pawl pawl, TestSource platform) Dl08(double h, string cp = "goods")
        {
            var pawl = new Pawl("dl08.pawl", PawlParams.Dl08Pawl());
            var platform = new TestSource("dl08.platform") { Position = h };
            return (Mech.Graph(cp, pawl, platform), pawl, platform);
        }

        [Fact]
        public void Pawl_AtTheLanding_BitesAtF22_OutAtF33_L3305_L3318()
        {
            var (g, pawl, _) = Dl08(1.0);
            Assert.Equal("LeverPull", pawl.Profile.Clip);
            double bitAt = -1;
            int steps = Mech.PlayAct(g, pawl, onStep: (k, f) => { if (Mech.Entered(g, "dl08.pawl", PawlState.Engaged)) bitAt = f; });
            Assert.InRange(bitAt, 22 - 1e-6, 22.4);
            Assert.InRange(steps * Mech.FramesPerStep, 33 - 1e-6, 33.4);
            Assert.True(pawl.Engaged);
            Assert.Equal(6, pawl.LeverDeg);                       // LEVER_NEAR once the act is over
        }

        [Fact]
        public void Pawl_BelowTheLanding_RattlesTwice_NeverBites_OutAtF45_L3305_L3314()
        {
            var (g, pawl, _) = Dl08(0.984);
            Assert.Equal("LeverStuck", pawl.Profile.Clip);
            var clatters = new List<double>();
            double maxDip = 0;
            int steps = Mech.PlayAct(g, pawl, onStep: (k, f) =>
            {
                if (Mech.Emitted(g, "dl08.pawl", PawlEvent.Clatter)) clatters.Add(f);
                maxDip = Math.Max(maxDip, pawl.Dip);
            });
            Assert.False(pawl.Engaged);
            Assert.Equal(2, clatters.Count);
            Assert.InRange(clatters[0], 12, 12.41);
            Assert.InRange(clatters[1], 21, 21.41);
            Assert.InRange(steps * Mech.FramesPerStep, 45 - 1e-6, 45.4);
            Assert.InRange(maxDip, 0.4, 0.45 * 1.4 + 1e-9);
            Assert.Equal(-18, pawl.LeverDeg);
        }

        [Fact]
        public void Pawl_WindowIsJudgedWhenTheActStarts_L3305()
        {
            var (g, pawl, platform) = Dl08(0.9);
            Mech.PlayAct(g, pawl, onStep: (k, f) => platform.Position = 1.0);   // reaches the landing mid-act: too late
            Assert.False(pawl.Engaged);
            Mech.PlayAct(g, pawl);                                              // a second pull bites
            Assert.True(pawl.Engaged);
        }

        [Fact]
        public void Pawl_StationOnTheDeck_NotOnceLatched_L3267_L3269()
        {
            var (g, pawl, _) = Dl08(1.0);
            Assert.True(pawl.IsAvailable(At(85.45 + 0.35, 1.6)));
            Assert.False(pawl.IsAvailable(At(85.45 + 0.37, 1.6)));
            Assert.False(pawl.IsAvailable(At(85.45, 1.66)));
            Assert.Equal(0.04, pawl.StandZ, 12);                  // PAWL_Z + 0.26 negated (§0.2)
            Mech.PlayAct(g, pawl);
            Assert.False(pawl.IsAvailable(At(85.45, 1.6)));
        }

        [Theory]
        [InlineData("goods", PawlState.Free, -18)]
        [InlineData("latched", PawlState.Engaged, 6)]
        [InlineData("tunnel", PawlState.Engaged, 6)]
        public void Pawl_ResetFromCheckpoint_L8043_L8044(string cp, PawlState state, double lever)
        {
            var (_, pawl, _) = Dl08(0, cp);
            Assert.Equal(state, pawl.State);
            Assert.Equal(lever, pawl.LeverDeg);
        }

        /// <summary>A platform that stays at the landing once the pawl holds it (L3180), reading the pawl this tick.</summary>
        private sealed class HeldPlatform : Mechanism, IPositionSource
        {
            private IEngageable _pawl;
            public HeldPlatform() : base("dl08.platform") { }
            public double Position { get; set; }
            public override void Link(MechanismLinker link) => _pawl = link.Read<IEngageable>("dl08.pawl");
            public override void Reset(in Checkpoint cp) { }
            public override void Step(in StepContext ctx) { if (_pawl.Engaged) Position = 1; else Position = Math.Max(0, Position - 0.1); }
            protected override void WriteFields(ISnapshotWriter w) => w.WriteDouble("h", Position);
            protected override void ReadFields(ISnapshotReader r) => Position = r.ReadDouble("h");
        }

        [Fact]
        public void Pawl_AndItsPlatform_ReadEachOther_PawlFirst_L3180_L3305()
        {
            var pawl = new Pawl("dl08.pawl", PawlParams.Dl08Pawl());
            var platform = new HeldPlatform { Position = 1 };
            var g = Mech.Graph("goods", pawl, platform);         // pawl reads the platform with ReadAnyOrder: builds
            Mech.PlayAct(g, pawl);
            Mech.Run(g, 30);
            Assert.True(pawl.Engaged);
            Assert.Equal(1.0, platform.Position);                 // held at the landing

            var bad = new MechanismGraph();
            bad.Add(new HeldPlatform());                          // platform first: its same-tick read of the pawl is refused
            bad.Add(new Pawl("dl08.pawl", PawlParams.Dl08Pawl()));
            Assert.Throws<InvalidOperationException>(() => bad.Build());
        }

        // ---- CageCatch ------------------------------------------------------------------------------------------------------

        private static (MechanismGraph g, CageCatch c, TestSource cage) Dl09(double y, string cp = "cage")
        {
            var c = new CageCatch("dl09.cagePawl", CageCatchParams.Dl09CagePawl());
            var cage = new TestSource("dl09.cage") { Position = y };
            return (Mech.Graph(cp, c, cage), c, cage);
        }

        [Theory]
        [InlineData(1.54, true)] [InlineData(1.8, true)] [InlineData(2.05, true)]
        [InlineData(1.539, false)] [InlineData(2.051, false)] [InlineData(3.0, false)] [InlineData(-0.1, false)]
        public void CageCatch_BitesOnlyInside_1_54_To_2_05_L5089(double y, bool bites)
        {
            var (g, c, _) = Dl09(y);
            c.Throw();
            Mech.Run(g, 1);
            Assert.Equal(bites ? CageCatchState.Bitten : CageCatchState.Rattling, c.State);
            Assert.Equal(bites, c.Engaged);
            Assert.True(c.Thrown);
        }

        [Fact]
        public void CageCatch_Rattle_RearmsAfter0_6s_AndIgnoresThrowsMeanwhile_L5092()
        {
            var (g, c, cage) = Dl09(2.5);
            c.Throw();
            Mech.Run(g, 1);
            cage.Position = 1.8;                                   // now inside: but it is still thrown
            c.Throw();
            Mech.Run(g, 1);
            Assert.Equal(CageCatchState.Rattling, c.State);
            int n = Mech.RunUntil(g, () => c.State == CageCatchState.Armed);
            Assert.Equal(35, n);                                   // 36 steps = 0.6 s after the throw
            Assert.True(Mech.Entered(g, "dl09.cagePawl", CageCatchState.Armed));
            c.Throw();
            Mech.Run(g, 1);
            Assert.True(c.Engaged);
        }

        [Fact]
        public void CageCatch_RearmOnANewRide_ButBittenStaysBitten_L5031()
        {
            var (g, c, cage) = Dl09(2.5);
            c.Throw();
            Mech.Run(g, 2);
            c.Rearm();
            Mech.Run(g, 1);
            Assert.Equal(CageCatchState.Armed, c.State);
            cage.Position = 1.6;
            c.Throw();
            Mech.Run(g, 1);
            c.Rearm();
            Mech.Run(g, 1);
            Assert.Equal(CageCatchState.Bitten, c.State);
        }

        [Theory]
        [InlineData("cage", CageCatchState.Armed)]
        [InlineData("landing8", CageCatchState.Bitten)]
        public void CageCatch_ResetFromCheckpoint_L4100(string cp, CageCatchState state)
        {
            var (_, c, _) = Dl09(3.4, cp);
            Assert.Equal(state, c.State);
        }

        [Fact]
        public void CageCatch_RestoredWhileRattling_RearmsOnTheSameTick()
        {
            var (ga, a, _) = Dl09(2.5);
            a.Throw();
            Mech.Run(ga, 10);
            var (gb, b, _) = Dl09(2.5);
            gb.Restore(Mech.Snapshot(ga));
            int na = Mech.RunUntil(ga, () => a.State == CageCatchState.Armed);
            int nb = Mech.RunUntil(gb, () => b.State == CageCatchState.Armed);
            Assert.Equal(na, nb);
            Assert.Equal(Mech.Dump(ga), Mech.Dump(gb));
        }

        // ---- CycleBrake -----------------------------------------------------------------------------------------------------

        private static (MechanismGraph g, CycleBrake b, TestSource lesson) Dl13(bool running, string cp = "lesson")
        {
            var lesson = new TestSource("dl13.lesson") { Engaged = running };
            var b = new CycleBrake("dl13.brake", CycleBrakeParams.Dl13Brake());
            return (Mech.Graph(cp, lesson, b), b, lesson);
        }

        [Fact]
        public void CycleBrake_EachPullToggles_0_35sIn_ActOverAfter1s_L5350_L5361()
        {
            var (g, b, _) = Dl13(true);
            double toggledAt = -1;
            int steps = Mech.PlayAct(g, b, onStep: (k, f) => { if (Mech.Entered(g, "dl13.brake", CycleBrakeState.Braked)) toggledAt = k * Mech.Dt; });
            Assert.InRange(toggledAt, 0.35, 0.35 + Mech.Dt + 1e-9);
            Assert.InRange(steps * Mech.Dt, 1.0 - 1e-9, 1.0 + Mech.Dt + 1e-9);
            Assert.True(b.Engaged);
            Mech.Run(g, 5);
            Mech.PlayAct(g, b);
            Assert.Equal(CycleBrakeState.Free, b.State);
        }

        [Fact]
        public void CycleBrake_WithNoCycleRunning_OnlyClunks_L5344()
        {
            var (g, b, _) = Dl13(false);
            int clunks = 0;
            Mech.PlayAct(g, b, onStep: (k, f) => { if (Mech.Emitted(g, "dl13.brake", CycleBrakeEvent.Clunk)) clunks++; });
            Assert.Equal(1, clunks);
            Assert.Equal(CycleBrakeState.Free, b.State);
        }

        [Fact]
        public void CycleBrake_Unwired_AlwaysRuns_Dl14a_L6079()
        {
            var b = new CycleBrake("dl14a.brake", CycleBrakeParams.Dl14aBrake());
            var g = Mech.Graph("dorm", b);
            Mech.PlayAct(g, b);
            Assert.True(b.Engaged);
        }

        [Fact]
        public void CycleBrake_StandsOffThePawl_ReachIsFromThePawl_L5290_L5298()
        {
            var (_, b, _) = Dl13(true);
            Assert.Equal(220.4, b.StandX, 12);
            Assert.Equal(220.6, b.AnchorX, 12);
            Assert.True(b.IsAvailable(At(220.6 + 0.39)));
            Assert.False(b.IsAvailable(At(220.6 - 0.41)));        // 0.21 from the stand point, 0.41 from the pawl
            Assert.Equal(0.6, b.Reach, 9);                        // the resolver's stand-point test never refuses first
        }

        [Theory]
        [InlineData("lesson", CycleBrakeState.Free)]
        [InlineData("gallery13", CycleBrakeState.Braked)]
        public void CycleBrake_ResetFromCheckpoint_L5236(string cp, CycleBrakeState state)
        {
            var (_, b, _) = Dl13(true, cp);
            Assert.Equal(state, b.State);
        }
    }
}
