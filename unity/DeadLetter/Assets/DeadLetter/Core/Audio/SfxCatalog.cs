using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Audio
{
    /// <summary>
    /// The render's file names (docs/unity/audio_inventory.md: <c>&lt;category&gt;_&lt;event&gt;[_variant].wav</c>):
    /// <c>_v1…_v9</c> is a take of a randomized sound, <c>_wet</c> is the dry file plus the depot reverb's return.
    /// Only a single digit after <c>_v</c> is a take: <c>mech_lift_crash_v040</c> is its own sound (v = 0.40).
    /// </summary>
    public static class SfxNaming
    {
        /// <summary>Splits <c>d17_step_v3.wav</c> into key <c>d17_step</c>, take 3, dry. A name with no take is take 1.</summary>
        public static bool TryParse(string fileName, out string key, out int take, out bool wet)
        {
            key = null; take = 1; wet = false;
            if (string.IsNullOrEmpty(fileName)) return false;
            string n = fileName.Replace('\\', '/');
            int slash = n.LastIndexOf('/');
            if (slash >= 0) n = n.Substring(slash + 1);
            if (n.EndsWith(".wav", StringComparison.OrdinalIgnoreCase)) n = n.Substring(0, n.Length - 4);
            if (n.Length == 0) return false;
            if (n.EndsWith("_wet", StringComparison.Ordinal)) { wet = true; n = n.Substring(0, n.Length - 4); }
            if (n.Length > 3 && n[n.Length - 3] == '_' && n[n.Length - 2] == 'v' && n[n.Length - 1] >= '1' && n[n.Length - 1] <= '9')
            {
                take = n[n.Length - 1] - '0';
                n = n.Substring(0, n.Length - 3);
            }
            key = n;
            return n.Length > 0;
        }

        /// <summary>Continuous layers: <c>loop_*</c> (Sound), <c>amb_*_loop</c> (emitters), <c>voice_crackle_*</c> (voice beds).</summary>
        public static bool IsLoop(string key) =>
            key != null && (key.StartsWith("loop_", StringComparison.Ordinal) || key.EndsWith("_loop", StringComparison.Ordinal)
                            || key.StartsWith("voice_crackle_", StringComparison.Ordinal));
    }

    /// <summary>How the bank picks between a sound's dry and baked-reverb files.</summary>
    public enum WetPolicy
    {
        /// <summary>Use the <c>_wet</c> file wherever one exists (the reviewer's default on #20: bake the reverb).</summary>
        PreferWet,
        /// <summary>Dry files only (for a later runtime reverb send).</summary>
        Dry,
    }

    /// <summary>One bank key: its playable files, one per take, in take order.</summary>
    public sealed class SfxEntry
    {
        public readonly string Key;
        public readonly string[] Files;
        public readonly bool Loop;

        public SfxEntry(string key, string[] files, bool loop)
        {
            Key = key; Files = files; Loop = loop;
        }

        public int Takes => Files.Length;
    }

    /// <summary>
    /// The SfxBank's contents, built from the rendered file names (the Editor importer passes the files in
    /// <c>art/sfx/out/</c>). Keys are the file stems without take and <c>_wet</c>.
    /// </summary>
    public sealed class SfxCatalog
    {
        private readonly List<SfxEntry> _entries;
        private readonly Dictionary<string, SfxEntry> _byKey;

        private SfxCatalog(List<SfxEntry> entries)
        {
            _entries = entries;
            _byKey = new Dictionary<string, SfxEntry>(StringComparer.Ordinal);
            foreach (SfxEntry e in entries) _byKey[e.Key] = e;
        }

        public IReadOnlyList<SfxEntry> Entries => _entries;

        public SfxEntry Find(string key) => key != null && _byKey.TryGetValue(key, out SfxEntry e) ? e : null;

        /// <summary>
        /// Groups <paramref name="fileNames"/> (with or without <c>.wav</c>, paths allowed) by key, takes in order. With
        /// <see cref="WetPolicy.PreferWet"/> a take's <c>_wet</c> file replaces its dry one. A wet file with no dry
        /// partner still counts. Entries are sorted by key (ordinal) so the bank is stable.
        /// </summary>
        public static SfxCatalog FromFiles(IEnumerable<string> fileNames, WetPolicy policy = WetPolicy.PreferWet)
        {
            var dry = new Dictionary<string, SortedDictionary<int, string>>(StringComparer.Ordinal);
            var wet = new Dictionary<string, SortedDictionary<int, string>>(StringComparer.Ordinal);
            foreach (string f in fileNames)
            {
                if (!SfxNaming.TryParse(f, out string key, out int take, out bool isWet)) continue;
                string stem = Stem(f);
                var map = isWet ? wet : dry;
                if (!map.TryGetValue(key, out var takes)) map[key] = takes = new SortedDictionary<int, string>();
                takes[take] = stem;
            }
            var keys = new SortedSet<string>(dry.Keys, StringComparer.Ordinal);
            foreach (string k in wet.Keys) keys.Add(k);
            var entries = new List<SfxEntry>();
            foreach (string key in keys)
            {
                dry.TryGetValue(key, out var d);
                wet.TryGetValue(key, out var w);
                var takeNumbers = new SortedSet<int>();
                if (d != null) foreach (int t in d.Keys) takeNumbers.Add(t);
                if (w != null) foreach (int t in w.Keys) takeNumbers.Add(t);
                var files = new List<string>();
                foreach (int t in takeNumbers)
                {
                    string dryFile = null, wetFile = null;
                    if (d != null) d.TryGetValue(t, out dryFile);
                    if (w != null) w.TryGetValue(t, out wetFile);
                    string pick = policy == WetPolicy.PreferWet ? wetFile ?? dryFile : dryFile ?? wetFile;
                    files.Add(pick);
                }
                entries.Add(new SfxEntry(key, files.ToArray(), SfxNaming.IsLoop(key)));
            }
            return new SfxCatalog(entries);
        }

        private static string Stem(string f)
        {
            string n = f.Replace('\\', '/');
            int slash = n.LastIndexOf('/');
            if (slash >= 0) n = n.Substring(slash + 1);
            return n.EndsWith(".wav", StringComparison.OrdinalIgnoreCase) ? n.Substring(0, n.Length - 4) : n;
        }
    }

    public enum SfxPickMode
    {
        /// <summary>A random take, never the one just played (the web build re-randomizes every call).</summary>
        RandomNoRepeat,
        /// <summary>Takes in turn.</summary>
        RoundRobin,
    }

    /// <summary>Chooses which take of a sound plays, seeded, per key.</summary>
    public sealed class SfxPicker
    {
        private readonly AudioRng _rng;
        private readonly Dictionary<string, int> _last = new Dictionary<string, int>(StringComparer.Ordinal);

        public SfxPicker(uint seed, SfxPickMode mode = SfxPickMode.RandomNoRepeat)
        {
            _rng = new AudioRng(seed);
            Mode = mode;
        }

        public SfxPickMode Mode { get; set; }

        /// <summary>The take index (0-based) to play for <paramref name="key"/> with <paramref name="takes"/> takes.</summary>
        public int Next(string key, int takes)
        {
            if (takes <= 1) return 0;
            bool had = _last.TryGetValue(key, out int last);
            int pick;
            if (Mode == SfxPickMode.RoundRobin) pick = had ? (last + 1) % takes : 0;
            else if (!had || last >= takes) pick = _rng.Next(takes);
            else
            {
                pick = _rng.Next(takes - 1);
                if (pick >= last) pick++;
            }
            _last[key] = pick;
            return pick;
        }
    }
}
