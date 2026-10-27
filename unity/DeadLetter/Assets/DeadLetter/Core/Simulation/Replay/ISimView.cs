using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Simulation.Replay
{
    /// <summary>
    /// What a scripted player reads each step: the fields bot.js reads from <c>window.__dl01</c> (<c>G.x</c>,
    /// <c>G.grounded</c>, <c>G.act</c>, <c>D.near()</c>, <c>G.checkpoint</c>, <c>D.scene()</c>, …). Any headless scene
    /// runner implements it (the U-20 scene sim, or a test rig), so scripts never depend on one runner.
    /// </summary>
    public interface ISimView
    {
        /// <summary>Game time, seconds (<c>G.clock</c>): it advances 1/60 per step, including the opening.</summary>
        double Clock { get; }
        double X { get; }
        double Y { get; }
        bool Grounded { get; }
        bool Mantling { get; }
        /// <summary>The act he is in, or null: the target mechanism's id for a motor act ("dl01.latch"), else a scene act's kind ("dl01.trench", "quirk", "transit").</summary>
        string Act { get; }
        /// <summary>The act is a quirk a move cancels (<c>G.act.kind === 'quirk' &amp;&amp; G.act.cancel</c>): the bot walks on through it.</summary>
        bool ActCancellable { get; }
        HoldKind Hold { get; }
        bool Riding { get; }
        /// <summary>The player has control (<c>G.mode === 'play'</c>), i.e. the opening is over.</summary>
        bool Playing { get; }
        /// <summary>A scripted walk is moving him (<c>G.transit</c>): input is ignored.</summary>
        bool InTransit { get; }
        int Region { get; }
        /// <summary>The last checkpoint reached (<c>G.checkpoint</c>), or null.</summary>
        string Checkpoint { get; }
        /// <summary>The scene he is in, as the prototype names it (<c>sceneName()</c>, L8135): "DL-01 The Wake".</summary>
        string SceneName { get; }
        /// <summary>What Use would start now (<c>D.near()</c>): the target mechanism's id, or null.</summary>
        string Near { get; }
        int Deaths { get; }
        /// <summary>Curiosities used (<c>Object.keys(D.curios).length</c>).</summary>
        int Found { get; }
        /// <summary>The scene's mechanisms, for script conditions (the cart's state, the door's height, …).</summary>
        MechanismGraph Mechanisms { get; }
        /// <summary>State the scenes share outside the graph (DL-03/04's <c>RacksReveal</c>: <c>G.revealed</c>).</summary>
        T Shared<T>() where T : class, new();
    }

    /// <summary>A target that raises presentation cues (music, voices, shots) each step; <see cref="SimRun"/> logs them.</summary>
    public interface ICueSource
    {
        /// <summary>The cues raised by the last step.</summary>
        System.Collections.Generic.IReadOnlyList<Cues.Cue> Cues { get; }
    }

    /// <summary>A headless scene a script can play: the view, plus one 60 Hz pipeline step.</summary>
    public interface ISimTarget : ISimView
    {
        void Step(in MotorInput input);
    }
}
