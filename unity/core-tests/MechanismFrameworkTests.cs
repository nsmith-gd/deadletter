using System;
using System.Collections.Generic;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Save;
using DeadLetter.Core.Simulation;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>The U-10 framework: IDs, checkpoints, graph order and links, the log, snapshots (§4.13l, §4.28).</summary>
    public class MechanismFrameworkTests
    {
        // ---- IDs and checkpoints ------------------------------------------------------------------------------------------

        [Theory]
        [InlineData("dl01.latch")] [InlineData("dl14a.nightLight")] [InlineData("att.relays")] [InlineData("dl09.cagePawl")] [InlineData("dl07.weight0")]
        public void MechanismId_AcceptsSection5Ids(string id)
        {
            Assert.True(MechanismId.IsValid(id));
            Assert.Equal(id, new MechanismId(id).ToString());
        }

        [Theory]
        [InlineData("")] [InlineData("dl01")] [InlineData("DL01.latch")] [InlineData("dl01.")] [InlineData(".latch")]
        [InlineData("dl01.la-tch")] [InlineData("a.b.c")] [InlineData("dl01.9x")] [InlineData("dl 01.x")]
        public void MechanismId_RejectsMalformed(string id)
        {
            Assert.False(MechanismId.IsValid(id));
            Assert.Throws<ArgumentException>(() => new MechanismId(id));
        }

        [Fact]
        public void MechanismId_IsOrdinalValueEquality_DefaultIsNone()
        {
            MechanismId a = "dl01.latch", b = new MechanismId("dl01." + "latch");
            Assert.Equal(a, b);
            Assert.True(a == b);
            Assert.Equal(a.GetHashCode(), b.GetHashCode());
            Assert.NotEqual(a, (MechanismId)"dl01.Latch");
            Assert.True(default(MechanismId).IsNone);
            Assert.True(((MechanismId)(string)null).IsNone);
        }

        [Fact]
        public void Checkpoint_PastFollowsCpOrder_L3976_L3979()
        {
            Assert.Equal(37, Checkpoint.PrototypeOrder.Length);
            var shutter = Mech.Cp("shutter");
            Assert.True(shutter.Past("start"));
            Assert.True(shutter.Past("shutter"));
            Assert.False(shutter.Past("hall"));
            Assert.False(shutter.Past(null));
            Assert.True(Mech.Cp("workshop").Past("latched"));
            Assert.Throws<ArgumentException>(() => shutter.Past("shuter"));
            Assert.Throws<ArgumentException>(() => Mech.Cp("nowhere"));
        }

        // ---- Graph: order, ticks, links -----------------------------------------------------------------------------------

        [Fact]
        public void Graph_StepsInAddOrder_AndStampsTicks()
        {
            var trace = new List<string>();
            var a = new Counter("t.a", trace);
            var b = new Counter("t.b", trace);
            var g = Mech.Graph(b, a);
            Mech.Run(g, 3);
            Assert.Equal(new[] { "t.b", "t.a", "t.b", "t.a", "t.b", "t.a" }, trace);
            Assert.Equal(new long[] { 0, 1, 2 }, a.Ticks);
            Assert.Equal(3, g.Tick);
        }

        [Fact]
        public void Read_SeesThisTick_ReadAnyOrder_SeesLastTick()
        {
            var early = new Probe("t.early", "t.src", anyOrder: true);
            var src = new Counter("t.src");
            var late = new Probe("t.late", "t.src");
            var g = Mech.Graph(early, src, late);
            Mech.Run(g, 3);
            Assert.Equal(new double[] { 1, 2, 3 }, late.Seen);
            Assert.Equal(new double[] { 0, 1, 2 }, early.Seen);
        }

        [Fact]
        public void Link_RejectsReadsOfLaterSources_MissingSources_AndWrongSignals()
        {
            var g1 = new MechanismGraph();
            g1.Add(new Probe("t.p", "t.src"));
            g1.Add(new Counter("t.src"));
            var ex = Assert.Throws<InvalidOperationException>(() => g1.Build());
            Assert.Contains("steps after it", ex.Message);

            var g2 = new MechanismGraph();
            g2.Add(new Probe("t.p", "t.missing"));
            Assert.Throws<InvalidOperationException>(() => g2.Build());

            var g3 = new MechanismGraph();
            g3.Add(new Latch("t.latch", LatchParams.Dl01Latch()));
            g3.Add(new Probe("t.p", "t.latch"));                  // a latch is not an IPositionSource
            Assert.Contains("does not implement", Assert.Throws<InvalidOperationException>(() => g3.Build()).Message);
        }

        [Fact]
        public void Graph_GuardsItsLifecycle()
        {
            var g = new MechanismGraph();
            g.Add(new Counter("t.a"));
            Assert.Throws<ArgumentException>(() => g.Add(new Counter("t.a")));
            Assert.Throws<InvalidOperationException>(() => g.Step(Mech.Dt, PlayerPose.Away));
            g.Build();
            Assert.Throws<InvalidOperationException>(() => g.Add(new Counter("t.b")));
            Assert.Throws<InvalidOperationException>(() => g.Build());
            Assert.IsType<Counter>(g.Get<Counter>("t.a"));
            Assert.Throws<InvalidCastException>(() => g.Get<Latch>("t.a"));
            Assert.False(g.TryGet<Counter>("t.zz", out _));
        }

        // ---- The log ------------------------------------------------------------------------------------------------------

        [Fact]
        public void Log_HoldsThisStepOnly_WithTickIndexAndValue()
        {
            var c = new Counter("t.c");
            var g = Mech.Graph(c);
            Mech.Run(g, 2);
            var e = Mech.Events(g);
            Assert.Equal(2, e.Count);
            Assert.Equal(MechanismEventKind.State, e[0].Kind);
            Assert.Equal(0, e[0].Code);                       // second step: back to state 0
            Assert.Equal(1, e[0].Tick);
            Assert.Equal(MechanismEventKind.Event, e[1].Kind);
            Assert.Equal(7, e[1].Code);
            Assert.Equal(3, e[1].Index);
            Assert.Equal(2.0, e[1].Value);
            Assert.True(g.Log.Has("t.c", MechanismEventKind.Event, 7));
            g.Reset(Mech.Cp());
            Assert.Equal(0, g.Log.Count);
        }

        [Fact]
        public void Enter_LogsOnlyChanges()
        {
            var src = new TestSource("t.src") { Position = 0 };
            var latch = new Latch("t.latch", new LatchParams { Trigger = "t.src", Threshold = 1 });
            var g = Mech.Graph(src, latch);
            Mech.Run(g, 1);
            Assert.Equal(0, g.Log.Count);
            src.Position = 1;
            Mech.Run(g, 1);
            Assert.True(Mech.Entered(g, "t.latch", LatchState.Released));
            Mech.Run(g, 1);
            Assert.Equal(0, g.Log.Count);
        }

        // ---- Snapshots ----------------------------------------------------------------------------------------------------

        [Fact]
        public void MemorySnapshot_RoundTripsExactly_AndIsStrict()
        {
            var s = new MemorySnapshot();
            s.WriteDouble("a", 0.1 + 0.2);
            s.WriteDouble("nan", double.NaN);
            s.WriteDouble("negz", -0.0);
            s.WriteLong("n", long.MinValue);
            s.WriteBool("b", true);
            Assert.Equal(0.1 + 0.2, s.ReadDouble("a"));
            Assert.True(double.IsNaN(s.ReadDouble("nan")));
            Assert.Equal(BitConverter.DoubleToInt64Bits(-0.0), BitConverter.DoubleToInt64Bits(s.ReadDouble("negz")));
            Assert.Equal(long.MinValue, s.ReadLong("n"));
            Assert.True(s.ReadBool("b"));
            Assert.Throws<KeyNotFoundException>(() => s.ReadDouble("missing"));
            Assert.Throws<InvalidOperationException>(() => s.ReadLong("a"));
            Assert.StartsWith("a=0.30000000000000004\nb=true\n", s.Dump());
        }

        [Fact]
        public void GraphSnapshot_KeysAreIdSlashField_AndRestoreRebuildsTheTick()
        {
            var g = Mech.Graph(new Counter("t.c"));
            Mech.Run(g, 5);
            var s = Mech.Snapshot(g);
            Assert.Equal(5, s.ReadLong("graph/tick"));
            Assert.Equal(5.0, s.ReadDouble("t.c/n"));
            Assert.True(s.Contains("t.c/state"));

            var c2 = new Counter("t.c");
            var g2 = Mech.Graph(c2);
            g2.Restore(s);
            Assert.Equal(5, g2.Tick);
            Assert.Equal(5.0, c2.Position);
            Assert.Equal(s.Dump(), Mech.Dump(g2));
        }

        // ---- FixedTick drives the graph -----------------------------------------------------------------------------------

        [Fact]
        public void FixedTick_DrivesTheGraph_TwoStepsPer30HzFrame()
        {
            var tick = new FixedTick(1.0 / 60.0);
            var c = new Counter("t.c");
            var g = Mech.Graph(c);
            for (int frame = 0; frame < 30; frame++)
            {
                int n = tick.Advance(1.0 / 30.0);
                for (int i = 0; i < n; i++) g.Step(tick.StepSeconds, PlayerPose.Away);
            }
            Assert.Equal(tick.TickCount, g.Tick);
            Assert.InRange(g.Tick, 59, 60);                       // 100 ns quantisation of 1/30 and 1/60
            Assert.Equal(g.Tick, (long)c.Position);
        }
    }
}
