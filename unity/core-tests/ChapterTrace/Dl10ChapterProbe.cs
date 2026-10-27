using System.Collections.Generic;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl10;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-10 in the chapter replay: on every step from DL-10's first (#25182, off the balcony's end at <c>UPONLY.x0</c>) to
    /// DL-11's first (#27923, past <c>REGION5_X</c> into region 5): the relocation lift (phase, rise, its clock from the world's
    /// build at <c>start</c>, riding), the car plate (loaded, needle, balance gauge), the gate, the service door's opening and
    /// the crank act's strokes, the last buzz, the suitcase (state, x, base), the <c>ringc</c> moment's clock and cut, the cold
    /// light's switch-off and the ride's clock (the recorder's DL-10 fields, tools/sim/record_trace.mjs). He is walked into
    /// DL-10 from DL-09 and rides out of it, so it has no scene replay of its own: this chapter replay is its proof.
    /// </summary>
    internal sealed class Dl10ChapterProbe : ChapterTraceProbe<Dl10ChapterProbe.S>
    {
        internal struct S
        {
            public string Phase, Case, ActKind;
            public double D, T, Needle, Gauge, Gate, Door, DoorM, BuzzAt, CaseX, CaseBase, ActT;
            public double? Moment, LightOff;
            public bool Riding, Loaded, Cut, Cranking;
            public int Strokes;
        }

        private UpOnly10 _rules;

        public override string Scene => "DL-10";
        public override int FirstStep => 25182;
        public override IReadOnlyList<string> KeyActs => new[]
        {
            "dl10.case:Approach", "dl10.case:Clip", "Place:Approach", "Place:Turn", "Place:StepIn", "Place:Clip", "Place:StepOut",
            "dl10.serviceCrank:Approach", "dl10.serviceCrank:Turn", "dl10.serviceCrank:Clip",
            "dl10.serviceUp:Approach", "dl10.serviceUp:Clip", "ride10:ride",
        };
        /// <summary>
        /// The crank's four strokes (0.12 each), the gate's slam (0.12), the car sent from the counterweight's panel (0.15) and
        /// the <c>ringc</c> moment with it (PressButtonHigh f16, #26574), the counterweight landing with him (0.35, #26905).
        /// </summary>
        public override IReadOnlyList<(int step, string cue)> KeyCues => new[]
        {
            (26293, "shake:12"), (26473, "shake:12"), (26574, "shake:15"), (26574, "moment:ringc"), (26905, "shake:35"),
        };

        public override void Bind(ChapterSim sim, Trace t)
        {
            foreach (var s in sim.Def.Scenes) if (s.Id == Scene) _rules = (UpOnly10)sim.RulesOf(s);
        }

        protected override S Sample(ChapterSim sim)
        {
            var r = _rules;
            var l = r.Lift;
            var act = sim.Act;
            return new S
            {
                Phase = Lower(l.State.ToString()), D = l.D, T = l.T, Riding = l.Riding,
                Loaded = r.CarPlate.Load > 0, Needle = r.CarPlate.Needle, Gauge = r.CarPlate.Gauge, Gate = r.CarGate.Position,
                Door = r.Crank.Position, DoorM = r.ServiceDoor.Position, Cranking = r.Crank.State == CrankState.Cranking, Strokes = r.Crank.Strokes,
                BuzzAt = r.BuzzAt,
                Case = r.Case.State == ItemState.Floor ? "floor" : r.Case.State == ItemState.Carried ? "carried" : r.Case.State == ItemState.Placed ? "car" : r.Case.State.ToString(),
                CaseX = r.Case.X, CaseBase = r.Case.BaseY,
                Moment = r.Moment.Time(sim.Clock), Cut = r.Moment.Cut, LightOff = r.LightOff,
                ActKind = act?.Kind.Name, ActT = act?.T ?? double.NaN,
            };
        }

        private static string Lower(string s) => char.ToLowerInvariant(s[0]) + s.Substring(1);

        /// <summary>
        /// DL-10's acts as Core names them: the suitcase's lift by the suitcase; the set-down into the car (the motor's Place on
        /// the car loader: approach, turn, step in, SetDown, step out); the crank and the two UP buttons by their mechanisms;
        /// the ride (<see cref="Dl10RideAct"/>); a quirk by its clip; a climb as the motor's.
        /// </summary>
        public override string ExpectedAct(Trace t, TraceStep p)
        {
            if (p.Mt) return "mantle:";
            if (p.Act == null) return null;
            var parts = p.Act.Split(':');
            string kind = parts[0], phase = parts[1];
            string Motor(string who) => who + ":" + (phase == "approach" ? "Approach" : phase == "turn" ? "Turn" : phase == "in" ? "StepIn" : phase == "out" ? "StepOut" : "Clip");
            switch (kind)
            {
                case "liftItem": return Motor("dl10.case");
                case "loadCar": return Motor("Place");
                case "crank10": return Motor("dl10.serviceCrank");
                case "up10": return Motor("dl10.upButton");
                case "ride10": return phase == "ride" ? "ride10:ride" : Motor("dl10.serviceUp");
                default: return kind + ":" + phase;
            }
        }

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            int compared = 0, rides = 0, strokes = 0, last = run.Rows[run.RowAfter(Scene)].P.I;
            for (int k = 0; k < run.Rows.Count; k++)
            {
                var p = run.Rows[k].P; var w = Samples[k]; int i = p.I;
                if (p.Ph10 == null || i < FirstStep || i > last) continue;
                compared++;
                if (p.Ph10 != w.Phase) bad.Add($"#{i} lift {p.Ph10} vs {w.Phase}");                                   // L4629–L4636
                Check(bad, i, "lift.d", p.D10.Value, w.D);
                Check(bad, i, "lift.t", p.T10.Value, w.T);                                                          // one world from start: uo.t counts from #1768
                if ((p.Rd10 ?? false) != w.Riding) bad.Add($"#{i} riding {p.Rd10} vs {w.Riding}");
                if ((p.Ld10 ?? false) != w.Loaded) bad.Add($"#{i} loaded {p.Ld10} vs {w.Loaded}");                    // L4554
                Check(bad, i, "needle", p.Nd10.Value, w.Needle);                                                    // L4641
                Check(bad, i, "gauge", p.Gk10.Value, w.Gauge);                                                      // L4645
                Check(bad, i, "gate", p.G10.Value, w.Gate);                                                         // L4620–L4624
                Check(bad, i, "service door", p.Dr10.Value, w.Door);                                                // L4567
                Check(bad, i, "service door (m)", p.Dr10.Value * 1.45, w.DoorM);                                    // UO.doorLift, L4654
                if (w.Cranking)
                {
                    strokes++;
                    if (p.Sk10 != w.Strokes) bad.Add($"#{i} strokes {p.Sk10} vs {w.Strokes}");                     // a.strokes, L4568
                }
                Check(bad, i, "buzz", p.Bz10.Value, w.BuzzAt);
                if (p.Cs10 != w.Case) bad.Add($"#{i} case {p.Cs10} vs {w.Case}");
                Check(bad, i, "case.x", p.Cx10.Value, w.CaseX);
                Check(bad, i, "case.base", p.Cb10.Value, w.CaseBase);
                if (p.Mt10.HasValue != w.Moment.HasValue) bad.Add($"#{i} moment {p.Mt10} vs {w.Moment}");
                else if (p.Mt10.HasValue) Check(bad, i, "moment", p.Mt10.Value, w.Moment.Value);
                if ((p.Mc10 ?? false) != w.Cut) bad.Add($"#{i} momentCut {p.Mc10} vs {w.Cut}");
                if (p.Lo10.HasValue != w.LightOff.HasValue) bad.Add($"#{i} lightOff {p.Lo10} vs {w.LightOff}");
                else if (p.Lo10.HasValue) Check(bad, i, "lightOff", p.Lo10.Value, w.LightOff.Value);
                if (w.ActKind == Dl10RideAct.RideKind.Name)                                                          // the ride's clock is a.t
                {
                    rides++;
                    if (!p.At10.HasValue) bad.Add($"#{i} act clock - vs {w.ActT}");
                    else Check(bad, i, "act.t", p.At10.Value, w.ActT);
                }
            }
            Assert.Equal(27923, last);                                                                              // DL-11's first step: region 5
            Assert.Equal(27923 - 25182 + 1, compared);
            Assert.True(rides > 1200, rides.ToString());                                                           // 5.5 s down and 16.5 s held
            Assert.True(strokes > 200, strokes.ToString());
        }
    }
}
