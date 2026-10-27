using System;
using System.Collections.Generic;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl07;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-07 in the chapter replay: on every step from the belt running to the exit (#14016) to DL-08's first (#17677, the
    /// doorway): the two weights (state, x, base, a tumble's progress), the bucket, the gate, the gallery, the collapse,
    /// the letter on the rail, the belt, the route, both levers, what he rides and every carrier with its loads (the
    /// recorder's DL-07 fields, tools/sim/record_trace.mjs). DL-07 starts mid-way through the stop lever's act on a floor
    /// already running, so it has no scene replay of its own: this chapter replay is its proof.
    /// </summary>
    internal sealed class Dl07ChapterProbe : ChapterTraceProbe<Dl07ChapterProbe.S>
    {
        internal struct S
        {
            public string W0s, W1s, Route, Carriers, Letter;
            public double W0x, W0b, W0t, W1x, W1b, W1t, Gate, CollapseT, LetterT, Stop, Points;
            public int Bucket, Collapse, Riding;
            public bool Upper, Belt;
        }

        private CarriedItem _w0, _w1; private Heap07 _rules; private CarrierLine _line; private PointsLever _stop, _points;

        public override string Scene => "DL-07";
        public override int FirstStep => 14016;
        public override IReadOnlyList<string> KeyActs => new[]
        {
            "dl07.weight0:Approach", "dl07.weight0:Clip", "dl07.weight1:Clip", "Place:Turn", "Place:Clip", "Board:Hop", "Alight:Turn", "Alight:Hop",
            "quirk:BrushOff",
        };
        /// <summary>
        /// The bucket takes the first weight (shake 0.2), the gate stalls under it (0.15), the bucket takes the second. (The
        /// collapse gives way at #17662 and hits 0.45 s on, past the doorway, in DL-08's steps.)
        /// </summary>
        public override IReadOnlyList<(int step, string cue)> KeyCues => new[] { (15355, "shake:20"), (0, "shake:15"), (16435, "shake:20") };

        public override void Bind(ChapterSim sim, Trace t)
        {
            var g = sim.Graph;
            _w0 = g.Get<CarriedItem>("dl07.weight0"); _w1 = g.Get<CarriedItem>("dl07.weight1");
            _line = g.Get<CarrierLine>("dl06.line");
            _stop = g.Get<PointsLever>("dl06.stopLever"); _points = g.Get<PointsLever>("dl06.points");
            foreach (var s in sim.Def.Scenes) if (s.Id == Scene) _rules = (Heap07)sim.RulesOf(s);
        }

        protected override S Sample(ChapterSim sim)
        {
            var l = _rules.Loading;
            return new S
            {
                W0s = StateOf(_w0, l.InBucket(0)), W0x = _w0.X, W0b = _w0.BaseY, W0t = l.TumbleOf(0),
                W1s = StateOf(_w1, l.InBucket(1)), W1x = _w1.X, W1b = _w1.BaseY, W1t = l.TumbleOf(1),
                Bucket = _rules.Bucket.Weights, Gate = _rules.Gate.Position, Upper = _rules.Gallery.Upper,
                Collapse = (int)_rules.Collapse.State, CollapseT = _rules.Collapse.T,
                Letter = LetterOf(_rules.Letter.State), LetterT = _rules.Letter.T,
                Belt = _stop.Engaged, Route = _points.Engaged ? "exit" : "chute", Stop = _stop.LeverDeg, Points = _points.LeverDeg,
                Riding = _line.Ride?.Seq ?? -1, Carriers = Dl06ChapterProbe.CarriersOf(_line, loads: true),
            };
        }

        /// <summary>The prototype's <c>it.state</c>.</summary>
        private static string StateOf(CarriedItem w, bool inBucket)
        {
            switch (w.State)
            {
                case ItemState.Floor: return "floor";
                case ItemState.Carried: return "carried";
                case ItemState.InCarrier: return "carrier";
                case ItemState.Tumble: return "tumble";
                case ItemState.Gone: return inBucket ? "bucket" : "gone";
                default: return w.State.ToString();
            }
        }

        /// <summary>The prototype's <c>letterState.heap</c>.</summary>
        private static string LetterOf(HeapLetterState s) => s == HeapLetterState.Rail ? "rail" : s == HeapLetterState.Falling ? "fallingRail" : "floor";

        /// <summary>
        /// DL-07's acts as Core names them: a weight's lift by the weight he lifts (the one carried after it), the set-down
        /// into a carrier (the motor's Place, its target the line's loader), boarding and alighting (the motor's ride acts);
        /// the floor's (the levers, a quirk) as DL-06's replay names them.
        /// </summary>
        public override string ExpectedAct(Trace t, TraceStep p)
        {
            if (p.Mt) return "mantle:";
            if (p.Act == null) return null;
            var parts = p.Act.Split(':');
            string kind = parts[0], phase = parts[1];
            switch (kind)
            {
                case "liftItem":
                {
                    string who = null;
                    for (int i = p.I; i < t.Steps.Count && who == null; i++)
                    {
                        var q = t.Steps[i];
                        if (q.W0s7 == "carried") who = "dl07.weight0";
                        else if (q.W1s7 == "carried") who = "dl07.weight1";
                    }
                    return who + ":" + (phase == "approach" ? "Approach" : "Clip");
                }
                case "loadCarrier": return "Place:" + (phase == "approach" ? "Approach" : phase == "turn" ? "Turn" : "Clip");
                case "board": return "Board:Hop";
                case "alight": return "Alight:" + (phase == "turn" ? "Turn" : "Hop");
                default: return Dl06TraceTests.ExpectedAct(t, p);
            }
        }

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            int compared = 0, carriers = 0, last = run.Rows[run.RowAfter(Scene)].P.I;
            for (int k = 0; k < run.Rows.Count; k++)
            {
                var p = run.Rows[k].P; var w = Samples[k];
                if (p.W0s7 == null || p.I < FirstStep || p.I > last) continue;
                compared++;
                Weight(bad, p.I, 0, p.W0s7, p.W0x7, p.W0b7, p.W0t7, w.W0s, w.W0x, w.W0b, w.W0t);
                Weight(bad, p.I, 1, p.W1s7, p.W1x7, p.W1b7, p.W1t7, w.W1s, w.W1x, w.W1b, w.W1t);
                if (p.Bk7 != w.Bucket) bad.Add($"#{p.I} bucket {p.Bk7} vs {w.Bucket}");
                Check(bad, p.I, "gate", p.G7.Value, w.Gate);
                if (p.Up7 != w.Upper) bad.Add($"#{p.I} upper {p.Up7} vs {w.Upper}");
                if (p.Co7 != w.Collapse) bad.Add($"#{p.I} collapse {p.Co7} vs {w.Collapse}");
                Check(bad, p.I, "collapse.t", p.Ct7.Value, w.CollapseT);
                if (p.Hl7 != w.Letter) bad.Add($"#{p.I} letter {p.Hl7} vs {w.Letter}");
                Check(bad, p.I, "letter.t", p.Ht7.Value, w.LetterT);
                if (p.Bl7 != w.Belt) bad.Add($"#{p.I} belt {p.Bl7} vs {w.Belt}");
                if (p.Rt7 != w.Route) bad.Add($"#{p.I} route {p.Rt7} vs {w.Route}");
                Check(bad, p.I, "stopLever", p.Sl7.Value, w.Stop);
                Check(bad, p.I, "pointsLever", p.Pl7.Value, w.Points);
                if ((int)(p.Rd7 ?? -1) != w.Riding) bad.Add($"#{p.I} riding {p.Rd7} vs {w.Riding}");
                Dl06ChapterProbe.CompareCarriers(bad, p.I, p.Cr7, w.Carriers, ref carriers);
            }
            Assert.Equal(17677, last);                                                          // DL-08's first step: the doorway
            Assert.Equal(17677 - 14016 + 1, compared);
            Assert.True(carriers > 3000, carriers.ToString());
        }

        private static void Weight(List<string> bad, int i, int n, string ps, double? px, double? pb, double? pt, string cs, double cx, double cb, double ct)
        {
            if (ps != cs) bad.Add($"#{i} weight{n} {ps} vs {cs}");
            Check(bad, i, $"weight{n}.x", px.Value, cx);
            Check(bad, i, $"weight{n}.base", pb.Value, cb);
            if (pt.HasValue != !double.IsNaN(ct)) bad.Add($"#{i} weight{n} tumble {pt} vs {ct}");
            else if (pt.HasValue) Check(bad, i, $"weight{n}.tumble", pt.Value, ct);
        }
    }
}
