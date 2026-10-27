using System;

namespace DeadLetter.Core.Save
{
    /// <summary>
    /// The options (§4.29; prototype <c>OPTS</c> and <c>dl01-bright</c>, L8283, L8306–L8312), plus U-17's additions.
    /// Defaults are the prototype's. Persisted in the <see cref="SaveModel"/> under <c>opt/</c> keys; a missing key
    /// reads as its default, so new options need no migration.
    /// </summary>
    public sealed class Settings
    {
        public const double BrightnessMin = 0.8, BrightnessMax = 1.8;

        public bool AutoRun = true;
        public bool Sound = true;
        public bool Music = true;
        /// <summary>Button prompts and glints (<c>prompts</c>).</summary>
        public bool Prompts = true;
        /// <summary>The stuck-assist glyph (<c>assist</c>).</summary>
        public bool StuckAssist;
        /// <summary>No flicker, flashes, shake or sparks; bloom 0.35 (<c>calm</c>).</summary>
        public bool Calm;
        public bool Telemetry = true;
        /// <summary>Exposure scale, clamped to 0.8–1.8 (<c>dl01-bright</c>).</summary>
        public double Brightness = 1;
        /// <summary>U-17: subtitles on, their size step (0 small, 1 medium, 2 large) and a backing box.</summary>
        public bool Subtitles = true;
        public long SubtitleSize = 1;
        public bool SubtitleBackground;
        /// <summary>U-17: held inputs (DL-16's lever) become press-to-toggle.</summary>
        public bool HoldToToggle;

        public Settings Clone() => (Settings)MemberwiseClone();

        public void Write(SaveDocument d)
        {
            d.SetBool("opt/autorun", AutoRun);
            d.SetBool("opt/sound", Sound);
            d.SetBool("opt/music", Music);
            d.SetBool("opt/prompts", Prompts);
            d.SetBool("opt/assist", StuckAssist);
            d.SetBool("opt/calm", Calm);
            d.SetBool("opt/telemetry", Telemetry);
            d.SetDouble("opt/bright", Brightness);
            d.SetBool("opt/subtitles", Subtitles);
            d.SetLong("opt/subtitleSize", SubtitleSize);
            d.SetBool("opt/subtitleBox", SubtitleBackground);
            d.SetBool("opt/holdToggle", HoldToToggle);
        }

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
            double b = d.GetDouble("opt/bright", s.Brightness);
            s.Brightness = double.IsNaN(b) ? 1 : Math.Max(BrightnessMin, Math.Min(BrightnessMax, b));
            s.Subtitles = d.GetBool("opt/subtitles", s.Subtitles);
            s.SubtitleSize = Math.Max(0, Math.Min(2, d.GetLong("opt/subtitleSize", s.SubtitleSize)));
            s.SubtitleBackground = d.GetBool("opt/subtitleBox", s.SubtitleBackground);
            s.HoldToToggle = d.GetBool("opt/holdToggle", s.HoldToToggle);
            return s;
        }
    }
}
