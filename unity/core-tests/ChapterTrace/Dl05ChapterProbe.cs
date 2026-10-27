using System.Collections.Generic;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>DL-05 in the chapter replay (as <see cref="Dl05TraceTests"/>): the drum, the body, the weigh-in, served, the hatch and the flag on every step DL-05 records them.</summary>
    internal sealed class Dl05ChapterProbe : ChapterTraceProbe<Dl05ChapterProbe.S>
    {
        internal struct S
        {
            public double DrumX, BodyX, W, Needle, Dip, Twitch, Hatch, Flag;
            public bool Served;
            public string DrumState, BodyState, Reading;
        }

        private Pushable _drum, _body; private WeighScale _scale; private Door _hatch, _flag;

        public override string Scene => "DL-05";
        public override int FirstStep => 9868;
        public override IReadOnlyList<string> KeyActs => new[] { "dl05.body:Hesitate", "quirk:Pat" };

        public override void Bind(ChapterSim sim, Trace t)
        {
            var g = sim.Graph;
            _drum = g.Get<Pushable>("dl05.drum"); _body = g.Get<Pushable>("dl05.body");
            _scale = g.Get<WeighScale>("dl05.weighIn"); _hatch = g.Get<Door>("dl05.hatch"); _flag = g.Get<Door>("dl05.servedFlag");
        }

        protected override S Sample(ChapterSim sim) => new S
        {
            DrumX = _drum.X, DrumState = StateName(_drum, "set"), BodyX = _body.X, BodyState = StateName(_body, "plate"),
            W = _scale.Load, Reading = _scale.Reading.ToString().ToLowerInvariant(), Needle = _scale.Needle, Dip = _scale.Dip,
            Twitch = _scale.TwitchOffset, Served = _scale.Engaged, Hatch = _hatch.Position, Flag = _flag.Position,
        };

        public override string ExpectedAct(Trace t, TraceStep p) => Dl05TraceTests.ExpectedAct(t, p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            int compared = 0, last = run.Rows[run.RowAfter(Scene)].P.I;                       // to the first step of DL-06
            for (int k = 0; k < run.Rows.Count; k++)
            {
                var p = run.Rows[k].P; var w = Samples[k];
                if (p.D5x == null || p.I > last) continue;                                      // DL-05's fields
                compared++;
                Check(bad, p.I, "drum.x", p.D5x.Value, w.DrumX);
                Check(bad, p.I, "body.x", p.B5x.Value, w.BodyX);
                if (p.D5s != w.DrumState) bad.Add($"#{p.I} drum {p.D5s} vs {w.DrumState}");
                if (p.B5s != w.BodyState) bad.Add($"#{p.I} body {p.B5s} vs {w.BodyState}");
                Check(bad, p.I, "W", p.W5.Value, w.W);
                if (p.W5r != w.Reading) bad.Add($"#{p.I} reading {p.W5r} vs {w.Reading}");
                Check(bad, p.I, "needle", p.N5.Value, w.Needle);
                Check(bad, p.I, "dip", p.P5.Value, w.Dip);
                Check(bad, p.I, "twitch", p.T5.Value, w.Twitch);
                if (p.S5 != w.Served) bad.Add($"#{p.I} served {p.S5} vs {w.Served}");
                Check(bad, p.I, "hatch", p.H5.Value, w.Hatch);
                Check(bad, p.I, "flag", p.F5.Value, w.Flag);
            }
            Assert.Equal(12073, last);
            Assert.Equal(12073 - 9868 + 1, compared);
        }

        private static string StateName(Pushable p, string docked)
            => p.State == PushableState.Docked ? docked : p.State == PushableState.Free ? "free" : p.State.ToString();
    }
}
