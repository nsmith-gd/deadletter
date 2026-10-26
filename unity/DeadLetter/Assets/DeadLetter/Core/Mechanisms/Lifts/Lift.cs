using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms.Lifts
{

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
