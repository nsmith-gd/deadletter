namespace DeadLetter.Core.Lane
{
    /// <summary>
    /// Something that changes the lane while the game runs (port_architecture §4.6): a pushable box, a cart lying in a
    /// pit, a shutter's swinging edge, a gate's wall. <see cref="LaneGeometry"/> asks each contributor of the active
    /// region after the static <see cref="LaneTable"/>, in registration order, passing the answer so far; a contributor
    /// returns it unchanged where it has no say. That is how the prototype composes its probes: the per-region code first,
    /// then <c>floorCh1</c>/<c>surfaceCh1</c>/<c>ceilingCh1</c>/<c>limitsCh1</c> (L4135–L4201) on top.
    /// <para>Mechanisms do not implement this themselves: an adapter in <c>Core/Lane</c> reads their signals
    /// (<see cref="Mechanisms.IPositionSource"/>, <see cref="Mechanisms.IEngageable"/>, or the public state of a
    /// mechanism type) so no mechanism needs editing. Contributors read state only (no allocation, no side effects): the
    /// motor probes many times a step, before the graph steps (§3.1 #4 before #6), so they see last step's mechanism state,
    /// as the prototype's probes did.</para>
    /// <para>Derive from <see cref="LaneContributor"/>, which passes every probe through.</para>
    /// </summary>
    public interface ILaneContributor
    {
        /// <summary>The ground level at x (a pit, the cart lying in it). Return <paramref name="floor"/> to leave it.</summary>
        double Floor(double x, double floor);

        /// <summary>The standable top at x (≥ the floor normally). Return <paramref name="surface"/> to leave it.</summary>
        double Surface(double x, double surface);

        /// <summary>The ceiling's underside at x. Return <paramref name="ceiling"/> to leave it.</summary>
        double Ceiling(double x, double ceiling);

        /// <summary>Narrow the walls for D-17's centre at (x, y) (a closed gate, a locked shutter).</summary>
        void Limits(double x, double y, ref double left, ref double right);
    }

    /// <summary>
    /// Optional, on a contributor: a surface that depends on where he is standing as well as on x. Chapter 1's boards in
    /// the air (DL-13's steps, DL-14's ledges, DL-15's balcony) are solid only to someone already up at the level below
    /// them (<c>surfaceAtt</c> reads <c>game.y</c>, L5258–L5264). <see cref="LaneGeometry"/> passes the probe's reference
    /// height, the motor's feet as they are at that point of its step (<see cref="Motor.IMotorWorld.SurfaceAt"/>), which
    /// is the prototype's <c>game.y</c> at the same point; a probe with no reference height passes NaN (then nothing
    /// height-dependent answers). <see cref="ILaneContributor.Surface"/> is not called on such a contributor.
    /// </summary>
    public interface ILaneHeightContributor : ILaneContributor
    {
        /// <summary>The standable top at x for someone with feet at <paramref name="refY"/> (NaN: unknown).</summary>
        double Surface(double x, double refY, double surface);
    }

    /// <summary>Base for contributors: every probe passes through unchanged.</summary>
    public abstract class LaneContributor : ILaneContributor
    {
        public virtual double Floor(double x, double floor) => floor;
        public virtual double Surface(double x, double surface) => surface;
        public virtual double Ceiling(double x, double ceiling) => ceiling;
        public virtual void Limits(double x, double y, ref double left, ref double right) { }
    }
}
