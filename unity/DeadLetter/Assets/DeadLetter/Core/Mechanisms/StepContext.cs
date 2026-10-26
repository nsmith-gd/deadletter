namespace DeadLetter.Core.Mechanisms
{
    /// <summary>
    /// D-17 as mechanisms see him this step (after the motor has moved: step order #4 before #6, §3.1). Used by rules
    /// such as "never onto him" (L2392) and "startle if he is near" (L2387). Built by the step pipeline from the motor.
    /// </summary>
    public readonly struct PlayerPose
    {
        public readonly double X, Y, Z;
        /// <summary>Lane speed, m/s (the prototype's <c>game.vx</c>; the motor's <c>Vx</c>).</summary>
        public readonly double Vx;
        public readonly bool Crouched;
        /// <summary>In an act (the prototype's <c>game.act</c>): quirks such as Startle do not interrupt one.</summary>
        public readonly bool Busy;
        /// <summary>On a support (<c>game.grounded</c>; the motor's <c>Grounded</c>). Defaults to true.</summary>
        public readonly bool Grounded;
        /// <summary>His hands are full (<c>game.hold</c>; the motor's <c>Hold != HoldKind.None</c>).</summary>
        public readonly bool Holding;
        /// <summary>In DL-14b's hide act (<c>game.act.what === 'hide'</c>, L5973). The motor has no hide act yet (U-11).</summary>
        public readonly bool Hiding;

        public PlayerPose(double x, double y, double z = 0, bool crouched = false, bool busy = false,
            double vx = 0, bool grounded = true, bool holding = false, bool hiding = false)
        {
            X = x; Y = y; Z = z; Crouched = crouched; Busy = busy;
            Vx = vx; Grounded = grounded; Holding = holding; Hiding = hiding;
        }

        /// <summary>Nobody in the lane (tests of a mechanism on its own).</summary>
        public static PlayerPose Away => new PlayerPose(-1e6, 0);
    }

    /// <summary>
    /// What one <see cref="IMechanism.Step"/> gets: the fixed step, the tick, D-17's pose, the options Core obeys, and
    /// the log it reports transitions to (through <see cref="Mechanism.Enter"/> and <see cref="Mechanism.Emit"/>).
    /// Reads of other mechanisms are not here: they are resolved once in <see cref="IMechanism.Link"/> (Signals.cs).
    /// </summary>
    public readonly struct StepContext
    {
        /// <summary>Fixed step, seconds (1/60 from <c>FixedTick</c>).</summary>
        public readonly double Dt;
        /// <summary>Index of this step since the graph was built (0 on the first step); restored by snapshots.</summary>
        public readonly long Tick;
        public readonly PlayerPose Player;
        /// <summary>The "calm" accessibility option (<c>game.calm</c>): softer flicker and no shutter jitter (L1541, L1695).</summary>
        public readonly bool Calm;
        public readonly MechanismLog Log;

        public StepContext(double dt, long tick, in PlayerPose player, bool calm, MechanismLog log)
        {
            Dt = dt; Tick = tick; Player = player; Calm = calm; Log = log;
        }
    }
}
