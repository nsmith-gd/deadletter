using System.Collections.Generic;
using DeadLetter.Core.Beings;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl14b;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-14b in Chapter 1's replay (<see cref="AttendanceChapterTraceTests"/>): through the dormitory door (<c>corridor</c>
    /// #10407), into niche A as the trolley passes (#10425–#10832), the figure nudged out of its bay (#11059), into the
    /// emptied bay while the trolley takes the figure back (#11339–#11751), up the stair, from DL-14b's first step (#10392)
    /// to DL-15's (#12063). The trolley patrols from the chapter's first step, so it is compared from there.
    /// </summary>
    internal sealed class Dl14bChapterProbe : ChapterTraceProbe<Dl14bChapterProbe.S>
    {
        internal struct S
        {
            public double Tx, Mt, FigX, Out;
            public int Dir;
            public string Mode, Fig;
            public bool Kept;
        }

        private EscortTrolley _trolley; private Dl14bFigure _fig;

        public override string Scene => "DL-14b";
        public override int FirstStep => 10392;
        public override IReadOnlyList<string> KeyActs => new[] { "dl14b.nicheA:Clip", "dl14b.figure:Nudge", "dl14b.bay:Clip" };
        public override IReadOnlyList<(int step, string cue)> KeyCues => new[] { (0, "voice:att_trolley") };

        public override void Bind(ChapterSim sim, Trace t)
        {
            _trolley = sim.Graph.Get<EscortTrolley>("dl14b.trolley"); _fig = sim.Graph.Get<Dl14bFigure>("dl14b.figure");
        }

        protected override S Sample(ChapterSim sim) => new S
        {
            Tx = _trolley.X, Dir = _trolley.Dir, Mode = ModeName(_trolley.State), Mt = _trolley.ModeTime,
            FigX = _fig.X, Fig = FigName(_fig.State), Out = _fig.Out, Kept = _fig.Kept,
        };

        public override string ExpectedAct(Trace t, TraceStep p) => AttendanceActs.Expected(p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            var rows = run.Rows;
            int to = run.RowAfter(Scene);
            for (int k = 0; k <= to; k++)
            {
                var p = rows[k].P; var w = Samples[k];
                Check(bad, p.I, "trolley.x", p.Tx14b.Value, w.Tx);
                if (p.Td14b.Value != w.Dir) bad.Add($"#{p.I} trolley.dir {p.Td14b} vs {w.Dir}");
                if (p.Tm14b != w.Mode) bad.Add($"#{p.I} trolley.mode {p.Tm14b} vs {w.Mode}");
                Check(bad, p.I, "trolley.mt", p.Tt14b.Value, w.Mt);
                Check(bad, p.I, "fig.x", p.Fx14b.Value, w.FigX);
                if (p.Fs14b != w.Fig) bad.Add($"#{p.I} fig {p.Fs14b} vs {w.Fig}");
                Check(bad, p.I, "fig.out", p.Fo14b.Value, w.Out);
                if (p.Fk14b.Value != w.Kept) bad.Add($"#{p.I} fig.kept {p.Fk14b} vs {w.Kept}");
            }
            Assert.Equal(12063, rows[to].P.I);
        }

        private static string ModeName(EscortState s)
        {
            switch (s)
            {
                case EscortState.Patrol: return "patrol";
                case EscortState.Turn: return "turn";
                case EscortState.Stop: return "stop";
                case EscortState.EscortFigure: return "escortFig";
                default: return "escortHim";
            }
        }

        private static string FigName(Dl14bFigureState s) => s == Dl14bFigureState.Bay ? "bay" : s == Dl14bFigureState.Rolling ? "rolling" : s == Dl14bFigureState.Free ? "free" : "escorted";
    }
}
