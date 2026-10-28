using System;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl02;
using Xunit;
using DeathKind = DeadLetter.Core.Hazards.DeathKind;   // #22: Motor has a DeathKind of its own (same members)

namespace DeadLetter.Core.Tests
{
    /// <summary>Core/Hazards (§4.14): the periodic crusher (DL-02's press), deaths and the respawn through the checkpoint service.</summary>
    public class HazardTests
    {
        private static PeriodicCrusher Press(out MechanismGraph g, Func<double> clock = null)
        {
            var c = new PeriodicCrusher("t.press", PeriodicCrusherParams.Dl02Press());
            if (clock != null) c.BindClock(clock);
            g = Mech.Graph("room", c);
            return c;
        }

        /// <summary>The prototype's <c>pressFace</c>, written out (L7310–L7316), with three.js's lerp.</summary>
        private static double ProtoFace(double t)
        {
            double S(double x) => Smooth.Step(x);
            double L(double a, double b, double k) => (1 - k) * a + k * b;
            if (t < 0.5) return 0.98;
            if (t < 0.62) return L(0.98, 0.055, S((t - 0.5) / 0.12));
            if (t < 0.97) return 0.055;
            if (t < 1.57) return L(0.055, 0.98, S((t - 0.97) / 0.6));
            return 0.98;
        }

        [Theory]
        [InlineData(0.0)] [InlineData(0.49)] [InlineData(0.5)] [InlineData(0.56)] [InlineData(0.6199)] [InlineData(0.62)] [InlineData(0.8)]
        [InlineData(0.97)] [InlineData(1.2)] [InlineData(1.5699)] [InlineData(1.57)] [InlineData(2.59)]
        public void Face_IsPressFace_L7310(double t)
        {
            var c = Press(out _);
            Assert.Equal(ProtoFace(t), c.FaceAt(t));                                                  // bit for bit
        }

        [Fact]
        public void Face_FollowsTheBoundClock_ModuloThePeriod_L7345()
        {
            double clock = 68.05;
            var c = Press(out var g, () => clock);
            for (int i = 0; i < 400; i++)
            {
                clock += Mech.Dt;
                g.Step(Mech.Dt, PlayerPose.Away);
                Assert.Equal(clock % 2.6, c.Phase);
                Assert.Equal(ProtoFace(clock % 2.6), c.Face);
            }
        }

        [Fact]
        public void States_FollowTheCycle()
        {
            double clock = 0;
            var c = Press(out var g, () => clock);
            var seen = new System.Collections.Generic.List<CrusherState>();
            for (int i = 0; i < 160; i++)
            {
                clock += Mech.Dt;
                g.Step(Mech.Dt, PlayerPose.Away);
                if (seen.Count == 0 || seen[seen.Count - 1] != c.State) seen.Add(c.State);
            }
            Assert.Equal(new[] { CrusherState.Tell, CrusherState.Falling, CrusherState.Down, CrusherState.Rising, CrusherState.Up, CrusherState.Tell }, seen);
        }

        /// <summary>The slam (thud, clank, shake 0.15·max(0.2, 1 − d/6)) on the one step that reaches the bed, if he is within 6 m (L7349–L7350).</summary>
        [Fact]
        public void Slam_OnTheStepThatReachesTheBed_WhenHeIsNear_L7350()
        {
            double clock = 0;
            var c = Press(out var g, () => clock);
            int slams = 0, far = 0;
            for (int i = 0; i < 3 * 156; i++)
            {
                clock += Mech.Dt;
                g.Step(Mech.Dt, Mech.Pose(12.95));
                if (Mech.Emitted(g, "t.press", CrusherEvent.Slam))
                {
                    slams++;
                    Assert.True(c.Phase >= 0.62 && c.Phase - Mech.Dt < 0.62);
                    var e = Mech.Events(g).Find(v => v.Code == (int)CrusherEvent.Slam);
                    Assert.Equal(0.15 * (1 - 1.0 / 6), e.Value, 12);
                }
            }
            for (int i = 0; i < 3 * 156; i++) { clock += Mech.Dt; g.Step(Mech.Dt, Mech.Pose(20)); if (Mech.Emitted(g, "t.press", CrusherEvent.Slam)) far++; }
            Assert.Equal(3, slams);
            Assert.Equal(0, far);
        }

        /// <summary>Under the ram (open span 13.62–14.28), face below 0.74, feet below 0.3 (L7351).</summary>
        [Theory]
        [InlineData(13.9, 0.0, 0.8, true)]
        [InlineData(13.63, 0.0, 0.8, true)]
        [InlineData(13.62, 0.0, 0.8, false)]
        [InlineData(14.28, 0.0, 0.8, false)]
        [InlineData(13.9, 0.29, 0.8, true)]
        [InlineData(13.9, 0.3, 0.8, false)]
        [InlineData(13.9, 0.0, 0.3, false)]
        [InlineData(13.9, 0.0, 1.3, true)]
        [InlineData(13.9, 0.0, 1.4, false)]
        public void Crushed_UnderTheRam_WhileItKills_L7351(double x, double y, double phase, bool crushed)
        {
            double clock = 26 + phase - Mech.Dt;
            var c = Press(out var g, () => clock);
            clock += Mech.Dt;
            g.Step(Mech.Dt, Mech.Pose(x, y));
            Assert.Equal(crushed, Mech.Emitted(g, "t.press", CrusherEvent.Crushed));
            Assert.Equal(c.Face < 0.74, c.Engaged);
        }

        [Fact]
        public void Reset_KeepsTheRhythm_AndRestoreThenStep_IsBitIdentical()
        {
            double clock = 30.3;
            var a = Press(out var ga, () => clock);
            for (int i = 0; i < 50; i++) { clock += Mech.Dt; ga.Step(Mech.Dt, Mech.Pose(13.9)); }
            double face = a.Face;
            ga.Reset(Mech.Cp("room"));
            Assert.Equal(face, a.Face);

            var own = Press(out var g1);
            for (int i = 0; i < 70; i++) g1.Step(Mech.Dt, PlayerPose.Away);
            var copy = Press(out var g2);
            g2.Restore(Mech.Snapshot(g1));
            for (int i = 0; i < 200; i++)
            {
                g1.Step(Mech.Dt, Mech.Pose(13.9)); g2.Step(Mech.Dt, Mech.Pose(13.9));
                Assert.Equal(Mech.Dump(g1), Mech.Dump(g2));
            }
            Assert.Equal(own.Face, copy.Face);
        }

        [Fact]
        public void Profiles_AreThePrototypes_L7421()
        {
            Assert.Equal(("DeathCrush", 0.7, 26, 0.9), Tuple(DeathProfile.Of(DeathKind.Crush)));
            Assert.Equal(("DeathShock", 1.0, 44, 0.45), Tuple(DeathProfile.Of(DeathKind.Shock)));
            Assert.Equal(("DeathGrabbed", 1.15, 18, 0.45), Tuple(DeathProfile.Of(DeathKind.Grabbed)));
            Assert.Equal(("DeathFall", 0.9, 20, 0.7), Tuple(DeathProfile.Of(DeathKind.Fall)));
            Assert.Equal(1.6, DeathProfile.Of(DeathKind.Shock).SparkSpeed);
            Assert.Equal(0, DeathProfile.EyeLevel(0.45, calm: false));
        }

        private static (string, double, int, double) Tuple(DeathProfile p) => (p.Clip, p.Hold, p.Sparks, p.Shake);

        // ---- Death and respawn in a scene -----------------------------------------------------------------------------
        /// <summary>DL-02 at room with the clock set so the ram comes down as he stands under it.</summary>
        private static SceneSim Hall(double clock, double x)
        {
            var sim = new SceneSim(Dl02Scene.Def()) { Clock = clock };
            sim.Begin("room");
            sim.Motor.Place(x, 0, 1);
            return sim;
        }

        [Fact]
        public void Crushed_HeDies_HoldsAndCuts_ThenRespawnsAtRoom_WithTheWorldRebuilt()
        {
            var sim = Hall(26.0, 13.9);
            int k = 0;
            while (sim.Deaths == 0 && k++ < 200) sim.Step(default);
            Assert.Equal(1, sim.Deaths);
            Assert.Equal("death", sim.ActKind);                                                       // the motor's death act
            Assert.Equal("Crush", sim.ActPhase);
            Assert.True(sim.Motor.Has(MotorEventKind.Death, "Crush"));                                // for the sparks, the eye and the shake
            Assert.InRange(sim.Clock % 2.6, 0.5, 0.62);                                               // as the face drops past 0.74
            Assert.Equal(0, sim.Vx);
            Assert.True(sim.Busy);
            double x = sim.X;

            int toCut = 0;
            while (sim.RespawnAt == 0) { sim.Step(new MotorInput { Move = 1 }); toCut++; Assert.Equal(x, sim.X); }
            Assert.Equal(42, toCut);                                                                  // 0.7 s
            Assert.Equal(sim.Clock + 0.6, sim.RespawnAt);
            int toRespawn = 0;
            while (sim.ActKind != null) { sim.Step(default); toRespawn++; }
            Assert.Equal(37, toRespawn);                                                              // clock ≥ respawnAt, L8494
            Assert.Equal(13.2, sim.X);
            Assert.Equal("room", sim.Checkpoints.Current.Name);
            Assert.Equal(1, sim.Deaths);                                                              // game.deaths outlives the respawn
            Assert.Equal(ItemState.Floor, sim.Graph.Get<CarriedItem>("dl02.box").State);
            Assert.Equal(17.4, sim.Graph.Get<CarriedItem>("dl02.box").X);
        }

        [Fact]
        public void Dying_IsOnce_UntilTheRespawn()
        {
            var sim = Hall(26.0, 13.9);
            for (int i = 0; i < 60; i++) sim.Step(default);
            Assert.Equal(1, sim.Deaths);
            Assert.False(sim.Chapter.Die(DeathKind.Fall));
        }

        [Fact]
        public void Die_DropsTheCarriedBox_WhereHeStands_AndLetsGo_L7425()
        {
            var sim = new SceneSim(Dl02Scene.Def());
            sim.Begin("room");
            sim.Motor.Place(17.0, 0, 1);
            var box = sim.Graph.Get<CarriedItem>("dl02.box");
            sim.Step(new MotorInput { UsePressed = true });
            int k = 0;
            while (sim.Motor.Hold != HoldKind.Item && k++ < 300) sim.Step(default);
            Assert.Equal(ItemState.Carried, box.State);
            for (int i = 0; i < 30; i++) sim.Step(new MotorInput { Move = 1 });
            double x = sim.X;
            Assert.True(sim.Chapter.Die(DeathKind.Fall));
            Assert.Equal(ItemState.Floor, box.State);
            Assert.Equal(x, box.X);
            Assert.Equal(0, box.BaseY);
            Assert.Equal(HoldKind.None, sim.Motor.Hold);
            Assert.Equal(x, sim.X);
            Assert.Equal(0.2, sim.Lane.SurfaceAt(x));                                                // a block where he died
        }

        [Fact]
        public void DeathInTheAir_KeepsHimAirborne_AndTurnsHimBackToHisFacing()
        {
            var sim = new SceneSim(Dl02Scene.Def());
            sim.Begin("room");
            sim.Motor.Place(16.0, 0, 1);
            sim.Step(new MotorInput { JumpPressed = true, JumpHeld = true });
            sim.Step(new MotorInput { Move = -1 });
            Assert.False(sim.Grounded);
            double y = sim.Y;
            sim.Chapter.Die(DeathKind.Fall);
            Assert.False(sim.Grounded);
            for (int i = 0; i < 30; i++) sim.Step(default);
            Assert.Equal(y, sim.Y);                                                                   // he does not fall meanwhile
            Assert.Equal(-Math.PI / 2, sim.Yaw, 12);                                                  // yawOverride = null: toward his facing
        }

        [Fact]
        public void ASinkingDeath_IsTheSceneAct_TheMotorsCannotSink_28()
        {
            var sim = new SceneSim(Dl02Scene.Def());
            sim.Begin("room");
            sim.Motor.Place(16.0, 0, 1);
            Assert.True(sim.Chapter.Die(DeathKind.Grabbed, sinkRate: 0.8));
            Assert.False(sim.Chapter.Die(DeathKind.Fall));
            for (int i = 0; i < 60; i++) sim.Step(default);
            Assert.Equal(-0.8, sim.Y, 9);
            Assert.Equal(1.15, ((DeathAct)sim.Act).Profile.Hold);
        }
    }
}
