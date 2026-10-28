using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Save;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// <see cref="ClockMark"/> (#48 review): a clock timer saved mid-run carries on from where it was in a session whose
    /// clock starts again at 0, as a door's delay, a latch's arming and a seat row's hold do across a Continue.
    /// </summary>
    public class ClockMarkTests
    {
        private const double Dt = Mech.Dt;

        private static StepContext At(double clock) => new StepContext(Dt, 0, PlayerPose.Away, false, null, clock);

        [Fact]
        public void Since_CountsOnTheClock_AndASnapshotCarriesTheElapsedTimeToAnotherClock()
        {
            var m = ClockMark.None;
            Assert.True(double.IsNaN(m.Since(At(240))));                                   // no mark
            m.Mark(At(240));
            double clock = 240;
            for (int i = 0; i < 30; i++) clock += Dt;
            double before = m.Since(At(clock));
            Assert.Equal(30 * Dt, before, 9);

            var snap = new MemorySnapshot();
            m.Write(snap, "e");
            Assert.Equal(before, snap.ReadDouble("e"));                                     // elapsed, not the clock time
            var r = ClockMark.None;
            r.Read(snap, "e");
            Assert.Equal(before + Dt, r.Since(At(Dt)), 9);                                  // a new session's first step
            Assert.Equal(before + 2 * Dt, r.Since(At(2 * Dt)), 9);
        }

        [Fact]
        public void NoGameClock_IsNaN_AndSavesNaN()
        {
            var m = ClockMark.None;
            m.Mark(At(double.NaN));
            Assert.True(double.IsNaN(m.Since(At(double.NaN))));
            var snap = new MemorySnapshot();
            m.Write(snap, "e");
            Assert.True(double.IsNaN(snap.ReadDouble("e")));
            m.Clear();
            m.Write(snap, "e");
            Assert.True(double.IsNaN(snap.ReadDouble("e")));
        }

        /// <summary>A door 0.5 s into a 1 s delay at a clock of 240 s, continued on a clock from 0: it opens 0.5 s later, not at 240 s.</summary>
        [Fact]
        public void Door_SavedMidDelay_OpensOnTime_OnANewSessionsClock()
        {
            MechanismGraph Build() => Mech.Graph(new TestSource("t.src"), new Door("t.door", new DoorParams { Trigger = "t.src", Delay = 1.0 }));
            var a = Build();
            a.Get<TestSource>("t.src").Engaged = true;
            a.Clock = 240;
            for (int i = 0; i < 30; i++) { a.Clock += Dt; a.Step(Dt, PlayerPose.Away); }
            Assert.Equal(DoorState.Closed, a.Get<Door>("t.door").State);
            var snap = Mech.Snapshot(a);

            var b = Build();
            b.Get<TestSource>("t.src").Engaged = true;
            b.Restore(snap);
            b.Clock = 0;
            var door = b.Get<Door>("t.door");
            int steps = 0;
            while (door.State == DoorState.Closed && steps < 600) { b.Clock += Dt; b.Step(Dt, PlayerPose.Away); steps++; }
            Assert.InRange(steps, 30, 32);                                                  // the rest of the second, not 4 minutes
        }
    }
}
