using System;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl01;
using DeadLetter.Core.Scenes.Dl02;
using DeadLetter.Core.Scenes.Dl03;
using DeadLetter.Core.Scenes.Dl04;
using DeadLetter.Core.Scenes.Dl05;
using DeadLetter.Core.Scenes.Dl06;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>Core/Scenes: <see cref="SceneSim"/> with DL-01's definition and rules, on its real lane.</summary>
    public class SceneSimTests
    {
        private static SceneSim Sim(string cp, bool fromOpening = false)
        {
            var s = new SceneSim(Dl01Scene.Def());
            s.Begin(cp, fromOpening);
            return s;
        }

        /// <summary>Walks right, hopping when he has stood still against something for 0.12 s (the bot's walk, bot.js).</summary>
        private static int WalkRight(SceneSim s, Func<SceneSim, bool> until, int max = 3000)
        {
            double last = s.X;
            int still = 0;
            for (int i = 1; i <= max; i++)
            {
                bool hop = still > 7;
                s.Step(new MotorInput { Move = 1, JumpPressed = hop, JumpHeld = hop });
                if (hop) still = 0;
                bool moved = Math.Abs(s.X - last) > 0.0008;
                last = s.X;
                still = !moved && s.Grounded && s.Act == null && !s.Motor.IsActing && !s.Motor.IsMantling ? still + 1 : 0;
                if (until(s)) return i;
            }
            return -1;
        }

        [Theory]
        [InlineData("start", 1.0, LatchState.Locked, TippingBridgeState.Free, CrankState.Idle)]
        [InlineData("shutter", 2.9, LatchState.Released, TippingBridgeState.Free, CrankState.Idle)]
        [InlineData("hall", 8.35, LatchState.Released, TippingBridgeState.Bridge, CrankState.Idle)]
        [InlineData("door", 9.62, LatchState.Released, TippingBridgeState.Bridge, CrankState.Done)]
        public void Begin_PlacesHimAndDerivesTheWorld_L7976_L8015(string cp, double x, LatchState latch, TippingBridgeState cart, CrankState crank)
        {
            var s = Sim(cp);
            Assert.Equal(x, s.X);
            Assert.Equal(0, s.Y);
            Assert.Equal(cp, s.Checkpoints.Current.Name);
            Assert.Equal(1, s.Region);
            Assert.Equal(latch, s.Graph.Get<Latch>("dl01.latch").State);
            Assert.Equal(cart, s.Graph.Get<TippingBridge>("dl01.cart").State);
            Assert.Equal(crank, s.Graph.Get<CrankActuator>("dl01.crank").State);
            Assert.Null(s.ActKind);
            Assert.Equal(3, s.Resolver.Registered.Count);                               // the latch, the crank and the cart: what he can use
            Assert.Throws<ArgumentException>(() => s.Begin("room"));                    // DL-02's
        }

        [Fact]
        public void TheLabelBeat_PlaysOnlyWhenPlayStartsFromTheOpening_L8107()
        {
            var a = Sim("start", fromOpening: true);
            a.Step(default);
            Assert.Equal("quirk", a.ActKind);
            Assert.Equal("CheckLabel", a.ActPhase);
            Assert.Contains("voice:dispatch_item", a.Cues);
            var b = Sim("start");
            b.Step(default);
            Assert.Null(b.ActKind);
            Assert.Empty(b.Cues);
        }

        [Fact]
        public void TheLabelBeat_HoldsHimUntilTheClipAndTheHold_ThenAMoveIsHis()
        {
            var s = Sim("start", fromOpening: true);
            s.Step(new MotorInput { Move = 1 });
            int steps = 1;
            while (s.ActKind == "quirk" && steps < 1000) { s.Step(new MotorInput { Move = 1 }); steps++; }
            // Not cancellable for 2.5 s, then any move ends it after 0.3 s of clip: the 151st step is 2.5 s on the game clock.
            Assert.InRange(steps, 151, 152);
            Assert.Equal(1.0, s.X, 12);                                                // he never moved while it played
            s.Step(new MotorInput { Move = 1 });
            Assert.True(s.X > 1.0);
        }

        [Fact]
        public void TheTrench_WithoutTheCart_StrandsHim_AndHeRespawnsAtTheCheckpoint_L4764_L4519_L2997()
        {
            var s = Sim("shutter");
            int n = WalkRight(s, x => x.ActKind == "dl01.trench");
            Assert.True(n > 0, "never stranded; x=" + s.X);
            Assert.InRange(s.X, 6.6 + 0.1, 8.0 - 0.1);
            Assert.Equal(-0.8, s.Y, 9);
            double x0 = s.X;
            int flinchAt = -1, respawnAt = -1;
            for (int i = 1; i <= 400 && respawnAt < 0; i++)
            {
                s.Step(new MotorInput { Move = 1 });
                if (flinchAt < 0 && s.ActPhase == "Flinch") flinchAt = i;
                if (s.ActKind == "dl01.trench") Assert.Equal(x0, s.X);                // he does not move meanwhile
                if (s.ActKind == null) respawnAt = i;
            }
            Assert.Equal(13, flinchAt);                                                 // t > 0.2 s: twelve sixtieths sum to 0.19999999999999998
            Assert.InRange(respawnAt, 120 + 78, 121 + 79);                              // t > 2.0 s, then respawnAt = clock + 1.3 s
            Assert.Equal(2.9 + 0.1 / 60, s.X, 9);                                     // respawned at 2.9 at #1, then a first step of his walk (#4)
            Assert.Equal("shutter", s.Checkpoints.Current.Name);
            Assert.Equal(TippingBridgeState.Free, s.Graph.Get<TippingBridge>("dl01.cart").State);
            Assert.Equal(LatchState.Released, s.Graph.Get<Latch>("dl01.latch").State);
        }

        [Fact]
        public void ThroughTheOpenDoor_ThePassageCarriesHimIntoDl02_L2040_L2129()
        {
            var s = Sim("door");
            int n = WalkRight(s, x => x.ActKind == "transit");
            Assert.True(n > 0);
            Assert.InRange(s.X, 10.15, 10.65);
            Assert.False(s.Exited);
            int exitAt = -1, endAt = -1;
            for (int i = 1; i <= 2000 && endAt < 0; i++)
            {
                s.Step(new MotorInput { Move = 1 });                                    // input is ignored: he walks himself
                if (exitAt < 0 && s.Exited) exitAt = i;
                if (s.ActKind == null) endAt = i;
            }
            Assert.True(exitAt > 0 && endAt > exitAt);
            Assert.Equal(2, s.Region);
            Assert.Equal("room", s.Checkpoints.Current.Name);
            Assert.Equal(13.2, s.X);
            Assert.Equal(0, s.Z);
            double x = s.X;
            s.Step(new MotorInput { Move = 1 });
            Assert.Equal(x, s.X);                                                      // DL-02's simulation takes him on from here
        }

        [Fact]
        public void Advance_StepsAt60Hz_WithTheExactPrototypeStep()
        {
            var s = Sim("start");
            double c0 = s.Clock;
            Assert.Equal(3, s.Advance(0.051, () => default));                          // FixedTick counts the steps (its step is 166,667 ticks)
            Assert.Equal(c0 + SceneSim.StepSeconds + SceneSim.StepSeconds + SceneSim.StepSeconds, s.Clock);   // each one exactly 1/60
            Assert.Equal(0, s.Advance(0.005, () => default));
            Assert.Equal(1, s.Advance(0.012, () => default));
            Assert.Equal(4, s.Steps);
        }

        // ---- The save across scenes (NewGame, Continue, Begin, Handover) --------------------------------------------------
        private static SaveModel Slot(MemorySaveStore store)
        {
            Assert.True(store.TryLoad(0, out var m));
            return m;
        }

        /// <summary>A game in the slot at <c>hall</c>: calm mode on, a curiosity found, the label beat seen, 12.5 s played.</summary>
        private static MemorySaveStore SavedAtHall()
        {
            var store = new MemorySaveStore();
            var a = new SceneSim(Dl01Scene.Def(), store: store);
            a.NewGame(fromOpening: true);
            a.Step(default);                                                            // the label beat: labelWake seen
            a.Checkpoints.ApplySettings(new Settings { Calm = true });
            a.Checkpoints.SetFlag(StoryFlags.Curio("cot"));
            a.Checkpoints.Update(12.5, playing: true);
            Assert.True(a.Checkpoints.Reach("hall"));
            return store;
        }

        [Fact]
        public void Begin_KeepsTheSlotsGame_AndWritesNothing_OnlyNewGameResetsIt()
        {
            var store = SavedAtHall();
            var bytes = (byte[])store.Slots[0].Clone();
            int writes = store.Writes;

            var b = new SceneSim(Dl01Scene.Def(), store: store);
            b.Begin("start", fromOpening: true);                                         // it used to be a new game, over the slot
            Assert.Equal(writes, store.Writes);
            Assert.Equal(bytes, store.Slots[0]);
            Assert.Equal("start", b.Checkpoints.Current.Name);
            Assert.Equal(1.0, b.X);
            Assert.True(b.Checkpoints.Settings.Calm);
            Assert.True(b.Graph.Calm);
            Assert.True(b.Checkpoints.Flags.Has(StoryFlags.Curio("cot")));
            Assert.Equal(12.5, b.Checkpoints.PlayTime);
            b.Step(default);
            Assert.Null(b.ActKind);                                                     // labelWake is seen: no label beat
            Assert.Equal(writes, store.Writes);

            b.Begin("door");                                                            // again: the game it holds goes on
            Assert.True(b.Checkpoints.Settings.Calm);
            Assert.True(b.Checkpoints.Reach("room"));                                   // the next save carries the game
            var m = Slot(store);
            Assert.Equal("room", m.Checkpoint);
            Assert.True(m.Settings.Calm);
            Assert.Contains(StoryFlags.Curio("cot"), m.Flags);
            Assert.Contains(Dl01Rules.LabelWake, m.Seen);

            b.NewGame();                                                                // Start over: the only reset
            m = Slot(store);
            Assert.Equal("start", m.Checkpoint);
            Assert.Empty(m.Flags);
            Assert.Empty(m.Seen);
            Assert.Equal(0, m.PlayTime);
            Assert.Throws<InvalidOperationException>(() => new SceneSim(Dl02Scene.Def()).NewGame());   // only DL-01 starts one
        }

        [Fact]
        public void Continue_PlacesHimAtTheSlotsCheckpoint_WithItsGame()
        {
            Assert.False(new SceneSim(Dl01Scene.Def(), store: new MemorySaveStore()).Continue());   // an empty slot
            var optionsOnly = new MemorySaveStore();
            optionsOnly.Save(0, new SaveModel { OptionsOnly = true, Settings = new Settings { Calm = true } });
            Assert.False(new SceneSim(Dl01Scene.Def(), store: optionsOnly).Continue());           // options only (#24)
            var store = SavedAtHall();
            int writes = store.Writes;
            var s = new SceneSim(Dl01Scene.Def(), store: store);
            Assert.True(s.Continue());
            Assert.Equal(writes, store.Writes);
            Assert.Equal("hall", s.Checkpoints.Current.Name);
            Assert.Equal(8.35, s.X);
            Assert.Equal(1, s.Region);
            Assert.True(s.Checkpoints.RestoredSnapshot);                                // saved in DL-01: its snapshot
            Assert.True(s.Checkpoints.Settings.Calm);
            Assert.True(s.Checkpoints.HasSeen(Dl01Rules.LabelWake));
            Assert.Equal(12.5, s.Checkpoints.PlayTime);
        }

        /// <summary>
        /// DL-01's passage ends at <c>room</c> and DL-02 takes him on: the previous scene's service carries the game (calm
        /// mode, flags, seen moments, play time) into the next one; the hand-over writes nothing, and a respawn keeps it.
        /// </summary>
        [Fact]
        public void Handover_CarriesTheGame_CalmModeIncluded_IntoTheNextScene()
        {
            var store = SavedAtHall();
            var a = new SceneSim(Dl01Scene.Def(), store: store);
            Assert.True(a.Continue());
            a.Checkpoints.MinSecondsBetweenWrites = 2;
            Assert.True(a.Checkpoints.Reach("room"));                                   // the passage's end (L2145); written
            a.Checkpoints.SetFlag(StoryFlags.Curio("scale"));
            Assert.True(a.Checkpoints.Pending);                                         // held by the rate limit
            int writes = store.Writes;

            var b = new SceneSim(Dl02Scene.Def(), store: store);
            b.Handover("room", 13.2, 0, 1, a.Checkpoints);
            Assert.False(a.Checkpoints.Pending);
            int after = store.Writes;
            Assert.Equal(writes + 1, after);                                            // the held write, flushed; nothing else
            Assert.Equal("room", b.Checkpoints.Current.Name);
            Assert.True(b.Checkpoints.Settings.Calm);
            Assert.True(b.Graph.Calm);
            Assert.True(b.Checkpoints.Flags.Has(StoryFlags.Curio("cot")));
            Assert.True(b.Checkpoints.Flags.Has(StoryFlags.Curio("scale")));
            Assert.True(b.Checkpoints.HasSeen(Dl01Rules.LabelWake));
            Assert.Equal(12.5, b.Checkpoints.PlayTime);
            b.Respawn();
            Assert.Equal(after, store.Writes);
            Assert.True(b.Checkpoints.Settings.Calm);
            Assert.True(b.Checkpoints.Flags.Has(StoryFlags.Curio("scale")));
            var m = Slot(store);
            Assert.True(m.Settings.Calm);
            Assert.Contains(StoryFlags.Curio("scale"), m.Flags);
        }

        // ---- The chapter's checkpoint table (PrologueCheckpoints) ----------------------------------------------------
        [Fact]
        public void TheTable_IsThePrologueInPlayOrder_AndEachSceneTakesItsOwnFromIt_L7975()
        {
            var all = PrologueCheckpoints.All;
            Assert.Equal(22, all.Count);
            for (int i = 0; i < all.Count; i++)
            {
                Assert.Equal(Mechanisms.Checkpoint.PrototypeOrder[i], all[i].Name);
                Assert.Equal(1, all[i].Facing);
                Assert.InRange(all[i].Region, 1, 5);
                Assert.StartsWith("DL-", all[i].Scene);
            }
            Assert.Equal("forwarded", all[all.Count - 1].Name);
            Assert.False(PrologueCheckpoints.TryGet("school", out _));                 // chapter 1's
            Assert.Equal(3.4, PrologueCheckpoints.Get("cage").Y);
            foreach (var def in new[] { Dl01Scene.Def(), Dl02Scene.Def(), Dl03Scene.Def(), Dl04Scene.Def(), Dl05Scene.Def(), Dl06Scene.Def() })
            {
                Assert.Equal(PrologueCheckpoints.Of(def.Id), def.Checkpoints);
                Assert.NotEmpty(def.Checkpoints);
            }
            Assert.Equal(new[] { "ration", "hatch" }, Array.ConvertAll(Dl05Scene.Def().Checkpoints, c => c.Name));   // bay is DL-04's
            Assert.Equal(Dl04Scene.BayX, PrologueCheckpoints.Get("bay").X);
            Assert.Equal(Dl06Scene.ScannedX, PrologueCheckpoints.Get("scanned").X);
        }

        /// <summary>Each scene respawns at the checkpoint it was walked into under, the previous scene's (L8494).</summary>
        [Theory]
        [InlineData("DL-03", "room", 25.45, 13.2)]
        [InlineData("DL-04", "solved", 30.0, 29.95)]
        [InlineData("DL-05", "bay", 47.95, 47.1)]
        public void Respawn_WorksAtThePreviousScenesCheckpoint(string scene, string cp, double x, double respawnX)
        {
            var def = scene == "DL-03" ? Dl03Scene.Def() : scene == "DL-04" ? Dl04Scene.Def() : Dl05Scene.Def();
            var s = new SceneSim(def);
            s.Handover(cp, x, 0);
            s.Respawn();
            Assert.Equal(cp, s.Checkpoints.Current.Name);
            Assert.Equal(respawnX, s.X, 12);
            Assert.Equal(2, s.Region);
        }
    }
}
