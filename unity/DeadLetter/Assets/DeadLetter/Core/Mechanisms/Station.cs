using System;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Save;

namespace DeadLetter.Core.Mechanisms
{
    /// <summary>
    /// Where D-17 stands to use a fixed control, and from where it answers (§4.9, §4.12). <see cref="Pose"/> turns it
    /// into the <see cref="StationPose"/> for one query; <see cref="Answers"/> is its reach and floor test.
    /// </summary>
    public readonly struct Station
    {
        public readonly double StandX;
        /// <summary>Use answers when |x − <see cref="ReachX"/>| &lt; Reach.</summary>
        public readonly double Reach;
        /// <summary>Facing during the act: +1 / −1, or 0 to keep his facing (ignored with <see cref="FaceTowards"/>).</summary>
        public readonly int Face;
        /// <summary>Unity z he steps to (+ into the set; the prototype's z negated, §0.2).</summary>
        public readonly double StandZ;
        /// <summary>The floor he must be on: answers only while y ≤ FloorY + 0.05 (L1810, L3267).</summary>
        public readonly double FloorY;
        /// <summary>Centre of the reach test; the prototype sometimes stands off it (DL-13 brake: stand pawlX − 0.2, reach from pawlX, L5290/L5298).</summary>
        public readonly double ReachX;
        /// <summary>
        /// Face toward the control from whichever side he comes (DL-01's crank: <c>face = x &lt; CRANK_X ? 1 : −1</c>,
        /// L1835): +1 when he is left of <see cref="ReachX"/>, else −1.
        /// </summary>
        public readonly bool FaceTowards;
        /// <summary>
        /// How fast he steps in to <see cref="StandZ"/> and back out (m/s); NaN = the motor's (0.45, L1845, L3615). The
        /// prototype's levers and pawl step at 0.4 (<c>updateAct3</c> L2916, <c>updateAct4</c> L3306).
        /// </summary>
        public readonly double StepInSpeed;

        public Station(double standX, double reach, int face, double standZ = 0, double floorY = 0, double reachX = double.NaN,
            bool faceTowards = false, double stepInSpeed = double.NaN)
        {
            StandX = standX; Reach = reach; Face = face; StandZ = standZ; FloorY = floorY;
            ReachX = double.IsNaN(reachX) ? standX : reachX;
            FaceTowards = faceTowards;
            StepInSpeed = stepInSpeed;
        }

        /// <summary>The prototype's lever and pawl step-in speed (<c>game.z += … 0.4 · dt</c>, L2916, L3306).</summary>
        public const double LeverStepInSpeed = 0.4;

        /// <summary>He is in reach and on its floor.</summary>
        public bool Answers(in InteractionQuery q)
            => q.Y <= FloorY + StationMechanism.FloorTolerance && Math.Abs(q.X - ReachX) < Reach;

        /// <summary>The stand point, depth and facing for <paramref name="q"/>; the anchor is the reach centre.</summary>
        public StationPose Pose(in InteractionQuery q)
            => new StationPose(StandX, FaceTowards ? (q.X < ReachX ? 1 : -1) : Face, StandZ, ReachX, StepInSpeed);
    }

    /// <summary>
    /// A mechanism D-17 operates with Use (latch, pawl lever, crank, brake): implements the U-11 <see cref="IUsable"/>
    /// station contract from a <see cref="Station"/>. Derived types add <see cref="CanUse"/> (state conditions),
    /// <see cref="Profile"/> (asked when Use starts and again once he has stepped in) and <see cref="OnActFrame"/>, which
    /// must only record the frame (see <see cref="ActInput"/>) and answers Continue, Done, a follow-up clip or a hop.
    /// </summary>
    public abstract class StationMechanism : Mechanism, IUsable
    {
        public const double FloorTolerance = 0.05;

        protected StationMechanism(MechanismId id, in Station station) : base(id) { Station = station; }

        public Station Station { get; }

        public InteractionCategory Category => InteractionCategory.Fixed;

        public bool Offer(in InteractionQuery q, out StationPose pose)
        {
            if (Station.Answers(q) && CanUse(q)) { pose = Station.Pose(q); return true; }
            pose = default;
            return false;
        }

        public bool IsAvailable(in InteractionQuery q) => Offer(q, out _);

        /// <summary>State conditions (e.g. not already released).</summary>
        protected abstract bool CanUse(in InteractionQuery q);

        /// <summary>The act's clip and manner as the mechanism's state is now (re-read once he has stepped in).</summary>
        public abstract ActProfile Profile { get; }

        public ActProfile ProfileFor(in InteractionQuery q) => Profile;

        /// <summary>Record the frame with <c>_act.Receive(f)</c>; answer from the frame alone (a pure function of the frame and state).</summary>
        public abstract ActStep OnActFrame(in ActFrame f);
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
        /// <summary>Which clip of the act (0 = the profile's; then the follow-ups the station chained). Frames restart per part.</summary>
        public int Part;
        private bool _fed;
        private double _lastTaken;
        private int _lastPart;

        public void Receive(in ActFrame f)
        {
            _fed = true; Frame = f.Frame; PrevFrame = f.PrevFrame; Time = f.Time; Move = f.Input.Move; Part = f.Part;
        }

        public void Take()
        {
            // A new act, or a new act straight after the last (its first clip's frames start over); a chained part is not.
            Started = _fed && Part == 0 && (!Active || _lastPart != 0 || Frame < _lastTaken);
            Active = _fed;
            if (_fed) { _lastTaken = Frame; _lastPart = Part; }
            _fed = false;
        }

        public void Clear() => this = default;

        public void Write(ISnapshotWriter w)
        {
            w.WriteBool("act.fed", _fed); w.WriteBool("act.active", Active);
            w.WriteDouble("act.frame", Frame); w.WriteDouble("act.prev", PrevFrame);
            w.WriteDouble("act.time", Time); w.WriteDouble("act.move", Move); w.WriteDouble("act.last", _lastTaken);
            w.WriteLong("act.part", Part); w.WriteLong("act.lastPart", _lastPart);
        }

        public void Read(ISnapshotReader r)
        {
            _fed = r.ReadBool("act.fed"); Active = r.ReadBool("act.active");
            Frame = r.ReadDouble("act.frame"); PrevFrame = r.ReadDouble("act.prev");
            Time = r.ReadDouble("act.time"); Move = r.ReadDouble("act.move"); _lastTaken = r.ReadDouble("act.last");
            Part = (int)r.ReadLong("act.part"); _lastPart = (int)r.ReadLong("act.lastPart");
            Started = false;
        }
    }
}
