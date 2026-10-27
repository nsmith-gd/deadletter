using System;

namespace DeadLetter.Core.Platform
{
    /// <summary>
    /// The platform with no services: achievements, rich presence and cloud are no-ops that return false, and the overlay
    /// never opens. The DRM-free desktop build (Itch) and the editor use it (Runtime <c>ItchPlatformServices</c>), and
    /// tests use it as the default.
    /// </summary>
    public class NullPlatformServices : IPlatformServices
    {
        private bool _ready;

        public virtual PlatformKind Kind => PlatformKind.Desktop;
        public virtual string Name => "None";
        public bool IsReady => _ready;
        public virtual bool IsSteamDeck => false;
        public virtual ICloudSync CloudSync => null;

        // Never raised: there is no overlay. The explicit accessors avoid an "event never used" warning.
        public event Action<bool> OverlayActiveChanged { add { } remove { } }

        public virtual bool Initialize() { _ready = true; return true; }
        public virtual void Tick() { }
        public virtual void Shutdown() { _ready = false; }
        public virtual bool UnlockAchievement(string id) => false;
        public virtual bool ClearAchievement(string id) => false;
        public virtual bool SetRichPresence(string key, string value) => false;
        public virtual void ClearRichPresence() { }
    }
}
