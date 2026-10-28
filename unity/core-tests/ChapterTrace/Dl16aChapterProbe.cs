using System.Collections.Generic;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Scenes;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-16a in Chapter 1's replay (<see cref="AttendanceChapterTraceTests"/>): <c>kitchen</c> (#16797), the call push
    /// (#16869) and the car down, into it, the bell (#17184) and the ride up to the passage (to #17471), the stair down, from
    /// DL-16a's first step (#16782) to DL-17's (#17898). The car is compared from the chapter's first step.
    /// </summary>
    internal sealed class Dl16aChapterProbe : ChapterTraceProbe<Dl16aChapterProbe.S>
    {
        internal struct S
        {
            public double H;
            public string Mode;
        }

        private Dumbwaiter _car;

        public override string Scene => "DL-16a";
        public override int FirstStep => 16782;
        public override IReadOnlyList<string> KeyActs => new[] { "dl16a.callPush:PressButtonHigh", "dl16a.car:PressButtonHigh", "dl16a.car:Ride" };

        public override void Bind(ChapterSim sim, Trace t) => _car = sim.Graph.Get<Dumbwaiter>("dl16a.car");

        protected override S Sample(ChapterSim sim) => new S { H = _car.H, Mode = ModeName(_car.State) };

        public override string ExpectedAct(Trace t, TraceStep p) => AttendanceActs.Expected(p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            var rows = run.Rows;
            int to = run.RowAfter(Scene);
            for (int k = 0; k <= to; k++)
            {
                var p = rows[k].P; var w = Samples[k];
                Check(bad, p.I, "car.h", p.H16a.Value, w.H);
                if (p.M16a != w.Mode) bad.Add($"#{p.I} car {p.M16a} vs {w.Mode}");
                if (p.Tin1_16a != "311.2,0,floor" || p.Tin2_16a != "311.45,0,floor") bad.Add($"#{p.I} tins {p.Tin1_16a} {p.Tin2_16a}");
            }
            Assert.Equal(17898, rows[to].P.I);
        }

        private static string ModeName(DumbwaiterState s)
        {
            switch (s)
            {
                case DumbwaiterState.Top: return "top";
                case DumbwaiterState.Down: return "down";
                case DumbwaiterState.Bottom: return "bottom";
                case DumbwaiterState.Rise: return "rise";
                default: return "shoot";
            }
        }
    }
}
