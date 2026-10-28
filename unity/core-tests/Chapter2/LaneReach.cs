using System;
using System.Collections.Generic;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Chapter 2's no-trap and station checks: where D-17 can get to on the lane as it is now, on foot: walking (a step up of
    /// at most STEP_UP, any drop) and standing mantles (MantleMin to MantleMax, within the standing scan), as
    /// <see cref="D17Motor"/> moves him. No jumps: none is needed (chapter2_plan §4: "none relies on a jump-catch"); the
    /// skip searches simulate jumps instead. Nodes every centimetre, at his support.
    /// </summary>
    internal sealed class LaneReach
    {
        private const double Step = 0.01;
        private readonly double _x0;
        private readonly ChapterSim _s;
        private readonly MotorConfig _c;
        private readonly Func<double, double, bool> _standable;
        private readonly int _n;
        private readonly double[] _y;
        private readonly List<int>[] _next;

        /// <param name="x0">The west end of the stretch searched; <paramref name="x1"/> its east end.</param>
        /// <param name="standable">Whether he stays standing at (x, y) (a plate that hops him off does not); null: everywhere.</param>
        public LaneReach(ChapterSim s, double x0, double x1, Func<double, double, bool> standable = null)
        {
            _s = s;
            _c = s.Config;
            _x0 = x0;
            _standable = standable;
            _n = (int)Math.Round((x1 - x0) / Step) + 1;
            _y = new double[_n];
            _next = new List<int>[_n];
            var lane = (IMotorWorld)s.Lane;
            for (int i = 0; i < _n; i++) _y[i] = s.Lane.SupportAt(X(i));
            for (int i = 0; i < _n; i++)
            {
                var to = _next[i] = new List<int>();
                if (!Stays(i)) continue;
                foreach (int dir in new[] { -1, 1 })
                {
                    int j = i + dir;
                    if (j >= 0 && j < _n && CanWalk(i, j, dir) && Stays(j)) to.Add(j);
                    if (lane.LedgeAhead(X(i), _y[i], dir, _c.MantleScanStanding, _c.StepUp, out var l)
                        && l.Top - _y[i] > _c.MantleMin && l.Top - _y[i] <= _c.MantleMax && l.Distance < _c.FaceDistance + _c.MantleReachExtra)
                    {
                        double end = X(i) + dir * (MotorConfig.MantleKeys[MotorConfig.MantleKeys.GetLength(0) - 1, 1] + Math.Max(0, l.Distance - _c.FaceDistance));
                        int k = Index(end);
                        if (k >= 0 && k < _n && Stays(k)) to.Add(k);
                    }
                }
            }
        }

        public double X(int i) => _x0 + i * Step;
        public double Y(int i) => _y[i];
        private int Index(double x) => (int)Math.Round((x - _x0) / Step);
        private bool Stays(int i) => _standable == null || _standable(X(i), _y[i]);

        private bool CanWalk(int i, int j, int dir)
        {
            double x = X(j);
            _s.Lane.Limits(X(i), _y[i], out double left, out double right);
            if (x < left - 1e-9 || x > right + 1e-9) return false;
            double lead = x + dir * _c.Half;
            return _s.Lane.SurfaceAt(lead) <= _y[i] + (_s.Lane.IsRamp(lead) ? _c.StepUpRamp : _c.StepUp) + 1e-9;
        }

        /// <summary>He can stand at x: on his support, his body clear of any face higher than a step, and he stays there.</summary>
        public bool CanStand(double x)
        {
            double y = _s.Lane.SupportAt(x);
            return _s.Lane.SurfaceAt(x - _c.Half + 1e-6) <= y + _c.StepUp && _s.Lane.SurfaceAt(x + _c.Half - 1e-6) <= y + _c.StepUp
                && (_standable == null || _standable(x, y));
        }

        /// <summary>Every node reachable from x.</summary>
        public bool[] From(double x)
        {
            var seen = new bool[_n];
            var q = new Queue<int>();
            int s = Index(x);
            seen[s] = true;
            q.Enqueue(s);
            while (q.Count > 0)
            {
                int i = q.Dequeue();
                foreach (int j in _next[i]) if (!seen[j]) { seen[j] = true; q.Enqueue(j); }
            }
            return seen;
        }

        public bool Any(bool[] r, Func<int, bool> f)
        {
            for (int i = 0; i < _n; i++) if (r[i] && f(i)) return true;
            return false;
        }

        public bool Answers(int i, IInteractable target) => Facing(i, target) != 0;

        /// <summary>The facing at node i from which Use resolves to <paramref name="target"/> (+1 tried first; 0: none).</summary>
        public int Facing(int i, IInteractable target)
        {
            foreach (int f in new[] { 1, -1 })
                if (Answers(i, target, f)) return f;
            return 0;
        }

        /// <summary>Use at node i, facing <paramref name="facing"/>, resolves to <paramref name="target"/>.</summary>
        public bool Answers(int i, IInteractable target, int facing)
            => _s.Resolver.Resolve(InteractionQuery.At(X(i), _y[i], facing), out var c) && ReferenceEquals(c.Target, target);

        /// <summary>A node he can stand at where Use resolves to <paramref name="target"/>.</summary>
        public int Station(IInteractable target)
        {
            for (int i = 0; i < _n; i++) if (CanStand(X(i)) && Answers(i, target)) return i;
            throw new Xunit.Sdk.XunitException("no station for " + target);
        }

        public bool HasStation(IInteractable target)
        {
            for (int i = 0; i < _n; i++) if (CanStand(X(i)) && Answers(i, target)) return true;
            return false;
        }
    }
}
