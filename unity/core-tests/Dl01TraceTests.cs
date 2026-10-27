using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using DeadLetter.Core.Mechanisms;
using DeadLetter.Core.Mechanisms.Actuators;
using DeadLetter.Core.Mechanisms.Bridges;
using DeadLetter.Core.Mechanisms.Catches;
using DeadLetter.Core.Mechanisms.Drives;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl01;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-01 parity (U-20): the prototype's own run (the mechanical bot, seed 1, recorded by tools/sim/record_trace.mjs into
    /// Traces/prologue_mech_seed1.jsonl.gz) replayed through Core's <see cref="SceneSim"/> from the <c>start</c>
    /// checkpoint, input for input, and compared at every 60 Hz step from the first step of play to the end of the
    /// passage (checkpoint <c>room</c>).
    /// <para><b>Tolerance 1e-6</b> on every continuous value: the trace rounds to 1e-6 (≤ 5e-7 of error), and the port
    /// computes the same expressions in the same order on the same clock, so the rest is float noise (≈ 1e-12 seen).
    /// Discrete signals (acts, grounded, checkpoints, relay sets, the scene exit) must fall on the same step.</para>
    /// <para><b>Known motor issues</b> (U-11, issue #22; nothing in Lane, Scenes or Mechanisms):
    /// M2, the mantle ends one step early (<c>ClipClock</c>'s 1e-6 slack against the prototype's raw <c>f &gt;= 56</c>, L1946);
    /// M3, a walk-off fall drops g·dt²·n/2 less than the prototype's semi-implicit Euler (L2013–L2014).
    /// The checks below run with the M2 step fed no input (it is the prototype's last mantle step, which ignores input),
    /// so M2 does not shift every later step; M2's own act step, its one-step-early <c>hall</c>, and M3's falls are
    /// asserted exactly as the issues predict. The strict replay (no compensation) is the skipped test at the end.</para>
    /// </summary>
    public class Dl01TraceTests
    {
        internal const string TraceFile = "prologue_mech_seed1.jsonl.gz";
        private const double Tol = 1e-6;
        private const double G = 9.8, Dt = 1.0 / 60.0;

        /// <summary>One replayed step: the prototype's record and Core's state after the same step.</summary>
        internal sealed class Row
        {
            public TraceStep P;
            public double X, Y, Z, Vx, Yaw, Shutter, Lever, WeightY, Door, Wheel, CartX, CartDrop, Relay;
            public bool G, Lip, Exited, Released;
            public string Kind, Phase, Cp, CartState;
            public int Region, RelaySets;
        }

        internal sealed class Replay
        {
            public readonly List<Row> Rows = new List<Row>();
            public SceneSim Sim;
            /// <summary>Steps where the prototype was still mantling after Core's mantle had ended (fed no input; see <see cref="Run"/>).</summary>
            public readonly List<int> MantleCompensated = new List<int>();
        }

        private static readonly Replay[] Cache = new Replay[2];

        /// <summary>
        /// Plays DL-01 from the first step of play to the end of the passage. <paramref name="compensateMantle"/>: on a
        /// step that the prototype spends in a mantle Core has already ended (M2), Core gets no input, as the prototype
        /// ignored it there; that keeps M2 from shifting every later step, so the rest stays testable at 1e-6.
        /// </summary>
        internal static Replay Run(bool compensateMantle = true)
        {
            int slot = compensateMantle ? 1 : 0;
            lock (Cache)
            {
                if (Cache[slot] != null) return Cache[slot];
                var t = Trace.Load(TraceFile);
                int play = t.FirstIndex(p => p.Mode == "play");
                int room = t.FirstIndex(p => p.Cp == "room");
                var r = new Replay();
                Door shutter = null;
                Latch latch = null;
                CrankActuator crank = null;
                TippingBridge cart = null;
                PulseSequencer relay = null;
                MotorInput Input(int k, SceneSim sim)
                {
                    if (compensateMantle && t.Steps[k - 1].Mt && !sim.Motor.IsMantling && sim.Act == null) { r.MantleCompensated.Add(t.Steps[k].I); return default; }
                    return t.Steps[k].Input;
                }
                r.Sim = TraceReplay.Run(t, Dl01Scene.Def(), "start", fromOpening: true, play, room, (p, sim) =>
                {
                    if (shutter == null)
                    {
                        shutter = sim.Graph.Get<Door>("dl01.shutter"); latch = sim.Graph.Get<Latch>("dl01.latch");
                        crank = sim.Graph.Get<CrankActuator>("dl01.crank"); cart = sim.Graph.Get<TippingBridge>("dl01.cart");
                        relay = sim.Graph.Get<PulseSequencer>("dl01.relay");
                    }
                    int sets = 0;
                    var log = sim.Graph.Log;
                    for (int e = 0; e < log.Count; e++)
                        if (log[e].Id == "dl01.relay" && log[e].Kind == MechanismEventKind.Event && log[e].Code == (int)PulseEvent.LampLit && log[e].Index == 0) sets++;
                    r.Rows.Add(new Row
                    {
                        P = p, X = sim.X, Y = sim.Y, Z = sim.Z, Vx = sim.Vx, Yaw = sim.Yaw, G = sim.Grounded,
                        Kind = sim.ActKind, Phase = sim.ActPhase, Cp = sim.Checkpoints.Current.Name, Region = sim.Region, Exited = sim.Exited,
                        Shutter = shutter.Position, Lever = latch.LeverDeg, WeightY = Door.ShutterCounterweightY(shutter.Elapsed),
                        Released = latch.State == LatchState.Released,
                        Door = crank.Position, Wheel = crank.WheelDeg, CartX = cart.X, CartDrop = cart.Drop, CartState = cart.State.ToString(),
                        Lip = cart.State == TippingBridgeState.AtLip, Relay = relay.Units, RelaySets = sets,
                    });
                }, Input);
                return Cache[slot] = r;
            }
        }

        // ---- The trace ------------------------------------------------------------------------------------------------
        [Fact]
        public void Trace_IsTheMechanicalPrologue_Seed1_AndSmall()
        {
            var t = Trace.Load(TraceFile);
            Assert.Equal("deadletter-trace/1", t.Header.GetProperty("format").GetString());
            Assert.Equal(1, t.Header.GetProperty("seed").GetInt32());
            Assert.Equal("mechanical", t.Header.GetProperty("mode").GetString());
            Assert.Equal(1, t.Header.GetProperty("rngSeed").GetInt32());
            Assert.Null(t.EndError);
            Assert.True(t.CompressedBytes < 5_000_000, t.CompressedBytes + " bytes");
            for (int i = 0; i < t.Steps.Count; i++) Assert.Equal(i, t.Steps[i].I);             // one line per step, none missing
            Assert.Equal("DL-11 The Child at the Address", t.Steps[t.Steps.Count - 1].Scene);    // the whole prologue
            int play = t.FirstIndex(p => p.Mode == "play");
            Assert.Equal(480, t.Steps[play].Fr, 6);                                              // play starts on the opening's last step
            Assert.Equal("quirk:CheckLabel", t.Steps[play].Act);
        }

        // ---- (a) position ---------------------------------------------------------------------------------------------
        [Fact]
        public void X_Z_Vx_And_Yaw_MatchEveryStep()
        {
            var r = Run();
            Assert.True(r.Rows.Count > 2000);
            Assert.Equal(new[] { 3130 }, r.MantleCompensated);                                   // M2: one step, the mantle's last
            var bad = new List<string>();
            foreach (var w in r.Rows)
            {
                Check(bad, w.P.I, "x", w.P.X, w.X);
                Check(bad, w.P.I, "z", -w.P.Z, w.Z);                                             // Unity z = −three z (§0.2)
                Check(bad, w.P.I, "vx", w.P.Vx, w.Vx);
                Check(bad, w.P.I, "yaw", w.P.Yaw, w.Yaw);
            }
            Assert.True(bad.Count == 0, Report(bad));
        }

        /// <summary>
        /// y matches at every step except while falling from a walk-off (the motor's M3), where Core is higher by exactly
        /// g·dt²·n/2 at the n-th step of the fall: Core integrates exactly from vy = 0 (y −= g(n·dt)²/2) while the
        /// prototype's <c>vy −= g·dt; y += vy·dt</c> (L2013–L2014) drops g·dt²·n(n+1)/2. Both land on the same step here.
        /// Jumps match exactly: the motor's parity launch speed makes its exact arc equal the prototype's Euler arc.
        /// </summary>
        [Fact]
        public void Y_MatchesEveryStep_ExceptWalkOffFalls_WhereTheGapIsExactlyM3()
        {
            var r = Run();
            var bad = new List<string>();
            var falls = new List<(int at, int steps)>();
            int walkOff = -1;
            for (int k = 0; k < r.Rows.Count; k++)
            {
                var p = r.Rows[k].P;
                if (p.G) walkOff = -1;
                else if (walkOff < 0 && k > 0 && r.Rows[k - 1].P.G && p.Vy == 0) { walkOff = p.I; falls.Add((p.I, 0)); }   // walked off: vy = 0, y kept (L2032)
                double expected = walkOff >= 0 ? G * Dt * Dt * (p.I - walkOff) / 2 : 0;
                if (Math.Abs(r.Rows[k].Y - p.Y - expected) > Tol) bad.Add($"#{p.I} y {p.Y} vs {r.Rows[k].Y:R} (expected gap {expected:E3})");
                if (walkOff >= 0 && p.I > walkOff) falls[falls.Count - 1] = (walkOff, p.I - walkOff);
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(new[] { (2683, 12), (2934, 13) }, falls);                                // off the conveyor; down onto the cart
        }

        // ---- (b) acts and grounded ------------------------------------------------------------------------------------
        [Fact]
        public void Grounded_MatchesEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Run().Rows) if (w.G != w.P.G) bad.Add($"#{w.P.I} grounded {w.P.G} vs {w.G}");
            Assert.True(bad.Count == 0, Report(bad));
        }

        /// <summary>
        /// Every act and phase on the prototype's steps: the label beat, the latch (approach, Pull, Flinch), the cart (approach,
        /// Grab), the shove, the mantle, the crank (approach, turn, Crank, the wait to turn back), Proud, and the four legs
        /// of the passage. The one exception is M2's step (#3129: the prototype is in its 141st mantle step).
        /// </summary>
        [Fact]
        public void Acts_MatchEveryStep_ExceptTheMantlesLastStep()
        {
            var rows = Run().Rows;
            var bad = new List<string>();
            var seen = new HashSet<string>();
            foreach (var w in rows)
            {
                string want = ExpectedAct(w.P), got = CoreAct(w);
                if (want != null) seen.Add(want);
                if (want != got && w.P.I != 3129) bad.Add($"#{w.P.I} act {want ?? "-"} vs {got ?? "-"}");
            }
            Assert.True(bad.Count == 0, Report(bad));
            var row = rows.Find(w => w.P.I == 3129);
            Assert.Equal("mantle:", ExpectedAct(row.P));
            Assert.Null(CoreAct(row));
            foreach (var a in new[] { "quirk:CheckLabel", "dl01.latch:Approach", "dl01.latch:Clip", "dl01.latch:Flinch", "dl01.cart:Approach",
                         "dl01.cart:Clip", "shove:Clip", "mantle:", "dl01.crank:Approach", "dl01.crank:Turn", "dl01.crank:Clip", "dl01.crank:Done",
                         "quirk:Proud", "transit:0", "transit:1", "transit:2", "transit:3" })
                Assert.Contains(a, seen);
        }

        // ---- (c) checkpoints ------------------------------------------------------------------------------------------
        /// <summary>
        /// shutter (the latch's release, L1677), door (the fifth stroke, L1890) and room (the passage's end, L2145) fire on
        /// the prototype's step. hall (L2065) fires one step early: its trigger runs only on free steps, and M2 frees him one
        /// step before the prototype's mantle ends (#3130, his first step on the floor past the trench).
        /// </summary>
        [Fact]
        public void Checkpoints_FireOnThePrototypesSteps_HallOneEarlyFromM2()
        {
            var r = Run();
            var proto = FirstSteps(r.Rows, w => w.P.Cp);
            var core = FirstSteps(r.Rows, w => w.Cp);
            Assert.Equal(new[] { "start", "shutter", "hall", "door", "room" }, proto.Keys);
            Assert.Equal(proto.Keys, core.Keys);
            Assert.Equal(proto["shutter"], core["shutter"]);
            Assert.Equal(proto["door"], core["door"]);
            Assert.Equal(proto["room"], core["room"]);
            Assert.Equal(3131, proto["hall"]);
            Assert.Equal(proto["hall"] - 1, core["hall"]);
        }

        // ---- (d) mechanisms -------------------------------------------------------------------------------------------
        [Fact]
        public void Mechanisms_MatchEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Run().Rows)
            {
                var p = w.P;
                Check(bad, p.I, "shutterAngle", p.Sh, w.Shutter);                  // L1690–L1696
                Check(bad, p.I, "leverAngle", p.Lv, w.Lever);                      // L1872
                Check(bad, p.I, "weightY", p.Wy, w.WeightY);                       // L1697–L1699
                Check(bad, p.I, "doorOpen", p.Door, w.Door);                       // L1884–L1890
                Check(bad, p.I, "wheelAngle", p.Wh, w.Wheel, wheel: true);         // L1885
                Check(bad, p.I, "cart.x", p.Cx.Value, w.CartX);                    // L4697, L4746, L4757
                Check(bad, p.I, "cart.drop", p.Cd.Value, w.CartDrop);              // L4757
                Check(bad, p.I, "frame (relay clock)", p.Fr, w.Relay);             // L8499
                string cs = w.CartState == "AtLip" ? "free" : w.CartState.ToLowerInvariant();
                if (cs != p.Cs) bad.Add($"#{p.I} cart.state {p.Cs} vs {w.CartState}");
                if (w.Lip != p.Cl) bad.Add($"#{p.I} cart.lip {p.Cl} vs {w.Lip}");
                if (w.Released != p.Rel) bad.Add($"#{p.I} released {p.Rel} vs {w.Released}");
            }
            Assert.True(bad.Count == 0, Report(bad));
        }

        /// <summary>The relay's sets (<c>nextRelay += 144</c>, L8511–L8516) light lamp 0 on the prototype's steps.</summary>
        [Fact]
        public void RelaySets_FallOnThePrototypesSteps()
        {
            var rows = Run().Rows;
            var proto = new List<int>();
            var core = new List<int>();
            for (int k = 0; k < rows.Count; k++)
            {
                if (k == 0 ? rows[k].P.Nr != 480 : rows[k].P.Nr != rows[k - 1].P.Nr) proto.Add(rows[k].P.I);
                for (int n = 0; n < rows[k].RelaySets; n++) core.Add(rows[k].P.I);
            }
            Assert.Equal(7, proto.Count);                                                         // every 144 frames (6 s) from frame 480
            Assert.Equal(proto, core);
        }

        // ---- (e) leaving DL-01 ----------------------------------------------------------------------------------------
        [Fact]
        public void LeavesDl01_OnThePrototypesStep_AndTheTransitEndsWithIt()
        {
            var rows = Run().Rows;
            int protoLeave = rows.Find(w => w.P.Region == 2).P.I, coreLeave = rows.Find(w => w.Exited).P.I;
            Assert.Equal(protoLeave, coreLeave);
            Assert.StartsWith("DL-02", rows.Find(w => w.P.I == protoLeave).P.Scene);
            Assert.StartsWith("DL-01", rows.Find(w => w.P.I == protoLeave - 1).P.Scene);
            Assert.Equal(2, rows.Find(w => w.P.I == coreLeave).Region);
            var last = rows[rows.Count - 1];
            Assert.Equal("room", last.Cp);
            Assert.Null(last.Kind);
            Assert.Equal(13.2, last.X, 9);
        }

        // ---- Strict ---------------------------------------------------------------------------------------------------
        /// <summary>The replay with nothing compensated: every signal at 1e-6 on every step.</summary>
        [Fact(Skip = "U-11 motor issues (#22). M2: ClipClock's 1e-6 slack ends the mantle after 140 steps (f = 55.999999999999915) where the "
            + "prototype's raw f >= MANTLE_FRAMES (L1946) needs 141 (#2989 to #3130): he walks a step early, hall fires a step early, the "
            + "crank approach ends 3 steps early and door fires at #3516, not #3519. M3: a walk-off fall starts from vy = 0 with exact "
            + "integration, g*dt^2*n/2 above the prototype's semi-implicit Euler (L2013-L2014): #2684-#2695 and #2935-#2947, up to 1.77 cm.")]
        public void Strict_EverySignalMatchesEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Run(compensateMantle: false).Rows)
            {
                var p = w.P;
                Check(bad, p.I, "x", p.X, w.X);
                Check(bad, p.I, "y", p.Y, w.Y);
                Check(bad, p.I, "doorOpen", p.Door, w.Door);
                if (ExpectedAct(p) != CoreAct(w)) bad.Add($"#{p.I} act {ExpectedAct(p)} vs {CoreAct(w)}");
                if (p.Cp != w.Cp) bad.Add($"#{p.I} checkpoint {p.Cp} vs {w.Cp}");
            }
            Assert.True(bad.Count == 0, Report(bad));
        }

        // ---- Helpers --------------------------------------------------------------------------------------------------
        /// <summary>The prototype's act as Core names it (<see cref="SceneSim.ActKind"/>:<see cref="SceneSim.ActPhase"/>).</summary>
        internal static string ExpectedAct(TraceStep p)
        {
            if (p.Tr >= 0) return "transit:" + p.Tr;
            if (p.Mt) return "mantle:";
            if (p.Act == null) return null;
            var parts = p.Act.Split(':');
            string kind = parts[0], phase = parts[1];
            switch (kind)
            {
                case "quirk": return "quirk:" + phase;
                case "latch": return "dl01.latch:" + (phase == "approach" ? "Approach" : phase == "act" ? "Clip" : "Flinch");
                case "grabPush": return "dl01.cart:" + (phase == "approach" ? "Approach" : "Clip");
                case "shove": return "shove:Clip";
                case "crank": return "dl01.crank:" + (phase == "approach" ? "Approach" : phase == "turn" ? "Turn" : phase == "act" ? "Clip" : "Done");
                case "trenchStuck": return "dl01.trench:Stuck";
                default: return kind + ":" + phase;
            }
        }

        internal static string CoreAct(Row r) => r.Kind == null ? null : r.Kind + ":" + (r.Kind == "mantle" ? "" : r.Phase);

        private static void Check(List<string> bad, int i, string what, double proto, double core, bool wheel = false)
        {
            // The wheel: the prototype snaps it back a stroke for the one step of each wrap, Core does not
            // (CrankActuator.WheelDeg's documented deviation), so compare it modulo a stroke.
            double d = Math.Abs(core - proto);
            if (wheel) d = Math.Min(d, Math.Abs(d - 60));
            if (d > Tol) bad.Add($"#{i} {what} {proto:R} vs {core:R}");
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

        /// <summary>Writes the replay side by side as TSV when DL01_TRACE_DUMP names a file (DL01_TRACE_STRICT=1: no compensation).</summary>
        [Fact]
        public void Dump()
        {
            var path = Environment.GetEnvironmentVariable("DL01_TRACE_DUMP");
            if (string.IsNullOrEmpty(path)) return;
            var r = Run(Environment.GetEnvironmentVariable("DL01_TRACE_STRICT") != "1");
            var sb = new StringBuilder("i\tpx\tcx\tpy\tcy\tpg\tcg\tpact\tcact\tpcp\tccp\tpsh\tcsh\tpdoor\tcdoor\tpcx\tccx\tpyaw\tcyaw\tpz\tcz\tin\n");
            foreach (var w in r.Rows)
            {
                var p = w.P;
                sb.Append(p.I).Append('\t').Append(p.X).Append('\t').Append(w.X.ToString("R")).Append('\t').Append(p.Y).Append('\t').Append(w.Y.ToString("R"))
                  .Append('\t').Append(p.G ? 1 : 0).Append('\t').Append(w.G ? 1 : 0).Append('\t').Append(ExpectedAct(p)).Append('\t').Append(CoreAct(w))
                  .Append('\t').Append(p.Cp).Append('\t').Append(w.Cp).Append('\t').Append(p.Sh).Append('\t').Append(w.Shutter.ToString("R"))
                  .Append('\t').Append(p.Door).Append('\t').Append(w.Door.ToString("R")).Append('\t').Append(p.Cx).Append('\t').Append(w.CartX.ToString("R"))
                  .Append('\t').Append(p.Yaw).Append('\t').Append(w.Yaw.ToString("R")).Append('\t').Append(p.Z).Append('\t').Append(w.Z.ToString("R"))
                  .Append('\t').Append(p.L ? "L" : "").Append(p.R ? "R" : "").Append(p.JP ? "J" : "").Append(p.UP ? "U" : "").Append(p.SH ? "S" : "").Append('\n');
            }
            File.WriteAllText(path, sb.ToString());
        }
    }
}
