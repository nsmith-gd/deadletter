using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Simulation;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// Test shim: one scene simulated on its own, as a <see cref="ChapterSim"/> over a one-scene <see cref="ChapterDef"/>
    /// (the prologue's checkpoint table, or the one given), with the per-scene view the scene tests and trace replays were written against:
    /// the scene's rules, the act as text (<see cref="ActKind"/>:<see cref="ActPhase"/>), cue names, and
    /// <see cref="Handover"/> (he walks in at rest from the scene before). Everything else is the chapter's. A game is a
    /// <see cref="ChapterSim"/> over <see cref="ChapterDefs.Prologue"/>; this exists so each scene's parity stays provable
    /// on its own window.
    /// </summary>
    public sealed class SceneSim
    {
        public const double StepSeconds = ChapterSim.StepSeconds;

        public SceneSim(SceneDef def, MotorConfig config = null, ISaveStore store = null)
            : this(def, ChapterDefs.PrologueCheckpoints, config, store) { }

        /// <summary>A scene of another chapter, with that chapter's checkpoint table (chapter 2's <see cref="ChapterDefs.SomeoneHomeCheckpoints"/>).</summary>
        public SceneSim(SceneDef def, CheckpointTable checkpoints, MotorConfig config = null, ISaveStore store = null)
        {
            Def = def ?? throw new ArgumentNullException(nameof(def));
            Chapter = new ChapterSim(new ChapterDef(def.Id, checkpoints, def), config, store);
        }

        public ChapterSim Chapter { get; }
        public SceneDef Def { get; }
        public SceneRules Rules => Chapter.RulesOf(Def);

        public MotorConfig Config => Chapter.Config;
        public D17Motor Motor => Chapter.Motor;
        public LaneGeometry Lane => Chapter.Lane;
        public MechanismGraph Graph => Chapter.Graph;
        public InteractionResolver Resolver => Chapter.Resolver;
        public CheckpointService Checkpoints => Chapter.Checkpoints;
        public FixedTick Tick => Chapter.Tick;
        public MotorSync Sync => Chapter.Sync;

        public double Clock { get => Chapter.Clock; set => Chapter.Clock = value; }
        public long Steps => Chapter.Steps;
        public int Region => Chapter.Region;
        /// <summary>He has left the scene (the one-scene chapter's end): the motor stops.</summary>
        public bool Exited => Chapter.Exited;
        public double RespawnAt { get => Chapter.RespawnAt; set => Chapter.RespawnAt = value; }
        public int Deaths => Chapter.Deaths;
        public SceneAct Act => Chapter.Act;

        /// <summary>This step's cues, as text ("music:racks", "shake:25").</summary>
        public IReadOnlyList<string> Cues
        {
            get
            {
                var names = new List<string>(Chapter.Cues.Count);
                foreach (var c in Chapter.Cues) names.Add(c.ToString());
                return names;
            }
        }

        public double X => Chapter.X;
        public double Y => Chapter.Y;
        public double Z => Chapter.Z;
        public double Yaw => Chapter.Yaw;
        public double Vx => Chapter.Vx;
        public double Vy => Chapter.Vy;
        public bool Grounded => Chapter.Grounded;
        public bool Busy => Chapter.Busy;
        public PlayerPose Pose => Chapter.Pose;
        public IInteractable MotorActTarget => Chapter.MotorActTarget;
        public IInteractable MotorActEndedOn => Chapter.MotorActEndedOn;

        /// <summary>
        /// What he is doing, as text: a scene act's kind; the motor's quirk ("quirk"), death ("death") or stuck act
        /// ("stuck"); its act's target mechanism ID (or "shove", or the verb); "mantle"; or null when he moves freely.
        /// </summary>
        public string ActKind => KindOf(Chapter);

        /// <summary>
        /// The act's phase as text: a scene act's own; a quirk's clip; a death's kind ("Crush"); the stuck act's clip
        /// ("Flinch" from 0.2 s); a clip the station chained (the latch's Flinch, <see cref="D17Motor.ActPart"/> &gt; 0);
        /// else the motor's <see cref="Motor.ActPhase"/>.
        /// </summary>
        public string ActPhase => PhaseOf(Chapter);

        /// <summary><see cref="ActKind"/> of any chapter (the whole-prologue replay names acts as the scene replays do).</summary>
        internal static string KindOf(ChapterSim c)
        {
            if (!c.SceneActKind.IsNone) return c.SceneActKind.Name;                       // the test boundary: interned ids to the prototype's names
            var m = c.Motor;
            if (m.IsMantling) return "mantle";
            if (!m.IsActing) return null;
            switch (m.ActVerb)
            {
                case Verb.Quirk: return "quirk";
                case Verb.Death: return "death";
                case Verb.Stuck: return "stuck";
                case Verb.None: return "shove";
            }
            return m.ActTarget is IMechanism mech ? mech.Id.Value : m.ActVerb.ToString();
        }

        /// <summary><see cref="ActPhase"/> of any chapter.</summary>
        internal static string PhaseOf(ChapterSim c)
        {
            if (!c.SceneActKind.IsNone) return c.SceneActPhase.IsNone ? null : c.SceneActPhase.Name;
            var m = c.Motor;
            if (!m.IsActing) return null;
            switch (m.ActVerb)
            {
                case Verb.Quirk: case Verb.Stuck: return m.Clip;
                case Verb.Death: return m.Clip.StartsWith("Death", StringComparison.Ordinal) ? m.Clip.Substring("Death".Length) : m.Clip;
            }
            return m.ActPart > 0 && m.ActPhase == global::DeadLetter.Core.Motor.ActPhase.Clip ? m.Clip : m.ActPhase.ToString();
        }

        public void NewGame(bool fromOpening = false) => Chapter.NewGame(fromOpening);
        public bool Continue() => Chapter.Continue();
        public void Begin(string checkpoint, bool fromOpening = false) => Chapter.Begin(checkpoint, fromOpening);
        public void Respawn() => Chapter.Respawn();

        /// <summary>
        /// He walks in from the previous scene at rest at (<paramref name="x"/>, <paramref name="y"/>), the world built at
        /// <paramref name="checkpoint"/> (which may be the previous scene's: DL-03 starts under DL-02's <c>room</c>), the game
        /// kept. A scene's replay starts here; a chapter never needs it (he walks on in one world).
        /// </summary>
        public void Handover(string checkpoint, double x, double y, int facing = 1) => Chapter.BeginAt(checkpoint, x, y, facing, Def.Region);

        public void Step(in MotorInput input) => Chapter.Step(input);
        public int Advance(double frameSeconds, Func<MotorInput> input) => Chapter.Advance(frameSeconds, input);
        public void StartAct(SceneAct act) => Chapter.StartAct(act);
        public void EndAct() => Chapter.EndAct();
        public void SetRegion(int region) => Chapter.SetRegion(region);
    }
}
