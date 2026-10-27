using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Settings;
using DeadLetter.Core.Simulation;
using DeadLetter.Runtime.Settings;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.Controls;

namespace DeadLetter.Runtime
{
    /// <summary>
    /// Thin Unity adapter for the Core <see cref="D17Motor"/>: reads the Gameplay action map, ticks the motor at a fixed
    /// 60 Hz from Update (Time.deltaTime through <see cref="FixedTick"/>'s accumulator, independent of Unity's 50 Hz
    /// default fixed step), answers the motor's lane probes with physics casts at a
    /// fixed z, and places the transform and drives the Animator from Core's state (render-interpolated). It decides
    /// nothing: every outcome is Core's (port_architecture §2 "Rules").
    ///
    /// Scene setup: D-17's own colliders must be on a layer outside <see cref="groundMask"/> and <see cref="ceilingMask"/>.
    /// Standable geometry and walls go in groundMask; undersides he can bump or crouch under go in ceilingMask; ramp
    /// colliders also go in rampMask (step-up 0.45 there).
    /// </summary>
    [DisallowMultipleComponent]
    public sealed class D17Controller : MonoBehaviour, IMotorWorld
    {
        public const double StepSeconds = 1.0 / 60.0;

        [Header("Input")]
        [SerializeField] private InputActionAsset actions;
        [SerializeField] private string actionMap = "Gameplay";

        [Header("Animation")]
        [SerializeField] private Animator animator;

        [Header("Lane")]
        [Tooltip("World z of the lane plane.")]
        [SerializeField] private float laneZ;
        [Tooltip("Lane limits for the body centre (prototype LEFT_LIMIT / RIGHT_LIMIT, L303).")]
        [SerializeField] private float leftLimit = -0.3f;
        [SerializeField] private float rightLimit = 11.45f;
        [SerializeField] private LayerMask groundMask = ~0;
        [SerializeField] private LayerMask ceilingMask;
        [SerializeField] private LayerMask rampMask;
        [Tooltip("Ground probes start this far above his feet; anything taller reads as a wall.")]
        [SerializeField] private float probeAbove = 2.0f;
        [SerializeField] private float probeBelow = 6.0f;
        [SerializeField] private float probeUp = 8.0f;

        [Header("Motor")]
        [Tooltip("Used only when there is no SettingsStore; otherwise the player's auto-run option wins (U-17).")]
        [SerializeField] private bool autoRun = true;

        private D17Motor _motor;
        private FixedTick _tick;
        private InteractionResolver _resolver;
        private InputActionMap _map;
        private InputAction _move, _jump, _crouch, _use, _run, _pause;
        private bool _jumpLatched, _useLatched;
        private Vector3 _prevPos, _currPos;
        private float _prevYaw, _currYaw;
        private int _lastClipSerial = -1;
        private bool _hasClipSpeed, _hasSpeed, _hasVy, _hasGrounded, _hasCrouched, _hasCarrying, _hasPushing, _hasState, _hasCarryBlend;

        /// <summary>The Core motor (read-only use from views; never write its state from Runtime).</summary>
        public D17Motor Motor => _motor;

        /// <summary>Mechanism and item views register their Core interactables here (U-10).</summary>
        public InteractionResolver Resolver => _resolver;

        /// <summary>Every motor event, after each Core step (sound, shake, noise, clip events).</summary>
        public event Action<MotorEvent> MotorEventRaised;

        /// <summary>Pause pressed (U-17 owns the pause card).</summary>
        public event Action PauseRequested;

        /// <summary>
        /// Gates each step's input before the motor sees it (U-13: a directed moment withholds control,
        /// <c>DirectedMomentPlayer</c>). Null = pass through.
        /// </summary>
        public Func<MotorInput, MotorInput> InputFilter { get; set; }

        /// <summary>Raised after each Core step with the step length (camera rig, cue-driven systems).</summary>
        public event Action<double> Stepped;

        /// <summary>Simulation time: Core steps × step length.</summary>
        public double SimTime => _motor != null ? _motor.StepCount * StepSeconds : 0;

        /// <summary>Render interpolation factor between the last two Core steps (as used for the transform).</summary>
        public float RenderAlpha => _tick == null ? 1f : Mathf.Clamp01((float)_tick.Alpha);

        private void Awake()
        {
            var config = MotorConfig.Prototype();
            _resolver = new InteractionResolver(config);
            _motor = new D17Motor(config, this, _resolver) { AutoRun = SettingsStore.Loaded ? SettingsStore.Current.AutoRun : autoRun };
            _tick = new FixedTick(StepSeconds, 4);

            Vector3 p = transform.position;
            _motor.Place(p.x, p.y, 1);
            _currPos = _prevPos = CorePosition();
            _currYaw = _prevYaw = CoreYawDegrees();

            if (animator == null) animator = GetComponentInChildren<Animator>();
            if (animator != null)
            {
                animator.applyRootMotion = false;   // clips are in place; Core moves him (DL-01 §7)
                CacheAnimatorParams();
            }

            if (actions != null)
            {
                _map = actions.FindActionMap(actionMap, true);
                _move = _map.FindAction("Move", true);
                _jump = _map.FindAction("Jump", true);
                _crouch = _map.FindAction("Crouch", false);
                _use = _map.FindAction("Use", true);
                _run = _map.FindAction("Run", false);
                _pause = _map.FindAction("Pause", false);
            }
            else Debug.LogWarning("D17Controller: no InputActionAsset assigned; D-17 will not respond to input.", this);
        }

        private void OnEnable()
        {
            _map?.Enable();
            SettingsStore.Applied += OnSettingsApplied;
        }

        private void OnDisable()
        {
            SettingsStore.Applied -= OnSettingsApplied;
            _map?.Disable();
            _jumpLatched = _useLatched = false;
        }

        private void Update()
        {
            // Edge events are latched here and consumed by the next Core step (L8527), so a press between two fixed
            // steps is never lost and never counted twice.
            if (_jump != null && _jump.WasPressedThisFrame()) _jumpLatched = true;
            if (_use != null && _use.WasPressedThisFrame()) _useLatched = true;
            if (_pause != null && _pause.WasPressedThisFrame()) PauseRequested?.Invoke();

            // Core ticks at its own 60 Hz from the render frame's delta, not from FixedUpdate: Unity's default fixed
            // step is 50 Hz, which would step Core 1,1,1,1,2 and leave nothing to interpolate (judder). The lane probes
            // are raycasts against static colliders, so stepping outside the physics loop is safe. If moving colliders
            // are ever added to groundMask/ceilingMask, call Physics.SyncTransforms() before this loop (or enable
            // Physics.autoSyncTransforms) so the probes see their current poses.
            int steps = _tick.Advance(Time.deltaTime);
            for (int i = 0; i < steps; i++)
            {
                MotorInput input = ReadInput();
                if (InputFilter != null) input = InputFilter(input);
                _jumpLatched = _useLatched = false;
                _prevPos = _currPos;
                _prevYaw = _currYaw;
                _motor.Step(input, _tick.StepSeconds);
                _currPos = CorePosition();
                _currYaw = CoreYawDegrees();
                var events = _motor.Events;
                if (MotorEventRaised != null)
                    for (int e = 0; e < events.Count; e++) MotorEventRaised(events[e]);
                Stepped?.Invoke(_tick.StepSeconds);
            }
        }

        private void LateUpdate()
        {
            // Render interpolation between the last two Core steps.
            float alpha = RenderAlpha;   // = _tick.Alpha: leftover time into the next Core step
            transform.SetPositionAndRotation(
                Vector3.Lerp(_prevPos, _currPos, alpha),
                Quaternion.Euler(0f, Mathf.LerpAngle(_prevYaw, _currYaw, alpha), 0f));
            DriveAnimator();
        }

        /// <summary>U-17: the options' auto-run toggle ("Auto-run (hold Shift or B to walk)", L170) → D17Motor.AutoRun.</summary>
        private void OnSettingsApplied(GameSettings s)
        {
            if (_motor != null) _motor.AutoRun = s.AutoRun;
        }

        private MotorInput ReadInput()
        {
            var input = new MotorInput();
            if (_map == null) return input;

            float axis = _move.ReadValue<float>();
            InputControl ctl = _move.activeControl;
            bool analog = ctl != null && ctl.parent is StickControl;
            input.Move = analog ? MotorInput.FromStick(axis, _motor.Config.StickDeadzone) : Mathf.Clamp(axis, -1f, 1f);
            input.MoveIsAnalog = analog && input.Move != 0;
            input.JumpPressed = _jumpLatched;
            input.JumpHeld = _jump.IsPressed();
            input.UsePressed = _useLatched;
            input.UseHeld = _use.IsPressed();
            input.RunModifierHeld = _run != null && _run.IsPressed();
            input.CrouchHeld = _crouch != null && _crouch.IsPressed();
            return input;
        }

        private Vector3 CorePosition() => new Vector3((float)_motor.X, (float)_motor.Y, laneZ + (float)_motor.Z);

        /// <summary>Core yaw (π/2 = +x, π = into the set) → Unity Y angle (90° = +x, 0° = +z into the set).</summary>
        private float CoreYawDegrees() => 180f - (float)(_motor.Yaw * (180.0 / Math.PI));

        // ---- Animator -------------------------------------------------------------------------------------------------
        private void CacheAnimatorParams()
        {
            foreach (var p in animator.parameters)
            {
                if (p.nameHash == D17AnimatorParams.ClipSpeedId) _hasClipSpeed = true;
                else if (p.nameHash == D17AnimatorParams.SpeedId) _hasSpeed = true;
                else if (p.nameHash == D17AnimatorParams.VerticalSpeedId) _hasVy = true;
                else if (p.nameHash == D17AnimatorParams.GroundedId) _hasGrounded = true;
                else if (p.nameHash == D17AnimatorParams.CrouchedId) _hasCrouched = true;
                else if (p.nameHash == D17AnimatorParams.CarryingId) _hasCarrying = true;
                else if (p.nameHash == D17AnimatorParams.PushingId) _hasPushing = true;
                else if (p.nameHash == D17AnimatorParams.StateId) _hasState = true;
                else if (p.nameHash == D17AnimatorParams.CarryBlendId) _hasCarryBlend = true;
            }
        }

        private void DriveAnimator()
        {
            if (animator == null || !animator.isActiveAndEnabled) return;
            if (_motor.ClipSerial != _lastClipSerial)
            {
                _lastClipSerial = _motor.ClipSerial;
                int state = Animator.StringToHash(_motor.Clip);
                if (animator.HasState(0, state))
                    animator.CrossFadeInFixedTime(state, (float)_motor.ClipFade, 0, Mathf.Max(0f, (float)_motor.ClipTime));
            }
            if (_hasClipSpeed) animator.SetFloat(D17AnimatorParams.ClipSpeedId, (float)_motor.ClipTimeScale);
            if (_hasSpeed) animator.SetFloat(D17AnimatorParams.SpeedId, Mathf.Abs((float)_motor.Vx));
            if (_hasVy) animator.SetFloat(D17AnimatorParams.VerticalSpeedId, (float)_motor.Vy);
            if (_hasGrounded) animator.SetBool(D17AnimatorParams.GroundedId, _motor.Grounded);
            if (_hasCrouched) animator.SetBool(D17AnimatorParams.CrouchedId, _motor.Crouched);
            if (_hasCarrying) animator.SetBool(D17AnimatorParams.CarryingId, _motor.Hold == HoldKind.Item);
            if (_hasPushing) animator.SetBool(D17AnimatorParams.PushingId, _motor.Hold == HoldKind.Push);
            if (_hasState) animator.SetInteger(D17AnimatorParams.StateId, (int)_motor.State);
            if (_hasCarryBlend) animator.SetFloat(D17AnimatorParams.CarryBlendId, (float)_motor.CarryBlend);
        }

        // ---- IMotorWorld: physics probes in the lane ------------------------------------------------------------------
        public double SurfaceAt(double x, double refY)
        {
            var origin = new Vector3((float)x, (float)(refY + probeAbove), laneZ);
            // Starting inside something taller than the probe: report the probe top (a wall).
            if (Physics.CheckSphere(origin, 0.001f, groundMask, QueryTriggerInteraction.Ignore)) return origin.y;
            if (Physics.Raycast(origin, Vector3.down, out RaycastHit hit, probeAbove + probeBelow, groundMask, QueryTriggerInteraction.Ignore))
                return hit.point.y;
            return LaneProbe.NoGround;
        }

        public double CeilingAt(double x, double refY)
        {
            if (ceilingMask.value == 0) return LaneProbe.NoCeiling;
            var origin = new Vector3((float)x, (float)refY + 0.01f, laneZ);
            if (Physics.Raycast(origin, Vector3.up, out RaycastHit hit, probeUp, ceilingMask, QueryTriggerInteraction.Ignore))
                return hit.point.y;
            return LaneProbe.NoCeiling;
        }

        public void Limits(double x, double y, out double left, out double right)
        {
            left = leftLimit;
            right = rightLimit;
        }

        public bool IsRamp(double x)
        {
            if (rampMask.value == 0) return false;
            var origin = new Vector3((float)x, (float)(_motor.Y + probeAbove), laneZ);
            return Physics.Raycast(origin, Vector3.down, probeAbove + 1f, rampMask, QueryTriggerInteraction.Ignore);
        }

        public bool LedgeAhead(double x, double y, int dir, double range, double stepUp, out Ledge ledge)
            => LaneProbe.ScanLedge(this, x, y, dir, range, stepUp, out ledge);

#if UNITY_EDITOR
        private void OnDrawGizmosSelected()
        {
            Gizmos.color = new Color(1f, 0.8f, 0.3f, 0.6f);
            Gizmos.DrawLine(new Vector3(leftLimit, transform.position.y, laneZ), new Vector3(rightLimit, transform.position.y, laneZ));
        }
#endif
    }
}
