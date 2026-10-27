using System;
using DeadLetter.Core.Options;

namespace DeadLetter.Core.Platform
{
    /// <summary>The button-prompt art set the UI draws.</summary>
    public enum GlyphSet
    {
        Keyboard = 0,
        Xbox = 1,
        PlayStation = 2,
        Switch = 3,
        SteamDeck = 4,
    }

    /// <summary>Which store build is running (chosen by scripting define, see Runtime <c>PlatformServices</c>).</summary>
    public enum PlatformKind
    {
        /// <summary>DRM-free desktop build (Itch), also the editor default.</summary>
        Desktop = 0,
        Steam = 1,
        Switch = 2,
    }

    /// <summary>Coarse device class, from the Input System device the player last used.</summary>
    public enum DeviceKind
    {
        None = 0,
        Keyboard = 1,
        Mouse = 2,
        Gamepad = 3,
        Touch = 4,
    }

    /// <summary>
    /// Engine-free description of an input device: the Runtime fills it from <c>InputDevice.layout</c> and
    /// <c>InputDevice.description</c> (product, manufacturer, interface).
    /// </summary>
    public struct DeviceInfo
    {
        public DeviceKind Kind;
        /// <summary>Input System layout name, e.g. <c>DualSenseGamepadHID</c>, <c>XInputControllerWindows</c>.</summary>
        public string Layout;
        public string Product;
        public string Manufacturer;

        public DeviceInfo(DeviceKind kind, string layout = null, string product = null, string manufacturer = null)
        {
            Kind = kind; Layout = layout; Product = product; Manufacturer = manufacturer;
        }

        public static readonly DeviceInfo None = new DeviceInfo(DeviceKind.None);
    }

    /// <summary>
    /// Picks the glyph set. In order:
    /// <list type="number">
    /// <item>An explicit preference in the options wins.</item>
    /// <item>On Switch, always Switch glyphs (lotcheck: platform-correct button names).</item>
    /// <item>Keyboard or mouse last used → Keyboard.</item>
    /// <item>A gamepad: by brand in layout / product / manufacturer (PlayStation, Nintendo, Xbox). A gamepad on a Steam Deck
    /// that is not a recognised brand (Steam Input presents the Deck's controls as a generic or Xbox-style pad) → Steam Deck.
    /// Any other unrecognised pad → Xbox (the de-facto PC default).</item>
    /// <item>Nothing used yet → the platform default: Switch, Steam Deck, or Keyboard.</item>
    /// </list>
    /// </summary>
    public static class GlyphRules
    {
        public static GlyphSet Select(GlyphPreference preference, DeviceInfo lastUsed, PlatformKind platform, bool onSteamDeck)
        {
            switch (preference)
            {
                case GlyphPreference.Keyboard: return GlyphSet.Keyboard;
                case GlyphPreference.Xbox: return GlyphSet.Xbox;
                case GlyphPreference.PlayStation: return GlyphSet.PlayStation;
                case GlyphPreference.Switch: return GlyphSet.Switch;
                case GlyphPreference.SteamDeck: return GlyphSet.SteamDeck;
            }

            if (platform == PlatformKind.Switch) return GlyphSet.Switch;

            switch (lastUsed.Kind)
            {
                case DeviceKind.Keyboard:
                case DeviceKind.Mouse:
                    return GlyphSet.Keyboard;
                case DeviceKind.Gamepad:
                    return ForGamepad(lastUsed, onSteamDeck);
                default:
                    return onSteamDeck ? GlyphSet.SteamDeck : GlyphSet.Keyboard;
            }
        }

        /// <summary>The glyph set for a gamepad, by brand.</summary>
        public static GlyphSet ForGamepad(DeviceInfo d, bool onSteamDeck)
        {
            if (Has(d, "steam deck") || Has(d, "steamdeck")) return GlyphSet.SteamDeck;
            if (Has(d, "dualsense") || Has(d, "dualshock") || Has(d, "playstation") || Has(d, "sony")
                || Has(d, "ps4") || Has(d, "ps5")) return GlyphSet.PlayStation;
            if (Has(d, "nintendo") || Has(d, "joy-con") || Has(d, "joycon") || Has(d, "switchpro")
                || Has(d, "pro controller") || Has(d, "npad")) return GlyphSet.Switch;
            if (onSteamDeck) return GlyphSet.SteamDeck;
            return GlyphSet.Xbox;
        }

        private static bool Has(DeviceInfo d, string needle)
            => Contains(d.Layout, needle) || Contains(d.Product, needle) || Contains(d.Manufacturer, needle);

        private static bool Contains(string hay, string needle)
            => !string.IsNullOrEmpty(hay) && hay.IndexOf(needle, StringComparison.OrdinalIgnoreCase) >= 0;
    }
}
