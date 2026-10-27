using System;
using DeadLetter.Core.Lane;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Motor;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Core/Lane (§4.6): every probe of DL-01's lane against values worked out by hand from index.html (lines cited),
    /// and the composition rules for tables and contributors.
    /// </summary>
    public class LaneGeometryTests
    {
        private sealed class Dl01
        {
            public readonly MechanismGraph G;
            public readonly LaneGeometry Lane = new LaneGeometry();
            public readonly TippingBridge Cart;

            public Dl01(string checkpoint)
            {
                Cart = new TippingBridge("dl01.cart", TippingBridgeParams.Dl01Cart());
                G = Mech.Graph(checkpoint, new Latch("dl01.latch", LatchParams.Dl01Latch()), new Door("dl01.shutter", DoorParams.Dl01Shutter()), Cart);
                Lane.AddRegion(Dl01Lane.Region, Dl01Lane.Table());
                foreach (var c in Dl01Lane.Contributors(G)) Lane.AddContributor(Dl01Lane.Region, c);
            }
        }

        // ---- floorAt, L1716, L4138 -------------------------------------------------------------------------------------
        [Theory]
        [InlineData("start", 0.0, 0.0)]
        [InlineData("start", 6.6, 0.0)]          // the trench's edges are open: x > PIT.x0 && x < PIT.x1
        [InlineData("start", 6.61, -0.8)]
        [InlineData("start", 7.99, -0.8)]
        [InlineData("start", 8.0, 0.0)]
        [InlineData("hall", 6.61, -0.25)]        // the cart lies in it: PIT.y + CART1.h
        [InlineData("hall", 7.3, -0.25)]
        [InlineData("hall", 8.0, 0.0)]
        public void FloorAt_L1716_L4138(string cp, double x, double floor)
        {
            Assert.Equal(floor, new Dl01(cp).Lane.FloorAt(x), 12);
        }

        // ---- surfaceAt, L1719–L1723, L4143–L4146 ---------------------------------------------------------------------
        [Theory]
        [InlineData("start", 3.59, 0.0)]
        [InlineData("start", 3.6, 0.22)]         // STEP, edges closed (PLATFORMS, L1722)
        [InlineData("start", 4.4, 0.22)]
        [InlineData("start", 4.41, 0.0)]
        [InlineData("start", 5.24, 0.0)]
        [InlineData("start", 5.26, 0.55)]        // the cart on the floor at 5.9: |x − 5.9| ≤ 0.65 → 0.55
        [InlineData("start", 6.54, 0.55)]
        [InlineData("start", 6.56, 0.0)]
        [InlineData("start", 7.0, -0.8)]
        [InlineData("hall", 5.9, 0.0)]           // a bridge, not a box
        [InlineData("hall", 7.0, -0.25)]
        public void SurfaceAt_L1722_L4146(string cp, double x, double surface)
        {
            Assert.Equal(surface, new Dl01(cp).Lane.SurfaceAt(x), 12);
        }

        [Fact]
        public void SurfaceAt_TheFallingCartIsNeitherBoxNorBridge_L4146_L4757()
        {
            var s = new Dl01("start");
            s.Cart.MoveTo(6.33, 0);
            s.Cart.OnShoved();
            s.G.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(TippingBridgeState.Falling, s.Cart.State);
            Assert.Equal(0.0, s.Lane.SurfaceAt(6.0), 12);
            Assert.Equal(-0.8, s.Lane.SurfaceAt(7.0), 12);
            Mech.RunUntil(s.G, () => s.Cart.State == TippingBridgeState.Bridge);
            Assert.Equal(-0.25, s.Lane.SurfaceAt(7.0), 12);
        }

        [Fact]
        public void SurfaceAt_TheCartsBoxCountsOnlyInsideItsWindow_L4145()
        {
            var p = TippingBridgeParams.Dl01Cart();
            p.StartX = 4.2;                                           // box 3.55 … 4.85, window x > 4
            var cart = new TippingBridge("dl01.cart", p);
            Mech.Graph(cart);
            var lane = new LaneGeometry().AddRegion(1, new LaneTable());
            lane.AddContributor(1, new TippingBridgeLane(cart, p, Dl01Lane.CartWindowX0, Dl01Lane.CartWindowX1));
            Assert.Equal(0.0, lane.SurfaceAt(3.9), 12);
            Assert.Equal(0.55, lane.SurfaceAt(4.1), 12);
        }

        // ---- supportAt, L1737 -----------------------------------------------------------------------------------------
        [Theory]
        [InlineData("start", 3.55, 0.22)]        // the step under his front foot (3.63)
        [InlineData("start", 3.51, 0.0)]
        [InlineData("start", 6.62, 0.55)]        // the cart under his back foot (6.54)
        [InlineData("hall", 6.62, 0.0)]          // the floor behind him, the cart below
        [InlineData("hall", 7.3, -0.25)]
        public void SupportAt_IsTheHighestOfThreeProbes_L1737(string cp, double x, double support)
        {
            var s = new Dl01(cp);
            Assert.Equal(support, s.Lane.SupportAt(x), 12);
            Assert.Equal(support, LaneProbe.SupportAt(s.Lane, x, 0, LaneGeometry.Foot), 12);
        }

        // ---- ceilingAt: the depot's roof and the shutter's edge, L1621–L1642 ------------------------------------------
        [Theory]
        [InlineData("start", 0.1, 2.45)]         // x < 2.6, left of the shutter's pivot
        [InlineData("start", 1.1, 1.11)]         // 1.6 + (0.62 − 1.6)·0.9/1.8
        [InlineData("start", 2.0, 0.62)]         // both segments' end
        [InlineData("start", 2.6, 0.61)]         // 0.62 − 0.02·0.6/1.2
        [InlineData("start", 3.0, 0.60333333333)]
        [InlineData("start", 3.3, 0.31)]         // the foot: 0.6 − 0.58·0.5
        [InlineData("start", 3.5, 4.0)]          // past it: the roof
        [InlineData("shutter", 0.1, 2.45)]       // open, 15° about (0.2, 1.6): points (2.1923, 1.1193) (3.3566, 1.4105) (3.6999, 0.9021)
        [InlineData("shutter", 1.1, 1.38283504576)]
        [InlineData("shutter", 3.0, 1.32132322105)]
        [InlineData("shutter", 3.5, 1.19813173088)]
        [InlineData("shutter", 3.75, 4.0)]
        public void CeilingAt_RoofAndShutterPath_L1632_L1637(string cp, double x, double ceiling)
        {
            Assert.Equal(ceiling, new Dl01(cp).Lane.CeilingAt(x), 9);
        }

        [Fact]
        public void MinCeiling_SevenSamples_L1643()
        {
            var s = new Dl01("start");
            Assert.Equal(0.542, s.Lane.MinCeiling(2.88, 3.22), 9);                  // the last sample, on the foot's slope
            Assert.Equal(LaneProbe.MinCeiling(s.Lane, 2.88, 3.22, 0), s.Lane.MinCeiling(2.88, 3.22), 15);
        }

        [Fact]
        public void SwingingPathCeiling_FollowsItsAngle()
        {
            var angle = new TestSource("t.angle");
            var c = new SwingingPathCeiling(angle, Dl01Lane.ShutterPivotX, Dl01Lane.ShutterPivotY, Dl01Lane.ShutterPath);
            Assert.Equal(0.60333333333, c.Ceiling(3.0, 4), 9);
            angle.Position = 15;
            Assert.Equal(1.32132322105, c.Ceiling(3.0, 4), 9);
            angle.Position = 0;
            Assert.Equal(0.60333333333, c.Ceiling(3.0, 4), 9);
            Assert.Equal(0.2, c.Ceiling(3.0, 0.2), 12);                              // never raises a lower ceiling
        }

        // ---- limits, L1757, L1765 -------------------------------------------------------------------------------------
        [Theory]
        [InlineData("start", -0.3, 3.02)]        // the locked shutter: LOCKED_LIMIT
        [InlineData("shutter", -0.3, 11.45)]
        [InlineData("door", -0.3, 11.45)]
        public void Limits_TheLockedShutterHoldsHimAt3_02_L1765(string cp, double left, double right)
        {
            new Dl01(cp).Lane.Limits(3.0, 0, out double l, out double r);
            Assert.Equal(left, l);
            Assert.Equal(right, r);
        }

        [Fact]
        public void Ramps_GiveTheRampStepUp_OnlyInsideTheirZone_L6351()
        {
            Assert.False(new Dl01("start").Lane.IsRamp(3.6));
            var lane = new LaneGeometry().AddRegion(6, new LaneTable { Ramps = new[] { new LaneSpan(2, 3, 0, SpanEdges.ClosedOpen) } });
            Assert.True(lane.IsRamp(2));
            Assert.True(lane.IsRamp(2.99));
            Assert.False(lane.IsRamp(3));
            Assert.False(lane.IsRamp(1.99));
        }

        // ---- ledgeAhead, L1738–L1748 ----------------------------------------------------------------------------------
        [Fact]
        public void LedgeAhead_FindsTheStepAndTheCart_L1738()
        {
            var s = new Dl01("start");
            Assert.True(s.Lane.LedgeAhead(3.2, 0, 1, 0.5, 0.07, out var step));
            Assert.Equal(0.40, step.Distance, 12);                                     // 3.2 + 0.40 = 3.6
            Assert.Equal(0.22, step.Top, 12);
            Assert.True(s.Lane.LedgeAhead(4.8, 0, 1, 0.5, 0.07, out var cart));
            Assert.Equal(0.46, cart.Distance, 12);                                     // 5.26: |5.25 − 5.9| is 0.65 + 4e-16
            Assert.Equal(0.55, cart.Top, 12);
            Assert.True(s.Lane.LedgeAhead(4.8, 0, -1, 0.5, 0.07, out var back));       // facing left, the step's far edge at 4.4
            Assert.Equal(0.40, back.Distance, 12);
            Assert.Equal(0.22, back.Top, 12);
            Assert.False(s.Lane.LedgeAhead(4.4, 0.22, 1, 0.5, 0.07, out _));          // on the step: the cart (0.33 higher) is beyond 0.5
            Assert.False(s.Lane.LedgeAhead(1.0, 0, 1, 0.5, 0.07, out _));
        }

        // ---- composition ---------------------------------------------------------------------------------------------
        private sealed class Probe : LaneContributor
        {
            public double? FloorTo, SurfaceTo, CeilingTo, RightTo;
            public override double Floor(double x, double floor) => FloorTo ?? floor;
            public override double Surface(double x, double surface) => SurfaceTo.HasValue ? Math.Max(surface, SurfaceTo.Value) : surface;
            public override double Ceiling(double x, double ceiling) => CeilingTo ?? ceiling;
            public override void Limits(double x, double y, ref double left, ref double right) { if (RightTo.HasValue) right = Math.Min(right, RightTo.Value); }
        }

        [Fact]
        public void Contributors_ComeAfterTheTable_InRegistrationOrder()
        {
            var table = new LaneTable
            {
                Left = -1, Right = 10, Floor = 0,
                Floors = new[] { new LaneSpan(2, 4, -1, SpanEdges.Open), new LaneSpan(3, 5, -2, SpanEdges.Open) },   // first match wins
                Platforms = new[] { new LaneSpan(0, 1, 0.3, SpanEdges.Closed), new LaneSpan(0.5, 1, 0.5, SpanEdges.Closed) },
                Ceiling = 3, Ceilings = new[] { new LaneSpan(0, 1, 2, SpanEdges.Closed) },
            };
            var lane = new LaneGeometry().AddRegion(1, table);
            Assert.Equal(-1, lane.FloorAt(3.5));
            Assert.Equal(-2, lane.FloorAt(4.5));
            Assert.Equal(0.5, lane.SurfaceAt(0.75));
            Assert.Equal(0.3, lane.SurfaceAt(0.25));
            Assert.Equal(2, lane.CeilingAt(0.5));
            Assert.Equal(3, lane.CeilingAt(5));

            var a = new Probe { FloorTo = 1 };
            var b = new Probe { SurfaceTo = 1.5, CeilingTo = 2.5, RightTo = 4 };
            lane.AddContributor(1, a).AddContributor(1, b);
            Assert.Equal(1, lane.FloorAt(3.5));                                         // a floor override replaces the pit
            Assert.Equal(1.5, lane.SurfaceAt(3.5));                                     // the surface starts from the overridden floor
            Assert.Equal(2.5, lane.CeilingAt(0.5));                                     // a contributor may replace the ceiling (ceilingCh1)
            lane.Limits(0, 0, out double l, out double r);
            Assert.Equal(-1, l);
            Assert.Equal(4, r);
        }

        [Fact]
        public void Regions_SwitchTheWholeLane()
        {
            var lane = new LaneGeometry().AddRegion(1, new LaneTable { Floor = 0 }).AddRegion(2, new LaneTable { Floor = 1.6 });
            Assert.Equal(1, lane.Region);
            Assert.Equal(0, lane.FloorAt(5));
            lane.Region = 2;
            Assert.Equal(1.6, lane.FloorAt(5));
            Assert.True(lane.HasRegion(2));
            Assert.False(lane.HasRegion(3));
            Assert.Throws<ArgumentException>(() => lane.Region = 3);
            Assert.Throws<ArgumentException>(() => lane.AddRegion(2, new LaneTable()));
            Assert.Throws<ArgumentException>(() => lane.AddContributor(3, new Probe()));
            Assert.Throws<InvalidOperationException>(() => new LaneGeometry().FloorAt(0));
        }

        [Fact]
        public void Spans_KeepThePrototypesEdgeTests()
        {
            Assert.True(new LaneSpan(1, 2, 0, SpanEdges.Closed).Contains(1));
            Assert.False(new LaneSpan(1, 2, 0, SpanEdges.Open).Contains(1));
            Assert.True(new LaneSpan(1, 2, 0, SpanEdges.ClosedOpen).Contains(1));
            Assert.False(new LaneSpan(1, 2, 0, SpanEdges.ClosedOpen).Contains(2));
            Assert.True(new LaneSpan(1, 2, 0, SpanEdges.OpenClosed).Contains(2));
            Assert.Throws<ArgumentException>(() => new LaneSpan(2, 1, 0, SpanEdges.Closed));
        }
    }
}
