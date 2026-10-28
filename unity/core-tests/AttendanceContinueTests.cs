using System;
using System.Collections.Generic;
using System.Globalization;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Save;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl15;
using DeadLetter.Core.Scenes.Dl16;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// A Continue at every chapter 1 checkpoint past <c>school</c> (where the chapter is begun, and nothing is written) (#48 review): the slot each checkpoint wrote while the prototype's trace
    /// played, restored into a fresh <see cref="ChapterSim"/>, whose clock starts again at 0. The clock timers
    /// (<see cref="Mechanisms.ClockMark"/>: the procession's dismissal, a door's delay, a latch's arming, the seats' hold) run
    /// on from where they were saved: the world continued on a clock from 0 plays out as the same world continued on the
    /// clock it was saved at.
    /// </summary>
    public class AttendanceContinueTests
    {
        private const double Dt = 1.0 / 60.0;

        private sealed class Slot
        {
            public string Checkpoint;
            public byte[] Bytes;
            public double Clock;
        }

        private static readonly object Gate = new object();
        private static List<Slot> _slots;

        /// <summary>The trace played as <see cref="AttendanceChapterTraceTests"/> plays it, with a slot: each checkpoint's save.</summary>
        private static List<Slot> Slots()
        {
            lock (Gate)
            {
                if (_slots != null) return _slots;
                var t = Trace.Load(AttendanceChapterTraceTests.TraceFile);
                var (from, to) = AttendanceChapterTraceTests.Window(t, ChapterTraceProbes.Attendance());
                var store = new MemorySaveStore();
                var sim = new ChapterSim(ChapterDefs.Attendance(), store: store);
                sim.Clock = from > 0 ? t.Steps[from - 1].Clk : 0;
                sim.Begin("school");                                                // as the trace test does: nothing is written there
                var slots = new List<Slot>();
                for (int k = from; k <= to; k++)
                {
                    string before = sim.Checkpoints.Current.Name;
                    sim.Step(t.Steps[k].Input);
                    if (sim.Checkpoints.Current.Name != before)
                        slots.Add(new Slot { Checkpoint = sim.Checkpoints.Current.Name, Bytes = (byte[])store.Slots[0].Clone(), Clock = sim.Clock });
                }
                return _slots = slots;
            }
        }

        private static ChapterSim ContinueFrom(Slot s)
        {
            var store = new MemorySaveStore();
            store.Slots[0] = (byte[])s.Bytes.Clone();
            var sim = new ChapterSim(ChapterDefs.Attendance(), store: store);
            Assert.True(sim.Continue(), s.Checkpoint);
            Assert.Equal(s.Checkpoint, sim.Checkpoints.Current.Name);
            Assert.True(sim.Checkpoints.RestoredSnapshot, s.Checkpoint);
            return sim;
        }

        [Fact]
        public void EveryChapter1CheckpointPastSchool_WritesASlot()
        {
            var names = new List<string>();
            foreach (var s in Slots()) names.Add(s.Checkpoint);
            Assert.Equal(new[] { "register", "lesson", "gallery13", "window", "hatch14", "dorm", "corridor", "sickbay",
                                 "class6", "dismissed", "crossing", "store", "kitchen", "workshop" }, names);
        }

        public static IEnumerable<object[]> Checkpoints()
        {
            foreach (var s in Slots()) yield return new object[] { s.Checkpoint };
        }

        /// <summary>
        /// Continued on a clock from 0 and on the clock the slot was saved at, standing still for 40 s: every mechanism field
        /// agrees every 5 s, and to 1e-6 at the end, once everything has settled. On the way a timer's threshold can fall a
        /// step apart (a clock difference rounds differently at 0 and at 240 s, which is why the timers run on the clock), so
        /// the 5 s checks allow 0.05 (three steps of a figure at 0.95 m/s). A timer kept as a clock time stalls on the first
        /// (its time since reads negative) and not on the second: metres apart.
        /// </summary>
        [Theory]
        [MemberData(nameof(Checkpoints))]
        public void Continue_TheClockTimersRunOn_WhateverTheNewSessionsClock(string checkpoint)
        {
            var slot = Slots().Find(s => s.Checkpoint == checkpoint);
            var fresh = ContinueFrom(slot);
            var saved = ContinueFrom(slot);
            saved.Clock = slot.Clock;
            Same(checkpoint + " restored", SaveKit.Dump(saved.Graph), SaveKit.Dump(fresh.Graph), 1e-6);
            for (int s = 1; s <= 8; s++)
            {
                for (int i = 0; i < 300; i++) { fresh.Step(default); saved.Step(default); }
                Same(checkpoint + " after " + 5 * s + " s", SaveKit.Dump(saved.Graph), SaveKit.Dump(fresh.Graph), s < 8 ? 0.05 : 1e-6);
            }
        }

        /// <summary>
        /// The review's case: continued at <c>dismissed</c> (and at <c>crossing</c>), the procession bows and rolls on, the
        /// time since the dismissal counting on from the slot's, where it used to stall about 4 minutes at the bow (the
        /// dismissal's clock time against a clock from 0).
        /// </summary>
        [Theory]
        [InlineData("dismissed")]
        [InlineData("crossing")]
        public void Continue_TheProcessionRollsOn(string checkpoint)
        {
            var sim = ContinueFrom(Slots().Find(s => s.Checkpoint == checkpoint));
            var p = sim.Graph.Get<Dl16Procession>("dl16.procession");
            double since = p.Since;
            Assert.True(since >= 0 && since < 30, checkpoint + " since " + since);
            var a = sim.Graph.Get<Dl15Figure>("dl15.figA");
            double x = a.X;
            for (int i = 0; i < 1800; i++) sim.Step(default);
            Assert.Equal(since + 30, p.Since, 6);
            Assert.True(a.State != Dl15Figure.FigureState.Procession || a.X > x + 1, checkpoint + ": figA at " + a.X + " from " + x);
        }

        private static void Same(string what, string expected, string actual, double tolerance)
        {
            if (expected == actual) return;
            var e = Fields(expected);
            var a = Fields(actual);
            Assert.Equal(e.Count, a.Count);
            foreach (var kv in e)
            {
                Assert.True(a.TryGetValue(kv.Key, out string v), what + ": " + kv.Key + " missing");
                if (v == kv.Value) continue;
                bool num = double.TryParse(kv.Value, NumberStyles.Float, CultureInfo.InvariantCulture, out double x)
                           & double.TryParse(v, NumberStyles.Float, CultureInfo.InvariantCulture, out double y);
                Assert.True(num && Math.Abs(x - y) <= tolerance, what + ": " + kv.Key + " " + kv.Value + " vs " + v);
            }
        }

        private static Dictionary<string, string> Fields(string dump)
        {
            var d = new Dictionary<string, string>();
            foreach (var line in dump.Split('\n'))
            {
                int eq = line.IndexOf('=');
                if (eq > 0) d[line.Substring(0, eq)] = line.Substring(eq + 1);
            }
            return d;
        }
    }
}
