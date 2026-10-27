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
            V2ToV3,
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
        /// Version 1 is a synthetic pre-release fixture format, never shipped: its keys were modelled on the fields of the
        /// prototype's <c>dl01-resume</c> record (L8336–L8342), but that record is localStorage JSON and is never
        /// imported. v1 holds <c>cp</c>, <c>scene</c>, <c>at</c> (ms since 1970),
        /// <c>found/curio|secret|voice/&lt;id&gt;</c>, <c>read/&lt;letter&gt;</c> and <c>persist/&lt;name&gt;</c>, with
        /// no snapshot, play time or options. It exists so the migration path is exercised by a fixture. Version 2 keeps every collection as a
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
    
        /// <summary>
        /// Version 3 keeps the seen moments in their own set (<c>seen/&lt;moment&gt;</c>, <see cref="SaveModel.Seen"/>) instead
        /// of as persist flags named <c>seen.&lt;moment&gt;</c> (the v2 home, <c>StoryFlags.Seen</c>, now gone): a seen moment
        /// is not story state a mechanism reads, and the runner asks the set every step.
        /// </summary>
        private static void V2ToV3(SaveDocument d)
        {
            foreach (var name in d.KeysUnder("flag/seen."))
            {
                bool on = d.GetBool("flag/seen." + name, false);
                d.Remove("flag/seen." + name);
                if (on) d.SetBool("seen/" + name, true);
            }
        }
    }
}
