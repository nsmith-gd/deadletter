using System.Collections.Generic;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl02;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>DL-02 in the chapter replay (as <see cref="Dl02TraceTests"/>): the press's face, the box and the tube's letter, from <c>room</c> to the first step of DL-03.</summary>
    internal sealed class Dl02ChapterProbe : ChapterTraceProbe<Dl02ChapterProbe.S>
    {
        internal struct S
        {
            public double Press, BoxX, BoxBase;
            public string BoxState, Letter;
        }

        private PeriodicCrusher _press; private CarriedItem _box; private Dl02TubeLetter _letter;

        public override string Scene => "DL-02";
        public override int FirstStep => 3999;
        public override IReadOnlyList<string> KeyActs => new[] { "dl02.box:Clip" };

        public override void Bind(ChapterSim sim, Trace t)
        {
            var g = sim.Graph;
            _press = g.Get<PeriodicCrusher>("dl02.press"); _box = g.Get<CarriedItem>("dl02.box"); _letter = g.Get<Dl02TubeLetter>("dl02.tubeLetter");
        }

        protected override S Sample(ChapterSim sim) => new S
        {
            Press = _press.Face, BoxX = _box.X, BoxBase = _box.BaseY, BoxState = _box.State.ToString(), Letter = _letter.State.ToString(),
        };

        public override string ExpectedAct(Trace t, TraceStep p) => Dl02TraceTests.ExpectedAct(p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            var rows = run.Rows;
            int room = rows.FindIndex(w => w.P.Cp == "room"), exit = run.RowAfter(Scene);
            for (int k = room + 1; k <= exit; k++)
            {
                var p = rows[k].P; var w = Samples[k];
                Check(bad, p.I, "press face", p.Pf.Value, w.Press);
                Check(bad, p.I, "box.x", p.Bx.Value, w.BoxX);
                Check(bad, p.I, "box.base", p.Bb.Value, w.BoxBase);
                string bs = w.BoxState == "Carried" ? "carried" : w.BoxState.ToLowerInvariant();
                if (bs != p.Bs) bad.Add($"#{p.I} box.state {p.Bs} vs {w.BoxState}");
                if (w.Letter.ToLowerInvariant() != p.Tl) bad.Add($"#{p.I} tube letter {p.Tl} vs {w.Letter}");
            }
            Assert.Equal(5228, rows[exit].P.I);                                                 // DL-03's first step
            Assert.True(exit - room > 1000);
        }
    }
}
