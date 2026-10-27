using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Chapter 1 Attendance as far as it is ported, replayed through ONE <see cref="ChapterSim"/> over
    /// <see cref="ChapterDefs.Attendance"/>: the prototype's own run (the mechanical bot from <c>school</c>, seed 1,
    /// Traces/attendance_mech_seed1.jsonl.gz, <c>CHAPTER=att</c>) from its first step to the first step of the scene after
    /// the last ported one, input for input, with no hand-over anywhere. As <see cref="PrologueChapterTraceTests"/>: what
    /// every scene shares is compared here (his pose, acts, holds, checkpoints, the scene that holds him), each scene's
    /// own signals by its probe (ChapterTrace/, <see cref="ChapterTraceProbes.Attendance"/>). Nothing is compensated.
    /// </summary>
    public class AttendanceChapterTraceTests
    {
        internal const string TraceFile = "attendance_mech_seed1.jsonl.gz";

        private static ChapterTraceRun _cached;
        private static readonly object Gate = new object();

        /// <summary>The window: the first step to the first step of the first scene with no probe (named by its full ID: "DL-14a").</summary>
        internal static (int from, int to) Window(Trace t, IReadOnlyList<IChapterTraceProbe> probes)
        {
            var ported = new HashSet<string>();
            foreach (var p in probes) ported.Add(p.Scene);
            return (t.FirstIndex(p => p.Mode == "play"), t.FirstIndex(p => p.Mode == "play" && p.Scene != null && !ported.Contains(SceneId(p.Scene))));
        }

        internal static ChapterTraceRun Run()
        {
            lock (Gate)
            {
                if (_cached != null) return _cached;
                var t = Trace.Load(TraceFile);
                var probes = ChapterTraceProbes.Attendance();
                var (from, to) = Window(t, probes);
                var sim = new ChapterSim(ChapterDefs.Attendance());
                var r = new ChapterTraceRun { Trace = t, Sim = sim, Probes = probes };
                int step = from - 1;
                sim.SceneChanged += (a, b, dir) => r.Changes.Add((step, a?.Id, b?.Id, dir));
                sim.Clock = from > 0 ? t.Steps[from - 1].Clk : 0;                    // the recorder starts the clock at 0 (step 0's startAt)
                sim.Begin("school");
                r.Changes.Clear();                                                  // the placement at school
                foreach (var p in probes) p.Bind(sim, t);

                for (int k = from; k <= to; k++)
                {
                    step = t.Steps[k].I;
                    sim.Step(t.Steps[k].Input);
                    var cues = new StringBuilder();
                    foreach (var c in sim.Cues) cues.Append(cues.Length > 0 ? "," : "").Append(c);
                    r.Rows.Add(new ChapterTraceRow
                    {
                        P = t.Steps[k], X = sim.X, Y = sim.Y, Z = sim.Z, Vx = sim.Vx, Yaw = sim.Yaw, G = sim.Grounded, Exited = sim.Exited,
                        Act = ActOf(sim), Cp = sim.Checkpoints.Current.Name, Hold = HoldName(sim.Motor), Scene = sim.Current?.Id, Region = sim.Region,
                        Cues = cues.ToString(),
                    });
                    foreach (var p in probes) p.Record(sim);
                }
                return _cached = r;
            }
        }

        public static IEnumerable<object[]> Scenes()
        {
            foreach (var p in ChapterTraceProbes.Attendance()) yield return new object[] { p.Scene };
        }

        private static IChapterTraceProbe Probe(ChapterTraceRun r, string scene)
        {
            foreach (var p in r.Probes) if (p.Scene == scene) return p;
            throw new ArgumentException("No probe for " + scene + ".", nameof(scene));
        }

        [Fact]
        public void TheTrace_IsChapter1FromSchool_Deterministic()
        {
            var t = Trace.Load(TraceFile);
            Assert.Equal("att", t.Header.GetProperty("chapter").GetString());
            Assert.Equal("school", t.Header.GetProperty("start").GetString());
            Assert.Null(t.EndError);
            Assert.Equal(20842, t.Steps.Count);
            Assert.Equal("school", t.Steps[0].Cp);
            Assert.Equal(6, t.Steps[0].Region);
            Assert.Equal(1.0 / 60, t.Steps[0].Clk);
        }

        // ---- The window -------------------------------------------------------------------------------------------------
        [Fact]
        public void Window_IsTheFirstStep_ToTheFirstStepPastThePortedScenes_NoHandOver()
        {
            var r = Run();
            var (from, to) = Window(r.Trace, r.Probes);
            Assert.Equal(r.Probes[0].FirstStep, from);
            var rows = r.Rows;
            Assert.Equal(to - from + 1, rows.Count);
            for (int k = 1; k < rows.Count; k++) Assert.Equal(rows[k - 1].P.I + 1, rows[k].P.I);
            var scenes = new List<string>();
            foreach (var w in rows) if (scenes.Count == 0 || scenes[scenes.Count - 1] != Scene5(w)) scenes.Add(Scene5(w));
            var want = new List<string>();
            foreach (var p in r.Probes) want.Add(p.Scene);
            want.Add(Scene5(rows[rows.Count - 1]));
            Assert.Equal(want, scenes);
        }

        // ---- (a) position -----------------------------------------------------------------------------------------------
        [Fact]
        public void X_Y_Z_Vx_Yaw_Grounded_AndRegion_MatchEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Run().Rows)
            {
                Check(bad, w.P.I, "x", w.P.X, w.X);
                Check(bad, w.P.I, "y", w.P.Y, w.Y);
                Check(bad, w.P.I, "z", -w.P.Z, w.Z);                                            // Unity z = −three z (§0.2)
                Check(bad, w.P.I, "vx", w.P.Vx, w.Vx);
                Check(bad, w.P.I, "yaw", w.P.Yaw, w.Yaw);
                if (w.G != w.P.G) bad.Add($"#{w.P.I} grounded {w.P.G} vs {w.G}");
                if (w.Region != w.P.Region) bad.Add($"#{w.P.I} region {w.P.Region} vs {w.Region}");
            }
            Assert.True(bad.Count == 0, Report(bad));
        }

        // ---- (b) acts, holds, checkpoints ---------------------------------------------------------------------------------
        [Fact]
        public void Acts_And_Holds_MatchEveryStep()
        {
            var r = Run();
            var bad = new List<string>();
            var seen = new HashSet<string>();
            foreach (var w in r.Rows)
            {
                string want = ExpectedAct(r, w.P);
                if (want != null) seen.Add(want);
                if (want != w.Act) bad.Add($"#{w.P.I} {Scene5(w)} act {want ?? "-"} vs {w.Act ?? "-"}");
                if (w.P.Hold != w.Hold) bad.Add($"#{w.P.I} hold {w.P.Hold ?? "-"} vs {w.Hold ?? "-"}");
            }
            Assert.True(bad.Count == 0, Report(bad));
            foreach (var p in r.Probes)
                foreach (var a in p.KeyActs) Assert.True(seen.Contains(a), p.Scene + ": " + a);
        }

        [Fact]
        public void Checkpoints_FireOnThePrototypesSteps()
        {
            var r = Run();
            var bad = new List<string>();
            var order = new List<string>();
            foreach (var w in r.Rows)
            {
                if (w.P.Cp != w.Cp) bad.Add($"#{w.P.I} checkpoint {w.P.Cp} vs {w.Cp}");
                if (order.Count == 0 || order[order.Count - 1] != w.Cp) order.Add(w.Cp);
            }
            Assert.True(bad.Count == 0, Report(bad));
            var want = new List<string>();
            foreach (var p in r.Probes) foreach (var cp in ChapterDefs.AttendanceCheckpoints.Of(p.Scene)) want.Add(cp.Name);
            // The scene after the last ported one may reach its first checkpoint on the window's last step; not here.
            Assert.Equal(want, order);
        }

        // ---- (c) the scenes -------------------------------------------------------------------------------------------------
        [Fact]
        public void CurrentScene_IsTheSceneName_EveryStep_AndSceneChangedFiresAtEachSeam()
        {
            var r = Run();
            var bad = new List<string>();
            var seams = new List<(int, string, string, ExitDir)>();
            string last = r.Probes[0].Scene, after = Scene5(r.Rows[r.Rows.Count - 1]);
            foreach (var w in r.Rows)
            {
                string proto = Scene5(w), core = w.Scene ?? after;
                if (proto != core) bad.Add($"#{w.P.I} scene {proto} vs {core}");
                if (proto != last) { seams.Add((w.P.I, last, proto == after ? null : proto, ExitDir.Right)); last = proto; }
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(seams, r.Changes);
            var steps = new List<int>();
            for (int i = 1; i < r.Probes.Count; i++) steps.Add(r.Probes[i].FirstStep);
            steps.Add(r.Rows[r.Rows.Count - 1].P.I);
            Assert.Equal(steps, r.Changes.ConvertAll(c => c.step));
            Assert.True(r.Rows[r.Rows.Count - 1].Exited);
            for (int k = 0; k < r.Rows.Count - 1; k++) Assert.False(r.Rows[k].Exited);
        }

        [Theory]
        [MemberData(nameof(Scenes))]
        public void Cues_AreRaisedOnThePrototypesSteps(string scene)
        {
            var r = Run();
            var cues = new List<(int, string)>();
            foreach (var w in r.Rows) if (w.Cues.Length > 0) foreach (var c in w.Cues.Split(',')) cues.Add((w.P.I, c));
            foreach (var (step, cue) in Probe(r, scene).KeyCues)
                Assert.True(cues.Exists(c => c.Item2 == cue && (step == 0 || c.Item1 == step)), scene + ": " + cue + (step == 0 ? "" : " at #" + step));
        }

        // ---- (d) every scene's mechanisms ---------------------------------------------------------------------------------
        [Theory]
        [MemberData(nameof(Scenes))]
        public void Mechanisms_MatchEveryStep(string scene)
        {
            var r = Run();
            var bad = new List<string>();
            Probe(r, scene).CheckMechanisms(r, bad);
            Assert.True(bad.Count == 0, scene + ": " + Report(bad));
        }

        // ---- Helpers --------------------------------------------------------------------------------------------------------
        /// <summary>"DL-14a" and "DL-14b" are scenes of their own; the prototype's name starts with the ID and a space.</summary>
        internal static string SceneId(string sceneName) => sceneName.Substring(0, sceneName.IndexOf(' '));

        private static string Scene5(ChapterTraceRow w) => SceneId(w.P.Scene);

        private static string ExpectedAct(ChapterTraceRun r, TraceStep p)
        {
            foreach (var probe in r.Probes) if (probe.ClaimsAct(p)) return probe.ExpectedAct(r.Trace, p);
            string scene = SceneId(p.Scene);
            foreach (var probe in r.Probes) if (probe.Scene == scene) return probe.ExpectedAct(r.Trace, p);
            return r.Probes[r.Probes.Count - 1].ExpectedAct(r.Trace, p);
        }

        private static string ActOf(ChapterSim sim)
        {
            string kind = SceneSim.KindOf(sim);
            return kind == null ? null : kind + ":" + (kind == "mantle" ? "" : SceneSim.PhaseOf(sim));
        }

        /// <summary>What his hands hold, as the trace records it: <c>item</c>, or <c>push:</c> and the pushable's key.</summary>
        private static string HoldName(D17Motor m)
        {
            if (m.Hold == HoldKind.None) return null;
            if (m.Hold == HoldKind.Item) return "item";
            var b = Base(m.Pushed);
            return "push:" + PushKey(b.Id.Value) + (m.Pushed is Push.PushTwin ? "Alt" : "");
        }

        /// <summary>The prototype's <c>PUSHABLES</c> key of a chapter 1 pushable.</summary>
        internal static string PushKey(string id)
        {
            switch (id)
            {
                case "dl12.figure": return "fig";
                case "dl13.figure": return "fig2";
                default: return id;
            }
        }

        /// <summary>Debugging aid, not a test: the replay side by side as TSV.</summary>
        internal static void Dump(string path)
        {
            var r = Run();
            var sb = new StringBuilder("i\tsc\tcsc\tpx\tcx\tpy\tcy\tpz\tcz\tpvx\tcvx\tpyaw\tcyaw\tpg\tcg\tpact\tcact\tph\tch\tpcp\tccp\tcues\tin\n");
            foreach (var w in r.Rows)
            {
                var p = w.P;
                sb.Append(p.I).Append('\t').Append(Scene5(w)).Append('\t').Append(w.Scene)
                  .Append('\t').Append(p.X).Append('\t').Append(R(w.X)).Append('\t').Append(p.Y).Append('\t').Append(R(w.Y))
                  .Append('\t').Append(-p.Z).Append('\t').Append(R(w.Z)).Append('\t').Append(p.Vx).Append('\t').Append(R(w.Vx))
                  .Append('\t').Append(p.Yaw).Append('\t').Append(R(w.Yaw)).Append('\t').Append(p.G ? 1 : 0).Append('\t').Append(w.G ? 1 : 0)
                  .Append('\t').Append(ExpectedAct(r, p)).Append('\t').Append(w.Act).Append('\t').Append(p.Hold).Append('\t').Append(w.Hold)
                  .Append('\t').Append(p.Cp).Append('\t').Append(w.Cp).Append('\t').Append(w.Cues)
                  .Append('\t').Append(p.L ? "L" : "").Append(p.R ? "R" : "").Append(p.JP ? "J" : "").Append(p.UP ? "U" : "").Append(p.SH ? "S" : "").Append('\n');
            }
            File.WriteAllText(path, sb.ToString());
        }
    }
}
