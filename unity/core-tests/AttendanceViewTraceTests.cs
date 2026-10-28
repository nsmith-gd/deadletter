using System;
using System.Collections.Generic;
using DeadLetter.Core.Maths;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Streaming;
using Xunit;
using static DeadLetter.Core.Tests.ChapterTraceKit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Chapter 1's mechanism view readers (issue #50), against the prototype's own view code: the whole of
    /// Traces/attendance_mech_seed1.jsonl.gz through one <see cref="ChapterSim"/>, and every step the value each reader gives
    /// is compared with the prototype's view formula applied to the recorded state (the blinds' <c>scale.y</c>, the doors'
    /// <c>rotateY</c>, the drawer's <c>z</c>, the steps' <c>rotateX</c>, the tree's scale, the lift, the bridge, the
    /// rack's counterweight, the car, the tank and beds). The state itself is the probes' (AttendanceChapterTraceTests);
    /// this checks that each reader reads the right state and transcribes its formula.
    /// </summary>
    public class AttendanceViewTraceTests
    {
        private sealed class View
        {
            public readonly string Name;
            public readonly Func<double> Read;
            public readonly Func<TraceStep, double?> Want;
            /// <summary>The formula's steepest slope in its recorded field: the field is rounded to 1e-6, so the tolerance is 1e-6 × this.</summary>
            public readonly double Gain;
            public View(string name, Func<double> read, Func<TraceStep, double?> want, double gain = 1) { Name = name; Read = read; Want = want; Gain = gain; }
        }

        private static Func<double> R(ChapterSim sim, string id, ViewChannel c, int index = 0)
        {
            Assert.True(sim.Graph.TryGet(id, out IMechanism m), id);
            Func<double> r = MechanismReadout.Reader(m, c, index, () => false);
            Assert.True(r != null, id + " " + c + "[" + index + "]");
            return r;
        }

        private static double S(double x) => Smooth.Step(x);

        [Fact]
        public void Chapter1Readers_GiveThePrototypesViewValues_EveryStep()
        {
            var t = Trace.Load(AttendanceChapterTraceTests.TraceFile);
            int from = t.FirstIndex(p => p.Mode == "play");
            var sim = new ChapterSim(ChapterDefs.Attendance());
            sim.Clock = from > 0 ? t.Steps[from - 1].Clk : 0;
            sim.Begin("school");

            var views = new List<View>
            {
                new View("blind A scale", R(sim, "dl14.blinds", ViewChannel.Scale, 0), p => p.Ba14 is double v ? Math.Max(0.04, v) : (double?)null),     // L5443
                new View("blind B scale", R(sim, "dl14.blinds", ViewChannel.Scale, 1), p => p.Bb14 is double v ? Math.Max(0.04, v) : (double?)null),
                new View("W1 scale", R(sim, "dl14a.blinds", ViewChannel.Scale, 0), p => p.W1a is double v ? Math.Max(0.04, v) : (double?)null),          // L6278
                new View("W2 scale", R(sim, "dl14a.blinds", ViewChannel.Scale, 1), p => p.W2a is double v ? Math.Max(0.04, v) : (double?)null),
                new View("W1 hem y", R(sim, "dl14a.blinds", ViewChannel.Y, 0), p => p.W1a is double v ? 3.21 - (3.21 - 1.93) * v : (double?)null, 1.28),      // hem14a, L5934
                new View("W1 hook y", R(sim, "dl14a.blinds", ViewChannel.Y, 1), p => p.W1a is double v ? 2.0 - (2.0 - 0.75) * v : (double?)null, 1.25),       // hook14a, L5933
                new View("14a door", R(sim, "dl14a.door", ViewChannel.Angle), p => p.Do14a is double v ? 90 * S(v) : (double?)null, 135),                    // L6283
                new View("15 door", R(sim, "dl15.classDoor", ViewChannel.Angle), p => p.Do15 is double v ? 90 * S(v) : (double?)null, 135),                  // L5832 (×95/90 in the binding)
                new View("17 door", R(sim, "dl17.stairDoor", ViewChannel.Angle), p => p.Do17 is double v ? 90 * S(v) : (double?)null, 135),                  // L5841
                new View("17 drawer z", R(sim, "dl17.drawer", ViewChannel.Z), p => p.Dr17 is double v ? -0.45 * S(v) : (double?)null, 0.675),                  // L5840
                new View("15 lift", R(sim, "dl15.lift", ViewChannel.Position), p => p.Li15),                                                             // L5823
                new View("15 lift gate", R(sim, "dl15.lift", ViewChannel.Angle), p => p.Li15 is double v ? -90 * S(1 - v / 0.25) : (double?)null, 540),      // L5824
                new View("16 bridge", R(sim, "dl16.bridge", ViewChannel.Angle), p => p.Br16 is double v ? -90 * S(v) : (double?)null, 135),                  // L5836
                new View("16 lever", R(sim, "dl16.lever", ViewChannel.Angle), p => p.He16 is bool h ? (h || p.La16 == true ? -35 : 0) : (double?)null),  // L5837
                new View("16 latch", R(sim, "dl16.latch", ViewChannel.Angle, 1), p => p.La16 is bool l ? (l ? 90 : 0) : (double?)null),                  // L5838
                new View("16 counterweight", R(sim, "dl16.rackCW", ViewChannel.Position), p => p.Cw16 is double v ? 2.0 * S(v) : (double?)null, 3),        // L5839
                new View("16a car", R(sim, "dl16a.car", ViewChannel.Position), p => p.H16a),                                                             // L6289
                new View("17 tank", R(sim, "dl17.rig", ViewChannel.Scale, 0), p => p.Tk17 is double v ? Math.Max(0.02, v) : (double?)null),             // L6307
                new View("13 lesson lamp", R(sim, "dl13.lesson", ViewChannel.Lamp, 0), p => p.L13 is bool on ? (on ? 3 : 0.05) : (double?)null),        // L5415
                new View("14b figure z", R(sim, "dl14b.figure", ViewChannel.Z), p => p.Fo14b is double v ? -(-0.85 + 0.30 * S(v)) : (double?)null, 0.45),     // L6432
                new View("14b figure x", R(sim, "dl14b.figure", ViewChannel.X), p => p.Fx14b),
                new View("13 brake", R(sim, "dl13.brake", ViewChannel.Angle), p => p.K13 is bool b ? (b ? 40 : 0) : (double?)null),                     // L5431
                new View("14a brake", R(sim, "dl14a.brake", ViewChannel.Angle), p => p.Nk14a is bool b ? (b ? 40 : 0) : (double?)null),                 // L6271
                new View("14a dial", R(sim, "dl14a.nightLight", ViewChannel.Angle, 0), p => p.Nt14a is double v ? -360 * v / 10 : (double?)null, 36),       // L6272
                new View("13 dial", R(sim, "dl13.lesson", ViewChannel.Angle, 0), p => p.T13 is double v ? -360 * v / 12 : (double?)null, 30),               // L5430
            };
            for (int s = 0; s < 3; s++)
            {
                int i = s;
                views.Add(new View("13 step " + (i + 1), R(sim, "dl13.lesson", ViewChannel.Angle, i + 1),
                    p => p.S13 != null ? -90 * (1 - TraceStep.Numbers(p.S13)[i]) : (double?)null, 90));                                                   // L5429
                views.Add(new View("17 bed " + (i + 1), R(sim, "dl17.rig", ViewChannel.Scale, i + 1),
                    p => p.Be17 != null ? Math.Max(0.01, TraceStep.Numbers(p.Be17)[i]) : (double?)null));                                              // L6309
            }
            for (int k = 0; k < 5; k++)
            {
                int i = k;
                views.Add(new View("13 tree " + i, R(sim, "dl13.lesson", ViewChannel.Scale, i),
                    p => p.Tr13 is double v ? Math.Max(0.001, S(Math.Min(1, Math.Max(0, v * 5 - i)))) : (double?)null, 7.5));                              // L5433
            }

            var bad = new List<string>();
            var checkedAt = new int[views.Count];
            for (int k = from; k < t.Steps.Count; k++)
            {
                TraceStep p = t.Steps[k];
                sim.Step(p.Input);
                for (int v = 0; v < views.Count; v++)
                {
                    double? want = views[v].Want(p);
                    if (!want.HasValue) continue;
                    checkedAt[v]++;
                    double got = views[v].Read();
                    if (!(Math.Abs(got - want.Value) <= Tol * views[v].Gain + 1e-9)) bad.Add($"#{p.I} {views[v].Name} {want.Value:R} vs {got:R}");
                }
            }
            Assert.True(bad.Count == 0, Report(bad));
            for (int v = 0; v < views.Count; v++) Assert.True(checkedAt[v] > 1000, views[v].Name + " checked " + checkedAt[v] + " times");
        }
    }
}
