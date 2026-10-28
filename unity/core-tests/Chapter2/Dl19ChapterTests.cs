using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl18;
using DeadLetter.Core.Scenes.Dl19;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-19 A Repair That Held in chapter 2's <see cref="ChapterSim"/>, driven by scripted input. No prototype and no
    /// trace: the scene doc's acceptance checks (docs/scenes/DL-19_a_repair_that_held.md §10) are the tests, with the layout
    /// of §3, the puzzle of §4, the checkpoints of §9 and the grey-box of §11. The mechanisms on their own are
    /// <see cref="Dl19MechanismTests"/>.
    /// </summary>
    public class Dl19ChapterTests
    {
        private const double Dt = ChapterSim.StepSeconds;
        private static readonly MotorInput Right = new MotorInput { Move = 1 }, Left = new MotorInput { Move = -1 };
        private static readonly MotorInput Tap = new MotorInput { UsePressed = true };

        internal static ChapterSim Begin(string cp = "half_landing", ISaveStore store = null)
        {
            var s = new ChapterSim(ChapterDefs.SomeoneHome(), store: store);
            s.Begin(cp);
            return s;
        }

        internal static RatchetJack Jack(ChapterSim s) => s.Graph.Get<RatchetJack>(Dl19Scene.Jack);
        internal static BracketPins Pins(ChapterSim s) => s.Graph.Get<BracketPins>(Dl19Scene.Pins);
        internal static HalfLanding Landing(ChapterSim s) => s.Graph.Get<HalfLanding>(Dl19Scene.Landing);

        private static string Where(ChapterSim s)
            => "t=" + (s.Steps * Dt).ToString("F2") + " x=" + s.X.ToString("F3") + " y=" + s.Y.ToString("F3") + " act=" + SceneSim.KindOf(s)
               + " hold=" + s.Motor.Hold + " jack=" + Jack(s).State + "@" + Jack(s).X.ToString("F3") + "/" + Jack(s).Extension.ToString("F3")
               + " pins=" + Pins(s).State + " landing=" + Landing(s).State + "@" + Landing(s).Position.ToString("F3") + " cp=" + s.Checkpoints.Current.Name;

        /// <summary>Every pin is in exactly one of the fork, the cup, the clip or his hands (§10 "No lost pin").</summary>
        internal static void AssertPinsPlaced(BracketPins p)
        {
            Assert.Contains(p.BentPin, new[] { PinPlace.Fork, PinPlace.Cup });
            Assert.Contains(p.SparePin, new[] { PinPlace.Clip, PinPlace.Hands, PinPlace.Fork });
            Assert.False(p.BentPin == PinPlace.Fork && p.SparePin == PinPlace.Fork);
        }

        /// <summary>
        /// Scripted play: each move is a few steps of input until a condition (§4's solution, a step at a time). Every step
        /// runs <see cref="Each"/>; once <see cref="StopAt"/> holds, every later move does nothing.
        /// </summary>
        internal sealed class Play
        {
            public readonly ChapterSim S;
            public Action<ChapterSim> Each;
            public Func<ChapterSim, bool> StopAt;
            public bool Stopped;

            public Play(ChapterSim s, Action<ChapterSim> each = null) { S = s; Each = each; }

            public void Step(MotorInput i)
            {
                if (Stopped) return;
                S.Step(i);
                Each?.Invoke(S);
                if (StopAt != null && StopAt(S)) Stopped = true;
            }

            /// <summary>Steps with <paramref name="i"/> until <paramref name="done"/>; returns the steps taken.</summary>
            public int Until(MotorInput i, Func<ChapterSim, bool> done, int max = 1800)
            {
                for (int k = 1; k <= max; k++)
                {
                    if (Stopped) return k - 1;
                    Step(i);
                    if (done(S)) return k;
                }
                throw new Xunit.Sdk.XunitException("never: " + Where(S));
            }

            private static bool Still(ChapterSim s) => !s.Busy && s.Grounded && !s.Motor.IsMantling && Math.Abs(s.Vx) < 1e-3 && s.Motor.Hold == HoldKind.None;

            /// <summary>Walks to x and stops.</summary>
            public void WalkTo(double x)
            {
                if (S.X < x) Until(Right, s => s.X >= x || (s.Vx == 0 && s.Steps > 0 && Blocked(s, +1)));
                else if (S.X > x) Until(Left, s => s.X <= x);
                Until(default, Still, 120);
            }

            private static bool Blocked(ChapterSim s, int dir) => s.Lane.SurfaceAt(s.X + dir * (s.Config.Half + 0.005)) > s.Y + s.Config.StepUp;

            /// <summary>Takes hold of the jack's push bar and pushes (+1, to the pocket) or pulls (−1, to the bay) it to the next detent.</summary>
            public void MoveJack(int dir)
            {
                var j = Jack(S);
                WalkTo(j.State == RatchetJackState.InPocket ? 362.75 : j.X - j.Params.Gap);
                Step(Tap);
                Until(default, s => s.Motor.Hold == HoldKind.Push, 120);
                Until(new MotorInput { Move = dir }, s => s.Motor.Hold == HoldKind.None);
                Until(default, Still, 120);
            }

            /// <summary>Holds Use at the crank (stick back to wind down) until <paramref name="done"/>, then lets go.</summary>
            public void Crank(bool down, Func<ChapterSim, bool> done)
            {
                WalkTo(362.98);
                var hold = new MotorInput { UseHeld = true, Move = down ? -1 : 0 };
                var first = hold;
                first.UsePressed = true;
                Step(first);
                Assert.True(Stopped || S.MotorActTarget is RatchetJack, "no crank: " + Where(S));
                Until(hold, done);
                Until(default, s => !s.Busy, 120);
            }

            /// <summary>One Use at the bracket.</summary>
            public void UsePins()
            {
                WalkTo(363.13);
                Step(Tap);
                Assert.True(Stopped || S.MotorActTarget is BracketPins, "no bracket: " + Where(S));
                Until(default, s => !s.Busy, 300);
            }

            /// <summary>Jumps toward a face ahead (a mantle) and waits until he stands on <paramref name="y"/>.</summary>
            public void Climb(double y)
            {
                Step(new MotorInput { Move = 1, JumpPressed = true });
                Assert.True(Stopped || S.Motor.IsMantling, "no mantle: " + Where(S));
                Until(default, s => !s.Busy && !s.Motor.IsMantling && s.Grounded && Math.Abs(s.Y - y) < 1e-9, 300);
            }

            /// <summary>
            /// §4's solution from wherever the jack and the pins are: the jack into its pocket, crank level, swap the pins,
            /// wind down, draw the jack back, mantle onto the half landing and walk up to <c>repaired</c>.
            /// </summary>
            public void Solve()
            {
                if (Jack(S).State != RatchetJackState.InPocket && Pins(S).State != BracketPinsState.SpareSeated) MoveJack(+1);
                if (Pins(S).State != BracketPinsState.SpareSeated)
                {
                    if (!Landing(S).MarksMeet) Crank(Landing(S).Position > Landing(S).Params.LevelY, s => Landing(s).MarksMeet);
                    for (int i = 0; i < 4 && !Stopped && Pins(S).State != BracketPinsState.SpareSeated; i++) UsePins();
                }
                if (Jack(S).Extension > 0) Crank(true, s => Jack(s).Extension <= 0);
                if (Jack(S).State != RatchetJackState.Parked) MoveJack(-1);
                Until(Right, s => s.Vx == 0 && s.X > 363.3);
                Climb(Dl19Lane.LevelY);
                Until(Right, s => s.Checkpoints.Current.Name == "repaired");
            }
        }

        // ---- The chapter: its table, and the seam from DL-18 ---------------------------------------------------------------

        [Fact]
        public void SomeoneHome_ListsDl19AfterDl18_ItsCheckpointsInRegion7()
        {
            var def = ChapterDefs.SomeoneHome();
            Assert.Equal(new[] { Dl18Scene.Id, Dl19Scene.Id }, new[] { def.Scenes[0].Id, def.Scenes[1].Id });
            var dl19 = def.Scene(Dl19Scene.Id);
            Assert.Equal((7, 361.0, 377.0), (dl19.Region, dl19.X0, dl19.X1));
            var a = def.Checkpoints.Get("half_landing");
            var b = def.Checkpoints.Get("repaired");
            Assert.Equal((362.0, 1.2, 7, Dl19Scene.Id), (a.X, a.Y, a.Region, a.Scene));
            Assert.Equal((371.0, 2.3, 7, Dl19Scene.Id), (b.X, b.Y, b.Region, b.Scene));

            var s = Begin();
            Assert.Equal((362.0, 1.2), (s.X, s.Y));
            Assert.Equal(Dl19Scene.Id, s.Current.Id);
            Assert.Equal((RatchetJackState.Parked, BracketPinsState.BentSeated, HalfLandingState.Drooping), (Jack(s).State, Pins(s).State, Landing(s).State));
            s.Step(default);
            Assert.Equal(PinSound.Creak, Pins(s).Sound);                                          // it hangs on the bent pin, creaking
        }

        [Fact]
        public void Lane_FloorsAndHeights_DL19_3()
        {
            var s = Begin();
            var lane = s.Lane;
            Assert.Equal(1.2, lane.SurfaceAt(361.5));                                              // the terrace landing
            Assert.Equal(1.2, lane.SurfaceAt(363.4));                                              // the mantle spot (jack in its bay)
            Assert.Equal(1.55, lane.SurfaceAt(363.6), 9);                                          // the drooping left end
            Assert.Equal(1.75, lane.SurfaceAt(366.2), 9);                                          // the hinge
            Assert.Equal(1.75 + 0.55 / 3, lane.SurfaceAt(366.7), 9);                               // the flight
            Assert.True(lane.IsRamp(366.7));
            Assert.Equal(2.3, lane.SurfaceAt(371.0), 9);                                           // the upper terrace
            Assert.Equal(2.3, lane.SurfaceAt(376.9), 9);
            lane.Limits(370, 2.3, out double left, out _);
            Assert.Equal(347.0 + Dl18Lane.Half, left);                                             // one region: DL-18's stair head is still the wall
        }

        [Fact]
        public void Seam_WalkingFromDl18IntoDl19_At361_OnOneFloor()
        {
            var s = Begin("terrace");
            var changes = new List<(string, string, ExitDir)>();
            s.SceneChanged += (a, b, dir) => changes.Add((a?.Id, b?.Id, dir));
            var play = new Play(s, x => Assert.Equal(1.2, x.Y, 12));                              // never a step at the seam
            play.Until(Right, x => x.Checkpoints.Current.Name == "half_landing", 600);
            Assert.Equal(new[] { (Dl18Scene.Id, Dl19Scene.Id, ExitDir.Right) }, changes);
            Assert.Equal(Dl19Scene.Id, s.Current.Id);
            Assert.True(s.X >= 362.0);
            Assert.Equal(361.0, s.Def.Scene(Dl19Scene.Id).X0);

            changes.Clear();
            play.Until(Left, x => x.X < 360.5, 600);                                              // and back: one world
            Assert.Equal(new[] { (Dl19Scene.Id, Dl18Scene.Id, ExitDir.Left) }, changes);
            Assert.Equal("half_landing", s.Checkpoints.Current.Name);
        }

        // ---- The scripted solve and the mechanical floor (§10) -------------------------------------------------------------

        [Fact]
        public void ScriptedSolve_ReachesRepairedInAbout35s_NoPinIsEverLost_AndTheSpareSeatsWithHeldAndWitness()
        {
            var s = Begin();
            var cues = new List<string>();
            var play = new Play(s, x =>
            {
                AssertPinsPlaced(Pins(x));
                foreach (var c in x.Cues) cues.Add(c.ToString());
            });
            play.Solve();
            double t = s.Steps * Dt;
            Assert.InRange(t, 35 * 0.75, 35 * 1.25);                                               // "about 35 s from half_landing to repaired"
            Assert.Equal("repaired", s.Checkpoints.Current.Name);
            Assert.Equal((RatchetJackState.Parked, BracketPinsState.SpareSeated, HalfLandingState.Pinned), (Jack(s).State, Pins(s).State, Landing(s).State));
            Assert.Equal(1.75, Landing(s).Position, 12);
            Assert.Contains("held", cues);
            Assert.Single(cues.FindAll(c => c == "witness"));
            Assert.DoesNotContain("dl19.lurch", cues);

            play.Until(Right, x => x.Exited, 900);                                                 // on to the lower flat's door
            double toDoor = s.Steps * Dt;
            Assert.InRange(toDoor - t, 3.0, 6.0 / 0.9 + 1);                                       // the upper terrace's 6 m at a run or a walk
            Assert.True(toDoor < 45 * 1.25);
        }

        // ---- Wrong paths (§4, §10) -----------------------------------------------------------------------------------------

        [Fact]
        public void WrongPath_PinFirst_DropsOntoTheStopsWithin0_5s_HalfOut_HeStartles_AnotherUseStrains_AndItCanStillBeSolved()
        {
            var s = Begin();
            int k = 0, drawn = -1, onStops = -1, startled = -1;
            var play = new Play(s, x =>
            {
                k++;
                AssertPinsPlaced(Pins(x));
                if (drawn < 0 && x.Graph.Log.Has(Dl19Scene.Pins, MechanismEventKind.Event, (int)BracketPinsEvent.Draw)) drawn = k;
                if (onStops < 0 && Landing(x).State == HalfLandingState.OnStops) onStops = k;
                if (startled < 0 && x.SceneActPhase == ActIds.Clip(ClipNames.Startle)) startled = k;
            });
            play.UsePins();
            Assert.True(drawn > 0 && onStops > 0);
            Assert.InRange((onStops - drawn) * Dt, 0, 0.5);
            Assert.Equal(BracketPinsState.BentHalfOut, Pins(s).State);
            Assert.Equal(1.45, Landing(s).Position, 12);
            play.Until(default, x => startled > 0 && !x.Busy, 200);
            Assert.InRange((startled - onStops) * Dt, 0, 1.5);

            int strains = 0;
            play.Each += x => { if (x.Graph.Log.Has(Dl19Scene.Pins, MechanismEventKind.Event, (int)BracketPinsEvent.Strain)) strains++; };
            play.UsePins();
            Assert.Equal(1, strains);                                                              // a strain, and nothing moves
            Assert.Equal(BracketPinsState.BentHalfOut, Pins(s).State);
            Assert.Equal(1.45, Landing(s).Position, 12);

            play.Solve();                                                                          // the solution is intact
            Assert.Equal("repaired", s.Checkpoints.Current.Name);
        }

        public static IEnumerable<object[]> Unpinned() => new[] { new object[] { false }, new object[] { true } };

        [Theory]
        [MemberData(nameof(Unpinned))]
        public void WrongPath_StepOn_LurchOrRock_TeeterAndAHopBackWithin1_5s_ThenSettle_AndSettleKeepsHisJump(bool onStops)
        {
            var s = Begin();
            var play = new Play(s);
            if (onStops) { play.UsePins(); play.Until(default, x => !x.Busy && x.Act == null, 200); }
            var cues = new List<string>();
            int k = 0, lurch = -1, hop = -1;
            play.Each = x =>
            {
                k++;
                foreach (var c in x.Cues) cues.Add(c.ToString());
                if (lurch < 0 && x.Graph.Log.Has(Dl19Scene.Landing, MechanismEventKind.Event, (int)HalfLandingEvent.Lurch)) lurch = k;
                if (hop < 0 && x.SceneActPhase == Dl19LurchAct.Hop) hop = k;
            };
            play.Until(Right, x => x.Vx == 0 && x.X > 363.3);
            play.Step(new MotorInput { Move = 1, JumpPressed = true });                            // he mantles onto its left end
            Assert.True(s.Motor.IsMantling);
            play.Until(default, x => lurch > 0, 300);
            Assert.Contains(onStops ? "dl19.rock" : "dl19.lurch", cues);
            play.Until(default, x => x.Act == null, 200);
            Assert.InRange((hop - lurch) * Dt, 0, 1.5);                                            // Teeter, then the hop back within 1.5 s
            Assert.Contains("dl19.settle", cues);
            Assert.Equal((Dl19LurchAct.BackX, 1.2), (s.X, s.Y));                                    // back on the terrace landing
            Assert.True(s.Grounded);
            Assert.Equal(onStops ? HalfLandingState.OnStops : HalfLandingState.Drooping, Landing(s).State);

            // Settle never changes jump distance: his next running jump is the jump of a D-17 who never stepped on it.
            var control = Begin();
            if (onStops) control.Graph.Restore(Mech.Snapshot(s.Graph));
            control.Motor.Place(Dl19LurchAct.BackX, 1.2, +1);
            for (int i = 0; i < 90; i++)
            {
                var input = new MotorInput { Move = -1, JumpPressed = i == 20 };
                s.Step(input);
                control.Step(input);
                Assert.Equal(control.X, s.X, 12);
                Assert.Equal(control.Y, s.Y, 12);
            }
        }

        // ---- The tell, recovery (§10) --------------------------------------------------------------------------------------

        [Fact]
        public void TheTell_WhenTheMarksMeet_TheCreakStopsAndTheRattleStartsWithin0_2s()
        {
            var s = Begin();
            var play = new Play(s);
            play.MoveJack(+1);
            int k = 0, meet = -1, rattle = -1, creakStops = -1;
            play.Each = x =>
            {
                k++;
                if (meet < 0 && Landing(x).MarksMeet) meet = k;
                if (rattle < 0 && Pins(x).Sound == PinSound.Rattle) rattle = k;
                if (creakStops < 0 && k > 1 && Pins(x).Sound != PinSound.Creak) creakStops = k;
            };
            Assert.Equal(PinSound.Creak, Pins(s).Sound);
            play.Crank(false, x => Landing(x).MarksMeet && Pins(x).Sound == PinSound.Rattle);
            Assert.True(meet > 0 && rattle > 0);
            Assert.InRange((rattle - meet) * Dt, 0, 0.2);
            Assert.InRange((creakStops - meet) * Dt, 0, 0.2);
        }

        [Fact]
        public void Recovery_FromTheStops_ReJackedToLevelInUnder8s()
        {
            var s = Begin();
            var play = new Play(s);
            play.UsePins();                                                                        // pin first: on the stops
            play.Until(default, x => !x.Busy && x.Act == null, 200);
            Assert.Equal(HalfLandingState.OnStops, Landing(s).State);
            long from = s.Steps;
            play.MoveJack(+1);
            play.Crank(false, x => Landing(x).MarksMeet);
            Assert.InRange((s.Steps - from) * Dt, 0, 8);
        }

        // ---- Checkpoints: respawn and continue (§9) ------------------------------------------------------------------------

        [Fact]
        public void HalfLanding_TheJackAndEveryPinPersist_ThroughARespawnAndThroughTheSave_ACarriedSpareBackInItsClip()
        {
            var store = new MemorySaveStore();
            var s = Begin(store: store);
            var play = new Play(s);
            play.MoveJack(+1);
            play.Crank(false, x => Landing(x).MarksMeet);
            play.UsePins();                                                                        // the bent pin into the cup
            play.UsePins();                                                                        // the spare in his hands
            Assert.Equal(BracketPinsState.SpareCarried, Pins(s).State);
            double ext = Jack(s).Extension;
            s.Checkpoints.Flush();                                                                 // a quit writes what is held

            void Check(ChapterSim c)
            {
                Assert.Equal("half_landing", c.Checkpoints.Current.Name);
                Assert.Equal((362.0, 1.2), (c.X, c.Y));
                Assert.Equal(RatchetJackState.InPocket, Jack(c).State);
                Assert.Equal(ext, Jack(c).Extension, 12);
                Assert.Equal(BracketPinsState.ForkEmpty, Pins(c).State);                          // the spare back in its clip
                Assert.Equal(PinPlace.Cup, Pins(c).BentPin);
                Assert.Equal(PinPlace.Clip, Pins(c).SparePin);
                Assert.Equal(HalfLandingState.Level, Landing(c).State);
            }

            var c2 = new ChapterSim(ChapterDefs.SomeoneHome(), store: store);
            Assert.True(c2.Continue());
            Check(c2);
            s.Respawn();
            Check(s);
            play.Solve();                                                                          // and on from there
            Assert.Equal("repaired", s.Checkpoints.Current.Name);
        }

        [Fact]
        public void Repaired_RespawnAndContinue_ThePlatformPinned_TheJackInItsBay_HeOnTheUpperTerrace()
        {
            var store = new MemorySaveStore();
            var s = Begin(store: store);
            new Play(s).Solve();
            new Play(s).Until(Right, x => x.X > 374, 600);
            s.Checkpoints.Flush();
            void Check(ChapterSim c)
            {
                Assert.Equal("repaired", c.Checkpoints.Current.Name);
                Assert.Equal((371.0, 2.3), (c.X, c.Y));
                Assert.Equal((RatchetJackState.Parked, BracketPinsState.SpareSeated, HalfLandingState.Pinned), (Jack(c).State, Pins(c).State, Landing(c).State));
                Assert.True(Landing(c).Standable);
            }
            s.Respawn();
            Check(s);
            var c2 = new ChapterSim(ChapterDefs.SomeoneHome(), store: store);
            Assert.True(c2.Continue());
            Check(c2);
            Check(Begin("repaired"));                                                              // derived from the checkpoint alone
            new Play(c2).Until(Left, x => x.X < 364.0 && x.Grounded, 600);                         // back down onto the pinned half landing: no lurch
            Assert.Equal(1.75, c2.Y, 9);
            Assert.Null(c2.Act);
        }

        // ---- Every action of the solution has a stand point, with the jack in either detent -----------------------------

        /// <summary>Where D-17 comes to rest from (x, y): there, but on an unpinned half landing the lurch hops him back off it.</summary>
        private static Func<double, double, double> Stays(ChapterSim s)
            => (x, y) => Landing(s).Standable || double.IsNaN(Landing(s).TopAt(x)) || Math.Abs(y - Landing(s).TopAt(x)) > 0.06 ? x : Dl19LurchAct.BackX;

        public static IEnumerable<object[]> JackStates() => new[]
        {
            new object[] { "bay" }, new object[] { "bayOnStops" }, new object[] { "pocket" }, new object[] { "pocketLevel" },
            new object[] { "pocketTop" }, new object[] { "pocketForkEmpty" }, new object[] { "pocketSpareCarried" },
            new object[] { "pocketPinnedRaised" }, new object[] { "pocketPinnedDown" },
        };

        /// <summary>Plays the world into a named state (jack, pins, half landing), then stands him at 362.0.</summary>
        internal static ChapterSim Setup(string state)
        {
            var s = Begin();
            var p = new Play(s);
            switch (state)
            {
                case "bay": break;
                case "bayOnStops": p.UsePins(); break;
                case "pocket": p.MoveJack(+1); break;
                case "pocketOnStops": p.MoveJack(+1); p.UsePins(); break;
                case "pocketHeld": p.MoveJack(+1); p.Crank(false, x => Landing(x).Position > 1.62); break;
                case "pocketLevel": p.MoveJack(+1); p.Crank(false, x => Landing(x).MarksMeet); break;
                case "pocketTop": p.MoveJack(+1); p.Crank(false, x => Jack(x).Extension >= Jack(x).Params.Travel - 1e-9); break;
                case "pocketForkEmpty": p.MoveJack(+1); p.Crank(false, x => Landing(x).MarksMeet); p.UsePins(); break;
                case "pocketSpareCarried": p.MoveJack(+1); p.Crank(false, x => Landing(x).MarksMeet); p.UsePins(); p.UsePins(); break;
                case "pocketPinnedRaised": p.MoveJack(+1); p.Crank(false, x => Landing(x).MarksMeet); p.UsePins(); p.UsePins(); p.UsePins(); break;
                case "pocketPinnedDown":
                    p.MoveJack(+1); p.Crank(false, x => Landing(x).MarksMeet); p.UsePins(); p.UsePins(); p.UsePins();
                    p.Crank(true, x => Jack(x).Extension <= 0);
                    break;
                case "free":
                    p.WalkTo(Jack(s).X - Jack(s).Params.Gap);
                    p.Step(Tap);
                    p.Until(default, x => x.Motor.Hold == HoldKind.Push, 120);
                    p.Until(Right, x => Jack(x).X > 363.2);
                    p.Step(new MotorInput { JumpPressed = true });                                 // he lets go on the tracks
                    break;
                case "solved": p.Solve(); break;
                default: throw new ArgumentException(state);
            }
            p.Until(default, x => !x.Busy && x.Act == null && x.Motor.Hold == HoldKind.None, 200);
            if (state != "solved") s.Motor.Place(362.0, 1.2);
            s.Step(default);
            return s;
        }

        [Theory]
        [MemberData(nameof(JackStates))]
        public void Stations_EveryUseOfTheSolution_HasAStandPoint_FacingEitherWay_WithTheJackInEitherDetent(string state)
        {
            var s = Setup(state);
            var reach = new LaneReach(s, 361.0, 363.7, Stays(s));
            var r = reach.From(362.0);
            var jack = Jack(s);
            var wanted = new List<(string, IInteractable)>();
            if (jack.State == RatchetJackState.Parked) wanted.Add(("push bar", jack.Chassis));
            else { wanted.Add(("crank", jack)); wanted.Add(("push bar", jack.Chassis)); }
            if (Pins(s).State != BracketPinsState.SpareSeated) wanted.Add(("bracket", Pins(s)));
            foreach (var (name, target) in wanted)
                foreach (int facing in new[] { 1, -1 })
                    Assert.True(reach.Any(r, n => reach.CanStand(reach.X(n)) && reach.Answers(n, target, facing)),
                        state + ": no stand point for the " + name + " facing " + facing);
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
            new Play(a).Solve();
            new Play(b).Solve();
            Assert.Equal(a.Steps, b.Steps);
            Assert.Equal(State(a), State(b));
        }

        [Fact]
        public void RoundTrip_ASnapshotWithTheJackInItsPocket_RestoredThen60StepsOfCranking_Equals60StepsStraight()
        {
            var a = Begin();
            var play = new Play(a) { StopAt = x => Jack(x).State == RatchetJackState.InPocket && x.Motor.CanCapture && !x.Busy && x.Motor.Hold == HoldKind.None };
            play.Solve();
            Assert.Equal(RatchetJackState.InPocket, Jack(a).State);
            var graph = Mech.Snapshot(a.Graph);
            var motor = a.Motor.Capture();

            var b = Begin();
            b.Graph.Restore(graph);
            b.Motor.SetState(motor);
            b.Clock = a.Clock;
            Assert.Equal(State(a), State(b));
            for (int i = 0; i < 60; i++)
            {
                var input = i < 12 ? Left : new MotorInput { UsePressed = i == 12, UseHeld = true };
                a.Step(input);
                b.Step(input);
            }
            Assert.True(Jack(a).Extension > 0);                                                    // it cranked meanwhile
            a.Step(default); b.Step(default);
            a.Step(default); b.Step(default);
            Assert.Equal(State(a), State(b));
        }

        // ---- Curiosities (§6) ---------------------------------------------------------------------------------------------

        [Fact]
        public void TheDrip_AfterLingeringInDl18_TicksOnce_NotInABurst()
        {
            // #47 review: the drip's clock starts when the world is built, but DL-19's rules run only while it holds him.
            var s = Begin("terrace");
            for (int i = 0; i < 60 * 185; i++) s.Step(default);
            var at = new List<long>();
            for (int i = 0; i < 60 * 130 && at.Count < 3; i++)
            {
                s.Step(s.X < 362.5 ? Right : default);
                foreach (var c in s.Cues) if (c.Id == Dl19Rules.Drip) at.Add(s.Steps);
            }
            Assert.True(at.Count >= 2, "drips: " + at.Count);
            for (int i = 1; i < at.Count; i++) Assert.True((at[i] - at[i - 1]) * Dt >= Dl19Rules.DripSeconds - 1e-9, "drips at " + string.Join(",", at));
        }

        [Fact]
        public void Curiosities_TheDripTicksEveryMinute_ThePotACloseLookFromThePinnedHalfLanding()
        {
            var s = Begin("repaired");
            int drips = 0;
            for (int i = 0; i < 60 * 125; i++) { s.Step(default); foreach (var c in s.Cues) if (c.Id == Dl19Rules.Drip) drips++; }
            Assert.Equal(2, drips);

            s.Motor.Place(363.75, 1.75);
            s.Step(Tap);
            Assert.Equal(Dl19Rules.PotKind, s.SceneActKind);
            Assert.Contains(s.Cues, c => c.Id == Dl19Rules.PotLook);
            int steps = 1;
            while (s.Busy && steps < 400) { s.Step(default); steps++; }
            Assert.InRange(steps * Dt, Dl19Rules.LookSeconds - Dt, Dl19Rules.LookSeconds + 2 * Dt);

            var floor = Begin();
            floor.Motor.Place(363.4, 1.2);                                                         // not from the floor
            floor.Step(Tap);
            Assert.True(floor.SceneActKind.IsNone);
        }
    }
}
