using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Save
{
    /// <summary>Where save slots live (§4.28). Platform stores implement <see cref="IFileSystem"/> under <see cref="AtomicFileStore"/>.</summary>
    public interface ISaveStore
    {
        /// <summary>False when the slot is empty or every copy of it is damaged or from a newer build.</summary>
        bool TryLoad(int slot, out SaveModel model);
        void Save(int slot, SaveModel model);
        void Delete(int slot);
    }

    /// <summary>
    /// The few file operations a save needs, by relative path. <see cref="WriteAll"/> must not return until the bytes
    /// are durable (fsync, or the platform's commit). <see cref="Replace"/> must be atomic: afterwards the destination
    /// is wholly the old file or wholly the new one.
    /// </summary>
    public interface IFileSystem
    {
        bool Exists(string path);
        /// <summary>Null when missing.</summary>
        byte[] ReadAll(string path);
        void WriteAll(string path, byte[] data);
        /// <summary>Atomically moves <paramref name="from"/> over <paramref name="to"/> (replacing it if present).</summary>
        void Replace(string from, string to);
        void Delete(string path);
    }

    /// <summary>
    /// Crash-safe slots over an <see cref="IFileSystem"/>: <c>slotN.dls</c> plus one backup <c>slotN.dls.bak</c>.
    /// Save: write <c>.tmp</c> (durable), move the current file (if it reads back valid) over <c>.bak</c>, move
    /// <c>.tmp</c> over the current. A crash at any point leaves a valid current file or a valid backup. Load: the
    /// current file, else the backup (bad checksum, torn or missing).
    /// </summary>
    public sealed class AtomicFileStore : ISaveStore
    {
        private readonly IFileSystem _fs;
        private readonly string _prefix;

        public AtomicFileStore(IFileSystem fs, string prefix = "slot")
        {
            _fs = fs ?? throw new ArgumentNullException(nameof(fs));
            _prefix = prefix;
        }

        /// <summary>Why the last <see cref="TryLoad"/> fell back or failed (null when the current file was good).</summary>
        public string LastError { get; private set; }
        /// <summary>True when the last successful load came from the backup.</summary>
        public bool LoadedBackup { get; private set; }

        public string PathOf(int slot) => _prefix + slot + ".dls";
        public string BackupOf(int slot) => PathOf(slot) + ".bak";
        public string TempOf(int slot) => PathOf(slot) + ".tmp";

        public bool TryLoad(int slot, out SaveModel model)
        {
            LoadedBackup = false;
            LastError = null;
            if (TryRead(PathOf(slot), out model, out string err)) return true;
            LastError = err;
            if (TryRead(BackupOf(slot), out model, out string bakErr)) { LoadedBackup = true; return true; }
            LastError = err + "; backup: " + bakErr;
            return false;
        }

        public void Save(int slot, SaveModel model)
        {
            var bytes = SaveCodec.Encode(model);
            string path = PathOf(slot), tmp = TempOf(slot), bak = BackupOf(slot);
            _fs.WriteAll(tmp, bytes);
            if (_fs.Exists(path))
            {
                if (TryRead(path, out _, out _)) _fs.Replace(path, bak);   // keep the last good one
                else _fs.Delete(path);                                     // never back up a damaged file over a good backup
            }
            _fs.Replace(tmp, path);
        }

        public void Delete(int slot)
        {
            foreach (var p in new[] { PathOf(slot), BackupOf(slot), TempOf(slot) }) if (_fs.Exists(p)) _fs.Delete(p);
        }

        private bool TryRead(string path, out SaveModel model, out string error)
        {
            model = null;
            byte[] bytes;
            try { bytes = _fs.ReadAll(path); }
            catch (Exception e) { error = path + ": " + e.Message; return false; }
            if (bytes == null) { error = path + ": missing"; return false; }
            if (!SaveCodec.TryLoad(bytes, out model, out error)) { error = path + ": " + error; return false; }
            return true;
        }
    }

    /// <summary>A store in memory (tests, and a fallback when the platform has no storage). Keeps encoded bytes, so it round-trips the format.</summary>
    public sealed class MemorySaveStore : ISaveStore
    {
        public readonly Dictionary<int, byte[]> Slots = new Dictionary<int, byte[]>();
        public int Writes { get; private set; }

        public bool TryLoad(int slot, out SaveModel model)
        {
            model = null;
            return Slots.TryGetValue(slot, out var b) && SaveCodec.TryLoad(b, out model, out _);
        }

        public void Save(int slot, SaveModel model) { Slots[slot] = SaveCodec.Encode(model); Writes++; }
        public void Delete(int slot) => Slots.Remove(slot);
    }
}
