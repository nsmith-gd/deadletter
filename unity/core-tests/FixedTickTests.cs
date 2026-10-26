using System;
using DeadLetter.Core.Simulation;
using Xunit;

namespace DeadLetter.Core.Tests
{
    public class FixedTickTests
    {
        [Fact]
        public void SixtyFramesAtSixtyHertz_ProducesSixtySteps()
        {
            var tick = new FixedTick(1.0 / 60.0);
            int total = 0;
            for (int i = 0; i < 60; i++)
                total += tick.Advance(1.0 / 60.0);

            Assert.Equal(60, total);
            Assert.Equal(60, tick.TickCount);
        }

        [Fact]
        public void UnevenFrames_AccumulateWithoutDrift()
        {
            var tick = new FixedTick(0.02);
            // 10,000 frames of 7ms = 70s = exactly 3,500 steps of 20ms.
            for (int i = 0; i < 10000; i++)
                tick.Advance(0.007);

            Assert.Equal(3500, tick.TickCount);
            Assert.Equal(0.0, tick.Alpha, 9);
        }

        [Fact]
        public void LargeDelta_IsCappedAndRemainderKept()
        {
            var tick = new FixedTick(0.1, maxStepsPerAdvance: 3);

            Assert.Equal(3, tick.Advance(1.05));
            Assert.Equal(7, tick.DroppedSteps);
            Assert.Equal(0.5, tick.Alpha, 9);
        }

        [Fact]
        public void SameInputs_ProduceSameStepSequence()
        {
            double[] deltas = { 0.016, 0.033, 0.001, 0.050, 0.017, 0.0, 0.1 };
            var a = new FixedTick(1.0 / 60.0);
            var b = new FixedTick(1.0 / 60.0);

            foreach (var d in deltas)
                Assert.Equal(a.Advance(d), b.Advance(d));
            Assert.Equal(a.TickCount, b.TickCount);
        }

        [Fact]
        public void Reset_ClearsState()
        {
            var tick = new FixedTick(0.1, maxStepsPerAdvance: 1);
            tick.Advance(0.55);
            tick.Reset();

            Assert.Equal(0, tick.TickCount);
            Assert.Equal(0, tick.DroppedSteps);
            Assert.Equal(0.0, tick.Alpha);
        }

        [Theory]
        [InlineData(0.0)]
        [InlineData(-1.0)]
        [InlineData(double.NaN)]
        [InlineData(double.PositiveInfinity)]
        public void InvalidStep_Throws(double step)
        {
            Assert.Throws<ArgumentOutOfRangeException>(() => new FixedTick(step));
        }

        [Fact]
        public void NegativeDelta_Throws()
        {
            var tick = new FixedTick(0.1);
            Assert.Throws<ArgumentOutOfRangeException>(() => tick.Advance(-0.01));
        }
    }
}
