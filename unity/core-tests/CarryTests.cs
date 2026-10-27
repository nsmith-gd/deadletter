using DeadLetter.Core.Carry;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl02;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>Core/Carry (§4.10): <see cref="CarriedItem"/> and its lane, and DL-02's box with the real motor; DL-02's tube letter.</summary>
    public class CarryTests
    {
        private static CarriedItem Box(out MechanismGraph g, string cp = "room")
        {
            var b = new CarriedItem("t.box", CarriedItemParams.Dl02Box());
            g = Mech.Graph(cp, b);
            return b;
        }

        [Fact]
        public void Callbacks_OnlyRecord_StepApplies()
        {
            var b = Box(out var g);
            b.OnLifted();
            Assert.Equal(ItemState.Floor, b.State);
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(ItemState.Carried, b.State);
            Assert.True(Mech.Emitted(g, "t.box", ItemEvent.Lifted));
            Assert.False(b.IsAvailable(default));
            b.OnSetDown(18.38, 0);
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(ItemState.Floor, b.State);
            Assert.Equal(18.38, b.X);
            Assert.Equal(0, b.SinceSetDown);
            Assert.True(Mech.Emitted(g, "t.box", ItemEvent.SetDown));
            Mech.Run(g, 13);
            Assert.True(b.SinceSetDown >= CarriedItem.DropSeconds);
        }

        [Fact]
        public void TopAt_IsTheBlock_OnlyOnTheFloor_L4150()
        {
            var b = Box(out var g);
            Assert.Equal(0.2, b.TopAt(17.4));
            Assert.Equal(0.2, b.TopAt(17.599));                                                      // |x − box.x| <= 0.2
            Assert.True(double.IsNaN(b.TopAt(17.601)));
            b.OnLifted(); g.Step(Mech.Dt, PlayerPose.Away);
            Assert.True(double.IsNaN(b.TopAt(17.4)));
            var lane = new CarriedItemLane(b, Dl02Lane.BoxWindowX0, Dl02Lane.BoxWindowX1);
            b.OnSetDown(25.3, 1.35); g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(1.55, lane.Surface(25.3, 1.35), 12);
            b.OnLifted(); g.Step(Mech.Dt, PlayerPose.Away);
            b.OnSetDown(25.5, 0); g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(0, lane.Surface(25.5, 0));                                                  // outside x < SH.x1 + 0.4
        }

        [Fact]
        public void MoveTo_Placed_KeepsTheSlot_AndReset_GoesHomeOrToItsSolvedPlace()
        {
            var p = CarriedItemParams.Dl02Box();
            p.MovedAfter = "solved"; p.MovedState = ItemState.Placed; p.MovedX = 29.0; p.MovedBaseY = 0.16; p.MovedSlot = 1;
            var b = new CarriedItem("t.w", p);
            var g = Mech.Graph("room", b);
            b.MoveTo(ItemState.Placed, 28.9, 0.16, 0);
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(ItemState.Placed, b.State);
            Assert.Equal(0, b.Slot);
            Assert.Equal(BodySupport.Placed, b.Support);
            g.Reset(Mech.Cp("weighroom"));
            Assert.Equal((ItemState.Floor, 17.4, -1), (b.State, b.X, b.Slot));
            g.Reset(Mech.Cp("solved"));
            Assert.Equal((ItemState.Placed, 29.0, 0.16, 1), (b.State, b.X, b.BaseY, b.Slot));
        }

        [Fact]
        public void Drop_OnlyFromHisHands_AndAtOnce()
        {
            var b = Box(out var g);
            b.Drop(15, 0);
            Assert.Equal(17.4, b.X);
            b.OnLifted(); g.Step(Mech.Dt, PlayerPose.Away);
            b.Drop(15, 0);
            Assert.Equal((ItemState.Floor, 15.0), (b.State, b.X));
        }

        [Fact]
        public void RestoreThenStep_IsBitIdentical()
        {
            var a = Box(out var ga);
            a.OnLifted(); ga.Step(Mech.Dt, PlayerPose.Away);
            a.OnSetDown(18.2, 0);                                                                    // pending at the snapshot
            var b = Box(out var gb);
            gb.Restore(Mech.Snapshot(ga));
            for (int i = 0; i < 20; i++) { ga.Step(Mech.Dt, PlayerPose.Away); gb.Step(Mech.Dt, PlayerPose.Away); Assert.Equal(Mech.Dump(ga), Mech.Dump(gb)); }
            Assert.Equal(18.2, b.X);
        }

        // ---- DL-02's box with the motor -------------------------------------------------------------------------------
        /// <summary>
        /// Lift (attach f22, carry f39), carry at 0.42 m/s with Jump doing nothing, set down GRIP_FWD in front where it is flat
        /// (f14), then the box is a 0.2 step: he hops on it and climbs to the table (scene doc §3).
        /// </summary>
        [Fact]
        public void Box_LiftCarrySetDown_ThenItIsTheStepToTheTable()
        {
            var sim = new SceneSim(Dl02Scene.Def());
            sim.Begin("room");
            sim.Motor.Place(16.9, 0, 1);
            var box = sim.Graph.Get<CarriedItem>("dl02.box");
            sim.Step(new MotorInput { UsePressed = true });
            Assert.Equal("dl02.box", sim.ActKind);
            int k = 0;
            while (box.State == ItemState.Floor && k++ < 300) sim.Step(default);
            Assert.Equal(ItemState.Carried, box.State);
            Assert.Equal(HoldKind.None, sim.Motor.Hold);                                            // f22: in his hands, not yet carried
            while (sim.Motor.Hold != HoldKind.Item && k++ < 300) sim.Step(default);
            Assert.Equal(MotorState.Carrying, sim.Motor.State);
            double y0 = sim.Y;
            for (int i = 0; i < 120; i++) sim.Step(new MotorInput { Move = 1, JumpPressed = i == 50, JumpHeld = i >= 50 && i < 60 });
            Assert.Equal(y0, sim.Y);                                                                 // no jump while carrying
            Assert.Equal(0.42, sim.Vx, 9);
            double x = sim.X;
            sim.Step(new MotorInput { UsePressed = true });
            while (sim.Motor.Hold == HoldKind.Item && k++ < 600) sim.Step(default);
            Assert.Equal(ItemState.Floor, box.State);
            Assert.Equal(x + 0.29, box.X, 9);
            Assert.Equal(0.2, sim.Lane.SurfaceAt(box.X));
            Assert.Null(sim.ActKind);
        }

        [Fact]
        public void Table_IsTooHighFromTheFloor_ButNotFromTheBox()
        {
            var lane = new LaneGeometry().AddRegion(2, Dl02Lane.Table());
            Assert.Equal(0.75, lane.SurfaceAt(18.6));
            Assert.Equal(0.75, lane.SurfaceAt(22.39));
            Assert.Equal(1.35, lane.SurfaceAt(22.4));                                               // the gantry over the table's end
            Assert.Equal(1.35, lane.SurfaceAt(25.32));
            Assert.Equal(0, lane.SurfaceAt(25.33));
            lane.Limits(13.2, 0, out double left, out _);
            Assert.Equal(12.2, left);
            Assert.Equal(4, lane.CeilingAt(25.1));
            Assert.Equal(2.6, lane.CeilingAt(25.11));
        }

        // ---- DL-02's tube letter --------------------------------------------------------------------------------------
        [Fact]
        public void TubeLetter_FallsOnceHePasses14_3_AndLands0_55sLater_L4772()
        {
            var l = new Dl02TubeLetter("t.tube");
            var g = Mech.Graph("room", l);
            g.Step(Mech.Dt, Mech.Pose(14.29));
            Assert.Equal(TubeLetterState.Cup, l.State);
            g.Step(Mech.Dt, Mech.Pose(14.31));
            Assert.Equal(TubeLetterState.Falling, l.State);
            Assert.True(Mech.Emitted(g, "t.tube", TubeLetterEvent.Cough));
            Assert.Equal(Mech.Dt, l.T);                                                              // it starts falling on the same step
            int n = 1;
            while (l.State == TubeLetterState.Falling) { g.Step(Mech.Dt, Mech.Pose(13)); n++; }
            Assert.Equal(33, n);                                                                     // 0.55 s
            Assert.True(Mech.Emitted(g, "t.tube", TubeLetterEvent.Landed));
            g.Reset(Mech.Cp("room"));
            Assert.Equal(TubeLetterState.Floor, l.State);                                            // a respawn does not put it back
        }

        [Fact]
        public void TubeLetter_ARespawnMidFall_RestartsItFromMinusOne_L4111()
        {
            var l = new Dl02TubeLetter("t.tube");
            var g = Mech.Graph("room", l);
            g.Step(Mech.Dt, Mech.Pose(14.5));
            g.Reset(Mech.Cp("room"));
            Assert.Equal(-1, l.T);
            int n = 0;
            while (l.State == TubeLetterState.Falling) { g.Step(Mech.Dt, Mech.Pose(13.2)); n++; }
            Assert.InRange(n, 93, 94);                                                              // 1.55 s
        }
    }
}
