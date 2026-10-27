using System.Collections.Generic;

namespace DeadLetter.Core.Mechanisms
{
    public enum MechanismEventKind : byte
    {
        /// <summary>The mechanism entered a named state; <see cref="MechanismEvent.Code"/> is its State enum value.</summary>
        State,
        /// <summary>A one-shot happened (a slam, a stroke, a lamp lit); <see cref="MechanismEvent.Code"/> is its Event enum value.</summary>
        Event,
    }

    /// <summary>
    /// One transition or one-shot. Codes are the mechanism type's own enums cast to int (e.g. <c>(int)LatchState.Released</c>),
    /// so a reader that knows the type casts back. Runtime views play sounds and shakes from these; U-14 sets
    /// checkpoints from them; tests assert on them.
    /// </summary>
    public readonly struct MechanismEvent
    {
        public readonly MechanismId Id;
        public readonly MechanismEventKind Kind;
        public readonly int Code;
        /// <summary>Which part (lamp, stroke); 0 when unused.</summary>
        public readonly int Index;
        /// <summary>A magnitude (impact speed, strength); 0 when unused.</summary>
        public readonly double Value;
        public readonly long Tick;

        public MechanismEvent(MechanismId id, MechanismEventKind kind, int code, int index, double value, long tick)
        {
            Id = id; Kind = kind; Code = code; Index = index; Value = value; Tick = tick;
        }

        public override string ToString() => Id + " " + (Kind == MechanismEventKind.State ? "state=" : "event=") + Code
            + (Index != 0 ? "#" + Index : "") + (Value != 0 ? " " + Value.ToString("R") : "") + " @" + Tick;
    }

    /// <summary>
    /// This step's transitions and one-shots, in the order they happened. Cleared at the start of every
    /// <see cref="MechanismGraph.Step"/> (like the motor's Events), so a consumer reads it after each step.
    /// Preallocated: adding does not allocate unless a step logs more than the capacity.
    /// </summary>
    public sealed class MechanismLog
    {
        private readonly List<MechanismEvent> _events;

        public MechanismLog(int capacity = 64) { _events = new List<MechanismEvent>(capacity); }

        public int Count => _events.Count;
        public MechanismEvent this[int i] => _events[i];

        public void Add(in MechanismEvent e) => _events.Add(e);
        public void Clear() => _events.Clear();

        /// <summary>True if <paramref name="id"/> logged <paramref name="code"/> of <paramref name="kind"/> this step.</summary>
        public bool Has(MechanismId id, MechanismEventKind kind, int code)
        {
            for (int i = 0; i < _events.Count; i++)
            {
                var e = _events[i];
                if (e.Kind == kind && e.Code == code && e.Id == id) return true;
            }
            return false;
        }
    }
}
