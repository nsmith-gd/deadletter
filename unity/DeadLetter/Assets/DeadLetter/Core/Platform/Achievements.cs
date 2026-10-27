using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Platform
{
    /// <summary>One achievement: the store API name and whether it is hidden until earned.</summary>
    public sealed class AchievementDef
    {
        /// <summary>The API name, identical on every store's back end (Steamworks partner site "API Name").</summary>
        public readonly string Id;
        /// <summary>Hidden until unlocked (story spoilers).</summary>
        public readonly bool Hidden;
        /// <summary>Designer note: what earns it (not shown to players; the stores hold the display strings).</summary>
        public readonly string Note;

        public AchievementDef(string id, bool hidden, string note)
        {
            if (string.IsNullOrEmpty(id)) throw new ArgumentException("Achievement id is required.", nameof(id));
            Id = id; Hidden = hidden; Note = note ?? "";
        }
    }

    /// <summary>
    /// The achievement catalog. <b>Empty for now</b>: none are designed yet (director decision).
    /// <para>
    /// To add one:
    /// <list type="number">
    /// <item>Add <c>new AchievementDef("DL_FOUND_ALL_LETTERS", hidden: false, note: "Read every letter in chapter 1")</c>
    /// to <see cref="All"/>. API names: upper snake case with a <c>DL_</c> prefix; never rename one after release.</item>
    /// <item>Create the same API name on the Steamworks partner site (App Admin → Stats &amp; Achievements) with its
    /// display name, description and icons, and publish.</item>
    /// <item>Call <c>PlatformServices.Current.UnlockAchievement(id)</c> from the rule that earns it (a Core event, not a
    /// view). Unlocking twice is harmless.</item>
    /// <item><c>AchievementsTests</c> checks ids are unique and well formed.</item>
    /// </list>
    /// Switch has no achievement system; its implementation ignores unlocks.
    /// </para>
    /// </summary>
    public static class Achievements
    {
        private static readonly AchievementDef[] Catalog = new AchievementDef[0];

        public static IReadOnlyList<AchievementDef> All => Catalog;

        public static bool IsKnown(string id) => Find(id) != null;

        public static AchievementDef Find(string id)
        {
            if (string.IsNullOrEmpty(id)) return null;
            for (int i = 0; i < Catalog.Length; i++)
                if (string.Equals(Catalog[i].Id, id, StringComparison.Ordinal)) return Catalog[i];
            return null;
        }

        /// <summary>API-name rule: 3–64 chars, <c>A-Z 0-9 _</c>, starting with a letter.</summary>
        public static bool IsValidId(string id)
        {
            if (string.IsNullOrEmpty(id) || id.Length < 3 || id.Length > 64) return false;
            if (id[0] < 'A' || id[0] > 'Z') return false;
            for (int i = 0; i < id.Length; i++)
            {
                char c = id[i];
                if (!((c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_')) return false;
            }
            return true;
        }
    }
}
