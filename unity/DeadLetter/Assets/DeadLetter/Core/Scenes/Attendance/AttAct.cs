using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes.Attendance
{
    /// <summary>
    /// Chapter 1's own acts (<c>game.act.kind === 'att'</c>, <c>beginAtt</c>/<c>updateAttAct</c>, L5288–L5380), where the
    /// motor's cannot play them: he walks to a stand point (<c>approachCh1</c>, L4380–L4388), then plays a clip with
    /// <c>yawOverride = π</c> taken at its first frame, not after a turn (L5313–L5316), and ends on its own frame. Owns
    /// his pose while it runs; at its end the motor is put back where it left him (<see cref="D17Motor.Place"/>), with
    /// what he carries if the act gave him something (<see cref="D17Motor.TakeItem"/>).
    /// <para>Timing, as the prototype's: the step Use is pressed only starts it (<c>beginCh1</c>: <c>game.vx = 0</c>, the
    /// act set, L4308); each later step adds dt to <see cref="SceneAct.T"/> first (<c>a.t += dt</c>, L4390), and the
    /// approach's arrival step snaps him to the stand point, zeroes the clock and starts the clip (time 0). The clip's
    /// frame is then <c>T · 24</c> (<c>actions[clip].time · FPS</c>: the mixer advances before <c>updatePlayer</c>, L8506).
    /// His yaw turns toward the override or his facing at 8 rad/s at the end of every step (<c>updateCharacter</c>,
    /// L7578–L7582).</para>
    /// </summary>
    public abstract class AttAct : SceneAct
    {
        /// <summary>The approach phase (<c>'approach'</c>).</summary>
        public static readonly ActId Approach = ActId.Of("Approach");

        private readonly double _standX, _walk, _yawRate, _arrive;
        private readonly int _face;
        private bool _fresh = true, _approaching, _hasOverride;
        private double _override;

        /// <param name="kind">What the act is on (the mechanism's ID, or a kind).</param>
        /// <param name="standX">Where he walks to (NaN: no approach, the clip starts on the next step).</param>
        /// <param name="face">His facing on the way and in the act (0: keep his own).</param>
        protected AttAct(ChapterSim sim, ActId kind, double standX, int face)
            : base(kind, double.IsNaN(standX) ? ActId.None : Approach)
        {
            if (sim == null) throw new ArgumentNullException(nameof(sim));
            X = sim.X; Y = sim.Y; Z = sim.Z; Yaw = sim.Yaw;
            Facing = sim.Motor.Facing;
            Sim = sim;
            _standX = standX; _face = face;
            _approaching = !double.IsNaN(standX);
            var c = sim.Config;
            _walk = c.Walk * c.ApproachFactor;                                                // WALK · 0.8, L4385
            _yawRate = c.YawRate;
            _arrive = c.ArriveX;                                                              // 0.012, L4384
        }

        public override bool OwnsPose => true;

        protected ChapterSim Sim { get; }
        /// <summary>His facing (<c>game.facing</c>).</summary>
        public int Facing { get; protected set; }
        /// <summary>The clip's frame this step (24 fps).</summary>
        protected double Frame => T * 24;

        /// <summary><c>game.yawOverride = v</c>.</summary>
        protected void FaceSet(double yaw) { _hasOverride = true; _override = yaw; }
        /// <summary><c>game.yawOverride = null</c>.</summary>
        protected void FaceLane() => _hasOverride = false;

        /// <summary>The arrival step: the clip starts (its phase, the override).</summary>
        protected abstract void OnArrive();

        /// <summary>One step of the clip, after the clock advanced; false when the act is over (that step is still its own).</summary>
        protected abstract bool OnClip(double dt);

        /// <summary>The act is over: the motor takes him back here (and what he carries, if anything).</summary>
        protected virtual void OnEnd() => Sim.Motor.Place(X, Y, Facing, Yaw);

        /// <summary>His hands are empty from now on, the act going on (the motor at his pose, holding nothing).</summary>
        protected void LetGo() => Sim.Motor.Place(X, Y, Facing, Yaw);

        public sealed override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            bool keep = true;
            if (_fresh) _fresh = false;                                                       // the Use step: beginCh1 only
            else
            {
                T += dt;                                                                      // a.t += dt, L4390
                if (_approaching)
                {
                    if (_face != 0) Facing = _face;                                           // L4381
                    double dx = _standX - X;
                    if (Math.Abs(dx) < _arrive) { X = _standX; _approaching = false; T = 0; OnArrive(); }   // L4384
                    else X += Smooth.Sign(dx) * Math.Min(Math.Abs(dx), _walk * dt);            // L4385
                }
                else keep = OnClip(dt);
            }
            if (!keep) FaceLane();
            double target = _hasOverride ? _override : (Facing > 0 ? Math.PI / 2 : -Math.PI / 2);
            Yaw = Smooth.MoveTowards(Yaw, target, _yawRate * dt);                            // updateCharacter, L7579–L7582
            if (!keep) OnEnd();
            return keep;
        }

        /// <summary>The clip's phase (named as the clip).</summary>
        protected void SetPhase(ActId phase) => Phase = phase;
    }
}
