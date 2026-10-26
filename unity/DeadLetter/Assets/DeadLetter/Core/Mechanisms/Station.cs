using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms
{
    /// <summary>Where D-17 stands to use a fixed control, and from where it answers (§4.9, §4.12).</summary>
    public readonly struct Station
    {
        public readonly double StandX;
        /// <summary>Use answers when |x − <see cref="ReachX"/>| &lt; Reach.</summary>
        public readonly double Reach;
        public readonly int Face;
        /// <summary>Unity z he steps to (+ into the set; the prototype's z negated, §0.2).</summary>
        public readonly double StandZ;
        /// <summary>The floor he must be on: answers only while y ≤ FloorY + 0.05 (L1810, L3267).</summary>
        public readonly double FloorY;
        /// <summary>Centre of the reach test; the prototype sometimes stands off it (DL-13 brake: stand pawlX − 0.2, reach from pawlX, L5290/L5298).</summary>
        public readonly double ReachX;

        public Station(double standX, double reach, int face, double standZ = 0, double floorY = 0, double reachX = double.NaN)
        {
            StandX = standX; Reach = reach; Face = face; StandZ = standZ; FloorY = floorY;
            ReachX = double.IsNaN(reachX) ? standX : reachX;
        }
    }

    /// <summary>
    /// A mechanism D-17 operates with Use (latch, pawl lever, crank, brake): implements the U-11 <see cref="IUsable"/>
    /// station contract from a <see cref="Station"/>. Derived types add <see cref="CanUse"/> (state conditions),
    /// <see cref="Profile"/> and <see cref="OnActFrame"/>, which must only record the frame (see <see cref="ActInput"/>).
    /// </summary>
    public abstract class StationMechanism : Mechanism, IUsable
    {
        public const double FloorTolerance = 0.05;

        protected StationMechanism(MechanismId id, in Station station) : base(id) { Station = station; }

        public Station Station { get; }

        public InteractionCategory Category => InteractionCategory.Fixed;
        public double StandX => Station.StandX;
        /// <summary>The resolver tests |x − StandX| &lt; Reach; widened so it never refuses what <see cref="IsAvailable"/> accepts.</summary>
        public double Reach => Math.Abs(Station.ReachX - Station.StandX) + Station.Reach;
        public double StandZ => Station.StandZ;
        public int Face => Station.Face;
        public double AnchorX => Station.ReachX;

        public bool IsAvailable(in InteractionQuery q)
            => q.Y <= Station.FloorY + FloorTolerance && Math.Abs(q.X - Station.ReachX) < Station.Reach && CanUse(q);

        /// <summary>State conditions (e.g. not already released).</summary>
        protected abstract bool CanUse(in InteractionQuery q);

        public abstract ActProfile Profile { get; }

        /// <summary>Record the frame with <c>_act.Receive(f)</c>; return true when the act is over (a pure function of the frame and state).</summary>
        public abstract bool OnActFrame(in ActFrame f);
    }

    /// <summary>
    /// The latest act frame a station received, held for <see cref="Mechanism.Step"/>. The motor calls OnActFrame during
    /// the player update (step #4), before the graph steps (#6), so Step sees this tick's frame, as the prototype's
    /// <c>updateAct</c> did. Call <see cref="Take"/> once at the top of Step.
    /// </summary>
    public struct ActInput
    {
        /// <summary>A frame arrived for this step: the act is running.</summary>
        public bool Active;
        /// <summary>This step is the first of a new act.</summary>
        public bool Started;
        /// <summary>Clip frame (24 fps, unwrapped for loops), previous frame, seconds since the clip started, stick.</summary>
        public double Frame, PrevFrame, Time, Move;
        private bool _fed;

        public void Receive(in ActFrame f)
        {
            _fed = true; Frame = f.Frame; PrevFrame = f.PrevFrame; Time = f.Time; Move = f.Input.Move;
        }

        public void Take()
        {
            Started = _fed && !Active;
            Active = _fed;
            _fed = false;
        }

        public void Clear() => this = default;

        public void Write(ISnapshotWriter w)
        {
            w.WriteBool("act.fed", _fed); w.WriteBool("act.active", Active);
            w.WriteDouble("act.frame", Frame); w.WriteDouble("act.prev", PrevFrame);
            w.WriteDouble("act.time", Time); w.WriteDouble("act.move", Move);
        }

        public void Read(ISnapshotReader r)
        {
            _fed = r.ReadBool("act.fed"); Active = r.ReadBool("act.active");
            Frame = r.ReadDouble("act.frame"); PrevFrame = r.ReadDouble("act.prev");
            Time = r.ReadDouble("act.time"); Move = r.ReadDouble("act.move");
            Started = false;
        }
    }
}
