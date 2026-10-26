namespace DeadLetter.Core.Mechanisms
{
    // =================================================================================================================
    // Signals: the only way one mechanism reads another (port_architecture §4.13l). A mechanism implements the signals it
    // produces; a consumer names its source by MechanismId in its params and resolves it once in Link():
    //
    //     _platform = link.Read<IPositionSource>(p.Source);       // source steps earlier: this tick's value
    //     _cage     = link.ReadAnyOrder<IPositionSource>(p.Cage); // read from an act, or a deliberate one-tick lag
    //
    // Reads are plain property gets on a resolved reference: no lookup, no allocation per tick.
    // Each producer documents its signal's unit (metres, degrees, 0..1) on the property.
    // =================================================================================================================

    /// <summary>A load measured or carried (plates, scales, strips, trays). Unit: the prototype's load shares (§4.13a).</summary>
    public interface ILoad
    {
        double Load { get; }
    }

    /// <summary>A position: a gate's height, a platform's travel, a cage's y, a crank's progress.</summary>
    public interface IPositionSource
    {
        double Position { get; }
    }

    /// <summary>A binary engagement: a latch released, a pawl bitten, a brake on, a door fully open, a cycle running.</summary>
    public interface IEngageable
    {
        bool Engaged { get; }
    }
}
