using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes.Dl03;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-03 The Weight of the Job's lane: region 2 (12.2 → 60.3, §0.3) as far as he can reach from DL-03, i.e. the end
    /// of DL-02's gantry, the weighing room 25.1–30.6 and the floor beyond the gate. Lines are index.html at 7b3c123.
    /// <para>Not here: DL-02's own moving parts (its box, L4151), DL-04's bay door (<c>limitsCh1</c>, L4174) and DL-05's
    /// crawl ceiling (<c>ceilingCh1</c>, L4166): they are those scenes' contributors, out of reach from DL-03.</para>
    /// </summary>
    public static class Dl03Lane
    {
        public const int Region = 2;

        /// <summary><c>SH.x0 + 0.2</c> (L1761, L4175; <c>SH</c> L3887) and <c>REGION3_X + 1</c> (L1768, L2457).</summary>
        public const double Left = 12.0 + 0.2, Right = 33 + 27.3 + 1;
        /// <summary><c>ROOM_X0</c>, <c>ROOM_LEFT</c> = OFF2 + 12.1, OFF2 + 12.32 (L319).</summary>
        public const double RoomX0 = 13 + 12.1, RoomLeft = 13 + 12.32;
        /// <summary><c>GATE_X</c> = OFF2 + 17.6 (L323).</summary>
        public const double GateX = 13 + 17.6;
        /// <summary>DL-02's sorting table and gantry, with the sill into the weighing room (<c>SH.table</c>, <c>SH.gantry</c>, <c>SH.sill</c>, L3888; <c>surfaceCh1</c> L4148–L4150).</summary>
        public const double TableX0 = 18.6, TableX1 = 22.6, TableH = 0.75, GantryX0 = 22.4, SillX1 = 13 + 12.32, GantryH = 1.35;
        /// <summary>The ceilings: 4 up to the room (<c>x &lt; 2.6 ? 2.45 : 4</c>, L1632), 2.6 in it, 5.5 past the gate (L1629–L1630).</summary>
        public const double HallCeiling = 4, RoomCeiling = 2.6, RacksCeiling = 5.5;
        /// <summary><c>CORRIDOR_X0</c> = OFF3 + 26.9 (L2455): the scanner corridor's 2.4 (L1628).</summary>
        public const double CorridorX0 = 33 + 26.9, CorridorX1 = 33 + 30.0, CorridorCeiling = 2.4;
        /// <summary><c>HALF</c>, <c>CROUCH_H</c> (L309–L310).</summary>
        public const double Half = 0.17, CrouchH = 0.58;

        /// <summary>The static lane of region 2 around DL-03.</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-03 (region 2)",
            Left = Left, Right = Right,                                                             // leftLimit0/rightLimit0, L1761, L1768
            Floor = 0,                                                                               // floorAt, L1716
            Platforms = new[]
            {
                new LaneSpan(TableX0, TableX1, TableH, SpanEdges.Closed),                            // x >= SH.table.x0 && x <= x1, L4149
                new LaneSpan(GantryX0, SillX1, GantryH, SpanEdges.Closed),                           // x >= SH.gantry.x0 && x <= SH.sill.x1, L4150
            },
            Ceiling = RacksCeiling,                                                                  // x >= GATE_X: 5.5, L1629
            Ceilings = new[]
            {
                new LaneSpan(double.NegativeInfinity, RoomX0, HallCeiling, SpanEdges.OpenClosed),    // x <= ROOM_X0: 4 (L1628, L1632)
                new LaneSpan(RoomX0, GateX, RoomCeiling, SpanEdges.Open),                            // ROOM_X0 < x < GATE_X: 2.6, L1629
                new LaneSpan(CorridorX0, CorridorX1, CorridorCeiling, SpanEdges.Open),               // the corridor, L1628
            },
        };

        /// <summary>
        /// The moving parts: the trolley's deck (<c>dl03.trolley</c>), the weight's top (<c>dl03.weight</c>, on the floor
        /// or the deck), and the gate (<c>dl03.gate</c>: a wall while down, a ceiling while up) (L1625–L1631, L1724–L1728,
        /// L1749, L1761, L1768).
        /// </summary>
        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new PushableTop(g.Get<Pushable>("dl03.trolley"), RoomX0),
            new Dl03WeightTop(g.Get<Dl03Weight>("dl03.weight"), RoomX0),
            new FollowerGateLane(g.Get<FollowerActuator>("dl03.gate"), GateX, CrouchH + 0.02, 0.07, 0.06 + Half),
        };
    }

    /// <summary>
    /// A pushable you can stand on (DL-03's trolley deck: <c>|x − t.x| ≤ TROLLEY_HALF</c> → <c>TROLLEY_DECK</c>, L1725;
    /// DL-08's goods trolley, L1732): while it is on the floor, its top over [x − Half, x + Half] (ends inclusive).
    /// </summary>
    public sealed class PushableTop : LaneContributor
    {
        private readonly Pushable _p;
        private readonly double _window, _half, _top;

        /// <param name="windowX0">It counts only for x &gt; windowX0 (DL-03: <c>x &gt; ROOM_X0</c>, L1724).</param>
        public PushableTop(Pushable p, double windowX0 = double.NegativeInfinity, double half = double.NaN, double top = double.NaN)
        {
            _p = p ?? throw new ArgumentNullException(nameof(p));
            _window = windowX0;
            _half = double.IsNaN(half) ? p.Params.Half : half;
            _top = double.IsNaN(top) ? p.Params.Top : top;
        }

        public override double Surface(double x, double surface)
        {
            var s = _p.State;
            if (s != PushableState.Free && s != PushableState.AtLip && s != PushableState.Docked) return surface;
            return x > _window && Math.Abs(x - _p.X) <= _half && _top > surface ? _top : surface;
        }
    }

    /// <summary>
    /// DL-03's weight as something to climb: its top, <c>WEIGHT_H</c> above the floor or the deck, over |x − weightX| ≤
    /// <c>WEIGHT_R</c>; nothing while carried (L1726–L1727). With the deck it climbs as one ledge (<c>ledgeAhead</c>, L1743).
    /// </summary>
    public sealed class Dl03WeightTop : LaneContributor
    {
        private readonly Dl03Weight _w;
        private readonly double _window;

        public Dl03WeightTop(Dl03Weight w, double windowX0 = double.NegativeInfinity)
        {
            _w = w ?? throw new ArgumentNullException(nameof(w));
            _window = windowX0;
        }

        public override double Surface(double x, double surface)
        {
            if (_w.State == Dl03WeightState.Carried || !(x > _window)) return surface;
            if (Math.Abs(x - _w.X) > _w.Params.Radius) return surface;
            return Math.Max(surface, _w.BaseY + _w.Params.Height);
        }
    }

    /// <summary>
    /// A gate that follows a load (<see cref="FollowerActuator"/>; DL-03 L1630, L1749, L1761, L1768): below
    /// <c>blockBelow</c> (<c>gateBlocks()</c>: y &lt; CROUCH_H + 0.02) it is a wall <c>wallGap</c> either side of its x for
    /// D-17's centre; above it, its lower edge is the ceiling within <c>halfWidth</c> of its x.
    /// </summary>
    public sealed class FollowerGateLane : LaneContributor
    {
        private readonly IPositionSource _gate;
        private readonly double _x, _blockBelow, _halfWidth, _wallGap;

        public FollowerGateLane(IPositionSource gate, double x, double blockBelow, double halfWidth, double wallGap)
        {
            _gate = gate ?? throw new ArgumentNullException(nameof(gate));
            _x = x; _blockBelow = blockBelow; _halfWidth = halfWidth; _wallGap = wallGap;
        }

        public bool Blocks => _gate.Position < _blockBelow;

        public override double Ceiling(double x, double ceiling)
            => Math.Abs(x - _x) < _halfWidth && !Blocks ? Math.Min(ceiling, _gate.Position) : ceiling;   // L1630

        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (!Blocks) return;
            if (x < _x) right = Math.Min(right, _x - _wallGap);                                          // L1768
            else if (x > _x) left = Math.Max(left, _x + _wallGap);                                       // L1761
        }
    }
}
