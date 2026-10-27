using System.Linq;
using DeadLetter.Core.Platform;
using DeadLetter.Core.Options;
using Xunit;

namespace DeadLetter.Core.Tests
{
    public class GlyphRulesTests
    {
        private static readonly DeviceInfo Keyboard = new DeviceInfo(DeviceKind.Keyboard, "Keyboard");
        private static readonly DeviceInfo Mouse = new DeviceInfo(DeviceKind.Mouse, "Mouse");
        private static readonly DeviceInfo XInput = new DeviceInfo(DeviceKind.Gamepad, "XInputControllerWindows", "Controller (Xbox One For Windows)", "");
        private static readonly DeviceInfo DualSense = new DeviceInfo(DeviceKind.Gamepad, "DualSenseGamepadHID", "DualSense Wireless Controller", "Sony Interactive Entertainment");
        private static readonly DeviceInfo DualShock = new DeviceInfo(DeviceKind.Gamepad, "DualShock4GamepadHID", "Wireless Controller", "Sony Computer Entertainment");
        private static readonly DeviceInfo SwitchPro = new DeviceInfo(DeviceKind.Gamepad, "SwitchProControllerHID", "Pro Controller", "Nintendo Co., Ltd.");
        private static readonly DeviceInfo Generic = new DeviceInfo(DeviceKind.Gamepad, "Gamepad", "USB Gamepad", "Generic");
        private static readonly DeviceInfo SteamVirtual = new DeviceInfo(DeviceKind.Gamepad, "XInputControllerWindows", "Steam Virtual Gamepad", "Valve");

        [Theory]
        [InlineData(GlyphPreference.Keyboard, GlyphSet.Keyboard)]
        [InlineData(GlyphPreference.Xbox, GlyphSet.Xbox)]
        [InlineData(GlyphPreference.PlayStation, GlyphSet.PlayStation)]
        [InlineData(GlyphPreference.Switch, GlyphSet.Switch)]
        [InlineData(GlyphPreference.SteamDeck, GlyphSet.SteamDeck)]
        public void ExplicitPreference_Wins_EvenOnSwitchOrDeck(GlyphPreference pref, GlyphSet expected)
        {
            Assert.Equal(expected, GlyphRules.Select(pref, DualSense, PlatformKind.Switch, true));
            Assert.Equal(expected, GlyphRules.Select(pref, Keyboard, PlatformKind.Steam, false));
        }

        [Fact]
        public void Auto_OnSwitch_AlwaysSwitch()
        {
            Assert.Equal(GlyphSet.Switch, GlyphRules.Select(GlyphPreference.Auto, DeviceInfo.None, PlatformKind.Switch, false));
            Assert.Equal(GlyphSet.Switch, GlyphRules.Select(GlyphPreference.Auto, Keyboard, PlatformKind.Switch, false));
            Assert.Equal(GlyphSet.Switch, GlyphRules.Select(GlyphPreference.Auto, XInput, PlatformKind.Switch, false));
        }

        [Fact]
        public void Auto_KeyboardOrMouse_ShowsKeys_EvenOnDeck()
        {
            Assert.Equal(GlyphSet.Keyboard, GlyphRules.Select(GlyphPreference.Auto, Keyboard, PlatformKind.Desktop, false));
            Assert.Equal(GlyphSet.Keyboard, GlyphRules.Select(GlyphPreference.Auto, Mouse, PlatformKind.Steam, false));
            Assert.Equal(GlyphSet.Keyboard, GlyphRules.Select(GlyphPreference.Auto, Keyboard, PlatformKind.Steam, true));
        }

        [Fact]
        public void Auto_GamepadBrands()
        {
            Assert.Equal(GlyphSet.Xbox, GlyphRules.Select(GlyphPreference.Auto, XInput, PlatformKind.Steam, false));
            Assert.Equal(GlyphSet.PlayStation, GlyphRules.Select(GlyphPreference.Auto, DualSense, PlatformKind.Steam, false));
            Assert.Equal(GlyphSet.PlayStation, GlyphRules.Select(GlyphPreference.Auto, DualShock, PlatformKind.Desktop, false));
            Assert.Equal(GlyphSet.Switch, GlyphRules.Select(GlyphPreference.Auto, SwitchPro, PlatformKind.Desktop, false));
        }

        [Fact]
        public void Auto_UnknownPad_OffDeck_IsXbox()
        {
            Assert.Equal(GlyphSet.Xbox, GlyphRules.Select(GlyphPreference.Auto, Generic, PlatformKind.Desktop, false));
        }

        [Fact]
        public void Auto_OnDeck_XboxStylePadFromSteamInput_IsDeck_ButBrandedPadKeepsBrand()
        {
            Assert.Equal(GlyphSet.SteamDeck, GlyphRules.Select(GlyphPreference.Auto, SteamVirtual, PlatformKind.Steam, true));
            Assert.Equal(GlyphSet.SteamDeck, GlyphRules.Select(GlyphPreference.Auto, Generic, PlatformKind.Steam, true));
            Assert.Equal(GlyphSet.PlayStation, GlyphRules.Select(GlyphPreference.Auto, DualSense, PlatformKind.Steam, true));
        }

        [Fact]
        public void Auto_NothingUsedYet_PlatformDefault()
        {
            Assert.Equal(GlyphSet.Keyboard, GlyphRules.Select(GlyphPreference.Auto, DeviceInfo.None, PlatformKind.Desktop, false));
            Assert.Equal(GlyphSet.SteamDeck, GlyphRules.Select(GlyphPreference.Auto, DeviceInfo.None, PlatformKind.Steam, true));
            Assert.Equal(GlyphSet.Keyboard, GlyphRules.Select(GlyphPreference.Auto, new DeviceInfo(DeviceKind.Touch), PlatformKind.Desktop, false));
        }

        [Fact]
        public void Gamepad_NamedSteamDeck_IsDeck_AnywhereAndNullFieldsAreSafe()
        {
            var deck = new DeviceInfo(DeviceKind.Gamepad, null, "Steam Deck", null);
            Assert.Equal(GlyphSet.SteamDeck, GlyphRules.ForGamepad(deck, false));
            Assert.Equal(GlyphSet.Xbox, GlyphRules.ForGamepad(new DeviceInfo(DeviceKind.Gamepad), false));
        }
    }

    public class PauseGateTests
    {
        [Fact]
        public void PlayerToggle_PausesAndResumes()
        {
            var g = new PauseGate();
            int changes = 0;
            g.Changed += () => changes++;
            g.TogglePlayer();
            Assert.True(g.IsPaused);
            Assert.True(g.ShowPauseCard);
            g.TogglePlayer();
            Assert.False(g.IsPaused);
            Assert.Equal(2, changes);
        }

        [Fact]
        public void OverlayDuringPlay_LeavesPlayerOnPauseCardWhenItCloses()
        {
            var g = new PauseGate();
            g.OnOverlay(true, inPlay: true);
            Assert.True(g.IsPaused);
            g.OnOverlay(false, inPlay: true);
            Assert.True(g.IsPaused);              // no surprise un-pause
            Assert.True(g.ShowPauseCard);
            g.TogglePlayer();
            Assert.False(g.IsPaused);
        }

        [Fact]
        public void OverlayOutsidePlay_DoesNotRaiseThePauseCard()
        {
            var g = new PauseGate();
            g.OnOverlay(true, inPlay: false);
            Assert.True(g.IsPaused);
            Assert.False(g.ShowPauseCard);
            g.OnOverlay(false, inPlay: false);
            Assert.False(g.IsPaused);
        }

        [Fact]
        public void ResumingWhileOverlayUp_StaysPaused()
        {
            var g = new PauseGate();
            g.OnOverlay(true, inPlay: true);
            g.SetPlayer(false);
            Assert.True(g.IsPaused);
            Assert.Equal(PauseReason.Overlay, g.Held);
        }

        [Fact]
        public void FocusLoss_RespectsOption()
        {
            var g = new PauseGate { PauseOnFocusLoss = false };
            g.OnFocus(false, inPlay: true);
            Assert.False(g.IsPaused);
            g.PauseOnFocusLoss = true;
            g.OnFocus(false, inPlay: true);
            Assert.Equal(PauseReason.Focus | PauseReason.Player, g.Held);
            g.OnFocus(true, inPlay: true);
            Assert.Equal(PauseReason.Player, g.Held);
        }
    }

    public class PlatformServicesTests
    {
        [Fact]
        public void NullServices_AreSafeNoOps()
        {
            IPlatformServices p = new NullPlatformServices();
            Assert.Equal(PlatformKind.Desktop, p.Kind);
            Assert.False(p.IsReady);
            Assert.True(p.Initialize());
            Assert.True(p.IsReady);
            Assert.False(p.UnlockAchievement("DL_ANY"));
            Assert.False(p.ClearAchievement("DL_ANY"));
            Assert.False(p.SetRichPresence("steam_display", "#Status"));
            Assert.Null(p.CloudSync);
            Assert.False(p.IsSteamDeck);
            p.OverlayActiveChanged += _ => { };
            p.ClearRichPresence();
            p.Tick();
            p.Shutdown();
            Assert.False(p.IsReady);
        }

        [Fact]
        public void AchievementCatalog_IdsUniqueAndValid()
        {
            var ids = Achievements.All.Select(a => a.Id).ToList();
            Assert.Equal(ids.Count, ids.Distinct().Count());
            Assert.All(ids, id => Assert.True(Achievements.IsValidId(id), id));
            Assert.False(Achievements.IsKnown("DL_NOT_A_REAL_ONE"));
            Assert.Null(Achievements.Find(null));
        }

        [Theory]
        [InlineData("DL_FOUND_ALL_LETTERS", true)]
        [InlineData("DL_1", true)]
        [InlineData("dl_lower", false)]
        [InlineData("1_STARTS_WITH_DIGIT", false)]
        [InlineData("DL-DASH", false)]
        [InlineData("DL", false)]
        public void AchievementIdRule(string id, bool valid)
        {
            Assert.Equal(valid, Achievements.IsValidId(id));
        }
    }
}
