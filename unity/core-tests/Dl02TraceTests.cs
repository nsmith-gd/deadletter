using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using DeadLetter.Core.Carry;
using DeadLetter.Core.Hazards;
using DeadLetter.Core.Interaction;
using DeadLetter.Core.Motor;
using DeadLetter.Core.Scenes;
using DeadLetter.Core.Scenes.Dl02;
using Xunit;

namespace DeadLetter.Core.Tests
{
    /// <summary>
    /// DL-02 parity (U-20): the prototype's own runs replayed through Core's <see cref="SceneSim"/> from the <c>room</c>
    /// checkpoint (the passage's end), input for input, and compared at every 60 Hz step until he leaves DL-02 (x ≥ 25.0,
    /// where <c>sceneName</c> turns to DL-03). Two recordings of the mechanical bot, seed 1 (tools/sim/record_trace.mjs):
    /// <list type="bullet">
    /// <item><b>prologue_mech_seed1</b>: he waits for the press, walks under it, passes the tube (its letter falls), lifts the
    /// box, carries it to the table's foot, sets it down, jumps and catches the table's edge, climbs to the gantry and
    /// walks out.</item>
    /// <item><b>dl02_press_death_seed1</b> (the same bot with <c>pressMistake</c>): he walks in on the slam, is crushed,
    /// respawns at <c>room</c> 1.3 s later, then does the same.</item>
    /// </list>
    /// <para><b>Tolerance 1e-6</b> (the trace's rounding) on every continuous value; discrete signals (acts, holds, grounded,
    /// item and letter states, deaths, the respawn, the scene exit) on the same step.</para>
    /// <para><b>Known motor issue</b> (U-11, #22): M2 only. Each of the two mantles (onto the table, onto the gantry) ends one
    /// step early, so the prototype's last mantle step is fed no input (as in <see cref="Dl01TraceTests"/>), and that one
    /// step's act is asserted as M2 predicts. The strict replay is the skipped test.</para>
    /// </summary>
    public class Dl02TraceTests
    {
        internal const string MainTrace = Dl01TraceTests.TraceFile;
        internal const string DeathTrace = "dl02_press_death_seed1.jsonl.gz";
        private const double Tol = 1e-6;

        internal sealed class Row
        {
            public TraceStep P;
            public double X, Y, Z, Vx, Yaw, Press, BoxX, BoxBase, RespawnAt;
            public bool G, Exited, Holding;
            public string Kind, Phase, Cp, BoxState, Letter;
            public int Region, Deaths;
        }

        internal sealed class Replay
        {
            public readonly List<Row> Rows = new List<Row>();
            public SceneSim Sim;
            public readonly List<int> MantleCompensated = new List<int>();
            public int Room, Exit;
        }

        private static readonly Dictionary<string, Replay> Cache = new Dictionary<string, Replay>();

        /// <summary>
        /// Plays DL-02 of <paramref name="file"/> from the step after <c>room</c> to the first step in DL-03 (inclusive).
        /// <paramref name="compensateMantle"/>: see <see cref="Dl01TraceTests.Run"/> (M2).
        /// </summary>
        internal static Replay Run(string file, bool compensateMantle = true)
        {
            lock (Cache)
            {
                string key = file + compensateMantle;
                if (Cache.TryGetValue(key, out var cached)) return cached;
                var t = Trace.Load(file);
                int room = t.FirstIndex(p => p.Cp == "room");
                int exit = t.FirstIndex(p => p.Scene != null && p.Scene.StartsWith("DL-03"));
                var r = new Replay { Room = t.Steps[room].I, Exit = t.Steps[exit].I };
                PeriodicCrusher press = null;
                CarriedItem box = null;
                Dl02TubeLetter letter = null;
                MotorInput Input(int k, SceneSim sim)
                {
                    if (compensateMantle && t.Steps[k - 1].Mt && !sim.Motor.IsMantling && sim.Act == null) { r.MantleCompensated.Add(t.Steps[k].I); return default; }
                    return t.Steps[k].Input;
                }
                r.Sim = TraceReplay.Run(t, Dl02Scene.Def(), "room", fromOpening: false, room + 1, exit, (p, sim) =>
                {
                    if (press == null)
                    {
                        press = sim.Graph.Get<PeriodicCrusher>("dl02.press"); box = sim.Graph.Get<CarriedItem>("dl02.box");
                        letter = sim.Graph.Get<Dl02TubeLetter>("dl02.tubeLetter");
                    }
                    r.Rows.Add(new Row
                    {
                        P = p, X = sim.X, Y = sim.Y, Z = sim.Z, Vx = sim.Vx, Yaw = sim.Yaw, G = sim.Grounded,
                        Kind = sim.ActKind, Phase = sim.ActPhase, Cp = sim.Checkpoints.Current.Name, Region = sim.Region, Exited = sim.Exited,
                        Holding = sim.Motor.Hold == HoldKind.Item,
                        Press = press.Face, BoxX = box.X, BoxBase = box.BaseY, BoxState = box.State.ToString(), Letter = letter.State.ToString(),
                        Deaths = ((Dl02Rules)sim.Rules).Death.Deaths, RespawnAt = sim.RespawnAt,
                    });
                }, Input);
                return Cache[key] = r;
            }
        }

        public static IEnumerable<object[]> Traces() => new[] { new object[] { MainTrace }, new object[] { DeathTrace } };

        // ---- The traces -----------------------------------------------------------------------------------------------
        [Fact]
        public void DeathTrace_IsTheMechanicalBot_WalkingInOnTheSlam()
        {
            var t = Trace.Load(DeathTrace);
            Assert.Equal("deadletter-trace/1", t.Header.GetProperty("format").GetString());
            Assert.Equal("mechanical", t.Header.GetProperty("mode").GetString());
            Assert.True(t.Header.GetProperty("botOpts").GetProperty("pressMistake").GetBoolean());
            Assert.Null(t.EndError);
            for (int i = 0; i < t.Steps.Count; i++) Assert.Equal(i, t.Steps[i].I);
            // The same run as the prologue's up to the press: DL-01 is identical step for step.
            var main = Trace.Load(MainTrace);
            int room = main.FirstIndex(p => p.Cp == "room");
            Assert.Equal(room, t.FirstIndex(p => p.Cp == "room"));
            for (int i = 0; i <= room; i++) Assert.Equal(main.Steps[i].ToString(), t.Steps[i].ToString());
        }

        [Theory, MemberData(nameof(Traces))]
        public void Window_StartsAtRoom_AndEndsWhenDl03Begins(string file)
        {
            var r = Run(file);
            Assert.Equal("room", r.Rows[0].P.Cp);
            Assert.Equal(r.Room + 1, r.Rows[0].P.I);
            Assert.Equal(r.Exit, r.Rows[r.Rows.Count - 1].P.I);
            Assert.True(r.Rows.Count > 1000, r.Rows.Count + " steps");
        }

        // ---- (a) position ---------------------------------------------------------------------------------------------
        [Theory, MemberData(nameof(Traces))]
        public void X_Y_Z_Vx_And_Yaw_MatchEveryStep(string file)
        {
            var r = Run(file);
            var bad = new List<string>();
            foreach (var w in r.Rows)
            {
                Check(bad, w.P.I, "x", w.P.X, w.X);
                Check(bad, w.P.I, "y", w.P.Y, w.Y);
                Check(bad, w.P.I, "z", -w.P.Z, w.Z);                                             // Unity z = −three z (§0.2)
                Check(bad, w.P.I, "vx", w.P.Vx, w.Vx);
                Check(bad, w.P.I, "yaw", w.P.Yaw, w.Yaw);
            }
            Assert.True(bad.Count == 0, Report(bad));
        }

        /// <summary>M2 compensates exactly the last step of each mantle: onto the table, then onto the gantry.</summary>
        [Theory, MemberData(nameof(Traces))]
        public void MantleCompensation_IsTheTwoMantlesLastSteps(string file)
        {
            var r = Run(file);
            var ends = MantleEnds(r.Rows);
            Assert.Equal(2, ends.Count);
            Assert.Equal(ends, r.MantleCompensated);
        }

        // ---- (b) acts, holds and grounded -----------------------------------------------------------------------------
        /// <summary>
        /// Grounded on every step except M2's, where the prototype is still in the mantle that started in the air (the
        /// jump that catches the table's edge: <c>game.grounded</c> stays false until it ends, L1946) and Core's has ended.
        /// The standing climb onto the gantry keeps him grounded throughout, so its M2 step matches.
        /// </summary>
        [Theory, MemberData(nameof(Traces))]
        public void Grounded_MatchesEveryStep_ExceptTheAirMantlesLastStep(string file)
        {
            var r = Run(file);
            var bad = new List<string>();
            var m2 = new List<int>();
            foreach (var w in r.Rows)
            {
                if (w.G == w.P.G) continue;
                if (r.MantleCompensated.Contains(w.P.I + 1) && w.P.Mt && !w.P.G && w.G && w.Kind == null) m2.Add(w.P.I);
                else bad.Add($"#{w.P.I} grounded {w.P.G} vs {w.G}");
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(new[] { r.MantleCompensated[0] - 1 }, m2);                             // the table; not the gantry
        }

        /// <summary>
        /// Every act and phase on the prototype's steps (the box's approach, Lift and SetDown, the two mantles, the death),
        /// and the carry (<c>game.hold === 'item'</c>) on the same steps. The exceptions are M2's: the step before each
        /// compensated one, where the prototype is in its 141st mantle step and Core's mantle has ended.
        /// </summary>
        [Theory, MemberData(nameof(Traces))]
        public void Acts_And_TheCarry_MatchEveryStep_ExceptEachMantlesLastStep(string file)
        {
            var r = Run(file);
            var m2 = new HashSet<int>();
            foreach (var i in r.MantleCompensated) m2.Add(i - 1);
            var bad = new List<string>();
            var seen = new HashSet<string>();
            foreach (var w in r.Rows)
            {
                string want = ExpectedAct(w.P), got = CoreAct(w);
                if (want != null) seen.Add(want);
                if (m2.Contains(w.P.I))
                {
                    if (want != "mantle:" || got != null) bad.Add($"#{w.P.I} M2 step: act {want ?? "-"} vs {got ?? "-"}");
                }
                else if (want != got) bad.Add($"#{w.P.I} act {want ?? "-"} vs {got ?? "-"}");
                bool holding = w.P.Hold == "item";
                if (holding != w.Holding) bad.Add($"#{w.P.I} hold {w.P.Hold ?? "-"} vs {(w.Holding ? "item" : "-")}");
            }
            Assert.True(bad.Count == 0, Report(bad));
            foreach (var a in new[] { "dl02.box:Approach", "dl02.box:Clip", "mantle:" }) Assert.Contains(a, seen);
            if (file == DeathTrace) Assert.Contains("death:Crush", seen);
        }

        // ---- (c) mechanisms -------------------------------------------------------------------------------------------
        /// <summary>The press's face (L7310–L7316), the box (x, base, state; L4419, L4425) and the tube's letter (L4772–L4779).</summary>
        [Theory, MemberData(nameof(Traces))]
        public void Mechanisms_MatchEveryStep(string file)
        {
            var bad = new List<string>();
            var letters = new List<string>();
            foreach (var w in Run(file).Rows)
            {
                var p = w.P;
                Check(bad, p.I, "press face", p.Pf.Value, w.Press);
                Check(bad, p.I, "box.x", p.Bx.Value, w.BoxX);
                Check(bad, p.I, "box.base", p.Bb.Value, w.BoxBase);
                string bs = w.BoxState == "Carried" ? "carried" : w.BoxState.ToLowerInvariant();
                if (bs != p.Bs) bad.Add($"#{p.I} box.state {p.Bs} vs {w.BoxState}");
                if (w.Letter.ToLowerInvariant() != p.Tl) bad.Add($"#{p.I} tube letter {p.Tl} vs {w.Letter}");
                if (letters.Count == 0 || letters[letters.Count - 1] != p.Tl) letters.Add(p.Tl);
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(new[] { "cup", "falling", "floor" }, letters);
        }

        // ---- (d) checkpoints, death and respawn -----------------------------------------------------------------------
        [Theory, MemberData(nameof(Traces))]
        public void Checkpoint_StaysRoom_DeathsAndTheRespawn_MatchEveryStep(string file)
        {
            var bad = new List<string>();
            var rows = Run(file).Rows;
            foreach (var w in rows)
            {
                if (w.P.Cp != w.Cp) bad.Add($"#{w.P.I} checkpoint {w.P.Cp} vs {w.Cp}");
                if (w.P.Dn != w.Deaths) bad.Add($"#{w.P.I} deaths {w.P.Dn} vs {w.Deaths}");
                Check(bad, w.P.I, "respawnAt", w.P.Ra, w.RespawnAt);
            }
            Assert.True(bad.Count == 0, Report(bad));
            Assert.Equal(file == DeathTrace ? 1 : 0, rows[rows.Count - 1].Deaths);
        }

        /// <summary>
        /// The death trace's story, step by step: crushed under the ram (x in 13.62–14.28, face below 0.74), the death holds
        /// 0.7 s (42 steps) before the cut sets the respawn 0.6 s on, and on that step he is back at room: 37 steps, as the
        /// clock summed in 1/60 s steps is a hair short of <c>respawnAt</c> after 36 (L8494).
        /// </summary>
        [Fact]
        public void Death_HoldsThenCuts_AndRespawnsAtRoom_OnThePrototypesSteps()
        {
            var rows = Run(DeathTrace).Rows;
            var died = rows.Find(w => w.P.Dn == 1);
            Assert.Equal("death:Crush", CoreAct(died));
            Assert.InRange(died.X, 13.62, 14.28);
            Assert.True(died.Press < 0.74, "face " + died.Press);
            var cut = rows.Find(w => w.P.Ra > 0);
            Assert.Equal(died.P.I + 42, cut.P.I);
            Assert.True(cut.RespawnAt > 0);
            var back = rows.Find(w => w.P.I > cut.P.I && w.P.Ra == 0);
            Assert.Equal(cut.P.I + 37, back.P.I);
            Assert.Equal(13.2, back.X, 9);
            Assert.Null(back.Kind);
            Assert.Equal("Floor", back.BoxState);
        }

        // ---- (e) leaving DL-02 ----------------------------------------------------------------------------------------
        [Theory, MemberData(nameof(Traces))]
        public void LeavesDl02_OnThePrototypesStep(string file)
        {
            var r = Run(file);
            var first = r.Rows.Find(w => w.Exited);
            Assert.NotNull(first);
            Assert.Equal(r.Exit, first.P.I);
            Assert.StartsWith("DL-02", r.Rows.Find(w => w.P.I == r.Exit - 1).P.Scene);
            Assert.True(first.X >= 25.0 && r.Rows.Find(w => w.P.I == r.Exit - 1).X < 25.0);
            Assert.Equal(1.35, first.Y, 9);                                                       // on the sill
            Assert.Equal("Floor", first.BoxState);                                                // the box left at the table
        }

        // ---- Strict ---------------------------------------------------------------------------------------------------
        [Fact(Skip = "U-11 motor issue M2 (#22): the mantle ends after 140 steps where the prototype's raw f >= MANTLE_FRAMES (L1946) needs "
            + "141. Uncompensated, each of DL-02's two mantles (#4698-#4838 onto the table, #4990-#5130 onto the gantry) frees him a step "
            + "early: the acts differ at #4838 and #5130, and he walks on a step ahead, so x differs on 239 of the 1,146 steps (up to "
            + "2.7 cm, one step's travel at a run) until the bot's next stop; y matches throughout.")]
        public void Strict_EverySignalMatchesEveryStep()
        {
            var bad = new List<string>();
            foreach (var w in Run(MainTrace, compensateMantle: false).Rows)
            {
                var p = w.P;
                Check(bad, p.I, "x", p.X, w.X);
                Check(bad, p.I, "y", p.Y, w.Y);
                if (ExpectedAct(p) != CoreAct(w)) bad.Add($"#{p.I} act {ExpectedAct(p)} vs {CoreAct(w)}");
            }
            Assert.True(bad.Count == 0, Report(bad));
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
                case "liftItem": return "dl02.box:" + (phase == "approach" ? "Approach" : "Clip");
                case "setdownItem": return "dl02.box:Clip";
                case "death": return "death:Crush";
                default: return kind + ":" + phase;
            }
        }

        internal static string CoreAct(Row r) => r.Kind == null ? null : r.Kind + ":" + (r.Kind == "mantle" ? "" : r.Phase);

        /// <summary>The first step after each recorded mantle (the prototype's own last mantle step: mt is 0 there).</summary>
        private static List<int> MantleEnds(List<Row> rows)
        {
            var ends = new List<int>();
            for (int k = 1; k < rows.Count; k++) if (rows[k - 1].P.Mt && !rows[k].P.Mt) ends.Add(rows[k].P.I);
            return ends;
        }

        private static void Check(List<string> bad, int i, string what, double proto, double core)
        {
            if (!(Math.Abs(core - proto) <= Tol)) bad.Add($"#{i} {what} {proto:R} vs {core:R}");
        }

        private static string Report(List<string> bad)
        {
            var sb = new StringBuilder().Append(bad.Count).Append(" mismatches");
            for (int i = 0; i < bad.Count && i < 12; i++) sb.Append("\n  ").Append(bad[i]);
            return sb.ToString();
        }

        /// <summary>Writes a replay side by side as TSV when DL02_TRACE_DUMP names a file (DL02_TRACE=death: the death trace; DL02_TRACE_STRICT=1).</summary>
        [Fact]
        public void Dump()
        {
            var path = Environment.GetEnvironmentVariable("DL02_TRACE_DUMP");
            if (string.IsNullOrEmpty(path)) return;
            var r = Run(Environment.GetEnvironmentVariable("DL02_TRACE") == "death" ? DeathTrace : MainTrace,
                Environment.GetEnvironmentVariable("DL02_TRACE_STRICT") != "1");
            var sb = new StringBuilder("i\tpx\tcx\tpy\tcy\tpvx\tcvx\tpyaw\tcyaw\tpg\tcg\tpact\tcact\tph\tch\tppf\tcpf\tpbx\tcbx\tpbs\tcbs\tptl\tctl\tin\n");
            foreach (var w in r.Rows)
            {
                var p = w.P;
                sb.Append(p.I).Append('\t').Append(p.X).Append('\t').Append(w.X.ToString("R")).Append('\t').Append(p.Y).Append('\t').Append(w.Y.ToString("R"))
                  .Append('\t').Append(p.Vx).Append('\t').Append(w.Vx.ToString("R")).Append('\t').Append(p.Yaw).Append('\t').Append(w.Yaw.ToString("R"))
                  .Append('\t').Append(p.G ? 1 : 0).Append('\t').Append(w.G ? 1 : 0).Append('\t').Append(ExpectedAct(p)).Append('\t').Append(CoreAct(w))
                  .Append('\t').Append(p.Hold).Append('\t').Append(w.Holding ? "item" : "").Append('\t').Append(p.Pf).Append('\t').Append(w.Press.ToString("R"))
                  .Append('\t').Append(p.Bx).Append('\t').Append(w.BoxX.ToString("R")).Append('\t').Append(p.Bs).Append('\t').Append(w.BoxState)
                  .Append('\t').Append(p.Tl).Append('\t').Append(w.Letter)
                  .Append('\t').Append(p.L ? "L" : "").Append(p.R ? "R" : "").Append(p.JP ? "J" : "").Append(p.UP ? "U" : "").Append(p.SH ? "S" : "").Append('\n');
            }
            File.WriteAllText(path, sb.ToString());
        }
    }
}
