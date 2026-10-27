using System;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes
{
    /// <summary>One leg of a transit: turn to <see cref="Yaw"/>, then walk to (<see cref="X"/>, <see cref="Z"/>) unless <see cref="Final"/>.</summary>
    public readonly struct TransitLeg
    {
        public readonly double Yaw, X, Z;
        /// <summary>The last leg only turns (<c>to: null</c>).</summary>
        public readonly bool Final;

        /// <param name="z">Unity sign (+ into the set): the prototype's z negated (§0.2).</param>
        public TransitLeg(double yaw, double x, double z) { Yaw = yaw; X = x; Z = z; Final = false; }

        private TransitLeg(double yaw) { Yaw = yaw; X = Z = 0; Final = true; }

        public static TransitLeg TurnTo(double yaw) => new TransitLeg(yaw);
    }

    /// <summary>
    /// A scripted walk that keeps the camera continuous between scenes (<c>TRANSIT</c>/<c>updateTransit</c>, L2129–L2157;
    /// port_architecture §4.8): for each leg he turns at 8 rad/s until within 0.06 rad of its yaw, then walks straight to its
    /// point at <c>speed</c>, snapping there within 1 cm. It owns his pose; <see cref="SceneAct.Phase"/> is the leg index (<see cref="ActIds.Leg"/>).
    /// </summary>
    public sealed class TransitAct : SceneAct
    {
        private readonly TransitLeg[] _legs;
        private readonly double _speed, _yawRate;
        private readonly Action<ChapterSim, int> _onLeg;
        private readonly Action<ChapterSim> _onEnd;
        private int _stage;
        private int _returnFrom = int.MaxValue;
        private double _returnSpeed;

        /// <param name="onLeg">Called when a leg's point is reached, with the new stage (DL-01: stage 2 is region 2, L2152).</param>
        /// <param name="onEnd">Called on the step the last leg's turn is done (DL-01: checkpoint <c>room</c>, L2145).</param>
        public TransitAct(ActId kind, TransitLeg[] legs, double speed, double x, double y, double z, double yaw, double yawRate,
            Action<ChapterSim, int> onLeg = null, Action<ChapterSim> onEnd = null) : base(kind, ActIds.Leg(0))
        {
            if (legs == null || legs.Length == 0 || !legs[legs.Length - 1].Final) throw new ArgumentException("Legs must end with TurnTo.");
            ActIds.Leg(legs.Length - 1);                                              // in range: a phase for every leg
            _legs = legs; _speed = speed; _yawRate = yawRate; _onLeg = onLeg; _onEnd = onEnd;
            X = x; Y = y; Z = z; Yaw = yaw;
        }

        public override bool OwnsPose => true;
        public int Stage => _stage;

        /// <summary>
        /// From leg <paramref name="stage"/> on, something else also draws him back toward the lane (z → 0) at
        /// <paramref name="speed"/> m/s after each leg step. DL-01: from stage 2 he is in region 2, whose rule for backing
        /// out after letting go of the courier (<c>updateCh1</c>, L4876: no act, no push, z &lt; 0) runs during the passage too.
        /// </summary>
        public TransitAct ReturnToLaneFrom(int stage, double speed) { _returnFrom = stage; _returnSpeed = speed; return this; }
        /// <summary>The yaw he turns toward this step (<c>game.yawOverride</c>).</summary>
        public double TargetYaw { get; private set; }

        /// <summary>
        /// The yaw after the step that started the transit: <c>updateCharacter</c> already turned him toward the first
        /// leg on that step (L7579–L7583), from <paramref name="yaw"/>.
        /// </summary>
        public static double FirstTurn(double yaw, TransitLeg first, double yawRate, double dt) => Smooth.MoveTowards(yaw, first.Yaw, yawRate * dt);

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            T += dt;
            bool keep = Leg(sim, dt);
            if (keep && _stage >= _returnFrom && Z > 0) Z = Math.Max(0, Z - _returnSpeed * dt);   // #7, after the leg (#4)
            Yaw = Smooth.MoveTowards(Yaw, TargetYaw, _yawRate * dt);                // updateCharacter, after updatePlayer
            return keep;
        }

        private bool Leg(ChapterSim sim, double dt)
        {
            var leg = _legs[_stage];
            TargetYaw = leg.Yaw;
            if (Math.Abs(Yaw - leg.Yaw) > 0.06) return true;                         // L2140
            if (leg.Final)                                                            // L2141–L2145
            {
                TargetYaw = Math.PI / 2;                                              // yawOverride = null; facing = 1
                _onEnd?.Invoke(sim);
                return false;
            }
            double dx = leg.X - X, dz = leg.Z - Z, d = Math.Sqrt(dx * dx + dz * dz);  // L2147 (Math.hypot)
            if (d < 0.01)                                                             // L2148–L2152
            {
                X = leg.X; Z = leg.Z;
                _stage++;
                Phase = ActIds.Leg(_stage);
                _onLeg?.Invoke(sim, _stage);
                return true;
            }
            double step = Math.Min(d, _speed * dt);                                   // L2154–L2155
            X += dx / d * step;
            Z += dz / d * step;
            return true;
        }
    }
}
