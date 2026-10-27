using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// One scene's part of the whole-chapter trace replay (<see cref="PrologueChapterTraceTests"/>): the chapter replays
    /// the prototype's run through one <see cref="ChapterSim"/> and compares what every scene shares (D-17's pose, acts,
    /// holds, checkpoints, the scene that holds him); each probe reads its own scene's trace columns, samples its own
    /// mechanisms after every step, names the prototype's acts as its scene replay does, and checks its own signals.
    /// <para>Porting a scene into the chapter replay is one probe file here plus one line in
    /// <see cref="ChapterTraceProbes.Prologue"/>; nothing else in the chapter replay changes.</para>
    /// </summary>
    internal interface IChapterTraceProbe
    {
        /// <summary>The scene ("DL-03"), as the trace's <c>sceneName</c> starts.</summary>
        string Scene { get; }
        /// <summary>The trace step its scene first holds him (the window's first step for the chapter's first scene).</summary>
        int FirstStep { get; }
        /// <summary>Acts the replay must show at least once, named as <see cref="ExpectedAct"/> names them.</summary>
        IReadOnlyList<string> KeyActs { get; }
        /// <summary>Cues the replay must raise: on that step, or on any step when the step is 0.</summary>
        IReadOnlyList<(int step, string cue)> KeyCues { get; }

        /// <summary>Once, after the chapter is built and begun: look up its mechanisms.</summary>
        void Bind(ChapterSim sim, Trace t);
        /// <summary>After every step of the window, in order: sample its signals (row k is the k-th call).</summary>
        void Record(ChapterSim sim);
        /// <summary>It names the act of <paramref name="p"/>, a step outside its scene (DL-01: the passage's last legs, to <c>room</c>).</summary>
        bool ClaimsAct(TraceStep p);
        /// <summary>The prototype's act at <paramref name="p"/> as its scene replay names it (<see cref="SceneSim.ActKind"/>:<see cref="SceneSim.ActPhase"/>).</summary>
        string ExpectedAct(Trace t, TraceStep p);
        /// <summary>Its mechanisms against the prototype's over the steps its scene replay compares them; adds each mismatch to <paramref name="bad"/>.</summary>
        void CheckMechanisms(ChapterTraceRun run, List<string> bad);
    }

    /// <summary>A probe that samples a <typeparamref name="T"/> per step (<see cref="Samples"/>[k] goes with <see cref="ChapterTraceRun.Rows"/>[k]).</summary>
    internal abstract class ChapterTraceProbe<T> : IChapterTraceProbe
    {
        protected readonly List<T> Samples = new List<T>();

        public abstract string Scene { get; }
        public abstract int FirstStep { get; }
        public abstract IReadOnlyList<string> KeyActs { get; }
        public virtual IReadOnlyList<(int step, string cue)> KeyCues => Array.Empty<(int, string)>();

        public abstract void Bind(ChapterSim sim, Trace t);
        public void Record(ChapterSim sim) => Samples.Add(Sample(sim));
        protected abstract T Sample(ChapterSim sim);
        public virtual bool ClaimsAct(TraceStep p) => false;
        public abstract string ExpectedAct(Trace t, TraceStep p);
        public abstract void CheckMechanisms(ChapterTraceRun run, List<string> bad);
    }

    /// <summary>What every scene shares at one step of the chapter replay: the prototype's record and Core's.</summary>
    internal sealed class ChapterTraceRow
    {
        public TraceStep P;
        public double X, Y, Z, Vx, Yaw;
        public bool G, Exited;
        public string Act, Cp, Hold, Scene, Cues;
        public int Region;

        /// <summary>The prototype's scene at this step ("DL-03").</summary>
        public string ProtoScene => P.Scene.Substring(0, 5);
    }

    /// <summary>The chapter replay, as the probes read it.</summary>
    internal sealed class ChapterTraceRun
    {
        public Trace Trace;
        public ChapterSim Sim;
        public IReadOnlyList<IChapterTraceProbe> Probes;
        public readonly List<ChapterTraceRow> Rows = new List<ChapterTraceRow>();
        public readonly List<(int step, string from, string to, ExitDir dir)> Changes = new List<(int, string, string, ExitDir)>();

        /// <summary>The row of trace step <paramref name="step"/> (−1: not in the window).</summary>
        public int RowOf(int step) => Rows.FindIndex(w => w.P.I == step);

        /// <summary>
        /// The row of the first step after <paramref name="scene"/>'s: the next probe's first step, or the window's last
        /// (the first step of the scene after the chapter's last ported one).
        /// </summary>
        public int RowAfter(string scene)
        {
            for (int i = 0; i < Probes.Count - 1; i++) if (Probes[i].Scene == scene) return RowOf(Probes[i + 1].FirstStep);
            return Rows.Count - 1;
        }
    }

    /// <summary>The comparisons the chapter replay and its probes share.</summary>
    internal static class ChapterTraceKit
    {
        public const double Tol = 1e-6, Dt = 1.0 / 60.0;

        /// <summary>Within 1e-6, the replays' tolerance on every continuous value.</summary>
        public static void Check(List<string> bad, int i, string what, double proto, double core)
        {
            if (!(Math.Abs(core - proto) <= Tol)) bad.Add($"#{i} {what} {proto:R} vs {core:R}");
        }

        public static string Report(List<string> bad)
        {
            var sb = new StringBuilder().Append(bad.Count).Append(" mismatches");
            for (int i = 0; i < bad.Count && i < 16; i++) sb.Append("\n  ").Append(bad[i]);
            return sb.ToString();
        }

        public static string R(double v) => v.ToString("R", CultureInfo.InvariantCulture);

        /// <summary>The pushable behind a face (a <see cref="PushTwin"/>'s base).</summary>
        public static Mechanism Base(IPushable p) => p is PushTwin tw ? tw.Base : p as Mechanism;
    }
}
