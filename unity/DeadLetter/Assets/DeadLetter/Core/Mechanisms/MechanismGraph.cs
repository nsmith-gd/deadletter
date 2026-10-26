using System;
using System.Collections.Generic;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms
{
    /// <summary>
    /// Owns a scene's mechanisms and steps them. <b>Step order is the order of <see cref="Add{T}"/></b>: add them in the
    /// scene definition's order, which follows the prototype's update order (relays #5, then <c>updateMechanisms</c>,
    /// <c>updateDL0x</c>, ... #6–7; §3.1). A mechanism reading another through <see cref="MechanismLinker.Read{T}"/>
    /// must be added after it, so it sees this tick's value; <see cref="Build"/> throws otherwise.
    /// Usage: <c>Add</c> ... <c>Build()</c> → <c>Reset(cp)</c> → <c>Step(dt, pose)</c> each FixedTick step.
    /// </summary>
    public sealed class MechanismGraph
    {
        private readonly List<IMechanism> _order = new List<IMechanism>();
        private readonly Dictionary<MechanismId, int> _index = new Dictionary<MechanismId, int>();
        private readonly ScopedSnapshot _scope = new ScopedSnapshot();
        private bool _built;

        public MechanismGraph(int logCapacity = 64) { Log = new MechanismLog(logCapacity); }

        /// <summary>This step's transitions and one-shots (cleared at the start of each Step).</summary>
        public MechanismLog Log { get; }

        /// <summary>Steps taken since Build (restored by snapshots).</summary>
        public long Tick { get; private set; }

        /// <summary>
        /// The persist flags (§4.28): story state that outlives a reload (the DL-17 drawer read, ...). Mechanisms read
        /// them through <see cref="MechanismLinker.Flags"/>; <c>CheckpointService</c> owns their saving.
        /// </summary>
        public PersistFlags Flags { get; } = new PersistFlags();

        /// <summary>The calm accessibility option, passed to every step.</summary>
        public bool Calm { get; set; }

        public int Count => _order.Count;
        public IMechanism this[int i] => _order[i];

        public T Add<T>(T mechanism) where T : class, IMechanism
        {
            if (_built) throw new InvalidOperationException("Add before Build.");
            if (mechanism == null) throw new ArgumentNullException(nameof(mechanism));
            if (_index.ContainsKey(mechanism.Id)) throw new ArgumentException("Duplicate mechanism ID " + mechanism.Id + ".");
            _index.Add(mechanism.Id, _order.Count);
            _order.Add(mechanism);
            return mechanism;
        }

        /// <summary>Links every mechanism, in order. Call once, after the last Add.</summary>
        public void Build()
        {
            if (_built) throw new InvalidOperationException("Already built.");
            var linker = new MechanismLinker(this);
            for (int i = 0; i < _order.Count; i++)
            {
                linker.Reader = i;
                _order[i].Link(linker);
            }
            _built = true;
        }

        public bool TryGet<T>(MechanismId id, out T mechanism) where T : class
        {
            mechanism = _index.TryGetValue(id, out int i) ? _order[i] as T : null;
            return mechanism != null;
        }

        public T Get<T>(MechanismId id) where T : class
        {
            if (!_index.TryGetValue(id, out int i)) throw new KeyNotFoundException("No mechanism " + id + ".");
            return _order[i] as T ?? throw new InvalidCastException(id + " is a " + _order[i].GetType().Name + ", not a " + typeof(T).Name + ".");
        }

        /// <summary>Rebuild every mechanism for <paramref name="checkpoint"/>, in step order. The tick count carries on.</summary>
        public void Reset(in Checkpoint checkpoint)
        {
            RequireBuilt();
            Log.Clear();
            for (int i = 0; i < _order.Count; i++) _order[i].Reset(checkpoint);
        }

        /// <summary>One fixed step of every mechanism, in order.</summary>
        public void Step(double dt, in PlayerPose player)
        {
            RequireBuilt();
            Log.Clear();
            var ctx = new StepContext(dt, Tick, player, Calm, Log);
            for (int i = 0; i < _order.Count; i++) _order[i].Step(ctx);
            Tick++;
        }

        /// <summary>Every mechanism's fields under <c>id/field</c>, plus the tick.</summary>
        public void Snapshot(ISnapshotWriter w)
        {
            RequireBuilt();
            w.WriteLong("graph/tick", Tick);
            for (int i = 0; i < _order.Count; i++)
            {
                _scope.Begin(_order[i].Id, w, null);
                _order[i].Snapshot(_scope);
            }
        }

        /// <summary>Restore a snapshot taken from a graph built from the same scene definition.</summary>
        public void Restore(ISnapshotReader r)
        {
            RequireBuilt();
            Log.Clear();
            Tick = r.ReadLong("graph/tick");
            for (int i = 0; i < _order.Count; i++)
            {
                _scope.Begin(_order[i].Id, null, r);
                _order[i].Restore(_scope);
            }
        }

        internal int IndexOf(MechanismId id) => _index.TryGetValue(id, out int i) ? i : -1;

        private void RequireBuilt()
        {
            if (!_built) throw new InvalidOperationException("Call Build() first.");
        }

        /// <summary>Prefixes keys with the mechanism ID, so each mechanism writes plain field names.</summary>
        private sealed class ScopedSnapshot : ISnapshotWriter, ISnapshotReader
        {
            private string _prefix;
            private ISnapshotWriter _w;
            private ISnapshotReader _r;

            public void Begin(MechanismId id, ISnapshotWriter w, ISnapshotReader r)
            {
                _prefix = id.Value + "/"; _w = w; _r = r;
            }

            public void WriteDouble(string key, double value) => _w.WriteDouble(_prefix + key, value);
            public void WriteLong(string key, long value) => _w.WriteLong(_prefix + key, value);
            public void WriteBool(string key, bool value) => _w.WriteBool(_prefix + key, value);
            public double ReadDouble(string key) => _r.ReadDouble(_prefix + key);
            public long ReadLong(string key) => _r.ReadLong(_prefix + key);
            public bool ReadBool(string key) => _r.ReadBool(_prefix + key);
        }
    }

    /// <summary>Resolves a mechanism's inputs during <see cref="MechanismGraph.Build"/>.</summary>
    public sealed class MechanismLinker
    {
        private readonly MechanismGraph _graph;

        internal MechanismLinker(MechanismGraph graph) { _graph = graph; }

        internal int Reader;

        /// <summary>The graph's persist flags: resolve a name here, read the handle in Reset and Step.</summary>
        public IPersistFlagReader Flags => _graph.Flags;

        /// <summary>
        /// The source's signal as of this tick: the source must step before the reader (be added earlier).
        /// <see cref="MechanismId.None"/> returns null (an optional input left unwired).
        /// </summary>
        public T Read<T>(MechanismId source) where T : class => Resolve<T>(source, sameTick: true);

        /// <summary>
        /// The source in any order: for reads made outside Step (in an act callback, which runs before the graph steps)
        /// or a deliberate one-tick lag that breaks a cycle (a pawl reads the platform; the platform reads the pawl).
        /// </summary>
        public T ReadAnyOrder<T>(MechanismId source) where T : class => Resolve<T>(source, sameTick: false);

        private T Resolve<T>(MechanismId source, bool sameTick) where T : class
        {
            if (source.IsNone) return null;
            int i = _graph.IndexOf(source);
            var reader = _graph[Reader].Id;
            if (i < 0) throw new InvalidOperationException(reader + " reads " + source + ", which is not in the graph.");
            if (!(_graph[i] is T t)) throw new InvalidOperationException(reader + " reads " + source + " as " + typeof(T).Name + ", which it does not implement.");
            if (sameTick && i >= Reader)
                throw new InvalidOperationException(reader + " reads " + source + ", which steps after it: add " + source + " first, or use ReadAnyOrder for a one-tick lag.");
            return t;
        }
    }
}
