using DeadLetter.Core.Audio;
using UnityEngine;
using UnityEngine.Audio;

namespace DeadLetter.Runtime.Audio
{
    /// <summary>
    /// <c>Sound</c>'s one-shots and continuous layers (port_architecture §4.23) on pooled 2D AudioSources through the SFX
    /// mixer group. Core picks the take (<see cref="SfxPicker"/>: seeded, no back-to-back repeat), the pan
    /// (<see cref="PanLaw"/> via <see cref="AudioWorld"/>) and the layers' glides (<see cref="SfxLoopMixer"/>); this only
    /// plays clips. Scene rules call <c>Play(SfxKeys.X, volume)</c> where the prototype called <c>Sound.x(v)</c>.
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class SfxPlayer : MonoBehaviour
    {
        [SerializeField] private SfxBank bank;
        [Tooltip("Master > SFX.")]
        [SerializeField] private AudioMixerGroup sfxGroup;
        [Tooltip("One-shot voices that can sound at once; the oldest is reused when all are busy.")]
        [Min(1)]
        [SerializeField] private int poolSize = 16;
        [SerializeField] private uint seed = 17;
        [SerializeField] private SfxPickMode pickMode = SfxPickMode.RandomNoRepeat;

        private AudioSource[] _pool;
        private float[] _startedAt;
        private readonly AudioSource[] _loops = new AudioSource[SfxLoopMixer.Count];
        private readonly SfxLoopMixer _mixer = new SfxLoopMixer();
        private SfxPicker _picker;

        /// <summary>The scene's SfxPlayer (the last one enabled).</summary>
        public static SfxPlayer Current { get; private set; }

        public SfxLoopMixer Loops => _mixer;

        private void Awake()
        {
            _picker = new SfxPicker(seed, pickMode);
            _pool = new AudioSource[Mathf.Max(1, poolSize)];
            _startedAt = new float[_pool.Length];
            for (int i = 0; i < _pool.Length; i++) _pool[i] = NewSource("Sfx " + i, false);
        }

        private void OnEnable() => Current = this;

        private void OnDisable()
        {
            if (Current == this) Current = null;
        }

        /// <summary>A one-shot at the centre, at <paramref name="volume"/> (the prototype's per-call gain).</summary>
        public AudioSource Play(string key, float volume = 1f) => PlayPanned(key, volume, 0f);

        /// <summary>A one-shot panned by where <paramref name="worldPosition"/> is on screen.</summary>
        public AudioSource Play(string key, float volume, Vector3 worldPosition)
        {
            AudioWorld w = AudioWorld.Current;
            return PlayPanned(key, volume, w != null ? w.PanFor(worldPosition) : 0f);
        }

        /// <summary>A one-shot at a stereo pan (−1..1).</summary>
        public AudioSource PlayPanned(string key, float volume, float pan)
        {
            AudioClip clip = Pick(key);
            if (clip == null || volume <= 0f) return null;
            int i = FreeVoice();
            AudioSource s = _pool[i];
            s.Stop();
            s.clip = clip;
            s.volume = Mathf.Clamp01(volume);
            s.panStereo = Mathf.Clamp(pan, -1f, 1f);
            s.Play();
            _startedAt[i] = Time.unscaledTime;
            return s;
        }

        /// <summary>A continuous layer's level (<c>Sound.hum(level)</c>, <c>roll</c>, <c>belt</c>…); it glides with its τ.</summary>
        public void SetLoop(SfxLoop loop, float level) => _mixer.Set(loop, level);

        /// <summary>The White rears and hisses (index.html L7152), on its own source so the steam cannot mask it.</summary>
        public void WhiteWarning() => _mixer.WhiteWarning(Time.unscaledTimeAsDouble);

        /// <summary>The take to play for <paramref name="key"/>, or null (logs a warning in the editor).</summary>
        public AudioClip Pick(string key)
        {
            SfxBank.Sound s = bank != null ? bank.Find(key) : null;
            if (s == null || s.takes == null || s.takes.Length == 0)
            {
#if UNITY_EDITOR
                Debug.LogWarning("[Audio] No clip for SFX key '" + key + "'. Run Dead Letter → Audio → Import Audio.", this);
#endif
                return null;
            }
            if (_picker == null) _picker = new SfxPicker(seed, pickMode);
            return s.takes[_picker.Next(key, s.takes.Length)];
        }

        private void Update()
        {
            // Layers glide on unscaled time: the web build's AudioParams run on the audio clock, not the game's.
            _mixer.Step(Time.unscaledTimeAsDouble, Time.unscaledDeltaTime);
            for (int i = 0; i < SfxLoopMixer.Count; i++)
            {
                float v = (float)_mixer.Volume((SfxLoop)i);
                AudioSource s = _loops[i];
                if (v <= 1e-4f && _mixer.Target((SfxLoop)i) <= 0)
                {
                    if (s != null && s.isPlaying) s.Stop();
                    continue;
                }
                if (s == null)
                {
                    AudioClip clip = bank != null ? bank.First(SfxLoopMixer.Keys[i]) : null;
                    if (clip == null) continue;
                    s = _loops[i] = NewSource("Loop " + (SfxLoop)i, true);
                    s.clip = clip;
                }
                s.volume = Mathf.Clamp01(v);
                if (!s.isPlaying) s.Play();
            }
        }

        private int FreeVoice()
        {
            int oldest = 0;
            for (int i = 0; i < _pool.Length; i++)
            {
                if (!_pool[i].isPlaying) return i;
                if (_startedAt[i] < _startedAt[oldest]) oldest = i;
            }
            return oldest;
        }

        private AudioSource NewSource(string name, bool loop)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            AudioSource s = go.AddComponent<AudioSource>();
            s.playOnAwake = false;
            s.loop = loop;
            s.spatialBlend = 0f;
            s.outputAudioMixerGroup = sfxGroup;
            return s;
        }
    }
}
