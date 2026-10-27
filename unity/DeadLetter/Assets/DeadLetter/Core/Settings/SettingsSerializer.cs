using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;

namespace DeadLetter.Core.Settings
{
    /// <summary>
    /// Reads and writes <see cref="GameSettings"/> as UTF-8 <c>key=value</c> lines:
    /// <code>
    /// # Dead Letter settings
    /// version=1
    /// autoRun=1
    /// volume.music=0.8
    /// input.bindings={"bindings":[...]}
    /// </code>
    /// <list type="bullet">
    /// <item>No reflection: a hand-written key table (IL2CPP / AOT safe, and renaming a field never renames a key).</item>
    /// <item>Forward compatible: keys this build does not know are kept, in order, and written back after the known ones.
    /// A file from a newer schema keeps its higher version number.</item>
    /// <item>Forgiving: a bad value leaves that option at its default; a malformed line is dropped; empty or garbage
    /// input gives the defaults. Reading never throws.</item>
    /// <item>Stable: the same settings always write the same text (known keys in table order, invariant culture,
    /// round-trip doubles), so the file diffs cleanly and cloud sync does not see spurious changes.</item>
    /// </list>
    /// Values escape <c>\</c>, newline and carriage return as <c>\\</c>, <c>\n</c>, <c>\r</c> (binding JSON may contain
    /// newlines). Everything after the first <c>=</c> is the value, so values may contain <c>=</c>.
    /// </summary>
    public static class SettingsSerializer
    {
        public const string VersionKey = "version";
        public const string Header = "# Dead Letter settings. Unknown keys are kept; delete this file to reset.";
        /// <summary>Longest key accepted; anything longer is treated as a corrupt line.</summary>
        public const int MaxKeyLength = 64;

        private sealed class Entry
        {
            public readonly string Key;
            public readonly Func<GameSettings, string> Write;
            /// <summary>Returns false when the value does not parse (the option keeps its current value).</summary>
            public readonly Func<GameSettings, string, bool> Read;

            public Entry(string key, Func<GameSettings, string> write, Func<GameSettings, string, bool> read)
            {
                Key = key; Write = write; Read = read;
            }
        }

        // The key table. Order is the file order. Never rename a key: add a new one and migrate (see GameSettings).
        private static readonly Entry[] Entries =
        {
            Bool("autoRun", s => s.AutoRun, (s, v) => s.AutoRun = v),
            Bool("sound", s => s.Sound, (s, v) => s.Sound = v),
            Bool("music", s => s.Music, (s, v) => s.Music = v),
            Bool("prompts", s => s.Prompts, (s, v) => s.Prompts = v),
            Bool("stuckAssist", s => s.StuckAssist, (s, v) => s.StuckAssist = v),
            Bool("calm", s => s.Calm, (s, v) => s.Calm = v),
            Bool("telemetry", s => s.Telemetry, (s, v) => s.Telemetry = v),
            Number("brightness", s => s.Brightness, (s, v) => s.Brightness = v),
            Number("volume.master", s => s.MasterVolume, (s, v) => s.MasterVolume = v),
            Number("volume.music", s => s.MusicVolume, (s, v) => s.MusicVolume = v),
            Number("volume.sfx", s => s.SfxVolume, (s, v) => s.SfxVolume = v),
            Number("volume.voice", s => s.VoiceVolume, (s, v) => s.VoiceVolume = v),
            Number("volume.ambience", s => s.AmbienceVolume, (s, v) => s.AmbienceVolume = v),
            new Entry("text.size", s => TextSizeName(s.TextSize), (s, v) =>
            {
                TextSize t;
                if (!TryParseTextSize(v, out t)) return false;
                s.TextSize = t;
                return true;
            }),
            Bool("text.background", s => s.TextBackground, (s, v) => s.TextBackground = v),
            Bool("cues.colourIndependent", s => s.ColourIndependentCues, (s, v) => s.ColourIndependentCues = v),
            Bool("input.toggleHolds", s => s.ToggleHolds, (s, v) => s.ToggleHolds = v),
            new Entry("input.glyphs", s => GlyphName(s.Glyphs), (s, v) =>
            {
                GlyphPreference g;
                if (!TryParseGlyph(v, out g)) return false;
                s.Glyphs = g;
                return true;
            }),
            new Entry("input.bindings", s => s.BindingOverrides ?? "", (s, v) => { s.BindingOverrides = v; return true; }),
        };

        /// <summary>The known keys, in file order.</summary>
        public static IEnumerable<string> KnownKeys
        {
            get { for (int i = 0; i < Entries.Length; i++) yield return Entries[i].Key; }
        }

        public static bool IsKnownKey(string key) => key == VersionKey || Find(key) != null;

        // ---- Write ----------------------------------------------------------------------------------------------------
        public static string Serialize(GameSettings s)
        {
            if (s == null) throw new ArgumentNullException(nameof(s));
            var sb = new StringBuilder(512);
            sb.Append(Header).Append('\n');
            int version = s.Version > GameSettings.CurrentVersion ? s.Version : GameSettings.CurrentVersion;
            sb.Append(VersionKey).Append('=').Append(version.ToString(CultureInfo.InvariantCulture)).Append('\n');
            for (int i = 0; i < Entries.Length; i++)
                sb.Append(Entries[i].Key).Append('=').Append(Escape(Entries[i].Write(s))).Append('\n');
            for (int i = 0; i < s.UnknownEntries.Count; i++)
            {
                var kv = s.UnknownEntries[i];
                if (!IsValidKey(kv.Key) || IsKnownKey(kv.Key)) continue;
                sb.Append(kv.Key).Append('=').Append(Escape(kv.Value ?? "")).Append('\n');
            }
            return sb.ToString();
        }

        public static byte[] SerializeUtf8(GameSettings s) => new UTF8Encoding(false).GetBytes(Serialize(s));

        // ---- Read -----------------------------------------------------------------------------------------------------
        /// <summary>Parse <paramref name="text"/>. Never throws; null, empty or garbage gives the defaults.</summary>
        public static GameSettings Deserialize(string text)
        {
            int rejected;
            return Deserialize(text, out rejected);
        }

        /// <summary>As <see cref="Deserialize(string)"/>; <paramref name="rejected"/> counts dropped lines and bad values.</summary>
        public static GameSettings Deserialize(string text, out int rejected)
        {
            rejected = 0;
            var s = new GameSettings();
            if (string.IsNullOrEmpty(text)) return s;

            if (text[0] == '\uFEFF') text = text.Substring(1);   // UTF-8 BOM from a hand edit
            int fileVersion = 0;   // 0 = no version line (treated as v1, the first schema)
            int pos = 0;
            while (pos <= text.Length)
            {
                int nl = text.IndexOf('\n', pos);
                if (nl < 0) nl = text.Length;
                string line = text.Substring(pos, nl - pos);
                pos = nl + 1;
                if (line.Length > 0 && line[line.Length - 1] == '\r') line = line.Substring(0, line.Length - 1);
                if (pos == 1 && line.Length > 0 && line[0] == '﻿') line = line.Substring(1);   // BOM

                string trimmed = line.Trim();
                if (trimmed.Length == 0 || trimmed[0] == '#') continue;

                int eq = line.IndexOf('=');
                if (eq <= 0) { rejected++; continue; }
                string key = line.Substring(0, eq).Trim();
                if (!IsValidKey(key)) { rejected++; continue; }
                string raw = line.Substring(eq + 1);
                if (HasControlChars(raw)) { rejected++; continue; }
                string value = Unescape(raw);

                if (key == VersionKey)
                {
                    int v;
                    if (int.TryParse(value.Trim(), NumberStyles.Integer, CultureInfo.InvariantCulture, out v) && v > 0) fileVersion = v;
                    else rejected++;
                    continue;
                }

                Entry e = Find(key);
                if (e != null)
                {
                    bool ok;
                    try { ok = e.Read(s, e.Key == "input.bindings" ? value : value.Trim()); }
                    catch (Exception) { ok = false; }
                    if (!ok) rejected++;
                    continue;
                }

                SetUnknown(s, key, value);
            }

            Migrate(s, fileVersion == 0 ? 1 : fileVersion);
            s.Sanitise();
            return s;
        }

        public static GameSettings DeserializeUtf8(byte[] data)
        {
            if (data == null || data.Length == 0) return new GameSettings();
            string text;
            try { text = new UTF8Encoding(false, false).GetString(data); }
            catch (Exception) { return new GameSettings(); }
            return Deserialize(text);
        }

        /// <summary>
        /// Brings a file of schema <paramref name="fromVersion"/> up to <see cref="GameSettings.CurrentVersion"/>.
        /// Version 1 is the first schema, so there is nothing to convert yet. A newer file is left as it is (its version
        /// is kept so this build does not write it back as older). Add each step as <c>if (fromVersion &lt; N) { ... }</c>.
        /// </summary>
        public static void Migrate(GameSettings s, int fromVersion)
        {
            s.Version = fromVersion > GameSettings.CurrentVersion ? fromVersion : GameSettings.CurrentVersion;
        }

        // ---- Helpers --------------------------------------------------------------------------------------------------
        private static Entry Find(string key)
        {
            for (int i = 0; i < Entries.Length; i++)
                if (string.Equals(Entries[i].Key, key, StringComparison.Ordinal)) return Entries[i];
            return null;
        }

        private static void SetUnknown(GameSettings s, string key, string value)
        {
            var list = s.UnknownEntries;
            for (int i = 0; i < list.Count; i++)
                if (string.Equals(list[i].Key, key, StringComparison.Ordinal))
                {
                    list[i] = new KeyValuePair<string, string>(key, value);
                    return;
                }
            list.Add(new KeyValuePair<string, string>(key, value));
        }

        /// <summary>Keys are 1–64 chars of <c>[A-Za-z0-9_.-]</c>.</summary>
        public static bool IsValidKey(string key)
        {
            if (string.IsNullOrEmpty(key) || key.Length > MaxKeyLength) return false;
            for (int i = 0; i < key.Length; i++)
            {
                char c = key[i];
                bool ok = (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') || (c >= '0' && c <= '9') || c == '_' || c == '.' || c == '-';
                if (!ok) return false;
            }
            return true;
        }

        private static bool HasControlChars(string s)
        {
            for (int i = 0; i < s.Length; i++)
            {
                char c = s[i];
                if (c < 0x20 && c != '\t') return true;
                if (c == '�') return true;   // invalid UTF-8 decoded as the replacement character
            }
            return false;
        }

        public static string Escape(string v)
        {
            if (string.IsNullOrEmpty(v)) return "";
            if (v.IndexOf('\\') < 0 && v.IndexOf('\n') < 0 && v.IndexOf('\r') < 0) return v;
            var sb = new StringBuilder(v.Length + 8);
            for (int i = 0; i < v.Length; i++)
            {
                char c = v[i];
                if (c == '\\') sb.Append("\\\\");
                else if (c == '\n') sb.Append("\\n");
                else if (c == '\r') sb.Append("\\r");
                else sb.Append(c);
            }
            return sb.ToString();
        }

        public static string Unescape(string v)
        {
            if (string.IsNullOrEmpty(v) || v.IndexOf('\\') < 0) return v ?? "";
            var sb = new StringBuilder(v.Length);
            for (int i = 0; i < v.Length; i++)
            {
                char c = v[i];
                if (c == '\\' && i + 1 < v.Length)
                {
                    char n = v[i + 1];
                    if (n == '\\') { sb.Append('\\'); i++; continue; }
                    if (n == 'n') { sb.Append('\n'); i++; continue; }
                    if (n == 'r') { sb.Append('\r'); i++; continue; }
                }
                sb.Append(c);
            }
            return sb.ToString();
        }

        public static bool TryParseBool(string v, out bool result)
        {
            switch ((v ?? "").Trim().ToLowerInvariant())
            {
                case "1": case "true": case "yes": case "on": result = true; return true;
                case "0": case "false": case "no": case "off": result = false; return true;
                default: result = false; return false;
            }
        }

        public static bool TryParseNumber(string v, out double result)
        {
            if (!double.TryParse(v, NumberStyles.Float, CultureInfo.InvariantCulture, out result)) return false;
            return !double.IsNaN(result) && !double.IsInfinity(result);
        }

        public static string TextSizeName(TextSize t)
        {
            switch (t)
            {
                case TextSize.Small: return "small";
                case TextSize.Large: return "large";
                case TextSize.ExtraLarge: return "xlarge";
                default: return "default";
            }
        }

        public static bool TryParseTextSize(string v, out TextSize t)
        {
            switch ((v ?? "").Trim().ToLowerInvariant())
            {
                case "small": t = TextSize.Small; return true;
                case "default": t = TextSize.Default; return true;
                case "large": t = TextSize.Large; return true;
                case "xlarge": t = TextSize.ExtraLarge; return true;
                default: t = TextSize.Default; return false;
            }
        }

        public static string GlyphName(GlyphPreference g)
        {
            switch (g)
            {
                case GlyphPreference.Keyboard: return "keyboard";
                case GlyphPreference.Xbox: return "xbox";
                case GlyphPreference.PlayStation: return "playstation";
                case GlyphPreference.Switch: return "switch";
                case GlyphPreference.SteamDeck: return "steamdeck";
                default: return "auto";
            }
        }

        public static bool TryParseGlyph(string v, out GlyphPreference g)
        {
            switch ((v ?? "").Trim().ToLowerInvariant())
            {
                case "auto": g = GlyphPreference.Auto; return true;
                case "keyboard": g = GlyphPreference.Keyboard; return true;
                case "xbox": g = GlyphPreference.Xbox; return true;
                case "playstation": g = GlyphPreference.PlayStation; return true;
                case "switch": g = GlyphPreference.Switch; return true;
                case "steamdeck": g = GlyphPreference.SteamDeck; return true;
                default: g = GlyphPreference.Auto; return false;
            }
        }

        private static Entry Bool(string key, Func<GameSettings, bool> get, Action<GameSettings, bool> set)
        {
            return new Entry(key, s => get(s) ? "1" : "0", (s, v) =>
            {
                bool b;
                if (!TryParseBool(v, out b)) return false;
                set(s, b);
                return true;
            });
        }

        private static Entry Number(string key, Func<GameSettings, double> get, Action<GameSettings, double> set)
        {
            return new Entry(key, s => get(s).ToString("R", CultureInfo.InvariantCulture), (s, v) =>
            {
                double d;
                if (!TryParseNumber(v, out d)) return false;
                set(s, d);
                return true;
            });
        }
    }
}
