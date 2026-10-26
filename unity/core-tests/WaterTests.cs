using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Water;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>Water, floods and floats (§4.13i): DL-17's sluice rig and float latch, DL-11's flood.</summary>
    public class WaterTests
    {
        private static InteractionQuery At(double x, double y = 0) => new InteractionQuery(x, y, 0, 1, true, false, HoldKind.None, null, null);

        // ---- Sluice ---------------------------------------------------------------------------------------------------------

        [Fact]
        public void Sluice_EachPullToggles_0_35sIn_ActOverAfter1s_L6194_L6195()
        {
            var s = new Sluice("dl17.sluiceA", SluiceParams.Dl17Sluice(0));
            var g = Mech.Graph("workshop", s);
            Assert.Equal(SluiceState.Open, s.State);
            Assert.Equal("Pull", s.Profile.Clip);
            double at = -1;
            int clunks = 0;
            int steps = Mech.PlayAct(g, s, onStep: (k, f) =>
            {
                if (Mech.Entered(g, "dl17.sluiceA", SluiceState.Shut)) at = k * Mech.Dt;
                if (Mech.Emitted(g, "dl17.sluiceA", SluiceEvent.Clunk)) clunks++;
            });
            Assert.InRange(at, 0.35, 0.35 + Mech.Dt + 1e-9);
            Assert.Equal(1, clunks);
            Assert.InRange(steps * Mech.Dt, 1.0, 1.0 + Mech.Dt + 1e-9);
            Assert.False(s.Engaged);
            Mech.Run(g, 3);
            Mech.PlayAct(g, s);
            Assert.True(s.Engaged);
        }

        [Fact]
        public void Sluice_StandsShortOfIt_AnswersWithin0_24_FromTheFloor_L5998_L6009()
        {
            for (int i = 0; i < 3; i++)
            {
                var s = new Sluice("dl17.sluiceA", SluiceParams.Dl17Sluice(i));
                double x = SluiceRigParams.Dl17SluiceX[i];
                Assert.Equal(x - 0.18, s.StandX, 12);
                Assert.True(s.IsAvailable(At(x + 0.23)));
                Assert.False(s.IsAvailable(At(x - 0.25)));
                Assert.False(s.IsAvailable(At(x, 0.06)));
            }
        }

        [Theory]
        [InlineData("start")] [InlineData("kitchen")] [InlineData("workshop")]
        public void Sluice_EveryResetOpensIt_L5923(string cp)
        {
            var s = new Sluice("dl17.sluiceB", SluiceParams.Dl17Sluice(1));
            var g = Mech.Graph(cp, s);
            Mech.PlayAct(g, s);
            Assert.False(s.Engaged);
            g.Reset(Mech.Cp(cp));
            Assert.True(s.Engaged);
        }

        // ---- Valve ----------------------------------------------------------------------------------------------------------

        [Fact]
        public void Valve_TurnsOnceAt0_4s_ActOverAt1_5s_L6200_L6207()
        {
            var v = new SluiceValve("dl17.valve", SluiceValveParams.Dl17Valve());
            var g = Mech.Graph("workshop", v);
            Assert.Equal("Crank", v.Profile.Clip);
            var pulses = new List<double>();
            int steps = Mech.PlayAct(g, v, onStep: (k, f) =>
            {
                Assert.Equal(SluiceValveState.Turning, v.State);
                if (v.Engaged) { pulses.Add(k * Mech.Dt); Assert.True(Mech.Emitted(g, "dl17.valve", SluiceValveEvent.Turn)); }
            });
            Assert.Single(pulses);
            Assert.InRange(pulses[0], 0.4, 0.4 + Mech.Dt + 1e-9);
            Assert.InRange(steps * Mech.Dt, 1.5, 1.5 + Mech.Dt + 1e-9);
            Mech.Run(g, 1);
            Assert.Equal(SluiceValveState.Idle, v.State);
            Assert.False(v.Engaged);
        }

        [Fact]
        public void Valve_StandsShortOfIt_AnswersWithin0_26_L5999_L6007()
        {
            var v = new SluiceValve("dl17.valve", SluiceValveParams.Dl17Valve());
            Assert.Equal(336.35, v.StandX, 12);
            Assert.Equal(336.55, v.AnchorX, 12);
            Assert.True(v.IsAvailable(At(336.55 - 0.25)));
            Assert.False(v.IsAvailable(At(336.55 + 0.27)));
        }

        // ---- SluiceRig ------------------------------------------------------------------------------------------------------

        private sealed class Rig
        {
            public readonly TestSource Valve = new TestSource("dl17.valve");
            public readonly TestSource[] S = { new TestSource("dl17.sluiceA"), new TestSource("dl17.sluiceB"), new TestSource("dl17.sluiceC") };
            public readonly TestSource Latch = new TestSource("dl17.latch");
            public readonly SluiceRig R = new SluiceRig("dl17.rig", SluiceRigParams.Dl17Rig());
            public readonly MechanismGraph G;

            public Rig(bool a = true, bool b = true, bool c = true, string cp = "workshop")
            {
                S[0].Engaged = a; S[1].Engaged = b; S[2].Engaged = c;
                G = Mech.Graph(cp, Valve, S[0], S[1], S[2], R, Latch);
            }

            /// <summary>Turns the valve for one step (the valve's pulse); returns that step's log.</summary>
            public List<MechanismEvent> Turn()
            {
                Valve.Engaged = true;
                Mech.Run(G, 1);
                Valve.Engaged = false;
                return Mech.Events(G);
            }

            public bool Logged(SluiceRigEvent e) => Mech.Emitted(G, "dl17.rig", e);
        }

        [Fact]
        public void Rig_FullTankAndAnOpenSluice_RunsFor6s_TankEmptiesLinearly_L6205_L6250()
        {
            var r = new Rig();
            Assert.Equal(SluiceRigState.Ready, r.R.State);
            r.Turn();
            Assert.True(r.Logged(SluiceRigEvent.Started));
            Assert.True(Mech.Entered(r.G, "dl17.rig", SluiceRigState.Running));
            Assert.True(r.R.Engaged);
            Assert.Equal(1 - Mech.Dt / 6, r.R.Tank, 12);             // the run's first step is the valve's step
            int n = Mech.RunUntil(r.G, () => r.Logged(SluiceRigEvent.Ended));
            Assert.InRange(n + 1, 359, 361);                           // 6 s of steps in all
            Assert.Equal(0, r.R.Tank);
            Assert.Equal(SluiceRigState.Refilling, r.R.State);
            Assert.True(r.R.Refilling);
        }

        [Fact]
        public void Rig_Refuses_LowTank_OrEverySluiceShut_AndIgnoresTurnsWhileRunning_L6202_L6204()
        {
            var shut = new Rig(false, false, false);
            shut.Turn();
            Assert.True(shut.Logged(SluiceRigEvent.RefusedShut));
            Assert.Equal(SluiceRigState.Ready, shut.R.State);

            var r = new Rig();
            r.Turn();
            Mech.Run(r.G, 30);
            var log = r.Turn();                                        // already running: nothing at all
            Assert.DoesNotContain(log, e => e.Id == "dl17.rig" && e.Kind == MechanismEventKind.Event);
            Mech.RunUntil(r.G, () => !r.R.Engaged);
            Mech.Run(r.G, 60 * 9);                                     // tank 0.9 after 9 s of refill
            r.Turn();
            Assert.True(r.Logged(SluiceRigEvent.RefusedLow));
            Mech.Run(r.G, 31);                                         // past 0.95: the valve works again
            r.Turn();
            Assert.True(r.Logged(SluiceRigEvent.Started));
        }

        [Fact]
        public void Rig_TankRefillsOver10s_ThenReady_L6255()
        {
            var r = new Rig();
            r.Turn();
            Mech.RunUntil(r.G, () => r.Logged(SluiceRigEvent.Ended));
            Mech.Run(r.G, 300);
            Assert.Equal(0.5, r.R.Tank, 9);
            int n = Mech.RunUntil(r.G, () => r.R.State == SluiceRigState.Ready);
            Assert.InRange(n, 299, 301);
            Assert.Equal(1, r.R.Tank);
            Assert.True(Mech.Entered(r.G, "dl17.rig", SluiceRigState.Ready));
        }

        [Theory]
        [InlineData(true, false, false, 2)]    // A waters bed 3
        [InlineData(false, true, false, 0)]    // B waters bed 1
        [InlineData(false, false, true, 1)]    // C waters bed 2
        public void Rig_OneSluiceFillsItsOwnBed_Feeds_L5905_L6251(bool a, bool b, bool c, int bed)
        {
            var r = new Rig(a, b, c);
            r.Turn();
            int full = Mech.RunUntil(r.G, () => r.R.Bed(bed) >= 0.95) + 1;
            Assert.InRange(full * Mech.Dt, 0.95 / 1.06 * 6 - Mech.Dt, 0.95 / 1.06 * 6 + Mech.Dt);
            Mech.RunUntil(r.G, () => !r.R.Engaged);
            Assert.InRange(r.R.Bed(bed), 1 - 2 * Mech.Dt / 20, 1);   // full (capped at 1), one drain step since the run ended
            for (int o = 0; o < 3; o++) if (o != bed) Assert.Equal(0, r.R.Bed(o));
            Assert.Equal(bed == 0, r.R.Position >= 0.95);              // the float is on bed 1
        }

        [Fact]
        public void Rig_ThreeOpenSluices_ShareTheTank_EachBedGets1_06Over3_L6251()
        {
            var r = new Rig();
            r.Turn();
            while (r.R.Engaged)
            {
                Mech.Run(r.G, 1);
                for (int b = 0; b < 3; b++) Assert.True(r.R.Fed(b) == r.R.Engaged);
            }
            for (int b = 0; b < 3; b++) Assert.InRange(r.R.Bed(b), 1.06 / 3 - 2 * Mech.Dt / 20, 1.06 / 3 + 1e-9);
            Assert.True(r.Logged(SluiceRigEvent.Failed));              // the float latch never lifted
        }

        [Fact]
        public void Rig_ASluiceShutMidRun_StopsItsStream_AndTheRestShare_L6249_L6256()
        {
            var r = new Rig();
            r.Turn();
            Mech.Run(r.G, 59);                                         // 1 s, three ways
            double b1 = r.R.Bed(0), b3 = r.R.Bed(2);
            r.S[0].Engaged = false;                                    // shut A: bed 3 now drains
            Mech.Run(r.G, 60);
            Assert.False(r.R.Fed(2));
            Assert.False(r.R.PipeFlow(0));
            Assert.True(r.R.PipeFlow(1));
            Assert.Equal(b3 - 60 * Mech.Dt / 20, r.R.Bed(2), 9);
            Assert.Equal(b1 + 60 * Mech.Dt / 6 / 2 * 1.06, r.R.Bed(0), 9);
        }

        [Fact]
        public void Rig_BedsDrainOver20s_WhenNotWatered_L6256()
        {
            var r = new Rig(false, true, false);
            r.Turn();
            Mech.RunUntil(r.G, () => !r.R.Engaged);
            double b = r.R.Bed(0);
            Mech.Run(r.G, 600);
            Assert.Equal(b - 600 * Mech.Dt / 20, r.R.Bed(0), 9);
            Assert.Equal(0.12 * r.R.Bed(0), r.R.FloatY, 12);           // L6311
            Mech.Run(r.G, 1200);
            Assert.Equal(0, r.R.Bed(0));
        }

        [Fact]
        public void Rig_FailedOnlyIfTheLatchIsDown_WhenTheRunEnds_L6254()
        {
            var r = new Rig(false, true, false);
            r.Turn();
            Mech.Run(r.G, 340);
            r.Latch.Engaged = true;
            Mech.RunUntil(r.G, () => r.Logged(SluiceRigEvent.Ended));
            Assert.False(r.Logged(SluiceRigEvent.Failed));
        }

        [Theory]
        [InlineData("start")] [InlineData("corridor")] [InlineData("workshop")]
        public void Rig_EveryResetFillsTheTankAndEmptiesTheBeds_L5923(string cp)
        {
            var r = new Rig();
            r.Turn();
            Mech.Run(r.G, 100);
            r.G.Reset(Mech.Cp(cp));
            Assert.Equal(SluiceRigState.Ready, r.R.State);
            Assert.Equal(1, r.R.Tank);
            for (int b = 0; b < 3; b++) Assert.Equal(0, r.R.Bed(b));
            Assert.Equal(0, r.G.Log.Count);
        }

        [Fact]
        public void Rig_RestoredMidRun_ContinuesBitIdentically()
        {
            var a = new Rig(true, true, false);
            a.Turn();
            Mech.Run(a.G, 150);
            var b = new Rig(false, false, false);
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            for (int k = 0; k < 900; k++)
            {
                Mech.Run(a.G, 1);
                Mech.Run(b.G, 1);
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            }
        }

        // ---- FloatLatch -----------------------------------------------------------------------------------------------------

        [Fact]
        public void FloatLatch_LatchesAt0_95_SwingsHomeOver0_8s_L6258_L6259()
        {
            var bed = new TestSource("dl17.rig");
            var l = new FloatLatch("dl17.latch", FloatLatchParams.Dl17Latch());
            var g = Mech.Graph("workshop", bed, l);
            bed.Position = 0.949;
            Mech.Run(g, 3);
            Assert.False(l.Engaged);
            Assert.Equal(70 * Maths.Smooth.Step(0.7 * 0.949), l.ArmDeg, 12);
            bed.Position = 0.95;
            Mech.Run(g, 1);
            Assert.True(Mech.Entered(g, "dl17.latch", FloatLatchState.Latched));
            Assert.True(Mech.Emitted(g, "dl17.latch", FloatLatchEvent.Clank));
            Assert.Equal(Mech.Dt / 0.8, l.Lift, 12);                   // swings on the step it latches
            int n = Mech.RunUntil(g, () => l.Lift >= 1);
            Assert.InRange(n + 1, 48, 49);
            Assert.Equal(70, l.ArmDeg, 12);
            bed.Position = 0;                                          // the water drains: it stays latched
            Mech.Run(g, 60);
            Assert.True(l.Engaged);
            Assert.Equal(70, l.ArmDeg, 12);
        }

        [Fact]
        public void FloatLatch_ASharedRunLiftsItPartWay_AndLetsItFall_L6314()
        {
            var bed = new TestSource("dl17.rig");
            var l = new FloatLatch("dl17.latch", FloatLatchParams.Dl17Latch());
            var g = Mech.Graph("workshop", bed, l);
            bed.Position = 1.06 / 3;
            Mech.Run(g, 1);
            double up = l.ArmDeg;
            Assert.InRange(up, 5, 15);
            bed.Position = 0.1;
            Mech.Run(g, 1);
            Assert.True(l.ArmDeg < up);
            Assert.Equal(FloatLatchState.Down, l.State);
        }

        [Theory]
        [InlineData("kitchen", null, FloatLatchState.Down)]
        [InlineData("workshop", null, FloatLatchState.Down)]           // the prototype never derives it (L5552, L5923)
        [InlineData("workshop", "workshop", FloatLatchState.Latched)]
        public void FloatLatch_ResetFromCheckpoint(string cp, string after, FloatLatchState state)
        {
            var p = FloatLatchParams.Dl17Latch();
            p.LatchedAfter = after;
            var l = new FloatLatch("dl17.latch", p);
            Mech.Graph(cp, new TestSource("dl17.rig"), l);
            Assert.Equal(state, l.State);
            Assert.Equal(state == FloatLatchState.Latched ? 70 : 0, l.ArmDeg, 12);
        }

        // ---- Flood ----------------------------------------------------------------------------------------------------------

        private static (MechanismGraph g, Flood f, TestSource duct) Dl11(bool bridged = false, string cp = "bedroom")
        {
            var duct = new TestSource("dl11.duct") { Engaged = bridged };
            var f = new Flood("dl11.dip", FloodParams.Dl11Dip());
            return (Mech.Graph(cp, duct, f), f, duct);
        }

        [Theory]
        [InlineData(149.0, 0, false)]                               // 149.0 + 0.102 = 149.102 > 149.1: at the edge
        [InlineData(148.99, 0, false)]
        [InlineData(150.5, 0, false)]
        [InlineData(150.6, 0, false)]
        [InlineData(149.5, 0.02, false)]
        [InlineData(149.5, 0, true)]
        public void Flood_TurnsHimBackAtTheEdge_L4860_L4861(double x, double y, bool busy)
        {
            var (g, _, _) = Dl11();
            Mech.Run(g, 1, Mech.Pose(x, y, busy: busy));
            bool expect = !busy && x + 0.17 * 0.6 > 149.1 && x < 150.6 && y < 0.02;
            Assert.Equal(expect, Mech.Emitted(g, "dl11.dip", FloodEvent.TurnBack));
            if (expect) Assert.Equal(149.1 - 0.35, Mech.Events(g).Find(e => e.Code == (int)FloodEvent.TurnBack).Value, 12);
        }

        [Fact]
        public void Flood_Bridged_NoTurnBack_FloorIsTheDuctTop_L4139()
        {
            var (g, f, duct) = Dl11();
            Assert.True(f.FloorAt(149.8, out double wet));
            Assert.Equal(-0.25, wet);
            Assert.False(f.FloorAt(149.1, out _));
            Assert.False(f.FloorAt(150.6, out _));
            duct.Engaged = true;
            Mech.Run(g, 1, Mech.Pose(149.5));
            Assert.True(Mech.Entered(g, "dl11.dip", FloodState.Bridged));
            Assert.False(Mech.Emitted(g, "dl11.dip", FloodEvent.TurnBack));
            Assert.True(f.FloorAt(149.8, out double top));
            Assert.Equal(0.01, top, 12);
        }

        [Theory]
        [InlineData(false, FloodState.Wet)]
        [InlineData(true, FloodState.Bridged)]
        public void Flood_ResetDerivesFromTheDuct_L4108(bool bridged, FloodState state)
        {
            var (g, f, _) = Dl11(bridged);
            Assert.Equal(state, f.State);
            Assert.Equal(0, g.Log.Count);
        }
    }
}
