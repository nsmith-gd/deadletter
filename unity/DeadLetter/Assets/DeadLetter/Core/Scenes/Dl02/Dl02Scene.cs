using DeadLetter.Core.Carry;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms;

namespace DeadLetter.Core.Scenes.Dl02
{
    /// <summary>
    /// DL-02 The Sorting Hall (port_architecture §5; docs/scenes/DL-02_the_sorting_hall.md): out of the passage at
    /// <c>room</c>, under the franking press (the hall's only way to die), past the tube that coughs out its letter, the
    /// box carried to the sorting table's foot, up onto the table and the gantry, and over the sill into DL-03.
    /// Lines are index.html at 7b3c123.
    /// <para>Not here: the curiosities (franker, mug; §4.27), picking up and posting letters (§4.26; the motor has no verb
    /// for them), the voice card, camera, lights and sound, which are other systems'.</para>
    /// </summary>
    public static class Dl02Scene
    {
        public const string Id = "DL-02";

        /// <summary>The scene definition.</summary>
        public static SceneDef Def() => new SceneDef
        {
            Id = Id,
            Title = "The Sorting Hall",
            X0 = Dl02Lane.X0, X1 = Dl02Lane.X1,                                                    // sceneName, L8139
            Region = Dl02Lane.Region,
            Checkpoints = new[]
            {
                new CheckpointDef("room", 13.2, region: Dl02Lane.Region),                         // EMERGE_X L319; CHECKPOINTS L7980
            },
            // Step order = the prototype's: the box changes in updatePlayer (#4) and is drawn in updateCh1 (#7, L4782),
            // the tube's letter falls in updateCh1 (L4770–L4779), the press stamps in updateHazards, last (#7, L7343–L7351).
            Mechanisms = new[]
            {
                new MechanismDef("dl02.box", () => new CarriedItem("dl02.box", CarriedItemParams.Dl02Box())),
                new MechanismDef("dl02.tubeLetter", () => new Dl02TubeLetter("dl02.tubeLetter")),
                new MechanismDef("dl02.press", () => new PeriodicCrusher("dl02.press", PeriodicCrusherParams.Dl02Press())),
            },
            Lane = Dl02Lane.Table,
            LaneContributors = Dl02Lane.Contributors,
            Rules = () => new Dl02Rules(),
        };
    }

    /// <summary>
    /// DL-02's rules: the press keeps the game clock's time (<c>game.clock % period</c>, L7345) and kills (<c>die('crush')</c>,
    /// L7351; the respawn at <c>room</c> through <see cref="DeathRule"/>); he leaves DL-02 when he reaches the sill's far
    /// side (<c>sceneName</c>: x ≥ <c>SH.x1</c>, L8139), where DL-03's simulation takes him on.
    /// </summary>
    public sealed class Dl02Rules : SceneRules
    {
        private PeriodicCrusher _press;

        /// <summary>Deaths and the death act (one per simulation: the count outlives respawns).</summary>
        public DeathRule Death { get; } = new DeathRule();

        public override void OnBegin(SceneSim sim, string checkpoint, bool fromOpening)
        {
            if (_press != null) return;
            _press = sim.Graph.Get<PeriodicCrusher>("dl02.press");
            _press.BindClock(() => sim.Clock);                                                   // game.clock, L7345; each step reads it
        }

        public override void AfterGraph(SceneSim sim)
        {
            Death.Watch(sim, _press);                                                            // L7351
            if (!sim.Exited && sim.X >= Dl02Lane.X1) sim.Exit();                                 // DL-03 from SH.x1, L8139
        }
    }
}
