using System;
using System.Collections.Generic;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Streaming;
using UnityEngine;

namespace DeadLetter.Runtime.Scenes
{
    /// <summary>
    /// Mirrors one Core mechanism onto one art node (a <c>MECH_&lt;Type&gt;_&lt;id&gt;[__&lt;part&gt;]</c> object,
    /// docs/unity/asset_conventions.md): views read state, never decide (§4.13l). The Editor's scene builder adds it to every
    /// <c>MECH_</c> node and fills <see cref="channels"/> from Core's <see cref="MechanismViewBindings"/>; the director tunes
    /// scales and pivots here.
    /// <para><b>Binding:</b> on enable the view joins <see cref="MechanismViewRegistry.Views"/>; the GameHost binds it to its
    /// chapter's mechanism by <see cref="MechanismId"/> once (one dictionary read), resolving a reader delegate per channel
    /// (<see cref="MechanismReadout.Reader"/>), so a frame does no string lookups and no type tests.</para>
    /// <para><b>Pose:</b> the art is authored in the state the chapter starts in. Each channel moves the node by the change of
    /// its value from that state (read once from a reference sim at the chapter's first checkpoint) × its scale: rotations
    /// first, about <see cref="pivot"/> (default: the centre of the node's renderers, since the export's meshes mostly sit at
    /// the origin), then translations; emission scales the renderers' rest emission. Values are sampled after every Core step
    /// and interpolated by the host's render alpha, like D-17 and the camera.</para>
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class MechanismView : MonoBehaviour
    {
        [Serializable]
        public struct Channel
        {
            public ViewChannel channel;
            [Tooltip("Lamp index (Lamp channel only).")]
            public int index;
            public ViewMotion motion;
            [Tooltip("Metres or degrees (or emission gain) per unit of the Core value.")]
            public float scale;
        }

        [Tooltip("The Core mechanism ID (dl01.shutter), from the node's MECH_ name.")]
        [SerializeField] private string mechanismId;
        [Tooltip("The part (the export's source object name), empty for the mechanism's root or anchor.")]
        [SerializeField] private string part;
        [SerializeField] private Channel[] channels = new Channel[0];
        [Tooltip("Rotate about this world point instead of the renderers' centre.")]
        [SerializeField] private bool hasPivot;
        [SerializeField] private Vector3 pivot;

        private static readonly int EmissionColor = Shader.PropertyToID("_EmissionColor");   // URP Lit

        private Func<double>[] _readers;
        private double[] _rest, _prev, _curr;
        private bool _bound, _failed, _emissive;
        private Vector3 _restPos, _pivot;
        private Quaternion _restRot;
        private Renderer[] _renderers;
        private Color[] _restEmission;
        private MaterialPropertyBlock _block;

        public string MechanismId => mechanismId;
        public string Part => part;
        public bool Bound => _bound;
        /// <summary>Binding was tried and failed (logged once); the node stays as authored.</summary>
        public bool Failed => _failed;

        /// <summary>Editor (scene builder): what this node shows.</summary>
        public void Configure(string id, string partName, Channel[] viewChannels)
        {
            mechanismId = id;
            part = partName ?? "";
            channels = viewChannels ?? new Channel[0];
        }

        public static Channel From(ViewBinding b) => new Channel { channel = b.Channel, index = b.Index, motion = b.Motion, scale = (float)b.Scale };

        private void OnEnable() => MechanismViewRegistry.Add(this);

        private void OnDisable()
        {
            MechanismViewRegistry.Remove(this);
            if (_bound) { transform.SetPositionAndRotation(_restPos, _restRot); SetEmission(1f); }
            _bound = false;
        }

        /// <summary>The host's registry binds the view (once): the live and reference mechanisms and the calm flag.</summary>
        internal bool TryBind(IMechanism live, IMechanism rest, Func<bool> calm)
        {
            if (_bound) return true;
            if (_failed) return false;
            int n = channels.Length;
            if (live == null || rest == null || n == 0) { _failed = true; return false; }   // no mechanism (logged by the registry), or nothing to show
            _readers = new Func<double>[n];
            _rest = new double[n];
            _prev = new double[n];
            _curr = new double[n];
            for (int i = 0; i < n; i++)
            {
                Channel c = channels[i];
                _readers[i] = MechanismReadout.Reader(live, c.channel, c.index, calm);
                Func<double> restReader = MechanismReadout.Reader(rest, c.channel, c.index, calm);
                if (_readers[i] == null || restReader == null)
                {
                    Debug.LogWarning("[MechanismView] " + name + ": " + mechanismId + " (" + (live != null ? live.GetType().Name : "missing") + ") has no " +
                                     c.channel + (c.channel == ViewChannel.Lamp ? "[" + c.index + "]" : "") + "; the node stays as authored.", this);
                    _failed = true;
                    return false;
                }
                _rest[i] = c.motion == ViewMotion.Emission ? 0 : restReader();   // emission is a gain, not a change
                if (c.motion == ViewMotion.Emission) _emissive = true;
            }
            _restPos = transform.position;
            _restRot = transform.rotation;
            _renderers = GetComponentsInChildren<Renderer>(true);
            _pivot = hasPivot ? pivot : Centre(_renderers, _restPos);
            if (_emissive)
            {
                _restEmission = new Color[_renderers.Length];
                for (int i = 0; i < _renderers.Length; i++)
                {
                    Material m = _renderers[i].sharedMaterial;
                    _restEmission[i] = m != null && m.HasProperty(EmissionColor) ? m.GetColor(EmissionColor) : Color.black;
                }
                _block = new MaterialPropertyBlock();
            }
            _bound = true;
            Sample();
            Snap();
            return true;
        }

        /// <summary>After each Core step: the values' change from the authored state.</summary>
        internal void Sample()
        {
            for (int i = 0; i < _readers.Length; i++)
            {
                _prev[i] = _curr[i];
                _curr[i] = _readers[i]() - _rest[i];
            }
        }

        /// <summary>A teleport (respawn, continue): no interpolation across it.</summary>
        internal void Snap()
        {
            for (int i = 0; i < _curr.Length; i++) _prev[i] = _curr[i];
        }

        /// <summary>Places the node for this frame, <paramref name="alpha"/> of the way from the last step's values to this one's.</summary>
        internal void Apply(float alpha)
        {
            Vector3 pos = _restPos;
            Quaternion rot = _restRot;
            float emission = -1f;
            for (int i = 0; i < channels.Length; i++)
            {
                float v = (float)(_prev[i] + (_curr[i] - _prev[i]) * alpha) * channels[i].scale;
                switch (channels[i].motion)
                {
                    case ViewMotion.RotateZ:
                        Quaternion q = Quaternion.AngleAxis(v, Vector3.forward);    // lane z: +x turns toward +y, as three.js rotation.z (§0.2)
                        pos = _pivot + q * (pos - _pivot);
                        rot = q * rot;
                        break;
                    case ViewMotion.Emission:
                        emission = Mathf.Max(0f, (float)(_prev[i] + (_curr[i] - _prev[i]) * alpha) * channels[i].scale);
                        break;
                }
            }
            for (int i = 0; i < channels.Length; i++)
            {
                if (channels[i].motion != ViewMotion.TranslateX && channels[i].motion != ViewMotion.TranslateY && channels[i].motion != ViewMotion.TranslateZ) continue;
                float v = (float)(_prev[i] + (_curr[i] - _prev[i]) * alpha) * channels[i].scale;
                if (channels[i].motion == ViewMotion.TranslateX) pos.x += v;
                else if (channels[i].motion == ViewMotion.TranslateY) pos.y += v;
                else pos.z += v;
            }
            transform.SetPositionAndRotation(pos, rot);
            if (emission >= 0f) SetEmission(emission);
        }

        /// <summary>
        /// Lamp brightness: rest emission × gain, through a property block (the shared material is untouched). Needs the
        /// material's <c>_EMISSION</c> keyword (ArtMaterials sets it for emissive materials); a lamp authored dark stays dark.
        /// </summary>
        private void SetEmission(float gain)
        {
            if (!_emissive || _renderers == null) return;
            for (int i = 0; i < _renderers.Length; i++)
            {
                if (_renderers[i] == null) continue;
                _renderers[i].GetPropertyBlock(_block);
                _block.SetColor(EmissionColor, _restEmission[i] * gain);
                _renderers[i].SetPropertyBlock(_block);
            }
        }

        private static Vector3 Centre(Renderer[] renderers, Vector3 fallback)
        {
            bool any = false;
            var b = new Bounds();
            foreach (Renderer r in renderers)
            {
                if (r == null) continue;
                if (!any) { b = r.bounds; any = true; }
                else b.Encapsulate(r.bounds);
            }
            return any ? b.center : fallback;
        }
    }

    /// <summary>
    /// Every enabled <see cref="MechanismView"/> and the chapter they bind to. Views add themselves on enable (in whatever
    /// scene and order they load); the GameHost gives the registry its chapter's mechanisms by ID (<see cref="Attach"/>), binds
    /// views as they arrive, samples them after each Core step and places them each frame. One per game (static: views and the
    /// host live in different scenes).
    /// </summary>
    public static class MechanismViewRegistry
    {
        private static readonly List<MechanismView> _views = new List<MechanismView>(64);
        private static Dictionary<string, IMechanism> _live, _rest;
        private static Func<bool> _calm;

        /// <summary>The enabled views (bound or not).</summary>
        public static IReadOnlyList<MechanismView> Views => _views;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        private static void ResetStatics()
        {
            _views.Clear();
            _live = _rest = null;
            _calm = null;
        }

        internal static void Add(MechanismView v)
        {
            if (!_views.Contains(v)) _views.Add(v);
            if (_live != null) Bind(v);
        }

        internal static void Remove(MechanismView v) => _views.Remove(v);

        /// <summary>
        /// The chapter's mechanisms: <paramref name="live"/> (the running sim's) and <paramref name="rest"/> (a sim at the
        /// chapter's first checkpoint, the authored state), both keyed by mechanism ID. Binds every waiting view.
        /// </summary>
        public static void Attach(Dictionary<string, IMechanism> live, Dictionary<string, IMechanism> rest, Func<bool> calm)
        {
            _live = live;
            _rest = rest;
            _calm = calm;
            for (int i = 0; i < _views.Count; i++) Bind(_views[i]);
        }

        public static void Detach()
        {
            _live = _rest = null;
        }

        private static void Bind(MechanismView v)
        {
            if (v.Bound || v.Failed) return;
            string id = v.MechanismId ?? "";
            if (!_live.TryGetValue(id, out IMechanism live) || !_rest.TryGetValue(id, out IMechanism rest))
            {
                Debug.LogWarning("[MechanismView] " + v.name + ": no mechanism '" + id + "' in this chapter; the node stays as authored.", v);
                v.TryBind(null, null, _calm);                                   // marks it failed
                return;
            }
            v.TryBind(live, rest, _calm);
        }

        /// <summary>After each Core step.</summary>
        public static void Sample()
        {
            for (int i = 0; i < _views.Count; i++) if (_views[i].Bound) _views[i].Sample();
        }

        /// <summary>After a respawn or continue.</summary>
        public static void Snap()
        {
            for (int i = 0; i < _views.Count; i++) if (_views[i].Bound) _views[i].Snap();
        }

        /// <summary>Each rendered frame.</summary>
        public static void Apply(float alpha)
        {
            for (int i = 0; i < _views.Count; i++) if (_views[i].Bound) _views[i].Apply(alpha);
        }
    }
}
