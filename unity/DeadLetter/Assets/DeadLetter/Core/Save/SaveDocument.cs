using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Save
{
    public enum SaveValueKind : byte { Long = 1, Double = 2, Bool = 3, String = 4 }

    /// <summary>One typed value of a <see cref="SaveDocument"/>. Doubles are kept as their bits.</summary>
    public readonly struct SaveValue
    {
        public readonly SaveValueKind Kind;
        public readonly long Bits;
        public readonly string Text;

        public SaveValue(SaveValueKind kind, long bits, string text) { Kind = kind; Bits = bits; Text = text; }

        public override string ToString() => Kind switch
        {
            SaveValueKind.Double => BitConverter.Int64BitsToDouble(Bits).ToString("R", System.Globalization.CultureInfo.InvariantCulture),
            SaveValueKind.Bool => Bits != 0 ? "true" : "false",
            SaveValueKind.String => "\"" + Text + "\"",
            _ => Bits.ToString(System.Globalization.CultureInfo.InvariantCulture),
        };
    }

    /// <summary>
    /// The save file's content: a flat map of typed values by key, iterated in ordinal key order (so the bytes are
    /// deterministic). Migrations edit it by key (rename, drop, default) before it becomes a <see cref="SaveModel"/>;
    /// it never goes through reflection.
    /// </summary>
    public sealed class SaveDocument
    {
        private readonly SortedDictionary<string, SaveValue> _values = new SortedDictionary<string, SaveValue>(StringComparer.Ordinal);

        public int Version;

        public SaveDocument(int version) { Version = version; }

        public int Count => _values.Count;
        public IEnumerable<KeyValuePair<string, SaveValue>> Entries => _values;
        public bool Contains(string key) => _values.ContainsKey(key);
        public bool Remove(string key) => _values.Remove(key);
        public bool TryGet(string key, out SaveValue v) => _values.TryGetValue(key, out v);

        public void Set(string key, SaveValue v)
        {
            if (string.IsNullOrEmpty(key)) throw new ArgumentException("Save keys must be non-empty.", nameof(key));
            if (v.Kind == SaveValueKind.String && v.Text == null) throw new ArgumentNullException(nameof(v));
            _values[key] = v;
        }

        public void SetLong(string key, long v) => Set(key, new SaveValue(SaveValueKind.Long, v, null));
        public void SetDouble(string key, double v) => Set(key, new SaveValue(SaveValueKind.Double, BitConverter.DoubleToInt64Bits(v), null));
        public void SetBool(string key, bool v) => Set(key, new SaveValue(SaveValueKind.Bool, v ? 1 : 0, null));
        public void SetString(string key, string v) => Set(key, new SaveValue(SaveValueKind.String, 0, v ?? throw new ArgumentNullException(nameof(v))));

        public long GetLong(string key, long fallback) => TryKind(key, SaveValueKind.Long, out var v) ? v.Bits : fallback;
        public double GetDouble(string key, double fallback) => TryKind(key, SaveValueKind.Double, out var v) ? BitConverter.Int64BitsToDouble(v.Bits) : fallback;
        public bool GetBool(string key, bool fallback) => TryKind(key, SaveValueKind.Bool, out var v) ? v.Bits != 0 : fallback;
        public string GetString(string key, string fallback) => TryKind(key, SaveValueKind.String, out var v) ? v.Text : fallback;

        /// <summary>The keys under <paramref name="prefix"/>, with the prefix cut off, in order.</summary>
        public List<string> KeysUnder(string prefix)
        {
            var list = new List<string>();
            foreach (var k in _values.Keys) if (k.StartsWith(prefix, StringComparison.Ordinal)) list.Add(k.Substring(prefix.Length));
            return list;
        }

        /// <summary>Moves every key under <paramref name="from"/> to <paramref name="to"/> (for migrations).</summary>
        public void RenamePrefix(string from, string to)
        {
            foreach (var rest in KeysUnder(from))
            {
                var v = _values[from + rest];
                _values.Remove(from + rest);
                _values[to + rest] = v;
            }
        }

        private bool TryKind(string key, SaveValueKind kind, out SaveValue v) => _values.TryGetValue(key, out v) && v.Kind == kind;
    }
}
