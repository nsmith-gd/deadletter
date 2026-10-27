using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Drives;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>Paired outputs and clutch (§4.13g): the wind crank and the paired blind drive of DL-14 and DL-14a.</summary>
    public class DriveTests
    {
        private const int TravelSteps = 132;                         // 2.2 s at 60 Hz

        private sealed class Rig
        {
            public readonly TestSource Crank, Hold;
            public readonly PairedBlindDrive Drive;
            public readonly MechanismGraph G;

            public Rig(PairedBlindParams p, string checkpoint, bool held)
            {
                Crank = new TestSource(p.Crank.Value);
                Hold = new TestSource(p.Hold.Value) { Engaged = held };
                Drive = new PairedBlindDrive(p.Crank.Value.StartsWith("dl14a") ? "dl14a.blinds" : "dl14.blinds", p);
                G = Mech.Graph(checkpoint, Crank, Hold, Drive);
            }

            /// <summary>One wind, then the chain runs for <paramref name="steps"/> steps (the wind lands on the first).</summary>
            public void Wind(int steps = TravelSteps + 2)
            {
                Crank.Position += 1;
                Mech.Run(G, 1);
                Mech.Run(G, steps - 1);
            }
        }

        private static Rig Dl14(string cp = "window", bool jammed = true) => new Rig(PairedBlindParams.Dl14Blinds(), cp, jammed);
        private static Rig Dl14a(string cp = "dorm", bool held = false) => new Rig(PairedBlindParams.Dl14aBlinds(), cp, held);

        // ---- WindCrank -----------------------------------------------------------------------------------------------

        [Fact]
        public void WindCrank_OneWindAt0_3s_RatchetAt0_9_ActEndsAfter1_5s_L5364_L5376()
        {
            var crank = new WindCrank("dl14.crank", WindCrankParams.Dl14Crank());
            var g = Mech.Graph("window", crank);
            int wind = -1, ratchet = -1, idle = -1;
            int steps = Mech.PlayAct(g, crank, onStep: (k, f) =>
            {
                if (Mech.Emitted(g, "dl14.crank", WindCrankEvent.Wind)) wind = k;
                if (Mech.Emitted(g, "dl14.crank", WindCrankEvent.Ratchet)) ratchet = k;
            });
            Assert.Equal(19, wind);                                  // a.t > 0.3: 19/60
            Assert.Equal(55, ratchet);                               // a.t > 0.9
            Assert.Equal(91, steps);                                 // a.t > 1.5 ends it
            Assert.Equal(1, crank.Position);
            Assert.Equal(WindCrankState.Winding, crank.State);
            Mech.Run(g, 1);
            Assert.Equal(WindCrankState.Idle, crank.State);
            Mech.PlayAct(g, crank, onStep: (k, f) => { if (Mech.Emitted(g, "dl14.crank", WindCrankEvent.Wind)) idle = k; });
            Assert.Equal(19, idle);
            Assert.Equal(2, crank.Position);                          // one wind per act
            g.Reset(Mech.Cp("window"));
            Assert.Equal(0, crank.Position);
        }

        [Theory]
        [InlineData(242.18, 0.0, true)] [InlineData(242.05, 0.0, true)] [InlineData(242.03, 0.0, false)] [InlineData(242.75, 0.0, true)]
        [InlineData(242.77, 0.0, false)] [InlineData(242.4, 0.1, false)]
        public void WindCrank_Dl14_AnswersWithin0_36OfTheCrank_OnTheFloor_L5291(double x, double y, bool answers)
        {
            var crank = new WindCrank("dl14.crank", WindCrankParams.Dl14Crank());
            Mech.Graph("window", crank);
            var q = new InteractionQuery(x, y, 0, 1, true, false, HoldKind.None, null, null);
            Assert.Equal(answers, crank.IsAvailable(q));
            Assert.Equal(242.18, crank.Station.StandX, 9);           // ATT.crankX − 0.22, L5298
        }

        [Fact]
        public void WindCrank_Dl14a_StandsShortOfItsCrank_L6006()
        {
            var crank = new WindCrank("dl14a.crank", WindCrankParams.Dl14aCrank());
            Assert.Equal(258.48, crank.Station.StandX, 9);
            Assert.Equal(258.7, crank.Station.ReachX, 9);
        }

        // ---- DL-14: the jam, the slip, the peel -----------------------------------------------------------------------

        [Fact]
        public void Dl14_FirstWindWithThePoleIn_SendsBDownAlone_ClutchSlips_L5368()
        {
            var r = Dl14();
            r.Crank.Position = 1;
            Mech.Run(r.G, 1);
            Assert.True(Mech.Emitted(r.G, "dl14.blinds", PairedBlindEvent.Wind));
            Assert.True(Mech.Emitted(r.G, "dl14.blinds", PairedBlindEvent.FirstSlip));
            Assert.Equal(PairedBlindState.Slipping, r.Drive.State);
            Assert.Equal(0, r.Drive.TargetA);
            Assert.Equal(1, r.Drive.TargetB);
            Assert.Equal(1.0 / TravelSteps, r.Drive.B, 9);                  // dt / 2.2 per step, L5440
            Assert.Equal(0, r.Drive.A);
            Assert.Equal(9.0 / 60, r.Drive.ClutchRad, 12);                   // spins at 9 rad/s, wheel A held (L5473)
            Assert.True(r.Drive.Slipping);
        }

        [Fact]
        public void Dl14_GrindEvery0_32sWhileSlipping_FirstSlipOnce_L5451_L5459()
        {
            var r = Dl14();
            r.Crank.Position = 1;
            var grinds = new List<int>();
            int firstSlips = 0;
            for (int i = 1; i <= TravelSteps + 10; i++)
            {
                Mech.Run(r.G, 1);
                if (Mech.Emitted(r.G, "dl14.blinds", PairedBlindEvent.Grind)) grinds.Add(i);
                if (Mech.Emitted(r.G, "dl14.blinds", PairedBlindEvent.FirstSlip)) firstSlips++;
            }
            Assert.Equal(1, firstSlips);
            Assert.Equal(20, grinds[0]);                                      // grindT > 0.32: 20/60
            for (int k = 1; k < grinds.Count; k++) Assert.Equal(20, grinds[k] - grinds[k - 1]);
            Assert.Equal(6, grinds.Count);                                    // 2.2 s of slipping
            Assert.Equal(PairedBlindState.Still, r.Drive.State);
            Assert.Equal(1.0, r.Drive.B);
            Assert.Equal((TravelSteps - 1) * 9.0 / 60, r.Drive.ClutchRad, 9);   // slipping until B is within 1e-3 (L5446)
        }

        [Fact]
        public void Dl14_BPast0_9_PeelsThePanelOver1_6s_AndCuesChild_L5474_L5475()
        {
            var r = Dl14();
            r.Crank.Position = 1;
            int peel = Mech.RunUntil(r.G, () => Mech.Emitted(r.G, "dl14.blinds", PairedBlindEvent.Peel));
            Assert.Equal(119, peel);                                          // B = 119/132 > 0.9
            Assert.Equal(1.0 / 96, r.Drive.Peel, 12);                         // += dt / 1.6 on the same step
            Mech.Run(r.G, 94);
            Assert.True(r.Drive.Peel < 1);
            Mech.Run(r.G, 1);
            Assert.Equal(1.0, r.Drive.Peel, 12);
            Mech.Run(r.G, 200);
            Assert.False(Mech.Emitted(r.G, "dl14.blinds", PairedBlindEvent.Peel));
        }

        [Theory]
        // unheld: A goes up as B comes down only from (A down, B up); otherwise A comes down as B goes up (L5369–L5370)
        [InlineData(0, 0, false, 1, 0)] [InlineData(1, 0, false, 0, 1)] [InlineData(0, 1, false, 1, 0)] [InlineData(1, 1, false, 1, 0)]
        // held: B goes the other way alone, A stays wherever it is (L5368)
        [InlineData(0, 0, true, 0, 1)] [InlineData(1, 1, true, 1, 0)] [InlineData(1, 0, true, 1, 1)] [InlineData(0, 1, true, 0, 0)]
        public void Dl14_WindRule_L5366_L5370(int a, int b, bool held, int ta, int tb)
        {
            var r = Dl14(jammed: held);
            Drive(r, a, b);
            r.Hold.Engaged = held;
            r.Wind();
            Assert.Equal(ta, r.Drive.A, 12);
            Assert.Equal(tb, r.Drive.B, 12);
        }

        /// <summary>Puts the blinds at (a, b) with real winds (the hold toggled as needed).</summary>
        private static void Drive(Rig r, int a, int b)
        {
            bool held = r.Hold.Engaged;
            for (int guard = 0; guard < 6 && (Math.Abs(r.Drive.A - a) > 1e-9 || Math.Abs(r.Drive.B - b) > 1e-9); guard++)
            {
                // move A with an unheld wind if A is wrong, else B alone with a held one
                r.Hold.Engaged = Math.Abs(r.Drive.A - a) < 1e-9;
                r.Wind();
            }
            Assert.Equal(a, r.Drive.A, 12);
            Assert.Equal(b, r.Drive.B, 12);
            r.Hold.Engaged = held;
        }

        [Fact]
        public void Dl14_TheSolution_JamUnjamJam_BothDown_LedgesOut_L5261_L5262()
        {
            var r = Dl14();
            r.Wind();                                                    // B down alone; the panel peels
            Assert.True(r.Drive.Peeled);
            Assert.False(r.Drive.LedgeOut(0));
            Assert.True(r.Drive.LedgeOut(1));
            r.Hold.Engaged = false;                                      // draw the pole out
            r.Wind();                                                    // A comes down as B goes up
            Assert.Equal(1, r.Drive.A, 12);
            Assert.Equal(0, r.Drive.B, 12);
            Assert.Equal(PairedBlindState.Still, r.Drive.State);
            r.Hold.Engaged = true;                                       // the pole back in, A held down
            r.Wind();
            Assert.Equal(1, r.Drive.A, 12);
            Assert.Equal(1, r.Drive.B, 12);
            Assert.Equal(3, r.Drive.Winds);
            Assert.True(r.Drive.Engaged);
            // ledges: solid only once out, and to someone above the level below (boards in the air)
            Assert.Equal(1.1, r.Drive.SurfaceAt(237.0, 0.6, 0));
            Assert.Equal(0, r.Drive.SurfaceAt(237.0, 0.4, 0));
            Assert.Equal(1.6, r.Drive.SurfaceAt(238.4, 1.1, 0));
            Assert.Equal(1.1, r.Drive.SurfaceAt(238.4, 0.9, 1.1));
            Assert.Equal(0, r.Drive.SurfaceAt(239.1, 1.7, 0));
        }

        [Theory]
        [InlineData(0.75, 0)] [InlineData(0.875, 0.5)] [InlineData(1.0, 1)] [InlineData(0.5, 0)]
        public void Dl14_LedgeFoldsOutFrom0_75_L5441(double v, double deploy)
        {
            var r = Dl14();
            // drive B partway: a held wind, stopped when B reaches v
            r.Crank.Position = 1;
            Mech.RunUntil(r.G, () => r.Drive.B >= v - 1e-9, 400);
            double expected = deploy;
            if (v > 0 && v < 1) expected = Maths.Smooth.Step((r.Drive.B - 0.75) / 0.25);
            Assert.Equal(expected, r.Drive.LedgeDeploy(1), 9);
            Assert.Equal(0, r.Drive.LedgeDeploy(0));
        }

        [Fact]
        public void Dl14_LedgeIsSolidOnlyAtOrPast0_95()
        {
            var r = Dl14();
            r.Crank.Position = 1;
            Mech.RunUntil(r.G, () => r.Drive.B >= 0.94);
            Assert.False(r.Drive.LedgeOut(1));
            Assert.Equal(0, r.Drive.SurfaceAt(238.4, 1.1, 0));
            Mech.RunUntil(r.G, () => r.Drive.B >= 0.95);
            Assert.True(r.Drive.LedgeOut(1));
        }

        [Fact]
        public void Dl14_ClutchTurnsWithWheelA_WhenFree_L5473()
        {
            var r = Dl14(jammed: false);
            r.Wind();
            Assert.Equal(1, r.Drive.A, 12);
            Assert.Equal(6, r.Drive.ClutchRad, 12);
            Assert.False(Mech.Emitted(r.G, "dl14.blinds", PairedBlindEvent.Grind));
        }

        [Theory]
        [InlineData("window", 0, 0, 0, false, PairedBlindState.Still)]
        [InlineData("gallery13", 0, 0, 0, false, PairedBlindState.Still)]
        [InlineData("hatch14", 1, 1, 3, true, PairedBlindState.Still)]
        [InlineData("dorm", 1, 1, 3, true, PairedBlindState.Still)]
        public void Dl14_ResetFromCheckpoint_L5237_L5238(string cp, double a, double b, int winds, bool peeled, PairedBlindState state)
        {
            var r = Dl14();
            r.Wind(40);                                                  // mid-motion before the reset
            r.G.Reset(Mech.Cp(cp));
            Assert.Equal(a, r.Drive.A);
            Assert.Equal(b, r.Drive.B);
            Assert.Equal(winds, r.Drive.Winds);
            Assert.Equal(peeled, r.Drive.Peeled);
            Assert.Equal(peeled ? 1 : 0, r.Drive.Peel);
            Assert.Equal(state, r.Drive.State);
            Assert.Equal(0, r.Drive.ClutchRad - (r.Drive.Held ? 0 : a * 6));
            // a reset does not replay a wind already counted by the crank
            Mech.Run(r.G, 5);
            Assert.False(Mech.Emitted(r.G, "dl14.blinds", PairedBlindEvent.Wind));
        }

        // ---- DL-14a: the bag on W1's hook, the gown -----------------------------------------------------------------

        [Theory]
        // unheld: decided by A alone (L6089–L6090)
        [InlineData(0, 0, false, 1, 0)] [InlineData(1, 0, false, 0, 1)] [InlineData(0, 1, false, 1, 0)] [InlineData(1, 1, false, 0, 1)]
        // held by the bag: W2 goes alone, and W1 is pulled fully down (L6088, L6223)
        [InlineData(0, 0, true, 1, 1)] [InlineData(1, 1, true, 1, 0)] [InlineData(1, 0, true, 1, 1)]
        public void Dl14a_WindRule_L6086_L6090(int a, int b, bool held, int ta, int tb)
        {
            var r = Dl14a();
            r.Hold.Engaged = false;
            if (a == 1 && b == 1) { r.Hold.Engaged = true; r.Wind(); r.Hold.Engaged = false; }   // (1, 1) via the bag
            else Drive14a(r, a, b);
            r.Hold.Engaged = held;
            r.Wind();
            Assert.Equal(ta, r.Drive.A, 12);
            Assert.Equal(tb, r.Drive.B, 12);
        }

        private static void Drive14a(Rig r, int a, int b)
        {
            if (a == 0 && b == 0) return;
            if (a == 1 && b == 0) { r.Wind(); return; }
            if (a == 0 && b == 1) { r.Wind(); r.Wind(); return; }
        }

        [Fact]
        public void Dl14a_TheBagPullsW1DownAtOnce_L6223()
        {
            var r = Dl14a();
            r.Hold.Engaged = true;
            Mech.Run(r.G, 1);
            Assert.Equal(1, r.Drive.A);
            Assert.Equal(1, r.Drive.TargetA);
            Assert.Equal(0.75, r.Drive.HookY, 12);                       // hook14a(1)
            Assert.Equal(1.93, r.Drive.HemY, 12);
        }

        [Fact]
        public void Dl14a_GownRidesUpWithW1_AndTheSecondFreeWindIsAWrongTry_L6090_L6091()
        {
            var r = Dl14a();
            r.Wind();                                                    // W1 down, W2 up: the first try
            Assert.False(Mech.Emitted(r.G, "dl14a.blinds", PairedBlindEvent.WrongTry));
            Assert.Equal(1, r.Drive.A, 12);
            r.Crank.Position += 1;
            Mech.Run(r.G, 1);
            Assert.True(Mech.Emitted(r.G, "dl14a.blinds", PairedBlindEvent.ARaised));   // the light gown rides up with W1
            Assert.True(Mech.Emitted(r.G, "dl14a.blinds", PairedBlindEvent.WrongTry));
            Mech.Run(r.G, TravelSteps);
            Assert.Equal(2.0, r.Drive.HookY, 12);                        // hook14a(0)
            Assert.Equal(3.21, r.Drive.HemY, 12);
            r.Hold.Engaged = true;                                       // the bag: no wrong try
            r.Crank.Position += 1;
            Mech.Run(r.G, 1);
            Assert.False(Mech.Emitted(r.G, "dl14a.blinds", PairedBlindEvent.WrongTry));
            Assert.Equal(PairedBlindState.Slipping, r.Drive.State);
            Assert.Equal(1, r.Drive.A);                                  // W1 pulled down at once; W2 goes up alone
            Assert.Equal(0, r.Drive.TargetB);
            Assert.False(Mech.Emitted(r.G, "dl14a.blinds", PairedBlindEvent.Grind));    // DL-14a has no grind
            Mech.Run(r.G, TravelSteps);
            Assert.False(r.Drive.Engaged);
            r.Crank.Position += 1;                                       // and once more: W2 down too
            Mech.Run(r.G, TravelSteps + 1);
            Assert.True(r.Drive.Engaged);                                // both down: the night light can go dark
        }

        [Theory]
        [InlineData("dorm", 0, false)] [InlineData("hatch14", 0, false)] [InlineData("corridor", 1, true)] [InlineData("workshop", 1, true)]
        public void Dl14a_ResetFromCheckpoint_L5914(string cp, double v, bool engaged)
        {
            var r = Dl14a();
            r.Wind(30);
            r.G.Reset(Mech.Cp(cp));
            Assert.Equal(v, r.Drive.A);
            Assert.Equal(v, r.Drive.B);
            Assert.Equal(0, r.Drive.Winds);
            Assert.Equal(engaged, r.Drive.Engaged);
            Assert.False(r.Drive.Peeled);
        }

        // ---- Snapshot and determinism --------------------------------------------------------------------------------

        [Fact]
        public void Dl14_RestoredMidSlip_ContinuesBitIdentically()
        {
            var a = Dl14();
            a.Crank.Position = 1;
            Mech.Run(a.G, 50);
            Assert.Equal(PairedBlindState.Slipping, a.Drive.State);
            var b = Dl14("hatch14", jammed: false);
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            for (int i = 0; i < 300; i++)
            {
                if (i == 150) { a.Hold.Engaged = b.Hold.Engaged = false; a.Crank.Position += 1; b.Crank.Position += 1; }
                Mech.Run(a.G, 1);
                Mech.Run(b.G, 1);
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
                Assert.Equal(Mech.Events(a.G).Count, Mech.Events(b.G).Count);
            }
            Assert.True(a.Drive.Peeled);
        }

        [Fact]
        public void PairedBlinds_TwoRunsWithTheSameWinds_AreBitIdentical()
        {
            var runs = new List<string>[2];
            for (int k = 0; k < 2; k++)
            {
                var r = Dl14();
                var trace = runs[k] = new List<string>();
                for (int i = 0; i < 900; i++)
                {
                    if (i % 170 == 0) r.Crank.Position += 1;
                    if (i % 340 == 100) r.Hold.Engaged = !r.Hold.Engaged;
                    Mech.Run(r.G, 1);
                    trace.Add(Mech.Dump(r.G));
                }
            }
            Assert.Equal(runs[0], runs[1]);
        }
    }
}
