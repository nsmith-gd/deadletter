using DeadLetter.Core.Camera;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Motor;
using DeadLetter.Runtime.Settings;
using Unity.Cinemachine;
using UnityEngine;

namespace DeadLetter.Runtime.Camera
{
    /// <summary>
    /// Applies Core's <see cref="CameraRig"/> to the scene camera (port_architecture §4.17). The rig steps on every Core
    /// step (<see cref="D17Controller.Stepped"/>), so it is deterministic and in lockstep with D-17; the rendered pose is
    /// interpolated between the last two steps.
    /// <para><b>Cinemachine:</b> the pose is written to a <see cref="CinemachineCamera"/> that has <b>no Position or
    /// Rotation Control</b> behaviours (so Cinemachine keeps its transform as is) and no damping, and the lens field of
    /// view is set from the focal length. The Brain then owns output, blends to other cameras and impulse; Core owns the
    /// framing and shot blending (1.4 in / 0.8 out, cue-clock dt) for parity. With no CinemachineCamera assigned the
    /// Unity <c>Camera</c> transform and FOV are written directly (same result; use that for tests and tools).</para>
    /// Positions convert at this edge only: Unity = (x, y, −z) (§0.2).
    /// <para><b>Bound mode</b> (U-20): with a scene host, Core's scene simulator steps the rig as step #10 of its pipeline
    /// (opening move included); <see cref="BindRig"/> makes this component only read <see cref="CameraRig.Pose"/> after each
    /// step and render it, interpolated.</para>
    /// </summary>
    [DisallowMultipleComponent]
    [DefaultExecutionOrder(-100)]   // before CinemachineBrain's LateUpdate
    public sealed class LaneCameraDriver : MonoBehaviour
    {
        [SerializeField] private D17Controller player;
        [SerializeField] private DirectedMomentPlayer moments;
        [Tooltip("Preferred. Leave empty to drive targetCamera directly.")]
        [SerializeField] private CinemachineCamera cinemachineCamera;
        [SerializeField] private UnityEngine.Camera targetCamera;
        [Tooltip("Write RenderSettings.fogDensity (ExponentialSquared) from the framing (U-15 may own this instead).")]
        [SerializeField] private bool driveFog = true;
        [Tooltip("Accessibility: no camera shake. The player's calm-mode option (SettingsStore.Calm) also disables it.")]
        [SerializeField] private bool calm;

        private CameraRig _rig;
        private bool _bound;
        private readonly FramingSignalTable _signals = new FramingSignalTable();
        private CameraPose _prev, _curr;
        private bool _hasPose;

        /// <summary>Scene rules publish framing signals here (dl02, dl02.reveal, …).</summary>
        public FramingSignalTable Signals => _signals;
        public CameraRig Rig => _rig;

        /// <summary>Set by scene/transit rules; see <see cref="CameraRigInput"/>.</summary>
        public bool InTransitOrExit { get; set; }
        public bool TransitStage0 { get; set; }
        public bool SlowFollow { get; set; }
        public bool LookingUpWell { get; set; }
        public bool Realising { get; set; }

        /// <summary>Swap the framing track when a chapter's scene definitions load.</summary>
        public void SetTrack(FramingTrack track)
        {
            _rig = new CameraRig(CameraConfig.Prototype, track);
            _bound = false;
            _hasPose = false;
        }

        /// <summary>Render a rig that Core steps (the scene simulator's); this component no longer steps it.</summary>
        public void BindRig(CameraRig rig)
        {
            _rig = rig ?? throw new System.ArgumentNullException(nameof(rig));
            _bound = true;
            _hasPose = false;
        }

        /// <summary>The viewport aspect, for Core's framing (the runner's <c>Aspect</c>).</summary>
        public double Aspect => targetCamera != null ? targetCamera.aspect : 16.0 / 9.0;

        public void Shake(float amount) => _rig?.Shake(amount, calm || SettingsStore.Calm);

        /// <summary>Checkpoint load / respawn: jump to the frame (L8115).</summary>
        public void Snap()
        {
            if (_bound && _rig != null) { _curr = _prev = _rig.Pose; _hasPose = true; return; }
            if (_rig == null || player == null) return;
            CameraRigInput i = BuildInput();
            _rig.SnapToFrame(i);
            _curr = _prev = _rig.Step(i, 0);
            _hasPose = true;
        }

        private void Awake()
        {
            if (_rig == null) SetTrack(PrologueFraming.Build());
            if (targetCamera == null) targetCamera = UnityEngine.Camera.main;
        }

        private void OnEnable() { if (player != null) player.Stepped += OnStep; }
        private void OnDisable() { if (player != null) player.Stepped -= OnStep; }

        private void OnStep(double dt)
        {
            if (_bound)
            {
                _prev = _hasPose ? _curr : _rig.Pose;
                _curr = _rig.Pose;
                _hasPose = true;
                return;
            }
            CameraRigInput i = BuildInput();
            _prev = _hasPose ? _curr : _rig.Pose;
            _curr = _rig.Step(i, dt);
            if (!_hasPose) { _prev = _curr; _hasPose = true; }
        }

        private CameraRigInput BuildInput()
        {
            D17Motor m = player.Motor;
            CameraPush push = CameraPush.None;
            if (m.IsMantling) push = CameraPush.Mantle;
            else if (m.IsActing && m.ActPhase != ActPhase.Approach && m.ActVerb != Verb.Grab && m.ActVerb != Verb.Quirk) push = CameraPush.Act;   // quirks do not push in (L7788)
            else if (Realising) push = CameraPush.Realise;
            else if (TransitStage0) push = CameraPush.Transit;
            return new CameraRigInput
            {
                X = m.X, Y = m.Y, Vx = m.Vx, Facing = m.Facing,
                NoLead = InTransitOrExit || m.Hold != HoldKind.None,
                Push = push,
                SlowFollow = SlowFollow,
                LookingUpWell = LookingUpWell,
                Aspect = targetCamera != null ? targetCamera.aspect : 16.0 / 9.0,
                Signals = _signals,
                Shot = moments != null ? moments.CurrentShot(m.X, m.Y) : null,
            };
        }

        private void LateUpdate()
        {
            if (!_hasPose || _rig == null) return;
            float a = player != null ? player.RenderAlpha : 1f;
            Vector3 pos = Vector3.Lerp(ToUnity(_prev.Position), ToUnity(_curr.Position), a);
            Vector3 look = Vector3.Lerp(ToUnity(_prev.Look), ToUnity(_curr.Look), a);
            double focal = _prev.Focal + (_curr.Focal - _prev.Focal) * a;
            float aspect = targetCamera != null ? targetCamera.aspect : 16f / 9f;
            float fov = (float)_rig.Config.VerticalFovDegrees(focal, aspect);
            Vector3 fwd = look - pos;
            Quaternion rot = fwd.sqrMagnitude > 1e-8f ? Quaternion.LookRotation(fwd, Vector3.up) : Quaternion.identity;

            if (cinemachineCamera != null)
            {
                cinemachineCamera.transform.SetPositionAndRotation(pos, rot);
                LensSettings lens = cinemachineCamera.Lens;
                lens.FieldOfView = fov;
                cinemachineCamera.Lens = lens;
            }
            else if (targetCamera != null)
            {
                targetCamera.transform.SetPositionAndRotation(pos, rot);
                targetCamera.fieldOfView = fov;
            }

            if (driveFog && !double.IsNaN(_curr.Fog))
            {
                RenderSettings.fog = true;
                RenderSettings.fogMode = FogMode.ExponentialSquared;
                RenderSettings.fogDensity = (float)_curr.Fog;
            }
        }

        private static Vector3 ToUnity(Vec3 v)
        {
            Vec3 u = v.ToUnity();
            return new Vector3((float)u.X, (float)u.Y, (float)u.Z);
        }
    }
}
