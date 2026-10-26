using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;

namespace DeadLetter.Core.Motor
{
    /// <summary>
    /// D-17's motor: a deterministic, fixed-step port of the prototype's <c>updatePlayer</c> (index.html L1931–L2067)
    /// with its mantle (L1906–L1947), holds (L2318–L2361, L4683–L4735) and acts (L1837–L1900, L4380–L4469, L3601–L3625,
    /// L5655–L5684). Kinematic and plane-constrained (DL-01 §7–§8): position is (X, Y) on the lane plus a depth Z used
    /// only when an act steps into the set (Unity sign: + is into the set). Clips play in place; the motor moves him.
    ///
    /// Each <see cref="Step"/> takes one <see cref="MotorInput"/>, queries <see cref="IMotorWorld"/>, and leaves position,
    /// velocity, facing, yaw, <see cref="State"/>, the clip to play (<see cref="Clip"/>, <see cref="ClipTimeScale"/>,
    /// <see cref="ClipTime"/>) and this step's <see cref="Events"/>. Act timing is read from Core's own clip clock in clip
    /// frames (<see cref="ClipTimings"/>), never from the Animator (port_architecture §3.3).
    ///
    /// Deliberate differences from the prototype (port_architecture §3.1, §9 #10: dt-approximate integration is not
    /// ported): gravity is integrated exactly (the jump apex is JUMP_APEX at any step), and release friction is an exact
    /// decay equal to the prototype's at 60 Hz. Scene-specific branches (regions, transits, rides, belts, triggers) are
    /// not here; they belong to the scene/mechanism systems that drive this motor.
    /// </summary>
    public sealed class D17Motor
    {
        private sealed class Act
        {
            public Verb Verb;
            public bool Shove;
            public ActPhase Phase;
            public IInteractable Target;
            public double StandX, ApproachZ, InZ;
            public int Face;
            public bool Turn, Crouch;
            public string ClipName;
            public double T, PrevFrame;
            public double TargetX, BaseY;
            public bool Done1, Seated;

            public void Reset()
            {
                Verb = Verb.None; Shove = false; Phase = ActPhase.None; Target = null;
                StandX = ApproachZ = InZ = 0; Face = 0; Turn = Crouch = false; ClipName = null;
                T = PrevFrame = 0; TargetX = BaseY = 0; Done1 = Seated = false;
            }

            public bool Active => Verb != Verb.None || Shove;
        }

        private readonly MotorConfig _c;
        private readonly IMotorWorld _w;
        private readonly InteractionResolver _r;
        private readonly List<MotorEvent> _events = new List<MotorEvent>(16);
        private readonly Act _act = new Act();

        // Mantle
        private bool _mantling;
        private double _mT, _mX0, _mY0, _mTop, _mExtra;
        private int _mDir;

        // Holds
        private int _holdSide;
        private double _pushFrom, _shove;
        private bool _atLip;

        private bool _hasYawOverride;
        private double _yawOverride;
        private double _lastStepPhase;

        public D17Motor(MotorConfig config, IMotorWorld world, InteractionResolver resolver = null)
        {
            _c = config ?? throw new ArgumentNullException(nameof(config));
            _w = world ?? throw new ArgumentNullException(nameof(world));
            _r = resolver;
            Clip = ClipNames.Idle;
            ClipTimeScale = 1;
        }

        public MotorConfig Config => _c;

        // ---- Output -------------------------------------------------------------------------------------------------------
        public double X { get; private set; }
        public double Y { get; private set; }
        /// <summary>Depth off the lane (Unity sign: + into the set).</summary>
        public double Z { get; private set; }
        public double Vx { get; private set; }
        public double Vy { get; private set; }
        public Vec2 Position => new Vec2(X, Y);
        public Vec2 Velocity => new Vec2(Vx, Vy);
        /// <summary>+1 facing +x, −1 facing −x.</summary>
        public int Facing { get; private set; } = 1;
        /// <summary>
        /// Body yaw in the prototype's convention (L7579): +π/2 faces +x, −π/2 faces −x, π faces into the set, 0 faces the
        /// camera. Unity Y rotation in degrees = 180 − Yaw·180/π. Turns at 8 rad/s; acts wait for it.
        /// </summary>
        public double Yaw { get; private set; } = Math.PI / 2;
        public bool Grounded { get; private set; } = true;
        public bool Crouched { get; private set; }
        public double Coyote { get; private set; }
        public double JumpBuffer { get; private set; }
        public double LandTimer { get; private set; }
        public double PeakY { get; private set; }
        public HoldKind Hold { get; private set; }
        public ICarryable Carried { get; private set; }
        public IPushable Pushed { get; private set; }
        /// <summary>0 → 1 over Lift f22–f26: how far the item has moved from its rest to his hands (L4419).</summary>
        public double CarryBlend { get; private set; }
        /// <summary>Clip to play (an Animator state name), its speed multiplier and seconds since it started.</summary>
        public string Clip { get; private set; }
        public double ClipTimeScale { get; private set; }
        public double ClipFade { get; private set; }
        public double ClipTime { get; private set; }
        /// <summary>Increments on every clip change, so a view can crossfade exactly once per change.</summary>
        public int ClipSerial { get; private set; }
        public long StepCount { get; private set; }
        public Verb ActVerb => _act.Shove ? Verb.None : _act.Verb;
        public ActPhase ActPhase => _act.Phase;
        public bool IsMantling => _mantling;
        public bool IsActing => _act.Active;
        /// <summary>Events of the last step only (cleared at the start of each step).</summary>
        public IReadOnlyList<MotorEvent> Events => _events;

        // ---- Settings other systems change ---------------------------------------------------------------------------
        /// <summary>Auto-run (default on, L8283). The Run input inverts it.</summary>
        public bool AutoRun { get; set; } = true;
        /// <summary>Pace zones (L2077–L2083): when &gt; 0, his top speed is this and he plays SadWalk.</summary>
        public double SlowWalkLimit { get; set; }
        /// <summary>Near the White's water no auto-run (L1925–L1926); set by the White's system.</summary>
        public bool Careful { get; set; }

        public MotorState State
        {
            get
            {
                if (_mantling) return MotorState.Mantling;
                if (_act.Active)
                {
                    if (_act.Verb == Verb.Present) return MotorState.Presenting;
                    if (_act.Verb == Verb.Sit) return MotorState.Sitting;
                    return MotorState.Acting;
                }
                if (Hold == HoldKind.Push) return MotorState.Pushing;
                if (Hold == HoldKind.Item && Carried != null && !Carried.IsLight) return MotorState.Carrying;
                if (!Grounded) return MotorState.Airborne;
                return Crouched ? MotorState.Crouched : MotorState.Grounded;
            }
        }

        /// <summary>Puts him at rest, standing on the lane at (x, y). Clears holds, acts and timers.</summary>
        public void Place(double x, double y, int facing = 1)
        {
            X = x; Y = y; Z = 0; Vx = Vy = 0;
            Facing = facing >= 0 ? 1 : -1;
            Yaw = Facing * Math.PI / 2;
            Grounded = true; Crouched = false;
            Coyote = JumpBuffer = LandTimer = 0; PeakY = y;
            Hold = HoldKind.None; Carried = null; Pushed = null; CarryBlend = 0;
            _mantling = false; _act.Reset(); _hasYawOverride = false; _shove = 0; _atLip = false;
            SetClip(ClipNames.Idle, 0, 1);
            _events.Clear();
        }

        /// <summary>What Use would do now, without doing it (for glints and hints, §4.19).</summary>
        public bool PreviewUse(out Candidate candidate)
        {
            candidate = default;
            return _r != null && _r.Resolve(Query(), out candidate);
        }

        public InteractionQuery Query()
            => new InteractionQuery(X, Y, Z, Facing, Grounded, _mantling || _act.Active, Hold, Carried, Pushed);

        // ---- The step -------------------------------------------------------------------------------------------------------
        /// <summary>Advances one fixed step (the pipeline's step 4, port_architecture §3.1).</summary>
        public void Step(in MotorInput input, double dt)
        {
            if (!(dt > 0) || double.IsInfinity(dt)) throw new ArgumentOutOfRangeException(nameof(dt));
            _events.Clear();
            StepCount++;

            double move = double.IsNaN(input.Move) ? 0 : Smooth.Clamp(input.Move, -1, 1);
            if (input.JumpPressed) JumpBuffer = _c.JumpBuffer;                         // L1935
            JumpBuffer = Math.Max(0, JumpBuffer - dt);                                // L1936

            if (_mantling) StepMantle(dt);
            else if (_act.Active) StepAct(input, move, dt);
            else StepFree(input, move, dt);

            // updateCharacter (L7579–L7583): yaw turns toward ±π/2 or the act's override.
            double targetYaw = _hasYawOverride ? _yawOverride : (Facing > 0 ? Math.PI / 2 : -Math.PI / 2);
            Yaw = Smooth.MoveTowards(Yaw, targetYaw, _c.YawRate * dt);

            // The mixer advances after the step; acts read this clock on the next step (actions.X.time * FPS).
            ClipTime += dt * ClipTimeScale;
        }

        // ---- Free movement: updatePlayer L1950–L2067 ----------------------------------------------------------------------
        private void StepFree(in MotorInput input, double move, double dt)
        {
            // Back to the lane after an act that stepped off it (L4876, L5796).
            if (Hold != HoldKind.Push && Z != 0) Z = Smooth.MoveTowards(Z, 0, _c.StepInSpeed * dt);

            if (input.UsePressed && _r != null && _r.Resolve(Query(), out var use))   // L1956–L1957
            {
                BeginUse(use);
                return;
            }

            bool lightCarry = Hold == HoldKind.Item && Carried != null && Carried.IsLight;   // L1967–L1969
            if (Hold == HoldKind.Push) { StepPush(input, move, dt); return; }
            if (Hold == HoldKind.Item && !lightCarry) { StepCarry(move, dt); return; }

            if (move != 0) Facing = Smooth.Sign(move);
            double clearance = LaneProbe.MinCeiling(_w, X - _c.ClearanceBack, X + Facing * _c.ClearanceAhead, Y) - Y;   // L1973
            if (Grounded)
            {
                if (!Crouched && (clearance < _c.CrouchBelow || input.CrouchHeld)) Crouched = true;              // L1975
                else if (Crouched && !input.CrouchHeld && clearance > _c.StandAbove) Crouched = false;          // L1976
            }
            bool slow = SlowWalkLimit > 0;
            bool run = WantsRun(input, move) && !slow && !lightCarry;
            double top = Crouched ? _c.CrouchWalk : slow ? SlowWalkLimit : run ? _c.Run : _c.Walk;
            double target = Smooth.Sign(move) * top * Math.Min(1, Math.Abs(move) * _c.StickGain);             // L1981
            double acc = Grounded ? (run ? _c.AccelGroundRun : _c.AccelGroundWalk) : _c.AccelAir;              // L1982
            Vx = Smooth.MoveTowards(Vx, target, acc * dt);
            if (move == 0 && Grounded) Vx *= Smooth.DecayFactor(_c.ReleaseFriction, dt);                        // L1984

            // Jump (coyote + buffer); near a ledge too high to hop, climb it instead (L1986–L1996).
            Coyote = Grounded ? _c.Coyote : Math.Max(0, Coyote - dt);
            if (JumpBuffer > 0 && Grounded && (move == 0 || Smooth.Sign(move) == Facing))
            {
                if (_w.LedgeAhead(X, Y, Facing, _c.MantleScanStanding, _c.StepUp, out var l)
                    && l.Top - Y > _c.MantleMin && l.Top - Y <= _c.MantleMax && l.Distance < _c.FaceDistance + _c.MantleReachExtra)
                {
                    JumpBuffer = 0;
                    StartMantle(l);
                    return;
                }
            }
            if (JumpBuffer > 0 && Coyote > 0 && !Crouched)
            {
                Vy = _c.JumpVelocity; Grounded = false; Coyote = 0; JumpBuffer = 0;
                SetClip(ClipNames.JumpAir, 0.08, 1);
                Emit(MotorEventKind.Jump, null, Vy);
            }

            // Integrate and collide along x (L1998–L2010).
            _w.Limits(X, Y, out double left, out double right);
            double nx = Smooth.Clamp(X + Vx * dt, left, right);
            int dir = Smooth.Sign(nx - X);
            if (dir != 0)
            {
                double lead = nx + dir * _c.Half;
                if (_w.SurfaceAt(lead, Y) > Y + (_w.IsRamp(lead) ? _c.StepUpRamp : _c.StepUp)) { nx = X; Vx = 0; }
            }
            if (!Grounded || Crouched)
            {
                if (LaneProbe.MinCeiling(_w, nx - _c.CeilingBlockProbe, nx + _c.CeilingBlockProbe, Y) - Y < _c.CrouchHeight) nx = X;
            }
            X = nx;

            // Vertical (L2012–L2034). Gravity is integrated exactly: y += vy·dt − ½g·dt², vy −= g·dt.
            double support = LaneProbe.SupportAt(_w, X, Y, _c.Foot);
            if (!Grounded)
            {
                Y += Vy * dt - 0.5 * _c.Gravity * dt * dt;
                Vy -= _c.Gravity * dt;
                double ceil = _w.CeilingAt(X, Y);
                if (Vy > 0 && Y + _c.StandHeight > ceil) { Vy = 0; Y = ceil - _c.StandHeight; Emit(MotorEventKind.Bonk, null, 0); }
                if (Clip == ClipNames.JumpAir && Vy < _c.FallClipVy && PeakY - Y > _c.FallClipDrop && Hold == HoldKind.None)
                    SetClip(ClipNames.Fall, 0.22, 1);
                // Catch a ledge edge mid-air (L2021–L2022).
                if (_w.LedgeAhead(X, Y, Facing, _c.MantleScanAir, _c.StepUp, out var la) && Vy < _c.MantleAirMaxVy
                    && la.Top - Y > _c.MantleMin && la.Top - Y <= _c.MantleMax + _c.MantleAirExtra)
                {
                    StartMantle(la);
                    return;
                }
                if (Y <= support)
                {
                    double fall = PeakY - support;
                    Y = support; Vy = 0; Grounded = true;
                    LandTimer = fall > _c.HardLandingDrop ? _c.LandTimerHard : _c.LandTimerSoft;
                    SetClip(ClipNames.Land, 0.06, 1);
                    Emit(MotorEventKind.Land, null, fall);
                    if (fall > _c.ShakeDrop) Emit(MotorEventKind.Shake, null, _c.ShakeAmount);
                    if (fall > _c.HardLandingDrop) Emit(MotorEventKind.Noise, null, _c.NoiseAmount);
                }
                PeakY = Math.Max(PeakY, Y);
            }
            else if (Y > support + 0.001 && Y - support < _c.SlopeSnap && Vy <= 0)
            {
                Y = support;                                    // down a stair or a slope: stay on it
            }
            else if (Y > support + 0.001)
            {
                Grounded = false; Vy = 0; PeakY = Y;            // walked off an edge
                SetClip(ClipNames.JumpAir, 0.12, 1);
            }
            else Y = support;
            if (Grounded) PeakY = Y;

            // Ground animation (L2052–L2064).
            if (Grounded)
            {
                LandTimer -= dt;
                if (LandTimer <= 0)
                {
                    double speed = Math.Abs(Vx);
                    bool moving = speed > _c.MovingSpeed;
                    if (lightCarry) SetClip(moving ? ClipNames.CarryWalk : ClipNames.CarryIdle, 0.22, moving ? Math.Max(_c.CarryMinTimeScale, speed / _c.ClipSpeedCarryWalk) : 1);
                    else if (Crouched) SetClip(moving ? ClipNames.CrouchWalk : ClipNames.CrouchIdle, 0.22, moving ? speed / _c.ClipSpeedCrouchWalk : 1);
                    else if (slow) SetClip(moving ? ClipNames.SadWalk : ClipNames.Idle, 0.3, moving ? Math.Max(_c.CarryMinTimeScale, speed / _c.ClipSpeedSadWalk) : 1);
                    else if (speed > _c.RunClipSpeed) SetClip(ClipNames.Run, 0.18, speed / _c.ClipSpeedRun);
                    else SetClip(moving ? ClipNames.Walk : ClipNames.Idle, 0.22, moving ? Math.Max(_c.WalkMinTimeScale, speed / _c.ClipSpeedWalk) : 1);
                }
                Footsteps();
            }
        }

        /// <summary><c>wantsRun</c>, L1921–L1929.</summary>
        private bool WantsRun(in MotorInput input, double move)
        {
            bool modifier = input.RunModifierHeld;
            if (Careful && AutoRun) return false;
            if (input.MoveIsAnalog && move != 0) return Math.Abs(move) > _c.StickRunThreshold ? AutoRun != modifier : false;
            return AutoRun != modifier;
        }

        // ---- Mantle: startMantle / mantleAt, L1906–L1919, L1938–L1949 ----------------------------------------------
        private void StartMantle(in Ledge l)
        {
            _mantling = true;
            _mT = 0; _mX0 = X; _mY0 = Y; _mDir = Facing; _mTop = l.Top;
            _mExtra = Math.Max(0, l.Distance - _c.FaceDistance);
            Vx = 0; Vy = 0;
            SetClip(ClipNames.Mantle, 0.1, 1);
            Emit(MotorEventKind.MantleStart, null, l.Top - Y);
        }

        private void StepMantle(double dt)
        {
            _mT += dt;
            double f = _mT * _c.Fps;
            MotorConfig.MantleAt(f, out double fwd, out double frac);
            double approach = Smooth.Step(f / _c.MantleApproachFrames);
            X = _mX0 + _mDir * (fwd + _mExtra * approach);
            Y = _mY0 + frac * (_mTop - _mY0);
            if (ClipClock.Reached(f, ClipTimings.MantleEvents.End))
            {
                _mantling = false; Grounded = true; Y = _mTop; PeakY = Y;
                SetClip(Hold == HoldKind.Item ? ClipNames.CarryIdle : ClipNames.Idle, 0.25, 1);
                Emit(MotorEventKind.MantleEnd, null, 0);
            }
        }

        // ---- Heavy carry: updateHold, L2318–L2361 (the not-pushing branch) -------------------------------------------
        private void StepCarry(double move, double dt)
        {
            if (move != 0) Facing = Smooth.Sign(move);
            double target = Smooth.Sign(move) * _c.CarryWalk * Math.Min(1, Math.Abs(move) * _c.StickGain);
            Vx = Smooth.MoveTowards(Vx, target, _c.AccelCarry * dt);
            if (move == 0) Vx *= Smooth.DecayFactor(_c.ReleaseFriction, dt);
            _w.Limits(X, Y, out double left, out double right);
            double nx = Smooth.Clamp(X + Vx * dt, left, right);
            int dir = Smooth.Sign(nx - X);
            if (dir != 0 && _w.SurfaceAt(nx + dir * _c.Half, Y) > Y + _c.StepUp) nx = X;
            if (Math.Abs(nx - X) < 1e-6) Vx = 0;
            X = nx;
            Y = LaneProbe.SupportAt(_w, X, Y, _c.Foot);
            double speed = Math.Abs(Vx);
            if (speed > _c.MovingSpeed) SetClip(ClipNames.CarryWalk, 0.2, Math.Max(_c.CarryMinTimeScale, speed / _c.ClipSpeedCarryWalk));
            else SetClip(ClipNames.CarryIdle, 0.25, 1);
            Footsteps();
        }

        // ---- Push / pull / drag: updateHoldCh1, L4683–L4735 ----------------------------------------------------------
        private void StepPush(in MotorInput input, double move, double dt)
        {
            var p = Pushed;
            double max = p.Max;
            bool tips = p.TipsIntoPit;
            bool atLip = tips && Math.Abs(p.X - max) < _c.PushLipTolerance;
            if (input.JumpPressed) { ReleasePush(atLip); return; }                    // L4688

            Facing = _holdSide;
            double target = Smooth.Sign(move) * p.Speed * Math.Min(1, Math.Abs(move) * _c.StickGain);
            Vx = Smooth.MoveTowards(Vx, target, _c.AccelPush * dt);
            if (move == 0) Vx *= Smooth.DecayFactor(_c.ReleaseFriction, dt);
            _w.Limits(X, Y, out double left, out double right);
            double nx = Smooth.Clamp(X + Vx * dt, left, right);
            double tx = Smooth.Clamp(nx + p.Side * p.Gap, p.Min, max);
            nx = tx - p.Side * p.Gap;
            if (nx < left || nx > right) { nx = X; tx = p.X; }
            p.MoveTo(tx, (tx - p.X) / Math.Max(dt, 1e-4));
            if (Math.Abs(nx - X) < 1e-6) Vx = 0;
            X = nx;
            Y = LaneProbe.SupportAt(_w, X, Y, _c.Foot);
            double speed = Math.Abs(Vx);
            if (speed > _c.MovingSpeed)
                SetClip(ClipNames.PushWalk, 0.2, (Smooth.Sign(Vx) == _holdSide ? 1 : -1) * Math.Max(_c.PushMinTimeScale, speed / _c.ClipSpeedPushWalk));
            else SetClip(ClipNames.PushIdle, 0.25, 1);
            Footsteps();

            if (tips)
            {
                _atLip = atLip;
                p.SetAtLip(atLip);
                _shove = atLip && move != 0 && Smooth.Sign(move) == p.Side ? _shove + dt : 0;
                if (_shove > _c.ShoveTime)
                {
                    Hold = HoldKind.None; Pushed = null; Vx = 0; _shove = 0; _atLip = false;
                    p.OnShoved();
                    Emit(MotorEventKind.Released, "shove", 1);
                    _act.Reset(); _act.Shove = true; _act.Phase = ActPhase.Clip;
                    SetClip(ClipNames.Nudge, 0.12, 1);
                }
                return;
            }
            if (p.HasDetents)
            {
                bool moved = Math.Abs(p.X - _pushFrom) > _c.DetentMove;
                if (moved && (Math.Abs(p.X - max) < _c.PushLipTolerance || Math.Abs(p.X - p.Min) < _c.PushLipTolerance))
                {
                    Vx = 0;
                    ReleaseTo(p, false, 0.3);
                }
                return;
            }
            if (Math.Abs(p.X - max) < _c.PushLipTolerance)
            {
                Vx = 0;
                ReleaseTo(p, false, 0.3);
                p.OnTravelEnd();
            }
        }

        private void ReleasePush(bool tip)
        {
            var p = Pushed;
            if (p == null) { Hold = HoldKind.None; return; }
            ReleaseTo(p, tip, 0.25);
        }

        private void ReleaseTo(IPushable p, bool tip, double fade)
        {
            Hold = HoldKind.None; Pushed = null; _shove = 0; _atLip = false;
            SetClip(ClipNames.Idle, fade, 1);
            p.OnReleased(tip);
            Emit(MotorEventKind.Released, null, tip ? 1 : 0);
        }

        // ---- Acts: beginUse / beginCh1 / updateActCh1 ------------------------------------------------------------------
        private void BeginUse(in Candidate c)
        {
            Vx = 0;                                                                     // L4308
            if (c.Verb == Verb.Release) { ReleasePush(_atLip); return; }               // L4309–L4313

            _act.Reset();
            _act.Verb = c.Verb;
            _act.Target = c.Target;
            _act.StandX = c.StandX;
            _act.Face = c.Face;
            _act.ApproachZ = Z;
            _act.InZ = Z;
            _act.Phase = ActPhase.Approach;
            Emit(MotorEventKind.ActStart, c.Verb.ToString(), 0);

            switch (c.Verb)
            {
                case Verb.SetDown:
                {
                    // Never refuse (L4340–L4353): no approach, straight into the clip.
                    PlaceSearch.Find(_w, _c, X, Y, Facing, Carried.Radius, out double tx, out double baseY, out int face);
                    Facing = face;
                    _act.TargetX = tx; _act.BaseY = baseY; _act.Face = face;
                    EnterClip(ClipNames.SetDown, 0.15);
                    break;
                }
                case Verb.Grab:
                    _act.ApproachZ = ((IPushable)c.Target).Z;                         // approachCh1(a, dt, a.p.z), L4461
                    break;
                case Verb.Sit:
                    _act.ApproachZ = c.StandZ;                                          // L5655
                    break;
                case Verb.Present:
                    _act.Turn = true; _act.InZ = c.StandZ; _act.ClipName = ClipNames.Present;
                    break;
                case Verb.Place:
                {
                    var pt = (IPlaceTarget)c.Target;
                    _act.Turn = pt.TurnIntoSet; _act.InZ = c.StandZ; _act.ClipName = pt.Clip ?? ClipNames.SetDown;
                    break;
                }
                case Verb.Use:
                {
                    var prof = ((IUsable)c.Target).Profile;
                    _act.Turn = prof.TurnIntoSet; _act.Crouch = prof.Crouch; _act.InZ = c.StandZ; _act.ClipName = prof.Clip;
                    break;
                }
            }
        }

        private void EnterClip(string clip, double fade)
        {
            _act.Phase = ActPhase.Clip;
            _act.T = 0;
            _act.PrevFrame = 0;
            SetClip(clip, fade, 1);
        }

        private void StepAct(in MotorInput input, double move, double dt)
        {
            var a = _act;
            a.T += dt;

            if (a.Shove)
            {
                if (a.T > _c.ShoveActTime) EndAct(false);                              // L4518
                return;
            }

            switch (a.Phase)
            {
                case ActPhase.Approach: StepApproach(dt); return;
                case ActPhase.Turn:
                    if (Math.Abs(Yaw - Math.PI) < _c.TurnTolerance) a.Phase = ActPhase.StepIn;   // L3606
                    else SetClip(ClipNames.Walk, 0.2, 0.6);
                    return;
                case ActPhase.StepIn:
                {
                    double dz = a.InZ - Z;
                    if (Math.Abs(dz) < _c.ArriveZ) { Z = a.InZ; EnterClip(a.ClipName, 0.2); return; }   // L3609–L3613
                    Z += Smooth.Sign(dz) * Math.Min(Math.Abs(dz), _c.StepInSpeed * dt);
                    SetClip(ClipNames.Walk, 0.2, _c.StepInSpeed / _c.ClipSpeedWalk);
                    return;
                }
                case ActPhase.StepOut:
                {
                    double dz = -Z;
                    if (Math.Abs(dz) < _c.ArriveZ) { Z = 0; EndAct(true); return; }
                    Z += Smooth.Sign(dz) * Math.Min(Math.Abs(dz), _c.StepInSpeed * dt);
                    SetClip(ClipNames.Walk, 0.2, -_c.StepInSpeed / _c.ClipSpeedWalk);
                    return;
                }
                case ActPhase.SitUp:
                    if (a.T > _c.SitUpTime) EndAct(false);                             // L5681
                    return;
                case ActPhase.Clip:
                    break;
                default:
                    EndAct(false);
                    return;
            }

            double f = ClipTime * _c.Fps;
            double prev = a.PrevFrame;
            a.PrevFrame = f;
            switch (a.Verb)
            {
                case Verb.Lift: ClipLift(f, prev); break;
                case Verb.SetDown: ClipSetDown(f); break;
                case Verb.Place: ClipPlace(f); break;
                case Verb.Grab: ClipGrab(f); break;
                case Verb.Present: ClipPresent(f, prev); break;
                case Verb.Sit: ClipSit(move, input.JumpPressed); break;
                case Verb.Use:
                {
                    var u = (IUsable)a.Target;
                    if (u.OnActFrame(new ActFrame(prev, f, a.T, input))) FinishClip();
                    break;
                }
                default: EndAct(false); break;
            }
        }

        /// <summary><c>approachCh1</c>, L4378–L4388 (and updateAct's approach, L1841–L1860).</summary>
        private void StepApproach(double dt)
        {
            var a = _act;
            if (a.Face != 0) Facing = a.Face;
            if (a.Crouch) Crouched = true;
            double dx = a.StandX - X, dz = a.ApproachZ - Z;
            if (dz != 0) Z += Smooth.Sign(dz) * Math.Min(Math.Abs(dz), _c.StepInSpeed * dt);
            if (Math.Abs(dx) < _c.ArriveX && Math.Abs(dz) < _c.ArriveZ)
            {
                X = a.StandX;
                Arrived();
                return;
            }
            double v = (Crouched ? _c.CrouchWalk : _c.Walk) * _c.ApproachFactor;
            X += Smooth.Sign(dx) * Math.Min(Math.Abs(dx), v * dt);
            SetClip(Crouched ? ClipNames.CrouchWalk : ClipNames.Walk, 0.15, v / (Crouched ? _c.ClipSpeedCrouchWalk : _c.ClipSpeedWalk));
        }

        private void Arrived()
        {
            var a = _act;
            switch (a.Verb)
            {
                case Verb.Lift: EnterClip(ClipNames.Lift, 0.15); return;                 // L4415
                case Verb.Grab: EnterClip(ClipNames.Grab, 0.12); return;                 // L4464
                case Verb.Sit:
                    _hasYawOverride = false;
                    if (a.Face != 0) Facing = a.Face;
                    EnterClip(ClipNames.Sit, 0.2);                                       // L5659
                    return;
                default:
                    if (a.Turn) { _hasYawOverride = true; _yawOverride = Math.PI; a.Phase = ActPhase.Turn; }
                    else a.Phase = ActPhase.StepIn;
                    return;
            }
        }

        private void ClipLift(double f, double prev)
        {
            var it = (ICarryable)_act.Target;
            if (ClipClock.Crossed(prev, f, ClipTimings.LiftEvents.Sound)) Emit(MotorEventKind.ActEvent, "sound", f);
            if (ClipClock.Reached(f, ClipTimings.LiftEvents.Attach))
            {
                if (!_act.Done1)
                {
                    _act.Done1 = true;
                    it.OnLifted();
                    Emit(MotorEventKind.PickedUp, "attach", f);
                }
                CarryBlend = Smooth.Step((f - ClipTimings.LiftEvents.Attach) / ClipTimings.LiftEvents.AttachBlend);
            }
            if (ClipClock.Reached(f, ClipTimings.LiftEvents.Carry))
            {
                Hold = HoldKind.Item; Carried = it; CarryBlend = 1;
                EndActKeepingClip();
                SetClip(ClipNames.CarryIdle, 0.2, 1);
            }
        }

        private void ClipSetDown(double f)
        {
            var it = Carried;
            if (ClipClock.Reached(f, ClipTimings.SetDownEvents.Release) && !_act.Done1)
            {
                _act.Done1 = true;
                it?.OnSetDown(_act.TargetX, _act.BaseY);
                CarryBlend = 0;
                Emit(MotorEventKind.SetDown, "release", f);
            }
            if (ClipClock.Reached(f, ClipTimings.SetDownEvents.Done))
            {
                Hold = HoldKind.None; Carried = null;
                EndAct(false);
            }
        }

        private void ClipPlace(double f)
        {
            var pt = (IPlaceTarget)_act.Target;
            if (ClipClock.Reached(f, ClipTimings.SetDownEvents.Release) && !_act.Done1)
            {
                _act.Done1 = true;
                pt.OnPlaced(Carried);
                CarryBlend = 0;
                Emit(MotorEventKind.Placed, "release", f);
            }
            if (ClipClock.Reached(f, ClipTimings.SetDownEvents.Done))
            {
                Hold = HoldKind.None; Carried = null;
                FinishClip();
            }
        }

        private void ClipGrab(double f)
        {
            if (!ClipClock.Reached(f, ClipTimings.GrabEvents.Hold)) return;            // L4467
            var p = (IPushable)_act.Target;
            Hold = HoldKind.Push; Pushed = p; _holdSide = p.Side; _pushFrom = p.X; _shove = 0; _atLip = false;
            EndActKeepingClip();
            SetClip(ClipNames.PushIdle, 0.15, 1);
            Emit(MotorEventKind.Grabbed, null, p.X);
        }

        private void ClipPresent(double f, double prev)
        {
            var t = (IPresentTarget)_act.Target;
            if (ClipClock.Crossed(prev, f, ClipTimings.PresentEvents.Lamp0)) Beat(t, PresentBeat.Lamp0, "lamp0", f);
            if (ClipClock.Crossed(prev, f, ClipTimings.PresentEvents.Lamp1)) Beat(t, PresentBeat.Lamp1, "lamp1", f);
            if (ClipClock.Crossed(prev, f, ClipTimings.PresentEvents.Lamp2)) Beat(t, PresentBeat.Lamp2, "lamp2", f);
            if (ClipClock.Crossed(prev, f, ClipTimings.PresentEvents.Nobody)) Beat(t, PresentBeat.Nobody, "nobody", f);
            if (ClipClock.Crossed(prev, f, ClipTimings.PresentEvents.Forward)) Beat(t, PresentBeat.Forward, "forward", f);
            if (ClipClock.Reached(f, ClipTimings.PresentEvents.Out)) FinishClip();
        }

        private void Beat(IPresentTarget t, PresentBeat beat, string name, double f)
        {
            t.OnPresentBeat(beat);
            Emit(MotorEventKind.ActEvent, name, f);
        }

        /// <summary>Sit, L5673–L5682: SitIdle after 0.66 s, seated after 0.4 s, any move after 1.0 s gets up (0.6 s).</summary>
        private void ClipSit(double move, bool jumpPressed)
        {
            var a = _act;
            var seat = (ISeat)a.Target;
            if (a.T > _c.SitIdleAfter && Clip != ClipNames.SitIdle) SetClip(ClipNames.SitIdle, 0.3, 1);
            bool seated = a.T > _c.SitSeatedAfter;
            if (seated != a.Seated)
            {
                a.Seated = seated;
                seat.OnSeated(seated);
                Emit(seated ? MotorEventKind.Seated : MotorEventKind.Stood, null, 0);
            }
            if ((move != 0 || jumpPressed) && a.T > _c.SitCanStandAfter)
            {
                if (a.Seated) { a.Seated = false; seat.OnSeated(false); Emit(MotorEventKind.Stood, null, 0); }
                a.Phase = ActPhase.SitUp;
                a.T = 0;
                SetClip(ClipNames.SitUp, 0.15, 1);
            }
        }

        /// <summary>After the clip: step back out to the lane if he stepped in, else finish.</summary>
        private void FinishClip()
        {
            if (Math.Abs(Z) >= _c.ArriveZ) _act.Phase = ActPhase.StepOut;
            else { Z = 0; EndAct(true); }
        }

        private void EndAct(bool restoreFacing)
        {
            var a = _act;
            if (restoreFacing && a.Face != 0) Facing = a.Face;
            if (a.Crouch) Crouched = false;
            EndActKeepingClip();
            SetClip(ClipNames.Idle, 0.3, 1);
        }

        private void EndActKeepingClip()
        {
            var verb = _act.Shove ? "Shove" : _act.Verb.ToString();
            _hasYawOverride = false;
            _act.Reset();
            Emit(MotorEventKind.ActEnd, verb, 0);
        }

        // ---- Animation clock --------------------------------------------------------------------------------------------
        /// <summary>The prototype's <c>setClip</c>, L1597–L1605: same clip → only the speed changes.</summary>
        private void SetClip(string name, double fade, double timeScale)
        {
            if (Clip == name) { ClipTimeScale = timeScale; return; }
            Clip = name; ClipFade = fade; ClipTimeScale = timeScale; ClipTime = 0;
            ClipSerial++;
            _lastStepPhase = 0;
            Emit(MotorEventKind.ClipChanged, name, fade);
        }

        /// <summary><c>stepSounds</c>, L2069–L2075: a footstep at each half cycle of a walking clip.</summary>
        private void Footsteps()
        {
            double loud;
            switch (Clip)
            {
                case ClipNames.Walk: loud = 1; break;
                case ClipNames.CrouchWalk: loud = 0.6; break;
                case ClipNames.Run: loud = 1.2; break;
                case ClipNames.CarryWalk: loud = 1.1; break;
                case ClipNames.PushWalk: loud = 0.8; break;
                case ClipNames.SadWalk: loud = 0.7; break;
                default: return;
            }
            double loopFrames = ClipTimings.LoopFramesOf(Clip);
            if (loopFrames <= 0) return;
            double d = loopFrames / _c.Fps;
            double ph = ((ClipTime / d) % 1 + 1) % 1;
            if ((_lastStepPhase < 0.5 && ph >= 0.5) || ph < _lastStepPhase - 0.5)
                Emit(MotorEventKind.Footstep, Clip, loud * (Crouched ? 0.6 : 1));
            _lastStepPhase = ph;
        }

        private void Emit(MotorEventKind kind, string name, double value) => _events.Add(new MotorEvent(kind, name, value));
    }
}
