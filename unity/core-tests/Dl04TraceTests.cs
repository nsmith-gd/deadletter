using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using DeadLetter.Core.Cues;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Lane.Tables;
using DeadLetter.Core.Mechanisms.Docks;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl03;
using DeadLetter.Core.Scenes.Dl04;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-04 parity (U-20): the prototype's own run (the mechanical bot, seed 1, Traces/prologue_mech_seed1.jsonl.gz, with
    /// DL-04's fields: the fallen courier's x and state, the cradle's arms, the bay door and what the bay wants) replayed
    /// through Core's <see cref="SceneSim"/> with <see cref="Dl04Scene.Def"/>, input for input, compared at every 60 Hz step.
    /// <para><b>One window</b>, from where he last stood at rest before DL-04 (handed over in the recorded state,
    /// <see cref="SceneSim.Handover"/> and <see cref="D17Motor.SetState"/>): after the gate's slam startled him in DL-03's weighing room (x 29.97, 0.63 short of
    /// the gate), through the gate into DL-04, the reveal, the realisation (the <c>kin</c> moment: 22.5 s held), the slow
    /// walk to 36.6, the run to the fallen courier, the grab (stepping in 0.35 behind the lane), the drag over the bay
    /// plate to the end of its travel, the cradle closing on it and seating it, the door opening, the walk back out to
    /// the lane, the touch, and out through the door past <c>bay</c> to the step he enters DL-05. DL-03 hands on its
    /// pending reveal (<see cref="Dl03Rules.RevealPending"/> at the end of its own replay).</para>
    /// <para><b>Tolerance 1e-6</b> on every continuous value (the trace rounds to 1e-6; the hand-over pose too).
    /// Discrete signals (acts, holds, grounded, the courier's state, what the bay wants, checkpoints, the exit) fall on the
    /// same step.</para>
    /// <para>M8 is fixed (#28): after he lets go of the courier he steps back out to the lane (0.45 m/s) after the player's
    /// update (<c>updateCh1</c>, #7, L4876), so on the very step he lets go, as the prototype does.</para>
    /// <para><b>Known difference</b>, asserted exactly where it shows: the bay door's deliberate deviation (<see cref="PlateDoor"/>): fully open with the bay wanting it,
    /// the prototype's <c>if (want &gt; door) … else close</c> (L4814) saws it 1 → 0.967 → 0.982 → 0.997 → 1; Core holds
    /// it at 1. The door's law, driven by Core's own want, reproduces the prototype's every step; Core is above it by the
    /// saw's phase while the door holds or closes after it, never by more than dt / 0.5, and never on the wrong side of
    /// 0.55 (where it walls him, L4174).</para>
    /// </summary>
    public class Dl04TraceTests
    {
        internal const string TraceFile = Dl01TraceTests.TraceFile;
        private const double Tol = 1e-6, Dt = 1.0 / 60.0;

        internal sealed class Row
        {
            public TraceStep P;
            public double X, Y, Z, Vx, Yaw, CourierX, Arm, Door;
            public bool G, Exited, Want, PlateOn;
            public string Kind, Phase, Cp, Hold, CourierState, Clip, Cues;
            public bool Slow, Idle;
            public int Region;
        }

        internal sealed class Replay
        {
            public readonly List<Row> Rows = new List<Row>();
            public SceneSim Sim;
            public int From, To;
            public string Checkpoint;
            public bool RevealPending;
        }

        private static Replay _cache;
        private static readonly object Lock = new object();

        /// <summary>The window: from his last rest before DL-04 (after the startle) to the step he enters DL-05.</summary>
        internal static (int from, int to) Window(Trace t)
        {
            int first = t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-04"));
            int rest = -1;
            for (int i = first - 1; i > 0 && rest < 0; i--)
            {
                var p = t.Steps[i];
                if (p.Vx == 0 && p.G && p.Act == null && p.Hold == null && !p.Mt) rest = i;
            }
            return (rest + 1, t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-05")));
        }

        internal static Replay Run()
        {
            lock (Lock)
            {
                if (_cache != null) return _cache;
                var t = Trace.Load(TraceFile);
                var (from, to) = Window(t);
                // What DL-03 hands on: its own replay, ended where DL-04 begins.
                bool pending = ((Dl03Rules)Dl03TraceTests.Room().Sim.Rules).RevealPending;
                var r = new Replay { From = from, To = to, Checkpoint = t.Steps[from - 1].Cp, RevealPending = pending };
                Pushable courier = null;
                Cradle cradle = null;
                LoadPlate plate = null;
                PlateDoor door = null;
                r.Sim = TraceReplay.Run(t, Dl04Scene.Def(pending), r.Checkpoint, false, from, to, (p, sim) =>
                {
                    if (courier == null)
                    {
                        courier = sim.Graph.Get<Pushable>("dl04.courier"); cradle = sim.Graph.Get<Cradle>("dl04.cradle");
                        plate = sim.Graph.Get<LoadPlate>("dl04.bayPlate"); door = sim.Graph.Get<PlateDoor>("dl04.bayDoor");
                    }
                    r.Rows.Add(new Row
                    {
                        P = p, X = sim.X, Y = sim.Y, Z = sim.Z, Vx = sim.Vx, Yaw = sim.Yaw, G = sim.Grounded,
                        Kind = sim.ActKind, Phase = sim.ActPhase, Cp = sim.Checkpoints.Current.Name, Region = sim.Region, Exited = sim.Exited,
                        Hold = HoldName(sim.Motor, courier),
                        CourierX = cradle.Position, CourierState = CourierName(cradle.State), Arm = cradle.ArmRad,
                        Door = door.Open01, Want = door.Want, PlateOn = plate.Engaged,
                        Clip = sim.Act is BayTouchAct ? null : sim.Motor.Clip, Cues = string.Join(",", sim.Cues), Slow = sim.Motor.SlowWalkLimit > 0,
                        Idle = sim.Act is RealiseAct ra && ra.Idle,
                    });
                }, handover: true);
                return _cache = r;
            }
        }

        private static string HoldName(D17Motor m, Pushable courier)
        {
            if (m.Hold == HoldKind.None) return null;
            if (m.Hold != HoldKind.Push) return m.Hold.ToString();
            return ReferenceEquals(m.Pushed, courier) ? "push:courier" : m.Pushed is PushTwin tw && ReferenceEquals(tw.Base, courier) ? "push:courierAlt" : "push:?";
        }

        private static string CourierName(CradleState s)
            => s == CradleState.Free ? "free" : s == CradleState.Drawing ? "drawn" : s == CradleState.Closing ? "cradle" : "seated";

        // ---- The trace ------------------------------------------------------------------------------------------------
        [Fact]
        public void Trace_HasDl04_AndTheWindowIsWhereExpected()
        {
            var t = Trace.Load(TraceFile);
            var (from, to) = Window(t);
            Assert.Equal(6248, from);                                                          // after the startle
            Assert.Equal("quirk:Startle", t.Steps[from - 2].Act);
            Assert.Equal(29.968522, t.Steps[from - 1].X, 6);
            Assert.Equal("solved", t.Steps[from - 1].Cp);
            Assert.Equal(9868, to);
            Assert.StartsWith("DL-04", t.Steps[to - 1].Scene);
            int first = t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-04"));
            Assert.Equal(6279, first);
            // DL-04's fields are written only while in DL-04 (null before); there, at their reset values.
            Assert.Null(t.Steps[first - 1].Kx4);
            Assert.Equal(41.2, t.Steps[first].Kx4.Value, 6);                                   // RK.courierX
            Assert.Equal("free", t.Steps[first].Ks4);
            Assert.Equal(0, t.Steps[first].Bd4.Value);
            Assert.Equal(0, t.Steps[first].Bw4.Value);
            Assert.True(Run().RevealPending);                                                   // DL-03 solved; the racks still dark
        }

        // ---- (a) position ---------------------------------------------------------------------------------------------
        /// <summary>x, y, vx, yaw and grounded at every step of the window: nothing compensated.</summary>
        [Fact]
        public void X_Y_Vx_Yaw_And_Grounded_MatchEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Run().Rows)
            {
                Check(bad, w.P.I, "x", w.P.X, w.X);
                Check(bad, w.P.I, "y", w.P.Y, w.Y);
                Check(bad, w.P.I, "vx", w.P.Vx, w.Vx);
                Check(bad, w.P.I, "yaw", w.P.Yaw, w.Yaw);
                if (w.G != w.P.G) bad.Add($"#{w.P.I} grounded {w.P.G} vs {w.G}");
                if (w.Region != w.P.Region) bad.Add($"#{w.P.I} region {w.P.Region} vs {w.Region}");
            }
            Assert.True(bad.Count == 0, Report(bad));
        }

        /// <summary>
        /// z (he steps in 0.35 behind the lane to take the tow loop, and back out after) matches at every step: from the step
        /// he lets go (#9534) he steps back out on the prototype's steps (M8, fixed in #28), back on the lane at #9580.
        /// </summary>
        [Fact]
        public void Z_MatchesEveryStep_TheStepBackOnTheReleasesStep_M8()
        {
            var rows = Run().Rows;
            var bad = new List<string>();
            foreach (var w in rows) Check(bad, w.P.I, "z", -w.P.Z, w.Z);                             // Unity z = −three z (§0.2)
            Assert.True(bad.Count == 0, Report(bad));
            var release = rows.Find(w => w.P.I == 9534);
            Assert.Null(release.P.Hold);
            Assert.Null(release.Hold);
            Assert.Equal("push:courier", rows.Find(w => w.P.I == 9533).Hold);
            Assert.Equal(0.35, rows.Find(w => w.P.I == 9533).Z, 12);                           // where he held it ...
            Assert.Equal(0.35 - 0.45 * Dt, release.Z, 12);                                     // ... a step out on the release's step
            Assert.True(rows.Find(w => w.P.I == 9579).Z > 0);
            Assert.Equal(0, rows.Find(w => w.P.I == 9580).Z);
            Assert.Equal(0.35, rows.Find(w => w.P.I == 8598).Z, 12);                           // stepped in for the grab, on its step
        }

        // ---- (b) acts and holds -----------------------------------------------------------------------------------------
        /// <summary>Every act and phase on the prototype's steps (the realisation, the grab, the touch), and what his hands hold.</summary>
        [Fact]
        public void Acts_And_Holds_MatchEveryStep()
        {
            var bad = new List<string>();
            var seen = new HashSet<string>();
            foreach (var w in Run().Rows)
            {
                string want = ExpectedAct(w.P), got = CoreAct(w);
                if (want != null) seen.Add(want);
                if (want != got) bad.Add($"#{w.P.I} act {want ?? "-"} vs {got ?? "-"}");
                if (w.P.Hold != w.Hold) bad.Add($"#{w.P.I} hold {w.P.Hold ?? "-"} vs {w.Hold ?? "-"}");
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(new HashSet<string> { "realise:act", "dl04.courier:Approach", "dl04.courier:Clip", "bayTouch:approach", "bayTouch:act" }, seen);
        }

        /// <summary>
        /// The racks are revealed the step he is GATE_X + 0.2 through (#6286, L2401); he realises on the first step a second
        /// after it (#6347, L1956), idles once the cue is past 9.5 s (#6918, L2313) and is freed at <c>control</c>, 22.5 s
        /// on the cue's clock (#7698, L2314: the bot touches nothing meanwhile). Then he walks slowly (SadWalk) to 36.6.
        /// </summary>
        [Fact]
        public void TheRealisation_RevealThenKin_OnThePrototypesSteps()
        {
            var r = Run();
            var t = Trace.Load(TraceFile);
            var rules = (Dl04Rules)r.Sim.Rules;
            Assert.Equal(t.Steps[6286].Clk, rules.RevealTime);
            Assert.Equal("music:racks", r.Rows.Find(w => w.P.I == 6286).Cues);
            Assert.Equal("moment:kin", r.Rows.Find(w => w.P.I == 6347).Cues);
            Assert.True(t.Steps[6346].Clk - rules.RevealTime <= 1.0 && t.Steps[6347].Clk - rules.RevealTime > 1.0);
            var cues = new List<string>();
            foreach (var w in r.Rows) if (w.Cues.Length > 0) cues.Add(w.P.I + ":" + w.Cues);
            Assert.Equal(new[] { "6286:music:racks", "6347:moment:kin" }, cues);
            var acts = FirstSteps(r.Rows, w => w.Kind);
            Assert.Equal(6347, acts["realise"]);
            Assert.Equal(6918, r.Rows.Find(w => w.Idle).P.I);
            Assert.Equal("Idle", r.Rows.Find(w => w.P.I == 6918).P.Clip);
            Assert.Equal("Realise", r.Rows.Find(w => w.P.I == 6917).P.Clip);
            Assert.Equal(7697, r.Rows.FindLast(w => w.Kind == "realise").P.I);
            Assert.Null(r.Rows.Find(w => w.P.I == 7698).P.Act);
            Assert.True(t.Steps[7698].Clk - t.Steps[6347].Clk >= PrologueMoments.Kin.Control);
            Assert.True(t.Steps[7697].Clk - t.Steps[6347].Clk < PrologueMoments.Kin.Control);
            Assert.True(rules.Realised && rules.KinSlow);
            // The slow walk: SadWalk while realised and short of KIN_UNTIL_X (paceSlow, L2079), on the prototype's steps.
            var bad = new List<string>();
            int slow = 0;
            foreach (var w in r.Rows)
            {
                if (w.Kind != null) continue;
                bool proto = w.P.Clip == "SadWalk";
                if (proto) slow++;
                if (proto != (w.Clip == "SadWalk")) bad.Add($"#{w.P.I} clip {w.P.Clip} vs {w.Clip}");
                if (proto && !w.Slow) bad.Add($"#{w.P.I} not slow");
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(8345 - 7699 + 1, slow);
            Assert.True(r.Rows.Find(w => w.P.I == 8345).X < Dl04Scene.KinUntilX + 0.01);
        }

        // ---- (c) checkpoints and the way on -----------------------------------------------------------------------------
        /// <summary>bay through the door (x &gt; 46.9, L4947) on the prototype's step; nothing else.</summary>
        [Fact]
        public void Checkpoints_FireOnThePrototypesSteps()
        {
            var rows = Run().Rows;
            var bad = new List<string>();
            foreach (var w in rows) if (w.P.Cp != w.Cp) bad.Add($"#{w.P.I} checkpoint {w.P.Cp} vs {w.Cp}");
            Assert.True(bad.Count == 0, Report(bad));
            var first = FirstSteps(rows, w => w.Cp);
            Assert.Equal(new[] { "solved", "bay" }, first.Keys);
            Assert.Equal(9830, first["bay"]);
        }

        [Fact]
        public void LeavesDl04_OnThePrototypesStep()
        {
            var rows = Run().Rows;
            var last = rows[rows.Count - 1];
            Assert.StartsWith("DL-05", last.P.Scene);
            Assert.True(last.Exited);
            Assert.False(rows[rows.Count - 2].Exited);
            Assert.StartsWith("DL-04", rows[rows.Count - 2].P.Scene);
            Assert.Null(last.Kind);
            Assert.Equal(2, last.Region);
            Assert.True(last.X >= Dl04Scene.X1 && rows[rows.Count - 2].X < Dl04Scene.X1);
        }

        // ---- (d) mechanisms ---------------------------------------------------------------------------------------------
        /// <summary>
        /// The courier's x and state (free, then the cradle's once dragged to the end of its travel at #9534, seated at
        /// #9599), the cradle's arms, and what the bay wants (him on the plate #9217–#9488, then the seated courier), at
        /// every step DL-04 records them.
        /// </summary>
        [Fact]
        public void Courier_Cradle_AndTheBaysWant_MatchEveryStep()
        {
            var bad = new List<string>();
            var states = new List<string>();
            string lastState = null;
            int recorded = 0;
            foreach (var w in Run().Rows)
            {
                var p = w.P;
                if (p.Ks4 == null) { Assert.Equal("free", w.CourierState); Assert.False(w.Want); continue; }
                recorded++;
                Check(bad, p.I, "courier.x", p.Kx4.Value, w.CourierX);                      // L4785, L4796
                Check(bad, p.I, "arms", p.Ka4.Value, w.Arm);                                 // L4794, L4802, L4811
                if (p.Ks4 != w.CourierState) bad.Add($"#{p.I} courier {p.Ks4} vs {w.CourierState}");
                if ((p.Bw4.Value == 1) != w.Want) bad.Add($"#{p.I} want {p.Bw4} vs {w.Want}");
                if (w.CourierState != "seated" && w.PlateOn != w.Want) bad.Add($"#{p.I} plate {w.PlateOn} vs want {w.Want}");
                if (w.CourierState != lastState) { states.Add(w.CourierState + "@" + p.I); lastState = w.CourierState; }
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(9868 - 6279 + 1, recorded);
            Assert.Equal(new[] { "free@6279", "cradle@9534", "seated@9599" }, states);
            var rows = Run().Rows;
            Assert.Equal(44.4955, rows.Find(w => w.P.I == 9534).CourierX, 9);               // let go within 0.005 of 44.5: the cradle takes it there
            Assert.Equal(new[] { 9217, 9489 }, new[] { rows.Find(w => w.Want).P.I, rows.Find(w => w.P.I > 9217 && !w.Want).P.I });
        }

        /// <summary>
        /// The bay door. The prototype's law (L4813–L4814: open at 1/1.1 or 1/2.2 a second toward want, else close at 1/0.5),
        /// driven by Core's own want and seated courier, reproduces the recorded door at every step. Core's door follows the
        /// same law except its deliberate hold at the top (<see cref="PlateDoor"/>): where the prototype's door, fully open
        /// and still wanted, saws 1 → 0.967 → 0.982 → 0.997 → 1 (from #9284 under him, and again once the courier holds it),
        /// Core's stays at 1, and when it then closes it is above the prototype's by the saw's phase. It is never below the
        /// law, never more than dt / 0.5 above it, and on the same side of 0.55 (where it walls him, L4174) at every step
        /// but one: closing after he stepped off, it goes under 0.55 a step later (#9501), with him 1 m short of the wall.
        /// </summary>
        [Fact]
        public void BayDoor_FollowsThePrototypesLaw_ButHoldsAtTheTop()
        {
            var bad = new List<string>();
            double law = 0;
            int above = -1, aboveCount = 0, opened = -1;
            var walls = new List<int>();
            foreach (var w in Run().Rows)
            {
                bool held = w.CourierState == "seated";
                law = (w.Want ? 1 : 0) > law ? Math.Min(1, law + Dt / (held ? 2.2 : 1.1)) : Math.Max(0, law - Dt / 0.5);   // L4814
                if (w.P.Bd4.HasValue) Check(bad, w.P.I, "door (law)", w.P.Bd4.Value, law);
                double d = w.Door - law;
                if (d > 1e-12)
                {
                    aboveCount++;
                    if (above < 0) above = w.P.I;
                    if (d > Dt / 0.5 + 1e-12) bad.Add($"#{w.P.I} door {w.Door:R} above the law {law:R} by more than a step");
                }
                else if (d < -1e-12) bad.Add($"#{w.P.I} door {w.Door:R} below the law {law:R}");
                if ((w.Door < 0.55) != (law < 0.55))
                {
                    walls.Add(w.P.I);
                    // Shut a step later; it matters only if he could reach the wall, 0.04 + HALF short of the door (L4174).
                    if (w.X + 1.6 * Dt >= Dl04Lane.DoorX0 - Dl04Lane.DoorGap) bad.Add($"#{w.P.I} door walls him {w.Door < 0.55} vs {law < 0.55} at x {w.X}");
                }
                if (opened < 0 && w.Door >= 1) opened = w.P.I;
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(9284, above);
            Assert.True(aboveCount > 0);
            Assert.Equal(9283, opened);                                                        // 1.1 s after he stepped on (#9217)
            Assert.Equal(new[] { 9501 }, walls);                                               // shut a step later, 1 m short of it
            var last = Run().Rows[Run().Rows.Count - 1];
            Assert.Equal(1, last.Door);                                                        // the courier holds it open
        }

        // ---- Dump ---------------------------------------------------------------------------------------------------
        /// <summary>Writes the window side by side as TSV when DL04_TRACE_DUMP names a file.</summary>
        [Fact]
        public void Dump()
        {
            var path = Environment.GetEnvironmentVariable("DL04_TRACE_DUMP");
            if (string.IsNullOrEmpty(path)) return;
            var sb = new StringBuilder("i\tpx\tcx\tpy\tcy\tpz\tcz\tpvx\tcvx\tpyaw\tcyaw\tpg\tcg\tpact\tcact\tph\tch\tpcp\tccp\tpkx\tckx\tpks\tcks\tpka\tcka\tpbd\tcbd\tpbw\tcbw\tpclip\tcclip\tcues\tin\n");
            foreach (var w in Run().Rows)
            {
                var p = w.P;
                sb.Append(p.I).Append('\t').Append(p.X).Append('\t').Append(w.X.ToString("R")).Append('\t').Append(p.Y).Append('\t').Append(w.Y.ToString("R"))
                  .Append('\t').Append(-p.Z).Append('\t').Append(w.Z.ToString("R")).Append('\t').Append(p.Vx).Append('\t').Append(w.Vx.ToString("R"))
                  .Append('\t').Append(p.Yaw).Append('\t').Append(w.Yaw.ToString("R"))
                  .Append('\t').Append(p.G ? 1 : 0).Append('\t').Append(w.G ? 1 : 0).Append('\t').Append(ExpectedAct(p)).Append('\t').Append(CoreAct(w))
                  .Append('\t').Append(p.Hold).Append('\t').Append(w.Hold).Append('\t').Append(p.Cp).Append('\t').Append(w.Cp)
                  .Append('\t').Append(p.Kx4).Append('\t').Append(w.CourierX.ToString("R")).Append('\t').Append(p.Ks4).Append('\t').Append(w.CourierState)
                  .Append('\t').Append(p.Ka4).Append('\t').Append(w.Arm.ToString("R")).Append('\t').Append(p.Bd4).Append('\t').Append(w.Door.ToString("R"))
                  .Append('\t').Append(p.Bw4).Append('\t').Append(w.Want ? 1 : 0).Append('\t').Append(p.Clip).Append('\t').Append(w.Clip).Append('\t').Append(w.Cues)
                  .Append('\t').Append(p.L ? "L" : "").Append(p.R ? "R" : "").Append(p.JP ? "J" : "").Append(p.UP ? "U" : "").Append(p.SH ? "S" : "").Append('\n');
            }
            File.WriteAllText(path, sb.ToString());
        }

        // ---- Helpers --------------------------------------------------------------------------------------------------
        /// <summary>The prototype's act as Core names it (<see cref="SceneSim.ActKind"/>:<see cref="SceneSim.ActPhase"/>).</summary>
        internal static string ExpectedAct(TraceStep p)
        {
            if (p.Mt) return "mantle:";
            if (p.Act == null) return null;
            var parts = p.Act.Split(':');
            string kind = parts[0], phase = parts[1];
            switch (kind)
            {
                // The courier's own face is its right (he stands right of it); its twin (courierAlt) the left, a verb.
                case "grabPush": return (p.Kx4.HasValue && p.X > p.Kx4.Value ? "dl04.courier:" : "Grab:") + (phase == "approach" ? "Approach" : "Clip");
                default: return kind + ":" + phase;
            }
        }

        internal static string CoreAct(Row r) => r.Kind == null ? null : r.Kind + ":" + (r.Kind == "mantle" ? "" : r.Phase);

        private static void Check(List<string> bad, int i, string what, double proto, double core)
        {
            if (Math.Abs(core - proto) > Tol) bad.Add($"#{i} {what} {proto:R} vs {core:R}");
        }

        private static Dictionary<string, int> FirstSteps(List<Row> rows, Func<Row, string> name)
        {
            var d = new Dictionary<string, int>();
            foreach (var w in rows) { var n = name(w); if (n != null && !d.ContainsKey(n)) d[n] = w.P.I; }
            return d;
        }

        private static string Report(List<string> bad)
        {
            var sb = new StringBuilder().Append(bad.Count).Append(" mismatches");
            for (int i = 0; i < bad.Count && i < 12; i++) sb.Append("\n  ").Append(bad[i]);
            return sb.ToString();
        }
    }
}
