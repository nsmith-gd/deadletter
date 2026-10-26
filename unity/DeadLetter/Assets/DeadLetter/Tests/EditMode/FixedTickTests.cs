using DeadLetter.Core.Simulation;
using NUnit.Framework;

namespace DeadLetter.Tests.EditMode
{
    public class FixedTickTests
    {
        [Test]
        public void SixtyFramesAtSixtyHertz_ProducesSixtySteps()
        {
            var tick = new FixedTick(1.0 / 60.0);
            int total = 0;
            for (int i = 0; i < 60; i++)
                total += tick.Advance(1.0 / 60.0);

            Assert.AreEqual(60, total);
            Assert.AreEqual(60, tick.TickCount);
        }

        [Test]
        public void LargeDelta_IsCappedAndRemainderKept()
        {
            var tick = new FixedTick(0.1, maxStepsPerAdvance: 3);

            Assert.AreEqual(3, tick.Advance(1.05));
            Assert.AreEqual(7, tick.DroppedSteps);
            Assert.AreEqual(0.5, tick.Alpha, 1e-9);
        }
    }
}
