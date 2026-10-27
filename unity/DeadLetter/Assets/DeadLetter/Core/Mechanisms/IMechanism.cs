using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms
{
    /// <summary>
    /// A mechanism instance (port_architecture §4.13l). One class per mechanism type; scenes instantiate types with
    /// params. Lifecycle, all driven by <see cref="MechanismGraph"/>:
    /// <list type="number">
    /// <item><see cref="Link"/> once, in step order: resolve the signals this mechanism reads.</item>
    /// <item><see cref="Reset"/> on load and respawn, in step order: derive state from the checkpoint's solved flags;
    /// sources added earlier are already reset, so a consumer may read them.</item>
    /// <item><see cref="Step"/> every fixed step, in step order.</item>
    /// <item><see cref="Snapshot"/>/<see cref="Restore"/> at any tick boundary: every field that changes over time.</item>
    /// </list>
    /// Derive from <see cref="Mechanism"/> rather than implementing this directly.
    /// </summary>
    public interface IMechanism
    {
        MechanismId Id { get; }
        void Link(MechanismLinker link);
        void Reset(in Checkpoint checkpoint);
        void Step(in StepContext ctx);
        void Snapshot(ISnapshotWriter w);
        void Restore(ISnapshotReader r);
    }
}
