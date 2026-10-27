using DeadLetter.Core.Audio;
using UnityEngine;
using UnityEngine.Audio;

namespace DeadLetter.Runtime.Audio
{
    /// <summary>
    /// One positional ambience emitter (index.html <c>Ambience</c>, L1145–L1211; <c>EMITTERS</c>, L6577–L6598) through the
    /// Ambience mixer group. Core's <see cref="EmitterState"/> decides everything each frame (in region / deck / condition,
    /// gain level·k² with its glides, when a blip fires, when it is freed); this plays the loop, or a take of the blip, at
    /// that gain, panned by its place on screen. Place one per emitter (U-20–U-22 scene builders will spawn them from
    /// <see cref="PrologueEmitters"/>), or call <see cref="Configure"/>.
    /// </summary>
    public sealed class AmbientEmitter : MonoBehaviour
    {
        [SerializeField] private SfxBank bank;
        [Tooltip("Master > Ambience.")]
        [SerializeField] private AudioMixerGroup ambienceGroup;
        [SerializeField] private EmitterKind kind = EmitterKind.Drip;
        [SerializeField] private int region = 1;
        [Tooltip("Lane x (used when useTransformX is off).")]
        [SerializeField] private float x;
        [SerializeField] private bool useTransformX = true;
        [SerializeField] private float level = 0.5f;
        [SerializeField] private float reach = 4f;
        [SerializeField] private EmitterDeck deck = EmitterDeck.Any;
        [Tooltip("Tick interval (s); 0 = 1 s.")]
        [SerializeField] private float period;
        [Tooltip("AudioWorld condition it waits on (empty = always): revealed, lessonRunning…")]
        [SerializeField] private string condition;
        [SerializeField] private uint seed = 1;

        private EmitterDef _def;
        private EmitterState _state;
        private AudioSource _source;
        private SfxPicker _picker;
        private double _freeAt = double.PositiveInfinity;

        /// <summary>Sets this emitter from Core's table (e.g. <c>PrologueEmitters.All[i]</c>).</summary>
        public void Configure(EmitterDef def, SfxBank sfxBank, AudioMixerGroup group)
        {
            bank = sfxBank;
            ambienceGroup = group;
            kind = def.Kind; region = def.Region; x = (float)def.X; useTransformX = false;
            level = (float)def.Level; reach = (float)def.Reach; deck = def.Deck; period = (float)def.Period;
            condition = def.Condition;
            _def = def;
            if (_source != null) _source.outputAudioMixerGroup = group;
        }

        private void Awake()
        {
            _source = gameObject.AddComponent<AudioSource>();
            _source.playOnAwake = false;
            _source.spatialBlend = 0f;
            _source.volume = 0f;
            _source.outputAudioMixerGroup = ambienceGroup;
            _state = new EmitterState(seed);
            _picker = new SfxPicker(seed);
        }

        private void OnValidate() => _def = null;

        private void Update()
        {
            AudioWorld world = AudioWorld.Current;
            if (world == null || bank == null) return;
            if (_def == null)
                _def = new EmitterDef(region, useTransformX ? transform.position.x : x, kind, level, reach, deck, period,
                    string.IsNullOrEmpty(condition) ? null : condition);

            double now = Time.timeAsDouble;
            EmitterStep step = _state.Update(_def, world.ListenerX, world.region, world.upper, world.Condition(_def.Condition),
                now, Time.deltaTime);
            float gain = Mathf.Clamp01((float)_state.Gain);
            _source.panStereo = world.PanForX(_def.X);

            if (step.Freed) _freeAt = now + EmitterState.FreeAfter;
            else if (_state.Live) _freeAt = double.PositiveInfinity;

            if (_def.IsEvent)
            {
                _source.volume = gain;
                if (step.Blip)
                {
                    SfxBank.Sound s = bank.Find(_def.BankKey);
                    if (s != null && s.takes != null && s.takes.Length > 0)
                        _source.PlayOneShot(s.takes[_picker.Next(_def.BankKey, s.takes.Length)], 1f);
                }
                return;
            }

            if (_state.Live && !_source.isPlaying)
            {
                AudioClip clip = bank.First(_def.BankKey);
                if (clip == null) return;
                _source.clip = clip;
                _source.loop = true;
                _source.Play();
            }
            _source.volume = gain;
            if (!_state.Live && now >= _freeAt && _source.isPlaying) _source.Stop();
        }
    }
}
