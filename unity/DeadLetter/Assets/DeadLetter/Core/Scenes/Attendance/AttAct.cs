using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes.Attendance
{
    /// <summary>
    /// Chapter 1's own acts (<c>game.act.kind === 'att'</c>, <c>beginAtt</c>/<c>updateAttAct</c>, L5288–L5380, and the
    /// expansion's <c>beginAtt3</c>/<c>updateAtt3Act</c>, L6008–L6105), where the motor's cannot play them: he walks to a
    /// stand point (<c>approachCh1</c>, L4380–L4388), optionally steps back toward the wall at 0.5 m/s (<c>STEP_IN14a</c>,
    /// L6004–L6036), plays a clip with <c>yawOverride = π</c> taken at its first frame, not after a turn (L5313–L5316),
    /// and steps out again if he stepped in. Owns his pose while it runs; at its end the motor is put back where it left
    /// him (<see cref="D17Motor.Place"/>), with what he is holding then (<see cref="D17Motor.TakeItem"/>).
    /// <para>Timing, as the prototype's: the step Use is pressed only starts it (<c>beginCh1</c>: <c>game.vx = 0</c>, the
    /// act set, L4308); each later step adds dt to <see cref="SceneAct.T"/> first (<c>a.t += dt</c>, L4390). The arrival
    /// step (or the step the step-in ends) snaps him there, zeroes the clock and starts the clip (time 0); the clip's
    /// frame is then <c>T · 24</c> (<c>actions[clip].time · FPS</c>: the mixer advances before <c>updatePlayer</c>, L8506).
    /// A step in or out moves him at most 0.5·dt toward its depth and ends on the step his distance before moving was
    /// under 0.005 (L6031–L6033). His yaw turns toward the override or his facing at 8 rad/s at the end of every step
    /// (<c>updateCharacter</c>, L7578–L7582).</para>
    /// <para>What he holds: whatever the motor had when the act began, until <see cref="LetGo"/> empties his hands or
    /// <see cref="Take"/> gives him something, which the motor shows at once (the prototype's <c>game.hold</c> changes
    /// mid-act).</para>
    /// </summary>
    public abstract class AttAct : SceneAct
    {
        /// <summary>The phases outside the clip (<c>'approach'</c>, <c>'in'</c>, <c>'out'</c>).</summary>
        public static readonly ActId Approach = ActId.Of("Approach"), In = ActId.Of("In"), Out = ActId.Of("Out");
        /// <summary>The step in and out (<c>0.5 · dt</c>, snap under 0.005; L6031–L6033).</summary>
        public const double StepSpeed = 0.5, StepSnap = 0.005;

        private enum Stage { Approach, In, Clip, Out }

        private readonly double _standX, _walk, _yawRate, _arrive, _stepIn;
        private readonly int _face;
        private bool _fresh = true, _hasOverride;
        private double _override;
        private Stage _stage;
        private ICarryable _held;

        /// <param name="kind">What the act is on (the mechanism's ID, or a kind).</param>
        /// <param name="standX">Where he walks to (NaN: no approach, the clip starts on the next step).</param>
        /// <param name="face">His facing on the way and in the act (0: keep his own).</param>
        /// <param name="stepIn">Unity z (+ into the set) he steps back to before the clip and out from after it; 0 = none.</param>
        protected AttAct(ChapterSim sim, ActId kind, double standX, int face, double stepIn = 0)
            : base(kind, double.IsNaN(standX) ? ActId.None : Approach)
        {
            if (sim == null) throw new ArgumentNullException(nameof(sim));
            X = sim.X; Y = sim.Y; Z = sim.Z; Yaw = sim.Yaw;
            Facing = sim.Motor.Facing;
            Sim = sim;
            _standX = standX; _face = face; _stepIn = stepIn;
            _stage = double.IsNaN(standX) ? Stage.Clip : Stage.Approach;
            _held = sim.Motor.Hold == HoldKind.Item ? sim.Motor.Carried : null;
            var c = sim.Config;
            _walk = c.Walk * c.ApproachFactor;                                                // WALK · 0.8, L4385
            _yawRate = c.YawRate;
            _arrive = c.ArriveX;                                                              // 0.012, L4384
        }

        public override bool OwnsPose => true;

        protected ChapterSim Sim { get; }
        /// <summary>His facing (<c>game.facing</c>).</summary>
        public int Facing { get; protected set; }
        /// <summary>What his hands hold now (null: nothing).</summary>
        public ICarryable Held => _held;
        /// <summary>The clip's frame this step (24 fps).</summary>
        protected double Frame => T * 24;

        /// <summary><c>game.yawOverride = v</c>.</summary>
        protected void FaceSet(double yaw) { _hasOverride = true; _override = yaw; }
        /// <summary><c>game.yawOverride = null</c>.</summary>
        protected void FaceLane() => _hasOverride = false;

        /// <summary>The clip starts (its phase, the override): on arrival, or once the step-in ends.</summary>
        protected abstract void OnArrive();

        /// <summary>One step of the clip, after the clock advanced; false when it is over (the act ends, or steps out).</summary>
        protected abstract bool OnClip(double dt);

        /// <summary>His hands are empty from now on (<c>game.hold = null</c>), the act going on.</summary>
        protected void LetGo()
        {
            _held = null;
            Sim.Motor.Place(X, Y, Facing, Yaw);
        }

        /// <summary>He holds <paramref name="item"/> from now on (<c>game.hold = 'item'; game.carry = it</c>), the act going on.</summary>
        protected void Take(ICarryable item)
        {
            _held = item ?? throw new ArgumentNullException(nameof(item));
            Sim.Motor.Place(X, Y, Facing, Yaw);
            Sim.Motor.TakeItem(item);
        }

        public sealed override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            bool keep = true;
            if (_fresh) _fresh = false;                                                       // the Use step: beginCh1 only
            else
            {
                T += dt;                                                                      // a.t += dt, L4390
                switch (_stage)
                {
                    case Stage.Approach:
                    {
                        if (_face != 0) Facing = _face;                                       // L4381
                        double dx = _standX - X;
                        if (Math.Abs(dx) < _arrive)                                           // L4384
                        {
                            X = _standX; T = 0;
                            if (_stepIn > 0) { _stage = Stage.In; Phase = In; FaceSet(Math.PI); }   // L6025
                            else { _stage = Stage.Clip; OnArrive(); }
                        }
                        else X += Smooth.Sign(dx) * Math.Min(Math.Abs(dx), _walk * dt);       // L4385
                        break;
                    }
                    case Stage.In:
                        if (StepTo(_stepIn, dt)) { _stage = Stage.Clip; T = 0; OnArrive(); }  // L6033–L6034
                        break;
                    case Stage.Clip:
                        if (!OnClip(dt))
                        {
                            if (_stepIn > 0) { _stage = Stage.Out; Phase = Out; }             // L6045, L6049, L6053
                            else keep = false;
                        }
                        break;
                    default:
                        if (StepTo(0, dt)) keep = false;                                      // L6035
                        break;
                }
            }
            if (!keep) FaceLane();
            double target = _hasOverride ? _override : (Facing > 0 ? Math.PI / 2 : -Math.PI / 2);
            Yaw = Smooth.MoveTowards(Yaw, target, _yawRate * dt);                            // updateCharacter, L7579–L7582
            if (!keep)
            {
                Sim.Motor.Place(X, Y, Facing, Yaw);
                if (_held != null) Sim.Motor.TakeItem(_held);
            }
            return keep;
        }

        /// <summary>One step toward depth <paramref name="to"/>; true (snapped there) when he was within 0.005 before it.</summary>
        private bool StepTo(double to, double dt)
        {
            double dz = to - Z;
            Z += Smooth.Sign(dz) * Math.Min(Math.Abs(dz), StepSpeed * dt);                       // L6031
            if (!(Math.Abs(dz) < StepSnap)) return false;
            Z = to;
            return true;
        }
    }
}
