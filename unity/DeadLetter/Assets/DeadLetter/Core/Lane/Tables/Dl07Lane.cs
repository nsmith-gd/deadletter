using System;
using DeadLetter.Core.Mechanisms;

namespace DeadLetter.Core.Lane.Tables
{
    /// <summary>
    /// DL-07 The Heap's lane: the gallery over DL-06's sorting floor (region 3 with <c>game.upper</c>, §0.3). DL-07 shares
    /// DL-06's floor (<see cref="Dl06Lane"/>, its table and its weights); up on the gallery the lane is another one, which
    /// <see cref="GalleryLane"/> lays over the floor's while he is up there. Lines are index.html at 7b3c123.
    /// <para>On the gallery: the deck at <c>GALLERY.h</c> 1.6 (<c>floorAt</c>, L1717); the walls <c>GALLERY.x0 + 0.15</c> and
    /// <c>REGION4_X + 1</c> (<c>leftLimit0</c>/<c>rightLimit0</c>, L1759, L1765); the gate's wall while it is under 0.8
    /// (<c>HP.gateX − 0.06 − HALF</c>, L4179); the slide's head (<c>HP.slide[0][0] + 0.1</c>, L4180); and once the collapse
    /// has started, the torn edge past it (<c>GALLERY6.x1 + 0.19</c>, L4181). The floor's weights are not solid up here
    /// (<c>!game.upper</c>, L4154). The hall's ceiling (6.5, L1629) is the floor's own past the corridor, where the gallery
    /// lies.</para>
    /// </summary>
    public static class Dl07Lane
    {
        public const int Region = Dl06Lane.Region;
        public const double Off3 = Dl06Lane.Off3;

        /// <summary><c>GALLERY</c> (L2459): x0, x1 and the deck's height.</summary>
        public const double GalleryX0 = Off3 + 38.85, GalleryX1 = Off3 + 47.4, Deck = 1.6;
        /// <summary>The gallery's walls (L1759, L1765): <c>GALLERY.x0 + 0.15</c>, <c>REGION4_X + 1</c>.</summary>
        public const double Left = GalleryX0 + 0.15, Right = Dl06Lane.Region4X + 1;
        /// <summary><c>HP.gateX</c> (L3893); it walls him <c>0.06 + HALF</c> short while under 0.8 (L4179).</summary>
        public const double GateX = Off3 + 41.9, GateGap = 0.06 + Dl03Lane.Half, GatePass = 0.8;
        /// <summary>The slide's head, <c>HP.slide[0][0]</c> (L3894), and its wall 0.1 past it (L4180).</summary>
        public const double SlideHeadX = Off3 + 38.85, SlideWall = SlideHeadX + 0.1;
        /// <summary><c>GALLERY6</c> (L7318): the panel that gives way, and where it is triggered.</summary>
        public const double CollapseX0 = Off3 + 45.95, CollapseX1 = Off3 + 47.05, CollapseTrigger = Off3 + 47.35;
        /// <summary>Once it has started, past it he cannot go back: <c>GALLERY6.x1 + 0.19</c> (L4181).</summary>
        public const double CollapseWall = CollapseX1 + 0.19;

        /// <summary>
        /// The gallery over the floor (<c>dl07.gallery</c> engaged = he is up there, <c>game.upper</c>), with the gate's and
        /// the collapse's walls (<c>dl07.gate</c>, <c>dl07.collapse</c> engaged = it has started).
        /// </summary>
        public static ILaneContributor[] Contributors(MechanismGraph g) => new ILaneContributor[]
        {
            new GalleryLane(g.Get<IEngageable>("dl07.gallery"), g.Get<IPositionSource>("dl07.gate"), g.Get<IEngageable>("dl07.collapse")),
        };
    }

    /// <summary>
    /// The gallery's lane, laid over the sorting floor's while he is up there (<c>game.upper</c>; <see cref="Dl07Lane"/>):
    /// the deck, its walls, the gate, the slide's head and the collapse. Registered after the floor's contributors, so up
    /// here it answers for the floor's weights too (they are not solid on the gallery, L4154). Down on the floor it passes
    /// every probe through.
    /// </summary>
    public sealed class GalleryLane : LaneContributor
    {
        private readonly IEngageable _upper, _collapse;
        private readonly IPositionSource _gate;

        /// <param name="upper">Engaged while he is on the gallery.</param>
        /// <param name="gate">The gate's height (it walls him below <see cref="Dl07Lane.GatePass"/>).</param>
        /// <param name="collapse">Engaged once the collapse has started.</param>
        public GalleryLane(IEngageable upper, IPositionSource gate, IEngageable collapse)
        {
            _upper = upper ?? throw new ArgumentNullException(nameof(upper));
            _gate = gate ?? throw new ArgumentNullException(nameof(gate));
            _collapse = collapse ?? throw new ArgumentNullException(nameof(collapse));
        }

        /// <summary><c>x &gt; CORRIDOR_X0 → game.upper ? GALLERY.h : 0</c> (L1717): all of region 3 is past the corridor's start.</summary>
        public override double Floor(double x, double floor) => _upper.Engaged ? Dl07Lane.Deck : floor;

        /// <summary>The deck and nothing on it: the floor's weights count only below (L4154), and nothing else stands here.</summary>
        public override double Surface(double x, double surface) => _upper.Engaged ? Dl07Lane.Deck : surface;

        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (!_upper.Engaged) return;
            left = Dl07Lane.Left; right = Dl07Lane.Right;                                                          // L1759, L1765
            if (x < Dl07Lane.GateX && _gate.Position < Dl07Lane.GatePass) right = Math.Min(right, Dl07Lane.GateX - Dl07Lane.GateGap);   // L4179
            left = Math.Max(left, Dl07Lane.SlideWall);                                                              // L4180
            if (_collapse.Engaged && x > Dl07Lane.CollapseX1) left = Math.Max(left, Dl07Lane.CollapseWall);       // L4181
        }
    }
}
