using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Save
{
    /// <summary>
    /// One save slot (§4.28, the prototype's <c>dl01-resume</c> record, L8336–L8342, plus the options): the checkpoint
    /// name, the scene, the persist flags, the mechanism snapshot taken when the checkpoint was reached, play time and
    /// settings. The world is rebuilt from the checkpoint and the flags (derived); the snapshot then puts every
    /// mechanism back exactly as it was when the checkpoint was reached (the plan's "Recovery": braked platforms,
    /// docked routes, inserted parts stay as left). A snapshot that no longer fits the scene is skipped.
    /// <para>Keys (version 4): <c>cp</c>, <c>scene</c>, <c>playTime</c>, <c>flag/&lt;name&gt;</c> (true),
    /// <c>seen/&lt;moment&gt;</c> (true), <c>mech/&lt;id&gt;/&lt;field&gt;</c> (the graph snapshot), <c>opt/&lt;name&gt;</c>
    /// (<see cref="Settings"/>). Version 3 added the seen moments, version 4 the clock timers' elapsed time
    /// (<see cref="SaveMigrations"/>).</para>
    /// </summary>
    public sealed class SaveModel
    {
        public const int CurrentVersion = 4;

        private const string FlagPrefix = "flag/", SeenPrefix = "seen/", MechPrefix = "mech/";

        public string Checkpoint = "start";
        /// <summary>The scene the checkpoint is in (the title card's "Continue: …").</summary>
        public string Scene = "";
        public double PlayTime;
        /// <summary>The set persist flags, sorted ordinal.</summary>
        public List<string> Flags = new List<string>();
        /// <summary>
        /// The directed moments and once-only beats already played (the prototype's <c>seen</c> set, <c>once()</c>,
        /// L1309–L1310: <c>wake</c>'s <c>labelWake</c>, <c>realise</c>, <c>awe</c>...), sorted ordinal. A checkpoint
        /// replay or a continue never plays them again; Start over clears them (§4.5).
        /// </summary>
        public List<string> Seen = new List<string>();
        /// <summary>The graph snapshot at the checkpoint; null: rebuild from the checkpoint alone.</summary>
        public MemorySnapshot Mechanisms;
        public Settings Settings = new Settings();
        /// <summary>
        /// Only the options are saved: the player changed them before ever starting a game. Nothing to continue (the
        /// prototype kept options apart from progress, so a fresh install never offers Continue).
        /// </summary>
        public bool OptionsOnly;

        public SaveDocument ToDocument()
        {
            var d = new SaveDocument(CurrentVersion);
            d.SetString("cp", Checkpoint ?? throw new InvalidOperationException("A save needs a checkpoint."));
            d.SetString("scene", Scene ?? "");
            d.SetDouble("playTime", PlayTime);
            if (OptionsOnly) d.SetBool("optionsOnly", true);
            foreach (var f in Flags) d.SetBool(FlagPrefix + f, true);
            foreach (var m in Seen ?? new List<string>()) d.SetBool(SeenPrefix + m, true);
            Mechanisms?.CopyTo(new PrefixWriter(d, MechPrefix));
            (Settings ?? new Settings()).Write(d);
            return d;
        }

        /// <summary>From a document already migrated to <see cref="CurrentVersion"/>.</summary>
        public static SaveModel FromDocument(SaveDocument d)
        {
            if (d.Version != CurrentVersion) throw new InvalidOperationException("Migrate to v" + CurrentVersion + " first (got v" + d.Version + ").");
            var m = new SaveModel
            {
                Checkpoint = d.GetString("cp", null) ?? throw new FormatException("The save has no checkpoint."),
                Scene = d.GetString("scene", ""),
                PlayTime = d.GetDouble("playTime", 0),
                OptionsOnly = d.GetBool("optionsOnly", false),
                Settings = Settings.Read(d),
            };
            foreach (var f in d.KeysUnder(FlagPrefix)) if (d.GetBool(FlagPrefix + f, false)) m.Flags.Add(f);
            m.Flags.Sort(StringComparer.Ordinal);
            foreach (var n in d.KeysUnder(SeenPrefix)) if (d.GetBool(SeenPrefix + n, false)) m.Seen.Add(n);
            m.Seen.Sort(StringComparer.Ordinal);
            var mech = new MemorySnapshot();
            foreach (var kv in d.Entries)
            {
                if (!kv.Key.StartsWith(MechPrefix, StringComparison.Ordinal)) continue;
                string k = kv.Key.Substring(MechPrefix.Length);
                var v = kv.Value;
                switch (v.Kind)
                {
                    case SaveValueKind.Double: mech.WriteDouble(k, BitConverter.Int64BitsToDouble(v.Bits)); break;
                    case SaveValueKind.Long: mech.WriteLong(k, v.Bits); break;
                    case SaveValueKind.Bool: mech.WriteBool(k, v.Bits != 0); break;
                    default: throw new FormatException("Snapshot field '" + k + "' is a string.");
                }
            }
            m.Mechanisms = mech.Count > 0 ? mech : null;
            return m;
        }

        private sealed class PrefixWriter : ISnapshotWriter
        {
            private readonly SaveDocument _d;
            private readonly string _prefix;
            public PrefixWriter(SaveDocument d, string prefix) { _d = d; _prefix = prefix; }
            public void WriteDouble(string key, double value) => _d.SetDouble(_prefix + key, value);
            public void WriteLong(string key, long value) => _d.SetLong(_prefix + key, value);
            public void WriteBool(string key, bool value) => _d.SetBool(_prefix + key, value);
        }
    }
}
