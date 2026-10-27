using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Lifts;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-08 The Handbrake's lane: region 4 (80.75 → 127.9, §0.3) from the residential doorway to the end of the returns
    /// belt (<c>CG.x0</c> 97.6, where DL-09 begins, <c>sceneName</c> L8143), on the deck at <c>DECK</c> 1.6 (he is up:
    /// <c>game.upper</c> from <c>landing</c> on). Lines are index.html at 7b3c123.
    /// <para>The static lane: the deck (<c>floorAt</c>: <c>x &gt; CORRIDOR_X0 → upper ? GALLERY.h : 0</c>, L1717); the walls
    /// <c>DOOR4_X − 0.6</c> and <c>REGION5_X + 1</c> (<c>leftLimit0</c>/<c>rightLimit0</c>, L1760, L1766); the hall's ceiling
    /// 6.5 (<c>ceilingAt</c>, L1629: nothing lower until DL-09's antechamber, <c>ceilingCh1</c> L4166); the far landing's
    /// safety rail <c>RAIL7</c> 88.6–88.75, 2.4 high (<c>surfaceCh1</c>, L4158; L3897).</para>
    /// <para>What moves (<see cref="Contributors"/>): Lift 2's shaft (85.8–88.3), whose floor is the platform's top
    /// (<c>platTop()</c>, L1714) and whose edges wall him while it is neither latched nor at the landing (<c>liftOpen</c>,
    /// L1755, L1760, L1766); the goods trolley, solid to the top of its ballast (L1732); the crates on the belt, solid while
    /// in the lane, and the belt itself, which carries him back while it runs (<c>beltCarry4</c>, L3439; L1733).</para>
    /// </summary>
    public static class Dl08Lane
    {
        public const int Region = 4;
        /// <summary><c>OFF3</c>, <c>OFF5</c> (L274); <c>DECK</c> (L3007).</summary>
        public const double Off3 = 33, Off5 = 54, Deck = 1.6;
        /// <summary><c>DOOR4_X</c>, <c>REGION4_X</c> (L3007); <c>REGION5_X</c> (L3446).</summary>
        public const double Door4X = Off3 + 47.5, Region4X = Off3 + 47.75, Region5X = Off5 + 73.9;
        /// <summary>The walls (L1760, L1766).</summary>
        public const double Left = Door4X - 0.6, Right = Region5X + 1;
        /// <summary>The hall's ceiling (L1629).</summary>
        public const double Ceiling = 6.5;
        /// <summary><c>SHAFT</c> (L3011); <c>HALF</c> (L310): walls <c>SHAFT.x0 − HALF + 0.08</c> and <c>SHAFT.x1 + HALF − 0.08</c> while shut.</summary>
        public const double ShaftX0 = Off3 + 52.8, ShaftX1 = Off3 + 55.3, Half = Dl03Lane.Half;
        /// <summary><c>liftOpen</c>: the platform at the landing (h ≥ 0.985) or latched (L1755).</summary>
        public const double OpenAt = 0.985;
        /// <summary><c>RAIL7</c> (L3897): the far landing's safety rail.</summary>
        public const double RailX0 = Off3 + 55.6, RailX1 = Off3 + 55.75, RailTop = Deck + 0.8;
        /// <summary><c>BELT4</c> (L3015): the returns belt.</summary>
        public const double BeltX0 = Off3 + 57.7, BeltX1 = Off3 + 64.6;
        /// <summary><c>CG.x0</c> (L3899): DL-08 ends, DL-09 (the slipping cage) begins.</summary>
        public const double X1 = Off3 + 64.6;

        /// <summary>Region 4's static lane (DL-08's stretch; DL-09's tables join it at <see cref="X1"/>).</summary>
        public static LaneTable Table() => new LaneTable
        {
            Name = "DL-08 (region 4, the goods hall)",
            Left = Left, Right = Right,                                                             // L1760, L1766
            Floor = Deck,                                                                           // upper: GALLERY.h, L1717 (Dl08ShaftLane: 0 if not)
            Ceiling = Ceiling,                                                                      // L1629
            Platforms = new[] { new LaneSpan(RailX0, RailX1, RailTop, SpanEdges.Closed) },         // x >= RAIL7.x0 && x <= RAIL7.x1, L4158
        };

        /// <summary>The shaft (<c>dl08.platform</c>, <c>dl07.gallery</c>), the goods trolley (<c>dl08.trolley</c>) and the belt (<c>dl08.belt</c>).</summary>
        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new Dl08ShaftLane(g.Get<CounterweightLift>("dl08.platform"), g.Get<IEngageable>("dl07.gallery")),
            new PushableTop(g.Get<Pushable>("dl08.trolley"), Door4X),                               // x > DOOR4_X, L1730–L1732
            new ReturnsBeltLane(g.Get<ReturnsBelt>("dl08.belt"), Door4X),
        };
    }

    /// <summary>
    /// Lift 2's shaft in the lane (<c>dl08.platform</c>): inside it (open ends) the floor is the platform's top
    /// (<c>platTop()</c>, L1714), elsewhere the deck while he is up (<c>game.upper</c>, <c>dl07.gallery</c>; else 0, L1717);
    /// while the platform is neither latched nor at the landing (<c>liftOpen</c>, L1755) its edges wall him on whichever side
    /// he stands (<c>leftLimit0</c>/<c>rightLimit0</c> for region 4, L1760, L1766).
    /// </summary>
    public sealed class Dl08ShaftLane : LaneContributor
    {
        private readonly CounterweightLift _platform;
        private readonly IEngageable _upper;

        public Dl08ShaftLane(CounterweightLift platform, IEngageable upper)
        {
            _platform = platform ?? throw new ArgumentNullException(nameof(platform));
            _upper = upper ?? throw new ArgumentNullException(nameof(upper));
        }

        /// <summary><c>liftOpen()</c>: <c>plat.latched || plat.h ≥ 0.985</c> (L1755).</summary>
        public bool Open => _platform.Latched || _platform.H >= Dl08Lane.OpenAt;

        public override double Floor(double x, double floor)
        {
            if (x > Dl08Lane.ShaftX0 && x < Dl08Lane.ShaftX1) return _platform.FloorAt(_platform.H);        // L1714
            return _upper.Engaged ? floor : 0;                                                              // L1717
        }

        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (Open) return;
            if (x >= Dl08Lane.ShaftX1 - 0.05) left = Math.Max(left, Dl08Lane.ShaftX1 + Dl08Lane.Half - 0.08);    // L1760
            if (x <= Dl08Lane.ShaftX0 + 0.05) right = Math.Min(right, Dl08Lane.ShaftX0 - Dl08Lane.Half + 0.08);  // L1766
        }
    }

    /// <summary>
    /// The returns belt in the lane (<c>dl08.belt</c>): its crates' tops while they are on it in the lane (<c>surfaceAt</c>,
    /// L1733) and, while it runs, the ground that carries him back toward the landing (<c>beltCarry4</c>, L3439: the motor
    /// asks it while he walks grounded, <see cref="ILaneConveyor"/>).
    /// </summary>
    public sealed class ReturnsBeltLane : LaneContributor, ILaneConveyor
    {
        private readonly ReturnsBelt _belt;
        private readonly double _window;

        /// <param name="windowX0">It counts only for x &gt; windowX0 (<c>x &gt; DOOR4_X</c>, L1730).</param>
        public ReturnsBeltLane(ReturnsBelt belt, double windowX0 = double.NegativeInfinity)
        {
            _belt = belt ?? throw new ArgumentNullException(nameof(belt));
            _window = windowX0;
        }

        public override double Surface(double x, double surface) => x > _window ? _belt.SurfaceAt(x, surface) : surface;

        public double CarryAt(double x, double y) => _belt.CarryVelocity(x);
    }
}
