using System;
using DeadLetter.Core.Lane;

namespace DeadLetter.Core.Carry
{
    /// <summary>
    /// A <see cref="CarriedItem"/> on the lane: while it rests on the floor it is a block he can stand on and climb
    /// (<see cref="CarriedItem.TopAt"/>: the box, <c>surfaceCh1</c> L4150; DL-03's weight, <c>surfaceAt</c> L1726). In his
    /// hands, placed or gone, it is nothing. It reads state only, as every contributor does.
    /// </summary>
    public sealed class CarriedItemLane : LaneContributor
    {
        private readonly CarriedItem _item;
        private readonly double _x0, _x1;

        /// <param name="windowX0">The item counts only for windowX0 &lt; x &lt; windowX1 (DL-02's box: <c>x &gt; SH.x0 &amp;&amp; x &lt; SH.x1 + 0.4</c>, L4145–L4147).</param>
        public CarriedItemLane(CarriedItem item, double windowX0 = double.NegativeInfinity, double windowX1 = double.PositiveInfinity)
        {
            _item = item ?? throw new ArgumentNullException(nameof(item));
            _x0 = windowX0; _x1 = windowX1;
        }

        public override double Surface(double x, double surface)
        {
            if (!(x > _x0 && x < _x1)) return surface;
            double top = _item.TopAt(x);
            return double.IsNaN(top) ? surface : Math.Max(surface, top);
        }
    }
}
