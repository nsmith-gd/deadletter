using System.Collections.Generic;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Cycles;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-13 in Chapter 1's replay (<see cref="AttendanceChapterTraceTests"/>): the second figure pushed into the front seat
    /// (#1355–#1672), the lesson it starts, the brake pulled with all three steps out (#1930–#2010), the climb up the held
    /// steps to the gallery (<c>gallery13</c> #2826), from DL-13's first step (#1313) to DL-14's (#3042).
    /// </summary>
    internal sealed class Dl13ChapterProbe : ChapterTraceProbe<Dl13ChapterProbe.S>
    {
        internal struct S
        {
            public double FigX, T, Tree, S0, S1, S2;
            public bool On, Braked;
        }

        private Pushable _fig; private CycleClock _lesson; private CycleBrake _brake;

        public override string Scene => "DL-13";
        public override int FirstStep => 1313;
        public override IReadOnlyList<string> KeyActs => new[] { "dl13.figure:Clip", "dl13.brake:Clip" };
        public override IReadOnlyList<(int step, string cue)> KeyCues => new[] { (0, "sound:bell") };

        public override void Bind(ChapterSim sim, Trace t)
        {
            var g = sim.Graph;
            _fig = g.Get<Pushable>("dl13.figure"); _lesson = g.Get<CycleClock>("dl13.lesson"); _brake = g.Get<CycleBrake>("dl13.brake");
        }

        protected override S Sample(ChapterSim sim) => new S
        {
            FigX = _fig.X, On = _lesson.On, T = _lesson.Phase, Braked = _brake.Engaged, Tree = _lesson.Value(3),
            S0 = _lesson.Value(0), S1 = _lesson.Value(1), S2 = _lesson.Value(2),
        };

        public override string ExpectedAct(Trace t, TraceStep p) => AttendanceActs.Expected(p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            var rows = run.Rows;
            // From the first step: the lesson and the seat are the chapter's from the start, and still till DL-13.
            for (int k = 0; k <= run.RowAfter(Scene); k++)
            {
                var p = rows[k].P; var w = Samples[k];
                Check(bad, p.I, "fig2.x", p.F13x.Value, w.FigX);
                if (p.L13.Value != w.On) bad.Add($"#{p.I} lesson.on {p.L13} vs {w.On}");
                if (p.K13.Value != w.Braked) bad.Add($"#{p.I} braked {p.K13} vs {w.Braked}");
                Check(bad, p.I, "lesson.t", p.T13.Value, w.T);
                var st = p.Steps13();
                Check(bad, p.I, "step1", st[0], w.S0);
                Check(bad, p.I, "step2", st[1], w.S1);
                Check(bad, p.I, "step3", st[2], w.S2);
                Check(bad, p.I, "tree", p.Tr13.Value, w.Tree);
            }
            Assert.Equal(3042, rows[run.RowAfter(Scene)].P.I);
        }
    }
}
