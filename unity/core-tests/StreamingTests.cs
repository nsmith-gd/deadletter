using System;
using System.Collections.Generic;
using System.IO;
using DeadLetter.Core.Art;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Camera;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Platform;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl01;
using DeadLetter.Core.Scenes.Dl03;
using DeadLetter.Core.Scenes.Dl04;
using DeadLetter.Core.Scenes.Dl06;
using DeadLetter.Core.Streaming;
using Xunit;
using DeathKind = DeadLetter.Core.Hazards.DeathKind;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Core/Streaming: what the Unity runtime's GameHost decides about a <see cref="ChapterSim"/> without Unity (port_architecture
    /// §7): which scene views to load and unload, how cues route to audio and camera, what the views read, and the scene paths
    /// the Editor builder and the runtime streamer share.
    /// </summary>
    public class StreamingTests
    {
        private static readonly MotorInput Right = new MotorInput { Move = 1 };

        private static SceneDef Span(string id, int region, double x0, double x1) => new SceneDef { Id = id, Region = region, X0 = x0, X1 = x1 };

        /// <summary>A, B and C on one region; C shares B's floor (as DL-07 shares DL-06's); D in the next region.</summary>
        private static StreamingPlanner Shared(double radius = 5) => new StreamingPlanner(new[]
        {
            Span("A", 1, 0, 10), Span("B", 1, 10, 20), Span("C", 1, 10, 20), Span("D", 2, 20, 30), Span("E", 2, 30, 40),
        }, radius);

        private static bool[] Resident(int n, params int[] which)
        {
            var r = new bool[n];
            foreach (int i in which) r[i] = true;
            return r;
        }

        // ---- The planner ------------------------------------------------------------------------------------------------------

        [Fact]
        public void Planner_GroupsScenesThatShareAStretch_IntoOneSlot()
        {
            var p = Shared();
            Assert.Equal(4, p.SlotCount);
            Assert.Equal(new[] { 0, 1, 1, 2, 3 }, new[] { p.SlotOf(0), p.SlotOf(1), p.SlotOf(2), p.SlotOf(3), p.SlotOf(4) });
            var prologue = new StreamingPlanner(ChapterDefs.Prologue(), StreamingRadii.Desktop);
            Assert.Equal(prologue.Count, prologue.SlotCount);                                       // DL-01 to DL-06: no shared floor yet
            Assert.Equal(3, prologue.IndexOf("DL-04"));
        }

        [Fact]
        public void Plan_LoadsHisSlot_AndTheNextOneOnlyInsideTheRadius()
        {
            var p = Shared(radius: 5);
            var load = new List<int>();
            var unload = new List<int>();
            p.Plan(1, toLeftSeam: 5, toRightSeam: 5, Resident(5), load, unload);                     // in B, 5 m from both seams
            Assert.Equal(new[] { 1, 2 }, load);                                                      // B and C (one floor), nothing else yet
            Assert.Empty(unload);
            p.Plan(1, toLeftSeam: 6, toRightSeam: 4.9, Resident(5, 1, 2), load, unload);
            Assert.Equal(new[] { 3 }, load);                                                         // D across the region seam
            p.Plan(1, toLeftSeam: 0.5, toRightSeam: 9.5, Resident(5, 1, 2, 3), load, unload);
            Assert.Equal(new[] { 0 }, load);
            Assert.Empty(unload);                                                                    // D is one slot away: kept
        }

        [Fact]
        public void Plan_UnloadsOnlyAFullSceneAway_SoTurningBackAtASeamKeepsWhatHeLeft()
        {
            var p = Shared();
            var load = new List<int>();
            var unload = new List<int>();
            // He crossed from B into D and turned back at once: B and C stay (one slot), A goes (two).
            p.Plan(3, toLeftSeam: 0.2, toRightSeam: 9.8, Resident(5, 0, 1, 2, 3), load, unload);
            Assert.Empty(load);
            Assert.Equal(new[] { 0 }, unload);
            p.Plan(4, toLeftSeam: 3, toRightSeam: 7, Resident(5, 1, 2, 3, 4), load, unload);
            Assert.Equal(new[] { 1, 2 }, unload);
            p.Plan(-1, 0, 0, Resident(5, 0, 1, 2, 3, 4), load, unload);                              // past the chapter: nothing changes
            Assert.Empty(load);
            Assert.Empty(unload);
        }

        [Fact]
        public void Placement_IsTheCheckpointsSlotAndBothNeighbours()
        {
            var p = Shared();
            var req = new List<int>();
            p.Placement(3, req);
            Assert.Equal(new[] { 1, 2, 3, 4 }, req);
            p.Placement(0, req);
            Assert.Equal(new[] { 0, 1, 2 }, req);
            Assert.True(p.SameSlot(2, 1));
            Assert.False(p.SameSlot(3, 1));
            Assert.Throws<ArgumentException>(() => p.Plan(0, 1, 1, new bool[2], new List<int>(), new List<int>()));
        }

        [Fact]
        public void Radii_AreLargerOnSwitch()
        {
            Assert.True(StreamingRadii.For(PlatformKind.Switch) > StreamingRadii.For(PlatformKind.Steam));
            Assert.Equal(StreamingRadii.Desktop, StreamingRadii.For(PlatformKind.Desktop));
        }

        /// <summary>The prologue walked from DL-01's hall: DL-02 streams in before the passage, and DL-01 goes once he is in DL-03.</summary>
        [Fact]
        public void Plan_FollowsTheSim_FromDl01IntoDl03()
        {
            var sim = new ChapterSim(ChapterDefs.Prologue());
            var p = new StreamingPlanner(sim.Def, StreamingRadii.Desktop);
            var resident = new bool[p.Count];
            var load = new List<int>();
            var unload = new List<int>();
            sim.Begin("hall");
            p.Plan(p.IndexOf(sim.Current), sim.DistanceToSeam(ExitDir.Left), sim.DistanceToSeam(ExitDir.Right), resident, load, unload);
            Assert.Equal(new[] { 0, 1 }, load);                                                      // 13.2 − 8.35 < 9 m: DL-02 too

            resident[0] = resident[1] = true;
            sim.Begin("weighroom");                                                                  // DL-03
            p.Plan(p.IndexOf(sim.Current), sim.DistanceToSeam(ExitDir.Left), sim.DistanceToSeam(ExitDir.Right), resident, load, unload);
            Assert.Equal("DL-03", sim.Current.Id);
            Assert.Contains(2, load);
            Assert.Equal(new[] { 0 }, unload);
        }

        // ---- Placement through a respawn --------------------------------------------------------------------------------------

        /// <summary>The presenter names the respawn's scene on exactly the step before the one that respawns him.</summary>
        [Fact]
        public void PendingRespawnScene_IsSetTheStepBeforeTheRespawn()
        {
            var sim = new ChapterSim(ChapterDefs.Prologue());
            var view = new ChapterPresenter(sim);
            sim.Begin("room");
            int reloads = 0;
            sim.Checkpoints.Reloaded += _ => reloads++;
            Assert.Null(view.PendingRespawnScene());
            Assert.True(sim.Die(DeathKind.Crush));
            for (int i = 0; i < 600 && view.PendingRespawnScene() == null; i++) sim.Step(default);
            Assert.Equal("DL-02", view.PendingRespawnScene()?.Id);
            Assert.Equal(0, reloads);
            sim.Step(default);
            Assert.Equal(1, reloads);
            Assert.Null(view.PendingRespawnScene());
        }

        // ---- Cues ------------------------------------------------------------------------------------------------------------

        [Fact]
        public void CueRoutes_ParseThePrefixes()
        {
            Assert.Equal(new CueRoute(CueKind.Music, "hall", MusicCues.DefaultFadeIn), CueRoutes.Parse("music:hall"));
            Assert.Equal(0.6, CueRoutes.Parse("music:racks").FadeIn);
            Assert.Equal(0.15, CueRoutes.Parse("music:dead").FadeIn);
            Assert.Equal(new CueRoute(CueKind.Moment, "kin"), CueRoutes.Parse("moment:kin"));
            Assert.Equal(new CueRoute(CueKind.Voice, "tan_scanner"), CueRoutes.Parse("voice:tan_scanner"));
            Assert.Equal("d17_worried", CueRoutes.Parse("sound:worried").Key);
            Assert.Equal(SfxKeys.SetDown(true), CueRoutes.Parse("sound:setDownHigh").Key);
            Assert.Equal(SfxKeys.SetDown(false), CueRoutes.Parse("sound:setDown").Key);
            Assert.Equal(CueKind.Shake, CueRoutes.Parse("shake").Kind);
            Assert.Equal(CueKind.Shot, CueRoutes.Parse("shot:pit").Kind);
            Assert.Equal(CueKind.Unknown, CueRoutes.Parse("hall").Kind);
            Assert.Equal(CueKind.Unknown, CueRoutes.Parse("thing:").Kind);
            Assert.Equal(CueKind.Unknown, CueRoutes.Parse("").Kind);
        }

        /// <summary>Every cue the ported scenes raise reaches something real: a catalogued track, voice, sound or moment.</summary>
        [Fact]
        public void EveryPrologueCue_RoutesToACataloguedAsset()
        {
            var cues = new[]
            {
                Dl01Rules.VoiceDispatchItem, Dl01Rules.MusicHall, Dl01Rules.MusicThreshold,
                Dl03Rules.SoundWorried, Dl03Rules.SoundSetDown, Dl03Rules.SoundSetDownHigh, Dl03Rules.SoundKnock,
                Dl04Rules.MusicRacks, Dl04Rules.MomentKin,
                ReturnToSender06.ShotScan, ReturnToSender06.ShotPit, ReturnToSender06.ShotCheck, ReturnToSender06.MusicDead,
                ReturnToSender06.VoiceTanScanner, ReturnToSender06.Shake,
            };
            var sfx = new HashSet<string>(SfxKeys.Simple.Values) { SfxKeys.SetDown(true), SfxKeys.SetDown(false) };
            var routes = new CueRoutes();
            foreach (var id in cues)
            {
                var r = routes.Resolve(id);
                Assert.Equal(r, routes.Resolve(id));
                switch (r.Kind)
                {
                    case CueKind.Music: Assert.NotNull(MusicCatalog.Find(r.Key)); break;
                    case CueKind.Voice: Assert.NotNull(VoiceCatalog.Find(r.Key)); break;
                    case CueKind.Sound: Assert.Contains(r.Key, sfx); break;
                    case CueKind.Moment: Assert.NotNull(PrologueMoments.Find(r.Key)); break;
                    case CueKind.Shot: case CueKind.Shake: break;
                    default: throw new Xunit.Sdk.XunitException(id.Name + " routes nowhere");
                }
            }
        }

        // ---- Paths -----------------------------------------------------------------------------------------------------------

        [Fact]
        public void ScenePaths_AreTheChapterFolderAndTheSceneId()
        {
            Assert.Equal("Assets/Scenes/Prologue/DL-01.unity", ChapterScenes.ScenePath(ChapterDefs.PrologueId, "DL-01"));
            Assert.Equal("Assets/Scenes/DL_Persistent.unity", ChapterScenes.BootstrapPath);
            Assert.Equal("DL-06", ChapterScenes.SceneName("DL-06"));
            Assert.NotNull(ChapterScenes.Create(ChapterDefs.PrologueId));
            Assert.NotSame(ChapterScenes.Create("prologue"), ChapterScenes.Create("prologue"));
            Assert.Null(ChapterScenes.Create("chapter9"));
            Assert.Throws<ArgumentException>(() => ChapterScenes.ScenePath("", "DL-01"));
        }

        // ---- Mechanism views ---------------------------------------------------------------------------------------------------

        /// <summary>
        /// Every <c>MECH_</c> node the export names for a mechanism of the prologue chapter (docs/unity/name_map.csv) gets
        /// bindings its Core mechanism can read: a binding table and Core's types cannot drift apart.
        /// </summary>
        [Fact]
        public void EveryBoundArtNode_ReadsAChannelItsMechanismHas()
        {
            var sim = new ChapterSim(ChapterDefs.Prologue());
            sim.Begin("start");
            int bound = 0, nodes = 0;
            var unboundTypes = new SortedSet<string>();
            foreach (string line in File.ReadAllLines(RepoFiles.Find("docs/unity/name_map.csv")))
            {
                string[] f = line.Split(',');
                if (f.Length < 3 || !f[2].StartsWith("MECH_", StringComparison.Ordinal)) continue;
                ArtName n = ArtNames.Parse(f[2]);
                if (!sim.Graph.TryGet(n.Id, out IMechanism m)) continue;                              // a scene not in the chapter yet
                nodes++;
                ViewBinding[] bindings = MechanismViewBindings.For(n.Type, n.Part);
                if (bindings.Length == 0) unboundTypes.Add(n.Type + (n.Part != null ? "__" + n.Part : ""));
                foreach (var b in bindings)
                {
                    Assert.True(MechanismReadout.Supports(m, b.Channel, b.Index), f[2] + ": " + m.GetType().Name + " has no " + b);
                    bound++;
                }
            }
            Assert.True(nodes > 30, "name_map rows for the prologue's mechanisms: " + nodes);
            Assert.True(bound > 25, "bindings: " + bound);
            // The static parts and the ones whose motion is not settled yet (listed so a change is deliberate).
            Assert.Equal(new[]
            {
                "CarrierLine", "CarrierLine__CarrierChassis", "CarrierLine__CarrierLamp", "CarrierLine__CarrierPlate", "CarrierLine__CarrierTub",
                "CarrierLine__ChainBelt0", "CarrierLine__ChainBelt1", "CarrierLine__ChainBelt2", "Cradle", "Door__Pulley", "Door__ShutterRail",
                "FollowerActuator__GateNeedle", "LoadPlate", "PointsLever__PointsBlade", "PulseSequencer", "Scanner",
            }, unboundTypes);
        }

        [Fact]
        public void Readout_ReadsTheMechanismsOwnValues()
        {
            var sim = new ChapterSim(ChapterDefs.Prologue());
            sim.Begin("start");
            var relay = sim.Graph.Get<IMechanism>("dl01.relay");
            Assert.NotNull(MechanismReadout.Reader(relay, ViewChannel.Lamp, 2, null));
            Assert.Null(MechanismReadout.Reader(relay, ViewChannel.Lamp, 3, null));
            Assert.Null(MechanismReadout.Reader(relay, ViewChannel.X, 0, null));
            var shutter = sim.Graph.Get<IPositionSource>("dl01.shutter");
            Assert.Equal(shutter.Position, MechanismReadout.Reader((IMechanism)shutter, ViewChannel.Position, 0, null)());
            Assert.Equal(new[] { new ViewBinding(ViewChannel.Lamp, ViewMotion.Emission, 1, 1) }, MechanismViewBindings.For("PulseSequencer", "RelayLamp1"));
            Assert.Equal(-1, MechanismViewBindings.For("Door", "Counterweight")[0].Scale);
            Assert.Equal(new[] { new ViewBinding(ViewChannel.Lamp, ViewMotion.Emission, MechanismViewBindings.SeatedLampGain, 0) },
                MechanismViewBindings.For("Cradle", "SeatedLamps"));                                      // U-17b: the seated lamps, calm or not
            Assert.Empty(MechanismViewBindings.For("Cradle", "SeatedCourier"));
            var cradle = sim.Graph.Get<IMechanism>("dl04.cradle");
            Assert.True(MechanismReadout.Supports(cradle, ViewChannel.Lamp, 0));
            Assert.Equal(0, MechanismReadout.Reader(cradle, ViewChannel.Lamp, 0, () => true)());               // not seated: dark
            Assert.Empty(MechanismViewBindings.For("Nonesuch", null));
        }

        // ---- The presenter -----------------------------------------------------------------------------------------------------

        [Fact]
        public void CameraInput_FollowsTheSimsPose_AndSetsThePrologueSignals()
        {
            var sim = new ChapterSim(ChapterDefs.Prologue());
            var view = new ChapterPresenter(sim);
            var signals = new FramingSignalTable();
            sim.Begin("start");
            view.UpdateSignals(signals);
            Assert.Equal(0, signals.Get(PrologueFraming.Dl02));
            var input = view.CameraInput(16.0 / 9.0, signals);
            Assert.Equal(sim.X, input.X);
            Assert.Equal(sim.Y, input.Y);
            Assert.Same(signals, input.Signals);
            Assert.Null(input.Shot);

            sim.Begin("bay");                                                                         // region 2, DL-04
            view.UpdateSignals(signals);
            Assert.Equal(1, signals.Get(PrologueFraming.Dl02));
            Assert.Equal(0, signals.Get(PrologueFraming.Dl06Pit));
            Assert.Equal(AmbienceRules.SceneAmbience(view.Ambience()).Name, AmbienceRules.SceneAmbience(new AmbienceContext { Region = 2, X = sim.X, Revealed = true }).Name);
        }

        /// <summary>The wake's label beat (a scene quirk): D-17 shows CheckLabel, and the camera takes the label shot from f2.</summary>
        [Fact]
        public void WakeLabelBeat_ShowsCheckLabel_AndTakesTheLabelShot()
        {
            var sim = new ChapterSim(ChapterDefs.Prologue());
            var view = new ChapterPresenter(sim);
            sim.Begin("start", fromOpening: true);
            Assert.Null(view.ActClip(out _));
            sim.Step(default);
            sim.Step(default);
            Assert.Equal(ClipNames.CheckLabel, view.ActClip(out double t));
            Assert.False(double.IsNaN(t));
            for (int i = 0; i < 10; i++) sim.Step(default);
            Assert.Equal("label", view.CameraInput(0, new FramingSignalTable()).Shot?.Name);
        }

        /// <summary>What the host reads after each step allocates nothing (as the step itself does not).</summary>
        [Fact]
        public void PresenterReads_AllocateNothing()
        {
            var sim = new ChapterSim(ChapterDefs.Prologue()) { Clock = 50 };
            var view = new ChapterPresenter(sim);
            var planner = new StreamingPlanner(sim.Def, StreamingRadii.Desktop);
            var routes = new CueRoutes();
            var signals = new FramingSignalTable();
            var resident = new bool[planner.Count];
            var load = new List<int>(8);
            var unload = new List<int>(8);
            sim.Begin("start");
            double sink = 0;
            void Frame()
            {
                sim.Step(Right);
                view.UpdateSignals(signals);
                sink += view.CameraInput(16.0 / 9.0, signals).X;
                sink += view.Ambience().X;
                if (view.ActClip(out _) != null) sink++;
                if (view.PendingRespawnScene() != null) sink++;
                for (int c = 0; c < sim.Cues.Count; c++) sink += (int)routes.Resolve(sim.Cues[c].Id).Kind;
                planner.Plan(planner.IndexOf(sim.Current), sim.DistanceToSeam(ExitDir.Left), sim.DistanceToSeam(ExitDir.Right), resident, load, unload);
            }
            for (int i = 0; i < 200; i++) Frame();                                                      // warm up
            long before = GC.GetAllocatedBytesForCurrentThread();
            for (int i = 0; i < 1000; i++) Frame();
            Assert.Equal(0, GC.GetAllocatedBytesForCurrentThread() - before);
            Assert.True(sink != 0);
        }

        [Fact]
        public void ActClip_OfADeath_IsItsDeathClip_BuiltOnce()
        {
            var sim = new ChapterSim(ChapterDefs.Prologue());
            var view = new ChapterPresenter(sim);
            sim.Begin("room");
            sim.Die(DeathKind.Crush, sinkRate: 0.8);                                                  // a death act (the sump's way)
            sim.Step(default);
            string a = view.ActClip(out _);
            Assert.Equal("DeathCrush", a);
            sim.Step(default);
            Assert.Same(a, view.ActClip(out _));
        }

        // ---- Across a seam (#51) ---------------------------------------------------------------------------------------------

        private static StreamingPlanner Seam(double radius = StreamingRadii.Desktop)
            => new StreamingPlanner(new[] { ChapterDefs.Attendance(), ChapterDefs.SomeoneHome() }, radius);

        [Fact]
        public void PlannerAcrossTheSeam_ListsBothChaptersScenes_InPlayOrder_EachWithItsChaptersPath()
        {
            var p = Seam();
            int i17 = p.IndexOf("DL-17"), i18 = p.IndexOf("DL-18"), i19 = p.IndexOf("DL-19");
            Assert.Equal(ChapterDefs.Attendance().Scenes.Count + 2, p.Count);
            Assert.Equal((i17 + 1, i17 + 2), (i18, i19));
            Assert.Equal(p.SlotOf(i17) + 1, p.SlotOf(i18));
            Assert.Equal(ChapterDefs.AttendanceId, p.ChapterOf(i17));
            Assert.Equal(ChapterDefs.SomeoneHomeId, p.ChapterOf(i18));
            Assert.Equal("Assets/Scenes/Someone_home/DL-18.unity", ChapterScenes.ScenePath(p.ChapterOf(i18), p[i18].Id));
            Assert.Equal("Assets/Scenes/Attendance/DL-17.unity", ChapterScenes.ScenePath(p.ChapterOf(i17), p[i17].Id));
            Assert.Null(Shared().ChapterOf(0));                                          // built from scenes alone
            Assert.Throws<ArgumentException>(() => new StreamingPlanner(new[] { ChapterDefs.Attendance(), ChapterDefs.Attendance() }, 9));
        }

        /// <summary>
        /// The streamer spans the seam: walking DL-17 toward its end loads DL-18 (chapter 2's) once he is within the radius of
        /// DL-17's end; after the handover, in DL-18, DL-17 stays loaded until he is in DL-19, two slots on.
        /// </summary>
        [Fact]
        public void Plan_LoadsDl18NearDl17sEnd_AndKeepsDl17AfterTheHandover_UntilDl19()
        {
            var p = Seam();
            int i16a = p.IndexOf("DL-16a"), i17 = p.IndexOf("DL-17"), i18 = p.IndexOf("DL-18"), i19 = p.IndexOf("DL-19");
            var load = new List<int>();
            var unload = new List<int>();

            var a = new ChapterSim(ChapterDefs.Attendance());
            a.Begin("workshop");                                                         // 325: 17.4 m from DL-17's end
            p.Plan(p.IndexOf(a.Current), a.DistanceToSeam(ExitDir.Left), a.DistanceToSeam(ExitDir.Right), Resident(p.Count, i16a, i17), load, unload);
            Assert.DoesNotContain(i18, load);
            for (int i = 0; i < 60 * 30 && a.DistanceToSeam(ExitDir.Right) >= p.Radius; i++) a.Step(Right);
            Assert.Equal("DL-17", a.Current.Id);
            p.Plan(p.IndexOf(a.Current), a.DistanceToSeam(ExitDir.Left), a.DistanceToSeam(ExitDir.Right), Resident(p.Count, i16a, i17), load, unload);
            Assert.Equal(new[] { i18 }, load);                                           // chapter 2's first scene, before the seam

            var b = new ChapterSim(ChapterDefs.SomeoneHome());
            b.Begin("ring_a");
            Assert.Equal(i18, p.IndexOf(b.Current));                                     // by ID: another sim's SceneDef
            p.Plan(i18, b.DistanceToSeam(ExitDir.Left), b.DistanceToSeam(ExitDir.Right), Resident(p.Count, i16a, i17, i18), load, unload);
            Assert.Empty(load);
            Assert.Equal(new[] { i16a }, unload);                                        // DL-17 stays: one slot back
            p.Plan(i19, 0, double.PositiveInfinity, Resident(p.Count, i17, i18, i19), load, unload);
            Assert.Equal(new[] { i17 }, unload);

            var required = new List<int>();
            p.Placement(i18, required);                                                  // a Continue at ring_a
            Assert.Equal(new[] { i17, i18, i19 }, required);
        }

        [Fact]
        public void ChapterScenes_KnowsEveryChapter()
        {
            Assert.Equal(new[] { ChapterDefs.PrologueId, ChapterDefs.AttendanceId, ChapterDefs.SomeoneHomeId }, ChapterScenes.Ids);
            foreach (var id in ChapterScenes.Ids) Assert.Equal(id, ChapterScenes.Create(id).Id);
        }
    }
}
