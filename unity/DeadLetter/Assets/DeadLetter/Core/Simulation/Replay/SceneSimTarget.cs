using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;

namespace DeadLetter.Core.Simulation.Replay
{
    /// <summary>
    /// A scripted player's view of a <see cref="SceneSim"/> (U-20's scene simulation): the fields bot.js reads from the
    /// prototype, mapped from the scene's state. Read-only on the sim; <see cref="Step"/> is one <see cref="SceneSim.Step"/>.
    /// </summary>
    public sealed class SceneSimTarget : ISimTarget
    {
        private readonly string _nextScene;
        private bool _started;

        /// <param name="nextSceneName">What <see cref="SceneName"/> reads once he has left the scene ("DL-02 The Sorting Hall").</param>
        public SceneSimTarget(SceneSim sim, string nextSceneName = null)
        {
            Sim = sim;
            _nextScene = nextSceneName;
        }

        public SceneSim Sim { get; }

        /// <summary>Begins the scene (<see cref="SceneSim.Begin"/>). From the opening, control comes after the first step, as <c>startPlay</c> runs in it.</summary>
        public SceneSimTarget Begin(string checkpoint, bool fromOpening)
        {
            Sim.Begin(checkpoint, fromOpening);
            _started = !fromOpening;
            return this;
        }

        public double Clock => Sim.Clock;
        public double X => Sim.X;
        public double Y => Sim.Y;
        public bool Grounded => Sim.Grounded;
        public bool Mantling => Sim.Motor.IsMantling;

        /// <summary>
        /// <see cref="SceneSim.ActKind"/>, without the mantle and the transit: the prototype keeps them apart from
        /// <c>G.act</c> (<c>G.mantle</c>, <c>G.transit</c>), so bot.js walks on through them (they ignore input).
        /// </summary>
        public string Act
        {
            get
            {
                string k = Sim.ActKind;
                return k == "mantle" || k == "transit" ? null : k;
            }
        }

        /// <summary>
        /// A quirk a move cancels (<c>G.act.kind === 'quirk' &amp;&amp; G.act.cancel</c>, bot.js L33). <see cref="QuirkAct"/>
        /// keeps its flag private; the prototype starts only CheckLabel uncancellable (<c>playQuirk(…, false)</c>, L8107, L5778).
        /// </summary>
        public bool ActCancellable => Sim.ActKind == "quirk" && Sim.ActPhase != "CheckLabel";

        public HoldKind Hold => Sim.Motor.Hold;
        public bool Riding => false;
        public bool Playing => _started && Sim.RespawnAt <= 0;
        public bool InTransit => Sim.ActKind == "transit";
        public int Region => Sim.Region;
        public string Checkpoint => Sim.Checkpoints.Current.Name;

        public string SceneName =>
            Sim.Exited && _nextScene != null ? _nextScene : Sim.Def.Id + (string.IsNullOrEmpty(Sim.Def.Title) ? "" : " " + Sim.Def.Title);

        public string Near
        {
            get
            {
                if (Sim.Act != null || !Sim.Motor.PreviewUse(out var c) || c.Target == null) return null;
                return c.Target is IMechanism m ? m.Id.Value : c.Target.GetType().Name;
            }
        }

        /// <summary>Deaths so far (<c>game.deaths</c>): each <see cref="Hazards.DeathAct"/> that starts. A respawn on its own (DL-01's trench) is not one.</summary>
        public int Deaths { get; private set; }
        public int Found => 0;
        public MechanismGraph Mechanisms => Sim.Graph;

        public void Step(in MotorInput input)
        {
            bool dying = Hazards.DeathRule.Dying(Sim);
            Sim.Step(input);
            if (!dying && Hazards.DeathRule.Dying(Sim)) Deaths++;
            _started = true;
        }
    }
}
