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
                    return (p.X < at ? id : "Grab") + ":" + (phase == "approach" ? "Approach" : "Clip");
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
                default: return "att." + p.Aw + ":" + phase;
            }
        }

        /// <summary>A step-in act's phase (<see cref="DeadLetter.Core.Scenes.Attendance.AttAct"/>): approach, in, its clip, out.</summary>
        private static string Stepped(string phase, string clip)
            => phase == "approach" ? "Approach" : phase == "in" ? "In" : phase == "out" ? "Out" : clip;

        /// <summary>The pushable he is taking hold of: the one whose stand points are nearest.</summary>
        private static (string id, double at) PushedNear(TraceStep p)
        {
            if (p.F13x.HasValue && p.X > 212) return ("dl13.figure", p.F13x.Value);
            return ("dl12.figure", p.F12x.Value);
        }

        /// <summary>The item he lifts or sets down (by where he is: the coat in DL-12, the pole in DL-14).</summary>
        private static string ItemAt(TraceStep p) => p.X < 216 ? "dl12.coat" : "dl14.pole";
    }
}
