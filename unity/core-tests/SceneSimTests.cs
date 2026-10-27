using System;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl01;
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
    }
}
