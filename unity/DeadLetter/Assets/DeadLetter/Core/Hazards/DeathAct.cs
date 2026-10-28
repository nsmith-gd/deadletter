using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;

namespace DeadLetter.Core.Hazards
{
    /// <summary>
    /// A death he sinks in (DL-07's sump: <c>game.y −= dt · 0.8</c> while <c>updateDeath</c> holds, L7375, L7444–L7453), as a
    /// scene act. Every other death is the motor's (<see cref="D17Motor.Die"/>, through <see cref="ChapterSim.Die"/>); the
    /// motor's death holds his y, so a sinking one stays a scene act until it can sink (#28). He stays where he died, sinking,
    /// turning back to his facing as <c>updateCharacter</c> does (L7579–L7583); after the profile's hold the screen cuts to
    /// black and the respawn is set for 0.6 s later. It runs until the respawn replaces it. Phase = the kind.
    /// </summary>
    public sealed class DeathAct : SceneAct
    {
        private readonly double _sink, _yawRate;
        private readonly int _facing;
        private readonly bool _grounded;
        private bool _calm;

        public DeathAct(DeathProfile profile, double x, double y, double z, double yaw, int facing, bool grounded, double sinkRate, double yawRate)
            : base(ActIds.Death, PhaseOf(profile.Kind))
        {
            Profile = profile;
            X = x; Y = y; Z = z; Yaw = yaw;
            _facing = facing >= 0 ? 1 : -1; _grounded = grounded; _sink = sinkRate; _yawRate = yawRate;
        }

        /// <summary>
        /// <c>die(how)</c>, L7432–L7442, sinking: he lets go of what he holds (a carried item drops where he is,
        /// <c>releaseHolds</c> L7425–L7428), stops, and the act owns his pose. Called by <see cref="ChapterSim.Die"/>.
        /// </summary>
        internal static void Begin(ChapterSim sim, DeathKind how, double sinkRate)
        {
            var m = sim.Motor;
            double x = sim.X, y = sim.Y, z = sim.Z, yaw = sim.Yaw;
            bool grounded = sim.Grounded;
            int facing = m.Facing;
            if (m.Hold == HoldKind.Item && m.Carried != null)
            {
                if (m.Carried is Carry.CarriedItem item) item.Drop(x, System.Math.Max(0, y));
                else m.Carried.OnSetDown(x, System.Math.Max(0, y));
            }
            m.Place(x, y, facing);                                                              // the motor has no "let go of everything" (#28)
            sim.StartAct(new DeathAct(DeathProfile.Of(how), x, y, z, yaw, facing, grounded, sinkRate, sim.Config.YawRate) { _calm = sim.Graph.Calm });
        }

        private static readonly ActId[] Phases =
        {
            ActId.Of(nameof(DeathKind.Crush)), ActId.Of(nameof(DeathKind.Shock)), ActId.Of(nameof(DeathKind.Grabbed)), ActId.Of(nameof(DeathKind.Fall)),
        };

        /// <summary>The act's phase for <paramref name="kind"/>: its name ("Crush").</summary>
        public static ActId PhaseOf(DeathKind kind) => Phases[(int)kind];

        public DeathProfile Profile { get; }
        public override bool OwnsPose => true;
        public override bool PoseGrounded => _grounded;
        /// <summary>The cut to black has happened (<c>a.cut</c>).</summary>
        public bool Cut { get; private set; }
        /// <summary>
        /// Calm mode as the act last saw it (<see cref="Mechanisms.MechanismGraph.Calm"/>, which the checkpoint service sets
        /// from <c>Settings.Calm</c>): read when the death starts and at every step, so the eye and sparks follow the option.
        /// </summary>
        public bool Calm => _calm;
        /// <summary>
        /// D-17's eye (<c>game.eyeLevel</c>, L7447) with calm mode applied: a stutter then dark, or in calm a plain fade
        /// (<see cref="DeathProfile.EyeLevel(double, bool)"/>). The only eye a presentation reads.
        /// </summary>
        public double EyeLevel => DeathProfile.EyeLevel(T, _calm);
        /// <summary>The sparks burst as he dies (<c>burstSparks(…, d.sparks)</c>, L7440): none in calm (<see cref="DeathProfile.SparksFor"/>).</summary>
        public int Sparks => Profile.SparksFor(_calm);
        /// <summary>Shock's extra bursts per second while the death plays (L7448): none in calm or after the cut.</summary>
        public double SparkRate => T < Profile.Hold ? Profile.SparkRateFor(_calm) : 0;

        public override bool Step(ChapterSim sim, in MotorInput input, double dt)
        {
            _calm = sim.Graph.Calm;
            T += dt;                                                                            // updateActCh1, a.t += dt
            Y -= dt * _sink;                                                                    // a.follow(a, dt)
            if (T >= Profile.Hold && !Cut)                                                      // L7449–L7453
            {
                Cut = true;
                sim.RespawnAt = sim.Clock + DeathProfile.CutToRespawn;
            }
            Yaw = Smooth.MoveTowards(Yaw, _facing * System.Math.PI / 2, _yawRate * dt);       // updateCharacter, yawOverride = null
            return true;
        }
    }
}
