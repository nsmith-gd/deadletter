using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Beings
{
    /// <summary>
    /// What the reactive beings read about D-17 and the world beyond <see cref="PlayerPose"/> (which carries his x, y, z,
    /// speed, footing and hiding): whether he is in play, which region and level he is in, and the
    /// <see cref="NoiseBus"/>. One instance per scene, shared by its beings; the step driver fills it every fixed step:
    /// <code>
    /// senses.BeginStep();                       // clears the bus
    /// motor.Careful = white.WantsCareful(motor.X);
    /// motor.Step(input, dt);                    // #4
    /// senses.ReadMotor(motor);                  // his landing noise
    /// graph.Step(dt, pose);                     // #6–#8: mechanisms post, then the beings read (pose from the motor)
    /// </code>
    /// It is input, rebuilt every step, so it is not snapshotted. Kept here, not in the pose: play mode, region and
    /// level are world state (<c>WorldState</c>, once it exists), not D-17's body.
    /// </summary>
    public sealed class BeingSenses
    {
        /// <summary><c>game.mode === 'play'</c>, not in the death act and no respawn pending (L7117, L7149, L6367).</summary>
        public bool Alive = true;
        /// <summary><c>game.region</c> (1–6; L1791–L1793, L2042–L2048).</summary>
        public int Region;
        /// <summary><c>game.upper</c>: on DL-07's gallery level (the heap water is only active below, L7327).</summary>
        public bool Upper;

        public readonly NoiseBus Noises = new NoiseBus();

        public void BeginStep() => Noises.Clear();

        /// <summary>
        /// Posts the motor's White noise (a real landing, <c>makeNoise(game.x, 1.1)</c>,
        /// L2028) as his own sound in <see cref="Region"/>. Call after the motor steps.
        /// </summary>
        public void ReadMotor(D17Motor m)
        {
            var events = m.Events;
            for (int i = 0; i < events.Count; i++)
            {
                var e = events[i];
                if (e.Kind == MotorEventKind.Noise) Noises.Post(NoiseEvent.Sound(m.X, e.Value, Region, fromHim: true));
            }
        }
    }
}
