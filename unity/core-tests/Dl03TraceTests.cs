using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Plates;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Push;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl03;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-03 parity (U-20): the prototype's own run (the mechanical bot, seed 1, Traces/prologue_mech_seed1.jsonl.gz, with
    /// DL-03's fields: the trolley, the weight, the plate's load and needle, the gate) replayed through Core's
    /// <see cref="SceneSim"/> with <see cref="Dl03Scene.Def"/>, input for input, compared at every 60 Hz step.
    /// <para><b>Two windows</b>, each starting where he stands at rest (handed over in the recorded state,
    /// <see cref="SceneSim.Handover"/> and <see cref="D17Motor.SetState"/>):
    /// <list type="bullet">
    /// <item><b>Entry</b>: from his last rest on DL-02's gantry (after the mantle up to it) along the gantry and the sill,
    /// off it into the weighing room (DL-03 from x 25.0), to the step he lands and reaches <c>weighroom</c>.</item>
    /// <item><b>Room</b>: from the step he asks to lift the weight (he has come to rest, and the act zeroes his speed in
    /// both) to the step he walks past the gate into DL-04: the lift, the carry, the set-down onto the deck, the grab,
    /// the push onto the plate, the gate winding up, <c>solved</c>, the climb over the loaded trolley (on the plate: the
    /// gate opens fully), the jumps down, the slam and his startle, and out.</item>
    /// </list></para>
    /// <para><b>Tolerance 1e-6</b> on every continuous value (the trace rounds to 1e-6; the hand-over pose too, ≤ 5e-7).
    /// Discrete signals (acts, holds, grounded, the weight's state, checkpoints, the exit) fall on the same step.</para>
    /// <para>M2 and M3 (#22) are fixed in U-11b (#25): the climb over the trolley takes the prototype's 141 steps and every
    /// walk-off fall, the entry's 1.35 m drop off the sill included, follows the prototype's arc and lands on its step.
    /// M5 is fixed (#28): Use lets go of the trolley before the prototype's <c>game.vx = 0</c> (<c>beginUse('release')</c>,
    /// L1820–L1821), so he keeps his push speed and drifts on as it decays (#5977: 0.42 m/s, 7.3 mm over four steps). Nothing
    /// is compensated.</para>
    /// </summary>
    public class Dl03TraceTests
    {
        internal const string TraceFile = Dl01TraceTests.TraceFile;
        private const double Tol = 1e-6;
        private const double G = 9.8, Dt = 1.0 / 60.0;

        internal sealed class Row
        {
            public TraceStep P;
            public double X, Y, Z, Vx, Yaw, TrolleyX, WeightX, WeightOff, Load, Needle, GateY, GateV;
            public bool G, Exited;
            public string Kind, Phase, Cp, Hold, WeightState;
            public int Region;
        }

        internal sealed class Replay
        {
            public readonly List<Row> Rows = new List<Row>();
            public SceneSim Sim;
            public int From, To;
            public string Checkpoint;
            /// <summary>Steps where Use let go of the trolley.</summary>
            public readonly List<int> UseReleases = new List<int>();
        }

        private static readonly Dictionary<string, Replay> Cache = new Dictionary<string, Replay>();

        /// <summary>The entry window: from his last rest before DL-03 to the step that reaches <c>weighroom</c>.</summary>
        internal static (int from, int to) EntryWindow(Trace t)
        {
            int first = t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-03"));
            int rest = -1;
            for (int i = first - 1; i > 0 && rest < 0; i--)
            {
                var p = t.Steps[i];
                if (p.Vx == 0 && p.G && p.Act == null && p.Hold == null && !p.Mt) rest = i;
            }
            return (rest + 1, t.FirstIndex(p => p.Cp == "weighroom"));
        }

        /// <summary>The room window: from the lift's Use to the step into DL-04.</summary>
        internal static (int from, int to) RoomWindow(Trace t)
            => (t.FirstIndex(p => p.Act != null && p.Act.StartsWith("lift:")), t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-04")));

        internal static Replay Entry() => Run("entry");
        internal static Replay Room() => Run("room");

        private static Replay Run(string window)
        {
            string key = window;
            lock (Cache)
            {
                if (Cache.TryGetValue(key, out var cached)) return cached;
                var t = Trace.Load(TraceFile);
                var (from, to) = window == "entry" ? EntryWindow(t) : RoomWindow(t);
                var r = new Replay { From = from, To = to, Checkpoint = t.Steps[from - 1].Cp };
                Pushable trolley = null;
                Dl03Weight weight = null;
                LoadPlate plate = null;
                FollowerActuator gate = null;
                bool pushUse = false;
                MotorInput Input(int k, SceneSim sim)
                {
                    var given = t.Steps[k].Input;
                    pushUse = given.UsePressed && sim.Motor.Hold == HoldKind.Push && sim.Act == null && !sim.Motor.IsActing;
                    return given;
                }
                r.Sim = TraceReplay.Run(t, Dl03Scene.Def(), r.Checkpoint, false, from, to, (p, sim) =>
                {
                    if (trolley == null)
                    {
                        trolley = sim.Graph.Get<Pushable>("dl03.trolley"); weight = sim.Graph.Get<Dl03Weight>("dl03.weight");
                        plate = sim.Graph.Get<LoadPlate>("dl03.plate"); gate = sim.Graph.Get<FollowerActuator>("dl03.gate");
                    }
                    if (pushUse && sim.Motor.Hold == HoldKind.None) r.UseReleases.Add(p.I);
                    r.Rows.Add(new Row
                    {
                        P = p, X = sim.X, Y = sim.Y, Z = sim.Z, Vx = sim.Vx, Yaw = sim.Yaw, G = sim.Grounded,
                        Kind = sim.ActKind, Phase = sim.ActPhase, Cp = sim.Checkpoints.Current.Name, Region = sim.Region, Exited = sim.Exited,
                        Hold = sim.Motor.Hold == HoldKind.Item ? "weight" : sim.Motor.Hold == HoldKind.Push ? "trolley" : null,
                        TrolleyX = trolley.X, WeightState = WeightName(weight.State), WeightX = weight.FloorX, WeightOff = weight.Offset,
                        Load = plate.Load, Needle = plate.Needle, GateY = gate.Position, GateV = gate.Velocity,
                    });
                }, Input, handover: true);
                return Cache[key] = r;
            }
        }

        private static string WeightName(Dl03WeightState s) => s == Dl03WeightState.Floor ? "floor" : s == Dl03WeightState.Carried ? "carried" : "trolley";

        // ---- The trace ------------------------------------------------------------------------------------------------
        [Fact]
        public void Trace_HasDl03_AndTheWindowsAreWhereExpected()
        {
            var t = Trace.Load(TraceFile);
            var (ef, et) = EntryWindow(t);
            var (rf, rt) = RoomWindow(t);
            Assert.Equal(5132, ef);                                                              // after the mantle onto the gantry
            Assert.Equal(1.35, t.Steps[ef - 1].Y, 6);
            Assert.Equal(5274, et);
            Assert.Equal(5279, rf);
            Assert.Equal("lift:approach", t.Steps[rf].Act);
            Assert.Equal(6279, rt);
            Assert.StartsWith("DL-03", t.Steps[rt - 1].Scene);
            Assert.Equal(5228, t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-03")));
            Assert.Equal(27.55, t.Steps[0].Tx, 6);                                                // TROLLEY_X
            Assert.Equal("floor", t.Steps[0].Ws);
            Assert.Equal(25.62, t.Steps[0].Wx, 6);                                                // WEIGHT_X
        }

        // ---- (a) position ---------------------------------------------------------------------------------------------
        [Fact]
        public void X_Z_Vx_And_Yaw_MatchEveryStep_BothWindows()
        {
            var bad = new List<string>();
            foreach (var r in new[] { Entry(), Room() })
                foreach (var w in r.Rows)
                {
                    Check(bad, w.P.I, "x", w.P.X, w.X);
                    Check(bad, w.P.I, "z", -w.P.Z, w.Z);                                             // Unity z = −three z (§0.2)
                    Check(bad, w.P.I, "vx", w.P.Vx, w.Vx);
                    Check(bad, w.P.I, "yaw", w.P.Yaw, w.Yaw);
                }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(new[] { 5977 }, Room().UseReleases);                                       // M5: Use lets go of the trolley ...
            var release = Room().Rows.Find(w => w.P.I == 5977);
            Assert.True(release.Vx > 0.4 && Math.Abs(release.Vx - release.P.Vx) <= Tol);           // ... and he keeps his speed (0.42)
            Assert.Empty(Entry().UseReleases);
        }

        /// <summary>
        /// y matches at every step, the three walk-off falls included (M3, fixed in #25): off the sill into the room
        /// (1.35 m, from #5243), off the weight onto the deck (#6194) and off the deck to the floor (#6210).
        /// </summary>
        [Fact]
        public void Y_MatchesEveryStep_WalkOffFallsIncluded()
        {
            var bad = new List<string>();
            var falls = new List<(int at, int steps)>();
            foreach (var r in new[] { Entry(), Room() })
            {
                int walkOff = -1;
                for (int k = 0; k < r.Rows.Count; k++)
                {
                    var p = r.Rows[k].P;
                    if (p.G) walkOff = -1;
                    else if (walkOff < 0 && k > 0 && r.Rows[k - 1].P.G && p.Vy == 0) { walkOff = p.I; falls.Add((p.I, 0)); }
                    if (Math.Abs(r.Rows[k].Y - p.Y) > Tol) bad.Add($"#{p.I} y {p.Y} vs {r.Rows[k].Y:R}");
                    if (walkOff >= 0 && p.I > walkOff) falls[falls.Count - 1] = (walkOff, p.I - walkOff);
                }
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(new[] { (5243, 30), (6194, 12), (6210, 10) }, falls);
        }

        /// <summary>
        /// The entry's 1.35 m drop lands on the prototype's step (M3, fixed in #25): its semi-implicit Euler has fallen
        /// g·dt²·31·32/2 = 1.3502 m after 31 steps, and so has Core's parity arc, so he lands at #5274, and the
        /// <c>weighroom</c> checkpoint (y &lt; 0.05, L4946) fires on that step.
        /// </summary>
        [Fact]
        public void Entry_LandsAndReachesWeighroom_OnThePrototypesStep()
        {
            var r = Entry();
            var last = r.Rows[r.Rows.Count - 1];
            Assert.Equal(5274, last.P.I);
            Assert.True(last.P.G);
            Assert.Equal(0, last.P.Y);
            Assert.True(last.G);
            Assert.Equal(0, last.Y, 9);
            Assert.True(G * Dt * Dt * 31 * 32 / 2 > 1.35 && G * Dt * Dt * 30 * 31 / 2 < 1.35);
            Assert.Equal("weighroom", last.Cp);
            Assert.Equal("room", r.Rows[r.Rows.Count - 2].Cp);
            for (int k = 0; k < r.Rows.Count; k++) Assert.True(r.Rows[k].G == r.Rows[k].P.G, "#" + r.Rows[k].P.I);
        }

        // ---- (b) acts, holds and grounded -----------------------------------------------------------------------------
        [Fact]
        public void Grounded_MatchesEveryStep_InTheRoom()
        {
            var bad = new List<string>();
            foreach (var w in Room().Rows) if (w.G != w.P.G) bad.Add($"#{w.P.I} grounded {w.P.G} vs {w.G}");
            Assert.True(bad.Count == 0, Report(bad));
        }

        /// <summary>
        /// Every act and phase on the prototype's steps: the lift (approach, clip), the set-down onto the deck (SetDownHigh),
        /// the grab (approach, clip), the climb over the loaded trolley (141 steps, M2 fixed in #25), the startle; and what
        /// his hands hold.
        /// </summary>
        [Fact]
        public void Acts_And_Holds_MatchEveryStep()
        {
            var bad = new List<string>();
            var seen = new HashSet<string>();
            foreach (var r in new[] { Entry(), Room() })
                foreach (var w in r.Rows)
                {
                    string want = ExpectedAct(w.P), got = CoreAct(w);
                    if (want != null) seen.Add(want);
                    if (want != got) bad.Add($"#{w.P.I} act {want ?? "-"} vs {got ?? "-"}");
                    if (w.P.Hold != w.Hold) bad.Add($"#{w.P.I} hold {w.P.Hold ?? "-"} vs {w.Hold ?? "-"}");
                }
            Assert.True(bad.Count == 0, Report(bad));
            foreach (var a in new[] { "dl03.weight:Approach", "dl03.weight:Clip", "dl03.weight:SetDownHigh", "dl03.trolley:Approach",
                         "dl03.trolley:Clip", "mantle:", "quirk:Startle" })
                Assert.Contains(a, seen);
        }

        // ---- (c) checkpoints and the way on -----------------------------------------------------------------------------
        /// <summary>weighroom (L4946) and solved (the plate holds without him and the gate is up, L2394–L2397) on the prototype's steps.</summary>
        [Fact]
        public void Checkpoints_FireOnThePrototypesSteps()
        {
            foreach (var r in new[] { Entry(), Room() })
                Assert.Equal(FirstSteps(r.Rows, w => w.P.Cp), FirstSteps(r.Rows, w => w.Cp));
            Assert.Equal(new[] { "room", "weighroom" }, FirstSteps(Entry().Rows, w => w.Cp).Keys);
            var room = FirstSteps(Room().Rows, w => w.Cp);
            Assert.Equal(new[] { "weighroom", "solved" }, room.Keys);
            Assert.Equal(6017, room["solved"]);
        }

        [Fact]
        public void LeavesDl03_OnThePrototypesStep()
        {
            var rows = Room().Rows;
            var last = rows[rows.Count - 1];
            Assert.StartsWith("DL-04", last.P.Scene);
            Assert.True(last.Exited);
            Assert.False(rows[rows.Count - 2].Exited);
            Assert.StartsWith("DL-03", rows[rows.Count - 2].P.Scene);
            Assert.Null(last.Kind);
            Assert.Equal(2, last.Region);
        }

        // ---- (d) mechanisms ---------------------------------------------------------------------------------------------
        /// <summary>The trolley's x, the weight (state, floor x, deck offset), the plate's load and needle, the gate's height and fall speed.</summary>
        [Fact]
        public void Mechanisms_MatchEveryStep()
        {
            var bad = new List<string>();
            var states = new HashSet<string>();
            foreach (var r in new[] { Entry(), Room() })
                foreach (var w in r.Rows)
                {
                    var p = w.P;
                    Check(bad, p.I, "trolley.x", p.Tx, w.TrolleyX);                  // L2347
                    Check(bad, p.I, "weight.x", p.Wx, w.WeightX);                    // L2284
                    Check(bad, p.I, "weight.off", p.Wo, w.WeightOff);                // L2284
                    Check(bad, p.I, "load", p.Ld, w.Load);                           // L2229–L2238, L2371
                    Check(bad, p.I, "needle", p.Nd, w.Needle);                       // L2374
                    Check(bad, p.I, "gate.y", p.Gy, w.GateY);                        // L2378–L2392
                    Check(bad, p.I, "gate.v", p.Gv, w.GateV);
                    if (p.Ws != w.WeightState) bad.Add($"#{p.I} weight {p.Ws} vs {w.WeightState}");
                    states.Add(w.WeightState);
                }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(new HashSet<string> { "floor", "carried", "trolley" }, states);
            var room = Room().Rows;
            Assert.Equal(1.72, room.Find(w => w.P.I == 6184).Load, 9);                  // on the weight on the trolley: standing at 0.38 counts (L2232)
            Assert.Equal(1.2, room.Find(w => w.P.I == 6193).GateY, 9);
            Assert.Equal(0.72 * 1.2, room[room.Count - 1].GateY, 9);
        }

        // ---- Strict -----------------------------------------------------------------------------------------------------
        /// <summary>The room window, strict: every signal at 1e-6 on every step (M5 fixed in #28: nothing is compensated).</summary>
        [Fact]
        public void Strict_EverySignalMatchesEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Room().Rows)
            {
                var p = w.P;
                Check(bad, p.I, "x", p.X, w.X);
                Check(bad, p.I, "y", p.Y, w.Y);
                Check(bad, p.I, "vx", p.Vx, w.Vx);
                Check(bad, p.I, "gate.y", p.Gy, w.GateY);
                if (ExpectedAct(p) != CoreAct(w)) bad.Add($"#{p.I} act {ExpectedAct(p)} vs {CoreAct(w)}");
                if (p.Cp != w.Cp) bad.Add($"#{p.I} checkpoint {p.Cp} vs {w.Cp}");
            }
            Assert.True(bad.Count == 0, Report(bad));
        }

        // ---- Dump ---------------------------------------------------------------------------------------------------
        /// <summary>Writes a window side by side as TSV when DL03_TRACE_DUMP names a file (DL03_TRACE_WINDOW=entry|room).</summary>
        [Fact]
        public void Dump()
        {
            var path = Environment.GetEnvironmentVariable("DL03_TRACE_DUMP");
            if (string.IsNullOrEmpty(path)) return;
            var r = Environment.GetEnvironmentVariable("DL03_TRACE_WINDOW") == "entry" ? Entry() : Room();
            var sb = new StringBuilder("i\tpx\tcx\tpy\tcy\tpvx\tcvx\tpg\tcg\tpact\tcact\tph\tch\tpcp\tccp\tptx\tctx\tpws\tcws\tpld\tcld\tpgy\tcgy\tpyaw\tcyaw\tin\n");
            foreach (var w in r.Rows)
            {
                var p = w.P;
                sb.Append(p.I).Append('\t').Append(p.X).Append('\t').Append(w.X.ToString("R")).Append('\t').Append(p.Y).Append('\t').Append(w.Y.ToString("R"))
                  .Append('\t').Append(p.Vx).Append('\t').Append(w.Vx.ToString("R"))
                  .Append('\t').Append(p.G ? 1 : 0).Append('\t').Append(w.G ? 1 : 0).Append('\t').Append(ExpectedAct(p)).Append('\t').Append(CoreAct(w))
                  .Append('\t').Append(p.Hold).Append('\t').Append(w.Hold).Append('\t').Append(p.Cp).Append('\t').Append(w.Cp)
                  .Append('\t').Append(p.Tx).Append('\t').Append(w.TrolleyX.ToString("R")).Append('\t').Append(p.Ws).Append('\t').Append(w.WeightState)
                  .Append('\t').Append(p.Ld).Append('\t').Append(w.Load.ToString("R")).Append('\t').Append(p.Gy).Append('\t').Append(w.GateY.ToString("R"))
                  .Append('\t').Append(p.Yaw).Append('\t').Append(w.Yaw.ToString("R"))
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
                case "quirk": return "quirk:" + phase;
                case "lift": return "dl03.weight:" + (phase == "approach" ? "Approach" : "Clip");
                case "setdown": return "dl03.weight:" + p.Clip;                                          // SetDownHigh or SetDown
                // grabL is the trolley's own face; grabR its twin (not a mechanism: the motor names the verb).
                case "grab": return (p.X < p.Tx ? "dl03.trolley:" : "Grab:") + (phase == "approach" ? "Approach" : "Clip");
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
            foreach (var w in rows) { var n = name(w); if (!d.ContainsKey(n)) d[n] = w.P.I; }
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
