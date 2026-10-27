using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Motor;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>Bridges made by tipping (§4.13j): DL-01's cart into the trench, DL-11's duct into the flood.</summary>
    public class BridgeTests
    {
        private static (TippingBridge b, MechanismGraph g) Cart(string cp = "start")
        {
            var b = new TippingBridge("dl01.cart", TippingBridgeParams.Dl01Cart());
            return (b, Mech.Graph(cp, b));
        }

        private static (TippingBridge b, MechanismGraph g) Duct(string cp = "ringc")
        {
            var b = new TippingBridge("dl11.duct", TippingBridgeParams.Dl11Duct());
            return (b, Mech.Graph(cp, b));
        }

        [Fact]
        public void Cart_PushRange_AndGrip_L3885_L4274()
        {
            var (b, _) = Cart();
            Assert.Equal(5.9, b.Min);
            Assert.Equal(6.6 - 0.65 + 0.38, b.Max, 12);                          // PIT.x0 − half + 0.38
            Assert.Equal(0.97, b.Gap);
            Assert.Equal(0.55, b.Speed);
            Assert.Equal(0.2, b.BackReach);
            Assert.True(b.TipsIntoPit);
            Assert.Equal(TippingBridgeState.Free, b.State);
        }

        [Fact]
        public void Cart_LetGoAtTheLip_TipsIn_LandsAtDrop0_8_SettlesAt7_27_L4688_L4741_L4757()
        {
            var (b, g) = Cart();
            b.MoveTo(b.Max, 0.5);
            b.SetAtLip(true);
            Mech.Run(g, 1);
            Assert.Equal(TippingBridgeState.AtLip, b.State);
            b.OnReleased(true);
            Mech.Run(g, 1);
            Assert.True(Mech.Emitted(g, "dl01.cart", TippingBridgeEvent.Tip));
            Assert.Equal(TippingBridgeState.Falling, b.State);
            Assert.Equal(1.0 / 54, b.Drop, 12);                                  // advances on the tipping step (dt / 0.9)
            Assert.False(b.IsAvailable(default));
            int land = Mech.RunUntil(g, () => Mech.Emitted(g, "dl01.cart", TippingBridgeEvent.Land));
            Assert.Equal(43, land);                                              // drop ≥ 0.8 on the 44th step of the fall
            Assert.Equal(0.4, Mech.Events(g).Find(e => e.Code == (int)TippingBridgeEvent.Land).Value);
            double prevX = b.X;
            int settled = Mech.RunUntil(g, () => b.Engaged);
            Assert.InRange(settled, 10, 11);
            Assert.Equal(7.27, b.X, 12);
            Assert.Equal(-0.8, b.ViewY);
            Assert.Equal(7.27, prevX, 9);                                        // slid home by drop 0.75 (k = smooth(t / 0.75))
            Assert.False(Mech.Emitted(g, "dl01.cart", TippingBridgeEvent.Land));   // one thud
            Assert.False(Mech.Emitted(g, "dl01.cart", TippingBridgeEvent.Splash));
        }

        [Fact]
        public void Cart_TipInto_NoseDipsSlidesAndBounces_L4743_L4750()
        {
            var (b, g) = Cart();
            b.MoveTo(b.Max, 0);
            b.OnShoved();
            var dips = new List<double>();
            for (int i = 0; i < 53; i++) { Mech.Run(g, 1); dips.Add(b.DipRad); }
            Assert.Equal(TippingBridgeState.Falling, b.State);
            Assert.True(dips[26] < -0.45);                                      // nose down near t 0.5
            Assert.True(b.X > 7.2 && b.X <= 7.27);
            Assert.True(b.DipRad > 0);                                           // the small bounce after 0.85
        }

        [Fact]
        public void Cart_ReleasedAwayFromTheLip_DoesNotTip()
        {
            var (b, g) = Cart();
            b.MoveTo(6.1, 0.4);
            b.SetAtLip(false);
            b.OnReleased(false);
            Mech.Run(g, 60);
            Assert.Equal(TippingBridgeState.Free, b.State);
            Assert.Equal(6.1, b.X);
            Assert.True(b.IsAvailable(default));
        }

        [Fact]
        public void Cart_TrenchFloor_AndStrandedWithoutTheBridge_L4140_L4764()
        {
            var (b, g) = Cart();
            Assert.Equal(-0.8, b.SurfaceAt(7.0));
            Assert.True(double.IsNaN(b.SurfaceAt(6.5)));
            Mech.Run(g, 1, new PlayerPose(7.0, -0.8));
            Assert.True(Mech.Emitted(g, "dl01.cart", TippingBridgeEvent.Stranded));
            Assert.True(double.IsNaN(Mech.Events(g)[0].Value));                  // the trench: respawn, no way back
            Mech.Run(g, 1, new PlayerPose(6.65, -0.8));
            Assert.False(Mech.Emitted(g, "dl01.cart", TippingBridgeEvent.Stranded));   // within 0.1 of the edge
            Mech.Run(g, 1, new PlayerPose(7.0, -0.8, busy: true));
            Assert.False(Mech.Emitted(g, "dl01.cart", TippingBridgeEvent.Stranded));
            Mech.Run(g, 1, new PlayerPose(7.0, -0.78, grounded: false));                // still falling: game.grounded, L4764
            Assert.False(Mech.Emitted(g, "dl01.cart", TippingBridgeEvent.Stranded));
            var (b2, g2) = Cart("hall");
            Assert.Equal(-0.25, b2.SurfaceAt(7.0), 12);                           // PIT.y + CART1.h
            Mech.Run(g2, 1, new PlayerPose(7.0, -0.8));
            Assert.False(Mech.Emitted(g2, "dl01.cart", TippingBridgeEvent.Stranded));
        }

        [Theory]
        [InlineData("start", TippingBridgeState.Free, 5.9)] [InlineData("shutter", TippingBridgeState.Free, 5.9)]
        [InlineData("hall", TippingBridgeState.Bridge, 7.27)] [InlineData("door", TippingBridgeState.Bridge, 7.27)]
        public void Cart_ResetFromCheckpoint_L4094(string cp, TippingBridgeState state, double x)
        {
            var (b, g) = Cart();
            b.MoveTo(b.Max, 0); b.OnShoved(); Mech.Run(g, 20);
            g.Reset(Mech.Cp(cp));
            Assert.Equal(state, b.State);
            Assert.Equal(x, b.X, 12);
            Assert.Equal(0, b.Drop);
        }

        [Fact]
        public void Duct_SettlesAt149_85_TopAt0_01_ThudSplashAndNoise1_5_L4855()
        {
            var (b, g) = Duct();
            Assert.Equal(149.1 - 0.75 + 0.4, b.Max, 9);
            Assert.Equal(0.45, b.Speed);
            Assert.Equal(1.1, b.Gap);
            b.MoveTo(b.Max, 0);
            b.OnReleased(true);
            int n = Mech.RunUntil(g, () => b.Engaged);
            Assert.InRange(n, 54, 55);
            Assert.True(Mech.Emitted(g, "dl11.duct", TippingBridgeEvent.Land));
            Assert.True(Mech.Emitted(g, "dl11.duct", TippingBridgeEvent.Splash));
            Assert.Equal(1.5, Mech.Events(g).Find(e => e.Code == (int)TippingBridgeEvent.Splash).Value);
            Assert.Equal(149.85, b.X, 9);
            Assert.Equal(0.01, b.SurfaceAt(150.0), 12);
        }

        [Fact]
        public void Duct_WaterTurnsHimBackTo148_75_L4860_L4862()
        {
            var (b, g) = Duct();
            Mech.Run(g, 1, new PlayerPose(149.0, 0));                            // x + HALF·0.6 > 149.1
            Assert.True(Mech.Emitted(g, "dl11.duct", TippingBridgeEvent.Stranded));
            Assert.Equal(148.75, Mech.Events(g)[0].Value, 9);
            Mech.Run(g, 1, new PlayerPose(148.99, 0));
            Assert.False(Mech.Emitted(g, "dl11.duct", TippingBridgeEvent.Stranded));
            var (_, g2) = Duct("bedroom");
            Mech.Run(g2, 1, new PlayerPose(149.5, 0.01));
            Assert.False(Mech.Emitted(g2, "dl11.duct", TippingBridgeEvent.Stranded));
        }

        [Fact]
        public void Cart_PushedByTheMotor_ToTheLip_AndShovedIn_L4683_L4715()
        {
            var (b, g) = Cart();
            var resolver = new InteractionResolver();
            resolver.Register(b);
            var m = Sim.Make(BoxWorld.Flat(0, 20), 4.93, 0, resolver);
            Assert.True(m.PreviewUse(out var c));
            Assert.Same(b, c.Target);
            void Step(MotorInput i) { m.Step(i, Mech.Dt); g.Step(Mech.Dt, Mech.Pose(m)); }
            Step(Sim.Use());
            for (int i = 0; i < 60 && m.Hold != HoldKind.Push; i++) Step(Sim.Move(0));
            Assert.Equal(HoldKind.Push, m.Hold);
            int tip = -1;
            bool atLip = false;
            for (int i = 0; i < 600 && tip < 0; i++)
            {
                Step(Sim.Move(1));
                atLip |= b.State == TippingBridgeState.AtLip;
                if (Mech.Emitted(g, "dl01.cart", TippingBridgeEvent.Tip)) tip = i;
            }
            Assert.True(atLip);
            Assert.True(tip > 0);
            Assert.Equal(HoldKind.None, m.Hold);
            for (int i = 0; i < 120; i++) Step(Sim.Move(0));
            Assert.Equal(TippingBridgeState.Bridge, b.State);
            Assert.Equal(7.27, b.X, 12);
        }

        [Fact]
        public void Cart_RestoredMidFall_ContinuesBitIdentically()
        {
            var (a, ga) = Cart();
            a.MoveTo(a.Max, 0); a.OnShoved();
            Mech.Run(ga, 25);
            var (b, gb) = Cart("hall");
            gb.Restore(Mech.Snapshot(ga));
            Assert.Equal(Mech.Dump(ga), Mech.Dump(gb));
            for (int i = 0; i < 60; i++)
            {
                Mech.Run(ga, 1); Mech.Run(gb, 1);
                Assert.Equal(Mech.Dump(ga), Mech.Dump(gb));
                Assert.Equal(Mech.Events(ga).Count, Mech.Events(gb).Count);
            }
            Assert.True(b.Engaged);
        }
    }
}
