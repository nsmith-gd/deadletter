using System.Collections.Generic;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl15;
using DeadLetter.Core.Scenes.Dl16;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-16 in Chapter 1's replay (<see cref="AttendanceChapterTraceTests"/>): his bow to the waiting figures (#14811,
    /// <c>crossing</c> #14852), the lever held while they cross (#14883–#16071), the rack full and latched, the
    /// counterweight up (<c>store</c> #16419), from DL-16's first step (#14788) to DL-16a's (#16782). The figures (DL-15's)
    /// are compared all along.
    /// </summary>
    internal sealed class Dl16ChapterProbe : ChapterTraceProbe<Dl16ChapterProbe.S>
    {
        internal struct S
        {
            public double Bridge, Cw, Ax, Bx;
            public bool Latched, Held;
            public int Stored;
            public string As, Bs;
        }

        private Dl16Bridge _bridge; private Latch _latch; private Dl16Lever _lever; private Rack _rack; private CounterweightRack _cw; private Dl15Figure _a, _b;

        public override string Scene => "DL-16";
        public override int FirstStep => 14788;
        public override IReadOnlyList<string> KeyActs => new[] { "quirk:AfterYou", "dl16.lever:Clip" };
        public override IReadOnlyList<(int step, string cue)> KeyCues => new[] { (0, "music:hush") };

        public override void Bind(ChapterSim sim, Trace t)
        {
            var g = sim.Graph;
            _bridge = g.Get<Dl16Bridge>("dl16.bridge"); _latch = g.Get<Latch>("dl16.latch"); _lever = g.Get<Dl16Lever>("dl16.lever");
            _rack = g.Get<Rack>("dl16.rack"); _cw = g.Get<CounterweightRack>("dl16.rackCW");
            _a = g.Get<Dl15Figure>("dl15.figA"); _b = g.Get<Dl15Figure>("dl15.figB");
        }

        protected override S Sample(ChapterSim sim) => new S
        {
            Bridge = _bridge.Position, Latched = _latch.Engaged, Held = _lever.Engaged, Stored = _rack.StoredCount, Cw = _cw.Progress,
            Ax = _a.X, As = Dl15ChapterProbe.Name(_a.State), Bx = _b.X, Bs = Dl15ChapterProbe.Name(_b.State),
        };

        public override string ExpectedAct(Trace t, TraceStep p) => AttendanceActs.Expected(p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            var rows = run.Rows;
            int to = run.RowAfter(Scene);
            for (int k = 0; k <= to; k++)
            {
                var p = rows[k].P; var w = Samples[k];
                Check(bad, p.I, "bridge", p.Br16.Value, w.Bridge);
                if (p.La16.Value != w.Latched) bad.Add($"#{p.I} latched {p.La16} vs {w.Latched}");
                if (p.He16.Value != w.Held) bad.Add($"#{p.I} held {p.He16} vs {w.Held}");
                if (p.Sn16.Value != w.Stored) bad.Add($"#{p.I} stored {p.Sn16} vs {w.Stored}");
                Check(bad, p.I, "cw", p.Cw16.Value, w.Cw);
                Check(bad, p.I, "A.x", p.Ax15.Value, w.Ax); Check(bad, p.I, "B.x", p.Bx15.Value, w.Bx);
                if (p.As15 != w.As || p.Bs15 != w.Bs) bad.Add($"#{p.I} figures {p.As15}/{p.Bs15} vs {w.As}/{w.Bs}");
            }
            Assert.Equal(16782, rows[to].P.I);
        }
    }
}
