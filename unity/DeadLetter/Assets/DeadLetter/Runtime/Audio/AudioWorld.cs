using System.Collections.Generic;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Presentation;
using UnityEngine;
using UnityEngine.Audio;

namespace DeadLetter.Runtime.Audio
{
    /// <summary>
    /// What the audio reads from the game each frame: D-17's lane x, his region and deck, and the named conditions the
    /// emitters and tannoys wait on (<c>revealed</c>, <c>released</c>, <c>lessonRunning</c>…). Bound to Core's
    /// <see cref="AmbienceWorld"/> (GameHost, U-23) it takes all of them from the sim and plays every <c>EMITTERS</c> row
    /// itself, on pooled sources through the Ambience group, at the gain and blips Core decides (<see cref="Present"/>);
    /// hand-placed <see cref="AmbientEmitter"/>s then stay silent. Unbound, <see cref="listener"/>'s x is used and every
    /// condition is false unless set. Also holds the one pan setting (±<see cref="edgePan"/> at the frame edges) every
    /// positional sound uses.
    /// </summary>
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(-50)]
    public sealed class AudioWorld : MonoBehaviour
    {
        [Tooltip("D-17's root. Its world x is the prototype's lane x (Vec3.ToUnity keeps x).")]
        [SerializeField] private Transform listener;
        [Tooltip("The camera the pan is measured in (empty = Camera.main).")]
        [SerializeField] private UnityEngine.Camera panCamera;
        [Tooltip("Pan at the left/right frame edges (decision on #20: 0.4). One value for the whole game.")]
        [Range(0f, 1f)]
        [SerializeField] private float edgePan = (float)PanLaw.DefaultEdgePan;

        [Tooltip("game.region: 1 DL-01, 2 DL-02–05, 3 DL-06–07, 4 DL-08–10, 5 DL-11, 6 chapter one.")]
        public int region = 1;
        [Tooltip("game.upper: on the upper deck.")]
        public bool upper;

        [Header("Emitters (Core, U-23)")]
        [Tooltip("Play Core's emitters (PrologueEmitters) here once GameHost binds the AmbienceWorld.")]
        [SerializeField] private bool emittersFromCore = true;
        [SerializeField] private SfxBank bank;
        [Tooltip("Master > Ambience.")]
        [SerializeField] private AudioMixerGroup ambienceGroup;
        [SerializeField] private uint emitterSeed = 5;

        private readonly HashSet<string> _conditions = new HashSet<string>();
        private AmbienceWorld _core;
        private AudioSource[] _emitters;
        private double[] _freeAt;
        private SfxPicker _picker;

        /// <summary>The scene's AudioWorld (the last one enabled).</summary>
        public static AudioWorld Current { get; private set; }

        public float EdgePan
        {
            get => edgePan;
            set => edgePan = Mathf.Clamp01(value);
        }

        /// <summary>D-17's lane x (the sim's once bound).</summary>
        public double ListenerX => _core != null ? _core.X : listener != null ? listener.position.x : 0.0;

        /// <summary>Core's emitters play here (bound, and <see cref="emittersFromCore"/>): hand-placed ones stay silent.</summary>
        public bool DrivesEmitters => _core != null && emittersFromCore;

        /// <summary>Takes region, deck, x, conditions and the emitters from Core (null: unbind).</summary>
        public void Bind(AmbienceWorld world)
        {
            _core = world;
            if (world == null || !emittersFromCore) return;
            if (_emitters == null || _emitters.Length != world.Count)
            {
                _emitters = new AudioSource[world.Count];
                _freeAt = new double[world.Count];
                for (int i = 0; i < world.Count; i++)
                {
                    var go = new GameObject("Emitter " + i + " " + world[i].Kind);
                    go.transform.SetParent(transform, false);
                    AudioSource s = go.AddComponent<AudioSource>();
                    s.playOnAwake = false;
                    s.spatialBlend = 0f;
                    s.volume = 0f;
                    s.outputAudioMixerGroup = ambienceGroup;
                    _emitters[i] = s;
                    _freeAt[i] = double.PositiveInfinity;
                }
            }
            _picker = new SfxPicker(emitterSeed);
        }

        /// <summary>
        /// Per frame after Core's <see cref="AmbienceWorld.Update"/>: the sim's region and deck, and each emitter's gain, pan
        /// and blip (<c>Ambience.update</c>, L1196–L1209): loops play while live and stop 2 s after they are freed.
        /// </summary>
        public void Present(double now)
        {
            if (_core == null) return;
            region = _core.Region;
            upper = _core.Upper;
            if (!emittersFromCore || _emitters == null || bank == null) return;
            for (int i = 0; i < _emitters.Length; i++)
            {
                EmitterDef def = _core[i];
                AudioSource s = _emitters[i];
                float gain = Mathf.Clamp01((float)_core.Gain(i));
                if (_core.Freed(i)) _freeAt[i] = now + EmitterState.FreeAfter;
                else if (_core.Live(i)) _freeAt[i] = double.PositiveInfinity;
                if (!_core.Live(i) && !s.isPlaying) continue;
                s.panStereo = PanForX(def.X);
                s.volume = gain;
                if (def.IsEvent)
                {
                    if (_core.Blip(i))
                    {
                        SfxBank.Sound sound = bank.Find(def.BankKey);
                        if (sound != null && sound.takes != null && sound.takes.Length > 0)
                            s.PlayOneShot(sound.takes[_picker.Next(def.BankKey, sound.takes.Length)], 1f);
                    }
                    continue;
                }
                if (_core.Live(i) && !s.isPlaying)
                {
                    AudioClip clip = bank.First(def.BankKey);
                    if (clip == null) continue;
                    s.clip = clip;
                    s.loop = true;
                    s.Play();
                }
                if (!_core.Live(i) && now >= _freeAt[i] && s.isPlaying) s.Stop();
            }
        }

        public void SetCondition(string name, bool on)
        {
            if (string.IsNullOrEmpty(name)) return;
            if (on) _conditions.Add(name); else _conditions.Remove(name);
        }

        /// <summary>True for a null/empty condition (none), else whether Core (bound) or a caller has set it.</summary>
        public bool Condition(string name) => string.IsNullOrEmpty(name) || _conditions.Contains(name) || (_core != null && _core.Condition(name));

        /// <summary>The stereo pan for a sound at <paramref name="worldPosition"/> (0 behind the camera or with no camera).</summary>
        public float PanFor(Vector3 worldPosition)
        {
            UnityEngine.Camera cam = panCamera != null ? panCamera : UnityEngine.Camera.main;
            if (cam == null) return 0f;
            Vector3 vp = cam.WorldToViewportPoint(worldPosition);
            if (vp.z <= 0f) return 0f;
            return (float)PanLaw.FromViewportX(vp.x, edgePan);
        }

        /// <summary>The pan for a lane x at the listener's height (sounds placed only by x, as the prototype's are).</summary>
        public float PanForX(double x)
        {
            Vector3 p = listener != null ? listener.position : Vector3.zero;
            p.x = (float)x;
            return PanFor(p);
        }

        private void OnEnable() => Current = this;

        private void OnDisable()
        {
            if (Current == this) Current = null;
        }
    }
}
