using System;

namespace DeadLetter.Core.Save
{
    /// <summary>
    /// The version migration hook: <see cref="Steps"/>[n] turns a version n document into version n + 1 in place.
    /// To change the format, bump <see cref="SaveModel.CurrentVersion"/> and add one step here (with a fixture test of
    /// the old bytes). Steps edit keys only; they never throw for a well-formed older file.
    /// </summary>
    public static class SaveMigrations
    {
        /// <summary>Index = the version it migrates from. Version 0 never existed.</summary>
        public static readonly Action<SaveDocument>[] Steps =
        {
            null,
            V1ToV2,
        };

        public static bool TryMigrate(SaveDocument d, out string error)
        {
            if (d.Version < 1) { error = "unknown version " + d.Version; return false; }
            if (d.Version > SaveModel.CurrentVersion) { error = "saved by a newer build (v" + d.Version + ")"; return false; }
            while (d.Version < SaveModel.CurrentVersion)
            {
                Steps[d.Version](d);
                d.Version++;
            }
            error = null;
            return true;
        }

        /// <summary>
        /// Version 1 mirrored the prototype's <c>dl01-resume</c> record (L8336–L8342): <c>cp</c>, <c>scene</c>, <c>at</c>
        /// (ms since 1970), <c>found/curio|secret|voice/&lt;id&gt;</c>, <c>read/&lt;letter&gt;</c> and
        /// <c>persist/&lt;name&gt;</c>, with no snapshot, play time or options. Version 2 keeps every collection as a
        /// named persist flag (<see cref="StoryFlags"/>) and adds play time; options read as their defaults.
        /// </summary>
        private static void V1ToV2(SaveDocument d)
        {
            d.Remove("at");
            d.RenamePrefix("found/curio/", "flag/curio.");
            d.RenamePrefix("found/secret/", "flag/secret.");
            d.RenamePrefix("found/voice/", "flag/voice.");
            d.RenamePrefix("read/", "flag/letter.read.");
            d.RenamePrefix("persist/", "flag/persist.");
            if (!d.Contains("playTime")) d.SetDouble("playTime", 0);
            if (!d.Contains("scene")) d.SetString("scene", "");
        }
    }
}
