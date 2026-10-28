using System.Collections.Generic;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl12;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-12 in Chapter 1's replay (<see cref="AttendanceChapterTraceTests"/>): coat 7 (off the bin #78–#201, onto peg 7
    /// from the bench #486–#598), the stand-in figure pushed onto the strip (#651–#914), the strip and the gate, from the
    /// first step at <c>school</c> to the first step of DL-13 (#1313).
    /// </summary>
    internal sealed class Dl12ChapterProbe : ChapterTraceProbe<Dl12ChapterProbe.S>
    {
        internal struct S
        {
            public double CoatX, CoatBase, FigX, GateY, GateV;
            public string Coat;
            public bool Present;
            public long Count;
        }

        private CarriedItem _coat; private Pushable _fig; private PresenceStrip _strip; private FollowerActuator _gate;

        public override string Scene => "DL-12";
        public override int FirstStep => 0;
        public override IReadOnlyList<string> KeyActs => new[] { "dl12.coat:Lift", "dl12.peg:SetDownHigh", "dl12.figure:Clip" };
        public override IReadOnlyList<(int step, string cue)> KeyCues => new[] { (0, "sound:plate"), (0, "voice:att_gate_3") };

        public override void Bind(ChapterSim sim, Trace t)
        {
            var g = sim.Graph;
            _coat = g.Get<CarriedItem>("dl12.coat"); _fig = g.Get<Pushable>("dl12.figure");
            _strip = g.Get<PresenceStrip>("dl12.strip"); _gate = g.Get<FollowerActuator>("dl12.gate");
        }

        protected override S Sample(ChapterSim sim) => new S
        {
            CoatX = _coat.X, CoatBase = _coat.BaseY, Coat = CoatName(_coat), FigX = _fig.X, GateY = _gate.Position, GateV = _gate.Velocity,
            Present = _strip.Present, Count = _strip.PresentCount,
        };

        public override string ExpectedAct(Trace t, TraceStep p) => AttendanceActs.Expected(p);

        public override void CheckMechanisms(ChapterTraceRun run, List<string> bad)
        {
            var rows = run.Rows;
            int from = run.RowOf(FirstStep), to = run.RowAfter(Scene);
            for (int k = from; k <= to; k++)
            {
                var p = rows[k].P; var w = Samples[k];
                Check(bad, p.I, "coat.x", p.C12x.Value, w.CoatX);
                Check(bad, p.I, "coat.base", p.C12b.Value, w.CoatBase);
                if (p.C12s != w.Coat) bad.Add($"#{p.I} coat {p.C12s} vs {w.Coat}");
                Check(bad, p.I, "fig.x", p.F12x.Value, w.FigX);
                Check(bad, p.I, "gate.y", p.G12y.Value, w.GateY);
                Check(bad, p.I, "gate.v", p.G12v.Value, w.GateV);
                if (p.P12.Value != w.Present) bad.Add($"#{p.I} present {p.P12} vs {w.Present}");
                if (p.Pc12.Value != w.Count) bad.Add($"#{p.I} presentCount {p.Pc12} vs {w.Count}");
            }
            Assert.Equal(1313, rows[to].P.I);
        }

        /// <summary>The coat's state as the prototype names it (<c>bin</c>, <c>carried</c>, <c>peg</c>, <c>floor</c>).</summary>
        internal static string CoatName(CarriedItem c)
        {
            switch (c.State)
            {
                case ItemState.Placed: return c.Slot == Dl12Scene.PegSlot ? "peg" : "bin";
                case ItemState.Carried: return "carried";
                case ItemState.Floor: return "floor";
                default: return c.State.ToString();
            }
        }
    }

    /// <summary>
    /// Chapter 1's acts as Core names them (<see cref="SceneSim.ActKind"/>:<see cref="SceneSim.ActPhase"/>), from the
    /// prototype's <c>kind:phase</c> and <c>aw</c> (<c>game.act.what</c>): the scene acts by what they are about and their
    /// clip, the motor's by the mechanism they are on and their phase.
    /// </summary>
    internal static class AttendanceActs
    {
        public static string Expected(TraceStep p)
        {
            if (p.Mt) return "mantle:";
            if (p.Act == null) return null;
            int c = p.Act.IndexOf(':');
            string kind = p.Act.Substring(0, c), phase = p.Act.Substring(c + 1);
            switch (kind)
            {
                case "att": return Att(p, phase);
                case "grabPush":
                {
                    // The face he takes: its own (left of it) or the twin's (right of it, a verb).
                    var (id, at) = PushedNear(p);
                    if (id.StartsWith("dl15.") || id.StartsWith("dl14b.") && p.X > at) id = "Grab";   // their faces are not mechanisms
                    return (p.X < at || id == "Grab" ? id : "Grab") + ":" + (phase == "approach" ? "Approach" : "Clip");
                }
                case "liftItem": return ItemAt(p) + ":" + (phase == "approach" ? "Approach" : "Clip");
                case "setdownItem": return ItemAt(p) + ":Clip";
                default: return kind + ":" + phase;
            }
        }

        private static string Att(TraceStep p, string phase)
        {
            switch (p.Aw)
            {
                case "coat": return "dl12.coat:" + (phase == "approach" ? "Approach" : "Lift");
                case "hang": return "dl12.peg:" + (phase == "approach" ? "Approach" : "SetDownHigh");
                case "reachpeg": return "dl12.reachPeg:Present";
                case "pawl": case "pawlIdle": return "dl13.brake:" + (phase == "approach" ? "Approach" : "Clip");
                case "crank": return "dl14.crank:" + (phase == "approach" ? "Approach" : "Clip");
                case "unjam": return "dl14.pole:" + (phase == "approach" ? "Approach" : "Lift");
                case "jam": return "dl14.wheel:" + (phase == "approach" ? "Approach" : "SetDown");
                case "duct": return "dl14.hatch:" + (phase == "in" ? "In" : phase == "along" ? "Along" : "Out");
                case "pawl14a": return "dl14a.brake:" + (phase == "approach" ? "Approach" : "Clip");
                case "crank14a": return "dl14a.crank:" + (phase == "approach" ? "Approach" : "Clip");
                case "bagBasket": return "dl14a.basket:" + (phase == "approach" ? "Approach" : "Lift");
                case "hangHook": return "dl14a.hook:" + Stepped(phase, "SetDownHigh");
                case "takeHook": return "dl14a.hook:" + Stepped(phase, "Lift");
                case "hangWall": return "dl14a.wallPeg:" + Stepped(phase, "SetDownHigh");
                case "takeWall": return "dl14a.wallPeg:" + Stepped(phase, "Lift");
                case "reachHook": return "dl14a.reachHook:Present";
                case "nudge14b": return "dl14b.figure:" + (phase == "approach" ? "Approach" : "Nudge");
                case "hide": return (p.X < 266 ? "dl14b.nicheA:" : "dl14b.bay:") + (phase == "approach" ? "Approach" : phase == "in" ? "StepIn" : phase == "act" ? "Clip" : "StepOut");
                case "escorted": return "Escorted:Clip";
                case "sit": return "dl15.chair:" + (phase == "approach" ? "Approach" : phase == "up" ? "SitUp" : "Clip");
                case "lever16": return "dl16.lever:" + (phase == "approach" ? "Approach" : "Clip");
                case "call16a": return "dl16a.callPush:" + (phase == "approach" ? "Approach" : "PressButtonHigh");
                case "bell16a": return "dl16a.car:PressButtonHigh";
                case "tray": return "dl17.tray:" + (phase == "approach" ? "Approach" : "Lift");
                case "drawer": return "dl17.drawer:" + (phase == "approach" ? "Approach" : "Tug");
                case "read": return "dl17.read:" + (phase == "approach" ? "Approach" : "ReadRoute");
                case "sluice17": return SluiceAt(p.X) + ":" + (phase == "approach" ? "Approach" : "Clip");
                case "valve17": return "dl17.valve:" + (phase == "approach" ? "Approach" : "Clip");
                case "ride16a": return "dl16a.car:Ride";
                default: return "att." + p.Aw + ":" + phase;
            }
        }

        /// <summary>A step-in act's phase (<see cref="DeadLetter.Core.Scenes.Attendance.AttAct"/>): approach, in, its clip, out.</summary>
        private static string Stepped(string phase, string clip)
            => phase == "approach" ? "Approach" : phase == "in" ? "In" : phase == "out" ? "Out" : clip;

        /// <summary>The pushable he is taking hold of: the one whose stand points are nearest.</summary>
        private static (string id, double at) PushedNear(TraceStep p)
        {
            if (p.Ax15.HasValue && p.X > 278)
            {
                // The DL-15 figure whose stand point he is nearest (gap 0.6 either side).
                double a = System.Math.Min(System.Math.Abs(p.X - (p.Ax15.Value - 0.6)), System.Math.Abs(p.X - (p.Ax15.Value + 0.6)));
                double b = System.Math.Min(System.Math.Abs(p.X - (p.Bx15.Value - 0.6)), System.Math.Abs(p.X - (p.Bx15.Value + 0.6)));
                return a <= b ? ("dl15.figA", p.Ax15.Value) : ("dl15.figB", p.Bx15.Value);
            }
            if (p.Fx14b.HasValue && p.X > 262) return ("dl14b.figure", p.Fx14b.Value);
            if (p.F13x.HasValue && p.X > 212) return ("dl13.figure", p.F13x.Value);
            return ("dl12.figure", p.F12x.Value);
        }

        /// <summary>The item he lifts or sets down (by where he is: the coat in DL-12, the pole in DL-14, the tray in DL-17).</summary>
        private static string ItemAt(TraceStep p) => p.X < 216 ? "dl12.coat" : p.X > 324 ? "dl17.tray" : "dl14.pole";

        /// <summary>The sluice he works (stand 0.18 short of each, within 0.24: 337.45, 338.1, 338.8).</summary>
        private static string SluiceAt(double x) => x < 337.7 ? "dl17.sluiceA" : x < 338.4 ? "dl17.sluiceB" : "dl17.sluiceC";
    }
}
