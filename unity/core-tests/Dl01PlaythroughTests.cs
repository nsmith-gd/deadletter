using System;
using System.Collections.Generic;
using System.Linq;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Prologue;
using Xunit;
using Xunit.Abstractions;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// A scripted first-time-but-competent player for DL-01, the Core port of <c>tools/sim/bot.js</c>'s <c>wake()</c> in
    /// mechanical mode (L115–L160 of bot.js: the latch, the step, the cart into the trench, the crank, out). It decides
    /// each step's <see cref="MotorInput"/> from Core state only, so it can start from any checkpoint. Like the bot it
    /// hops when it has stood still against something (bot.js <c>walk</c>, L33–L48), and presses Use when the game
    /// offers the thing it wants (<c>useAt</c>, L50–L61).
    /// </summary>
    internal sealed class Dl01Bot
    {
        private readonly SceneRunner _r;
        private readonly Latch _latch;
        private readonly TippingBridge _cart;
        private readonly CrankActuator _crank;
        private readonly Door _door;
        private double _lastX = double.NaN;
        private int _still;
        private bool _usedLast;

        /// <summary>Steps stood still before hopping (bot.js mechanical <c>react()</c> = 0.12 s).</summary>
        public const int HopAfter = 8;

        public Dl01Bot(SceneRunner r)
        {
            _r = r;
            _latch = r.Graph.Get<Latch>(Dl01Wake.LatchId);
            _cart = r.Graph.Get<TippingBridge>(Dl01Wake.CartId);
            _crank = r.Graph.Get<CrankActuator>(Dl01Wake.CrankId);
            _door = r.Graph.Get<Door>(Dl01Wake.DoorId);
        }

        public string Goal { get; private set; }

        public MotorInput Next()
        {
            D17Motor m = _r.Motor;
            if (_r.InOpening || _r.RespawnPending) { Goal = "wait"; return Sim.Move(1); }   // holding right: the gate must ignore it
            if (m.Hold == HoldKind.Push) { Goal = "push the cart"; return Sim.Move(1); }    // to the lip and on: the shove tips it (L4686)
            if (m.IsActing || m.IsMantling) { _usedLast = false; return Sim.Move(0); }
            if (_latch.State == LatchState.Locked) return UseOr(_latch, 3.0, "latch");
            if (_cart.State == TippingBridgeState.Falling) { Goal = "watch the cart"; return Sim.Move(0); }
            if (_cart.State != TippingBridgeState.Bridge) return UseOr(_cart, 5.9 - 0.97, "cart");
            if (!_door.Engaged) return UseOr(_crank, 9.62, "crank");
            Goal = "through the door";
            return Walk(+1);
        }

        private MotorInput UseOr(object target, double x, string goal)
        {
            Goal = goal;
            if (!_usedLast && _r.Motor.PreviewUse(out var c) && ReferenceEquals(c.Target, target))
            {
                _usedLast = true;
                return Sim.Use();
            }
            _usedLast = false;
            return Walk(Math.Abs(x - _r.Motor.X) < 0.02 ? 0 : Math.Sign(x - _r.Motor.X));
        }

        private MotorInput Walk(int dir)
        {
            D17Motor m = _r.Motor;
            bool moved = double.IsNaN(_lastX) || Math.Abs(m.X - _lastX) > 0.0008;
            _lastX = m.X;
            _still = !moved && dir != 0 && m.Grounded ? _still + 1 : 0;
            if (_still > HopAfter) { _still = 0; return Sim.Jump(dir); }
            return Sim.Move(dir);
        }
    }

    /// <summary>
    /// DL-01 played headless through <see cref="SceneRunner"/> with the real definition (<see cref="Dl01Wake"/>), motor,
    /// lane, mechanisms, checkpoints and camera: DL-01 §8 test 1 ("a recorded input replay that completes the scene")
    /// and test 2 ("save, quit and reload at both checkpoints"), §9 "Recovery". The mechanisms' own rules and timings
    /// are <see cref="Dl01SceneTests"/>' (U-10); this file checks the scene as a whole.
    /// </summary>
    public class Dl01PlaythroughTests
    {
        private readonly ITestOutputHelper _out;
        public Dl01PlaythroughTests(ITestOutputHelper output) { _out = output; }

        /// <summary>One play of the scene with a log of every beat (step: what happened).</summary>
        private sealed class Play
        {
            public readonly MemoryFileSystem Fs;
            public readonly SceneRunner R;
            public readonly Dl01Bot Bot;
            public readonly List<(int step, string beat)> Beats = new List<(int, string)>();
            public readonly List<(string cp, byte[] save, string dump)> Saves = new List<(string, byte[], string)>();
            public int Steps;

            public Play(MemoryFileSystem fs = null)
            {
                Fs = fs ?? new MemoryFileSystem();
                R = new SceneRunner(new Dl01Wake(), new AtomicFileStore(Fs));
                Bot = new Dl01Bot(R);
            }

            public void NewGame(bool opening = true)
            {
                R.NewGame(opening);
                Saves.Add((R.Checkpoint, (byte[])Fs.Files["slot0.dls"].Clone(), SaveKit.Dump(R.Checkpoints.CheckpointSnapshot)));
            }

            public void Step(MotorInput input)
            {
                Steps++;
                R.Step(input);
                foreach (var c in R.CuesThisStep) Beats.Add((Steps, "cue " + c));
                if (R.ControlReturnedThisStep) Beats.Add((Steps, "control"));
                if (R.ReachedThisStep != null)
                {
                    Beats.Add((Steps, "checkpoint " + R.ReachedThisStep));
                    Saves.Add((R.ReachedThisStep, (byte[])Fs.Files["slot0.dls"].Clone(), SaveKit.Dump(R.Checkpoints.CheckpointSnapshot)));
                }
                if (R.RespawnedThisStep) Beats.Add((Steps, "respawn"));
                if (R.ExitedThisStep) Beats.Add((Steps, "exit"));
                foreach (var e in R.Motor.Events)
                    if (e.Kind == MotorEventKind.Jump || e.Kind == MotorEventKind.MantleStart || e.Kind == MotorEventKind.Released)
                        Beats.Add((Steps, "motor " + e.Kind));
                for (int i = 0; i < R.Graph.Log.Count; i++)
                {
                    var e = R.Graph.Log[i];
                    if (e.Kind != MechanismEventKind.State || e.Id == Dl01Wake.RelayId || e.Id == Dl01Wake.ScaleId) continue;
                    Beats.Add((Steps, e.Id.Value + " " + StateName(e)));
                }
            }

            /// <summary>Plays the bot until <paramref name="done"/>; fails with the bot's goal if it takes more than <paramref name="max"/> steps.</summary>
            public int Until(Func<bool> done, int max = 60 * 120)
            {
                int start = Steps;
                while (!done())
                {
                    if (Steps - start >= max) throw new Xunit.Sdk.XunitException("stuck: " + Bot.Goal + " at x=" + R.Motor.X.ToString("F3") + " y=" + R.Motor.Y.ToString("F3") + " after " + max + " steps");
                    Step(Bot.Next());
                }
                return Steps - start;
            }

            public int At(string beat) => Beats.FindIndex(b => b.beat == beat) is int i && i >= 0 ? Beats[i].step : -1;

            private static string StateName(MechanismEvent e)
            {
                if (e.Id == Dl01Wake.LatchId) return ((LatchState)e.Code).ToString();
                if (e.Id == Dl01Wake.ShutterId || e.Id == Dl01Wake.DoorId) return ((DoorState)e.Code).ToString();
                if (e.Id == Dl01Wake.CrankId) return ((CrankState)e.Code).ToString();
                if (e.Id == Dl01Wake.CartId) return ((TippingBridgeState)e.Code).ToString();
                return e.Code.ToString();
            }
        }

        [Fact]
        public void TheWake_FromTheOpeningToTheDoor_EveryBeatInOrder()
        {
            var p = new Play();
            p.NewGame(opening: true);
            Assert.True(p.R.InOpening);
            Assert.Equal("start", p.R.Checkpoint);

            // The opening (L8503–L8507): 480 frames; the bot holds right throughout and nothing moves him.
            int opening = p.Until(() => !p.R.InOpening, 1300);
            Assert.InRange(opening, 1200, 1201);                                     // control by 0:20 (DL-01 §9), L269
            Assert.Equal(1, p.At("cue wake"));                                        // Music.play('wake'), L8068
            Assert.Equal(opening, p.At("control"));
            Assert.Equal(Dl01Wake.StartX, p.R.Motor.X);                               // the gate held him at the cradle
            p.Beats.Clear();
            var relay = p.R.Graph.Get<PulseSequencer>(Dl01Wake.RelayId);
            Assert.True(relay.Units >= 480 - 1e-6 && relay.Units < 481, "the relay ran the opening's sets from frame 0 (L8061)");

            // Play: the latch, the shutter, the step, the cart, the trench, the crank, the door.
            int play = p.Until(() => p.R.Exited);
            foreach (var b in p.Beats) _out.WriteLine(b.step + "\t" + b.beat);
            double seconds = play * SceneRunner.StepSeconds;
            _out.WriteLine("play " + seconds.ToString("F1") + " s");

            string[] order =
            {
                "dl01.latch Released", "dl01.shutter Opening", "dl01.shutter Open",
                "motor Jump",                                                          // the fallen conveyor (0.22): a hop, L281
                "dl01.cart AtLip", "motor Released", "dl01.cart Falling", "dl01.cart Bridge",
                "cue hall", "motor MantleStart", "checkpoint hall",                    // out of the trench onto the hall floor (0.25)
                "dl01.crank Cranking", "dl01.door Open", "dl01.crank Done",
                "exit",
            };
            int last = 0;
            foreach (string beat in order)
            {
                int at = p.At(beat);
                Assert.True(at >= last, "missing or out of order: " + beat);
                last = at;
            }
            Assert.Equal(p.At("dl01.latch Released"), p.At("checkpoint shutter"));     // set by release(), L1677
            Assert.Equal(p.At("dl01.door Open"), p.At("checkpoint door"));             // the last stroke opens it, L1890
            Assert.Equal(p.At("checkpoint door"), p.At("cue threshold"));
            Assert.Equal(p.At("dl01.cart Falling"), p.At("motor Released"));           // the shove tips it, L4686
            Assert.Equal(-1, p.At("respawn"));                                        // no failure on the intended route (§9)
            Assert.True(p.At("motor MantleStart") > p.At("dl01.cart Bridge"));
            Assert.InRange(seconds, 20, 120);                                         // a competent run is well inside 2 min (DL-01 header)

            // Where he ends: in the doorway, the door up a metre, every mechanism solved.
            Assert.InRange(p.R.Motor.X, Dl01Wake.DoorX0 + 0.15, Dl01Wake.DoorX1 - 0.15);
            Assert.Equal(1.0, p.R.Graph.Get<Door>(Dl01Wake.DoorId).Position);
            Assert.Equal("door", p.R.Checkpoint);
            Assert.Equal("DL-02", p.R.Definition.Exit.NextScene);
            Assert.Equal(new[] { "start", "shutter", "hall", "door" }, p.Saves.Select(s => s.cp));
        }

        [Fact]
        public void TheShutter_HoldsHimCrouchedAndShut_UntilTheLatch_L1764_L1975()
        {
            var p = new Play();
            p.NewGame(opening: false);
            bool crouched = false;
            for (int i = 0; i < 600; i++)
            {
                p.Step(Sim.Move(1));
                crouched |= p.R.Motor.Crouched;
                Assert.True(p.R.Motor.X <= Dl01Wake.LockedLimit + 1e-9);
            }
            Assert.True(crouched, "the shutter's underside (0.6) crouches him");
            Assert.Equal(Dl01Wake.LockedLimit, p.R.Motor.X, 9);
            Assert.True(p.R.Motor.PreviewUse(out var c));
            Assert.IsType<Latch>(c.Target);
        }

        [Fact]
        public void SaveAtEachCheckpoint_ThenContinueInAFreshGame_ReachesTheExit()
        {
            var p = new Play();
            p.NewGame(opening: false);
            p.Until(() => p.R.Exited);
            Assert.Equal(new[] { "start", "shutter", "hall", "door" }, p.Saves.Select(s => s.cp));

            foreach (var (cp, save, dump) in p.Saves)
            {
                var fs = new MemoryFileSystem();
                fs.Files["slot0.dls"] = (byte[])save.Clone();
                var q = new Play(fs);
                Assert.True(q.R.Continue(), cp);
                Assert.Equal(cp, q.R.Checkpoint);
                Assert.True(q.R.Checkpoints.RestoredSnapshot);
                Assert.Equal(dump, SaveKit.Dump(q.R.Graph));                         // the exact state at the checkpoint (§9 Recovery)
                SpawnPoint spawn = q.R.Definition.SpawnFor(cp);
                Assert.Equal(spawn.X, q.R.Motor.X);
                Assert.Equal(spawn.Y, q.R.Motor.Y);
                Assert.False(q.R.InOpening);                                          // continuing never replays the opening

                q.Until(() => q.R.Exited);
                Assert.Equal("door", q.R.Checkpoint);
                Assert.Equal(-1, q.At("respawn"));
                _out.WriteLine(cp + ": exit after " + (q.Steps * SceneRunner.StepSeconds).ToString("F1") + " s");
            }
        }

        [Fact]
        public void TwoPlaythroughs_WithTheSameInputs_AreBitIdentical()
        {
            List<string> Run()
            {
                var p = new Play();
                p.NewGame(opening: true);
                var trace = new List<string>();
                while (!p.R.Exited && p.Steps < 60 * 150)
                {
                    p.Step(p.Bot.Next());
                    var cam = p.R.Camera.Pose;
                    trace.Add(Sim.Snapshot(p.R.Motor) + "#" + Mech.Dump(p.R.Graph) + "#" + cam.Position.X.ToString("R") + ","
                        + cam.Position.Y.ToString("R") + "," + cam.Position.Z.ToString("R") + "," + cam.Focal.ToString("R")
                        + "#" + string.Join(",", p.R.CuesThisStep) + "#" + p.R.ReachedThisStep);
                }
                Assert.True(p.R.Exited);
                return trace;
            }
            var a = Run();
            var b = Run();
            Assert.Equal(a.Count, b.Count);
            for (int i = 0; i < a.Count; i++) Assert.True(a[i] == b[i], "diverged at step " + (i + 1));
        }

        [Fact]
        public void IntoTheTrenchWithoutTheCart_HeIsStuck_ThenRespawnsAtTheCheckpoint_L4765_L4519_L2998()
        {
            var p = new Play();
            p.NewGame(opening: false);
            // To the shutter and through it (the bot), then over the cart and off its far end.
            p.Until(() => p.R.Checkpoint == "shutter" && !p.R.Motor.IsActing);
            int stillSteps = 0;
            double lastX = p.R.Motor.X;
            int stuck = -1;
            for (int i = 0; i < 60 * 30 && stuck < 0; i++)
            {
                bool still = Math.Abs(p.R.Motor.X - lastX) < 0.0008 && p.R.Motor.Grounded;
                lastX = p.R.Motor.X;
                stillSteps = still ? stillSteps + 1 : 0;
                p.Step(stillSteps > Dl01Bot.HopAfter ? Sim.Jump(1) : Sim.Move(1));
                if (stillSteps > Dl01Bot.HopAfter) stillSteps = 0;
                if (p.R.RespawnPending) stuck = p.Steps;
            }
            Assert.True(stuck > 0, "he never got stuck in the trench");
            Assert.True(p.R.Motor.Y < Dl01Wake.PitY + 0.05);
            Assert.Equal(TippingBridgeState.Free, p.R.Graph.Get<TippingBridge>(Dl01Wake.CartId).State);
            Assert.True(p.At("motor MantleStart") > 0, "he climbed the cart (0.55)");

            double x = p.R.Motor.X;
            int respawn = -1;
            for (int i = 0; i < 400 && respawn < 0; i++)
            {
                p.Step(Sim.Move(1));
                if (p.R.RespawnedThisStep) respawn = p.Steps;
                else Assert.Equal(x, p.R.Motor.X);                                   // no control while stuck (the act)
            }
            Assert.Equal(198, respawn - stuck);                                       // 2.0 s stuck + 1.3 s fade = 3.3 s
            Assert.Equal("shutter", p.R.Checkpoint);
            Assert.InRange(p.R.Motor.X, 2.9, 2.9 + 1.6 / 60);                       // CHECKPOINTS.shutter (L7977), then that step's move (L8494)
            Assert.Equal(LatchState.Released, p.R.Graph.Get<Latch>(Dl01Wake.LatchId).State);

            // And the scene can still be finished from there.
            p.Until(() => p.R.Exited);
        }

        [Fact]
        public void SkippingTheOpening_HandsControlOverAtOnce_L8071()
        {
            var p = new Play();
            p.NewGame(opening: true);
            for (int i = 0; i < 90; i++) p.Step(Sim.Move(1));
            Assert.Equal(Dl01Wake.StartX, p.R.Motor.X);
            p.R.SkipOpening();
            Assert.False(p.R.InOpening);
            for (int i = 0; i < 30; i++) p.Step(Sim.Move(1));
            Assert.True(p.R.Motor.X > Dl01Wake.StartX + 0.1);
        }

        [Fact]
        public void TheStep_IsAllocationFree_OnAStepThatReachesNoCheckpoint()
        {
            var p = new Play();
            p.NewGame(opening: false);
            p.Until(() => p.R.Checkpoint == "hall");
            for (int i = 0; i < 120; i++) p.R.Step(Sim.Move(-1));                     // warm up every path once
            for (int i = 0; i < 120; i++) p.R.Step(Sim.Move(1));
            long before = GC.GetAllocatedBytesForCurrentThread();
            for (int i = 0; i < 240; i++) p.R.Step(i < 120 ? Sim.Move(-1) : Sim.Move(1));   // walking, the camera following, the relay pulsing
            long after = GC.GetAllocatedBytesForCurrentThread();
            Assert.Equal(0, after - before);
        }
    }

    /// <summary>The DL-01 definition itself: lane parity with index.html, and its views against the art's names.</summary>
    public class Dl01DefinitionTests
    {
        private static SceneRunner Runner(string cp = "start")
        {
            var fs = new MemoryFileSystem();
            new AtomicFileStore(fs).Save(0, new SaveModel { Checkpoint = cp, Scene = Dl01Wake.SceneId });
            var r = new SceneRunner(new Dl01Wake(), new AtomicFileStore(fs));
            Assert.True(r.Continue());
            return r;
        }

        [Theory]
        // x, closed ceiling (ceilingAt with shutterAngle 0, L1630–L1641), ground (floorAt/surfaceAt, L1712–L1726, L4146)
        [InlineData(0.1, 2.45, 0.0)]                              // left of the pivot: the alcove's 2.45, L1632
        [InlineData(1.0, 1.1644444444444444, 0.0)]                // the path's first segment, (0.2, 1.6) → (2.0, 0.62)
        [InlineData(2.6, 0.61, 0.0)]                              // its second, (2.0, 0.62) → (3.2, 0.6): crouch height
        [InlineData(3.3, 0.31, 0.0)]                              // the foot, (3.2, 0.6) → (3.4, 0.02)
        [InlineData(4.0, 4.0, 0.22)]                              // STEP, L281
        [InlineData(5.9, 4.0, 0.55)]                              // the cart, free (CART1, L3885)
        [InlineData(7.3, 4.0, -0.8)]                              // PIT, L283
        [InlineData(9.0, 4.0, 0.0)]
        public void TheLaneAtStart_MatchesThePrototype(double x, double ceiling, double ground)
        {
            var r = Runner();
            Assert.Equal(ceiling, r.Lane.CeilingAt(x, 0), 9);
            Assert.Equal(ground, r.Lane.SurfaceAt(x, 0), 9);
            r.Lane.Limits(x, 0, out double left, out double right);
            Assert.Equal(-0.3, left);
            Assert.Equal(3.02, right);                                              // LOCKED_LIMIT until released, L1764
        }

        [Fact]
        public void PastTheHall_TheShutterIsUp_TheWallIsGone_AndTheCartBridgesTheTrench()
        {
            var r = Runner("hall");
            Assert.True(r.Lane.CeilingAt(3.3, 0) > 0.76, "15° up: he walks under (L277)");
            Assert.Equal(-0.25, r.Lane.SurfaceAt(7.3, 0), 9);                       // PIT.y + CART1.h, L4140
            Assert.Equal(0.0, r.Lane.SurfaceAt(5.9, 0), 9);                         // the cart is no longer on the floor
            r.Lane.Limits(5, 0, out _, out double right);
            Assert.Equal(11.45, right);
            Assert.Equal(8.35, r.Motor.X);
        }

        /// <summary>The MECH_ names docs/unity/name_map.csv gives DL-01 on PR #24 (U-12), which the SceneBuilder binds to.</summary>
        private static readonly string[] ArtNodes =
        {
            "MECH_TippingBridge_dl01_cart", "MECH_CrankActuator_dl01_crank", "MECH_Door_dl01_door", "MECH_Latch_dl01_latch",
            "MECH_Latch_dl01_latch__LatchTag", "MECH_PulseSequencer_dl01_relay", "MECH_PulseSequencer_dl01_relay__RelayLamp0",
            "MECH_PulseSequencer_dl01_relay__RelayLamp1", "MECH_PulseSequencer_dl01_relay__RelayLamp2", "MECH_LoadPlate_dl01_scale",
            "MECH_LoadPlate_dl01_scale__ScaleNeedle", "MECH_Door_dl01_shutter", "MECH_Door_dl01_shutter__Counterweight",
            "MECH_Door_dl01_shutter__CounterweightStripes", "MECH_Door_dl01_shutter__Pulley", "MECH_Door_dl01_shutter__ShutterRail",
        };

        [Fact]
        public void EveryView_NamesAnArtNode_AndReadsItsMechanism()
        {
            var r = Runner();
            foreach (var v in r.Definition.Views)
            {
                Assert.Contains(v.NodeName, ArtNodes);
                Assert.True(r.Graph.TryGet<IMechanism>(v.ReadFrom, out var m), v.NodeName);
                Assert.Equal(v.Type, r.Graph.Get<IMechanism>(v.Node).GetType().Name);   // MECH_<Type> is the Core class (asset_conventions)
                Assert.True(MechanismReadout.Supports(m, v.Channel), v.NodeName + " " + v.Channel);
                double value = MechanismReadout.Apply(v, m);
                Assert.False(double.IsNaN(value));
            }
        }

        [Fact]
        public void TheViews_AtRest_LeaveTheArtWhereItWasBuilt_AndSolved_MoveIt()
        {
            double Value(SceneRunner r, string node, ViewChannel ch)
            {
                var v = r.Definition.Views.First(d => d.NodeName == node && d.Channel == ch);
                return MechanismReadout.Apply(v, r.Graph.Get<IMechanism>(v.ReadFrom));
            }
            var start = Runner("start");
            Assert.Equal(0, Value(start, "MECH_Door_dl01_shutter", ViewChannel.Position));
            Assert.Equal(0, Value(start, "MECH_Door_dl01_shutter__Counterweight", ViewChannel.ShutterCounterweightY), 12);
            Assert.Equal(0, Value(start, "MECH_TippingBridge_dl01_cart", ViewChannel.BridgeX), 12);
            Assert.Equal(0, Value(start, "MECH_Door_dl01_door", ViewChannel.Position));
            var done = Runner("door");
            Assert.Equal(15, Value(done, "MECH_Door_dl01_shutter", ViewChannel.Position));
            Assert.Equal(0.12 - 1.56, Value(done, "MECH_Door_dl01_shutter__Counterweight", ViewChannel.ShutterCounterweightY), 12);
            Assert.Equal(6.6 + 0.65 + 0.02 - 5.9, Value(done, "MECH_TippingBridge_dl01_cart", ViewChannel.BridgeX), 12);
            Assert.Equal(-0.8, Value(done, "MECH_TippingBridge_dl01_cart", ViewChannel.BridgeY), 12);
            Assert.Equal(1.0, Value(done, "MECH_Door_dl01_door", ViewChannel.Position));
            Assert.Equal(-300, Value(done, "MECH_CrankActuator_dl01_crank", ViewChannel.WheelDeg));
        }

        [Fact]
        public void EveryCheckpointRule_HasASpawn_InTheScene()
        {
            var d = new Dl01Wake();
            foreach (var rule in d.CheckpointRules) Assert.True(d.HasSpawn(rule.Checkpoint), rule.Checkpoint);
            Assert.True(d.HasSpawn(d.FirstCheckpoint));
            Assert.Same(typeof(Dl01Wake), SceneCatalog.Create(Dl01Wake.SceneId).GetType());
        }
    }
}
