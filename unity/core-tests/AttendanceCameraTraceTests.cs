using System;
using System.Collections.Generic;
using DeadLetter.Core.Camera;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Streaming;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Chapter 1's camera (issue #50, U-22b), replayed against the prototype: the whole of
    /// Traces/attendance_mech_seed1.jsonl.gz through ONE <see cref="ChapterSim"/> over <see cref="ChapterDefs.Attendance"/>,
    /// read by a <see cref="ChapterPresenter"/> and followed by a <see cref="CameraRig"/> on
    /// <see cref="ChapterFraming.For"/>("attendance"), placed and stepped as <c>GameHost</c> does it. Every step's side view
    /// (the rig's lane camera before an authored shot blends in: <c>cam</c> after <c>updateCamera</c>'s framing step,
    /// L7787–L7804) is compared with the recorded one at 1e-6: position, look target, fov and fog.
    /// </summary>
    public class AttendanceCameraTraceTests
    {
        private const string TraceFile = AttendanceChapterTraceTests.TraceFile;
        /// <summary>The recorder's page: a 320×180 viewport (record_trace.mjs), so <c>camera.aspect</c> is 16:9.</summary>
        private const double Aspect = 320.0 / 180.0;

        private sealed class Row
        {
            public TraceStep P;
            public Vec Pos, Look;
            public double Fov, Fog;
        }

        private struct Vec { public double X, Y, Z; }

        private static List<Row> _cached;
        private static readonly object Gate = new object();

        private static List<Row> Run()
        {
            lock (Gate)
            {
                if (_cached != null) return _cached;
                var t = Trace.Load(TraceFile);
                int from = t.FirstIndex(p => p.Mode == "play");
                var sim = new ChapterSim(ChapterDefs.Attendance());
                var presenter = new ChapterPresenter(sim);
                var signals = new FramingSignalTable();
                var rig = new CameraRig(CameraConfig.Prototype, ChapterFraming.For(ChapterDefs.AttendanceId));
                sim.Clock = from > 0 ? t.Steps[from - 1].Clk : 0;
                sim.Begin("school");

                // GameHost.AfterPlacement: the rig snaps to the frame where he is placed (startPlay, L8115).
                presenter.UpdateSignals(signals);
                CameraRigInput placed = presenter.CameraInput(Aspect, signals);
                rig.SnapToFrame(placed);
                rig.Step(placed, 0);

                var rows = new List<Row>();
                for (int k = from; k < t.Steps.Count; k++)
                {
                    sim.Step(t.Steps[k].Input);
                    presenter.UpdateSignals(signals);                                          // GameHost.StepOnce
                    CameraPose pose = rig.Step(presenter.CameraInput(Aspect, signals), ChapterSim.StepSeconds);
                    rows.Add(new Row
                    {
                        P = t.Steps[k],
                        Pos = new Vec { X = rig.X, Y = rig.Height, Z = rig.Distance },
                        Look = new Vec { X = rig.X, Y = rig.LookHeight, Z = 0 },
                        Fov = rig.Config.VerticalFovDegrees(rig.Config.BaseFocal, Aspect),
                        Fog = pose.Fog,
                    });
                }
                return _cached = rows;
            }
        }

        [Fact]
        public void TheTrace_CarriesTheCamera_InEveryStep()
        {
            var rows = Run();
            Assert.Equal(20842, rows.Count);
            foreach (var w in rows)
            {
                Assert.Equal(6, w.P.Region);
                Assert.True(w.P.CamX6.HasValue && w.P.CamY6.HasValue && w.P.CamZ6.HasValue && w.P.LookX6.HasValue
                            && w.P.LookY6.HasValue && w.P.LookZ6.HasValue && w.P.Fov6.HasValue && w.P.Fog6.HasValue, "#" + w.P.I);
            }
        }

        [Fact]
        public void Position_MatchesEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Run())
            {
                Check(bad, w.P.I, "cam.x " + Where(w), w.P.CamX6.Value, w.Pos.X);
                Check(bad, w.P.I, "cam.y " + Where(w), w.P.CamY6.Value, w.Pos.Y);
                Check(bad, w.P.I, "cam.dist " + Where(w), w.P.CamZ6.Value, w.Pos.Z);
            }
            Assert.True(bad.Count == 0, Report(bad));
        }

        [Fact]
        public void LookTarget_MatchesEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Run())
            {
                Check(bad, w.P.I, "look.x " + Where(w), w.P.LookX6.Value, w.Look.X);
                Check(bad, w.P.I, "look.y " + Where(w), w.P.LookY6.Value, w.Look.Y);
                Check(bad, w.P.I, "look.z " + Where(w), w.P.LookZ6.Value, w.Look.Z);
            }
            Assert.True(bad.Count == 0, Report(bad));
        }

        [Fact]
        public void Fov_And_Fog_MatchEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Run())
            {
                Check(bad, w.P.I, "fov", w.P.Fov6.Value, w.Fov);
                Check(bad, w.P.I, "fog " + Where(w), w.P.Fog6.Value, w.Fog);
            }
            Assert.True(bad.Count == 0, Report(bad));
        }

        /// <summary>The run goes through every framing zone's ground, so no zone is untested: DL-12 to DL-17 and the duct.</summary>
        [Fact]
        public void TheRun_CrossesEveryZone()
        {
            var rows = Run();
            double maxX = double.NegativeInfinity;
            bool duct = false;
            foreach (var w in rows) { maxX = Math.Max(maxX, w.P.X); duct |= w.P.Aw == "duct"; }
            Assert.True(duct);
            Assert.True(maxX > 341.1, "past DL-17's landing: " + maxX);
            foreach (var z in ChapterFraming.For(ChapterDefs.AttendanceId).Zones)
                if (!double.IsNaN(z.XIn)) Assert.True(maxX > z.XIn + z.XInBlend, z.Name);
        }

        private static string Where(Row w) => $"(x {w.P.X:0.###} {w.P.Act ?? "-"}/{w.P.Aw ?? "-"})";
    }
}
