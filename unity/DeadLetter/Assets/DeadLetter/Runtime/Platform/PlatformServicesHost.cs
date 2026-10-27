using System;
using DeadLetter.Core.Platform;
using DeadLetter.Core.Options;
using DeadLetter.Runtime.Camera;
using DeadLetter.Runtime.Settings;
using UnityEngine;

namespace DeadLetter.Runtime.Platform
{
    /// <summary>
    /// Starts the platform services, pumps them, and turns the platform's interruptions into pauses. Put one in
    /// <c>DL_Persistent</c> (never unloaded) next to <see cref="SettingsStore"/>.
    /// <para>
    /// Pausing: <see cref="Pause"/> (Core <see cref="PauseGate"/>) collects the player's pause (D-17's Pause action),
    /// the overlay (Steam overlay, Switch HOME) and focus loss. While anything holds it, <c>Time.timeScale</c> is 0 (D-17's
    /// Core tick runs on <c>Time.deltaTime</c>, so it stops) and the directed-moment player and its music clock are paused.
    /// The pause card UI (U-17 UI Toolkit screen, not built yet) shows while <see cref="PauseGate.ShowPauseCard"/> and
    /// calls <c>Pause.SetPlayer(false)</c> on Resume.
    /// </para>
    /// </summary>
    [DefaultExecutionOrder(-1000)]
    [DisallowMultipleComponent]
    public sealed class PlatformServicesHost : MonoBehaviour
    {
        [Tooltip("D-17: its Pause action toggles the pause card.")]
        [SerializeField] private D17Controller player;
        [Tooltip("Paused and resumed with the game so a moment's cue and Timeline hold still under the pause card.")]
        [SerializeField] private DirectedMomentPlayer moments;
        [Tooltip("Pause when the window loses focus (desktop). Always on for Switch.")]
        [SerializeField] private bool pauseOnFocusLoss = true;
        [Tooltip("Drive Time.timeScale from the pause state.")]
        [SerializeField] private bool driveTimeScale = true;

        private static PlatformServicesHost _instance;
        private readonly PauseGate _pause = new PauseGate();
        private GlyphTracker _glyphs;
        private IPlatformServices _services;

        public static PlatformServicesHost Instance => _instance;
        public static IPlatformServices Services => PlatformServices.Current;

        public PauseGate Pause => _pause;
        public GlyphTracker Glyphs => _glyphs;

        /// <summary>True while the game is in play (not on the title or an end card). Title flow (U-17 UI) sets it.</summary>
        public Func<bool> InPlay { get; set; } = () => true;

        private void Awake()
        {
            if (_instance != null && _instance != this)
            {
                Debug.LogWarning("PlatformServicesHost: a second host was found; disabling it.", this);
                enabled = false;
                return;
            }
            _instance = this;

            IPlatformServices services = _services = PlatformServices.Initialize();
            services.OverlayActiveChanged += OnOverlay;
            _pause.PauseOnFocusLoss = pauseOnFocusLoss || services.Kind == PlatformKind.Switch;
            _pause.Changed += OnPauseChanged;

            _glyphs = new GlyphTracker(services.Kind, services.IsSteamDeck);
            SettingsStore.Applied += OnSettingsApplied;
            if (SettingsStore.Loaded) OnSettingsApplied(SettingsStore.Current);

            if (player != null) player.PauseRequested += OnPauseRequested;
        }

        private void OnDestroy()
        {
            if (_instance != this) return;
            SettingsStore.Applied -= OnSettingsApplied;
            if (player != null) player.PauseRequested -= OnPauseRequested;
            if (_services != null) _services.OverlayActiveChanged -= OnOverlay;
            _glyphs?.Dispose();
            _glyphs = null;
            PlatformServices.Shutdown();
            if (driveTimeScale) Time.timeScale = 1f;
            _instance = null;
        }

        private void Update() => _services?.Tick();

        private void OnApplicationFocus(bool hasFocus) => _pause.OnFocus(hasFocus, InPlay());

        private void OnApplicationQuit() => PlatformServices.Shutdown();

        private void OnOverlay(bool active) => _pause.OnOverlay(active, InPlay());

        private void OnPauseRequested()
        {
            if (InPlay()) _pause.TogglePlayer();
        }

        private void OnSettingsApplied(GameSettings s) => _glyphs?.SetPreference(s.Glyphs);

        private void OnPauseChanged()
        {
            bool paused = _pause.IsPaused;
            if (driveTimeScale) Time.timeScale = paused ? 0f : 1f;
            if (moments != null) moments.SetPaused(paused);
        }
    }
}
