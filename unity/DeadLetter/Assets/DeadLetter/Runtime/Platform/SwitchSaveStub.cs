using DeadLetter.Core.Save;

namespace DeadLetter.Runtime.Platform
{
    /// <summary>
    /// Nintendo Switch save data: a no-op placeholder (nothing is stored; Continue is never offered).
    /// TODO(U-17, NDA): implement over the NintendoSDK file system (<c>nn::fs</c>, via Unity's Switch support package
    /// from the Nintendo Developer Portal): mount the user's save data (<c>nn::fs::MountSaveData</c> /
    /// <c>EnsureSaveData</c>) once at boot; WriteAll/Replace/Delete on the mount, then <c>nn::fs::CommitSaveData</c>
    /// after <see cref="AtomicFileStore"/>'s final Replace (wrap the store, or commit in Replace when the destination is
    /// the slot file). Set <c>CheckpointService.MinSecondsBetweenWrites = 2</c> on Switch (§4.28) and Flush on suspend.
    /// Keep this file free of SDK code: the SDK and its headers may not be committed to this repository.
    /// </summary>
    public sealed class SwitchSaveStub : IFileSystem
    {
        public bool Exists(string path) => false;
        public byte[] ReadAll(string path) => null;
        public void WriteAll(string path, byte[] data) { }
        public void Replace(string from, string to) { }
        public void Delete(string path) { }
    }
}
