using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Folding;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl18;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-18 Room for One in chapter 2's <see cref="ChapterSim"/> (<see cref="ChapterDefs.SomeoneHome"/>), driven by scripted
    /// input. No prototype and no trace: the scene doc's acceptance checks (docs/scenes/DL-18_room_for_one.md §10) are the
    /// tests, with the layout of §3 and the grey-box of §11. The leaves on their own are <see cref="Dl18SceneTests"/>.
    /// </summary>
    public class Dl18ChapterTests
    {
        private const double Dt = ChapterSim.StepSeconds;
        private static readonly MotorInput Right = new MotorInput { Move = 1 }, Left = new MotorInput { Move = -1 };
        private static readonly MotorInput Use = new MotorInput { UsePressed = true };
        private static readonly MotorInput JumpRight = new MotorInput { Move = 1, JumpPressed = true };

        private static ChapterSim Begin(string cp = "ring_a", ISaveStore store = null)
        {
            var s = new ChapterSim(ChapterDefs.SomeoneHome(), store: store);
            s.Begin(cp);
            return s;
        }

        private static FoldingLeaf Bed(ChapterSim s) => s.Graph.Get<FoldingLeaf>(Dl18Scene.Bed);
        private static FoldingLeaf Bench(ChapterSim s) => s.Graph.Get<FoldingLeaf>(Dl18Scene.Bench);

        private static string Where(ChapterSim s)
            => "t=" + (s.Steps * Dt).ToString("F2") + " x=" + s.X.ToString("F3") + " y=" + s.Y.ToString("F3") + " act=" + SceneSim.KindOf(s)
               + " bed=" + Bed(s).State + " bench=" + Bench(s).State + " cp=" + s.Checkpoints.Current.Name;

        /// <summary>Steps with <paramref name="input"/> until <paramref name="done"/>; returns the steps taken.</summary>
        private static int Until(ChapterSim s, MotorInput input, Func<ChapterSim, bool> done, int max = 1200, Action<ChapterSim> each = null)
        {
            for (int i = 1; i <= max; i++)
            {
                s.Step(input);
                each?.Invoke(s);
                if (done(s)) return i;
            }
            throw new Xunit.Sdk.XunitException("never: " + Where(s));
        }

        private static bool Settled(FoldingLeaf l)
            => l.State == FoldingLeafState.Down || l.State == FoldingLeafState.Folded || l.State == FoldingLeafState.Propped;

        private static bool Free(ChapterSim s) => !s.Busy && !s.Motor.IsMantling && s.Grounded;

        /// <summary>A mantle (Jump into a face ahead) and its end, standing on <paramref name="y"/>.</summary>
        private static void Climb(ChapterSim s, double y, Action<ChapterSim> each)
        {
            s.Step(JumpRight);
            each?.Invoke(s);
            Assert.True(s.Motor.IsMantling, "no mantle: " + Where(s));
            Until(s, default, x => Free(x) && Math.Abs(x.Y - y) < 1e-9, each: each);
        }

        /// <summary>
        /// The solution (§2 "Fold", "Up and out"; §4): from <c>ring_a</c> along the gallery, onto the bed and off its foot,
        /// Use the foot rail (the bed folds up), back to the strap, Use it (the bench comes down to its stop), then climb
        /// the bench (0.6) and the sill (1.2) and walk on to <c>terrace</c>. He waits for each leaf to settle before he walks
        /// into its swing (it would wait for him). Returns the steps from the start.
        /// </summary>
        private static int Solve(ChapterSim s, Action<ChapterSim> each = null, Func<ChapterSim, bool> stopAt = null)
        {
            bool Stop(ChapterSim x) => stopAt != null && stopAt(x);
            long n0 = s.Steps;
            int N() => (int)(s.Steps - n0);
            void Go(MotorInput i, Func<ChapterSim, bool> done) => Until(s, i, x => done(x) || Stop(x), each: each);
            void Once(MotorInput i) { s.Step(i); each?.Invoke(s); }

            Go(Right, x => x.X >= 351.72);                                                        // the gallery, to the bed's head
            if (Stop(s)) return N();
            Once(JumpRight);                                                                       // onto the bed (0.45: a mantle)
            Go(default, x => Free(x) && x.Y == 0.45);
            if (Stop(s)) return N();
            Go(Right, x => Free(x) && x.Y == 0 && x.X > Dl18Lane.SillX - 0.3);                    // off its foot, between it and the sill
            if (Stop(s)) return N();
            Once(Use);                                                                             // the foot rail
            Go(default, x => !x.Busy && Bed(x).State == FoldingLeafState.Folded);
            if (Stop(s)) return N();
            Go(Left, x => x.X <= 353.45);                                                          // to the strap
            if (Stop(s)) return N();
            Once(Use);
            Go(default, x => !x.Busy && Bench(x).State == FoldingLeafState.Down);
            if (Stop(s)) return N();
            Go(Right, x => x.Vx == 0 && x.X > 353.0);                                             // to the bench's face
            if (Stop(s)) return N();
            Climb(s, 0.6, each);
            if (Stop(s)) return N();
            Go(Right, x => x.Vx == 0 && x.X > 353.9);                                             // to the sill's face
            if (Stop(s)) return N();
            Climb(s, Dl18Lane.SillY, each);
            if (Stop(s)) return N();
            Go(Right, x => x.Checkpoints.Current.Name == "terrace");
            return N();
        }

        // ---- The chapter: Checkpoint.GameOrder and chapter 2's table ------------------------------------------------------

        [Fact]
        public void GameOrder_IsThePrototypeOrderThenChapter2s_WithNoDuplicates()
        {
            var game = Checkpoint.GameOrder;
            Assert.True(game.Length > Checkpoint.PrototypeOrder.Length);
            for (int i = 0; i < Checkpoint.PrototypeOrder.Length; i++) Assert.Equal(Checkpoint.PrototypeOrder[i], game[i]);
            Assert.Equal(game.Length, new HashSet<string>(game).Count);
            Assert.Equal("ring_a", game[Checkpoint.PrototypeOrder.Length]);
            Assert.True(new Checkpoint(game, "terrace").Past("ring_a"));
            Assert.True(new Checkpoint(game, "ring_a").Past("workshop"));                       // chapter 2 comes after chapter 1
        }

        [Fact]
        public void SomeoneHome_IsRegion7FromTheStairHead_ItsCheckpointsInDl18()
        {
            var def = ChapterDefs.SomeoneHome();
            Assert.Equal(ChapterDefs.SomeoneHomeId, def.Id);
            Assert.Same(Checkpoint.GameOrder, def.Checkpoints.Order);
            var dl18 = def.Scene(Dl18Scene.Id);
            Assert.Equal(7, dl18.Region);
            Assert.Equal(347.0, dl18.X0);
            Assert.Equal(361.0, dl18.X1);
            var ringA = def.Checkpoints.Get("ring_a");
            var terrace = def.Checkpoints.Get("terrace");
            Assert.Equal((347.6, 0.0, 7, Dl18Scene.Id), (ringA.X, ringA.Y, ringA.Region, ringA.Scene));
            Assert.Equal((355.8, 1.2, 7, Dl18Scene.Id), (terrace.X, terrace.Y, terrace.Region, terrace.Scene));

            var s = Begin();
            Assert.Equal(Dl18Scene.Id, s.Current.Id);
            Assert.Equal(7, s.Lane.Region);
            Assert.Equal((347.6, 0.0), (s.X, s.Y));
            Assert.Equal(FoldingLeafState.Down, Bed(s).State);                                     // §2 "Her room": the bed down,
            Assert.Equal(FoldingLeafState.Folded, Bench(s).State);                                 // the bench folded above it
            Assert.Throws<InvalidOperationException>(() => s.NewGame());                           // "start" is the prologue's
        }

        [Fact]
        public void SceneSim_TakesAnotherChaptersTable()
        {
            var sim = new SceneSim(Dl18Scene.Def(), ChapterDefs.SomeoneHomeCheckpoints);
            sim.Begin("terrace");
            Assert.Equal((355.8, 1.2), (sim.X, sim.Y));
            Assert.Throws<ArgumentException>(() => new SceneSim(Dl18Scene.Def()).Begin("ring_a"));   // the prologue's table has no ring_a
        }

        // ---- The lane (§3) ------------------------------------------------------------------------------------------------

        [Fact]
        public void Lane_FloorsAndHeights_DL18_3()
        {
            var s = Begin();
            var lane = s.Lane;
            Assert.Equal(0, lane.SurfaceAt(348.0));                                                // gallery
            Assert.Equal(0, lane.SurfaceAt(351.7));                                                // box room
            Assert.Equal(0.45, lane.SurfaceAt(352.5), 12);                                         // the bed down: its top
            Assert.Equal(0.45, lane.SurfaceAt(353.5), 12);                                         // the quilt is not a step
            Assert.Equal(0, lane.SurfaceAt(354.1));                                                // beyond the bed's foot
            Assert.Equal(1.2, lane.SurfaceAt(Dl18Lane.SillX));                                     // the sill lip
            Assert.Equal(1.2, lane.SurfaceAt(358.0));                                              // the terrace landing
            Assert.Equal(LaneProbe.NoCeiling, lane.CeilingAt(353.8));
            lane.Limits(350, 0, out double left, out _);
            Assert.Equal(347.0 + Dl18Lane.Half, left);                                             // the stair head

            var t = Begin("terrace");                                                              // solved: bed folded, bench a seat
            Assert.Equal(0, t.Lane.SurfaceAt(352.5));
            Assert.Equal(0.6, t.Lane.SurfaceAt(353.8), 12);
            Assert.Equal(0, t.Lane.SurfaceAt(353.3));
        }

        // ---- The scripted solve and the mechanical floor (§10) -------------------------------------------------------------

        [Fact]
        public void ScriptedSolve_ReachesTheTerraceInAbout25s_AndItsSaveHoldsBothLeavesSolved()
        {
            var store = new MemorySaveStore();
            var s = Begin(store: store);
            int steps = Solve(s);
            double t = steps * Dt;
            Assert.InRange(t, 25 * 0.75, 25 * 1.25);                                               // "about 25 s from ring_a to terrace"
            Assert.Equal("terrace", s.Checkpoints.Current.Name);
            Assert.Equal((FoldingLeafState.Folded, FoldingLeafState.Down), (Bed(s).State, Bench(s).State));
            Assert.True(s.X >= Dl18Scene.TerraceX && s.Y == Dl18Lane.LandingY);

            Assert.True(store.TryLoad(0, out var m));
            Assert.Equal("terrace", m.Checkpoint);
            Assert.Equal(ChapterDefs.SomeoneHomeId, m.Scene);
            var b = new ChapterSim(ChapterDefs.SomeoneHome(), store: store);
            Assert.True(b.Continue());
            Assert.True(b.Checkpoints.RestoredSnapshot);
            Assert.Equal((FoldingLeafState.Folded, FoldingLeafState.Down), (Bed(b).State, Bench(b).State));
        }

        [Fact]
        public void Checkpoints_ByPosition_RingAAtTheStart_TerraceOnlyOnTheLanding()
        {
            var s = Begin();
            Assert.Equal("ring_a", s.Checkpoints.Current.Name);
            s.Motor.Place(354.9, 1.2);                                                             // in the doorway: not yet
            s.Step(default);
            Assert.Equal("ring_a", s.Checkpoints.Current.Name);
            Until(s, Right, x => x.X >= Dl18Scene.TerraceX);
            Assert.Equal("terrace", s.Checkpoints.Current.Name);
        }

        [Fact]
        public void RespawnAndContinueAtTerrace_TheLeavesSolved_HeStandsOnTheLanding()
        {
            var store = new MemorySaveStore();
            var s = Begin(store: store);
            Solve(s);
            Until(s, Right, x => x.X > 357);
            s.Respawn();
            Assert.Equal((355.8, 1.2), (s.X, s.Y));
            Assert.Equal((FoldingLeafState.Folded, FoldingLeafState.Down), (Bed(s).State, Bench(s).State));
            Assert.Equal(Dl18Scene.Id, s.Current.Id);

            var c = new ChapterSim(ChapterDefs.SomeoneHome(), store: store);
            Assert.True(c.Continue());
            Assert.Equal("terrace", c.Checkpoints.Current.Name);
            Assert.Equal((355.8, 1.2), (c.X, c.Y));
            Assert.True(c.Grounded);
            Assert.Equal((FoldingLeafState.Folded, FoldingLeafState.Down), (Bed(c).State, Bench(c).State));
            for (int i = 0; i < 60; i++) c.Step(default);
            Assert.Equal((355.8, 1.2), (c.X, c.Y));                                               // he stands there

            var fresh = Begin("terrace");                                                          // derived from the checkpoint alone
            Assert.Equal((FoldingLeafState.Folded, FoldingLeafState.Down), (Bed(fresh).State, Bench(fresh).State));
        }

        // ---- Wrong paths (§4, §10) -----------------------------------------------------------------------------------------

        [Fact]
        public void WrongPath_BenchPulledWithTheBedDown_PropsOnTheQuilt_AndAHopAtItLandsHimBackOnTheBed()
        {
            var s = Begin();
            s.Motor.Place(353.45, 0.45);                                                           // on the bed, at the strap
            s.Step(Use);
            int toggled = -1, propped = -1, k = 0;
            Until(s, default, x => !x.Busy && Settled(Bench(x)), each: x =>
            {
                k++;
                if (toggled < 0 && Bench(x).State != FoldingLeafState.Folded) toggled = k;
                if (propped < 0 && Bench(x).State == FoldingLeafState.Propped) propped = k;
            });
            Assert.Equal(FoldingLeafState.Propped, Bench(s).State);
            Assert.InRange(Bench(s).AngleDeg, 15, 35);                                             // tilted, "about 30°"
            Assert.InRange((propped - toggled) * Dt, 0, 1.5);                                      // within 1.5 s of the Use's toggle (the hop)
            Assert.Equal(0.45, s.Y, 9);                                                            // the hop put him back on the bed
            Assert.Equal(353.45 - 0.4, s.X, 9);

            // He goes for it: a hop at the tilted bench lands him back on the mattress, never on the bench.
            Until(s, Right, x => x.X >= 353.3);
            s.Step(new MotorInput { JumpPressed = true });
            Assert.False(s.Grounded);
            int back = Until(s, default, x => x.Grounded);
            Assert.InRange(back * Dt, 0, 1.0);
            Assert.Equal(0.45, s.Y, 9);
            for (double x = 353.4; x <= 353.8; x += 0.05) Assert.Equal(0.45, s.Lane.SurfaceAt(x), 9);   // never ground while propped
        }

        /// <summary>
        /// §10 "Reverse case". In the lane the seat (0.6) is ground over the foot rail's floor, so with the bench down he cannot
        /// stand at the foot rail (the doc's D-17 would crouch under the seat: a height field has no space under it); the
        /// bed is pulled down on the chapter's own graph instead, as from the foot rail.
        /// </summary>
        [Fact]
        public void WrongPath_Reverse_TheBedPulledDownOntoTheBench_PropsAgainstItWithin1_5s()
        {
            var s = Begin("terrace");                                                              // bed folded, bench down
            int toggled = -1, propped = -1;
            int played = Mech.PlayAct(s.Graph, Bed(s), onStep: (k, f) =>
            {
                if (toggled < 0 && Bed(s).State != FoldingLeafState.Folded) toggled = k;
                if (propped < 0 && Bed(s).State == FoldingLeafState.Propped) propped = k;
            });
            int more = Mech.RunUntil(s.Graph, () => Bed(s).State == FoldingLeafState.Propped, 300);
            if (propped < 0) propped = played + more;
            Assert.Equal(FoldingLeafState.Propped, Bed(s).State);
            Assert.InRange((propped - toggled) * Dt, 0, 1.5);
            Assert.False(Bed(s).Standable);
            Assert.Equal(FoldingLeafState.Down, Bench(s).State);
            Assert.Equal(0.6, s.Lane.SurfaceAt(353.8), 9);                                         // the seat is still a step
            Assert.Equal(0, s.Lane.SurfaceAt(352.5));                                              // the propped bed is not
        }

        // ---- No crushing (§10) ---------------------------------------------------------------------------------------------

        [Fact]
        public void NoCrushing_TheBenchMeetsHimAndStopsWithin0_1s_ThenResumesWhenHeMoves()
        {
            var s = Begin();
            Mech.PlayAct(s.Graph, Bed(s));                                                         // the bed folded away
            Mech.RunUntil(s.Graph, () => Bed(s).State == FoldingLeafState.Folded, 300);
            Mech.PlayAct(s.Graph, Bench(s));                                                       // the bench let go,
            s.Motor.Place(353.8, 0);                                                               // with him under its free edge
            var bench = Bench(s);
            var before = bench.State;
            Until(s, default, x =>
            {
                if (bench.State == FoldingLeafState.Waiting) return true;
                before = bench.State;
                return false;
            }, 120);
            Assert.Equal(FoldingLeafState.Unfolding, before);                                      // it stopped the step it met him
            Assert.True(Mech.Emitted(s.Graph, Dl18Scene.Bench, FoldingLeafEvent.Met));
            var body = SweptBox.Aligned(s.X - 0.17, s.X + 0.17, 0.10, 0.44, s.Y, s.Y + 0.76);
            for (int i = 0; i < bench.VolumeCount; i++) Assert.False(SweptBox.Overlap(bench.Volume(i), body, 1e-4));   // touching, not into him
            double angle = bench.AngleDeg;
            for (int i = 0; i < 60; i++) s.Step(default);                                          // it waits while he stays
            Assert.Equal(FoldingLeafState.Waiting, bench.State);
            Assert.Equal(angle, bench.AngleDeg);
            Until(s, Left, x => bench.State != FoldingLeafState.Waiting, 120);                    // he moves clear: it carries on
            Assert.True(s.X < 353.8 - 0.1);
            Until(s, default, x => bench.State == FoldingLeafState.Down, 120);
            Assert.True(bench.Standable);
        }

        // ---- No traps (§4 "Reset", §10) ------------------------------------------------------------------------------------

        /// <summary>
        /// The four ways the leaves rest in play (§3's table): the start, both folded, the solution, and the bench propped on
        /// the quilt (both pulled down). The bed propped on the bench needs the foot rail with the seat down, which the lane
        /// cannot reach (see the reverse case), so play never gets there.
        /// </summary>
        public static IEnumerable<object[]> Configurations() => new[]
        {
            new object[] { "start" }, new object[] { "bothFolded" }, new object[] { "solved" }, new object[] { "benchPropped" },
        };

        private static ChapterSim Configure(string config)
        {
            var s = Begin(config == "solved" ? "terrace" : "ring_a");
            void Toggle(FoldingLeaf l)
            {
                Mech.PlayAct(s.Graph, l);
                Assert.True(Mech.RunUntil(s.Graph, () => Settled(Bed(s)) && Settled(Bench(s)), 600) > 0);
            }
            if (config == "bothFolded") Toggle(Bed(s));
            else if (config == "benchPropped") Toggle(Bench(s));
            return s;
        }

        [Theory]
        [MemberData(nameof(Configurations))]
        public void NoTraps_FromEveryStandingPlace_EachLeafHasAReachableStation_AndOneUseReturnsIt(string config)
        {
            var s = Configure(config);
            var reach = new LaneReach(s, 347.2, 357.0);
            var bed = Bed(s);
            var bench = Bench(s);
            int starts = 0;
            for (int i = 0; i <= 52; i++)
            {
                double x = 351.6 + 0.05 * i;
                if (!reach.CanStand(x)) continue;
                starts++;
                var r = reach.From(x);
                Assert.True(reach.Any(r, n => reach.X(n) < Dl18Lane.RoomDoorX), config + ": no way back to the gallery from " + x);
                Assert.True(reach.Any(r, n => reach.Answers(n, bench)), config + ": the strap is out of reach from " + x);
                // The foot rail too, except under the seat, where the folded bed is out of the way and the strap frees it.
                if (!reach.Any(r, n => reach.Answers(n, bed)))
                    Assert.True(config == "solved", config + ": the foot rail is out of reach from " + x);
                if (config == "solved")
                    Assert.True(reach.Any(r, n => reach.X(n) >= Dl18Scene.TerraceX && reach.Y(n) == Dl18Lane.LandingY), "no way out from " + x);
            }
            Assert.True(starts >= 20, config + ": " + starts + " places to stand");

            // One Use at a station: the leaf goes back (a leaf the other rests on waits until that one goes back: §4).
            foreach (var leaf in new[] { bed, bench })
            {
                if (!reach.HasStation(leaf)) continue;                                                 // the foot rail under the seat
                var t = Configure(config);
                var l = t.Graph.Get<FoldingLeaf>(leaf.Id);
                var other = ReferenceEquals(leaf, bed) ? Bench(t) : Bed(t);
                var before = l.State;
                var at = reach.Station(leaf);
                t.Motor.Place(reach.X(at), reach.Y(at), reach.Facing(at, leaf));
                Assert.True(t.Motor.PreviewUse(out var c) && ReferenceEquals(c.Target, l), config + " " + leaf.Id);
                t.Step(Use);
                Until(t, default, x => !x.Busy && Settled(l) || (l.State == FoldingLeafState.Waiting && other.State == FoldingLeafState.Propped && !x.Busy), 900);
                if (l.State == FoldingLeafState.Waiting)
                {
                    Assert.Equal(FoldingLeafState.Down, before);                                  // it holds the other's prop
                    Mech.PlayAct(t.Graph, other);
                    Assert.True(Mech.RunUntil(t.Graph, () => l.State == FoldingLeafState.Folded, 600) > 0);
                }
                else if (before == FoldingLeafState.Propped || before == FoldingLeafState.Down) Assert.Equal(FoldingLeafState.Folded, l.State);
                else Assert.True(l.State == FoldingLeafState.Down || l.State == FoldingLeafState.Propped, config + " " + leaf.Id + " " + l.State);
            }
        }

        // ---- The chain and the curiosities (§2, §6, §11) -------------------------------------------------------------------

        /// <summary>Use at (x, y) and the act it starts, to its end: the cues it raised, in order.</summary>
        private static List<string> Play(ChapterSim s, double x, double y, out int steps, Action<ChapterSim> first = null)
        {
            s.Motor.Place(x, y);
            s.Step(Use);
            first?.Invoke(s);
            var cues = new List<string>();
            foreach (var c in s.Cues) cues.Add(c.ToString());
            steps = 1 + Until(s, default, z => { foreach (var c in z.Cues) cues.Add(c.ToString()); return !z.Busy; });
            return cues;
        }

        [Fact]
        public void TheWorksDoorsChain_TwoTugs_ItClanksTwice_AndNothingGives()
        {
            var s = Begin();
            var cues = Play(s, 348.0, 0, out int steps, first: x =>
            {
                Assert.Equal(Dl18Rules.WorksDoor, x.SceneActKind);
                Assert.Equal(Dl18Rules.Tug, x.SceneActPhase);
            });
            Assert.Equal(new[] { "dl18.chain.clank", "dl18.chain.clank" }, cues);
            Assert.InRange(steps * Dt, 2 * QuirkAct.ClipSeconds("Tug") - Dt, 2 * QuirkAct.ClipSeconds("Tug") + 2 * Dt);
            Assert.Equal((348.0, 0.0), (s.X, s.Y));                                                // he tugs where he stands
            Assert.Equal((FoldingLeafState.Down, FoldingLeafState.Folded), (Bed(s).State, Bench(s).State));
            Assert.Equal("ring_a", s.Checkpoints.Current.Name);
        }

        [Fact]
        public void TheAlarmClock_RingsTwoSeconds_HeStartles_ThenPatsIt()
        {
            var s = Begin();
            s.Motor.Place(351.8, 0);
            s.Step(Use);
            Assert.Equal(Dl18Rules.AlarmClock, s.SceneActKind);
            Assert.Equal(Dl18Rules.Startle, s.SceneActPhase);
            Assert.Contains(s.Cues, c => c.Id == Dl18Rules.ClockRing);
            int still = Until(s, default, z => { foreach (var c in z.Cues) if (c.Id == Dl18Rules.ClockStill) return true; return false; });
            Assert.InRange((still + 1) * Dt, Dl18Rules.RingSeconds - Dt, Dl18Rules.RingSeconds + Dt);   // rings 2 s
            Assert.Equal(Dl18Rules.Pat, s.SceneActPhase);
            Until(s, default, z => !z.Busy);
            Assert.False(s.Busy);
        }

        [Fact]
        public void TheSketch_ACloseLook_ThreeSeconds_FromTheBenchSeat()
        {
            var s = Begin("terrace");                                                              // the bench down: a seat
            s.Motor.Place(353.75, 0.6);
            Assert.False(s.Motor.PreviewUse(out _));                                               // nothing else answers on the bench
            var cues = Play(s, 353.75, 0.6, out int steps);
            Assert.Equal(new[] { "dl18.sketch.look" }, cues);
            Assert.InRange(steps * Dt, Dl18Rules.LookSeconds - Dt, Dl18Rules.LookSeconds + 2 * Dt);

            var floor = Begin("terrace");
            floor.Motor.Place(353.2, 0);                                                           // from the floor: out of reach
            floor.Step(Use);
            Assert.True(floor.SceneActKind.IsNone);
        }

        [Fact]
        public void TheStrapAndTheFootRail_WinOverTheCuriosities()
        {
            var s = Begin();
            s.Motor.Place(353.6, 0.45);                                                            // on the bed under the sketch, at the strap
            s.Step(Use);
            Assert.True(s.SceneActKind.IsNone);
            Assert.Same(Bench(s), s.MotorActTarget);
        }

        // ---- Determinism and the round trip --------------------------------------------------------------------------------

        private static string State(ChapterSim s)
        {
            var m = s.Motor.Capture();
            return Mech.Dump(s.Graph) + "|" + m.X.ToString("R") + "," + m.Y.ToString("R") + "," + m.Vx.ToString("R") + "," + m.Vy.ToString("R")
                + "," + m.Facing + "," + m.Yaw.ToString("R") + "," + m.Grounded + "," + m.Crouched + "," + m.Clip + "," + m.ClipTime.ToString("R")
                + "|" + s.Clock.ToString("R") + "|" + s.Checkpoints.Current.Name;
        }

        [Fact]
        public void Determinism_TheSameScriptTwice_GivesTheSameSnapshot()
        {
            var a = Begin();
            var b = Begin();
            Assert.Equal(Solve(a), Solve(b));
            Assert.Equal(State(a), State(b));
        }

        [Fact]
        public void RoundTrip_ASnapshotWhileTheBedFolds_RestoredThen60Steps_Equals60StepsStraight()
        {
            var a = Begin();
            Solve(a, stopAt: x => Bed(x).State == FoldingLeafState.Folding && x.Motor.CanCapture && !x.Busy);
            Assert.Equal(FoldingLeafState.Folding, Bed(a).State);
            var graph = Mech.Snapshot(a.Graph);
            var motor = a.Motor.Capture();

            var b = Begin();
            b.Graph.Restore(graph);
            b.Motor.SetState(motor);
            b.Clock = a.Clock;
            Assert.Equal(State(a), State(b));
            for (int i = 0; i < 60; i++)
            {
                var input = i < 30 ? default : Left;
                a.Step(input);
                b.Step(input);
            }
            Assert.Equal(State(a), State(b));
            Assert.NotEqual(FoldingLeafState.Down, Bed(b).State);
        }
    }
}
