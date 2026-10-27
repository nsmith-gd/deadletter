using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// #22 motor parity fixes found by nathaniel1's golden-trace replay of DL-01 (Dl01TraceTests): M1 a station on the
    /// lane starts its clip on the step he arrives or finishes turning; M2 clip thresholds are the prototype's exact
    /// <c>f &gt;= n</c>; M3 falls from rest drop as the prototype's 60 Hz Euler step; M4 the latch's crouch holds through
    /// the chained Flinch.
    /// <para>#28 (the DL-03–DL-06 replays): M5 Use lets go of a pushable keeping his speed; M7 pushables rank by their grip's
    /// distance alone; M8 the step back to the lane runs after the player's update; M9 the motor's state can be handed over
    /// (<see cref="D17Motor.SetState"/>, <see cref="D17Motor.Capture"/>, <see cref="D17Motor.Place"/>'s yaw, <see cref="D17Motor.Stop"/>);
    /// M10 a station's own step-in speed; and DL-05's toy, a step in <c>in</c> after the turn.</para>
    /// </summary>
    public class MotorParityTests
    {
        private const double Dt = Sim.Dt;
        private const double G = 9.8;

        private static D17Motor With(BoxWorld w, double x, double y, params IInteractable[] things)
        {
            var r = new InteractionResolver();
            foreach (var t in things) r.Register(t);
            return Sim.Make(w, x, y, r);
        }

        // ---- M1 --------------------------------------------------------------------------------------------------------

        [Fact]
        public void M1_AStationOnTheLane_StartsItsClipOnTheStepHeArrives_L1846_L1850()
        {
            var lever = new TestLever { StandX = 1.0, Profile = new ActProfile("Pull", crouch: true) };
            var m = With(BoxWorld.Flat(), 0.95, 0, lever);
            m.Step(Sim.Use(), Dt);
            Assert.Equal(ActPhase.Approach, m.ActPhase);
            int arrived = Sim.RunUntil(m, Sim.Move(0), mm => mm.X == 1.0, 200);
            Assert.True(arrived > 0);
            Assert.Equal(ActPhase.Clip, m.ActPhase);                                  // latch: a.phase = 'act'; setClip('Pull') (L1846–L1848)
            Assert.Equal("Pull", m.Clip);
            Assert.Equal(1, lever.ProfileAsks - 1);                                   // the profile is still asked again before the clip
            Assert.Equal(0, m.Z);
        }

        [Fact]
        public void M1_AStationOnTheLaneThatTurnsIntoTheSet_StartsItsClipOnTheStepHeHasTurned_L1879()
        {
            var crank = new TestLever { StandX = 1.0, Profile = new ActProfile("Crank", turnIntoSet: true) };
            var m = With(BoxWorld.Flat(), 1.0, 0, crank);
            m.Step(Sim.Use(), Dt);
            int turned = Sim.RunUntil(m, Sim.Move(0), mm => mm.ActPhase != ActPhase.Approach && mm.ActPhase != ActPhase.Turn, 200);
            Assert.True(turned > 0);
            Assert.True(Math.Abs(m.Yaw - Math.PI) < m.Config.TurnTolerance + m.Config.YawRate * Dt);
            Assert.Equal(ActPhase.Clip, m.ActPhase);                                  // crank: a.phase = 'act'; setClip('Crank') (L1879)
            Assert.Equal("Crank", m.Clip);
        }

        [Fact]
        public void M1_AStationInTheSet_StillStepsInFirst_AndStartsTheClipOnTheStepHeReachesItsDepth_L3606_L3613()
        {
            var present = new TestLever { StandX = 1.0, StandZ = 0.3, Profile = new ActProfile("Present", turnIntoSet: true) };
            var m = With(BoxWorld.Flat(), 1.0, 0, present);
            m.Step(Sim.Use(), Dt);
            Sim.RunUntil(m, Sim.Move(0), mm => mm.ActPhase == ActPhase.StepIn, 200);
            Assert.True(m.Z < 0.3);
            Assert.NotEqual("Present", m.Clip);
            int steps = Sim.RunUntil(m, Sim.Move(0), mm => mm.ActPhase == ActPhase.Clip, 200);
            Assert.InRange(steps, (int)Math.Ceiling(0.3 / (m.Config.StepInSpeed * Dt)), 200);
            Assert.Equal(0.3, m.Z, 12);
        }

        // ---- M2 --------------------------------------------------------------------------------------------------------

        [Fact]
        public void M2_TheMantleEndsOnItsStep141_AsTheRawFGreaterOrEqual56_L1946()
        {
            var m = Sim.Make(BoxWorld.Flat().AddSolid(1.3, 3.0, 0.5), 1.0);
            m.Step(Sim.Jump(), Dt);
            double t = 0;
            int protoSteps = 0;
            do { t += Dt; protoSteps++; } while (!(t * 24 >= 56));                  // m.t += dt; f >= MANTLE_FRAMES
            Assert.Equal(141, protoSteps);
            Assert.Equal(protoSteps, Sim.RunUntil(m, Sim.Move(1), d => !d.IsMantling));
        }

        [Fact]
        public void M2_ClipClock_IsExact()
        {
            double f = 0;
            for (int i = 0; i < 140; i++) f += Dt * 24;
            Assert.False(ClipClock.Reached(f, 56));                                  // 55.99999999999991
            Assert.True(ClipClock.Reached(f + Dt * 24, 56));
            Assert.True(ClipClock.Crossed(f, f + Dt * 24, 56));
        }

        // ---- M3 --------------------------------------------------------------------------------------------------------

        /// <summary>He walks off a 1 m ledge; every airborne step's y must equal the prototype's Euler step from vy = 0.</summary>
        [Fact]
        public void M3_AWalkOffFall_DropsExactlyAsThePrototypesEulerStep_L2013_L2014_L2032()
        {
            var w = BoxWorld.Flat().AddSolid(-10, 0, 1.0);
            var m = Sim.Make(w, -0.3, 1.0);
            Sim.RunUntil(m, Sim.Move(1), d => !d.Grounded);
            double py = m.Y, pvy = 0;                                                  // the walk-off step: y kept, vy = 0
            int n = 0;
            while (true)
            {
                double x = m.X;
                m.Step(Sim.Move(1), Dt);
                if (m.Grounded) break;
                pvy -= G * Dt; py += pvy * Dt;
                n++;
                Assert.Equal(py, m.Y, 12);
                Assert.Equal(pvy, m.Vy + m.Config.ParityVelocityOffset, 12);
            }
            Assert.InRange(n, 10, 40);
        }

        [Fact]
        public void M3_AJump_StillPeaksAt0_377_AndMatchesTheEulerArcStepForStep()
        {
            var m = Sim.Make(BoxWorld.Flat());
            m.Step(Sim.Jump(), Dt);
            double py = 0, pvy = m.Config.JumpVelocityDesigned, peak = 0;
            pvy -= G * Dt; py += pvy * Dt;                                             // the jump step integrates too (L1992, L2013)
            Assert.Equal(py, m.Y, 12);
            while (!m.Grounded)
            {
                m.Step(Sim.Move(0), Dt);
                if (m.Grounded) break;
                pvy -= G * Dt; py += pvy * Dt;
                Assert.Equal(py, m.Y, 12);
                peak = Math.Max(peak, m.Y);
            }
            Assert.InRange(peak, 0.376, 0.378);
        }

        [Fact]
        public void M3_ABonk_FallsFromTheCeilingAsThePrototype_L2016()
        {
            var w = BoxWorld.Flat().AddCeiling(-5, 5, 0.76 + 0.2);                    // his head meets it 0.2 up
            var m = Sim.Make(w);
            m.Step(Sim.Jump(), Dt);
            Assert.True(Sim.RunUntil(m, Sim.Move(0), d => Sim.Has(d, MotorEventKind.Bonk), 60) > 0);
            double py = m.Y, pvy = 0;
            Assert.Equal(0.2, py, 12);
            while (true)
            {
                m.Step(Sim.Move(0), Dt);
                if (m.Grounded) break;
                pvy -= G * Dt; py += pvy * Dt;
                Assert.Equal(py, m.Y, 12);
            }
        }

        [Fact]
        public void M3_Designed_FallsFromRestExactly()
        {
            var c = MotorConfig.Prototype();
            c.JumpMode = JumpMode.Designed;
            Assert.Equal(0, c.FallStartVelocity);
            Assert.Equal(0, c.ParityVelocityOffset);
            var w = BoxWorld.Flat().AddSolid(-10, 0, 1.0);
            var m = Sim.Make(w, -0.3, 1.0, config: c);
            Sim.RunUntil(m, Sim.Move(1), d => !d.Grounded);
            double y0 = m.Y;
            m.Step(Sim.Move(1), Dt);
            m.Step(Sim.Move(1), Dt);
            Assert.Equal(y0 - 0.5 * G * (2 * Dt) * (2 * Dt), m.Y, 12);
        }

        // ---- M4 --------------------------------------------------------------------------------------------------------

        [Fact]
        public void M4_TheLatchsCrouch_HoldsThroughTheChainedFlinch_AndEndsWithIt_L1846_L1875_L1876()
        {
            var latch = new TestLever { StandX = 1.0, Profile = new ActProfile("Pull", crouch: true) };
            latch.Answer = f => f.Part == 0 ? (ClipClock.Reached(f.Frame, 39) ? ActStep.Then("Flinch", 0.06) : ActStep.Continue)
                : ActStep.DoneIf(f.Time >= 1.6);
            var m = With(BoxWorld.Flat(), 0.9, 0, latch);
            m.Step(Sim.Use(), Dt);
            bool sawFlinch = false;
            while (m.IsActing)
            {
                if (m.ActPhase != ActPhase.Approach) Assert.True(m.Crouched);         // game.crouched = true from the approach (L1846)
                sawFlinch |= m.Clip == "Flinch";
                m.Step(Sim.Move(0), Dt);
            }
            Assert.True(sawFlinch);
            Assert.False(m.Crouched);                                                 // the Flinch's end: game.crouched = false (L1876)
            Assert.Equal(ClipNames.Idle, m.Clip);
        }

        // ---- #28 ------------------------------------------------------------------------------------------------------

        private static D17Motor Pushing(TestPushable p, double x)
        {
            var m = With(BoxWorld.Flat(), x, 0, p);
            m.Step(Sim.Use(), Dt);
            Assert.True(Sim.RunUntil(m, Sim.Move(0), mm => mm.Hold == HoldKind.Push, 600) > 0);
            return m;
        }

        [Fact]
        public void M5_UseLetsGoOfAPushable_KeepingHisSpeed_WhichThenDecays_L1820()
        {
            var p = new TestPushable { X = 1.6, Min = 0, Max = 10, LetGoAtMax = false };
            var m = Pushing(p, 1.0);
            Sim.Run(m, Sim.Move(1), 60);
            double vx = m.Vx, x = m.X;
            Assert.True(vx > 0.3);
            m.Step(Sim.Use(), Dt);                                                     // beginUse('release'): returns before game.vx = 0
            Assert.Equal(HoldKind.None, m.Hold);
            Assert.True(p.Released);
            Assert.Equal(vx, m.Vx);
            Assert.Equal(x, m.X);
            m.Step(Sim.Move(0), Dt);                                                   // he drifts on as it decays (vx *= 1 − 10·dt)
            Assert.True(m.Vx > 0 && m.Vx < vx);
            Assert.True(m.X > x);
        }

        [Fact]
        public void M5_EveryOtherUseStillStopsHim_L1821()
        {
            var lever = new TestLever { StandX = 1.3, Reach = 0.4, Profile = new ActProfile("Pull") };
            var m = With(BoxWorld.Flat(), 1.0, 0, lever);
            Sim.Run(m, Sim.Move(1), 5);
            Assert.True(m.Vx > 0);
            m.Step(Sim.Use(), Dt);
            Assert.True(m.IsActing);
            Assert.Equal(0, m.Vx);
        }

        [Fact]
        public void M7_PushablesRankByTheirGripsDistanceAlone_WhicheverWayHeFaces_L4251_L4255()
        {
            // Facing −x at 5.0: a grip 0.30 ahead (its pushable in front of him) and one 0.15 behind.
            var ahead = new TestPushable { X = 4.1, Side = -1, Gap = 0.6, Min = 0, Max = 10 };        // stand 4.70
            var behind = new TestPushable { X = 5.75, Side = 1, Gap = 0.6, Min = 0, Max = 10 };       // stand 5.15
            var r = new InteractionResolver();
            r.Register(ahead); r.Register(behind);
            var q = new InteractionQuery(5.0, 0, 0, -1, true, false, HoldKind.None, null, null);
            Assert.True(r.Resolve(q, out var c));
            Assert.Same(behind, c.Target);
            Assert.False(c.InFront);
            // Equal distances: the first registered (PUSHABLES order).
            var twin = new TestPushable { X = 4.25, Side = -1, Gap = 0.6, Min = 0, Max = 10 };        // stand 4.85, 0.15 ahead
            var r2 = new InteractionResolver();
            r2.Register(behind); r2.Register(twin);
            Assert.True(r2.Resolve(q, out c));
            Assert.Same(behind, c.Target);
        }

        [Fact]
        public void M7_StationsStillPreferWhatIsInFrontOfHim()
        {
            var ahead = new TestLever { StandX = 4.7, Reach = 0.4 };
            var behind = new TestLever { StandX = 5.15, Reach = 0.4 };
            var r = new InteractionResolver();
            r.Register(behind); r.Register(ahead);
            Assert.True(r.Resolve(new InteractionQuery(5.0, 0, 0, -1, true, false, HoldKind.None, null, null), out var c));
            Assert.Same(ahead, c.Target);
        }

        [Fact]
        public void M8_HeStepsBackToTheLaneOnTheStepHeLetsGo_L4876()
        {
            var p = new TestPushable { X = 1.6, Z = 0.35, Min = 0, Max = 10, LetGoAtMax = false };
            var m = Pushing(p, 1.0);
            Assert.Equal(0.35, m.Z, 12);
            Sim.Run(m, Sim.Move(1), 20);
            Assert.Equal(0.35, m.Z, 12);                                               // not while he holds it (game.hold !== 'push')
            m.Step(Sim.Jump(), Dt);                                                    // lets go
            Assert.Equal(HoldKind.None, m.Hold);
            Assert.Equal(0.35 - 0.45 * Dt, m.Z, 12);                                   // updateCh1 runs after the player's update
            int back = Sim.RunUntil(m, Sim.Move(0), mm => mm.Z == 0, 200);
            Assert.Equal((int)Math.Ceiling(0.35 / (0.45 * Dt)) - 1, back);
        }

        [Fact]
        public void M9_PlaceTakesAYaw_AndCaptureAndSetStateHandOverAMovingD17()
        {
            var m = Sim.Make(BoxWorld.Flat(), 2.0);
            m.Place(2.0, 0, 1, yaw: -1.437);                                           // turning back to the lane (DL-05's hand-over)
            Assert.Equal(-1.437, m.Yaw);
            Assert.Equal(1, m.Facing);
            m.Step(Sim.Move(0), Dt);
            Assert.Equal(-1.437 + m.Config.YawRate * Dt, m.Yaw, 12);

            var run = MotorSnapshot.AtRest(3.0, 0, 1);
            run.Vx = 1.6;                                                              // DL-06's hand-over: running in
            m.SetState(run);
            var got = m.Capture();
            Assert.Equal(3.0, got.X);
            Assert.Equal(1.6, got.Vx);
            Assert.True(got.Grounded);
            Assert.Equal(Math.PI / 2, got.Yaw);
            m.Step(Sim.Move(1), Dt);
            Assert.Equal(1.6, m.Vx, 12);                                               // already at the run's top speed
            Assert.Equal(3.0 + 1.6 * Dt, m.X, 12);

            var air = new MotorSnapshot { X = 1, Y = 1, Vx = 0.5, Vy = 0.2, Facing = -1, Yaw = -Math.PI / 2, PeakY = 1.1 };
            m.SetState(air);
            var back = m.Capture();
            Assert.False(back.Grounded);
            Assert.Equal(0.2, back.Vy);
            Assert.Equal(1.1, back.PeakY);
            Assert.Equal(-1, back.Facing);
            Assert.Equal(MotorState.Airborne, m.State);
        }

        [Fact]
        public void M9_StopZeroesHisSpeedOnly()
        {
            var m = Sim.Make(BoxWorld.Flat(), 2.0);
            Sim.Run(m, Sim.Move(-1), 3);                                               // turning, walking
            double yaw = m.Yaw, x = m.X;
            string clip = m.Clip;
            Assert.True(m.Vx < 0 && yaw > -Math.PI / 2);
            m.Stop();
            Assert.Equal(0, m.Vx);
            Assert.Equal(yaw, m.Yaw);
            Assert.Equal(x, m.X);
            Assert.Equal(clip, m.Clip);
        }

        [Fact]
        public void M10_AStationStepsInAndOutAtItsOwnSpeed_L2916()
        {
            foreach (var (own, rate) in new[] { (0.4, 0.4), (double.NaN, 0.45) })
            {
                var lever = new TestLever { StandX = 1.0, StandZ = 0.11, StepInSpeed = own };
                var m = With(BoxWorld.Flat(), 1.0, 0, lever);
                m.Step(Sim.Use(), Dt);
                Sim.RunUntil(m, Sim.Move(0), mm => mm.ActPhase == ActPhase.StepIn && mm.Z > 0, 200);
                Assert.Equal(rate * Dt, m.Z, 12);
                Assert.Equal(m.Config.StepInSpeed / m.Config.ClipSpeedWalk, m.ClipTimeScale, 12);   // the clip at 0.45 either way (L2917)
                int steps = Sim.RunUntil(m, Sim.Move(0), mm => mm.ActPhase == ActPhase.Clip, 200);
                Assert.Equal((int)Math.Ceiling((0.11 - 0.004) / (rate * Dt)), steps);
                Sim.RunUntil(m, Sim.Move(0), mm => mm.ActPhase == ActPhase.StepOut && mm.Z < 0.11, 400);
                Assert.Equal(0.11 - rate * Dt, m.Z, 12);
            }
        }

        [Fact]
        public void Toy_AStationCanSpendAStepInAfterItsTurn_L3606()
        {
            var toy = new TestLever { StandX = 1.0, Profile = new ActProfile("Straighten", turnIntoSet: true, stepAfterTurn: true) };
            var m = With(BoxWorld.Flat(), 1.0, 0, toy);
            m.Step(Sim.Use(), Dt);
            Sim.RunUntil(m, Sim.Move(0), mm => mm.ActPhase != ActPhase.Approach && mm.ActPhase != ActPhase.Turn, 200);
            Assert.Equal(ActPhase.StepIn, m.ActPhase);                                 // the turn's step: a.phase = 'in'
            Assert.NotEqual("Straighten", m.Clip);
            m.Step(Sim.Move(0), Dt);
            Assert.Equal(ActPhase.Clip, m.ActPhase);                                   // the next: |dz| < 0.004, the clip
            Assert.Equal("Straighten", m.Clip);
        }
    }
}
