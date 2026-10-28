using System.Collections.Generic;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl15;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-15 in Chapter 1's replay (<see cref="AttendanceChapterTraceTests"/>): onto the balcony (<c>sickbay</c> #12074), B
    /// pushed onto the lift (#12104), the lift down with it and him, B pushed to the first friend's place (#12763;
    /// <c>class6</c> #13101), A pushed back to the second (#13370), Mara's chair (#14305), the dismissal (#14443) and the
    /// figures' bow, from DL-15's first step (#12063) to DL-16's (#14788).
    /// </summary>
    internal sealed class Dl15ChapterProbe : ChapterTraceProbe<Dl15ChapterProbe.S>
    {
        internal struct S
        {
            public double Ax, Ab, Al, Bx, Bb, Bl, Lift, LiftV, Door;
            public string As, Bs, Lamps;
            public bool Seated, Dismissed;
        }

        private Dl15Figure _a, _b; private PupilLift _lift; private SeatRow _seats; private Dl15Chair _chair; private Door _door;

        public override string Scene => "DL-15";
        public override int FirstStep => 12063;
        public override IReadOnlyList<string> KeyActs => new[] { "Grab:Clip", "dl15.chair:Clip", "dl15.chair:SitUp" };
        public override IReadOnlyList<(int step, string cue)> KeyCues => new[] { (0, "music:child"), (0, "sound:bell") };

        public override void Bind(ChapterSim sim, Trace t)
        {
            var g = sim.Graph;
            _a = g.Get<Dl15Figure>("dl15.figA"); _b = g.Get<Dl15Figure>("dl15.figB"); _lift = g.Get<PupilLift>("dl15.lift");
            _seats = g.Get<SeatRow>("dl15.seats"); _chair = g.Get<Dl15Chair>("dl15.chair"); _door = g.Get<Door>("dl15.classDoor");
        }

        protected override S Sample(ChapterSim sim) => new S
        {
            Ax = _a.X, Ab = _a.Base, As = Name(_a.State), Al = _a.Lean, Bx = _b.X, Bb = _b.Base, Bs = Name(_b.State), Bl = _b.Lean,
            Lift = _lift.Y, LiftV = _lift.FloorVelocity, Lamps = (_seats.Lit(0) ? "1" : "0") + "," + (_seats.Lit(1) ? "1" : "0") + "," + (_seats.Lit(2) ? "1" : "0"),
            Seated = _chair.Engaged, Dismissed = _seats.Engaged, Door = _door.Position,
        };

        public override string ExpectedAct(Trace t, TraceStep p) => AttendanceActs.Expected(p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            var rows = run.Rows;
            int to = run.RowAfter(Scene);
            for (int k = 0; k <= to; k++)
            {
                var p = rows[k].P; var w = Samples[k];
                Check(bad, p.I, "A.x", p.Ax15.Value, w.Ax); Check(bad, p.I, "A.base", p.Ab15.Value, w.Ab); Check(bad, p.I, "A.lean", p.Al15.Value, w.Al);
                if (p.As15 != w.As) bad.Add($"#{p.I} A {p.As15} vs {w.As}");
                Check(bad, p.I, "B.x", p.Bx15.Value, w.Bx); Check(bad, p.I, "B.base", p.Bb15.Value, w.Bb); Check(bad, p.I, "B.lean", p.Bl15.Value, w.Bl);
                if (p.Bs15 != w.Bs) bad.Add($"#{p.I} B {p.Bs15} vs {w.Bs}");
                Check(bad, p.I, "lift", p.Li15.Value, w.Lift);
                Check(bad, p.I, "lift.v", p.Lv15.Value, w.LiftV);
                if (p.Lm15 != w.Lamps) bad.Add($"#{p.I} lamps {p.Lm15} vs {w.Lamps}");
                if (p.Se15.Value != w.Seated) bad.Add($"#{p.I} seated {p.Se15} vs {w.Seated}");
                if (p.Di15.Value != w.Dismissed) bad.Add($"#{p.I} dismissed {p.Di15} vs {w.Dismissed}");
                Check(bad, p.I, "door", p.Do15.Value, w.Door);
            }
            Assert.Equal(14788, rows[to].P.I);
        }

        internal static string Name(Dl15Figure.FigureState s) => s == Dl15Figure.FigureState.Free ? "free" : s == Dl15Figure.FigureState.Procession ? "procession" : "stored";
    }
}
