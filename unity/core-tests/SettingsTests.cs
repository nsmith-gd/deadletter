using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Threading;
using DeadLetter.Core.Settings;
using Xunit;

namespace DeadLetter.Core.Tests
{
    public class SettingsDefaultsTests
    {
        // OPTS, index.html L8283: { sound: true, music: true, prompts: true, assist: false, calm: false, autorun: true, telemetry: true }
        [Fact]
        public void PrototypeToggles_DefaultAsInOpts()
        {
            var s = new GameSettings();
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
            Assert.False(new GameSettings().Telemetry);
        }

        [Fact]
        public void Brightness_DefaultAndRange_MatchPrototype()
        {
            // L175: range 0.8–1.8, value 1; L8309: exposure = 1.4 × v.
            var s = new GameSettings();
            Assert.Equal(1.0, s.Brightness);
            Assert.Equal(0.8, GameSettings.BrightnessMin);
            Assert.Equal(1.8, GameSettings.BrightnessMax);
            Assert.Equal(1.4, s.Exposure, 12);
        }

        [Fact]
        public void Bloom_CalmIs035_NormalIs055()
        {
            // L8290: bloom.strength = calm ? 0.35 : 0.55
            var s = new GameSettings();
            Assert.Equal(0.55, s.Bloom);
            s.Calm = true;
            Assert.Equal(0.35, s.Bloom);
        }

        [Fact]
        public void NewOptions_HaveNeutralDefaults()
        {
            var s = new GameSettings();
            Assert.Equal(1.0, s.MasterVolume);
            Assert.Equal(1.0, s.MusicVolume);
            Assert.Equal(1.0, s.SfxVolume);
            Assert.Equal(1.0, s.VoiceVolume);
            Assert.Equal(1.0, s.AmbienceVolume);
            Assert.Equal(TextSize.Default, s.TextSize);
            Assert.Equal(1.0, s.TextScale);
            Assert.False(s.TextBackground);
            Assert.False(s.ColourIndependentCues);
            Assert.False(s.ToggleHolds);
            Assert.Equal(GlyphPreference.Auto, s.Glyphs);
            Assert.Equal("", s.BindingOverrides);
            Assert.Equal(GameSettings.CurrentVersion, s.Version);
            Assert.Empty(s.UnknownEntries);
        }

        [Fact]
        public void TextScale_IncreasesWithSize()
        {
            double prev = 0;
            foreach (TextSize t in new[] { TextSize.Small, TextSize.Default, TextSize.Large, TextSize.ExtraLarge })
            {
                double k = GameSettings.TextScaleFor(t);
                Assert.True(k > prev);
                prev = k;
            }
        }

        [Fact]
        public void Sanitise_ClampsAndRepairs()
        {
            var s = new GameSettings
            {
                Brightness = 5, MasterVolume = -1, MusicVolume = double.NaN, SfxVolume = 2,
                TextSize = (TextSize)99, Glyphs = (GlyphPreference)42, BindingOverrides = null,
            };
            s.Sanitise();
            Assert.Equal(1.8, s.Brightness);
            Assert.Equal(0.0, s.MasterVolume);
            Assert.Equal(1.0, s.MusicVolume);
            Assert.Equal(1.0, s.SfxVolume);
            Assert.Equal(TextSize.Default, s.TextSize);
            Assert.Equal(GlyphPreference.Auto, s.Glyphs);
            Assert.Equal("", s.BindingOverrides);
        }

        [Fact]
        public void Clone_IsDeep()
        {
            var a = new GameSettings { Calm = true, MusicVolume = 0.3 };
            a.UnknownEntries.Add(new KeyValuePair<string, string>("x", "1"));
            var b = a.Clone();
            b.Calm = false;
            b.UnknownEntries.Add(new KeyValuePair<string, string>("y", "2"));
            Assert.True(a.Calm);
            Assert.Equal(0.3, b.MusicVolume);
            Assert.Single(a.UnknownEntries);
            Assert.Equal(2, b.UnknownEntries.Count);
        }
    }

    public class SettingsSerializerTests
    {
        private static GameSettings NonDefault()
        {
            return new GameSettings
            {
                AutoRun = false, Sound = false, Music = false, Prompts = false, StuckAssist = true, Calm = true,
                Telemetry = true, Brightness = 1.35, MasterVolume = 0.9, MusicVolume = 0.123456789, SfxVolume = 0,
                VoiceVolume = 0.5, AmbienceVolume = 0.25, TextSize = TextSize.ExtraLarge, TextBackground = true,
                ColourIndependentCues = true, ToggleHolds = true, Glyphs = GlyphPreference.PlayStation,
                BindingOverrides = "{\"bindings\":[{\"action\":\"Gameplay/Jump\",\"id\":\"a=b\",\"path\":\"<Keyboard>/k\"}]}\n{line2}\\end",
            };
        }

        private static void AssertSame(GameSettings a, GameSettings b)
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
            Assert.Equal(a.TextSize, b.TextSize);
            Assert.Equal(a.TextBackground, b.TextBackground);
            Assert.Equal(a.ColourIndependentCues, b.ColourIndependentCues);
            Assert.Equal(a.ToggleHolds, b.ToggleHolds);
            Assert.Equal(a.Glyphs, b.Glyphs);
            Assert.Equal(a.BindingOverrides, b.BindingOverrides);
        }

        [Fact]
        public void RoundTrip_Defaults()
        {
            var d = new GameSettings();
            AssertSame(d, SettingsSerializer.Deserialize(SettingsSerializer.Serialize(d)));
        }

        [Fact]
        public void RoundTrip_EveryFieldChanged_IncludingMultilineBindingJson()
        {
            var a = NonDefault();
            int rejected;
            var b = SettingsSerializer.Deserialize(SettingsSerializer.Serialize(a), out rejected);
            AssertSame(a, b);
            Assert.Equal(0, rejected);
        }

        [Fact]
        public void RoundTrip_Utf8Bytes()
        {
            var a = NonDefault();
            AssertSame(a, SettingsSerializer.DeserializeUtf8(SettingsSerializer.SerializeUtf8(a)));
        }

        [Fact]
        public void Serialize_IsStable_SameInputSameText()
        {
            var a = NonDefault();
            string once = SettingsSerializer.Serialize(a);
            string twice = SettingsSerializer.Serialize(SettingsSerializer.Deserialize(once));
            Assert.Equal(once, twice);
        }

        [Fact]
        public void Serialize_OneLinePerKey_NoRawNewlinesInValues()
        {
            string text = SettingsSerializer.Serialize(NonDefault());
            var lines = text.Split('\n').Where(l => l.Length > 0 && l[0] != '#').ToList();
            Assert.Equal(SettingsSerializer.KnownKeys.Count() + 1, lines.Count);   // + version
            Assert.StartsWith("version=", lines[0]);
            Assert.All(lines, l => Assert.Contains("=", l));
        }

        [Fact]
        public void Serialize_IsCultureInvariant()
        {
            var prev = Thread.CurrentThread.CurrentCulture;
            try
            {
                Thread.CurrentThread.CurrentCulture = new CultureInfo("de-DE");
                string text = SettingsSerializer.Serialize(new GameSettings { Brightness = 1.25 });
                Assert.Contains("brightness=1.25\n", text);
                Assert.Equal(1.25, SettingsSerializer.Deserialize(text).Brightness);
            }
            finally { Thread.CurrentThread.CurrentCulture = prev; }
        }

        [Fact]
        public void BoolsWrittenAsOneZero_LikeThePrototypesLocalStorage()
        {
            // L8285: localStorage.setItem('dl01-' + name, value ? '1' : '0')
            string text = SettingsSerializer.Serialize(new GameSettings());
            Assert.Contains("autoRun=1\n", text);
            Assert.Contains("calm=0\n", text);
        }

        [Fact]
        public void UnknownKeys_ArePreservedInOrder_AndWrittenBack()
        {
            string text = "version=1\nfuture.hdr=1\ncalm=1\nfuture.fov=72.5\nfuture.note=a\\nb\n";
            var s = SettingsSerializer.Deserialize(text);
            Assert.True(s.Calm);
            Assert.Equal(new[] { "future.hdr", "future.fov", "future.note" }, s.UnknownEntries.Select(e => e.Key));
            Assert.Equal("a\nb", s.UnknownEntries[2].Value);

            string written = SettingsSerializer.Serialize(s);
            Assert.Contains("future.hdr=1\n", written);
            Assert.Contains("future.fov=72.5\n", written);
            Assert.Contains("future.note=a\\nb\n", written);
            Assert.True(written.IndexOf("future.hdr") < written.IndexOf("future.fov"));
            // and again
            var again = SettingsSerializer.Deserialize(written);
            Assert.Equal(s.UnknownEntries, again.UnknownEntries);
        }

        [Fact]
        public void UnknownKey_DuplicateKeepsLastValue_FirstPosition()
        {
            var s = SettingsSerializer.Deserialize("a.x=1\nb.y=2\na.x=3\n");
            Assert.Equal(2, s.UnknownEntries.Count);
            Assert.Equal("a.x", s.UnknownEntries[0].Key);
            Assert.Equal("3", s.UnknownEntries[0].Value);
        }

        [Fact]
        public void NewerVersion_IsKeptOnWrite()
        {
            var s = SettingsSerializer.Deserialize("version=7\ncalm=1\n");
            Assert.Equal(7, s.Version);
            Assert.Contains("version=7\n", SettingsSerializer.Serialize(s));
        }

        [Fact]
        public void MissingVersion_TreatedAsCurrent()
        {
            var s = SettingsSerializer.Deserialize("music=0\n");
            Assert.False(s.Music);
            Assert.Equal(GameSettings.CurrentVersion, s.Version);
        }

        [Theory]
        [InlineData(null)]
        [InlineData("")]
        [InlineData("   \n\n")]
        [InlineData("\0\0\0\u0001garbage")]
        [InlineData("{\"json\": true}")]
        [InlineData("=====\n=\n")]
        public void EmptyOrGarbage_GivesDefaults(string text)
        {
            var s = SettingsSerializer.Deserialize(text);
            var d = new GameSettings();
            Assert.Equal(d.AutoRun, s.AutoRun);
            Assert.Equal(d.Brightness, s.Brightness);
            Assert.Equal(d.Calm, s.Calm);
            Assert.Empty(s.UnknownEntries);
        }

        [Fact]
        public void BadValues_FallBackToDefault_GoodOnesStillLoad()
        {
            string text = "autoRun=maybe\nmusic=0\nbrightness=bright\nvolume.sfx=NaN\nvolume.voice=0.4\ntext.size=huge\ninput.glyphs=atari\ncalm=yes\n";
            int rejected;
            var s = SettingsSerializer.Deserialize(text, out rejected);
            Assert.True(s.AutoRun);                         // bad → default on
            Assert.False(s.Music);                          // good
            Assert.Equal(1.0, s.Brightness);                // bad → default
            Assert.Equal(1.0, s.SfxVolume);                 // NaN rejected
            Assert.Equal(0.4, s.VoiceVolume);
            Assert.Equal(TextSize.Default, s.TextSize);
            Assert.Equal(GlyphPreference.Auto, s.Glyphs);
            Assert.True(s.Calm);
            Assert.Equal(5, rejected);
            Assert.Empty(s.UnknownEntries);                 // a bad known key is not demoted to unknown
        }

        [Fact]
        public void OutOfRangeNumbers_AreClamped()
        {
            var s = SettingsSerializer.Deserialize("brightness=9\nvolume.master=-3\nvolume.music=1e300\n");
            Assert.Equal(1.8, s.Brightness);
            Assert.Equal(0.0, s.MasterVolume);
            Assert.Equal(1.0, s.MusicVolume);
        }

        [Fact]
        public void CorruptLines_AreDropped_NotPreserved()
        {
            int rejected;
            var s = SettingsSerializer.Deserialize("no equals sign\n=novalue\nbad key=1\nk\u0001=2\nok.key=v\u0002x\ncalm=1\n", out rejected);
            Assert.True(s.Calm);
            Assert.Empty(s.UnknownEntries);
            Assert.Equal(5, rejected);
        }

        [Fact]
        public void Tolerates_CrLf_Bom_Comments_Whitespace_AndTruncation()
        {
            var s = SettingsSerializer.Deserialize("﻿# hand edited\r\n  calm = 1 \r\nsound=0\r\nbrightn");
            Assert.True(s.Calm);
            Assert.False(s.Sound);
            Assert.Equal(1.0, s.Brightness);
        }

        [Fact]
        public void BoolParsing_AcceptsCommonSpellings()
        {
            foreach (var t in new[] { "1", "true", "TRUE", "yes", "on" })
                Assert.True(SettingsSerializer.Deserialize("music=0\nmusic=" + t).Music);
            foreach (var f in new[] { "0", "false", "No", "off" })
                Assert.False(SettingsSerializer.Deserialize("music=" + f).Music);
        }

        [Fact]
        public void ValueMayContainEquals()
        {
            var s = SettingsSerializer.Deserialize("input.bindings=a=b=c\n");
            Assert.Equal("a=b=c", s.BindingOverrides);
        }

        [Fact]
        public void Escape_Unescape_RoundTrip()
        {
            foreach (var v in new[] { "", "plain", "a\\b", "line1\nline2", "cr\r\nlf", "\\n literal", "trailing\\" })
                Assert.Equal(v, SettingsSerializer.Unescape(SettingsSerializer.Escape(v)));
        }

        [Fact]
        public void UnknownEntry_ShadowingAKnownKey_IsNotWrittenTwice()
        {
            var s = new GameSettings();
            s.UnknownEntries.Add(new KeyValuePair<string, string>("calm", "1"));
            s.UnknownEntries.Add(new KeyValuePair<string, string>("version", "99"));
            string text = SettingsSerializer.Serialize(s);
            Assert.Equal(1, CountOccurrences(text, "\ncalm="));
            Assert.Equal(1, CountOccurrences(text, "version="));
            Assert.False(SettingsSerializer.Deserialize(text).Calm);
        }

        [Fact]
        public void KnownKeys_AreUniqueAndValid()
        {
            var keys = SettingsSerializer.KnownKeys.ToList();
            Assert.Equal(keys.Count, keys.Distinct().Count());
            Assert.All(keys, k => Assert.True(SettingsSerializer.IsValidKey(k)));
            Assert.DoesNotContain(SettingsSerializer.VersionKey, keys);
        }

        private static int CountOccurrences(string hay, string needle)
        {
            int n = 0, i = 0;
            while ((i = hay.IndexOf(needle, i, StringComparison.Ordinal)) >= 0) { n++; i += needle.Length; }
            return n;
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
            var s = new GameSettings { Sound = false };
            Assert.Equal(AudioLevels.SilentDb, AudioLevels.Decibels(s, AudioGroup.Sfx));
            Assert.Equal(AudioLevels.SilentDb, AudioLevels.Decibels(s, AudioGroup.Voice));
            Assert.Equal(AudioLevels.SilentDb, AudioLevels.Decibels(s, AudioGroup.Ambience));
            Assert.Equal(0.0, AudioLevels.Decibels(s, AudioGroup.Music));
            Assert.Equal(0.0, AudioLevels.Decibels(s, AudioGroup.Master));
        }

        [Fact]
        public void MusicToggle_MutesOnlyMusic_AndKeepsTheSliderValue()
        {
            var s = new GameSettings { Music = false, MusicVolume = 0.7 };
            Assert.Equal(0.0, AudioLevels.Linear(s, AudioGroup.Music));
            Assert.Equal(1.0, AudioLevels.Linear(s, AudioGroup.Sfx));
            s.Music = true;
            Assert.Equal(0.7, AudioLevels.Linear(s, AudioGroup.Music));
        }

        [Fact]
        public void Master_IsNotMultipliedIntoChildGroups()
        {
            var s = new GameSettings { MasterVolume = 0.5, SfxVolume = 0.5 };
            Assert.Equal(0.5, AudioLevels.Linear(s, AudioGroup.Sfx));
            Assert.Equal(0.5, AudioLevels.Linear(s, AudioGroup.Master));
        }
    }
}
