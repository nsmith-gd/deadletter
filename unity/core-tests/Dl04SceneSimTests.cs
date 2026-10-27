using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl04;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-04 as Core runs it (<see cref="Dl04Scene.Def"/> in a <see cref="SceneSim"/>): the rules the trace does not reach
    /// (letting go of the courier short of the bay, so the cradle draws it in, and it is not his to take back; the shut
    /// door's wall; the reload at <c>bay</c>; the realisation after a reload at <c>solved</c>). L1956–L1958, L4171–L4174,
    /// L4783–L4816, L4096–L4097.
    /// </summary>
    public class Dl04SceneSimTests
    {
        private static readonly MotorInput Use = new MotorInput { UsePressed = true, UseHeld = true };
        private static readonly MotorInput Right = new MotorInput { Move = 1 };
        private static readonly MotorInput Jump = new MotorInput { JumpPressed = true, JumpHeld = true };

        private static int Until(SceneSim s, MotorInput input, Func<SceneSim, bool> done, int max = 4000)
        {
            for (int i = 1; i <= max; i++) { s.Step(input); if (done(s)) return i; }
            throw new Xunit.Sdk.XunitException("never: x=" + s.X + " act=" + s.ActKind + ":" + s.ActPhase);
        }

        /// <summary>Walked in at <paramref name="x"/> after a reload at <c>solved</c> (racks lit): he realises at once, and is freed 22.5 s on.</summary>
        private static SceneSim Realised(double x, int facing = 1)
        {
            var s = new SceneSim(Dl04Scene.Def());
            s.Handover("solved", x, 0, facing);
            s.Step(default);
            Assert.Equal("realise", s.ActKind);                                        // revealTime −100: at once (L8029, L1956)
            int n = Until(s, default, x2 => x2.Act == null);
            Assert.InRange(n * SceneSim.StepSeconds, 22.5 - 1e-9, 22.5 + 2 * SceneSim.StepSeconds);   // kin's control
            Assert.True(((Dl04Rules)s.Rules).KinSlow);
            return s;
        }

        private static Pushable Courier(SceneSim s) => s.Graph.Get<Pushable>("dl04.courier");
        private static Cradle Cradle(SceneSim s) => s.Graph.Get<Cradle>("dl04.cradle");
        private static PlateDoor Door(SceneSim s) => s.Graph.Get<PlateDoor>("dl04.bayDoor");

        [Fact]
        public void LetGoShortOfTheBay_TheCradleDrawsItIn_AndItIsNotHisToTakeBack_L4789_L4797()
        {
            var s = Realised(41.87, -1);
            s.Step(Use);
            Until(s, default, x => x.Motor.Hold == HoldKind.Push);
            Assert.Same(Courier(s), s.Motor.Pushed);                                  // its own face, from its right
            Assert.Equal(-0.35, -s.Z, 12);                                              // stepped in to its line
            Until(s, Right, x => Courier(s).X > 44.0);                                  // dragged to within 0.5 of the bay
            Assert.Equal(CradleState.Free, Cradle(s).State);                           // never out of his hands
            s.Step(Jump);                                                               // let go
            Assert.Equal(HoldKind.None, s.Motor.Hold);
            Assert.Equal(CradleState.Drawing, Cradle(s).State);
            Assert.False(s.Motor.PreviewUse(out _));                                   // pushHere: only while 'free'
            Until(s, default, x => Cradle(x).State == CradleState.Seated);
            Assert.Equal(Dl04Lane.BayX, Cradle(s).Position);
            Assert.Equal(PushableState.Free, Courier(s).State);                       // drawn in: never docked by his hands
            Assert.Equal("bayTouch", s.ActKind);                                        // he goes to it, once
            Until(s, default, x => x.Act == null);
            Assert.Equal(Dl04Scene.TouchStandX, s.X, 12);
            Assert.Equal(1, s.Motor.Facing);
            Until(s, default, x => Door(x).Engaged, 200);
            Assert.False(s.Motor.PreviewUse(out _));
        }

        [Fact]
        public void TheShutDoor_WallsHim_L4174()
        {
            var s = Realised(45.3);
            Until(s, Right, x => x.X > 46.09 - 1e-9);
            Assert.Equal(Dl04Lane.DoorX0 - 0.04 - 0.17, s.X, 12);                      // 46.09
            Assert.Equal(0, Door(s).Open01);
            for (int i = 0; i < 60; i++) s.Step(Right);
            Assert.Equal(Dl04Lane.DoorX0 - 0.04 - 0.17, s.X, 12);
            Assert.Equal("solved", s.Checkpoints.Current.Name);
        }

        [Fact]
        public void HeAloneOpensIt_UntilHeStepsOff_L4786_L4815()
        {
            var s = Realised(43.4);
            Assert.Equal(0, Door(s).Open01);
            Until(s, Right, x => x.X > Dl04Lane.PlateX0);                              // onto the plate
            Assert.True(s.Graph.Get<LoadPlate>("dl04.bayPlate").Engaged);
            Assert.Equal(SceneSim.StepSeconds / 1.1, Door(s).Open01, 12);
            int open = Until(s, default, x => Door(x).Engaged, 200);
            Assert.Equal(66, open);                                                     // 1.1 s
            Until(s, Right, x => x.X >= Dl04Lane.PlateX1);                              // off the plate
            Assert.Equal(1 - SceneSim.StepSeconds / 0.5, Door(s).Open01, 12);
            int shut = Until(s, default, x => Door(x).Open01 == 0, 200);
            Assert.Equal(30, shut);                                                     // 0.5 s and a step: 30 decrements of 1/30 leave a rounding residue
        }

        [Fact]
        public void ReloadAtBay_TheCourierSeated_TheDoorOpen_NoTouch_L4096_L4097()
        {
            var s = new SceneSim(Dl04Scene.Def());
            s.Begin("bay");
            Assert.Equal(Dl04Scene.BayX, s.X, 12);
            Assert.Equal(CradleState.Seated, Cradle(s).State);
            Assert.Equal(PushableState.Docked, Courier(s).State);
            Assert.Equal(Dl04Lane.BayX, Cradle(s).Position);
            Assert.Equal(1, Door(s).Open01);
            for (int i = 0; i < 120; i++) s.Step(default);
            Assert.NotEqual("bayTouch", s.ActKind);
            Assert.Equal(1, Door(s).Open01);
            Until(s, Right, x => x.Exited);
            Assert.True(s.X >= Dl04Scene.X1);
        }
    }
}
