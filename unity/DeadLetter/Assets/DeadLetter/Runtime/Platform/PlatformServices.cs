using System;
using DeadLetter.Core.Platform;
using UnityEngine;

namespace DeadLetter.Runtime.Platform
{
    /// <summary>
    /// Chooses the store layer at compile time:
    /// <list type="bullet">
    /// <item><c>DL_STEAM</c> on a standalone target → <see cref="SteamPlatformServices"/> (needs the Steamworks.NET package).</item>
    /// <item><c>UNITY_SWITCH</c> → <see cref="SwitchPlatformServices"/> (stub until the NDA SDK work is done).</item>
    /// <item>anything else (Itch, editor without <c>DL_STEAM</c>) → <see cref="ItchPlatformServices"/> (no-ops).</item>
    /// </list>
    /// <c>BuildScripts</c> adds <c>DL_STEAM</c> to the Steam builds only (<c>BuildPlayerOptions.extraScriptingDefines</c>);
    /// to try Steam in the editor add it in Player Settings → Scripting Define Symbols.
    /// <para>
    /// If the chosen SDK fails to start (Steam not running, no <c>steam_appid.txt</c> in the editor), <see cref="Current"/>
    /// falls back to the no-op services, so the game always runs.
    /// </para>
    /// </summary>
    public static class PlatformServices
    {
        private static IPlatformServices _current;
        private static bool _initialized;

        /// <summary>The live services. Before <see cref="Initialize"/> it is the no-op implementation, never null.</summary>
        public static IPlatformServices Current => _current ?? (_current = new ItchPlatformServices());

        /// <summary>Raised after <see cref="Initialize"/> picks the services.</summary>
        public static event Action<IPlatformServices> Initialized;

        /// <summary>The services this build was compiled for (not yet initialised).</summary>
        public static IPlatformServices Create()
        {
#if DL_STEAM && UNITY_STANDALONE
            return new SteamPlatformServices();
#elif UNITY_SWITCH
            return new SwitchPlatformServices();
#else
            return new ItchPlatformServices();
#endif
        }

        /// <summary>Create and start the build's services once; on failure use the no-op ones. Idempotent.</summary>
        public static IPlatformServices Initialize()
        {
            if (_initialized && _current != null) return _current;

            IPlatformServices chosen = Create();
            bool ok;
            try { ok = chosen.Initialize(); }
            catch (Exception e)
            {
                Debug.LogException(e);
                ok = false;
            }
            if (!ok)
            {
                Debug.LogWarning($"PlatformServices: {chosen.Name} did not start; continuing without platform services.");
                chosen = new ItchPlatformServices();
                chosen.Initialize();
            }
            _current = chosen;
            _initialized = true;
            Debug.Log($"PlatformServices: {chosen.Name} (Steam Deck: {chosen.IsSteamDeck}).");
            Initialized?.Invoke(chosen);
            return chosen;
        }

        public static void Shutdown()
        {
            if (_current == null) return;
            try { _current.Shutdown(); }
            catch (Exception e) { Debug.LogException(e); }
            _current = null;
            _initialized = false;
        }

        // Enter Play Mode with domain reload off keeps statics between sessions; start each one clean.
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics()
        {
            _current = null;
            _initialized = false;
            Initialized = null;
        }

        /// <summary>
        /// SteamOS sets <c>SteamDeck=1</c> in the environment of games launched on a Deck. Used by the non-Steam builds
        /// (an Itch build added to Steam as a non-Steam game) and as the Steam build's fallback.
        /// </summary>
        public static bool SteamDeckFromEnvironment()
        {
            try { return Environment.GetEnvironmentVariable("SteamDeck") == "1"; }
            catch (Exception) { return false; }
        }
    }
}
