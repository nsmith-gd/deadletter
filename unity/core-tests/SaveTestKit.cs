using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Save;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// An in-memory <see cref="IFileSystem"/> with fault injection: a torn write (only the first n bytes land, then the
    /// "power goes"), and a crash before the k-th Replace.
    /// </summary>
    internal sealed class MemoryFileSystem : IFileSystem
    {
        public readonly Dictionary<string, byte[]> Files = new Dictionary<string, byte[]>();
        /// <summary>&gt;= 0: the next WriteAll stores only this many bytes, then throws.</summary>
        public int TearNextWriteAt = -1;
        /// <summary>&gt;= 0: Replace calls left before one throws (0: the next one throws, before moving anything).</summary>
        public int CrashAtReplace = -1;

        public bool Exists(string path) => Files.ContainsKey(path);
        public byte[] ReadAll(string path) => Files.TryGetValue(path, out var b) ? (byte[])b.Clone() : null;

        public void WriteAll(string path, byte[] data)
        {
            if (TearNextWriteAt >= 0)
            {
                Files[path] = data.Take(TearNextWriteAt).ToArray();
                TearNextWriteAt = -1;
                throw new IOException("torn write");
            }
            Files[path] = (byte[])data.Clone();
        }

        public void Replace(string from, string to)
        {
            if (CrashAtReplace == 0) { CrashAtReplace = -1; throw new IOException("crash"); }
            if (CrashAtReplace > 0) CrashAtReplace--;
            if (!Files.TryGetValue(from, out var b)) throw new FileNotFoundException(from);
            Files.Remove(from);
            Files[to] = b;
        }

        public void Delete(string path) => Files.Remove(path);
    }

    internal static class SaveKit
    {
        /// <summary><see cref="Mech.Dump"/> without <c>graph/tick</c> (the tick carries on across a reload).</summary>
        public static string Dump(MechanismGraph g) => NoTick(Mech.Dump(g));
        public static string Dump(MemorySnapshot s) => NoTick(s.Dump());

        private static string NoTick(string dump)
            => string.Concat(dump.Split('\n').Where(l => l.Length > 0 && !l.StartsWith("graph/tick=", StringComparison.Ordinal)).Select(l => l + "\n"));

        /// <summary>A service over an atomic store on <paramref name="fs"/>, for the prototype's checkpoint order.</summary>
        public static CheckpointService Service(MechanismGraph g, MemoryFileSystem fs, string scene)
            => new CheckpointService(g, Checkpoint.PrototypeOrder, new AtomicFileStore(fs), 0, scene);

        /// <summary>
        /// Quit and continue: a fresh scene (<paramref name="fresh"/>, any state) continues from what <paramref name="fs"/>
        /// holds; its mechanisms must equal <paramref name="expected"/> (a dump taken when the checkpoint was reached).
        /// Returns the fresh service.
        /// </summary>
        public static CheckpointService Continue(MechanismGraph fresh, MemoryFileSystem fs, string scene, string checkpoint, string expected,
            Action<CheckpointService> bind = null)
        {
            var svc = Service(fresh, fs, scene);
            bind?.Invoke(svc);
            Assert.True(svc.TryContinue());
            Assert.Equal(checkpoint, svc.Current.Name);
            Assert.True(svc.RestoredSnapshot);
            Assert.Equal(expected, Dump(fresh));
            return svc;
        }
    }
}
