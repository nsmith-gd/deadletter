using System;

namespace DeadLetter.Core.Settings
{
    /// <summary>The five mixer groups (U-16). Each has an AudioMixer exposed parameter named by <see cref="AudioLevels.ExposedParameter"/>.</summary>
    public enum AudioGroup
    {
        Master = 0,
        Music = 1,
        Sfx = 2,
        Voice = 3,
        Ambience = 4,
    }

    /// <summary>
    /// Slider → mixer maths, engine-free so it is tested here. The Runtime <c>SettingsStore</c> calls
    /// <c>AudioMixer.SetFloat(ExposedParameter(g), Decibels(settings, g))</c> for each group.
    /// <para>
    /// The prototype's two toggles are kept: Sound off mutes SFX, Voice and Ambience (<c>Sound.setEnabled</c>, L8286);
    /// Music off mutes Music (L8287). Master is not multiplied into the child groups: the mixer's group hierarchy does
    /// that (Music, SFX, Voice and Ambience route into Master).
    /// </para>
    /// </summary>
    public static class AudioLevels
    {
        /// <summary>Mixer floor, dB. Unity's mixer attenuation goes down to −80 dB.</summary>
        public const double SilentDb = -80.0;

        /// <summary>All groups, in the options screen's order.</summary>
        public static readonly AudioGroup[] All =
        {
            AudioGroup.Master, AudioGroup.Music, AudioGroup.Sfx, AudioGroup.Voice, AudioGroup.Ambience,
        };

        /// <summary>The exposed parameter name on the U-16 mixer.</summary>
        public static string ExposedParameter(AudioGroup g)
        {
            switch (g)
            {
                case AudioGroup.Master: return "Master";
                case AudioGroup.Music: return "Music";
                case AudioGroup.Sfx: return "SFX";
                case AudioGroup.Voice: return "Voice";
                case AudioGroup.Ambience: return "Ambience";
                default: throw new ArgumentOutOfRangeException(nameof(g));
            }
        }

        /// <summary>Slider value for <paramref name="g"/>, 0–1, before the toggles.</summary>
        public static double Slider(GameSettings s, AudioGroup g)
        {
            switch (g)
            {
                case AudioGroup.Master: return s.MasterVolume;
                case AudioGroup.Music: return s.MusicVolume;
                case AudioGroup.Sfx: return s.SfxVolume;
                case AudioGroup.Voice: return s.VoiceVolume;
                case AudioGroup.Ambience: return s.AmbienceVolume;
                default: throw new ArgumentOutOfRangeException(nameof(g));
            }
        }

        /// <summary>Linear gain sent to the group: the slider, zeroed by the prototype's Sound/Music toggles.</summary>
        public static double Linear(GameSettings s, AudioGroup g)
        {
            double v = Slider(s, g);
            if (double.IsNaN(v)) v = 1;
            v = v < 0 ? 0 : v > 1 ? 1 : v;
            switch (g)
            {
                case AudioGroup.Music: return s.Music ? v : 0;
                case AudioGroup.Sfx:
                case AudioGroup.Voice:
                case AudioGroup.Ambience: return s.Sound ? v : 0;
                default: return v;
            }
        }

        /// <summary>The group's attenuation in dB for the mixer.</summary>
        public static double Decibels(GameSettings s, AudioGroup g) => LinearToDecibels(Linear(s, g));

        /// <summary><c>20·log10(v)</c>, floored at <see cref="SilentDb"/> (0 → −80 dB, 1 → 0 dB, 0.5 → −6.02 dB).</summary>
        public static double LinearToDecibels(double linear)
        {
            if (double.IsNaN(linear) || linear <= 0) return SilentDb;
            if (linear >= 1) return 0;
            double db = 20.0 * Math.Log10(linear);
            return db < SilentDb ? SilentDb : db;
        }
    }
}
