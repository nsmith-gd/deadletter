using System;
using System.Collections.Generic;

namespace DeadLetter.Core.Mechanisms
{
    /// <summary>
    /// The checkpoint a reset rebuilds the world for. Mechanism state on reload is derived from <see cref="Past"/>, the
    /// prototype's <c>past(cp, name)</c> (L3979): e.g. the DL-01 latch is released iff past <c>shutter</c> (§4.28).
    /// Each mechanism's params name the checkpoint that marks it solved (e.g. <c>ReleasedAfter = "shutter"</c>).
    /// U-14 owns the real CheckpointOrder/CheckpointDef in Core/Save; this is the minimal view mechanisms need.
    /// </summary>
    public readonly struct Checkpoint
    {
        /// <summary><c>CP_ORDER</c>, L3976–L3978: the prologue and chapter 1, in play order.</summary>
        public static readonly string[] PrototypeOrder =
        {
            "start", "shutter", "hall", "door", "room", "weighroom", "solved", "bay", "ration", "hatch", "scanned", "landing",
            "gallery", "goods", "latched", "cage", "landing8", "tunnel", "uponly", "ringc", "bedroom", "forwarded", "school",
            "register", "lesson", "gallery13", "window", "hatch14", "dorm", "corridor", "sickbay", "class6", "dismissed",
            "crossing", "store", "kitchen", "workshop",
        };

        private readonly IReadOnlyList<string> _order;
        private readonly int _index;

        public readonly string Name;

        public Checkpoint(IReadOnlyList<string> order, string name)
        {
            _order = order ?? throw new ArgumentNullException(nameof(order));
            _index = IndexIn(order, name);
            Name = name;
        }

        /// <summary>A checkpoint of the prototype's order.</summary>
        public static Checkpoint Prototype(string name) => new Checkpoint(PrototypeOrder, name);

        /// <summary>
        /// <c>past(cp, name)</c>: this checkpoint is <paramref name="name"/> or later. A null name means "never solved by a
        /// checkpoint" and returns false. An unknown name throws (catches typos in params).
        /// </summary>
        public bool Past(string name) => name != null && _index >= IndexIn(_order, name);

        private static int IndexIn(IReadOnlyList<string> order, string name)
        {
            for (int i = 0; i < order.Count; i++) if (string.Equals(order[i], name, StringComparison.Ordinal)) return i;
            throw new ArgumentException("Unknown checkpoint '" + name + "'.", nameof(name));
        }

        public override string ToString() => Name;
    }
}
