using System.Collections.Generic;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl03;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-03 in the chapter replay (as <see cref="Dl03TraceTests"/>): the trolley, the weight, the plate's load and needle and
    /// the gate, from his rest on DL-02's gantry (#5132) to the first step of DL-04, the four steps between the scene
    /// replay's two windows included. And M5 (#30): Use lets go of the trolley keeping his push speed, nothing compensated.
    /// </summary>
    internal sealed class Dl03ChapterProbe : ChapterTraceProbe<Dl03ChapterProbe.S>
    {
        internal struct S
        {
            public double TrolleyX, WeightX, WeightOff, Load, Needle, GateY, GateV;
            public string WeightState;
        }

        private Pushable _trolley; private Dl03Weight _weight; private LoadPlate _plate; private FollowerActuator _gate;

        public override string Scene => "DL-03";
        public override int FirstStep => 5228;
        public override IReadOnlyList<string> KeyActs => new[] { "dl03.weight:SetDownHigh", "quirk:Startle" };

        public override void Bind(ChapterSim sim, Trace t)
        {
            var g = sim.Graph;
            _trolley = g.Get<Pushable>("dl03.trolley"); _weight = g.Get<Dl03Weight>("dl03.weight");
            _plate = g.Get<LoadPlate>("dl03.plate"); _gate = g.Get<FollowerActuator>("dl03.gate");
        }

        protected override S Sample(ChapterSim sim) => new S
        {
            TrolleyX = _trolley.X, WeightState = WeightName(_weight.State), WeightX = _weight.FloorX, WeightOff = _weight.Offset,
            Load = _plate.Load, Needle = _plate.Needle, GateY = _gate.Position, GateV = _gate.Velocity,
        };

        public override string ExpectedAct(Trace t, TraceStep p) => Dl03TraceTests.ExpectedAct(p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            var rows = run.Rows;
            int from = run.RowOf(5132), to = run.RowAfter(Scene);
            for (int k = from; k <= to; k++)
            {
                var p = rows[k].P; var w = Samples[k];
                Check(bad, p.I, "trolley.x", p.Tx, w.TrolleyX);
                Check(bad, p.I, "weight.x", p.Wx, w.WeightX);
                Check(bad, p.I, "weight.off", p.Wo, w.WeightOff);
                Check(bad, p.I, "load", p.Ld, w.Load);
                Check(bad, p.I, "needle", p.Nd, w.Needle);
                Check(bad, p.I, "gate.y", p.Gy, w.GateY);
                Check(bad, p.I, "gate.v", p.Gv, w.GateV);
                if (p.Ws != w.WeightState) bad.Add($"#{p.I} weight {p.Ws} vs {w.WeightState}");
            }
            Assert.Equal(6279, rows[to].P.I);

            // M5: the one Use that lets go of the trolley (#5977) keeps his speed (beginUse 'release', L1820), as the prototype.
            var releases = new List<int>();
            for (int k = 1; k < rows.Count; k++)
                if (rows[k - 1].Hold == "trolley" && rows[k].Hold == null && rows[k].P.UP)
                {
                    releases.Add(rows[k].P.I);
                    Assert.NotEqual(0, rows[k].Vx);
                    Check(bad, rows[k].P.I, "vx (M5: Use lets go keeping it)", rows[k].P.Vx, rows[k].Vx);
                }
            Assert.Equal(new[] { 5977 }, releases);
        }

        private static string WeightName(Dl03WeightState s) => s == Dl03WeightState.Floor ? "floor" : s == Dl03WeightState.Carried ? "carried" : "trolley";
    }
}
