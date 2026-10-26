using System;
using System.Collections.Generic;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Drives;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>Relays and pulse sequencers (§4.13e).</summary>
    public class RelayTests
    {
        private static PulseSequencer Relay() => new PulseSequencer("dl01.relay", PulseParams.Dl01Relay());

        [Theory]
        // set 168: lamp 0 on 168–198, lamp 1 on 180–198, lamp 2 on 192–198, then a 10-frame fade (L1543–L1546)
        [InlineData(0, 167.9, 0)] [InlineData(0, 168, 1)] [InlineData(0, 197.9, 1)] [InlineData(0, 203, 0.5)] [InlineData(0, 208, 0)]
        [InlineData(1, 179.9, 0)] [InlineData(1, 180, 1)] [InlineData(2, 191.9, 0)] [InlineData(2, 195, 1)] [InlineData(2, 206, 0.2)]
        // the first set is at 0.55 strength (RELAY_SETS, L332)
        [InlineData(0, 130, 0.55)] [InlineData(2, 155, 0.55 * 0.5)]
        // then every 144 frames from 480 (L1536)
        [InlineData(0, 470, 0)] [InlineData(0, 480, 1)] [InlineData(1, 480 + 144 * 3 + 12, 1)] [InlineData(2, 480 + 144 * 40 + 29, 1)]
        [InlineData(0, 480 + 144 * 40 + 100, 0)]
        public void Dl01Relay_LampWindows_L1538_L1548(int lamp, double frame, double value)
        {
            var r = Relay();
            Assert.Equal(value, r.ValueAtUnits(lamp, frame), 9);
        }

        [Fact]
        public void Dl01Relay_LampsClickAtTheCueFrames_L1585_L1588_L8511()
        {
            var r = Relay();
            var g = Mech.Graph(r);
            r.SetClock(0);                                        // the opening starts the scene clock (L8061)
            var lit = new List<(int lamp, double strength, double frame)>();
            for (int i = 0; i < 60 * 30; i++)                     // 30 s = 720 frames
            {
                g.Step(Mech.Dt, PlayerPose.Away);
                foreach (var e in Mech.Events(g))
                    if (e.Kind == MechanismEventKind.Event && e.Code == (int)PulseEvent.LampLit) lit.Add((e.Index, e.Value, r.Units));
            }
            double[] starts = { 120, 168, 336, 480, 624 };
            Assert.Equal(starts.Length * 3, lit.Count);
            for (int s = 0; s < starts.Length; s++)
                for (int i = 0; i < 3; i++)
                {
                    var e = lit[s * 3 + i];
                    Assert.Equal(i, e.lamp);
                    Assert.Equal(s == 0 ? 0.55 : 1.0, e.strength);
                    Assert.InRange(e.frame - (starts[s] + 12 * i), 0, 0.4 + 1e-9);
                }
        }

        [Fact]
        public void Dl01Relay_PulsingAndDark_AreLoggedStates()
        {
            var r = Relay();
            var g = Mech.Graph(r);
            r.SetClock(470);
            int n = Mech.RunUntil(g, () => Mech.Entered(g, "dl01.relay", PulseState.Pulsing));
            Assert.InRange(r.Units, 480, 480.4 + 1e-6);
            Assert.InRange(n, 25, 26);
            Mech.RunUntil(g, () => Mech.Entered(g, "dl01.relay", PulseState.Dark));
            Assert.InRange(r.Units, 520, 520.4 + 1e-6);                  // off at 510, faded by 520
        }

        [Fact]
        public void Dl01Relay_Calm_IsASoftSineBump_L1541()
        {
            var r = Relay();
            Assert.Equal(0.7, r.ValueAtUnits(0, 168 + 20, calm: true), 9);
            Assert.Equal(0.55 * 0.7 * Math.Sin(Math.PI * 10 / 40), r.ValueAtUnits(1, 132 + 10, calm: true), 9);
            Assert.Equal(0, r.ValueAtUnits(0, 168 + 40, calm: true), 9);
            var g = Mech.Graph(r);
            g.Calm = true;
            r.SetClock(168 + 20 - 0.4);
            Mech.Run(g, 1);
            Assert.Equal(0.7, r.Value(0), 6);
        }

        [Fact]
        public void Dl01Relay_ResetRaisesTheClockTo480_ButARespawnKeepsThePhase_L8095()
        {
            var r = Relay();
            var g = Mech.Graph(r);
            Assert.Equal(480, r.Units, 9);
            r.SetClock(1000);
            g.Reset(Mech.Cp("hall"));
            Assert.Equal(1000, r.Units, 9);
        }

        [Fact]
        public void AttRelays_SevenSecondCycle_PhasesTwoPointThreeApart_L6319()
        {
            var pump = new TestSource("dl17.pump");
            var r = new PulseSequencer("att.relays", PulseParams.AttRelays());
            var g = Mech.Graph("school", pump, r);
            Assert.Equal(4, r.LampCount);
            for (int step = 1; step <= 60 * 20; step++)
            {
                g.Step(Mech.Dt, PlayerPose.Away);
                double t = r.Seconds;
                for (int i = 0; i < 4; i++)
                {
                    double cyc = (t + i * 2.3) % 7;
                    if (Math.Abs(cyc) < 1e-6 || Math.Abs(cyc - 0.25) < 1e-6 || Math.Abs(cyc - 7) < 1e-6) continue;   // boundary
                    Assert.Equal(cyc < 0.25 ? 1.0 : 0.0, r.Value(i));
                }
            }
        }

        [Fact]
        public void AttRelays_PumpRelayBlinksWhileTheTankRefills_L6320()
        {
            var pump = new TestSource("dl17.pump");
            var r = new PulseSequencer("att.relays", PulseParams.AttRelays());
            var g = Mech.Graph("workshop", pump, r);
            pump.Engaged = true;
            int on = 0, off = 0;
            for (int i = 0; i < 120; i++)
            {
                g.Step(Mech.Dt, PlayerPose.Away);
                double cyc = (r.Seconds + 6.9) % 7;
                if (cyc < 0.25) continue;
                if (Math.Sin(r.Seconds * 6) > 0) { Assert.Equal(1.0, r.Value(3)); on++; }
                else { Assert.Equal(0.0, r.Value(3)); off++; }
            }
            Assert.True(on > 20 && off > 20);
        }

        [Fact]
        public void Relay_RestoredMidPulse_ContinuesBitIdentically()
        {
            var a = Relay();
            var ga = Mech.Graph(a);
            a.SetClock(495);
            Mech.Run(ga, 7);
            var b = Relay();
            var gb = Mech.Graph(b);
            gb.Restore(Mech.Snapshot(ga));
            for (int i = 0; i < 400; i++)
            {
                ga.Step(Mech.Dt, PlayerPose.Away);
                gb.Step(Mech.Dt, PlayerPose.Away);
                Assert.Equal(Mech.Dump(ga), Mech.Dump(gb));
                Assert.Equal(Mech.Events(ga).Count, Mech.Events(gb).Count);
            }
        }
    }
}
