using System;

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

    /// <summary>Where a loose thing rests, as the prototype's item and pushable <c>state</c> strings say.</summary>
    public enum BodySupport
    {
        /// <summary>Not in the lane (stored on a hook, gone down a chute): weighs on nothing.</summary>
        Away,
        /// <summary>On the floor (<c>'floor'</c>, <c>'free'</c>).</summary>
        Floor,
        /// <summary>On the floor, in his hands (<c>game.hold === 'push'</c>): weighs as on the floor.</summary>
        Pushed,
        /// <summary>Riding something that moves (<c>'trolley'</c>): weighs where its carrier is (<see cref="IPlateBody.SupportX"/>).</summary>
        Carrier,
        /// <summary>Lifted by D-17 (<c>'carried'</c>): weighs with him.</summary>
        Carried,
        /// <summary>Set into its receiver (<c>'tray'</c>, <c>'car'</c>, <c>'peg'</c>).</summary>
        Placed,
    }

    /// <summary>
    /// A loose thing a plate can weigh: an item (U-12 Carry) or a pushable (Push). Producer: items and
    /// pushables; consumers: the Plates family, Docks, Routes.
    /// </summary>
    public interface IPlateBody
    {
        /// <summary>Lane x of its centre, metres.</summary>
        double X { get; }
        /// <summary>Lane x of what it rests on (its carrier's x when <see cref="Support"/> is Carrier; otherwise <see cref="X"/>).</summary>
        double SupportX { get; }
        BodySupport Support { get; }
    }

    /// <summary>
    /// What ride sync reads from a lift that carries D-17 (step #9, <c>syncRide</c>, L2959–L2964; §3.1): the floor he
    /// stands on, how fast it moved this tick, and whether the lift holds him to it. Mechanisms step at #6–7, so a
    /// ride sync at #9 places him on this tick's floor (the prototype's carrier fix: "without that he trails the carrier
    /// by a frame", L2959).
    /// </summary>
    public interface ILiftRide
    {
        /// <summary>Unity y of the floor he rides, metres, after this tick's move.</summary>
        double FloorY { get; }
        /// <summary>That floor's vertical velocity this tick, m/s (+ up): (FloorY − last tick's FloorY) / dt.</summary>
        double FloorVelocity { get; }
        /// <summary>
        /// The lift holds him to its floor this tick (the prototype's own rule, per lift, including any
        /// <c>game.grounded</c> test, read from <see cref="PlayerPose.Grounded"/>). Ride sync sets his y to
        /// <see cref="FloorY"/> while it is true.
        /// </summary>
        bool Carrying { get; }
    }

    /// <summary>
    /// An oriented box of a swept volume: a lane-x extent times a rectangle in the cross-section plane (D = depth from the
    /// frame's back wall toward the lane, Y = height). Leaves on one frame share the plane, so their hinge axes are parallel.
    /// </summary>
    public readonly struct SweptBox
    {
        public readonly double X0, X1;
        /// <summary>Centre (D, Y), unit axis (Ux, Uy) along its first half-extent Hu; the second axis is (−Uy, Ux), half-extent Hv.</summary>
        public readonly double Cd, Cy, Ux, Uy, Hu, Hv;

        public SweptBox(double x0, double x1, double cd, double cy, double ux, double uy, double hu, double hv)
        {
            X0 = x0; X1 = x1; Cd = cd; Cy = cy; Ux = ux; Uy = uy; Hu = hu; Hv = hv;
        }

        /// <summary>An axis-aligned box (D-17's body).</summary>
        public static SweptBox Aligned(double x0, double x1, double d0, double d1, double y0, double y1)
            => new SweptBox(x0, x1, (d0 + d1) / 2, (y0 + y1) / 2, 1, 0, (d1 - d0) / 2, (y1 - y0) / 2);

        /// <summary>True if the boxes overlap by more than <paramref name="margin"/> (touching is not overlapping). Separating axes.</summary>
        public static bool Overlap(in SweptBox a, in SweptBox b, double margin)
        {
            if (!(a.X0 < b.X1 - margin && b.X0 < a.X1 - margin)) return false;
            double dx = b.Cd - a.Cd, dy = b.Cy - a.Cy;
            return !Separated(a, b, a.Ux, a.Uy, dx, dy, margin) && !Separated(a, b, -a.Uy, a.Ux, dx, dy, margin)
                && !Separated(a, b, b.Ux, b.Uy, dx, dy, margin) && !Separated(a, b, -b.Uy, b.Ux, dx, dy, margin);
        }

        private static bool Separated(in SweptBox a, in SweptBox b, double nx, double ny, double dx, double dy, double margin)
        {
            double ra = a.Hu * Math.Abs(a.Ux * nx + a.Uy * ny) + a.Hv * Math.Abs(-a.Uy * nx + a.Ux * ny);
            double rb = b.Hu * Math.Abs(b.Ux * nx + b.Uy * ny) + b.Hv * Math.Abs(-b.Uy * nx + b.Ux * ny);
            return Math.Abs(dx * nx + dy * ny) >= ra + rb - margin;
        }
    }

    /// <summary>
    /// Something that occupies space a folding leaf sweeps through (another leaf; later a shelf or a bed section). The
    /// boxes describe its current pose.
    /// </summary>
    public interface ISweptVolume
    {
        int VolumeCount { get; }
        SweptBox Volume(int i);
    }
}
