using System;
using System.Collections.Generic;
using DeadLetter.Core.Platform;

namespace DeadLetter.Core.Save
{
    /// <summary>Subtitle and letter text size (§4.29 "subtitles size"). Stored as its number under <c>opt/subtitleSize</c>.</summary>
    public enum TextSize
    {
        Small = 0,
        Default = 1,
        Large = 2,
        ExtraLarge = 3,
    }

    /// <summary>
    /// The player's options, the one settings model (§4.4, §4.29; prototype <c>OPTS</c> and <c>dl01-bright</c>, L8283,
    /// L8306–L8312, labels L170–177), plus U-17's additions (volumes, text, cues, glyphs, rebinding). Defaults are the
    /// prototype's except <see cref="Telemetry"/>. Persisted in the <see cref="SaveModel"/> under <c>opt/</c> keys and
    /// applied by <see cref="CheckpointService.ApplySettings"/>; the Runtime <c>SettingsStore</c> pushes them to the
    /// engine. A missing key reads as its default and a numeric is clamped into range, so a new option needs no
    /// migration: add a field with its default, one line each in <see cref="Write"/> and <see cref="Read"/>, and a
    /// default test. Never rename a key or change its meaning without a <see cref="SaveMigrations"/> step.
    /// <para><c>opt/</c> keys this build does not know (a newer build's options) are kept in <see cref="UnknownOptions"/>
    /// and written back unchanged.</para>
    /// </summary>
    public sealed class Settings
    {
        public const string Prefix = "opt/";
        /// <summary>Brightness range and default, L8308 (<c>clamp(+v || 1, 0.8, 1.8)</c>), L175.</summary>
        public const double BrightnessMin = 0.8, BrightnessMax = 1.8, BrightnessDefault = 1.0;
        /// <summary>Renderer exposure = 1.4 × brightness, L8309.</summary>
        public const double ExposurePerBrightness = 1.4;
        /// <summary>Bloom strength: 0.55 normally, 0.35 in calm mode, L8290.</summary>
        public const double BloomStrength = 0.55, BloomStrengthCalm = 0.35;

        // ---- Prototype options (OPTS, L8283) ---------------------------------------------------------------------------
        /// <summary>"Auto-run (hold Shift or B to walk)", L170 (<c>autorun</c>). Feeds <c>D17Motor.AutoRun</c>.</summary>
        public bool AutoRun = true;
        /// <summary>"Sound", L171. Off mutes SFX, Voice and Ambience (<c>Sound.setEnabled</c>, L8286).</summary>
        public bool Sound = true;
        /// <summary>"Music", L172. Off mutes Music (<c>Music.setEnabled</c>, L8287).</summary>
        public bool Music = true;
        /// <summary>Button prompts and glints (<c>prompts</c>).</summary>
        public bool Prompts = true;
        /// <summary>The stuck-assist glyph (<c>assist</c>).</summary>
        public bool StuckAssist;
        /// <summary>No flicker, flashes, shake or sparks; bloom 0.35 (<c>calm</c>).</summary>
        public bool Calm;
        /// <summary>
        /// "Share anonymous play data", L177. Off by default: §4.30 makes the shipped uploader opt-in. The prototype
        /// defaulted it on (<c>telemetry: true</c>); this is a deliberate deviation.
        /// </summary>
        public bool Telemetry;
        /// <summary>Exposure scale, clamped to 0.8–1.8 (<c>dl01-bright</c>).</summary>
        public double Brightness = BrightnessDefault;

        // ---- New in the port (U-17) -------------------------------------------------------------------------------------
        /// <summary>Volume sliders, linear 0–1, one per U-16 mixer group (<c>Core.Audio.AudioLevels</c>).</summary>
        public double MasterVolume = 1, MusicVolume = 1, SfxVolume = 1, VoiceVolume = 1, AmbienceVolume = 1;
        /// <summary>Subtitles on.</summary>
        public bool Subtitles = true;
        /// <summary>Subtitle and letter text size (0 small, 1 default, 2 large, 3 extra large).</summary>
        public TextSize SubtitleSize = TextSize.Default;
        /// <summary>An opaque backing box behind subtitles and letter text.</summary>
        public bool SubtitleBackground;
        /// <summary>Every cue carried by colour alone (signal lamps, glint tint, ring C's cold light) also gets a shape.</summary>
        public bool ColourIndependentCues;
        /// <summary>Held inputs (DL-16's lever, held Use) become press-to-toggle (§4.29 "hold-to-press alternatives").</summary>
        public bool HoldToToggle;
        /// <summary>Button glyph set; Auto follows the last device used (<see cref="GlyphRules"/>).</summary>
        public GlyphPreference Glyphs = GlyphPreference.Auto;
        /// <summary>Input System binding overrides (<c>SaveBindingOverridesAsJson</c>). Empty = default bindings.</summary>
        public string BindingOverrides = "";

        /// <summary><c>opt/</c> keys this build does not know, written back unchanged.</summary>
        public SortedDictionary<string, SaveValue> UnknownOptions { get; private set; } = new SortedDictionary<string, SaveValue>(StringComparer.Ordinal);

        // ---- Derived ----------------------------------------------------------------------------------------------------
        /// <summary>Renderer exposure multiplier for the current brightness (L8309).</summary>
        public double Exposure => ExposurePerBrightness * Brightness;
        /// <summary>Bloom strength for the current calm setting (L8290).</summary>
        public double Bloom => Calm ? BloomStrengthCalm : BloomStrength;
        /// <summary>Text scale for <see cref="SubtitleSize"/>. Default (1.0) must already be legible on a Steam Deck.</summary>
        public double TextScale => TextScaleFor(SubtitleSize);

        public static double TextScaleFor(TextSize size)
        {
            switch (size)
            {
                case TextSize.Small: return 0.85;
                case TextSize.Large: return 1.25;
                case TextSize.ExtraLarge: return 1.6;
                default: return 1.0;
            }
        }

        /// <summary>A deep copy (the options screen edits a copy and applies it on confirm).</summary>
        public Settings Clone()
        {
            var c = (Settings)MemberwiseClone();
            c.UnknownOptions = new SortedDictionary<string, SaveValue>(UnknownOptions, StringComparer.Ordinal);
            return c;
        }

        /// <summary>Clamp every numeric into range (NaN → default) and repair enums and nulls.</summary>
        public void Sanitise()
        {
            Brightness = Clamp(Brightness, BrightnessMin, BrightnessMax, BrightnessDefault);
            MasterVolume = Clamp(MasterVolume, 0, 1, 1);
            MusicVolume = Clamp(MusicVolume, 0, 1, 1);
            SfxVolume = Clamp(SfxVolume, 0, 1, 1);
            VoiceVolume = Clamp(VoiceVolume, 0, 1, 1);
            AmbienceVolume = Clamp(AmbienceVolume, 0, 1, 1);
            if (SubtitleSize < TextSize.Small) SubtitleSize = TextSize.Small;
            else if (SubtitleSize > TextSize.ExtraLarge) SubtitleSize = TextSize.ExtraLarge;
            if (!Enum.IsDefined(typeof(GlyphPreference), Glyphs)) Glyphs = GlyphPreference.Auto;
            if (BindingOverrides == null) BindingOverrides = "";
            if (UnknownOptions == null) UnknownOptions = new SortedDictionary<string, SaveValue>(StringComparer.Ordinal);
        }

        public void Write(SaveDocument d)
        {
            foreach (var kv in UnknownOptions)
                if (kv.Key.StartsWith(Prefix, StringComparison.Ordinal) && !IsKnownKey(kv.Key)) d.Set(kv.Key, kv.Value);
            d.SetBool("opt/autorun", AutoRun);
            d.SetBool("opt/sound", Sound);
            d.SetBool("opt/music", Music);
            d.SetBool("opt/prompts", Prompts);
            d.SetBool("opt/assist", StuckAssist);
            d.SetBool("opt/calm", Calm);
            d.SetBool("opt/telemetry", Telemetry);
            d.SetDouble("opt/bright", Brightness);
            d.SetDouble("opt/volMaster", MasterVolume);
            d.SetDouble("opt/volMusic", MusicVolume);
            d.SetDouble("opt/volSfx", SfxVolume);
            d.SetDouble("opt/volVoice", VoiceVolume);
            d.SetDouble("opt/volAmbience", AmbienceVolume);
            d.SetBool("opt/subtitles", Subtitles);
            d.SetLong("opt/subtitleSize", (long)SubtitleSize);
            d.SetBool("opt/subtitleBox", SubtitleBackground);
            d.SetBool("opt/colourCues", ColourIndependentCues);
            d.SetBool("opt/holdToggle", HoldToToggle);
            d.SetLong("opt/glyphs", (long)Glyphs);
            d.SetString("opt/bindings", BindingOverrides ?? "");
        }

        /// <summary>Reads the options; a missing key or one of the wrong kind is its default, numerics are clamped.</summary>
        public static Settings Read(SaveDocument d)
        {
            var s = new Settings();
            s.AutoRun = d.GetBool("opt/autorun", s.AutoRun);
            s.Sound = d.GetBool("opt/sound", s.Sound);
            s.Music = d.GetBool("opt/music", s.Music);
            s.Prompts = d.GetBool("opt/prompts", s.Prompts);
            s.StuckAssist = d.GetBool("opt/assist", s.StuckAssist);
            s.Calm = d.GetBool("opt/calm", s.Calm);
            s.Telemetry = d.GetBool("opt/telemetry", s.Telemetry);
            s.Brightness = d.GetDouble("opt/bright", s.Brightness);
            s.MasterVolume = d.GetDouble("opt/volMaster", s.MasterVolume);
            s.MusicVolume = d.GetDouble("opt/volMusic", s.MusicVolume);
            s.SfxVolume = d.GetDouble("opt/volSfx", s.SfxVolume);
            s.VoiceVolume = d.GetDouble("opt/volVoice", s.VoiceVolume);
            s.AmbienceVolume = d.GetDouble("opt/volAmbience", s.AmbienceVolume);
            s.Subtitles = d.GetBool("opt/subtitles", s.Subtitles);
            long size = d.GetLong("opt/subtitleSize", (long)s.SubtitleSize);
            s.SubtitleSize = (TextSize)Math.Max((long)TextSize.Small, Math.Min((long)TextSize.ExtraLarge, size));
            s.SubtitleBackground = d.GetBool("opt/subtitleBox", s.SubtitleBackground);
            s.ColourIndependentCues = d.GetBool("opt/colourCues", s.ColourIndependentCues);
            s.HoldToToggle = d.GetBool("opt/holdToggle", s.HoldToToggle);
            long glyphs = d.GetLong("opt/glyphs", (long)s.Glyphs);
            s.Glyphs = glyphs >= int.MinValue && glyphs <= int.MaxValue ? (GlyphPreference)(int)glyphs : GlyphPreference.Auto;
            s.BindingOverrides = d.GetString("opt/bindings", s.BindingOverrides);
            foreach (var kv in d.Entries)
                if (kv.Key.StartsWith(Prefix, StringComparison.Ordinal) && !IsKnownKey(kv.Key)) s.UnknownOptions[kv.Key] = kv.Value;
            s.Sanitise();
            return s;
        }

        /// <summary>The keys <see cref="Write"/> writes, in order.</summary>
        public static readonly IReadOnlyList<string> KnownKeys = new[]
        {
            "opt/autorun", "opt/sound", "opt/music", "opt/prompts", "opt/assist", "opt/calm", "opt/telemetry", "opt/bright",
            "opt/volMaster", "opt/volMusic", "opt/volSfx", "opt/volVoice", "opt/volAmbience",
            "opt/subtitles", "opt/subtitleSize", "opt/subtitleBox", "opt/colourCues", "opt/holdToggle", "opt/glyphs", "opt/bindings",
        };

        public static bool IsKnownKey(string key)
        {
            for (int i = 0; i < KnownKeys.Count; i++) if (string.Equals(KnownKeys[i], key, StringComparison.Ordinal)) return true;
            return false;
        }

        private static double Clamp(double v, double lo, double hi, double fallback)
        {
            if (double.IsNaN(v)) return fallback;
            return v < lo ? lo : v > hi ? hi : v;
        }
    }
}
