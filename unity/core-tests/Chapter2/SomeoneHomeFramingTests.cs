using System;
using System.Collections.Generic;
using DeadLetter.Core.Camera;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Streaming;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Chapter 2's framing (#53, <see cref="SomeoneHomeFraming"/>): the lens per zone, what DL-18's and DL-19's §7 say each
    /// frame holds, D-17 in frame everywhere on the lane in every leaf and jack state, the scripted solves through
    /// <see cref="ChapterSim"/>, <see cref="ChapterPresenter"/> and <see cref="CameraRig"/>, and the seam from chapter 1.
    /// </summary>
    public class SomeoneHomeFramingTests
    {
        private const double Dt = ChapterSim.StepSeconds;
        private static readonly CameraConfig C = CameraConfig.Prototype;
        private static readonly FramingSignalTable NoSignals = new FramingSignalTable();
        private static readonly MotorInput Right = new MotorInput { Move = 1 };
        /// <summary>The frame's inner part D-17 stays in at rest: 5% of the frame clear on every side.</summary>
        private const double Margin = 0.9;
        /// <summary>How far the rig's x may move in one step (6 m/s): it eases, so more is a jump.</summary>
        private const double MaxStepX = 0.1;

        /// <summary>16:9, the Switch handheld (1280×720: the same aspect, checked on its own) and 4:3 as the narrowest.</summary>
        public static IEnumerable<object[]> Aspects() => new[]
        {
            new object[] { "16:9", 16.0 / 9.0 }, new object[] { "switch handheld", 1280.0 / 720.0 }, new object[] { "4:3", 4.0 / 3.0 },
        };

        // ---- Projection ---------------------------------------------------------------------------------------------------

        /// <summary>
        /// Where <paramref name="q"/> lands in the frame of <paramref name="p"/>: −1..1 across and up (three.js with the 36 mm
        /// gauge across the frame, aspect ≥ 1, as <see cref="CameraConfig.VerticalFovDegrees"/>).
        /// </summary>
        internal static (double U, double V) Project(CameraPose p, double aspect, Vec3 q)
        {
            Vec3 f = p.Look - p.Position;
            f = f * (1 / f.Length);
            var r = new Vec3(-f.Z, 0, f.X);
            r = r * (1 / r.Length);
            var up = new Vec3(r.Y * f.Z - r.Z * f.Y, r.Z * f.X - r.X * f.Z, r.X * f.Y - r.Y * f.X);
            Vec3 d = q - p.Position;
            double z = Dot(d, f);
            Assert.True(z > 0, "behind the camera: " + q + " from " + p.Position);
            double tanH = C.FilmGauge * 0.5 / p.Focal, tanV = tanH / Math.Max(aspect, 1);
            return (Dot(d, r) / (z * tanH), Dot(d, up) / (z * tanV));
        }

        private static double Dot(Vec3 a, Vec3 b) => a.X * b.X + a.Y * b.Y + a.Z * b.Z;

        /// <summary>The worst |u| or |v| of D-17's standing box (half-width either side, feet to head) at (x, y).</summary>
        internal static double BodyExtent(CameraPose p, double aspect, double x, double y)
        {
            double worst = 0;
            foreach (double bx in new[] { x - Body.Half, x + Body.Half })
                foreach (double by in new[] { y, y + Body.StandHeight })
                {
                    var (u, v) = Project(p, aspect, new Vec3(bx, by, 0));
                    worst = Math.Max(worst, Math.Max(Math.Abs(u), Math.Abs(v)));
                }
            return worst;
        }

        /// <summary>D-17's body: chapter 2's motor config.</summary>
        private static readonly MotorConfig Body = new ChapterSim(ChapterDefs.SomeoneHome()).Config;

        /// <summary>The rig at rest on him at (x, y) facing <paramref name="facing"/>: snapped, then eased until it is still.</summary>
        private static CameraPose Rest(CameraRig rig, double x, double y, int facing, double aspect)
        {
            var i = new CameraRigInput { X = x, Y = y, Facing = facing, Aspect = aspect, Signals = NoSignals };
            rig.SnapToFrame(i);
            CameraPose p = default;
            for (int k = 0; k < 12; k++) p = rig.Step(i, 1.0);                                  // Damp is exact at any dt: e^(−1.4·12) ≈ 5e-8
            return p;
        }

        // ---- The track ----------------------------------------------------------------------------------------------------

        [Fact]
        public void EachZone_HasItsScenesLens_AndTheProloguesAndChapter1sStayAt35mm()
        {
            var t = SomeoneHomeFraming.Build();
            double At(double x, double y) => t.Evaluate(x, y, 0, NoSignals, C, C.Aspect).Focal;
            Assert.Equal(32, At(348.0, 0));                                                          // DL-18 §7 arrival
            Assert.Equal(35, At(351.0, 0), 9);                                                       // gallery: normal
            Assert.Equal(40, At(353.0, 0), 9);                                                       // box room
            Assert.Equal(35, At(358.0, 1.2), 9);                                                     // terrace landing: no lens given
            Assert.Equal(38, At(364.0, 1.2), 9);                                                     // DL-19 §7 the repair
            Assert.Equal(30, At(372.0, 2.3), 9);                                                     // upper terrace
            for (double x = 347.0; x <= 377.0; x += 0.05)
            {
                double f = At(x, 0);
                Assert.True(f >= 30 && f <= 40, x + ": " + f);
            }
            foreach (FramingTrack other in new[] { PrologueFraming.Build(), AttendanceFraming.Build() })
                for (double x = 0; x < 340; x += 0.5)
                    Assert.Equal(C.BaseFocal, other.Evaluate(x, 0, 0.6, NoSignals, C, C.Aspect).Focal);  // exactly: NaN zones keep 35
        }

        [Fact]
        public void AZonesFocal_BlendsLikeItsFog_AndItsFitUsesItsOwnLens()
        {
            var baseZone = FramingZone.Named("base").WithCx(0, 0).WithVolume(5, 1, 1).WithFog(0.02);
            var wide = FramingZone.Named("wide").In(10, 2).WithVolume(5, 1, 1, 8).WithFog(0.04).WithFocal(30);
            var t = new FramingTrack(baseZone, wide);
            Frame half = t.Evaluate(11, 0, 0, NoSignals, C, C.Aspect), full = t.Evaluate(13, 0, 0, NoSignals, C, C.Aspect);
            Assert.Equal(35, t.Evaluate(9, 0, 0, NoSignals, C, C.Aspect).Focal);
            Assert.Equal(32.5, half.Focal, 12);                                                       // smooth(0.5) = 0.5, as the fog
            Assert.Equal(0.03, half.Fog, 12);
            Assert.Equal(30, full.Focal, 12);
            Assert.Equal(C.WidthFit(30, 8, C.Aspect), full.Volume.Distance, 12);                     // 8 m at 30 mm, not at 35
        }

        [Fact]
        public void TheRig_EasesItsLensTowardTheFrames_AndSnapsToIt()
        {
            var rig = new CameraRig(C, SomeoneHomeFraming.Build());
            var i = new CameraRigInput { X = 353.0, Y = 0, Facing = 1, Signals = NoSignals };
            Assert.Equal(35, rig.Focal);
            CameraPose p = rig.Step(i, Dt);
            Assert.Equal(35 + 5 * Damp.Factor(C.FollowRate, Dt), p.Focal, 12);                    // eased like the distance
            rig.SnapToFrame(i);
            Assert.Equal(40, rig.Focal, 12);
            Assert.Equal(40, rig.Step(i, Dt).Focal, 12);
        }

        /// <summary>DL-18 §7: the arrival holds the sealed Works door (347.4–348.6, to 2.1) while he walks the first 2.5 m.</summary>
        [Theory]
        [MemberData(nameof(Aspects))]
        public void DL18_TheArrivalFrame_HoldsTheSealedDoor(string name, double aspect)
        {
            var rig = new CameraRig(C, SomeoneHomeFraming.Build());
            for (double x = Dl18Lane.StairHeadX; x <= 349.5; x += 0.05)
                foreach (int facing in new[] { 1, -1 })
                {
                    CameraPose p = Rest(rig, x, 0, facing, aspect);
                    Assert.Equal(SomeoneHomeFraming.ArrivalFocal, p.Focal, 9);
                    foreach (var q in new[] { new Vec3(347.4, 0, 0), new Vec3(348.6, 2.1, 0) })
                    {
                        var (u, v) = Project(p, aspect, q);
                        Assert.True(Math.Abs(u) <= 1 && Math.Abs(v) <= 1, name + ": at " + x.ToString("F2") + " " + q + " is out of frame (" + u.ToString("F3") + ", " + v.ToString("F3") + ")");
                    }
                }
        }

        /// <summary>DL-18 §7: the box room door to the landing doorway, floor to frame top (1.5), while he is anywhere in the room.</summary>
        [Theory]
        [MemberData(nameof(Aspects))]
        public void DL18_TheBoxRoomFrame_HoldsDoorToDoorway_FloorToTheFramesTop(string name, double aspect)
        {
            var rig = new CameraRig(C, SomeoneHomeFraming.Build());
            for (double x = Dl18Lane.RoomX0 + 0.2; x <= Dl18Lane.SillX - Body.Half; x += 0.05)
                foreach (int facing in new[] { 1, -1 })
                {
                    CameraPose p = Rest(rig, x, 0, facing, aspect);
                    Assert.Equal(SomeoneHomeFraming.BoxRoomFocal, p.Focal, 9);
                    foreach (var q in new[] { new Vec3(SomeoneHomeFraming.BoxRoomHoldX0, 0, 0), new Vec3(SomeoneHomeFraming.BoxRoomHoldX1, SomeoneHomeFraming.BoxRoomHoldTop, 0) })
                    {
                        var (u, v) = Project(p, aspect, q);
                        Assert.True(Math.Abs(u) <= 1 && Math.Abs(v) <= 1, name + ": at " + x.ToString("F2") + " " + q + " is out of frame (" + u.ToString("F3") + ", " + v.ToString("F3") + ")");
                    }
                }
        }

        /// <summary>DL-19 §7: the jack bay to the top of the upper flight, floor (1.2) to the drip tube, from the floor and the half landing.</summary>
        [Theory]
        [MemberData(nameof(Aspects))]
        public void DL19_TheRepairFrame_HoldsTheBayToTheFlightsTop_FloorToBarnaby(string name, double aspect)
        {
            var rig = new CameraRig(C, SomeoneHomeFraming.Build());
            for (double x = 362.0; x <= 366.0; x += 0.05)
                foreach (double y in x < 363.5 ? new[] { Dl19Lane.FloorY } : new[] { Dl19Lane.LevelY })
                    foreach (int facing in new[] { 1, -1 })
                    {
                        CameraPose p = Rest(rig, x, y, facing, aspect);
                        Assert.Equal(SomeoneHomeFraming.RepairFocal, p.Focal, 9);
                        foreach (var q in new[] { new Vec3(SomeoneHomeFraming.RepairHoldX0, SomeoneHomeFraming.RepairHoldBottom, 0), new Vec3(SomeoneHomeFraming.RepairHoldX1, SomeoneHomeFraming.RepairHoldTop, 0) })
                        {
                            var (u, v) = Project(p, aspect, q);
                            Assert.True(Math.Abs(u) <= 1 && Math.Abs(v) <= 1, name + ": at " + x.ToString("F2") + "," + y + " " + q + " is out of frame (" + u.ToString("F3") + ", " + v.ToString("F3") + ")");
                        }
                    }
        }

        // ---- (a) D-17 in frame along the whole lane, in every leaf and jack state -------------------------------------------

        public static IEnumerable<object[]> LeafStates()
        {
            foreach (var a in Aspects())
                foreach (var c in Dl18SkipSearchTests.Configurations()) yield return new[] { c[0], a[0], a[1] };
        }

        public static IEnumerable<object[]> JackStates()
        {
            string[] states =
            {
                "bay", "bayOnStops", "pocket", "pocketOnStops", "pocketHeld", "pocketLevel", "pocketTop", "pocketForkEmpty",
                "pocketSpareCarried", "pocketPinnedRaised", "pocketPinnedDown", "free", "solved",
            };
            foreach (var a in Aspects())
                foreach (string s in states) yield return new[] { s, a[0], a[1] };
        }

        /// <summary>
        /// Every 0.05 m of DL-18's lane (347.0 to 361.0), standing on the floor and on whatever he stands on there (the bed,
        /// the bench, the sill and the landing), facing either way, the rig at rest: his whole body is inside the frame's
        /// inner 90%.
        /// </summary>
        [Theory]
        [MemberData(nameof(LeafStates))]
        public void A_DL18_HeStaysInFrame_AtEvery5cm_InEveryLeafState(string leaves, string name, double aspect)
        {
            ChapterSim s = Dl18SkipSearchTests.Configure(leaves);
            SweepInFrame(s, Dl18Lane.StairHeadX, Dl18Lane.EndX, 0, leaves + ", " + name, aspect);
        }

        /// <summary>
        /// The same along DL-19's lane (361.0 to 377.0): the terrace landing, the half landing in each of its states and the
        /// upper terrace. The jack is never stood on (DL-19 §3: a column in the lane, not climbable), so where it stands the
        /// highest surface is the floor beside it.
        /// </summary>
        [Theory]
        [MemberData(nameof(JackStates))]
        public void A_DL19_HeStaysInFrame_AtEvery5cm_InEveryJackState(string jack, string name, double aspect)
        {
            ChapterSim s = Dl19ChapterTests.Setup(jack);
            SweepInFrame(s, Dl19Lane.X0, Dl19Lane.X1, Dl19Lane.FloorY, jack + ", " + name, aspect);
        }

        private static void SweepInFrame(ChapterSim s, double x0, double x1, double floor, string what, double aspect)
        {
            var rig = new CameraRig(C, SomeoneHomeFraming.Build());
            int n = (int)Math.Round((x1 - x0) / 0.05), checkedPoints = 0;
            for (int k = 0; k <= n; k++)
            {
                double x = x0 + k * 0.05;
                double top = s.Lane.SupportAt(x);
                var ys = new List<double>();
                if (double.IsFinite(top) && top < Dl19Lane.ColumnTop - 1) ys.Add(top);                // not on the jack's column
                if (x < (floor > 0 ? Dl19Lane.FlightX0 : Dl18Lane.SillX) && !ys.Contains(floor)) ys.Add(floor);
                foreach (double y in ys)
                    foreach (int facing in new[] { 1, -1 })
                    {
                        CameraPose p = Rest(rig, x, y, facing, aspect);
                        double e = BodyExtent(p, aspect, x, y);
                        Assert.True(e <= Margin, what + ": at x " + x.ToString("F2") + " y " + y.ToString("F3") + " facing " + facing
                            + " he reaches " + e.ToString("F3") + " of the frame (focal " + p.Focal.ToString("F1") + ", camera " + p.Position + ")");
                        checkedPoints++;
                    }
            }
            Assert.True(checkedPoints >= 2 * (n + 1), what + ": " + checkedPoints);                     // every x, facing either way
        }

        // ---- (b) The scripted solves through ChapterSim, ChapterPresenter and CameraRig ---------------------------------------

        /// <summary>The rig as GameHost drives it over a sim, with what each step must hold.</summary>
        private sealed class Filmed
        {
            public readonly ChapterPresenter Presenter;
            public readonly CameraRig Rig;
            private readonly FramingSignalTable _signals = new FramingSignalTable();
            private readonly double _aspect;
            public int Steps;
            public double MinFocal = double.PositiveInfinity, MaxFocal = double.NegativeInfinity, MaxStepX, WorstExtent;
            private double _lastX = double.NaN;

            public Filmed(ChapterSim s, double aspect)
            {
                _aspect = aspect;
                Presenter = new ChapterPresenter(s);
                Rig = new CameraRig(C, ChapterFraming.For(s.Def.Id));
                Presenter.UpdateSignals(_signals);
                Rig.SnapToFrame(Presenter.CameraInput(aspect, _signals));
                _lastX = Rig.X;
            }

            public void Shoot(ChapterSim s)
            {
                Presenter.UpdateSignals(_signals);
                CameraPose p = Rig.Step(Presenter.CameraInput(_aspect, _signals), Dt);
                Steps++;
                Assert.True(double.IsFinite(p.Position.X) && double.IsFinite(p.Position.Y) && double.IsFinite(p.Position.Z)
                    && double.IsFinite(p.Look.X) && double.IsFinite(p.Look.Y) && double.IsFinite(p.Focal), "step " + Steps + ": " + p.Position);
                MaxStepX = Math.Max(MaxStepX, Math.Abs(Rig.X - _lastX));
                Assert.True(Math.Abs(Rig.X - _lastX) <= SomeoneHomeFramingTests.MaxStepX, "step " + Steps + " at x " + s.X.ToString("F3") + ": cx " + _lastX + " → " + Rig.X);
                _lastX = Rig.X;
                MinFocal = Math.Min(MinFocal, p.Focal);
                MaxFocal = Math.Max(MaxFocal, p.Focal);
                WorstExtent = Math.Max(WorstExtent, BodyExtent(p, _aspect, s.X, s.Y));
                Assert.True(WorstExtent <= 1, "step " + Steps + ": he leaves the frame at x " + s.X.ToString("F3") + " y " + s.Y.ToString("F3"));
            }
        }

        /// <summary>
        /// DL-18's solve (<c>Dl18ChapterTests.Solve</c>) from <c>ring_a</c>, then DL-19's (<c>Dl19ChapterTests.Play.Solve</c>) from
        /// the terrace, then on along the upper terrace to DL-20's door: no NaN, cx eases (no step moves it more than 0.1 m), the
        /// lens stays within 30–40 mm, and he never leaves the frame (mantles and acts push in).
        /// </summary>
        [Theory]
        [MemberData(nameof(Aspects))]
        public void B_TheScriptedSolves_FramedThroughTheRig_HaveNoNaN_AContinuousCx_AndALensIn30To40(string name, double aspect)
        {
            ChapterSim s = Dl18ChapterTests.Begin();
            var film = new Filmed(s, aspect);
            Dl18ChapterTests.Solve(s, film.Shoot);
            Assert.Equal("terrace", s.Checkpoints.Current.Name);
            new Dl19ChapterTests.Play(s, film.Shoot).Solve();
            Assert.Equal("repaired", s.Checkpoints.Current.Name);
            for (int i = 0; i < 60 * 10 && s.X < Dl19Lane.X1 - 0.5; i++) { s.Step(Right); film.Shoot(s); }
            Assert.True(s.X >= Dl19Lane.X1 - 0.5, name + ": " + s.X);

            Assert.True(film.MinFocal >= 30 - 1e-9 && film.MaxFocal <= 40 + 1e-9, name + ": " + film.MinFocal + "–" + film.MaxFocal);
            Assert.True(film.MinFocal < 31 && film.MaxFocal > 39, name + ": the run sees the box room's and the upper terrace's lenses");
            Assert.True(film.MaxStepX > 0);
        }

        /// <summary>DL-19's own solve from <c>half_landing</c> (its <c>ScriptedSolve</c>), framed the same way.</summary>
        [Theory]
        [MemberData(nameof(Aspects))]
        public void B_DL19sSolve_FromHalfLanding_FramedThroughTheRig(string name, double aspect)
        {
            ChapterSim s = Dl19ChapterTests.Begin();
            var film = new Filmed(s, aspect);
            new Dl19ChapterTests.Play(s, film.Shoot).Solve();
            Assert.Equal("repaired", s.Checkpoints.Current.Name);
            Assert.True(film.MinFocal >= 30 - 1e-9 && film.MaxFocal <= 40 + 1e-9, name + ": " + film.MinFocal + "–" + film.MaxFocal);
            Assert.True(film.Steps > 600, name);
        }

        // ---- (c) Across the seam ------------------------------------------------------------------------------------------

        /// <summary>
        /// The seam run (<c>ChapterSeamTests.Run</c>: chapter 1's trace, the stair walk, the handover, chapter 2's first 2 s
        /// walking right), filmed as GameHost films it: chapter 1's track, then <see cref="CameraRig.UseTrack"/> with chapter 2's
        /// at its origin. In the world, <see cref="CameraRig.UseTrack"/> moves nothing; every step after it is the rig's own
        /// easing toward chapter 2's frame (x at the follow rate, the lens at the distance's rate, nothing more than 0.1 m), and
        /// it converges: the gap to the arrival frame is under a third of the handover's in 2 s, and D-17 is back inside the
        /// frame's inner 90% within 1 s and stays there.
        /// <para>He is out of frame at the handover itself: chapter 1's DL-17 frame holds cx at most 339.0 (L5877) while the
        /// stair walk takes him to 347.0. That is chapter 1's framing past the prototype's end, not chapter 2's.</para>
        /// </summary>
        [Fact]
        public void C_AcrossTheSeam_ThePoseEasesOntoChapter2sFrame_WithNoJump()
        {
            var r = ChapterSeamTests.Run();
            Assert.Equal(r.Rows.Count, r.Poses.Count);
            Assert.Equal("dl18.arrival", r.Rig.Track.Base.Name);
            ChapterSeams.Origin(ChapterDefs.SomeoneHomeId, out double ox, out double oy);
            Assert.Equal(new Vec3(ox, oy, 0), r.Rig.Origin);
            int h = r.HandoverRow, last = r.Poses.Count - 1;

            CameraPose before = r.Poses[h - 1], at = r.PoseAtUseTrack;                                 // UseTrack moves nothing
            Assert.True((at.Position - before.Position).Length < 1e-9 && (at.Look - before.Look).Length < 1e-9, before.Position + " → " + at.Position);
            Assert.Equal(before.Focal, at.Focal);

            double kx = Damp.Factor(C.FollowRateX, Dt), k = Damp.Factor(C.FollowRate, Dt);
            for (int i = Math.Max(1, r.ExitRow - 120); i <= last; i++)
            {
                CameraPose a = r.Poses[i - 1], b = r.Poses[i];
                string row = "row " + i + (i == h ? " (the handover)" : "") + ": ";
                Assert.True(Math.Abs(b.Position.Y - a.Position.Y) <= MaxStepX && Math.Abs(b.Position.Z - a.Position.Z) <= MaxStepX
                    && Math.Abs(b.Look.Y - a.Look.Y) <= MaxStepX, row + a.Position + " → " + b.Position);
                double eased = i >= h ? kx * Math.Abs(r.Frames[i].Cx + ox - a.Position.X) + 1e-9 : MaxStepX;
                Assert.True(Math.Abs(b.Position.X - a.Position.X) <= eased, row + "x " + a.Position.X + " → " + b.Position.X);
                Assert.True(Math.Abs(b.Focal - a.Focal) <= k * Math.Abs(r.Frames[i].Focal - a.Focal) + 1e-9, row + "focal " + a.Focal + " → " + b.Focal);
            }

            // The lens: chapter 1's 35 mm up to the handover, then easing toward the arrival's 32 mm (and on toward the
            // gallery's 35 as he walks past 349.5), each step nearer the frame's and never past it.
            Assert.Equal(C.BaseFocal, before.Focal);
            Assert.Equal(SomeoneHomeFraming.ArrivalFocal, r.Frames[h].Focal);
            Assert.True(r.Poses[h].Focal < before.Focal);
            for (int i = h; i <= last; i++)
            {
                double want = r.Frames[i].Focal, a = (i == h ? before : r.Poses[i - 1]).Focal, b = r.Poses[i].Focal;
                Assert.True(Math.Abs(b - want) <= Math.Abs(a - want) && (b - want) * (a - want) >= 0, "row " + i + ": focal " + a + " → " + b + " toward " + want);
            }

            double Gap(int i)
            {
                Frame f = r.Frames[i];
                CameraPose p = r.Poses[i];
                return Math.Abs(p.Position.X - ox - f.Cx) + Math.Abs(p.Position.Z - f.Volume.Distance) + Math.Abs(p.Focal - f.Focal);
            }
            Assert.True(Gap(last) < Gap(h) / 3, "gap " + Gap(h) + " → " + Gap(last));

            for (int i = h + 60; i <= last; i++)
            {
                double e = BodyExtent(r.Poses[i], C.Aspect, r.Rows[i].X + ox, r.Rows[i].Y + oy);
                Assert.True(e <= Margin, "row " + i + ": he reaches " + e.ToString("F3") + " of the frame at x " + r.Rows[i].X.ToString("F3"));
            }
        }
    }
}
