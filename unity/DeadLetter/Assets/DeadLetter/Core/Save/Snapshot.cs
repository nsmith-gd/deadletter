using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace DeadLetter.Core.Save
{
    /// <summary>
    /// Writes primitive fields by key. Mechanisms, and later every Core system, snapshot themselves through this
    /// (port_architecture §4.13l, §4.28). Keys are stable strings: they end up in replays and rewind buffers.
    /// U-14 builds its save model on top; keep this interface this small.
    /// </summary>
    public interface ISnapshotWriter
    {
        void WriteDouble(string key, double value);
        void WriteLong(string key, long value);
        void WriteBool(string key, bool value);
    }

    /// <summary>Reads what an <see cref="ISnapshotWriter"/> wrote. A missing key or a type mismatch throws.</summary>
    public interface ISnapshotReader
    {
        double ReadDouble(string key);
        long ReadLong(string key);
        bool ReadBool(string key);
    }

    /// <summary>
    /// In-memory snapshot: exact round trips (doubles are kept as their bits). For tests, replays and rewind; not a
    /// save format. <see cref="Dump"/> gives a sorted, bit-exact text form for comparisons.
    /// </summary>
    public sealed class MemorySnapshot : ISnapshotWriter, ISnapshotReader
    {
        private enum Kind : byte { Double, Long, Bool }

        private readonly Dictionary<string, (Kind kind, long bits)> _fields = new Dictionary<string, (Kind, long)>();

        public int Count => _fields.Count;
        public IEnumerable<string> Keys => _fields.Keys;
        public bool Contains(string key) => _fields.ContainsKey(key);
        public void Clear() => _fields.Clear();

        public void WriteDouble(string key, double value) => Put(key, Kind.Double, BitConverter.DoubleToInt64Bits(value));
        public void WriteLong(string key, long value) => Put(key, Kind.Long, value);
        public void WriteBool(string key, bool value) => Put(key, Kind.Bool, value ? 1 : 0);

        public double ReadDouble(string key) => BitConverter.Int64BitsToDouble(Get(key, Kind.Double));
        public long ReadLong(string key) => Get(key, Kind.Long);
        public bool ReadBool(string key) => Get(key, Kind.Bool) != 0;

        /// <summary>Writes every field to <paramref name="w"/> with its own type, in ordinal key order (deterministic).</summary>
        public void CopyTo(ISnapshotWriter w)
        {
            var keys = new List<string>(_fields.Keys);
            keys.Sort(StringComparer.Ordinal);
            foreach (var k in keys)
            {
                var f = _fields[k];
                switch (f.kind)
                {
                    case Kind.Double: w.WriteDouble(k, BitConverter.Int64BitsToDouble(f.bits)); break;
                    case Kind.Long: w.WriteLong(k, f.bits); break;
                    default: w.WriteBool(k, f.bits != 0); break;
                }
            }
        }

        /// <summary>Every field as <c>key=value</c> lines, sorted by key; doubles printed round-trip exact.</summary>
        public string Dump()
        {
            var keys = new List<string>(_fields.Keys);
            keys.Sort(StringComparer.Ordinal);
            var sb = new StringBuilder();
            foreach (var k in keys)
            {
                var f = _fields[k];
                sb.Append(k).Append('=');
                switch (f.kind)
                {
                    case Kind.Double: sb.Append(BitConverter.Int64BitsToDouble(f.bits).ToString("R", CultureInfo.InvariantCulture)); break;
                    case Kind.Long: sb.Append(f.bits.ToString(CultureInfo.InvariantCulture)); break;
                    default: sb.Append(f.bits != 0 ? "true" : "false"); break;
                }
                sb.Append('\n');
            }
            return sb.ToString();
        }

        private void Put(string key, Kind kind, long bits)
        {
            if (string.IsNullOrEmpty(key)) throw new ArgumentException("Snapshot keys must be non-empty.", nameof(key));
            _fields[key] = (kind, bits);
        }

        private long Get(string key, Kind kind)
        {
            if (!_fields.TryGetValue(key, out var f)) throw new KeyNotFoundException("Snapshot has no field '" + key + "'.");
            if (f.kind != kind) throw new InvalidOperationException("Snapshot field '" + key + "' is a " + f.kind + ", not a " + kind + ".");
            return f.bits;
        }
    }
}
