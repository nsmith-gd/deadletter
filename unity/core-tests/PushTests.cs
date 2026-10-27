using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Push;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Core/Push (port_architecture §2, §4.11): <see cref="Pushable"/>, <see cref="PushTwin"/>, <see cref="TipIntoPit"/>,
    /// <see cref="Detents"/>. DL-03's trolley is the worked case (L321–L325, L2255–L2258, L2329–L2348); the pit and the
    /// detents are checked against the prototype's DL-01 cart and DL-15 figures.
    /// </summary>
    public class PushTests
    {
        private const double Dt = Mech.Dt;
        private const double PlateMid = (13 + 15.8 + (13 + 16.55)) / 2;

        private static (MechanismGraph g, Pushable trolley, TestBody weight) Dl03(string cp = "weighroom", double weightX = 25.62,
            BodySupport ws = BodySupport.Floor)
        {
            var trolley = new Pushable("dl03.trolley", PushableParams.Dl03Trolley());
            var weight = new TestBody("dl03.weight", weightX, ws);
            return (Mech.Graph(cp, trolley, weight), trolley, weight);
        }

        private static InteractionQuery At(double x, int facing = 1, double y = 0)
            => new InteractionQuery(x, y, 0, facing, true, false, HoldKind.None, null, null);

        // ---- Pushable: DL-03's trolley -------------------------------------------------------------------------------------
        [Fact]
        public void Dl03Trolley_Data_L321_L325()
        {
            var p = PushableParams.Dl03Trolley();
            Assert.Equal(27.55, p.StartX, 12);
            Assert.Equal(25.44, p.Min, 12);                       // ROOM_X0 + 0.06 + TROLLEY_HALF
            Assert.Equal(29.97, p.Max, 12);                       // GATE_X − 0.35 − TROLLEY_HALF
            Assert.Equal(0.62, p.Gap);
            Assert.Equal(3, p.Accel);
            Assert.Equal(29.175, p.ParkedX, 12);
        }

        [Theory]
        [InlineData("weighroom", 27.55)]
        [InlineData("solved", 29.175)]
        [InlineData("bay", 29.175)]
        public void Reset_TrolleyXOrParkedOnThePlate_L8026(string cp, double x)
        {
            var (_, t, _) = Dl03(cp);
            Assert.Equal(x, t.X, 12);
            Assert.Equal(PushableState.Free, t.State);
            Assert.False(t.Held);
            Assert.Equal(BodySupport.Floor, t.Support);
        }

        /// <summary>It stops 0.39 short of the weight standing on the floor, either way; not of the weight riding it (L2343–L2346).</summary>
        [Theory]
        [InlineData(28.5, BodySupport.Floor, 25.44, 28.5 - 0.39)]
        [InlineData(25.62, BodySupport.Floor, 25.62 + 0.39, 29.97)]
        [InlineData(26.0, BodySupport.Carried, 25.44, 29.97)]
        [InlineData(27.40, BodySupport.Carrier, 25.44, 29.97)]
        public void Range_StopsAgainstTheWeightOnTheFloor_L2343(double wx, BodySupport ws, double min, double max)
        {
            var (_, t, _) = Dl03(weightX: wx, ws: ws);
            Assert.Equal(min, t.Min, 12);
            Assert.Equal(max, t.Max, 12);
        }

        [Fact]
        public void Speed_055_042WithTheWeightOnIt_L2330()
        {
            var (_, t, w) = Dl03();
            Assert.Equal(0.55, t.Speed);
            Assert.False(t.Loaded);
            w.Support = BodySupport.Carrier; w.CarrierX = t.X;
            Assert.Equal(0.42, t.Speed);
            Assert.True(t.Loaded);
        }

        [Fact]
        public void MoveTo_HoldsItUntilLetGo_VelocityZeroOnce_L2347_L2369()
        {
            var (g, t, _) = Dl03();
            t.MoveTo(27.56, 0.6);
            Assert.True(t.Held);
            Assert.Equal(BodySupport.Pushed, t.Support);
            g.Step(Dt, PlayerPose.Away);
            Assert.Equal(0.6, t.Velocity);
            g.Step(Dt, PlayerPose.Away);                          // no move this step (not held by the motor any more)
            Assert.Equal(0, t.Velocity);
            t.OnReleased(false);
            Assert.False(t.Held);
            Assert.Equal(27.56, t.X);
            Assert.Equal(PushableState.Free, t.State);
        }

        [Fact]
        public void CanStandAt_GatesEachFace_AtItsOwnStandPoint_L2257()
        {
            var (_, t, _) = Dl03();
            var twin = new PushTwin(t);
            var asked = new List<double>();
            t.CanStandAt = x => { asked.Add(x); return x < 27.0; };
            Assert.True(t.IsAvailable(At(26.93)));
            Assert.False(twin.IsAvailable(At(28.17, -1)));
            Assert.Equal(new[] { 27.55 - 0.62, 27.55 + 0.62 }, asked);
        }

        // ---- PushTwin ------------------------------------------------------------------------------------------------------
        [Fact]
        public void Twin_IsTheSameTrolleyFromTheOtherEnd()
        {
            var (_, t, w) = Dl03();
            var twin = new PushTwin(t);
            Assert.Equal(-1, twin.Side);
            Assert.Equal(t.X, twin.X);
            Assert.Equal(t.Gap, twin.Gap);
            Assert.Equal(t.Max, twin.Max);
            twin.MoveTo(27.40, -0.3);
            Assert.Equal(27.40, t.X);
            Assert.True(t.Held);
            w.Support = BodySupport.Carrier;
            Assert.Equal(0.42, twin.Speed);
            Assert.Same(t, twin.Base);
            Assert.Equal(0.06, new PushTwin(t, forwardReach: 0.06).ForwardReach);   // bodyAlt.fwd, L4295
            Assert.Equal(0.34, twin.ForwardReach);
        }

        /// <summary>
        /// <c>nearUse2</c> (L2255–L2258): grabL from 0.62 left of its centre, grabR from 0.62 right, within 0.34 of the stand
        /// point; between the two, neither.
        /// </summary>
        [Theory]
        [InlineData(26.93, 1, +1, 26.93)]
        [InlineData(27.10, 1, +1, 26.93)]
        [InlineData(26.60, 1, +1, 26.93)]
        [InlineData(28.17, -1, -1, 28.17)]
        [InlineData(27.90, -1, -1, 28.17)]
        [InlineData(27.55, 1, 0, 0)]
        [InlineData(26.58, 1, 0, 0)]
        public void Resolver_OffersTheFaceHeStandsBy_L2255_L2258(double x, int facing, int side, double stand)
        {
            var (_, t, _) = Dl03();
            var r = new InteractionResolver();
            r.Register(t);
            r.Register(new PushTwin(t));
            bool found = r.Resolve(At(x, facing), out var c);
            Assert.Equal(side != 0, found);
            if (!found) return;
            Assert.Equal(Verb.Grab, c.Verb);
            Assert.Equal(side, ((IPushable)c.Target).Side);
            Assert.Equal(stand, c.StandX, 12);
            Assert.Equal(side, c.Face);
        }

        [Fact]
        public void Twin_RefusedForAThingThatTipsIntoAPit_L4286()
            => Assert.Throws<ArgumentException>(() => new PushTwin(new Pushable("t.cart", Cart())));

        // ---- TipIntoPit ----------------------------------------------------------------------------------------------------
        private static PushableParams Cart() => new PushableParams
        {
            StartX = 5.9, Side = 1, Gap = 0.97, Speed = 0.55, BackReach = 0.2, Min = 5.9, Max = TipParams.Dl01Cart().LipX,
            Pit = TipParams.Dl01Cart(), ParkedAfter = "hall", ParkedState = PushableState.Settled, Half = 0.65, Top = 0.55,
        };

        /// <summary>The same cart through Bridges/TippingBridge and Push/Pushable: let go at the lip, it falls the same way, step for step.</summary>
        [Fact]
        public void TipIntoPit_FallsAsTippingBridgeDoes_StepForStep_L4739_L4757()
        {
            var cart = new Pushable("t.cart", Cart());
            var bridge = new TippingBridge("t.bridge", TippingBridgeParams.Dl01Cart());
            var g = Mech.Graph("start", cart, bridge);
            Assert.Equal(bridge.Max, cart.Max, 12);
            Assert.Equal(6.33, cart.Max, 12);
            cart.MoveTo(cart.Max, 0.5); bridge.MoveTo(bridge.Max, 0.5);
            cart.SetAtLip(true); bridge.SetAtLip(true);
            g.Step(Dt, PlayerPose.Away);
            Assert.Equal(PushableState.AtLip, cart.State);
            cart.OnReleased(true); bridge.OnReleased(true);
            int landedCart = -1, landedBridge = -1;
            for (int i = 0; i < 70; i++)
            {
                g.Step(Dt, PlayerPose.Away);
                Assert.Equal(bridge.X, cart.X, 12);
                Assert.Equal(bridge.Drop, cart.Tip.Drop, 12);
                Assert.Equal(bridge.ViewY, cart.Tip.ViewY, 12);
                Assert.Equal(bridge.DipRad, cart.Tip.DipRad, 12);
                if (landedCart < 0 && Mech.Emitted(g, "t.cart", PushableEvent.Land)) landedCart = i;
                if (landedBridge < 0 && Mech.Emitted(g, "t.bridge", TippingBridgeEvent.Land)) landedBridge = i;
                Assert.Equal(bridge.State == TippingBridgeState.Bridge, cart.State == PushableState.Settled);
            }
            Assert.Equal(landedBridge, landedCart);
            Assert.Equal(PushableState.Settled, cart.State);
            Assert.Equal(7.27, cart.X, 12);
            Assert.True(cart.Engaged);
            Assert.Equal(BodySupport.Away, cart.Support);
        }

        [Fact]
        public void TipIntoPit_ShoveTips_ReleaseAwayFromTheLipDoesNot_L4688_L4712()
        {
            var cart = new Pushable("t.cart", Cart());
            var g = Mech.Graph("start", cart);
            cart.MoveTo(6.0, 0.3);
            cart.OnReleased(false);
            g.Step(Dt, PlayerPose.Away);
            Assert.Equal(PushableState.Free, cart.State);
            cart.MoveTo(cart.Max, 0.3);
            cart.SetAtLip(true);
            cart.OnShoved();
            g.Step(Dt, PlayerPose.Away);
            Assert.Equal(PushableState.Falling, cart.State);
            Assert.True(Mech.Emitted(g, "t.cart", PushableEvent.Tip));
        }

        [Fact]
        public void TipIntoPit_SettledFromItsCheckpoint_L4094()
        {
            var cart = new Pushable("t.cart", Cart());
            Mech.Graph("hall", cart);
            Assert.Equal(PushableState.Settled, cart.State);
            Assert.Equal(7.27, cart.X, 12);
            Assert.False(cart.IsAvailable(At(6.3)));
        }

        // ---- Detents -------------------------------------------------------------------------------------------------------
        /// <summary><c>figRange15</c> (L5569–L5573): the first detent past where he took hold, either way; one within 0.02 does not stop it.</summary>
        [Theory]
        [InlineData(283.0, 280.0, 290.0, 280.0, 283.2)]
        [InlineData(283.2, 280.0, 290.0, 280.0, 284.6)]
        [InlineData(283.21, 280.0, 290.0, 280.0, 284.6)]
        [InlineData(283.9, 280.0, 290.0, 283.2, 284.6)]
        [InlineData(285.0, 280.0, 290.0, 284.6, 290.0)]
        [InlineData(283.9, 284.0, 290.0, 284.0, 284.6)]
        [InlineData(283.9, 285.0, 284.8, 285.0, 285.0)]
        public void Detents_StopAtTheNextOneEitherWay_L5569_L5573(double from, double lo0, double hi0, double lo, double hi)
        {
            double a = lo0, b = hi0;
            Detents.Clamp(new[] { 283.2, 284.6 }, from, ref a, ref b);
            Assert.Equal(lo, a, 12);
            Assert.Equal(hi, b, 12);
        }

        [Fact]
        public void Detents_MeasuredFromWhereHeTookHold()
        {
            var stool = new Pushable("t.stool", new PushableParams
            {
                StartX = 310.45, Side = 1, Gap = 0.5, Speed = 0.4, Min = 310.45, Max = 312.2, Detents = new[] { 311.3 },
            });
            Mech.Graph("start", stool);
            Assert.True(stool.HasDetents);
            Assert.Equal(311.3, stool.Max, 12);
            stool.MoveTo(311.0, 0.4);                               // held from 310.45: the detent ahead still holds it
            Assert.Equal(311.3, stool.Max, 12);
            stool.MoveTo(311.3, 0.4);
            stool.OnReleased(false);                                // the motor lets go at the detent
            Assert.Equal(312.2, stool.Max, 12);                     // grabbed again there, it goes on to the end
            Assert.Equal(310.45, stool.Min, 12);                    // or back to the start: the detent it stands on does not hold it
        }

        [Fact]
        public void Params_RejectMisorderedDetents_AndAPitWithDetents()
        {
            Assert.Throws<ArgumentException>(() => new Pushable("t.a", new PushableParams { Gap = 1, Max = 2, Detents = new[] { 1.5, 1.0 } }));
            var p = Cart(); p.Detents = new[] { 6.0 };
            Assert.Throws<ArgumentException>(() => new Pushable("t.b", p));
        }

        // ---- Docking -------------------------------------------------------------------------------------------------------
        /// <summary>At the end of its travel the motor lets go; the courier docks in its cradle there (L4723–L4729).</summary>
        [Fact]
        public void Dock_AtTheEndOfItsTravel_L4723()
        {
            var courier = new Pushable("t.courier", new PushableParams
            {
                StartX = 41.2, Side = -1, Gap = 0.67, Speed = 0.22, Min = 41.2, Max = 44.5, DockAt = 44.5, Z = 0.35,
            });
            var g = Mech.Graph("start", courier);
            courier.MoveTo(43.0, 0.2);
            courier.OnReleased(false);
            courier.OnTravelEnd();
            g.Step(Dt, PlayerPose.Away);
            Assert.Equal(PushableState.Free, courier.State);
            courier.MoveTo(44.5, 0.2);
            courier.OnReleased(false);
            courier.OnTravelEnd();
            g.Step(Dt, PlayerPose.Away);
            Assert.Equal(PushableState.Docked, courier.State);
            Assert.True(courier.Engaged);
            Assert.True(Mech.Emitted(g, "t.courier", PushableEvent.Dock));
            Assert.False(courier.IsAvailable(At(44.5 + 0.67)));
        }

        // ---- Snapshot ------------------------------------------------------------------------------------------------------
        [Fact]
        public void SnapshotMidFall_RestoresAndContinuesBitIdentically()
        {
            var a = new Pushable("t.cart", Cart());
            var ga = Mech.Graph("start", a);
            a.MoveTo(a.Max, 0.4); a.SetAtLip(true);
            ga.Step(Dt, PlayerPose.Away);
            a.OnReleased(true);
            Mech.Run(ga, 20);
            var b = new Pushable("t.cart", Cart());
            var gb = Mech.Graph("hall", b);
            PlateKit.RoundTrip(ga, gb, 60);
            Assert.Equal(PushableState.Settled, b.State);
        }

        [Fact]
        public void SnapshotHeld_RestoresWhereHeTookHold()
        {
            var (ga, a, _) = Dl03();
            a.MoveTo(27.6, 0.5);
            ga.Step(Dt, PlayerPose.Away);
            var (gb, b, _) = Dl03("solved");
            gb.Restore(Mech.Snapshot(ga));
            Assert.Equal(Mech.Dump(ga), Mech.Dump(gb));
            Assert.True(b.Held);
            Assert.Equal(27.6, b.X);
        }

        /// <summary>
        /// DL-08's goods trolley: its travel ends at the pan's buffer stop (84.5) until the pawl holds the platform, then at
        /// the far landing's rail (88.22), read as the pawl is now (L2340); from <c>latched</c> it is parked there (L4123).
        /// </summary>
        [Fact]
        public void GoodsTrolley_TravelEndsAtTheBuffer_UntilThePawlIsSet_ThenAtTheRail_L2340_L4123()
        {
            var pawl = new TestSource("dl08.pawl");
            var t = new Pushable("dl08.trolley", PushableParams.Dl08Trolley());
            Mech.Graph("goods", t, pawl);
            Assert.Equal(82.5, t.X, 12);
            Assert.Equal(81.95, t.Min, 12);
            Assert.Equal(84.5, t.Max, 12);
            pawl.Engaged = true;
            Assert.Equal(88.22, t.Max, 12);
            var parked = new Pushable("dl08.trolley", PushableParams.Dl08Trolley());
            Mech.Graph("latched", parked, new TestSource("dl08.pawl") { Engaged = true });
            Assert.Equal(88.22, parked.X, 12);
            Assert.False(t.LetGoAtMax);
            Assert.Equal(1.3, t.Accel);
            var bad = PushableParams.Dl08Trolley();
            bad.ExtendedBy = "dl08.nothing";
            Assert.ThrowsAny<Exception>(() => Mech.Graph("goods", new Pushable("dl08.trolley", bad)));
        }
    }
}
