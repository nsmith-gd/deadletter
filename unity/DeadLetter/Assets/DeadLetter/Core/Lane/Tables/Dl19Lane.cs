using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Lifts;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-19 A Repair That Held's lane: region 7 (chapter 2's set, as DL-18), game x 361.0 to 377.0, heights above the ring A
    /// datum (docs/scenes/DL-19_a_repair_that_held.md §3). No prototype: values cite the doc's sections. The terrace landing
    /// at 1.2 runs on from DL-18 to the half landing; the half landing (363.6–366.2) is a contributor
    /// (<see cref="HalfLandingLane"/>); the upper flight (366.2–367.4) is three risers of 0.18 from the landing's level 1.75,
    /// walked as a ramp; the upper terrace is 2.3 on to DL-20 at 377.0.
    /// <para>The skirt (364.3–366.2, §3 "to 1.67") closes the space under the half landing and is never a step: its top is
    /// under the plate in every state (a fixed 1.67 would stand proud of a plate drooping to 1.60 at 364.3), so the lane is
    /// the plate's top there. Under the plate's left end (363.6–364.3) is the jack's space, not his. The jack is a column
    /// while it is out of its bay (<see cref="JackLane"/>). No ceiling.</para>
    /// </summary>
    public static class Dl19Lane
    {
        public const int Region = Dl18Lane.Region;

        /// <summary>DL-19's stretch (chapter2_plan §4 table): from DL-18's end to DL-20's lower flat.</summary>
        public const double X0 = Dl18Lane.EndX, X1 = 377.0;
        /// <summary>The terrace landing (§3: 361.0–366.2 at 1.2; reachable to the half landing's left end).</summary>
        public const double FloorY = 1.2;
        /// <summary>The upper flight: from the hinge (366.2, the landing's level 1.75) to the upper terrace (367.4, 2.3), three risers (§3).</summary>
        public const double FlightX0 = 366.2, FlightX1 = 367.4, LevelY = 1.75, TerraceY = 2.3, Riser = (TerraceY - LevelY) / 3;
        /// <summary>A column, not a step: nothing he can jump to catches a face this tall (the jack, "not climbable", §3).</summary>
        public const double ColumnTop = 9.0;

        /// <summary>The static lane of DL-19's stretch.</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-19 (region 7)",
            Left = X0,                                                                   // DL-18's lane is west of it (joined: the outermost wall)
            Floor = FloorY,                                                              // the terrace landing (§3)
            Floors = new[]
            {
                new LaneSpan(FlightX0, FlightX0 + 0.4, LevelY, SpanEdges.ClosedOpen),   // the flight's foot, at the hinge (§3)
                new LaneSpan(FlightX0 + 0.4, FlightX0 + 0.8, LevelY + Riser, SpanEdges.ClosedOpen),
                new LaneSpan(FlightX0 + 0.8, FlightX1, LevelY + 2 * Riser, SpanEdges.ClosedOpen),
                new LaneSpan(FlightX1, X1, TerraceY, SpanEdges.ClosedOpen),             // the upper terrace (§3)
            },
            // "Three steps of about 0.18; walkable" (§3): a ramp zone, out past the top riser by his half-width (the motor
            // asks it at his leading edge).
            Ramps = new[] { new LaneSpan(FlightX0, FlightX1 + Dl18Lane.Half, 0, SpanEdges.Closed) },
        };

        /// <summary>The half landing's top, and the jack's column while it is out of its bay.</summary>
        public static ILaneContributor[] Contributors(MechanismGraph g)
        {
            var landing = g.Get<HalfLanding>("dl19.landing");
            return new ILaneContributor[]
            {
                new HalfLandingLane(landing),
                new JackLane(g.Get<RatchetJack>("dl19.jack"), landing.Params.LeftX),
            };
        }
    }

    /// <summary>
    /// The half landing in the lane: its sloped top (<see cref="HalfLanding.TopAt"/>) in every state, so he can mantle onto
    /// the drooping end and lurch (DL-19 §3 "The half landing's states"); the scene's rules hop him back off it unless it is
    /// pinned.
    /// </summary>
    public sealed class HalfLandingLane : LaneContributor
    {
        private readonly HalfLanding _l;

        public HalfLandingLane(HalfLanding landing) { _l = landing ?? throw new ArgumentNullException(nameof(landing)); }

        public override double Surface(double x, double surface)
        {
            double top = _l.TopAt(x);
            return double.IsNaN(top) || top <= surface ? surface : top;
        }
    }

    /// <summary>
    /// The jack in the lane: in its bay it is off the lane line (§3 "Jack bay": "off the lane line"); out of it, its chassis
    /// left of the half landing (its crank post end) is a column he can neither step, mantle nor catch: "The jack is not
    /// climbable: no flat surface, the crank wheel and ratchet on top" (§3). So with the jack in its pocket the mantle spot
    /// (363.35–363.6) is its, and a mantle or jump toward the half landing meets the column first (§10 "Blocked spot").
    /// </summary>
    public sealed class JackLane : LaneContributor
    {
        private readonly RatchetJack _jack;
        private readonly double _until;

        /// <param name="until">The half landing's left end: under the plate the plate is the lane.</param>
        public JackLane(RatchetJack jack, double until)
        {
            _jack = jack ?? throw new ArgumentNullException(nameof(jack));
            _until = until;
        }

        public override double Surface(double x, double surface)
        {
            if (_jack.State == RatchetJackState.Parked || x < _jack.X0 || x >= Math.Min(_jack.X1, _until)) return surface;
            return Math.Max(surface, Dl19Lane.ColumnTop);
        }
    }
}
