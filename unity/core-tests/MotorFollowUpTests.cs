using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// #32 (U-11d), follow-ups from the #30 reviews: Use at a pit's lip lets go without tipping (L1820); the step back to
    /// the lane only where the prototype's scenes have it (L3569, L4876, L5796); the snapshot carries the clip; Capture
    /// refuses an act, hold, mantle or ride; a trace hand-over's peakY.
    /// </summary>
    public class MotorFollowUpTests
    {
        private const double Dt = Sim.Dt;

        // ---- Use at the lip (L1820 vs L4688, L4708–L4715) -------------------------------------------------------------

        /// <summary>Takes hold of what <paramref name="r"/> offers and pushes it on until <paramref name="atLip"/>, stepping the graph after the motor.</summary>
        private static Action<MotorInput> PushToTheLip(D17Motor m, MechanismGraph g, Func<bool> atLip)
        {
            void Step(MotorInput i) { m.Step(i, Dt); g.Step(Dt, Mech.Pose(m)); }
            Step(Sim.Use());
            for (int i = 0; i < 120 && m.Hold != HoldKind.Push; i++) Step(Sim.Move(0));
            Assert.Equal(HoldKind.Push, m.Hold);
            for (int i = 0; i < 600 && !atLip(); i++) Step(Sim.Move(1));
            Assert.True(atLip());
            Assert.Equal(HoldKind.Push, m.Hold);                                       // reached it, not yet shoved (0.45 s)
            return Step;
        }

        private static double ReleasedValue(D17Motor m)
        {
            foreach (var e in m.Events) if (e.Kind == MotorEventKind.Released) return e.Value;
            return double.NaN;
        }

        [Fact]
        public void UseAtTheLip_LetsGoWithoutTipping_ItStaysTeetering_JumpThereTipsIt_L1820_L4688()
        {
            var b = new TippingBridge("dl01.cart", TippingBridgeParams.Dl01Cart());
            var g = Mech.Graph("start", b);
            var r = new InteractionResolver();
            r.Register(b);
            var m = Sim.Make(BoxWorld.Flat(0, 20), 4.93, 0, r);
            var step = PushToTheLip(m, g, () => b.State == TippingBridgeState.AtLip);

            step(Sim.Use());                                                           // beginUse 'release': hold = null, Idle
            Assert.Equal(HoldKind.None, m.Hold);
            Assert.Equal(0, ReleasedValue(m));
            Assert.Equal(ClipNames.Idle, m.Clip);
            Assert.False(Mech.Emitted(g, "dl01.cart", TippingBridgeEvent.Tip));
            for (int i = 0; i < 120; i++)
            {
                step(Sim.Move(0));
                Assert.Equal(TippingBridgeState.AtLip, b.State);                        // s.lip stays: still teetering
                Assert.False(Mech.Emitted(g, "dl01.cart", TippingBridgeEvent.Tip));
            }
            Assert.Equal(b.Max, b.X, 12);

            step(Sim.Use());                                                           // take hold again, still at the lip
            for (int i = 0; i < 120 && m.Hold != HoldKind.Push; i++) step(Sim.Move(0));
            Assert.Equal(HoldKind.Push, m.Hold);
            step(Sim.Jump());                                                          // L4688: Jump at the lip tips it in
            Assert.Equal(HoldKind.None, m.Hold);
            Assert.Equal(1, ReleasedValue(m));
            Assert.True(Mech.Emitted(g, "dl01.cart", TippingBridgeEvent.Tip));
            Assert.Equal(TippingBridgeState.Falling, b.State);
        }

        [Fact]
        public void UseAtTheLip_APushableStaysAtTheLipToo_L1820()
        {
            var tip = TipParams.Dl01Cart();
            var cart = new Pushable("t.cart", new PushableParams
            {
                StartX = 5.9, Side = 1, Gap = 0.97, Speed = 0.55, BackReach = 0.2, Min = 5.9, Max = tip.LipX,
                Pit = tip, ParkedAfter = "hall", ParkedState = PushableState.Settled, Half = 0.65, Top = 0.55,
            });
            var g = Mech.Graph("start", cart);
            var r = new InteractionResolver();
            r.Register(cart);
            var m = Sim.Make(BoxWorld.Flat(0, 20), 4.93, 0, r);
            var step = PushToTheLip(m, g, () => cart.State == PushableState.AtLip);

            step(Sim.Use());
            Assert.Equal(HoldKind.None, m.Hold);
            Assert.Equal(0, ReleasedValue(m));
            for (int i = 0; i < 120; i++)
            {
                step(Sim.Move(0));
                Assert.Equal(PushableState.AtLip, cart.State);
                Assert.False(Mech.Emitted(g, "t.cart", PushableEvent.Tip));
            }
        }

        [Fact]
        public void ATestPushable_IsToldNotToTip_OnUseAtTheLip()
        {
            var p = new TestPushable { X = 1.6, Min = 0, Max = 2.0, TipsIntoPit = true, LetGoAtMax = false };
            var r = new InteractionResolver();
            r.Register(p);
            var m = Sim.Make(BoxWorld.Flat(), 1.0, 0, r);
            m.Step(Sim.Use(), Dt);
            Assert.True(Sim.RunUntil(m, Sim.Move(0), mm => mm.Hold == HoldKind.Push, 600) > 0);
            Assert.True(Sim.RunUntil(m, Sim.Move(1), mm => p.AtLip, 600) > 0);
            m.Step(Sim.Use(), Dt);
            Assert.True(p.Released);
            Assert.False(p.Tipped);
            Assert.True(p.AtLip);                                                      // the motor never cleared it
        }

        // ---- The step back to the lane (L3569–L3570, L4876, L5796) ------------------------------------------------------

        private static D17Motor OnRegion(int region, double x, double z, MotorConfig config = null)
        {
            var lane = new LaneGeometry().AddRegion(region, new LaneTable());
            var m = new D17Motor(config ?? MotorConfig.Prototype(), lane);
            var s = MotorSnapshot.AtRest(x, 0);
            s.Z = z;
            m.SetState(s);
            return m;
        }

        [Theory]
        [InlineData(2, 1.0, true)]       // updateCh1, L4876: region 2, anywhere
        [InlineData(5, 120.0, true)]     // updateDL05, L3569: region 5 (the desk)
        [InlineData(6, 248.0, false)]    // updateAtt2, L5796: region 6 only past x 248
        [InlineData(6, 248.01, true)]
        [InlineData(1, 1.0, false)]      // DL-01: no such rule
        [InlineData(3, 40.0, false)]     // DL-06: no such rule
        [InlineData(4, 70.0, false)]
        public void StepBack_OnlyWhereThePrototypeHasIt(int region, double x, bool back)
        {
            var m = OnRegion(region, x, 0.3);
            m.Step(Sim.Move(0), Dt);
            Assert.Equal(back ? 0.3 - 0.45 * Dt : 0.3, m.Z, 12);
            Assert.Equal(back, MotorConfig.PrototypeReturnsToLane(new LaneGeometry().AddRegion(region, new LaneTable()), x));
        }

        [Fact]
        public void StepBack_OnlyFromIntoTheSet_ThePrototypesZBelow0()
        {
            var m = OnRegion(2, 1.0, -0.3);                                            // three z = +0.3: game.z < 0 is false
            Sim.Run(m, Sim.Move(0), 30);
            Assert.Equal(-0.3, m.Z, 12);
            var into = OnRegion(2, 1.0, 0.01);
            Sim.Run(into, Sim.Move(0), 30);
            Assert.Equal(0, into.Z);                                                   // Math.min(0, z + 0.45·dt): exactly 0
        }

        [Fact]
        public void StepBack_NoneOnAWorldWithoutRegions()
        {
            Assert.False(MotorConfig.PrototypeReturnsToLane(BoxWorld.Flat(), 1.0));
            var m = Sim.Make(BoxWorld.Flat(), 1.0);
            var s = m.Capture();
            s.Z = 0.3;
            m.SetState(s);
            Sim.Run(m, Sim.Move(0), 10);
            Assert.Equal(0.3, m.Z);
        }

        [Fact]
        public void StepBack_GoesOnWhileHeMantles_TheRulesDoNotCheckGameMantle()
        {
            var cfg = MotorConfig.Prototype();
            cfg.ReturnsToLane = (w, x) => true;
            var m = Sim.Make(BoxWorld.Flat().AddSolid(1.3, 3.0, 0.4), 1.0, config: cfg);
            var s = m.Capture();
            s.Z = 0.3;
            m.SetState(s);
            m.Step(Sim.Jump(), Dt);
            Assert.True(m.IsMantling);
            Assert.Equal(0.3 - 0.45 * Dt, m.Z, 12);
            Sim.Run(m, Sim.Move(0), 20);
            Assert.True(m.IsMantling);
            Assert.Equal(0.3 - 21 * 0.45 * Dt, m.Z, 12);
        }

        // ---- The snapshot's clip -----------------------------------------------------------------------------------------

        [Fact]
        public void Snapshot_ARunningHandOver_KeepsTheClipPhaseAndFootsteps()
        {
            var a = Sim.Make(BoxWorld.Flat(), 0);
            Sim.Run(a, Sim.Move(1), 47);
            var s = a.Capture();
            Assert.Equal(ClipNames.Run, s.Clip);
            Assert.True(s.ClipTime > 0);

            var b = Sim.Make(BoxWorld.Flat(), 5);
            b.SetState(s);
            Assert.Equal(a.Clip, b.Clip);
            Assert.Equal(a.ClipTime, b.ClipTime);
            Assert.Equal(a.ClipTimeScale, b.ClipTimeScale);
            int steps = 0;
            for (int i = 0; i < 120; i++)
            {
                a.Step(Sim.Move(1), Dt); b.Step(Sim.Move(1), Dt);
                Assert.Equal(Sim.Snapshot(a), Sim.Snapshot(b));                         // footsteps on the same steps
                Assert.Equal(a.ClipTime, b.ClipTime);
                if (Sim.Has(a, MotorEventKind.Footstep)) steps++;
            }
            Assert.True(steps > 4);
        }

        [Fact]
        public void Snapshot_AnAirborneHandOver_PlaysTheAirClip_ThenFallsAsThePrototype_L2019()
        {
            var m = Sim.Make(BoxWorld.Flat(), 0);
            m.SetState(new MotorSnapshot { X = 1, Y = 2, Vy = -2, Facing = 1, Yaw = Math.PI / 2, PeakY = 2.5 });
            Assert.Equal(ClipNames.JumpAir, m.Clip);                                   // no clip given: in the air, JumpAir
            m.Step(Sim.Move(0), Dt);
            Assert.Equal(ClipNames.Fall, m.Clip);                                      // vy < −1.4 and peakY − y > 0.25

            var ground = Sim.Make(BoxWorld.Flat(), 0);
            ground.SetState(MotorSnapshot.AtRest(1, 0));
            Assert.Equal(ClipNames.Idle, ground.Clip);

            // Captured mid-jump, restored elsewhere: the same arc, the same clip, the same landing.
            var a = Sim.Make(BoxWorld.Flat(), 0);
            a.Step(Sim.Jump(1), Dt);
            Sim.Run(a, Sim.Move(1), 10);
            Assert.False(a.Grounded);
            var b = Sim.Make(BoxWorld.Flat(), 3);
            b.SetState(a.Capture());
            Assert.Equal(ClipNames.JumpAir, b.Clip);
            for (int i = 0; i < 60; i++)
            {
                a.Step(Sim.Move(1), Dt); b.Step(Sim.Move(1), Dt);
                Assert.Equal(Sim.Snapshot(a), Sim.Snapshot(b));
            }
        }

        /// <summary>
        /// A hand-over doesn't depend on the receiving motor's history (#33 review): one already in the snapshot's clip
        /// restarts it at the snapshot's time, as a fresh motor does, instead of keeping its own time and serial.
        /// </summary>
        [Fact]
        public void Snapshot_HandOverOntoAMotorAlreadyInThatClip_MatchesAFreshMotor()
        {
            var a = Sim.Make(BoxWorld.Flat(), 0);
            a.Step(Sim.Jump(1), Dt);
            Sim.Run(a, Sim.Move(1), 10);
            var s = a.Capture();
            s.Clip = null;                                                             // no clip given: JumpAir in the air

            var used = Sim.Make(BoxWorld.Flat(), 3);
            used.Step(Sim.Jump(1), Dt);
            Sim.Run(used, Sim.Move(1), 20);
            Assert.Equal(ClipNames.JumpAir, used.Clip);
            int serial = used.ClipSerial;
            used.SetState(s);

            var fresh = Sim.Make(BoxWorld.Flat(), 3);
            fresh.SetState(s);
            Assert.Equal(fresh.Clip, used.Clip);
            Assert.Equal(fresh.ClipTime, used.ClipTime);
            Assert.Equal(0, used.ClipTime);
            Assert.NotEqual(serial, used.ClipSerial);
        }

        // ---- Capture refuses what a snapshot cannot hold ----------------------------------------------------------------

        [Fact]
        public void Capture_ThrowsDuringAHoldAnActOrAMantle()
        {
            var m = Sim.Make(BoxWorld.Flat(), 1.0);
            Assert.True(m.CanCapture);
            m.Capture();

            var p = new TestPushable { X = 1.6, Min = 0, Max = 10, LetGoAtMax = false };
            var r = new InteractionResolver();
            r.Register(p);
            var push = Sim.Make(BoxWorld.Flat(), 1.0, 0, r);
            push.Step(Sim.Use(), Dt);
            Assert.True(push.IsActing);                                                // the grab act
            Assert.False(push.CanCapture);
            Assert.Throws<InvalidOperationException>(() => push.Capture());
            Sim.RunUntil(push, Sim.Move(0), mm => mm.Hold == HoldKind.Push, 600);
            Assert.False(push.CanCapture);
            Assert.Throws<InvalidOperationException>(() => push.Capture());
            push.Step(Sim.Jump(), Dt);                                                 // lets go
            Assert.True(push.CanCapture);

            var mantle = Sim.Make(BoxWorld.Flat().AddSolid(1.3, 3.0, 0.4), 1.0);
            mantle.Step(Sim.Jump(), Dt);
            Assert.True(mantle.IsMantling);
            Assert.False(mantle.CanCapture);
            Assert.Throws<InvalidOperationException>(() => mantle.Capture());

            var item = new TestItem { X = 1.29, IsLight = true };
            var ri = new InteractionResolver();
            ri.Register(item);
            var carry = Sim.Make(BoxWorld.Flat(), 1.0, 0, ri);
            item.Motor = carry;
            carry.Step(Sim.Use(), Dt);
            Sim.RunUntil(carry, Sim.Move(0), mm => mm.Hold == HoldKind.Item && !mm.IsActing, 600);
            Assert.Equal(HoldKind.Item, carry.Hold);
            Assert.False(carry.CanCapture);                                            // even a light item: the snapshot has no hands
            Assert.Throws<InvalidOperationException>(() => carry.Capture());
        }

        // ---- TakeItem: a scene act's own lift hands him the item (#35, L4420, L5303) -----------------------------------

        [Fact]
        public void TakeItem_HoldsItAsLiftF39Leaves_UseSetsItDown_CaptureRefuses()
        {
            var item = new TestItem { X = 3.0, IsLight = true };
            var r = new InteractionResolver();
            r.Register(item);
            var m = Sim.Make(BoxWorld.Flat(), 1.0, 0, r);
            m.Place(2.0, 0, -1);
            item.Carried = true;                                                       // the scene's act lifted it (its OnLifted)
            m.TakeItem(item);

            Assert.Equal(HoldKind.Item, m.Hold);
            Assert.Same(item, m.Carried);
            Assert.Equal(1, m.CarryBlend);
            Assert.Equal(ClipNames.CarryIdle, m.Clip);
            Assert.False(m.IsActing);
            Assert.False(m.CanCapture);
            Assert.Throws<InvalidOperationException>(() => m.Capture());

            m.Step(Sim.Move(0), Dt);
            var q = m.Query();
            Assert.Equal(HoldKind.Item, q.Hold);
            Assert.Same(item, q.Carried);
            Assert.True(m.PreviewUse(out var c));
            Assert.Equal(Verb.SetDown, c.Verb);
            Assert.Same(item, c.Target);

            m.Step(Sim.Use(), Dt);                                                     // and the set-down plays as after a Lift
            Sim.RunUntil(m, Sim.Move(0), mm => !mm.IsActing, 600);
            Assert.Equal(HoldKind.None, m.Hold);
            Assert.False(item.Carried);
        }

        [Fact]
        public void TakeItem_OnlyFromRest()
        {
            var item = new TestItem { IsLight = true };
            Assert.Throws<ArgumentNullException>(() => Sim.Make(BoxWorld.Flat(), 1.0).TakeItem(null));

            var holding = Sim.Make(BoxWorld.Flat(), 1.0);
            holding.TakeItem(item);
            Assert.Throws<InvalidOperationException>(() => holding.TakeItem(new TestItem()));
            Assert.Same(item, holding.Carried);

            var acting = Sim.Make(BoxWorld.Flat(), 1.0);
            Assert.True(acting.PlayQuirk(ClipNames.Idle, holdFor: 2));
            Assert.Throws<InvalidOperationException>(() => acting.TakeItem(item));
            Assert.Equal(HoldKind.None, acting.Hold);

            var mantle = Sim.Make(BoxWorld.Flat().AddSolid(1.3, 3.0, 0.4), 1.0);
            mantle.Step(Sim.Jump(), Dt);
            Assert.True(mantle.IsMantling);
            Assert.Throws<InvalidOperationException>(() => mantle.TakeItem(item));
            Assert.Equal(HoldKind.None, mantle.Hold);
        }

        // ---- A trace hand-over's peakY ----------------------------------------------------------------------------------

        [Fact]
        public void TraceHandOver_PeakYIsTheTopOfTheFallSoFar_L2030_L2036()
        {
            var t = new Trace();
            foreach (var (y, g) in new[] { (0.0, true), (0.0, true), (0.1, false), (0.3, false), (0.37, false), (0.33, false), (0.2, false) })
                t.Steps.Add(new TraceStep { Y = y, G = g, F = 1, Clip = g ? ClipNames.Run : ClipNames.JumpAir });
            Assert.Equal(0.37, TraceReplay.PeakYOf(t, 6));
            Assert.Equal(0.3, TraceReplay.PeakYOf(t, 3));
            Assert.Equal(0.0, TraceReplay.PeakYOf(t, 1));
            var s = TraceReplay.StateOf(t, 6, MotorConfig.Prototype());
            Assert.Equal(0.37, s.PeakY);
            Assert.Equal(ClipNames.JumpAir, s.Clip);
            Assert.False(s.Grounded);
        }
    }
}
