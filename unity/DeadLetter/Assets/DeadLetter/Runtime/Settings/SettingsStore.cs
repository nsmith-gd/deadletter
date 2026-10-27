using System;
using System.IO;
using DeadLetter.Core.Settings;
using UnityEngine;
using UnityEngine.Audio;
using UnityEngine.InputSystem;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace DeadLetter.Runtime.Settings
{
    /// <summary>
    /// Loads, saves and applies <see cref="GameSettings"/>. One per game, in <c>DL_Persistent</c>.
    /// <para>
    /// <b>File:</b> <c>Application.persistentDataPath/settings.cfg</c>, the Core <see cref="SettingsSerializer"/> text
    /// format, written atomically (temp file, then replace). Settings are per device on purpose (a Deck and a desktop
    /// want different text sizes and glyphs), so they are not cloud-synced. On Switch the path must move into the mounted
    /// save data first (<c>SwitchPlatformServices</c> TODO).
    /// </para>
    /// <para>
    /// <b>Applying</b> (<see cref="Apply"/>, also after every <see cref="Commit"/>):
    /// <list type="bullet">
    /// <item>Audio: each U-16 mixer group's exposed parameter (<c>Master</c>, <c>Music</c>, <c>SFX</c>, <c>Voice</c>,
    /// <c>Ambience</c>) gets <see cref="AudioLevels.Decibels"/>. Unity ignores <c>AudioMixer.SetFloat</c> during Awake, so the
    /// first apply runs in Start.</item>
    /// <item>Calm mode: <see cref="Calm"/> is a static flag every flicker / shake / spark source reads
    /// (<c>LaneCameraDriver.Shake</c> already does; lights and sparks must, §4.29). Bloom drops to 0.35/0.55 of authored.</item>
    /// <item>Brightness: URP <c>ColorAdjustments.postExposure</c> on <see cref="postVolume"/> = log2(brightness), so 1.0 is
    /// the authored look (the prototype's 1.4× exposure is the authored base).</item>
    /// <item>Auto-run: <c>D17Controller</c> copies <see cref="GameSettings.AutoRun"/> into <c>D17Motor.AutoRun</c> on
    /// <see cref="Applied"/>.</item>
    /// <item>Rebinding: <see cref="GameSettings.BindingOverrides"/> is loaded into <see cref="actions"/>
    /// (<c>LoadBindingOverridesFromJson</c>); <see cref="BindingRebinder"/> writes it back.</item>
    /// </list>
    /// </para>
    /// </summary>
    [DefaultExecutionOrder(-900)]
    [DisallowMultipleComponent]
    public sealed class SettingsStore : MonoBehaviour
    {
        public const string FileName = "settings.cfg";

        [Tooltip("The U-16 mixer, with exposed parameters Master, Music, SFX, Voice, Ambience (dB).")]
        [SerializeField] private AudioMixer mixer;
        [Tooltip("DeadLetter.inputactions: binding overrides are loaded into and saved from this asset.")]
        [SerializeField] private InputActionAsset actions;
        [Tooltip("Global post-processing Volume with ColorAdjustments (brightness) and Bloom (calm).")]
        [SerializeField] private Volume postVolume;

        private static GameSettings _current = new GameSettings();
        private static SettingsStore _instance;
        private float _authoredBloom = -1f;
        private bool _started;

        public static SettingsStore Instance => _instance;

        /// <summary>The live settings (defaults until loaded). Treat as read-only; change via <see cref="Commit"/>.</summary>
        public static GameSettings Current => _current;

        /// <summary>The settings file has been read (or found missing) this session.</summary>
        public static bool Loaded { get; private set; }

        /// <summary>Calm mode ("Reduce flicker and flashes"): no flicker, flashes, shake or sparks. Read by every such source.</summary>
        public static bool Calm => _current.Calm;

        /// <summary>Raised after settings are applied (load, commit). Listeners: D-17 auto-run, glyphs, UI text size, cues.</summary>
        public static event Action<GameSettings> Applied;

        public InputActionAsset Actions => actions;

        public static string FilePath => Path.Combine(Application.persistentDataPath, FileName);

        private void Awake()
        {
            if (_instance != null && _instance != this)
            {
                Debug.LogWarning("SettingsStore: a second store was found; disabling it.", this);
                enabled = false;
                return;
            }
            _instance = this;
            _current = Load();
            Loaded = true;
            ApplyBindings();
        }

        private void Start()
        {
            _started = true;
            Apply();
        }

        private void OnDestroy()
        {
            if (_instance == this) _instance = null;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics()
        {
            _current = new GameSettings();
            _instance = null;
            Loaded = false;
            Applied = null;
        }

        /// <summary>Replace the settings with an edited copy, save, and apply (the options screen's Confirm).</summary>
        public void Commit(GameSettings edited)
        {
            if (edited == null) throw new ArgumentNullException(nameof(edited));
            var next = edited.Clone();
            next.Sanitise();
            _current = next;
            Save();
            ApplyBindings();
            Apply();
        }

        /// <summary>Back to defaults (keeps unknown keys from newer builds), save and apply.</summary>
        public void ResetToDefaults()
        {
            var d = new GameSettings();
            d.UnknownEntries.AddRange(_current.UnknownEntries);
            d.Version = _current.Version;
            if (actions != null) actions.RemoveAllBindingOverrides();
            Commit(d);
        }

        /// <summary>The options screen was cancelled: drop rebinds made while editing and restore the saved ones.</summary>
        public void RevertBindings() => ApplyBindings();

        // ---- Persistence ----------------------------------------------------------------------------------------------
        public static GameSettings Load()
        {
            string path = FilePath;
            try
            {
                if (!File.Exists(path)) return new GameSettings();
                int rejected;
                var s = SettingsSerializer.Deserialize(File.ReadAllText(path), out rejected);
                if (rejected > 0) Debug.LogWarning($"SettingsStore: {rejected} unreadable line(s) in {path}; those options use defaults.");
                return s;
            }
            catch (Exception e)
            {
                Debug.LogWarning($"SettingsStore: could not read {path} ({e.Message}); using defaults.");
                return new GameSettings();
            }
        }

        public void Save()
        {
            string path = FilePath;
            string tmp = path + ".tmp";
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                File.WriteAllBytes(tmp, SettingsSerializer.SerializeUtf8(_current));
                if (File.Exists(path)) File.Delete(path);
                File.Move(tmp, path);
            }
            catch (Exception e)
            {
                Debug.LogWarning($"SettingsStore: could not write {path} ({e.Message}).");
            }
        }

        // ---- Applying -------------------------------------------------------------------------------------------------
        public void Apply()
        {
            GameSettings s = _current;
            if (_started) ApplyAudio(s);
            ApplyPost(s);
            Applied?.Invoke(s);
        }

        private void ApplyAudio(GameSettings s)
        {
            if (mixer == null) return;
            for (int i = 0; i < AudioLevels.All.Length; i++)
            {
                AudioGroup g = AudioLevels.All[i];
                string param = AudioLevels.ExposedParameter(g);
                if (!mixer.SetFloat(param, (float)AudioLevels.Decibels(s, g)))
                    Debug.LogWarning($"SettingsStore: mixer has no exposed parameter '{param}' (U-16).", this);
            }
        }

        private void ApplyPost(GameSettings s)
        {
            if (postVolume == null) return;
            VolumeProfile profile = postVolume.profile;   // instance copy; the asset on disk is untouched
            if (profile == null) return;
            if (profile.TryGet(out ColorAdjustments colour))
                colour.postExposure.Override((float)(Math.Log(s.Brightness) / Math.Log(2.0)));
            if (profile.TryGet(out Bloom bloom))
            {
                if (_authoredBloom < 0f) _authoredBloom = bloom.intensity.value;
                bloom.intensity.Override(_authoredBloom * (float)(s.Bloom / GameSettings.BloomStrength));
            }
        }

        private void ApplyBindings()
        {
            if (actions == null) return;
            try
            {
                actions.RemoveAllBindingOverrides();
                if (!string.IsNullOrEmpty(_current.BindingOverrides))
                    actions.LoadBindingOverridesFromJson(_current.BindingOverrides);
            }
            catch (Exception e)
            {
                Debug.LogWarning($"SettingsStore: binding overrides unreadable ({e.Message}); using default bindings.");
                actions.RemoveAllBindingOverrides();
            }
        }
    }
}
