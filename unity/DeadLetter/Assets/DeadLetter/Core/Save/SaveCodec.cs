using System;
using System.Collections.Generic;
using System.Text;

namespace DeadLetter.Core.Save
{
    /// <summary>
    /// The save file's bytes, written and read by hand (no reflection: IL2CPP/AOT-safe). Little-endian:
    /// <code>
    /// "DLSV" | u16 version | u32 count | count × (u16 keyLen, key UTF-8, u8 kind, value) | u32 CRC-32
    /// value: Long/Double = 8 bytes (double as its bits), Bool = 1 byte, String = u32 byteLen + UTF-8
    /// </code>
    /// Entries are in ordinal key order, so a model always encodes to the same bytes. The CRC-32 (IEEE 802.3) covers
    /// every byte before it. Older versions are migrated on load (<see cref="SaveMigrations"/>).
    /// </summary>
    public static class SaveCodec
    {
        public static readonly byte[] Magic = { (byte)'D', (byte)'L', (byte)'S', (byte)'V' };
        private const int HeaderSize = 4 + 2 + 4, CrcSize = 4;

        public static byte[] Encode(SaveModel model) => Encode(model.ToDocument());

        public static byte[] Encode(SaveDocument d)
        {
            if (d.Version < 0 || d.Version > ushort.MaxValue) throw new ArgumentOutOfRangeException(nameof(d), "Bad version.");
            var b = new List<byte>(256);
            b.AddRange(Magic);
            PutU16(b, d.Version);
            PutU32(b, (uint)d.Count);
            foreach (var kv in d.Entries)
            {
                var key = Encoding.UTF8.GetBytes(kv.Key);
                if (key.Length > ushort.MaxValue) throw new ArgumentException("Key too long: " + kv.Key);
                PutU16(b, key.Length);
                b.AddRange(key);
                b.Add((byte)kv.Value.Kind);
                switch (kv.Value.Kind)
                {
                    case SaveValueKind.Bool: b.Add((byte)(kv.Value.Bits != 0 ? 1 : 0)); break;
                    case SaveValueKind.String:
                        var s = Encoding.UTF8.GetBytes(kv.Value.Text);
                        PutU32(b, (uint)s.Length);
                        b.AddRange(s);
                        break;
                    default: PutU64(b, (ulong)kv.Value.Bits); break;
                }
            }
            var bytes = new byte[b.Count + CrcSize];
            b.CopyTo(bytes);
            uint crc = Crc32.Compute(bytes, 0, b.Count);
            WriteU32(bytes, b.Count, crc);
            return bytes;
        }

        /// <summary>Checks the magic and the checksum, then reads the document at its own version (no migration).</summary>
        public static bool TryDecode(byte[] bytes, out SaveDocument doc, out string error)
        {
            doc = null;
            if (bytes == null || bytes.Length < HeaderSize + CrcSize) { error = "too short"; return false; }
            for (int i = 0; i < 4; i++) if (bytes[i] != Magic[i]) { error = "not a save file"; return false; }
            int end = bytes.Length - CrcSize;
            if (Crc32.Compute(bytes, 0, end) != ReadU32(bytes, end)) { error = "bad checksum"; return false; }
            try
            {
                int p = 4;
                var d = new SaveDocument(ReadU16(bytes, ref p, end));
                uint count = ReadU32(bytes, ref p, end);
                for (uint n = 0; n < count; n++)
                {
                    int keyLen = ReadU16(bytes, ref p, end);
                    Need(p, keyLen, end);
                    string key = Encoding.UTF8.GetString(bytes, p, keyLen);
                    p += keyLen;
                    Need(p, 1, end);
                    var kind = (SaveValueKind)bytes[p++];
                    switch (kind)
                    {
                        case SaveValueKind.Bool: Need(p, 1, end); d.SetBool(key, bytes[p++] != 0); break;
                        case SaveValueKind.String:
                            int len = checked((int)ReadU32(bytes, ref p, end));
                            Need(p, len, end);
                            d.SetString(key, Encoding.UTF8.GetString(bytes, p, len));
                            p += len;
                            break;
                        case SaveValueKind.Long:
                        case SaveValueKind.Double:
                            Need(p, 8, end);
                            d.Set(key, new SaveValue(kind, (long)ReadU64(bytes, p), null));
                            p += 8;
                            break;
                        default: throw new FormatException("Unknown value kind " + (int)kind + " at '" + key + "'.");
                    }
                }
                if (p != end) throw new FormatException("Trailing bytes.");
                doc = d;
                error = null;
                return true;
            }
            catch (Exception e) when (e is FormatException || e is OverflowException || e is ArgumentException)
            {
                error = e.Message;
                return false;
            }
        }

        /// <summary>Decode, migrate to <see cref="SaveModel.CurrentVersion"/>, map. False on any damage or a newer version.</summary>
        public static bool TryLoad(byte[] bytes, out SaveModel model, out string error)
        {
            model = null;
            if (!TryDecode(bytes, out var doc, out error)) return false;
            if (!SaveMigrations.TryMigrate(doc, out error)) return false;
            try { model = SaveModel.FromDocument(doc); return true; }
            catch (FormatException e) { error = e.Message; return false; }
        }

        private static void Need(int p, int n, int end)
        {
            if (n < 0 || p + n > end) throw new FormatException("Truncated.");
        }

        private static void PutU16(List<byte> b, int v) { b.Add((byte)v); b.Add((byte)(v >> 8)); }
        private static void PutU32(List<byte> b, uint v) { for (int i = 0; i < 4; i++) b.Add((byte)(v >> (8 * i))); }
        private static void PutU64(List<byte> b, ulong v) { for (int i = 0; i < 8; i++) b.Add((byte)(v >> (8 * i))); }
        private static void WriteU32(byte[] b, int p, uint v) { for (int i = 0; i < 4; i++) b[p + i] = (byte)(v >> (8 * i)); }

        private static int ReadU16(byte[] b, ref int p, int end) { Need(p, 2, end); int v = b[p] | (b[p + 1] << 8); p += 2; return v; }
        private static uint ReadU32(byte[] b, ref int p, int end) { Need(p, 4, end); uint v = ReadU32(b, p); p += 4; return v; }
        private static uint ReadU32(byte[] b, int p) => (uint)(b[p] | (b[p + 1] << 8) | (b[p + 2] << 16) | (b[p + 3] << 24));
        private static ulong ReadU64(byte[] b, int p) => ReadU32(b, p) | ((ulong)ReadU32(b, p + 4) << 32);
    }

    /// <summary>CRC-32, IEEE 802.3 (reflected polynomial 0xEDB88320), as zlib's <c>crc32</c>.</summary>
    public static class Crc32
    {
        private static readonly uint[] Table = Build();

        public static uint Compute(byte[] data, int offset, int count)
        {
            uint c = 0xFFFFFFFFu;
            for (int i = offset; i < offset + count; i++) c = Table[(c ^ data[i]) & 0xFF] ^ (c >> 8);
            return c ^ 0xFFFFFFFFu;
        }

        private static uint[] Build()
        {
            var t = new uint[256];
            for (uint n = 0; n < 256; n++)
            {
                uint c = n;
                for (int k = 0; k < 8; k++) c = (c & 1) != 0 ? 0xEDB88320u ^ (c >> 1) : c >> 1;
                t[n] = c;
            }
            return t;
        }
    }
}
