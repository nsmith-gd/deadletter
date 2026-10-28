using System.Collections.Generic;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl14;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-14 in Chapter 1's replay (<see cref="AttendanceChapterTraceTests"/>): down the stair (<c>window</c> #3141), a wind
    /// with the pole through A's wheel (B down alone, the panel peels), the pole out (#4187), set down, a wind (they swap),
    /// the pole back up and through the wheel with A down (#5814), a wind (both down), up the ledges into the hatch and
    /// along the duct (<c>hatch14</c> #7886), from DL-14's first step (#3042) to DL-14a's (#8265).
    /// </summary>
    internal sealed class Dl14ChapterProbe : ChapterTraceProbe<Dl14ChapterProbe.S>
    {
        internal struct S
        {
            public double A, B, PoleX, PoleBase, Peel;
            public int Ta, Tb, Winds;
            public bool Jammed, Peeled, Rattle, Duct;
            public string Pole;
        }

        private PairedBlindDrive _blinds; private CarriedItem _pole; private Dl14Jam _jam; private Dl14Rules _rules;

        public override string Scene => "DL-14";
        public override int FirstStep => 3042;
        public override IReadOnlyList<string> KeyActs => new[] { "dl14.crank:Clip", "dl14.pole:Lift", "dl14.wheel:SetDown", "dl14.hatch:Along" };
        public override IReadOnlyList<(int step, string cue)> KeyCues => new[] { (0, "music:child") };

        public override void Bind(ChapterSim sim, Trace t)
        {
            var g = sim.Graph;
            _blinds = g.Get<PairedBlindDrive>("dl14.blinds"); _pole = g.Get<CarriedItem>("dl14.pole"); _jam = g.Get<Dl14Jam>("dl14.jam");
            _rules = (Dl14Rules)sim.RulesOf(sim.Def.Scene("DL-14"));
        }

        protected override S Sample(ChapterSim sim) => new S
        {
            A = _blinds.A, B = _blinds.B, Ta = (int)_blinds.TargetA, Tb = (int)_blinds.TargetB, Winds = _blinds.Winds,
            Jammed = _jam.Engaged, PoleX = _pole.X, PoleBase = _pole.BaseY, Pole = PoleName(_pole), Peel = _blinds.Peel, Peeled = _blinds.Peeled,
            Rattle = _blinds.Slipping, Duct = _rules.DuctTaken,
        };

        public override string ExpectedAct(Trace t, TraceStep p) => AttendanceActs.Expected(p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            var rows = run.Rows;
            int to = run.RowAfter(Scene);
            for (int k = 0; k <= to; k++)
            {
                var p = rows[k].P; var w = Samples[k];
                Check(bad, p.I, "blind.a", p.Ba14.Value, w.A);
                Check(bad, p.I, "blind.b", p.Bb14.Value, w.B);
                if (p.Ta14.Value != w.Ta || p.Tb14.Value != w.Tb) bad.Add($"#{p.I} targets {p.Ta14}/{p.Tb14} vs {w.Ta}/{w.Tb}");
                if (p.W14.Value != w.Winds) bad.Add($"#{p.I} winds {p.W14} vs {w.Winds}");
                if (p.J14.Value != w.Jammed) bad.Add($"#{p.I} jammed {p.J14} vs {w.Jammed}");
                Check(bad, p.I, "pole.x", p.Px14.Value, w.PoleX);
                Check(bad, p.I, "pole.base", p.Pb14.Value, w.PoleBase);
                if (p.Ps14 != w.Pole) bad.Add($"#{p.I} pole {p.Ps14} vs {w.Pole}");
                Check(bad, p.I, "peel", p.Pe14.Value, w.Peel);
                if (p.Pd14.Value != w.Peeled) bad.Add($"#{p.I} peeled {p.Pd14} vs {w.Peeled}");
                if (p.Rt14.Value != w.Rattle) bad.Add($"#{p.I} rattle {p.Rt14} vs {w.Rattle}");
                if (p.Du14.Value != w.Duct) bad.Add($"#{p.I} duct {p.Du14} vs {w.Duct}");
            }
            Assert.Equal(8265, rows[to].P.I);
        }

        private static string PoleName(CarriedItem c)
        {
            switch (c.State)
            {
                case ItemState.Placed: return "jam";
                case ItemState.Carried: return "carried";
                case ItemState.Floor: return "floor";
                default: return c.State.ToString();
            }
        }
    }
}
