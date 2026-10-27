using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes
{
    /// <summary>One mechanism of a scene: its stable ID and how to build it (a params factory, §4.13l).</summary>
    public readonly struct MechanismDef
    {
        public readonly MechanismId Id;
        public readonly Func<IMechanism> Create;

        public MechanismDef(MechanismId id, Func<IMechanism> create)
        {
            Id = id;
            Create = create ?? throw new ArgumentNullException(nameof(create));
        }
    }

    /// <summary>
    /// A scene's definition (port_architecture §2 <c>Scenes/</c>, §6): its stretch of the lane, its mechanisms in step
    /// order (the prototype's update order, §3.1), the static lane of that stretch and the contributors that adapt its
    /// mechanisms to the lane, and its bespoke rules. Data only, plus factories. One static class per scene builds it
    /// (<c>Scenes/Dl01/Dl01Scene.Def()</c>); a <see cref="ChapterDef"/> lists them in lane order and
    /// <see cref="ChapterSim"/> builds them all into one world. Its checkpoints are the chapter's
    /// (<see cref="CheckpointTable"/>).
    /// </summary>
    public sealed class SceneDef
    {
        /// <summary>"DL-01".</summary>
        public string Id = "";
        public string Title = "";
        /// <summary>
        /// The lane x the scene spans in its <see cref="Region"/>, [X0, X1) (<c>sceneName</c>, L8135–L8144; §5). In a
        /// chapter the scenes of one region follow each other (X1 = the next one's X0); a region change is a seam too.
        /// </summary>
        public double X0, X1;
        /// <summary>The prototype's <c>game.region</c> for this scene's lane (§0.3).</summary>
        public int Region = 1;
        /// <summary>The mechanisms, in step order.</summary>
        public MechanismDef[] Mechanisms = Array.Empty<MechanismDef>();
        /// <summary>The static lane of the scene's stretch (<c>Lane/Tables/</c>).</summary>
        public Func<LaneTable> Lane;
        /// <summary>The moving parts of the lane, adapted from the built graph's mechanisms.</summary>
        public Func<MechanismGraph, ILaneContributor[]> LaneContributors;
        /// <summary>Bespoke rules (triggers, follow-up acts, transits); null = none.</summary>
        public Func<SceneRules> Rules;
        /// <summary>
        /// The motor's tuning while he is in this scene (null = the chapter's): the fields where it differs from
        /// <see cref="MotorConfig.Prototype"/> apply from the step he enters, e.g. DL-06's lever step-in speed (M10, #28).
        /// </summary>
        public Func<MotorConfig> Motor;
        /// <summary>Things he can use that are not mechanisms (a pushable's <c>PushTwin</c> face), registered after the scene's mechanisms; null = none.</summary>
        public Func<MechanismGraph, IInteractable[]> Interactables;

        /// <summary>The same definition with other rules (a scene simulated with a variant of its own, a later scene on a shared floor).</summary>
        public SceneDef WithRules(Func<SceneRules> rules)
        {
            Rules = rules;
            return this;
        }
    }
}
