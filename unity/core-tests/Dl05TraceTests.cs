using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl05;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-05 parity (U-20): the prototype's own run (the mechanical bot, seed 1, Traces/prologue_mech_seed1.jsonl.gz, with
    /// DL-05's fields: the drum, the body, the weigh-in's load, reading, needle, dip and twitch, the hatch, the flag)
    /// replayed through Core's <see cref="SceneSim"/> with <see cref="Dl05Scene.Def"/>, input for input, compared at every
    /// 60 Hz step.
    /// <para><b>One window</b>, from his last rest before DL-05 (the end of DL-04's bay touch: the motor cannot be handed a
    /// moving D-17, <see cref="SceneSim.Handover"/>, under DL-04's <c>solved</c>) through <c>bay</c>, <c>ration</c>, the label
    /// check, standing on the plate (UNDER), the drum pushed over the plate (UNDER, PERSON, OVER) and on to the wall (set),
    /// the first grab of the body and its hesitation, the drag onto the plate (PERSON, served, the hatch winding up, the
    /// flag), the pat, the crawl under the hatch, <c>hatch</c>, and out into region 3, DL-06.</para>
    /// <para><b>Tolerance 1e-6</b> on every continuous value (the trace rounds to 1e-6; the hand-over pose too). Discrete
    /// signals (acts and phases, holds, grounded, the drum's and the body's states, the reading, served, checkpoints, the
    /// region and the exit) fall on the same step. One compensation, M9 (#28): the hand-over's yaw (below).</para>
    /// </summary>
    public class Dl05TraceTests
    {
        internal const string TraceFile = Dl01TraceTests.TraceFile;
        private const double Tol = 1e-6;

        internal sealed class Row
        {
            public TraceStep P;
            public double X, Y, Z, Vx, Yaw, DrumX, BodyX, Load, Needle, Dip, Twitch, Hatch, Flag;
            public bool G, Exited, Served;
            public string Kind, Phase, Cp, Hold, DrumState, BodyState, Reading;
            public int Region;
        }

        internal sealed class Replay
        {
            public readonly List<Row> Rows = new List<Row>();
            public SceneSim Sim;
            public int From, To;
            public string Checkpoint;
        }

        private static Replay _cached;
        private static readonly object Gate = new object();

        /// <summary>The window: from his last rest before DL-05 to the step into DL-06.</summary>
        internal static (int from, int to) Window(Trace t)
        {
            int first = t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-05"));
            int rest = -1;
            for (int i = first - 1; i > 0 && rest < 0; i--)
            {
                var p = t.Steps[i];
                if (p.Vx == 0 && p.G && p.Act == null && p.Hold == null && !p.Mt) rest = i;
            }
            return (rest + 1, t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-06")));
        }

        internal static Replay Run()
        {
            lock (Gate)
            {
                if (_cached != null) return _cached;
                var t = Trace.Load(TraceFile);
                var (from, to) = Window(t);
                var r = new Replay { From = from, To = to, Checkpoint = t.Steps[from - 1].Cp };
                Pushable drum = null, body = null;
                WeighScale scale = null;
                Door hatch = null, flag = null;
                r.Sim = TraceReplay.Run(t, Dl05Scene.Def(), r.Checkpoint, false, from, to, (p, sim) =>
                {
                    if (drum == null)
                    {
                        drum = sim.Graph.Get<Pushable>("dl05.drum"); body = sim.Graph.Get<Pushable>("dl05.body");
                        scale = sim.Graph.Get<WeighScale>("dl05.weighIn");
                        hatch = sim.Graph.Get<Door>("dl05.hatch"); flag = sim.Graph.Get<Door>("dl05.servedFlag");
                    }
                    r.Rows.Add(new Row
                    {
                        P = p, X = sim.X, Y = sim.Y, Z = sim.Z, Vx = sim.Vx, Yaw = sim.Yaw, G = sim.Grounded,
                        Kind = sim.ActKind, Phase = sim.ActPhase, Cp = sim.Checkpoints.Current.Name, Region = sim.Region, Exited = sim.Exited,
                        Hold = HoldName(sim.Motor, drum, body),
                        DrumX = drum.X, DrumState = StateName(drum, "set"), BodyX = body.X, BodyState = StateName(body, "plate"),
                        Load = scale.Load, Reading = scale.Reading.ToString().ToLowerInvariant(), Needle = scale.Needle, Dip = scale.Dip,
                        Twitch = scale.TwitchOffset, Served = scale.Engaged, Hatch = hatch.Position, Flag = flag.Position,
                    });
                }, (k, sim) =>
                {
                    // The hand-over's yaw: he is still turning back to the lane from the bay touch (#9748 yaw −1.437); the
                    // motor can only be placed facing ±π/2 (D17Motor.Place, #28 M9), so the test hands it the recorded yaw.
                    if (k == from) SetMotorYaw(sim.Motor, t.Steps[from - 1].Yaw);
                    return t.Steps[k].Input;
                }, handover: true);
                return _cached = r;
            }
        }

        /// <summary>The motor keeps no setter for its yaw (U-11): the hand-over gives it the recorded one.</summary>
        private static void SetMotorYaw(D17Motor m, double yaw) => typeof(D17Motor).GetProperty(nameof(D17Motor.Yaw)).SetValue(m, yaw);

        private static string HoldName(D17Motor m, Pushable drum, Pushable body)
        {
            if (m.Hold == HoldKind.None) return null;
            if (m.Hold != HoldKind.Push) return m.Hold.ToString();
            var p = m.Pushed;
            string Key(Pushable b) => ReferenceEquals(p, b) ? b.Id.Value : p is PushTwin tw && ReferenceEquals(tw.Base, b) ? b.Id.Value + "Alt" : null;
            var k = Key(drum) ?? Key(body);
            return k == null ? "push:?" : "push:" + k.Substring("dl05.".Length);
        }

        private static string StateName(Pushable p, string docked)
            => p.State == PushableState.Docked ? docked : p.State == PushableState.Free ? "free" : p.State.ToString();

        // ---- The trace ------------------------------------------------------------------------------------------------
        [Fact]
        public void Trace_HasDl05_AndTheWindowIsWhereExpected()
        {
            var t = Trace.Load(TraceFile);
            var (from, to) = Window(t);
            Assert.Equal(9749, from);
            Assert.Null(t.Steps[from - 1].Act);
            Assert.Equal("bayTouch:act", t.Steps[from - 2].Act);                                  // at rest after DL-04's bay touch
            Assert.Equal("solved", t.Steps[from - 1].Cp);
            Assert.Equal(12073, to);
            Assert.StartsWith("DL-05", t.Steps[to - 1].Scene);
            Assert.Equal(3, t.Steps[to].Region);
            int first = t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-05"));
            Assert.Equal(9868, first);
            Assert.Equal(Dl05Scene.Drum0, t.Steps[first].D5x.Value, 6);
            Assert.Equal(Dl05Scene.Body0, t.Steps[first].B5x.Value, 6);
            Assert.Null(t.Steps[first - 1].D5x);                                                  // DL-05's fields start in DL-05
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
        public void Grounded_MatchesEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Run().Rows) if (w.G != w.P.G) bad.Add($"#{w.P.I} grounded {w.P.G} vs {w.G}");
            Assert.True(bad.Count == 0, Report(bad));
        }

        /// <summary>
        /// Every act and phase on the prototype's steps: the label check, the grabs of the drum and of the body (approach, the
        /// first body grab's hesitation, the Grab clip), the pat; and what his hands hold (the drum, the body, by which face).
        /// </summary>
        [Fact]
        public void Acts_And_Holds_MatchEveryStep()
        {
            var t = Trace.Load(TraceFile);
            var rows = Run().Rows;
            var bad = new List<string>();
            var seen = new HashSet<string>();
            for (int k = 0; k < rows.Count; k++)
            {
                var w = rows[k];
                string want = ExpectedAct(t, w.P), got = CoreAct(w);
                if (want != null) seen.Add(want);
                if (want != got) bad.Add($"#{w.P.I} act {want ?? "-"} vs {got ?? "-"}");
                if (w.P.Hold != w.Hold) bad.Add($"#{w.P.I} hold {w.P.Hold ?? "-"} vs {w.Hold ?? "-"}");
            }
            Assert.True(bad.Count == 0, Report(bad));
            foreach (var a in new[] { "quirk:CheckLabel", "dl05.drum:Approach", "dl05.drum:Clip", "dl05.body:Approach", "dl05.body:Hesitate",
                         "dl05.body:Clip", "quirk:Pat" })
                Assert.Contains(a, seen);
        }

        // ---- (c) checkpoints and the way on -----------------------------------------------------------------------------
        /// <summary><c>bay</c> (L4947), <c>ration</c> (L4935) and <c>hatch</c> (L4936) on the prototype's steps.</summary>
        [Fact]
        public void Checkpoints_FireOnThePrototypesSteps()
        {
            var rows = Run().Rows;
            var bad = new List<string>();
            foreach (var w in rows) if (w.P.Cp != w.Cp) bad.Add($"#{w.P.I} checkpoint {w.P.Cp} vs {w.Cp}");
            Assert.True(bad.Count == 0, Report(bad));
            var first = FirstSteps(rows, w => w.Cp);
            Assert.Equal(new[] { "solved", "bay", "ration", "hatch" }, first.Keys);
            Assert.Equal(9830, first["bay"]);
            Assert.Equal(9890, first["ration"]);
            Assert.Equal(11947, first["hatch"]);
        }

        [Fact]
        public void LeavesDl05_IntoRegion3_OnThePrototypesStep()
        {
            var rows = Run().Rows;
            var last = rows[rows.Count - 1];
            Assert.StartsWith("DL-06", last.P.Scene);
            Assert.True(last.Exited);
            Assert.Equal(3, last.Region);
            Assert.Equal(3, last.P.Region);
            for (int k = 0; k < rows.Count - 1; k++)
            {
                Assert.False(rows[k].Exited, "#" + rows[k].P.I);
                Assert.Equal(rows[k].P.Region, rows[k].Region);
            }
            Assert.Null(last.Kind);
        }

        // ---- (d) mechanisms ---------------------------------------------------------------------------------------------
        /// <summary>
        /// The drum and the body (x, state), the weigh-in (W, its reading, the needle, the plate's dip, the hatch's twitch
        /// lift), served, the hatch's height and the flag, on every step the trace has them (from DL-05's first step).
        /// </summary>
        [Fact]
        public void Mechanisms_MatchEveryStep()
        {
            var bad = new List<string>();
            var readings = new HashSet<string>();
            int compared = 0;
            foreach (var w in Run().Rows)
            {
                var p = w.P;
                if (p.D5x == null) continue;
                compared++;
                Check(bad, p.I, "drum.x", p.D5x.Value, w.DrumX);                                    // L4697
                Check(bad, p.I, "body.x", p.B5x.Value, w.BodyX);
                if (p.D5s != w.DrumState) bad.Add($"#{p.I} drum {p.D5s} vs {w.DrumState}");          // L4728
                if (p.B5s != w.BodyState) bad.Add($"#{p.I} body {p.B5s} vs {w.BodyState}");          // L4729
                Check(bad, p.I, "W", p.W5.Value, w.Load);                                           // L4890–L4892
                if (p.W5r != w.Reading) bad.Add($"#{p.I} reading {p.W5r} vs {w.Reading}");           // L4893
                Check(bad, p.I, "needle", p.N5.Value, w.Needle);                                    // L4903–L4905
                Check(bad, p.I, "dip", p.P5.Value, w.Dip);                                          // L4913
                Check(bad, p.I, "twitch", p.T5.Value, w.Twitch);                                    // L4909–L4910, L4920
                if (p.S5 != w.Served) bad.Add($"#{p.I} served {p.S5} vs {w.Served}");                 // L4901
                Check(bad, p.I, "hatch", p.H5.Value, w.Hatch);                                      // L4916–L4917
                Check(bad, p.I, "flag", p.F5.Value, w.Flag);                                        // L4918
                readings.Add(w.Reading);
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(12073 - 9868 + 1, compared);
            Assert.Equal(new HashSet<string> { "empty", "under", "person", "over" }, readings);
            var rows = Run().Rows;
            var end = rows[rows.Count - 1];
            Assert.True(Math.Abs(end.DrumX - Dl05Scene.DrumPark) < 0.005 && end.DrumState == "set");      // let go within 0.005 of its end, L4724
            Assert.True(Math.Abs(end.BodyX - Dl05Scene.BodyPlate) < 0.005 && end.BodyState == "plate");
            Assert.Equal(0.64, end.Hatch, 9);
            Assert.Equal(1, end.Flag, 9);
        }

        // ---- Dump ---------------------------------------------------------------------------------------------------
        /// <summary>Writes the window side by side as TSV when DL05_TRACE_DUMP names a file.</summary>
        [Fact]
        public void Dump()
        {
            var path = Environment.GetEnvironmentVariable("DL05_TRACE_DUMP");
            if (string.IsNullOrEmpty(path)) return;
            var t = Trace.Load(TraceFile);
            var sb = new StringBuilder("i\tpx\tcx\tpvx\tcvx\tpyaw\tcyaw\tpg\tcg\tpact\tcact\tph\tch\tpcp\tccp\tpdx\tcdx\tpbx\tcbx\tpw\tcw\tpr\tcr\tpn\tcn\tph5\tch5\tin\n");
            foreach (var w in Run().Rows)
            {
                var p = w.P;
                sb.Append(p.I).Append('\t').Append(p.X).Append('\t').Append(w.X.ToString("R")).Append('\t').Append(p.Vx).Append('\t').Append(w.Vx.ToString("R"))
                  .Append('\t').Append(p.Yaw).Append('\t').Append(w.Yaw.ToString("R"))
                  .Append('\t').Append(p.G ? 1 : 0).Append('\t').Append(w.G ? 1 : 0).Append('\t').Append(ExpectedAct(t, p)).Append('\t').Append(CoreAct(w))
                  .Append('\t').Append(p.Hold).Append('\t').Append(w.Hold).Append('\t').Append(p.Cp).Append('\t').Append(w.Cp)
                  .Append('\t').Append(p.D5x).Append('\t').Append(w.DrumX.ToString("R")).Append('\t').Append(p.B5x).Append('\t').Append(w.BodyX.ToString("R"))
                  .Append('\t').Append(p.W5).Append('\t').Append(w.Load.ToString("R")).Append('\t').Append(p.W5r).Append('\t').Append(w.Reading)
                  .Append('\t').Append(p.N5).Append('\t').Append(w.Needle.ToString("R")).Append('\t').Append(p.H5).Append('\t').Append(w.Hatch.ToString("R"))
                  .Append('\t').Append(p.L ? "L" : "").Append(p.R ? "R" : "").Append(p.JP ? "J" : "").Append(p.UP ? "U" : "").Append(p.SH ? "S" : "").Append('\n');
            }
            File.WriteAllText(path, sb.ToString());
        }

        // ---- Helpers --------------------------------------------------------------------------------------------------
        /// <summary>
        /// The prototype's act as Core names it (<see cref="SceneSim.ActKind"/>:<see cref="SceneSim.ActPhase"/>). A grab is
        /// named by what he takes hold of at its end (<c>game.pushKey</c>): the mechanism's own face, or "Grab" for its twin
        /// (a <see cref="PushTwin"/> is not a mechanism, so the motor names the verb).
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
                case "grabPush":
                {
                    string key = null;
                    for (int i = p.I; i < t.Steps.Count && key == null; i++) if (t.Steps[i].Hold != null) key = t.Steps[i].Hold.Substring("push:".Length);
                    string who = key == null ? "?" : key.EndsWith("Alt") ? "Grab" : "dl05." + key;
                    return who + ":" + (phase == "approach" ? "Approach" : phase == "hesitate" ? "Hesitate" : "Clip");
                }
                default: return kind + ":" + phase;
            }
        }

        internal static string CoreAct(Row r) => r.Kind == null ? null : r.Kind + ":" + (r.Kind == "mantle" ? "" : r.Phase);

        private static void Check(List<string> bad, int i, string what, double proto, double core)
        {
            if (!(Math.Abs(core - proto) <= Tol)) bad.Add($"#{i} {what} {proto:R} vs {core:R}");
        }

        private static Dictionary<string, int> FirstSteps(List<Row> rows, Func<Row, string> name)
        {
            var d = new Dictionary<string, int>();
            foreach (var w in rows) { var n = name(w); if (!d.ContainsKey(n)) d[n] = w.P.I; }
            return d;
        }

        private static string Report(List<string> bad)
        {
            var sb = new StringBuilder().Append(bad.Count).Append(" mismatches");
            for (int i = 0; i < bad.Count && i < 16; i++) sb.Append("\n  ").Append(bad[i]);
            return sb.ToString();
        }
    }
}
