using System;
using DeadLetter.Core.Platform;
using UnityEngine.InputSystem;

namespace DeadLetter.Runtime.Platform
{
    /// <summary>
    /// Watches which device the player last used (any performed Input System action) and keeps the glyph set the UI
    /// should draw, by <see cref="GlyphRules"/>. Owned by <see cref="PlatformServicesHost"/>; UI reads
    /// <see cref="Current"/> and listens to <see cref="Changed"/>.
    /// </summary>
    public sealed class GlyphTracker : IDisposable
    {
        private DeviceInfo _last = DeviceInfo.None;
        private GlyphPreference _preference = GlyphPreference.Auto;
        private readonly PlatformKind _platform;
        private readonly bool _deck;

        public GlyphSet Current { get; private set; }
        public event Action<GlyphSet> Changed;

        public GlyphTracker(PlatformKind platform, bool onSteamDeck)
        {
            _platform = platform;
            _deck = onSteamDeck;
            Current = GlyphRules.Select(_preference, _last, _platform, _deck);
            InputSystem.onActionChange += OnActionChange;
        }

        public void Dispose()
        {
            InputSystem.onActionChange -= OnActionChange;
        }

        /// <summary>The options' glyph preference changed (SettingsStore.Applied).</summary>
        public void SetPreference(GlyphPreference preference)
        {
            _preference = preference;
            Recompute();
        }

        private void OnActionChange(object obj, InputActionChange change)
        {
            if (change != InputActionChange.ActionPerformed) return;
            var action = obj as InputAction;
            InputDevice device = action?.activeControl?.device;
            if (device == null) return;
            DeviceInfo info = Describe(device);
            if (info.Kind == _last.Kind && info.Layout == _last.Layout && info.Product == _last.Product) return;
            _last = info;
            Recompute();
        }

        public static DeviceInfo Describe(InputDevice device)
        {
            DeviceKind kind =
                device is Keyboard ? DeviceKind.Keyboard :
                device is Mouse ? DeviceKind.Mouse :
                device is Gamepad ? DeviceKind.Gamepad :
                device is Touchscreen ? DeviceKind.Touch :
                DeviceKind.None;
            return new DeviceInfo(kind, device.layout, device.description.product, device.description.manufacturer);
        }

        private void Recompute()
        {
            GlyphSet next = GlyphRules.Select(_preference, _last, _platform, _deck);
            if (next == Current) return;
            Current = next;
            Changed?.Invoke(next);
        }
    }
}
