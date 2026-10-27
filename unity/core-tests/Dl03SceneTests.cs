using System.Collections.Generic;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-03 The Weight of the Job as a scene: the load plate drives the follower gate, D-17 walked by the real motor
    /// (motor #4, then the graph #6; §3.1). The trolley and the weight stand in for the Push and Carry families.
    /// L318–L329, L2229–L2238, L2365–L2403.
    /// </summary>
    public class Dl03SceneTests
    {
        private const double Dt = Mech.Dt, GateX = 30.6, PlateMid = (28.8 + 29.55) / 2;

        private sealed class Scene
        {
            public readonly MechanismGraph G = new MechanismGraph();
            public readonly TestBody Trolley, Weight;
            public readonly LoadPlate Plate;
            public readonly FollowerActuator Gate;
            public readonly D17Motor Motor;

            public Scene(string checkpoint, double x)
            {
                bool solved = Checkpoint.Prototype(checkpoint).Past("solved");
                Trolley = G.Add(new TestBody("dl03.trolley", solved ? PlateMid : 13 + 14.55));                    // TROLLEY_X, L8026
                Weight = G.Add(new TestBody("dl03.weight", solved ? 13 + 16.0 : 13 + 12.62, solved ? BodySupport.Carrier : BodySupport.Floor)
                    { CarrierX = solved ? PlateMid : double.NaN });                                                // WEIGHT_X, L8025
                Plate = G.Add(new LoadPlate("dl03.plate", LoadPlateParams.Dl03Plate()));                           // updateDL02 order
                Gate = G.Add(new FollowerActuator("dl03.gate", FollowerParams.Dl03Gate()));
                G.Build();
                G.Reset(Checkpoint.Prototype(checkpoint));
                Motor = Sim.Make(BoxWorld.Flat(), x, 0);
            }

            public void Step(MotorInput input)
            {
                Motor.Step(input, Dt);
                G.Step(Dt, Mech.Pose(Motor));
            }

            public bool Solved => Plate.SolvedWith(Gate.Position, 1.2);
        }

        [Fact]
        public void HeAloneOpensTheGate_ItFollowsHimOff_AndSlamsBehindHim_L2372_L2392()
        {
            var s = new Scene("weighroom", 27.0);
            int onAt = -1;
            for (int i = 0; i < 600 && s.Motor.X < PlateMid; i++) { s.Step(Sim.Move(1)); if (onAt < 0 && s.Plate.PlayerOn) onAt = i; }
            Assert.True(onAt >= 0);
            for (int i = 0; i < 300; i++) s.Step(Sim.Move(0));
            Assert.True(s.Plate.PlayerOn);
            Assert.Equal(1.0, s.Plate.Load);
            Assert.Equal(1.2, s.Gate.Position);                    // min(1, load) × GATE_OPEN_H
            Assert.False(s.Solved);                                // he does not count

            // The trolley and the weight hold it at 0.864 once he walks off and stands under it; take the weight away
            // and it drops, but never onto him (stand height 0.76 + 0.03).
            s.Trolley.X = PlateMid;
            s.Weight.Support = BodySupport.Carrier; s.Weight.CarrierX = PlateMid;
            Sim.RunUntil(s.Motor, Sim.Move(1), m => { s.G.Step(Dt, Mech.Pose(m)); return m.X >= GateX - 0.1; }, 600);
            for (int i = 0; i < 60; i++) s.Step(Sim.Move(0));
            Assert.False(s.Plate.PlayerOn);
            Assert.InRange(s.Motor.X, GateX - 0.2, GateX + 0.2);
            Assert.Equal(0.72 * 1.2, s.Gate.Position, 9);
            s.Weight.Support = BodySupport.Floor; s.Weight.X = 13 + 12.62;
            for (int i = 0; i < 120; i++) s.Step(Sim.Move(0));
            Assert.Equal(0.76 + 0.03, s.Gate.Position, 9);

            // Walk on: it slams behind him and startles him.
            bool slam = false, startle = false;
            for (int i = 0; i < 300; i++)
            {
                s.Step(Sim.Move(i < 30 ? 1 : 0));
                slam |= Mech.Emitted(s.G, "dl03.gate", FollowerEvent.Slam);
                startle |= Mech.Emitted(s.G, "dl03.gate", FollowerEvent.Startle);
            }
            Assert.True(slam);
            Assert.True(startle);
            Assert.Equal(0.3 * 1.2, s.Gate.Position, 12);
        }

        [Fact]
        public void TrolleyAndWeightWithoutHim_HoldTheGateAt0864_Solved_L2396_L2403()
        {
            var s = new Scene("weighroom", 27.0);
            s.Trolley.X = PlateMid;
            s.Weight.Support = BodySupport.Carrier; s.Weight.CarrierX = PlateMid; s.Weight.X = PlateMid - 0.12;
            int solvedAt = -1;
            for (int i = 1; i <= 300 && solvedAt < 0; i++) { s.Step(Sim.Move(0)); if (s.Solved) solvedAt = i; }
            Assert.InRange(solvedAt * Dt * 0.55, 0.68 * 1.2 - 0.01 - 0.01, 0.68 * 1.2 + 0.01);   // wound up at 0.55 m/s
            for (int i = 0; i < 120; i++) s.Step(Sim.Move(0));
            Assert.Equal(0.72 * 1.2, s.Gate.Position, 12);
        }

        [Theory]
        [InlineData("weighroom", 0.0, false)]
        [InlineData("solved", 0.72, true)]
        [InlineData("bay", 0.72, true)]
        public void ResetFromCheckpoint_DerivesPlateAndGate_L8025_L8030(string cp, double load, bool solved)
        {
            var s = new Scene(cp, 26.0);
            Assert.Equal(load, s.Plate.Load, 12);
            Assert.Equal(load * 1.2, s.Gate.Position, 12);
            Assert.Equal(solved, s.Solved);
            Assert.Equal(0, s.G.Log.Count);
        }

        [Fact]
        public void SnapshotMidRise_RestoresAndContinuesBitIdentically()
        {
            var a = new Scene("weighroom", 28.6);
            for (int i = 0; i < 90; i++) a.Step(Sim.Move(i < 20 ? 1 : 0));
            Assert.Equal(FollowerState.Rising, a.Gate.State);
            var b = new Scene("solved", 26.0);
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            for (int i = 0; i < 200; i++)
            {
                a.Step(Sim.Move(i > 100 && i < 130 ? -1 : 0));
                b.G.Step(Dt, Mech.Pose(a.Motor));
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            }
        }

        [Fact]
        public void TwoRunsOfTheScene_WithTheSameInputs_AreBitIdentical()
        {
            var runs = new List<string>[2];
            for (int r = 0; r < 2; r++)
            {
                var s = new Scene("weighroom", 27.0);
                var trace = runs[r] = new List<string>();
                for (int step = 0; step < 900; step++)
                {
                    if (step == 400) s.Trolley.X = PlateMid;
                    s.Step(Sim.Move(step < 120 ? 1 : step < 300 ? 0 : step < 360 ? 1 : 0));
                    trace.Add(Sim.Snapshot(s.Motor) + "#" + Mech.Dump(s.G));
                }
            }
            Assert.Equal(runs[0], runs[1]);
        }
    }
}
