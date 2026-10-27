using System;
using System.Collections.Generic;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Mechanisms.Plates;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Lifts and counterweights (§4.13f). Step counts are at 60 Hz with the README's 1e-9 time slack (so "5.5 s" is
    /// 330 steps); the prototype's own counts were cross-checked with a JS transcription of the cited lines.
    /// </summary>
    public class LiftTests
    {
        private const double Dt = Mech.Dt;

        private static MechanismEvent? Find<T>(MechanismGraph g, MechanismId id, T evt) where T : struct, Enum
        {
            int code = Convert.ToInt32(evt);
            for (int i = 0; i < g.Log.Count; i++)
                if (g.Log[i].Id == id && g.Log[i].Kind == MechanismEventKind.Event && g.Log[i].Code == code) return g.Log[i];
            return null;
        }

        /// <summary>Runs until a state is entered; returns the step count (1-based) or -1.</summary>
        private static int StepsUntilEntered<T>(MechanismGraph g, MechanismId id, T state, Func<PlayerPose> pose = null, int max = 5000,
            Action<int> before = null) where T : struct, Enum
        {
            for (int i = 1; i <= max; i++)
            {
                before?.Invoke(i);
                g.Step(Dt, pose?.Invoke() ?? PlayerPose.Away);
                if (Mech.Entered(g, id, state)) return i;
            }
            return -1;
        }

        /// <summary>Runs <paramref name="g"/> and a restored copy side by side; every dump must match.</summary>
        private static void AssertRestoreContinues(MechanismGraph a, MechanismGraph b, int steps, Func<int, PlayerPose> pose = null,
            Action<int> beforeA = null, Action<int> beforeB = null)
        {
            b.Restore(Mech.Snapshot(a));
            Assert.Equal(Mech.Dump(a), Mech.Dump(b));
            for (int k = 0; k < steps; k++)
            {
                beforeA?.Invoke(k);
                beforeB?.Invoke(k);
                var p = pose?.Invoke(k) ?? PlayerPose.Away;
                a.Step(Dt, p);
                b.Step(Dt, p);
                Assert.Equal(Mech.Dump(a), Mech.Dump(b));
                Assert.Equal(Mech.Events(a).Count, Mech.Events(b).Count);
            }
        }

        // ---- CounterweightLift (dl08.platform) ---------------------------------------------------------------------------

        private sealed class Dl08
        {
            public readonly TestSource Pawl = new TestSource("dl08.pawl");
            public readonly TestSource Pan = new TestSource("dl08.pan");
            public readonly CounterweightLift Lift = new CounterweightLift("dl08.platform", CounterweightLiftParams.Dl08Platform());
            public readonly MechanismGraph G;
            public Dl08(double pan = 0, bool latched = false, string cp = "goods")
            {
                Pan.Load = pan; Pawl.Engaged = latched;
                G = Mech.Graph(cp, Pawl, Pan, Lift);
            }
        }

        [Fact]
        public void Platform_RisesTowardThePan_At0_6mps_ArrivesAfter4_5s_TicksEvery0_04_L3185_L3188()
        {
            var s = new Dl08(pan: 1.05);
            int ticks = 0, arrive = -1;
            for (int i = 1; i <= 400; i++)
            {
                s.G.Step(Dt, PlayerPose.Away);
                if (Mech.Emitted(s.G, "dl08.platform", CounterweightLiftEvent.Tick)) ticks++;
                if (Mech.Emitted(s.G, "dl08.platform", CounterweightLiftEvent.Arrive)) arrive = i;
                if (i == 1) Assert.True(Mech.Entered(s.G, "dl08.platform", CounterweightLiftState.Rising));
                if (i < 270) Assert.Equal(0.6, s.Lift.FloorVelocity, 9);
            }
            Assert.Equal(270, arrive);                                        // 2.7 m at 0.6 m/s
            Assert.Equal(24, ticks);
            Assert.InRange(s.Lift.Position, 1 - 1e-4, 1);
            Assert.True(s.Lift.Position >= 0.985);                           // the pawl's bite window
            Assert.Equal(CounterweightLiftState.Still, s.Lift.State);
            Assert.Equal(1.6, s.Lift.FloorY, 3);
        }

        [Fact]
        public void Platform_DropsWithAccel8_UpTo3_4_AndCrashes_L3190_L3194()
        {
            var s = new Dl08(pan: 0, latched: true);                         // held at the landing
            Assert.Equal(1.0, s.Lift.Position);
            s.Pawl.Engaged = false;                                          // (only for the test: the pawl never lets go)
            double minV = 0;
            int crash = -1;
            MechanismEvent? e = null;
            for (int i = 1; i <= 100 && crash < 0; i++)
            {
                s.G.Step(Dt, PlayerPose.Away);
                minV = Math.Min(minV, s.Lift.FloorVelocity);
                if ((e = Find(s.G, "dl08.platform", CounterweightLiftEvent.Crash)) != null) crash = i;
            }
            Assert.Equal(60, crash);
            Assert.Equal(3.4, e.Value.Value, 12);
            Assert.Equal(-3.4, minV, 9);
            Assert.Equal(0, s.Lift.Position);
            Assert.Equal(0, s.Lift.FallSpeed);
            Assert.Equal(1.6 - 2.7, s.Lift.FloorY, 12);
        }

        [Theory]
        [InlineData(85.0, false, true)]     // on the deck by the shaft, free: startled
        [InlineData(85.0, true, false)]     // in an act: not
        [InlineData(90.0, false, false)]    // 3.5 from x 86.5: not
        public void Platform_Crash_StartlesHimNearTheShaft_L3195(double x, bool busy, bool startled)
        {
            var s = new Dl08(pan: 0, latched: true);
            s.Pawl.Engaged = false;
            var pose = Mech.Pose(x, 1.6, busy: busy);
            bool seen = false;
            for (int i = 0; i < 70; i++) { s.G.Step(Dt, pose); seen |= Mech.Emitted(s.G, "dl08.platform", CounterweightLiftEvent.Startle); }
            Assert.Equal(startled, seen);
        }

        [Fact]
        public void Platform_SlowFall_DoesNotCrash_L3191()
        {
            var s = new Dl08(pan: 0.5);
            Mech.Run(s.G, 300);
            Assert.Equal(0.5, s.Lift.Position, 12);
            s.Pan.Load = 0.495;                                              // a 1.35 cm drop: it lands at 0.53 m/s
            bool crashed = false;
            for (int i = 0; i < 30; i++) { s.G.Step(Dt, PlayerPose.Away); crashed |= Mech.Emitted(s.G, "dl08.platform", CounterweightLiftEvent.Crash); }
            Assert.False(crashed);
            Assert.InRange(s.Lift.Position, 0.495, 0.495 + 1e-4);           // it stops within the 1e-4 dead band (L3189)
            Assert.Equal(CounterweightLiftState.Still, s.Lift.State);
        }

        [Fact]
        public void Platform_Latched_HoldsAtTheLanding_WhateverThePan_L3182()
        {
            var s = new Dl08(pan: 0.2, latched: true);
            Mech.Run(s.G, 120, Mech.Pose(87.0, 1.6));                       // he walks over it: no teeter once latched
            Assert.Equal(1.0, s.Lift.Position);
            Assert.False(s.Lift.Lurching);
            Assert.True(s.Lift.Carrying);
            Assert.Equal(CounterweightLiftState.Still, s.Lift.State);
        }

        [Fact]
        public void Platform_OntoItUnlatched_TeetersBack_DipsThenRecovers_L3278_L3335()
        {
            var s = new Dl08(pan: 1.05);
            Mech.Run(s.G, 300);                                              // at the landing, pawl not set
            double floor = s.Lift.FloorY;
            s.G.Step(Dt, Mech.Pose(86.0, floor));                            // steps onto the left half of the platform
            var e = Find(s.G, "dl08.platform", CounterweightLiftEvent.Teeter);
            Assert.NotNull(e);
            Assert.Equal(85.8 - 0.28, e.Value.Value, 12);                    // back to SHAFT.x0 − 0.28
            Assert.True(s.Lift.Lurching);
            // The act runs (Busy): the platform drops 0.1 m and crashes into its dip.
            bool crashed = false;
            for (int i = 0; i < 40; i++) { s.G.Step(Dt, Mech.Pose(85.6, 1.6, busy: true)); crashed |= Mech.Emitted(s.G, "dl08.platform", CounterweightLiftEvent.Crash); }
            Assert.True(crashed);
            Assert.Equal(1 - 0.1 / 2.7, s.Lift.Position, 12);
            s.Lift.EndLurch();                                               // Teeter f22: he lands on the deck
            Mech.Run(s.G, 60, Mech.Pose(85.52, 1.6, busy: true));
            Assert.False(s.Lift.Lurching);
            Assert.True(s.Lift.Position > 1 - 1e-4 - 1e-12);                 // wound back up to the landing
            s.G.Step(Dt, Mech.Pose(88.6, 1.6));                              // right of the shaft: it scrambles right
            Assert.Null(Find(s.G, "dl08.platform", CounterweightLiftEvent.Teeter));
        }

        [Fact]
        public void Platform_TeeterBack_GoesToTheNearerSide_L3279()
        {
            var s = new Dl08(pan: 1.05);
            Mech.Run(s.G, 300);
            s.G.Step(Dt, Mech.Pose(88.0, s.Lift.FloorY));
            Assert.Equal(88.3 + 0.28, Find(s.G, "dl08.platform", CounterweightLiftEvent.Teeter).Value.Value, 12);
        }

        [Fact]
        public void Platform_HisWeightComesOffThePan_WhileHeIsOnIt_L3182()
        {
            var s = new Dl08(pan: 1.05);
            for (int i = 0; i < 300; i++) s.G.Step(Dt, Mech.Pose(87.0, s.Lift.FloorY, busy: true));   // riding it, in an act: no teeter
            Assert.Equal(0.55, s.Lift.Position, 12);                         // 1.05 − 0.5
            Assert.False(s.Lift.Lurching);
        }

        [Theory]
        [InlineData("goods", 0.0)]
        [InlineData("latched", 1.0)]
        [InlineData("workshop", 1.0)]
        public void Platform_ResetFromCheckpoint_WithTheRealPawl_L8043(string cp, double h)
        {
            var pawl = new Pawl("dl08.pawl", PawlParams.Dl08Pawl());
            var pan = new TestSource("dl08.pan");
            var lift = new CounterweightLift("dl08.platform", CounterweightLiftParams.Dl08Platform());
            var g = Mech.Graph(cp, pawl, pan, lift);
            Assert.Equal(h, lift.Position);
            Assert.Equal(1.6 - 2.7 * (1 - h), lift.FloorY, 12);
            Assert.Equal(0, lift.FloorVelocity);
            Assert.Equal(CounterweightLiftState.Still, lift.State);
            Assert.Equal(0, g.Log.Count);
        }

        [Fact]
        public void Platform_ResetWithoutAPawl_UsesItsCheckpoint()
        {
            var p = CounterweightLiftParams.Dl08Platform();
            p.Pawl = MechanismId.None;
            var lift = new CounterweightLift("dl08.platform", p);
            Mech.Graph("latched", new TestSource("dl08.pan"), lift);
            Assert.True(lift.Latched);
            Assert.Equal(1.0, lift.Position);
        }

        [Fact]
        public void Platform_AndTheRealPawl_BitesAtTheLanding_ThenHolds_L3180_L3305()
        {
            var pawl = new Pawl("dl08.pawl", PawlParams.Dl08Pawl());
            var pan = new TestSource("dl08.pan") { Load = 1.05 };
            var lift = new CounterweightLift("dl08.platform", CounterweightLiftParams.Dl08Platform());
            var g = Mech.Graph("goods", pawl, pan, lift);
            Mech.Run(g, 280);
            Mech.PlayAct(g, pawl);
            Assert.True(pawl.Engaged);
            pan.Load = 0;                                                    // trolley off the pan
            Mech.Run(g, 120);
            Assert.True(lift.Position >= 1 - 1e-4);
        }

        [Fact]
        public void Platform_RestoredMidFall_ContinuesIdentically()
        {
            var a = new Dl08(pan: 0, latched: true);
            a.Pawl.Engaged = false;
            Mech.Run(a.G, 20);
            var b = new Dl08(pan: 0.7);
            b.Pawl.Engaged = false;
            AssertRestoreContinues(a.G, b.G, 80);
            Assert.Equal(0, b.Lift.Position);
        }

        // ---- SlippingCage (dl09.cage) -------------------------------------------------------------------------------------

        private sealed class Dl09
        {
            public readonly TestSource Tray = new TestSource("dl09.tray");
            public readonly CageCatch Catch = new CageCatch("dl09.cagePawl", CageCatchParams.Dl09CagePawl());
            public readonly SlippingCage Cage = new SlippingCage("dl09.cage", SlippingCageParams.Dl09Cage());
            public readonly MechanismGraph G;
            public bool InCage = true, Grounded = true, Holding;
            public Dl09(int plates, string cp = "cage")
            {
                Tray.Load = plates;
                G = Mech.Graph(cp, Tray, Catch, Cage);
            }
            /// <summary>He stands in the cage on its floor (ride sync), in the cage act while it carries him.</summary>
            public PlayerPose Pose() => InCage ? Mech.Pose(101.52, Cage.FloorY, busy: Cage.Riding, grounded: Grounded, holding: Holding)
                : Mech.Pose(100.5, 3.4, grounded: Grounded, holding: Holding);
            public void Step() => G.Step(Dt, Pose());
        }

        /// <summary>Records every state entered and event emitted by the cage, with its step number.</summary>
        private static List<string> RunCage(Dl09 s, int steps, Func<int, bool> pull = null, Func<bool> until = null)
        {
            var trace = new List<string>();
            for (int i = 1; i <= steps && (until == null || !until()); i++)
            {
                if (pull != null && pull(i)) s.Cage.PullPawl();
                s.Step();
                foreach (var e in Mech.Events(s.G))
                    if (e.Id == "dl09.cage")
                        trace.Add(i + " " + (e.Kind == MechanismEventKind.State ? ((SlippingCageState)e.Code).ToString() : ((SlippingCageEvent)e.Code) + "#" + e.Index));
            }
            return trace;
        }

        [Theory]
        [InlineData(0, 3.02, 155)]
        [InlineData(1, 3.18, 131)]
        public void Cage_TooLight_DipsHoldsAndHaulsBack_ThenNeedsHimToStepOut_L5020_L5029(int plates, double dipY, int topStep)
        {
            var s = new Dl09(plates);
            var trace = RunCage(s, 98);
            Assert.Equal(new[] { "1 Dip", "1 RideStart#0", "23 DipBang#0", "98 HaulDip" }, trace);   // bang > 0.35 s, haul > 1.6 s
            Assert.Equal(dipY, s.Cage.Y, 9);                                 // 0.38 (empty) / 0.22 (one plate) below the top
            trace = RunCage(s, topStep - 98);
            Assert.Equal(new[] { topStep - 98 + " Top", topStep - 98 + " RideEnd#" + SlippingCage.QuirkStartle }, trace);   // at 0.4 m/s
            Assert.Equal(3.4, s.Cage.Y);
            Assert.False(s.Cage.Riding);
            Assert.Empty(RunCage(s, 200));                                   // still standing in it: needs to step out
            s.InCage = false;
            s.Step();
            s.InCage = true;
            Assert.Equal(new[] { "1 Dip", "1 RideStart#0" }, RunCage(s, 1));
        }

        [Fact]
        public void Cage_AfterADip_IsReadyOnly0_8sLater_L5029()
        {
            var s = new Dl09(0);
            RunCage(s, 155);
            s.InCage = false;
            s.Step();                                                        // out: needExit cleared, 1 step after the top
            s.InCage = true;
            var trace = RunCage(s, 60);
            Assert.Equal(new[] { "48 Dip", "48 RideStart#0" }, trace);      // 49 steps after reaching the top: clock > readyAt
        }

        [Fact]
        public void Cage_FullRide_WithoutThePawl_SlipsCatchesOnceStallsAndCrashes_Death_L5031_L5048()
        {
            var s = new Dl09(2);
            var trace = RunCage(s, 865);  // ready again 1.6 s after the top: 773 + 97 > 865
            // Settle > 1.0 s, lower 0.55 m at 0.32 m/s, shudder > 0.7 s, slip to 1.95, stall > 0.75 s, slip to −0.1, crash
            // > 1.4 s, haul 3.5 m at 0.7 m/s. (At exactly 60 Hz the prototype's summed dt passes "t > 1.0" one step early
            // by rounding (1.0000000000000007); with the README slack an exact threshold is not yet passed.)
            Assert.Equal("1 Settle|1 RideStart#1|62 Lower|158 Shudder|201 Slip|253 Stall|299 Slip|388 Crash|388 Death#0|473 Haul|773 Top",
                string.Join("|", trace));
            Assert.Equal(3.4, s.Cage.Y);
            Assert.False(s.Cage.Riding);                                     // he died at the crash: no RideEnd
        }

        [Fact]
        public void Cage_FullRide_PhaseHeightsAndSpeeds_L5036_L5048()
        {
            var s = new Dl09(2);
            var seen = new Dictionary<SlippingCageState, double>();
            double maxSlip = 0, lowerV = 0;
            for (int i = 1; i <= 470; i++)
            {
                var before = s.Cage.State;
                s.Step();
                if (s.Cage.State != before && !seen.ContainsKey(s.Cage.State)) seen[s.Cage.State] = s.Cage.Y;
                if (s.Cage.State == SlippingCageState.Lower) lowerV = s.Cage.FloorVelocity;
                maxSlip = Math.Max(maxSlip, s.Cage.SlipSpeed);
            }
            Assert.Equal(3.36, seen[SlippingCageState.Lower], 9);            // settled 0.04
            Assert.InRange(seen[SlippingCageState.Shudder], 3.4 - 0.55 - 0.32 * Dt, 3.4 - 0.55);
            Assert.Equal(1.95, seen[SlippingCageState.Stall], 12);           // catches once at landing + 0.35
            Assert.Equal(-0.1, seen[SlippingCageState.Crash], 12);
            Assert.Equal(-0.32, lowerV, 9);
            Assert.Equal(1.6, maxSlip, 12);
        }

        [Fact]
        public void Cage_PawlThrownInTheStall_Bites_EasesToTheLanding_Caught_Proud_L5089_L5046_L5094()
        {
            var s = new Dl09(2);
            RunCage(s, 400, pull: null, until: () => s.Cage.State == SlippingCageState.Stall);
            RunCage(s, 10);
            var trace = RunCage(s, 1, pull: i => true);
            Assert.Equal(new[] { "1 Bite" }, trace);
            Assert.True(s.Catch.Engaged);
            Assert.Equal(1.95 + (1.6 - 1.95) * 9 * Dt, s.Cage.Y, 12);
            trace = RunCage(s, 60);
            Assert.Equal(new[] { "30 Caught", "56 RideEnd#" + SlippingCage.QuirkProud }, trace);   // 292, 318
            Assert.Equal(1.6, s.Cage.Y);
            Assert.Equal(0, s.Cage.FloorVelocity);
            Assert.False(s.Cage.Riding);
            Assert.Empty(RunCage(s, 600));                                   // caught for good
        }

        [Fact]
        public void Cage_PawlThrownTooEarly_Rattles_RearmsAfter0_6s_SecondThrowBites_L5091_L5092()
        {
            var s = new Dl09(2);
            RunCage(s, 160, pull: i => i == 160);                            // shuddering at 2.85: outside the window
            Assert.Equal(CageCatchState.Rattling, s.Catch.State);
            Assert.Equal(SlippingCageState.Shudder, s.Cage.State);
            RunCage(s, 36);
            Assert.Equal(CageCatchState.Armed, s.Catch.State);
            var trace = RunCage(s, 100, pull: i => s.Cage.State == SlippingCageState.Stall);
            Assert.Contains(trace, t => t.EndsWith(" Bite"));
        }

        [Fact]
        public void Cage_PawlOnlyThrowsWhileLoweringOrSlipping_AndOnlyRiding_L5085()
        {
            var s = new Dl09(2);
            RunCage(s, 10, pull: i => true);                                 // settling: Use does nothing
            Assert.Equal(CageCatchState.Armed, s.Catch.State);
            Assert.False(s.Cage.PawlThrowable);
            var idle = new Dl09(2) { InCage = false };
            RunCage(idle, 5, pull: i => true);
            Assert.Equal(CageCatchState.Armed, idle.Catch.State);
        }

        [Fact]
        public void Cage_BelowTheWindow_ThePawlMisses_AndItCrashes_L5089()
        {
            var s = new Dl09(2);
            var trace = RunCage(s, 400, pull: i => s.Cage.State == SlippingCageState.Slip && s.Cage.Y < 1.54 - 0.05);
            Assert.Contains(trace, t => t.EndsWith(" Death#0"));
            Assert.Equal(CageCatchState.Rattling, s.Catch.State);
            Assert.DoesNotContain(trace, t => t.EndsWith(" Bite"));
        }

        [Fact]
        public void Cage_DoesNotStartWhileHeIsBusyOrHolding_L5020_L5031()
        {
            var s = new Dl09(2);
            for (int i = 0; i < 30; i++) s.G.Step(Dt, Mech.Pose(101.52, 3.4, busy: true));
            Assert.Equal(SlippingCageState.Top, s.Cage.State);
            for (int i = 0; i < 30; i++) { s.Grounded = true; s.Holding = true; s.Step(); }
            Assert.Equal(SlippingCageState.Top, s.Cage.State);
            for (int i = 0; i < 30; i++) { s.Grounded = false; s.Holding = false; s.Step(); }
            Assert.Equal(SlippingCageState.Top, s.Cage.State);
            s.G.Step(Dt, Mech.Pose(101.25, 3.4));                            // not 0.1 inside the shaft
            Assert.Equal(SlippingCageState.Top, s.Cage.State);
            s.Grounded = true; s.Holding = false;
            s.Step();
            Assert.Equal(SlippingCageState.Settle, s.Cage.State);
        }

        [Fact]
        public void Cage_CarriesHimForTheWholeAct_FloorAndVelocity()
        {
            var s = new Dl09(2);
            for (int i = 1; s.Cage.State != SlippingCageState.Crash; i++)
            {
                double y0 = s.Cage.FloorY;
                s.Step();
                Assert.True(s.Cage.Carrying);
                Assert.Equal(s.Cage.Y, s.Cage.FloorY);
                Assert.Equal((s.Cage.FloorY - y0) / Dt, s.Cage.FloorVelocity, 9);
                Assert.True(i < 1000);
            }
            Assert.True(Mech.Emitted(s.G, "dl09.cage", SlippingCageEvent.Death));    // his fall follows the cage (L5044)
            s.Step();
            Assert.False(s.Cage.Carrying);
        }

        [Theory]
        [InlineData("tunnel", SlippingCageState.Caught, 1.6, CageCatchState.Bitten)]
        [InlineData("cage", SlippingCageState.Top, 3.4, CageCatchState.Armed)]
        [InlineData("landing8", SlippingCageState.Caught, 1.6, CageCatchState.Bitten)]
        [InlineData("latched", SlippingCageState.Top, 3.4, CageCatchState.Armed)]
        public void Cage_ResetFromCheckpoint_L4100(string cp, SlippingCageState state, double y, CageCatchState pawl)
        {
            var s = new Dl09(2, cp);
            Assert.Equal(state, s.Cage.State);
            Assert.Equal(y, s.Cage.Y);
            Assert.Equal(y, s.Cage.FloorY);
            Assert.Equal(pawl, s.Catch.State);
            Assert.False(s.Cage.Riding);
            Assert.Equal(0, s.G.Log.Count);
        }

        [Fact]
        public void Cage_ResetMidRide_PutsItBackAtTheTop_Armed()
        {
            var s = new Dl09(2);
            RunCage(s, 160, pull: i => i == 160);
            s.G.Reset(Mech.Cp("cage"));
            Assert.Equal(SlippingCageState.Top, s.Cage.State);
            Assert.Equal(CageCatchState.Armed, s.Catch.State);
            Assert.Equal(new[] { "1 Settle", "1 RideStart#1" }, RunCage(s, 1));
        }

        [Fact]
        public void Cage_RestoredMidSlip_ContinuesIdentically_WithItsCatch()
        {
            var a = new Dl09(2);
            RunCage(a, 210);                                                 // slipping
            Assert.Equal(SlippingCageState.Slip, a.Cage.State);
            var b = new Dl09(0, "landing8");
            AssertRestoreContinues(a.G, b.G, 120, k => a.Pose(),
                beforeA: k => { if (k == 50) a.Cage.PullPawl(); },
                beforeB: k => { if (k == 50) b.Cage.PullPawl(); });
            Assert.Equal(SlippingCageState.Caught, b.Cage.State);
        }

        // ---- RelocationLift (dl10.lift) ---------------------------------------------------------------------------------

        private sealed class Dl10
        {
            public readonly TestSource Plate = new TestSource("dl10.carPlate");
            public readonly TestSource Gate = new TestSource("dl10.carGate");
            public readonly RelocationLift Lift = new RelocationLift("dl10.lift", RelocationLiftParams.Dl10Lift());
            public readonly MechanismGraph G;
            public Dl10(bool loaded = true, bool gateShut = true, string cp = "uponly")
            {
                Plate.Load = loaded ? 1 : 0; Gate.Position = gateShut ? 1 : 0;
                G = Mech.Graph(cp, Plate, Gate, Lift);
            }
        }

        [Fact]
        public void Relocation_WiredToTheRealPlateAndGate_ReadyOnlyOnceTheGateHasShut_L4584_L4623()
        {
            var suitcase = new TestBody("dl10.case", 121.3, BodySupport.Floor);
            var plate = new LoadPlate("dl10.carPlate", LoadPlateParams.Dl10CarPlate());
            var gate = new Door("dl10.carGate", PlateOutputs.Dl10CarGate());
            var lift = new RelocationLift("dl10.lift", RelocationLiftParams.Dl10Lift());
            var g = Mech.Graph("uponly", suitcase, plate, gate, lift);
            Mech.Run(g, 5);
            Assert.False(lift.Loaded || lift.GateShut || lift.Ready);
            suitcase.Support = BodySupport.Placed;                               // set into the car
            int ready = Mech.RunUntil(g, () => lift.Ready);
            Assert.InRange(ready, 131, 133);                                     // 0.8 s + 1.4 s = 132 steps: the gate is shut
            Assert.Equal(DoorState.Open, gate.State);
            Assert.True(lift.Loaded && lift.GateShut);
            lift.PressUp(false);
            g.Step(Dt, PlayerPose.Away);
            Assert.True(Mech.Entered(g, "dl10.lift", RelocationLiftState.Up));
        }

        [Theory]
        [InlineData(false, false, 0)]
        [InlineData(true, false, 1)]
        public void Relocation_WontGoEmptyOrWithTheGateOpen_Buzzes_L4584_L4590(bool loaded, bool gate, int index)
        {
            var s = new Dl10(loaded, gate);
            Assert.False(s.Lift.Ready);
            s.Lift.PressUp(false);
            s.G.Step(Dt, PlayerPose.Away);
            Assert.Equal(index, Find(s.G, "dl10.lift", RelocationLiftEvent.Buzz).Value.Index);
            Assert.Equal(RelocationLiftState.Idle, s.Lift.State);
        }

        [Fact]
        public void Relocation_FromTheLobby_Up5_5s_Top3s_Down5_5s_L4629_L4635()
        {
            var s = new Dl10();
            Assert.True(s.Lift.Ready && s.Lift.AtRest);
            s.Lift.PressUp(false);
            s.G.Step(Dt, PlayerPose.Away);
            Assert.Equal(0, Find(s.G, "dl10.lift", RelocationLiftEvent.Go).Value.Index);
            Assert.True(Mech.Entered(s.G, "dl10.lift", RelocationLiftState.Up));
            Assert.Equal(329, StepsUntilEntered(s.G, "dl10.lift", RelocationLiftState.Top));    // 330 steps = 5.5 s
            Assert.Equal(1.6, s.Lift.Position);
            Assert.Equal(0.12, Find(s.G, "dl10.lift", RelocationLiftEvent.Arrive).Value.Value);
            Assert.Equal(181, StepsUntilEntered(s.G, "dl10.lift", RelocationLiftState.Down));   // > 3 s
            Assert.Equal(330, StepsUntilEntered(s.G, "dl10.lift", RelocationLiftState.Idle));
            Assert.Equal(0, s.Lift.Position);
            Assert.True(s.Lift.Ready);
            Assert.False(s.Lift.Riding);
        }

        [Fact]
        public void Relocation_SmoothstepTravel_HalfwayAtHalfTime_L4630()
        {
            var s = new Dl10();
            s.Lift.PressUp(false);
            Mech.Run(s.G, 165);
            Assert.Equal(0.8, s.Lift.Position, 9);
            Assert.Equal(1.6 * 1.5 / 5.5, s.Lift.FloorVelocity * -1, 2);      // peak speed 1.5 · travel / T
        }

        [Fact]
        public void Relocation_FromTheCounterweight_HeRidesItDown_Gone_L4585_L4600_L4631()
        {
            var s = new Dl10();
            s.Lift.PressUp(true);
            s.G.Step(Dt, PlayerPose.Away);
            Assert.Equal(1, Find(s.G, "dl10.lift", RelocationLiftEvent.Go).Value.Index);
            Assert.True(s.Lift.Riding && s.Lift.Carrying);
            int gone = -1;
            for (int i = 2; i <= 400 && gone < 0; i++)
            {
                s.G.Step(Dt, PlayerPose.Away);
                Assert.Equal(1.6 - s.Lift.Position, s.Lift.FloorY, 12);
                if (Mech.Entered(s.G, "dl10.lift", RelocationLiftState.Gone)) gone = i;
                else Assert.True(s.Lift.Carrying);
            }
            Assert.Equal(330, gone);
            Assert.Equal(0.35, Find(s.G, "dl10.lift", RelocationLiftEvent.Arrive).Value.Value);
            Assert.False(s.Lift.Carrying);
            Assert.Equal(0, s.Lift.CounterweightY, 12);
            Mech.Run(s.G, 600);
            Assert.Equal(RelocationLiftState.Gone, s.Lift.State);           // for good
            s.Lift.PressUp(true);
            s.G.Step(Dt, PlayerPose.Away);
            Assert.NotNull(Find(s.G, "dl10.lift", RelocationLiftEvent.Buzz));
        }

        [Fact]
        public void Relocation_RidingFollowsTheCueClock_NeverBackwards_L4616_L4617()
        {
            var s = new Dl10();
            s.Lift.PressUp(true);
            s.G.Step(Dt, PlayerPose.Away);
            for (int i = 0; i < 60; i++) { s.Lift.FollowCue(0); s.G.Step(Dt, PlayerPose.Away); }   // cue held: the car waits
            Assert.Equal(1.6 * Maths.Smooth.Step(Dt / 5.5), s.Lift.Position, 12);
            s.Lift.FollowCue(5.0);                                           // the cue jumps ahead: the car follows it
            s.G.Step(Dt, PlayerPose.Away);
            Assert.Equal(1.6 * Maths.Smooth.Step(5.0 / 5.5), s.Lift.Position, 12);
            s.Lift.FollowCue(5.5);
            s.G.Step(Dt, PlayerPose.Away);
            Assert.Equal(RelocationLiftState.Gone, s.Lift.State);
        }

        [Theory]
        [InlineData("tunnel", RelocationLiftState.Idle, 0.0)]
        [InlineData("uponly", RelocationLiftState.Idle, 0.0)]
        [InlineData("ringc", RelocationLiftState.Gone, 1.6)]
        [InlineData("school", RelocationLiftState.Gone, 1.6)]
        public void Relocation_ResetFromCheckpoint_L4101(string cp, RelocationLiftState state, double d)
        {
            var s = new Dl10(cp: cp);
            Assert.Equal(state, s.Lift.State);
            Assert.Equal(d, s.Lift.Position);
            Assert.Equal(1.6 - d, s.Lift.FloorY, 12);
            Assert.False(s.Lift.Riding);
        }

        [Fact]
        public void Relocation_RestoredMidRide_ContinuesIdentically()
        {
            var a = new Dl10();
            a.Lift.PressUp(true);
            Mech.Run(a.G, 100);
            var b = new Dl10(loaded: false, cp: "ringc");
            AssertRestoreContinues(a.G, b.G, 260);
            Assert.Equal(RelocationLiftState.Gone, b.Lift.State);
        }

        // ---- PupilLift (dl15.lift) --------------------------------------------------------------------------------------

        private sealed class Dl15
        {
            public readonly TestSource Pupil = new TestSource("dl15.pupil");
            public readonly TestSource Occupied = new TestSource("dl15.occupied");
            public readonly PupilLift Lift;
            public readonly MechanismGraph G;
            public bool Aboard = true;
            public Dl15(string cp = "sickbay")
            {
                var p = PupilLiftParams.Dl15Lift();
                p.Pupil = "dl15.pupil"; p.Occupied = "dl15.occupied";
                Lift = new PupilLift("dl15.lift", p);
                G = Mech.Graph(cp, Pupil, Occupied, Lift);
            }
            public PlayerPose Pose() => Aboard ? Mech.Pose(281.9, Lift.FloorY) : Mech.Pose(280.5, 1.6);
        }

        [Fact]
        public void PupilLift_GoesDownWithAPupilAndHim_At0_65mps_L5720_L5722()
        {
            var s = new Dl15();
            s.Pupil.Engaged = true;
            int arrive = -1;
            for (int i = 1; i <= 200 && arrive < 0; i++)
            {
                s.G.Step(Dt, s.Pose());
                Assert.True(s.Lift.Carrying);
                if (Mech.Emitted(s.G, "dl15.lift", PupilLiftEvent.Arrive)) arrive = i;
                else Assert.Equal(-0.65, s.Lift.FloorVelocity, 9);
                if (i == 1) Assert.True(Mech.Entered(s.G, "dl15.lift", PupilLiftState.Descending));
            }
            Assert.Equal(148, arrive);                                       // 1.6 m at 0.65 m/s
            Assert.Equal(0, s.Lift.Position);
            Mech.Run(s.G, 10, s.Pose());
            Assert.Equal(PupilLiftState.Still, s.Lift.State);
        }

        [Fact]
        public void PupilLift_HimAlone_BuzzesOnceAndStays_L5716_L5720()
        {
            var s = new Dl15();
            int buzzes = 0;
            for (int i = 0; i < 120; i++) { s.G.Step(Dt, s.Pose()); if (Mech.Emitted(s.G, "dl15.lift", PupilLiftEvent.Buzz)) buzzes++; }
            Assert.Equal(1, buzzes);
            Assert.Equal(1.6, s.Lift.Position);
            s.Aboard = false; s.G.Step(Dt, s.Pose());
            s.Aboard = true; s.G.Step(Dt, s.Pose());
            Assert.True(Mech.Emitted(s.G, "dl15.lift", PupilLiftEvent.Buzz));   // stepping on again buzzes again
            Assert.Equal(1.6, s.Lift.Position);
        }

        [Fact]
        public void PupilLift_EmptyAtTheBottom_ComesBackUp_UnlessAFigureIsOnIt_L5719_L5720()
        {
            var s = new Dl15("class6");
            Assert.Equal(0, s.Lift.Position);
            s.Occupied.Engaged = true;
            Mech.Run(s.G, 60);                                               // a figure still over its deck: it waits
            Assert.Equal(0, s.Lift.Position);
            s.Occupied.Engaged = false;
            Assert.Equal(148, Mech.RunUntil(s.G, () => Mech.Emitted(s.G, "dl15.lift", PupilLiftEvent.Arrive), 300));
            Assert.Equal(1.6, s.Lift.Position);
        }

        [Fact]
        public void PupilLift_HimAboardWithoutAPupil_HoldsMidway_L5720()
        {
            var s = new Dl15();
            s.Pupil.Engaged = true;
            Mech.Run(s.G, 50, null);
            Assert.Equal(1.6, s.Lift.Position);                              // the pupil alone does not send it
            for (int i = 0; i < 50; i++) s.G.Step(Dt, s.Pose());
            double y = s.Lift.Position;
            s.Pupil.Engaged = false;                                         // the pupil steps off mid-way: he holds it
            for (int i = 0; i < 50; i++) s.G.Step(Dt, s.Pose());
            Assert.Equal(y, s.Lift.Position);
            Assert.Equal(PupilLiftState.Still, s.Lift.State);
        }

        [Theory]
        [InlineData("sickbay", 1.6)]
        [InlineData("class6", 0.0)]
        [InlineData("dismissed", 1.6)]
        [InlineData("workshop", 1.6)]
        public void PupilLift_ResetFromCheckpoint_L5546(string cp, double y)
        {
            var s = new Dl15(cp);
            Assert.Equal(y, s.Lift.Position);
            Assert.Equal(y, s.Lift.FloorY);
        }

        [Fact]
        public void PupilLift_RestoredMidDescent_ContinuesIdentically()
        {
            var a = new Dl15();
            a.Pupil.Engaged = true;
            Mech.Run(a.G, 40, a.Pose());
            var b = new Dl15("class6");
            AssertRestoreContinues(a.G, b.G, 140, k => a.Pose());
        }

        [Fact]
        public void PupilLift_DoesNotCarryHimWhileAirborne_GameGrounded_L5724()
        {
            var s = new Dl15();
            s.G.Step(Dt, Mech.Pose(281.9, s.Lift.FloorY, grounded: false));
            Assert.False(s.Lift.Carrying);
            s.G.Step(Dt, s.Pose());
            Assert.True(s.Lift.Carrying);
        }

        /// <summary>The steps (1-based) on which <paramref name="id"/> emitted <paramref name="evt"/>, and the states it was in.</summary>
        private static List<int> EventSteps<T>(MechanismGraph g, MechanismId id, T evt, int steps, Func<PlayerPose> pose = null,
            Action<int> after = null) where T : struct, Enum
        {
            var list = new List<int>();
            for (int i = 1; i <= steps; i++)
            {
                g.Step(Dt, pose?.Invoke() ?? PlayerPose.Away);
                if (Mech.Emitted(g, id, evt)) { list.Add(i); after?.Invoke(i); }
            }
            return list;
        }

        [Fact]
        public void Relocation_SqueaksAtRandomOnlyWhileMoving_SeededAndReplayedOnReset_L4637()
        {
            List<int> Run(Dl10 s)
            {
                s.Lift.PressUp(false);
                return EventSteps(s.G, "dl10.lift", RelocationLiftEvent.Squeak, 900, after: _ =>
                    Assert.True(s.Lift.State == RelocationLiftState.Up || s.Lift.State == RelocationLiftState.Down));
            }
            var a = new Dl10();
            var first = Run(a);
            Assert.InRange(first.Count, 6, 40);                                 // 1.5 /s over 11 s of travel
            Assert.Equal(first, Run(new Dl10()));                               // same seed, same squeaks
            a.G.Reset(Mech.Cp("uponly"));
            Assert.Equal(first, Run(a));                                        // a reload replays them
        }

        [Fact]
        public void PupilLift_RatchetsAtRandomOnlyWhileMoving_L5722()
        {
            var s = new Dl15();
            Assert.Empty(EventSteps(s.G, "dl15.lift", PupilLiftEvent.Ratchet, 120, s.Pose));   // still at the top
            s.Pupil.Engaged = true;
            var r = EventSteps(s.G, "dl15.lift", PupilLiftEvent.Ratchet, 200, s.Pose,
                _ => Assert.Equal(PupilLiftState.Descending, s.Lift.State));
            Assert.InRange(r.Count, 3, 30);                                     // 5 /s over 2.46 s
        }

        [Fact]
        public void RackCw_RatchetsAtRandomOnlyWhileLifting_L5766()
        {
            var latch = new TestSource("dl16.latch");
            var cw = new CounterweightRack("dl16.rackCW", CounterweightRackParams.Dl16RackCw());
            var g = Mech.Graph("crossing", latch, cw);
            Assert.Empty(EventSteps(g, "dl16.rackCW", CounterweightRackEvent.Ratchet, 60));
            latch.Engaged = true;
            var r = EventSteps(g, "dl16.rackCW", CounterweightRackEvent.Ratchet, 300);
            Assert.InRange(r.Count, 3, 30);                                     // 6 /s over 1.8 s
            Assert.All(r, i => Assert.True(i <= 108));
        }

        // ---- CounterweightRack (dl16.rackCW) ----------------------------------------------------------------------------

        [Fact]
        public void RackCw_LiftsTwoMetresOver1_8s_OnceLatched_ClearsTheLaneAt0_75_L5766_L5608_L5839()
        {
            var latch = new TestSource("dl16.latch");
            var cw = new CounterweightRack("dl16.rackCW", CounterweightRackParams.Dl16RackCw());
            var g = Mech.Graph("crossing", latch, cw);
            Mech.Run(g, 30);
            Assert.Equal(0, cw.Position);
            latch.Engaged = true;
            int clear = -1, up = -1;
            for (int i = 1; i <= 200; i++)
            {
                g.Step(Dt, PlayerPose.Away);
                if (i == 1) Assert.True(Mech.Entered(g, "dl16.rackCW", CounterweightRackState.Lifting));
                if (clear < 0 && cw.Engaged) clear = i;
                if (Mech.Entered(g, "dl16.rackCW", CounterweightRackState.Up)) up = i;
            }
            Assert.InRange(clear, 81, 82);                                   // 0.75 · 1.8 s
            Assert.Equal(108, up);
            Assert.Equal(2.0, cw.Position);
        }

        [Theory]
        [InlineData("crossing", 0.0, CounterweightRackState.Down)]
        [InlineData("store", 2.0, CounterweightRackState.Up)]
        public void RackCw_ResetFromCheckpoint_L5551(string cp, double y, CounterweightRackState state)
        {
            var cw = new CounterweightRack("dl16.rackCW", CounterweightRackParams.Dl16RackCw());
            Mech.Graph(cp, new TestSource("dl16.latch"), cw);
            Assert.Equal(y, cw.Position);
            Assert.Equal(state, cw.State);
            Assert.Equal(y > 0, cw.Engaged);
        }

        [Fact]
        public void RackCw_WithTheRealLatch_FullRackLatches1_2sLater_ThenLifts_L5764_L5766()
        {
            var rack = new TestSource("dl16.rack");
            var latch = new Latch("dl16.latch", new LatchParams { Trigger = "dl16.rack", Threshold = 1, Delay = 1.2, ReleasedAfter = "store" });
            var cw = new CounterweightRack("dl16.rackCW", CounterweightRackParams.Dl16RackCw());
            var g = Mech.Graph("crossing", rack, latch, cw);
            rack.Position = 1;
            int up = StepsUntilEntered(g, "dl16.rackCW", CounterweightRackState.Up, max: 400);
            Assert.InRange(up, 72 + 108, 73 + 108);
        }

        [Fact]
        public void RackCw_RestoredMidLift_ContinuesIdentically()
        {
            var la = new TestSource("dl16.latch") { Engaged = true };
            var a = new CounterweightRack("dl16.rackCW", CounterweightRackParams.Dl16RackCw());
            var ga = Mech.Graph("crossing", la, a);
            Mech.Run(ga, 40);
            var gb = Mech.Graph("store", new TestSource("dl16.latch"), new CounterweightRack("dl16.rackCW", CounterweightRackParams.Dl16RackCw()));
            AssertRestoreContinues(ga, gb, 80);
        }

        // ---- Dumbwaiter (dl16a.car) -------------------------------------------------------------------------------------

        private sealed class Dl16a
        {
            public readonly TestSource Load = new TestSource("dl16a.carLoad");
            public readonly Dumbwaiter Car;
            public readonly MechanismGraph G;
            public Dl16a(double need = 0, string cp = "kitchen")
            {
                var p = DumbwaiterParams.Dl16aCar();
                p.Need = need;
                Car = new Dumbwaiter("dl16a.car", p);
                G = Mech.Graph(cp, Load, Car);
            }
            public PlayerPose InCar() => Mech.Pose(313.0, Car.FloorY);
        }

        [Fact]
        public void Dumbwaiter_StartsAtTheTop_CallBringsItDownOver4_2s_L5919_L6146_L6237()
        {
            var s = new Dl16a();
            Assert.Equal(DumbwaiterState.Top, s.Car.State);
            Assert.Equal(2.45, s.Car.Position);
            s.Car.Call();
            s.G.Step(Dt, PlayerPose.Away);
            Assert.True(Mech.Entered(s.G, "dl16a.car", DumbwaiterState.Down));
            // 253 steps: 252 sum to 4.1999999…, short of 4.2 (F.mt >= 4.2, L6237), as the chapter 1 trace has it (#17153).
            Assert.Equal(252, StepsUntilEntered(s.G, "dl16a.car", DumbwaiterState.Bottom));
            Assert.Equal(0.05, s.Car.Position);
            Assert.Equal(1, Find(s.G, "dl16a.car", DumbwaiterEvent.Arrive).Value.Index);
            s.Car.Call();                                                    // at the bottom: only the ding
            s.G.Step(Dt, PlayerPose.Away);
            Assert.Equal(DumbwaiterState.Bottom, s.Car.State);
        }

        [Fact]
        public void Dumbwaiter_RightLoad_RisesOver4_2s_CarryingHim_L6175_L6236()
        {
            var s = new Dl16a();
            s.Car.Call();
            Mech.Run(s.G, 260);
            s.Car.Bell();
            s.G.Step(Dt, s.InCar());
            Assert.True(Mech.Entered(s.G, "dl16a.car", DumbwaiterState.Rise));
            Assert.True(s.Car.Carrying);
            int top = -1;
            for (int i = 2; i <= 300 && top < 0; i++)
            {
                s.G.Step(Dt, s.InCar());
                if (Mech.Entered(s.G, "dl16a.car", DumbwaiterState.Top)) top = i;
                else Assert.True(s.Car.Carrying && s.Car.FloorVelocity >= 0);
            }
            Assert.Equal(253, top);                                         // 252 steps sum to 4.1999999… (L6236; the trace, #17469)
            Assert.Equal(2.45, s.Car.Position);
            Assert.Equal(0, Find(s.G, "dl16a.car", DumbwaiterEvent.Arrive).Value.Index);
            s.G.Step(Dt, s.InCar());
            Assert.False(s.Car.Carrying);                                    // stopped: the ride is over
        }

        [Fact]
        public void Dumbwaiter_TooHeavy_BuzzesAndStays_L6173()
        {
            var s = new Dl16a();
            s.Car.Call();
            Mech.Run(s.G, 260);
            s.Load.Load = 1;
            s.Car.Bell();
            s.G.Step(Dt, PlayerPose.Away);
            Assert.Equal(1, Find(s.G, "dl16a.car", DumbwaiterEvent.Over).Value.Value);
            Assert.Equal(DumbwaiterState.Bottom, s.Car.State);
        }

        [Fact]
        public void Dumbwaiter_TooLight_ShootsCatchesAndIsLowered_L6174_L6238_L6244()
        {
            var s = new Dl16a(need: 1);
            s.Car.Call();
            Mech.Run(s.G, 260);
            s.Car.Bell();
            s.G.Step(Dt, PlayerPose.Away);
            Assert.True(Mech.Entered(s.G, "dl16a.car", DumbwaiterState.Shoot));
            int caught = -1, bottom = -1;
            double max = 0, atCatch = 0;
            for (int i = 2; i <= 300 && bottom < 0; i++)
            {
                s.G.Step(Dt, PlayerPose.Away);
                max = Math.Max(max, s.Car.Position);
                if (Mech.Emitted(s.G, "dl16a.car", DumbwaiterEvent.CatchBite)) { caught = i; atCatch = s.Car.Position; }
                if (Mech.Entered(s.G, "dl16a.car", DumbwaiterState.Bottom)) bottom = i;
            }
            Assert.Equal(48, caught);                                        // 0.8 s
            Assert.Equal(0.05 + 1.5 * Math.Pow(47.0 / 48, 1.6), atCatch, 9);  // held where the last rise step left it
            Assert.Equal(241, bottom);                                       // > 4.0 s
            Assert.InRange(max, 1.549, 1.55);
            Assert.Equal(0.05, s.Car.Position);
        }

        [Fact]
        public void Dumbwaiter_BellAtTheTop_SendsItDown_ButNotWhileMoving_L5995_L6172()
        {
            var s = new Dl16a();
            s.Car.Bell();
            s.G.Step(Dt, PlayerPose.Away);
            Assert.Equal(DumbwaiterState.Down, s.Car.State);
            Mech.Run(s.G, 10);
            double h = s.Car.Position;
            s.Car.Bell();
            s.Car.Call();
            s.G.Step(Dt, PlayerPose.Away);
            Assert.Equal(DumbwaiterState.Down, s.Car.State);
            Assert.True(s.Car.Position < h);
        }

        [Fact]
        public void Dumbwaiter_ResetFromAnyCheckpoint_IsAtTheTop_L5919()
        {
            var s = new Dl16a(cp: "workshop");
            Assert.Equal(DumbwaiterState.Top, s.Car.State);
            Assert.Equal(2.45, s.Car.FloorY);
            s.Car.Call();
            Mech.Run(s.G, 30);
            s.G.Reset(Mech.Cp("kitchen"));
            Assert.Equal(DumbwaiterState.Top, s.Car.State);
            Assert.Equal(2.45, s.Car.Position);
        }

        [Fact]
        public void Dumbwaiter_RestoredMidShoot_ContinuesIdentically()
        {
            var a = new Dl16a(need: 1);
            a.Car.Call();
            Mech.Run(a.G, 260);
            a.Car.Bell();
            Mech.Run(a.G, 70);                                               // caught, waiting to be lowered
            var b = new Dl16a(need: 1);
            AssertRestoreContinues(a.G, b.G, 200);
            Assert.Equal(DumbwaiterState.Bottom, b.Car.State);
        }
    }
}
