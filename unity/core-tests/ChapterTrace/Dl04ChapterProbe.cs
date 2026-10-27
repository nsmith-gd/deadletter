using System;
using System.Collections.Generic;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Scenes;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-04 in the chapter replay (as <see cref="Dl04TraceTests"/>): the courier, the cradle's arms and what the bay wants on
    /// every step DL-04 records them; the bay door against the prototype's law, with its deliberate hold at the top (never
    /// below the law, never more than a step above it).
    /// </summary>
    internal sealed class Dl04ChapterProbe : ChapterTraceProbe<Dl04ChapterProbe.S>
    {
        internal struct S
        {
            public double CourierX, Arm, BayDoor;
            public bool Want, PlateOn;
            public string CourierState;
        }

        private Cradle _cradle; private LoadPlate _bayPlate; private PlateDoor _bayDoor;

        public override string Scene => "DL-04";
        public override int FirstStep => 6279;
        public override IReadOnlyList<string> KeyActs => new[] { "realise:act", "bayTouch:act" };
        public override IReadOnlyList<(int step, string cue)> KeyCues => new[] { (6286, "music:racks"), (6347, "moment:kin") };

        public override void Bind(ChapterSim sim, Trace t)
        {
            var g = sim.Graph;
            _cradle = g.Get<Cradle>("dl04.cradle"); _bayPlate = g.Get<LoadPlate>("dl04.bayPlate"); _bayDoor = g.Get<PlateDoor>("dl04.bayDoor");
        }

        protected override S Sample(ChapterSim sim) => new S
        {
            CourierX = _cradle.Position, CourierState = CourierName(_cradle.State), Arm = _cradle.ArmRad,
            BayDoor = _bayDoor.Open01, Want = _bayDoor.Want, PlateOn = _bayPlate.Engaged,
        };

        public override string ExpectedAct(Trace t, TraceStep p) => Dl04TraceTests.ExpectedAct(p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            int recorded = 0, last = run.Rows[run.RowAfter(Scene)].P.I;                        // to the first step of DL-05
            double law = 0;
            for (int k = 0; k < run.Rows.Count; k++)
            {
                var p = run.Rows[k].P; var w = Samples[k];
                if (p.Ks4 == null || p.I > last) continue;                                      // DL-04's fields
                recorded++;
                Check(bad, p.I, "courier.x", p.Kx4.Value, w.CourierX);
                Check(bad, p.I, "arms", p.Ka4.Value, w.Arm);
                if (p.Ks4 != w.CourierState) bad.Add($"#{p.I} courier {p.Ks4} vs {w.CourierState}");
                if ((p.Bw4.Value == 1) != w.Want) bad.Add($"#{p.I} want {p.Bw4} vs {w.Want}");
                if (w.CourierState != "seated" && w.PlateOn != w.Want) bad.Add($"#{p.I} plate {w.PlateOn} vs want {w.Want}");
                law = (w.Want ? 1 : 0) > law ? Math.Min(1, law + Dt / (w.CourierState == "seated" ? 2.2 : 1.1)) : Math.Max(0, law - Dt / 0.5);   // L4814
                Check(bad, p.I, "door (law)", p.Bd4.Value, law);
                double d = w.BayDoor - law;
                if (d < -1e-12 || d > Dt / 0.5 + 1e-12) bad.Add($"#{p.I} door {w.BayDoor:R} vs the law {law:R}");
            }
            Assert.Equal(9868, last);
            Assert.Equal(9868 - 6279 + 1, recorded);
        }

        private static string CourierName(CradleState s)
            => s == CradleState.Free ? "free" : s == CradleState.Drawing ? "drawn" : s == CradleState.Closing ? "cradle" : "seated";
    }
}
