using System.Collections.Generic;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;

namespace DeadLetter.Core.Simulation.Replay
{
    /// <summary>
    /// A scripted player's view of a <see cref="ChapterSim"/> (one Core world per chapter): the fields bot.js reads from
    /// the prototype, mapped from the chapter's state. Read-only on the sim; <see cref="Step"/> is one
    /// <see cref="ChapterSim.Step"/>.
    /// </summary>
    public sealed class ChapterSimTarget : ISimTarget, ICueSource
    {
        private static readonly string[] VerbNames = BuildVerbNames();
        private bool _started;

        public ChapterSimTarget(ChapterSim sim) { Sim = sim; }

        public ChapterSim Sim { get; }

        /// <summary>A new game (<see cref="ChapterSim.NewGame"/>). From the opening, control comes after the first step, as <c>startPlay</c> runs in it.</summary>
        public ChapterSimTarget NewGame(bool fromOpening)
        {
            Sim.NewGame(fromOpening);
            _started = !fromOpening;
            return this;
        }

        /// <summary>Begins at <paramref name="checkpoint"/> (<see cref="ChapterSim.Begin"/>).</summary>
        public ChapterSimTarget Begin(string checkpoint, bool fromOpening = false)
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
        /// What bot.js reads as <c>G.act.kind</c>: a scene act's kind, else the motor act's target mechanism ("dl01.latch")
        /// or its verb in lower case ("quirk", "stuck", "death"). The mantle and DL-01's passage are not acts to bot.js
        /// (<c>G.mantle</c>, <c>G.transit</c>): it walks on through them, and they ignore input.
        /// </summary>
        public string Act
        {
            get
            {
                if (Sim.Act != null) return Sim.SceneActKind == ActIds.Transit ? null : Sim.SceneActKind.Name;
                var m = Sim.Motor;
                if (!m.IsActing) return null;
                if (m.ActTarget is IMechanism mech) return mech.Id.Value;
                return VerbNames[(int)m.ActVerb];
            }
        }

        /// <summary>
        /// A quirk a move cancels (<c>G.act.kind === 'quirk' &amp;&amp; G.act.cancel</c>, bot.js L33). Core keeps the flag
        /// private (asked on #16), so it is inferred: in the prologue only the wake's label (DL-01's scene <see cref="QuirkAct"/>,
        /// L8107) and the flinch (<c>Motor.Flinch</c>, L1875) are uncancellable; every other quirk is <c>playQuirk(clip)</c>'s
        /// default (DL-05's label, L4941; Proud). Chapter 1's L5778 label is another uncancellable one: revisit with #18.
        /// </summary>
        public bool ActCancellable
        {
            get
            {
                if (Sim.Act != null)
                    return Sim.SceneActKind == ActIds.Quirk && !(Sim.SceneActPhase.Name == ClipNames.CheckLabel && Sim.Current != null && Sim.Current.Id == "DL-01");
                var m = Sim.Motor;
                return m.IsActing && m.ActVerb == Verb.Quirk && m.Clip != ClipNames.Flinch;
            }
        }

        public HoldKind Hold => Sim.Motor.Hold;
        public bool Riding => Sim.Motor.Ride != null;
        public bool Playing => _started && Sim.RespawnAt <= 0;
        public bool InTransit => Sim.Act != null && Sim.SceneActKind == ActIds.Transit;
        public int Region => Sim.Region;
        public string Checkpoint => Sim.Checkpoints.Current.Name;

        /// <summary>The prototype's <c>sceneName()</c>: "DL-01 The Wake"; null once he is past the chapter's last scene.</summary>
        public string SceneName
        {
            get
            {
                var s = Sim.Current;
                if (s == null) return null;
                return string.IsNullOrEmpty(s.Title) ? s.Id : s.Id + " " + s.Title;
            }
        }

        public string Near
        {
            get
            {
                if (Sim.Act != null || !Sim.Motor.PreviewUse(out var c) || c.Target == null) return null;
                return c.Target is IMechanism m ? m.Id.Value : c.Target.GetType().Name;
            }
        }

        public int Deaths => Sim.Deaths;
        public int Found => 0;
        public MechanismGraph Mechanisms => Sim.Graph;
        public IReadOnlyList<Cue> Cues => Sim.Cues;
        public T Shared<T>() where T : class, new() => Sim.Shared<T>();

        public void Step(in MotorInput input)
        {
            Sim.Step(input);
            _started = true;
        }

        private static string[] BuildVerbNames()
        {
            var values = (Verb[])System.Enum.GetValues(typeof(Verb));
            int max = 0;
            foreach (var v in values) if ((int)v > max) max = (int)v;
            var names = new string[max + 1];
            foreach (var v in values) names[(int)v] = v.ToString().ToLowerInvariant();
            return names;
        }
    }
}
