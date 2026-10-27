using System;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Loose;
using DeadLetter.Core.Mechanisms.Routes;
using DeadLetter.Core.Motor;

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

    /// <summary>
    /// A <see cref="Carryable"/> resting in the lane is a block (the DL-03 weight, <c>surfaceAt</c> L1726–L1727; the DL-02
    /// box and the plates, <c>surfaceCh1</c> L4150–L4156): its top, base + Height, within Radius. On a deck it stands on the
    /// deck. Plates and the case only count for a probe already at their base (|h − base| &lt; 0.05).
    /// </summary>
    public sealed class CarryableLane : ILaneContributor
    {
        private readonly Carryable _c;

        public CarryableLane(Carryable c) { _c = c ?? throw new ArgumentNullException(nameof(c)); }

        public double Surface(double x, double refY, double h)
        {
            var st = _c.State;
            var p = _c.Params;
            if (!p.Solid || (st != CarryableState.Rest && st != CarryableState.OnDeck)) return h;
            if (Math.Abs(x - _c.X) > p.Radius) return h;
            if (p.SolidAtBaseOnly && Math.Abs(h - _c.BaseY) >= 0.05) return h;
            return Math.Max(h, _c.BaseY + p.Height);
        }

        public double Ceiling(double x, double refY, double h) => h;
        public void Limits(double x, double y, ref double left, ref double right) { }
    }

    /// <summary>
    /// A <see cref="Pushable"/>'s body: solid to its floor + Height within Half − SolidInset (the DL-03 trolley's deck, L1725;
    /// the DL-08 goods trolley to its ballast, L1731). The motor's push hold does not test the lane, so holding it is unaffected.
    /// </summary>
    public sealed class PushableLane : ILaneContributor
    {
        private readonly Pushable _p;

        public PushableLane(Pushable p) { _p = p ?? throw new ArgumentNullException(nameof(p)); }

        public double Surface(double x, double refY, double h)
        {
            var pp = _p.Params;
            if (pp.Height <= 0 || Math.Abs(x - _p.X) > pp.Half - pp.SolidInset) return h;
            return Math.Max(h, pp.FloorY + pp.Height);
        }

        public double Ceiling(double x, double refY, double h) => h;
        public void Limits(double x, double y, ref double left, ref double right) { }
    }

    /// <summary>
    /// DL-08's returns belt in the lane: its crates are solid while in the lane (<c>surfaceAt</c>, L1733), and while it
    /// runs it carries whoever stands on it back toward −x (<c>beltCarry4</c>, L3439; the motor applies it, L1998–L2006).
    /// </summary>
    public sealed class ReturnsBeltLane : ILaneContributor, ILaneConveyor
    {
        private readonly ReturnsBelt _b;

        public ReturnsBeltLane(ReturnsBelt belt) { _b = belt ?? throw new ArgumentNullException(nameof(belt)); }

        public double Surface(double x, double refY, double h) => _b.SurfaceAt(x, h);
        public double Ceiling(double x, double refY, double h) => h;
        public void Limits(double x, double y, ref double left, ref double right) { }
        public double CarryAt(double x, double y) => _b.CarryVelocity(x);
    }

    /// <summary>
    /// Swept volumes in the lane (DL-18's fold bed and bench, <see cref="ISweptVolume"/>): each box's cross-section, clipped
    /// to the depth band D-17 fills (<see cref="D0"/>..<see cref="D1"/>, the leaf's own BodyD0/BodyD1), within its lane
    /// x-extent. While <see cref="Standable"/> is engaged (a leaf down on its stop) its top is ground; otherwise (folding,
    /// propped, waiting) its underside is a ceiling above his feet, never ground: he slides off a propped leaf and cannot
    /// pass through a moving one. No prototype: DL-18 §3–§4, §11.
    /// </summary>
    public sealed class SweptVolumeLane : ILaneContributor
    {
        private readonly ISweptVolume _v;
        private readonly IEngageable _standable;
        public readonly double D0, D1;

        public SweptVolumeLane(ISweptVolume volume, IEngageable standable, double d0 = 0.10, double d1 = 0.44)
        {
            _v = volume ?? throw new ArgumentNullException(nameof(volume));
            _standable = standable;
            if (!(d0 < d1)) throw new ArgumentException("d0 must be below d1.");
            D0 = d0; D1 = d1;
        }

        public double Surface(double x, double refY, double h)
        {
            if (_standable == null || !_standable.Engaged) return h;
            for (int i = 0, n = _v.VolumeCount; i < n; i++)
            {
                var b = _v.Volume(i);
                if (x < b.X0 || x > b.X1 || !Band(b, out _, out double top)) continue;
                if (top > h) h = top;
            }
            return h;
        }

        public double Ceiling(double x, double refY, double h)
        {
            if (_standable != null && _standable.Engaged) return h;
            for (int i = 0, n = _v.VolumeCount; i < n; i++)
            {
                var b = _v.Volume(i);
                if (x < b.X0 || x > b.X1 || !Band(b, out double bottom, out _)) continue;
                if (bottom >= refY && bottom < h) h = bottom;
            }
            return h;
        }

        public void Limits(double x, double y, ref double left, ref double right) { }

        /// <summary>The lowest and highest Y of the box's (D, Y) rectangle inside D0 ≤ D ≤ D1; false if it misses the band.</summary>
        private bool Band(in SweptBox b, out double lo, out double hi)
        {
            lo = double.PositiveInfinity; hi = double.NegativeInfinity;
            double vx = -b.Uy, vy = b.Ux;                                         // the second axis
            for (int k = 0; k < 4; k++)
            {
                double su = k == 0 || k == 3 ? 1 : -1, sv = k < 2 ? 1 : -1;
                // Corner k and the next one round the rectangle: (+u, +v), (−u, +v), (−u, −v), (+u, −v).
                double ad = b.Cd + su * b.Hu * b.Ux + sv * b.Hv * vx, ay = b.Cy + su * b.Hu * b.Uy + sv * b.Hv * vy;
                int n = (k + 1) & 3;
                double nu = n == 0 || n == 3 ? 1 : -1, nv = n < 2 ? 1 : -1;
                double bd = b.Cd + nu * b.Hu * b.Ux + nv * b.Hv * vx, by = b.Cy + nu * b.Hu * b.Uy + nv * b.Hv * vy;
                if (ad >= D0 && ad <= D1) { if (ay < lo) lo = ay; if (ay > hi) hi = ay; }
                Cross(ad, ay, bd, by, D0, ref lo, ref hi);
                Cross(ad, ay, bd, by, D1, ref lo, ref hi);
            }
            return hi >= lo;
        }

        private static void Cross(double ad, double ay, double bd, double by, double d, ref double lo, ref double hi)
        {
            if ((ad - d) * (bd - d) > 0 || ad == bd) return;
            double y = ay + (by - ay) * (d - ad) / (bd - ad);
            if (y < lo) lo = y;
            if (y > hi) hi = y;
        }
    }
}
