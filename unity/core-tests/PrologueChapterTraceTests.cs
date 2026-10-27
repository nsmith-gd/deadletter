using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl03;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// The whole prologue as far as it is ported, DL-01 to DL-06, replayed through ONE <see cref="ChapterSim"/> over
    /// <see cref="ChapterDefs.Prologue"/>: the prototype's own run (the mechanical bot, seed 1,
    /// Traces/prologue_mech_seed1.jsonl.gz) from the first step of play at DL-01's <c>start</c> (#1768, the opening's last
    /// step) to the first step of the scene after the last ported one (DL-07's, #14016), input for input, with no hand-over
    /// anywhere: one motor carries his speed, yaw and holds across every seam, one graph steps every scene's mechanisms all
    /// along, one checkpoint service holds the game.
    /// <para>This class compares what every scene shares, at 1e-6 on every continuous value and discrete ones on the same
    /// step: his pose, the act and what he holds, the checkpoints, and what only a chapter has (the scene that holds him,
    /// <see cref="ChapterSim.Current"/>, is the prototype's <c>sceneName</c> on every step, and
    /// <see cref="ChapterSim.SceneChanged"/> fires exactly on the steps it changes). Each scene's own signals, act names, key
    /// acts and cues are its probe's (<see cref="IChapterTraceProbe"/>, ChapterTrace/; registered in
    /// <see cref="ChapterTraceProbes.Prologue"/>).</para>
    /// <para>Nothing is compensated: the motor's parity gaps M5, M7–M10 are fixed (#30), so every signal is strict.</para>
    /// </summary>
    public class PrologueChapterTraceTests
    {
        private const string TraceFile = Dl01TraceTests.TraceFile;

        private static ChapterTraceRun _cached;
        private static readonly object Gate = new object();

        /// <summary>
        /// The window: the first step of play to the first step of the first scene with no probe (the replay names its act
        /// as the last probe's scene).
        /// </summary>
        internal static (int from, int to) Window(Trace t, IReadOnlyList<IChapterTraceProbe> probes)
        {
            var ported = new HashSet<string>();
            foreach (var p in probes) ported.Add(p.Scene);
            return (t.FirstIndex(p => p.Mode == "play"), t.FirstIndex(p => p.Mode == "play" && p.Scene != null && !ported.Contains(p.Scene.Substring(0, 5))));
        }

        internal static ChapterTraceRun Run()
        {
            lock (Gate)
            {
                if (_cached != null) return _cached;
                var t = Trace.Load(TraceFile);
                var probes = ChapterTraceProbes.Prologue();
                var (from, to) = Window(t, probes);
                var sim = new ChapterSim(ChapterDefs.Prologue());
                var r = new ChapterTraceRun { Trace = t, Sim = sim, Probes = probes };
                int step = from - 1;
                sim.SceneChanged += (a, b, dir) => r.Changes.Add((step, a?.Id, b?.Id, dir));
                sim.Clock = t.Steps[from - 1].Clk;                                  // the quirk timers compare clock differences
                sim.Begin("start", fromOpening: true);
                r.Changes.Clear();                                                  // the placement at start
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

        /// <summary>The ported scenes, for the per-scene theories.</summary>
        public static IEnumerable<object[]> Scenes()
        {
            foreach (var p in ChapterTraceProbes.Prologue()) yield return new object[] { p.Scene };
        }

        private static IChapterTraceProbe Probe(ChapterTraceRun r, string scene)
        {
            foreach (var p in r.Probes) if (p.Scene == scene) return p;
            throw new ArgumentException("No probe for " + scene + ".", nameof(scene));
        }

        // ---- The window -------------------------------------------------------------------------------------------------
        [Fact]
        public void Window_IsTheFirstStepOfPlay_ToTheFirstStepPastThePortedScenes_NoHandOver()
        {
            var r = Run();
            var (from, to) = Window(r.Trace, r.Probes);
            Assert.Equal(r.Probes[0].FirstStep, from);                                          // DL-01's: #1768
            var rows = r.Rows;
            Assert.Equal(to - from + 1, rows.Count);
            for (int k = 1; k < rows.Count; k++) Assert.Equal(rows[k - 1].P.I + 1, rows[k].P.I);
            var scenes = new List<string>();
            foreach (var w in rows) if (scenes.Count == 0 || scenes[scenes.Count - 1] != w.ProtoScene) scenes.Add(w.ProtoScene);
            var want = new List<string>();
            foreach (var p in r.Probes) want.Add(p.Scene);
            want.Add(rows[rows.Count - 1].ProtoScene);                                          // the scene after the ported ones (DL-07, #14016)
            Assert.Equal(want, scenes);
            Assert.DoesNotContain(rows[rows.Count - 1].ProtoScene, want.GetRange(0, r.Probes.Count));
        }

        // ---- (a) position -----------------------------------------------------------------------------------------------
        /// <summary>x, y, z, vx, yaw, grounded and the region at every step from the wake to the belt running to the exit.</summary>
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
        /// <summary>Every act and phase, named as its scene's probe names it, and what his hands hold; every probe's key acts seen.</summary>
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
                if (want != w.Act) bad.Add($"#{w.P.I} {w.ProtoScene} act {want ?? "-"} vs {w.Act ?? "-"}");
                if (w.P.Hold != w.Hold) bad.Add($"#{w.P.I} hold {w.P.Hold ?? "-"} vs {w.Hold ?? "-"}");
            }
            Assert.True(bad.Count == 0, Report(bad));
            foreach (var p in r.Probes)
                foreach (var a in p.KeyActs) Assert.True(seen.Contains(a), p.Scene + ": " + a);
        }

        /// <summary>Every checkpoint on the prototype's step, each ported scene's in turn (its rows of the table), one service all along.</summary>
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
            foreach (var p in r.Probes) foreach (var cp in ChapterDefs.PrologueCheckpoints.Of(p.Scene)) want.Add(cp.Name);
            Assert.Equal(want, order);                                                          // start … scanned
        }

        // ---- (c) the scenes -------------------------------------------------------------------------------------------------
        /// <summary>
        /// The scene that holds him is the prototype's <c>sceneName</c> on every step (by region and x for DL-01 to DL-05, by
        /// what has happened for DL-06 → DL-07, which is past this chapter), and <see cref="ChapterSim.SceneChanged"/> fires
        /// once at each seam, on its step (each probe's <see cref="IChapterTraceProbe.FirstStep"/>, then the window's last),
        /// going right.
        /// </summary>
        [Fact]
        public void CurrentScene_IsTheSceneName_EveryStep_AndSceneChangedFiresAtEachSeam()
        {
            var r = Run();
            var bad = new List<string>();
            var seams = new List<(int, string, string, ExitDir)>();
            string last = r.Probes[0].Scene, after = r.Rows[r.Rows.Count - 1].ProtoScene;
            foreach (var w in r.Rows)
            {
                string proto = w.ProtoScene, core = w.Scene ?? after;                           // past the chapter: the next scene's
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

        /// <summary>Each probe's cues, typed, on their steps.</summary>
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

        // ---- (d) every scene's mechanisms, over the steps its replay compares them -------------------------------------------
        /// <summary>Each ported scene's mechanisms, as its probe compares them (its scene replay's signals and steps).</summary>
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
        /// <summary>
        /// The prototype's act as the probe that covers the step names it: a probe that claims it (DL-01's to <c>room</c>),
        /// else the probe of the step's own scene, else (the window's last step, the scene after) the last probe.
        /// </summary>
        private static string ExpectedAct(ChapterTraceRun r, TraceStep p)
        {
            foreach (var probe in r.Probes) if (probe.ClaimsAct(p)) return probe.ExpectedAct(r.Trace, p);
            string scene = p.Scene.Substring(0, 5);
            foreach (var probe in r.Probes) if (probe.Scene == scene) return probe.ExpectedAct(r.Trace, p);
            return r.Probes[r.Probes.Count - 1].ExpectedAct(r.Trace, p);
        }

        private static string ActOf(ChapterSim sim)
        {
            string kind = SceneSim.KindOf(sim);
            return kind == null ? null : kind + ":" + (kind == "mantle" ? "" : SceneSim.PhaseOf(sim));
        }

        /// <summary>What his hands hold, as the trace records it (<c>game.hold</c>, with <c>pushKey</c> for a pushable).</summary>
        private static string HoldName(D17Motor m)
        {
            if (m.Hold == HoldKind.None) return null;
            if (m.Hold == HoldKind.Item) return m.Carried is Dl03Weight ? "weight" : "item";
            var b = Base(m.Pushed);
            string key = b.Id.Value.Substring(b.Id.Value.IndexOf('.') + 1);
            if (key == "trolley") return "trolley";                                                      // DL-03's: hold 'trolley'
            return "push:" + key + (m.Pushed is PushTwin ? "Alt" : "");
        }

        /// <summary>
        /// Debugging aid, not a test: writes the replay side by side as TSV to <paramref name="path"/> (call it from a scratch
        /// test or the debugger).
        /// </summary>
        internal static void Dump(string path)
        {
            var r = Run();
            var sb = new StringBuilder("i\tsc\tcsc\tpx\tcx\tpy\tcy\tpz\tcz\tpvx\tcvx\tpyaw\tcyaw\tpg\tcg\tpact\tcact\tph\tch\tpcp\tccp\tcues\tin\n");
            foreach (var w in r.Rows)
            {
                var p = w.P;
                sb.Append(p.I).Append('\t').Append(w.ProtoScene).Append('\t').Append(w.Scene)
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
