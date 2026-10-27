using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Save
{
    /// <summary>
    /// What a mechanism may read of the persist flags (§4.28). Resolve a name once, in <c>Link</c>, then read the handle
    /// each step: no string lookup per tick. Names are registered on first resolve, so a flag nobody has set reads false.
    /// </summary>
    public interface IPersistFlagReader
    {
        int Resolve(string name);
        bool Get(int handle);
    }

    /// <summary>
    /// The named story flags that outlive a respawn and a checkpoint reload and are cleared by Start over (L4133,
    /// L7307): letters read, curiosities, secret rooms, voice cards, and the prototype's <c>persist</c> object. The save
    /// holds the names of the flags that are set (sorted, ordinal). The seen moments use a second instance of this class
    /// (<see cref="CheckpointService.Seen"/>), saved under their own keys since version 3.
    /// </summary>
    public sealed class PersistFlags : IPersistFlagReader
    {
        private readonly Dictionary<string, int> _index = new Dictionary<string, int>(StringComparer.Ordinal);
        private readonly List<string> _names = new List<string>();
        private readonly List<bool> _values = new List<bool>();

        /// <summary>Bumped on every change that sets or clears a flag (the service saves when it moves).</summary>
        public long Version { get; private set; }

        public int Resolve(string name)
        {
            if (string.IsNullOrEmpty(name)) throw new ArgumentException("Flag names must be non-empty.", nameof(name));
            if (_index.TryGetValue(name, out int i)) return i;
            _index.Add(name, _names.Count);
            _names.Add(name);
            _values.Add(false);
            return _names.Count - 1;
        }

        public bool Get(int handle) => _values[handle];
        public bool Has(string name) => _index.TryGetValue(name, out int i) && _values[i];

        public void Set(string name, bool value = true)
        {
            int i = Resolve(name);
            if (_values[i] == value) return;
            _values[i] = value;
            Version++;
        }

        /// <summary>Start over: every flag false (handles stay valid).</summary>
        public void Clear()
        {
            bool any = false;
            for (int i = 0; i < _values.Count; i++) { any |= _values[i]; _values[i] = false; }
            if (any) Version++;
        }

        /// <summary>The names of the set flags, sorted ordinal.</summary>
        public List<string> SetNames()
        {
            var list = new List<string>();
            for (int i = 0; i < _names.Count; i++) if (_values[i]) list.Add(_names[i]);
            list.Sort(StringComparer.Ordinal);
            return list;
        }

        /// <summary>Replace the set with exactly <paramref name="names"/>.</summary>
        public void Load(IEnumerable<string> names)
        {
            Clear();
            foreach (var n in names) Set(n);
        }
    }

    /// <summary>Flag names (stable strings: they are in save files). Collections take an ID suffix.</summary>
    public static class StoryFlags
    {
        /// <summary><c>persist.warned</c> (L7150): the White has warned him once; it strikes from now on (<c>WhiteBrain.Warned</c>).</summary>
        public const string WhiteWarned = "persist.warned";
        /// <summary><c>persist.shockedOnce</c> (L7411): the first arc shock knocks him back; later ones do not.</summary>
        public const string ShockedOnce = "persist.shockedOnce";
        /// <summary><c>persist.cageDanger</c> (L5037, L5048): the cage slipped and has not yet been caught (the failure music, L8157).</summary>
        public const string CageDanger = "persist.cageDanger";
        /// <summary><c>persist.cw = 2</c> (L4436): every counterweight plate is on the tray.</summary>
        public const string CounterweightsStowed = "persist.cw";
        /// <summary>DL-17: Lisle's drawing has been read (<c>f17.read</c>, L5702–L5703). The stair door waits for it (L5776, L5789).</summary>
        public const string Dl17DrawerRead = "dl17.drawerRead";

        public static string LetterRead(string id) => "letter.read." + id;
        public static string LetterPosted(string id) => "letter.posted." + id;
        public static string Curio(string id) => "curio." + id;
        public static string Secret(string id) => "secret." + id;
        public static string Voice(string id) => "voice." + id;
    }
}
