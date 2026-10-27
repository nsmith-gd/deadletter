#if STEAMWORKS_NET
using DeadLetter.Core.Save;
using Steamworks;

namespace DeadLetter.Runtime.Platform
{
    /// <summary>
    /// <see cref="IFileSystem"/> over Steam Cloud (<c>ISteamRemoteStorage</c>, Steamworks.NET). Compiled only with
    /// <c>STEAMWORKS_NET</c> (U-17 adds the package and the define). Steam has no rename: <see cref="Replace"/> is a
    /// read, a write of the destination (Steam's FileWrite replaces a file whole) and a delete, so the destination is
    /// never torn; Core's <see cref="AtomicFileStore"/> keeps the backup and checks the checksum.
    /// </summary>
    public sealed class SteamRemoteStorageFileSystem : IFileSystem
    {
        public bool Exists(string path) => SteamRemoteStorage.FileExists(path);

        public byte[] ReadAll(string path)
        {
            if (!SteamRemoteStorage.FileExists(path)) return null;
            int size = SteamRemoteStorage.GetFileSize(path);
            var data = new byte[size];
            int read = SteamRemoteStorage.FileRead(path, data, size);
            if (read == size) return data;
            var part = new byte[read < 0 ? 0 : read];                 // a short read: the checksum rejects it
            System.Array.Copy(data, part, part.Length);
            return part;
        }

        public void WriteAll(string path, byte[] data)
        {
            if (!SteamRemoteStorage.FileWrite(path, data, data.Length))
                throw new System.IO.IOException("Steam Cloud refused to write " + path + " (quota or disabled).");
        }

        public void Replace(string from, string to)
        {
            var data = ReadAll(from) ?? throw new System.IO.FileNotFoundException(from);
            WriteAll(to, data);
            SteamRemoteStorage.FileDelete(from);
        }

        public void Delete(string path) => SteamRemoteStorage.FileDelete(path);
    }
}
#endif
