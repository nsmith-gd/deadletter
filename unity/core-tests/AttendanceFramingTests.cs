using System;
using DeadLetter.Core.Camera;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Streaming;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// <see cref="ChapterFraming"/>, <see cref="AttendanceFraming"/> and its eased state (issue #50). The whole track is
    /// checked against the prototype step by step in <see cref="AttendanceCameraTraceTests"/>; these pin the pieces.
    /// </summary>
    public class AttendanceFramingTests
    {
        private static readonly CameraConfig C = CameraConfig.Prototype;

        [Fact]
        public void ChapterFraming_PicksTheChaptersTrack_NullOtherwise()
        {
            Assert.NotNull(ChapterFraming.For(ChapterDefs.PrologueId));
            Assert.NotNull(ChapterFraming.For(ChapterDefs.AttendanceId));
            Assert.Equal("dl01.alcove", ChapterFraming.For(ChapterDefs.PrologueId).Base.Name);
            Assert.Equal("dl12.register", ChapterFraming.For(ChapterDefs.AttendanceId).Base.Name);
            Assert.Equal("dl18.arrival", ChapterFraming.For(ChapterDefs.SomeoneHomeId).Base.Name);
            Assert.Null(ChapterFraming.For("no_such_chapter"));
            Assert.Null(ChapterFraming.For(null));
        }

        [Fact]
        public void DL12_TheRegister_IsClampedAndFitTo8_8m()
        {
            var t = AttendanceFraming.Build();
            var s = new FramingSignalTable();
            Frame f = t.Evaluate(200.8, 0, 0, s, C, C.Aspect);
            Assert.Equal(203.6, f.Cx);                                       // clamp(x + 0.5·lead, 203.6, 207.0)
            Assert.Equal(C.WidthFit(35, 8.8, C.Aspect), f.Volume.Distance, 12);
            Assert.Equal(1.45, f.Volume.Height);
            Assert.Equal(0.035, f.Fog);
        }

        [Fact]
        public void TheDuct_TakesTheWholeFrame_OnHim()
        {
            var t = AttendanceFraming.Build();
            var s = new FramingSignalTable().Set(AttendanceFraming.Duct, 1);
            Frame f = t.Evaluate(244.0, 2.0, 0.9, s, C, C.Aspect);
            Assert.Equal(244.0, f.Cx, 9);                                     // cx: x, no lead
            Assert.Equal(2.4, f.Volume.Height, 9);
            Assert.Equal(0.03, f.Fog, 9);
        }

        [Fact]
        public void DL17_TheWorkshop_ReachesFurther_AsTheStairDoorOpens()
        {
            var t = AttendanceFraming.Build();
            var shut = t.Evaluate(340.0, 0, 0.6, new FramingSignalTable(), C, C.Aspect);
            var open = t.Evaluate(340.0, 0, 0.6, new FramingSignalTable().Set(AttendanceFraming.Door17, 1), C, C.Aspect);
            Assert.Equal(336.8, shut.Cx, 9);
            Assert.Equal(339.0, open.Cx, 9);                                  // 336.8 + 2.2, x + 0.4·lead = 340.24 beyond it
            Assert.Equal(shut.Volume.Distance, open.Volume.Distance);         // cx only (L5877's volume is commented out)
        }

        [Fact]
        public void DL15_TheBalcony_BlendsOverTheClassroom()
        {
            var t = AttendanceFraming.Build();
            var room = t.Evaluate(286.0, 0, 0, new FramingSignalTable().Set(AttendanceFraming.Balcony, 0), C, C.Aspect);
            var balc = t.Evaluate(286.0, 0, 0, new FramingSignalTable().Set(AttendanceFraming.Balcony, 1), C, C.Aspect);
            Assert.Equal(286.0, room.Cx, 9);
            Assert.Equal(281.3, balc.Cx, 9);
            Assert.Equal(2.5, balc.Volume.Height, 9);
        }

        [Fact]
        public void TheEasedState_StartsAt0And1_EasesAt0_9_AndResets()
        {
            var a = new AttendanceFramingState();
            Assert.Equal(0, a.K13);
            Assert.Equal(1, a.K15);
            a.Step(lessonOn: true, x: 218, y: 0, dt: 1.0 / 60);
            Assert.Equal(0.9 / 60, a.K13, 12);                                // k += (1 − k)·min(1, dt·0.9)
            Assert.Equal(1 - 0.9 / 60, a.K15, 12);                            // on the floor: easing out of the balcony
            a.Step(lessonOn: false, x: 280, y: 1.6, dt: 1.0 / 60);            // up on the balcony, past the steps
            Assert.True(a.K13 > 0.9 / 60 && a.K15 > 1 - 0.9 / 60);
            a.Reset();
            Assert.Equal(0, a.K13);
            Assert.Equal(1, a.K15);
        }

        [Fact]
        public void Fallback_LogsAndGivesTheProloguesTrack()
        {
            string said = null;
            FramingTrack t = ChapterFraming.Fallback("no_such_chapter", m => said = m);
            Assert.Equal("dl01.alcove", t.Base.Name);
            Assert.Contains("'no_such_chapter' has no framing yet", said);
            Assert.NotNull(ChapterFraming.Fallback("x", null));
        }

        /// <summary>
        /// GameHost's <c>startAt</c> (issue #50: the editor reaches each chapter 1 checkpoint): every one begins in its
        /// scene, steps, and frames on chapter 1's track as GameHost places the rig.
        /// </summary>
        [Fact]
        public void EveryChapter1Checkpoint_Begins_Steps_AndFrames()
        {
            foreach (CheckpointDef cp in ChapterDefs.AttendanceCheckpoints.All)
            {
                var sim = new ChapterSim(ChapterDefs.Attendance());
                Assert.True(sim.CanContinueAt(cp.Name), cp.Name);
                sim.Begin(cp.Name);
                Assert.Equal(cp.Scene, sim.Current.Id);
                var presenter = new ChapterPresenter(sim);
                var signals = new FramingSignalTable();
                var rig = new CameraRig(C, ChapterFraming.For(ChapterDefs.AttendanceId));
                presenter.UpdateSignals(signals);
                rig.SnapToFrame(presenter.CameraInput(0, signals));
                CameraPose p = default;
                for (int i = 0; i < 360; i++)
                {
                    sim.Step(default);
                    presenter.UpdateSignals(signals);
                    p = rig.Step(presenter.CameraInput(0, signals), ChapterSim.StepSeconds);
                    Assert.True(double.IsFinite(p.Position.X) && p.Position.Z > 4 && p.Position.Z < 14, cp.Name + " " + p.Position);
                }
                // Settled on him. (At dismissed it starts on the balcony, 11 m back: resetAtt leaves k15 at 1, `?? 1`, as the prototype.)
                Assert.True(Math.Abs(p.Position.X - sim.X) < 8, cp.Name + " " + p.Position + " for x " + sim.X);
            }
        }

        [Fact]
        public void ThePresenter_PublishesChapter1Signals_OnlyForChapter1()
        {
            var att = new ChapterPresenter(new ChapterSim(ChapterDefs.Attendance()));
            att.Sim.Begin("school");
            var s = new FramingSignalTable();
            att.UpdateSignals(s);
            Assert.Equal(0, s.Get(AttendanceFraming.Lesson));
            Assert.Equal(1, s.Get(AttendanceFraming.Balcony));
            Assert.Equal(0.3, s.Get(AttendanceFraming.Gallery));
            att.UpdateSignals(s);                                             // a second call in the same step eases nothing
            Assert.Equal(0, s.Get(AttendanceFraming.Lesson));

            var pro = new ChapterPresenter(new ChapterSim(ChapterDefs.Prologue()));
            pro.Sim.Begin("start");
            var p = new FramingSignalTable();
            pro.UpdateSignals(p);
            Assert.Equal(0, p.Get(AttendanceFraming.Balcony));
            Assert.Equal(0, p.Get(AttendanceFraming.Gallery));
        }
    }
}
