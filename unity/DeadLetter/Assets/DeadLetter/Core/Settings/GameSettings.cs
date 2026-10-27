using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Options
{
    /// <summary>Subtitle and letter text size (port_architecture §4.29: "subtitles size").</summary>
    public enum TextSize
    {
        Small = 0,
        Default = 1,
        Large = 2,
        ExtraLarge = 3,
    }

    /// <summary>Which button glyphs to show. <see cref="Auto"/> follows the last device used (<c>Platform.GlyphRules</c>).</summary>
    public enum GlyphPreference
    {
        Auto = 0,
        Keyboard = 1,
        Xbox = 2,
        PlayStation = 3,
        Switch = 4,
        SteamDeck = 5,
    }

    /// <summary>
    /// The player's options (port_architecture §4.4, §4.29; task U-17). The first block is the prototype's options card,
    /// ported key for key from <c>game/undelivered/index.html</c> at 7b3c123: <c>OPTS</c> L8283, brightness L8307–8319,
    /// labels L170–177. The second block is new for the Unity port.
    /// <para>
    /// Plain fields so the options screen can bind to them; <see cref="SettingsSerializer"/> persists them. Keys this build
    /// does not know (written by a newer build) are kept in <see cref="UnknownEntries"/> and written back unchanged.
    /// </para>
    /// To add an option: add a field here with its default, add one entry to <see cref="SettingsSerializer"/>'s key table,
    /// and add a default test. Bump <see cref="CurrentVersion"/> only when an existing key changes meaning (then add the
    /// conversion to <see cref="SettingsSerializer.Migrate"/>); a new key never needs a bump.
    /// </summary>
    public sealed class GameSettings
    {
        /// <summary>Schema version this build writes.</summary>
        public const int CurrentVersion = 1;

        /// <summary>Brightness range and default, L8308 (<c>clamp(+v || 1, 0.8, 1.8)</c>), L175.</summary>
        public const double BrightnessMin = 0.8, BrightnessMax = 1.8, BrightnessDefault = 1.0;
        /// <summary>Renderer exposure = 1.4 × brightness, L8309.</summary>
        public const double ExposurePerBrightness = 1.4;
        /// <summary>Bloom strength: 0.55 normally, 0.35 in calm mode, L8290.</summary>
        public const double BloomStrength = 0.55, BloomStrengthCalm = 0.35;

        /// <summary>Version of the data this was read from (or <see cref="CurrentVersion"/> for a fresh one).</summary>
        public int Version = CurrentVersion;

        // ---- Prototype options (OPTS, L8283) -----------------------------------------------------------------------
        /// <summary>"Auto-run (hold Shift or B to walk)", L170. <c>autorun: true</c>. Feeds <c>D17Motor.AutoRun</c>.</summary>
        public bool AutoRun = true;
        /// <summary>"Sound", L171. <c>sound: true</c>. Off mutes SFX, Voice and Ambience (<c>Sound.setEnabled</c>, L8286).</summary>
        public bool Sound = true;
        /// <summary>"Music", L172. <c>music: true</c>. Off mutes Music (<c>Music.setEnabled</c>, L8287).</summary>
        public bool Music = true;
        /// <summary>"Light up things I can use, and show the button", L173. <c>prompts: true</c> (glints, L7000, L7632).</summary>
        public bool Prompts = true;
        /// <summary>"Show a button prompt if I'm stuck", L174. <c>assist: false</c> (idle hint glyph, L7634).</summary>
        public bool StuckAssist;
        /// <summary>"Reduce flicker and flashes", L176. <c>calm: false</c>: steady lights, no shake, no sparks, bloom 0.35.</summary>
        public bool Calm;
        /// <summary>
        /// "Share anonymous play data", L177. The prototype defaults it on (<c>telemetry: true</c>), but §4.30 makes the
        /// shipped uploader opt-in, so the port defaults it <b>off</b>. Deliberate deviation; see the U-17 README section.
        /// </summary>
        public bool Telemetry;
        /// <summary>Brightness 0.8–1.8, default 1 (L175, L8307–8319). Exposure = 1.4 × this.</summary>
        public double Brightness = BrightnessDefault;

        // ---- New in the port (U-17) ---------------------------------------------------------------------------------
        /// <summary>Volume sliders, linear 0–1. Each maps to the AudioMixer exposed parameter of the same group (U-16).</summary>
        public double MasterVolume = 1.0;
        public double MusicVolume = 1.0;
        public double SfxVolume = 1.0;
        public double VoiceVolume = 1.0;
        public double AmbienceVolume = 1.0;

        /// <summary>Subtitle and letter text size.</summary>
        public TextSize TextSize = TextSize.Default;
        /// <summary>Opaque backing panel behind subtitles and letter text (§4.29).</summary>
        public bool TextBackground;
        /// <summary>
        /// Every cue carried by colour alone (signal lamps, glint tint, ring C's cold light) also gets a shape, icon or
        /// pattern. Each view that uses a colour cue reads this flag.
        /// </summary>
        public bool ColourIndependentCues;
        /// <summary>Held actions (DL-16's lever, held Use) become press-to-toggle (§4.29 "hold-to-press alternatives").</summary>
        public bool ToggleHolds;
        /// <summary>Button glyph set; Auto follows the last device used.</summary>
        public GlyphPreference Glyphs = GlyphPreference.Auto;
        /// <summary>Input System binding overrides (<c>SaveBindingOverridesAsJson</c>). Empty = default bindings.</summary>
        public string BindingOverrides = "";

        /// <summary>Keys this build did not recognise, in file order, written back unchanged.</summary>
        public readonly List<KeyValuePair<string, string>> UnknownEntries = new List<KeyValuePair<string, string>>();

        /// <summary>Renderer exposure multiplier for the current brightness (L8309).</summary>
        public double Exposure => ExposurePerBrightness * Brightness;

        /// <summary>Bloom strength for the current calm setting (L8290).</summary>
        public double Bloom => Calm ? BloomStrengthCalm : BloomStrength;

        /// <summary>Text scale factor for <see cref="TextSize"/>. Default (1.0) must already be legible at 1280×800 on a
        /// 7" screen (Steam Deck); see the README's Steam Deck checklist.</summary>
        public double TextScale => TextScaleFor(TextSize);

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

        /// <summary>A fresh copy with every default.</summary>
        public static GameSettings Defaults() => new GameSettings();

        /// <summary>Clamp every numeric field into range (NaN → default). Called after loading and before applying.</summary>
        public void Sanitise()
        {
            Brightness = Clamp(Brightness, BrightnessMin, BrightnessMax, BrightnessDefault);
            MasterVolume = Clamp(MasterVolume, 0, 1, 1);
            MusicVolume = Clamp(MusicVolume, 0, 1, 1);
            SfxVolume = Clamp(SfxVolume, 0, 1, 1);
            VoiceVolume = Clamp(VoiceVolume, 0, 1, 1);
            AmbienceVolume = Clamp(AmbienceVolume, 0, 1, 1);
            if (!Enum.IsDefined(typeof(TextSize), TextSize)) TextSize = TextSize.Default;
            if (!Enum.IsDefined(typeof(GlyphPreference), Glyphs)) Glyphs = GlyphPreference.Auto;
            if (BindingOverrides == null) BindingOverrides = "";
        }

        /// <summary>Deep copy (the options screen edits a copy and applies on confirm).</summary>
        public GameSettings Clone()
        {
            var c = new GameSettings();
            c.CopyFrom(this);
            return c;
        }

        private void CopyFrom(GameSettings o)
        {
            Version = o.Version;
            AutoRun = o.AutoRun; Sound = o.Sound; Music = o.Music; Prompts = o.Prompts; StuckAssist = o.StuckAssist;
            Calm = o.Calm; Telemetry = o.Telemetry; Brightness = o.Brightness;
            MasterVolume = o.MasterVolume; MusicVolume = o.MusicVolume; SfxVolume = o.SfxVolume;
            VoiceVolume = o.VoiceVolume; AmbienceVolume = o.AmbienceVolume;
            TextSize = o.TextSize; TextBackground = o.TextBackground; ColourIndependentCues = o.ColourIndependentCues;
            ToggleHolds = o.ToggleHolds; Glyphs = o.Glyphs; BindingOverrides = o.BindingOverrides;
            UnknownEntries.Clear();
            UnknownEntries.AddRange(o.UnknownEntries);
        }

        private static double Clamp(double v, double lo, double hi, double fallback)
        {
            if (double.IsNaN(v) || double.IsInfinity(v)) return fallback;
            return v < lo ? lo : v > hi ? hi : v;
        }
    }
}
