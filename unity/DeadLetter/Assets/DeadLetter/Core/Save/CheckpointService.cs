using System;
using System.Collections.Generic;
using DeadLetter.Core.Mechanisms;

namespace DeadLetter.Core.Save
{
    /// <summary>
    /// Checkpoints and saving (§4.28; plan "Recovery and accessibility"). A checkpoint is a name in a total order
    /// (<c>CP_ORDER</c>, L3976). Reaching a later one makes it current, captures the mechanism snapshot and saves;
    /// an earlier or equal one is ignored (the prototype's <c>!past(cp, X)</c> guards, L4935–L4950). Reload (respawn,
    /// <c>loadCheckpoint</c>, L8117) rebuilds the graph from the checkpoint and the persist flags, then puts back the
    /// snapshot taken at the checkpoint, so solved states come back exactly; flags set since then are kept.
    /// <para>Persist flags live in <see cref="MechanismGraph.Flags"/>. State a Core object keeps itself (the White's
    /// <c>Warned</c>) is joined with <see cref="BindFlag"/>: read into the flags before every save and reload, written
    /// back after every reload.</para>
    /// <para>Writes can be rate-limited (<see cref="MinSecondsBetweenWrites"/>; Switch: 2 s): a save inside the window
    /// is held and written by <see cref="Update"/>. The Runtime calls <see cref="Update"/> every frame and
    /// <see cref="Flush"/> on quit/suspend.</para>
    /// <para>Options (<see cref="Settings"/>) are the player's, not the run's: the constructor reads them from the slot
    /// (<see cref="TryLoadSettings"/>) without touching the world, so calm mode, volumes and bindings hold from boot, and
    /// <see cref="NewGame"/> keeps them. Until the service holds a game (<see cref="Started"/>: a new game, a load or a
    /// reached checkpoint) its world is only the scene's start, so a write then puts only the options into the slot and
    /// leaves the slot's checkpoint, flags, play time and snapshot as they are (an empty slot gets a fresh model).</para>
    /// </summary>
    public sealed class CheckpointService
    {
        private readonly MechanismGraph _graph;
        private readonly IReadOnlyList<string> _order;
        private readonly ISaveStore _store;
        private readonly List<(string name, Func<bool> get, Action<bool> set)> _bindings = new List<(string, Func<bool>, Action<bool>)>();
        private MemorySnapshot _snapshot;
        private double _sinceWrite = double.PositiveInfinity;
        private long _savedFlags = -1;

        public CheckpointService(MechanismGraph graph, IReadOnlyList<string> order, ISaveStore store, int slot = 0, string scene = "")
        {
            _graph = graph ?? throw new ArgumentNullException(nameof(graph));
            _order = order ?? throw new ArgumentNullException(nameof(order));
            if (_order.Count == 0) throw new ArgumentException("Empty checkpoint order.", nameof(order));
            _store = store ?? throw new ArgumentNullException(nameof(store));
            Slot = slot;
            Scene = scene ?? "";
            Current = new Checkpoint(_order, _order[0]);
            TryLoadSettings();
        }

        public int Slot { get; }
        /// <summary>The scene the graph belongs to; a saved snapshot is only applied to the same scene.</summary>
        public string Scene { get; set; }
        public Checkpoint Current { get; private set; }
        public PersistFlags Flags => _graph.Flags;
        public Settings Settings { get; private set; } = new Settings();
        /// <summary>Seconds of play (accumulated by <see cref="Update"/>).</summary>
        public double PlayTime { get; private set; }
        /// <summary>The snapshot that the next <see cref="Reload"/> restores (null: derived from the checkpoint only).</summary>
        public MemorySnapshot CheckpointSnapshot => _snapshot;
        public double MinSecondsBetweenWrites { get; set; }
        /// <summary>A save is waiting for the rate limit.</summary>
        public bool Pending { get; private set; }
        public int Writes { get; private set; }
        /// <summary>The last load restored the snapshot (false: derived from the checkpoint alone).</summary>
        public bool RestoredSnapshot { get; private set; }
        /// <summary>
        /// The service holds a game (<see cref="NewGame"/>, <see cref="Load"/>/<see cref="TryContinue"/> or a
        /// <see cref="Reach"/>), so a write saves the whole slot. Before that, a write saves only <see cref="Settings"/>
        /// into what the slot already holds.
        /// </summary>
        public bool Started { get; private set; }
        /// <summary>
        /// The world was rebuilt at <see cref="Current"/> (respawn, reload, continue or a new game). Systems outside the
        /// graph that hold time or control (directed moments, the camera, hints) reset themselves here.
        /// </summary>
        public event Action<Checkpoint> Reloaded;

        /// <summary>The order index of <paramref name="name"/>; throws for an unknown name.</summary>
        public int IndexOf(string name)
        {
            for (int i = 0; i < _order.Count; i++) if (string.Equals(_order[i], name, StringComparison.Ordinal)) return i;
            throw new ArgumentException("Unknown checkpoint '" + name + "'.", nameof(name));
        }

        /// <summary>Joins a persist flag to state held elsewhere (e.g. <c>WhiteBrain.Warned</c> ↔ <see cref="StoryFlags.WhiteWarned"/>).</summary>
        public void BindFlag(string name, Func<bool> get, Action<bool> set)
        {
            _bindings.Add((name ?? throw new ArgumentNullException(nameof(name)), get ?? throw new ArgumentNullException(nameof(get)),
                set ?? throw new ArgumentNullException(nameof(set))));
            Flags.Resolve(name);
        }

        /// <summary>
        /// Adopt the options saved in the slot without loading the world (boot, the title screen). Called by the
        /// constructor. False when the slot is empty or unreadable (the options stay as they are: defaults at boot), or
        /// when options applied here are still waiting to be written (they are newer than the slot's).
        /// </summary>
        public bool TryLoadSettings()
        {
            if (Pending) return false;
            if (!_store.TryLoad(Slot, out var m) || m == null) return false;
            Settings = (m.Settings ?? new Settings()).Clone();
            _graph.Calm = Settings.Calm;
            return true;
        }

        /// <summary>
        /// Start over (<c>clearLetters</c>, L4133): no flags, the first checkpoint, the world rebuilt; saved. The
        /// player's options (<see cref="Settings"/>) are kept.
        /// </summary>
        public void NewGame()
        {
            Started = true;
            Flags.Clear();
            PushBindings();
            Current = new Checkpoint(_order, _order[0]);
            PlayTime = 0;
            _snapshot = null;
            _graph.Reset(Current);
            _snapshot = Capture();
            Save();
            Reloaded?.Invoke(Current);
        }

        /// <summary>
        /// A checkpoint trigger fired. Later than the current one: it becomes current, the graph is captured as it is
        /// now (call after the step that reached it) and the slot is saved. Returns whether it advanced.
        /// </summary>
        public bool Reach(string name)
        {
            if (IndexOf(name) <= IndexOf(Current.Name)) return false;
            Started = true;
            Current = new Checkpoint(_order, name);
            PullBindings();
            _snapshot = Capture();
            Save();
            return true;
        }

        /// <summary>Set (or clear) a story flag and save it, keeping the checkpoint and its snapshot.</summary>
        public void SetFlag(string name, bool value = true)
        {
            Flags.Set(name, value);
            SaveIfFlagsChanged();
        }

        /// <summary>Saves when a flag (or a bound flag) has changed since the last write.</summary>
        public void SaveIfFlagsChanged()
        {
            PullBindings();
            if (Flags.Version != _savedFlags) Save();
        }

        /// <summary>
        /// Changed options: saved with the slot. Before <see cref="Started"/> (the title screen) only the options are
        /// written into the slot; its progress is kept.
        /// </summary>
        public void ApplySettings(Settings settings)
        {
            Settings = (settings ?? throw new ArgumentNullException(nameof(settings))).Clone();
            _graph.Calm = Settings.Calm;
            Save();
        }

        /// <summary>
        /// Respawn or reload at the current checkpoint: the world derived from the checkpoint and the flags, then the
        /// checkpoint's snapshot on top. Flags set since the checkpoint survive. The graph's tick carries on.
        /// </summary>
        public void Reload()
        {
            PullBindings();
            _graph.Reset(Current);
            RestoredSnapshot = false;
            if (_snapshot != null)
            {
                var derived = Capture();                      // the world _graph.Reset(Current) just derived, exactly
                try
                {
                    _graph.Restore(new KeepTick(_snapshot, _graph.Tick));
                    RestoredSnapshot = true;
                }
                catch (Exception e) when (!SaveCodec.IsFatal(e))
                {
                    // The scene changed since the save (a renamed mechanism, a smaller pool, fewer crate types) or the
                    // snapshot is otherwise stale. Never leave the graph half-restored: put back the derived world,
                    // including the fields Reset carries on (clocks, sequences) that a partial restore may have
                    // overwritten, and drop the snapshot so a later respawn does not try it again.
                    _snapshot = null;
                    RestoredSnapshot = false;
                    _graph.Restore(derived);
                }
            }
            PushBindings();                                   // a snapshot holds old copies of bound flags
            if (Flags.Version != _savedFlags) Save();         // e.g. warned on the run that ended in this respawn
            Reloaded?.Invoke(Current);
        }

        /// <summary>
        /// Continue from the slot: checkpoint, flags, play time and options from the store, then <see cref="Reload"/>.
        /// A snapshot from another scene, or an unknown checkpoint, is dropped. False when the slot is empty or unreadable.
        /// </summary>
        public bool TryContinue()
        {
            if (!_store.TryLoad(Slot, out var m) || m.OptionsOnly) return false;
            Load(m);
            return true;
        }

        /// <summary>
        /// Applies a loaded model and reloads (see <see cref="TryContinue"/>). Options applied before the service
        /// started that are still waiting for the rate limit are newer than the model's, so they are kept (and stay
        /// pending).
        /// </summary>
        public void Load(SaveModel m)
        {
            if (m == null) throw new ArgumentNullException(nameof(m));
            bool keepOptions = !Started && Pending;
            Started = true;
            int idx = -1;
            for (int i = 0; i < _order.Count; i++) if (string.Equals(_order[i], m.Checkpoint, StringComparison.Ordinal)) idx = i;
            Current = new Checkpoint(_order, idx >= 0 ? m.Checkpoint : _order[0]);
            Flags.Load(m.Flags);
            PushBindings();
            PlayTime = m.PlayTime;
            if (!keepOptions) Settings = (m.Settings ?? new Settings()).Clone();
            _graph.Calm = Settings.Calm;
            _snapshot = idx >= 0 && string.Equals(m.Scene ?? "", Scene, StringComparison.Ordinal) ? m.Mechanisms : null;
            _savedFlags = Flags.Version;
            Pending = keepOptions;                            // else what is in the store is what was just loaded
            Reload();                                         // after: a save from a Reloaded handler must stay pending
        }

        /// <summary>The slot as it would be written now.</summary>
        public SaveModel ToModel()
        {
            PullBindings();
            return new SaveModel
            {
                Checkpoint = Current.Name,
                Scene = Scene,
                PlayTime = PlayTime,
                Flags = Flags.SetNames(),
                Mechanisms = _snapshot,
                Settings = Settings.Clone(),
            };
        }

        /// <summary>Per frame: <paramref name="dt"/> real seconds; play time counts only while <paramref name="playing"/>.</summary>
        public void Update(double dt, bool playing)
        {
            if (playing) PlayTime += dt;
            _sinceWrite += dt;
            PullBindings();
            if (Flags.Version != _savedFlags) Pending = true;
            if (Pending && _sinceWrite >= MinSecondsBetweenWrites) Write();
        }

        /// <summary>Write a held save now (quit, suspend).</summary>
        public void Flush()
        {
            if (Pending) Write();
        }

        private void Save()
        {
            Pending = true;
            if (_sinceWrite >= MinSecondsBetweenWrites) Write();
        }

        private void Write()
        {
            var m = Started ? ToModel() : OptionsIntoSlot();
            _store.Save(Slot, m);
            _savedFlags = Flags.Version;
            Pending = false;
            _sinceWrite = 0;
            Writes++;
        }

        /// <summary>Not started: the slot as stored with only its options replaced (a fresh model when it is empty).</summary>
        private SaveModel OptionsIntoSlot()
        {
            if (!_store.TryLoad(Slot, out var stored) || stored == null)
            {
                var fresh = ToModel();
                fresh.OptionsOnly = true;
                return fresh;
            }
            stored.Settings = Settings.Clone();
            return stored;
        }

        private MemorySnapshot Capture()
        {
            var s = new MemorySnapshot();
            _graph.Snapshot(s);
            return s;
        }

        private void PullBindings()
        {
            foreach (var b in _bindings) Flags.Set(b.name, b.get());
        }

        private void PushBindings()
        {
            foreach (var b in _bindings) b.set(Flags.Has(b.name));
        }

        /// <summary>Reads a snapshot but keeps the graph's own tick (ticks only ever count up).</summary>
        private sealed class KeepTick : ISnapshotReader
        {
            private readonly ISnapshotReader _r;
            private readonly long _tick;
            public KeepTick(ISnapshotReader r, long tick) { _r = r; _tick = tick; }
            public double ReadDouble(string key) => _r.ReadDouble(key);
            public long ReadLong(string key) => key == "graph/tick" ? _tick : _r.ReadLong(key);
            public bool ReadBool(string key) => _r.ReadBool(key);
        }
    }
}
