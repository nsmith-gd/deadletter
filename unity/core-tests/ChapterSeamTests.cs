using System;
using System.Collections.Generic;
using DeadLetter.Core.Camera;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl17;
using DeadLetter.Core.Scenes.Dl18;
using DeadLetter.Core.Streaming;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Chapter seams (#51): the seam table, the DL-17 → <c>ring_a</c> handover through <see cref="GameSession"/>, and a Continue
    /// on either side. The run is chapter 1's own trace (<see cref="AttendanceChapterTraceTests"/>) from <c>school</c> to the
    /// step he leaves DL-17, then the stair walk with no input, the handover, and chapter 2 with the stick held right. The
    /// lane camera follows the run as <c>GameHost</c> drives it (each chapter's track, <see cref="CameraRig.UseTrack"/> at the
    /// handover); chapter 2's framing across the seam is checked in <c>SomeoneHomeFramingTests</c> (#53).
    /// </summary>
    public class ChapterSeamTests
    {
        private static readonly MotorInput Right = new MotorInput { Move = 1 };
        /// <summary>Chapter 2's first steps checked after the handover.</summary>
        private const int After = 120;

        internal struct Row
        {
            public string Chapter;
            public double X, Y, Vx, MotorVx;
            public bool Grounded, Acting;
        }

        internal sealed class SeamRun
        {
            public readonly List<Row> Rows = new List<Row>();
            /// <summary>The rig's pose (world coordinates) after each row's step, and the frame target the rig eased toward.</summary>
            public readonly List<CameraPose> Poses = new List<CameraPose>();
            public readonly List<Frame> Frames = new List<Frame>();
            public CameraRig Rig;
            /// <summary>The rig's pose right after <see cref="CameraRig.UseTrack"/> at the handover, before the next step.</summary>
            public CameraPose PoseAtUseTrack;
            /// <summary>Index in <see cref="Rows"/> of: the trace's last step (he leaves DL-17); chapter 2's first row (the handover).</summary>
            public int ExitRow, HandoverRow;
            public int ClimbSteps;
            public byte[] SlotAtExit, SlotAtEntry;
            public ChapterSim A, B;
            public ChapterSeam Seam;
            public double AVxAtHandover, BVxAtHandover, BXAtHandover;
            public bool AGroundedAtHandover, BGroundedAtHandover;
            public int BRegion;
            public string BScene, BCheckpoint;
            public List<string> AFlags, BFlags, ASeen, BSeen;
            public double APlayTime, BPlayTime, AClock, BClock;
        }

        private static readonly object Gate = new object();
        private static SeamRun _run;

        internal static SeamRun Run()
        {
            lock (Gate)
            {
                if (_run != null) return _run;
                var t = Trace.Load(AttendanceChapterTraceTests.TraceFile);
                var (from, to) = AttendanceChapterTraceTests.Window(t, ChapterTraceProbes.Attendance());
                var store = new MemorySaveStore();
                var session = new GameSession(ChapterDefs.Attendance(), store);
                var a = session.Sim;
                a.Clock = from > 0 ? t.Steps[from - 1].Clk : 0;
                a.Begin("school");
                var r = new SeamRun { A = a };
                var signals = new FramingSignalTable();
                var presenter = new ChapterPresenter(a);
                var rig = r.Rig = new CameraRig(CameraConfig.Prototype, ChapterFraming.For(a.Def.Id));
                presenter.UpdateSignals(signals);
                rig.SnapToFrame(presenter.CameraInput(0, signals));
                void Shoot()
                {
                    presenter.UpdateSignals(signals);
                    CameraRigInput i = presenter.CameraInput(0, signals);
                    r.Frames.Add(rig.FrameFor(i));
                    r.Poses.Add(rig.Step(i, ChapterSim.StepSeconds));
                }
                for (int k = from; k <= to; k++)
                {
                    a.Step(t.Steps[k].Input);
                    r.Rows.Add(RowOf(a));
                    Shoot();
                    Assert.Null(session.Seam);
                }
                Assert.True(a.Exited);
                r.ExitRow = r.Rows.Count - 1;
                r.SlotAtExit = (byte[])store.Slots[0].Clone();

                for (int i = 0; i < 60 * 30 && session.Seam == null; i++) { a.Step(Right); r.Rows.Add(RowOf(a)); Shoot(); r.ClimbSteps++; }
                r.Seam = session.Seam;
                Assert.NotNull(r.Seam);
                r.AVxAtHandover = a.Motor.Vx;
                r.AGroundedAtHandover = a.Motor.Grounded;
                r.AFlags = a.Checkpoints.Flags.SetNames(); r.ASeen = a.Checkpoints.Seen.SetNames();
                r.APlayTime = a.Checkpoints.PlayTime; r.AClock = a.Clock;

                Assert.True(session.TryHandOver(out var left));
                Assert.Same(a, left);
                var b = r.B = session.Sim;
                r.BVxAtHandover = b.Vx;
                r.BXAtHandover = b.X;
                r.BGroundedAtHandover = b.Grounded;
                r.BRegion = b.Region; r.BScene = b.Current?.Id; r.BCheckpoint = b.Checkpoints.Current.Name;
                r.BFlags = b.Checkpoints.Flags.SetNames(); r.BSeen = b.Checkpoints.Seen.SetNames();
                r.BPlayTime = b.Checkpoints.PlayTime; r.BClock = b.Clock;
                r.SlotAtEntry = (byte[])store.Slots[0].Clone();
                r.HandoverRow = r.Rows.Count;
                ChapterSeams.Origin(b.Def.Id, out double ox, out double oy);                               // GameHost.HandOver
                presenter = new ChapterPresenter(b);
                rig.UseTrack(ChapterFraming.For(b.Def.Id), new Vec3(ox, oy, 0));
                r.PoseAtUseTrack = rig.Pose;
                for (int i = 0; i < After; i++) { b.Step(Right); r.Rows.Add(RowOf(b)); Shoot(); }
                return _run = r;
            }
        }

        private static Row RowOf(ChapterSim s) => new Row
        {
            Chapter = s.Def.Id, X = s.X, Y = s.Y, Vx = s.Vx, MotorVx = s.Motor.Vx, Grounded = s.Grounded, Acting = s.Act != null,
        };

        // ---- The table ----------------------------------------------------------------------------------------------------

        [Fact]
        public void TheFirstRow_IsAttendanceWorkshop_ToSomeoneHomeRingA_AndItsNamesAreTheChaptersOwn()
        {
            var seam = Assert.Single(ChapterSeams.All);
            Assert.Equal((ChapterDefs.AttendanceId, "workshop", ChapterDefs.SomeoneHomeId, "ring_a"), (seam.From, seam.Exit, seam.To, seam.Entry));
            Assert.Same(seam, ChapterSeams.Next(ChapterDefs.AttendanceId, "workshop"));
            Assert.Null(ChapterSeams.Next(ChapterDefs.AttendanceId, "kitchen"));
            Assert.Null(ChapterSeams.Next(ChapterDefs.SomeoneHomeId, "ring_a"));

            var att = ChapterDefs.Attendance();
            var home = ChapterDefs.SomeoneHome();
            var attAll = att.Checkpoints.All;
            Assert.Equal("workshop", attAll[attAll.Count - 1].Name);                                 // chapter 1's last checkpoint
            Assert.Equal(Dl17Scene.Id, att.Checkpoints.SceneOf("workshop"));
            Assert.Equal("ring_a", home.Checkpoints.All[0].Name);                                    // chapter 2's first
            Assert.Equal(Dl18Scene.Id, home.Checkpoints.SceneOf("ring_a"));
            Assert.True(new ChapterSim(home).CanContinueAt("ring_a"));
            int exit = Array.IndexOf(Checkpoint.GameOrder, "workshop"), entry = Array.IndexOf(Checkpoint.GameOrder, "ring_a");
            Assert.Equal(exit + 1, entry);                                                           // next to each other in the game's order
        }

        /// <summary>
        /// Where DL-17 ends and DL-18 begins in lane x: DL-17's end (341.22, L5792) is the foot of the stair, which neither
        /// lane has; the stair head, where DL-18's lane begins, is the seam's exit x. Ring A's datum is the stair's top.
        /// </summary>
        [Fact]
        public void TheExit_IsTheStairHead_WhereDl18sLaneBegins_AndChapter2sDatumIsTheStairsTop()
        {
            var seam = ChapterSeams.Next(ChapterDefs.AttendanceId, "workshop");
            Assert.Equal(Dl18Lane.StairHeadX + Dl18Lane.Half, seam.ExitX, 12);
            Assert.Equal(Dl18Lane.Table().Left, seam.ExitX, 12);
            Assert.Equal(Dl17Lane.StairHeadX, Dl18Scene.X0);
            Assert.True(Dl17Scene.EndAt < Dl12Lane.Right && Dl12Lane.Right < Dl18Scene.X0);           // the stair is between the lanes
            Assert.Equal(0, seam.OffsetX);
            Assert.Equal(-18 * 0.18, seam.OffsetY, 12);
            Assert.Equal(-Dl17Lane.StairY(Dl17Lane.StairHeadX), seam.OffsetY, 12);
            Assert.True(seam.ExitX < Dl18Scene.RingAX);                                              // he walks on into ring_a
        }

        [Fact]
        public void ThePrologueHasNoSeamYet_DL11sExitIsNotInCore()
        {
            Assert.Null(ChapterSeams.Into(ChapterDefs.AttendanceId));
            foreach (var cp in ChapterDefs.PrologueCheckpoints.All) Assert.Null(ChapterSeams.Next(ChapterDefs.PrologueId, cp.Name));
            Assert.Equal(new[] { ChapterDefs.PrologueId }, ChapterSeams.Span(ChapterDefs.PrologueId));
        }

        [Fact]
        public void SpanAndOrigin_JoinChapter1And2_Chapter2IsDrawnAtRingAsHeight()
        {
            var both = new[] { ChapterDefs.AttendanceId, ChapterDefs.SomeoneHomeId };
            Assert.Equal(both, ChapterSeams.Span(ChapterDefs.AttendanceId));
            Assert.Equal(both, ChapterSeams.Span(ChapterDefs.SomeoneHomeId));
            ChapterSeams.Origin(ChapterDefs.AttendanceId, out double ax, out double ay);
            ChapterSeams.Origin(ChapterDefs.SomeoneHomeId, out double hx, out double hy);
            Assert.Equal((0.0, 0.0), (ax, ay));
            Assert.Equal((0.0, Dl17Lane.StairTop), (hx, hy));
            foreach (var s in ChapterSeams.All) { Assert.NotNull(ChapterDefs.Create(s.From)); Assert.NotNull(ChapterDefs.Create(s.To)); }
        }

        // ---- The handover ---------------------------------------------------------------------------------------------------

        /// <summary>
        /// The seam continuity test (#51): chapter 1's last trace steps, the stair walk, the handover, chapter 2's first steps.
        /// In the world (chapter 2's y + 3.24), x and y never move more than one step's run in a step, and the handover itself
        /// moves him not at all.
        /// </summary>
        [Fact]
        public void XAndY_StayContinuous_FromChapter1sLastSteps_UpTheStair_IntoChapter2sFirstSteps()
        {
            var r = Run();
            ChapterSeams.Origin(ChapterDefs.SomeoneHomeId, out _, out double rise);
            double step = r.A.Config.Run * ChapterSim.StepSeconds + 1e-9;
            int from = Math.Max(1, r.ExitRow - 120);
            for (int k = from; k < r.Rows.Count; k++)
            {
                Row p = r.Rows[k - 1], q = r.Rows[k];
                double py = p.Y + (p.Chapter == ChapterDefs.SomeoneHomeId ? rise : 0), qy = q.Y + (q.Chapter == ChapterDefs.SomeoneHomeId ? rise : 0);
                Assert.True(Math.Abs(q.X - p.X) <= step, $"row {k}: x {p.X} → {q.X}");
                Assert.True(Math.Abs(qy - py) <= step, $"row {k}: y {py} → {qy}");
            }
            var last = r.Rows[r.HandoverRow - 1];
            Assert.Equal(ChapterDefs.AttendanceId, last.Chapter);
            Assert.Equal(r.Seam.ExitX, last.X, 9);
            Assert.Equal(Dl17Lane.StairTop, last.Y, 9);
            Assert.Equal(r.Seam.ExitX, r.BXAtHandover, 12);                                      // the handover moves him not at all
            Assert.True(r.Rows[r.Rows.Count - 1].X > Dl18Scene.RingAX);
        }

        [Fact]
        public void Vx_IsCarried_AndGroundedHolds_ThroughChapter2sFirstSteps()
        {
            var r = Run();
            Assert.Equal(r.A.Config.Walk * Dl17StairAct.SpeedOfWalk, r.AVxAtHandover, 12);       // the stair walk's speed
            Assert.Equal(r.AVxAtHandover, r.BVxAtHandover, 12);
            Assert.True(r.AGroundedAtHandover && r.BGroundedAtHandover);
            double accel = Math.Max(r.B.Config.AccelGroundRun, r.B.Config.AccelGroundWalk) * ChapterSim.StepSeconds + 1e-9;
            double vx = r.BVxAtHandover;
            for (int k = r.HandoverRow; k < r.Rows.Count; k++)
            {
                var w = r.Rows[k];
                Assert.True(w.Grounded, "chapter 2 step " + (k - r.HandoverRow));
                Assert.True(Math.Abs(w.Vx - vx) <= accel, $"chapter 2 step {k - r.HandoverRow}: vx {vx} → {w.Vx}");
                vx = w.Vx;
            }
            Assert.True(vx > r.BVxAtHandover);                                                   // the stick held right: he speeds up
        }

        [Fact]
        public void TheStairWalk_StartsTheStepAfterTheEnd_RisesToRingA_AndHandsTheMotorAWalkingD17()
        {
            var r = Run();
            var exit = r.Rows[r.ExitRow];
            Assert.False(exit.Acting);                                                           // the trace's last step is untouched
            Assert.True(r.Rows[r.ExitRow + 1].Acting);
            Assert.Equal(exit.X, r.Rows[r.ExitRow + 1].X);                                       // started that step, moves from the next
            double speed = r.A.Config.Walk * Dl17StairAct.SpeedOfWalk;
            int climb = (int)Math.Ceiling((Dl17StairAct.EndX - exit.X) / (speed * ChapterSim.StepSeconds));
            Assert.InRange(r.ClimbSteps, climb, climb + 3);
            double top = 0;
            for (int k = r.ExitRow; k < r.HandoverRow; k++) top = Math.Max(top, r.Rows[k].Y);
            Assert.Equal(Dl17Lane.StairTop, top, 9);
            Assert.Equal("Walk", r.A.Motor.Clip);
            Assert.True(r.A.Exited);
        }

        [Fact]
        public void ChapterTwo_StartsAtRingA_InDl18_WithChapter1sGame()
        {
            var r = Run();
            Assert.Equal(ChapterDefs.SomeoneHomeId, r.B.Def.Id);
            Assert.Equal("ring_a", r.BCheckpoint);
            Assert.Equal(Dl18Lane.Region, r.BRegion);
            Assert.Equal(Dl18Scene.Id, r.BScene);
            Assert.Contains(StoryFlags.Dl17DrawerRead, r.AFlags);
            Assert.Equal(r.AFlags, r.BFlags);
            Assert.Equal(r.ASeen, r.BSeen);
            Assert.Equal(r.APlayTime, r.BPlayTime);
            Assert.Equal(r.AClock, r.BClock);                                                    // the game clock runs on
            Assert.Equal(HoldKind.None, r.B.Motor.Hold);                                         // he carries nothing over
        }

        // ---- Continue at the exit and at the entry -----------------------------------------------------------------------

        private static MemorySaveStore StoreWith(byte[] slot)
        {
            var store = new MemorySaveStore();
            store.Slots[0] = (byte[])slot.Clone();
            return store;
        }

        [Fact]
        public void TheSlot_NamesTheChapter_WorkshopInAttendanceAtTheExit_RingAInSomeoneHomeAfterTheHandover()
        {
            var r = Run();
            Assert.True(SaveCodec.TryLoad(r.SlotAtExit, out var exit, out string err), err);
            Assert.Equal(("workshop", ChapterDefs.AttendanceId), (exit.Checkpoint, exit.ChapterId));
            Assert.True(SaveCodec.TryLoad(r.SlotAtEntry, out var entry, out err), err);
            Assert.Equal(("ring_a", ChapterDefs.SomeoneHomeId, ChapterDefs.SomeoneHomeId), (entry.Checkpoint, entry.ChapterId, entry.Scene));
            Assert.Contains(StoryFlags.Dl17DrawerRead, entry.Flags);
            Assert.NotNull(entry.Mechanisms);
        }

        [Fact]
        public void Continue_AtTheExit_PicksAttendance_AndPutsHimAtWorkshop()
        {
            var r = Run();
            var store = StoreWith(r.SlotAtExit);
            Assert.Equal(ChapterDefs.AttendanceId, GameSession.ContinueChapter(store));
            Assert.False(new ChapterSim(ChapterDefs.SomeoneHome(), store: StoreWith(r.SlotAtExit)).Continue());
            var sim = new ChapterSim(ChapterDefs.Attendance(), store: store);
            Assert.True(sim.Continue());
            Assert.Equal("workshop", sim.Checkpoints.Current.Name);
            Assert.Equal(Dl17Scene.Id, sim.Current.Id);
            Assert.Equal(ChapterDefs.AttendanceCheckpoints.Get("workshop").X, sim.X);
            Assert.True(sim.Checkpoints.Flags.Has(StoryFlags.Dl17DrawerRead));
        }

        [Fact]
        public void Continue_AtTheEntry_PicksSomeoneHome_AndPutsHimAtRingA_WithChapter1sFlags()
        {
            var r = Run();
            var store = StoreWith(r.SlotAtEntry);
            Assert.Equal(ChapterDefs.SomeoneHomeId, GameSession.ContinueChapter(store));
            Assert.False(new ChapterSim(ChapterDefs.Attendance(), store: StoreWith(r.SlotAtEntry)).Continue());
            var session = new GameSession(ChapterDefs.Create(GameSession.ContinueChapter(store)), store);
            Assert.True(session.Sim.Continue());
            var sim = session.Sim;
            Assert.Equal("ring_a", sim.Checkpoints.Current.Name);
            Assert.Equal(Dl18Scene.Id, sim.Current.Id);
            Assert.Equal((Dl18Scene.RingAX, 0.0, Dl18Lane.Region), (sim.X, sim.Y, sim.Region));
            Assert.True(sim.Checkpoints.RestoredSnapshot);
            Assert.True(sim.Checkpoints.Flags.Has(StoryFlags.Dl17DrawerRead));
            Assert.Null(session.Seam);
            for (int i = 0; i < 60; i++) sim.Step(Right);
            Assert.True(sim.Grounded && sim.X > Dl18Scene.RingAX);
        }

        [Fact]
        public void ContinueChapter_IsNullForAnEmptyOrOptionsOnlySlot_OrOneNoChapterCanContinue()
        {
            Assert.Null(GameSession.ContinueChapter(new MemorySaveStore()));
            Assert.Null(GameSession.ContinueChapter(null));
            var store = new MemorySaveStore();
            store.Save(0, new SaveModel { Checkpoint = "start", ChapterId = ChapterDefs.PrologueId, OptionsOnly = true });
            Assert.Null(GameSession.ContinueChapter(store));
            store.Save(0, new SaveModel { Checkpoint = "landing", ChapterId = ChapterDefs.PrologueId });   // DL-07: not ported
            Assert.Null(GameSession.ContinueChapter(store));
            store.Save(0, new SaveModel { Checkpoint = "hall", ChapterId = ChapterDefs.PrologueId });
            Assert.Equal(ChapterDefs.PrologueId, GameSession.ContinueChapter(store));
        }

        // ---- Carry on its own ---------------------------------------------------------------------------------------------

        /// <summary>He holds DL-17's tray at the seam: chapter 2 has no <c>dl17.tray</c>, so he arrives empty-handed.</summary>
        [Fact]
        public void Carry_AHeldItemTheNextChapterLacks_IsLeftBehind()
        {
            var a = new ChapterSim(ChapterDefs.Attendance());
            a.Begin("workshop");
            TakeTray(a);
            var b = new ChapterSim(ChapterDefs.SomeoneHome());
            ChapterHandover.Carry(a, b);
            Assert.Equal(HoldKind.None, b.Motor.Hold);
            Assert.Equal(a.X, b.X);
            Assert.Equal(a.Y - Dl17Lane.StairTop, b.Y, 12);
        }

        /// <summary>A next chapter that has a mechanism of the held item's ID gets it in his hands, in the state he held it in.</summary>
        [Fact]
        public void Carry_AHeldItemTheNextChapterHas_ComesWithHim()
        {
            var a = new ChapterSim(ChapterDefs.Attendance());
            a.Begin("workshop");
            var tray = TakeTray(a);
            var withTray = Dl18Scene.Def();
            var mechs = new List<MechanismDef>(withTray.Mechanisms) { new MechanismDef("dl17.tray", () => new CarriedItem("dl17.tray", Dl17Scene.TrayParams())) };
            withTray.Mechanisms = mechs.ToArray();
            var b = new ChapterSim(new ChapterDef(ChapterDefs.SomeoneHomeId, ChapterDefs.SomeoneHomeCheckpoints, withTray, Scenes.Dl19.Dl19Scene.Def()));
            ChapterHandover.Carry(a, b);
            var there = b.Graph.Get<CarriedItem>("dl17.tray");
            Assert.Equal(HoldKind.Item, b.Motor.Hold);
            Assert.Same(there, b.Motor.Carried);
            Assert.Equal(ItemState.Carried, there.State);
            Assert.Equal(tray.X, there.X);
        }

        [Fact]
        public void Carry_RefusesAChapterThatIsNotTheSeamsNext_OrACheckpointWithNoSeam()
        {
            var a = new ChapterSim(ChapterDefs.Attendance());
            a.Begin("kitchen");
            Assert.Throws<InvalidOperationException>(() => ChapterHandover.Carry(a, new ChapterSim(ChapterDefs.SomeoneHome())));
            a.Begin("workshop");
            Assert.Throws<ArgumentException>(() => ChapterHandover.Carry(a, new ChapterSim(ChapterDefs.Prologue())));
        }

        [Fact]
        public void TryHandOver_DoesNothingBeforeTheSeam()
        {
            var session = new GameSession(ChapterDefs.Attendance());
            session.Sim.Begin("workshop");
            for (int i = 0; i < 30; i++) session.Sim.Step(Right);
            Assert.Null(session.Seam);
            Assert.False(session.TryHandOver(out var from));
            Assert.Null(from);
            Assert.Equal(ChapterDefs.AttendanceId, session.Sim.Def.Id);
        }

        private static CarriedItem TakeTray(ChapterSim sim)
        {
            var tray = sim.Graph.Get<CarriedItem>("dl17.tray");
            tray.MoveTo(ItemState.Carried, sim.X, tray.BaseY);
            sim.Motor.TakeItem(tray);
            sim.Step(default);                                                                   // the move is the item's next step
            Assert.Equal(ItemState.Carried, tray.State);
            return tray;
        }
    }
}
