using System;
using DeadLetter.Core.Simulation;

namespace DeadLetter.Core.Cues
{
    /// <summary>
    /// A presentation cue's name (music, a voice line, a sound, a shot, a directed moment, a shake): interned once into a
    /// small integer, so raising one in a step allocates nothing and comparing two is an integer compare. Declare each
    /// as a static field next to the rule that raises it, with the prototype's name:
    /// <c>public static readonly CueId MusicHall = CueId.Of("music:hall");</c>. The Runtime binds names to assets once.
    /// </summary>
    public readonly struct CueId : IEquatable<CueId>
    {
        private static readonly NameTable Names = new NameTable();

        /// <summary>The interned number; 0 is <see cref="None"/>.</summary>
        public readonly int Value;

        private CueId(int value) { Value = value; }

        public static CueId None => default;

        /// <summary>The cue called <paramref name="name"/>, interned on first use (keep it in a static field: this locks).</summary>
        public static CueId Of(string name) => new CueId(Names.Of(name, "cue"));

        public string Name => Names.Name(Value);
        public bool IsNone => Value == 0;

        public bool Equals(CueId other) => Value == other.Value;
        public override bool Equals(object obj) => obj is CueId c && c.Value == Value;
        public override int GetHashCode() => Value;
        public static bool operator ==(CueId a, CueId b) => a.Value == b.Value;
        public static bool operator !=(CueId a, CueId b) => a.Value != b.Value;
        public override string ToString() => Name;
    }

    /// <summary>
    /// A cue raised in one step (<c>ChapterSim.Cues</c>): its name and an integer argument whose meaning the cue's
    /// declaration gives (a shake's amount in hundredths), 0 when it has none.
    /// </summary>
    public readonly struct Cue : IEquatable<Cue>
    {
        public readonly CueId Id;
        public readonly int Arg;

        public Cue(CueId id, int arg = 0) { Id = id; Arg = arg; }

        public bool Equals(Cue other) => Id == other.Id && Arg == other.Arg;
        public override bool Equals(object obj) => obj is Cue c && Equals(c);
        public override int GetHashCode() => (Id.Value * 397) ^ Arg;

        /// <summary>"music:racks", or "shake:25" with an argument (allocates: for logs and tests, not per frame).</summary>
        public override string ToString() => Arg == 0 ? Id.Name : Id.Name + ":" + Arg;
    }
}
