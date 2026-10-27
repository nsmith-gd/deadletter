using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Bridges;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// A wall that stands until a mechanism engages: the DL-01 shutter's foot until the latch is released
    /// (<c>rightLimit0</c>: <c>released ? RIGHT_LIMIT : LOCKED_LIMIT</c>, L1764), a bay door, a gate. Blocks the side
    /// given by <see cref="RightSide"/> at <see cref="Limit"/> (a body-centre limit, already inset by HALF).
    /// </summary>
    public sealed class WallUntilEngaged : ILaneContributor
    {
        private readonly IEngageable _open;
        public readonly double Limit;
        public readonly bool RightSide;

        public WallUntilEngaged(IEngageable open, double limit, bool rightSide = true)
        {
            _open = open ?? throw new ArgumentNullException(nameof(open));
            Limit = limit;
            RightSide = rightSide;
        }

        public double Surface(double x, double refY, double h) => h;
        public double Ceiling(double x, double refY, double h) => h;

        public void Limits(double x, double y, ref double left, ref double right)
        {
            if (_open.Engaged) return;
            if (RightSide) right = Math.Min(right, Limit);
            else left = Math.Max(left, Limit);
        }
    }

    /// <summary>
    /// A ceiling whose underside is a polyline hinged at a pivot and swung by a mechanism's angle in degrees: the DL-01
    /// shutter (<c>SHUTTER_PATH</c>, <c>SHUTTER_PIVOT</c>, L275–L276; <c>rotatedPath</c>/<c>ceilingAt</c>, L1620–L1641).
    /// Like the prototype it ignores his height (the shutter is the only thing overhead there). Segments with no
    /// width (|dx| ≤ 1e-4) are skipped, as L1638.
    /// </summary>
    public sealed class HingedCeiling : ILaneContributor
    {
        private readonly IPositionSource _angleDeg;
        private readonly double[] _px, _py;
        private readonly double _pivotX, _pivotY;

        /// <param name="angleDeg">Swing in degrees (+ = counter-clockwise in the lane's x-y plane, the prototype's rotation.z).</param>
        /// <param name="path">Polyline points as (x, y) pairs, closed pose.</param>
        public HingedCeiling(IPositionSource angleDeg, double pivotX, double pivotY, params double[] path)
        {
            _angleDeg = angleDeg ?? throw new ArgumentNullException(nameof(angleDeg));
            if (path == null || path.Length < 4 || path.Length % 2 != 0) throw new ArgumentException("path needs two or more (x, y) points.", nameof(path));
            _pivotX = pivotX; _pivotY = pivotY;
            int n = path.Length / 2;
            _px = new double[n]; _py = new double[n];
            for (int i = 0; i < n; i++) { _px[i] = path[2 * i]; _py[i] = path[2 * i + 1]; }
        }

        public double Surface(double x, double refY, double h) => h;

        public double Ceiling(double x, double refY, double h)
        {
            double a = _angleDeg.Position * (Math.PI / 180), c = Math.Cos(a), s = Math.Sin(a);
            double x0 = Rx(0, c, s), y0 = Ry(0, c, s);
            for (int i = 1; i < _px.Length; i++)
            {
                double x1 = Rx(i, c, s), y1 = Ry(i, c, s);
                if (x >= Math.Min(x0, x1) && x <= Math.Max(x0, x1) && Math.Abs(x1 - x0) > 1e-4)
                    h = Math.Min(h, y0 + (y1 - y0) * (x - x0) / (x1 - x0));
                x0 = x1; y0 = y1;
            }
            return h;
        }

        public void Limits(double x, double y, ref double left, ref double right) { }

        private double Rx(int i, double c, double s) => _pivotX + (_px[i] - _pivotX) * c - (_py[i] - _pivotY) * s;
        private double Ry(int i, double c, double s) => _pivotY + (_px[i] - _pivotX) * s + (_py[i] - _pivotY) * c;
    }

    /// <summary>
    /// A <see cref="TippingBridge"/>'s collision: while it stands on the floor it is a block of its height
    /// (<c>surfaceCh1</c>, L4146: the cart; L4162: the duct); settled in its pit it raises the pit's floor to
    /// <c>PitFloor + Height</c> (<c>floorCh1</c>, L4140, L4139). While it tips it is neither (it is in the air).
    /// </summary>
    public sealed class TippingBridgeLane : ILaneContributor
    {
        private readonly TippingBridge _b;
        private readonly TippingBridgeParams _p;

        public TippingBridgeLane(TippingBridge bridge, TippingBridgeParams p)
        {
            _b = bridge ?? throw new ArgumentNullException(nameof(bridge));
            _p = p ?? throw new ArgumentNullException(nameof(p));
        }

        public double Surface(double x, double refY, double h)
        {
            TippingBridgeState st = _b.State;
            if (st == TippingBridgeState.Bridge)
            {
                if (x > _p.PitX0 && x < _p.PitX1) h = Math.Max(h, _p.PitFloor + _p.Height);
            }
            else if (st != TippingBridgeState.Falling && Math.Abs(x - _b.X) <= _p.Half) h = Math.Max(h, _p.Height);
            return h;
        }

        public double Ceiling(double x, double refY, double h) => h;
        public void Limits(double x, double y, ref double left, ref double right) { }
    }
}
