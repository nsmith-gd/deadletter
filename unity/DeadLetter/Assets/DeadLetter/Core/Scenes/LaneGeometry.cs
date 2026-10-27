using System;
using System.Collections.Generic;
using DeadLetter.Core.Motor;

namespace DeadLetter.Core.Scenes
{
    /// <summary>
    /// A standable box on the lane: a column from below up to <see cref="Top"/> over [X0, X1], edges inclusive
    /// (port_architecture §4.6, §6.1; the Blender <c>COL_</c> boxes once U-12 authors them). Floors are boxes too: a pit
    /// is a lower box between two floor boxes, so the lane's ground is the highest box at x.
    /// </summary>
    public readonly struct LaneBox
    {
        public readonly double X0, X1, Top;
        /// <summary>
        /// The "boards in the air" case (§4.6, L5256–L5264): it only counts for someone whose feet are already within
        /// <see cref="LaneGeometry.OnlyFromAboveTolerance"/> of its top, so he walks under it from below.
        /// </summary>
        public readonly bool OnlyFromAbove;
        public LaneBox(double x0, double x1, double top, bool onlyFromAbove = false) { X0 = x0; X1 = x1; Top = top; OnlyFromAbove = onlyFromAbove; }
    }

    /// <summary>A ceiling slab over [X0, X1] whose underside is <see cref="Bottom"/> (counts only above his feet).</summary>
    public readonly struct LaneCeiling
    {
        public readonly double X0, X1, Bottom;
        public LaneCeiling(double x0, double x1, double bottom) { X0 = x0; X1 = x1; Bottom = bottom; }
    }

    /// <summary>A straight ramp whose top runs from (X0, Y0) to (X1, Y1); step-up there is 0.45 (L2004, L6351).</summary>
    public readonly struct LaneRamp
    {
        public readonly double X0, Y0, X1, Y1;
        public LaneRamp(double x0, double y0, double x1, double y1) { X0 = x0; Y0 = y0; X1 = x1; Y1 = y1; }
    }

    /// <summary>
    /// Collision a mechanism owns and changes (§4.6: "dynamic contributors owned by mechanisms"): a cart that is a
    /// block and then a bridge, a shutter whose underside swings, a wall that opens with a latch, crates on a belt, a
    /// folding leaf's swept volume. A contributor that is also an <see cref="ILaneConveyor"/> (a running belt) carries
    /// whoever stands on it. Each call folds this
    /// contributor into the value the static boxes (and earlier contributors) gave. Must be cheap, deterministic and
    /// allocation-free: the motor probes the lane dozens of times per step.
    /// </summary>
    public interface ILaneContributor
    {
        /// <summary>The ground at x given everything before it (<paramref name="h"/>); usually <c>max(h, top)</c>.</summary>
        double Surface(double x, double refY, double h);
        /// <summary>The ceiling at x given everything before it (<paramref name="h"/>); usually <c>min(h, bottom)</c>.</summary>
        double Ceiling(double x, double refY, double h);
        /// <summary>Narrow the walls for the body centre at (x, y).</summary>
        void Limits(double x, double y, ref double left, ref double right);
    }

    /// <summary>
    /// A scene's lane as the motor sees it (<see cref="IMotorWorld"/>; port_architecture §4.6): static boxes, ceilings
    /// and ramps from the scene definition, plus <see cref="ILaneContributor"/>s that read mechanism state. The Core
    /// replacement for the prototype's <c>floorAt/surfaceAt/ceilingAt/leftLimit/rightLimit</c> (L1617–L1769) and the
    /// chapter 1 overrides (L4135–L4201). Runtime uses this too: no Unity physics for the hero (§4.6).
    /// Behaves exactly like <see cref="BoxWorld"/> for the static parts, so motor tests carry over.
    /// </summary>
    public sealed class LaneGeometry : IMotorWorld, ILaneConveyor
    {
        /// <summary>How far below a board's top his feet may be and still stand on an <see cref="LaneBox.OnlyFromAbove"/> box.</summary>
        public const double OnlyFromAboveTolerance = 0.05;

        private readonly List<LaneBox> _solids = new List<LaneBox>();
        private readonly List<LaneCeiling> _ceilings = new List<LaneCeiling>();
        private readonly List<LaneRamp> _ramps = new List<LaneRamp>();
        private readonly List<ILaneContributor> _contributors = new List<ILaneContributor>();

        public LaneGeometry(double leftLimit, double rightLimit)
        {
            if (!(leftLimit < rightLimit)) throw new ArgumentException("leftLimit must be below rightLimit.");
            LeftLimit = leftLimit;
            RightLimit = rightLimit;
        }

        /// <summary>The scene's static walls for the body centre (<c>LEFT_LIMIT</c>, <c>RIGHT_LIMIT</c>, L303).</summary>
        public double LeftLimit { get; }
        public double RightLimit { get; }

        public IReadOnlyList<LaneBox> Solids => _solids;
        public IReadOnlyList<LaneCeiling> Ceilings => _ceilings;
        public IReadOnlyList<LaneRamp> Ramps => _ramps;
        public IReadOnlyList<ILaneContributor> Contributors => _contributors;

        public LaneGeometry Solid(double x0, double x1, double top, bool onlyFromAbove = false) { _solids.Add(new LaneBox(x0, x1, top, onlyFromAbove)); return this; }
        public LaneGeometry Ceiling(double x0, double x1, double bottom) { _ceilings.Add(new LaneCeiling(x0, x1, bottom)); return this; }
        public LaneGeometry Ramp(double x0, double y0, double x1, double y1) { _ramps.Add(new LaneRamp(x0, y0, x1, y1)); return this; }
        public LaneGeometry Add(ILaneContributor contributor) { _contributors.Add(contributor ?? throw new ArgumentNullException(nameof(contributor))); return this; }

        public double SurfaceAt(double x, double refY)
        {
            double h = LaneProbe.NoGround;
            for (int i = 0; i < _solids.Count; i++)
            {
                LaneBox s = _solids[i];
                if (x < s.X0 || x > s.X1 || s.Top <= h) continue;
                if (s.OnlyFromAbove && refY < s.Top - OnlyFromAboveTolerance) continue;
                h = s.Top;
            }
            for (int i = 0; i < _ramps.Count; i++)
            {
                LaneRamp r = _ramps[i];
                if (x >= r.X0 && x <= r.X1 && r.X1 > r.X0)
                {
                    double t = r.Y0 + (r.Y1 - r.Y0) * (x - r.X0) / (r.X1 - r.X0);
                    if (t > h) h = t;
                }
            }
            for (int i = 0; i < _contributors.Count; i++) h = _contributors[i].Surface(x, refY, h);
            return h;
        }

        public double CeilingAt(double x, double refY)
        {
            double h = LaneProbe.NoCeiling;
            for (int i = 0; i < _ceilings.Count; i++)
            {
                LaneCeiling c = _ceilings[i];
                if (x >= c.X0 && x <= c.X1 && c.Bottom >= refY && c.Bottom < h) h = c.Bottom;
            }
            for (int i = 0; i < _contributors.Count; i++) h = _contributors[i].Ceiling(x, refY, h);
            return h;
        }

        public void Limits(double x, double y, out double left, out double right)
        {
            left = LeftLimit;
            right = RightLimit;
            for (int i = 0; i < _contributors.Count; i++) _contributors[i].Limits(x, y, ref left, ref right);
        }

        public bool IsRamp(double x)
        {
            for (int i = 0; i < _ramps.Count; i++)
                if (x >= _ramps[i].X0 && x <= _ramps[i].X1) return true;
            return false;
        }

        public bool LedgeAhead(double x, double y, int dir, double range, double stepUp, out Ledge ledge)
            => LaneProbe.ScanLedge(this, x, y, dir, range, stepUp, out ledge);

        /// <summary>The sum of the contributors that carry (<see cref="ILaneConveyor"/>: a running belt), m/s.</summary>
        public double CarryAt(double x, double y)
        {
            double v = 0;
            for (int i = 0; i < _contributors.Count; i++) if (_contributors[i] is ILaneConveyor c) v += c.CarryAt(x, y);
            return v;
        }
    }
}
