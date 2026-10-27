#if DL_STEAM && UNITY_STANDALONE
// Compiled only for Steam builds (BuildScripts adds DL_STEAM) on standalone targets, where Steamworks.NET defines its
// types. Needs the Steamworks.NET package and the "com.rlabrecque.steamworks.net" reference in DeadLetter.Runtime.asmdef
// (see unity/README.md, "Platforms and settings (U-17)").
using System;
using DeadLetter.Core.Platform;
using Steamworks;
using UnityEngine;

namespace DeadLetter.Runtime.Platform
{
    /// <summary>
    /// Steam via Steamworks.NET: init (with the restart-through-Steam check in players), achievements, rich presence,
    /// the overlay callback (the game pauses when it opens), Steam Deck detection and Steam Remote Storage as
    /// <see cref="ICloudSync"/>. Modelled on Steamworks.NET's SteamManager, without the MonoBehaviour: the
    /// <see cref="PlatformServicesHost"/> calls <see cref="Tick"/> every frame and <see cref="Shutdown"/> on quit.
    /// </summary>
    public sealed class SteamPlatformServices : IPlatformServices
    {
        /// <summary>
        /// The Steam App ID. <b>Placeholder</b>: 0 skips <c>RestartAppIfNecessary</c>. The director sets the real ID here
        /// (it is not secret, but none exists yet). The editor and local test builds read it from <c>steam_appid.txt</c>.
        /// </summary>
        public const uint AppId = 0;

        private bool _ready, _deck;
        private Callback<GameOverlayActivated_t> _overlay;
        private SteamCloudSync _cloud;

        public PlatformKind Kind => PlatformKind.Steam;
        public string Name => "Steam";
        public bool IsReady => _ready;
        public bool IsSteamDeck => _deck;
        public ICloudSync CloudSync => _ready ? _cloud : null;
        public event Action<bool> OverlayActiveChanged;

        public bool Initialize()
        {
            if (_ready) return true;

            if (!Packsize.Test())
            {
                Debug.LogError("Steam: Packsize test failed; the wrong Steamworks.NET binaries for this platform.");
                return false;
            }
            if (!DllCheck.Test())
            {
                Debug.LogError("Steam: DllCheck failed; steam_api is missing or the wrong version.");
                return false;
            }

#if !UNITY_EDITOR
            try
            {
                // Launched outside Steam: Steam relaunches the game through itself and this copy quits.
                if (AppId != 0 && SteamAPI.RestartAppIfNecessary(new AppId_t(AppId)))
                {
                    Application.Quit();
                    return false;
                }
            }
            catch (DllNotFoundException e)
            {
                Debug.LogError("Steam: steam_api native library not found. " + e.Message);
                return false;
            }
#endif

            bool ok;
            try { ok = SteamAPI.Init(); }
            catch (DllNotFoundException e)
            {
                Debug.LogError("Steam: steam_api native library not found. " + e.Message);
                return false;
            }
            if (!ok)
            {
                Debug.LogWarning("Steam: SteamAPI.Init failed (Steam not running, or no steam_appid.txt next to the editor / exe).");
                return false;
            }

            _ready = true;
            _overlay = Callback<GameOverlayActivated_t>.Create(OnOverlayActivated);
            try { _deck = SteamUtils.IsSteamRunningOnSteamDeck(); }
            catch (Exception) { _deck = false; }
            _deck = _deck || PlatformServices.SteamDeckFromEnvironment();
            _cloud = new SteamCloudSync();
            return true;
        }

        public void Tick()
        {
            if (_ready) SteamAPI.RunCallbacks();
        }

        public void Shutdown()
        {
            if (!_ready) return;
            _ready = false;
            if (_overlay != null) { _overlay.Dispose(); _overlay = null; }
            SteamAPI.Shutdown();
        }

        public bool UnlockAchievement(string id)
        {
            if (!_ready || string.IsNullOrEmpty(id)) return false;
            if (!Achievements.IsKnown(id)) Debug.LogWarning($"Steam: achievement '{id}' is not in the Core catalog.");
            // Steam SDK 1.61+ syncs the user's stats at startup itself (RequestCurrentStats is gone). With an older SDK
            // in the package, call SteamUserStats.RequestCurrentStats() after Init and wait for UserStatsReceived_t.
            if (!SteamUserStats.SetAchievement(id)) return false;
            return SteamUserStats.StoreStats();
        }

        public bool ClearAchievement(string id)
        {
            if (!_ready || string.IsNullOrEmpty(id)) return false;
            if (!SteamUserStats.ClearAchievement(id)) return false;
            return SteamUserStats.StoreStats();
        }

        public bool SetRichPresence(string key, string value)
        {
            if (!_ready || string.IsNullOrEmpty(key)) return false;
            return SteamFriends.SetRichPresence(key, value ?? "");
        }

        public void ClearRichPresence()
        {
            if (_ready) SteamFriends.ClearRichPresence();
        }

        private void OnOverlayActivated(GameOverlayActivated_t e)
        {
            OverlayActiveChanged?.Invoke(e.m_bActive != 0);
        }

        /// <summary>Steam Remote Storage, whole files. (Steam Auto-Cloud needs no code; use one or the other.)</summary>
        private sealed class SteamCloudSync : ICloudSync
        {
            public bool IsAvailable => SteamRemoteStorage.IsCloudEnabledForAccount() && SteamRemoteStorage.IsCloudEnabledForApp();

            public bool Exists(string name) => IsAvailable && SteamRemoteStorage.FileExists(name);

            public bool TryRead(string name, out byte[] data)
            {
                data = null;
                if (!Exists(name)) return false;
                int size = SteamRemoteStorage.GetFileSize(name);
                if (size <= 0) return false;
                var buffer = new byte[size];
                int read = SteamRemoteStorage.FileRead(name, buffer, size);
                if (read != size) return false;
                data = buffer;
                return true;
            }

            public bool Write(string name, byte[] data)
            {
                if (!IsAvailable || data == null) return false;
                return SteamRemoteStorage.FileWrite(name, data, data.Length);
            }

            public bool Delete(string name) => IsAvailable && SteamRemoteStorage.FileDelete(name);
        }
    }
}
#endif
