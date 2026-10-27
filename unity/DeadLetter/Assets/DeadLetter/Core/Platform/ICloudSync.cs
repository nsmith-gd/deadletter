namespace DeadLetter.Core.Platform
{
    /// <summary>
    /// A narrow, blob-level cloud store: whole named files in and out, nothing else. It deliberately knows nothing about
    /// save slots or formats, so the save system (U-14's <c>ISaveStore</c>) can wrap it later: write locally first, then
    /// <see cref="Write"/> the same bytes; on load, compare and pick. Steam implements it with Steam Remote Storage (Steam
    /// Auto-Cloud is the zero-code alternative, configured on the partner site). Switch save data is not "cloud" from
    /// the game's side (the system backs it up), so the Switch stub returns null for <c>CloudSync</c> and does its
    /// commit in the save store instead.
    /// </summary>
    public interface ICloudSync
    {
        /// <summary>Cloud enabled for this account and app right now.</summary>
        bool IsAvailable { get; }

        bool Exists(string name);

        /// <summary>Read the whole file; false (and null) when missing or unavailable.</summary>
        bool TryRead(string name, out byte[] data);

        /// <summary>Write the whole file, replacing any previous one.</summary>
        bool Write(string name, byte[] data);

        bool Delete(string name);
    }
}
