using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Bridges;

namespace DeadLetter.Core.Lane
{
    /// <summary>
    /// A pushable that tips into a pit and becomes a bridge (<see cref="TippingBridge"/>: DL-01's cart, DL-11's duct),
    /// on the lane: while it stands on the floor it is a box he can climb (<c>|x − cart.x| ≤ half</c> → its height,
    /// <c>surfaceCh1</c> L4146, L4161); once it is a bridge the pit's floor is its top (<c>floorCh1</c> L4138–L4139);
    /// while it falls it is neither. The pit itself is static (the scene's <see cref="LaneTable.Floors"/>).
    /// </summary>
    public sealed class TippingBridgeLane : LaneContributor
    {
        private readonly TippingBridge _b;
        private readonly TippingBridgeParams _p;
        private readonly double _x0, _x1;

        /// <param name="windowX0">The box counts only for windowX0 &lt; x &lt; windowX1 (DL-01's cart: <c>x &gt; 4 &amp;&amp; x &lt; SH.x1 + 0.4</c>, L4145).</param>
        public TippingBridgeLane(TippingBridge bridge, TippingBridgeParams p, double windowX0 = double.NegativeInfinity, double windowX1 = double.PositiveInfinity)
        {
            _b = bridge ?? throw new ArgumentNullException(nameof(bridge));
            _p = p ?? throw new ArgumentNullException(nameof(p));
            _x0 = windowX0; _x1 = windowX1;
        }

        public override double Floor(double x, double floor)
            => _b.Engaged && x > _p.PitX0 && x < _p.PitX1 ? _p.PitFloor + _p.Height : floor;

        public override double Surface(double x, double surface)
        {
            var s = _b.State;
            if ((s == TippingBridgeState.Free || s == TippingBridgeState.AtLip) && x > _x0 && x < _x1 && Math.Abs(x - _b.X) <= _p.Half)
                return Math.Max(surface, _p.Height);
            return surface;
        }
    }

    /// <summary>
    /// A ceiling made of a polyline that swings about a pivot by an angle read from a mechanism (DL-01's shutter: the
    /// path <c>SHUTTER_PATH</c> rotated by <c>game.shutterAngle</c> about <c>SHUTTER_PIVOT</c>, <c>rotatedPath</c> and
    /// <c>ceilingAt</c>, L1621–L1642). Where x lies over a segment (ends inclusive; near-vertical segments skipped), the
    /// ceiling is at most the segment's height there. The rotated points are cached per angle.
    /// </summary>
    public sealed class SwingingPathCeiling : LaneContributor
    {
        private const double DegToRad = Math.PI / 180;      // three.js MathUtils.DEG2RAD
        private readonly IPositionSource _angle;
        private readonly double[] _px, _py, _rx, _ry;
        private readonly double _pivotX, _pivotY;
        private double _cachedDeg = double.NaN;

        /// <param name="angleDeg">The swing in degrees, counter-clockwise in the lane plane (+x right, +y up).</param>
        /// <param name="points">Path points (x, y) at angle 0, flattened: x0, y0, x1, y1, ...</param>
        public SwingingPathCeiling(IPositionSource angleDeg, double pivotX, double pivotY, params double[] points)
        {
            _angle = angleDeg ?? throw new ArgumentNullException(nameof(angleDeg));
            if (points == null || points.Length < 4 || points.Length % 2 != 0) throw new ArgumentException("Two or more (x, y) points.");
            int n = points.Length / 2;
            _px = new double[n]; _py = new double[n]; _rx = new double[n]; _ry = new double[n];
            for (int i = 0; i < n; i++) { _px[i] = points[2 * i]; _py[i] = points[2 * i + 1]; }
            _pivotX = pivotX; _pivotY = pivotY;
        }

        public override double Ceiling(double x, double ceiling)
        {
            Rotate();
            double h = ceiling;
            for (int i = 0; i < _rx.Length - 1; i++)
            {
                double x0 = _rx[i], z0 = _ry[i], x1 = _rx[i + 1], z1 = _ry[i + 1];
                if (x >= Math.Min(x0, x1) && x <= Math.Max(x0, x1) && Math.Abs(x1 - x0) > 1e-4)
                    h = Math.Min(h, z0 + (z1 - z0) * (x - x0) / (x1 - x0));     // L1637
            }
            return h;
        }

        private void Rotate()
        {
            double deg = _angle.Position;
            if (deg == _cachedDeg) return;
            _cachedDeg = deg;
            double a = deg * DegToRad, c = Math.Cos(a), s = Math.Sin(a);
            for (int i = 0; i < _px.Length; i++)
            {
                double dx = _px[i] - _pivotX, dz = _py[i] - _pivotY;                // L1623
                _rx[i] = _pivotX + dx * c - dz * s;
                _ry[i] = _pivotY + dx * s + dz * c;
            }
        }
    }

    /// <summary>
    /// A wall that stands until a mechanism engages: while <see cref="IEngageable.Engaged"/> is false, D-17's centre
    /// stays at or left of <c>right</c> (and at or right of <c>left</c>). DL-01: the locked shutter holds him at
    /// <c>LOCKED_LIMIT</c> 3.02 until the latch is released (<c>game.released ? RIGHT_LIMIT : LOCKED_LIMIT</c>, L1765).
    /// </summary>
    public sealed class LockedWall : LaneContributor
    {
        private readonly IEngageable _until;
        private readonly double _left, _right;

        public LockedWall(IEngageable until, double right = double.PositiveInfinity, double left = double.NegativeInfinity)
        {
            _until = until ?? throw new ArgumentNullException(nameof(until));
            _left = left; _right = right;
        }

        public override void Limits(double x, double y, ref double left, ref double right)
        {
            if (_until.Engaged) return;
            if (_right < right) right = _right;
            if (_left > left) left = _left;
        }
    }
}
