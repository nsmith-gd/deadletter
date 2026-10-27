using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// A scene's own rules, called by <see cref="ChapterSim"/> at fixed points of the §3.1 step. Rules read state, start
    /// <see cref="SceneAct"/>s or the motor's acts, reach checkpoints, raise cues and switch regions; they never move a
    /// mechanism (the graph owns those).
    /// <para><b>When they run.</b> <see cref="OnBegin"/> runs for every scene's rules whenever the chapter's world is
    /// rebuilt (it is one world). The step hooks run for the scene that holds him when the step begins
    /// (<see cref="ChapterSim.Current"/>), and every step for rules whose <see cref="Always"/> is true: the prototype
    /// runs each of its update functions every step, so a rule that reaches past its scene's stretch (DL-03's gate
    /// startles him on either side of it) sets <see cref="Always"/> and guards itself as the prototype does.</para>
    /// <para>Cross-scene state (the prototype's <c>game.*</c> fields two scenes read) lives in the one graph or in an
    /// object the rules share through <see cref="ChapterSim.Shared{T}"/>; never in a definition's parameters.</para>
    /// </summary>
    public class SceneRules
    {
        /// <summary>Run the step hooks every step, wherever he is (they then guard themselves by region and x).</summary>
        public virtual bool Always => false;

        /// <summary>
        /// After the world is rebuilt at a checkpoint (begin, new game, continue, respawn): every scene's rules, in lane
        /// order. <paramref name="fromOpening"/>: play starts at the opening's last step.
        /// </summary>
        public virtual void OnBegin(ChapterSim sim, string checkpoint, bool fromOpening) { }

        /// <summary>
        /// The first step after a begin with <c>fromOpening</c>, after the clock and before #4: the opening's last step,
        /// where the prototype's <c>startPlay</c> runs before <c>updatePlayer</c> (L8507).
        /// </summary>
        public virtual void OnOpeningEnd(ChapterSim sim) { }

        /// <summary>
        /// #4's head, when no scene act runs: before the motor reads <paramref name="input"/>. A rule may take the input
        /// (clear an edge it handles itself), set this step's pace (<see cref="D17Motor.SlowWalkLimit"/>, which the chapter
        /// clears first: pace zones hold only while a rule asks), or start a <see cref="SceneAct"/>, which then runs this
        /// step in the motor's place (DL-03's set-down, which the motor cannot do).
        /// </summary>
        public virtual void BeforeMotor(ChapterSim sim, ref MotorInput input) { }

        /// <summary>
        /// #4's tail, after the motor's step (<c>updatePlayer</c>'s last lines). <paramref name="freeStep"/>: the motor
        /// walked, jumped or fell this step (no act, mantle or hold before or after), which is when the prototype reaches
        /// its position triggers.
        /// </summary>
        public virtual void AfterMotor(ChapterSim sim, bool freeStep) { }

        /// <summary>After the mechanisms stepped (#5–#7): rules driven by their transitions (<see cref="Mechanisms.MechanismGraph.Log"/>).</summary>
        public virtual void AfterGraph(ChapterSim sim) { }

        /// <summary>
        /// He has left this scene by what has happened rather than where he stands (<c>sceneName</c>'s DL-06 → DL-07: the
        /// belt runs to the exit, L8141). Asked at the step's end, for the scene that holds him by position; true hands
        /// him to the next scene of the region (or out of the chapter). Default: never.
        /// </summary>
        public virtual bool HasLeft(ChapterSim sim) => false;
    }
}
