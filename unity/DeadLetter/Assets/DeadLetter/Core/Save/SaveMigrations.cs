using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Scenes;

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
            V3ToV4,
            V4ToV5,
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
        /// <para>Version 3 also added station snapshot fields (#22) that a v2 snapshot lacks; a restore reads them, so they
        /// are filled with what a v2 station implies: an act has one part (<c>act.part</c> = <c>act.lastPart</c> = 0, no
        /// chained clip); a latch's <c>pullF</c> is the Pull frame last taken while its act runs (−1 otherwise); a lever's
        /// <c>clipStuck</c> is the stuck it judged when its act started (v2 judged the clip there too).</para>
        /// </summary>
        private static void V2ToV3(SaveDocument d)
        {
            foreach (var name in d.KeysUnder("flag/seen."))
            {
                bool on = d.GetBool("flag/seen." + name, false);
                d.Remove("flag/seen." + name);
                if (on) d.SetBool("seen/" + name, true);
            }

            const string Mech = "mech/", ActFed = "act.fed";
            foreach (var rest in d.KeysUnder(Mech))
            {
                if (!rest.EndsWith("/" + ActFed, StringComparison.Ordinal)) continue;
                string m = Mech + rest.Substring(0, rest.Length - ActFed.Length);    // "mech/<id>/"
                if (!d.Contains(m + "act.part")) d.SetLong(m + "act.part", 0);
                if (!d.Contains(m + "act.lastPart")) d.SetLong(m + "act.lastPart", 0);
                if (d.Contains(m + "armedFor") && !d.Contains(m + "pullF"))             // Latch
                    d.SetDouble(m + "pullF", d.GetBool(m + "act.active", false) ? d.GetDouble(m + "act.last", -1) : -1);
                if (d.Contains(m + "stuck") && !d.Contains(m + "clipStuck"))            // Pawl, PointsLever
                    d.SetBool(m + "clipStuck", d.GetBool(m + "stuck", false));
            }
        }

        /// <summary>
        /// Version 4 added the clock timers' elapsed time (#48, <see cref="Mechanisms.ClockMark"/>): a door's delay
        /// (<c>heldElapsed</c>), a latch's arming (<c>armedElapsed</c>) and a seat row's hold (<c>allElapsed</c>), each timed on
        /// the game clock as the prototype does. A v3 snapshot has none, so each is filled NaN (no mark): the timer runs on its
        /// own sum of dt (<c>held</c>, <c>armedFor</c>, <c>allFor</c>), as v3 timed it.
        /// </summary>
        private static void V3ToV4(SaveDocument d)
        {
            const string Mech = "mech/";
            foreach (var rest in d.KeysUnder(Mech))
            {
                int slash = rest.LastIndexOf('/');
                if (slash < 0) continue;
                string m = Mech + rest.Substring(0, slash + 1), field = rest.Substring(slash + 1);     // "mech/<id>/", field
                if (field == "cued" && d.Contains(m + "held") && d.Contains(m + "t") && d.Contains(m + "pos") && !d.Contains(m + "heldElapsed"))
                    d.SetDouble(m + "heldElapsed", double.NaN);                                        // Door
                if (field == "armedFor" && !d.Contains(m + "armedElapsed")) d.SetDouble(m + "armedElapsed", double.NaN);   // Latch
                if (field == "allFor" && !d.Contains(m + "allElapsed")) d.SetDouble(m + "allElapsed", double.NaN);         // SeatRow
            }
        }

        /// <summary>
        /// Version 5 names the slot's chapter (<c>chapter</c>, <see cref="SaveModel.ChapterId"/>; #51): Continue builds that
        /// chapter's sim. A v4 slot has none, so it is resolved from the checkpoint (<see cref="ChapterOf"/>).
        /// </summary>
        private static void V4ToV5(SaveDocument d)
        {
            if (!d.Contains("chapter")) d.SetString("chapter", ChapterOf(d.GetString("cp", "")));
        }

        /// <summary>
        /// The chapter <paramref name="checkpoint"/> belongs to, by its place in <see cref="Checkpoint.GameOrder"/>: before
        /// <c>school</c> the prologue's, from <c>school</c> chapter 1's, from <c>ring_a</c> chapter 2's (each chapter's
        /// checkpoints are one run of the order: <c>ChapterDefs</c>' tables). Empty for a name outside the order.
        /// </summary>
        public static string ChapterOf(string checkpoint)
        {
            int at = Array.IndexOf(Checkpoint.GameOrder, checkpoint);
            if (at < 0) return "";
            string chapter = ChapterDefs.PrologueId;
            for (int i = 0; i < ChapterStarts.Length; i++)
                if (at >= Array.IndexOf(Checkpoint.GameOrder, ChapterStarts[i].first)) chapter = ChapterStarts[i].chapter;
            return chapter;
        }

        /// <summary>Each chapter after the prologue and its first checkpoint, in play order.</summary>
        private static readonly (string first, string chapter)[] ChapterStarts =
        {
            ("school", ChapterDefs.AttendanceId),
            ("ring_a", ChapterDefs.SomeoneHomeId),
        };
    }
}
