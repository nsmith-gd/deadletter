using System;
using System.Globalization;
using System.Linq;
using System.Threading;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Platform;
using DeadLetter.Core.Save;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>U-17's options on the one settings model, <see cref="Settings"/> (persisted in the save slot, §4.28/§4.29).</summary>
    public class SettingsDefaultsTests
    {
        // OPTS, index.html L8283: { sound: true, music: true, prompts: true, assist: false, calm: false, autorun: true, telemetry: true }
        [Fact]
        public void PrototypeToggles_DefaultAsInOpts()
        {
            var s = new Settings();
            Assert.True(s.AutoRun);
            Assert.True(s.Sound);
            Assert.True(s.Music);
            Assert.True(s.Prompts);
            Assert.False(s.StuckAssist);
            Assert.False(s.Calm);
        }

        [Fact]
        public void Telemetry_DefaultsOff_DeliberateDeviationForOptIn()
        {
            // The prototype defaults telemetry on; §4.30 makes the shipped uploader opt-in.
            Assert.False(new Settings().Telemetry);
            Assert.False(Settings.Read(new SaveDocument(SaveModel.CurrentVersion)).Telemetry);
        }

        [Fact]
        public void Brightness_DefaultAndRange_MatchPrototype()
        {
            // L175: range 0.8–1.8, value 1; L8309: exposure = 1.4 × v.
            var s = new Settings();
            Assert.Equal(1.0, s.Brightness);
            Assert.Equal(0.8, Settings.BrightnessMin);
            Assert.Equal(1.8, Settings.BrightnessMax);
            Assert.Equal(1.4, s.Exposure, 12);
        }

        [Fact]
        public void Bloom_CalmIs035_NormalIs055()
        {
            // L8290: bloom.strength = calm ? 0.35 : 0.55
            var s = new Settings();
            Assert.Equal(0.55, s.Bloom);
            s.Calm = true;
            Assert.Equal(0.35, s.Bloom);
        }

        [Fact]
        public void NewOptions_HaveNeutralDefaults()
        {
            var s = new Settings();
            Assert.Equal(1.0, s.MasterVolume);
            Assert.Equal(1.0, s.MusicVolume);
            Assert.Equal(1.0, s.SfxVolume);
            Assert.Equal(1.0, s.VoiceVolume);
            Assert.Equal(1.0, s.AmbienceVolume);
            Assert.True(s.Subtitles);
            Assert.Equal(TextSize.Default, s.SubtitleSize);
            Assert.Equal(1L, (long)s.SubtitleSize);   // U-14's "1 = medium"
            Assert.Equal(1.0, s.TextScale);
            Assert.False(s.SubtitleBackground);
            Assert.False(s.ColourIndependentCues);
            Assert.False(s.HoldToToggle);
            Assert.Equal(GlyphPreference.Auto, s.Glyphs);
            Assert.Equal("", s.BindingOverrides);
            Assert.Empty(s.UnknownOptions);
        }

        [Fact]
        public void TextSize_KeepsU14Numbering()
        {
            Assert.Equal(0, (int)TextSize.Small);
            Assert.Equal(1, (int)TextSize.Default);
            Assert.Equal(2, (int)TextSize.Large);
            Assert.Equal(3, (int)TextSize.ExtraLarge);
        }

        [Fact]
        public void TextScale_IncreasesWithSize()
        {
            double prev = 0;
            foreach (TextSize t in new[] { TextSize.Small, TextSize.Default, TextSize.Large, TextSize.ExtraLarge })
            {
                double k = Settings.TextScaleFor(t);
                Assert.True(k > prev);
                prev = k;
            }
        }

        [Fact]
        public void Sanitise_ClampsAndRepairs()
        {
            var s = new Settings
            {
                Brightness = 5, MasterVolume = -1, MusicVolume = double.NaN, SfxVolume = 2,
                SubtitleSize = (TextSize)99, Glyphs = (GlyphPreference)42, BindingOverrides = null,
            };
            s.Sanitise();
            Assert.Equal(1.8, s.Brightness);
            Assert.Equal(0.0, s.MasterVolume);
            Assert.Equal(1.0, s.MusicVolume);
            Assert.Equal(1.0, s.SfxVolume);
            Assert.Equal(TextSize.ExtraLarge, s.SubtitleSize);
            Assert.Equal(GlyphPreference.Auto, s.Glyphs);
            Assert.Equal("", s.BindingOverrides);
            s.Brightness = double.NaN;
            s.SubtitleSize = (TextSize)(-3);
            s.Sanitise();
            Assert.Equal(1.0, s.Brightness);
            Assert.Equal(TextSize.Small, s.SubtitleSize);
        }

        [Fact]
        public void Clone_IsDeep()
        {
            var a = new Settings { Calm = true, MusicVolume = 0.3 };
            a.UnknownOptions["opt/x"] = new SaveValue(SaveValueKind.Long, 1, null);
            var b = a.Clone();
            b.Calm = false;
            b.UnknownOptions["opt/y"] = new SaveValue(SaveValueKind.Long, 2, null);
            Assert.True(a.Calm);
            Assert.Equal(0.3, b.MusicVolume);
            Assert.Single(a.UnknownOptions);
            Assert.Equal(2, b.UnknownOptions.Count);
        }
    }

    public class SettingsPersistenceTests
    {
        private const string Json = "{\"bindings\":[{\"action\":\"Gameplay/Jump\",\"id\":\"a=b\",\"path\":\"<Keyboard>/k\"}]}\n{line2}\\end";

        private static Settings NonDefault()
        {
            return new Settings
            {
                AutoRun = false, Sound = false, Music = false, Prompts = false, StuckAssist = true, Calm = true,
                Telemetry = true, Brightness = 1.35, MasterVolume = 0.9, MusicVolume = 0.123456789, SfxVolume = 0,
                VoiceVolume = 0.5, AmbienceVolume = 0.25, Subtitles = false, SubtitleSize = TextSize.ExtraLarge,
                SubtitleBackground = true, ColourIndependentCues = true, HoldToToggle = true, Glyphs = GlyphPreference.PlayStation,
                BindingOverrides = Json,
            };
        }

        private static void AssertSame(Settings a, Settings b)
        {
            Assert.Equal(a.AutoRun, b.AutoRun);
            Assert.Equal(a.Sound, b.Sound);
            Assert.Equal(a.Music, b.Music);
            Assert.Equal(a.Prompts, b.Prompts);
            Assert.Equal(a.StuckAssist, b.StuckAssist);
            Assert.Equal(a.Calm, b.Calm);
            Assert.Equal(a.Telemetry, b.Telemetry);
            Assert.Equal(a.Brightness, b.Brightness);
            Assert.Equal(a.MasterVolume, b.MasterVolume);
            Assert.Equal(a.MusicVolume, b.MusicVolume);
            Assert.Equal(a.SfxVolume, b.SfxVolume);
            Assert.Equal(a.VoiceVolume, b.VoiceVolume);
            Assert.Equal(a.AmbienceVolume, b.AmbienceVolume);
            Assert.Equal(a.Subtitles, b.Subtitles);
            Assert.Equal(a.SubtitleSize, b.SubtitleSize);
            Assert.Equal(a.SubtitleBackground, b.SubtitleBackground);
            Assert.Equal(a.ColourIndependentCues, b.ColourIndependentCues);
            Assert.Equal(a.HoldToToggle, b.HoldToToggle);
            Assert.Equal(a.Glyphs, b.Glyphs);
            Assert.Equal(a.BindingOverrides, b.BindingOverrides);
            Assert.Equal(a.UnknownOptions, b.UnknownOptions);
        }

        private static Settings ViaDocument(Settings s)
        {
            var d = new SaveDocument(SaveModel.CurrentVersion);
            s.Write(d);
            return Settings.Read(d);
        }

        private static Settings ViaBytes(Settings s)
        {
            Assert.True(SaveCodec.TryLoad(SaveCodec.Encode(new SaveModel { Settings = s }), out var m, out string err), err);
            return m.Settings;
        }

        [Fact]
        public void RoundTrip_Defaults()
        {
            var d = new Settings();
            AssertSame(d, ViaDocument(d));
            AssertSame(d, ViaBytes(d));
        }

        [Fact]
        public void RoundTrip_EveryFieldChanged_IncludingMultilineBindingJson()
        {
            var a = NonDefault();
            AssertSame(a, ViaDocument(a));
            AssertSame(a, ViaBytes(a));
        }

        [Fact]
        public void Encode_IsStable_SameInputSameBytes()
        {
            byte[] once = SaveCodec.Encode(new SaveModel { Settings = NonDefault() });
            byte[] twice = SaveCodec.Encode(new SaveModel { Settings = ViaBytes(NonDefault()) });
            Assert.Equal(once, twice);
        }

        [Fact]
        public void Write_EveryKnownKeyOnce_UnderOpt_WithItsKind()
        {
            var d = new SaveDocument(SaveModel.CurrentVersion);
            NonDefault().Write(d);
            Assert.Equal(Settings.KnownKeys.OrderBy(k => k, StringComparer.Ordinal), d.Entries.Select(e => e.Key));
            Assert.Equal(Settings.KnownKeys.Count, Settings.KnownKeys.Distinct().Count());
            Assert.All(Settings.KnownKeys, k => Assert.StartsWith(Settings.Prefix, k));
            Assert.True(d.TryGet("opt/calm", out var v) && v.Kind == SaveValueKind.Bool);
            Assert.True(d.TryGet("opt/bright", out v) && v.Kind == SaveValueKind.Double);
            Assert.True(d.TryGet("opt/volMusic", out v) && v.Kind == SaveValueKind.Double);
            Assert.True(d.TryGet("opt/subtitleSize", out v) && v.Kind == SaveValueKind.Long && v.Bits == 3);
            Assert.True(d.TryGet("opt/glyphs", out v) && v.Kind == SaveValueKind.Long && v.Bits == (long)GlyphPreference.PlayStation);
            Assert.True(d.TryGet("opt/bindings", out v) && v.Kind == SaveValueKind.String && v.Text == Json);
        }

        [Fact]
        public void U14Keys_KeepTheirMeaning()
        {
            // A save written before U-17's options were merged: only U-14's keys.
            var d = new SaveDocument(SaveModel.CurrentVersion);
            d.SetBool("opt/autorun", false);
            d.SetDouble("opt/bright", 1.2);
            d.SetLong("opt/subtitleSize", 2);
            d.SetBool("opt/subtitleBox", true);
            d.SetBool("opt/holdToggle", true);
            var s = Settings.Read(d);
            Assert.False(s.AutoRun);
            Assert.Equal(1.2, s.Brightness);
            Assert.Equal(TextSize.Large, s.SubtitleSize);
            Assert.True(s.SubtitleBackground);
            Assert.True(s.HoldToToggle);
            Assert.Equal(1.0, s.MasterVolume);                        // missing → default
            Assert.Equal(GlyphPreference.Auto, s.Glyphs);
            Assert.Equal("", s.BindingOverrides);
            Assert.Empty(s.UnknownOptions);
        }

        [Fact]
        public void Encode_IsCultureInvariant()
        {
            var prev = Thread.CurrentThread.CurrentCulture;
            try
            {
                Thread.CurrentThread.CurrentCulture = new CultureInfo("de-DE");
                var a = new Settings { Brightness = 1.25, MusicVolume = 0.75 };
                byte[] de = SaveCodec.Encode(new SaveModel { Settings = a });
                Thread.CurrentThread.CurrentCulture = CultureInfo.InvariantCulture;
                Assert.Equal(de, SaveCodec.Encode(new SaveModel { Settings = a }));
                Assert.Equal(1.25, ViaBytes(a).Brightness);
            }
            finally { Thread.CurrentThread.CurrentCulture = prev; }
        }

        [Fact]
        public void UnknownOptKeys_ArePreserved_AndWrittenBack()
        {
            var d = new SaveDocument(SaveModel.CurrentVersion);
            d.SetBool("opt/future.hdr", true);
            d.SetBool("opt/calm", true);
            d.SetDouble("opt/future.fov", 72.5);
            d.SetString("opt/future.note", "a\nb");
            d.SetString("cp", "hall");                                 // not an option: not Settings' business
            var s = Settings.Read(d);
            Assert.True(s.Calm);
            Assert.Equal(new[] { "opt/future.fov", "opt/future.hdr", "opt/future.note" }, s.UnknownOptions.Keys);

            var again = ViaBytes(s);
            Assert.Equal(s.UnknownOptions, again.UnknownOptions);
            Assert.Equal("a\nb", again.UnknownOptions["opt/future.note"].Text);
            var w = new SaveDocument(SaveModel.CurrentVersion);
            again.Write(w);
            Assert.True(w.GetBool("opt/future.hdr", false));
            Assert.Equal(72.5, w.GetDouble("opt/future.fov", 0));
            Assert.False(w.Contains("cp"));
        }

        [Fact]
        public void UnknownEntry_ShadowingAKnownKey_DoesNotOverrideIt()
        {
            var s = new Settings();
            s.UnknownOptions["opt/calm"] = new SaveValue(SaveValueKind.Bool, 1, null);
            s.UnknownOptions["cp"] = new SaveValue(SaveValueKind.String, 0, "x");
            var d = new SaveDocument(SaveModel.CurrentVersion);
            s.Write(d);
            Assert.False(d.GetBool("opt/calm", true));
            Assert.False(d.Contains("cp"));
            Assert.False(Settings.Read(d).Calm);
            Assert.Empty(Settings.Read(d).UnknownOptions);
        }

        [Fact]
        public void EmptyDocument_GivesDefaults()
        {
            var s = Settings.Read(new SaveDocument(SaveModel.CurrentVersion));
            AssertSame(new Settings(), s);
        }

        [Fact]
        public void WrongKindOrBadValues_FallBackToDefault_GoodOnesStillLoad()
        {
            var d = new SaveDocument(SaveModel.CurrentVersion);
            d.SetString("opt/autorun", "maybe");                      // wrong kind → default on
            d.SetBool("opt/music", false);                            // good
            d.SetString("opt/bright", "bright");                      // wrong kind → default
            d.SetDouble("opt/volSfx", double.NaN);                    // NaN → default
            d.SetDouble("opt/volVoice", 0.4);
            d.SetLong("opt/glyphs", 42);                              // unknown enum → Auto
            d.SetLong("opt/bindings", 7);                             // wrong kind → ""
            d.SetBool("opt/calm", true);
            var s = Settings.Read(d);
            Assert.True(s.AutoRun);
            Assert.False(s.Music);
            Assert.Equal(1.0, s.Brightness);
            Assert.Equal(1.0, s.SfxVolume);
            Assert.Equal(0.4, s.VoiceVolume);
            Assert.Equal(GlyphPreference.Auto, s.Glyphs);
            Assert.Equal("", s.BindingOverrides);
            Assert.True(s.Calm);
            Assert.Empty(s.UnknownOptions);                           // a bad known key is not demoted to unknown
        }

        [Fact]
        public void OutOfRangeNumbers_AreClamped()
        {
            var d = new SaveDocument(SaveModel.CurrentVersion);
            d.SetDouble("opt/bright", 9);
            d.SetDouble("opt/volMaster", -3);
            d.SetDouble("opt/volMusic", 1e300);
            d.SetLong("opt/subtitleSize", 99);
            var s = Settings.Read(d);
            Assert.Equal(1.8, s.Brightness);
            Assert.Equal(0.0, s.MasterVolume);
            Assert.Equal(1.0, s.MusicVolume);
            Assert.Equal(TextSize.ExtraLarge, s.SubtitleSize);
            d.SetLong("opt/subtitleSize", -5);
            d.SetLong("opt/glyphs", long.MaxValue);
            s = Settings.Read(d);
            Assert.Equal(TextSize.Small, s.SubtitleSize);
            Assert.Equal(GlyphPreference.Auto, s.Glyphs);
        }

        [Theory]
        [InlineData("")]
        [InlineData("   \n\n")]
        [InlineData("\0\0\0\u0001garbage")]
        [InlineData("{\"json\": true}")]
        [InlineData("calm=1\nversion=1\n")]
        public void GarbageBytes_DoNotThrow_AndLoadNothing(string text)
        {
            // The old settings.cfg text format is not a save: it is not read as options (the slot's defaults apply).
            Assert.False(SaveCodec.TryLoad(System.Text.Encoding.UTF8.GetBytes(text), out _, out _));
        }

        [Fact]
        public void CorruptedBytes_LoadNothing_NotHalfASettings()
        {
            byte[] b = SaveCodec.Encode(new SaveModel { Settings = NonDefault() });
            b[b.Length / 2] ^= 0x5A;
            Assert.False(SaveCodec.TryLoad(b, out _, out _));
            Assert.False(SaveCodec.TryLoad(b.AsSpan(0, b.Length / 3).ToArray(), out _, out _));
        }

        [Fact]
        public void ApplySettings_SavesTheNewOptions_AndCopies()
        {
            var g = Mech.Graph("start", new TestSource("t.a"));
            var store = new MemorySaveStore();
            var svc = new CheckpointService(g, Checkpoint.PrototypeOrder, store);
            var edited = NonDefault();
            svc.ApplySettings(edited);
            edited.MusicVolume = 0.9;                                 // the service holds its own copy
            Assert.Equal(0.123456789, svc.Settings.MusicVolume);
            Assert.True(store.TryLoad(0, out var m));
            AssertSame(NonDefault(), m.Settings);
        }
    }

    public class AudioLevelsTests
    {
        [Fact]
        public void ExposedParameterNames_MatchU16Mixer()
        {
            Assert.Equal(new[] { "Master", "Music", "SFX", "Voice", "Ambience" },
                AudioLevels.All.Select(AudioLevels.ExposedParameter));
        }

        [Theory]
        [InlineData(1.0, 0.0)]
        [InlineData(0.5, -6.0206)]
        [InlineData(0.1, -20.0)]
        [InlineData(0.0, -80.0)]
        [InlineData(1e-9, -80.0)]
        [InlineData(-1.0, -80.0)]
        [InlineData(2.0, 0.0)]
        public void LinearToDecibels(double linear, double db)
        {
            Assert.Equal(db, AudioLevels.LinearToDecibels(linear), 3);
        }

        [Fact]
        public void SoundToggle_MutesSfxVoiceAmbience_NotMusicOrMaster()
        {
            var s = new Settings { Sound = false };
            Assert.Equal(AudioLevels.SilentDb, AudioLevels.Decibels(s, AudioGroup.Sfx));
            Assert.Equal(AudioLevels.SilentDb, AudioLevels.Decibels(s, AudioGroup.Voice));
            Assert.Equal(AudioLevels.SilentDb, AudioLevels.Decibels(s, AudioGroup.Ambience));
            Assert.Equal(0.0, AudioLevels.Decibels(s, AudioGroup.Music));
            Assert.Equal(0.0, AudioLevels.Decibels(s, AudioGroup.Master));
        }

        [Fact]
        public void MusicToggle_MutesOnlyMusic_AndKeepsTheSliderValue()
        {
            var s = new Settings { Music = false, MusicVolume = 0.7 };
            Assert.Equal(0.0, AudioLevels.Linear(s, AudioGroup.Music));
            Assert.Equal(1.0, AudioLevels.Linear(s, AudioGroup.Sfx));
            s.Music = true;
            Assert.Equal(0.7, AudioLevels.Linear(s, AudioGroup.Music));
        }

        [Fact]
        public void Master_IsNotMultipliedIntoChildGroups()
        {
            var s = new Settings { MasterVolume = 0.5, SfxVolume = 0.5 };
            Assert.Equal(0.5, AudioLevels.Linear(s, AudioGroup.Sfx));
            Assert.Equal(0.5, AudioLevels.Linear(s, AudioGroup.Master));
        }
    }
}
