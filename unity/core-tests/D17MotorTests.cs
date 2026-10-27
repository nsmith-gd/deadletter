using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// D-17 motor against the prototype (game/undelivered/index.html at 7b3c123). Line numbers in names and comments.
    /// All runs use the port's fixed 60 Hz step.
    /// </summary>
    public class D17MotorTests
    {
        private const double Dt = Sim.Dt;

        // ---- Constants ---------------------------------------------------------------------------------------------------

        [Fact]
        public void Config_MatchesPrototypeConstants_L304_L327()
        {
            var c = MotorConfig.Prototype();
            Assert.Equal(24, c.Fps);
            Assert.Equal(0.9, c.Walk); Assert.Equal(1.6, c.Run); Assert.Equal(0.5, c.CrouchWalk);
            Assert.Equal(9.8, c.Gravity); Assert.Equal(0.4, c.JumpApex);
            Assert.Equal(0.10, c.Coyote); Assert.Equal(0.12, c.JumpBuffer);
            Assert.Equal(0.76, c.StandHeight); Assert.Equal(0.58, c.CrouchHeight);
            Assert.Equal(0.17, c.Half); Assert.Equal(0.08, c.Foot); Assert.Equal(0.07, c.StepUp); Assert.Equal(0.17, c.FaceDistance);
            Assert.Equal(0.24, c.MantleMin); Assert.Equal(0.62, c.MantleMax); Assert.Equal(0.72, c.MantleMax + c.MantleAirExtra, 12);
            Assert.Equal(0.42, c.CarryWalk); Assert.Equal(0.29, c.GripForward);
            Assert.Equal(0.79, c.ClipSpeedWalk); Assert.Equal(1.52, c.ClipSpeedRun); Assert.Equal(0.49, c.ClipSpeedCrouchWalk);
        }

        [Fact]
        public void JumpVelocity_DefaultsToSixtyHertzParity_DesignedIsSqrtTwoGravityApex_L307()
        {
            var c = MotorConfig.Prototype();
            Assert.Equal(JumpMode.Parity60Hz, c.JumpMode);
            Assert.Equal(Math.Sqrt(2 * 9.8 * 0.4), c.JumpVelocityDesigned, 12);
            Assert.Equal(2.80, c.JumpVelocityDesigned, 2);
            Assert.Equal(Math.Sqrt(2 * 9.8 * 0.4) - 9.8 / 120, c.JumpVelocity, 12);
            Assert.Equal(2.7183, c.JumpVelocity, 4);

            var m = Sim.Make(BoxWorld.Flat());
            m.Step(Sim.Jump(), Dt);
            Assert.True(Sim.Has(m, MotorEventKind.Jump));
            Assert.Equal(c.JumpVelocityParity, FindJump(m), 12);

            c.JumpMode = JumpMode.Designed;
            Assert.Equal(c.JumpVelocityDesigned, c.JumpVelocity, 12);
        }

        private static double FindJump(D17Motor m)
        {
            foreach (var e in m.Events) if (e.Kind == MotorEventKind.Jump) return e.Value;
            return double.NaN;
        }

        // ---- Jump ---------------------------------------------------------------------------------------------------------

        /// <summary>Highest Y over a jump from flat ground, and the steps until he lands.</summary>
        private static double JumpPeak(MotorConfig config, double dt, out int steps)
        {
            var m = Sim.Make(BoxWorld.Flat(), config: config);
            m.Step(Sim.Jump(), dt);
            double peak = m.Y;
            steps = 1;
            for (int i = 0; i < 4000 && !m.Grounded; i++) { m.Step(Sim.Move(0), dt); peak = Math.Max(peak, m.Y); steps++; }
            Assert.True(m.Grounded);
            Assert.Equal(0.0, m.Y);
            return peak;
        }

        [Fact]
        public void JumpApex_Parity_MatchesSixtyHertzPrototypePeak_L1992_L2013()
        {
            // The prototype's 60 Hz Euler step (vy -= g·dt; y += vy·dt) peaks at 0.3768 m and lands on frame 34.
            double peak = JumpPeak(MotorConfig.Prototype(), Dt, out int steps);
            Assert.InRange(peak, 0.375, 0.379);
            Assert.InRange(steps, 33, 35);
            // Exact integration: the same apex at any step length.
            Assert.InRange(JumpPeak(MotorConfig.Prototype(), 1.0 / 144.0, out _), 0.375, 0.379);
            Assert.InRange(JumpPeak(MotorConfig.Prototype(), 1.0 / 30.0, out _), 0.373, 0.379);
        }

        [Fact]
        public void JumpApex_Designed_ReachesJumpApexWithinOneCentimetre_L306()
        {
            var c = MotorConfig.Prototype();
            c.JumpMode = JumpMode.Designed;
            double peak = JumpPeak(c, Dt, out int steps);
            Assert.InRange(peak, 0.398, 0.401);
            // Airtime 2·v/g ≈ 0.571 s, within a step.
            Assert.InRange(steps * Dt, 2 * 2.8 / 9.8 - Dt, 2 * 2.8 / 9.8 + 2 * Dt);
        }

        [Fact]
        public void Jump_NotWhileCrouched_L1992()
        {
            var w = BoxWorld.Flat().AddCeiling(-1, 1, 0.70);
            var m = Sim.Make(w);
            m.Step(Sim.Move(0), Dt);
            Assert.True(m.Crouched);
            Assert.False(Sim.Run(m, Sim.Jump(), 1, MotorEventKind.Jump));
        }

        [Fact]
        public void Coyote_JumpAllowedUpTo100msAfterWalkingOffAnEdge_L1987()
        {
            Assert.True(JumpAfterLeavingEdge(1));
            Assert.True(JumpAfterLeavingEdge(5));     // 5/60 = 83 ms
            Assert.False(JumpAfterLeavingEdge(7));    // 117 ms > COYOTE
        }

        private static bool JumpAfterLeavingEdge(int stepsAfter)
        {
            var w = BoxWorld.Flat().AddSolid(-10, 0, 1.0);
            var m = Sim.Make(w, -0.3, 1.0);
            Assert.True(Sim.RunUntil(m, Sim.Move(1), d => !d.Grounded) > 0);
            Sim.Run(m, Sim.Move(1), stepsAfter - 1);
            m.Step(Sim.Jump(1), Dt);
            return Sim.Has(m, MotorEventKind.Jump);
        }

        [Fact]
        public void JumpBuffer_PressUpTo120msBeforeLanding_JumpsOnLanding_L1935()
        {
            int landing = LandingStep(-1);
            Assert.True(BufferedJumpFires(landing - 3, landing));   // pressed 50 ms early
            Assert.True(BufferedJumpFires(landing - 5, landing));   // 83 ms early
            Assert.False(BufferedJumpFires(landing - 8, landing));  // 133 ms early: lost
        }

        private static int LandingStep(int pressAt)
        {
            var m = Sim.Make(BoxWorld.Flat());
            m.Step(Sim.Jump(), Dt);
            for (int i = 1; i < 200; i++)
            {
                m.Step(i == pressAt ? Sim.Jump() : Sim.Move(0), Dt);
                if (Sim.Has(m, MotorEventKind.Land)) return i;
            }
            return -1;
        }

        private static bool BufferedJumpFires(int pressAt, int landing)
        {
            var m = Sim.Make(BoxWorld.Flat());
            m.Step(Sim.Jump(), Dt);
            for (int i = 1; i <= landing + 6; i++)
            {
                m.Step(i == pressAt ? Sim.Jump() : Sim.Move(0), Dt);
                if (i > landing && Sim.Has(m, MotorEventKind.Jump)) return true;
            }
            return false;
        }

        // ---- Speeds -------------------------------------------------------------------------------------------------------

        [Theory]
        [InlineData(true, false, 1.6)]   // auto-run on: full key runs
        [InlineData(true, true, 0.9)]    // Shift/B walks
        [InlineData(false, false, 0.9)]  // auto-run off: walks
        [InlineData(false, true, 1.6)]   // ... and Shift runs (L1921–L1929)
        public void KeyboardSpeeds_RunAndWalk_L304_L1928(bool autoRun, bool modifier, double expected)
        {
            var m = Sim.Make(BoxWorld.Flat());
            m.AutoRun = autoRun;
            Sim.Run(m, new MotorInput { Move = 1, RunModifierHeld = modifier }, 120);
            Assert.Equal(expected, m.Vx, 9);
            Assert.Equal(expected > 1.15 ? ClipNames.Run : ClipNames.Walk, m.Clip);
        }

        [Theory]
        [InlineData(0.5, 0.9 * 0.575)]  // below the run threshold: walk, scaled by min(1, |a|·1.15) (L1981)
        [InlineData(0.7, 1.6 * 0.805)]  // |a| > 0.65 runs (L1927), still scaled by min(1, |a|·1.15)
        [InlineData(1.0, 1.6)]
        [InlineData(0.1, 0.0)]          // inside the 0.22 deadzone (L1266)
        public void StickSpeeds_L1266_L1927_L1981(double raw, double expected)
        {
            var m = Sim.Make(BoxWorld.Flat());
            double axis = MotorInput.FromStick(raw);
            Sim.Run(m, new MotorInput { Move = axis, MoveIsAnalog = true }, 180);
            Assert.Equal(expected, m.Vx, 9);
        }

        [Fact]
        public void CrouchHeld_WalksAtCrouchSpeed_L304()
        {
            var m = Sim.Make(BoxWorld.Flat());
            Sim.Run(m, new MotorInput { Move = 1, CrouchHeld = true }, 120);
            Assert.True(m.Crouched);
            Assert.Equal(MotorState.Crouched, m.State);
            Assert.Equal(0.5, m.Vx, 9);
            Assert.Equal(ClipNames.CrouchWalk, m.Clip);
        }

        [Fact]
        public void ReleaseFriction_MatchesPrototypeAt60Hz_L1984()
        {
            var m = Sim.Make(BoxWorld.Flat());
            m.AutoRun = false;
            Sim.Run(m, Sim.Move(1), 120);
            Assert.Equal(0.9, m.Vx, 9);
            m.Step(Sim.Move(0), Dt);
            // Prototype: vx += clamp(0 − vx, ±4.5·dt) then vx *= 1 − 10·dt.
            Assert.Equal((0.9 - 4.5 * Dt) * (1 - 10 * Dt), m.Vx, 12);
        }

        // ---- Step up, walls ------------------------------------------------------------------------------------------------

        [Fact]
        public void StepUp_007Climbs_008Blocks_L310_L2004()
        {
            var m = Sim.Make(BoxWorld.Flat().AddSolid(1.3, 5.0, 0.07), 1.0);
            Sim.Run(m, Sim.Move(1), 90);
            Assert.True(m.X > 1.6);
            Assert.Equal(0.07, m.Y, 12);

            var b = Sim.Make(BoxWorld.Flat().AddSolid(1.3, 3.0, 0.08), 1.0);
            Sim.Run(b, Sim.Move(1), 90);
            Assert.True(b.X <= 1.3 - 0.17 + 0.03, "blocked at the face: " + b.X);
            Assert.Equal(0.0, b.Y);
        }

        [Fact]
        public void Ramp_AllowsHigherStep_L2004()
        {
            var w = BoxWorld.Flat().AddRamp(1.3, 0.0, 2.3, 0.4).AddSolid(2.3, 4, 0.4);
            var m = Sim.Make(w, 1.0);
            Sim.Run(m, Sim.Move(1), 120);
            Assert.True(m.X > 2.4);
            Assert.Equal(0.4, m.Y, 9);
        }

        // ---- Mantle --------------------------------------------------------------------------------------------------------

        [Theory]
        [InlineData(0.25, true)]
        [InlineData(0.40, true)]
        [InlineData(0.62, true)]    // MANTLE_MAX is inclusive (L1990)
        [InlineData(0.24, false)]   // MANTLE_MIN is exclusive: top − y > 0.24 (L1990)
        [InlineData(0.20, false)]
        [InlineData(0.63, false)]
        [InlineData(0.70, false)]
        public void StandingMantle_AcceptedOnlyAbove024UpTo062_L1990(double height, bool mantles)
        {
            var m = Sim.Make(BoxWorld.Flat().AddSolid(1.3, 3.0, height), 1.0);
            m.Step(Sim.Jump(), Dt);
            Assert.Equal(mantles, Sim.Has(m, MotorEventKind.MantleStart));
            Assert.Equal(!mantles, Sim.Has(m, MotorEventKind.Jump));
            Assert.Equal(mantles ? MotorState.Mantling : MotorState.Airborne, m.State);
        }

        [Fact]
        public void StandingMantle_NeedsLedgeWithinFaceDPlus03_L1990()
        {
            // Ledge face 0.48 m ahead: beyond FACE_D + 0.3 = 0.47, so he jumps instead.
            var m = Sim.Make(BoxWorld.Flat().AddSolid(1.48, 3.0, 0.4), 1.0);
            m.Step(Sim.Jump(), Dt);
            Assert.False(Sim.Has(m, MotorEventKind.MantleStart));
            Assert.True(Sim.Has(m, MotorEventKind.Jump));
        }

        [Fact]
        public void Mantle_Lasts56FramesAt24fps_AndEndsOnTop_L311_L313()
        {
            var m = Sim.Make(BoxWorld.Flat().AddSolid(1.3, 3.0, 0.5), 1.0);
            m.Step(Sim.Jump(), Dt);
            Assert.Equal(MotorState.Mantling, m.State);
            int steps = Sim.RunUntil(m, Sim.Move(0), d => Sim.Has(d, MotorEventKind.MantleEnd));
            Assert.Equal(140, steps);                                 // 56 / 24 s = 2.333 s = 140 steps at 60 Hz
            Assert.InRange(steps * Dt, 56.0 / 24.0 - Dt, 56.0 / 24.0 + Dt);
            Assert.Equal(0.5, m.Y, 12);
            Assert.Equal(1.0 + 0.38 + (0.30 - 0.17), m.X, 9);       // MANTLE_KEYS forward 0.38 + (dist − FACE_D)
            Assert.True(m.Grounded);
            Assert.Equal(ClipNames.Idle, m.Clip);
        }

        [Theory]
        [InlineData(0.70, true)]
        [InlineData(1.09, true)]    // at the parity apex (≈0.377) the ledge is ≈0.713 above him: inside MANTLE_MAX + 0.1
        [InlineData(1.11, false)]   // ≈0.733 above the apex: beyond 0.72 (highest catchable ≈ 1.097, as the prototype)
        [InlineData(1.15, false)]
        public void MidAirCatch_UpTo072AboveHim_L2022(double height, bool caught)
        {
            var m = Sim.Make(BoxWorld.Flat().AddSolid(1.3, 3.0, height), 1.0);
            m.Step(Sim.Jump(), Dt);
            Assert.True(Sim.Has(m, MotorEventKind.Jump));
            bool mantled = false;
            Sim.RunUntil(m, Sim.Move(0), d => { mantled |= Sim.Has(d, MotorEventKind.MantleStart); return d.Grounded || mantled; });
            Assert.Equal(caught, mantled);
            if (caught)
            {
                Assert.True(Sim.Run(m, Sim.Move(0), 200, MotorEventKind.MantleEnd));
                Assert.Equal(height, m.Y, 12);
            }
        }

        [Theory]
        [InlineData(0.5, 48)]       // standing mantle scan, L1989: d = 0.02 … 0.49
        [InlineData(0.32, 30)]      // mid-air scan, L2021: d = 0.02 … 0.31
        [InlineData(0.6, 58)]       // ledgeAhead's default range, L1738
        public void LedgeScan_SamplesLikeThePrototypeLoop_L1739(double range, int samples)
        {
            var w = new CountingWorld(BoxWorld.Flat());
            Assert.False(LaneProbe.ScanLedge(w, 0, 0, 1, range, 0.07, out _));
            Assert.Equal(samples, w.SurfaceCalls);
            Assert.Equal(samples, LaneProbe.ScanSampleCount(range));
            Assert.Equal(0.02, w.MinX, 9);
            Assert.Equal(range - 0.01, w.MaxX, 9);
        }

        [Fact]
        public void LedgeScan_FaceAtExactlyTheRange_IsNotSeen()
        {
            // A face at 0.32 is beyond the prototype's last mid-air sample (0.31); at 0.31 it is caught.
            Assert.False(LaneProbe.ScanLedge(BoxWorld.Flat().AddSolid(0.32, 3.0, 0.5), 0, 0, 1, 0.32, 0.07, out _));
            Assert.True(LaneProbe.ScanLedge(BoxWorld.Flat().AddSolid(0.31, 3.0, 0.5), 0, 0, 1, 0.32, 0.07, out var l));
            Assert.Equal(0.31, l.Distance, 9);
        }

        private sealed class CountingWorld : IMotorWorld
        {
            private readonly IMotorWorld _w;
            public int SurfaceCalls;
            public double MinX = double.PositiveInfinity, MaxX = double.NegativeInfinity;
            public CountingWorld(IMotorWorld w) { _w = w; }
            public double SurfaceAt(double x, double refY)
            {
                SurfaceCalls++; MinX = Math.Min(MinX, x); MaxX = Math.Max(MaxX, x);
                return _w.SurfaceAt(x, refY);
            }
            public double CeilingAt(double x, double refY) => _w.CeilingAt(x, refY);
            public void Limits(double x, double y, out double left, out double right) => _w.Limits(x, y, out left, out right);
            public bool IsRamp(double x) => _w.IsRamp(x);
            public bool LedgeAhead(double x, double y, int dir, double range, double stepUp, out Ledge ledge)
                => _w.LedgeAhead(x, y, dir, range, stepUp, out ledge);
        }

        // ---- Ceilings and crouch ---------------------------------------------------------------------------------------------

        [Fact]
        public void Ceiling_BetweenCrouchAndStandHeight_AutoCrouchesThrough_L1975_L2008()
        {
            var m = Sim.Make(BoxWorld.Flat().AddCeiling(2.0, 4.0, 0.70));
            bool crouchedUnder = false;
            double maxSpeedUnder = 0;
            for (int i = 0; i < 600 && m.X < 5; i++)
            {
                m.Step(Sim.Move(1), Dt);
                if (m.X > 2.1 && m.X < 3.9)
                {
                    crouchedUnder |= m.Crouched;
                    Assert.True(m.Crouched);
                    maxSpeedUnder = Math.Max(maxSpeedUnder, Math.Abs(m.Vx));
                }
            }
            Assert.True(crouchedUnder);
            Assert.True(m.X >= 5);
            Assert.True(maxSpeedUnder <= 0.5 + 1e-9);
            Assert.Equal(MotorState.Grounded, m.State);   // stands again once clearance > 0.85 (L1976)
        }

        [Fact]
        public void Ceiling_BelowCrouchHeight_Blocks_L2008()
        {
            var m = Sim.Make(BoxWorld.Flat().AddCeiling(2.0, 4.0, 0.50));
            Sim.Run(m, Sim.Move(1), 600);
            Assert.True(m.X < 2.0, "stopped before the gap: " + m.X);
            Assert.True(m.Crouched);
        }

        [Fact]
        public void Ceiling_StandHeightClear_NoCrouch()
        {
            var m = Sim.Make(BoxWorld.Flat().AddCeiling(2.0, 4.0, 0.86));
            bool crouched = false;
            for (int i = 0; i < 400; i++) { m.Step(Sim.Move(1), Dt); crouched |= m.Crouched; }
            Assert.False(crouched);
        }

        [Fact]
        public void Bonk_HeadHitsCeilingWhileRising_L2017()
        {
            var m = Sim.Make(BoxWorld.Flat().AddCeiling(-1, 1, 1.0));
            m.Step(Sim.Jump(), Dt);
            Assert.True(Sim.Run(m, Sim.Move(0), 30, MotorEventKind.Bonk));
        }

        // ---- Landing ---------------------------------------------------------------------------------------------------------

        [Fact]
        public void HardLanding_ShakesAndMakesNoise_L2024_L2028()
        {
            var w = BoxWorld.Flat().AddSolid(-10, 0, 0.5);
            var m = Sim.Make(w, -0.3, 0.5);
            var kinds = new HashSet<MotorEventKind>();
            for (int i = 0; i < 200 && !kinds.Contains(MotorEventKind.Land); i++)
            {
                m.Step(Sim.Move(1), Dt);
                foreach (var e in m.Events) kinds.Add(e.Kind);
            }
            Assert.Contains(MotorEventKind.Land, kinds);
            Assert.Contains(MotorEventKind.Shake, kinds);
            Assert.Contains(MotorEventKind.Noise, kinds);
            Assert.Equal(0.3, m.LandTimer + Dt, 9);    // land timer 0.30 for a drop > 0.25, ticked once
        }

        // ---- Determinism ----------------------------------------------------------------------------------------------------

        [Fact]
        public void SameInputs_ProduceIdenticalTrace()
        {
            var a = Trace();
            Assert.Equal(a, Trace());
            string all = string.Join("\n", a);
            foreach (var kind in new[] { "Jump", "Land", "MantleStart", "MantleEnd", "Footstep", "ClipChanged:CrouchWalk" })
                Assert.Contains(kind, all);
        }

        private static List<string> Trace()
        {
            var w = new BoxWorld { LeftLimit = -5, RightLimit = 30 }
                .AddSolid(-6, 12, 0)
                .AddSolid(2.0, 2.6, 0.45)        // mantle
                .AddCeiling(4.0, 5.5, 0.66)      // crouch gap
                .AddSolid(7.0, 7.4, 0.22)        // hop
                .AddRamp(9.0, 0.0, 10.0, 0.4).AddSolid(10.0, 12.0, 0.4)
                .AddSolid(12.0, 31, -0.3);       // a drop
            var r = new InteractionResolver();
            var item = new TestItem { X = 13.5, BaseY = -0.3 };
            r.Register(item);
            var m = Sim.Make(w, 0, 0, r);
            item.Motor = m;
            var trace = new List<string>();
            for (int i = 0; i < 1500; i++)
            {
                var input = new MotorInput
                {
                    Move = (i / 200) % 5 == 3 ? 0.5 : 1,
                    MoveIsAnalog = (i / 200) % 5 == 3,
                    JumpPressed = i % 37 == 0,
                    UsePressed = i == 1100 || i == 1350,
                    RunModifierHeld = (i / 150) % 3 == 1,
                };
                m.Step(input, Dt);
                trace.Add(Sim.Snapshot(m));
            }
            return trace;
        }
    }
}
