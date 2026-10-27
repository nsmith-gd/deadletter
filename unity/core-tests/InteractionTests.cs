using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>Interaction resolver and the carry / push / present / sit / use acts (§4.9–§4.12).</summary>
    public class InteractionTests
    {
        private const double Dt = Sim.Dt;

        private static InteractionQuery Pose(double x, int facing, double y = 0)
            => new InteractionQuery(x, y, 0, facing, true, false, HoldKind.None, null, null);

        // ---- Resolver -------------------------------------------------------------------------------------------------------

        [Fact]
        public void PicksTargetInFront_NotBehind_EvenWhenBehindIsNearer()
        {
            var r = new InteractionResolver();
            var behind = new TestItem { X = 0.70 };   // stand point 0.99: 0.01 from him
            var front = new TestItem { X = 1.35 };    // stand point 1.06: 0.06 from him
            r.Register(behind);
            r.Register(front);

            Assert.True(r.Resolve(Pose(1.0, +1), out var c));
            Assert.Same(front, c.Target);
            Assert.Equal(Verb.Lift, c.Verb);
            Assert.Equal(1.35 - 0.29, c.StandX, 12);   // GRIP_FWD, L4220
            Assert.Equal(+1, c.Face);

            Assert.True(r.Resolve(Pose(1.0, -1), out var c2));
            Assert.Same(behind, c2.Target);
            Assert.Equal(-1, c2.Face);
        }

        [Fact]
        public void PicksNearestAmongTargetsInFront()
        {
            var r = new InteractionResolver();
            var far = new TestItem { X = 1.55 };
            var near = new TestItem { X = 1.35 };
            r.Register(far);
            r.Register(near);
            Assert.True(r.Resolve(Pose(1.0, +1), out var c));
            Assert.Same(near, c.Target);
        }

        [Fact]
        public void BehindTargetStillAnswersWhenNothingIsInFront_L4220()
        {
            var r = new InteractionResolver();
            var behind = new TestItem { X = 0.70 };
            r.Register(behind);
            Assert.True(r.Resolve(Pose(1.0, +1), out var c));
            Assert.Same(behind, c.Target);
            Assert.False(c.InFront);
        }

        [Fact]
        public void ItemReach_Is04AroundTheStandPoint_AndSameLevel_L4219_L4221()
        {
            var r = new InteractionResolver();
            r.Register(new TestItem { X = 2.0 });
            Assert.True(r.Resolve(Pose(2.0 - 0.29 - 0.39, +1), out _));
            Assert.False(r.Resolve(Pose(2.0 - 0.29 - 0.41, +1), out _));
            Assert.False(r.Resolve(Pose(1.71, +1, y: 0.06), out _));   // not on its level
        }

        [Fact]
        public void CategoryPriority_ItemBeatsPush_L4204_L4257()
        {
            var r = new InteractionResolver();
            var push = new TestPushable { X = 1.6, Side = 1, Gap = 0.6, Min = 0, Max = 5 };   // stand 1.0
            var item = new TestItem { X = 0.6 };                                            // behind him
            r.Register(push);
            r.Register(item);
            Assert.True(r.Resolve(Pose(1.0, +1), out var c));
            Assert.Same(item, c.Target);
            var all = new List<Candidate>();
            Assert.Equal(2, r.AnswersByCategory(Pose(1.0, +1), all));   // an overlap the audit must flag
        }

        [Fact]
        public void PushGrip_BackReachShorterThanForward_L4254_L4274()
        {
            var r = new InteractionResolver();
            var cart = new TestPushable { X = 1.6, Side = 1, Gap = 0.6, Min = 0, Max = 5, BackReach = 0.2 };   // stand 1.0
            r.Register(cart);
            Assert.True(r.Resolve(Pose(1.0 + 0.33, +1), out _));     // in front of the grip: 0.34
            Assert.False(r.Resolve(Pose(1.0 - 0.25, +1), out _));    // behind it: only 0.2
            Assert.True(r.Resolve(Pose(1.0 - 0.19, +1), out _));
        }

        [Fact]
        public void NothingAnswersInTheAir_L4205()
        {
            var r = new InteractionResolver();
            r.Register(new TestItem { X = 1.35 });
            var q = new InteractionQuery(1.0, 0, 0, 1, false, false, HoldKind.None, null, null);
            Assert.False(r.Resolve(q, out _));
        }

        // ---- Carry -------------------------------------------------------------------------------------------------------------

        [Fact]
        public void Lift_AttachesAtFrame22_CarriesAtFrame39_ThenSetDownNeverRefuses_L4418_L4426()
        {
            var r = new InteractionResolver();
            var item = new TestItem { X = 1.35 };
            r.Register(item);
            var m = Sim.Make(BoxWorld.Flat(), 1.0, 0, r);
            item.Motor = m;

            m.Step(Sim.Use(), Dt);
            Assert.Equal(MotorState.Acting, m.State);
            Assert.Equal(Verb.Lift, m.ActVerb);
            int toClip = Sim.RunUntil(m, Sim.Move(0), d => d.Clip == ClipNames.Lift);
            Assert.True(toClip > 0);
            Assert.Equal(1.35 - 0.29, m.X, 12);
            long clipStart = m.StepCount;

            int attach = Sim.RunUntil(m, Sim.Move(0), d => item.Carried);
            Assert.InRange(item.LiftedAtStep - clipStart, 22.0 / 24 * 60 - 1, 22.0 / 24 * 60 + 2);
            int carry = Sim.RunUntil(m, Sim.Move(0), d => d.Hold == HoldKind.Item);
            Assert.InRange(m.StepCount - clipStart, 39.0 / 24 * 60 - 1, 39.0 / 24 * 60 + 2);
            Assert.Equal(MotorState.Carrying, m.State);
            Assert.Equal(1.0, m.CarryBlend);

            // Heavy carry: 0.42 m/s, no jump (L2318–L2361).
            Sim.Run(m, Sim.Move(1), 120);
            Assert.Equal(0.42, m.Vx, 9);
            Assert.False(Sim.Run(m, Sim.Jump(1), 1, MotorEventKind.Jump));

            // Set down in front, at GRIP_FWD (L4344).
            Sim.Run(m, Sim.Move(0), 60);
            double x = m.X;
            m.Step(Sim.Use(), Dt);
            Assert.Equal(Verb.SetDown, m.ActVerb);
            Sim.RunUntil(m, Sim.Move(0), d => d.Hold == HoldKind.None);
            Assert.False(item.Carried);
            Assert.Equal(x + 0.29, item.X, 9);
            Assert.Equal(MotorState.Grounded, m.State);
        }

        [Fact]
        public void SetDown_TriesBehindWhenFrontIsNotFlat_L4343_L4347()
        {
            var w = BoxWorld.Flat().AddSolid(1.2, 1.6, 0.3);   // a step right in front of him
            var c = MotorConfig.Prototype();
            PlaceSearch.Find(w, c, 1.0, 0, +1, 0.1, out double tx, out double baseY, out int face);
            Assert.Equal(-1, face);
            Assert.Equal(1.0 - 0.29, tx, 12);
            Assert.Equal(0, baseY);
        }

        [Fact]
        public void LightCarry_WalksAndJumps_L1967_L1970()
        {
            var r = new InteractionResolver();
            var coat = new TestItem { X = 1.35, IsLight = true };
            r.Register(coat);
            var m = Sim.Make(BoxWorld.Flat(), 1.0, 0, r);
            m.Step(Sim.Use(), Dt);
            Sim.RunUntil(m, Sim.Move(0), d => d.Hold == HoldKind.Item);
            Sim.Run(m, Sim.Move(1), 120);
            Assert.Equal(0.9, m.Vx, 9);                       // no running
            Assert.Equal(MotorState.Grounded, m.State);
            Assert.True(Sim.Run(m, Sim.Jump(1), 1, MotorEventKind.Jump));
        }

        // ---- Push --------------------------------------------------------------------------------------------------------------

        [Fact]
        public void Grab_PushToEndOfTravel_ReleasesAndEnds_L4683_L4735()
        {
            var r = new InteractionResolver();
            var fig = new TestPushable { X = 1.6, Side = 1, Gap = 0.6, Speed = 0.4, Min = 1.6, Max = 2.4 };
            r.Register(fig);
            var m = Sim.Make(BoxWorld.Flat(), 0.9, 0, r);

            m.Step(Sim.Use(), Dt);
            Assert.Equal(Verb.Grab, m.ActVerb);
            Sim.RunUntil(m, Sim.Move(0), d => d.Hold == HoldKind.Push);
            Assert.Equal(1.0, m.X, 9);
            Assert.Equal(MotorState.Pushing, m.State);

            Sim.RunUntil(m, Sim.Move(1), d => fig.Ended, 1200);
            Assert.True(fig.Ended);
            Assert.True(fig.Released);
            Assert.InRange(fig.X, 2.4 - 0.005, 2.4);            // stops within 5 mm of Max (L4723)
            Assert.Equal(fig.X - 0.6, m.X, 9);
            Assert.Equal(HoldKind.None, m.Hold);
        }

        [Fact]
        public void Push_PullsBackwardsWithNegativeClipSpeed_AndJumpLetsGo_L4688_L4701()
        {
            var r = new InteractionResolver();
            var fig = new TestPushable { X = 1.6, Side = 1, Gap = 0.6, Speed = 0.4, Min = 1.0, Max = 2.4 };
            r.Register(fig);
            var m = Sim.Make(BoxWorld.Flat(), 1.0, 0, r);
            m.Step(Sim.Use(), Dt);
            Sim.RunUntil(m, Sim.Move(0), d => d.Hold == HoldKind.Push);
            Sim.Run(m, Sim.Move(-1), 60);
            Assert.True(fig.X < 1.6);
            Assert.Equal(ClipNames.PushWalk, m.Clip);
            Assert.True(m.ClipTimeScale < 0);
            Assert.Equal(+1, m.Facing);
            m.Step(Sim.Jump(), Dt);
            Assert.True(fig.Released);
            Assert.False(fig.Tipped);
            Assert.Equal(HoldKind.None, m.Hold);
        }

        [Fact]
        public void Tipping_HeldIntoTheLipFor045s_Shoves_L4708_L4715()
        {
            var r = new InteractionResolver();
            var cart = new TestPushable { X = 1.6, Side = 1, Gap = 0.6, Speed = 0.55, Min = 1.6, Max = 1.9, TipsIntoPit = true };
            r.Register(cart);
            var m = Sim.Make(BoxWorld.Flat(), 1.0, 0, r);
            m.Step(Sim.Use(), Dt);
            Sim.RunUntil(m, Sim.Move(0), d => d.Hold == HoldKind.Push);
            int steps = Sim.RunUntil(m, Sim.Move(1), d => cart.Shoved, 600);
            Assert.True(steps > 0);
            Assert.True(cart.Tipped);
            Assert.Equal(ClipNames.Nudge, m.Clip);
            Assert.Equal(MotorState.Acting, m.State);
            Sim.Run(m, Sim.Move(0), 60);
            Assert.Equal(MotorState.Grounded, m.State);
        }

        // ---- Present, sit, use ------------------------------------------------------------------------------------------

        [Fact]
        public void Present_TurnsStepsInBeatsAtClipFramesAndStepsOut_L3603_L3625()
        {
            var r = new InteractionResolver();
            var term = new TestPresent { StandX = 1.2, Reach = 0.5, StandZ = 0.4, Face = 1 };
            r.Register(term);
            var m = Sim.Make(BoxWorld.Flat(), 1.0, 0, r);
            term.Motor = m;
            m.Step(Sim.Use(), Dt);
            Assert.Equal(MotorState.Presenting, m.State);

            double maxZ = 0;
            Sim.RunUntil(m, Sim.Move(0), d => { maxZ = Math.Max(maxZ, d.Z); return !d.IsActing; }, 1200);
            Assert.Equal(0.4, maxZ, 9);
            Assert.Equal(0.0, m.Z);
            Assert.Equal(5, term.Beats.Count);
            double[] frames = { 20, 25, 30, 36, 50 };
            for (int i = 0; i < 5; i++)
            {
                Assert.Equal((PresentBeat)i, term.Beats[i].beat);
                Assert.InRange(term.Beats[i].frame, frames[i] - 1e-6, frames[i] + 24.0 / 60 + 1e-6);   // within one step
            }
            Sim.Run(m, Sim.Move(0), 30);               // the yaw turns back after the act, at 8 rad/s (L7581)
            Assert.Equal(Math.PI / 2, m.Yaw, 9);
        }

        [Fact]
        public void Sit_SeatedAfter04s_GetsUpOnMoveAfter1s_L5673_L5681()
        {
            var r = new InteractionResolver();
            var chair = new TestSeat { StandX = 1.1, Reach = 0.3, StandZ = 0.3, Face = 1 };
            r.Register(chair);
            var m = Sim.Make(BoxWorld.Flat(), 1.0, 0, r);
            m.Step(Sim.Use(), Dt);
            Sim.RunUntil(m, Sim.Move(0), d => d.Clip == ClipNames.Sit);
            Assert.Equal(MotorState.Sitting, m.State);
            Assert.Equal(0.3, m.Z, 9);
            Sim.Run(m, Sim.Move(0), 23);
            Assert.Empty(chair.Calls);
            Sim.Run(m, Sim.Move(0), 2);
            Assert.Equal(new[] { true }, chair.Calls);
            Sim.Run(m, Sim.Move(1), 20);                     // 0.75 s: SitIdle, but too early to stand (< 1.0 s)
            Assert.Equal(MotorState.Sitting, m.State);
            Assert.Equal(ClipNames.SitIdle, m.Clip);
            Sim.RunUntil(m, Sim.Move(1), d => d.Clip == ClipNames.SitUp);
            Assert.Equal(new[] { true, false }, chair.Calls);
            Sim.Run(m, Sim.Move(0), 40);
            Assert.False(m.IsActing);
        }

        [Fact]
        public void Use_FixedControl_RunsClipFramesThroughTheContract_L2899_L2937()
        {
            var r = new InteractionResolver();
            var lever = new TestLever { StandX = 1.2, Reach = 0.38, Face = 1 };
            r.Register(lever);
            var m = Sim.Make(BoxWorld.Flat(), 1.0, 0, r);
            m.Step(Sim.Use(), Dt);
            Sim.RunUntil(m, Sim.Move(0), d => !d.IsActing, 600);
            Assert.Equal(1, lever.ThrownCount);
            Assert.InRange(lever.LastFrame, 33, 33 + 0.4 + 1e-9);
        }
    }

    public class ClipTimingsTests
    {
        [Fact]
        public void Table_Has76Clips_FromD17Glb()
        {
            Assert.Equal(76, ClipTimings.All.Length);
            var names = new HashSet<string>();
            foreach (var c in ClipTimings.All) Assert.True(names.Add(c.Name), c.Name);
        }

        [Fact]
        public void MantleClip_Is56Frames_MatchesMantleFramesAndKeys_L311_L313()
        {
            Assert.True(ClipTimings.TryGet(ClipNames.Mantle, out var mantle));
            Assert.Equal(56, mantle.Frames);
            Assert.Equal(56.0 / 24.0, mantle.Seconds(), 12);
            Assert.Equal(ClipTimings.MantleEvents.End, mantle.Frames);
            Assert.Equal(56, MotorConfig.MantleKeys[MotorConfig.MantleKeys.GetLength(0) - 1, 0]);
            MotorConfig.MantleAt(56, out double fwd, out double frac);
            Assert.Equal(0.38, fwd, 12);
            Assert.Equal(1.0, frac, 12);
        }

        [Fact]
        public void EveryClipEvent_FallsInsideItsClip()
        {
            foreach (var e in ClipTimings.Events)
            {
                Assert.True(ClipTimings.TryGet(e.Clip, out var clip), "missing clip " + e.Clip);
                Assert.True(e.Frame <= clip.Frames, e.Clip + "." + e.Name + " f" + e.Frame + " > " + clip.Frames + " (" + e.Line + ")");
            }
        }

        [Theory]
        [InlineData("Idle", 168)] [InlineData("Walk", 11)] [InlineData("Run", 10)] [InlineData("CrouchWalk", 13)]
        [InlineData("CrouchIdle", 48)] [InlineData("JumpAir", 8)] [InlineData("Fall", 16)] [InlineData("SitIdle", 48)]
        [InlineData("Crank", 24)] [InlineData("CageRideLever", 48)] [InlineData("CarryIdle", 48)] [InlineData("CarryWalk", 14)]
        [InlineData("PushIdle", 48)] [InlineData("PushWalk", 12)] [InlineData("Ride", 48)] [InlineData("SadWalk", 16)]
        public void LoopFrames_MatchPrototype_L315_L316(string clip, double loopFrames)
        {
            Assert.True(ClipTimings.TryGet(clip, out var c));
            Assert.True(c.Loop);
            Assert.Equal(loopFrames, c.LoopFrames);
        }

        [Fact]
        public void ClipClock_CrossedFiresOnce()
        {
            Assert.True(ClipClock.Crossed(21.9, 22.3, 22));
            Assert.False(ClipClock.Crossed(22.3, 22.7, 22));
            Assert.True(ClipClock.Reached(21.9999999999, 22));
        }

        [Theory]
        [InlineData(0.1, 0.0)]
        [InlineData(0.22, 0.0)]
        [InlineData(-0.3, -0.3)]
        [InlineData(1.4, 1.0)]
        public void StickDeadzone_Unscaled_L1266(double raw, double expected)
        {
            Assert.Equal(expected, MotorInput.FromStick(raw));
        }
    }
}
