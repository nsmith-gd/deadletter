using System;
using System.Collections.Generic;
using DeadLetter.Core.Lane;
using DeadLetter.Core.Mechanisms;

namespace DeadLetter.Core.Scenes
{
    /// <summary>Where a checkpoint puts D-17 (<c>CHECKPOINTS</c>, L7975–L8014): lane x, feet y, facing +x.</summary>
    public readonly struct CheckpointDef
    {
        public readonly string Name;
        public readonly double X, Y;
        /// <summary>The lane region he is in there (<c>c.region || 1</c>, L8026).</summary>
        public readonly int Region;

        public CheckpointDef(string name, double x, double y = 0, int region = 0)
        {
            Name = name ?? throw new ArgumentNullException(nameof(name));
            X = x; Y = y; Region = region;
        }
    }

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
    /// A scene's definition (port_architecture §2 <c>Scenes/</c>, §6): what <see cref="SceneSim"/> builds. Data only,
    /// plus factories: the mechanisms in step order (the prototype's update order, §3.1), the static lane of its region
    /// and the contributors that adapt its mechanisms to the lane, its checkpoints, and its bespoke rules. One static
    /// class per scene builds it (<c>Scenes/Dl01/Dl01Scene.Def()</c>).
    /// </summary>
    public sealed class SceneDef
    {
        /// <summary>"DL-01": also the save's scene key (a snapshot is applied only to the same scene).</summary>
        public string Id = "";
        public string Title = "";
        /// <summary>Lane x the scene spans (<c>sceneName</c>, L8135–L8144; §5).</summary>
        public double X0, X1;
        /// <summary>The prototype's <c>game.region</c> for this scene's lane (§0.3).</summary>
        public int Region = 1;
        /// <summary>The checkpoint order the save uses (<c>CP_ORDER</c>, L3976).</summary>
        public IReadOnlyList<string> CheckpointOrder = Checkpoint.PrototypeOrder;
        /// <summary>The checkpoints that place D-17 in this scene.</summary>
        public CheckpointDef[] Checkpoints = Array.Empty<CheckpointDef>();
        /// <summary>The mechanisms, in step order.</summary>
        public MechanismDef[] Mechanisms = Array.Empty<MechanismDef>();
        /// <summary>The region's static lane (<c>Lane/Tables/</c>).</summary>
        public Func<LaneTable> Lane;
        /// <summary>The moving parts of the lane, adapted from the built graph's mechanisms.</summary>
        public Func<MechanismGraph, ILaneContributor[]> LaneContributors;
        /// <summary>Bespoke rules (triggers, follow-up acts, transits); null = none.</summary>
        public Func<SceneRules> Rules;

        public bool TryGetCheckpoint(string name, out CheckpointDef cp)
        {
            for (int i = 0; i < Checkpoints.Length; i++)
                if (string.Equals(Checkpoints[i].Name, name, StringComparison.Ordinal)) { cp = Checkpoints[i]; return true; }
            cp = default;
            return false;
        }
    }

    /// <summary>
    /// A scene's own rules, called by <see cref="SceneSim"/> at fixed points of the §3.1 step. Rules read state and start
    /// <see cref="SceneAct"/>s, reach checkpoints and switch regions; they never move a mechanism (the graph owns those).
    /// </summary>
    public class SceneRules
    {
        /// <summary>After the world is rebuilt at a checkpoint (Begin, respawn). <paramref name="fromOpening"/>: play starts at the opening's last step.</summary>
        public virtual void OnBegin(SceneSim sim, string checkpoint, bool fromOpening) { }

        /// <summary>
        /// The first step after <c>Begin(fromOpening: true)</c>, after the clock and before #4: the opening's last step,
        /// where the prototype's <c>startPlay</c> runs before <c>updatePlayer</c> (L8507).
        /// </summary>
        public virtual void OnOpeningEnd(SceneSim sim) { }

        /// <summary>
        /// #4's tail, after the motor's step (<c>updatePlayer</c>'s last lines). <paramref name="freeStep"/>: the motor
        /// walked, jumped or fell this step (no act, mantle or hold before or after), which is when the prototype reaches
        /// its position triggers.
        /// </summary>
        public virtual void AfterMotor(SceneSim sim, bool freeStep) { }

        /// <summary>After the mechanisms stepped (#5–#7): rules driven by their transitions (<see cref="MechanismGraph.Log"/>).</summary>
        public virtual void AfterGraph(SceneSim sim) { }
    }
}
