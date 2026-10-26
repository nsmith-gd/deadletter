using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Maths;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>Docks and cradles (§4.13b): the DL-04 cradle, the DL-16 rack, the DL-15 rail detents.</summary>
    public class DockTests
    {
        // ---- Cradle: DL-04 -------------------------------------------------------------------------------------------------

        private static (MechanismGraph g, TestBody courier, Cradle cradle, LoadPlate plate, PlateDoor door) Dl04(string cp = "room")
        {
            bool bay = Checkpoint.Prototype(cp).Past("bay");
            var courier = new TestBody("dl04.courier", bay ? 44.5 : 41.2);
            var cradle = new Cradle("dl04.cradle", CradleParams.Dl04Cradle());
            var plate = new LoadPlate("dl04.bayPlate", LoadPlateParams.Dl04BayPlate());
            var door = new PlateDoor("dl04.bayDoor", PlateDoorParams.Dl04BayDoor());
            return (Mech.Graph(cp, courier, cradle, plate, door), courier, cradle, plate, door);
        }

        [Fact]
        public void Cradle_NeverTakesItOutOfHisHands_NorFartherThan06_L4789_L4790()
        {
            var (g, courier, cradle, _, _) = Dl04();
            courier.Support = BodySupport.Pushed;
            courier.X = 44.4;
            Mech.Run(g, 10);
            Assert.Equal(CradleState.Free, cradle.State);
            Assert.Equal(44.4, cradle.Position);
            courier.Support = BodySupport.Floor;
            courier.X = 43.9;
            Mech.Run(g, 10);
            Assert.Equal(CradleState.Free, cradle.State);
            courier.X = 43.91;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.True(Mech.Entered(g, "dl04.cradle", CradleState.Drawing));
            Assert.True(Mech.Emitted(g, "dl04.cradle", CradleEvent.Take));
            Assert.True(cradle.Taken);
        }

        [Fact]
        public void Cradle_Reaches12s_DrawsFrom03s_Closes_SeatsAfter11s_L4792_L4808()
        {
            var (g, courier, cradle, _, door) = Dl04();
            courier.X = 44.0;
            g.Step(Mech.Dt, PlayerPose.Away);
            double x = 44.0, t = Mech.Dt;
            Assert.Equal(0.3 * Math.Sin(Math.PI * t / 1.2), cradle.ArmRad, 12);
            courier.X = 40;                                        // its own x no longer matters: the cradle has it
            int closing = -1, seated = -1;
            for (int k = 2; k <= 200 && seated < 0; k++)
            {
                g.Step(Mech.Dt, PlayerPose.Away);
                t += Mech.Dt;
                if (closing < 0)
                {
                    if (t > 0.3) x += (44.5 - x) * Math.Min(1, Mech.Dt * 3);
                    if (Mech.Entered(g, "dl04.cradle", CradleState.Closing)) { closing = k; Assert.Equal(44.5, cradle.Position); }
                    else Assert.Equal(x, cradle.Position, 12);
                }
                if (Mech.Entered(g, "dl04.cradle", CradleState.Seated)) { seated = k; Assert.True(Mech.Emitted(g, "dl04.cradle", CradleEvent.Seat)); }
            }
            Assert.InRange(closing, 72, 73);                       // t > 1.2
            Assert.InRange(seated - closing, 65, 66);               // t > 1.1, counted from the closing step (t = dt there)
            Assert.Equal(0, cradle.SeatedFor);
            Assert.True(cradle.Engaged);
            Assert.InRange(cradle.ArmRad, -0.558, -0.55);
            int open = Mech.RunUntil(g, () => door.Engaged);
            Assert.InRange(open, 131, 133);                         // the courier holds the door: 2.2 s
            Mech.Run(g, 60);
            Assert.Equal(0, cradle.ArmRad, 12);                     // lifted back by 0.15 + 1.2 s
            Assert.Equal(0.55, Cradle.SeatedLamp(cradle.SeatedFor));
        }

        [Theory]
        [InlineData(0.0, 0.05 * 0.4)] [InlineData(2.2, 0.55)] [InlineData(-1, 0.0)]
        public void Cradle_SeatedLampsFlicker22sThenHold_L4818(double t, double v)
        {
            Assert.Equal(v, Cradle.SeatedLamp(t), 12);
            Assert.Equal(0.6 * (0.4 + 0.6 * Smooth.Step(0.05 / 2.2)), Cradle.SeatedLamp(0.05), 12);
            Assert.Equal(0.05 * (0.4 + 0.6 * Smooth.Step(0.2 / 2.2)), Cradle.SeatedLamp(0.2), 12);   // sin(6.2) < 0.2
        }

        [Theory]
        [InlineData("room", CradleState.Free, 41.2, 0.0)]
        [InlineData("bay", CradleState.Seated, 44.5, 1.7)]
        [InlineData("tunnel", CradleState.Seated, 44.5, 1.7)]
        public void Cradle_ResetFromCheckpoint_L4096_L4097(string cp, CradleState state, double x, double door)
        {
            var (g, _, cradle, _, d) = Dl04(cp);
            Assert.Equal(state, cradle.State);
            Assert.Equal(x, cradle.Position);
            Assert.Equal(0, cradle.ArmRad);
            Assert.Equal(door, d.Position);
            Assert.Equal(0, g.Log.Count);
            Mech.Run(g, 30);
            Assert.Equal(0, cradle.ArmRad, 12);
            if (state == CradleState.Seated) Assert.Equal(0.55, Cradle.SeatedLamp(cradle.SeatedFor));
        }

        [Fact]
        public void Cradle_RestoredMidDraw_ContinuesIdentically()
        {
            var (a, ca, _, _, _) = Dl04();
            ca.X = 44.0;
            Mech.Run(a, 40);
            var (b, _, _, _, _) = Dl04("bay");
            PlateKit.RoundTrip(a, b, 200);
            Assert.True(b.Get<Cradle>("dl04.cradle").Engaged);
        }

        // ---- Rack: DL-16 ---------------------------------------------------------------------------------------------------

        private static (MechanismGraph g, TestBody a, TestBody b, Rack rack, Latch latch) Dl16(string cp = "crossing")
        {
            bool stored = Checkpoint.Prototype(cp).Past("store");
            var b = new TestBody("dl15.figB", stored ? 305.6 : 297.62);
            var a = new TestBody("dl15.figA", stored ? 305.6 : 296.82);
            var rack = new Rack("dl16.rack", RackParams.Dl16Rack());
            var latch = new Latch("dl16.latch", new LatchParams { Trigger = "dl16.rack", Threshold = 1, Delay = 1.2, ReleasedAfter = "store" });
            return (Mech.Graph(cp, b, a, rack, latch), a, b, rack, latch);
        }

        [Fact]
        public void Rack_TakesFiguresInArrivalOrder_OntoHooks_Over18s_L5753_L5762()
        {
            var (g, a, b, rack, _) = Dl16();
            b.X = 305.6 - 0.0011;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(0, rack.StoredCount);
            b.X = 305.6 - 0.001;
            g.Step(Mech.Dt, PlayerPose.Away);
            var e = PlateKit.Find(g, "dl16.rack", (int)RackEvent.Stored).Value;
            Assert.Equal(0, e.Index);                               // figure 0 (B) ...
            Assert.Equal(0, e.Value);                               // ... on hook 0
            Assert.True(Mech.Entered(g, "dl16.rack", RackState.Partial));
            Assert.Equal(0.5, rack.Position);
            Assert.Equal(Mech.Dt / 1.8, rack.Hang(0), 12);
            Assert.True(rack.IsStored(0));
            Assert.False(rack.IsStored(1));
            a.X = 305.7;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.True(Mech.Emitted(g, "dl16.rack", RackEvent.Full));
            Assert.Equal(1, rack.HookOf(1));
            Assert.True(rack.Engaged);
            int hung = Mech.RunUntil(g, () => rack.Hang(1) >= 1);
            Assert.InRange(hung, 106, 108);
        }

        [Fact]
        public void Rack_BothArriveTogether_FrontOneFirst_L5743()
        {
            var (g, a, b, rack, _) = Dl16();
            a.X = 305.8; b.X = 305.7;
            g.Step(Mech.Dt, PlayerPose.Away);
            Assert.Equal(1, rack.HookOf(0));                        // B
            Assert.Equal(0, rack.HookOf(1));                        // A, ahead
            Assert.Equal(1, PlateKit.Count(g, "dl16.rack", (int)RackEvent.Full));
        }

        [Fact]
        public void Rack_Full_LatchReleases12sLater_L5764()
        {
            var (g, a, b, rack, latch) = Dl16();
            a.X = b.X = 305.6;
            g.Step(Mech.Dt, PlayerPose.Away);
            int n = Mech.RunUntil(g, () => latch.Engaged);
            Assert.InRange(n, 72, 73);
        }

        [Theory]
        [InlineData("crossing", 0, false)]
        [InlineData("store", 2, true)]
        public void Rack_ResetFromCheckpoint_L5548_L5552(string cp, int stored, bool latched)
        {
            var (g, _, _, rack, latch) = Dl16(cp);
            Assert.Equal(stored, rack.StoredCount);
            Assert.Equal(latched, latch.Engaged);
            if (stored > 0) { Assert.Equal(0, rack.HookOf(0)); Assert.Equal(1, rack.HookOf(1)); Assert.Equal(1, rack.Hang(1)); }
            for (int k = 0; k < 5; k++) { g.Step(Mech.Dt, PlayerPose.Away); Assert.Empty(Mech.Events(g)); }
        }

        [Fact]
        public void Rack_RestoredMidHang_ContinuesIdentically()
        {
            var (a, fa, fb, _, _) = Dl16();
            fb.X = 305.6;
            Mech.Run(a, 20);
            fa.X = 305.6;
            Mech.Run(a, 10);
            var (b, _, _, _, _) = Dl16("store");
            PlateKit.RoundTrip(a, b, 150);
        }

        // ---- RailDetents: DL-15 --------------------------------------------------------------------------------------------

        [Theory]
        [InlineData(282.5, 278.6, 293.0, 281.9, 283.2)]
        [InlineData(283.2, 278.6, 293.0, 281.9, 284.6)]            // starting on a seat: the next one stops it
        [InlineData(283.21, 278.6, 293.0, 281.9, 284.6)]
        [InlineData(283.23, 278.6, 293.0, 283.2, 284.6)]
        [InlineData(286.0, 278.6, 293.0, 284.6, 293.0)]
        [InlineData(280.0, 278.6, 281.5, 278.6, 281.5)]            // the rail's own limit is nearer
        [InlineData(284.0, 284.2, 293.0, 284.2, 284.6)]
        [InlineData(284.0, 284.7, 293.0, 284.7, 284.7)]            // hi never below lo
        public void Detents_APushStopsAtTheFirstOneItReaches_L5569_L5573(double from, double lo, double hi, double wantLo, double wantHi)
        {
            RailDetents.Limit(RailDetents.Dl15, from, ref lo, ref hi);
            Assert.Equal(wantLo, lo);
            Assert.Equal(wantHi, hi);
        }
    }
}
