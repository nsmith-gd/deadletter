using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Simulation;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// A scene act's kind or phase (<see cref="SceneAct.Kind"/>, <see cref="SceneAct.Phase"/>), interned as a
    /// <see cref="Cues.CueId"/> is: a small integer, so the runtime matches the act D-17 is in by an integer compare and a step
    /// names it without allocating. The names are the prototype's (<c>game.act.kind</c>, its phase or clip), so a log or a
    /// trace replay reads them back with <see cref="Name"/>. Declare each as a static field (<see cref="ActIds"/>, or next to
    /// the act that uses it): <see cref="Of(string)"/> locks.
    /// </summary>
    public readonly struct ActId : IEquatable<ActId>
    {
        private static readonly NameTable Names = new NameTable();

        /// <summary>The interned number; 0 is <see cref="None"/>.</summary>
        public readonly int Value;

        private ActId(int value) { Value = value; }

        /// <summary>No act (<see cref="ChapterSim.SceneActKind"/> while the motor has him).</summary>
        public static ActId None => default;

        /// <summary>The kind or phase called <paramref name="name"/>, interned on first use (keep it in a static field: this locks).</summary>
        public static ActId Of(string name) => new ActId(Names.Of(name, "scene act kind or phase"));

        /// <summary>The act about mechanism <paramref name="id"/> (<c>dl06.scanner</c>).</summary>
        public static ActId Of(MechanismId id) => Of(id.Value);

        public string Name => Names.Name(Value);
        public bool IsNone => Value == 0;

        public bool Equals(ActId other) => Value == other.Value;
        public override bool Equals(object obj) => obj is ActId a && a.Value == Value;
        public override int GetHashCode() => Value;
        public static bool operator ==(ActId a, ActId b) => a.Value == b.Value;
        public static bool operator !=(ActId a, ActId b) => a.Value != b.Value;
        public override string ToString() => Name;
    }

    /// <summary>The scene acts' kinds and phases that are not one scene's (a scene's own sit next to its acts).</summary>
    public static class ActIds
    {
        /// <summary><see cref="QuirkAct"/>'s kind; its phase is the clip (<see cref="Clip"/>).</summary>
        public static readonly ActId Quirk = ActId.Of("quirk");
        /// <summary><see cref="Hazards.DeathAct"/>'s kind; its phase is the death's kind ("Crush").</summary>
        public static readonly ActId Death = ActId.Of("death");
        /// <summary>DL-01's passage (<see cref="TransitAct"/>); its phase is the leg (<see cref="Leg"/>).</summary>
        public static readonly ActId Transit = ActId.Of("transit");
        /// <summary>A phase called "act" (the realisation's, the bay touch's once he is there).</summary>
        public static readonly ActId Act = ActId.Of("act");

        private static readonly ActId[] Legs = new ActId[16];

        static ActIds()
        {
            for (int i = 0; i < Legs.Length; i++) Legs[i] = ActId.Of(i.ToString(System.Globalization.CultureInfo.InvariantCulture));
        }

        /// <summary>A transit's leg <paramref name="stage"/> as its phase ("0", "1" …); the prototype's <c>a.stage</c>.</summary>
        public static ActId Leg(int stage)
        {
            if (stage < 0 || stage >= Legs.Length) throw new ArgumentOutOfRangeException(nameof(stage), "A transit has at most " + Legs.Length + " legs.");
            return Legs[stage];
        }

        /// <summary>A clip played as an act's phase (a quirk's, a set-down's): <paramref name="clip"/> interned. Not per step.</summary>
        public static ActId Clip(string clip) => ActId.Of(clip);
    }
}
