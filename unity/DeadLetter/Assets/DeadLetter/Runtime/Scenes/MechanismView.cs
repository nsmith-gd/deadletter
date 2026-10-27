using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Scenes;
using UnityEngine;

namespace DeadLetter.Runtime.Scenes
{
    /// <summary>
    /// Mirrors Core mechanism state onto one art node (a <c>MECH_&lt;Type&gt;_&lt;scene&gt;_&lt;name&gt;[__part]</c> object,
    /// docs/unity/asset_conventions.md) every rendered frame (§4.13l: views read state, never decide). One generic
    /// component: the scene definition's <see cref="MechanismViewDef"/>s say which value moves the node and how, and the
    /// Editor's SceneBuilder copies them into <see cref="channels"/>. Values come from <see cref="MechanismReadout"/>,
    /// so what a view shows is tested headless.
    /// <para>Composition: from the node's rest pose (captured on first bind), rotations about their pivots in channel
    /// order, then translations; emission scales the node's renderers' rest emission colour.</para>
    /// <para>Not interpolated: mechanism motion is slow next to 60 Hz; D-17 and the camera are.</para>
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class MechanismView : MonoBehaviour
    {
        [Serializable]
        public struct Channel
        {
            [Tooltip("Mechanism ID read, e.g. dl01.shutter.")]
            public string source;
            public ViewChannel channel;
            public int index;
            public ViewMotion motion;
            public float scale;
            public float offset;
            [Tooltip("Rotation pivot in world (= lane) space; off = the node's own origin at rest.")]
            public bool hasPivot;
            public Vector3 pivot;
        }

        [SerializeField] private SceneHost host;
        [Tooltip("The mechanism ID this node belongs to (from its MECH_ name).")]
        [SerializeField] private string mechanismId;
        [SerializeField] private Channel[] channels = new Channel[0];

        private IMechanism[] _sources;
        private bool _bound, _failed;
        private Vector3 _restPos;
        private Quaternion _restRot;
        private Renderer[] _renderers;
        private Color[] _restEmission;
        private MaterialPropertyBlock _block;
        private static readonly int EmissionColor = Shader.PropertyToID("_EmissionColor");   // URP Lit

        public string MechanismId => mechanismId;

        /// <summary>Editor (SceneBuilder): configure from the scene definition.</summary>
        public void Configure(SceneHost sceneHost, string id, Channel[] viewChannels)
        {
            host = sceneHost;
            mechanismId = id;
            channels = viewChannels ?? new Channel[0];
        }

        /// <summary>A definition's view channel as serialized data.</summary>
        public static Channel From(MechanismViewDef d) => new Channel
        {
            source = d.ReadFrom.Value,
            channel = d.Channel,
            index = d.Index,
            motion = d.Motion,
            scale = (float)d.Scale,
            offset = (float)d.Offset,
            hasPivot = !double.IsNaN(d.Pivot.X),
            pivot = double.IsNaN(d.Pivot.X) ? Vector3.zero : new Vector3((float)d.Pivot.X, (float)d.Pivot.Y, (float)d.Pivot.Z),
        };

        private void LateUpdate()
        {
            if (!_bound && !Bind()) return;
            Vector3 pos = _restPos;
            Quaternion rot = _restRot;
            for (int i = 0; i < channels.Length; i++)
            {
                if (channels[i].motion != ViewMotion.RotateZ) continue;
                float deg = Value(i);
                Vector3 p = channels[i].hasPivot ? channels[i].pivot : _restPos;
                Quaternion q = Quaternion.AngleAxis(deg, Vector3.forward);    // about lane z: same sign as three.js rotation.z (§0.2)
                pos = p + q * (pos - p);
                rot = q * rot;
            }
            for (int i = 0; i < channels.Length; i++)
            {
                switch (channels[i].motion)
                {
                    case ViewMotion.TranslateX: pos.x += Value(i); break;
                    case ViewMotion.TranslateY: pos.y += Value(i); break;
                    case ViewMotion.Emission: SetEmission(Value(i)); break;
                }
            }
            transform.SetPositionAndRotation(pos, rot);
        }

        private float Value(int i)
        {
            Channel c = channels[i];
            return (float)((MechanismReadout.Read(_sources[i], c.channel, c.index) + c.offset) * c.scale);
        }

        private bool Bind()
        {
            if (_failed || host == null || host.Runner == null) return false;
            _sources = new IMechanism[channels.Length];
            for (int i = 0; i < channels.Length; i++)
            {
                if (!host.Runner.Graph.TryGet(channels[i].source, out IMechanism m) || !MechanismReadout.Supports(m, channels[i].channel))
                {
                    Debug.LogWarning($"MechanismView {name}: no {channels[i].channel} on '{channels[i].source}' in {host.Runner.Definition.Id}.", this);
                    _failed = true;
                    return false;
                }
                _sources[i] = m;
            }
            _restPos = transform.position;
            _restRot = transform.rotation;
            _renderers = GetComponentsInChildren<Renderer>();
            _restEmission = new Color[_renderers.Length];
            for (int i = 0; i < _renderers.Length; i++)
            {
                Material mat = _renderers[i].sharedMaterial;
                _restEmission[i] = mat != null && mat.HasProperty(EmissionColor) ? mat.GetColor(EmissionColor) : Color.black;
            }
            _block = new MaterialPropertyBlock();
            _bound = true;
            return true;
        }

        /// <summary>
        /// Lamp brightness: the rest emission × value. UNVERIFIED in the Editor: needs the material's <c>_EMISSION</c>
        /// keyword on (ArtMaterials sets it for emitting materials, PR #24); a lamp authored dark stays dark (U-15's
        /// light pool should own lamp glow).
        /// </summary>
        private void SetEmission(float value)
        {
            for (int i = 0; i < _renderers.Length; i++)
            {
                _renderers[i].GetPropertyBlock(_block);
                _block.SetColor(EmissionColor, _restEmission[i] * value);
                _renderers[i].SetPropertyBlock(_block);
            }
        }
    }
}
