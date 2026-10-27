using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Text.Json;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl06;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-06 parity (U-20): the prototype's own run (the mechanical bot, seed 1, Traces/prologue_mech_seed1.jsonl.gz, with
    /// DL-06's fields: the scanner's phase and clock, the belt, the route, both levers' angles, the carrier he rides and every
    /// carrier's id, state, route, x, y, s, wait, t, tip and payload) replayed through Core's <see cref="SceneSim"/> with
    /// <see cref="Dl06Scene.Def"/>, input for input, compared at every 60 Hz step.
    /// <para><b>One window</b>, from DL-06's first step (#12073, where DL-05's ends: he runs in from the hatch past
    /// <c>REGION3_X</c>) through the scan (attention, the hatch's carrier rising at 3.6 s, the reveal), the walk over the pit
    /// (drawn on toward the rail at the reveal's pace, stopped by DL-07's first weight), the label check, <c>scanned</c> and
    /// the belt's start, the stop lever (belt stopped with the carrier still docked), the points to the exit and Proud, and
    /// the stop lever again: the belt runs to the exit and the floor is DL-07's (#14016, the step of the throw).</para>
    /// <para><b>Tolerance 1e-6</b> on every continuous value (the trace rounds to 1e-6). Discrete signals (acts and phases,
    /// grounded, the scanner's phase, the belt, the route, the carriers' states and routes, checkpoints, the region and the
    /// exit) fall on the same step.</para>
    /// <para>Nothing is compensated: the hand-over is of a running D-17, in the recorded state (vx 1.6 at #12072,
    /// <see cref="D17Motor.SetState"/>, #28), and the levers step in and out at their own 0.4 m/s (L2902, L2916; the
    /// station's <see cref="Mechanisms.Station.StepInSpeed"/>, M10), where the motor's other stations step at 0.45.</para>
    /// </summary>
    public class Dl06TraceTests
    {
        internal const string TraceFile = Dl01TraceTests.TraceFile;
        private const double Tol = 1e-6;

        internal sealed class Row
        {
            public TraceStep P;
            public double X, Y, Z, Vx, Yaw, ScanT, Stop, Points;
            public bool G, Exited, Belt;
            public string Kind, Phase, Cp, Scan, Route, Carriers, Hold;
            public int Region, Riding;
        }

        internal sealed class Replay
        {
            public readonly List<Row> Rows = new List<Row>();
            public SceneSim Sim;
            public int From, To;
        }

        private static Replay _cached;
        private static readonly object Gate = new object();

        /// <summary>The window: DL-06's first step to the first of DL-07.</summary>
        internal static (int from, int to) Window(Trace t)
            => (t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-06")), t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-07")));

        internal static Replay Run()
        {
            lock (Gate)
            {
                if (_cached != null) return _cached;
                var t = Trace.Load(TraceFile);
                var (from, to) = Window(t);
                var r = new Replay { From = from, To = to };
                ReturnToSender06 rules = null;
                r.Sim = TraceReplay.Run(t, Dl06Scene.Def(), t.Steps[from - 1].Cp, false, from, to, (p, sim) =>
                {
                    rules ??= (ReturnToSender06)sim.Rules;
                    var line = rules.Line;
                    r.Rows.Add(new Row
                    {
                        P = p, X = sim.X, Y = sim.Y, Z = sim.Z, Vx = sim.Vx, Yaw = sim.Yaw, G = sim.Grounded,
                        Kind = sim.ActKind, Phase = sim.ActPhase, Cp = sim.Checkpoints.Current.Name, Region = sim.Region, Exited = sim.Exited,
                        Hold = sim.Motor.Hold == HoldKind.None ? null : sim.Motor.Hold.ToString(),
                        Scan = rules.Scanner.Phase.ToString().ToLowerInvariant(), ScanT = rules.Scanner.T,
                        Belt = rules.StopLever.Engaged, Route = rules.Points.Engaged ? "exit" : "chute",
                        Stop = rules.StopLever.LeverDeg, Points = rules.Points.LeverDeg,
                        Riding = line.Ride?.Seq ?? -1, Carriers = CarriersOf(line),
                    });
                }, handover: true);
                return _cached = r;
            }
        }

        private static readonly string[] StateNames = { "rise", "dock", "move", "unload", "tipload", "tip", "back", "sink" };

        /// <summary>The line's carriers in the recorder's shape (as text, to compare with the record's).</summary>
        private static string CarriersOf(CarrierLine line)
        {
            var sb = new StringBuilder("[");
            for (int i = 0; i < line.Count; i++)
            {
                var c = line.At(i);
                if (i > 0) sb.Append(',');
                sb.Append('[').Append(c.Seq).Append(",\"").Append(StateNames[(int)c.State]).Append("\",")
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

        private static string R(double v) => v.ToString("R", System.Globalization.CultureInfo.InvariantCulture);

        // ---- The trace ------------------------------------------------------------------------------------------------
        [Fact]
        public void Trace_HasDl06_AndTheWindowIsWhereExpected()
        {
            var t = Trace.Load(TraceFile);
            var (from, to) = Window(t);
            Assert.Equal(12073, from);
            Assert.Equal(Dl05TraceTests.Window(t).to, from);                                       // where DL-05's window ends
            Assert.Equal(14016, to);
            Assert.Equal("hatch", t.Steps[from - 1].Cp);
            Assert.Null(t.Steps[from - 1].Act);
            Assert.Equal(1.6, t.Steps[from - 1].Vx);                                               // running in: the hand-over's speed
            Assert.Null(t.Steps[from - 1].Sp6);                                                    // DL-06's fields start in DL-06
            Assert.Equal("idle", t.Steps[from].Sp6);
            Assert.Equal("done", t.Steps[to].Sp6);                                                 // and end on the step he leaves it
            Assert.StartsWith("DL-07", t.Steps[to].Scene);
        }

        // ---- (a) position ---------------------------------------------------------------------------------------------
        [Fact]
        public void X_Y_Z_Vx_And_Yaw_MatchEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Run().Rows)
            {
                Check(bad, w.P.I, "x", w.P.X, w.X);
                Check(bad, w.P.I, "y", w.P.Y, w.Y);
                Check(bad, w.P.I, "z", -w.P.Z, w.Z);                                                 // Unity z = −three z (§0.2)
                Check(bad, w.P.I, "vx", w.P.Vx, w.Vx);
                Check(bad, w.P.I, "yaw", w.P.Yaw, w.Yaw);
            }
            Assert.True(bad.Count == 0, Report(bad));
        }

        // ---- (b) acts, holds and grounded -----------------------------------------------------------------------------
        [Fact]
        public void Grounded_AndHolds_MatchEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Run().Rows)
            {
                if (w.G != w.P.G) bad.Add($"#{w.P.I} grounded {w.P.G} vs {w.G}");
                if (w.P.Hold != w.Hold) bad.Add($"#{w.P.I} hold {w.P.Hold ?? "-"} vs {w.Hold ?? "-"}");   // nothing in his hands here
            }
            Assert.True(bad.Count == 0, Report(bad));
        }

        /// <summary>The scan, the label check, the three lever acts (approach, turn, step in, the clip, step out) and Proud.</summary>
        [Fact]
        public void Acts_MatchEveryStep()
        {
            var t = Trace.Load(TraceFile);
            var bad = new List<string>();
            var seen = new HashSet<string>();
            foreach (var w in Run().Rows)
            {
                string want = ExpectedAct(t, w.P), got = CoreAct(w);
                if (want != null) seen.Add(want);
                if (want != got) bad.Add($"#{w.P.I} act {want ?? "-"} vs {got ?? "-"}");
            }
            Assert.True(bad.Count == 0, Report(bad));
            foreach (var a in new[] { "dl06.scanner:Scan", "dl06.scanner:Check", "dl06.stopLever:Approach", "dl06.stopLever:Turn",
                         "dl06.stopLever:StepIn", "dl06.stopLever:Clip", "dl06.stopLever:StepOut", "dl06.points:Approach", "dl06.points:Turn",
                         "dl06.points:StepIn", "dl06.points:Clip", "dl06.points:StepOut", "quirk:Proud" })
                Assert.Contains(a, seen);
        }

        // ---- (c) checkpoints and the way on -----------------------------------------------------------------------------
        /// <summary><c>scanned</c> at the end of the label check (L2813), on the prototype's step.</summary>
        [Fact]
        public void Checkpoints_FireOnThePrototypesSteps()
        {
            var rows = Run().Rows;
            var bad = new List<string>();
            foreach (var w in rows) if (w.P.Cp != w.Cp) bad.Add($"#{w.P.I} checkpoint {w.P.Cp} vs {w.Cp}");
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(13371, rows.Find(w => w.Cp == "scanned").P.I);
        }

        /// <summary>The floor is DL-07's from the step the stop lever starts the belt with the points to the exit (L8141).</summary>
        [Fact]
        public void LeavesDl06_IntoDl07_OnThePrototypesStep()
        {
            var rows = Run().Rows;
            var last = rows[rows.Count - 1];
            Assert.StartsWith("DL-07", last.P.Scene);
            Assert.True(last.Exited);
            Assert.True(last.Belt);
            Assert.Equal("exit", last.Route);
            for (int k = 0; k < rows.Count - 1; k++)
            {
                Assert.False(rows[k].Exited, "#" + rows[k].P.I);
                Assert.Equal(rows[k].P.Region, rows[k].Region);
            }
            Assert.Equal(3, last.Region);
            Assert.Equal("dl06.stopLever:Clip", CoreAct(last));                                     // mid-throw: f22 of LeverPull
        }

        // ---- (d) mechanisms ---------------------------------------------------------------------------------------------
        /// <summary>
        /// The scanner (phase, clock), the belt, the route, the stop and points levers' angles, what he rides and every
        /// carrier (id, state, route, x, y, s, wait, t, ridden, tip and its payload's parcels), on every step of DL-06.
        /// </summary>
        [Fact]
        public void Mechanisms_MatchEveryStep()
        {
            var bad = new List<string>();
            var phases = new HashSet<string>();
            int compared = 0, carriers = 0;
            foreach (var w in Run().Rows)
            {
                var p = w.P;
                if (p.Sp6 == null) continue;
                compared++;
                if (p.Sp6 != w.Scan) bad.Add($"#{p.I} scanner {p.Sp6} vs {w.Scan}");                         // L2774–L2815
                Check(bad, p.I, "scan.t", p.St6.Value, w.ScanT);
                if (p.Bl6 != w.Belt) bad.Add($"#{p.I} belt {p.Bl6} vs {w.Belt}");                           // L2813, L2930
                if (p.Rt6 != w.Route) bad.Add($"#{p.I} route {p.Rt6} vs {w.Route}");                        // L2931
                Check(bad, p.I, "stopLever", p.Sl6.Value, w.Stop);                                          // L2833, L2916–L2924
                Check(bad, p.I, "pointsLever", p.Pl6.Value, w.Points);                                      // L2834
                if ((int)(p.Rd6 ?? -1) != w.Riding) bad.Add($"#{p.I} riding {p.Rd6} vs {w.Riding}");
                CompareCarriers(bad, p.I, p.Cr6, w.Carriers, ref carriers);                               // L2660–L2751
                phases.Add(w.Scan);
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(14016 - 12073 + 1, compared);
            Assert.Equal(new HashSet<string> { "idle", "scan", "reveal", "check", "done" }, phases);
            Assert.True(carriers > 1600, carriers.ToString());                                             // the hatch's carrier, from 3.6 s into the scan
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
                string[] names = { "id", "state", "route", "x", "y", "s", "wait", "t", "ridden", "tip", "payload" };
                for (int f = 0; f < names.Length; f++)
                {
                    var u = x[f]; var v = y[f];
                    if (f == 10)
                    {
                        if (u.GetArrayLength() != v.GetArrayLength()) { bad.Add($"#{i} carrier {k} payload {u} vs {v}"); continue; }
                        for (int q = 0; q < u.GetArrayLength(); q++)
                            for (int e = 0; e < 3; e++) Check(bad, i, $"carrier {k} parcel {q}.{e}", u[q][e].GetDouble(), v[q][e].GetDouble());
                    }
                    else if (u.ValueKind == JsonValueKind.Number && f >= 3) Check(bad, i, $"carrier {k} {names[f]}", u.GetDouble(), v.GetDouble());
                    else if (u.ToString() != v.ToString()) bad.Add($"#{i} carrier {k} {names[f]} {u} vs {v}");
                }
            }
        }

        // ---- The levers' own step-in (M10, fixed) -----------------------------------------------------------------------
        /// <summary>
        /// The levers step in and out at 0.4 m/s (<c>updateAct3</c>, L2902, L2916), their station's own speed
        /// (<see cref="Mechanisms.Station.StepInSpeed"/>), where the motor's other stations step at 0.45 (L1845, L4382); the
        /// scene runs on the prototype's motor tuning. The stop lever, turned at #13477: 0.11 m in 16 steps, the clip on the
        /// 17th (#13494; at 0.45 it took 15 and the clip started a step early).
        /// </summary>
        [Fact]
        public void TheLeversStepInAtTheirOwn0_4_M10()
        {
            Assert.Null(Dl06Scene.Def().Motor);
            var rows = Run().Rows;
            int clip = rows.FindIndex(w => CoreAct(w) == "dl06.stopLever:Clip");
            Assert.Equal(13494, rows[clip].P.I);
            int stepIn = rows.FindIndex(w => CoreAct(w) == "dl06.stopLever:StepIn");
            Assert.Equal(16, clip - stepIn - 1);
            Assert.Equal(0.4 / 60, Math.Abs(rows[stepIn + 2].Z - rows[stepIn + 1].Z), 12);
        }

        // ---- Dump ---------------------------------------------------------------------------------------------------
        /// <summary>Writes the window side by side as TSV when DL06_TRACE_DUMP names a file.</summary>
        [Fact]
        public void Dump()
        {
            var path = Environment.GetEnvironmentVariable("DL06_TRACE_DUMP");
            if (string.IsNullOrEmpty(path)) return;
            var t = Trace.Load(TraceFile);
            var sb = new StringBuilder("i\tpx\tcx\tpz\tcz\tpvx\tcvx\tpyaw\tcyaw\tpact\tcact\tpcp\tccp\tpscan\tcscan\tpst\tcst\tpsl\tcsl\tppl\tcpl\tin\tpcr\tccr\n");
            foreach (var w in Run().Rows)
            {
                var p = w.P;
                sb.Append(p.I).Append('\t').Append(p.X).Append('\t').Append(R(w.X)).Append('\t').Append(-p.Z).Append('\t').Append(R(w.Z))
                  .Append('\t').Append(p.Vx).Append('\t').Append(R(w.Vx)).Append('\t').Append(p.Yaw).Append('\t').Append(R(w.Yaw))
                  .Append('\t').Append(ExpectedAct(t, p)).Append('\t').Append(CoreAct(w)).Append('\t').Append(p.Cp).Append('\t').Append(w.Cp)
                  .Append('\t').Append(p.Sp6).Append('\t').Append(w.Scan).Append('\t').Append(p.St6).Append('\t').Append(R(w.ScanT))
                  .Append('\t').Append(p.Sl6).Append('\t').Append(R(w.Stop)).Append('\t').Append(p.Pl6).Append('\t').Append(R(w.Points))
                  .Append('\t').Append(p.L ? "L" : "").Append(p.R ? "R" : "").Append(p.JP ? "J" : "").Append(p.UP ? "U" : "")
                  .Append('\t').Append(p.Cr6).Append('\t').Append(w.Carriers).Append('\n');
            }
            File.WriteAllText(path, sb.ToString());
        }

        // ---- Helpers --------------------------------------------------------------------------------------------------
        /// <summary>
        /// The prototype's act as Core names it (<see cref="SceneSim.ActKind"/>:<see cref="SceneSim.ActPhase"/>): the scanner's
        /// acts; a lever act by the lever it is on (the one whose stand point he reaches: <c>a.which</c> is not recorded) and
        /// the motor's phases; quirks by their clip.
        /// </summary>
        internal static string ExpectedAct(Trace t, TraceStep p)
        {
            if (p.Mt) return "mantle:";
            if (p.Act == null) return null;
            var parts = p.Act.Split(':');
            string kind = parts[0], phase = parts[1];
            switch (kind)
            {
                case "quirk": return "quirk:" + phase;
                case "scan": return "dl06.scanner:Scan";
                case "check": return "dl06.scanner:Check";
                case "fall": return "dl06.chute:" + char.ToUpperInvariant(phase[0]) + phase.Substring(1);
                case "lever":
                {
                    // The act's own clip step: ahead of it while he approaches, turns and steps in; behind it from the clip on.
                    double stand = double.NaN;
                    bool back = phase == "act" || phase == "out";
                    for (int i = p.I; i >= 0 && i < t.Steps.Count && double.IsNaN(stand); i += back ? -1 : 1) if (t.Steps[i].Act == "lever:act") stand = t.Steps[i].X;
                    string who = Math.Abs(stand - 62.5) < 1e-9 ? "dl06.stopLever" : Math.Abs(stand - 63.3) < 1e-9 ? "dl06.points" : "?";
                    string ph = phase == "approach" ? "Approach" : phase == "turn" ? "Turn" : phase == "in" ? "StepIn" : phase == "act" ? "Clip" : "StepOut";
                    return who + ":" + ph;
                }
                default: return kind + ":" + phase;
            }
        }

        internal static string CoreAct(Row r) => r.Kind == null ? null : r.Kind + ":" + (r.Kind == "mantle" ? "" : r.Phase);

        private static void Check(List<string> bad, int i, string what, double proto, double core)
        {
            if (!(Math.Abs(core - proto) <= Tol)) bad.Add($"#{i} {what} {proto:R} vs {core:R}");
        }

        private static string Report(List<string> bad)
        {
            var sb = new StringBuilder().Append(bad.Count).Append(" mismatches");
            for (int i = 0; i < bad.Count && i < 16; i++) sb.Append("\n  ").Append(bad[i]);
            return sb.ToString();
        }
    }
}
