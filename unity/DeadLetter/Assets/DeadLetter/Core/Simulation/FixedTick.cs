using System;

namespace DeadLetter.Core.Simulation
{
    /// <summary>
    /// Deterministic fixed-timestep accumulator.
    /// Variable frame deltas go in; a whole number of fixed simulation steps comes out.
    /// Time is accumulated in integer 100ns ticks (TimeSpan ticks) so that the same
    /// sequence of deltas always produces the same sequence of step counts, with no
    /// floating-point drift over long sessions.
    /// Engine-free: no UnityEngine references (DeadLetter.Core has noEngineReferences).
    /// </summary>
    public sealed class FixedTick
    {
        private readonly long _stepTicks;
        private readonly int _maxStepsPerAdvance;
        private long _accumulatedTicks;

        /// <param name="stepSeconds">Length of one simulation step, e.g. 1/60.</param>
        /// <param name="maxStepsPerAdvance">
        /// Cap on steps returned by a single <see cref="Advance"/> call (spiral-of-death guard).
        /// Excess whole steps beyond the cap are dropped; the sub-step remainder is kept.
        /// </param>
        public FixedTick(double stepSeconds, int maxStepsPerAdvance = 8)
        {
            if (!(stepSeconds > 0.0) || double.IsInfinity(stepSeconds))
                throw new ArgumentOutOfRangeException(nameof(stepSeconds), "Step must be a positive, finite number of seconds.");
            if (maxStepsPerAdvance < 1)
                throw new ArgumentOutOfRangeException(nameof(maxStepsPerAdvance), "Must allow at least one step per advance.");

            _stepTicks = SecondsToTicks(stepSeconds);
            if (_stepTicks < 1)
                throw new ArgumentOutOfRangeException(nameof(stepSeconds), "Step is shorter than 100ns.");
            _maxStepsPerAdvance = maxStepsPerAdvance;
        }

        /// <summary>Fixed step length in seconds (after quantisation to 100ns ticks).</summary>
        public double StepSeconds => _stepTicks / (double)TimeSpan.TicksPerSecond;

        /// <summary>Total fixed steps produced since construction or <see cref="Reset"/>.</summary>
        public long TickCount { get; private set; }

        /// <summary>Steps dropped by the per-advance cap since construction or <see cref="Reset"/>.</summary>
        public long DroppedSteps { get; private set; }

        /// <summary>Interpolation factor in [0, 1): how far the leftover time is into the next step.</summary>
        public double Alpha => _accumulatedTicks / (double)_stepTicks;

        /// <summary>Adds a frame delta and returns how many fixed steps to simulate now.</summary>
        public int Advance(double deltaSeconds)
        {
            if (deltaSeconds < 0.0 || double.IsNaN(deltaSeconds) || double.IsInfinity(deltaSeconds))
                throw new ArgumentOutOfRangeException(nameof(deltaSeconds), "Delta must be a non-negative, finite number of seconds.");

            _accumulatedTicks += SecondsToTicks(deltaSeconds);

            long steps = _accumulatedTicks / _stepTicks;
            _accumulatedTicks -= steps * _stepTicks;

            if (steps > _maxStepsPerAdvance)
            {
                DroppedSteps += steps - _maxStepsPerAdvance;
                steps = _maxStepsPerAdvance;
            }

            TickCount += steps;
            return (int)steps;
        }

        /// <summary>Clears accumulated time and counters.</summary>
        public void Reset()
        {
            _accumulatedTicks = 0;
            TickCount = 0;
            DroppedSteps = 0;
        }

        private static long SecondsToTicks(double seconds)
        {
            return (long)Math.Round(seconds * TimeSpan.TicksPerSecond, MidpointRounding.AwayFromZero);
        }
    }
}
