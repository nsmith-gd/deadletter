using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl06;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-06 in the chapter replay (as <see cref="Dl06TraceTests"/>): the scanner, the belt, the route, both levers, what he
    /// rides and every carrier, on every step of DL-06 to the first step of the scene after it.
    /// </summary>
    internal sealed class Dl06ChapterProbe : ChapterTraceProbe<Dl06ChapterProbe.S>
    {
        internal struct S
        {
            public string Scan, Route, Carriers;
            public double ScanT, Stop, Points;
            public bool Belt;
            public int Riding;
        }

        private Dl06Scanner _scanner; private PointsLever _stopLever, _points; private CarrierLine _line;

        public override string Scene => "DL-06";
        public override int FirstStep => 12073;
        public override IReadOnlyList<string> KeyActs => new[] { "dl06.scanner:Check", "dl06.points:StepOut", "quirk:Proud" };
        public override IReadOnlyList<(int step, string cue)> KeyCues => new[] { (0, "shot:scan") };

        public override void Bind(ChapterSim sim, Trace t)
        {
            var g = sim.Graph;
            _scanner = g.Get<Dl06Scanner>("dl06.scanner"); _stopLever = g.Get<PointsLever>("dl06.stopLever");
            _points = g.Get<PointsLever>("dl06.points"); _line = g.Get<CarrierLine>("dl06.line");
        }

        protected override S Sample(ChapterSim sim) => new S
        {
            Scan = _scanner.Phase.ToString().ToLowerInvariant(), ScanT = _scanner.T, Belt = _stopLever.Engaged,
            Route = _points.Engaged ? "exit" : "chute", Stop = _stopLever.LeverDeg, Points = _points.LeverDeg,
            Riding = _line.Ride?.Seq ?? -1, Carriers = CarriersOf(_line),
        };

        /// <summary>DL-06's, and DL-07's first step (the window's last) as DL-06's replay names it.</summary>
        public override string ExpectedAct(Trace t, TraceStep p) => Dl06TraceTests.ExpectedAct(t, p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            int compared = 0, carriers = 0, last = run.Rows[run.RowAfter(Scene)].P.I;
            for (int k = 0; k < run.Rows.Count; k++)
            {
                var p = run.Rows[k].P; var w = Samples[k];
                if (p.Sp6 == null || p.I > last) continue;
                compared++;
                if (p.Sp6 != w.Scan) bad.Add($"#{p.I} scanner {p.Sp6} vs {w.Scan}");
                Check(bad, p.I, "scan.t", p.St6.Value, w.ScanT);
                if (p.Bl6 != w.Belt) bad.Add($"#{p.I} belt {p.Bl6} vs {w.Belt}");
                if (p.Rt6 != w.Route) bad.Add($"#{p.I} route {p.Rt6} vs {w.Route}");
                Check(bad, p.I, "stopLever", p.Sl6.Value, w.Stop);
                Check(bad, p.I, "pointsLever", p.Pl6.Value, w.Points);
                if ((int)(p.Rd6 ?? -1) != w.Riding) bad.Add($"#{p.I} riding {p.Rd6} vs {w.Riding}");
                CompareCarriers(bad, p.I, p.Cr6, w.Carriers, ref carriers);
            }
            Assert.Equal(14016, last);                                                          // DL-07's first step
            Assert.Equal(14016 - 12073 + 1, compared);
            Assert.True(carriers > 1600, carriers.ToString());
        }

        private static readonly string[] CarrierStates = { "rise", "dock", "move", "unload", "tipload", "tip", "back", "sink" };

        /// <summary>The line's carriers in the recorder's shape (tools/sim/record_trace.mjs), as Dl06TraceTests writes them.</summary>
        private static string CarriersOf(CarrierLine line)
        {
            var sb = new StringBuilder("[");
            for (int i = 0; i < line.Count; i++)
            {
                var c = line.At(i);
                if (i > 0) sb.Append(',');
                sb.Append('[').Append(c.Seq).Append(",\"").Append(CarrierStates[(int)c.State]).Append("\",")
                  .Append(c.Route == CarrierRoute.None ? "null" : c.Route == CarrierRoute.Chute ? "\"chute\"" : "\"exit\"")
                  .Append(',').Append(R(c.Position)).Append(',').Append(R(c.Y)).Append(',').Append(R(c.S)).Append(',').Append(R(c.Wait))
                  .Append(',').Append(R(c.T)).Append(',').Append(c.Ridden ? 1 : 0).Append(',').Append(R(c.TipRad)).Append(",[");
                for (int k = 0; k < c.Parcels; k++)
                {
                    if (k > 0) sb.Append(',');
                    sb.Append('[').Append(R(c.ParcelSizeOf(k))).Append(',').Append(R(-c.ParcelZOf(k))).Append(',').Append(R(c.ParcelYawOf(k))).Append(']');
                }
                sb.Append("]]");
            }
            return sb.Append(']').ToString();
        }

        private static void CompareCarriers(List<string> bad, int i, string proto, string core, ref int seen)
        {
            using var a = JsonDocument.Parse(proto);
            using var b = JsonDocument.Parse(core);
            int n = a.RootElement.GetArrayLength();
            if (n != b.RootElement.GetArrayLength()) { bad.Add($"#{i} carriers {proto} vs {core}"); return; }
            for (int k = 0; k < n; k++)
            {
                seen++;
                var x = a.RootElement[k]; var y = b.RootElement[k];
                for (int f = 0; f < 11; f++)
                {
                    var u = x[f]; var v = y[f];
                    if (f == 10)
                    {
                        if (u.GetArrayLength() != v.GetArrayLength()) { bad.Add($"#{i} carrier {k} payload {u} vs {v}"); continue; }
                        for (int q = 0; q < u.GetArrayLength(); q++)
                            for (int e = 0; e < 3; e++) Check(bad, i, $"carrier {k} parcel {q}.{e}", u[q][e].GetDouble(), v[q][e].GetDouble());
                    }
                    else if (u.ValueKind == JsonValueKind.Number && f >= 3) Check(bad, i, $"carrier {k} field {f}", u.GetDouble(), v.GetDouble());
                    else if (u.ToString() != v.ToString()) bad.Add($"#{i} carrier {k} field {f} {u} vs {v}");
                }
            }
        }
    }
}
