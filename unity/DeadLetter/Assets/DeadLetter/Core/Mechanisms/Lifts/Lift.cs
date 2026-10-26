using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Lifts
{
    /// <summary>
    /// What ride sync reads from a lift that carries D-17 (step #9, <c>syncRide</c>, L2959–L2964; §3.1): the floor he
    /// stands on, how fast it moved this tick, and whether the lift holds him to it. Mechanisms step at #6–7, so a
    /// ride sync at #9 places him on this tick's floor (the prototype's carrier fix: "without that he trails the carrier
    /// by a frame", L2959).
    /// <para>Proposed for Signals.cs (framework change, see Mechanisms/README.md); it lives here until reviewed.</para>
    /// </summary>
    public interface ILiftRide
    {
        /// <summary>Unity y of the floor he rides, metres, after this tick's move.</summary>
        double FloorY { get; }
        /// <summary>That floor's vertical velocity this tick, m/s (+ up): (FloorY − last tick's FloorY) / dt.</summary>
        double FloorVelocity { get; }
        /// <summary>
        /// The lift holds him to its floor this tick (the prototype's own rule, per lift). Ride sync sets his y to
        /// <see cref="FloorY"/> while it is true; where the prototype also requires <c>game.grounded</c> (DL-15), ride sync
        /// adds that test (PlayerPose has no Grounded yet).
        /// </summary>
        bool Carrying { get; }
    }

    /// <summary>
    /// Base of the lifts that carry D-17 (§4.13f): keeps <see cref="ILiftRide"/>'s floor and velocity and snapshots
    /// them. Derived types call <see cref="InitFloor"/> in Reset and <see cref="MoveFloor"/> once per Step, and
    /// implement <see cref="IPositionSource.Position"/> with their own documented unit.
    /// </summary>
    public abstract class Lift : Mechanism, IPositionSource, ILiftRide
    {
        /// <summary>Time thresholds compare with this slack (Mechanisms/README.md "Time").</summary>
        public const double Slack = 1e-9;

        protected Lift(MechanismId id) : base(id) { }

        public abstract double Position { get; }
        public double FloorY { get; private set; }
        public double FloorVelocity { get; private set; }
        public bool Carrying { get; protected set; }

        protected void InitFloor(double y)
        {
            FloorY = y;
            FloorVelocity = 0;
            Carrying = false;
        }

        protected void MoveFloor(in StepContext ctx, double y)
        {
            FloorVelocity = ctx.Dt > 0 ? (y - FloorY) / ctx.Dt : 0;
            FloorY = y;
        }

        /// <summary>The prototype's <c>t &gt; s</c> on accumulated time.</summary>
        protected static bool After(double t, double s) => t > s + Slack;

        /// <summary>The prototype's <c>t &gt;= s</c> on accumulated time.</summary>
        protected static bool Reached(double t, double s) => t >= s - Slack;

        protected sealed override void WriteFields(ISnapshotWriter w)
        {
            w.WriteDouble("floorY", FloorY);
            w.WriteDouble("floorV", FloorVelocity);
            w.WriteBool("carrying", Carrying);
            WriteLift(w);
        }

        protected sealed override void ReadFields(ISnapshotReader r)
        {
            FloorY = r.ReadDouble("floorY");
            FloorVelocity = r.ReadDouble("floorV");
            Carrying = r.ReadBool("carrying");
            ReadLift(r);
        }

        protected abstract void WriteLift(ISnapshotWriter w);
        protected abstract void ReadLift(ISnapshotReader r);
    }
}
