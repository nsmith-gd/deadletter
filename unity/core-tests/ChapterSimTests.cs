using System;
using System.Collections.Generic;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Lane;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl01;
using DeadLetter.Core.Scenes.Dl02;
using DeadLetter.Core.Scenes.Dl03;
using DeadLetter.Core.Scenes.Dl04;
using DeadLetter.Core.Scenes.Dl05;
using DeadLetter.Core.Scenes.Dl06;
using DeadLetter.Core.Scenes.Dl08;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Core/Scenes: <see cref="ChapterSim"/>, one world per chapter (port_architecture §7). The prologue's own scenes where
    /// the behaviour is theirs; a three-scene test chapter on a flat lane where it is the chapter's own.
    /// </summary>
    public class ChapterSimTests
    {
        private static readonly MotorInput Right = new MotorInput { Move = 1 }, Left = new MotorInput { Move = -1 };

        private static int Until(ChapterSim s, MotorInput input, Func<ChapterSim, bool> done, int max = 3000)
        {
            for (int i = 1; i <= max; i++) { s.Step(input); if (done(s)) return i; }
            throw new Xunit.Sdk.XunitException("never: x=" + s.X + " scene=" + s.Current?.Id + " act=" + SceneSim.KindOf(s));
        }

        /// <summary>Counts the step hooks it is given, then passes them to the scene's own rules.</summary>
        private sealed class Counting : SceneRules
        {
            private readonly SceneRules _inner;
            public int Before, After, Graph, Begins;
            public Counting(SceneRules inner) { _inner = inner; }
            public override bool Always => _inner.Always;
            public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening) { Begins++; _inner.OnBegin(sim, checkpoint, fromOpening); }
            public override void OnOpeningEnd(ChapterSim sim) => _inner.OnOpeningEnd(sim);
            public override void BeforeMotor(ChapterSim sim, ref MotorInput input) { Before++; _inner.BeforeMotor(sim, ref input); }
            public override void AfterMotor(ChapterSim sim, bool freeStep) { After++; _inner.AfterMotor(sim, freeStep); }
            public override void AfterGraph(ChapterSim sim) { Graph++; _inner.AfterGraph(sim); }
            public override bool HasLeft(ChapterSim sim) => _inner.HasLeft(sim);
        }

        // ---- Walking back: one world --------------------------------------------------------------------------------------
        /// <summary>
        /// From DL-03's <c>solved</c> through the held-open gate into DL-04, and back: the rules switch at each seam (DL-04's run
        /// only while he is in DL-04; DL-03's, <see cref="SceneRules.Always"/>, every step; DL-02's never), the seam fires once
        /// each way with its direction, and DL-03's mechanisms are the ones he left, as he left them. Meanwhile a scene he is
        /// not in goes on: DL-02's press keeps stamping.
        /// </summary>
        [Fact]
        public void WalkingBackFromDl04IntoDl03_TheRulesSwitch_AndTheWorldGoesOn()
        {
            var dl02 = new Counting(new Dl02Rules());
            var dl03 = new Counting(new Dl03Rules());
            var dl04 = new Counting(new Dl04Rules());
            var def = new ChapterDef("test", ChapterDefs.PrologueCheckpoints, Dl01Scene.Def(), Dl02Scene.Def().WithRules(() => dl02),
                Dl03Scene.Def().WithRules(() => dl03), Dl04Scene.Def().WithRules(() => dl04), Dl05Scene.Def(), Dl06Scene.Def());
            var s = new ChapterSim(def) { Clock = 100 };
            var changes = new List<(string, string, ExitDir)>();
            s.SceneChanged += (a, b, dir) => changes.Add((a?.Id, b?.Id, dir));
            s.Begin("solved");
            Assert.Equal(new[] { ((string)null, "DL-03", ExitDir.None) }, changes);
            changes.Clear();
            Assert.Equal(1, dl04.Begins);                                                     // every scene's rules see the world rebuilt
            var gate = s.Graph.Get<FollowerActuator>("dl03.gate");
            var trolley = s.Graph.Get<Pushable>("dl03.trolley");
            Assert.Contains(gate, s.MechanismsOf(s.Current));
            double gateY = gate.Position, trolleyX = trolley.X;
            Assert.Equal(0.72 * 1.2, gateY, 9);                                               // held open by the loaded trolley

            int b4 = dl04.Before, b3 = dl03.Before;
            int n = Until(s, Right, x => x.Current.Id == "DL-04");
            Assert.Equal(dl04.Before, b4);                                                     // not his scene yet
            Assert.Equal(b3 + n, dl03.Before);
            Assert.Equal(new[] { ("DL-03", "DL-04", ExitDir.Right) }, changes);

            var press = s.Graph.Get<PeriodicCrusher>("dl02.press");
            var faces = new HashSet<double>();
            int b2 = dl02.Before;
            for (int i = 0; i < 20; i++) s.Step(new MotorInput { Move = 1, RunModifierHeld = true });
            for (int i = 0; i < 180; i++) { s.Step(default); faces.Add(press.Face); }               // three seconds: a stamp's period
            Assert.True(s.X < Dl04Scene.RealiseX, "x " + s.X);                                 // short of the realisation
            Assert.Equal(200, dl04.Before - b4);                                               // DL-04's from the step after the seam
            Assert.Equal(b2, dl02.Before);
            Assert.True(faces.Count > 1, "the press stood still");                            // DL-02 goes on without him

            n = Until(s, Left, x => x.Current.Id == "DL-03");
            Assert.Equal(new[] { ("DL-03", "DL-04", ExitDir.Right), ("DL-04", "DL-03", ExitDir.Left) }, changes);
            int b4Back = dl04.Before;
            for (int i = 0; i < 10; i++) s.Step(default);
            Assert.Equal(b4Back, dl04.Before);                                                 // DL-04's rules stopped at the seam
            Assert.Same(gate, s.Graph.Get<FollowerActuator>("dl03.gate"));
            Assert.Equal(gateY, gate.Position, 12);                                            // the world he left, as he left it
            Assert.Equal(trolleyX, trolley.X, 12);
            Assert.Equal("solved", s.Checkpoints.Current.Name);
        }

        // ---- Respawn and continue anywhere in the chapter ------------------------------------------------------------------
        /// <summary>
        /// He walks into DL-06 under DL-05's <c>hatch</c> and the respawn puts him back in DL-05, in region 2's lane (#26's
        /// finding: a DL-06 simulation respawned him at hatch outside its lane), where he walks on. The motor runs on the
        /// chapter's one tuning throughout; DL-06's levers carry their own step-in speed (M10).
        /// </summary>
        [Fact]
        public void ARespawnAtAnotherScenesCheckpoint_LandsInThatSceneAndItsLane()
        {
            var s = new ChapterSim(ChapterDefs.Prologue()) { Clock = 100 };
            var changes = new List<(string, string, ExitDir)>();
            s.SceneChanged += (a, b, dir) => changes.Add((a?.Id, b?.Id, dir));
            s.Begin("hatch");
            Assert.Equal("DL-05", s.Current.Id);
            Until(s, Right, x => x.Current.Id == "DL-06");
            Assert.Equal(3, s.Region);
            Assert.Equal(3, s.Lane.Region);
            Assert.Equal(MotorConfig.Prototype().StepInSpeed, s.Config.StepInSpeed);           // one tuning for the chapter
            Assert.Equal(Station.LeverStepInSpeed, s.Graph.Get<PointsLever>("dl06.stopLever").Station.StepInSpeed);   // the lever's own (M10)
            Assert.Equal("hatch", s.Checkpoints.Current.Name);

            changes.Clear();
            s.Respawn();
            Assert.Equal("DL-05", s.Current.Id);
            Assert.Equal(new[] { ("DL-06", "DL-05", ExitDir.None) }, changes);
            Assert.Equal(ChapterDefs.PrologueCheckpoints.Get("hatch").X, s.X, 12);
            Assert.Equal(2, s.Region);
            Assert.Equal(2, s.Lane.Region);                                                    // region 2's lane, not DL-06's
            Assert.Equal(MotorConfig.Prototype().StepInSpeed, s.Config.StepInSpeed);           // nothing to revert
            Assert.Equal(ChapterDefs.PrologueId + " (region 2)", s.Lane.Table.Name);          // DL-02 to DL-05's tables, joined
            double x0 = s.X;
            for (int i = 0; i < 30; i++) s.Step(Left);
            Assert.True(s.X < x0 - 0.2 && s.Grounded && s.Y == 0, "x " + s.X + " y " + s.Y);   // he walks on region 2's floor
        }

        /// <summary>
        /// A continue at a checkpoint another scene owns restores the snapshot taken there, whichever scene's mechanisms it
        /// holds (#26: a scene simulation dropped a snapshot saved in another scene): here DL-02's box, moved, then saved at
        /// DL-03's <c>weighroom</c>.
        /// </summary>
        [Fact]
        public void ContinueAtACheckpointAnotherSceneOwns_RestoresItsSnapshot()
        {
            var store = new MemorySaveStore();
            var a = new ChapterSim(ChapterDefs.Prologue(), store: store);
            a.NewGame();
            a.Begin("room");
            var box = a.Graph.Get<CarriedItem>("dl02.box");
            box.MoveTo(ItemState.Floor, 20.0, 0);                                               // not where weighroom derives it
            a.Step(default);
            Assert.Equal(20.0, box.X);
            Assert.True(a.Checkpoints.Reach("weighroom"));

            var b = new ChapterSim(ChapterDefs.Prologue(), store: store);
            Assert.True(b.Continue());
            Assert.Equal("weighroom", b.Checkpoints.Current.Name);
            Assert.True(b.Checkpoints.RestoredSnapshot);
            Assert.Equal(ChapterDefs.PrologueId, b.Checkpoints.Scene);
            Assert.Equal(20.0, b.Graph.Get<CarriedItem>("dl02.box").X);
            Assert.Equal("DL-03", b.Current.Id);
            Assert.Same(b.Current, b.SceneOf("weighroom"));
            Assert.Equal(ChapterDefs.PrologueCheckpoints.Get("weighroom").X, b.X);

            var fresh = new ChapterSim(ChapterDefs.Prologue());
            fresh.Begin("weighroom");
            Assert.Equal(17.4, fresh.Graph.Get<CarriedItem>("dl02.box").X);                    // derived: the box at home
        }

        /// <summary>
        /// Continue at every checkpoint the prologue places (#31 review): each of DL-01 to DL-10's lands him in its own scene,
        /// region and lane; each of DL-11's (placed in the table, owned by a scene this chapter lacks) is refused,
        /// with nothing changed here or in the slot, where it used to return true with him exited and the lane on region 1.
        /// </summary>
        [Fact]
        public void Continue_AtEveryPlacedCheckpoint_LandsInItsScene_AndRefusesTheRowsOfScenesNotInTheChapter()
        {
            int continued = 0, refused = 0;
            foreach (var cp in ChapterDefs.PrologueCheckpoints.All)
            {
                var store = new MemorySaveStore();
                store.Save(0, new SaveModel { Checkpoint = cp.Name, Scene = ChapterDefs.PrologueId, Flags = { StoryFlags.Curio("cot") } });
                var s = new ChapterSim(ChapterDefs.Prologue(), store: store);
                bool ours = s.Def.Scene(cp.Scene) != null;
                Assert.Equal(ours, s.CanContinueAt(cp.Name));
                if (ours)
                {
                    Assert.True(s.Continue(), cp.Name);
                    Assert.Equal(cp.Scene, s.Current.Id);
                    Assert.Equal(cp.Name, s.Checkpoints.Current.Name);
                    Assert.Equal(cp.X, s.X, 12);
                    Assert.Equal(cp.Y, s.Y, 12);
                    Assert.Equal(cp.Region, s.Region);
                    Assert.Equal(cp.Region, s.Lane.Region);
                    Assert.False(s.Exited, cp.Name);
                    Assert.True(s.Checkpoints.Flags.Has(StoryFlags.Curio("cot")));                // the slot's game
                    continued++;
                    continue;
                }

                // Refused over a chapter already in play: its game, its world and the slot stay as they were.
                s.Begin("hatch");                                                               // adopts the slot's game once
                s.Checkpoints.SetFlag(StoryFlags.Curio("mug"));                                 // played on since (a flag is saved at once)
                for (int i = 0; i < 20; i++) s.Step(Right);
                store.Save(0, new SaveModel { Checkpoint = cp.Name, Scene = ChapterDefs.PrologueId });   // and the slot now at the row
                var slot = (byte[])store.Slots[0].Clone();
                int writes = store.Writes;
                double x = s.X, clock = s.Clock;
                long steps = s.Steps;
                var scene = s.Current;
                Assert.False(s.Continue(), cp.Name);
                Assert.Equal(x, s.X);
                Assert.Equal(clock, s.Clock);
                Assert.Equal(steps, s.Steps);
                Assert.Same(scene, s.Current);
                Assert.Equal("hatch", s.Checkpoints.Current.Name);
                Assert.Equal(2, s.Region);
                Assert.Equal(2, s.Lane.Region);
                Assert.True(s.Checkpoints.Flags.Has(StoryFlags.Curio("mug")), cp.Name);         // the slot's game was not loaded over it
                Assert.Equal(slot, store.Slots[0]);
                Assert.Equal(writes, store.Writes);
                Assert.Throws<ArgumentException>(() => s.Begin(cp.Name));
                Assert.Equal(slot, store.Slots[0]);
                refused++;
            }
            Assert.Equal(19, continued);                                                        // start … uponly
            Assert.Equal(3, refused);                                                           // ringc … forwarded
        }

        /// <summary>A respawn due at a checkpoint none of the chapter's scenes owns is refused before anything reloads (#31 review).</summary>
        [Fact]
        public void Respawn_AtACheckpointOfASceneNotInTheChapter_Throws_AndChangesNothing()
        {
            var s = new ChapterSim(ChapterDefs.Prologue());
            s.Begin("scanned");
            for (int i = 0; i < 10; i++) s.Step(Right);
            Assert.True(s.Checkpoints.Reach("ringc"));                                          // DL-11's: placed, not ours
            double x = s.X;
            int region = s.Region, lane = s.Lane.Region;
            var scene = s.Current;
            Assert.Throws<InvalidOperationException>(() => s.Respawn());
            Assert.Equal(x, s.X);
            Assert.Equal(region, s.Region);
            Assert.Equal(lane, s.Lane.Region);
            Assert.Same(scene, s.Current);
            Assert.Equal("ringc", s.Checkpoints.Current.Name);
        }

        /// <summary>
        /// Scene acts are typed (#31 review): their kind and phase are interned <see cref="ActId"/>s, the prototype's names,
        /// reported by the chapter alongside the motor's <see cref="ChapterSim.ActPhase"/>, and matched without a string or
        /// an allocation.
        /// </summary>
        [Fact]
        public void SceneActs_AreInternedIds_ReportedAlongsideTheMotorsActPhase()
        {
            Assert.Equal(ActId.Of("quirk"), ActIds.Quirk);
            Assert.Equal("dl06.scanner", Dl06ScanAct.Scanner.Name);
            Assert.Equal(ActId.Of("3"), ActIds.Leg(3));
            Assert.Equal(ActIds.Clip("CheckLabel"), ActId.Of("CheckLabel"));
            Assert.True(default(ActId).IsNone);
            Assert.Throws<ArgumentException>(() => ActId.Of(""));

            var s = new ChapterSim(ChapterDefs.Prologue());
            s.Begin("scanned");
            Assert.True(s.SceneActKind.IsNone && s.SceneActPhase.IsNone);
            s.StartAct(new HoldAct(Dl06ScanAct.Scanner, Dl06ScanAct.Check, 1.0));
            s.Step(default);
            Assert.Equal(Dl06ScanAct.Scanner, s.SceneActKind);
            Assert.Equal(Dl06ScanAct.Check, s.SceneActPhase);
            Assert.Equal(ActPhase.None, s.ActPhase);                                           // the motor's: none while a scene act holds him
            long before = GC.GetAllocatedBytesForCurrentThread();
            int matched = 0;
            for (int i = 0; i < 1000; i++) if (s.SceneActKind == Dl06ScanAct.Scanner && s.SceneActPhase == Dl06ScanAct.Check) matched++;
            Assert.Equal(before, GC.GetAllocatedBytesForCurrentThread());
            Assert.Equal(1000, matched);
            for (int i = 0; i < 70 && !s.SceneActKind.IsNone; i++) s.Step(default);
            Assert.True(s.SceneActKind.IsNone && s.SceneActPhase.IsNone);
        }

        /// <summary>The save semantics of #26 (a): NewGame is the only reset, Continue loads, Begin keeps the game it holds and writes nothing.</summary>
        [Fact]
        public void TheSave_NewGameResets_BeginKeeps_ContinueLoads_OneServiceForTheChapter()
        {
            var store = new MemorySaveStore();
            var a = new ChapterSim(ChapterDefs.Prologue(), store: store);
            a.NewGame();
            a.Checkpoints.ApplySettings(new Settings { Calm = true });
            a.Checkpoints.SetFlag(StoryFlags.Curio("cot"));
            Assert.True(a.Checkpoints.Reach("room"));
            int writes = store.Writes;

            var b = new ChapterSim(ChapterDefs.Prologue(), store: store);
            b.Begin("scanned");                                                                 // over the slot: its game, nothing written
            Assert.Equal(writes, store.Writes);
            Assert.True(b.Checkpoints.Settings.Calm);
            Assert.True(b.Checkpoints.Flags.Has(StoryFlags.Curio("cot")));
            Assert.Equal("DL-06", b.Current.Id);
            b.Begin("start");                                                                   // and on: the same game
            Assert.True(b.Checkpoints.Settings.Calm);
            Assert.Equal(writes, store.Writes);

            Assert.True(new ChapterSim(ChapterDefs.Prologue(), store: store).Continue());
            b.NewGame();
            Assert.True(store.TryLoad(0, out var m));
            Assert.Equal("start", m.Checkpoint);
            Assert.Empty(m.Flags);
            Assert.Throws<ArgumentException>(() => b.Begin("ringc"));                          // DL-11's: not in this chapter
            Assert.Throws<ArgumentException>(() => b.Begin("school"));                         // chapter 1's
        }

        // ---- Seams: SceneChanged, Next, DistanceToSeam ------------------------------------------------------------------------
        [Fact]
        public void SceneChanged_FiresOncePerCrossing_WithTheDirection_AndAtARegionSeam()
        {
            var (s, rules) = TestChapter();
            var changes = new List<(string, string, ExitDir)>();
            s.SceneChanged += (a, b, dir) => changes.Add((a?.Id, b?.Id, dir));
            s.Begin("a");
            Assert.Equal(new[] { ((string)null, "A", ExitDir.None) }, changes);
            changes.Clear();

            Until(s, Right, x => x.X >= 10);
            Assert.Equal(new[] { ("A", "B", ExitDir.Right) }, changes);
            for (int i = 0; i < 30; i++) s.Step(Right);
            Assert.Single(changes);                                                             // once, not every step past it
            Until(s, Left, x => x.X < 10);
            Until(s, Right, x => x.X >= 10);
            Assert.Equal(new[] { ("A", "B", ExitDir.Right), ("B", "A", ExitDir.Left), ("A", "B", ExitDir.Right) }, changes);

            rules["B"].SwitchRegionPast = 14;                                                   // B's rule takes him into region 2: C
            Until(s, Right, x => x.Region == 2);
            Assert.Equal(("B", "C", ExitDir.Right), changes[changes.Count - 1]);
            Assert.Equal(4, changes.Count);
            Until(s, Right, x => x.Exited);                                                     // past C, the chapter's last scene
            Assert.Equal(("C", (string)null, ExitDir.Right), changes[changes.Count - 1]);
            Assert.Null(s.Current);
            double x0 = s.X;
            s.Step(Right);
            Assert.Equal(x0, s.X);                                                              // the motor stops past the chapter
        }

        [Fact]
        public void TheStepHooks_RunForTheSceneThatHoldsHim_PlusTheAlwaysRules()
        {
            var (s, rules) = TestChapter();
            s.Begin("a");
            s.Step(default);
            Assert.Equal((1, 0), (rules["A"].Before, rules["B"].Before));
            Assert.Equal(1, rules["C"].Before);                                                 // C's are Always
            Until(s, Right, x => x.X >= 10);
            int a = rules["A"].Before, b = rules["B"].Before;
            s.Step(Right);
            Assert.Equal((a, b + 1), (rules["A"].Before, rules["B"].Before));
            Assert.Equal(3, rules["A"].Begins + rules["B"].Begins + rules["C"].Begins);         // OnBegin: every scene's
        }

        [Fact]
        public void NextAndDistanceToSeam_LookAheadForStreaming()
        {
            var s = new ChapterSim(ChapterDefs.Prologue());
            s.Begin("start");
            Assert.Null(s.Next(ExitDir.Left));
            Assert.Equal("DL-02", s.Next(ExitDir.Right).Id);
            Assert.Equal(Dl01Scene.EmergeX - 1.0, s.DistanceToSeam(ExitDir.Right), 12);         // where the passage comes out
            Assert.Equal(1.0 - Dl01Lane.Left, s.DistanceToSeam(ExitDir.Left), 12);
            s.Begin("room");
            Assert.Equal("DL-01", s.Next(ExitDir.Left).Id);
            Assert.Equal("DL-03", s.Next(ExitDir.Right).Id);
            Assert.Equal(Dl02Lane.X1 - 13.2, s.DistanceToSeam(ExitDir.Right), 12);
            s.Begin("solved");
            Assert.Equal(Dl03Scene.GateX - 29.95, s.DistanceToSeam(ExitDir.Right), 12);
            Assert.Equal(29.95 - Dl03Scene.X0, s.DistanceToSeam(ExitDir.Left), 12);
            s.Begin("scanned");
            Assert.Equal("DL-07", s.Next(ExitDir.Right).Id);                                    // on DL-06's floor: in view already
            Assert.Equal(0, s.DistanceToSeam(ExitDir.Right));
            s.Begin("gallery");
            Assert.Equal("DL-06", s.Next(ExitDir.Left).Id);
            Assert.Equal("DL-08", s.Next(ExitDir.Right).Id);                                    // through the doorway: region 4
            Assert.Equal(Dl06Scene.X1 - (33 + 42.3), s.DistanceToSeam(ExitDir.Right), 12);
            s.Begin("latched");
            Assert.Equal("DL-07", s.Next(ExitDir.Left).Id);
            Assert.Equal("DL-09", s.Next(ExitDir.Right).Id);                                    // off the end of the belt
            Assert.Equal(Dl08Scene.X1 - (33 + 56.2), s.DistanceToSeam(ExitDir.Right), 12);     // the end of the belt
            s.Begin("tunnel");
            Assert.Equal("DL-08", s.Next(ExitDir.Left).Id);
            Assert.Equal("DL-10", s.Next(ExitDir.Right).Id);                                    // the lobby
            Assert.Equal(Dl09Lane.X1 - (42 + 65.7), s.DistanceToSeam(ExitDir.Right), 12);      // UPONLY.x0
            s.Begin("uponly");
            Assert.Equal("DL-09", s.Next(ExitDir.Left).Id);
            Assert.Null(s.Next(ExitDir.Right));                                                 // DL-11 is not ported yet
            Assert.Equal(Dl10Lane.X1 - (42 + 76.8 + 0.6), s.DistanceToSeam(ExitDir.Right), 12); // REGION5_X: down the shaft
            Assert.Equal(double.PositiveInfinity, new ChapterSim(ChapterDefs.Prologue()).DistanceToSeam(ExitDir.Right));   // not placed

            var (t, _) = TestChapter(sharedLast: true);                                          // a scene on the same stretch: in view already
            t.Begin("a");
            Until(t, Right, x => x.X >= 10);
            Assert.Equal("B2", t.Next(ExitDir.Right).Id);
            Assert.Equal(0, t.DistanceToSeam(ExitDir.Right));
        }

        [Fact]
        public void SceneOf_AndMechanismsOf_AreTheChaptersView()
        {
            var s = new ChapterSim(ChapterDefs.Prologue());
            Assert.Equal("DL-05", s.SceneOf("hatch").Id);
            Assert.Equal("DL-04", s.SceneOf("bay").Id);
            Assert.Equal("DL-07", s.SceneOf("landing").Id);
            Assert.Equal("DL-08", s.SceneOf("goods").Id);
            Assert.Equal("DL-09", s.SceneOf("cage").Id);
            Assert.Equal("DL-10", s.SceneOf("uponly").Id);
            Assert.Null(s.SceneOf("ringc"));                                                    // DL-11's
            var dl04 = s.SceneOf("bay");
            Assert.Equal(new[] { "dl04.courier", "dl04.bayPlate", "dl04.cradle", "dl04.bayDoor" },
                Array.ConvertAll(ToArray(s.MechanismsOf(dl04)), m => m.Id.Value));
            int total = 0;
            foreach (var scene in s.Def.Scenes) total += s.MechanismsOf(scene).Count;
            Assert.Equal(s.Graph.Count, total);                                                 // every scene's, in one graph
            Assert.Throws<ArgumentException>(() => s.MechanismsOf(Dl04Scene.Def()));            // not this chapter's instance
        }

        // ---- Cues and allocation ---------------------------------------------------------------------------------------------
        [Fact]
        public void Cues_AreTyped_InternedIds_WithAnIntArgument()
        {
            var s = new ChapterSim(ChapterDefs.Prologue());
            s.Begin("start", fromOpening: true);
            s.Step(default);
            Assert.Equal(new[] { new Cue(Dl01Rules.VoiceDispatchItem) }, s.Cues);
            Assert.Equal(Dl01Rules.VoiceDispatchItem, CueId.Of("voice:dispatch_item"));       // interned: one id per name
            Assert.Equal("voice:dispatch_item", s.Cues[0].ToString());
            Assert.NotEqual(Dl04Rules.MusicRacks, Dl04Rules.MomentKin);
            Assert.Equal("shake:25", new Cue(ReturnToSender06.Shake, 25).ToString());
            Assert.True(CueId.None.IsNone);
            s.Step(default);
            Assert.Empty(s.Cues);                                                               // cleared each step
        }

        /// <summary>
        /// A step allocates nothing: 1000 free steps walking into DL-01's locked shutter, and a walk across the DL-04 → DL-05
        /// seam (the commit, <see cref="ChapterSim.SceneChanged"/> with no listener, the next scene's rules).
        /// </summary>
        [Fact]
        public void Step_AllocatesNothing_OverAThousandFreeSteps_OrAcrossASeam()
        {
            var s = new ChapterSim(ChapterDefs.Prologue()) { Clock = 50 };
            s.Begin("start");
            for (int i = 0; i < 200; i++) s.Step(Right);                                         // warm up (JIT, list capacities)
            var walk = new MotorInput { Move = 1 };
            long before = GC.GetAllocatedBytesForCurrentThread();
            for (int i = 0; i < 1000; i++) s.Step(walk);
            long bytes = GC.GetAllocatedBytesForCurrentThread() - before;
            Assert.Equal(0, bytes);
            Assert.True(s.X > 2.5 && !s.Busy, "x " + s.X);

            s.Checkpoints.MarkSeen(Dl04Rules.SeenRealise);                                      // the kin moment has played: he walks on
            s.Begin("bay");
            var stroll = new MotorInput { Move = 1, RunModifierHeld = true };                    // walking pace: short of DL-05's label at 51.9
            for (int i = 0; i < 5; i++) s.Step(stroll);
            before = GC.GetAllocatedBytesForCurrentThread();
            for (int i = 0; i < 80; i++) s.Step(stroll);                                       // short of ration (48.5), whose snapshot allocates
            bytes = GC.GetAllocatedBytesForCurrentThread() - before;
            Assert.Equal("DL-05", s.Current.Id);
            Assert.Equal(0, bytes);
        }

        // ---- Definitions ---------------------------------------------------------------------------------------------------
        [Fact]
        public void ChapterDef_TakesScenesInLaneOrder_ContiguousWithinARegion()
        {
            var cps = ChapterDefs.PrologueCheckpoints;
            Assert.Throws<ArgumentException>(() => new ChapterDef("x", cps, Dl03Scene.Def(), Dl02Scene.Def()));            // backwards
            Assert.Throws<ArgumentException>(() => new ChapterDef("x", cps, Dl02Scene.Def(), Dl04Scene.Def()));            // a gap
            Assert.Throws<ArgumentException>(() => new ChapterDef("x", cps, Dl02Scene.Def(), Dl02Scene.Def()));            // twice
            Assert.Throws<ArgumentException>(() => new ChapterDef("x", cps, Dl06Scene.Def(), Dl05Scene.Def()));            // regions go back
            var prologue = ChapterDefs.Prologue();
            Assert.Equal(new[] { "DL-01", "DL-02", "DL-03", "DL-04", "DL-05", "DL-06", "DL-07", "DL-08", "DL-09", "DL-10" }, Array.ConvertAll(ToArray(prologue.Scenes), d => d.Id));
            Assert.NotNull(new ChapterDef("x", cps, Dl01Scene.Def(), Dl02Scene.Def()));                                    // a region seam: DL-01 → DL-02
        }

        /// <summary>
        /// Region 2's lane is DL-02's to DL-05's tables joined: on each scene's stretch every probe answers as that scene's
        /// table alone does (the static lane only), and the walls are the region's outermost.
        /// </summary>
        [Fact]
        public void TheJoinedLane_AnswersAsEachScenesOwnTable_OnItsStretch()
        {
            var tables = new[] { Dl02Lane.Table(), Dl03Lane.Table(), Dl04Lane.Table(), Dl05Lane.Table() };
            var seams = new[] { Dl02Lane.X1, Dl03Scene.GateX, Dl05Lane.HallX0 };
            var joined = new LaneGeometry().AddRegion(2, LaneTable.Join("region 2", tables, seams));
            for (int i = 0; i < tables.Length; i++)
            {
                var own = new LaneGeometry().AddRegion(2, tables[i]);
                double lo = i == 0 ? 12.0 : seams[i - 1], hi = i == tables.Length - 1 ? 62.0 : seams[i];
                for (double x = lo; x < hi; x += 0.005)
                {
                    Assert.Equal(own.FloorAt(x), joined.FloorAt(x));
                    Assert.Equal(own.SurfaceAt(x), joined.SurfaceAt(x));
                    Assert.Equal(own.CeilingAt(x), joined.CeilingAt(x));
                    Assert.Equal(own.IsRamp(x), joined.IsRamp(x));
                }
                foreach (double x in new[] { lo, hi - 1e-9 })                                     // the seams themselves
                {
                    Assert.Equal(own.SurfaceAt(x), joined.SurfaceAt(x));
                    Assert.Equal(own.CeilingAt(x), joined.CeilingAt(x));
                }
            }
            joined.Limits(20, 0, out double left, out double right);
            Assert.Equal((Dl02Lane.Left, Dl03Lane.Right), (left, right));                       // DL-02's gate wall is the gate's contributor
            Assert.Throws<ArgumentException>(() => LaneTable.Join("x", tables, new[] { 25.0 }));
        }

        // ---- The test chapter ------------------------------------------------------------------------------------------------
        private sealed class Spy : SceneRules
        {
            public int Before, Begins;
            public bool AlwaysOn;
            public double SwitchRegionPast = double.PositiveInfinity;
            public override bool Always => AlwaysOn;
            public override void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening) => Begins++;
            public override void BeforeMotor(ChapterSim sim, ref MotorInput input) => Before++;
            public override void AfterMotor(ChapterSim sim, bool freeStep) { if (freeStep && sim.X > SwitchRegionPast) sim.SetRegion(2); }
        }

        private static SceneDef Flat(string id, int region, double x0, double x1, Spy rules) => new SceneDef
        {
            Id = id, Region = region, X0 = x0, X1 = x1,
            Lane = () => new LaneTable { Name = id, Left = -5, Right = 100, Floor = 0 },
            Rules = () => rules,
        };

        /// <summary>A (region 1, 0–10), B (region 1, 10–20), C (region 2, 12–40; its rules Always); or B2 sharing B's stretch.</summary>
        private static (ChapterSim, Dictionary<string, Spy>) TestChapter(bool sharedLast = false)
        {
            var rules = new Dictionary<string, Spy> { ["A"] = new Spy(), ["B"] = new Spy(), ["C"] = new Spy { AlwaysOn = true }, ["B2"] = new Spy() };
            var cps = new CheckpointTable(new[] { "a", "b", "c" },
                new CheckpointDef("a", 1, region: 1, scene: "A"), new CheckpointDef("b", 11, region: 1, scene: "B"), new CheckpointDef("c", 15, region: 2, scene: "C"));
            var def = sharedLast
                ? new ChapterDef("t", cps, Flat("A", 1, 0, 10, rules["A"]), Flat("B", 1, 10, 20, rules["B"]), Flat("B2", 1, 10, 20, rules["B2"]))
                : new ChapterDef("t", cps, Flat("A", 1, 0, 10, rules["A"]), Flat("B", 1, 10, 20, rules["B"]), Flat("C", 2, 12, 40, rules["C"]));
            return (new ChapterSim(def), rules);
        }

        private static T[] ToArray<T>(IReadOnlyList<T> list)
        {
            var a = new T[list.Count];
            for (int i = 0; i < a.Length; i++) a[i] = list[i];
            return a;
        }
    }
}
