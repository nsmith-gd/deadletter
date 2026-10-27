using DeadLetter.Core.Save;
using UnityEngine;

#if UNITY_SWITCH && !DEVELOPMENT_BUILD
#error SwitchSaveStub stores nothing: a release Switch build needs the real save store over the NintendoSDK file system (nn::fs MountSaveData/CommitSaveData, NDA, TODO U-17). Implement it outside this repository before shipping.
#endif

namespace DeadLetter.Runtime.Platform
{
    /// <summary>
    /// Nintendo Switch save data: a no-op placeholder (nothing is stored; Continue is never offered). Every write
    /// "succeeds" and is dropped, so it warns once when first used, and a release (non-development) Switch build will
    /// not compile while it is in the project.
    /// TODO(U-17, NDA): implement over the NintendoSDK file system (<c>nn::fs</c>, via Unity's Switch support package
    /// from the Nintendo Developer Portal): mount the user's save data (<c>nn::fs::MountSaveData</c> /
    /// <c>EnsureSaveData</c>) once at boot; WriteAll/Replace/Delete on the mount, then <c>nn::fs::CommitSaveData</c>
    /// after <see cref="AtomicFileStore"/>'s final Replace (wrap the store, or commit in Replace when the destination is
    /// the slot file). Set <c>CheckpointService.MinSecondsBetweenWrites = 2</c> on Switch (§4.28) and Flush on suspend.
    /// Keep this file free of SDK code: the SDK and its headers may not be committed to this repository.
    /// </summary>
    public sealed class SwitchSaveStub : IFileSystem
    {
        private static bool _warned;

        private static void WarnOnce()
        {
            if (_warned) return;
            _warned = true;
            Debug.LogWarning("SwitchSaveStub: saves are NOT stored on this build (placeholder until the nn::fs store, U-17). Progress will be lost on quit.");
        }

        public bool Exists(string path) { WarnOnce(); return false; }
        public byte[] ReadAll(string path) { WarnOnce(); return null; }
        public void WriteAll(string path, byte[] data) => WarnOnce();
        public void Replace(string from, string to) => WarnOnce();
        public void Delete(string path) => WarnOnce();
    }
}
