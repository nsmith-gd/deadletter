using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;

namespace DeadLetter.Core.Hazards
{
    /// <summary>
    /// Death and respawn (§4.14: Core <c>DeathRules</c> + <c>RespawnRule</c>), for a scene's rules to call: <see cref="Die"/>
    /// is the prototype's <c>die</c> (L7432–L7442) and <see cref="DeathAct"/> its <c>updateDeath</c> (L7444–L7453). After the
    /// death's hold the act sets <see cref="SceneSim.RespawnAt"/> 0.6 s on, and <see cref="SceneSim"/> respawns at the current
    /// checkpoint on that step (L8494): <see cref="Save.CheckpointService.Reload"/> rebuilds the mechanisms from the
    /// checkpoint (and its snapshot), the motor is placed at the checkpoint, and the rules' <c>OnBegin</c> runs.
    /// One instance per scene simulation; it keeps the death count (<c>game.deaths</c>) across respawns.
    /// </summary>
    public sealed class DeathRule
    {
        /// <summary>Deaths so far (<c>game.deaths</c>, L7437).</summary>
        public int Deaths { get; private set; }

        /// <summary>He is dying now (the prototype's <c>alive</c> is false, L7342).</summary>
        public static bool Dying(SceneSim sim) => sim.Act is DeathAct;

        /// <summary>
        /// Kills him if <paramref name="crusher"/> reported him under it this step (<see cref="CrusherEvent.Crushed"/>;
        /// L7351). Call from <see cref="SceneRules.AfterGraph"/>.
        /// </summary>
        public bool Watch(SceneSim sim, PeriodicCrusher crusher)
        {
            if (crusher == null || !sim.Graph.Log.Has(crusher.Id, MechanismEventKind.Event, (int)CrusherEvent.Crushed)) return false;
            return Die(sim, crusher.Params.Kills);
        }

        /// <summary>
        /// <c>die(how)</c>, L7432–L7442: unless he is already dying, he lets go of what he holds (a carried item drops where he
        /// is, <c>releaseHolds</c> L7425–L7428), stops (vx = vy = 0, no yaw override) and plays the death. Returns whether he died.
        /// </summary>
        /// <param name="sinkRate">He sinks this fast meanwhile, m/s (DL-07's sump: <c>game.y −= dt · 0.8</c>, L7375); 0 = he stays put.</param>
        public bool Die(SceneSim sim, DeathKind how, double sinkRate = 0)
        {
            if (sim == null) throw new ArgumentNullException(nameof(sim));
            if (Dying(sim)) return false;
            var m = sim.Motor;
            double x = sim.X, y = sim.Y, z = sim.Z, yaw = sim.Yaw;
            bool grounded = sim.Grounded;
            int facing = m.Facing;
            // releaseHolds: the item he carries (game.carry, set from Lift f39) is on the floor where he is, at once.
            if (m.Hold == HoldKind.Item && m.Carried != null)
            {
                if (m.Carried is Carry.CarriedItem item) item.Drop(x, Math.Max(0, y));
                else m.Carried.OnSetDown(x, Math.Max(0, y));
            }
            // U-11 has no "let go of everything" (#22): Place clears his holds, act and mantle. The death owns his pose
            // until the respawn places him again.
            m.Place(x, y, facing);
            Deaths++;
            var profile = DeathProfile.Of(how);
            sim.StartAct(new DeathAct(profile, x, y, z, yaw, facing, grounded, sinkRate, sim.Config.YawRate));
            sim.Cue("death:" + profile.Kind.ToString().ToLowerInvariant());
            return true;
        }
    }

    /// <summary>
    /// The death itself (<c>game.act = { kind: 'death' }</c>, <c>updateDeath</c> L7444–L7453): he stays where he died (or
    /// sinks), turning back to his facing as <c>updateCharacter</c> does (L7579–L7583); after the profile's hold the screen
    /// cuts to black and the respawn is set for 0.6 s later. It runs until the respawn replaces it. Phase = the kind.
    /// </summary>
    public sealed class DeathAct : SceneAct
    {
        private readonly double _sink, _yawRate;
        private readonly int _facing;
        private readonly bool _grounded;

        public DeathAct(DeathProfile profile, double x, double y, double z, double yaw, int facing, bool grounded, double sinkRate, double yawRate)
            : base("death", profile.Kind.ToString())
        {
            Profile = profile;
            X = x; Y = y; Z = z; Yaw = yaw;
            _facing = facing >= 0 ? 1 : -1; _grounded = grounded; _sink = sinkRate; _yawRate = yawRate;
        }

        public DeathProfile Profile { get; }
        public override bool OwnsPose => true;
        public override bool PoseGrounded => _grounded;
        /// <summary>The cut to black has happened (<c>a.cut</c>).</summary>
        public bool Cut { get; private set; }
        /// <summary>D-17's eye (<c>game.eyeLevel</c>): a stutter, then dark.</summary>
        public double EyeLevel => DeathProfile.EyeLevel(T);

        public override bool Step(SceneSim sim, in MotorInput input, double dt)
        {
            T += dt;                                                                            // updateActCh1, a.t += dt
            if (_sink > 0) Y -= dt * _sink;                                                     // a.follow(a, dt)
            if (T >= Profile.Hold && !Cut)                                                      // L7449–L7453
            {
                Cut = true;
                sim.RespawnAt = sim.Clock + DeathProfile.CutToRespawn;
                sim.Cue("death:cut");
            }
            Yaw = Smooth.MoveTowards(Yaw, _facing * Math.PI / 2, _yawRate * dt);              // updateCharacter, yawOverride = null
            return true;
        }
    }
}
