using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Motor;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-14 The Window as a scene: the crank winds the chain, the pole through A's wheel jams A, the clutch slips and B
    /// comes down alone, the panel peels; then pole out, wind, pole in, wind: both down, both ledges out. Driven by the
    /// real motor and resolver in the pipeline order (motor #4, graph #6–7; §3.1). The pole is a test source (engaged =
    /// through A's wheel): its jam/unjam at the wheel (a place target for a light carried item) is not ported yet.
    /// </summary>
    public class Dl14SceneTests
    {
        private const double Dt = Mech.Dt;

        private sealed class Scene
        {
            public readonly MechanismGraph G = new MechanismGraph();
            public readonly TestSource Pole;
            public readonly WindCrank Crank;
            public readonly PairedBlindDrive Blinds;
            public readonly D17Motor Motor;

            public Scene(string checkpoint, double x)
            {
                Pole = G.Add(new TestSource("dl14.pole") { Engaged = true });          // left through A's wheel, L5232
                Crank = G.Add(new WindCrank("dl14.crank", WindCrankParams.Dl14Crank()));
                Blinds = G.Add(new PairedBlindDrive("dl14.blinds", PairedBlindParams.Dl14Blinds()));
                G.Build();
                G.Reset(Checkpoint.Prototype(checkpoint));
                var resolver = new InteractionResolver();
                resolver.Register(Crank);
                Motor = Sim.Make(BoxWorld.Flat(200, 300), x, 0, resolver);
            }

            public void Step(MotorInput input)
            {
                Motor.Step(input, Dt);
                G.Step(Dt, Mech.Pose(Motor));
            }

            /// <summary>Use the crank and play the act out; returns the motor's clip time at the wind (or -1).</summary>
            public double Wind()
            {
                Assert.True(Motor.PreviewUse(out var c));
                Assert.Same(Crank, c.Target);
                Step(Sim.Use());
                double at = -1;
                for (int i = 0; i < 600 && (Motor.IsActing || i < 2); i++)
                {
                    Step(Sim.Move(0));
                    if (Mech.Emitted(G, "dl14.blinds", PairedBlindEvent.Wind)) { at = Motor.ClipTime; Assert.Equal("Crank", Motor.Clip); }
                }
                Assert.False(Motor.IsActing);
                return at;
            }

            public void Settle() { for (int i = 0; i < 150; i++) Step(Sim.Move(0)); }
        }

        [Fact]
        public void TheWindow_JamSlipPeel_ThenUnjamWindJamWind_BothDown_L5364_L5376_L5437_L5475()
        {
            var s = new Scene("window", 242.3);
            int slipSteps = 0, grinds = 0, peel = 0;
            double at = s.Wind();
            Assert.InRange(at - Dt, 0.3, 0.3 + Dt + 1e-9);                      // a.t > 0.3 (ClipTime is read after the mixer advances)
            Assert.Equal(0, s.Blinds.TargetA);
            Assert.Equal(1, s.Blinds.TargetB);                                  // B comes down alone
            for (int i = 0; i < 150; i++)
            {
                s.Step(Sim.Move(0));
                if (s.Blinds.Slipping) slipSteps++;
                if (Mech.Emitted(s.G, "dl14.blinds", PairedBlindEvent.Grind)) grinds++;
                if (Mech.Emitted(s.G, "dl14.blinds", PairedBlindEvent.Peel)) peel++;
            }
            Assert.True(slipSteps > 30);
            Assert.True(grinds >= 2);
            Assert.True(s.Blinds.Peeled);
            Assert.True(peel <= 1);
            Assert.True(s.Blinds.ClutchRad > 10);                               // it spun on its own
            Assert.Equal(0, s.Blinds.A);
            Assert.Equal(1, s.Blinds.B, 12);

            s.Pole.Engaged = false;                                             // he draws the pole out (Lift f16, L5327)
            s.Wind();
            s.Settle();
            Assert.Equal(1, s.Blinds.A, 12);                                    // A down as B goes up
            Assert.Equal(0, s.Blinds.B, 12);
            Assert.Equal(PairedBlindState.Still, s.Blinds.State);

            s.Pole.Engaged = true;                                              // back through the wheel (SetDown f14, L5336)
            s.Wind();
            s.Settle();
            Assert.Equal(1, s.Blinds.A, 12);
            Assert.Equal(1, s.Blinds.B, 12);
            Assert.Equal(3, s.Blinds.Winds);
            Assert.True(s.Blinds.LedgeOut(0) && s.Blinds.LedgeOut(1));
            Assert.Equal(1.6, s.Blinds.SurfaceAt(238.4, 1.2, 1.1));
            Assert.Equal(3, s.Crank.Winds);
        }

        [Theory]
        [InlineData("window", 0, 0, false)]
        [InlineData("hatch14", 1, 1, true)]
        [InlineData("corridor", 1, 1, true)]
        public void ResetFromCheckpoint_DerivesTheBlinds_L5237_L5238(string cp, double a, double b, bool peeled)
        {
            var s = new Scene("window", 242.3);
            s.Wind();
            for (int i = 0; i < 30; i++) s.Step(Sim.Move(0));
            s.G.Reset(Checkpoint.Prototype(cp));
            Assert.Equal(a, s.Blinds.A);
            Assert.Equal(b, s.Blinds.B);
            Assert.Equal(peeled, s.Blinds.Peeled);
            Assert.Equal(0, s.Crank.Winds);
            Assert.Equal(WindCrankState.Idle, s.Crank.State);
        }

        [Fact]
        public void SnapshotMidSlip_RestoresAndContinuesBitIdentically()
        {
            var a = new Scene("window", 242.3);
            a.Wind();                                                           // the act is over at 1.5 s; B runs on to 2.5 s
            Assert.Equal(PairedBlindState.Slipping, a.Blinds.State);
            var b = new Scene("hatch14", 230);
            b.G.Restore(Mech.Snapshot(a.G));
            Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
            for (int i = 0; i < 200; i++)
            {
                a.Step(Sim.Move(0));
                b.G.Step(Dt, Mech.Pose(a.Motor));
                Assert.Equal(Mech.Dump(a.G), Mech.Dump(b.G));
                Assert.Equal(Mech.Events(a.G).Count, Mech.Events(b.G).Count);
            }
            Assert.True(b.Blinds.Peeled);
            Assert.Equal(PairedBlindState.Still, b.Blinds.State);
        }

        [Fact]
        public void TwoRunsOfTheScene_WithTheSameInputs_AreBitIdentical()
        {
            var runs = new List<string>[2];
            for (int r = 0; r < 2; r++)
            {
                var s = new Scene("window", 242.3);
                var trace = runs[r] = new List<string>();
                for (int step = 0; step < 1200; step++)
                {
                    if (step == 300) s.Pole.Engaged = false;
                    if (step == 700) s.Pole.Engaged = true;
                    s.Step(step % 300 == 0 ? Sim.Use() : Sim.Move(0));
                    trace.Add(Sim.Snapshot(s.Motor) + "#" + Mech.Dump(s.G));
                }
                Assert.Equal(4, s.Blinds.Winds);
            }
            Assert.Equal(runs[0], runs[1]);
        }
    }
}
