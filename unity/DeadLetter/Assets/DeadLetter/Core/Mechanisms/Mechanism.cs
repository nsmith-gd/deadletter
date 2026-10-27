using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms
{
    /// <summary>
    /// Base of every mechanism. It owns the named state (an int holding the type's State enum) and the log calls.
    /// A derived type:
    /// <list type="bullet">
    /// <item>declares <c>enum XState</c> and <c>enum XEvent</c> next to the class, and exposes
    /// <c>public XState State => (XState)StateCode;</c></item>
    /// <item>changes state only in <see cref="Step"/>, through <see cref="Enter"/> (logged), or in Reset/Restore through
    /// <see cref="Init"/> (not logged). Interaction callbacks (OnActFrame, Throw, ...) only record input for Step.</item>
    /// <item>snapshots its own fields in <see cref="WriteFields"/>/<see cref="ReadFields"/>; the state is written here.</item>
    /// </list>
    /// </summary>
    public abstract class Mechanism : IMechanism
    {
        protected Mechanism(MechanismId id)
        {
            if (id.IsNone) throw new System.ArgumentException("A mechanism needs an ID.", nameof(id));
            Id = id;
        }

        public MechanismId Id { get; }

        /// <summary>The current State enum value, as an int.</summary>
        public int StateCode { get; private set; }

        public virtual void Link(MechanismLinker link) { }
        public abstract void Reset(in Checkpoint checkpoint);
        public abstract void Step(in StepContext ctx);

        public void Snapshot(ISnapshotWriter w)
        {
            w.WriteLong("state", StateCode);
            WriteFields(w);
        }

        public void Restore(ISnapshotReader r)
        {
            StateCode = (int)r.ReadLong("state");
            ReadFields(r);
        }

        protected abstract void WriteFields(ISnapshotWriter w);
        protected abstract void ReadFields(ISnapshotReader r);

        /// <summary>Set the state without logging (Reset and the constructor).</summary>
        protected void Init(int state) => StateCode = state;

        /// <summary>Enter a state; logs a <see cref="MechanismEventKind.State"/> entry if it changed.</summary>
        protected void Enter(in StepContext ctx, int state)
        {
            if (state == StateCode) return;
            StateCode = state;
            ctx.Log.Add(new MechanismEvent(Id, MechanismEventKind.State, state, 0, 0, ctx.Tick));
        }

        /// <summary>Log a one-shot (a sound, a shake, a cue for U-14 or the camera).</summary>
        protected void Emit(in StepContext ctx, int evt, int index = 0, double value = 0)
            => ctx.Log.Add(new MechanismEvent(Id, MechanismEventKind.Event, evt, index, value, ctx.Tick));

        public override string ToString() => GetType().Name + " " + Id;
    }
}
