using System;
using System.Collections.Generic;
using DeadLetter.Core.Camera;
using DeadLetter.Core.Maths;
using Xunit;

namespace DeadLetter.Core.Tests
{
    public class CameraRigTests
    {
        private const double Dt = 1.0 / 60.0;
        private static readonly CameraConfig C = CameraConfig.Prototype;
        private static readonly double Aspect = 16.0 / 9.0;

        // ---- Reference: index.html frameFor (L7667–L7726), transcribed literally (watchLoad = 0) -----------------
        private static double[] L3(double[] a, double[] b, double k) => new[] { a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k, a[2] + (b[2] - a[2]) * k };
        private static double[] Fit(double[] v, double w, double aspect) => new[] { Math.Max(v[0], C.WidthFit(35, w, aspect)), v[1], v[2] };
        private static double S(double v) => Smooth.Step(v);
        private static double Cl(double v, double a, double b) => Smooth.Clamp(v, a, b);

        private static (double cx, double[] v, double fog) Reference(double x, double y, double lead, double k, double kr, bool realised, double kp, double aspect)
        {
            double[] alcove = { 5.2, 1.0, 0.8 }, hall = { 9.2, 2.35, 1.95 }, bulk = { 6.0, 1.15, 0.9 };
            double inHall = S((x - 6.9) / 0.9) * (1 - S((x - 8.9) / 0.8));
            double[] v = L3(L3(alcove, hall, S((x - 6.9) / 0.9)), bulk, S((x - 8.9) / 0.8));
            double cx = Cl(x + lead * (1 - 0.6 * inHall), 1.2, 10.6), fog = 0.075 - 0.032 * inHall;
            if (k > 0)
            {
                double ksh = 1 - S((x - (25.0 - 0.6)) / 1.2);
                double shx = Cl(x + lead * 0.6, 15.2, 20.9); double[] shv = Fit(new[] { 6.6, 1.55, 0.95 }, 8.4, aspect);
                cx += (Cl(13 + 15.05 + 0.2 * (x - (13 + 15)), 13 + 15.0, 13 + 15.35) - cx) * k;
                v = L3(v, Fit(new[] { 5.9, 1.2, 0.85 }, 6.2, aspect), k); fog += (0.06 - fog) * k;
                double kh = S((x - (13 + 17.3)) / 1.4) * k;
                cx += (Cl(x + lead, 13 + 19.0, 13 + 24.4) - cx) * kh; v = L3(v, Fit(new[] { 7.4, 1.6, 1.1 }, 6.4, aspect), kh); fog += (0.045 - fog) * kh;
                if (kr > 0) { cx += (13 + 20.7 - cx) * kr; v = L3(v, Fit(new[] { 10.8, 2.7, 1.45 }, 9.5, aspect), kr); fog += (0.03 - fog) * kr; }
                double ks = realised ? S((x - (13 + 17.7)) / 0.5) * (1 - S((x - (13 + 22.6)) / 1.2)) : 0;
                if (ks > 0) { cx += (Cl(x + 0.4, 13 + 19.2, 13 + 24.0) - cx) * ks * 0.6; v = L3(v, Fit(new[] { 6.2, 0.95, 0.72 }, 6.0, aspect), ks); }
                double kbay = S((x - (13 + 25.4)) / 1.4);
                if (kbay > 0) { cx += (Cl(x + lead * 0.5, 41.2 + 0.4, 46.3 - 1.4) - cx) * kbay; v = L3(v, Fit(new[] { 6.2, 1.15, 0.8 }, 7.0, aspect), kbay); fog += (0.05 - fog) * kbay; }
                double krh = S((x - (13 + 34.9 - 0.8)) / 1.2);
                if (krh > 0)
                {
                    double kc = S((x - (13 + 38.6)) / 1.4);
                    double tx = Cl(x + lead * 0.6, 13 + 36.6, 13 + 38.6);
                    tx += (Cl(x + lead * 0.3, 13 + 40.8, 13 + 44.2) - tx) * kc;
                    cx += (tx - cx) * krh; v = L3(v, Fit(new[] { 6.4, 1.25, 0.8 }, 6.8, aspect), krh); fog += (0.045 - fog) * krh;
                }
                if (ksh > 0) { cx += (shx - cx) * ksh; v = L3(v, shv, ksh); fog += (0.05 - fog) * ksh; }
            }
            double k3 = S((x - (33 + 25.4)) / 1.6);
            if (k3 > 0)
            {
                double kf = S((x - (33 + 29.6)) / 1.0), ku = S((y - 0.2) / 1.2);
                double tx = Cl(x + lead * 0.6, 33 + 27.6, 33 + 29.6);
                tx += (Cl(x + lead * 0.5, 33 + 31.8, 33 + 34.2) - tx) * kf;
                tx += (Cl(x + lead, 33 + 40.2, 33 + 45.4) - tx) * ku;
                double[] v3 = L3(Fit(new[] { 5.4, 1.15, 0.85 }, 5.0, aspect), Fit(new[] { 6.6, 1.35, 0.85 }, 6.6, aspect), kf);
                v3 = L3(v3, Fit(new[] { 7.0, 1.4, 0.9 }, 7.0, aspect), ku);
                cx += (tx - cx) * k3; v = L3(v, v3, k3); fog += (0.05 - 0.012 * ku - fog) * k3;
                if (kp > 0) { cx += (33 + 37.9 - cx) * kp; v = L3(v, Fit(new[] { 11.5, 2.5, -0.7 }, 12.2, aspect), kp); fog += (0.028 - fog) * kp; }
            }
            return (cx, v, fog);
        }

        private static void AssertFrame((double cx, double[] v, double fog) r, Frame f, string at, double cxTol = 1e-9)
        {
            const double tol = 1e-9;
            Assert.True(Math.Abs(r.cx - f.Cx) < cxTol, at + " cx " + r.cx + " vs " + f.Cx);
            Assert.True(Math.Abs(r.v[0] - f.Volume.Distance) < tol, at + " dist " + r.v[0] + " vs " + f.Volume.Distance);
            Assert.True(Math.Abs(r.v[1] - f.Volume.Height) < tol, at + " height");
            Assert.True(Math.Abs(r.v[2] - f.Volume.Look) < tol, at + " look");
            Assert.True(Math.Abs(r.fog - f.Fog) < tol, at + " fog " + r.fog + " vs " + f.Fog);
        }

        [Theory]
        [InlineData(0.0, 1.0)]
        [InlineData(1.16, 1.0)]
        [InlineData(-0.95, 1.0)]
        [InlineData(0.6, 0.5625)]   // portrait: widthFit bites
        public void PrologueTrack_MatchesFrameFor_AlongTheLane(double lead, double aspectScale)
        {
            double aspect = aspectScale == 1.0 ? Aspect : aspectScale;
            FramingTrack track = PrologueFraming.Build();
            var signals = new FramingSignalTable();
            for (double x = -0.3; x <= 80.0; x += 0.0625)
            {
                foreach (double y in new[] { 0.0, 0.9, 2.1 })
                {
                    int region = x < 11.45 ? 1 : x < 60.3 ? 2 : 3;
                    double k = PrologueFraming.Dl02Signal(region, region == 1 && x > 10.4 ? 1 : -1, x);
                    double kr = x > 30 && x < 40 ? PrologueFraming.RevealSignal(x - 31) : 0;
                    bool realised = region == 2 && x > 31;
                    double kp = PrologueFraming.PitSignal(x > 62 && x < 72, (x - 62) * 2.2);
                    signals.Set(PrologueFraming.Dl02, k).Set(PrologueFraming.Dl02Reveal, kr)
                           .Set(PrologueFraming.Dl02Realised, realised ? 1 : 0).Set(PrologueFraming.Dl06Pit, kp);
                    Frame f = track.Evaluate(x, y, lead, signals, C, aspect);
                    AssertFrame(Reference(x, y, lead, k, kr, realised, kp, aspect), f, "x=" + x + " y=" + y);
                }
            }
        }

        [Fact]
        public void VolumeBlending_IsExactOutsideBlends_AndContinuousInside()
        {
            FramingTrack track = PrologueFraming.Build();
            var none = new FramingSignalTable();
            Frame alcove = track.Evaluate(4.0, 0, 0, none, C, Aspect);
            Assert.Equal(5.2, alcove.Volume.Distance, 12); Assert.Equal(1.0, alcove.Volume.Height, 12); Assert.Equal(0.075, alcove.Fog, 12);
            Frame hall = track.Evaluate(7.8, 0, 0, none, C, Aspect);   // fully in the hall, before the bulkhead blend
            Assert.Equal(9.2, hall.Volume.Distance, 12); Assert.Equal(0.043, hall.Fog, 12);
            Frame bulk = track.Evaluate(9.8, 0, 0, none, C, Aspect);
            Assert.Equal(6.0, bulk.Volume.Distance, 12); Assert.Equal(0.075, bulk.Fog, 12);
            // Halfway into the hall blend: smoothstep(0.5) = 0.5.
            Frame mid = track.Evaluate(6.9 + 0.45, 0, 0, none, C, Aspect);
            Assert.Equal((5.2 + 9.2) / 2, mid.Volume.Distance, 12);
            // No jumps: 1 mm steps change the distance by far less than a centimetre.
            double prev = track.Evaluate(0, 0, 0.6, none, C, Aspect).Volume.Distance;
            for (double x = 0.001; x < 11; x += 0.001)
            {
                double d = track.Evaluate(x, 0, 0.6, none, C, Aspect).Volume.Distance;
                Assert.True(Math.Abs(d - prev) < 0.01, "jump at " + x);
                prev = d;
            }
        }

        [Fact]
        public void Gates_AndSignals_SwitchZones()
        {
            FramingTrack track = PrologueFraming.Build();
            var s = new FramingSignalTable();
            // Region 2 but the gate signal is 0: DL-01's clamp holds cx at 10.6.
            Assert.Equal(10.6, track.Evaluate(20, 0, 0, s, C, Aspect).Cx, 12);
            s.Set(PrologueFraming.Dl02, 1);
            Assert.Equal(20.0, track.Evaluate(20, 0, 0, s, C, Aspect).Cx, 9);   // the sorting hall frame
            // The reveal pan pulls to 33.7 at its full weight.
            s.Set(PrologueFraming.Dl02Reveal, 1);
            Assert.Equal(33.7, track.Evaluate(33, 0, 0, s, C, Aspect).Cx, 9);
        }

        // ---- Rig dynamics ---------------------------------------------------------------------------------------

        private static CameraRigInput At(double x, double y = 0, int facing = 1, double vx = 0, IFramingSignals s = null) =>
            new CameraRigInput { X = x, Y = y, Facing = facing, Vx = vx, Signals = s ?? new FramingSignalTable(), Aspect = Aspect };

        [Fact]
        public void Damp_IsExactAt60Hz_AndCompoundsAtOtherRates()
        {
            Assert.Equal(1.6 / 60, Damp.Factor(1.6, Dt), 15);
            double a = 0, b = 0;
            a = Damp.Toward(a, 1, 1.4, Dt);
            b = Damp.Toward(Damp.Toward(b, 1, 1.4, Dt / 2), 1, 1.4, Dt / 2);
            Assert.Equal(a, b, 12);
            double c = 0; for (int i = 0; i < 2; i++) c = Damp.Toward(c, 1, 1.4, Dt);
            Assert.Equal(c, Damp.Toward(0, 1, 1.4, 2 * Dt), 12);   // a 30 Hz step = two 60 Hz steps
        }

        [Fact]
        public void Follow_ConvergesOnTheFrame_AndMatchesThePrototypeStepAt60Hz()
        {
            var rig = new CameraRig(C, PrologueFraming.Build());
            CameraRigInput i = At(4.0);
            double cx = rig.FrameFor(i).Cx;   // 4.0 + 0.6
            Assert.Equal(4.6, cx, 12);

            // One step = the prototype's x += (cx − x)·min(1, dt·1.6).
            double x0 = rig.X;
            rig.Step(i, Dt);
            Assert.Equal(x0 + (cx - x0) * (Dt * 1.6), rig.X, 12);

            for (int n = 0; n < 60 * 8; n++) rig.Step(i, Dt);
            Assert.True(Math.Abs(rig.X - cx) < 1e-3, "x " + rig.X);
            Assert.True(Math.Abs(rig.Distance - 5.2) < 1e-3);
            Assert.True(Math.Abs(rig.Height - 1.0) < 1e-3);
            Assert.True(Math.Abs(rig.LookHeight - 0.8) < 1e-3);
            Assert.Equal(new Vec3(rig.X, rig.Height, rig.Distance), rig.Pose.Position);
        }

        [Fact]
        public void Follow_IsFrameRateIndependent()
        {
            var a = new CameraRig(C, PrologueFraming.Build());
            var b = new CameraRig(C, PrologueFraming.Build());
            // A cut to a new target, then 4 s at 60 Hz vs 30 Hz: the exact damping lands both at the same place.
            CameraRigInput i = At(9.5, 0.6); i.Push = CameraPush.Act;
            for (int n = 0; n < 240; n++) a.Step(i, Dt);
            for (int n = 0; n < 120; n++) b.Step(i, 2 * Dt);
            Assert.Equal(a.X, b.X, 9);                 // constant target: exact
            Assert.Equal(a.PushAmount, b.PushAmount, 9);
            // Height/distance chase a target that moves with the push: equal to integration error only.
            Assert.True(Math.Abs(a.Height - b.Height) < 1e-3);
            Assert.True(Math.Abs(a.Distance - b.Distance) < 1e-3);
        }

        [Fact]
        public void SlowPace_AndPushIn_AndHeight()
        {
            var rig = new CameraRig(C, PrologueFraming.Build());
            CameraRigInput i = At(4.0); i.SlowFollow = true;
            double x0 = rig.X; rig.Step(i, Dt);
            Assert.Equal(x0 + (4.6 - x0) * (Dt * 0.6), rig.X, 12);

            i = At(4.0, 1.2); i.Push = CameraPush.Mantle;
            for (int n = 0; n < 60 * 12; n++) rig.Step(i, Dt);
            Assert.Equal(1.0, rig.PushAmount, 3);
            Assert.Equal(5.2 * (1 - 0.22), rig.Distance, 3);
            Assert.Equal(1.0 - 0.25 + 0.6 * 1.0, rig.Height, 3);
            Assert.Equal(0.8 - 0.2 + 0.5 * 1.0, rig.LookHeight, 3);
        }

        [Fact]
        public void Lead_FollowsFacingAndSpeed_AndDropsWhileHolding()
        {
            var rig = new CameraRig(C, PrologueFraming.Build());
            Assert.Equal(-(0.6 + 0.35 * 1.6), rig.Lead(At(3, 0, -1, -1.6)), 12);
            CameraRigInput hold = At(3, 0, 1, 0.9); hold.NoLead = true;
            Assert.Equal(0, rig.Lead(hold));
        }

        [Fact]
        public void Shot_BlendsInAt1_4_AndOutAt0_8_Smoothstepped()
        {
            var rig = new CameraRig(C, PrologueFraming.Build());
            CameraRigInput i = At(3.0);
            for (int n = 0; n < 600; n++) rig.Step(i, Dt);
            var shot = new ShotRequest("test", new Vec3(3, 2, 2), new Vec3(3, 0, 0), 50, 1.2);
            i.Shot = shot;
            CameraPose p = rig.Step(i, Dt);
            Assert.Equal(Dt * 1.4, rig.ShotWeightRaw, 12);
            Assert.Equal(Smooth.Step(Dt * 1.4), p.ShotWeight, 12);
            Assert.Equal("test", p.ShotName);
            for (int n = 0; n < 60 * 10; n++) p = rig.Step(i, Dt);
            Assert.True(p.ShotWeight > 0.999);
            Assert.True(Math.Abs(p.Focal - 50) < 0.01);
            i.Shot = null;
            double w = rig.ShotWeightRaw;
            rig.Step(i, Dt);
            Assert.Equal(w + (0 - w) * Dt * 0.8, rig.ShotWeightRaw, 12);
        }

        [Fact]
        public void MomentShot_FollowsTheCueClock_NotTheStep()
        {
            // A 0.3 s stall: the frame step is 1/60 but the cue clock moved 0.3 s; the shot catches up by the cue delta.
            var a = new CameraRig(C, PrologueFraming.Build());
            var b = new CameraRig(C, PrologueFraming.Build());
            CameraRigInput i = At(31.0);
            i.Shot = MomentShots.Kin(31.0, 0); a.Step(i, Dt); b.Step(i, Dt);
            i.Shot = MomentShots.Kin(31.0, 0.3);
            a.Step(i, Dt);
            double raw = b.ShotWeightRaw;
            b.Step(i, 0.3);
            Assert.Equal(b.ShotWeightRaw, a.ShotWeightRaw, 12);
            Assert.Equal(raw + (1 - raw) * Damp.Factor(1.4, 0.3), a.ShotWeightRaw, 12);
            // and the delta is clamped at 0.5 s
            var c = new CameraRig(C, PrologueFraming.Build());
            i.Shot = MomentShots.Kin(31.0, 0); c.Step(i, Dt);
            i.Shot = MomentShots.Kin(31.0, 5.0); c.Step(i, Dt);
            Assert.Equal(Damp.Toward(Damp.Factor(1.4, Dt), 1, 1.4, 0.5), c.ShotWeightRaw, 12);
        }

        [Fact]
        public void Shake_DecaysAndIsOffInCalmMode()
        {
            var rig = new CameraRig(C, PrologueFraming.Build());
            rig.Shake(1, calm: true);
            Assert.Equal(0, rig.ShakeAmount);
            rig.Shake(1, calm: false);
            rig.Step(At(3), Dt);
            Assert.Equal(Math.Exp(-Dt * 5), rig.ShakeAmount, 12);
        }

        [Fact]
        public void Opening_StartsAtTheChest_AndEndsOnTheSideView()
        {
            var chest = new Vec3(1.0, 0.55, 0.1);
            CameraPose p0 = CameraRig.OpeningPose(C, 0, chest, Aspect);
            double s = Math.Sin(Math.PI / 4);
            Assert.Equal(chest.X + s * 1.05, p0.Position.X, 12);
            Assert.Equal(chest.Y + 0.12, p0.Position.Y, 12);
            Assert.Equal(50, p0.Focal, 12);
            CameraPose p1 = CameraRig.OpeningPose(C, 300, chest, Aspect);
            Assert.Equal(1.9, p1.Position.X, 9); Assert.Equal(1.0, p1.Position.Y, 9); Assert.Equal(Math.Max(5.2, C.WidthFit(35, 4.6, Aspect)), p1.Position.Z, 9);
            Assert.Equal(35, p1.Focal, 9);
            Assert.Equal(C.OpeningEndTarget, p1.Look);
        }

        [Fact]
        public void Lens_VerticalFov_MatchesThreeJsFilmGauge36()
        {
            // three.js: fov = 2·atan(0.5·(36 / aspect) / focal) for aspect ≥ 1.
            Assert.Equal(2 * Math.Atan(18 / (35 * Aspect)) * 180 / Math.PI, C.VerticalFovDegrees(35, Aspect), 12);
            Assert.Equal(2 * Math.Atan(18 / 35.0) * 180 / Math.PI, C.VerticalFovDegrees(35, 0.5), 12);
        }

        [Fact]
        public void Rig_IsDeterministic()
        {
            List<CameraPose> Run()
            {
                var rig = new CameraRig(C, PrologueFraming.Build());
                var s = new FramingSignalTable();
                var poses = new List<CameraPose>();
                for (int n = 0; n < 2400; n++)
                {
                    double x = 0.5 + n * 0.02;
                    s.Set(PrologueFraming.Dl02, PrologueFraming.Dl02Signal(x < 11.45 ? 1 : 2, x > 10.4 ? 1 : -1, x));
                    CameraRigInput i = At(x, Math.Abs(Math.Sin(n * 0.01)), n % 300 < 150 ? 1 : -1, 0.9, s);
                    if (n == 900) rig.Shake(0.8, false);
                    if (n > 1000 && n < 1500) i.Shot = MomentShots.Kin(31, (n - 1000) / 60.0);
                    poses.Add(rig.Step(i, Dt));
                }
                return poses;
            }
            List<CameraPose> a = Run(), b = Run();
            for (int n = 0; n < a.Count; n++)
            {
                Assert.Equal(a[n].Position, b[n].Position);
                Assert.Equal(a[n].Look, b[n].Look);
                Assert.Equal(a[n].Focal, b[n].Focal);
                Assert.Equal(a[n].Fog, b[n].Fog);
            }
        }
    }
}
