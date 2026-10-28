using System;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Save;
using DeadLetter.Runtime.Save;
using UnityEngine;
using UnityEngine.Audio;
using UnityEngine.InputSystem;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
// Inside DeadLetter.Runtime, a bare "Settings" names this namespace, so the options type goes by an alias.
using Options = DeadLetter.Core.Save.Settings;

namespace DeadLetter.Runtime.Settings
{
    /// <summary>
    /// Applies the player's options (Core <see cref="Options"/>, the one settings model) to the engine. One per game,
    /// in <c>DL_Persistent</c>. It keeps no copy of its own on disk.
    /// <para>
    /// <b>Storage:</b> the options live in the save slot (<c>opt/</c> keys of <see cref="SaveModel"/>), owned by U-14's
    /// <see cref="CheckpointService"/>, which this store reaches through <see cref="CheckpointTrigger.Service"/>.
    /// The service reads the slot's options when it is constructed (<see cref="CheckpointService.TryLoadSettings"/>), so
    /// whoever builds it must set <see cref="CheckpointTrigger.Service"/> at boot, before the title screen, for calm
    /// mode, volumes and bindings to hold there. <see cref="Commit"/> calls <see cref="CheckpointService.ApplySettings"/>
    /// (which also sets the graph's calm flag and saves; before a game is started or continued it writes only the
    /// options into the slot, keeping its progress). When the service is replaced or reloads (new game, continue,
    /// respawn) the store adopts <see cref="CheckpointService.Settings"/> and applies it. A commit made while no service
    /// exists is held in memory and handed to the next service bound.
    /// </para>
    /// <para>
    /// <b>Applying</b> (<see cref="Apply"/>, after every commit and adopt):
    /// <list type="bullet">
    /// <item>Audio: each U-16 mixer group's exposed parameter (<c>Master</c>, <c>Music</c>, <c>SFX</c>, <c>Voice</c>,
    /// <c>Ambience</c>) gets <see cref="AudioLevels.Decibels"/>. Unity ignores <c>AudioMixer.SetFloat</c> during Awake, so the
    /// first apply runs in Start.</item>
    /// <item>Calm mode: <see cref="Calm"/> is a static flag every flicker / shake / spark source reads
    /// (<c>LaneCameraDriver.Shake</c> already does; lights and sparks must, §4.29); Core mechanisms read the graph's
    /// <c>Calm</c>, set by the service. Bloom drops to 0.35/0.55 of authored.</item>
    /// <item>Brightness: URP <c>ColorAdjustments.postExposure</c> on <see cref="postVolume"/> = log2(brightness), so 1.0 is
    /// the authored look (the prototype's 1.4× exposure is the authored base).</item>
    /// <item>Auto-run: <c>D17Controller</c> copies <see cref="Options.AutoRun"/> into <c>D17Motor.AutoRun</c> on
    /// <see cref="Applied"/>.</item>
    /// <item>Rebinding: <see cref="Options.BindingOverrides"/> is loaded into <see cref="actions"/>
    /// (<c>LoadBindingOverridesFromJson</c>); <see cref="BindingRebinder"/> captures it back.</item>
    /// </list>
    /// </para>
    /// </summary>
    [DefaultExecutionOrder(-900)]
    [DisallowMultipleComponent]
    public sealed class SettingsStore : MonoBehaviour
    {
        [Tooltip("The U-16 mixer, with exposed parameters Master, Music, SFX, Voice, Ambience (dB).")]
        [SerializeField] private AudioMixer mixer;
        [Tooltip("DeadLetter.inputactions: binding overrides are loaded into and saved from this asset.")]
        [SerializeField] private InputActionAsset actions;
        [Tooltip("Global post-processing Volume with ColorAdjustments (brightness) and Bloom (calm).")]
        [SerializeField] private Volume postVolume;

        private static Options _current = new Options();
        private static SettingsStore _instance;
        private CheckpointService _service;
        /// <summary>A commit made while no service was bound; handed to the next one.</summary>
        private Options _held;
        private float _authoredBloom = -1f;
        private bool _started;

        public static SettingsStore Instance => _instance;

        /// <summary>The live options (defaults until a service is bound). Treat as read-only; change via <see cref="Commit"/>.</summary>
        public static Options Current => _current;

        /// <summary>A store is running, so <see cref="Current"/> is the player's options (not just the defaults of no store).</summary>
        public static bool Loaded { get; private set; }

        /// <summary>Calm mode ("Reduce flicker and flashes"): no flicker, flashes, shake or sparks. Read by every such source.</summary>
        public static bool Calm => _current.Calm;

        /// <summary>Raised after the options are applied (adopt, commit). Listeners: D-17 auto-run, glyphs, UI text size, cues.</summary>
        public static event Action<Options> Applied;

        public InputActionAsset Actions => actions;

        private void Awake()
        {
            if (_instance != null && _instance != this)
            {
                Debug.LogWarning("SettingsStore: a second store was found; disabling it.", this);
                enabled = false;
                return;
            }
            _instance = this;
            Loaded = true;
            CheckpointTrigger.ServiceChanged += Bind;
            Bind(CheckpointTrigger.Service);
            ApplyBindings();
        }

        private void Start()
        {
            _started = true;
            Apply();
        }

        private void OnDestroy()
        {
            if (_instance != this) return;
            CheckpointTrigger.ServiceChanged -= Bind;
            if (_service != null) _service.Reloaded -= OnReloaded;
            _service = null;
            _instance = null;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics()
        {
            _current = new Options();
            _instance = null;
            Loaded = false;
            Applied = null;
        }

        /// <summary>
        /// Replace the options with an edited copy and apply it (the options screen's Confirm). Saved with the slot
        /// through <see cref="CheckpointService.ApplySettings"/>, or held until a service is bound.
        /// </summary>
        public void Commit(Options edited)
        {
            if (edited == null) throw new ArgumentNullException(nameof(edited));
            var next = edited.Clone();
            next.Sanitise();
            if (_service != null)
            {
                _service.ApplySettings(next);   // clones, sets the graph's calm, saves
                _current = _service.Settings.Clone();
                _held = null;
            }
            else
            {
                _current = next;
                _held = next;
            }
            ApplyBindings();
            Apply();
        }

        /// <summary>Back to defaults (keeps <c>opt/</c> keys from newer builds) and apply.</summary>
        public void ResetToDefaults()
        {
            var d = new Options();
            foreach (var kv in _current.UnknownOptions) d.UnknownOptions[kv.Key] = kv.Value;
            if (actions != null) actions.RemoveAllBindingOverrides();
            Commit(d);
        }

        /// <summary>The options screen was cancelled: drop rebinds made while editing and restore the saved ones.</summary>
        public void RevertBindings() => ApplyBindings();

        // ---- The save system ------------------------------------------------------------------------------------------
        private void Bind(CheckpointService service)
        {
            if (_service == service) return;
            if (_service != null) _service.Reloaded -= OnReloaded;
            _service = service;
            if (_service == null) return;
            _service.Reloaded += OnReloaded;
            if (_held != null)
            {
                // Edited while no service existed: newer than the slot's. ApplySettings keeps the slot's progress.
                var held = _held;
                _held = null;
                _service.ApplySettings(held);
            }
            // The service read the slot's options when it was built, so this is the player's options from boot.
            Adopt(_service.Settings);
        }

        /// <summary>New game, continue or respawn: adopt the service's options (a continue loads the slot's).</summary>
        private void OnReloaded(Checkpoint _) => Adopt(_service.Settings);

        private void Adopt(Options s)
        {
            var next = s.Clone();
            next.Sanitise();
            _current = next;
            ApplyBindings();
            Apply();
        }

        // ---- Applying -------------------------------------------------------------------------------------------------
        public void Apply()
        {
            Options s = _current;
            if (_started) ApplyAudio(s);
            ApplyPost(s);
            Applied?.Invoke(s);
        }

        private void ApplyAudio(Options s)
        {
            if (mixer == null) return;
            // U-23: while the mix director drives this mixer it writes the levels (options + the moment duck) every frame.
            Audio.AudioMixDirector director = Audio.AudioMixDirector.Current;
            if (director != null && director.Driving && director.Mixer == mixer) { director.Refresh(); return; }
            for (int i = 0; i < AudioLevels.All.Length; i++)
            {
                AudioGroup g = AudioLevels.All[i];
                string param = AudioLevels.ExposedParameter(g);
                if (!mixer.SetFloat(param, (float)AudioLevels.Decibels(s, g)))
                    Debug.LogWarning($"SettingsStore: mixer has no exposed parameter '{param}' (U-16).", this);
            }
        }

        private void ApplyPost(Options s)
        {
            if (postVolume == null) return;
            VolumeProfile profile = postVolume.profile;   // instance copy; the asset on disk is untouched
            if (profile == null) return;
            if (profile.TryGet(out ColorAdjustments colour))
                colour.postExposure.Override((float)(Math.Log(s.Brightness) / Math.Log(2.0)));
            if (profile.TryGet(out Bloom bloom))
            {
                if (_authoredBloom < 0f) _authoredBloom = bloom.intensity.value;
                bloom.intensity.Override(_authoredBloom * (float)(s.Bloom / Options.BloomStrength));
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
