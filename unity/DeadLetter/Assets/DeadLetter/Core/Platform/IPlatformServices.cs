using System;

namespace DeadLetter.Core.Platform
{
    /// <summary>
    /// What the game asks of the store / console layer (port_architecture §3 <c>Platform/</c>, task U-17). One
    /// implementation per store, chosen at build time by scripting define (Runtime <c>PlatformServices.Create</c>):
    /// Steam (<c>DL_STEAM</c>), Switch (<c>UNITY_SWITCH</c>, stub), otherwise the DRM-free desktop build (Itch, no-ops).
    /// <para>
    /// Game code calls these unconditionally; an implementation that has no such feature does nothing and returns false.
    /// Every call is main-thread only.
    /// </para>
    /// </summary>
    public interface IPlatformServices
    {
        PlatformKind Kind { get; }

        /// <summary>Short name for logs ("Steam", "Itch", "Switch").</summary>
        string Name { get; }

        /// <summary>True once <see cref="Initialize"/> succeeded and before <see cref="Shutdown"/>.</summary>
        bool IsReady { get; }

        /// <summary>Running on Steam Deck hardware (Steam only; false elsewhere).</summary>
        bool IsSteamDeck { get; }

        /// <summary>Start the platform SDK. False = unavailable; the game carries on with the no-op behaviour.</summary>
        bool Initialize();

        /// <summary>Pump platform callbacks. Call once per rendered frame.</summary>
        void Tick();

        void Shutdown();

        /// <summary>Unlock achievement <paramref name="id"/> (an <see cref="Achievements"/> API name) and store it.</summary>
        bool UnlockAchievement(string id);

        /// <summary>Re-lock an achievement (debug / test builds only).</summary>
        bool ClearAchievement(string id);

        /// <summary>Set one rich-presence key. On Steam the visible line is <c>steam_display</c> (a localisation token).</summary>
        bool SetRichPresence(string key, string value);

        void ClearRichPresence();

        /// <summary>
        /// The platform overlay (Steam overlay, Switch HOME menu / applet) opened (true) or closed (false). The game
        /// pauses on open and stays paused on close (the player resumes): see <see cref="PauseGate"/>.
        /// </summary>
        event Action<bool> OverlayActiveChanged;

        /// <summary>Cloud save hook, or null when the platform has none (Itch).</summary>
        ICloudSync CloudSync { get; }
    }
}
