using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Tests
{
    /// <summary>Shared helpers for mechanism tests: a 60 Hz graph stepper, act feeding, log queries and snapshots.</summary>
    internal static class Mech
    {
        public const double Dt = 1.0 / 60.0;
        /// <summary>Clip frames per 60 Hz step (24 fps clips).</summary>
        public const double FramesPerStep = 24.0 / 60.0;

        public static Checkpoint Cp(string name = "start") => Checkpoint.Prototype(name);

        /// <summary>Add, Build, Reset to <paramref name="checkpoint"/>.</summary>
        public static MechanismGraph Graph(string checkpoint, params IMechanism[] mechanisms)
        {
            var g = new MechanismGraph();
            foreach (var m in mechanisms) g.Add(m);
            g.Build();
            g.Reset(Cp(checkpoint));
            return g;
        }

        public static MechanismGraph Graph(params IMechanism[] mechanisms) => Graph("start", mechanisms);

        public static PlayerPose Pose(double x, double y = 0, bool crouched = false, bool busy = false,
            bool grounded = true, bool holding = false, double vx = 0)
            => new PlayerPose(x, y, 0, crouched, busy, vx, grounded, holding);

        /// <summary>The pose the step pipeline builds from the real motor (<see cref="PlayerPose.Of"/>).</summary>
        public static PlayerPose Pose(D17Motor m) => PlayerPose.Of(m);

        public static void Run(MechanismGraph g, int steps, PlayerPose? pose = null)
        {
            for (int i = 0; i < steps; i++) g.Step(Dt, pose ?? PlayerPose.Away);
        }

        /// <summary>Steps until <paramref name="until"/> holds after a step; returns the number of steps (or -1).</summary>
        public static int RunUntil(MechanismGraph g, Func<bool> until, int max = 5000, PlayerPose? pose = null)
        {
            for (int i = 1; i <= max; i++)
            {
                g.Step(Dt, pose ?? PlayerPose.Away);
                if (until()) return i;
            }
            return -1;
        }

        /// <summary>
        /// Plays an act on a station as the motor does: each step, OnActFrame with the clip clock (frames 0.4, 0.8, ...)
        /// and the clip from <see cref="IUsable.ProfileFor"/>, then the graph steps; a chained clip (<see cref="ActStep.Then"/>)
        /// restarts the clock as a new part; a hop ends the act (the motor owns it). <paramref name="onStep"/> runs after each
        /// graph step with the frame of the current part. Returns the steps until the act ended.
        /// </summary>
        public static int PlayAct(MechanismGraph g, IUsable u, int max = 2000, Func<int, double> move = null,
            Action<int, double> onStep = null, PlayerPose? pose = null, int startStep = 1)
        {
            var at = pose ?? PlayerPose.Away;
            string clip = u.ProfileFor(new InteractionQuery(at.X, at.Y, at.Z, 1, true, true, HoldKind.None, null, null)).Clip;
            int part = 0, k0 = 0;                                   // frames count from step 0 until a chained clip restarts them
            double prev = (startStep - 1) * FramesPerStep;
            for (int k = startStep; k < startStep + max; k++)
            {
                double f = (k - k0) * FramesPerStep, t = (k - k0) * Dt;
                var step = u.OnActFrame(new ActFrame(prev, f, t, new MotorInput { Move = move?.Invoke(k) ?? 0 }, clip, part));
                g.Step(Dt, at);
                onStep?.Invoke(k, f);
                prev = f;
                if (step.Kind == ActStepKind.Then) { part++; clip = step.Clip; k0 = k; prev = 0; continue; }
                if (step.Kind == ActStepKind.Done || step.Kind == ActStepKind.Hop) return k - startStep + 1;
            }
            return -1;
        }

        public static bool Entered<T>(MechanismGraph g, MechanismId id, T state) where T : struct, Enum
            => g.Log.Has(id, MechanismEventKind.State, Convert.ToInt32(state));

        public static bool Emitted<T>(MechanismGraph g, MechanismId id, T evt) where T : struct, Enum
            => g.Log.Has(id, MechanismEventKind.Event, Convert.ToInt32(evt));

        public static List<MechanismEvent> Events(MechanismGraph g)
        {
            var list = new List<MechanismEvent>();
            for (int i = 0; i < g.Log.Count; i++) list.Add(g.Log[i]);
            return list;
        }

        public static MemorySnapshot Snapshot(MechanismGraph g)
        {
            var s = new MemorySnapshot();
            g.Snapshot(s);
            return s;
        }

        public static string Dump(MechanismGraph g) => Snapshot(g).Dump();
    }

    /// <summary>A settable source of every signal, for testing a consumer on its own.</summary>
    internal sealed class TestSource : Mechanism, ILoad, IPositionSource, IEngageable
    {
        public TestSource(MechanismId id) : base(id) { }
        public double Load { get; set; }
        public double Position { get; set; }
        public bool Engaged { get; set; }
        public override void Reset(in Checkpoint cp) { }
        public override void Step(in StepContext ctx) { }
        protected override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("load", Load); w.WriteDouble("pos", Position); w.WriteBool("on", Engaged);
        }
        protected override void ReadFields(ISnapshotReader r)
        {
            Load = r.ReadDouble("load"); Position = r.ReadDouble("pos"); Engaged = r.ReadBool("on");
        }
    }

    /// <summary>Position counts its own steps; records the order it stepped in and the ticks it saw.</summary>
    internal sealed class Counter : Mechanism, IPositionSource
    {
        private readonly List<string> _trace;
        public readonly List<long> Ticks = new List<long>();
        public Counter(MechanismId id, List<string> trace = null) : base(id) { _trace = trace; }
        public double Position { get; private set; }
        public override void Reset(in Checkpoint cp) => Position = 0;
        public override void Step(in StepContext ctx)
        {
            Position += 1;
            Ticks.Add(ctx.Tick);
            _trace?.Add(Id.Value);
            Enter(ctx, StateCode == 0 ? 1 : 0);
            Emit(ctx, 7, 3, Position);
        }
        protected override void WriteFields(ISnapshotWriter w) => w.WriteDouble("n", Position);
        protected override void ReadFields(ISnapshotReader r) => Position = r.ReadDouble("n");
    }

    /// <summary>Reads a source at Step and records what it saw.</summary>
    internal sealed class Probe : Mechanism
    {
        private readonly MechanismId _source;
        private readonly bool _anyOrder;
        private IPositionSource _s;
        public readonly List<double> Seen = new List<double>();
        public Probe(MechanismId id, MechanismId source, bool anyOrder = false) : base(id) { _source = source; _anyOrder = anyOrder; }
        public override void Link(MechanismLinker link) => _s = _anyOrder ? link.ReadAnyOrder<IPositionSource>(_source) : link.Read<IPositionSource>(_source);
        public override void Reset(in Checkpoint cp) { }
        public override void Step(in StepContext ctx) => Seen.Add(_s.Position);
        protected override void WriteFields(ISnapshotWriter w) { }
        protected override void ReadFields(ISnapshotReader r) { }
    }
}
