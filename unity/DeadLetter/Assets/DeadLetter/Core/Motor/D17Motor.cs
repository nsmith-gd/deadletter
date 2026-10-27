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
    /// ported): gravity is integrated exactly (the apex is the same at any step; by default the launch speed
    /// is lowered so it matches the 60 Hz prototype's 0.377 m, see <see cref="MotorConfig.JumpMode"/>), and release friction is an exact
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
            /// <summary>Seconds since the act started, or since its current clip started (EnterClip resets it).</summary>
            public double T, PrevFrame;
            /// <summary>Seconds since the act started (never reset).</summary>
            public double Total;
            public double TargetX, BaseY;
            public bool Done1, Seated;
            /// <summary>0 = the profile's clip; +1 per chained clip or hop.</summary>
            public int Part;
            // Hop (board, alight, a station's chained hop): from, to, tracking a ride's pose.
            public double FromX, FromY, FromZ, ToX, ToY, ToZ;
            public bool TrackRide, TookOff, Landed;
            public int Token;
            // Quirk / flinch.
            public bool Cancel;
            public double HoldFor, CancelAfter, EndAfter, EndAt;
            // Stuck / death.
            public DeathKind Death;
            public double Hold;
            public bool Flinched, Cut;
            // Escorted.
            public EscortWalk Walk;

            public void Reset()
            {
                Verb = Verb.None; Shove = false; Phase = ActPhase.None; Target = null;
                StandX = ApproachZ = InZ = 0; Face = 0; Turn = Crouch = false; ClipName = null;
                T = PrevFrame = Total = 0; TargetX = BaseY = 0; Done1 = Seated = false; Part = 0;
                FromX = FromY = FromZ = ToX = ToY = ToZ = 0; TrackRide = TookOff = Landed = false; Token = 0;
                Cancel = false; HoldFor = CancelAfter = EndAfter = EndAt = double.NaN;
                Death = DeathKind.Fall; Hold = 0; Flinched = Cut = false; Walk = default;
            }

            public bool Active => Verb != Verb.None || Shove;
        }

        private readonly MotorConfig _c;
        private readonly IMotorWorld _w;
        private readonly InteractionResolver _r;
        private readonly ILaneConveyor _conveyor;
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

        // Riding (board / ride / alight)
        private int _rideToken;
        /// <summary>How many of <see cref="_events"/> the last Step emitted (the rest came from calls since).</summary>
        private int _stepEvents;

        public D17Motor(MotorConfig config, IMotorWorld world, InteractionResolver resolver = null)
        {
            _c = config ?? throw new ArgumentNullException(nameof(config));
            _w = world ?? throw new ArgumentNullException(nameof(world));
            _r = resolver;
            _conveyor = world as ILaneConveyor;
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
        /// <summary>What the current act is on (the station, item, pushable, seat, ride, hide spot), or null (no act, a quirk, stuck, death, escorted, the shove).</summary>
        public IInteractable ActTarget => _act.Active ? _act.Target : null;
        /// <summary>0 for the act's first clip, +1 per follow-up clip or hop a station chained (<see cref="ActStep"/>).</summary>
        public int ActPart => _act.Part;
        public bool IsMantling => _mantling;
        public bool IsActing => _act.Active;
        /// <summary>In the hide act (<c>game.act.what === 'hide'</c>, any phase; L5973): <c>PlayerPose.Hiding</c>.</summary>
        public bool IsHiding => _act.Verb == Verb.Hide;
        /// <summary>In the escorted act (L6126–L6134): <c>PlayerPose.Escorted</c>.</summary>
        public bool IsEscorted => _act.Verb == Verb.Escorted;
        /// <summary>In the death act (the clip holds, then the cut).</summary>
        public bool IsDead => _act.Verb == Verb.Death;
        /// <summary>What he rides (<c>game.riding</c>), or null.</summary>
        public IRide Ride { get; private set; }
        public int RideToken => _rideToken;
        /// <summary>A quirk's own hold after its clip (<c>a.holdFor</c>; NaN = the default), for the label shot's ease (L3740).</summary>
        public double QuirkHoldFor => _act.Verb == Verb.Quirk ? _act.HoldFor : double.NaN;
        /// <summary>
        /// Events of the last step, followed by any emitted since by calls between steps (a scene rule's
        /// <see cref="BeginStuck"/>, <see cref="Die"/>, <see cref="PlayQuirk"/>, <see cref="BeginEscort"/>); those are also
        /// reported with the next step. Cleared at the start of each step.
        /// </summary>
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
                    if (_act.Verb == Verb.Death) return MotorState.Dead;
                    return MotorState.Acting;
                }
                if (Ride != null) return MotorState.Riding;
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
            Ride = null; _rideToken = 0;
            SetClip(ClipNames.Idle, 0, 1);
            _events.Clear();
            _stepEvents = 0;
        }

        /// <summary>What Use would do now, without doing it (for glints and hints, §4.19).</summary>
        public bool PreviewUse(out Candidate candidate)
        {
            candidate = default;
            return _r != null && _r.Resolve(Query(), out candidate);
        }

        public InteractionQuery Query()
            => new InteractionQuery(X, Y, Z, Facing, Grounded, _mantling || _act.Active || Ride != null, Hold, Carried, Pushed);

        // ---- The step -------------------------------------------------------------------------------------------------------
        /// <summary>Advances one fixed step (the pipeline's step 4, port_architecture §3.1).</summary>
        public void Step(in MotorInput input, double dt)
        {
            if (!(dt > 0) || double.IsInfinity(dt)) throw new ArgumentOutOfRangeException(nameof(dt));
            _events.RemoveRange(0, _stepEvents);                                    // keep what calls since the last step emitted
            StepCount++;

            double move = double.IsNaN(input.Move) ? 0 : Smooth.Clamp(input.Move, -1, 1);
            if (input.JumpPressed) JumpBuffer = _c.JumpBuffer;                         // L1935
            JumpBuffer = Math.Max(0, JumpBuffer - dt);                                // L1936

            if (_mantling) StepMantle(dt);
            else if (_act.Active) StepAct(input, move, dt);
            else if (Ride != null) StepRide(input);
            else StepFree(input, move, dt);

            // updateCharacter (L7579–L7583): yaw turns toward ±π/2 or the act's override.
            double targetYaw = _hasYawOverride ? _yawOverride : (Facing > 0 ? Math.PI / 2 : -Math.PI / 2);
            Yaw = Smooth.MoveTowards(Yaw, targetYaw, _c.YawRate * dt);

            // The mixer advances after the step; acts read this clock on the next step (actions.X.time * FPS).
            ClipTime += dt * ClipTimeScale;
            _stepEvents = _events.Count;
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

            // A standing jump beside something he can board hops him on (L1964–L1966).
            if (input.JumpPressed && move == 0 && Grounded && Hold == HoldKind.None && _r != null && _r.ResolveBoard(Query(), out var board))
            {
                JumpBuffer = 0;
                BeginUse(board);
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

            // Integrate and collide along x (L1998–L2010); on a belt he is carried while he walks (L1998, L2006).
            double carry = Grounded && _conveyor != null ? _conveyor.CarryAt(X, Y) * dt : 0;
            _w.Limits(X, Y, out double left, out double right);
            double nx = Smooth.Clamp(X + Vx * dt, left, right);
            int dir = Smooth.Sign(nx - X);
            if (dir != 0)
            {
                double lead = nx + dir * _c.Half;
                if (_w.SurfaceAt(lead, Y) > Y + (_w.IsRamp(lead) ? _c.StepUpRamp : _c.StepUp)) { nx = X; Vx = 0; }
            }
            if (carry != 0 && _w.SurfaceAt(nx + carry + Smooth.Sign(carry) * _c.Half, Y) <= Y + _c.StepUp)   // L2006
                nx = Smooth.Clamp(nx + carry, left, right);                                                   // (the walls hold: a port guard)
            if (!Grounded || Crouched)
            {
                if (LaneProbe.MinCeiling(_w, nx - _c.CeilingBlockProbe, nx + _c.CeilingBlockProbe, Y) - Y < _c.CrouchHeight) nx = X;
            }
            X = nx;

            // Vertical (L2012–L2034). Gravity is integrated exactly: y += vy·dt − ½g·dt², vy −= g·dt. In parity mode Vy is
            // the prototype's less ParityVelocityOffset (launches and falls from rest start lower by it), so heights match
            // its Euler step and thresholds compare the prototype's velocity (pvy).
            double support = LaneProbe.SupportAt(_w, X, Y, _c.Foot);
            if (!Grounded)
            {
                Y += Vy * dt - 0.5 * _c.Gravity * dt * dt;
                Vy -= _c.Gravity * dt;
                double pvy = Vy + _c.ParityVelocityOffset;
                double ceil = _w.CeilingAt(X, Y);
                if (pvy > 0 && Y + _c.StandHeight > ceil)                                                   // L2016
                {
                    Vy = _c.FallStartVelocity; pvy = 0; Y = ceil - _c.StandHeight;
                    Emit(MotorEventKind.Bonk, null, 0);
                }
                if (Clip == ClipNames.JumpAir && pvy < _c.FallClipVy && PeakY - Y > _c.FallClipDrop && Hold == HoldKind.None)
                    SetClip(ClipNames.Fall, 0.22, 1);
                // Catch a ledge edge mid-air (L2021–L2022).
                if (_w.LedgeAhead(X, Y, Facing, _c.MantleScanAir, _c.StepUp, out var la) && pvy < _c.MantleAirMaxVy
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
                Grounded = false; Vy = _c.FallStartVelocity; PeakY = Y;   // walked off an edge (vy = 0, L2032; M3: see FallStartVelocity)
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
            Vx = Smooth.MoveTowards(Vx, target, p.Accel * dt);                         // L4690 (1.4), L2332 (3, 1.3)
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
            if (p.LetGoAtMax && Math.Abs(p.X - max) < _c.PushLipTolerance)
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

        /// <summary>
        /// He lets go of everything (<c>releaseHolds</c>, L7428–L7433; the escort's drop, L6399–L6400): a pushed thing is
        /// released where it is, a carried one rests at his feet on <paramref name="baseY"/>, a ride is left, a mantle ends.
        /// </summary>
        private void DropAll(double baseY)
        {
            if (Hold == HoldKind.Push && Pushed != null)
            {
                var p = Pushed;
                Hold = HoldKind.None; Pushed = null; _shove = 0; _atLip = false;
                p.OnReleased(false);
                Emit(MotorEventKind.Released, "drop", 0);
            }
            if (Hold == HoldKind.Item && Carried != null)
            {
                var it = Carried;
                Hold = HoldKind.None; Carried = null; CarryBlend = 0;
                it.OnSetDown(X, baseY);
                Emit(MotorEventKind.SetDown, "drop", 0);
            }
            Hold = HoldKind.None;
            if (Ride != null) LeaveRide("gone");
            _mantling = false;
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
                    var prof = ((IUsable)c.Target).ProfileFor(Query());                // turn and crouch from the first answer
                    _act.Turn = prof.TurnIntoSet; _act.Crouch = prof.Crouch; _act.InZ = c.StandZ; _act.ClipName = prof.Clip;
                    break;
                }
                case Verb.Hide:
                    _act.InZ = ((IHideSpot)c.Target).HideZ;                             // L6011: his own facing, the niche's centre
                    break;
                case Verb.Board:
                {
                    // Straight in: he turns to the rail as he hops (beginUse3 'board', L2875–L2880).
                    var ride = (IRide)c.Target;
                    _act.Token = c.Token;
                    ride.OnBoarding(c.Token);
                    _hasYawOverride = true; _yawOverride = Math.PI;
                    StartHop(X, Y, Z, true);
                    break;
                }
            }
        }

        private void EnterClip(string clip, double fade)
        {
            _act.Phase = ActPhase.Clip;
            _act.T = 0;
            _act.PrevFrame = 0;
            SetClip(clip, fade, 1, restart: true);
        }

        private void StepAct(in MotorInput input, double move, double dt)
        {
            var a = _act;
            a.T += dt;
            a.Total += dt;

            if (a.Shove)
            {
                if (a.T > _c.ShoveActTime) EndAct(false);                              // L4518
                return;
            }

            switch (a.Verb)
            {
                case Verb.Hide: StepHide(input, move, dt); return;
                case Verb.Escorted: StepEscorted(dt); return;
                case Verb.Stuck: StepStuck(); return;
                case Verb.Death: StepDeath(); return;
                case Verb.Quirk: StepQuirk(input, move); return;
                case Verb.Alight when a.Phase == ActPhase.Turn:
                    if (Math.Abs(Yaw) < _c.TurnTolerance) StartHop(X, Ride != null ? Ride.AlightY(_rideToken) : Y, 0, false);   // L2952
                    else SetClip(ClipNames.Ride, 0.2, 1);
                    return;
            }

            switch (a.Phase)
            {
                case ActPhase.Approach: StepApproach(dt); return;
                case ActPhase.Turn:
                    if (Math.Abs(Yaw - Math.PI) < _c.TurnTolerance) BeginStepIn();       // L3606; on the lane: the clip now (L1879)
                    else SetClip(ClipNames.Walk, 0.2, 0.6);
                    return;
                case ActPhase.StepIn:
                {
                    if (TryEnterStationClip()) return;                                         // L3609–L3613
                    double dz = a.InZ - Z;
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
                case ActPhase.Hop:
                    StepHop();
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
                    var step = u.OnActFrame(new ActFrame(prev, f, a.T, input, a.ClipName, a.Part));
                    switch (step.Kind)
                    {
                        case ActStepKind.Done: FinishClip(); break;
                        case ActStepKind.Then:                                         // e.g. latch Pull → Flinch (L1875)
                            a.Part++;
                            a.ClipName = step.Clip;
                            EnterClip(step.Clip, step.Fade);
                            Emit(MotorEventKind.ActEvent, step.Clip, f);
                            break;
                        case ActStepKind.Hop:                                          // e.g. DL-18's strap: a 0.4 m hop back
                        {
                            a.Part++;
                            double tx = step.Relative ? X + step.X : step.X;
                            double ty = double.IsNaN(step.Y) ? LaneProbe.SupportAt(_w, tx, Y, _c.Foot) : step.Y;
                            StartHop(tx, ty, step.Z, false);
                            break;
                        }
                    }
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
                case Verb.Hide:
                    _hasYawOverride = true; _yawOverride = 0;                            // backs in facing out, L6027
                    a.Phase = ActPhase.StepIn;
                    return;
                default:
                    if (a.Turn) { _hasYawOverride = true; _yawOverride = Math.PI; a.Phase = ActPhase.Turn; }
                    else BeginStepIn();                                                  // on the lane: the clip now (L1846–L1850)
                    return;
            }
        }

        /// <summary>
        /// Into the step-in phase. A station on the lane (already within <see cref="MotorConfig.ArriveZ"/> of its depth)
        /// starts its clip on this same step, as the prototype's does on the step he arrives (<c>updateAct</c>,
        /// L1846–L1850: the latch's Pull) or finishes turning (L1879: the crank). A station in the set starts it on the
        /// step he reaches its depth.
        /// </summary>
        private void BeginStepIn()
        {
            _act.Phase = ActPhase.StepIn;
            TryEnterStationClip();
        }

        /// <summary>At the station's depth: snap to it, ask the profile again (L3305, L2910) and start the clip. False while still stepping in.</summary>
        private bool TryEnterStationClip()
        {
            var a = _act;
            if (!(Math.Abs(a.InZ - Z) < _c.ArriveZ)) return false;
            Z = a.InZ;
            if (a.Verb == Verb.Use) a.ClipName = ((IUsable)a.Target).ProfileFor(Query()).Clip;   // asked again here
            EnterClip(a.ClipName, 0.2);
            return true;
        }

        // ---- Hop: board, alight, a chained hop (hopTo, L2884–L2894) -------------------------------------------------
        /// <summary>Starts the Hop clip from where he is toward (x, y, z); with <paramref name="trackRide"/> the target is the ride's pose each step.</summary>
        private void StartHop(double x, double y, double z, bool trackRide)
        {
            var a = _act;
            a.FromX = X; a.FromY = Y; a.FromZ = Z;
            a.ToX = x; a.ToY = y; a.ToZ = z;
            a.TrackRide = trackRide; a.TookOff = a.Landed = false;
            Vx = Vy = 0;
            EnterClip(ClipNames.Hop, 0.1);
            a.Phase = ActPhase.Hop;
        }

        private void StepHop()
        {
            var a = _act;
            double f = ClipTime * _c.Fps;
            if (a.TrackRide && a.Target is IRide ride && ride.RidePose(a.Token, out double rx, out double ry, out double rz))
            {
                a.ToX = rx; a.ToY = ry; a.ToZ = rz;                                       // the carrier keeps moving, L2949
            }
            double u = Smooth.Clamp((f - ClipTimings.HopEvents.TakeOff) / (ClipTimings.HopEvents.Land - ClipTimings.HopEvents.TakeOff), 0, 1);
            double k = Smooth.Step(u);
            X = a.FromX + (a.ToX - a.FromX) * k;
            Z = a.FromZ + (a.ToZ - a.FromZ) * k;
            Y = a.FromY + (a.ToY - a.FromY) * k + _c.HopArc * Math.Sin(Math.PI * u);
            if (!a.TookOff && ClipClock.Reached(f, ClipTimings.HopEvents.TakeOff)) { a.TookOff = true; Emit(MotorEventKind.ActEvent, "takeoff", f); }
            if (!a.Landed && ClipClock.Reached(f, ClipTimings.HopEvents.Land)) { a.Landed = true; Emit(MotorEventKind.ActEvent, "land", f); }
            if (!ClipClock.Reached(f, ClipTimings.HopEvents.Done)) return;

            X = a.ToX; Y = a.ToY; Z = a.ToZ; PeakY = Y; Grounded = true;
            switch (a.Verb)
            {
                case Verb.Board:                                                          // L2949–L2950
                {
                    var r = (IRide)a.Target;
                    int token = a.Token;
                    Ride = r; _rideToken = token;
                    r.OnMounted(token);
                    EndActKeepingClip();
                    _hasYawOverride = true; _yawOverride = Math.PI / 2; Facing = 1;
                    SetClip(ClipNames.Ride, 0.25, 1);
                    Emit(MotorEventKind.Mounted, null, token);
                    return;
                }
                case Verb.Alight:                                                         // L2953–L2957, L2973
                {
                    bool landing = Ride != null;
                    if (Ride != null) LeaveRide("landing");
                    EndActKeepingClip();
                    Facing = 1;
                    SetClip(ClipNames.Idle, 0.3, 1);
                    if (!landing) Emit(MotorEventKind.Alighted, "hop", 0);
                    return;
                }
                default:
                    FinishClip();
                    return;
            }
        }

        // ---- Riding (updateRide, L2966–L2974; syncRide L2961–L2964) -------------------------------------------------
        private void StepRide(in MotorInput input)
        {
            var r = Ride;
            SyncRide();
            RideStatus st = r.Status(_rideToken);
            if (st == RideStatus.Gone) { LeaveRide("gone"); Grounded = false; Vy = _c.FallStartVelocity; PeakY = Y; return; }
            if (st == RideStatus.Unloading)                                               // turn to the landing, then hop (L2970)
            {
                _act.Reset(); _act.Verb = Verb.Alight; _act.Target = r; _act.Token = _rideToken; _act.Phase = ActPhase.Turn;
                _hasYawOverride = true; _yawOverride = 0;
                Emit(MotorEventKind.ActStart, Verb.Alight.ToString(), 0);
                return;
            }
            if ((input.UsePressed || input.JumpPressed) && st == RideStatus.CanHopOff)    // out anywhere on the floor (L2971–L2974)
            {
                double y = LaneProbe.SupportAt(_w, X, Y, _c.Foot);
                _act.Reset(); _act.Verb = Verb.Alight; _act.Target = r;
                _hasYawOverride = true; _yawOverride = 0;
                Emit(MotorEventKind.ActStart, Verb.Alight.ToString(), 0);
                LeaveRide(null);
                StartHop(X, y, 0, false);
                return;
            }
            SetClip(ClipNames.Ride, 0.25, 1);
        }

        private void LeaveRide(string why)
        {
            var r = Ride;
            Ride = null;
            _rideToken = 0;
            if (r == null) return;
            r.OnAlighted();
            if (why != null) Emit(MotorEventKind.Alighted, why, 0);
            if (!_act.Active) _hasYawOverride = false;
        }

        /// <summary>
        /// Ride sync (§3.1 step #9, <c>syncRide</c>, L2959–L2964): after the mechanisms have stepped, he is placed on what he
        /// rides, so he never trails it by a frame. Not during an act: the board/alight hop moves him itself (the prototype
        /// re-placed him on the carrier during its own alight hop, hiding the hop; a deliberate difference).
        /// </summary>
        public void SyncRide()
        {
            if (Ride == null || _act.Active) return;
            if (!Ride.RidePose(_rideToken, out double x, out double y, out double z)) return;
            X = x; Y = y; Z = z; Vx = Vy = 0; Grounded = true; PeakY = y;
        }

        /// <summary>
        /// Ride sync for a lift that carries him (<c>ILiftRide.Carrying</c>, §3.1 step #9): his feet go to its floor
        /// <paramref name="floorY"/>, grounded. Not while mantling (the climb owns his y).
        /// </summary>
        public void SnapToFloor(double floorY)
        {
            if (_mantling) return;
            Y = floorY; Vy = 0; Grounded = true; PeakY = floorY;
        }

        // ---- Hide (DL-14b, L6111–L6125) --------------------------------------------------------------------------------
        private void StepHide(in MotorInput input, double move, double dt)
        {
            var a = _act;
            switch (a.Phase)
            {
                case ActPhase.Approach: StepApproach(dt); return;
                case ActPhase.StepIn:                                                     // back into the recess, L6114–L6116
                    Z = Math.Min(a.InZ, Z + _c.HideInSpeed * dt);
                    SetClip(ClipNames.Walk, 0.2, -_c.HideWalkSpeed / _c.ClipSpeedWalk);
                    if (Z >= a.InZ - 1e-3)
                    {
                        a.Phase = ActPhase.Clip; a.T = 0; Crouched = true;
                        SetClip(ClipNames.CrouchIdle, 0.25, 1);
                        Emit(MotorEventKind.ActEvent, "hidden", 0);
                    }
                    return;
                case ActPhase.Clip:                                                       // any move after 0.3 s, L6118–L6120
                {
                    Crouched = true;
                    bool moving = move != 0 || input.JumpPressed || input.UsePressed;
                    if (moving && a.T > _c.HideLeaveAfter + 1e-9) { a.Phase = ActPhase.StepOut; Crouched = false; }
                    return;
                }
                default:                                                                  // out again, L6122–L6123
                    Z = Math.Max(0, Z - _c.HideOutSpeed * dt);
                    SetClip(ClipNames.Walk, 0.2, _c.HideWalkSpeed / _c.ClipSpeedWalk);
                    if (Z <= 1e-3) { Z = 0; EndAct(false, 0.2); }
                    return;
            }
        }

        // ---- Escorted (DL-14b, L6126–L6134) ------------------------------------------------------------------------
        /// <summary>
        /// The escort has him (the prototype's trolley sets <c>game.act</c>, L6399): he drops what he holds (L6399–L6400)
        /// and is walked to <see cref="EscortWalk.ToX"/>. Ignored while already escorted.
        /// </summary>
        public void BeginEscort(in EscortWalk walk)
        {
            if (_act.Verb == Verb.Escorted || _act.Verb == Verb.Death) return;
            DropAll(Y);
            _act.Reset();
            _act.Verb = Verb.Escorted; _act.Phase = ActPhase.Clip; _act.Walk = walk;
            Vx = 0;
            _hasYawOverride = false;
            Emit(MotorEventKind.ActStart, Verb.Escorted.ToString(), 0);
        }

        private void StepEscorted(double dt)
        {
            var a = _act;
            var w = a.Walk;
            Facing = w.Facing; Crouched = false;
            Z = Damp.Toward(Z, 0, _c.EscortZRate, dt);                                    // L6129
            if (a.T < w.HoldSeconds) { SetClip(ClipNames.Idle, 0.2, 1); return; }        // L6130
            X = Smooth.MoveTowards(X, w.ToX, w.Speed * dt);                               // L6131
            SetClip(ClipNames.Walk, 0.2, w.Speed / _c.ClipSpeedWalk);
            Footsteps();
            if (w.Facing < 0 ? X <= w.ArriveX : X >= w.ArriveX)                           // L6133
            {
                Facing = w.EndFacing;
                EndAct(false);
            }
        }

        // ---- Stuck and death (L4519–L4521, L7425–L7453) -------------------------------------------------------------
        /// <summary>
        /// The stuck act (DL-01's trench, <c>trenchStuck</c>, L4764–L4766, L4519–L4521): he stops; Flinch from 0.2 s; at 2.0 s
        /// <see cref="MotorEventKind.RespawnDue"/> (1.3 s, the fade). Ignored while stuck or dead.
        /// </summary>
        public void BeginStuck()
        {
            if (_act.Verb == Verb.Stuck || _act.Verb == Verb.Death) return;
            _mantling = false;
            _act.Reset();
            _act.Verb = Verb.Stuck; _act.Phase = ActPhase.Clip;
            Vx = 0;
            Emit(MotorEventKind.ActStart, Verb.Stuck.ToString(), 0);
        }

        private void StepStuck()
        {
            var a = _act;
            if (!a.Flinched && a.T > _c.StuckFlinchAfter + 1e-9) { a.Flinched = true; SetClip(ClipNames.Flinch, 0.2, 1); Emit(MotorEventKind.ActEvent, "flinch", 0); }
            if (!a.Cut && a.T > _c.StuckRespawnAfter + 1e-9) { a.Cut = true; Emit(MotorEventKind.RespawnDue, "stuck", _c.RespawnFade); }
        }

        /// <summary>
        /// <c>die(how)</c>, L7435–L7442: he lets go of everything, stops, plays the death clip and shakes the camera; after
        /// the hold (<paramref name="hold"/>, NaN = the kind's) <see cref="MotorEventKind.RespawnDue"/> (0.6 s, the cut).
        /// The sparks and the eye are presentation (Runtime reads <see cref="MotorEventKind.Death"/>). Ignored while dead.
        /// </summary>
        public void Die(DeathKind how, double hold = double.NaN)
        {
            if (_act.Verb == Verb.Death) return;
            DropAll(Math.Max(0, Y));                                                      // releaseHolds, L7428–L7433
            _act.Reset();
            _act.Verb = Verb.Death; _act.Phase = ActPhase.Clip; _act.Death = how;
            _act.Hold = double.IsNaN(hold) ? _c.DeathHold(how) : hold;
            Vx = Vy = 0;
            _hasYawOverride = false;
            string clip = how == DeathKind.Crush ? ClipNames.DeathCrush : how == DeathKind.Shock ? ClipNames.DeathShock
                : how == DeathKind.Grabbed ? ClipNames.DeathGrabbed : ClipNames.DeathFall;
            SetClip(clip, 0.05, 1, restart: true);
            Emit(MotorEventKind.ActStart, Verb.Death.ToString(), 0);
            Emit(MotorEventKind.Death, how.ToString(), _act.Hold);
            Emit(MotorEventKind.Shake, null, _c.DeathShake(how));
        }

        private void StepDeath()
        {
            var a = _act;
            if (!a.Cut && a.T >= a.Hold - 1e-9) { a.Cut = true; Emit(MotorEventKind.RespawnDue, "death", _c.DeathCut); }   // L7448–L7451
        }

        // ---- Quirks (playQuirk / updateQuirk, L3841–L3856) ---------------------------------------------------------
        /// <summary>
        /// <c>playQuirk(clip, cancel)</c>: a short reaction (CheckLabel, Flinch, Proud, PeekDown, Startle...). Refused (false)
        /// while in an act, holding, riding, mantling or in the air (L3842). <paramref name="cancel"/>: any move after 0.3 s
        /// of the clip ends it; <paramref name="cancelAfter"/> allows that only after so many seconds (the wake's label, 2.5 s,
        /// L8108). It ends 0.05 s before the clip's end, or after <paramref name="endAfter"/> seconds; CheckLabel then holds
        /// <paramref name="holdFor"/> (NaN = 0.8 s, L3853).
        /// </summary>
        public bool PlayQuirk(string clip, bool cancel = true, double holdFor = double.NaN, double cancelAfter = double.NaN, double endAfter = double.NaN)
        {
            if (clip == null) throw new ArgumentNullException(nameof(clip));
            if (_act.Active || Hold != HoldKind.None || Ride != null || _mantling || !Grounded) return false;
            if (double.IsNaN(endAfter) && !ClipTimings.TryGet(clip, out _)) return false;          // !actions[clip]
            _act.Reset();
            _act.Verb = Verb.Quirk; _act.Phase = ActPhase.Clip; _act.ClipName = clip;
            _act.Cancel = cancel; _act.HoldFor = holdFor; _act.CancelAfter = cancelAfter; _act.EndAfter = endAfter;
            Vx = 0;
            SetClip(clip, 0.15, 1, restart: true);
            Emit(MotorEventKind.ActStart, Verb.Quirk.ToString(), 0);
            return true;
        }

        /// <summary>A flinch (Flinch for 1.6 s, as after the latch, L1875–L1876): a quirk nothing cancels.</summary>
        public bool Flinch(double seconds = ClipTimings.FlinchEvents.End / 24) => PlayQuirk(ClipNames.Flinch, false, endAfter: seconds);

        private void StepQuirk(in MotorInput input, double move)
        {
            var a = _act;
            bool moving = move != 0 || input.JumpPressed;
            bool cancel = a.Cancel || (!double.IsNaN(a.CancelAfter) && a.Total > a.CancelAfter);
            if (cancel && moving && ClipTime > _c.QuirkCancelAfter) { EndActKeepingClip(); return; }   // L3851
            double end = !double.IsNaN(a.EndAfter) ? a.EndAfter
                : (ClipTimings.TryGet(a.ClipName, out var info) ? info.Seconds(_c.Fps) : 0) - _c.QuirkEndEarly;
            if (ClipTime + 1e-9 < end) return;                                            // act.time: the mixer's, a step behind (as L3852)
            if (a.ClipName == ClipNames.CheckLabel)                                       // held a beat, L3853
            {
                if (double.IsNaN(a.EndAt)) a.EndAt = a.Total;
                if (a.Total - a.EndAt + 1e-9 < (double.IsNaN(a.HoldFor) ? _c.CheckLabelHold : a.HoldFor)) return;
            }
            EndAct(false, 0.35);
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
                var it = Carried;
                pt.OnPlaced(it);
                it?.OnPlaced(pt);
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

        private void EndAct(bool restoreFacing, double fade = 0.3)
        {
            var a = _act;
            if (restoreFacing && a.Face != 0) Facing = a.Face;
            if (a.Crouch || a.Verb == Verb.Hide) Crouched = false;
            EndActKeepingClip();
            SetClip(ClipNames.Idle, fade, 1);
        }

        private void EndActKeepingClip()
        {
            var verb = _act.Shove ? "Shove" : _act.Verb.ToString();
            _hasYawOverride = false;
            _act.Reset();
            Emit(MotorEventKind.ActEnd, verb, 0);
        }

        // ---- Animation clock --------------------------------------------------------------------------------------------
        /// <summary>The prototype's <c>setClip</c>, L1597–L1605: same clip → only the speed changes (unless <paramref name="restart"/>: an act's clip starts over).</summary>
        private void SetClip(string name, double fade, double timeScale, bool restart = false)
        {
            if (Clip == name && !restart) { ClipTimeScale = timeScale; return; }
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
