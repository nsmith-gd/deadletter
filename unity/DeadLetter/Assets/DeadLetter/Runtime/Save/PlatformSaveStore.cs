using DeadLetter.Core.Platform;
using DeadLetter.Core.Save;
using DeadLetter.Runtime.Platform;

namespace DeadLetter.Runtime.Save
{
    /// <summary>
    /// The save store this build writes to (U-14 over U-17's file systems): Core's <see cref="AtomicFileStore"/> (temp file,
    /// backup, checksum) on the platform's <see cref="IFileSystem"/>:
    /// <list type="bullet">
    /// <item>Switch: <see cref="SwitchSaveStub"/> (stores nothing until the nn::fs store exists; a release build will not compile).</item>
    /// <item>Steam with Steam Cloud available (<c>DL_STEAM</c>): <c>SteamRemoteStorageFileSystem</c>.</item>
    /// <item>Everything else (Itch, the editor, Steam without cloud): <see cref="LocalFileSystem"/> under persistentDataPath.</item>
    /// </list>
    /// Built once at boot by the GameHost, after <see cref="PlatformServices.Initialize"/> (PlatformServicesHost runs first).
    /// </summary>
    public static class PlatformSaveStore
    {
        /// <summary>Seconds between slot writes on Switch (§4.28: the card is slow and wears; the service holds a pending write).</summary>
        public const double SwitchMinSecondsBetweenWrites = 2;

        public static ISaveStore Create(IPlatformServices services)
        {
            PlatformKind kind = services != null ? services.Kind : PlatformKind.Desktop;
            if (kind == PlatformKind.Switch) return new AtomicFileStore(new SwitchSaveStub());
#if DL_STEAM && UNITY_STANDALONE
            if (kind == PlatformKind.Steam && services.CloudSync != null && services.CloudSync.IsAvailable)
                return new AtomicFileStore(new SteamRemoteStorageFileSystem());
#endif
            return new AtomicFileStore(new LocalFileSystem());
        }

        /// <summary>The write rate limit for <paramref name="kind"/> (<see cref="CheckpointService.MinSecondsBetweenWrites"/>).</summary>
        public static double MinSecondsBetweenWrites(PlatformKind kind) => kind == PlatformKind.Switch ? SwitchMinSecondsBetweenWrites : 0;
    }
}
