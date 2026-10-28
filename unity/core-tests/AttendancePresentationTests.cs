using System;
using System.Collections.Generic;
using System.Linq;
using DeadLetter.Core.Audio;
using DeadLetter.Core.Presentation;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Streaming;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// Chapter 1's presentation in Core (issue #50, U-23's pattern): the whole of Traces/attendance_mech_seed1.jsonl.gz
    /// through one <see cref="ChapterSim"/> and its <see cref="ChapterPresentation"/>, stepped as GameHost does. The sounds
    /// are checked against the prototype's own moments in the trace (a wind, the lesson starting, a door opening, a seat
    /// lamp, the car setting off, the run, the float latch); the emitters' and tannoys' conditions, the driven lights and
    /// the mix against the recorded state, every step.
    /// </summary>
    public class AttendancePresentationTests
    {
        private sealed class Row
        {
            public TraceStep P;
            public readonly List<string> Sounds = new List<string>();
            public bool LessonRunning, RestDoorShut, Dismissed;
            public double Sun, W1, W2;
            public MixSnapshot Mix;
        }

        private static List<Row> _cached;
        private static readonly object Gate = new object();

        private static List<Row> Run()
        {
            lock (Gate)
            {
                if (_cached != null) return _cached;
                var t = Trace.Load(AttendanceChapterTraceTests.TraceFile);
                int from = t.FirstIndex(p => p.Mode == "play");
                var sim = new ChapterSim(ChapterDefs.Attendance());
                sim.Clock = from > 0 ? t.Steps[from - 1].Clk : 0;
                var view = new ChapterPresentation(sim);
                sim.Begin("school");
                view.OnPlaced();
                int sun = Light(view, LightDriver.AttSun), w1 = Light(view, LightDriver.AttBlindW1), w2 = Light(view, LightDriver.AttBlindW2);
                var rows = new List<Row>();
                for (int k = from; k < t.Steps.Count; k++)
                {
                    sim.Step(t.Steps[k].Input);
                    view.AfterStep(voicePlaying: false, calm: false);
                    view.Frame(sim.Clock, ChapterSim.StepSeconds, sim.X, calm: false);
                    var r = new Row { P = t.Steps[k] };
                    var q = view.Sounds.Sounds;
                    for (int i = 0; i < q.Count; i++) r.Sounds.Add(q[i].Key);
                    r.LessonRunning = view.Ambience.Condition(PrologueEmitters.LessonRunning);
                    r.RestDoorShut = view.Ambience.Condition(VoiceCatalog.RestDoorShut);
                    r.Dismissed = view.Ambience.Condition(VoiceCatalog.Dismissed);
                    r.Sun = view.Lighting.Pool.Level(sun);
                    r.W1 = view.Lighting.Pool.Level(w1);
                    r.W2 = view.Lighting.Pool.Level(w2);
                    r.Mix = view.Mix.Snapshot;
                    rows.Add(r);
                }
                return _cached = rows;
            }
        }

        private static int Light(ChapterPresentation v, LightDriver d)
        {
            for (int i = 0; i < v.Lighting.Pool.Count; i++) if (v.Lighting.Pool[i].Driver == d) return i;
            throw new InvalidOperationException("no " + d + " light");
        }

        /// <summary>Steps where <paramref name="changed"/> holds between a row and the one before.</summary>
        private static List<int> Moments(List<Row> rows, Func<TraceStep, TraceStep, bool> changed)
        {
            var at = new List<int>();
            for (int k = 1; k < rows.Count; k++) if (changed(rows[k - 1].P, rows[k].P)) at.Add(k);
            return at;
        }

        /// <summary>Each moment hears <paramref name="keys"/> within <paramref name="window"/> steps of it (the trace's state lags the event by a step where the prototype applies it after the sound).</summary>
        private static void Hears(List<Row> rows, List<int> moments, string what, int window, params string[] keys)
        {
            Assert.True(moments.Count > 0, what + ": the trace never shows it");
            foreach (int m in moments)
                foreach (string key in keys)
                {
                    bool heard = false;
                    for (int k = Math.Max(0, m - window); k <= Math.Min(rows.Count - 1, m + window) && !heard; k++) heard = rows[k].Sounds.Contains(key);
                    Assert.True(heard, what + " at #" + rows[m].P.I + ": no " + key);
                }
        }

        [Fact]
        public void Winds_Lesson_Doors_Seats_Car_Run_AndLatch_SoundWhenThePrototypesDo()
        {
            var r = Run();
            Hears(r, Moments(r, (a, b) => b.W14 > a.W14), "DL-14 wind", 1, SfxKeys.Chain(2.2), SfxKeys.Simple["ratchet"]);
            Hears(r, Moments(r, (a, b) => b.Wn14a > a.Wn14a), "DL-14a wind", 1, SfxKeys.Chain(2.2), SfxKeys.Simple["ratchet"]);
            Hears(r, Moments(r, (a, b) => b.L13 == true && a.L13 != true), "the lesson starts", 1, SfxKeys.Simple["bell"]);
            Hears(r, Moments(r, (a, b) => b.Op14a == true && a.Op14a != true), "DL-14a's door", 2,
                SfxKeys.Simple["clank"], SfxKeys.Simple["bell"], SfxKeys.Simple["doorOpen"]);
            Hears(r, Moments(r, (a, b) => b.Do17 > 0 && !(a.Do17 > 0)), "DL-17's stair door", 2, SfxKeys.Creak(0.7));
            Hears(r, Moments(r, (a, b) => b.Ld17 == true && a.Ld17 != true), "the float latch", 1, SfxKeys.Simple["clank"], SfxKeys.Creak(0.6));
            Hears(r, Moments(r, (a, b) => b.Ru17 > 0 && !(a.Ru17 > 0)), "the run", 1, SfxKeys.Simple["ratchet"], SfxKeys.Simple["splash"]);
            Hears(r, Moments(r, (a, b) => b.Lm15 != a.Lm15 && b.Lm15 != null && a.Lm15 != null
                                             && b.Lm15.Count(c => c == '1') > a.Lm15.Count(c => c == '1')), "a seat lamp", 1, SfxKeys.Simple["plate"]);
            Hears(r, Moments(r, (a, b) => b.M16a == "rise" && a.M16a != "rise"), "the car rises", 1, SfxKeys.Simple["clunk"], SfxKeys.Chain(3.0));
            Hears(r, Moments(r, (a, b) => b.M16a == "down" && a.M16a != "down"), "the car comes down", 1, SfxKeys.Chain(3.0));
            Hears(r, Moments(r, (a, b) => a.Li15 != b.Li15 && (b.Li15 == 0 || b.Li15 == 1.6)), "the pupil lift arrives", 1, SfxKeys.Simple["clunk"]);
            Hears(r, Moments(r, (a, b) => b.Di15 == true && a.Di15 != true), "the dismissal", 1, SfxKeys.Simple["bell"]);
        }

        [Fact]
        public void TheSounds_AreAllInTheBank_AndTheDoorCueIsNotPlayedAsAKey()
        {
            var keys = new HashSet<string>(Run().SelectMany(w => w.Sounds));
            Assert.DoesNotContain(AttendanceSounds.DoorCueKey, keys);
            Assert.DoesNotContain(null, keys);
            foreach (string k in keys) Assert.True(k.Contains("_"), "not a bank key: " + k);   // every bank key is <family>_<name>
        }

        [Fact]
        public void EmitterAndTannoyConditions_FollowTheRecordedState()
        {
            var bad = new List<string>();
            foreach (var w in Run())
            {
                var p = w.P;
                if (p.L13.HasValue && w.LessonRunning != (p.L13.Value && p.K13 != true)) bad.Add("#" + p.I + " lessonRunning " + w.LessonRunning);
                if (p.Op14a.HasValue && w.RestDoorShut != !(p.Op14a.Value || p.Do14a > 0)) bad.Add("#" + p.I + " restDoorShut " + w.RestDoorShut);
                if (p.Di15.HasValue && w.Dismissed != p.Di15.Value) bad.Add("#" + p.I + " dismissed " + w.Dismissed);
                if (w.Mix != MixSnapshot.School) bad.Add("#" + p.I + " mix " + w.Mix);
            }
            Assert.True(bad.Count == 0, string.Join("\n", bad.Take(20)));
            Assert.Contains(Run(), w => w.LessonRunning);
            Assert.Contains(Run(), w => !w.RestDoorShut);
            Assert.Contains(Run(), w => w.Dismissed);
        }

        [Fact]
        public void DL14a_Sun_AndBlindLights_FollowTheNightLightAndTheBlinds()
        {
            var bad = new List<string>();
            foreach (var w in Run())
            {
                var p = w.P;
                if (p.W1a is double v1 && Math.Abs(w.W1 - 2.4 * (1 - v1)) > 2.4e-6) bad.Add("#" + p.I + " W1 " + w.W1 + " for " + v1);   // L6275
                if (p.W2a is double v2 && Math.Abs(w.W2 - 2.0 * (1 - v2)) > 2.0e-6) bad.Add("#" + p.I + " W2 " + w.W2 + " for " + v2);   // L6276
            }
            Assert.True(bad.Count == 0, string.Join("\n", bad.Take(20)));
            Assert.Contains(Run(), w => w.Sun < 2.6 * 0.2);                                                // the sun goes dark
            Assert.Contains(Run(), w => w.Sun > 2.6 * 0.9);
        }

        [Fact]
        public void Chapter1Lights_AreTheAttendanceRows_AndTheAlwaysOnes()
        {
            LightDef[] defs = ChapterPresentation.LightsFor(ChapterDefs.AttendanceId, touch: false);
            Assert.All(defs, d => Assert.True(d.Group == LightGroup.Always || d.Group == LightGroup.Attendance, d.ToString()));
            Assert.Equal(AttendanceLights.Build().Length, defs.Count(d => d.Group == LightGroup.Attendance));
            Assert.Equal(68, AttendanceLights.Build().Length);                                             // refs.attLights (L5176–L5221)
            Assert.Equal(PrologueLights.Build().Length, ChapterPresentation.LightsFor(ChapterDefs.PrologueId, false).Length);
            Assert.DoesNotContain(AttendanceLights.Build(touch: true), d => d.Shadow);                    // !touchDevice
            Assert.Contains(AttendanceLights.Build(), d => d.Shadow);
        }

        [Fact]
        public void InRegion6_ThePoolLightsTheSchool()
        {
            var sim = new ChapterSim(ChapterDefs.Attendance());
            var view = new ChapterPresentation(sim);
            foreach (string cp in new[] { "school", "lesson", "window", "dorm", "corridor", "sickbay", "crossing", "kitchen", "workshop" })
            {
                sim.Begin(cp);
                view.OnPlaced();
                view.Frame(0, ChapterSim.StepSeconds, sim.X, calm: false);
                int lit = 0;
                for (int i = 0; i < view.Lighting.Pool.Count; i++)
                    if (view.Lighting.Pool[i].Group == LightGroup.Attendance && view.Lighting.Pool.On(i)) lit++;
                Assert.True(lit > 10, cp + ": " + lit + " school lights on");
                Assert.Equal(MixSnapshot.School, view.Mix.Snapshot);
            }
        }
    }
}
