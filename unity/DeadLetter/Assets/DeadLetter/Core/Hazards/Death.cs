using System;

namespace DeadLetter.Core.Hazards
{
    /// <summary>How D-17 dies (<c>DEATH</c>, L7421–L7424; port_architecture §4.14).</summary>
    public enum DeathKind
    {
        /// <summary>Under DL-02's franking press.</summary>
        Crush,
        /// <summary>DL-08's live cable, the second touch.</summary>
        Shock,
        /// <summary>Dragged under in DL-07's sump.</summary>
        Grabbed,
        /// <summary>A fall (also the fallback for an unknown kind, <c>DEATH[how] || DEATH.fall</c>, L7432).</summary>
        Fall,
    }

    /// <summary>The motor's own <see cref="Motor.DeathKind"/> (#22: it has one with the same members).</summary>
    public static class DeathKinds
    {
        public static Motor.DeathKind ToMotor(DeathKind how) => (Motor.DeathKind)(int)how;
    }

    /// <summary>
    /// One kind of death as the prototype stages it (<c>DEATH</c>, L7421–L7424; <c>die</c>, L7429–L7442): the clip, how
    /// long it holds before the cut, the sparks and the shake. Presentation reads <see cref="Clip"/>, <see cref="SparksFor"/>,
    /// <see cref="SparkRateFor"/>, <see cref="SparkSpeed"/>, <see cref="EyeLevel(double, bool)"/> and <see cref="Shake"/>, all
    /// with calm mode (§4.29); Core uses <see cref="Hold"/>.
    /// </summary>
    public readonly struct DeathProfile
    {
        /// <summary>After the hold, a hard cut to black; the respawn comes this long after it (<c>respawnAt = clock + 0.6</c>, L7451).</summary>
        public const double CutToRespawn = 0.6;
        /// <summary>A respawn that is not a death (DL-01's trench) fades for 1.3 s on the game clock (<c>respawn</c>, L2997–L2999).</summary>
        public const double FadeToRespawn = 1.3;
        /// <summary>The eye stutters out over this long (<c>updateDeath</c>, L7447).</summary>
        public const double EyeOut = 0.45;

        public readonly DeathKind Kind;
        public readonly string Clip;
        /// <summary>Seconds the death plays before the cut (<c>a.hold</c>).</summary>
        public readonly double Hold;
        public readonly int Sparks;
        /// <summary>Spark burst speed (<c>how === 'shock' ? 1.6 : 1.0</c>, L7439).</summary>
        public readonly double SparkSpeed;
        /// <summary>Camera shake (<c>crush 0.9, fall 0.7, else 0.45</c>, L7441).</summary>
        public readonly double Shake;

        public DeathProfile(DeathKind kind, string clip, double hold, int sparks, double sparkSpeed, double shake)
        {
            Kind = kind; Clip = clip ?? throw new ArgumentNullException(nameof(clip)); Hold = hold; Sparks = sparks; SparkSpeed = sparkSpeed; Shake = shake;
        }

        /// <summary>The prototype's table (L7421–L7424, L7439–L7441).</summary>
        public static DeathProfile Of(DeathKind kind)
        {
            switch (kind)
            {
                case DeathKind.Crush: return new DeathProfile(kind, "DeathCrush", 0.7, 26, 1.0, 0.9);
                case DeathKind.Shock: return new DeathProfile(kind, "DeathShock", 1.0, 44, 1.6, 0.45);
                case DeathKind.Grabbed: return new DeathProfile(kind, "DeathGrabbed", 1.15, 18, 1.0, 0.45);
                default: return new DeathProfile(DeathKind.Fall, "DeathFall", 0.9, 20, 1.0, 0.7);
            }
        }

        /// <summary>Shock's extra spark bursts per second while it plays (<c>Math.random() &lt; dt · 14</c>, L7448).</summary>
        public const double ShockSparkRate = 14;

        /// <summary>The sparks burst as he dies: <see cref="Sparks"/>, none in calm (<c>if (!game.calm) burstSparks</c>, L7440).</summary>
        public int SparksFor(bool calm) => calm ? 0 : Sparks;

        /// <summary>Extra bursts per second while the death plays: <see cref="ShockSparkRate"/> for a shock, none in calm (L7448).</summary>
        public double SparkRateFor(bool calm) => !calm && Kind == DeathKind.Shock ? ShockSparkRate : 0;

        /// <summary>
        /// The eye's level <paramref name="t"/> seconds into a death (<c>game.eyeLevel</c>, L7447), with calm mode: the prototype stutters it at 11 Hz whatever <c>game.calm</c> says (L7447); calm fades
        /// it out over the same <see cref="EyeOut"/> instead (port_architecture §4.29; docs/unity/accessibility.md).
        /// </summary>
        public static double EyeLevel(double t, bool calm)
        {
            if (t >= EyeOut) return 0;
            if (calm) return 1 - t / EyeOut;
            return Math.Sin(t * 70) > 0 ? 1 - t / EyeOut : 0.1;
        }
    }
}
