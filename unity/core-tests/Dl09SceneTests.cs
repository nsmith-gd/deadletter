using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Motor;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-09 The Slipping Cage as a scene: the counterweight tray (a stand-in source: the plates family), the cage's pawl
    /// and the cage, driven by the real motor in the pipeline order (motor #4, graph #6–7, ride sync #9; §3.1), with the
    /// prototype's timings (§4.13c, §4.13f, L5011–L5095). The cage act's own parts (bracing at <c>CG.braceX</c>, the
    /// CageRideLever/CagePullPawl clips) belong to U-11; here Use during the ride calls <see cref="SlippingCage.PullPawl"/>
    /// and ride sync places him on the cage floor.
    /// </summary>
    public class Dl09SceneTests
    {
        private const double Dt = Mech.Dt;
        private const double ShaftX0 = 101.2, ShaftX1 = 102.8, Half = 0.17;

        /// <summary>The ante-room at the top (3.4), the shaft (the cage's floor), the lit landing (1.6) beyond it.</summary>
        private sealed class CageWorld : IMotorWorld
        {
            public SlippingCage Cage;
            public double SurfaceAt(double x, double refY) => x < ShaftX0 ? 3.4 : x <= ShaftX1 ? Cage.FloorY : 1.6;
            public double CeilingAt(double x, double refY) => LaneProbe.NoCeiling;
            public void Limits(double x, double y, out double left, out double right)
            {
                left = 95;
                right = Cage.State == SlippingCageState.Caught ? 110 : ShaftX1 - Half;   // the cage's gate until it holds at the landing
            }
            public bool IsRamp(double x) => false;
            public bool LedgeAhead(double x, double y, int dir, double range, double stepUp, out Ledge ledge)
                => LaneProbe.ScanLedge(this, x, y, dir, range, stepUp, out ledge);
        }

        private sealed class Scene
        {
            public readonly MechanismGraph G = new MechanismGraph();
            public readonly TestSource Tray;
            public readonly CageCatch Catch;
            public readonly SlippingCage Cage;
            public readonly D17Motor Motor;
            public readonly List<string> Trace = new List<string>();
            public int Steps;

            public Scene(string checkpoint, double x, double y, int plates)
            {
                Tray = G.Add(new TestSource("dl09.tray") { Load = plates });
                Catch = G.Add(new CageCatch("dl09.cagePawl", CageCatchParams.Dl09CagePawl()));   // before the cage: it bites this tick
                Cage = G.Add(new SlippingCage("dl09.cage", SlippingCageParams.Dl09Cage()));
                G.Build();
                G.Reset(Checkpoint.Prototype(checkpoint));
                Motor = new D17Motor(MotorConfig.Prototype(), new CageWorld { Cage = Cage });
                Motor.Place(x, y);
            }

            /// <summary>One pipeline step; Use during the ride throws the pawl (the cage act, #4).</summary>
            public void Step(MotorInput input)
            {
                Steps++;
                if (input.UsePressed && Cage.Riding) Cage.PullPawl();
                Motor.Step(input, Dt);                                                    // #4
                G.Step(Dt, Mech.Pose(Motor));                                             // #6–7
                if (Cage.Carrying) Motor.Place(Motor.X, Cage.FloorY, Motor.Facing);       // #9 ride sync
                foreach (var e in Mech.Events(G))
                    if (e.Id == "dl09.cage")
                        Trace.Add(e.Kind == MechanismEventKind.State ? ((SlippingCageState)e.Code).ToString() : ((SlippingCageEvent)e.Code) + "#" + e.Index);
            }

            public int StepUntil(MotorInput input, Func<bool> until, int max = 2000)
            {
                for (int i = 1; i <= max; i++) { Step(input); if (until()) return i; }
                return -1;
            }

            public int WalkIn() => StepUntil(Sim.Move(1), () => Cage.Riding, 300);
        }

        [Fact]
        public void LoadedRide_PawlThrownAtTheCatch_BitesAndHoldsAtTheLanding_HeWalksOff_L5031_L5089_L5094_L4950()
        {
            var s = new Scene("cage", 100.4, 3.4, plates: 2);
            Assert.True(s.WalkIn() > 0);
            Assert.Equal(new[] { "Settle", "RideStart#1" }, s.Trace);
            Assert.InRange(s.Motor.X, ShaftX0 + 0.1, ShaftX1 - 0.1);
            int stall = s.StepUntil(Sim.Move(0), () => s.Cage.State == SlippingCageState.Stall);
            Assert.Equal(253 - 1, stall);                                    // 253 steps from boarding (LiftTests)
            Assert.Equal(1.95, s.Motor.Y, 12);                               // ride sync: on the cage floor
            for (int i = 0; i < 10; i++) s.Step(Sim.Move(0));
            s.Step(Sim.Use());
            Assert.Equal(SlippingCageState.Bite, s.Cage.State);
            Assert.True(s.Catch.Engaged);
            int proud = s.StepUntil(Sim.Move(0), () => !s.Cage.Riding);
            Assert.Equal(56, proud);                                         // caught > 0.5 s, the act ends 0.4 s later
            Assert.Equal("RideEnd#" + SlippingCage.QuirkProud, s.Trace[s.Trace.Count - 1]);
            Assert.Equal(1.6, s.Motor.Y, 12);
            Assert.Equal(SlippingCageState.Caught, s.Cage.State);
            s.StepUntil(Sim.Move(1), () => s.Motor.X > ShaftX1 + 0.35, 200);
            Assert.Equal(1.6, s.Motor.Y, 9);                                 // onto the landing: landing8's trigger (L4950)
            Assert.True(Math.Abs(s.Motor.Y - 1.6) < 0.1 && s.Cage.State == SlippingCageState.Caught);
        }

        [Fact]
        public void LoadedRide_NoPawl_HeRidesItIntoTheBuffers_Death_ThenRespawnInTheCage_L5042_L5044()
        {
            var s = new Scene("cage", 100.4, 3.4, plates: 2);
            s.WalkIn();
            double minY = 10;
            int death = s.StepUntil(Sim.Move(0), () =>
            {
                if (s.Cage.Carrying) Assert.Equal(s.Cage.FloorY, s.Motor.Y, 12);
                minY = Math.Min(minY, s.Motor.Y);
                return s.Trace.Contains("Death#0");
            });
            Assert.Equal(388 - 1, death);
            Assert.Equal(-0.1, s.Cage.Y);
            Assert.True(minY < 0.1);
            // Respawn (§4.14): the world is rebuilt for the checkpoint and he is back at the top.
            s.G.Reset(Checkpoint.Prototype("cage"));
            s.Motor.Place(100.4, 3.4);
            s.Trace.Clear();
            Assert.Equal(SlippingCageState.Top, s.Cage.State);
            Assert.Equal(CageCatchState.Armed, s.Catch.State);
            Assert.True(s.WalkIn() > 0);
            Assert.Equal(new[] { "Settle", "RideStart#1" }, s.Trace);
        }

        [Fact]
        public void PawlThrownTooEarly_Rattles_ButCanBeThrownAgainInTime_L5091_L5092()
        {
            var s = new Scene("cage", 100.4, 3.4, plates: 2);
            s.WalkIn();
            s.StepUntil(Sim.Move(0), () => s.Cage.State == SlippingCageState.Shudder);
            s.Step(Sim.Use());
            Assert.Equal(CageCatchState.Rattling, s.Catch.State);
            Assert.True(s.Catch.Thrown);
            s.StepUntil(Sim.Move(0), () => s.Cage.State == SlippingCageState.Stall);
            Assert.Equal(CageCatchState.Armed, s.Catch.State);               // re-armed 0.6 s after the rattle
            s.Step(Sim.Use());
            Assert.Equal(SlippingCageState.Bite, s.Cage.State);
        }

        [Fact]
        public void TooLight_ItDipsAndHaulsBack_HeMustStepOutAndBackIn_ThenWithBothPlatesItRides_L5020_L5031()
        {
            var s = new Scene("cage", 100.4, 3.4, plates: 1);
            s.WalkIn();
            Assert.Equal(new[] { "Dip", "RideStart#0" }, s.Trace);
            s.StepUntil(Sim.Move(0), () => !s.Cage.Riding);
            Assert.Equal(new[] { "Dip", "RideStart#0", "DipBang#0", "HaulDip", "Top", "RideEnd#" + SlippingCage.QuirkStartle }, s.Trace);
            Assert.Equal(3.4, s.Motor.Y, 12);
            for (int i = 0; i < 120; i++) s.Step(Sim.Move(0));
            Assert.Equal(SlippingCageState.Top, s.Cage.State);              // still in it: nothing
            s.StepUntil(Sim.Move(-1), () => s.Motor.X < ShaftX0 + 0.1, 200);
            s.Tray.Load = 2;                                                 // the second plate goes into the tray
            s.Trace.Clear();
            Assert.True(s.WalkIn() > 0);
            Assert.Equal(new[] { "Settle", "RideStart#1" }, s.Trace);
        }

        [Fact]
        public void ResetPastLanding8_TheCageIsCaughtAtTheLanding_AndHeCanCrossIt_L4100()
        {
            var s = new Scene("landing8", 102.0, 1.6, plates: 2);
            Assert.Equal(SlippingCageState.Caught, s.Cage.State);
            Assert.Equal(CageCatchState.Bitten, s.Catch.State);
            s.StepUntil(Sim.Move(1), () => s.Motor.X > 104, 200);
            Assert.Equal(1.6, s.Motor.Y, 9);
            Assert.Empty(s.Trace);
            Assert.False(s.Cage.Riding);
        }

        [Fact]
        public void SnapshotMidSlip_RestoresAndContinuesBitIdentically()
        {
            var a = new Scene("cage", 100.4, 3.4, plates: 2);
            a.WalkIn();
            a.StepUntil(Sim.Move(0), () => a.Cage.State == SlippingCageState.Slip);
            for (int k = 0; k < 8; k++) a.Step(Sim.Move(0));

            var b = new Scene("landing8", 102.0, 1.6, plates: 0);           // any state: the snapshot overwrites it
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            for (int k = 0; k < 200; k++)
            {
                bool use = k == 60;                                          // in the stall
                if (use) b.Cage.PullPawl();
                a.Step(use ? Sim.Use() : Sim.Move(0));
                b.G.Step(Dt, Mech.Pose(a.Motor));
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
                Assert.Equal(Mech.Events(a.G).Count, Mech.Events(b.G).Count);
            }
            Assert.Equal(SlippingCageState.Caught, b.Cage.State);
        }

        [Fact]
        public void TwoRunsOfTheScene_WithTheSameInputs_AreBitIdentical()
        {
            var runs = new List<string>[2];
            for (int r = 0; r < 2; r++)
            {
                var s = new Scene("cage", 100.4, 3.4, plates: 2);
                var trace = runs[r] = new List<string>();
                for (int step = 0; step < 700; step++)
                {
                    bool pull = s.Cage.State == SlippingCageState.Stall && s.Cage.Elapsed > 0.2 && !s.Catch.Thrown;
                    MotorInput input = step < 40 ? Sim.Move(1) : pull ? Sim.Use() : step > 600 ? Sim.Move(1) : Sim.Move(0);
                    s.Step(input);
                    trace.Add(Sim.Snapshot(s.Motor) + "#" + Mech.Dump(s.G));
                }
                Assert.Equal(SlippingCageState.Caught, s.Cage.State);
                Assert.True(s.Motor.X > ShaftX1);
            }
            Assert.Equal(runs[0], runs[1]);
        }
    }
}
