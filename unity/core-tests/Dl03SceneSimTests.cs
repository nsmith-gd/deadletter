using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl03;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-03 as Core runs it (<see cref="Dl03Scene.Def"/> in a <see cref="SceneSim"/>): the rules the trace does not reach
    /// (the floor set-down and its refusal, the trolley's right-hand grip, the stop against the weight) and the checkpoints'
    /// worlds. L2239–L2287, L2329–L2348, L8025–L8030.
    /// </summary>
    public class Dl03SceneSimTests
    {
        private static readonly MotorInput Use = new MotorInput { UsePressed = true, UseHeld = true };

        private static SceneSim Begin(string cp)
        {
            var s = new SceneSim(Dl03Scene.Def());
            s.Begin(cp);
            return s;
        }

        private static void Run(SceneSim s, MotorInput input, int steps) { for (int i = 0; i < steps; i++) s.Step(input); }

        private static int Until(SceneSim s, MotorInput input, Func<SceneSim, bool> done, int max = 3000)
        {
            for (int i = 1; i <= max; i++) { s.Step(input); if (done(s)) return i; }
            throw new Xunit.Sdk.XunitException("never: x=" + s.X + " act=" + s.ActKind + ":" + s.ActPhase);
        }

        private static Pushable Trolley(SceneSim s) => s.Graph.Get<Pushable>("dl03.trolley");
        private static Dl03Weight Weight(SceneSim s) => s.Graph.Get<Dl03Weight>("dl03.weight");

        /// <summary>From weighroom (25.9, facing right): Use lifts the weight behind him at 25.62 (stand 25.91), until his hands hold it.</summary>
        private static SceneSim Lifted()
        {
            var s = Begin("weighroom");
            s.Step(Use);
            Until(s, default, x => x.Motor.Hold == HoldKind.Item);
            Assert.Equal(25.91, s.X, 12);
            Assert.Equal(Dl03WeightState.Carried, Weight(s).State);
            return s;
        }

        [Theory]
        [InlineData("weighroom", 25.9, 27.55, Dl03WeightState.Floor, 0.0)]
        [InlineData("solved", 29.95, 29.175, Dl03WeightState.OnTrolley, 0.72)]
        [InlineData("bay", 29.95, 29.175, Dl03WeightState.OnTrolley, 0.72)]
        public void Begin_BuildsTheRoom_L8025_L8030(string cp, double x, double tx, Dl03WeightState ws, double load)
        {
            var s = Begin(cp == "bay" ? "solved" : cp);
            if (cp == "bay") s.Checkpoints.Load(new Save.SaveModel { Checkpoint = "bay", Scene = Dl03Scene.Id });
            if (cp != "bay") Assert.Equal(x, s.X, 12);
            Assert.Equal(tx, Trolley(s).X, 12);
            Assert.Equal(ws, Weight(s).State);
            Assert.Equal(load, s.Graph.Get<LoadPlate>("dl03.plate").Load, 12);
            Assert.Equal(load * 1.2, s.Graph.Get<FollowerActuator>("dl03.gate").Position, 12);
            if (ws == Dl03WeightState.OnTrolley) Assert.Equal(29.175 - 0.12, Weight(s).X, 12);
            Run(s, default, 120);
            Assert.Equal(load * 1.2, s.Graph.Get<FollowerActuator>("dl03.gate").Position, 12);
        }

        /// <summary>Set down on clear floor, GRIP_FWD in front of him; he stands still meanwhile; f14 it is down, f35 his hands are free (L2265–L2287).</summary>
        [Fact]
        public void SetDown_OnClearFloor_InFrontOfHim_L2265_L2284()
        {
            var s = Lifted();
            Until(s, new MotorInput { Move = 1 }, z => z.X >= 26.4);
            Until(s, default, z => z.Motor.Vx == 0);
            double x = s.X;
            s.Step(Use);
            Assert.Equal("dl03.weight", s.ActKind);
            Assert.Equal("SetDown", s.ActPhase);
            int n = Until(s, default, z => z.Act == null);
            Assert.Equal(88, n);                                                // f35 = 87.5 steps after the Use step
            Assert.Equal(x, s.X, 12);
            Assert.Equal(HoldKind.None, s.Motor.Hold);
            Assert.Equal(Dl03WeightState.Floor, Weight(s).State);
            Assert.Equal(x + 0.29, Weight(s).X, 12);
            Assert.Equal(0.22, s.Lane.SurfaceAt(x + 0.29), 12);                // something to climb again
        }

        /// <summary>Neither on the deck nor clear of the trolley: he will not put it down (<c>Sound.worried</c>, L2266–L2267).</summary>
        [Fact]
        public void SetDown_Refused_AgainstTheTrolleysEnd_L2266()
        {
            var s = Lifted();
            Until(s, new MotorInput { Move = 1 }, z => z.X >= 26.88);
            Until(s, default, z => z.Motor.Vx == 0);
            double tx = s.X + 0.29;
            Assert.InRange(Math.Abs(tx - 27.55), 0.30 + 1e-9, 0.39);
            s.Step(Use);
            Assert.Null(s.Act);
            Assert.Contains("sound:worried", s.Cues);
            Assert.Equal(HoldKind.Item, s.Motor.Hold);
            Assert.Equal(Dl03WeightState.Carried, Weight(s).State);
        }

        /// <summary>Onto the deck: within 0.30 of its centre, at most 0.17 off it; then the trolley carries it (L2264, L2269, L2284).</summary>
        [Fact]
        public void SetDown_OntoTheDeck_ClampedTo017_ThenItRides_L2269()
        {
            var s = Lifted();
            Until(s, new MotorInput { Move = 1 }, z => z.X >= 26.98);
            Until(s, default, z => z.Motor.Vx == 0);
            double off = Math.Max(-0.17, s.X + 0.29 - 27.55);
            s.Step(Use);
            Assert.Equal("SetDownHigh", s.ActPhase);
            Until(s, default, z => z.Act == null);
            Assert.Equal(Dl03WeightState.OnTrolley, Weight(s).State);
            Assert.Equal(off, Weight(s).Offset, 12);
            Assert.Equal(0.16 + 0.22, s.Lane.SurfaceAt(27.55 + off), 12);
            Assert.Equal(0.42, Trolley(s).Speed);
        }

        /// <summary>
        /// grabR: the twin face. He takes the bar at the right end (0.62 right of its centre) and pushes it left; it stops
        /// 0.39 short of the weight on the floor (L2256, L2345).
        /// </summary>
        [Fact]
        public void GrabR_PushesItLeft_UntilItStopsAgainstTheWeight_L2256_L2345()
        {
            var s = Begin("weighroom");
            s.Handover("weighroom", 28.2, 0, -1);
            s.Step(Use);
            Assert.Equal("Grab", s.ActKind);                                  // the twin is not a mechanism: the motor names the verb
            Until(s, default, z => z.Motor.Hold == HoldKind.Push);
            Assert.Equal(27.55 + 0.62, s.X, 12);
            Assert.Equal(-1, s.Motor.Pushed.Side);
            Until(s, new MotorInput { Move = -1 }, z => Trolley(z).X <= 25.62 + 0.39 + 1e-9, 1200);
            Run(s, new MotorInput { Move = -1 }, 30);
            Assert.Equal(25.62 + 0.39, Trolley(s).X, 12);
            Assert.Equal(HoldKind.Push, s.Motor.Hold);                         // pushing towards Min: the motor keeps hold
            Assert.Equal(25.62 + 0.39 + 0.62, s.X, 12);
        }

        /// <summary>Pushed right into the weight standing on the floor, the trolley stops 0.39 short of it (L2344).</summary>
        [Fact]
        public void GrabL_PushedIntoTheWeight_StopsShortOfIt_L2344()
        {
            var s = PushedIntoTheWeight();
            Assert.Equal(Weight(s).X - 0.39, Trolley(s).X, 12);
            Assert.Equal(Dl03WeightState.Floor, Weight(s).State);
        }

        /// <summary>
        /// M6 (#22, fixed in #25 by <c>IPushable.LetGoAtMax</c>): DL-03's trolley is an old hold (updateHold, L2341–L2349):
        /// it stops at the weight, or at TROLLEY_MAX, and he keeps hold, so he can pull it back without grabbing again.
        /// </summary>
        [Fact]
        public void GrabL_KeepsHoldAtTheStop_L2341()
        {
            var s = PushedIntoTheWeight();
            Assert.Equal(HoldKind.Push, s.Motor.Hold);
        }

        private static SceneSim PushedIntoTheWeight()
        {
            // The weight on the floor beyond the trolley (he cannot carry it past the trolley: set it there directly).
            var s = Begin("weighroom");
            var w = Weight(s);
            w.OnLifted(); s.Step(default);
            w.OnSetDown(28.6, 0); s.Step(default);
            Assert.Equal(Dl03WeightState.Floor, w.State);
            double wx = w.X;
            Until(s, new MotorInput { Move = 1 }, z => z.X >= 26.8);
            Until(s, default, z => z.Motor.Vx == 0);
            s.Step(Use);
            Until(s, default, z => z.Motor.Hold == HoldKind.Push);
            Assert.Equal(26.93, s.X, 12);
            Until(s, new MotorInput { Move = 1 }, z => Trolley(z).X >= wx - 0.39 - 1e-9 || z.Motor.Hold != HoldKind.Push, 1200);
            Run(s, new MotorInput { Move = 1 }, 30);
            return s;
        }
    }
}
