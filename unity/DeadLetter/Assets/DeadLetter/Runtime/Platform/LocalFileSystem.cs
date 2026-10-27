using System.IO;
using DeadLetter.Core.Save;
using UnityEngine;

namespace DeadLetter.Runtime.Platform
{
    /// <summary>
    /// <see cref="IFileSystem"/> over System.IO under <c>Application.persistentDataPath/saves</c> (PC, itch, and Steam
    /// without Steam Cloud). Writes are flushed to disk before returning; Replace is a rename. All logic (temp file,
    /// backup, checksum) is Core's <see cref="AtomicFileStore"/>.
    /// </summary>
    public sealed class LocalFileSystem : IFileSystem
    {
        private readonly string _root;

        public LocalFileSystem(string root = null)
        {
            _root = root ?? Path.Combine(Application.persistentDataPath, "saves");
            Directory.CreateDirectory(_root);
        }

        public bool Exists(string path) => File.Exists(Full(path));

        public byte[] ReadAll(string path)
        {
            string p = Full(path);
            return File.Exists(p) ? File.ReadAllBytes(p) : null;
        }

        public void WriteAll(string path, byte[] data)
        {
            using (var fs = new FileStream(Full(path), FileMode.Create, FileAccess.Write, FileShare.None))
            {
                fs.Write(data, 0, data.Length);
                fs.Flush(true);                                   // fsync
            }
        }

        public void Replace(string from, string to)
        {
            string src = Full(from), dst = Full(to);
            if (File.Exists(dst)) File.Replace(src, dst, null);   // atomic swap (ReplaceFile / rename)
            else File.Move(src, dst);
        }

        public void Delete(string path) => File.Delete(Full(path));

        private string Full(string path) => Path.Combine(_root, path);
    }
}
